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
      MASKED, not leaked. CONTROL a generated file (and, with the clone, one from the real rows) passes.
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
import time
import zipfile
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
WARN_EXIT = 4


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
    with contextlib.redirect_stdout(buf):
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
    recs = X.extract(sub, set(), CLONE / "ai-agent" / "runs", CLONE / "sandbox-pokebot" / "profiles", ids, names)
    both = [r for r in recs if r["tier"] == "A+B"]
    compared = sum(len(r["agrees_with_runs_jsonl"]) for r in both)
    dis = [(r["key"], d) for r in recs for d in r["disagreements"]]
    check(f"E2 REAL ({', '.join(pick)}): every tier-B boss equals runs.jsonl's boss_log", not dis and compared > 0,
          f"{len(dis)} disagree of {compared}: {dis[:3]}")
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
    base = X.build_priors(recs, set())
    flipped = copy.deepcopy(recs)
    for r in flipped:
        if r["key"] == flip_key:
            r["usable"] = False
    after = X.build_priors(flipped, set())
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

def zip_cycle(root: Path, tag: str, profiles: list[str], mutate: tuple[str, bytes, bytes] | None = None) -> None:
    """Replace runs/<tag>/batch and the profiles with runs/<tag>/raw.zip (stdlib; names as O3 writes them)."""
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
    root = fake_clone(tmp / "e7", {"golden.log": GOLDEN.read_bytes()}, [golden_row(), tl_row(1), dirty])
    store = tmp / "e7" / "store"
    run_main(extract_args(root, store))
    out = tmp / "e7" / "priors.json"
    code, msg = run_main(["--priors", "--store", store, "--priors-out", out, "--clone", root])
    text = out.read_text(encoding="utf-8") if out.exists() else ""
    check("E7 CONTROL: the generated priors pass the gate; the dirty wall label is MASKED, not leaked",
          code == 0 and text and "3E751CAF" not in text and "Kingdra" not in text and "(5, 3)" not in text
          and "FLAG_" not in text, msg)
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
        def leaky(recs, species_):
            p = real_build(recs, species_)
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
        problems = X.check_ai_facing(X.build_priors(recs, species), species)
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


# ============================================================================================ main

def main() -> int:
    tests = (e1, e2, e3, e4, e5, e6a, e6b, e7, e8, e10, g_guards, j1)
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
