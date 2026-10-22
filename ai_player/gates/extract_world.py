#!/usr/bin/env python3
"""KB2 slice 1 (spec S3-4): the world a seasoned player knows: trainers, bosses (L2), maps and the campaign manifest (L1).

    py -3.12 ai_player/gates/extract_world.py                 # writes ai_player/knowledge/world/*.json from the PINNED clone
    py -3.12 ai_player/gates/extract_world.py --check         # re-extracts into a temp folder; exit 1 if a file differs
    py -3.12 ai_player/gates/extract_world.py --decomp DIR    # a clone elsewhere (its HEAD must still equal tools/decomp.pin)

INTENT (USER RULING 40, a SEASONED player): the AI knows the game's static facts the way a person who has played Emerald
before knows them: who the trainers are and what they send out, where the doors and the trainers stand, which badge
lets a field move be used, and the order of the story. This file turns the pret/pokeemerald decomp into four JSON files
under `ai_player/knowledge/world/`:
  trainers.json  every id in include/constants/opponents.h (855) joined to its src/data/trainers.h block and its party in
                 src/data/trainer_parties.h, ALL FOUR party shapes; `rematch_of` from gRematchTable (src/battle_setup.c).
  bosses.json    L2: every gym leader, Elite Four member, Champion, rival fight, Magma/Aqua leader and admin that a map
                 script battles; each party with moves (custom, or the game's default moveset derived from KB1's
                 learnsets) and types (KB1 species, marked derived_from); the gym leaders' badges read from their
                 defeat scripts; `measured` is null (A6's chapter_priors.json is not generated yet).
  maps.json      every map folder: header fields, connections, warps (coordinates kept: RULING 45), trainers joined to
                 their trainerbattle lines (tile and sight range kept: RULING 45), item balls and hidden items.
  campaign.json  L1: the hand-authored skeleton (gates/campaign_skeleton.json: ids, order, chapters, areas, bosses) with
                 every `needs` field filled from the data above. Never routes, coordinates or step lists (W6).
WHY HERE AND NOT AT THE KNOWLEDGE TOP LEVEL: check_fairness.py globs `knowledge/*.json` (not recursive) and fails on a
file with no KNOWLEDGE_FIELDS schema. Nothing may read these files until a loader and that classification exist (a
separate, graded step), so all four live in the unglobbed `world/` folder (coordinator decision A, 2026-10-21).

WITHHELD (USER RULING 44, 2026-10-21): `iv` and `aiFlags` never leave the decomp (WITHHELD_FIELDS; refuse_withheld runs
on every file before it is written, and verify_world.py scans every file under knowledge/). `heldItem` is ALLOWED (a
seasoned player knows what a boss holds) and is written as `held_item`; moves and levels are kept. The bot's species
shares never enter (USER RULING 45). Trainers' bag items (`.items`) are not in the spec's field list and are not written.

NOT IN THIS SLICE (so an absent list is never read as "none"): items_gifts.json and events.json (slice 2, NEEDS DESIGN),
gifts, marts and scripted events, and tools/make_chapter_pack.py with its W7 adversarial pass (the next slice).

THE GUARDS (each refuses with exit 2 naming what it found; test_kb2.py feeds each a broken input beside a healthy one,
and a scratch mutant that deletes each CALL is caught):
  refuse_withheld      W1  a withheld field (iv / aiFlags, any spelling) in an output
  check_party_count    W5  parsed party arrays != the `static const struct TrainerMon` arrays in trainer_parties.h
  check_parties        W5  a trainer with an empty party other than TRAINER_NONE (trainers.h `.partySize = 0`, by name),
                           a party array that does not exist, or a macro whose shape differs from the array's struct
  check_field_moves        the badge table of src/party_menu.c disagrees with src/field_control_avatar.c's FlagGet lines
  leader_badge             a gym leader whose defeat script sets no badge, or more than one
  check_milestone_ids  W4  the skeleton's first ids are not milestones.json's milestones, in order
  check_area_maps      W4  an area map the skeleton names is not in maps.json
  check_bosses             a skeleton boss that is no bosses.json fight; a key item that items.h does not define
  cite_line                a skeleton citation whose line is not in the decomp
  check_badge_order    W4b a needed badge that no EARLIER entry's boss awards
  refuse_route_keys    W6  a key named x, y, route, path, steps or coords in campaign.json
The decomp is read ONLY from the pinned local clone (tools/decomp.pin), never `gh api`; verify_world.py re-derives the
outputs by its own regex reading of the raw text and never imports this file.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from extract_seasoned import Decomp, balanced, parse_defines, parse_enum_blocks, write_json  # noqa: E402  (spec S3-4)

REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT_DEFAULT = os.path.join(REPO, "ai_player", "knowledge", "world")
SKELETON_DEFAULT = os.path.join(HERE, "campaign_skeleton.json")
SEASONED_DEFAULT = os.path.join(REPO, "ai_player", "knowledge", "seasoned")
MILESTONES_DEFAULT = os.path.join(REPO, "ai_player", "knowledge", "milestones.json")
PIN_FILE = os.path.join(REPO, "tools", "decomp.pin")
DEFAULT_DECOMP = os.path.normpath(os.path.join(REPO, "..", "_decomp", "pokeemerald"))
MADE_BY = "ai_player/gates/extract_world.py"
MAX_LABELS = 400  # bound on one script closure (the largest map script reaches far fewer labels)
OUTPUTS = ("trainers.json", "bosses.json", "maps.json", "campaign.json")

#: USER RULING 44 (2026-10-21): exact stats and AI flags stay withheld. Matched on the key with case and every
#: non-letter dropped, plus a plural, so `ivs`, `IV`, `ai_flags` and `AI-Flags` are all caught.
WITHHELD_FIELDS = ("iv", "aiFlags")
_WITHHELD_NORMS = {"iv", "ivs", "aiflags"}
#: W6, L1's rule: a manifest must never become the bot's script.
ROUTE_KEYS = ("x", "y", "route", "path", "steps", "coords")
#: struct suffix -> (the trainers.h macro, has a held item, has custom moves): include/data.h:67-70
PARTY_SHAPES = {
    "NoItemDefaultMoves": ("NO_ITEM_DEFAULT_MOVES", False, False),
    "NoItemCustomMoves": ("NO_ITEM_CUSTOM_MOVES", False, True),
    "ItemDefaultMoves": ("ITEM_DEFAULT_MOVES", True, False),
    "ItemCustomMoves": ("ITEM_CUSTOM_MOVES", True, True),
}
#: W5's ONE exemption from "party length >= 1", by NAME (coordinator decision B): trainers.h:2-14 gives TRAINER_NONE
#: `.partySize = 0` and a NULL party; it is the "no trainer" placeholder, never battled.
EXEMPT_EMPTY_PARTY = ("TRAINER_NONE",)
ROLE_OF_CLASS = {
    "TRAINER_CLASS_LEADER": "gym_leader", "TRAINER_CLASS_ELITE_FOUR": "elite_four",
    "TRAINER_CLASS_CHAMPION": "champion", "TRAINER_CLASS_RIVAL": "rival",
    "TRAINER_CLASS_AQUA_LEADER": "team_leader", "TRAINER_CLASS_MAGMA_LEADER": "team_leader",
    "TRAINER_CLASS_AQUA_ADMIN": "team_admin", "TRAINER_CLASS_MAGMA_ADMIN": "team_admin",
}
#: a boss note is written only when it is cited to the party's own moves (spec: "notes that change play only where a
#: decomp or recon source is cited"): two or more of these on one mon is a stall set.
STALL_MOVES = ("MOVE_REST", "MOVE_DOUBLE_TEAM", "MOVE_MINIMIZE", "MOVE_PROTECT", "MOVE_TOXIC", "MOVE_SLEEP_TALK",
               "MOVE_SUBSTITUTE", "MOVE_ATTRACT")
#: the trainerbattle macros' argument index of the post-defeat script (asm/macros/event.inc:788 and :800)
EVENT_SCRIPT_ARG = {"trainerbattle_single": 3, "trainerbattle_double": 4}
REMATCH_MACROS = ("trainerbattle_rematch", "trainerbattle_rematch_double")
NOT_IN_SLICE = ("items_gifts.json and events.json (spec S3-4 slice 2, NEEDS DESIGN): gifts, marts, TM gifts and scripted "
                "events are NOT here, so an absent list is not 'none'; tools/make_chapter_pack.py and its W7 adversarial "
                "pass are the next slice")
READER = ("no loader reads this file yet; check_fairness.py does not glob knowledge/world (fact 2), and nothing in "
          "ai_player's play code may read it until a loader and a KNOWLEDGE_FIELDS classification exist")
MEASURED_NULL = ("null: A6's chapter_priors.json (spec S3-3) is not generated yet (it waits for the AI's loader); when it "
                 "is, this block is copied from it and labelled source: 'bot corpus'")


class Refused(Exception):
    """A guard's refusal: the decomp, the skeleton or an output breaks a rule; nothing is written."""


