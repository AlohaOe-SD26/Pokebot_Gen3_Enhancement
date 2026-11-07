"""SKILL: play a battle to its end with the AI's own decider and hands (build step 4; it replaces `skills/flee.py` for the
brains that battle: the world brains of step 3 still flee). Framework-free.

WHAT A PERSON DOES: reads the battle's texts ("Wild ZIGZAGOON appeared!", "MUDKIP used WATER GUN!", "It's super
effective!") and, whenever the game asks, decides: at FIGHT / BAG / POKéMON / RUN what to do this turn (the decider,
`brain/battle.py`); in the move grid which move; in the bag which ball or potion, and USE; in the party menu who goes
in, and SHIFT / SEND OUT; at a yes/no ("Use next POKéMON?", "Will ... change POKéMON?", "Delete a move to make room for
...?", "Stop learning ...?", a nickname) the answer by its words; in the summary screen which move to forget. A
level-up's stats box is pressed through; an EVOLUTION is let happen (nothing is pressed while it plays: B would stop it).

HOW: every text is advanced ONLY on the eyes' waits (`hands/dialogue.py` advance: the museum-greeter rule); every cursor
is READ and moved one step at a time (`skills/flee.py` choose_in_grid for the two 2 x 2 grids, `hands/menus.py`
choose / move_cursor for the lists), and A is pressed only on a look showing it on the option. Every decision is logged
with its reason (`[AI-HANDS] battle: ...`), and every loop is bounded (`BATTLE_STEPS` menus, `TEXT_BUDGET` frames a
stretch of text, `ITEM_STEPS` presses in the bag, `SEND_IN_TRIES` choices in the party menu). The outcome is the game's
own (`gBattleOutcome` on the look after the battle: won, lost, ran, caught, ...).

THE FIELD AND THE PARTY MENU'S REFUSAL (the step-4 verifier's round). The party menu covers the battle, so the decider is
shown every look the hands take (a watcher: `BattleMind.see`) and REMEMBERS the field from the last look at the battle
(who stands there, whom it faces), and the skill tells it whom it sent in (`BattleMind.sent`). When the game still refuses
a choice, the party menu prints its words ("GROVYLE is already in battle!", "CASTFORM has no energy left to battle!":
printer 6, a WAIT) and takes no input until A: the skill READS them (`_read_message`: the reading delay, then A on the
look's wait), tells the decider who was refused (the member it chose, or the one under the menu's cursor when the
message was on screen before any choice of its own), and chooses again. Until this round the skill watched that message
for `MENU_SETTLE_BUDGET` frames and gave up: "the party on screen neither took input nor closed".

STEP 4.1. The shift question ("TRAINER X is about to use TREECKO. Will ... change POKéMON?") is answered with the pages
before it (the decider reads the next foe from the words; the battle view still holds the fainted one), and the party
menu after a YES gets the member chosen there (`BattleMind.replacement`). When the move grid comes back after a move was
chosen, the game REFUSED that move (Disabled, Taunt, no PP): the decider is told (`BattleMind.cannot_use`) before it
decides again, so it cannot choose the same move until the battle's bound. A healing item's target is given by
`_give_item`, which READS the party menu's message after it ("MUDKIP's HP was restored by 17 point(s)."): the HEAL arm's
first development run found the skill stuck there ("the Potion could not be given", the Potion used and the HP restored).
"""

from __future__ import annotations

import re
from collections.abc import Generator

from ai_player.brain.battle import BattleMind, Decision, LearnChoice, learn_choice
from ai_player.eyes.observation import Observation
from ai_player.eyes.screens import BAG_POCKETS, page_text
from ai_player.hands.dialogue import STUCK, advance, new_characters, player_free
from ai_player.hands.menus import choose, move_cursor, wait_for_ui
from ai_player.hands.pad import Hands
from ai_player.knowledge.facts import move_named
from ai_player.skills.flee import BATTLE_ACTION, battle_over, choose_in_grid, in_battle

__all__ = [
    "BATTLE_MOVE",
    "BATTLE_STEPS",
    "BATTLE_TARGET",
    "BATTLE_YES_NO",
    "ITEM_STEPS",
    "OUTCOMES",
    "TEXT_BUDGET",
    "battle_done",
    "play_battle",
]

