"""SKILL: the New Game intro, PLAYED by the AI (build step 2; design draft §6 criterion 1, RULING 37 Q4: an
official acceptance run starts from a real New Game, naming included).

From a fresh boot to the moment the player stands in the moving truck:
  the intro movie   skipped with START after a moment (`src/intro.c` MainCB2_Intro: any new key ends it, but
                    only while no palette fade runs), as a person does; the title's logo animation likewise
                    (Task_TitleScreenPhase1/2);
  the title         START at "PRESS START" (Task_TitleScreenPhase3);
  the main menu     NEW GAME, chosen by reading the cursor (on a fresh save it is the first of two);
  Birch's speech    every page READ, then A, only when the eyes say the game waits (`hands/dialogue.py`);
  BOY or GIRL       the personality's weighted draw (`ai_player/personality.py`), chosen by reading the cursor;
  "your name?"      the task that waits for A/B (`eyes/screens.py` TASK_WAITS), then the naming keyboard: the
                    name drawn from the personality's list, TYPED key by key (`hands/menus.py` type_name);
  "So it's NAME?"   YES by intent, after checking the question names EXACTLY what was typed (`name_in_question`);
  the rest          read and advanced until the truck's map is loaded; then the skill STOPS, pressing
                    nothing in the truck (the ride is a scene; leaving the truck is step 3's navigator).

ONE LOOP, ONE GOAL (the truck): `advance` moves the text on and returns "menu:<kind>" the moment a choice is
on screen; this skill answers each choice by intent and goes back to advancing. That is also what makes the
FAULT arm honest: with `ungated_a` the very same code never sees a choice (the naive driver presses A
through them), so the default is picked: BOY, and the keyboard's top-left key, 'A', typed until it is full.

STEP 2.1 (the step-2 review, items 4, 5 and 6):
  * START is pressed on the movie or the title only while the eyes say it TAKES INPUT, which is never during a
    palette fade (`eyes/screens.py` read_ui): measured 2026-10-08, seed 3's first START landed on a fading
    frame of the movie, where the game ignores keys;
  * the name question is compared EXACTLY (it was a substring test: "Kai" is in "So it's Kaiden?"), and when
    the page cannot be read as the question at all, the AI relies on what the keyboard CONFIRMED (`type_name`
    pressed OK only on a look whose text read exactly the name) instead of answering NO and re-typing a name
    it typed right until the menu limit runs out;
  * a choice, a name or an answer that FAILS ends the skill at once with its reason (each sub-skill has said
    why in the run's log) instead of going round this loop until its 60 turns run out; so does a stuck
    `advance` (`hands/dialogue.py` stall detector).
"""

from __future__ import annotations

import re
from collections.abc import Generator

from ai_player.eyes.observation import Observation
from ai_player.eyes.screens import page_text
from ai_player.hands.dialogue import STUCK, advance, busy_reason
from ai_player.hands.menus import answer_yes_no, choose, type_name
from ai_player.hands.pad import Hands
from ai_player.personality import Personality, choose_gender, choose_name

__all__ = ["INPUT_WAIT_BUDGET", "INTRO_MENU_STEPS", "TRUCK_MAP", "in_truck", "name_in_question", "play_intro", "skip_title"]

#: The truck's map (`MAP_INSIDE_OF_TRUCK`, the framework's map table names it so).
TRUCK_MAP = "INSIDE_OF_TRUCK"
#: The most menus the intro may meet (movie skips, title, main menu, gender, keyboard, yes/no, retries).
INTRO_MENU_STEPS = 60
#: How long the AI waits for the movie or the title to take input (a fade to end) before it looks again.
INPUT_WAIT_BUDGET = 600
#: `data/text/birch_speech.inc` gText_Birch_SoItsPlayer "So it's {PLAYER}{KUN}?" ({KUN} is empty in English; the
#: eyes' charmap reads the apostrophe as ’, `eyes/screens.py` CHARMAP 0xB4).
_NAME_QUESTION = re.compile(r"So it['’]s (?P<name>.*)\?")


def in_truck(look: Observation) -> bool:
    """The player stands in the moving truck: the overworld, the truck's map, a settled position."""
    player = look.player
    return (look.screen.game_state == "OVERWORLD" and player is not None and player.map_const == TRUCK_MAP
            and not player.settling)


def name_in_question(question: str | None, name: str) -> bool | None:
    """Does "So it's NAME?" name EXACTLY `name`? True or False; None when the page cannot be read as that question
    (no text, or another text: with no printer active the eyes' text is the last message printed)."""
    if question is None:
        return None
    match = _NAME_QUESTION.fullmatch(question.strip())
    if match is None:
        return None
    return match.group("name") == name


