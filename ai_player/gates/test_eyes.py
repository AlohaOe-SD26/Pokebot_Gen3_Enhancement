"""UNIT PROOFS of AI-player build step 1 (the eyes, the action log, the scorer lines). Test side.

    py -3.12 ai_player/gates/test_eyes.py        (exit 0 = every test passed)

What each class proves, and its FAULT half (a check that cannot fail proves nothing, CLAUDE.md rule 6):
  FrameworkFreeTests   the eyes' vocabulary, perception rules and party decoder, the action log and the
                       brain import NOTHING from the framework or the host side (a standalone build keeps
                       them); FAULT: a planted framework import and a planted host import are caught.
  GeometryTests        the on-screen window is 15 x 11 (dx -7..+7, dy -5..+5), edges included/excluded.
  BehaviorTableTests   the behaviour table (generated from pokeemerald's header) has the decomp's values,
                       and agrees with the FRAMEWORK's independent tile-name table on every behaviour the
                       eyes classify (grass, ledges, doors, water).
  PartyDecoderTests    `eyes/party.py` decodes a Pokemon encrypted by an encoder that uses the FRAMEWORK's
                       own substructure table, for all 24 personality orders, and agrees with the
                       framework's decoder; a torn slot is refused; FAULT: one swapped table row is caught.
  FlagTests            every story / badge flag name the eyes read exists in the flag table the framework
                       uses (`get_event_flag` returns False SILENTLY for a phantom); FAULT: a phantom fails.
  ScreenTests          what `classify_screen` calls each screen.
  WaitRuleTests        `text_printer_wait`: the decomp's render states (WAIT = 1 is `{PAUSE_UNTIL_PRESS}`,
                       CLEAR = 2 and SCROLL_START = 3 the down arrow) wait, on ANY of the 32 printers, and
                       nothing waits under autoScroll; FAULT: the pre-fix rule (states {2, 3}, the round-1
                       defect the verifier found) misses a trainer's defeat text, and printer 0 only misses
                       the party menu's (the live arm XW does the same on natural captures).
  ScorerTests          the lines the AI writes are parsed by `ai-agent/scoring.py` `parse_log` ITSELF into
                       the expected record (starter, maps, catches, Pokedex, badges, wins, money, frames),
                       each line matches the scorer's own regex, and the New Game path is OBSERVED;
                       FAULT: events before the starter line are ignored by the scorer, and a [MAP] line
                       missing its (group,number) is not counted (so the format is load-bearing).
  ActionLogTests       one JSON line per record with frame, digest, decision, action, reason and the
                       compact observation (165 tiles); a record with a newline is refused.
"""

from __future__ import annotations

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "ai_player"
BUILD_ROOT = REPO / "sandbox-pokebot"
for entry in (str(REPO), str(BUILD_ROOT), str(REPO / "ai-agent")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from ai_player.eyes import party as party_module  # noqa: E402
from ai_player.eyes.observation import (  # noqa: E402
    BagSummary, BattleMon, BattleView, MonSummary, Observation, PlayerState, Progress, ScreenState, Tile, View,
)
from ai_player.eyes.party import PARTY_MON_SIZE, decode_party_mon  # noqa: E402
from ai_player.eyes import view as view_module  # noqa: E402
from ai_player.eyes.view import (  # noqa: E402
    BADGE_FLAGS, BEHAVIOR, BEHAVIOR_NAMES, DOOR_BEHAVIORS, LEDGE_DIRECTIONS, RENDER_STATE_NAMES, STORY_FLAGS,
    TALL_GRASS_BEHAVIORS, TEXT_FLAG_AUTO_SCROLL, TEXT_PRINTER_COUNT, TEXT_PRINTER_WAIT_STATES, VIEW_DOWN, VIEW_HALF_WIDTH,
    VIEW_UP, classify_screen, in_view, text_printer_wait, view_offsets,
)
from ai_player.memory_log import ActionLog, ScorerLines  # noqa: E402
from ai_player.runlog import RecordFile  # noqa: E402

#: The files that must stay framework-free (and host-free).
FRAMEWORK_FREE = ("eyes/__init__.py", "eyes/observation.py", "eyes/view.py", "eyes/party.py", "memory_log.py", "mode.py")


# ------------------------------------------------------------------------------------------- helpers
def foreign_imports(source: str) -> list[str]:
    """Every import that is neither the standard library nor a framework-free part of ai_player."""
    found = []
    stdlib = sys.stdlib_module_names
    for node in ast.walk(ast.parse(source)):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""] if node.level == 0 else [f"<relative {node.module}>"]
        for name in names:
            top = name.split(".", 1)[0]
            if name.startswith("ai_player.host") or name.startswith("ai_player.gates"):
                found.append(name)
            elif top == "ai_player" or top == "__future__" or top in stdlib:
                continue
            else:
                found.append(name)
    return found


