"""
Unit tests for modules/obtainability.py (#41).

Fact-checks the compiled Emerald obtainability categories against the ROM's
own encounter tables + species data. Runs headless: it wires the Emerald ROM
*header* (via load_rom_data — no emulator boot) into the context so the
Emerald override + the cached encounter index resolve. Skips cleanly if the
Emerald ROM or its encounter-index cache is not present.

See PROJECT KNOWLEDGE/11-LIVINGDEX-DESIGN.md (Phase: #41-research) for the
compiled lists, citations, and the full validation report.
"""

import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from modules.context import context
from modules.runtime import get_base_path


def _wire_emerald_rom() -> bool:
    """Point context at the real Emerald ROM header. Returns False to skip."""
    from modules.roms import load_rom_data

    roms_dir = get_base_path() / "roms"
    if not roms_dir.is_dir():
        return False
    for f in roms_dir.glob("*.gba"):
        try:
            rom = load_rom_data(f)
        except Exception:
            continue
        if rom.is_emerald:
            cache = get_base_path() / "cache" / f"encounter_index_{rom.id}.json"
            if not cache.is_file():
                return False  # no cached wild index -> would need emulator to build
            context.profile = SimpleNamespace(rom=rom, path=Path("."))
            return True
    return False


@unittest.skipUnless(_wire_emerald_rom(), "Emerald ROM + encounter-index cache required")
class TestObtainability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from modules import obtainability as ob

        cls.ob = ob
        cls.census = ob.census()

    def _kind(self, name: str) -> str:
        from modules.pokemon import get_species_by_name

        return self.ob.classify(get_species_by_name(name).index)["kind"]

    def _info(self, name: str) -> dict:
        from modules.pokemon import get_species_by_name

        return self.ob.classify(get_species_by_name(name).index)

    # -- census integrity -------------------------------------------------
    def test_census_sums_to_386(self):
        self.assertEqual(self.census["total"], 386)
        self.assertEqual(sum(self.census["by_kind"].values()), 386)

    def test_no_species_left_unknown(self):
        self.assertNotIn("unknown", self.census["by_kind"])

    def test_category_counts(self):
        self.assertEqual(
            self.census["by_kind"],
            # User ruling 2026-07-19: both Lati@s obtainable (roamer) → static 7 / roamer 2.
            {"wild": 132, "evolution": 149, "gift": 7, "static": 7, "roamer": 2,
             "event": 6, "breeding": 3, "special": 1, "unobtainable": 79},
        )

    def test_emerald_reachable_denominator(self):
        # obtainable in Emerald WITHOUT trading (the 2nd living-dex denominator)
        # 218 after the Latias+Latios-both-obtainable ruling (Latios flipped +1).
        self.assertEqual(self.census["emerald_reachable"], 218)
        self.assertEqual(self.census["not_reachable"], 168)

    # -- override integrity ----------------------------------------------
    def test_override_natdex_roundtrip(self):
        from modules.pokemon import get_species_by_national_dex

        for nd, entry in self.ob._load_override_raw().items():
            self.assertEqual(get_species_by_national_dex(nd).name, entry["name"])

    # -- spot-checks by category -----------------------------------------
    def test_static_legendaries(self):
        for n in ["Rayquaza", "Kyogre", "Groudon", "Regirock", "Regice", "Registeel", "Sudowoodo"]:
            self.assertEqual(self._kind(n), "static", n)

    def test_lati_pair(self):
        # User ruling 2026-07-19: BOTH obtainable (bot targets whichever roams
        # in the actual save via get_roamer()). Both classified roamer+reachable.
        self.assertEqual(self._kind("Latias"), "roamer")
        self.assertEqual(self._kind("Latios"), "roamer")
        self.assertTrue(self._info("Latias")["emerald_reachable"])
        self.assertTrue(self._info("Latios")["emerald_reachable"])

    def test_gifts(self):
        for n in ["Treecko", "Torchic", "Mudkip", "Castform", "Lileep", "Anorith", "Beldum"]:
            self.assertEqual(self._kind(n), "gift", n)

    def test_events(self):
        for n in ["Mew", "Celebi", "Jirachi", "Deoxys", "Lugia", "Ho-Oh"]:
            self.assertEqual(self._kind(n), "event", n)
            self.assertFalse(self._info(n)["emerald_reachable"], n)

    def test_breeding_and_special(self):
        for n in ["Pichu", "Igglybuff", "Azurill"]:
            self.assertEqual(self._kind(n), "breeding", n)
            self.assertTrue(self._info(n)["emerald_reachable"], n)
        self.assertEqual(self._kind("Feebas"), "special")
        self.assertTrue(self._info("Feebas")["emerald_reachable"])

    def test_unobtainable(self):
        for n in ["Bulbasaur", "Charmander", "Squirtle", "Meowth", "Eevee",
                  "Zangoose", "Lunatone", "Roselia", "Meditite", "Surskit"]:
            self.assertEqual(self._kind(n), "unobtainable", n)
            self.assertFalse(self._info(n)["emerald_reachable"], n)

    def test_wild(self):
        for n in ["Wailmer", "Ralts", "Wynaut", "Poochyena"]:
            self.assertEqual(self._kind(n), "wild", n)

    # -- evolution reachability ------------------------------------------
    def test_trade_evolutions_not_reachable_without_trade(self):
        for n in ["Alakazam", "Machamp", "Golem", "Gengar", "Politoed", "Slowking",
                  "Steelix", "Scizor", "Kingdra", "Porygon2", "Huntail", "Gorebyss"]:
            info = self._info(n)
            self.assertEqual(info["kind"], "evolution", n)
            self.assertFalse(info["emerald_reachable"], n)

    def test_evolution_of_unobtainable_base_not_reachable(self):
        self.assertFalse(self._info("Venusaur")["emerald_reachable"])
        self.assertFalse(self._info("Raticate")["emerald_reachable"])
        # Raichu evolves from Pikachu (wild in the Safari Zone) -> reachable
        self.assertTrue(self._info("Raichu")["emerald_reachable"])

    # -- plan_for obtainability gate -------------------------------------
    def test_plan_gate_blocks_non_wild(self):
        from modules.pokemon import get_species_by_name

        for n in ["Bulbasaur", "Mew", "Rayquaza", "Beldum", "Latias", "Feebas", "Azurill"]:
            p = self.ob.plan_for(get_species_by_name(n).index)
            self.assertFalse(p["wild_huntable"], n)
            self.assertIsNone(p["target_index"], n)

    def test_plan_gate_allows_wild_and_wild_base_evolution(self):
        from modules.pokemon import get_species_by_name

        for n in ["Wailmer", "Ralts", "Gardevoir"]:
            p = self.ob.plan_for(get_species_by_name(n).index)
            self.assertTrue(p["wild_huntable"], n)
            self.assertIsNotNone(p["target_index"], n)


if __name__ == "__main__":
    unittest.main()
