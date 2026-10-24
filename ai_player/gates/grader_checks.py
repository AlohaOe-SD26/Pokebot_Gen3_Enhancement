"""TEST SIDE (build step 5.3, stage A1-1: N8 and B1's grader half): the step-5 graders' checks, TYPED.

WHY. Before 5.3 a check of `rate_step5.py` or `live_step5.py` was a bare `(ok, text)` tuple. "Reported" existed only as a
TEXT PREFIX that `p2_reported` matched with `str.startswith`, 15 of the 67 rows of the newest graded sweep (ledger #34)
were forced PASS, a check that saw no sample at all read PASS (`08-MISTAKES.md` 2026-09-02), and nothing said which
checks graded the AI by its OWN record (the Goodhart channel B1 names: the grader taking its windows and constants from
the code it grades). Stage A1 changes NOTHING in what is measured: it makes each check say what it is.

A CHECK is `Check(id, kind, status, n, floor, inputs, text)`:
  kind    GRADED      counts in the verdict.
          HONESTY     the AI's own word judged against the game; counts.
          DIAGNOSTIC  printed, never counts (a property with no game form, or AI-only; listed in the evidence as a property
                      the grade no longer counts).
          REPORTED    a measure with no bound; never counts (the 5.2 P2 shares keep their OLD bound's verdict as `status`,
                      printed as "the old bound HELD / did NOT hold").
  status  PASS, FAIL, or VACUOUS (`n < floor`: the check saw too few samples to say anything). VACUOUS FAILS the verdict
          unless its id is waived in `grader_waivers.json` with a reason.
  inputs  a subset of {game, harness, ai}, declared HONESTLY for today's code (what the check's code reads, helpers
          included). Construction RAISES (`CheckError`) when a GRADED check names `ai` and its id is not in
          `b1_debt.json` (the debt A2 pays down), and when a HONESTY check does not name both `ai` and `game`.
THE VERDICT is PASS iff there is at least one check and every GRADED and HONESTY check is PASS, or VACUOUS with a waiver
(`verdict`). Ids are stable and unique; every id, its kind, its inputs and the start of its text live in ONE table,
`CHECKS`, which is validated against both json files when this module is imported (a debt entry for a check that does
not read the AI, or a waiver for an unknown id, refuses the import: the lists stay exact both ways).

THE TWO TUPLE VIEWS (kept for the tuple consumers; stage A1-4 re-pointed `test_goals.py`'s to check ids, `check_by_id`):
  * a sub-verdict function's row (`grade`) reads `(status is PASS, text)`: its own outcome, whatever its kind;
  * `verdict_row` (what `rate_step5.verdicts` and `live_step5`'s overall line use) reads `(does not fail the verdict,
    text)`, so `all(ok for ok, _ in rows)` is exactly `verdict(rows) == "PASS"`.
`as_check` types a legacy `(ok, text)` tuple by the START of its text (`CHECKS` titles; none is a prefix of another in its
grader), and RAISES for a text no title starts: no untyped check reaches a verdict. It exists for `live_step2.check_purity`
(outside stage A1's files), whose rows are plain tuples; since A1-4 no unit test mocks a sub-verdict with one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

GATES = Path(__file__).resolve().parent
WAIVERS_FILE = GATES / "grader_waivers.json"
DEBT_FILE = GATES / "b1_debt.json"

GRADED, HONESTY, DIAGNOSTIC, REPORTED = "GRADED", "HONESTY", "DIAGNOSTIC", "REPORTED"
KINDS = (GRADED, HONESTY, DIAGNOSTIC, REPORTED)
#: the kinds the verdict counts
COUNTED = (GRADED, HONESTY)
PASS, FAIL, VACUOUS = "PASS", "FAIL", "VACUOUS"
STATUSES = (PASS, FAIL, VACUOUS)
GAME, HARNESS, AI = "game", "harness", "ai"
INPUTS = frozenset({GAME, HARNESS, AI})


class CheckError(ValueError):
    """A check that breaks the typing rules (an undeclared AI input on a GRADED check, a HONESTY check without both
    halves, an unknown id or kind, a text that does not start with its id's title, a stale debt or waiver entry)."""


@dataclass(frozen=True)
class Spec:
    """One row of `CHECKS`: the check's kind, its inputs, the START of its text (`title`), the recon row it was (`was`:
    `#n` of `2026-10-22-B1-grader-recon.md` §1, or a live_step5 line), `old_bound` for a REPORTED share of frames that keeps
    its 5.2 bound's verdict, and `dropped`: for a check A1 made DIAGNOSTIC, the property the grade no longer counts."""
    kind: str
    inputs: frozenset
    title: str
    was: str = ""
    old_bound: bool = False
    dropped: str = ""


def _spec(kind: str, inputs: str, title: str, was: str = "", old_bound: bool = False, dropped: str = "") -> Spec:
    return Spec(kind, frozenset(inputs.split("+")), title, was, old_bound, dropped)


G, H, A = "game", "harness", "ai"
# ---------------------------------------------------------------------------------------------------------------- THE TABLE
#: EVERY check of the two step-5 graders: id -> Spec. R5.* = `rate_step5.py` (the seed sweep), L5.* = `live_step5.py` (the
#: launcher arms). `inputs` is what today's code READS (helpers included): `ai` = the AI's action log, world memory, report,
#: reason, told lines or a value derived from them (its goal spans as WINDOWS included); `game` = the harness's own reads of
#: the game (recorders, `truth`, save blocks); `harness` = the harness's or the launcher's own instrument (its frame count, the
#: verdict file's counters, the run's configuration).
CHECKS: dict[str, Spec] = {
    # ---- rate_step5.verdicts
    "R5.CH1_REACHED": _spec(GRADED, G, "CH1: the POKéDEX reached", "#1"),
    "R5.CH1_FIRST_TRY": _spec(GRADED, G, "CH1: the rival beaten at the FIRST try", "#2"),
    "R5.CH1_TRAINED": _spec(GRADED, G + "+" + A, "CH1: every seed that beat the rival TRAINED first", "#3"),
    "R5.CH1_WILD_WON": _spec(REPORTED, G, "CH1 (reported): wild battles WON anywhere", "#4"),
    "R5.CH1_SPINS": _spec(GRADED, A, "CH1: the back-and-forth spins", "#5"),
    "R5.CH1_CATCH_ALL": _spec(DIAGNOSTIC, A, "CH1: no stretch standing still under the catch-all", "#6",
                              dropped="no idle stretch under the catch-all reason (the AI's own reason labels)"),
    "R5.CH1_WHITEOUTS": _spec(GRADED, G, "CH1: the game's whiteouts", "#7"),
    "R5.CH1_REST_RULE": _spec(GRADED, A, "CH1: THE REST RULE", "#8"),
    "R5.CH1_RECORDER": _spec(GRADED, G, "CH1: the recorder saw every battle end", "#9"),
    "R5.LOSSES_AGREE": _spec(HONESTY, A + "+" + G, "ALL PLANS: the AI's battles lost", "#10"),
    "R5.NOTRAIN_MECHANISM": _spec(GRADED, G, "NOTRAIN (the mechanism)", "#11"),
    "R5.NOTRAIN_TRAINED_CHECK": _spec(GRADED, G + "+" + A, "THE TRAINED CHECK TELLS TRAINING FROM NONE", "#12"),
    "R5.NOTRAIN_LEVEL": _spec(GRADED, G, "NOTRAIN (the effect", "#13"),
    "R5.NOTRAIN_HP": _spec(REPORTED, G, "NOTRAIN (reported, not bounded): the HP share", "#14"),
    "R5.NOTRAIN_FIRST_TRY": _spec(REPORTED, G, "NOTRAIN (reported, not bounded): the rival beaten", "#15"),
    "R5.DEADREST": _spec(GRADED, A, "DEADREST (the fix REMOVED", "#16"),
    "R5.NOHINTS_SLOWER": _spec(GRADED, G, "NOHINTS: reached", "#17"),
    # ---- rate_step5.stop_verdicts
    "R5.STOP": _spec(HONESTY, A + "+" + G + "+" + H, "STOP (MAX_LOSSES 1", "#18"),
    "R5.STOPDEAD": _spec(HONESTY, A + "+" + G + "+" + H, "STOPDEAD (MAX_LOSSES 1", "#19"),
    # ---- rate_step5.step51_verdicts
    "R5.STALL": _spec(GRADED, A + "+" + G, "THE STALL PROPERTY (every run", "#20"),
    "R5.STALL_SECOND_PATH": _spec(GRADED, G, "THE STALL PROPERTY's second path", "#21"),
    "R5.STALL1": _spec(GRADED, A + "+" + G, "STALL1 (the fix REVERTED", "#22"),
    "R5.STALL2": _spec(GRADED, A + "+" + G, "STALL2 (the fix REVERTED", "#23"),
    "R5.STALL3": _spec(GRADED, A + "+" + G, "STALL3 (the fix REVERTED", "#24"),
    "R5.STALL_PATHS_AGREE": _spec(HONESTY, A + "+" + G, "THE TWO PATHS AGREE on the stall verdict", "#25"),
    "R5.ASIDE_BACK": _spec(DIAGNOSTIC, A, "A STORY GOAL PUT ASIDE COMES BACK", "#26",
                           dropped="a story goal put aside comes back within ASIDE_STREAK_MAX (the AI's goal keys only)"),
    "R5.GO_AFTER_PAGE": _spec(DIAGNOSTIC, A, "EVERY GO GOAL WITH A MAP CAME AFTER THE PAGE", "#27",
                              dropped="every go goal with a map came after the page that told it (the AI's read records)"),
    "R5.CH1_INTENT_MIX": _spec(REPORTED, A + "+" + G, "THE INTENT MIX (CH1)", "#28", old_bound=True),
    "R5.CH1_FREE": _spec(REPORTED, A + "+" + G, "CURIOSITY THE STORY DID NOT NEED (CH1", "#29", old_bound=True),
    "R5.SEED_DIVERGENCE": _spec(GRADED, A, "SEED DIVERGENCE", "#30"),
    "R5.OFF_MOVES_MIX": _spec(REPORTED, A + "+" + G, "ERRANDS_OFF MOVES THE INTENT MIX", "#31", old_bound=True),
    "R5.OFF_MOVES_DIVERGENCE": _spec(GRADED, A, "ERRANDS_OFF MOVES THE DIVERGENCE", "#32"),
    "R5.BEELINE_FAILS_FREE": _spec(REPORTED, A + "+" + G, "THE BEELINE FAILS THE CURIOSITY BOUND", "#33", old_bound=True),
    "R5.OFF_BEELINE": _spec(GRADED, A, "OFF THE BEELINE", "#34"),
    "R5.ERRANDS_DIFFER": _spec(DIAGNOSTIC, A, "THE ERRANDS DIFFER BY SEED", "#35",
                               dropped="the curiosity decisions differ by seed (the AI's goal sequence)"),
    "R5.NO_SPEEDRUN": _spec(GRADED, G + "+" + A, "NO SPEEDRUN (the time)", "#36"),
    "R5.NO_SPEEDRUN_DICE": _spec(GRADED, A, "NO SPEEDRUN, WITHOUT THE GRASS'S DICE", "#37"),
    "R5.LOSE3": _spec(GRADED, A + "+" + G + "+" + H, "LOSE3 (a copy", "#38"),
    "R5.PATIENCE": _spec(GRADED, G + "+" + A, "PATIENCE (STORY_PATIENCE", "#39"),
    "R5.PATIENCE_OLD": _spec(GRADED, G + "+" + H, "PATIENCE_OLD (the same", "#40 (critic Q1: by the game)"),
    "R5.PATIENCE_OLD_WORD": _spec(DIAGNOSTIC, A, "PATIENCE_OLD's own word", "#40 (its AI half)",
                                  dropped="PATIENCE_OLD stopped 'no progress for ...' WHILE TRAINING (the AI's reason and "
                                          "goal; the game's half, ended early without the POKéDEX, is R5.PATIENCE_OLD)"),
    # ---- rate_step5.chapter2_verdicts
    "R5.CH2_WALLY": _spec(GRADED, G, "CH2: WALLY's tutorial", "#41"),
    "R5.CH2_INTENT_MIX": _spec(REPORTED, A + "+" + G, "CH2: THE INTENT MIX", "#42", old_bound=True),
    "R5.CH2_FREE": _spec(REPORTED, A + "+" + G, "CH2: CURIOSITY THE STORY DID NOT NEED", "#43", old_bound=True),
    "R5.CH2_NEW_PLACE": _spec(HONESTY, A + "+" + G, "CH2: A NEW PLACE IS NEW", "#44"),
    "R5.CH2_WHITEOUTS": _spec(GRADED, G, "CH2: the game's whiteouts", "#45"),
    "R5.CH2_OFF_UNDER": _spec(REPORTED, A + "+" + G, "CH2_OFF (the beeline control's chapter 2)", "#46", old_bound=True),
    "R5.CH2_NOBATTLE": _spec(GRADED, A, "CH2: NO SPEEDRUN, WITHOUT THE GRASS'S DICE", "#47"),
    # ---- rate_step5.step52_verdicts
    "R5.CH1_YIELD": _spec(GRADED, G + "+" + A, "CH1: CURIOSITY BY YIELD", "#48"),
    "R5.CH2_YIELD": _spec(GRADED, G + "+" + A, "CH2: CURIOSITY BY YIELD", "#49"),
    "R5.NO_LOAFING": _spec(GRADED, G + "+" + A, "NO LOAFING", "#50"),
    "R5.YIELD_AGREE": _spec(DIAGNOSTIC, A + "+" + G, "(reported) the AI's own word on its curiosity's yield", "#51",
                            dropped="the AI's yield verdict agrees with the game's (true by construction while the AI "
                                    "computes the grader's own 8/20 rule)"),
    "R5.LOAF": _spec(GRADED, G + "+" + A, "LOAF (the control", "#52"),
    "R5.OFF_REPORTED": _spec(REPORTED, G + "+" + A, "(reported) ERRANDS_OFF, the beeline", "#53"),
    "R5.SPACED": _spec(DIAGNOSTIC, A, "CURIOSITY SPACED", "#54",
                       dropped="at most SPACING_ROW_MAX curiosity goals in a row (goal KINDS: no game form)"),
    "R5.GREEDY": _spec(DIAGNOSTIC, A, "GREEDY (the control", "#55",
                       dropped="the GREEDY control over the spacing bound (goal KINDS: no game form)"),
    "R5.DETOURS_ARRIVE": _spec(HONESTY, A + "+" + G, "DETOURS THAT ARRIVE", "#56"),
    "R5.DETOUR_WORD": _spec(HONESTY, A + "+" + G, "THE DETOUR'S WORD IS TRUE", "#57"),
    "R5.PUSHING": _spec(GRADED, A + "+" + G, "THE PUSHING PROPERTY (every run", "#58"),
    "R5.PUSH_PATHS_AGREE": _spec(HONESTY, A + "+" + G, "THE TWO PATHS AGREE on the pushing verdict", "#59"),
    "R5.BLOCKED": _spec(GRADED, A + "+" + G, "BLOCKED (the control", "#60"),
    "R5.LEFT_NOT_NEW": _spec(HONESTY, A + "+" + G, "A PLACE IT HAS LEFT IS NO NEW PLACE", "#61"),
    "R5.ASK_STEP": _spec(DIAGNOSTIC, A, "THE ASK STEP WALKS TO ITS HOUSE", "#62",
                         dropped="the ask step never walks with nothing said (the AI's goal reasons)"),
    "R5.PLACES_READ": _spec(GRADED, G, "THE GAME'S PLACES (second path) were read", "#63"),
    # (build step 5.3, stage A2 carry-over 2) the harness's row errors: no plan of the sweep can hide by never playing
    "R5.PLANS_PLAYED": _spec(GRADED, H, "EVERY PLAN PLAYED", "A2 carry-over 2"),
    "R5.OUT_OF_IDEAS": _spec(DIAGNOSTIC, A, "OUT OF IDEAS ONLY WITH NO LEAD", "#64",
                             dropped="no led run ends 'out of ideas' (the AI's reason)"),
    "R5.NOHINTS_IDEAS": _spec(REPORTED, A, "(reported) NOHINTS (no hint ever used)", "#65"),
    "R5.CHATS_IDLE": _spec(REPORTED, G + "+" + A, "(reported) the chats the GAME says told it nothing new", "#66"),
    "R5.TALKS_PATHS": _spec(REPORTED, A + "+" + G, "(reported) THE TWO PATHS ON THE TALKS", "#67"),
    # ---- live_step5 (and the purity checks of `live_step2.check_purity`, which it calls)
    "L5.PURITY_GATE": _spec(GRADED, H, "the launcher gated the real package", "live_step2 check_purity"),
    "L5.PURITY_CLEAN": _spec(GRADED, H, "verdict file: verdict=", "live_step2 check_purity"),
    "L5.PURITY_PRESSES": _spec(GRADED, A + "+" + H, "ai_presses=", "live_step2 check_purity"),
    "L5.PURITY_FRAMES": _spec(GRADED, A + "+" + H, "the AI pad's own frame count", "live_step2 check_purity"),
    "L5.PURITY_BREACHES": _spec(GRADED, H, "every breach counter 0", "live_step2 check_purity"),
    # (A1 fix round, the stage-A1 verifier's failure 3) `exit_reason` is the HARNESS's text only when it stopped the run on
    # its frame budget or its wall clock; for a clean exit it is the BRAIN's own reason (`host/lifecycle.py` writes the
    # reason the play loop returned), so the AI's text can flip this check: it reads `ai` (B1 debt; A2: the end cause from
    # the harness's own record)
    "L5.PURITY_ENDED": _spec(GRADED, H + "+" + A, "ended by itself", "live_step2 check_purity"),
    "L5.PURITY_OUTCOME": _spec(GRADED, A, "the brain's outcome", "live_step2 check_purity"),
    "L5.PURITY_PACKAGE": _spec(GRADED, H, "the verdict file names the package that ran", "live_step2 check_purity"),
    "L5.THIS_RUN": _spec(GRADED, H + "+" + G, "the state graded is the one THIS run wrote", "L:332"),
    "L5.PRESS_GATES": _spec(GRADED, A, "THE PRESSES:", "L:342"),
    "L5.A_KINDS": _spec(GRADED, A, "EVERY A press is a WAIT", "L:354"),
    "L5.BLIND": _spec(GRADED, A, "no press without the eyes asked", "L:357"),
    # (A1 fix round, the coordinator's ruling F4) the live twins of R5.CH1_CATCH_ALL, R5.ASIDE_BACK and R5.GO_AFTER_PAGE
    # are DIAGNOSTIC like them: the spec says these properties have NO game form, so a B1 debt row for them could never be
    # paid (a launcher run has no second path while it plays)
    "L5.CATCH_ALL": _spec(DIAGNOSTIC, A, "THE CATCH-ALL:", "L:360",
                          dropped="a live arm's idle stretches under the catch-all reason (the AI's own reason labels; no "
                                  "game form, as R5.CH1_CATCH_ALL)"),
    "L5.HAS_GOAL": _spec(GRADED, A, "NEVER WITHOUT A GOAL", "L:363"),
    "L5.STALL": _spec(GRADED, A, "THE STALL PROPERTY (its record", "L:373"),
    "L5.GO_AFTER_PAGE": _spec(DIAGNOSTIC, A, "EVERY GO GOAL WITH A MAP CAME AFTER THE PAGE", "L:379",
                              dropped="a live arm's go goals after the page that told them (the AI's read records; no game "
                                      "form, as R5.GO_AFTER_PAGE)"),
    "L5.NO_LOAFING": _spec(DIAGNOSTIC, A, "NO LOAFING (its record", "L:389",
                           dropped="a live arm's loafing by its own record (its 5.2 AI-only checks; the sweep grades the "
                                   "game's)"),
    "L5.SPACED": _spec(DIAGNOSTIC, A, "CURIOSITY SPACED", "L:399",
                       dropped="a live arm's curiosity spacing (goal KINDS: no game form)"),
    "L5.PUSHING": _spec(DIAGNOSTIC, A, "THE PUSHING PROPERTY (its record", "L:404",
                        dropped="a live arm's pushing by its own record (the sweep grades both paths)"),
    "L5.ASK_STEP": _spec(DIAGNOSTIC, A, "THE ASK STEP WALKS TO ITS HOUSE", "L:412",
                         dropped="a live arm's ask step (the AI's goal reasons)"),
    "L5.NEW_PLACE": _spec(GRADED, A, "A NEW PLACE IS NEW", "L:474"),
    "L5.ASIDE_BACK": _spec(DIAGNOSTIC, A, "A STORY GOAL PUT ASIDE COMES BACK", "L:435",
                           dropped="a live arm's story goal put aside comes back within ASIDE_STREAK_MAX (the AI's goal "
                                   "keys; no game form, as R5.ASIDE_BACK)"),
    "L5.BOUNDED": _spec(GRADED, H, "BOUNDED:", "L:583"),
    "L5.CH1_PROOFS": _spec(GRADED, G, "THE GAME (save block 1", "L:594"),
    "L5.NAME_GENDER": _spec(HONESTY, A + "+" + G, "THE GAME (save block 2)", "L:596"),
    "L5.STARTER_OT": _spec(GRADED, G + "+" + H, "THE GAME (the framework's party decoder)", "L:603"),
    "L5.BALLS": _spec(GRADED, G, "THE GAME (the bag)", "L:607"),
    "L5.TRAINED": _spec(GRADED, A, "TRAINED BEFORE THE RIVAL", "L:623"),
    "L5.REST_RULE": _spec(GRADED, A, "THE REST RULE (its log)", "L:529"),
    "L5.OWN_LOSSES": _spec(GRADED, A, "ITS END LINE'S LOSSES", "L:554"),
    "L5.OWN_TRAINING": _spec(GRADED, A, "ITS END LINE'S TRAINING", "L:562"),
    "L5.TOLD_WILD": _spec(HONESTY, A + "+" + G, "THE GAME AGREES WITH ITS COUNT", "L:634"),
    "L5.SPINS": _spec(GRADED, A, "ROAMING, NOT SPINNING", "L:641"),
    "L5.CH2_WALLY": _spec(GRADED, G, "THE GAME: WALLY's tutorial", "L:655"),
    "L5.CAUGHT": _spec(GRADED, G, "CAUGHT:", "L:664"),
    "L5.HEALED": _spec(GRADED, G, "HEALED:", "L:668"),
    "L5.ITEMS": _spec(GRADED, G, "ITEMS:", "L:670"),
    "L5.SHOPPED": _spec(GRADED, A, "SHOPPED (its told purchase)", "L:674"),
    "L5.FROZEN": _spec(GRADED, H, "FROZEN TREE", "L:758"),
    "L5.POOLED_SPINS": _spec(DIAGNOSTIC, A, "the CH1 arms' spins together", "L:769-777",
                             dropped="the CH1 arms' spins pooled under 2 % of their roam steps (the AI's roam reports)"),
    "L5.REST_OCCASIONS": _spec(DIAGNOSTIC, A, "the CH1 arms' occasions for the rest rule together", "L:773-780",
                               dropped="the CH1 arms had at least one rest-rule occasion (the AI's battle records)"),
}
#: (build step 5.3, A1-4: the step-5.3 critic's Q6 and Q7 item 1) the `rate_step5.BOUNDS` keys that ONLY checks which never
#: count read (REPORTED or DIAGNOSTIC since A1-1), in either grader: key -> those checks. A bound read by no counting check
#: bounds nothing the verdict counts, so a lesson may not name it as Enforced (`check_lessons.py`); it names it on its
#: Reported line. Found by a scan of every `BOUNDS[...]` read in `rate_step5.py` and `live_step5.py` (2026-10-23), and held
#: to the code by `test_step53_a1.UngradedBoundTests` (tightening each one moves no verdict of the healthy sweep while it
#: moves its own checks; tightening a graded bound fails the sweep). ASIDE_STREAK_MAX joined it in the A1 fix round, when
#: its live reader `L5.ASIDE_BACK` became DIAGNOSTIC like `R5.ASIDE_BACK` (ruling F4); a key read by one counting check and
#: one that does not count (LOAF_FRAMES_MAX: R5.NO_LOAFING GRADED, L5.NO_LOAFING DIAGNOSTIC) stays out.
UNGRADED_BOUNDS: dict[str, tuple[str, ...]] = {
    "ASIDE_STREAK_MAX": ("R5.ASIDE_BACK", "L5.ASIDE_BACK"),
    "CH2_OFF_UNDER_MIN": ("R5.CH2_OFF_UNDER",),
    "CURIOSITY_MIN": ("R5.CH1_INTENT_MIX",),
    "CUR_DIV_MIN": ("R5.ERRANDS_DIFFER",),
    "FREE_CONTROL_FAILS_MIN": ("R5.BEELINE_FAILS_FREE",),
    "FREE_MEAN_MIN": ("R5.CH1_FREE",),
    "FREE_RUN_MIN": ("R5.CH1_FREE", "R5.BEELINE_FAILS_FREE", "R5.CH2_FREE"),
    "GREEDY_FAILS_MIN": ("R5.GREEDY",),
    "MIX_DROP_MIN": ("R5.OFF_MOVES_MIX",),
    "MIX_MIN": ("R5.CH1_INTENT_MIX", "R5.CH2_INTENT_MIX", "R5.CH2_OFF_UNDER"),
    "OUT_OF_IDEAS_LED_MAX": ("R5.OUT_OF_IDEAS",),
    "SPACING_ROW_MAX": ("R5.SPACED", "R5.GREEDY", "L5.SPACED"),
}


# ---------------------------------------------------------------------------------------------------------------- THE FILES
def load_debt(path: Path = DEBT_FILE) -> dict[str, dict]:
    """`b1_debt.json`: id -> {"ai_input": what AI input it reads, "plan": the A2 plan}. Every entry must name both."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    debt = data.get("debt")
    if not isinstance(debt, dict):
        raise CheckError(f"{path}: no 'debt' object")
    for key, entry in debt.items():
        if not isinstance(entry, dict) or not str(entry.get("ai_input") or "").strip() or not str(entry.get("plan") or "").strip():
            raise CheckError(f"{path}: debt entry {key!r} must name its 'ai_input' and its A2 'plan'")
    return debt


def load_waivers(path: Path = WAIVERS_FILE) -> dict[str, dict]:
    """`grader_waivers.json`: id -> {"reason": why a VACUOUS result of it may pass}. A waiver without a reason is refused."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    waivers = data.get("waivers")
    if not isinstance(waivers, dict):
        raise CheckError(f"{path}: no 'waivers' object")
    for key, entry in waivers.items():
        if not isinstance(entry, dict) or not str(entry.get("reason") or "").strip():
            raise CheckError(f"{path}: waiver {key!r} has no reason")
    return waivers


def rule_problems(check_id: str, kind: str, inputs: frozenset, debt: dict) -> list[str]:
    """THE TYPING RULES of one check (empty: it obeys them)."""
    problems = []
    if kind not in KINDS:
        problems.append(f"{check_id}: unknown kind {kind!r} (one of {KINDS})")
    if not inputs or not inputs <= INPUTS:
        problems.append(f"{check_id}: inputs {sorted(inputs)} must be a non-empty subset of {sorted(INPUTS)}")
    if kind == GRADED and AI in inputs and check_id not in debt:
        problems.append(f"{check_id}: a GRADED check that reads an AI input must be listed in b1_debt.json")
    if kind == HONESTY and not {AI, GAME} <= inputs:
        problems.append(f"{check_id}: a HONESTY check judges the AI's word against the game: it must name both ai and "
                        f"game, not {sorted(inputs)}")
    return problems


def validate(checks: dict[str, Spec], debt: dict, waivers: dict) -> None:
    """The table against both files, both ways: every row obeys the rules; every debt entry is a GRADED check that reads
    the AI (no stale debt: a paid debt leaves the file); every waiver names a known id; no title is the start of another
    title of the same grader (`as_check` resolves by the start)."""
    problems = [p for key, spec in checks.items() for p in rule_problems(key, spec.kind, spec.inputs, debt)]
    for key in debt:
        spec = checks.get(key)
        if spec is None or spec.kind != GRADED or AI not in spec.inputs:
            problems.append(f"b1_debt.json lists {key!r}, which is not a GRADED check that reads an AI input")
    problems += [f"grader_waivers.json waives {key!r}, which is no check" for key in waivers if key not in checks]
    for key, spec in checks.items():
        problems += [f"{key}'s title is the start of {other}'s" for other, them in checks.items()
                     if other != key and other[:3] == key[:3] and them.title.startswith(spec.title)]
    problems += [f"{key}: a dropped property on a {spec.kind} check" for key, spec in checks.items()
                 if spec.dropped and spec.kind != DIAGNOSTIC]
    # (A1-4) an ungraded bound's readers are checks of the table that never count
    problems += [f"UNGRADED_BOUNDS[{bound!r}] names {key!r}, which is no check or one that counts"
                 for bound, keys in UNGRADED_BOUNDS.items() for key in keys
                 if key not in checks or checks[key].kind in COUNTED]
    if problems:
        raise CheckError("; ".join(problems))


DEBT = load_debt()
WAIVERS = load_waivers()
validate(CHECKS, DEBT, WAIVERS)


# ---------------------------------------------------------------------------------------------------------------- THE TYPE
class Check(tuple):
    """`Check(id, kind, status, n, floor, inputs, text)`. It IS a 2-tuple `(ok, text)` for the tuple consumers (module
    docstring, THE TWO TUPLE VIEWS); `view_ok` sets that bool (None: `status == PASS`). Construction raises `CheckError`
    when the typing rules are broken (`rule_problems`, against `debt`, by default `b1_debt.json`)."""

    def __new__(cls, check_id: str, kind: str, status: str, n: int | None, floor: int | None, inputs, text: str, *,
                view_ok: bool | None = None, debt: dict | None = None):
        inputs = frozenset(inputs)
        problems = rule_problems(check_id, kind, inputs, DEBT if debt is None else debt)
        if status not in STATUSES:
            problems.append(f"{check_id}: unknown status {status!r} (one of {STATUSES})")
        if problems:
            raise CheckError("; ".join(problems))
        self = super().__new__(cls, (status == PASS if view_ok is None else bool(view_ok), text))
        self.id, self.kind, self.status, self.n, self.floor, self.inputs, self.text = (
            check_id, kind, status, n, floor, inputs, text)
        return self

    def __repr__(self) -> str:
        return f"Check({self.id!r}, {self.kind}, {self.status}, n={self.n}, floor={self.floor}, {self.text[:60]!r})"


def status_of(ok: bool, n: int | None, floor: int | None) -> str:
    """VACUOUS when the check saw fewer than `floor` samples (whatever `ok` says: a check with no sample reads nothing),
    else PASS or FAIL by `ok`. A check with no floor cannot be vacuous."""
    if floor is not None and (n is None or n < floor):
        return VACUOUS
    return PASS if ok else FAIL


def grade(check_id: str, ok: bool, text: str, n: int | None = None, floor: int | None = None) -> Check:
    """A check of the table: its kind and inputs from `CHECKS`, its status by `status_of`. A GRADED or HONESTY check must
    give its sample count `n` and its `floor` (a count it may not go under and still say something): no check that counts
    can pass on zero samples. Its text must START with its id's title."""
    spec = CHECKS.get(check_id)
    if spec is None:
        raise CheckError(f"{check_id!r} is no check of the table (`grader_checks.CHECKS`)")
    if not text.startswith(spec.title):
        raise CheckError(f"{check_id}: its text must start with its title {spec.title!r}: {text[:80]!r}")
    if spec.kind in COUNTED and (n is None or floor is None):
        raise CheckError(f"{check_id}: a {spec.kind} check must give its sample count n and its floor")
    return Check(check_id, spec.kind, status_of(ok, n, floor), n, floor, spec.inputs, text)


def as_check(item, grader: str) -> Check:
    """A Check unchanged; a legacy `(ok, text)` tuple typed by the start of its text among `grader`'s ids ("R5" or "L5"),
    with no sample count (it gives none). RAISES for a text no title of that grader starts: an untyped check never
    reaches a verdict."""
    if isinstance(item, Check):
        return item
    ok, text = item
    found = [key for key, spec in CHECKS.items() if key.startswith(grader + ".") and str(text).startswith(spec.title)]
    if len(found) != 1:
        raise CheckError(f"an untyped check of {grader} (no id, and its text starts no title of the table): {str(text)[:100]!r}")
    spec = CHECKS[found[0]]
    return Check(found[0], spec.kind, PASS if ok else FAIL, None, None, spec.inputs, str(text))


# ---------------------------------------------------------------------------------------------------------------- THE VERDICT
def waived(check: Check, waivers: dict | None = None) -> bool:
    """A VACUOUS check whose id has a waiver (with a reason) in `grader_waivers.json`."""
    return check.status == VACUOUS and check.id in (WAIVERS if waivers is None else waivers)


def counts_ok(check: Check, waivers: dict | None = None) -> bool:
    """Whether this check lets the verdict PASS: a DIAGNOSTIC or REPORTED check always (it never counts); a GRADED or
    HONESTY check when it PASSED, or was VACUOUS with a waiver."""
    if check.kind not in COUNTED:
        return True
    return check.status == PASS or waived(check, waivers)


def verdict(checks, waivers: dict | None = None) -> str:
    """THE VERDICT: PASS iff at least one check, and every GRADED and HONESTY check is PASS (or a waived VACUOUS)."""
    checks = list(checks)
    return "PASS" if checks and all(counts_ok(c, waivers) for c in checks) else "FAIL"


def verdict_row(check: Check, waivers: dict | None = None) -> Check:
    """The VERDICT view of a check (module docstring): its tuple bool is `counts_ok`; a REPORTED share of frames that keeps
    its old 5.2 bound (`Spec.old_bound`) says whether that bound held, as 5.2's `p2_reported` wrote it."""
    text = check.text
    if check.kind == REPORTED and CHECKS[check.id].old_bound:
        text = (f"(reported, 5.2 P2: a share of frames is not graded; the old bound "
                f"{'HELD' if check.status == PASS else 'did NOT hold'}) {text}")
    return Check(check.id, check.kind, check.status, check.n, check.floor, check.inputs, text,
                 view_ok=counts_ok(check, waivers))


def evidence_lines(checks, waivers: dict | None = None, debt: dict | None = None) -> list[str]:
    """One line per check (`[status] id kind n/floor inputs: text`, a waived VACUOUS marked), then one `B1 DEBT` line per
    GRADED check here that reads an AI input (`b1_debt.json`: the input and the A2 plan), then one `NO LONGER GRADED` line
    per DIAGNOSTIC check A1 reclassified (the property the grade no longer counts)."""
    debt = DEBT if debt is None else debt
    checks = list(checks)
    lines = []
    for c in checks:
        mark = " (WAIVED)" if waived(c, waivers) else ""
        count = f"{'-' if c.n is None else c.n}/{'-' if c.floor is None else c.floor}"
        lines.append(f"  [{c.status}]{mark} {c.id} {c.kind} n/floor {count} inputs {'+'.join(sorted(c.inputs))}: {c.text}")
    seen = []
    for c in checks:
        if c.id in debt and c.id not in seen:
            seen.append(c.id)
            # the plan is printed as written: every plan of `b1_debt.json` names its stage itself ("A2: ...", "A2
            # (coordinator): ..."), so a prefix here printed "A2: A2:" (the stage-A1 verifier's weak proof)
            lines.append(f"B1 DEBT {c.id} ({c.status}): reads the AI's {debt[c.id]['ai_input']}; plan: {debt[c.id]['plan']}")
    dropped = []
    for c in checks:
        spec = CHECKS[c.id]
        if spec.dropped and c.id not in dropped:
            dropped.append(c.id)
            lines.append(f"NO LONGER GRADED {c.id} ({c.status}, DIAGNOSTIC since 5.3 A1): {spec.dropped}")
    return lines
