"""One LANE of an ENDLESS LOOP x4 batch (punch-list #24-x4).

This is a `pokebot.py` frontend, selected by `--tile-shm`. It is `PokebotHeadless`
with one addition: instead of throwing every frame away, it publishes a 240x160 RGB
frame plus a small status blob into the batch's shared memory (`modules/tile_bridge`),
where the dashboard paints it as one tile of a 2x2 grid.

WHY A SEPARATE PROCESS AT ALL
-----------------------------
`context` is a process-wide singleton with exactly one `context.emulator`; four
emulators in one process is a fork-wide refactor. See `modules/tile_bridge.py`.

‼ VIDEO MUST BE ON IN A LANE
----------------------------
`get_current_screen_image()` returns whatever mGBA last rendered — with the renderer
off it is blank, and `get_screenshot()`'s save-state-and-step workaround costs a state
round-trip per publish, which on the hot path of four unthrottled lanes is not
acceptable. So a lane runs with `context.video = True` and eats the renderer cost.
That is the deliberate trade named in the design: an x4 batch is the WATCHABLE mode,
not the fastest way to generate logs (a headless `livetest.py` lane is faster).

‼ AND NOTHING HERE MAY RAISE
----------------------------
Everything on the publish path is wrapped: a lane that dies because a party read
threw is a lane that stops producing the logs the batch exists to collect.
"""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

from modules.context import context
from modules.game import set_rom
from modules.libmgba import LibmgbaEmulator
from modules.tile_bridge import FRAME_HEIGHT, FRAME_WIDTH, TileBridge

if TYPE_CHECKING:
    from pokebot import StartupSettings

#: Publish rate. The lanes emulate UNTHROTTLED (hundreds of fps); painting every frame
#: would be pure waste and would starve the dashboard. 20 Hz is enough to see motion,
#: read the message line and tell a wedged lane from a live one.
PUBLISH_HZ = 20
_PUBLISH_INTERVAL_NS = int(1_000_000_000 / PUBLISH_HZ)


