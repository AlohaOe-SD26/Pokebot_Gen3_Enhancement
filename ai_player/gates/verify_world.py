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


# ---------------------------------------------------------------- slice 2, stage 2a: items_gifts.json
# A SECOND READING of extract_items.py's output (spec S3-4 slice 2, "THE INDEPENDENT VERIFIER"). Nothing here is shared
# with the extractor, and the route differs: the extractor walks FORWARD from every root through a parsed command
# graph; this walks BACKWARD from each gift line through the raw text's word mentions to the map.json files and C
# lines that start it. Item balls are re-derived from map.json objects whose label's FIRST command is finditem; marts
# from the pokemart operand to its `.2byte` lines; `daily` from a FLAG_DAILY_ test near the gift; the fossil
# exclusivity from map.json object flags; the R-4 key rule by its own walker.
S2_FILE = "items_gifts.json"
S2_WATCH = ("giveitem", "givemon", "giveegg", "givedecoration", "finditem", "additem", "adddecoration", "pokemart",
            "pokemartdecoration", "pokemartdecoration2")
S2_GIFTS = ("giveitem", "givemon", "giveegg", "givedecoration")
#: fix round 2 (item 6): every command that never runs on to the next line, the verifier's own list (src/scrcmd.c:
#: ScrCmd_end / goto / return / vgoto / gotostd / returnram / endram / gotopostbattlescript / gotobeatenscript)
S2_ENDS = ("end", "return", "goto", "step_end", "pokemartlistend", "vgoto", "gotostd", "returnram", "endram",
           "gotopostbattlescript", "gotobeatenscript")
S2_NAMED = re.compile(r"\b(?:FLAG|VAR)_\w+")
#: the stage-2a plants: (e) a gift moved to another map, (g) the dead Aqua Hideout Master Ball promoted into gifts,
#: (h) the Lilycove berry loses daily, (h2) Root/Claw lose exclusive_with, (i) a mart list item dropped, (j) an
#: Electrode (ITEM_BALL graphics) reported as a gift, (k) a flag name moved out of `dev` to a bare `flag` key
#: fix round 1 adds (l) HM Surf once -> repeatable, (m) the Favor Lady random -> choice, (n) the lottery's one_of
#: collapsed to one item, (o) the Deep Sea Tooth's exclusive_with emptied, (p) HM Surf's map_script_2 test dropped
#: from dev.tests, (q) a map_script giver added to the Route 114 berry man
#: fix round 2 adds (a1)..(a8): one plant per rule check, each on a record the golden list does not hold, so deleting
#: the rule turns its plant arm red (round 1's l / o / q were also caught by the golden list)
#: fix round 3 adds (a7s) until_received over a flag another script writes, (a9) 'no condition' over a false-at-start own
#: test, (a10) a worded `when` over an unread special, (d3) a daily-re-armed Shoal shell said repeatable, (gw) a golden
#: `unknown` record that no longer names its outside writer; a6 moves to the Lava Cookie (Cozmo is now golden)
S2_PLANTS = ("e", "g", "h", "h2", "i", "j", "k", "l", "m", "n", "o", "p", "q",
             "a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a7s", "a9", "a10", "d3", "gw")
_S2 = {}


def s2_strip(text):
    """The text as a vanilla build assembles it, one output line per input line: `#ifdef BUGFIX|UBFIX` keeps its
    `#else` side, `#ifndef` its first side; `@` and `//` comments go (a `.string` line is kept whole)."""
    out, keep = [], []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("#ifdef") or s.startswith("#ifndef"):
            keep.append(s.startswith("#ifndef"))
            out.append("")
            continue
        if s.startswith("#else"):
            keep[-1] = not keep[-1]
            out.append("")
            continue
        if s.startswith("#endif"):
            keep.pop()
            out.append("")
            continue
        if s.startswith("#") or (keep and not all(keep)):
            out.append("")
            continue
        out.append(line if s.startswith(".string") else re.split(r"@|//", line, 1)[0].rstrip())
    return out


def s2_raw(root):
    """The verifier's own tables for slice 2, read once per root."""
    if root in _S2:
        return _S2[root]
    r = raw(root)
    rd = r["rd"]
    gift_files = set(re.findall(r'\.include "(data/scripts/[\w.]+)"', rd("data/mystery_gift.s")))
    files = dict(r["scripts"])
    files.update({k: v for k, v in r["library"].items() if k not in gift_files})
    files["data/event_scripts.s"] = rd("data/event_scripts.s")
    labs, order = {}, []
    for rel in sorted(files):
        cur = None
        for n, line in enumerate(s2_strip(files[rel]), 1):
            m = re.match(r"^([A-Za-z_]\w*)::?\s*$", line)
            if m:
                cur = m.group(1)
                labs[cur] = {"file": rel, "line": n, "lines": []}
                order.append(cur)
            elif cur and line.strip():
                labs[cur]["lines"].append((n, line.strip()))
    nxt = {a: b for a, b in zip(order, order[1:]) if labs[a]["file"] == labs[b]["file"]}
    c_src = {}
    for top in ("src", "include"):
        for dirpath, _, names in os.walk(os.path.join(root, top)):
            for fn in names:
                if fn.endswith((".c", ".h")):
                    p = os.path.join(dirpath, fn)
                    c_src[os.path.relpath(p, root).replace("\\", "/")] = open(p, encoding="utf-8", errors="replace").read()
    c_words = set()
    for t in c_src.values():
        c_words |= set(re.findall(r"[A-Za-z_]\w*", t))
    never = set()  # a branch on `specialvar VAR_RESULT, Fn` where Fn's whole body is `return FALSE;` never jumps
    for t in c_src.values():
        never |= set(re.findall(r"\b(\w+)\(void\)\s*\{\s*return FALSE;[^\n}]*\s*\}", t))
    mentioned_by, at, fwd = {}, {}, {}
    for name, lab in labs.items():
        prev = ""
        for n, line in lab["lines"]:
            if not line.startswith(".string"):
                skip = re.match(r"goto_if_eq VAR_RESULT, TRUE,", line) and \
                    re.match(r"specialvar VAR_RESULT, (\w+)", prev) and \
                    re.match(r"specialvar VAR_RESULT, (\w+)", prev).group(1) in never
                if not skip:
                    for w in set(re.findall(r"[A-Za-z_]\w*", line)):
                        if w in labs and w != name:
                            mentioned_by.setdefault(w, set()).add(name)
                            at.setdefault(w, []).append((name, n))
                            fwd.setdefault(name, []).append((w, n))
            prev = line
        cmds = [ln for _, ln in lab["lines"] if not ln.startswith(".")]
        last = lab["lines"][-1][1] if lab["lines"] else ""
        falls = not lab["lines"] or (cmds and not last.startswith(".") and last.split()[0] not in S2_ENDS)
        if falls and name in nxt:
            mentioned_by.setdefault(nxt[name], set()).add(name)
            at.setdefault(nxt[name], []).append((name, 10 ** 9))
            fwd.setdefault(name, []).append((nxt[name], 10 ** 9))
    roots, ms_of = {}, {}  # label -> {map ids}; map id -> its <owner>_MapScripts label
    for mid, (folder, text) in r["maps"].items():
        for s in re.findall(r'"script": "(\w+)"', text):
            roots.setdefault(s, set()).add(mid)
        owner = re.search(r'"shared_scripts_map": "(\w+)"', text) or re.search(r'"name": "(\w+)"', text)
        roots.setdefault(owner.group(1) + "_MapScripts", set()).add(mid)
        ms_of[mid] = owner.group(1) + "_MapScripts"
    s = {"labs": labs, "by": mentioned_by, "at": at, "fwd": fwd, "roots": roots, "ms_of": ms_of, "c_words": c_words,
         "gift_files": gift_files, "files": files, "owner": {}, "maps_raw": r["maps"], "root": root}
    _S2[root] = s
    return s


def s2_owner(s, label):
    """(maps, reached from C, the labels on the way) by a BACKWARD walk over mentions and fall-throughs."""
    if label in s["owner"]:
        return s["owner"][label]
    seen, todo, maps, c = set(), [label], set(), False
    while todo and len(seen) < 4000:
        x = todo.pop()
        if x in seen:
            continue
        seen.add(x)
        maps |= s["roots"].get(x, set())
        c = c or x in s["c_words"]
        todo += [y for y in s["by"].get(x, ()) if y not in seen]
    s["owner"][label] = (maps, c, seen)
    return s["owner"][label]


def s2_before(s, name, upto, depth, seen=None):
    """The raw lines that run BEFORE line `upto` of `name`: its own earlier lines, then each mentioning label's lines
    before its mention (a fall-through: all of them), `depth` labels back."""
    seen = set() if seen is None else seen
    if (name, upto) in seen:
        return []
    seen.add((name, upto))
    out = [ln for n, ln in s["labs"][name]["lines"] if n < upto]
    if depth:
        for src, n in s["at"].get(name, ()):
            out += s2_before(s, src, n, depth - 1, seen)
    return out


def s2_lines(s, cmds):
    """[(label, nth gift of the label, 'file:line', command, operand)] of every `cmds` line, file order."""
    out = []
    for name, lab in s["labs"].items():
        k = 0
        for n, line in lab["lines"]:
            parts = line.replace(",", " ").split()
            if parts and parts[0] in cmds:
                if parts[0] in S2_GIFTS:
                    k += 1
                out.append((name, k, "%s:%d" % (lab["file"], n), parts[0], parts[1] if len(parts) > 1 else None))
    return out


