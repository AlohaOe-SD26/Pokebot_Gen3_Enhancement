"""Offline gate for the learner: `py -3.12 test_agent.py` (no emulator, about 10 seconds). Exit 0 = all pass.

Each check names what it protects. The FAULT rows prove a guard actually bites: a check that passes on broken
input is decoration.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
import random
import shutil
import stat
import subprocess
import sys
import tempfile
import time
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


#: EVERY helper child this suite starts runs this prelude and loops only while `alive()` (re-verify 2026-10-21, F7):
#: it ends at its deadline (argv[2] seconds, never more than CHILD_DEADLINE_S) AND as soon as the suite process whose
#: pid is argv[1] is gone. Why: the restart gate `tests_pass()` hard-kills this suite on its 600 s timeout
#: (TerminateProcess on the suite only), and an unbounded `while True` writer then outlived it, appending into %TEMP%
#: for ever (measured). A child's own arguments are ARGS (argv[3:]).
CHILD_DEADLINE_S = 60.0
CHILD_PRELUDE = ("import os, sys, time\nfrom pathlib import Path\nimport psutil\n"
                 "PARENT, END, ARGS = int(sys.argv[1]), time.time() + float(sys.argv[2]), sys.argv[3:]\n"
                 "def alive():\n"
                 "    return time.time() < END and psutil.pid_exists(PARENT)\n")
#: A child that only exists (holds a lock, poses as a lane or a batch runner) until its bound.
SLEEP_BODY = "while alive():\n    time.sleep(0.05)\n"


def child(body: str, *args: object, deadline: float = CHILD_DEADLINE_S, parent: int | None = None,
          **popen) -> subprocess.Popen:
    """Start a BOUNDED helper child: CHILD_PRELUDE + `body`, its parent pid (this process unless a test says otherwise)
    and deadline in argv[1:3], then `args`. A test name in `args` (e.g. 'learner.py archive') is what the learner's
    process scans see in its command line."""
    return subprocess.Popen([sys.executable, "-c", CHILD_PRELUDE + body, str(os.getpid() if parent is None else parent),
                             str(min(deadline, CHILD_DEADLINE_S)), *map(str, args)], **popen)


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
    cat = "f{f} [CATCH] end kind=team sp={s}#{n} end=caught res={r} thrown=2 frames=10 dest=party"
    run3 = ["f1 [MAP] LITTLEROOT TOWN(0,9) -> ROUTE 101(0,16) pos=(1, 1)",  # before the run starts: ignored
            "f13000 [STEP] 'Story: choosing Mudkip!'",
            "f13100 [MAP] LITTLEROOT TOWN(0,9) -> ROUTE 101(0,16) pos=(1, 1)",
            "f13200 [MAP] ROUTE 101(0,16) -> OLDALE TOWN(0,1) pos=(1, 1)",
            "f13300 [MAP] OLDALE TOWN(0,1) -> ROUTE 101(0,16) pos=(1, 1)",
            cat.format(f=13400, s="Wurmple", n=265, r="Caught"), cat.format(f=13500, s="Poochyena", n=261, r="Fled"),
            cat.format(f=13600, s="Zigzagoon", n=263, r="Caught"), cat.format(f=13700, s="Wurmple", n=265, r="Caught"),
            "f13710 [DEX] owned 1 -> 2: +#265", "f13720 [DEX] owned 2 -> 3: +#263",
            "f13730 [DEXFENCE] skip #278 Wingull — party is not at full strength",
            "f13740 [DEXFENCE] skip #122 Mr. Mime — party is not at full strength",
            "f13750 [DEXFENCE] skip #41 Zubat — a training grind is in progress",
            "f900 [STORY] DERAIL #5: Could not reach (1, 1)"]
    (b / "L01" / "debug-logs" / "a-1.log").write_text("\n".join(run1), encoding="utf-8")
    (b / "L01" / "debug-logs" / "a-2.log").write_text("\n".join(run2), encoding="utf-8")
    # named to sort FIRST, so a-2.log stays the lane's last (censored) log
    (b / "L01" / "debug-logs" / "a-0.log").write_text("\n".join(run3), encoding="utf-8")
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
    r3 = recs["a-0.log"]
    check("S11 human-like signals: successful catches by species, distinct places entered (failed catch ignored)",
          r3["species_caught"] == ["Wurmple", "Zigzagoon"] and r3["catches"] == 3 and r3["maps_visited"] == 2,
          (r3["species_caught"], r3["catches"], r3["maps_visited"]))
    check("S13 Pokedex owned and the reasons new species were skipped (a species name with a space included)",
          r3["dex_owned"] == 3 and r3["catch_skips"] == {"party is not at full strength": 2,
                                                         "a training grind is in progress": 1},
          (r3["dex_owned"], r3["catch_skips"]))
    check("S14 the balanced human score = half progress/13 + half Pokedex/202",
          r3["human_score"] == round(0.5 * 0 / 13 + 0.5 * 3 / 202, 4) and c["human_score"] == round(0.5, 4),
          (r3["human_score"], c["human_score"]))
    import report
    text, _ = report.build(list(recs.values()), [], "test")
    check("S12 the report states the human-like goal and shows the play columns",
          "HUMAN-LIKE PLAY" in text and "species caught / run" in text and "Human-like check" in text)


def test_brain() -> None:
    g = dict(K.STEP14_A)
    check("B1 genome id is stable and order-free", brain.genome_id(g) == brain.genome_id(dict(reversed(g.items()))))
    check("B2 baseline and arm B have different ids", brain.genome_id(K.STEP14_A) != brain.genome_id(K.STEP14_B))
    partial = {k: v for k, v in K.STEP14_B.items() if k != "POKEBOT_BOSSMODE_TOPUP"}
    check("B2b adding a knob at its default never renames a genome (ids hash only the changed knobs)",
          brain.genome_id(partial) == brain.genome_id(K.STEP14_B))
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
    catcher = dict(K.STEP14_A, POKEBOT_R25_CAP="1")
    mix = [{"genome": K.STEP14_A, "usable": True, "score": 0.7, "human_score": 0.40, "champion": False,
            "starter": "Mudkip"}] * 6 + \
          [{"genome": catcher, "usable": True, "score": 0.6, "human_score": 0.50, "champion": False,
            "starter": "Mudkip"}] * 6
    best = {k: max(brain.summarize(mix, k).values(), key=lambda s: s["mean"])["label"] for k in ("score", "human_score")}
    check("B12 the objective decides the ranking: progress prefers the faster genome, the human score the catcher",
          best["score"].startswith("baseline") and best["human_score"] == "R25_CAP", best)
    check("B13 the learner ranks by the balanced human score by default (USER RULINGS 32/33)",
          learner.score_key(learner.DEFAULTS) == "human_score" and learner.score_key({"objective": "progress"}) == "score")
    check("B7 FAULT: an unknown knob is refused", K.validate_genes({"POKEBOT_FAKE": "1"}) != [])
    check("B8 FAULT: a disallowed value is refused", K.validate_genes({"POKEBOT_R25_CAP": "2"}) != [])
    def balanced(rs: list[dict]) -> bool:
        n = len(rs)
        cols = list(zip(*[[r[g] != brain.BASE[g] for g in sorted(K.GENES)] for r in rs]))
        return all(sum(c) == n // 2 for c in cols) and all(
            sum(a and b for a, b in zip(cols[i], cols[j])) == n // 4
            for i in range(len(cols)) for j in range(i + 1, len(cols)))

    name, rows = brain.screen_rows()
    check(f"B9 the screening design ({name}, {len(K.GENES)} knobs): distinct rows, each knob ON in half, every pair "
          f"ON together in a quarter", rows and len({brain.genome_id(r) for r in rows}) == len(rows) and balanced(rows),
          (name, len(rows)))
    check("B9b the design matches the knob count (PB12 for 11, H16 for 12-15)",
          (name, len(rows)) == (("pb12", 12) if len(K.GENES) == 11 else ("h16", 16)), (name, len(rows)))
    design = {"rows": rows, "next": 0}
    picks = brain.choose_arms(6, brain.summarize(recs), [], random.Random(5), design=design)
    check("B10 a design cycle = the incumbent + the next design rows, and the row pointer advances",
          brain.genome_id(picks[0][0]) == brain.genome_id(K.STEP14_A) and 5 <= design["next"] <= 6
          and all("screening design row" in w for _, w in picks[1:]) and len(picks) == 6, [w for _, w in picks])
    bad = [dict(r) for r in rows]
    bad[1]["POKEBOT_R25_CAP"] = "1" if bad[1]["POKEBOT_R25_CAP"] == "0" else "0"
    check("B11 FAULT: one flipped cell makes the balance check fail", not balanced(bad))
    sys.path.insert(0, str(learner.REPO / "sandbox-pokebot"))
    from modules.story import bossmode_topup as bt
    check("K1 the boss-mode knob defaults to the old +1 when unset", bt.topup_levels({}) == 1)
    check("K2 the learner's values reach the bot as integers", [bt.topup_levels({bt.ENV: v}) for v in
                                                                K.GENES[bt.ENV][0]] == [1, 4])
    check("K3 FAULT: junk or out-of-range values fall back to 1, never a huge grind",
          [bt.topup_levels({bt.ENV: v}) for v in ("", "x", "0", "11", "-3", "4.5")] == [1] * 6)


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


#: Every path the learner WRITES, re-pointed into a test's temp dir. This suite runs INSIDE the live learner's clone
#: as its restart gate, so a test that reached the real `runs/` or `data/` would archive or delete live raw logs.
LEARNER_PATHS = {"RUNS": "runs", "PROFILES": "profiles", "DATA": "data", "FINDINGS": "findings", "INBOX": "inbox",
                 "PUBLISHED": "published", "RUNS_FILE": "data/runs.jsonl", "CYCLES_FILE": "data/cycles.jsonl",
                 "STATE_FILE": "data/state.json", "LOCK": "data/agent.lock", "LOG": "data/learner.log",
                 "OPS_FILE": "data/ops.jsonl",
                 "STOP": "STOP", "ATTENTION": "findings/ATTENTION.md", "DEPLOYMENT": "DEPLOYMENT"}
#: The only learner Path globals allowed to stay real: the code folders it READS (code, config.json, the bot).
CODE_ROOTS = {"AI", "REPO", "STORY_DEV"}
#: ISOLATION ON BY DEFAULT (O3 review finding 3): `main()` points every learner path here BEFORE the first test, so a
#: test that forgets to patch acts on temp files, never on the live clone; sandboxes restore to it, never to the real
#: paths. None only when this module is imported by a helper process (the R5b wrapper patches its own root).
GLOBAL_ROOT: Path | None = None


def assert_isolated(root: Path) -> None:
    """Raise unless EVERY Path global of the learner module (so also one added later) lies under `root`, `root` lies
    under the system temp dir, and no write path lies inside the learner's own code folder. Called after patching and,
    by `main()`, before EVERY test."""
    root = Path(root).resolve()
    if not root.is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise AssertionError(f"test root {root} is not under the temp dir")
    code = Path(learner.AI).resolve()
    for name, value in vars(learner).items():
        if isinstance(value, Path) and name not in CODE_ROOTS and (
                not value.resolve().is_relative_to(root) or value.resolve().is_relative_to(code)):
            raise AssertionError(f"learner.{name} = {value} is outside the test dir {root}")


def patch_learner_paths(root: Path) -> dict:
    """Point every learner write path into `root`, assert it, and return the old values for `restore_paths`."""
    root = Path(root).resolve()
    saved = {name: getattr(learner, name) for name in LEARNER_PATHS}
    for name, rel in LEARNER_PATHS.items():
        setattr(learner, name, root / rel)
    assert_isolated(root)
    return saved


def restore_paths(saved: dict) -> None:
    """Undo a `patch_learner_paths`. While the suite runs this goes back to GLOBAL_ROOT, NEVER to the real paths."""
    if GLOBAL_ROOT is not None:
        patch_learner_paths(GLOBAL_ROOT)
        return
    for name, value in saved.items():
        setattr(learner, name, value)


def test_prune_and_inbox(tmp: Path) -> None:
    runs, profiles, inbox = tmp / "runs", tmp / "profiles", tmp / "inbox"
    patch_learner_paths(tmp)
    learner.free_gb = lambda: 500.0  # prune reads free disk now (O3); a fixed value keeps R1/R2 deterministic
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
    # The backlog cap (2026-10-17): a full queue must skip BEFORE Claude is reached; under the cap it goes ahead.
    box = tmp / "consult_queue"
    (box / "inbox").mkdir(parents=True)
    (box / "data").mkdir()
    for name in ("a", "b"):
        (box / "inbox" / f"{name}.json").write_text("{}", encoding="utf-8")
    cfg = {"consult": {"enabled": True, "max_calls_per_day": 99, "max_waiting_proposals": 2}}
    real_which = consult.shutil.which

    def claude_reached(name: str) -> str:
        raise AssertionError("the consult reached for claude")

    consult.shutil.which = claude_reached
    try:
        try:
            out = consult.maybe_consult(cfg, tmp, box, "x")
        except AssertionError as error:
            out = f"CALLED: {error}"
    finally:
        consult.shutil.which = real_which
    check("C3 a full queue skips the consult without reaching Claude",
          out.startswith("consult: skipped, 2 proposal(s) already waiting (cap 2)"), out)
    (box / "inbox" / "b.json").unlink()
    consult.shutil.which = lambda name: None
    try:
        out = consult.maybe_consult(cfg, tmp, box, "x")
    finally:
        consult.shutil.which = real_which
    # Since O5 the line also says why the novelty gate let it through (here: no latest.json, so it failed open).
    check("C4 FAULT CONTROL: under the cap the consult goes ahead (here it stops at 'no claude on PATH')",
          out.startswith("consult: the `claude` command is not on PATH"), out)


def test_adopt_and_reparse(tmp: Path) -> None:
    """A learner that dies mid-cycle must not lose the cycle: the next one waits for the batch, then scores it."""
    patch_learner_paths(tmp)
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
          out is True and st["current"] is None and len(recs) == 4 and st["cycles"][-1]["exit"] == "adopted",
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
          len(after) == 5 and sum(r["batch"] == "OLD-PRUNED" for r in after) == 1, len(after))


# ------------------------------------------------------------------------------------- O3: archive, never just delete
BIG_LOG = b"f123456 [hb] mode=Story state=7 controllable=True map=ROUTE 104(0,19) pos=(5, 6) party=['Mudkip:L9']\n"


def make_raw_cycle(root: Path, tag: str) -> dict:
    """A finished cycle the learner created: `runs/<tag>/batch` (ARMS.json + 3 logs, one 5 MB and repetitive) and a
    lane profile shaped like a real one (measured on the clone 2026-10-21): a save, a badge-log.json found nowhere else,
    and a debug log BYTE-IDENTICAL to the batch's copy of it (so every archive test also exercises `dup_of`). Returns
    its state entry, recorded exactly as `finish_cycle` records it."""
    batch = learner.RUNS / tag / "batch"
    (batch / "L01" / "debug-logs").mkdir(parents=True)
    (batch / "L02" / "debug-logs").mkdir(parents=True)
    (batch / "ARMS.json").write_text(json.dumps({"stamp": tag, "lanes": []}), encoding="utf-8")
    (batch / "L01" / "debug-logs" / "a-1.log").write_text(f"{tag} first run\n" * 50, encoding="utf-8")
    big = BIG_LOG * (5 * 2 ** 20 // len(BIG_LOG))
    (batch / "L01" / "debug-logs" / "big.log").write_bytes(big)
    (batch / "L02" / "stdout.txt").write_bytes(bytes(range(256)) * 40)
    prof = learner.PROFILES / f"endless-{tag}-H1-torchic"
    (prof / "debug-logs").mkdir(parents=True)
    (prof / "save.ss1").write_bytes(b"\x01" * 1000)
    (prof / "badge-log.json").write_text(json.dumps({"tag": tag, "badges": ["ROXANNE"], "team": ["Combusken:L20"]}),
                                         encoding="utf-8")
    (prof / "debug-logs" / "big.log").write_bytes(big)
    return {"tag": tag, "created": [str(batch), str(prof)], "pruned": False}


def tree(root: Path) -> dict[str, str]:
    """relative path -> sha256 of every file under `root` (missing root = empty)."""
    import hashlib
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()} if root.exists() else {}


def zip_tree(zpath: Path) -> dict[str, str]:
    import hashlib
    import zipfile
    with zipfile.ZipFile(zpath) as zf:
        return {n: hashlib.sha256(zf.read(n)).hexdigest() for n in zf.namelist()}


def raw_view(root: Path, tag: str) -> dict[str, str]:
    """What the cycle's originals look like (path -> sha256), keyed as the archive names them: `batch/<rel>` and, for
    every `endless-<tag>-*` lane profile on disk, `profiles/<profile>/<rel>`."""
    out = {k[len(tag) + 1:]: v for k, v in tree(learner.RUNS).items() if k.startswith(f"{tag}/batch/")}
    out.update({"profiles/" + k: v for k, v in tree(learner.PROFILES).items() if k.startswith(f"endless-{tag}-")})
    return out


def manifest_for(zpath: Path) -> Path:
    """The manifest that belongs to an archive: raw.zip -> raw.manifest.json, raw.zip.bad.<k> -> .json.bad.<k>."""
    return zpath.with_name(zpath.name.replace("raw.zip", "raw.manifest.json", 1))


def restored(cdir: Path, zname: str = "raw.zip") -> dict[str, str]:
    """name -> sha256 of every original as the archive gives it BACK, read independently of the learner: a stored
    member from the zip's own bytes, a `dup_of` member (its manifest says which) from its target's bytes. A target
    absent from the zip reads as 'MISSING'. No manifest: the stored members only."""
    import hashlib
    import zipfile
    zpath, mpath = cdir / zname, manifest_for(cdir / zname)
    members = json.loads(mpath.read_text(encoding="utf-8"))["members"] if mpath.exists() else []
    with zipfile.ZipFile(zpath) as zf:
        names = set(zf.namelist())
        out = {n: hashlib.sha256(zf.read(n)).hexdigest() for n in sorted(names)}
        for m in members:
            if m.get("dup_of"):
                out[m["name"]] = hashlib.sha256(zf.read(m["dup_of"])).hexdigest() if m["dup_of"] in names \
                    else "MISSING"
    return out


def flip_member_byte(zpath: Path, name: str) -> None:
    """Flip one byte INSIDE the compressed data of `name` (deterministic: the zip's own local header gives where)."""
    import struct
    import zipfile
    with zipfile.ZipFile(zpath) as zf:
        info = zf.getinfo(name)
    data = bytearray(zpath.read_bytes())
    n, m = struct.unpack("<HH", data[info.header_offset + 26:info.header_offset + 30])
    at = info.header_offset + 30 + n + m + info.compress_size // 2
    data[at] ^= 0xFF
    zpath.write_bytes(bytes(data))


#: Every learner attribute an O3 test may patch; O3Sandbox restores them all on exit.
SANDBOX_ATTRS = ("free_gb", "REPLACE_WAIT_S", "REPLACE_TRIES", "_copy_member", "verify_archive", "_os_replace",
                 "_os_rename", "_delete_ours", "load_config", "archive_cycle", "_write_manifest", "QUIET_MINUTES",
                 "_cmdlines", "LOCK_POLL_S", "LOCK_WAIT_MAX_MIN", "disk_guard", "sleep_unless_stopped", "run_cycle",
                 "acquire_lock", "_lock_holder",
                 # O6 + O7 (test_o6_o7)
                 "prune", "batch_command", "now", "CPU_SAMPLE_S", "SIZE_WALK_CAP_S", "_ops_row", "_CpuSampler",
                 "append_jsonl", "write_ops_row",
                 # the O6/O7 review fixes: the pinned and stepping clocks, the walk's check interval, a raising O7
                 "time", "SIZE_WALK_CHECK_EVERY", "early_archive")
#: The real learner attributes, captured at import, before any test patches one.
O3_REAL = {k: getattr(learner, k) for k in SANDBOX_ATTRS}


def delete_half(c: dict) -> None:
    """A delete that stops part-way, on any OS: it removes ARMS.json and big.log (raw.zip is then their ONLY copy) and
    keeps a-1.log, stdout.txt and the lane profile."""
    b = learner.RUNS / c["tag"] / "batch"
    for rel in ("ARMS.json", "L01/debug-logs/big.log"):
        (b / rel).unlink()


class O3Sandbox:
    """A temp learner tree: every learner write path inside it (asserted), free disk and the rename wait fixed, the
    cycle counted QUIET at once (QUIET_MINUTES = 0) and no process seen as using it (a process scan costs 0.5 s; the
    quiescence test R15 restores the real scan). Restores everything it patched on exit, whatever happened."""

    def __init__(self, root: Path, free: float = 500.0):
        self.root, self.free = Path(root).resolve(), free

    def __enter__(self) -> "O3Sandbox":
        self.root.mkdir(parents=True, exist_ok=True)
        self.saved = patch_learner_paths(self.root)
        self.saved_fns = {k: getattr(learner, k) for k in SANDBOX_ATTRS}
        learner.free_gb = lambda: self.free
        learner.REPLACE_WAIT_S = 0.01
        learner.QUIET_MINUTES = 0
        learner._cmdlines = lambda: iter(())
        return self

    def __exit__(self, *exc) -> None:
        for k, v in self.saved_fns.items():
            setattr(learner, k, v)
        restore_paths(self.saved)

    @staticmethod
    def state(cycles: list[dict]) -> dict:
        st = {"cycle": len(cycles), "cycles": cycles, "current": None, "failures": 0}
        learner.save_state(st)
        return st


def test_o3_archive(tmp: Path) -> None:
    import zipfile
    keep1 = {"keep_raw_cycles": 1, "max_archives_per_prune": 3}

    # R4 round trip ------------------------------------------------------------------------------------------------
    with O3Sandbox(tmp / "r4"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        before1, before2 = raw_view(tmp, "ai0001"), raw_view(tmp, "ai0002")
        st = {"cycles": [c1, c2]}
        learner.prune(keep1, st)
        cdir = learner.RUNS / "ai0001"
        mpath = cdir / "raw.manifest.json"
        man = json.loads(mpath.read_text(encoding="utf-8")) if mpath.exists() else {}
        got = restored(cdir) if (cdir / "raw.zip").exists() else {}
        check("R4 prune archives an old cycle: every original's bytes (4 batch + 3 lane-profile files) read back from "
              "raw.zip equal the originals' sha256", len(before1) == 7 and got == before1, (len(before1), sorted(got)))
        check("R4 then its batch/ and lane profile are gone and it is flagged archived + pruned",
              not (cdir / "batch").exists() and not (learner.PROFILES / "endless-ai0001-H1-torchic").exists()
              and c1.get("archived") is True and c1.get("pruned") is True, c1)
        check("R4 the manifest lists the members, sizes and CRCs exactly",
              man.get("n_files") == 7 and learner.verify_archive(cdir / "raw.zip", man.get("members", [])) is None
              and man.get("bytes_raw") == sum(m["size"] for m in man.get("members", [])), man.get("n_files"))
        with zipfile.ZipFile(cdir / "raw.zip") as zf:
            names = zf.namelist()
            deflated = all(i.compress_type == zipfile.ZIP_DEFLATED for i in zf.infolist())
        check("R4 member names are relative to runs/<tag>/ and deflated", "batch/L01/debug-logs/big.log" in names
              and deflated, names)
        check("R4 CONTROL: the newest cycle (inside keep_raw_cycles) is untouched",
              raw_view(tmp, "ai0002") == before2 and not (learner.RUNS / "ai0002" / "raw.zip").exists()
              and not c2.get("pruned"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = learner.cmd_archive_check()
        rec = json.loads((learner.DATA / "archive_check.json").read_text(encoding="utf-8"))
        check("R12 archive-check: OK <tag> <members> <bytes>, exit 0, result saved with a timestamp",
              rc == 0 and out.getvalue().startswith("OK ai0001 7 ") and rec["bad"] == 0 and rec["checked"],
              (rc, out.getvalue()))
        zbefore = (cdir / "raw.zip").read_bytes()
        flip_member_byte(cdir / "raw.zip", "batch/L01/debug-logs/big.log")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = learner.cmd_archive_check()
        check("R12 FAULT: a flipped byte in a zip -> BAD <tag> <reason>, exit 1",
              rc == 1 and out.getvalue().startswith("BAD ai0001 "), (rc, out.getvalue()))
        (cdir / "raw.zip").write_bytes(zbefore)

    # R4b the per-boundary cap --------------------------------------------------------------------------------------
    with O3Sandbox(tmp / "r4b"):
        cs = [make_raw_cycle(tmp, f"ai00{i:02d}") for i in range(1, 7)]
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 3}, {"cycles": cs})
        done = [c["tag"] for c in cs if c.get("archived")]
        check("R4b max_archives_per_prune: 3 of 5 eligible archived this boundary, oldest first; the rest wait",
              done == ["ai0001", "ai0002", "ai0003"] and (learner.RUNS / "ai0004" / "batch").exists(), done)

    # R5 FAULT: the stream copy raises after the first member --------------------------------------------------------
    with O3Sandbox(tmp / "r5"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        before = raw_view(tmp, "ai0001")
        calls = []
        real_copy = learner._copy_member

        def copy_then_fail(zf, src, name):
            calls.append(name)
            if len(calls) > 1:
                raise OSError("simulated disk error mid-archive")
            return real_copy(zf, src, name)

        learner._copy_member = copy_then_fail
        try:
            learner.prune(keep1, {"cycles": [c1, c2]})
            escaped = None
        except Exception as exc:  # noqa: BLE001
            escaped = exc
        learner._copy_member = real_copy
        cdir = learner.RUNS / "ai0001"
        check("R5 FAULT: a copy error mid-archive -> prune returns normally (nothing raised into the loop)",
              escaped is None and len(calls) == 2, (escaped, calls))
        check("R5 FAULT: the originals are byte-identical, no raw.zip, no .part, not flagged pruned",
              raw_view(tmp, "ai0001") == before and not (cdir / "raw.zip").exists()
              and not (cdir / "raw.zip.part").exists() and not c1.get("pruned") and not c1.get("archived"), c1)
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R5 CONTROL: the next prune with no fault archives it",
              c1.get("archived") and restored(cdir) == before and not (cdir / "batch").exists())

    # R6 FAULT: verification sees a corrupt archive ------------------------------------------------------------------
    with O3Sandbox(tmp / "r6"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        before = raw_view(tmp, "ai0001")
        real_verify = learner.verify_archive

        def flip_then_verify(zpath, members):
            if Path(zpath).name.endswith(".part"):
                flip_member_byte(Path(zpath), "batch/L01/debug-logs/big.log")
            return real_verify(zpath, members)

        learner.verify_archive = flip_then_verify
        learner.prune(keep1, {"cycles": [c1, c2]})
        learner.verify_archive = real_verify
        cdir = learner.RUNS / "ai0001"
        check("R6 FAULT: an archive with one flipped byte is never trusted: originals kept, .part removed, no raw.zip",
              raw_view(tmp, "ai0001") == before and not (cdir / "raw.zip.part").exists()
              and not (cdir / "raw.zip").exists() and not c1.get("pruned"), sorted(p.name for p in cdir.iterdir()))
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R6 CONTROL: untouched verification -> archived and the originals deleted",
              c1.get("archived") and not (cdir / "batch").exists() and restored(cdir) == before)

    # R7 a crash between the rename and the delete ------------------------------------------------------------------
    with O3Sandbox(tmp / "r7"):
        c1, c3, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0003"), make_raw_cycle(tmp, "ai0002")
        before1, before3 = raw_view(tmp, "ai0001"), raw_view(tmp, "ai0003")
        real_delete = learner._delete_ours

        def crash(c):
            raise RuntimeError("simulated crash after the rename, before the delete")

        learner._delete_ours = crash
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, {"cycles": [c1, c3, c2]})
        learner._delete_ours = real_delete
        d1, d3 = learner.RUNS / "ai0001", learner.RUNS / "ai0003"
        setup_ok = all((d / "raw.zip").exists() and (d / "raw.manifest.json").exists() for d in (d1, d3)) and \
            raw_view(tmp, "ai0001") == before1 and not c1.get("pruned")
        # ai0003's raw.zip: a VALID zip with the same names and sizes, one byte of content changed
        bad_zip = d3 / "raw.zip"
        bad_zip.unlink()
        with zipfile.ZipFile(bad_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted((d3 / "batch").rglob("*")):
                if f.is_file():
                    data = bytearray(f.read_bytes())
                    if f.name == "big.log":
                        data[100] ^= 0x01
                    zf.writestr(f.relative_to(d3).as_posix(), bytes(data))
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, {"cycles": [c1, c3, c2]})
        check("R7 setup: a crash after the rename leaves raw.zip + manifest + the originals, not flagged", setup_ok)
        check("R7 raw.zip + originals -> re-verified against them, then the originals deleted",
              c1.get("archived") and not (d1 / "batch").exists() and restored(d1) == before1, c1)
        check("R7 FAULT: a CORRUPT raw.zip + manifest + all originals -> originals kept, zip AND manifest set aside "
              "as .bad.1", raw_view(tmp, "ai0003") == before3 and (d3 / "raw.zip.bad.1").exists()
              and (d3 / "raw.manifest.json.bad.1").exists() and not bad_zip.exists()
              and not (d3 / "raw.manifest.json").exists() and not c3.get("pruned") and not c3.get("held"),
              sorted(p.name for p in d3.iterdir()))
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, {"cycles": [c1, c3, c2]})
        check("R7 CONTROL: the next prune re-archives the kept originals correctly",
              c3.get("archived") and not (d3 / "batch").exists() and restored(d3) == before3)

    # R7b an original that changed after its archive was written: the archive no longer describes it --------------
    with O3Sandbox(tmp / "r7b"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        real_delete = learner._delete_ours
        learner._delete_ours = lambda c: (_ for _ in ()).throw(RuntimeError("simulated crash before the delete"))
        learner.prune(keep1, {"cycles": [c1, c2]})
        learner._delete_ours = real_delete
        d1 = learner.RUNS / "ai0001"
        with open(d1 / "batch" / "L01" / "debug-logs" / "a-1.log", "ab") as fh:
            fh.write(b"one more line written after the archive\n")
        changed = raw_view(tmp, "ai0001")
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R7b FAULT: an original that differs from the manifest (delete not started) -> originals kept, zip and "
              "manifest set aside", raw_view(tmp, "ai0001") == changed and (d1 / "raw.zip.bad.1").exists()
              and (d1 / "raw.manifest.json.bad.1").exists() and not c1.get("pruned"),
              sorted(p.name for p in d1.iterdir()))

    # R13 the delete stops part-way (a locked file): flags only once the originals are really gone ------------------
    with O3Sandbox(tmp / "r13"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        before = raw_view(tmp, "ai0001")
        d1 = learner.RUNS / "ai0001"
        stuck = d1 / "batch" / "L02" / "stdout.txt"
        real_delete = learner._delete_ours
        learner._delete_ours = delete_half  # OS-independent: the delete removes some originals, then stops
        try:
            learner.prune(keep1, {"cycles": [c1, c2]})
            escaped = None
        except Exception as exc:  # noqa: BLE001
            escaped = exc
        learner._delete_ours = real_delete
        partial = stuck.exists() and not (d1 / "batch" / "L01" / "debug-logs" / "big.log").exists()
        check("R13 FAULT: a delete that stops part-way -> NOT flagged archived/pruned, nothing escapes",
              escaped is None and partial and not c1.get("pruned") and not c1.get("archived")
              and (d1 / "raw.zip").exists(), (escaped, partial, c1))
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R13 CONTROL: the next prune re-verifies the zip against the manifest + the REMAINING originals",
              c1.get("archived") and not (d1 / "batch").exists() and restored(d1) == before, c1)

    # R8 the rename is locked (antivirus) ---------------------------------------------------------------------------
    with O3Sandbox(tmp / "r8"):
        c1, c3, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0003"), make_raw_cycle(tmp, "ai0002")
        before1, before3 = raw_view(tmp, "ai0001"), raw_view(tmp, "ai0003")
        real_rename, tries = learner._os_rename, []

        def locked_twice(src, dst):  # the .part -> raw.zip rename is locked twice, then free
            if Path(src).name.endswith(".part"):
                tries.append(src)
                if len(tries) <= 2:
                    raise PermissionError("simulated antivirus lock")
            return real_rename(src, dst)

        learner._os_rename = locked_twice
        learner.prune({"keep_raw_cycles": 2, "max_archives_per_prune": 9}, {"cycles": [c1, c3, c2]})
        check("R8 a rename locked twice then free -> retried and archived",
              len(tries) == 3 and c1.get("archived") and restored(learner.RUNS / "ai0001") == before1,
              (len(tries), c1))
        always = []

        def locked_forever(src, dst):
            always.append(src)
            raise PermissionError("simulated permanent lock")

        learner._os_rename = locked_forever
        try:
            learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, {"cycles": [c1, c3, c2]})
            escaped = None
        except Exception as exc:  # noqa: BLE001
            escaped = exc
        learner._os_rename = real_rename
        d3 = learner.RUNS / "ai0003"
        check("R8 FAULT: always locked -> 5 tries, originals intact, no raw.zip or .part, nothing escapes",
              escaped is None and len(always) == learner.REPLACE_TRIES and raw_view(tmp, "ai0003") == before3
              and not (d3 / "raw.zip").exists() and not (d3 / "raw.zip.part").exists() and not c3.get("pruned"),
              (escaped, len(always)))

    # R10 the emergency floor ----------------------------------------------------------------------------------------
    for arm, free, fail in (("FAULT", 1.0, True), ("FAULT working-archive", 1.0, False), ("CONTROL", 50.0, True)):
        with O3Sandbox(tmp / f"r10-{arm.replace(' ', '-')}", free=free):
            c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
            before = tree(learner.RUNS), tree(learner.PROFILES)
            view1 = raw_view(tmp, "ai0001")
            attempts = []
            real_archive = learner.archive_cycle
            real_copy = learner._copy_member

            def failing_copy(zf, src, name):
                raise OSError("simulated: the archive cannot be written")

            def counted(c, cmds=None):
                attempts.append(c["tag"])
                return real_archive(c, cmds)

            learner.archive_cycle = counted
            if fail:
                learner._copy_member = failing_copy
            st = {"cycle": 2, "cycles": [c1, c2], "current": None}
            cfg = dict(learner.DEFAULTS, min_free_gb=25, keep_raw_cycles=20)
            started = learner.disk_guard(cfg, st)
            after = tree(learner.RUNS), tree(learner.PROFILES)
            if arm.startswith("FAULT"):
                check(f"R10 {arm}: 1 GB free -> nothing archived or deleted, the batch NOT started, ATTENTION.md",
                      not started and after == before and attempts == [] and learner.ATTENTION.exists()
                      and "deleted NOTHING" in learner.ATTENTION.read_text(encoding="utf-8"), (started, attempts))
                learner.prune(keep1, st)
                check(f"R10 {arm}: and the boundary prune at 1 GB archives and deletes nothing either",
                      (tree(learner.RUNS), tree(learner.PROFILES)) == before and attempts == [], attempts)
            else:
                check("R10 CONTROL: 50 GB free, a failing archive -> nothing deleted, the batch starts, no ATTENTION",
                      started and after == before and not learner.ATTENTION.exists(), started)
                learner.prune(keep1, st)
                kept = raw_view(tmp, "ai0001") == view1 and len(view1) == 7
                learner._copy_member = real_copy
                learner.prune(keep1, st)
                check("R10 CONTROL: the failing archive deletes nothing, and the next boundary archives it",
                      kept and attempts == ["ai0001", "ai0001"] and c1.get("archived")
                      and not (learner.RUNS / "ai0001" / "batch").exists(), (kept, attempts))

    with O3Sandbox(tmp / "r10c", free=10.0):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        before1 = raw_view(tmp, "ai0001")
        started = learner.disk_guard(dict(learner.DEFAULTS, min_free_gb=25, keep_raw_cycles=20),
                                     {"cycles": [c1, c2]})
        check("R10c under min_free_gb but above the floor: archives (verified) all but the newest; still short -> stop",
              not started and c1.get("archived") and restored(learner.RUNS / "ai0001") == before1
              and not c2.get("pruned") and learner.ATTENTION.exists(), (started, c1))

    # R11 the manual `archive` command and the learner's lock --------------------------------------------------------
    with O3Sandbox(tmp / "r11"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        O3Sandbox.state([c1, c2])
        learner.load_config = lambda: dict(learner.DEFAULTS, keep_raw_cycles=1)
        holder = child(SLEEP_BODY, "learner.py")
        try:
            learner.DATA.mkdir(parents=True, exist_ok=True)
            learner.LOCK.write_text(str(holder.pid))
            before = tree(learner.RUNS), tree(learner.PROFILES)
            with contextlib.redirect_stdout(io.StringIO()):
                rc = learner.cmd_archive()
            check("R11 FAULT: a live learner holds the lock -> `archive` refuses and the tree is byte-identical",
                  rc == 2 and (tree(learner.RUNS), tree(learner.PROFILES)) == before
                  and learner.LOCK.read_text() == str(holder.pid), rc)
        finally:
            holder.kill()
            holder.wait()
        learner.LOCK.unlink()
        before1, before2 = raw_view(tmp, "ai0001"), raw_view(tmp, "ai0002")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = learner.cmd_archive()
        st = learner.load_state()
        check("R11 CONTROL: lock free -> `archive` archives, records it, and releases the lock",
              rc == 0 and restored(learner.RUNS / "ai0001") == before1
              and st["cycles"][0].get("archived") and not learner.LOCK.exists(), rc)
        check("R11 CONTROL: and the NEWEST cycle (inside keep_raw_cycles) is untouched",
              len(before2) == 7 and raw_view(tmp, "ai0002") == before2
              and not (learner.RUNS / "ai0002" / "raw.zip").exists() and not st["cycles"][1].get("pruned"))


def test_o3_kill(tmp: Path) -> None:
    """R5b: a REAL kill of a process mid-archive (the backlog's 'kill mid-gzip'). The slowing lives in a TEST-SIDE
    wrapper; the learner has no delay switch. The wrapper is BOUNDED like every helper child (F7): each slowed member
    first checks that the suite (argv[4]) is alive and CHILD_DEADLINE_S has not passed, else it exits at once."""
    with O3Sandbox(tmp):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        O3Sandbox.state([c1, c2])
        before = raw_view(tmp, "ai0001")
        wrapper = tmp / "r5b_wrapper.py"
        wrapper.write_text(
            "import os, sys, time\n"
            "from pathlib import Path\n"
            "import psutil\n"
            "root, ai, tag, parent = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])\n"
            "sys.path.insert(0, str(ai))\n"
            "import test_agent as T\n"
            "import learner\n"
            "end = time.time() + T.CHILD_DEADLINE_S\n"
            "T.patch_learner_paths(root)  # asserts every learner path is inside root BEFORE anything acts\n"
            "real = learner._copy_member\n"
            "def slow(zf, src, name):\n"
            "    if time.time() > end or not psutil.pid_exists(parent):\n"
            "        os._exit(3)\n"
            "    time.sleep(1.0)\n"
            "    return real(zf, src, name)\n"
            "learner._copy_member = slow\n"
            "learner.free_gb = lambda: 500.0\n"
            "learner.QUIET_MINUTES = 0  # the fresh test files count as quiet, as in O3Sandbox\n"
            "learner._cmdlines = lambda: iter(())\n"
            "c = next(c for c in learner.load_state()['cycles'] if c['tag'] == tag)\n"
            "learner.archive_cycle(c)\n", encoding="utf-8")
        part, cdir = learner.RUNS / "ai0001" / "raw.zip.part", learner.RUNS / "ai0001"
        proc = subprocess.Popen([sys.executable, str(wrapper), str(tmp), str(AI), "ai0001", str(os.getpid())],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        deadline = time.time() + 30
        while not part.exists() and proc.poll() is None and time.time() < deadline:
            time.sleep(0.02)
        time.sleep(0.3)  # inside the first slowed member
        alive = proc.poll() is None
        proc.kill()
        out = proc.communicate()[0].decode("utf-8", "replace")
        check("R5b setup: the wrapper was killed while raw.zip.part existed (mid-archive)",
              alive and part.exists() and not (cdir / "raw.zip").exists(), out[-300:])
        check("R5b FAULT: after the kill the originals are intact and nothing was flagged",
              raw_view(tmp, "ai0001") == before and not learner.load_state()["cycles"][0].get("pruned"))
        learner.prune({"keep_raw_cycles": 5, "max_archives_per_prune": 3}, learner.load_state())
        check("R5b the next prune removes the leftover .part even for a cycle it does not archive; raw intact",
              not part.exists() and raw_view(tmp, "ai0001") == before and not (cdir / "raw.zip").exists())
        part.write_bytes(b"PK\x03\x04 half a zip")  # a second interrupted attempt, left for the archiving prune
        st = learner.load_state()
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 3}, st)
        check("R5b CONTROL: the next prune completes the archive",
              st["cycles"][0].get("archived") and restored(cdir) == before and not part.exists()
              and not (cdir / "batch").exists(), st["cycles"][0])