BATTLE_MOVE = "battle_move"
BATTLE_TARGET = "battle_target"
BATTLE_YES_NO = "battle_yes_no"
#: A double battle's target: frames to see whether the game asks for one, presses to reach it.
TARGET_WAIT = 90
TARGET_PRESSES = 6
#: Menus answered in one battle, at most (a long battle has a few dozen).
BATTLE_STEPS = 150
#: The longest one stretch of a battle's texts and animations may take (one `advance`; an evolution included).
TEXT_BUDGET = 5400
#: Presses to find a pocket and an item in the bag; frames for the bag to close after USE.
ITEM_STEPS = 24
BAG_CLOSE_BUDGET = 240
#: Frames a menu may stay on screen without taking input (opening, closing) before it is reported stuck.
MENU_SETTLE_BUDGET = 600
#: (the step-4 verifier's round) Choices in the party menu after a faint, at most (each refused one is not chosen again).
SEND_IN_TRIES = 6
#: The party menu's refusals (`src/strings.c` gText_PkmnAlreadyInBattle "{STR_VAR_1} is already in battle!",
#: gText_PkmnHasNoEnergy "... has no energy left to battle!", gText_PkmnAlreadySelected "... has already been selected.",
#: gText_PkmnCantSwitchOut "... can't be switched out!"; the eyes join the lines with a space): the name before the words
#: is the Pokemon refused.
_REFUSED = re.compile(r"^(.+?) (?:is already|has no energy|has already been|can't be switched|can't battle)", re.I)
#: `include/constants/battle.h` B_OUTCOME_*: what `gBattleOutcome` says after the battle.
OUTCOMES = {1: "won", 2: "lost", 3: "drew", 4: "ran", 5: "teleported", 6: "the foe fled", 7: "caught",
            8: "no safari balls", 9: "forfeited", 10: "the foe teleported"}
_TRYING = re.compile(r"(.+?) is trying to learn (.+?)[.!]", re.I)
_ROOM = re.compile(r"make room for (.+?)\?", re.I)
_STOP = re.compile(r"stop learning (.+?)\?", re.I)


def battle_done(look: Observation) -> bool:
    """Back on the map and free (`skills/flee.py` battle_over): the battle, its level-ups and any evolution are over."""
    return battle_over(look)


class _Pages:
    """Every page of text the eyes showed during the battle (a watcher on the hands' looks): the learn-a-move question's
    earlier page names the Pokemon ("MUDKIP is trying to learn BIDE.")."""

    def __init__(self) -> None:
        self.pages: list[str] = []

    def __call__(self, look: Observation) -> None:
        page = page_text(look.screen.text) if look.screen.text else None
        if page and (not self.pages or self.pages[-1] != page):
            self.pages.append(page)
            del self.pages[:-40]


def play_battle(hands: Hands, mind: BattleMind, why: str = "win the battle") -> Generator[None, None, str]:
    """Play the battle on screen to its end (module docstring). Returns the game's outcome ("won", "caught", "ran",
    "lost", ...), or what went wrong ("stuck:...", "the battle: ...")."""
    look = hands.look()
    if not in_battle(look):
        return "no battle"
    pages = _Pages()
    field = _Field(mind)
    mind.enter()
    field(look)
    hands.watchers.append(pages)
    hands.watchers.append(field)
    try:
        return (yield from _play(hands, mind, why, pages))
    finally:
        hands.watchers.remove(pages)
        hands.watchers.remove(field)


class _Field:
    """(the step-4 verifier's round) Shows the decider every look the hands take during the battle (`BattleMind.see`): the
    last look AT the battle is the field it remembers once the party menu covers it."""

    def __init__(self, mind: BattleMind) -> None:
        self.mind = mind

    def __call__(self, look: Observation) -> None:
        self.mind.see(look)