def s2_key_hits(obj, path="$", inside=False):
    """R-4, the verifier's own walker: flag/flags/var/vars keys and FLAG_/VAR_ strings outside a `dev` dict."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if not inside and k in ("flag", "flags", "var", "vars"):
                hits.append("%s.%s" % (path, k))
            hits += s2_key_hits(v, "%s.%s" % (path, k), inside or k == "dev")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += s2_key_hits(v, "%s[%d]" % (path, i), inside)
    elif isinstance(obj, str) and not inside and S2_NAMED.search(obj):
        hits.append("%s=%s" % (path, obj[:40]))
    return hits


#: fix round 1 (F7): commands that move saved state, the verifier's own list for the `repeatable` rule check
S2_SETTER = re.compile(r"^(setflag|clearflag|setvar|addvar|subvar|copyvar|removeobject)\s+(\w+)")
#: scratch registers, never state (VAR_RESULT, the special 0x80xx vars)
S2_SCRATCH = re.compile(r"VAR_RESULT$|VAR_0x80[0-9A-Fa-f]{2}$")
#: a command whose answer a following `switch VAR_RESULT` reads: the player's menu choice
S2_MENU = re.compile(r"^(?:multichoice|multichoicedefault|multichoicegrid|yesnobox)\b|^msgbox\b.*\bMSGBOX_YESNO\b"
                     r"|^special\s+ShowScrollableMultichoice\b")
#: fix round 2: a VAR_RESULT made by one of these is bag/party ROOM (never a condition in `when`). Fix round 3: a yes/no
#: box is NOT room (it is the player's answer, S2_ANSWER), so the two are told apart
S2_ROOMISH = re.compile(r"^(?:checkitemspace|checkdecorspace|getpartysize|giveitem|givedecoration|givemon|giveegg|"
                        r"additem|adddecoration)\b")
#: fix round 3: a VAR_RESULT made by a yes/no box is the player's ANSWER (a choice made on the spot, never game state)
S2_ANSWER = re.compile(r"^yesnobox\b|^msgbox\b.*\bMSGBOX_YESNO\b")
#: fix round 2: a "do you own X" check (a possession: a condition `when` must word, item 3); fix round 3 adds money,
#: coins and decorations (src/scrcmd.c ScrCmd_checkmoney / checkcoins / checkdecor), group 1 = what is checked
S2_HAVE = re.compile(r"^(?:checkitem|checkpcitem|checkdecor)\s+((?:ITEM|DECOR)_\w+)|^(?:checkmoney|checkcoins)\s+(\w+)")
#: (c) a daily guard: a FLAG_DAILY_ test in either jump or call form, set or unset (round 0 matched goto_if_set only)
S2_DAILY = re.compile(r"\b(?:goto|call)_if_(?:set|unset)\s+FLAG_DAILY_\w+")
#: (b) THE GOLDEN LIST: records read off the decomp BY HAND for fix round 1, each with the lines that make it true
#: as (path:line, a token that must be on that line). The tokens are checked AT VERIFY TIME against the pinned clone,
#: so a moved pin fails loudly (a golden entry whose line moved is a mismatch), never a silent pass. Keys: repeat,
#: chosen_by, one_of (the item set), exclusive_with (exact), tests (each must be in dev.tests), givers (the giver
#: kinds, exact), when (exact), words_has (a phrase in what.words).
S2_GOLDEN = [
    {"id": "PetalburgCity_WallysHouse_EventScript_GiveHMSurf:1", "repeat": "unknown", "truth": "once",
     "other_writer": ("data/maps/PetalburgCity/scripts.inc:47", "setvar VAR_PETALBURG_CITY_STATE"),
     "exclusive_with": [],
     "tests": ["VAR_PETALBURG_CITY_STATE eq 4"], "givers": ["map_script"],
     "cites": [("data/maps/PetalburgCity_WallysHouse/scripts.inc:16",
                "map_script_2 VAR_PETALBURG_CITY_STATE, 4, PetalburgCity_WallysHouse_EventScript_GiveHMSurf"),
               ("data/maps/PetalburgCity_WallysHouse/scripts.inc:22", "giveitem ITEM_HM_SURF"),
               ("data/maps/PetalburgCity_WallysHouse/scripts.inc:25", "setvar VAR_PETALBURG_CITY_STATE, 5")]},
    {"id": "Route119_EventScript_GiveFlyHM:1", "repeat": "once",
     "cites": [("data/maps/Route119/scripts.inc:130", "giveitem ITEM_HM_FLY"),
               ("data/maps/Route119/scripts.inc:131", "setflag FLAG_RECEIVED_HM_FLY"),
               ("data/maps/Route119/scripts.inc:144", "setvar VAR_ROUTE119_STATE, 1"),
               ("data/maps/Route119/map.json:613", '"var": "VAR_ROUTE119_STATE"')]},
    {"id": "PetalburgCity_Gym_EventScript_GiveFacade:1", "repeat": "unknown", "truth": "until_received",
     "other_writer": ("data/maps/DewfordTown_Gym/scripts.inc:152", "addvar VAR_PETALBURG_GYM_STATE"),
     "cites": [("data/maps/PetalburgCity_Gym/scripts.inc:394", "giveitem ITEM_TM_FACADE"),
               ("data/maps/PetalburgCity_Gym/scripts.inc:395", "goto_if_eq VAR_RESULT, FALSE, Common_EventScript_BagIsFull"),
               ("data/maps/PetalburgCity_Gym/scripts.inc:396", "setflag FLAG_RECEIVED_TM_FACADE")]},
    {"id": "MirageTower_4F_EventScript_RootFossil:1", "repeat": "unknown", "truth": "once", "when": None,
     "other_writer": ("data/maps/MirageTower_4F/scripts.inc:32", "setflag FLAG_HIDE_MIRAGE_TOWER_ROOT_FOSSIL"),
     "exclusive_with": ["MirageTower_4F_EventScript_ClawFossil:1"],
     "cites": [("data/maps/MirageTower_4F/scripts.inc:9", "giveitem ITEM_ROOT_FOSSIL"),
               ("data/maps/MirageTower_4F/scripts.inc:11", "setflag FLAG_HIDE_MIRAGE_TOWER_ROOT_FOSSIL"),
               ("data/maps/MirageTower_4F/scripts.inc:12", "setflag FLAG_HIDE_MIRAGE_TOWER_CLAW_FOSSIL"),
               ("data/maps/MirageTower_4F/map.json:29", '"flag": "FLAG_HIDE_MIRAGE_TOWER_ROOT_FOSSIL"'),
               ("src/mirage_tower.c:328", "visible = rand & 1;")]},
    {"id": "MirageTower_4F_EventScript_ClawFossil:1", "repeat": "unknown", "truth": "once", "when": None,
     "other_writer": ("data/maps/MirageTower_4F/scripts.inc:12", "setflag FLAG_HIDE_MIRAGE_TOWER_CLAW_FOSSIL"),
     "exclusive_with": ["MirageTower_4F_EventScript_RootFossil:1"],
     "cites": [("data/maps/MirageTower_4F/scripts.inc:29", "giveitem ITEM_CLAW_FOSSIL"),
               ("data/maps/MirageTower_4F/scripts.inc:31", "setflag FLAG_HIDE_MIRAGE_TOWER_CLAW_FOSSIL"),
               ("data/maps/MirageTower_4F/map.json:43", '"flag": "FLAG_HIDE_MIRAGE_TOWER_CLAW_FOSSIL"')]},
    {"id": "DesertUnderpass_EventScript_GiveClawFossil:1", "repeat": "unknown", "truth": "once",
     "other_writer": ("data/maps/Route111/scripts.inc:122", "clearflag FLAG_HIDE_DESERT_UNDERPASS_FOSSIL"),
     "exclusive_with": ["DesertUnderpass_EventScript_GiveRootFossil:1"], "tests": ["FLAG_CHOSE_ROOT_FOSSIL set"],
     "cites": [("data/maps/DesertUnderpass/scripts.inc:12",
                "goto_if_set FLAG_CHOSE_ROOT_FOSSIL, DesertUnderpass_EventScript_GiveClawFossil"),
               ("data/maps/DesertUnderpass/scripts.inc:18", "giveitem ITEM_CLAW_FOSSIL"),
               ("data/maps/DesertUnderpass/scripts.inc:19", "removeobject LOCALID_UNDERPASS_FOSSIL"),
               ("data/maps/DesertUnderpass/map.json:29", '"flag": "FLAG_HIDE_DESERT_UNDERPASS_FOSSIL"')]},
    {"id": "MossdeepCity_StevensHouse_EventScript_StevenGivesDive:1", "repeat": "unknown", "truth": "once",
     "other_writer": ("data/maps/MossdeepCity_SpaceCenter_2F/scripts.inc:288", "setvar VAR_STEVENS_HOUSE_STATE"),
     "givers": ["map_script"],
     "tests": ["VAR_STEVENS_HOUSE_STATE eq 1"],
     "cites": [("data/maps/MossdeepCity_StevensHouse/scripts.inc:25",
                "map_script_2 VAR_STEVENS_HOUSE_STATE, 1, MossdeepCity_StevensHouse_EventScript_StevenGivesDive"),
               ("data/maps/MossdeepCity_StevensHouse/scripts.inc:36", "giveitem ITEM_HM_DIVE"),
               ("data/maps/MossdeepCity_StevensHouse/scripts.inc:45", "setvar VAR_STEVENS_HOUSE_STATE, 2")]},
    {"id": "GraniteCave_StevensRoom_EventScript_Steven:1", "repeat": "once",
     "cites": [("data/maps/GraniteCave_StevensRoom/scripts.inc:12", "giveitem ITEM_TM_STEEL_WING"),
               ("data/maps/GraniteCave_StevensRoom/scripts.inc:13",
                "call_if_eq VAR_RESULT, FALSE, GraniteCave_StevensRoom_EventScript_BagFull"),
               ("data/maps/GraniteCave_StevensRoom/scripts.inc:30", "removeobject LOCALID_GRANITE_CAVE_STEVEN"),
               ("data/maps/GraniteCave_StevensRoom/scripts.inc:52", "return"),
               ("data/maps/GraniteCave_StevensRoom/map.json:29", '"flag": "FLAG_HIDE_GRANITE_CAVE_STEVEN"')]},
    {"id": "Route111_EventScript_GiveSecretPower:1", "repeat": "until_received",
     "cites": [("data/scripts/secret_power_tm.inc:46", "giveitem ITEM_TM_SECRET_POWER"),
               ("data/scripts/secret_power_tm.inc:47",
                "goto_if_eq VAR_RESULT, FALSE, Route111_EventScript_NoRoomForSecretPower"),
               ("data/scripts/secret_power_tm.inc:55", "removeobject VAR_LAST_TALKED")]},
    # fix round 2: the Deep Sea pair is `until_received`: a full bag jumps away (:336) before the Scanner is taken
    # (:337) and the flag set (:339); the trigger needs the Scanner (:305), whose one source is the Abandoned Ship
    {"id": "SlateportCity_Harbor_EventScript_DeepSeaTooth:1", "repeat": "until_received", "when_has": "Scanner",
     "exclusive_with": ["SlateportCity_Harbor_EventScript_DeepSeaScale:1"],
     "cites": [("data/maps/SlateportCity_Harbor/scripts.inc:305", "checkitem ITEM_SCANNER"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:324", "multichoice 0, 0, MULTI_STERN_DEEPSEA, FALSE"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:326", "case 0, SlateportCity_Harbor_EventScript_DeepSeaTooth"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:335", "giveitem ITEM_DEEP_SEA_TOOTH"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:336", "goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:337", "removeitem ITEM_SCANNER"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:339", "setflag FLAG_EXCHANGED_SCANNER")]},
    {"id": "SlateportCity_Harbor_EventScript_DeepSeaScale:1", "repeat": "until_received", "when_has": "Scanner",
     "exclusive_with": ["SlateportCity_Harbor_EventScript_DeepSeaTooth:1"],
     "cites": [("data/maps/SlateportCity_Harbor/scripts.inc:327", "case 1, SlateportCity_Harbor_EventScript_DeepSeaScale"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:346", "giveitem ITEM_DEEP_SEA_SCALE"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:347", "goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:348", "removeitem ITEM_SCANNER"),
               ("data/maps/SlateportCity_Harbor/scripts.inc:350", "setflag FLAG_EXCHANGED_SCANNER")]},
    # fix round 2: ONE tent. The Entrance pair is the End pair's pick-up after a full PC (End :157 / :195 set
    # VAR_TRICK_HOUSE_PRIZE_PICKUP 1; only that, at level 8, makes the Entrance set state 6, :19 / :33 / :38, whose case
    # 6 offers the tent again, :225): the four lines are exclusive with each other
    {"id": "Route110_TrickHouseEnd_EventScript_GiveRedTent:1", "repeat": "once",
     "exclusive_with": ["Route110_TrickHouseEnd_EventScript_GiveBlueTent:1",
                        "Route110_TrickHouseEntrance_EventScript_GiveBlueTent:1",
                        "Route110_TrickHouseEntrance_EventScript_GiveRedTent:1"],
     "cites": [("data/maps/Route110_TrickHouseEnd/scripts.inc:165", "multichoice 0, 0, MULTI_TENT, TRUE"),
               ("data/maps/Route110_TrickHouseEnd/scripts.inc:167", "case 0, Route110_TrickHouseEnd_EventScript_GiveRedTent"),
               ("data/maps/Route110_TrickHouseEnd/scripts.inc:171", "givedecoration DECOR_RED_TENT"),
               ("data/maps/Route110_TrickHouseEnd/scripts.inc:183", "addvar VAR_TRICK_HOUSE_LEVEL, 1"),
               ("data/maps/Route110_TrickHouseEnd/scripts.inc:195", "setvar VAR_TRICK_HOUSE_PRIZE_PICKUP, 1"),
               ("data/maps/Route110_TrickHouseEntrance/scripts.inc:19", "goto_if_eq VAR_TRICK_HOUSE_PRIZE_PICKUP, 1"),
               ("data/maps/Route110_TrickHouseEntrance/scripts.inc:38", "setvar VAR_TRICK_HOUSE_ENTRANCE_STATE, 6")]},
    {"id": "Route110_TrickHouseEnd_EventScript_GiveBlueTent:1", "repeat": "once",
     "exclusive_with": ["Route110_TrickHouseEnd_EventScript_GiveRedTent:1",
                        "Route110_TrickHouseEntrance_EventScript_GiveBlueTent:1",
                        "Route110_TrickHouseEntrance_EventScript_GiveRedTent:1"],
     "cites": [("data/maps/Route110_TrickHouseEnd/scripts.inc:168", "goto Route110_TrickHouseEnd_EventScript_GiveBlueTent"),
               ("data/maps/Route110_TrickHouseEnd/scripts.inc:175", "givedecoration DECOR_BLUE_TENT")]},
    {"id": "Route110_TrickHouseEntrance_EventScript_GiveRedTent:1", "repeat": "unknown", "truth": "until_received",
     "other_writer": ("data/maps/Route110_TrickHouseEntrance/scripts.inc:180", "removeobject"),
     "exclusive_with": ["Route110_TrickHouseEnd_EventScript_GiveBlueTent:1",
                        "Route110_TrickHouseEnd_EventScript_GiveRedTent:1",
                        "Route110_TrickHouseEntrance_EventScript_GiveBlueTent:1"],
     "cites": [("data/maps/Route110_TrickHouseEntrance/scripts.inc:225",
                "case 6, Route110_TrickHouseEntrance_EventScript_MechadollReward"),
               ("data/maps/Route110_TrickHouseEntrance/scripts.inc:403", "multichoice 0, 0, MULTI_TENT, TRUE"),
               ("data/maps/Route110_TrickHouseEntrance/scripts.inc:405",
                "case 0, Route110_TrickHouseEntrance_EventScript_GiveRedTent"),
               ("data/maps/Route110_TrickHouseEntrance/scripts.inc:409", "givedecoration DECOR_RED_TENT"),
               ("data/maps/Route110_TrickHouseEntrance/scripts.inc:425", "setvar VAR_TRICK_HOUSE_ENTRANCE_STATE, 5")]},
    # fix round 2: the Favor Lady's prize is until_received (her state goes COMPLETED, read back at :13; a full bag at
    # :115 leaves it PRIZE, read at :16), she is there only for some trainer IDs, and her prize excludes the Quiz Lady's
    {"id": "LilycoveCity_PokemonCenter_1F_EventScript_FavorLadyPrize:1", "chosen_by": "random",
     "repeat": "unknown", "truth": "until_received", "when_has": "Favor Lady",
     "why_has": "STATE_FAVOR_LADY: not a flag or var name",
     "exclusive_with": ["LilycoveCity_PokemonCenter_1F_EventScript_GivePrize:1"],
     "one_of": ["ITEM_HEART_SCALE", "ITEM_LUXURY_BALL", "ITEM_NUGGET", "ITEM_PP_MAX", "ITEM_PROTEIN", "ITEM_RARE_CANDY"],
     "cites": [("data/scripts/lilycove_lady.inc:112", "specialvar VAR_0x8004, FavorLadyGetPrize"),
               ("data/scripts/lilycove_lady.inc:114", "giveitem VAR_0x8004"),
               ("data/scripts/lilycove_lady.inc:115", "goto_if_eq VAR_RESULT, 0"),
               ("data/scripts/lilycove_lady.inc:125", "special SetFavorLadyState_Complete"),
               ("data/scripts/lilycove_lady.inc:13", "specialvar VAR_RESULT, GetFavorLadyState"),
               ("src/lilycove_lady.c:292", "sFavorLadyPtr->state = LILYCOVE_LADY_STATE_COMPLETED;"),
               ("src/lilycove_lady.c:64", "id %= 6;"),
               ("src/lilycove_lady.c:133", "favorId = Random() % ARRAY_COUNT(sFavorLadyRequests)"),
               ("src/lilycove_lady.c:283", "prize = sFavorLadyPrizes[sFavorLadyPtr->favorId]"),
               ("src/data/lilycove_lady.h:425", "ITEM_LUXURY_BALL"), ("src/data/lilycove_lady.h:430", "ITEM_PP_MAX")]},
    # fix round 2 additions (item 7), each read off the decomp
    {"id": "Route113_GlassWorkshop_EventScript_GiveGlassFlute:1", "repeat": "repeatable",
     "cites": [("data/maps/Route113_GlassWorkshop/scripts.inc:27",
                "goto_if_eq VAR_GLASS_WORKSHOP_STATE, 2, Route113_GlassWorkshop_EventScript_CheckCollectedAsh"),
               ("data/maps/Route113_GlassWorkshop/scripts.inc:59", "special ShowScrollableMultichoice"),
               ("data/maps/Route113_GlassWorkshop/scripts.inc:80", "subvar VAR_ASH_GATHER_COUNT, BLUE_FLUTE_PRICE"),
               ("data/maps/Route113_GlassWorkshop/scripts.inc:195", "setvar VAR_GLASS_WORKSHOP_STATE, 2"),
               ("data/maps/Route113_GlassWorkshop/scripts.inc:200", "giveitem VAR_0x8008")]},
    {"id": "ContestHall_EventScript_GiveLuxuryBall:1", "repeat": "repeatable",
     "cites": [("data/maps/ContestHall/scripts.inc:58", "map_script_2 VAR_CONTEST_HALL_STATE, 1, ContestHall_EventScript_Contest"),
               ("data/scripts/contest_hall.inc:181", "setvar VAR_CONTEST_HALL_STATE, 1"),
               ("data/scripts/contest_hall.inc:202", "setvar VAR_CONTEST_HALL_STATE, 2"),
               ("data/scripts/contest_hall.inc:1094", "goto_if_eq VAR_CONTEST_RANK, CONTEST_RANK_MASTER"),
               ("data/scripts/contest_hall.inc:1109", "giveitem ITEM_LUXURY_BALL")]},
    {"id": "MauvilleCity_House2_EventScript_AcceptTrade:1", "repeat": "once", "when": "needs 1 Harbor Mail",
     "cites": [("data/maps/MauvilleCity_House2/scripts.inc:9", "checkitem ITEM_HARBOR_MAIL"),
               ("data/maps/MauvilleCity_House2/scripts.inc:10", "goto_if_eq VAR_RESULT, TRUE"),
               ("data/maps/MauvilleCity_House2/scripts.inc:26", "giveitem ITEM_COIN_CASE"),
               ("data/maps/MauvilleCity_House2/scripts.inc:27", "setflag FLAG_RECEIVED_COIN_CASE")]},
    {"id": "ShoalCave_LowTideEntranceRoom_EventScript_ShellBellExpert:1", "repeat": "repeatable",
     "when": "needs 4 Shoal Salt; needs 4 Shoal Shell",
     "cites": [("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:23", "checkitem ITEM_SHOAL_SALT, 4"),
               ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:25", "checkitem ITEM_SHOAL_SHELL, 4"),
               ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:35", "giveitem ITEM_SHELL_BELL"),
               ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:38", "setflag FLAG_TEMP_2")]},
    {"id": "RustboroCity_EventScript_ReturnGoods:1", "repeat": "unknown", "truth": "once", "when": None,
     "other_writer": ("data/maps/RustboroCity/scripts.inc:286", "clearflag FLAG_HIDE_RUSTBORO_CITY_DEVON_EMPLOYEE_1"),
     "cites": [("data/maps/RustboroCity/scripts.inc:441", "goto_if_set FLAG_RECOVERED_DEVON_GOODS"),
               ("data/maps/RustboroCity/scripts.inc:557", "giveitem ITEM_GREAT_BALL"),
               ("data/maps/RustboroCity/scripts.inc:563", "setvar VAR_RUSTBORO_CITY_STATE, 5")]},
    {"id": "LittlerootTown_ProfessorBirchsLab_EventScript_MayGivePokeBalls:1",
     "exclusive_with": ["LittlerootTown_ProfessorBirchsLab_EventScript_BrendanGivePokeBalls:1"],
     "cites": [("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:506", "checkplayergender"),
               ("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:507", "call_if_eq VAR_RESULT, MALE"),
               ("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:508", "call_if_eq VAR_RESULT, FEMALE"),
               ("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:522", "setvar VAR_RESULT, 0")]},
    {"id": "LittlerootTown_ProfessorBirchsLab_EventScript_BrendanGivePokeBalls:1",
     "exclusive_with": ["LittlerootTown_ProfessorBirchsLab_EventScript_MayGivePokeBalls:1"],
     "cites": [("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:527", "giveitem ITEM_POKE_BALL, 5")]},
    {"id": "MossdeepCity_StevensHouse_EventScript_GiveBeldum:1", "repeat": "unknown", "truth": "until_received",
     "other_writer": ("data/scripts/hall_of_fame.inc:40",
                      "clearflag FLAG_HIDE_MOSSDEEP_CITY_STEVENS_HOUSE_BELDUM_POKEBALL"),
     "cites": [("data/maps/MossdeepCity_StevensHouse/scripts.inc:81", "givemon SPECIES_BELDUM, 5"),
               ("data/maps/MossdeepCity_StevensHouse/scripts.inc:84", "goto Common_EventScript_NoMoreRoomForPokemon"),
               ("data/scripts/hall_of_fame.inc:21", "call_if_unset FLAG_RECEIVED_BELDUM"),
               ("data/scripts/hall_of_fame.inc:40", "clearflag FLAG_HIDE_MOSSDEEP_CITY_STEVENS_HOUSE_BELDUM_POKEBALL")]},
    {"id": "LittlerootTown_ProfessorBirchsLab_EventScript_GiveCyndaquil:1",
     "when": "the giver is not there at first: they appear later in the story",
     "tests": ["FLAG_HIDE_LITTLEROOT_TOWN_BIRCHS_LAB_POKEBALL_CYNDAQUIL unset"],
     "cites": [("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:329", "givemon SPECIES_CYNDAQUIL, 5"),
               ("data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:363",
                "setvar VAR_DEX_UPGRADE_JOHTO_STARTER_STATE, 6"),
               ("data/scripts/new_game.inc:122", "setflag FLAG_HIDE_LITTLEROOT_TOWN_BIRCHS_LAB_POKEBALL_CYNDAQUIL")]},
    {"id": "PlayersHouse_1F_EventScript_GetSSTicketAndSeeLatiTV:1", "repeat": "unknown", "truth": "once",
     "other_writer": ("data/maps/LittlerootTown/scripts.inc:69", "setvar VAR_LITTLEROOT_HOUSES_STATE_MAY"),
     "tests": ["VAR_LITTLEROOT_HOUSES_STATE_MAY eq 3"], "when": "after entering the Hall of Fame",
     "cites": [("data/maps/LittlerootTown_BrendansHouse_1F/scripts.inc:54",
                "map_script_2 VAR_LITTLEROOT_HOUSES_STATE_MAY, 3, PlayersHouse_1F_EventScript_GetSSTicketAndSeeLatiTV"),
               ("data/maps/LittlerootTown_MaysHouse_1F/scripts.inc:53",
                "map_script_2 VAR_LITTLEROOT_HOUSES_STATE_MAY, 3, PlayersHouse_1F_EventScript_GetSSTicketAndSeeLatiTV"),
               ("data/scripts/hall_of_fame.inc:44", "setvar VAR_LITTLEROOT_HOUSES_STATE_MAY, 3"),
               ("data/scripts/players_house.inc:407", "giveitem ITEM_SS_TICKET"),
               ("data/scripts/players_house.inc:449", "setvar VAR_LITTLEROOT_HOUSES_STATE_MAY, 4")]},
    {"id": "LilycoveCity_EventScript_BerryGentleman:1", "repeat": "daily", "chosen_by": "random",
     "one_of": ["ITEM_ASPEAR_BERRY", "ITEM_CHERI_BERRY", "ITEM_CHESTO_BERRY", "ITEM_LEPPA_BERRY", "ITEM_LUM_BERRY",
                "ITEM_ORAN_BERRY", "ITEM_PECHA_BERRY", "ITEM_PERSIM_BERRY", "ITEM_RAWST_BERRY", "ITEM_SITRUS_BERRY"],
     "cites": [("data/maps/LilycoveCity/scripts.inc:37", "goto_if_set FLAG_DAILY_LILYCOVE_RECEIVED_BERRY"),
               ("data/maps/LilycoveCity/scripts.inc:39", "random 10"),
               ("data/maps/LilycoveCity/scripts.inc:40", "addvar VAR_RESULT, FIRST_BERRY_INDEX"),
               ("include/constants/items.h:152", "ITEM_CHERI_BERRY,"),
               ("include/constants/items.h:161", "ITEM_SITRUS_BERRY,")]},
    {"id": "LilycoveCity_DepartmentStore_1F_EventScript_LotteryClerk:1", "repeat": "daily", "chosen_by": "draw",
     "one_of": ["ITEM_EXP_SHARE", "ITEM_MASTER_BALL", "ITEM_MAX_REVIVE", "ITEM_PP_UP"], "words_has": "win nothing",
     "cites": [("data/maps/LilycoveCity_DepartmentStore_1F/scripts.inc:13", "goto_if_set FLAG_DAILY_PICKED_LOTO_TICKET"),
               ("data/maps/LilycoveCity_DepartmentStore_1F/scripts.inc:40", "giveitem VAR_0x8005"),
               ("src/lottery_corner.c:16", "ITEM_PP_UP"), ("src/lottery_corner.c:19", "ITEM_MASTER_BALL"),
               ("src/lottery_corner.c:70", "numMatchingDigits > 1")]},
    {"id": "PacifidlogTown_House2_EventScript_GiveReturn:1", "repeat": "weekly",
     "exclusive_with": ["PacifidlogTown_House2_EventScript_GiveFrustration:1"],
     "cites": [("data/maps/PacifidlogTown_House2/scripts.inc:14",
                "goto_if_ge VAR_RESULT, FRIENDSHIP_150_TO_199, PacifidlogTown_House2_EventScript_GiveReturn"),
               ("data/maps/PacifidlogTown_House2/scripts.inc:41", "giveitem ITEM_TM_RETURN"),
               ("data/maps/PacifidlogTown_House2/scripts.inc:43", "setflag FLAG_RECEIVED_FANCLUB_TM_THIS_WEEK")]},
    {"id": "PacifidlogTown_House2_EventScript_GiveFrustration:1", "repeat": "weekly",
     "exclusive_with": ["PacifidlogTown_House2_EventScript_GiveReturn:1"],
     "cites": [("data/maps/PacifidlogTown_House2/scripts.inc:56", "giveitem ITEM_TM_FRUSTRATION")]},
    {"id": "MauvilleCity_GameCorner_EventScript_GiveTreeckoDoll:1", "repeat": "unknown", "truth": "once",
     "when": "by your starter",
     "other_writer": ("data/maps/MauvilleCity_GameCorner/scripts.inc:407", "setflag FLAG_RECEIVED_STARTER_DOLL"),
     "exclusive_with": ["MauvilleCity_GameCorner_EventScript_GiveMudkipDoll:1",
                        "MauvilleCity_GameCorner_EventScript_GiveTorchicDoll:1"],
     "cites": [("data/maps/MauvilleCity_GameCorner/scripts.inc:385", "switch VAR_STARTER_MON"),
               ("data/maps/MauvilleCity_GameCorner/scripts.inc:396", "givedecoration DECOR_TREECKO_DOLL"),
               ("data/maps/MauvilleCity_GameCorner/scripts.inc:397", "setflag FLAG_RECEIVED_STARTER_DOLL")]},
    {"id": "RustboroCity_Gym_EventScript_GiveRockTomb:1", "repeat": "unknown", "truth": "until_received",
     "why_has": "TRAINER:TRAINER_ROXANNE_1: not a flag or var name", "when": "after you defeat LEADER ROXANNE",
     "tests": ["TRAINER_ROXANNE_1 defeated"],
     "cites": [("data/maps/RustboroCity_Gym/scripts.inc:29", "giveitem ITEM_TM_ROCK_TOMB"),
               ("data/maps/RustboroCity_Gym/scripts.inc:30", "goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull")]},
    {"id": "Route114_EventScript_Man:1", "givers": ["object"], "repeat": "daily",
     "cites": [("data/maps/Route114/scripts.inc:18", "Route114_OnFrame:"),
               ("data/maps/Route114/scripts.inc:20", ".2byte 0"),
               ("data/maps/Route114/scripts.inc:22", "Route114_EventScript_Man::"),
               ("data/maps/Route114/scripts.inc:31", "giveitem VAR_RESULT")]},
    {"id": "Route118_EventScript_ReceiveGoodRod:1", "givers": ["object"],
     "cites": [("data/maps/Route118/scripts.inc:34", "giveitem ITEM_GOOD_ROD")]},
    {"id": "RustboroCity_DevonCorp_3F_EventScript_MeetPresident:1", "repeat": "once", "givers": ["map_script"],
     "tests": ["VAR_DEVON_CORP_3F_STATE eq 0"],
     "cites": [("data/maps/RustboroCity_DevonCorp_3F/scripts.inc:25",
                "map_script_2 VAR_DEVON_CORP_3F_STATE, 0, RustboroCity_DevonCorp_3F_EventScript_MeetPresident"),
               ("data/maps/RustboroCity_DevonCorp_3F/scripts.inc:48", "giveitem ITEM_LETTER"),
               ("data/maps/RustboroCity_DevonCorp_3F/scripts.inc:67", "setvar VAR_DEVON_CORP_3F_STATE, 1")]},
    # fix round 3 additions (item 7), each read off the decomp. A Shoal Cave salt: re-armed DAILY (src/clock.c:53 sets
    # FLAG_SYS_SHOAL_ITEM each day, field_specials.c:1420; the Shell Bell man's :22 call_if_set then clears the salt
    # and shell flags, :82-90), never until_received
    {"id": "ShoalCave_LowTideInnerRoom_EventScript_ShoalSalt1:1", "repeat": "daily", "when_has": "Shell Bell man",
     "cites": [("data/maps/ShoalCave_LowTideInnerRoom/scripts.inc:113",
                "goto_if_set FLAG_RECEIVED_SHOAL_SALT_1, ShoalCave_LowTideInnerRoom_EventScript_ReceivedShoalSalt"),
               ("data/maps/ShoalCave_LowTideInnerRoom/scripts.inc:114", "giveitem ITEM_SHOAL_SALT"),
               ("data/maps/ShoalCave_LowTideInnerRoom/scripts.inc:118", "setflag FLAG_RECEIVED_SHOAL_SALT_1"),
               ("src/clock.c:53", "SetShoalItemFlag(daysSince);"),
               ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:22", "call_if_set FLAG_SYS_SHOAL_ITEM"),
               ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc:82", "clearflag FLAG_RECEIVED_SHOAL_SALT_1")]},
    # the lottery's owed prize: :12 tests VAR_POKELOT_PRIZE_ITEM ne ITEM_NONE, FALSE at new game (the var starts 0 =
    # ITEM_NONE), so it is a precondition, never 'no condition'; the var has outside writers (:92, lottery_corner.c:29)
    {"id": "LilycoveCity_DepartmentStore_1F_EventScript_GivePrizeFromEarlier:1", "repeat": "unknown", "when": None,
     "tests": ["VAR_POKELOT_PRIZE_ITEM ne ITEM_NONE"],
     "other_writer": ("data/maps/LilycoveCity_DepartmentStore_1F/scripts.inc:92", "copyvar VAR_POKELOT_PRIZE_ITEM"),
     "cites": [("data/maps/LilycoveCity_DepartmentStore_1F/scripts.inc:12",
                "goto_if_ne VAR_POKELOT_PRIZE_ITEM, ITEM_NONE, LilycoveCity_DepartmentStore_1F_EventScript_GivePrizeFromEarlier"),
               ("data/maps/LilycoveCity_DepartmentStore_1F/scripts.inc:103", "giveitem VAR_POKELOT_PRIZE_ITEM"),
               ("src/lottery_corner.c:29", "VarSet(VAR_POKELOT_PRIZE_ITEM, ITEM_NONE);")]},
    # the contest counter's Luxury Ball: re-armed by every Master-rank win with a full bag (contest_hall.inc:1105),
    # so not until_received
    {"id": "LilycoveCity_ContestLobby_EventScript_GiveLuxuryBallAtCounter:1", "repeat": "unknown",
     "other_writer": ("data/scripts/contest_hall.inc:1105", "setvar VAR_CONTEST_PRIZE_PICKUP, 4"),
     "cites": [("data/scripts/contest_hall.inc:29", "giveitem ITEM_LUXURY_BALL"),
               ("data/scripts/contest_hall.inc:31", "setvar VAR_CONTEST_PRIZE_PICKUP, 0")]},
    # Cozmo's TM: the trigger needs the Meteorite (:8-9); the yes/no answer after the two opposite call_ifs (:15-17)
    # is the player's choice, not the checkitem; FLAG_RECEIVED_TM_RETURN is set only here (:23)
    {"id": "FallarborTown_CozmosHouse_EventScript_PlayerHasMeteorite:1", "repeat": "until_received",
     "when_has": "Meteorite",
     "cites": [("data/maps/FallarborTown_CozmosHouse/scripts.inc:8", "checkitem ITEM_METEORITE"),
               ("data/maps/FallarborTown_CozmosHouse/scripts.inc:9",
                "goto_if_eq VAR_RESULT, TRUE, FallarborTown_CozmosHouse_EventScript_PlayerHasMeteorite"),
               ("data/maps/FallarborTown_CozmosHouse/scripts.inc:15", "call_if_unset FLAG_TEMP_2"),
               ("data/maps/FallarborTown_CozmosHouse/scripts.inc:16", "call_if_set FLAG_TEMP_2"),
               ("data/maps/FallarborTown_CozmosHouse/scripts.inc:17", "goto_if_eq VAR_RESULT, NO"),
               ("data/maps/FallarborTown_CozmosHouse/scripts.inc:23", "setflag FLAG_RECEIVED_TM_RETURN")]},
    # Castform: the talk script is ungated, but the scientist stands behind Team Aqua until Shelly is beaten (:6, :12,
    # :42, :60): `when` is null (a map condition), never 'no condition'
    {"id": "Route119_WeatherInstitute_2F_EventScript_ReceiveCastform:1", "when": None,
     "cites": [("data/maps/Route119_WeatherInstitute_2F/scripts.inc:6",
                "call_if_eq VAR_WEATHER_INSTITUTE_STATE, 0, Route119_WeatherInstitute_2F_EventScript_SetScientistPosAquaHere"),
               ("data/maps/Route119_WeatherInstitute_2F/scripts.inc:12",
                "setobjectxyperm LOCALID_WEATHER_INSTITUTE_2F_SCIENTIST, 1, 6"),
               ("data/maps/Route119_WeatherInstitute_2F/scripts.inc:60", "setvar VAR_WEATHER_INSTITUTE_STATE, 1"),
               ("data/maps/Route119_WeatherInstitute_2F/scripts.inc:81", "givemon SPECIES_CASTFORM, 25")]},
    {"mart": "PetalburgCity_Mart_EventScript_Clerk", "list": "PetalburgCity_Mart_Pokemart_Expanded",
     "setter": "data/event_scripts.s:678",
     "reached_by": {"ref": "data/maps/RustboroCity_Gym/scripts.inc:24", "test": "VAR_PETALBURG_GYM_STATE eq 6"},
     "cites": [("data/maps/PetalburgCity_Mart/scripts.inc:9", "goto_if_set FLAG_PETALBURG_MART_EXPANDED_ITEMS"),
               ("data/event_scripts.s:676", "Common_EventScript_ReadyPetalburgGymForBattle::"),
               ("data/event_scripts.s:678", "setflag FLAG_PETALBURG_MART_EXPANDED_ITEMS"),
               ("data/maps/RustboroCity_Gym/scripts.inc:24",
                "call_if_eq VAR_PETALBURG_GYM_STATE, 6, Common_EventScript_ReadyPetalburgGymForBattle")]},
]


def s2_reach(s, starts, stop=None):
    """Every label reached FORWARD from `starts` through the raw mentions and fall-throughs, never entering `stop`."""
    seen, todo = set(), list(starts)
    while todo and len(seen) < 4000:
        x = todo.pop()
        if x in seen or x == stop or x not in s["labs"]:
            continue
        seen.add(x)
        todo += [w for w, _ in s["fwd"].get(x, ())]
    return seen


def s2_after(s, name, n, depth=6, seen=None):
    """The raw lines that run AFTER line `n` of `name`: its own lines to the first terminator, every label mentioned
    after the line (a jump, a call, a branch, a case, the fall), and after a `return` the lines after each line that
    mentions `name` (where a call into it resumes); `depth` labels on."""
    seen = set() if seen is None else seen
    if (name, n) in seen or depth < 0:
        return []
    seen.add((name, n))
    out, stop, end = [], 10 ** 9, None
    for m, ln in s["labs"][name]["lines"]:
        if m <= n:
            continue
        out.append(("%s:%d" % (s["labs"][name]["file"], m), ln))
        if ln.split()[0] in S2_ENDS:
            stop, end = m, ln.split()[0]
            break
    for w, m in s["fwd"].get(name, ()):
        if n < m <= stop:
            out += s2_after(s, w, 0, depth - 1, seen)
    if end == "return":
        for src, m in s["at"].get(name, ()):
            if m < 10 ** 9:
                out += s2_after(s, src, m, depth - 1, seen)
    return out


def s2_menus(s):
    """[(label, 'file:line', [arm labels])] of each `switch VAR_RESULT` right after a menu command: the `case` targets
    and the `goto` after the last case (the default arm)."""
    out = []
    for name, lab in s["labs"].items():
        lines = lab["lines"]
        for i, (n, ln) in enumerate(lines):
            if i == 0 or not re.match(r"switch VAR_RESULT\s*$", ln) or not S2_MENU.match(lines[i - 1][1]):
                continue
            arms = []
            for _, ln2 in lines[i + 1:]:
                c = re.match(r"case [^,]+,\s*(\w+)\s*$", ln2)
                if c:
                    arms += [c.group(1)] if c.group(1) not in arms else []
                    continue
                gt = re.match(r"goto (\w+)\s*$", ln2)
                if gt and gt.group(1) not in arms:
                    arms.append(gt.group(1))
                break
            out.append((name, "%s:%d" % (lab["file"], n), arms))
    return out


def s2_map_entries(s, mid):
    """The labels a map's own map scripts run: each `map_script` target, or, for a table, each `map_script_2` target."""
    out = []
    for _, ln in s["labs"].get(s["ms_of"].get(mid), {"lines": []})["lines"]:
        m = re.match(r"map_script \w+,\s*(\w+)", ln)
        if not m or m.group(1) not in s["labs"]:
            continue
        table = [re.match(r"map_script_2 [^,]+,[^,]+,\s*(\w+)", x) for _, x in s["labs"][m.group(1)]["lines"]]
        if any(table):
            out += [t.group(1) for t in table if t]
        else:
            out.append(m.group(1))
    return out


