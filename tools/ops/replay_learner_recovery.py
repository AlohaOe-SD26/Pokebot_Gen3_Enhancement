"""Off-gate REAL-DATA acceptance for the bot tuner's game journal and crash recovery (backlog E2 + O8, build spec
`PROJECT KNOWLEDGE/ai-research-notes/2026-10-28-E2-O8-BUILD-SPEC.md` section 4, checks RD1 and RD2).

WHY IT EXISTS, AND WHY IT IS NOT IN test_agent.py: test_agent.py is the learner's deploy gate and runs INSIDE the live
clone, so it must never depend on live data. These checks replay real cycles of that clone through THIS checkout's
`ai-agent/learner.py`:

- RD1 (ai0031, the 2026-10-17 shutdown): its `raw.zip` and `plan.json` are copied out and unzipped into a scratch
  folder, and `recover_records` is run on them, as the next start would have run it had E2 existed then (no journal).
- RD2 (faithfulness): for finished cycles whose lane profiles AND copied batch AND ground-truth rows all exist, (a)
  `journal_games` (stable window 0) must journal records equal, field for field, to the clone's own runs.jsonl rows;
  (b) `recover_records` over the lane PROFILES, once with no journal and once with (a)'s, must give exactly the clone's
  rows for that batch: the same key set by IDENTITY `(batch, lane, log)`, and every row equal field for field, the
  censored newest logs included. Any difference is a STOP for the deploy.

SAFETY: the clone is READ-ONLY here. Every learner write path points into `--scratch`; the clone's batch folders and
lane profiles are passed only as read sources, and their (size, mtime) are snapshotted before and compared after, so a
write into them would be reported. It runs no git and starts no process.

Usage (from the repo root):
  py -3.12 tools/ops/replay_learner_recovery.py --scratch <empty dir> [--rd1] [--rd2 ai0049 ai0050 ai0051 ai0052]
  py -3.12 tools/ops/replay_learner_recovery.py --predict-only ...   (print the registered predictions and exit)
Exit 0 = every check passed; 1 = a check failed (the output names it); 2 = a precondition is missing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AI = REPO / "ai-agent"
sys.path.insert(0, str(AI))
import learner  # noqa: E402

DEFAULT_CLONE = Path(r"C:\Remote Projects\pokebot-learner")
#: Every learner write path, pointed into the scratch folder (the same names test_agent.py isolates).
WRITE_PATHS = {"RUNS": "runs", "DATA": "data", "FINDINGS": "findings", "INBOX": "inbox", "PUBLISHED": "published",
               "RUNS_FILE": "data/runs.jsonl", "CYCLES_FILE": "data/cycles.jsonl", "STATE_FILE": "data/state.json",
               "STATE_BAK": "data/state.json.bak", "CRASH_FILE": "data/crashes.json", "LOCK": "data/agent.lock",
               "LOG": "data/learner.log", "OPS_FILE": "data/ops.jsonl", "STOP": "STOP",
               "ATTENTION": "findings/ATTENTION.md", "DEPLOYMENT": "DEPLOYMENT"}


def canon(rec: dict) -> dict:
    return json.loads(json.dumps(rec, default=str))


def key(r: dict) -> tuple:
    return r.get("batch"), r.get("lane"), r.get("log")


def point_into(scratch: Path, profiles: Path) -> None:
    for name, rel in WRITE_PATHS.items():
        setattr(learner, name, scratch / rel)
    learner.PROFILES = profiles
    learner.DATA.mkdir(parents=True, exist_ok=True)


def snapshot(paths: list[Path]) -> dict[str, tuple[int, int]]:
    out = {}
    for root in paths:
        for p in sorted(root.rglob("*")) if root.is_dir() else []:
            if p.is_file():
                st = p.stat()
                out[str(p)] = (st.st_size, st.st_mtime_ns)
    return out


def predictions(rd1: bool, rd2: list[str]) -> list[str]:
    out = ["REGISTERED PREDICTIONS (written before any check runs):"]
    if rd1:
        out += ["  RD1 ai0031: recover_records returns 24 records (the 24 profile logs of its manifest, all under "
                "profiles/endless-ai0031-H*/debug-logs); per lane in ARMS order H1-H12: 2,1,1,2,2,3,1,3,4,1,2,2",
                "  RD1 ai0031: the 12 logs that are NOT the newest of their lane are complete (12 complete at least); "
                "each lane's newest log is complete only if it reached the Champion or derail #5 (count reported)",
                "  RD1 ai0031: recovered = '24 from lane profiles, 0 from the journal'; every record has source "
                "'ai0031', a genome_id, and batch '20261017-023005'"]
    for tag in rd2:
        out += [f"  RD2(a) {tag}: every journaled record equals its clone runs.jsonl row field for field "
                f"(0 differences); the journal holds exactly the clone's NOT-newest-in-lane rows",
                f"  RD2(b) {tag}: recover_records without a journal AND with (a)'s journal: key set == the clone's "
                f"rows for that batch (by (batch, lane, log)), every row equal field for field (0 differences)"]
    out.append("  SAFETY: no file under the clone's batch folders or lane profiles changes size or mtime")
    return out


def restore_zip(zpath: Path, manifest: Path, dest: Path) -> int:
    """Extract every member, then every `dup_of` member from its target, with each file's mtime set from the zip's own
    date_time (local time, 2 s resolution) so the journal's mtime filter sees roughly the original times."""
    man = json.loads(manifest.read_text(encoding="utf-8"))
    n = 0
    with zipfile.ZipFile(zpath) as zf:
        infos = {i.filename: i for i in zf.infolist()}
        for m in man["members"]:
            src = m.get("dup_of") or m["name"]
            info = infos[src]
            out = dest / m["name"]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(zf.read(info))
            t = dt.datetime(*info.date_time).timestamp()
            os.utime(out, (t, t))
            n += 1
    return n


