"""RIDES AND TRIPS (chapter 6, 2026-11-06): a person offers to TAKE the player somewhere, and what the AI learns when it goes
along. Framework-free.

WHY (the chapter-6 development probes, ledger #101 and #102, 4 of 6 runs): in DEWFORD, MR. BRINEY asks "Have you
delivered your LETTER? Or were you meaning to sail back to PETALBURG?", and the AI answered YES by the story skill's
default (`skills/story.py` QUESTION_RULES: "a person goes along with what the game asks"), so it sailed away from the
island where its letter was to be delivered (NS1). Back on the mainland it had no way back: the sail's map changes are a
SCENE's (the boat carries the player across the sea while the controls are locked), from tiles that look like no way out,
so `brain/explore.py` route_to, which follows only the links a person can walk, knew no route to DEWFORD or GRANITE CAVE
(NS2: route_to ROUTE104 -> DEWFORD_TOWN was None on probe7 C1's own memory).

A TRIP OFFER (`trip_offer`): a yes/no whose WORDS offer to take the player to a named TOWN or CITY ("sail back to
PETALBURG", "set sail for DEWFORD"): a travelling verb, "to" or "for", and the town's name as people say it
(`knowledge/atlas.py` town_places, static knowledge of the region map). The words are on the screen: fair (USER RULING 40).

A RIDE (`RideWatch`): what the AI SAW when it went along: it answered YES to a trip offer by someone standing in front of
it, the map changed only by scenes (no step or door of its own), and it got the controls back on ANOTHER map. Kept in the
world memory (`WorldMemory.rides`, saved in `world.jsonl`): who (the person's id and figure, and the tile they stood on),
the words answered, the place offered, from which map to which, and where the player stood when the controls came back.
`brain/explore.py` route_to and region_hops, and `brain/goals.py` world_distance, use a ride as a LINK (walk up to the
person, talk, answer YES); `brain/navigator.py` takes it through the play brain's `rider` (`brain/goals.py`
GoalRunner.ride). A ride whose person was not there, or who asked something else, is put aside until there is news
(`WorldMemory.close_ride`), as a door found closed is.

WHAT IS NOT A RIDE: a map change after a NO, after a question that offers no trip, after a talk with no question, a scene
the AI did not say YES to (a whiteout's warp to a POKéMON CENTER, a fall through a cracked floor, PROF. BIRCH carrying
the player to his lab), anything with a battle in it, and a scene that ends on the map it began on. The scene's
brief free moments are not its end (the first sail warps to ROUTE 104's dock and frees the player for two frames before
the boat's script locks the controls again, probe8 C1 f755049-f755051): the controls are back only when the AI acts on
its own (a press while free) or `RIDE_SETTLE` free frames have passed.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from ai_player.eyes.observation import Observation, SeenObject
from ai_player.eyes.screens import page_text
from ai_player.hands.dialogue import player_free
from ai_player.knowledge.atlas import town_places
from ai_player.skills.flee import in_battle

__all__ = [
    "RIDE_MAX_FRAMES",
    "RIDE_SETTLE",
    "SPEAKER_REACH",
    "RideWatch",
    "folded",
    "speaker_of",
    "trip_offer",
]

#: Frames the controls must stay with the player, with no press, before a ride is taken to have ended there (when the AI
#: does not act first): the first sail freed the player on ROUTE 104's dock for 2 frames between two scenes (probe8 C1).
RIDE_SETTLE = 120
#: A pending ride not over after this many frames is dropped (the first sail, DAD's call included: 5,350 frames).
RIDE_MAX_FRAMES = 20_000
#: How far in front of the player the one who asks may stand (a counter between: the nurse, the clerk).
SPEAKER_REACH = 2
_FACING = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
#: a travelling verb, "back" or not, then "to" or "for" (and "the"): what an offer to take someone somewhere says
_TRAVEL = r"\b(?:sail|sailing|set sail|go|going|head|heading|take you|travel|fly|flying|ride)(?:\s+back)?\s+(?:to|for)\s+(?:the\s+)?"


def folded(text: str | None) -> str:
    """A page's words as compared: lower case, whitespace folded, the game's curly apostrophe made plain."""
    return " ".join((page_text(text) or "").replace("’", "'").lower().split())


def trip_offer(words: str | None) -> str | None:
    """The TOWN or CITY (its map const) that the words `words` offer to take the player to, or None: a travelling verb,
    "to"/"for", then the place's name as people say it, as WHOLE words (`town_places`). Two places named: the first."""
    text = " ".join((words or "").replace("’", "'").lower().split())
    found: list[tuple[int, str]] = []
    for name, const in town_places().items():
        match = re.search(_TRAVEL + re.escape(name.lower()) + r"\b", text)
        if match is not None:
            found.append((match.start(), const))
    return min(found)[1] if found else None


