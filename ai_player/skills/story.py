"""SKILLS for playing the STORY (build step 5): walking UP to someone or something and dealing with it, with the AI's own
hands and navigator. Framework-free.

  approach       walk to a tile from which a person or a thing on screen can be TALKED to: beside it, or across a counter
                 (the nurse, the clerk); the navigator's own walk (`brain/navigator.py` go_to), bounded
  talk_to        approach someone and TALK: face them, A only while the player is free (`hands/dialogue.py` talk), then
                 the whole conversation and whatever it leads to (a question, a battle, a scene) played through the
                 navigator's `handle` with the brain's own answers (`answer_question`)
  use_thing      the same for a THING on a wall (the clock): a sign-like bg event, faced and pressed
  pick_up        an ITEM BALL seen on the map: approach, face, A, read "{PLAYER} found ..." (the eyes' text), and CHECK the
                 bag grew (pillar 4: "pick up every visible item it can reach")
  enter_door     walk to a door the AI SEES (by its look: the POKéMON CENTER's, the MART's) and walk in
  heal_at_center inside a POKéMON CENTER: the nurse by her look, across the counter, `hands/menus.py` nurse_heal
  shop_at_mart   inside a POKéMON MART: the clerk by his look, across the counter, `hands/menus.py` mart_buy per item
  choose_starter PROF. BIRCH's bag: the cursor READ (`eyes/screens.py` STARTER_OPTIONS) and moved Left / Right to the
                 starter the personality drew, then A
  answer_question a yes/no in a scene answered by its WORDS, the way a person goes along with the story: YES to
                 "Do you choose this POKéMON?", to PROF. BIRCH's "a good idea to go see {RIVAL}?", to the nurse; NO to a
                 nickname (this player keeps names as they are); YES otherwise, with the reason logged. (The step-3
                 explorer's rule, NO to everything, stays the navigator's default for its own brains.)
Every loop is bounded; every press has its gate (the pad refuses one without); every outcome is a string the goal
manager logs.
"""

from __future__ import annotations

from collections.abc import Generator

from ai_player.brain.navigator import Navigator, Target, nav_free
from ai_player.eyes.observation import Observation, SeenObject
from ai_player.eyes.screens import STARTER_OPTIONS, page_text
from ai_player.hands.dialogue import player_free, talk, talk_direction
from ai_player.hands.menus import MART_CLERK_GFX, NURSE_GFX, mart_buy, nurse_heal, wait_for_ui
from ai_player.hands.pad import Hands
from ai_player.skills.flee import in_battle
from ai_player.world.memory import DIRECTIONS, OPPOSITE, moved

__all__ = [
    "APPROACH_BUDGET",
    "QUESTION_RULES",
    "SCENE_ROUNDS",
    "answer_question",
    "approach",
    "choose_starter",
    "enter_door",
    "heal_at_center",
    "pick_up",
    "play_out",
    "shop_at_mart",
    "stand_tiles",
    "talk_to",
    "use_thing",
]

#: Frames a walk up to someone may take (the navigator's intent budget).
APPROACH_BUDGET = 4000
#: How many interruptions (scenes, battles) one `play_out` may play before it gives up: a long story scene raises several.
SCENE_ROUNDS = 12
#: Presses a starter cursor may take to reach its ball.
STARTER_MOVES = 8
#: The QUESTIONS a person answers by their words (lower-case words -> (yes, why)); first match wins. Anything else: YES,
#: a person goes along with what the story asks (`answer_question`).
QUESTION_RULES: tuple[tuple[str, bool, str], ...] = (
    ("nickname", False, "a nickname: this player keeps the name a Pokemon has"),
    ("do you choose this", True, "the Pokemon it chose from PROF. BIRCH's bag"),
    ("good idea to go see", True, "PROF. BIRCH's suggestion to go see the rival: a person goes along with it"),
    ("rest your", True, "the nurse offers to heal the party"),
)