def tile(x: int, y: int, px: int, py: int) -> Tile:
    return Tile(x=x, y=y, dx=x - px, dy=y - py, metatile=1, behavior=0, behavior_name="NORMAL", collision=0,
                elevation=3, blocked=False, water=False, encounter=None, tall_grass=False, ledge=None, door=False,
                warp=False, half_visible=abs(y - py) == 5)


def make_view(px: int, py: int) -> View:
    rows = tuple(tuple(tile(px + dx, py + dy, px, py) for dx in range(-7, 8)) for dy in range(-5, 6))
    return View(left=7, right=7, up=5, down=5, rows=rows, objects=(), cropped=True)


def mon(species: str, dex: int, level: int, slot: int = 0, ot_id: int = 0xABCD1234, pid: int = 1) -> MonSummary:
    return MonSummary(slot=slot, species=species, dex=dex, level=level, hp=20, max_hp=20, status="ok", types=("Water",),
                      moves=(), pid=pid, ot_id=ot_id, is_egg=False)


def observe(frame: int, *, where=("ROUTE 101", 0, 16), xy=(5, 5), party=(), owned=(), money=3000, in_battle=False,
            battle: BattleView | None = None, outcome: int = 0, badges=(), trainer_id=0xABCD1234) -> Observation:
    name, group, number = where
    player = PlayerState(map_group=group, map_number=number, map_name=name, map_const=None, x=xy[0], y=xy[1],
                         facing="down", movement="walking", elevation=3, avatar_flags=1, trainer_id=trainer_id)
    screen = ScreenState(game_state="BATTLE" if in_battle else "OVERWORLD", screen="battle" if in_battle else "overworld",
                         menu=None, text_box_open=False, waits_for_button=False, in_battle=in_battle)
    progress = Progress(money=money, badges=tuple(badges), dex_owned=len(owned), dex_seen=len(owned),
                        owned_dex=tuple(owned), flags=())
    return Observation(frame=frame, screen=screen, player=player, view=None if in_battle else make_view(*xy),
                       party=tuple(party), bag=BagSummary(balls=(("Poke Ball", 5),), healing=(), ball_total=5),
                       progress=progress, battle=battle, last_battle_outcome=outcome, problems=(), cost_ms=1.0)


def battle_view(kind: str, foe: str, dex: int, level: int, trainer: int | None = None) -> BattleView:
    foe_mon = BattleMon(species=foe, dex=dex, level=level, hp=10, max_hp=10, status="ok", types=("Bug",), moves=())
    own = BattleMon(species="Mudkip", dex=258, level=8, hp=20, max_hp=20, status="ok", types=("Water",), moves=())
    return BattleView(kind=kind, double=False, type_flags=8 if kind == "trainer" else 4, opponent_trainer_id=trainer,
                      own=(own,), foe=(foe_mon,))


def scorer_lines(observations: list[Observation]) -> list[str]:
    scorer = ScorerLines()
    lines: list[str] = []
    for observation in observations:
        lines += scorer.update(observation)
    return lines


def parse(lines: list[str]) -> dict:
    import scoring

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "ai_player.log"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return scoring.parse_log(path)


