"""The AUTHORITATIVE generator of `sandbox-pokebot/modules/data/emerald_rarity.json` (design v2 step 7, RP), plus the
reproduction of the 2026-08-06 record it grew out of (`#24-rarepredicate`).

WHAT "RARE" MEANS (`ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md` §2 step 7):

    RARE  =  legendary  OR  special  OR  rate  OR  pseudo  OR  variant        (shiny keeps its own branch)

  * rate      the species' BEST live per-table rate is <= 4% (the 2026-08-06 spec's rate half; the user deferred
              "rare" to the notes, 06:8081). ‼ The rate is the SUM of the species' slots in ONE map+method table
              (Skitty's two 1% land slots on Route 116 = 2%), exactly what `encounter_index._build_index` stores. A
              strict single-slot reading would give 34 species, not 14.
  * pseudo    exactly 1 region-map location (MAPSEC) AND at least 2 gates on its EASIEST home (min over its rows).
              A gate is an HM field move or a fishing rod needed to reach the encounter FROM THE STORY PATH: the
              proposal put to the user as Q6, stated in `PSEUDO_RULE`. Gates come from the encounter method (Surf, an
              underwater map, a rod, Rock Smash) plus `MAP_ACCESS_GATES`, a tile-MEASURED table.
  * variant   per INDIVIDUAL, the ULTRA tier: ratio 31/63/191, the minority gender, and best_rate x P(minority)
              <= 4% (an interpretation stated to the user in Q5). This file records the species' variant gender;
              `modules/rarity.py` checks the individual.
  * special   Feebas only (the one special case the record names, 06:8084-8088). No derivable rule can see it.
  * legendary the literal list below.

WHERE THE DATA COMES FROM: OUR ROM, read STATICALLY (no emulator). The ROM is tracked in git; the encounter cache is
not (`sandbox-pokebot/.gitignore` ignores `cache/`).
  * The wild tables: `gWildMonHeaders`, the FIRST header per map. ‼ The runtime reader (`modules/map.py`
    `get_wild_encounters_for_map`) keys headers by (group, number), so for Altering Cave, which has NINE headers (one
    per `VAR_ALTERING_CAVE_WILD_SET` value), the LAST wins and the cache holds the DEAD set 8 (Smeargle 100%), not
    the live set 0 (Zubat). The game takes the first matching header and adds the var (decomp `wild_encounter.c`
    `GetCurrentMapWildMonHeaderId`). Only a Mystery Gift event script changes the var
    (`data/scripts/gift_altering_cave.inc`), so in ordinary play the first header is the live one. This generator
    reads the first, and asserts that the cache differs from it in exactly that one map.
  * MAPSEC: map header byte 0x14 (`regionMapSectionId`), the byte `MapLocation.map_name` reads. ‼ KEY BY THE ID,
    NEVER BY THE NAME: UNDERWATER_124 and UNDERWATER_126 are two sections that share the name "UNDERWATER", so
    counting names would make Chinchou, Clamperl and Relicanth single-location.

EXCLUDED ROWS (tables that exist in the ROM but that a player cannot meet): the unused Cave of Origin maps 1-3; Route
130's land table (Mirage Island only; it holds Wynaut and nothing else); Altering Cave sets 1-8 (by construction).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 rare_species_dataset.py            # summary + hard checks
      PYTHONUTF8=1 py -3.12 rare_species_dataset.py --write    # regenerate the committed JSON
      PYTHONUTF8=1 py -3.12 rare_species_dataset.py --check    # regenerate in memory and DIFF (exit 1 on drift)
The warp-depth column, the cache agreement and the 2026-08-06 reproduction need the gitignored `cache/` files. Without
them each prints a visible SKIP (never a PASS), and `--check` compares everything except the warp-depth column.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys
from fractions import Fraction

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"
CACHE = SANDBOX / "cache"
OUT = SANDBOX / "modules" / "data" / "emerald_rarity.json"
if str(SANDBOX) not in sys.path:
    sys.path.insert(0, str(SANDBOX))

# ------------------------------------------------------------------------------------------------ the rule's constants
RATE_MAX_PCT = 4        # archive:6149 "Rare species = `best_slot_rate <= 4%`"; the cliff is between 4% and 5%
VARIANT_MAX_PCT = 4     # Q5 (a stated interpretation): the same cut as the rate
VARIANT_RATIOS = (31, 63, 191)
LEGENDARY = (144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 251,
             377, 378, 379, 380, 381, 382, 383, 384, 385, 386)
SPECIAL = {349: "Feebas: six random Route 119 fishing tiles, in no wild table (the user's words in 03 `#24-rarepredicate`; 06:8084-8088)"}

PSEUDO_RULE = ("exactly 1 MAPSEC AND >= 2 gates on the easiest home. A gate is an HM field move or a fishing rod "
               "needed to reach the encounter FROM THE STORY PATH (the Q6 proposal: a map the story walks through "
               "adds no gate, so Victory Road's species do not qualify; bikes are not gates)")

# Slot rates per table, as `modules/map.py` reads them (and the decomp's `wild_encounters.json`).
LAND_RATES = (20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1)
WATER_RATES = (60, 30, 5, 4, 1)
FISH_RATES = ((0, 2, "Old Rod", (70, 30)), (2, 5, "Good Rod", (60, 20, 20)), (5, 10, "Super Rod", (40, 40, 15, 4, 1)))

METHOD_GATES = {"Grass": (), "Surfing": ("surf",), "Rock Smash": ("rock_smash",),
                "Old Rod": ("rod",), "Good Rod": ("rod",), "Super Rod": ("rod",)}

# (group, number) of maps whose tables are EXCLUDED, with the method (None = every table on that map).
EXCLUDED = {
    (24, 39): (None, "CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP1: unused, no warp reaches it"),
    (24, 40): (None, "CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP2: unused, no warp reaches it"),
    (24, 41): (None, "CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP3: unused, no warp reaches it"),
    (0, 45): ("Grass", "ROUTE130 land: Mirage Island only (Wynaut), which appears on a PV-matched random day"),
}

# ‼ MEASURED gates only. Each entry is the set of gates needed to reach that MAP's encounter area from the story path.
# A map not listed here contributes no gates beyond its encounter method.
MAP_ACCESS_GATES: dict[tuple[int, int], tuple[str, ...]] = {
    # Meteor Falls, from the story arrival in 1F_1R (27,18): ONLY the 2026-09-11 measurement
    # (`modules/story/training_areas.py`, the comment above its Meteor Falls rows; a controlled decoder), which agrees
    # with the user's own words for Bagon (03 `#24-rarepredicate`). The step 7 verifier's flood is NOT a citation:
    # its pre-registered control failed (R3), so nothing it prints is believed.
    (24, 1): ("surf", "waterfall"),   # METEOR_FALLS_1F_2R
    (24, 2): ("surf", "waterfall"),   # METEOR_FALLS_B1F_1R
    (24, 3): ("surf", "waterfall"),   # METEOR_FALLS_B1F_2R (Bagon's only room)
    # Shoal Cave, from Mossdeep: Surf to reach Route 125's island, and inside the cave the Lower Room boulder seals
    # the Ice Room until it is pushed east three times (`probe_rarity_shoal_path.py`, production `calculate_path`;
    # the pseudo verdict rests on its NO-PATH readings, which are conservative because `calculate_path` is more
    # permissive than the controlled decoder). The high-tide maps own no wild table.
    (24, 46): ("surf",),              # SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM
    (24, 47): ("surf",),              # SHOAL_CAVE_LOW_TIDE_INNER_ROOM
    (24, 48): ("surf",),              # SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM
    (24, 49): ("surf",),              # SHOAL_CAVE_LOW_TIDE_LOWER_ROOM
    (24, 83): ("strength", "surf"),   # SHOAL_CAVE_LOW_TIDE_ICE_ROOM (Snorunt's only room)
}
MAP_ACCESS_SOURCE = ("Meteor Falls: sandbox-pokebot/modules/story/training_areas.py (measured 2026-09-11); "
                     "Shoal Cave: tools/story-dev/probe_rarity_shoal_path.py "
                     "(evidence/2026-09-29-rarepredicate-SHOALPATH.txt, production calculate_path). NOT a citation: "
                     "tools/story-dev/probe_rarity_access_gates.py, whose pre-registered 262/299 control failed "
                     "(296/333), so nothing it prints is believed")

# Off-story-path areas whose tiles have NOT been measured. A single-MAPSEC species found only there is decided on its
# method gates alone, and its row says so (`gates_unmeasured`), so a step-8 log can name the gap.
UNMEASURED = {
    "NEW_MAUVILLE": "Surf to reach; the Basement Key is an item, not a gate",
    "ABANDONED_SHIP": "Surf to reach; Dive for the hidden floor",
    "ARTISAN_CAVE": "Battle Frontier (post-game); Surf across the Frontier's water",
    "DESERT_UNDERPASS": "post-game tunnel off Route 114",
    "SAFARI_ZONE": "HM needs not measured; its Mach/Acro Bike areas are not gates under the Q6 proposal",
}


# ------------------------------------------------------------------------------------------------ pure rule functions
def minority_gender(ratio: int) -> str | None:
    """The minority gender of a ratio that has one (Gen 3: female iff (pv & 0xFF) < ratio)."""
    if ratio in (31, 63):
        return "female"
    if ratio == 191:
        return "male"
    return None


def p_minority(ratio: int) -> Fraction:
    """P(minority) for a uniform PV low byte: female = ratio/256, male = (256 - ratio)/256."""
    return Fraction(ratio, 256) if minority_gender(ratio) == "female" else Fraction(256 - ratio, 256)


def row_gates(map_key: tuple[int, int], method: str, underwater: set) -> frozenset:
    gates = set(METHOD_GATES[method])
    if map_key in underwater:           # the underwater table is read as "Surfing"; the MAP decides Dive
        gates |= {"surf", "dive"}
    gates |= set(MAP_ACCESS_GATES.get(map_key, ()))
    return frozenset(gates)


def easiest_gates(rows: list[dict], underwater: set) -> frozenset:
    """MIN over a species' rows: a species is only as gated as its easiest home. (Solrock also lives in Bagon's room,
    but it lives in 1F_1R too, with no gate, so it is not pseudo.) Ties break on the sorted names, for stable output."""
    options = [row_gates(tuple(r["map"]), r["method"], underwater) for r in rows]
    return min(options, key=lambda g: (len(g), sorted(g)))


def n_mapsecs(rows: list[dict], mapsec_of: dict) -> int:
    """Distinct region-map sections, by ID (never by name: see the module docstring)."""
    return len({mapsec_of[tuple(r["map"])] for r in rows})


def is_pseudo(gates: frozenset, mapsecs: int) -> bool:
    return len(gates) >= 2 and mapsecs == 1


# ------------------------------------------------------------------------------------------------ static ROM reads
def load_rom():
    """Load our tracked Emerald ROM's bytes and symbols. No emulator."""
    from modules.game import get_symbol, set_rom
    from modules.roms import ROMS_DIRECTORY, load_rom_data

    for file in sorted(ROMS_DIRECTORY.iterdir()):
        if file.suffix.lower() != ".gba":
            continue
        rom = load_rom_data(file)
        if rom.id == "BPEE0":
            set_rom(rom)
            return rom.id, file.read_bytes(), get_symbol
    raise FileNotFoundError(f"no BPEE0 ROM in {ROMS_DIRECTORY}")