# ---------------------------------------------------------------- the pinned clone
def resolve_decomp(explicit=None):
    """The decomp root: `explicit`, else env POKEBOT_DECOMP, else ../_decomp/pokeemerald; its HEAD must equal the pin.
    WHY: an answer from another commit is the failure the pin exists to prevent (tools/decomp_lookup.py, spec S3-2)."""
    root = explicit or os.environ.get("POKEBOT_DECOMP") or DEFAULT_DECOMP
    with open(PIN_FILE, encoding="utf-8") as f:
        pin = f.read().strip()
    r = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True)
    head = r.stdout.strip()
    if r.returncode != 0 or head != pin:
        raise Refused("the decomp at %s is at %r, not the pinned %s (tools/decomp.pin)" % (root, head or None, pin))
    return root


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def cite_line(d, rel, needle):
    """GUARD: 'rel:N' of the first line whose stripped text contains `needle`; refuses when there is none.
    WHY: a skeleton claim that quotes the decomp must stay TRUE for the pinned decomp, or it is not a citation."""
    for i, ln in enumerate(d.read(rel).splitlines(), 1):
        if needle in ln:
            return "%s:%d" % (rel, i)
    raise Refused("cited line not found in %s: %r" % (rel, needle))


# ---------------------------------------------------------------- the W1 and W6 scans
def withheld_keys(obj, path="$"):
    """Every key path in `obj` whose key is a withheld field (WITHHELD_FIELDS, any case or spelling)."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if re.sub(r"[^a-z]", "", str(k).lower()) in _WITHHELD_NORMS:
                out.append("%s.%s" % (path, k))
            out += withheld_keys(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += withheld_keys(v, "%s[%d]" % (path, i))
    return out


def refuse_withheld(name, obj):
    hits = withheld_keys(obj)
    if hits:
        raise Refused("%s holds withheld fields %s (USER RULING 44: iv and aiFlags stay out)" % (name, hits[:5]))


def route_keys(obj, path="$"):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ROUTE_KEYS:
                out.append("%s.%s" % (path, k))
            out += route_keys(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += route_keys(v, "%s[%d]" % (path, i))
    return out


def refuse_route_keys(obj):
    hits = route_keys(obj)
    if hits:
        raise Refused("campaign.json holds route keys %s (W6: never routes, coordinates or step lists)" % hits[:5])


# ---------------------------------------------------------------- trainers
def trainer_ids(d):
    t = d.read("include/constants/opponents.h")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^#define\s+(TRAINER_\w+)\s+(\d+)\s*$", t, re.M)}


def class_names(d):
    t = d.read("src/data/text/trainer_class_names.h")
    return {m.group(1): m.group(2) for m in re.finditer(r'\[(TRAINER_CLASS_\w+)\]\s*=\s*_\("([^"]*)"\)', t)}


def parse_party_arrays(d, shapes=PARTY_SHAPES):
    """({array name: {shape, line, members}}, the count of `static const struct TrainerMon` arrays in the file).
    Each member: {iv, lvl, species, heldItem?, moves?} as written (the iv is read only to be dropped)."""
    rel = "src/data/trainer_parties.h"
    t = d.read(rel)
    raw_count = len(re.findall(r"static const struct TrainerMon\w*\s+\w+\s*\[\s*\]", t))
    arrays = {}
    pat = re.compile(r"static const struct TrainerMon(%s)\s+(\w+)\s*\[\s*\]\s*=\s*\{" % "|".join(shapes))
    for m in pat.finditer(t):
        shape, name = m.group(1), m.group(2)
        start = m.end() - 1
        body = t[start + 1:balanced(t, start) - 1]
        members, i = [], 0
        while True:
            j = body.find("{", i)
            if j < 0:
                break
            k = balanced(body, j)
            mt = body[j:k]
            mem = {"lvl": int(re.search(r"\.lvl\s*=\s*(\d+)", mt).group(1)),
                   "species": re.search(r"\.species\s*=\s*(SPECIES_\w+)", mt).group(1)}
            iv = re.search(r"\.iv\s*=\s*(\d+)", mt)
            mem["iv"] = int(iv.group(1)) if iv else None
            held = re.search(r"\.heldItem\s*=\s*(ITEM_\w+)", mt)
            if held:
                mem["heldItem"] = held.group(1)
            mv = re.search(r"\.moves\s*=\s*\{([^}]*)\}", mt)
            if mv:
                mem["moves"] = [s.strip() for s in mv.group(1).split(",") if s.strip()]
            _, has_item, custom = shapes[shape]
            if has_item != ("heldItem" in mem) or custom != ("moves" in mem):
                raise Refused("%s (%s) member at line %d does not have its shape's fields" % (name, shape, line_of(t, m.start())))
            members.append(mem)
            i = k
        arrays[name] = {"shape": shape, "line": line_of(t, m.start()), "members": members}
    return arrays, raw_count


def check_party_count(arrays, raw_count):
    """GUARD (W5): every party array of the file was parsed. WHY: a shape the parser does not know would silently drop
    its trainers' parties; the count of `static const struct TrainerMon` arrays is read without knowing the shapes."""
    if len(arrays) != raw_count:
        raise Refused("parsed %d party arrays, trainer_parties.h declares %d (a party shape the parser does not know?)"
                      % (len(arrays), raw_count))


