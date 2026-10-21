"""Offline gate for the learner: `py -3.12 test_agent.py` (no emulator, about 10 seconds). Exit 0 = all pass.

Each check names what it protects. The FAULT rows prove a guard actually bites: a check that passes on broken
input is decoration.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import random
import shutil
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
    check("C4 FAULT CONTROL: under the cap the consult goes ahead (here it stops at 'no claude on PATH')",
          out == "consult: the `claude` command is not on PATH", out)


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
    lane profile. Returns its state entry, recorded exactly as `finish_cycle` records it."""
    batch = learner.RUNS / tag / "batch"
    (batch / "L01" / "debug-logs").mkdir(parents=True)
    (batch / "L02" / "debug-logs").mkdir(parents=True)
    (batch / "ARMS.json").write_text(json.dumps({"stamp": tag, "lanes": []}), encoding="utf-8")
    (batch / "L01" / "debug-logs" / "a-1.log").write_text(f"{tag} first run\n" * 50, encoding="utf-8")
    (batch / "L01" / "debug-logs" / "big.log").write_bytes(BIG_LOG * (5 * 2 ** 20 // len(BIG_LOG)))
    (batch / "L02" / "stdout.txt").write_bytes(bytes(range(256)) * 40)
    prof = learner.PROFILES / f"endless-{tag}-H1-torchic"
    prof.mkdir(parents=True)
    (prof / "save.ss1").write_bytes(b"\x01" * 1000)
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
    """What the cycle's originals look like, keyed as the zip names them (relative to runs/<tag>/)."""
    return {k[len(tag) + 1:]: v for k, v in tree(learner.RUNS).items() if k.startswith(f"{tag}/batch/")}


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
                 "acquire_lock", "_lock_holder")
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
        got = zip_tree(cdir / "raw.zip") if (cdir / "raw.zip").exists() else {}
        check("R4 prune archives an old cycle: every member's bytes read back from raw.zip equal the originals' sha256",
              len(before1) == 4 and got == before1, (len(before1), sorted(got)))
        check("R4 then its batch/ and lane profile are gone and it is flagged archived + pruned",
              not (cdir / "batch").exists() and not (learner.PROFILES / "endless-ai0001-H1-torchic").exists()
              and c1.get("archived") is True and c1.get("pruned") is True, c1)
        check("R4 the manifest lists the members, sizes and CRCs exactly",
              man.get("n_files") == 4 and learner.verify_archive(cdir / "raw.zip", man.get("members", [])) is None
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
              rc == 0 and out.getvalue().startswith("OK ai0001 4 ") and rec["bad"] == 0 and rec["checked"],
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
              c1.get("archived") and zip_tree(cdir / "raw.zip") == before and not (cdir / "batch").exists())

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
              c1.get("archived") and not (cdir / "batch").exists() and zip_tree(cdir / "raw.zip") == before)

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
              c1.get("archived") and not (d1 / "batch").exists() and zip_tree(d1 / "raw.zip") == before1, c1)
        check("R7 FAULT: a CORRUPT raw.zip + manifest + all originals -> originals kept, zip AND manifest set aside "
              "as .bad.1", raw_view(tmp, "ai0003") == before3 and (d3 / "raw.zip.bad.1").exists()
              and (d3 / "raw.manifest.json.bad.1").exists() and not bad_zip.exists()
              and not (d3 / "raw.manifest.json").exists() and not c3.get("pruned") and not c3.get("held"),
              sorted(p.name for p in d3.iterdir()))
        learner.prune({"keep_raw_cycles": 1, "max_archives_per_prune": 9}, {"cycles": [c1, c3, c2]})
        check("R7 CONTROL: the next prune re-archives the kept originals correctly",
              c3.get("archived") and not (d3 / "batch").exists() and zip_tree(d3 / "raw.zip") == before3)

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
              c1.get("archived") and not (d1 / "batch").exists() and zip_tree(d1 / "raw.zip") == before, c1)

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
              len(tries) == 3 and c1.get("archived") and zip_tree(learner.RUNS / "ai0001" / "raw.zip") == before1,
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
                      tree(learner.RUNS) == before[0] and attempts == [], attempts)
            else:
                check("R10 CONTROL: 50 GB free, a failing archive -> nothing deleted, the batch starts, no ATTENTION",
                      started and after == before and not learner.ATTENTION.exists(), started)
                learner.prune(keep1, st)
                kept = raw_view(tmp, "ai0001") == {k[len("ai0001/"):]: v for k, v in before[0].items()
                                                   if k.startswith("ai0001/batch/")}
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
              not started and c1.get("archived") and zip_tree(learner.RUNS / "ai0001" / "raw.zip") == before1
              and not c2.get("pruned") and learner.ATTENTION.exists(), (started, c1))

    # R11 the manual `archive` command and the learner's lock --------------------------------------------------------
    with O3Sandbox(tmp / "r11"):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        O3Sandbox.state([c1, c2])
        learner.load_config = lambda: dict(learner.DEFAULTS, keep_raw_cycles=1)
        holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "learner.py"])
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
              rc == 0 and zip_tree(learner.RUNS / "ai0001" / "raw.zip") == before1
              and st["cycles"][0].get("archived") and not learner.LOCK.exists(), rc)
        check("R11 CONTROL: and the NEWEST cycle (inside keep_raw_cycles) is untouched",
              len(before2) == 4 and raw_view(tmp, "ai0002") == before2
              and not (learner.RUNS / "ai0002" / "raw.zip").exists() and not st["cycles"][1].get("pruned"))