# ------------------------------------------------------------------------------------------- tests
class FrameworkFreeTests(unittest.TestCase):
    def test_brain_side_files_import_no_framework_and_no_host(self) -> None:
        for relative in FRAMEWORK_FREE:
            source = (PACKAGE / relative).read_text(encoding="utf-8")
            self.assertEqual(foreign_imports(source), [], relative)

    def test_fault_a_planted_framework_or_host_import_is_caught(self) -> None:
        planted = "from modules.map import get_map_objects\nfrom ai_player.host.eyes import FrameworkEyes\nimport json\n"
        self.assertEqual(foreign_imports(planted), ["modules.map", "ai_player.host.eyes"])


class GeometryTests(unittest.TestCase):
    def test_the_window_is_15_by_11(self) -> None:
        self.assertEqual((VIEW_HALF_WIDTH, VIEW_UP, VIEW_DOWN), (7, 5, 5))
        offsets = view_offsets()
        self.assertEqual(len(offsets), 15 * 11)
        self.assertEqual((offsets[0], offsets[-1]), ((-7, -5), (7, 5)))

    def test_edges(self) -> None:
        self.assertTrue(in_view(10, 10, 17, 10))
        self.assertFalse(in_view(10, 10, 18, 10))
        self.assertTrue(in_view(10, 10, 3, 10))
        self.assertFalse(in_view(10, 10, 2, 10))
        self.assertTrue(in_view(10, 10, 10, 15))
        self.assertFalse(in_view(10, 10, 10, 16))
        self.assertTrue(in_view(10, 10, 10, 5))
        self.assertFalse(in_view(10, 10, 10, 4))


class BehaviorTableTests(unittest.TestCase):
    def test_decomp_values(self) -> None:
        self.assertEqual(len(BEHAVIOR_NAMES), 240)  # MB_NORMAL .. MB_UNUSED_EF
        expected = {"TALL_GRASS": 0x02, "LONG_GRASS": 0x03, "DEEP_WATER": 0x12, "JUMP_EAST": 0x38, "JUMP_SOUTH": 0x3B,
                    "NON_ANIMATED_DOOR": 0x60, "ANIMATED_DOOR": 0x69, "WATER_DOOR": 0x6C, "PETALBURG_GYM_DOOR": 0x8D,
                    "SKY_PILLAR_CLOSED_DOOR": 0xEA, "UNUSED_EF": 0xEF}
        self.assertEqual({name: BEHAVIOR[name] for name in expected}, expected)

    def test_agrees_with_the_frameworks_independent_names(self) -> None:
        from modules.context import context
        from modules.game import set_rom
        from modules.map import _get_tile_type_name
        from modules.profiles import load_profile_by_name

        profile = load_profile_by_name("ai-step0-fixture")
        context.profile = profile
        set_rom(profile.rom)

        def theirs(value: int) -> str:
            return _get_tile_type_name(value).upper().replace(" ", "_").replace("-", "_")

        classified = set(TALL_GRASS_BEHAVIORS) | {v for v, d in LEDGE_DIRECTIONS.items() if d in ("east", "west", "north", "south")}
        classified |= set(DOOR_BEHAVIORS) | {BEHAVIOR[n] for n in ("POND_WATER", "DEEP_WATER", "OCEAN_WATER", "WATERFALL")}
        # The one wording difference among the classified values, measured on the first run: the framework
        # names 0x69 "Door Warp", the decomp MB_ANIMATED_DOOR. Same value, a door either way.
        aliases = {BEHAVIOR["ANIMATED_DOOR"]: "DOOR_WARP"}
        disagree = [(hex(v), BEHAVIOR_NAMES[v], theirs(v)) for v in sorted(classified)
                    if theirs(v) != BEHAVIOR_NAMES[v] and theirs(v) != aliases.get(v)]
        self.assertEqual(disagree, [])
        # The WHOLE table's positions: every value the framework knows no Emerald name for ('???') must be
        # one of the decomp's UNUSED_xx. A table shifted by one would put '???' on a real behaviour.
        # (Measured on the first run: 123 of 240 names equal verbatim; 40 differ in wording only, e.g.
        # MT_PYRE_HOLE vs 'Mount Pyre Hole'; 18 UNUSED slots carry FRLG names in the framework's merged
        # table; 59 are '???'.)
        unknown = [v for v in range(240) if _get_tile_type_name(v) == "???"]
        misplaced = [(hex(v), BEHAVIOR_NAMES[v]) for v in unknown if not BEHAVIOR_NAMES[v].startswith("UNUSED")]
        agreeing = sum(1 for v in range(240) if theirs(v) == BEHAVIOR_NAMES[v])
        print(f"\n  behaviour names: {agreeing} of 240 equal to the framework's table verbatim; {len(unknown)} the "
              f"framework calls '???', all of them UNUSED in the decomp: {not misplaced}")
        self.assertEqual(misplaced, [])
        self.assertGreaterEqual(len(unknown), 50)