def parse_trainer_blocks(d):
    rel = "src/data/trainers.h"
    t = d.read(rel)
    out = {}
    for m in re.finditer(r"^[ \t]*\[(TRAINER_\w+)\]\s*=\s*\{", t, re.M):
        start = m.end() - 1
        b = t[start:balanced(t, start)]
        party = re.search(r"\.party\s*=\s*(NO_ITEM_DEFAULT_MOVES|NO_ITEM_CUSTOM_MOVES|ITEM_DEFAULT_MOVES|ITEM_CUSTOM_MOVES)"
                          r"\(\s*(\w+)\s*\)", b)
        size0 = re.search(r"\.partySize\s*=\s*0\b", b)
        dbl = re.search(r"\.doubleBattle\s*=\s*(TRUE|FALSE)", b)
        out[m.group(1)] = {
            "class": re.search(r"\.trainerClass\s*=\s*(TRAINER_CLASS_\w+)", b).group(1),
            "name": re.search(r'\.trainerName\s*=\s*_\("([^"]*)"\)', b).group(1),
            "double": bool(dbl) and dbl.group(1) == "TRUE",
            "double_line": line_of(t, start + dbl.start()) if dbl else None,
            "macro": party.group(1) if party else None,
            "array": party.group(2) if party else None,
            "empty": bool(size0) and not party,
            "line": line_of(t, m.start()),
        }
    return out


def check_parties(blocks, arrays, ids):
    """GUARD (W5): every trainer has a party of at least one mon, except TRAINER_NONE by name; every party macro names
    an array that exists and has the macro's shape; every opponents.h id has a block. WHY: an empty or mis-shaped
    party would be written as a trainer with nothing to fight, and nothing downstream could tell."""
    macro_shape = {v[0]: k for k, v in PARTY_SHAPES.items()}
    missing = sorted(set(ids) - set(blocks))
    if missing:
        raise Refused("opponents.h ids with no trainers.h block: %s" % missing[:5])
    for sym, b in blocks.items():
        if sym in EXEMPT_EMPTY_PARTY:
            if not b["empty"]:
                raise Refused("%s was expected to have the empty placeholder party (trainers.h .partySize = 0)" % sym)
            continue
        if b["array"] is None:
            raise Refused("%s has an empty party (only %s is exempt, by name)" % (sym, EXEMPT_EMPTY_PARTY))
        a = arrays.get(b["array"])
        if a is None:
            raise Refused("%s names the party array %s, which does not exist" % (sym, b["array"]))
        if macro_shape[b["macro"]] != a["shape"]:
            raise Refused("%s: macro %s but %s is a TrainerMon%s" % (sym, b["macro"], b["array"], a["shape"]))
        if not a["members"]:
            raise Refused("%s: party array %s has no members" % (sym, b["array"]))


def parse_rematches(d):
    t = d.read("src/battle_setup.c")
    out = {}
    for m in re.finditer(r"REMATCH\(\s*(TRAINER_\w+)\s*,\s*(TRAINER_\w+)\s*,\s*(TRAINER_\w+)\s*,\s*(TRAINER_\w+)\s*,"
                         r"\s*(TRAINER_\w+)\s*,\s*(MAP_\w+)\s*\)", t):
        first = m.group(1)
        for later in m.groups()[1:5]:
            if later != first:
                out[later] = first
    return out


