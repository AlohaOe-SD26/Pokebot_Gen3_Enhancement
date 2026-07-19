#!/usr/bin/env python3
"""
extract_pokedex_entries.py — DEX DATA Phase 3a extractor.

Boots the Emerald ROM headlessly (libmgba, no GUI), reads the ROM's
``gPokedexEntries`` table for all 386 National-Dex species, decodes each
species' **category**, **height**, **weight**, and **flavor text**, and MERGES
those four previously-null fields into the Phase-2 dataset:

    modules/data/generated/pokedex_data.json

Everything else already in that file is preserved untouched. The script is
deterministic and re-runnable (it overwrites just the four ROM-sourced fields
each run and rewrites ``_phase3_gaps`` to reflect what is now populated).

Source of truth = the ROM itself (offline, self-contained). No external data.

Run from the sandbox-pokebot directory:
    py -3.12 tools/extract_pokedex_entries.py

Pipeline note: ``build_dex_data.py`` (Phase 2) assembles pokedex_data.json from
the bot's JSON with these four fields left null. Run THIS script afterwards to
fill them from the ROM. If build_dex_data.py is re-run it re-nulls the fields;
just re-run this script to repopulate them.

--- gPokedexEntries layout (Emerald, verified empirically) ------------------
Symbol size 0x3060 = 12384 bytes / 32 = 387 entries, one per National-Dex
number (index 0 is a dummy; real species are 1..386 == national_dex_number).
Each 32-byte entry:
    0x00  categoryName   u8[12]  Gen-3 encoded, 0xFF-terminated  (e.g. "SEED")
    0x0C  height         u16     decimeters   -> height_m = dm / 10
    0x0E  weight         u16     hectograms   -> weight_kg = hg / 10
    0x10  description    u32     ROM pointer to the flavor-text string
    ...   (scale/offset display fields, unused here)
Category is stored ALL-CAPS ("SEED"); the game appends " POKéMON" at display
time. We store the properly-cased classification ("Seed Pokémon") as
``category`` and preserve the exact ROM string as ``category_raw``.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # sandbox-pokebot/
sys.path.append(str(ROOT))

from modules.context import context  # noqa: E402
from modules.config import Config  # noqa: E402
from modules.roms import load_rom_data  # noqa: E402
from modules.profiles import Profile  # noqa: E402
from modules.game import set_rom, decode_string  # noqa: E402
from modules.libmgba import LibmgbaEmulator  # noqa: E402
from modules.memory import read_symbol, get_symbol, unpack_uint16, unpack_uint32  # noqa: E402

DATA = ROOT / "modules" / "data"
OUT = DATA / "generated"
POKEDEX_JSON = OUT / "pokedex_data.json"
ROM_FILE = ROOT / "roms" / "Pokemon - Emerald Version (USA, Europe).gba"

ENTRY_SIZE = 32
NATIONAL_DEX_COUNT = 386

# gPokedexEntries struct offsets within each 32-byte entry.
OFF_CATEGORY = 0x00
CATEGORY_LEN = 0x0C  # category occupies bytes 0x00..0x0B (height starts at 0x0C)
OFF_HEIGHT = 0x0C
OFF_WEIGHT = 0x0E
OFF_DESCRIPTION = 0x10

# Category words that must stay upper-case (all-caps acronyms). Verified against
# all 386 Emerald categories: "DNA" (Deoxys) is the only one that breaks a plain
# title-case; every other category title-cases cleanly ("Psi", "Symbol", ...).
ACRONYM_WORDS = {"DNA"}


# ---------------------------------------------------------------------------
# ROM boot (headless) — mirrors tests/utility.py::_set_up_test_emulator but
# without a save state, since we only read immutable ROM data.
# ---------------------------------------------------------------------------
def boot_rom() -> None:
    rom = load_rom_data(ROM_FILE)
    if rom.game_code != "BPE":
        raise RuntimeError(f"Expected Emerald (BPE) ROM, got game_code={rom.game_code!r}")
    context.testing = True
    context.config = Config(ROOT / "modules" / "config" / "templates")
    context.profile = Profile(rom, ROOT, datetime.now())
    set_rom(rom)
    context.emulator = LibmgbaEmulator(context.profile, lambda: None, is_test_run=True)


# ---------------------------------------------------------------------------
# Decoding helpers
# ---------------------------------------------------------------------------
def format_category(raw: str) -> str:
    """ALL-CAPS ROM category (e.g. "SEED", "SKY HIGH", "DNA") -> classification
    string ("Seed Pokémon", "Sky High Pokémon", "DNA Pokémon")."""
    words = []
    for word in raw.split():
        words.append(word if word in ACRONYM_WORDS else word.capitalize())
    return " ".join(words) + " Pokémon"


def extract_entries() -> dict[int, dict]:
    """Return {national_dex_number: {category, category_raw, height_m, weight_kg, flavor_text}}."""
    addr, length = get_symbol("gPokedexEntries")
    expected = (NATIONAL_DEX_COUNT + 1) * ENTRY_SIZE
    if length < expected:
        raise RuntimeError(
            f"gPokedexEntries is {length} bytes; expected >= {expected} "
            f"({NATIONAL_DEX_COUNT + 1} x {ENTRY_SIZE})."
        )
    table = read_symbol("gPokedexEntries")

    out: dict[int, dict] = {}
    for ndex in range(1, NATIONAL_DEX_COUNT + 1):
        base = ndex * ENTRY_SIZE
        entry = table[base : base + ENTRY_SIZE]

        raw_category = decode_string(entry[OFF_CATEGORY : OFF_CATEGORY + CATEGORY_LEN])
        height_dm = unpack_uint16(entry[OFF_HEIGHT : OFF_HEIGHT + 2])
        weight_hg = unpack_uint16(entry[OFF_WEIGHT : OFF_WEIGHT + 2])
        desc_ptr = unpack_uint32(entry[OFF_DESCRIPTION : OFF_DESCRIPTION + 4])

        if not (0x08000000 <= desc_ptr < 0x09000000):
            raise RuntimeError(f"National-dex #{ndex}: bad description pointer 0x{desc_ptr:08x}")
        # 512 bytes is comfortably longer than any Gen-3 flavor string.
        raw_desc = context.emulator.read_bytes(desc_ptr, 512)
        flavor = decode_string(raw_desc, replace_newline=True).strip()

        out[ndex] = {
            "category": format_category(raw_category),
            "category_raw": raw_category,
            "height_m": round(height_dm / 10, 1),
            "weight_kg": round(weight_hg / 10, 1),
            "flavor_text": flavor,
        }
    return out


# ---------------------------------------------------------------------------
# Merge into pokedex_data.json
# ---------------------------------------------------------------------------
def merge(entries: dict[int, dict]) -> list[dict]:
    with open(POKEDEX_JSON, encoding="utf-8") as f:
        pokedex = json.load(f)

    missing = []
    for species in pokedex:
        ndex = species["national_dex_number"]
        rom = entries.get(ndex)
        if rom is None:
            missing.append(ndex)
            continue
        species["category"] = rom["category"]
        species["category_raw"] = rom["category_raw"]
        species["height_m"] = rom["height_m"]
        species["weight_kg"] = rom["weight_kg"]
        species["flavor_text"] = rom["flavor_text"]
        # These four are now sourced from the ROM; only dex_artwork remains a gap.
        remaining = [g for g in species.get("_phase3_gaps", []) if g not in
                     ("category", "height_m", "weight_kg", "flavor_text")]
        species["_phase3_gaps"] = remaining

    if missing:
        raise RuntimeError(f"No ROM entry for national-dex numbers: {missing}")

    with open(POKEDEX_JSON, "w", encoding="utf-8") as f:
        json.dump(pokedex, f, ensure_ascii=False, indent=1)
    return pokedex


# ---------------------------------------------------------------------------
# Fact-check + validation
# ---------------------------------------------------------------------------
# (national_dex, name, expected_category, height_m, weight_kg, flavor_substring)
KNOWN_VALUES = [
    (1, "Bulbasaur", "Seed Pokémon", 0.7, 6.9, "seed"),
    (6, "Charizard", "Flame Pokémon", 1.7, 90.5, None),
    (25, "Pikachu", "Mouse Pokémon", 0.4, 6.0, None),
    (321, "Wailord", "Float Whale Pokémon", 14.5, 398.0, None),
    (384, "Rayquaza", "Sky High Pokémon", 7.0, 206.5, None),
    # Additional spot-checks: Unown, Deoxys, a starter, a legendary.
    (201, "Unown", "Symbol Pokémon", 0.5, 5.0, None),
    (386, "Deoxys", "DNA Pokémon", 1.7, 60.8, None),
    (252, "Treecko", "Wood Gecko Pokémon", 0.5, 5.0, None),
    (150, "Mewtwo", "Genetic Pokémon", 2.0, 122.0, None),
    (382, "Kyogre", "Sea Basin Pokémon", 4.5, 352.0, None),
]

REPLACEMENT_CHAR = "�"


def fact_check(pokedex: list[dict]) -> tuple[bool, list[str]]:
    by_ndex = {s["national_dex_number"]: s for s in pokedex}
    lines: list[str] = []
    ok = True

    lines.append("--- Known-value fact-check ---")
    for ndex, name, cat, h, w, flavor_sub in KNOWN_VALUES:
        s = by_ndex.get(ndex)
        problems = []
        if s is None:
            problems.append("MISSING SPECIES")
        else:
            if s["name"] != name:
                problems.append(f"name={s['name']!r}!={name!r}")
            if s["category"] != cat:
                problems.append(f"category={s['category']!r}!={cat!r}")
            if s["height_m"] != h:
                problems.append(f"height={s['height_m']}!={h}")
            if s["weight_kg"] != w:
                problems.append(f"weight={s['weight_kg']}!={w}")
            if flavor_sub and flavor_sub.lower() not in s["flavor_text"].lower():
                problems.append(f"flavor missing {flavor_sub!r}")
        status = "OK" if not problems else "FAIL"
        if problems:
            ok = False
        lines.append(f"  [{status}] #{ndex} {name}: " + (", ".join(problems) if problems else
                     f"{s['category']} | {s['height_m']}m | {s['weight_kg']}kg"))

    # Completeness: every species has non-empty category + flavor, positive h/w.
    empty_cat, empty_flavor, bad_h, bad_w, mojibake = [], [], [], [], []
    for s in pokedex:
        if not s.get("category") or not s.get("category_raw"):
            empty_cat.append(s["national_dex_number"])
        if not s.get("flavor_text"):
            empty_flavor.append(s["national_dex_number"])
        if not isinstance(s.get("height_m"), (int, float)) or s["height_m"] <= 0:
            bad_h.append(s["national_dex_number"])
        if not isinstance(s.get("weight_kg"), (int, float)) or s["weight_kg"] <= 0:
            bad_w.append(s["national_dex_number"])
        if REPLACEMENT_CHAR in (s.get("flavor_text", "") + s.get("category", "")):
            mojibake.append(s["national_dex_number"])

    lines.append("--- Completeness (all 386) ---")
    lines.append(f"  species with category:   {386 - len(empty_cat)}/386")
    lines.append(f"  species with flavor_text:{386 - len(empty_flavor)}/386")
    lines.append(f"  species with height>0:   {386 - len(bad_h)}/386")
    lines.append(f"  species with weight>0:   {386 - len(bad_w)}/386")
    lines.append(f"  species with mojibake (U+FFFD): {len(mojibake)}")
    for label, lst in (("empty category", empty_cat), ("empty flavor", empty_flavor),
                       ("height<=0", bad_h), ("weight<=0", bad_w), ("mojibake", mojibake)):
        if lst:
            ok = False
            lines.append(f"  !! {label}: {lst}")

    # Extremes sanity: Wailord largest, some smallest.
    tallest = max(pokedex, key=lambda s: s["height_m"])
    heaviest = max(pokedex, key=lambda s: s["weight_kg"])
    lines.append("--- Extremes ---")
    lines.append(f"  tallest: {tallest['name']} {tallest['height_m']}m")
    lines.append(f"  heaviest: {heaviest['name']} {heaviest['weight_kg']}kg")

    return ok, lines


def sample_flavors(pokedex: list[dict], ndexes: list[int]) -> list[str]:
    by_ndex = {s["national_dex_number"]: s for s in pokedex}
    out = []
    for n in ndexes:
        s = by_ndex.get(n)
        if s:
            out.append(f"  #{n} {s['name']} ({s['category']}): {s['flavor_text']}")
    return out


def main() -> int:
    print("Booting Emerald ROM headlessly ...")
    boot_rom()
    print("Reading gPokedexEntries ...")
    entries = extract_entries()
    print(f"Extracted {len(entries)} entries. Merging into {POKEDEX_JSON.name} ...")
    pokedex = merge(entries)

    ok, lines = fact_check(pokedex)
    print("\n".join(lines))
    print("--- Sample decoded flavor text ---")
    print("\n".join(sample_flavors(pokedex, [1, 6, 25, 133, 321, 384, 386])))

    print("\nFACT-CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
