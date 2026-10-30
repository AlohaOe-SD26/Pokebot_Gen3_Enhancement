"""SKILL (R1, build spec 2026-10-29 section 3 (b)): the AI saves its game through the game's own START -> SAVE -> YES dialog
and CONTINUES it from the title, reading each page by its WORDS. Framework-free.

THE PAGES (build stage 1, the EYES, build spec E2 and section 4's word tests): the classifiers the save and continue skills
decide by. Every page's words are the game's own, from the pinned decomp:
  * the save dialog (`data/text/save.inc:2-29`): CONFIRM "Would you like to save the game?"; OVERWRITE "There is already a saved
    file. Is it okay to overwrite it?"; DIFFERENT "WARNING!" and three paragraph breaks before "Are you sure you want to save
    now and overwrite the other save file?" (`:16-24`); SAVING "SAVING… DON'T TURN OFF THE POWER."; SAVED "{PLAYER} saved the
    game."; ERROR "Save error." then one paragraph break (`:26-29`);
  * the main menu's error pages (`src/strings.c:35-38`, shown by `src/main_menu.c:649-660` and `:723-737` on printer 7):
    "The save file is corrupted. The previous save file will be loaded." (the game falls back to the save before),
    "The save file has been erased due to corruption or damage." (no save left), and "The internal battery has run dry..."
    (the clock, not the save).
The text the eyes report is decoded by `eyes/screens.py` decode_text: a line break is a space, a paragraph break PARAGRAPH, and
the apostrophe the game prints is "’"; `fold` folds all three, so a page compares like a person reads it.

THE SAVE (build stage 3, spec section 3 (b), `save_game`): START on a free screen, SAVE chosen by reading the cursor, then the
dialog played page by page. Each question is READ, and answered on the look that shows ITS WORDS (orchestrator ruling 3,
2026-10-29: stage 1 measured a lag frame after a NO where the yes/no still read as taking input under another text; every
answer therefore rests on the question's words read on the SAME look as the press, `_press_on`'s gate). CONFIRM: YES.
OVERWRITE: YES only when the cartridge's save is this game's own (`cart_is_own`, D17), else NO. DIFFERENT (another game's
save): NO. A question it cannot read: NO, never YES. No YES with fewer than `COMMIT_FRAMES_NEEDED` frames left in the run
(the YES is the only press that starts a write, and a skill the run's budget closes mid-write tears the save: F10). Every NO
backs out to a free screen (a NO reopens the START menu, `src/start_menu.c:823-827`). From the first look that shows the
WHOLE "SAVING…" page on, nothing is pressed until the SAVED or the ERROR page ("DON'T TURN OFF THE POWER"); that first look
calls `on_writing` ONCE, which is where the brain appends the save's memory line (D5: at the START of the write, so a kill
after the write never leaves a save the memory does not know). "saved" is declared ONLY on the SAVED page.

Pages are believed only where they can be NEW: a SAVING, SAVED or ERROR page counts only after a YES was pressed in this
dialog (printer 0's buffer keeps its last message, and stage 1 measured the next message expanded into it a frame before it
prints), and a SAVED page only once SAVING was seen (if it never was, the stamp is taken late, and said).

THE CONTINUE (spec section 3 (b), `continue_game`): from power-on, the movie and the title skipped as the intro does
(`skills/intro.py` skip_title), any main-menu error page READ and acknowledged, then on the main menu: no CONTINUE -> STOP
(the save is gone; never NEW GAME); CONTINUE with a TIME that matches no save line it wrote -> STOP; else CONTINUE, chosen on
a look that shows the same TIME, and the arrival VERIFIED (map, tile, and the party by PID and species) against the save
line. No STOP path presses anything once the main menu takes input.

BOUNDS (orchestrator ruling 1, 2026-10-29: every budget at least 2x the widest value measured so far; stage 1's eyes probe,
at the AI's slowest pacing): `SAVE_WRITE_BUDGET` 900 from the first whole SAVING look to SAVED (measured e3-4 to e5, 347 at
most); `SAVE_CLOSE_BUDGET` 600 from SAVED to a free screen (measured e5 to e7, 103); `SAVE_DIALOG_BUDGET` 3600 from START to
the write or to a free screen (measured START to free 1,603 at most; the spec's 3000 was under 2x of that, so it is 3600);
`COMMIT_FRAMES_NEEDED` 1500 (measured YES to free 624 at most: 2x is 1,248). The continue's budgets are PROVISIONAL until
step 6 measures the AI's own continues (spec section 3 (b)).
"""

from __future__ import annotations

import re
from collections.abc import Callable, Generator
from dataclasses import dataclass