def answer_question(look: Observation) -> tuple[bool, str]:
    """(yes, why) for the yes/no on screen, by the WORDS the eyes read (module docstring)."""
    words = (page_text(look.screen.text) or "").lower()
    if look.screen.game_state == "CHOOSE_STARTER":
        return True, "the starter's 'Do you choose this POKéMON?' in PROF. BIRCH's bag: YES, the one it chose"
    for key, yes, why in QUESTION_RULES:
        if key in words:
            return yes, f"{why} ({words[:60]!r})"
    return True, f"a question in the story ({words[:60]!r}): YES, a person goes along with what the game asks"


def stand_tiles(look: Observation, nav: Navigator, target: SeenObject) -> list[tuple[int, int]]:
    """The tiles from which `target` can be talked to, nearest first: beside it (walkable, known, nobody there), or two
    away across a COUNTER tile (the nurse and the clerk stand behind one: `hands/dialogue.py` talk_direction)."""
    found = nav.where(look)
    if found is None:
        return []
    memory, here = found
    out = []
    for direction, (dx, dy) in DIRECTIONS.items():
        beside = (target.x + dx, target.y + dy)
        if memory.passable(beside) and (beside not in memory.objects_now or beside == here):
            out.append(beside)
        across = (target.x + 2 * dx, target.y + 2 * dy)
        between = memory.fact(beside)
        if between is not None and between.behavior == "COUNTER" and memory.passable(across):
            out.append(across)
    return sorted(set(out), key=lambda xy: (abs(xy[0] - here[0]) + abs(xy[1] - here[1]), xy))


def _same(look: Observation, target: SeenObject) -> SeenObject | None:
    """The same person / thing on a later look: a person by its map id, a bg event by its tile."""
    for seen in look.view.objects if look.view is not None else ():
        if seen.source == target.source and (seen.local_id == target.local_id if seen.source == "object"
                                             else (seen.x, seen.y) == (target.x, target.y)):
            return seen
    return None


def approach(hands: Hands, nav: Navigator, target: SeenObject, why: str,
             budget: int = APPROACH_BUDGET) -> Generator[None, None, str]:
    """Walk to a tile from which `target` can be talked to. Returns "reached", "battle" (something stopped the walk), or
    "unreachable: ..."."""
    look = hands.look()
    seen = _same(look, target) or target
    if talk_direction(look, seen) is not None:
        return "reached"
    for spot in stand_tiles(look, nav, seen)[:6]:
        outcome = yield from nav.go_to(spot, f"{why}: walk up to the {seen.kind} at {(seen.x, seen.y)}", budget)
        look = hands.look()
        if in_battle(look) or not nav_free(look):
            return "battle" if in_battle(look) else "scene"
        now = _same(look, target)
        if now is not None and talk_direction(look, now) is not None:
            # a person who has just walked up to someone looks at them before speaking (measured 2026-10-14: an A on the
            # frame the walk ended, the step's last frames still playing, started no conversation with the nurse: "no
            # conversation started within 90 frames", then the second try worked)
            yield from hands.pad.idle(hands.pad.think_frames(), f"walked up to the {now.kind} at {(now.x, now.y)}: "
                                                                f"looking at them before speaking")
            return "reached"
        if outcome.startswith("stuck") and "battle" in outcome:
            return "battle"
    return f"unreachable: no tile from which the {seen.kind} at {(seen.x, seen.y)} can be talked to was reached"


def play_out(hands: Hands, nav: Navigator, why: str) -> Generator[None, None, str | None]:
    """Whatever is on screen after a talk (the conversation, a question, a battle, a scene) played to its end through the
    navigator's `handle` (its battler fights, its `answer` answers, its `on_menu` takes a starter's bag). None once the
    player is free again; otherwise why it stopped."""
    for _ in range(SCENE_ROUNDS):
        look = hands.look()
        if nav_free(look):
            return None
        stop = yield from nav.handle(look, why)
        if stop is not None:
            return stop
    return f"stuck: {SCENE_ROUNDS} scenes and battles in a row after {why}"


