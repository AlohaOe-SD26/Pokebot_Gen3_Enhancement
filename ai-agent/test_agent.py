"""Offline gate for the learner: `py -3.12 test_agent.py` (no emulator, about 10 seconds). Exit 0 = all pass.

Each check names what it protects. The FAULT rows prove a guard actually bites: a check that passes on broken
input is decoration.
"""
from __future__ import annotations

import json
import random
import shutil
import sys
import tempfile
from pathlib import Path

AI = Path(__file__).resolve().parent
sys.path.insert(0, str(AI))
import brain  # noqa: E402
import consult  # noqa: E402
import knowledge as K  # noqa: E402
import learner  # noqa: E402
import scoring  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def win(opp: int, res: str = "Won") -> str:
    return f"f100 [TRAINER] end opp={opp} class=0x20(LEADER) value=1 lvl_last=1 first=True base=1 res={res} money=1->2"


def make_batch(root: Path) -> Path:
    b = root / "batch"
    a_env, b_env = brain.full_env(K.STEP14_A), brain.full_env(K.STEP14_B)
    (b / "L01" / "debug-logs").mkdir(parents=True)
    (b / "L02" / "debug-logs").mkdir(parents=True)
    (b / "ARMS.json").write_text(json.dumps({
        "stamp": "T", "code_commit": "abc", "arms_text": json.dumps({"arms": {"A": a_env, "B": b_env}}),
        "lanes": [{"arm": "A", "starter": "mudkip", "profile": "endless-x-H1-mudkip"},
                  {"arm": "B", "starter": "torchic", "profile": "endless-x-H2-torchic"}]}), encoding="utf-8")
    hb = ("f{f} [hb] mode=Story (ENDLESS RESET) state=7 controllable=True map=PETALBURG CITY(0,7) pos=(5, 6) "
          "party={p} ids=[]")
    run1 = [win(265), win(266),  # a stale boot's battles BEFORE the run starts must not count
            "f13000 [STEP] 'Story: choosing Mudkip!'", win(265), win(266),
            hb.format(f=500, p="['Marshtomp:L20', 'Poochyena:L10']"), win(269, "Lost"),
            hb.format(f=600, p="['Marshtomp:L30', 'Poochyena:L20']"), win(269, "Lost"),
            "f900 [STORY] DERAIL #5: this boss: 5 losses with no super-effective answer to Normal. Need one"]
    run2 = ["f13000 [STEP] 'Story: choosing Torchic!'", win(265)]  # last log of the lane, no end: censored
    champ = ["f13000 [STEP] 'Story: choosing Torchic!'"] + [win(o) for o in range(265, 273)] + \
            [win(o) for o in range(261, 265)] + [win(335)]
    (b / "L01" / "debug-logs" / "a-1.log").write_text("\n".join(run1), encoding="utf-8")
    (b / "L01" / "debug-logs" / "a-2.log").write_text("\n".join(run2), encoding="utf-8")
    (b / "L02" / "debug-logs" / "b-1.log").write_text("\n".join(champ), encoding="utf-8")
    return b


def test_scoring(tmp: Path) -> None:
    recs = {r["log"]: r for r in scoring.parse_batch(make_batch(tmp), "test")}
    r1, r2, c = recs["a-1.log"], recs["a-2.log"], recs["b-1.log"]
    check("S1 battles before 'choosing' are ignored (KI-119)", r1["badges"] == ["ROXANNE", "BRAWLY"], r1["badges"])
    check("S2 losses counted per boss", r1["losses"] == {"NORMAN": 2}, r1["losses"])
    check("S3 a run followed by another log is complete", r1["complete"] and r1["usable"])
    check("S4 the lane's last log without an end is CENSORED", not r2["complete"] and not r2["usable"])
    check("S5 a Champion scores 13/13", c["champion"] and c["score"] == 1.0, c["score"])
    check("S6 the Norman message is named as his wall", r1["wall"] == "boss wall: Norman", r1["wall"])
    check("S7 genome read from the lane's arm", r1["genome"] == K.STEP14_A and c["genome"] == K.STEP14_B)
    nb = r1["boss_log"].get("NORMAN", {})
    check("S8 the party at a boss's FIRST loss is the heartbeat before it, not a later one",
          nb.get("losses") == 2 and not nb.get("won") and "L20'" in (nb.get("party_first_loss") or ""), nb)
    check("S9 milestones are the first wins, in order", [m[0] for m in c["milestones"]][:3] ==
          ["ROXANNE", "BRAWLY", "WATTSON"] and c["milestones"][-1][0] == "WALLACE", c["milestones"][:3])
    check("S10 money after the last battle is read", r1["money_last"] == 2, r1["money_last"])