def test_o3_reparse(tmp: Path) -> None:
    """R9 (fact 4): a batch whose ARMS.json exists but whose logs are gone must not erase its old run records."""
    with O3Sandbox(tmp):
        good = scoring.parse_batch(make_batch(tmp / "src"), "x")[0]
        empty = learner.RUNS / "ai0009" / "batch"
        (empty / "L01" / "debug-logs").mkdir(parents=True)
        (empty / "ARMS.json").write_text(json.dumps({"stamp": "T9", "arms_text": json.dumps({"arms": {}}),
                                                     "lanes": [{"arm": "A", "profile": "p"}]}), encoding="utf-8")
        full = learner.RUNS / "ai0010"
        make_batch(full)
        O3Sandbox.state([{"tag": "ai0009", "created": []}, {"tag": "ai0010", "created": []}])
        old = [dict(good, batch="T9", log="old-T9.log"), dict(good, batch="T", log="stale-T.log")]
        learner.write_jsonl(learner.RUNS_FILE, old)
        learner.cmd_reparse()
        after = learner.load_jsonl(learner.RUNS_FILE)
        check("R9 FAULT: ARMS.json with no logs -> that batch's old records are KEPT",
              [r["log"] for r in after if r["batch"] == "T9"] == ["old-T9.log"], [r["log"] for r in after])
        check("R9 CONTROL: a batch whose logs exist is re-read (its stale record replaced by the 4 fresh ones)",
              sorted(r["log"] for r in after if r["batch"] == "T") == ["a-0.log", "a-1.log", "a-2.log", "b-1.log"],
              sorted(r["log"] for r in after if r["batch"] == "T"))