def _play(hands: Hands, mind: BattleMind, why: str, pages: _Pages) -> Generator[None, None, str]:
    began = False
    learn: LearnChoice | None = None
    learn_key: str | None = None
    for _ in range(BATTLE_STEPS):
        outcome = yield from advance(hands, battle_done, why, budget=TEXT_BUDGET)
        look = hands.last
        if not began and look.battle is not None and look.battle.foe:
            began = True
            hands.tell(f"battle: {mind.begin(look)}")
        if outcome == "done":
            result = OUTCOMES.get(look.last_battle_outcome, f"the battle ended (outcome {look.last_battle_outcome})")
            hands.tell(f"battle: over: {result} (gBattleOutcome {look.last_battle_outcome}); party "
                       f"{[(m.species, m.level, m.hp, m.max_hp) for m in look.party or ()]}")
            return result
        if outcome.startswith(STUCK) or outcome == "budget":
            ended = OUTCOMES.get(look.last_battle_outcome) if look is not None and not in_battle(look) else None
            if ended is not None:
                # (chapter 7 stops round 4, 2026-11-06; the likely mechanism of KI-131: its records agree; its own case not
                # re-run) the BATTLE is over by the game's own word
                # (gBattleOutcome: 0 while a battle runs) and the screen has left it: what held the screen past the
                # budget or the watchdog came AFTER it (level-ups and an evolution, then the map's own scene: a gym
                # leader's badge fanfare and words, which `battle_done` waits through because the player is not free).
                # The caller plays that scene as any other. MEASURED (probe #104): C2's win over BRAWLY ended "the
                # battle: budget" 5,411 frames after its last press (three level-ups, the leader's words, an evolution),
                # C3's "stuck: ... a scene plays" at the badge's fanfare; the game had set BADGE02_GET in both
                hands.tell(f"battle: over: {ended} (gBattleOutcome {look.last_battle_outcome}); what came after it held "
                           f"the screen ({outcome}): the scene after the battle is played on")
                return ended
            return f"the battle: {outcome}"
        kind = outcome[5:] if outcome.startswith("menu:") else outcome
        if kind == BATTLE_ACTION:
            if not began and look.battle is not None and look.battle.foe:
                began = True
                hands.tell(f"battle: {mind.begin(look)}")
            mind_foe = mind.memory.foe_key
            foe = look.battle.foe[0] if look.battle is not None and look.battle.foe else None
            if foe is not None and f"{foe.species}:{foe.level}" != mind_foe:
                hands.tell(f"battle: the foe is now {foe.species} L{foe.level}")
                mind.next_foe(look)
            battler = look.screen.ui.battler if look.screen.ui is not None else None
            decision = mind.decide(look, battler)
            # (the step-4 verifier's round) the battler position the decision is for (0, or 2 in a double battle) and what
            # the type chart changed in it (`brain/battle.py` TypeSay): the sweep pairs each with the move the GAME shows chosen
            hands.tell(f"battle: turn {mind.memory.turns}: {decision.action}"
                       f"{' ' + decision.move_name if decision.move_name else ''}"
                       f"{' ' + decision.ball if decision.ball else ''}{' ' + decision.item if decision.item else ''}: "
                       f"{decision.reason}" + (f" [{'; '.join(decision.values)}]" if decision.values else "")
                       + f" (battler {battler if battler is not None else 0})"
                       + (f" {decision.types.line()}" if decision.types is not None else ""))
            hands.note("decide", f"battle {decision.action}", decision.reason,
                       {"move": decision.move_name, "slot": decision.move_slot, "ball": decision.ball,
                        "switch_pid": decision.switch_pid, "item": decision.item, "values": list(decision.values),
                        "battler": battler if battler is not None else 0,
                        "types": None if decision.types is None else {"near": list(decision.types.near), "blind": decision.types.blind,
                                                                      "hurting": decision.types.hurting,
                                                                      "decisive": decision.types.decisive}})
            done = yield from _execute(hands, mind, decision, why)
            if done is not None:
                return done
            continue
        if kind == BATTLE_MOVE:
            # back in the move grid without a decision in hand: the game REFUSED the move it chose (Disabled, Taunt,
            # Torment, no PP: `src/battle_main.c` TrySetCantSelectMoveBattleScript prints why, then the grid again).
            # (Step 4.1) the decider is told, so that move is out of its values for the rest of the turn, and decides again
            battler = look.screen.ui.battler if look.screen.ui is not None else None
            words = pages.pages[-1] if pages.pages else ""
            refused = mind.cannot_use(words)
            hands.tell(f"battle: the move grid came back: {refused or 'a move'} cannot be used now ({words!r}): decide again "
                       f"(battler {battler if battler is not None else 0})")
            decision = mind.decide(look, battler, redecide=True)
            if decision.action != "fight" or decision.move_slot is None:
                # (step 4.1 review, finding 2) the SAME turn decided again is no fight (a catch whose only safe weakening
                # move was refused now throws a ball): back out of the move grid with B, as a person would, and carry the
                # decision out from the action menu. Never a give-up here.
                hands.tell(f"battle: the new decision is to {decision.action}, not a move: B back to the action menu")
                yield from hands.pad.press("B", why, f"battle: leave the move grid to {decision.action}")
                back = yield from wait_for_ui(hands, BATTLE_ACTION, why)
                if back is None:
                    return "the battle: the action menu did not come back after B"
                done = yield from _execute(hands, mind, decision, why)
                if done is not None:
                    return done
                continue
            hands.tell(f"battle: turn {mind.memory.turns}: fight {decision.move_name}: {decision.reason} (battler "
                       f"{battler if battler is not None else 0})")
            if not (yield from choose_in_grid(hands, BATTLE_MOVE, decision.move_slot, f"{why}: {decision.reason}")):
                return "the battle: the move could not be chosen"
            mind.chose(battler, decision.move_name)
            if not (yield from _aim(hands, decision, why)):
                return "the battle: the target could not be chosen"
            continue
        if kind == BATTLE_TARGET:
            # a target asked for without a decision in hand: the foe with the lowest bar (finish it)
            foes = sorted(look.battle.foe if look.battle is not None else (), key=lambda f: (f.hp_bar, f.battler or 0))
            aim = Decision("fight", "a target asked for: the foe with the lowest bar", target=foes[0].battler if foes else None)
            if not (yield from _aim(hands, aim, why)):
                return "the battle: the target could not be chosen"
            continue
        if kind == BATTLE_YES_NO:
            question = page_text(look.screen.text) or ""
            learning = _ROOM.search(question) or _STOP.search(question)
            if learning:
                key = learning.group(1).strip()
                if learn is None or learn_key != key:
                    learn, learn_key = _learn(hands, look, key, pages), key
            # (step 4.1) the pages before the question and the whole message: the shift question names the next foe on the
            # page before "Will ... change POKéMON?"
            context = " ".join(pages.pages[-4:] + [look.screen.text or ""])
            yes, reason = mind.answer(question, look, learn if learning else None, context)
            hands.tell(f"battle: the question {question!r}: {'YES' if yes else 'NO'} ({reason})")
            if not (yield from choose(hands, BATTLE_YES_NO, 0 if yes else 1, f"{why}: {reason}")):
                return f"the battle: the question {question!r} could not be answered"
            continue
        if kind == "move_forget":
            ui = look.screen.ui
            names = list(ui.options) if ui is not None else []
            if learn is None or not learn.learn or learn.forget is None:
                index = len(names) - 1  # the new move: keep the four it knows
                reason = "keep the four moves it knows"
            else:
                wanted = [i for i, n in enumerate(names[:4]) if move_named(n) == learn.forget or n == learn.forget]
                index = wanted[0] if wanted else len(names) - 1
                reason = f"forget {learn.forget}: {learn.reason}"
            hands.tell(f"battle: the moves {names}: {reason}")
            if not (yield from choose(hands, "move_forget", index, f"{why}: {reason}")):
                return "the battle: the move to forget could not be chosen"
            continue
        if kind in ("party", "bag") and look.screen.ui is not None and not look.screen.ui.accepts_input:
            # a menu opening or closing (measured 2026-10-08: after SHIFT the party list stays on screen, not taking
            # input, for a few frames): watch it, then look again. (The step-4 verifier's round) or the party menu's
            # REFUSAL on screen before any choice of this battle's (a battle resumed at it): read it, and the member under
            # the cursor is the one refused
            settled = yield from _settle(hands, (kind,), why, messages=not mind.faults.ignore_refusal)
            if settled == "message":
                refused = _refused_member(hands.last)
                words = yield from _read_message(hands, why)
                if words is None:
                    return f"the battle: the {kind}'s message could not be read on"
                if kind == "party" and refused is not None:
                    mind.refuse(refused.pid, words)
                hands.tell(f"battle: the {kind} says {words!r}"
                           + (f": {refused.species} ({refused.pid:08x}) cannot go in" if kind == "party" and refused else ""))
                continue
            if settled != "open":
                if settled == "stuck":
                    return f"the battle: the {kind} on screen neither took input nor closed"
                continue
        if kind == "party":
            if not (yield from _send_in(hands, mind, why, forced=True)):
                return "the battle: no Pokemon could be sent in"
            continue
        if kind == "party_action":
            if (yield from _party_action(hands, why, mind)) != "ok":
                return "the battle: the party menu's action could not be chosen"
            continue
        return f"the battle: an unexpected {kind} on screen"
    return f"the battle did not end within {BATTLE_STEPS} menus"


