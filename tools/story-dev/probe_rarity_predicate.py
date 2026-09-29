"""GATE — the rare-species predicate (design v2 step 7, RP): `modules/rarity.py` over `emerald_rarity.json`, and the
generator `rare_species_dataset.py` that writes it.

WHY. Step 8 will let a RARE species through the cap-3 rule without limit, and the user accepted that a rare species may
cost whiteout after whiteout (06:8093-8095). So a species wrongly called rare is a real cost, and one wrongly called
ordinary is a lost catch. Every branch of the predicate is reachable with literal inputs, so the proof is pure.

WHAT IT CHECKS
  L   literal rows through the REAL `Pokemon.gender` property (a stub borrows it), the real species objects and the
      committed table: Skitty at the gender boundary, Abra, Relicanth, Bagon, Solrock, Mawile, Ralts, Pelipper,
      Magneton (genderless), Feebas, Mew, Rayquaza, the no-data species, the empty slot and index 0 (reads as Mew),
      a raising adapter, and an unreadable table.
  S   full-set equality against the literal lists (rate 14, variant 6, pseudo, legendary 21, special 1, nothing else).
  D   data facts the recon found: the UNDERWATER name trap, the Altering Cave dead set, the excluded rows.
  P   the generator's pure rule on synthetic stubs (per-MAPSEC counting, min over rows, the underwater gate, P(minority)).
  C   `rare_species_dataset.py --check`: the committed JSON is exactly what the generator produces (C1), and the
      comparator goes red on a drifted copy (C2).
  M   one source mutant per guard, each of which must turn a named check RED (a missing anchor fails explicitly), and
      a negative arm: editing a COMMENT that mentions a guarded token must turn nothing red.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_rarity_predicate.py        (exit 1 on any failure)
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import types

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

GEN_PATH = HERE / "rare_species_dataset.py"
RAR_PATH = SANDBOX / "modules" / "rarity.py"

spec = importlib.util.spec_from_file_location("rare_species_dataset", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

from modules import rarity  # noqa: E402
from modules.pokemon import Pokemon, get_species_by_index, get_species_by_national_dex  # noqa: E402

# ------------------------------------------------------------------------------------------------ the literal record
RATE = {82, 101, 195, 224, 273, 274, 313, 321, 352,   # 1%
        88, 300, 311, 358,                            # 2%
        280}                                          # 4% (Ralts)
VARIANT = {300: ("male", 0.5078125), 369: ("female", 0.60546875), 209: ("male", 1.26953125),
           63: ("female", 2.4609375), 39: ("male", 2.5390625), 222: ("male", 3.80859375)}
PSEUDO = {361, 371}   # Snorunt (Shoal Cave Ice Room: strength + surf) and Bagon (surf + waterfall)
LEGENDARY = {144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 251, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386}
SPECIAL = {349}

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)
    return ok


class Mon:
    """A stand-in `Pokemon` that borrows the REAL `gender` property, so the gender rule under test is production's."""

    gender = Pokemon.gender

    def __init__(self, national=None, pv=0, shiny=False, empty=False, internal=None, valid=True, egg=False):
        self.species = get_species_by_index(internal) if internal is not None else get_species_by_national_dex(national)
        self.personality_value = pv
        self.is_shiny = shiny
        self.is_empty = empty
        self.is_valid = valid
        self.is_egg = egg


class RaisingMon:
    is_empty = False
    is_valid = True
    is_egg = False

    @property
    def species(self):
        raise RuntimeError("adapter fault")


def verdict_of(mod, table, national, pv=0, shiny=False):
    return mod.encounter_rarity(Mon(national, pv, shiny), table)