def test_o3_kill(tmp: Path) -> None:
    """R5b: a REAL kill of a process mid-archive (the backlog's 'kill mid-gzip'). The slowing lives in a TEST-SIDE
    wrapper; the learner has no delay switch."""
    with O3Sandbox(tmp):
        c1, c2 = make_raw_cycle(tmp, "ai0001"), make_raw_cycle(tmp, "ai0002")
        O3Sandbox.state([c1, c2])
        before = raw_view(tmp, "ai0001")
        wrapper = tmp / "r5b_wrapper.py"
        wrapper.write_text(
            "import sys, time\n"
            "from pathlib import Path\n"
            "root, ai, tag = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]\n"
            "sys.path.insert(0, str(ai))\n"
            "import test_agent as T\n"
            "import learner\n"
            "T.patch_learner_paths(root)  # asserts every learner path is inside root BEFORE anything acts\n"
            "real = learner._copy_member\n"
            "def slow(zf, src, name):\n"
            "    time.sleep(1.0)\n"
            "    return real(zf, src, name)\n"
            "learner._copy_member = slow\n"
            "learner.free_gb = lambda: 500.0\n"
            "learner.QUIET_MINUTES = 0  # the fresh test files count as quiet, as in O3Sandbox\n"
            "learner._cmdlines = lambda: iter(())\n"
            "c = next(c for c in learner.load_state()['cycles'] if c['tag'] == tag)\n"
            "learner.archive_cycle(c)\n", encoding="utf-8")
        part, cdir = learner.RUNS / "ai0001" / "raw.zip.part", learner.RUNS / "ai0001"
        proc = subprocess.Popen([sys.executable, str(wrapper), str(tmp), str(AI), "ai0001"],
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
              st["cycles"][0].get("archived") and zip_tree(cdir / "raw.zip") == before and not part.exists()
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
    """name -> every sha256 that name has in the raw files, raw.zip, or ANY set-aside raw.zip.bad.<k>."""
    cdir = learner.RUNS / tag
    out: dict[str, set[str]] = {}
    sources = [raw_view(None, tag)] + [zip_tree(z) for z in sorted(cdir.glob("raw.zip*")) if z.name != "raw.zip.part"
                                       and not z.name.endswith(".tmp")]
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
        members = learner._scan_originals(cdir, files)
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
              and zip_tree(d["ai0003"] / "raw.zip") == before["ai0003"]
              and learner.verify_archive(d["ai0003"] / "raw.zip", learner._read_manifest(
                  d["ai0003"] / "raw.manifest.json")["members"]) is None, cc)
        learner.prune(keep1, {"cycles": [ca, cb, cc, cn]})
        check("R7c CONTROL: the next prune archives the set-aside cycles afresh; the .bad.1 files stay byte-intact",
              ca.get("archived") and cb.get("archived") and zip_tree(d["ai0001"] / "raw.zip") == before["ai0001"]
              and zip_tree(d["ai0002"] / "raw.zip") == before["ai0002"]
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
              c1.get("archived") and zip_tree(d1 / "raw.zip") == before and (d1 / "raw.zip.bad.1").read_bytes() == stale
              and (d1 / "raw.zip.bad.2").read_bytes() == zbad)
        c3 = make_raw_cycle(tmp, "ai0003")  # a manifest WITHOUT its zip (a set-aside interrupted between its renames)
        d3 = learner.RUNS / "ai0003"
        before3, orphan_man = raw_view(tmp, "ai0003"), b'{"members": []}'
        (d3 / "raw.manifest.json").write_bytes(orphan_man)
        learner.prune(keep1, {"cycles": [c3, c2]})
        check("R16 a manifest without its zip is set aside (never overwritten), then the cycle is archived afresh",
              c3.get("archived") and (d3 / "raw.manifest.json.bad.1").read_bytes() == orphan_man
              and zip_tree(d3 / "raw.zip") == before3, sorted(p.name for p in d3.iterdir()))
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
              and zip_tree(learner.RUNS / "ai0005" / "raw.zip") == before5 and not cs["ai0006"].get("pruned"),
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
        learner._write_manifest(d4, "ai0004", learner._scan_originals(d4, learner._originals(d4 / "batch")))
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
            for f in (learner.RUNS / t / "batch").rglob("*"):
                os.utime(f, (old, old))
        lane = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "pokebot.py",
                                 "endless-ai0003-H1-torchic"])
        runner = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "x4_headless.py", "--out",
                                   str(learner.RUNS / "ai0004" / "batch")])
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
              cs[2].get("archived") and cs[3].get("archived") and zip_tree(learner.RUNS / "ai0003" / "raw.zip")
              == before3, [c.get("archived") for c in cs])

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
            got = zip_tree(learner.RUNS / "ai0001" / "raw.zip") if (learner.RUNS / "ai0001" / "raw.zip").exists() else {}
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
            body = ("import sys, time\nfrom pathlib import Path\np, done = sys.argv[1], Path(sys.argv[2])\ni = 0\n" +
                    ("f = open(p, 'ab')\nwhile True:\n    f.write(f'orphan line {i}\\n'.encode()); f.flush()\n"
                     "    done.write_text(str(i)); i += 1; time.sleep(0.1)\n" if mode == "hold" else
                     "while True:\n    with open(p, 'ab') as f:\n        f.write(f'orphan line {i}\\n'.encode())\n"
                     "    done.write_text(str(i)); i += 1; time.sleep(0.05)\n"))
            writer = subprocess.Popen([sys.executable, "-c", body, str(target), str(progress)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
            reader = subprocess.Popen([sys.executable, "-c",
                                       "import sys, time\nfrom pathlib import Path\nf = open(sys.argv[1], 'rb')\n"
                                       "Path(sys.argv[2]).write_text('1')\ntime.sleep(float(sys.argv[3]))\n",
                                       str(learner.STATE_FILE), str(ready), "0.6"])
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
              c3.get("archived") and zip_tree(learner.RUNS / "ai0003" / "raw.zip") == before3, c3)

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


def test_o3_lock(tmp: Path) -> None:
    """F5: a learner starting while a manual `learner.py archive` holds the lock WAITS for it instead of exiting 2
    (run_agent.ps1 treats exit 2 as 'another learner runs' and stops for good)."""
    with O3Sandbox(tmp):
        learner.DATA.mkdir(parents=True, exist_ok=True)
        learner.DEPLOYMENT.write_text("", encoding="utf-8")
        learner.FINDINGS.mkdir(parents=True, exist_ok=True)
        learner.ATTENTION.write_text("stop right after taking the lock", encoding="utf-8")
        learner.LOCK_POLL_S = 0.2
        results = {}
        for arm, args, wait_min in (("archive finishes", ["1.2", "learner.py", "archive"], 120.0),
                                    ("a real learner", ["30", "learner.py", "run"], 120.0),
                                    ("archive never finishes", ["30", "learner.py", "archive"], 0.01)):
            learner.LOCK_WAIT_MAX_MIN = wait_min
            holder = subprocess.Popen([sys.executable, "-c", "import sys, time; time.sleep(float(sys.argv[1]))", *args])
            try:
                time.sleep(0.2)
                learner.LOCK.write_text(str(holder.pid))
                t0 = time.time()
                rc, _ = captured(lambda: learner.loop(single=True))
                results[arm] = (rc, round(time.time() - t0, 1), learner.LOCK.exists())
            finally:
                holder.kill()
                holder.wait()
            learner.LOCK.unlink(missing_ok=True)
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
                 lambda: test_o3_lock(tmp / "o3lock"))
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