def _learn(hands: Hands, look: Observation, printed: str, pages: _Pages) -> LearnChoice:
    """Which Pokemon is learning which move (the question's earlier page names them), and the decider's choice."""
    move = move_named(printed) or printed
    who = None
    for page in reversed(pages.pages):
        found = _TRYING.search(page)
        if found:
            who = found.group(1).strip().casefold()
            break
    party = list(look.party or ())
    mon = next((m for m in party if who is not None and m.species.casefold() == who), None)
    if mon is None and look.battle is not None and look.battle.own:
        mon = next((m for m in party if m.pid == look.battle.own[0].pid), None)
    if mon is None:
        mon = next((m for m in party if len(m.moves) == 4), None)
    if mon is None:
        return LearnChoice(False, None, f"it cannot tell which Pokemon learns {move}: keep the moves")
    choice = learn_choice(mon, move)
    hands.tell(f"battle: {mon.species} L{mon.level} would learn {move}: {'LEARN, forget ' + choice.forget if choice.learn else 'do NOT learn'} "
               f"({choice.reason})")
    hands.note("decide", "learn a move", choice.reason, {"pid": f"{mon.pid:08x}", "species": mon.species, "move": move,
                                                         "learn": choice.learn, "forget": choice.forget})
    return choice


def _execute(hands: Hands, mind: BattleMind, decision: Decision, why: str) -> Generator[None, None, str | None]:
    """Carry out a decision from the action menu. None when done (the battle goes on), or a reason to stop."""
    reason = f"{why}: {decision.reason}"
    if decision.action == "fight":
        if not (yield from choose_in_grid(hands, BATTLE_ACTION, 0, f"{reason} (FIGHT)")):
            return "the battle: FIGHT could not be chosen"
        if decision.move_slot is None:
            return None  # no move has PP: the game uses STRUGGLE by itself
        look = yield from wait_for_ui(hands, BATTLE_MOVE, reason, budget=300)
        if look is None:
            return None  # the game went on without the grid (e.g. STRUGGLE): watch it
        if not (yield from choose_in_grid(hands, BATTLE_MOVE, decision.move_slot, reason)):
            return "the battle: the move could not be chosen"
        mind.chose(look.screen.ui.battler if look.screen.ui is not None else None, decision.move_name)
        if not (yield from _aim(hands, decision, reason)):
            return "the battle: the target could not be chosen"
        return None
    if decision.action == "run":
        if not (yield from choose_in_grid(hands, BATTLE_ACTION, 3, f"{reason} (RUN)")):
            return "the battle: RUN could not be chosen"
        return None
    if decision.action in ("ball", "item"):
        if not (yield from choose_in_grid(hands, BATTLE_ACTION, 1, f"{reason} (BAG)")):
            return "the battle: BAG could not be chosen"
        pocket = pocket_for(decision)
        item = decision.ball if decision.action == "ball" else decision.item
        if not (yield from _use_item(hands, pocket, item, reason)):
            return f"the battle: the {item} could not be used"
        if decision.target_pid is not None:
            if not (yield from _give_item(hands, decision.target_pid, item, reason)):
                return f"the battle: the {item} could not be given"
        return None
    if decision.action == "switch":
        if not (yield from choose_in_grid(hands, BATTLE_ACTION, 2, f"{reason} (POKéMON)")):
            return "the battle: POKéMON could not be chosen"
        if not (yield from _pick_member(hands, decision.switch_pid, reason)):
            return "the battle: the Pokemon to switch to could not be chosen"
        result = yield from _party_action(hands, reason, mind)
        if result.startswith("refused:"):
            # (the step-4 verifier's round) the game refused the switch: the decider will not choose it again this turn;
            # back to the battle's menu with B (the party menu takes input again after its words), and decide again
            if decision.switch_pid is not None:
                mind.refuse(decision.switch_pid, result[len("refused:"):])
            look = yield from wait_for_ui(hands, "party", reason)
            if look is None:
                return "the battle: the party menu did not take input after its refusal"
            yield from hands.pad.press("B", reason, f"party cursor on {look.screen.ui.cursor}, the switch refused "
                                                    f"({result[len('refused:'):]!r}): back to the battle's menu")
            return None
        if result != "ok":
            return "the battle: SHIFT could not be chosen"
        return None
    return f"the battle: an unknown decision {decision.action}"