def encode_mon(personality: int, ot_id: int, species: int, moves: tuple[int, int, int, int], pp: tuple[int, int, int, int],
               level: int, table) -> bytes:
    """Build an ENCRYPTED `struct Pokemon` the way the game does, placing the substructures by `table`
    (the FRAMEWORK's table in the tests, so the decoder's own table is checked against an independent one)."""
    growth = species.to_bytes(2, "little") + (0).to_bytes(2, "little") + (1000).to_bytes(4, "little") + bytes([0, 70]) + bytes(2)
    attacks = b"".join(m.to_bytes(2, "little") for m in moves) + bytes(pp)
    evs = bytes(12)
    misc = bytes(4) + (31).to_bytes(4, "little") + bytes(4)
    plain_blocks = [growth, attacks, evs, misc]
    order = table[personality % 24]
    placed = [b""] * 4
    for substruct, position in enumerate(order):
        placed[position] = plain_blocks[substruct]
    plain = b"".join(placed)
    checksum = sum(int.from_bytes(plain[i:i + 2], "little") for i in range(0, 48, 2)) & 0xFFFF
    key = personality ^ ot_id
    secure = b"".join((int.from_bytes(plain[i:i + 4], "little") ^ key).to_bytes(4, "little") for i in range(0, 48, 4))
    head = personality.to_bytes(4, "little") + ot_id.to_bytes(4, "little") + bytes(10) + bytes([2, 0x02]) + bytes(8)
    head += checksum.to_bytes(2, "little") + bytes(2)
    tail = bytes(4) + bytes([level, 0]) + (20).to_bytes(2, "little") + (25).to_bytes(2, "little") + bytes(10)
    data = head + secure + tail
    assert len(data) == PARTY_MON_SIZE
    return data


class PartyDecoderTests(unittest.TestCase):
    def _round_trip(self) -> list[str]:
        from modules.pokemon import POKEMON_DATA_SUBSTRUCTS_ORDER, Pokemon

        failures = []
        for residue in range(24):
            personality = 0x1234500 + residue  # 0x1234500 % 24 == 0
            data = encode_mon(personality, 0xCAFEBABE, 280, (33, 45, 0, 0), (35, 40, 0, 0), 9, POKEMON_DATA_SUBSTRUCTS_ORDER)
            mine = decode_party_mon(data)
            framework = Pokemon(data)
            if isinstance(mine, str):
                failures.append(f"residue {residue}: {mine}")
                continue
            got = (mine.species_id, mine.moves, mine.pp, mine.level, mine.hp, mine.max_hp, mine.is_egg)
            want = (280, (33, 45, 0, 0), (35, 40, 0, 0), 9, 20, 25, False)
            if got != want or framework.species.index != mine.species_id:
                failures.append(f"residue {residue}: got {got}, framework species {framework.species.index}")
        return failures

    def test_all_24_orders_against_the_frameworks_table_and_decoder(self) -> None:
        self.assertEqual(0x1234500 % 24, 0)
        self.assertEqual(self._round_trip(), [])

    def test_a_torn_slot_is_refused(self) -> None:
        from modules.pokemon import POKEMON_DATA_SUBSTRUCTS_ORDER

        data = bytearray(encode_mon(7, 99, 280, (33, 0, 0, 0), (35, 0, 0, 0), 5, POKEMON_DATA_SUBSTRUCTS_ORDER))
        data[40] ^= 0xFF  # a byte of the encrypted area changes, as if the game were writing it
        self.assertIsInstance(decode_party_mon(bytes(data)), str)

    def test_fault_one_swapped_table_row_is_caught(self) -> None:
        mutated = list(party_module.SUBSTRUCT_POSITIONS)
        mutated[13] = (1, 2, 0, 3)  # row 13 is (1, 3, 0, 2)
        with mock.patch.object(party_module, "SUBSTRUCT_POSITIONS", tuple(mutated)):
            failures = self._round_trip()
        self.assertTrue(any(f.startswith("residue 13:") for f in failures), failures)


