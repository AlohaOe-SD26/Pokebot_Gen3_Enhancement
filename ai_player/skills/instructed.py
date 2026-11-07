"""SKILL (chapter 5, 2026-11-05): THE INSTRUCTED CHOICE. A menu a scene FORCES on the player, chosen the way a person chooses
it: by reading what they were just told and picking the option the words name. Framework-free.

WHY (the chapter-5 development probe, `evidence/2026-11-01-chapter5-development-probe.txt`; the design read-only at e70a8469):
after the POKéNAV is handed over, Rustboro's scientist says "Please give our PRESIDENT a call." and the game opens a FORCED
start menu (`data/maps/RustboroCity/scripts.inc` RustboroCity_EventScript_MatchCallTutorial, `special
ScriptMenu_CreateStartMenuForPokenavTutorial`): every choice but POKéNAV loops back to "Please select the POKéNAV.", and
the POKéNAV then opens in a forced MATCH CALL mode until MR. STONE is called (`src/pokenav_menu_handler.c`
HandleMainMenuInputTutorial, `src/pokenav_match_call_list.c` CB2_HandleMatchCallInput). The AI had no skill for a
multichoice, so the navigator stopped on "an unexpected multichoice on screen" until its patience ran out. A person reads
the prompt and picks the option it names; inside the POKéNAV they follow the same instruction (MATCH CALL, then MR.
STONE, then CALL); when nothing more is named, they back out with B.

THE RULE (`named_option`): words are case-folded whole words (`WORD`). An option's LABEL WORDS are its words of 3 or more
letters, minus the player's own name (`PlayerState.name`: "MILO'S PC" is never named by "Milo booted up the PC."); a
label with none (the player's-name blank of the START menu, "MR.", "PC") is never named. A PAGE names an option when every
label word is a word of the page. The pages are read NEWEST FIRST; the first page that names an option not followed yet
decides: one option, chosen; two or more, AMBIGUOUS, nothing chosen (and said). The rule reads no flag, no mark, no
milestone, no knowledge file, no place and no count: only the words on screen (RULINGS 35 and 40; D1: a general skill).

THE INSTRUCTION (`Instructed.read_along`, a watcher on every look): the FIELD pages the player READ since the player was last
free (a page counts once it waits for a press, as `hands/dialogue.py` advance reads it); the transcript is cleared when the
player is free again. Pages read INSIDE an app (the call's own pages, game state not OVERWORLD) are conversation, never an
instruction (guard G3). A re-capture APPENDS (critic MENU-1): "Please select the POKéNAV." joins the pages before it, so the
POKéNAV's own menus are still named by "Using the MATCH CALL feature...". A run that began INSIDE a scene (no free look
yet) takes the message box's last message, the one the FIELD menu stands under, as read before the pages it reads itself
(critic MENU-4: the forced menu opens after `closemessage`, so that buffer is what was shown, not proof it is still drawn;
it is used only then. CONTROL: once the player has been free, a stale message in the buffer is never an instruction).

`used` (guard G4): the (kind, label) pairs followed since the player was last free: each named option is followed once,
so the call is never made twice. When a field menu comes back under NEW pages, its own kind's pairs are cleared (the
instruction was given again), and `FIELD_CHOICES_MAX` bounds how often.

THE EPISODE (`follow`): from the first instructed menu until the game is back in the field. A field multichoice that
nothing names is BACKED OUT OF when the AI opened it itself, and otherwise ends the run (below: THE MENU NOBODY ASKED FOR);
a GRID of options is refused with no press (its cursor moves in 2-D); a menu of an app (`APP_KINDS`) that nothing names
is backed out of with B, and a B the screen ignores is counted (`B_REFUSALS`). Every loop is bounded (`EPISODE_BUDGET`
frames, `MAX_DECISIONS`, `FIELD_CHOICES_MAX`), and every stop says why in the run's log.

THE MENU NOBODY ASKED FOR (chapter 6 stops round 5, 2026-11-06, the round-4 verifier's VR4-1; KI-132's class). MEASURED
(#106 arm A, both runs, `s53/ch6stops4/verify/wedge.py`): after a curiosity chat the AI CHOSE with MR. BRINEY on
DEWFORD's dock, his PETALBURG/SLATEPORT/EXIT multichoice opened (`data/maps/DewfordTown/scripts.inc`
DewfordTown_EventScript_Briney: `multichoicedefault ... MULTI_BRINEY_ON_DEWFORD, 2, FALSE` once STEVEN's letter is
delivered; B gives MULTI_B_PRESSED, which cancels like EXIT). Nothing read named an option, the skill left it to the
caller, and the play loop returned "stuck: an unexpected multichoice on screen" once a frame until the run's end (20,167
and 15,360 frames). THE RULE (the lead's decision for this round): a person who opens a field menu nobody asked them to
choose from, and wants none of its places, backs out of it, as the AI already backs out of an app menu nothing names:
  * the AI OPENED the scene itself when the last press it made while FREE, before the scene began, was its own A (it
    talked to someone or used something: `SceneOpener`, a watcher on the pad's own presses, never on the game's state);
  * such a field multichoice is cancelled with B (the game's MULTI_B_PRESSED), read from the screen: the menu leaves
    within `B_REACT_FRAMES`; a B the menu ignores is followed by the option whose words read EXIT or CANCEL
    (`CANCEL_WORDS`), chosen like any option; each cancel is counted (`backouts`: the goal that talked puts itself aside,
    `brain/goals.py` GoalRunner);
  * a menu still (or again) on screen after its cancel in the same scene, a cancel refused with no EXIT or CANCEL on the
    menu, or such a menu in a scene the AI did NOT open (the game forces it; a run that began inside a scene) is a FORCED
    menu nothing names: no press, said once, and `forced` keeps the stop, which ends the run AT ONCE (`mode.py` _play;
    KI-132's first fix direction) instead of one "stuck" a frame until the run's bound.
A forced menu the words DO name (the POKéNAV tutorial's) is chosen by THE RULE above, unchanged; an app menu nothing names
is backed out of exactly as before.

FAULT `AI_PLAYER_FAULT_NO_INSTRUCTED` (`options.py`): `mode._story_menu` never calls this skill (the code before it).
FAULT `AI_PLAYER_FAULT_INSTRUCTED_MISSTEP` (`options.py`, the live L4 arm): the FIRST field choice of a scene takes the next
option with a word instead of the named one (a person's slip of the thumb), so the forced menu loops back under "Please
select the POKéNAV." and the append rule is exercised live.
"""

