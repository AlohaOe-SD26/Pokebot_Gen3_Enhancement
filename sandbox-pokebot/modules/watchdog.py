"""
Watchdog / auto-recovery (fork enhancement, punch-list #22).

Makes unattended 24/7 hunting trustworthy: detect when the bot is STUCK or
has faulted and recover automatically, with alerts, instead of silently
wasting hours.

Detection signals (each guarded against false-trips):
  * Encounter stall — a hunting mode that WAS producing encounters stops
    producing them for `encounter_stall_minutes` while the game is still
    running (walked into a wall / desync). The primary, reliably-recoverable
    fault. Keyed off "we saw encounters, then they stopped", so a
    non-encounter mode (which never seeds that flag) can never false-trip.
  * Fault drop-to-Manual — the bot mode raised and main.py dropped to
    Manual (an error message appears coincident with the transition). We
    ALWAYS alert (so an overnight hunt dying is noticed); auto-restart only
    if `auto_restart_on_error`.
  * Frame freeze — the emulator frame counter stops advancing entirely
    (the main loop is hung). Detected by a background thread; recovery of a
    truly hung main thread is not safely possible, so this is ALERT-ONLY
    (honest scope).

Recovery ladder (escalating, capped, each step alerted):
  1. re-assert the same bot mode (rebuild its generator);
  2. reload a recent healthy save state (a periodically-captured in-memory
     snapshot, or the profile's current_state.ss1) + re-assert — a safety
     backup is taken first if the backup system is available;
  3. after `max_recovery_attempts` failures: STOP — drop to Manual, alert
     loudly, and do NOT hammer a broken state.

Every state/memory action is safe-state gated and fully exception-guarded:
the watchdog can never crash the frame loop or corrupt a save. Disabled
config = fully inert (zero per-frame cost).
"""

from __future__ import annotations

import logging
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from modules.context import context
from modules.runtime import get_base_path

DEFAULTS: dict = {
    "enabled": True,
    "softlock_seconds": 45,          # frame counter frozen this long -> freeze alert
    "encounter_stall_minutes": 20,   # hunting mode produced nothing this long -> recover
    "max_recovery_attempts": 3,      # consecutive attempts before giving up
    "recovery_cooldown_seconds": 90, # wait after an attempt before escalating
    "reload_savestate": True,        # ladder step 2 (else it's skipped)
    "backup_before_reload": True,    # safety backup before a savestate reload
    "auto_restart_on_error": True,   # restart the mode after a fault drop-to-Manual
    "healthy_snapshot_minutes": 10,  # capture an in-memory good state this often
    "alerts": True,                  # desktop toast + sound on fault/recovery
}

# Modes we consider "hunting" for the encounter-stall grace. The stall check
# is gated on having-seen-an-encounter anyway; this list is only used to
# avoid arming a cold-start timer on obviously non-encounter modes.
_NON_HUNTING_MODES = {"Manual", "", "Macro (Custom)"}

# Modes that manage their OWN failure recovery (whiteouts, derails) and must NEVER
# be save-state-reloaded by the watchdog. Reloading rewinds a story playthrough to
# an older state — the exact "loads older and older save states" regression the user
# reported. The Story bot navigates its own defeat/whiteout sequence and resumes
# from the respawn point, so the watchdog stays completely hands-off for it.
_SELF_RECOVERING_MODES = {"Story"}

_log = logging.getLogger("watchdog")


def _setup_log() -> None:
    if _log.handlers:
        return
    try:
        log_dir = get_base_path() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(log_dir / "watchdog.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s"))
        _log.addHandler(handler)
        _log.setLevel(logging.INFO)
    except Exception:
        pass


def _to_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_config(profile_path: "Path | None" = None) -> dict:
    """Merge DEFAULTS with watchdog.yml (global root, then per-profile
    override). Malformed / missing files fall back key-by-key to defaults —
    mirrors the backup.yml / alerts.yml convention."""
    import yaml

    config = dict(DEFAULTS)

    def _read(path: Path) -> "dict | None":
        try:
            if path.is_file():
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else None
        except Exception as error:
            _log.warning("could not read %s: %s", path, error)
        return None

    for source in (get_base_path() / "watchdog.yml", (profile_path / "watchdog.yml") if profile_path else None):
        if source is None:
            continue
        data = _read(source)
        if not data:
            continue
        for key, default in DEFAULTS.items():
            if key in data:
                if isinstance(default, bool):
                    config[key] = bool(data[key])
                elif isinstance(default, int):
                    config[key] = _to_int(data[key], default)
    return config