def _aim(hands: Hands, decision: Decision, why: str) -> Generator[None, None, bool]:
    """A DOUBLE battle's target, when the game asks for one after the move (`battle_target`: the cursor is a battler
    position): Right steps the cursor round the battlers (`src/battle_controller_player.c` HandleInputChooseTarget), read
    after every press; A on the foe decided. True when there was nothing to aim (a single battle, one foe left, a move that
    hits both) or the target was chosen."""
    first = hands.look()
    if first.battle is not None and not first.battle.double and (first.screen.ui is None or first.screen.ui.kind != BATTLE_TARGET):
        return True  # a single battle never asks
    for _ in range(TARGET_WAIT):
        look = hands.look()
        ui = look.screen.ui
        if ui is not None and ui.kind == BATTLE_TARGET and ui.accepts_input:
            break
        if ui is not None and ui.kind not in (BATTLE_MOVE, BATTLE_TARGET):
            return True
        if ui is None and (look.screen.waits_for_button or look.screen.text):
            return True  # the turn began: no target was asked for
        yield from hands.pad.busy("watching whether the game asks for a target")
    else:
        return True
    wanted = decision.target
    if wanted is None:
        foes = sorted(look.battle.foe if look.battle is not None else (), key=lambda f: (f.hp_bar, f.battler or 0))
        wanted = foes[0].battler if foes else None
    for _ in range(TARGET_PRESSES):
        look = hands.look()
        ui = look.screen.ui
        if ui is None or ui.kind != BATTLE_TARGET:
            return True
        names = ui.options
        here = f"{ui.cursor} ({names[ui.cursor] if ui.cursor is not None and ui.cursor < len(names) else '?'})"
        if ui.cursor == wanted:
            yield from hands.pad.press("A", why, f"battle_target cursor on {here}, the foe decided")
            return True
        yield from hands.pad.press("Right", why, f"battle_target cursor on {here}, wanted {wanted}: one step on")
    hands.tell(f"{why}: the target cursor did not reach {wanted} in {TARGET_PRESSES} presses")
    return False