from __future__ import annotations

import re
from collections.abc import Generator

from ai_player.eyes.observation import Observation
from ai_player.eyes.screens import PARAGRAPH, page_text
from ai_player.hands.dialogue import advance, player_free, seen_now
from ai_player.hands.menus import choose
from ai_player.hands.pad import Hands

__all__ = [
    "APP_KINDS",
    "B_REACT_FRAMES",
    "B_REFUSALS",
    "CANCEL_WORDS",
    "EPISODE_BUDGET",
    "FIELD_CHOICES_MAX",
    "GRID_KIND",
    "INSTRUCTED_KINDS",
    "Instructed",
    "MAX_DECISIONS",
    "MAX_PAGES",
    "STILL_PASSES_MAX",
    "SceneOpener",
    "label_words",
    "named_option",
    "said_words",
]

#: The menus the skill plays: a script's multichoice in the field, and the POKéNAV's three (`eyes/screens.py` pokenav_view).
INSTRUCTED_KINDS = frozenset({"multichoice", "pokenav_menu", "pokenav_list", "pokenav_options"})
#: The menus of an APP (the POKéNAV): a menu of one that nothing names is backed out of with B.
APP_KINDS = frozenset({"pokenav_menu", "pokenav_list", "pokenav_options"})
#: A grid of options (`eyes/screens.py` UI_TASKS): refused, with no press.
GRID_KIND = "multichoice_grid"
#: The episode's bound: 3 minutes of game time (the scripted reference path took 5,438 frames with generous waits).
EPISODE_BUDGET = 3 * 60 * 60
#: At most this many choices and B presses in one scene (the reference path makes 6: 4 choices and 2 B).
MAX_DECISIONS = 16
#: A B the screen ignored this many times ends the episode (the tutorial's list refuses B until MR. STONE is called).
B_REFUSALS = 2
#: Frames a B has to change what is on screen before it counts as refused.
B_REACT_FRAMES = 45
#: At most this many choices on a FIELD menu in one scene (a menu that keeps coming back: "Please select the POKéNAV.").
FIELD_CHOICES_MAX = 3
#: The transcript keeps the newest pages only (a long scene never grows it without bound).
MAX_PAGES = 40
#: Passes of the episode's loop in a row that let no frame pass before it stops (it never spins: every bound above counts
#: frames or choices, and a pass that presses nothing and waits for nothing would count neither).
STILL_PASSES_MAX = 50
#: Whole words, case-folded (the é of POKéNAV is a letter).
WORD = re.compile(r"[0-9a-zé]+")
#: A label word has at least this many letters ("MR." and "PC" carry none).
MIN_WORD = 3
#: (round 5, VR4-1) the words of the option that backs out of a field menu whose B is refused (MR. BRINEY's "EXIT").
CANCEL_WORDS = ("exit", "cancel")