def rd1(clone_ai: Path, scratch: Path) -> list[str]:
    fails = []
    tag = "ai0031"
    src = clone_ai / "runs" / tag
    work = scratch / "rd1"
    if work.exists():
        raise SystemExit(f"{work} exists: use an empty --scratch")
    copy = work / "copied"
    copy.mkdir(parents=True)
    for name in ("raw.zip", "raw.manifest.json", "plan.json"):
        shutil.copy2(src / name, copy / name)
    tree = work / "tree"
    n = restore_zip(copy / "raw.zip", copy / "raw.manifest.json", tree)
    # the archive names its members batch/<rel> and profiles/<profile>/<rel>: lay them out as the learner sees them
    runs_tag = work / "runs" / tag
    runs_tag.mkdir(parents=True)
    shutil.move(str(tree / "batch"), str(runs_tag / "batch"))
    shutil.copy2(copy / "plan.json", runs_tag / "plan.json")
    point_into(work, tree / "profiles")
    learner.RUNS = work / "runs"
    batch = runs_tag / "batch"
    copied = learner._copied_logs(batch)
    recs, recovered = learner.recover_records(tag, batch)
    meta = json.loads((batch / "ARMS.json").read_text(encoding="utf-8"))
    per_lane = [sum(1 for r in recs if r["lane"] == i + 1) for i in range(len(meta["lanes"]))]
    newest = {}
    for r in recs:
        if r["lane"] not in newest or r["log"] > newest[r["lane"]]["log"]:
            newest[r["lane"]] = r
    newest_keys = {(r["lane"], r["log"]) for r in newest.values()}
    not_newest = [r for r in recs if (r["lane"], r["log"]) not in newest_keys]
    newest_complete = [r for r in newest.values() if r["complete"]]
    print(f"RD1 {tag}: {n} files restored from raw.zip; copied batch logs present: {copied}")
    print(f"RD1 {tag}: {len(recs)} records; recovered = {recovered!r}")
    print(f"RD1 {tag}: per lane (ARMS order): {per_lane}")
    print(f"RD1 {tag}: not-newest {len(not_newest)} (complete {sum(r['complete'] for r in not_newest)}, usable "
          f"{sum(r['usable'] for r in not_newest)}); newest {len(newest)} (complete {len(newest_complete)}: "
          f"{[(r['lane'], r['champion'], r['derails']) for r in newest_complete]})")
    print(f"RD1 {tag}: usable in total {sum(r['usable'] for r in recs)}; champions "
          f"{sum(r['champion'] for r in recs)}; walls {sorted({r['wall'] for r in recs if r['usable']})[:8]}")
    if copied:
        fails.append("RD1: copied batch logs exist in the restored archive (expected none)")
    if len(recs) != 24:
        fails.append(f"RD1: {len(recs)} records, predicted 24")
    if per_lane != [2, 1, 1, 2, 2, 3, 1, 3, 4, 1, 2, 2]:
        fails.append(f"RD1: per-lane counts {per_lane} differ from the prediction")
    if len(not_newest) != 12 or not all(r["complete"] for r in not_newest):
        fails.append(f"RD1: not-newest {len(not_newest)}, complete {sum(r['complete'] for r in not_newest)}; "
                     f"predicted 12 and 12")
    if recovered != "24 from lane profiles, 0 from the journal":
        fails.append(f"RD1: recovered = {recovered!r}")
    bad = [r["log"] for r in recs if r.get("source") != tag or not r.get("genome_id")
           or r.get("batch") != "20261017-023005"]
    if bad:
        fails.append(f"RD1: {len(bad)} record(s) lack source/genome_id/batch: {bad[:3]}")
    for r in newest.values():  # a newest log is complete only by the Champion or derail #5 (today's rule)
        if r["complete"] != bool(r["champion"] or r["derails"] >= 5):
            fails.append(f"RD1: lane {r['lane']} newest {r['log']} complete={r['complete']} breaks the censoring rule")
    return fails


