#!/usr/bin/env python3
"""Seasoned-player knowledge base extractor (USER RULING 40).

Parses the pret/pokeemerald decomp into static JSON under
ai_player/knowledge/seasoned/.  Standard library only.

  python3 ai_player/gates/extract_seasoned.py --decomp /tmp/pokeemerald
  python3 ai_player/gates/extract_seasoned.py --decomp /tmp/pokeemerald --check

--check re-extracts into a temp folder and fails if the committed files differ.
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
OUT_DEFAULT = os.path.normpath(os.path.join(HERE, "..", "knowledge", "seasoned"))
MADE_BY = "ai_player/gates/extract_seasoned.py"
MAX_ITER = 2_000_000  # bound for every scanning loop


# ---------------------------------------------------------------- helpers
class Decomp:
    def __init__(self, root):
        self.root = root
        self.used = {}
        r = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True)
        self.sha = r.stdout.strip() or "unknown"

    def read(self, rel):
        with open(os.path.join(self.root, rel), "rb") as f:
            raw = f.read()
        self.used[rel] = hashlib.sha256(raw).hexdigest()
        return raw.decode("utf-8")

    def header(self, files):
        return {"_source": "pret/pokeemerald@" + self.sha,
                "_files": {p: self.used[p] for p in sorted(files)},
                "_kind": "static game knowledge (USER RULING 40)",
                "_made_by": MADE_BY}


def strip_comments(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    return re.sub(r"//[^\n]*", "", t)


def safe_eval(expr, names):
    """Evaluate a C integer expression made of ints, names, + - * / ( )."""
    expr = expr.strip()
    expr = re.sub(r"\b0x[0-9A-Fa-f]+\b", lambda m: str(int(m.group(0), 16)), expr)
    def sub(m):
        if m.group(0) not in names:
            raise KeyError(m.group(0))
        return str(names[m.group(0)])
    expr = re.sub(r"[A-Za-z_]\w*", sub, expr)
    if not re.fullmatch(r"[\d\s+\-*/()]*", expr):
        raise ValueError(expr)
    return int(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 (validated above)


def parse_defines(text, names=None):
    names = {} if names is None else names
    pending = []
    for m in re.finditer(r"^[ \t]*#define[ \t]+([A-Za-z_]\w*)[ \t]+([^\n]+)$", strip_comments(text), flags=re.M):
        pending.append((m.group(1), m.group(2).strip().rstrip("\\").strip()))
    for _ in range(6):  # a few passes resolve forward references
        left = []
        for k, v in pending:
            try:
                names[k] = safe_eval(v, names)
            except (KeyError, ValueError, SyntaxError):
                left.append((k, v))
        pending = left
    return names


def parse_enum_blocks(text):
    """Return {name: ordinal} for every anonymous/named enum { A, B = 5, ... }."""
    out = {}
    text = strip_comments(text)
    for m in re.finditer(r"enum\s*\w*\s*\{(.*?)\}", text, flags=re.S):
        n = 0
        for item in m.group(1).split(","):
            item = item.strip()
            if not item:
                continue
            if "=" in item:
                k, v = [s.strip() for s in item.split("=", 1)]
                n = safe_eval(v, out)
            else:
                k = item
            out[k] = n
            n += 1
    return out


def balanced(text, start, open_ch="{", close_ch="}"):
    """text[start] == open_ch; return index just past the matching close."""
    depth = 0
    for i in range(start, min(len(text), start + MAX_ITER)):
        c = text[i]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced")


def pretty(name):
    return name.replace("_", " ").title()


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")


# ---------------------------------------------------------------- shared tables
class Consts:
    def __init__(self, d):
        self.species = parse_defines(d.read("include/constants/species.h"))
        self.moves = parse_defines(d.read("include/constants/moves.h"))
        self.abilities = parse_defines(d.read("include/constants/abilities.h"))
        self.items = parse_defines(d.read("include/constants/items.h"))
        self.pokemon = parse_defines(d.read("include/constants/pokemon.h"))
        self.pokedex = parse_enum_blocks(d.read("include/constants/pokedex.h"))
        self.pokedex.update(parse_defines(d.read("include/constants/pokedex.h")))
        self.rev_species = {v: k for k, v in self.species.items() if k.startswith("SPECIES_") and 0 < v <= 411
                            and not k.endswith("_COUNT") and k != "SPECIES_EGG"}
        self.rev_moves = {v: k for k, v in self.moves.items() if k.startswith("MOVE_") and k != "MOVES_COUNT"}
        self.rev_items = {}
        for k, v in self.items.items():
            if k.startswith("ITEM_") and v not in self.rev_items:
                self.rev_items[v] = k
        self.rev_abilities = {v: k for k, v in self.abilities.items() if k.startswith("ABILITY_") and k != "ABILITIES_COUNT"}
        self.types = {v: k[5:] for k, v in self.pokemon.items() if re.fullmatch(r"TYPE_[A-Z]+", k)}


def species_names(d):
    t = d.read("src/data/text/species_names.h")
    return {m.group(1): m.group(2) for m in re.finditer(r'\[(SPECIES_\w+)\]\s*=\s*_\("([^"]*)"\)', t)}


def move_names(d):
    t = d.read("src/data/text/move_names.h")
    return {m.group(1): m.group(2) for m in re.finditer(r'\[(MOVE_\w+)\]\s*=\s*_\("([^"]*)"\)', t)}


def item_label(c, sym):
    return None if sym in (None, "ITEM_NONE") else sym


# ---------------------------------------------------------------- species.json
def species_blocks(d):
    """{SPECIES_X: body-text} from species_info.h, expanding the OLD_UNOWN macro."""
    t = d.read("src/data/pokemon/species_info.h")
    macro = re.search(r"#define OLD_UNOWN_SPECIES_INFO\s*\\\n(.*?)\n\s*\}\s*\n", t, flags=re.S)
    macro_body = macro.group(1).replace("\\", " ") if macro else ""
    t = strip_comments(t)
    out = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*", t):
        name = m.group(1)
        pos = m.end()
        if t.startswith("OLD_UNOWN_SPECIES_INFO", pos):
            if name not in out:
                out[name] = macro_body
            continue
        if t[pos] == "{":
            try:
                end = balanced(t, pos)
            except ValueError:
                continue
            if name not in out:
                out[name] = t[pos:end]
    return out


def field(body, key, default=None):
    m = re.search(r"\." + key + r"\s*=\s*([^,\n]+)", body)
    return m.group(1).strip() if m else default


def gender_info(expr):
    if expr == "MON_MALE":
        return 0, 0.0
    if expr == "MON_FEMALE":
        return 254, 100.0
    if expr == "MON_GENDERLESS":
        return 255, None
    m = re.fullmatch(r"PERCENT_FEMALE\(([\d.]+)\)", expr)
    pct = float(m.group(1))
    return min(254, int(pct * 255 / 100)), pct


def parse_evolutions(d, c):
    t = strip_comments(d.read("src/data/pokemon/evolution.h"))
    out = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*\{", t):
        end = balanced(t, m.end() - 1)
        evs = []
        for e in re.finditer(r"\{\s*(EVO_\w+)\s*,\s*([^,]+?)\s*,\s*(SPECIES_\w+)\s*\}", t[m.end():end - 1]):
            param = e.group(2).strip()
            if param.startswith("ITEM_"):
                pv = {"item": param}
            else:
                pv = {"value": safe_eval(param, c.pokemon)}
            evs.append({"method": e.group(1), "parameter": pv, "into": e.group(3)})
        out[m.group(1)] = evs
    return out


def build_species(d, c):
    names = species_names(d)
    blocks = species_blocks(d)
    evos = parse_evolutions(d, c)
    pk = d.read("src/pokemon.c")
    # dex tables: SPECIES_TO_HOENN(NAME) / SPECIES_TO_NATIONAL(NAME) entries, indexed by species-1
    hoenn_t = re.search(r"sSpeciesToHoennPokedexNum\[NUM_SPECIES - 1\]\s*=\s*\{(.*?)\};", pk, flags=re.S).group(1)
    nat_t = re.search(r"sSpeciesToNationalPokedexNum\[NUM_SPECIES - 1\]\s*=\s*\{(.*?)\};", pk, flags=re.S).group(1)
    hoenn = {m.group(1): c.pokedex["HOENN_DEX_" + m.group(1)] for m in re.finditer(r"SPECIES_TO_HOENN\((\w+)\)", hoenn_t)}
    natl = {m.group(1): c.pokedex["NATIONAL_DEX_" + m.group(1)] for m in re.finditer(r"SPECIES_TO_NATIONAL\((\w+)\)", nat_t)}
    hoenn_count = c.pokedex["HOENN_DEX_DEOXYS"]
    species = []
    for sid in sorted(c.rev_species):
        sym = c.rev_species[sid]
        body = blocks.get(sym)
        if body is None:
            continue
        short = sym[8:]
        placeholder = short.startswith("OLD_UNOWN_")
        types = re.search(r"\.types\s*=\s*\{\s*(\w+)\s*,\s*(\w+)\s*\}", body)
        t1, t2 = c.types[c.pokemon[types.group(1)]], c.types[c.pokemon[types.group(2)]]
        ab = re.search(r"\.abilities\s*=\s*\{\s*(\w+)\s*,\s*(\w+)\s*\}", body)
        abil = [a for a in (ab.group(1), ab.group(2)) if a != "ABILITY_NONE"]
        raw_gender, pct = gender_info(field(body, "genderRatio"))
        ic, ir = field(body, "itemCommon"), field(body, "itemRare")
        if ic == ir and ic != "ITEM_NONE":
            held = [{"item": ic, "chance_pct": 100}]
        else:
            held = []
            if ic != "ITEM_NONE":
                held.append({"item": ic, "chance_pct": 50})
            if ir != "ITEM_NONE":
                held.append({"item": ir, "chance_pct": 5})
        nd = natl.get(short)
        hd = hoenn.get(short)
        species.append({
            "id": sid, "symbol": sym,
            "name": names.get(sym, pretty(short)),
            "national_dex": nd if nd and not placeholder else None,
            "hoenn_dex": hd if hd and 0 < hd <= hoenn_count else None,
            "placeholder": placeholder,
            "types": [t1] if t1 == t2 else [t1, t2],
            "base_stats": {"hp": int(field(body, "baseHP")), "attack": int(field(body, "baseAttack")),
                           "defense": int(field(body, "baseDefense")), "sp_attack": int(field(body, "baseSpAttack")),
                           "sp_defense": int(field(body, "baseSpDefense")), "speed": int(field(body, "baseSpeed"))},
            "abilities": abil,
            "catch_rate": int(field(body, "catchRate")),
            "base_exp": int(field(body, "expYield")),
            "growth_rate": field(body, "growthRate")[7:],
            "gender_ratio_byte": raw_gender,
            "female_pct": pct,
            "wild_held_items": held,
            "egg_cycles": int(field(body, "eggCycles")),
            "egg_groups": sorted({g[10:] for g in re.findall(r"EGG_GROUP_\w+", field_line(body, "eggGroups"))}),
            "evolutions": evos.get(sym, []),
        })
    return species


def field_line(body, key):
    m = re.search(r"\." + key + r"\s*=\s*\{[^}]*\}", body)
    return m.group(0) if m else ""


def extract_species(d, c, out):
    sp = build_species(d, c)
    hdr = d.header(["src/data/pokemon/species_info.h", "src/data/pokemon/evolution.h",
                    "src/data/text/species_names.h", "src/pokemon.c", "include/constants/species.h",
                    "include/constants/pokemon.h", "include/constants/pokedex.h",
                    "include/constants/abilities.h", "include/constants/items.h"])
    hdr["_notes"] = {
        "wild_held_item_rule": "src/pokemon.c SetWildMonHeldItem: roll 0-99; <45 none, <95 itemCommon (50%), else itemRare (5%); "
                               "if both slots are the same non-NONE item it is held 100%. A lead with Compound Eyes uses 20/60/20 instead "
                               "(none/common/rare). Not applied for legendary/trainer/pyramid/pike battles. Altering Cave has its own table.",
        "placeholder": "SPECIES_OLD_UNOWN_B..Z (252-276) are unused filler entries, flagged placeholder=true; the 28 Unown forms "
                       "above NUM_SPECIES are forms of SPECIES_UNOWN and have no own species_info entry.",
        "female_pct": "null = genderless; derived from the decomp's PERCENT_FEMALE() byte macro (gender_ratio_byte).",
    }
    hdr["count"] = len(sp)
    hdr["count_real"] = sum(1 for s in sp if not s["placeholder"])
    hdr["species"] = sp
    write_json(os.path.join(out, "species.json"), hdr)
    return sp


# ---------------------------------------------------------------- moves.json
def extract_moves(d, c, out):
    t = strip_comments(d.read("src/data/battle_moves.h"))
    names = move_names(d)
    moves = []
    for m in re.finditer(r"\[(MOVE_\w+)\]\s*=\s*\{", t):
        sym = m.group(1)
        body = t[m.end():balanced(t, m.end() - 1)]
        mid = c.moves[sym]
        if mid == 0:
            continue
        flags = [f[5:] for f in re.findall(r"FLAG_\w+", field(body, "flags", "0") or "0")]
        moves.append({
            "id": mid, "symbol": sym, "name": names.get(sym, pretty(sym[5:])),
            "type": c.types[c.pokemon[field(body, "type")]],
            "power": int(field(body, "power")), "accuracy": int(field(body, "accuracy")),
            "pp": int(field(body, "pp")), "priority": int(field(body, "priority")),
            "effect": field(body, "effect")[7:],
            "secondary_effect_chance": int(field(body, "secondaryEffectChance")),
            "target": field(body, "target")[12:],
            "flags": flags, "makes_contact": "MAKES_CONTACT" in flags,
        })
    moves.sort(key=lambda x: x["id"])
    hdr = d.header(["src/data/battle_moves.h", "src/data/text/move_names.h", "include/constants/moves.h",
                    "include/constants/pokemon.h"])
    hdr["_notes"] = {"accuracy": "0 = never misses (bypasses accuracy check)",
                     "priority": "signed; positive acts first",
                     "type_category": "Gen 3 physical/special split is by TYPE, not by move; see the decomp's IS_TYPE_PHYSICAL (types before MYSTERY physical)."}
    hdr["count"] = len(moves)
    hdr["moves"] = moves
    write_json(os.path.join(out, "moves.json"), hdr)
    return moves


# ---------------------------------------------------------------- learnsets.json
def extract_learnsets(d, c, out):
    lv_text = strip_comments(d.read("src/data/pokemon/level_up_learnsets.h"))
    lists = {}
    for m in re.finditer(r"static const u16 (\w+)\[\]\s*=\s*\{(.*?)\};", lv_text, flags=re.S):
        lists[m.group(1)] = [(int(a), b) for a, b in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*(MOVE_\w+)\s*\)", m.group(2))]
    ptr = strip_comments(d.read("src/data/pokemon/level_up_learnset_pointers.h"))
    level_by_species = {m.group(1): lists[m.group(2)] for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*(\w+)", ptr)}

    # TM/HM: order of FOREACH_TM / FOREACH_HM in tms_hms.h gives the numbering
    th = d.read("include/constants/tms_hms.h")
    tm_names = re.findall(r"F\((\w+)\)", re.search(r"FOREACH_TM\(F\)(.*?)#define FOREACH_HM", th, flags=re.S).group(1))
    hm_names = re.findall(r"F\((\w+)\)", re.search(r"FOREACH_HM\(F\)(.*?)#define FOREACH_TMHM", th, flags=re.S).group(1))
    tmhm_label = {n: "TM%02d" % (i + 1) for i, n in enumerate(tm_names)}
    tmhm_label.update({n: "HM%02d" % (i + 1) for i, n in enumerate(hm_names)})
    tm_text = strip_comments(d.read("src/data/pokemon/tmhm_learnsets.h"))
    tmhm_by_species = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*\{\s*\.learnset\s*=\s*\{", tm_text):
        body = tm_text[m.end():balanced(tm_text, m.end() - 1)]
        tmhm_by_species[m.group(1)] = [(tmhm_label[n], "MOVE_" + n) for n in re.findall(r"\.(\w+)\s*=\s*TRUE", body)]

    # Tutors
    tu = strip_comments(d.read("src/data/pokemon/tutor_learnsets.h"))
    tutor_by_species = {}
    for m in re.finditer(r"\[(SPECIES_\w+)\]\s*=\s*\(([^;]*?)\)\s*,", tu):
        tutor_by_species[m.group(1)] = re.findall(r"TUTOR\((MOVE_\w+)\)", m.group(2))

    # Egg moves
    eg = strip_comments(d.read("src/data/pokemon/egg_moves.h"))
    egg_by_species = {}
    for m in re.finditer(r"egg_moves\((\w+),(.*?)\)\s*,", eg, flags=re.S):
        egg_by_species["SPECIES_" + m.group(1)] = re.findall(r"MOVE_\w+", m.group(2))

    names = move_names(d)
    def mv(sym):
        return {"move": sym, "name": names.get(sym)}
    sp_list = []
    sp_ids = sorted((v, k) for k, v in c.species.items() if k.startswith("SPECIES_") and 0 < v <= 411 and k != "SPECIES_EGG")
    for sid, sym in sp_ids:
        if sym.startswith("SPECIES_OLD_UNOWN_"):
            continue
        sp_list.append({
            "id": sid, "symbol": sym,
            "level_up": [{"level": l, "move": m_} for l, m_ in level_by_species.get(sym, [])],
            "tm_hm": [{"tm": a, "move": b} for a, b in tmhm_by_species.get(sym, [])],
            "tutor": tutor_by_species.get(sym, []),
            "egg": egg_by_species.get(sym, []),
        })
    tm_table = [{"tm": tmhm_label[n], "move": "MOVE_" + n, "name": names.get("MOVE_" + n)} for n in tm_names + hm_names]
    tutor_moves = re.findall(r"\[TUTOR_MOVE_\w+\]\s*=\s*(MOVE_\w+)", tu)
    hdr = d.header(["src/data/pokemon/level_up_learnsets.h", "src/data/pokemon/level_up_learnset_pointers.h",
                    "src/data/pokemon/tmhm_learnsets.h", "src/data/pokemon/tutor_learnsets.h",
                    "src/data/pokemon/egg_moves.h", "include/constants/tms_hms.h",
                    "src/data/text/move_names.h", "include/constants/species.h", "include/constants/moves.h"])
    hdr["_notes"] = {"level_up": "moves learned at that level; a move at level 1 is known on creation. Learnset order is game order.",
                     "tutor": "Emerald tutors (gTutorMoves); not every one is reachable in a normal playthrough, that is not decided here.",
                     "egg": "egg moves are only inheritable through breeding."}
    hdr["tm_table"] = tm_table
    hdr["tutor_moves"] = tutor_moves
    hdr["count"] = len(sp_list)
    hdr["species"] = sp_list
    write_json(os.path.join(out, "learnsets.json"), hdr)
    return sp_list


# ---------------------------------------------------------------- encounters.json
def _slots(mons, rates, offset=0):
    out = []
    for i, w in enumerate(mons):
        r = rates[offset + i]
        out.append({"slot": offset + i, "species": w["species"], "min_level": w["min_level"],
                    "max_level": w["max_level"], "chance_pct": r})
    return out


def _method(slots, rate):
    by = {}
    for sl in slots:
        e = by.setdefault(sl["species"], {"chance_pct": 0, "min_level": sl["min_level"], "max_level": sl["max_level"], "slots": []})
        e["chance_pct"] += sl["chance_pct"]
        e["min_level"] = min(e["min_level"], sl["min_level"])
        e["max_level"] = max(e["max_level"], sl["max_level"])
        e["slots"].append(sl["slot"])
    return {"encounter_rate": rate, "slots": slots,
            "rarity": dict(sorted(by.items(), key=lambda kv: (-kv[1]["chance_pct"], kv[0])))}


def extract_encounters(d, c, out):
    j = json.loads(d.read("src/data/wild_encounters.json"))
    wc = d.read("src/wild_encounter.c")
    fields = {f["type"]: f for f in j["wild_encounter_groups"][0]["fields"]}
    land_r = fields["land_mons"]["encounter_rates"]
    water_r = fields["water_mons"]["encounter_rates"]
    rock_r = fields["rock_smash_mons"]["encounter_rates"]
    fish_r = fields["fishing_mons"]["encounter_rates"]
    groups = fields["fishing_mons"]["groups"]
    expected = {"land": [20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1], "water": [60, 30, 5, 4, 1],
                "rock_smash": [60, 30, 5, 4, 1], "old_rod": [70, 30], "good_rod": [60, 20, 20], "super_rod": [40, 40, 15, 4, 1]}
    got = {"land": land_r, "water": water_r, "rock_smash": rock_r,
           "old_rod": [fish_r[i] for i in groups["old_rod"]], "good_rod": [fish_r[i] for i in groups["good_rod"]],
           "super_rod": [fish_r[i] for i in groups["super_rod"]]}
    # the C code compares against ENCOUNTER_CHANCE_*_SLOT_n constants generated from these same json fields
    code_uses_generated = "ENCOUNTER_CHANCE_LAND_MONS_SLOT_0" in wc and "ENCOUNTER_CHANCE_FISHING_MONS_SUPER_ROD_SLOT_5" in wc
    maps = []
    for gi, g in enumerate(j["wild_encounter_groups"]):
        is_main = g["label"] == "gWildMonHeaders"
        for e in g["encounters"]:
            entry = {"group": g["label"], "base_label": e["base_label"], "map": e.get("map"), "methods": {}}
            if "land_mons" in e:
                lm = e["land_mons"]
                entry["methods"]["land"] = _method(_slots(lm["mons"], land_r), lm["encounter_rate"])
            if "water_mons" in e:
                wm = e["water_mons"]
                entry["methods"]["water"] = _method(_slots(wm["mons"], water_r), wm["encounter_rate"])
            if "rock_smash_mons" in e:
                rm = e["rock_smash_mons"]
                entry["methods"]["rock_smash"] = _method(_slots(rm["mons"], rock_r), rm["encounter_rate"])
            if "fishing_mons" in e:
                fm = e["fishing_mons"]
                for rod in ("old_rod", "good_rod", "super_rod"):
                    idx = groups[rod]
                    sl = []
                    for i in idx:
                        w = fm["mons"][i]
                        sl.append({"slot": i, "species": w["species"], "min_level": w["min_level"],
                                   "max_level": w["max_level"], "chance_pct": fish_r[i]})
                    entry["methods"][rod] = _method(sl, fm["encounter_rate"])
            maps.append(entry)
    # overall per-species index: where can I find X, best chance per method
    where = {}
    for m in maps:
        for meth, info in m["methods"].items():
            for sp, r in info["rarity"].items():
                where.setdefault(sp, []).append({"map": m["map"] or m["base_label"], "base_label": m["base_label"],
                                                 "method": meth, "chance_pct": r["chance_pct"],
                                                 "min_level": r["min_level"], "max_level": r["max_level"]})
    for v in where.values():
        v.sort(key=lambda x: (-x["chance_pct"], x["map"], x["method"]))
    hdr = d.header(["src/data/wild_encounters.json", "src/wild_encounter.c"])
    hdr["slot_probabilities_pct"] = got
    hdr["slot_probabilities_match_expected_gen3"] = got == expected
    hdr["slot_probabilities_note"] = (
        "Taken from the fields block of wild_encounters.json; src/wild_encounter.c selects slots with the "
        "ENCOUNTER_CHANCE_*_SLOT_n constants that the build generates from those same fields "
        "(wild_encounters.constants.json.txt), so code and json agree by construction. "
        "Result of comparing against the expected Gen-3 lists: %s." % ("IDENTICAL" if got == expected else "DIFFERENT"))
    hdr["encounter_rate_note"] = ("encounter_rate is the map's per-step base; WildEncounterCheck multiplies it by 16 and compares "
                                  "Random() % 2880 < rate (cap 2880), then modifiers (flute, cleanse tag, abilities, bike). "
                                  "Per-step chance = encounter_rate*16/2880.")
    hdr["ability_note"] = ("Static/Magnet Pull (land/water) force a matching-type slot 50%; Intimidate/Keen Eye/Cute Charm-style "
                           "effects change level/odds; chance_pct here is the unmodified slot table.")
    hdr["feebas"] = {
        "map": "MAP_ROUTE119", "species": "SPECIES_FEEBAS", "min_level": 20, "max_level": 25,
        "rule": "FishingWildEncounter -> CheckFeebas(): on Route 119 any rod; 50% roll (Random()%100 > 49 fails), then 6 'Feebas "
                "spots' are chosen among 447 fishing tiles (131+167+149) by an RNG seeded from dewfordTrends[0].rand (the "
                "Dewford trend seed); spots 1-3 are rerolled (inaccessible). If the fished tile's spot id is one of the 6 the "
                "encounter is Feebas instead of the rod table.",
        "tiles": "NOT STATICALLY EXTRACTABLE: the 6 tiles depend on the save's trend seed, which changes when the Dewford trend is "
                 "re-rolled. The decomp gives the algorithm, not coordinates; tile coordinates need the map data plus the seed.",
        "fishing_tiles_by_section": {"y 0-45": 131, "y 46-91": 167, "y 92-139": 149}}
    hdr["count_map_entries"] = len(maps)
    hdr["groups"] = [{"label": g["label"], "entries": len(g["encounters"])} for g in j["wild_encounter_groups"]]
    hdr["maps"] = maps
    hdr["where_to_find"] = dict(sorted(where.items()))
    write_json(os.path.join(out, "encounters.json"), hdr)
    return maps


STEPS = [("species", extract_species), ("moves", extract_moves), ("learnsets", extract_learnsets), ("encounters", extract_encounters)]


def run(decomp_root, out):
    os.makedirs(out, exist_ok=True)
    d = Decomp(decomp_root)
    c = Consts(d)
    ctx = {}
    for name, fn in STEPS:
        ctx[name] = fn(d, c, out)
    return ctx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decomp", required=True)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        with tempfile.TemporaryDirectory() as tmp:
            run(a.decomp, tmp)
            bad = []
            for fn in sorted(os.listdir(tmp)):
                p = os.path.join(a.out, fn)
                if not os.path.exists(p) or open(p, "rb").read() != open(os.path.join(tmp, fn), "rb").read():
                    bad.append(fn)
            if bad:
                print("CHECK FAILED, differ/missing:", ", ".join(bad))
                return 1
            print("CHECK OK: %d files identical" % len(os.listdir(tmp)))
            return 0
    run(a.decomp, a.out)
    print("wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
