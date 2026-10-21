#!/usr/bin/env python3
"""Independent verifier for ai_player/knowledge/seasoned/*.json (USER RULING 40).

Deliberately does NOT import extract_seasoned.py and does NOT use its parser:
every expected value is re-derived by regex / line scanning over the raw decomp text.

  python3 ai_player/gates/verify_seasoned.py --decomp /tmp/pokeemerald [--seed N] [--data DIR]
  python3 ai_player/gates/verify_seasoned.py --decomp /tmp/pokeemerald --selftest

--selftest plants wrong values in a temp copy of the data and requires each to be caught, and runs the same check on
the untouched data as its CONTROL (it must pass). Since 2026-10-21 the plants include each KB1 semantic error that was
fixed in encounters.json (F-1, F-2, F-4, F-5, F-6, plus a leaking normal-play index and a false citation), checked
by check_availability, which re-derives every table's availability from the raw decomp in its own way.
Since the KB1 step-5 review (2026-10-21) check_progression also re-derives, without the extractor's gate list: which
tables are reached only after the Hall of Fame (a forward walk from the new-game start over warps, connections and
map scripts, with FLAG_SYS_GAME_CLEAR unset and set, plus a layout flood fill for blockers only the Hall of Fame
removes), which table methods exist only in a swapped layout (an encounter-tile census of every layout a map's
scripts load), the Feebas rule, and the facts the encounter-rate, ability and held-item notes state. Its plants put
each fixed error back (PROG_PLANTS). The species reader accepts the LAST species block (no trailing comma) and the
encounter-table reader parses the JSON objects, so key order does not matter (reader_arms tests both).
Exit 0 = every check passed; non-zero = at least one failure.
"""
import argparse
import json
import os
import random
import re
import shutil
import struct
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DEFAULT = os.path.normpath(os.path.join(HERE, "..", "knowledge", "seasoned"))


class Ctx:
    def __init__(self, decomp, data):
        self.decomp = decomp
        self.raw = {}
        sp = json.load(open(os.path.join(data, "species.json"), encoding="utf-8"))
        self.sp = sp["species"]
        self.sp_notes = sp.get("_notes", {})
        self.mv = json.load(open(os.path.join(data, "moves.json"), encoding="utf-8"))["moves"]
        self.ls = json.load(open(os.path.join(data, "learnsets.json"), encoding="utf-8"))
        self.en = json.load(open(os.path.join(data, "encounters.json"), encoding="utf-8"))
        self.sp_by = {s["symbol"]: s for s in self.sp}
        self.mv_by = {m["symbol"]: m for m in self.mv}
        self.ls_by = {s["symbol"]: s for s in self.ls["species"]}
        self.en_by = {}
        for m in self.en["maps"]:
            self.en_by.setdefault(m["base_label"], m)
        self.results = []

    def text(self, rel):
        if rel not in self.raw:
            self.raw[rel] = open(os.path.join(self.decomp, rel), encoding="utf-8").read()
        return self.raw[rel]

    def check(self, label, ok, detail=""):
        self.results.append((label, bool(ok), detail))
        return bool(ok)  # callers chain `ok &= cx.check(...)`; a list or None here would raise, not fail


def nocomment(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"//[^\n]*", "", t)


# ------------------------------------------------------------------ raw-text lookups
def raw_species_block(cx, sym):
    """The body of `[sym] =\\n    {\\n ... \\n    }` in species_info.h. The closing brace's comma is OPTIONAL: the last
    entry (SPECIES_CHIMECHO on the pinned decomp) ends `    }\\n};`. Before 2026-10-21 the comma was required, so
    every seed that sampled the last species failed on correct data (KB1 step-5 review finding 4, ~3% of seeds)."""
    t = nocomment(cx.text("src/data/pokemon/species_info.h"))
    m = re.search(r"\[" + sym + r"\]\s*=\s*\n\s*\{\n(.*?)\n\s{4}\},?[ \t]*\n", t, flags=re.S)
    return m.group(1) if m else None


def last_species_symbol(cx):
    """The symbol of the LAST `[SPECIES_X] =` entry in species_info.h (the block that has no trailing comma)."""
    t = nocomment(cx.text("src/data/pokemon/species_info.h"))
    return re.findall(r"\[(SPECIES_\w+)\]\s*=\s*\n\s*\{", t)[-1]


def rfield(block, key):
    m = re.search(r"\." + key + r"\s*=\s*([^,\n]+)", block)
    return m.group(1).strip() if m else None


def check_species(cx, sym):
    b = raw_species_block(cx, sym)
    j = cx.sp_by.get(sym)
    if b is None or j is None:
        return cx.check("species %s present" % sym, False, "raw=%s json=%s" % (b is not None, j is not None))
    ok = True
    ty = re.search(r"\.types\s*=\s*\{\s*TYPE_(\w+)\s*,\s*TYPE_(\w+)\s*\}", b)
    exp_t = sorted({ty.group(1), ty.group(2)})
    ok &= cx.check("%s types" % sym, sorted(j["types"]) == exp_t, "json=%s raw=%s" % (j["types"], exp_t))
    ab = re.search(r"\.abilities\s*=\s*\{\s*(\w+)\s*,\s*(\w+)\s*\}", b)
    exp_a = [a for a in ab.groups() if a != "ABILITY_NONE"]
    ok &= cx.check("%s abilities" % sym, j["abilities"] == exp_a, "json=%s raw=%s" % (j["abilities"], exp_a))
    for jk, rk in (("hp", "baseHP"), ("attack", "baseAttack"), ("speed", "baseSpeed")):
        ok &= cx.check("%s base %s" % (sym, jk), j["base_stats"][jk] == int(rfield(b, rk)))
    ok &= cx.check("%s catch rate" % sym, j["catch_rate"] == int(rfield(b, "catchRate")))
    ok &= cx.check("%s growth" % sym, "GROWTH_" + j["growth_rate"] == rfield(b, "growthRate"))
    return ok


def check_held(cx, sym):
    b = raw_species_block(cx, sym)
    if b is None:  # a missing block is a FAIL, not a TypeError on rfield(None, ...)
        return cx.check("%s held items" % sym, False, "raw species block not found")
    ic, ir = rfield(b, "itemCommon"), rfield(b, "itemRare")
    if ic == ir and ic != "ITEM_NONE":
        exp = [(ic, 100)]
    else:
        exp = ([(ic, 50)] if ic != "ITEM_NONE" else []) + ([(ir, 5)] if ir != "ITEM_NONE" else [])
    got = [(h["item"], h["chance_pct"]) for h in cx.sp_by[sym]["wild_held_items"]]
    return cx.check("%s held items" % sym, got == exp, "json=%s raw=%s" % (got, exp))


def check_levelup(cx, sym):
    ptr = cx.text("src/data/pokemon/level_up_learnset_pointers.h")
    label = re.search(r"\[" + sym + r"\]\s*=\s*(\w+),", ptr).group(1)
    lt = cx.text("src/data/pokemon/level_up_learnsets.h")
    body = re.search(r"static const u16 " + label + r"\[\]\s*=\s*\{(.*?)\};", lt, flags=re.S).group(1)
    exp = [(int(a), b) for a, b in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_\w+)\s*\)", body)]
    got = [(x["level"], x["move"]) for x in cx.ls_by[sym]["level_up"]]
    return cx.check("%s level-up moves" % sym, got == exp, "json n=%d raw n=%d" % (len(got), len(exp)))


def tm_numbering(cx):
    t = cx.text("include/constants/tms_hms.h")
    tm = re.search(r"define FOREACH_TM\(F\)(.*?)define FOREACH_HM", t, flags=re.S).group(1)
    hm = re.search(r"define FOREACH_HM\(F\)(.*?)define FOREACH_TMHM", t, flags=re.S).group(1)
    num = {}
    for i, n in enumerate(re.findall(r"F\((\w+)\)", tm), 1):
        num["MOVE_" + n] = "TM%02d" % i
    for i, n in enumerate(re.findall(r"F\((\w+)\)", hm), 1):
        num["MOVE_" + n] = "HM%02d" % i
    return num


def check_tmhm(cx, sym):
    t = nocomment(cx.text("src/data/pokemon/tmhm_learnsets.h"))
    i = t.index("[" + sym + "]")
    nxt = t.find("[SPECIES_", i + 5)
    seg = t[i:nxt if nxt > 0 else len(t)]
    num = tm_numbering(cx)
    exp = sorted((num["MOVE_" + n], "MOVE_" + n) for n in re.findall(r"\.(\w+)\s*=\s*TRUE", seg))
    got = sorted((x["tm"], x["move"]) for x in cx.ls_by[sym]["tm_hm"])
    return cx.check("%s TM/HM set" % sym, got == exp, "json n=%d raw n=%d" % (len(got), len(exp)))


def check_tutor(cx, sym):
    t = nocomment(cx.text("src/data/pokemon/tutor_learnsets.h"))
    i = t.index("[" + sym + "]")
    nxt = t.find("[SPECIES_", i + 5)
    seg = t[i:nxt if nxt > 0 else len(t)]
    exp = re.findall(r"TUTOR\((MOVE_\w+)\)", seg)
    return cx.check("%s tutor moves" % sym, cx.ls_by[sym]["tutor"] == exp, "json=%s raw=%s" % (cx.ls_by[sym]["tutor"], exp))


def check_egg(cx, sym):
    t = nocomment(cx.text("src/data/pokemon/egg_moves.h"))
    short = sym[8:]
    m = re.search(r"egg_moves\(" + short + r",(.*?)\)\s*,", t, flags=re.S)
    exp = re.findall(r"MOVE_\w+", m.group(1)) if m else []
    return cx.check("%s egg moves" % sym, cx.ls_by[sym]["egg"] == exp, "json=%s raw=%s" % (cx.ls_by[sym]["egg"], exp))