# ------------------------------------------------- O3 review fixes (2026-10-21): recovery, HOLD, quiescence, liveness
def crash_before_delete(c: dict) -> None:
    raise RuntimeError("simulated crash after the archive, before the delete")


def all_tree() -> dict[str, str]:
    """Every file of the sandbox's runs/ and profiles/ (path -> sha256): 'touch nothing' means this is unchanged."""
    return {**{"runs/" + k: v for k, v in tree(learner.RUNS).items()},
            **{"profiles/" + k: v for k, v in tree(learner.PROFILES).items()}}


def everywhere(tag: str) -> dict[str, set[str]]:
    """name -> every sha256 that name has in the raw files, raw.zip, or ANY set-aside raw.zip.bad.<k> (a `dup_of`
    member read back through its target, as `restored` does)."""
    cdir = learner.RUNS / tag
    out: dict[str, set[str]] = {}
    sources = [raw_view(None, tag)] + [restored(cdir, z.name) for z in sorted(cdir.glob("raw.zip*"))
                                       if z.name != "raw.zip.part" and not z.name.endswith(".tmp")]
    for src in sources:
        for k, v in src.items():
            out.setdefault(k, set()).add(v)
    return out


def all_versions(tag: str, name: str) -> list[bytes]:
    """Every copy of one original: the raw file and the member of that name in every archive (set-aside ones too)."""
    import zipfile
    cdir = learner.RUNS / tag
    out = [(cdir / name).read_bytes()] if (cdir / name).exists() else []
    for z in sorted(cdir.glob("raw.zip*")):
        if z.name == "raw.zip.part":
            continue
        with zipfile.ZipFile(z) as zf:
            if name in zf.namelist():
                out.append(zf.read(name))
    return out