from ai_player.brain.navigator import nav_free
from ai_player.eyes.observation import Observation
from ai_player.eyes.screens import PARAGRAPH, YES_NO
from ai_player.game_memory import party_of, where_of
from ai_player.hands.dialogue import busy_reason
from ai_player.hands.menus import move_cursor, wait_for_ui
from ai_player.hands.pad import Hands
from ai_player.skills.intro import skip_title

__all__ = [
    "ARRIVAL_BUDGET",
    "BACKOUT_PRESSES",
    "COMMIT_FRAMES_NEEDED",
    "CONFIRM_TEXT",
    "CONTINUE_BUDGET",
    "CORRUPTED_TEXT",
    "ERASED_TEXT",
    "ERROR_PAGES",
    "ERROR_PRESSES",
    "OVERWRITE_TEXT",
    "PAGE_PRESSES",
    "SAVE_CLOSE_BUDGET",
    "SAVE_DIALOG_BUDGET",
    "SAVE_FRAMES_NEEDED",
    "SAVE_PAGES",
    "SAVE_WRITE_BUDGET",
    "SAVING_TEXT",
    "ContinueResult",
    "continue_game",
    "error_page",
    "fold",
    "save_game",
    "save_page",
]

#: `data/text/save.inc` gText_ConfirmSave, gText_AlreadySavedFile, gText_SavingDontTurnOff (folded: `fold`).
CONFIRM_TEXT = "Would you like to save the game?"
OVERWRITE_TEXT = "There is already a saved file. Is it okay to overwrite it?"
SAVING_TEXT = "SAVING… DON'T TURN OFF THE POWER."
#: gText_DifferentSaveFile and gText_SaveError begin so (`:16`, `:26`).
DIFFERENT_START = "WARNING!"
ERROR_START = "Save error."
#: gText_PlayerSavedGame "{PLAYER} saved the game." (the player's name first).
_SAVED = re.compile(r"^.+ saved the game\.$")
#: `src/strings.c` gText_SaveFileCorrupted, gText_SaveFileErased; gText_BatteryRunDry begins so.
CORRUPTED_TEXT = "The save file is corrupted. The previous save file will be loaded."
ERASED_TEXT = "The save file has been erased due to corruption or damage."
BATTERY_START = "The internal battery has run dry."
#: What `save_page` can answer: each page of the save dialog, "printing" (a prefix of a known page, still being printed), or
#: None (not a page of the save dialog).
SAVE_PAGES = ("CONFIRM", "OVERWRITE", "DIFFERENT", "SAVING", "SAVED", "ERROR", "printing")

#: BOUNDS (module docstring; orchestrator ruling 1). From the first whole SAVING look to the SAVED (or ERROR) page.
SAVE_WRITE_BUDGET = 900
#: From the SAVED (or ERROR) page to a free screen held over two looks; also the frame bound of a back-out.
SAVE_CLOSE_BUDGET = 600
#: From START to the write (or to a free screen again). The spec's 3000 was under 2x of the measured 1,603 (ruling 1).
SAVE_DIALOG_BUDGET = 3600
#: No YES with fewer frames left in the run (the write and the close must fit: F10).
COMMIT_FRAMES_NEEDED = SAVE_WRITE_BUDGET + SAVE_CLOSE_BUDGET
#: The policy starts no save with fewer frames left (`brain/saving.py`; a coarse filter: the commit check is the guard). The
#: spec's 3000 is raised with SAVE_DIALOG_BUDGET, which it must cover (ruling 1).
SAVE_FRAMES_NEEDED = SAVE_DIALOG_BUDGET
#: B presses that may close the START menu or a save question; paragraph pages turned inside one dialog; A presses on a save
#: error; main-menu error pages acknowledged.
BACKOUT_PRESSES = 6
PAGE_PRESSES = 6
ERROR_PRESSES = 4
ERROR_PAGES = 3
#: SET in build step 6 (c) from the AI's OWN continues, at 2x the longest seen (spec section 8 step 6 (c); orchestrator
#: ruling 1's margin): power-on to the main menu taking input, widest 825 frames (a corrupted page read first; 400-418
#: with no page), and the CONTINUE press to the arrival held free, widest 159. Ten child Bs on development seeds 5405 and
#: 5406 (`gates/live_r1.py`, s53/r1build/build/s5-dev/ai-continue-spans.out); the provisional values were 6000 and 1200.
CONTINUE_BUDGET = 1700
ARRIVAL_BUDGET = 320
#: How often a press whose gate does not hold is tried again (`_press_on`), and how long a menu has to react to its A
#: (the same 45 frames as `hands/menus.py` choose).
PRESS_TRIES = 3
REACT_BUDGET = 45
#: Passes of the continue's loop in a row that let no frame pass before it stops (every pass plays, waits or presses: this
#: many in a row is a loop that does nothing).
STILL_PASSES_MAX = 50
#: The save's yes/no (`eyes/screens.py` YES_NO): YES on top.
_YES, _NO = YES_NO.index("YES"), YES_NO.index("NO")


