"""SKILL: the New Game intro, PLAYED by the AI (build step 2; design draft §6 criterion 1, RULING 37 Q4: an
official acceptance run starts from a real New Game, naming included).

From a fresh boot to the moment the player stands in the moving truck:
  the intro movie   skipped with START after a moment (`src/intro.c` MainCB2_Intro: any new key ends it), as
                    a person does; the title's logo animation likewise (Task_TitleScreenPhase1/2);
  the title         START at "PRESS START" (Task_TitleScreenPhase3);
  the main menu     NEW GAME, chosen by reading the cursor (on a fresh save it is the first of two);
  Birch's speech    every page READ, then A, only when the eyes say the game waits (`hands/dialogue.py`);
  BOY or GIRL       the personality's weighted draw (`ai_player/personality.py`), chosen by reading the cursor;
  "your name?"      the task that waits for A/B (`eyes/screens.py` TASK_WAITS), then the naming keyboard: the
                    name drawn from the personality's list, TYPED key by key (`hands/menus.py` type_name);
  "So it's NAME?"   YES by intent, after checking the question names what was typed;
  the rest          read and advanced until the truck's map is loaded; then the skill STOPS, pressing
                    nothing in the truck (the ride is a scene; leaving the truck is step 3's navigator).

ONE LOOP, ONE GOAL (the truck): `advance` moves the text on and returns "menu:<kind>" the moment a choice is
on screen; this skill answers each choice by intent and goes back to advancing. That is also what makes the
FAULT arm honest: with `ungated_a` the very same code never sees a choice (the naive driver presses A
through them), so the default is picked: BOY, and the keyboard's top-left key, 'A', typed until it is full.
"""

from __future__ import annotations

from collections.abc import Generator

from ai_player.eyes.observation import Observation
from ai_player.eyes.screens import page_text
from ai_player.hands.dialogue import advance
from ai_player.hands.menus import answer_yes_no, choose, type_name
from ai_player.hands.pad import Hands
from ai_player.personality import Personality, choose_gender, choose_name

__all__ = ["INTRO_MENU_STEPS", "TRUCK_MAP", "in_truck", "play_intro"]

#: The truck's map (`MAP_INSIDE_OF_TRUCK`, the framework's map table names it so).
TRUCK_MAP = "INSIDE_OF_TRUCK"
#: The most menus the intro may meet (movie skips, title, main menu, gender, keyboard, yes/no, retries).
INTRO_MENU_STEPS = 60


def in_truck(look: Observation) -> bool:
    """The player stands in the moving truck: the overworld, the truck's map, a settled position."""
    player = look.player
    return (look.screen.game_state == "OVERWORLD" and player is not None and player.map_const == TRUCK_MAP
            and not player.settling)


def play_intro(hands: Hands, personality: Personality) -> Generator[None, None, str]:
    """Play the intro to the truck. Returns "in the truck as NAME (GENDER)" or what went wrong."""
    gender, lean = choose_gender(hands.choices, personality)
    name = choose_name(hands.choices, gender)
    hands.tell(f"intro: personality {personality.name} ({personality.chosen_by}; seed {personality.seed}): "
               f"gender {gender} (drawn with P(GIRL)={lean}), name {name!r} (from {gender}'s list)")
    hands.note("decide", f"gender {gender}", "personality-weighted draw", {"p_girl": lean, "personality": personality.name})
    hands.note("decide", f"name {name}", "drawn from the personality's list", {"gender": gender})
    why = "the intro: from the title to the truck"
    for _ in range(INTRO_MENU_STEPS):
        outcome = yield from advance(hands, in_truck, why)
        if outcome == "done":
            look = hands.look()
            hands.tell(f"intro: in the truck ({look.player.map_name}, {look.player.map_const}) at f{look.frame}")
            return f"in the truck; intended {name} ({gender})"
        if outcome == "budget":
            return "intro: the dialogue budget ran out"
        kind = outcome.split(":", 1)[1]
        if kind == "intro_movie":
            yield from hands.pad.idle(hands.pad.think_frames(), "the intro plays; a person skips it")
            look = hands.look()
            if look.screen.ui is not None and look.screen.ui.kind == "intro_movie":
                yield from hands.pad.press("Start", "skip the intro", "intro movie / title animation: any key skips it")
        elif kind == "title":
            yield from hands.pad.idle(hands.pad.think_frames(), "the title screen: PRESS START")
            look = hands.look()
            if look.screen.ui is not None and look.screen.ui.kind == "title":
                yield from hands.pad.press("Start", "start the game", "title screen: Task_TitleScreenPhase3 takes START")
        elif kind == "main_menu":
            yield from choose(hands, "main_menu", "NEW GAME", "a new game")
        elif kind == "gender":
            yield from choose(hands, "gender", gender, f"the personality chose {gender}")
        elif kind == "naming":
            yield from type_name(hands, name, f"the name {name!r}")
        elif kind == "yes_no":
            look = hands.look()
            question = page_text(look.screen.text) or ""
            agrees = name in question
            hands.note("read", "text", question, {"names_the_typed_name": agrees})
            yield from answer_yes_no(hands, agrees, f"'{question}' (it {'names' if agrees else 'does NOT name'} {name!r})")
        else:
            return f"intro: an unexpected {kind} on screen"
    return "intro: too many menus"
