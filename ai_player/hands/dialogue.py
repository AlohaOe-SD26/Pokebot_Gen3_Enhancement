"""The AI's TEXT AND DIALOGUE DRIVER (build step 2): advance text ONLY when the game waits for it, answer a
yes/no by intent, and start a conversation only when nothing else is running.

THE RULE (the project's museum-greeter lesson, `PROJECT KNOWLEDGE/08-MISTAKES.md` 2026-07-23, and the
orchestrator's hard rule for step 2): pressing A on every frame is HOLDING it, and an A pressed when nothing
waits for it is not "advance the text": next to a person it STARTS a conversation, and on a choice it PICKS
the highlighted option. So `advance` presses A only when the eyes say `waits_for_button` on a look taken
right before the press (a text printer waiting, a script's `waitbuttonpress`, or a task polling A/B), and
it STOPS, without pressing, the moment a menu is on screen: a choice is the caller's to make, by intent
(`hands/menus.py`: answer_yes_no, choose).

HUMAN PACE: before each A the driver READS: the pad's reading delay for the characters that appeared since
the last press (`eyes/screens.py` page_text: the page on screen), 0.3 s to 2.5 s; the page it read goes into
the action log, so a run's log says what the AI read and when.

FAULT `ungated_a` (`hands/pad.py` Faults): the naive driver, which presses A on the pad's cadence until its
goal is reached, whatever is on screen, and never stops for a menu. `gates/live_step2.py` runs it beside the
real driver to show the harm (a choice made by the default instead of by intent).
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import replace

from ai_player.eyes.observation import Observation, SeenObject
from ai_player.eyes.screens import page_text
from ai_player.hands.pad import Hands

__all__ = [
    "DIALOGUE_BUDGET",
    "FREE_BUDGET",
    "GENERIC_BUSY",
    "STALL_FRAMES",
    "STALL_FRAMES_SCENE",
    "STUCK",
    "TALK_START_BUDGET",
    "UNGATED_GATE",
    "advance",
    "awaits_press",
    "busy_reason",
    "dialogue_over",
    "facing_direction",
    "new_characters",
    "player_free",
    "seen_now",
    "stall_limit",
    "talk",
    "talk_direction",
]

#: The longest any one `advance` may run: three minutes of game time (a long scene). A budget, not a target.
DIALOGUE_BUDGET = 3 * 60 * 60
#: STEP 2.1 (the step-2 review, item 1: "an unrecognised prompt causes a silent 3-minute stall with a false
#: reason"): how many frames `advance` watches a screen on which NOTHING the eyes see changes (`seen_now`) before it
#: says it is STUCK, instead of watching on to the budget above. 300 frames (5 s) when the eyes name nothing that
#: plays (an unlisted menu in a script looks exactly like "a scene plays": the review's case); 900 (15 s) while
#: they NAME the scene (`ScreenState.scene`: a person who knows the healing jingle waits it out). MEASURED
#: 2026-10-08 (in-process, seed 3, every busy frame of `advance` in the four step-2 skills): the longest still
#: stretches were 455 frames of "Professor Birch's speech" (his opening: timers and a sprite blend the eyes do not
#: report) and 319 of "the nurse healing the party" (the machine and its jingle), both NAMED; the longest unnamed
#: one was 58 (the nurse's script). One threshold of 300 would have stopped the intro and the nurse falsely.
STALL_FRAMES = 300
STALL_FRAMES_SCENE = 900
#: The outcome prefix `advance` returns when it is stuck: "stuck:<what it was watching>".
STUCK = "stuck:"
#: After the A that starts a conversation, how long the script has to start before the attempt failed.
TALK_START_BUDGET = 90
#: How long `talk` waits for the player to be free (a scene ending) before it gives up.
FREE_BUDGET = 1200
#: The gate the ungated FAULT writes on its presses, so the log can never pass one off as gated.
UNGATED_GATE = "NONE (FAULT ungated A: pressed on the cadence, the eyes not asked)"
#: STEP 2.1: the catch-all busy reason, for a screen no scene table names (`busy_reason`).
GENERIC_BUSY = "watching: the game is busy"

_DIRECTION = {(0, -1): "up", (0, 1): "down", (-1, 0): "left", (1, 0): "right"}
_BUTTON = {"up": "Up", "down": "Down", "left": "Left", "right": "Right"}


def new_characters(previous: str | None, page: str | None) -> int:
    """How many characters of `page` a person has not read yet, when `previous` is the page they last read
    (the same page grows as it prints; a new paragraph starts afresh)."""
    if page is None:
        return 0
    if previous and page.startswith(previous):
        return len(page) - len(previous)
    return len(page)


def busy_reason(look: Observation) -> str:
    """Why the AI stands still for a frame, in words (it is always one of these: never idle without a reason).

    STEP 2.1 (the step-2 verifier): the last two rules name WHAT the AI watches, a fade or the scene that plays
    (`ScreenState.fading`, `ScreenState.scene`, `eyes/screens.py` scene_of), so the catch-all
    (`GENERIC_BUSY`) is left only for a screen no table names; `gates/live_step2.py` fails a real run that
    logs it, and `gates/test_hands.py` checks every rule."""
    screen = look.screen
    if screen.screen == "transition" or screen.game_state == "CHANGE_MAP":
        return "watching: the screen changes"
    if screen.ui is not None and not screen.ui.accepts_input:
        return f"watching: the {screen.ui.kind} is not taking input yet"
    if screen.text is not None and not screen.waits_for_button and screen.ui is None:
        return "reading along: a text is printing"
    if screen.game_state == "OVERWORLD" and (screen.script_running or screen.controls_locked):
        return "watching: a scene plays (a script runs, the controls are locked)"
    if screen.fading:
        return f"watching: the screen fades ({screen.scene or screen.game_state.lower()})"
    if screen.scene is not None:
        return f"watching: {screen.scene} (it runs by itself: nothing on screen takes a press now)"
    if screen.game_state == "OVERWORLD" and look.player is not None and look.player.settling:
        # BUILD STEP 5 (measured 2026-10-14: one frame per ledge jump and per map edge crossed, the play brain's
        # chapter-1 sweep): the object's tile and the save block's position disagree for a frame (`PlayerState.settling`)
        return "watching: the player's move finishing (a jump, a map's edge: the position settles)"
    return f"{GENERIC_BUSY} ({screen.game_state.lower()})"


def seen_now(look: Observation) -> tuple:
    """Everything the eyes see in one look, without WHEN (the frame) and what the look cost (and its problems,
    which say what could not be read, not what is on screen): the screen (menu, wait, text as printed, fade,
    scene), the player, the window and the people in it, the party, the bag, the progress, the battle. Two looks
    with equal `seen_now` show a person the same thing (step 2.1's stall detector compares them).
    R1 (build spec D18): the progress is compared WITHOUT its play time: the play time is not on the screen the AI watches,
    and a minute tick would reset `advance`'s stall counter."""
    progress = look.progress if look.progress is None else replace(look.progress, play_time=None)
    return (look.screen, look.player, look.view, look.party, look.bag, progress, look.battle,
            look.last_battle_outcome, look.storage)


def stall_limit(look: Observation) -> int:
    """How long `advance` watches an unchanging screen before it is stuck (`STALL_FRAMES`, or `STALL_FRAMES_SCENE`
    while the eyes name the scene that plays)."""
    return STALL_FRAMES_SCENE if look.screen.scene is not None else STALL_FRAMES


def player_free(look: Observation) -> bool:
    """The player stands in the overworld with nothing running: no script, controls free, no menu, no text,
    nothing waiting, the position settled. Only then does an A press START something."""
    screen, player = look.screen, look.player
    return (screen.game_state == "OVERWORLD" and not screen.script_running and not screen.controls_locked
            and screen.ui is None and not screen.text_box_open and not screen.waits_for_button
            and player is not None and not player.settling)


def dialogue_over(look: Observation) -> bool:
    """A conversation has ended: the player is free again (`player_free`)."""
    return player_free(look)


def talk_direction(look: Observation, target: SeenObject) -> str | None:
    """Which way the player must face to talk to `target`: next to it, or across a shop or Pokemon Center
    COUNTER between the two (the nurse and the clerk stand behind one; `MetatileBehavior_IsCounter` lets the
    game reach across it). None when `target` is not in talking reach."""
    dx, dy = target.dx, target.dy
    if (dx, dy) in _DIRECTION:
        return _DIRECTION[(dx, dy)]
    if look.view is not None and (abs(dx), abs(dy)) in ((0, 2), (2, 0)):
        step = (dx // 2, dy // 2)
        between = look.view.tile(*step)
        if between is not None and between.behavior_name == "COUNTER":
            return _DIRECTION[step]
    return None


def facing_direction(look: Observation) -> str | None:
    return None if look.player is None else look.player.facing


def _same(seen: SeenObject, target: SeenObject) -> bool:
    """The same thing on a later look: a person by its map id (people move), a sign by its tile (every sign
    has local id -1)."""
    if seen.source != target.source:
        return False
    if seen.source == "object":
        return seen.local_id == target.local_id
    return (seen.x, seen.y) == (target.x, target.y)


def advance(hands: Hands, until: Callable[[Observation], bool], why: str,
            budget: int = DIALOGUE_BUDGET) -> Generator[None, None, str]:
    """Move a dialogue or a scene on until `until(look)`: "done". Returns "menu:<kind>" WITHOUT pressing the
    moment a menu is on screen (the caller chooses), "stuck:<what it watched>" when nothing the eyes see has
    changed for `stall_limit` frames while it waits (step 2.1), or "budget" after `budget` frames. A is pressed
    only when the eyes say the game waits for it, after reading the page, on a look taken right before the press.

    The TWO wait checks (measured by `gates/revert_step2.py`): the FIRST (the look that starts the reading)
    makes the reading delay start on a page that has finished printing (H2-outer, caught by
    `test_each_page_is_read_after_it_has_printed`); the SECOND (the gate) is REDUNDANT ALONE, because a wait
    the eyes report ends only on a press (H2-gate; the decomp citations are in that script). It stays: it is
    the press's logged gate, and it is what refuses A while printing if the first check is ever removed
    (H2-both is caught).

    THE STALL DETECTOR (step 2.1, the step-2 review's item 1): every frame it stands still, `advance` compares
    what the eyes see (`seen_now`) with the look before. A screen that waits for a press the eyes do not
    recognise (a list menu, a number input, a scrolling multichoice in a script) reads as "a scene plays" or
    "a text is printing", and before step 2.1 the AI watched it for the whole budget, three minutes, under that
    false reason. Now it returns "stuck:<reason>" (and says so in the run's log) once the screen has not changed
    for `stall_limit(look)` frames, and the caller reports it (`gates/test_hands.py` StallTests; the live arms
    XSTALL and XSTALLR of `gates/live_step2.py`, where the nurse's yes/no is made unknown to the eyes)."""
    start = hands.pad.frames
    last_page: str | None = None
    seen, still = None, 0  # what the eyes saw on the last busy frame; for how many looks it has not changed
    while hands.pad.frames - start < budget:
        look = hands.look()
        if until(look):
            return "done"
        if hands.faults.ungated_a:
            # FAULT: the naive driver. No wait gate and no menu check: A on the cadence until the goal.
            yield from hands.pad.press("A", why, UNGATED_GATE)
            continue
        ui = look.screen.ui
        if ui is not None:
            return f"menu:{ui.kind}"
        if look.screen.waits_for_button:
            page = page_text(look.screen.text)
            characters = new_characters(last_page, page)
            words = f"{page!r}" if page is not None else f"(a page the eyes cannot read; {look.screen.wait_reason})"
            yield from hands.pad.idle(hands.pad.reading_frames(characters), f"reading {characters} new characters: {words}")
            look = hands.look()  # THE GATE: the look right before the press
            if look.screen.waits_for_button and look.screen.ui is None:
                if page is not None:
                    hands.note("read", "text", page)
                yield from hands.pad.press("A", why, look.screen.wait_reason or "waits")
                last_page = page
            seen, still = None, 0
            continue
        reason = busy_reason(look)
        now = seen_now(look)
        if now != seen:
            seen, still = now, 0
        still += 1
        if still > stall_limit(look):
            hands.tell(f"{why}: STUCK: nothing on screen changed for {still - 1} frames while {reason} "
                       f"(scene {look.screen.scene!r}, {look.screen.game_state}; the limit {stall_limit(look)}): "
                       f"{look.digest()}")
            return f"{STUCK}{reason}"
        yield from hands.pad.busy(reason)
    return "budget"


def awaits_press(look: Observation) -> str | None:
    """(build step 5.1) What on screen WAITS FOR A PRESS, in words, or None: a text waiting for A or B
    (`ScreenState.waits_for_button`), or a menu that takes input (a yes/no, a list, a cursor). A screen like that never
    frees itself: a person presses."""
    screen = look.screen
    if screen.waits_for_button:
        return f"a text waits for a press ({screen.wait_reason or 'A/B'})"
    if screen.ui is not None and screen.ui.accepts_input:
        return f"the {screen.ui.kind} takes input"
    return None


def talk(hands: Hands, target: SeenObject, why: str, give_way: bool = False) -> Generator[None, None, bool]:
    """Start a conversation with `target`: face it (a short tap, checked), then A, but only while the player
    is FREE (nothing running, nothing on screen): the museum-greeter rule. Returns True once the game has
    started the conversation (a script runs or a text appears), False if it did not within the budget.

    `give_way` (build step 5.1, the step-5 verifier's FAILURE (b)): while it waits for the player to be free, a screen that
    WAITS FOR A PRESS (`awaits_press`: a scene began, its text waits for A) is not waited out: it returns False at once, so
    its caller plays the scene (measured 2026-10-14, live arm CH1M: a chat chosen on the frame PROF. BIRCH's scene landed
    stood here 1,200 frames while his text waited for A). The default (False) is the step-2 rule, unchanged for its callers."""
    for _ in range(4):
        look = hands.look()
        for _ in range(FREE_BUDGET):
            if player_free(look):
                break
            waiting = awaits_press(look) if give_way else None
            if waiting is not None:
                hands.tell(f"talk: {why}: {waiting}: a scene began before it could talk; it gives the screen back")
                return False
            yield from hands.pad.busy("waiting until the player is free to talk")
            look = hands.look()
        else:
            hands.tell(f"talk: {why}: the player was not free within {FREE_BUDGET} frames")
            return False
        seen = next((o for o in (look.view.objects if look.view else ()) if _same(o, target)), None)
        if seen is None:
            hands.tell(f"talk: {why}: the {target.kind} is not on screen any more")
            return False
        what = f"the {seen.kind} (gfx {seen.graphics_id})" if seen.source == "object" else f"the {seen.kind}"
        direction = talk_direction(look, seen)
        if direction is None:
            hands.tell(f"talk: {why}: {what} at ({seen.dx},{seen.dy}) is not in talking reach")
            return False
        if look.player.facing != direction:
            yield from hands.pad.turn(_BUTTON[direction], why, f"turn {direction} to face {what} at ({seen.dx},{seen.dy})")
            yield from hands.pad.idle(hands.pad.think_frames(), f"looking at {what} before talking")
            continue
        yield from hands.pad.press("A", why, f"talk: facing {direction} to {what} at ({seen.dx},{seen.dy}), "
                                             f"nothing running (no script, controls free, no text, no menu)")
        for _ in range(TALK_START_BUDGET):
            look = hands.look()
            screen = look.screen
            if screen.script_running or screen.text_box_open or screen.ui is not None or screen.waits_for_button:
                return True
            yield from hands.pad.busy("waiting for the person to answer")
        hands.tell(f"talk: {why}: no conversation started within {TALK_START_BUDGET} frames")
        return False
    hands.tell(f"talk: {why}: could not face the person")
    return False