class FlagTests(unittest.TestCase):
    TABLE = BUILD_ROOT / "modules" / "data" / "event_flags" / "emerald.txt"

    def known(self) -> set[str]:
        return {line.split()[1] for line in self.TABLE.read_text(encoding="utf-8").splitlines() if len(line.split()) >= 2}

    def test_every_flag_the_eyes_read_exists(self) -> None:
        known = self.known()
        names = [name for name, _ in STORY_FLAGS] + list(BADGE_FLAGS)
        self.assertEqual([name for name in names if name not in known], [])
        self.assertEqual(len(names), 18)

    def test_fault_a_phantom_name_is_caught(self) -> None:
        known = self.known()
        self.assertNotIn("FLAG_BADGE01_GET", known)  # the decomp's spelling: the table has no FLAG_ prefix
        self.assertNotIn("DEFEATED_RIVAL_ROUTE_103", known)

    def numbers(self) -> dict[str, int]:
        return {line.split()[1]: int(line.split()[0]) for line in self.TABLE.read_text(encoding="utf-8").splitlines()
                if len(line.split()) >= 2 and line.split()[0].isdigit()}

    def test_each_flag_id_agrees_with_the_decomp(self) -> None:
        """The framework's table (what `get_event_flag` reads for the eyes) and the decomp's values (what
        `gates/probe_eyes.py` reads its ground-truth bits at) name the SAME bit for every flag."""
        from ai_player.gates.probe_eyes import DECOMP_FLAG_IDS

        names = sorted({name for name, _ in STORY_FLAGS} | set(BADGE_FLAGS))  # BADGE01_GET is in both lists
        numbers = self.numbers()
        self.assertEqual(names, sorted(DECOMP_FLAG_IDS))
        self.assertEqual({n: numbers[n] for n in names}, {n: DECOMP_FLAG_IDS[n] for n in names})

    def test_fault_one_wrong_id_is_caught(self) -> None:
        from ai_player.gates.probe_eyes import DECOMP_FLAG_IDS

        numbers = self.numbers()
        wrong = dict(DECOMP_FLAG_IDS, HIDE_PETALBURG_CITY_WALLYS_MOM=0x87)  # the id of the flag it replaced
        self.assertNotEqual({n: numbers[n] for n in wrong}, wrong)

    def test_the_wally_tutorial_flag_is_not_the_dads_thanks(self) -> None:
        """2026-10-07: the Ch2 entry was THANKED_FOR_PLAYING_WITH_WALLY, which only Wally's DAD sets
        (`data/maps/PetalburgCity_WallysHouse/scripts.inc`, an optional chat), so it read False on every
        fixture; the tutorial's scene sets HIDE_PETALBURG_CITY_WALLYS_MOM (`PetalburgCity_Gym/scripts.inc`
        BeginWallyTutorial). Measured: every fixture past Petalburg has it set (`live_step1.py` STORY FLAGS)."""
        names = [name for name, _ in STORY_FLAGS]
        self.assertNotIn("THANKED_FOR_PLAYING_WITH_WALLY", names)
        self.assertIn("HIDE_PETALBURG_CITY_WALLYS_MOM", names)


class ProbeDecoderTests(unittest.TestCase):
    """The probe's own decoders, which the live arms' ground truth stands on."""

    def test_own_charmap(self) -> None:
        from ai_player.gates.probe_eyes import own_text

        self.assertEqual(own_text(bytes.fromhex("CAC9C51B00BCBBC6C6FF00")), "POKé BALL")
        self.assertEqual(own_text(bytes.fromhex("CCC9CFCEBF00A2A2A7FF")), "ROUTE 116")

    def test_item_names_compare_across_tables(self) -> None:
        from ai_player.gates.live_step1 import item_key

        self.assertEqual(item_key("POKé BALL"), item_key("Poké Ball"))
        self.assertEqual(item_key("KING’S ROCK"), item_key("King's Rock"))
        self.assertNotEqual(item_key("SUPER POTION"), item_key("Potion"))


