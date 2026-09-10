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

#: ‼ IN-BATTLE stall threshold. A battle legitimately holds still mid-turn and during the EXP
#: fill, so the 300-frame overworld threshold would false-trigger on every turn — which is why
#: stall detection used to be disabled OUTRIGHT while `battle_active`. That made the detector
#: STRUCTURALLY BLIND to an in-battle wedge.
#:
#: MEASURED (user log `20260729-122709`): a mid-battle rotation wedged the PARTY MENU in
#: Fortree Gym. The run then sat at `state=3 controllable=False`, one fixed position, for
#: **~280,000 frames** and emitted **ZERO stuck dumps** — no generator stack, nothing to
#: diagnose from. The frame budget would eventually have ended the run (at 3.5M; it was at
#: 2.78M), but a budget only STOPS a wedge, it cannot tell you where it was.
#:
#: 18,000 frames = 5 minutes of real time at 60fps. The longest legitimate quiet stretch in a
#: battle is an EXP fill plus level-up/move-learn dialogue — thousands of frames at worst, and
#: a two-order-of-magnitude margin keeps this from crying wolf. A battle whose entire observed
#: state is unchanged for five minutes is wedged, not thinking.
_BATTLE_STALL_DUMP_AFTER = 18_000

#: ‼ AND AFTER THIS, STOP IT (KI-36). Diagnosis without termination is what let one lane burn
#: 25,632,106 frames — 5x the per-run cap — while the batch reported `frame-cap=0`.
#:
#: WHY THE PER-RUN FRAME BUDGET CANNOT DO THIS. `StoryEndlessResetMode._run_with_frame_budget`
#: is a GENERATOR WRAPPER, and the controller stack is FLAT: `main_loop` advances only the TOP
#: generator. During that 25.6M-frame wedge the stack was
#: `[StoryEndlessResetMode.run, TrainerApproachListener.handle_trainer_approach,
#: BattleListener.fight]` in 8,022 of ~8,200 samples — so the story generator, and its budget,
#: was never stepped. The budget is structurally blind to the one failure class it was written
#: for, because every wedge we have is inside a battle handler.
#:
#: THIS module is not. `on_frame()` is called from `modules/main.py` as a per-frame LISTENER,
#: so it keeps sampling no matter what sits on top of the stack — which is exactly why the
#: stall DUMPS worked when the budget did not. So the thing that already NOTICES becomes the
#: thing that ENDS it, through the designed channel (`modules/battle_fault.py`): the mode
#: claims a recoverable derail and the endless loop starts the next run.
#:
#: 60,000 frames ≈ 16 minutes of real time at 60fps, and >3x the dump threshold: by then the
#: state has been byte-identical for over three re-dumps. A legitimate battle cannot do that.
#: ‼ LIMITATION, STATED: this only works while debug logging is ON. It is a net for batch runs
#: (which always enable it), NOT a general-purpose watchdog. A stack-independent budget in
#: `main_loop` remains the complete fix — see KI-36.
_BATTLE_STALL_FAULT_AFTER = 60_000
_HEARTBEAT_EVERY = 3600               # periodic state line even without events

#: last observed National-Dex OWNED set, sampled on the heartbeat only. `None` = never read.
#: ⛔ SAMPLED, NOT HOOKED: `Pokedex.owned_species` scans 412 indices and builds a Species per hit
#: (`modules/pokedex.py:42-52`), so this must never move into `_light_state`, which runs EVERY
#: FRAME. At heartbeat cadence it is ~1 read/minute; per-frame it would be a 412-iteration scan on
#: the hot path. ‼ Consequence, stated honestly: a `[DEX]` line can be up to a minute late, and two
#: catches inside one interval are reported together.
_last_owned: "set[int] | None" = None


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


def _git_facts() -> "dict[str, str]":
    """Identify the checkout WITHOUT shelling out to git.

    Reads `.git/HEAD` and the ref file directly: a subprocess costs ~50-150ms on Windows,
    this costs a couple of file reads, and it still works when `git` is not on PATH — which
    is common on a machine that only ever runs the installer.
    """
    facts: dict[str, str] = {}
    try:
        from pathlib import Path

        here = Path(__file__).resolve()
        git_dir = None
        for parent in here.parents:
            candidate = parent / ".git"
            if candidate.is_dir():
                git_dir = candidate
                break
        if git_dir is None:
            return {"repo": "not a git checkout"}
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref = head[5:].strip()
            facts["branch"] = ref.rsplit("/", 1)[-1]
            ref_file = git_dir / ref
            if ref_file.is_file():
                facts["commit"] = ref_file.read_text(encoding="utf-8").strip()[:12]
            else:  # packed-refs
                packed = git_dir / "packed-refs"
                if packed.is_file():
                    for line in packed.read_text(encoding="utf-8").splitlines():
                        if line.endswith(" " + ref):
                            facts["commit"] = line.split(" ", 1)[0][:12]
                            break
        else:  # detached HEAD
            facts["branch"] = "(detached)"
            facts["commit"] = head[:12]
    except Exception as e:  # noqa: BLE001
        facts["repo"] = f"unreadable ({type(e).__name__})"
    return facts


