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

#: Hoenn badges in gym order. Flag names verified present in the sandbox's own story code
#: (`modules/story/progress.py`, `modules/capabilities.py`), not guessed.
#: The HM each badge authorises is recorded because it is what makes a badge matter to the
#: bot's routing — `capabilities.py` gates Rock Smash on BADGE03 and Surf on BADGE05.
BADGES: tuple[tuple[str, str, str, str, str], ...] = (
    # (flag,           badge name, leader,        city,       sprite)
    ("BADGE01_GET", "Stone",   "Roxanne",      "Rustboro",  "Stone.png"),
    ("BADGE02_GET", "Knuckle", "Brawly",       "Dewford",   "Knuckle.png"),
    ("BADGE03_GET", "Dynamo",  "Wattson",      "Mauville",  "Dynamo.png"),
    ("BADGE04_GET", "Heat",    "Flannery",     "Lavaridge", "Heat.png"),
    ("BADGE05_GET", "Balance", "Norman",       "Petalburg", "Balance.png"),
    ("BADGE06_GET", "Feather", "Winona",       "Fortree",   "Feather.png"),
    ("BADGE07_GET", "Mind",    "Tate & Liza",  "Mossdeep",  "Mind.png"),
    ("BADGE08_GET", "Rain",    "Wallace",      "Sootopolis", "Rain.png"),
)

_FILENAME = "badge-log.json"

#: How often to poll the badge flags, in frames. ~1s at 60fps.
_POLL_INTERVAL = 60

# --- module state (per process; a lane is its own process) -------------------
_known: set[str] | None = None      # flags already seen set, so a flip fires once
_last_poll_frame: int = -1
_run_started_frame: int = 0


def reset_for_new_run(frame: int = 0) -> None:
    """Called when a fresh playthrough begins, so records can be grouped by run.

    ‼ Also clears `_known`. The endless mode hard-resets the emulator between runs, which
    takes every badge flag back to 0; without clearing, the SECOND run's Stone Badge would
    be treated as already-known and never recorded — the bug that would have made this
    module useless in exactly the batch it was built for.
    """
    global _known, _run_started_frame, _last_poll_frame
    _known = None
    _last_poll_frame = -1
    _run_started_frame = int(frame)


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
    global _known, _last_poll_frame

    try:
        if _last_poll_frame >= 0 and frame - _last_poll_frame < _POLL_INTERVAL:
            return
        _last_poll_frame = frame

        from modules.memory import get_event_flag

        current = {flag for flag, *_ in BADGES if get_event_flag(flag)}

        if _known is None:
            # First poll of a run: adopt whatever is already set WITHOUT recording it.
            # Loading a mid-game save would otherwise fabricate "just earned" records for
            # badges won long ago, with today's team attached to them.
            _known = current
            return

        newly = current - _known
        if not newly:
            _known = current
            return
        _known = current

        for flag in sorted(newly):
            _record(flag, frame)
    except Exception:
        pass


def _record(flag: str, frame: int) -> None:
    from modules.context import context
    from modules.remote_party import mon_payload

    meta = next((b for b in BADGES if b[0] == flag), None)
    record = {
        "flag": flag,
        "badge": meta[1] if meta else flag,
        "leader": meta[2] if meta else "?",
        "city": meta[3] if meta else "?",
        "earned_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "frame": int(frame),
        "run_started_frame": _run_started_frame,
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