def check_move(cx, sym):
    t = nocomment(cx.text("src/data/battle_moves.h"))
    m = re.search(r"\[" + sym + r"\]\s*=\s*\n\s*\{\n(.*?)\n\s{4}\},?[ \t]*\n", t, flags=re.S)  # last block: no comma
    if m is None:
        return cx.check("%s present" % sym, False, "raw move block not found")
    b = m.group(1)
    j = cx.mv_by[sym]
    ok = True
    ok &= cx.check("%s power" % sym, j["power"] == int(rfield(b, "power")), "json=%s" % j["power"])
    ok &= cx.check("%s accuracy" % sym, j["accuracy"] == int(rfield(b, "accuracy")))
    ok &= cx.check("%s pp" % sym, j["pp"] == int(rfield(b, "pp")))
    ok &= cx.check("%s priority" % sym, j["priority"] == int(rfield(b, "priority")))
    ok &= cx.check("%s type" % sym, "TYPE_" + j["type"] == rfield(b, "type"))
    ok &= cx.check("%s effect" % sym, "EFFECT_" + j["effect"] == rfield(b, "effect"))
    ok &= cx.check("%s contact" % sym, j["makes_contact"] == ("FLAG_MAKES_CONTACT" in rfield(b, "flags") or "FLAG_MAKES_CONTACT" in b))
    return ok


def raw_encounter_chunk(cx, label):
    t = cx.text("src/data/wild_encounters.json")
    i = t.index('"base_label": "%s"' % label)
    j = t.find('"base_label"', i + 10)
    return t[i:j if j > 0 else len(t)]


def section(chunk, key):
    keys = ["land_mons", "water_mons", "rock_smash_mons", "fishing_mons"]
    i = chunk.find('"%s"' % key)
    if i < 0:
        return None
    ends = [chunk.find('"%s"' % k, i + 5) for k in keys if k != key]
    ends = [e for e in ends if e > 0]
    return chunk[i:min(ends) if ends else len(chunk)]


def raw_triples(sec):
    return [(int(a), int(b), c) for a, b, c in
            re.findall(r'"min_level"\s*:\s*(\d+)\s*,\s*"max_level"\s*:\s*(\d+)\s*,\s*"species"\s*:\s*"(\w+)"', sec)]


def check_encounter_slot(cx, label, method, rnd):
    chunk = raw_encounter_chunk(cx, label)
    key = {"land": "land_mons", "water": "water_mons", "rock_smash": "rock_smash_mons"}.get(method, "fishing_mons")
    tri = raw_triples(section(chunk, key))
    rates = {"land": [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1], "water": [60, 30, 5, 4, 1], "rock_smash": [60, 30, 5, 4, 1],
             "old_rod": [70, 30], "good_rod": [60, 20, 20], "super_rod": [40, 40, 15, 4, 1]}[method]
    base = {"old_rod": 0, "good_rod": 2, "super_rod": 5}.get(method, 0)
    j = cx.en_by[label]["methods"][method]
    i = rnd.randrange(len(rates))
    lo, hi, sp = tri[base + i]
    s = j["slots"][i]
    ok = cx.check("%s %s slot %d" % (label, method, i),
                  (s["species"], s["min_level"], s["max_level"], s["chance_pct"]) == (sp, lo, hi, rates[i]),
                  "json=%s raw=%s" % ((s["species"], s["min_level"], s["max_level"], s["chance_pct"]), (sp, lo, hi, rates[i])))
    rate = int(re.search(r'"encounter_rate"\s*:\s*(\d+)', section(chunk, key)).group(1))
    ok &= cx.check("%s %s encounter_rate" % (label, method), j["encounter_rate"] == rate)
    tot = sum(x["chance_pct"] for x in j["rarity"].values())
    ok &= cx.check("%s %s rarity sums to 100" % (label, method), tot == 100, "sum=%s" % tot)
    return ok


# ------------------------------------------------------------------ totals
def totals(cx):
    t = nocomment(cx.text("src/data/pokemon/species_info.h"))
    n_sp = len(set(re.findall(r"\[(SPECIES_(?!NONE\])\w+)\]\s*=", t)))
    cx.check("TOTAL species count (raw=%d)" % n_sp, len(cx.sp) == n_sp, "json=%d" % len(cx.sp))
    cx.check("TOTAL real species = 386", sum(1 for s in cx.sp if not s["placeholder"]) == 386)
    bm = nocomment(cx.text("src/data/battle_moves.h"))
    n_mv = len(set(re.findall(r"\[(MOVE_(?!NONE\])\w+)\]\s*=", bm)))
    cx.check("TOTAL move count (raw=%d)" % n_mv, len(cx.mv) == n_mv, "json=%d" % len(cx.mv))
    cx.check("TOTAL TM+HM = 58", len(cx.ls["tm_table"]) == 58)
    cx.check("TOTAL tutor moves = 30", len(cx.ls["tutor_moves"]) == 30)
    cx.check("TOTAL learnset species = real species", len(cx.ls["species"]) == 386)
    bad = []
    n_land = 0
    for m in cx.en["maps"]:
        for meth, rates_n, in (("land", 12), ("water", 5), ("rock_smash", 5), ("old_rod", 2), ("good_rod", 3), ("super_rod", 5)):
            if meth in m["methods"]:
                sl = m["methods"][meth]["slots"]
                if len(sl) != rates_n or sum(x["chance_pct"] for x in sl) != 100:
                    bad.append((m["base_label"], meth, len(sl), sum(x["chance_pct"] for x in sl)))
        if "land" in m["methods"]:
            n_land += 1
    cx.check("TOTAL every method's slots sum to 100 (%d land maps)" % n_land, not bad, str(bad[:3]))
    raw_land = len(re.findall(r'"land_mons"\s*:\s*\{\s*"encounter_rate"', cx.text("src/data/wild_encounters.json")))
    cx.check("TOTAL land tables raw=%d json=%d" % (raw_land, n_land), raw_land == n_land)
    raw_maps = len(re.findall(r'"base_label"', cx.text("src/data/wild_encounters.json")))
    cx.check("TOTAL map entries raw=%d json=%d" % (raw_maps, len(cx.en["maps"])), raw_maps == len(cx.en["maps"]))
    names = [s["name"] for s in cx.sp if not s["placeholder"]]
    cx.check("TOTAL species ids unique", len({s["id"] for s in cx.sp}) == len(cx.sp))


# ------------------------------------------------------------------ availability (KB1 semantic fixes, 2026-10-21)
# INTENT: re-derive, from the raw decomp and WITHOUT the extractor's rules, which wild tables a player meets in normal
# play, and require encounters.json to say the same for every table and every where_to_find row.
# WHY: the first KB1 extraction listed Battle Pyramid header species, Pike header levels, Altering Cave sets 2-9 and the
# unused Cave of Origin maps as ordinary finds (findings F-1, F-2, F-4, F-6) and put a base_label in a map field (F-5).
# This verifier passed all of them, because it only compared the tables, never what they MEAN. The readings here are
# deliberately different from the extractor's: a different scan (write commands, not all mentions; namer folders, not
# a reachability walk) and the raw json read by regex, so one shared mistake has to be made twice to pass.
AV_KINDS = ("normal", "battle_frontier_runtime_species", "battle_frontier_runtime_level", "mystery_gift_required",
            "unreachable_unused_map")
_SCAN_CACHE = {}


def raw_tables(cx):
    """[(base_label, map or None, group label)] in file order, from the raw wild_encounters.json parsed as JSON.
    CHANGED 2026-10-21 (step-5 review note): this was a regex that required "map" to come BEFORE "base_label" inside
    each object; with the keys in the other order it returned map=None and expected_availability crashed. Parsing
    the objects reads the keys in any order. It stays independent of the extractor's labelling code: only the file
    format (JSON) is shared, which is not a reading of what the tables MEAN."""
    out = []
    for g in json.loads(cx.text("src/data/wild_encounters.json"))["wild_encounter_groups"]:
        for e in g["encounters"]:
            out.append((e["base_label"], e.get("map"), g["label"]))
    return out


def decomp_scan(root):
    """One walk of data/ and src/: (folder_id {map folder: MAP id}, namers {MAP id: set of (folder or None)},
    writers [(rel, line)] of VAR_ALTERING_CAVE_WILD_SET). Cached per decomp root (the selftest builds many Ctx)."""
    if root in _SCAN_CACHE:
        return _SCAN_CACHE[root]
    folder_id = {}
    for name in sorted(os.listdir(os.path.join(root, "data", "maps"))):
        p = os.path.join(root, "data", "maps", name, "map.json")
        if os.path.isfile(p):
            folder_id[name] = re.search(r'"id"\s*:\s*"(MAP_\w+)"', open(p, encoding="utf-8").read()).group(1)
    namers = {}
    writers = []
    write_cmd = re.compile(r"^\s*(setvar|addvar|subvar|copyvar|setorcopyvar|copyvarifnotzero|random)\s+"
                           r"VAR_ALTERING_CAVE_WILD_SET\b|VarSet\(\s*VAR_ALTERING_CAVE_WILD_SET")
    for base in ("data", "src"):
        for dp, dn, fn in os.walk(os.path.join(root, base)):
            dn.sort()
            for f in sorted(fn):
                rel = os.path.relpath(os.path.join(dp, f), root).replace("\\", "/")
                if rel.startswith("data/layouts/") or rel == "src/data/wild_encounters.json":
                    continue
                if not f.endswith((".c", ".h", ".inc", ".s", ".json", ".pory")):
                    continue
                text = open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()
                parts = rel.split("/")
                folder = parts[2] if rel.startswith("data/maps/") and len(parts) > 3 and parts[2] in folder_id else None
                for mid in set(re.findall(r"\bMAP_[A-Z0-9_]+\b", text)):
                    if folder is None or folder_id[folder] != mid:
                        namers.setdefault(mid, set()).add(folder)
                if "VAR_ALTERING_CAVE_WILD_SET" in text:
                    writers += [(rel, ln.strip()) for ln in text.splitlines() if write_cmd.search(ln)]
    _SCAN_CACHE[root] = (folder_id, namers, writers)
    return _SCAN_CACHE[root]