#: Env vars that CHANGE BEHAVIOUR. Any experiment flag added later belongs here, or a log
#: cannot say which arm produced it.
_BEHAVIOUR_ENV_VARS = ("POKEBOT_FODDER_RULE",)


def _write_run_header() -> None:
    """Emit everything needed to identify the build, the config and the experiment.

    ‼ WHY THIS EXISTS (user, 2026-07-29): *"all of this should be native to the debug
    logging... I should not have to make arbitrary cmd commands to do this"*. Correct. The
    header used to be two lines — a timestamp and the log path — so answering "which build
    produced this log?" meant running `git log` on the machine that made it, and answering
    "which experiment arm was this?" was impossible after the fact. Three separate times a
    shared log could not be interpreted without going back to the user.

    A forensic log must be SELF-DESCRIBING. Everything here is wrapped so that a failure to
    read any one fact degrades that line to "unknown" and never blocks logging.
    """
    def _line(label: str, value) -> None:
        _raw(f"    {label:<14} {value}")

    _raw("--- RUN HEADER (build, config, experiment) ---")

    try:
        g = _git_facts()
        if "commit" in g:
            _line("build:", f"{g.get('commit', '?')} on branch {g.get('branch', '?')}")
        else:
            _line("build:", g.get("repo", "unknown"))
    except Exception:  # noqa: BLE001
        _line("build:", "unknown")

    try:
        from modules.version import pokebot_name, pokebot_version

        _line("bot:", f"{pokebot_name} {pokebot_version}")
    except Exception:  # noqa: BLE001
        pass

    try:
        import platform
        import sys

        _line("python:", f"{sys.version.split()[0]} on {platform.system()} {platform.release()}")
    except Exception:  # noqa: BLE001
        pass

    try:
        from modules.context import context

        _line("mode:", context.bot_mode)
        try:
            _line("profile:", context.profile.path.name)
        except Exception:  # noqa: BLE001
            pass
        try:
            rom = context.rom
            _line("rom:", f"{rom.short_name if hasattr(rom, 'short_name') else rom.game_name} "
                          f"({rom.language}) rev {getattr(rom, 'revision', '?')}")
        except Exception:  # noqa: BLE001
            pass
        try:
            _line("emulation:", f"speed={context.emulation_speed} video={context.video} "
                                f"audio={context.audio}")
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001
        pass

    # ‼ EXPERIMENT FLAGS. Without these a log cannot be attributed to a condition, which is
    # the whole point of running an A/B.
    try:
        import os

        from modules.story import training_areas as _ta

        how = "env" if "POKEBOT_FODDER_RULE" in os.environ else "default"
        _line("fodder-rule:", f"{_ta.FODDER_RULE} ({how})"
                              + (f" ratio={_ta.XP_RATE_RELOCATE_RATIO}"
                                 if _ta.FODDER_RULE == "xp_rate" else ""))
    except Exception:  # noqa: BLE001
        pass

    try:
        import os

        set_vars = {k: os.environ[k] for k in _BEHAVIOUR_ENV_VARS if k in os.environ}
        _line("env:", set_vars if set_vars else "(no behaviour env vars set)")
    except Exception:  # noqa: BLE001
        pass

    _raw("--- END RUN HEADER ---")