def test_brain() -> None:
    g = dict(K.STEP14_A)
    check("B1 genome id is stable and order-free", brain.genome_id(g) == brain.genome_id(dict(reversed(g.items()))))
    check("B2 baseline and arm B have different ids", brain.genome_id(K.STEP14_A) != brain.genome_id(K.STEP14_B))
    rng = random.Random(1)
    m = brain.mutate(g, rng, 2)
    changed = [k for k in K.GENES if m[k] != g[k]]
    check("B3 a 2-flip mutant changes exactly 2 knobs to allowed values",
          len(changed) == 2 and not K.validate_genes(m), changed)
    recs = [{"genome": K.STEP14_A, "usable": True, "score": 0.9, "champion": False, "starter": "Mudkip"}] * 6 + \
           [{"genome": K.STEP14_B, "usable": True, "score": 0.5, "champion": False, "starter": "Mudkip"}] * 6
    prop = {"name": "p", "why": "t", "genes": {"POKEBOT_R25_CAP": "1"}}
    picks = brain.choose_arms(4, brain.summarize(recs), [prop], random.Random(2))
    ids = [brain.genome_id(p) for p, _ in picks]
    check("B4 k distinct genomes", len(ids) == 4 and len(set(ids)) == 4, ids)
    check("B5 the best-measured genome is the incumbent", ids[0] == brain.genome_id(K.STEP14_A), picks[0][1])
    check("B6 an inbox proposal runs", brain.genome_id(prop["genes"]) in ids)
    check("B7 FAULT: an unknown knob is refused", K.validate_genes({"POKEBOT_FAKE": "1"}) != [])
    check("B8 FAULT: a disallowed value is refused", K.validate_genes({"POKEBOT_R25_CAP": "2"}) != [])
    def balanced(rs: list[dict]) -> bool:
        cols = list(zip(*[[r[g] != brain.BASE[g] for g in sorted(K.GENES)] for r in rs]))
        return all(sum(c) == 6 for c in cols) and all(
            sum(a and b for a, b in zip(cols[i], cols[j])) == 3 for i in range(len(cols)) for j in range(i + 1, len(cols)))

    rows = brain.pb12_rows()
    check("B9 the screening design: 12 distinct rows, each knob ON in 6, every pair ON together in 3",
          len({brain.genome_id(r) for r in rows}) == 12 and balanced(rows))
    design = {"rows": rows, "next": 0}
    picks = brain.choose_arms(6, brain.summarize(recs), [], random.Random(5), design=design)
    check("B10 a design cycle = the incumbent + the next design rows, and the row pointer advances",
          brain.genome_id(picks[0][0]) == brain.genome_id(K.STEP14_A) and design["next"] == 5
          and all("screening design row" in w for _, w in picks[1:]), [w for _, w in picks])
    bad = [dict(r) for r in rows]
    bad[0]["POKEBOT_R25_CAP"] = "1" if bad[0]["POKEBOT_R25_CAP"] == "0" else "0"
    check("B11 FAULT: one flipped cell makes the balance check fail", not balanced(bad))


def test_effects() -> None:
    rng = random.Random(3)
    recs = []
    for _ in range(400):
        genes = {k: rng.choice(v[0]) for k, v in K.GENES.items()}
        score = 0.4 + (0.2 if genes["POKEBOT_R25_CAP"] == "1" else 0) + rng.gauss(0, 0.05)
        recs.append({"genome": genes, "usable": True, "score": score, "starter": rng.choice(["Mudkip", "Torchic"])})
    eff = {e["gene"]: e for e in brain.gene_effects(recs)}
    cap = eff["POKEBOT_R25_CAP"]
    check("E1 a planted +0.20 effect is recovered", abs(cap["effect"] - 0.2) < 0.03 and cap["separable"], cap)
    check("E2 a knob with no effect reads near zero", abs(eff["POKEBOT_R27_KEYITEMS"]["effect"]) < 0.03)
    together = [{"genome": K.STEP14_A if i % 2 else K.STEP14_B, "usable": True, "score": 0.5, "starter": "Mudkip"}
                for i in range(40)]
    eff2 = brain.gene_effects(together)
    check("E3 FAULT: knobs that always moved together are flagged NOT separable",
          eff2 and not any(e["separable"] for e in eff2))


