#!/usr/bin/env python3
"""The INDEPENDENT verifier of KB2 slice 1 (spec S3-4): trainers.json, bosses.json, maps.json, campaign.json.

    py -3.12 ai_player/gates/verify_world.py                  # every record, against the pinned decomp
    py -3.12 ai_player/gates/verify_world.py --seed 7         # a fixed-seed sample: 60 trainers, 20 maps, 20 item records
                                                              #   (+ every boss, the field-move table, the campaign,
                                                              #   every citation of the four files)
    py -3.12 ai_player/gates/verify_world.py --plant          # W2: four planted errors must be reported, and only them
    py -3.12 ai_player/gates/verify_world.py --selftest       # the plant arm, its control, and the W1 / W6 scans' arms
    exit 0 = clean (with --plant: exactly the four plants), 1 = a mismatch, 2 = refused (no pinned clone)

WHY A SECOND READING (spec S3-4, the KB1 pattern): an extractor that misreads the decomp writes its misreading with
full confidence, and re-running it only repeats it. This file NEVER imports extract_world.py. It re-derives every
checked value by regex over the RAW decomp text, by a different route where one exists:
  * trainers: the block up to its closing `    },` line (not brace matching); the party array up to `\\n};`; the
    default moveset recomputed from src/data/pokemon/level_up_learnsets.h (the extractor uses KB1's learnsets.json);
    types from src/data/pokemon/species_info.h (the extractor uses KB1's species.json);
  * a gym leader's badge: the ONE `setflag FLAG_BADGEnn_GET` in the scripts.inc that holds the leader's non-rematch
    battle (the extractor follows the post-defeat script's labels);
  * the field-move badges: the `// FLAG_BADGEnn_GET` comments of src/party_menu.c's enum (the extractor counts the
    enum's ordinals and checks them against field_control_avatar.c);
  * maps: regex over the raw map.json text (the extractor json-loads it); a trainer object's or coord event's own
    script label only, looked up in the map scripts AND the shared library data/scripts/*.inc (the extractor follows
    the label's jumps), so the verifier's ids must be a SUBSET of the extractor's join; each map's item balls exactly;
    and every trainer a map's scripts battle, counted per map: the battles of the labels its events name must be on
    that map, and the battles of its own scripts.inc must be on it or on a map whose events use that file;
  * the campaign: the skeleton's ids, areas, bosses and needs (so a DROPPED need is reported), milestones.json's ids,
    W4b re-derived from the raw badges; each entry's `area_bosses` re-read from its area maps' trainerbattle lines
    (every boss referenced by an area's scripts must be listed); its `fights` re-derived (the skeleton's boss plus the
    other opponent of a TRAINER_BATTLE_SET_TRAINER_A/B multi battle in the same scripts.inc); its level band (low AND
    high) and types from the raw parties of the fights ahead; every boss's `order` and `entry` from those fights;
  * EVERY CITATION: each `file:line` in any string of the four files must be covered by a rule of CITATION_RULES and
    its line, read from the pinned clone, must CONTAIN the token the citation is evidence for: a field move's line
    names the move and its badge flag; a badge line names the badge flag; a trainer's or boss's line names its symbol
    (`[TRAINER_X]`); a party line names the party array the trainer's block points to (the trainer symbol is not on
    that line); a key item's line names the item; Norman's gate line sits in the same label as its badge's setflag. A
    citation moved to an unrelated line (`src/party_menu.c:2`, an #include) is a mismatch, and so is a citation in a
    place no rule covers.
W1 (USER RULING 44): every JSON file under ai_player/knowledge/ (recursively) is scanned for a withheld key (iv,
aiFlags, any spelling). W6: campaign.json may hold no key named x, y, route, path, steps or coords.
A mismatch prints one `MISMATCH <kind> <key>: <what>` line per record (every problem of a record on its one line), so
`--plant` can require exactly its four.
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
KNOWLEDGE = os.path.join(REPO, "ai_player", "knowledge")
DATA_DEFAULT = os.path.join(KNOWLEDGE, "world")
MILESTONES = os.path.join(KNOWLEDGE, "milestones.json")
SKELETON = os.path.join(HERE, "campaign_skeleton.json")
PIN_FILE = os.path.join(REPO, "tools", "decomp.pin")
DEFAULT_DECOMP = os.path.normpath(os.path.join(REPO, "..", "_decomp", "pokeemerald"))
DEFAULT_SEED = 20261021
SAMPLE = {"trainers": 60, "maps": 20, "items": 20}
#: the verifier's OWN copy of USER RULING 44's list (test_kb2 checks it equals the extractor's)
WITHHELD = ("iv", "aiFlags")
_WITHHELD_NORMS = {"iv", "ivs", "aiflags"}
ROUTE_KEYS = ("x", "y", "route", "path", "steps", "coords")
BOSS_CLASSES = {"LEADER": "gym_leader", "ELITE_FOUR": "elite_four", "CHAMPION": "champion", "RIVAL": "rival",
                "AQUA_LEADER": "team_leader", "MAGMA_LEADER": "team_leader", "AQUA_ADMIN": "team_admin",
                "MAGMA_ADMIN": "team_admin"}
BATTLE_RE = r"^\s*trainerbattle\w*\s+(?:TRAINER_BATTLE_\w+,\s*)?(TRAINER_\w+)"
CITE_RE = re.compile(r"((?:src|data|include|asm|constants)/[\w./-]+?\.(?:c|h|inc|s|json)):(\d+)")


class Refused(Exception):
    pass


def pinned_root(explicit=None):
    """The decomp root; its HEAD must EQUAL tools/decomp.pin (a clone at another commit is refused, not only a folder
    that is no git repository)."""
    root = explicit or os.environ.get("POKEBOT_DECOMP") or DEFAULT_DECOMP
    with open(PIN_FILE, encoding="utf-8") as f:
        pin = f.read().strip()
    r = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True)
    if r.returncode != 0 or r.stdout.strip() != pin:
        raise Refused("no clone at the pinned %s under %s (got %r)" % (pin, root, r.stdout.strip() or None))
    return root


# ---------------------------------------------------------------- the raw decomp, read once per root
_RAW = {}


def label_split(text):
    """{label: body text} of a script file (first definition wins)."""
    out = {}
    parts = re.split(r"^([A-Za-z_]\w*)::?[ \t]*$", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        out.setdefault(parts[i], parts[i + 1])
    return out


def raw(root):
    if root in _RAW:
        return _RAW[root]

    def rd(rel):
        with open(os.path.join(root, rel), "rb") as f:
            return f.read().decode("utf-8").replace("\r\n", "\n")
    r = {"rd": rd, "lines": {}}
    r["ids"] = {m.group(1): int(m.group(2)) for m in
                re.finditer(r"^#define (TRAINER_\w+)\s+(\d+)\s*$", rd("include/constants/opponents.h"), re.M)}
    th = rd("src/data/trainers.h")
    r["blocks"] = {m.group(1): m.group(2) for m in re.finditer(r"\[(TRAINER_\w+)\] =\s*\n\s*\{(.*?)\n    \},", th, re.S)}
    tp = rd("src/data/trainer_parties.h")
    r["arrays"] = {m.group(2): (m.group(1), m.group(3)) for m in
                   re.finditer(r"static const struct TrainerMon(\w+) (\w+)\[\] = \{(.*?)\n\};", tp, re.S)}
    r["n_arrays"] = tp.count("static const struct TrainerMon")
    r["rematch"] = {}
    for line in rd("src/battle_setup.c").split("\n"):
        m = re.search(r"= REMATCH\(([^)]*)\)", line)
        if m:
            ids = [a.strip() for a in m.group(1).split(",")][:5]
            for t in ids[1:]:
                if t != ids[0]:
                    r["rematch"][t] = ids[0]
    fl = re.search(r"#define TRAINER_FLAGS_START\s+(0x[0-9A-Fa-f]+|\d+)", rd("include/constants/flags.h")).group(1)
    r["flag_start"] = int(fl, 0)
    r["class_names"] = dict(re.findall(r'\[(TRAINER_CLASS_\w+)\] = _\("([^"]*)"\)', rd("src/data/text/trainer_class_names.h")))
    si = rd("src/data/pokemon/species_info.h")
    r["types"] = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\] =\s*\n\s*\{(.*?)\n    \},", si, re.S):
        tm = re.search(r"\.types = \{\s*TYPE_(\w+),\s*TYPE_(\w+)\s*\}", m.group(2))
        if tm:
            r["types"][m.group(1)] = list(dict.fromkeys([tm.group(1), tm.group(2)]))
    ptr = dict(re.findall(r"\[(SPECIES_\w+)\] = (s\w+LevelUpLearnset)", rd("src/data/pokemon/level_up_learnset_pointers.h")))
    lu = rd("src/data/pokemon/level_up_learnsets.h")
    sets = {m.group(1): [(int(a), b) for a, b in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+),\s*(MOVE_\w+)\)", m.group(2))]
            for m in re.finditer(r"static const u16 (s\w+LevelUpLearnset)\[\] = \{(.*?)\};", lu, re.S)}
    r["levelup"] = {sp: sets[name] for sp, name in ptr.items() if name in sets}
    maps_dir = os.path.join(root, "data", "maps")
    r["maps"], r["scripts"] = {}, {}
    for folder in sorted(os.listdir(maps_dir)):
        if os.path.isfile(os.path.join(maps_dir, folder, "map.json")):
            text = rd("data/maps/%s/map.json" % folder)
            r["maps"][re.search(r'"id": "(MAP_\w+)"', text).group(1)] = (folder, text)
        if os.path.isfile(os.path.join(maps_dir, folder, "scripts.inc")):
            r["scripts"]["data/maps/%s/scripts.inc" % folder] = rd("data/maps/%s/scripts.inc" % folder)
    lib_dir = os.path.join(root, "data", "scripts")
    r["library"] = {"data/scripts/%s" % f: rd("data/scripts/%s" % f) for f in sorted(os.listdir(lib_dir))
                    if f.endswith(".inc")}
    r["label_body"], r["label_file"] = {}, {}
    for rel, text in list(r["scripts"].items()) + list(r["library"].items()):  # a map's own label wins
        for lab, body in label_split(text).items():
            r["label_body"].setdefault(lab, body)
            r["label_file"].setdefault(lab, rel)
    r["battles"] = {}  # trainer -> [(rel, macro)] of every trainerbattle line in a map script
    r["multi"] = {}    # rel -> {"A": [trainers], "B": [trainers]} of the multi-battle lines
    for rel, text in r["scripts"].items():
        for m in re.finditer(r"^\s*(trainerbattle\w*)\s+(?:TRAINER_BATTLE_\w+,\s*)?(TRAINER_\w+)", text, re.M):
            r["battles"].setdefault(m.group(2), []).append((rel, m.group(1)))
        for ab, tid in re.findall(r"^\s*trainerbattle\s+TRAINER_BATTLE_SET_TRAINER_([AB]),\s*(TRAINER_\w+)", text, re.M):
            r["multi"].setdefault(rel, {"A": [], "B": []})[ab].append(tid)
    r["events"], r["event_battles"] = {}, {}
    for mid, (folder, text) in r["maps"].items():
        evs = [("object", o) for o in objects_of(text, "object_events")] + \
              [("coord_event", o) for o in objects_of(text, "coord_events")]
        r["events"][mid] = evs
        r["event_battles"][mid] = set()
        for _, o in evs:
            r["event_battles"][mid] |= direct_battles(r, jfield(o, "script"))
    ib = rd("data/scripts/item_ball_scripts.inc")
    r["balls"] = dict(re.findall(r"^(\w+)::\n\s*finditem (ITEM_\w+)", ib, re.M))
    _RAW[root] = r
    return r


def direct_battles(r, label):
    """The trainers on the trainerbattle lines of the label's OWN body (no jumps followed)."""
    return set(re.findall(BATTLE_RE, r["label_body"].get(label or "", ""), re.M))