# ------------------------------------------------------------------------------------------------ the checks (reusable)
def literal_rows(mod, table, tag="") -> list[str]:
    """The L rows. Returns the labels that failed (the caller decides whether that is expected)."""
    failed: list[str] = []

    def row(label, national, pv, want_rare, want_tier, want_reasons, shiny=False, want_note=None):
        v = verdict_of(mod, table, national, pv, shiny)
        ok = (v.rare, v.tier, v.reasons, v.note) == (want_rare, want_tier, tuple(want_reasons), want_note)
        if not ok:
            failed.append(label)
        if not tag:
            check(label, ok, f"got {v}")

    row("L1 Skitty 300 PV 0x10 (female) -> rate, RARE", 300, 0x10, True, "RARE", ["rate"])
    row("L2 Skitty 300 PV 0xC0 (male) -> rate + variant, ULTRA", 300, 0xC0, True, "ULTRA", ["rate", "variant"])
    row("L3 Skitty 300 PV 0xBE (190 < 191: female) -> RARE", 300, 0xBE, True, "RARE", ["rate"])
    row("L4 Skitty 300 PV 0xBF (191: male) -> ULTRA", 300, 0xBF, True, "ULTRA", ["rate", "variant"])
    row("L5 Bagon 371 -> pseudo, RARE", 371, 0, True, "RARE", ["pseudo"])
    row("L5b Snorunt 361 -> pseudo, RARE (Shoal Cave Ice Room)", 361, 0x10, True, "RARE", ["pseudo"])
    row("L5c Spheal 363 -> not rare (Shoal Cave, but its easiest room needs only Surf)", 363, 0x10, False, None, [])
    row("L6 Zigzagoon 263 female -> not rare", 263, 0x10, False, None, [])
    row("L7 Zigzagoon 263 male -> not rare", 263, 0xF0, False, None, [])
    row("L8 Zigzagoon 263 shiny -> shiny, ULTRA", 263, 0x10, True, "ULTRA", ["shiny"], shiny=True)
    row("L9 Abra 63 PV 10 (female) -> variant, ULTRA", 63, 10, True, "ULTRA", ["variant"])
    row("L10 Abra 63 PV 200 (male) -> not rare", 63, 200, False, None, [])
    row("L11 Abra 63 PV 62 (female, boundary) -> variant", 63, 62, True, "ULTRA", ["variant"])
    row("L12 Abra 63 PV 63 (male, boundary) -> not rare", 63, 63, False, None, [])
    row("L13 Relicanth 369 PV 30 (female) -> variant, ULTRA", 369, 30, True, "ULTRA", ["variant"])
    row("L14 Relicanth 369 PV 31 (male) -> not rare", 369, 31, False, None, [])
    row("L15 Pelipper 279 -> not rare (5%)", 279, 0x10, False, None, [])
    row("L16 Ralts 280 -> rate, RARE (4%)", 280, 0x10, True, "RARE", ["rate"])
    row("L17 Feebas 349 -> special, RARE", 349, 0x10, True, "RARE", ["special"])
    row("L18 Mew 151 -> legendary, RARE", 151, 0, True, "RARE", ["legendary"])
    row("L19 Rayquaza 384 (internal 406) -> legendary, RARE", 384, 0, True, "RARE", ["legendary"])
    row("L20 Magneton 82 (genderless) -> rate, RARE", 82, 0x10, True, "RARE", ["rate"])
    row("L21 Solrock 338 -> not rare (Meteor Falls only, but 1F_1R has no gate)", 338, 0, False, None, [])
    row("L22 Mawile 303 -> not rare (Victory Road is on the story path; 5%)", 303, 0x10, False, None, [])
    row("L23 Wynaut 360 -> not rare, no data (Route 130 land is excluded)", 360, 0x10, False, None, [], want_note="no_data")
    row("L24 Sudowoodo 185 -> not rare, no data (not special)", 185, 0x10, False, None, [], want_note="no_data")
    row("L25 Surskit 283 -> not rare, no data", 283, 0x10, False, None, [], want_note="no_data")
    row("L26 Surskit 283 shiny -> shiny, ULTRA, no data", 283, 0x10, True, "ULTRA", ["shiny"], shiny=True,
        want_note="no_data")

    def special(label, mon, want_note):
        try:
            v = mod.encounter_rarity(mon, table)
            ok = (v.rare, v.note) == (False, want_note)
        except Exception as error:  # noqa: BLE001
            v, ok = f"RAISED {type(error).__name__}: {error}", False
        if not ok:
            failed.append(label)
        if not tag:
            check(label, ok, f"got {v}")

    # ‼ The empty slot names a REAL species (stale bytes), so only the is_empty guard can keep it out (the review:
    # an internal-0 fixture here passed with that guard deleted, because the index-0 guard caught it first).
    special("L27 an empty slot whose stale bytes name Mew -> not rare, no_species", Mon(151, empty=True), "no_species")
    special("L27b a failed checksum that decodes to Lugia -> not rare, invalid", Mon(249, valid=False), "invalid")
    special("L27c an egg of a male Skitty -> not rare, egg", Mon(300, 0xC0, egg=True), "egg")
    special("L28 species index 0 (national reads 151 = Mew) -> not rare, no_species", Mon(internal=0), "no_species")
    special("L29 an adapter that raises -> not rare, adapter_error, no raise", RaisingMon(), "adapter_error:RuntimeError")
    special("L30 None -> not rare, no_species", None, "no_species")
    return failed