class ScreenTests(unittest.TestCase):
    def test_screens(self) -> None:
        self.assertEqual(classify_screen("PARTY_MENU", True, 0, ()), ("menu", "party"))
        self.assertEqual(classify_screen("BATTLE", True, 0, ()), ("battle", None))
        self.assertEqual(classify_screen("OVERWORLD", False, 2, {"Task_DrawFieldMessage"}), ("text", None))
        self.assertEqual(classify_screen("OVERWORLD", False, 0, {"Task_ShowStartMenu"}), ("menu", "start_menu"))
        self.assertEqual(classify_screen("OVERWORLD", False, 2, {"Task_HandleYesNoInput"}), ("menu", "yes_no"))
        self.assertEqual(classify_screen("OVERWORLD", False, 0, {"Task_WeatherMain"}), ("overworld", None))
        self.assertEqual(classify_screen("CHANGE_MAP", False, 0, ()), ("transition", None))
        self.assertEqual(classify_screen("TITLE_SCREEN", False, 0, ()), ("title", None))


class WaitRuleTests(unittest.TestCase):
    """`eyes/view.py` text_printer_wait against the decomp (`include/text.h`, `src/text.c` RenderText)."""

    #: (index, active, state) for all 32 printers, idle.
    IDLE = [(i, 0, 0) for i in range(32)]

    def printers(self, **active: int) -> list[tuple[int, int, int]]:
        """`printer6=1` makes printer 6 active in state 1."""
        rows = list(self.IDLE)
        for key, state in active.items():
            index = int(key.removeprefix("printer"))
            rows[index] = (index, 1, state)
        return rows

    def test_the_decomps_states(self) -> None:
        self.assertEqual(RENDER_STATE_NAMES[:4], ("HANDLE_CHAR", "WAIT", "CLEAR", "SCROLL_START"))
        self.assertEqual(TEXT_PRINTER_WAIT_STATES, frozenset({1, 2, 3}))
        self.assertEqual(TEXT_PRINTER_COUNT, 32)  # WINDOWS_MAX: RunTextPrinters runs them all
        self.assertEqual(TEXT_FLAG_AUTO_SCROLL, 0x04)  # bit 2 (live_step1 measures the order in a battle)

    def test_each_wait_state_waits_and_says_which(self) -> None:
        self.assertEqual(text_printer_wait(self.printers(printer0=1), 0), "text printer 0 WAIT")  # {PAUSE_UNTIL_PRESS}
        self.assertEqual(text_printer_wait(self.printers(printer0=2), 0), "text printer 0 CLEAR")  # \p
        self.assertEqual(text_printer_wait(self.printers(printer0=3), 0), "text printer 0 SCROLL_START")  # \l
        self.assertEqual(text_printer_wait(self.printers(printer6=1), 0x01), "text printer 6 WAIT")  # the party menu's

    def test_printing_scrolling_pausing_and_idle_do_not_wait(self) -> None:
        for state in (0, 4, 5, 6):  # HANDLE_CHAR, SCROLL, WAIT_SE, PAUSE: each moves on by itself
            self.assertIsNone(text_printer_wait(self.printers(printer0=state), 0), state)
        self.assertIsNone(text_printer_wait([(0, 0, 2)] + self.IDLE[1:], 0))  # an INACTIVE printer's leftover state
        self.assertIsNone(text_printer_wait(self.IDLE, 0))

    def test_auto_scroll_waits_for_nothing(self) -> None:
        self.assertIsNone(text_printer_wait(self.printers(printer0=2), TEXT_FLAG_AUTO_SCROLL | 0x03))
        self.assertEqual(text_printer_wait(self.printers(printer0=2), 0x03), "text printer 0 CLEAR")  # battle flags, no autoScroll

    def test_fault_the_pre_fix_rule_misses_the_defeat_text(self) -> None:
        with mock.patch.object(view_module, "TEXT_PRINTER_WAIT_STATES", frozenset({2, 3})):
            self.assertIsNone(text_printer_wait(self.printers(printer0=1), 0))  # the round-1 defect

    def test_fault_printer_0_only_misses_the_party_menu(self) -> None:
        only_zero = [row for row in self.printers(printer6=1) if row[0] == 0]  # what reading one printer sees
        self.assertIsNone(text_printer_wait(only_zero, 0))
        self.assertIsNotNone(text_printer_wait(self.printers(printer6=1), 0))