def captured(fn) -> tuple[object, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = fn()
    return rc, out.getvalue()


def log_text() -> str:
    return learner.LOG.read_text(encoding="utf-8") if learner.LOG.exists() else ""


def test_o3_review(tmp: Path) -> None:
    import zipfile
    keep1 = {"keep_raw_cycles": 1, "max_archives_per_prune": 9}

    # R4c verify_archive refuses an EXTRA member (kills review mutant M5) ------------------------------------------
    with O3Sandbox(tmp / "r4c"):
        c1 = make_raw_cycle(tmp, "ai0001")
        cdir = learner.RUNS / "ai0001"
        files = sorted(f for f in (cdir / "batch").rglob("*") if f.is_file())
        members = learner._scan_originals({f.relative_to(cdir).as_posix(): f for f in files})
        exact, extra = cdir / "exact.zip", cdir / "extra.zip"
        for z, more in ((exact, False), (extra, True)):
            with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    zf.write(f, f.relative_to(cdir).as_posix())
                if more:
                    zf.writestr("batch/L01/debug-logs/stray.log", b"not an original")
        check("R4c CONTROL: a zip holding exactly the members verifies", learner.verify_archive(exact, members) is None)
        check("R4c FAULT: a zip with one EXTRA member fails verification",
              learner.verify_archive(extra, members) is not None, learner.verify_archive(extra, members))
        del c1

    # R7c manifest-less recovery: a crash between the rename and the manifest --------------------------------------
    with O3Sandbox(tmp / "r7c"):
        ca, cb, cc, cn = (make_raw_cycle(tmp, t) for t in ("ai0001", "ai0002", "ai0003", "ai0004"))
        before = {t: raw_view(tmp, t) for t in ("ai0001", "ai0002", "ai0003")}
        learner._write_manifest = lambda cdir, tag, members: (_ for _ in ()).throw(OSError("simulated: disk full"))
        learner.prune(keep1, {"cycles": [ca, cb, cc, cn]})
        learner._write_manifest = O3_REAL["_write_manifest"]
        d = {t: learner.RUNS / t for t in ("ai0001", "ai0002", "ai0003")}
        setup = all((x / "raw.zip").exists() and not (x / "raw.manifest.json").exists()
                    and raw_view(tmp, t) == before[t] for t, x in d.items())
        check("R7c setup: a crash after the rename leaves raw.zip with NO manifest beside every original", setup)
        flip_member_byte(d["ai0001"] / "raw.zip", "batch/L01/debug-logs/big.log")  # FAULT a: a corrupt member
        short = d["ai0002"] / "raw.zip"  # FAULT b: a VALID zip that lacks one original
        with zipfile.ZipFile(short) as zf:
            keep = {n: zf.read(n) for n in zf.namelist() if not n.endswith("stdout.txt")}
        short.unlink()
        with zipfile.ZipFile(short, "w", zipfile.ZIP_DEFLATED) as zf:
            for n, data in keep.items():
                zf.writestr(n, data)
        za, zb = (d["ai0001"] / "raw.zip").read_bytes(), short.read_bytes()
        learner.prune(keep1, {"cycles": [ca, cb, cc, cn]})
        for t, c, zbytes, what in (("ai0001", ca, za, "a corrupt member"), ("ai0002", cb, zb, "a missing member")):
            check(f"R7c FAULT: no manifest + a zip with {what} -> every original kept, the zip set aside as "
                  f"raw.zip.bad.1 byte-intact, nothing flagged",
                  raw_view(tmp, t) == before[t] and not (d[t] / "raw.zip").exists()
                  and (d[t] / "raw.zip.bad.1").read_bytes() == zbytes and not c.get("pruned") and not c.get("held"),
                  sorted(p.name for p in d[t].iterdir()))
        check("R7c CONTROL: no manifest + a zip that matches the originals exactly -> manifest written, then deleted",
              cc.get("archived") and not (d["ai0003"] / "batch").exists()
              and restored(d["ai0003"]) == before["ai0003"]
              and learner.verify_archive(d["ai0003"] / "raw.zip", learner._read_manifest(
                  d["ai0003"] / "raw.manifest.json")["members"]) is None, cc)
        learner.prune(keep1, {"cycles": [ca, cb, cc, cn]})
        check("R7c CONTROL: the next prune archives the set-aside cycles afresh; the .bad.1 files stay byte-intact",
              ca.get("archived") and cb.get("archived") and restored(d["ai0001"]) == before["ai0001"]
              and restored(d["ai0002"]) == before["ai0002"]
              and (d["ai0001"] / "raw.zip.bad.1").read_bytes() == za and (d["ai0002"] / "raw.zip.bad.1").read_bytes()
              == zb)

    # R14 per-cycle state persistence: a process killed during the 2nd archive keeps the 1st's flags on disk --------
    with O3Sandbox(tmp / "r14"):
        cs = [make_raw_cycle(tmp, f"ai000{i}") for i in range(1, 4)]
        st = O3Sandbox.state(cs)
        real_archive, seen = learner.archive_cycle, []

        class Killed(BaseException):
            pass

        def second_dies(c, cmds=None):
            seen.append(c["tag"])
            if len(seen) == 2:
                raise Killed("simulated kill during the 2nd archive")
            return real_archive(c, cmds)

        learner.archive_cycle = second_dies
        try:
            learner.prune(keep1, st)
            died = False
        except Killed:
            died = True
        on_disk = json.loads(learner.STATE_FILE.read_text(encoding="utf-8"))["cycles"]
        check("R14 FAULT: killed during the 2nd archive -> state.json ON DISK already shows the 1st archived",
              died and on_disk[0].get("archived") is True and on_disk[0].get("pruned") is True
              and not on_disk[1].get("pruned"), (died, on_disk[0].get("archived"), seen))

    # R16 a set-aside NEVER overwrites: a stale raw.zip.bad.1 is kept, the new one is .bad.2 ------------------------
    with O3Sandbox(tmp / "r16"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        before = raw_view(tmp, "ai0001")
        learner._delete_ours = crash_before_delete
        learner.prune(keep1, {"cycles": [c1, c2]})
        learner._delete_ours = O3_REAL["_delete_ours"]
        d1 = learner.RUNS / "ai0001"
        stale = b"AN EARLIER SET-ASIDE ARCHIVE"
        (d1 / "raw.zip.bad.1").write_bytes(stale)
        flip_member_byte(d1 / "raw.zip", "batch/L01/debug-logs/big.log")
        zbad, mbytes = (d1 / "raw.zip").read_bytes(), (d1 / "raw.manifest.json").read_bytes()
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R16 FAULT: a stale raw.zip.bad.1 present -> the new set-aside is .bad.2 (zip AND manifest), both "
              "byte-intact, originals kept", (d1 / "raw.zip.bad.1").read_bytes() == stale
              and (d1 / "raw.zip.bad.2").read_bytes() == zbad and (d1 / "raw.manifest.json.bad.2").read_bytes() == mbytes
              and raw_view(tmp, "ai0001") == before and not (d1 / "raw.zip").exists(),
              sorted(p.name for p in d1.iterdir()))
        src, dst = d1 / "x.src", d1 / "raw.zip.bad.1"
        src.write_bytes(b"new")
        try:
            learner._rename_no_overwrite(src, dst)
            refused = False
        except FileExistsError:
            refused = True
        check("R16 FAULT: the no-overwrite rename refuses an existing target, both files unchanged",
              refused and dst.read_bytes() == stale and src.read_bytes() == b"new")
        learner._os_rename = os.replace  # POSIX semantics: the OS rename itself WOULD overwrite
        try:
            learner._rename_no_overwrite(src, dst)
            refused = False
        except FileExistsError:
            refused = True
        learner._os_rename = O3_REAL["_os_rename"]
        check("R16 FAULT: the refusal is the learner's own check, not Windows': with an overwriting OS rename the "
              "target is still kept", refused and dst.read_bytes() == stale and src.read_bytes() == b"new")
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R16 CONTROL: the next prune archives afresh; .bad.1 and .bad.2 are still byte-intact",
              c1.get("archived") and restored(d1) == before and (d1 / "raw.zip.bad.1").read_bytes() == stale
              and (d1 / "raw.zip.bad.2").read_bytes() == zbad)
        c3 = make_raw_cycle(tmp, "ai0003")  # a manifest WITHOUT its zip (a set-aside interrupted between its renames)
        d3 = learner.RUNS / "ai0003"
        before3, orphan_man = raw_view(tmp, "ai0003"), b'{"members": []}'
        (d3 / "raw.manifest.json").write_bytes(orphan_man)
        learner.prune(keep1, {"cycles": [c3, c2]})
        check("R16 a manifest without its zip is set aside (never overwritten), then the cycle is archived afresh",
              c3.get("archived") and (d3 / "raw.manifest.json.bad.1").read_bytes() == orphan_man
              and restored(d3) == before3, sorted(p.name for p in d3.iterdir()))
        man3 = (d3 / "raw.manifest.json").read_bytes()
        try:
            learner._write_manifest(d3, "ai0003", [])
            kept = False
        except FileExistsError:
            kept = True
        check("R16 FAULT: writing a manifest over an existing one is refused; the existing manifest is unchanged",
              kept and (d3 / "raw.manifest.json").read_bytes() == man3)

    # R17 HOLD: what the code cannot prove safe touches NOTHING and is flagged for a human ---------------------------
    with O3Sandbox(tmp / "r17"):
        cs = {t: make_raw_cycle(tmp, t) for t in ("ai0001", "ai0002", "ai0003", "ai0004", "ai0005", "ai0006")}
        newest = make_raw_cycle(tmp, "ai0009")
        order = list(cs.values()) + [newest]
        learner._delete_ours = delete_half  # ai0001 and ai0002: a delete that stopped part-way
        learner.prune(keep1, {"cycles": [cs["ai0001"], cs["ai0002"], newest]})
        learner._delete_ours = crash_before_delete  # ai0004: zip + manifest + originals, delete not started
        learner.prune(keep1, {"cycles": [cs["ai0004"], newest]})
        learner._delete_ours = O3_REAL["_delete_ours"]
        with open(learner.RUNS / "ai0001" / "batch" / "L01" / "debug-logs" / "a-1.log", "ab") as fh:
            fh.write(b"written after the partial delete\n")  # ai0001: a remaining original CHANGED
        (learner.RUNS / "ai0002" / "batch" / "L02" / "late.log").write_bytes(b"new file\n")  # ai0002: an EXTRA file
        cs["ai0003"]["created"] = [p for p in cs["ai0003"]["created"] if not p.endswith("batch")]  # unnamed batch/
        (learner.RUNS / "ai0004" / "raw.manifest.json").write_text("{ half a manifest", encoding="utf-8")
        if os.name == "nt":  # ai0005: `created` names its batch/ with another case and separators (finding 8)
            cs["ai0005"]["created"][0] = cs["ai0005"]["created"][0].upper().replace("\\", "/") + "/"
        else:
            cs["ai0005"]["created"][0] = cs["ai0005"]["created"][0] + "/"
        before5 = raw_view(tmp, "ai0005")
        snap = all_tree()
        st = {"cycle": len(order), "cycles": order, "current": None, "failures": 0}
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 1}, st)
        held = {t: c.get("held") for t, c in cs.items() if c.get("held")}
        untouched = {k: v for k, v in all_tree().items() if not k.startswith(("runs/ai0005/", "profiles/endless-ai0005",
                                                                               "runs/ai0006/", "profiles/endless-ai0006"))}
        snap_rest = {k: v for k, v in snap.items() if not k.startswith(("runs/ai0005/", "profiles/endless-ai0005",
                                                                         "runs/ai0006/", "profiles/endless-ai0006"))}
        check("R17 FAULT: a partial delete + a CHANGED original -> HELD", "ai0001" in held
              and "no longer match" in held["ai0001"]["reason"], held.get("ai0001"))
        check("R17 FAULT: a partial delete + an EXTRA original -> HELD", "ai0002" in held, held.get("ai0002"))
        check("R17 FAULT: batch/ on disk that no `created` entry names -> HELD (its profile NOT deleted either)",
              "ai0003" in held and (learner.PROFILES / "endless-ai0003-H1-torchic").exists(), held.get("ai0003"))
        check("R17 FAULT: an unreadable raw.manifest.json -> HELD", "ai0004" in held, held.get("ai0004"))
        check("R17 FAULT: HELD touches NOTHING: every file of the held cycles byte-identical, raw.zip still raw.zip",
              untouched == snap_rest and (learner.RUNS / "ai0001" / "raw.zip").exists()
              and not any(c.get("pruned") or c.get("archived") for t, c in cs.items() if t in held), sorted(held))
        check("R17 CONTROL: held cycles do not count toward max_archives_per_prune (cap 1): ai0005 (a case/separator "
              "variant of its batch path) is archived", cs["ai0005"].get("archived")
              and restored(learner.RUNS / "ai0005") == before5 and not cs["ai0006"].get("pruned"),
              cs["ai0005"])
        calls = []
        real_archive = learner.archive_cycle
        learner.archive_cycle = lambda c, cmds=None: calls.append(c["tag"]) or real_archive(c, cmds)
        held_part = learner.RUNS / "ai0001" / "raw.zip.part"
        held_part.write_bytes(b"PK left in a held cycle")
        learner.LOG.write_text("", encoding="utf-8")
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, st)
        learner.archive_cycle = real_archive
        check("R17 a held cycle is SKIPPED at the next boundary (not even its leftover .part is touched), with one "
              "summary line naming it", not set(held) & set(calls) and "ai0006" in calls and held_part.exists()
              and "held for review: ai0001, ai0002, ai0003, ai0004" in log_text(), calls)
        held_part.unlink()
        learner.save_state(st)
        rc, out = captured(learner.cmd_archive_check)
        rec = json.loads((learner.DATA / "archive_check.json").read_text(encoding="utf-8"))
        check("R17 archive-check lists 'HELD <tag> <reason>', records the count, exits 1",
              rc == 1 and "HELD ai0001 " in out and "HELD ai0004 " in out and rec["held"] == 4, (rc, out[-300:]))
        rc, out = captured(learner.cmd_status)
        check("R17 `learner.py status` prints the held count", "held for review: 4 (" in out, out)
        for c in cs.values():  # a human resolves them: clears 'held', rewrites ai0004's manifest from its originals
            c.pop("held", None)
        d4 = learner.RUNS / "ai0004"
        (d4 / "raw.manifest.json").unlink()
        learner._write_manifest(d4, "ai0004", learner._plan_members(learner._scan_originals(
            learner._cycle_originals(cs["ai0004"]))))
        learner.save_state(st)
        rc, out = captured(learner.cmd_archive_check)
        check("R17 CONTROL: nothing held and every zip OK -> archive-check exits 0",
              rc == 0 and "HELD" not in out and "BAD" not in out, (rc, out))
        cs["ai0002"]["held"] = {"reason": "test", "since": "now"}
        learner.save_state(st)
        rc, out = captured(learner.cmd_archive_check)
        check("R17 FAULT: every zip OK but one cycle HELD -> archive-check exits 1 on the hold alone",
              rc == 1 and "BAD" not in out and "HELD ai0002 test" in out, (rc, out))
        cs["ai0002"].pop("held")

    # R15 QUIESCENCE: a cycle still in use is skipped this boundary (not held, not counted) ------------------------
    with O3Sandbox(tmp / "r15"):
        learner.QUIET_MINUTES = 60
        learner._cmdlines = O3_REAL["_cmdlines"]  # the REAL process scan
        cs = [make_raw_cycle(tmp, f"ai000{i}") for i in range(1, 6)]
        # sorts first, so the in-use reason names it: a cp1252 console or pipe cannot print it (log() must cope)
        (learner.RUNS / "ai0001" / "batch" / "A-Pokémon — 日本.log").write_bytes(b"x\n")
        st = {"cycles": cs}
        snap = all_tree()
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, st)
        check("R15 FAULT: originals modified within QUIET_MINUTES -> nothing archived or deleted, nothing flagged",
              all_tree() == snap and not any(c.get("pruned") or c.get("held") for c in cs)
              and "in use (" in log_text(), [c.get("pruned") for c in cs])
        check("R15 an in-use reason naming a non-ASCII file is logged (no UnicodeEncodeError aborts the prune)",
              "ai0001: in use (batch/A-Pokémon" in log_text() and "prune FAILED" not in log_text(),
              log_text()[-300:])
        old = time.time() - 2 * 3600
        for t in ("ai0002", "ai0003", "ai0004"):
            for f in list((learner.RUNS / t / "batch").rglob("*")) + \
                    list((learner.PROFILES / f"endless-{t}-H1-torchic").rglob("*")):
                os.utime(f, (old, old))
        for f in (learner.RUNS / "ai0001" / "batch").rglob("*"):  # ai0001: batch/ quiet, its lane PROFILE just written
            os.utime(f, (old, old))
        lane = child(SLEEP_BODY, "pokebot.py", "endless-ai0003-H1-torchic")
        runner = child(SLEEP_BODY, "x4_headless.py", "--out", learner.RUNS / "ai0004" / "batch")
        try:
            time.sleep(0.3)
            before3, before4 = raw_view(tmp, "ai0003"), raw_view(tmp, "ai0004")
            learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 1}, st)
            check("R15 CONTROL: quiet for QUIET_MINUTES and no process -> archived, even with cap 1 after a cycle "
                  "that was skipped as in use (in use is not counted)", cs[1].get("archived") and not cs[0].get("pruned"),
                  [c.get("archived") for c in cs])
            learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, st)
            check("R15 FAULT: a live process naming endless-<tag>- (an orphaned lane) -> that cycle untouched",
                  raw_view(tmp, "ai0003") == before3 and not cs[2].get("pruned") and not cs[2].get("held"))
            check("R15 FAULT: its batch runner alive (x4_headless.py naming the cycle folder) -> untouched",
                  raw_view(tmp, "ai0004") == before4 and not cs[3].get("pruned") and not cs[3].get("held"))
        finally:
            for p in (lane, runner):
                p.kill()
                p.wait()
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, st)
        check("R15 CONTROL: once those processes are gone the next boundary archives both",
              cs[2].get("archived") and cs[3].get("archived") and restored(learner.RUNS / "ai0003") == before3,
              [c.get("archived") for c in cs])
        check("R22 FAULT: batch/ quiet but a LANE-PROFILE file modified within QUIET_MINUTES -> in use, untouched",
              not cs[0].get("pruned") and "ai0001: in use (profiles/endless-ai0001-H1-torchic/" in log_text()
              and (learner.PROFILES / "endless-ai0001-H1-torchic" / "badge-log.json").exists(), log_text()[-400:])
        before1 = raw_view(tmp, "ai0001")
        for f in (learner.PROFILES / "endless-ai0001-H1-torchic").rglob("*"):
            os.utime(f, (old, old))
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, st)
        check("R22 CONTROL: once the profile is quiet too, the cycle is archived (profile files included)",
              cs[0].get("archived") and restored(learner.RUNS / "ai0001") == before1
              and not (learner.PROFILES / "endless-ai0001-H1-torchic").exists(), cs[0])

    # R19 a junction inside batch/: never followed, never archived, and what it points to is never deleted --------
    with O3Sandbox(tmp / "r19"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        before = raw_view(tmp, "ai0001")
        outside = tmp / "r19" / "OUTSIDE"
        (outside / "sub").mkdir(parents=True)
        (outside / "precious.txt").write_bytes(b"must never be archived or deleted\n" * 50)
        (outside / "sub" / "deep.txt").write_bytes(b"deep\n")
        out_before = tree(outside)
        link = learner.RUNS / "ai0001" / "batch" / "L01" / "junction_out"
        try:
            import _winapi
            _winapi.CreateJunction(str(outside), str(link))
            made = link.is_junction()
        except Exception as exc:  # noqa: BLE001
            made = False
            print(f"SKIP R19 (junction arm): a junction could not be made without privilege here: {exc!r}")
        if made:
            learner.prune(keep1, {"cycles": [c1, c2]})
            got = restored(learner.RUNS / "ai0001") if (learner.RUNS / "ai0001" / "raw.zip").exists() else {}
            check("R19 FAULT: a junction inside batch/ is not followed: no member from outside batch/ is archived",
                  not any("junction_out" in n for n in got), sorted(got))
            check("R19 FAULT: and what the junction points to is byte-identical after the delete",
                  tree(outside) == out_before and len(out_before) == 2)
            check("R19 CONTROL: every real original is archived and batch/ is gone",
                  got == before and c1.get("archived") and not (learner.RUNS / "ai0001" / "batch").exists(), sorted(got))
            c3 = make_raw_cycle(tmp, "ai0003")  # runs/<tag>/batch ITSELF a junction to a folder outside
            b3 = learner.RUNS / "ai0003" / "batch"
            shutil.rmtree(b3)
            _winapi.CreateJunction(str(outside), str(b3))
            snap = tree(outside)
            learner.prune(keep1, {"cycles": [c3, c2]})
            check("R19 FAULT: runs/<tag>/batch that is itself a junction -> HELD, what it points to untouched",
                  c3.get("held") and tree(outside) == snap and b3.is_junction()
                  and not (learner.RUNS / "ai0003" / "raw.zip").exists(), c3)
            os.rmdir(b3)  # removes the junction only


def read_progress(path: Path) -> int:
    """The writer's last completed line number (it rewrites the file per line: a read can land mid-rewrite)."""
    for _ in range(100):
        try:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                return int(text)
        except (OSError, ValueError):
            pass
        time.sleep(0.01)
    raise AssertionError(f"no progress readable from {path}")


def test_o3_orphan(tmp: Path) -> None:
    """The O3 review's ORPHAN WRITER, as a regression test: a REAL process appends to one old-cycle log across 4
    boundaries. At EVERY boundary every static original's sha256 must exist raw or in some archive member (raw.zip or
    any raw.zip.bad.<k>), and the appended log's newest line (the writer records each one it completed) must exist in
    some copy. Variants: the writer holds the file open; it stops after boundary 2; it reopens the file per line (no
    open handle, so Windows CAN delete it mid-archive)."""
    name = "batch/L01/debug-logs/a-1.log"
    for variant, stop_after, mode in (("holding", 99, "hold"), ("stops after boundary 2", 2, "hold"),
                                      ("reopening", 99, "reopen")):
        root = tmp / variant.replace(" ", "-")
        with O3Sandbox(root):
            c1, c2 = make_raw_cycle(root, "ai0001"), make_raw_cycle(root, "ai0002")
            st = O3Sandbox.state([c1, c2])
            static = {k: v for k, v in raw_view(root, "ai0001").items() if k != name}
            progress = root / "orphan-progress.txt"
            target = learner.RUNS / "ai0001" / name
            # BOUNDED (F7): `alive()` is checked before every line, so a hard-killed suite leaves no writer behind
            body = ("p, done = ARGS[0], Path(ARGS[1])\ni = 0\n" +
                    ("f = open(p, 'ab')\nwhile alive():\n    f.write(f'orphan line {i}\\n'.encode()); f.flush()\n"
                     "    done.write_text(str(i)); i += 1; time.sleep(0.1)\n" if mode == "hold" else
                     "while alive():\n    with open(p, 'ab') as f:\n        f.write(f'orphan line {i}\\n'.encode())\n"
                     "    done.write_text(str(i)); i += 1; time.sleep(0.05)\n"))
            writer = child(body, target, progress, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.time() + 10
            while not progress.exists() and time.time() < deadline:
                time.sleep(0.02)
            bad, steps = [], []
            try:
                for b in range(1, 5):
                    learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 3}, st)
                    if b == stop_after:
                        writer.kill()
                        writer.wait()
                    last = read_progress(progress)
                    where = everywhere("ai0001")
                    lost = [k for k, v in static.items() if v not in where.get(k, set())]
                    newest = f"orphan line {last}\n".encode()
                    have_newest = any(newest in v for v in all_versions("ai0001", name))
                    steps.append((b, sorted(p.name for p in (learner.RUNS / "ai0001").iterdir()),
                                  bool(c1.get("held")), bool(c1.get("archived"))))
                    if lost or not have_newest:
                        bad.append((b, lost, last, have_newest))
                    time.sleep(0.3)
            finally:
                writer.kill()
                writer.wait()
            touched = any(n.startswith("raw.zip") for n in steps[-1][1]) if steps else False
            check(f"R18 ORPHAN WRITER ({variant}): at every one of 4 boundaries every original's bytes exist raw or in "
                  f"an archive, and the newest appended line exists", not bad and len(steps) == 4 and touched,
                  (bad, steps))


def test_o3_liveness(tmp: Path) -> None:
    """F2: save_state rides out a reader holding state.json; prune never raises; the loop survives a failing disk
    check without starting a batch."""
    with O3Sandbox(tmp / "save"):
        st = {"cycle": 1, "cycles": [], "current": None, "failures": 0}
        real_replace, calls = learner._os_replace, []

        def locked_twice(src, dst):
            calls.append(src)
            if len(calls) <= 2:
                raise PermissionError("simulated: a reader holds state.json open")
            return real_replace(src, dst)

        learner._os_replace = locked_twice
        learner.save_state(dict(st, cycle=7))
        learner._os_replace = real_replace
        check("R20 save_state retries a locked replace (twice locked, then free) and writes the new state",
              len(calls) == 3 and learner.load_state()["cycle"] == 7, len(calls))
        if os.name == "nt":  # the DEMONSTRATED trigger: a real process holding state.json open for reading
            ready = tmp / "save" / "reader-ready"
            reader = child("f = open(ARGS[0], 'rb')\nPath(ARGS[1]).write_text('1')\n" + SLEEP_BODY,
                           learner.STATE_FILE, ready, deadline=0.6)  # holds state.json open for its 0.6 s bound
            try:
                while not ready.exists() and reader.poll() is None:
                    time.sleep(0.01)
                learner.REPLACE_TRIES = 1
                try:
                    learner.save_state(dict(st, cycle=8))
                    fault = "not blocked"
                except PermissionError:
                    fault = "blocked"
                learner.REPLACE_TRIES, learner.REPLACE_WAIT_S = 6, 0.25
                learner.save_state(dict(st, cycle=9))
                reader.wait(timeout=10)  # bounded here too: a reader that never lets go fails the test, never hangs it
            finally:
                reader.kill()
                reader.wait()
            check("R20 FAULT: a real reader holding state.json open blocks a single replace (the trigger is real)",
                  fault == "blocked", fault)
            check("R20 CONTROL: with the retry, save_state waits the reader out and writes",
                  learner.load_state()["cycle"] == 9)

    with O3Sandbox(tmp / "prune"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        results = {}
        for label, setup in (("free_gb raises", lambda: setattr(learner, "free_gb", lambda: 1 / 0)),
                             ("state.json can never be replaced",
                              lambda: setattr(learner, "_os_replace", lambda s, d: (_ for _ in ()).throw(
                                  PermissionError("simulated: locked for good"))))):
            setup()
            try:
                learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 3},
                              {"cycles": [{"created": []}, dict(c1), dict(c2)]})
                results[label] = "returned"
            except Exception as exc:  # noqa: BLE001
                results[label] = f"RAISED {exc!r}"
            learner.free_gb, learner._os_replace = (lambda: 500.0), O3_REAL["_os_replace"]
        check("R20 FAULT: prune NEVER raises into the loop (free_gb raising; state.json locked for good)",
              set(results.values()) == {"returned"} and "prune FAILED" in log_text(), results)
        c3, c4 = make_raw_cycle(tmp, "ai0003"), make_raw_cycle(tmp, "ai0004")
        before3 = raw_view(tmp, "ai0003")
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 3}, {"cycles": [{"created": []}, c3, c4]})
        check("R20 CONTROL: a tag-less cycle entry is skipped, the others are still archived",
              c3.get("archived") and restored(learner.RUNS / "ai0003") == before3, c3)

    with O3Sandbox(tmp / "loop"):
        learner.DEPLOYMENT.parent.mkdir(parents=True, exist_ok=True)
        learner.DEPLOYMENT.write_text("", encoding="utf-8")
        learner.save_state({"cycle": 0, "cycles": [], "current": None, "failures": 0,
                            "parser_version": scoring.PARSER_VERSION})
        learner.load_config = lambda: dict(learner.DEFAULTS, auto_update=False)
        calls = {"guard": 0, "sleep": [], "run": 0}

        def failing_guard(cfg, state):
            calls["guard"] += 1
            raise OSError("simulated: disk_usage failed")

        learner.disk_guard = failing_guard
        learner.sleep_unless_stopped = lambda m: calls["sleep"].append(m) or len(calls["sleep"]) < 2
        learner.run_cycle = lambda *a: calls.__setitem__("run", calls["run"] + 1) or True
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                rc = learner.loop(single=False)
            except Exception as exc:  # noqa: BLE001
                rc = f"RAISED {exc!r}"
        check("R20 FAULT: disk_guard raising -> logged, NO batch started, it waits idle_wait_minutes (STOP-aware) and "
              "continues the loop", rc == 0 and calls["guard"] == 2 and calls["run"] == 0
              and calls["sleep"] == [15.0, 15.0] and "disk check FAILED" in log_text()
              and not learner.LOCK.exists(), (rc, calls))