def fold(text: str | None) -> str:
    """A text as compared: the paragraph mark and every run of whitespace one space, the game's apostrophe "’" a "'"."""
    if not text:
        return ""
    return " ".join(text.replace(PARAGRAPH, " ").replace("’", "'").split())


def save_page(text: str | None) -> str | None:
    """Which page of the save dialog `text` is (`SAVE_PAGES`), by its words (build spec E2). The WARNING and the error page
    are known by how they BEGIN (they have paragraph breaks, and the eyes may report them part printed); CONFIRM, OVERWRITE
    and SAVING only WHOLE (a part printed one is "printing": no answer and no stamp may rest on it); SAVED by its pattern.
    Anything else is None: never a page the AI may answer."""
    body = fold(text)
    if not body:
        return None
    if body.startswith(DIFFERENT_START):
        return "DIFFERENT"
    if body.startswith(ERROR_START):
        return "ERROR"
    for name, words in (("CONFIRM", CONFIRM_TEXT), ("OVERWRITE", OVERWRITE_TEXT), ("SAVING", SAVING_TEXT)):
        if body == words:
            return name
    if _SAVED.match(body):
        return "SAVED"
    if any(words.startswith(body) for words in (CONFIRM_TEXT, OVERWRITE_TEXT, SAVING_TEXT)):
        return "printing"
    return None


def error_page(text: str | None) -> str | None:
    """Which main-menu error page `text` is: "corrupted" (the previous save will be loaded), "erased" (no save left),
    "battery" (the clock's battery), or None. Whole pages only, but "battery" by its first sentence (it has a paragraph
    break, so its first page is what a reader sees first)."""
    body = fold(text)
    if body == CORRUPTED_TEXT:
        return "corrupted"
    if body == ERASED_TEXT:
        return "erased"
    if body.startswith(BATTERY_START):
        return "battery"
    return None


# ------------------------------------------------------------------ shared steps
def _ui_kind(look: Observation) -> str | None:
    ui = look.screen.ui
    return None if ui is None else ui.kind


def _page_of(look: Observation) -> str | None:
    """The save dialog's page on this look: only while the save dialog or its question is on screen (under the START menu
    the eyes' text is printer 0's LAST message, whatever it was)."""
    if _ui_kind(look) not in ("save_dialog", "save_yes_no"):
        return None
    return save_page(look.screen.text)


def _held_free(hands: Hands, budget: int, why: str) -> Generator[None, None, Observation | None]:
    """Watch, pressing nothing, until the player is free (`nav_free`) on two looks a decision pause apart (LESSONS PL-18:
    one free look is not a free screen). That second look, or None when `budget` frames passed first."""
    start = hands.pad.frames
    while hands.pad.frames - start < budget:
        look = hands.look()
        if nav_free(look):
            yield from hands.pad.idle(hands.pad.think_frames(), f"{why}: the screen looks free; a moment to be sure")
            again = hands.look()
            if nav_free(again):
                return again
            continue
        yield from hands.pad.busy(busy_reason(look))
    return None


def _press_on(hands: Hands, kind: str, index: int, check: Callable[[Observation], str | bool | None],
              why: str) -> Generator[None, None, bool]:
    """Choose option `index` of the `kind` menu: bring the cursor there by reading it (`hands/menus.py` move_cursor), then
    press A only on a look (THE GATE, the look right before the press) that shows the `kind` menu taking input with its
    cursor ON `index` and on which `check(look)` returns the words the choice rests on (orchestrator ruling 3: the
    question's words read on the SAME look as the press). `check` returns False to REFUSE the press outright (the caller
    then answers otherwise). True once the menu reacted (it closed, changed, or stopped taking input); at most
    `PRESS_TRIES` presses."""
    for _ in range(PRESS_TRIES):
        if not (yield from move_cursor(hands, kind, index, why)):
            return False
        look = hands.look()  # THE GATE
        ui = look.screen.ui
        words = check(look)
        if words is False:
            return False
        if ui is None or ui.kind != kind or not ui.accepts_input or ui.cursor != index or not words:
            yield from hands.pad.busy(f"{why}: the {kind} is not as read; looking again")
            continue
        option = ui.options[index] if 0 <= index < len(ui.options) else str(index)
        yield from hands.pad.press("A", why, f"{kind} cursor on {index} ({option}); {words}")
        for _ in range(REACT_BUDGET):
            look = hands.look()
            ui = look.screen.ui
            if ui is None or ui.kind != kind or not ui.accepts_input:
                return True
            yield from hands.pad.busy(f"waiting for the {kind} to take the choice")
    hands.tell(f"{why}: the {kind} did not take option {index}")
    return False