def objects_of(text, section):
    m = re.search(r'"%s": \[(?:\]|(.*?)\n  \])' % section, text, re.S)  # an empty `[]` must not run on into the next list
    return re.findall(r"\{[^{}]*\}", m.group(1)) if m and m.group(1) else []


def jfield(block, key):
    m = re.search(r'"%s": ("([^"]*)"|-?\d+|true|false|null)' % key, block)
    if not m:
        return None
    v = m.group(1)
    if v.startswith('"'):
        return m.group(2)
    return {"true": True, "false": False, "null": None}.get(v, int(v) if re.fullmatch(r"-?\d+", v) else v)


def as_int(v):
    """'3' -> 3; a symbolic warp id (WARP_ID_DYNAMIC, WARP_ID_SECRET_BASE) stays a string."""
    return int(v) if isinstance(v, str) and re.fullmatch(r"-?\d+", v) else v


def party_array(r, sym):
    pm = re.search(r"\.party = (\w+)\((\w+)\)", r["blocks"].get(sym, ""))
    return pm.group(2) if pm else None


def raw_party(r, sym):
    arr = party_array(r, sym)
    if arr is None:
        return None, []
    shape, body = r["arrays"][arr]
    out = []
    for mt in re.findall(r"\{\s*(\.iv.*?)\n\s*\}", body, re.S):
        mem = {"species": re.search(r"\.species = (SPECIES_\w+)", mt).group(1),
               "level": int(re.search(r"\.lvl = (\d+)", mt).group(1))}
        h = re.search(r"\.heldItem = (ITEM_\w+)", mt)
        if h:
            mem["held_item"] = None if h.group(1) == "ITEM_NONE" else h.group(1)
        mv = re.search(r"\.moves = \{([^}]*)\}", mt)
        if mv:
            mem["moves"] = [x.strip() for x in mv.group(1).split(",") if x.strip() and x.strip() != "MOVE_NONE"]
        out.append(mem)
    return shape, out


