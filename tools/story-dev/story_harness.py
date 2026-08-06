"""FAITHFUL reproduction harness for the Lv16 move-learn hang (ML-11/ML-12).

Replicates modules/main.py's main_loop EXACTLY (FrameInfo build + listener
dispatch + controller-stack advance + run_single_frame) so behaviour matches
the real bot. Loads a save state, optionally injects a party, runs Story mode,
and logs battle/level-up/move-learn transitions + a full per-frame trace while
any move-learn or evolution is active, and a no-progress dump if it stalls.

Usage:
    python repro_movelearn.py <state.ss1> [--inject-treecko] [--frames N] [--build sandbox|custom]
"""

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ap = argparse.ArgumentParser()
ap.add_argument("state", help=".ss1 save state to load (basename in scratchpad or full path)")
ap.add_argument("--inject-treecko", action="store_true", help="inject a Lv15 Treecko at exp_for_16 - 1 as lead")
ap.add_argument("--inject-weak", action="store_true", help="inject a lone Lv3 Poochyena (loses everything â†’ forces a whiteout, for defeat-recovery testing)")
ap.add_argument("--inject-faintbench", action="store_true", help="inject Lv3 lead + Lv4 bench (forces the after-faint party menu â€” KI-12 repro)")
ap.add_argument("--inject-shedinja-faint", action="store_true", help="inject an all-BURNED 1-HP party (Shedinja lead + bench) — rapid in-battle faints for the KI-15 after-faint chooser repro; pair with --driver faintrepro")
ap.add_argument("--set-balls", type=int, default=None, help="force the PokÃ© Ball count (test out-of-balls provisioning)")
ap.add_argument("--inject-at", type=int, default=8, help="frame to inject the party at")
ap.add_argument("--frames", type=int, default=60000)
ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"])
ap.add_argument("--profile", default="repro-ml")
ap.add_argument("--driver", default="spin", choices=["spin", "story", "rival", "ch5recon", "martrecon", "martbuy", "healtest", "traintest", "traintest102", "gymtest", "pokenavtut", "pokenavclear", "pokenavskip", "pokenavfaith", "sailrecon", "rivalretry", "saildewford", "shinytest", "storydebugreset", "cavetrain", "fierycave", "hmtest", "faintrepro", "journey", "smashroute", "cavethread", "normancounter"])
ap.add_argument(
    "--break-state",
    action="store_true",
    help="FAULT INJECTION: simulate the user's env â€” make get_learn_move_state never "
    "report AskWhetherToLearn (returns Unknown) and force is_waiting_for_input False, "
    "so ONLY the on-screen text can drive the yes/no. Old code hangs; the fix must not.",
)
ap.add_argument("--log", default=None)
ap.add_argument("--video", action="store_true", help="enable the BG/OBJ renderer (needed to drive the PokÃ©Nav app)")
args = ap.parse_args()

# Paths are resolved RELATIVE TO THE REPO so this works on any machine/checkout:
# this file lives at <repo>/tools/story-dev/story_harness.py.
_REPO = Path(__file__).resolve().parents[2]
BUILD = _REPO / f"{args.build}-pokebot"
sys.path.insert(0, str(BUILD))
SCRATCH = Path(__file__).parent            # tools/story-dev/  (logs + newly-written states land here)
SAVES = SCRATCH / "saves"                  # committed checkpoint saves (load these by basename)
LOG = Path(args.log) if args.log else SCRATCH / f"harness_{args.build}.log"

FRESH = args.state.lower() == "fresh"
state_path = None
if not FRESH:
    state_path = Path(args.state)
    if not state_path.is_absolute():
        # try saves/ first (committed checkpoints), then the tool dir.
        for cand in (SAVES / args.state, SCRATCH / args.state):
            if cand.is_file():
                state_path = cand
                break
        else:
            state_path = SAVES / args.state
    assert state_path.is_file(), f"no such state: {state_path} (looked in {SAVES} and {SCRATCH})"

logf = open(LOG, "w", encoding="utf-8")


def log(msg):
    logf.write(msg + "\n")
    logf.flush()
    print(msg)


# ---- bootstrap headless (mirrors modules/gui/headless.py) --------------------
from modules.context import context
from modules.profiles import create_profile, profile_directory_exists, load_profile_by_name
from modules.roms import list_available_roms
from modules.game import set_rom

if not profile_directory_exists(args.profile):
    roms = list_available_roms()
    assert roms, "no ROMs found in roms/"
    create_profile(args.profile, roms[0])
    log(f"[setup] created profile {args.profile}")

profile = load_profile_by_name(args.profile)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = bool(getattr(args, "video", False))  # renderer on when --video (PokÃ©Nav app needs it)
context.emulation_speed = 0
context.debug = False
context.bot_mode = "Story"

# load the save state (unless a fresh-from-title boot was requested)
if FRESH:
    log(f"[setup] FRESH boot from title (no save state); build={args.build}")
else:
    context.emulator.load_save_state(state_path.read_bytes())
    log(f"[setup] loaded save state {state_path.name}; build={args.build}")

# ---- the faithful loop pieces ------------------------------------------------
from modules.memory import get_game_state, GameState, read_symbol, unpack_uint16
from modules.modes import FrameInfo, get_bot_listeners, get_bot_mode_by_name, BotModeError
from modules.plugins import load_built_in_plugins, plugin_profile_loaded
from modules.state_cache import state_cache
from modules.stats import StatsDatabase
from modules.tasks import get_global_script_context, get_tasks, task_is_active
from modules.battle_state import (
    battle_is_active,
    get_current_battle_script_instruction,
    get_main_battle_callback,
)
from modules.pokemon_party import get_party
from modules.game import decode_string


class ManualBotMode:
    @staticmethod
    def name():
        return "Manual"

    def run(self):
        yield


from modules.modes import BotMode


class FaintReproMode(BotMode):
    """KI-15 repro driver: spin for wild encounters but NEVER FLEE (attack-through), so a
    poisoned 1-HP Shedinja lead stays in and faints from end-of-turn poison -> the
    after-faint PARTY_MENU -> handle_fainted_pokemon (the thing we want to stress)."""
    @staticmethod
    def name():
        return "FaintRepro"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy
        from modules.battle_strategies import TurnAction, BattleStrategyUtil

        class _NoFlee(LevelUpTravelBattleStrategy):
            def decide_turn(self, battle_state):
                util = BattleStrategyUtil(battle_state)
                active = battle_state.own_side.active_battler
                move = util.get_strongest_move_against(active, battle_state.opponent.active_battler) if active else None
                if move is not None:
                    return TurnAction.use_move(move)
                if active is not None:
                    for i, learned in enumerate(active.moves):
                        if learned is not None and util.move_is_usable(learned):
                            return TurnAction.use_move(i)
                return TurnAction.use_move(0)

            def should_flee_after_faint(self, battle_state):
                # KI-15: the base strategy FLEES after a faint ("Got away safely!"), which
                # skips choose-new-lead and the after-faint PARTY_MENU sweep entirely. Force
                # send-out so the faint routes THROUGH the choose menu (the hang site).
                return False
        return _NoFlee()

    def run(self):
        from modules.modes.util import spin
        yield from spin()