def build_trainers(d):
    ids = trainer_ids(d)
    blocks = parse_trainer_blocks(d)
    arrays, raw = parse_party_arrays(d)
    check_party_count(arrays, raw)
    check_parties(blocks, arrays, ids)
    names = class_names(d)
    rem = parse_rematches(d)
    start = parse_defines(d.read("include/constants/flags.h")).get("TRAINER_FLAGS_START")
    if start is None:
        raise Refused("TRAINER_FLAGS_START not found in include/constants/flags.h")
    out = []
    for sym, tid in sorted(ids.items(), key=lambda kv: kv[1]):
        b = blocks[sym]
        rec = {"id": tid, "symbol": sym, "name": b["name"], "class": b["class"][len("TRAINER_CLASS_"):],
               "class_name": names.get(b["class"]), "double": b["double"], "flag": start + tid}
        if b["array"] is None:
            rec.update({"party_shape": None, "party": []})
        else:
            a = arrays[b["array"]]
            party = []
            for mem in a["members"]:
                p = {"species": mem["species"], "level": mem["lvl"]}
                if "heldItem" in mem:
                    p["held_item"] = None if mem["heldItem"] == "ITEM_NONE" else mem["heldItem"]
                if "moves" in mem:
                    p["moves"] = [mv for mv in mem["moves"] if mv != "MOVE_NONE"]
                party.append(p)
            rec.update({"party_shape": a["shape"], "party": party,
                        "party_ref": "src/data/trainer_parties.h:%d" % a["line"]})
        if sym in rem:
            rec["rematch_of"] = rem[sym]
        rec["ref"] = "src/data/trainers.h:%d" % b["line"]
        out.append(rec)
    return out, blocks


# ---------------------------------------------------------------- map scripts
def script_labels(text):
    """{label: {line, body: [(line number, code)]}}: a label is `Name::` or `Name:` alone on its line; an `@` comment
    is dropped from the code (a `.string` line is kept whole)."""
    labels, cur = {}, None
    for i, line in enumerate(text.split("\n"), 1):
        m = re.match(r"^([A-Za-z_]\w*)::?\s*(?:@.*)?$", line)
        if m:
            cur = m.group(1)
            labels[cur] = {"line": i, "body": []}
            continue
        if cur is not None:
            code = line if line.lstrip().startswith(".string") else line.split("@", 1)[0]
            labels[cur]["body"].append((i, code))
    return labels


def battle_line(code):
    """(macro, [args]) of a trainerbattle line, else None."""
    m = re.match(r"^\s*(trainerbattle\w*)\s+(.*)$", code)
    if not m:
        return None
    return m.group(1), [a.strip() for a in m.group(2).split(",")]


def battle_trainer(args):
    for a in args:
        if a.startswith("TRAINER_") and not a.startswith("TRAINER_BATTLE_"):
            return a
    return None


def reach(labels, start):
    """Every label reachable from `start` in the same file: any token of a body line that is a label of the file
    (goto, call, the conditional forms, a trainerbattle's post-defeat script). Bounded by MAX_LABELS."""
    seen, todo = set(), [start]
    while todo:
        lab = todo.pop()
        if lab in seen or lab not in labels:
            continue
        seen.add(lab)
        if len(seen) > MAX_LABELS:
            raise Refused("script closure from %s passed %d labels" % (start, MAX_LABELS))
        for _, code in labels[lab]["body"]:
            if code.lstrip().startswith(".string"):
                continue
            for tok in re.findall(r"[A-Za-z_]\w*", code):
                if tok in labels and tok not in seen:
                    todo.append(tok)
    return seen


def label_trainers(labels):
    out = {}
    for lab, v in labels.items():
        ids = []
        for _, code in v["body"]:
            bl = battle_line(code)
            if bl and battle_trainer(bl[1]):
                ids.append(battle_trainer(bl[1]))
        if ids:
            out[lab] = ids
    return out


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return v


def item_ball_scripts(d):
    t = d.read("data/scripts/item_ball_scripts.inc")
    return {m.group(1): m.group(2) for m in re.finditer(r"^(\w+)::\s*\n\s*finditem\s+(ITEM_\w+)", t, re.M)}


def map_folders(d):
    base = os.path.join(d.root, "data", "maps")
    return sorted(f for f in os.listdir(base) if os.path.isfile(os.path.join(base, f, "map.json")))


def build_maps(d):
    """Every map folder's record. Pass 1 joins each object and coord event to the battles its script reaches; a script
    label that is not in the map's own scripts.inc is found in the file that defines it (the Lavaridge gym's B1F
    trainers and Mt. Pyre 4F/5F keep their scripts in the neighbouring floor's file). Pass 2 lists, under the map that
    owns each scripts.inc, the battles of that file no event reached (source 'script'), so every trainerbattle line of
    every map script appears in maps.json exactly where the file puts it."""
    balls = item_ball_scripts(d)
    folders = map_folders(d)
    files = {}
    for folder in folders:
        rel = "data/maps/%s/scripts.inc" % folder
        if os.path.isfile(os.path.join(d.root, rel)):
            labels = script_labels(d.read(rel))
            files[rel] = (labels, label_trainers(labels))
    home = {}
    for rel, (labels, _) in files.items():
        for lab in labels:
            home.setdefault(lab, rel)
    covered = {rel: set() for rel in files}

    def joined(own, script):
        rel = own if own in files and script in files[own][0] else home.get(script)
        if rel is None:
            return []
        labels, direct = files[rel]
        ids = sorted({t for lab in reach(labels, script) for t in direct.get(lab, [])})
        covered[rel].update(ids)
        return ids

    out = []
    for folder in folders:
        j = json.loads(d.read("data/maps/%s/map.json" % folder))
        rec = {"id": j["id"], "name": j["name"], "region_map_section": j.get("region_map_section"),
               "map_type": j.get("map_type"), "requires_flash": j.get("requires_flash"),
               "allow_cycling": j.get("allow_cycling"), "allow_escaping": j.get("allow_escaping"),
               "allow_running": j.get("allow_running"),
               "connections": [{"dir": c["direction"], "map": c["map"], "offset": c["offset"]}
                               for c in (j.get("connections") or [])],
               "warps": [{"x": w["x"], "y": w["y"], "elevation": w["elevation"], "dest_map": w["dest_map"],
                          "dest_warp_id": _int(w["dest_warp_id"])} for w in (j.get("warp_events") or [])]}
        if j.get("shared_events_map"):
            rec["shared_events_map"] = j["shared_events_map"]
        script_owner = j.get("shared_scripts_map") or folder
        if j.get("shared_scripts_map"):
            rec["shared_scripts_map"] = j["shared_scripts_map"]
        srel = "data/maps/%s/scripts.inc" % script_owner
        trainers = []
        for n, o in enumerate(j.get("object_events") or [], 1):
            ids = joined(srel, o.get("script"))
            if ids or o.get("trainer_type", "TRAINER_TYPE_NONE") != "TRAINER_TYPE_NONE":
                trainers.append({"source": "object", "object": n, "script": o.get("script"),
                                 "trainer_type": o.get("trainer_type"), "sight": _int(o.get("trainer_sight_or_berry_tree_id")),
                                 "x": o["x"], "y": o["y"], "elevation": o.get("elevation"), "trainers": ids})
        for c in j.get("coord_events") or []:
            ids = joined(srel, c.get("script"))
            if ids:
                trainers.append({"source": "coord_event", "script": c.get("script"), "x": c["x"], "y": c["y"],
                                 "elevation": c.get("elevation"), "trainers": ids})
        rec["trainers"] = trainers
        rec["item_balls"] = [{"x": o["x"], "y": o["y"], "elevation": o.get("elevation"), "item": balls[o["script"]],
                              "flag": o.get("flag"), "script": o["script"]}
                             for o in (j.get("object_events") or [])
                             if o.get("graphics_id") == "OBJ_EVENT_GFX_ITEM_BALL" and o.get("script") in balls]
        rec["hidden_items"] = [{"x": b["x"], "y": b["y"], "elevation": b.get("elevation"), "item": b["item"],
                                "flag": b["flag"]} for b in (j.get("bg_events") or []) if b.get("type") == "hidden_item"]
        out.append(rec)
    for rec, folder in zip(out, folders):  # pass 2: the battles no event reached, under the file's own map
        rel = "data/maps/%s/scripts.inc" % folder
        if rel not in files:
            continue
        labels, direct = files[rel]
        for lab in sorted(direct, key=lambda k: labels[k]["line"]):
            left = sorted(set(direct[lab]) - covered[rel])
            if left:
                rec["trainers"].append({"source": "script", "label": lab, "trainers": left,
                                        "ref": "%s:%d" % (rel, labels[lab]["line"])})
                covered[rel].update(left)
    return out