def raw_default_moves(r, species, level):
    known = []
    for lv, mv in r["levelup"][species]:
        if lv > level:
            break
        if mv not in known:
            known = (known + [mv])[-4:]
    return known


# ---------------------------------------------------------------- the checks
class Report:
    """Mismatches grouped by record: every problem of one (kind, key) is joined onto that record's ONE line."""

    def __init__(self):
        self.bad = {}
        self.counts = {}

    def mismatch(self, kind, key, what):
        self.bad.setdefault((kind, key), []).append(what)

    @property
    def lines(self):
        return ["MISMATCH %s %s: %s" % (kind, key, "; ".join(whats)) for (kind, key), whats in self.bad.items()]

    def seen(self, kind, n=1):
        self.counts[kind] = self.counts.get(kind, 0) + n


def check_trainer(r, rec, rep):
    sym = rec["symbol"]
    b = r["blocks"].get(sym)
    if b is None:
        rep.mismatch("trainer", sym, "no trainers.h block")
        return
    bad = []
    cls = re.search(r"\.trainerClass = TRAINER_CLASS_(\w+)", b).group(1)
    want = {"id": r["ids"].get(sym), "name": re.search(r'\.trainerName = _\("([^"]*)"\)', b).group(1), "class": cls,
            "class_name": r["class_names"].get("TRAINER_CLASS_" + cls),
            "double": re.search(r"\.doubleBattle = (\w+)", b).group(1) == "TRUE",
            "flag": r["flag_start"] + r["ids"].get(sym, -9999), "rematch_of": r["rematch"].get(sym)}
    for k, v in want.items():
        if rec.get(k) != v:
            bad.append("%s %r != decomp %r" % (k, rec.get(k), v))
    shape, party = raw_party(r, sym)
    if rec.get("party_shape") != shape:
        bad.append("party_shape %r != decomp %r" % (rec.get("party_shape"), shape))
    if rec.get("party") != party:
        bad.append("party differs from trainer_parties.h")
    if bad:
        rep.mismatch("trainer", sym, "; ".join(bad))
    rep.seen("trainers")


def file_users(r):
    """{script file: {map ids whose events name a label of that file}}: who may carry a file's battles."""
    out = {}
    for mid, evs in r["events"].items():
        for _, o in evs:
            rel = r["label_file"].get(jfield(o, "script") or "")
            if rel:
                out.setdefault(rel, set()).add(mid)
    return out


def check_map(r, rec, rep, maps_by_id=None, users=None):
    mid = rec["id"]
    if mid not in r["maps"]:
        rep.mismatch("map", mid, "no such map.json")
        return
    folder, text = r["maps"][mid]
    bad = []
    for k in ("region_map_section", "map_type", "requires_flash", "allow_cycling", "allow_escaping", "allow_running"):
        if rec.get(k) != jfield(text, k):
            bad.append("%s %r != %r" % (k, rec.get(k), jfield(text, k)))
    if rec.get("name") != folder:
        bad.append("name %r != folder %r" % (rec.get("name"), folder))
    conns = [{"dir": d, "map": m, "offset": int(o)} for m, o, d in
             re.findall(r'\{\s*"map": "(MAP_\w+)",\s*"offset": (-?\d+),\s*"direction": "(\w+)"\s*\}', text)]
    if rec.get("connections") != conns:
        bad.append("connections %s != %s" % (rec.get("connections"), conns))
    warps = [{"x": jfield(w, "x"), "y": jfield(w, "y"), "elevation": jfield(w, "elevation"),
              "dest_map": jfield(w, "dest_map"), "dest_warp_id": as_int(jfield(w, "dest_warp_id"))}
             for w in objects_of(text, "warp_events")]
    if rec.get("warps") != warps:
        bad.append("warps differ")
    hidden = [{"x": jfield(o, "x"), "y": jfield(o, "y"), "elevation": jfield(o, "elevation"), "item": jfield(o, "item"),
               "flag": jfield(o, "flag")} for o in objects_of(text, "bg_events") if jfield(o, "type") == "hidden_item"]
    if rec.get("hidden_items") != hidden:
        bad.append("hidden_items differ")
    balls = [rec_ for m_, kind, rec_ in map_items(r, mid) if kind == "ball"]
    if rec.get("item_balls") != balls:  # EXACT: an invented or a dropped item ball is reported
        bad.append("item_balls differ")
    by_ev = {(t["source"], t.get("script"), t.get("x"), t.get("y")): t for t in rec.get("trainers", [])}
    for kind, o in r["events"][mid]:
        script, ttype = jfield(o, "script"), jfield(o, "trainer_type")
        direct = direct_battles(r, script)
        if kind == "coord_event" and not direct:
            continue
        if kind == "object" and ttype in ("TRAINER_TYPE_NONE", None) and not direct:
            continue
        t = by_ev.get((kind, script, jfield(o, "x"), jfield(o, "y")))
        if t is None:
            bad.append("trainer %s %s at (%s,%s) missing" % (kind, script, jfield(o, "x"), jfield(o, "y")))
            continue
        if kind == "object" and (t.get("trainer_type") != ttype
                                 or t.get("sight") != int(jfield(o, "trainer_sight_or_berry_tree_id"))):
            bad.append("trainer object %s type/sight differ" % script)
        if not direct <= set(t.get("trainers", [])):
            bad.append("trainer %s %s: its label battles %s, maps.json joins %s" % (kind, script, sorted(direct),
                                                                                  t.get("trainers")))
    # every trainer this map's scripts battle, counted independently: its events' labels' battles must be on THIS map;
    # its own scripts.inc's battles on it, or on a map whose events name a label of that file
    on_map = {tid for t in rec.get("trainers", []) for tid in t["trainers"]}
    gone = sorted(r["event_battles"][mid] - on_map)
    if gone:
        bad.append("battled by its events' scripts but not on this map: %s" % gone)
    own = "data/maps/%s/scripts.inc" % folder
    if maps_by_id is not None and own in r["scripts"]:
        users = users if users is not None else file_users(r)
        carriers = {tid for m2 in (users.get(own, set()) | {mid}) if m2 in maps_by_id
                    for t in maps_by_id[m2].get("trainers", []) for tid in t["trainers"]}
        lost = sorted(set(re.findall(BATTLE_RE, r["scripts"][own], re.M)) - carriers)
        if lost:
            bad.append("battled in its scripts.inc but on none of its maps: %s" % lost)
    if bad:
        rep.mismatch("map", mid, "; ".join(bad))
    rep.seen("maps")


