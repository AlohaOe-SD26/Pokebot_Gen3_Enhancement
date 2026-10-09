"""THE SEED SWEEP of AI-player build step 4: how OFTEN each battle goes the way it should, over seeds (a FREQUENCY measurement,
CLAUDE.md rule 9), in-process (`gates/hands_harness.py`, each run in its own process and throwaway emulator, the cartridge's
clock pinned).

    py -3.12 ai_player/gates/rate_step4.py [--plans TYPE,RECOIL,...] [--seeds 10] [--workers 8] [--evidence PATH]
                                           [--first-seed 1]

(The step-4 verifier's second round: "determinism replays aren't replications".) Seeds from 1 are the seeds of the
development sweep the bounds below were registered from, so the graded run REPLAYS it; `--first-seed 101` plays HELD-OUT
seeds no development run played, graded by the same bounds: a replication.

HOW EACH RUN IS GRADED (the step-4 verifier's round: "its docstring claims each run graded by its SECOND-PATH truth ...
in fact TYPE, TYPE-FAULT, RECOIL, RECOIL-FAULT, RIVAL and FAINT are graded from the AI's own told lines"). Every run now
carries TWO second paths, read by the test side, never the AI's eyes or code: the end state (`hands_harness.py truth`:
party by PID, OT ids, `gBattleOutcome`, defeated flags, balls, boxes) and THE GAME'S OWN BATTLE, read after every frame
(`hands_harness.py --battle-log`, `BattleRecorder`: the move each battler chose, `gChosenMoveByBattler`; who hit whom
with what and the HP it cost, `gBattleMons` with `gBattlerAttacker` / `gCurrentMove` / `gBattlerTarget`; every Pokemon
that came onto a battler position, by PID). The AI's told lines are used only to CROSS-CHECK (what it said it chose
against what the game did) and to know WHY; each verdict names the path it rests on. And every run must END BY ITSELF
(`ended_by_itself`: no "stopped" by the frame budget, no harness error, no "stuck:" of the battle), on EVERY plan, unless
the plan is a fault arm whose prediction IS the stuck end (the verifier: "rate_step4 hid it: TYPE-FAULT grades only the
first move, although its docstring says every run must end by itself").

THE PLANS (the fixtures of `gates/live_step4.py`; seeds 1..N, Story unless named):
  TYPE / TYPE-FAULT   `geodude_grovyle.ss1` (a DOUBLE battle: Geodude and Shroomish against Grovyle and Nincada): the GAME's
                      first move chosen by battler 0 (Grovyle) and the species its first hit landed on. PRE-REGISTERED: the
                      real decider Absorb at the Geodude in every seed, the fault (`--fault ignore_types`) in none. NOT a
                      chance argument: the first move is ONE deterministic decision ("Absorb is clearly the best", worth
                      120 against 40) replayed over seeds (CLAUDE.md rule 8); the evidence of the type chart is the A/B.
                      Both plans must end by themselves: the verifier found TYPE-FAULT seed 6 STUCK when the partner
                      Nincada fainted (the replacement sent in the Grovyle already on the field).
  FIELD-FAULT, FIELD-STEP4  the TYPE-FAULT battles (30 seeds each, as TYPE-FAULT: they lose the partner more often than
                      TYPE, which lost none in development) with the replacement's field
                      memory off (`forget_field`), and with the party menu's refusal also ignored (`forget_field,
                      ignore_refusal`: the step-4 code). The DOUBLE-FAINT A/B of the verifier's finding: in every run the
                      partner falls, the real code sends in a Pokemon NOT on the field and the game refuses nothing;
                      FIELD-FAULT is refused ("... is already in battle!"), reads it and sends another; FIELD-STEP4 ends
                      "stuck" there (the bug, reproduced).
  RECOIL / RECOIL-FAULT  `ch13_r119_wedge.ss1` (a real wild battle: Marshtomp L32 74/99 with TAKE DOWN against a 15-HP
                      Poochyena L3): the GAME's first move of battler 0 and the recoil the game charged (its HP drop on its
                      own Take Down). The step-4 verifier: "recoil_penalty charges the fraction of the move's WORTH, not of
                      the HP actually dealt ... On the 15-HP Poochyena the real recoil was 3 HP, while the AI charged 21.5
                      of 76.5 worth". Now the recoil is a quarter of what the hit can take (`recoil_risk`): about 3.75 HP,
                      and Take Down is the move worth most. PRE-REGISTERED: the real decider takes Take Down in at least
                      `RECOIL_REAL_MIN` of 10; the FAULT `uncapped_recoil` (the step-4 rule) in at most `RECOIL_FAULT_MAX`.
                      (A recoil move AVOIDED at low HP is the unit and recorded-look proof: `test_battle.py`
                      RecordedRecoilTests and RecoilTests, against this foe at 3 HP and against a sturdy Taillow at 20 %.)
  WILD                `route101_south.ss1`, 4 battles: at least one wild battle WON with the Mudkip's experience (by PID) up.
  CATCH               the same start, Catcher, 1 battle: CAUGHT (gBattleOutcome 7, a new PID with the player's OT) in at least
                      `CATCH_MIN` of 10; any other run must be a foe knocked out by a weakening hit the decider judged safe.
                      The balls each run spent are reported (truth: the bag before and after).
  TRAINER             `trainer_battle_r116.ss1`: won, Joey's flag set.
  RIVAL               `rival_r103.ss1` (Mudkip 13/23 against May's Treecko): the WIN RATE (no bound: reported).
  FAINT               `faint_r116.ss1`: when the lead faints, the GAME shows the Pokemon the decider named come onto battler 0
                      (by PID), the decider named it "against" the foe it remembered (the verifier: the live party menu has
                      no battle view, so step 4 ranked by level and HP alone), and the battle goes on to its end.
  LEARN               `learn_r116.ss1` (5 seeds): level 15, Bide learned and Growl forgotten in every seed.
  REFUSE / REFUSE-FAULT  `ki17_partymenu_wedge.ss1` (5 seeds; a story-bot save stopped ON the party menu's "SKITTY is
                      already in battle!"): the AI reads the words, presses A on their wait, and the GAME shows the other
                      healthy member (Mightyena) come in; the battle ends by itself. FAULT `ignore_refusal` (the step-4 skill):
                      "the party on screen neither took input nor closed" in every seed.

THE STEP-4 VERIFIER'S SECOND ROUND ("TYPE 'rate across seeds' is not a rate. The first decision is deterministic ... one
counterfactual A/B replayed ... Only one matchup is played live"). TYPE-DECISIONS: EVERY choice of the best move in the
sweep, every turn of every battle of every plan, not only TYPE's first; each choice tells what the type chart changed in it
(`brain/battle.py` TypeSay: the moves about as good WITH the chart, the best with NO types, the moves that attack), and is
paired, in order and per battler position, with the move the GAME shows chosen that turn (`gChosenMoveByBattler` is cleared
at every turn's end, `src/battle_main.c`, so each change of it from none to a move is one turn's choice; a run whose counts
differ is not paired, and said). A choice is DECISIVE when the type-blind best is not about as good with the chart. The
rate: the GAME's choice in the chart's near-best set over the decisive choices, against the chance a type-blind random pick
of an attacking move lands there, and against the type-blind plans (`ignore_types`), classified by the chart they did not
use. PRE-REGISTERED from this round's development sweep (`TYPE_*`: 81 decisive choices of 391 over 95 real runs, all 81 in
the set, a random pick 38 %; the type-blind plans 0 of 843): it is a rate over many turns of a few MATCHUPS (who chose,
against whom, by the game's battlers): the saves give few battles where the type chart turns the strongest move into a poor
one (a Normal move against a Rock, a Ghost or a Steel type), and none was made for this round.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.gates.live_step2 import clean_env, run_json  # noqa: E402
from ai_player.gates.provenance import provenance as tree_provenance  # noqa: E402

GATES = Path(__file__).resolve().parent
HARNESS = GATES / "hands_harness.py"
FIX = GATES / "fixtures"
SAVES = REPO / "tools" / "story-dev" / "saves"
GAME_CLOCK = "2026-10-08T06:00"
MUDKIP = "550a9be6"
#: RECOIL (pre-registered from the development sweep of this round, in-process, seeds 1-10, before the graded run):
#: the real decider took Take Down in 10 of 10 (worth 74.7 after a 1.8 recoil, Water Gun 60: not within 85 %); the
#: step-4 rule (`uncapped_recoil`) in 2 of 10 (54.9 against 60: a draw that favours Water Gun)
RECOIL_REAL_MIN = 9
RECOIL_FAULT_MAX = 5
#: the recoil the game charges for Take Down on the 15-HP Poochyena: a quarter of the 15 HP the hit takes, rounded down
RECOIL_GAME_HP = 3
#: CATCH: caught in at least this many of 10 (pre-registered after the first sweep found seed 9's Wurmple knocked out by the
#: weakening Tackle the decider judged safe at 48-56 % of its HP: a critical hit; a person loses that catch too)
CATCH_MIN = 8
#: The party menu's refusal at the start of `ki17_partymenu_wedge.ss1` and the healthy member that can go in.
KI17_REFUSED, KI17_ONLY = "Skitty", "Mightyena"
#: (the step-4 verifier's round) TYPE-DECISIONS, PRE-REGISTERED from this round's development sweep (the docstring): at
#: least this many DECISIVE choices over the real plans, the game's choice in the chart's near-best set at least this
#: often and this far over a type-blind random pick, and the type-blind plans in that set at most this often
TYPE_DECISIVE_MIN = 30
TYPE_MATCHUPS_MIN = 3
TYPE_NEAR_MIN = 0.90
TYPE_OVER_CHANCE = 0.30
TYPE_BLIND_MAX = 0.35
PLANS: dict[str, dict] = {
    "TYPE": {"state": FIX / "geodude_grovyle.ss1", "frames": 30000, "args": []},
    # (the step-4 verifier's round) 30 seeds: the partner falls in few of them (seed 6 of the first 10), and each such seed
    # is a case of the DOUBLE-FAINT A/B
    "TYPE-FAULT": {"state": FIX / "geodude_grovyle.ss1", "frames": 30000, "args": ["--fault", "ignore_types"], "seeds": 30},
    "FIELD-FAULT": {"state": FIX / "geodude_grovyle.ss1", "frames": 30000, "args": ["--fault", "ignore_types,forget_field"],
                    "seeds": 30},
    "FIELD-STEP4": {"state": FIX / "geodude_grovyle.ss1", "frames": 30000,
                    "args": ["--fault", "ignore_types,forget_field,ignore_refusal"], "seeds": 30},
    "RECOIL": {"state": SAVES / "ch13_r119_wedge.ss1", "frames": 8000, "args": []},
    "RECOIL-FAULT": {"state": SAVES / "ch13_r119_wedge.ss1", "frames": 8000, "args": ["--fault", "uncapped_recoil"]},
    "WILD": {"state": FIX / "route101_south.ss1", "frames": 40000, "args": [], "battles": 4},
    "CATCH": {"state": FIX / "route101_south.ss1", "frames": 20000, "args": [], "personality": "Catcher"},
    "TRAINER": {"state": FIX / "trainer_battle_r116.ss1", "frames": 12000, "args": []},
    "RIVAL": {"state": FIX / "rival_r103.ss1", "frames": 12000, "args": []},
    "FAINT": {"state": FIX / "faint_r116.ss1", "frames": 20000, "args": []},
    "LEARN": {"state": FIX / "learn_r116.ss1", "frames": 12000, "args": [], "seeds": 5},
    "REFUSE": {"state": SAVES / "ki17_partymenu_wedge.ss1", "frames": 30000, "args": [], "seeds": 5},
    "REFUSE-FAULT": {"state": SAVES / "ki17_partymenu_wedge.ss1", "frames": 3000, "args": ["--fault", "ignore_refusal"],
                     "seeds": 5},
}
#: The plans whose PREDICTION is a stuck end (the fault reproduces the bug): `ended_by_itself` is not asked of them.
STUCK_BY_DESIGN = ("FIELD-STEP4", "REFUSE-FAULT")


def run_one(plan: str, seed: int) -> dict:
    spec = PLANS[plan]
    folder = Path(tempfile.mkdtemp(prefix=f"ai_step4_rate_{plan}_"))
    command = [sys.executable, str(HARNESS), "battle", "--state", str(spec["state"]), "--seed", str(seed), "--frames",
               str(spec["frames"]), "--personality", spec.get("personality", "Story"), "--battles", str(spec.get("battles", 1)),
               *spec["args"], "--run-dir", str(folder), "--game-clock", GAME_CLOCK, "--battle-log"]
    try:
        data, raw = run_json(command, "HANDS", clean_env({}), 1500)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    if data is None:
        return {"plan": plan, "seed": seed, "error": raw[-600:]}
    lines = [line for line in data.get("lines") or [] if "battle" in line]
    return {"plan": plan, "seed": seed, "reason": data.get("reason"), "frames": data.get("frames"), "presses": data.get("presses"),
            "lines": lines, "before": data.get("start_truth"), "after": data.get("truth"), "game": data.get("game_battle") or {}}


# ------------------------------------------------------------------ the game's own battle (second path)
def game_first_move(row: dict, battler: int = 0) -> tuple[str, str]:
    """(the move battler `battler` CHOSE first, the species its first hit with that move landed on), by the GAME
    (`gChosenMoveByBattler`, `gBattleMons` HP changes with `gBattlerAttacker` / `gCurrentMove` / `gBattlerTarget`)."""
    chosen = next((c["chosen"][battler] for c in row["game"].get("chosen") or [] if c["chosen"][battler] != "-"), "")
    hit = next((e for e in row["game"].get("events") or [] if e["kind"] == "hp" and e["attacker"] == battler
                and e["move"] == chosen and e["battler"] != battler), None)
    return chosen, hit["species"] if hit else ""


def game_recoil(row: dict, move: str, battler: int = 0) -> list[int]:
    """The HP the game took from battler `battler` on its OWN `move` (the recoil), each time."""
    return [e["hp"][0] - e["hp"][1] for e in row["game"].get("events") or []
            if e["kind"] == "hp" and e["attacker"] == battler and e["battler"] == battler and e["move"] == move]


def game_sent_in(row: dict) -> list[dict]:
    """Every REPLACEMENT by the game: a Pokemon that came onto one of the PLAYER's positions (0, 2) where the one before it
    (a real Pokemon, PID not 0) had fainted (HP 0): a battle's own opening send-outs are not counted. Each with who stood
    on the player's OTHER position at that frame (its PID and HP)."""
    game = row["game"]
    here = {s["battler"]: (s["pid"], s["hp"][0]) for s in game.get("start") or []}
    out = []
    for event in game.get("events") or []:
        if event["kind"] == "in" and event["battler"] in (0, 2):
            before = here.get(event["battler"])
            if before is not None and before[0] != "00000000" and before[1] == 0:
                out.append({**event, "replaced": before[0], "other": here.get(2 - event["battler"])})
        if event["kind"] in ("in", "hp"):
            hp = event["hp"][0] if event["kind"] == "in" else event["hp"][1]
            here[event["battler"]] = (event["pid"], hp)
    return out