def test_o3_profiles(tmp: Path) -> None:
    """F6 (re-verify 2026-10-21): a cycle's LANE PROFILES are archived with its batch/ before anything is deleted. On the
    clone each profile holds badge-log.json, stats.db and the saves (found nowhere else) plus debug logs byte-identical
    to batch/'s copies; before F6 they were deleted unarchived."""
    import zipfile
    keep1 = {"keep_raw_cycles": 1, "max_archives_per_prune": 9}
    prof = lambda tag: learner.PROFILES / f"endless-{tag}-H1-torchic"  # noqa: E731

    # R22a dup_of: a byte-identical twin is recorded, not stored; a near-twin is stored; foreign paths untouched ------
    with O3Sandbox(tmp / "r22a"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        p1 = prof("ai0001")
        a1 = (learner.RUNS / "ai0001" / "batch" / "L01" / "debug-logs" / "a-1.log").read_bytes()
        (p1 / "debug-logs" / "a-1.log").write_bytes(a1[:-1] + bytes([a1[-1] ^ 1]))  # same name and size, other bytes
        (p1 / "copy-of-stdout.txt").write_bytes((learner.RUNS / "ai0001" / "batch" / "L02" / "stdout.txt").read_bytes())
        (p1 / "stats.db").write_bytes(bytes(range(256)) * 9)
        unlisted = learner.PROFILES / "endless-ai0001-H9-unlisted"  # same tag, but no `created` entry names it
        foreign = [learner.PROFILES / "endless-s14-H1-torchic", tmp / "r22a" / "elsewhere"]
        for d in [unlisted] + foreign:
            d.mkdir(parents=True)
            (d / "keep.txt").write_bytes(b"not this cycle's to archive or delete\n")
        c1["created"] += [str(d) for d in foreign]
        if os.name == "nt":  # the SAME profile named twice, once in another case: archived once, under one name
            c1["created"].append(str(p1.parent / p1.name.upper()))
        before = {k: v for k, v in raw_view(tmp, "ai0001").items() if "H9-unlisted" not in k}
        outside = {d: tree(d) for d in [unlisted] + foreign}
        learner.prune(keep1, {"cycles": [c1, c2]})
        cdir = learner.RUNS / "ai0001"
        man = learner._read_manifest(cdir / "raw.manifest.json") or {"members": []}
        by = {m["name"]: m for m in man["members"]}
        with zipfile.ZipFile(cdir / "raw.zip") as zf:
            names = set(zf.namelist())
        pre = "profiles/endless-ai0001-H1-torchic/"
        check("R22 every lane-profile file's bytes read back from raw.zip (stored, or through dup_of its batch twin) "
              "equal the original's sha256, and the profile is gone", len(before) == 10 and restored(cdir) == before
              and not p1.exists() and c1.get("archived"), (len(before), sorted(set(before) ^ set(restored(cdir)))))
        check("R22 the byte-identical twin (same name, size, CRC32) is dup_of the batch member and NOT stored again",
              by.get(pre + "debug-logs/big.log", {}).get("dup_of") == "batch/L01/debug-logs/big.log"
              and pre + "debug-logs/big.log" not in names and man.get("n_dup") == 1 and man.get("n_stored") == 9,
              (by.get(pre + "debug-logs/big.log"), man.get("n_stored"), man.get("n_dup")))
        check("R22 CONTROL: same name+size but other bytes, and same bytes under another name, are STORED",
              {pre + "debug-logs/a-1.log", pre + "copy-of-stdout.txt", pre + "badge-log.json", pre + "stats.db"} <= names
              and not by[pre + "debug-logs/a-1.log"].get("dup_of") and not by[pre + "copy-of-stdout.txt"].get("dup_of"),
              sorted(names))
        check("R22 FAULT: a same-tag profile no `created` entry names, and foreign `created` paths, are neither archived "
              "nor deleted", all(tree(d) == t for d, t in outside.items())
              and not any("H9-unlisted" in n or "s14" in n or "elsewhere" in n for n in names), sorted(names))

        # R22b verify_archive checks every dup_of target, and archive-check reports a bad one ------------------------
        good = man["members"]
        twin = pre + "debug-logs/big.log"
        bent = {"is not in the zip": [dict(m, dup_of="batch/L01/debug-logs/gone.log") if m["name"] == twin else m
                                      for m in good],
                "has another CRC": [dict(m, crc32=m["crc32"] ^ 1) if m["name"] == twin else m for m in good],
                "has another size": [dict(m, size=m["size"] + 1) if m["name"] == twin else m for m in good]}
        bent["repeats a stored member's name"] =good + [dict(by["batch/L02/stdout.txt"], dup_of="batch/L02/stdout.txt")]
        check("R22 CONTROL: the written manifest verifies against raw.zip",
              learner.verify_archive(cdir / "raw.zip", good) is None)
        odd = cdir / "odd.manifest.json"
        odd.write_text(json.dumps(dict(man, members=[dict(m, dup_of=123) if m["name"] == twin else m for m in good])),
                       encoding="utf-8")
        check("R22 FAULT: a manifest whose dup_of is not a string is unreadable (-> HOLD, case 1); CONTROL: the real "
              "one reads", learner._read_manifest(odd) is None
              and learner._read_manifest(cdir / "raw.manifest.json") is not None)
        odd.unlink()
        for what, members in bent.items():
            check(f"R22 FAULT: a manifest whose dup_of member {what} fails verification",
                  learner.verify_archive(cdir / "raw.zip", members) is not None,
                  learner.verify_archive(cdir / "raw.zip", members))
        mbytes = (cdir / "raw.manifest.json").read_bytes()
        (cdir / "raw.manifest.json").write_text(json.dumps(dict(man, members=bent["has another CRC"])),
                                                encoding="utf-8")
        rc, out = captured(learner.cmd_archive_check)
        (cdir / "raw.manifest.json").write_bytes(mbytes)
        check("R22 FAULT: archive-check reports BAD when a manifest's dup_of no longer matches its target",
              rc == 1 and out.startswith("BAD ai0001 ") and "dup_of" in out, out)

    # R22c a cycle with NO batch file but profile files ARCHIVES them (never the old 'no raw logs' delete) -----------
    with O3Sandbox(tmp / "r22c"):
        c1, c3, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0003"), make_raw_cycle(tmp, "ai0002")
        shutil.rmtree(learner.RUNS / "ai0001" / "batch")
        (learner.RUNS / "ai0001" / "batch").mkdir()
        before = raw_view(tmp, "ai0001")
        shutil.rmtree(learner.RUNS / "ai0003")  # runs/<tag>/ itself gone, its profile left
        before3 = raw_view(tmp, "ai0003")
        learner.prune(keep1, {"cycles": [c1, c3, c2]})
        check("R22 FAULT: empty batch/ + profile files -> the profile files are archived (all stored: no batch twin) "
              "and only then deleted", len(before) == 3 and c1.get("archived") and not prof("ai0001").exists()
              and restored(learner.RUNS / "ai0001") == before, (len(before), c1))
        check("R22 FAULT: runs/<tag>/ gone entirely + profile files -> archived into a new runs/<tag>/raw.zip",
              len(before3) == 3 and c3.get("archived") and restored(learner.RUNS / "ai0003") == before3, c3)
        c4, c5 = make_raw_cycle(tmp, "ai0004"), make_raw_cycle(tmp, "ai0005")
        shutil.rmtree(learner.RUNS / "ai0004" / "batch")
        shutil.rmtree(prof("ai0004"))
        prof("ai0004").mkdir()
        learner.prune(keep1, {"cycles": [c4, c5]})
        check("R22 CONTROL: no file anywhere (an empty profile folder) -> 'no raw logs', its empty leftovers deleted, "
              "no raw.zip", c4.get("pruned") and not prof("ai0004").exists()
              and not (learner.RUNS / "ai0004" / "raw.zip").exists(), c4)

    # R22e the pre-delete re-stat covers profile files ---------------------------------------------------------------
    with O3Sandbox(tmp / "r22e"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        badge = prof("ai0001") / "badge-log.json"
        real_verify = learner.verify_archive

        def write_during(zpath, members):  # a lane writes its badge log while the archive is being verified
            if Path(zpath).name.endswith(".part"):
                with open(badge, "ab") as fh:
                    fh.write(b"\n{\"late\": true}")
            return real_verify(zpath, members)

        learner.verify_archive = write_during
        learner.prune(keep1, {"cycles": [c1, c2]})
        learner.verify_archive = real_verify
        late = badge.read_bytes() if badge.exists() else b""
        check("R22 FAULT: a profile file written while the cycle was being archived -> NOTHING deleted, not flagged",
              late.endswith(b"{\"late\": true}") and (learner.RUNS / "ai0001" / "batch").exists()
              and not c1.get("pruned") and "changed while it was being archived" in log_text(), c1)
        now_view = raw_view(tmp, "ai0001")
        learner.prune(keep1, {"cycles": [c1, c2]})  # the manifest no longer matches: set aside
        learner.prune(keep1, {"cycles": [c1, c2]})  # archived afresh
        check("R22 CONTROL: the next boundaries set the stale archive aside and archive the CURRENT bytes",
              c1.get("archived") and restored(learner.RUNS / "ai0001") == now_view
              and (learner.RUNS / "ai0001" / "raw.zip.bad.1").exists(), c1)

    # R22f a profile `created` entry that is a file or a junction -> HELD, nothing touched ---------------------------
    with O3Sandbox(tmp / "r22f"):
        c1, c3, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0003"), make_raw_cycle(tmp, "ai0002")
        as_file = learner.PROFILES / "endless-ai0001-H9-file"
        as_file.write_bytes(b"a profile that is a file\n")
        c1["created"].append(str(as_file))
        made = False
        out_snap: dict[str, str] = {}
        if os.name == "nt":
            outside = tmp / "r22f" / "OUTSIDE"
            outside.mkdir()
            (outside / "precious.txt").write_bytes(b"never archived, never deleted\n")
            out_snap = tree(outside)
            import _winapi
            junction = learner.PROFILES / "endless-ai0003-H9-junction"
            try:
                _winapi.CreateJunction(str(outside), str(junction))
                made = junction.is_junction()
            except Exception as exc:  # noqa: BLE001
                print(f"SKIP R22 (junction arm): {exc!r}")
            c3["created"].append(str(junction))
        snap = all_tree()
        learner.prune(keep1, {"cycles": [c1, c3, c2]})
        check("R22 FAULT: a profile `created` entry that is a FILE -> HELD, every file of the cycle byte-identical",
              c1.get("held") and "lane profile" in c1["held"]["reason"] and not c1.get("pruned")
              and {k: v for k, v in all_tree().items() if "ai0001" in k} == {k: v for k, v in snap.items()
                                                                            if "ai0001" in k}, c1.get("held"))
        if made:
            check("R22 FAULT: a profile that is a JUNCTION -> HELD; what it points to untouched",
                  c3.get("held") and tree(outside) == out_snap and len(out_snap) == 1
                  and not (learner.RUNS / "ai0003" / "raw.zip").exists(), c3)
            os.rmdir(junction)
        c1.pop("held")
        c1["created"].remove(str(as_file))
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R22 CONTROL: without that entry the cycle archives; the stray file (no longer named) is untouched",
              c1.get("archived") and as_file.read_bytes() == b"a profile that is a file\n", c1)

    # R22g a delete that stops part-way INSIDE a profile: not flagged; resumed (case 4), or HELD on an extra file -----
    with O3Sandbox(tmp / "r22g"):
        c1, c3, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0003"), make_raw_cycle(tmp, "ai0002")
        before1 = raw_view(tmp, "ai0001")

        def batch_and_half_a_profile(c):
            shutil.rmtree(learner.RUNS / c["tag"] / "batch")
            (prof(c["tag"]) / "badge-log.json").unlink()

        learner._delete_ours = batch_and_half_a_profile
        learner.prune(keep1, {"cycles": [c1, c3, c2]})
        learner._delete_ours = O3_REAL["_delete_ours"]
        check("R22 FAULT: batch/ deleted but the profile only part-way -> NOT flagged archived/pruned",
              not c1.get("pruned") and not c1.get("archived") and prof("ai0001").exists()
              and not (learner.RUNS / "ai0001" / "batch").exists(), c1)
        (prof("ai0003") / "debug-logs" / "late.log").write_bytes(b"a file that appeared after the partial delete\n")
        learner.prune(keep1, {"cycles": [c1, c3, c2]})
        check("R22 CONTROL: the next prune resumes the delete (raw.zip re-verified against the remaining profile "
              "files)", c1.get("archived") and not prof("ai0001").exists()
              and restored(learner.RUNS / "ai0001") == before1, c1)
        check("R22 FAULT: a partial delete + an EXTRA profile file -> HELD, the profile left as it is",
              c3.get("held") and (prof("ai0003") / "debug-logs" / "late.log").exists(), c3.get("held"))

    # R22i a manifest written before profiles were archived (batch/ only) -> set aside, archived afresh with them -----
    with O3Sandbox(tmp / "r22i"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        before1 = raw_view(tmp, "ai0001")
        cdir = learner.RUNS / "ai0001"
        old = {f.relative_to(cdir).as_posix(): f for f in learner._originals(cdir / "batch")}
        with zipfile.ZipFile(cdir / "raw.zip", "w", zipfile.ZIP_DEFLATED) as zf:
            for n, f in old.items():
                zf.write(f, n)
        learner._write_manifest(cdir, "ai0001", learner._scan_originals(old))
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R22 FAULT: a batch-only archive beside profile files -> set aside, every original kept",
              (cdir / "raw.zip.bad.1").exists() and raw_view(tmp, "ai0001") == before1 and not c1.get("pruned"),
              sorted(p.name for p in cdir.iterdir()))
        learner.prune(keep1, {"cycles": [c1, c2]})
        check("R22 CONTROL: the next prune archives the cycle afresh, profile files included",
              c1.get("archived") and restored(cdir) == before1 and not prof("ai0001").exists(), c1)


def test_children(tmp: Path) -> None:
    """F7 (re-verify 2026-10-21): every helper child is BOUNDED. Proven here on `child()` itself; the hard-kill of the
    whole suite mid-R18 is proven by the re-verify's orphans.py."""
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    orphan = child(SLEEP_BODY, parent=dead.pid)  # its parent is already gone
    expiring = child(SLEEP_BODY, deadline=0.5)  # its parent (this suite) lives on
    control = child(SLEEP_BODY)
    t0 = time.time()
    while time.time() - t0 < 5 and (orphan.poll() is None or expiring.poll() is None):
        time.sleep(0.05)
    time.sleep(max(0.0, 1.5 - (time.time() - t0)))
    states = {"orphan": orphan.poll(), "expiring": expiring.poll(), "control": control.poll()}
    for p in (orphan, expiring, control):
        p.kill()
        p.wait()
    check("R23 FAULT: a helper child whose parent pid is gone exits by itself (within 5 s)",
          states["orphan"] is not None, states)
    check("R23 FAULT: a helper child past its deadline exits by itself, its parent alive", states["expiring"] is not None,
          states)
    check("R23 CONTROL: a child with a live parent and time left is still running after 1.5 s",
          states["control"] is None, states)


def test_o3_lock(tmp: Path) -> None:
    """F5: a learner starting while a manual `learner.py archive` holds the lock WAITS for it instead of exiting 2
    (run_agent.ps1 treats exit 2 as 'another learner runs' and stops for good). F8: when it GIVES UP it writes
    ATTENTION.md with the real reason, so that stop is visible."""
    with O3Sandbox(tmp):
        learner.DATA.mkdir(parents=True, exist_ok=True)
        learner.DEPLOYMENT.write_text("", encoding="utf-8")
        learner.FINDINGS.mkdir(parents=True, exist_ok=True)
        planted = "stop right after taking the lock"
        learner.LOCK_POLL_S = 0.2
        results, attention_after = {}, {}
        # the waits are capped well above each holder's own life (1.2 s) so a holder that never exits FAILS the check
        # instead of hanging the suite for 120 min (found when mutant M16 deleted the children's deadline)
        for arm, args, secs_alive, wait_min in (("archive finishes", ["learner.py", "archive"], 1.2, 0.25),
                                                ("a real learner", ["learner.py", "run"], 30, 0.25),
                                                ("archive never finishes", ["learner.py", "archive"], 30, 0.01)):
            learner.ATTENTION.write_text(planted, encoding="utf-8")  # makes loop() return right after the lock
            learner.LOCK_WAIT_MAX_MIN = wait_min
            holder = child(SLEEP_BODY, *args, deadline=secs_alive)
            try:
                time.sleep(0.2)
                learner.LOCK.write_text(str(holder.pid))
                t0 = time.time()
                rc, _ = captured(lambda: learner.loop(single=True))
                results[arm] = (rc, round(time.time() - t0, 1), learner.LOCK.exists())
                attention_after[arm] = learner.ATTENTION.read_text(encoding="utf-8")
            finally:
                holder.kill()
                holder.wait()
            learner.LOCK.unlink(missing_ok=True)
        gave_up = attention_after["archive never finishes"]
        check("R21 FAULT (F8): giving up writes ATTENTION.md with the REAL reason (a manual archive held the lock past "
              "LOCK_WAIT_MAX_MIN; no second learner ran)", gave_up != planted and "did NOT start" in gave_up
              and "`learner.py archive`" in gave_up and "no second learner was running" in gave_up, gave_up[:300])
        check("R21 CONTROL (F8): an immediate refusal by a real learner and a wait that succeeds leave ATTENTION.md "
              "as it was", attention_after["a real learner"] == planted
              and attention_after["archive finishes"] == planted, attention_after)
        rc, secs, lock_left = results["archive finishes"]
        check("R21 CONTROL: a manual `learner.py archive` holds the lock -> the learner WAITS, then takes the lock "
              "(rc 0 here, released on exit)", rc == 0 and secs >= 0.8 and not lock_left
              and "waiting for it to finish" in log_text(), results)
        rc, secs, lock_left = results["a real learner"]
        check("R21 FAULT: a live `learner.py run` holds it -> refused at once with exit 2 (no wait)",
              rc == 2 and secs < 1.0 and lock_left, results)
        rc, secs, lock_left = results["archive never finishes"]
        check("R21 FAULT: the archive outlasts LOCK_WAIT_MAX_MIN -> gives up with a log line, exit 2",
              rc == 2 and 0.5 <= secs < 5 and "gave up waiting" in log_text(), results)
        answers = ["another learner is running (pid 1)", None]  # the holder exits between the refusal and the look
        learner.acquire_lock = lambda: answers.pop(0)
        learner._lock_holder = lambda: None
        check("R21 a holder that exits between the refusal and the look -> the lock is taken (no exit 2)",
              learner.acquire_lock_waiting_for_archive() is None and not answers, answers)


# ------------------------------------------------------------------- O6 the ops ledger, O7 the early archive (S1-3)
#: A stand-in for the batch runner: a BOUNDED child (CHILD_PRELUDE) that copies a prepared batch into place, then
#: lives about 0.4 s so the CPU sampler takes readings while `run_cycle` blocks on it, as it does on a real batch.
FAKE_BATCH_BODY = ("import shutil\nshutil.copytree(ARGS[0], ARGS[1])\nt = time.time()\n"
                   "while alive() and time.time() - t < 0.4:\n    time.sleep(0.02)\n")


def fake_batch_command(template: Path):
    def command(plan: dict, cdir: Path) -> list[str]:
        return [sys.executable, "-c", CHILD_PRELUDE + FAKE_BATCH_BODY, str(os.getpid()), "20", str(template),
                str(cdir / "batch")]
    return command


def ops_rows() -> list[dict]:
    return learner.load_jsonl(learner.OPS_FILE) if learner.OPS_FILE.is_file() else []


def drive_cycle(template: Path, cfg: dict) -> tuple[object, dict]:
    """One whole fake cycle through the REAL `run_cycle` (ops_start, the sampler, finish_cycle, prune, the ops row),
    with only the batch runner replaced. Returns (its result or 'RAISED ...', the newest cycle in state.json)."""
    learner.batch_command = fake_batch_command(template)
    learner.load_config = lambda: cfg
    try:
        ok, _ = captured(lambda: learner.run_cycle(cfg, learner.load_state(), 8))
    except Exception as exc:  # noqa: BLE001 - a raise here IS the failure the ledger must never cause
        ok = f"RAISED {exc!r}"
    cycles = learner.load_state()["cycles"]
    return ok, (cycles[-1] if cycles else {})


def scored(ok: object, newest: dict, tag: str) -> bool:
    """The cycle was scored and recorded: run_cycle returned True, state.json records `tag`, runs.jsonl holds its 4."""
    return ok is True and newest.get("tag") == tag and newest.get("usable") == 3 and \
        len(learner.load_jsonl(learner.RUNS_FILE)) == 4


class FrozenDatetime(__import__("datetime").datetime):
    @classmethod
    def now(cls, tz=None):  # noqa: ANN206
        return cls(2026, 1, 1, 8, 0, 0)


#: The fixed instant O6-1 and O6-6 run at: 8 AM on a 1 January (no DST change is near it in any time zone) in the
#: FUTURE, so every file the test writes is older than it and the archive's quiescence check (QUIET_MINUTES 0) passes.
#: WHY pinned: the gap and started/finished checks parse naive TIME_FMT strings, which are ambiguous in the repeated
#: autumn DST hour; at the real clock this test, which is the learner's restart gate, could fail inside that hour.
PIN_EPOCH = FrozenDatetime(2030, 1, 1, 8, 0, 0).timestamp()


class PinnedClock:
    """Stands in for the learner's `time` module: `time()` starts at PIN_EPOCH and runs at real speed (so `minutes`
    and the sampler's readings stay real); everything else is the real module."""

    def __init__(self) -> None:
        self.m0 = time.monotonic()

    def time(self) -> float:
        return PIN_EPOCH + (time.monotonic() - self.m0)

    def __getattr__(self, name: str):  # noqa: ANN204
        return getattr(time, name)


class StepClock:
    """Stands in for the learner's `time` module: every `monotonic()` call returns 1.0, 2.0, 3.0 ... so a test can put
    a deadline BETWEEN two of the size walk's checks without depending on how fast the disk is."""

    def __init__(self) -> None:
        self.n = 0

    def monotonic(self) -> float:
        self.n += 1
        return float(self.n)

    def __getattr__(self, name: str):  # noqa: ANN204
        return getattr(time, name)


def pin_clock() -> PinnedClock:
    """Pin the learner's clock (`time.time` and `now()`) to PIN_EPOCH; O3Sandbox restores both."""
    clock = PinnedClock()
    learner.time = clock
    learner.now = lambda: __import__("datetime").datetime.fromtimestamp(clock.time()).strftime(learner.TIME_FMT)
    return clock


def at_pin(offset_s: float) -> str:
    """PIN_EPOCH + offset_s as a TIME_FMT string."""
    return __import__("datetime").datetime.fromtimestamp(PIN_EPOCH + offset_s).strftime(learner.TIME_FMT)


def test_o6_o7(tmp: Path) -> None:
    """S1-3. O6: every finished cycle appends one data/ops.jsonl row, and NO failure of that ledger (psutil missing or
    raising, the row builder raising, the file unwritable) ever fails the cycle. O7: under min_free_gb +
    early_prune_margin_gb the loop runs the O3 archive prune with keep 2 BEFORE the disk_guard floor path."""
    import types
    import report
    template = tmp / "template"
    make_batch(template)
    template = template / "batch"
    cfg = dict(learner.DEFAULTS, keep_raw_cycles=1, max_archives_per_prune=3)
    real_psutil = sys.modules["psutil"]
    five_min_ago = (FrozenDatetime.fromtimestamp(time.time() - 300)).strftime(learner.TIME_FMT)

    # O6-1 a real cycle appends one row with every key and sane types (the clock pinned: see PIN_EPOCH) --------------
    with O3Sandbox(tmp / "o6-1"):
        learner.CPU_SAMPLE_S = 0.1
        pin_clock()
        old = dict(make_raw_cycle(tmp, "ai0001"), finished=at_pin(-300))
        O3Sandbox.state([old])
        ok, newest = drive_cycle(template, cfg)
        rows = ops_rows()
        row = rows[-1] if rows else {}
        zsize = (learner.RUNS / "ai0001" / "raw.zip").stat().st_size if \
            (learner.RUNS / "ai0001" / "raw.zip").exists() else -1
        num = (int, float)
        sane = (len(rows) == 1 and tuple(row) == learner.OPS_KEYS and row["tag"] == "ai0002"
                and learner._parse_time(row["started"]) <= learner._parse_time(row["finished"])
                and isinstance(row["finished_epoch"], num) and PIN_EPOCH <= row["finished_epoch"] < PIN_EPOCH + 300
                and isinstance(row["minutes"], num) and 0 <= row["minutes"] < 5
                and row["free_gb_start"] == 500.0 and row["free_gb_end"] == 500.0
                and isinstance(row["learner_gb"], num) and row["learner_gb"] >= 0
                and isinstance(row["cpu_avg"], num) and 0 <= row["cpu_avg"] <= 100
                and isinstance(row["consult_seconds"], num) and row["consult_seconds"] >= 0
                and learner._parse_time(row["boot_time"]) < time.time()
                and isinstance(row["gap_minutes"], num) and 4.9 <= row["gap_minutes"] <= 6
                and isinstance(row["archive_seconds"], num) and row["archive_seconds"] >= 0
                and row["ops_error"] is None)
        check("O6-1 a finished cycle appends ONE ops.jsonl row: every key in order, sane types, CPU sampled during the "
              "batch, gap from the previous cycle's finish", scored(ok, newest, "ai0002") and sane, (ok, row))
        check("O6-1 archive_bytes is the size of the raw.zip this boundary's prune wrote",
              zsize > 0 and row.get("archive_bytes") == zsize, (zsize, row.get("archive_bytes")))
        check("O6-1 the row's finished_epoch is what the NEXT cycle's gap reads back (write -> read round trip)",
              row.get("finished_epoch") is not None and learner._prev_finished_epoch("ai0002") == row["finished_epoch"],
              (row.get("finished_epoch"), learner._prev_finished_epoch("ai0002")))

    # O6-2 FAULT: the ledger fails in every way it can -> the cycle is still scored, a row says why ---------------------
    class RaisingPsutil(types.ModuleType):
        def cpu_percent(self, *a):
            raise RuntimeError("simulated: psutil.cpu_percent failed")

        def boot_time(self):
            raise RuntimeError("simulated: psutil.boot_time failed")

    def no_sampler():
        raise RuntimeError("simulated: the sampler cannot start")

    def broken_builder(*a, **k):
        raise RuntimeError("simulated: the row builder failed")

    arms = (("psutil cannot be imported", lambda: sys.modules.__setitem__("psutil", None),
             lambda r: r["cpu_avg"] is None and r["boot_time"] is None
             and r["ops_error"].count("import of psutil halted") == 2 and "cpu_avg: ModuleNotFoundError" in
             r["ops_error"] and "boot_time: ModuleNotFoundError" in r["ops_error"] and r["free_gb_start"] == 500.0
             and r["free_gb_end"] == 500.0),
            ("psutil raises", lambda: sys.modules.__setitem__("psutil", RaisingPsutil("psutil")),
             lambda r: r["cpu_avg"] is None and r["boot_time"] is None and "cpu_percent failed" in r["ops_error"]
             and "boot_time failed" in r["ops_error"] and r["free_gb_end"] == 500.0
             and isinstance(r["learner_gb"], (int, float))),
            ("the sampler cannot start", lambda: setattr(learner, "_CpuSampler", no_sampler),
             lambda r: r["cpu_avg"] is None and "ops_start" in r["ops_error"] and r["free_gb_end"] == 500.0),
            ("the row builder raises", lambda: setattr(learner, "_ops_row", broken_builder),
             lambda r: r["tag"] == "ai0002" and r["minutes"] is None and tuple(r) == learner.OPS_KEYS
             and "could not be built" in r["ops_error"]
             and isinstance(r["finished_epoch"], float) and abs(r["finished_epoch"] - time.time()) < 300),
            ("ops.jsonl cannot be written", lambda: learner.OPS_FILE.mkdir(parents=True),
             None))
    for i, (arm, fault, row_ok) in enumerate(arms):
        with O3Sandbox(tmp / f"o6-2-{i}"):
            learner.CPU_SAMPLE_S = 0.1
            O3Sandbox.state([dict(make_raw_cycle(tmp, "ai0001"), finished=five_min_ago)])
            try:
                fault()
                ok, newest = drive_cycle(template, cfg)
            finally:
                sys.modules["psutil"] = real_psutil
            rows = ops_rows()
            if row_ok is None:  # nowhere to write: the cycle is recorded and the failure logged instead
                good = learner.OPS_FILE.is_dir() and "could not write its data/ops.jsonl row" in log_text()
            else:
                good = len(rows) == 1 and bool(row_ok(rows[0]))
            check(f"O6-2 FAULT ({arm}): the cycle is still scored and recorded, and the ledger says why",
                  scored(ok, newest, "ai0002") and good, (ok, rows[-1] if rows else None))

    # O6-3 CONTROL: what report.write and cycles.jsonl see is byte-identical with and without the ledger ---------------
    plan = {"tag": "ai0005", "lanes": 8, "arms": {"A": {"genome": "g"}}, "proposal_files": []}
    out = {}
    real_report_dt = report.dt
    for arm in ("with ops.jsonl", "without ops.jsonl", "LEAK"):
        with O3Sandbox(tmp / f"o6-3-{arm.replace(' ', '-')}"):
            report.dt = types.SimpleNamespace(datetime=FrozenDatetime)
            learner.now = lambda: "2026-01-01 08:00:00 AM"
            learner.load_config = lambda: cfg
            try:
                st = O3Sandbox.state([])
                shutil.copytree(template, learner.RUNS / "ai0005" / "batch")
                if arm == "without ops.jsonl":
                    learner.write_ops_row = lambda *a, **k: None
                if arm == "LEAK":  # the comparison must SEE a ledger field leaking into cycles.jsonl
                    real_append = learner.append_jsonl
                    learner.append_jsonl = lambda p, rows: real_append(p, [dict(r, cpu_avg=1.0) if p ==
                                                                          learner.CYCLES_FILE else r for r in rows])
                ops = learner.ops_start(st)
                learner.ops_batch_ended(ops)
                captured(lambda: learner.finish_cycle(cfg, st, plan, 0, ops))
                out[arm] = ({n: (learner.FINDINGS / n).read_bytes() for n in ("LATEST.md", "latest.json")},
                            learner.CYCLES_FILE.read_bytes(), learner.OPS_FILE.exists())
            finally:
                report.dt = real_report_dt
    w, wo, leak = out["with ops.jsonl"], out["without ops.jsonl"], out["LEAK"]
    check("O6-3 CONTROL: LATEST.md, latest.json and cycles.jsonl are byte-identical with and without the ledger",
          w[2] and not wo[2] and w[0] == wo[0] and w[1] == wo[1], (w[2], wo[2], w[1][:120], wo[1][:120]))
    check("O6-3 FAULT: a ledger field leaking into cycles.jsonl IS seen by that comparison",
          leak[1] != wo[1] and leak[2], leak[1][:160])
    keys = set(json.loads(w[1].decode("utf-8").splitlines()[-1]))
    check("O6-3 CONTROL: a cycles.jsonl row holds exactly its pre-O6 keys (no ledger field in either arm)",
          keys == {"source", "tag", "finished", "exit", "lanes", "runs", "usable", "arms_label", "code_commit",
                   "pruned"}, sorted(keys))

    # O6-4 learner_gb: exactly the learner's own files, and capped ---------------------------------------------------
    with O3Sandbox(tmp / "o6-4"):
        make_raw_cycle(tmp, "ai0001")
        foreign = learner.PROFILES / "endless-s14-H1-torchic"
        foreign.mkdir(parents=True)
        (foreign / "save.ss1").write_bytes(b"\x02" * 12345)
        ours = sum(p.stat().st_size for root in [learner.RUNS, *learner.PROFILES.glob("endless-ai*")]
                   for p in root.rglob("*") if p.is_file())
        got = learner.learner_bytes()
        check("O6-4 learner_gb counts runs/ and the learner's endless-ai* profiles, never another profile",
              got == ours and ours > 10 * 2 ** 20, (got, ours))
        learner.SIZE_WALK_CAP_S = -1.0  # the walk is already past its cap when it starts
        r = learner._ops_row("ai0009", {"errors": []}, "x", time.time(), 0.0, {"seconds": 0.0, "bytes": 0})
        check("O6-4 FAULT: a size walk past SIZE_WALK_CAP_S gives learner_gb null with the reason, not a hang",
              r["learner_gb"] is None and "learner_gb: TimeoutError" in (r["ops_error"] or ""), r)
        learner.SIZE_WALK_CAP_S = O3_REAL["SIZE_WALK_CAP_S"]
        r = learner._ops_row("ai0009", None, "x", time.time(), 0.0, None)
        check("O6-5 an ADOPTED cycle (its start never measured) gets a row whose ops_error says so",
              r["started"] is None and r["minutes"] is None and r["cpu_avg"] is None
              and (r["ops_error"] or "").startswith("adopted"), r)

        # O6-4b the cap is checked INSIDE one directory too. StepClock: the check before the directory reads 1.0, the
        # first in-directory check (entry SIZE_WALK_CHECK_EVERY = 10) reads 2.0, so a deadline of 1.5 falls between.
        flat = tmp / "o6-4-flat"
        flat.mkdir()
        for k in range(25):
            (flat / f"f{k}.txt").write_bytes(b"x" * 7)
        learner.SIZE_WALK_CHECK_EVERY = 10
        learner.time = StepClock()
        try:
            learner._tree_bytes([flat], 1.5)
            inner = "returned"
        except TimeoutError as exc:
            inner = f"TimeoutError {exc}"
        learner.time = StepClock()
        control = learner._tree_bytes([flat], 10 ** 9)
        check("O6-4b FAULT: a deadline passed while ONE directory is being walked stops the walk (checked every "
              "SIZE_WALK_CHECK_EVERY entries, not only between directories)", "inside one directory" in inner, inner)
        check("O6-4b CONTROL: with the deadline far away the same directory is counted in full", control == 25 * 7,
              control)

    # O6-6 gap_minutes comes from the previous ROW's epoch when that row is the previous cycle's ---------------------
    # Discriminator: the previous cycle's `finished` STRING says 60 min ago and the ops row's EPOCH says 5 min ago, so
    # the two sources give 60.0 and 5.0 in any time zone. (In the repeated DST hour the string can be 60 min off.)
    def gap_with(name: str, ops_text: str | None, as_dir: bool = False) -> object:
        with O3Sandbox(tmp / f"o6-6-{name}"):
            pin_clock()
            st = O3Sandbox.state([{"tag": "ai0001", "finished": at_pin(-3600)}])
            learner.OPS_FILE.parent.mkdir(parents=True, exist_ok=True)
            if as_dir:
                learner.OPS_FILE.mkdir()
            elif ops_text is not None:
                learner.OPS_FILE.write_text(ops_text, encoding="utf-8")
            ops = learner.ops_start(st)
            learner.ops_batch_ended(ops)
            return ops.get("gap_minutes"), ops.get("errors")

    def ops_line(tag: str, epoch: object) -> str:
        return json.dumps({"tag": "ai0000", "finished_epoch": PIN_EPOCH - 99999}) + "\n" + \
            json.dumps({"tag": tag, "finished_epoch": epoch}) + "\n"

    def near(g: object, minutes: float) -> bool:
        """The gap is `minutes` (the pinned clock runs on: allow the few ms ops_start takes) and no gap error was
        recorded. The sampler is stopped at once here, so its own 'no sample was taken' is expected and ignored."""
        return isinstance(g, tuple) and isinstance(g[0], float) and abs(g[0] - minutes) <= 0.2 and \
            not [e for e in g[1] if not e.startswith("cpu_avg:")]

    g = gap_with("epoch", ops_line("ai0001", PIN_EPOCH - 300))
    check("O6-6 the previous cycle's ops row carries finished_epoch -> gap_minutes is from that EPOCH (5.0), not the "
          "string (60.0)", near(g, 5.0), g)
    g = gap_with("other-tag", ops_line("ai0000", PIN_EPOCH - 300))
    check("O6-6 IDENTITY: the last ops row is ANOTHER cycle's -> its epoch is not used; the string gives 60.0",
          near(g, 60.0), g)
    g = gap_with("no-file", None)
    check("O6-6 CONTROL: no ops.jsonl yet (the first row after O6) -> the string gives 60.0, no error", near(g, 60.0),
          g)
    bad = {"null": "null", "text": '"x"', "NaN": "NaN", "bool": "true"}
    got = {k: gap_with(f"bad-{k}", json.dumps({"tag": "ai0001"})[:-1] + f', "finished_epoch": {v}}}\n')
           for k, v in bad.items()}
    got["unreadable"] = gap_with("unreadable", None, as_dir=True)
    got["junk line"] = gap_with("junk", "{not json\n")
    check("O6-6 FAULT: an unusable epoch (null, text, NaN, true) or an unreadable ops.jsonl -> the string, never a crash "
          "or a null gap", all(near(v, 60.0) for v in got.values()), got)

    # O7 the early archive, driven through the REAL loop -------------------------------------------------------------
    def drive_loop(name: str, free: float, margin: object, n: int = 3, held: bool = False, busy: bool = False,
                   fail: bool = False, early_raises: bool = False) -> dict:
        with O3Sandbox(tmp / name, free=free):
            learner._BAD_MARGIN_LOGGED.clear()  # 'logged once' is per process: each arm starts with none logged
            learner.DEPLOYMENT.parent.mkdir(parents=True, exist_ok=True)
            learner.DEPLOYMENT.write_text("", encoding="utf-8")
            cs = [make_raw_cycle(tmp, f"ai{k:04d}") for k in range(1, n + 1)]
            if held:
                cs[0]["held"] = {"reason": "planted by the test", "since": "x"}
            st = O3Sandbox.state(cs)
            st["parser_version"] = scoring.PARSER_VERSION
            learner.save_state(st)
            before = {c["tag"]: raw_view(tmp, c["tag"]) for c in cs}
            whole = tree(learner.RUNS), tree(learner.PROFILES)
            lcfg = dict(learner.DEFAULTS, auto_update=False, lanes=8, keep_raw_cycles=20, min_free_gb=25,
                        early_prune_margin_gb=margin, wait_if_other_bots_running=False)
            learner.load_config = lambda: lcfg
            order: list[tuple] = []
            real_prune, real_guard = learner.prune, learner.disk_guard
            learner.prune = lambda c, s: order.append(("prune", c["keep_raw_cycles"])) or real_prune(c, s)
            learner.disk_guard = lambda c, s: order.append(("guard",)) or real_guard(c, s)
            learner.run_cycle = lambda *a: order.append(("run",)) or True
            if busy:  # an orphaned lane of ai0001 still names it: the cycle is NOT quiet
                learner._cmdlines = lambda: iter([(4242, "python lane.py --profile endless-ai0001-H1-torchic")])
            if fail:
                def failing_copy(zf, src, nm):
                    raise OSError("simulated: the archive cannot be written")
                learner._copy_member = failing_copy
            if early_raises:
                def raising_early(c, s):
                    order.append(("early raised",))
                    raise OSError("simulated: the early archive failed")
                learner.early_archive = raising_early
            try:
                rc, _ = captured(lambda: learner.loop(single=True))
            except Exception as exc:  # noqa: BLE001 - a raise out of loop is a failure the arms must be able to see
                rc = f"RAISED {exc!r}"
            stc = {c["tag"]: c for c in learner.load_state()["cycles"]}
            return {"rc": rc, "order": order, "state": stc, "same": (tree(learner.RUNS), tree(learner.PROFILES)) ==
                    whole, "raw": {t: raw_view(tmp, t) == before[t] for t in before},
                    "restored": {t: (learner.RUNS / t / "raw.zip").exists() and restored(learner.RUNS / t) == before[t]
                                 for t in before}, "log": log_text()}

    r = drive_loop("o7-1", free=38.0, margin=15.0)
    check("O7-1 free 38 GB (min 25 + margin 15): the loop runs the archive prune with keep 2 BEFORE disk_guard, then "
          "the batch", r["rc"] == 0 and r["order"] == [("prune", 2), ("guard",), ("run",)], r["order"])
    check("O7-1 and it ARCHIVES (verified read-back) all but the newest 2; those 2 stay raw",
          r["restored"]["ai0001"] and r["state"]["ai0001"].get("archived")
          and r["raw"]["ai0002"] and r["raw"]["ai0003"] and not r["state"]["ai0002"].get("pruned"), r["state"])
    r = drive_loop("o7-fail", free=38.0, margin=15.0, fail=True)
    check("O7-1 FAULT: archiving fails -> the early prune deletes NOTHING (whole tree byte-identical); the batch "
          "still starts", r["same"] and r["order"] == [("prune", 2), ("guard",), ("run",)]
          and not r["state"]["ai0001"].get("pruned"), r["order"])
    r = drive_loop("o7-60", free=60.0, margin=15.0)
    check("O7 CONTROL: free 60 GB -> no early prune (only disk_guard, then the batch), nothing touched",
          r["order"] == [("guard",), ("run",)] and r["same"], r["order"])
    r = drive_loop("o7-m0", free=38.0, margin=0.0)
    check("O7 FAULT: margin 0 at 38 GB -> no early prune: the margin is what fires it",
          r["order"] == [("guard",), ("run",)] and r["same"], r["order"])
    r = drive_loop("o7-held", free=38.0, margin=15.0, n=4, held=True)
    check("O7 HOLD: a HELD cycle is untouched by the early archive; the next eligible one is archived",
          r["raw"]["ai0001"] and not r["state"]["ai0001"].get("pruned") and r["restored"]["ai0002"]
          and r["raw"]["ai0003"] and r["raw"]["ai0004"], r["state"])
    r = drive_loop("o7-busy", free=38.0, margin=15.0, n=4, busy=True)
    check("O7 QUIESCENCE: a cycle a live process still names is skipped by the early archive (in use); the next is "
          "archived", r["raw"]["ai0001"] and not r["state"]["ai0001"].get("pruned") and r["restored"]["ai0002"]
          and "ai0001: in use" in r["log"], r["state"])

    # O7 an unusable margin, and a failing early archive, can never withhold the disk check or the batch ------------
    # At free 60 GB: the default margin (15) gives a 40 GB threshold, so the guarded parse runs no early archive. An
    # UNGUARDED parse raises on null, a word or a list (order [], no batch: the review's finding) and fires at ANY free
    # space on NaN (order [prune, guard, run]): both differ from [guard, run].
    junk = {}
    for label, m in (("null", None), ("word", "abc"), ("list", [15]), ("NaN", float("nan")), ("inf", float("inf")),
                     ("negative", -30.0), ("bool", True)):
        r = drive_loop(f"o7-bad-{label}", free=60.0, margin=m, n=1)
        junk[label] = (r["rc"], r["order"], r["log"].count("is unusable"))
    check("O7 FAULT: margin null / 'abc' / [15] / NaN / inf / -30 / true at 60 GB -> [guard, run]: the disk check and "
          "the batch still run, no early archive fires, and the bad value is logged ONCE",
          all(v == (0, [("guard",), ("run",)], 1) for v in junk.values()), junk)
    r = drive_loop("o7-bad-38", free=38.0, margin="abc")
    check("O7 an unusable margin means the DEFAULT 15 (not 'no early archive'): 'abc' at 38 GB still archives early",
          r["order"] == [("prune", 2), ("guard",), ("run",)] and r["restored"]["ai0001"], r["order"])
    r = drive_loop("o7-str15", free=38.0, margin="15", n=1)
    check("O7 CONTROL: a numeric string '15' is a usable margin and is NOT logged as unusable",
          r["order"] == [("prune", 2), ("guard",), ("run",)] and "is unusable" not in r["log"], r["order"])
    r = drive_loop("o7-raises", free=38.0, margin=15.0, n=1, early_raises=True)
    check("O7 FAULT: the early archive RAISES -> logged, and the loop still runs disk_guard and the batch (only "
          "disk_guard's own failure may withhold a batch)",
          r["rc"] == 0 and r["order"] == [("early raised",), ("guard",), ("run",)]
          and "early archive FAILED" in r["log"] and "disk check FAILED" not in r["log"], (r["rc"], r["order"]))
    with O3Sandbox(tmp / "o7-once", free=60.0):
        learner._BAD_MARGIN_LOGGED.clear()
        bad_cfg = dict(learner.DEFAULTS, early_prune_margin_gb="abc")
        for _ in range(3):
            learner.early_archive(bad_cfg, {"cycles": []})
        once = log_text().count("is unusable")
    check("O7 the same unusable margin over 3 loop passes is logged ONCE, not every pass", once == 1, once)


# ------------------------------------------------------------------------------------------- O5 (spec S2-2) tests
#: A consult config that passes both caps, so only the novelty gate decides.
O5_CFG = {"consult": {"enabled": True, "max_calls_per_day": 99, "max_waiting_proposals": 99}}
#: 1,000 scored runs: Norman 30 %, the League basket 30 %, the Champion 40 %.
O5_WALLS = (("boss wall: Norman", 300), ("E4 refused: League basket short", 300), ("CHAMPION", 400))
#: The key terms every generated note shares (two KI ids, two walls).
O5_TERMS = "KI-122 and KI-118 at Tate & Liza and Norman"
O5_NOTE_WALLS = ["boss wall: Tate & Liza", "boss wall: Norman", "CHAMPION"]


def o5_latest(top3: tuple = ("ga", "gb", "gc"), walls: tuple = O5_WALLS, scored: int = 1000) -> dict:
    """A findings/latest.json with the fields the digest reads (report.build writes more)."""
    return {"ranked": [{"genome": g} for g in top3], "walls": [list(w) for w in walls], "scored": scored}


def o5_box(root: Path, latest: dict | None = None, prev: dict | None = None, days_ago: float = 1.0) -> Path:
    """A consult folder (maybe_consult's `ai`): data/, inbox/, findings/latest.json from `latest`, and from `prev` the
    state of a last consult that went ahead `days_ago` days ago."""
    for sub in ("data", "inbox", "findings"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    if latest is not None:
        (root / "findings" / "latest.json").write_text(json.dumps(latest), encoding="utf-8")
    if prev is not None:
        consult.write_state(root, consult.digest_of(prev), dt.datetime.now() - dt.timedelta(days=days_ago), "ai0001")
    return root


def o5_consult(box: Path, cfg: dict | None = None, tag: str = "ai0002") -> tuple[str, bool]:
    """maybe_consult with no `claude` installed: (its outcome, whether it REACHED for claude). Reaching it means the
    gate let the consult through (the outcome is then the 'not on PATH' line); a skip never reaches it."""
    reached: list[str] = []
    real = consult.shutil.which
    consult.shutil.which = lambda name: reached.append(name)  # returns None: 'not on PATH'
    try:
        out = consult.maybe_consult(cfg or O5_CFG, box, box, tag)
    finally:
        consult.shutil.which = real
    return out, bool(reached)


def o5_notes(n: int, terms: str = O5_TERMS) -> str:
    """`n` DEVELOPER-NOTES.md entries exactly as the learner writes them in Windows text mode (CRLF, a blank line
    before each heading). Entry 2 holds a '## ' line and an inline quote of a heading, and the last entry a prose
    mention of the repeat format: the MENTION controls, none of which may split an entry or count as a repeat."""
    out = ""
    for i in range(1, n + 1):
        body = f"Note {i}: fix {terms}."
        if i == 2:
            body += "\r\n## A heading inside a note\r\nIt quotes '## 2026-10-01 01:00 AM, after cycle ai0099' inline."
        if i == n:
            body += "\r\nA reader wrote that it was unchanged since 2026-10-01 01:00 AM (5 consults)."
        out += f"\r\n## 2026-10-{i:02d} {i:02d}:00 AM, after cycle ai{i:04d}\r\n\r\n{body}\r\n"
    return out


def o5_put(inbox: Path, name: str, genes: dict, days_old: float) -> bytes:
    """A waiting proposal whose file time is `days_old` days ago; returns its bytes."""
    inbox.mkdir(parents=True, exist_ok=True)
    p = inbox / f"{name}.json"
    p.write_text(json.dumps({"name": name, "why": "test", "genes": genes}), encoding="utf-8")
    t = time.time() - days_old * 86400
    os.utime(p, (t, t))
    return p.read_bytes()


def test_o5(tmp: Path) -> None:
    """S2-2 (backlog O5): the consult's novelty gate, the developer-notes collapse and roll, the inbox expiry, and the
    --probe-context probe (built, never run against the real `claude`)."""
    import types
    base = o5_latest()

    # N1 / N2 an unchanged digest is skipped without reaching Claude; a changed top 3 goes ahead --------------------
    box = o5_box(tmp / "n1", base, prev=base)
    out, reached = o5_consult(box)
    skips = box / "data" / consult.SKIPS_NAME
    check("N1 an unchanged digest skips the consult, logs it in consult_skips.jsonl (not consult_log.jsonl), and never "
          "reaches Claude", out.startswith("consult: skipped, nothing new since") and not reached and skips.is_file()
          and len(skips.read_text(encoding="utf-8").splitlines()) == 1
          and not (box / "data" / consult.LOG_NAME).exists(), (out, reached))
    box = o5_box(tmp / "n2", o5_latest(top3=("ga", "gb", "gz")), prev=base)
    out, reached = o5_consult(box)
    check("N2 FAULT CONTROL: the top 3 changed -> the consult goes ahead (it reaches the 'not on PATH' line, as C4)",
          reached and out.startswith("consult: the `claude` command is not on PATH") and "top 3 changed" in out, out)
    out, reached = o5_consult(o5_box(tmp / "n2b", o5_latest(top3=("gb", "ga", "gc")), prev=base))
    check("N2b a new leader among the same three genomes is news too (the top 3 compare in order)", reached, out)

    # N3 the wall rule and the new-runs rule, each on both sides of its threshold ----------------------------------
    def moved(tenths: int) -> tuple:  # Norman's share up by tenths/10 points and the basket's down by as much
        return (("boss wall: Norman", 300 + tenths), ("E4 refused: League basket short", 300 - tenths),
                ("CHAMPION", 400))
    res = {t: o5_consult(o5_box(tmp / f"n3-{t}", o5_latest(walls=moved(t)), prev=base))[1] for t in (29, 30, 31)}
    check("N3 a wall's share moved 2.9 points -> skip; 3.1 -> go; exactly 3.0 -> go (the threshold is inclusive)",
          res == {29: False, 30: True, 31: True}, res)
    # Norman 19 of 60 -> 26 of 75 is exactly 31.67% -> 34.67% (3.0 points), but 2.9999999999999964 in floats; the other
    # two walls move 0.3 and 2.7 points (found by a brute-force search over small tables)
    before = o5_latest(walls=(("boss wall: Norman", 19), ("x", 1), ("y", 40)), scored=60)
    after = o5_latest(walls=(("boss wall: Norman", 26), ("x", 1), ("y", 48)), scored=60)
    gap = consult.digest_of(after)["walls"]["boss wall: Norman"] - consult.digest_of(before)["walls"]["boss wall: Norman"]
    out_eps = o5_consult(o5_box(tmp / "n3-eps", after, prev=before))[1]
    check("N3c a move of exactly 3.0 points that floats compute a hair under still goes ahead (EPS)",
          gap < 3.0 and abs(gap - 3.0) < 1e-9 and out_eps, (gap, out_eps))
    res = {m: o5_consult(o5_box(tmp / f"n3b-{m}", o5_latest(scored=1000 + m), prev=base))[1] for m in (149, 150)}
    check("N3b 149 new scored runs -> skip; 150 -> go (new_runs, both sides)", res == {149: False, 150: True}, res)

    # N4 the weekly force, both sides ----------------------------------------------------------------------------------
    res = {d: o5_consult(o5_box(tmp / f"n4-{d}", base, prev=base, days_ago=d))[1] for d in (6, 8)}
    check("N4 forced_days 7: the last consult 8 days ago -> go; 6 days ago -> skip", res == {6: False, 8: True}, res)

    # N5 skips never use up the daily cap --------------------------------------------------------------------------
    box = o5_box(tmp / "n5", base, prev=base)
    cap1 = {"consult": dict(O5_CFG["consult"], max_calls_per_day=1)}
    outs = [o5_consult(box, cap1, tag=f"ai{i:04d}") for i in range(5)]
    log = box / "data" / consult.LOG_NAME
    calls = consult._calls_today(log)
    (box / "findings" / "latest.json").write_text(json.dumps(o5_latest(top3=("gz", "ga", "gb"))), encoding="utf-8")
    after, reached = o5_consult(box, cap1, tag="ai0009")
    check("N5 FAULT: 5 skips use none of the daily cap (_calls_today stays 0, consult_log.jsonl unwritten), so a real "
          "change after them still goes ahead under a cap of 1",
          all(o.startswith("consult: skipped, nothing new") and not r for o, r in outs) and calls == 0
          and not log.exists() and reached, (calls, after))

    # N6 any doubt in the gate fails OPEN ----------------------------------------------------------------------------
    box = o5_box(tmp / "n6a", None, prev=base)
    (box / "findings" / "latest.json").write_text("{not json", encoding="utf-8")
    six = [o5_consult(box)]
    box = o5_box(tmp / "n6b", base)
    (box / "data" / consult.STATE_NAME).write_text('{"digest": 7', encoding="utf-8")
    six.append(o5_consult(box))
    six.append(o5_consult(o5_box(tmp / "n6c", dict(base, scored="1000"), prev=base)))
    six.append(o5_consult(o5_box(tmp / "n6d", base, prev=base),
                          {"consult": dict(O5_CFG["consult"], wall_move_points="abc")}))
    check("N6 FAULT: a corrupt latest.json, a corrupt consult_state.json, a wrong-shape digest and an unusable "
          "threshold each FAIL OPEN: the consult goes ahead and its line says why (N1 is the control)",
          all(r and "failed open" in o for o, r in six), six)

    # N7 roll_notes: newest 5 kept, the rest moved verbatim, never lost ----------------------------------------------
    f = tmp / "n7"
    f.mkdir(parents=True)
    original = o5_notes(7)
    notes, arch = f / consult.NOTES, f / consult.NOTES_ARCHIVE
    notes.write_bytes(original.encode("utf-8"))
    msg = consult.roll_notes(f)
    kept_text, arch_text = notes.read_bytes().decode("utf-8"), arch.read_bytes().decode("utf-8")
    pre, kept = consult.split_notes(kept_text)
    _, moved_entries = consult.split_notes(arch_text)
    check("N7 7 notes -> the newest 5 stay and the 2 oldest move to the archive byte for byte: pre + archive + kept "
          "== the original, CRLF kept, and a '## ' line or a quoted heading inside a note splits nothing",
          len(kept) == 5 and len(moved_entries) == 2 and pre + arch_text + kept_text[len(pre):] == original
          and "after cycle ai0003" in kept[0] and "A heading inside a note" in moved_entries[1]
          and "\r\n" in arch_text, msg)
    again = consult.roll_notes(f)
    check("N7b a second roll moves nothing and changes neither file", again == ""
          and notes.read_bytes().decode("utf-8") == kept_text and arch.read_bytes().decode("utf-8") == arch_text, again)
    f = tmp / "n7c"
    f.mkdir()
    eight = o5_notes(8)
    _, e8 = consult.split_notes(eight)
    (f / consult.NOTES).write_bytes(eight.encode("utf-8"))
    (f / consult.NOTES_ARCHIVE).write_bytes(("older\r\n" + e8[0] + e8[1]).encode("utf-8"))  # a crash after the append
    consult.roll_notes(f)
    arch_c = (f / consult.NOTES_ARCHIVE).read_bytes().decode("utf-8")
    check("N7c after a crash between the archive append and the rewrite, the next roll archives no entry twice",
          arch_c == "older\r\n" + "".join(e8[:3]) and len(consult.split_notes(
              (f / consult.NOTES).read_bytes().decode("utf-8"))[1]) == 5, arch_c.count("## "))
    f = tmp / "n7d"
    f.mkdir()
    (f / consult.NOTES).write_bytes(original.encode("utf-8"))
    ro = f / consult.NOTES_ARCHIVE
    ro.write_bytes(b"")
    os.chmod(ro, stat.S_IREAD)
    try:
        try:
            consult.roll_notes(f)
            raised = False
        except OSError:
            raised = True
    finally:
        os.chmod(ro, stat.S_IREAD | stat.S_IWRITE)
    check("N7d FAULT: an archive that cannot be written raises and leaves DEVELOPER-NOTES.md byte-identical",
          raised and (f / consult.NOTES).read_bytes() == original.encode("utf-8"), raised)
    f = tmp / "n7e"
    f.mkdir()
    (f / consult.NOTES).write_bytes(original.encode("utf-8"))
    late = "\r\n## 2026-10-21 04:06 AM, after cycle ai0999\r\n\r\nLate.\r\n"
    real_read, reads = consult._read_exact, []

    def racing(path: Path) -> str:
        if path.name == consult.NOTES:
            reads.append(path)
            if len(reads) == 2:  # the re-read just before the replace: a consult appends a note first
                with open(path, "ab") as fh:
                    fh.write(late.encode("utf-8"))
        return real_read(path)

    consult._read_exact = racing
    try:
        try:
            consult.roll_notes(f)
            raced = "rolled"
        except RuntimeError as exc:
            raced = str(exc)
    finally:
        consult._read_exact = real_read
    final = (f / consult.NOTES).read_bytes().decode("utf-8")
    check("N7e FAULT: a note appended DURING a roll is never lost: the roll leaves the file as it is",
          "changed while rolling" in raced and final == original + late, raced)
    f = tmp / "n7f"
    f.mkdir()
    (f / consult.NOTES).write_bytes(original.encode("utf-8"))

    def short_archive(path: Path) -> str:  # the archive reads back without the entries just appended
        return "" if path.name == consult.NOTES_ARCHIVE else real_read(path)

    consult._read_exact = short_archive
    try:
        try:
            consult.roll_notes(f)
            verdict = "rolled"
        except RuntimeError as exc:
            verdict = str(exc)
    finally:
        consult._read_exact = real_read
    check("N7f FAULT: when the archive does not read back with the moved entries, the notes file is not rewritten",
          "does not end with the entries to move" in verdict
          and (f / consult.NOTES).read_bytes() == original.encode("utf-8"), verdict)

    # N8 the repeat collapse -----------------------------------------------------------------------------------------
    f = tmp / "n8"
    f.mkdir()
    (f / consult.NOTES).write_bytes(o5_notes(3).encode("utf-8"))
    same = "Still: fix KI-122 first, then KI-118. Tate & Liza and Norman remain the walls."
    when = dt.datetime(2026, 10, 21, 4, 6)
    kinds = [consult.write_note(f, same, when, "ai0010", O5_NOTE_WALLS)]
    line1 = (f / consult.NOTES).read_text(encoding="utf-8").rstrip("\n").rsplit("\n", 1)[-1]
    kinds.append(consult.write_note(f, same, when + dt.timedelta(hours=12), "ai0011", O5_NOTE_WALLS))
    text = (f / consult.NOTES).read_text(encoding="utf-8")
    line2 = text.rstrip("\n").rsplit("\n", 1)[-1]
    check("N8 a note with the same key terms as the last 2 becomes ONE line under 200 characters, counting the consults "
          "since the last distinct note (a prose mention of the format counts nothing)",
          kinds == ["repeat", "repeat"] and len(line1) < 200 and line1.startswith("- 2026-10-21 04:06 AM, after ai0010")
          and "unchanged since 2026-10-03 03:00 AM (1 consult)" in line1 and "(2 consults)" in line2
          and len(consult.split_notes(text)[1]) == 3 and same not in text, (line1, line2))
    kinds = [consult.write_note(f, same + " New: KI-200 is the cause.", when, "ai0012", O5_NOTE_WALLS),
             consult.write_note(f, "Something else: POKEBOT_R25_RARE and the Winona wall.", when, "ai0013",
                                O5_NOTE_WALLS)]
    text = (f / consult.NOTES).read_text(encoding="utf-8")
    check("N8b CONTROL: a note naming a NEW KI- id is written in full (one new id among 4 shared terms leaves the "
          "Jaccard at 0.8), and so is a note about other things", kinds == ["full", "full"]
          and "KI-200 is the cause" in text and "POKEBOT_R25_RARE" in text, kinds)
    g = tmp / "n8c"
    g.mkdir()
    (g / consult.NOTES).write_bytes(o5_notes(1).encode("utf-8"))
    check("N8c with only one earlier note, a note is always written in full",
          consult.write_note(g, same, when, "ai0002", O5_NOTE_WALLS) == "full")

    # I3 / I4 / I5 / I6 the inbox expiry --------------------------------------------------------------------------
    with O3Sandbox(tmp / "i3"):
        exp = learner.INBOX / "expired"
        old = o5_put(learner.INBOX, "old", {"POKEBOT_R25_CAP": "1"}, 4.0)
        o5_put(learner.INBOX, "young", {"POKEBOT_R27_KEYITEMS": "1"}, 2.9)
        exp.mkdir(parents=True)
        (exp / "old.json").write_bytes(b"an earlier expiry of the same name")
        got = [p["name"] for p in learner.read_inbox(3)]
        why = (exp / "old.1.why.txt").read_text(encoding="utf-8") if (exp / "old.1.why.txt").exists() else ""
        check("I3 a proposal 4 days old moves to inbox/expired/ with a .why.txt, its bytes kept (never deleted); one "
              "2.9 days old stays waiting", got == ["young"] and (exp / "old.1.json").read_bytes() == old
              and "4.0 days" in why and not (learner.INBOX / "old.json").exists(), (got, why))
        check("I3b an expiry never overwrites an earlier expired file of the same name",
              (exp / "old.json").read_bytes() == b"an earlier expiry of the same name")
    with O3Sandbox(tmp / "i4"):
        o5_put(learner.INBOX, "dup-old", {"POKEBOT_R25_RARE": "1"}, 1.0)
        o5_put(learner.INBOX, "dup-new", {"POKEBOT_R25_RARE": "1", "POKEBOT_R25_CAP": "0"}, 0.5)  # same genome
        o5_put(learner.INBOX, "other", {"POKEBOT_R20_OPENFENCE": "1"}, 0.2)
        got = [p["name"] for p in learner.read_inbox(3)]
        exp = learner.INBOX / "expired"
        why = (exp / "dup-new.why.txt").read_text(encoding="utf-8") if (exp / "dup-new.why.txt").exists() else ""
        check("I4 a proposal naming the same GENOME as an older waiting one (spelt differently) moves to expired/; the "
              "older one and a distinct genome (CONTROL) stay", got == ["dup-old", "other"]
              and (exp / "dup-new.json").exists() and "dup-old.json" in why, (got, why))
    with O3Sandbox(tmp / "i5"):
        o5_put(learner.INBOX, "two-days", {"POKEBOT_R25_CAP": "1"}, 2.0)
        cfg = dict(learner.DEFAULTS, consult=dict(learner.DEFAULTS["consult"], proposal_ttl_days=1))
        plan = learner.plan_cycle(cfg, {"cycle": 0}, 8)
        check("I5 plan_cycle (so also `learner.py plan`) expires by the CONFIGURED proposal_ttl_days (1: a 2-day-old "
              "proposal goes, and is not planned)", (learner.INBOX / "expired" / "two-days.json").exists()
              and not plan["proposal_files"], plan["proposal_files"])
    with O3Sandbox(tmp / "i6"):
        o5_put(learner.INBOX, "ancient", {"POKEBOT_R25_CAP": "1"}, 30.0)
        got = [[p["name"] for p in learner.read_inbox(bad)] for bad in ("abc", 0, None)]
        check("I6 an unusable proposal_ttl_days ('abc', 0, None) expires nothing by age: a bad value must not empty the "
              "queue", got == [["ancient"]] * 3 and "is unusable" in log_text(), got)

    # N9 every cycle end rolls the notes, and a failed roll never fails the cycle -----------------------------------
    off = dict(learner.DEFAULTS)  # the consult OFF: the roll must not depend on a consult
    plan = {"tag": "ai0001", "lanes": 8, "arms": {}}
    with O3Sandbox(tmp / "n9"):
        learner.FINDINGS.mkdir(parents=True, exist_ok=True)
        (learner.FINDINGS / consult.NOTES).write_bytes(o5_notes(7).encode("utf-8"))
        learner.load_config = lambda: off
        captured(lambda: learner.finish_cycle(off, O3Sandbox.state([]), dict(plan), 0))
        n_kept = len(consult.split_notes((learner.FINDINGS / consult.NOTES).read_text(encoding="utf-8"))[1])
        check("N9 every cycle end rolls DEVELOPER-NOTES.md, with the consult OFF (5 kept, 2 archived)",
              n_kept == 5 and (learner.FINDINGS / consult.NOTES_ARCHIVE).exists(), n_kept)
    with O3Sandbox(tmp / "n9b"):
        learner.FINDINGS.mkdir(parents=True, exist_ok=True)
        (learner.FINDINGS / consult.NOTES).write_bytes(o5_notes(7).encode("utf-8"))
        learner.load_config = lambda: off
        real_roll = consult.roll_notes

        def broken(findings: Path) -> str:
            raise OSError("the disk went away")

        consult.roll_notes = broken
        try:
            try:
                captured(lambda: learner.finish_cycle(off, O3Sandbox.state([]), dict(plan), 0))
                res = "returned"
            except Exception as exc:  # noqa: BLE001 - a raise here IS the failure under test
                res = f"RAISED {exc!r}"
        finally:
            consult.roll_notes = real_roll
        tags = [c["tag"] for c in learner.load_state()["cycles"]]
        check("N9b FAULT: a roll that raises never fails the cycle: finish_cycle returns, the cycle is recorded, its ops "
              "row is written, the log says why and the notes are untouched",
              res == "returned" and tags == ["ai0001"] and len(ops_rows()) == 1
              and "rolling DEVELOPER-NOTES.md failed" in log_text()
              and (learner.FINDINGS / consult.NOTES).read_bytes() == o5_notes(7).encode("utf-8"), (res, tags))

    # N10 the --probe-context probe, with a fake `claude` (it is never run for real here) --------------------------
    calls = []

    def fake_probe(cmd, cwd=None, **kw):  # noqa: ANN001, ANN202
        calls.append((list(cmd), Path(cwd), sorted(os.listdir(cwd))))
        usage = {"input_tokens": 5, "cache_creation_input_tokens": 12000 if len(calls) == 1 else 2000,
                 "cache_read_input_tokens": 100}
        return types.SimpleNamespace(returncode=0, stdout=json.dumps({"usage": usage}), stderr="")

    repo = tmp / "n10repo"
    repo.mkdir()
    rc, printed = captured(lambda: consult.probe_context(repo, {"model": "sonnet"}, run=fake_probe,
                                                         which=lambda name: "claude"))
    ok = len(calls) == 2
    c1, cwd1, _ = calls[0] if ok else ([], None, None)
    c2, cwd2, ls2 = calls[1] if ok else ([], None, None)
    check("N10 the probe runs the consult's own flags twice: from the repo, then from an EMPTY temp dir with --add-dir "
          "<repo>, and prints the input-token difference", ok and rc == 0 and cwd1 == repo and "--add-dir" not in c1
          and cwd2 != repo and ls2 == [] and c2[-2:] == ["--add-dir", str(repo)]
          and all(c[c.index("--setting-sources") + 1] == "user" and c[2] == "Reply OK"
                  and c[c.index("--output-format") + 1] == "json" for c in (c1, c2))
          and "difference (repo minus empty dir): 10000 tokens" in printed, (rc, printed))
    rc_none, _ = captured(lambda: consult.probe_context(repo, {}, run=fake_probe, which=lambda name: None))
    rc_main, _ = captured(lambda: consult.main([]))
    check("N10b FAULT: without claude the probe stops before any call, and `consult.py` without --probe-context runs "
          "nothing", rc_none == 2 and len(calls) == 2 and rc_main == 2, (rc_none, rc_main, len(calls)))

    # N11 only a consult that went through moves the baseline --------------------------------------------------------
    box = o5_box(tmp / "n11", base)
    reply = ("Diagnosis.\n```json\n" + json.dumps({"proposals": [{"name": "p", "why": "w", "genes": {
        "POKEBOT_R25_CAP": "1"}}], "for_the_developer": "Fix KI-122."}) + "\n```\n")
    seen, rc_box = [], [1]

    def fake_claude(cmd, cwd=None, **kw):  # noqa: ANN001, ANN202
        seen.append(Path(cwd))
        return types.SimpleNamespace(stdout=reply, returncode=rc_box[0])

    real_run, real_which = consult.subprocess.run, consult.shutil.which
    consult.subprocess.run, consult.shutil.which = fake_claude, lambda name: "claude"
    try:
        outs = [consult.maybe_consult(O5_CFG, repo, box, "ai0002"), consult.maybe_consult(O5_CFG, repo, box, "ai0003")]
        rc_box[0] = 0
        outs += [consult.maybe_consult(O5_CFG, repo, box, "ai0004"), consult.maybe_consult(O5_CFG, repo, box, "ai0005")]
    finally:
        consult.subprocess.run, consult.shutil.which = real_run, real_which
    rows = learner.load_jsonl(box / "data" / consult.LOG_NAME)
    check("N11 only a call that went through (exit 0) saves the baseline: after exit 1 the next cycle asks again, after "
          "exit 0 an unchanged digest is skipped; 3 calls logged, each run from the repo (the cwd is unchanged)",
          [o.split(",")[0] for o in outs] == ["consult: exit 1", "consult: exit 1", "consult: exit 0",
                                               "consult: skipped"]
          and len(seen) == 3 and all(s == repo for s in seen) and consult._calls_today(box / "data" / consult.LOG_NAME)
          == 3 and [r["exit"] for r in rows] == [1, 1, 0] and rows[0]["why"] == "no previous digest", outs)


def main() -> int:
    global GLOBAL_ROOT
    tmp = Path(tempfile.mkdtemp(prefix="aiagent-test-")).resolve()
    started = time.time()
    try:
        # ISOLATION ON BY DEFAULT: every learner write path points into the temp dir BEFORE the first test runs, and is
        # re-asserted before EVERY test. A test that never patches therefore acts on temp files, never the live clone.
        GLOBAL_ROOT = tmp / "global"
        patch_learner_paths(GLOBAL_ROOT)
        tests = (lambda: test_scoring(tmp / "s"), test_brain, test_effects, lambda: test_preflight(tmp),
                 lambda: test_prune_and_inbox(tmp / "p"), lambda: test_adopt_and_reparse(tmp / "a"),
                 lambda: test_o3_archive(tmp / "o3"), lambda: test_o3_kill(tmp / "o3kill"),
                 lambda: test_o3_reparse(tmp / "o3reparse"), lambda: test_o3_review(tmp / "o3review"),
                 lambda: test_o3_orphan(tmp / "o3orphan"), lambda: test_o3_liveness(tmp / "o3live"),
                 lambda: test_o3_lock(tmp / "o3lock"), lambda: test_o3_profiles(tmp / "o3prof"),
                 lambda: test_children(tmp / "children"), lambda: test_o6_o7(tmp / "o6o7"),
                 lambda: test_o5(tmp / "o5"))
        for i, t in enumerate(tests):
            try:
                assert_isolated(tmp)
            except AssertionError as exc:  # stop: the next test would act on a real path
                check(f"ISOLATION before test {i + 1}: every learner path is inside the test dir", False, repr(exc))
                break
            try:
                t()
            except Exception as exc:  # a crash is a failed check, not a silent pass
                check(f"crash in {getattr(t, '__name__', 'test')} #{i + 1}", False, repr(exc))
        else:
            try:
                assert_isolated(tmp)
            except AssertionError as exc:
                check("ISOLATION after the last test", False, repr(exc))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"  -> {detail}"))
    failed = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"{'ALL PASS' if not failed else f'{failed} FAILED'} ({len(RESULTS)} checks, {time.time() - started:.1f} s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