def map_items(r, mid):
    """[(map id, kind, record)] of the map's item balls (an ITEM_BALL object with a finditem script) and hidden items
    (read once per map: the raw text does not change between runs)."""
    cache = r.setdefault("items_cache", {})
    if mid not in cache:
        cache[mid] = _map_items(r, mid)
    return [(m, k, dict(v)) for m, k, v in cache[mid]]


def _map_items(r, mid):
    folder, text = r["maps"][mid]
    out = []
    for o in objects_of(text, "object_events"):
        if jfield(o, "graphics_id") == "OBJ_EVENT_GFX_ITEM_BALL" and jfield(o, "script") in r["balls"]:
            out.append((mid, "ball", {"x": jfield(o, "x"), "y": jfield(o, "y"), "elevation": jfield(o, "elevation"),
                                      "item": r["balls"][jfield(o, "script")], "flag": jfield(o, "flag"),
                                      "script": jfield(o, "script")}))
    for o in objects_of(text, "bg_events"):
        if jfield(o, "type") == "hidden_item":
            out.append((mid, "hidden", {"x": jfield(o, "x"), "y": jfield(o, "y"), "elevation": jfield(o, "elevation"),
                                        "item": jfield(o, "item"), "flag": jfield(o, "flag")}))
    return out


def raw_items(r):
    """[(map id, kind, record)] of every item ball and hidden item, raw."""
    return [it for mid in sorted(r["maps"]) for it in map_items(r, mid)]


def check_item(maps_by_id, mid, kind, want, rep):
    rec = maps_by_id.get(mid)
    have = (rec or {}).get("item_balls" if kind == "ball" else "hidden_items", [])
    if want not in have:
        rep.mismatch("item", "%s %s (%s,%s)" % (mid, kind, want["x"], want["y"]), "%s not in maps.json" % want)
    rep.seen("items")


def raw_badge_of(r, leader):
    files = {rel for rel, macro in r["battles"].get(leader, []) if "rematch" not in macro}
    found = set()
    for rel in files:
        found |= set(re.findall(r"^\s*setflag FLAG_(BADGE\d\d)_GET\s*$", r["scripts"][rel], re.M))
    return found.pop() if len(found) == 1 else None


def check_bosses(r, bosses, rep):
    rematch_firsts = set(r["rematch"].values())
    want_ids = set()
    for sym, b in r["blocks"].items():
        cls = re.search(r"\.trainerClass = TRAINER_CLASS_(\w+)", b).group(1)
        if cls in BOSS_CLASSES and sym not in r["rematch"] and sym in r["battles"]:
            want_ids.add(sym)
    got_ids = {b["id"] for b in bosses}
    if got_ids != want_ids:
        rep.mismatch("bosses", "the set", "extra %s, missing %s" % (sorted(got_ids - want_ids), sorted(want_ids - got_ids)))
    roles = [b["role"] for b in bosses]
    if (roles.count("gym_leader"), roles.count("elite_four"), roles.count("champion")) != (8, 4, 1):
        rep.mismatch("bosses", "the league", "gym leaders %d, Elite Four %d, Champion %d (want 8, 4, 1)" % (
            roles.count("gym_leader"), roles.count("elite_four"), roles.count("champion")))
    for rec in bosses:
        sym, bad = rec["id"], []
        if sym not in r["blocks"]:
            rep.mismatch("boss", sym, "no trainers.h block")
            continue
        b = r["blocks"][sym]
        cls = re.search(r"\.trainerClass = TRAINER_CLASS_(\w+)", b).group(1)
        if rec.get("role") != BOSS_CLASSES.get(cls):
            bad.append("role %r != class %s" % (rec.get("role"), cls))
        if rec.get("double") != (re.search(r"\.doubleBattle = (\w+)", b).group(1) == "TRUE"):
            bad.append("double differs")
        _, party = raw_party(r, sym)
        if len(party) != len(rec.get("party", [])):
            bad.append("party length %d != %d" % (len(rec.get("party", [])), len(party)))
        for i, (p, q) in enumerate(zip(rec.get("party", []), party), 1):
            moves = q.get("moves") or raw_default_moves(r, q["species"], q["level"])
            if (p["species"], p["level"], p.get("held_item"), p["moves"], p["types"]) != \
                    (q["species"], q["level"], q.get("held_item"), moves, r["types"].get(q["species"])):
                bad.append("slot %d (%s L%d) differs" % (i, q["species"], q["level"]))
        if sorted(rec.get("rematches", [])) != sorted(t for t, f in r["rematch"].items() if f == sym):
            bad.append("rematches differ")
        if rec.get("role") == "gym_leader":
            if (rec.get("badge") or {}).get("id") != raw_badge_of(r, sym):
                bad.append("badge %r != %r" % ((rec.get("badge") or {}).get("id"), raw_badge_of(r, sym)))
        if sym in rematch_firsts and rec.get("rematches") == []:
            bad.append("has rematches in gRematchTable but lists none")
        if bad:
            rep.mismatch("boss", sym, "; ".join(bad))
        rep.seen("bosses")


def raw_field_badges(r):
    """{MOVE name: BADGEnn} from the comments of src/party_menu.c's enum and sFieldMoves (src/data/party_menu.h)."""
    by_fm = dict(re.findall(r"^\s*(FIELD_MOVE_\w+),\s*// FLAG_(BADGE\d\d)_GET", r["rd"]("src/party_menu.c"), re.M))
    moves = dict(re.findall(r"\[(FIELD_MOVE_\w+)\]\s*= MOVE_(\w+)", r["rd"]("src/data/party_menu.h")))
    return {moves[fm]: badge for fm, badge in by_fm.items()}


def file_lines(r, rel):
    if rel not in r["lines"]:
        try:
            r["lines"][rel] = r["rd"](rel).split("\n")
        except (OSError, UnicodeDecodeError):
            r["lines"][rel] = None
    return r["lines"][rel]


def line_at(r, ref):
    """The text of `file:N` in the pinned clone, or None when the file or the line does not exist."""
    rel, n = ref.rsplit(":", 1)
    lines = file_lines(r, rel)
    if lines is None or not n.isdigit():
        return None
    return lines[int(n) - 1] if 0 < int(n) <= len(lines) else None


def label_of_line(r, rel, n):
    """(label, its body's lines) of the script label whose body holds line n of `rel`, or (None, [])."""
    lines = file_lines(r, rel) or []
    start = None
    for i in range(min(n, len(lines)), 0, -1):
        if re.match(r"^([A-Za-z_]\w*)::?[ \t]*$", lines[i - 1]):
            start = i
            break
    if start is None or start == n:
        return None, []
    body = []
    for ln in lines[start:]:
        if re.match(r"^([A-Za-z_]\w*)::?[ \t]*$", ln):
            break
        body.append(ln)
    return lines[start - 1].rstrip(":").rstrip(":"), body