def s2_rules(s, items, want, prob):
    """(a) the fix-round-1 RULE checks, each re-derived from the raw text (`prob(record id, problem)`):
    a1 no `repeatable` gift with a state setter on its own continuation (s2_after);
    a2 every gift in one arm of a menu switch is exclusive_with the gifts of its sibling arms (s2_menus; not between
       two `repeatable` gifts, whose menu can be opened again);
    a3 no `map_script` giver unless the map's own table walk reaches the gift (s2_map_entries + s2_reach);
    a4 every `giveitem VAR_*` record has `one_of` (a list or 'unknown') and a `chosen_by`."""
    gifts = {g["id"]: g for g in items["gifts"]}
    by_label = {}
    for gid in gifts:
        by_label.setdefault(gid.rsplit(":", 1)[0], []).append(gid)
    for gid, g in gifts.items():
        name = gid.rsplit(":", 1)[0]
        if g["repeat"] == "repeatable":
            # fix round 2: a setter after a repeatable gift is allowed only when the record cites a re-arm of that
            # name (dev.rearm), or it is a TEMP name no line of the gift's own file tests (cleared on map entry)
            rearmed = {w["writes"] for w in g["dev"].get("rearm") or []}
            hit = [(where, ln) for where, ln in s2_after(s, name, int(g["ref"].rsplit(":", 1)[1]))
                   if S2_SETTER.match(ln) and not S2_SCRATCH.match(S2_SETTER.match(ln).group(2))
                   and not re.match(r"(FLAG|VAR)_TEMP_", S2_SETTER.match(ln).group(2))
                   and where.rsplit(":", 1)[0] == s["labs"][name]["file"]]
            if hit and not rearmed:
                prob(gid, "repeatable, but %r runs after it (%s)" % (hit[0][1], hit[0][0]))
        s2_rules_round2(s, gid, g, name, prob)
        for gv in g.get("giver") or []:
            if gv["kind"] == "map_script" and name not in s2_reach(s, s2_map_entries(s, gv["map"])):
                prob(gid, "giver map_script on %s, but no map_script / map_script_2 entry of it reaches %s" %
                     (gv["map"], name))
        if g["ref"] in want and want[g["ref"]][2] == "giveitem" and (want[g["ref"]][3] or "").startswith("VAR_"):
            w = g["what"]
            if not isinstance(w, dict) or not (isinstance(w.get("one_of"), list) or w.get("one_of") == "unknown") \
                    or "chosen_by" not in w:
                prob(gid, "a giveitem VAR_* record needs one_of (a list or 'unknown') and chosen_by, has %r" % (w,))
    for name, where, arms in s2_menus(s):
        members = [{gid for x in s2_reach(s, [a], stop=name) for gid in by_label.get(x, ())} for a in arms]
        for i, mine in enumerate(members):
            others = set().union(*[m for j, m in enumerate(members) if j != i])
            for gid in mine - others:
                for hid in sorted(others - mine):
                    if gifts[gid]["repeat"] == gifts[hid]["repeat"] == "repeatable":
                        continue
                    if hid not in gifts[gid]["exclusive_with"]:
                        prob(gid, "one arm of the menu at %s, but exclusive_with lacks the sibling arm's %s" %
                             (where, hid))
    s2_gender(s, gifts, by_label, prob)