def expected_availability(cx):
    """{base_label: (availability, map, group)} from the verifier's own reading of the decomp."""
    folder_id, namers, writers = decomp_scan(cx.decomp)
    pyr = cx.text("src/battle_pyramid.c")
    pike = cx.text("src/battle_pike.c")
    pyramid_replaces = "SetMonData(&gEnemyParty[0], MON_DATA_SPECIES, &wildMons[id].species)" in pyr
    pike_body = pike[pike.find("bool32 TryGenerateBattlePikeWildMon("):]
    pike_body = pike_body[:pike_body.find("\n}\n")]
    pike_party_level = "GetHighestLevelInPlayerParty()" in pike_body and "levelDelta" in pike_body
    gift_only = bool(writers) and all(rel == "data/scripts/gift_altering_cave.inc" for rel, _ in writers)
    unused_folders = {f for f, mid in folder_id.items() if "UNUSED" in mid}
    out = {}
    seen_alter = False
    for bl, mp, grp in raw_tables(cx):
        if grp == "gBattlePyramidWildMonHeaders":
            av = "battle_frontier_runtime_species" if pyramid_replaces else "normal"
        elif grp == "gBattlePikeWildMonHeaders":
            av = "battle_frontier_runtime_level" if pike_party_level else "normal"
        elif mp == "MAP_ALTERING_CAVE":
            av = "mystery_gift_required" if seen_alter and gift_only else "normal"
            seen_alter = True
        elif "UNUSED" in mp and not (namers.get(mp, set()) - unused_folders):
            av = "unreachable_unused_map"   # no file outside an UNUSED map's folder names it
        else:
            av = "normal"
        out[bl] = (av, mp, grp)
    return out


def _cited_pairs(cites):
    """'path:12,14 text' -> {(path, 12), (path, 14)}; also accepts the short 'p:1,2; q:3' row form."""
    pairs = set()
    for c in cites:
        for part in c.split("; "):
            m = re.match(r"([\w./-]+):([\d,]+)", part)
            if m:
                pairs |= {(m.group(1), int(n)) for n in m.group(2).split(",") if n}
    return pairs


def check_availability(cx):
    exp = expected_availability(cx)
    en = cx.en
    ok = cx.check("AVAIL every table has a known label", all(m.get("availability") in AV_KINDS for m in en["maps"]),
                  str([m["base_label"] for m in en["maps"] if m.get("availability") not in AV_KINDS][:5]))
    for kind in AV_KINDS:
        want = sorted(bl for bl, (av, _, _) in exp.items() if av == kind)
        got = sorted(m["base_label"] for m in en["maps"] if m.get("availability") == kind)
        ok &= cx.check("AVAIL maps[] %s: %d tables (raw decomp reading)" % (kind, len(want)), got == want,
                       "only json=%s only raw=%s" % (sorted(set(got) - set(want))[:6], sorted(set(want) - set(got))[:6]))
    bad_rows, bad_map, n = [], [], 0
    src_of = {m["base_label"]: m.get("availability_source") for m in en["maps"]}
    for sp, rows in en["where_to_find"].items():
        for r in rows:
            if r.get("special") is not None:  # rule-based rows (Feebas) belong to no table; check_progression checks them
                continue
            n += 1
            av, mp, grp = exp.get(r["base_label"], (None, None, None))
            if (r.get("availability"), r.get("group"), r.get("availability_source")) != (av, grp, src_of.get(
                    r["base_label"])):
                bad_rows.append((sp, r["base_label"], r.get("availability"), av))
            if r.get("map") != mp:
                bad_map.append((sp, r["base_label"], r.get("map"), mp))
    ok &= cx.check("AVAIL where_to_find: all %d rows carry their table's raw availability, group and source" % n,
                   not bad_rows, str(bad_rows[:4]))
    ok &= cx.check("AVAIL where_to_find map = the raw table's MAP_* id, null for frontier tables (F-5)",
                   not bad_map, str(bad_map[:4]))
    want_np = {}
    for sp, rows in en["where_to_find"].items():
        keep = [r for r in rows if r.get("availability") == "normal"]
        if keep:
            want_np[sp] = keep
    got_np = en.get("where_to_find_normal_play")
    diff = sorted(set(want_np) ^ set(got_np or {})) + sorted(s for s in want_np if (got_np or {}).get(s) not in
                                                               (None, want_np[s]))
    ok &= cx.check("AVAIL where_to_find_normal_play = exactly the where_to_find rows labelled normal (%d species)"
                   % len(want_np), got_np == want_np, "species that differ: %s" % diff[:6])
    # The citations must be TRUE: each cited line number holds the quoted text, and each row points only at lines
    # its kind's rule cites.
    rules = en.get("availability_rules", {})
    bad_cite = []
    allowed = {}
    for kind in AV_KINDS:
        r = rules.get(kind, {})
        cites = list(r.get("decomp", [])) + [v["id_line"] for v in r.get("maps", {}).values()]
        allowed[kind] = _cited_pairs(cites)
        for c in cites:
            m = re.match(r"([\w./-]+):([\d,]+) (.*)$", c)
            if not m:
                bad_cite.append(c)
                continue
            lines = cx.text(m.group(1)).splitlines()
            for num in m.group(2).split(","):
                if not (0 < int(num) <= len(lines) and lines[int(num) - 1].strip() == m.group(3)):
                    bad_cite.append(c)
        for mid, v in r.get("maps", {}).items():
            for nb in v["named_only_by"]:
                path, num = nb.rsplit(":", 1)
                if mid not in cx.text(path).splitlines()[int(num) - 1]:
                    bad_cite.append(nb)
    ok &= cx.check("AVAIL every availability_rules citation quotes its decomp line exactly",
                   bool(rules) and not bad_cite,
                   str(bad_cite[:4]))
    stray = [(m["base_label"], m.get("availability_source")) for m in en["maps"]
             if not _cited_pairs([m.get("availability_source") or ""])
             or not _cited_pairs([m.get("availability_source") or ""]) <= allowed.get(m.get("availability"), set())]
    ok &= cx.check("AVAIL every table's availability_source points only at lines its kind's rule cites",
                   not stray, str(stray[:4]))
    return ok


# ------------------------------------------------------------------ progression gates, conditions, Feebas, notes
# (KB1 step-5 adversarial review, 2026-10-21, findings 1-4 and the notes)
# INTENT: re-derive WHEN a player can first meet each table, which methods exist only in a swapped layout, the Feebas
# rule and the facts the notes state, from the raw decomp, WITHOUT the extractor's gate list.
# WHY A DIFFERENT READING: the extractor declares its gates (cited lines + a backwards walk over map names). This
# verifier instead WALKS FORWARD from the new-game start over every warp, connection and map script, with
# FLAG_SYS_GAME_CLEAR unset ("pre") and set ("post"): a table is post-game when its map is reached only "post". It
# reads scripts as control flow (a goto_if_unset FLAG_SYS_GAME_CLEAR branch is taken pre-game, its fallthrough is
# not), metatile changes on warp tiles from the layout's collision bits, and blockers that only the Hall of Fame
# hides by a flood fill over layout collision and elevation. The two readings share no code and no gate list, so one
# mistake has to be made twice, in two different ways, to pass.
# WHAT IT CANNOT SEE: warps done by C code (fly, Dig, Teleport, secret bases, facility-internal warps) are not edges.
# For a table the extractor calls ungated, a map reachable ONLY that way reads as unreachable here and FAILS loudly.
# For a table the extractor calls post_game, a pre-game C-code way in would be missed by BOTH readings; the guard for
# that case is the extractor's G5, which pins every non-map file that names a gated region (root_mentions, each
# with its reason) and refuses when that set changes. The flood fill models collision, elevation, Surf and one-way
# ledges, and relaxes everything else (bike-only slopes, rails and waterfalls are walked freely; objects other than
# the Hall-of-Fame blockers are ignored). The collision-1 tiles in the Safari layouts are plain walls, ledges,
# Pokeblock feeders, two doors (warps) and one secret-base wall (measured 2026-10-21), so a map the fill does not
# reach there is not reachable on foot. It runs only on connection groups the start's own group does not contain
# (the Safari Zone); a Hall-of-Fame blocker in the main overworld (the Lilycove rival) is listed, not modelled.
# Script reading limits: branches on any flag but FLAG_SYS_GAME_CLEAR are taken both ways, and a script is entered
# only from its map's MapScripts label and the scripts its map.json events name.
GC_FLAG = "FLAG_SYS_GAME_CLEAR"
HOF_SCRIPT = "data/scripts/hall_of_fame.inc"
_WARP_CMD = re.compile(r"^(warp\w*|set\w*warp)\s+(MAP_\w+)")
_SETMT = re.compile(r"^setmetatile\s+(\d+)\s*,\s*(\d+)\s*,\s*\w+\s*,\s*(TRUE|FALSE)")
_LABEL = re.compile(r"([A-Za-z_]\w*)::?\s*(@.*)?$")
_FLAG_WRITE = re.compile(r"\b(?:setflag|clearflag)\s+(FLAG_\w+)|\bFlag(?:Set|Clear)\(\s*(FLAG_\w+)\s*\)")
_TOK = re.compile(r"[A-Za-z_]\w*")
_WORLD = {}