# ------------------------------------------------------------------ the save
def _answer(hands: Hands, page: str, yes: bool, frames_left: Callable[[], int],
            why: str) -> Generator[None, None, str]:
    """Answer the save question whose page is `page`: "yes", "no", "no: too few frames" (a YES its gate refused because
    fewer than `COMMIT_FRAMES_NEEDED` frames are left: answered NO instead), or "failed"."""
    refused = False

    def question_words(look: Observation) -> str | None:
        if save_page(look.screen.text) != page:
            return None
        return f"the page reads {page}: '{fold(look.screen.text)}'"

    def commit_check(look: Observation) -> str | bool | None:
        nonlocal refused
        left = frames_left()
        if left < COMMIT_FRAMES_NEEDED:
            refused = True
            return False
        said = question_words(look)
        return None if said is None else f"{said}; {left} frames left (a save needs {COMMIT_FRAMES_NEEDED})"

    if yes:
        if (yield from _press_on(hands, "save_yes_no", _YES, commit_check, why)):
            return "yes"
        if not refused:
            return "failed"
        hands.tell(f"save: {frames_left()} frames left in the run, fewer than the {COMMIT_FRAMES_NEEDED} a save needs to "
                   f"finish: NO, not YES (a save the run's end cuts is a torn save)")
    if (yield from _press_on(hands, "save_yes_no", _NO, question_words, why)):
        return "no: too few frames" if refused else "no"
    return "failed"


def _decide(page: str | None, cart_is_own: bool) -> tuple[bool, str]:
    """(YES?, why) for a question page (build spec 3 (b) step 4)."""
    if page == "CONFIRM":
        return True, "it wants to save"
    if page == "OVERWRITE":
        if cart_is_own:
            return True, "the saved file on the cartridge is this game's own"
        return False, "not saved: a saved file it does not know"
    if page == "DIFFERENT":
        return False, "not saved: another game's save"
    return False, "not saved: an unread question"


def _back_out(hands: Hands, why: str, result: str) -> Generator[None, None, str]:
    """BACK OUT (step 7): B on each look that shows the START menu or a save question TAKING INPUT (a B on the question is
    NO, `MENU_B_PRESSED`; a B on the menu closes it), until the screen is free over two looks; at most `BACKOUT_PRESSES`
    presses and `SAVE_CLOSE_BUDGET` frames. Called only before any SAVING page. `result` when free, else "stuck: ..."."""
    presses = 0
    start = hands.pad.frames
    while hands.pad.frames - start < SAVE_CLOSE_BUDGET:
        look = hands.look()
        if nav_free(look):
            yield from hands.pad.idle(hands.pad.think_frames(), f"{why}: backing out; the screen looks free")
            if nav_free(hands.look()):
                return result
            continue
        ui = look.screen.ui
        if ui is not None and ui.kind in ("start_menu", "save_yes_no") and ui.accepts_input:
            if presses >= BACKOUT_PRESSES:
                break
            what = f"the save question ('{fold(look.screen.text)}'): B is NO" if ui.kind == "save_yes_no" else \
                "the START menu: B closes it"
            yield from hands.pad.press("B", why, f"{ui.kind} takes input; {what}")
            presses += 1
            continue
        yield from hands.pad.busy(busy_reason(look))
    hands.tell(f"save: {why}: the dialog could not be closed ({presses} B presses; {result})")
    return "stuck: the dialog could not be closed"