def s2_root_conds(s, label):
    """[[condition]] one list per map.json event that starts `label`: the object's hide flag (it is there only while
    the flag is clear) and a coord trigger's var test; [] (no condition) for a sign or an object without a flag."""
    if "root_conds" not in s:
        rc = {}
        for mid, (folder, text) in raw_root_maps(s):
            j = json.loads(text)
            for o in j.get("object_events") or []:
                rc.setdefault(o.get("script"), []).append(
                    [("object", o["flag"], True, "%s object" % mid)] if o.get("flag") not in (None, "0") else [])
            for c in j.get("coord_events") or []:
                if c.get("script"):
                    rc.setdefault(c["script"], []).append([("coord %s %s" % (c.get("var"), c.get("var_value")),
                                                            c.get("var"), True, "%s coord" % mid)])
            for b in j.get("bg_events") or []:
                if b.get("script"):
                    rc.setdefault(b["script"], []).append([])
        s["root_conds"] = rc
    return s["root_conds"].get(label, [])


def raw_root_maps(s):
    return s["maps_raw"].items()


def s2_paths(s, name, n, depth=12, stack=(), cap=64):
    """The verifier's own PATHS into line `n` of `name`, walked BACKWARD over the raw mentions: [[(line, tested name,
    taken, where)]], each a conditional line on the way (taken: the jump into the next label; not taken: a goto_if the
    flow survived), a map.json event's own condition, or a `<map>_MapScripts` entry. None when past `cap` paths."""
    lab = s["labs"][name]
    own = [(ln, s2_tested(ln), False, "%s:%d" % (lab["file"], m)) for m, ln in lab["lines"]
           if m < n and re.match(r"goto_if_\w+ ", ln)]
    out = [p + own for p in s2_root_conds(s, name)]
    if name in s["c_words"] or name.endswith("_MapScripts"):
        out.append(list(own))
    if depth:
        for src, m in s["at"].get(name, ()):
            if src in stack:
                continue
            line = next((ln for k, ln in s["labs"][src]["lines"] if k == m), "")
            mine = [(line, s2_tested(line, s["labs"][src], m), True, "%s:%d" % (s["labs"][src]["file"], m))] \
                if re.match(r"(?:goto|call)_if_\w+ |case |map_script_2 ", line) else []
            sub = s2_paths(s, src, m, depth - 1, stack + (name,), cap)
            if sub is None:
                return None
            out += [p + mine + own for p in sub]
            if len(out) > cap:
                return None
    return out


def s2_tested(line, lab=None, m=None):
    """The flag / var a conditional line tests (a `case` tests the var of the `switch` above it)."""
    w = line.replace(",", " ").split()
    if not w:
        return None
    if w[0] == "case" and lab is not None:
        sw = [ln for k, ln in lab["lines"] if k < m and ln.startswith("switch ")]
        return sw[-1].split()[1] if sw else None
    return w[1] if len(w) > 1 else None