def set_rows(species: dict, tag="") -> list[str]:
    """The S rows over a {national-string: row} table."""
    failed: list[str] = []

    def srow(label, ok, detail=""):
        if not ok:
            failed.append(label)
        if not tag:
            check(label, ok, detail)

    by = lambda reason: {int(k) for k, r in species.items() if reason in r["reasons"]}  # noqa: E731
    srow("S1 rate == the 14 literal species", by("rate") == RATE, str(sorted(by("rate") ^ RATE)))
    got_v = {int(k): (r["variant_gender"], r["variant_pct"]) for k, r in species.items() if r["variant_gender"]}
    srow("S2 variant == the 6 literal (gender, exact %)", got_v == VARIANT, str(got_v))
    srow("S3 pseudo == the literal set", by("pseudo") == PSEUDO, str(sorted(by("pseudo"))))
    srow("S4 legendary == the 21 literal", by("legendary") == LEGENDARY, str(sorted(by("legendary") ^ LEGENDARY)))
    srow("S5 special == {349}", by("special") == SPECIAL, str(sorted(by("special"))))
    others = {int(k) for k, r in species.items() if r["reasons"]} - RATE - PSEUDO - LEGENDARY - SPECIAL
    srow("S6 no other species carries a reason", not others, str(sorted(others)))
    srow("S7 131 wild species + 21 legendary + Feebas = 153 rows", len(species) == 153, str(len(species)))
    return failed


def data_rows(species: dict, tag="") -> list[str]:
    failed: list[str] = []

    def drow(label, ok, detail=""):
        if not ok:
            failed.append(label)
        if not tag:
            check(label, ok, detail)

    def secs(n):
        return len(species.get(str(n), {}).get("mapsecs", []))

    drow("D1 Chinchou 170, Clamperl 366, Relicanth 369 each have 2 MAPSECs (UNDERWATER_124/126 share a NAME)",
         [secs(170), secs(366), secs(369)] == [2, 2, 2], str([secs(170), secs(366), secs(369)]))
    drow("D2 Smeargle 235 has 1 MAPSEC, Artisan Cave only (the dead Altering Cave set is not read)",
         species.get("235", {}).get("maps") == ["ARTISAN_CAVE_1F", "ARTISAN_CAVE_B1F"],
         str(species.get("235", {}).get("maps")))
    drow("D3 Zubat 41 lives in ALTERING_CAVE (the live set 0)", "ALTERING_CAVE" in species.get("41", {}).get("maps", []))
    dead = sorted({m for r in species.values() for m in r["maps"] if m.startswith("CAVE_OF_ORIGIN_UNUSED")})
    drow("D4 no row lists an unused Cave of Origin map", not dead, str(dead))
    drow("D5 keyed by NATIONAL dex: Skitty 300 is internal 315 (key 315, Roselia, has no Emerald wild table); "
         "Nuzleaf 274 is internal 299, and key 299 is Nosepass, not rare",
         species.get("300", {}).get("internal") == 315 and "315" not in species
         and species.get("274", {}).get("internal") == 299 and species.get("299", {}).get("name") == "Nosepass"
         and not species["299"]["reasons"] and species["274"]["reasons"] == ["rate"])
    drow("D6 Bagon's gates are {surf, waterfall} in 1 MAPSEC",
         species.get("371", {}).get("gates") == ["surf", "waterfall"] and secs(371) == 1)
    drow("D7 Snorunt's gates are {strength, surf} in 1 MAPSEC; Spheal's are {surf}",
         species.get("361", {}).get("gates") == ["strength", "surf"] and secs(361) == 1
         and species.get("363", {}).get("gates") == ["surf"])
    return failed


