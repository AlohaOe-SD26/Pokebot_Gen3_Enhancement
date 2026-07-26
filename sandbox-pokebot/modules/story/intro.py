"""Story-mode Chapter 0 — the New Game intro (Emerald).

Drives, from the title screen through Professor Birch's intro speech:
  title screen -> New Game -> Birch speech -> gender select -> name entry ->
  "is this name okay?" -> end of speech -> player lands in the moving truck.

This is the hardest-to-automate stretch of the game: it is a scripted cutscene
with almost no event flags, so it is driven by watching the intro's named
*tasks* (from `pokeemerald.sym`) and the `GameState` enum, pressing the right
button at each step. Everything is bounded by a frame cap so a missed
transition raises `BotModeError` instead of hanging forever.

Emerald specifics that matter here (NOT the Kanto intro):
  * The professor is **Birch**, the town is **Littleroot**, and the "van" is
    the **moving truck** you start inside after the speech.
  * The gender menu is a dedicated menu (`Task_NewGameBirchSpeech_ChooseGender`)
    whose current selection is the byte `sIntroCharacterGender` (0=Boy, 1=Girl),
    NOT a generic multi-choice — so we read that byte to confirm the cursor.
  * Name entry uses the shared `type_in_naming_screen()` keyboard helper.
"""

from __future__ import annotations

import os
import random
from typing import Generator

from modules.context import context
from modules.keyboard import get_naming_screen_data, type_in_naming_screen
from modules.memory import GameState, get_game_state
from modules.modes import BotModeError
from modules.modes.util.sleep import wait_for_n_frames
from modules.modes.util.tasks_scripts import (
    wait_until_task_is_active,
    wait_until_task_is_not_active,
)
from modules.modes.util.walking import wait_for_player_avatar_to_be_controllable
from modules.tasks import task_is_active

GENDER_TO_INDEX = {"boy": 0, "girl": 1}
MAX_NAME_LENGTH = 7  # Gen-3 player names are capped at 7 characters

# ---------------------------------------------------------------------------
# RNG DECORRELATION — why a random pause on the naming screen is load-bearing
# ---------------------------------------------------------------------------
# ‼ WITHOUT THIS, TWO RUNS OF THIS INTRO ARE THE SAME GAME. Verified against the
# pokeemerald decomp (2026-07-26, commit 83df84e4), not assumed:
#
#   * `gRngValue` is 0 at every hard reset (`src/random.c`: COMMON_DATA, cleared by
#     `RegisterRamReset(RESET_ALL)`, and stored in no save block).
#   * Emerald is NOT RTC-seeded. `SeedRngWithRtc()` exists but sits inside
#     `#ifdef BUGFIX`, and `include/config.h:48` has `//#define BUGFIX` — Emerald
#     inherited FireRed's version of main.c. (Ruby/Sapphire DO seed from the RTC;
#     if this were Ruby none of this would be necessary.)
#   * The only per-frame advance is a bare `Random()` in `VBlankIntr()`
#     (`src/main.c:365-366`) — a pure function of frames since boot.
#   * The ONLY single-player reseed is `SeedRngAndSetTrainerId()`
#     (`src/main.c:208-214`): `SeedRng(REG_TM1CNT_L)`, reading a cycle-exact hardware
#     timer that `StartTimer1()` (`src/naming_screen.c:412`) starts when the naming
#     screen OPENS and that is read when the name is CONFIRMED
#     (`src/naming_screen.c:701`).
#
# So the post-intro RNG state depends on exactly one thing we control: how many
# CPU cycles pass between the naming screen opening and the name being confirmed.
# A delay anywhere EARLIER is discarded, because `SeedRng` overwrites the state.
#
# One GBA frame is 228 x 1232 = 280,896 cycles, and 280,896 mod 65,536 = 18,752, so
# each extra idle frame here shifts the seed by +18,752 (mod 2^16). `gcd(18752, 65536)`
# is 64, so the reachable seeds cycle every 1,024 frames — a 0..120 frame pause gives
# 121 widely separated, distinct seeds for at most two seconds of wall clock.
#
# This is also FAITHFUL: a human takes a variable moment to confirm their name.
#
# Set POKEBOT_RNG_DECORRELATION_FRAMES=0 to disable it and get the old, fully
# deterministic behaviour — which is what you want when REPRODUCING a bug from a
# cold start rather than sampling independent runs.
_RNG_DECORRELATION_ENV = "POKEBOT_RNG_DECORRELATION_FRAMES"
RNG_DECORRELATION_MAX_FRAMES = 120


def _rng_decorrelation_frames() -> int:
    """How many idle frames to hold the naming screen for. 0 == deterministic."""
    override = os.environ.get(_RNG_DECORRELATION_ENV)
    if override is not None:
        try:
            return max(0, int(override))
        except ValueError:
            pass
    return random.randint(0, RNG_DECORRELATION_MAX_FRAMES)