def enable(profile=None, name_prefix: str | None = None) -> str:
    """Open a fresh log file and start logging. Returns the path (or an error
    string). `profile` defaults to context.profile.

    `name_prefix` is prepended to the filename — ENDLESS LOOP x4 passes the lane tag
    ("P1-", "P2-", ...) so that logs handed over for review say which bot produced
    them without having to open them."""
    global _enabled, _file, _path, _prev, _stall_frames, _last_sig, _last_dump_stall, _last_owned
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
        # ⛔ PER-RUN, NOT PER-PROCESS: an endless-reset batch calls enable() for every run. Without
        # this, run 2's first heartbeat diffs against run 1's dex and its early catches go unlogged.
        _last_owned = None
        _bytes_written = 0
        _capped = False
        _raw(f"=== DEBUG LOG START {now.isoformat(timespec='seconds')} ===")
        _raw(f"    log: {_path}")
        _write_run_header()
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
    global _last_owned
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
    # ‼ A battle is USUALLY progress — its state legitimately holds still mid-turn and during
    # the EXP fill — so it gets a far larger threshold than the overworld. But it is NOT
    # exempt. This branch used to reset `_stall_frames` to 0 on every in-battle frame, which
    # made the detector structurally unable to see an in-battle wedge: the 2026-07-29 Fortree
    # party-menu freeze held one state for ~280,000 frames and produced ZERO dumps, so there
    # was no generator stack to diagnose it from. See `_BATTLE_STALL_DUMP_AFTER`.
    sig = _progress_signature(st)
    in_battle = bool(st.get("battle_active"))
    threshold = _BATTLE_STALL_DUMP_AFTER if in_battle else _STALL_DUMP_AFTER
    if sig == _last_sig:
        _stall_frames += 1
    else:
        if _stall_frames >= threshold:
            _event(fc, f"[RESUMED] after {_stall_frames} frames with no progress")
        _stall_frames = 0
        _last_sig = sig
        _last_dump_stall = 0
    # ‼ TERMINATE a wedge the per-run frame budget cannot see (KI-36). Fires ONCE per stall,
    # only in battle, and only via the recoverable battle-fault channel — never by raising,
    # which on this flat controller stack would drop straight to Manual.
    if in_battle and _stall_frames == _BATTLE_STALL_FAULT_AFTER:
        try:
            from modules.battle_fault import request_mode_recovery

            _reason = (
                f"in-battle wedge: state unchanged for {_stall_frames:,} frames "
                f"(KI-36; the per-run frame budget cannot fire while a battle handler is on "
                f"the controller stack)"
            )
            if request_mode_recovery(_reason):
                _event(fc, f"[STALL] handing a recoverable derail to the mode — {_reason}")
            else:
                _event(fc, f"[STALL] {_reason} — no mode accepted the fault; it will NOT be ended here")
        except Exception:  # noqa: BLE001 - a watchdog must never break the run it watches
            pass

    if _stall_frames == threshold or (
        _stall_frames > threshold and (_stall_frames - _last_dump_stall) >= _STALL_REDUMP_EVERY
    ):
        _last_dump_stall = _stall_frames
        try:
            _dump(f"STUCK — {_stall_frames} frames no progress", st)
        except Exception:
            pass

    # --- heartbeat ---
    if fc is not None and _start_frame is not None and (fc - _start_frame) % _HEARTBEAT_EVERY == 0 and fc != _start_frame:
        # ⛔ THE DEX READ LIVES HERE, NOT IN `_light_state` — it scans 412 indices; see `_last_owned`.
        owned = _safe(_owned_dex, None)
        if owned is not None:
            if _last_owned is not None and owned - _last_owned:
                gained = sorted(owned - _last_owned)
                _event(fc, f"[DEX] owned {len(_last_owned)} -> {len(owned)}: "
                           f"+{', '.join('#%d' % d for d in gained)}")
            _last_owned = owned
        _event(
            fc,
            f"[hb] mode={st.get('mode')} state={st.get('game_state')} "
            f"controllable={st.get('controllable')} map={_fmt_map(st.get('map'))} "
            f"pos={st.get('pos')} party={st.get('party_key')} "
            f"ids={st.get('party_ids')} owned={len(owned) if owned is not None else '?'} "
            f"msg={st.get('message')!r}",
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
            # ‼ PARTY HP AT THE START OF THE BATTLE (`#24-bosstelemetry` part 2, 2026-08-09).
            # `probe_fainted_ace.py` had to INFER the starting party state from the first faint,
            # because nothing recorded it — and that inference produced a ~99% rate that is far
            # more likely a misreading than a fact. This is the direct measurement it needs: what
            # the party's HP actually was when the battle opened. The question it settles matters
            # — `--driver normancounter` showed the bot fighting Norman with its L36 ace already
            # at 0 HP, and if THAT generalises then the counter chain's "no super-effective
            # answer" stop (79% of all non-finishing runs) is a misdiagnosis of fights lost on
            # preparation.
            _hp = ""
            try:
                from modules.pokemon_party import get_party

                _hp = " hp=" + str(
                    [
                        (getattr(getattr(m, "species", None), "name", "?"), m.current_hp, m.total_hp)
                        for m in get_party()
                        if m is not None
                    ]
                )
            except Exception:  # noqa: BLE001 - instrumentation must never affect the battle
                _hp = " hp=<unreadable>"
            _event(fc, f"[BATTLE] started{_hp}")
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


def _owned_dex():
    """National-Dex numbers currently OWNED, or `None` if the dex cannot be read.

    ⛔ CALL ONLY FROM THE HEARTBEAT — see `_last_owned` for why this is not per-frame safe.
    Returns a set of ints so the caller can name exactly which numbers are NEW, which is what makes
    a catching A/B gradeable: a bare count says "something happened", a set says WHAT.
    """
    from modules.pokedex import get_pokedex

    return {s.national_dex_number for s in get_pokedex().owned_species}


def _party_ids():
    """Per-slot IDENTITY + EXP: ``["Species#PID:L<lv>:exp<n>", ...]``.

    ⛔⛔ THIS IS DELIBERATELY **NOT** `_party_key`, AND MUST NEVER BE MERGED INTO IT.
    `_party_key` is `["Species:L<lv>"]` and is consumed by `_detect_events` — a size change is read
    as a CATCH and a per-slot change as a LEVEL-UP/EVOLUTION. Folding PIDs or exp into it would
    change which frames count as a party change: a behaviour change wearing telemetry clothes.
    This field is written to the heartbeat and read by nothing.

    ⭐ WHY IT EXISTS (measured 2026-09-09; scope: `x4-runs` 298 `stdout.txt` + its
    `debug-logs/*.log`, `sandbox-pokebot/profiles` + `tools/story-dev` 500 `*.log` each):
    **no continuous PID-bearing party telemetry existed
    anywhere.** `Species#PID` appeared in 96 stdout lines, ALL of them §Ch23 refusal messages, plus
    ~15 from one-off probes. A Pokemon therefore could not be followed across a run, which blocked
    TWO separate questions that had each already stalled an investigation:
      * whether laggards are BORN behind (reported 88.8%, never reproducible) — this decides whether
        the fix belongs at CATCH time or at TRAINING time;
      * the real EXP split during swap-training (solo vs 2-way), which decides whether §Ch23's bar is
        L35 or L42 — filed as needing "one log line, not more analysis".
    ⇒ identity + exp per slot answers both, from ordinary runs, with no new driver.

    ‼ PID, NOT SLOT. Slots are reshuffled by lead rotation and by `_rotate_lead_safely`, so a
    slot index names a different Pokemon after a swap — this project has three logged bugs from
    asserting on slot indices.

    ⛔⛔ BUT PID IS **NOT UNIQUE**, AND A CONSUMER THAT ASSUMES IT IS WILL SILENTLY MERGE TWO MONS.
    Gen 3 creates **Shedinja as a COPY of Nincada**, so it inherits the parent's personality value:
    after a Nincada evolves, `Ninjask#XXXXXXXX` and `Shedinja#XXXXXXXX` sit in the party carrying
    the SAME PID. **Measured in batch `20260909-160339`: 1,360 heartbeats (7.9%) contain exactly
    this collision** — the only one in that corpus, but a real one.
    ⇒ **key on `(run, PID, species-lineage)`, never on PID alone.** `tools/story-dev/
    probe_laggard_origin.py` shows the pattern; keying on PID alone changes its population from
    63 mons to 61 and shifts every downstream figure.
    ‼ PID still survives EVOLUTION (`Wurmple#AB` -> `Silcoon#AB` is the SAME mon), which is exactly
    why species-name keying is wrong in the other direction: it SPLITS one mon across its
    evolutions and MERGES two mons of one species. Neither key alone is identity; the pair is.
    Cost: `_party_exp` already walks the party every frame for `total_exp`; this adds one attribute
    read per mon, and heartbeats are ~1/3,600 frames.
    """
    from modules.pokemon_party import get_party

    out = []
    for p in get_party():
        if p is None:
            continue
        try:
            pid = getattr(p, "personality_value", None)
            pid_s = f"{pid:08X}" if isinstance(pid, int) else "????????"
            out.append(f"{p.species.name}#{pid_s}:L{p.level}:exp{getattr(p, 'total_exp', 0)}")
        except Exception:  # noqa: BLE001 - telemetry must never break a run
            out.append("<unreadable>")
    return out


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
    # ⛔ SEPARATE FROM `party_key` ON PURPOSE — see `_party_ids`. Read by nothing; logged only.
    d["party_ids"] = _safe(_party_ids)
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