class Watchdog:
    """Singleton — state lives here (not in the listener), so it survives the
    listener rebuilds that happen on every emulator reset."""

    def __init__(self) -> None:
        self._config: dict = dict(DEFAULTS)
        self._loaded_for: "Path | None" = None

        self._last_check = 0.0
        self._last_encounter = time.monotonic()
        self._seen_encounter = False
        self._last_hunting_mode = ""
        self._prev_mode = "Manual"
        self._msg_while_hunting = ""

        self._recovery_attempts = 0
        self._last_recovery = 0.0
        self._status = "OK"
        self._recovered_count = 0
        self._last_event = ""
        self._given_up = False
        self._suppress_manual = False

        self._last_good_state: "bytes | None" = None
        self._last_snapshot = 0.0

        self._bg_thread: "threading.Thread | None" = None
        self._bg_stop = threading.Event()
        self._bg_last_frame = -1
        self._bg_last_change = time.monotonic()
        self._freeze_alerted = False

    # ---- config ----
    def _cfg(self) -> dict:
        profile_path = context.profile.path if context.profile is not None else None
        if profile_path != self._loaded_for:
            self._config = load_config(profile_path)
            self._loaded_for = profile_path
        return self._config

    # ---- public: called from the plugin ----
    def note_encounter(self) -> None:
        """An encounter was logged — the hunt is making progress. Resets the
        stall timer and clears any fault (progress == recovered)."""
        try:
            self._last_encounter = time.monotonic()
            self._seen_encounter = True
            if self._recovery_attempts or self._status != "OK":
                self._set_status("OK", "hunt resumed")
            self._recovery_attempts = 0
            self._given_up = False
        except Exception:
            pass

    def start_background_monitor(self) -> None:
        _setup_log()
        if not self._cfg()["enabled"] or self._bg_thread is not None:
            return
        self._bg_stop.clear()
        self._bg_thread = threading.Thread(target=self._bg_loop, name="watchdog-freeze", daemon=True)
        self._bg_thread.start()

    def get_status_line(self) -> str:
        if not self._cfg()["enabled"]:
            return ""
        base = {"OK": "Watchdog: OK", "recovering": "Watchdog: recovering…", "FAULT": "Watchdog: FAULT — needs attention"}
        line = base.get(self._status, "Watchdog: OK")
        if self._recovered_count:
            line += f" · recovered {self._recovered_count}×"
        if self._last_event and self._status != "OK":
            line += f" · {self._last_event}"
        return line

    # ---- per-frame tick (main thread, safe point) ----
    def tick(self) -> None:
        try:
            cfg = self._cfg()
            if not cfg["enabled"] or context.emulator is None or context.debug:
                return
            now = time.monotonic()
            if now - self._last_check < 1.0:   # throttle: ~once/second
                return
            self._last_check = now

            mode = context.bot_mode
            self._detect_fault_drop_to_manual(mode, cfg)

            if mode in _NON_HUNTING_MODES or mode in _SELF_RECOVERING_MODES:
                # For self-recovering modes we still ran fault detection above (to
                # alert), but we do NOT snapshot state, track it as a hunting mode,
                # or run stall recovery — it owns its own recovery.
                self._prev_mode = mode
                return
            self._last_hunting_mode = mode
            self._msg_while_hunting = context.message or ""
            self._prev_mode = mode

            self._maybe_snapshot_healthy_state(cfg, now)
            self._check_encounter_stall(cfg, now)
        except Exception as error:  # a watchdog bug must never take down the loop
            _log.error("tick error: %s", error)

    # ---- detection ----
    def _detect_fault_drop_to_manual(self, mode: str, cfg: dict) -> None:
        if mode == "Manual" and self._prev_mode not in ("Manual", ""):
            if self._suppress_manual:          # our own give-up caused this
                self._suppress_manual = False
                self._prev_mode = "Manual"
                return
            message = context.message or ""
            is_error = bool(message) and message != self._msg_while_hunting
            if is_error:
                self._alert(f"Bot stopped: {message}", loud=True)
                self._set_status("FAULT", "mode error")
                # A self-recovering mode (Story) manages its own recovery — NEVER
                # reload a save state for it (that rewinds progress, user-reported);
                # just alert and leave it in Manual for the user to restart.
                if (
                    cfg["auto_restart_on_error"]
                    and not self._given_up
                    and self._prev_mode not in _SELF_RECOVERING_MODES
                ):
                    self._recover("fault drop-to-Manual", cfg, target_mode=self._last_hunting_mode)
            self._prev_mode = "Manual"

    def _check_encounter_stall(self, cfg: dict, now: float) -> None:
        if not self._seen_encounter:
            return  # a mode that never produced an encounter can't "stall"
        stall_seconds = cfg["encounter_stall_minutes"] * 60
        if now - self._last_encounter < stall_seconds:
            return
        if self._given_up:
            return
        if now - self._last_recovery < cfg["recovery_cooldown_seconds"]:
            return  # give a prior attempt time to take effect
        minutes = int((now - self._last_encounter) / 60)
        self._recover(f"no encounters for {minutes} min", cfg, target_mode=context.bot_mode)

    def _maybe_snapshot_healthy_state(self, cfg: dict, now: float) -> None:
        if self._status != "OK" or not self._seen_encounter:
            return
        if now - self._last_snapshot < cfg["healthy_snapshot_minutes"] * 60:
            return
        if not self._in_safe_state():
            return
        try:
            self._last_good_state = context.emulator.get_save_state()
            self._last_snapshot = now
            _log.info("captured healthy save-state snapshot")
        except Exception as error:
            _log.warning("healthy snapshot failed: %s", error)

    # ---- recovery ladder ----
    def _recover(self, reason: str, cfg: dict, target_mode: str) -> None:
        if not target_mode or target_mode in _NON_HUNTING_MODES:
            return
        self._recovery_attempts += 1
        self._last_recovery = time.monotonic()
        attempt = self._recovery_attempts
        _log.warning("recovery attempt %s (%s): %s", attempt, target_mode, reason)

        if attempt > cfg["max_recovery_attempts"]:
            self._give_up(reason)
            return

        self._set_status("recovering", f"attempt {attempt}: {reason}")
        try:
            if attempt == 1 or not cfg["reload_savestate"]:
                self._reassert_mode(target_mode)
                self._alert(f"Auto-recovery: restarting {target_mode} ({reason}).")
            else:
                self._reload_savestate(cfg, target_mode)
                self._alert(f"Auto-recovery: reloaded save state + restarting {target_mode} ({reason}).", loud=True)
            self._recovered_count += 1
        except Exception as error:
            _log.error("recovery action failed: %s", error)
            self._alert(f"Auto-recovery step failed: {error}", loud=True)

    def _reassert_mode(self, target_mode: str) -> None:
        # Clearing the controller stack + (re)setting the mode makes main_loop
        # rebuild the mode's generator on its next iteration.
        try:
            context.controller_stack.clear()
        except Exception:
            pass
        context.emulator.reset_held_buttons()
        context.bot_mode = target_mode

    def _reload_savestate(self, cfg: dict, target_mode: str) -> None:
        if not self._in_safe_state():
            # Not safe to touch state right now — fall back to a plain re-assert.
            self._reassert_mode(target_mode)
            return
        if cfg["backup_before_reload"] and context.profile is not None:
            try:
                from modules import backup_manager

                backup_manager.create_backup(context.profile.path, reason="watchdog")
            except Exception as error:
                _log.warning("pre-reload backup failed (continuing): %s", error)
        state = self._last_good_state
        if state is None and context.profile is not None:
            try:
                path = context.profile.path / "current_state.ss1"
                if path.is_file():
                    state = path.read_bytes()
            except Exception as error:
                _log.warning("could not read current_state.ss1: %s", error)
        if state is None:
            self._reassert_mode(target_mode)
            return
        context.emulator.load_save_state(state)
        self._reassert_mode(target_mode)

    def _give_up(self, reason: str) -> None:
        self._given_up = True
        self._set_status("FAULT", f"gave up after {self._recovery_attempts - 1} tries")
        self._alert(f"Watchdog gave up ({reason}) — dropped to Manual, needs attention.", loud=True)
        try:
            self._suppress_manual = True
            context.set_manual_mode()
        except Exception as error:
            _log.error("give-up set_manual_mode failed: %s", error)

    # ---- helpers ----
    def _in_safe_state(self) -> bool:
        try:
            from modules.memory import GameState, get_game_state

            return get_game_state() == GameState.OVERWORLD
        except Exception:
            return False

    def _set_status(self, status: str, event: str) -> None:
        self._status = status
        self._last_event = event
        _log.info("status=%s (%s)", status, event)

    def _alert(self, message: str, loud: bool = False) -> None:
        self._last_event = message
        try:
            context.message = message
        except Exception:
            pass
        if not self._cfg()["alerts"]:
            return
        try:
            from notifypy import Notify

            toast = Notify()
            toast.application_name = "PokéBot"
            toast.title = "🐶 Watchdog"
            toast.message = message
            toast.send(block=False)
        except Exception:
            pass
        if loud:
            try:
                import winsound

                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass

    # ---- background frame-freeze monitor ----
    def _bg_loop(self) -> None:
        while not self._bg_stop.wait(1.0):
            self._freeze_check()

    def _freeze_check(self) -> bool:
        """One sampling step for the frame-freeze monitor. Returns True if it
        raised a freeze alert this call. Safe to call from the bg thread —
        it never touches context.profile (which the main thread owns)."""
        try:
            cfg = self._config  # not _cfg(): avoid touching context.profile from the thread
            if not cfg["enabled"] or context.emulator is None:
                return False
            if context.bot_mode in _NON_HUNTING_MODES or context.debug:
                self._bg_last_change = time.monotonic()
                self._freeze_alerted = False
                return False
            frame = context.emulator.get_frame_count()
            if frame != self._bg_last_frame:
                self._bg_last_frame = frame
                self._bg_last_change = time.monotonic()
                self._freeze_alerted = False
            elif not self._freeze_alerted and time.monotonic() - self._bg_last_change > cfg["softlock_seconds"]:
                # Frame counter frozen while a mode is active = the main loop
                # is hung. A hung main thread cannot be safely auto-recovered
                # from here, so this is ALERT-ONLY.
                self._freeze_alerted = True
                self._set_status("FAULT", "frame counter frozen")
                self._alert("Emulator appears frozen (no frame progress) — needs attention.", loud=True)
                return True
        except Exception as error:
            _log.error("bg monitor error: %s", error)
        return False


watchdog = Watchdog()