def _press_until_task(
    task_name: str, button: str, *, timeout_frames: int = 3600, label: str = ""
) -> Generator:
    """Mash ``button`` each frame until ``task_name`` becomes active, or raise
    if it never does within ``timeout_frames``."""
    frames = 0
    while not task_is_active(task_name):
        if frames >= timeout_frames:
            raise BotModeError(
                f"Intro timed out waiting for task '{task_name}'"
                + (f" ({label})" if label else "")
                + f" after {timeout_frames} frames (game state: {get_game_state().name})."
            )
        context.emulator.press_button(button)
        frames += 1
        yield


def run_intro(character_name: str, gender: str = "boy") -> Generator:
    """Play the New Game intro up to landing in the moving truck.

    :param character_name: The player character's name (<= 7 chars, trimmed).
    :param gender: "boy" or "girl".
    """
    gender = (gender or "boy").strip().lower()
    if gender not in GENDER_TO_INDEX:
        raise BotModeError(f"gender must be 'boy' or 'girl', got {gender!r}.")
    name = (character_name or "").strip()
    if not name:
        raise BotModeError("A non-empty character name is required for the intro.")

    # --- 1+2. Boot -> title -> New Game -> Birch's speech, up to the gender
    # prompt. A single bounded A-mash carries the copyright/title screens, the
    # main menu (A selects New Game on a save-less profile), and Birch's whole
    # welcome speech. We stop at `BoyOrGirl` — the task JUST BEFORE the gender
    # menu opens — so a stray A can't accidentally confirm the default gender.
    context.message = "Intro: New Game + Professor Birch's welcome speech..."
    yield from _press_until_task(
        "Task_NewGameBirchSpeech_BoyOrGirl", "A",
        timeout_frames=10800, label="boot -> gender prompt",
    )
    # Let the gender menu actually open — press nothing while it slides in.
    yield from wait_until_task_is_active("Task_NewGameBirchSpeech_ChooseGender")

    # --- 3. Gender selection. Position-based & deterministic: the menu opens
    # with the cursor on BOY (top). For a girl, move the cursor down once; then
    # confirm. (`sIntroCharacterGender` proved unreliable as a live cursor read.)
    context.message = f"Intro: selecting gender ({gender})..."
    yield from wait_for_n_frames(12)  # let the menu finish sliding in
    if gender == "girl":
        context.emulator.press_button("Down")
        yield from wait_for_n_frames(8)
    context.emulator.press_button("A")
    yield
    yield from wait_until_task_is_not_active("Task_NewGameBirchSpeech_ChooseGender")

    # --- 4. "What's your name?" -> naming screen -> type the name. -----------
    context.message = "Intro: entering the naming screen..."
    frames = 0
    while get_game_state() is not GameState.NAMING_SCREEN:
        context.emulator.press_button("A")
        frames += 1
        if frames > 3600:
            raise BotModeError("Intro never reached the naming screen after gender select.")
        yield

    # The NAMING_SCREEN game state flips a few frames before the keyboard
    # struct pointer is populated; wait for it so type_in_naming_screen (which
    # raises if the struct is null) has something to work with.
    frames = 0
    while get_naming_screen_data() is None:
        frames += 1
        if frames > 600:
            raise BotModeError("Naming screen state active but keyboard struct never initialised.")
        yield

    context.message = f"Intro: typing the name '{name}'..."
    yield from type_in_naming_screen(name, max_length=MAX_NAME_LENGTH)

    # ‼ THE ONE PLACE A DELAY CHANGES THE GAME'S RNG. See the block comment at the top
    # of this module: the seed is taken from a hardware timer read when the name is
    # CONFIRMED, so idling here — after typing, before the confirm below — is what makes
    # this run's encounters, damage rolls and IVs differ from the last one's. Idle frames
    # only: pressing anything would advance the naming screen.
    _decorrelation_frames = _rng_decorrelation_frames()
    if _decorrelation_frames:
        context.message = f"Intro: holding {_decorrelation_frames}f before confirming (RNG decorrelation)..."
        try:
            from modules.console import console

            console.print(
                f"[cyan]RNG decorrelation: holding the naming screen {_decorrelation_frames} "
                f"frame(s) before confirming.[/]"
            )
        except Exception:
            pass
        yield from wait_for_n_frames(_decorrelation_frames)

    # --- 5. Confirm the name and ride the closing cutscene to first control. --
    # After the keyboard closes, Birch asks "is this name okay?" (default YES,
    # so 'A' confirms it) and then delivers the closing speech, after which the
    # player shrinks, the screen fades, and the moving-truck cutscene plays and
    # auto-drops the player in Littleroot. Mashing 'A' advances the confirm +
    # speech; we STOP at the very first controllable overworld moment (arrival),
    # which is the clean end of Chapter 0. Note: Birch's speech reports as the
    # MAIN_MENU game state, so we advance until the state becomes OVERWORLD.
    context.message = "Intro: confirming the name and riding to Littleroot..."
    frames = 0
    while get_game_state() is not GameState.OVERWORLD:
        context.emulator.press_button("A")
        frames += 1
        if frames > 10800:
            raise BotModeError("Intro never reached the overworld after naming/confirmation.")
        yield
    # In the intro overworld now (truck ride / arrival). Wait for control WITHOUT
    # pressing anything so we don't overshoot past the arrival.
    yield from wait_for_player_avatar_to_be_controllable()

    context.message = "Intro complete — arrived in Littleroot (Chapter 0 done)."