def s2_label_at(s, where):
    """The label holding raw line 'file:line' (an index built once)."""
    if "label_at" not in s:
        s["label_at"] = {(lb["file"], m): k for k, lb in s["labs"].items() for m, _ in lb["lines"]}
        s["file_menu"] = {lb["file"] for lb in s["labs"].values() if any(S2_MENU.match(ln) for _, ln in lb["lines"])}
    if ":" not in where or not where.rsplit(":", 1)[1].isdigit():
        return None
    rel, k = where.rsplit(":", 1)
    return s["label_at"].get((rel, int(k)))


def s2_cond_kept(s, cond, written):
    """Is this path condition a CONDITION `when` must word (not the repeat axis)? Dropped: a TEMP flag/var, a name the
    gift itself writes (its once-guard), and a VAR_RESULT / 0x80xx made by a room check, a yes/no or a constant."""
    line, name, taken, where = cond
    if not name or re.match(r"(FLAG|VAR)_TEMP_", name) or name in written:
        return False
    if line.startswith("case ") and re.match(r"VAR_RESULT$|VAR_0x80", name) and not taken is False:
        # an arm of a switch on a value computed here picks WHAT is given (the berry by trainer ID), not whether
        lab = s["labs"].get(s2_label_at(s, where))  # kept only when a menu made the switched value (a choice)
        lines = [ln for m, ln in (lab or {"lines": []})["lines"] if m < int(where.rsplit(":", 1)[1])]
        sw = max((i for i, ln in enumerate(lines) if ln.startswith("switch ")), default=None)
        return bool(sw) and bool(S2_MENU.match(lines[sw - 1]))
    if re.match(r"VAR_RESULT$|VAR_0x80", name):
        k = where.rsplit(":", 1)[1]
        lab = s["labs"].get(s2_label_at(s, where))
        if lab is not None:
            before = [ln for m, ln in lab["lines"] if m < int(k) and (ln.startswith(("checkitem", "checkpcitem",
                                                                                      "checkdecor", "checkmoney",
                                                                                      "checkcoins", "specialvar",
                                                                                      "special ", "setvar " + name,
                                                                                      "copyvar " + name))
                                                                    or S2_ROOMISH.match(ln) or S2_MENU.match(ln)
                                                                    or S2_ANSWER.match(ln)
                                                                    or ln.startswith(("random", "checkplayergender")))]
            last = before[-1] if before else ""
            # room (the repeat axis) and the player's yes/no answer (a choice on the spot) are no conditions
            if S2_ROOMISH.match(last) or S2_ANSWER.match(last) or last.startswith("setvar " + name):
                return False
    return True


def s2_merge(paths):
    """Two paths differing only by one conditional line taken in one and survived in the other are one path."""
    ps = [frozenset((c[3], c[2]) for c in p) for p in paths]
    full = {(c[3], c[2]): c for p in paths for c in p}
    changed = True
    while changed:
        changed = False
        ps = sorted(set(ps), key=lambda p: (len(p), sorted(p)))
        for i, p in enumerate(ps):
            for q in ps[i + 1:]:
                d1, d2 = p - q, q - p
                if p < q or (len(d1) == len(d2) == 1 and next(iter(d1))[0] == next(iter(d2))[0]):
                    ps.remove(q)
                    if not p < q:
                        ps.remove(p)
                        ps.append(p & q)
                    changed = True
                    break
            if changed:
                break
    return [[full[x] for x in p] for p in ps]


#: fix round 3 (a7): the verifier's OWN list of C code that writes flags or vars by a RANGE or a computed id (a grep of
#: src/ for FlagSet / FlagClear / VarSet / memset on the save flags with an id that is no single name). Membership is
#: by NAME here (the extractor's is by numeric id): (key, a regex over names or a map.json object list, cite). The
#: new-game memset (src/event_data.c:34-35) is the START state, not a writer, so it is not listed.
S2_RANGES = [
    ("daily flags", "DAILY", ("src/event_data.c:52", "memset(&gSaveBlock1Ptr->flags[DAILY_FLAGS_START / 8]")),
    ("temp flags and vars", r"(?:FLAG|VAR)_TEMP_\w+", ("src/event_data.c:41", "TEMP_FLAGS_START / 8")),
    ("match call registrations", r"FLAG_REGISTERED_\w+",
     ("src/pokenav_match_call_data.c:1160", "FlagSet(TRAINER_REGISTERED_FLAGS_START + index);")),
    ("decoration flags", r"FLAG_DECORATION_\d+", ("src/decoration.c:1291", "FlagClear(FLAG_DECORATION_1 + i);")),
    ("hidden item flags", r"FLAG_HIDDEN_ITEM_\w+", ("src/field_specials.c:937", "FlagSet(gSpecialVar_0x8004);")),
    ("union room players", r"FLAG_HIDE_UNION_ROOM_PLAYER_\d+",
     ("src/union_room_player_avatar.c:161", "FlagSet(FLAG_HIDE_UNION_ROOM_PLAYER_1 + player_idx);")),
    ("frontier symbols", r"FLAG_SYS_(?:TOWER|DOME|PALACE|ARENA|FACTORY|PIKE|PYRAMID)_(?:SILVER|GOLD)",
     ("src/frontier_util.c:1922", "FlagSet(FLAG_SYS_TOWER_SILVER + facility * 2);")),
    ("object graphics vars", r"VAR_OBJ_GFX_ID_[0-9A-F]", ("src/union_room_player_avatar.c:171", "VarSet(VAR_OBJ_GFX_ID_0")),
    ("objects removed by C", (("BirthIsland_Exterior", "LOCALID_BIRTH_ISLAND_EXTERIOR_ROCK"),
                              ("BattleFrontier_BattleTowerLobby", "LOCALID_TOWER_LOBBY_REPORTER")),
     ("src/field_effect.c:3734", "RemoveObjectEventByLocalIdAndMap(tLocalId, tMapNum, tMapGroup);")),
]
#: fix round 3 (daily): flags a C function sets every new day and whose `call_if_set` runs a label that clears other
#: flags (the Shoal Cave: SetShoalItemFlag, src/clock.c:53 -> src/field_specials.c:1420): the flags that label clears
#: come back daily, so a gift guarded by one is `daily` though no FLAG_DAILY_ name is on its way
S2_DAILY_SYS = {"FLAG_SYS_SHOAL_ITEM": [("src/clock.c:53", "SetShoalItemFlag(daysSince);"),
                                        ("src/field_specials.c:1420", "FlagSet(FLAG_SYS_SHOAL_ITEM);")]}
#: fix round 3 (a10): the verifier's own list of the specials whose C body was READ (each cited to its definition, the
#: token checked at verify time like the golden cites). A special not here on a gift's way in makes a worded `when` a
#: mismatch; on its continuation, an asserted `repeat`.
S2_SPECIALS = {
    "BufferFavorLadyItemName": ("src/lilycove_lady.c:198", "BufferFavorLadyItemName(void)"),
    "BufferFavorLadyPlayerName": ("src/lilycove_lady.c:210", "BufferFavorLadyPlayerName(void)"),
    "BufferFavorLadyRequest": ("src/lilycove_lady.c:175", "BufferFavorLadyRequest(void)"),
    "BufferQuizAuthorNameAndCheckIfLady": ("src/lilycove_lady.c:457", "BufferQuizAuthorNameAndCheckIfLady(void)"),
    "BufferQuizPrizeItem": ("src/lilycove_lady.c:487", "BufferQuizPrizeItem(void)"),
    "BufferTMHMMoveName": ("src/field_specials.c:1638", "BufferTMHMMoveName(void)"),
    "BufferTrendyPhraseString": ("src/dewford_trend.c:290", "BufferTrendyPhraseString(void)"),
    "ChangeBoxPokemonNickname": ("src/tv.c:3307", "ChangeBoxPokemonNickname(void)"),
    "ChangePokemonNickname": ("src/tv.c:3292", "ChangePokemonNickname(void)"),
    "ChoosePartyMon": ("src/party_menu.c:6262", "ChoosePartyMon(void)"),
    "ClearLinkContestFlags": ("src/contest_util.c:2771", "ClearLinkContestFlags(void)"),
    "ClearQuizLadyPlayerAnswer": ("src/lilycove_lady.c:505", "ClearQuizLadyPlayerAnswer(void)"),
    "ClearQuizLadyQuestionAndAnswer": ("src/lilycove_lady.c:526", "ClearQuizLadyQuestionAndAnswer(void)"),
    "CompareLotadSize": ("src/pokemon_size_record.c:183", "CompareLotadSize(void)"),
    "CompareSeedotSize": ("src/pokemon_size_record.c:164", "CompareSeedotSize(void)"),
    "DidFavorLadyLikeItem": ("src/lilycove_lady.c:218", "DidFavorLadyLikeItem(void)"),
    "DoBerryBlending": ("src/berry_blender.c:1047", "DoBerryBlending(void)"),
    "DoContestHallWarp": ("src/field_screen_effect.c:755", "DoContestHallWarp(void)"),
    "DoMirageTowerCeilingCrumble": ("src/mirage_tower.c:420", "DoMirageTowerCeilingCrumble(void)"),
    "DrawWholeMapView": ("src/field_camera.c:94", "DrawWholeMapView(void)"),
    "FavorLadyGetPrize": ("src/lilycove_lady.c:278", "FavorLadyGetPrize(void)"),
    "GetFavorLadyState": ("src/lilycove_lady.c:159", "GetFavorLadyState(void)"),
    "GetLeadMonFriendshipScore": ("src/field_specials.c:949", "GetLeadMonFriendshipScore(void)"),
    "GetLotadSizeRecordInfo": ("src/pokemon_size_record.c:176", "GetLotadSizeRecordInfo(void)"),
    "GetPCBoxToSendMon": ("src/field_specials.c:3400", "GetPCBoxToSendMon(void)"),
    "GetPlayerBigGuyGirlString": ("src/field_specials.c:906", "GetPlayerBigGuyGirlString(void)"),
    "GetPlayerTrainerIdOnesDigit": ("src/field_specials.c:901", "GetPlayerTrainerIdOnesDigit(void)"),
    "GetQuizAuthor": ("src/lilycove_lady.c:358", "GetQuizAuthor(void)"),
    "GetQuizLadyState": ("src/lilycove_lady.c:347", "GetQuizLadyState(void)"),
    "GetSeedotSizeRecordInfo": ("src/pokemon_size_record.c:157", "GetSeedotSizeRecordInfo(void)"),
    "HasAnotherPlayerGivenFavorLadyItem": ("src/lilycove_lady.c:181", "HasAnotherPlayerGivenFavorLadyItem(void)"),
    "HasEnoughBerryPowder": ("src/berry_powder.c:153", "HasEnoughBerryPowder(void)"),
    "HealPlayerParty": ("src/script_pokemon_util.c:30", "HealPlayerParty(void)"),
    "InitRoamer": ("src/roamer.c:108", "InitRoamer(void)"),
    "IsFavorLadyThresholdMet": ("src/lilycove_lady.c:264", "IsFavorLadyThresholdMet(void)"),
    "IsQuizAnswerCorrect": ("src/lilycove_lady.c:479", "IsQuizAnswerCorrect(void)"),
    "MauvilleGymDeactivatePuzzle": ("src/field_specials.c:727", "MauvilleGymDeactivatePuzzle(void)"),
    "PrintPlayerBerryPowderAmount": ("src/berry_powder.c:217", "PrintPlayerBerryPowderAmount(void)"),
    "QuizLadyGetPlayerAnswer": ("src/lilycove_lady.c:474", "QuizLadyGetPlayerAnswer(void)"),
    "QuizLadyPickNewQuestion": ("src/lilycove_lady.c:516", "QuizLadyPickNewQuestion(void)"),
    "QuizLadyRecordCustomQuizData": ("src/lilycove_lady.c:547", "QuizLadyRecordCustomQuizData(void)"),
    "QuizLadySetCustomQuestion": ("src/lilycove_lady.c:536", "QuizLadySetCustomQuestion(void)"),
    "QuizLadySetWaitingForChallenger": ("src/lilycove_lady.c:559", "QuizLadySetWaitingForChallenger(void)"),
    "QuizLadyShowQuizQuestion": ("src/easy_chat.c:1573", "QuizLadyShowQuizQuestion(void)"),
    "QuizLadyTakePrizeForCustomQuiz": ("src/lilycove_lady.c:542", "QuizLadyTakePrizeForCustomQuiz(void)"),
    "RemoveBerryPowderVendorMenu": ("src/berry_powder.c:234", "RemoveBerryPowderVendorMenu(void)"),
    "ResetHealLocationFromDewford": ("src/field_specials.c:3881", "ResetHealLocationFromDewford(void)"),
    "ResetTrickHouseNuggetFlag": ("src/field_specials.c:1182", "ResetTrickHouseNuggetFlag(void)"),
    "Script_DoesFavorLadyLikeItem": ("src/lilycove_lady.c:259", "Script_DoesFavorLadyLikeItem(void)"),
    "Script_FavorLadyOpenBagMenu": ("src/lilycove_lady.c:224", "Script_FavorLadyOpenBagMenu(void)"),
    "Script_GetLilycoveLadyId": ("src/lilycove_lady.c:115", "Script_GetLilycoveLadyId(void)"),
    "Script_QuizLadyOpenBagMenu": ("src/lilycove_lady.c:511", "Script_QuizLadyOpenBagMenu(void)"),
    "SetContestTrainerGfxIds": ("src/contest_util.c:2294", "SetContestTrainerGfxIds(void)"),
    "SetFavorLadyState_Complete": ("src/lilycove_lady.c:289", "SetFavorLadyState_Complete(void)"),
    "SetPacifidlogTMReceivedDay": ("src/field_specials.c:1566", "SetPacifidlogTMReceivedDay(void)"),
    "SetQuizLadyState_Complete": ("src/lilycove_lady.c:493", "SetQuizLadyState_Complete(void)"),
    "SetQuizLadyState_GivePrize": ("src/lilycove_lady.c:499", "SetQuizLadyState_GivePrize(void)"),
    "ShakeCamera": ("src/field_specials.c:1470", "ShakeCamera(void)"),
    "ShouldReadyContestArtist": ("src/contest_util.c:2367", "ShouldReadyContestArtist(void)"),
    "ShouldShowBoxWasFullMessage": ("src/field_specials.c:3405", "ShouldShowBoxWasFullMessage(void)"),
    "ShouldTryRematchBattle": ("src/battle_setup.c:1839", "ShouldTryRematchBattle(void)"),
    "ShowScrollableMultichoice": ("src/field_specials.c:2254", "ShowScrollableMultichoice(void)"),
    "SwapRegisteredBike": ("src/item.c:572", "SwapRegisteredBike(void)"),
    "TakeBerryPowder": ("src/berry_powder.c:188", "TakeBerryPowder(void)"),
    "TryEnterContestMon": ("src/contest_util.c:1958", "TryEnterContestMon(void)"),
    "TryPutLotteryWinnerReportOnAir": ("src/tv.c:2186", "TryPutLotteryWinnerReportOnAir(void)"),
    "TurnOffTVScreen": ("src/tv.c:869", "TurnOffTVScreen(void)"),
    "TurnOnTVScreen": ("src/tv.c:875", "TurnOnTVScreen(void)"),
}
#: fix round 3 (a10): a re-arm the verifier read by hand, so a `repeatable` record whose way in runs an unread special
#: may still be repeatable when its dev.rearm names this var (the contest hall: the reception sets the state back to 1
#: on every entry, contest_hall.inc:181, and the hall's map_script_2 runs the contest on 1, ContestHall/scripts.inc:58)
S2_REARMED = {"VAR_CONTEST_HALL_STATE": [("data/scripts/contest_hall.inc:181", "setvar VAR_CONTEST_HALL_STATE, 1"),
                                         ("data/maps/ContestHall/scripts.inc:58",
                                          "map_script_2 VAR_CONTEST_HALL_STATE, 1, ContestHall_EventScript_Contest")]}