def test_preflight(tmp: Path) -> None:
    """The arms file the learner writes must pass the story bot's OWN batch-runner checks."""
    sys.path.insert(0, str(learner.STORY_DEV))
    import x4_headless as x4
    root = x4.REPO_ROOT / x4.BUILD_ROOTS["sandbox"]  # BUILD_ROOTS holds folder NAMES, relative to the repo
    rng = random.Random(4)
    picks = brain.choose_arms(6, {}, [], rng)
    spec = {"comment": "t", "arms": {chr(65 + i): brain.full_env(g) for i, (g, _) in enumerate(picks)}}
    p = tmp / "arms.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    errs, _, _ = x4.arms_preflight(p, "aitest9999", 24, "sandbox", root, learner.PROFILES)
    check("P1 a 6-arm, 24-lane arms file passes x4_headless's preflight", errs == [], errs[:3])
    errs, _, _ = x4.arms_preflight(p, "aitest9999", 16, "sandbox", root, learner.PROFILES)
    check("P2 FAULT: 6 arms on 16 lanes is refused", errs != [])
    bad = json.loads(json.dumps(spec))
    bad["arms"]["A"]["POKEBOT_R25_CAPP"] = bad["arms"]["A"].pop("POKEBOT_R25_CAP")
    p.write_text(json.dumps(bad), encoding="utf-8")
    errs, _, _ = x4.arms_preflight(p, "aitest9999", 24, "sandbox", root, learner.PROFILES)
    check("P3 FAULT: a misspelt knob is refused", any("CAPP" in e for e in errs), errs[:3])
    src = x4.build_source_text(root)
    missing = [k for k in K.ALL_KEYS if k not in src]
    check("P4 every knob exists in the sandbox source", bool(src) and not missing, missing)


def test_prune_and_inbox(tmp: Path) -> None:
    runs, profiles, inbox = tmp / "runs", tmp / "profiles", tmp / "inbox"
    learner.RUNS, learner.PROFILES, learner.INBOX = runs, profiles, inbox
    learner.DATA, learner.STATE_FILE, learner.LOG = tmp / "data", tmp / "data" / "s.json", tmp / "data" / "l.log"
    ours = [runs / "ai0001" / "batch", profiles / "endless-ai0001-H1-torchic"]
    foreign = [profiles / "endless-s14-H1-torchic", tmp / "elsewhere"]
    for d in ours + foreign:
        d.mkdir(parents=True)
    state = {"cycles": [{"tag": "ai0001", "created": [str(x) for x in ours + foreign]},
                        {"tag": "ai0002", "created": []}]}
    learner.prune({"keep_raw_cycles": 1}, state)
    check("R1 prune deletes the old cycle's own batch and profiles", not any(d.exists() for d in ours))
    check("R2 FAULT: prune never deletes a path it did not create by name", all(d.exists() for d in foreign))
    inbox.mkdir()
    (inbox / "good.json").write_text(json.dumps({"name": "g", "genes": {"POKEBOT_R25_CAP": "1"}}), encoding="utf-8")
    (inbox / "bad.json").write_text(json.dumps({"name": "b", "genes": {"POKEBOT_NOPE": "1"}}), encoding="utf-8")
    got = learner.read_inbox()
    check("I1 a valid proposal is read", [p["name"] for p in got] == ["g"])
    check("I2 FAULT: an invalid proposal is moved to rejected/", (inbox / "rejected" / "bad.json").exists())
    check("C1 consult is off by default", consult.maybe_consult(learner.DEFAULTS, tmp, tmp, "x") == "consult: off")
    cmd = consult.build_command("claude", learner.DEFAULTS["consult"])
    joined = " ".join(cmd)
    check("C2 consult skips project hooks (no git pull), is read-only, capped and on a cheap model",
          "--setting-sources user" in joined and "--allowedTools Read,Grep,Glob" in joined
          and "--max-budget-usd" in cmd and "--model sonnet" in joined and "--max-turns" not in cmd, joined[-160:])