def said_words(text: str) -> list[str]:
    """The whole words of `text`, case-folded (an apostrophe splits: "MILO'S" is "milo", "s")."""
    return WORD.findall(text.casefold().replace("’", "'"))


def label_words(label: str, own_name: str | None) -> tuple[str, ...]:
    """An option's words that a page must say to name it: its words of `MIN_WORD` letters or more, minus the words of the
    player's own name (guard G2). Empty: the option is never named (guard G1: the START menu's player's-name blank)."""
    own = set(said_words(own_name or ""))
    return tuple(w for w in said_words(label) if len(w) >= MIN_WORD and w not in own)


def named_option(options: tuple[str, ...] | list[str], pages: list[str], used: frozenset | set,
                 own_name: str | None) -> tuple[int | None, str]:
    """THE RULE (module docstring): (the index of the option the instruction names, the deciding page) or (None, why).
    Pages newest first; the first page naming an option whose label is not in `used` decides; two named there: None,
    ambiguous (guard G5)."""
    for page in reversed(pages):
        said = set(said_words(page))
        hits = []
        for index, label in enumerate(options):
            needed = label_words(label, own_name)
            if needed and label not in used and all(w in said for w in needed):
                hits.append(index)
        if len(hits) == 1:
            return hits[0], page
        if len(hits) > 1:
            return None, f"ambiguous: {page!r} names {[options[i] for i in hits]}"
    return None, "nothing on it is named by the instruction"


def _in_field(look: Observation) -> bool:
    """Back in the field with something the navigator plays: the player free, a field page waiting, or another menu."""
    screen = look.screen
    return (screen.game_state == "OVERWORLD" and not screen.fading
            and (player_free(look) or screen.waits_for_button or screen.ui is not None))


class SceneOpener:
    """(round 5, VR4-1) Did the AI OPEN the scene now on screen itself? A watcher on every look (`Hands.watchers`) that reads
    only the AI's OWN presses (`pad.history`) beside whether the player is free (`player_free`): the presses made after a
    free look were made while the player was free; when a free stretch ends (the first look that is not free), the scene
    was opened by the AI when the LAST press of that stretch was its A (`talk` faces the person, then presses A). A step
    into a trigger (a direction), a scene that began with no press, and a run that began inside a scene are not opened by
    it. A walking step ends a free stretch too (the player is settling); the next stretch decides again."""

    def __init__(self, pad) -> None:
        self.pad = pad
        self.was_free = False
        self.seen = len(getattr(pad, "history", ()))
        self.last_free_press: str | None = None
        self.opened = False

    def watch(self, look: Observation) -> None:
        free = player_free(look)
        history = getattr(self.pad, "history", ())  # (a pad that keeps no presses: nothing is ever opened by the AI)
        for entry in history[self.seen:]:
            self.last_free_press = entry.get("button")
        self.seen = len(history)
        if free and not self.was_free:
            # a new free stretch: no press made in it yet (what was pressed before it, in a scene, is dropped here)
            self.last_free_press = None
        if not free and self.was_free:
            self.opened = self.last_free_press == "A"
        self.was_free = free


