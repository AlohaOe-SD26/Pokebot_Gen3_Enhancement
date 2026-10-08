"""SKILL: get away from a WILD battle by choosing RUN (build step 3, a minimal battle skill until step 4's battle
decider; design draft §6 build order).

WHAT A PERSON DOES: reads "Wild WURMPLE appeared!" and "Go! MUDKIP!", and when the four choices come up (FIGHT / BAG /
POKéMON / RUN) moves the cursor to RUN and presses A; "Got away safely!" is read and moved on. If the foe is faster
the run can fail ("Can't escape!"), the foe attacks, and the choices come back: they try again, a few times.

HOW: the text is advanced ONLY on the eyes' waits (`hands/dialogue.py` advance: the museum-greeter rule), and the
action menu's cursor is READ, never counted (`eyes/screens.py` battle_action: `gActionSelectionCursor`, a 2 x 2
grid; `choose_in_grid` moves one step at a time toward RUN and presses A only on a look that shows the cursor ON it).
A TRAINER battle cannot be fled (`src/battle_util.c`: "No! There's no running from a TRAINER battle!"), and fighting
is step 4: the skill returns `TRAINER_OUT_OF_SCOPE` on the first look at the choices, having pressed nothing on them.
Every loop is bounded; a run that cannot get away within `FLEE_ATTEMPTS` choices returns a reason.
"""

from __future__ import annotations

from collections.abc import Generator

from ai_player.eyes.observation import Observation
from ai_player.hands.dialogue import advance, player_free
from ai_player.hands.pad import Hands

__all__ = [
    "BATTLE_ACTION",
    "FLEE_ATTEMPTS",
    "FLEE_BUDGET",
    "RUN",
    "TRAINER_OUT_OF_SCOPE",
    "battle_over",
    "choose_in_grid",
    "flee",
    "in_battle",
]

#: The battle's action menu (`eyes/screens.py` BATTLE_ACTIONS) and RUN's place in it (B_ACTION_RUN, bottom-right).
BATTLE_ACTION = "battle_action"
RUN = 3
#: How many times RUN is chosen before the skill gives up (a failed run gives the foe a turn each time).
FLEE_ATTEMPTS = 8
#: The longest one stretch of the battle's text and animations may take (one `advance`).
FLEE_BUDGET = 3600
#: Presses to bring the grid cursor to RUN (two at most are needed), and frames for the menu to take the A.
GRID_PRESSES = 8
CONFIRM_FRAMES = 60
TRAINER_OUT_OF_SCOPE = ("a trainer battle: out of scope for step 3 (a trainer cannot be fled, and fighting is step 4's "
                        "battle decider)")


def in_battle(look: Observation) -> bool:
    screen = look.screen
    return screen.in_battle or screen.game_state in ("BATTLE", "BATTLE_STARTING", "BATTLE_ENDING")


def battle_over(look: Observation) -> bool:
    """Back on the map and free to walk (no fade still running)."""
    return not in_battle(look) and player_free(look) and not look.screen.fading


def choose_in_grid(hands: Hands, kind: str, index: int, why: str) -> Generator[None, None, bool]:
    """Bring a 2 x 2 menu's cursor (bit 0 the column, bit 1 the row) to `index` by READING it, one press at a time, and
    press A only on a look that shows it there. True once the menu has closed after the A."""
    thought = False
    for _ in range(GRID_PRESSES):
        look = hands.look()
        ui = look.screen.ui
        if ui is None or ui.kind != kind:
            hands.tell(f"{why}: the {kind} closed before the choice")
            return False
        if not ui.accepts_input or ui.cursor is None:
            yield from hands.pad.busy(f"waiting for the {kind} to take input")
            continue
        names = ui.options
        if not thought:
            thought = True
            yield from hands.pad.idle(hands.pad.think_frames(), f"looking at the {kind}: {list(names)}, cursor on "
                                                                f"{ui.cursor} ({names[ui.cursor]}); wanted {names[index]}")
            continue
        if ui.cursor == index:
            yield from hands.pad.press("A", why, f"{kind} cursor on {index} ({names[index]})")
            for _ in range(CONFIRM_FRAMES):
                look = hands.look()
                if look.screen.ui is None or look.screen.ui.kind != kind:
                    return True
                yield from hands.pad.busy(f"waiting for the {kind} to take the choice")
            continue  # the A was dropped: look again, press again (bounded)
        if (ui.cursor ^ index) & 1:
            button = "Right" if index & 1 else "Left"
        else:
            button = "Down" if index & 2 else "Up"
        yield from hands.pad.press(button, why, f"{kind} cursor on {ui.cursor} ({names[ui.cursor]}), wanted {index} "
                                                f"({names[index]}): one step {button.lower()}")
    hands.tell(f"{why}: the {kind} cursor did not reach {index} in {GRID_PRESSES} presses")
    return False


def flee(hands: Hands, why: str = "get away from the wild Pokemon") -> Generator[None, None, str]:
    """Returns "fled" (RUN chosen, back on the map), "the battle ended" (it ended without a RUN), TRAINER_OUT_OF_SCOPE,
    or what went wrong."""
    look = hands.look()
    if not in_battle(look):
        return "no battle"
    tries = 0
    foe = None
    for _ in range(3 * FLEE_ATTEMPTS):
        outcome = yield from advance(hands, battle_over, why, budget=FLEE_BUDGET)
        if outcome == "done":
            hands.tell(f"flee: {'got away' if tries else 'the battle ended'} from {foe or 'the battle'} after {tries} RUN "
                       f"choice(s), at f{hands.last.frame}")
            return "fled" if tries else "the battle ended"
        if outcome == f"menu:{BATTLE_ACTION}":
            battle = hands.last.battle
            if battle is not None and battle.kind == "trainer":
                hands.tell(f"flee: {TRAINER_OUT_OF_SCOPE} (trainer {battle.opponent_trainer_id})")
                return TRAINER_OUT_OF_SCOPE
            if battle is not None and battle.foe:
                foe = f"a wild {battle.foe[0].species} L{battle.foe[0].level}"
            if tries >= FLEE_ATTEMPTS:
                return f"could not get away in {tries} tries"
            tries += 1
            if not (yield from choose_in_grid(hands, BATTLE_ACTION, RUN, f"{why}: RUN from {foe or 'the foe'} (try {tries})")):
                return "RUN could not be chosen"
            continue
        if outcome.startswith("menu:"):
            return f"an unexpected {outcome[5:]} in the battle"
        return f"the battle: {outcome}"
    return "the battle did not end"
