"""R2: THE AI'S MEMORY OF ONE GAME, `memory.jsonl` (build spec 2026-10-29 section 3 (c); D4-D7, D9, D15, D16; backlog R2,
DP2 and L3 (a)-(b)). Framework-free, play-loop side.

WHY A FILE OF ITS OWN: a person who switches the game off and on again continues from their SAVE and remembers what they
had done UP TO THAT SAVE. Before R2 only the world memory crossed processes, as the LAST line of a `world.jsonl`
(`world/memory.py` read_world), which after a kill is NEWER than the save the game loads: the AI would "remember" maps
it never reached in the game it is now playing. So the AI writes one line per save, at the START of the save's flash
write (D5: the first look that shows the whole "SAVING... DON'T TURN OFF THE POWER." page), stamped with the game's PLAY
TIME in hours and minutes, the value the game writes into the save and shows again on the CONTINUE window (D4). A
continue reads that TIME, finds the save line it belongs to (`MemoryBook.match_time`: the NEWEST line within
`MATCH_MINUTES`, then verified on arrival by the caller) and restores the memory AS OF THAT SAVE (`restore`), never
newer. The measured silent window (a second save cut in its first sector loads the first save with NO error page, probe
report FR2/FR5) is why the TIME, and not the error page, decides.

THE FILE (schema 1, `SCHEMA_VERSION`; one JSON object per line, append-only, never rewritten):
    header   {"kind", "schema_version", "game", "identity"}: written with the FIRST save line (no save, no file)
    session  {"kind", "n", "started", "how", "host", "run_dir", "cart", "frame_base", "continued_from", "page",
              "verified", "restored_maps", "losses"}: at a session's first save, a continue's restore, or a STOP; (U2 spec
              D13) a continue's line also `dropped` {"frames" (None: not recorded), "lost"}: what it told it drops
    save     {"kind", "id", "parent", "full", "play_time", "frame", "where", "party", "why", "memory"}
    saved    {"kind", "id", "frame"}: the SAVED page was read (nothing depends on it)
    lost     {"kind", "frame", "play_time", "where", "after_save"}: a battle lost (D12 (e))
    end      {"kind", "session", "reason", "chosen", "budget", "at_save", "frame", "stopped_before_restore", "play_time",
              "where"} (the last two since U2, D13: the last look's, for the launcher's drop sentence)
    torn    {"kind", "length"}: written by the next session before its first line, when the file ended in a line a kill
             cut short; it names that line's length, so the line it acknowledges is skipped and no OTHER broken line is
CODE OVER SPEC (the builder's notes, said where): the spec's codec tags are `__set__` / `__tuple__` / `__dict__`; a
string whose whole value is a dunder identifier is refused in the play loop (`gates/check_purity.py` rule d), so the tags
are `$set` / `$tuple` / `$dict`. The spec's `torn` line is new: the spec ignores a torn LAST line, but the next append
would then join it on one line, turning it into a torn MIDDLE line that refuses the whole file; the writer therefore ends
the cut line and acknowledges it first. The spec's delta paths are "at most two keys" with the example
`["world", "maps", "<map key>"]`: the code follows the example (a section, then two keys: `DELTA_DEPTH` 3), or every
save would rewrite every map.

A SAVE'S `memory` is a FULL payload (`build_payload`: the world memory, the goal manager's KEEP fields, the personality,
the battle mind's wishes and meetings, the Pokemon registry, the loss count) when the save has no parent or `FULL_EVERY`
deltas already follow the last full line of its chain; otherwise a DELTA against its PARENT's rebuilt payload
(`{"set": [[path, value], ...], "del": [path, ...]}`). After a continue from save k the next save's parent is k, so the
lines of an abandoned branch are never on a chain again. A torn last line is ignored (and told); any other unreadable or
non-ASCII line (every line is written with `ensure_ascii=True`, so one means a corrupted byte) refuses the file; a NEWER schema is refused with the file left byte-identical (D9).

WHAT A CONTINUE RESTORES (D16, `GOAL_KEEP` / `GOAL_RESET` / `GOAL_IN_WORLD`): what a person would REMEMBER at the save
(whom it talked to, the items it tried, the places it looked round, its fight preparation, ...) is kept; a process's
loop guards, clocks and reports start afresh. Every field of the goal manager's memory must be in one of the three
tables: an unclassified field makes `goals_part` raise, so a new field cannot be silently dropped or silently kept.

L3 (a)-(b), `MonRegistry`: every Pokemon of the player's by its PID (hex), with its species (and every species seen for
that PID: evolution keeps the PID), where and when it was first seen in the party, how it came, and `roles` (vocabulary
`ROLES`; none is assigned in this build).

FRAMES (D7): in a continue run the brain's frames are the emulator's plus `MemoryBook.frame_base()`, 1 + the largest
frame stamp in the file, so every carried stamp stays in the past after a cold boot (the emulator's counter starts at 0).
(U2 spec 2026-10-30 1.4, corrected) The stamps are NOT monotonic across sessions in every case: only `save`, `saved`,
`lost` and `end` lines carry a frame, and a session ended by the soft wall clock or a hard kill writes no `end` line, so
its last stamp can be its save's own and the next session's base lands inside the frames it played. A count of the
frames a continue drops is therefore built PER SESSION from that session's own `end` line (`MemoryBook.dropped_after`;
"not recorded" without one), and the launcher adds the HOST's own count (`host/launcher.py` memory_check).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from ai_player.personality import DRIFT_EVERY
from ai_player.runlog import RecordFile

__all__ = [
    "BATTLE_FIELDS",
    "CARTS",
    "DELTA_DEPTH",
    "FULL_EVERY",
    "GOAL_IN_WORLD",
    "GOAL_KEEP",
    "GOAL_RESET",
    "HOSTS",
    "LINE_KINDS",
    "MATCH_MINUTES",
    "MEMORY_FILE_NAME",
    "MON_HOW",
    "PERSONALITY_FIELDS",
    "R1_NEW_FIELDS",
    "ROLES",
    "SCHEMA_VERSION",
    "SESSION_HOW",
    "TAGS",
    "MemoryBook",
    "MemoryFileError",
    "MemoryWriter",
    "MonRegistry",
    "Restored",
    "SaveWrite",
    "apply_delta",
    "battle_part",
    "build_payload",
    "decode_value",
    "diff",
    "encode_value",
    "end_line",
    "goals_part",
    "minutes_apart",
    "party_of",
    "personality_part",
    "pid_hex",
    "read_book",
    "restore",
    "restore_battle",
    "restore_goals",
    "restore_personality",
    "where_of",
]

MEMORY_FILE_NAME = "memory.jsonl"
SCHEMA_VERSION = 1
#: A full payload at least every this many saves along a chain (the rest are deltas).
FULL_EVERY = 8
#: A save line matches the CONTINUE window's TIME when its stamp is at most this many minutes away (D4, T1: the stamp's
#: look can come one frame before the write freezes the clock, so the written minute can be one later).
MATCH_MINUTES = 1
#: A delta's paths go at most this deep: a payload section, then two keys (`["world", "maps", "<map key>"]`).
DELTA_DEPTH = 3
LINE_KINDS = ("header", "session", "save", "saved", "lost", "end", "torn")
SESSION_HOW = ("new game", "continue")
HOSTS = ("launcher", "harness")
#: D17: what the cart held when the run began (`empty`: --fresh or --state emptied it; `continued`; `kept`: no flag).
CARTS = ("empty", "continued", "kept")
#: D15: the roles a Pokemon may be given (assigned by L3 (c)-(d), not this build).
ROLES = ("lead", "hm_carrier", "counter", "catch_helper", "spare")
MON_HOW = ("starter", "caught", "joined")
#: The codec's tags (a JSON object with exactly one of these keys is a tagged value, never a plain dict).
TAG_SET, TAG_TUPLE, TAG_DICT = "$set", "$tuple", "$dict"
TAGS = (TAG_SET, TAG_TUPLE, TAG_DICT)

#: D16, THE RESTORE TABLE of the goal manager's memory (`brain/goals.py` _Memory). KEEP: what a person remembers at the
#: save (restored as of the save).
GOAL_KEEP: dict[str, str] = {
    "talked": "the people it talked to",
    "tried_items": "the item balls it tried and is done with",
    "item_tries": "the walks to an item ball it began",
    "catch_maps": "the maps where it made its catch draw",
    "chat_drawn": "the people whose chat draw it made",
    "asked_rounds": "how often it asked a map's people round, per milestone",
    "fight_prep": "its training for each fight so far",
    "sightings": "where it last saw someone it recognises",
    "pages": "the pages it has read",
    "looked": "the maps it looked round",
    "detoured": "the detour draws it made",
    "seen_levels": "how strong the trainers of a route were",
    "last_map": "the outdoor map it last stood on",
    "no_balls": "the marts whose list showed no POKé BALLS",
    "home_heals": "the times MOM healed the party",
    "scene_walls": "the tiles a scene sent it back from",
    "again": "the looks round 'some more' it made",
    "break_stops": "the walks whose boredom draw it made",
    "exhausted": "the places whose look round brought nothing new",
    "blocked": "the places curiosity could not get to",
    "center_looked": "the towns whose POKéMON CENTER it looked for",
    "explored": "the maps it looked round",
    "saved_for": "the gym approaches it saved before (R1)",
    "last_save": "its last save (R1: the 3-minute gap)",
}
#: RESET: a process's loop guards, clocks and reports (a fresh session starts them afresh).
GOAL_RESET: dict[str, str] = {
    "fails": "failures in a row: a loop guard of this process",
    "cooldown": "decision numbers of this process",
    "decisions": "this process's decision count",
    "known_before": "recomputed at the session's first decision",
    "aside_from": "frames of this process's asides",
    "passed_new": "a count of this process's walk",
    "spent": "this session's goal frames: a report",
    "curious_since": "the boredom clock: starts at the session's first decision",
    "curious_row": "curiosity goals in a row: a loop guard",
    "idle": "a report of this session",
    "decided_with_party": "the last goal's own flag",
    "danger_again": "retries in a row: a loop guard",
    "hearing": "the goal being pursued (none at a restore)",
    "lost_end": "a stamp of this process's navigator",
    "save_due": "a due save expires with the process (R1)",
}
#: Fields the play brain links to the WORLD memory (`mode.py` _play: `manager.memory.landmarks = world.landmarks`), which
#: carries them in its own payload section.
GOAL_IN_WORLD: dict[str, str] = {
    "landmarks": "the doors it recognised: `WorldMemory.landmarks`",
    "spoke": "the people who spoke to it: `WorldMemory.spoke`",
}
#: The goal manager's fields that R1's policy adds (build stage 4, `brain/saving.py`): classified above before they exist.
R1_NEW_FIELDS = ("saved_for", "last_save", "save_due")
#: What a continue keeps of the personality (`personality.py` PersonalityState) and the battle mind (`brain/battle.py`).
PERSONALITY_FIELDS = ("base", "favourite", "history", "draws")
BATTLE_FIELDS = ("wishes", "met", "wild_met")


class MemoryFileError(ValueError):
    """The memory file cannot be used. `kind`: "newer" (a newer program wrote it: refused, left byte-identical),
    "no_header", "unreadable" (a line other than a torn last line), "chain" (a save's parent chain is broken),
    "unclassified" (a goal-memory field in no restore table), "codec", "state" (the writer was used out of order)."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


# ------------------------------------------------------------------ the codec (sets, tuples, non-string keys)
def _order(item) -> str:
    return json.dumps(item, sort_keys=True, ensure_ascii=True)


def encode_value(value):
    """`value` as plain JSON: a set is `{"$set": [...]}` (sorted, so equal sets write equal text), a tuple
    `{"$tuple": [...]}`, a dict with a non-string key (or a key that is a tag) `{"$dict": [[key, value], ...]}`."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (set, frozenset)):
        return {TAG_SET: sorted((encode_value(item) for item in value), key=_order)}
    if isinstance(value, tuple):
        return {TAG_TUPLE: [encode_value(item) for item in value]}
    if isinstance(value, list):
        return [encode_value(item) for item in value]
    if isinstance(value, dict):
        if all(isinstance(key, str) and key not in TAGS for key in value):
            return {key: encode_value(item) for key, item in value.items()}
        return {TAG_DICT: [[encode_value(key), encode_value(item)] for key, item in value.items()]}
    raise MemoryFileError("codec", f"the memory cannot write a {type(value).__name__}")


def decode_value(value):
    """The inverse of `encode_value`."""
    if isinstance(value, list):
        return [decode_value(item) for item in value]
    if isinstance(value, dict):
        if len(value) == 1:
            key = next(iter(value))
            inner = value[key]
            if key == TAG_SET:
                return {decode_value(item) for item in inner}
            if key == TAG_TUPLE:
                return tuple(decode_value(item) for item in inner)
            if key == TAG_DICT:
                return {decode_value(pair[0]): decode_value(pair[1]) for pair in inner}
        return {key: decode_value(item) for key, item in value.items()}
    return value


def _copy(value):
    """A deep copy of plain JSON."""
    return json.loads(json.dumps(value, ensure_ascii=True))


# ------------------------------------------------------------------ deltas
def _branch(value) -> bool:
    """A plain JSON object a delta may go into (a tagged value is a leaf)."""
    return isinstance(value, dict) and not (len(value) == 1 and next(iter(value)) in TAGS)


def _same(a, b) -> bool:
    """Equal as JSON text (`1 == True` in Python is not the same value in the file)."""
    return _order(a) == _order(b)


def diff(parent: dict, child: dict, depth: int = DELTA_DEPTH) -> dict:
    """The delta that turns `parent` into `child` (both plain JSON payloads): keys gone are `del` paths, keys new or
    changed are `set` paths with their whole value; a changed object is gone into while the path is shorter than
    `depth`."""
    sets: list = []
    dels: list = []

    def walk(old: dict, new: dict, path: list) -> None:
        for key in old:
            if key not in new:
                dels.append(path + [key])
        for key, value in new.items():
            if key not in old:
                sets.append([path + [key], _copy(value)])
            elif not _same(old[key], value):
                if len(path) + 1 < depth and _branch(old[key]) and _branch(value):
                    walk(old[key], value, path + [key])
                else:
                    sets.append([path + [key], _copy(value)])

    walk(parent, child, [])
    return {"set": sets, "del": dels}


def _container(payload: dict, path: list, what: str) -> dict:
    node = payload
    for key in path[:-1]:
        node = node.get(key) if isinstance(node, dict) else None
        if not isinstance(node, dict):
            raise MemoryFileError("chain", f"a delta {what} {path} goes through a value that is not an object")
    return node


def apply_delta(parent: dict, delta: dict) -> dict:
    """`parent` with `delta` applied (a new payload; `parent` is not changed). Every deletion must find its key."""
    if not isinstance(delta, dict) or not isinstance(delta.get("set"), list) or not isinstance(delta.get("del"), list):
        raise MemoryFileError("chain", "a delta must be {'set': [...], 'del': [...]}")
    out = _copy(parent)
    for path in delta["del"]:
        if not isinstance(path, list) or not path or len(path) > DELTA_DEPTH:
            raise MemoryFileError("chain", f"a delta deletes at {path!r}: not a path of 1 to {DELTA_DEPTH} keys")
        node = _container(out, path, "deletes at")
        if path[-1] not in node:
            raise MemoryFileError("chain", f"a delta deletes {path}, which its parent does not hold")
        del node[path[-1]]
    for item in delta["set"]:
        if not isinstance(item, list) or len(item) != 2 or not isinstance(item[0], list) or not item[0] \
                or len(item[0]) > DELTA_DEPTH:
            raise MemoryFileError("chain", f"a delta sets {item!r}: not [path, value]")
        node = _container(out, item[0], "sets at")
        node[item[0][-1]] = _copy(item[1])
    return out


# ------------------------------------------------------------------ what a look says about the party and the place
def pid_hex(pid: int) -> str:
    return f"{pid & 0xFFFFFFFF:08x}"


def where_of(look) -> dict:
    """Where the player stands, as a save line, a `lost` line and the registry record it: `{"map", "tile"}` only (D15:
    never `x`, `y` or `state`)."""
    player = look.player
    if player is None:
        return {"map": None, "tile": None}
    tile = [player.x, player.y] if player.x is not None and player.y is not None else None
    return {"map": player.map_const, "tile": tile}


def party_of(look) -> list[dict]:
    """The party by IDENTITY, in its order: `[{"pid": hex, "species"}]` (CLAUDE.md rule 3)."""
    return [{"pid": pid_hex(mon.pid), "species": mon.species} for mon in look.party or ()]


def _stamp_of(look) -> list[int] | None:
    """A look's play time as a line stamps it, `[hours, minutes]`, or None when it was not read (named apart from the
    eyes' `host/eyes.py` _play_time: the call-site census matches functions by name)."""
    progress = look.progress
    play_time = progress.play_time if progress is not None else None
    return None if play_time is None else [int(play_time[0]), int(play_time[1])]


def minutes_apart(a, b) -> int:
    """|a - b| in minutes for two (hours, minutes) play times."""
    return abs((int(a[0]) * 60 + int(a[1])) - (int(b[0]) * 60 + int(b[1])))


# ------------------------------------------------------------------ L3 (a)-(b): the Pokemon registry
class MonRegistry:
    """Every Pokemon of the player's by PID (hex): `{"species", "species_seen", "first": {"map", "tile"}, "frame",
    "play_time", "how", "roles"}`. Filled from every look with a party (`observe`, a hands watcher the brain adds);
    eggs are not registered (an egg's species is not its own yet); a Pokemon seen only in a PC box is not either
    (`StoredMon` has no species)."""

    def __init__(self, entries: dict | None = None) -> None:
        self.entries: dict[str, dict] = {}
        for key, entry in (entries or {}).items():
            for role in entry.get("roles") or []:
                self._check_role(role)
            self.entries[str(key)] = _copy(entry)

    @staticmethod
    def _check_role(role) -> None:
        if not isinstance(role, dict) or set(role) != {"role", "for", "until"} or role.get("role") not in ROLES:
            raise MemoryFileError("unreadable", f"a role must be {{'role': one of {ROLES}, 'for', 'until'}}, not {role!r}")

    def observe(self, look, caught: bool = False) -> list[str]:
        """Register every Pokemon of `look`'s party not registered yet (`caught`: the battle log's last outcome is a
        catch, as the brain tells it); a registered PID whose species changed evolved. Returns the new PIDs."""
        new: list[str] = []
        for mon in look.party or ():
            if mon.is_egg:
                continue
            key = pid_hex(mon.pid)
            entry = self.entries.get(key)
            if entry is None:
                how = "starter" if not self.entries else ("caught" if caught else "joined")
                self.entries[key] = {"species": mon.species, "species_seen": [mon.species], "first": where_of(look),
                                     "frame": int(look.frame), "play_time": _stamp_of(look), "how": how, "roles": []}
                new.append(key)
            elif entry["species"] != mon.species:
                entry["species"] = mon.species
                if mon.species not in entry["species_seen"]:
                    entry["species_seen"].append(mon.species)
        return new

    def add_role(self, pid: int, role: str, boss: str | None = None, until: str | None = None) -> None:
        """Give a registered Pokemon a role (`ROLES`; L3 (c)-(d) assigns them). An unknown role is refused."""
        record = {"role": role, "for": boss, "until": until}
        self._check_role(record)
        key = pid_hex(pid)
        if key not in self.entries:
            raise MemoryFileError("state", f"no Pokemon with PID {key} is registered")
        self.entries[key]["roles"].append(record)

    def to_dict(self) -> dict:
        return _copy(self.entries)


# ------------------------------------------------------------------ the payload and the restore table
def goals_part(memory) -> dict:
    """The goal manager's KEEP fields, encoded. A field in no restore table RAISES (D16: never silently dropped)."""
    values = asdict(memory)
    unclassified = sorted(name for name in values if name not in GOAL_KEEP and name not in GOAL_RESET
                          and name not in GOAL_IN_WORLD)
    if unclassified:
        raise MemoryFileError("unclassified", f"goal-memory fields in no restore table (game_memory.py GOAL_KEEP / "
                                              f"GOAL_RESET / GOAL_IN_WORLD): {', '.join(unclassified)}")
    return {name: encode_value(values[name]) for name in sorted(GOAL_KEEP) if name in values}


def restore_goals(fresh, part: dict):
    """A goal-manager memory: `fresh` (a new one, every RESET field at its start) with every KEEP field of `part`. The
    WORLD fields are left for the brain to link to the restored world memory, as it does in every run."""
    names = set(asdict(fresh))
    kept = {name: decode_value(value) for name, value in part.items() if name in GOAL_KEEP and name in names}
    return replace(fresh, **kept)


def personality_part(state) -> dict:
    return {"base": state.base, "favourite": state.favourite, "history": _copy(state.history), "draws": int(state.draws)}


def restore_personality(state, part: dict) -> None:
    """Keep the base, the favourite, the history and the draws; the drift starts afresh (it counts the navigator's
    per-process steps): active = base, no drift under way, the next draw at `DRIFT_EVERY`."""
    if part.get("base") != state.base:
        raise MemoryFileError("state", f"the save's personality is {part.get('base')!r}, the run's {state.base!r}")
    state.favourite = part.get("favourite")
    state.history = _copy(part.get("history") or [])
    state.draws = int(part.get("draws") or 0)
    state.active = state.base
    state.drift_until = None
    state.next_draw = DRIFT_EVERY


def battle_part(mind) -> dict:
    return {"wishes": dict(mind.wishes), "met": dict(mind.met), "wild_met": int(mind.wild_met)}


def restore_battle(mind, part: dict) -> None:
    mind.wishes = {str(key): bool(value) for key, value in (part.get("wishes") or {}).items()}
    mind.met = {str(key): int(value) for key, value in (part.get("met") or {}).items()}
    mind.wild_met = int(part.get("wild_met") or 0)


def build_payload(*, world: dict, goals: dict, personality: dict, battle: dict, mons: dict, losses: int) -> dict:
    """A save's memory (plain JSON): `world` = `WorldMemory.to_dict()`, `goals` = `goals_part`, `personality` =
    `personality_part`, `battle` = `battle_part`, `mons` = `MonRegistry.to_dict()`, `losses` = the run's lost battles."""
    return _copy({"world": encode_value(world), "goals": goals, "personality": encode_value(personality), "battle": encode_value(battle),
                  "mons": mons, "losses": int(losses)})


@dataclass(frozen=True)
class Restored:
    """A save's memory, rebuilt and decoded (`restore`)."""

    save: dict  # the save line (its payload left out)
    payload: dict  # the rebuilt payload, plain JSON
    world: dict  # for `WorldMemory.from_dict`
    goals: dict  # for `restore_goals`
    personality: dict
    battle: dict
    mons: MonRegistry
    losses: int

    @property
    def restored_maps(self) -> list[str]:
        """The map keys of the restored world memory (the session line's `restored_maps`)."""
        return sorted((self.world.get("maps") or {}).keys())


def restore(book: "MemoryBook", save_id: int) -> Restored:
    """The memory AS OF save `save_id`: its chain rebuilt from the last full line (`MemoryBook.rebuild`)."""
    payload = book.rebuild(save_id)
    line = {key: value for key, value in book.save(save_id).items() if key != "memory"}
    return Restored(save=line, payload=payload, world=decode_value(payload.get("world") or {}),
                    goals=dict(payload.get("goals") or {}), personality=decode_value(payload.get("personality") or {}),
                    battle=decode_value(payload.get("battle") or {}), mons=MonRegistry(payload.get("mons") or {}),
                    losses=int(payload.get("losses") or 0))


def end_line(session: int, reason: str, at_save: bool, frame: int, stopped_before_restore: bool = False,
             look=None) -> dict:
    """The `end` line (D12 (a)): `chosen` = the AI ended the run (`done:` or `stuck:`), `budget` = the frame budget
    ended it (`stopped:`), `at_save` = the last thing the run did was a successful save. `reason` is the play brain's
    outcome, with or without the `play: ` its end line puts in front.
    (R1 fix round, review R-2) `stopped_before_restore`: a CONTINUE that stopped on a bound or a failed read
    (`ContinueResult.may_retry`) before it restored or played anything. Such an end is NOT chosen: it changed nothing a
    later continue could undo, and the launcher looks through it to the session before (`host/launcher.py`
    judge_end). The spec's own stops (the save gone, a TIME it does not remember, an arrival that differs) stay
    chosen.
    (U2 spec 2026-10-30 D13) `play_time` and `where` of the run's LAST look (`look`; None without one): written for the
    launcher's drop sentence (`host/launcher.py` memory_check), which says from which play time to which a continue
    drops; the AI never reads them back (D19: a continued game's memory is its save's). A line without them (schema 1,
    written before U2) still reads."""
    text = reason[len("play: "):] if reason.startswith("play: ") else reason
    held = bool(stopped_before_restore) and text.startswith("stuck:")
    line = {"kind": "end", "session": int(session), "reason": reason,
            "chosen": text.startswith(("done:", "stuck:")) and not held, "budget": text.startswith("stopped:"),
            "at_save": bool(at_save), "frame": int(frame), "stopped_before_restore": held}
    line["play_time"] = _stamp_of(look) if look is not None else None
    line["where"] = where_of(look) if look is not None else None
    return line


# ------------------------------------------------------------------ reading
_SAVE_KEYS = ("id", "parent", "full", "play_time", "frame", "where", "party", "why", "memory")


def _check_line(line, number: int) -> None:
    if not isinstance(line, dict) or line.get("kind") not in LINE_KINDS:
        raise MemoryFileError("unreadable", f"line {number} is not a memory line of schema {SCHEMA_VERSION}")
    kind = line["kind"]
    if kind == "save":
        missing = [key for key in _SAVE_KEYS if key not in line]
        play_time = line.get("play_time")
        if missing or not isinstance(line.get("id"), int) or not isinstance(line.get("full"), bool) \
                or not (isinstance(play_time, list) and len(play_time) == 2) or not isinstance(line.get("frame"), int):
            raise MemoryFileError("unreadable", f"line {number}: a save line without {missing or 'a valid id, full, '
                                                                                           'play_time or frame'}")
        if not line["full"] and not isinstance(line.get("parent"), int):
            raise MemoryFileError("unreadable", f"line {number}: a delta save line names no parent")
    elif kind == "session":
        if line.get("how") not in SESSION_HOW or not isinstance(line.get("n"), int):
            raise MemoryFileError("unreadable", f"line {number}: a session line without a valid n and how")
    elif kind == "end":
        if not isinstance(line.get("session"), int) or not isinstance(line.get("at_save"), bool):
            raise MemoryFileError("unreadable", f"line {number}: an end line without its session and at_save")
    elif kind == "torn":
        if not isinstance(line.get("length"), int):
            raise MemoryFileError("unreadable", f"line {number}: a torn line without the length of the line it ends")


@dataclass
class MemoryBook:
    """A memory file as read (`read_book`): its lines in file order. `torn`: a last line a kill cut short (ignored,
    told), or None; `ends_clean`: the file ends with a newline (else the writer ends the last line before appending)."""

    path: Path
    lines: list
    torn: str | None = None
    ends_clean: bool = True
    #: the cut lines acknowledged by a `torn` line (ignored)
    acknowledged: int = 0

    @property
    def header_line(self) -> dict:
        return self.lines[0]

    def saves(self) -> list[dict]:
        return [line for line in self.lines if line["kind"] == "save"]

    def save(self, save_id: int) -> dict:
        for line in self.lines:
            if line["kind"] == "save" and line["id"] == save_id:
                return line
        raise MemoryFileError("chain", f"no save line with id {save_id}")

    def newest_save(self) -> dict | None:
        saves = self.saves()
        return saves[-1] if saves else None

    def next_save_id(self) -> int:
        return 1 + max((line["id"] for line in self.saves()), default=0)

    def sessions(self) -> list[dict]:
        return [line for line in self.lines if line["kind"] == "session"]

    def last_session(self) -> dict | None:
        sessions = self.sessions()
        return sessions[-1] if sessions else None

    def end_of(self, session: int) -> dict | None:
        """The `end` line of session `session` (None: it ended without one: killed, or an exception)."""
        ends = [line for line in self.lines if line["kind"] == "end" and line["session"] == session]
        return ends[-1] if ends else None

    def match_time(self, time) -> dict | None:
        """The save the CONTINUE window's TIME `(hours, minutes)` belongs to: the NEWEST save line (by file order) whose
        stamp is within `MATCH_MINUTES` of it, or None (D4: an abandoned branch's line is always older in the file)."""
        for line in reversed(self.saves()):
            if minutes_apart(line["play_time"], time) <= MATCH_MINUTES:
                return line
        return None

    def chain(self, save_id: int) -> list[dict]:
        """Save `save_id` and its ancestors back to (and with) its full line, newest first."""
        out: list[dict] = []
        line = self.save(save_id)
        # (build stage 4) the walk is a bounded `for` (a chain is at most every save line long): the refusal below is
        # its only way out without a full line, so deleting it can never turn a looping chain into a hang
        for _ in range(len(self.saves()) + 1):
            out.append(line)
            if line["full"]:
                return out
            line = self.save(line["parent"])
        raise MemoryFileError("chain", f"save {save_id}'s parents loop")

    def deltas_since_full(self, save_id: int) -> int:
        """How many delta lines follow the last full line on save `save_id`'s chain (with it)."""
        return len(self.chain(save_id)) - 1

    def rebuild(self, save_id: int) -> dict:
        """Save `save_id`'s payload: its full ancestor's, with every delta on the way applied in order."""
        lines = self.chain(save_id)
        payload = _copy(lines[-1]["memory"])
        for line in reversed(lines[:-1]):
            payload = apply_delta(payload, line["memory"])
        return payload

    def frame_base(self) -> int:
        """D7: 1 + the largest frame stamp in the file (and never below an earlier session's base); 0 for a file with
        none."""
        stamps = [line["frame"] for line in self.lines if isinstance(line.get("frame"), int)]
        bases = [line["frame_base"] for line in self.lines if line["kind"] == "session"
                 and isinstance(line.get("frame_base"), int)]
        return max(bases + ([1 + max(stamps)] if stamps else []), default=0)

    def timeline(self) -> list[tuple]:
        """The LIVE history at the end of the file: ("save", id) and ("lost", line) in order, where a continue from save
        k cut everything after k (those events were undone)."""
        events: list[tuple] = []
        for line in self.lines:
            kind = line["kind"]
            if kind == "session" and line["how"] == "continue" and isinstance(line.get("continued_from"), int):
                k = line["continued_from"]
                at = next((i for i, event in enumerate(events) if event == ("save", k)), None)
                if at is not None:
                    events = events[:at + 1]
                else:
                    events = [("save", item["id"]) for item in reversed(self.chain(k))]
            elif kind == "save":
                events.append(("save", line["id"]))
            elif kind == "lost":
                events.append(("lost", line))
        return events

    def undone_losses(self, save_id: int) -> list[dict] | None:
        """The battles lost after save `save_id` that a continue from it undoes (D12 (e)): the `lost` lines after it in
        the live history. None: the save is not in the live history."""
        events = self.timeline()
        at = next((i for i, event in enumerate(events) if event == ("save", save_id)), None)
        if at is None:
            return None
        return [event[1] for event in events[at + 1:] if event[0] == "lost"]

    def dropped_after(self, save_id: int) -> dict | None:
        """(U2 spec 2026-10-30 D13) What a continue from save `save_id` DROPS, over ONE set of sessions: the sessions from
        the LATEST one that continued this save, or (when nothing has continued it yet) the save's own session from the
        save on, with every session after them. These are the events THIS continue undoes; earlier drops were told by
        earlier continues. Frames, battles and (launcher-side) maps are all counted over this set; `lost` is
        `undone_losses`, which walks the same live history. Returns None when the save is not in the live history, else
        `{"save", "sessions": [{"n", "run_dir", "own", "since", "frames"}], "frames", "at_save", "at_end", "lost"}`:
        a session's `frames` is its own `end` line's frame minus its `since` (its `frame_base`; for the save's own
        session the save's frame), None ("not recorded") when it has NO end line, never derived from a later session's
        stamps; `frames` is their sum (None if any is not recorded); `at_save` the save's play time and `at_end` the
        play time of the NEWEST session's own end line (None without one). The AI may read `frames` and `lost` only: a
        play time or a place of the dropped play is not what a person who switched off remembers (D19, ruling 40)."""
        undone = self.undone_losses(save_id)
        if undone is None:
            return None
        save = self.save(save_id)
        at = next(i for i, line in enumerate(self.lines) if line is save)
        sessions = [(i, line) for i, line in enumerate(self.lines) if line["kind"] == "session"]
        continued = [i for i, line in sessions if i > at and line.get("how") == "continue"
                     and line.get("continued_from") == save_id]
        own = next((line for i, line in reversed(sessions) if i < at), None)
        if continued:
            chosen = [line for i, line in sessions if i >= continued[-1]]
        else:
            chosen = ([own] if own is not None else []) + [line for i, line in sessions if i > at]
        entries = []
        for session in chosen:
            end = self.end_of(session["n"])
            since = save["frame"] if session is own else session.get("frame_base")
            frames = None if end is None or not isinstance(since, int) else int(end["frame"]) - since
            entries.append({"n": session["n"], "run_dir": session.get("run_dir"), "own": session is own, "since": since,
                            "frames": frames})
        newest_end = self.end_of(chosen[-1]["n"]) if chosen else None
        counted = [entry["frames"] for entry in entries]
        return {"save": save_id, "sessions": entries,
                "frames": sum(counted) if entries and None not in counted else None,
                "at_save": list(save["play_time"]), "at_end": newest_end.get("play_time") if newest_end else None,
                "lost": len(undone)}


def read_book(path) -> MemoryBook | None:
    """The memory file at `path` (read only; never changed), or None when there is none. Raises `MemoryFileError`:
    "newer" when the header's schema is newer than `SCHEMA_VERSION`, "no_header", "unreadable" for any unreadable or
    non-ASCII line but a torn last one (or a cut line a later `torn` line acknowledges). (R1 + R2 follow-up, spec D4) Every
    line is written with `ensure_ascii=True`, so a non-ASCII character in a line means a corrupted byte: that line is
    unparsable."""
    try:
        # errors="replace" ON PURPOSE (spec D4): a strict decode would raise UnicodeDecodeError past the MemoryFileError
        # contract, and one bad byte in a torn LAST line would refuse the whole file; the per-line ASCII check below
        # refuses a corrupted middle line instead
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except FileNotFoundError:
        return None
    parts = text.split("\n")
    ends_clean = text.endswith("\n") or text == ""
    if ends_clean:
        parts = parts[:-1]
    if not parts:
        raise MemoryFileError("no_header", f"{path} is empty: a memory file begins with its header")
    try:
        first = json.loads(parts[0]) if parts[0].isascii() else None  # (D4) a non-ASCII header is no header
    except ValueError:
        first = None
    if isinstance(first, dict) and first.get("kind") == "header":
        version = first.get("schema_version")
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise MemoryFileError("unreadable", f"{path}: the header's schema_version {version!r} is not a version")
        if version > SCHEMA_VERSION:
            raise MemoryFileError("newer", f"{path} was written by a newer program (schema {version}; this program "
                                           f"reads {SCHEMA_VERSION}): refused, the file is left as it is")
    else:
        raise MemoryFileError("no_header", f"{path}: the first line is not a memory header")
    lines: list = []
    torn: str | None = None
    acknowledged = 0
    parsed: list = []
    for text_line in parts:
        if not text_line.isascii():
            parsed.append(None)  # (D4) a non-ASCII line is a corrupted one: unparsable
            continue
        try:
            parsed.append(json.loads(text_line))
        except ValueError:
            parsed.append(None)
    for index, (raw, line) in enumerate(zip(parts, parsed)):
        number = index + 1
        if line is None:
            if index == len(parts) - 1:
                torn = raw
                continue
            follower = parsed[index + 1]
            if isinstance(follower, dict) and follower.get("kind") == "torn" and follower.get("length") == len(raw):
                acknowledged += 1
                continue
            raise MemoryFileError("unreadable", f"{path}: line {number} cannot be read (and is not the last line)")
        _check_line(line, number)
        if line["kind"] == "torn":
            continue
        if line["kind"] == "header" and index != 0:
            raise MemoryFileError("unreadable", f"{path}: line {number} is a second header")
        lines.append(line)
    ids = [line["id"] for line in lines if line["kind"] == "save"]
    if len(ids) != len(set(ids)):
        raise MemoryFileError("unreadable", f"{path}: two save lines share an id")
    return MemoryBook(Path(path), lines, torn=torn, ends_clean=ends_clean, acknowledged=acknowledged)


# ------------------------------------------------------------------ writing
@dataclass(frozen=True)
class SaveWrite:
    """What `MemoryWriter.write_save` did: the save's id, whether it is full, its line's size, and whether EVERY line it
    needed (header, session, save) reached the file (`RecordFile.written` rose for each)."""

    id: int
    full: bool
    size: int
    reached: bool


class MemoryWriter:
    """The play brain's writer of ONE session's lines (only through `runlog.RecordFile`, each line opened, appended and
    closed). A new game (`book` None) writes its header with its first save; a continue (`book` given) writes after the
    lines already there, after ending and acknowledging a line a kill cut short. Every append is checked: a line that
    did not reach the file makes the call return False (the brain then ends the run, spec section 3 (c))."""

    def __init__(self, path, book: MemoryBook | None, *, header: dict | None, session: dict) -> None:
        how = session.get("how")
        if how not in SESSION_HOW or session.get("host") not in HOSTS or session.get("cart") not in CARTS:
            raise MemoryFileError("state", f"a session needs how in {SESSION_HOW}, host in {HOSTS} and cart in {CARTS}")
        if (book is None) != (how == "new game"):
            raise MemoryFileError("state", "a new game writes a new file; only a continue writes after an existing one")
        if book is None and not isinstance(header, dict):
            raise MemoryFileError("state", "a new game's memory needs its header (game and identity)")
        path = Path(path)
        self.records = RecordFile(path.parent, path.name)
        self.book = book
        self.header = None if book is not None else {"kind": "header", "schema_version": SCHEMA_VERSION,
                                                     "game": header.get("game"), "identity": _copy(header.get("identity"))}
        self.session = {"kind": "session", "n": 1 + len(book.sessions()) if book is not None else 1, "started": None,
                        "how": how, "host": None, "run_dir": None, "cart": None, "frame_base": 0, "continued_from": None,
                        "page": None, "verified": None, "restored_maps": None, "losses": 0}
        self.session.update({key: value for key, value in session.items() if key != "kind"})
        self.session_written = False
        self.mend = book is not None and not book.ends_clean
        self.torn = book.torn if book is not None else None
        self.next_id = book.next_save_id() if book is not None else 1
        continued = self.session.get("continued_from")
        self.parent: int | None = continued if book is not None and isinstance(continued, int) else None
        self.last_payload: dict | None = book.rebuild(self.parent) if self.parent is not None else None
        self.deltas = book.deltas_since_full(self.parent) if self.parent is not None else 0
        self.saves_written = 0
        self.problems: list[str] = []

    def _append(self, record: dict) -> bool:
        before = self.records.written
        self.records.append(json.dumps(record, separators=(",", ":"), ensure_ascii=True))
        ok = self.records.written == before + 1
        if not ok:
            self.problems.append(f"a {record.get('kind')} line did not reach {self.records.path}")
        return ok

    def _prepare(self) -> bool:
        """Before this session's first line: end a line the last process left without its newline, acknowledge it if it
        was cut short, write the header of a new game, then this session's line."""
        ok = True
        if self.mend:
            before = self.records.written
            self.records.append("")
            ok = self.records.written == before + 1 and ok
            self.mend = False
        if self.torn is not None:
            ok = self._append({"kind": "torn", "length": len(self.torn)}) and ok
            self.torn = None
        if self.header is not None:
            ok = self._append(self.header) and ok
            self.header = None
        if not self.session_written:
            ok = self._append(self.session) and ok
            self.session_written = True
        return ok

    def write_session(self, **updates) -> bool:
        """Write this session's line now (a continue's restore, before its first look; or a STOP), with `updates`. A new
        game with no save yet writes nothing (no save, no file) and returns False."""
        if self.session_written:
            raise MemoryFileError("state", "this session's line is already written")
        if self.book is None and self.saves_written == 0:
            return False
        self.session.update({key: value for key, value in updates.items() if key != "kind"})
        return self._prepare()

    def write_save(self, *, play_time, frame: int, where: dict, party: list, why: str, payload: dict) -> SaveWrite:
        """Append a save line (at the START of the write, D5): full or a delta against the parent's payload. The next
        save's parent is this one only if the line reached the file."""
        if play_time is None:
            raise MemoryFileError("state", "a save line needs the play time the SAVING page was read with")
        full = self.parent is None or self.deltas >= FULL_EVERY
        normal = _copy(payload)
        memory = normal if full else diff(self.last_payload, normal)
        line = {"kind": "save", "id": self.next_id, "parent": self.parent, "full": full,
                "play_time": [int(play_time[0]), int(play_time[1])], "frame": int(frame), "where": _copy(where),
                "party": _copy(party), "why": str(why), "memory": memory}
        ready = self._prepare()
        reached = self._append(line) and ready
        size = len(json.dumps(line, separators=(",", ":"), ensure_ascii=True))
        result = SaveWrite(self.next_id, full, size, reached)
        if reached:
            self.parent, self.last_payload = self.next_id, normal
            self.deltas = 0 if full else self.deltas + 1
            self.saves_written += 1
        self.next_id += 1
        return result

    def _line(self, record: dict) -> bool | None:
        """Append a line of this session. None: not written, because a new game with no save yet has no file."""
        if self.book is None and self.saves_written == 0:
            return None
        ready = self._prepare()
        return self._append(record) and ready

    def write_saved(self, save_id: int, frame: int) -> bool | None:
        return self._line({"kind": "saved", "id": int(save_id), "frame": int(frame)})

    def write_lost(self, look) -> bool | None:
        """A battle lost (D12 (e)), after the save this branch last made (or continued)."""
        return self._line({"kind": "lost", "frame": int(look.frame), "play_time": _stamp_of(look), "where": where_of(look),
                           "after_save": self.parent})

    def write_end(self, reason: str, at_save: bool, frame: int, stopped_before_restore: bool = False,
                  look=None) -> bool | None:
        return self._line(end_line(self.session["n"], reason, at_save, frame, stopped_before_restore, look))
