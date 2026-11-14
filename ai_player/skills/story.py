"""SKILLS for playing the STORY (build step 5): walking UP to someone or something and dealing with it, with the AI's own
hands and navigator. Framework-free.

  approach       walk to a tile from which a person or a thing on screen can be TALKED to: beside it, or across a counter
                 (the nurse, the clerk); the navigator's own walk (`brain/navigator.py` go_to), bounded. Someone seen to
                 MOVE is met the way a person meets someone walking round a room (`meet_walker`): watch where they walk,
                 stand beside the way facing it, and speak when they step in front
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

from collections import deque
from collections.abc import Generator

from ai_player.brain.navigator import Navigator, Target, nav_free
from ai_player.eyes.observation import Observation, SeenObject
from ai_player.eyes.screens import STARTER_OPTIONS, page_text
from ai_player.hands.dialogue import advance, player_free, talk, talk_direction
from ai_player.hands.menus import GAVE_WAY, MART_CLERK_GFX, NURSE_GFX, choose, mart_buy, nurse_heal
from ai_player.hands.pad import Hands
from ai_player.skills.flee import in_battle
from ai_player.world.memory import DIRECTIONS, OPPOSITE, moved

__all__ = [
    "APPROACH_BUDGET",
    "LIST_WAIT",
    "NOT_FOR_SALE",
    "QUESTION_RULES",
    "SCENE_ROUNDS",
    "STARTER_WAIT",
    "APPROACH_SPOTS",
    "ASIDE_STEPS",
    "WALKER_MEETINGS",
    "WALKER_SPOTS",
    "WALKER_STILL",
    "WALKER_WAIT",
    "WALKER_WATCH",
    "answer_question",
    "approach",
    "bag_or_its_question",
    "choose_starter",
    "leave_shop",
    "enter_door",
    "heal_at_center",
    "meet_walker",
    "pick_up",
    "play_out",
    "shop_at_mart",
    "stand_tiles",
    "talk_to",
    "use_thing",
    "waiting_spots",
    "watch_walker",
]

#: Frames a walk up to someone may take (the navigator's intent budget).
APPROACH_BUDGET = 4000
#: How many interruptions (scenes, battles) one `play_out` may play before it gives up: a long story scene raises several.
SCENE_ROUNDS = 12
#: Presses a starter cursor may take to reach its ball.
STARTER_MOVES = 8
#: (build step 5.1) What `hands/menus.py` mart_buy answers when the item is not on the list it READ (the list stays open).
NOT_FOR_SALE = "is not for sale here"
#: (build step 5.1) Frames a mart's item list may take to take input (it slides in: `CB2_BuyMenu`).
LIST_WAIT = 300
#: (build step 5.1) Frames PROF. BIRCH's bag may take to take input again (a ball opening: measured 2026-10-14, the yes/no
#: came 39 frames after the A in the live arm CH1T): a bound, never a wait for something that will not come.
STARTER_WAIT = 600
#: (chapter 6, 2026-11-05) SOMEONE WHO WALKS ROUND and never stands still: MR. BRINEY in his cottage once PEEKO is home
#: (pinned decomp `data/maps/Route104_MrBrineysHouse/scripts.inc` SetBrineyPeekoPos: MOVEMENT_TYPE_WALK_SEQUENCE_DOWN_LEFT_
#: UP_RIGHT from (9,3), range 3; `src/event_object_movement.c` MoveNextDirectionInSequence takes the next step the frame the
#: last one ends, so his tile changes every 16-17 frames round his table, and PEEKO walks the same round three steps ahead).
#: Walking to the tile beside where he WAS seen arrives after he has gone: the KI-134 B arm (ledger #98) made 54 talk goals
#: in the Story run and none landed. A person watches where he walks, stands beside the way facing it, and speaks when he
#: steps in front (`meet_walker`). How long it watches before choosing where to wait (his round of 12 steps is ~200 frames;
#: the watch ends sooner once the way comes back round to where it began):
WALKER_WATCH = 240
#: Someone who keeps one tile this many frames is not walking round (a step takes 16 frames; a wanderer waits 32 or more
#: between steps, `src/event_object_movement.c` sMovementDelaysMedium/Short): they are walked up to the ordinary way.
WALKER_STILL = 24
#: How long it waits beside the way, facing it, for them to step in front (three of MR. BRINEY's rounds): a bound.
WALKER_WAIT = 600
#: Waiting places tried, nearest first.
WALKER_SPOTS = 3
#: How many times one approach meets a walker (a second when the one met first turned out to keep still, then walked on).
WALKER_MEETINGS = 2
#: Tiles beside a person walked to at most, in one approach (the step-5 number, unchanged).
APPROACH_SPOTS = 6
#: How far it steps aside, at most, when it finds it stands where people walk (a walker meets the player on its way and
#: walks in place: MOVEMENT_TYPE_WALK_SEQUENCE's collision rule).
ASIDE_STEPS = 3
_FACE = {"up": "Up", "down": "Down", "left": "Left", "right": "Right"}
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


def _moved(now: SeenObject, before: SeenObject) -> bool:
    """A PERSON (an object event) is on another tile than before: they walk."""
    return now.source == "object" and (now.x, now.y) != (before.x, before.y)


def approach(hands: Hands, nav: Navigator, target: SeenObject, why: str,
             budget: int = APPROACH_BUDGET) -> Generator[None, None, str]:
    """Walk to a tile from which `target` can be talked to. Returns "reached", "battle" (something stopped the walk), or
    "unreachable: ...". (Chapter 6) Someone seen on another tile than where they were chosen, or than where a walk up to
    them began, is MOVING: `meet_walker` meets them (at most `WALKER_MEETINGS` times an approach). Someone who turns out to
    keep still is walked up to the ordinary way, AIMED at where they stand now: once they have moved, the tiles beside them
    are worked out again from their new tile (the tiles already tried left out). Someone who never moves is walked up to
    exactly as before: the tiles beside them, nearest first, at most `APPROACH_SPOTS`."""
    look = hands.look()
    began = look.frame
    seen = _same(look, target) or target
    if talk_direction(look, seen) is not None:
        return "reached"
    meetings = 0
    if _moved(seen, target):
        meetings += 1
        met = yield from meet_walker(hands, nav, seen, why, since=began)
        if met != "standing":
            return met
        # the look the meeting ended on (it found them keeping still): beside them already, the first spot below is the
        # player's own tile (`stand_tiles` keeps it), and the walk to it ends at once
        look = hands.last
        seen = _same(look, target) or seen
    spots = stand_tiles(look, nav, seen)[:APPROACH_SPOTS]
    tried: list[tuple[int, int]] = []
    while spots and len(tried) < APPROACH_SPOTS:
        spot = spots.pop(0)
        tried.append(spot)
        battles = len(nav.battle_log)
        outcome = yield from nav.go_to(spot, f"{why}: walk up to the {seen.kind} at {(seen.x, seen.y)}", budget)
        look = hands.look()
        if in_battle(look) or not nav_free(look):
            return "battle" if in_battle(look) else "scene"
        now = _same(look, target)
        if now is not None and _moved(now, seen):
            # (chapter 6) they walked on while the player walked up: met as someone walking round (the pause below would
            # lose even one who is beside the player now: MR. BRINEY takes a step every 16 frames)
            if meetings < WALKER_MEETINGS:
                meetings += 1
                met = yield from meet_walker(hands, nav, now, why, since=began)
                if met != "standing":
                    return met
                look = hands.last  # the look the meeting ended on
                now = _same(look, target) or now
            seen = now
            spots = [s for s in stand_tiles(look, nav, seen) if s not in tried][:APPROACH_SPOTS - len(tried)]
        if now is not None and talk_direction(look, now) is not None:
            # a person who has just walked up to someone looks at them before speaking (measured 2026-10-14: an A on the
            # frame the walk ended, the step's last frames still playing, started no conversation with the nurse: "no
            # conversation started within 90 frames", then the second try worked)
            yield from hands.pad.idle(hands.pad.think_frames(), f"walked up to the {now.kind} at {(now.x, now.y)}: "
                                                                f"looking at them before speaking")
            return "reached"
        # (chapter 6) a walk a BATTLE stopped, by the navigator's own battle log (an event, never a word: the old test,
        # '"battle" in outcome', matched the "N battles" of every stuck walk's summary, so ANY spot that could not be
        # reached ended the approach as "battle" and the next spot was never tried: 'interrupted on the way: played out'
        # 28 times in the KI-134 B arm's Story run)
        if outcome.startswith("stuck") and len(nav.battle_log) > battles:
            return "battle"
    return f"unreachable: no tile from which the {seen.kind} at {(seen.x, seen.y)} can be talked to was reached"


def watch_walker(hands: Hands, target: SeenObject, why: str,
                 frames: int = WALKER_WATCH) -> Generator[None, None, tuple[list, set, bool, SeenObject | None]]:
    """(chapter 6) Watch `target` walk, one look a frame, for at most `frames` frames: (the tiles it walked, in order: its
    WAY; every tile anyone ELSE stood on meanwhile; whether it kept one tile `WALKER_STILL` frames, i.e. it is not walking
    round; where it is now, None when out of sight or when something else took the screen). The watch ends early once the
    way comes back round to the tile it began on (a round seen whole), or the person keeps still."""
    way: list[tuple[int, int]] = []
    others: set[tuple[int, int]] = set()
    kept = 0
    now: SeenObject | None = None
    for _ in range(frames):
        look = hands.look()
        if not nav_free(look):
            return way, others, False, None
        now = _same(look, target)
        if now is None:
            return way, others, False, None
        others.update((o.x, o.y) for o in look.view.objects if o.source == "object" and o.local_id != target.local_id)
        tile = (now.x, now.y)
        if way and way[-1] == tile:
            kept += 1
        elif len(way) >= 4 and tile == way[0]:
            return way, others, False, now
        else:
            way.append(tile)
            kept = 1
        if kept >= WALKER_STILL:
            return way, others, True, now
        yield from hands.pad.busy(f"{why}: watching the {target.kind} walk: where does the way go?")
    return way, others, False, now


def waiting_spots(memory, here: tuple[int, int], way: list, others: set) -> list[tuple[tuple[int, int], tuple[int, int], str]]:
    """(chapter 6) Where to wait for someone who walks `way`: (a spot, the tile of the way it looks at, the direction to
    face). A spot is a known walkable tile BESIDE a tile of the way and on no tile anyone was seen on while watching (the
    way itself, the others' ways), so the player blocks nobody; each spot once, nearest to the player first."""
    walked = set(way) | set(others)
    best: dict[tuple[int, int], tuple[tuple[int, int], str]] = {}
    for tile in dict.fromkeys(way):
        for direction, (dx, dy) in DIRECTIONS.items():
            spot = (tile[0] - dx, tile[1] - dy)
            if spot in walked or spot in best or not memory.passable(spot):
                continue
            best[spot] = (tile, direction)
    spots = [(spot, tile, direction) for spot, (tile, direction) in best.items()]
    return sorted(spots, key=lambda s: (abs(s[0][0] - here[0]) + abs(s[0][1] - here[1]), s[0]))


def _out_of_the_way(memory, here: tuple[int, int], since: int) -> tuple[int, int] | None:
    """The nearest known walkable tile, at most `ASIDE_STEPS` steps away over walkable tiles, on which nobody has been seen
    since frame `since` and nobody stands now (`MapMemory.people`: the last frame a person was seen on a tile); None if none."""
    seen_tiles, queue = {here}, deque([(here, 0)])
    while queue:
        tile, steps = queue.popleft()
        if tile != here and memory.people.get(tile, -1) < since and tile not in memory.objects_now:
            return tile
        if steps >= ASIDE_STEPS:
            continue
        for dx, dy in DIRECTIONS.values():
            ahead = (tile[0] + dx, tile[1] + dy)
            if ahead not in seen_tiles and memory.passable(ahead) and ahead not in memory.objects_now:
                seen_tiles.add(ahead)
                queue.append((ahead, steps + 1))
    return None


def meet_walker(hands: Hands, nav: Navigator, target: SeenObject, why: str, budget: int = APPROACH_BUDGET,
                since: int | None = None) -> Generator[None, None, str]:
    """(chapter 6, module constants WALKER_*) Meet someone who walks round the way a person does, from what the screen shows:
    WATCH where they walk (`watch_walker`), stand at the nearest spot BESIDE the way (`waiting_spots`), face the way, and
    wait for them to step onto the tile in front. Returns "reached" on the look that shows them there, the player facing
    them (no pause: a person waiting for someone speaks up as they come past; the caller's `talk` presses A at once);
    "standing" when they turn out to keep still (the caller walks up the ordinary way); "battle" / "scene"; or
    "unreachable: ...". With `since` (the frame the approach began): a player standing where someone has been seen since
    then is IN THEIR WAY (a walker walks in place against it, and the one behind against the walker: no round is watched)
    and first steps aside (`_out_of_the_way`)."""
    look = hands.look()
    found = nav.where(look)
    if since is not None and found is not None and found[0].people.get(found[1], -1) >= since:
        aside = _out_of_the_way(found[0], found[1], since)
        if aside is not None:
            hands.tell(f"talk: {why}: the player stands where people have walked ({found[1]}): it steps aside to {aside} "
                       f"to watch the {target.kind} walk")
            yield from nav.go_to(aside, f"{why}: out of the way of the people walking here, to {aside}", budget)
            look = hands.look()
            if in_battle(look) or not nav_free(look):
                return "battle" if in_battle(look) else "scene"
    way, others, standing, now = yield from watch_walker(hands, target, why)
    look = hands.look()
    if in_battle(look) or not nav_free(look):
        return "battle" if in_battle(look) else "scene"
    if now is None:
        return f"unreachable: the {target.kind} walked out of sight while it watched"
    if standing:
        return "standing"
    found = nav.where(look)
    if found is None:
        return "unreachable: the player's tile is not known"
    memory, here = found
    spots = waiting_spots(memory, here, way, others)
    hands.tell(f"talk: {why}: the {target.kind} (gfx {target.graphics_id}) walks round without stopping (the way seen: "
               f"{way[:14]}): it waits beside the way, facing it, at the nearest of {len(spots)} places "
               f"{[s[0] for s in spots[:WALKER_SPOTS]]}")
    for spot, tile, direction in spots[:WALKER_SPOTS]:
        if here != spot:
            yield from nav.go_to(spot, f"{why}: to wait beside the way the {target.kind} walks, at {spot}", budget)
            look = hands.look()
            if in_battle(look) or not nav_free(look):
                return "battle" if in_battle(look) else "scene"
            found = nav.where(look)
            if found is None or found[1] != spot:
                here = found[1] if found is not None else here
                continue
            here = spot
        result = yield from _wait_for_walker(hands, target, tile, direction, why)
        if result is not None:
            return result
    return (f"unreachable: the {target.kind} who walks round did not step in front of any of "
            f"{min(len(spots), WALKER_SPOTS)} waiting places")


def _wait_for_walker(hands: Hands, target: SeenObject, tile: tuple[int, int], direction: str,
                     why: str) -> Generator[None, None, str | None]:
    """Face `tile` (a tile of the way, `direction` from the player) and wait, a look a frame, for `target` (by its map id)
    to step onto it: "reached" then; None after `WALKER_WAIT` frames or when the player cannot face it; "battle" / "scene"
    when something else takes the screen. Someone else on that tile (PEEKO walks MR. BRINEY's round three steps ahead) is
    let pass: only the person it came for is spoken to."""
    for turns in range(4):
        look = hands.look()
        if in_battle(look) or not nav_free(look):
            return "battle" if in_battle(look) else "scene"
        if look.player.facing == direction:
            break
        if turns == 3:
            return None
        yield from hands.pad.turn(_FACE[direction], why, f"turn {direction} to face {tile}, a tile of the way the "
                                                         f"{target.kind} walks; the player free")
    for _ in range(WALKER_WAIT):
        look = hands.look()
        if in_battle(look) or not nav_free(look):
            return "battle" if in_battle(look) else "scene"
        now = _same(look, target)
        if now is not None and (now.x, now.y) == tile and look.player.facing == direction:
            return "reached"
        yield from hands.pad.busy(f"{why}: waiting beside the way the {target.kind} walks, facing {tile}, for them to "
                                  f"step in front")
    return None


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
    if not nav_free(look):
        # (build step 5.1) a scene began on the last steps of the walk: it is played first, never waited out
        stop = yield from play_out(hands, nav, why)
        return f"interrupted before it could talk: {stop or 'a scene, played out'}"
    seen = _same(look, target)
    if seen is None:
        return f"the {target.kind} is not on screen any more"
    if not (yield from talk(hands, seen, why, give_way=True)):
        if not nav_free(hands.look()):
            # (build step 5.1, the step-5 verifier's FAILURE (b)) a scene began while it turned to talk: its text waits for
            # A, so it is PLAYED (it used to stand 1,200 frames in `talk` waiting for the player to be free)
            stop = yield from play_out(hands, nav, why)
            return f"interrupted before it could talk: {stop or 'a scene, played out'}"
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
    outcome = ""
    for _ in range(2):
        # (build step 5.1, the verifier's second round: seed 42 stood 1,203 frames in front of the nurse while "TREECKO
        # fainted…", the poison's faint on the way in, waited for A) a screen that waits for a press is PLAYED, then the
        # nurse asked again (once)
        outcome = yield from nurse_heal(hands, why, give_way=True)
        if outcome != GAVE_WAY:
            return outcome
        stop = yield from play_out(hands, nav, why)
        if stop is not None:
            return f"interrupted at the nurse: {stop}"
    return outcome


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
        outcome = yield from mart_buy(hands, item, count, f"{why}: {count} x {item}", give_way=True)
        if outcome == GAVE_WAY:
            # (build step 5.1, the verifier's second round) a screen that waits for a press came first: played, then the
            # clerk asked again (once)
            stop = yield from play_out(hands, nav, why)
            if stop is not None:
                out.append(f"{item}: interrupted at the clerk: {stop}")
                break
            outcome = yield from mart_buy(hands, item, count, f"{why}: {count} x {item}", give_way=True)
        out.append(f"{item} x{count}: {outcome}")
        if NOT_FOR_SALE in outcome:
            # (build step 5.1) the list was READ and the item is not on it: the list is still open (`mart_buy` stops
            # there), so it is left the way a person leaves it, and the next item wanted is asked for
            left = yield from leave_shop(hands, nav, why)
            if left != "left":
                out.append(f"after: {left}")
                break
            continue
        if not player_free(hands.look()):
            stop = yield from play_out(hands, nav, why)
            if stop is not None:
                out.append(f"after: {stop}")
                break
    return out


def leave_shop(hands: Hands, nav: Navigator, why: str) -> Generator[None, None, str]:
    """(build step 5.1) Out of a mart's conversation, whatever it shows: the item list left with B (LIST_CANCEL), QUIT in
    the shop menu, the goodbye read on the eyes' waits. Returns "left" or why not. Bounded (`SCENE_ROUNDS` menus, each
    wait `LIST_WAIT` frames)."""
    for _ in range(SCENE_ROUNDS):
        if player_free(hands.look()):
            return "left"
        outcome = yield from advance(hands, player_free, f"{why}: leaving the shop")
        if outcome == "done":
            return "left"
        if outcome == "menu:mart_buy":
            for _ in range(LIST_WAIT):
                ui = hands.look().screen.ui
                if ui is None or ui.kind != "mart_buy" or ui.accepts_input:
                    break
                yield from hands.pad.busy("waiting for the item list to take input")
            ui = hands.look().screen.ui
            if ui is not None and ui.kind == "mart_buy" and ui.accepts_input:
                yield from hands.pad.idle(hands.pad.think_frames(), "nothing on this list it came for: leaving the list")
                yield from hands.pad.press("B", why, "the item list is open: B leaves it (LIST_CANCEL)")
            continue
        if outcome == "menu:mart_menu":
            if not (yield from choose(hands, "mart_menu", "QUIT", f"{why}: the shop menu")):
                return "could not choose QUIT in the shop menu"
            continue
        return f"unexpected while leaving the shop: {outcome}"
    return f"the shop conversation did not end within {SCENE_ROUNDS} menus"


def _person(look: Observation, graphics_id: int) -> SeenObject | None:
    people = [o for o in (look.view.objects if look.view else ()) if o.source == "object" and o.graphics_id == graphics_id]
    return min(people, key=lambda o: (abs(o.dx) + abs(o.dy), o.local_id)) if people else None


def bag_or_its_question(hands: Hands, why: str, budget: int = STARTER_WAIT) -> Generator[None, None, Observation | None]:
    """(build step 5.1, the step-5 verifier's FAILURE (a)) Watch PROF. BIRCH's bag until something on it takes input: the
    bag itself (its cursor), or what the bag ASKS once it took a choice ("Do you choose this POKéMON?": a yes/no of
    `Task_HandleConfirmStarterInput`), or the bag is gone (the scene goes on). Returns that look, or None after `budget`
    frames. (`wait_for_ui(choose_starter)` watched for the bag ALONE: after the A on a ball the bag shows busy while the ball
    opens, so the scene handed it back here, and the yes/no that followed was watched for 600 frames, never pressed: 20 of
    40 sweep runs and the live arm CH1M, A at f34499, YES at f35142.)"""
    for _ in range(budget):
        look = hands.look()
        ui = look.screen.ui
        if ui is not None and ui.accepts_input:
            return look
        if ui is None and look.screen.game_state != "CHOOSE_STARTER":
            return look
        yield from hands.pad.busy("waiting for PROF. BIRCH's bag: a ball opening or its cursor sliding")
    hands.tell(f"{why}: PROF. BIRCH's bag took no input within {budget} frames")
    return None


def choose_starter(hands: Hands, starter: str, why: str) -> Generator[None, None, bool]:
    """PROF. BIRCH's bag: bring the cursor to `starter` by READING it (Left / Right) and press A on its look. True once the
    bag took the choice (the question that follows is the scene's, answered by `answer_question`), and True at once when the
    bag has its choice already and ASKS about it (build step 5.1: `bag_or_its_question`)."""
    if starter not in STARTER_OPTIONS:
        hands.tell(f"{why}: {starter!r} is not in the bag {STARTER_OPTIONS}")
        return False
    target = STARTER_OPTIONS.index(starter)
    look = yield from bag_or_its_question(hands, why)
    if look is None:
        return False
    if look.screen.ui is None or look.screen.ui.kind != "choose_starter":
        what = look.screen.ui.kind if look.screen.ui is not None else "nothing (the bag is gone)"
        hands.tell(f"{why}: the bag has taken its choice: {what} on screen now, the scene's to answer")
        return True
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