def save_game(hands: Hands, why: str, cart_is_own: bool, frames_left: Callable[[], int],
              on_writing: Callable[[tuple | None, Observation], object],
              on_saved: Callable[[Observation], object]) -> Generator[None, None, str]:
    """Save the game through START -> SAVE -> YES (module docstring). Returns "saved" (or "saved; the box did not close
    within 600 frames"), "not saved: <why>" (the screen free again), or "stuck: <why>" (a dialog that could not be closed, a
    write that never ended, or a save the memory could not record: the caller ends the run).

    `cart_is_own`: D17's rule (`brain/saving.py` own_cart). `frames_left()`: the run's frames left (the commit check).
    `on_writing(play_time, look)`: called ONCE, on the first look with the WHOLE SAVING page (after a YES), with that look's
    play time `(hours, minutes)` (None if not read); it returns False when the memory line did not reach its file, and the
    skill then returns "stuck: the memory of this save could not be written" once the game has saved. `on_saved(look)`: on
    the SAVED page."""
    look = hands.look()
    if not nav_free(look):
        return "not saved: the player is not free (no START on this screen)"
    yield from hands.pad.press("Start", why, "the player is free on the overworld: START opens the menu")
    look = yield from wait_for_ui(hands, "start_menu", why)
    if look is None:
        return "not saved: the menu did not open"
    if "SAVE" not in look.screen.ui.options:
        hands.tell(f"save: {why}: the START menu has no SAVE ({list(look.screen.ui.options)})")
        return (yield from _back_out(hands, why, "not saved: the START menu has no SAVE"))
    yield from hands.pad.idle(hands.pad.think_frames(), f"looking at the START menu: {list(look.screen.ui.options)}")
    index = look.screen.ui.options.index("SAVE")

    def on_save(gate: Observation) -> str | None:
        ui = gate.screen.ui
        return "the option reads SAVE" if ui is not None and ui.options[index:index + 1] == ("SAVE",) else None

    if not (yield from _press_on(hands, "start_menu", index, on_save, why)):
        return (yield from _back_out(hands, why, "not saved: SAVE could not be chosen"))
    start = hands.pad.frames
    yes_given = False  # a YES was pressed in this dialog: SAVING / SAVED / ERROR pages can be NEW only after one
    pages_turned = 0
    while hands.pad.frames - start < SAVE_DIALOG_BUDGET:
        look = hands.look()
        kind = _ui_kind(look)
        page = _page_of(look)
        if yes_given and page in ("SAVING", "SAVED", "ERROR"):
            return (yield from _write(hands, why, look, on_writing, on_saved))
        if kind == "save_yes_no" and look.screen.ui.accepts_input:
            yield from hands.pad.idle(hands.pad.reading_frames(len(fold(look.screen.text))),
                                      f"reading the save question: '{fold(look.screen.text)}'")
            look = hands.look()  # the decision rests on the page as read now (and the press on its gate's own look)
            if _ui_kind(look) != "save_yes_no" or not look.screen.ui.accepts_input:
                continue  # it changed while it was read: look again
            page = save_page(look.screen.text)
            hands.note("read", "text", fold(look.screen.text), {"page": page})
            yes, reason = _decide(page, cart_is_own)
            answer = yield from _answer(hands, page, yes, frames_left, why)
            hands.tell(f"save: {why}: the question '{fold(look.screen.text)}' ({page}): {answer} ({reason})")
            if answer == "yes":
                yes_given = True
                continue
            if answer == "no: too few frames":
                reason = "not saved: too few frames left in the run to finish a save"
            elif answer == "failed":
                reason = "not saved: the question could not be answered"
            return (yield from _back_out(hands, why, reason))
        if kind == "save_dialog" and look.screen.waits_for_button:
            # a paragraph of the dialog's page waits (the WARNING's three, finding G2): read it, then A only turns the page
            if pages_turned >= PAGE_PRESSES:
                hands.tell(f"save: {why}: more than {PAGE_PRESSES} pages waited for A: it stops turning them")
                return (yield from _back_out(hands, why, "not saved: the dialog's pages did not end"))
            words = fold(look.screen.text)
            yield from hands.pad.idle(hands.pad.reading_frames(len(words)), f"reading the save dialog's page: '{words}'")
            look = hands.look()  # THE GATE
            if _ui_kind(look) == "save_dialog" and look.screen.waits_for_button:
                hands.note("read", "text", fold(look.screen.text), {"page": save_page(look.screen.text)})
                yield from hands.pad.press("A", why, f"a paragraph of the save dialog's page waits "
                                                     f"({look.screen.wait_reason or 'A/B'}): A only turns the page")
                pages_turned += 1
            continue
        if kind == "start_menu" and look.screen.ui.accepts_input:
            hands.tell(f"save: {why}: the START menu is back with no question answered: the dialog closed")
            return (yield from _back_out(hands, why, "not saved: the save dialog closed"))
        if kind is None and nav_free(look):
            hands.tell(f"save: {why}: the screen is free with no SAVED page: not saved")
            return "not saved: the box closed with no SAVED page"
        yield from hands.pad.busy(busy_reason(look))
    look = hands.look()
    hands.tell(f"save: {why}: the dialog did not reach the write within {SAVE_DIALOG_BUDGET} frames "
               f"(last on screen: {_ui_kind(look)} '{fold(look.screen.text)}')")
    return (yield from _back_out(hands, why, f"not saved: the dialog did not finish within {SAVE_DIALOG_BUDGET} frames"))