class ScorerTests(unittest.TestCase):
    def synthetic_run(self) -> list[Observation]:
        """A run from a save with a party: Route 101, a wild Wurmple caught, Oldale, Roxanne beaten."""
        mudkip = mon("Mudkip", 258, 8)
        wurmple = mon("Wurmple", 265, 3, slot=1, ot_id=0xABCD1234, pid=2)
        return [
            observe(100, party=[mudkip], owned=(258,)),
            observe(160, party=[mudkip], owned=(258,), in_battle=True, battle=battle_view("wild", "Wurmple", 265, 3)),
            observe(220, party=[mudkip], owned=(258,), in_battle=True, battle=battle_view("wild", "Wurmple", 265, 3)),
            observe(280, party=[mudkip, wurmple], owned=(258, 265), outcome=7),
            observe(340, where=("OLDALE TOWN", 0, 10), xy=(5, 19), party=[mudkip, wurmple], owned=(258, 265)),
            observe(400, where=("RUSTBORO CITY", 11, 3), xy=(5, 5), party=[mudkip, wurmple], owned=(258, 265), money=3000,
                    in_battle=True, battle=battle_view("trainer", "Geodude", 74, 12, trainer=265)),
            observe(460, where=("RUSTBORO CITY", 11, 3), xy=(5, 5), party=[mudkip, wurmple], owned=(258, 265), money=4200,
                    outcome=1, badges=("BADGE01_GET",)),
        ]

    def test_parse_log_reads_the_ai_lines_like_a_bot_run(self) -> None:
        lines = scorer_lines(self.synthetic_run())
        record = parse(lines)
        print("\n  synthetic AI log:\n    " + "\n    ".join(lines))
        print("  scoring.parse_log -> " + json.dumps({k: record[k] for k in (
            "starter", "maps_visited", "catches", "species_caught", "dex_owned", "badges", "wins", "money_last",
            "frames", "progress", "score", "human_score")}))
        self.assertEqual(record["starter"], "Mudkip")
        self.assertEqual(record["maps_visited"], 3)  # ROUTE 101, OLDALE TOWN, RUSTBORO CITY
        self.assertEqual((record["catches"], record["species_caught"]), (1, ["Wurmple"]))
        self.assertEqual(record["dex_owned"], 2)
        self.assertEqual((record["badges"], record["wins"]), (["ROXANNE"], {"ROXANNE": 1}))
        self.assertEqual(record["money_last"], 4200)
        self.assertEqual(record["frames"], 460)
        self.assertEqual(record["progress"], 1)

    def test_each_line_matches_the_scorers_own_regex(self) -> None:
        import scoring

        lines = scorer_lines(self.synthetic_run())
        wanted = {
            "[AI-STARTER]": scoring.STARTER_RE, "[MAP]": scoring.MAP_RE, "[DEX] owned": scoring.DEX_RE,
            "[CATCH] end": scoring.CATCH_OK_RE, "[TRAINER] end": scoring.TRAINER_END_RE,
        }
        for tag, regex in wanted.items():
            tagged = [line for line in lines if tag in line]
            self.assertTrue(tagged, f"no {tag} line")
            for line in tagged:
                self.assertTrue(regex.search(line), f"{regex.pattern!r} does not match {line!r}")
                self.assertTrue(scoring.FRAME_RE.match(line), f"no frame prefix: {line!r}")
        self.assertTrue(scoring.MONEY_RE.search(next(line for line in lines if "[TRAINER] end" in line)))

    def test_heartbeats_give_the_scorer_the_end_of_the_run(self) -> None:
        import scoring

        mudkip = mon("Mudkip", 258, 8)
        scorer = ScorerLines()
        lines: list[str] = []
        for frame in range(1000, 1000 + 4000, 600):  # 1000 .. 4600: one periodic heartbeat at >= 3600 frames
            lines += scorer.update(observe(frame, party=[mudkip], xy=(frame % 7, 3)))
        last = observe(4700, party=[mudkip, mon("Wurmple", 265, 3, slot=1)], where=("OLDALE TOWN", 0, 10), xy=(6, 9))
        lines += scorer.update(last)
        lines += scorer.final(last)
        beats = [line for line in lines if "[hb]" in line]
        self.assertEqual(len(beats), 2, beats)
        self.assertTrue(all(scoring.HB_RE.search(line) for line in beats), beats)
        self.assertTrue(beats[-1].endswith("end=1"))
        record = parse(lines)
        self.assertEqual((record["frames"], record["end_map"], record["end_pos"], record["end_party"]),
                         (4700, "OLDALE TOWN", [6, 9], "['Mudkip:L8', 'Wurmple:L3']"))
        self.assertEqual(scoring.party_levels(record["end_party"]), [8, 3])

    def test_new_game_starter_is_observed(self) -> None:
        lines = scorer_lines([observe(10, where=("LITTLEROOT TOWN", 0, 9)), observe(70, where=("ROUTE 101", 0, 16)),
                              observe(130, where=("ROUTE 101", 0, 16), party=[mon("Torchic", 255, 5)])])
        self.assertIn("(observed: the party went from 0 to 1", lines[0])
        record = parse(lines)
        self.assertEqual((record["starter"], record["maps_visited"]), ("Torchic", 1))  # maps before the starter: ignored, as for the bot

    def test_a_traded_starter_family_mon_is_not_the_starter(self) -> None:
        lines = scorer_lines([observe(10, party=[mon("Marshtomp", 259, 20, ot_id=0x11112222)])])
        self.assertIn("choosing Unknown!", lines[0])

    def test_fault_events_before_the_starter_line_are_ignored_by_the_scorer(self) -> None:
        lines = scorer_lines(self.synthetic_run())
        starter = [line for line in lines if "[AI-STARTER]" in line]
        moved = [line for line in lines if "[AI-STARTER]" not in line] + starter  # the starter LAST
        record = parse(moved)
        self.assertEqual((record["catches"], record["badges"], record["maps_visited"]), (0, [], 0))

    def test_fault_a_map_line_without_its_numbers_is_not_counted(self) -> None:
        good = parse(["f1 [AI-STARTER] Story: choosing Mudkip! (x)", "f2 [MAP] None -> ROUTE 101(0,16) pos=(1, 1)"])
        broken = parse(["f1 [AI-STARTER] Story: choosing Mudkip! (x)", "f2 [MAP] None -> ROUTE 101 pos=(1, 1)"])
        self.assertEqual((good["maps_visited"], broken["maps_visited"]), (1, 0))


class ActionLogTests(unittest.TestCase):
    def test_one_json_line_per_record(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            sink = RecordFile(Path(folder))
            log = ActionLog(sink)
            observation = observe(500, party=[mon("Mudkip", 258, 8)])
            log.record(observation, decision="observe", action="none", reason="test", full=True)
            log.record(None, decision="give-up", action="none", reason="done", frame=560)
            lines = sink.path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        first, second = json.loads(lines[0]), json.loads(lines[1])
        self.assertEqual([first[k] for k in ("frame", "decision", "action", "reason")], [500, "observe", "none", "test"])
        self.assertTrue(first["digest"].startswith("f500 overworld ROUTE 101(0,16)"))
        self.assertEqual(len(first["observation"]["view"]["tiles"]), 165)
        self.assertEqual(len(first["observation"]["view"]["ascii"]), 11)
        self.assertEqual((second["frame"], second["digest"]), (560, None))

    def test_a_record_with_a_newline_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                RecordFile(Path(folder)).append("two\nlines")


if __name__ == "__main__":
    unittest.main(verbosity=2)
