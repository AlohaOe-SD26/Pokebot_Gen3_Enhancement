"""TEST SIDE (build step 5.2, G2): THE SEED + BOUNDS LEDGER of the graded sweeps (`gates/ledger.json`, committed).

    py -3.12 ai_player/gates/ledger.py              every entry, one line each
    py -3.12 ai_player/gates/ledger.py --check      the ledger is well formed (exit 0) or what is wrong (exit 1)
    (registering a graded range is the driver's: `rate_step5.py --purpose graded --first-seed 901 --seeds 20 --register`)

WHY (the lessons draft, PF-7 and PF-8; the step-5.1 rounds moved 401-410 to 501-520 to 601-620 to 701-720 to 801-820
"because the earlier seeds' results were known"): "held-out" and "pre-registered" were a DOCSTRING, and `rate_step5.py
--first-seed` defaulted to 1, a development seed, so a graded sweep with default arguments played development seeds and
said nothing. Now every sweep of a family (the story's: `rate_step5.py` and its successors) declares its PURPOSE and is
written here, and:
  * a GRADED run must have been REGISTERED first, for exactly its seed range, with the sha256 of the numbers it is graded
    by (`bounds_sha256`, of the driver's `registered_numbers()`); it is REFUSED when no registration exists, when the numbers
    differ from the registered ones (a bound changed after registration), or when its seeds overlap ANY other entry
    (development, an earlier graded run, a replay): a held-out seed is played once;
  * a REGISTRATION is refused when its range overlaps an entry already played; re-registering the SAME unplayed range (the
    numbers changed before any run) is allowed and kept in its `history`;
  * a DEVELOPMENT run is refused on seeds registered for a graded run not yet played (it would spend them);
  * a REPLAY is allowed only on seeds already played, and is written and reported as a replay, never a second measurement
    (CLAUDE.md rule 8);
  * the entry is written when the run STARTS (status "started": a crash still spends the seeds) and completed at its end
    (status "done", the verdict, the evidence file).
(Build step 5.3, A1-3: the step-5.3 critic's Q5 item 7, "a verdict function can change between `--register` and the run")
the numbers a graded run is compared by now include the sha256 of the CHECK CODE (`rate_step5.HASHED_FILES`: the grader,
the live grader, the harness, the screen window, the check table) and of the files a verdict reads (the mark set, the item
flags, the B1 debt and waiver lists, the map table), the mutant edit texts and the harness's parameters. This module's rule
is unchanged (`begin` refuses a graded run whose numbers sha differs from its registration); what it compares now covers the
code. `test_step53_a1.LedgerHashTests` registers a range, edits the check code, and sees the run refused.
The ledger is a RECORD, not the code under test: `provenance.py` leaves it out of the working-tree digest and the frozen-tree
watch (a graded run writes it at its start and end). Writes go through a lock file beside it (`ledger.json.lock`).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = Path(__file__).resolve().parent / "ledger.json"
PURPOSES = ("development", "graded", "replay")
STATUSES = ("registered", "started", "done")
LOCK_WAIT = 60.0


class Refused(Exception):
    """A run the ledger refuses: its message says why and what to do instead."""


def numbers_sha256(numbers: dict) -> str:
    """The sha256 of the numbers a run is graded by (JSON, keys sorted: the same numbers give the same hash)."""
    return hashlib.sha256(json.dumps(numbers, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def load(path: Path = LEDGER) -> dict:
    if not path.is_file():
        return {"what": "", "entries": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(data: dict, path: Path) -> None:
    lines = ["{", f'  "what": {json.dumps(data.get("what", ""), ensure_ascii=False)},', '  "entries": [']
    entries = data.get("entries", [])
    for at, entry in enumerate(entries):
        lines.append("    " + json.dumps(entry, ensure_ascii=False, sort_keys=False) + ("," if at < len(entries) - 1 else ""))
    lines += ["  ]", "}"]
    temp = path.with_name(path.name + ".tmp")
    temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temp, path)


@contextlib.contextmanager
def _locked(path: Path):
    lock = path.with_name(path.name + ".lock")
    began = time.monotonic()
    while True:
        try:
            handle = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() - began > LOCK_WAIT:
                raise Refused(f"the ledger is locked ({lock} exists for over {LOCK_WAIT:.0f}s): another sweep is writing it, "
                              f"or one died while writing (then delete the lock file)")
            time.sleep(0.2)
    try:
        os.write(handle, f"{os.getpid()}\n".encode())
        os.close(handle)
        yield
    finally:
        with contextlib.suppress(OSError):
            lock.unlink()


def _overlap(entry: dict, first: int, last: int) -> bool:
    return entry["first"] <= last and first <= entry["last"]


def _span(entry: dict) -> str:
    return f"{entry['first']}-{entry['last']}" if entry["first"] != entry["last"] else str(entry["first"])


def _show(entry: dict) -> str:
    return (f"#{entry['id']} {entry['purpose']} {entry['family']} seeds {_span(entry)} ({entry['status']}"
            f"{', tree ' + entry['tree'] if entry.get('tree') else ''}{', ' + entry['verdict'] if entry.get('verdict') else ''})")


def _today() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def register(family: str, driver: str, first: int, last: int, bounds: str, note: str = "",
             path: Path = LEDGER) -> dict:
    """Pre-register a GRADED range: refused when it overlaps an entry already played (or another registration); the SAME
    unplayed range registered again takes the new numbers' hash, the old one kept in `history`."""
    if first > last or first < 1:
        raise Refused(f"no seeds in {first}-{last}")
    with _locked(path):
        data = load(path)
        entries = data.setdefault("entries", [])
        same = [e for e in entries if e["family"] == family and e["purpose"] == "graded" and e["status"] == "registered"
                and e["first"] == first and e["last"] == last]
        other = [e for e in entries if e["family"] == family and _overlap(e, first, last) and e not in same]
        if other:
            raise Refused(f"seeds {first}-{last} overlap {[_show(e) for e in other]}: a held-out seed is played once. "
                          f"Register NEW seeds no entry names (the ledger: py -3.12 ai_player/gates/ledger.py)")
        if same:
            entry = same[0]
            if entry["bounds_sha256"] != bounds:
                entry.setdefault("history", []).append({"bounds_sha256": entry["bounds_sha256"],
                                                        "registered": entry["registered"]})
                entry.update({"bounds_sha256": bounds, "registered": _today(), "note": note or entry.get("note", "")})
        else:
            entry = {"id": max((e["id"] for e in entries), default=0) + 1, "family": family, "driver": driver,
                     "purpose": "graded", "first": first, "last": last, "status": "registered", "registered": _today(),
                     "bounds_sha256": bounds, "tree": None, "started": None, "ended": None, "verdict": None,
                     "evidence": None, "note": note}
            entries.append(entry)
        _save(data, path)
        return entry