def test_adopt_and_reparse(tmp: Path) -> None:
    """A learner that dies mid-cycle must not lose the cycle: the next one waits for the batch, then scores it."""
    learner.RUNS, learner.PROFILES, learner.INBOX = tmp / "runs", tmp / "profiles", tmp / "inbox"
    learner.DATA, learner.FINDINGS = tmp / "data", tmp / "findings"
    learner.STATE_FILE, learner.LOG = tmp / "data" / "state.json", tmp / "data" / "learner.log"
    learner.RUNS_FILE, learner.CYCLES_FILE = tmp / "data" / "runs.jsonl", tmp / "data" / "cycles.jsonl"
    cdir = learner.RUNS / "ai0007"
    make_batch(cdir)  # creates cdir/batch
    plan = {"tag": "ai0007", "lanes": 8, "arms": {"A": {"genome": "x"}}, "proposal_files": []}
    (cdir / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    learner.save_state({"cycle": 7, "cycles": [], "current": {"tag": "ai0007"}, "failures": 0})
    polls = []
    real_running, real_sleep = learner.batch_running, learner.sleep_unless_stopped
    learner.batch_running = lambda d: len(polls) < 2  # "still running" for two polls, then finished
    learner.sleep_unless_stopped = lambda m: polls.append(m) or True
    try:
        out = learner.adopt_unfinished(dict(learner.DEFAULTS))
    finally:
        learner.batch_running, learner.sleep_unless_stopped = real_running, real_sleep
    st = learner.load_state()
    recs = learner.load_jsonl(learner.RUNS_FILE)
    check("L1 adoption waits while the orphaned batch still runs", len(polls) == 2, polls)
    check("L2 then scores it and clears the current cycle",
          out is True and st["current"] is None and len(recs) == 3 and st["cycles"][-1]["exit"] == "adopted",
          (out, st["current"], len(recs)))
    check("L3 FAULT: nothing to adopt returns None", learner.adopt_unfinished(dict(learner.DEFAULTS)) is None)
    a = tmp / "sig"
    a.mkdir()
    (a / "m.py").write_text("x = 1", encoding="utf-8")
    s1 = learner.code_signature(a)
    (a / "m.py").write_text("x = 2", encoding="utf-8")
    check("L4 an edited code file changes the code signature (hot reload trigger)", s1 != learner.code_signature(a))
    cmds = learner.update_commands()
    flat = [" ".join(c[3:]) for c in cmds]
    check("L5 the learner's only git is fetch + fast-forward-only merge (nothing that can discard work)",
          flat == ["fetch --quiet origin", "merge --ff-only --quiet origin/main"], flat)
    real_dep = learner.DEPLOYMENT
    learner.DEPLOYMENT = tmp / "no-such-marker"
    try:
        refused = learner.loop(single=True)
    finally:
        learner.DEPLOYMENT = real_dep
    check("L6 FAULT: run/once refuse outside the deployment clone", refused == 2 and not (tmp / "data" / "agent.lock")
          .exists(), refused)
    stale = dict(recs[0], boss_log={}, batch="OLD-PRUNED")
    learner.write_jsonl(learner.RUNS_FILE, recs + [stale])
    learner.cmd_reparse()
    after = learner.load_jsonl(learner.RUNS_FILE)
    check("R3 reparse re-reads batches that still exist and keeps records of pruned ones",
          len(after) == 4 and sum(r["batch"] == "OLD-PRUNED" for r in after) == 1, len(after))


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="aiagent-test-"))
    try:
        for t in (lambda: test_scoring(tmp / "s"), test_brain, test_effects, lambda: test_preflight(tmp),
                  lambda: test_prune_and_inbox(tmp / "p"), lambda: test_adopt_and_reparse(tmp / "a")):
            try:
                t()
            except Exception as exc:  # a crash is a failed check, not a silent pass
                check(f"crash in {getattr(t, '__name__', 'test')}", False, repr(exc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))
    failed = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"{'ALL PASS' if not failed else f'{failed} FAILED'} ({len(RESULTS)} checks)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