def talk_to(hands: Hands, nav: Navigator, target: SeenObject, why: str) -> Generator[None, None, str]:
    """Approach `target` and talk to it; then play out what it leads to. Returns "talked" or why not."""
    reached = yield from approach(hands, nav, target, why)
    if reached in ("battle", "scene"):
        stop = yield from play_out(hands, nav, why)
        return f"interrupted on the way: {stop or 'played out'}"
    if reached != "reached":
        return reached
    look = hands.look()
    seen = _same(look, target)
    if seen is None:
        return f"the {target.kind} is not on screen any more"
    if not (yield from talk(hands, seen, why)):
        return f"the {target.kind} did not answer"
    stop = yield from play_out(hands, nav, why)
    return "talked" if stop is None else f"talked; then {stop}"


def use_thing(hands: Hands, nav: Navigator, thing: SeenObject, why: str) -> Generator[None, None, str]:
    """A thing on a wall or the floor (a bg event: the clock) is used like a person: approach, face, A."""
    return (yield from talk_to(hands, nav, thing, why))


def pick_up(hands: Hands, nav: Navigator, ball: SeenObject, why: str) -> Generator[None, None, str]:
    """Pick up the item ball `ball`: approach, face, A, read what was found, and check the bag (its balls and healing
    items, what the eyes see of it) or the words. Returns "picked up: <words>" or why not."""
    before = hands.look()
    count = _items(before)
    pages: list[str] = []

    def listen(look: Observation) -> None:
        if look.screen.waits_for_button and look.screen.text:
            page = page_text(look.screen.text)
            if page and page not in pages:
                pages.append(page)

    hands.watchers.append(listen)
    try:
        outcome = yield from talk_to(hands, nav, ball, why)
    finally:
        hands.watchers.remove(listen)
    after = _items(hands.look())
    # the words the game says for an item ball (`data/scripts/obtain_item.inc`): "{PLAYER} found one POTION!" plays under a
    # fanfare and may never wait for a press, so "... put away the POTION in the ITEMS POCKET." is often the only page that
    # waits (measured 2026-10-14, the chapter-2 development run c2b: the Potion picked up, its flag set, and only that page)
    found = next((p for p in pages if any(w in p.lower() for w in ("found", "obtained", "put the", "put away the"))), None)
    if outcome != "talked":
        return f"not picked up: {outcome}"
    if found is None:
        return f"not picked up: no 'found' words read (pages {pages[:3]})"
    grew = "" if count is None or after is None else f"; balls + healing items {count} -> {after}"
    return f"picked up: {found!r}{grew}"


def _items(look: Observation) -> int | None:
    if look.bag is None:
        return None
    return look.bag.ball_total + sum(quantity for _, quantity in look.bag.healing)


def enter_door(hands: Hands, nav: Navigator, door: tuple[int, int], why: str,
               budget: int = APPROACH_BUDGET) -> Generator[None, None, str]:
    """Walk to the door at `door` (a tile of the current map the AI has seen) and in: from the tile below it, pressing up
    (a door is walked into from below: `brain/navigator.py` exit_press). Returns "entered" or why not."""
    look = hands.look()
    found = nav.where(look)
    if found is None:
        return "the player's tile is not known"
    memory, here = found
    stand = moved(door, OPPOSITE["up"])
    if not memory.passable(stand):
        return f"the tile below the door at {door} is not a known walkable tile"
    key = nav.world.current
    if here != stand:
        outcome = yield from nav.go_to(stand, f"{why}: to the door at {door}", budget)
        look = hands.look()
        if nav.world.current != key:
            return "entered"  # (the walk itself went in: the door is ON the way)
        if not nav_free(look):
            stop = yield from play_out(hands, nav, why)
            if stop is not None:
                return f"interrupted: {stop}"
        if nav.where(hands.look()) is None or nav.where(hands.look())[1] != stand:
            return f"the door's stand tile {stand} was not reached: {outcome}"
    result = yield from nav.use_exit(Target("door", stand, why, exit=door, direction="up"), why)
    if result == "used" or nav.world.current != key:
        yield from nav.settle(why)
        nav.take_changes()
        return "entered"
    if result in ("battle", "scene"):
        stop = yield from play_out(hands, nav, why)
        return "entered" if nav.world.current != key else f"interrupted at the door: {stop or 'played out'}"
    return f"the door at {door} did not open ({result})"