def begin(family: str, driver: str, purpose: str, first: int, last: int, bounds: str, tree: str | None,
          note: str = "", path: Path = LEDGER) -> tuple[dict, list[str]]:
    """A run of `purpose` on seeds `first`-`last` STARTS: refused (`Refused`) by the rules of the module docstring, else
    written (status "started") and returned with the evidence header's lines."""
    if purpose not in PURPOSES:
        raise Refused(f"purpose {purpose!r}: one of {PURPOSES}")
    if first > last or first < 1:
        raise Refused(f"no seeds in {first}-{last}")
    with _locked(path):
        data = load(path)
        entries = data.setdefault("entries", [])
        family_entries = [e for e in entries if e["family"] == family]
        lines: list[str] = []
        if purpose == "graded":
            mine = [e for e in family_entries if e["purpose"] == "graded" and e["status"] == "registered"
                    and e["first"] == first and e["last"] == last]
            if not mine:
                raise Refused(f"a GRADED run on seeds {first}-{last} was never REGISTERED: pre-register it first (before any "
                              f"run, with the bounds it is graded by): py -3.12 ai_player/gates/{driver}.py --purpose graded "
                              f"--first-seed {first} --seeds {last - first + 1} --register")
            entry = mine[0]
            if entry["bounds_sha256"] != bounds:
                raise Refused(f"the numbers this run is graded by (sha256 {bounds[:16]}) are NOT the ones registered for seeds "
                              f"{first}-{last} on {entry['registered']} (sha256 {entry['bounds_sha256'][:16]}): a bound changed "
                              f"after registration. Restore it, or re-register this unplayed range BEFORE the run (never to "
                              f"pass a check: the user's rule, never loosen a bound to pass)")
            other = [e for e in family_entries if e is not entry and _overlap(e, first, last)]
            if other:
                raise Refused(f"seeds {first}-{last} overlap {[_show(e) for e in other]}: a held-out seed is played once")
            entry.update({"status": "started", "started": _today(), "tree": tree})
            lines.append(f"SEED LEDGER: GRADED, HELD-OUT seeds {first}-{last} (ledger entry #{entry['id']}), REGISTERED "
                         f"{entry['registered']} with the bounds sha256 {entry['bounds_sha256'][:16]}; this run's bounds sha256 "
                         f"{bounds[:16]} (the same); no other entry of family {family!r} names any of these seeds")
        elif purpose == "development":
            reserved = [e for e in family_entries if e["status"] == "registered" and _overlap(e, first, last)]
            if reserved:
                raise Refused(f"seeds {first}-{last} overlap {[_show(e) for e in reserved]}, REGISTERED for a graded run not "
                              f"played yet: a development run would spend them. Develop on other seeds")
            entry = {"id": max((e["id"] for e in entries), default=0) + 1, "family": family, "driver": driver,
                     "purpose": "development", "first": first, "last": last, "status": "started", "registered": None,
                     "bounds_sha256": bounds, "tree": tree, "started": _today(), "ended": None, "verdict": None,
                     "evidence": None, "note": note}
            entries.append(entry)
            lines.append(f"SEED LEDGER: DEVELOPMENT, seeds {first}-{last} (ledger entry #{entry['id']}): NOT a graded result; "
                         f"these seeds can never be graded now")
        else:
            played = [e for e in family_entries if e["status"] in ("started", "done") and _overlap(e, first, last)]
            unplayed = [s for s in range(first, last + 1) if not any(e["first"] <= s <= e["last"] for e in played)]
            if unplayed:
                raise Refused(f"seeds {unplayed[:10]} were never played (no started or done entry names them): that is not a "
                              f"replay. Use --purpose development, or register a graded run")
            entry = {"id": max((e["id"] for e in entries), default=0) + 1, "family": family, "driver": driver,
                     "purpose": "replay", "first": first, "last": last, "status": "started", "registered": None,
                     "bounds_sha256": bounds, "tree": tree, "started": _today(), "ended": None, "verdict": None,
                     "evidence": None, "note": note, "replays": [e["id"] for e in played]}
            entries.append(entry)
            lines.append(f"SEED LEDGER: a REPLAY of seeds {first}-{last} (ledger entry #{entry['id']}), already played in "
                         f"{[_show(e) for e in played]}: a REPLAY, never a second measurement (CLAUDE.md rule 8)")
        _save(data, path)
        return entry, lines