def compare(label: str, got: list[dict], truth: list[dict]) -> list[str]:
    fails = []
    g = {key(r): canon(r) for r in got}
    t = {key(r): canon(r) for r in truth}
    if len(g) != len(got):
        fails.append(f"{label}: duplicate keys among {len(got)} records")
    missing, extra = sorted(set(t) - set(g)), sorted(set(g) - set(t))
    if missing:
        fails.append(f"{label}: {len(missing)} clone row(s) not produced: {missing[:3]}")
    if extra:
        fails.append(f"{label}: {len(extra)} record(s) the clone does not have: {extra[:3]}")
    for k in sorted(set(g) & set(t)):
        if g[k] != t[k]:
            fields = sorted(f for f in set(g[k]) | set(t[k]) if g[k].get(f) != t[k].get(f))
            fails.append(f"{label}: {k} differs in {fields[:6]}")
    return fails


def rd2(clone_ai: Path, profiles: Path, scratch: Path, tags: list[str]) -> list[str]:
    fails = []
    rows = [json.loads(x) for x in (clone_ai / "data" / "runs.jsonl").read_bytes().split(b"\n") if x.strip()]
    for tag in tags:
        batch = clone_ai / "runs" / tag / "batch"
        if not (batch / "ARMS.json").is_file():
            fails.append(f"RD2 {tag}: no copied batch (archived?): use later cycles")
            continue
        meta = json.loads((batch / "ARMS.json").read_text(encoding="utf-8"))
        prof_dirs = [profiles / ln["profile"] for ln in meta["lanes"]]
        if not all(p.is_dir() for p in prof_dirs):
            fails.append(f"RD2 {tag}: a lane profile is gone (archived?): use later cycles")
            continue
        truth = [r for r in rows if r.get("source") == tag and r.get("batch") == meta.get("stamp")]
        before = snapshot([batch] + prof_dirs)
        work = scratch / "rd2" / tag
        work.mkdir(parents=True)
        point_into(work, profiles)
        learner.JOURNAL_STABLE_S = 0.0
        t0 = time.time()
        known: set = set()
        n = learner.journal_games(tag, batch, known)
        journal = learner._journal_records(learner.RUNS / tag / learner.JOURNAL)
        truth_by = {key(r): r for r in truth}
        newest = {}
        for r in truth:
            if r["lane"] not in newest or r["log"] > newest[r["lane"]]:
                newest[r["lane"]] = r["log"]
        not_newest = [r for r in truth if newest[r["lane"]] != r["log"]]
        fa = compare(f"RD2(a) {tag} journal", journal, not_newest)
        with_journal, how_with = learner.recover_records(tag, batch)  # (a)'s journal on disk
        jpath = learner.RUNS / tag / learner.JOURNAL
        jpath.rename(jpath.with_name("games.jsonl.set-aside"))
        bare, how_bare = learner.recover_records(tag, batch)  # no journal
        fb1 = compare(f"RD2(b) {tag} with the journal", with_journal, truth)
        fb2 = compare(f"RD2(b) {tag} without a journal", bare, truth)
        after = snapshot([batch] + prof_dirs)
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        print(f"RD2 {tag}: clone rows {len(truth)} (not newest {len(not_newest)}); journaled {n} "
              f"({len(journal)} read back); with journal: {len(with_journal)} records ({how_with}); without: "
              f"{len(bare)} records ({how_bare}); {time.time() - t0:.1f} s")
        print(f"RD2 {tag}: (a) {len(fa)} difference(s); (b) with journal {len(fb1)}, without {len(fb2)}; "
              f"clone files changed: {len(changed)}")
        for f in fa + fb1 + fb2:
            print("   ", f)
        fails += fa + fb1 + fb2
        if changed:
            fails.append(f"RD2 {tag}: {len(changed)} clone file(s) changed during the replay: {changed[:3]}")
        if not truth:
            fails.append(f"RD2 {tag}: the clone has no rows for this batch")
        if any(k not in truth_by for k in map(key, journal)):
            fails.append(f"RD2 {tag}: a journal record has no clone row")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clone", type=Path, default=DEFAULT_CLONE)
    ap.add_argument("--scratch", type=Path, required=True, help="an EMPTY folder outside the clone")
    ap.add_argument("--rd1", action="store_true")
    ap.add_argument("--rd2", nargs="*", default=[])
    ap.add_argument("--predict-only", action="store_true")
    a = ap.parse_args()
    for line in predictions(a.rd1, a.rd2):
        print(line)
    if a.predict_only:
        return 0
    clone = a.clone.resolve()
    scratch = a.scratch.resolve()
    if scratch.is_relative_to(clone):
        print("--scratch must be outside the clone")
        return 2
    scratch.mkdir(parents=True, exist_ok=True)
    if any(scratch.iterdir()):
        print(f"--scratch {scratch} is not empty")
        return 2
    clone_ai = clone / "ai-agent"
    print(f"\nRESULTS (this checkout's learner code, {REPO}; clone {clone} read-only; scratch {scratch}):")
    fails = []
    if a.rd1:
        fails += rd1(clone_ai, scratch)
    if a.rd2:
        fails += rd2(clone_ai, clone / "sandbox-pokebot" / "profiles", scratch, a.rd2)
    print("\n" + ("ALL RD CHECKS PASS" if not fails else f"{len(fails)} RD FAILURE(S):"))
    for f in fails:
        print("  FAIL", f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