def told_names(row: dict) -> list[str]:
    """The species the decider NAMED at each party menu ("who goes in: Taillow L6 ...")."""
    return re.findall(r"who goes in: (.+?) L\d+ ", " ".join(told(row, "who goes in")))


def told(row: dict, pattern: str) -> list[str]:
    return [line for line in row.get("lines") or [] if re.search(pattern, line)]


def told_first_move(row: dict) -> str:
    for line in row.get("lines") or []:
        hit = re.search(r"turn \d+: fight (.+?): ", line)
        if hit:
            return hit.group(1)
    return ""


def outcomes(row: dict) -> list[str]:
    found = re.search(r"battles: \d+ played:? (\[.*?\])", str(row.get("reason")))
    return json.loads(found.group(1).replace("'", '"')) if found else []


def exp(row: dict, key: str, pid: str) -> int | None:
    return next((r[2] for r in (row.get(key) or {}).get("party_exp") or [] if r[0] == pid), None)


def ended_by_itself(row: dict) -> bool:
    """The run ended by itself: a result, no frame-budget stop, no harness error, no stuck battle."""
    reason = str(row.get("reason"))
    return ("error" not in row and not reason.startswith(("stopped", "harness")) and "stuck" not in reason
            and "the battle:" not in reason)


def pid_of(row: dict, species: str) -> str | None:
    return next((r[0] for r in (row.get("before") or {}).get("party_exp") or [] if r[1] == species), None)


