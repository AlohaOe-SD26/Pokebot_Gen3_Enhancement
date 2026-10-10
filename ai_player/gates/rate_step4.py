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
                      `RECOIL_REAL_MIN` of 10; the FAULT `uncapped_recoil` (the step-4 rule) as the DRAW it is (round 3,
                      below: within the window of the chance its told worths give, over 30 seeds).
                      (A recoil move AVOIDED at low HP is the unit and recorded-look proof: `test_battle.py`
                      RecordedRecoilTests and RecoilTests, against this foe at 3 HP and against a sturdy Taillow at 20 %.)
  WILD                `route101_south.ss1`, 4 battles: at least one wild battle WON with the Mudkip's experience (by PID) up.
  CATCH               the same start, Catcher, 1 battle: CAUGHT (gBattleOutcome 7, a new PID with the player's OT) at least
                      as often as its development rate's floor (round 3: 20 seeds, `DEV_RATES`); any other run must be a foe
                      knocked out by a weakening hit the decider judged safe.
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

STEP 4.1 (2026-10-09, the step-4 verifier's and adversarial review's findings; every bound below PRE-REGISTERED from this
round's development sweep of the final code, seeds 1-10, before the graded run):
  TYPE SECOND MATCHUP  (finding 8: "the TYPE proof rests on one matchup's A/B") the same TYPE / TYPE-FAULT battles, the
                      OTHER attacker: the Nincada (battler 2) against the Shroomish, LEECH LIFE (Bug x2, STAB: 60) over SCRATCH
                      (40) only by the chart: real 10 of 10, the type-blind fault 0 of 30, by the game (gChosenMoveByBattler[2]).
  OVERKILL / OVERKILL-FAULT  (finding 6) `ch13_r119_wedge.ss1`: every damaging move finishes the 15-HP Poochyena; real:
                      never Take Down (`OVERKILL_REAL_MAX`); FAULT `overkill` (step 4): Take Down (`OVERKILL_FAULT_MIN`).
                      RECOIL / RECOIL-FAULT now play under FAULT `overkill` (the valuation in which Take Down is still worth most),
                      so the recoil cap keeps its A/B.
  SHIFT / SHIFT-FAULT (finding 1) `rival_rustboro.ss1`, Trainer: the shift question judged about the species its words name
                      (the game sends that species out next), YES at the Trainer's switch_willing chance (round 3: its window),
                      and every YES's member onto position 0 by its PID before the next foe; FAULT `shift_fainted`: judged about
                      the foe that had just fainted, every seed.
  HEAL                (finding 3) `heal_r103.ss1`: a Potion used (one fewer by the truth, the HP up at position 0 by the game, its
                      max HP unchanged): correct in EVERY seed that healed, and healing as often as its development rate's floor.
  SWITCH              (finding 3) `switch_joey.ss1`: the decider switches, the Mudkip comes onto position 0 by PID with the
                      Poochyena standing, every seed.
  RUN                 (finding 3) `run_r116.ss1`: gBattleOutcome 4 at least as often as its development rate's floor.
  STATUS              (finding 5) every told fight of every run paired with the game's chosen move. (STEP 4.1 ROUND 2, its
                      verifier: "2 status moves chosen BY CHOICE (bound >= 3) ... SHIFT and SHIFT-FAULT with the same seed
                      ... ONE first-turn decision replayed") NOW A RATE: over the REAL plans only (a fault plan replays its
                      real plan's first turn), every CHANCE the opener rule had (drawn, "an OPENING move", or passed over by
                      the draw, "no opener this time": the decider says both) against the chance each temperament was built
                      with (`OPENER_CHANCE`), within `OPENER_SIGMAS` standard deviations, over at least `OPENER_CHANCES_MIN`
                      chances (the plan OPENER: Rustboro's rival again, 30 seeds of its own, gives the rate its power), each
                      drawn opener shown chosen by the game at a safe HP by the game. "Clearly the best" is reported LIKE FOR
                      LIKE: over the 8 real-decider plans of the step-4 sweep (`STEP4_REAL_PLANS`), beside every plan.
  FIELD-FAULT, FIELD-STEP4 (step 4.1 round 2, the verifier: "both vacuous because the case never occurred" held out) play the
                      seeds where this sweep's TYPE-FAULT had a player's Pokemon fall, plus the anchor seed 6 (live_step4
                      DFAINT's case: a replay, said so): never empty.
  RUN                 (step 4.1 round 2, the verifier: "the gBattleOutcome check never records the value before the run")
                      by the game every frame (`hands_harness.py` BattleRecorder: gBattleOutcome's first value and every
                      change): the battle's own clear to 0, then 4.
  SING / SING-FAULT   (step 4.1 round 2, the verifier's weak proof: "the catch's sleep or paralysis move is never exercised
                      live") `sing_r117.ss1` (`make_step41_fixtures.py --only sing`: a Skitty with SING put first, a wild Oddish
                      the Pokedex has not got), Catcher: Sing TAKEN by the game, the Oddish ASLEEP by the game
                      (gBattleMons[1].status1) before the end, each at least as often as its development rate's floor; FAULT
                      `no_catch_status`: never.
  REFUSED / REFUSED-FAULT  (its weak proof: "Finding 2 has no live arm (no fixture has a Disabled move)")
                      `grind_stall_ppzero.ss1` (a story-bot save in a wild battle: Wailord L61, three moves at 0 PP), the
                      decider made blind to PP (FAULT `ignore_pp`): the GAME refuses each move with none (the code that refuses
                      a Disabled move), at least two different moves out in one turn, the game takes only moves with PP, won;
                      with `forget_unusable` too (step 4): the 150-menu bound, no move taken.
  TYPE-DECISIONS is LABELLED A HANDS CHECK (finding 8): the decider draws only from the chart's near-best set, so the game
                      showing such a move chosen proves the told choice reached the game, not that the chart is right.

STEP 4.1 ROUND 3 (2026-10-09, the step-4.1 verifier's second round: "NEW HELD-OUT SEEDS FAIL rate_step4 (seeds 301-310)
... RECOIL-FAULT ... a weighted draw with p about 0.37. A bound of 5 or fewer fails about 11% of 10-seed samples ...
REFUSED ... a floor of 3 fought seeds fails about 17% of samples ... What fails are fragile pre-registered bounds"; and its
weak proofs): EVERY BOUND ON A COUNT OF A CHANCE EVENT IS SET WHERE A SAMPLE FAILS IT WITH PROBABILITY AT MOST `FALSE_FAIL`
(0.1 %) UNDER A MODEL NAMED BESIDE IT (`floor_for`, `window_for`, `dev_floor`), and the grader prints that probability:
  * a rate the decider's OWN RULE sets is judged by the binomial window of that rule's chance: RECOIL-FAULT (the step-4 rule's
    draw between Take Down and Water Gun, its chance computed from the worths the decider TOLD: `draw_chance`, 30 seeds),
    SHIFT's YES (the Trainer's switch_willing 0.8 over the questions where the switch rule found a better member), the
    REFUSED plans' fought seeds (the Story decider lets a new species go with chance 0.4: 30 seeds each), TYPE INDEPENDENT
    MATCHUP's type-blind draw, STATUS (3.29 standard deviations: a two-sided 0.1 % window);
  * a rate with no rule behind it (the game's dice: a catch, a heal, an escape, a win, a faint, Sing landing) is judged
    by the binomial floor at the 95 % LOWER confidence bound of its rate over every development seed (`DEV_RATES`: seeds
    1.., 101.., 201.., 301.. of this round's code, played before the held-out run from 401);
  * one decision replayed, or a correctness claim about every seed where a case occurred, stays "every seed".
  NEW PLANS: TRAINER-TYPE-FAULT (finding 8: "the 'second matchup' ... is a different battler in the same double battle":
  TYPE INDEPENDENT MATCHUP is another fixture, a single battle, a resistance: Pursuit never with the chart, a draw at 1/2
  type-blind); SHIFT-CARRY / SHIFT-CARRY-FAULT (finding 1: "the PID carried to the party menu cannot fail live":
  `rival_rustboro_hurt.ss1`, where a party menu ranking again by level sends the Poochyena, so the game shows which); OPENER-
  WILD (finding 5: "the opener rate comes almost entirely from one fixture": the Route 116 team's Mudkip with Growl roaming
  wild battles, a second source of chances, counted with the rest). The damage estimate no longer reads the foe's species'
  base stats (`brain/battle.py` STEP 4.1 ROUND 3), so every plan was re-measured: seeds 1.., 101.., 201.., 301.. are the
  development seeds of `DEV_RATES`; the held-out replication was seeds 401.. (`--first-seed 401`). ‼ IT FAILED ONE CHECK,
  TYPE-FAULT DOUBLE-FAINT, BY A GRADER BUG: in seed 422 BOTH of the player's Pokemon fell one after the other and the
  check pooled every send-in's PID against every send-in's neighbour (`not_beside`: now send-in by send-in, with a SELFTEST
  of the three shapes at every run). The AI's code did not change, so seeds 401.. replay identically and are RE-GRADED (said
  so); the HELD-OUT replication of the fixed grader is seeds 501.. (`--first-seed 501`), played by no run before it.

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
from ai_player.gates.provenance import keep_earlier, provenance as tree_provenance  # noqa: E402

GATES = Path(__file__).resolve().parent
HARNESS = GATES / "hands_harness.py"
FIX = GATES / "fixtures"
SAVES = REPO / "tools" / "story-dev" / "saves"
GAME_CLOCK = "2026-10-08T06:00"
MUDKIP = "550a9be6"


# ------------------------------------------------------------------ (step 4.1 ROUND 3) how a bound on a COUNT is set
#: (the step-4.1 verifier's second round: "NEW HELD-OUT SEEDS FAIL ... RECOIL-FAULT: Take Down in 8 of 10 seeds (bound <=
#: 5) ... a weighted draw with p about 0.37. A bound of 5 or fewer fails about 11% of 10-seed samples ... a floor of 3
#: fought seeds fails about 17% of samples ... What fails are fragile pre-registered bounds.") Every bound on a count of a
#: CHANCE event is now set where a sample of the process fails it with probability at most `FALSE_FAIL`, under a model
#: NAMED beside it, and the grader prints that probability:
#:   * a RATE THE DECIDER'S OWN RULE SETS (a temperament's chance, a draw's weights from the told values): the count must
#:     lie in the binomial WINDOW of that chance (two-sided: `FALSE_FAIL` / 2 below and above): the rule itself is the claim;
#:   * a rate with no rule behind it (a catch, a heal, an escape: the game's dice): the binomial FLOOR at the one-sided 95 %
#:     LOWER confidence bound of the rate over EVERY development seed (`DEV_RATES`, Clopper-Pearson), so a process as
#:     poor as the development seeds allow still passes with probability at least 1 - `FALSE_FAIL`;
#:   * what is not chance (one decision replayed, a correctness claim about every seed where a case occurred) stays "every
#:     seed": a failure there is a change of the code, not bad luck.
FALSE_FAIL = 0.001


def binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    from math import comb

    if k < 0:
        return 0.0
    return min(1.0, sum(comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(0, min(k, n) + 1)))


def floor_for(n: int, p: float, tail: float = FALSE_FAIL) -> int:
    """The largest bound k with P(X < k) <= `tail`, X ~ Binomial(n, p)."""
    k = 0
    while k < n and binom_cdf(k, n, p) <= tail:
        k += 1
    return k


def ceiling_for(n: int, p: float, tail: float = FALSE_FAIL) -> int:
    """The smallest bound k with P(X > k) <= `tail`, X ~ Binomial(n, p)."""
    k = n
    while k > 0 and 1.0 - binom_cdf(k - 1, n, p) <= tail:
        k -= 1
    return k


def window_for(n: int, p: float, tail: float = FALSE_FAIL) -> tuple[int, int]:
    """(low, high): the two-sided window of a count X ~ Binomial(n, p), `tail` / 2 outside each side."""
    return floor_for(n, p, tail / 2), ceiling_for(n, p, tail / 2)


def lower_rate(successes: int, trials: int, confidence: float = 0.95) -> float:
    """The one-sided Clopper-Pearson LOWER confidence bound of a rate seen `successes` times in `trials` (the largest p
    with P(X >= successes | trials, p) <= 1 - confidence), by bisection."""
    if successes <= 0:
        return 0.0
    low, high = 0.0, successes / trials
    for _ in range(60):
        mid = (low + high) / 2
        if 1.0 - binom_cdf(successes - 1, trials, mid) <= 1.0 - confidence:
            low = mid
        else:
            high = mid
    return low


def tail_below(count: int, n: int, p: float) -> float:
    """P(X < count): the chance a sample of the model falls under a floor of `count`."""
    return binom_cdf(count - 1, n, p)


#: (round 3) the near-best share each temperament was BUILT with (`brain/battle.py` TEMPERAMENTS), written here as the claim
#: a draw's chance is computed from: a decider that drew otherwise fails the window
NEAR_BEST = {"Story": 0.85, "Catcher": 0.80, "Trainer": 0.90}
#: (round 3) the shift question's YES chance each temperament was built with (`Temperament.switch_willing`)
SWITCH_WILLING = {"Story": 0.3, "Catcher": 0.5, "Trainer": 0.8}
#: (round 3) the chance a Story decider FIGHTS a wild species it has not caught (1 - catch_new 0.6)
STORY_LETS_GO = 0.4


def draw_chance(values: dict[str, float], move: str, near_best: float) -> float:
    """The chance the decider's near-best draw (`brain/battle.py` choose_move: the moves within `near_best` of the best,
    each weighted by its worth over that floor plus 5 % of the best) picks `move`, from the worths it TOLD."""
    if not values or move not in values:
        return 0.0
    best = max(values.values())
    floor = near_best * best
    near = {name: value - floor + 0.05 * best for name, value in values.items() if value >= floor}
    return near.get(move, 0.0) / sum(near.values()) if near else 0.0


TOLD_VALUE = re.compile(r"([A-Z][A-Za-z' -]+?): (-?\d+\.\d) = ")


def told_values(line: str) -> dict[str, float]:
    """The worths a told fight line gives each damaging move ("[Take Down: 54.9 = x1 type ...; Water Gun: 60.0 = ...]")."""
    inside = line[line.find("[") + 1:] if "[" in line else ""
    return {name.strip(): float(value) for name, value in TOLD_VALUE.findall(inside)}


#: RECOIL (pre-registered from the development sweep of this round, in-process, seeds 1-10, before the graded run):
#: the real decider took Take Down in 10 of 10 (worth 74.7 after a 1.8 recoil, Water Gun 60: not within 85 %); the
#: step-4 rule (`uncapped_recoil`) in 2 of 10 (54.9 against 60: a draw that favours Water Gun). (Round 3) the step-4 rule's
#: count is judged as the DRAW it is: within the window of the chance the told worths give (`draw_chance`), over 30 seeds
RECOIL_REAL_MIN = 9
#: the recoil the game charges for Take Down on the 15-HP Poochyena: a quarter of the 15 HP the hit takes, rounded down
RECOIL_GAME_HP = 3
#: (round 3) THE DEVELOPMENT RATES of the counts with no rule behind them (`FALSE_FAIL`): (successes, trials) over EVERY
#: development seed of this round's code (seeds 1.., 101.., 201.., 301..: the step-4.1 sweeps' seeds, all played before
#: the held-out run from 401), PRE-REGISTERED before the held-out run; each floor is the binomial floor at the 95 % lower
#: confidence bound of its rate (`dev_floor`). CATCH: caught (the rest a weakening hit's critical); HEAL: a Potion used and
#: the battle ended by itself; RUN: ran; WILD: a wild battle won with experience gained; TRAINER: Joey won; FAINT_ANY: a
#: seed where the lead fainted (FAINT's correctness needs one); SING_TAKEN, SING_ASLEEP: Sing taken, the Oddish asleep
#: MEASURED 2026-10-09 (the four development sweeps of this round's final decider, in-process, the clock pinned; CATCH and
#: FAINT 20 seeds a sweep, the rest 10): CATCH 18, 18, 19, 19 of 20 (every other a weakening hit that knocked the foe out);
#: FAINT 12, 12, 7, 9 of 20; SING taken 10, 9, 9, 10 of 10, asleep 7, 6, 7, 8; HEAL, RUN, WILD, TRAINER 10 of 10 each
DEV_RATES: dict[str, tuple[int, int]] = {
    "CATCH": (74, 80), "HEAL": (40, 40), "RUN": (40, 40), "WILD": (40, 40), "TRAINER": (40, 40), "FAINT_ANY": (40, 80),
    "SING_TAKEN": (38, 40), "SING_ASLEEP": (28, 40),
}


def dev_floor(name: str, n: int) -> tuple[int, float, float]:
    """(the floor of a count over `n` seeds, the rate it assumes, the chance a sample of that rate falls under it) for the
    development rate `name` (`DEV_RATES`): the binomial floor at its 95 % lower confidence bound."""
    successes, trials = DEV_RATES[name]
    rate = lower_rate(successes, trials)
    floor = floor_for(n, rate)
    return floor, rate, tail_below(floor, n, rate)


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
#: (step 4.1) the pre-registered bounds of the step-4.1 plans (from this round's development sweep, the docstring's STEP 4.1).
#: OVERKILL is one decision replayed (not chance). (Round 3) SHIFT's YES is judged as the temperament's switch_willing
#: chance (`SWITCH_WILLING`, a window), HEAL and RUN by their development rates (`DEV_RATES`)
OVERKILL_REAL_MAX = 0
OVERKILL_FAULT_MIN = 9
#: (step 4.1 ROUND 2, the verifier: "2 status moves chosen BY CHOICE (bound >= 3) ... SHIFT and SHIFT-FAULT with the same
#: seed ... ONE first-turn decision replayed") THE OPENERS AS A RATE, not a count: every chance the rule had (an opener
#: drawn, "an OPENING move", or passed over by the draw, "no opener this time": `brain/battle.py` says both) over the REAL
#: plans only (a FAULT plan replays its real plan's first turn: never counted), and the openers drawn against the chance its
#: temperament gives (`Temperament.opener`): within `OPENER_SIGMAS` standard deviations of the expected count, over at least
#: `OPENER_CHANCES_MIN` chances (the plan OPENER gives the rate its power), each drawn opener at a safe HP by the game.
#: (Round 3) 3.29 standard deviations: a two-sided window a sample falls outside of with probability 0.1 % (`FALSE_FAIL`);
#: the plans that REPLAY another plan's first turn on another fixture (`"replays"`) are not counted either
OPENER_SIGMAS = 3.29
OPENER_CHANCES_MIN = 25
#: (round 3, the verifier: "the opener rate comes almost entirely from one fixture ... the other 12 real plans give 1 chance
#: in all") chances from at least this many FIXTURES with at least `OPENER_SOURCE_CHANCES` each (the development sweeps of
#: this round: Rustboro's rival 51-55 chances, the Route 116 team's wild battles (OPENER-WILD) 50-53, every other fixture
#: under 20)
OPENER_SOURCES = 2
OPENER_SOURCE_CHANCES = 20
#: the chance of an opener each temperament was BUILT with (`brain/battle.py` TEMPERAMENTS, written here as the claim
#: under test: a decider that drew at another rate fails)
OPENER_CHANCE = {"Story": 0.12, "Catcher": 0.20, "Trainer": 0.25}
OPENER_HP_SHARE = 0.7  # `brain/battle.py` OPENER_HP: an opener only at this share of its HP or more
#: the 8 plans with the real decider that the STEP-4 sweep had (its "clearly the best" 307 of 550 was over its 14 plans; the
#: verifier's like-for-like A/B used these 8: HEAD 302 of 367 told fights, 82 %, the step-4.1 tree 267 of 368, 73 %)
STEP4_REAL_PLANS = ("TYPE", "WILD", "CATCH", "TRAINER", "RIVAL", "FAINT", "LEARN", "REFUSE")
#: (step 4.1 round 2, the verifier: "FIELD-FAULT and FIELD-STEP4, both vacuous because the case never occurred" in the
#: held-out seeds) the FIELD plans now play the seeds where THIS sweep's TYPE-FAULT had a player's Pokemon fall (the case
#: they are the A/B of), plus these ANCHOR seeds where the development sweep found the partner fall and the step-4
#: replacement pick the Grovyle on the field (seed 6: live_step4's DFAINT), so the A/B is never empty; the grader says
#: which seeds are anchors (a replay) and which came from this sweep
FIELD_ANCHOR_SEEDS = (6,)
#: the game's battle positions of the second TYPE matchup: the Nincada (battler 2) against the Shroomish
TYPE_SECOND = ("Leech Life", "Shroomish")
#: (round 3, the verifier: "the 'second matchup' ... is a different battler in the same double battle and fixture, not an
#: independent battle") an INDEPENDENT matchup: TRAINER's single battle (`trainer_battle_r116.ss1`, Route 116, Grovyle L16
#: against YOUNGSTER JOEY's Machop L9): with the chart, PURSUIT (Dark, x0.5 on Fighting: 20) is out and QUICK ATTACK (40) is
#: clearly the best; type-blind, Pursuit and Quick Attack are worth 40 each: a draw at 1/2 (`draw_chance` of the told worths)
TYPE_THIRD = ("Pursuit", "Quick Attack")
#: (round 3, the verifier's weak proof: "Finding 1, the PID carried to the party menu, cannot fail live") the hurt-Taillow
#: fixture's PIDs (`make_step41_fixtures.py --only rival_hurt`): the Taillow the question chooses, and the Poochyena a party
#: menu ranking again by level sends
TAILLOW_RUSTBORO, POOCHYENA_RUSTBORO = "a8dbcf1b", "2b19ca91"
PLANS: dict[str, dict] = {
    "TYPE": {"state": FIX / "geodude_grovyle.ss1", "frames": 30000, "args": []},
    # (the step-4 verifier's round) 30 seeds: the partner falls in few of them (seed 6 of the first 10), and each such seed
    # is a case of the DOUBLE-FAINT A/B
    "TYPE-FAULT": {"state": FIX / "geodude_grovyle.ss1", "frames": 30000, "args": ["--fault", "ignore_types"], "seeds": 30},
    # (step 4.1 round 2) the FIELD plans play the seeds where this sweep's TYPE-FAULT had a player's Pokemon fall, and the
    # anchors (`FIELD_ANCHOR_SEEDS`): their "seeds" is not a count (main)
    "FIELD-FAULT": {"state": FIX / "geodude_grovyle.ss1", "frames": 30000, "args": ["--fault", "ignore_types,forget_field"]},
    "FIELD-STEP4": {"state": FIX / "geodude_grovyle.ss1", "frames": 30000,
                    "args": ["--fault", "ignore_types,forget_field,ignore_refusal"]},
    # (step 4.1) the recoil cap's A/B under the OVERKILL fault (the step-4 valuation, in which Take Down is the move worth
    # most against the 15-HP Poochyena): with every move finishing it, the real decider no longer takes Take Down at all
    # (OVERKILL below), so the recoil rules are shown where step 4's valuation still reaches them
    "RECOIL": {"state": SAVES / "ch13_r119_wedge.ss1", "frames": 8000, "args": ["--fault", "overkill"]},
    # (round 3) 30 seeds: the step-4 rule's choice is a DRAW (about 1 in 3 for Take Down), judged by its window
    "RECOIL-FAULT": {"state": SAVES / "ch13_r119_wedge.ss1", "frames": 8000, "args": ["--fault", "overkill,uncapped_recoil"],
                     "seeds": 30},
    # (step 4.1, finding 6) the same battle: every damaging move FINISHES the Poochyena, so the real decider compares them by
    # hit chance and recoil (never Take Down, 85 % and recoil); FAULT `overkill` (step 4): Take Down
    "OVERKILL": {"state": SAVES / "ch13_r119_wedge.ss1", "frames": 8000, "args": []},
    "OVERKILL-FAULT": {"state": SAVES / "ch13_r119_wedge.ss1", "frames": 8000, "args": ["--fault", "overkill"]},
    # (step 4.1, findings 1 and 3) the step-4.1 fixtures (`gates/make_step41_fixtures.py`)
    "SHIFT": {"state": FIX / "rival_rustboro.ss1", "frames": 30000, "args": [], "personality": "Trainer"},
    "SHIFT-FAULT": {"state": FIX / "rival_rustboro.ss1", "frames": 30000, "args": ["--fault", "shift_fainted"],
                    "personality": "Trainer"},
    # (step 4.1 round 2, finding 5) the OPENER's power: Rustboro's rival again (the Marshtomp's first turn against her
    # Wingull is a safe one with Growl), 30 seeds of their own (offset 1000: no seed SHIFT plays), each an independent
    # first-turn draw of the Trainer's opener chance
    "OPENER": {"state": FIX / "rival_rustboro.ss1", "frames": 30000, "args": [], "personality": "Trainer", "seeds": 30,
               "seed_offset": 1000},
    # (round 3, the verifier's weak proof: "the opener rate comes almost entirely from one fixture ... the other 12 real
    # plans give 1 chance in all") a SECOND, independent source of opener chances: the Route 116 team's Mudkip (L13, 37/40,
    # GROWL) roaming Route 116's grass, 3 wild battles a run, 20 seeds: another fixture, lead, temperament (Story) and foes
    "OPENER-WILD": {"state": SAVES / "route116team.ss1", "frames": 40000, "args": [], "battles": 3, "seeds": 20},
    # (round 3, the verifier's weak proof: the carry "cannot fail live" on rival_rustboro.ss1, where the by-level ranking
    # also picks the Taillow) the hurt-Taillow fixture: the carried PID sends the Taillow, a party menu ranking again by
    # level (FAULT `forget_shift`) the Poochyena. Its first turn REPLAYS SHIFT's opener draw (the same seed, the same first
    # draw): not counted in STATUS
    "SHIFT-CARRY": {"state": FIX / "rival_rustboro_hurt.ss1", "frames": 30000, "args": [], "personality": "Trainer",
                    "replays": "SHIFT"},
    "SHIFT-CARRY-FAULT": {"state": FIX / "rival_rustboro_hurt.ss1", "frames": 30000, "args": ["--fault", "forget_shift"],
                          "personality": "Trainer"},
    "HEAL": {"state": FIX / "heal_r103.ss1", "frames": 20000, "args": []},
    "SWITCH": {"state": FIX / "switch_joey.ss1", "frames": 20000, "args": []},
    "RUN": {"state": FIX / "run_r116.ss1", "frames": 12000, "args": []},
    "WILD": {"state": FIX / "route101_south.ss1", "frames": 40000, "args": [], "battles": 4},
    # (round 3) 20 seeds: the catch rate's floor (`dev_floor`) has power at 20 (a catch that failed half the time fails it)
    "CATCH": {"state": FIX / "route101_south.ss1", "frames": 20000, "args": [], "personality": "Catcher", "seeds": 20},
    "TRAINER": {"state": FIX / "trainer_battle_r116.ss1", "frames": 12000, "args": []},
    # (round 3, finding 8's weak proof) the INDEPENDENT type-blind A/B: TRAINER's battle with types ignored, 30 seeds
    "TRAINER-TYPE-FAULT": {"state": FIX / "trainer_battle_r116.ss1", "frames": 12000, "args": ["--fault", "ignore_types"],
                           "seeds": 30},
    "RIVAL": {"state": FIX / "rival_r103.ss1", "frames": 12000, "args": []},
    # (round 3) 20 seeds: FAINT's correctness needs a seed where the lead faints (about half of them), and at 10 seeds the
    # chance of none was above `FALSE_FAIL` at the development rate's lower bound
    "FAINT": {"state": FIX / "faint_r116.ss1", "frames": 20000, "args": [], "seeds": 20},
    "LEARN": {"state": FIX / "learn_r116.ss1", "frames": 12000, "args": [], "seeds": 5},
    "REFUSE": {"state": SAVES / "ki17_partymenu_wedge.ss1", "frames": 30000, "args": [], "seeds": 5},
    "REFUSE-FAULT": {"state": SAVES / "ki17_partymenu_wedge.ss1", "frames": 3000, "args": ["--fault", "ignore_refusal"],
                     "seeds": 5},
    # (step 4.1 round 2, the verifier's weak proofs) a catch helped by SLEEP (the Skitty's Sing on a wild Oddish not caught
    # yet: `make_step41_fixtures.py --only sing`), and its fault (no status move to help a catch: step 4)
    "SING": {"state": FIX / "sing_r117.ss1", "frames": 20000, "args": [], "personality": "Catcher"},
    "SING-FAULT": {"state": FIX / "sing_r117.ss1", "frames": 20000, "args": ["--fault", "no_catch_status"],
                   "personality": "Catcher"},
    # a move the GAME refuses (finding 2 live): the decider blind to PP chooses moves with none (a story-bot save in a wild
    # battle: Wailord L61, Surf, Water Spout and Waterfall at 0 PP, Dive at 10); and the step-4 rule (forget_unusable)
    # (round 3, the verifier: "REFUSED ... in 2 of the 2 seeds where it FOUGHT (bound: every one, at least 3) ... a floor of
    # 3 fought seeds fails about 17% of samples") 30 seeds each: the Story decider FIGHTS the Zubat with its 0.4 chance of
    # letting a new species go, so the fought seeds' floor (`STORY_LETS_GO`) fails by chance at most `FALSE_FAIL`
    "REFUSED": {"state": SAVES / "grind_stall_ppzero.ss1", "frames": 12000, "args": ["--fault", "ignore_pp"], "seeds": 30},
    "REFUSED-FAULT": {"state": SAVES / "grind_stall_ppzero.ss1", "frames": 40000,
                      "args": ["--fault", "ignore_pp,forget_unusable"], "seeds": 30},
}
#: The plans whose PREDICTION is a stuck end (the fault reproduces the bug): `ended_by_itself` is not asked of them.
STUCK_BY_DESIGN = ("FIELD-STEP4", "REFUSE-FAULT", "REFUSED-FAULT")
#: (step 4.1 round 2) SING: Sing TAKEN and the foe ASLEEP before the end (Sing hits 55 % of the time and is tried twice at
#: most; a turn its own HP makes unsafe takes none); FAULT: never either. (Round 3) both floors from `DEV_RATES`.


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


def not_beside(pids: list[str], beside: list[str]) -> bool:
    """(step 4.1 round 3) Every Pokemon the game sent in (`pids`, in order) is NOT the one standing on the player's other
    position AT THAT SEND-IN (`beside`, the same order): compared send-in by send-in, never pooled (the held-out seed 422:
    the Skitty sent in first stood beside the Whismur sent in second)."""
    return all(pid != other for pid, other in zip(pids, beside))


def selftest_not_beside() -> list[str]:
    """(step 4.1 round 3) The double-faint identity check on the shapes it must tell apart (rule 6: a gate is fault-tested):
    seed 422's (two send-ins, the first then standing beside the second): PASS; the step-4 bug (the Grovyle standing at 0
    sent onto 2): FAIL; the round-2 pooled check on seed 422's shape: FAIL (the false alarm it raised)."""
    broken = []
    if not not_beside(["skitty", "whismur"], ["nincada", "skitty"]):
        broken.append("seed 422's shape refused")
    if not_beside(["grovyle"], ["grovyle"]):
        broken.append("the one standing beside accepted")
    pooled = not set(["skitty", "whismur"]) & set(["nincada", "skitty"])
    if pooled:
        broken.append("the round-2 pooled check did not reproduce its false alarm")
    return broken


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
        if "the move grid came back" in line:
            # (step 4.1) the game REFUSED the move just told (`TrySetCantSelectMoveBattleScript`: it never reaches
            # gChosenMoveByBattler); the next told fight is that turn's choice
            where = re.search(r"\(battler (\d)\)", line)
            battler = int(where.group(1)) if where else 0
            if out.get(battler):
                out[battler].pop()
            continue
        hit = TOLD_FIGHT.search(line)
        if hit is None:
            continue
        near = [n.strip().strip("'") for n in hit.group(3).split(",")] if hit.group(3) else None
        out.setdefault(int(hit.group(2)), []).append(
            {"move": hit.group(1), "near": near, "blind": hit.group(4), "hurting": int(hit.group(5)) if hit.group(5) else None,
             "decisive": bool(hit.group(6)),
             # (step 4.1) a status move by choice: an opener, or a catch's sleep or paralysis move
             "status": "an OPENING move" in line or "makes a ball hold better" in line,
             # (step 4.1 round 2) an OPENER drawn (the rate's numerator), apart from a catch's status move
             "opener": "an OPENING move" in line,
             "clearly": "is clearly the best" in line})
    return out


def game_hp_at(row: dict, battler: int, frame: int) -> tuple[int, int] | None:
    """(step 4.1) The (HP, max HP) of the Pokemon at battle position `battler` at `frame`, by the GAME (the recorder's start
    and every HP change or send-in before that frame)."""
    game = row["game"]
    here = next(((s["hp"][0], s["hp"][1]) for s in game.get("start") or [] if s["battler"] == battler), None)
    for event in game.get("events") or []:
        if event["f"] > frame:
            break
        if event["battler"] != battler:
            continue
        if event["kind"] == "in":
            here = (event["hp"][0], event["hp"][1])
        elif event["kind"] == "hp":
            here = (event["hp"][1], event.get("max_hp") or (here[1] if here else 0))
    return here


def grade_step41(by: dict[str, list[dict]], judge, say) -> None:
    """(step 4.1) SHIFT, SHIFT-FAULT, HEAL, SWITCH, RUN and STATUS, each by the GAME (`--battle-log`) or the TRUTH."""
    def pid_named(row: dict, species: str) -> str | None:
        return next((r[0] for r in (row.get("before") or {}).get("party_exp") or [] if r[1] == species), None)

    def ins(row: dict, battler: int) -> list[dict]:
        return [e for e in row["game"].get("events") or [] if e["kind"] == "in" and e["battler"] == battler]

    if "SHIFT" in by:
        rows_, yes = [], 0
        for r in by["SHIFT"]:
            question = next((line for line in told(r, "change POK") if "the question" in line), "")
            named = re.search(r"the words say (\w+) comes next", question)
            # the question is asked after a FOE faints (its HP 0 at position 1) and before the next is sent out: the foe
            # the game sends onto position 1 after that faint, and who came onto position 0 between the two
            faint = next((e["f"] for e in r["game"].get("events") or [] if e["kind"] == "hp" and e["battler"] == 1
                          and e["hp"][1] == 0), None)
            next_foe = next((e for e in ins(r, 1) if faint is not None and e["f"] > faint), None)
            foe_in = [next_foe["species"]] if next_foe else []
            said_yes = "': YES" in question
            sent = told(r, "who goes in: .*decided at the question")
            sent_species = re.findall(r"who goes in: (.+?) L\d+ ", " ".join(sent))
            mine_in = [e for e in ins(r, 0) if faint is not None and e["f"] > faint][:1]
            before_foe = bool(mine_in and next_foe and mine_in[0]["f"] < next_foe["f"])
            ok_named = bool(named) and foe_in == [named.group(1).capitalize()] if named else False
            ok_yes = (not said_yes) or (sent_species and mine_in and mine_in[0]["pid"] == pid_named(r, sent_species[0])
                                         and before_foe)
            yes += said_yes and bool(ok_yes)
            rows_.append({"seed": r["seed"], "named": named.group(1) if named else None, "game_next_foe": foe_in,
                          "yes": said_yes, "sent": sent_species, "game_in": [(e["species"], e["pid"]) for e in mine_in],
                          "before_foe": before_foe, "ok": bool(ok_named and ok_yes),
                          # (round 3) the switch_willing draw happened (the switch rule found a much better member)
                          "drew": "switch_willing" in question})
        # (round 3, the verifier: fragile count bounds) YES is the Trainer's switch_willing chance, drawn once per question
        # where the switch rule found a much better member: the count must lie in that chance's binomial window
        drew = sum(1 for x in rows_ if x["drew"])
        low, high = window_for(drew, SWITCH_WILLING["Trainer"])
        judge("SHIFT", all(x["ok"] for x in rows_) and drew >= 1 and low <= yes <= high,
              f"BY THE GAME (who came onto positions 0 and 1 after the question, by PID): in every seed the question was "
              f"judged about the species its WORDS named and the game then sent that species out, and in every YES the "
              f"member the decider chose at the question came onto position 0 by its PID BEFORE the next foe; YES in {yes} "
              f"of the {drew} questions where the switch rule found a better member, the Trainer's switch_willing "
              f"{SWITCH_WILLING['Trainer']} drawn (window {low}-{high}: a sample of that chance falls outside it with "
              f"probability at most {FALSE_FAIL:.1%}): "
              f"{[(x['seed'], x['named'], x['game_next_foe'], x['yes'], x['sent'], x['game_in'], x['before_foe']) for x in rows_]}")
    # (round 3, the verifier's weak proof: "Finding 1, the PID carried to the party menu, cannot fail live ... the by-level
    # fallback ... also picks the L17 Taillow") the hurt-Taillow fixture, where a party menu ranking again by level sends the
    # POOCHYENA: the carried PID is the only way the Taillow comes in
    for plan, want, other in (("SHIFT-CARRY", TAILLOW_RUSTBORO, POOCHYENA_RUSTBORO),
                              ("SHIFT-CARRY-FAULT", POOCHYENA_RUSTBORO, TAILLOW_RUSTBORO)):
        if plan not in by:
            continue
        rows_ = []
        for r in by[plan]:
            question = next((line for line in told(r, "change POK") if "the question" in line), "")
            faint = next((e["f"] for e in r["game"].get("events") or [] if e["kind"] == "hp" and e["battler"] == 1
                          and e["hp"][1] == 0), None)
            next_foe = next((e for e in ins(r, 1) if faint is not None and e["f"] > faint), None)
            mine_in = [e for e in ins(r, 0) if faint is not None and e["f"] > faint
                       and (next_foe is None or e["f"] < next_foe["f"])][:1]
            named = re.search(r"the words say (\w+) comes next", question)
            rows_.append({"seed": r["seed"], "yes": "': YES" in question, "named": named.group(1) if named else None,
                          "about": bool(named) and next_foe is not None
                          and named.group(1).capitalize() == next_foe["species"],
                          "game_in": [(e["species"], e["pid"]) for e in mine_in],
                          "next": next_foe["species"] if next_foe else None, "ended": ended_by_itself(r)})
        yeses = [x for x in rows_ if x["yes"]]
        ok = (len(yeses) >= 1 and all(x["about"] for x in rows_) and all(x["ended"] for x in rows_)
              and all([pid for _, pid in x["game_in"]] == [want] and x["next"] == "Treecko" for x in yeses))
        judge(plan, ok,
              f"BY THE GAME (who came onto position 0 between the first foe's faint and the next foe's send-out, by PID; the "
              f"Taillow first hurt into the window where the by-level ranking puts it under the Poochyena: "
              f"`rival_rustboro_hurt.ss1`){' FAULT forget_shift (the member chosen at the question NOT carried)' if 'FAULT' in plan else ''}: "
              f"every question judged about the species its words named, the one the game then sent out (the rival "
              f"sometimes switches its Wingull out, so the Treecko falls first): {all(x['about'] for x in rows_)}; in every "
              f"YES ({len(yeses)} of {len(rows_)}, each about the Treecko) the game shows {want} come in (never {other}): "
              f"{[(x['seed'], x['named'], x['yes'], x['game_in'], x['next']) for x in rows_]}; every battle ended by itself: "
              f"{all(x['ended'] for x in rows_)}")
    if "SHIFT-CARRY" in by and "SHIFT-CARRY-FAULT" in by:
        def came(plan: str, pid: str) -> int:
            return sum(1 for r in by[plan] for e in ins(r, 0)[1:2] if e["pid"] == pid)
        say(f"SHIFT-CARRY A/B (by the game, the first Pokemon onto position 0 after the lead): the Taillow ({TAILLOW_RUSTBORO}) "
            f"REAL {came('SHIFT-CARRY', TAILLOW_RUSTBORO)} of {len(by['SHIFT-CARRY'])}, not carried "
            f"{came('SHIFT-CARRY-FAULT', TAILLOW_RUSTBORO)} of {len(by['SHIFT-CARRY-FAULT'])}; the Poochyena ({POOCHYENA_RUSTBORO}) "
            f"REAL {came('SHIFT-CARRY', POOCHYENA_RUSTBORO)}, not carried {came('SHIFT-CARRY-FAULT', POOCHYENA_RUSTBORO)}")
    if "SHIFT-FAULT" in by:
        rows_ = []
        for r in by["SHIFT-FAULT"]:
            question = next((line for line in told(r, "change POK") if "the question" in line), "")
            judged = re.search(r"against (\w+) \(FAULT shift_fainted", question)
            events = r["game"].get("events") or []
            faint = next((e for e in events if e["kind"] == "hp" and e["battler"] == 1 and e["hp"][1] == 0), None)
            next_foe = next((e for e in ins(r, 1) if faint is not None and e["f"] > faint["f"]), None)
            rows_.append({"seed": r["seed"], "judged": judged.group(1) if judged else None,
                          "fainted": faint["species"] if faint else None, "next": next_foe["species"] if next_foe else None})
        stale = [x for x in rows_ if x["judged"] is not None and x["judged"] == x["fainted"] and x["next"] != x["judged"]]
        judge("SHIFT-FAULT", len(stale) == len(rows_),
              f"FAULT shift_fainted (step 4): BY THE GAME the question was judged about the foe that had just FAINTED at "
              f"position 1, not the one the game sent out next, in {len(stale)} of {len(rows_)} seeds (the finding "
              f"reproduced): {[(x['seed'], x['judged'], x['fainted'], x['next']) for x in rows_]}")
    if "SHIFT" in by and "SHIFT-FAULT" in by:
        say(f"SHIFT A/B: YES about the incoming Treecko REAL {sum(1 for r in by['SHIFT'] if any(chr(39) + ': YES' in l for l in told(r, 'change POK')))} "
            f"of {len(by['SHIFT'])}, step 4's answer about the fainted Wingull "
            f"{sum(1 for r in by['SHIFT-FAULT'] if any(chr(39) + ': YES' in l for l in told(r, 'change POK')))} of {len(by['SHIFT-FAULT'])}")
    if "HEAL" in by:
        rows_ = []
        for r in by["HEAL"]:
            heals = len(told(r, r"turn \d+: item Potion"))
            before = ((r.get("before") or {}).get("items") or {}).get("POTION", 0)
            after = ((r.get("after") or {}).get("items") or {}).get("POTION", 0)
            start_max = next((s["hp"][1] for s in r["game"].get("start") or [] if s["battler"] == 0), None)
            rises = [e["hp"] for e in r["game"].get("events") or [] if e["kind"] == "hp" and e["battler"] == 0
                     and e["hp"][1] > e["hp"][0] and e.get("max_hp") == start_max]
            rows_.append({"seed": r["seed"], "heals": heals, "potions": (before, after), "rises": rises,
                          "outcome": (r.get("after") or {}).get("battle_outcome"), "ended": ended_by_itself(r)})
        healed = [x for x in rows_ if x["heals"] >= 1 and x["potions"][0] - x["potions"][1] == x["heals"]
                  and len(x["rises"]) >= x["heals"] and x["ended"]]
        # (round 3) CORRECTNESS in every seed that healed (the count fell by the heals told, the HP rose); the FREQUENCY of a
        # heal by its development rate's floor (`dev_floor`: the battle's dice decide whether the Mudkip gets low)
        wrong = [x for x in rows_ if x["heals"] >= 1 and x not in healed]
        heal_min, rate, chance = dev_floor("HEAL", len(rows_))
        judge("HEAL", len(healed) >= heal_min and not wrong and all(x["ended"] for x in rows_),
              f"BY THE TRUTH (the bag's Potions before and after) and THE GAME (the Mudkip's HP rising at position 0, its max "
              f"HP unchanged: not a level-up): in EVERY seed that healed the count fell by exactly the heals told and the HP "
              f"rose (wrong: {[x['seed'] for x in wrong] or 'none'}); a Potion used in {len(healed)} of {len(rows_)} seeds "
              f"(bound >= {heal_min}: the development rate {DEV_RATES['HEAL'][0]}/{DEV_RATES['HEAL'][1]}, its 95 % lower "
              f"bound {rate:.3f}, falls under it with probability {chance:.2%}); every battle ended by itself: "
              f"{[(x['seed'], x['heals'], x['potions'], x['rises'], x['outcome']) for x in rows_]}")
    if "SWITCH" in by:
        rows_ = []
        for r in by["SWITCH"]:
            said = told(r, r"turn \d+: switch: Poochyena is badly matched against Machop")
            mudkip = pid_named(r, "Mudkip")
            came = [e for e in ins(r, 0)][1:2]
            fainted_before = any(e["kind"] == "hp" and e["battler"] == 0 and e["hp"][1] == 0
                                 for e in r["game"].get("events") or [] if came and e["f"] < came[0]["f"])
            rows_.append({"seed": r["seed"], "said": bool(said), "came": [(e["species"], e["pid"]) for e in came],
                          "ok": bool(said) and bool(came) and came[0]["pid"] == mudkip and not fainted_before,
                          "outcome": (r.get("after") or {}).get("battle_outcome")})
        judge("SWITCH", all(x["ok"] for x in rows_),
              f"BY THE GAME: a forced bad matchup (the Poochyena, Dark, against Joey's Machop, Fighting x2): the decider "
              f"SWITCHED, and the Mudkip came onto position 0 by its PID with the Poochyena still standing (not a faint's "
              f"send-in), in {sum(x['ok'] for x in rows_)} of {len(rows_)} seeds: "
              f"{[(x['seed'], x['came'], x['outcome']) for x in rows_]}")
    if "RUN" in by:
        def outcome_seq(r: dict) -> list:
            game = r["game"]
            return [game.get("outcome_start")] + [o["value"] for o in game.get("outcomes") or []]

        def cleared_then_ran(r: dict) -> bool:
            # (step 4.1 round 2, the verifier: "the gBattleOutcome check never records the value before the run. The
            # fixture's start state already reads 4") BY THE GAME, every frame: the battle's own clear to 0
            # (`BattleStartClearSetData`, pret src/battle_main.c), THEN 4 (B_OUTCOME_RAN), the last value
            seq = outcome_seq(r)
            zeros = [i for i, v in enumerate(seq) if v == 0]
            return bool(zeros) and seq[-1] == 4 and zeros[-1] < len(seq) - 1
        ran = [r["seed"] for r in by["RUN"] if (r.get("after") or {}).get("battle_outcome") == 4
               and told(r, r"turn \d+: run: its Poochyena is low") and cleared_then_ran(r)]
        run_min, rate, chance = dev_floor("RUN", len(by["RUN"]))
        judge("RUN", len(ran) >= run_min,
              f"BY THE GAME every frame (gBattleOutcome: its value on the first frame, then each change) and THE TRUTH "
              f"(gBattleOutcome 4, 'ran', at the end): training, the Poochyena under its run_low, an unwanted wild battle "
              f"RUN from, the 4 written AFTER the battle's own clear to 0, in {len(ran)} of {len(by['RUN'])} seeds (bound >= "
              f"{run_min}: an escape can fail; the development rate {DEV_RATES['RUN'][0]}/{DEV_RATES['RUN'][1]}, its 95 % "
              f"lower bound {rate:.3f}, falls under it with probability {chance:.2%}) {ran}; the values per seed "
              f"{[(r['seed'], outcome_seq(r)) for r in by['RUN']]}")
    # (step 4.1, finding 5: '"clearly the best" 307 of 550; never a status move') every told fight of every run, paired
    # with the move the GAME shows chosen that turn: the status moves chosen by choice (openers, a catch's sleep or
    # paralysis), each at an HP share the GAME shows safe, and how often a choice was "clearly the best"
    pairs, unpaired = [], 0
    for runs in by.values():
        for r in runs:
            for battler, fights in told_fights(r).items():
                game = [(c["f"], c["chosen"][battler]) for c in _turn_choices(r, battler)]
                if len(game) != len(fights):
                    unpaired += 1
                    continue
                for fight, (frame, chosen) in zip(fights, game):
                    pairs.append({**fight, "game": chosen, "hp": game_hp_at(r, battler, frame), "plan": r["plan"],
                                  "seed": r["seed"]})
    # (step 4.1 ROUND 2) the OPENERS as a RATE over independent chances: the REAL plans only (a fault plan replays its
    # real plan's first turn: SHIFT-FAULT's opener IS SHIFT's), every chance the rule had (drawn or passed over), against
    # the temperament's chance; each drawn opener shown chosen by the game, at a safe HP by the game
    real_plans = [plan for plan in by if "--fault" not in PLANS[plan]["args"] and not PLANS[plan].get("replays")]
    chances, drawn_n, expected, variance = [], 0, 0.0, 0.0
    for plan in real_plans:
        chance = OPENER_CHANCE[PLANS[plan].get("personality", "Story")]
        for r in by[plan]:
            for line in r.get("lines") or []:
                drew, passed = "an OPENING move" in line, "no opener this time" in line
                if drew or passed:
                    chances.append((plan, r["seed"], drew))
                    drawn_n += drew
                    expected += chance
                    variance += chance * (1 - chance)
    sigma = variance ** 0.5
    opener_pairs = [p for p in pairs if p["plan"] in real_plans and p.get("opener")]
    unsafe = [p for p in opener_pairs if not p["hp"] or p["hp"][0] < OPENER_HP_SHARE * p["hp"][1]]
    wrong = [p for p in opener_pairs if p["game"].casefold().replace(" ", "") != p["move"].casefold().replace(" ", "")]
    catch_status = [p for p in pairs if p["plan"] in real_plans and p["status"] and not p.get("opener")]
    within = abs(drawn_n - expected) <= OPENER_SIGMAS * sigma
    # (round 3, the verifier: "the opener rate comes almost entirely from one fixture") the chances by FIXTURE: at least
    # `OPENER_SOURCES` fixtures (independent battles, leads and foes) with `OPENER_SOURCE_CHANCES` chances each
    by_fixture: dict[str, int] = {}
    for plan, _seed, _drew in chances:
        name = Path(PLANS[plan]["state"]).name
        by_fixture[name] = by_fixture.get(name, 0) + 1
    sources = sorted(name for name, n in by_fixture.items() if n >= OPENER_SOURCE_CHANCES)
    judge("STATUS", len(chances) >= OPENER_CHANCES_MIN and within and drawn_n >= 1 and not unsafe and not wrong
          and len(opener_pairs) == drawn_n and len(sources) >= OPENER_SOURCES,
          f"THE OPENERS AS A RATE (the real plans {real_plans}; a fault plan replays its real plan's first turn and is never "
          f"counted, nor a plan that replays another's first draw on another fixture: "
          f"{[p for p in by if PLANS[p].get('replays')]}): {len(chances)} chances the rule had (bound >= {OPENER_CHANCES_MIN}: drawn 'an OPENING move' or passed "
          f"over 'no opener this time', as the decider says), {drawn_n} openers drawn against {expected:.1f} expected by "
          f"each temperament's chance (+/- {OPENER_SIGMAS:g} sigma = {OPENER_SIGMAS * sigma:.1f}, a two-sided "
          f"{FALSE_FAIL:.1%} window): {'within' if within else 'OUTSIDE'}; "
          f"BY THE GAME (each turn's gChosenMoveByBattler paired with the told fights, the HP from gBattleMons): each drawn "
          f"opener shown chosen ({len(wrong)} not; {len(opener_pairs)} paired of {drawn_n}), none under "
          f"{OPENER_HP_SHARE:.0%} of its HP ({len(unsafe)}): {[(p['plan'], p['seed'], p['move'], p['hp']) for p in opener_pairs][:12]}; "
          f"per plan {sorted({(c[0], sum(1 for d in chances if d[0] == c[0]), sum(1 for d in chances if d[0] == c[0] and d[2])) for c in chances})} "
          f"(plan, chances, drawn); by fixture {by_fixture}: {len(sources)} fixtures with at least {OPENER_SOURCE_CHANCES} "
          f"chances {sources} (bound >= {OPENER_SOURCES}); a CATCH's sleep or paralysis move (reported): "
          f"{[(p['plan'], p['seed'], p['move']) for p in catch_status]}")
    # "clearly the best", LIKE FOR LIKE (the verifier: "307/550 (56 %) -> 618/1674 (37 %) compares a 14-plan sweep with a
    # 21-plan sweep"): over the 8 real-decider plans the step-4 sweep had, and over every plan (reported, no bound)
    like = [p for p in pairs if p["plan"] in STEP4_REAL_PLANS]
    clearly_like = sum(1 for p in like if p["clearly"])
    clearly = sum(1 for p in pairs if p["clearly"])
    say(f"CLEARLY THE BEST (reported; finding 5's measure): over the step-4 sweep's 8 real-decider plans {list(STEP4_REAL_PLANS)} "
        f"{clearly_like} of {len(like)} fight choices paired with the game ({clearly_like / max(1, len(like)):.0%}; the "
        f"verifier's like-for-like A/B on the same plans and seeds, told fights: HEAD (step 4) 302 of 367, 82 %, the step-4.1 "
        f"tree 267 of 368, 73 %); over every plan of this sweep {clearly} of {len(pairs)} ({clearly / max(1, len(pairs)):.0%}: "
        f"another set of plans, NOT comparable with step 4's 307 of 550); unpaired battlers {unpaired}")


def _turn_choices(row: dict, battler: int) -> list[dict]:
    """Every change of `gChosenMoveByBattler[battler]` from none to a move (one turn's choice, as `game_choices`), with its
    frame."""
    out, last = [], "-"
    for entry in row["game"].get("chosen") or []:
        now = entry["chosen"][battler]
        if now != "-" and last == "-":
            out.append(entry)
        last = now
    return out


def game_choices(row: dict, battler: int) -> list[tuple[str, str, tuple[str, ...]]]:
    """The move battler `battler` CHOSE each turn, by the GAME: `gChosenMoveByBattler` is cleared to MOVE_NONE at every turn's
    end (`src/battle_main.c`, the turn counter's increment: `gChosenMoveByBattler[i] = MOVE_NONE`), so every change of it
    from none to a move is one turn's choice (the recorder logs every change); with the species on the field at that
    frame (`gBattleMons`: the chooser's, and the foes' at positions 1 and 3): (move, the chooser, the foes)."""
    out, last = [], "-"
    # (step 4.1) position 3 counts only when a Pokemon came onto it in THIS battle (a double battle): in a single battle it
    # holds what an earlier battle left there (the step-4.1 development sweep listed "('Marshtomp', ('Wingull', 'Lotad'))"
    # in the rival's single battle)
    third = any(e["kind"] == "in" and e["battler"] == 3 for e in row["game"].get("events") or [])
    for entry in row["game"].get("chosen") or []:
        now = entry["chosen"][battler]
        if now != "-" and last == "-":
            species = entry.get("species") or ["?"] * 4
            # position 3 of a SINGLE battle is empty: species 0, whose name is "??????????" (the development sweep of
            # 2026-10-09 listed a matchup "('Machop', '??????????')" until this filter)
            foes = (species[1], species[3]) if third else (species[1],)
            out.append((now, species[battler], tuple(s for s in foes if s and s.strip("?") and s != "-")))
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
    field_plans = [p for p in wanted if p in ("FIELD-FAULT", "FIELD-STEP4")]
    jobs = [(plan, PLANS[plan].get("seed_offset", 0) + seed) for plan in wanted if plan not in field_plans
            for seed in range(args.first_seed, args.first_seed + PLANS[plan].get("seeds", args.seeds))]
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        rows = list(pool.map(lambda job: run_one(*job), jobs))
    # (step 4.1 round 2) the FIELD plans, second: the seeds where this sweep's TYPE-FAULT had a player's Pokemon fall, and
    # the anchors (`FIELD_ANCHOR_SEEDS`)
    fell = sorted({r["seed"] for r in rows if r["plan"] == "TYPE-FAULT" and "error" not in r and told(r, "who goes in")})
    field_seeds = sorted(set(fell) | set(FIELD_ANCHOR_SEEDS))
    if field_plans:
        field_jobs = [(plan, seed) for plan in field_plans for seed in field_seeds]
        jobs += field_jobs
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            rows += list(pool.map(lambda job: run_one(*job), field_jobs))
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

    broken = selftest_not_beside()
    judge("SELFTEST", not broken, f"the double-faint identity check, send-in by send-in, on its three shapes (seed 422's: "
                                  f"pass; the one standing beside sent in: fail; the round-2 pooled check's false alarm "
                                  f"reproduced): {broken or 'as expected'}")
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
        # (step 4.1, finding 8: "the TYPE proof rests on one matchup's A/B") a SECOND matchup in the same battles, another
        # attacker, another defender, another type: the Nincada (battler 2, Bug/Ground) against the Shroomish (Grass), where
        # LEECH LIFE (Bug 20, x2, STAB: worth 60) beats SCRATCH (Normal 40) only by the chart (with no types: 40 against 20)
        real2 = [game_first_move(r, 2) for r in by["TYPE"]]
        fault2 = [game_first_move(r, 2) for r in by["TYPE-FAULT"]]
        hits2, fault_hits2 = real2.count(TYPE_SECOND), sum(1 for p in fault2 if p[0] == TYPE_SECOND[0])
        judge("TYPE SECOND MATCHUP", hits2 == len(real2) and fault_hits2 == 0,
              f"BY THE GAME (gChosenMoveByBattler[2], the first hit's target): the Nincada's first move {TYPE_SECOND[0]} at the "
              f"{TYPE_SECOND[1]} REAL {hits2} of {len(real2)}, FAULT (types ignored) {TYPE_SECOND[0]} at all {fault_hits2} of "
              f"{len(fault2)} (its picks {sorted(set(fault2))}): a second attacker and defender, a second type (Bug on Grass "
              f"against Grass on Rock/Ground); each still ONE decision replayed per plan, the evidence the A/B. (Round 3, the "
              f"verifier: this is the SAME double battle and fixture, not an independent battle: TYPE INDEPENDENT MATCHUP "
              f"below is)")
    # (round 3, the verifier: "the 'second matchup' ... is a different battler in the same double battle and fixture, not
    # an independent battle") an INDEPENDENT battle: TRAINER (Route 116, Joey's Machop, a single battle, another fixture)
    # against TRAINER-TYPE-FAULT. With the chart Pursuit (Dark, resisted by Fighting) is never the first move and Quick
    # Attack is clearly the best; type-blind, Pursuit and Quick Attack are worth the same and the draw takes Pursuit about
    # half the time: its chance computed from the told worths, the count in its window
    if "TRAINER" in by and "TRAINER-TYPE-FAULT" in by:
        real3 = [game_first_move(r)[0] for r in by["TRAINER"]]
        fault3 = [game_first_move(r)[0] for r in by["TRAINER-TYPE-FAULT"]]
        said3 = [told_first_move(r) for r in by["TRAINER-TYPE-FAULT"]]
        firsts = [next((line for line in told(r, r"turn 1: fight ")), "") for r in by["TRAINER-TYPE-FAULT"]]
        chances = [draw_chance(told_values(line), TYPE_THIRD[0], NEAR_BEST["Story"]) for line in firsts]
        same = len({round(c, 4) for c in chances}) == 1
        chance = chances[0] if chances else 0.0
        low, high = window_for(len(fault3), chance) if same else (0, -1)
        pursuits = fault3.count(TYPE_THIRD[0])
        clearly = all("Quick Attack is clearly the best" in next((line for line in told(r, r"turn 1: fight ")), "")
                      for r in by["TRAINER"])
        judge("TYPE INDEPENDENT MATCHUP",
              real3 == [TYPE_THIRD[1]] * len(real3) and clearly and fault3 == said3 and same and 0 < chance < 1
              and low <= pursuits <= high and pursuits >= 1,
              f"BY THE GAME (gChosenMoveByBattler[0], another fixture: Route 116, Joey's Machop, a single battle): with the "
              f"chart the Grovyle's first move {TYPE_THIRD[1]} in {real3.count(TYPE_THIRD[1])} of {len(real3)} seeds, "
              f"{TYPE_THIRD[0]} (Dark, resisted by Fighting) in {real3.count(TYPE_THIRD[0])} ('clearly the best' told in "
              f"every seed: {clearly}); TYPE-BLIND (`ignore_types`) {TYPE_THIRD[0]} in {pursuits} of {len(fault3)} (the "
              f"draw's chance from the told worths {chance:.3f}, the same in every seed: {same}; window {low}-{high}, at "
              f"least 1), the told move agrees with the game: {fault3 == said3}; picks {sorted(set(fault3))}")

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
            # (step 4.1 round 3, its HELD-OUT run, seed 422: BOTH of the player's Pokemon fell one after the other, the
            # Skitty came onto position 0 and then the Whismur onto position 2 beside it; the step-4 verifier's-round check
            # pooled every send-in's PID against every send-in's neighbour, so the Skitty, sent in first and standing beside
            # the second, read as "the one standing beside it". A GRADER bug, not the AI's: the check is now PER SEND-IN,
            # the Pokemon that came in against the one standing on the other position AT THAT FRAME)
            def beside_ok(x: dict) -> bool:
                return not_beside(x["pids"], x["beside"])
            ok = all(x["refused"] == 0 and x["ended"] and [s for _, s in x["came"]] == x["named"] and beside_ok(x)
                     for x in rows_)
            judge(f"{plan} DOUBLE-FAINT", ok,
                  f"BY THE GAME (who came onto the player's positions after a faint): a player's Pokemon fell in "
                  f"{len(rows_)} of {len(by[plan])} seeds; in every one the Pokemon the decider NAMED came in: "
                  f"{all([s for _, s in x['came']] == x['named'] for x in rows_)}, never the one standing on the other "
                  f"position at that send-in: {all(beside_ok(x) for x in rows_)}, the game refused nothing ('already in "
                  f"battle' never on screen): {all(x['refused'] == 0 for x in rows_)}, the battle ended by itself: "
                  f"{all(x['ended'] for x in rows_)} {[(x['seed'], x['named'], x['came'], x['refused']) for x in rows_]}")
    if field_plans:
        say(f"FIELD SEEDS (step 4.1 round 2: the A/B is played where its case occurs): this sweep's TYPE-FAULT had a player's "
            f"Pokemon fall in seeds {fell} ({len(fell)} of {len(by.get('TYPE-FAULT', []))}); the FIELD plans play those and the "
            f"ANCHOR seeds {list(FIELD_ANCHOR_SEEDS)} (the development sweep's case, live_step4 DFAINT: a replay, not a new "
            f"sample): {field_seeds}")
    if "FIELD-FAULT" in faint_runs:
        rows_ = faint_runs["FIELD-FAULT"]
        refused = [x for x in rows_ if x["refused"]]
        fresh = [x["seed"] for x in refused if x["seed"] not in FIELD_ANCHOR_SEEDS]
        ok = bool(refused) and all(x["ended"] and x["came"] for x in rows_)
        judge("FIELD-FAULT", ok,
              f"FAULT forget_field (the step-4 replacement), the refusal READ: the game refused the one on the field in "
              f"{len(refused)} seeds ({[x['seed'] for x in refused]}; of them from this sweep's own falls, not an anchor: "
              f"{fresh or 'none'}), the AI read the words and the game shows another come "
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
                # one decision replayed ("Take Down is clearly the best"): not chance
                judge(plan, take >= RECOIL_REAL_MIN and agree and set(picks) <= {"Take Down", "Water Gun"}
                      and charged == [RECOIL_GAME_HP],
                      f"BY THE GAME, under FAULT overkill (step 4.1: the step-4 valuation, where Take Down is worth most): "
                      f"Marshtomp's first move Take Down in {take} of {n} seeds (bound >= {RECOIL_REAL_MIN}: its "
                      f"recoil is a quarter of the 15 HP the hit can take); the recoil the GAME charged for it {charged} HP "
                      f"(want [{RECOIL_GAME_HP}]); the told move agrees: {agree}; picks {picks}")
            else:
                # (round 3, the verifier: "Take Down in 8 of 10 seeds (bound <= 5) ... a weighted draw with p about 0.37
                # ... 8 of 10 is about a 0.6% tail") the step-4 rule's choice is a DRAW between Take Down and Water Gun:
                # the chance of Take Down is computed from the worths the decider TOLD (`draw_chance`, the Story
                # near-best share), every first decision must be such a draw with Water Gun worth MORE (the step-4 rule
                # overcharging the recoil), and the count of Take Downs must lie in that chance's binomial window
                firsts = [next((line for line in told(r, r"turn 1: fight ")), "") for r in by[plan]]
                worths = [told_values(line) for line in firsts]
                chances = [draw_chance(w, "Take Down", NEAR_BEST["Story"]) for w in worths]
                drawn = all("drawn among the about-as-good" in line for line in firsts)
                water_more = all(w.get("Water Gun", 0) > w.get("Take Down", 0) > 0 for w in worths)
                same = len({round(c, 4) for c in chances}) == 1
                chance = chances[0] if chances else 0.0
                low, high = window_for(n, chance) if same else (0, -1)
                judge(plan, agree and drawn and water_more and same and 0 < chance < 1 and low <= take <= high,
                      f"BY THE GAME, FAULTS overkill + uncapped_recoil (the step-4 rule: the recoil of the whole worth): "
                      f"Take Down in {take} of {n} seeds; every first decision a DRAW among the about-as-good ({drawn}) "
                      f"with Water Gun worth more than Take Down ({water_more}: the told worths {sorted(set(tuple(sorted(w.items())) for w in worths))[:2]}); "
                      f"the draw's chance of Take Down from those worths {chance:.3f} (the same in every seed: {same}), "
                      f"window {low}-{high} (a sample of that draw falls outside it with probability at most "
                      f"{FALSE_FAIL:.1%}); the told move agrees: {agree}; picks {picks}")
    if "RECOIL" in by and "RECOIL-FAULT" in by:
        say(f"RECOIL A/B (by the game, both under FAULT overkill): Take Down with the recoil cap "
            f"{[game_first_move(r)[0] for r in by['RECOIL']].count('Take Down')} of {len(by['RECOIL'])} (clearly the best: "
            f"every seed), the step-4 rule {[game_first_move(r)[0] for r in by['RECOIL-FAULT']].count('Take Down')} of "
            f"{len(by['RECOIL-FAULT'])} (a draw that favours Water Gun)")
    # (step 4.1, finding 6) OVERKILL: every damaging move finishes the 15-HP Poochyena
    for plan in ("OVERKILL", "OVERKILL-FAULT"):
        if plan in by:
            picks = [game_first_move(r)[0] for r in by[plan]]
            said = [told_first_move(r) for r in by[plan]]
            take = picks.count("Take Down")
            agree = picks == said
            ended = all(ended_by_itself(r) for r in by[plan])
            if plan == "OVERKILL":
                judge(plan, take <= OVERKILL_REAL_MAX and agree and ended and "Take Down" not in picks,
                      f"BY THE GAME (gChosenMoveByBattler[0]): every damaging move FINISHES the Poochyena (its rough damage "
                      f"over its bar), so each is worth as the strongest and the hit chance and recoil decide: Take Down (85 %, "
                      f"recoil) in {take} of {len(picks)} seeds (bound <= {OVERKILL_REAL_MAX}); the moves chosen {sorted(set(picks))}; "
                      f"the told move agrees: {agree}; every battle ended by itself: {ended}")
            else:
                judge(plan, take >= OVERKILL_FAULT_MIN and agree,
                      f"BY THE GAME, FAULT overkill (step 4: every move uncapped): Take Down in {take} of {len(picks)} seeds "
                      f"(bound >= {OVERKILL_FAULT_MIN}): the finding reproduced; the told move agrees: {agree}")
    if "OVERKILL" in by and "OVERKILL-FAULT" in by:
        say(f"OVERKILL A/B (by the game): Take Down REAL {[game_first_move(r)[0] for r in by['OVERKILL']].count('Take Down')} of "
            f"{len(by['OVERKILL'])}, step 4's valuation {[game_first_move(r)[0] for r in by['OVERKILL-FAULT']].count('Take Down')} "
            f"of {len(by['OVERKILL-FAULT'])}")
    grade_step41(by, judge, say)
    if "WILD" in by:
        won = [r for r in by["WILD"] if "won" in outcomes(r) and (exp(r, "after", MUDKIP) or 0) > (exp(r, "before", MUDKIP) or 0)
               and ended_by_itself(r)]
        battles = [((r["after"] or {}).get("game_stats") or {}).get("wild_battles", 0)
                   - ((r["before"] or {}).get("game_stats") or {}).get("wild_battles", 0) for r in by["WILD"]]
        wild_min, rate, chance = dev_floor("WILD", len(by["WILD"]))
        judge("WILD", len(won) >= wild_min,
              f"BY THE TRUTH (the Mudkip's experience by PID, the game's wild-battle count): {len(won)} of {len(by['WILD'])} runs "
              f"won a wild battle by fighting and raised the Mudkip's experience (bound >= {wild_min}: the development rate "
              f"{DEV_RATES['WILD'][0]}/{DEV_RATES['WILD'][1]}, its 95 % lower bound {rate:.3f}, falls under it with "
              f"probability {chance:.2%}); wild battles per run {battles}; outcomes {[(r['seed'], outcomes(r)) for r in by['WILD']]}")
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
        catch_min, rate, chance = dev_floor("CATCH", len(by["CATCH"]))
        judge("CATCH", len(caught) >= catch_min and len(caught) + len(knocked) == len(by["CATCH"]),
              f"BY THE TRUTH (gBattleOutcome 7, ONE new PID whose OT is the player's, the bag's balls): {len(caught)} of "
              f"{len(by['CATCH'])} caught (bound >= {catch_min}: the development rate {DEV_RATES['CATCH'][0]}/"
              f"{DEV_RATES['CATCH'][1]}, its 95 % lower bound {rate:.3f}, falls under it with probability {chance:.2%}); "
              f"EVERY other run knocked out by a weakening hit judged safe: seeds {[r['seed'] for r in knocked]}; balls spent "
              f"per seed {spent} (total {sum(spent)})")
    if "TRAINER" in by:
        won = [r for r in by["TRAINER"] if outcomes(r) == ["won"] and ((r.get("after") or {}).get("trainer_defeated") or {}).get("322")]
        trainer_min, rate, chance = dev_floor("TRAINER", len(by["TRAINER"]))
        judge("TRAINER", len(won) >= trainer_min,
              f"BY THE TRUTH (Joey's defeated flag 322): {len(won)} of {len(by['TRAINER'])} won (bound >= {trainer_min}: the "
              f"development rate {DEV_RATES['TRAINER'][0]}/{DEV_RATES['TRAINER'][1]}, its 95 % lower bound {rate:.3f}, falls "
              f"under it with probability {chance:.2%})")
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
        # (round 3) the CORRECTNESS claim needs cases: the lead faints by the battle's dice, so a floor of fainting seeds
        # from the development rate (20 seeds: at 10 the chance of none was above `FALSE_FAIL`)
        faint_min, rate, chance = dev_floor("FAINT_ANY", len(rows_))
        ok = len(fainted) >= max(1, faint_min) and all(x["came"] == x["named"] and x["against"] and x["ended"] for x in fainted) \
            and all(x["ended"] for x in rows_)
        judge("FAINT", ok,
              f"BY THE GAME (the Pokemon that came onto battler 0) against the decider's word: the lead fainted in "
              f"{len(fainted)} of {len(rows_)} seeds (bound >= {max(1, faint_min)}: the development rate "
              f"{DEV_RATES['FAINT_ANY'][0]}/{DEV_RATES['FAINT_ANY'][1]}, its 95 % lower bound {rate:.3f}, falls under it with "
              f"probability {chance:.2%}); in EVERY one the one the decider NAMED came in, named 'against' the foe it "
              f"remembered (the party menu has no battle view), and every battle went on to its end: "
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
    # (step 4.1 round 2, the verifier's weak proofs) SING (a catch helped by sleep) and REFUSED (a move the game refuses)
    def taken(row: dict, battler: int = 0) -> list[str]:
        return [c["chosen"][battler] for c in row["game"].get("chosen") or [] if c["chosen"][battler] != "-"]

    def asleep_before_end(row: dict) -> bool:
        game = row["game"]
        ends = [o["f"] for o in game.get("outcomes") or [] if o["value"]]
        sleeps = [s["f"] for s in game.get("statuses") or [] if s["battler"] == 1 and s["sleep"] > 0]
        return bool(sleeps) and (not ends or sleeps[0] < ends[-1])
    if "SING" in by:
        rows_ = [(r["seed"], taken(r), asleep_before_end(r), (r.get("after") or {}).get("battle_outcome")) for r in by["SING"]]
        sang = [x for x in rows_ if "Sing" in x[1]]
        asleep = [x for x in rows_ if x[2]]
        taken_min, taken_rate, taken_chance = dev_floor("SING_TAKEN", len(rows_))
        asleep_min, asleep_rate, asleep_chance = dev_floor("SING_ASLEEP", len(rows_))
        judge("SING", len(sang) >= taken_min and len(asleep) >= asleep_min,
              f"BY THE GAME (the moves it TOOK, gChosenMoveByBattler[0]; the foe's status1 every frame; gBattleOutcome): a "
              f"Skitty with SING against a wild Oddish the Pokedex has not got (Catcher): Sing taken in {len(sang)} of "
              f"{len(rows_)} seeds (bound >= {taken_min}: not on a turn its own HP makes unsafe; the development rate "
              f"{DEV_RATES['SING_TAKEN'][0]}/{DEV_RATES['SING_TAKEN'][1]}, lower bound {taken_rate:.3f}, falls under it with "
              f"probability {taken_chance:.2%}), the Oddish ASLEEP before the battle's end in {len(asleep)} (bound >= "
              f"{asleep_min}: Sing hits 55 % of the time, tried twice at most; the development rate "
              f"{DEV_RATES['SING_ASLEEP'][0]}/{DEV_RATES['SING_ASLEEP'][1]}, lower bound {asleep_rate:.3f}, falls under it "
              f"with probability {asleep_chance:.2%}); caught (gBattleOutcome 7) in {sum(1 for x in rows_ if x[3] == 7)} "
              f"(reported): {rows_}")
    if "SING-FAULT" in by:
        rows_ = [(r["seed"], taken(r), asleep_before_end(r), (r.get("after") or {}).get("battle_outcome")) for r in by["SING-FAULT"]]
        judge("SING-FAULT", all("Sing" not in x[1] and not x[2] for x in rows_),
              f"FAULT no_catch_status (step 4: no status move to help a catch), BY THE GAME: Sing never taken and the Oddish "
              f"never asleep in {sum(1 for x in rows_ if 'Sing' not in x[1] and not x[2])} of {len(rows_)} seeds; caught in "
              f"{sum(1 for x in rows_ if x[3] == 7)} (reported): {rows_}")
    if "REFUSED" in by:
        rows_ = []
        for r in by["REFUSED"]:
            pp = {name: left for row in (r.get("before") or {}).get("party_pp") or [] if row[1] == "Wailord" for name, left in row[2]}
            refused = re.findall(r"the move grid came back: (.+?) cannot be used now", " ".join(r.get("lines") or []))
            took = taken(r)
            fought = bool(told(r, r"turn \d+: fight "))
            rows_.append({"seed": r["seed"], "refused": refused, "taken": took, "outcomes": outcomes(r), "fought": fought,
                          "ok": (len(set(refused)) >= 2 and all(pp.get(m) == 0 for m in refused) and bool(took)
                                 and all(pp.get(m, 0) > 0 for m in took) and outcomes(r) == ["won"])})
        fought = [x for x in rows_ if x["fought"]]
        # (round 3, the verifier: "a floor of 3 fought seeds fails about 17% of samples") the seeds where it FOUGHT are the
        # Story temperament's chance of letting a new species go (0.4): 30 seeds, the floor that chance misses at most
        # `FALSE_FAIL` of the time
        fought_min = floor_for(len(rows_), STORY_LETS_GO)
        judge("REFUSED", len(fought) >= fought_min and all(x["ok"] for x in fought),
              f"BY THE TRUTH (each move's PP at the start) and THE GAME (the moves it TOOK: a refused move never reaches "
              f"gChosenMoveByBattler): the decider made blind to PP (FAULT ignore_pp) chose moves with none, the game refused "
              f"each and gave the grid back, at least two different moves out in one turn, the game took only moves with PP, and "
              f"the battle was won, in {sum(x['ok'] for x in fought)} of the {len(fought)} seeds where it FOUGHT (bound: EVERY "
              f"one; and at least {fought_min} fought: the Story decider lets a new species go with chance {STORY_LETS_GO}, "
              f"which falls under that with probability {tail_below(fought_min, len(rows_), STORY_LETS_GO):.3%}); the others "
              f"it wanted the Zubat and threw balls (nothing to refuse): {[(x['seed'], x['refused'], x['taken'], x['outcomes']) for x in rows_]}")
    if "REFUSED-FAULT" in by:
        # the step-4 loop: a refused move chosen again and again, the game taking no move, until a bound ends the run (the
        # skill's 150 menus, or the run's frame budget first: measured, 134 refusals in 40,000 frames)
        rows_ = [(r["seed"], bool(told(r, r"turn \d+: fight ")),
                  len(re.findall(r"the move grid came back", " ".join(r.get("lines") or []))), taken(r),
                  str(r.get("reason"))[:80]) for r in by["REFUSED-FAULT"]]
        fought = [x for x in rows_ if x[1]]
        fought_min = floor_for(len(rows_), STORY_LETS_GO)
        judge("REFUSED-FAULT", len(fought) >= fought_min and all(n >= 20 and not took for _, _, n, took, _ in fought),
              f"FAULTS ignore_pp + forget_unusable (the step-4 rule: a refused move chosen again), in EVERY seed where it "
              f"fought (at least {fought_min}, as REFUSED): the grid came back again and again and the game took no move "
              f"until a bound ended the run, in {sum(1 for _, _, n, t, _ in fought if n >= 20 and not t)} of {len(fought)} "
              f"(finding 2's loop, reproduced): {rows_}")
    # (the step-4 verifier's round: "TYPE 'rate across seeds' is not a rate ... one counterfactual A/B replayed") EVERY
    # choice of the best move in the sweep where the type chart was DECISIVE (the type-blind best not about as good with
    # the chart), paired with the move the GAME shows chosen that turn; the type-blind plans the same, classified by the
    # chart the decider did not use
    real_rows = [r for plan, runs in by.items() if not any(f in " ".join(PLANS[plan]["args"]) for f in ("ignore_types",))
                 for r in runs]
    # (round 3) TRAINER-TYPE-FAULT is not one of these type-blind plans: its type-blind draw is between two moves worth the
    # same (one in the chart's set), graded by its own A/B (TYPE INDEPENDENT MATCHUP) and its window
    blind_rows = [r for plan, runs in by.items() if "ignore_types" in " ".join(PLANS[plan]["args"])
                  and plan != "TRAINER-TYPE-FAULT" for r in runs]
    if real_rows:
        real = type_decisions(real_rows)
        blind = type_decisions(blind_rows) if blind_rows else None
        rate = real["near"] / real["decisive"] if real["decisive"] else 0.0
        blind_rate = (blind["near"] / blind["decisive"]) if blind and blind["decisive"] else None
        ok = (real["decisive"] >= TYPE_DECISIVE_MIN and len(real["matchups"]) >= TYPE_MATCHUPS_MIN and rate >= TYPE_NEAR_MIN
              and rate >= real["chance"] + TYPE_OVER_CHANCE
              and real["disagree"] == 0 and (blind_rate is None or blind_rate <= TYPE_BLIND_MAX))
        # (step 4.1, finding 8) LABELLED A HANDS CHECK: the decider draws only from the chart's near-best set, so "the game
        # shows a move of that set chosen" holds BY CONSTRUCTION whenever the hands press what the decider chose: it proves
        # the told choice reached the game (and how many turns the chart was decisive in), not that the chart is right.
        # The chart's own evidence is the type-blind A/B (TYPE / TYPE-FAULT and TYPE SECOND MATCHUP)
        judge("TYPE-DECISIONS (a HANDS CHECK)", ok,
              f"A HANDS CHECK, NOT A TYPE-CHART PROOF (the chart's evidence is the type-blind A/B above): "
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
        keep_earlier(args.evidence)  # (step 4.1 round 3) an earlier tree's file is archived, not written over
        args.evidence.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