def trainer_block_of_line(r, rel, n):
    """The `[TRAINER_X]` whose src/data/trainers.h block holds line n (the last block start at or above it)."""
    for ln in reversed((file_lines(r, rel) or [])[:n]):
        m = re.match(r"^\s*\[(TRAINER_\w+)\] =", ln)
        if m:
            return m.group(1)
    return None


def need_all(line, tokens):
    miss = [t for t in tokens if t not in line]
    return None if not miss else "the line does not hold %s" % miss


def array_tokens(r, sym):
    arr = party_array(r, sym)
    return ["TrainerMon", " %s[]" % arr] if arr else ["(no party array for %s)" % sym]


def _rule_moves_source(r, s, line, rel, n, st):
    boss = st[-2]
    return need_all(line, array_tokens(r, boss["id"]) if s.startswith("custom") else ["GiveBoxMonInitialMoveset"])


def _rule_note(r, s, line, rel, n, st):
    boss = st[-1]
    if "doubleBattle = TRUE" in s:
        if trainer_block_of_line(r, rel, n) != boss["id"]:
            return "the line is not in %s's trainers.h block" % boss["id"]
        return need_all(line, [".doubleBattle = TRUE"])
    return need_all(line, array_tokens(r, boss["id"]) if "custom (" in s else ["GiveBoxMonInitialMoveset"])


def _rule_boss_badge(r, s, line, rel, n, st):
    boss, badge = st[-2], st[-1]
    if rel not in {f for f, macro in r["battles"].get(boss["id"], []) if "rematch" not in macro}:
        return "%s is not the file that battles %s" % (rel, boss["id"])
    return need_all(line, ["setflag FLAG_%s_GET" % badge.get("id")])


def _rule_map_label(r, s, line, rel, n, st):
    t, mp = st[-1], st[-2]
    if rel != "data/maps/%s/scripts.inc" % mp["name"]:
        return "%s is not the map's own scripts.inc" % rel
    return None if re.match(r"^%s::?\s*$" % re.escape(t.get("label", "")), line) else \
        "the line is not the label %s" % t.get("label")


def _rule_gate(r, s, line, rel, n, st):
    g = st[-1]
    if not re.match(r"^\s*(call|goto)_if\w*\s+VAR_\w+", line):
        return "the line is not a conditional on a VAR_"
    _, body = label_of_line(r, rel, n)
    if not any(re.match(r"^\s*setflag FLAG_%s_GET\s*$" % g.get("badge"), ln) for ln in body):
        return "the line is not in the label that sets FLAG_%s_GET" % g.get("badge")
    return None


def _rule_party_min(r, s, line, rel, n, st, skeleton_by_id=None, fights=None):
    e = st[-2]
    sk = (skeleton_by_id or {}).get(e["id"], {})
    if sk.get("battle"):
        return need_all(line, [sk["battle"]["needle"]])
    m = re.match(r"^\s*\[(TRAINER_\w+)\] =", line)
    variants = {v["id"] for f in e.get("fights", []) for v in (fights or {}).get(f, [])}
    if not m or m.group(1) not in variants:
        return "the line is no block of the entry's fights %s" % e.get("fights")
    if not re.search(r"\.doubleBattle = TRUE", r["blocks"].get(m.group(1), "")):
        return "%s's block is not a double battle" % m.group(1)
    return None


#: (path pattern, where the mismatch is reported, the rule). A path is the JSON path with `[]` for any list index.
#: `st` is the stack of dicts enclosing the string (st[-1] holds the key or the list the string is in).
CITATION_RULES = [
    (r"^trainers/trainers\[\]/ref$", lambda st: ("trainer", st[-1]["symbol"]),
     lambda r, s, line, rel, n, st: need_all(line, ["[%s]" % st[-1]["symbol"]])),
    (r"^trainers/trainers\[\]/party_ref$", lambda st: ("trainer", st[-1]["symbol"]),
     lambda r, s, line, rel, n, st: need_all(line, array_tokens(r, st[-1]["symbol"]))),
    (r"^bosses/bosses\[\]/ref$", lambda st: ("boss", st[-1]["id"]),
     lambda r, s, line, rel, n, st: need_all(line, ["[%s]" % st[-1]["id"]])),
    (r"^bosses/bosses\[\]/badge/ref$", lambda st: ("boss", st[-2]["id"]), _rule_boss_badge),
    (r"^bosses/bosses\[\]/party\[\]/moves_source$", lambda st: ("boss", st[-2]["id"]), _rule_moves_source),
    (r"^bosses/bosses\[\]/notes\[\]$", lambda st: ("boss", st[-1]["id"]), _rule_note),
    (r"^maps/maps\[\]/trainers\[\]/ref$", lambda st: ("map", st[-2]["id"]), _rule_map_label),
    (r"^campaign/field_move_badges\[\]/ref$", lambda st: ("field_move", st[-1]["move"]),
     lambda r, s, line, rel, n, st: need_all(line, [st[-1]["field_move"], "FLAG_%s_GET" % st[-1]["badge"]])),
    (r"^campaign/field_move_badges\[\]/rule_ref$", lambda st: ("field_move", st[-1]["move"]),
     lambda r, s, line, rel, n, st: need_all(line, ["FlagGet(FLAG_BADGE01_GET + fieldMove)"])),
    (r"^campaign/field_move_badges\[\]/move_ref$", lambda st: ("field_move", st[-1]["move"]),
     lambda r, s, line, rel, n, st: need_all(line, ["[%s]" % st[-1]["field_move"], "MOVE_%s" % st[-1]["move"]])),
    (r"^campaign/field_move_badges\[\]/overworld_ref$", lambda st: ("field_move", st[-1]["move"]),
     lambda r, s, line, rel, n, st: need_all(line, ["FlagGet(FLAG_%s_GET)" % st[-1]["badge"]])),
    (r"^campaign/entries\[\]/needs/field_moves\[\]/ref$", lambda st: ("campaign", st[-3]["id"]),
     lambda r, s, line, rel, n, st: need_all(line, ["FIELD_MOVE_%s" % st[-1]["move"], "FLAG_%s_GET" % st[-1]["badge"]])),
    (r"^campaign/entries\[\]/needs/field_moves\[\]/rule_ref$", lambda st: ("campaign", st[-3]["id"]),
     lambda r, s, line, rel, n, st: need_all(line, ["FlagGet(FLAG_BADGE01_GET + fieldMove)"])),
    (r"^campaign/entries\[\]/needs/badge_refs/(BADGE\d\d)\[\]$", lambda st: ("campaign", st[-3]["id"]), None),
    (r"^campaign/entries\[\]/needs/badge_gates\[\]/ref$", lambda st: ("campaign", st[-3]["id"]), _rule_gate),
    (r"^campaign/entries\[\]/needs/badge_gates\[\]/setflag_ref$", lambda st: ("campaign", st[-3]["id"]),
     lambda r, s, line, rel, n, st: need_all(line, ["setflag FLAG_%s_GET" % st[-1]["badge"]])),
    (r"^campaign/entries\[\]/needs/key_items\[\]/ref$", lambda st: ("campaign", st[-3]["id"]),
     lambda r, s, line, rel, n, st: need_all(line, [st[-1]["item"]])),
    (r"^campaign/entries\[\]/needs/party_min_ref$", lambda st: ("campaign", st[-2]["id"]), _rule_party_min),
]