# ------------------------------------------------------------------ (the step-4 verifier's round) TYPE-DECISIONS
TOLD_FIGHT = re.compile(r"turn \d+: fight (.+?): .*\(battler (\d)\)(?: \{types: about as good with the chart \[(.*?)\]; with no "
                        r"types the best (.+?); (\d+) that hurt(; DECISIVE)?\})?$")


def told_fights(row: dict) -> dict[int, list[dict]]:
    """Every FIGHT the decider told, per battler position, in order: the move, and what the type chart changed in it
    (`brain/battle.py` TypeSay: the near-best set with the chart, the best with no types, the moves that attack) when it
    was a choice of the best move (a catch's weakening hit is not)."""
    out: dict[int, list[dict]] = {}
    for line in row.get("lines") or []:
        hit = TOLD_FIGHT.search(line)
        if hit is None:
            continue
        near = [n.strip().strip("'") for n in hit.group(3).split(",")] if hit.group(3) else None
        out.setdefault(int(hit.group(2)), []).append(
            {"move": hit.group(1), "near": near, "blind": hit.group(4), "hurting": int(hit.group(5)) if hit.group(5) else None,
             "decisive": bool(hit.group(6))})
    return out


def game_choices(row: dict, battler: int) -> list[tuple[str, str, tuple[str, ...]]]:
    """The move battler `battler` CHOSE each turn, by the GAME: `gChosenMoveByBattler` is cleared to MOVE_NONE at every turn's
    end (`src/battle_main.c`, the turn counter's increment: `gChosenMoveByBattler[i] = MOVE_NONE`), so every change of it
    from none to a move is one turn's choice (the recorder logs every change); with the species on the field at that
    frame (`gBattleMons`: the chooser's, and the foes' at positions 1 and 3): (move, the chooser, the foes)."""
    out, last = [], "-"
    for entry in row["game"].get("chosen") or []:
        now = entry["chosen"][battler]
        if now != "-" and last == "-":
            species = entry.get("species") or ["?"] * 4
            # position 3 of a SINGLE battle is empty: species 0, whose name is "??????????" (the development sweep of
            # 2026-10-09 listed a matchup "('Machop', '??????????')" until this filter)
            out.append((now, species[battler], tuple(s for s in (species[1], species[3]) if s and s.strip("?") and s != "-")))
        last = now
    return out