class PokebotTileChild:
    """Headless frontend that mirrors its screen into the batch's shared memory."""

    def __init__(self, main_loop: callable, on_exit: callable, shm_name: str, slot: int, lanes: int, lane_tag: str):
        self._main_loop = main_loop
        self._on_exit = on_exit
        self._shm_name = shm_name
        self._slot = int(slot)
        self._lanes = int(lanes)
        self._lane_tag = lane_tag
        self.is_headless = True
        #: `pokebot.on_exit` pokes `gui.window`; headless frontends must still have it.
        self.window = None

        self._bridge: TileBridge | None = None
        self._sequence = 0
        self._last_publish_ns = 0
        self._pid = os.getpid()
        self._log_path: str | None = None
        self._log_reenables = 0
        self._parked = False
        self._last_command_seq = 0

    # ------------------------------------------------------------------
    def run(self, startup_settings: "StartupSettings"):
        if startup_settings.profile is None:
            raise RuntimeError("A tile lane cannot be started without a profile.")

        context.profile = startup_settings.profile
        context.config.load(startup_settings.profile.path, strict=False)
        set_rom(startup_settings.profile.rom)
        context.emulator = LibmgbaEmulator(startup_settings.profile, self._on_frame)
        # Muted at the source: four `sounddevice` output streams fighting over one
        # device is a real failure mode, and the user asked for all lanes muted.
        context.audio = False
        context.video = True  # REQUIRED — see module docstring
        context.emulation_speed = startup_settings.emulation_speed
        context.debug = False

        try:
            self._bridge = TileBridge(self._shm_name, self._lanes, create=False)
        except Exception as exc:  # noqa: BLE001
            # No tile is survivable (the run still produces logs); dying is not.
            from modules.console import console

            console.print(f"[yellow]{self._lane_tag}: could not attach to the tile bridge ({exc}); running blind.[/]")

        # The whole point of an x4 batch is diagnosable logs, so debug logging is ON
        # and the file carries the lane tag (P1..P4) the user asked for.
        self._enable_debug_log(startup_settings.profile)

        context.bot_mode = startup_settings.bot_mode
        self._main_loop()

    def on_settings_updated(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Debug logging — the deliverable, so it is loud about failing
    # ------------------------------------------------------------------
    def _enable_debug_log(self, profile) -> None:
        """Start the debug logger and SAY WHAT HAPPENED.

        ‼ This was `try: enable(...) except: pass`, which is doubly blind:
        `debug_logger.enable()` reports failure by RETURNING an error string, not by
        raising, so a lane could run for hours writing nothing and neither the console nor
        the tile would say so (user report 2026-07-26: "seems like they didn't [log]").
        A feature whose entire purpose is producing logs must never fail quietly.
        """
        from modules.console import console

        try:
            from modules import debug_logger

            result = debug_logger.enable(profile, name_prefix=f"{self._lane_tag}-")
        except Exception as exc:  # noqa: BLE001
            self._log_path = None
            console.print(f"[red]{self._lane_tag}: debug logging FAILED to start: {type(exc).__name__}: {exc}[/]")
            return

        if not result or result.startswith("<failed"):
            self._log_path = None
            console.print(f"[red]{self._lane_tag}: debug logging FAILED to start: {result}[/]")
        else:
            self._log_path = result
            console.print(f"[green]{self._lane_tag}: debug log -> {result}[/]")

    def _ensure_logging(self) -> None:
        """Re-arm the debug logger if it has stopped. Bounded, and cheap enough to run at
        publish rate.

        The first `enable()` happens before the emulator has executed a single frame, and
        the endless mode hard-resets the emulator between runs — if either ever leaves the
        logger off, the lane silently stops being useful. Each re-arm opens a NEW file, so
        this is capped rather than looping.
        """
        # ‼ A PARKED lane must stay un-logged. Parking deliberately closes the log file so
        # the dashboard can copy and archive it; without this check the self-healer would
        # re-open it a fraction of a second later and the collector would be moving a file
        # that is being written to again.
        if self._parked:
            return
        try:
            from modules import debug_logger

            if debug_logger.is_enabled() or self._log_reenables >= 5:
                return
            self._log_reenables += 1
            from modules.console import console

            console.print(f"[yellow]{self._lane_tag}: debug logging was off — re-arming "
                          f"({self._log_reenables}/5).[/]")
            self._enable_debug_log(context.profile)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _on_frame(self) -> None:
        """Emulator frame callback. Must be cheap and must never raise."""
        try:
            now = time.perf_counter_ns()
            if now - self._last_publish_ns < _PUBLISH_INTERVAL_NS:
                return
            self._last_publish_ns = now
            self._poll_commands()
            self._ensure_logging()
            if self._bridge is None:
                return

            image = context.emulator.get_current_screen_image()
            if image.mode != "RGB":
                image = image.convert("RGB")
            if image.size != (FRAME_WIDTH, FRAME_HEIGHT):
                image = image.resize((FRAME_WIDTH, FRAME_HEIGHT))

            self._sequence += 1
            self._bridge.publish(
                self._slot, image.tobytes(), self._sequence, self._pid, self._runs_completed(), self._status()
            )
        except Exception:
            # Never let the tile channel take down the lane.
            pass

    # ------------------------------------------------------------------
    # Commands from the dashboard
    # ------------------------------------------------------------------
    def _poll_commands(self) -> None:
        """Act on a command posted by the dashboard. Checked at publish rate (~20 Hz)."""
        if self._bridge is None:
            return
        try:
            from modules.tile_bridge import CMD_PARK

            command, sequence = self._bridge.read_command(self._slot)
            if sequence == self._last_command_seq:
                return  # nothing new — the child acts on a CHANGE, not on a value
            self._last_command_seq = sequence
            if command == CMD_PARK:
                self._park()
        except Exception:
            pass

    def _park(self) -> None:
        """Bring the lane to a safe, quiescent, NOT-WRITING state.

        This is what makes `modules/x4_logs.py` safe: a log file being copied (and then
        MOVED) must not still be open for append in another process. Order matters —
        stop the bot first, then close the log, so nothing can write between the two.
        """
        from modules.console import console

        console.print(f"[cyan]{self._lane_tag}: PARK requested — stopping the batch and closing the log.[/]")
        self._parked = True  # set FIRST: blocks the logging self-healer from re-arming

        for label, action in (
            ("bot mode -> Manual", lambda: setattr(context, "bot_mode", "Manual")),
            ("speed -> 1x", lambda: setattr(context, "emulation_speed", 1)),
            ("reset to title", lambda: context.emulator.reset()),
        ):
            try:
                action()
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]{self._lane_tag}: park step '{label}' failed: {exc}[/]")

        try:
            from modules import debug_logger

            debug_logger.disable()  # flushes and CLOSES the file
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]{self._lane_tag}: could not close the debug log: {exc}[/]")

        console.print(f"[green]{self._lane_tag}: parked.[/]")

    @staticmethod
    def _runs_completed() -> int:
        try:
            from plugins.custom_modes import story_mode as _sm

            return int(getattr(_sm, "ENDLESS_RESET_COMPLETED", 0))
        except Exception:
            return 0

    def _status(self) -> dict:
        status = {
            "lane": self._lane_tag,
            "message": str(getattr(context, "message", "") or "")[:160],
            "mode": str(getattr(context, "bot_mode", "") or ""),
            "frame": int(getattr(context, "frame", 0) or 0),
            # The dashboard WAITS on this before it copies anything.
            "parked": self._parked,
        }
        # Logging state travels with every frame, so the dashboard can show at a glance
        # whether a lane is actually producing the logs it exists to produce.
        if self._log_path:
            status["log"] = os.path.basename(self._log_path)
            try:
                status["log_bytes"] = os.path.getsize(self._log_path)
            except Exception:
                pass
        else:
            status["log"] = None

        try:
            from modules.pokemon_party import get_party

            party = list(get_party())
            lead = next((mon for mon in party if mon is not None and not mon.is_egg), None)
            if lead is not None:
                status["party"] = f"{lead.name} L{lead.level}  {lead.current_hp}/{lead.total_hp}"
            status["team"] = [self._mon_payload(mon) for mon in party if mon is not None]
        except Exception:
            pass
        try:
            from modules.player import get_player_location

            game_map, coords = get_player_location()
            status["where"] = f"{getattr(game_map, 'name', game_map)} {coords}"
        except Exception:
            pass
        return status

    @staticmethod
    def _mon_payload(mon) -> dict:
        """Serialise one party member. Lives in `modules/remote_party.py` because the badge
        log freezes the same shape at the moment a badge is earned."""
        from modules.remote_party import mon_payload

        return mon_payload(mon)