# ---------------------------------------------------------------- field moves and badges
def field_move_table(d):
    """[{move, field_move, badge, flag, ref, rule_ref, move_ref, overworld_ref?}] for every field move the party menu
    gates by a badge: src/party_menu.c's enum (FIELD_MOVE_X ordinal i <= FIELD_MOVE_WATERFALL needs FLAG_BADGE01_GET + i,
    the rule at the `FlagGet(FLAG_BADGE01_GET + fieldMove)` line), the move from src/data/party_menu.h sFieldMoves, and
    for Surf, Waterfall and Dive the overworld FlagGet line of src/field_control_avatar.c."""
    pm = "src/party_menu.c"
    t = d.read(pm)
    em = re.search(r"enum\s*\{\s*(FIELD_MOVE_CUT\b.*?)\}", t, re.S)
    if not em:
        raise Refused("the FIELD_MOVE enum is not in src/party_menu.c")
    names = [re.match(r"\s*(FIELD_MOVE_\w+)", ln).group(1) for ln in em.group(1).split("\n")
             if re.match(r"\s*FIELD_MOVE_\w+", ln)]
    if "FIELD_MOVE_WATERFALL" not in names:
        raise Refused("FIELD_MOVE_WATERFALL is not in the enum")
    rule_ref = cite_line(d, pm, "FlagGet(FLAG_BADGE01_GET + fieldMove)")
    fm = d.read("src/data/party_menu.h")
    moves = {m.group(1): (m.group(2), line_of(fm, m.start()))
             for m in re.finditer(r"\[(FIELD_MOVE_\w+)\]\s*=\s*(MOVE_\w+)", fm)}
    enum_start = line_of(t, em.start(1))
    table = []
    for i, name in enumerate(names[:names.index("FIELD_MOVE_WATERFALL") + 1]):
        badge = "BADGE%02d" % (i + 1)
        row = {"move": moves[name][0][len("MOVE_"):], "field_move": name, "badge": badge,
               "flag": "FLAG_%s_GET" % badge, "ref": "%s:%d" % (pm, enum_start + i), "rule_ref": rule_ref,
               "move_ref": "src/data/party_menu.h:%d" % moves[name][1]}
        table.append(row)
    fca = "src/field_control_avatar.c"
    ft = d.read(fca)
    overworld = {"SURF": r"FlagGet\((FLAG_BADGE\d\d_GET)\)\s*==\s*TRUE\s*&&\s*PartyHasMonWithSurf",
                 "WATERFALL": r"FlagGet\((FLAG_BADGE\d\d_GET)\)\s*==\s*TRUE\s*&&\s*IsPlayerSurfingNorth",
                 "DIVE": r"FlagGet\((FLAG_BADGE\d\d_GET)\)\s*&&\s*TrySetDiveWarp\(\)\s*==\s*2"}
    for row in table:
        if row["move"] in overworld:
            m = re.search(overworld[row["move"]], ft)
            row["overworld_ref"] = "%s:%d" % (fca, line_of(ft, m.start())) if m else None
            row["_overworld_flag"] = m.group(1) if m else None
    check_field_moves(table)
    for row in table:
        row.pop("_overworld_flag", None)
    return table


def check_field_moves(table):
    """GUARD: where the overworld code gates a field move by a badge too, it is the party menu's badge. WHY: the spec
    names both sources; two readings that disagree mean the table no longer says what the game does."""
    for row in table:
        if "overworld_ref" in row and row.get("_overworld_flag") != row["flag"]:
            raise Refused("%s: the party menu says %s, field_control_avatar.c says %s" % (row["move"], row["flag"],
                                                                                          row.get("_overworld_flag")))


def map_scripts(d):
    out = {}
    for folder in map_folders(d):
        rel = "data/maps/%s/scripts.inc" % folder
        if os.path.isfile(os.path.join(d.root, rel)):
            out[rel] = d.read(rel)
    return out