def pocket_for(decision: Decision) -> str:
    """The bag pocket a decision's item lives in. (Step 4.1 review, finding 1) berries have their OWN pocket: an Oran
    Berry looked for under "items" failed every time and left the bag open."""
    if decision.action == "ball":
        return "poke_balls"
    return "berries" if (decision.item or "").endswith("Berry") else "items"


def _use_item(hands: Hands, pocket: str, item: str | None, why: str) -> Generator[None, None, bool]:
    """In the bag: the pocket (Left / Right, read), the item by its name in the list, A, then USE in its action list."""
    for _ in range(ITEM_STEPS):
        look = yield from wait_for_ui(hands, "bag", why)
        if look is None:
            return False
        ui = look.screen.ui
        if ui.pocket != pocket:
            here, there = BAG_POCKETS.index(ui.pocket) if ui.pocket in BAG_POCKETS else 0, BAG_POCKETS.index(pocket)
            right = (there - here) % len(BAG_POCKETS)
            button = "Right" if right <= len(BAG_POCKETS) - right else "Left"
            yield from hands.pad.press(button, why, f"bag: the {ui.pocket} pocket is open, the {item} is in the {pocket} "
                                                    f"pocket: one {button.lower()}")
            continue
        names = list(ui.options)
        index = next((i for i, name in enumerate(names) if _same_item(name, item)), None)
        if index is None:
            hands.tell(f"{why}: no {item} in the {pocket} pocket {names}")
            return False
        if not (yield from choose(hands, "bag", index, f"{why}: the {item}")):
            return False
        if not (yield from choose(hands, "bag_action", "USE", f"{why}: USE the {item}")):
            return False
        # the bag closes by itself (a fade back to the battle, or the party menu for a potion): watch it go
        for _ in range(BAG_CLOSE_BUDGET):
            look = hands.look()
            ui = look.screen.ui
            if ui is None or ui.kind not in ("bag", "bag_action"):
                return True
            yield from hands.pad.busy("watching: the bag closes")
        hands.tell(f"{why}: the bag did not close within {BAG_CLOSE_BUDGET} frames after USE")
        return False
    hands.tell(f"{why}: the {pocket} pocket was not reached in {ITEM_STEPS} presses")
    return False


