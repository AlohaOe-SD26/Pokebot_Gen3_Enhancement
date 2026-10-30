"""TEST SIDE (build step 5.2, G4): THE PERSON-FAIR DATA DOOR. An AST gate over the AI's deciding code and its knowledge.

    py -3.12 ai_player/gates/check_fairness.py [--package DIR]        exit 0 = PASS, 1 = FAIL

WHY (USER RULINGS 35-37: only on-screen information and the hints the game's dialogue gives; the lessons draft, PL-7): the
person-fairness rules were enforced PIECEMEAL (the foe's HP as a bar, exits by their look, no catch rate, named fights
only, no invisible flags for errands), each by its own test, and two doors stayed OPEN: the milestone flags reached the
brain as a plain dict (`Progress.marks`), which ANY errand could read (exactly how step 5 shopped on FLAG_ADVENTURE_STARTED
and healed on FLAG_RESCUED_BIRCH), and the knowledge files carry DEVELOPER data (measured coordinates, decomp locations,
trainer ids and flags, the bot's teaching sources) that nothing stopped the AI from reading. Chapters 3-4 bring the most
developer-only data yet. So:

RULE A, THE FLAG DOOR. In the DECIDING code (`DECIDING`: brain/, skills/, hands/, world/, mode.py, personality.py and, since
R2, game_memory.py, whose restored memory the brain decides from) the game's
flags (`FLAG_FIELDS`: `.marks` and `.flags` of anything but the object's own `self`/`cls`, also through `getattr` with a
constant name) and the door function `marks_of` may be read ONLY where `FLAG_DOORS` declares it, each with its PURPOSE:
milestone detection (the memory of events the player LIVED THROUGH) and novelty (a story event that just happened counts as
progress). An errand decides only from on-screen facts: it is in no door. A string whose WHOLE value names a game flag or
var (`FLAG_*`, `VAR_*`, `TRAINER_*`, or a proof name of `knowledge/milestones.json`) is refused there too: a hidden flag's
name has no business in deciding code.
RULE B, THE KNOWLEDGE FILES. Every key path of every knowledge file is CLASSIFIED in `KNOWLEDGE_FIELDS` (`ai`: what a person
knows, with its purpose; `developer`: for the developers' proofs only, with why; `hidden`: carried for the test side, never
read by the brain; `meta`: where the file came from) and an unclassified path FAILS, so new developer data must be marked
before it lands. Then:
  B1  only the declared LOADERS (`LOADERS`) may name a knowledge file;
  B2  no loader and no deciding code may subscript (`x["k"]`, `x.get("k")`, `.pop`, `.setdefault`) a key that is
      DEVELOPER-ONLY (a key name that occurs in the knowledge only under developer paths: `developer_keys()`), and only a
      loader declared to CARRY it (`CARRIES`) may subscript a HIDDEN key;
  B3  the deciding code may not read a species' hidden facts (`HIDDEN_ATTRIBUTES`: base stats, catch rate, experience,
      growth) from a `species_fact(...)` value, directly or through a name bound to one in the same function, and may
      never name `.catch_rate`, `.exp_yield` or `.growth` at all.

RULE C, THE PLAY TIME (R1 + R2, build spec 2026-10-29 D18). The game's play time (`Progress.play_time`) is not on the
screen the AI watches (a person sees it on the trainer card, the save window and CONTINUE), so in the deciding code only
the save code reads it (`PLAY_TIME_DOORS`, each with its purpose): the save and continue skill, the save policy, the
memory file. A door no read goes through is stale, as RULE A's are.

MENTIONS NEVER FIRE: the AST has no comments; a string statement (a docstring) is skipped, and so is the text of an
f-string; a string counts only when its WHOLE value is the name; a dict DISPLAY's keys are not reads; `self.flags` is the
object's own field. `test_safety_gates.py` G4 proves both directions on plants (an errand keyed on a mark, a coordinate
read, a hidden fact, an unclassified knowledge key) and on mentions.

LIMITS. Static analysis cannot follow a value: a marks dict a door hands on (as an argument) to an errand is not traced (the
door's purpose is the review point, and the flag-name rule refuses the errand's key); a key name that is AI-visible in one
file and developer-only in another (`id`, `map`, `metatile`) is not refused by name (its developer paths are still marked);
and the developer-only key NAMES (`x`, `y`, `state`, `line`, ...) are refused in every dict the deciding code reads, so a
dict of the AI's own that wants one of those names must use another (the price of a rule by name).
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from fnmatch import fnmatchcase
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
#: the AI's DECIDING code (folders and files of the package)
DECIDING = ("brain", "skills", "hands", "world", "mode.py", "personality.py", "game_memory.py")
#: the knowledge LOADERS: file -> the knowledge files it may name and read
LOADERS = {
    "knowledge/story.py": ("milestones.json",),
    "knowledge/facts.py": ("types.json", "moves.json", "species.json"),
    "personality.py": ("wild_species.json",),
}
#: the loaders that CARRY hidden keys into a record the brain must not read (rule B2/B3): file -> hidden keys
CARRIES = {
    "knowledge/facts.py": ("base", "hp", "attack", "defense", "speed", "sp_attack", "sp_defense", "catch_rate", "exp_yield",
                           "growth"),
}
#: RULE A: the game's flags as the eyes hand them over (`eyes/observation.py` Progress)
FLAG_FIELDS = {"marks": "save block 1's milestone flags and vars (`Progress.marks`)",
               "flags": "the story flags (`Progress.flags`)"}
FLAG_DOOR_CALLS = {"marks_of": "`brain/goals.py` marks_of: the marks of a look, as a dict"}
#: RULE A's allowlist: (file, function qualname, what is read, its PURPOSE)
FLAG_DOORS: list[tuple[str, str, str, str]] = [
    ("brain/goals.py", "marks_of", "marks",
     "THE DOOR itself: a look's milestone marks as a dict, for milestone detection only"),
    ("brain/goals.py", "GoalManager.milestone", "marks_of",
     "MILESTONE DETECTION: the first milestone the marks do not prove: the memory of events the player LIVED THROUGH"),
    ("mode.py", "HandsBrain._play", "marks",
     "MILESTONE DETECTION: are the marks read in this look (then the goal manager names the milestone)"),
    ("mode.py", "HandsBrain._play.current", "marks",
     "MILESTONE DETECTION: the milestone now, once the marks are read"),
    ("mode.py", "HandsBrain._milestone_line", "marks",
     "MILESTONE DETECTION: the log's MILESTONE line (passed, its proofs): events the player lived through; and (R1, D18) "
     "the save after a big story moment (USER RULING 51): only milestone ids reach `brain/saving.py`"),
    ("brain/navigator.py", "Novelty._flags", "flags",
     "NOVELTY: a story flag that just turned on is an event the player just lived through (progress for the intent's "
     "clock); it never chooses where to go"),
]
#: RULE C (R1 + R2, build spec 2026-10-29 D18): the game's PLAY TIME (`Progress.play_time`, hours and minutes) is not on the
#: screen the AI watches: a person sees it on the trainer card, the save window and CONTINUE. So in the deciding code only
#: these may READ it (`.play_time` of anything but `self`/`cls`, or `getattr(x, "play_time")`): (file, function qualname
#: or "*" for the whole file, its PURPOSE). A door's nested functions are inside it. `hands/dialogue.py` seen_now DROPS it
#: (`replace(progress, play_time=None)`: a keyword, no read), so it needs no door.
PLAY_TIME_FIELD = "play_time"
PLAY_TIME_DOORS: list[tuple[str, str, str]] = [
    ("skills/saving.py", "*", "THE SAVE AND THE CONTINUE: the stamp read on the SAVING page (what the game writes into the "
                              "save), checked through the write; the CONTINUE window's TIME"),
    ("brain/saving.py", "*", "WHEN TO SAVE: 3 game minutes between saves (`SAVE_MIN_MINUTES`); no save without the play time"),
    ("game_memory.py", "*", "THE MEMORY FILE: every line's stamp, so a continue matches the save the game loaded"),
]
#: a game flag's or var's constant name; a trainer's flag is named by the milestone proofs (`TRAINER_JOSH`): a bare
#: `TRAINER_` prefix is no flag (`skills/flee.py` exports TRAINER_OUT_OF_SCOPE, a refusal's name)
_FLAG_NAME = re.compile(r"(?:FLAG|VAR)_[A-Z0-9_]+")
#: RULE B3: a species' facts the decider may never read (step 4.1: "the decider reads a species' TYPES and NAME only")
HIDDEN_ATTRIBUTES = ("hp", "attack", "defense", "speed", "sp_attack", "sp_defense", "catch_rate", "exp_yield", "growth")
HIDDEN_ANYWHERE = ("catch_rate", "exp_yield", "growth")
SPECIES_FACT_CALLS = ("species_fact",)

AI, DEVELOPER, HIDDEN, META = "ai", "developer", "hidden", "meta"
#: RULE B: every key path of every knowledge file -> (kind, why, covers its whole subtree). `*` is any one key, `[]` a list.
KNOWLEDGE_FIELDS: dict[str, dict[str, tuple[str, str, bool]]] = {
    "milestones.json": {
        "provenance": (META, "where the file came from (extractor, teacher sources, tables)", True),
        "gendered_maps": (AI, "which house is the player's and which the rival's, by the gender the AI chose", True),
        "looks": (AI, "what a person RECOGNISES on screen, by name", False),
        "looks.*": (AI, "one look", False),
        "looks.*.gfx": (AI, "a figure's object graphics ids: what a person sees", True),
        "looks.*.metatile": (AI, "a tile's metatile ids: what a person sees", True),
        "looks.*.what": (AI, "the look in words", True),
        "looks.*.decomp": (DEVELOPER, "where the decomp defines it: the developers' proof (`--verify`)", True),
        "looks.*.measured": (DEVELOPER, "COORDINATES the developers MEASURED (the clock's tile): proof design only, never "
                                        "a hint", True),
        "trainers": (AI, "the trainers of the story's fights, by name", False),
        "trainers.*": (AI, "one trainer", False),
        "trainers.*.levels": (AI, "how strong a fight is: used only for a fight the game NAMES or whose levels are SEEN "
                                  "(G72)", True),
        "trainers.*.id": (DEVELOPER, "the game's trainer id: the developers' cross-check", True),
        "trainers.*.flag": (DEVELOPER, "the trainer's flag NUMBER: the developers' cross-check", True),
        "milestones": (AI, "the story a person knows is ahead", False),
        "milestones[]": (AI, "one milestone", False),
        "milestones[].id": (AI, "its name", True),
        "milestones[].chapter": (AI, "its chapter", True),
        "milestones[].title": (AI, "its title", True),
        "milestones[].done": (AI, "its PROOFS: read only by milestone detection through the flag door (rule A)", True),
        "milestones[].waypoint": (AI, "a map the player stands on when it has passed", True),
        "milestones[].optional": (AI, "a milestone the path may never meet (the gym's trainers)", True),
        "milestones[].maps": (AI, "where it happens", True),
        "milestones[].steps": (AI, "what a person DOES for it (go, talk, ask, use, follow)", True),
        "milestones[].hint": (AI, "the game's own words that tell it, and where", True),
        "milestones[].fight": (AI, "the fight's levels and whether the game names it", True),
        "milestones[].note": (DEVELOPER, "the developers' explanation of the proofs", True),
        "milestones[].taught_by": (DEVELOPER, "the bot's teaching source (file, line, sha256): the teacher, never read", True),
        "milestones[].decomp": (DEVELOPER, "where the decomp defines each proof: the developers' check", True),
    },
    "species.json": {
        "provenance": (META, "where the file came from", True),
        "what": (META, "what the file holds, in words", True),
        "species": (AI, "every species by the name the game shows", False),
        "species.*": (AI, "one species", False),
        "species.*.types": (AI, "its types (a Pokedex shows them)", True),
        "species.*.dex": (AI, "its POKéDEX number", True),
        "species.*.base": (HIDDEN, "base stats: carried for the test side (TYPICAL_BASE's median), never read by the "
                                   "brain (step 4.1 round 3)", True),
        "species.*.catch_rate": (HIDDEN, "the catch rate: hidden (step 4.1 round 1, the ball by what is seen)", True),
        "species.*.exp_yield": (HIDDEN, "the experience yield: hidden", True),
        "species.*.growth": (HIDDEN, "the growth rate: hidden", True),
    },
    "moves.json": {
        "provenance": (META, "where the file came from", True),
        "what": (META, "what the file holds, in words", True),
        "moves": (AI, "every move as the game and a strategy guide describe it (type, power, accuracy, PP, effect, "
                      "recoil)", True),
    },
    "types.json": {
        "provenance": (META, "where the file came from", True),
        "what": (META, "what the file holds, in words", True),
        "types": (AI, "the types", True),
        "physical_types": (AI, "the Gen-3 physical types", True),
        "special_types": (AI, "the Gen-3 special types", True),
        "chart": (AI, "the type chart a person knows", True),
    },
    "wild_species.json": {
        "provenance": (META, "where the file came from", True),
        "species": (AI, "the species a person can meet in the wild (the favourite is drawn from them)", True),
    },
}


# ---------------------------------------------------------------------- the knowledge schema (rule B)
Path_ = tuple[str, ...]


def key_paths(value, path: Path_ = ()) -> list[Path_]:
    """Every key path of a JSON value, as a tuple of its keys ('[]' for a list's items, each item walked): a key may hold
    a dot ('Mr. Mime'), so a path is never split on one."""
    out: list[Path_] = []
    if isinstance(value, dict):
        for key, item in value.items():
            here = (*path, str(key))
            out.append(here)
            out += key_paths(item, here)
    elif isinstance(value, list):
        for item in value:
            out += key_paths(item, (*path, "[]"))
    return out


def shown(path: Path_) -> str:
    return ".".join(path).replace(".[]", "[]")


def _pattern(pattern: str) -> Path_:
    return tuple(re.findall(r"[^.\[\]]+|\[\]", pattern.replace("[]", ".[]")))


def classify(path: Path_, fields: dict[str, tuple[str, str, bool]]) -> tuple[str, tuple[str, str, bool]] | None:
    """The schema entry that classifies a concrete key path: an exact pattern, else the longest SUBTREE pattern over it."""
    best = None
    for pattern, entry in fields.items():
        parts = _pattern(pattern)
        if len(parts) > len(path) or not all(fnmatchcase(s, p) for s, p in zip(path, parts)):
            continue
        if len(parts) == len(path):
            return pattern, entry
        if entry[2] and (best is None or len(parts) > len(_pattern(best[0]))):
            best = (pattern, entry)
    return best


def schema_problems(knowledge: Path, fields: dict[str, dict] = KNOWLEDGE_FIELDS) -> tuple[list[str], dict[str, int]]:
    """(problems, how many key paths of each kind): every knowledge file has a schema and every path is classified."""
    problems: list[str] = []
    counts: dict[str, int] = {}
    for path in sorted(knowledge.glob("*.json")):
        schema = fields.get(path.name)
        if schema is None:
            problems.append(f"knowledge/{path.name}: a knowledge file with no schema in KNOWLEDGE_FIELDS (classify its "
                            f"fields: ai / developer / hidden / meta)")
            continue
        paths = sorted(set(key_paths(json.loads(path.read_text(encoding="utf-8")))))
        unclassified = [shown(p) for p in paths if classify(p, schema) is None]
        if unclassified:
            problems.append(f"knowledge/{path.name}: {len(unclassified)} UNCLASSIFIED key paths {unclassified[:8]}: mark "
                            f"each in KNOWLEDGE_FIELDS (developer data is never left unmarked)")
        for p in paths:
            found = classify(p, schema)
            if found is not None:
                counts[found[1][0]] = counts.get(found[1][0], 0) + 1
    return problems, counts


def developer_keys(fields: dict[str, dict] = KNOWLEDGE_FIELDS, knowledge: Path | None = None) -> set[str]:
    """The key NAMES that occur only under developer paths (in the files, when given; else in the patterns)."""
    developer: set[str] = set()
    elsewhere: set[str] = set()
    for name, paths in _sources(fields, knowledge):
        for p in paths:
            found = classify(p, fields[name])
            keys = [s for s in p if s != "[]"]
            if not keys:
                continue
            (developer if found is not None and found[1][0] == DEVELOPER else elsewhere).add(keys[-1])
    return developer - elsewhere


def _sources(fields: dict[str, dict], knowledge: Path | None) -> list[tuple[str, list[Path_]]]:
    """(file, its key paths): the files' own paths when the folder is given, else the schema's patterns."""
    if knowledge is None:
        return [(name, [_pattern(p) for p in schema]) for name, schema in fields.items()]
    return [(path.name, sorted(set(key_paths(json.loads(path.read_text(encoding="utf-8"))))))
            for path in sorted(knowledge.glob("*.json")) if path.name in fields]


def hidden_keys(fields: dict[str, dict] = KNOWLEDGE_FIELDS, knowledge: Path | None = None) -> set[str]:
    out: set[str] = set()
    for name, paths in _sources(fields, knowledge):
        for p in paths:
            found = classify(p, fields[name])
            keys = [s for s in p if s != "[]"]
            if found is not None and found[1][0] == HIDDEN and keys:
                out.add(keys[-1])
    return out


# ---------------------------------------------------------------------- the AST rules
def _owners(tree: ast.AST) -> dict[int, str]:
    """Each node -> the qualname of its innermost function or class ('<module>' at the top)."""
    owner: dict[int, str] = {}

    def visit(node: ast.AST, name: str) -> None:
        for child in ast.iter_child_nodes(node):
            inner = name
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                inner = child.name if name == "<module>" else f"{name}.{child.name}"
            owner[id(child)] = inner
            visit(child, inner)

    visit(tree, "<module>")
    return owner


def _skipped_strings(tree: ast.AST) -> set[int]:
    """String constants that are never a value: docstrings and other string statements, f-string text, and the names a
    module EXPORTS (`__all__`: Python names, not game data)."""
    out: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            out.add(id(node.value))
        if isinstance(node, ast.JoinedStr):
            out.update(id(v) for v in node.values if isinstance(v, ast.Constant))
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets) and node.value is not None:
                out.update(id(v) for v in ast.walk(node.value) if isinstance(v, ast.Constant))
    return out


def _subscript_keys(node: ast.AST) -> str | None:
    """The constant key a node READS: `x["k"]` (loaded), `x.get("k")`, `.pop("k")`, `.setdefault("k")`."""
    if isinstance(node, ast.Subscript) and isinstance(node.ctx, ast.Load) and isinstance(node.slice, ast.Constant) \
            and isinstance(node.slice.value, str):
        return node.slice.value
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("get", "pop", "setdefault") \
            and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    return None


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def files_of(package: Path, parts) -> list[Path]:
    out: list[Path] = []
    for part in parts:
        path = package / part
        if path.is_dir():
            out += sorted(p for p in path.rglob("*.py") if "__pycache__" not in p.parts)
        elif path.is_file():
            out.append(path)
    return out


def time_door(rel: str, qualname: str) -> tuple[str, str] | None:
    """(RULE C) The PLAY_TIME_DOORS entry (file, function) that lets function `qualname` of file `rel` read the play time,
    or None. A door's nested functions are inside it; "*" is the whole file."""
    for file, function, _ in PLAY_TIME_DOORS:
        if file == rel and (function == "*" or qualname == function or qualname.startswith(function + ".")):
            return file, function
    return None


def scan_file(rel: str, source: str, flag_names: set[str], dev_keys: set[str], hid_keys: set[str],
              knowledge_files: set[str], used: set | None = None) -> list[str]:
    """The rule breaches of one file (relative POSIX path `rel` in the package); `used` collects the doors read through."""
    tree = ast.parse(source)
    owner = _owners(tree)
    skipped = _skipped_strings(tree)
    deciding = rel in DECIDING or rel.split("/")[0] in DECIDING
    loader = rel in LOADERS
    doors = {(f, q, w) for f, q, w, _ in FLAG_DOORS}
    out: list[str] = []

    def where(node: ast.AST) -> str:
        return f"{rel}:{getattr(node, 'lineno', '?')} ({owner.get(id(node), '<module>')})"

    # B3's tracked names: a name bound to a species_fact(...) value, per function
    fact_names: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and _call_name(node.value) in SPECIES_FACT_CALLS:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    fact_names.setdefault(owner.get(id(node), "<module>"), set()).add(target.id)
    for node in ast.walk(tree):
        here = owner.get(id(node), "<module>")
        if deciding:
            # RULE A: the flag fields and the door function
            field = None
            if isinstance(node, ast.Attribute) and node.attr in FLAG_FIELDS and isinstance(node.ctx, ast.Load) \
                    and not (isinstance(node.value, ast.Name) and node.value.id in ("self", "cls")):
                field = node.attr
            if isinstance(node, ast.Call) and _call_name(node) in ("getattr", "hasattr") and len(node.args) >= 2 \
                    and isinstance(node.args[1], ast.Constant) and node.args[1].value in FLAG_FIELDS:
                field = node.args[1].value
            if isinstance(node, ast.Call) and _call_name(node) in FLAG_DOOR_CALLS:
                field = _call_name(node)
            if field is not None and (rel, here, field) not in doors:
                out.append(f"A  {where(node)}: reads the game's flags ({field}) outside the flag door: an errand decides "
                           f"from on-screen facts only; a new purpose is a reviewed entry of FLAG_DOORS")
            elif field is not None and used is not None:
                used.add((rel, here, field))
            # RULE C (R1, D18): the game's play time, read only through its doors
            reads_time = (isinstance(node, ast.Attribute) and node.attr == PLAY_TIME_FIELD and isinstance(node.ctx, ast.Load)
                          and not (isinstance(node.value, ast.Name) and node.value.id in ("self", "cls")))
            reads_time = reads_time or (isinstance(node, ast.Call) and _call_name(node) in ("getattr", "hasattr")
                                        and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant)
                                        and node.args[1].value == PLAY_TIME_FIELD)
            if reads_time:
                door = time_door(rel, here)
                if door is None:
                    out.append(f"C  {where(node)}: reads the game's PLAY TIME outside its doors (PLAY_TIME_DOORS): it is "
                               f"not on the screen the AI watches; only the save code may read it")
                elif used is not None:
                    used.add(("time", door[0], door[1]))
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skipped \
                    and (_FLAG_NAME.fullmatch(node.value) or node.value in flag_names):
                out.append(f"A  {where(node)}: names the game flag {node.value!r}: a hidden flag's name has no business in "
                           f"deciding code")
            # RULE B1: only a loader names a knowledge file
            if not loader and isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skipped \
                    and any(node.value == name or node.value.endswith("/" + name) for name in knowledge_files):
                out.append(f"B1 {where(node)}: names the knowledge file {node.value!r}: only a declared loader reads one")
            # RULE B3: a species' hidden facts
            if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
                if node.attr in HIDDEN_ANYWHERE:
                    out.append(f"B3 {where(node)}: reads .{node.attr}, a hidden species fact")
                elif node.attr in HIDDEN_ATTRIBUTES and (
                        (isinstance(node.value, ast.Call) and _call_name(node.value) in SPECIES_FACT_CALLS)
                        or (isinstance(node.value, ast.Name) and node.value.id in fact_names.get(here, set()))):
                    out.append(f"B3 {where(node)}: reads .{node.attr} of a species_fact value (a base stat): hidden")
        if deciding or loader:
            key = _subscript_keys(node)
            if key is not None and key in dev_keys:
                out.append(f"B2 {where(node)}: reads the DEVELOPER-ONLY knowledge key {key!r} (coordinates, decomp "
                           f"locations, trainer flags, teaching sources): for the developers' proofs, never the AI")
            elif key is not None and key in hid_keys and key not in CARRIES.get(rel, ()) and loader:
                out.append(f"B2 {where(node)}: reads the HIDDEN knowledge key {key!r}, which this loader is not declared "
                           f"to carry")
    return out