def _write(hands: Hands, why: str, look: Observation, on_writing: Callable, on_saved: Callable) -> Generator[None, None, str]:
    """From the first look of the write (a whole SAVING page after a YES, or SAVED / ERROR if SAVING was never seen whole):
    NO PRESS until the SAVED or the ERROR page; the play time on every SAVING look is kept and must not change (else it is
    told: the stamp may not be the written value); SAVED -> `on_saved`, then a held free screen; ERROR -> read, A at each wait
    the eyes report, until free."""
    stamp = look.progress.play_time if look.progress is not None else None
    if _page_of(look) == "SAVING":
        written = on_writing(stamp, look) is not False
        hands.note("read", "text", fold(look.screen.text), {"page": "SAVING", "play_time": stamp})
    else:
        hands.tell(f"save: {why}: the SAVING page was never read whole: the stamp is taken late ({stamp})")
        written = on_writing(stamp, look) is not False
    times = {stamp}
    start = hands.pad.frames
    while hands.pad.frames - start < SAVE_WRITE_BUDGET:
        page = _page_of(look)
        if page == "SAVING":
            times.add(look.progress.play_time if look.progress is not None else None)
        elif page == "SAVED":
            if len(times) > 1:
                hands.tell(f"save: {why}: the play time changed during the write ({sorted(times, key=str)}): the stamp "
                           f"{stamp} may not be the written value")
            hands.note("read", "text", fold(look.screen.text), {"page": "SAVED"})
            on_saved(look)
            free = yield from _held_free(hands, SAVE_CLOSE_BUDGET, "the save is done")
            if not written:
                return "stuck: the memory of this save could not be written (the game saved)"
            if free is None:
                hands.tell(f"save: {why}: saved, but the box did not close within {SAVE_CLOSE_BUDGET} frames")
                return f"saved; the box did not close within {SAVE_CLOSE_BUDGET} frames"
            return "saved"
        elif page == "ERROR":
            return (yield from _error(hands, why, look))
        elif _ui_kind(look) is None and nav_free(look):
            hands.tell(f"save: {why}: the box closed with no SAVED page after the write began: not saved")
            return "not saved: the box closed with no SAVED page"
        yield from hands.pad.busy("watching the save being written: DON'T TURN OFF THE POWER (no press)")
        look = hands.look()
    hands.tell(f"save: {why}: STUCK: the save did not finish within {SAVE_WRITE_BUDGET} frames (no press was made)")
    return f"stuck: the save did not finish within {SAVE_WRITE_BUDGET} frames"


def _error(hands: Hands, why: str, look: Observation) -> Generator[None, None, str]:
    """The save failed: "Save error. Please exchange the backup memory." READ, then A at each wait the eyes report (its
    paragraph break, then `SaveReturnErrorCallback` once its timer is 0), at most `ERROR_PRESSES`, until free."""
    words = fold(look.screen.text)
    hands.note("read", "text", words, {"page": "ERROR"})
    hands.tell(f"save: {why}: the game said: {words}")
    presses = 0
    start = hands.pad.frames
    while hands.pad.frames - start < SAVE_CLOSE_BUDGET:
        look = hands.look()
        if nav_free(look):
            yield from hands.pad.idle(hands.pad.think_frames(), f"{why}: the error is closed; the screen looks free")
            if nav_free(hands.look()):
                return f"not saved: the game said: {words}"
            continue
        if look.screen.waits_for_button and presses < ERROR_PRESSES:
            page = fold(look.screen.text)
            yield from hands.pad.idle(hands.pad.reading_frames(len(page)), f"reading the save error: '{page}'")
            look = hands.look()  # THE GATE
            if look.screen.waits_for_button and save_page(look.screen.text) == "ERROR":
                yield from hands.pad.press("A", why, f"the save error page waits ({look.screen.wait_reason or 'A/B'}): "
                                                     f"'{fold(look.screen.text)}'")
                presses += 1
            continue
        yield from hands.pad.busy(busy_reason(look))
    hands.tell(f"save: {why}: the save error did not close ({presses} A presses)")
    return "stuck: the save error page did not close"