def heal_at_center(hands: Hands, nav: Navigator, why: str = "heal at the POKéMON CENTER") -> Generator[None, None, str]:
    """Inside a POKéMON CENTER: the nurse by her look (`hands/menus.py` NURSE_GFX), approached across the counter, then
    `nurse_heal`. Returns "healed" or why not."""
    look = hands.look()
    nurse = _person(look, NURSE_GFX)
    if nurse is None:
        return "no nurse in sight"
    reached = yield from approach(hands, nav, nurse, why)
    if reached != "reached":
        return f"could not reach the nurse: {reached}"
    return (yield from nurse_heal(hands, why))


def shop_at_mart(hands: Hands, nav: Navigator, wants: list[tuple[str, int]],
                 why: str = "shop at the POKéMON MART") -> Generator[None, None, list[str]]:
    """Inside a POKéMON MART: the clerk by his look, approached across the counter, then one `mart_buy` per item wanted
    (a conversation each). Returns each purchase's outcome."""
    out = []
    for item, count in wants:
        look = hands.look()
        clerk = _person(look, MART_CLERK_GFX)
        if clerk is None:
            out.append(f"{item}: no clerk in sight")
            break
        reached = yield from approach(hands, nav, clerk, why)
        if reached != "reached":
            out.append(f"{item}: could not reach the clerk: {reached}")
            break
        outcome = yield from mart_buy(hands, item, count, f"{why}: {count} x {item}")
        out.append(f"{item} x{count}: {outcome}")
        if not player_free(hands.look()):
            stop = yield from play_out(hands, nav, why)
            if stop is not None:
                out.append(f"after: {stop}")
                break
    return out


def _person(look: Observation, graphics_id: int) -> SeenObject | None:
    people = [o for o in (look.view.objects if look.view else ()) if o.source == "object" and o.graphics_id == graphics_id]
    return min(people, key=lambda o: (abs(o.dx) + abs(o.dy), o.local_id)) if people else None


def choose_starter(hands: Hands, starter: str, why: str) -> Generator[None, None, bool]:
    """PROF. BIRCH's bag: bring the cursor to `starter` by READING it (Left / Right) and press A on its look. True once the
    bag took the choice (the question that follows is the scene's, answered by `answer_question`)."""
    if starter not in STARTER_OPTIONS:
        hands.tell(f"{why}: {starter!r} is not in the bag {STARTER_OPTIONS}")
        return False
    target = STARTER_OPTIONS.index(starter)
    look = yield from wait_for_ui(hands, "choose_starter", why)
    if look is None:
        return False
    yield from hands.pad.idle(hands.pad.think_frames(), f"looking at the three POKé BALLS {list(STARTER_OPTIONS)}: the cursor "
                                                        f"on {look.screen.ui.cursor}, wanted {target} ({starter})")
    for _ in range(STARTER_MOVES * 30):
        look = hands.look()
        ui = look.screen.ui
        if ui is None or ui.kind != "choose_starter":
            hands.tell(f"{why}: the bag closed while its cursor was being moved")
            return False
        if not ui.accepts_input or ui.cursor is None:
            yield from hands.pad.busy("waiting for the bag's cursor to settle")
            continue
        if ui.cursor == target:
            yield from hands.pad.press("A", why, f"choose_starter cursor on {target} ({starter})")
            for _ in range(600):
                look = hands.look()
                ui = look.screen.ui
                if ui is None or ui.kind != "choose_starter" or not ui.accepts_input:
                    return True
                yield from hands.pad.busy("waiting for the bag to take the choice")
            return False
        button = "Right" if ui.cursor < target else "Left"
        yield from hands.pad.press(button, why, f"choose_starter cursor on {ui.cursor} ({STARTER_OPTIONS[ui.cursor]}), "
                                                f"wanted {target} ({starter}): one step {button.lower()}")
    hands.tell(f"{why}: the bag's cursor did not reach {starter}")
    return False