def pure_rows(g, tag="") -> list[str]:
    failed: list[str] = []

    def prow(label, ok, detail=""):
        if not ok:
            failed.append(label)
        if not tag:
            check(label, ok, detail)

    two_maps_one_sec = [{"map": [7, 1], "method": "Grass", "rate": 20}, {"map": [7, 2], "method": "Grass", "rate": 20}]
    prow("P1 two maps in ONE section count as 1 location", g.n_mapsecs(two_maps_one_sec, {(7, 1): 9, (7, 2): 9}) == 1)
    prow("P2 ... and two sections as 2", g.n_mapsecs(two_maps_one_sec, {(7, 1): 9, (7, 2): 10}) == 2)
    saved = dict(g.MAP_ACCESS_GATES)
    try:
        g.MAP_ACCESS_GATES.clear()
        g.MAP_ACCESS_GATES.update({(7, 1): ("surf", "waterfall"), (7, 2): ("surf", "waterfall")})
        gates = g.easiest_gates(two_maps_one_sec, set())
        prow("P3 a species in 2 gated maps of 1 section is pseudo",
             g.is_pseudo(gates, g.n_mapsecs(two_maps_one_sec, {(7, 1): 9, (7, 2): 9})), str(sorted(gates)))
        mixed = [{"map": [7, 1], "method": "Grass", "rate": 20}, {"map": [7, 3], "method": "Grass", "rate": 20}]
        prow("P4 min over rows: an ungated second home makes the species ungated",
             g.easiest_gates(mixed, set()) == frozenset(), str(sorted(g.easiest_gates(mixed, set()))))
    finally:
        g.MAP_ACCESS_GATES.clear()
        g.MAP_ACCESS_GATES.update(saved)
    prow("P5 an underwater map's Surfing row needs {surf, dive}",
         g.row_gates((0, 50), "Surfing", {(0, 50)}) == frozenset({"surf", "dive"}))
    prow("P6 P(minority): 191 -> male 65/256; 63 -> female 63/256; 31 -> female 31/256; 127 -> none",
         (g.minority_gender(191), float(g.p_minority(191)), g.minority_gender(63), float(g.p_minority(63)),
          g.minority_gender(31), float(g.p_minority(31)), g.minority_gender(127))
         == ("male", 65 / 256, "female", 63 / 256, "female", 31 / 256, None))
    return failed


def run_check(g) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = g.main(["--check"])
    return rc, buf.getvalue()