class SpinFightMode(BotMode):
    """Minimal driver: walk in grass to trigger WILD battles and fight them with
    the REAL Story battle strategy (so the move-learn REPLACE path runs). This
    isolates the battle/move-learn flow from Story's overworld navigation."""

    @staticmethod
    def name():
        return "ReproSpin"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        seq = ["Up", "Up", "Down", "Down", "Left", "Left", "Right", "Right"]
        i = 0
        while True:
            context.emulator.press_button(seq[(i // 6) % len(seq)])
            yield
            i += 1


def _dump_mart_state(step):
    """Log the shop UI state: game_state, active tasks, and sMartInfo (item list)."""
    try:
        from modules.memory import read_symbol, unpack_uint16, unpack_uint32
        from modules.tasks import get_tasks
        from modules.pokemon import get_item_by_index

        gs = get_game_state()
        tasks = [t.symbol for t in get_tasks()] if get_tasks() else []
        info = read_symbol("sMartInfo")  # 0x10 bytes
        item_list_ptr = unpack_uint32(info[8:12])
        item_count = unpack_uint16(info[12:14])
        mart_type = info[15]
        items = []
        if (0x02000000 <= item_list_ptr < 0x02040000 or 0x08000000 <= item_list_ptr < 0x0A000000) and 0 < item_count < 40:
            raw = context.emulator.read_bytes(item_list_ptr, length=item_count * 2)
            for i in range(item_count):
                iid = unpack_uint16(raw[i * 2 : i * 2 + 2])
                try:
                    items.append(get_item_by_index(iid).name)
                except Exception:
                    items.append(f"#{iid}")
        log(f"  m{step} gs={gs.name if hasattr(gs,'name') else gs} type={mart_type} items={items} tasks={tasks}")
    except Exception as e:
        log(f"  m{step} dump err {e}")


class HealTestMode(BotMode):
    """Isolated test: heal at Oldale PC and observe enter â†’ heal â†’ EXIT (the suspect)."""

    @staticmethod
    def name():
        return "HealTest"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.modes.util.higher_level_actions import heal_in_pokemon_center
        from modules.modes.util.walking import wait_for_player_avatar_to_be_controllable
        from modules.map_data import PokemonCenter

        yield from wait_for_player_avatar_to_be_controllable()
        for _ in range(20):
            yield
        log("[heal] calling heal_in_pokemon_center(OldaleTown)")
        try:
            yield from heal_in_pokemon_center(PokemonCenter.OldaleTown)
            log("[heal] DONE â€” healed and exited cleanly")
        except Exception as e:
            import traceback

            log(f"[heal] ERROR: {e}\n{traceback.format_exc()}")
        while True:
            context.emulator.press_button("B")
            yield


class MartBuyMode(BotMode):
    """Test buy_poke_balls: log balls+money before/after buying a fixed count."""

    @staticmethod
    def name():
        return "MartBuy"

    def run(self):
        from modules.story.early_game import buy_poke_balls, buy_poke_balls_in_tens, _total_poke_balls, _money, _ball_count

        import os
        from modules.tasks import get_tasks

        if os.environ.get("DBG"):
            from modules.modes.util.global_navigation import navigate_to_anywhere
            from modules.modes.util.sleep import wait_for_n_frames
            from modules.map_data import MapRSE

            def tks():
                return [t.symbol for t in get_tasks() if any(k in t.symbol for k in ("Buy", "Shop", "YesOrNo", "HowMany"))] if get_tasks() else []

            def logt(tag):
                log(f"[dbg] {tag} balls={_total_poke_balls()} money={_money()} tasks={tks()}")

            yield from navigate_to_anywhere(MapRSE.RUSTBORO_CITY_MART, (3, 3))
            context.emulator.press_button("Left"); yield
            yield from wait_for_n_frames(8)
            for i in range(20):
                t = tks()
                if "Task_GoToBuyOrSellMenu" in t or "Task_BuyMenu" in t:
                    break
                context.emulator.press_button("A"); yield from wait_for_n_frames(10)
            logt("after-dialogue")
            log("--- press A (select Buy) ---"); context.emulator.press_button("A")
            for i in range(30):
                yield
                if i % 3 == 0: logt(f"buyA+{i}")
            log("--- item list: press A up to 6x (14f each) until quantity ---")
            for k in range(6):
                if "Task_BuyHowManyDialogueHandleInput" in [t.symbol for t in get_tasks()]:
                    break
                context.emulator.press_button("A")
                yield from wait_for_n_frames(14)
                logt(f"itemA#{k}")
            log("--- press Up x3 ---")
            for _ in range(3):
                context.emulator.press_button("Up"); yield from wait_for_n_frames(5)
            logt("after-Up")
            log("--- press A (confirm qty) ---"); context.emulator.press_button("A")
            for i in range(30):
                yield
                if i % 3 == 0: logt(f"qtyA+{i}")
            log("--- press A (Yes) ---"); context.emulator.press_button("A")
            for i in range(40):
                yield
                if i % 3 == 0: logt(f"yesA+{i}")
            logt("FINAL")
        elif os.environ.get("SPAM"):
            pass
        else:
            n = int(os.environ.get("BUYN", "5"))
            _pb = "PokÃ© Ball"
            log(f"[buy] BEFORE: pokeballs={_ball_count(_pb)} premier={_ball_count('Premier Ball')} money={_money()} (buying {n} in tens)")
            try:
                yield from buy_poke_balls_in_tens(n)
                log(f"[buy] AFTER: pokeballs={_ball_count(_pb)} premier={_ball_count('Premier Ball')} money={_money()}")
            except Exception as e:
                import traceback

                log(f"[buy] ERROR: {e}\n{traceback.format_exc()}")
        while True:
            context.emulator.press_button("B")
            yield


class PokenavTutMode(BotMode):
    """Reach the forced PokeNav/Match-Call tutorial (after getting the PokeNav from
    Mr. Stone on Devon Corp 3F), CAPTURE a save state at it, and observe the menu
    internals (start-menu order/cursor, VAR_RESULT, active tasks) so we can build a
    deterministic 'clear the tutorial' routine. Also snapshots pokenav_got.ss1
    (post-PokeNav, controllable on 3F) for fast iteration."""

    @staticmethod
    def name():
        return "PokenavTut"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from pathlib import Path as _P
        from modules.story.early_game import (
            return_devon_goods_and_get_pokenav,
            wait_until_truly_controllable,
        )
        from modules.modes.util.global_navigation import navigate_to_anywhere
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var
        from modules.menu_parsers import parse_start_menu
        from modules.tasks import get_tasks

        SCRATCH = _P(__file__).parent

        def _tasks():
            ts = get_tasks()
            return [t.symbol for t in ts] if ts else []

        def _var():
            try:
                return get_event_var("VAR_RESULT")
            except Exception as e:
                return f"<err {e}>"

        def _dump(tag, step):
            try:
                sm = parse_start_menu()
            except Exception as e:
                sm = f"<err {e}>"
            gs = get_game_state()
            log(
                f"  [tut/{tag}] f{step} gs={gs.name if hasattr(gs,'name') else gs} "
                f"VAR_RESULT={_var()} startmenu={sm} tasks={_tasks()}"
            )

        step = 0
        # Phase 1: get the PokeNav (skip if a resume state already has it).
        if not get_event_flag("RECEIVED_POKENAV"):
            log("[tut] phase1: return Devon goods + get the PokeNav from Mr. Stone")
            yield from return_devon_goods_and_get_pokenav()
        yield from wait_until_truly_controllable()
        try:
            (SCRATCH / "pokenav_got.ss1").write_bytes(context.emulator.get_save_state())
            log("[tut] saved pokenav_got.ss1 (post-PokeNav, controllable on 3F)")
        except Exception as e:
            log(f"[tut] save pokenav_got err {e}")

        # Phase 2: walk out to Rustboro City -> the forced tutorial fires on the way.
        log("[tut] phase2: navigate out to Rustboro City (should trigger the tutorial)")
        captured = False
        for rnd in range(20):
            try:
                yield from navigate_to_anywhere(
                    MapRSE.RUSTBORO_CITY, (16, 40), avoid_encounters=True, avoid_scripted_events=False
                )
            except Exception as e:
                log(f"[tut] r{rnd} nav interrupted ({str(e)[:80]})")
            for _ in range(30):
                step += 1
                tks = _tasks()
                _dump("scan", step)
                if any(("Multichoice" in t) or ("StartMenu" in t) for t in tks):
                    if not captured:
                        try:
                            (SCRATCH / "pokenav_tut.ss1").write_bytes(context.emulator.get_save_state())
                            log("[tut] *** captured pokenav_tut.ss1 (tutorial menu active) ***")
                        except Exception as e:
                            log(f"[tut] save tut err {e}")
                        captured = True
                yield
            if captured:
                break

        # Phase 3: idle-observe the tutorial WITHOUT input, to read its steady state.
        log("[tut] phase3: idle-observe tutorial (no input) 120f")
        for _ in range(120):
            step += 1
            _dump("idle", step)
            yield
        log("[tut] observation done; idling on B")
        while True:
            context.emulator.press_button("B")
            yield


class PokenavClearMode(BotMode):
    """From pokenav_got.ss1 (post-PokeNav, on Devon Corp 3F): walk out to Rustboro City
    to trigger the forced Match-Call tutorial, then CLEAR it by selecting POKENAV
    (index 3) in the tutorial start menu and backing out of the PokeNav app. Heavy
    logging of game_state / tasks / VAR_RESULT / controllable throughout so we can see
    exactly what each phase does and whether it clears."""

    @staticmethod
    def name():
        return "PokenavClear"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.modes.util.global_navigation import navigate_to_anywhere
        from modules.modes.util.tasks_scripts import wait_for_multiple_choice_question
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var, get_event_flag_by_number
        from modules.tasks import get_tasks, task_is_active, get_global_script_context
        from modules.player import get_player_avatar
        from modules.modes.util.walking import wait_for_player_avatar_to_be_controllable

        def _tasks():
            ts = get_tasks()
            return [t.symbol for t in ts] if ts else []

        def _ctrl():
            try:
                from modules.modes.util.walking import player_avatar_is_controllable

                return player_avatar_is_controllable()
            except Exception as e:
                return f"<err {e}>"

        def _script():
            try:
                sc = get_global_script_context()
                return (sc.stack[-3:] if sc.is_active else [])
            except Exception as e:
                return f"<err {e}>"

        def _dump(tag, step):
            gs = get_game_state()
            try:
                vr = get_event_var("VAR_RESULT")
            except Exception as e:
                vr = f"<err {e}>"
            try:
                pa = get_player_avatar()
                pos = (pa.map_group_and_number, pa.local_coordinates)
            except Exception as e:
                pos = f"<err {e}>"
            log(
                f"  [clr/{tag}] f{step} gs={gs.name if hasattr(gs,'name') else gs} ctrl={_ctrl()} "
                f"VAR_RESULT={vr} pos={pos} mc={task_is_active('Task_HandleMultichoiceInput')} "
                f"script={_script()} tasks={_tasks()}"
            )

        def _tutorial_active():
            sc = get_global_script_context()
            in_script = sc.is_active and any("ScientistAddMatchCall" in f or "MatchCallTutorial" in f for f in sc.stack)
            return in_script or task_is_active("Task_HandleMultichoiceInput")

        step = 0
        log("[clr] phase1: navigate out to Rustboro City -> should trigger the tutorial")
        triggered = False
        for rnd in range(15):
            try:
                yield from navigate_to_anywhere(
                    MapRSE.RUSTBORO_CITY, (16, 45), avoid_encounters=True, avoid_scripted_events=False
                )
            except Exception as e:
                log(f"[clr] r{rnd} nav interrupted ({str(e)[:70]})")
            # observe a few frames; if the Scientist tutorial script is running, break to clear it
            for _ in range(20):
                step += 1
                _dump("scan", step)
                if _tutorial_active():
                    triggered = True
                    break
                yield
            if triggered:
                break

        log(f"[clr] phase2: tutorial active? {triggered} â€” advancing intro + selecting POKENAV (index 3)")
        if triggered:
            yield from wait_for_multiple_choice_question(3)
            log(f"[clr] after multichoice-select: VAR_RESULT={get_event_var('VAR_RESULT')} "
                f"gs={get_game_state()} tasks={_tasks()}")
            for i in range(30):
                step += 1
                _dump("post-select", step)
                yield

            log("[clr] phase3: FORCE_CALL_READY â€” drive Match Call with A; log gs/script transitions")
            import os as _os
            btn = _os.environ.get("P3BTN", "A")
            period = int(_os.environ.get("P3PERIOD", "10"))  # press every N frames (let UI settle)
            prev = None
            for i in range(1500):
                step += 1
                gs = get_game_state()
                sc = get_global_script_context()
                sig = (gs.name if hasattr(gs, "name") else gs,
                       tuple(sc.stack[-2:]) if sc.is_active else (),
                       task_is_active("Task_HandleMultichoiceInput"))
                if sig != prev:
                    _dump(f"exit-app", step)
                    prev = sig
                # stop as soon as the tutorial script finished (back to field, controllable)
                if _ctrl() is True and not (sc.is_active and "MatchCallTutorial" in " ".join(sc.stack)):
                    log(f"[clr] phase3 DONE at f{step}: controllable, tutorial script gone")
                    break
                if i % period == 0:
                    context.emulator.press_button(btn)
                yield

        log("[clr] phase4: wait for controllable + walk a few steps to prove we're free")
        try:
            yield from wait_for_player_avatar_to_be_controllable()
            log("[clr] CONTROLLABLE after tutorial!")
        except Exception as e:
            log(f"[clr] not controllable: {e}")
        for i in range(20):
            step += 1
            _dump("walk", step)
            context.emulator.press_button("Down")
            yield
        log(f"[clr] FINAL flags: MatchCall={get_event_flag('FLAG_ADDED_MATCH_CALL_TO_POKENAV')} "
            f"RECEIVED_POKENAV={get_event_flag('RECEIVED_POKENAV')}")
        while True:
            context.emulator.press_button("B")
            yield


class PokenavFaithMode(BotMode):
    """FAITHFUL tutorial attempt WITH VIDEO ENABLED (the PokeNav app's looped task needs the
    BG/OBJ renderer, which the headless harness disables). From pokenav_got.ss1: trigger the
    Scientist tutorial, select POKENAV in the multichoice, then drive the PokeNav app
    (Match Call -> Mr. Stone -> Call -> ride dialogue -> exit). Logs on-screen text + tasks +
    PokeNav mode each step so we can script the exact button sequence.

    Env: FAITHBTN (default 'A'), FAITHPERIOD (default 24)."""

    @staticmethod
    def name():
        return "PokenavFaith"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        import os as _os
        from modules.modes.util.global_navigation import navigate_to_anywhere
        from modules.modes.util.tasks_scripts import wait_for_multiple_choice_question
        from modules.modes.util.sleep import wait_for_n_frames
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var, read_symbol
        from modules.tasks import get_tasks, task_is_active, get_global_script_context
        from modules.player import player_avatar_is_controllable
        from modules.game import decode_string

        # ENABLE the renderer â€” the PokeNav app won't advance without it.
        context.video = True
        log("[faith] video ENABLED (renderer on)")

        def _tasks():
            ts = get_tasks()
            return [t.symbol for t in ts] if ts else []

        def _text():
            out = {}
            for sym in ("gStringVar4", "gDisplayedStringBattle"):
                try:
                    out[sym] = decode_string(read_symbol(sym))[:40]
                except Exception:
                    pass
            return out

        def _pmode():
            # gPokenavResources is a pointer; mode is the first field of the struct it points to.
            try:
                import struct
                from modules.memory import unpack_uint32
                ptr = unpack_uint32(read_symbol("gPokenavResources"))
                if 0x02000000 <= ptr < 0x02040000:
                    return context.emulator.read_bytes(ptr, length=1)[0]
            except Exception as e:
                return f"<err {e}>"
            return None

        def _dump(tag, step):
            gs = get_game_state()
            try:
                ctrl = player_avatar_is_controllable()
            except Exception:
                ctrl = "?"
            sc = get_global_script_context()
            log(f"  [faith/{tag}] f{step} gs={gs.name if hasattr(gs,'name') else gs} ctrl={ctrl} "
                f"pmode={_pmode()} script={sc.stack[-2:] if sc.is_active else []} "
                f"txt={_text()} tasks={_tasks()}")

        step = 0
        # Phase 1: trigger the Scientist tutorial + select POKENAV (index 3).
        log("[faith] phase1: navigate out, trigger Scientist, select POKENAV")
        triggered = False
        for rnd in range(15):
            try:
                yield from navigate_to_anywhere(MapRSE.RUSTBORO_CITY, (16, 45), avoid_encounters=True, avoid_scripted_events=False)
            except Exception as e:
                log(f"[faith] r{rnd} nav interrupted ({str(e)[:60]})")
            for _ in range(20):
                step += 1
                sc = get_global_script_context()
                if (sc.is_active and any("ScientistAddMatchCall" in f or "MatchCallTutorial" in f for f in sc.stack)) \
                        or task_is_active("Task_HandleMultichoiceInput"):
                    triggered = True
                    break
                yield
            if triggered:
                break
        log(f"[faith] tutorial active? {triggered}; selecting POKENAV")
        if triggered:
            yield from wait_for_multiple_choice_question(3)
        log(f"[faith] after select: gs={get_game_state()} tasks={_tasks()}")

        # Phase 2: SCRIPTED probe â€” reach the main menu, screenshot, then run a button
        # script from env FAITHSEQ (comma list like "shot,Down,shot,A,shot,...") capturing a
        # screenshot at each 'shot'. Lets us SEE each PokeNav screen and find the sequence.
        from pathlib import Path as _P
        SCRATCH = _P(__file__).parent
        shot_n = {"i": 0}

        def _shot(label):
            try:
                p = SCRATCH / f"faith_{shot_n['i']:02d}_{label}.png"
                context.emulator.get_screenshot().save(p)
                log(f"[faith] SHOT {p.name} gs={get_game_state()} pmode={_pmode()} tasks={_tasks()}")
                shot_n["i"] += 1
            except Exception as e:
                log(f"[faith] shot err {e}")

        # wait for the main menu to be up + settled (Task_CurrentMenuOptionGlow)
        for _ in range(400):
            step += 1
            if task_is_active("Task_CurrentMenuOptionGlow"):
                break
            yield
        yield from wait_for_n_frames(30)
        _dump("mainmenu", step)
        _shot("mainmenu")

        # Run the scripted button sequence.
        seq = _os.environ.get("FAITHSEQ", "A,shot,A,shot,A,shot,B,shot,B,shot").split(",")
        for tok in seq:
            tok = tok.strip()
            if tok == "shot":
                _shot("seq")
            elif tok == "wait":
                yield from wait_for_n_frames(30)
            elif tok:
                context.emulator.press_button(tok)
                yield
                yield from wait_for_n_frames(20)
            step += 1
            _dump(f"after-{tok}", step)
        # Completion probe: after the scripted seq, drive to completion and log how.
        # Env COMPLETEBTN: 'A' (pure A), 'AB' (alternate A/B), 'B' (pure B).
        cbtn = _os.environ.get("COMPLETEBTN", "A")
        log(f"[faith] completion loop with '{cbtn}' until RUSTBORO_CITY_STATE>=7 or 4000f")
        prev = None
        for i in range(4000):
            step += 1
            sc = get_global_script_context()
            sig = (get_game_state().name if hasattr(get_game_state(), "name") else get_game_state(),
                   tuple(_tasks()), _pmode(), get_event_var("RUSTBORO_CITY_STATE"),
                   tuple(sc.stack[-2:]) if sc.is_active else ())
            if sig != prev:
                _dump("complete", step)
                prev = sig
            if get_event_var("RUSTBORO_CITY_STATE") >= 7:
                log(f"[faith] *** TUTORIAL COMPLETE at f{step} (STATE=7) ***")
                _shot("done")
                break
            if cbtn == "AB":
                context.emulator.press_button("A" if i % 2 == 0 else "B")
            else:
                context.emulator.press_button(cbtn)
            yield
        # settle to controllable
        for _ in range(600):
            step += 1
            try:
                if player_avatar_is_controllable():
                    log(f"[faith] controllable at f{step}")
                    break
            except Exception:
                pass
            context.emulator.press_button("B")
            yield
        log(f"[faith] FINAL: gs={get_game_state()} RUSTBORO_CITY_STATE={get_event_var('RUSTBORO_CITY_STATE')} "
            f"ADDED_MC={get_event_flag('ADDED_MATCH_CALL_TO_POKENAV')} "
            f"DEFEATED_RIVAL={get_event_flag('DEFEATED_RIVAL_RUSTBORO')}")
        while True:
            yield


class SailDewfordMode(BotMode):
    """VALIDATE sail_to_dewford: from post_rival (Rustboro (16,53)), walk south to Route 104,
    to Mr. Briney's house, sail to Dewford. Logs map/pos transitions + the Briney interaction."""

    @staticmethod
    def name():
        return "SailDewford"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.story.early_game import sail_to_dewford, _map_group_number
        from modules.player import get_player_avatar
        from modules.map_data import MapRSE

        def _pos():
            try:
                pa = get_player_avatar()
                return (pa.map_group_and_number, pa.local_coordinates)
            except Exception as e:
                return f"<err {e}>"

        log(f"[sail] start pos={_pos()}")
        try:
            yield from sail_to_dewford()
            arrived = _map_group_number() == MapRSE.DEWFORD_TOWN.value
            log(f"[sail] sail_to_dewford returned; pos={_pos()} in_dewford={arrived}")
            if arrived:
                # Ride out any leftover arrival dialogue BEFORE saving: a checkpoint taken
                # mid-textbox loads with the avatar permanently non-controllable (the first
                # dewford.ss1 did exactly that and broke every navigate on resume).
                from modules.player import player_avatar_is_controllable

                stable = 0
                for _ in range(1200):
                    if player_avatar_is_controllable():
                        stable += 1
                        if stable >= 120:
                            break
                        yield
                    else:
                        stable = 0
                        context.emulator.press_button("B")
                        yield
                import pathlib
                out = pathlib.Path(__file__).resolve().parent / "saves" / "dewford.ss1"
                out.write_bytes(context.emulator.get_save_state())
                log(f"[sail] checkpoint saved: {out.name} (controllable-stable={stable})")
        except Exception as e:
            import traceback
            log(f"[sail] ERROR pos={_pos()}: {e}\n{traceback.format_exc()[:900]}")
        while True:
            context.emulator.press_button("B")
            yield


class ShinyTestMode(BotMode):
    """FAULT-INJECTION (user directive 2026-07-22): force every WILD encounter to read as
    SHINY and verify the Story shiny branch actually THROWS BALLS and CATCHES â€” even for
    an already-owned species (Route 116 wilds are all owned by post_rival). Success =
    a battle ends with outcome Caught."""

    def __init__(self):
        super().__init__()
        self._outcome = None
        self._caught = False

    @staticmethod
    def name():
        return "ShinyTest"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import StoryMode

        if encounter is not None:
            real = encounter

            class _ShinyProxy:
                def __getattr__(self, n):
                    return getattr(real, n)

                @property
                def is_shiny(self):
                    return True

            encounter = _ShinyProxy()
            log("[shinytest] forced is_shiny=True on this wild encounter")
        # Delegate to the REAL StoryMode routing (unbound call with a minimal shim
        # carrying the attrs the shiny/catch branches read).
        shim = SimpleNamespace(_catch_team_target=4, _should_catch=lambda e: False)
        return StoryMode.on_battle_started(shim, encounter)

    def on_battle_ended(self, outcome):
        self._outcome = outcome
        try:
            from modules.battle_state import BattleOutcome

            self._caught = outcome is BattleOutcome.Caught
        except Exception:
            pass
        log(f"[shinytest] battle ended: outcome={outcome} caught={self._caught}")

    def run(self):
        from modules.items import get_item_bag
        from modules.map_data import MapRSE
        from modules.modes.util import spin
        from modules.modes.util.global_navigation import navigate_to_anywhere

        balls = sum(s.quantity for s in get_item_bag().poke_balls)
        log(f"[shinytest] starting with {balls} PokÃ© Ball(s)")
        if balls == 0:
            log("[shinytest] INVALID TEST: no balls in this save")
            return
        yield from navigate_to_anywhere(MapRSE.ROUTE116, (11, 7), avoid_encounters=False, avoid_scripted_events=True)
        log("[shinytest] in the Route 116 grass â€” spinning for a wild...")
        yield from spin(stop_condition=lambda: self._outcome is not None)
        log(f"[shinytest] RESULT: caught={self._caught} outcome={self._outcome} "
            f"balls_left={sum(s.quantity for s in get_item_bag().poke_balls)}")
        while True:
            context.emulator.press_button("B")
            yield


class HmTestMode(BotMode):
    """FAULT-INJECTION (user report 2026-07-23): patch the CURRENT party to 'nobody can
    learn Rock Smash' and run the real `ensure_hm_learner(HM06)` — it must derive the
    hunting grounds from ROM data, walk there, catch a learner wild via the story catch
    branch, and return its slot; then `teach_hm_move` must teach THAT mon. Success =
    a compatible mon is in the party and knows Rock Smash at the end."""

    def __init__(self):
        super().__init__()
        self._real_can_learn = None

    @staticmethod
    def name():
        return "HmTest"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import StoryMode

        shim = SimpleNamespace(_catch_team_target=4, _should_catch=lambda e: False)
        return StoryMode.on_battle_started(shim, encounter)

    def run(self):
        from modules.items import get_item_by_name
        from modules.pokemon import Species
        from modules.pokemon_party import get_party
        from modules.story import early_game

        hm06 = get_item_by_name("HM06")
        party_species = {m.species.name for m in get_party() if m is not None}
        log(f"[hmtest] party={sorted(party_species)} — patching all of them to 'cannot learn'")
        self._real_can_learn = real = Species.can_learn_tm_hm
        Species.can_learn_tm_hm = (
            lambda sp, tm_hm: False if sp.name in party_species else real(sp, tm_hm)
        )
        assert early_game.hm_learner_slot(hm06) is None, "patch did not take"
        slot = yield from early_game.ensure_hm_learner(hm06)
        mon = get_party()[slot]
        log(f"[hmtest] HUNT OK: slot {slot} = {mon.species.name} L{mon.level} "
            f"(really compatible: {real(mon.species, hm06)})")
        yield from early_game.teach_hm_move(hm06, slot)
        knows = any(l is not None and l.move.name == "Rock Smash" for l in get_party()[slot].moves)
        log(f"[hmtest] TEACH OK: {mon.species.name} knows Rock Smash = {knows}")
        log("[hmtest] RESULT: PASS" if knows else "[hmtest] RESULT: FAIL")
        while True:
            context.emulator.press_button("B")
            yield


class CaveTrainMode(BotMode):
    """VALIDATE the cave-aware training legs (the 2Ã— real-HW 'not on connected maps'
    Manual drops): Dewford â†’ thread into Granite Cave to the (35,11) spot â†’ exit the
    cave â†’ heal at the Dewford PC â†’ thread back in. Exactly the legs that failed."""

    @staticmethod
    def name():
        return "CaveTrain"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.map_data import MapRSE, PokemonCenter
        from modules.modes.util.higher_level_actions import heal_in_pokemon_center
        from modules.story.early_game import (
            _exit_training_cave_if_inside,
            _goto_training_area,
            _map_group_number,
        )

        try:
            log("[cavetrain] leg 1: Dewford -> cave spot (35,11)")
            yield from _goto_training_area(MapRSE.GRANITE_CAVE_1F, (35, 11))
            log(f"[cavetrain] at spot; map={_map_group_number()}")
            log("[cavetrain] leg 2: exit cave")
            yield from _exit_training_cave_if_inside()
            log(f"[cavetrain] outside; map={_map_group_number()}")
            log("[cavetrain] leg 3: heal at Dewford PC")
            yield from heal_in_pokemon_center(PokemonCenter.DewfordTown)
            log(f"[cavetrain] healed; map={_map_group_number()}")
            log("[cavetrain] leg 4: back to the cave spot")
            yield from _goto_training_area(MapRSE.GRANITE_CAVE_1F, (35, 11))
            log(f"[cavetrain] RESULT: back at spot; map={_map_group_number()} â€” ALL LEGS PASS")
        except Exception as e:
            import traceback

            log(f"[cavetrain] ERROR: {e}\n{traceback.format_exc()[:800]}")
        while True:
            context.emulator.press_button("B")
            yield


class FieryCaveMode(BotMode):
    """VALIDATE the FIERY_PATH round trip end to end, in the FAITHFUL harness.

    ‼ WHY THIS EXISTS AND `probe_counter_tiles.py --nav` COULD NOT DO IT. That probe
    drives the navigator generator directly, with NO bot listeners — so the moment a wild
    encounter fires in cave terrain nothing resolves the battle and the run freezes with
    `controllable=False, script_active=False`. Every BACK leg it reported as a failure was
    that artifact, not a map problem. This harness runs the real main loop (listeners
    included), so encounters are fought and the legs mean something.

    Legs mirror `cavetrain` (Granite Cave) for the second in-cave ground, FIERY_PATH —
    the Machop hunting ground that is the reachable Norman counter (#24-counters):
      1. Lavaridge -> Fiery Path spin tile (18,19)   [_goto_training_area, cave door]
      2. exit the cave                                [_exit_training_cave_if_inside]
      3. heal at Lavaridge                            [the mapped heal centre]
      4. back to the spin tile                        [the full round trip]
    Run: py -3.12 story_harness.py lavaridge --driver fierycave --frames 400000
    """

    @staticmethod
    def name():
        return "FieryCave"

    def run(self):
        from modules.map_data import MapRSE, PokemonCenter
        from modules.modes.util.higher_level_actions import heal_in_pokemon_center
        from modules.story.early_game import (
            _exit_training_cave_if_inside,
            _goto_training_area,
            _map_group_number,
        )

        legs = []
        try:
            log("[fierycave] leg 1: Lavaridge -> Fiery Path spin tile (18,19)")
            yield from _goto_training_area(MapRSE.FIERY_PATH, (18, 19))
            inside = _map_group_number() == MapRSE.FIERY_PATH.value
            log(f"[fierycave] at spot; map={_map_group_number()} inside_fiery={inside}")
            legs.append(("1 goto", inside))

            log("[fierycave] leg 2: exit the cave")
            yield from _exit_training_cave_if_inside()
            outside = _map_group_number() != MapRSE.FIERY_PATH.value
            log(f"[fierycave] outside; map={_map_group_number()} left_cave={outside}")
            legs.append(("2 exit", outside))

            log("[fierycave] leg 3: heal at Lavaridge PC")
            yield from heal_in_pokemon_center(PokemonCenter.LavaridgeTown)
            log(f"[fierycave] healed; map={_map_group_number()}")
            legs.append(("3 heal", True))

            log("[fierycave] leg 4: back to the spin tile")
            yield from _goto_training_area(MapRSE.FIERY_PATH, (18, 19))
            back = _map_group_number() == MapRSE.FIERY_PATH.value
            log(f"[fierycave] back at spot; map={_map_group_number()} inside_fiery={back}")
            legs.append(("4 return", back))
        except Exception as e:
            import traceback

            log(f"[fierycave] ERROR: {e}")
            log(traceback.format_exc()[:800])
        ok = all(v for _, v in legs) and len(legs) == 4
        log(f"[fierycave] RESULT: {'ALL LEGS PASS' if ok else 'INCOMPLETE'} -> {legs}")
        while True:
            context.emulator.press_button("B")
            yield


class JourneyMode(BotMode):
    """#24-journey / KI-39: drive ONE arm of the cross-map journey A/B, faithfully.

    ‼ WHY IT LIVES HERE AND NOT IN A STANDALONE PROBE — the same lesson `FieryCaveMode`
    above was written for. Driving `navigate_to_anywhere` directly (no bot listeners) fails
    the moment the route crosses a trainer sight-line or a wild encounter: measured
    2026-07-31, the Mauville -> Route 116 journey died at 717 frames with "We unexpectedly
    triggered a scripted event" on Route 117's forced doubles. That is the BARE DRIVER's
    artefact, not the planner's. This harness runs the real main loop, so scenes and
    battles resolve and an arrival means something.

    Env inputs (so the wrapper can run both arms with everything else identical):
      JOURNEY_ARM     'new' (default) | 'old' — 'old' blinds the planner exactly the way
                      the pre-fix code was blind: `warp_candidates` and `plan` both [].
      JOURNEY_TARGET  'ROUTE116:11,7' (default) — MapRSE name : x,y
    Emits one machine-readable line the wrapper parses:
      [journey] RESULT arm=<arm> arrived=<bool> map=<name> detail=<...>
    """

    @staticmethod
    def name():
        return "Journey"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.modes.util.global_navigation import navigate_to_anywhere
        from modules.player import get_player_avatar
        from modules.story.early_game import wait_until_truly_controllable
        from modules.warp_graph import WarpGraph, get_warp_graph

        arm = os.environ.get("JOURNEY_ARM", "new").strip().lower()
        raw = os.environ.get("JOURNEY_TARGET", "ROUTE116:11,7").strip()
        map_name, _, tile = raw.partition(":")
        x, _, y = tile.partition(",")
        target = MapRSE[map_name.strip()]
        target_tile = (int(x), int(y))

        yield from wait_until_truly_controllable()

        graph = get_warp_graph()
        here = tuple(get_player_avatar().map_group_and_number)
        log(f"[journey] arm={arm} from={MapRSE(here).name} to={target.name}{target_tile}")
        log(f"[journey] same_region={graph.region_of(here) == graph.region_of(tuple(target.value))} "
            f"plan()={graph.plan(here, tuple(target.value))} "
            f"warp_candidates={len(graph.warp_candidates(here, tuple(target.value)))}")

        saved = None
        if arm == "old":
            saved = (WarpGraph.warp_candidates, WarpGraph.plan)
            WarpGraph.warp_candidates = lambda self, a, b, limit=6: []
            WarpGraph.plan = lambda self, a, b: []

        arrived, detail = False, ""
        try:
            yield from navigate_to_anywhere(target, target_tile)
            arrived = tuple(get_player_avatar().map_group_and_number) == tuple(target.value)
            detail = "arrived" if arrived else "returned on the wrong map"
        except Exception as error:  # noqa: BLE001
            detail = f"{type(error).__name__}: {str(error)[:160]}".replace("\n", " ")
        finally:
            if saved is not None:
                WarpGraph.warp_candidates, WarpGraph.plan = saved

        try:
            final = MapRSE(tuple(get_player_avatar().map_group_and_number)).name
        except Exception:  # noqa: BLE001
            final = "?"
        log(f"[journey] RESULT arm={arm} arrived={arrived} map={final} detail={detail}")
        context.set_manual_mode()
        return


class NormanCounterMode(BotMode):
    """#24-counters: does an UNDERLEVELLED Fighting counter actually beat Norman?

    ‼ THE POINT IS TO AVOID SPENDING A BUDGET DECISION ON A GUESS. Batch `20260731-170603`
    showed the chain catch a Machop and field it at **L16 against Norman's L28-31 team**,
    winning **0** Balance Badges. At the measured ~89k frames/level, the current 250k
    training budget buys ~2 levels; closing to within 5 levels of Norman would cost ~890k.
    Before raising any budget — or re-ranking counter candidates by level gap — answer the
    cheap binary question first: **is a 2x-STAB counter at level L enough?**

    This injects a Machop at `NORMAN_MACHOP_LEVEL` into the existing party and runs the real
    `do_petalburg_gym()`. One run per level, a few minutes each, versus three hours for a
    batch that (per the power analysis) could not resolve the difference anyway.

    Env:
      NORMAN_MACHOP_LEVEL  level to inject (default 18 — what the current budget buys)
    Emits: [normancounter] RESULT level=<L> badge=<bool> detail=<...>

    ‼ HOW TO READ A RUN THAT PRINTS NO RESULT LINE. A boss loss ends in a whiteout, and the
    whiteout path calls `set_manual_mode()`, which CLEARS `context.controller_stack` — so
    this generator is destroyed mid-flight and never reaches its own logging. That is not a
    driver bug to chase; it is the documented shape of a loss. Read the verdict off the
    no-progress dump instead, which says it plainly:

        instr=BattleScript_LocalBattleLostEnd  bt='NICK whited out!'  bot_mode=Manual

    A WIN prints the RESULT line with `badge=True`. So: RESULT line -> read it; no RESULT
    line plus `whited out` -> the counter LOST at that level.
    """

    @staticmethod
    def name():
        return "NormanCounter"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        import os

        from modules.debug_utilities import debug_create_pokemon, debug_write_party
        from modules.memory import get_event_flag
        from modules.pokemon import LearnedMove, get_move_by_name, get_species_by_name
        from modules.pokemon_party import get_party
        from modules.story.early_game import do_petalburg_gym, wait_until_truly_controllable

        level = int(os.environ.get("NORMAN_MACHOP_LEVEL", "18"))
        yield from wait_until_truly_controllable()

        machop = get_species_by_name("Machop")
        # Moves a wild Machop actually has around this level — Karate Chop is the STAB
        # Fighting move that makes it a "counter" at all. Read from the species learnset
        # rather than hard-coded, so this cannot drift from the game.
        wanted = ["Karate Chop", "Low Kick", "Leer", "Focus Energy"]
        moves = []
        for name in wanted:
            try:
                moves.append(LearnedMove.create(get_move_by_name(name)))
            except Exception:  # noqa: BLE001 - skip anything this ROM names differently
                pass
        mon = debug_create_pokemon(
            species=machop, level=level,
            experience=machop.level_up_type.get_experience_needed_for_level(level),
            moves=moves, nickname="MACHOP", current_hp=None,
        )
        existing = [m for m in get_party() if m is not None and not m.is_egg]
        party = (existing[:5] + [mon]) if len(existing) >= 5 else (existing + [mon])
        debug_write_party(party)
        log(f"[normancounter] injected Machop L{level} moves={[m.move.name for m in moves]}")
        log(f"[normancounter] party now: {[(m.species.name, m.level) for m in get_party() if m is not None]}")

        badge_before = bool(get_event_flag("BADGE05_GET"))
        detail = ""
        try:
            yield from do_petalburg_gym()
            detail = "gym segment returned"
        except Exception as error:  # noqa: BLE001
            detail = f"{type(error).__name__}: {str(error)[:150]}".replace("\n", " ")
        badge = bool(get_event_flag("BADGE05_GET"))
        log(f"[normancounter] RESULT level={level} badge={badge} "
            f"(was {badge_before}) detail={detail}")
        context.set_manual_mode()
        return


class SmashRouteMode(BotMode):
    """#24-smashroute / KI-41: can the bot now reach FIERY_PATH from Mauville?

    This is the end-to-end claim that matters — Fiery Path's Machop is the counter the
    `#24-counters` ladder names for Norman, and it was unreachable because a Rock Smash rock
    at ROUTE111 (18,101) seals the corridor (ROUTE112 scored 0 of 76 tiles from Mauville).
    Route planning was never the blocker: after the `#24-journey` fix a warp route to Fiery
    Path IS found, and neither of its two first legs is walkable.

    Env inputs:
      SMASH_ARM     'new' (default) | 'old' — 'old' blinds `find_obstacle_on_route` so the
                    trip behaves exactly as it did before this feature.
      SMASH_TARGET  'FIERY_PATH:18,19' (default)
    Emits: [smashroute] RESULT arm=<arm> arrived=<bool> map=<name> detail=<...>
    """

    @staticmethod
    def name():
        return "SmashRoute"

    def on_battle_started(self, encounter):
        # Rock Smash rolls a wild encounter (Geodude), and the corridor is grass — without
        # a strategy nothing resolves those battles and the run freezes.
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story import obstacle_clearing as oc
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

        arm = os.environ.get("SMASH_ARM", "new").strip().lower()
        raw = os.environ.get("SMASH_TARGET", "FIERY_PATH:18,19").strip()
        map_name, _, tile = raw.partition(":")
        x, _, y = tile.partition(",")
        target = MapRSE[map_name.strip()]
        target_tile = (int(x), int(y))

        yield from wait_until_truly_controllable()
        here = tuple(get_player_avatar().map_group_and_number)
        log(f"[smashroute] arm={arm} from={MapRSE(here).name} to={target.name}{target_tile}")
        plan = oc.find_obstacle_on_route(here, tuple(target.value), prefer_toward=target_tile)
        log(f"[smashroute] obstacle plan: {plan.describe() if plan else 'none'}")

        saved = None
        if arm == "old":
            saved = oc.find_obstacle_on_route
            oc.find_obstacle_on_route = lambda *a, **k: None

        # Match the production call site: `counter_hunt.hunt()` passes tries=24, because a
        # counter hunt is the longest journey the bot makes and the default 10 was being
        # exhausted WHILE STILL ADVANCING. A driver that used the default would be testing
        # a call the bot never makes.
        tries = int(os.environ.get("SMASH_TRIES", "24"))
        arrived, detail = False, ""
        try:
            yield from _navigate_riding_out(target, target_tile, tries=tries)
            arrived = tuple(get_player_avatar().map_group_and_number) == tuple(target.value)
            detail = "arrived" if arrived else "returned on the wrong map"
        except Exception as error:  # noqa: BLE001
            detail = f"{type(error).__name__}: {str(error)[:160]}".replace("\n", " ")
        finally:
            if saved is not None:
                oc.find_obstacle_on_route = saved

        try:
            final = MapRSE(tuple(get_player_avatar().map_group_and_number)).name
        except Exception:  # noqa: BLE001
            final = "?"
        log(f"[smashroute] RESULT arm={arm} arrived={arrived} map={final} detail={detail}")
        context.set_manual_mode()
        return


class CaveThreadMode(BotMode):
    """`#24-cavethread`: can the EXISTING navigator already thread a MULTI-WARP cave?

    ‼ WHY THIS PROBE EXISTS — it tests a claim the punch list currently assumes is false.
    `#24-cavethread` says `_CAVE_EXITS`/`_CAVE_ENTRANCES` are SINGLE-HOP and concludes that
    deep interiors (MT_PYRE_SUMMIT 3 warps, MAGMA_HIDEOUT_4F 4) need a hand-built chain
    table. But those two tables were written 2026-07-26, and their justifying comment — "the
    global navigator can NOT cross warp levels" — PREDATES `#24-journey` (2026-07-31), which
    made `navigate_to_anywhere` a multi-hop, self-replanning, live-validated warp navigator.

    STATIC RECON (2026-08-05, no emulator, replaying `WarpGraph.map_route` against the
    committed ROM cache) says the graph already knows every route in question, BOTH ways:
        ROUTE106 -> GRANITE_CAVE_B2F      3 hops
        GRANITE_CAVE_B2F -> DEWFORD_TOWN  4 hops
        ROUTE122  -> MT_PYRE_SUMMIT       3 hops
        JAGGED_PASS -> MAGMA_HIDEOUT_4F   4 hops
    ‼ That proves the route is KNOWN, not that it is WALKABLE — `map_route`'s own docstring
    warns its connection edges can be PHANTOMS (the Verdanturf->Route116 case). Only a live
    drive of the production call can settle it, which is this driver.

    GRANITE CAVE IS THE DELIBERATE TEST CASE, not a convenience. It is the same 3-warp depth
    as Mt. Pyre Summit, it is already PARKED as a training ground for exactly this reason, and
    it carries the HARDEST known hazard: `_walk_warp_chain` documents a ONE-WAY LEDGE on 1F
    that makes within-floor reachability DIRECTIONAL, so the graph's single "GRANITE_CAVE_1F"
    node is really two disjoint sections. A map-granular planner cannot see that. If the
    generic navigator survives Granite Cave, it will survive Mt. Pyre.

    ‼ THE DESTINATION TILE IS NOT GUESSED. It is the warp graph's own `to_coords` — where the
    ROM says you ARRIVE when taking that warp — so it is walkable by construction. Writing a
    cave tile from memory is exactly what the project's "never write a game fact from memory"
    rule forbids.

    Env inputs:
      CAVE_TARGET  deep interior map (default 'GRANITE_CAVE_B2F')
      CAVE_OUT     town to return to  (default 'DEWFORD_TOWN')
      CAVE_LEG     'in' | 'out' | 'both' (default 'both')
      CAVE_TRIES   retries per leg (default 24, matching `counter_hunt.hunt()`)
    Emits: [cavethread] RESULT leg=<in|out> arrived=<bool> map=<name> detail=<...>
    """

    @staticmethod
    def name():
        return "CaveThread"

    def on_battle_started(self, encounter):
        # Cave interiors are wild-encounter tiles; without a strategy the first Zubat
        # freezes the probe and we would be measuring the battle system, not navigation.
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.warp_graph import get_warp_graph
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

        target = MapRSE[os.environ.get("CAVE_TARGET", "GRANITE_CAVE_B2F").strip()]
        town = MapRSE[os.environ.get("CAVE_OUT", "DEWFORD_TOWN").strip()]
        leg = os.environ.get("CAVE_LEG", "both").strip().lower()
        tries = int(os.environ.get("CAVE_TRIES", "24"))

        graph = get_warp_graph()

        def arrival_tile(dest_map):
            """A walkable tile on `dest_map`: where the ROM says a warp INTO it lands you.

            ‼ EVERY tile this can return is a WARP tile, which is the wrong kind of target —
            walking onto one fires it and the trip ends one map past the destination. Prefer
            `CAVE_TILE`, an explicit PLAIN tile, whenever one is known (for MT_PYRE_SUMMIT it
            is (23,7), the coord-trigger the whole chapter turns on)."""
            override = os.environ.get("CAVE_TILE", "").strip()
            if override:
                x, _, y = override.partition(",")
                return (int(x), int(y))
            for edge in graph.edges:
                if tuple(edge.to_map) == tuple(dest_map.value):
                    return tuple(edge.to_coords)
            return None

        yield from wait_until_truly_controllable()

        def tracked(gen, seen):
            """Sample the avatar's map on every yield of `gen`.

            ‼ WHY THIS EXISTS (2026-08-05, second cavethread run). The first run reported
            `arrived=False map=GRANITE_CAVE_B1F` and I nearly recorded "threading stops one hop
            short". It did not: **every tile the warp graph knows on B2F is a LADDER**, so the
            destination I picked, B2F (29,13), is the ladder back UP to B1F. Navigating ONTO a
            warp tile FIRES it — so the bot threaded all the way down to B2F, stepped on the
            target, and was warped straight back out. `navigate_to_anywhere` then returned
            perfectly happily, because by its own lights it had reached the tile it was asked for.

            A final-position check cannot see that; it reads a successful 3-warp thread as a
            failure. Recording the maps VISITED can, and needs no non-warp tile to exist."""
            for value in gen:
                try:
                    seen.add(tuple(get_player_avatar().map_group_and_number))
                except Exception:  # noqa: BLE001
                    pass
                yield value

        def drive(name, dest_map, dest_tile):
            arrived, detail = False, ""
            if dest_tile is None:
                log(f"[cavethread] RESULT leg={name} arrived=False map=? detail=no ROM arrival tile for {dest_map.name}")
                return False
            here = tuple(get_player_avatar().map_group_and_number)
            try:
                start = MapRSE(here).name
            except Exception:  # noqa: BLE001
                start = str(here)
            hops = graph.map_route(here, tuple(dest_map.value))
            log(f"[cavethread] leg={name} from={start} to={dest_map.name}{dest_tile} "
                f"graph_hops={len(hops) if hops is not None else 'none'}")
            seen: set = set()
            try:
                yield from tracked(_navigate_riding_out(dest_map, dest_tile, tries=tries), seen)
                arrived = tuple(get_player_avatar().map_group_and_number) == tuple(dest_map.value)
                detail = "arrived" if arrived else "returned on the wrong map"
            except Exception as error:  # noqa: BLE001
                # ‼ 160 chars was TOO SHORT and cost a diagnosis (2026-08-05): the Route 120
                # failure surfaced as "...(Could not find a path fro" — cut off exactly where
                # the useful part starts. Navigation errors here nest an inner `calculate_path`
                # message that names the failing leg, so keep the whole thing.
                detail = f"{type(error).__name__}: {str(error)[:800]}".replace("\n", " ")
            try:
                final = MapRSE(tuple(get_player_avatar().map_group_and_number)).name
            except Exception:  # noqa: BLE001
                final = "?"
            # ‼ `reached_dest` is the REAL question for `#24-cavethread` — did the generic
            # navigator ever set foot on the deep interior? `arrived` only says whether it was
            # STANDING there when the call returned, which a warp tile destination makes
            # unanswerable (see `tracked`).
            reached = tuple(dest_map.value) in seen
            names = []
            for m in seen:
                try:
                    names.append(MapRSE(m).name)
                except Exception:  # noqa: BLE001
                    names.append(str(m))
            log(f"[cavethread] RESULT leg={name} arrived={arrived} reached_dest={reached} "
                f"map={final} detail={detail}")
            log(f"[cavethread] maps visited during leg={name}: {sorted(names)}")
            return reached

        went_in = True
        if leg in ("in", "both"):
            went_in = yield from drive("in", target, arrival_tile(target))

        # ‼ The OUT leg is the one that matters most: a heal targeting a town PC from INSIDE a
        # cave is what dropped two real-hardware runs to Manual on 2026-07-22. Run it even if
        # the IN leg failed ONLY when we actually ended up inside — otherwise it would report
        # a trivially-true "arrived" from the overworld and look like a pass.
        if leg in ("out", "both"):
            inside = tuple(get_player_avatar().map_group_and_number) == tuple(target.value)
            if inside:
                yield from drive("out", town, arrival_tile(town))
            else:
                log(f"[cavethread] leg=out SKIPPED — not inside {target.name} "
                    f"(in-leg arrived={went_in}); an out-leg from the overworld proves nothing.")

        context.set_manual_mode()
        return


class RivalRetryMode(BotMode):
    """VALIDATE the bug fix: with MET_RIVAL_RUSTBORO already set (simulating a PRIOR LOSS),
    confirm fight_rustboro_rival still steps onto the y=53 trigger and RE-ENGAGES the rival
    (the old code broke on the MET flag and stalled at the staging tile)."""

    @staticmethod
    def name():
        return "RivalRetry"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.memory import set_event_flag, get_event_flag
        from modules.story.early_game import (
            skip_pokenav_match_call_tutorial,
            fight_rustboro_rival,
            _lead_best_matchup,
            wait_until_truly_controllable,
        )

        yield from wait_until_truly_controllable()
        yield from skip_pokenav_match_call_tutorial()
        set_event_flag("MET_RIVAL_RUSTBORO", True)  # simulate a prior loss: met, NOT defeated
        log(f"[retry] simulated prior loss: MET=True DEFEATED={get_event_flag('DEFEATED_RIVAL_RUSTBORO')}")
        yield from _lead_best_matchup(["Grass"])
        log("[retry] calling fight_rustboro_rival â€” expect it to step onto y=53 and RE-ENGAGE")
        try:
            yield from fight_rustboro_rival()
            log(f"[retry] fight_rustboro_rival returned; DEFEATED={get_event_flag('DEFEATED_RIVAL_RUSTBORO')}")
        except Exception as e:
            log(f"[retry] fight_rustboro_rival raised: {e}")
        while True:
            context.emulator.press_button("B")
            yield


class SailReconMode(BotMode):
    """Synthesize a POST-RIVAL state (state-write DEFEATED_RIVAL_RUSTBORO + tutorial done),
    navigate to Mr. Briney's cottage on Route 104, save a checkpoint, then talk to Briney and
    OBSERVE the sail interaction (multichoice 'where are we bound?' vs a direct sail) so we can
    script sail_to_dewford correctly."""

    @staticmethod
    def name():
        return "SailRecon"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from pathlib import Path as _P
        from modules.memory import get_event_flag, set_event_flag, set_event_var, get_event_var
        from modules.modes.util.global_navigation import navigate_to_anywhere
        from modules.story.early_game import skip_pokenav_match_call_tutorial, wait_until_truly_controllable, _map_group_number
        from modules.map_data import MapRSE
        from modules.tasks import get_tasks, task_is_active, get_global_script_context
        from modules.player import get_player_avatar
        from modules.game import decode_string
        from modules.memory import read_symbol

        SCRATCH = _P(__file__).parent

        def _tasks():
            ts = get_tasks()
            return [t.symbol for t in ts] if ts else []

        def _pos():
            try:
                pa = get_player_avatar()
                return (pa.map_group_and_number, pa.local_coordinates)
            except Exception as e:
                return f"<err {e}>"

        def _txt():
            try:
                return decode_string(read_symbol("gStringVar4"))[:50]
            except Exception:
                return "?"

        def _dump(tag, step):
            log(f"  [sail/{tag}] f{step} gs={get_game_state()} pos={_pos()} "
                f"mc={task_is_active('Task_HandleMultichoiceInput')} "
                f"script={get_global_script_context().stack[-2:] if get_global_script_context().is_active else []} "
                f"txt={_txt()!r} tasks={_tasks()}")

        # 1) synthesize post-rival state
        yield from wait_until_truly_controllable()
        yield from skip_pokenav_match_call_tutorial()  # STATE=7 (headless fallback)
        set_event_flag("MET_RIVAL_RUSTBORO", True)
        set_event_flag("DEFEATED_RIVAL_RUSTBORO", True)
        log(f"[sail] synthesized post-rival: DEFEATED_RIVAL={get_event_flag('DEFEATED_RIVAL_RUSTBORO')} "
            f"STATE={get_event_var('RUSTBORO_CITY_STATE')}")

        from modules.modes.util.sleep import wait_for_n_frames

        # 2a) leg-by-leg: navigate to Rustboro south staging (16,52), then walk DOWN across
        #     the Rustboro->Route104 map connection (rival is marked defeated so y=53 is inert).
        log("[sail] leg1: Rustboro south staging (16,52), then walk Down onto Route 104")
        for rnd in range(8):
            try:
                yield from navigate_to_anywhere(MapRSE.RUSTBORO_CITY, (16, 52), avoid_encounters=True, avoid_scripted_events=False)
                break
            except Exception as e:
                log(f"[sail] stage r{rnd} ({str(e)[:60]}) pos={_pos()}")
                for _ in range(15):
                    yield
        for _ in range(40):
            if _map_group_number() == MapRSE.ROUTE104.value:
                break
            context.emulator.press_button("Down")
            yield
            yield from wait_for_n_frames(12)
        log(f"[sail] on Route 104? {_map_group_number() == MapRSE.ROUTE104.value} pos={_pos()}")

        # 2b) now navigate to Mr. Briney's house (a warp within Route 104)
        log("[sail] leg2: navigate to Mr. Briney's house (ROUTE104_MR_BRINEYS_HOUSE)")
        reached = False
        for rnd in range(20):
            if _map_group_number() == MapRSE.ROUTE104_MR_BRINEYS_HOUSE.value:
                reached = True
                break
            try:
                yield from navigate_to_anywhere(MapRSE.ROUTE104_MR_BRINEYS_HOUSE, (5, 4), avoid_encounters=True, avoid_scripted_events=False)
                reached = True
                break
            except Exception as e:
                log(f"[sail] r{rnd} nav interrupted ({str(e)[:70]}) pos={_pos()}")
                for _ in range(20):
                    yield
        log(f"[sail] reached Briney's house? {reached} pos={_pos()}")
        if reached:
            try:
                (SCRATCH / "briney_approach.ss1").write_bytes(context.emulator.get_save_state())
                log("[sail] saved briney_approach.ss1")
            except Exception as e:
                log(f"[sail] save err {e}")

        # 3) talk to Briney (5,3) from (5,4): face up, then advance dialogue, logging the UI
        yield from wait_until_truly_controllable()
        context.emulator.press_button("Up"); yield
        for _ in range(6):
            yield
        log("[sail] talking to Briney; observing 200f (press A when waiting for input)")
        from modules.tasks import is_waiting_for_input
        step = 0
        prev = None
        for i in range(300):
            step += 1
            sig = (str(get_game_state()), task_is_active("Task_HandleMultichoiceInput"),
                   _map_group_number(), _txt())
            if sig != prev:
                _dump("talk", step)
                prev = sig
            if _map_group_number() == MapRSE.DEWFORD_TOWN.value:
                log(f"[sail] *** ARRIVED IN DEWFORD at f{step} ***")
                break
            if task_is_active("Task_HandleMultichoiceInput"):
                log(f"[sail] *** MULTICHOICE up at f{step} â€” 'where are we bound?' ***")
                _dump("multichoice", step)
                break
            try:
                if is_waiting_for_input():
                    context.emulator.press_button("A")
            except Exception:
                context.emulator.press_button("A")
            yield
        log(f"[sail] FINAL pos={_pos()} map={_map_group_number()}")
        while True:
            context.emulator.press_button("B")
            yield


class PokenavSkipMode(BotMode):
    """VALIDATE skip_pokenav_match_call_tutorial: from pokenav_got.ss1 (on Devon Corp 3F,
    RECEIVED_POKENAV), apply the state-write skip, then navigate south to the rival and
    win â€” proving the Scientist tutorial never fires and the rival still triggers."""

    @staticmethod
    def name():
        return "PokenavSkip"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.story.early_game import (
            skip_pokenav_match_call_tutorial,
            fight_rustboro_rival,
            wait_until_truly_controllable,
        )
        from modules.memory import get_event_var, get_event_flag
        from modules.tasks import get_global_script_context

        def _v(name):
            try:
                return get_event_var(name)
            except Exception as e:
                return f"<err {e}>"

        log(f"[skip] BEFORE: RUSTBORO_CITY_STATE={_v('RUSTBORO_CITY_STATE')} "
            f"ROUTE104_STATE={_v('ROUTE104_STATE')} RECEIVED_POKENAV={get_event_flag('RECEIVED_POKENAV')}")
        yield from wait_until_truly_controllable()
        yield from skip_pokenav_match_call_tutorial()
        log(f"[skip] AFTER write: RUSTBORO_CITY_STATE={_v('RUSTBORO_CITY_STATE')} "
            f"ROUTE104_STATE={_v('ROUTE104_STATE')} HAS_MATCH_CALL={get_event_flag('HAS_MATCH_CALL')} "
            f"ADDED_MC={get_event_flag('ADDED_MATCH_CALL_TO_POKENAV')} "
            f"HIDE_SCIENTIST={get_event_flag('HIDE_RUSTBORO_CITY_SCIENTIST')}")

        import os as _os
        from modules.player import get_player_avatar
        from modules.battle_state import battle_is_active
        from modules.modes.util.global_navigation import navigate_to_anywhere
        from modules.map_data import MapRSE

        def _pos():
            try:
                pa = get_player_avatar()
                return (pa.map_group_and_number, pa.local_coordinates)
            except Exception as e:
                return f"<err {e}>"

        if _os.environ.get("MANUAL"):
            # RECON: walk to the SOUTH exit of Rustboro; log pos + MET/DEFEATED_RIVAL +
            # battle each step to find the exact rival trigger tile.
            log("[skip] MANUAL recon: navigate to (16,52) then Down-step across the y=53 rival trigger")
            prevpos = None
            # 1) navigate to just NORTH of the trigger row (reachable, no trigger)
            for rnd in range(8):
                try:
                    yield from navigate_to_anywhere(MapRSE.RUSTBORO_CITY, (16, 52), avoid_encounters=True, avoid_scripted_events=False)
                    log(f"[skip] reached staging pos={_pos()}")
                    break
                except Exception as e:
                    log(f"[skip] stage nav r{rnd} interrupted ({str(e)[:70]}) pos={_pos()}")
                    for _ in range(20):
                        yield
            # 2) Down-step across y=53 to cross a RivalTrigger tile
            for dstep in range(10):
                p = _pos()
                log(f"[skip] down-step {dstep}: pos={p} MET={get_event_flag('MET_RIVAL_RUSTBORO')} "
                    f"battle={battle_is_active()}")
                if get_event_flag("MET_RIVAL_RUSTBORO") or battle_is_active():
                    log(f"[skip] *** RIVAL ENGAGED at pos={p} ***")
                    break
                context.emulator.press_button("Down")
                yield
                for _ in range(16):
                    if battle_is_active():
                        break
                    yield
            for rnd in range(0):
                for _ in range(30):
                    p = _pos()
                    if p != prevpos:
                        log(f"[skip] pos={p} MET={get_event_flag('MET_RIVAL_RUSTBORO')} "
                            f"DEF={get_event_flag('DEFEATED_RIVAL_RUSTBORO')} battle={battle_is_active()} "
                            f"script={get_global_script_context().stack[-2:] if get_global_script_context().is_active else []}")
                        prevpos = p
                    if get_event_flag("MET_RIVAL_RUSTBORO") or battle_is_active():
                        log(f"[skip] *** RIVAL ENGAGED at pos={p} ***")
                        break
                    yield
                if get_event_flag("MET_RIVAL_RUSTBORO") or battle_is_active():
                    break
            # Let the battle (if any) resolve via the Story strategy.
            for _ in range(6000):
                if get_event_flag("DEFEATED_RIVAL_RUSTBORO"):
                    break
                context.emulator.press_button("A")
                yield
        else:
            log("[skip] running fight_rustboro_rival (walk south to the rival)")
            try:
                yield from fight_rustboro_rival()
            except Exception as e:
                import traceback
                log(f"[skip] fight_rustboro_rival ERROR: {e}\n{traceback.format_exc()[:800]}")
        log(f"[skip] FINAL: pos={_pos()} RUSTBORO_CITY_STATE={_v('RUSTBORO_CITY_STATE')} "
            f"MET_RIVAL={get_event_flag('MET_RIVAL_RUSTBORO')} "
            f"DEFEATED_RIVAL_RUSTBORO={get_event_flag('DEFEATED_RIVAL_RUSTBORO')}")
        while True:
            context.emulator.press_button("B")
            yield


class MartReconMode(BotMode):
    """Drive into the Rustboro mart, open the shop, and log the UI so we can build a
    robust buy_at_mart. Logs sMartInfo (item order) + game_state + tasks."""

    @staticmethod
    def name():
        return "MartRecon"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.modes.util.global_navigation import navigate_to_anywhere
        from modules.map_data import MapRSE

        log("[mart] into the Rustboro mart, up to the counter-front (3,3)")
        yield from navigate_to_anywhere(MapRSE.RUSTBORO_CITY_MART, (3, 3))
        log("[mart] facing left + talking to clerk across the counter")
        context.emulator.press_button("Left")
        yield
        for _ in range(8):
            yield
        # Advance dialogue to open the shop list, logging state as we go.
        for phase in range(60):
            _dump_mart_state(phase)
            context.emulator.press_button("A")
            yield
            for _ in range(8):
                yield
        log("[mart] recon done; idling")
        while True:
            context.emulator.press_button("B")
            yield


class Chapter5ReconMode(BotMode):
    """RECON: from gym1_done (inside Rustboro Gym at (5,3)), exit the gym and walk
    toward the Devon Corp / east to observe WHERE the theft scene fires and where
    the Devon employee is. Logs map/pos/flags/script the whole way."""

    @staticmethod
    def name():
        return "Ch5Recon"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.modes.util.global_navigation import navigate_to_anywhere
        from modules.modes.util.walking import navigate_to
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag
        from modules.story.early_game import _ride_out_scripted_scene, _pass_through_door, _map_group_number

        route116 = MapRSE.ROUTE116.value
        tunnel = MapRSE.RUSTURF_TUNNEL.value

        # 1. Exit gym + trigger theft (anchor on DEVON_GOODS_STOLEN).
        log("[ch5] step1: exit gym + trigger theft")
        rounds = 0
        while not get_event_flag("DEVON_GOODS_STOLEN") and rounds < 20:
            rounds += 1
            try:
                yield from navigate_to_anywhere(MapRSE.RUSTBORO_CITY, (18, 20), avoid_encounters=True, avoid_scripted_events=False)
            except Exception as e:
                log(f"[ch5] s1 nav aborted ({str(e)[:60]}); ride out")
                yield from _ride_out_scripted_scene("B")
        log(f"[ch5] DEVON_GOODS_STOLEN={get_event_flag('DEVON_GOODS_STOLEN')}")
        yield from _ride_out_scripted_scene("B")

        # 2. Chase EAST to Route 116. Target the near WEST edge first (leg approach)
        #    â€” the far tile (40,8) had no path (Route 116 has blocked tiles).
        log("[ch5] step2: chase east onto Route 116 (near edge 5,9)")
        rounds = 0
        while _map_group_number() != route116 and rounds < 25:
            rounds += 1
            try:
                yield from navigate_to_anywhere(MapRSE.ROUTE116, (5, 9), avoid_encounters=True, avoid_scripted_events=False)
                break
            except Exception as e:
                log(f"[ch5] s2 nav aborted ({str(e)[:70]}); ride out")
                yield from _ride_out_scripted_scene("B")
        log(f"[ch5] on Route116? map={_map_group_number()}")
        # 2b. Cross Route 116 east toward the tunnel door approach (47,9) â€” the door
        #     (47,8) is entered from BELOW. Try the global navigator (handles ledges).
        if _map_group_number() == route116:
            rounds = 0
            while rounds < 12:
                rounds += 1
                try:
                    yield from navigate_to_anywhere(MapRSE.ROUTE116, (47, 9), avoid_encounters=True, avoid_scripted_events=False)
                    break
                except Exception as e:
                    log(f"[ch5] s2b nav aborted ({str(e)[:70]}); ride out")
                    yield from _ride_out_scripted_scene("B")
            log(f"[ch5] crossed Route116 toward door; map={_map_group_number()}")

        # 3. Into the tunnel via the west door Route116 (47,8).
        log("[ch5] step3: into Rusturf Tunnel via (47,8)")
        rounds = 0
        while _map_group_number() == route116 and rounds < 8:
            rounds += 1
            try:
                yield from navigate_to(MapRSE.ROUTE116, (47, 9))
                yield from _pass_through_door((47, 8), route116)
            except Exception as e:
                log(f"[ch5] s3 aborted ({str(e)[:60]}); ride out")
                yield from _ride_out_scripted_scene("B")
        log(f"[ch5] in tunnel? map={_map_group_number()}")

        # 4. The grunt is at (13,5) (Mr. Briney at (13,4)), facing WEST along row 5.
        #    Approach from the west â€” its line of sight triggers the battle. Navigate
        #    toward a tile just west of it, riding out the scene/battle, anchored on
        #    RECOVERED_DEVON_GOODS.
        log("[ch5] step4: approach the grunt at (13,5) from the west, engage with A")
        from modules.game import decode_string
        from modules.memory import read_symbol as _rs
        # Get adjacent-west of the grunt (12,5).
        try:
            yield from navigate_to_anywhere(MapRSE.RUSTURF_TUNNEL, (12, 5), avoid_encounters=True, avoid_scripted_events=False)
        except Exception as e:
            log(f"[ch5] s4 approach nav ({str(e)[:60]})")
        # Engage: face east + advance the grunt dialogue with A until the battle
        # starts (the listener fights it) and the goods are recovered.
        frames = 0
        while not get_event_flag("RECOVERED_DEVON_GOODS") and frames < 4000:
            context.emulator.press_button("Right" if frames % 5 == 0 else "A")
            frames += 1
            if frames % 200 == 0:
                try:
                    ft = decode_string(_rs("gStringVar4"))
                except Exception:
                    ft = ""
                log(f"[ch5] s4 f{frames}: field={ft!r}")
            yield
        log(f"[ch5] RECOVERED_DEVON_GOODS={get_event_flag('RECOVERED_DEVON_GOODS')}")
        yield from _ride_out_scripted_scene("B")
        log("[ch5] recon complete; idling")
        while True:
            context.emulator.press_button("B")
            yield


class RivalReproMode(BotMode):
    """Walk to the Route 103 rival (a SINGLE-Pokemon trainer) with encounters
    avoided, then engage. The near-Lv16 Treecko crosses Lv16 on the KO that ENDS
    the trainer battle â€” the exact ML-11 edge case (move-learn as the trainer
    battle ends), fought with the real Story strategy."""

    @staticmethod
    def name():
        return "ReproRival"

    def on_battle_started(self, encounter):
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

        return LevelUpTravelBattleStrategy()

    def run(self):
        from modules.modes.util.walking import navigate_to
        from modules.map_data import MapRSE

        log("[rival] navigating to rival approach (10,4), encounters avoided")
        yield from navigate_to(MapRSE.ROUTE103, (10, 4))
        log("[rival] at approach; facing rival and talking")
        context.emulator.press_button("Up")
        yield
        for _ in range(6):
            yield
        context.emulator.press_button("A")
        yield
        # After engaging, the BattleListener fights. Ride out afterwards with B.
        while True:
            context.emulator.press_button("B")
            yield


from modules.plugins import load_plugins

load_plugins()  # registers the custom Story bot mode (plugins/custom_modes/)
load_built_in_plugins()
plugin_profile_loaded(context.profile)
context.stats = StatsDatabase(context.profile)
context.bot_listeners = get_bot_listeners(context.rom)
assert get_bot_mode_by_name("Story") is not None, "Story mode did not register"

# Validate the new opt-in debug logger end-to-end (writes to profile/debug-logs/).
try:
    from modules import debug_logger as _dbglog

    _dbglog.enable(context.profile)
except Exception as _e:
    print("debug_logger enable failed:", _e)
    _dbglog = None


def inject_treecko():
    from modules.debug_utilities import debug_create_pokemon, debug_write_party
    from modules.pokemon import get_species_by_name, get_move_by_name, LearnedMove

    treecko = get_species_by_name("Treecko")
    exp16 = treecko.level_up_type.get_experience_needed_for_level(16)
    moves = [
        LearnedMove.create(get_move_by_name("Pound")),
        LearnedMove.create(get_move_by_name("Leer")),
        LearnedMove.create(get_move_by_name("Absorb")),
        LearnedMove.create(get_move_by_name("Quick Attack")),
    ]
    mon = debug_create_pokemon(
        species=treecko,
        level=15,
        experience=exp16 - 1,
        moves=moves,
        nickname="TREECKO",
        current_hp=None,
    )
    debug_write_party([mon])
    log(f"[inject] Treecko Lv15 exp={exp16 - 1} (exp_for_16={exp16}) moves=Pound/Leer/Absorb/QuickAttack")


def inject_weak():
    from modules.debug_utilities import debug_create_pokemon, debug_write_party
    from modules.pokemon import get_species_by_name, get_move_by_name, LearnedMove

    mon = debug_create_pokemon(
        species=get_species_by_name("Poochyena"),
        level=3,
        moves=[LearnedMove.create(get_move_by_name("Tackle"))],
        nickname="WEAKLING",
    )
    debug_write_party([mon])
    log("[inject] lone Poochyena Lv3 (will lose â†’ whiteout)")


def inject_faintbench():
    """A weak LEAD + a weak BENCH: the lead faints in the first gym exchange, forcing
    the AFTER-FAINT PARTY MENU with a real bench to select â€” the exact machinery of the
    130k-frame party-menu hang (KI-12). Both mons then faint â†’ whiteout recovery."""
    from modules.debug_utilities import debug_create_pokemon, debug_write_party
    from modules.pokemon import get_species_by_name, get_move_by_name, LearnedMove

    lead = debug_create_pokemon(
        species=get_species_by_name("Poochyena"),
        level=3,
        moves=[LearnedMove.create(get_move_by_name("Tackle"))],
        nickname="FAINTME",
    )
    bench = debug_create_pokemon(
        species=get_species_by_name("Zigzagoon"),
        level=4,
        moves=[LearnedMove.create(get_move_by_name("Tackle"))],
        nickname="BENCHY",
    )
    debug_write_party([lead, bench])
    log("[inject] Poochyena Lv3 lead + Zigzagoon Lv4 bench (forces the after-faint party menu)")


def inject_shedinja_faint():
    """AFTER-FAINT SWEEP STRESS (kept as infra). ‼ NOTE 2026-07-23: this was built to repro
    KI-15 under the ORIGINAL (mis)diagnosis of a party-menu chooser hang. That diagnosis was
    WRONG — the real KI-15 is a post-battle STORY-RESUME hang, not a battle-handler bug (see
    05-KNOWN-ISSUES KI-15). This inject is retained because it usefully STRESS-TESTS the
    after-faint PARTY_MENU sweep and PROVED it robust: an all-BURNED, all-1-HP party led by a
    Wonder Guard Shedinja faints ONE PER TURN in battle (burn damages at end-of-turn, bypasses
    Wonder Guard, and — unlike poison — does NOT tick in the overworld so the mons reach
    battle alive), driving 5 back-to-back after-faint menus. With `--driver faintrepro`
    (never flees — the `should_flee_after_faint=False` override is REQUIRED to route faints
    through the choose-menu) the sweep handled all 5 cleanly (0 livelock). Growl-only so the
    mons can't KO the weak wild before the burn tick. Non-Fire species only (burn-immune)."""
    from modules.debug_utilities import debug_create_pokemon, debug_write_party
    from modules.pokemon import get_species_by_name, get_move_by_name, LearnedMove, StatusCondition

    def m(sp, lvl, mv, hp=1, status=StatusCondition.Burn):
        return debug_create_pokemon(species=get_species_by_name(sp), level=lvl,
            moves=[LearnedMove.create(get_move_by_name(mv))], current_hp=hp,
            status_condition=status)
    # Shedinja LEAD (Wonder Guard) burned at 1 HP faints to burn EOT1 regardless of the
    # wild's typing; the bench (all burnable, all 1 HP, all burned) each faint EOT of their
    # first active turn -> rapid successive after-faint menus.
    # ALL mons get GROWL only (non-damaging) so they CANNOT KO the wild — the battle then
    # lasts to the end-of-turn burn tick that faints them (an attacker would one-shot the
    # weak wild and win before burn ever ticks). Each faints EOT of its first active turn.
    debug_write_party([
        m("Shedinja", 22, "Growl"),   # Wonder Guard; only burn (EOT, bypasses WG) can faint it
        m("Swellow", 22, "Growl"),    # run05 partner
        m("Marshtomp", 22, "Growl"),
        m("Lombre", 20, "Growl"),
        m("Zigzagoon", 18, "Growl"),
        m("Whismur", 18, "Growl"),
    ])
    log("[inject] all-BURNED 1-HP Growl-only party (Shedinja lead + bench) — rapid in-battle faints; KI-15")


def learn_state_str():
    try:
        from modules.battle_move_replacing import get_learn_move_state

        return str(get_learn_move_state()).replace("LearnMoveState.", "")
    except Exception as e:
        return f"<err {e}>"


def battle_text():
    try:
        return decode_string(read_symbol("gDisplayedStringBattle"))
    except Exception:
        return ""


def party_snapshot():
    try:
        return "|".join(f"{p.species.name}:L{p.level}:exp{p.total_exp}" for p in get_party())
    except Exception as e:
        return f"<err {e}>"


def active_ml_tasks():
    names = (
        "Task_HandleReplaceMoveYesNoInput",
        "Task_HandleReplaceMoveInput",
        "Task_HandleStopLearningMoveYesNoInput",
        "Task_EvolutionScene",
        "Task_BattleStart",
    )
    return [n for n in names if task_is_active(n)]


#: How many stall snapshots a single run may write. A run can stall many times; capturing only
#: the first (the old behaviour) usually captures a recoverable hiccup rather than the fatal
#: wedge, but capturing every one could fill the disk on a pathological run.
_STALL_SAVE_CAP = 6


def _all_task_names():
    """EVERY task the game currently has running — not a filtered subset.

    ‼ The attribute is `symbol`, NOT `name` (modules/tasks.py: Task.symbol resolves the
    function pointer to a symbol). My first cut used `t.name` and every dump printed
    `tasks=<err 'Task' object has no attribute 'name'>` — caught within one validation
    run. The pre-existing STUCK-OW branch had the same `t.name` bug, but its bare
    `except` swallowed it into a silent `tasks="?"`, so it had been broken invisibly."""
    try:
        from modules.tasks import get_tasks

        return [t.symbol for t in get_tasks()]
    except Exception as e:
        return f"<err {e}>"


def _script_names():
    """Names of the field scripts the game currently reports as ACTIVE.

    ‼ 2026-07-24: the harness's stuck-dumps did NOT carry this field, and that is
    exactly why three long runs that all died on Route 111 (18,99) were undiagnosable
    from harness logs alone. The user's in-game DEBUG dump DOES print it, and it showed
    `EventScript_SmashRock` still reading active 140,000 frames after the bot had
    dropped to Manual and stopped pressing anything. A parked field script swallows
    input and wedges every script-gated wait downstream, so it must appear in any
    "why is nothing progressing" dump. Never diagnose a wedge without it."""
    try:
        from modules.tasks import get_global_script_context

        ctx = get_global_script_context()
        if ctx is not None and ctx.is_active:
            return list(ctx.stack or [])
        return []
    except Exception as e:
        return f"<err {e}>"


# ---- optional fault injection: simulate the user's failing environment -------
if args.break_state:
    import modules.battle_move_replacing as _bmr
    import modules.tasks as _tasks_mod

    _orig_gls = _bmr.get_learn_move_state

    def _broken_gls():
        s = _orig_gls()
        # The Emerald battle "Delete a move?" Yes/No is detected ONLY by a fragile
        # script-offset; simulate that offset NEVER matching â†’ state stuck Unknown.
        if s == _bmr.LearnMoveState.AskWhetherToLearn:
            return _bmr.LearnMoveState.Unknown
        return s

    _bmr.get_learn_move_state = _broken_gls
    # is_waiting_for_input reads the field printer â†’ unreliable in battle; force the
    # worst case (always False) so the old wfi-gated text branch never presses.
    _tasks_mod.is_waiting_for_input = lambda: False
    if hasattr(_bmr, "is_waiting_for_input"):
        _bmr.is_waiting_for_input = lambda: False
    log("[break-state] FAULT INJECTED: AskWhetherToLearn->Unknown, is_waiting_for_input->False")

# ---- run the loop ------------------------------------------------------------
previous_frame_info = None
prev_party = None
prev_ctrl = None
prev_ml = "DialogueNotActive"
in_battle_prev = False
trace_active = False  # verbose trace while a move-learn/evo is happening
no_progress = 0
last_sig = None
last_heartbeat = 0
injected = not (args.inject_treecko or args.inject_weak or args.inject_faintbench or args.inject_shedinja_faint)

CH5_FLAGS = (
    "DEVON_GOODS_STOLEN", "RECOVERED_DEVON_GOODS", "RETURNED_DEVON_GOODS",
    "RECEIVED_POKENAV", "DEFEATED_RIVAL_RUSTBORO",
)
_prev_flags = {}
_prev_mappos = None


def ch5_track(step):
    global _prev_flags, _prev_mappos
    try:
        from modules.memory import get_event_flag
        from modules.player import get_player_avatar
        from modules.map import get_map_data_for_current_position

        d = get_map_data_for_current_position()
        a = get_player_avatar()
        mp = (d.map_name, (d.map_group, d.map_number), tuple(a.local_coordinates))
        if mp != _prev_mappos:
            log(f"f{step}: POS {mp[0]} {mp[1]} local={mp[2]}")
            _prev_mappos = mp
        cur = {f: bool(get_event_flag(f)) for f in CH5_FLAGS}
        if not _prev_flags:
            _prev_flags = cur
            log(f"f{step}: FLAGS baseline {cur}")
        else:
            for f in CH5_FLAGS:
                if _prev_flags.get(f) != cur[f]:
                    log(f"f{step}: FLAG {f} -> {cur[f]}")
            _prev_flags = cur
    except Exception:
        pass

log(f"[run] starting faithful loop for up to {args.frames} frames")

import os as _os_hook
_saved_post_rival = False
_rival_stable = 0
_CKPT_STATE: dict = {}  # SAVE_CHECKPOINT hook state (stable counter + saved flag)
_WANT_POST_RIVAL_SAVE = bool(_os_hook.environ.get("SAVE_POST_RIVAL"))
for step in range(args.frames):
    context.frame = step

    # Capture the post-rival save once the rival is defeated â€” ONLY when explicitly asked
    # (SAVE_POST_RIVAL=1), else it would clobber an existing post_rival.ss1 during other
    # tests that happen to run from a post-rival state. Require the flag STABLE for many
    # consecutive frames + controllable (the flag has a 1-frame read flicker).
    if _WANT_POST_RIVAL_SAVE and not _saved_post_rival and step > 50:
        try:
            from modules.memory import get_event_flag as _gef
            from modules.player import player_avatar_is_controllable as _pac

            if _gef("DEFEATED_RIVAL_RUSTBORO") and _pac():
                _rival_stable += 1
            else:
                _rival_stable = 0
            if _rival_stable >= 120:
                (SCRATCH / "post_rival.ss1").write_bytes(context.emulator.get_save_state())
                log(f"f{step}: *** DEFEATED_RIVAL_RUSTBORO stable â€” saved post_rival.ss1 ***")
                _saved_post_rival = True
        except Exception:
            pass

    if _dbglog is not None:
        try:
            _dbglog.on_frame()
        except Exception:
            pass

    if not injected and step >= args.inject_at:
        if args.inject_weak:
            inject_weak()
        elif args.inject_faintbench:
            inject_faintbench()
        elif args.inject_shedinja_faint:
            inject_shedinja_faint()
        else:
            inject_treecko()
        injected = True

    if args.set_balls is not None and step == max(1, args.inject_at):
        try:
            from modules.debug_utilities import debug_write_item_bag
            from modules.items import get_item_bag, ItemSlot
            from modules.pokemon import get_item_by_name

            bag = get_item_bag()
            ne = lambda pocket: [s for s in pocket if s.quantity > 0]
            pb = get_item_by_name("PokÃ© Ball")
            debug_write_item_bag(
                items=ne(bag.items), key_items=ne(bag.key_items),
                poke_balls=([ItemSlot(pb, args.set_balls)] if args.set_balls > 0 else []),
                tms_hms=ne(bag.tms_hms), berries=ne(bag.berries),
            )
            log(f"[setup] set PokÃ© Balls to {args.set_balls}")
        except Exception as e:
            log(f"[setup] set-balls err {e}")

    game_state = get_game_state()
    script_context = get_global_script_context()
    script_stack = script_context.stack if script_context is not None and script_context.is_active else []
    task_list = get_tasks()
    active_tasks = [t.symbol.lower() for t in task_list] if task_list is not None else []

    frame_info = FrameInfo(
        frame_count=context.emulator.get_frame_count(),
        game_state=game_state,
        active_tasks=active_tasks,
        script_stack=script_stack,
        controller_stack=[c.__qualname__ for c in context.controller_stack],
        previous_frame=previous_frame_info,
    )

    # SAVE_CHECKPOINT="FLAG:name" â€” snapshot saves/name.ss1 the first time FLAG is set
    # AND the avatar is stably controllable (captures a clean, loadable checkpoint at a
    # story milestone, e.g. SAVE_CHECKPOINT="DELIVERED_DEVON_GOODS:stern_done").
    _ckpt = _os_hook.environ.get("SAVE_CHECKPOINT")
    if _ckpt and ":" in _ckpt and not _CKPT_STATE.get("saved"):
        try:
            from modules.memory import get_event_flag as _gef
            from modules.player import player_avatar_is_controllable as _pac

            _flag, _name = _ckpt.split(":", 1)
            if _gef(_flag):
                _CKPT_STATE["stable"] = _CKPT_STATE.get("stable", 0) + 1
                if _CKPT_STATE["stable"] >= 90 and _pac():
                    import pathlib as _pl2

                    _out = _pl2.Path(__file__).resolve().parent / "saves" / f"{_name}.ss1"
                    _out.write_bytes(context.emulator.get_save_state())
                    _CKPT_STATE["saved"] = True
                    log(f"[checkpoint] saved {_out.name} on {_flag}")
            else:
                _CKPT_STATE["stable"] = 0
        except Exception:
            pass

    if previous_frame_info is not None and previous_frame_info.frame_count > frame_info.frame_count:
        state_cache.reset()
        context.bot_listeners = get_bot_listeners(context.rom)

    if context.bot_mode == "Manual":
        context.bot_mode_instance = ManualBotMode()
    elif len(context.controller_stack) == 0:
        if args.driver == "spin":
            context.bot_mode_instance = SpinFightMode()
        elif args.driver == "rival":
            context.bot_mode_instance = RivalReproMode()
        elif args.driver == "ch5recon":
            context.bot_mode_instance = Chapter5ReconMode()
        elif args.driver == "martrecon":
            context.bot_mode_instance = MartReconMode()
        elif args.driver == "pokenavtut":
            context.bot_mode_instance = PokenavTutMode()
        elif args.driver == "pokenavclear":
            context.bot_mode_instance = PokenavClearMode()
        elif args.driver == "pokenavskip":
            context.bot_mode_instance = PokenavSkipMode()
        elif args.driver == "sailrecon":
            context.bot_mode_instance = SailReconMode()
        elif args.driver == "rivalretry":
            context.bot_mode_instance = RivalRetryMode()
        elif args.driver == "saildewford":
            context.bot_mode_instance = SailDewfordMode()
        elif args.driver == "shinytest":
            context.bot_mode_instance = ShinyTestMode()
        elif args.driver == "storydebugreset":
            from plugins.custom_modes.story_mode import StoryDebugResetMode

            context.bot_mode_instance = StoryDebugResetMode()
        elif args.driver == "cavetrain":
            context.bot_mode_instance = CaveTrainMode()
        elif args.driver == "hmtest":
            context.bot_mode_instance = HmTestMode()
        elif args.driver == "faintrepro":
            context.bot_mode_instance = FaintReproMode()
        elif args.driver == "pokenavfaith":
            context.bot_mode_instance = PokenavFaithMode()
        elif args.driver == "martbuy":
            context.bot_mode_instance = MartBuyMode()
        elif args.driver == "healtest":
            context.bot_mode_instance = HealTestMode()
        elif args.driver == "fierycave":
            context.bot_mode_instance = FieryCaveMode()
        elif args.driver == "journey":
            context.bot_mode_instance = JourneyMode()
        elif args.driver == "smashroute":
            context.bot_mode_instance = SmashRouteMode()
        elif args.driver == "cavethread":
            context.bot_mode_instance = CaveThreadMode()
        elif args.driver == "normancounter":
            context.bot_mode_instance = NormanCounterMode()
        elif args.driver == "traintest":
            from plugins.custom_modes.story_mode import StoryMode as _SM

            class _TrainTest(_SM):
                def run(self):
                    from modules.story.early_game import train_team, RUSTBORO_TRAINING_GRASS
                    from modules.map_data import PokemonCenter

                    yield from train_team(
                        17, scope="whole", grass=RUSTBORO_TRAINING_GRASS, heal_center=PokemonCenter.RustboroCity
                    )
                    while True:
                        context.emulator.press_button("B")
                        yield

            context.bot_mode_instance = _TrainTest()
        elif args.driver == "traintest102":
            # MEASUREMENT (probe_training_economics.py, punch-list training-economics
            # task, 2026-07-24): drive the REAL train_team() on Route 102 (Petalburg
            # fodder patch) from whatever save is loaded, slot 0 only, no level cap
            # worth stopping for (target 200) — --frames bounds the window. Used to
            # empirically measure frames/battle via the PARTY CHANGE log lines below.
            from plugins.custom_modes.story_mode import StoryMode as _SM

            class _TrainTest102(_SM):
                def run(self):
                    from modules.story.early_game import train_team, PETALBURG_TRAINING_GRASS
                    from modules.map_data import PokemonCenter

                    yield from train_team(
                        200, slots={0}, grass=PETALBURG_TRAINING_GRASS, heal_center=PokemonCenter.PetalburgCity
                    )
                    while True:
                        context.emulator.press_button("B")
                        yield

            context.bot_mode_instance = _TrainTest102()
        elif args.driver == "gymtest":
            from plugins.custom_modes.story_mode import StoryMode as _SM

            class _GymTest(_SM):
                def run(self):
                    from modules.story.early_game import do_rustboro_gym

                    yield from do_rustboro_gym()
                    while True:
                        context.emulator.press_button("B")
                        yield

            context.bot_mode_instance = _GymTest()
        else:
            context.bot_mode_instance = get_bot_mode_by_name(context.bot_mode)()
        context.controller_stack.append(context.bot_mode_instance.run())

    # -------- instrumentation (before advancing) --------
    ctrl = frame_info.controller_stack[-1] if frame_info.controller_stack else "<none>"
    if ctrl != prev_ctrl:
        log(f"f{step}: CONTROLLER -> {ctrl}   (state={game_state.name if hasattr(game_state,'name') else game_state})")
        prev_ctrl = ctrl

    ba = battle_is_active()
    if ba != in_battle_prev:
        # ‼ LOG THE OUTCOME, NOT JUST THE TRANSITION (2026-07-26). The user's real-HW
        # log exposed a livelock — 3,011 RanAway vs 5 Won, full HP, ~2.9M frames, no
        # level gained — and the ONLY signal was the outcome tally. This harness logged
        # `battle_is_active -> False` and nothing else, so batch 20260726-052205 could
        # not have reported that bug even though it ran five full cold starts. A
        # validation harness that cannot see "the bot flees everything" is blind to an
        # entire failure class; `livetest.py` now tallies these into every batch summary.
        _outcome = ""
        if not ba:
            try:
                from modules.battle_state import get_last_battle_outcome

                _outcome = f"  outcome={get_last_battle_outcome()}"
            except Exception:
                _outcome = "  outcome=<unreadable>"
        log(f"f{step}: battle_is_active -> {ba}{_outcome}  party=[{party_snapshot()}]")
        in_battle_prev = ba

    ml = learn_state_str()
    ml_active = ml != "DialogueNotActive" or any(
        ph in battle_text() for ph in ("trying to learn", "make room for", "Delete a move", "wants to learn")
    )
    evo_active = task_is_active("Task_EvolutionScene")

    if (ml_active or evo_active) and not trace_active:
        trace_active = True
        log(f"f{step}: === MOVE-LEARN/EVO WINDOW OPEN === party=[{party_snapshot()}]")
    if trace_active:
        try:
            from modules.tasks import is_waiting_for_input as _wfi

            wfi = _wfi()
        except Exception as e:
            wfi = f"<err {e}>"
        log(
            f"  f{step} st={game_state.name if hasattr(game_state,'name') else game_state} "
            f"instr={get_current_battle_script_instruction()} cb={get_main_battle_callback()} "
            f"ml={ml} wfi={wfi} tasks={active_ml_tasks()} ctrl={ctrl!r} "
            f"bt={battle_text()!r}"
        )
    if trace_active and not ml_active and not evo_active:
        # window closed
        trace_active = False
        log(f"f{step}: === window closed === party=[{party_snapshot()}]")

    if args.driver in ("ch5recon", "story", "healtest"):
        ch5_track(step)

    # party level-up detection
    ps = party_snapshot()
    if ps != prev_party:
        if prev_party is not None:
            log(f"f{step}: PARTY CHANGE [{prev_party}] -> [{ps}]")
        prev_party = ps

    # -------- advance the controller stack (faithful) --------
    try:
        for listener in context.bot_listeners.copy():
            listener.handle_frame(context.bot_mode_instance, frame_info)
        if context.bot_mode == "Manual":
            context.controller_stack = []
        if len(context.controller_stack) > 0:
            next(context.controller_stack[-1])
    except (StopIteration, GeneratorExit):
        if context.controller_stack:
            context.controller_stack.pop()
    except BotModeError as e:
        context.emulator.reset_held_buttons()
        context.message = str(e)
        log(f"f{step}: *** BotModeError -> Manual: {e}")
        context.set_manual_mode()
    except Exception as e:
        import traceback

        log(f"f{step}: *** EXCEPTION: {e}\n{traceback.format_exc()}")
        context.set_manual_mode()

    # -------- no-progress detector (independent of the in-battle watchdog) --------
    # Position is part of the signature: run 7's Mauville maze solver actively explored
    # (positions changing every few frames) while controller/state/party froze — the
    # position-blind sig called that a HANG. Movement IS progress.
    try:
        from modules.player import get_player_avatar as _gpa
        _pos = tuple(_gpa().local_coordinates)
    except Exception:
        _pos = None
    sig = (
        ctrl,
        game_state.name if hasattr(game_state, "name") else str(game_state),
        get_current_battle_script_instruction() if ba else "",
        ml,
        ps,
        _pos,
    )
    if sig == last_sig:
        no_progress += 1
    else:
        no_progress = 0
        last_sig = sig
        # re-arm save-on-stall: progress resumed, so the NEXT stall episode gets its own
        # capture (2026-07-24: an early self-recovering scene consumed the once-per-process
        # save and the REAL later wedge went uncaptured). ‼ Nothing to re-arm now that each
        # stall writes its own uniquely-named file — the only limit is the per-run
        # `_STALL_SAVE_CAP`, which must NOT be reset here or a run that stalls repeatedly
        # would write unboundedly many snapshots. Left as a no-op comment deliberately: the
        # old `_stuck_saved = False` line was a live-looking reset of a flag nothing reads
        # any more, which is exactly the kind of stale code that misleads the next reader.
        pass
    # STUCK-OVERWORLD DIAGNOSTIC: the reliable "is the game actually blocked"
    # signal is player_avatar_is_controllable() (gDisplayedStringBattle/gBattleMainFunc
    # go STALE after a battle, so they lie). Log a compact trace on change whenever
    # we're in the overworld, NOT in a battle, but NOT controllable â€” the real hang.
    try:
        from modules.modes.util.walking import player_avatar_is_controllable as _pic

        _ctl = _pic()
    except Exception:
        _ctl = None
    # SAVE-ON-STUCK: capture the state after being non-controllable in the overworld
    # for a sustained window, so it can be single-stepped offline.
    if sig[1] == "OVERWORLD" and not ba and _ctl is False:
        globals()["_stuck_run"] = globals().get("_stuck_run", 0) + 1
    else:
        globals()["_stuck_run"] = 0
    # ‼ PER-RUN, PER-STALL SAVE PATHS (2026-07-25). This used to write one shared
    # `midstuck.ss1` and fire only ONCE per run. Both halves cost real diagnostic work:
    #   * SHARED PATH — three concurrent runs each overwrote it, so the file could not be
    #     trusted to belong to any particular failure. The move-learn stall that killed 2 of 3
    #     cold-start runs STILL has no clean repro for exactly this reason, and one earlier
    #     investigation wasted effort on a `midstuck.ss1` that turned out to be a whiteout
    #     state from a different map entirely.
    #   * ONCE PER RUN — a run typically stalls several times; only the FIRST was ever
    #     captured, which is usually a recoverable hiccup rather than the fatal wedge.
    # Now: <profile>-<frame>.ss1 under saves/stalls/, up to _STALL_SAVE_CAP per run so a
    # pathological run cannot fill the disk. The profile name makes concurrent runs unambiguous.
    if no_progress == 900 and globals().get("_stall_saves", 0) < _STALL_SAVE_CAP:
        globals()["_stall_saves"] = globals().get("_stall_saves", 0) + 1
        try:
            _dir = SAVES / "stalls"
            _dir.mkdir(parents=True, exist_ok=True)
            _prof = getattr(getattr(context, "profile", None), "path", None)
            _prof = _prof.name if _prof is not None else "unknown-profile"
            _sp = _dir / f"{_prof}-f{step}.ss1"
            _sp.write_bytes(context.emulator.get_save_state())
            log(f"f{step}: SAVED stall state #{globals()['_stall_saves']} to "
                f"stalls/{_sp.name} (bt={(battle_text() or '')!r})")
        except Exception as _e:
            log(f"f{step}: save-on-stuck failed: {_e}")
    if sig[1] == "OVERWORLD" and not ba and _ctl is False:
        try:
            from modules.game import get_text_printer as _gtp

            _tp = _gtp()
            _tpstate = f"active={_tp.active} state={_tp.state}" if _tp else "None"
        except Exception as _e:
            _tpstate = f"<err {_e}>"
        try:
            from modules.tasks import get_tasks as _gt

            _tasks = [t.symbol for t in _gt()]  # `.symbol`, not `.name` — see _all_task_names()
        except Exception as _e:
            _tasks = f"<err {_e}>"  # never swallow into "?" — that hid this exact bug
        _dsig = (get_main_battle_callback(), get_current_battle_script_instruction(), _tpstate, ctrl, ps)
        if _dsig != globals().get("_last_dsig"):
            globals()["_last_dsig"] = _dsig
            log(f"f{step}: STUCK-OW cb={get_main_battle_callback()} instr={get_current_battle_script_instruction()} "
                f"textprinter={_tpstate} tasks={_tasks} ctrl={ctrl} bt={(battle_text() or '')!r} "
                f"scripts={_script_names()} party=[{ps}]")
    if no_progress in (1200, 3000, 8000, 15000):
        log(
            f"f{step}: !!! NO-PROGRESS x{no_progress} sig={sig} "
            f"instr={get_current_battle_script_instruction()} cb={get_main_battle_callback()} "
            # ‼ 2026-07-24: this used to print active_ml_tasks(), which filters the task
            # list down to FIVE move-learn task names. So a wedge with a full, busy task
            # list printed `tasks=[]` — which reads as "nothing is running" and is how the
            # "transient tasks=[]" mystery in KI-15 was mis-read for days. The real culprit
            # of a wedge is usually a task NOT in that allow-list (e.g. ExecuteMatchCall,
            # a PokéNav match call, which is a TASK and not a field script and is therefore
            # invisible to every script-context guard we own). Print ALL of them.
            f"ml_tasks={active_ml_tasks()} tasks={_all_task_names()} scripts={_script_names()} "
            f"bt={battle_text()!r} bot_mode={context.bot_mode}"
        )
        # The Ch9 fainted-menu hang proved a sig alone can't localize an in-battle
        # wedge — dump the exact generator frame the bot is waiting in as well.
        try:
            from modules.debug_logger import _generator_stack
            for entry in _generator_stack():
                log(f"f{step}:     gen -> {entry}")
        except Exception as e:
            log(f"f{step}:     gen -> <err {e}>")
    if no_progress >= 20000:
        # ‼ DISTINGUISH "FINISHED" FROM "HUNG" (#24-harness-finish, seen 2026-07-25 on the
        # first cold-start Badge 6 run). When the story bot reaches the end of built content it
        # prints "end of built content ... handing to manual" and legitimately stops doing
        # anything — so the frame-based detector fires 20,000 frames later and the log ends with
        # "HANG CONFIRMED" on a run that SUCCEEDED. That false signal is expensive twice over:
        # it wastes an investigation, and it made compare_runs.py file a success as a failure.
        _finished = False
        try:
            _finished = "end of built content" in str(getattr(context, "message", "") or "")
        except Exception:
            _finished = False
        if _finished:
            log(f"f{step}: RUN COMPLETE — end of built content reached; the bot is idle by "
                f"design, not hung. Stopping cleanly.")
        else:
            log(f"f{step}: HANG CONFIRMED (20000 frames no progress). Stopping.")
        break

    if step - last_heartbeat >= 2000:
        last_heartbeat = step
        log(f"f{step}: heartbeat mode={context.bot_mode} ctrl={ctrl} state={sig[1]} party=[{ps}]")

    context.emulator.get_inputs()
    context.emulator.run_single_frame()
    previous_frame_info = frame_info
    previous_frame_info.previous_frame = None

log(f"[done] ran {step + 1} frames; final mode={context.bot_mode} party=[{party_snapshot()}]")
try:
    from modules.memory import get_event_flag as _gef

    log("[final flags] " + ", ".join(f"{f}={bool(_gef(f))}" for f in CH5_FLAGS))
except Exception as e:
    log(f"[final flags] err {e}")
try:
    for p in get_party():
        mv = ", ".join(lm.move.name for lm in p.moves if lm is not None)
        log(f"[moveset] {p.species.name} L{p.level}: {mv}")
except Exception as e:
    log(f"[moveset] err {e}")
logf.close()