S2_WRITER = re.compile(r"^(setflag|clearflag|setvar|addvar|subvar|copyvar|setorcopyvar|specialvar|checkcoins)\s+"
                       r"((?:FLAG|VAR)_\w+)\b")


def s2_sole_tables(s, root):
    """The verifier's OWN whole-decomp tables for a7 (fix round 3), built once per root: writers {name: ['file:line']}
    from a grep of EVERY data/ *.inc / *.s file (S2_WRITER, getplayerxy's two vars, and each `removeobject` as a writer
    of the hide flag of every object of that local id, or of every object when it removes through a var, on the maps
    its label reaches); c {name: ['file:line']} every src/ line naming it; alias {name: [names]} from `#define A B`
    lines of flags.h / vars.h; daily {names} between DAILY_FLAGS_START and DAILY_FLAGS_END in flags.h; start {flags set
    by EventScript_ResetAllMapFlags}; rearmed_daily {flags a daily S2_DAILY_SYS label clears}; obj {folder: [(local
    id, flag)]}."""
    if "sole" in s:
        return s["sole"]
    obj, objs = {}, {}
    for mid, (folder, text) in s["maps_raw"].items():
        obj[folder] = [(jfield(o, "local_id"), jfield(o, "flag")) for o in objects_of(text, "object_events")
                       if jfield(o, "flag") not in (None, "0")]
        objs[folder] = [(jfield(o, "local_id"), jfield(o, "flag"), jfield(o, "script"))
                        for o in objects_of(text, "object_events") if jfield(o, "flag") not in (None, "0")]
    folder_of = {mid: folder for mid, (folder, _) in s["maps_raw"].items()}
    writers, rearmed = {}, set()
    for dirpath, _, files in os.walk(os.path.join(root, "data")):
        for fn in files:
            if not fn.endswith((".inc", ".s")):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root).replace("\\", "/")
            label = None
            for n, line in enumerate(s2_strip(open(p, encoding="utf-8", errors="replace").read()), 1):
                t = line.strip()
                m = re.match(r"^([A-Za-z_]\w*)::?$", t)
                if m:
                    label = m.group(1)
                    continue
                where = "%s:%d" % (rel, n)
                w = S2_WRITER.match(t)
                if w:
                    writers.setdefault(w.group(2), []).append(where)
                xy = re.match(r"^getplayerxy\s+(\w+),\s*(\w+)", t)
                if xy:
                    for v in xy.groups():
                        writers.setdefault(v, []).append(where)
                ro = re.match(r"^removeobject\s+(\w+)", t)
                if ro and label in s["labs"]:
                    for mid in s2_owner(s, label)[0]:
                        for lid, flag, script in objs.get(folder_of.get(mid), []):
                            # VAR_LAST_TALKED is the object talked to: one whose own script reaches this line;
                            # any other var could hold any local id of the map
                            if lid == ro.group(1) or (ro.group(1) == "VAR_LAST_TALKED" and
                                                      label in s2_reach(s, [script])) or \
                                    (ro.group(1).startswith("VAR_") and ro.group(1) != "VAR_LAST_TALKED"):
                                writers.setdefault(flag, []).append(where)
                cs = re.match(r"^call_if_set\s+(\w+),\s*(\w+)", t)
                if cs and cs.group(1) in S2_DAILY_SYS and cs.group(2) in s["labs"]:
                    rearmed |= {re.match(r"clearflag (\w+)", x).group(1) for _, x in s["labs"][cs.group(2)]["lines"]
                                if re.match(r"clearflag (\w+)", x) and x.split()[1] not in S2_DAILY_SYS}
    c = {}
    for dirpath, _, files in os.walk(os.path.join(root, "src")):
        for fn in files:
            if fn.endswith((".c", ".h")):
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, root).replace("\\", "/")
                for n, line in enumerate(open(p, encoding="utf-8", errors="replace").read().split("\n"), 1):
                    for name in set(re.findall(r"\b(?:FLAG|VAR)_\w+", line)):
                        c.setdefault(name, []).append("%s:%d" % (rel, n))
    alias, daily, inside = {}, set(), False
    for rel in ("include/constants/flags.h", "include/constants/vars.h"):
        for line in open(os.path.join(root, rel), encoding="utf-8").read().split("\n"):
            m = re.match(r"#define\s+((?:FLAG|VAR)_\w+)\s+((?:FLAG|VAR)_\w+)\s*(?://.*)?$", line)
            if m:
                alias.setdefault(m.group(1), set()).add(m.group(2))
                alias.setdefault(m.group(2), set()).add(m.group(1))
            if re.match(r"#define\s+DAILY_FLAGS_START\b", line):
                inside = True
            elif re.match(r"#define\s+DAILY_FLAGS_END\b", line):
                inside = False
            elif inside:
                d = re.match(r"#define\s+(FLAG_\w+)", line)
                if d:
                    daily.add(d.group(1))
    start = {x.split()[1] for _, x in s["labs"].get("EventScript_ResetAllMapFlags", {"lines": []})["lines"]
             if x.startswith("setflag ")}
    s["sole"] = {"writers": writers, "c": c, "alias": alias, "daily": daily, "start": start, "obj": obj,
                 "rearmed_daily": rearmed}
    return s["sole"]


def s2_target(line, s):
    """The label a branch line jumps or calls to (its last operand, when that is a label), else None."""
    w = line.replace(",", " ").split()
    if len(w) > 1 and re.match(r"(?:goto|call)(?:_if_\w+)?$|case$", w[0]) and w[-1] in s["labs"]:
        return w[-1]
    return None


def s2_cont(s, name, n):
    """Fix round 3 (a7, a10): the verifier's own CONTINUATION of the gift line `n` of `name`: ['file:line'] of every line
    that can run after it. The rest of its label to the first terminator; every label a goto / goto_if / case / call /
    call_if on those lines enters (a callee's `return` ends the callee); the next label when the label runs off its end;
    and after a `return` in the gift's own frame (not a callee's), the lines after each `call` / `call_if` of a label
    whose goto / branch / case / fall chain leads into the gift's label (where that call resumes)."""
    out, seen, todo = [], set(), [(name, n, False)]
    while todo:
        x, after, in_call = todo.pop()
        if (x, after, in_call) in seen or x not in s["labs"]:
            continue
        seen.add((x, after, in_call))
        lab, ended = s["labs"][x], False
        for m, ln in lab["lines"]:
            if m <= after:
                continue
            out.append(("%s:%d" % (lab["file"], m), ln))
            tgt = s2_target(ln, s)
            if tgt:
                todo.append((tgt, 0, in_call or ln.startswith("call")))
            if ln.split()[0] in S2_ENDS:
                if ln.split()[0] == "return" and not in_call:
                    todo += [(src, m2, False) for src, m2 in s2_frame_calls(s, x)]
                ended = True
                break
        if not ended:
            todo += [(w, 0, in_call) for w, m in s["fwd"].get(x, ()) if m == 10 ** 9]
    return out


def s2_frame_calls(s, name):
    """[(label, line)] of each call / call_if whose callee leads into `name` by gotos, branches, cases or falls."""
    out, seen, todo = set(), set(), [name]
    while todo and len(seen) < 4000:
        x = todo.pop()
        if x in seen:
            continue
        seen.add(x)
        for src, m in s["at"].get(x, ()):
            line = "" if m == 10 ** 9 else next((ln for k, ln in s["labs"][src]["lines"] if k == m), "")
            if m == 10 ** 9 or re.match(r"goto(?:_if_\w+)?\s|case\s", line):
                todo.append(src)
            elif re.match(r"call(?:_if_\w+)?\s", line) and s2_target(line, s) == x:
                out.add((src, m))
    return sorted(out)


def s2_names_of(t, name):
    """`name` and every name a `#define A B` chain makes the same flag / var."""
    seen, todo = set(), [name]
    while todo:
        x = todo.pop()
        if x not in seen:
            seen.add(x)
            todo += sorted(t["alias"].get(x, ()))
    return sorted(seen)


def s2_outside_writers(s, root, name, own):
    """a7's scan for one blocking name: every writer of it (or an alias) the gift's own continuation `own` does not
    hold: a script writer, a src/ line naming it, a C range by name."""
    t = s2_sole_tables(s, root)
    out = []
    for nm in s2_names_of(t, name):
        out += ["script %s" % w for w in t["writers"].get(nm, []) if w not in own]
        out += ["C %s" % w for w in t["c"].get(nm, [])]
        for key, pat, (cite, _) in S2_RANGES:
            if pat == "DAILY":
                hit = nm in t["daily"]
            elif isinstance(pat, str):
                hit = re.fullmatch(pat, nm) is not None
            else:
                hit = any(nm == f for folder, lid in pat for lid2, f in t["obj"].get(folder, []) if lid2 == lid)
            if hit:
                out.append("C range %s (%s)" % (key, cite))
    return out


def s2_item_sources(s, root, item):
    """Every line of data/ that GIVES `item` (giveitem / finditem / additem, a `.2byte` mart entry) and every map.json
    hidden item of it: the verifier's count of where the item comes from."""
    t = s2_sole_tables(s, root)
    if "items" not in t:
        src = {}
        for name, lab in s["labs"].items():
            for n, ln in lab["lines"]:
                m = re.match(r"^(?:giveitem|finditem|additem|\.2byte)\s+(ITEM_\w+)", ln)
                if m:
                    src.setdefault(m.group(1), []).append("%s:%d" % (lab["file"], n))
        for mid, (folder, text) in s["maps_raw"].items():
            for b in objects_of(text, "bg_events"):
                if jfield(b, "item"):
                    src.setdefault(jfield(b, "item"), []).append("%s hidden" % mid)
        t["items"] = src
    return t["items"].get(item, [])


def s2_false_at_start(s, root, cond):
    """Is this path condition FALSE at new game? (line, name, taken, where): a flag starts clear unless
    EventScript_ResetAllMapFlags sets it; a var starts 0. True / False / None (a value this cannot read)."""
    line, name, taken, where = cond
    t = s2_sole_tables(s, root)
    w = line.replace(",", " ").split()
    if not w or not name:
        return None
    if w[0] == "object" or line.startswith("coord "):
        if w[0] == "object":
            return name in t["start"]  # the giver must be there: its hide flag clear
        k = w[2] if len(w) > 2 else None
        op = "eq"
    elif re.match(r"(?:goto|call)_if_(set|unset)$", w[0]):
        want_set = (w[0].endswith("_set")) == bool(taken)
        return want_set != (name in t["start"])
    elif re.match(r"(?:goto|call)_if_(eq|ne|lt|le|gt|ge)$", w[0]):
        op = w[0].rsplit("_", 1)[1]
        if not taken:
            op = {"eq": "ne", "ne": "eq", "lt": "ge", "ge": "lt", "gt": "le", "le": "gt"}[op]
        k = w[2] if len(w) > 2 else None
    elif w[0] in ("map_script_2", "case"):
        op, k = "eq", (w[2] if w[0] == "map_script_2" else w[1])
    else:
        return None
    if k is None:
        return None
    v = {"TRUE": 1, "FALSE": 0, "ITEM_NONE": 0}.get(k)
    if v is None:
        try:
            v = int(k, 0)
        except ValueError:
            return None
    holds = {"eq": 0 == v, "ne": 0 != v, "lt": 0 < v, "le": 0 <= v, "gt": 0 > v, "ge": 0 >= v}[op]
    return not holds


def s2_specials_in(lines):
    """The special functions named by `special Fn` / `specialvar V, Fn` lines."""
    out = set()
    for ln in lines:
        m = re.match(r"^special\s+(\w+)|^specialvar\s+\w+,\s*(\w+)", ln)
        if m:
            out.add(m.group(1) or m.group(2))
    return out


