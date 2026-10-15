#!/usr/bin/env python3
"""Independent verifier for ai_player/knowledge/seasoned/*.json (USER RULING 40).

Deliberately does NOT import extract_seasoned.py and does NOT use its parser:
every expected value is re-derived by regex / line scanning over the raw decomp text.

  python3 ai_player/gates/verify_seasoned.py --decomp /tmp/pokeemerald [--seed N] [--data DIR]
  python3 ai_player/gates/verify_seasoned.py --decomp /tmp/pokeemerald --selftest

--selftest plants wrong values in a temp copy of the data and requires each to be caught.
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
        for desc, kind, key in plants:
            cx = Ctx(decomp, tmp)
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
            failed = any(not r[1] for r in cx.results)
            print("  planted [%s] -> %s" % (desc, "CAUGHT (verifier failed as required)" if failed else "MISSED"))
            caught += failed
        # the total checks must also notice a planted wrong total
        cx = Ctx(decomp, tmp)
        cx.sp = cx.sp[:-1]
        totals(cx)
        failed = any(not r[1] for r in cx.results)
        print("  planted [species count - 1] -> %s" % ("CAUGHT" if failed else "MISSED"))
        caught += failed
        want = len(plants) + 1
        print("SELFTEST: %d of %d plants caught" % (caught, want))
        return 0 if caught == want else 1


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