# ------------------------------------------------------------------ the continue
@dataclass(frozen=True)
class ContinueResult:
    """What `continue_game` did. `outcome` "continued" or "stopped"; `why` the stop's sentence (or the continue's first line);
    `record` the save line it continued (the book's line, its payload included); `page` / `page_kind` the main-menu error
    page it read (`error_page`), if any; `newest` the record is the file's newest save; `undone` the `lost` lines after
    the record that the continue undoes (D12 (e)); `arrival` where it arrived and with whom, `arrived_at` that look's
    frame (the second of the two free looks); `lines` what it told.
    `may_retry` (R1 fix round, review R-2): the stop is a BOUND or a READ that failed (no main menu in time, the main menu
    gone while read, its TIME unreadable, CONTINUE not taken, no free arrival in time, a loop that let no frame pass, too
    many pages): nothing was restored and nothing played, so another continue undoes nothing this one did not, and the
    brain's `end` line says so (`stopped_before_restore`). False for the spec's own stops (section 3 (f): the save is
    gone, a TIME it does not remember, an arrival that differs), which stay CHOSEN ends: no later continue.
    `dropped` (U2 spec 2026-10-30 D13: USER RULING 53, "every such continue tells what it drops"): what it told it drops,
    `{"frames": the frames of play after the save by its own record (None: not recorded), "lost": the battles undone}`;
    never a play time or a map (D19: a continued game's memory is its save's)."""

    outcome: str
    why: str
    record: dict | None = None
    page: str | None = None
    page_kind: str | None = None
    newest: bool | None = None
    undone: tuple = ()
    arrival: dict | None = None
    arrived_at: int | None = None
    lines: tuple[str, ...] = ()
    may_retry: bool = False
    dropped: dict | None = None

    @property
    def continued(self) -> bool:
        return self.outcome == "continued"


def _shown_time(play_time) -> str:
    return f"{int(play_time[0])}:{int(play_time[1]):02d}" if play_time is not None else "?:??"


def _stopped(hands: Hands, why: str, page: str | None, page_kind: str | None,
             record: dict | None = None, arrival: dict | None = None, retry: bool = False) -> ContinueResult:
    """A STOP. `retry`: a bound or a failed read, not one of the spec's stops (`ContinueResult.may_retry`); it is given by
    name at each such stop, so a new stop is a CHOSEN end unless it says otherwise (fail closed, USER RULING 52)."""
    hands.tell(f"continue: STOP: {why}{' (nothing restored: another continue may try again)' if retry else ''}")
    return ContinueResult("stopped", why, record=record, page=page, page_kind=page_kind, arrival=arrival, lines=(why,),
                          may_retry=bool(retry))


def continue_game(hands: Hands, book, why: str) -> Generator[None, None, ContinueResult]:
    """CONTINUE the game from power-on (module docstring; spec section 3 (b) and (f)). `book` is the open memory file
    (`game_memory.MemoryBook`). Never NEW GAME: every path that cannot continue the save it remembers STOPS, and none of
    them presses anything once the main menu takes input."""
    page_words: str | None = None
    page_kind: str | None = None
    pages = 0
    start = hands.pad.frames
    still, last_frames = 0, -1
    while hands.pad.frames - start < CONTINUE_BUDGET:
        # (build stage 4) a bound on passes that let no frame pass too: the frame budget alone never ends a loop whose
        # pass presses and waits for nothing (found by the call-site census's mutant of `skip_title`'s call: a hang)
        still = still + 1 if hands.pad.frames == last_frames else 0
        last_frames = hands.pad.frames
        if still > STILL_PASSES_MAX:
            return _stopped(hands, f"{still} passes before the main menu let no frame pass", page_words, page_kind,
                            retry=True)
        look = hands.look()
        ui = look.screen.ui
        kind = None if ui is None else ui.kind
        if kind in ("intro_movie", "title"):
            yield from skip_title(hands, kind)
            continue
        if kind == "main_menu":
            if not ui.accepts_input:
                yield from hands.pad.busy(busy_reason(look))
                continue
            return (yield from _on_main_menu(hands, book, why, look, page_words, page_kind))
        if kind is None and look.screen.waits_for_button and look.screen.game_state != "OVERWORLD":
            # a main-menu error page (E4: printer 7's words while its task waits): READ, then A
            words = fold(look.screen.text)
            yield from hands.pad.idle(hands.pad.reading_frames(len(words)), f"reading the page: '{words}'")
            look = hands.look()  # THE GATE
            if look.screen.ui is None and look.screen.waits_for_button and fold(look.screen.text) == words:
                if pages >= ERROR_PAGES:
                    return _stopped(hands, f"more than {ERROR_PAGES} pages before the main menu (the last: '{words}')",
                                    page_words, page_kind, retry=True)
                found = error_page(words) or "other"
                hands.note("read", "text", words, {"page": found})
                hands.tell(f"continue: the game says: '{words}' ({found})")
                if found != "battery":
                    page_words, page_kind = words, found
                yield from hands.pad.press("A", why, f"the page waits ({look.screen.wait_reason or 'A/B'}): '{words}' "
                                                     f"read ({found})")
                pages += 1
            continue
        yield from hands.pad.busy(busy_reason(look))
    return _stopped(hands, f"the main menu did not come within {CONTINUE_BUDGET} frames of power-on", page_words, page_kind,
                    retry=True)