def s2_rules_round2(s, gid, g, name, prob, root=None):
    """Fix round 2's rules (a5, a6) and fix round 3's (a7 rewritten, a9, a10), each re-derived from the raw text:
    a5  'no condition beyond `repeat`' while EVERY path makes a condition (a trigger's own included: the giver's hide
        flag, a coord var, a map_script_2 var) is a mismatch;
    a6  a possession check (checkitem / checkpcitem / checkdecor X, checkmoney / checkcoins N) on every path that a
        worded `when` does not name is a mismatch;
    a7  (fix round 3: the SOLE-WRITER scan, over EVERY `once` / `until_received` record) the record must name its
        blocking flag/var in dev.blocked_by, and each named one must have NO writer outside the gift's own
        continuation (s2_cont: every line that can run after the gift line, no depth bound): no `setflag / clearflag /
        setvar / addvar / subvar / copyvar / setorcopyvar / specialvar / checkcoins / getplayerxy` line of it (or of an alias) in any data/ script file, no
        `removeobject` of an object carrying it, no src/ line naming it, no C range covering it (S2_RANGES); an ITEM:
        blocker must have exactly one source (s2_item_sources). Anything else is a mismatch;
    a9  'no condition beyond `repeat`' while every path tests a flag/var the gift ITSELF writes at a value that is
        FALSE at new game (a precondition, never the once-guard: the owed lottery prize) is a mismatch;
    a10 a special not in S2_SPECIALS on the way in (s2_before, 12 labels back) with a non-null `when`, or with a
        `repeatable` not re-armed by an S2_REARMED var; or on the continuation (s2_cont) with any `repeat` but
        `unknown`, is a mismatch."""
    root = root or s.get("root")
    n = int(g["ref"].rsplit(":", 1)[1])
    after = s2_after(s, name, n)
    written = {S2_SETTER.match(ln).group(2) for _, ln in after if S2_SETTER.match(ln)}
    written |= {re.match(r"setflag (\w+)", ln).group(1) for m, ln in s["labs"][name]["lines"]
                if m < n and re.match(r"setflag (\w+)", ln)}
    if any(ln.startswith("removeobject ") for _, ln in after):  # removing the giver sets its hide flag
        written |= {c[1] for x in s2_owner(s, name)[2] for p in s2_root_conds(s, x) for c in p if c[0] == "object"}
    # a10 first: it needs no path walk
    before_lines = s2_before(s, name, n, 12)
    # a label CALLED on the way in runs its body before the gift too (the Berry Master's wife's easy-chat screen)
    called = [s2_target(ln, s) for ln in before_lines if ln.startswith("call") and s2_target(ln, s)]
    before_lines = before_lines + [ln for x in s2_reach(s, called) for _, ln in s["labs"][x]["lines"]]
    unread_in = sorted(s2_specials_in(before_lines) - set(S2_SPECIALS))
    cont = s2_cont(s, name, n)
    unread_after = sorted(s2_specials_in([ln for _, ln in cont]) - set(S2_SPECIALS))
    rearmed = {w["writes"] for w in g["dev"].get("rearm") or []} & set(S2_REARMED)
    if unread_in and (g["when"] is not None or (g["repeat"] == "repeatable" and not rearmed)):
        prob(gid, "a special the verifier has not read (%s) runs on the way in, but `when` is %r and repeat %s" %
             (", ".join(unread_in), g["when"], g["repeat"]))
    if unread_after and g["repeat"] != "unknown":
        prob(gid, "a special the verifier has not read (%s) runs after the gift, but repeat is %s" %
             (", ".join(unread_after), g["repeat"]))
    if g["repeat"] in ("once", "until_received") and root:
        own = {where for where, _ in cont}
        blockers = [b.split(" = ", 1)[0] for b in g["dev"].get("blocked_by") or []]
        if not blockers:
            prob(gid, "%s, but dev.blocked_by names no blocking flag/var a scan can check" % g["repeat"])
        for b in blockers:
            if b.startswith("ITEM:"):
                src = s2_item_sources(s, root, b[5:])
                if len(src) != 1:
                    prob(gid, "%s, but its blocker %s has %d sources (%s)" % (g["repeat"], b, len(src), src[:3]))
            elif re.fullmatch(r"(?:FLAG|VAR)_\w+", b):
                other = s2_outside_writers(s, root, b, own)
                if other:
                    prob(gid, "%s, but %s has a writer outside its own continuation: %s" %
                         (g["repeat"], b, "; ".join(other[:3])))
            else:
                prob(gid, "%s, but its blocker %s is no flag or var a scan can check" % (g["repeat"], b))
    raw = s2_paths(s, name, n)
    if raw is None:
        return
    paths = s2_merge([[c for c in p if s2_cond_kept(s, c, written)] for p in raw])
    if g["when"] == "no condition beyond `repeat`" and paths and all(paths):
        prob(gid, "'no condition', but every path makes one (e.g. %r at %s)" % (paths[0][0][0], paths[0][0][3]))
    if g["when"] == "no condition beyond `repeat`" and raw and root:
        pre = [[c for c in p if c[1] in written and s2_false_at_start(s, root, c) is True] for p in raw]
        if all(pre):
            prob(gid, "'no condition', but every path tests a value the gift itself writes that is FALSE at new game "
                      "(a precondition, not its once-guard), e.g. %r at %s" % (pre[0][0][0], pre[0][0][3]))
    if g["when"] and paths and all(paths):
        haves = [{s2_have_word(x) for x in s2_have_lines(s, p)} for p in raw]
        common = set.intersection(*haves) if haves and all(haves) else set()
        for what, word in sorted(common):
            if word not in g["when"].lower():
                prob(gid, "a %s possession check on every path, but `when` %r does not name it" % (what, g["when"]))


def s2_have_word(line):
    """(what is checked, the word `when` must hold) of a possession-check line: an item or decoration by its name
    (ITEM_SHOAL_SALT -> 'shoal salt'), money as 'money', coins as 'coins' (fix round 3: S2_HAVE grew the last three)."""
    m = S2_HAVE.match(line)
    if m.group(1):
        return m.group(1), m.group(1).split("_", 1)[1].replace("_", " ").lower()
    word = "money" if line.startswith("checkmoney") else "coins"
    return "%s %s" % (word, m.group(2)), word


def s2_have_lines(s, path):
    """The possession-check lines right before each conditional of a path (the line the test reads)."""
    out = []
    for line, name, taken, where in path:
        if name != "VAR_RESULT" or ":" not in where:
            continue
        lb = s["labs"].get(s2_label_at(s, where))
        if lb is not None:
            prev = [ln for m, ln in lb["lines"] if m < int(where.rsplit(":", 1)[1])]
            if prev and S2_HAVE.match(prev[-1]):
                out.append(prev[-1])
    return out


def s2_gender(s, gifts, by_label, prob):
    """a8: the gifts on the two arms of a `checkplayergender` test (`(goto|call)_if_eq VAR_RESULT, MALE / FEMALE`)
    are one gift by the player's gender: each must be exclusive_with the other arm's."""
    for name, lab in s["labs"].items():
        lines = lab["lines"]
        for i, (m, ln) in enumerate(lines):
            if ln.strip() != "checkplayergender":
                continue
            arms = {}
            for _, ln2 in lines[i + 1:i + 3]:
                g2 = re.match(r"(?:goto|call)_if_eq VAR_RESULT,\s*(MALE|FEMALE),\s*(\w+)", ln2)
                if g2:
                    arms[g2.group(1)] = {gid for x in s2_reach(s, [g2.group(2)], stop=name)
                                         for gid in by_label.get(x, ())}
            if len(arms) == 2:
                for a, b in (("MALE", "FEMALE"), ("FEMALE", "MALE")):
                    for gid in sorted(arms[a] - arms[b]):
                        for hid in sorted(arms[b] - arms[a]):
                            if hid not in gifts[gid]["exclusive_with"]:
                                prob(gid, "one arm of the gender test at %s:%d, but exclusive_with lacks %s" %
                                     (lab["file"], m, hid))


def s2_table_cites(r, prob):
    """Fix round 3: every cite of the verifier's own hand tables (S2_RANGES, S2_DAILY_SYS, S2_SPECIALS, S2_REARMED)
    still holds its token at the pin, so a moved pin fails loudly instead of leaving a stale rule."""
    cites = [("S2_RANGES " + k, c) for k, _, c in S2_RANGES]
    cites += [("S2_DAILY_SYS " + k, c) for k, v in S2_DAILY_SYS.items() for c in v]
    cites += [("S2_SPECIALS " + k, c) for k, c in S2_SPECIALS.items()]
    cites += [("S2_REARMED " + k, c) for k, v in S2_REARMED.items() for c in v]
    for key, (where, token) in cites:
        line = line_at(r, where)
        if line is None or token not in line:
            prob("table " + key, "cite %s no longer holds %r at the pin" % (where, token))


def s2_golden(r, items, prob):
    """(b) each S2_GOLDEN entry: its cited lines still hold their tokens at the pin, and the record says what was read
    off the decomp by hand."""
    gifts = {g["id"]: g for g in items["gifts"]}
    lists = {(m["id"], lst["label"]): lst for m in items["marts"] for lst in m["lists"]}
    for e in S2_GOLDEN:
        key = e.get("id") or "mart %s %s" % (e["mart"], e["list"])
        for where, token in e["cites"]:
            line = line_at(r, where)
            if line is None or token not in line:
                prob(key, "golden cite %s no longer holds %r at the pin" % (where, token))
        if "mart" in e:
            lst = lists.get((e["mart"], e["list"]))
            setters = (lst or {}).get("dev", {}).get("setters") or []
            hit = [x for x in setters if x["ref"] == e["setter"] and e["reached_by"] in x["reached_by"]]
            if not hit:
                prob(key, "dev.setters lacks %s reached by %s" % (e["setter"], e["reached_by"]))
            continue
        g = gifts.get(e["id"])
        if g is None:
            prob(key, "the golden record is missing")
            continue
        w = g["what"] if isinstance(g["what"], dict) else {}
        for k, have in (("repeat", g["repeat"]), ("chosen_by", w.get("chosen_by")), ("one_of", w.get("one_of")),
                        ("exclusive_with", g["exclusive_with"]), ("when", g["when"]),
                        ("givers", sorted({x["kind"] for x in g["giver"]}))):
            if k in e and have != e[k]:
                prob(key, "%s %r, the decomp read by hand says %r" % (k, have, e[k]))
        for t in e.get("tests", ()):
            if t not in g["dev"]["tests"]:
                prob(key, "dev.tests lacks %r" % t)
        if "words_has" in e and e["words_has"] not in (w.get("words") or ""):
            prob(key, "what.words lacks %r" % e["words_has"])
        if "when_has" in e and e["when_has"] not in (g["when"] or ""):
            prob(key, "when %r lacks %r" % (g["when"], e["when_has"]))
        # fix round 3: a record the sole-writer rule leaves `unknown` names the outside writer read here by hand
        if "other_writer" in e:
            where, token = e["other_writer"]
            line = line_at(r, where)
            seen = " ".join((g["dev"].get("other_writers") or []) + (g["dev"].get("c_uses") or []))
            if line is None or token not in line:
                prob(key, "golden other_writer %s no longer holds %r at the pin" % (where, token))
            elif where not in seen:
                prob(key, "dev.other_writers / c_uses lack the outside writer %s" % where)
        if "why_has" in e and e["why_has"] not in (g["dev"].get("repeat_why") or ""):
            prob(key, "dev.repeat_why %r lacks %r" % (g["dev"].get("repeat_why"), e["why_has"]))