def walk_strings(obj, path, stack):
    """(path, string, stack of enclosing dicts) of every string in obj."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, "%s/%s" % (path, k), stack + [obj])
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v, path + "[]", stack)
    elif isinstance(obj, str):
        yield path, obj, stack


def check_citations(r, data, rep, skeleton_by_id, fights):
    """F1: every `file:line` of the four files is covered by a rule and its line HOLDS the rule's token."""
    n_cites = 0
    for name in ("trainers", "bosses", "maps", "campaign"):
        for path, s, st in walk_strings(data[name], name, []):
            for m in CITE_RE.finditer(s):
                n_cites += 1
                rel, n = m.group(1), int(m.group(2))
                rule = next(((re.match(p, path), where, fn) for p, where, fn in CITATION_RULES if re.match(p, path)),
                            None)
                if rule is None:
                    rep.mismatch("citation", path, "%s:%d is in a place no citation rule covers" % (rel, n))
                    continue
                pm, where, fn = rule
                try:
                    kind, key = where(st)
                except (KeyError, IndexError, TypeError):
                    kind, key = "citation", path
                line = line_at(r, "%s:%d" % (rel, n))
                if line is None:
                    rep.mismatch(kind, key, "%s:%d cites no line of the pinned decomp" % (rel, n))
                    continue
                if fn is None:  # badge_refs: the badge named by the key
                    err = need_all(line, ["FLAG_%s_GET" % pm.group(1)])
                elif fn is _rule_party_min:
                    err = fn(r, s, line, rel, n, st, skeleton_by_id, fights)
                else:
                    try:
                        err = fn(r, s, line, rel, n, st)
                    except (KeyError, IndexError, TypeError) as exc:
                        err = "its record lacks %s" % exc
                if err:
                    rep.mismatch(kind, key, "%s:%d (%s): %s" % (rel, n, path.rsplit("/", 1)[-1], err))
    rep.seen("citations", n_cites)


def raw_fights(r, boss, fights):
    """The entry's fights, re-derived: the boss, then the other opponent of each multi battle (SET_TRAINER_A/B in the
    one scripts.inc) that sets up any of its variants."""
    if boss is None:
        return []
    fight_of_id = {v["id"]: f for f, vs in fights.items() for v in vs}
    out = [boss]
    for v in fights.get(boss, []):
        for rel, ab in r["multi"].items():
            if v["id"] in ab["A"] + ab["B"]:
                for other in ab["A"] + ab["B"]:
                    f = fight_of_id.get(other)
                    if f and f not in out:
                        out.append(f)
    return out


def raw_area_bosses(r, area, fight_of_id):
    """Every boss fight referenced by the area maps' scripts: each map's own scripts.inc (or its shared one) and the
    labels its events name, wherever they are defined."""
    out = set()
    for name in area:
        if "MAP_" + name not in r["maps"]:
            continue
        folder, text = r["maps"]["MAP_" + name]
        own = "data/maps/%s/scripts.inc" % (jfield(text, "shared_scripts_map") or folder)
        tids = set(re.findall(BATTLE_RE, r["scripts"].get(own, ""), re.M)) | r["event_battles"]["MAP_" + name]
        out |= {fight_of_id[t] for t in tids if t in fight_of_id}
    return sorted(out)