def drift_detected(g) -> tuple[bool, str]:
    """Point `--check` at a DRIFTED copy of the committed table (Bagon's gates edited) and require it to go red. This
    is the only thing that fault-tests the comparator, which alone catches edits to MAP_ACCESS_GATES, the underwater
    rule or the method gates (none of the S/D/P rows see those; the step 7 review measured it)."""
    drifted = json.loads(rarity.DATA_FILE.read_text(encoding="utf-8"))
    drifted["species"]["371"]["gates"] = ["surf"]
    saved = g.OUT
    with tempfile.TemporaryDirectory() as tmp:
        g.OUT = pathlib.Path(tmp) / "emerald_rarity.json"
        g.OUT.write_text(json.dumps(drifted, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        try:
            rc, out = run_check(g)
        finally:
            g.OUT = saved
    return rc == 1 and "FAIL  --check:" in out, f"rc={rc}"


# ------------------------------------------------------------------------------------------------ mutants
def mutant(path: pathlib.Path, name: str, old: str, new: str, count: int = 1) -> types.ModuleType:
    src = path.read_text(encoding="utf-8")
    n = src.count(old)
    if n != count:
        raise AssertionError(f"mutant anchor for {name!r} found {n} times, expected {count}: {old!r}")
    mod = types.ModuleType(f"mut_{name}")
    mod.__file__ = str(path)
    sys.modules[mod.__name__] = mod   # `@dataclass` looks its module up in sys.modules
    exec(compile(src.replace(old, new), f"<mutant {name}>", "exec"), mod.__dict__)
    return mod


def main() -> int:
    table = rarity.load_table()
    committed = json.loads(rarity.DATA_FILE.read_text(encoding="utf-8"))["species"]
    print("L — literal rows (real Pokemon.gender, real species, the committed table)")
    literal_rows(rarity, table)
    print("\nL' — an unreadable table degrades to {} and never raises")
    with tempfile.TemporaryDirectory() as tmp:
        bad = pathlib.Path(tmp) / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        check("L31 a missing file -> {}", rarity.load_table(pathlib.Path(tmp) / "absent.json") == {})
        check("L32 a corrupt file -> {}", rarity.load_table(bad) == {})
        v = rarity.encounter_rarity(Mon(300, 0xC0), {})
        check("L33 with an empty table the male Skitty is not rare (no_data), and nothing raises",
              (v.rare, v.note) == (False, "no_data"), str(v))
    print("\nS — full-set equality (committed table)")
    set_rows(committed)
    print("\nD — data facts")
    data_rows(committed)
    print("\nP — the generator's pure rule on synthetic stubs")
    pure_rows(gen)
    print("\nC — the committed JSON is exactly what the generator produces")
    rc, out = run_check(gen)
    check("C1 rare_species_dataset.py --check exits 0", rc == 0,
          "; ".join(l.strip() for l in out.splitlines() if "FAIL" in l or "SKIP" in l) or "")
    for line in out.splitlines():
        if "SKIP" in line:
            print(f"  {line.strip()}")
    ok, detail = drift_detected(gen)
    check("C2 --check goes RED on a drifted copy of the table (the comparator can fail)", ok, detail)

    print("\nM — mutants (each must turn its named check RED)")

    def expect_red(label, failed: list[str], must_include: str):
        check(label, any(f.startswith(must_include) for f in failed), f"red: {failed[:6]}")

    # rarity.py
    m = mutant(RAR_PATH, "gender_inverted", 'gender == row["variant_gender"]', 'gender != row["variant_gender"]')
    expect_red("M1 gender inverted -> L2 red", literal_rows(m, table, "m"), "L2 ")
    m = mutant(RAR_PATH, "keyed_internal", "rows.get(species.national_dex_number)", "rows.get(species.index)")
    expect_red("M2 keyed by the internal index -> L2 red (key 315 has no row)", literal_rows(m, table, "m"), "L2 ")
    m = mutant(RAR_PATH, "tier_dropped", "tier = TIER_ULTRA if any(r in ULTRA_REASONS for r in reasons) else TIER_RARE",
               "tier = TIER_RARE")
    expect_red("M3 the tier dropped -> L2 red", literal_rows(m, table, "m"), "L2 ")
    m = mutant(RAR_PATH, "adapter_raises", "    except Exception as error:  # noqa: BLE001\n        return RareVerdict(False, None, (), f\"adapter_error",
               "    except ZeroDivisionError as error:  # noqa: BLE001\n        return RareVerdict(False, None, (), f\"adapter_error")
    expect_red("M4 the adapter raising -> L29 red", literal_rows(m, table, "m"), "L29 ")
    m = mutant(RAR_PATH, "no_index0_guard", "        if species.index == 0:\n", "        if False:\n")
    expect_red("M5 no index-0 guard -> L28 red (it reads as Mew, legendary)", literal_rows(m, table, "m"), "L28 ")

    # the generator: regenerate in memory under the mutant, then run the same set/data checks
    def regen(g):
        payload, *_ = g.generate()
        return payload["species"]

    m = mutant(GEN_PATH, "threshold5", "RATE_MAX_PCT = 4 ", "RATE_MAX_PCT = 5 ")
    expect_red("M6 a <=5% threshold -> S1 red", set_rows(regen(m), "m"), "S1 ")
    m = mutant(GEN_PATH, "per_map", 'return len({mapsec_of[tuple(r["map"])] for r in rows})',
               'return len({tuple(r["map"]) for r in rows})')
    expect_red("M7 locations counted per map -> P1 red", pure_rows(m, "m"), "P1 ")
    m = mutant(GEN_PATH, "max_rows", "return min(options, key=lambda g: (len(g), sorted(g)))",
               "return max(options, key=lambda g: (len(g), sorted(g)))")
    expect_red("M8 max (not min) over rows -> S3 red (Solrock turns pseudo)", set_rows(regen(m), "m"), "S3 ")
    m = mutant(GEN_PATH, "cave_of_origin", "    (24, 39): (None,", "    (99, 39): (None,")
    expect_red("M9 the unused Cave of Origin rows included -> D4 red", data_rows(regen(m), "m"), "D4 ")
    m = mutant(GEN_PATH, "route130", '    (0, 45): ("Grass",', '    (99, 45): ("Grass",')
    expect_red("M10 Route 130's land table included -> S7 red (Wynaut gets a row)", set_rows(regen(m), "m"), "S7 ")
    m = mutant(GEN_PATH, "every_set", "        if key in seen:\n", "        if key in seen and False:\n")
    expect_red("M11 Altering Cave sets 1-8 included -> D2 red (Smeargle gains ALTERING_CAVE)",
               data_rows(regen(m), "m"), "D2 ")
    m = mutant(GEN_PATH, "name_keyed", "    return mapsec_of, index, duplicates",
               "    mapsec_of[(0, 51)] = mapsec_of[(0, 50)]\n    return mapsec_of, index, duplicates")
    expect_red("M12 keyed by region-map NAME (UNDERWATER_124 == 126) -> D1 red", data_rows(regen(m), "m"), "D1 ")
    if (gen.CACHE / "warp_graph_BPEE0.json").exists():
        m = mutant(GEN_PATH, "edge1", "s, d = tuple(edge[0]), tuple(edge[2])", "s, d = tuple(edge[0]), tuple(edge[1])")
        rc_m, out_m = run_check(m)
        check("M13 parsing edge[1] -> --check red (the warp-depth column and the record drift)",
              rc_m == 1 and "FAIL  the record: the warp-depth histogram" in out_m and "FAIL  --check:" in out_m,
              f"rc={rc_m}")
    else:
        print("  SKIP  M13 edge[1] — cache/ is absent. THIS IS NOT A PASS.")

    m = mutant(RAR_PATH, "no_empty_guard", "        if pokemon is None or pokemon.is_empty:\n",
               "        if pokemon is None:\n")
    expect_red("M14 no is_empty guard -> L27 red (a stale Mew reads as legendary)", literal_rows(m, table, "m"), "L27 ")
    m = mutant(RAR_PATH, "no_valid_guard", "        if not pokemon.is_valid:\n", "        if False:\n")
    expect_red("M15 no checksum guard -> L27b red", literal_rows(m, table, "m"), "L27b ")
    m = mutant(RAR_PATH, "no_egg_guard", "        if pokemon.is_egg:\n", "        if False:\n")
    expect_red("M16 no egg guard -> L27c red", literal_rows(m, table, "m"), "L27c ")
    m = mutant(GEN_PATH, "blind_comparator",
               '        committed = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}',
               "        committed = json.loads(text)")
    ok, detail = drift_detected(m)
    check("M17 a --check that compares the fresh table with itself -> C2 red", not ok, detail)

    print("\nN — negative arm: a comment mentioning guarded tokens is not a guard")
    m = mutant(GEN_PATH, "comment_only", "(`modules/warp_graph.py` `to_json`), so the destination MAP is `edge[2]`",
               "(`modules/warp_graph.py` `to_json`), so the destination MAP is `edge[1]` (edited comment)")
    regenerated = regen(m)
    check("N1 editing a comment that names edge[2] turns no S/D/P row red",
          not (set_rows(regenerated, "m") + data_rows(regenerated, "m") + pure_rows(m, "m")))
    m = mutant(RAR_PATH, "doc_only", "‼ Not by the internal ROM index", "‼ (edited) Not by the internal ROM index")
    check("N2 editing the rarity docstring turns no L row red", not literal_rows(m, table, "m"))

    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