def verify_items(root, items, maps_doc, rep):
    """Every check of items_gifts.json (stage 2a). Mismatches go to `rep` (kind 'items')."""
    s, rr = s2_raw(root), raw(root)
    labs = s["labs"]
    gifts = {g["ref"]: g for g in items["gifts"]}
    want, eon = {}, set()
    for name, k, where, cmd_, opnd in s2_lines(s, S2_GIFTS):
        maps, c, way = s2_owner(s, name)
        if any("ShouldDistributeEonTicket" in ln for x in way for _, ln in labs[x]["lines"]):
            eon.add(where)  # R-3: the record-mixing Eon Ticket
            continue
        if maps or c:
            want[where] = (name, k, cmd_, opnd, maps)
    rep.seen("items_gift_lines", len(want))
    for where, g in gifts.items():
        if where not in want:
            rep.mismatch("items", "gift %s" % g["id"], "%s is not a reachable gift command line" % where)
            continue
        name, k, cmd_, opnd, maps = want[where]
        if g["id"] != "%s:%d" % (name, k):
            rep.mismatch("items", "gift %s" % g["id"], "the line is gift %d of %s" % (k, name))
        if sorted(maps) != g["maps"]:
            rep.mismatch("items", "gift %s" % g["id"], "maps %s, the backward walk finds %s" % (g["maps"], sorted(maps)))
        if not opnd.startswith("VAR_") and g["what"] != opnd:
            rep.mismatch("items", "gift %s" % g["id"], "what %r, the line gives %s" % (g["what"], opnd))
        # fix round 3: or a flag a daily C function's call_if_set label clears is tested on its way (the Shoal Cave)
        way = s2_before(s, name, int(where.rsplit(":", 1)[1]), 4)
        rearmed = s2_sole_tables(s, root)["rearmed_daily"]
        daily = any(S2_DAILY.search(ln) for ln in way) or any(
            re.match(r"(?:goto|call)_if_(?:set|unset)\s+(\w+)", ln) and
            re.match(r"(?:goto|call)_if_(?:set|unset)\s+(\w+)", ln).group(1) in rearmed for ln in way)
        if daily != (g["repeat"] == "daily"):
            rep.mismatch("items", "gift %s" % g["id"], "repeat %s, a daily test (a FLAG_DAILY_ name, or a flag a daily "
                         "C function's label clears) %s on its way" %
                         (g["repeat"], "is" if daily else "is not"))
    for where in sorted(set(want) - set(gifts)):
        rep.mismatch("items", "gift %s" % where, "a reachable gift command line with no gift record")

    def prob(key, what):
        rep.mismatch("items", key if key.startswith("mart ") else "gift %s" % key, what)
    # fix round 1: the rule checks (a) and the golden list (b); before them the verifier never read repeat, when,
    # chosen_by or one_of of a var-valued record (round 0's verdict: plants on them reported 0 mismatches)
    s2_rules(s, items, want, prob)
    s2_golden(rr, items, prob)
    s2_table_cites(rr, prob)
    rep.seen("items_golden", len(S2_GOLDEN))
    # (h2) the object-hide exclusivity: the gift's label sets the map.json flag of another object whose label gives
    by_label = {}
    for g in items["gifts"]:
        by_label.setdefault(g["id"].rsplit(":", 1)[0], []).append(g["id"])
    for g in items["gifts"]:
        name = g["id"].rsplit(":", 1)[0]
        for flag in re.findall(r"setflag (FLAG_\w+)", "\n".join(ln for _, ln in labs[name]["lines"])):
            for mid in g["maps"]:
                for o in objects_of(rr["maps"][mid][1], "object_events"):
                    if jfield(o, "flag") == flag and jfield(o, "script") in by_label and jfield(o, "script") != name:
                        for other in by_label[jfield(o, "script")]:
                            if other not in g["exclusive_with"]:
                                rep.mismatch("items", "gift %s" % g["id"], "taking it hides %s's object (%s) but "
                                             "exclusive_with lacks %s" % (jfield(o, "script"), flag, other))
    # dead: watched lines no root reaches
    dead_want = set()
    for name, k, where, cmd_, opnd in s2_lines(s, S2_WATCH):
        maps, c, _ = s2_owner(s, name)
        if not maps and not c:
            dead_want.add(where)
    dead_have = {x["line"] for x in items["dead"]}
    if dead_want != dead_have:
        rep.mismatch("items", "dead", "missing %s, extra %s" % (sorted(dead_want - dead_have),
                                                              sorted(dead_have - dead_want)))
    rep.seen("items_dead", len(dead_want))
    if not items["dead"] or not items["excluded"]:
        rep.mismatch("items", "dead/excluded", "an empty list (the recon names dead and excluded lines)")
    # marts: the pokemart operand to its .2byte list
    lines, live = {}, set()
    for name, k, where, cmd_, opnd in s2_lines(s, ("pokemart", "pokemartdecoration", "pokemartdecoration2")):
        lines[where] = opnd
        if any(s2_owner(s, name)[:2]):
            live.add(where)
    seen_refs = set()
    for m in items["marts"]:
        for lst in m["lists"]:
            seen_refs.add(lst["ref"])
            opnd = lines.get(lst["ref"])
            if opnd != lst["label"]:
                rep.mismatch("items", "mart %s" % m["id"], "%s is not a pokemart line of %s" % (lst["ref"], lst["label"]))
                continue
            got = []
            for _, ln in labs[opnd]["lines"]:
                w = ln.split()
                if w[0] == "pokemartlistend" or (w[0] == ".2byte" and w[1] in ("ITEM_NONE", "DECOR_NONE", "0")):
                    break
                if w[0] == ".2byte":
                    got.append(w[1])
            if got != lst["items"]:
                rep.mismatch("items", "mart %s" % m["id"], "list %s holds %s, the output %s" % (opnd, got, lst["items"]))
    if live - seen_refs:
        rep.mismatch("items", "marts", "pokemart lines with no list: %s" % sorted(live - seen_refs)[:5])
    rep.seen("items_mart_lists", len(seen_refs))
    # tm_hm's maps.json pointers, and every TM/HM item ball and hidden TM listed
    by_id = {mp["id"]: mp for mp in maps_doc["maps"]}
    pointed = set()
    for row in items["tm_hm"]:
        for src in row["sources"]:
            for kind in ("field_item", "hidden_item"):
                if kind in src:
                    p = src[kind]["maps_json"]
                    lst = by_id.get(p["map"], {}).get(p["list"]) or []
                    if p["index"] >= len(lst) or lst[p["index"]]["item"] != row["item"]:
                        rep.mismatch("items", "tm_hm %s" % row["item"], "pointer %s does not hold it" % p)
                    pointed.add((p["map"], p["list"], p["index"]))
    for mp in maps_doc["maps"]:
        for lst in ("item_balls", "hidden_items"):
            for i, it in enumerate(mp.get(lst) or []):
                if re.match(r"ITEM_(TM|HM)_", it["item"]) and it["item"] != "ITEM_TM_CASE" and \
                        (mp["id"], lst, i) not in pointed:
                    rep.mismatch("items", "tm_hm %s" % it["item"], "%s %s[%d] is not listed" % (mp["id"], lst, i))
    # R-4 / R-6 on the whole file
    hits = s2_key_hits(items)
    if hits:
        rep.mismatch("items", "R-4", "flag/var names outside dev: %s" % hits[:5])
    rk = route_keys(items)
    if rk:
        rep.mismatch("items", "R-6", "route keys %s" % rk[:5])
    rep.seen("items_eon_excluded", len(eon))


def s2_plant(items, name):
    """Apply one stage-2a plant to `items` (in memory); returns the report prefix it must produce."""
    gifts = items["gifts"]
    if name == "e":
        g = next(x for x in gifts if x["id"].startswith("RustboroCity_Gym_EventScript_GiveRockTomb"))
        g["maps"] = ["MAP_ROUTE101"]
        return "MISMATCH items gift %s:" % g["id"]
    if name == "g":
        gifts.append({"id": "AquaHideout_B2F_EventScript_ItemMasterBall:1", "maps": ["MAP_AQUA_HIDEOUT_B2F"],
                      "kind": "item", "what": "ITEM_MASTER_BALL", "repeat": "once", "exclusive_with": [],
                      "when": "no condition beyond `repeat`", "dev": {}, "ref": "data/scripts/item_ball_scripts.inc:530"})
        return "MISMATCH items gift AquaHideout_B2F_EventScript_ItemMasterBall:1:"
    if name == "h":
        g = next(x for x in gifts if x["id"].startswith("LilycoveCity_EventScript_BerryGentleman"))
        g["repeat"] = "once"
        return "MISMATCH items gift %s:" % g["id"]
    if name == "h2":
        g = next(x for x in gifts if x["id"].startswith("MirageTower_4F_EventScript_RootFossil"))
        g["exclusive_with"] = []
        return "MISMATCH items gift %s:" % g["id"]
    if name == "i":
        m = next(x for x in items["marts"] if x["id"] == "OldaleTown_Mart_EventScript_Clerk")
        m["lists"][1]["items"] = m["lists"][1]["items"][:-1]
        return "MISMATCH items mart %s:" % m["id"]
    if name == "j":
        gifts.append({"id": "AquaHideout_B1F_EventScript_Electrode1:1", "maps": ["MAP_AQUA_HIDEOUT_B1F"],
                      "kind": "item", "what": "ITEM_POKE_BALL", "repeat": "once", "exclusive_with": [],
                      "when": "no condition beyond `repeat`", "dev": {}, "ref": None})
        lab = s2_raw_any()["labs"]["AquaHideout_B1F_EventScript_Electrode1"]
        gifts[-1]["ref"] = "%s:%d" % (lab["file"], lab["lines"][0][0])
        return "MISMATCH items gift AquaHideout_B1F_EventScript_Electrode1:1:"
    if name == "k":
        g = gifts[0]
        g["flag"] = (g["dev"].get("flags") or ["FLAG_RECEIVED_TM_BULLET_SEED"])[0]
        return "MISMATCH items R-4:"
    by_id = {x["id"]: x for x in gifts}
    if name == "l":  # F1: HM Surf's setvar/setflag after the gift ignored
        g = by_id["PetalburgCity_WallysHouse_EventScript_GiveHMSurf:1"]
        g["repeat"] = "repeatable"
    elif name == "m":  # F4: the Favor Lady's random prize called a choice
        g = by_id["LilycoveCity_PokemonCenter_1F_EventScript_FavorLadyPrize:1"]
        g["what"]["chosen_by"] = "choice"
    elif name == "n":  # the lottery's prize set collapsed to one item
        g = by_id["LilycoveCity_DepartmentStore_1F_EventScript_LotteryClerk:1"]
        g["what"]["one_of"] = g["what"]["one_of"][:1]
    elif name == "o":  # F3: the Deep Sea Tooth no longer excludes the Scale
        g = by_id["SlateportCity_Harbor_EventScript_DeepSeaTooth:1"]
        g["exclusive_with"] = []
    elif name == "p":  # F2: HM Surf's map_script_2 test dropped
        g = by_id["PetalburgCity_WallysHouse_EventScript_GiveHMSurf:1"]
        g["dev"]["tests"] = [t for t in g["dev"]["tests"] if not t.startswith("VAR_PETALBURG_CITY_STATE")]
    elif name == "q":  # F2: the phantom map_script giver back on the Route 114 berry man
        g = by_id["Route114_EventScript_Man:1"]
        g["giver"] = g["giver"] + [{"map": "MAP_ROUTE114", "kind": "map_script"}]
    # fix round 2: one plant per rule a1..a8, each on a record the golden list does NOT hold, so only the RULE reports
    elif name == "a1":  # a repeatable gift whose setflag runs after it, citing no re-arm
        g = by_id["FortreeCity_Gym_EventScript_GiveAerialAce:1"]
        g["repeat"] = "repeatable"
    elif name == "a2":  # a menu arm without its sibling
        g = by_id["Route110_TrickHouseEntrance_EventScript_GiveBlueTent:1"]
        g["exclusive_with"] = []
    elif name == "a3":  # a map_script giver no map script reaches
        g = by_id["Route116_EventScript_GiveRepeatBall:1"]
        g["giver"] = g["giver"] + [{"map": "MAP_ROUTE116", "kind": "map_script"}]
    elif name == "a4":  # a var-valued giveitem without chosen_by
        g = by_id["Route120_EventScript_GiveBerry:1"]
        g["what"] = {"one_of": ["ITEM_FIGY_BERRY"]}
    elif name == "a5":  # 'no condition' over a gift every path of which is gated
        g = by_id["PetalburgWoods_EventScript_DevonResearcherPostBattle:1"]
        g["when"] = "no condition beyond `repeat`"
    elif name == "a6":  # a worded `when` that leaves out the possession every path checks (fix round 3: the Lava
        # Cookie's 200 money, a checkmoney S2_HAVE now reads; Cozmo's Meteorite moved to the golden list)
        g = by_id["MtChimney_EventScript_LavaCookieLady:1"]
        g["when"] = "the giver is not there at first: they appear later in the story"
    elif name == "a7":  # until_received although its own continuation writes the trigger's value back (fix round 3:
        # its blocked_by names nothing the sole-writer scan can check)
        g = by_id["Route113_GlassWorkshop_EventScript_GiveGlassDecor:1"]
        g["repeat"] = "until_received"
    elif name == "a7s":  # fix round 3: until_received over a blocking flag another script also writes (round 2's
        # Shoal Cave failure, on a record the golden list does not hold: Brawly's TM, set again at :174)
        g = by_id["DewfordTown_Gym_EventScript_GiveBulkUp2:1"]
        g["repeat"] = "until_received"
        g["dev"]["blocked_by"] = ["FLAG_RECEIVED_TM_BULK_UP = set (data/maps/DewfordTown_Gym/scripts.inc:174)"]
    elif name == "a9":  # fix round 3: 'no condition' over a test of its own var that is FALSE at new game
        g = by_id["RusturfTunnel_EventScript_ClearTunnelScene:1"]
        g["when"] = "no condition beyond `repeat`"
    elif name == "a10":  # fix round 3: a worded `when` over a special the verifier has not read (ShowEasyChatScreen)
        g = by_id["Route123_BerryMastersHouse_EventScript_GiveNormalBerry:1"]
        g["when"] = "after badge 1"
    elif name == "d3":  # fix round 3: a Shoal Cave shell re-armed daily (the Shell Bell man's reset) said repeatable
        g = by_id["ShoalCave_LowTideInnerRoom_EventScript_ShoalShell3:1"]
        g["repeat"] = "repeatable"
    elif name == "gw":  # fix round 3: a golden `unknown` whose outside writer the record no longer names
        g = by_id["LilycoveCity_DepartmentStore_1F_EventScript_GivePrizeFromEarlier:1"]
        g["dev"]["other_writers"] = []
    elif name == "a8":  # one arm of a gender test without the other arm's gift
        g = by_id["LavaridgeTown_EventScript_MayGiveGoGoggles:1"]
        g["exclusive_with"] = []
    else:
        raise KeyError(name)
    return "MISMATCH items gift %s:" % g["id"]


def s2_raw_any():
    return next(iter(_S2.values()))


def load_items(data_dir):
    p = os.path.join(data_dir, S2_FILE)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def s2_plant_result(root, data_dir, name):
    """(ok, lines, prefix): ok iff the plant is reported on exactly ONE line, its own (every problem of a record is
    joined onto that record's one line), and nothing else is reported."""
    items, maps_doc = load_items(data_dir), load(data_dir)["maps"]
    s2_raw(root)
    prefix = s2_plant(items, name)
    rep = Report()
    verify_items(root, items, maps_doc, rep)
    return len(rep.lines) == 1 and rep.lines[0].startswith(prefix), rep.lines, prefix


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
    root = next(k for k, v in _RAW.items() if v is r)
    if load_items(data_dir) is not None:
        rep2 = Report()
        verify_items(root, load_items(data_dir), load(data_dir)["maps"], rep2)
        results.append(("S2 CONTROL: items_gifts.json, %d mismatches (%s)" % (len(rep2.lines), rep2.counts),
                        not rep2.lines))
        for name in S2_PLANTS:
            ok, lines, prefix = s2_plant_result(root, data_dir, name)
            results.append(("S2 FAULT (%s): %s reported" % (name, prefix.strip(":")), ok))
    for name, good in results:
        print("[%s] %s" % ("PASS" if good else "FAIL", name))
    return all(g for _, g in results)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--decomp")
    ap.add_argument("--data", default=DATA_DEFAULT)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--plant", nargs="?", const="w2", choices=("w2",) + S2_PLANTS,
                    help="w2 (alone: slice 1's four plants) or one stage-2a plant of items_gifts.json")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--knowledge", default=KNOWLEDGE, help="the tree W1 scans (default ai_player/knowledge)")
    a = ap.parse_args(argv)
    try:
        root = pinned_root(a.decomp)
        r = raw(root)
    except Refused as exc:
        print("[VERIFY-WORLD] REFUSED:", exc)
        return 2
    if a.plant in S2_PLANTS:
        ok, lines, prefix = s2_plant_result(root, a.data, a.plant)
        for ln in lines:
            print(ln)
        print("[VERIFY-WORLD] PLANT %s %s: %s reported (%d lines)" % (a.plant, "PASS" if ok else "FAIL",
                                                                     prefix, len(lines)))
        return 0 if ok else 1
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
    data = load(a.data)
    rep, n = verify(r, data, milestones, seed)
    items = load_items(a.data)
    if items is not None:
        verify_items(root, items, data["maps"], rep)  # stage 2a: always every record (it is one file)
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
