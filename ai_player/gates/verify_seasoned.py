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
Exit 0 = every check passed; non-zero = at least one failure.
"""
import argparse
import json
import os
import random
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DEFAULT = os.path.normpath(os.path.join(HERE, "..", "knowledge", "seasoned"))


class Ctx:
    def __init__(self, decomp, data):
        self.decomp = decomp
        self.raw = {}
        self.sp = json.load(open(os.path.join(data, "species.json")))["species"]
        self.mv = json.load(open(os.path.join(data, "moves.json")))["moves"]
        self.ls = json.load(open(os.path.join(data, "learnsets.json")))
        self.en = json.load(open(os.path.join(data, "encounters.json")))
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
        return ok


def nocomment(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"//[^\n]*", "", t)


# ------------------------------------------------------------------ raw-text lookups
def raw_species_block(cx, sym):
    t = nocomment(cx.text("src/data/pokemon/species_info.h"))
    m = re.search(r"\[" + sym + r"\]\s*=\s*\n\s*\{\n(.*?)\n\s{4}\},", t, flags=re.S)
    return m.group(1) if m else None


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
    m = re.search(r"\[" + sym + r"\]\s*=\s*\n\s*\{\n(.*?)\n\s{4}\},", t, flags=re.S)
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
    """[(base_label, map or None, group label)] in file order, by regex over the raw wild_encounters.json."""
    t = cx.text("src/data/wild_encounters.json")
    groups = [(m.start(), m.group(1)) for m in re.finditer(r'"label"\s*:\s*"(\w+)"', t)]
    out = []
    for m in re.finditer(r'\{\s*(?:"map"\s*:\s*"(MAP_\w+)"\s*,\s*)?"base_label"\s*:\s*"(\w+)"', t):
        grp = [g for pos, g in groups if pos < m.start()][-1]
        out.append((m.group(2), m.group(1), grp))
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
                pairs |= {(m.group(1), int(n)) for n in m.group(2).split(",")}
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
        want = len(plants) + 1 + a_n
        caught += a_caught
        controls += a_ctrl
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