def finish(entry_id: int, verdict: str, evidence: str | None, path: Path = LEDGER) -> None:
    """The run of entry `entry_id` ENDED: its verdict and evidence file are written, status "done"."""
    with _locked(path):
        data = load(path)
        for entry in data.get("entries", []):
            if entry["id"] == entry_id:
                entry.update({"status": "done", "ended": _today(), "verdict": verdict, "evidence": evidence})
                break
        else:
            raise Refused(f"no ledger entry #{entry_id}")
        _save(data, path)


def label(purpose: str) -> str:
    """How a verdict line names its run's purpose: a development or replay verdict never reads as a graded one."""
    return {"graded": "GRADED", "development": "DEVELOPMENT, not graded", "replay": "REPLAY, not a measurement"}[purpose]


def check(data: dict) -> list[str]:
    """What is wrong with a ledger (empty: well formed)."""
    problems = []
    entries = data.get("entries", [])
    ids = [e.get("id") for e in entries]
    if len(set(ids)) != len(ids):
        problems.append(f"duplicate ids {ids}")
    for entry in entries:
        missing = [k for k in ("id", "family", "driver", "purpose", "first", "last", "status") if k not in entry]
        if missing:
            problems.append(f"entry {entry.get('id')}: missing {missing}")
            continue
        if entry["purpose"] not in PURPOSES or entry["status"] not in STATUSES:
            problems.append(f"entry {entry['id']}: purpose {entry['purpose']!r} / status {entry['status']!r}")
        if entry["first"] > entry["last"]:
            problems.append(f"entry {entry['id']}: first {entry['first']} > last {entry['last']}")
        if entry["purpose"] == "graded" and entry["status"] in ("registered", "started") and not entry.get("bounds_sha256"):
            problems.append(f"entry {entry['id']}: a graded range with no bounds sha256")
    graded = [e for e in entries if e.get("purpose") == "graded"]
    for at, a in enumerate(graded):
        for b in graded[at + 1:]:
            if a["family"] == b["family"] and _overlap(a, b["first"], b["last"]):
                problems.append(f"graded entries {a['id']} and {b['id']} overlap: a held-out seed was graded twice")
    return problems


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    args = parser.parse_args()
    data = load(args.ledger)
    if args.check:
        problems = check(data)
        print(f"LEDGER {args.ledger.name}: {len(data.get('entries', []))} entries; "
              f"{'well formed -> PASS' if not problems else 'FAIL: ' + '; '.join(problems)}")
        return 0 if not problems else 1
    for entry in data.get("entries", []):
        print(_show(entry) + (f"  {entry.get('note', '')[:140]}" if entry.get("note") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
