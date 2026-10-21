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


def scan_map_references(root):
    """Walk data/ and src/ once. Returns (owner_refs, root_refs, map_dirs, altering_mentions, n_files, digest).
    Files are read raw (not through Decomp.read) so the 1500+ scanned files stay out of `_files`; their identity is
    recorded as one digest over the sorted (path, sha256) list instead."""
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
                if ALTERING_VAR in text and rel != "include/constants/vars.h":
                    mentions += [(rel, ln.strip()) for ln in text.splitlines() if ALTERING_VAR in ln]
    return owner_refs, root_refs, map_dirs, mentions, n, h.hexdigest()


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


def availability_rules(d, j):
    """Decide each table's availability. Returns (rules, label_of) where label_of[base_label] = (availability, source)
    and `rules` is the top-level `availability_rules` block: what each label means and the decomp lines behind it."""
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
    owner_refs, root_refs, map_dirs, mentions, n_files, digest = scan_map_references(d.root)
    check_altering_var_mentions(mentions)
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
        AV_NORMAL: {"meaning": "the map's own wild table, met in ordinary play (walking, surfing, fishing, Rock Smash). "
                               "For the Altering Cave that is set 1, because the set var a new game zeroes is added to "
                               "the first header. Conditional terrain still counts: e.g. ROUTE130 land exists only "
                               "while Mirage Island is shown.", "decomp": normal + gift[:4]},
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
    return rules, label_of


def extract_encounters(d, c, out):
    j = json.loads(d.read("src/data/wild_encounters.json"))
    rules, label_of = availability_rules(d, j)
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
            entry = {"group": g["label"], "base_label": e["base_label"], "map": e.get("map"),
                     "availability": av, "availability_source": av_src, "methods": {}}
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
                                                 "availability_source": m["availability_source"]})
    for v in where.values():
        v.sort(key=lambda x: (-x["chance_pct"], x["map"] or x["base_label"], x["method"]))
    # The consumer view: only what a player meets in normal play. A species with no normal row is absent here.
    normal_play = {}
    for sp, rows in where.items():
        keep = [r for r in rows if r["availability"] == AV_NORMAL]
        if keep:
            normal_play[sp] = keep
    hdr = d.header(sorted({"src/data/wild_encounters.json", "src/wild_encounter.c"} | d.cited))
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
    hdr["availability_note"] = (
        "Every maps[] entry and every where_to_find row carries `availability` (see availability_rules for what each "
        "value means and the decomp lines behind it) and a short `availability_source` (file:line). where_to_find "
        "keeps ALL tables (the raw facts); where_to_find_normal_play keeps only availability == 'normal', and is the "
        "index to use for 'where can a player find X in normal play'. `map` is null for Battle Frontier tables, "
        "which belong to no map; their label is in base_label.")
    hdr["availability_rules"] = rules
    hdr["maps"] = maps
    hdr["where_to_find"] = dict(sorted(where.items()))
    hdr["where_to_find_normal_play"] = dict(sorted(normal_play.items()))
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
        put("data/maps/Route101/scripts.inc", "setvar VAR_ALTERING_CAVE_WILD_SET, 3\n")
    for folder, (mid, warps) in maps.items():
        put("data/maps/%s/map.json" % folder, json.dumps(
            {"id": mid, "name": folder, "warps": [{"dest_map": w} for w in warps]}, indent=2) + "\n")
    j = {"wild_encounter_groups": [
        {"label": MAIN_GROUP, "encounters": [{"map": mp, "base_label": bl} for mp, bl in main_rows]},
        {"label": PYRAMID_GROUP, "encounters": [{"base_label": "gBattlePyramid_1"}]},
        {"label": PIKE_GROUP, "encounters": [{"base_label": "gBattlePike_1"}]}]}
    put("src/data/wild_encounters.json", json.dumps(j))
    return j


def selftest():
    """FAULT and CONTROL for each availability guard (G1-G4) and the reachability walk, on synthetic input.
    WHY: these guards only fire when the decomp changes, which the pinned clone never does, so without arms that
    feed them a changed input a deleted guard call would pass every real run unnoticed."""
    results = []

    def arm(name, fn, want_raise):
        try:
            fn()
            raised = False
        except SemanticsChanged:
            raised = True
        ok = raised == want_raise
        results.append(ok)
        print("%s  %s (%s)" % ("PASS" if ok else "FAIL", name, "raised" if raised else "accepted"))

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
            "gOldUnused1": AV_UNUSED, "gBattlePyramid_1": AV_PYRAMID, "gBattlePike_1": AV_PIKE}

    def tree_arm(name, change, want_raise):
        with tempfile.TemporaryDirectory() as root:
            j = _mini_decomp(root, change)
            try:
                _, label_of = availability_rules(Decomp(root), j)
                got = {bl: av for bl, (av, _) in label_of.items()}
                raised = False
            except SemanticsChanged:
                got, raised = None, True
        ok = raised if want_raise else got == want
        results.append(ok)
        print("%s  %s (%s)" % ("PASS" if ok else "FAIL", name, "raised" if raised else got))

    tree_arm("TREE CONTROL: the six tables get the six labels", None, False)
    tree_arm("TREE FAULT G1: a cited line removed from src/wild_encounter.c refuses", "drop_line", True)
    tree_arm("TREE FAULT G2: a second gWildMonHeaders entry for MAP_ROUTE101 refuses", "dup_header", True)
    tree_arm("TREE FAULT G3: a map script that sets the Altering Cave var refuses", "setvar", True)
    tree_arm("TREE FAULT G4: a wild map nothing names, without UNUSED in its id, refuses", "orphan", True)
    print("SELFTEST: %d of %d arms as required" % (sum(results), len(results)))
    return 0 if all(results) else 1


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