def leader_badge(d, scripts, leader):
    """GUARD: the ONE badge a gym leader's defeat script sets: the post-defeat script named on the leader's (non-rematch)
    trainerbattle line, followed through the file's labels, must set exactly one FLAG_BADGEnn_GET."""
    for rel, text in scripts.items():
        labels = script_labels(text)
        for lab, v in labels.items():
            for n_battle, code in v["body"]:
                bl = battle_line(code)
                if not bl or battle_trainer(bl[1]) != leader or bl[0] in REMATCH_MACROS:
                    continue
                idx = EVENT_SCRIPT_ARG.get(bl[0])
                if idx is not None and len(bl[1]) > idx:
                    # the post-defeat script named on the line (trainerbattle_single/_double's event_script)
                    lines = [ln for l2 in reach(labels, bl[1][idx]) for ln in labels[l2]["body"]]
                else:
                    # no script named (trainerbattle_no_intro, Norman): the script goes on after the battle, in this
                    # label, and into the labels those lines name
                    after = [(n, c) for n, c in v["body"] if n > n_battle]
                    named = {tok for _, c in after for tok in re.findall(r"[A-Za-z_]\w*", c) if tok in labels}
                    lines = after + [ln for t0 in sorted(named) for l2 in reach(labels, t0) for ln in labels[l2]["body"]]
                found = {}
                for n, c2 in lines:
                    m = re.match(r"^\s*setflag\s+(FLAG_BADGE(\d\d)_GET)\s*$", c2)
                    if m:
                        found.setdefault(m.group(1), "%s:%d" % (rel, n))
                if len(found) != 1:
                    raise Refused("%s: its defeat script sets %d badges %s, not one" % (leader, len(found), sorted(found)))
                flag, ref = next(iter(found.items()))
                return {"id": flag[len("FLAG_"):-len("_GET")], "flag": flag, "ref": ref}
    raise Refused("%s: no map script battles this gym leader" % leader)


# ---------------------------------------------------------------- bosses
def fight_of(sym, rematch_firsts):
    """The fight id that groups a boss's variants: a rival's gender and starter variants share one
    (TRAINER_MAY_ROUTE_103_MUDKIP -> RIVAL_ROUTE_103), a trainer with rematches drops its _1 (TRAINER_ROXANNE_1 ->
    ROXANNE), any other is its symbol without TRAINER_."""
    m = re.match(r"^TRAINER_(?:BRENDAN|MAY)_(.+)_(?:MUDKIP|TREECKO|TORCHIC)$", sym)
    if m:
        return "RIVAL_" + m.group(1)
    name = sym[len("TRAINER_"):]
    if sym in rematch_firsts and name.endswith("_1"):
        return name[:-2]
    return name


def default_moveset(level_up, level):
    """The game's default moveset (src/pokemon.c GiveBoxMonInitialMoveset): walk the level-up learnset in order up to
    the level; a known move is skipped; a fifth pushes out the first."""
    moves = []
    for row in level_up:
        if row["level"] > level:
            break
        if row["move"] in moves:
            continue
        if len(moves) == 4:
            moves.pop(0)
        moves.append(row["move"])
    return moves


def load_json(path):
    with open(path, "rb") as f:
        raw = f.read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def build_bosses(d, trainers, blocks, maps, scripts, seasoned_dir):
    species, sp_sha = load_json(os.path.join(seasoned_dir, "species.json"))
    learn, ln_sha = load_json(os.path.join(seasoned_dir, "learnsets.json"))
    types = {s["symbol"]: s["types"] for s in species["species"]}
    levelup = {s["symbol"]: s["level_up"] for s in learn["species"]}
    initial = cite_line(d, "src/pokemon.c", "void GiveBoxMonInitialMoveset(struct BoxPokemon *boxMon)")
    battled = {}
    for mp in maps:
        for t in mp["trainers"]:
            for tid in t["trainers"]:
                battled.setdefault(tid, set()).add(mp["id"])
    by_sym = {t["symbol"]: t for t in trainers}
    rematches = {}
    for t in trainers:
        if "rematch_of" in t:
            rematches.setdefault(t["rematch_of"], []).append(t["symbol"])
    out, excluded = [], []
    for t in trainers:
        role = ROLE_OF_CLASS.get("TRAINER_CLASS_" + t["class"])
        if role is None or "rematch_of" in t:
            continue
        if t["symbol"] not in battled:
            excluded.append(t["symbol"])
            continue
        party = []
        for slot, p in enumerate(t["party"], 1):
            if p["species"] not in types or p["species"] not in levelup:
                raise Refused("%s: species %s is not in KB1" % (t["symbol"], p["species"]))
            row = {"species": p["species"], "level": p["level"]}
            if "held_item" in p:
                row["held_item"] = p["held_item"]
            if "moves" in p:
                row["moves"], row["moves_source"] = p["moves"], "custom (%s)" % t["party_ref"]
            else:
                row["moves"] = default_moveset(levelup[p["species"]], p["level"])
                row["moves_source"] = ("default moveset, derived_from KB1 learnsets.json level_up by the rule of %s"
                                       % initial)
            row["types"] = types[p["species"]]
            party.append(row)
        notes = []
        if t["double"]:
            notes.append("a double battle: two of its mons are out at once (src/data/trainers.h:%d doubleBattle = TRUE)"
                         % blocks[t["symbol"]]["double_line"])
        for slot, row in enumerate(party, 1):
            stall = [m[len("MOVE_"):] for m in row["moves"] if m in STALL_MOVES]
            if len(stall) >= 2:
                notes.append("%s (slot %d) carries %s: a stall set (its moves, %s)"
                             % (row["species"][len("SPECIES_"):], slot, " + ".join(stall), row["moves_source"]))
        rec = {"fight": fight_of(t["symbol"], rematches), "id": t["symbol"], "name": t["name"], "role": role,
               "order": None, "double": t["double"], "party": party, "rematches": sorted(rematches.get(t["symbol"], [])),
               "battled_on": sorted(battled[t["symbol"]]), "types_derived_from": "KB1 species.json (types)",
               "notes": notes, "measured": None, "ref": t["ref"]}
        if role == "gym_leader":
            rec["badge"] = leader_badge(d, scripts, t["symbol"])
        out.append(rec)
    return out, sorted(excluded), {"species.json": sp_sha, "learnsets.json": ln_sha}


# ---------------------------------------------------------------- campaign (L1)
def check_milestone_ids(entries, milestones):
    """GUARD (W4): the skeleton's first entries are milestones.json's milestones, same ids, same order, same chapters."""
    want = [(m["id"], m["chapter"]) for m in milestones["milestones"]]
    got = [(e["id"], e["chapter"]) for e in entries[:len(want)]]
    if got != want:
        bad = [(g, w) for g, w in zip(got, want) if g != w] or [("(too few entries)", want[len(got):][:1])]
        raise Refused("the skeleton's first entries are not milestones.json's milestones: %s" % bad[:3])


