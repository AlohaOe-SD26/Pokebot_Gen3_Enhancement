"""GATE: prove tools/experience/extract_experience.py (spec S3-3, A6) records the bot's games TRUTHFULLY and SAFELY.

    py -3.12 tools/experience/test_extract_experience.py      exit 0 all pass; 1 a FAIL; 4 WARN: no FAIL, but the
                                                              real-data arms were SKIPPED (no learner clone or no
                                                              pinned decomp on this machine): never a pass

WHY THIS EXISTS. The extractor runs unattended over the only copy of data that is being deleted (fact 9), and its
output becomes a prior the AI reads. Its failure modes are silent: a parse that calls a cut-off fight a win, a cut
game counted as a boss wall, a store rewritten over records whose logs are gone, a priors file changed in the middle
of a graded sweep, a PID or a species share leaking into the AI-facing file. Every test pairs a FAULT arm (the bad
condition, which must be caught) with a CONTROL arm (the good one, which must pass), so a test that cannot fail does
not count. Synthetic arms run on a FAKE clone tree in a temp folder; the real clone (`EXPERIENCE_CLONE`, default
C:/Remote Projects/pokebot-learner) is only READ, and its logs are copied before any mutation.

  E1  golden 40-line log (`fixtures/golden.log`): the tier-B record equals a HAND-DERIVED expectation (pre-start lines
      ignored, a won-first-try boss, a lost-twice-then-won boss, a fight cut by the end of the log is incomplete with
      res null). FAULT: the golden with one res flipped no longer equals it.
  E2  REAL cross-check (the control, an independent second source): tier B won/losses per boss equal runs.jsonl's
      boss_log for one real cycle (all raw cycles with EXPERIENCE_E2_ALL=1; `--full` reports every row).
  E3  FAULT one gym's res=Won flipped to res=Lost in a COPY of a real log -> agrees_with_runs_jsonl false, exit 1;
      CONTROL the untouched copy agrees, exit 0. E3b FAULT the copy truncated mid-gym-fight -> that fight is
      incomplete, never Won; CONTROL untruncated -> Won.
  E4  censoring: a Tate & Liza-stuck row marked usable false drops that boss's failure count and the wall count by
      exactly one, moves the row to n_censored, and leaves the bosses it beat unchanged; CONTROL usable true counts
      it. Synthetic AND on the real rows.
  E5  DETERMINISM (one input, replayed; not a replication): two --full runs are byte-identical; --incremental after
      adding one log appends exactly one record and leaves the earlier bytes untouched (prefix sha256); a second
      --incremental changes nothing.
  E6  archive parity: E6a a stdlib zip of the golden cycle; E6b a COPY of one real lane archived by the learner's own
      `archive_cycle` (lane profile included, its debug logs `dup_of` the batch twins): the store from the zip is
      byte-identical to the store from the folder. FAULT: a zip with one member changed gives a different store.
  E7  the privacy gate on the AI-facing file: FAULT a planted PID, position, flag name, species, or a missing
      "bot corpus" label each fail; the writer refuses a failing file (nothing written); a dirty wall label is
      never written (counted as <other>). CONTROL a generated file (and, with the clone, one from the real rows) passes.
  E8  format drift: a >1,000-line log with no [TRAINER] start is parse_suspect; CONTROL with one start, it is not;
      unknown tags are counted, never fatal.
  E10 the digest scope: --incremental on a scratch git repo leaves its ai_player/ digest (provenance.py) unchanged;
      FAULT a priors write into scratch ai_player/ CHANGES the digest (the assertion is not vacuous); FAULT
      --incremental pointed into ai_player/ is REFUSED with the digest unchanged; --incremental --priors is a usage
      error.
  G1-G6, J1  the other guards: --full refuses a non-empty store; a held lock refuses, a stale one is replaced; a torn
      store line or a cursor key missing from the store refuses; a store inside the clone refuses; a decomp whose boss
      ids drift refuses; an incomplete-only boss is adjudicated but a tier-A-absent WIN is still a disagreement; the
      badge-log joins by frame identity (wrong frames are not attached, stale-boot entries are dropped).
ADDED BY THE 2026-10-21 REVIEW FIX (each arm failed on 57a7ec28 or on a mutant that suite let survive):
  P1  a second golden (`fixtures/golden_pairing.log`, hand-derived): a boss start cut off by another start is
      incomplete, never a loss; an end line for another opp closes nothing of the open fight; G6 a LOST boss absent from
      runs.jsonl is a disagreement (the incomplete-only adjudication must not widen).
  E7b the label ALLOWLIST: the review's crafted labels become `<other>` (counted), allowlisted names pass unchanged,
      the allowlist covers classify_wall's real names; E7c the DENYLIST gate alone catches them as VALUES and as KEYS
      (case, possessives, phrases, both apostrophes, hex PIDs with/without # or 0x, x=/y= and [a, b], flag_/var_), and
      does not fire on mentions.
  G4b the write guard on resolved paths and identity: a junction, a `\\\\?\\` prefix, an 8.3 short name, a UNC admin
      share, case and slashes; the default clone and this checkout's ai_player/ stay guarded when --clone/--repo point
      elsewhere; the trees the run reads; each layer tested alone; --priors guards its --store and never creates one.
  R1-R4 the O3 race: a cycle archived between two records gives the same store as no race; a log missing from a cycle
      not yet archived is DEFERRED (exit 6, not in the cursor) and retried; a final archive or a pruned cycle is not.
  G2b the lock: a held take-mutex refuses; two runs that both see a stale lock never both acquire (each layer alone,
      and the harness shows they DO without both); a run removes only its own lock. C1 a crash exits 5, never 1.
  N2  a torn last runs.jsonl line is skipped and picked up once whole.
ADDED BY REVIEW ROUND 2 (2026-10-21; each arm failed on df792190 or on a mutant):
  B1  the deferral is bounded: a cycle pruned leaving an EMPTY batch/ stores tier A (was exit 6 forever); a cycle the
      learner's state.json marks pruned stores tier A for a missing log; CONTROLS: the same log missing from an
      unmarked cycle that still has logs, or beside a raw.zip, still defers. B2 the ledger: a run deferred in 3 passes
      over 24 h (an injected clock) is stored as tier A `deferred-timeout:` with one WARN; fewer passes, or less time,
      still defer; a recovered run leaves the ledger.
  R5b a ZIP_DEFLATED member with corrupt compressed bytes (zlib.error, not a CRC error) is deferred, the other stored.
  G2c the lock release: under the take-mutex (a reader holding the mutex and a handle on .lock) and with a brief retry
      (a reader holding only a handle), .lock is removed and a later run acquires; an unlink that keeps failing is a
      WARN and exit 0, never exit 5 after a successful append.
  G4d a hard link planted at any existing write target (store, cursor, ledger, lock, mutex, priors file) is refused,
      the linked file untouched; CONTROL an ordinary existing file is written.
  E7c the denylist after NFKC, format-character stripping and the non-ASCII-letter rule: the review round 2 vectors
      (fullwidth, Cyrillic, soft hyphen, zero width, PID glued or decimal, camelCase and digit-glued species, nidoranf,
      spaced letters, x 12 y 7, tile 12/7, a bare 12,7, FLAGBADGE07); its mentions stay clean; --check-priors says it is
      the SECOND layer.
E9 (wall time, tier shares) is measured by the real `--full` run and recorded in 07, not here.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
import zipfile
import zlib
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
CLONE = Path(os.environ.get("EXPERIENCE_CLONE", "C:/Remote Projects/pokebot-learner"))
#: The module under test; a mutant run points this at a scratch copy (the copy's REPO is reset to this checkout).
UNDER_TEST = Path(os.environ.get("EXPERIENCE_UNDER_TEST", HERE / "extract_experience.py"))
GOLDEN = HERE / "fixtures" / "golden.log"
GOLDEN_PAIRING = HERE / "fixtures" / "golden_pairing.log"
WARN_EXIT = 4
#: The extractor's documented exit codes, pinned here (O1 and a reader act on them): a crash is never 1.
EXIT_CRASH, EXIT_DEFERRED = 5, 6
#: The deferral ledger's file name, pinned here too (a version without a ledger then FAILS its arms, not crashes).
LEDGER_FILE = "deferrals.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


X = _load(UNDER_TEST, "extract_experience_under_test")
X.REPO = REPO
FALLBACK = dict(X.BOSS_IDS_FALLBACK)
NAMES = {265: "TRAINER_ROXANNE_1", 266: "TRAINER_BRAWLY_1", 267: "TRAINER_WATTSON_1"}

RESULTS: list[tuple[str, bool, str]] = []
SKIPPED: list[tuple[str, str]] = []


def check(name: str, ok, detail="") -> bool:
    RESULTS.append((name, bool(ok), str(detail)))
    return bool(ok)


def skip(name: str, why: str) -> None:
    SKIPPED.append((name, why))


def parse_bytes(data: bytes) -> dict:
    return X.parse_log_stream(io.BytesIO(data), FALLBACK, NAMES)


def run_main(args: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):  # a crash's traceback is part of the output
        code = X.main([str(a) for a in args])
    return code, buf.getvalue()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ============================================================================================ the golden expectation

def _mon(sp, lv):
    return {"species": sp, "level": lv}


def _fight(**kw) -> dict:
    base = {"opp": None, "opp_name": None, "boss": None, "class": "LEADER", "start_frame": None, "end_frame": None,
            "lvl_last": None, "first": None, "double": False, "res": None, "incomplete": False, "orphan_end": False,
            "money_before": None, "money_after": None, "heal_stock_before": None, "heal_stock_after": None,
            "enemy_alive": 3, "party": None, "party_age_frames": None, "moves_used": [], "use_item_turns": 0,
            "heal_spent": None, "fight_no": 1}
    base.update(kw)
    return base


#: Derived BY HAND from fixtures/golden.log (2026-10-21), line by line, not printed from the code.
EXPECTED_GOLDEN = {
    "started": True, "starter": "Torchic", "start_frame": 13041, "lines": 40, "frames_max": 242000,
    "trainer_starts": 7, "pre_start_trainer_lines": 2, "parse_suspect": False,
    "unknown_tags": {"NEWTAG": 1}, "untagged_lines": 2,
    "fights": [
        _fight(opp=265, opp_name="TRAINER_ROXANNE_1", boss="ROXANNE", start_frame=174824, end_frame=182534,
               lvl_last=15, first=True, res="Won", money_before=7368, money_after=8868, heal_stock_before={},
               heal_stock_after={}, heal_spent={}, party=[_mon("Combusken", 16), _mon("Poochyena", 7)],
               party_age_frames=4824, moves_used=["Double Kick", "Ember"]),
        _fight(opp=266, opp_name="TRAINER_BRAWLY_1", boss="BRAWLY", start_frame=200000, end_frame=203000,
               lvl_last=19, first=True, res="Lost", money_before=5000, money_after=2500,
               heal_stock_before={"Potion": 5, "Revive": 1}, heal_stock_after={"Potion": 4, "Revive": 1},
               heal_spent={"Potion": 1}, party=[_mon("Combusken", 17), _mon("Poochyena", 8)], party_age_frames=1999,
               moves_used=["Peck"], use_item_turns=1),
        _fight(opp=266, opp_name="TRAINER_BRAWLY_1", boss="BRAWLY", start_frame=210000, end_frame=213000,
               lvl_last=19, first=False, res="Lost", money_before=2500, money_after=1250,
               heal_stock_before={"Potion": 4, "Revive": 1}, heal_stock_after={"Potion": 2, "Revive": 1},
               heal_spent={"Potion": 2}, party=[_mon("Combusken", 17), _mon("Poochyena", 8)], party_age_frames=11999,
               use_item_turns=2, fight_no=2),
        _fight(opp=266, opp_name="TRAINER_BRAWLY_1", boss="BRAWLY", start_frame=221000, end_frame=223000,
               lvl_last=19, first=False, res="Won", money_before=4000, money_after=5900,
               heal_stock_before={"Potion": 2, "Revive": 1}, heal_stock_after={"Potion": 2, "Revive": 1},
               heal_spent={}, party=[_mon("Combusken", 20), _mon("Taillow", 18)], party_age_frames=999,
               moves_used=["Wing Attack"], fight_no=3),
        _fight(opp=267, opp_name="TRAINER_WATTSON_1", boss="WATTSON", start_frame=241000, lvl_last=24, first=True,
               res=None, incomplete=True, money_before=6700, heal_stock_before={"Potion": 2, "Revive": 1},
               enemy_alive=4, party=[_mon("Combusken", 20), _mon("Taillow", 18)], party_age_frames=20999,
               moves_used=["Ember"]),
    ],
    "bosses": {"BRAWLY": {"won": True, "losses": 2, "fights": 3, "incomplete": 0},
               "ROXANNE": {"won": True, "losses": 0, "fights": 1, "incomplete": 0},
               "WATTSON": {"won": False, "losses": 0, "fights": 1, "incomplete": 1}},
    "badges": [{"n": 1, "frame": 183421, "party_n": 2}, {"n": 2, "frame": 223100, "party_n": 2}],
    "whiteouts": [{"frame": 203100, "at": [0, 2], "boss_next": "BRAWLY"}],
    "derails_n": 1,
    "derail_texts": [{"text": "Brawly: 2 losses with no super-effective answer to Fighting. Need one of: Flying.",
                      "count": 1}],
    "gym_tm": [{"frame": 213600, "boss": "Brawly", "losses": 2, "wall": "Makuhita", "outcome": "no plan"}],
}

TAG = "ai9001"
PROFILE = f"endless-{TAG}-H1-torchic"


def golden_row(log: str = "golden.log", **over) -> dict:
    row = {"source": TAG, "lane": 1, "log": log, "batch": "20261021-000000", "code_commit": "fixture", "arm": "A",
           "genome_id": "g0", "lane_starter": "torchic", "starter": "Torchic", "usable": True, "complete": True,
           "champion": False, "progress": 2, "frames": 242000, "wall": "boss wall: Wattson", "derail_walls": [],
           "money_last": 6700, "catches": 0, "dex_owned": 6,
           "boss_log": {"ROXANNE": {"losses": 0, "won": True, "party_first_loss": None,
                                    "party_win": "['Combusken:L17', 'Poochyena:L7']"},
                        "BRAWLY": {"losses": 2, "won": True, "party_first_loss": "['Combusken:L17', 'Poochyena:L8']",
                                   "party_win": "['Combusken:L20', 'Taillow:L18']"}},
           "milestones": [["ROXANNE", 182534], ["BRAWLY", 223000]]}
    row.update(over)
    return row


GOLDEN_BADGE_LOG = [
    {"flag": "BADGE01_GET", "leader": "Roxanne", "frame": 301, "run_index": 1, "team": []},  # a stale save's boot
    {"flag": "BADGE01_GET", "leader": "Roxanne", "frame": 183421, "run_index": 1,
     "team": [{"species": "Combusken", "level": 17, "moves": ["Ember"], "item": None, "ivs": [1, 2, 3, 4, 5, 6]}]},
    {"flag": "BADGE02_GET", "leader": "Brawly", "frame": 223100, "run_index": 1,
     "team": [{"species": "Taillow", "level": 18, "moves": ["Wing Attack"], "item": None, "ivs": [6, 5, 4, 3, 2, 1]}]},
]


def fake_clone(root: Path, logs: dict[str, bytes], rows: list[dict], badge_log=GOLDEN_BADGE_LOG,
               tag: str = TAG, lane: int = 1, profile: str = PROFILE) -> Path:
    """A learner-clone-shaped tree at `root/clone` (returned; a store beside it in `root` is OUTSIDE it, as the
    clone guard requires): runs.jsonl, runs/<tag>/batch/{ARMS.json, L<lane>/debug-logs/*}, and the lane profile's
    badge-log.json (plus a copy of each log in the profile, as the batch runner leaves it)."""
    root = root / "clone"
    ai = root / "ai-agent"
    (ai / "data").mkdir(parents=True, exist_ok=True)
    with open(ai / "data" / "runs.jsonl", "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    batch = ai / "runs" / tag / "batch"
    d = batch / f"L{lane:02d}" / "debug-logs"
    d.mkdir(parents=True, exist_ok=True)
    lanes = [{"tag": f"H{i}", "profile": f"endless-{tag}-H{i}-x"} for i in range(1, lane)]
    lanes.append({"tag": f"H{lane}", "arm": "A", "starter": "torchic", "profile": profile})
    (batch / "ARMS.json").write_text(json.dumps({"stamp": "x", "lanes": lanes}), encoding="utf-8")
    prof = root / "sandbox-pokebot" / "profiles" / profile
    (prof / "debug-logs").mkdir(parents=True, exist_ok=True)
    for name, data in logs.items():
        (d / name).write_bytes(data)
        (prof / "debug-logs" / name).write_bytes(data)
    if badge_log is not None:
        (prof / "badge-log.json").write_text(json.dumps(badge_log), encoding="utf-8")
    return root


def store_lines(store: Path) -> list[dict]:
    return [json.loads(x) for x in (store / X.STORE_FILE).read_text(encoding="utf-8").splitlines()]


def records(store: Path) -> list[dict]:
    return [r for r in store_lines(store) if "_header" not in r]


def extract_args(clone: Path, store: Path, mode: str = "--full", repo: Path | None = None) -> list:
    return [mode, "--clone", clone, "--store", store, "--repo", repo or REPO]


# ============================================================================================ E1 golden

def e1(tmp: Path) -> None:
    data = GOLDEN.read_bytes()
    got = parse_bytes(data)
    check("E1 golden: the fixture is the spec's 40-line log", got["lines"] == 40, got["lines"])
    diff = sorted(k for k in set(got) | set(EXPECTED_GOLDEN) if got.get(k) != EXPECTED_GOLDEN.get(k))
    check("E1 golden: tier B equals the hand-derived record", not diff,
          {k: (got.get(k), EXPECTED_GOLDEN.get(k)) for k in diff[:2]})
    check("E1 golden: the truncated fight is incomplete with res null",
          got["fights"][-1]["incomplete"] is True and got["fights"][-1]["res"] is None, got["fights"][-1])
    flipped = data.replace(b"res=Won money=7368->8868", b"res=Lost money=7368->8868")
    check("E1 FAULT: one flipped res changes the record (the comparison is not vacuous)",
          parse_bytes(flipped) != EXPECTED_GOLDEN)
    rec = X.build_record(golden_row(), None, FALLBACK, NAMES)
    check("E1 tier A: parties parsed by literal_eval, win frames from milestones",
          rec["tier_a"]["BRAWLY"] == {"won": True, "losses": 2, "party_first_loss": [_mon("Combusken", 17),
                                      _mon("Poochyena", 8)], "party_win": [_mon("Combusken", 20), _mon("Taillow", 18)],
                                      "win_frame": 223000} and rec["tier"] == "A", rec["tier_a"])
    cut = X.parse_party("['Combusken:L17', 'Poochyena:L8', 'Shroo")
    check("E1 tier A: a repr cut at 200 characters keeps its whole items",
          cut == [_mon("Combusken", 17), _mon("Poochyena", 8)], cut)


# ============================================================================================ E2 / E3 real data

def clone_ready() -> bool:
    return (CLONE / "ai-agent" / "data" / "runs.jsonl").is_file()


def real_rows() -> list[dict]:
    return X.load_rows(CLONE / "ai-agent" / "data" / "runs.jsonl")


def raw_cycles(rows: list[dict]) -> list[str]:
    tags = sorted({str(r.get("source")) for r in rows})
    return [t for t in tags if (CLONE / "ai-agent" / "runs" / t / "batch").is_dir()
            or (CLONE / "ai-agent" / "runs" / t / "raw.zip").is_file()]


def e2(tmp: Path) -> None:
    if not clone_ready():
        skip("E2", f"no learner clone at {CLONE}")
        return
    rows = real_rows()
    cycles = raw_cycles(rows)
    if not cycles:
        skip("E2", "the clone has no raw cycle")
        return
    pick = cycles if os.environ.get("EXPERIENCE_E2_ALL") == "1" else cycles[-1:]
    ids, names, source = X.boss_tables()
    sub = [r for r in rows if r.get("source") in pick]
    recs, deferred = X.extract(sub, set(), CLONE / "ai-agent" / "runs", CLONE / "sandbox-pokebot" / "profiles", ids,
                               names)
    both = [r for r in recs if r["tier"] == "A+B"]
    compared = sum(len(r["agrees_with_runs_jsonl"]) for r in both)
    dis = [(r["key"], d) for r in recs for d in r["disagreements"]]
    check(f"E2 REAL ({', '.join(pick)}): every tier-B boss equals runs.jsonl's boss_log; no run deferred",
          not dis and compared > 0 and not deferred, f"{len(dis)} disagree of {compared}: {dis[:3]}; deferred "
          f"{deferred[:3]}")
    check("E2 REAL: non-vacuous (most rows have a log; each such row compared at least one boss when it has one)",
          len(both) >= 0.8 * len(sub) and all(r["agrees_with_runs_jsonl"] or not r["tier_a"] for r in both),
          f"{len(both)} A+B of {len(sub)}")
    if "decomp" not in source:
        skip("E2 decomp names", f"boss names from {source}")


def pick_real_log(rows: list[dict]):
    """(row, path) of the smallest real log of a raw folder cycle whose boss_log has Roxanne won first try."""
    best = None
    for r in rows:
        bl = r.get("boss_log") or {}
        rox = bl.get("ROXANNE") or {}
        if not (rox.get("won") and rox.get("losses") == 0):
            continue
        p = CLONE / "ai-agent" / "runs" / str(r["source"]) / "batch" / f"L{r['lane']:02d}" / "debug-logs" / r["log"]
        if p.is_file() and (best is None or p.stat().st_size < best[1].stat().st_size):
            best = (r, p)
    return best


def e3(tmp: Path) -> None:
    if not clone_ready():
        skip("E3/E3b", f"no learner clone at {CLONE}")
        return
    rows = real_rows()
    picked = pick_real_log(rows)
    if picked is None:
        skip("E3/E3b", "no raw real log with a first-try Roxanne win")
        return
    row, path = picked
    data = path.read_bytes()  # a COPY in memory; the clone's file is never written
    tag, lane, log = row["source"], row["lane"], row["log"]

    def run(name: str, payload: bytes):
        root = fake_clone(tmp / name, {log: payload}, [row], badge_log=None, tag=tag, lane=lane,
                          profile=f"endless-{tag}-H{lane}-x")
        code, out = run_main(extract_args(root, tmp / name / "store"))
        return code, records(tmp / name / "store")[0], out

    code, rec, out = run("e3control", data)
    check(f"E3 CONTROL: the untouched copy of {tag}/L{lane:02d}/{log} agrees with runs.jsonl, exit 0",
          code == 0 and rec["agrees_with_runs_jsonl"].get("ROXANNE") is True and not rec["disagreements"],
          f"exit {code}; {rec['disagreements'][:2]}")
    lines = data.split(b"\n")
    i_end = next(i for i, ln in enumerate(lines) if b"[TRAINER] end opp=265" in ln and b"res=Won" in ln)
    flipped = lines[:]
    flipped[i_end] = flipped[i_end].replace(b"res=Won", b"res=Lost", 1)
    code, rec, out = run("e3fault", b"\n".join(flipped))
    check("E3 FAULT: Roxanne's res=Won flipped -> agrees_with_runs_jsonl false and exit 1",
          code == 1 and rec["agrees_with_runs_jsonl"].get("ROXANNE") is False and "DISAGREE" in out,
          f"exit {code}; {rec['agrees_with_runs_jsonl']}")
    i_start = max(i for i in range(i_end) if b"[TRAINER] start opp=265" in lines[i])
    cut = b"\n".join(lines[:i_start + 1 + (i_end - i_start) // 2]) + b"\n"
    tb = parse_bytes_real(cut)
    last = [f for f in tb["fights"] if f["boss"] == "ROXANNE"][-1]
    check("E3b FAULT: the copy cut mid-Roxanne-fight -> that fight is incomplete, never Won",
          last["incomplete"] is True and last["res"] is None and tb["bosses"]["ROXANNE"]["won"] is False, last)
    tb = parse_bytes_real(data)
    last = [f for f in tb["fights"] if f["boss"] == "ROXANNE"][0]
    check("E3b CONTROL: untruncated -> the same fight is Won", last["res"] == "Won" and not last["incomplete"], last)


def parse_bytes_real(data: bytes) -> dict:
    return X.parse_log_stream(io.BytesIO(data), FALLBACK, {})


# ============================================================================================ E4 censoring

def tl_row(n: int, usable: bool = True) -> dict:
    won = {k: {"losses": 0, "won": True, "party_first_loss": None, "party_win": "['Marshtomp:L30']"}
           for k in X.BOSS_ORDER[:6]}
    won["TATE_AND_LIZA"] = {"losses": 4, "won": False, "party_first_loss": "['Marshtomp:L38']", "party_win": None}
    return golden_row(log=f"tl{n}.log", boss_log=won, usable=usable, complete=usable, wall="boss wall: Tate & Liza",
                      milestones=[])


def e4_arms(rows: list[dict], flip_key: str, label: str) -> None:
    recs = [X.build_record(r, None, FALLBACK, {}) for r in rows]
    base = X.build_priors(recs)
    flipped = copy.deepcopy(recs)
    for r in flipped:
        if r["key"] == flip_key:
            r["usable"] = False
    after = X.build_priors(flipped)
    tl0, tl1 = base["bosses"]["TATE_AND_LIZA"], after["bosses"]["TATE_AND_LIZA"]
    w = "boss wall: Tate & Liza"
    beaten = [k for k, v in (next(r for r in recs if r["key"] == flip_key)["tier_a"] or {}).items() if v["won"]]
    check(f"E4 {label} FAULT: the stuck row marked usable false -> T&L failures -1 and wall count -1",
          tl1["failures"]["n"] == tl0["failures"]["n"] - 1 and
          after["runs"]["wall_labels"].get(w, 0) == base["runs"]["wall_labels"].get(w, 0) - 1,
          (tl0["failures"]["n"], tl1["failures"]["n"]))
    check(f"E4 {label} FAULT: the row moves to n_censored; the {len(beaten)} bosses it beat are unchanged",
          tl1["n_censored"] == tl0["n_censored"] + 1 and tl1["n_fought"] == tl0["n_fought"] - 1 and beaten and
          all(after["bosses"][k]["n_fought"] == base["bosses"][k]["n_fought"] for k in beaten),
          (tl0["n_censored"], tl1["n_censored"], beaten))
    check(f"E4 {label} CONTROL: usable true counts it as a failure",
          tl0["failures"]["n"] >= 1 and tl0["failures"]["labels"].get(w, 0) >= 1, tl0["failures"])


def e4(tmp: Path) -> None:
    rows = [tl_row(1), tl_row(2), golden_row()]
    e4_arms(rows, X.row_key(rows[0]), "synthetic")
    if not clone_ready():
        skip("E4 real", f"no learner clone at {CLONE}")
        return
    real = real_rows()
    stuck = next((r for r in real if r.get("usable") and r.get("wall") == "boss wall: Tate & Liza"
                  and isinstance(r.get("boss_log"), dict) and r["boss_log"].get("TATE_AND_LIZA")
                  and not r["boss_log"]["TATE_AND_LIZA"]["won"]), None)
    if stuck is None:
        skip("E4 real", "no Tate & Liza-stuck usable row")
        return
    e4_arms(real, X.row_key(stuck), "REAL rows")


# ============================================================================================ E5 determinism

def e5(tmp: Path) -> None:
    g = GOLDEN.read_bytes()
    root = fake_clone(tmp / "e5", {"golden.log": g}, [golden_row()])
    s1, s2 = tmp / "e5" / "s1", tmp / "e5" / "s2"
    c1, _ = run_main(extract_args(root, s1))
    c2, _ = run_main(extract_args(root, s2))
    same = all((s1 / f).read_bytes() == (s2 / f).read_bytes() for f in (X.STORE_FILE, X.CURSOR_FILE))
    check("E5 determinism (one input, replayed): two --full runs are byte-identical", c1 == c2 == 0 and same)
    before = (s1 / X.STORE_FILE).read_bytes()
    (root / "ai-agent/runs" / TAG / "batch/L01/debug-logs/golden2.log").write_bytes(g)
    with open(root / "ai-agent/data/runs.jsonl", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(golden_row("golden2.log")) + "\n")
    c3, out = run_main(extract_args(root, s1, "--incremental"))
    after = (s1 / X.STORE_FILE).read_bytes()
    check("E5 --incremental after one new log appends exactly one record; the earlier bytes are untouched",
          c3 == 0 and hashlib.sha256(after[:len(before)]).digest() == hashlib.sha256(before).digest()
          and after.count(b"\n") == before.count(b"\n") + 1, out[-300:])
    c4, _ = run_main(extract_args(root, s1, "--incremental"))
    check("E5 a second --incremental changes nothing", c4 == 0 and (s1 / X.STORE_FILE).read_bytes() == after)
    keys = json.loads((s1 / X.CURSOR_FILE).read_text(encoding="utf-8"))["extracted"]
    check("E5 the cursor lists exactly the extracted keys", keys == sorted(r["key"] for r in records(s1)), keys)


# ============================================================================================ E6 archive parity

def zip_cycle(root: Path, tag: str, profiles: list[str], mutate: tuple[str, bytes, bytes] | None = None,
              delete_batch: bool = True) -> None:
    """Replace runs/<tag>/batch and the profiles with runs/<tag>/raw.zip (stdlib; names as O3 writes them).
    `delete_batch=False` stops part-way, as O3's delete can: the zip is in, the profiles are gone, the batch is not."""
    cdir = root / "ai-agent/runs" / tag
    with zipfile.ZipFile(cdir / "raw.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted((cdir / "batch").rglob("*")):
            if f.is_file():
                name = f.relative_to(cdir).as_posix()
                data = f.read_bytes()
                if mutate and name.endswith(mutate[0]):
                    data = data.replace(mutate[1], mutate[2], 1)
                zf.writestr(name, data)
        for p in profiles:
            pdir = root / "sandbox-pokebot/profiles" / p
            for f in sorted(pdir.rglob("*")):
                if f.is_file():
                    zf.writestr(f"profiles/{p}/{f.relative_to(pdir).as_posix()}", f.read_bytes())
    if delete_batch:
        shutil.rmtree(cdir / "batch")
    for p in profiles:
        shutil.rmtree(root / "sandbox-pokebot/profiles" / p)


def e6a(tmp: Path) -> None:
    g = GOLDEN.read_bytes()
    stores = {}
    for arm in ("folder", "zip", "fault"):
        root = fake_clone(tmp / f"e6{arm}", {"golden.log": g}, [golden_row()])
        if arm != "folder":
            zip_cycle(root, TAG, [PROFILE], mutate=("golden.log", b"res=Won money=7368", b"res=Lost money=7368")
                      if arm == "fault" else None)
        run_main(extract_args(root, tmp / f"e6{arm}" / "store"))
        stores[arm] = (tmp / f"e6{arm}" / "store" / X.STORE_FILE).read_bytes()
    zrec = records(tmp / "e6zip" / "store")[0]
    check("E6a archive parity (stdlib zip): the store from raw.zip is byte-identical to the folder's, badge-log "
          "read from the zip's profiles/ member", stores["zip"] == stores["folder"] and zrec["tier"] == "A+B"
          and zrec["badge_log_join"].startswith("ok"), zrec["badge_log_join"])
    check("E6a FAULT: a zip with one member changed gives a different store", stores["fault"] != stores["folder"])


def patch_learner(learner, root: Path) -> dict:
    """Point EVERY Path global of the learner module (but its code roots) into `root`, and assert it."""
    saved = {}
    for name, value in list(vars(learner).items()):
        if isinstance(value, Path) and name not in ("AI", "REPO", "STORY_DEV"):
            saved[name] = value
            setattr(learner, name, root / "_learner" / name)
    learner.RUNS = root / "ai-agent" / "runs"
    learner.PROFILES = root / "sandbox-pokebot" / "profiles"
    for name, value in vars(learner).items():
        if isinstance(value, Path) and name not in ("AI", "REPO", "STORY_DEV"):
            if not value.resolve().is_relative_to(root.resolve()):
                raise AssertionError(f"learner.{name} = {value} is outside {root}")
    return saved


def e6b(tmp: Path) -> None:
    if not clone_ready():
        skip("E6b", f"no learner clone at {CLONE}")
        return
    rows = real_rows()
    folders = [t for t in raw_cycles(rows) if (CLONE / "ai-agent/runs" / t / "batch").is_dir()]
    if not folders:
        skip("E6b", "no raw folder cycle in the clone")
        return
    tag = folders[-1]
    arms = json.loads((CLONE / "ai-agent/runs" / tag / "batch/ARMS.json").read_text(encoding="utf-8"))
    best = None
    for i, ln in enumerate(arms["lanes"], 1):
        d = CLONE / "ai-agent/runs" / tag / "batch" / f"L{i:02d}" / "debug-logs"
        if d.is_dir():
            size = sum(p.stat().st_size for p in d.glob("*.log"))
            if best is None or size < best[1]:
                best = (i, size)
    lane = best[0]
    profile = arms["lanes"][lane - 1]["profile"]
    sub = [r for r in rows if r.get("source") == tag and r.get("lane") == lane]
    work = tmp / "e6b"
    logs = {p.name: p.read_bytes() for p in sorted((CLONE / "ai-agent/runs" / tag / "batch" / f"L{lane:02d}" /
                                                     "debug-logs").glob("*.log"))}
    badge = CLONE / "sandbox-pokebot/profiles" / profile / "badge-log.json"
    root = fake_clone(work, logs, sub, badge_log=json.loads(badge.read_text(encoding="utf-8")) if badge.is_file()
                      else None, tag=tag, lane=lane, profile=profile)
    shutil.copy2(CLONE / "ai-agent/runs" / tag / "batch/ARMS.json", root / "ai-agent/runs" / tag / "batch/ARMS.json")
    run_main(extract_args(root, work / "s_folder"))
    sys.path.insert(0, str(REPO / "ai-agent"))
    learner = _load(REPO / "ai-agent" / "learner.py", "learner_for_e6b")
    saved = patch_learner(learner, root)
    learner.QUIET_MINUTES = 0  # the fresh copies count as quiet, as in test_agent's O3Sandbox
    c = {"tag": tag, "created": [str(learner.RUNS / tag / "batch"), str(learner.PROFILES / profile)]}
    try:
        how = learner.archive_cycle(c, cmds=[])
    finally:
        for k, v in saved.items():
            setattr(learner, k, v)
    zpath = root / "ai-agent/runs" / tag / "raw.zip"
    man = json.loads((root / "ai-agent/runs" / tag / "raw.manifest.json").read_text(encoding="utf-8"))
    check(f"E6b the learner's own archive_cycle archived a copy of {tag} L{lane:02d} ({len(logs)} logs, "
          f"{best[1] / 2**20:.0f} MB) and deleted the originals",
          zpath.is_file() and not (root / "ai-agent/runs" / tag / "batch").exists()
          and not (root / "sandbox-pokebot/profiles" / profile).exists() and man.get("n_dup", 0) >= len(logs), how)
    run_main(extract_args(root, work / "s_zip"))
    a, b = (work / "s_folder" / X.STORE_FILE).read_bytes(), (work / "s_zip" / X.STORE_FILE).read_bytes()
    recs = records(work / "s_zip")
    check("E6b archive parity (real lane, O3's raw.zip): the store from the zip is byte-identical to the folder's",
          a == b and recs and all(r["tier"] == "A+B" for r in recs), f"{len(recs)} records")
    check("E6b the badge-log was joined from the zip's STORED profiles/ member",
          any(r["badge_log"] for r in recs) == badge.is_file(), [r["badge_log_join"] for r in recs])
    fault_work = tmp / "e6bfault"
    mut = fault_work / "clone"
    shutil.copytree(root / "ai-agent", mut / "ai-agent")
    zsrc = mut / "ai-agent/runs" / tag / "raw.zip"
    tmpz = zsrc.with_suffix(".tmp")
    with zipfile.ZipFile(zsrc) as zi, zipfile.ZipFile(tmpz, "w", zipfile.ZIP_DEFLATED) as zo:
        done = False
        for info in zi.infolist():
            data = zi.read(info.filename)
            if not done and info.filename.startswith("batch/") and info.filename.endswith(".log"):
                # a GYM LEADER's win (a grunt's res=Won is not in a record, so flipping it would prove nothing)
                data, n = re.subn(rb"(\[TRAINER\] end opp=2(?:6[5-9]|7[0-2])\b[^\n]*?)res=Won", rb"\1res=Lost",
                                  data, count=1)
                done = n == 1
            zo.writestr(info.filename, data)
    os.replace(tmpz, zsrc)
    run_main(extract_args(mut, fault_work / "s"))
    check("E6b FAULT: one gym win flipped inside the zip gives a different store",
          done and (fault_work / "s" / X.STORE_FILE).read_bytes() != a, f"mutated: {done}")


# ============================================================================================ E7 privacy gate

def e7(tmp: Path) -> None:
    species = X._species_names(REPO)
    check("E7 setup: the species list is loaded (else the species check is vacuous)", len(species) > 300,
          len(species))
    dirty = tl_row(9)  # a usable row that LOST a boss, so its label lands in that boss's failures AND the run walls
    dirty["wall"] = "boss wall: Kingdra at (5, 3) #3E751CAF FLAG_BADGE07_GET"
    # The two tier-A rows come from a cycle with NO raw data (ai9002): a row of a cycle that still has its folder but
    # not its log is deferred (the O3 race rule, R2), and these rows have no log.
    tier_a_only = [r | {"source": "ai9002"} for r in (tl_row(1), dirty)]
    root = fake_clone(tmp / "e7", {"golden.log": GOLDEN.read_bytes()}, [golden_row(), *tier_a_only])
    store = tmp / "e7" / "store"
    run_main(extract_args(root, store))
    out = tmp / "e7" / "priors.json"
    code, msg = run_main(["--priors", "--store", store, "--priors-out", out, "--clone", root])
    text = out.read_text(encoding="utf-8") if out.exists() else ""
    walls = json.loads(text)["runs"]["wall_labels"] if text else {}
    check("E7 CONTROL: the generated priors pass the gate; the dirty wall label is not leaked but COUNTED as <other>",
          code == 0 and text and "3E751CAF" not in text and "Kingdra" not in text and "(5, 3)" not in text
          and "FLAG_" not in text and walls.get("<other>") == 1 and walls.get("boss wall: Tate & Liza") == 1,
          f"{msg} | {walls}")
    c2, _ = run_main(["--check-priors", out])
    check("E7 CONTROL: --check-priors passes the generated file", c2 == 0)
    priors = json.loads(text) if text else {}
    check("E7 every block is labelled bot corpus",
          priors.get("source") == X.CORPUS and priors.get("runs", {}).get("source") == X.CORPUS and
          all(b.get("source") == X.CORPUS for b in priors.get("bosses", {}).values()))
    if not priors:
        return  # the CONTROL above already FAILED; the planted arms need a file to plant into
    check("E7 species shares are excluded (no species key or value anywhere)",
          not any(s in text for s in ("Combusken", "Taillow", "Poochyena", "Marshtomp")))
    plants = {
        "a PID": lambda p: p["runs"].__setitem__("note", "lead Combusken#3E751CAF"),
        "a position": lambda p: p["runs"].__setitem__("note", "stood at (12, 7)"),
        "a flag name": lambda p: p["runs"].__setitem__("note", "FLAG_BADGE01_GET set"),
        "a species": lambda p: p["bosses"]["ROXANNE"].__setitem__("note", "Marshtomp led"),
        "a missing label": lambda p: p["bosses"]["NORMAN"].pop("source"),
    }
    for what, plant in plants.items():
        bad = copy.deepcopy(priors)
        plant(bad)
        path = tmp / "e7" / f"planted-{what.replace(' ', '_')}.json"
        path.write_text(json.dumps(bad), encoding="utf-8")
        c3, o3 = run_main(["--check-priors", path])
        check(f"E7 FAULT: {what} planted in a scratch priors file fails the gate", c3 == X.EXIT_GATE, o3[-200:])
    real_build = X.build_priors
    try:
        def leaky(recs):
            p = real_build(recs)
            p["runs"]["note"] = "#3E751CAF"
            return p
        X.build_priors = leaky
        out2 = tmp / "e7" / "leaky.json"
        c4, msg4 = run_main(["--priors", "--store", store, "--priors-out", out2, "--clone", root])
    finally:
        X.build_priors = real_build
    check("E7 FAULT: the writer refuses a file that fails the gate, and writes nothing",
          c4 == X.EXIT_GATE and not out2.exists(), msg4)
    if clone_ready():
        recs = [X.build_record(r, None, FALLBACK, {}) for r in real_rows()]
        problems = X.check_ai_facing(X.build_priors(recs), species)
        check("E7 CONTROL (REAL rows): priors built from every real runs.jsonl row pass the gate", not problems,
              problems[:3])
    else:
        skip("E7 real", f"no learner clone at {CLONE}")


# ============================================================================================ E8 drift canary

def e8(tmp: Path) -> None:
    body = b"".join(b"f%d [MAP] ROUTE101(0,16) -> ROUTE102(0,17)\n" % i for i in range(1200))
    t = parse_bytes(b"f1 [STEP] 'Story: choosing Mudkip!'\n" + body)
    check("E8 FAULT: a 1,201-line log with no [TRAINER] start is parse_suspect", t["parse_suspect"] is True)
    t2 = parse_bytes(b"f1 [STEP] 'Story: choosing Mudkip!'\n" + body + GOLDEN.read_bytes().split(b"\n")[9] + b"\n")
    check("E8 CONTROL: the same log with one [TRAINER] start is not", t2["parse_suspect"] is False)
    check("E8 CONTROL: the 40-line golden is not suspect", parse_bytes(GOLDEN.read_bytes())["parse_suspect"] is False)
    junk = parse_bytes(b"f1 [STEP] 'Story: choosing Mudkip!'\n\xff\xfe garbage\nf12 [WEIRD] x\n"
                       b"f13 [TRAINER] end opp=999 res=\nf14 [hb] party=[broken\nf15 [TRAINER] start opp=abc\n"
                       b"f16 [BATTLE] [TURN x] ->\n")
    check("E8 unknown tags and malformed lines (after the start) are counted, never fatal",
          junk["unknown_tags"] == {"WEIRD": 1} and junk["untagged_lines"] == 1 and junk["fights"] == [],
          junk["unknown_tags"])


# ============================================================================================ E10 the digest scope

def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", *args],
                   cwd=repo, check=True, capture_output=True, timeout=60)


def e10(tmp: Path) -> None:
    prov = _load(REPO / "ai_player" / "gates" / "provenance.py", "provenance_for_e10")
    repo = tmp / "e10repo"
    (repo / "ai_player" / "knowledge").mkdir(parents=True)
    (repo / "ai_player" / "knowledge" / "x.json").write_text("{}", encoding="utf-8")
    (repo / ".gitignore").write_text("tools/experience/store/\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "--", "ai_player", ".gitignore")
    _git(repo, "commit", "-q", "-m", "fixture")

    def digest() -> str:
        _, diff, untracked, _ = prov.read_tree(repo, ("ai_player",))
        return prov.tree_digest(diff, untracked)

    d0 = digest()
    root = fake_clone(tmp / "e10clone", {"golden.log": GOLDEN.read_bytes()}, [golden_row()])
    store = repo / "tools" / "experience" / "store"
    code, out = run_main(extract_args(root, store, "--incremental", repo))
    check("E10 CONTROL: --incremental (the real flags) writes the store and leaves the ai_player/ digest unchanged",
          code == 0 and (store / X.STORE_FILE).exists() and digest() == d0, out[-200:])
    bad_store = repo / "ai_player" / "knowledge" / "experience"
    code, out = run_main(extract_args(root, bad_store, "--incremental", repo))
    check("E10 FAULT: --incremental pointed into ai_player/ is REFUSED, nothing written, digest unchanged",
          code == X.EXIT_REFUSED and not bad_store.exists() and digest() == d0, out[-200:])
    code, _ = run_main(["--priors", "--store", store, "--priors-out", repo / X.PRIORS_REL, "--clone", root,
                        "--repo", repo, "--force-priors"])
    check("E10 FAULT (sensitivity): a priors write into scratch ai_player/ CHANGES the digest (the assertion bites)",
          code == 0 and digest() != d0)
    try:
        with contextlib.redirect_stderr(io.StringIO()):
            X.main(["--incremental", "--priors"])
        usage = False
    except SystemExit as exc:
        usage = exc.code == 2
    check("E10 --incremental --priors together is a usage error (the routine path never writes the priors)", usage)


# ============================================================================================ G / J guards

def g_guards(tmp: Path) -> None:
    g = GOLDEN.read_bytes()
    root = fake_clone(tmp / "g", {"golden.log": g}, [golden_row()])
    store = tmp / "g" / "store"
    c0, _ = run_main(extract_args(root, store))
    before = (store / X.STORE_FILE).read_bytes()
    c1, out = run_main(extract_args(root, store))
    check("G1 FAULT: --full on a non-empty store is REFUSED and the store is untouched",
          c1 == X.EXIT_REFUSED and (store / X.STORE_FILE).read_bytes() == before, out[-200:])
    check("G1 CONTROL: --full on an empty store runs", c0 == 0)

    (store / X.LOCK_FILE).write_text("1 1", encoding="utf-8")
    c2, out = run_main(extract_args(root, store, "--incremental"))
    check("G2 FAULT: a fresh lock (another extractor) REFUSES", c2 == X.EXIT_REFUSED, out[-200:])
    old = time.time() - X.LOCK_STALE_S - 60
    os.utime(store / X.LOCK_FILE, (old, old))
    c3, _ = run_main(extract_args(root, store, "--incremental"))
    check("G2 CONTROL: a stale lock is replaced, and no lock is left behind",
          c3 == 0 and not (store / X.LOCK_FILE).exists())

    torn = tmp / "g" / "torn"
    shutil.copytree(store, torn)
    with open(torn / X.STORE_FILE, "ab") as fh:
        fh.write(b'{"key": "half')
    c4, out = run_main(extract_args(root, torn, "--incremental"))
    check("G3 FAULT: a torn store line REFUSES (the store is never repaired by rewriting)", c4 == X.EXIT_REFUSED,
          out[-200:])
    cut = tmp / "g" / "cut"
    shutil.copytree(store, cut)
    body = (cut / X.STORE_FILE).read_bytes()
    (cut / X.STORE_FILE).write_bytes(body[:-1])  # the last record whole, only its newline lost: still a torn append
    c4b, out = run_main(extract_args(root, cut, "--incremental"))
    check("G3 FAULT: a last record that lost only its newline REFUSES (the next append would join its line)",
          c4b == X.EXIT_REFUSED, out[-200:])
    ghost = tmp / "g" / "ghost"
    shutil.copytree(store, ghost)
    (ghost / X.CURSOR_FILE).write_text(json.dumps({"schema": 1, "extracted": ["nope/1/x.log"]}), encoding="utf-8")
    c5, out = run_main(extract_args(root, ghost, "--incremental"))
    check("G3 FAULT: a cursor key missing from the store REFUSES", c5 == X.EXIT_REFUSED, out[-200:])

    inside = root / "ai-agent" / "experience-store"
    c6, out = run_main(extract_args(root, inside))
    check("G4 FAULT: a store inside the clone is REFUSED and not created", c6 == X.EXIT_REFUSED and not inside.exists(),
          out[-200:])
    c7, out = run_main(["--priors", "--store", store, "--priors-out", root / "p.json", "--clone", root])
    check("G4 FAULT: a priors file inside the clone is REFUSED", c7 == X.EXIT_REFUSED and not (root / "p.json").exists(),
          out[-200:])

    sys.path.insert(0, str(REPO / "tools"))
    try:
        import decomp_lookup as dl
        dl.decomp_root()
        have_decomp = True
    except Exception as exc:  # noqa: BLE001
        have_decomp, why = False, str(exc).splitlines()[0]
    if have_decomp:
        ids, names, source = X.boss_tables()
        check("G5 CONTROL: the pinned decomp's boss ids equal the table runs.jsonl uses",
              ids == FALLBACK and names.get(265) == "TRAINER_ROXANNE_1" and "decomp" in source, source)
        real = dl.trainer
        try:
            dl.trainer = lambda root_, name: dict(real(root_, name), id=real(root_, name)["id"] + 1) \
                if name == "TRAINER_NORMAN_1" else real(root_, name)
            try:
                X.boss_tables()
                refused = False
            except X.Refused:
                refused = True
        finally:
            dl.trainer = real
        check("G5 FAULT: a decomp whose Norman id drifts is REFUSED", refused)
    else:
        ids, _, source = X.boss_tables()
        check("G5 no decomp: the fallback table is used and the label says so", ids == FALLBACK and "fallback" in source)
        skip("G5 decomp arms", f"no pinned decomp: {why}")

    pri = tmp / "g" / "priors.json"
    c8, _ = run_main(["--priors", "--store", store, "--priors-out", pri, "--clone", root])
    first = pri.read_bytes()
    obj = json.loads(first)
    obj["inputs"]["records"] = 1000  # pretend the committed file was built from a far bigger sample
    pri.write_text(json.dumps(obj), encoding="utf-8")
    marked = pri.read_bytes()
    c9, msg9 = run_main(["--priors", "--store", store, "--priors-out", pri, "--clone", root])
    check("G7 FAULT: under 10 % growth the committed priors are NOT regenerated (the file is untouched)",
          c8 == 0 and c9 == 0 and pri.read_bytes() == marked and "not regenerated" in msg9, msg9)
    c10, _ = run_main(["--priors", "--store", store, "--priors-out", pri, "--clone", root, "--force-priors"])
    check("G7 CONTROL: --force-priors regenerates it", c10 == 0 and pri.read_bytes() == first)

    row = golden_row(boss_log={"ROXANNE": golden_row()["boss_log"]["ROXANNE"]})  # BRAWLY absent from tier A
    rec = build_from_bytes(row, g)
    check("G6 FAULT: a boss WON in the log but absent from runs.jsonl is still a disagreement",
          any(d["boss"] == "BRAWLY" for d in rec["disagreements"]), rec["disagreements"])
    rec = build_from_bytes(golden_row(), g)
    check("G6 CONTROL: an incomplete-only boss (Wattson, cut by the end of the log) is adjudicated, not a "
          "disagreement", rec["bosses_incomplete_only"] == ["WATTSON"] and not rec["disagreements"], rec)


def build_from_bytes(row: dict, data: bytes) -> dict:
    class OneLog:
        def open_log(self, lane, log):
            return io.BytesIO(data)

        def arms(self):
            return None

        def lane_logs(self, lane):
            return [row["log"]]

        def badge_log(self, profile):
            return None
    return X.build_record(row, OneLog(), FALLBACK, NAMES)


def j1(tmp: Path) -> None:
    tb = parse_bytes(GOLDEN.read_bytes())
    out, why = X.join_badge_log(GOLDEN_BADGE_LOG, 1, tb)
    check("J1 CONTROL: frames match -> joined; the stale-boot f301 entry is dropped, said in the reason",
          out is not None and [e["n"] for e in out] == [1, 2] and "1 stale-boot" in why
          and "ivs" not in json.dumps(out), why)
    wrong = copy.deepcopy(GOLDEN_BADGE_LOG)
    wrong[2]["frame"] = 999999
    out, why = X.join_badge_log(wrong, 1, tb)
    check("J1 FAULT: one entry's frame differs from the log's [BADGE] frame -> nothing attached", out is None
          and why.startswith("mismatch"), why)
    out, why = X.join_badge_log(GOLDEN_BADGE_LOG, 2, tb)
    check("J1 FAULT: the wrong run_index (position) finds no entries and attaches nothing", out is None, why)
    out, why = X.join_badge_log(GOLDEN_BADGE_LOG, 1, None)
    check("J1 no raw log -> unverified, not attached", out is None and why.startswith("unverified"), why)
    stale_only = [e for e in GOLDEN_BADGE_LOG if e["frame"] == 301]
    nob = parse_bytes(b"f13041 [STEP] 'Story: choosing Torchic!'\n")
    out, why = X.join_badge_log(stale_only, 1, nob)
    check("J1 CONTROL: a run with no badge whose only entries are stale-boot ones joins as ok with none",
          out == [] and why.startswith("ok"), why)


# ============================================================================================ P1 pairing golden

#: Derived BY HAND from fixtures/golden_pairing.log (2026-10-21), line by line, not printed from the code. The f50
#: heartbeat is before `Story: choosing` (ignored; the party comes from f200, 800 frames before the first start).
#: Flannery (opp 268): the f1000 start is cut off by a SECOND start at f1500, so that fight is incomplete and never a
#: loss; the f1500 fight ends Won. Norman (269) starts at f3000; the f3500 end is for opp=270 (Winona), so it closes
#: NOTHING of Norman's (his fight is incomplete) and is Winona's orphan Lost end; the f4000 end opp=269 is an orphan
#: Lost for Norman. scoring.py counts END lines, so it agrees: Flannery won with 0 losses, Norman 1 loss, Winona 1.
EXPECTED_PAIRING_BOSSES = {"FLANNERY": {"won": True, "losses": 0, "fights": 2, "incomplete": 1},
                           "NORMAN": {"won": False, "losses": 1, "fights": 2, "incomplete": 1},
                           "WINONA": {"won": False, "losses": 1, "fights": 1, "incomplete": 0}}
#: (boss, start_frame, end_frame, res, incomplete, orphan_end, fight_no, money_before, money_after)
EXPECTED_PAIRING_FIGHTS = [("FLANNERY", 1000, None, None, True, False, 1, 9000, None),
                           ("FLANNERY", 1500, 2000, "Won", False, False, 2, 9000, 11900),
                           ("NORMAN", 3000, None, None, True, False, 1, 11900, None),
                           ("WINONA", None, 3500, "Lost", False, True, 1, 11900, 5950),
                           ("NORMAN", None, 4000, "Lost", False, True, 2, 5950, 2975)]


def pairing_row(**over) -> dict:
    """The row scoring.py writes for golden_pairing.log: a boss_log entry for every boss with an END line."""
    team = "['Marshtomp:L30', 'Taillow:L25']"
    bl = {"FLANNERY": {"losses": 0, "won": True, "party_first_loss": None, "party_win": team},
          "NORMAN": {"losses": 1, "won": False, "party_first_loss": team, "party_win": None},
          "WINONA": {"losses": 1, "won": False, "party_first_loss": team, "party_win": None}}
    return golden_row(log="pairing.log", boss_log=bl, milestones=[["FLANNERY", 2000]], **over)


def p1(tmp: Path) -> None:
    data = GOLDEN_PAIRING.read_bytes()
    got = parse_bytes(data)
    check("P1 pairing golden: 9 lines, the run starts at f100, 3 starts, the pre-start heartbeat ignored",
          got["lines"] == 9 and got["start_frame"] == 100 and got["trainer_starts"] == 3
          and got["fights"][0]["party_age_frames"] == 800, (got["lines"], got["start_frame"], got["trainer_starts"]))
    check("P1 FAULT-SHAPES: a start cut off by a start is incomplete (never a loss); an end for another opp closes "
          "nothing of the open fight: per boss equal to the hand-derived table", got["bosses"] == EXPECTED_PAIRING_BOSSES,
          got["bosses"])
    proj = [(f["boss"], f["start_frame"], f["end_frame"], f["res"], f["incomplete"], f["orphan_end"], f["fight_no"],
             f["money_before"], f["money_after"]) for f in got["fights"]]
    check("P1 every fight equals the hand-derived pairing (frames, result, incomplete, orphan, number, money)",
          proj == EXPECTED_PAIRING_FIGHTS, proj)
    rec = build_from_bytes(pairing_row(), data)
    check("P1 CONTROL: scoring.py's boss_log for this log agrees boss by boss; nothing adjudicated",
          rec["agrees_with_runs_jsonl"] == {"FLANNERY": True, "NORMAN": True, "WINONA": True}
          and not rec["disagreements"] and rec["bosses_incomplete_only"] == [], rec["disagreements"])
    row = pairing_row()
    row["boss_log"].pop("WINONA")
    rec = build_from_bytes(row, data)
    check("G6 FAULT: a boss LOST in the log (1 loss, never won) but absent from runs.jsonl is a disagreement, never "
          "adjudicated as incomplete-only", any(d["boss"] == "WINONA" for d in rec["disagreements"])
          and "WINONA" not in rec["bosses_incomplete_only"], (rec["disagreements"], rec["bosses_incomplete_only"]))


# ============================================================================================ E7b/E7c labels, gate

#: The review's crafted wall labels (2026-10-21): each reached the AI-facing file through the old masks. The allowlist
#: must turn every one into <other> (the last three are not leaks, only not EXACTLY an allowlisted name).
LEAKY_LABELS = (
    "boss wall: kingdra", "boss wall: KINGDRA", "boss wall: Kingdra's Dragon Dance", "boss wall: Mr. Mime",
    "boss wall: Farfetch'd", "boss wall: Farfetch’d", "boss wall: Nidoran♀'s", "boss wall: Kingdra-type",
    "boss wall: Kingdra/Luvdisc", "lead #3e751caf fainted", "lead pid=3E751CAF fainted", "lead 0x3E751CAF fainted",
    "stuck at x=12 y=7", "stuck at [12, 7]", "stuck at 12,7 on ROUTE 111", "flag_badge07_get unset",
    "FLAGBADGE07 unset", "Ch# (Victory Road) failed after # attempts. attempt #: BotModeError: C",
    "boss wall: norman", "boss wall: Norman ")
#: What the DENYLIST gate must catch ON ITS OWN (the independent second layer; the allowlist is the guarantee).
DENY_PLANTS = (
    "kingdra", "KINGDRA", "Kingdra's Dragon Dance", "Mr. Mime", "mr mime", "Farfetch'd", "Farfetch’d", "farfetchd",
    "Nidoran♀'s", "Kingdra-type", "Kingdra/Luvdisc", "two Zubats", "Ho-Oh", "#3e751caf", "pid=3E751CAF",
    "0x3E751CAF", "lead 3e751caf fainted", "x=12 y=7", "y: -3", "[12, 7]", "at (5, 3)", "pos=(5, 3)", "map=11,3",
    "flag_badge07_get", "Var_Temp_1", "set_flag_x", "FLAG_BADGE07_GET", "BADGE07_GET")
#: Review round 2 (2026-10-21): each of these PASSED the round-1 gate as a value. One per layer, so a mutant that drops
#: a layer is caught: NFKC (fullwidth `＝` and digits, which are no letters), the format-character strip (soft hyphen,
#: zero width), the non-ASCII-letter rule (Cyrillic `а`; fullwidth letters fold to ASCII under NFKC), `pid` glued or
#: decimal, the bare pair, `x 12 y 7`, `tile`, the camelCase and letter/digit split, the Nidoran aliases, the
#: spaced-letter join, `flag`/`var` glued to a name with a digit.
DENY_PLANTS_R2 = (
    "12,7 on ROUTE 111", "PID3E751CAF", "pid 1047919791", "KingdraLuvdisc", "Kingdra2", "lead: K i n g d r a",
    "FLAGBADGE07", "tile 12/7", "x 12 y 7", "Ｋｉｎｇｄｒａ", "Kingdrа", "Kin­gdra", "nidoranf", "NidoranM",
    "King​dra", "stuck at x＝12 y＝7", "stuck at １２,７", "stuck at 12, 7", "VarTemp1")
#: Mentions the gate must NOT fire on (a gate with false positives teaches people to bypass it). The second group is
#: the review round 2 checker's 15 mentions.
DENY_NEGATIVES = (
    "no PID, position, flag or var name, or species", "up to 3,600 frames old", "27-29", "first_try_win_rate",
    "a game cut by the time limit (usable false) is censored", "boss wall: Tate & Liza",
    "E4 refused: League basket short", "max=3", "variable flags were flagged", "the map", "Poke Balls", "heal_stock",
    "2026-10-21", "deadbeef12", "1234567", "boss wall: this boss", "<other>", "CHAMPION", "Abracadabra", "Drake",
    "Normal",
    "unreachable target", "heal walk blocked", "bot corpus", "first try", "the deadline", "decades", "faceted",
    "Wallace", "x-ray", "max", "p10", "rapid 12", "flagship", "1,234 runs", "tiles of grass", "levels_at_badge")


def e7b(tmp: Path) -> None:
    """The label ALLOWLIST (the first layer)."""
    other = [lab for lab in LEAKY_LABELS if X.priors_label(lab) != "<other>"]
    check(f"E7b FAULT: each of {len(LEAKY_LABELS)} crafted labels (species in any spelling, hex PIDs, x=/[a, b] "
          f"positions, flag names, free text, a wrong case) becomes <other>", not other, other)
    kept = [lab for lab in sorted(X.ALLOWED_LABELS) if X.priors_label(lab) != lab]
    check("E7b CONTROL: every allowlisted name passes unchanged", not kept and len(X.ALLOWED_LABELS) >= 20, kept)
    check("E7b CONTROL: a row with no wall gets the fixed '<no wall label>'", X.priors_label(None) == "<no wall label>",
          X.priors_label(None))
    species = X._species_names(REPO)
    dirty = [lab for lab in sorted(X.ALLOWED_LABELS) if X.check_ai_facing(
        {"bosses": {}, "runs": {"source": X.CORPUS, "wall_labels": {lab: 1}, "note": lab}}, species)]
    check("E7b CONTROL: the allowlist's own names pass the denylist gate, as keys and as values", not dirty, dirty)
    knowledge = _load(REPO / "ai-agent" / "knowledge.py", "knowledge_for_e7b")
    emitted = {name for name, _, _ in knowledge.WALLS} | {knowledge.classify_wall(None)}
    emitted |= {knowledge.classify_wall(f"{b}: 3 losses with no super-effective answer to Water. Need one of: Grass.")
                for b in X.BOSS_DISPLAY}
    emitted |= {knowledge.classify_wall(f"this boss: 3 losses with no super-effective answer to {t}. x")
                for t in ("Normal", "Rock")}
    missing = sorted(emitted - X.ALLOWED_LABELS)
    check("E7b CONTROL: every name classify_wall emits from its table, for the 13 bosses and for 'this boss', is "
          "allowlisted (a new WALLS name must be reviewed and added)", not missing and len(emitted) >= 20, missing)
    rows = [tl_row(i) | {"wall": lab} for i, lab in enumerate(LEAKY_LABELS)] + [tl_row(99)]
    recs = [X.build_record(r, None, FALLBACK, {}) for r in rows]
    p = X.build_priors(recs)
    text = json.dumps(p, ensure_ascii=False)
    leaked = [lab for lab in LEAKY_LABELS if lab in text]
    n = len(LEAKY_LABELS)
    check("E7b END TO END: priors built from rows with the crafted labels carry none of them, count each as <other> "
          "(run walls and the boss's failure labels), keep the allowlisted one, and pass the gate",
          not leaked and p["runs"]["wall_labels"] == {"<other>": n, "boss wall: Tate & Liza": 1}
          and p["bosses"]["TATE_AND_LIZA"]["failures"]["labels"] == {"<other>": n, "boss wall: Tate & Liza": 1}
          and not X.check_ai_facing(p, species), (leaked, p["runs"]["wall_labels"]))


def e7c(tmp: Path) -> None:
    """The DENYLIST gate on its own (it never consults the allowlist)."""
    species = X._species_names(REPO)
    base = {"bosses": {k: {"source": X.CORPUS, "failures": {"labels": {}}} for k in X.BOSS_ORDER},
            "runs": {"source": X.CORPUS, "wall_labels": {}}}
    clean = X.check_ai_facing(base, species)
    check("E7c CONTROL: the clean skeleton passes", not clean, clean)

    def missed(place, plants) -> list[str]:
        out = []
        for s in plants:
            obj = copy.deepcopy(base)
            place(obj, s)
            if not X.check_ai_facing(obj, species):
                out.append(s)
        return out

    places = (("a string VALUE", lambda o, s: o["runs"].__setitem__("note", s)),
              ("a runs.wall_labels KEY", lambda o, s: o["runs"]["wall_labels"].__setitem__(s, 1)),
              ("a boss's failures.labels KEY", lambda o, s: o["bosses"]["JUAN"]["failures"]["labels"].__setitem__(s, 1)))
    for what, place in places:
        m = missed(place, DENY_PLANTS)
        check(f"E7c FAULT: each of {len(DENY_PLANTS)} planted leaks fails the gate as {what}", not m, m)
        m = missed(place, DENY_PLANTS_R2)
        check(f"E7c FAULT (round 2): each of {len(DENY_PLANTS_R2)} normalised spellings fails the gate as {what}",
              not m, [ascii(s) for s in m])
    path = tmp / "clean.json"
    path.write_text(json.dumps(base), encoding="utf-8")
    code, out = run_main(["--check-priors", path])
    check("E7c --check-priors' PASS line says it is the SECOND layer and that the allowlist is the guarantee",
          code == 0 and "SECOND layer" in out and "allowlist is the guarantee" in out, out[-200:])
    fp = []
    for s in DENY_NEGATIVES:
        obj = copy.deepcopy(base)
        obj["runs"]["note"] = s
        obj["runs"]["wall_labels"][s] = 1
        if X.check_ai_facing(obj, species):
            fp.append(s)
    check(f"E7c CONTROL: the gate does not fire on {len(DENY_NEGATIVES)} mentions and the file's own words",
          not fp, fp)


# ============================================================================================ N2, C1: inputs, crashes

def n2(tmp: Path) -> None:
    g = GOLDEN.read_bytes()
    root = fake_clone(tmp / "torn", {"a.log": g, "b.log": g}, [golden_row("a.log")])
    rj = root / "ai-agent" / "data" / "runs.jsonl"
    whole = json.dumps(golden_row("b.log")) + "\n"
    with open(rj, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(whole[:len(whole) // 2])  # the tuner is appending this row right now
    store = tmp / "torn" / "store"
    code, out = run_main(extract_args(root, store, "--incremental"))
    keys = [r["key"] for r in records(store)] if (store / X.STORE_FILE).exists() else []
    check("N2 FAULT: a torn last runs.jsonl line is skipped: exit 0, only the whole row extracted",
          code == 0 and keys == [f"{TAG}/1/a.log"], f"exit {code}; {keys}; {out[-200:]}")
    with open(rj, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(whole[len(whole) // 2:])
    code, out = run_main(extract_args(root, store, "--incremental"))
    keys = [r["key"] for r in records(store)]
    check("N2 CONTROL: once the line is whole, the next --incremental extracts it",
          code == 0 and keys == [f"{TAG}/1/a.log", f"{TAG}/1/b.log"], f"exit {code}; {keys}")


def main_exit(args: list) -> tuple[int, str]:
    """main()'s exit code as `sys.exit(main())` turns it into one: an exception escaping main() is exit 1."""
    try:
        return run_main(args)
    except Exception as exc:  # noqa: BLE001 - exactly what this measures
        return 1, f"(escaped main) {type(exc).__name__}: {exc}"


def c1(tmp: Path) -> None:
    root = fake_clone(tmp / "c1", {"golden.log": GOLDEN.read_bytes()}, [golden_row()])
    rj = root / "ai-agent" / "data" / "runs.jsonl"
    rj.write_bytes(b"{not json}\n" + rj.read_bytes())
    code, out = main_exit(extract_args(root, tmp / "c1" / "store", "--incremental"))
    check("C1 FAULT: a corrupt runs.jsonl line exits 5 (never 1, 'a boss disagrees') and names line 1",
          code == EXIT_CRASH and "runs.jsonl line 1 is not JSON" in out, f"exit {code}: {out[-200:]}")
    real = X.read_cursor

    def planted(store):
        raise RuntimeError("planted")
    X.read_cursor = planted
    try:
        code, out = main_exit(extract_args(root, tmp / "c1" / "store2", "--incremental"))
    finally:
        X.read_cursor = real
    check("C1 FAULT: any uncaught error exits 5 with its traceback, never 1",
          code == EXIT_CRASH and "RuntimeError: planted" in out and "Traceback" in out, f"exit {code}: {out[-200:]}")
    rj.write_bytes(rj.read_bytes().split(b"\n", 1)[1])
    code, _ = main_exit(extract_args(root, tmp / "c1" / "store3", "--incremental"))
    check("C1 CONTROL: the same runs.jsonl without the bad line exits 0", code == 0, code)
    codes = [getattr(X, n, None) for n in ("EXIT_OK", "EXIT_DISAGREE", "EXIT_REFUSED", "EXIT_GATE", "EXIT_CRASH",
                                           "EXIT_DEFERRED")]
    check("C1 the documented exit codes: crash 5, deferred 6, all six distinct", codes[4:] == [EXIT_CRASH, EXIT_DEFERRED]
          and len(set(codes)) == 6, codes)


# ============================================================================================ R1-R4 the O3 race

def _raced(tmp: Path, name: str, rows: list[dict], logs: dict[str, bytes], o3) -> tuple[int, str, Path]:
    """--incremental over a fake clone, with `o3(root)` run just BEFORE the second record is built: O3 archives the
    cycle in the middle of a pass, after the cycle was opened as a folder and its first record was written."""
    root = fake_clone(tmp / name, logs, rows)
    real = X.build_record
    calls = {"n": 0}

    def wrapped(row, raw, ids, names):
        calls["n"] += 1
        if calls["n"] == 2:
            o3(root)
        return real(row, raw, ids, names)
    X.build_record = wrapped
    try:
        code, out = run_main(extract_args(root, tmp / name / "store", "--incremental"))
    finally:
        X.build_record = real
    return code, out, tmp / name / "store"


def deflate_corrupt_cycle(work: Path, logs: dict[str, bytes], rows: list[dict], member: str = "b.log") -> Path:
    """A fake clone whose cycle is in its FINAL archived form, with the DEFLATE stream of `batch/.../<member>` broken:
    its first four compressed bytes set to 0xFF (an invalid block type), so reading it raises zlib.error before any
    CRC check. Asserted, so an arm built on it cannot be vacuous."""
    root = fake_clone(work, logs, rows)
    zip_cycle(root, TAG, [PROFILE])
    zpath = root / "ai-agent/runs" / TAG / "raw.zip"
    name = f"batch/L01/debug-logs/{member}"
    with zipfile.ZipFile(zpath) as zf:
        info = zf.getinfo(name)
    if info.compress_type != zipfile.ZIP_DEFLATED:
        raise AssertionError(f"{name} is not deflated")
    data = bytearray(zpath.read_bytes())
    start = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)  # the local header, then data
    data[start:start + 4] = b"\xff" * 4
    zpath.write_bytes(bytes(data))
    try:
        with zipfile.ZipFile(zpath) as zf, zf.open(name) as fh:
            fh.read()
        raise AssertionError("the corrupted member still reads")
    except zlib.error:
        pass
    return root


def r_race(tmp: Path) -> None:
    g = GOLDEN.read_bytes()
    rows = [golden_row("a.log"), golden_row("b.log")]
    logs = {"a.log": g, "b.log": g}
    ref_root = fake_clone(tmp / "ref", logs, rows)
    c0, _ = run_main(extract_args(ref_root, tmp / "ref" / "store", "--incremental"))
    ref = (tmp / "ref" / "store" / X.STORE_FILE).read_bytes()
    check("R CONTROL: the no-race reference run writes both logs as tier A+B",
          c0 == 0 and [r["tier"] for r in records(tmp / "ref" / "store")] == ["A+B", "A+B"])

    code, out, store = _raced(tmp, "r1", rows, logs, lambda root: zip_cycle(root, TAG, [PROFILE]))
    got = (store / X.STORE_FILE).read_bytes()
    check("R1 FAULT: O3 archives the cycle between two records (raw.zip in, folder and profile deleted): the second "
          "record is still A+B, and the store equals the no-race store byte for byte, exit 0",
          code == 0 and got == ref, f"exit {code}; tiers {[r['tier'] for r in records(store)]}; "
                                    f"{[r['badge_log_join'] for r in records(store)]}")

    code, out, store = _raced(tmp, "r1b", rows, logs,
                              lambda root: zip_cycle(root, TAG, [PROFILE], delete_batch=False))
    got = (store / X.STORE_FILE).read_bytes()
    check("R1b FAULT: raw.zip arrives and the lane profile is deleted, the logs not yet: a record built then (the log "
          "read fine, the badge-log gone from the folder) is rebuilt from the zip: same store as no race",
          code == 0 and got == ref, f"exit {code}; {[r['badge_log_join'] for r in records(store)]}")

    root = fake_clone(tmp / "r2", {"a.log": g}, rows)  # b.log's row exists, its file is not in the folder (yet)
    store = tmp / "r2" / "store"
    code, out = run_main(extract_args(root, store, "--incremental"))
    keys = [r["key"] for r in records(store)]
    cursor = json.loads((store / X.CURSOR_FILE).read_text(encoding="utf-8"))["extracted"]
    check("R2 FAULT: a log missing from a cycle that still has its folder (not in its final archived form) is "
          "DEFERRED: exit 6, not in the store, not in the cursor, named in a WARN",
          code == EXIT_DEFERRED and keys == [f"{TAG}/1/a.log"] and cursor == [f"{TAG}/1/a.log"]
          and f"DEFERRED {TAG}/1/b.log" in out, f"exit {code}; {keys}; {out[-300:]}")
    (root / "ai-agent/runs" / TAG / "batch/L01/debug-logs/b.log").write_bytes(g)
    code, out = run_main(extract_args(root, store, "--incremental"))
    check("R2 CONTROL: the next --incremental retries it and appends it as A+B, exit 0",
          code == 0 and [r["tier"] for r in records(store)] == ["A+B", "A+B"], f"exit {code}; {out[-200:]}")

    root = fake_clone(tmp / "r3", {"a.log": g}, rows)
    zip_cycle(root, TAG, [PROFILE])
    code, out = run_main(extract_args(root, tmp / "r3" / "store", "--incremental"))
    check("R3 CONTROL: in a cycle in its FINAL archived form (raw.zip, no folder) a member the zip lacks is gone for "
          "good: appended as tier A, exit 0, not deferred",
          code == 0 and [r["tier"] for r in records(tmp / "r3" / "store")] == ["A+B", "A"], f"exit {code}; {out[-200:]}")

    root = fake_clone(tmp / "r5", logs, rows)
    zip_cycle(root, TAG, [PROFILE])
    zpath = root / "ai-agent/runs" / TAG / "raw.zip"
    with zipfile.ZipFile(zpath) as zi:
        members = [(i.filename, zi.read(i.filename)) for i in zi.infolist()]
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as zo:  # stored, so one flipped byte is a CRC failure
        for name, data in members:
            zo.writestr(name, data)
        offset = zo.getinfo("batch/L01/debug-logs/b.log").header_offset
    blob = zpath.read_bytes()
    body = g.replace(b"res=Won money=7368", b"res=Wox money=7368", 1)
    at = blob.index(g, offset)  # the stored bytes of THE member the extractor reads (not the profile's twin)
    zpath.write_bytes(blob[:at] + body + blob[at + len(g):])
    code, out = run_main(extract_args(root, tmp / "r5" / "store", "--incremental"))
    keys = [r["key"] for r in records(tmp / "r5" / "store")]
    check("R5 FAULT: a member of a FINAL archive that fails to READ (a bad CRC) is DEFERRED, never written as tier A: "
          "exit 6 (a read failure is never proof the data is gone)", code == EXIT_DEFERRED and len(keys) == 1
          and "read failed" in out, f"exit {code}; {keys}; {out[-240:]}")

    root = deflate_corrupt_cycle(tmp / "r5b", logs, rows)
    code, out = run_main(extract_args(root, tmp / "r5b" / "store", "--incremental"))
    keys = [r["key"] for r in records(tmp / "r5b" / "store")] if (tmp / "r5b/store" / X.STORE_FILE).exists() else []
    check("R5b FAULT: a ZIP_DEFLATED member whose compressed bytes are corrupt (zlib.error, not a CRC error) is "
          "DEFERRED, exit 6, and the other run is stored (the error never escapes the pass)",
          code == EXIT_DEFERRED and keys == [f"{TAG}/1/a.log"] and f"DEFERRED {TAG}/1/b.log: read failed: error("
          in out and "Error -3" in out, f"exit {code}; {keys}; {out[-240:]}")

    root = fake_clone(tmp / "r4", {"a.log": g}, rows)
    shutil.rmtree(root / "ai-agent/runs" / TAG / "batch")
    code, out = run_main(extract_args(root, tmp / "r4" / "store", "--incremental"))
    check("R4 CONTROL: a cycle with no raw data at all (pruned before O3) is not deferred: tier A, exit 0",
          code == 0 and [r["tier"] for r in records(tmp / "r4" / "store")] == ["A", "A"], f"exit {code}; {out[-200:]}")


# ============================================================================================ B1/B2 the deferral bound

def _tiers(store: Path) -> list[str]:
    return ([r["key"].split("/")[-1] + ":" + r["tier"] for r in records(store)]
            if (store / X.STORE_FILE).exists() else [])


def _ledger(store: Path) -> dict:
    p = store / LEDGER_FILE
    return json.loads(p.read_text(encoding="utf-8"))["deferred"] if p.exists() else {}


def _state_json(root: Path, pruned: bool) -> None:
    """The learner's state.json beside runs.jsonl, shaped as learner.py writes it (`cycles[].pruned`)."""
    (root / "ai-agent/data/state.json").write_text(json.dumps(
        {"cycle": 1, "current": None, "cycles": [{"source": "cycle", "tag": TAG, "pruned": pruned}]}), encoding="utf-8")


def b_bound(tmp: Path) -> None:
    check("B the ledger file name the tests read is the extractor's", getattr(X, "LEDGER_FILE", None) == LEDGER_FILE)
    g = GOLDEN.read_bytes()
    rows = [golden_row("a.log"), golden_row("b.log")]
    logs = {"a.log": g, "b.log": g}

    # B1 (a): the review's perm_defer shape. The learner's prune (rmtree, ignore_errors) left an EMPTY batch/.
    root = fake_clone(tmp / "b1empty", logs, rows)
    cdir = root / "ai-agent/runs" / TAG
    shutil.rmtree(cdir / "batch")
    (cdir / "batch").mkdir()
    store = tmp / "b1empty" / "store"
    codes = [run_main(extract_args(root, store, "--incremental"))[0] for _ in range(3)]
    recs = records(store) if (store / X.STORE_FILE).exists() else []
    check("B1 FAULT: a cycle pruned leaving an EMPTY batch/ (no raw.zip) stores both runs as tier A on the first pass, "
          "the reason in raw_missing (was: exit 6 on every pass, nothing stored)",
          codes == [0, 0, 0] and _tiers(store) == ["a.log:A", "b.log:A"]
          and all("missing for good" in str(r["raw_missing"]) for r in recs), (codes, _tiers(store)))

    # B1 (a): a cycle the learner marked pruned in state.json, its rmtree stopped part-way (a.log left, b.log gone).
    for arm, pruned, want_code, want in (("marked", True, 0, ["a.log:A+B", "b.log:A"]),
                                         ("unmarked", False, EXIT_DEFERRED, ["a.log:A+B"])):
        root = fake_clone(tmp / f"b1{arm}", {"a.log": g}, rows)
        _state_json(root, pruned)
        store = tmp / f"b1{arm}" / "store"
        code, out = run_main(extract_args(root, store, "--incremental"))
        b = [r for r in records(store) if r["key"].endswith("b.log")] if (store / X.STORE_FILE).exists() else []
        if pruned:
            check("B1 FAULT: a log missing from a cycle state.json marks PRUNED (its folder half deleted, other logs "
                  "left) is stored as tier A with the reason, exit 0",
                  code == 0 and _tiers(store) == want and "marked the cycle pruned" in str(b[0]["raw_missing"]),
                  f"exit {code}; {_tiers(store)}; {out[-200:]}")
        else:
            check("B1 CONTROL: the same missing log in a cycle NOT marked pruned (other logs still there) is deferred, "
                  "exit 6", code == want_code and _tiers(store) == want, f"exit {code}; {_tiers(store)}")

    # B1 (a): an empty batch/ beside a raw.zip that lacks the member: O3 may be mid-delete, so it is not settled for
    # good by (a) (the general bound (b) still ends it).
    root = fake_clone(tmp / "b1zip", {"a.log": g}, rows)
    zip_cycle(root, TAG, [PROFILE])
    (root / "ai-agent/runs" / TAG / "batch").mkdir()
    store = tmp / "b1zip" / "store"
    code, out = run_main(extract_args(root, store, "--incremental"))
    check("B1 CONTROL: an empty batch/ BESIDE a raw.zip that lacks the log still defers (exit 6): only 'no log AND no "
          "raw.zip' is settled for good", code == EXIT_DEFERRED and _tiers(store) == ["a.log:A+B"],
          f"exit {code}; {_tiers(store)}")

    # B2 (b): the general bound, on a corrupt member of a final archive (never settled by (a)). Clock injected.
    t0 = 1_800_000_000.0
    real_clock = getattr(X, "CLOCK", None)

    def at(work: str, hours: float) -> tuple[int, str]:
        X.CLOCK = lambda: t0 + hours * 3600
        try:
            return run_main(extract_args(roots[work], tmp / work / "store", "--incremental"))
        finally:
            X.CLOCK = real_clock

    roots = {w: deflate_corrupt_cycle(tmp / w, logs, rows) for w in ("b2", "b2age", "b2passes")}
    seq = [at("b2", h) for h in (0, 1, 2)]
    led = _ledger(tmp / "b2" / "store")
    check("B2 CONTROL: before the bound each pass defers (exit 6) and the ledger counts it",
          [c for c, _ in seq] == [EXIT_DEFERRED] * 3 and led.get(f"{TAG}/1/b.log", {}).get("passes") == 3
          and led[f"{TAG}/1/b.log"]["first_deferred_at"] == round(t0), led)
    code4, out4 = at("b2", 25)
    b = [r for r in records(tmp / "b2" / "store") if r["key"].endswith("b.log")]
    check("B2 FAULT: deferred in 3 passes AND 24 h since the first -> stored as tier A, raw_missing 'deferred-timeout: "
          "read failed...', one WARN naming it, exit 0, the ledger entry dropped",
          code4 == 0 and len(b) == 1 and b[0]["tier"] == "A"
          and str(b[0]["raw_missing"]).startswith("deferred-timeout: read failed")
          and out4.count(f"WARN DEFERRED-TIMEOUT {TAG}/1/b.log") == 1 and not _ledger(tmp / "b2" / "store"),
          f"exit {code4}; {_tiers(tmp / 'b2' / 'store')}; {out4[-300:]}")
    before = (tmp / "b2" / "store" / X.STORE_FILE).read_bytes()
    code5, out5 = at("b2", 26)
    check("B2 CONTROL: the next pass is a no-op (exit 0, store unchanged, no WARN again)",
          code5 == 0 and (tmp / "b2" / "store" / X.STORE_FILE).read_bytes() == before and "WARN" not in out5,
          f"exit {code5}; {out5[-200:]}")
    ages = [at("b2age", h)[0] for h in (0, 1, 2, 3, 23.9)]
    check("B2 CONTROL (age): 5 deferred passes within 24 h of the first all defer (passes alone never end it)",
          ages == [EXIT_DEFERRED] * 5 and _tiers(tmp / "b2age" / "store") == ["a.log:A+B"], ages)
    passes = [at("b2passes", h)[0] for h in (0, 30, 31)]
    code_p, _ = at("b2passes", 32)
    check("B2 CONTROL (passes): a run first deferred 30 h ago but in only 1-2 passes still defers; its 4th pass, after "
          "3 deferred passes, stores it (time alone never ends it)",
          passes == [EXIT_DEFERRED] * 3 and code_p == 0 and _tiers(tmp / "b2passes" / "store") == ["a.log:A+B",
                                                                                                    "b.log:A"],
          (passes, code_p))

    # The ledger follows a recovery: a log missing from a fresh cycle defers, then is stored once it appears.
    root = fake_clone(tmp / "b2rec", {"a.log": g}, rows)
    store = tmp / "b2rec" / "store"
    c1, _ = run_main(extract_args(root, store, "--incremental"))
    led1 = _ledger(store)
    (root / "ai-agent/runs" / TAG / "batch/L01/debug-logs/b.log").write_bytes(g)
    c2, _ = run_main(extract_args(root, store, "--incremental"))
    check("B2 CONTROL: a deferred run that recovers is stored A+B and leaves the ledger",
          c1 == EXIT_DEFERRED and led1.get(f"{TAG}/1/b.log", {}).get("passes") == 1 and c2 == 0
          and _tiers(store) == ["a.log:A+B", "b.log:A+B"] and _ledger(store) == {}, (c1, led1, c2, _ledger(store)))


# ============================================================================================ G4b the write guard

def _junction(link: Path, target: Path) -> bool:
    """A directory junction (no admin rights needed), as `mklink /J` makes it."""
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, text=True,
                       timeout=30)
    return r.returncode == 0 and link.is_dir()


def _short(p: Path) -> str | None:
    """The 8.3 short spelling of `p`, or None where the volume makes no short names."""
    import ctypes  # noqa: PLC0415 - Windows only, and only here
    buf = ctypes.create_unicode_buffer(2048)
    n = ctypes.windll.kernel32.GetShortPathNameW(str(p), buf, 2048)
    return buf.value if n and "~" in buf.value and buf.value.casefold() != str(p).casefold() else None


def g_paths(tmp: Path) -> None:
    g = GOLDEN.read_bytes()
    fakerepo = tmp / "fakerepo"
    (fakerepo / "ai_player" / "knowledge").mkdir(parents=True)
    root = fake_clone(tmp / "Long Clone Name Here", {"golden.log": g}, [golden_row()])
    inputs = ["--runs-jsonl", root / "ai-agent/data/runs.jsonl", "--runs-dir", root / "ai-agent/runs",
              "--profiles-dir", root / "sandbox-pokebot/profiles"]

    def attempt(store, repo: Path = fakerepo, clone: Path = root) -> tuple[int, list[str], str]:
        code, out = run_main(["--incremental", "--clone", clone, "--store", store, "--repo", repo, *inputs])
        landed = [str(p) for base in (fakerepo / "ai_player", root)
                  for name in (X.STORE_FILE, X.LOCK_FILE, getattr(X, "MUTEX_FILE", ".lock.mutex"))
                  for p in base.rglob(name)]
        for p in landed:  # the next arm starts clean (a landed write is in a scratch tree)
            shutil.rmtree(Path(p).parent, ignore_errors=True)
        return code, landed, out

    code, landed, out = attempt(tmp / "ok_store")
    check("G4b CONTROL: a store outside every protected tree is written", code == 0 and not landed
          and (tmp / "ok_store" / X.STORE_FILE).is_file(), out[-200:])
    links: list[Path] = []
    try:
        # (what, the --store spelling, whether the resolved-path layer can see it: all but the UNC share)
        arms = [("upper case and backslashes into ai_player/",
                 str(fakerepo / "AI_PLAYER" / "Knowledge" / "exp").upper().replace("/", "\\"), True),
                ("a \\\\?\\ prefix into ai_player/", "\\\\?\\" + str(fakerepo / "ai_player" / "knowledge" / "exp"), True)]
        j_sub, j_clone = tmp / "J_sub", tmp / "J_clone"
        if _junction(j_sub, fakerepo / "ai_player" / "knowledge") and _junction(j_clone, root / "ai-agent"):
            links += [j_sub, j_clone]
            arms += [("a junction to a folder inside ai_player/", j_sub / "exp", True),
                     ("a junction into the clone", j_clone / "exp", True)]
        else:
            skip("G4b junction arms", "mklink /J failed on this machine")
        short = _short(root)
        if short:
            arms.append((f"the clone's 8.3 short name (...{short[-30:]})", short + "\\ai-agent\\exp", True))
        else:
            skip("G4b short-name arm", "this volume makes no 8.3 short names")
        unc = "\\\\localhost\\" + str(root)[0] + "$" + str(root)[2:]
        if os.path.isdir(unc):
            arms.append(("a UNC admin share (\\\\localhost\\C$) into the clone", unc + "\\ai-agent\\exp", False))
        else:
            skip("G4b UNC arm", "no \\\\localhost admin share on this machine")
        for what, store, _ in arms:
            code, landed, out = attempt(store)
            check(f"G4b FAULT: a store reached by {what} is REFUSED, nothing written", code == X.EXIT_REFUSED
                  and not landed, f"exit {code}; landed {landed}; {out[-160:]}")
        # The module's own defaults stay guarded whatever the arguments say (pointed into scratch trees here, so a
        # broken guard writes only there).
        saved = X.REPO, X.DEFAULT_CLONE
        try:
            X.REPO = fakerepo
            code, landed, out = attempt(fakerepo / "ai_player" / "knowledge" / "exp", repo=tmp / "elsewhere_repo")
            check("G4b FAULT: --repo pointed elsewhere does not unguard this checkout's ai_player/",
                  code == X.EXIT_REFUSED and not landed, f"exit {code}; {landed}")
            X.REPO = saved[0]
            X.DEFAULT_CLONE = root
            code, landed, out = attempt(root / "ai-agent" / "exp", clone=tmp / "elsewhere_clone")
            check("G4b FAULT: --clone pointed elsewhere does not unguard the DEFAULT clone",
                  code == X.EXIT_REFUSED and not landed, f"exit {code}; {landed}")
        finally:
            X.REPO, X.DEFAULT_CLONE = saved
        code, landed, out = attempt(root / "ai-agent" / "runs" / "exp", clone=tmp / "elsewhere_clone")
        check("G4b FAULT: a store inside a tree the run READS (--runs-dir) is refused even with --clone elsewhere",
              code == X.EXIT_REFUSED and not landed, f"exit {code}; {landed}")
        # Each layer ALONE (the other switched off), so neither can hide behind the other.
        for layer, off, wanted in (("resolved-path", "_inside_by_identity", [a for a in arms if a[2]]),
                                   ("file-identity", "_inside_by_path", arms)):
            real = getattr(X, off)
            setattr(X, off, lambda p, r: False)
            try:
                res = [(what, attempt(store)) for what, store, _ in wanted]
            finally:
                setattr(X, off, real)
            bad = [(w, c, la) for w, (c, la, _) in res if c != X.EXIT_REFUSED or la]
            check(f"G4b FAULT (the {layer} layer ALONE): its {len(res)} spellings are still REFUSED",
                  res and not bad, bad)
    finally:
        for link in links:
            os.rmdir(link)  # removes the junction only, never its target


def _hardlink(link: Path, target: Path) -> bool:
    """A hard link (`mklink /H`, no admin rights needed on NTFS), confirmed by the link count."""
    r = subprocess.run(["cmd", "/c", "mklink", "/H", str(link), str(target)], capture_output=True, text=True,
                       timeout=30)
    return r.returncode == 0 and link.is_file() and os.stat(target).st_nlink == 2


def g_hardlinks(tmp: Path) -> None:
    g = GOLDEN.read_bytes()
    root = fake_clone(tmp / "hl", {"golden.log": g}, [golden_row()])
    good = tmp / "hl" / "good"
    run_main(extract_args(root, good))
    victims = root / "ai-agent" / "data"
    # A new row waits, so a run that is NOT refused really writes (into the linked file, for the store file).
    with open(root / "ai-agent/data/runs.jsonl", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(golden_row("golden2.log")) + "\n")
    (root / "ai-agent/runs" / TAG / "batch/L01/debug-logs/golden2.log").write_bytes(g)
    made = 0
    for name in (X.STORE_FILE, X.CURSOR_FILE, LEDGER_FILE, LEDGER_FILE + ".tmp", X.CURSOR_FILE + ".tmp",
                 X.LOCK_FILE, X.MUTEX_FILE):
        store = tmp / "hl" / f"s_{name.strip('.')}"
        shutil.copytree(good, store)
        (store / name).unlink(missing_ok=True)
        victim = victims / f"victim_{name.strip('.')}"
        # The store's own files keep a VALID body (so only the link check can refuse them); a stale lock, so only the
        # link check can refuse it (a fresh one is refused as held).
        body = (good / name).read_bytes() if (good / name).is_file() else b"VICTIM inside the clone\n"
        victim.write_bytes(body)
        if name == X.LOCK_FILE:
            old = time.time() - X.LOCK_STALE_S - 60
            os.utime(victim, (old, old))
        if not _hardlink(store / name, victim):
            skip("G4d hard-link arms", "mklink /H failed on this machine")
            return
        made += 1
        before = sorted(p.name for p in store.iterdir())
        code, out = run_main(extract_args(root, store, "--incremental"))
        check(f"G4d FAULT: a hard link planted at <store>/{name} (to a file inside the clone) is REFUSED, the clone's "
              f"file untouched, nothing written in the store", code == X.EXIT_REFUSED and victim.is_file()
              and victim.read_bytes() == body and sorted(p.name for p in store.iterdir()) == before,
              f"exit {code}; {out[-160:]}")
    pri_victim = victims / "victim_priors.json"
    pri_victim.write_bytes(b"{}\n")
    out_file = tmp / "hl" / "priors.json"
    if _hardlink(out_file, pri_victim):
        code, out = run_main(["--priors", "--store", good, "--priors-out", out_file, "--clone", root, "--force-priors"])
        check("G4d FAULT: a hard link at the priors file (to a file inside the clone) is REFUSED, the clone's file "
              "untouched", code == X.EXIT_REFUSED and pri_victim.read_bytes() == b"{}\n", f"exit {code}; {out[-160:]}")
        out_file.unlink()
    out_file.write_bytes(b"{}\n")  # an ORDINARY existing priors file: regenerated
    code, out = run_main(["--priors", "--store", good, "--priors-out", out_file, "--clone", root, "--force-priors"])
    check("G4d CONTROL: an ordinary existing priors file (one link) is regenerated", code == 0
          and json.loads(out_file.read_text(encoding="utf-8")).get("source") == X.CORPUS, out[-160:])
    code, out = run_main(extract_args(root, good, "--incremental"))
    check("G4d CONTROL: an ordinary existing store (every file one link) takes the new record, exit 0",
          code == 0 and len(records(good)) == 2 and made == 7, f"exit {code}; {out[-160:]}")


def g_priors_store(tmp: Path) -> None:
    g = GOLDEN.read_bytes()
    fakerepo = tmp / "fakerepo"
    (fakerepo / "ai_player").mkdir(parents=True)
    root = fake_clone(tmp / "ps", {"golden.log": g}, [golden_row()])
    good = tmp / "ps" / "store"
    run_main(extract_args(root, good))
    for what, store in (("inside the clone", root / "ai-agent" / "data" / "newdir"),
                        ("inside ai_player/", fakerepo / "ai_player" / "knowledge" / "exp")):
        code, out = run_main(["--priors", "--store", store, "--priors-out", tmp / "ps" / "p.json", "--clone", root,
                              "--repo", fakerepo])
        check(f"G4c FAULT: --priors with its --store {what} is REFUSED before the lock: no folder, no .lock",
              code == X.EXIT_REFUSED and not store.exists() and not (tmp / "ps" / "p.json").exists(),
              f"exit {code}; exists {store.exists()}; {out[-160:]}")
    for what, store in (("an EXISTING store inside the clone", root / "ai-agent" / "data" / "oldstore"),
                        ("an EXISTING store inside ai_player/", fakerepo / "ai_player" / "oldstore")):
        store.mkdir(parents=True)
        shutil.copy2(good / X.STORE_FILE, store / X.STORE_FILE)  # a store that would read fine: only the guard stops it
        code, out = run_main(["--priors", "--store", store, "--priors-out", tmp / "ps" / "p.json", "--clone", root,
                              "--repo", fakerepo])
        check(f"G4c FAULT: --priors on {what} is REFUSED before the lock: no lock file of any kind is created there",
              code == X.EXIT_REFUSED and sorted(p.name for p in store.iterdir()) == [X.STORE_FILE]
              and not (tmp / "ps" / "p.json").exists(), f"exit {code}; {sorted(p.name for p in store.iterdir())}")
    missing = tmp / "ps" / "no-such-store"
    code, out = run_main(["--priors", "--store", missing, "--priors-out", tmp / "ps" / "p.json", "--clone", root])
    check("G4c FAULT: a read-only --priors with a missing store is refused and never creates it",
          code == X.EXIT_REFUSED and not missing.exists(), f"exit {code}; {out[-160:]}")
    code, out = run_main(["--priors", "--store", good, "--priors-out", tmp / "ps" / "p.json", "--clone", root,
                          "--repo", fakerepo])
    check("G4c CONTROL: --priors on a real store outside the protected trees writes the file",
          code == 0 and (tmp / "ps" / "p.json").is_file(), out[-200:])


# ============================================================================================ G2b the store lock

def _stale_race(tmp: Path, name: str, mutex: bool = True, verify: bool = True) -> list[str]:
    """Two runs that BOTH see a stale lock (forced: each waits at a barrier right after reading the lock's age), the
    second one's retire delayed until the first has taken a fresh lock (the review's interleaving). -> who acquired."""
    store = tmp / name
    store.mkdir()
    (store / X.LOCK_FILE).write_text("1 1", encoding="utf-8")
    old = time.time() - X.LOCK_STALE_S - 60
    os.utime(store / X.LOCK_FILE, (old, old))
    barrier = threading.Barrier(2)

    class SlowPath(type(store)):
        def stat(self, *a, **k):
            st = super().stat(*a, **k)
            if self.name == X.LOCK_FILE:
                try:
                    barrier.wait(timeout=1.0)
                except threading.BrokenBarrierError:
                    pass
            return st

    held: list[str] = []
    real_replace, real_unlink = os.replace, Path.unlink
    patched: dict = {}

    def slow_replace(src, dst, *a, **k):
        if threading.current_thread().name == "B" and Path(src).name == X.LOCK_FILE:
            time.sleep(0.3)  # B retires AFTER A has taken its fresh lock
        return real_replace(src, dst, *a, **k)

    def slow_unlink(self, *a, **k):  # the same delay for a retire by unlink (how 57a7ec28 retired a stale lock)
        if threading.current_thread().name == "B" and self.name == X.LOCK_FILE and not held:
            time.sleep(0.3)
        return real_unlink(self, *a, **k)

    def plain_retire(self) -> None:  # the retire WITHOUT checking it moved the lock it judged stale
        try:
            age = time.time() - self.path.stat().st_mtime
        except FileNotFoundError:
            return
        if age < X.LOCK_STALE_S:
            raise X.Refused("held")
        aside = self.path.with_name(f"{X.LOCK_FILE}.stale.{uuid.uuid4().hex}")
        try:
            os.replace(self.path, aside)
        except FileNotFoundError:
            return
        aside.unlink(missing_ok=True)

    def worker(name: str) -> None:
        lk = X.StoreLock(store)
        lk.path = SlowPath(lk.path)
        try:
            lk.__enter__()
        except X.Refused:
            return
        held.append(name)
        time.sleep(1.0)
        lk.__exit__(None, None, None)

    os.replace, Path.unlink = slow_replace, slow_unlink
    if not mutex:
        patched["_OsMutex"] = X._OsMutex
        X._OsMutex = lambda path: contextlib.nullcontext()
    if not verify:
        patched["_retire_if_stale"] = X.StoreLock._retire_if_stale
        X.StoreLock._retire_if_stale = plain_retire
    try:
        ts = [threading.Thread(target=worker, args=(n,), name=n) for n in ("A", "B")]
        for t in ts:
            t.start()
        for t in ts:
            t.join(timeout=60)
    finally:
        os.replace, Path.unlink = real_replace, real_unlink
        if "_OsMutex" in patched:
            X._OsMutex = patched["_OsMutex"]
        if "_retire_if_stale" in patched:
            X.StoreLock._retire_if_stale = patched["_retire_if_stale"]
    return sorted(held)


def g_lock(tmp: Path) -> None:
    got = _stale_race(tmp, "race_real")
    check("G2b FAULT (race_real): two runs that both saw a stale lock (the second retiring after the first took a "
          "fresh lock) -> exactly ONE acquires", len(got) == 1, got)
    store = tmp / "held"
    store.mkdir()
    saved = X.MUTEX_WAIT_S
    X.MUTEX_WAIT_S = 0.3
    try:
        with X._OsMutex(store / X.MUTEX_FILE):
            try:
                with X.StoreLock(store):
                    took = True
            except X.Refused:
                took = False
    finally:
        X.MUTEX_WAIT_S = saved
    check("G2b FAULT: while another run holds the take-mutex, a run REFUSES and creates no .lock",
          not took and not (store / X.LOCK_FILE).exists(), took)
    with X.StoreLock(store):
        pass
    check("G2b CONTROL: with the mutex free the lock is taken and released", not (store / X.LOCK_FILE).exists())

    both = _stale_race(tmp, "race_none", mutex=False, verify=False)
    check("G2b HARNESS: with BOTH layers off, the forced interleaving makes both runs acquire (the race is real, so the "
          "arms below are not vacuous)", both == ["A", "B"], both)
    for name, kw in (("race_mutex_only", {"verify": False}), ("race_verify_only", {"mutex": False})):
        got = _stale_race(tmp, name, **kw)
        check(f"G2b FAULT ({name}): two runs that both saw a stale lock -> exactly ONE acquires", len(got) == 1, got)

    store = tmp / "own"
    store.mkdir()
    lk = X.StoreLock(store)
    lk.__enter__()
    (store / X.LOCK_FILE).write_bytes(b"999 1 another-run")  # the lock now belongs to someone else
    lk.__exit__(None, None, None)
    lock = store / X.LOCK_FILE
    check("G2b FAULT: a run removes .lock only while it holds ITS token (someone else's lock survives its exit)",
          lock.is_file() and lock.read_bytes() == b"999 1 another-run", lock.is_file())
    g_lock_release(tmp)


@contextlib.contextmanager
def _exclusive(path: Path):
    """`path` opened with NO sharing at all (CreateFileW, share mode 0): no other handle may read, write or delete it,
    the worst a foreign process can do to `.lock`."""
    import ctypes  # noqa: PLC0415 - Windows only, and only here
    from ctypes import wintypes  # noqa: PLC0415
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                                wintypes.DWORD, wintypes.HANDLE]
    h = k32.CreateFileW(str(path), 0x80000000, 0, None, 3, 0x80, None)  # GENERIC_READ, no share, OPEN_EXISTING
    if h in (None, wintypes.HANDLE(-1).value):
        raise OSError(ctypes.get_last_error(), "CreateFileW failed")
    try:
        yield
    finally:
        k32.CloseHandle(h)


def _exit_while_read(store: Path, hold_s: float, with_mutex: bool, how: str = "thread") -> tuple[str, bool, bool]:
    """The review round 2 interleaving: another run has `.lock` OPEN for reading (as `_retire_if_stale`'s read_bytes
    does) at the instant this run's `__exit__` removes it. `with_mutex`: the reader also holds the take-mutex, as the
    real reader does. `how`: "thread" a reader thread holding a Python handle `hold_s`; "sync" the review's
    lock_exit.py (a Python handle open for the WHOLE of __exit__, closed only after it returns); "exclusive" a thread
    holding a no-sharing handle `hold_s`. -> (what __exit__ printed or raised, .lock left behind, a later run took
    the lock)."""
    store.mkdir()
    lk = X.StoreLock(store)
    lk.__enter__()
    ready = threading.Event()

    def reader() -> None:
        with (X._OsMutex(store / X.MUTEX_FILE) if with_mutex else contextlib.nullcontext()):
            with (_exclusive(store / X.LOCK_FILE) if how == "exclusive" else open(store / X.LOCK_FILE, "rb")):
                ready.set()
                time.sleep(hold_s)

    t = threading.Thread(target=reader)
    held = open(store / X.LOCK_FILE, "rb") if how == "sync" else None
    if held is None:
        t.start()
        ready.wait(10)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            lk.__exit__(None, None, None)
        said = buf.getvalue()
    except Exception as e:  # noqa: BLE001 - exactly what this measures (df792190 raised PermissionError here)
        said = f"raised {type(e).__name__}: {e}"
    finally:
        if held is not None:
            held.close()
    if held is None:
        t.join(30)
    left = (store / X.LOCK_FILE).exists()
    try:
        with X.StoreLock(store):
            later = True
    except X.Refused:
        later = False
    return said, left, later


def g_lock_release(tmp: Path) -> None:
    # The reader holds the mutex for 1 s, longer than the whole retry window (UNLINK_TRIES x UNLINK_RETRY_S = 0.5 s):
    # only waiting for the mutex releases the lock in time.
    said, left, later = _exit_while_read(tmp / "rel_mutex", 1.0, with_mutex=True)
    check("G2c FAULT: a reader holding the take-mutex and a handle on .lock while this run exits: __exit__ waits for "
          "the mutex, removes .lock, no WARN, and a later run acquires", not said and not left and later,
          (said[-200:], left, later))
    said, left, later = _exit_while_read(tmp / "rel_retry", 0.2, with_mutex=False)
    check("G2c FAULT: a reader holding only a handle on .lock for 0.2 s: the unlink is retried, .lock removed, and a "
          "later run acquires", not said and not left and later, (said[-200:], left, later))
    said, left, later = _exit_while_read(tmp / "rel_sync", 0, with_mutex=False, how="sync")
    check("G2c FAULT (the review's lock_exit.py): a handle open for the WHOLE of __exit__: the lock is marked released "
          "in place (a NOTE, no exception), and a later run acquires at once",
          "marked released" in said and not said.startswith("raised") and later, (said[-200:], left, later))
    said, left, later = _exit_while_read(tmp / "rel_excl", 1.0, with_mutex=False, how="exclusive")
    check("G2c FAULT: a no-sharing handle (neither delete nor mark possible): __exit__ returns with a WARN, never an "
          "exception", said.startswith("WARN could not remove"), said[-200:])

    # The mark re-reads the lock through its OWN handle: a lock that turned out not to be ours by then (the earlier
    # read is made to lie here, so the moment is deterministic) is never marked released.
    store = tmp / "rel_foreign"
    store.mkdir()
    lk = X.StoreLock(store)
    lk.__enter__()
    foreign = b"999 1 another-run"
    (store / X.LOCK_FILE).write_bytes(foreign)
    real_rb, real_unlink = Path.read_bytes, Path.unlink

    def lying_read(self):
        return lk.token if self.name == X.LOCK_FILE else real_rb(self)

    def no_unlink(self, *a, **k):
        if self.name == X.LOCK_FILE:
            raise PermissionError(32, "planted: in use", str(self))
        return real_unlink(self, *a, **k)
    Path.read_bytes, Path.unlink = lying_read, no_unlink
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            lk.__exit__(None, None, None)
    finally:
        Path.read_bytes, Path.unlink = real_rb, real_unlink
    check("G2c FAULT: the release mark never rewrites a lock that is not this run's (checked through its own handle)",
          (store / X.LOCK_FILE).read_bytes() == foreign, (store / X.LOCK_FILE).read_bytes())

    # Through main(): a .lock that cannot be deleted after a SUCCESSFUL append must never turn it into exit 5.
    def through_main(name: str, deny_open: bool) -> tuple[int, str, Path]:
        root = fake_clone(tmp / name, {"golden.log": GOLDEN.read_bytes()}, [golden_row()])
        store = tmp / name / "store"
        real_unlink, real_open = Path.unlink, Path.open

        def no_unlink(self, *a, **k):
            if self.name == X.LOCK_FILE:
                raise PermissionError(32, "planted: the file is in use by another process", str(self))
            return real_unlink(self, *a, **k)

        def no_write(self, mode="r", *a, **k):
            if self.name == X.LOCK_FILE and "+" in mode:
                raise PermissionError(32, "planted: the file is in use by another process", str(self))
            return real_open(self, mode, *a, **k)
        Path.unlink = no_unlink
        if deny_open:
            Path.open = no_write
        try:
            code, out = main_exit(extract_args(root, store, "--incremental"))
        finally:
            Path.unlink, Path.open = real_unlink, real_open
        return code, out, store

    code, out, store = through_main("rel_main", deny_open=False)
    try:
        with X.StoreLock(store):
            later = True
    except X.Refused:
        later = False
    check("G2c FAULT: a .lock that cannot be deleted after a SUCCESSFUL append: exit 0, the record stored, the lock "
          "marked released, and the next run takes it", code == 0 and _tiers(store) == ["golden.log:A+B"]
          and "marked released" in out and later, f"exit {code}; later {later}; {out[-240:]}")
    code, out, store = through_main("rel_main2", deny_open=True)
    check("G2c FAULT: a .lock that can be neither deleted nor marked: exit 0, the record stored, a WARN naming the "
          "lock (never exit 5, a crash that did not happen)",
          code == 0 and _tiers(store) == ["golden.log:A+B"] and "WARN could not remove" in out,
          f"exit {code}; {out[-240:]}")
    (store / X.LOCK_FILE).unlink(missing_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), X.StoreLock(store):
        pass
    check("G2c CONTROL: an ordinary exit removes .lock with no WARN", not (store / X.LOCK_FILE).exists()
          and not buf.getvalue(), buf.getvalue())


# ============================================================================================ main

def main() -> int:
    tests = (e1, e2, e3, e4, e5, e6a, e6b, e7, e7b, e7c, e8, e10, g_guards, g_paths, g_priors_store, g_hardlinks,
             g_lock, j1, p1, r_race, b_bound, n2, c1)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        tmp = Path(td)
        for test in tests:
            sub = tmp / test.__name__
            sub.mkdir()
            try:
                test(sub)
            except Exception as ex:  # noqa: BLE001 - a crash is a FAIL with its reason, never a silent pass
                import traceback
                check(f"{test.__name__.upper()} crashed", False, f"{type(ex).__name__}: {ex} "
                      f"{traceback.format_exc().splitlines()[-3:]}")
    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        line = ("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:400]}")
        print(line.encode("ascii", "backslashreplace").decode("ascii"))
    for name, why in SKIPPED:
        print(f"SKIPPED {name}: {why}")
    verdict = "FAILED" if bad else ("WARN (real-data arms SKIPPED: not a pass)" if SKIPPED else "ALL PASS")
    print(f"{verdict} ({len(RESULTS)} checks, {len(bad)} failed, {len(SKIPPED)} skipped)")
    return 1 if bad else (WARN_EXIT if SKIPPED else 0)


if __name__ == "__main__":
    sys.exit(main())