def play_intro(hands: Hands, personality: Personality) -> Generator[None, None, str]:
    """Play the intro to the truck. Returns "in the truck as NAME (GENDER)" or what went wrong."""
    gender, lean = choose_gender(hands.choices, personality)
    name = choose_name(hands.choices, gender)
    hands.tell(f"intro: personality {personality.name} ({personality.chosen_by}; seed {personality.seed}): "
               f"gender {gender} (drawn with P(GIRL)={lean}), name {name!r} (from {gender}'s list)")
    hands.note("decide", f"gender {gender}", "personality-weighted draw", {"p_girl": lean, "personality": personality.name})
    hands.note("decide", f"name {name}", "drawn from the personality's list", {"gender": gender})
    why = "the intro: from the title to the truck"
    typed = False  # the last `type_name` CONFIRMED the name: OK pressed on a look whose text read exactly `name`
    for _ in range(INTRO_MENU_STEPS):
        outcome = yield from advance(hands, in_truck, why)
        if outcome == "done":
            look = hands.look()
            hands.tell(f"intro: in the truck ({look.player.map_name}, {look.player.map_const}) at f{look.frame}")
            return f"in the truck; intended {name} ({gender})"
        if outcome == "budget":
            return "intro: the dialogue budget ran out"
        if outcome.startswith(STUCK):
            return f"intro: {outcome}"
        kind = outcome.split(":", 1)[1]
        if kind in ("intro_movie", "title"):
            yield from skip_title(hands, kind)
        elif kind == "main_menu":
            if not (yield from choose(hands, "main_menu", "NEW GAME", "a new game")):
                return "intro: NEW GAME could not be chosen on the main menu"
        elif kind == "gender":
            if not (yield from choose(hands, "gender", gender, f"the personality chose {gender}")):
                return f"intro: {gender} could not be chosen on the gender menu"
        elif kind == "naming":
            typed = yield from type_name(hands, name, f"the name {name!r}")
            if not typed:
                return f"intro: the name {name!r} could not be typed on the keyboard"
        elif kind == "yes_no":
            look = hands.look()
            question = page_text(look.screen.text)
            names = name_in_question(question, name)
            if names is None and not typed:
                return f"intro: the name question cannot be read ({question!r}) and the keyboard did not confirm {name!r}"
            agrees = typed if names is None else names
            hands.note("read", "text", question or "", {"names_the_typed_name": names, "relied_on_the_keyboard": names is None})
            if names is None:
                because = f"the page cannot be read as the name question ({question!r}); the keyboard CONFIRMED {name!r}"
            else:
                because = f"'{question}' ({'names' if names else 'does NOT name'} exactly {name!r})"
            if not (yield from answer_yes_no(hands, agrees, because)):
                return "intro: the name question could not be answered"
        else:
            return f"intro: an unexpected {kind} on screen"
    return "intro: too many menus"


def skip_title(hands: Hands, kind: str) -> Generator[None, None, bool]:
    """The intro movie or the title (`kind`), skipped with START as a person does: wait until it takes input (no fade
    runs), look at it for a moment, and press START only if the look right before the press still shows it taking input.
    True when START was pressed; False when the screen went away first (the movie runs into the title: look again).
    R1 (build spec section 3 (b), continue_game step 1): moved here from `play_intro` unchanged, so the continue skill
    (`skills/saving.py`) skips the title exactly as the intro does."""
    look = yield from _until_it_takes_input(hands, kind)
    if look is None:
        return False  # it ended by itself (the movie runs into the title): look again
    what = "the intro movie / the title's animation: any key skips it" if kind == "intro_movie" else \
        "the title screen: Task_TitleScreenPhase3 takes START"
    yield from hands.pad.idle(hands.pad.think_frames(), "the intro plays; a person skips it" if kind == "intro_movie"
                              else "the title screen: PRESS START")
    look = hands.look()
    ui = look.screen.ui
    if ui is not None and ui.kind == kind and ui.accepts_input:
        yield from hands.pad.press("Start", "skip the intro" if kind == "intro_movie" else "start the game",
                                   f"{what} (it takes input: no fade runs)")
        return True
    return False


def _until_it_takes_input(hands: Hands, kind: str) -> Generator[None, None, Observation | None]:
    """Watch until the `kind` screen takes input (no fade runs); that look, or None if it went away first or did
    not within INPUT_WAIT_BUDGET frames."""
    for _ in range(INPUT_WAIT_BUDGET):
        look = hands.look()
        ui = look.screen.ui
        if ui is None or ui.kind != kind:
            return None
        if ui.accepts_input:
            return look
        yield from hands.pad.busy(busy_reason(look))
    hands.tell(f"intro: the {kind} did not take input within {INPUT_WAIT_BUDGET} frames")
    return None