def speaker_of(look: Observation) -> SeenObject | None:
    """The person straight in front of the player, at most `SPEAKER_REACH` tiles away (the one who asks a question while
    the player faces them: a script's `faceplayer` turns them to the player, the player faces them to talk), or None."""
    player, view = look.player, look.view
    if player is None or view is None:
        return None
    ahead = _FACING.get(player.facing or "")
    if ahead is None:
        return None
    for reach in range(1, SPEAKER_REACH + 1):
        for seen in view.objects:
            if seen.source == "object" and seen.kind == "npc" and (seen.dx, seen.dy) == (ahead[0] * reach, ahead[1] * reach):
                return seen
    return None


class RideWatch:
    """A hands watcher (`Hands.watchers`, after the world memory's own): told by the travel answer when the AI says YES to
    a trip offer (`offered`), it watches what follows on every look and records a RIDE in the world memory when the
    module docstring's conditions hold (`WorldMemory.record_ride`); `presses()` is the pad's press count, `tell(line,
    extra)` the navigator's line."""

    def __init__(self, world, presses: Callable[[], int], tell: Callable[..., None]) -> None:
        self.world = world
        self._presses = presses
        self._tell = tell
        #: the ride under way: what was answered, by whom, from where, and the free stretch it may end in
        self.pending: dict | None = None
        #: (for the tests and the log) every ride recorded or dropped by this watch: (frame, "recorded"/"dropped", why)
        self.history: list[tuple[int, str, str]] = []

    def offered(self, look: Observation, place: str, words: str) -> None:
        """The AI answered YES to `words`, an offer of a trip to `place` (a map const), on the look `look`."""
        speaker = speaker_of(look)
        key = self.world.current
        if speaker is None or key is None:
            self.history.append((look.frame, "dropped", "no one stands in front of the player, or no map: no ride"))
            return
        self.pending = {"from": key, "who": speaker.local_id, "gfx": speaker.graphics_id, "tile": [speaker.x, speaker.y],
                        "words": words, "place": place, "frame": look.frame, "changes": len(self.world.transitions),
                        "free": None}

    def _drop(self, frame: int, why: str) -> None:
        self.history.append((frame, "dropped", why))
        self._tell(f"no ride recorded: {why}", {"ride_dropped": why})
        self.pending = None

    def __call__(self, look: Observation) -> None:
        ride = self.pending
        if ride is None:
            return
        if look.frame - ride["frame"] > RIDE_MAX_FRAMES:
            self._drop(look.frame, f"the scene after the YES did not end within {RIDE_MAX_FRAMES} frames")
            return
        if in_battle(look):
            self._drop(look.frame, "a battle came after the YES: a ride has none")
            return
        changes = self.world.transitions[ride["changes"]:]
        if any(change.by != "scene" for change in changes):
            # the AI moved the player itself before the controls were taken to be back: the map it left is where it ended
            self._close(look, changes, own=True)
            return
        free = (player_free(look) and not look.screen.fading and look.view is not None and look.player is not None
                and look.player.x is not None)
        if not free:
            ride["free"] = None  # a free moment between two scenes (the first sail's dock) is no end
            return
        stretch = ride["free"]
        if stretch is None:
            ride["free"] = {"map": self.world.current, "at": [look.player.x, look.player.y], "frame": look.frame,
                            "presses": self._presses()}
            return
        if self._presses() != stretch["presses"] or look.frame - stretch["frame"] >= RIDE_SETTLE:
            self._close(look, changes, own=False)

    def _close(self, look: Observation, changes: list, own: bool) -> None:
        ride = self.pending
        stretch = ride["free"]
        if own:
            first_own = next(index for index, change in enumerate(changes) if change.by != "scene")
            scene = changes[:first_own]
            end = changes[first_own].source
            at = list(changes[first_own].tile) if changes[first_own].tile else None
        else:
            scene = changes
            end = stretch["map"] if stretch is not None else self.world.current
            at = stretch["at"] if stretch is not None else None
        if not scene:
            self._drop(look.frame, "no map change came after the YES (a scene that ends where it began)")
            return
        if end == ride["from"] or at is None:
            self._drop(look.frame, "the controls came back on the map the question was asked on")
            return
        record = {"from": ride["from"], "to": end, "arrival": at, "who": ride["who"], "gfx": ride["gfx"],
                  "tile": ride["tile"], "words": ride["words"], "place": ride["place"],
                  "via": [change.target for change in scene[:-1]], "frame": look.frame}
        kept = self.world.record_ride(record)
        names = self.world.names()
        self.history.append((look.frame, "recorded", f"{ride['from']} -> {end}"))
        self._tell(f"RIDE: answering YES to {ride['words'][:70]!r} (person {ride['who']} at {tuple(ride['tile'])} on "
                   f"{names.get(ride['from'], ride['from'])}) carried the player to {names.get(end, end)} {tuple(at)} by "
                   f"scenes only ({len(scene)} map change(s)): kept as a way there ({kept.get('uses')} time(s))",
                   {"ride": {key: value for key, value in kept.items() if key != "closed"}})
        self.pending = None
