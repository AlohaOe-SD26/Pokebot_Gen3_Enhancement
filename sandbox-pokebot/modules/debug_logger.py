"""Opt-in extensive run logger (sandbox) — diagnose hard-to-reproduce freezes.

OFF by default. Toggled from the GUI Run (bot-mode) menu. When enabled it writes a
compact, structured diagnostic log to:

    <profile>/debug-logs/<mode>-debug-<YYYYmmdd-HHMMSS>.log

Built for the Story-bot post-battle freeze (Bug #2). It records:

  * an EVENT stream — bot-mode changes (incl. derails to Manual), story-step
    changes (`context.message`), map changes, battle start/end + outcome,
    level-ups / evolutions / catches, move-learn state changes, and explicit
    Story derail/recovery events;
  * automatic STUCK DUMPS — when the game stops making progress for a while, a
    one-shot rich snapshot INCLUDING the running generator's call stack (function
    + line), i.e. the EXACT place the bot is waiting when it froze;
  * periodic heartbeats so the log always shows liveness + current state.

Every line is flushed immediately, so the log is complete even if the process has
to be killed while frozen. Everything is wrapped in try/except and gated by
`is_enabled()`, so this can never slow down or break a normal run.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

# --- module singleton state -------------------------------------------------
_enabled: bool = False
_file = None
_path: Optional[Path] = None

_prev: Optional[dict] = None          # last light snapshot (for change detection)
_stall_frames: int = 0                # consecutive frames with an unchanged sig
_last_sig = None                      # progress signature at the last frame
_last_dump_stall: int = 0             # stall count at which we last dumped (throttle)
_start_frame: Optional[int] = None
_bytes_written: int = 0
_capped: bool = False

# --- tuning -----------------------------------------------------------------
_MAX_BYTES = 30 * 1024 * 1024         # after this, keep STUCK dumps but drop chatter
_STALL_DUMP_AFTER = 300               # frames unchanged before the first stuck dump
_STALL_REDUMP_EVERY = 3000            # while still stalled, re-dump every N frames
_HEARTBEAT_EVERY = 3600               # periodic state line even without events


# ===========================================================================
# Public API
# ===========================================================================
def is_enabled() -> bool:
    return _enabled


def log_path() -> Optional[str]:
    return str(_path) if _path else None


#: A prefix applied to EVERY subsequent log filename. ENDLESS LOOP x4 sets it once per
#: lane so files are self-identifying (`P1-…`).
#: ‼ THIS EXISTS BECAUSE PASSING THE PREFIX PER CALL WAS NOT ENOUGH. The lane frontend
#: enabled logging with `name_prefix="P1-"`, and then `StoryDebugResetMode` re-enabled it
#: per run (`plugins/custom_modes/story_mode.py:2704,2733`) with no prefix — so the tiny
#: startup log was tagged and the REAL story log, the one anyone would actually read, was
#: not. Confirmed in the user's 2026-07-26 bundle: `P1-Manual-debug-*.log` (1 KB) beside an
#: untagged `Story_(ENDLESS_RESET)-debug-*.log` (649 KB). A module-level prefix is picked
#: up by every caller, including ones that know nothing about lanes.
_name_prefix: str = ""


def set_name_prefix(prefix: str) -> None:
    """Tag every subsequent log file. Call once at lane startup."""
    global _name_prefix
    _name_prefix = str(prefix or "")


def enable(profile=None, name_prefix: str | None = None) -> str:
    """Open a fresh log file and start logging. Returns the path (or an error
    string). `profile` defaults to context.profile.

    `name_prefix` is prepended to the filename — ENDLESS LOOP x4 passes the lane tag
    ("P1-", "P2-", ...) so that logs handed over for review say which bot produced
    them without having to open them."""
    global _enabled, _file, _path, _prev, _stall_frames, _last_sig, _last_dump_stall
    global _start_frame, _bytes_written, _capped
    disable()
    try:
        if profile is None:
            from modules.context import context

            profile = context.profile
        base = Path(profile.path) / "debug-logs"
        base.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now()
        ts = now.strftime("%Y%m%d-%H%M%S")
        mode = _safe(_cur_mode) or "run"
        prefix = _name_prefix if name_prefix is None else name_prefix
        _path = base / f"{prefix}{str(mode).replace(' ', '_').replace('/', '-')}-debug-{ts}.log"
        _file = open(_path, "w", encoding="utf-8", buffering=1)  # line-buffered
        _enabled = True
        _prev = None
        _stall_frames = 0
        _last_sig = None
        _last_dump_stall = 0
        _start_frame = None
        _bytes_written = 0
        _capped = False
        _raw(f"=== DEBUG LOG START {now.isoformat(timespec='seconds')} ===")
        _raw(f"    log: {_path}")
        _dump("enable — initial state")
        return str(_path)
    except Exception as e:  # noqa: BLE001
        _enabled = False
        _file = None
        _path = None
        return f"<failed to open debug log: {e}>"


def disable() -> None:
    global _enabled, _file, _path
    if _file is not None:
        try:
            _raw("=== DEBUG LOG END ===")
            _file.close()
        except Exception:
            pass
    _enabled = False
    _file = None
    _path = None


def event(message: str, *, category: str = "STORY") -> None:
    """Log an explicit event from bot code (e.g. Story derail/recovery). No-op
    when logging is off, so callers can invoke it unconditionally."""
    if not _enabled or _file is None:
        return
    fc = _safe(_frame_count)
    _event(fc, f"[{category}] {message}")


def on_frame(frame_info=None) -> None:
    """Called every frame from the main loop (guarded by is_enabled()). Detects
    events, tracks progress, and emits stuck dumps + heartbeats."""
    global _prev, _stall_frames, _last_sig, _last_dump_stall, _start_frame
    if not _enabled or _file is None:
        return
    try:
        st = _light_state()
    except Exception:
        return
    fc = st.get("frame")
    if _start_frame is None and fc is not None:
        _start_frame = fc

    # --- event detection ---
    if _prev is not None:
        try:
            _detect_events(_prev, st)
        except Exception:
            pass

    # --- stall detection ---
    # A battle is always progress (its state legitimately holds still mid-turn /
    # during EXP fill), so never flag a stall while one is active — otherwise every
    # battle turn false-triggers. Bug #2 freezes are in the OVERWORLD after a battle,
    # which this still catches (battle_active is False there).
    sig = _progress_signature(st)
    if st.get("battle_active"):
        if _stall_frames >= _STALL_DUMP_AFTER:
            _event(fc, f"[RESUMED] after {_stall_frames} frames with no progress")
        _stall_frames = 0
        _last_sig = sig
        _last_dump_stall = 0
    elif sig == _last_sig:
        _stall_frames += 1
    else:
        if _stall_frames >= _STALL_DUMP_AFTER:
            _event(fc, f"[RESUMED] after {_stall_frames} frames with no progress")
        _stall_frames = 0
        _last_sig = sig
        _last_dump_stall = 0
    if _stall_frames == _STALL_DUMP_AFTER or (
        _stall_frames > _STALL_DUMP_AFTER and (_stall_frames - _last_dump_stall) >= _STALL_REDUMP_EVERY
    ):
        _last_dump_stall = _stall_frames
        try:
            _dump(f"STUCK — {_stall_frames} frames no progress", st)
        except Exception:
            pass

    # --- heartbeat ---
    if fc is not None and _start_frame is not None and (fc - _start_frame) % _HEARTBEAT_EVERY == 0 and fc != _start_frame:
        _event(
            fc,
            f"[hb] mode={st.get('mode')} state={st.get('game_state')} "
            f"controllable={st.get('controllable')} map={_fmt_map(st.get('map'))} "
            f"pos={st.get('pos')} party={st.get('party_key')} msg={st.get('message')!r}",
        )

    _prev = st


# ===========================================================================
# Internals — writing
# ===========================================================================
def _raw(line: str) -> None:
    global _bytes_written
    if _file is None:
        return
    try:
        s = line if line.endswith("\n") else line + "\n"
        _file.write(s)
        _file.flush()
        _bytes_written += len(s)
    except Exception:
        pass


def _event(frame_count, line: str) -> None:
    global _capped
    if _bytes_written >= _MAX_BYTES:
        if not _capped:
            _capped = True
            _raw("... (event log size cap reached — only STUCK dumps from here) ...")
        return
    _raw(f"f{frame_count} {line}")


def _dump(tag: str, st: Optional[dict] = None) -> None:
    """Write a full, multi-line snapshot including the generator call stack."""
    if st is None:
        st = _safe(_light_state) or {}
    fc = st.get("frame")
    heavy = _safe(_heavy_state) or {}
    lines = [f"f{fc} ===== DUMP [{tag}] ====="]
    lines.append(f"    mode={st.get('mode')}  message={st.get('message')!r}")
    lines.append(f"    game_state={st.get('game_state')}  controllable={st.get('controllable')}")
    lines.append(f"    map={_fmt_map(st.get('map'))}  pos={st.get('pos')}  facing={heavy.get('facing')}")
    lines.append(
        f"    battle: active={st.get('battle_active')}  callback={heavy.get('battle_cb')}  "
        f"instr={heavy.get('battle_instr')}"
    )
    lines.append(f"    battle_text={heavy.get('battle_text')!r}  learn_state={st.get('learn_state')}")
    lines.append(f"    party={heavy.get('party') or st.get('party_key')}")
    lines.append(f"    held_buttons={heavy.get('held_buttons')}")
    lines.append(f"    controllers={heavy.get('controllers')}")
    lines.append(f"    tasks={heavy.get('tasks')}")
    lines.append(f"    scripts={heavy.get('scripts')}")
    lines.append("    generator call stack (where the bot is waiting):")
    for entry in heavy.get("gen_stack") or ["<none>"]:
        lines.append(f"      -> {entry}")
    for ln in lines:
        _raw(ln)


def _detect_events(prev: dict, st: dict) -> None:
    fc = st.get("frame")
    if prev.get("mode") != st.get("mode"):
        # A change to Manual is almost always a derail — the reason is in message.
        _event(fc, f"[MODE] {prev.get('mode')} -> {st.get('mode')}   (message={st.get('message')!r})")
    if prev.get("message") != st.get("message"):
        _event(fc, f"[STEP] {st.get('message')!r}")
    if prev.get("map") != st.get("map"):
        _event(fc, f"[MAP] {_fmt_map(prev.get('map'))} -> {_fmt_map(st.get('map'))} pos={st.get('pos')}")
    if prev.get("battle_active") != st.get("battle_active"):
        if st.get("battle_active"):
            _event(fc, "[BATTLE] started")
        else:
            _event(fc, f"[BATTLE] ended (outcome={_safe(_last_outcome)}) party={st.get('party_key')}")
    # party: level-up / evolution / size (catch)
    p0 = prev.get("party_key") or []
    p1 = st.get("party_key") or []
    if len(p0) != len(p1):
        _event(fc, f"[PARTY] size {len(p0)} -> {len(p1)}: {p1}")
    else:
        for i, (a, b) in enumerate(zip(p0, p1)):
            if a != b:
                _event(fc, f"[PARTY] slot{i} {a} -> {b}")
    if prev.get("learn_state") != st.get("learn_state"):
        _event(fc, f"[LEARN] {prev.get('learn_state')} -> {st.get('learn_state')}")
    if prev.get("balls") != st.get("balls"):
        _event(fc, f"[BALLS] {prev.get('balls')} -> {st.get('balls')}")


# ===========================================================================
# Internals — reading game/bot state (all guarded)
# ===========================================================================
def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _cur_mode():
    from modules.context import context

    return context.bot_mode


def _frame_count():
    from modules.context import context

    return context.emulator.get_frame_count()


def _controllable():
    from modules.player import player_avatar_is_controllable

    return bool(player_avatar_is_controllable())


def _map_data():
    from modules.map import get_map_data_for_current_position

    d = get_map_data_for_current_position()
    return (d.map_group, d.map_number, getattr(d, "map_name", None))


def _fmt_map(m):
    if not m:
        return None
    try:
        return f"{m[2]}({m[0]},{m[1]})"
    except Exception:
        return str(m)


def _pos_facing():
    from modules.player import get_player_avatar

    a = get_player_avatar()
    return (tuple(a.local_coordinates), str(getattr(a, "facing_direction", "?")))


def _battle_active():
    from modules.battle_state import battle_is_active

    return bool(battle_is_active())


def _last_outcome():
    from modules.battle_state import get_last_battle_outcome

    return str(get_last_battle_outcome())


def _learn_state():
    from modules.battle_move_replacing import get_learn_move_state

    return str(get_learn_move_state())


def _party_key():
    from modules.pokemon_party import get_party

    return [f"{p.species.name}:L{p.level}" for p in get_party()]


def _party_exp():
    from modules.pokemon_party import get_party

    return sum(getattr(p, "total_exp", 0) for p in get_party())


def _light_state() -> dict:
    """Cheap per-frame read: everything needed for stall detection + event
    detection. Heavier reads (tasks, battle text, generator stack) happen only
    in _dump()."""
    from modules.context import context
    from modules.memory import get_game_state

    d: dict = {}
    d["frame"] = _safe(_frame_count)
    d["mode"] = _safe(lambda: context.bot_mode)
    d["message"] = _safe(lambda: context.message)
    gs = _safe(get_game_state)
    d["game_state"] = str(gs) if gs is not None else None
    d["controllable"] = _safe(_controllable)
    d["map"] = _safe(_map_data)
    d["pos"] = _safe(lambda: _pos_facing()[0])
    d["battle_active"] = _safe(_battle_active)
    d["learn_state"] = _safe(_learn_state)
    d["party_key"] = _safe(_party_key)
    d["party_exp"] = _safe(_party_exp)
    d["balls"] = _safe(_ball_count)
    return d


def _ball_count():
    from modules.items import get_item_bag

    return sum(s.quantity for s in get_item_bag().poke_balls)


def _heavy_state() -> dict:
    from modules.context import context

    d: dict = {}
    d["facing"] = _safe(lambda: _pos_facing()[1])
    d["battle_cb"] = _safe(_battle_callback)
    d["battle_instr"] = _safe(_battle_instr)
    d["battle_text"] = _safe(_battle_text)
    d["party"] = _safe(_party_full)
    d["held_buttons"] = _safe(_held_buttons)
    d["controllers"] = _safe(lambda: [_qual(g) for g in context.controller_stack])
    d["tasks"] = _safe(_task_names)
    d["scripts"] = _safe(_script_names)
    d["gen_stack"] = _safe(_generator_stack)
    return d


def _held_buttons():
    from modules.context import context

    out = []
    for name in ("A", "B", "Up", "Down", "Left", "Right", "Start", "Select", "L", "R"):
        try:
            if context.emulator.is_button_held(name):
                out.append(name)
        except Exception:
            pass
    return out


def _battle_callback():
    from modules.battle_state import get_main_battle_callback

    return get_main_battle_callback()


def _battle_instr():
    from modules.battle_state import get_current_battle_script_instruction

    return get_current_battle_script_instruction()


def _battle_text():
    from modules.game import decode_string
    from modules.memory import read_symbol

    return decode_string(read_symbol("gDisplayedStringBattle"))


def _party_full():
    from modules.pokemon_party import get_party

    return [f"{p.species.name} L{p.level} {p.current_hp}/{p.total_hp}" for p in get_party()]


def _task_names():
    from modules.tasks import get_tasks

    return [getattr(t, "symbol", getattr(t, "name", "?")) for t in get_tasks()]


def _script_names():
    from modules.tasks import get_global_script_context

    ctx = get_global_script_context()
    if ctx is not None and ctx.is_active:
        return list(ctx.stack or [])
    return []


def _qual(gen) -> str:
    return getattr(gen, "__qualname__", type(gen).__name__)


def _generator_stack() -> list:
    """Walk the top controller's yield-from chain down to the deepest active
    frame, so a stuck dump shows the EXACT function + line the bot is waiting at
    (e.g. `heal_in_pokemon_center` blocked in `wait_for_yes_no_question:NN`)."""
    from modules.context import context

    out: list = []
    try:
        stack = context.controller_stack
        if not stack:
            return ["<no controller on the stack (Manual mode / dropped out)>"]
        gen = stack[-1]
        depth = 0
        while gen is not None and depth < 60:
            fr = getattr(gen, "gi_frame", None)
            if fr is None:
                break
            code = fr.f_code
            name = getattr(code, "co_qualname", code.co_name)
            fn = code.co_filename.replace("\\", "/").split("/")[-1]
            out.append(f"{name}  @ {fn}:{fr.f_lineno}")
            nxt = getattr(gen, "gi_yieldfrom", None)
            if nxt is None:
                # A generator DRIVEN via next() (not yield-from) breaks the chain —
                # StoryMode.run's global watchdog drives _play that way. Hop into the
                # driven generator via the frame's local so dumps stay deep.
                for local_name in ("_play_gen", "gen", "generator"):
                    cand = fr.f_locals.get(local_name)
                    if cand is not None and getattr(cand, "gi_frame", None) is not None:
                        nxt = cand
                        break
            gen = nxt
            depth += 1
    except Exception as e:  # noqa: BLE001
        out.append(f"<generator stack walk error: {e}>")
    return out


def _progress_signature(st: dict):
    """A fingerprint that changes during NORMAL play (walking moves pos, battles
    change exp/game_state) but stays CONSTANT during a real freeze — so an
    unchanged signature for many frames means the bot is genuinely stuck."""
    return (
        st.get("map"),
        st.get("pos"),
        st.get("game_state"),
        st.get("controllable"),
        st.get("battle_active"),
        st.get("party_exp"),
        st.get("message"),
    )
