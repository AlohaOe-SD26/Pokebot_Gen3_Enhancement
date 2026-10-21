"""GATE: cross-check KB1's seasoned knowledge (`ai_player/knowledge/seasoned/*.json`) against the in-tree sources that
were NOT made by KB1's extractor (spec S3-1 step 4 V5, `ai-research-notes/2026-10-19-BUILD-SPECS-step-3.md`).

WHY. KB1's own gates (`extract_seasoned.py --check`, `verify_seasoned.py`) re-read the pinned decomp with the SAME reading
the extractor used, so a systematic misreading passes both. This file compares KB1 with data that took a different road
to the same facts, and every difference must carry a STATED reason (the tables below are data, not prose).

    X1  moves:   ai_player/knowledge/moves.json            vs seasoned moves.json      type, power, accuracy, PP, priority
    X2  species: ai_player/knowledge/species.json          vs seasoned species.json    types, six base stats, catch rate,
                                                                                         experience yield
    X3  species: sandbox-pokebot/modules/data/species.json vs seasoned species.json + learnsets.json, JOINED ON NATIONAL
                 DEX (names differ): types, abilities, stats, catch rate, gender byte, egg groups, wild held items,
                 level-up (level, move), TM/HM, tutor, egg moves
    X4  encounters: sandbox-pokebot/modules/data/emerald_rarity.json vs seasoned encounters.json
                 `where_to_find_normal_play` (the rows KB1 labels availability=normal): the species set, then per
                 species the set of maps and the best per-map-and-method rate. The check is not "equal" but "every
                 difference carries a stated reason" (GAP_SPECIES, X4_SCOPE, FIELD_REASONS). Both sides describe
                 what a player meets in ordinary play, so they are compared like for like.
                 X4 also ties KB1's `unreachable_unused_map` labels to the rarity file's own EXCLUDED list (an
                 independent measurement: "no warp reaches it"), each leftover entry carrying a stated reason.
                 KB1's Feebas rule rows (special 'feebas_tiles', added 2026-10-21) are projected away by the scope
                 rule feebas_rule_rows: the rarity file records Feebas as 'special' with no map, the same fact.
                 X4 does not read `requires`/`where_to_find_main_story`: the rarity file has no notion of the Hall
                 of Fame, so the post-game gates are verified only by verify_seasoned.py.
    NON-VACUITY: each X compares at least 90 % of the smaller side, so a join that matches nothing cannot pass.

CHANGED 2026-10-21 (the KB1 semantic fixes F-1, F-2, F-4, F-5, F-6). X4 used to read KB1's full `where_to_find` and
project away, by three scope rules of its own, the Battle Pyramid/Pike rows, the Altering Cave sets 2-9 and the unused
Cave of Origin maps, and to explain 8 Pyramid placeholder species and 3 Pike species as "only in seasoned". KB1 now
LABELS those rows itself (decomp-cited, verified by verify_seasoned.py) and keeps them out of its normal-play index,
so the three rules and the 11 Pike/Pyramid gap reasons became stale and were removed: a stale reason is a failure
here, so leaving them would have turned this gate red. WHY X4 reads the normal-play index rather than re-filtering:
that index is what a consumer asks, so it is the thing worth cross-checking; a label leak (a Pyramid row marked
normal) now shows up as an unexplained species or map, which fault arms F8-F11 prove.

WHAT THESE CHECKS CAN AND CANNOT SEE (read this before trusting a PASS).
  * ‼ AGREEMENT CERTIFIES NOTHING. Every source here descends from the same game: the decomp (KB1), the ROM (the rarity
    file, read by our ROM reader), and the upstream pokebot's species/moves data (origin not re-proven here).
    ⛔ X2 IS NOT INDEPENDENT OF X3: `ai_player/knowledge/{species,moves}.json` were EXTRACTED FROM
    `sandbox-pokebot/modules/data/{species,moves}.json` (their own `provenance.source`). X1-X4 FIND DISAGREEMENTS to
    adjudicate by hand against the decomp; they do not certify the rows that agree.
  * Types are compared as SETS: the sandbox data and ai_player/knowledge store types alphabetically, so type ORDER
    (type1/type2) is invisible here.
  * The sandbox level-up learnset is a dict keyed by move, so a move learned at several levels (Smeargle's Sketch)
    keeps ONE level there; X3 accepts it when that level is one of KB1's levels and says so (reason R-LVL-DICT).
  * X4 sees the 131 species both files hold and the set of species each holds; it cannot see slot levels, methods or
    the encounter rate. The rarity file reads only `gWildMonHeaders` (first header per map), so it has no counterpart
    for the rows KB1 labels battle_frontier_runtime_* or mystery_gift_required: X4 cannot confirm those labels, only
    notice a row that LEAKS into the normal-play index (verify_seasoned.py re-derives the labels from the decomp).
  * Nothing here reads the decomp, so a value BOTH sides got wrong passes. The adversarial pass (S3-1 step 5) exists
    for that.

MERGE STATE. Until KB1 is merged the default folder does not exist. Then, and ONLY then (the KB1 branch tip is not an
ancestor of HEAD, by `git merge-base --is-ancestor`), this prints `SKIPPED: seasoned/ not merged yet` and exits 0. A
missing folder after the merge, an explicitly passed `--seasoned-dir` that is missing, or an undecidable merge state
(a shallow clone without the tip) is a FAILURE.

FAULT ARMS (built in, each beside its CONTROL): a planted move power (X1), a planted base stat (X2), a planted wrong
type (X3), a dropped map (X4), a broken join (the non-vacuity guard), a stale reason (a GAP_SPECIES entry for a
species that is not in the gap), and each fixed KB1 error leaked back into the normal-play index or labels (F8 a
Pyramid placeholder, F9 an Altering Cave set 6 row, F10 the unused Cave of Origin map 1, F11 a Pike-only species),
F12 an index leak, F13 a Wynaut row off its stated reason, F14 an old-format KB1, and (2026-10-21) F15 Feebas rows
without their `special` marker, F16 the Feebas rows gone (the scope rule goes stale), F17 a Wynaut row without its
Mirage Island condition and F18 a special Feebas row off Route 119 (only the scope rule's reason check sees it).
Each must turn its check red, naming the planted row.

Run:  cd tools/story-dev && py -3.12 selftest_seasoned_crosscheck.py [--seasoned-dir DIR] [--verbose]
Exit: 0 all checks pass (or SKIPPED before the merge); 1 any check failed or any difference is unexplained.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SEASONED_DEFAULT = REPO / "ai_player" / "knowledge" / "seasoned"
KN_MOVES = REPO / "ai_player" / "knowledge" / "moves.json"
KN_SPECIES = REPO / "ai_player" / "knowledge" / "species.json"
SB_SPECIES = REPO / "sandbox-pokebot" / "modules" / "data" / "species.json"
RARITY = REPO / "sandbox-pokebot" / "modules" / "data" / "emerald_rarity.json"
SEASONED_FILES = ("species.json", "moves.json", "learnsets.json", "encounters.json")

# The tip of origin/claude/kb1-seasoned-knowledge-cr1f5t (KB1 step 5 report), pinned by SHA so the check does not
# depend on a remote branch that may be deleted after the merge.
KB1_TIP = "880d7448d8647e28cf168f05cef5cf7825b44133"
GUARD_MIN = 0.90

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((name, bool(ok), detail))


def key(name: str) -> str:
    """The normalization `ai_player/gates/verify_knowledge.py key()` uses: 'Mud-slap' / MOVE_MUD_SLAP -> MUDSLAP."""
    name = name.replace("♀", "F").replace("♂", "M")
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def strip(token: str, prefix: str) -> str:
    return token[len(prefix):] if token.startswith(prefix) else token


def tkey(t: str) -> str:
    """A type as both sides spell it: 'Water' / WATER; '???' / MYSTERY."""
    return "MYSTERY" if t == "???" else key(strip(t, "TYPE_"))


# Egg-group names that `key()` does not reconcile: the sandbox's display name vs the decomp constant.
EGG_GROUP_ALIAS = {"NOEGGS": "NOEGGSDISCOVERED"}

# ======================================================================================== the reasons (DATA, not prose)
# X4, species present in ONE file only. Every entry names the side and the reason; the check requires the computed gap
# to equal this table EXACTLY in both directions (a missing row is an unexplained difference, an extra row is stale).
_LEG = ("rarity", "legendary: met in a static/scripted/roaming encounter, never in a wild table; the rarity file adds "
                  "it by its literal LEGENDARY list with maps=[] (rare_species_dataset.py LEGENDARY); KB1's "
                  "where_to_find indexes wild tables only")
GAP_SPECIES: dict[int, tuple[str, str]] = {
    **{n: _LEG for n in (144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 251,
                         377, 378, 379, 380, 381, 382, 383, 384, 385, 386)},
    360: ("seasoned", "Wynaut: its only wild table is ROUTE130 land (Mirage Island), which the rarity file EXCLUDES "
                      "(rare_species_dataset.py EXCLUDED (0, 45): 'Mirage Island only ... a PV-matched random day'); "
                      "KB1 keeps it as normal play, since Mirage Island is reachable on its day, and marks the rows "
                      "with condition 'mirage_island_shown' (this check asserts Wynaut's normal rows are all "
                      "MAP_ROUTE130 land with that condition)."),
}

# X4 scope rules: which seasoned rows are projected away before the per-species comparison, so that both sides
# describe the same set of tables. Each rule must remove at least one row (a rule that removes nothing is stale).
# The three 2026-10-21 rules (frontier, altering, excluded) became KB1's own availability labels, which keep those rows
# out of where_to_find_normal_play; the old "excluded" rule's ROUTE130 half removed no row of a species both files
# hold (Route 130 land is Wynaut only), so it is covered by Wynaut's gap reason.
# ADDED 2026-10-21 (KB1 step-5 review finding 2): KB1 now lists SPECIES_FEEBAS in its indexes as three rule rows
# (special 'feebas_tiles', MAP_ROUTE119, one per rod) instead of only in its `feebas` block. The rarity file lists
# Feebas with maps=[] and reason 'special' (no wild slot). Both describe the same fact, a rule rather than a table, so
# the rule rows are projected away and Feebas is compared as "no table on either side". Before this, Feebas was the
# rarity-only gap entry 349, which is now stale and removed.
X4_SCOPE: dict = {
    "feebas_rule_rows": ("KB1's Feebas rows describe CheckFeebas's tile rule, not a wild table; the rarity file "
                         "records the same species as 'special' with no map",
                         lambda e: e.get("special") == "feebas_tiles"),
}

# The rarity file's own EXCLUDED list (its measurement, not KB1's) must equal KB1's unreachable_unused_map maps plus
# the entries below, each with the reason KB1 does NOT mark it unreachable.
RARITY_EXCLUDED_KB1_NORMAL = {
    "ROUTE130": "Mirage Island land: rare (a PV-matched day) but reachable in ordinary play, so KB1 labels it normal "
                "with condition 'mirage_island_shown'; its only species, Wynaut, is the seasoned-only gap entry 360",
}

# Per-field differences that remain after the scope projection, each with its reason:
#   (check, subject, field) -> reason.   Empty when the sides agree everywhere they are compared.
FIELD_REASONS: dict[tuple[str, str, str], str] = {}

R_LVL_DICT = ("R-LVL-DICT: the sandbox level-up learnset is a dict keyed by move id, so a move KB1 lists at several "
              "levels keeps one level there; accepted when that level is one of KB1's")


# ================================================================================================ loading
def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_all(seasoned_dir: Path) -> dict:
    d = {name.split(".")[0]: load(seasoned_dir / name) for name in SEASONED_FILES}
    d["kn_moves"] = load(KN_MOVES)
    d["kn_species"] = load(KN_SPECIES)
    d["sb_species"] = load(SB_SPECIES)
    d["rarity"] = load(RARITY)
    return d


# ================================================================================================ the comparisons
def guard(label: str, compared: int, a: int, b: int) -> None:
    smaller = min(a, b)
    check(f"{label} non-vacuity: compared {compared} >= {GUARD_MIN:.0%} of the smaller side ({smaller})",
          smaller > 0 and compared >= GUARD_MIN * smaller, f"compared={compared} sides={a},{b}")


def explain(diffs: list[tuple], label: str) -> list[tuple]:
    """Return the differences no stated reason covers, and record a check for them."""
    unexplained = [d for d in diffs if (label, d[0], d[1]) not in FIELD_REASONS]
    detail = "; ".join(f"{s} {f}: other={o!r} seasoned={v!r}" for s, f, o, v in unexplained[:12])
    check(f"{label} every difference carries a stated reason ({len(diffs)} differences, "
          f"{len(unexplained)} unexplained)", not unexplained, detail)
    return unexplained


def x1(d: dict) -> list[tuple]:
    kn = {key(n): (n, v) for n, v in d["kn_moves"]["moves"].items()}
    sea = {key(m["name"]): m for m in d["moves"]["moves"]}
    common = sorted(set(kn) & set(sea))
    diffs = []
    for k in common:
        n, a = kn[k]
        b = sea[k]
        if tkey(a["type"]) != tkey(b["type"]):
            diffs.append((b["symbol"], "type", a["type"], b["type"]))
        for f in ("power", "pp", "priority"):
            if a[f] != b[f]:
                diffs.append((b["symbol"], f, a[f], b[f]))
        # ai_player/knowledge spells "never misses" as never_misses=True (accuracy kept as 100); the decomp as 0.
        if bool(a["never_misses"]) != (b["accuracy"] == 0) or (not a["never_misses"] and a["accuracy"] != b["accuracy"]):
            diffs.append((b["symbol"], "accuracy", (a["accuracy"], a["never_misses"]), b["accuracy"]))
    check("X1 move name sets agree (after key())", set(kn) == set(sea),
          f"only knowledge: {sorted(set(kn) - set(sea))[:8]} only seasoned: {sorted(set(sea) - set(kn))[:8]}")
    guard("X1", len(common), len(kn), len(sea))
    return diffs


def real_seasoned_species(d: dict) -> dict[int, dict]:
    return {s["national_dex"]: s for s in d["species"]["species"] if not s["placeholder"] and s["national_dex"]}


def x2(d: dict) -> list[tuple]:
    kn = {v["dex"]: (n, v) for n, v in d["kn_species"]["species"].items()}
    sea = real_seasoned_species(d)
    common = sorted(set(kn) & set(sea))
    diffs = []
    for nat in common:
        n, a = kn[nat]
        b = sea[nat]
        if key(n) != key(strip(b["symbol"], "SPECIES_")) and key(n) != key(b["name"]):
            diffs.append((b["symbol"], "name", n, b["name"]))
        if sorted({tkey(t) for t in a["types"]}) != sorted({tkey(t) for t in b["types"]}):
            diffs.append((b["symbol"], "types", a["types"], b["types"]))
        for f in ("hp", "attack", "defense", "speed", "sp_attack", "sp_defense"):
            if a["base"][f] != b["base_stats"][f]:
                diffs.append((b["symbol"], f"base {f}", a["base"][f], b["base_stats"][f]))
        if a["catch_rate"] != b["catch_rate"]:
            diffs.append((b["symbol"], "catch_rate", a["catch_rate"], b["catch_rate"]))
        if a["exp_yield"] != b["base_exp"]:
            diffs.append((b["symbol"], "exp_yield", a["exp_yield"], b["base_exp"]))
    check("X2 species dex sets agree", set(kn) == set(sea),
          f"only knowledge: {sorted(set(kn) - set(sea))[:8]} only seasoned: {sorted(set(sea) - set(kn))[:8]}")
    guard("X2", len(common), len(kn), len(sea))
    return diffs


def sandbox_real(d: dict) -> dict[int, dict]:
    """The sandbox's real species by national dex. Index 0 ('??????????', which carries national 151 and all-zero stats)
    and the 25 '?' old-Unown fillers (national 387+) are placeholders, skipped by name."""
    out = {}
    for e in d["sb_species"]:
        if e["name"] in ("??????????", "?"):
            continue
        if e["national_dex_number"] in out:
            raise ValueError(f"sandbox national {e['national_dex_number']} twice")
        out[e["national_dex_number"]] = e
    return out


def x3(d: dict) -> list[tuple]:
    sb = sandbox_real(d)
    sea = real_seasoned_species(d)
    learn = {s["symbol"]: s for s in d["learnsets"]["species"]}
    move_sym = {m["id"]: m["symbol"] for m in d["moves"]["moves"]}
    common = sorted(set(sb) & set(sea))
    diffs = []
    # Per-field exercise counts: a field that is empty on BOTH sides compares nothing, so each list field must be
    # non-empty on both sides for enough species (FIELD_MIN) or its agreement is vacuous.
    exercised = {"wild_held_items": 0, "level_up": 0, "tm_hm": 0, "tutor": 0, "egg": 0, "abilities": 0}
    for nat in common:
        a, b = sb[nat], sea[nat]
        sym = b["symbol"]
        ls0 = learn.get(sym) or {}
        exercised["wild_held_items"] += bool(a["held_items_rse"]) and bool(b["wild_held_items"])
        exercised["abilities"] += bool(b["abilities"])
        for f, g in (("level_up", "level_up"), ("tm_hm", "tm_hm"), ("tutor", "tutor"), ("egg", "egg")):
            exercised[f] += bool(a["learnset"][f]) and bool(ls0.get(g))
        if sorted({tkey(t) for t in a["types"]}) != sorted({tkey(t) for t in b["types"]}):
            diffs.append((sym, "types", a["types"], b["types"]))
        ab_a = [key(x) for x in a["abilities"] if x != "-------"]
        ab_b = [key(strip(x, "ABILITY_")) for x in b["abilities"]]
        if ab_a != ab_b:
            diffs.append((sym, "abilities", a["abilities"], b["abilities"]))
        st = a["base_stats"]
        for f_sb, f_sea in (("hp", "hp"), ("attack", "attack"), ("defence", "defense"), ("speed", "speed"),
                            ("special_attack", "sp_attack"), ("special_defence", "sp_defense")):
            if st[f_sb] != b["base_stats"][f_sea]:
                diffs.append((sym, f"base {f_sea}", st[f_sb], b["base_stats"][f_sea]))
        if a["catch_rate"] != b["catch_rate"]:
            diffs.append((sym, "catch_rate", a["catch_rate"], b["catch_rate"]))
        if a["gender_ratio"] != b["gender_ratio_byte"]:
            diffs.append((sym, "gender_ratio", a["gender_ratio"], b["gender_ratio_byte"]))
        eg_a = sorted({EGG_GROUP_ALIAS.get(key(g), key(g)) for g in a["egg_groups"]})
        eg_b = sorted({key(g) for g in b["egg_groups"]})
        if eg_a != eg_b:
            diffs.append((sym, "egg_groups", a["egg_groups"], b["egg_groups"]))
        hi_a = sorted((key(i), round(p * 100)) for i, p in a["held_items_rse"])
        hi_b = sorted((key(strip(h["item"], "ITEM_")), h["chance_pct"]) for h in b["wild_held_items"])
        if hi_a != hi_b:
            diffs.append((sym, "wild_held_items", a["held_items_rse"], b["wild_held_items"]))
        ls = learn.get(sym)
        if ls is None:
            diffs.append((sym, "learnset", "present", None))
            continue
        # level-up: the sandbox dict {move id: level}; KB1 a list of {level, move}
        lv_b: dict[str, set] = {}
        for e in ls["level_up"]:
            lv_b.setdefault(e["move"], set()).add(e["level"])
        lv_a = {move_sym.get(int(m), f"?{m}"): lvl for m, lvl in a["learnset"]["level_up"].items()}
        if set(lv_a) != set(lv_b):
            diffs.append((sym, "level_up moves", sorted(set(lv_a) - set(lv_b)), sorted(set(lv_b) - set(lv_a))))
        for mv in sorted(set(lv_a) & set(lv_b)):
            if lv_a[mv] not in lv_b[mv]:
                diffs.append((sym, f"level_up {mv}", lv_a[mv], sorted(lv_b[mv])))
        for field, sb_list, sea_list in (
                ("tm_hm", a["learnset"]["tm_hm"], [e["move"] for e in ls["tm_hm"]]),
                ("tutor", a["learnset"]["tutor"], ls["tutor"]),
                ("egg", a["learnset"]["egg"], ls["egg"])):
            sa = {move_sym.get(int(m), f"?{m}") for m in sb_list}
            sb_ = set(sea_list)
            if sa != sb_:
                diffs.append((sym, field, sorted(sa - sb_), sorted(sb_ - sa)))
    check("X3 species national-dex sets agree", set(sb) == set(sea),
          f"only sandbox: {sorted(set(sb) - set(sea))[:8]} only seasoned: {sorted(set(sea) - set(sb))[:8]}")
    guard("X3", len(common), len(sb), len(sea))
    for f, n in exercised.items():
        check(f"X3 field '{f}' exercised: non-empty on both sides for {n} species (>= {FIELD_MIN[f]})",
              n >= FIELD_MIN[f], str(n))
    return diffs


# The minimum number of species whose field is non-empty on BOTH sides (measured 2026-10-21 on the KB1 tip, rounded
# down; a sharp fall means one side lost the field and the comparison went vacuous).
#   measured: wild_held_items 117, level_up 386, tm_hm 372, tutor 372, egg 165, abilities 386.
FIELD_MIN = {"wild_held_items": 110, "level_up": 380, "tm_hm": 360, "tutor": 360, "egg": 155, "abilities": 380}


def x3_multilevel_count(d: dict) -> int:
    n = 0
    for s in d["learnsets"]["species"]:
        seen: dict[str, int] = {}
        for e in s["level_up"]:
            seen[e["move"]] = seen.get(e["move"], 0) + 1
        n += sum(1 for c in seen.values() if c > 1)
    return n


def x4(d: dict, report: list | None = None) -> list[tuple]:
    enc = d["encounters"]
    nat_of = {s["symbol"]: s["national_dex"] for s in d["species"]["species"]}
    if "where_to_find_normal_play" not in enc:
        check("X4 KB1 has where_to_find_normal_play (an extraction from before 2026-10-21 does not)", False)
        return []
    wtf = enc["where_to_find_normal_play"]
    sea_species = {nat_of[s]: s for s in wtf}
    rar = {int(k): v for k, v in d["rarity"]["species"].items()}

    # 1. the species-level gap, species by species, against GAP_SPECIES
    only_r = set(rar) - set(sea_species)
    only_s = set(sea_species) - set(rar)
    gap = {n: "rarity" for n in only_r} | {n: "seasoned" for n in only_s}
    missing = sorted(n for n in gap if n not in GAP_SPECIES or GAP_SPECIES[n][0] != gap[n])
    stale = sorted(n for n in GAP_SPECIES if n not in gap)
    check(f"X4 the species gap ({len(rar)} rarity vs {len(wtf)} seasoned: {len(only_r)} only in rarity, "
          f"{len(only_s)} only in seasoned) is explained species by species",
          not missing, f"UNEXPLAINED: {[(n, gap[n]) for n in missing]}")
    check("X4 no stale GAP_SPECIES entry (every stated reason explains a species that IS in the gap)",
          not stale, f"stale: {stale}")
    # The reasons' own claims, checked where the data can check them:
    check("X4 reason check: every rarity-only species has maps=[] and a legendary/special reason",
          all(not rar[n]["maps"] and set(rar[n]["reasons"]) & {"legendary", "special"} for n in only_r),
          str([(n, rar[n]["maps"], rar[n]["reasons"]) for n in only_r if rar[n]["maps"]]))
    feb = wtf.get("SPECIES_FEEBAS", [])
    check("X4 reason check (scope rule feebas_rule_rows): KB1's feebas block names SPECIES_FEEBAS, its normal rows are "
          "all special 'feebas_tiles' on MAP_ROUTE119, and the rarity file lists Feebas as 'special' with no map",
          enc.get("feebas", {}).get("species") == "SPECIES_FEEBAS" and bool(feb)
          and all(e.get("special") == "feebas_tiles" and e["map"] == "MAP_ROUTE119" for e in feb)
          and 349 in rar and rar[349]["maps"] == [] and "special" in rar[349]["reasons"],
          f"block={enc.get('feebas', {}).get('species')} rows={[(e.get('special'), e['map']) for e in feb]} "
          f"rarity={rar.get(349, {}).get('maps')},{rar.get(349, {}).get('reasons')}")
    wyn = wtf.get("SPECIES_WYNAUT", [])
    check("X4 reason check: Wynaut's normal rows are all MAP_ROUTE130 land with condition 'mirage_island_shown' "
          "(its gap reason)",
          bool(wyn) and all(e["map"] == "MAP_ROUTE130" and e["method"] == "land"
                            and e.get("condition") == "mirage_island_shown" for e in wyn), str(wyn)[:200])
    # KB1's unreachable labels against the rarity file's independent EXCLUDED list (ROM reader + warp walk).
    kb1_unused = {strip(m["map"], "MAP_") for m in enc["maps"] if m.get("availability") == "unreachable_unused_map"}
    r_excl = set(d["rarity"]["_meta"].get("excluded", {}))
    check("X4 reason check: the rarity file's EXCLUDED list = KB1's unreachable_unused_map maps + "
          "RARITY_EXCLUDED_KB1_NORMAL (each with a stated reason)",
          bool(kb1_unused) and r_excl == kb1_unused | set(RARITY_EXCLUDED_KB1_NORMAL)
          and not kb1_unused & set(RARITY_EXCLUDED_KB1_NORMAL),
          f"rarity excluded={sorted(r_excl)} kb1 unreachable={sorted(kb1_unused)}")
    leaked = sorted({e["base_label"] for rows in wtf.values() for e in rows if e.get("availability") != "normal"})
    check("X4 KB1's normal-play index holds only rows labelled normal", not leaked, str(leaked[:6]))
    if report is not None:
        for n in sorted(gap):
            name = rar[n]["name"] if n in rar else sea_species[n]
            report.append(f"  {n:>3} {name:<22} only in {gap[n]:<8} {GAP_SPECIES.get(n, ('', 'UNEXPLAINED'))[1][:110]}")

    # 2. per species, after projecting the seasoned rows onto the rarity file's scope
    removed = {r: 0 for r in X4_SCOPE}
    common = sorted(set(rar) & set(sea_species))
    diffs = []
    for n in common:
        rows = []
        for e in wtf[sea_species[n]]:
            hit = next((r for r, (_, pred) in X4_SCOPE.items() if pred(e)), None)
            if hit:
                removed[hit] += 1
            else:
                rows.append(e)
        sym = sea_species[n]
        # a frontier row has map null; if one leaks in, its base_label stands in so it shows up as a map difference
        maps_s = sorted({strip(e["map"] or e["base_label"], "MAP_") for e in rows})
        maps_r = sorted(rar[n]["maps"])
        if maps_s != maps_r:
            diffs.append((sym, "maps", sorted(set(maps_r) - set(maps_s)), sorted(set(maps_s) - set(maps_r))))
        best_s = max((e["chance_pct"] for e in rows), default=None)
        if best_s != rar[n]["best_rate"]:
            diffs.append((sym, "best_rate", rar[n]["best_rate"], best_s))
    for r, c in removed.items():
        check(f"X4 scope rule '{r}' removed {c} row(s) (a rule that removes nothing is stale)", c > 0)
    guard("X4", len(common), len(rar), len(wtf))
    return diffs


# ================================================================================================ fault arms
def run_all(d: dict, label_prefix: str = "") -> tuple[int, list]:
    """Run X1-X4 on `d`; return (number of failed checks it added, unexplained differences)."""
    start = len(RESULTS)
    un = []
    un += explain(x1(d), "X1")
    un += explain(x2(d), "X2")
    un += explain(x3(d), "X3")
    un += explain(x4(d), "X4")
    added = RESULTS[start:]
    del RESULTS[start:]
    return sum(1 for r in added if not r[1]), un, added


def fault_arms(d: dict) -> None:
    # CONTROL is the real run in main(); each FAULT below must turn red, naming the planted row.
    if "where_to_find_normal_play" not in d["encounters"]:
        check("FAULT arms skipped: KB1 has no where_to_find_normal_play (X4 already failed on it)", False)
        return
    # F1 X1: a planted move power
    f = copy.deepcopy(d)
    mv = next(m for m in f["moves"]["moves"] if m["symbol"] == "MOVE_TACKLE")
    mv["power"] += 1
    _, un, _ = run_all(f)
    check("FAULT F1 (X1 has teeth): planted MOVE_TACKLE power+1 is reported",
          any(u[0] == "MOVE_TACKLE" and u[1] == "power" for u in un), str(un[:3]))
    # F2 X2: a planted base stat
    f = copy.deepcopy(d)
    sp = next(s for s in f["species"]["species"] if s["symbol"] == "SPECIES_TREECKO")
    sp["base_stats"]["speed"] += 1
    _, un, _ = run_all(f)
    check("FAULT F2 (X2 has teeth): planted SPECIES_TREECKO speed+1 is reported by X2 and X3",
          sum(1 for u in un if u[0] == "SPECIES_TREECKO" and u[1] == "base speed") == 2, str(un[:4]))
    # F3 X3: a planted wrong type (acceptance test M4, in memory)
    f = copy.deepcopy(d)
    sp = next(s for s in f["species"]["species"] if s["symbol"] == "SPECIES_SABLEYE")
    sp["types"] = ["DARK", "STEEL"]
    _, un, _ = run_all(f)
    check("FAULT F3 (X3 has teeth, M4): planted SPECIES_SABLEYE types DARK/STEEL is reported",
          any(u[0] == "SPECIES_SABLEYE" and u[1] == "types" for u in un), str(un[:3]))
    # F3b X3 learnset: a planted level change
    f = copy.deepcopy(d)
    ls = next(s for s in f["learnsets"]["species"] if s["symbol"] == "SPECIES_BULBASAUR")
    ls["level_up"][4]["level"] += 1
    _, un, _ = run_all(f)
    check("FAULT F3b (X3 learnsets have teeth): planted BULBASAUR level_up[4] level+1 is reported",
          any(u[0] == "SPECIES_BULBASAUR" and u[1].startswith("level_up") for u in un), str(un[:3]))
    # F4 X4: a dropped map
    f = copy.deepcopy(d)
    f["encounters"]["where_to_find_normal_play"]["SPECIES_ABRA"] = [
        e for e in f["encounters"]["where_to_find_normal_play"]["SPECIES_ABRA"] if e["map"] != "MAP_ROUTE116"]
    _, un, _ = run_all(f)
    check("FAULT F4 (X4 has teeth): dropped SPECIES_ABRA's MAP_ROUTE116 row is reported",
          any(u[0] == "SPECIES_ABRA" and u[1] == "maps" for u in un), str(un[:3]))
    # F5 the non-vacuity guard: a join that matches (almost) nothing
    f = copy.deepcopy(d)
    for s in f["species"]["species"]:
        if s["national_dex"]:
            s["national_dex"] += 1000
    _, _, added = run_all(f)
    check("FAULT F5 (non-vacuity guard): a broken national-dex join fails X2 and X3's guards",
          sum(1 for name, ok, _ in added if "non-vacuity" in name and name[:2] in ("X2", "X3") and not ok) == 2,
          str([n for n, ok, _ in added if "non-vacuity" in n]))
    # F4b X4: a changed rate
    f = copy.deepcopy(d)
    for e in f["encounters"]["where_to_find_normal_play"]["SPECIES_ABSOL"]:
        e["chance_pct"] += 1
    _, un, _ = run_all(f)
    check("FAULT F4b (X4 rates have teeth): SPECIES_ABSOL chance_pct+1 is reported as best_rate",
          any(u[0] == "SPECIES_ABSOL" and u[1] == "best_rate" for u in un), str(un[:3]))
    # F6 a stale reason: GAP_SPECIES explains a species that is not in the gap
    GAP_SPECIES[25] = ("rarity", "planted stale reason")
    try:
        _, _, added = run_all(d)
    finally:
        del GAP_SPECIES[25]
    check("FAULT F6 (stale reasons are caught): a GAP_SPECIES row for Pikachu (in both files) fails the stale check",
          any("stale" in name and not ok for name, ok, _ in added))
    # F7 an unexplained species: remove a reason row
    saved = GAP_SPECIES.pop(360)
    try:
        _, _, added = run_all(d)
    finally:
        GAP_SPECIES[360] = saved
    check("FAULT F7 (an unexplained species is caught): without Wynaut's reason the gap check fails naming 360",
          any("species by species" in name and not ok and "360" in detail for name, ok, detail in added))

    # F8-F11: each fixed KB1 semantic error, leaked back as a MISLABEL (availability 'normal' and in the normal-play
    # index), must be caught by the rarity side, not merely by KB1's own label check.
    def leak(f, sp, label):
        enc = f["encounters"]
        row = next(e for e in enc["where_to_find"][sp] if e["base_label"] == label)
        row["availability"] = "normal"
        enc["where_to_find_normal_play"].setdefault(sp, []).append(row)

    f = copy.deepcopy(d)
    leak(f, "SPECIES_BULBASAUR", "gBattlePyramid_1")
    _, _, added = run_all(f)
    check("FAULT F8 (F-1 leak): a Pyramid header Bulbasaur labelled normal is an unexplained gap species (1)",
          any("species by species" in name and not ok and "(1, 'seasoned')" in detail for name, ok, detail in added))
    f = copy.deepcopy(d)
    leak(f, "SPECIES_AIPOM", "gAlteringCave6")
    _, un, _ = run_all(f)
    check("FAULT F9 (F-4 leak): Altering Cave set 6 labelled normal gives Aipom an unexplained ALTERING_CAVE map",
          any(u[0] == "SPECIES_AIPOM" and u[1] == "maps" and "ALTERING_CAVE" in u[3] for u in un), str(un[:3]))
    f = copy.deepcopy(d)
    next(m for m in f["encounters"]["maps"]
         if m["base_label"] == "gCaveOfOrigin_UnusedRubySapphireMap1")["availability"] = "normal"
    leak(f, "SPECIES_ZUBAT", "gCaveOfOrigin_UnusedRubySapphireMap1")
    _, un, added = run_all(f)
    check("FAULT F10 (F-6 leak): unused Cave of Origin map 1 labelled normal fails the EXCLUDED tie and gives Zubat "
          "an unexplained map",
          any("EXCLUDED list" in name and not ok for name, ok, _ in added)
          and any(u[0] == "SPECIES_ZUBAT" and u[1] == "maps" for u in un), str(un[:3]))
    f = copy.deepcopy(d)
    leak(f, "SPECIES_BRELOOM", "gBattlePike_3")
    _, _, added = run_all(f)
    check("FAULT F11 (F-2 leak): a Pike-only Breloom labelled normal is an unexplained gap species (286)",
          any("species by species" in name and not ok and "(286, 'seasoned')" in detail for name, ok, detail in added))
    # F12: a row still labelled non-normal but sitting in the normal-play index (an index-building bug, not a label one)
    f = copy.deepcopy(d)
    enc = f["encounters"]
    enc["where_to_find_normal_play"]["SPECIES_SEVIPER"].append(
        next(e for e in enc["where_to_find"]["SPECIES_SEVIPER"] if e["base_label"] == "gBattlePike_1"))
    _, _, added = run_all(f)
    check("FAULT F12 (index leak): a Pike row still labelled runtime-level inside the normal-play index is reported",
          any("holds only rows labelled normal" in name and not ok and "gBattlePike_1" in detail
              for name, ok, detail in added))
    # F13: Wynaut's gap reason claims ROUTE130 land; a Wynaut row elsewhere makes that reason false
    f = copy.deepcopy(d)
    f["encounters"]["where_to_find_normal_play"]["SPECIES_WYNAUT"][0]["map"] = "MAP_ROUTE119"
    _, _, added = run_all(f)
    check("FAULT F13 (a reason's own claim is checked): a Wynaut row off ROUTE130 land fails Wynaut's reason check",
          any("Wynaut's normal rows" in name and not ok for name, ok, _ in added))
    # F14: an extraction from before 2026-10-21 (no normal-play index) must fail X4, not crash or pass
    f = copy.deepcopy(d)
    del f["encounters"]["where_to_find_normal_play"]
    _, _, added = run_all(f)
    check("FAULT F14 (old-format KB1): no where_to_find_normal_play fails X4",
          any("has where_to_find_normal_play" in name and not ok for name, ok, _ in added))
    # F15: a Feebas row that has lost its `special` marker looks like a table row; the scope rule no longer applies
    # to it, so Feebas gets an unexplained ROUTE119 map
    f = copy.deepcopy(d)
    for e in f["encounters"]["where_to_find_normal_play"]["SPECIES_FEEBAS"]:
        e["special"] = None
    _, un, _ = run_all(f)
    check("FAULT F15 (scope rule has teeth): Feebas rows without special 'feebas_tiles' give Feebas an unexplained map",
          any(u[0] == "SPECIES_FEEBAS" and u[1] == "maps" for u in un), str(un[:3]))
    # F16: the Feebas rows gone (the pre-fix KB1): the scope rule removes nothing and goes stale, and Feebas is an
    # unexplained rarity-only species
    f = copy.deepcopy(d)
    del f["encounters"]["where_to_find_normal_play"]["SPECIES_FEEBAS"]
    _, _, added = run_all(f)
    check("FAULT F16 (the pre-fix KB1 without Feebas rows): the feebas_rule_rows scope rule goes stale and 349 is "
          "an unexplained gap species",
          any("feebas_rule_rows" in name and not ok for name, ok, _ in added)
          and any("species by species" in name and not ok and "(349, 'rarity')" in detail
                  for name, ok, detail in added))
    # F17: Wynaut's gap reason now also claims KB1's Mirage Island condition; a row without it makes the reason false
    f = copy.deepcopy(d)
    f["encounters"]["where_to_find_normal_play"]["SPECIES_WYNAUT"][0]["condition"] = None
    _, _, added = run_all(f)
    check("FAULT F17 (Wynaut's condition is checked): a Wynaut row without 'mirage_island_shown' fails its reason check",
          any("Wynaut's normal rows" in name and not ok for name, ok, _ in added))
    # F18: the scope rule projects Feebas rows away, so only the reason check sees a Feebas row off Route 119
    f = copy.deepcopy(d)
    f["encounters"]["where_to_find_normal_play"]["SPECIES_FEEBAS"][0]["map"] = "MAP_ROUTE120"
    _, _, added = run_all(f)
    check("FAULT F18 (the scope rule's own claim is checked): a special Feebas row off MAP_ROUTE119 fails the "
          "feebas_rule_rows reason check",
          any("scope rule feebas_rule_rows" in name and not ok for name, ok, _ in added))


# ================================================================================================ merge state
def absent_verdict(state: str) -> int:
    """The exit code when the DEFAULT folder is absent: 0 (SKIPPED) only when KB1 is provably not merged."""
    return 0 if state == "not_merged" else 1


def skip_arms() -> None:
    """FAULT/CONTROL for the skip rule (runs whenever the data is present, i.e. after the merge)."""
    check("SKIP CONTROL: absent + not merged -> exit 0 (SKIPPED)", absent_verdict("not_merged") == 0)
    check("SKIP FAULT: absent + merged -> exit 1", absent_verdict("merged") == 1)
    check("SKIP FAULT: absent + undecidable (shallow clone) -> exit 1", absent_verdict("unknown") == 1)
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    check("SKIP CONTROL: the detector reports HEAD itself as 'merged' (it can say yes)",
          bool(head) and merge_state(head) == "merged", head)


def merge_state(tip: str | None = None) -> str:
    """'merged', 'not_merged' or 'unknown' for `tip` (default: KB1_TIP, read at CALL time) relative to HEAD."""
    tip = tip or KB1_TIP
    p = subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", tip, "HEAD"],
                       capture_output=True, text=True)
    if p.returncode == 0:
        return "merged"
    if p.returncode == 1:
        return "not_merged"
    # 128: the object is unknown. In a full clone that means it is not in HEAD's history; in a shallow one, undecidable.
    s = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--is-shallow-repository"], capture_output=True, text=True)
    return "not_merged" if s.returncode == 0 and s.stdout.strip() == "false" else "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasoned-dir", default=None)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    explicit = args.seasoned_dir is not None
    sdir = Path(args.seasoned_dir) if explicit else SEASONED_DEFAULT

    absent = [n for n in SEASONED_FILES if not (sdir / n).is_file()]
    if absent:
        if not explicit and len(absent) == len(SEASONED_FILES) and not sdir.exists():
            state = merge_state()
            if absent_verdict(state) == 0:
                print(f"SKIPPED: seasoned/ not merged yet (KB1 tip {KB1_TIP[:8]} is not an ancestor of HEAD; "
                      f"nothing compared)")
                return 0
            print(f"FAIL {sdir} is missing and the KB1 merge state is '{state}': after the merge this folder must exist")
            return 1
        print(f"FAIL seasoned files missing in {sdir}: {absent}")
        return 1

    d = load_all(sdir)
    print(f"seasoned dir: {sdir}")
    report: list[str] = []
    u1 = explain(x1(d), "X1")
    u2 = explain(x2(d), "X2")
    u3 = explain(x3(d), "X3")
    check(f"X3 note: {x3_multilevel_count(d)} (species, move) pairs are learned at several levels in KB1 "
          f"({R_LVL_DICT[:10]} applies to them)", True)
    u4 = explain(x4(d, report), "X4")
    fault_arms(d)
    skip_arms()

    print("X4 species gap, species by species (national, name, side, reason):")
    print("\n".join(report))
    bad = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" | {detail[:600]}"))
    unexplained = u1 + u2 + u3 + u4
    if unexplained:
        print(f"UNEXPLAINED DIFFERENCES ({len(unexplained)}), each a finding to adjudicate against the decomp:")
        for u in unexplained if args.verbose else unexplained[:40]:
            print(f"  {u[0]} {u[1]}: other={u[2]!r} seasoned={u[3]!r}")
    print(f"{'ALL PASS' if not bad else 'FAILED'} ({len(RESULTS)} checks)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
