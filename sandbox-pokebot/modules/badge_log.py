"""Record WHAT THE TEAM WAS at the moment each badge was earned (punch-list #24-badges).

WHY THIS EXISTS NOW, AHEAD OF ITS UI
------------------------------------
The user asked for a trainer-card overlay: the eight Hoenn badges laid out like a badge
case, silhouetted until earned, and — the part that needs this module — "if defeating
them, logs what my team was when I beat it".

The overlay can be built at any time. This capture cannot: it only ever records badges
earned AFTER it is switched on. Every ENDLESS LOOP x4 run in the meantime would otherwise
produce badge wins that can never be reconstructed, because nothing in the save tells you
what the party looked like at the instant a flag flipped. So the recorder ships first and
the UI reads whatever has accumulated by the time it lands.

WHERE IT WRITES
---------------
`<profile>/badge-log.json` — one file per profile, so an x4 batch yields four independent
badge histories (P1 Torchic's Roxanne team vs P4's, and so on) with no extra plumbing.

The file is a LIST of records, appended across runs and never rewritten, because a batch
plays the story many times: comparing the Roxanne-winning team across twenty runs is
exactly the question this is for. Each record carries `run_started_frame` so records from
one playthrough can be grouped.

COST
----
Eight event-flag reads every `_POLL_INTERVAL` frames. Badge acquisition is a human-scale
event; frame precision buys nothing, and a batch runs unthrottled where per-frame memory
reads on four lanes would not be free.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path

#: Hoenn badges in gym order, DERIVED from the single canonical table in
#: `modules/badge_case.py` so the two can never drift.
#:
#: ‼ THIS TABLE USED TO BE A SECOND, HAND-WRITTEN COPY AND IT WAS WRONG: it named WALLACE
#: as the Sootopolis leader, which is Ruby/Sapphire. In EMERALD the 8th leader is JUAN and
#: Wallace is the Champion (`src/data/trainers.h:3268-3278` vs `:4024-4034`). Any
#: `badge-log.json` record written before 2026-07-26 carries the wrong `leader` string for
#: BADGE08; the `flag` and `team` fields in those records are unaffected.
#:
#: ‼ DERIVED ON EVERY ACCESS, not snapshotted at import. `BADGES = tuple(... badge_case
#: .BADGES ...)` at module level looked equivalent and was not: it froze whatever the
#: canonical table held at first import, so the two COULD drift — which is precisely what
#: the "no second copy to drift" test caught.
def badge_table() -> tuple[tuple[str, str, str, str, str], ...]:
    """(flag, badge, leader, city, sprite) for each badge, from the canonical table."""
    from modules.badge_case import BADGES as info

    return tuple((b.flag, b.badge, b.leader, b.city, b.sprite) for b in info)


def __getattr__(name: str):
    """Keep `badge_log.BADGES` working as a read-only, always-current view."""
    if name == "BADGES":
        return badge_table()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

_FILENAME = "badge-log.json"

#: How often to poll the badge flags, in frames. ~1s at 60fps.
_POLL_INTERVAL = 60

# --- module state (per process; a lane is its own process) -------------------
_known: set[str] | None = None      # flags already seen set, so a flip fires once
_pending: set[str] | None = None    # flags seen set on the PREVIOUS poll but not yet confirmed
_recorded_this_run: set[str] = set()
_last_poll_frame: int = -1
_run_started_frame: int = 0
_run_index: int = 0


def reset_for_new_run(frame: int = 0) -> None:
    """Called when a fresh playthrough begins, so records can be grouped by run.

    ‼ Also clears `_known` and `_recorded_this_run`. The endless mode hard-resets the
    emulator between runs, taking every badge flag back to 0; without clearing, the SECOND
    run's Stone Badge would be treated as already-known and never recorded.

    ‼ CALL THIS FROM THE MODE, NOT ONLY FROM FRAME-COUNT DETECTION. `modules/main.py` also
    calls it when the frame counter goes backwards, but the user's 2026-07-26 bundle showed
    that is unreliable: P4 started two runs and every one of its 14 records still carried
    `run_started_frame=0`, so run grouping silently collapsed. The endless mode knows
    exactly when a run begins and says so.
    """
    global _known, _pending, _recorded_this_run, _run_started_frame, _last_poll_frame, _run_index

    # ‼ DEDUPE: this is called TWICE for the same run — `modules/main.py` when the frame
    # counter goes backwards (the hard reset), and `StoryEndlessResetMode` immediately
    # afterwards as the authoritative signal. Both callers are wanted, but counting both
    # made `run_index` advance by two per run: the user's 20:18 bundle shows run_index
    # 1, 3, 5, 7, 9 and no even numbers.
    #
    # The signal is "has anything HAPPENED since the last reset?" — `_last_poll_frame` is
    # set to -1 here and to a real frame by the first poll, so two resets with no poll
    # between them are one boundary.
    #
    # ‼ Two rejected alternatives, both worse: deduping on FRAME distance is actively wrong
    # because `get_frame_count()` resets with the emulator, so every run starts near 0 and
    # every boundary would have looked like a duplicate — it would have merged an entire
    # batch into one run. Deduping on WALL-CLOCK works in production but makes the function
    # untestable without sleeping. This version is deterministic and needs no clock.
    if _run_index and _last_poll_frame < 0:
        return

    _known = None
    _pending = None
    _recorded_this_run = set()
    _last_poll_frame = -1
    _run_started_frame = int(frame)
    _run_index += 1


def known_badges() -> set[str]:
    """The badge flags currently set, as of the last poll.

    Served from the poll cache rather than re-reading memory: the badge case reads this
    at UI refresh rates and during an x4 batch every lane publishes it every frame, and
    eight fresh memory reads at that cadence would be pure waste. `None` (no poll yet)
    reads as "nothing known", which is correct — the caller shows an empty case until the
    first poll lands about a second later.
    """
    return set(_known) if _known else set()


def log_path(profile=None) -> Path | None:
    try:
        if profile is None:
            from modules.context import context

            profile = context.profile
        return Path(profile.path) / _FILENAME
    except Exception:
        return None


def read_log(profile=None) -> list[dict]:
    """Every badge record for a profile, oldest first. Never raises."""
    path = log_path(profile)
    if path is None or not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def on_frame(frame: int) -> None:
    """Poll the badge flags and record any that have just been earned.

    Fully guarded: this runs on the emulator's hot path and must never be able to break or
    slow a run. Called from `modules/main.py`'s frame loop.
    """
    global _known, _pending, _last_poll_frame

    try:
        if _last_poll_frame >= 0 and frame - _last_poll_frame < _POLL_INTERVAL:
            return
        _last_poll_frame = frame

        from modules.memory import get_event_flag

        current = {flag for flag, *_ in badge_table() if get_event_flag(flag)}

        if _known is None:
            # First poll of a run: adopt whatever is already set WITHOUT recording it.
            # Loading a mid-game save would otherwise fabricate "just earned" records for
            # badges won long ago, with today's team attached to them. Adopting into
            # `_recorded_this_run` (not a separate "seen" set) is what makes that stick.
            _known = set(current)
            _pending = set(current)
            _recorded_this_run.update(current)
            return

        # ---- FILTER 1: DEBOUNCE ------------------------------------------------
        # ‼ Badge flags live in the save block, and during a map warp the save-block reads
        # return GARBAGE for a frame or two. The user's 2026-07-26 bundle is unambiguous:
        # the debug log shows the map itself flipping to nonsense in the same window
        # (`f1190097 [MAP] MAUVILLE CITY(0,2) -> MAUVILLE CITY(10,5)` and back four frames
        # later), and the badge poll landing there produced a BALANCE badge — the 5th —
        # in a run that had only reached the 2nd, plus Stone/Knuckle "re-earned" in pairs.
        # P1 recorded the Stone Badge TEN TIMES inside a SINGLE run.
        # A flag must therefore read set on two CONSECUTIVE polls (60 frames apart) before
        # it counts. No warp transient survives that.
        confirmed = current & (_pending if _pending is not None else set())
        _pending = set(current)

        # `_known` is the DISPLAY set (`known_badges()`): debounced, and monotonic within a
        # run because a badge cannot be un-earned. It deliberately plays no part in
        # deciding what to RECORD — an earlier version used it for that, and a badge
        # rejected by the gym-order filter got absorbed into it and could then never be
        # recorded even once its predecessors legitimately arrived. `_recorded_this_run` is
        # the only thing that suppresses a write.
        _known = _known | confirmed

        for flag in sorted(confirmed):
            # ---- FILTER 2: ONCE PER RUN ---------------------------------------
            # A badge cannot be earned twice in one playthrough. Anything claiming
            # otherwise is a flag that flickered off and back on.
            if flag in _recorded_this_run:
                continue

            # ---- FILTER 3: GYM ORDER ------------------------------------------
            # Hoenn's gyms are gated linearly (Petalburg alone demands four badges), so a
            # badge whose predecessors are not also set is a corrupt read, not a win.
            if not _predecessors_set(flag, current):
                continue

            _recorded_this_run.add(flag)
            _record(flag, frame)
    except Exception:
        pass


def _predecessors_set(flag: str, current: set[str]) -> bool:
    """True if every badge before `flag` in gym order is also currently set."""
    order = [row[0] for row in badge_table()]
    try:
        index = order.index(flag)
    except ValueError:
        return True
    return all(earlier in current for earlier in order[:index])


def _record(flag: str, frame: int) -> None:
    from modules.context import context
    from modules.remote_party import mon_payload

    meta = next((b for b in badge_table() if b[0] == flag), None)
    record = {
        "flag": flag,
        "badge": meta[1] if meta else flag,
        "leader": meta[2] if meta else "?",
        "city": meta[3] if meta else "?",
        "earned_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "frame": int(frame),
        "run_started_frame": _run_started_frame,
        # ‼ Group by THIS, not by run_started_frame. The frame-count reset heuristic proved
        # unreliable in the user's 2026-07-26 bundle (P4 ran twice; every record still said
        # run_started_frame=0), so records collapsed into one apparent run. `run_index` is
        # incremented by `reset_for_new_run()`, which the endless mode now calls directly.
        "run_index": _run_index,
        "team": [],
    }
    try:
        from modules.pokemon_party import get_party

        record["team"] = [mon_payload(mon) for mon in get_party() if mon is not None]
    except Exception:
        pass

    path = log_path()
    if path is None:
        return
    try:
        existing = read_log()
        existing.append(record)
        path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    except Exception:
        return

    try:
        from modules.console import console

        lead = record["team"][0]["name"] if record["team"] else "?"
        console.print(
            f"[bold green]BADGE: {record['badge']} Badge ({record['leader']}, {record['city']}) — "
            f"team of {len(record['team'])}, lead {lead}. Logged to {path.name}.[/]"
        )
    except Exception:
        pass
