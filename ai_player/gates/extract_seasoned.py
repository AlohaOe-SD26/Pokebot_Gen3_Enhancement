#!/usr/bin/env python3
"""Seasoned-player knowledge base extractor (USER RULING 40).

Parses the pret/pokeemerald decomp into static JSON under
ai_player/knowledge/seasoned/.  Standard library only.

  python3 ai_player/gates/extract_seasoned.py --decomp /tmp/pokeemerald
  python3 ai_player/gates/extract_seasoned.py --decomp /tmp/pokeemerald --check
  python3 ai_player/gates/extract_seasoned.py --selftest

--check re-extracts into a temp folder and fails if the committed files differ.
--selftest runs a FAULT and a CONTROL arm for every guard below on synthetic input (no decomp needed).

ENCOUNTER AVAILABILITY (added 2026-10-21, the KB1 decomp-confirmed semantic fixes F-1, F-2, F-4, F-5, F-6).
INTENT: a seasoned player knows the wild tables AND knows which of them a player actually meets in normal play.
WHY: the first KB1 extraction copied every wild table into `where_to_find` as if it were findable, so a consumer
asking "where do I find Bulbasaur?" got the Battle Pyramid, where Bulbasaur never appears (its header species is
only an index the game replaces). The raw facts are KEPT; each table and each where_to_find row now carries an
`availability` label and the decomp line that justifies it, and `where_to_find_normal_play` holds only the
`normal` rows, so a consumer that asks the normal-play question cannot get the other kinds by accident:
  normal                            the map's first gWildMonHeaders entry, met by walking/surfing/fishing/smashing
  battle_frontier_runtime_species   Battle Pyramid: the header species is an INDEX, replaced at runtime (F-1)
  battle_frontier_runtime_level     Battle Pike: the species is real, the level comes from the party (F-2)
  mystery_gift_required             Altering Cave sets 2-9: only a Mystery Gift script moves the set var (F-4)
  unreachable_unused_map            the unused Cave of Origin maps: nothing outside them names them (F-6)
F-5: a frontier table has no map; its where_to_find `map` is null and the label stays in `base_label` (before, the
label was substituted into `map`, a field that otherwise holds MAP_* ids).
Each rule's decomp citation is COMPUTED at extraction time (cite()), so it is true for the pinned decomp, and the
extractor REFUSES to write (SemanticsChanged) when a cited line or an assumed property is gone: on a different
decomp the rules must be re-adjudicated, not silently re-applied.

PROGRESSION GATES, CONDITIONS, FEEBAS AND NOTES (added 2026-10-21, the KB1 step-5 adversarial review).
  * requires='post_game' (with requires_gate and requires_source) on every table behind the Hall of Fame: the Altering
    Cave, Steven's cave in Meteor Falls, the Desert Underpass, the Safari Zone Northeast/Southeast expansion, Artisan
    Cave and the Battle Pike/Pyramid tables (POST_GAME_GATES; the top-level `progression_gates` block cites the
    lines). where_to_find_normal_play still holds every normal row; the new where_to_find_main_story holds only the
    ungated ones. GUARDS: G1 (each cited line), G5 (the gated edges are the only way into the gated region:
    gate_region / check_gate_region), G6 (the gate flag's only writers: check_flag_writers).
  * `conditions` per table method: Route 130 land only while Mirage Island is shown, and the two Shoal Cave rooms'
    water and rods only at high tide (CONDITIONS; the `conditions` block cites the lines). GUARD G7: a condition on a
    method the table lacks refuses.
  * SPECIES_FEEBAS rows in every index (special 'feebas_tiles', one per rod; chance_pct is per cast on a Feebas tile),
    every value read from src/wild_encounter.c (feebas_rows refuses when the reading fails or Feebas has a slot).
  * encounter_rate_note (the 4-step grace and the 60% new-metatile gate), ability_note (Cute Charm = gender, Magnet
    Pull land only) and species.json's wild_held_item_rule (the Altering Cave branch) are built from cited lines.
The verifier (verify_seasoned.py) re-derives all of it by a different reading; this file's --selftest feeds every
guard a changed input (FAULT) beside an unchanged one (CONTROL), so a deleted guard call turns an arm red.
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
        self.cited = set()  # files an availability rule quotes; they join encounters.json's _files
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
    held_text, held_cites = held_item_note(d)
    hdr["_notes"] = {
        # Corrected 2026-10-21 (step-5 review note): the Altering Cave branch was "has its own table", which hid that
        # its list species hold only the list item, at the rare chance, and that the 100% rule does not apply there.
        "wild_held_item_rule": held_text,
        "wild_held_item_decomp": held_cites,
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


# ---------------------------------------------------------------- encounter availability (F-1, F-2, F-4, F-5, F-6)
class SemanticsChanged(Exception):
    """A decomp fact an availability rule rests on is gone or different: re-adjudicate, do not extract."""


AV_NORMAL = "normal"
AV_PYRAMID = "battle_frontier_runtime_species"
AV_PIKE = "battle_frontier_runtime_level"
AV_GIFT = "mystery_gift_required"
AV_UNUSED = "unreachable_unused_map"
ALTERING_MAP = "MAP_ALTERING_CAVE"
ALTERING_VAR = "VAR_ALTERING_CAVE_WILD_SET"
ALTERING_GIFT_FILE = "data/scripts/gift_altering_cave.inc"
PYRAMID_GROUP = "gBattlePyramidWildMonHeaders"
PIKE_GROUP = "gBattlePikeWildMonHeaders"
MAIN_GROUP = "gWildMonHeaders"
MAP_TOKEN = re.compile(r"\bMAP_[A-Z0-9_]+\b")
SCAN_DIRS = ("data", "src")
SCAN_EXT = (".c", ".h", ".inc", ".s", ".json", ".pory")
# wild_encounters.json names every map with a table, so it would make each one look "referenced"; layouts name
# LAYOUT_* ids, not maps. Neither is a way for a player to get somewhere.
SCAN_SKIP_PREFIX = ("data/layouts/", "src/data/wild_encounters.json")

# ---------------------------------------------------------------- progression gates and table conditions (2026-10-21)
# INTENT: `normal` says HOW a table is met (walking, surfing, fishing); it does not say WHEN a player can first get
# there. A seasoned player planning a team before the Champion must know that the Safari Zone expansion, the Desert
# Underpass, Artisan Cave, the Altering Cave and Steven's cave in Meteor Falls open only after the Hall of Fame.
# WHY: the KB1 step-5 adversarial review found 20 species whose every normal-play row is behind the Hall of Fame,
# listed in where_to_find_normal_play without a caveat (finding 1). The fix keeps those rows (they ARE normal play,
# after the credits) and labels each table `requires: post_game` with the decomp lines that gate it; the new
# where_to_find_main_story index leaves them out.
# HOW THE LIST WAS DERIVED (from the decomp, 2026-10-21, pinned 731ad5bf): every script line in data/ that branches on
# FLAG_SYS_GAME_CLEAR, plus every flag data/scripts/hall_of_fame.inc sets or clears, was read; those that open or
# close the way to a map with a wild table are the five gates below. verify_seasoned.py re-derives the same set in a
# different way (a walk of every warp, connection and map script from the new-game start, with the flag unset).
# Each gate names its GATED EDGES (map folder -> map it leads to). GUARD G5 walks BACKWARDS from the gate's seed maps
# over every map folder that names a map, stopping only at a gated edge, and refuses unless (a) every gated edge is
# met and (b) the set of non-map files (C code, shared scripts) that name a map of that region is exactly the
# `root_mentions` below, each with the reason it is not a way in. A new warp into the region from anywhere else makes
# the walk spill into the main world, whose maps C code names, so (b) fails. GUARD G6 refuses unless the flag's
# writers are exactly the listed lines (the flag is set only by the Hall of Fame).
REQ_POST_GAME = "post_game"
GAME_CLEAR = "FLAG_SYS_GAME_CLEAR"
SAFARI_WORKERS = "FLAG_HIDE_SAFARI_ZONE_SOUTH_CONSTRUCTION_WORKERS"
HOF_LINES = (("data/maps/EverGrandeCity_HallOfFame/scripts.inc", "special GameClear"),
             ("src/post_battle_event_funcs.c", "int GameClear(void)"))
GAME_CLEAR_WRITERS = (("src/post_battle_event_funcs.c", "FlagSet(FLAG_SYS_GAME_CLEAR);"),)
FLAG_WRITE = re.compile(r"\b(?:setflag|clearflag)\s+(FLAG_\w+)|\bFlag(?:Set|Clear)\(\s*(FLAG_\w+)\s*\)")
_BF_ROOT_WHY = ("a test of the map the player is ALREADY in, or a list of such maps (Pokemon Centers, marts, save "
                "locations, the Frontier Pass map); read 2026-10-21, no warp")
POST_GAME_GATES = (
    {"id": "altering_cave_opened_at_game_clear",
     "meaning": "Route 103's ON_LOAD script turns the wall over the Altering Cave's warp tile (45,6) into a cave mouth "
                "only when FLAG_SYS_GAME_CLEAR is set, which GameClear sets after the Hall of Fame. Before that the "
                "warp tile is a wall. This gates every Altering Cave set, set 1 included.",
     "seeds": ("MAP_ALTERING_CAVE",), "groups": {},
     "edges": (("Route103", "MAP_ALTERING_CAVE"),),
     "flags": {GAME_CLEAR: GAME_CLEAR_WRITERS},
     "lines": (("data/maps/Route103/scripts.inc", "call_if_set FLAG_SYS_GAME_CLEAR, Route103_EventScript_OpenAlteringCave"),
               ("data/maps/Route103/scripts.inc", "setmetatile 45, 6, METATILE_General_CaveEntrance_Bottom, FALSE")),
     "root_mentions": {"src/wild_encounter.c": "GetCurrentMapWildMonHeaderId tests whether the player IS in the "
                                               "Altering Cave; a location test, not a way in"}},
    {"id": "meteor_falls_stevens_cave_opened_at_game_clear",
     "meaning": "Meteor Falls 1F_1R's ON_LOAD script opens the cave mouth over the warp tile (4,2) to Steven's cave "
                "only when FLAG_SYS_GAME_CLEAR is set. Before that the warp tile is a wall.",
     "seeds": ("MAP_METEOR_FALLS_STEVENS_CAVE",), "groups": {},
     "edges": (("MeteorFalls_1F_1R", "MAP_METEOR_FALLS_STEVENS_CAVE"),),
     "flags": {GAME_CLEAR: GAME_CLEAR_WRITERS},
     "lines": (("data/maps/MeteorFalls_1F_1R/scripts.inc",
                "call_if_set FLAG_SYS_GAME_CLEAR, MeteorFalls_1F_1R_EventScript_OpenStevensCave"),
               ("data/maps/MeteorFalls_1F_1R/scripts.inc",
                "setmetatile 4, 2, METATILE_MeteorFalls_CaveEntrance_Bottom, FALSE")),
     "root_mentions": {}},
    {"id": "desert_underpass_closed_until_game_clear",
     "meaning": "The Fossil Maniac's tunnel's ON_LOAD script puts a rock wall on the Desert Underpass warp tile (6,2) "
                "while FLAG_SYS_GAME_CLEAR is NOT set, so the underpass opens only after the Hall of Fame.",
     "seeds": ("MAP_DESERT_UNDERPASS",), "groups": {},
     "edges": (("Route114_FossilManiacsTunnel", "MAP_DESERT_UNDERPASS"),),
     "flags": {GAME_CLEAR: GAME_CLEAR_WRITERS},
     "lines": (("data/maps/Route114_FossilManiacsTunnel/scripts.inc",
                "call_if_unset FLAG_SYS_GAME_CLEAR, Route114_FossilManiacsTunnel_EventScript_CloseDesertUnderpass"),
               ("data/maps/Route114_FossilManiacsTunnel/scripts.inc",
                "setmetatile 6, 2, METATILE_Fallarbor_RedRockWall, TRUE")),
     "root_mentions": {}},
    {"id": "battle_frontier_ferry_after_game_clear",
     "meaning": "Artisan Cave and the Battle Pike and Pyramid lie on the Battle Frontier island, reached only by the "
                "S.S. Tidal from the Lilycove and Slateport harbors. Both ferry attendants refuse before "
                "FLAG_SYS_GAME_CLEAR is set. The Pike and Pyramid tables (no map of their own) are used only on the "
                "layouts cited below, which are Battle Frontier maps.",
     "seeds": ("MAP_ARTISAN_CAVE_1F", "MAP_ARTISAN_CAVE_B1F", "MAP_BATTLE_FRONTIER_BATTLE_PIKE_ROOM_WILD_MONS",
               "MAP_BATTLE_FRONTIER_BATTLE_PYRAMID_FLOOR"),
     "groups": {PIKE_GROUP: ("src/wild_encounter.c",
                             "if (gMapHeader.mapLayoutId == LAYOUT_BATTLE_FRONTIER_BATTLE_PIKE_ROOM_WILD_MONS)"),
                PYRAMID_GROUP: ("src/wild_encounter.c",
                                "if (gMapHeader.mapLayoutId == LAYOUT_BATTLE_FRONTIER_BATTLE_PYRAMID_FLOOR)")},
     "edges": (("LilycoveCity_Harbor", "MAP_BATTLE_FRONTIER_OUTSIDE_WEST"),
               ("SlateportCity_Harbor", "MAP_BATTLE_FRONTIER_OUTSIDE_WEST")),
     "flags": {GAME_CLEAR: GAME_CLEAR_WRITERS},
     "lines": (("data/maps/LilycoveCity_Harbor/scripts.inc",
                "goto_if_unset FLAG_SYS_GAME_CLEAR, LilycoveCity_Harbor_EventScript_FerryUnavailable"),
               ("data/maps/SlateportCity_Harbor/scripts.inc",
                "goto_if_set FLAG_SYS_GAME_CLEAR, SlateportCity_Harbor_EventScript_AskForTicket"),
               ("data/maps/LilycoveCity_Harbor/scripts.inc", "warp MAP_BATTLE_FRONTIER_OUTSIDE_WEST, 19, 67"),
               ("data/maps/SlateportCity_Harbor/scripts.inc", "warp MAP_BATTLE_FRONTIER_OUTSIDE_WEST, 19, 67")),
     "root_mentions": {
         "data/scripts/battle_pike.inc": "the Battle Pike's own room-to-room warps, run from inside the Pike",
         "src/data/heal_locations.json": "a fly and whiteout target; flying there needs a visit first",
         "src/field_door.c": _BF_ROOT_WHY, "src/field_specials.c": _BF_ROOT_WHY, "src/frontier_pass.c": _BF_ROOT_WHY,
         "src/party_menu.c": _BF_ROOT_WHY, "src/save_location.c": _BF_ROOT_WHY, "src/tv.c": _BF_ROOT_WHY}},
    {"id": "safari_zone_expansion_after_hall_of_fame",
     "meaning": "Two construction workers stand in the Safari Zone South area's only path east until the Hall of Fame "
                "script sets their hide flag; nothing else sets it. The North area's map also connects to the "
                "Northeast area, but no walkable tile pair crosses that edge from the part of North a player "
                "reaches (layout collision and elevation; verify_seasoned.py re-derives it with a flood fill).",
     "seeds": ("MAP_SAFARI_ZONE_NORTHEAST", "MAP_SAFARI_ZONE_SOUTHEAST"), "groups": {},
     "edges": (("SafariZone_South", "MAP_SAFARI_ZONE_SOUTHEAST"), ("SafariZone_North", "MAP_SAFARI_ZONE_NORTHEAST")),
     "flags": {SAFARI_WORKERS: (("data/scripts/hall_of_fame.inc", "setflag " + SAFARI_WORKERS),)},
     "lines": (("data/maps/SafariZone_South/map.json", '"flag": "%s"' % SAFARI_WORKERS),
               ("data/maps/SafariZone_South/map.json", '"map": "MAP_SAFARI_ZONE_SOUTHEAST",'),
               ("data/maps/SafariZone_North/map.json", '"map": "MAP_SAFARI_ZONE_NORTHEAST",'),
               ("data/maps/EverGrandeCity_HallOfFame/scripts.inc",
                "call EverGrandeCity_HallOfFame_EventScript_SetGameClearFlags")),
     "root_mentions": {}},
)

# Conditions: a method of a table that exists only while a script has swapped the map's layout. Not a progression
# gate: the condition can hold at any point of the game. verify_seasoned.py re-derives the (map, method) pairs by
# counting encounter tiles in every layout each map's scripts can load.
CONDITIONS = (
    {"id": "mirage_island_shown",
     "methods": {"MAP_ROUTE130": ("land",)},
     "meaning": "Route 130's only land tiles are on Mirage Island, in LAYOUT_ROUTE130_MIRAGE_ISLAND. The map's "
                "ON_TRANSITION script loads that layout only when IsMirageIslandPresent() is TRUE: some party "
                "Pokemon's personality, low 16 bits, equals the high 16 bits of the mirage value, which "
                "UpdateMirageRnd re-rolls each day. With six party Pokemon that is about 6 in 65536 on a given "
                "day. The water and fishing tables need no condition.",
     "lines": (("src/time_events.c", "u16 rnd = GetMirageRnd() >> 16;"),
               ("src/time_events.c", "if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) && "
                                     "(GetMonData(&gPlayerParty[i], MON_DATA_PERSONALITY) & 0xFFFF) == rnd)"),
               ("src/clock.c", "UpdateMirageRnd(daysSince);"),
               ("data/maps/Route130/scripts.inc", "specialvar VAR_RESULT, IsMirageIslandPresent"),
               ("data/maps/Route130/scripts.inc",
                "goto_if_eq VAR_RESULT, TRUE, Route130_EventScript_SetMirageIslandLayout"),
               ("data/maps/Route130/scripts.inc", "setmaplayoutindex LAYOUT_ROUTE130_MIRAGE_ISLAND"))},
    {"id": "shoal_cave_high_tide",
     "methods": {"MAP_SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM": ("water", "old_rod", "good_rod", "super_rod"),
                 "MAP_SHOAL_CAVE_LOW_TIDE_INNER_ROOM": ("water", "old_rod", "good_rod", "super_rod")},
     "meaning": "These two Shoal Cave rooms have no water at low tide. Their ON_TRANSITION scripts load the "
                "high-tide layout when FLAG_SYS_SHOAL_TIDE is set, and UpdateShoalTideFlag sets it from the game "
                "clock's hour: high tide at hours %s. Surfing and fishing there need high tide; the land table "
                "is met at either tide.",
     "lines": (("src/time_events.c", "if (tide[gLocalTime.hours])"),
               ("src/time_events.c", "FlagSet(FLAG_SYS_SHOAL_TIDE);"),
               ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc",
                "goto_if_set FLAG_SYS_SHOAL_TIDE, ShoalCave_LowTideEntranceRoom_EventScript_SetHighTide"),
               ("data/maps/ShoalCave_LowTideEntranceRoom/scripts.inc",
                "setmaplayoutindex LAYOUT_SHOAL_CAVE_HIGH_TIDE_ENTRANCE_ROOM"),
               ("data/maps/ShoalCave_LowTideInnerRoom/scripts.inc",
                "goto_if_set FLAG_SYS_SHOAL_TIDE, ShoalCave_LowTideInnerRoom_EventScript_SetHighTide"),
               ("data/maps/ShoalCave_LowTideInnerRoom/scripts.inc",
                "setmaplayoutindex LAYOUT_SHOAL_CAVE_HIGH_TIDE_INNER_ROOM"))},
)


def cite_lines(text, needle):
    """GUARD G1: the 1-based numbers of the lines whose stripped text is exactly `needle`; raises when there is none.
    WHY: a rule's justification must be TRUE for the decomp it was extracted from. Looking the line up (instead of
    hard-coding a number) keeps the citation right when lines move, and refuses when the code itself changed."""
    found = [i for i, ln in enumerate(text.splitlines(), 1) if ln.strip() == needle]
    if not found:
        raise SemanticsChanged("cited line not found: %r" % needle)
    return found


def cite(d, rel, needle):
    d.cited.add(rel)
    return "%s:%s %s" % (rel, ",".join(str(n) for n in cite_lines(d.read(rel), needle)), needle)


def short_cites(cites):
    """'src/x.c:12 foo' + 'src/x.c:14 bar' -> 'src/x.c:12,14' (the per-row pointer into availability_rules)."""
    by = {}
    for c_ in cites:
        path, rest = c_.split(":", 1)
        by.setdefault(path, []).append(rest.split(" ", 1)[0])
    return "; ".join("%s:%s" % (p, ",".join(v)) for p, v in by.items())


def check_header_multiplicity(main_entries, n_altering_tables):
    """GUARD G2: in gWildMonHeaders only MAP_ALTERING_CAVE may own several headers, and exactly NUM_ALTERING_CAVE_TABLES.
    WHY: GetCurrentMapWildMonHeaderId (src/wild_encounter.c) returns the FIRST header whose map matches, adding the
    set var only for the Altering Cave; a second header on any other map would never be read, and the labels below
    would call it normal. `main_entries` is the list of (base_label, map) in file order."""
    count = {}
    for _, mp in main_entries:
        count[mp] = count.get(mp, 0) + 1
    bad = sorted(mp for mp, n in count.items() if n > 1 and mp != ALTERING_MAP)
    if bad:
        raise SemanticsChanged("maps with several gWildMonHeaders entries besides the Altering Cave: %s" % bad)
    if count.get(ALTERING_MAP, 0) != n_altering_tables:
        raise SemanticsChanged("Altering Cave headers %d != NUM_ALTERING_CAVE_TABLES %d"
                               % (count.get(ALTERING_MAP, 0), n_altering_tables))


def check_altering_var_mentions(mentions):
    """GUARD G3: every mention of VAR_ALTERING_CAVE_WILD_SET in data/ and src/ is either a VarGet read in C or a line
    of the Mystery Gift script data/scripts/gift_altering_cave.inc. `mentions` is a list of (rel path, stripped line).
    WHY: the label mystery_gift_required claims nothing else in the game moves the var off 0; any other mention (a
    script setvar, a C VarSet) must be adjudicated before the label can stand."""
    bad = [(rel, ln) for rel, ln in mentions
           if not (rel == ALTERING_GIFT_FILE or (rel.endswith(".c") and "VarGet(%s)" % ALTERING_VAR in ln))]
    if bad:
        raise SemanticsChanged("unexpected %s mention(s): %s" % (ALTERING_VAR, bad[:5]))
    if not any(rel == ALTERING_GIFT_FILE for rel, _ in mentions):
        raise SemanticsChanged("the Mystery Gift writer %s no longer names %s" % (ALTERING_GIFT_FILE, ALTERING_VAR))


def unreached_maps(owner_refs, root_refs):
    """The maps a BFS from `root_refs` cannot reach. `owner_refs` = {map id: maps its own folder's files name};
    `root_refs` = maps named by files that belong to no map (C code, shared scripts: the new-game warp, heal
    locations, fly targets...). An edge A -> B means a warp, connection or script in A's folder names B."""
    seen = set()
    todo = sorted(root_refs)
    for _ in range(MAX_ITER):
        if not todo:
            break
        m = todo.pop()
        if m in seen:
            continue
        seen.add(m)
        todo.extend(sorted(owner_refs.get(m, ())))
    else:
        # a cut-short walk would call reachable maps unreachable: refuse instead of labelling from a partial walk
        raise SemanticsChanged("map reference walk did not finish in %d steps" % MAX_ITER)
    return sorted(set(owner_refs) - seen)


def check_unused_names(unreached_wild):
    """GUARD G4: every wild-table map the scan cannot reach must be one the decomp itself NAMES unused.
    WHY: the scan only sees maps named in text. A map reached through a COMPUTED id (the Battle Pyramid squares are
    MAP_NUM(SQUARE01) + offset, src/battle_pyramid.c) looks unreached too, so the scan alone can call a real map
    unreachable. Requiring the decomp's own 'UNUSED' name as a second, independent condition keeps that error out;
    a wild map that fails it stops the extraction for a human to adjudicate."""
    bad = [m for m in unreached_wild if "UNUSED" not in m]
    if bad:
        raise SemanticsChanged("wild-table maps no reference reaches, without an UNUSED name: %s" % bad)


def scan_map_references(root, watch_flags=()):
    """Walk data/ and src/ once. Returns (owner_refs, root_refs, map_dirs, altering_mentions, n_files, digest,
    root_files_of, flag_writes): root_files_of = {map id: non-map files naming it}; flag_writes = {flag: [(rel, line)]}
    for each flag in `watch_flags`, every setflag/clearflag/FlagSet/FlagClear line that writes it.
    Files are read raw (not through Decomp.read) so the 1500+ scanned files stay out of `_files`; their identity is
    recorded as one digest over the sorted (path, sha256) list instead."""
    root_files_of = {}
    flag_writes = {f: [] for f in watch_flags}
    map_dirs = {}
    maps_root = os.path.join(root, "data", "maps")
    for name in sorted(os.listdir(maps_root)):
        p = os.path.join(maps_root, name, "map.json")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                map_dirs[name] = json.load(f)["id"]
    owner_refs = {mid: set() for mid in map_dirs.values()}
    root_refs = set()
    mentions = []
    h = hashlib.sha256()
    n = 0
    for base in SCAN_DIRS:
        for dp, dn, fn in os.walk(os.path.join(root, base)):
            dn.sort()
            for f in sorted(fn):
                rel = os.path.relpath(os.path.join(dp, f), root).replace("\\", "/")
                if not f.endswith(SCAN_EXT) or rel.startswith(SCAN_SKIP_PREFIX):
                    continue
                with open(os.path.join(dp, f), "rb") as fh:
                    raw = fh.read()
                n += 1
                h.update(("%s %s\n" % (rel, hashlib.sha256(raw).hexdigest())).encode())
                text = raw.decode("utf-8", errors="replace")
                refs = set(MAP_TOKEN.findall(text))
                parts = rel.split("/")
                owner = map_dirs.get(parts[2]) if rel.startswith("data/maps/") and len(parts) > 3 else None
                if owner:
                    owner_refs[owner] |= refs - {owner}
                else:
                    root_refs |= refs
                    for r in refs:
                        root_files_of.setdefault(r, set()).add(rel)
                if ALTERING_VAR in text and rel != "include/constants/vars.h":
                    mentions += [(rel, ln.strip()) for ln in text.splitlines() if ALTERING_VAR in ln]
                if any(f in text for f in flag_writes):
                    for ln in text.splitlines():
                        for m in FLAG_WRITE.finditer(ln):
                            if (m.group(1) or m.group(2)) in flag_writes:
                                flag_writes[m.group(1) or m.group(2)].append((rel, ln.strip()))
    return owner_refs, root_refs, map_dirs, mentions, n, h.hexdigest(), root_files_of, flag_writes


def namer_lines(root, map_dirs, mid):
    """'path:line' for every line in another map's folder that names `mid` (the evidence quoted for an unused map)."""
    out = []
    for name, owner in sorted(map_dirs.items()):
        if owner == mid:
            continue
        folder = os.path.join(root, "data", "maps", name)
        for f in sorted(os.listdir(folder)):
            with open(os.path.join(folder, f), encoding="utf-8", errors="replace") as fh:
                for i, ln in enumerate(fh, 1):
                    if re.search(r"\b%s\b" % mid, ln):
                        out.append("data/maps/%s/%s:%d" % (name, f, i))
    return out


def gate_region(seeds, edges, owner_refs, root_files_of):
    """The maps behind a gate: walk BACKWARDS from `seeds` over every map folder that names a map in the region,
    stopping only at a gated edge (holder map id, target map id) in `edges`. Returns (region, edges met, non-map
    files naming a region map). A namer that is not a gated edge joins the region, so a new way in spills the walk
    into the main world instead of being skipped."""
    named_by = {}
    for owner, refs in owner_refs.items():
        for r in refs:
            named_by.setdefault(r, set()).add(owner)
    region, met = set(), set()
    todo = list(seeds)
    for _ in range(MAX_ITER):
        if not todo:
            break
        m = todo.pop()
        if m in region:
            continue
        region.add(m)
        for owner in sorted(named_by.get(m, ())):
            if (owner, m) in edges:
                met.add((owner, m))
            elif owner not in region:
                todo.append(owner)
    else:
        raise SemanticsChanged("gate region walk did not finish in %d steps" % MAX_ITER)
    roots = set()
    for m in region:
        roots |= root_files_of.get(m, set())
    return region, met, roots


def check_gate_region(gate_id, edges, met, roots, want_roots):
    """GUARD G5: every gated edge still exists, and the non-map files that name the gated region are exactly the
    listed ones. WHY: the post_game label claims the gated edges are the ONLY way in. A warp from an ungated map
    pulls that map into the region (gate_region), and from there the walk reaches maps that C code and shared
    scripts name, so the file set changes and the label is refused instead of silently kept."""
    if met != set(edges):
        raise SemanticsChanged("gate %s: gated edges %s not found as map references" % (gate_id, sorted(set(edges) - met)))
    if roots != set(want_roots):
        raise SemanticsChanged("gate %s: non-map files naming the region changed: new %s, gone %s"
                               % (gate_id, sorted(roots - set(want_roots)), sorted(set(want_roots) - roots)))


def check_flag_writers(flag, got, want):
    """GUARD G6: the lines that set or clear `flag` in data/ and src/ are exactly `want`. WHY: a gate holds only
    while the flag that opens it is written by the Hall of Fame and nothing else; a second writer (an earlier
    setflag, a clearflag) means the gate can open, or close, at another point of the game."""
    if sorted(set(got)) != sorted(set(want)):
        raise SemanticsChanged("%s writers changed: %s (expected %s)" % (flag, sorted(set(got)), sorted(set(want))))


def build_gates(d, owner_refs, root_files_of, flag_writes, map_dirs, gates):
    """Apply G1, G5 and G6 to every gate spec. Returns {gate id: the encounters.json block}."""
    out = {}
    for g in gates:
        edges = set()
        for folder, target in g["edges"]:
            if folder not in map_dirs:
                raise SemanticsChanged("gate %s: map folder %s is gone" % (g["id"], folder))
            edges.add((map_dirs[folder], target))
        region, met, roots = gate_region(g["seeds"], edges, owner_refs, root_files_of)
        check_gate_region(g["id"], edges, met, roots, g["root_mentions"])
        cites = [cite(d, rel, needle) for rel, needle in g["lines"]]
        for flag, writers in g["flags"].items():
            check_flag_writers(flag, flag_writes.get(flag, []), writers)
            cites += [cite(d, rel, ln) for rel, ln in writers]
        cites += [cite(d, rel, needle) for rel, needle in HOF_LINES]
        cites += [cite(d, rel, needle) for rel, needle in g["groups"].values()]
        out[g["id"]] = {"requires": REQ_POST_GAME, "meaning": g["meaning"], "seed_maps": list(g["seeds"]),
                        "groups": sorted(g["groups"]),
                        "gated_edges": [{"from": f, "to": t} for f, t in g["edges"]],
                        "region": sorted(region), "decomp": cites,
                        "root_mentions": dict(sorted(g["root_mentions"].items()))}
    return out


def build_conditions(d, j, conditions):
    """G1 for every condition's lines, and refuse when a named method is not in that map's table."""
    have = {}
    for g in j["wild_encounter_groups"]:
        if g["label"] != MAIN_GROUP:
            continue
        for e in g["encounters"]:
            meths = set()
            for k, names in (("land_mons", ("land",)), ("water_mons", ("water",)), ("rock_smash_mons", ("rock_smash",)),
                             ("fishing_mons", ("old_rod", "good_rod", "super_rod"))):
                if k in e:
                    meths |= set(names)
            have[e["map"]] = meths
    out = {}
    for c in conditions:
        for mp, meths in c["methods"].items():
            if not set(meths) <= have.get(mp, set()):
                raise SemanticsChanged("condition %s: %s has no %s table" % (c["id"], mp, sorted(set(meths) - have.get(mp, set()))))
        meaning = c["meaning"]
        if "%s" in meaning:  # the Shoal Cave tide hours, read from src/time_events.c tide[]
            t = d.read("src/time_events.c")
            body = re.search(r"static const u8 tide\[\]\s*=\s*\{(.*?)\};", t, flags=re.S)
            if not body:
                raise SemanticsChanged("src/time_events.c tide[] table not found")
            hours = [int(h) for v, h in re.findall(r"([01]),\s*//\s*(\d+)", body.group(1)) if v == "1"]
            if not hours:
                raise SemanticsChanged("src/time_events.c tide[] has no high-tide hour")
            meaning = meaning % ", ".join("%02d" % h for h in hours)
        out[c["id"]] = {"meaning": meaning, "methods": {k: list(v) for k, v in c["methods"].items()},
                        "decomp": [cite(d, rel, needle) for rel, needle in c["lines"]]}
    return out


def availability_rules(d, j, gates=None, conditions=None):
    """Decide each table's availability, progression gate and conditions. Returns (rules, label_of, extra):
    label_of[base_label] = (availability, source); `rules` is the top-level `availability_rules` block (what each
    label means and the decomp lines behind it); extra = {"gates", "requires_of", "conditions", "condition_of"}
    where requires_of[base_label] = gate id and condition_of[(base_label, method)] = condition id."""
    gates = POST_GAME_GATES if gates is None else gates
    conditions = CONDITIONS if conditions is None else conditions
    wc = "src/wild_encounter.c"
    pyr = "src/battle_pyramid.c"
    pike = "src/battle_pike.c"
    # normal: GetCurrentMapWildMonHeaderId returns the first header whose map matches (src/wild_encounter.c:305-333).
    normal = [cite(d, wc, "static u16 GetCurrentMapWildMonHeaderId(void)")]
    # F-1: src/battle_pyramid.c:1361-1362 overwrite the species with wildMons[species - 1] of the round's table;
    # called from src/wild_encounter.c:588 (and :722) right after TryGenerateWildMon on the Pyramid header.
    pyramid = [cite(d, pyr, "id = GetMonData(&gEnemyParty[0], MON_DATA_SPECIES, NULL) - 1;"),
               cite(d, pyr, "SetMonData(&gEnemyParty[0], MON_DATA_SPECIES, &wildMons[id].species);"),
               cite(d, wc, "GenerateBattlePyramidWildMon();")]
    # F-2: src/battle_pike.c:1118 (open level, then :1125 minus levelDelta) and :1132 (level 50) set the level; the
    # species is only mapped to an index (SpeciesToPikeMonId, :1644) and is not overwritten. Called from
    # src/wild_encounter.c:572.
    pike_c = [cite(d, pike, "monLevel = GetHighestLevelInPlayerParty();"),
              cite(d, pike, "monLevel -= wildMons[headerId][pikeMonId].levelDelta;"),
              cite(d, pike, "monLevel = FRONTIER_MAX_LEVEL_50 - wildMons[headerId][pikeMonId].levelDelta;"),
              cite(d, wc, "else if (!TryGenerateBattlePikeWildMon(TRUE))")]
    # F-4: src/wild_encounter.c:321 and :325 offset the Altering Cave header by the set var; a new game zeroes it
    # (src/new_game.c:160 ClearSav1, src/load_save.c:66 CpuFill16(0, &gSaveblock1...)); its only writer is the
    # Mystery Gift script data/scripts/gift_altering_cave.inc:3, included from data/mystery_gift.s:25 (G3 enforces it).
    gift = [cite(d, wc, "u16 alteringCaveId = VarGet(VAR_ALTERING_CAVE_WILD_SET);"),
            cite(d, wc, "i += alteringCaveId;"),
            cite(d, "src/new_game.c", "ClearSav1();"),
            cite(d, "src/load_save.c", "CpuFill16(0, &gSaveblock1, sizeof(struct SaveBlock1ASLR));"),
            cite(d, ALTERING_GIFT_FILE, "addvar VAR_ALTERING_CAVE_WILD_SET, 1"),
            cite(d, "data/mystery_gift.s", '.include "data/scripts/gift_altering_cave.inc"')]
    n_tables = int(re.search(r"#define NUM_ALTERING_CAVE_TABLES (\d+)",
                             d.read("src/data/wild_encounters.constants.json.txt")).group(1))
    d.cited.add("src/data/wild_encounters.constants.json.txt")
    main = [(e["base_label"], e.get("map")) for g in j["wild_encounter_groups"] if g["label"] == MAIN_GROUP
            for e in g["encounters"]]
    check_header_multiplicity(main, n_tables)
    watch = sorted({f for g in gates for f in g["flags"]})
    owner_refs, root_refs, map_dirs, mentions, n_files, digest, root_files_of, flag_writes = \
        scan_map_references(d.root, watch)
    check_altering_var_mentions(mentions)
    gate_blocks = build_gates(d, owner_refs, root_files_of, flag_writes, map_dirs, gates)  # map_dirs: folder -> id
    cond_blocks = build_conditions(d, j, conditions)
    wild_ids = {mp for _, mp in main}
    # F-6: the reference scan; G4 adds the decomp's own UNUSED name as a second condition. On the pinned decomp it
    # leaves exactly data/maps/CaveOfOrigin_UnusedRubySapphireMap1..3 (map.json:2 "id": ...UNUSED...), named only by
    # each other's warps (Map2/map.json:22 -> Map1, Map1/map.json:29 and Map3/map.json:22 -> Map2, Map2/map.json:29 ->
    # Map3) and by nothing in src/ (no CAVE_OF_ORIGIN map id appears in any .c/.h there, so no computed id either).
    unreached = [m for m in unreached_maps(owner_refs, root_refs) if m in wild_ids]
    check_unused_names(unreached)
    dir_of = {v: k for k, v in map_dirs.items()}
    unused_evidence = {}
    for m in unreached:
        rel = "data/maps/%s/map.json" % dir_of[m]
        unused_evidence[m] = {"id_line": cite(d, rel, '"id": "%s",' % m),
                              "named_only_by": namer_lines(d.root, map_dirs, m)}
    first_alter = next(bl for bl, mp in main if mp == ALTERING_MAP)
    label_of = {}
    for g in j["wild_encounter_groups"]:
        for e in g["encounters"]:
            bl, mp = e["base_label"], e.get("map")
            if g["label"] == PYRAMID_GROUP:
                label_of[bl] = (AV_PYRAMID, short_cites(pyramid))
            elif g["label"] == PIKE_GROUP:
                label_of[bl] = (AV_PIKE, short_cites(pike_c))
            elif g["label"] != MAIN_GROUP:
                raise SemanticsChanged("unknown wild encounter group %s" % g["label"])
            elif mp == ALTERING_MAP:
                label_of[bl] = ((AV_NORMAL, short_cites(gift[:4])) if bl == first_alter
                                else (AV_GIFT, short_cites(gift)))
            elif mp in unused_evidence:
                label_of[bl] = (AV_UNUSED, unused_evidence[mp]["id_line"].split(" ", 1)[0] + "; availability_rules")
            else:
                label_of[bl] = (AV_NORMAL, short_cites(normal))
    rules = {
        AV_NORMAL: {"meaning": "the map's own wild table, met in ordinary play (walking, surfing, fishing, Rock Smash) "
                               "once the player can get there. For the Altering Cave that is set 1, because the set "
                               "var a new game zeroes is added to the first header. `normal` says HOW a table is met, "
                               "not WHEN: a table behind the Hall of Fame carries requires='post_game' (see "
                               "progression_gates), and a method that exists only in a swapped layout carries a "
                               "condition (see conditions; e.g. ROUTE130 land only while Mirage Island is shown).",
                    "decomp": normal + gift[:4]},
        AV_PYRAMID: {"meaning": "Battle Pyramid: the header species is an INDEX (species - 1) into the round's own "
                                "table, and the game replaces species and level at runtime; a player never meets the "
                                "header species there. min/max level and species in these rows are NOT what is met.",
                     "decomp": pyramid},
        AV_PIKE: {"meaning": "Battle Pike: the species is real, but the level is set at runtime from the player's "
                             "party (open level) or 50 minus a delta (level 50); the rows' min/max level are header "
                             "values, not what is met.", "decomp": pike_c},
        AV_GIFT: {"meaning": "Altering Cave sets 2-%d: the game reads header 1 + %s, which a new game zeroes and only "
                             "a Mystery Gift script changes. In ordinary play only set 1 is live." % (n_tables, ALTERING_VAR),
                  "decomp": gift},
        AV_UNUSED: {"meaning": "a leftover map no warp, connection or script outside the unused group names, and "
                               "whose decomp id says UNUSED: its table exists in the ROM but no player reaches it.",
                    "scan": {"dirs": list(SCAN_DIRS), "extensions": list(SCAN_EXT), "skipped": list(SCAN_SKIP_PREFIX),
                             "files": n_files, "digest": digest},
                    "maps": unused_evidence},
    }
    requires_of, condition_of = {}, {}
    for g in gates:
        gid = g["id"]
        for grp in j["wild_encounter_groups"]:
            for e in grp["encounters"]:
                if e.get("map") in g["seeds"] or grp["label"] in g["groups"]:
                    if e["base_label"] in requires_of:
                        raise SemanticsChanged("table %s is behind two gates" % e["base_label"])
                    requires_of[e["base_label"]] = gid
    for c_ in conditions:
        for grp in j["wild_encounter_groups"]:
            for e in grp["encounters"]:
                for meth in c_["methods"].get(e.get("map"), ()):
                    condition_of[(e["base_label"], meth)] = c_["id"]
    return rules, label_of, {"gates": gate_blocks, "requires_of": requires_of, "conditions": cond_blocks,
                             "condition_of": condition_of}


# ---------------------------------------------------------------- notes with decomp citations (2026-10-21)
def cite_quiet(d, rel, needle):
    """cite() for a note in a file whose header lists its own sources (it does not join encounters.json's _files)."""
    return "%s:%s %s" % (rel, ",".join(str(n) for n in cite_lines(d.read(rel), needle)), needle)


def _ln(cites, i):
    """'path:12,14' of the i-th full citation (the form a note's text quotes)."""
    return cites[i].split(" ", 1)[0]


def encounter_rate_note(d):
    """The step-level rule, with the two gates the first KB1 note left out (finding 3 of the step-5 review)."""
    wc, fca = "src/wild_encounter.c", "src/field_control_avatar.c"
    cites = [cite(d, wc, "static bool8 WildEncounterCheck(u32 encounterRate, bool8 ignoreAbility)"),  # 0
             cite(d, wc, "encounterRate *= 16;"),                                                       # 1
             cite(d, wc, "#define MAX_ENCOUNTER_RATE 2880"),                                            # 2
             cite(d, wc, "if (Random() % MAX_ENCOUNTER_RATE < encounterRate)"),                         # 3
             cite(d, wc, "encounterRate = encounterRate * 80 / 100;"),                                  # 4
             cite(d, fca, "if (sWildEncounterImmunitySteps < 4)"),                                      # 5
             cite(d, fca, "sWildEncounterImmunitySteps = 0;"),                                          # 6
             cite(d, "src/battle_setup.c", "RestartWildEncounterImmunitySteps();"),                     # 7
             cite(d, "src/overworld.c", "RestartWildEncounterImmunitySteps();"),                        # 8
             cite(d, wc, "static bool8 AllowWildCheckOnNewMetatile(void)"),                             # 9
             cite(d, wc, "if (Random() % 100 >= 60)"),                                                  # 10
             cite(d, wc, "else if (prevMetatileBehavior != curMetatileBehavior && !AllowWildCheckOnNewMetatile())")]  # 11
    text = ("encounter_rate is the map's per-step base. WildEncounterCheck (%s) multiplies it by 16 (%s), applies the "
            "modifiers (Mach/Acro Bike x0.8 %s; White/Black Flute; Cleanse Tag; lead ability: Stench and White Smoke "
            "halve it (Stench x3/4 on a Battle Pyramid floor), Illuminate and Arena Trap double it, Sand Veil halves "
            "it in a sandstorm), caps it at 2880 (%s) "
            "and passes when Random() %% 2880 < rate (%s). That check is not run on every step: (a) for 4 steps after "
            "each wild encounter, each battle start and each map change (a warp or walking across a map connection) "
            "no check runs (%s; the counter is reset at %s, at %s in Task_BattleStart and the first battle, and at "
            "%s in LoadMapFromCameraTransition and LoadMapFromWarp); (b) a step onto a tile whose metatile "
            "behaviour differs from the previous step's is "
            "checked only 60%% of the time (%s, %s; applied at %s for land and water). So encounter_rate*16/2880 "
            "is the chance on a CHECKED step, and the real per-step rate is lower."
            % (_ln(cites, 0), _ln(cites, 1), _ln(cites, 4), _ln(cites, 2), _ln(cites, 3), _ln(cites, 5),
               _ln(cites, 6), _ln(cites, 7), _ln(cites, 8), _ln(cites, 9), _ln(cites, 10), _ln(cites, 11)))
    return text, cites


def ability_note(d):
    """Lead-slot ability effects on what is met (finding: the first note misdescribed Cute Charm and Magnet Pull)."""
    wc = "src/wild_encounter.c"
    cites = [cite(d, wc, "if (TRY_GET_ABILITY_INFLUENCED_WILD_MON_INDEX(wildMonInfo->wildPokemon, TYPE_STEEL, "
                         "ABILITY_MAGNET_PULL, &wildMonIndex, NUM_LAND_MONS_ENCOUNTER_SLOTS))"),             # 0
             cite(d, wc, "if (TRY_GET_ABILITY_INFLUENCED_WILD_MON_INDEX(wildMonInfo->wildPokemon, TYPE_ELECTRIC, "
                         "ABILITY_STATIC, &wildMonIndex, NUM_LAND_MONS_ENCOUNTER_SLOTS))"),                  # 1
             cite(d, wc, "if (TRY_GET_ABILITY_INFLUENCED_WILD_MON_INDEX(wildMonInfo->wildPokemon, TYPE_ELECTRIC, "
                         "ABILITY_STATIC, &wildMonIndex, NUM_WATER_MONS_ENCOUNTER_SLOTS))"),                 # 2
             cite(d, wc, "if (ability == ABILITY_HUSTLE || ability == ABILITY_VITAL_SPIRIT || ability == ABILITY_PRESSURE)"),  # 3
             cite(d, wc, "if (ability == ABILITY_KEEN_EYE || ability == ABILITY_INTIMIDATE)"),            # 4
             cite(d, wc, "&& GetMonAbility(&gPlayerParty[0]) == ABILITY_CUTE_CHARM"),                     # 5
             cite(d, wc, "&& GetMonAbility(&gPlayerParty[0]) == ABILITY_SYNCHRONIZE"),                    # 6
             cite(d, wc, "static bool8 TryGetAbilityInfluencedWildMonIndex(const struct WildPokemon *wildMon, "
                         "u8 type, u8 ability, u8 *monIndex, u32 size)")]                                   # 7
    text = ("Lead-slot abilities change what is met; chance_pct here is the unmodified slot table. Magnet Pull "
            "(land only, %s) picks a Steel-type slot and Static (land %s and water %s) an Electric-type slot, each "
            "50%% of the time and only when the table has such a slot (%s). Hustle, Vital Spirit and Pressure give "
            "the slot's max level 50%% of the time (%s). Keen Eye and Intimidate, on a lead above level 5, drop 50%% "
            "of encounters with a wild Pokemon 5 or more levels below the lead (%s). Cute Charm makes a gendered "
            "wild Pokemon the lead's opposite gender 2/3 of the time (%s). Synchronize gives the lead's nature 50%% "
            "of the time (%s)."
            % tuple(_ln(cites, i) for i in (0, 1, 2, 7, 3, 4, 5, 6)))
    return text, cites


def held_item_note(d):
    """species.json's wild held-item rule, with the Altering Cave branch stated exactly (step-5 review note)."""
    pk = "src/pokemon.c"
    cites = [cite_quiet(d, pk, "u16 chanceNoItem = 45;"),                                             # 0
             cite_quiet(d, pk, "u16 chanceNotRare = 95;"),                                            # 1
             cite_quiet(d, pk, "chanceNoItem = 20;"),                                                 # 2
             cite_quiet(d, pk, "chanceNotRare = 80;"),                                                # 3
             cite_quiet(d, pk, "if (gMapHeader.mapLayoutId == LAYOUT_ALTERING_CAVE)"),               # 4
             cite_quiet(d, pk, "if (rnd < chanceNotRare)"),                                           # 5
             cite_quiet(d, pk, "SetMonData(&gEnemyParty[0], MON_DATA_HELD_ITEM, "
                               "&sAlteringCaveWildMonHeldItems[alteringCaveId].item);"),              # 6
             cite_quiet(d, pk, "if (gSpeciesInfo[species].itemCommon == gSpeciesInfo[species].itemRare && "
                               "gSpeciesInfo[species].itemCommon != ITEM_NONE)"),                     # 7
             cite_quiet(d, pk, "static const struct SpeciesItem sAlteringCaveWildMonHeldItems[] =")]  # 8
    text = ("src/pokemon.c SetWildMonHeldItem: roll 0-99; <45 none, <95 itemCommon (50%%), else itemRare (5%%) "
            "(%s, %s); if both slots are the same non-NONE item it is held 100%% (%s). A lead with Compound Eyes "
            "uses 20/60/20 instead (%s, %s). Not applied for legendary/trainer/pyramid/pike battles. In the Altering "
            "Cave (%s) a species listed in sAlteringCaveWildMonHeldItems (%s: the set 2-9 species) holds only that "
            "list's item, on the rare roll alone: 5%%, or 20%% with Compound Eyes (%s, %s); there it never holds its "
            "own itemCommon/itemRare. Any other species there (set 1's Zubat) uses the 45/50/5 roll WITHOUT the "
            "both-slots-equal 100%% rule, which applies only outside the Altering Cave."
            % (_ln(cites, 0), _ln(cites, 1), _ln(cites, 7), _ln(cites, 2), _ln(cites, 3), _ln(cites, 4),
               _ln(cites, 8), _ln(cites, 5), _ln(cites, 6)))
    return text, cites


def feebas_rows(d, rods, where):
    """SPECIES_FEEBAS where_to_find rows (finding 2 of the step-5 review: the index omitted the only route to
    Milotic). Every value is read from src/wild_encounter.c; refuses when the reading fails, and when `where` (the
    slot-built index) already holds SPECIES_FEEBAS, because then the special rows would duplicate or contradict it."""
    if "SPECIES_FEEBAS" in where:
        raise SemanticsChanged("SPECIES_FEEBAS now has a wild slot; re-adjudicate the special feebas_tiles rows")
    wc = "src/wild_encounter.c"
    t = d.read(wc)
    m = re.search(r"static const struct WildPokemon sWildFeebas = \{(\d+), (\d+), (SPECIES_\w+)\};", t)
    body = re.search(r"static bool8 CheckFeebas\(void\)\n\{(.*?)\n\}\n", t, flags=re.S)
    fish = re.search(r"void FishingWildEncounter\(u8 rod\)\n\{(.*?)\n\}\n", t, flags=re.S)
    roll = re.search(r"if \(Random\(\) % 100 > (\d+)\)", body.group(1)) if body else None
    if not (m and body and fish and roll and "MAP_ROUTE119" in body.group(1)
            and fish.group(1).find("CheckFeebas()") != -1
            and fish.group(1).find("CheckFeebas()") < fish.group(1).find("rod")
            and m.group(3) == "SPECIES_FEEBAS"):
        raise SemanticsChanged("the Feebas rule in %s no longer reads as: any rod on Route 119, sWildFeebas levels" % wc)
    cites = [cite(d, wc, m.group(0)), cite(d, wc, "void FishingWildEncounter(u8 rod)"),
             cite(d, wc, "if (CheckFeebas() == TRUE)"),
             cite(d, wc, "if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_ROUTE119)"),
             cite(d, wc, roll.group(0))]
    chance = 100 - (int(roll.group(1)) + 1)
    rows = [{"map": "MAP_ROUTE119", "base_label": None, "group": None, "method": rod, "chance_pct": chance,
             "min_level": int(m.group(1)), "max_level": int(m.group(2)), "availability": AV_NORMAL,
             "availability_source": short_cites(cites), "requires": None, "requires_gate": None,
             "requires_source": None, "condition": None, "special": "feebas_tiles"} for rod in rods]
    return rows, cites, chance


def extract_encounters(d, c, out):
    j = json.loads(d.read("src/data/wild_encounters.json"))
    rules, label_of, extra = availability_rules(d, j)
    gate_src = {gid: short_cites(g["decomp"]) for gid, g in extra["gates"].items()}
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
            av, av_src = label_of[e["base_label"]]
            gid = extra["requires_of"].get(e["base_label"])
            entry = {"group": g["label"], "base_label": e["base_label"], "map": e.get("map"),
                     "availability": av, "availability_source": av_src,
                     "requires": REQ_POST_GAME if gid else None, "requires_gate": gid,
                     "requires_source": gate_src[gid] if gid else None,
                     "conditions": {meth: cid for (bl, meth), cid in sorted(extra["condition_of"].items())
                                    if bl == e["base_label"]},
                     "methods": {}}
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
                # F-5: `map` is the table's MAP_* id or null (a frontier table has none); before 2026-10-21 the
                # base_label was substituted here, a non-map string in a map field (maps[] already said null).
                where.setdefault(sp, []).append({"map": m["map"], "base_label": m["base_label"], "group": m["group"],
                                                 "method": meth, "chance_pct": r["chance_pct"],
                                                 "min_level": r["min_level"], "max_level": r["max_level"],
                                                 "availability": m["availability"],
                                                 "availability_source": m["availability_source"],
                                                 "requires": m["requires"], "requires_gate": m["requires_gate"],
                                                 "requires_source": m["requires_source"],
                                                 "condition": m["conditions"].get(meth), "special": None})
    # Feebas: a rule, not a slot (finding 2). Its rows join the indexes so "where is Feebas?" has an answer there.
    f_rows, f_cites, f_chance = feebas_rows(d, ("old_rod", "good_rod", "super_rod"), where)
    where["SPECIES_FEEBAS"] = f_rows
    for v in where.values():
        v.sort(key=lambda x: (-x["chance_pct"], x["map"] or x["base_label"], x["method"]))
    # The consumer views. normal_play: every row a player meets in ordinary play, at any point of the game (a species
    # with no normal row is absent). main_story: the normal rows with no progression gate, i.e. reachable before the
    # Hall of Fame; rows with a `condition` stay (the condition can hold before the Champion) and say so.
    normal_play, main_story = {}, {}
    for sp, rows in where.items():
        keep = [r for r in rows if r["availability"] == AV_NORMAL]
        if keep:
            normal_play[sp] = keep
        keep = [r for r in keep if r["requires"] is None]
        if keep:
            main_story[sp] = keep
    rate_text, rate_cites = encounter_rate_note(d)
    ab_text, ab_cites = ability_note(d)
    hdr = d.header(sorted({"src/data/wild_encounters.json", "src/wild_encounter.c"} | d.cited))
    hdr["slot_probabilities_pct"] = got
    hdr["slot_probabilities_match_expected_gen3"] = got == expected
    hdr["slot_probabilities_note"] = (
        "Taken from the fields block of wild_encounters.json; src/wild_encounter.c selects slots with the "
        "ENCOUNTER_CHANCE_*_SLOT_n constants that the build generates from those same fields "
        "(wild_encounters.constants.json.txt), so code and json agree by construction. "
        "Result of comparing against the expected Gen-3 lists: %s." % ("IDENTICAL" if got == expected else "DIFFERENT"))
    # Corrected 2026-10-21 (step-5 review finding 3): the old text called encounter_rate*16/2880 the per-step chance.
    hdr["encounter_rate_note"] = rate_text
    hdr["encounter_rate_decomp"] = rate_cites
    # Corrected 2026-10-21 (step-5 review note): Cute Charm sets gender, not level; Magnet Pull is land only.
    hdr["ability_note"] = ab_text
    hdr["ability_decomp"] = ab_cites
    hdr["feebas"] = {
        "map": "MAP_ROUTE119", "species": "SPECIES_FEEBAS", "min_level": f_rows[0]["min_level"],
        "max_level": f_rows[0]["max_level"],
        "rule": "FishingWildEncounter -> CheckFeebas(): on Route 119 any rod; %d%% roll (Random()%%100 > %d fails), then "
                "6 'Feebas spots' are chosen among 447 fishing tiles (131+167+149) by an RNG seeded from "
                "dewfordTrends[0].rand (the Dewford trend seed); spots 1-3 are rerolled (inaccessible). If the fished "
                "tile's spot id is one of the 6 the encounter is Feebas instead of the rod table."
                % (f_chance, 99 - f_chance),
        "tiles": "NOT STATICALLY EXTRACTABLE: the 6 tiles depend on the save's trend seed, which changes when the Dewford trend is "
                 "re-rolled. The decomp gives the algorithm, not coordinates; tile coordinates need the map data plus the seed.",
        "fishing_tiles_by_section": {"y 0-45": 131, "y 46-91": 167, "y 92-139": 149},
        "where_to_find_rows": "SPECIES_FEEBAS has one where_to_find row per rod (map MAP_ROUTE119, base_label null, "
                              "special 'feebas_tiles'). Their chance_pct (%d) is the chance PER CAST ON ONE OF THE 6 "
                              "FEEBAS TILES, not a slot share: on every other Route 119 tile it is 0." % f_chance,
        "decomp": f_cites}
    hdr["count_map_entries"] = len(maps)
    hdr["groups"] = [{"label": g["label"], "entries": len(g["encounters"])} for g in j["wild_encounter_groups"]]
    hdr["availability_note"] = (
        "Every maps[] entry and every where_to_find row carries `availability` (see availability_rules for what each "
        "value means and the decomp lines behind it) and a short `availability_source` (file:line). It also carries "
        "`requires` ('post_game' or null), `requires_gate` and `requires_source`: a table behind the Hall of Fame "
        "(see progression_gates). A row's `condition` (or a maps[] entry's `conditions`, per method) names a layout "
        "condition (see conditions). A row's `special` is 'feebas_tiles' for the Feebas rows (see feebas; their "
        "chance_pct is per cast on one of the 6 Feebas tiles, not a slot share), else null. where_to_find keeps "
        "ALL tables (the raw facts). where_to_find_normal_play keeps only availability == "
        "'normal' at ANY point of the game, the Hall of Fame included. where_to_find_main_story keeps the normal "
        "rows with requires == null: the index for 'where can a player find X before the Champion'. A species "
        "whose every normal row is post-game is in normal_play and NOT in main_story. `map` is null for Battle "
        "Frontier tables, which belong to no map; their label is in base_label.")
    hdr["availability_rules"] = rules
    hdr["progression_gates"] = extra["gates"]
    hdr["conditions"] = extra["conditions"]
    hdr["maps"] = maps
    hdr["where_to_find"] = dict(sorted(where.items()))
    hdr["where_to_find_normal_play"] = dict(sorted(normal_play.items()))
    hdr["where_to_find_main_story"] = dict(sorted(main_story.items()))
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


def _mini_decomp(root, change=None):
    """Write a minimal decomp tree that holds every line availability_rules() cites, plus four maps: ROUTE101 (named by
    C code), ALTERING_CAVE (named by ROUTE101's warp), OLD_UNUSED_MAP1 (named by nothing) and, for the 'orphan' arm,
    SECRET_ROOM (named by nothing, no UNUSED in its id). Returns the parsed wild_encounters json."""
    def put(rel, text):
        p = os.path.join(root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    wc = ["static u16 GetCurrentMapWildMonHeaderId(void)", "u16 alteringCaveId = VarGet(VAR_ALTERING_CAVE_WILD_SET);",
          "i += alteringCaveId;", "else if (!TryGenerateBattlePikeWildMon(TRUE))", "GenerateBattlePyramidWildMon();"]
    if change == "drop_line":
        wc.remove("i += alteringCaveId;")
    put("src/wild_encounter.c", "\n".join(wc) + "\n")
    put("src/battle_pyramid.c", "id = GetMonData(&gEnemyParty[0], MON_DATA_SPECIES, NULL) - 1;\n"
                                "SetMonData(&gEnemyParty[0], MON_DATA_SPECIES, &wildMons[id].species);\n")
    put("src/battle_pike.c", "monLevel = GetHighestLevelInPlayerParty();\n"
                             "monLevel -= wildMons[headerId][pikeMonId].levelDelta;\n"
                             "monLevel = FRONTIER_MAX_LEVEL_50 - wildMons[headerId][pikeMonId].levelDelta;\n")
    put("src/new_game.c", "ClearSav1();\nSetWarpDestination(MAP_ROUTE101);\n")
    put("src/load_save.c", "CpuFill16(0, &gSaveblock1, sizeof(struct SaveBlock1ASLR));\n")
    put(ALTERING_GIFT_FILE, "addvar VAR_ALTERING_CAVE_WILD_SET, 1\n")
    put("data/mystery_gift.s", '.include "data/scripts/gift_altering_cave.inc"\n')
    put("src/data/wild_encounters.constants.json.txt", "#define NUM_ALTERING_CAVE_TABLES 2\n")
    # the post-game gate of MINI_GATES: Route101 -> ALTERING_CAVE, opened by a FLAG_SYS_GAME_CLEAR script line
    put("src/post_battle_event_funcs.c", "int GameClear(void)\n{\n    FlagSet(FLAG_SYS_GAME_CLEAR);\n}\n")
    put("data/maps/EverGrandeCity_HallOfFame/scripts.inc", "special GameClear\n")
    r101 = ["call_if_set FLAG_SYS_GAME_CLEAR, Route101_EventScript_OpenCave"]
    maps = {"Route101": ("MAP_ROUTE101", ["MAP_ALTERING_CAVE"]), "AlteringCave": ("MAP_ALTERING_CAVE", []),
            "OldUnusedMap1": ("MAP_OLD_UNUSED_MAP1", [])}
    main_rows = [("MAP_ROUTE101", "gRoute101"), ("MAP_ALTERING_CAVE", "gAlteringCave1"),
                 ("MAP_ALTERING_CAVE", "gAlteringCave2"), ("MAP_OLD_UNUSED_MAP1", "gOldUnused1")]
    if change == "dup_header":
        main_rows.append(("MAP_ROUTE101", "gRoute101b"))
    if change == "orphan":
        maps["SecretRoom"] = ("MAP_SECRET_ROOM", [])
        main_rows.append(("MAP_SECRET_ROOM", "gSecretRoom"))
    if change == "setvar":
        r101.append("setvar VAR_ALTERING_CAVE_WILD_SET, 3")
    if change == "gate_leak":  # a second, ungated way in: Route101 -> Route102 -> the cave
        maps["Route101"] = ("MAP_ROUTE101", ["MAP_ALTERING_CAVE", "MAP_ROUTE102"])
        maps["Route102"] = ("MAP_ROUTE102", ["MAP_ALTERING_CAVE"])
    if change == "gate_moved":  # the gated edge is gone; the cave is reached through Route103 instead
        maps["Route101"] = ("MAP_ROUTE101", ["MAP_ROUTE103"])
        maps["Route103"] = ("MAP_ROUTE103", ["MAP_ALTERING_CAVE"])
    if change == "flag_writer":  # a second writer of the gate's flag
        r101.append("setflag FLAG_SYS_GAME_CLEAR")
    if change == "gate_line":
        r101.remove("call_if_set FLAG_SYS_GAME_CLEAR, Route101_EventScript_OpenCave")
    put("data/maps/Route101/scripts.inc", "\n".join(r101) + "\n")
    for folder, (mid, warps) in maps.items():
        put("data/maps/%s/map.json" % folder, json.dumps(
            {"id": mid, "name": folder, "warps": [{"dest_map": w} for w in warps]}, indent=2) + "\n")
    j = {"wild_encounter_groups": [
        {"label": MAIN_GROUP, "encounters": [dict({"map": mp, "base_label": bl},
                                                  **({"land_mons": {}} if bl == "gRoute101" else {}))
                                             for mp, bl in main_rows]},
        {"label": PYRAMID_GROUP, "encounters": [{"base_label": "gBattlePyramid_1"}]},
        {"label": PIKE_GROUP, "encounters": [{"base_label": "gBattlePike_1"}]}]}
    put("src/data/wild_encounters.json", json.dumps(j))
    return j


def selftest():
    """FAULT and CONTROL for each availability guard (G1-G4), the progression-gate guards (G5, G6, the double gate,
    a gone folder, the bounded region walk), the condition guard (G7, the tide table) and the Feebas reading, plus the
    reachability walk, on synthetic input.
    WHY: these guards only fire when the decomp changes, which the pinned clone never does, so without arms that
    feed them a changed input a deleted guard call would pass every real run unnoticed."""
    results = []

    def arm(name, fn, want_raise):
        crash = None
        try:
            fn()
            raised = False
        except SemanticsChanged:
            raised = True
        except Exception as exc:  # any other exception is a crash, never a refusal: the arm fails
            raised, crash = None, exc
        ok = raised == want_raise
        results.append(ok)
        print("%s  %s (%s)" % ("PASS" if ok else "FAIL", name,
                               "CRASHED: %r" % crash if crash else "raised" if raised else "accepted"))

    txt = "void f(void)\n{\n    x = 1;\n}\n"
    arm("G1 CONTROL: a present line is cited", lambda: cite_lines(txt, "x = 1;"), False)
    arm("G1 FAULT: a missing line refuses", lambda: cite_lines(txt, "x = 2;"), True)
    alter = [("gAlteringCave%d" % i, ALTERING_MAP) for i in range(1, 10)]
    arm("G2 CONTROL: one header per map + 9 Altering Cave headers",
        lambda: check_header_multiplicity([("gRoute101", "MAP_ROUTE101")] + alter, 9), False)
    arm("G2 FAULT: a second header on another map refuses",
        lambda: check_header_multiplicity([("gRoute101", "MAP_ROUTE101"), ("gRoute101b", "MAP_ROUTE101")] + alter, 9),
        True)
    arm("G2 FAULT: an Altering Cave header count != NUM_ALTERING_CAVE_TABLES refuses",
        lambda: check_header_multiplicity(alter[:8], 9), True)
    ok_m = [("src/wild_encounter.c", "u16 alteringCaveId = VarGet(VAR_ALTERING_CAVE_WILD_SET);"),
            (ALTERING_GIFT_FILE, "addvar VAR_ALTERING_CAVE_WILD_SET, 1")]
    arm("G3 CONTROL: VarGet reads + the gift script", lambda: check_altering_var_mentions(ok_m), False)
    arm("G3 FAULT: a setvar in a map script refuses", lambda: check_altering_var_mentions(
        ok_m + [("data/maps/AlteringCave/scripts.inc", "setvar VAR_ALTERING_CAVE_WILD_SET, 3")]), True)
    arm("G3 FAULT: a C VarSet refuses", lambda: check_altering_var_mentions(
        ok_m + [("src/foo.c", "VarSet(VAR_ALTERING_CAVE_WILD_SET, 2);")]), True)
    arm("G3 FAULT: the gift writer gone refuses", lambda: check_altering_var_mentions(ok_m[:1]), True)
    arm("G4 CONTROL: an unreached UNUSED map is accepted",
        lambda: check_unused_names(["MAP_CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP1"]), False)
    arm("G4 FAULT: an unreached map without an UNUSED name refuses",
        lambda: check_unused_names(["MAP_BATTLE_PYRAMID_SQUARE02"]), True)
    # The walk: A is a root; A -> B; C <-> D only name each other; E is named only by C.
    owner = {"A": {"B"}, "B": set(), "C": {"D", "E"}, "D": {"C"}, "E": set()}
    got = unreached_maps(owner, {"A"})
    ok = got == ["C", "D", "E"]
    results.append(ok)
    print("%s  walk CONTROL+FAULT: root-reached A,B kept; the closed C,D cluster and E (named only by it) unreached: %s"
          % ("PASS" if ok else "FAIL", got))
    global MAX_ITER
    saved = MAX_ITER
    MAX_ITER = 2  # the walk above needs 3 loop passes from A (pop A, pop B, see the empty list)
    try:
        arm("walk FAULT: a walk cut short by its bound refuses (never labels from a partial walk)",
            lambda: unreached_maps(owner, {"A"}), True)
    finally:
        MAX_ITER = saved
    # The same guards through availability_rules() on a tiny synthetic decomp tree, so a deleted guard CALL (not only
    # a broken guard function) turns an arm red.
    want = {"gRoute101": AV_NORMAL, "gAlteringCave1": AV_NORMAL, "gAlteringCave2": AV_GIFT,
            "gOldUnused1": AV_UNUSED, "gBattlePyramid_1": AV_PYRAMID, "gBattlePike_1": AV_PIKE,
            "requires": {"gAlteringCave1": "mini_gate", "gAlteringCave2": "mini_gate"},
            "conditions": {("gRoute101", "land"): "mini_cond"}}

    def tree_arm(name, change, want_raise, conditions=None):
        with tempfile.TemporaryDirectory() as root:
            j = _mini_decomp(root, change)
            try:
                _, label_of, extra = availability_rules(Decomp(root), j, gates=MINI_GATES,
                                                        conditions=conditions or MINI_CONDITIONS)
                got = {bl: av for bl, (av, _) in label_of.items()}
                got["requires"] = extra["requires_of"]
                got["conditions"] = extra["condition_of"]
                raised = False
            except SemanticsChanged:
                got, raised = None, True
        ok = raised if want_raise else got == want
        results.append(ok)
        print("%s  %s (%s)" % ("PASS" if ok else "FAIL", name, "raised" if raised else got))

    tree_arm("TREE CONTROL: the six tables get the six labels, the gate and the condition", None, False)
    tree_arm("TREE FAULT G1: a cited line removed from src/wild_encounter.c refuses", "drop_line", True)
    tree_arm("TREE FAULT G2: a second gWildMonHeaders entry for MAP_ROUTE101 refuses", "dup_header", True)
    tree_arm("TREE FAULT G3: a map script that sets the Altering Cave var refuses", "setvar", True)
    tree_arm("TREE FAULT G4: a wild map nothing names, without UNUSED in its id, refuses", "orphan", True)
    # 2026-10-21: the progression gate and the condition (step-5 review findings 1 and the Route 130 note)
    tree_arm("TREE FAULT G5: an ungated second way into the gated map (Route101 -> Route102 -> cave) refuses",
             "gate_leak", True)
    tree_arm("TREE FAULT G5: the gated edge gone, the map reached through another map instead, refuses",
             "gate_moved", True)
    tree_arm("TREE FAULT G6: a second writer of FLAG_SYS_GAME_CLEAR (a map script setflag) refuses", "flag_writer", True)
    tree_arm("TREE FAULT G1: the gate's cited flag line removed refuses", "gate_line", True)
    tree_arm("TREE FAULT G7: a condition on a method the map's table does not have refuses", None, True,
             conditions=(dict(MINI_CONDITIONS[0], methods={"MAP_ROUTE101": ("water",)}),))

    def gates_arm(name, gates, want_raise):
        with tempfile.TemporaryDirectory() as root:
            j = _mini_decomp(root, None)
            arm(name, lambda: availability_rules(Decomp(root), j, gates=gates, conditions=MINI_CONDITIONS), want_raise)

    arm_gate = MINI_GATES[0]
    gates_arm("GATES FAULT: one table behind two gates refuses",
              (arm_gate, dict(arm_gate, id="mini_gate_twice")), True)
    gates_arm("GATES FAULT: a gated edge from a map folder that is gone refuses",
              (dict(arm_gate, edges=(("NoSuchFolder", "MAP_ALTERING_CAVE"),)),), True)
    # gate_region on its own: A is named by B (not a gated edge), so the walk needs 3 passes (A, B, the empty list)
    arm("GATES CONTROL: a gate region walk within its bound finishes",
        lambda: gate_region(("A",), set(), {"B": {"A"}}, {}), False)
    saved = MAX_ITER
    MAX_ITER = 2
    try:
        arm("GATES FAULT: a gate region walk cut short by its bound refuses (never labels from a partial walk)",
            lambda: gate_region(("A",), set(), {"B": {"A"}}, {}), True)
    finally:
        MAX_ITER = saved
    # the Shoal Cave tide hours are read from src/time_events.c tide[]; no table (or no high-tide hour) refuses
    tide_cond = ({"id": "tide", "methods": {"MAP_ROUTE101": ("land",)}, "meaning": "hours %s",
                  "lines": (("src/wild_encounter.c", "static u16 GetCurrentMapWildMonHeaderId(void)"),)},)
    for name, text, want_raise in (
            ("TIDE CONTROL: hours read from tide[]", "static const u8 tide[] =\n{\n    0, // 00\n    1, // 01\n};\n", False),
            ("TIDE FAULT: no tide[] table refuses", "int x;\n", True),
            ("TIDE FAULT: a tide[] with no high-tide hour refuses", "static const u8 tide[] =\n{\n    0, // 00\n};\n", True)):
        with tempfile.TemporaryDirectory() as root:
            j = _mini_decomp(root, None)
            with open(os.path.join(root, "src", "time_events.c"), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            got = {}

            def go():
                got.update(build_conditions(Decomp(root), j, tide_cond))
            arm(name, go, want_raise)
            if not want_raise:
                ok = got.get("tide", {}).get("meaning") == "hours 01"
                results.append(ok)
                print("%s  TIDE CONTROL value: 'hours 01' (%s)" % ("PASS" if ok else "FAIL", got.get("tide", {}).get("meaning")))
    # Feebas (step-5 review finding 2): feebas_rows reads every value from src/wild_encounter.c and refuses otherwise.
    feebas_c = ("static const struct WildPokemon sWildFeebas = {20, 25, SPECIES_FEEBAS};\n"
                "static bool8 CheckFeebas(void)\n{\n"
                "    if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_ROUTE119)\n"
                "        if (Random() % 100 > 49)\n}\n"
                "void FishingWildEncounter(u8 rod)\n{\n    if (CheckFeebas() == TRUE)\n"
                "        x = GenerateFishingWildMon(info, rod);\n}\n")

    def feebas_arm(name, text, where, want_raise):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "src"))
            with open(os.path.join(root, "src", "wild_encounter.c"), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            got = None

            def go():
                nonlocal got
                got = feebas_rows(Decomp(root), ("old_rod", "good_rod", "super_rod"), where)
            arm(name, go, want_raise)
        if not want_raise and got is not None:
            rows, _, chance = got
            ok = (chance == 50 and [(r["method"], r["min_level"], r["max_level"], r["map"]) for r in rows]
                  == [(rod, 20, 25, "MAP_ROUTE119") for rod in ("old_rod", "good_rod", "super_rod")])
            results.append(ok)
            print("%s  FEEBAS CONTROL values: 3 rods, levels 20-25, MAP_ROUTE119, chance 50" % ("PASS" if ok else "FAIL"))

    feebas_arm("FEEBAS CONTROL: the rule reads (any rod, Route 119, sWildFeebas)", feebas_c, {}, False)
    feebas_arm("FEEBAS FAULT: CheckFeebas no longer tests MAP_ROUTE119 refuses",
               feebas_c.replace("MAP_ROUTE119", "MAP_ROUTE120"), {}, True)
    # every cited line still present, only the READING changes: these turn red only through feebas_rows' own check
    feebas_arm("FEEBAS FAULT: sWildFeebas names another species (cited lines intact) refuses",
               feebas_c.replace("SPECIES_FEEBAS}", "SPECIES_MAGIKARP}"), {}, True)
    feebas_arm("FEEBAS FAULT: the rod table is used before CheckFeebas (cited lines intact) refuses",
               feebas_c.replace("    if (CheckFeebas() == TRUE)\n        x = GenerateFishingWildMon(info, rod);\n",
                                "    x = GenerateFishingWildMon(info, rod);\n    if (CheckFeebas() == TRUE)\n"),
               {}, True)
    feebas_arm("FEEBAS FAULT: SPECIES_FEEBAS already has a wild slot refuses (re-adjudicate the special rows)",
               feebas_c, {"SPECIES_FEEBAS": [{}]}, True)
    print("SELFTEST: %d of %d arms as required" % (sum(results), len(results)))
    return 0 if all(results) else 1


# The synthetic gate and condition the selftest's mini decomp is built for (see _mini_decomp).
MINI_GATES = ({"id": "mini_gate", "meaning": "m", "seeds": ("MAP_ALTERING_CAVE",), "groups": {},
               "edges": (("Route101", "MAP_ALTERING_CAVE"),), "flags": {GAME_CLEAR: GAME_CLEAR_WRITERS},
               "lines": (("data/maps/Route101/scripts.inc",
                          "call_if_set FLAG_SYS_GAME_CLEAR, Route101_EventScript_OpenCave"),),
               "root_mentions": {}},)
MINI_CONDITIONS = ({"id": "mini_cond", "methods": {"MAP_ROUTE101": ("land",)}, "meaning": "m",
                    "lines": (("src/wild_encounter.c", "static u16 GetCurrentMapWildMonHeaderId(void)"),)},)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decomp")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.decomp:
        ap.error("--decomp is required (except with --selftest)")
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
    try:
        sys.exit(main())
    except SemanticsChanged as exc:
        print("REFUSED (an availability rule's decomp fact changed; re-adjudicate before extracting):", exc)
        sys.exit(2)