def type_decisions(rows: list[dict]) -> dict:
    """Over `rows`: every told fight paired, in order and per battler, with the GAME's choice for that turn (a run whose
    counts differ for a battler is not paired: reported); of the pairs whose told TypeSay is DECISIVE (the type-blind best
    not about as good with the chart), how many the GAME shows chose a move of the chart's near-best set, the chance a
    type-blind random pick of an attacking move lands in that set, and the distinct situations (foe species, battles)."""
    pairs, unpaired, disagree = [], [], 0
    for row in rows:
        told_by = told_fights(row)
        for battler, fights in told_by.items():
            game = game_choices(row, battler)
            if len(game) != len(fights):
                unpaired.append((row["plan"], row["seed"], battler, len(fights), len(game)))
                continue
            for fight, (chosen, own, foes) in zip(fights, game):
                disagree += fight["move"].casefold().replace(" ", "") != chosen.casefold().replace(" ", "")
                pairs.append({**fight, "game": chosen, "own": own, "foes": foes, "plan": row["plan"], "seed": row["seed"]})
    decisive = [p for p in pairs if p["decisive"] and p["near"]]
    won = [p for p in decisive if p["game"].casefold().replace(" ", "") in {n.casefold().replace(" ", "") for n in p["near"]}]
    blind = [p for p in decisive if p["game"].casefold().replace(" ", "") == p["blind"].casefold().replace(" ", "")]
    chance = sum(min(1.0, len(p["near"]) / p["hurting"]) for p in decisive if p["hurting"]) / len(decisive) if decisive else 0.0
    per_plan: dict[str, int] = {}
    for p in decisive:
        per_plan[p["plan"]] = per_plan.get(p["plan"], 0) + 1
    return {"pairs": len(pairs), "unpaired": unpaired, "disagree": disagree, "decisive": len(decisive), "near": len(won),
            "blind": len(blind), "chance": chance,
            # a SITUATION: who chose, against whom (the GAME's battlers that frame), and what the chart changed
            "situations": sorted({(p["own"], p["foes"], p["blind"], tuple(p["near"])) for p in decisive}),
            "matchups": sorted({(p["own"], p["foes"]) for p in decisive}), "per_plan": per_plan,
            "runs": sorted({(p["plan"], p["seed"]) for p in decisive})}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plans", default=",".join(PLANS))
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--evidence", type=Path)
    # (the step-4 verifier's second round: "determinism replays aren't replications") the graded sweep plays the SAME
    # seeds as the development sweep its bounds came from, so it replays that pass; a sweep from another first seed is a
    # HELD-OUT replication: seeds no development run played, graded by the same pre-registered bounds
    parser.add_argument("--first-seed", type=int, default=1)
    args = parser.parse_args()
    wanted = [p.strip() for p in args.plans.split(",") if p.strip()]
    jobs = [(plan, seed) for plan in wanted
            for seed in range(args.first_seed, args.first_seed + PLANS[plan].get("seeds", args.seeds))]
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        rows = list(pool.map(lambda job: run_one(*job), jobs))
    by: dict[str, list[dict]] = {}
    for row in rows:
        by.setdefault(row["plan"], []).append(row)
    out: list[str] = [f"AI PLAYER BUILD STEP 4 - THE SEED SWEEP (rate_step4.py)", f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                      f"code: {tree_provenance(REPO)}", f"plans {wanted}, {len(jobs)} runs, the cartridge's clock pinned "
                      f"{GAME_CLOCK}, {round(time.monotonic() - started)} s; every run read by the GAME's battle each frame "
                      f"(`--battle-log`) and its end state (`truth`)",
                      f"seeds from {args.first_seed}: " + ("the seeds of the development sweep the bounds came from (this run "
                      "REPLAYS it: a determinism check of those numbers, not another sample)" if args.first_seed == 1 else
                      "HELD OUT (no development run played them): a REPLICATION, graded by the same pre-registered bounds")]
    verdicts: list[tuple[str, bool]] = []

    def say(line: str) -> None:
        out.append(line)
        print(line, flush=True)

    def judge(name: str, ok: bool, text: str) -> None:
        verdicts.append((name, ok))
        say(f"[{'PASS' if ok else 'FAIL'}] {name}: {text}")

    errors = [r for r in rows if "error" in r]
    judge("RUNS", not errors, f"{len(rows) - len(errors)} of {len(rows)} runs gave a result (errors: {[(r['plan'], r['seed']) for r in errors][:4] or 'none'})")
    good = [r for r in rows if "error" not in r]
    unended = [(r["plan"], r["seed"], str(r.get("reason"))[:120]) for r in good
               if r["plan"] not in STUCK_BY_DESIGN and not (ended_by_itself(r) or outcomes(r) == ["lost"])]
    judge("ENDED", not unended, f"every run of every plan but {list(STUCK_BY_DESIGN)} ended by itself (by its result: no "
                                f"stuck battle, no frame-budget stop; a LOST battle counts as ended): "
                                f"{len([r for r in good if r['plan'] not in STUCK_BY_DESIGN]) - len(unended)} of "
                                f"{len([r for r in good if r['plan'] not in STUCK_BY_DESIGN])}; not ended: {unended or 'none'}")
    by = {plan: [r for r in runs if "error" not in r] for plan, runs in by.items()}

    for plan in ("TYPE", "TYPE-FAULT"):
        if plan in by:
            picks = [game_first_move(r) for r in by[plan]]
            said = [told_first_move(r) for r in by[plan]]
            hits = sum(1 for p in picks if p == ("Absorb", "Geodude"))
            agree = all(p[0] == s for p, s in zip(picks, said))
            n = len(picks)
            ended = [ended_by_itself(r) or outcomes(r) == ["lost"] for r in by[plan]]
            path = "BY THE GAME (gChosenMoveByBattler[0], the first hit's target in gBattleMons)"
            if plan == "TYPE":
                judge(plan, hits == n and agree and all(ended),
                      f"{path}: Grovyle's first move Absorb at the Geodude in {hits} of {n} seeds (one decision, 'Absorb is "
                      f"clearly the best', replayed: the type chart's evidence is the A/B with TYPE-FAULT); the told move "
                      f"agrees in every seed: {agree}; every battle ended by itself: {all(ended)} "
                      f"{[(r['seed'], outcomes(r)) for r in by[plan]]}; picks {picks}")
            else:
                judge(plan, hits == 0 and agree and all(ended),
                      f"{path}, FAULT (types ignored): Absorb at the Geodude in {hits} of {n} seeds; the told move agrees: "
                      f"{agree}; every battle ended by itself: {all(ended)} {[(r['seed'], outcomes(r)) for r in by[plan]]}; "
                      f"picks {picks}")
    if "TYPE" in by and "TYPE-FAULT" in by:
        say(f"TYPE A/B (by the game): Absorb at the Geodude REAL {sum(game_first_move(r) == ('Absorb', 'Geodude') for r in by['TYPE'])} "
            f"of {len(by['TYPE'])}, FAULT {sum(game_first_move(r) == ('Absorb', 'Geodude') for r in by['TYPE-FAULT'])} of "
            f"{len(by['TYPE-FAULT'])}")

    # the DOUBLE-FAINT A/B (the verifier's finding): who came onto the field when a partner fell, by the game
    double_plans = [p for p in ("TYPE", "TYPE-FAULT", "FIELD-FAULT", "FIELD-STEP4") if p in by]
    faint_runs: dict[str, list] = {}
    for plan in double_plans:
        rows_ = []
        for r in by[plan]:
            if not told(r, "who goes in"):
                continue  # no Pokemon of the player's fell in this seed
            came = game_sent_in(r)
            rows_.append({"seed": r["seed"], "came": [(e["battler"], e["species"]) for e in came],
                          "beside": [(e["other"] or ("", 0))[0] for e in came], "pids": [e["pid"] for e in came],
                          "named": told_names(r), "refused": len(told(r, r"already in battle")),
                          "ended": ended_by_itself(r) or outcomes(r) == ["lost"], "reason": str(r.get("reason"))[:90]})
        faint_runs[plan] = rows_
    for plan in ("TYPE", "TYPE-FAULT"):
        if plan in faint_runs:
            rows_ = faint_runs[plan]
            ok = all(x["refused"] == 0 and x["ended"] and [s for _, s in x["came"]] == x["named"]
                     and not set(x["pids"]) & set(x["beside"]) for x in rows_)
            judge(f"{plan} DOUBLE-FAINT", ok,
                  f"BY THE GAME (who came onto the player's positions after a faint): a player's Pokemon fell in "
                  f"{len(rows_)} of {len(by[plan])} seeds; in every one the Pokemon the decider NAMED came in (never the one "
                  f"standing beside it), the game refused nothing ('already in battle' never on screen), and the battle "
                  f"ended by itself: {ok} {[(x['seed'], x['named'], x['came'], x['refused']) for x in rows_]}")
    if "FIELD-FAULT" in faint_runs:
        rows_ = faint_runs["FIELD-FAULT"]
        refused = [x for x in rows_ if x["refused"]]
        ok = bool(refused) and all(x["ended"] and x["came"] for x in rows_)
        judge("FIELD-FAULT", ok,
              f"FAULT forget_field (the step-4 replacement), the refusal READ: the game refused the one on the field in "
              f"{len(refused)} seeds ({[x['seed'] for x in refused]}), the AI read the words and the game shows another come "
              f"in, and every battle ended by itself: {all(x['ended'] for x in rows_)} "
              f"{[(x['seed'], x['named'], x['came'], x['refused']) for x in rows_]}")
    if "FIELD-STEP4" in faint_runs:
        rows_ = faint_runs["FIELD-STEP4"]
        stuck = [r for r in by["FIELD-STEP4"] if "no Pokemon could be sent in" in str(r.get("reason"))]
        fault_refused = {x["seed"] for x in faint_runs.get("FIELD-FAULT", []) if x["refused"]}
        ok = bool(stuck) and {r["seed"] for r in stuck} == fault_refused
        judge("FIELD-STEP4", ok,
              f"THE STEP-4 CODE (forget_field + ignore_refusal): 'the battle: no Pokemon could be sent in' in seeds "
              f"{sorted(r['seed'] for r in stuck)}, exactly the seeds FIELD-FAULT was refused in ({sorted(fault_refused)}): "
              f"the verifier's stuck battle reproduced, and each layer of the fix alone ends it")

    for plan in ("RECOIL", "RECOIL-FAULT"):
        if plan in by:
            picks = [game_first_move(r)[0] for r in by[plan]]
            said = [told_first_move(r) for r in by[plan]]
            take = picks.count("Take Down")
            charged = sorted({hp for r in by[plan] for hp in game_recoil(r, "Take Down")})
            agree = picks == said
            n = len(picks)
            if plan == "RECOIL":
                judge(plan, take >= RECOIL_REAL_MIN and agree and set(picks) <= {"Take Down", "Water Gun"}
                      and charged == [RECOIL_GAME_HP],
                      f"BY THE GAME: Marshtomp's first move Take Down in {take} of {n} seeds (bound >= {RECOIL_REAL_MIN}: its "
                      f"recoil is a quarter of the 15 HP the hit can take); the recoil the GAME charged for it {charged} HP "
                      f"(want [{RECOIL_GAME_HP}]); the told move agrees: {agree}; picks {picks}")
            else:
                judge(plan, take <= RECOIL_FAULT_MAX and agree,
                      f"BY THE GAME, FAULT uncapped_recoil (the step-4 rule: the recoil of the whole worth, 21.6 of 76.5): "
                      f"Take Down in {take} of {n} seeds (bound <= {RECOIL_FAULT_MAX}); the told move agrees: {agree}; picks {picks}")
    if "RECOIL" in by and "RECOIL-FAULT" in by:
        say(f"RECOIL A/B (by the game): Take Down REAL {[game_first_move(r)[0] for r in by['RECOIL']].count('Take Down')} of "
            f"{len(by['RECOIL'])}, the step-4 rule {[game_first_move(r)[0] for r in by['RECOIL-FAULT']].count('Take Down')} of "
            f"{len(by['RECOIL-FAULT'])}")
    if "WILD" in by:
        won = [r for r in by["WILD"] if "won" in outcomes(r) and (exp(r, "after", MUDKIP) or 0) > (exp(r, "before", MUDKIP) or 0)
               and ended_by_itself(r)]
        battles = [((r["after"] or {}).get("game_stats") or {}).get("wild_battles", 0)
                   - ((r["before"] or {}).get("game_stats") or {}).get("wild_battles", 0) for r in by["WILD"]]
        judge("WILD", len(won) == len(by["WILD"]),
              f"BY THE TRUTH (the Mudkip's experience by PID, the game's wild-battle count): {len(won)} of {len(by['WILD'])} runs "
              f"won a wild battle by fighting and raised the Mudkip's experience; wild battles per run {battles}; outcomes "
              f"{[(r['seed'], outcomes(r)) for r in by['WILD']]}")
    if "CATCH" in by:
        def new_pids(r: dict) -> list:
            before = {p[0] for p in (r.get("before") or {}).get("party_ot") or []} | {b[0] for b in (r.get("before") or {}).get("boxes") or []}
            after = [(p[0], p[1]) for p in (r.get("after") or {}).get("party_ot") or []] + \
                    [(b[0], b[1]) for b in (r.get("after") or {}).get("boxes") or []]
            return [p for p in after if p[0] not in before]
        caught = [r for r in by["CATCH"] if (r.get("after") or {}).get("battle_outcome") == 7
                  and [ot for _, ot in new_pids(r)] == [(r.get("after") or {}).get("player_tid")]]
        knocked = [r for r in by["CATCH"] if outcomes(r) == ["won"] and any("weaken it first" in line for line in r["lines"])]
        spent = [sum((r['before'] or {}).get('balls', {}).values()) - sum((r['after'] or {}).get('balls', {}).values())
                 for r in by["CATCH"]]
        judge("CATCH", len(caught) >= CATCH_MIN and len(caught) + len(knocked) == len(by["CATCH"]),
              f"BY THE TRUTH (gBattleOutcome 7, ONE new PID whose OT is the player's, the bag's balls): {len(caught)} of "
              f"{len(by['CATCH'])} caught (bound >= {CATCH_MIN}); the rest knocked out by a weakening hit judged safe: seeds "
              f"{[r['seed'] for r in knocked]}; balls spent per seed {spent} (total {sum(spent)})")
    if "TRAINER" in by:
        won = [r for r in by["TRAINER"] if outcomes(r) == ["won"] and ((r.get("after") or {}).get("trainer_defeated") or {}).get("322")]
        judge("TRAINER", len(won) == len(by["TRAINER"]), f"BY THE TRUTH (Joey's defeated flag 322): {len(won)} of "
                                                         f"{len(by['TRAINER'])} won")
    if "RIVAL" in by:
        won = [r["seed"] for r in by["RIVAL"] if (r.get("after") or {}).get("battle_outcome") == 1
               and ((r.get("after") or {}).get("trainer_defeated") or {}).get("529")]
        ended = all((r.get("after") or {}).get("battle_outcome") in (1, 2) for r in by["RIVAL"])
        judge("RIVAL", ended, f"BY THE TRUTH (gBattleOutcome, May's flag 529): WIN RATE {len(won)} of {len(by['RIVAL'])} "
                              f"(seeds {won}); every battle played to its end (outcome 1 or 2): {ended} (Mudkip L6 at 13/23 "
                              f"HP against a full-HP Treecko: no bound, reported)")
    if "FAINT" in by:
        rows_ = []
        for r in by["FAINT"]:
            said = told(r, "who goes in")
            entries = [e for e in game_sent_in(r) if e["battler"] == 0]
            named = told_names(r)
            rows_.append({"seed": r["seed"], "said": said, "came": [e["species"] for e in entries], "named": named,
                          "against": all(" against " in s for s in said), "ended": ended_by_itself(r) or outcomes(r) == ["lost"],
                          "outcome": (r.get("after") or {}).get("battle_outcome")})
        fainted = [x for x in rows_ if x["said"]]
        ok = bool(fainted) and all(x["came"] == x["named"] and x["against"] and x["ended"] for x in fainted) \
            and all(x["ended"] for x in rows_)
        judge("FAINT", ok,
              f"BY THE GAME (the Pokemon that came onto battler 0) against the decider's word: the lead fainted in "
              f"{len(fainted)} of {len(rows_)} seeds; in every one the one the decider NAMED came in, named 'against' the "
              f"foe it remembered (the party menu has no battle view), and every battle went on to its end: "
              f"{[(x['seed'], x['named'], x['came'], x['outcome']) for x in fainted]}")
    if "LEARN" in by:
        def learned(r: dict) -> bool:
            moves = next((m[2] for m in (r.get("after") or {}).get("party_moves") or [] if m[0] == MUDKIP), [])
            return "Bide" in moves and "Growl" not in moves
        good_ = [r for r in by["LEARN"] if learned(r)]
        judge("LEARN", len(good_) == len(by["LEARN"]), f"BY THE TRUTH (the Mudkip's moves by PID): {len(good_)} of "
                                                       f"{len(by['LEARN'])} seeds: Bide learned, Growl forgotten")
    if "REFUSE" in by:
        rows_ = []
        for r in by["REFUSE"]:
            only = pid_of(r, KI17_ONLY)
            came = [e for e in game_sent_in(r)]
            rows_.append({"seed": r["seed"], "read": bool(told(r, r"the party says .*already in battle")),
                          "came": [(e["battler"], e["species"]) for e in came], "only": any(e["pid"] == only for e in came),
                          "refused_again": len(told(r, "the game refused")), "ended": ended_by_itself(r) or outcomes(r) == ["lost"],
                          "outcome": (r.get("after") or {}).get("battle_outcome")})
        ok = all(x["read"] and x["only"] and x["ended"] and x["refused_again"] == 0 for x in rows_)
        judge("REFUSE", ok,
              f"BY THE GAME: resumed ON the party menu's '{KI17_REFUSED.upper()} is already in battle!', in every seed the AI "
              f"read the words (A on their wait), {KI17_ONLY} came onto the field by its PID, nothing else was refused, and "
              f"the battle ended by itself: {[(x['seed'], x['came'], x['outcome']) for x in rows_]}")
    if "REFUSE-FAULT" in by:
        stuck = [r["seed"] for r in by["REFUSE-FAULT"] if "neither took input nor closed" in str(r.get("reason"))]
        judge("REFUSE-FAULT", len(stuck) == len(by["REFUSE-FAULT"]),
              f"FAULT ignore_refusal (the step-4 skill): 'the party on screen neither took input nor closed' in {len(stuck)} "
              f"of {len(by['REFUSE-FAULT'])} seeds")
    # (the step-4 verifier's round: "TYPE 'rate across seeds' is not a rate ... one counterfactual A/B replayed") EVERY
    # choice of the best move in the sweep where the type chart was DECISIVE (the type-blind best not about as good with
    # the chart), paired with the move the GAME shows chosen that turn; the type-blind plans the same, classified by the
    # chart the decider did not use
    real_rows = [r for plan, runs in by.items() if not any(f in " ".join(PLANS[plan]["args"]) for f in ("ignore_types",))
                 for r in runs]
    blind_rows = [r for plan, runs in by.items() if "ignore_types" in " ".join(PLANS[plan]["args"]) for r in runs]
    if real_rows:
        real = type_decisions(real_rows)
        blind = type_decisions(blind_rows) if blind_rows else None
        rate = real["near"] / real["decisive"] if real["decisive"] else 0.0
        blind_rate = (blind["near"] / blind["decisive"]) if blind and blind["decisive"] else None
        ok = (real["decisive"] >= TYPE_DECISIVE_MIN and len(real["matchups"]) >= TYPE_MATCHUPS_MIN and rate >= TYPE_NEAR_MIN
              and rate >= real["chance"] + TYPE_OVER_CHANCE
              and real["disagree"] == 0 and (blind_rate is None or blind_rate <= TYPE_BLIND_MAX))
        judge("TYPE-DECISIONS", ok,
              f"BY THE GAME (each turn's gChosenMoveByBattler, paired in order with the decider's told fights; told/game "
              f"disagreements {real['disagree']}; unpaired battlers {real['unpaired'][:6] or 'none'}): of {real['pairs']} "
              f"choices of the best move over {len(real_rows)} runs of the real plans, {real['decisive']} were DECISIVE (the "
              f"type-blind best not about as good with the chart; bound >= {TYPE_DECISIVE_MIN}), in {len(real['runs'])} runs "
              f"(per plan {real['per_plan']}), {len(real['matchups'])} distinct matchups (who chose, against whom, by the GAME's "
              f"battlers: bound >= {TYPE_MATCHUPS_MIN}) {real['matchups']}; the GAME shows a move of the chart's near-best set chosen in "
              f"{real['near']} ({rate:.0%}; bound >= {TYPE_NEAR_MIN:.0%}), the type-blind best in {real['blind']}; a type-blind "
              f"random pick of an attacking move would land in that set {real['chance']:.0%} of the time (bound: at least "
              f"{TYPE_OVER_CHANCE:.0%} over it)"
              + (f"; THE TYPE-BLIND PLANS (`ignore_types`), classified by the chart they did not use: {blind['decisive']} "
                 f"decisive of {blind['pairs']}, the chart's set chosen in {blind['near']} ({blind_rate if blind_rate is None else round(blind_rate, 2)}; "
                 f"bound <= {TYPE_BLIND_MAX:.0%}), the type-blind best in {blind['blind']}" if blind else "")
              + f"; the situations (the type-blind best, the chart's set): {real['situations'][:12]}")
    ok = all(v for _, v in verdicts)
    say(f"OVERALL: {'PASS' if ok else 'FAIL'} ({sum(1 for _, v in verdicts if v)} of {len(verdicts)})")
    if args.evidence is not None:
        args.evidence.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