def check_area_maps(entries, map_ids):
    """GUARD (W4): every area map of every entry is a map of maps.json; names the first one that is not."""
    for e in entries:
        for name in e["area"]:
            if "MAP_" + name not in map_ids:
                raise Refused("entry %s: area map %s is not in maps.json" % (e["id"], name))


def check_bosses(entries, fights, item_syms):
    """GUARD: a skeleton boss is a bosses.json fight; a key item is an items.h symbol."""
    for e in entries:
        if e.get("boss") is not None and e["boss"] not in fights:
            raise Refused("entry %s: boss %s is no bosses.json fight" % (e["id"], e["boss"]))
        for k in (e.get("needs") or {}).get("key_items", []):
            if k["item"] not in item_syms:
                raise Refused("entry %s: key item %s is not in include/constants/items.h" % (e["id"], k["item"]))


def check_badge_order(entries, badge_award):
    """GUARD (W4b): every badge an entry needs (needs.badges and needs.field_moves[].badge) is awarded by the boss of an
    EARLIER entry. WHY: the order is hand-authored; this is its only test past the 20 milestones."""
    awarded_at = {}
    for e in entries:
        b = badge_award.get(e.get("boss"))
        if b and b not in awarded_at:
            awarded_at[b] = e
    for e in entries:
        need = set(e["needs"]["badges"]) | {fm["badge"] for fm in e["needs"]["field_moves"]}
        for b in sorted(need):
            giver = awarded_at.get(b)
            if giver is None:
                raise Refused("entry %s needs %s, which no entry's boss awards" % (e["id"], b))
            if giver["order"] >= e["order"]:
                raise Refused("entry %s (order %d) needs %s, awarded by entry %s (order %d), which is not earlier"
                              % (e["id"], e["order"], b, giver["id"], giver["order"]))


def build_campaign(d, skeleton, milestones, maps, bosses, trainers, fm_table):
    entries = skeleton["entries"]
    check_milestone_ids(entries, milestones)
    map_ids = {m["id"] for m in maps}
    check_area_maps(entries, map_ids)
    fights = {}
    for b in bosses:
        fights.setdefault(b["fight"], []).append(b)
    items_text = d.read("include/constants/items.h")  # an enum on the pinned decomp, defines on older ones
    items = dict(parse_enum_blocks(items_text), **parse_defines(items_text))
    check_bosses(entries, fights, {k for k in items if k.startswith("ITEM_")})
    fm_by_move = {r["move"]: r for r in fm_table}
    badge_award = {f: v[0]["badge"]["id"] for f, v in fights.items() if "badge" in v[0]}
    by_sym = {t["symbol"]: t for t in trainers}
    out = []
    for k, e in enumerate(entries, 1):
        sk = e.get("needs") or {}
        field_moves = []
        for fm in sk.get("field_moves", []):
            row = fm_by_move.get(fm["move"])
            if row is None:
                raise Refused("entry %s: %s is not a badge-gated field move" % (e["id"], fm["move"]))
            field_moves.append({"move": fm["move"], "badge": row["badge"],
                                "ref": row.get("overworld_ref") or row["ref"], "rule_ref": row["rule_ref"],
                                "need_basis": fm["basis"]})
        badge_refs = {}
        for b in sk.get("badges", []):
            badge_refs.setdefault(b["badge"], []).append(cite_line(d, b["file"], b["needle"]))
        for fm in field_moves:
            badge_refs.setdefault(fm["badge"], []).append(fm["ref"])
        key_items = [{"item": ki["item"], "ref": cite_line(d, ki["file"], ki["needle"])} for ki in sk.get("key_items", [])]
        variants = fights.get(e.get("boss"), [])
        battle = e.get("battle")
        if battle:
            double = bool(battle["double_battle"])
            party_min = battle["party_min"]
            party_basis = "%s; %s (%s)" % (battle["kind"], battle["basis"], cite_line(d, battle["file"], battle["needle"]))
        elif any(v["double"] for v in variants):
            dv = next(v for v in variants if v["double"])
            double, party_min = True, 2
            party_basis = "decomp: %s has doubleBattle = TRUE (its block, %s)" % (dv["id"], by_sym[dv["id"]]["ref"])
        else:
            double, party_min = False, 1
            party_basis = "a single battle (or none): one able mon is enough to start it"
        ahead = next((x for x in entries[k - 1:] if x.get("boss")), None)
        ahead_variants = fights.get(ahead["boss"], []) if ahead else []
        types_ahead = sorted({ty for v in ahead_variants for p in v["party"] for ty in p["types"]})
        # the level band of the boss ahead (this entry's own, or the next one's): a map's other trainers are not used,
        # because a map is often visited long before its trainers are fought (Petalburg's gym in chapter 2)
        levels = [p["level"] for v in ahead_variants for p in v["party"]]
        band = {"low": min(levels), "high": max(levels),
                "basis": "decomp boss top level (bosses.json %s%s)" % (ahead["boss"], "" if variants else ", the boss ahead")} \
            if levels else None
        out.append({"id": e["id"], "chapter": e["chapter"], "order": k, "area": list(e["area"]), "boss": e.get("boss"),
                    "needs": {"field_moves": field_moves, "badges": sorted(badge_refs), "badge_refs": badge_refs,
                              "key_items": key_items, "party_min": party_min, "party_min_basis": party_basis,
                              "double_battle": double, "types_ahead": types_ahead,
                              "types_ahead_of": ahead["boss"] if ahead else None, "level_band": band,
                              "money_checkpoint": None},
                    "measured": None})
    check_badge_order(out, badge_award)
    return out