def check(package: Path = PACKAGE) -> tuple[bool, list[str], str]:
    """(ok, the breaches, a summary line) of the package at `package`."""
    knowledge = package / "knowledge"
    problems, counts = schema_problems(knowledge)
    flag_names: set[str] = set()
    milestones = knowledge / "milestones.json"
    if milestones.is_file():
        data = json.loads(milestones.read_text(encoding="utf-8"))
        for milestone in data.get("milestones", []):
            done = milestone.get("done") or {}
            flag_names |= set(done.get("flags") or {}) | set(done.get("variables") or {})
            flag_names |= {f"TRAINER_{name}" for name in done.get("trainers") or {}}
    dev_keys = developer_keys(knowledge=knowledge)
    hid_keys = hidden_keys(knowledge=knowledge)
    names = {p.name for p in knowledge.glob("*.json")}
    scanned = 0
    used: set[tuple[str, str, str]] = set()
    for path in sorted(set(files_of(package, (*DECIDING, *LOADERS)))):
        rel = path.relative_to(package).as_posix()
        scanned += 1
        problems += scan_file(rel, path.read_text(encoding="utf-8"), flag_names, dev_keys, hid_keys, names, used)
    # a door no read goes through any more is STALE: it would let a new read into that function silently
    for file, qualname, what, _ in FLAG_DOORS:
        if (file, qualname, what) not in used:
            problems.append(f"FLAG_DOORS: the door ({file}, {qualname}, {what}) is read by nothing: a stale door (remove "
                            f"it, or the read moved: review where)")
    for file, function, _ in PLAY_TIME_DOORS:
        if ("time", file, function) not in used:
            problems.append(f"PLAY_TIME_DOORS: the door ({file}, {function}) reads no play time: a stale door (remove it, "
                            f"or the read moved: review where)")
    summary = (f"{scanned} files (deciding code and loaders); {len(FLAG_DOORS)} flag doors, each with its purpose; "
               f"knowledge key paths by kind {dict(sorted(counts.items()))}; developer-only keys {sorted(dev_keys)}; "
               f"hidden keys {sorted(hid_keys)}")
    return not problems, problems, summary


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--package", type=Path, default=PACKAGE)
    args = parser.parse_args()
    ok, problems, summary = check(args.package.resolve())
    for line in problems:
        print(f"  [FAIL] {line}")
    print(summary)
    print(f"PERSON-FAIR DATA DOOR: {'PASS' if ok else 'FAIL'} ({len(problems)} breaches)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