def read_rom_tables(data: bytes, get_symbol):
    """(`mapsec_of`, `index`, `duplicates`): each wild map's MAPSEC byte, the wild index {internal species: [rows]}
    from the FIRST header per map, and the maps that have more than one header."""

    def u32(address: int) -> int:
        return struct.unpack_from("<I", data, address - 0x08000000)[0]

    def u8(address: int) -> int:
        return data[address - 0x08000000]

    groups_addr, _ = get_symbol("gMapGroups")
    headers_addr, headers_size = get_symbol("gWildMonHeaders")

    seen: set[tuple[int, int]] = set()
    duplicates: dict[tuple[int, int], int] = {}
    index: dict[int, list] = {}
    for i in range(headers_size // 20):
        base = headers_addr + 20 * i
        key = (u8(base), u8(base + 1))
        if key[0] == 0xFF:
            break
        if key in seen:
            duplicates[key] = duplicates.get(key, 1) + 1
            continue  # ‼ the game's GetCurrentMapWildMonHeaderId takes the FIRST header (+ the Altering Cave var: 0 without a Mystery Gift)
        seen.add(key)
        tables = []
        for offset, count, rates, method in ((4, 12, LAND_RATES, "Grass"), (8, 5, WATER_RATES, "Surfing"),
                                             (12, 5, WATER_RATES, "Rock Smash")):
            info = u32(base + offset)
            if info and u8(info) > 0:
                tables.append((method, u32(info + 4), 0, count, rates))
        info = u32(base + 16)
        # Fishing: the game checks only the POINTER (decomp `wild_encounter.c` `DoesCurrentMapHaveFishingMons`), never
        # the rate byte, so neither does this. (The runtime reader, `modules/map.py`, also requires rate > 0; no
        # fishing table in our ROM has rate 0, so the two readers still agree. Found by the step 7 review.)
        if info:
            for start, end, method, rates in FISH_RATES:
                tables.append((method, u32(info + 4), start, end - start, rates))
        for method, slots, first, count, rates in tables:
            agg: dict[int, int] = {}
            for n in range(count):
                species = struct.unpack_from("<H", data, slots - 0x08000000 + 4 * (first + n) + 2)[0]
                agg[species] = agg.get(species, 0) + rates[n]
            for species, rate in agg.items():
                index.setdefault(species, []).append({"map": [key[0], key[1]], "method": method, "rate": rate})
    mapsec_of = {key: u8(u32(u32(groups_addr + 4 * key[0]) + 4 * key[1]) + 0x14) for key in seen}
    return mapsec_of, index, duplicates


def apply_exclusions(index: dict) -> dict:
    out: dict[int, list] = {}
    for species, rows in index.items():
        kept = []
        for r in rows:
            rule = EXCLUDED.get(tuple(r["map"]))
            if rule is not None and (rule[0] is None or rule[0] == r["method"]):
                continue
            kept.append(r)
        if kept:
            out[species] = kept
    return out


def underwater_maps(group0_only: bool = False) -> set:
    from modules.map_data import MapRSE

    return {m.value for m in MapRSE
            if m.name.startswith("UNDERWATER_") and (m.value[0] == 0 or not group0_only)}


# ------------------------------------------------------------------------------------------------ warp depth (diagnostic)
def warp_depths() -> dict | None:
    """The 2026-08-06 warp depth per MAP (0-1 BFS; connections cost 0, warps 1). None when the cache is absent."""
    path = CACHE / "warp_graph_BPEE0.json"
    if not path.exists():
        return None
    wg = json.loads(path.read_text(encoding="utf-8"))
    adj_free: dict[tuple, set] = {}
    adj_warp: dict[tuple, set] = {}
    for src, dsts in wg["connections"]:
        s = tuple(src)
        for d in dsts:
            adj_free.setdefault(s, set()).add(tuple(d))
            adj_free.setdefault(tuple(d), set()).add(s)
    # ⛔ FIXED 2026-09-29 (v2 step 0): an edge is `[from_map, from_coords, to_map, to_coords]`
    # (`modules/warp_graph.py` `to_json`), so the destination MAP is `edge[2]`; `edge[1]` is a TILE coordinate.
    for edge in wg["edges"]:
        s, d = tuple(edge[0]), tuple(edge[2])
        adj_warp.setdefault(s, set()).add(d)
        adj_warp.setdefault(d, set()).add(s)
    # Seed every NON-UNDERWATER group-0 map (v2 step 0 fix: the underwater maps ARE group 0).
    underwater_g0 = underwater_maps(group0_only=True)
    seeds = {tuple(m) for m, _region in wg["regions"] if m[0] == 0 and tuple(m) not in underwater_g0}
    depth: dict[tuple, int] = {}

    def relax(frontier: set, d: int) -> set:
        out, stack = set(), list(frontier)
        while stack:
            m = stack.pop()
            if depth.get(m, 99) <= d:
                out.add(m)
                continue
            depth[m] = d
            out.add(m)
            stack.extend(n for n in adj_free.get(m, ()) if depth.get(n, 99) > d)
        return out

    level, d = relax(seeds, 0), 0
    while level and d < 20:
        nxt = {n for m in level for n in adj_warp.get(m, ()) if depth.get(n, 99) > d + 1}
        if not nxt:
            break
        d += 1
        level = relax(nxt, d)
    return depth


# ------------------------------------------------------------------------------------------------ the dataset
def build(rom_id: str, index: dict, mapsec_of: dict, depth: dict | None) -> dict:
    from modules.map_data import MapRSE
    from modules.pokemon import get_species_by_index, get_species_by_national_dex

    underwater = underwater_maps()
    names = {m.value: m.name for m in MapRSE}
    species_out: dict[str, dict] = {}

    def base(internal: int) -> tuple[int, dict]:
        sp = get_species_by_index(internal)
        return sp.national_dex_number, {"name": sp.name, "internal": internal, "national": sp.national_dex_number,
                                        "gender_ratio": sp.gender_ratio}

    for internal, rows in sorted(index.items()):
        if internal == 0:
            raise ValueError("a wild table holds species index 0 (the '??????????' placeholder)")
        national, row = base(internal)
        best = max(r["rate"] for r in rows)
        gates = easiest_gates(rows, underwater)
        secs = n_mapsecs(rows, mapsec_of)
        reasons = []
        if best <= RATE_MAX_PCT:
            reasons.append("rate")
        if is_pseudo(gates, secs):
            reasons.append("pseudo")
        minority = minority_gender(row["gender_ratio"])
        variant_pct = float(best * p_minority(row["gender_ratio"])) if minority else None
        areas = sorted({key for r in rows for key in UNMEASURED if names.get(tuple(r["map"]), "").startswith(key)})
        row.update({
            "best_rate": best,
            "mapsecs": sorted({mapsec_of[tuple(r["map"])] for r in rows}),
            "maps": sorted({names.get(tuple(r["map"]), str(r["map"])) for r in rows}),
            "gates": sorted(gates),
            "variant_gender": minority if minority and variant_pct <= VARIANT_MAX_PCT else None,
            "variant_pct": variant_pct,
            "warp_depth": (min(depth.get(tuple(r["map"]), 99) for r in rows) if depth is not None else None),
            "gates_unmeasured": areas if (secs == 1 and areas and "pseudo" not in reasons) else [],
            "reasons": reasons,
        })
        if str(national) in species_out:
            raise ValueError(f"national {national} twice (internal {internal})")
        species_out[str(national)] = row

    for national in (*LEGENDARY, *SPECIAL):
        sp = get_species_by_national_dex(national)
        if sp.index == 0:
            raise ValueError(f"national {national} resolved to index 0 (the '??????????' placeholder)")
        row = species_out.get(str(national))
        if row is None:
            _, row = base(sp.index)
            row.update({"best_rate": None, "mapsecs": [], "maps": [], "gates": [], "variant_gender": None,
                        "variant_pct": None, "warp_depth": None, "gates_unmeasured": [], "reasons": []})
            species_out[str(national)] = row
        row["reasons"] = (["legendary"] if national in LEGENDARY else ["special"]) + row["reasons"]

    return {
        "_meta": {
            "generator": "tools/story-dev/rare_species_dataset.py --write",
            "rom": rom_id,
            "design": "PROJECT KNOWLEDGE/ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md §2 step 7",
            "keyed_by": "national dex number (as a string); `internal` is the ROM species index",
            "rule": "RARE = legendary OR special OR rate OR pseudo OR variant; shiny is its own branch",
            "rate": f"best per-table summed rate <= {RATE_MAX_PCT}%",
            "variant": (f"ratio in {list(VARIANT_RATIOS)}, the minority gender, best_rate x P(minority) <= "
                        f"{VARIANT_MAX_PCT}% (Q5, a stated interpretation); modules/rarity.py checks the individual"),
            "pseudo": PSEUDO_RULE,
            "map_access_gates": {names.get(k, str(k)): list(v) for k, v in sorted(MAP_ACCESS_GATES.items())},
            "map_access_source": MAP_ACCESS_SOURCE,
            "unmeasured_areas": UNMEASURED,
            "excluded": {names.get(k, str(k)): v[1] for k, v in sorted(EXCLUDED.items())},
            "tier": "ULTRA when the variant (or shiny) reason is present, otherwise RARE",
            "warp_depth": "diagnostic only (the 2026-08-06 axis, replaced by pseudo); null without cache/",
        },
        "species": dict(sorted(species_out.items(), key=lambda kv: int(kv[0]))),
    }


# ------------------------------------------------------------------------------------------------ cross-checks
def compare_with_cache(index: dict, check) -> None:
    """Two readers must agree: this static read vs the runtime cache, except the one known Altering Cave map."""
    path = CACHE / "encounter_index_BPEE0.json"
    if not path.exists():
        print("  SKIP  static-vs-cache agreement — cache/ is absent. THIS IS NOT A PASS.")
        return
    cache = json.loads(path.read_text(encoding="utf-8"))["index"]
    a = {(s, tuple(r["map"]), r["method"], r["rate"]) for s, rs in index.items() for r in rs}
    b = {(int(s), tuple(r["map"]), r["method"], r["rate"]) for s, rs in cache.items() for r in rs}
    off = {x for x in a ^ b if x[1] != (24, 106)}
    check("the static ROM read equals the cache everywhere except ALTERING_CAVE (24,106)", not off,
          f"{len(off)} other differences, e.g. {sorted(off)[:3]}")
    check("there, the cache holds the DEAD set (Smeargle, internal 235) and the ROM's first header Zubat (internal 41)",
          {x[0] for x in b - a} == {235} and {x[0] for x in a - b} == {41},
          f"cache-only {sorted(b - a)} rom-only {sorted(a - b)}")


def reproduce_record(check) -> None:
    """The 2026-08-06 record, over the runtime CACHE it was computed from. Hard checks since v2 step 0."""
    path = CACHE / "encounter_index_BPEE0.json"
    depth = warp_depths()
    if depth is None or not path.exists():
        print("  SKIP  the 2026-08-06 reproduction — cache/ is absent. THIS IS NOT A PASS.")
        return
    check("the underwater group-0 maps are found by name (7 in Emerald)", len(underwater_maps(True)) == 7)
    ei = json.loads(path.read_text(encoding="utf-8"))["index"]
    rows = [(max(l["rate"] for l in locs), min(depth.get(tuple(l["map"]), 99) for l in locs))
            for locs in ei.values() if locs]
    hist: dict[str, int] = {}
    for _, wd in rows:
        k = "d99" if wd >= 99 else (f"d{wd}" if wd < 4 else "d4+")
        hist[k] = hist.get(k, 0) + 1
    check("the record: 132 species carry wild encounters in the cache", len(rows) == 132, str(len(rows)))
    check("the record: the warp-depth histogram", hist == {"d0": 59, "d1": 21, "d2": 39, "d3": 7, "d4+": 3, "d99": 3},
          str(dict(sorted(hist.items()))))
    check("the record: 13 species at depth >= 3", sum(wd >= 3 for _, wd in rows) == 13)
    check("the record: 26 RARE under the archived rule (rate <= 4 OR depth >= 3)",
          sum(r <= 4 or wd >= 3 for r, wd in rows) == 26)


def generate():
    rom_id, data, get_symbol = load_rom()
    mapsec_of, raw, duplicates = read_rom_tables(data, get_symbol)
    index = apply_exclusions(raw)
    return build(rom_id, index, mapsec_of, warp_depths()), raw, index, mapsec_of, duplicates


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the committed JSON")
    ap.add_argument("--check", action="store_true", help="regenerate and diff against the committed JSON")
    args = ap.parse_args(argv)
    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
        if not ok:
            failures.append(label)

    payload, raw, index, mapsec_of, duplicates = generate()
    sp = payload["species"]
    print(f"ROM {payload['_meta']['rom']}: {len(mapsec_of)} maps with a wild header; "
          f"duplicate headers {({str(k): v for k, v in duplicates.items()})}")
    print(f"live wild species after the exclusions: {len(index)}; rows in the table: {len(sp)}")
    for reason in ("legendary", "special", "rate", "pseudo"):
        print(f"  {reason:<9} {[int(k) for k, r in sp.items() if reason in r['reasons']]}")
    print("  variant   " + str([(int(k), r["variant_gender"], r["variant_pct"])
                                for k, r in sp.items() if r["variant_gender"]]))
    print()
    print("CHECKS")
    check("only ALTERING_CAVE has more than one wild header (9)", duplicates == {(24, 106): 9}, str(duplicates))
    check("UNDERWATER_124 and UNDERWATER_126 are DIFFERENT sections by ID", mapsec_of[(0, 50)] != mapsec_of[(0, 51)],
          f"{mapsec_of[(0, 50)]:#x} vs {mapsec_of[(0, 51)]:#x}")
    check("131 live wild species after the exclusions", len(index) == 131, str(len(index)))
    compare_with_cache(raw, check)
    reproduce_record(check)

    text = json.dumps(payload, indent=1, ensure_ascii=False) + "\n"
    if args.write:
        OUT.write_text(text, encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(REPO).as_posix()}")
    if args.check:
        committed = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
        fresh = json.loads(text)
        if warp_depths() is None:
            print("  SKIP  --check of the warp_depth column — cache/ is absent. THIS IS NOT A PASS.")
            for obj in (committed.get("species", {}), fresh["species"]):
                for r in obj.values():
                    r["warp_depth"] = None
        drift = sorted(k for k in set(committed.get("species", {})) | set(fresh["species"])
                       if committed.get("species", {}).get(k) != fresh["species"].get(k))
        meta_same = committed.get("_meta") == fresh["_meta"]
        check("--check: the committed emerald_rarity.json is what the generator produces",
              not drift and meta_same,
              "" if not drift and meta_same else f"drifted rows {drift[:8]}, _meta same={meta_same}; run --write")

    print()
    if failures:
        print(f"FAILED {len(failures)} check(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