class World:
    """The decomp's maps, layouts and scripts, read once per decomp root (the selftest builds many Ctx)."""

    def __init__(self, root):
        self.root = root
        self.maps = {}
        for name in sorted(os.listdir(os.path.join(root, "data", "maps"))):
            p = os.path.join(root, "data", "maps", name, "map.json")
            if os.path.isfile(p):
                mj = json.load(open(p, encoding="utf-8"))
                self.maps[mj["id"]] = {"folder": name, "j": mj}
        self.layouts = {l["id"]: l for l in json.load(open(os.path.join(root, "data", "layouts", "layouts.json"),
                                                           encoding="utf-8"))["layouts"] if "id" in l}
        self.files, self.labels, self.writes = {}, {}, {}
        for base in ("data", "src"):
            for dp, dn, fn in os.walk(os.path.join(root, base)):
                dn.sort()
                for f in sorted(fn):
                    rel = os.path.relpath(os.path.join(dp, f), root).replace("\\", "/")
                    if rel.startswith("data/layouts/") or not f.endswith((".inc", ".s", ".c")):
                        continue
                    lines = open(os.path.join(dp, f), encoding="utf-8", errors="replace").read().splitlines()
                    for ln in lines:
                        for m in _FLAG_WRITE.finditer(ln):
                            self.writes.setdefault(m.group(1) or m.group(2), set()).add((rel, ln.strip()))
                    if f.endswith(".c"):
                        continue
                    self.files[rel] = lines
                    for i, ln in enumerate(lines):
                        m = _LABEL.match(ln)
                        if m:
                            self.labels.setdefault(m.group(1), (rel, i))
        self._script, self._grid, self._text = {}, {}, {}
        ng = open(os.path.join(root, "src", "new_game.c"), encoding="utf-8").read()
        self.start = re.search(r"SetWarpDestination\(MAP_GROUP\((MAP_\w+)\)", ng).group(1)

    def walk(self, entries, post):
        """Every warp target and setmetatile reachable from `entries` through goto/call/branches and fallthrough.
        Branches on FLAG_SYS_GAME_CLEAR follow the flag's value; every other branch is followed both ways."""
        warps, setmt, seen = set(), set(), set()
        stack = [self.labels[e] for e in entries if e in self.labels]
        while stack:
            rel, i = stack.pop()
            lines = self.files[rel]
            while i < len(lines):
                if (rel, i) in seen:
                    break
                seen.add((rel, i))
                ln = lines[i].split("@", 1)[0].strip()
                i += 1
                if not ln or _LABEL.match(ln):
                    continue
                cmd = ln.split(None, 1)[0]
                if cmd in (".string", "step_end", "end", "return") or ln == ".byte 0":
                    break
                m = _WARP_CMD.match(ln)
                if m:
                    warps.add(m.group(2))
                m = _SETMT.match(ln)
                if m:
                    setmt.add((int(m.group(1)), int(m.group(2)), m.group(3) == "TRUE"))
                rest = ln[len(cmd):]
                refs = [t for t in _TOK.findall(rest) if t in self.labels]
                if GC_FLAG in [a.strip() for a in rest.split(",")] and cmd in (
                        "goto_if_set", "goto_if_unset", "call_if_set", "call_if_unset"):
                    if (cmd.endswith("_set") and post) or (cmd.endswith("_unset") and not post):
                        stack += [self.labels[t] for t in refs]
                        if cmd.startswith("goto"):
                            break
                    continue
                stack += [self.labels[t] for t in refs]
                if cmd == "goto":
                    break
        return warps, setmt

    def script(self, mid, post):
        if (mid, post) not in self._script:
            mj = self.maps[mid]["j"]
            entries = [self.maps[mid]["folder"] + "_MapScripts"] + [
                e["script"] for k in ("object_events", "coord_events", "bg_events") for e in mj.get(k) or []
                if e.get("script")]
            self._script[(mid, post)] = self.walk(entries, post)
        return self._script[(mid, post)]

    def grid(self, layout_id):
        if layout_id not in self._grid:
            l = self.layouts[layout_id]
            raw = open(os.path.join(self.root, l["blockdata_filepath"]), "rb").read()
            self._grid[layout_id] = (l["width"], l["height"],
                                     struct.unpack("<%dH" % (l["width"] * l["height"]), raw))
        return self._grid[layout_id]

    def warp_edges(self, mid, post):
        """Map warps out of `mid`, minus those a FLAG_SYS_GAME_CLEAR-dependent setmetatile shuts in this mode:
        a wall put on the warp tile only in this mode, or a wall (layout collision) opened only in the other."""
        sw, smt = self.script(mid, post)
        _, smt_other = self.script(mid, not post)
        w, h, g = self.grid(self.maps[mid]["j"]["layout"])
        out, cuts = set(sw), []
        for wp in self.maps[mid]["j"].get("warp_events") or []:
            x, y, dest = wp["x"], wp["y"], wp["dest_map"]
            here = {imp for a, b, imp in smt if (a, b) == (x, y)}
            other = {imp for a, b, imp in smt_other if (a, b) == (x, y)}
            wall = 0 <= x < w and 0 <= y < h and (g[y * w + x] >> 10) & 3 != 0
            if (here == {True} and True not in other) or (not here and False in other and wall):
                cuts.append(dest)
                continue
            if dest != "MAP_DYNAMIC":
                out.add(dest)
        return out, cuts

    def components(self):
        adj = {m: set() for m in self.maps}
        for m, v in self.maps.items():
            for c in v["j"].get("connections") or []:
                if c["map"] in self.maps and c["direction"] in ("up", "down", "left", "right"):
                    adj[m].add(c["map"])
                    adj[c["map"]].add(m)
        comp = {}
        for m in sorted(self.maps):
            if m in comp:
                continue
            stack, members = [m], set()
            while stack:
                x = stack.pop()
                if x not in members:
                    members.add(x)
                    stack += adj[x]
            for x in members:
                comp[x] = frozenset(members)
        return comp

    def text(self, rel):
        if rel not in self._text:
            self._text[rel] = open(os.path.join(self.root, rel), encoding="utf-8").read()
        return self._text[rel]

    def behaviour_info(self):
        """({MB_ name: number} from metatile_behaviors.h, {behaviour number: TILE_FLAG bits}, {TILE_FLAG_ name: bit})
        from src/metatile_behavior.c's sTileBitAttributes."""
        if "info" not in self._text:
            body = re.search(r"enum\s*\{(.*?)\}", self.text("include/constants/metatile_behaviors.h"), flags=re.S).group(1)
            mb, n = {}, 0
            for item in body.split(","):
                item = re.sub(r"//[^\n]*", "", item).strip()
                if item:
                    k, _, v = item.partition("=")
                    n = int(v, 0) if v.strip() else n
                    mb[k.strip()] = n
                    n += 1
            mbc = self.text("src/metatile_behavior.c")
            flag = {m.group(1): 1 << int(m.group(2))
                    for m in re.finditer(r"#define (TILE_FLAG_\w+)\s+\(1 << (\d+)\)", mbc)}
            attr = {mb[m.group(1)]: sum(flag[f.strip()] for f in m.group(2).split("|"))
                    for m in re.finditer(r"\[(MB_\w+)\]\s*=\s*([^,\n]+),", mbc)}
            self._text["info"] = (mb, attr, flag)
        return self._text["info"]

    def behaviours(self, layout_id):
        """The metatile behaviour of every tile of a layout, through its two tilesets' metatile_attributes.bin."""
        key = "mb:" + layout_id
        if key not in self._text:
            hdr, mt = self.text("src/data/tilesets/headers.h"), self.text("src/data/tilesets/metatiles.h")

            def attrs(tileset):
                sym = re.search(r"const struct Tileset " + tileset + r"\s*=\s*\{.*?\.metatileAttributes\s*=\s*(\w+)",
                                hdr, flags=re.S).group(1)
                path = re.search(sym + r"\[\]\s*=\s*INCBIN_U16\(\"([^\"]+)\"\)", mt).group(1)
                raw = open(os.path.join(self.root, path), "rb").read()
                return struct.unpack("<%dH" % (len(raw) // 2), raw)
            l = self.layouts[layout_id]
            pa, sa = attrs(l["primary_tileset"]), attrs(l["secondary_tileset"])
            n_prim = int(re.search(r"#define NUM_METATILES_IN_PRIMARY (\d+)", self.text("include/fieldmap.h")).group(1))
            self._text[key] = tuple(((pa[t & 0x3FF] if (t & 0x3FF) < n_prim else sa[(t & 0x3FF) - n_prim]) & 0xFF)
                                    for t in self.grid(layout_id)[2])
        return self._text[key]

    def fill(self, comp, seeds, blocked):
        """Walk inside one connection group: collision-0 tiles, the elevation rule of src/event_object_movement.c
        (elevation 0 and 15 match anything; moving updates the current elevation unless the tile is 15), water
        (elevation 1) enterable from any neighbour (Surf), and ledges: a MB_JUMP_<dir> tile (collision 1 in the
        layouts) is jumped over in its own direction onto the next tile (diagonal jump tiles in any direction).
        Bike-only slopes, rails and waterfalls are collision-0 tiles and are walked freely; objects other than
        `blocked` are ignored. Every relaxation adds reach, so "not reached" here is a safe "cannot reach"."""
        G = {m: self.grid(self.maps[m]["j"]["layout"]) for m in comp}
        mb = self.behaviour_info()[0]
        cardinal = {mb[k]: d for k, d in (("MB_JUMP_EAST", (1, 0)), ("MB_JUMP_WEST", (-1, 0)),
                                          ("MB_JUMP_NORTH", (0, -1)), ("MB_JUMP_SOUTH", (0, 1))) if k in mb}
        any_dir = {v for k, v in mb.items() if k.startswith("MB_JUMP_") and v not in cardinal}
        B = {m: self.behaviours(self.maps[m]["j"]["layout"]) for m in comp}
        conn = {m: {c["direction"]: (c["map"], int(c["offset"])) for c in self.maps[m]["j"].get("connections") or []
                    if c["map"] in comp} for m in comp}

        def step(m, x, y, dx, dy):
            w, h, _ = G[m]
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                return m, nx, ny
            d = "right" if nx >= w else "left" if nx < 0 else "down" if ny >= h else "up"
            if d not in conn[m]:
                return None
            nm, off = conn[m][d]
            ow, oh, _ = G[nm]
            nx, ny = {"right": (0, ny - off), "left": (ow - 1, ny - off), "down": (nx - off, 0),
                      "up": (nx - off, oh - 1)}[d]
            return (nm, nx, ny) if 0 <= nx < ow and 0 <= ny < oh else None

        start = []
        for m, x, y in seeds:
            w, h, g = G[m]
            if 0 <= x < w and 0 <= y < h:
                start.append((m, x, y, g[y * w + x] >> 12))
        seen = set(start)
        todo = list(start)
        while todo:
            m, x, y, el = todo.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                s = step(m, x, y, dx, dy)
                if not s or s in blocked:
                    continue
                nm, nx, ny = s
                ow, _, og = G[nm]
                t = og[ny * ow + nx]
                if (t >> 10) & 3:
                    b = B[nm][ny * ow + nx]
                    if cardinal.get(b) != (dx, dy) and b not in any_dir:
                        continue
                    s = step(nm, nx, ny, dx, dy)  # the ledge jump lands one tile further
                    if not s or s in blocked:
                        continue
                    nm, nx, ny = s
                    ow, _, og = G[nm]
                    t = og[ny * ow + nx]
                    if (t >> 10) & 3:
                        continue
                    e = t >> 12
                else:
                    e = t >> 12
                    if e != 1 and el not in (0, 1) and e not in (0, 15) and e != el:
                        continue
                st = (nm, nx, ny, el if e == 15 else e)
                if st not in seen:
                    seen.add(st)
                    todo.append(st)
        return {s[0] for s in seen}

    def hof_only_flags(self):
        """Flags whose every write in data/ and src/ is a `setflag` in the Hall of Fame script."""
        return {f for f, ws in self.writes.items() if ws and all(r == HOF_SCRIPT and l.startswith("setflag")
                                                                  for r, l in ws)}

    def reach(self, post):
        """{maps reached from the new-game start}, plus what the fill modelled and what it skipped."""
        comp = self.components()
        hof = self.hof_only_flags()
        world = set().union(*(comp[m] for m in self.script(self.start, post)[0] if m in comp))
        blockers = {}
        for m, v in self.maps.items():
            for o in v["j"].get("object_events") or []:
                if o.get("flag") in hof:
                    blockers.setdefault(comp[m], set()).add((m, o["x"], o["y"]))
        enclosed = {c: b for c, b in blockers.items() if not c & world}
        skipped = sorted(b for c, bs in blockers.items() if c & world for b in bs)
        edges = {m: self.warp_edges(m, post)[0] for m in self.maps}
        seen, todo, filled, fill_maps = set(), [self.start], set(), {}
        for _ in range(len(self.maps) + 1):
            while todo:
                m = todo.pop()
                if m in seen or m not in self.maps:
                    continue
                seen.add(m)
                todo += sorted(edges[m])
                if comp[m] not in enclosed:
                    todo += [c["map"] for c in self.maps[m]["j"].get("connections") or []]
            grew = False
            for c, b in enclosed.items():
                hit = frozenset(c & seen)
                if not hit or (c, hit) in filled:
                    continue
                filled.add((c, hit))
                seeds = [(m, wp["x"], wp["y"]) for m in hit for wp in self.maps[m]["j"].get("warp_events") or []]
                got = self.fill(c, seeds, set() if post else b)
                fill_maps[c] = got
                new = got - seen
                todo += sorted(new)
                grew = grew or bool(new)
            if not grew:
                break
        # per modelled group: (its maps, the maps the fill reached), so a caller can see the fill crossed connections
        return seen, sorted((sorted(c), sorted(fill_maps.get(c, ()))) for c in enclosed), skipped


def world(root):
    if root not in _WORLD:
        _WORLD[root] = World(root)
    return _WORLD[root]


def frontier_group_maps(cx, W):
    """{frontier group label: maps whose layout is the one src/wild_encounter.c tests before using that group}."""
    t = cx.text("src/wild_encounter.c")
    out = {}
    for m in re.finditer(r"if \(gMapHeader\.mapLayoutId == (LAYOUT_\w+)\)\s*\{(.{0,400}?)(gBattle\w+WildMonHeaders)",
                         t, flags=re.S):
        out.setdefault(m.group(3), set()).update(mid for mid, v in W.maps.items() if v["j"]["layout"] == m.group(1))
    return out


def layout_census(cx, W, layout_id):
    """(land encounter tiles, water encounter tiles, surfable tiles) of a layout, read through its tilesets'
    metatile behaviours and src/metatile_behavior.c's sTileBitAttributes (HAS_ENCOUNTERS, SURFABLE)."""
    _, attr, flag = W.behaviour_info()
    land = water = surf = 0
    for b in W.behaviours(layout_id):
        f = attr.get(b, 0)
        surf += bool(f & flag["TILE_FLAG_SURFABLE"])
        if f & flag["TILE_FLAG_HAS_ENCOUNTERS"]:
            water += bool(f & flag["TILE_FLAG_SURFABLE"])
            land += not f & flag["TILE_FLAG_SURFABLE"]
    return land, water, surf


def expected_conditions(cx, W):
    """{(map, method)} for every method a map's table has but that has no tile in one of the layouts the map's own
    scripts can load (setmaplayoutindex) and does in another. Fishing follows the surfable tiles."""
    tables = {}
    for e in json.loads(cx.text("src/data/wild_encounters.json"))["wild_encounter_groups"][0]["encounters"]:
        tables[e["map"]] = [k for k in ("land_mons", "water_mons", "fishing_mons") if k in e]
    out = set()
    for mp, keys in tables.items():
        v = W.maps[mp]
        sc = "data/maps/%s/scripts.inc" % v["folder"]
        swaps = set(re.findall(r"setmaplayoutindex\s+(LAYOUT_\w+)", "\n".join(W.files.get(sc, []))))
        if not swaps:
            continue
        cen = [layout_census(cx, W, lid) for lid in sorted(swaps | {v["j"]["layout"]})]
        for key, idx, meths in (("land_mons", 0, ("land",)), ("water_mons", 1, ("water",)),
                                ("fishing_mons", 2, ("old_rod", "good_rod", "super_rod"))):
            counts = [c[idx] for c in cen]
            if key in keys and 0 in counts and any(counts):
                out |= {(mp, m) for m in meths}
    return out


def raw_feebas(cx):
    """(min, max, chance %, map) of the Feebas rule as src/wild_encounter.c states it, or None."""
    t = cx.text("src/wild_encounter.c")
    m = re.search(r"sWildFeebas\s*=\s*\{\s*(\d+)\s*,\s*(\d+)\s*,\s*SPECIES_FEEBAS\s*\}", t)
    chk = re.search(r"bool8 CheckFeebas\(void\)(.*?)\n\}", t, flags=re.S)
    fish = re.search(r"void FishingWildEncounter\(u8 rod\)(.*?)\n\}", t, flags=re.S)
    if not (m and chk and fish and "CheckFeebas()" in fish.group(1)):
        return None
    mp = re.search(r"MAP_GROUP\((MAP_\w+)\)", chk.group(1))
    roll = re.search(r"Random\(\) % 100 > (\d+)", chk.group(1))
    return int(m.group(1)), int(m.group(2)), 99 - int(roll.group(1)) if roll else None, mp.group(1) if mp else None


def _quote_ok(cx, c):
    m = re.match(r"([\w./-]+):([\d,]+) (.*)$", c)
    if not m:
        return False
    lines = cx.text(m.group(1)).splitlines()
    return all(0 < int(n) <= len(lines) and lines[int(n) - 1].strip() == m.group(3) for n in m.group(2).split(","))


def check_progression(cx):
    en = cx.en
    W = world(cx.decomp)
    pre, enclosed, skipped = W.reach(False)
    post, _, _ = W.reach(True)
    tables = raw_tables(cx)
    gmaps = frontier_group_maps(cx, W)
    exp_req = {}
    for bl, mp, grp in tables:
        ms = {mp} if mp else gmaps.get(grp, set())
        exp_req[bl] = bool(ms) and all(m not in pre and m in post for m in ms)
    by_bl = {m["base_label"]: m for m in en["maps"]}
    got_req = {bl: by_bl.get(bl, {}).get("requires") == "post_game" for bl in exp_req}
    ok = cx.check("PROG non-vacuity: the walk reaches %d of %d maps before the Hall of Fame and %d after; %d tables are "
                  "post-game; the layout fill modelled %d connection group(s), reaching %s of their maps before the "
                  "Hall of Fame (Hall-of-Fame blockers listed, not modelled: %s)"
                  % (len(pre), len(W.maps), len(post), sum(exp_req.values()), len(enclosed),
                     ["%d/%d" % (len(r), len(c)) for c, r in enclosed], skipped),
                  len(pre) > len(W.maps) // 2 and len(post) > len(pre) and any(exp_req.values()) and bool(enclosed)
                  and all(len(r) > 1 for _, r in enclosed)  # the fill crossed at least one connection
                  and set(gmaps) == {"gBattlePikeWildMonHeaders", "gBattlePyramidWildMonHeaders"})
    diff = sorted(bl for bl in exp_req if exp_req[bl] != got_req[bl])
    ok &= cx.check("PROG maps[] requires='post_game' on exactly the tables reached only after the Hall of Fame "
                   "(%d tables)" % sum(exp_req.values()), not diff and set(by_bl) == set(exp_req),
                   "differ: %s" % [(bl, "raw post_game=%s" % exp_req[bl]) for bl in diff[:6]])
    gates = en.get("progression_gates") or {}
    bad = []
    for m in en["maps"]:
        if m.get("requires") is None:
            if m.get("requires_gate") is not None or m.get("requires_source") is not None:
                bad.append((m["base_label"], "a gate without requires"))
            continue
        g = gates.get(m.get("requires_gate"))
        if not g or not (m.get("map") in g.get("seed_maps", []) or m["group"] in g.get("groups", [])):
            bad.append((m["base_label"], "gate %s does not name this table" % m.get("requires_gate")))
        elif not _cited_pairs([m.get("requires_source") or ""]) or \
                not _cited_pairs([m["requires_source"]]) <= _cited_pairs(g.get("decomp", [])):
            bad.append((m["base_label"], "requires_source points outside its gate's citations"))
    ok &= cx.check("PROG every gated table names a gate that names it, and cites only that gate's lines", not bad,
                   str(bad[:4]))
    bad_cite = [c for g in gates.values() for c in g.get("decomp", []) if not _quote_ok(cx, c)]
    ok &= cx.check("PROG every progression_gates citation quotes its decomp line exactly (%d)"
                   % sum(len(g.get("decomp", [])) for g in gates.values()), bool(gates) and not bad_cite, str(bad_cite[:3]))
    # The gate flags' writers, read independently: each gate's flag must be written only by the Hall of Fame path.
    w_gc = W.writes.get(GC_FLAG, set())
    ok &= cx.check("PROG FLAG_SYS_GAME_CLEAR has exactly one writer, a FlagSet in GameClear's file, which the Hall of "
                   "Fame map script calls", len(w_gc) == 1 and next(iter(w_gc))[1] == "FlagSet(FLAG_SYS_GAME_CLEAR);"
                   and any("special GameClear" in ln for ln in W.files.get(
                       "data/maps/EverGrandeCity_HallOfFame/scripts.inc", [])), str(sorted(w_gc)))
    # Conditions: (map, method) pairs from the encounter-tile census of every layout each map can load.
    exp_c = expected_conditions(cx, W)
    got_c = {(m["map"], meth) for m in en["maps"] for meth in (m.get("conditions") or {})}
    conds = en.get("conditions") or {}
    ok &= cx.check("PROG maps[] conditions = the methods with no tile in one of the map's layouts (%d pairs)" % len(exp_c),
                   bool(exp_c) and exp_c == got_c and all(cid in conds for m in en["maps"]
                                                          for cid in (m.get("conditions") or {}).values()),
                   "only json=%s only raw=%s" % (sorted(got_c - exp_c)[:4], sorted(exp_c - got_c)[:4]))
    bad_cite = [c for x in conds.values() for c in x.get("decomp", []) if not _quote_ok(cx, c)]
    ok &= cx.check("PROG every conditions citation quotes its decomp line exactly", bool(conds) and not bad_cite,
                   str(bad_cite[:3]))
    # Rows: each table row carries its table's requires/gate/source and the method's condition; only Feebas is special.
    bad_rows, specials = [], []
    for sp, rows in en["where_to_find"].items():
        for r in rows:
            if r.get("special") is not None:
                specials.append((sp, r.get("special")))
                continue
            t = by_bl.get(r["base_label"], {})
            if (r.get("requires"), r.get("requires_gate"), r.get("requires_source"), r.get("condition")) != (
                    t.get("requires"), t.get("requires_gate"), t.get("requires_source"),
                    (t.get("conditions") or {}).get(r["method"])):
                bad_rows.append((sp, r["base_label"], r["method"]))
    ok &= cx.check("PROG where_to_find rows carry their table's requires, gate, source and the method's condition",
                   not bad_rows, str(bad_rows[:4]))
    want_ms = {}
    for sp, rows in en["where_to_find"].items():
        keep = [r for r in rows if r.get("availability") == "normal" and r.get("requires") is None]
        if keep:
            want_ms[sp] = keep
    got_ms = en.get("where_to_find_main_story")
    ok &= cx.check("PROG where_to_find_main_story = exactly the normal rows with no progression gate (%d species)"
                   % len(want_ms), got_ms == want_ms,
                   "species that differ: %s" % sorted(set(want_ms) ^ set(got_ms or {}))[:6])
    # Feebas (finding 2): the rule read from the decomp, against the rows and the feebas block.
    rf = raw_feebas(cx)
    frows = en["where_to_find"].get("SPECIES_FEEBAS", [])
    want_f = [("MAP_ROUTE119", rod, rf[0], rf[1], rf[2], "normal", None, "feebas_tiles")
              for rod in ("good_rod", "old_rod", "super_rod")] if rf and rf[3] == "MAP_ROUTE119" else None
    got_f = sorted((r.get("map"), r.get("method"), r.get("min_level"), r.get("max_level"), r.get("chance_pct"),
                    r.get("availability"), r.get("requires"), r.get("special")) for r in frows)
    ok &= cx.check("PROG Feebas: one row per rod on Route 119 with sWildFeebas levels and CheckFeebas's chance, "
                   "special 'feebas_tiles', in all three indexes; only Feebas rows are special",
                   want_f is not None and got_f == sorted(want_f)
                   and en.get("where_to_find_normal_play", {}).get("SPECIES_FEEBAS") == frows
                   and (got_ms or {}).get("SPECIES_FEEBAS") == frows
                   and set(specials) == {("SPECIES_FEEBAS", "feebas_tiles")}
                   and (en.get("feebas", {}).get("min_level"), en.get("feebas", {}).get("max_level")) == (rf[0], rf[1])
                   and all(_quote_ok(cx, c) for c in en.get("feebas", {}).get("decomp", ["x"])),
                   "raw=%s json=%s specials=%s" % (want_f and want_f[0], got_f[:1], sorted(set(specials))))
    ok &= check_notes(cx)
    return ok


def _note_refs_ok(cx, text, cites):
    """Every 'path:N' a note's text quotes is a line its citation list holds, and every citation quotes exactly."""
    refs = _cited_pairs(re.findall(r"[\w./-]+\.(?:c|h|inc|json):\d+(?:,\d+)*", text))
    return bool(cites) and all(_quote_ok(cx, c) for c in cites) and refs and refs <= _cited_pairs(cites)


def check_notes(cx):
    """The notes' factual claims, each re-derived from the decomp (step-5 review finding 3 and the notes)."""
    en = cx.en
    wc = cx.text("src/wild_encounter.c")
    fca = cx.text("src/field_control_avatar.c")
    steps = re.search(r"if \(sWildEncounterImmunitySteps < (\d+)\)", fca)
    gate = re.search(r"static bool8 AllowWildCheckOnNewMetatile\(void\)\s*\{\s*if \(Random\(\) % 100 >= (\d+)\)", wc)
    rn = en.get("encounter_rate_note", "")
    ok = cx.check("NOTE encounter_rate_note states the %s-step grace and the %s%% new-metatile gate with their lines"
                  % (steps and steps.group(1), gate and gate.group(1)),
                  bool(steps and gate) and ("for %s steps" % steps.group(1)) in rn
                  and ("only %s%% of the time" % gate.group(1)) in rn and "CHECKED step" in rn
                  and _note_refs_ok(cx, rn, en.get("encounter_rate_decomp", [])), rn[:120])
    body = re.search(r"static bool8 TryGenerateWildMon\(.*?\n\}", wc, flags=re.S).group(0)
    land = body[body.find("case WILD_AREA_LAND"):body.find("case WILD_AREA_WATER")]
    water = body[body.find("case WILD_AREA_WATER"):body.find("case WILD_AREA_ROCKS")]
    lvl = re.search(r"static u8 ChooseWildMonLevel\(.*?\n\}", wc, flags=re.S).group(0)
    lvl_ab = sorted(re.findall(r"ABILITY_(\w+)", lvl))
    cute = re.search(r"static void CreateWildMon\(.*?\n\}", wc, flags=re.S).group(0)
    an = en.get("ability_note", "")
    facts = [("MAGNET_PULL" in land and "MAGNET_PULL" not in water, "Magnet Pull (land only"),
             ("STATIC" in land and "STATIC" in water, "Static (land"),
             (lvl_ab == ["HUSTLE", "PRESSURE", "VITAL_SPIRIT"], "Hustle, Vital Spirit and Pressure give the slot's max level"),
             ("ABILITY_CUTE_CHARM" in cute and "gender" in cute and "Random() % 3 != 0" in cute,
              "Cute Charm makes a gendered wild Pokemon the lead's opposite gender 2/3")]
    ok &= cx.check("NOTE ability_note: Magnet Pull land only, Static land+water, max level = Hustle/Vital Spirit/"
                   "Pressure, Cute Charm = gender 2/3 (each read from wild_encounter.c), with true line refs",
                   all(f and phrase in an for f, phrase in facts) and "level/odds" not in an
                   and _note_refs_ok(cx, an, en.get("ability_decomp", [])),
                   str([(phrase, bool(f), phrase in an) for f, phrase in facts if not (f and phrase in an)]))
    pk = cx.text("src/pokemon.c")
    fn = re.search(r"void SetWildMonHeldItem\(void\)\n\{.*?\n\}", pk, flags=re.S).group(0)
    i = fn.find("if (gMapHeader.mapLayoutId == LAYOUT_ALTERING_CAVE)")
    j = fn.find("\n        else\n", i)
    alter = fn[i:j] if i >= 0 and j > i else ""
    rare_only = re.search(r"if \(alteringCaveId != 0\)\s*\{[^}]*if \(rnd < chanceNotRare\)\s*return;", alter) is not None
    eq_outside = "itemCommon == gSpeciesInfo[species].itemRare" in fn[j:] and \
        "itemCommon == gSpeciesInfo[species].itemRare" not in alter
    hn = cx.sp_notes.get("wild_held_item_rule", "")
    ok &= cx.check("NOTE wild_held_item_rule: in the Altering Cave a listed species holds only the list item on the "
                   "rare roll, and the both-slots-equal 100% rule applies only outside it (read from pokemon.c)",
                   rare_only and eq_outside and "on the rare roll alone" in hn
                   and "WITHOUT the both-slots-equal 100% rule" in hn
                   and _note_refs_ok(cx, hn, cx.sp_notes.get("wild_held_item_decomp", [])),
                   "rare_only=%s eq_outside=%s note=%s" % (rare_only, eq_outside, hn[-120:]))
    return ok


def run_checks(cx, seed):
    rnd = random.Random(seed)
    real = [s["symbol"] for s in cx.sp if not s["placeholder"]]
    for sym in rnd.sample(real, 12):
        check_species(cx, sym)
    for sym in rnd.sample([s for s in real if cx.sp_by[s]["wild_held_items"]], 4):
        check_held(cx, sym)
    for sym in rnd.sample(real, 10):
        check_levelup(cx, sym)
    for sym in rnd.sample(real, 8):
        check_tmhm(cx, sym)
    for sym in rnd.sample([s for s in real if cx.ls_by[s]["tutor"]], 4):
        check_tutor(cx, sym)
    for sym in rnd.sample([s for s in real if cx.ls_by[s]["egg"]], 3):
        check_egg(cx, sym)
    for sym in rnd.sample([m["symbol"] for m in cx.mv], 8):
        check_move(cx, sym)
    methods = ["land", "water", "rock_smash", "old_rod", "good_rod", "super_rod"]
    pairs = [(m["base_label"], k) for m in cx.en["maps"] for k in m["methods"]]
    for label, meth in rnd.sample(pairs, 14):
        check_encounter_slot(cx, label, meth, rnd)
    totals(cx)
    check_availability(cx)
    check_progression(cx)


def report(cx):
    fails = [r for r in cx.results if not r[1]]
    for label, ok, detail in cx.results:
        print(("PASS  " if ok else "FAIL  ") + label + ("   [" + detail + "]" if detail and not ok else ""))
    print("---- %d checks, %d passed, %d FAILED" % (len(cx.results), len(cx.results) - len(fails), len(fails)))
    return len(fails)


def selftest(decomp, data, seed):
    """Plant one wrong value per file in a temp copy and require the matching check to fail."""
    with tempfile.TemporaryDirectory() as tmp:
        for fn in os.listdir(data):
            shutil.copy(os.path.join(data, fn), tmp)
        def load(fn):
            return json.load(open(os.path.join(tmp, fn)))
        def save(fn, o):
            json.dump(o, open(os.path.join(tmp, fn), "w"), indent=1)
        plants = []
        s = load("species.json")
        sp = next(x for x in s["species"] if x["symbol"] == "SPECIES_SABLEYE")
        sp["types"] = ["DARK", "FAIRY"]  # planted wrong type
        plants.append(("species type SABLEYE", "species", "SPECIES_SABLEYE"))
        save("species.json", s)
        l = load("learnsets.json")
        ls = next(x for x in l["species"] if x["symbol"] == "SPECIES_BULBASAUR")
        ls["level_up"][2]["level"] = 8  # planted: Leech Seed 7 -> 8
        plants.append(("level-up BULBASAUR", "levelup", "SPECIES_BULBASAUR"))
        tmh = next(x for x in l["species"] if x["symbol"] == "SPECIES_SWELLOW")
        tmh["tm_hm"].pop()  # planted: drop a TM
        plants.append(("TM SWELLOW", "tm", "SPECIES_SWELLOW"))
        save("learnsets.json", l)
        e = load("encounters.json")
        m = next(x for x in e["maps"] if x["base_label"] == "gRoute101")
        m["methods"]["land"]["slots"][0]["species"] = "SPECIES_RALTS"  # planted
        plants.append(("encounter Route101 slot 0", "enc", "gRoute101"))
        save("encounters.json", e)
        mv = load("moves.json")
        mm = next(x for x in mv["moves"] if x["symbol"] == "MOVE_TACKLE")
        mm["power"] = 99
        plants.append(("move TACKLE power", "move", "MOVE_TACKLE"))
        save("moves.json", mv)
        caught = 0
        controls = 0

        def run_one(cx, kind, key):
            if kind == "species":
                check_species(cx, key)
            elif kind == "levelup":
                check_levelup(cx, key)
            elif kind == "tm":
                check_tmhm(cx, key)
            elif kind == "enc":
                check_encounter_slot(cx, key, "land", _Force(0))
            elif kind == "move":
                check_move(cx, key)
            return any(not r[1] for r in cx.results)

        for desc, kind, key in plants:
            failed = run_one(Ctx(decomp, tmp), kind, key)
            # CONTROL: the same check on the untouched data must pass, or a CAUGHT above proves nothing.
            ctrl_ok = not run_one(Ctx(decomp, data), kind, key)
            print("  planted [%s] -> %s; control %s" % (desc, "CAUGHT (verifier failed as required)" if failed
                                                         else "MISSED", "passes" if ctrl_ok else "FAILS"))
            caught += failed
            controls += ctrl_ok
        # the total checks must also notice a planted wrong total
        cx = Ctx(decomp, tmp)
        cx.sp = cx.sp[:-1]
        totals(cx)
        failed = any(not r[1] for r in cx.results)
        cx = Ctx(decomp, data)
        totals(cx)
        ctrl_ok = all(r[1] for r in cx.results)
        print("  planted [species count - 1] -> %s; control %s" % ("CAUGHT" if failed else "MISSED",
                                                                  "passes" if ctrl_ok else "FAILS"))
        caught += failed
        controls += ctrl_ok
        a_caught, a_ctrl, a_n = availability_plants(decomp, data)
        p_caught, p_ctrl, p_n = progression_plants(decomp, data)
        r_caught, r_ctrl, r_n = reader_arms(decomp, data)
        want = len(plants) + 1 + a_n + p_n + r_n
        caught += a_caught + p_caught + r_caught
        controls += a_ctrl + p_ctrl + r_ctrl
        print("SELFTEST: %d of %d plants caught, %d of %d controls pass" % (caught, want, controls, want))
        return 0 if caught == want and controls == want else 1


def _row(en, sp, label):
    return next(r for r in en["where_to_find"][sp] if r["base_label"] == label)


def _plant_f1(en):
    r = _row(en, "SPECIES_BULBASAUR", "gBattlePyramid_1")
    r["availability"] = "normal"
    en["where_to_find_normal_play"]["SPECIES_BULBASAUR"] = [r]


def _plant_f2(en):
    _row(en, "SPECIES_SEVIPER", "gBattlePike_1")["availability"] = "normal"


def _plant_f4(en):
    _row(en, "SPECIES_AIPOM", "gAlteringCave6")["availability"] = "normal"


def _plant_f5(en):
    r = _row(en, "SPECIES_BULBASAUR", "gBattlePyramid_1")
    r["map"] = r["base_label"]


def _plant_f6(en):
    next(m for m in en["maps"] if m["base_label"] == "gCaveOfOrigin_UnusedRubySapphireMap1")["availability"] = "normal"


def _plant_index(en):
    en["where_to_find_normal_play"].setdefault("SPECIES_SEVIPER", []).append(
        _row(en, "SPECIES_SEVIPER", "gBattlePike_1"))


def _plant_source(en):
    """A Pike table (and its rows) pointing at the Pyramid rule's lines: the label is right, its justification is not."""
    pyr = next(m for m in en["maps"] if m["base_label"] == "gBattlePyramid_1")["availability_source"]
    next(m for m in en["maps"] if m["base_label"] == "gBattlePike_1")["availability_source"] = pyr
    for rows in en["where_to_find"].values():
        for r in rows:
            if r["base_label"] == "gBattlePike_1":
                r["availability_source"] = pyr


def _plant_cite(en):
    c = en["availability_rules"]["battle_frontier_runtime_species"]["decomp"]
    path, rest = c[0].split(":", 1)
    num, text = rest.split(" ", 1)
    c[0] = "%s:%d %s" % (path, int(num) + 1, text)


# Each KB1 semantic error fixed on 2026-10-21, planted back, and the AVAIL check label that must name it.
AVAIL_PLANTS = [
    ("F-1 Pyramid header species Bulbasaur as a normal find", _plant_f1, "where_to_find: all"),
    ("F-2 Pike Seviper header level as a normal find", _plant_f2, "where_to_find: all"),
    ("F-4 Altering Cave set 6 (Aipom) without the Mystery Gift label", _plant_f4, "where_to_find: all"),
    ("F-5 a Pyramid row's map holding its base_label", _plant_f5, "where_to_find map"),
    ("F-6 the unused Cave of Origin map 1 labelled normal", _plant_f6, "maps[] normal"),
    ("normal-play index leaking a Pike row", _plant_index, "normal_play"),
    ("a rule citation off by one line", _plant_cite, "citation quotes"),
    ("a Pike table justified by the Pyramid rule's lines", _plant_source, "points only at lines"),
]


def availability_plants(decomp, data):
    """FAULT: each plant must turn check_availability red ON ITS OWN LABEL. CONTROL: the untouched data passes."""
    import copy
    base = Ctx(decomp, data)
    clean = copy.deepcopy(base.en)
    check_availability(base)
    ctrl_ok = all(r[1] for r in base.results)
    caught = controls = 0
    for desc, plant, label in AVAIL_PLANTS:
        cx = Ctx.__new__(Ctx)
        cx.__dict__.update(base.__dict__)
        cx.results = []
        cx.en = copy.deepcopy(clean)
        plant(cx.en)
        check_availability(cx)
        hit = any(not ok and label in name for name, ok, _ in cx.results)
        print("  planted [%s] -> %s; control %s" % (desc, "CAUGHT by '%s'" % label if hit else "MISSED",
                                                     "passes" if ctrl_ok else "FAILS"))
        caught += hit
        controls += ctrl_ok
    # The same through run_checks(), the path a normal run takes: the check must be CALLED there, not only exist.
    cx = Ctx.__new__(Ctx)
    cx.__dict__.update(base.__dict__)
    cx.results = []
    cx.en = copy.deepcopy(clean)
    _plant_f1(cx.en)
    run_checks(cx, 20261015)
    hit = any(not ok and name.startswith("AVAIL") for name, ok, _ in cx.results)
    ctrl = Ctx(decomp, data)
    run_checks(ctrl, 20261015)
    c_ok = all(r[1] for r in ctrl.results)
    print("  planted [F-1 through run_checks] -> %s; control %s" % ("CAUGHT" if hit else "MISSED",
                                                                    "passes" if c_ok else "FAILS"))
    return caught + hit, controls + c_ok, len(AVAIL_PLANTS) + 1


# ------------------------------------------------------------------ progression plants (step-5 review, 2026-10-21)
def _set_requires(en, label, gate):
    """Give table `label` (and every row of it) the requires fields of `gate` (None = ungated)."""
    src = None
    if gate:
        src = next(m["requires_source"] for m in en["maps"] if m.get("requires_gate") == gate)
    for obj in [m for m in en["maps"] if m["base_label"] == label] + \
               [r for rows in en["where_to_find"].values() for r in rows if r.get("base_label") == label]:
        obj["requires"] = "post_game" if gate else None
        obj["requires_gate"] = gate
        obj["requires_source"] = src


def _plant_safari_main_story(en):
    """The reviewer's plant: the Safari Zone Southeast table relabelled main-story, and its rows in that index."""
    _set_requires(en, "gSafariZone_Southeast", None)
    for sp, rows in en["where_to_find"].items():
        keep = [r for r in rows if r.get("availability") == "normal" and r.get("requires") is None]
        if keep:
            en["where_to_find_main_story"][sp] = keep


def _plant_altering_ungated(en):
    _set_requires(en, "gAlteringCave1", None)


def _plant_wrong_gate(en):
    _set_requires(en, "gArtisanCave_1F", "safari_zone_expansion_after_hall_of_fame")


def _plant_gate_cite(en):
    g = en["progression_gates"]["desert_underpass_closed_until_game_clear"]["decomp"]
    path, rest = g[0].split(":", 1)
    num, text = rest.split(" ", 1)
    g[0] = "%s:%d %s" % (path, int(num) + 1, text)


def _plant_main_story_leak(en):
    en["where_to_find_main_story"]["SPECIES_DITTO"] = en["where_to_find_normal_play"]["SPECIES_DITTO"]


def _plant_feebas_gone(en):
    for k in ("where_to_find", "where_to_find_normal_play", "where_to_find_main_story"):
        en[k].pop("SPECIES_FEEBAS", None)


def _plant_feebas_chance(en):
    for r in en["where_to_find"]["SPECIES_FEEBAS"]:
        r["chance_pct"] = 100


def _plant_special_hide(en):
    """A normal row marked special, so the AVAIL row check skips it."""
    en["where_to_find"]["SPECIES_ZIGZAGOON"][0]["special"] = "feebas_tiles"


def _plant_mirage_dropped(en):
    next(m for m in en["maps"] if m["base_label"] == "gRoute130")["conditions"] = {}
    for r in en["where_to_find"]["SPECIES_WYNAUT"]:
        r["condition"] = None


def _plant_row_condition(en):
    next(r for r in en["where_to_find"]["SPECIES_WYNAUT"] if r["base_label"] == "gRoute130")["condition"] = None


def _plant_rate_note(en):
    en["encounter_rate_note"] = ("encounter_rate is the map's per-step base; WildEncounterCheck multiplies it by 16 and "
                                 "compares Random() % 2880 < rate (cap 2880), then modifiers (flute, cleanse tag, "
                                 "abilities, bike). Per-step chance = encounter_rate*16/2880.")


def _plant_rate_cite(en):
    c = en["encounter_rate_decomp"]
    path, rest = c[5].split(":", 1)
    num, text = rest.split(" ", 1)
    c[5] = "%s:%d %s" % (path, int(num) + 1, text)


def _plant_ability_note(en):
    en["ability_note"] = ("Static/Magnet Pull (land/water) force a matching-type slot 50%; Intimidate/Keen Eye/Cute "
                          "Charm-style effects change level/odds; chance_pct here is the unmodified slot table.")


# Each fixed error planted back, and the check label that must name it. The last two plant into species.json's notes.
PROG_PLANTS = [
    ("Safari Zone Southeast relabelled main-story (rows in main_story)", _plant_safari_main_story, "PROG maps[] requires"),
    ("Altering Cave set 1 without its game-clear gate", _plant_altering_ungated, "PROG maps[] requires"),
    ("Artisan Cave pointed at the Safari gate", _plant_wrong_gate, "names a gate that names it"),
    ("a gate citation off by one line", _plant_gate_cite, "progression_gates citation"),
    ("main_story leaking post-game-only Ditto", _plant_main_story_leak, "main_story = exactly"),
    ("Feebas rows dropped from the indexes", _plant_feebas_gone, "PROG Feebas"),
    ("Feebas chance read as a 100% slot share", _plant_feebas_chance, "PROG Feebas"),
    ("a normal Zigzagoon row hidden as special", _plant_special_hide, "PROG Feebas"),
    ("Route 130's Mirage Island condition dropped", _plant_mirage_dropped, "PROG maps[] conditions"),
    ("a Wynaut row without its table's condition", _plant_row_condition, "rows carry"),
    ("encounter_rate_note reverted to the per-step claim", _plant_rate_note, "NOTE encounter_rate_note"),
    ("an encounter_rate citation off by one line", _plant_rate_cite, "NOTE encounter_rate_note"),
    ("ability_note reverted (Cute Charm 'level/odds', Magnet Pull water)", _plant_ability_note, "NOTE ability_note"),
]
NOTE_PLANT = ("wild_held_item_rule reverted ('Altering Cave has its own table')",
              "src/pokemon.c SetWildMonHeldItem: roll 0-99; <45 none, <95 itemCommon (50%), else itemRare (5%); if "
              "both slots are the same non-NONE item it is held 100%. Altering Cave has its own table.",
              "NOTE wild_held_item_rule")


def progression_plants(decomp, data):
    """FAULT: each plant must turn check_progression red ON ITS OWN LABEL. CONTROL: the untouched data passes."""
    import copy
    base = Ctx(decomp, data)
    clean, clean_notes = copy.deepcopy(base.en), copy.deepcopy(base.sp_notes)
    check_progression(base)
    ctrl_ok = all(r[1] for r in base.results)
    caught = controls = 0

    def one(desc, label, en=None, notes=None):
        cx = Ctx.__new__(Ctx)
        cx.__dict__.update(base.__dict__)
        cx.results = []
        cx.en = en if en is not None else copy.deepcopy(clean)
        cx.sp_notes = notes if notes is not None else copy.deepcopy(clean_notes)
        check_progression(cx)
        hit = any(not ok and label in name for name, ok, _ in cx.results)
        print("  planted [%s] -> %s; control %s" % (desc, "CAUGHT by '%s'" % label if hit else "MISSED",
                                                     "passes" if ctrl_ok else "FAILS"))
        return hit

    for desc, plant, label in PROG_PLANTS:
        en = copy.deepcopy(clean)
        plant(en)
        caught += one(desc, label, en=en)
        controls += ctrl_ok
    notes = copy.deepcopy(clean_notes)
    notes["wild_held_item_rule"] = NOTE_PLANT[1]
    caught += one(NOTE_PLANT[0], NOTE_PLANT[2], notes=notes)
    controls += ctrl_ok
    # The same through run_checks(), the path a normal run takes: check_progression must be CALLED there.
    cx = Ctx.__new__(Ctx)
    cx.__dict__.update(base.__dict__)
    cx.results = []
    cx.en = copy.deepcopy(clean)
    _plant_safari_main_story(cx.en)
    run_checks(cx, 20261015)
    hit = any(not ok and name.startswith("PROG") for name, ok, _ in cx.results)
    ctrl = Ctx(decomp, data)
    run_checks(ctrl, 20261015)
    c_ok = all(r[1] for r in ctrl.results)
    print("  planted [Safari Southeast main-story through run_checks] -> %s; control %s"
          % ("CAUGHT" if hit else "MISSED", "passes" if c_ok else "FAILS"))
    return caught + hit, controls + c_ok, len(PROG_PLANTS) + 2


def reader_arms(decomp, data):
    """The two raw readers the step-5 review broke: the LAST species block (no trailing comma) and
    wild_encounters.json objects with their keys in another order. Each arm is a CONTROL that must pass and a FAULT
    that must be caught."""
    caught = controls = 0
    # last species: CONTROL = check_species + check_held pass on it; FAULT = a planted catch rate is caught, with
    # the raw block FOUND (so the failure is the value, not a reader that cannot see the block).
    cx = Ctx(decomp, data)
    last = last_species_symbol(cx)
    check_species(cx, last)
    check_held(cx, last)
    ctrl = bool(cx.results) and all(r[1] for r in cx.results)
    cx = Ctx(decomp, data)
    cx.sp_by[last] = dict(cx.sp_by[last], catch_rate=cx.sp_by[last]["catch_rate"] + 1)
    check_species(cx, last)
    hit = any(not ok and name == "%s catch rate" % last for name, ok, _ in cx.results)
    print("  planted [last species %s catch rate + 1] -> %s; control (species + held on the untouched last block) %s"
          % (last, "CAUGHT by '%s catch rate'" % last if hit else "MISSED", "passes" if ctrl else "FAILS"))
    caught += hit
    controls += ctrl
    # check_held on a block the reader cannot find records a FAIL instead of raising TypeError (rfield on None).
    cx = Ctx(decomp, data)
    try:
        check_held(cx, "SPECIES_PLANTED_MISSING")
        hit2 = any(not ok and name == "SPECIES_PLANTED_MISSING held items" for name, ok, _ in cx.results)
    except Exception as exc:  # noqa: BLE001 - a crash is exactly the defect this arm guards
        hit2 = False
        print("    check_held crashed: %r" % exc)
    print("  planted [check_held on a species block that is not there] -> %s; control (as above) %s"
          % ("CAUGHT as a FAIL, no crash" if hit2 else "MISSED", "passes" if ctrl else "FAILS"))
    caught += hit2
    controls += ctrl
    # key order: the same tables whatever the key order inside each object (CONTROL); a changed map is seen (FAULT).
    raw_text = Ctx(decomp, data).text("src/data/wild_encounters.json")
    src = json.loads(raw_text)
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "src", "data"))

        def tables_of(groups):
            with open(os.path.join(root, "src", "data", "wild_encounters.json"), "w", encoding="utf-8") as f:
                json.dump({"wild_encounter_groups": groups}, f)
            cx2 = Ctx.__new__(Ctx)
            cx2.decomp, cx2.raw = root, {}
            return raw_tables(cx2)
        straight = tables_of(src["wild_encounter_groups"])
        rev = [dict(g, encounters=[dict(reversed(list(e.items()))) for e in g["encounters"]])
               for g in src["wild_encounter_groups"]]
        ctrl = (tables_of(rev) == straight and len(straight) == raw_text.count('"base_label"')
                and any(mp for _, mp, _ in straight))
        rev[0]["encounters"][0]["map"] = "MAP_PLANTED"
        hit = tables_of(rev) != straight
    print("  planted [wild_encounters.json keys reversed, first map changed] -> %s; control (keys reversed, same "
          "tables) %s" % ("CAUGHT" if hit else "MISSED", "passes" if ctrl else "FAILS"))
    return caught + hit, controls + ctrl, 3


class _Force:
    def __init__(self, v):
        self.v = v

    def randrange(self, n):
        return self.v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decomp", required=True)
    ap.add_argument("--data", default=DATA_DEFAULT)
    ap.add_argument("--seed", type=int, default=20261015)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest(a.decomp, a.data, a.seed)
    cx = Ctx(a.decomp, a.data)
    run_checks(cx, a.seed)
    return 1 if report(cx) else 0


if __name__ == "__main__":
    sys.exit(main())