def check_campaign(r, camp, bosses, rep, milestones, skeleton):
    want = raw_field_badges(r)
    for row in camp.get("field_move_badges", []):
        if want.get(row["move"]) != row["badge"] or row["flag"] != "FLAG_%s_GET" % want.get(row["move"]):
            rep.mismatch("field_move", row["move"], "badge %s / flag %s != decomp %s" % (row["badge"], row["flag"],
                                                                                         want.get(row["move"])))
        rep.seen("field_moves")
    if sorted(want) != sorted(row["move"] for row in camp.get("field_move_badges", [])):
        rep.mismatch("field_move", "the table", "moves %s != decomp %s" % (
            [row["move"] for row in camp.get("field_move_badges", [])], sorted(want)))
    entries = camp.get("entries", [])
    ms = [(m["id"], m["chapter"]) for m in milestones["milestones"]]
    if [(e["id"], e["chapter"]) for e in entries[:len(ms)]] != ms:
        rep.mismatch("campaign", "milestones", "the first %d ids/chapters are not milestones.json's" % len(ms))
    sk_entries = skeleton["entries"]
    if [e["id"] for e in entries] != [s["id"] for s in sk_entries]:
        rep.mismatch("campaign", "skeleton", "the entry ids are not the skeleton's, in its order")
    sk_by_id = {s["id"]: s for s in sk_entries}
    fights = {}
    for b in bosses:
        fights.setdefault(b["fight"], []).append(b)
    fight_of_id = {b["id"]: b["fight"] for b in bosses}
    award = {}
    for e in entries:
        vs = fights.get(e.get("boss"), [])
        badge = raw_badge_of(r, vs[0]["id"]) if vs and vs[0]["role"] == "gym_leader" else None
        if badge and badge not in award:
            award[badge] = e["order"]
    own_fights = [raw_fights(r, e.get("boss"), fights) for e in entries]
    first = {}
    for k, (e, fs) in enumerate(zip(entries, own_fights), 1):
        for f in fs:
            first.setdefault(f, (k, e["id"]))
    for b in bosses:  # every boss's order and entry, from the fights re-derived above
        k, eid = first.get(b["fight"], (None, None))
        if (b.get("order"), b.get("entry")) != (k, eid):
            rep.mismatch("boss", b["id"], "order/entry %r/%r != the first entry fighting it %r/%r"
                         % (b.get("order"), b.get("entry"), k, eid))
    for k, e in enumerate(entries, 1):
        bad, n = [], e["needs"]
        sk = sk_by_id.get(e["id"], {})
        skn = sk.get("needs") or {}
        if e["order"] != k:
            bad.append("order %r at position %d" % (e["order"], k))
        if (e.get("area"), e.get("boss"), e.get("chapter")) != (sk.get("area"), sk.get("boss"), sk.get("chapter")):
            bad.append("area/boss/chapter are not the skeleton's")
        for name in e["area"]:
            if "MAP_" + name not in r["maps"]:
                bad.append("area map %s is not in the decomp" % name)
        if e.get("boss") is not None and e["boss"] not in fights:
            bad.append("boss %s is no fight" % e["boss"])
        if e.get("fights") != own_fights[k - 1]:
            bad.append("fights %s != re-derived %s" % (e.get("fights"), own_fights[k - 1]))
        area_bosses = raw_area_bosses(r, e["area"], fight_of_id)
        if e.get("area_bosses") != area_bosses:
            bad.append("area_bosses %s != the bosses its area's scripts battle %s" % (e.get("area_bosses"), area_bosses))
        if not set(own_fights[k - 1]) <= set(area_bosses):
            bad.append("fights %s are not battled on its area maps" % own_fights[k - 1])
        # the needs the skeleton states must all be there (a DROPPED need is a mismatch, not silence)
        if [fm["move"] for fm in n["field_moves"]] != [fm["move"] for fm in skn.get("field_moves", [])]:
            bad.append("field moves %s != the skeleton's" % [fm["move"] for fm in n["field_moves"]])
        want_badges = sorted({b["badge"] for b in skn.get("badges", [])}
                             | {want.get(fm["move"]) for fm in skn.get("field_moves", [])})
        if n["badges"] != want_badges or sorted(n["badge_refs"]) != want_badges:
            bad.append("badges %s != the skeleton's needs %s" % (n["badges"], want_badges))
        if [b["badge"] for b in n.get("badge_gates", [])] != [b["badge"] for b in skn.get("badges", [])
                                                               if b.get("gate_needle")]:
            bad.append("badge gates are not the skeleton's")
        if [ki["item"] for ki in n["key_items"]] != [ki["item"] for ki in skn.get("key_items", [])]:
            bad.append("key items %s != the skeleton's" % [ki["item"] for ki in n["key_items"]])
        for fm in n["field_moves"]:
            if want.get(fm["move"]) != fm["badge"]:
                bad.append("field move %s badge %s != decomp %s" % (fm["move"], fm["badge"], want.get(fm["move"])))
        for badge in n["badges"]:
            if award.get(badge, 10 ** 6) >= e["order"]:
                bad.append("needs %s, which no earlier boss awards (W4b)" % badge)
        vs = [v for f in own_fights[k - 1] for v in fights.get(f, [])]
        if sk.get("battle"):
            if (n["double_battle"], n["party_min"]) != (bool(sk["battle"]["double_battle"]), sk["battle"]["party_min"]):
                bad.append("double_battle/party_min are not the skeleton's battle")
        else:
            dbl = any(re.search(r"\.doubleBattle = TRUE", r["blocks"][v["id"]]) for v in vs if v["id"] in r["blocks"])
            if n["double_battle"] != dbl or n["party_min"] != (2 if dbl else 1):
                bad.append("double_battle/party_min %s/%s != decomp %s" % (n["double_battle"], n["party_min"], dbl))
        ahead_k = next((j for j in range(k - 1, len(entries)) if entries[j].get("boss")), None)
        if ahead_k is not None:
            ahead_fights = own_fights[ahead_k]
            parties = [p for f in ahead_fights for v in fights.get(f, []) for p in raw_party(r, v["id"])[1]]
            lv = [p["level"] for p in parties]
            band = n["level_band"] or {}
            if lv and (band.get("low"), band.get("high")) != (min(lv), max(lv)):
                bad.append("level_band %r..%r != the fights ahead's %d..%d" % (band.get("low"), band.get("high"),
                                                                              min(lv), max(lv)))
            types = sorted({t for p in parties for t in r["types"].get(p["species"], [])})
            if n["types_ahead"] != types or n.get("types_ahead_of") != ahead_fights:
                bad.append("types_ahead %s of %s != the fights ahead's %s of %s" % (
                    n["types_ahead"], n.get("types_ahead_of"), types, ahead_fights))
        if bad:
            rep.mismatch("campaign", e["id"], "; ".join(bad))
        rep.seen("campaign")
    hits = route_keys(camp)
    if hits:
        rep.mismatch("campaign", "W6", "route keys %s" % hits[:5])
    return sk_by_id, fights