def _same_item(shown: str, wanted: str | None) -> bool:
    if wanted is None:
        return False
    def key(name: str) -> str:
        return "".join(c for c in name.casefold().replace("é", "e") if c.isalnum())
    return key(shown) == key(wanted)


def _pick_member(hands: Hands, pid: int | None, why: str) -> Generator[None, None, bool]:
    """In the party menu: the Pokemon with this PID (identity, never a slot remembered from before: the menu lists the
    party in battle order), by reading the cursor, then A."""
    look = yield from wait_for_ui(hands, "party", why)
    if look is None or pid is None:
        return False
    pids = [m.pid for m in look.party or ()]
    if pid not in pids:
        hands.tell(f"{why}: PID {pid:08x} is not in the party {[f'{p:08x}' for p in pids]}")
        return False
    return (yield from choose(hands, "party", pids.index(pid), f"{why}: {look.party[pids.index(pid)].species}"))


def _give_item(hands: Hands, pid: int, item: str | None, why: str) -> Generator[None, None, bool]:
    """(step 4.1, found by the HEAL arm's first development run) A healing item's TARGET in the party menu the bag opens:
    the Pokemon with this PID (identity), by reading the cursor, A on the look that shows it there; then the party menu
    stays on screen while the HP bar fills and its message waits for A ("MUDKIP's HP was restored by 17 point(s).",
    `src/party_menu.c` ItemUseCB_Medicine: printer 6, a WAIT over a party list that takes no input), so the message is
    READ (`_read_message`) and the menu watched until it closes back to the battle. Step 4 waited for the menu to close
    after the A, and gave up while the message waited: "the battle: the Potion could not be given" (the Potion used, the
    HP restored, the battle stuck). True once the party menu has closed."""
    look = yield from wait_for_ui(hands, "party", why)
    if look is None:
        return False
    pids = [m.pid for m in look.party or ()]
    if pid not in pids:
        hands.tell(f"{why}: PID {pid:08x} is not in the party {[f'{p:08x}' for p in pids]}")
        return False
    index = pids.index(pid)
    if not (yield from move_cursor(hands, "party", index, why)):
        return False
    look = hands.look()  # THE GATE: the cursor on the member, the menu taking input, on the look right before the press
    ui = look.screen.ui
    if ui is None or ui.kind != "party" or ui.cursor != index or not ui.accepts_input:
        hands.tell(f"{why}: the party cursor is not on {look.party[index].species} before the press")
        return False
    yield from hands.pad.press("A", why, f"party cursor on {index}")  # the menus' own gate words (`hands/menus.py` choose)
    for _ in range(SEND_IN_TRIES):
        settled = yield from _settle(hands, ("party",), why)
        if settled == "gone":
            return True
        if settled != "message":
            hands.tell(f"{why}: after the {item} the party menu {'took input again' if settled == 'open' else 'did not close'}")
            return False
        words = yield from _read_message(hands, why)
        if words is None:
            return False
        hands.tell(f"battle: the party says {words!r}")
    hands.tell(f"{why}: the party menu did not close after the {item}")
    return False


def _party_action(hands: Hands, why: str, mind: BattleMind) -> Generator[None, None, str]:
    """The party menu's action list after a Pokemon is chosen in a battle: SHIFT (a switch) or SEND OUT (after a faint);
    then the party menu closes by itself (it stays on screen, not taking input, for a few frames): watched until it is
    gone. Returns "ok"; "refused:<the game's words>" when the game refused the Pokemon (the party menu's message, READ
    and pressed on by `_read_message`: the menu takes input again after it); "" when it went wrong (said why)."""
    look = yield from wait_for_ui(hands, "party_action", why)
    if look is None:
        return ""
    options = look.screen.ui.options
    wanted = "SEND OUT" if "SEND OUT" in options else "SHIFT"
    if wanted not in options:
        hands.tell(f"{why}: neither SHIFT nor SEND OUT in {options}")
        return ""
    if not (yield from choose(hands, "party_action", wanted, f"{why}: {wanted}")):
        return ""
    settled = yield from _settle(hands, ("party",), why, messages=not mind.faults.ignore_refusal)
    if settled == "message":
        words = yield from _read_message(hands, why)
        if words is None:
            hands.tell(f"{why}: after {wanted} the party menu's message could not be read on")
            return ""
        return f"refused:{words}"
    if settled != "gone":
        hands.tell(f"{why}: after {wanted} the party menu {'took input again' if settled == 'open' else 'did not close'}")
        return ""
    return "ok"