# ---------------------------------------------------------------- run
def header(d, kind, files, inputs=None, also=None):
    """The provenance block: the pinned SHA and the sha256 of each decomp file THIS output's stage read (a later stage
    that also leans on an earlier output's files says so in `_also_uses`, so 518 map files are listed once)."""
    h = {"_source": "pret/pokeemerald@" + d.sha,
         "_files": {p: d.used[p] for p in sorted(files)},
         "_kind": kind, "_made_by": MADE_BY, "_slice": "spec S3-4 slice 1 (KB2)",
         "_not_in_this_slice": NOT_IN_SLICE, "_reader": READER}
    if also:
        h["_also_uses"] = also
    if inputs:
        h["_inputs"] = inputs
    return h


def build_all(d, skeleton_path=SKELETON_DEFAULT, seasoned_dir=SEASONED_DEFAULT, milestones_path=MILESTONES_DEFAULT):
    """{file name: object} for the four outputs; every guard runs; nothing is written."""
    stage = {}
    trainers, blocks = build_trainers(d)
    stage["trainers"] = set(d.used)
    maps = build_maps(d)
    stage["maps"] = set(d.used) - stage["trainers"]
    scripts = map_scripts(d)
    bosses, excluded, kb1 = build_bosses(d, trainers, blocks, maps, scripts, seasoned_dir)
    stage["bosses"] = set(d.used) - stage["trainers"] - stage["maps"]
    fm_table = field_move_table(d)
    skeleton, sk_sha = load_json(skeleton_path)
    milestones, ms_sha = load_json(milestones_path)
    campaign = build_campaign(d, skeleton, milestones, maps, bosses, trainers, fm_table)
    stage["campaign"] = set(d.used) - stage["trainers"] - stage["maps"] - stage["bosses"]
    order = {}
    for e in campaign:
        if e["boss"]:
            order.setdefault(e["boss"], e["order"])
    for b in bosses:
        b["order"] = order.get(b["fight"])
    kind ="static game knowledge (USER RULING 40)"
    out = {
        "trainers.json": dict(header(d, kind, stage["trainers"]), _withheld=list(WITHHELD_FIELDS),
                              _withheld_why="USER RULING 44 (2026-10-21): exact stats (IVs) and AI flags stay withheld; "
                                            "heldItem is allowed (as held_item); moves and levels are kept",
                              _notes={"flag": "the trainer's defeat flag NUMBER (TRAINER_FLAGS_START + id): a number, "
                                              "not a name",
                                      "party_shape": "the trainer_parties.h struct: a DefaultMoves party has no `moves` "
                                                     "(the game gives each mon its default level-up moveset)",
                                      "rematch_of": "from gRematchTable (src/battle_setup.c)",
                                      "bag_items": "the trainer's bag (`.items`) is not extracted (not in the spec's "
                                                   "field list)",
                                      "exempt_empty_party": "%s has no party (trainers.h .partySize = 0), by name"
                                                            % list(EXEMPT_EMPTY_PARTY)},
                              count=len(trainers), trainers=trainers),
        "bosses.json": dict(header(d, kind, stage["bosses"], {"kb1": kb1, "campaign_skeleton.json": sk_sha},
                                   also="trainers.json and maps.json (their _files: parties, the map scripts' battles)"),
                            _measured=MEASURED_NULL,
                            _excluded={"ids": excluded, "why": "a boss-class trainer that no map script battles"},
                            _notes={"fight": "groups a boss's variants (a rival's gender and starter); campaign.json's "
                                             "boss names a fight", "order": "the campaign skeleton's order of the "
                                             "fight's first entry (null: not in the campaign)",
                                    "badge": "read from the gym leader's defeat script (setflag FLAG_BADGEnn_GET)"},
                            count=len(bosses), bosses=bosses),
        "maps.json": dict(header(d, kind, stage["maps"]),
                          _notes={"trainers": "objects and coord events joined to the trainerbattle lines reachable "
                                              "from their script label (goto/call/branch targets in the label's file, "
                                              "the map's own scripts.inc or the one that defines the label); source "
                                              "'script' lists the battles of the map's file that no event reaches",
                                  "item_balls": "object events whose script is a finditem label of "
                                                "data/scripts/item_ball_scripts.inc",
                                  "coordinates": "kept (USER RULING 45): tiles, sight ranges, doors"},
                          count=len(maps), maps=maps),
    }
    out["campaign.json"] = dict(header(d, "the campaign manifest (L1): skeleton order + decomp-derived needs",
                                       stage["campaign"], {"campaign_skeleton.json": sk_sha, "milestones.json": ms_sha},
                                       also="bosses.json and maps.json (their _files)"),
                                _measured=MEASURED_NULL, field_move_badges=fm_table, count=len(campaign), entries=campaign)
    return out


def write_outputs(out_dir, objs):
    """The ONE door to disk: W1 and W6 run here on every output, so no path writes a file they have not seen."""
    os.makedirs(out_dir, exist_ok=True)
    for name, obj in objs.items():
        refuse_withheld(name, obj)
        if name == "campaign.json":
            refuse_route_keys(obj)
    for name, obj in objs.items():
        write_json(os.path.join(out_dir, name), obj)


def run(decomp_root, out_dir=OUT_DEFAULT, **kw):
    d = Decomp(decomp_root)
    objs = build_all(d, **kw)
    write_outputs(out_dir, objs)
    return objs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--decomp")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--skeleton", default=SKELETON_DEFAULT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    try:
        root = resolve_decomp(a.decomp)
        if a.check:
            with tempfile.TemporaryDirectory() as tmp:
                run(root, tmp, skeleton_path=a.skeleton)
                bad = [fn for fn in OUTPUTS if not os.path.exists(os.path.join(a.out, fn))
                       or open(os.path.join(a.out, fn), "rb").read() != open(os.path.join(tmp, fn), "rb").read()]
            if bad:
                print("[KB2] CHECK FAILED, differ/missing: %s (regenerate: py -3.12 ai_player/gates/extract_world.py)"
                      % ", ".join(bad))
                return 1
            print("[KB2] CHECK OK: %d files identical to a fresh extraction" % len(OUTPUTS))
            return 0
        objs = run(root, a.out, skeleton_path=a.skeleton)
        print("[KB2] wrote %s: %s" % (a.out, ", ".join("%s (%d)" % (k, v["count"]) for k, v in objs.items())))
        return 0
    except Refused as exc:
        print("[KB2] REFUSED:", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