class Instructed:
    """The skill's memory of ONE scene (since the player was last free): what was read, what was followed, the bounds."""

    #: (round 5, VR4-1) set by the play brain (`mode.py`): whether the AI opened the scene itself; None: never opened
    opener: SceneOpener | None = None
    #: (round 5) field menus nobody asked for that were backed out of, over the whole run (never reset by a free look)
    backouts = 0
    #: (round 5) the stop of a FORCED field menu nothing names (still on screen after its cancel, or in a scene the AI did
    #: not open): the play loop ends the run with it at once; the skill presses nothing more once it is set
    forced: str | None = None

    def __init__(self, misstep: bool = False) -> None:
        self.misstep = misstep
        self.pages: list[str] = []  # the field pages read since the player was last free
        self.waiting: str | None = None  # the field page waiting on the last look (read once while it waits)
        self.used: set[tuple[str, str]] = set()
        self.own_name: str | None = None
        self.free_seen = False  # the player has been free in this run (else the run began inside a scene)
        self.joined: list[str] | None = None  # the message box's pages, for a run that began inside a scene
        self.read_total = 0  # pages read in this scene, never capped (the re-capture test counts this, not `pages`)
        self.at_field: int | None = None  # `read_total` at the last field decision
        self.started: int | None = None
        self.decisions = 0
        self.refused = 0
        self.field_choices = 0
        self.slipped = False
        self.cancelled: set[tuple[str, tuple]] = set()  # (round 5) field menus backed out of in this scene

    def read_along(self, look: Observation) -> None:
        """A watcher on every look (`Hands.watchers`): the transcript of FIELD pages read, cleared once the player is free."""
        if look.player is not None and look.player.name:
            self.own_name = look.player.name
        screen = look.screen
        if player_free(look):
            if self.pages or self.used or self.started is not None or self.joined is not None:
                self.__init__(self.misstep)
                self.own_name = look.player.name
            self.free_seen = True
            return
        if screen.game_state != "OVERWORLD" or not screen.waits_for_button or screen.ui is not None:
            self.waiting = None
            return  # guard G3: a page inside an app (the call's) is conversation, never an instruction
        page = page_text(screen.text)
        if page and page != self.waiting:
            # a page is READ once per time it waits: the same words waiting again after a press (the loop's "Please select
            # the POKéNAV.") are read again
            self.pages.append(page)
            self.read_total += 1
            del self.pages[:-MAX_PAGES]
        self.waiting = page

    def instruction_now(self, look: Observation, field: bool) -> tuple[list[str], str]:
        """The instruction: the field pages read since the player was last free. For a run that began inside the scene
        (never free yet), the message a FIELD menu stands under, read once from its box, goes before them (never an app's
        text: the first field menu sets it)."""
        if field and not self.free_seen and self.joined is None:
            text = look.screen.text or ""
            self.joined = [part.strip() for part in text.split(PARAGRAPH) if part.strip()]
        if self.free_seen:
            return list(self.pages), "the pages read since the player was last free"
        return list(self.joined or []) + self.pages, ("the message the field menu stood under (the run began inside this "
                                                      "scene) and the pages read since")

    def follow(self, hands: Hands, kind: str, why: str) -> Generator[None, None, bool]:
        """Play the instructed menus from here until the game is back in the field (True once it chose or backed out at
        least once, a field menu backed out of included), or False: a STOP (a FORCED field menu nothing names, a grid, a
        bound run out, a menu that would not take a choice or a B; said once, at the end)."""
        made = 0
        if self.forced is not None:
            # (round 5) a forced field menu nothing names has already ended the run (`mode.py` _play): nothing more pressed
            return False
        if self.started is None:
            self.started = hands.pad.frames
        stop = None
        still, last_frames = 0, -1
        while stop is None:
            # never a loop that lets no frame pass (the play loop's STILL_PASSES_MAX rule): the bounds below count frames
            still = still + 1 if hands.pad.frames == last_frames else 0
            last_frames = hands.pad.frames
            if still > STILL_PASSES_MAX:
                stop = f"{still} passes in a row let no frame pass"
                break
            if hands.pad.frames - self.started > EPISODE_BUDGET:
                stop = f"the scene's menus took more than {EPISODE_BUDGET} frames"
                break
            if self.decisions >= MAX_DECISIONS:
                stop = f"{self.decisions} choices and backs-out in one scene (MAX_DECISIONS)"
                break
            look = hands.look()
            ui = look.screen.ui
            if ui is not None and ui.kind == GRID_KIND:
                stop = (f"a GRID of options {list(ui.options)}: its cursor moves in two directions; the skill chooses "
                        f"nothing on a grid (no press)")
                break
            if ui is None or ui.kind not in INSTRUCTED_KINDS:
                if ui is not None or _in_field(look):
                    return made > 0  # the field (or a menu the navigator knows): the scene goes on there
                outcome = yield from advance(hands, _in_field, f"{why}: the instructed menus",
                                             budget=max(1, EPISODE_BUDGET - (hands.pad.frames - self.started)))
                if outcome != "done" and not outcome.startswith("menu:"):
                    stop = f"between the menus: {outcome}"
                continue
            if not ui.accepts_input:
                yield from hands.pad.busy(f"watching: the {ui.kind} is not taking input yet")
                continue
            app = ui.kind in APP_KINDS
            pages, source = self.instruction_now(look, field=not app)
            if not app and self.at_field is not None and self.read_total > self.at_field:
                # the field menu came back under NEW pages: the instruction was given again (its own kind's pairs clear).
                # A COUNT OF PAGES READ, never `len(pages)`: that list is capped at MAX_PAGES, so once full a new page left
                # its length unchanged and the re-capture never fired (the gap check's cap probe, 2026-11-05)
                self.used = {pair for pair in self.used if pair[0] != ui.kind}
            used = {label for k, label in self.used if k == ui.kind}
            index, deciding = named_option(ui.options, pages, used, self.own_name)
            if index is not None:
                if not app:
                    self.field_choices += 1
                    self.at_field = self.read_total
                    if self.field_choices > FIELD_CHOICES_MAX:
                        stop = f"the {ui.kind} came back {self.field_choices} times in one scene (FIELD_CHOICES_MAX)"
                        break
                    if self.misstep and not self.slipped:
                        index = self._slip(ui.options, index)
                        self.slipped = True
                option = ui.options[index]
                hands.tell(f"{why}: the {ui.kind} {list(ui.options)}: {option!r} is named by {deciding!r} ({source})")
                hands.note("instructed", "choose", f"{ui.kind}: {option}",
                           {"kind": ui.kind, "option": option, "page": deciding, "pages": len(pages)})
                self.decisions += 1
                made += 1
                if not (yield from choose(hands, ui.kind, index, f"{why}: {option} (named by the instruction)")):
                    stop = f"the {ui.kind} did not take {option!r}"
                    break
                self.used.add((ui.kind, option))
                continue
            if not app:
                # (round 5, VR4-1) a FIELD menu nothing names (the module docstring's THE MENU NOBODY ASKED FOR)
                menu = (ui.kind, tuple(ui.options))
                opened = self.opener is not None and self.opener.opened
                if menu in self.cancelled or not opened:
                    reason = ("it is on screen again after the AI backed out of it: the game refuses the cancel"
                              if menu in self.cancelled else
                              "in a scene the AI did not open itself: the game forces it")
                    stop = self.forced = (f"a forced {ui.kind} {list(ui.options)} that nothing read names ({reason}): "
                                          f"no press; the run ends here")
                    break
                hands.tell(f"{why}: the {ui.kind} {list(ui.options)}: {deciding} ({source}, {len(pages)} pages): the AI "
                           f"opened it itself (it talked to someone) and wants none of it: it backs out")
                hands.note("instructed", "cancel", f"{ui.kind}: {deciding}", {"kind": ui.kind, "pages": len(pages),
                                                                              "options": list(ui.options)})
                self.decisions += 1
                left = yield from self._back_out(hands, ui, why)
                if left is None:
                    stop = self.forced = (f"a forced {ui.kind} {list(ui.options)} that nothing read names (it ignored B, "
                                          f"and no option reading {' or '.join(w.upper() for w in CANCEL_WORDS)} took it "
                                          f"off the screen): the run ends here")
                    break
                self.cancelled.add(menu)
                self.backouts += 1
                made += 1
                continue
            before = seen_now(look)
            hands.note("instructed", "back", f"{ui.kind}: {deciding}", {"kind": ui.kind, "pages": len(pages)})
            yield from hands.pad.press("B", why, f"{ui.kind} takes input; nothing on this menu is named by the "
                                                 f"instruction: B backs out")
            self.decisions += 1
            made += 1
            for _ in range(B_REACT_FRAMES):
                if seen_now(hands.look()) != before:
                    break
                yield from hands.pad.busy("watching the B take effect")
            else:
                self.refused += 1
                hands.tell(f"{why}: the {ui.kind} ignored B ({self.refused} of at most {B_REFUSALS})")
                if self.refused >= B_REFUSALS:
                    stop = f"the {ui.kind} ignored B {self.refused} times and nothing on it is named"
        hands.tell(f"{why}: the instructed menus stop: {stop}")
        hands.note("instructed", "stop", stop)
        return False

    def _back_out(self, hands: Hands, ui, why: str) -> Generator[None, None, str | None]:
        """(round 5, VR4-1) Back out of the field menu `ui` the AI opened itself, read from the screen: B (the game's
        MULTI_B_PRESSED), then, if the menu is still there after `B_REACT_FRAMES`, the option whose words read EXIT or
        CANCEL (`CANCEL_WORDS`). "B" or the option chosen once the menu has reacted; None when it ignored B and has no such
        option, or did not take it (a FORCED menu: the caller ends the run)."""
        menu = (ui.kind, tuple(ui.options))

        def still(seen: Observation) -> bool:
            now = seen.screen.ui
            return now is not None and (now.kind, tuple(now.options)) == menu

        yield from hands.pad.press("B", why, f"the {ui.kind} {list(ui.options)} takes input; nothing on it is named, the "
                                             f"AI opened it itself and wants none of it: B backs out")
        for _ in range(B_REACT_FRAMES):
            if not still(hands.look()):
                hands.tell(f"{why}: the {ui.kind} left the screen after B (backed out)")
                return "B"
            yield from hands.pad.busy("watching the B take effect")
        if not still(hands.look()):
            return "B"
        exits = [i for i, label in enumerate(ui.options) if any(w in CANCEL_WORDS for w in said_words(label))]
        hands.tell(f"{why}: the {ui.kind} ignored B; "
                   + (f"it takes {ui.options[exits[-1]]!r}, the option that backs out" if exits else
                      "no option on it reads EXIT or CANCEL"))
        if not exits:
            return None
        option = ui.options[exits[-1]]
        if not (yield from choose(hands, ui.kind, exits[-1], f"{why}: {option} (backing out of a menu nobody asked for)")):
            return None
        return option

    @staticmethod
    def _slip(options: tuple[str, ...], index: int) -> int:
        """FAULT misstep: the next option below the named one that has a word (a slip of the thumb)."""
        for step in range(1, len(options)):
            other = (index + step) % len(options)
            if said_words(options[other]):
                return other
        return index