def _settle(hands: Hands, kinds: tuple[str, ...], why: str, messages: bool = True) -> Generator[None, None, str]:
    """A menu of `kinds` on screen that does not take input (it opens or closes): watch it until it takes input ("open")
    or is gone ("gone"); (the step-4 verifier's round) "message" when it shows a text that waits for A (the party menu's
    "... is already in battle!": the caller reads it, `_read_message`); "stuck" after `MENU_SETTLE_BUDGET` frames.
    `messages` False: the FAULT `ignore_refusal` (step 4: the message watched like a menu closing, until the bound)."""
    for _ in range(MENU_SETTLE_BUDGET):
        look = hands.look()
        ui = look.screen.ui
        if ui is None or ui.kind not in kinds:
            return "gone"
        if ui.accepts_input:
            return "open"
        if messages and look.screen.waits_for_button:
            return "message"
        yield from hands.pad.busy(f"watching: the {ui.kind} is not taking input (it opens or closes)")
    hands.tell(f"{why}: the {'/'.join(kinds)} neither took input nor closed within {MENU_SETTLE_BUDGET} frames")
    return "stuck"


def _read_message(hands: Hands, why: str) -> Generator[None, None, str | None]:
    """(the step-4 verifier's round) A menu's message that waits for A (the party menu's refusal): read it (the reading
    delay of its characters), then A on the look right before the press, ONLY while that look still waits for it (the
    gate: its wait reason). Returns its words ("" when the eyes cannot read them), None when no wait was there to press."""
    look = hands.look()
    page = page_text(look.screen.text) if look.screen.text else None
    characters = new_characters(None, page)
    words = f"{page!r}" if page is not None else f"(a message the eyes cannot read; {look.screen.wait_reason})"
    yield from hands.pad.idle(hands.pad.reading_frames(characters), f"reading the menu's message: {words}")
    look = hands.look()  # THE GATE: the look right before the press
    if not look.screen.waits_for_button:
        hands.tell(f"{why}: the menu's message {words} no longer waits for a press")
        return None
    if page is not None:
        hands.note("read", "text", page)
    yield from hands.pad.press("A", why, look.screen.wait_reason or "waits")
    return page or ""


def _refused_member(look: Observation):
    """The party member a party-menu refusal on screen is about: the one under the menu's cursor (the one just chosen),
    checked against the name the words begin with when they name one (a nickname would not match a species: then the
    cursor alone). None when neither can be told."""
    party = list(look.party or ())
    ui = look.screen.ui
    under = party[ui.cursor] if ui is not None and ui.cursor is not None and 0 <= ui.cursor < len(party) else None
    words = page_text(look.screen.text) if look.screen.text else None
    named = _REFUSED.match(words or "")
    if named:
        name = named.group(1).strip().casefold().replace("é", "e")
        matches = [m for m in party if m.species.casefold().replace("é", "e") == name]
        if under is not None and under in matches:
            return under
        if len(matches) == 1:
            return matches[0]
    return under


def _send_in(hands: Hands, mind: BattleMind, why: str, forced: bool) -> Generator[None, None, bool]:
    """The party menu opened by the game (a Pokemon fainted): the decider's choice goes in. (The step-4 verifier's round)
    If the game refuses it, its words are read, the decider is told (`BattleMind.refuse`) and chooses again, at most
    `SEND_IN_TRIES` times; the one sent in is told too (`BattleMind.sent`: in a double battle where both fell, the second
    party menu comes before any look at the field shows the first one there)."""
    for _ in range(SEND_IN_TRIES):
        look = yield from wait_for_ui(hands, "party", why)
        if look is None:
            return False
        pid, reason = mind.replacement(look, forced)
        hands.tell(f"battle: who goes in: {reason}")
        hands.note("decide", "send in", reason, {"pid": None if pid is None else f"{pid:08x}"})
        if pid is None:
            return False
        if not (yield from _pick_member(hands, pid, f"{why}: {reason}")):
            return False
        result = yield from _party_action(hands, f"{why}: {reason}", mind)
        if result == "ok":
            mind.sent(pid)
            return True
        if not result.startswith("refused:"):
            return False
        words = result[len("refused:"):]
        mind.refuse(pid, words)
        hands.tell(f"battle: the game refused {pid:08x}: {words!r}: choose again")
    hands.tell(f"{why}: no Pokemon went in after {SEND_IN_TRIES} choices")
    return False