def _on_main_menu(hands: Hands, book, why: str, look: Observation, page_words: str | None,
                  page_kind: str | None) -> Generator[None, None, ContinueResult]:
    """The main menu takes input: STOP (no press) unless CONTINUE is offered with a TIME that one of its save lines has;
    else CONTINUE on a look that shows the same TIME, and the arrival verified."""
    ui = look.screen.ui
    yield from hands.pad.idle(hands.pad.think_frames(), f"looking at the main menu: {list(ui.options)}")
    look = hands.look()
    ui = look.screen.ui
    if ui is None or ui.kind != "main_menu" or not ui.accepts_input:
        return _stopped(hands, "the main menu went away while it was read", page_words, page_kind, retry=True)
    if "CONTINUE" not in ui.options:
        gone = page_words if page_kind == "erased" else "the main menu offers no CONTINUE"
        return _stopped(hands, f"the save is gone: {gone}", page_words, page_kind)
    if ui.hours is None or ui.minutes is None:
        return _stopped(hands, "the CONTINUE window's TIME cannot be read", page_words, page_kind, retry=True)
    time = (ui.hours, ui.minutes)
    hands.note("read", "text", f"CONTINUE TIME {_shown_time(time)}", {"time": list(time)})
    record = book.match_time(time)
    if record is None:
        known = ", ".join(f"{line['id']}@{_shown_time(line['play_time'])}" for line in book.saves()) or "none"
        return _stopped(hands, f"the game holds a save the AI does not remember making (TIME {_shown_time(time)}; its saves: "
                               f"{known})", page_words, page_kind)
    index = ui.options.index("CONTINUE")

    def same_time(gate: Observation) -> str | None:
        seen = gate.screen.ui
        if seen is None or seen.options[index:index + 1] != ("CONTINUE",) or (seen.hours, seen.minutes) != time:
            return None
        return f"the option reads CONTINUE, TIME {_shown_time(time)} = save {record['id']}'s stamp {_shown_time(record['play_time'])}"

    if not (yield from _press_on(hands, "main_menu", index, same_time, why)):
        return _stopped(hands, "CONTINUE could not be chosen", page_words, page_kind, record, retry=True)
    arrival = yield from _held_free(hands, ARRIVAL_BUDGET, "arriving in the continued game")
    if arrival is None:
        return _stopped(hands, f"the continued game did not reach a free overworld within {ARRIVAL_BUDGET} frames",
                        page_words, page_kind, record, retry=True)
    seen = {"where": where_of(arrival), "party": party_of(arrival)}
    remembered = {"where": record.get("where"), "party": record.get("party")}
    if seen != remembered:
        return _stopped(hands, f"the save it continued is not the one it remembers: the game shows {seen}, save "
                               f"{record['id']} remembers {remembered}", page_words, page_kind, record, seen)
    newest = book.newest_save()
    is_newest = newest is not None and newest["id"] == record["id"]
    where = record["where"]
    lines = [f"continued the save of {_shown_time(record['play_time'])} ({where.get('map')} "
             f"{','.join(str(v) for v in where.get('tile') or ())})"]
    if page_kind == "corrupted":
        lines.append("the game said the save was corrupted: it continues the save before it")
    elif not is_newest:
        lines.append("the game continued an OLDER save than its last, with no page")
    # (U2 spec D13) what this continue drops, by the AI's own record: the frames of play after the save (or "not
    # recorded": a session ended by its time limit wrote no end line) and the battles undone; no play time, no map
    drop = book.dropped_after(record["id"])
    dropped = {"frames": drop["frames"], "lost": drop["lost"]} if drop is not None else None
    if dropped is None:
        lines.append(f"what this continue drops is not known: save {record['id']} is not in the memory's live history")
    elif dropped["frames"] is None:
        lines.append(f"this continue drops the play after save {record['id']}, its frames not recorded (a session ended "
                     f"without its end line), and {dropped['lost']} battle(s) lost")
    else:
        lines.append(f"this continue drops {dropped['frames']} frames of play after save {record['id']}, and "
                     f"{dropped['lost']} battle(s) lost")
    undone = tuple(book.undone_losses(record["id"]) or ())
    if undone:
        lines.append(f"this continue undoes {len(undone)} battle{'s' if len(undone) != 1 else ''} lost after save "
                     f"{_shown_time(record['play_time'])}")
    for line in lines:
        hands.tell(f"continue: {line}")
    return ContinueResult("continued", lines[0], record=record, page=page_words, page_kind=page_kind, newest=is_newest,
                          undone=undone, arrival=seen, arrived_at=arrival.frame, lines=tuple(lines), dropped=dropped)
