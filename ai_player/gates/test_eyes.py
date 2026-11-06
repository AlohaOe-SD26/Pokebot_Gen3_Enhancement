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

STEP 1.1 (the step-1 adversarial review's findings; each test FAILS when its fix is reverted, which
`gates/revert_step11.py` proves on copies of the package, one revert per copy):
  CatchTests           (1) Wally's tutorial ends `Caught` with no new Pokemon of the player's: no [CATCH];
                       a real catch is logged with the NEW PID and where THAT PID is (party or box), also
                       when the battle's first look could not read the party (5: dest by PID, not count).
  BattleLineTests      (2) the foe is refreshed on every in-battle look (the first look can hold the
                       previous battle's foe); a battle ends only on a result (`gBattleOutcome` != 0), so
                       a look out of the battle before its result writes no `res=InProgress`.
  PerceptionTests      (3) the foe's HP is the 48-pixel bar (the decomp's GetScaledHPFraction), its moves
                       only those used (PP below max), no PP; every person is an "npc"; the OT id and the
                       player's id are the VISIBLE 16 bits (the host's own `_mon` and `_battle_mon`).
  SettlingTests        (4) the position is None while the object's tile and the save block's differ (a
                       warp, measured: 6 frames); the [MAP] line waits for the settled position.
  PartyNoneTests       (5) None (not read) is not () (no Pokemon): the starter is not "observed" after an
                       unread party; the closing heartbeat comes from the last complete look; and (step 2.1,
                       the step-2 verifier's weak proof) the HOST's own `_party` makes the whole party None
                       when one slot is torn (revert R5c).
  ScriptWaitTests      (6) the script's `waitbuttonpress` waits only while the context is not shut down
                       (a finished script leaves WaitForAorBPress behind: measured on dewford.ss1).
"""

from __future__ import annotations

import ast
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "ai_player"
#: Where the framework and the learner's scorer live. A REVERT copy of the package (`gates/revert_step11.py`)
#: runs this file from a temporary folder and points here at the real repo.
SUPPORT = Path(os.environ.get("AI_PLAYER_TEST_SUPPORT_ROOT") or REPO)
BUILD_ROOT = SUPPORT / "sandbox-pokebot"
for entry in (str(REPO), str(BUILD_ROOT), str(SUPPORT / "ai-agent")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from ai_player.eyes import party as party_module  # noqa: E402
from ai_player.eyes.observation import (  # noqa: E402
    BagSummary, BattleMon, BattleView, MonSummary, Observation, PlayerState, Progress, ScreenState, StoredMon, Tile, View,
)
from ai_player.eyes.party import PARTY_MON_SIZE, decode_party_mon  # noqa: E402
from ai_player.eyes import view as view_module  # noqa: E402
from ai_player.eyes.view import (  # noqa: E402
    BADGE_FLAGS, BATTLE_TYPE_WALLY_TUTORIAL, BEHAVIOR, BEHAVIOR_NAMES, DOOR_BEHAVIORS, GFX_KINDS, HP_BAR_PIXELS,
    LEDGE_DIRECTIONS, RENDER_STATE_NAMES, STORY_FLAGS, TALL_GRASS_BEHAVIORS, TEXT_FLAG_AUTO_SCROLL, TEXT_PRINTER_COUNT,
    TEXT_PRINTER_WAIT_STATES, VIEW_DOWN, VIEW_HALF_WIDTH, VIEW_UP, classify_screen, foe_move_seen, hp_bar_pixels, in_view,
    object_kind, script_waits_for_button, settled_position, text_printer_wait, view_offsets, visible_id,
)
from ai_player.memory_log import ActionLog, ScorerLines, owned_pids  # noqa: E402
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


#: The player's VISIBLE trainer id in the synthetic runs (the eyes report the visible 16 bits only).
ME = 0x1234


def mon(species: str, dex: int, level: int, slot: int = 0, ot_id: int = ME, pid: int = 1) -> MonSummary:
    return MonSummary(slot=slot, species=species, dex=dex, level=level, hp=20, max_hp=20, status="ok", types=("Water",),
                      moves=(), pid=pid, ot_id=ot_id, is_egg=False)


def boxed(pid: int, box: int = 0, slot: int = 0, ot_id: int = ME) -> StoredMon:
    return StoredMon(box=box, slot=slot, pid=pid, ot_id=ot_id, is_egg=False)


def observe(frame: int, *, where=("ROUTE 101", 0, 16), xy=(5, 5), party=(), owned=(), money=3000, in_battle=False,
            battle: BattleView | None = None, outcome: int = 0, badges=(), trainer_id=ME, storage=(),
            settling: bool = False, game_state: str | None = None) -> Observation:
    """A synthetic look. `party=None` / `storage=None` = not read; `game_state` overrides the screen (e.g.
    NAMING_SCREEN, the nickname screen a catch opens outside the battle screen)."""
    name, group, number = where
    player = PlayerState(map_group=group, map_number=number, map_name=name, map_const=None,
                         x=None if settling else xy[0], y=None if settling else xy[1], facing="down", movement="walking",
                         elevation=3, avatar_flags=1, trainer_id=trainer_id, settling=settling)
    state = game_state or ("BATTLE" if in_battle else "OVERWORLD")
    kind = {"BATTLE": "battle", "OVERWORLD": "overworld"}.get(state, "menu")
    screen = ScreenState(game_state=state, screen=kind, menu=None, text_box_open=False, waits_for_button=False,
                         in_battle=in_battle)
    progress = Progress(money=money, badges=tuple(badges), dex_owned=len(owned), dex_seen=len(owned),
                        owned_dex=tuple(owned), flags=())
    return Observation(frame=frame, screen=screen, player=player,
                       view=None if (in_battle or settling or state != "OVERWORLD") else make_view(*xy),
                       party=None if party is None else tuple(party),
                       bag=BagSummary(balls=(("Poke Ball", 5),), healing=(), ball_total=5),
                       progress=progress, battle=battle, last_battle_outcome=outcome, problems=(), cost_ms=1.0,
                       storage=None if storage is None else tuple(storage))


def battle_view(kind: str, foe: str, dex: int, level: int, trainer: int | None = None, flags: int | None = None) -> BattleView:
    foe_mon = BattleMon(species=foe, dex=dex, level=level, hp=None, max_hp=None, hp_bar=HP_BAR_PIXELS, status="ok",
                        types=("Bug",), moves=())
    own = BattleMon(species="Mudkip", dex=258, level=8, hp=20, max_hp=20, hp_bar=HP_BAR_PIXELS, status="ok",
                    types=("Water",), moves=())
    type_flags = flags if flags is not None else (8 if kind == "trainer" else 4)
    return BattleView(kind=kind, double=False, type_flags=type_flags, opponent_trainer_id=trainer, own=(own,), foe=(foe_mon,))


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
            got = (mine.species_id, mine.moves, mine.pp, mine.level, mine.hp, mine.max_hp, mine.is_egg, mine.experience)
            want = (280, (33, 45, 0, 0), (35, 40, 0, 0), 9, 20, 25, False, 1000)
            # step 3: the experience (growth @4, `encode_mon` writes 1000) against the framework's own `total_exp`
            if got != want or framework.species.index != mine.species_id or framework.total_exp != mine.experience:
                failures.append(f"residue {residue}: got {got}, framework species {framework.species.index} "
                                f"experience {framework.total_exp}")
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
        wurmple = mon("Wurmple", 265, 3, slot=1, ot_id=ME, pid=2)
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
        lines = scorer_lines([observe(10, party=[mon("Marshtomp", 259, 20, ot_id=0x2222)])])
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


# ------------------------------------------------------------------------------------------- step 1.1
def lines_of(observations: list[Observation]) -> list[str]:
    """The scorer lines AFTER the starter line (each test's subject)."""
    return [line for line in scorer_lines(observations) if "[AI-STARTER]" not in line]


def framework_rom() -> None:
    """The framework's ROM and data tables, for the tests that run the host's own conversions."""
    from modules.context import context
    from modules.game import set_rom
    from modules.profiles import load_profile_by_name

    if getattr(context, "rom", None) is None:
        profile = load_profile_by_name("ai-step0-fixture")
        context.profile = profile
        set_rom(profile.rom)


class CatchTests(unittest.TestCase):
    """Finding 1 (Wally's tutorial is not a player catch) and finding 5's `dest` by PID."""

    MUDKIP = mon("Mudkip", 258, 8, pid=0x550A9BE6)
    DEFAULT = object()  # "the Mudkip party" (None means NOT READ, so it cannot be the default's marker)

    def battle(self, frame: int, foe=("Wurmple", 265, 3), flags: int | None = None, party=DEFAULT, storage=()) -> Observation:
        return observe(frame, party=[self.MUDKIP] if party is self.DEFAULT else party, owned=(258,), in_battle=True,
                       battle=battle_view("wild", *foe, flags=flags), storage=storage)

    def test_wally_tutorial_is_not_a_player_catch(self) -> None:
        """`BATTLE_TYPE_WALLY_TUTORIAL`: `BattleScript_WallyBallThrow` sets B_OUTCOME_CAUGHT with no
        `givecaughtmon` (`data/battle_scripts_2.s`), so the party and the boxes are unchanged."""
        tutorial = BATTLE_TYPE_WALLY_TUTORIAL | 4
        run = [observe(100, party=[self.MUDKIP], owned=(258,)),
               self.battle(160, foe=("Ralts", 280, 5), flags=tutorial), self.battle(220, foe=("Ralts", 280, 5), flags=tutorial),
               observe(280, party=[self.MUDKIP], owned=(258,), outcome=7)]
        lines = lines_of(run)
        record = parse(scorer_lines(run))
        print(f"\n  Wally's tutorial: {lines}")
        self.assertFalse([line for line in lines if "[CATCH]" in line], lines)
        self.assertEqual(record["catches"], 0)
        self.assertTrue(any("res=Caught" in line and "tutorial=wally" in line and "player_catch=none" in line for line in lines), lines)

    def test_a_catch_into_the_party_names_the_new_pid(self) -> None:
        wurmple = mon("Wurmple", 265, 3, slot=1, pid=0x7D6D2751)
        run = [observe(100, party=[self.MUDKIP], owned=(258,)), self.battle(160), self.battle(220),
               observe(280, party=[self.MUDKIP, wurmple], owned=(258, 265), outcome=7)]
        catch = [line for line in lines_of(run) if "[CATCH]" in line]
        self.assertEqual(len(catch), 1, catch)
        self.assertIn("sp=Wurmple#265", catch[0])
        self.assertIn("dest=party pid=7D6D2751", catch[0])
        self.assertEqual(parse(scorer_lines(run))["catches"], 1)

    def test_a_catch_sent_to_a_box_is_found_there_by_pid(self) -> None:
        full = [mon(f"Mon{i}", 258, 8, slot=i, pid=0x100 + i) for i in range(6)]
        run = [observe(100, party=full, owned=(258,), storage=[boxed(0x900)]),
               self.battle(160, party=full, storage=[boxed(0x900)]),
               observe(280, party=full, owned=(258, 265), outcome=7, storage=[boxed(0x900), boxed(0x7D6D2751, slot=1)])]
        catch = [line for line in lines_of(run) if "[CATCH]" in line]
        self.assertEqual(len(catch), 1, catch)
        self.assertIn("dest=box pid=7D6D2751", catch[0])

    def test_dest_is_by_pid_even_when_the_first_look_could_not_read_the_party(self) -> None:
        """Finding 5: the battle's FIRST look had a torn party (None). The party COUNT (None -> 6) would say
        "party"; the new PID is in a BOX. (Until step 1.1 an unread party was () and dest came from the count.)"""
        full = [mon(f"Mon{i}", 258, 8, slot=i, pid=0x100 + i) for i in range(6)]
        run = [observe(100, party=full, owned=(258,)),
               self.battle(160, party=None),  # the battle's first look: party not read
               self.battle(220, party=full),  # the next look reads it: the baseline of who is the player's
               observe(280, party=full, owned=(258, 265), outcome=7, storage=[boxed(0x7D6D2751)])]
        catch = [line for line in lines_of(run) if "[CATCH]" in line]
        self.assertEqual(len(catch), 1, catch)
        self.assertIn("dest=box pid=7D6D2751", catch[0])

    def test_someone_elses_pokemon_is_not_the_players_catch(self) -> None:
        """Ownership is the VISIBLE id: a new Pokemon whose OT is not the player's is no catch of the player's."""
        run = [observe(100, party=[self.MUDKIP], owned=(258,)), self.battle(160),
               observe(280, party=[self.MUDKIP, mon("Ralts", 280, 5, slot=1, pid=0x77, ot_id=0x4321)], owned=(258,), outcome=7)]
        self.assertFalse([line for line in lines_of(run) if "[CATCH]" in line])

    def test_owned_pids_is_none_when_anything_is_unread(self) -> None:
        self.assertIsNone(owned_pids(observe(1, party=None)))
        self.assertIsNone(owned_pids(observe(1, party=[self.MUDKIP], storage=None)))
        self.assertEqual(owned_pids(observe(1, party=[self.MUDKIP], storage=[boxed(9)])), {0x550A9BE6: "party", 9: "box"})


class BattleLineTests(unittest.TestCase):
    """Finding 2: the foe refreshed on every in-battle look; a battle ends only on a result."""

    MUDKIP = mon("Mudkip", 258, 8, pid=0x550A9BE6)

    def test_the_foe_is_refreshed_on_every_in_battle_look(self) -> None:
        """The battle's first look holds the PREVIOUS battle's foe (`gBattleMons` is filled a few frames in,
        `BattleIntroGetMonsData`); the lines must name the foe of the LAST look."""
        wurmple = mon("Wurmple", 265, 3, slot=1, pid=0x7D6D2751)
        run = [observe(100, party=[self.MUDKIP], owned=(258,)),
               observe(160, party=[self.MUDKIP], owned=(258,), in_battle=True, battle=battle_view("wild", "Zigzagoon", 263, 2)),
               observe(220, party=[self.MUDKIP], owned=(258,), in_battle=True, battle=battle_view("wild", "Wurmple", 265, 3)),
               observe(280, party=[self.MUDKIP, wurmple], owned=(258, 265), outcome=7)]
        lines = lines_of(run)
        self.assertTrue(lines and all("Zigzagoon" not in line for line in lines), lines)
        self.assertTrue(any("[CATCH]" in line and "sp=Wurmple#265" in line for line in lines), lines)

    def test_a_foe_not_out_yet_is_refreshed_when_it_is(self) -> None:
        """The eyes report NO foe while `gBattleMons` still holds the previous battle's (`host/eyes.py`
        _battle's identity guard): the record opens on that look and takes the foe of a later one."""
        empty = BattleView(kind="wild", double=False, type_flags=4, opponent_trainer_id=None,
                           own=battle_view("wild", "X", 1, 1).own, foe=())
        run = [observe(100, party=[self.MUDKIP], owned=(258,)),
               observe(160, party=[self.MUDKIP], owned=(258,), in_battle=True, battle=empty),
               observe(220, party=[self.MUDKIP], owned=(258,), in_battle=True, battle=battle_view("wild", "Poochyena", 261, 4)),
               observe(280, party=[self.MUDKIP], owned=(258,), outcome=4)]
        ends = [line for line in lines_of(run) if "[AI-BATTLE] end" in line]
        self.assertEqual(len(ends), 1, ends)
        self.assertIn("sp=Poochyena#261 res=RanAway", ends[0])

    def test_present_pids_reads_the_occupied_slots(self) -> None:
        """`eyes/party.py` present_pids: the PIDs of a raw party's occupied slots (hasSpecies), no decryption."""
        from modules.pokemon import POKEMON_DATA_SUBSTRUCTS_ORDER

        raw = (encode_mon(0xB11EC02B, 0x5870, 280, (33, 0, 0, 0), (35, 0, 0, 0), 4, POKEMON_DATA_SUBSTRUCTS_ORDER)
               + bytes(PARTY_MON_SIZE * 5))
        self.assertEqual(party_module.present_pids(raw), frozenset({0xB11EC02B}))
        self.assertEqual(party_module.present_pids(bytes(PARTY_MON_SIZE * 6)), frozenset())

    def test_no_result_no_end_and_never_in_progress(self) -> None:
        """A look out of the battle screen (in_battle False) while `gBattleOutcome` is still 0 must end
        nothing, and no line may say InProgress (the step-1 rule wrote `res=InProgress`, a LOSS for the
        scorer). SYNTHETIC: the live catch (`live_step1.py` arm BLW) measured the nickname screen as
        in_battle True and the result set before in_battle first reads False, so this order is the rule's
        guarantee, not a captured state."""
        wurmple = mon("Wurmple", 265, 3, slot=1, pid=0x7D6D2751)
        run = [observe(100, party=[self.MUDKIP], owned=(258,)),
               observe(160, party=[self.MUDKIP], owned=(258,), in_battle=True, battle=battle_view("wild", "Wurmple", 265, 3)),
               observe(220, party=[self.MUDKIP], owned=(258,), outcome=0, game_state="UNKNOWN"),
               observe(280, party=[self.MUDKIP, wurmple], owned=(258, 265), outcome=7)]
        lines = lines_of(run)
        print(f"\n  a look out of the battle before its result: {lines}")
        self.assertFalse([line for line in lines if "InProgress" in line], lines)
        ends = [line for line in lines if "[AI-BATTLE] end" in line]
        self.assertEqual(len(ends), 1, lines)
        self.assertIn("res=Caught", ends[0])
        self.assertEqual(parse(scorer_lines(run))["catches"], 1)

    def test_the_end_waits_for_a_readable_look(self) -> None:
        """Between two screens the eyes withhold the save-block parts (`host/eyes.py`
        _save_blocks_may_be_moving): a result seen on such a look ends nothing; the next readable look ends
        the battle with ITS money, and no [DEX] line comes from the withheld Pokedex."""
        between = observe(220, party=None, owned=(258,), money=3144, outcome=1, storage=None)
        between = Observation(**{**between.__dict__, "progress": None, "player": None})
        run = [observe(100, party=[self.MUDKIP], owned=(258,), money=3000),
               observe(160, party=[self.MUDKIP], owned=(258,), money=3000, in_battle=True,
                       battle=battle_view("trainer", "Machop", 66, 9, trainer=322)),
               between,
               observe(280, party=[self.MUDKIP], owned=(258,), money=3144, outcome=1)]
        lines = lines_of(run)
        trainer = [line for line in lines if "[TRAINER] end" in line]
        self.assertEqual(len(trainer), 1, lines)
        self.assertTrue(trainer[0].startswith("f280 ") and "money=3000->3144" in trainer[0], trainer)
        self.assertFalse([line for line in lines if "[DEX]" in line], lines)

    def test_a_trainer_battle_ends_won_with_its_money(self) -> None:
        run = [observe(100, party=[self.MUDKIP], owned=(258,), money=3000),
               observe(160, party=[self.MUDKIP], owned=(258,), money=3000, in_battle=True,
                       battle=battle_view("trainer", "Machop", 66, 9, trainer=322)),
               observe(220, party=[self.MUDKIP], owned=(258,), money=3144, outcome=1)]
        lines = lines_of(run)
        trainer = [line for line in lines if "[TRAINER] end" in line]
        self.assertEqual(len(trainer), 1, lines)
        self.assertIn("opp=322 last_seen=Machop#66", trainer[0])
        self.assertIn("res=Won money=3000->3144 delta=144", trainer[0])


class PerceptionTests(unittest.TestCase):
    """Finding 3: what a person sees of a foe, of people on the map, and of trainer ids."""

    def test_the_hp_bar_is_the_decomps_48_pixels(self) -> None:
        """`src/battle_interface.c` GetScaledHPFraction(hp, maxhp, B_HEALTHBAR_PIXELS = 48), C integer maths,
        at least 1 pixel while hp > 0. Checked against a transcription with C truncation for every hp of
        three max values, and on the battle fixtures' values (Wurmple 14/14, Machop 31/31 and 0/31)."""
        self.assertEqual(HP_BAR_PIXELS, 48)

        def decomp(hp: int, maxhp: int) -> int:
            result = int(hp * 48 / maxhp)  # u8 result = hp * scale / maxhp (both non-negative: truncation)
            return 1 if result == 0 and hp > 0 else result

        for maxhp in (14, 31, 714):
            self.assertEqual([hp_bar_pixels(hp, maxhp) for hp in range(maxhp + 1)], [decomp(hp, maxhp) for hp in range(maxhp + 1)])
        self.assertEqual((hp_bar_pixels(14, 14), hp_bar_pixels(31, 31), hp_bar_pixels(0, 31), hp_bar_pixels(1, 714)), (48, 48, 0, 1))
        self.assertEqual(hp_bar_pixels(15, 31), 23)

    def test_a_foe_move_is_seen_once_used(self) -> None:
        self.assertTrue(foe_move_seen(29, 30))  # E10's Machop: Leer 29/30 after "Foe MACHOP used LEER!"
        self.assertFalse(foe_move_seen(20, 20))  # Low Kick, never used

    @staticmethod
    def battler(hp: int, max_hp: int, moves: list[tuple]) -> SimpleNamespace:
        """A stand-in for the framework's BattlePokemon (`modules/battle_state.py`), with the attributes the
        host's `_battle_mon` reads."""
        return SimpleNamespace(
            species=SimpleNamespace(name="Machop", national_dex_number=66), level=9, current_hp=hp, total_hp=max_hp,
            status_permanent=SimpleNamespace(name="Healthy"), types=[SimpleNamespace(name="Fighting")],
            personality_value=0x1234ABCD,  # build step 4: the own battler's identity
            moves=[SimpleNamespace(move=SimpleNamespace(name=n, type=SimpleNamespace(name=t), base_power=p), pp=pp, total_pp=top)
                   for n, t, p, pp, top in moves] + [None])

    def test_a_foe_is_seen_as_a_person_sees_it(self) -> None:
        """The HOST's conversion (`host/eyes.py` FrameworkEyes._battle_mon), E10's Machop: 0/31 HP, Low Kick
        20/20, Leer 29/30, Focus Energy 29/30. A foe: the bar, no numbers, only the used moves, no PP."""
        from ai_player.host.eyes import FrameworkEyes

        moves = [("Low Kick", "Fighting", 0, 20, 20), ("Leer", "Normal", 0, 29, 30), ("Focus Energy", "Normal", 0, 29, 30)]
        foe = FrameworkEyes._battle_mon(self.battler(15, 31, moves), own=False)
        self.assertEqual((foe.hp, foe.max_hp, foe.hp_bar), (None, None, 23))
        self.assertEqual([(m.name, m.pp, m.max_pp) for m in foe.moves], [("Leer", None, None), ("Focus Energy", None, None)])
        own = FrameworkEyes._battle_mon(self.battler(15, 31, moves), own=True)
        self.assertEqual((own.hp, own.max_hp, own.hp_bar), (15, 31, 23))
        self.assertEqual([(m.name, m.pp, m.max_pp) for m in own.moves], [(n, pp, top) for n, _, _, pp, top in moves])
        # build step 4: which of the player's own Pokemon is out, by its PID; a foe's identity is not on screen
        self.assertEqual((own.pid, foe.pid), (0x1234ABCD, None))

    def test_every_person_is_an_npc(self) -> None:
        """No "trainer" label before a trainer engages: the kind comes from the LOOK only (one argument)."""
        self.assertEqual(object_kind(7), "npc")  # a person's graphics
        self.assertEqual(object_kind(59), "item_ball")
        self.assertNotIn("trainer", set(GFX_KINDS.values()))
        self.assertNotIn("trainer", view_module.GLYPHS)

    def test_ids_are_the_visible_16_bits(self) -> None:
        """The HOST's party decode (`host/eyes.py` FrameworkEyes._mon) reports the VISIBLE OT id; the secret
        half (0xCAFE of 0xCAFEBABE) is in no field of the Observation's party."""
        from ai_player.host.eyes import FrameworkEyes
        from modules.pokemon import POKEMON_DATA_SUBSTRUCTS_ORDER

        framework_rom()
        self.assertEqual(visible_id(0xCAFEBABE), 0xBABE)
        data = encode_mon(0x1234500, 0xCAFEBABE, 280, (33, 45, 0, 0), (35, 40, 0, 0), 9, POKEMON_DATA_SUBSTRUCTS_ORDER)
        summary = FrameworkEyes._mon(0, data)
        self.assertEqual((summary.ot_id, summary.pid, summary.level), (0xBABE, 0x1234500, 9))
        self.assertNotIn(0xCAFE, (summary.ot_id >> 16, summary.ot_id))


class SettlingTests(unittest.TestCase):
    """Finding 4: a warp's settling frames report no position, and no map line is written from them."""

    def test_the_rule(self) -> None:
        """BOTH coordinates must agree. The measured warp (Dewford's door) differs in x only, so the y-only and
        both-differ cases are here on purpose: a rule that compares x alone (or y alone) passed the measured
        case and still mixed maps (the step-2 verifier's mutant V4; `gates/revert_step11.py` R4x, R4y)."""
        self.assertEqual(settled_position((3, 8), (3, 8)), (3, 8))
        self.assertIsNone(settled_position((8, 8), (3, 8)))  # measured: Dewford's door tile vs the arrival tile (x differs)
        self.assertIsNone(settled_position((3, 5), (3, 8)))  # y differs only (a door straight above its arrival tile)
        self.assertIsNone(settled_position((8, 5), (3, 8)))  # both differ

    def test_the_map_line_waits_for_the_settled_position(self) -> None:
        party = [mon("Mudkip", 258, 8)]
        run = [observe(100, where=("DEWFORD TOWN", 0, 11), xy=(8, 8), party=party),
               observe(160, where=("DEWFORD TOWN", 3, 5), party=party, settling=True),  # mid-warp: unknown
               observe(220, where=("DEWFORD TOWN", 3, 5), xy=(3, 8), party=party)]
        maps = [line for line in lines_of(run) if "[MAP]" in line]
        self.assertEqual(len(maps), 2, maps)
        self.assertTrue(maps[1].startswith("f220 ") and maps[1].endswith("(3,5) pos=(3, 8)"), maps)


class PartyNoneTests(unittest.TestCase):
    """Finding 5: an unread party (None) is not an empty one (())."""

    def test_an_unread_party_is_not_an_empty_one_for_the_starter(self) -> None:
        """A look that could not read the party, then a party: the starter is INFERRED (the run started with
        a party), never "observed: the party went from 0 to 1". (Before step 1.1 an unread party was ().)"""
        lines = scorer_lines([observe(10, party=None), observe(70, party=[mon("Torchic", 255, 5)])])
        self.assertIn("inferred at run start", lines[0])
        empty = scorer_lines([observe(10, party=()), observe(70, party=[mon("Torchic", 255, 5)])])
        self.assertIn("observed: the party went from 0 to 1", empty[0])

    def test_the_closing_heartbeat_comes_from_the_last_complete_look(self) -> None:
        import scoring

        scorer = ScorerLines()
        party = [mon("Mudkip", 258, 8)]
        scorer.update(observe(100, party=party, xy=(4, 4)))
        last = observe(160, party=None, xy=(5, 5))  # the brain's last look could not read the party
        scorer.update(last)
        beat = scorer.final(last)
        self.assertEqual(len(beat), 1, beat)
        self.assertTrue(beat[0].startswith("f100 ") and scoring.HB_RE.search(beat[0]), beat)

    def test_the_digest_says_the_party_was_not_read(self) -> None:
        self.assertIn("party=?", observe(10, party=None).digest())
        self.assertNotIn("party=", observe(10, party=()).digest())

    def test_a_torn_slot_makes_the_whole_party_none(self) -> None:
        """Finding 5, the HOST half (`host/eyes.py` FrameworkEyes._party: `return None if torn else party`). STEP 2.1:
        the step-2 verifier's weak proof: reverting it to `return party` failed no test (its V3; `revert_step11.py`
        covered only the memory_log half). The host's OWN `_party` reads a party of two through the framework's
        `read_symbol`, from a FAKE emulator memory: slot 1 a Pokemon encoded as the game encodes it, slot 2 another
        whose encrypted area has one byte changed (a slot caught while the game writes it: its checksum fails). The
        whole party is None and the problem names slot 2; with both slots whole the same path reads both
        (non-vacuity: the fake memory reaches the decoder). `revert_step11.py` R5c reverts it."""
        from modules.context import context
        from modules.game import get_symbol
        from modules.pokemon import POKEMON_DATA_SUBSTRUCTS_ORDER

        from ai_player.host.eyes import FrameworkEyes

        framework_rom()
        # the game's INTERNAL species indices: 280 Torchic, 283 Mudkip
        first = encode_mon(0x1234500, ME, 280, (33, 0, 0, 0), (35, 0, 0, 0), 5, POKEMON_DATA_SUBSTRUCTS_ORDER)
        second = encode_mon(0x1234501, ME, 283, (33, 0, 0, 0), (35, 0, 0, 0), 6, POKEMON_DATA_SUBSTRUCTS_ORDER)
        torn = bytearray(second)
        torn[40] ^= 0xFF  # as PartyDecoderTests.test_a_torn_slot_is_refused
        count_at, party_at = get_symbol("gPlayerPartyCount")[0], get_symbol("gPlayerParty")[0]

        class Memory:
            """The two symbols `_party` reads, at their real addresses; anything else is a test error."""

            def __init__(self, party: bytes) -> None:
                self.party = party

            def read_bytes(self, address: int, length: int) -> bytes:
                if address == count_at:
                    return bytes([2]) + bytes(length - 1)
                if address == party_at:
                    return (self.party + bytes(length))[:length]
                raise AssertionError(f"_party read 0x{address:08X}")

        def read(party: bytes) -> tuple[list | None, list[str]]:
            problems: list[str] = []
            with mock.patch.object(context, "emulator", Memory(party), create=True):
                return FrameworkEyes()._party(problems), problems

        whole, problems = read(first + second)
        self.assertEqual([(m.species, m.level, m.pid) for m in whole], [("Torchic", 5, 0x1234500), ("Mudkip", 6, 0x1234501)])
        self.assertEqual(problems, [])
        party, problems = read(first + bytes(torn))
        self.assertIsNone(party, "a party with a torn slot was reported one Pokemon short instead of not read")
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("party slot 2: "), problems)


class PokenavEyesTests(unittest.TestCase):
    """(chapter 5, 2026-11-05) The POKéNAV the AI was blind to (567 recon records of the MATCH CALL tutorial: ui None,
    scene None, the call-exit wait "not waiting"): U2 its three menus (`eyes/screens.py` pokenav_view, and the HOST's read of
    `gPokenavResources`), U3 the call-exit wait, U4 its scene, E7 the grid's own kind, E1 the player's name. Each FAULT
    half is what the eyes said before: no view (no `Task_Pokenav` rule), no wait, no scene, `multichoice`."""

    STATE_INPUT = bytes([3, 0]) + bytes(30)  # Task_Pokenav's data[0] = 3: it reads keys
    STATE_LOOPING = bytes([2, 0]) + bytes(30)  # data[0] = 2: a looped task runs (an animation, a list being built)

    def view(self, raw: dict, data: bytes | None = None):
        from ai_player.eyes.screens import read_ui

        return read_ui("UNKNOWN", {"Task_Pokenav": data or self.STATE_INPUT, "Task_MoveBgDots": bytes(32)},
                       {"pokenav": {"state": (data or self.STATE_INPUT)[0], **raw}})

    def test_u2_the_main_menu_in_each_of_its_tutorial_handlers(self) -> None:
        """Critic MENU-5: the tutorial runs `HandleMainMenuInputTutorial` before the call and `...EndTutorial` after it
        (recon: cursor @0, @1, @2, then @2): both take input; a transition's callback (`GetMenuId`) is no menu."""
        for handler in ("HANDLEMAINMENUINPUT", "HANDLEMAINMENUINPUTTUTORIAL", "HANDLEMAINMENUINPUTENDTUTORIAL"):
            with self.subTest(handler):
                ui = self.view({"menu": {"type": 1, "cursor": 2, "handler": handler}})
                self.assertEqual((ui.kind, ui.options, ui.cursor, ui.accepts_input),
                                 ("pokenav_menu", ("HOENN MAP", "CONDITION", "MATCH CALL", "SWITCH OFF"), 2, True))
        self.assertFalse(self.view({"menu": {"type": 1, "cursor": 1, "handler": "HANDLEMAINMENUINPUTTUTORIAL"}},
                                   self.STATE_LOOPING).accepts_input)  # moving: no key read
        self.assertIsNone(self.view({"menu": {"type": 1, "cursor": 2, "handler": "GETMENUID"}}))
        self.assertEqual(self.view({"menu": {"type": 2, "cursor": 0, "handler": "HANDLEMAINMENUINPUT"}}).options[3], "RIBBONS")

    def test_u2_the_match_call_list_and_an_entrys_options(self) -> None:
        listed = self.view({"mc": {"handler": "CB2_HANDLEMATCHCALLINPUT", "entries": ["MR. STONE"], "list_cursor": 0,
                                   "option_cursor": 0, "options": []}})
        self.assertEqual((listed.kind, listed.options, listed.cursor, listed.accepts_input),
                         ("pokenav_list", ("MR. STONE",), 0, True))
        options = self.view({"mc": {"handler": "CB2_HANDLEMATCHCALLOPTIONSINPUT", "entries": ["MR. STONE"],
                                    "list_cursor": 0, "option_cursor": 0, "options": [0, 2]}})
        self.assertEqual((options.kind, options.options, options.cursor), ("pokenav_options", ("CALL", "CANCEL"), 0))
        self.assertIsNone(self.view({"mc": {"handler": "CB2_HANDLECALLEXITINPUT", "entries": ["MR. STONE"],
                                            "list_cursor": 0, "option_cursor": 0, "options": [0, 2]}}))
        # FAULT half: before the rule, a POKéNAV screen read as nothing at all
        from ai_player.eyes.screens import read_ui

        self.assertIsNone(read_ui("UNKNOWN", {"Task_MoveBgDots": bytes(32)}, {}))

    def test_u2_the_host_follows_gpokenavresources(self) -> None:
        """The HOST's own `_pokenav` on a FAKE memory laid out as the decomp's structs (`src/pokenav.c` PokenavResources,
        `src/pokenav_menu_handler.c` Pokenav_Menu, `src/pokenav_match_call_list.c` Pokenav_MatchCallMenu, `src/pokenav_list.c`
        PokenavList's windowState @0x888): the main menu, then MR. STONE's options; the handlers named by the REAL reverse
        lookup (the handlers' real addresses, thumb bit set as the game stores them), `gPokenavResources` at its real address."""
        from modules.context import context
        from modules.game import get_symbol

        import ai_player.host.eyes as host_eyes

        framework_rom()
        pointer_at = get_symbol("gPokenavResources")[0]
        resources, menu, mc, listing, rom = 0x02010000, 0x02011000, 0x02012000, 0x02013000, 0x08600000
        tutorial, options_input = get_symbol("HandleMainMenuInputTutorial")[0], get_symbol("CB2_HandleMatchCallOptionsInput")[0]

        def u16(v: int) -> bytes:
            return v.to_bytes(2, "little")

        def u32(v: int) -> bytes:
            return v.to_bytes(4, "little")

        def memory(subs: dict[int, int]) -> dict[int, bytes]:
            table = b"".join(u32(subs.get(i, 0)) for i in range(19))
            return {pointer_at: u32(resources),
                    resources: bytes(16) + table,
                    menu: u16(1) + u16(2) + u16(2) + u16(0) + u32(0) + u32(tutorial | 1),
                    mc: u16(0) + u16(1) + u32(rom) + u16(0) + u16(1) + u16(5) + bytes(2) + u32(1) + u32(0)
                        + u32(options_input | 1) + bytes([1, 10]) + u16(0),
                    listing + 0x888: u16(0) + u16(1) + u16(0) + u16(0),
                    rom: bytes([0, 2])}

        class Memory:
            def __init__(self, cells: dict[int, bytes]) -> None:
                self.cells = cells

            def read_bytes(self, address: int, length: int) -> bytes:
                for start, data in self.cells.items():
                    if start <= address and address + length <= start + len(data) + 64:
                        return (data[address - start:] + bytes(length))[:length]
                raise AssertionError(f"_pokenav read 0x{address:08X} (+{length})")

        def read(subs):
            with mock.patch.object(context, "emulator", Memory(memory(subs)), create=True):
                return host_eyes.FrameworkEyes()._pokenav(self.STATE_INPUT)

        found = read({1: menu})
        self.assertEqual(found["menu"], {"type": 1, "cursor": 2, "handler": "HANDLEMAINMENUINPUTTUTORIAL"})
        self.assertEqual(self.view({k: v for k, v in found.items() if k != "state"}).kind, "pokenav_menu")
        # the host's `_ui` reads it whenever `Task_Pokenav` runs (its call of `_pokenav`), and `read_ui` names the menu
        with mock.patch.object(context, "emulator", Memory(memory({1: menu})), create=True):
            ui = host_eyes.FrameworkEyes()._ui("UNKNOWN", {"Task_Pokenav": self.STATE_INPUT})
        self.assertEqual((ui.kind, ui.cursor, ui.accepts_input), ("pokenav_menu", 2, True))
        found = read({5: mc, 17: listing})
        self.assertEqual(found["mc"], {"handler": "CB2_HANDLEMATCHCALLOPTIONSINPUT", "option_cursor": 0, "options": [0, 2],
                                       "entries": ["MR. STONE"], "list_cursor": 0})
        self.assertEqual(self.view({k: v for k, v in found.items() if k != "state"}).options, ("CALL", "CANCEL"))

    # ---- (gap round 2026-11-05, the verifier's F1: guards and arithmetic no test exercised)
    def test_u2_the_list_and_the_options_take_no_input_while_a_looped_task_runs(self) -> None:
        """`pokenav_view`'s "takes input" guard on the MATCH CALL list and on an entry's CALL / CANCEL, as the main menu's
        test has it: `Task_Pokenav` calls the current menu's handler only in state 3; in state 2 a looped task runs (the
        list being built, the options sliding in) and `break`s before any handler reads a key (`src/pokenav.c:452-457`).
        CONTROL: state 3, both take input. FAULT half: state 2, the same view (kind and cursor) takes none
        (`revert_r1_mutants.json` CH5E8 and CH5E9 delete the state from each)."""
        listed = {"mc": {"handler": "CB2_HANDLEMATCHCALLINPUT", "entries": ["MR. STONE", "MOM"], "list_cursor": 1,
                         "option_cursor": 0, "options": []}}
        options = {"mc": {"handler": "CB2_HANDLEMATCHCALLOPTIONSINPUT", "entries": ["MR. STONE"], "list_cursor": 0,
                          "option_cursor": 1, "options": [0, 2]}}
        for raw, kind, cursor in ((listed, "pokenav_list", 1), (options, "pokenav_options", 1)):
            with self.subTest(kind):
                taking, looping = self.view(raw), self.view(raw, self.STATE_LOOPING)
                self.assertEqual((taking.kind, taking.cursor, taking.accepts_input), (kind, cursor, True))  # CONTROL
                self.assertEqual((looping.kind, looping.cursor, looping.accepts_input), (kind, cursor, False))

    @staticmethod
    def _host_read(cells: dict[int, bytes], task: bytes, rom: bytes | None = None) -> dict | None:
        """The host's `_pokenav` on a FAKE memory: `cells` (exact ranges; EWRAM structs, or a value PLANTED over the
        cartridge), then, with `rom`, the REAL cartridge behind them (`context.rom.file`, the fixture profile's ROM)."""
        from modules.context import context

        import ai_player.host.eyes as host_eyes

        class Memory:
            def read_bytes(self, address: int, length: int) -> bytes:
                for start, data in cells.items():
                    if start <= address and address + length <= start + len(data):
                        return data[address - start:address - start + length]
                if rom is not None and 0x08000000 <= address and address + length <= 0x08000000 + len(rom):
                    return rom[address - 0x08000000:address - 0x08000000 + length]
                raise AssertionError(f"_pokenav read 0x{address:08X} (+{length})")

        with mock.patch.object(context, "emulator", Memory(), create=True):
            return host_eyes.FrameworkEyes()._pokenav(task)

    @staticmethod
    def _match_call_cells(entries: list[tuple[int, int]], top: int, offset: int) -> dict[int, bytes]:
        """`gPokenavResources` -> substruct 5 (Pokenav_MatchCallMenu on its list handler, `entries` as (isSpecialTrainer,
        headerId)) and 17 (PokenavList: the window state @0x888 {windowTopIndex @0, listLength @2, entriesOffscreen @4,
        selectedIndexOffset @6}, `src/pokenav_list.c:29-40`), laid out as `test_u2_the_host_follows_gpokenavresources`."""
        from modules.game import get_symbol

        def u16(v: int) -> bytes:
            return v.to_bytes(2, "little")

        def u32(v: int) -> bytes:
            return v.to_bytes(4, "little")

        resources, mc, listing = 0x02010000, 0x02012000, 0x02013000
        table = b"".join(u32({5: mc, 17: listing}.get(i, 0)) for i in range(19))
        handler = get_symbol("CB2_HandleMatchCallInput")[0]
        head = (u16(0) + u16(0) + u32(0) + u16(0) + u16(len(entries)) + u16(0) + bytes(2) + u32(1) + u32(0)
                + u32(handler | 1))
        listed = b"".join(bytes([special, 10]) + u16(header) for special, header in entries)
        return {get_symbol("gPokenavResources")[0]: u32(resources), resources: bytes(16) + table, mc: head + listed,
                listing + 0x888: u16(top) + u16(len(entries)) + u16(0) + u16(offset)}

    def test_u2_the_list_cursor_is_the_windows_top_plus_its_offset(self) -> None:
        """The MATCH CALL list's cursor is the entry SELECTED: `windowTopIndex + selectedIndexOffset`
        (`src/pokenav_list.c:445-450` PokenavList_GetSelectedIndex). A list of six scrolled 3 entries down with the cursor
        on the window's 2nd row has entry 4 (WALLY) selected. FAULT half (the offset alone, `revert_r1_mutants.json`
        CH5E10): row 1 of the list, PROF. BIRCH. CONTROL: a window at its top (the tutorial's, top 0) is the same index
        both ways, which is why `test_u2_the_host_follows_gpokenavresources` could not tell them apart."""
        framework_rom()
        specials = [(1, header) for header in range(6)]  # MC_HEADER_MR_STONE .. MC_HEADER_NORMAN (`include/pokenav.h:188`)
        found = self._host_read(self._match_call_cells(specials, top=3, offset=1), self.STATE_INPUT)
        self.assertEqual(found["mc"]["entries"], ["MR. STONE", "PROF. BIRCH", "BRENDAN", "MAY", "WALLY", "DAD"])
        self.assertEqual(found["mc"]["list_cursor"], 4)
        ui = self.view({"mc": found["mc"]})
        self.assertEqual((ui.kind, ui.cursor, ui.options[ui.cursor], ui.accepts_input), ("pokenav_list", 4, "WALLY", True))
        at_top = self._host_read(self._match_call_cells(specials, top=0, offset=4), self.STATE_INPUT)
        self.assertEqual(at_top["mc"]["list_cursor"], 4)  # CONTROL: top 0, the offset alone is the index

    def test_u2_an_ordinary_trainers_entry_is_named_from_the_rom(self) -> None:
        """An ORDINARY trainer's MATCH CALL entry (isSpecialTrainer 0) is named as the game names it (its name; the class
        the game draws beside it is left out on purpose, `eyes/screens.py`)
        (`src/pokenav_match_call_list.c:399-410` BufferMatchCallNameAndDesc: `GetTrainerIdxByRematchIdx(headerId)`, which
        is `gRematchTable[rematchIdx].trainerIds[0]`, `src/pokenav_match_call_data.c:735-738`, then that trainer's
        `gTrainers[].trainerName`), the host reading the ROM's OWN tables (the fixture profile's cartridge behind a fake
        EWRAM). EXPECTED, from the pinned decomp: REMATCH_ANDRES 1 and REMATCH_DUSTY 2 (`include/constants/rematches.h:6-7`)
        -> TRAINER_ANDRES_1 and TRAINER_DUSTY_1 (`src/battle_setup.c:263-264`) -> "ANDRES" and "DUSTY"
        (`src/data/trainers.h:8853`, `:537`); REMATCH_WALLACE, the table's LAST row (77, `include/constants/rematches.h:82`)
        -> TRAINER_WALLACE (`src/battle_setup.c:339`) -> "WALLACE" (`src/data/trainers.h:4029`). MR. STONE is the special
        entry the tutorial has.

        THIS TEST FOUND A REAL DEFECT (gap round, 2026-11-05): the build read the table at the struct's 14 bytes of
        members, but agbcc pads `struct RematchTrainer` to 16 (the symbol table's gRematchTable is 0x4E0 = 78 x 16 bytes),
        so REMATCH_ANDRES was named "" and REMATCH_DUSTY "GRUNT" (the FAULT half: `revert_r1_mutants.json` CH5E5 restores
        14). The two RANGE GUARDS, each with a value PLANTED where its guard is the only thing between the read and a
        name: a header past the table (78 = REMATCH_TABLE_ENTRIES, a real trainer id planted right after the table) and a
        row naming trainer 855 (TRAINERS_COUNT, `include/constants/opponents.h:864`; past gTrainers lies gSpeciesNames)
        each name NOTHING (FAULT halves: CH5E6 and CH5E7 delete each guard). CONTROL: row 77 is in range and named."""
        from modules.context import context
        from modules.game import get_symbol

        framework_rom()
        rom = Path(context.rom.file).read_bytes()
        rematch, size = get_symbol("gRematchTable")
        self.assertEqual(size, 78 * 16)  # REMATCH_TABLE_ENTRIES (78) rows of 16 bytes: the padding is in the ROM's table
        entries = [(1, 0), (0, 1), (0, 2), (0, 77), (0, 78), (0, 5)]
        cells = self._match_call_cells(entries, top=0, offset=0)
        cells[rematch + 16 * 78] = (44).to_bytes(2, "little")  # PLANTED: TRAINER_DUSTY_1 right after the table
        cells[rematch + 16 * 5] = (855).to_bytes(2, "little")  # PLANTED: row 5 (REMATCH_LILA_AND_ROY) names trainer 855
        found = self._host_read(cells, self.STATE_INPUT, rom)
        self.assertEqual(found["mc"]["entries"], ["MR. STONE", "ANDRES", "DUSTY", "WALLACE", "", ""])

    def test_u3_the_call_exit_wait_is_seen(self) -> None:
        from ai_player.eyes.screens import pokenav_wait

        ended = {"state": 3, "mc": {"handler": "CB2_HANDLECALLEXITINPUT"}}
        self.assertEqual(pokenav_wait(ended), "task Task_Pokenav (A or B: the call has ended)")
        self.assertIsNone(pokenav_wait({**ended, "state": 2}))  # the call's message still runs (a looped task)
        self.assertIsNone(pokenav_wait({"state": 3, "mc": {"handler": "CB2_HANDLEMATCHCALLINPUT"}}))  # the list: a menu
        self.assertIsNone(pokenav_wait(None))

    def test_u4_the_pokenav_is_a_named_scene(self) -> None:
        from ai_player.eyes.screens import SCENE_CALLBACKS, scene_of

        for callback in ("CB2_InitPokenavForTutorial", "CB2_Pokenav", "CB2_InitPokeNav"):
            self.assertEqual(scene_of("UNKNOWN", (), callback), "the POKéNAV")
        self.assertIsNone(scene_of("UNKNOWN", (), "CB2_SomethingElse"))  # FAULT half: an unnamed callback: no scene
        self.assertIn("CB2_Pokenav", SCENE_CALLBACKS)

    def test_e7_a_grid_of_options_is_its_own_kind(self) -> None:
        """Critic MENU-3: E7 RECLASSIFIES the grid (`Task_HandleMultichoiceGridInput`, the Rustboro school's blackboard),
        which the eyes reported as `multichoice` before: its options and cursor are still read; a list multichoice is
        unchanged (CONTROL)."""
        from ai_player.eyes.screens import read_ui

        menu = bytes([0, 0, 2, 0, 5]) + bytes(7)  # sMenu: cursorPos 2, maxCursorPos 5
        names = ["PSN", "PAR", "SLP", "BRN", "FRZ", "EXIT"]
        grid = read_ui("OVERWORLD", {"Task_HandleMultichoiceGridInput": bytes(32)},
                       {"menu": menu, "multichoice_options": names, "multichoice_delay": 0})
        self.assertEqual((grid.kind, grid.options, grid.cursor), ("multichoice_grid", tuple(names), 2))
        listed = read_ui("OVERWORLD", {"Task_HandleMultichoiceInput": bytes(32)},
                         {"menu": menu, "multichoice_options": names, "multichoice_delay": 0})
        self.assertEqual(listed.kind, "multichoice")

    def test_e1_the_player_has_a_name_field(self) -> None:
        from dataclasses import fields

        self.assertIn("name", {f.name for f in fields(PlayerState)})
        self.assertIsNone(PlayerState(0, 0, "X", None, 0, 0, "down", "walking", 3, 0, 1).name)


class ScriptWaitTests(unittest.TestCase):
    """Finding 6: the script's waitbuttonpress branch (`eyes/view.py` script_waits_for_button)."""

    def test_the_rule(self) -> None:
        # measured on dewford.ss1, reading its sign (`gates/live_step1.py` arm SW): status 0, Native, WaitForAorBPress
        self.assertTrue(script_waits_for_button(0, "Native", "WaitForAorBPress"))
        # measured on dewford.ss1's first frame: a FINISHED script (status 2, mode Stopped) leaves WaitForAorBPress behind
        self.assertFalse(script_waits_for_button(2, "Stopped", "WaitForAorBPress"))
        # each check alone refuses it (`live_step1.py` arm SW: SW-R1 and SW-R2 remove one each, not caught)
        self.assertFalse(script_waits_for_button(2, "Native", "WaitForAorBPress"))
        self.assertFalse(script_waits_for_button(0, "Stopped", "WaitForAorBPress"))
        self.assertFalse(script_waits_for_button(0, "Bytecode", "WaitForAorBPress"))
        self.assertFalse(script_waits_for_button(0, "Native", "IsFieldMessageBoxHidden"))  # waitmessage: the text prints


class CallEndHostTests(unittest.TestCase):
    """(chapter 6, 2026-11-05) THE END OF A CALL IN THE FIELD, the HOST's reads on a FAKE memory laid out at the real symbols:
    `_match_call_wait` asks the printer of the CALL'S window (`ExecuteMatchCall` data[2]), never printer 0, and the two
    sound-effect players (`IsSEPlaying`); `_call_window` gives that window once the call's printer is readied (state 3 on);
    `_text` reads the call window's words before printer 0's. Each FAULT half is a printer-0 read or no call window."""

    CALL = bytes([5, 0, 0, 0, 1, 0]) + bytes(26)  # tState 5 (PrintMessage), tWindowId 1

    def memory(self, active: dict[int, int], se1: int = 0, se2: int = 0, pointers: dict[int, int] | None = None,
               extra: dict[int, bytes] | None = None):
        from modules.game import get_symbol

        framework_rom()
        printers = bytearray(0x24 * 32)
        for index, on in active.items():
            printers[index * 0x24 + 0x1B] = on
        for index, pointer in (pointers or {}).items():
            printers[index * 0x24:index * 0x24 + 4] = pointer.to_bytes(4, "little")
        cells = {get_symbol("sTextPrinters")[0]: bytes(printers),
                 get_symbol("gMPlayInfo_SE1")[0]: bytes(4) + se1.to_bytes(4, "little"),
                 get_symbol("gMPlayInfo_SE2")[0]: bytes(4) + se2.to_bytes(4, "little"), **(extra or {})}

        class Memory:
            def read_bytes(self, address: int, length: int) -> bytes:
                for start, data in cells.items():
                    if start <= address and address + length <= start + len(data):
                        return bytes(data[address - start:address - start + length])
                raise AssertionError(f"read 0x{address:08X} (+{length})")

        return Memory()

    def wait(self, memory) -> str | None:
        from modules.context import context

        import ai_player.host.eyes as host_eyes

        with mock.patch.object(context, "emulator", memory, create=True):
            return host_eyes.FrameworkEyes()._match_call_wait(self.CALL)

    def test_the_wait_is_read_from_the_calls_own_printer_and_the_sound(self) -> None:
        self.assertEqual(self.wait(self.memory({})),
                         "task ExecuteMatchCall (A or B: the call's last page has printed; a press hangs up)")
        self.assertIsNone(self.wait(self.memory({1: 1})))  # the call's window still printing
        self.assertIsNone(self.wait(self.memory({}, se1=3)))  # a sound effect playing
        self.assertEqual(self.wait(self.memory({}, se1=0x80000003, se2=0x80000001)), self.wait(self.memory({})))  # both paused
        # FAULT half: printer 0 (the field's message window) says nothing about the call: busy there, the call still waits
        self.assertIsNotNone(self.wait(self.memory({0: 1})))

    def test_the_call_window_and_its_words(self) -> None:
        from modules.context import context
        from modules.game import get_symbol

        import ai_player.host.eyes as host_eyes

        framework_rom()
        eyes = host_eyes.FrameworkEyes
        self.assertEqual(eyes._call_window(self.CALL), 1)
        for state, window in ((2, None), (3, 1), (4, 1), (6, 1), (7, 1)):
            with self.subTest(state=state):
                self.assertEqual(eyes._call_window(bytes([state, 0, 0, 0, 1, 0]) + bytes(26)), window)
        self.assertIsNone(eyes._call_window(None))
        self.assertIsNone(eyes._call_window(bytes([5, 0, 0, 0, 40, 0])))  # not a printer
        var4, var4_size = get_symbol("gStringVar4")
        battle, battle_size = get_symbol("gDisplayedStringBattle")
        call_words = encode("See you again!") + b"\xff"
        old_words = encode("GROVYLE gained 47 EXP. Points!") + b"\xff"
        memory = self.memory({}, pointers={0: battle + len(old_words) - 1, 1: var4 + len(call_words) - 1},
                             extra={var4: call_words + bytes(var4_size - len(call_words)),
                                    battle: old_words + bytes(battle_size - len(old_words))})
        with mock.patch.object(context, "emulator", memory, create=True):
            self.assertEqual(eyes._text(True, frozenset({"ExecuteMatchCall"}), 1), "See you again!")
            # FAULT half: no call window, printer 0's stale battle message (measured on call_end_cindy.ss1)
            self.assertEqual(eyes._text(True, frozenset({"ExecuteMatchCall"}), None), "GROVYLE gained 47 EXP. Points!")


def encode(words: str) -> bytes:
    """Words in the game's charmap (`eyes/screens.py` encode_char), for a fake memory."""
    from ai_player.eyes.screens import encode_char

    return bytes(encode_char(c) for c in words)


class LiveCallEndTests(unittest.TestCase):
    """(chapter 6, 2026-11-05) THE END OF A CALL on the REAL game: the KI-134 B arm's two end states, which the AI never left
    (`fixtures/call_end_dad.build.json`: DAD's call from MR. BRINEY's first-sail script; `call_end_cindy.build.json`: a
    trainer's MATCH CALL in PETALBURG WOODS). The eyes report the wait, with the call's words; ONE A ends the call (the
    task gone); after it nothing waits while the window slides out with the controls still locked (a scene that really
    locks them), and the next wait is the ordinary text that follows (DAD's: "Registered DAD NORMAN", a script's wait).
    FAULT half on the same frame: the rules the eyes had before (the printers, the script, the task table, the POKéNAV's)
    report no wait at all."""

    FIXTURES = SUPPORT / "ai_player" / "gates" / "fixtures"

    @classmethod
    def setUpClass(cls) -> None:
        from ai_player.gates.probe_eyes import boot

        with mock.patch.dict(os.environ, {"AI_PLAYER_BUILD_ROOT": str(BUILD_ROOT)}):
            cls.context = boot("ai-step0-fixture")
        cls.emulator = cls.context.emulator

    def load(self, name: str):
        from modules.state_cache import state_cache

        from ai_player.host.eyes import FrameworkEyes

        self.emulator.load_save_state((self.FIXTURES / name).read_bytes())
        state_cache.reset()
        self.emulator.run_single_frame()
        return FrameworkEyes()

    @staticmethod
    def tasks() -> set[str]:
        from modules.tasks import get_tasks

        return {task.symbol for task in get_tasks()}

    def old_rules(self, eyes) -> str | None:
        """What the eyes' rules before the fix say on this frame (the host's own reads, each rule unchanged)."""
        from ai_player.eyes.screens import pokenav_wait, task_wait

        return eyes._waits_for_button() or task_wait(self.tasks()) or pokenav_wait(None)

    def hang_up(self, eyes, frames: int = 300) -> list:
        """ONE A, then `frames` frames: each frame's (call task running, waits, wait reason, controls locked)."""
        self.emulator.press_button("A")
        self.emulator.run_single_frame()
        seen = []
        for _ in range(frames):
            self.emulator.run_single_frame()
            screen = eyes.look().screen
            seen.append(("ExecuteMatchCall" in self.tasks(), screen.waits_for_button, screen.wait_reason,
                         screen.controls_locked))
        return seen

    def test_dads_call_on_the_first_sail(self) -> None:
        eyes = self.load("call_end_dad.ss1")
        screen = eyes.look().screen
        self.assertTrue(screen.waits_for_button)
        self.assertTrue(screen.wait_reason.startswith("task ExecuteMatchCall"), screen.wait_reason)
        self.assertTrue(screen.text.endswith("Click!"), screen.text)
        self.assertIsNone(self.old_rules(eyes))  # FAULT half
        seen = self.hang_up(eyes, 400)
        ended = next(i for i, s in enumerate(seen) if not s[0])
        self.assertLess(ended, 120)
        self.assertFalse(any(s[1] for s in seen[:ended]))  # the window slides out: no wait
        self.assertTrue(all(s[3] for s in seen[:ended]))  # ... with the controls locked
        after = [s[2] for s in seen[ended:] if s[1]]
        self.assertTrue(after, "the script's next text never waited")
        self.assertFalse(any((reason or "").startswith("task ExecuteMatchCall") for reason in after))  # CONTROL
        self.assertIn("Registered DAD NORMAN", eyes.look().screen.text or "")

    def test_a_trainers_match_call_in_the_woods(self) -> None:
        eyes = self.load("call_end_cindy.ss1")
        screen = eyes.look().screen
        self.assertTrue(screen.waits_for_button)
        self.assertTrue(screen.wait_reason.startswith("task ExecuteMatchCall"), screen.wait_reason)
        self.assertTrue(screen.text.endswith("See you again!"), screen.text)  # the call's words, not printer 0's
        self.assertFalse(screen.script_running or screen.text_box_open)  # no script, no field box: only the call
        self.assertIsNone(self.old_rules(eyes))  # FAULT half
        seen = self.hang_up(eyes, 120)
        ended = next(i for i, s in enumerate(seen) if not s[0])
        self.assertLess(ended, 80)
        self.assertFalse(any(s[1] for s in seen))  # no wait after the A, while sliding out or after
        self.assertTrue(seen[ended - 1][3] and not seen[-1][3])  # locked while it slides out; free after
        self.assertIsNone(eyes.look().screen.text)

    def test_control_a_text_box_that_waits_is_read_as_before(self) -> None:
        """CONTROL: a trainer's defeat text that waits for a press (`trainer_defeat_text_r116.ss1`, printer 0 WAIT) is
        reported by the printer rule, as before, with no call running."""
        eyes = self.load("trainer_defeat_text_r116.ss1")
        screen = eyes.look().screen
        self.assertNotIn("ExecuteMatchCall", self.tasks())
        self.assertTrue(screen.waits_for_button)
        self.assertTrue(screen.wait_reason.startswith("text printer 0"), screen.wait_reason)

    def test_control_the_sail_after_the_call_is_a_scene_that_really_locks_the_controls(self) -> None:
        """(chapter 6 stops, the second builder, 2026-11-06) CONTROL: a scene that REALLY locks the controls, on the real
        game. After DAD's call is hung up (ONE A), MR. BRINEY's boat crosses ROUTE 105 and 106 to DEWFORD with the script
        running and the controls locked for some 900 frames: the eyes report no wait there (a press there would be mashing),
        never the call's wait once the call has ended, and only the script's own waits (the 'Registered DAD NORMAN' button
        wait, MR. BRINEY's words at DEWFORD) between; a press on each of those, and the sail ends in DEWFORD with the
        player free (VISITED_DEWFORD_TOWN set by the game). Measured by s53/ch6stops2/sail_proto.py: 3 waits, the longest
        locked stretch with no wait 917 frames, DEWFORD at frame 749 after the A."""
        from modules.memory import get_event_flag

        eyes = self.load("call_end_dad.ss1")
        self.emulator.press_button("A")
        self.emulator.run_single_frame()
        frames, waits, locked_quiet, longest, ended, free = 0, [], 0, 0, None, None
        for frames in range(1, 1700):
            self.emulator.run_single_frame()
            screen = eyes.look().screen
            if ended is None and "ExecuteMatchCall" not in self.tasks():
                ended = frames
            if ended is not None:
                self.assertFalse((screen.wait_reason or "").startswith("task ExecuteMatchCall"), (frames, screen.wait_reason))
            if screen.waits_for_button:
                waits.append(screen.wait_reason)
                locked_quiet = 0
                self.emulator.press_button("A")
                self.emulator.run_single_frame()
                continue
            locked_quiet = locked_quiet + 1 if screen.controls_locked and screen.script_running else 0
            longest = max(longest, locked_quiet)
            if get_event_flag("VISITED_DEWFORD_TOWN") and not screen.controls_locked and not screen.script_running:
                free = frames
                break
        self.assertIsNotNone(ended)
        self.assertLess(ended, 80)
        self.assertGreaterEqual(longest, 600)  # the boat moving: a scene that locks the controls, no wait, no press
        self.assertTrue(waits and len(waits) <= 4, waits)
        self.assertTrue(all(w.startswith(("script ", "text printer")) for w in waits), waits)
        self.assertIsNotNone(free, "the sail never ended with the player free in DEWFORD")

    def test_control_the_chapter5_pokenav_call_is_read_exactly_as_before(self) -> None:
        """(chapter 6 stops, the second builder, 2026-11-06) CONTROL: the chapter-5 POKéNAV registration call (MR. STONE's
        MATCH CALL in RustboroCity_EventScript_MatchCallTutorial, `pokenav_tutorial_rustboro.ss1`) is read EXACTLY as before
        the round. Presses are chosen from what the round's eyes report (the forced START menu to POKéNAV, MATCH CALL, MR.
        STONE, CALL, A on every page that waits, B out of the POKéNAV, A on the field's last words); a SECOND eyes with the
        chapter-6 branch patched out (`_match_call_wait` and `_call_window` None: the eyes before the round) reads every
        frame too, and the two never differ. That call runs inside the POKéNAV (`Task_Pokenav`), never `ExecuteMatchCall`,
        and its end is the POKéNAV's own wait (`pokenav_wait`). The tutorial completes: VAR_RUSTBORO_CITY_STATE 6 -> 7."""
        from modules.memory import get_event_var, get_game_state_symbol

        from ai_player.host.eyes import FrameworkEyes

        new = self.load("pokenav_tutorial_rustboro.ss1")
        old = FrameworkEyes()
        old._match_call_wait = lambda call: None  # noqa: SLF001 - the eyes before the round
        old._call_window = lambda call: None  # noqa: SLF001
        self.assertEqual(get_event_var("RUSTBORO_CITY_STATE"), 6)
        seen = {"frames": 0, "reasons": set(), "presses": 0}

        def frame():
            self.emulator.run_single_frame()
            seen["frames"] += 1
            a, b = new.look().screen, old.look().screen
            self.assertEqual(a, b, seen["frames"])
            self.assertNotIn("ExecuteMatchCall", self.tasks())
            if a.wait_reason:
                seen["reasons"].add(a.wait_reason.split(" (")[0])
            return a

        def press(button):
            self.emulator.press_button(button)
            seen["presses"] += 1
            return frame()

        def until(test, limit):
            for _ in range(limit):
                screen = frame()
                if test(screen):
                    return screen
            self.fail(f"not reached in {limit} frames (frame {seen['frames']})")

        def menu(kind):
            return lambda s: s.ui is not None and s.ui.kind == kind and s.ui.accepts_input

        screen = frame()
        for _ in range(12):
            if menu("multichoice")(screen) and screen.ui.cursor == 3:
                break
            press("Down")
            screen = until(lambda s: s.ui is not None and s.ui.accepts_input, 60)
        press("A")  # POKéNAV
        screen = until(menu("pokenav_menu"), 1500)
        while screen.ui.cursor != 2:
            press("Down")
            screen = until(menu("pokenav_menu"), 120)
        press("A")  # MATCH CALL
        until(menu("pokenav_list"), 1500)
        press("A")  # MR. STONE
        until(menu("pokenav_options"), 600)
        press("A")  # CALL
        for _ in range(3000):
            screen = frame()
            if screen.waits_for_button:
                press("A")
            elif menu("pokenav_list")(screen):
                break
        press("B")
        until(menu("pokenav_menu"), 600)
        press("B")
        for _ in range(3000):
            screen = frame()
            if get_game_state_symbol() in ("CB2_OVERWORLD", "CB2_Overworld"):
                if screen.waits_for_button:
                    press("A")
                elif not screen.script_running and not screen.controls_locked:
                    break
        self.assertEqual(seen["reasons"], {"text printer 1 CLEAR", "task Task_Pokenav", "script waitbuttonpress"})
        self.assertEqual(get_event_var("RUSTBORO_CITY_STATE"), 7)


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