# ---------------------------------------------------------------- W1 and W6 scans (no decomp needed)
def withheld_hits_in(obj, path="$"):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if re.sub(r"[^a-z]", "", str(k).lower()) in _WITHHELD_NORMS:
                out.append("%s.%s" % (path, k))
            out += withheld_hits_in(v, "%s.%s" % (path, k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += withheld_hits_in(v, "%s[%d]" % (path, i))
    return out


def withheld_scan(root=KNOWLEDGE):
    """W1: (files scanned, [(file, key path)]) over EVERY .json under `root`, recursively."""
    hits, n = [], 0
    for dirpath, _, names in os.walk(root):
        for name in sorted(names):
            if name.endswith(".json"):
                n += 1
                p = os.path.join(dirpath, name)
                with open(p, encoding="utf-8") as f:
                    hits += [(os.path.relpath(p, root), h) for h in withheld_hits_in(json.load(f))]
    return n, hits


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


# ---------------------------------------------------------------- the run
def load(data_dir):
    out = {}
    for name in ("trainers", "bosses", "maps", "campaign"):
        with open(os.path.join(data_dir, name + ".json"), encoding="utf-8") as f:
            out[name] = json.load(f)
    return out


def load_skeleton(path=SKELETON):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def choose(r, data, seed):
    """The fixed-seed sample: trainer symbols, map ids (at least 5 with connections), raw item records."""
    rnd = random.Random(seed)
    syms = sorted(t["symbol"] for t in data["trainers"]["trainers"])
    t_pick = rnd.sample(syms, SAMPLE["trainers"])
    with_conn = sorted(m["id"] for m in data["maps"]["maps"] if m["connections"])
    rest = sorted(m["id"] for m in data["maps"]["maps"] if not m["connections"])
    m_pick = rnd.sample(with_conn, 5) + rnd.sample(rest, SAMPLE["maps"] - 5)
    items = raw_items(r)
    i_pick = rnd.sample(items, SAMPLE["items"])
    return t_pick, m_pick, i_pick


def verify(r, data, milestones, seed=None, skeleton=None):
    """Report over the whole data (seed None) or the fixed-seed sample plus every boss, the table, the campaign and
    every citation."""
    skeleton = skeleton if skeleton is not None else load_skeleton()
    rep = Report()
    trainers = {t["symbol"]: t for t in data["trainers"]["trainers"]}
    maps = {m["id"]: m for m in data["maps"]["maps"]}
    bosses = data["bosses"]["bosses"]
    if seed is None:
        t_pick, m_pick, i_pick = sorted(trainers), sorted(maps), raw_items(r)
    else:
        t_pick, m_pick, i_pick = choose(r, data, seed)
    boss_ids = sorted({b["id"] for b in bosses})
    for sym in list(dict.fromkeys(t_pick + boss_ids)):
        if sym in trainers:
            check_trainer(r, trainers[sym], rep)
        else:
            rep.mismatch("trainer", sym, "not in trainers.json")
    users = file_users(r)
    for mid in m_pick:
        check_map(r, maps[mid], rep, maps, users)
    for mid, kind, want in i_pick:
        check_item(maps, mid, kind, want, rep)
    check_bosses(r, bosses, rep)
    sk_by_id, fights = check_campaign(r, data["campaign"], bosses, rep, milestones, skeleton)
    check_citations(r, data, rep, sk_by_id, fights)
    # totals, whatever the sample (W5's count and every battle a map's scripts reference placed on a map)
    if len(trainers) != len(r["ids"]):
        rep.mismatch("totals", "trainers", "%d records, opponents.h has %d ids" % (len(trainers), len(r["ids"])))
    refs = {t.get("party_ref") for t in trainers.values() if t.get("party_ref")}
    if len(refs) != r["n_arrays"]:
        rep.mismatch("totals", "parties", "%d distinct parties, trainer_parties.h has %d arrays" % (len(refs), r["n_arrays"]))
    empty = sorted(s for s, t in trainers.items() if not t.get("party"))
    if empty != ["TRAINER_NONE"]:
        rep.mismatch("totals", "empty parties", "%s (only TRAINER_NONE may be empty)" % empty)
    placed = {tid for m in maps.values() for t in m["trainers"] for tid in t["trainers"]}
    referenced = set(r["battles"]) | {tid for s in r["event_battles"].values() for tid in s}
    if placed != referenced:
        rep.mismatch("totals", "map battles", "missing %s, extra %s" % (sorted(referenced - placed)[:8],
                                                                       sorted(placed - referenced)[:8]))
    rep.seen("map_battles", len(referenced))
    return rep, (len(t_pick), len(m_pick), len(i_pick))


def apply_plants(r, data, seed):
    """W2's four plants, in memory; returns their report keys: (a) a boss's level, (b) Surf's badge BADGE05 -> BADGE04,
    (c) a doubleBattle, (d) one connection's map."""
    t_pick, m_pick, _ = choose(r, data, seed)
    rox = next(b for b in data["bosses"]["bosses"] if b["fight"] == "ROXANNE")
    rox["party"][0]["level"] += 1
    surf = next(row for row in data["campaign"]["field_move_badges"] if row["move"] == "SURF")
    surf["badge"] = "BADGE04"
    tr = next(t for t in data["trainers"]["trainers"] if t["symbol"] == t_pick[0])
    tr["double"] = not tr["double"]
    mp = next(m for m in data["maps"]["maps"] if m["id"] == m_pick[0])
    mp["connections"][0]["map"] = "MAP_LITTLEROOT_TOWN" if mp["connections"][0]["map"] != "MAP_LITTLEROOT_TOWN" \
        else "MAP_ROUTE101"
    return ["MISMATCH boss %s:" % rox["id"], "MISMATCH field_move SURF:", "MISMATCH trainer %s:" % tr["symbol"],
            "MISMATCH map %s:" % mp["id"]]


def plant_result(r, data_dir, milestones, seed):
    """(ok, the report lines, the plant keys): ok iff each plant is reported exactly once and nothing else is."""
    data = load(data_dir)
    keys = apply_plants(r, data, seed)
    rep, _ = verify(r, data, milestones, seed)
    lines = rep.lines
    hit = [sum(1 for ln in lines if ln.startswith(k)) for k in keys]
    return hit == [1, 1, 1, 1] and len(lines) == 4, lines, keys


def selftest(r, data_dir, milestones, seed):
    """FAULT and CONTROL arms of the verifier itself (the plants, the W1 and W6 scans)."""
    results = []
    ok, lines, keys = plant_result(r, data_dir, milestones, seed)
    results.append(("W2 FAULT: the four plants reported, nothing else (%d lines)" % len(lines), ok))
    rep, n = verify(r, load(data_dir), milestones, seed)
    results.append(("W2 CONTROL: no plant, sample %s: %d mismatches" % (n, len(rep.lines)), not rep.lines))
    data = load(data_dir)
    data["trainers"]["trainers"][1]["party"][0]["iv"] = 0
    results.append(("W1 FAULT: an iv planted in trainers.json is found", bool(withheld_hits_in(data["trainers"]))))
    nfiles, hits = withheld_scan(KNOWLEDGE)
    results.append(("W1 CONTROL: %d knowledge files, no withheld key" % nfiles, nfiles > 0 and not hits))
    data["campaign"]["entries"][0]["route"] = ["ROUTE101"]
    results.append(("W6 FAULT: a route key planted in campaign.json is found", bool(route_keys(data["campaign"]))))
    results.append(("W6 CONTROL: the real campaign.json has none", not route_keys(load(data_dir)["campaign"])))
    for name, good in results:
        print("[%s] %s" % ("PASS" if good else "FAIL", name))
    return all(g for _, g in results)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--decomp")
    ap.add_argument("--data", default=DATA_DEFAULT)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--plant", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--knowledge", default=KNOWLEDGE, help="the tree W1 scans (default ai_player/knowledge)")
    a = ap.parse_args(argv)
    try:
        r = raw(pinned_root(a.decomp))
    except Refused as exc:
        print("[VERIFY-WORLD] REFUSED:", exc)
        return 2
    with open(MILESTONES, encoding="utf-8") as f:
        milestones = json.load(f)
    seed = DEFAULT_SEED if a.seed is None and (a.plant or a.selftest) else a.seed
    if a.selftest:
        good = selftest(r, a.data, milestones, seed)
        print("[VERIFY-WORLD] SELFTEST %s" % ("PASS" if good else "FAIL"))
        return 0 if good else 1
    if a.plant:
        ok, lines, keys = plant_result(r, a.data, milestones, seed)
        for ln in lines:
            print(ln)
        print("[VERIFY-WORLD] PLANT %s: %d of 4 plants reported, %d lines in all" % (
            "PASS" if ok else "FAIL", sum(1 for k in keys if any(ln.startswith(k) for ln in lines)), len(lines)))
        return 0 if ok else 1
    rep, n = verify(r, load(a.data), milestones, seed)
    lines = rep.lines
    for ln in lines:
        print(ln)
    nfiles, hits = withheld_scan(a.knowledge)
    for f, h in hits:
        print("MISMATCH withheld %s: %s (USER RULING 44)" % (f, h))
    scope = "every record" if seed is None else "seed %d: %d trainers, %d maps, %d item records" % ((seed,) + n)
    bad = len(lines) + len(hits)
    print("[VERIFY-WORLD] %s: %d mismatches (%s; checked %s; W1 scanned %d knowledge files)" % (
        "PASS" if not bad else "FAIL", bad, scope, dict(sorted(rep.counts.items())), nfiles))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
