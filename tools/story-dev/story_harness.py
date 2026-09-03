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
import datetime as _dt
import os as _os
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
ap.add_argument("--driver", default="spin", choices=["spin", "story", "rival", "ch5recon", "martrecon", "martbuy", "healtest", "traintest", "traintest102", "gymtest", "pokenavtut", "pokenavclear", "pokenavskip", "pokenavfaith", "sailrecon", "rivalretry", "saildewford", "shinytest", "storydebugreset", "cavetrain", "fierycave", "hmtest", "faintrepro", "journey", "smashroute", "cavethread", "boxcatch", "boxwithdraw", "teachfull", "groundsweep", "anchorcapture", "anchorstory", "magmadoor", "magmatravel", "magmahideout", "magmaexit", "slateporttheft", "aquahideout", "mossdeeptravel", "mossdeepgym", "mossdeepbadge", "spacecenter1", "spacecenter2", "spacecenter", "normancounter", "roster", "partypids", "boxcounter", "boxcounter2", "boxwrite", "ki80ladder", "secondwind", "ch20dive", "ch20room1", "ch20room2", "ch20room6", "ch20room3", "ch20room8", "ch20room9", "ch20chapter", "ch21dive", "ch21leg2probe", "ch21escort", "ch21cave", "ch21pocket", "ch21approach", "ch21climb", "ch21leg5probe", "ch21return", "ch21chapter", "ch22probe", "ch22ice", "divelearner", "ki66faint", "ki76warp"])
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
# ⛔⛔ THE DEFAULT LOG NAME MUST NOT COLLIDE — `#24-orphans` item (4), fixed 2026-08-16.
# It used to be `harness_{build}.log`: ONE fixed name per build, opened `"w"`. So running the
# SECOND ARM of an A/B **destroyed the first arm's transcript**, and the destruction was silent.
# ‼ That is an instrument that eats evidence, and it had already cost a Tier 1 kick-back on
# 2026-08-15 when arm 2 overwrote arm 1 and left a TRUE claim unverifiable.
# ⛔ The countermeasure shipped that day was a PROSE HABIT ("give each arm a distinct --log"),
# which a fresh session has no reason to know. A default that CANNOT collide is the real fix:
# build + driver + timestamp + PID, so even two runs starting in the same second differ.
# ⚠ `--log` still wins and is still honoured EXACTLY — scripts that pin a path keep working.
if args.log:
    LOG = Path(args.log)
else:
    _stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    LOG = SCRATCH / f"harness_{args.build}_{args.driver}_{_stamp}_{_os.getpid()}.log"

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


# ‼ ANNOUNCE THE LOG PATH FIRST, BEFORE ANYTHING CAN FAIL. The names are unique now (see above),
# so "read `harness_<build>.log`" is no longer an instruction anyone can follow — the path has to
# come from the run itself. `log()` writes it to BOTH the file and stdout, and it is the first line
# of each, so a hung run can still be diagnosed by tailing the path printed here.
# ⇒ to find the newest afterwards:  ls -t tools/story-dev/harness_*.log | head -1
log(f"[setup] LOG -> {LOG}")
if not args.log:
    log("[setup] (unique per run by design — #24-orphans (4); pass --log to pin a path)")

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
        # ‼ `#24-battleitems` A/B (2026-08-09). `NORMAN_STRATEGY=old` forces the PRE-FEATURE
        # strategy so the two arms differ in exactly one thing: whether the bot may use items.
        # Default is the production strategy, so this fixture keeps testing what actually ships.
        import os

        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy, StoryItemBattleStrategy

        if os.environ.get("NORMAN_STRATEGY", "new").strip().lower() == "old":
            return LevelUpTravelBattleStrategy()
        return StoryItemBattleStrategy()

    def run(self):
        import os

        from modules.debug_utilities import debug_create_pokemon, debug_write_party
        from modules.memory import get_event_flag
        from modules.pokemon import LearnedMove, get_move_by_name, get_species_by_name
        from modules.pokemon_party import get_party
        from modules.story.early_game import do_petalburg_gym, wait_until_truly_controllable

        level = int(os.environ.get("NORMAN_MACHOP_LEVEL", "18"))
        yield from wait_until_truly_controllable()

        # ‼ FIXTURE WRITE — STOCK THE BAG (`NORMAN_ITEMS`, default `4x Hyper Potion`).
        # `prenorman_fodder_grind.ss1` holds **zero** healing items (measured), so without this
        # the `#24-battleitems` arms would differ in nothing and the A/B would silently compare
        # two identical runs — the "a fixture must create its condition" rule, which has already
        # cost this project two wasted runs today. The write is declared, not hidden: the RESULT
        # line reports what the bag actually held once it was done.
        try:
            from modules.debug_utilities import debug_write_item_bag
            from modules.items import ItemSlot, get_item_bag, get_item_by_name
            from modules.modes.util.sleep import wait_for_n_frames

            spec = os.environ.get("NORMAN_ITEMS", "Hyper Potion:4").strip()
            if spec and spec.lower() not in ("none", "0"):
                extra = []
                for chunk in spec.split(","):
                    name, _, qty = chunk.partition(":")
                    extra.append(ItemSlot(get_item_by_name(name.strip()), int(qty or 1)))
                bag = get_item_bag()
                debug_write_item_bag(
                    items=list(bag.items) + extra,
                    key_items=list(bag.key_items),
                    poke_balls=list(bag.poke_balls),
                    tms_hms=list(bag.tms_hms),
                    berries=list(bag.berries),
                )
                yield from wait_for_n_frames(10)  # the bag is cached per frame; read it back after
                log(f"[normancounter] FIXTURE: stocked {spec}; bag now "
                    f"{[(s.item.name, s.quantity) for s in get_item_bag().items]}")
        except Exception as error:  # noqa: BLE001
            log(f"[normancounter] ‼ could not stock the bag: {type(error).__name__}: {error} "
                f"— an items A/B from this save would be MEANINGLESS; fix before reading a result.")

        # ‼ CONTROL ARM (`NORMAN_MACHOP_LEVEL=0`) — added 2026-08-09, and this experiment is
        # UNINTERPRETABLE without it. The question is "does a counter at level L win the fight",
        # and the only way "L26 wins" means anything is if the SAME party without the counter
        # LOSES. Otherwise a win measures the anchor's own team, not the counter — and this
        # anchor is not weak (Combusken L35 / Mightyena L30 / Ninjask L27 vs Norman's L28-31).
        # ‼ The party's existing MOVES are logged for the same reason: if something already
        # carries a Fighting move, the boss's "no super-effective answer" stop could never have
        # fired here and the fixture is answering a different question than the batch asks.
        for _m in [m for m in get_party() if m is not None and not m.is_egg]:
            try:
                log(f"[normancounter] existing {_m.species.name} L{_m.level} "
                    f"moves={[lm.move.name for lm in _m.moves if lm is not None]}")
            except Exception:  # noqa: BLE001
                pass

        if level <= 0:
            log("[normancounter] CONTROL ARM — injecting NOTHING; measuring whether this party "
                "beats Norman on its own.")
            badge_before = bool(get_event_flag("BADGE05_GET"))
            detail = ""
            try:
                yield from do_petalburg_gym()
                detail = "gym segment returned"
            except Exception as error:  # noqa: BLE001
                detail = f"{type(error).__name__}: {str(error)[:150]}".replace("\n", " ")
            badge = bool(get_event_flag("BADGE05_GET"))
            log(f"[normancounter] RESULT level=CONTROL badge={badge} (was {badge_before}) detail={detail}")
            context.set_manual_mode()
            return

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
        # ‼ `NORMAN_MACHOP_NATURAL=1` — THE ARM THAT CHECKS THE FIXTURE ITSELF (2026-08-09).
        # `#24-bosstelemetry`'s first run showed the injected Machop selecting Karate Chop on
        # five consecutive turns with **PP frozen at 22 and Slaking on 143/143 throughout** —
        # i.e. the move was never executed — while natural party members' moves decremented PP
        # and dealt damage normally. That correlates exactly with "built by
        # `LearnedMove.create` and written in by `debug_create_pokemon`", so the six-arm
        # "a counter does not beat Norman" result may be measuring a BROKEN INJECTED MON.
        # This arm omits `moves=` entirely and lets the species' natural learnset stand, which
        # is the discriminating test.
        # ‼‼ NATURAL IS NOW THE DEFAULT, AND THE EXPLICIT PATH IS KNOWN-BROKEN (2026-08-09).
        # `moves=[LearnedMove.create(...)]` builds slots the battle engine SELECTS BUT NEVER
        # EXECUTES: measured `Karate Chop(pp22)` chosen on five consecutive turns with PP frozen
        # and the opponent untouched at 143/143. Six arms of this experiment were run on that
        # mon and its conclusion had to be retracted (`08-MISTAKES` 2026-08-09). Passing
        # `NORMAN_MACHOP_MOVES=explicit` restores it ONLY so the broken behaviour stays
        # reproducible for whoever fixes `debug_create_pokemon`; it must never be used to
        # measure anything.
        natural = os.environ.get("NORMAN_MACHOP_MOVES", "natural").strip().lower() != "explicit"
        if os.environ.get("NORMAN_MACHOP_NATURAL", "").strip() in ("1", "true", "yes"):
            natural = True
        create_kwargs = dict(
            species=machop, level=level,
            experience=machop.level_up_type.get_experience_needed_for_level(level),
            nickname="MACHOP", current_hp=None,
        )
        if not natural:
            create_kwargs["moves"] = moves
        else:
            log("[normancounter] NATURAL-MOVES ARM — not passing moves=; the species learnset stands")
        mon = debug_create_pokemon(**create_kwargs)
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

        # ‼ CAVE_BOXCHECK — does `pc_trip.box_views()` actually read the PC? Suspicion
        # 2026-08-06: it does `getattr(storage, "boxes", lambda: [])()`, calling `boxes` — but
        # `PokemonStorage.boxes` is a @cached_property returning a LIST, so `list()` raises
        # TypeError. If so, `find_in_box` (which calls it unguarded) can never find anything and
        # `withdraw_from_box` can never fire — a second, independent reason `withdrawing` has
        # logged 0 in every batch.
        if os.environ.get("CAVE_BOXCHECK", "").strip():
            from modules.pokemon_storage import get_pokemon_storage
            from modules.story import pc_trip

            st = get_pokemon_storage()
            log(f"[cavethread] BOXCHECK storage.pokemon_count={st.pokemon_count} "
                f"boxes_type={type(st.boxes).__name__}")
            try:
                views, mons = pc_trip.box_views()
                log(f"[cavethread] BOXCHECK box_views() OK -> {len(views)} views, {len(mons)} mons")
            except Exception as error:  # noqa: BLE001
                log(f"[cavethread] BOXCHECK box_views() RAISED {type(error).__name__}: {error}")
            context.set_manual_mode()
            return

        # ‼ CAVE_PATHCHECK — answer "is this leg reachable FROM HERE at all?" without walking.
        # Route 120 (2026-08-05): the navigator picked leg ROUTE122 (22,29) and failed to reach
        # it from ROUTE120 (7,56). Two explanations with different fixes — the leg was NEVER
        # reachable (calculate_path spans only DIRECTLY CONNECTED maps, and ROUTE120->ROUTE122
        # is two connections via ROUTE121), or the bot walked itself somewhere it stopped being
        # reachable. Asking from the START position separates them in one cheap run.
        pathcheck = os.environ.get("CAVE_PATHCHECK", "").strip()
        if pathcheck:
            from modules.map_path import calculate_path
            from modules.player import get_player_location
            from modules.items import get_item_bag, get_item_by_name

            here = get_player_location()
            log(f"[cavethread] PATHCHECK from {here}")
            # ‼ `calculate_path.can_surf()` gates every water tile on exactly these two, so
            # print them: a False here makes any "unreachable" verdict about a water crossing
            # meaningless (2026-08-05 — Route 121's south shore reads as unreachable and the
            # question is whether that is terrain or a missing capability).
            try:
                from modules.memory import get_event_flag
                from modules.pokemon_party import get_party

                log(f"[cavethread] SURF-GATE BADGE05_GET={get_event_flag('BADGE05_GET')} "
                    f"party_has_surf={get_party().has_pokemon_with_move('Surf')}")
            except Exception as error:  # noqa: BLE001
                log(f"[cavethread] SURF-GATE unreadable: {type(error).__name__}: {error}")
            # ‼ Read named event flags LIVE. `mapfacts.py` dumps the map as AUTHORED, so an
            # object it lists may be hidden at runtime — the flag is what decides. Used to
            # settle whether Route 121's Team Aqua grunts are actually standing in the corridor.
            for flag_name in [f for f in os.environ.get("CAVE_FLAGS", "").split(",") if f.strip()]:
                try:
                    from modules.memory import get_event_flag

                    log(f"[cavethread] FLAG {flag_name.strip()} = {get_event_flag(flag_name.strip())}")
                except Exception as error:  # noqa: BLE001
                    log(f"[cavethread] FLAG {flag_name.strip()} unreadable: {error}")
            for spec in pathcheck.split(";"):
                mname, _, tile = spec.strip().partition(":")
                x, _, y = tile.partition(",")
                dest = (tuple(MapRSE[mname.strip()].value), (int(x), int(y)))
                try:
                    wp = calculate_path(
                        here, dest,
                        has_acro_bike=get_item_bag().quantity_of(get_item_by_name("Acro Bike")) > 0,
                        has_mach_bike=get_item_bag().quantity_of(get_item_by_name("Mach Bike")) > 0,
                    )
                    log(f"[cavethread] PATHCHECK {mname.strip()}{(int(x), int(y))} -> OK, {len(wp)} waypoints")
                except Exception as error:  # noqa: BLE001
                    log(f"[cavethread] PATHCHECK {mname.strip()}{(int(x), int(y))} -> "
                        f"{type(error).__name__}: {str(error)[:300]}".replace("\n", " "))
            context.set_manual_mode()
            return

        # ‼ A/B ARM for the 2026-08-05 connection-step fix. `old` blinds `_connection_step` so
        # the trip behaves exactly as it did before the change — same build, same save, one
        # variable. (Monkeypatched rather than env-gated in production: this is a temporary
        # experiment, not a regression flag that should live in the bot.)
        arm = os.environ.get("CAVE_ARM", "new").strip().lower()
        _saved_conn = None
        if arm == "old":
            from modules.modes.util import global_navigation as _gn

            _saved_conn = _gn._connection_step
            _gn._connection_step = lambda *a, **k: None
        log(f"[cavethread] arm={arm}")

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


class BoxCatchMode(BotMode):
    """`#24-boxmessage` — CAPABILITY TEST: does a FULL-PARTY catch complete and exit cleanly?

    ‼ WHY A CAPABILITY TEST AND NOT A BATCH. Measured 2026-08-06: four batches of ~25 runs each,
    and NOT ONE pair of finish rates was statistically resolvable (all |z| < 1.96). A 3-hour batch
    cannot grade this. This asks the question directly, in minutes, and answers binary.

    THE CLAIM UNDER TEST. With a full party the game sends a catch straight to the PC
    (`Cmd_givecaughtmon` -> `GiveMonToPlayer` -> `CopyMonToPC`) and shows an EXTRA text box the
    party-catch path never shows — one of FOUR variants (`B_MSG_SENT_SOMEONES_PC` /
    `B_MSG_SOMEONES_BOX_FULL`, each +1 once `FLAG_SYS_PC_LANETTE` is set). The bot has NO handling
    for it: `grep VAR_PC_BOX_TO_SEND_MON` across `modules/` returns zero. If that message wedges
    the battle exit, this test hangs — which is exactly the suspected cause of the overflow path
    never firing.

    Run from a save with a FULL PARTY and ideally an EMPTY BOX (`post_mtpyre.ss1` is both), so a
    box arrival is unambiguous:
        PYTHONUTF8=1 py -3.12 story_harness.py post_mtpyre.ss1 --driver boxcatch --frames 400000

    Emits: [boxcatch] RESULT caught=<bool> box_before=<n> box_after=<n> exited_clean=<bool>
           frames=<n> box_var=<VAR_PC_BOX_TO_SEND_MON>
    """

    @staticmethod
    def name():
        return "BoxCatch"

    def on_battle_started(self, encounter):
        # Catch EVERY wild. The party is full by construction, so every catch is a box-send —
        # which is the path under test. `StoryCatchStrategy` is the same strategy the story
        # bot's counter branch returns, so this exercises production code, not a stand-in.
        from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy, StoryCatchStrategy

        # ‼ TRAINER battles need a strategy too. First run of this probe returned None for
        # them and hung 20,000 frames on `NICK got $1200 for winning!` — Mt. Pyre's summit has
        # trainers, and with no strategy nothing drives the post-battle dialogue. That is the
        # probe failing, NOT the box path; the same trap `cavethread` documents ("without a
        # strategy the first Zubat freezes the probe and we measure the battle system").
        # ‼ AND the trainer strategy must not TRAIN. `LevelUpTravelBattleStrategy` levels the
        # LEAD, which on `post_mtpyre.ss1` is an L3 Zigzagoon HM slave — run 3 of this probe
        # walked it into a whiteout (`bt='NICK whited out!'`, Zigzagoon L3 -> L11). For a catch
        # test we want to survive the walk, not grind. `DefaultBattleStrategy` fights normally
        # with the party as-is.
        if encounter is None:
            try:
                from modules.battle_strategies import DefaultBattleStrategy

                return DefaultBattleStrategy()
            except Exception:  # noqa: BLE001
                return LevelUpTravelBattleStrategy()
        return StoryCatchStrategy()

    def run(self):
        import os

        from modules.memory import GameState, get_game_state, get_event_var
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party
        from modules.pokemon_storage import get_pokemon_storage
        from modules.story.early_game import _story_spin, wait_until_truly_controllable

        budget = int(os.environ.get("BOXCATCH_FRAMES", "300000"))

        yield from wait_until_truly_controllable()
        party_n = len([m for m in get_party() if m is not None])
        box_before = get_pokemon_storage().pokemon_count
        log(f"[boxcatch] start party={party_n} box={box_before} "
            f"map={tuple(get_player_avatar().map_group_and_number)}")
        if party_n < 6:
            log(f"[boxcatch] ABORT — party is {party_n}, not 6. This test is meaningless without "
                f"a full party; a catch would go to the party and never touch the box.")
            context.set_manual_mode()
            return

        # ‼ WALK TO VERIFIED GRASS FIRST. The first two runs of this probe spun 20,000 frames
        # on MT_PYRE_SUMMIT (23,7) and produced no encounter — that tile is not grass, so
        # `_story_spin` had nothing to do and the harness called it a hang. The probe was
        # broken, not the box path. Targets come from `training_areas.TRAINING_GRASS`, which is
        # two-way swept, rather than a tile picked by eye.
        from modules.map_data import MapRSE
        from modules.story.early_game import _navigate_riding_out

        raw = os.environ.get("BOXCATCH_GRASS", "ROUTE119:21,109").strip()
        gname, _, gtile = raw.partition(":")
        gx, _, gy = gtile.partition(",")
        grass_map, grass_tile = MapRSE[gname.strip()], (int(gx), int(gy))
        log(f"[boxcatch] walking to grass {grass_map.name}{grass_tile}…")
        try:
            yield from _navigate_riding_out(grass_map, grass_tile, avoid_encounters=False, tries=24)
        except Exception as error:  # noqa: BLE001
            log(f"[boxcatch] ABORT — could not reach the grass: "
                f"{type(error).__name__}: {str(error)[:180]}")
            context.set_manual_mode()
            return
        log(f"[boxcatch] at {tuple(get_player_avatar().map_group_and_number)} — spinning for a wild")

        frames = {"n": 0}

        def _stop() -> bool:
            frames["n"] += 1
            if frames["n"] > budget:
                return True
            try:
                return get_pokemon_storage().pokemon_count > box_before
            except Exception:  # noqa: BLE001
                return False

        try:
            yield from _story_spin(_stop)
        except Exception as error:  # noqa: BLE001
            log(f"[boxcatch] spin raised {type(error).__name__}: {str(error)[:200]}")

        # ‼‼ KEEP DRIVING THROUGH THE FULL EXIT — DO NOT STOP AT THE CATCH.
        # Run 4 of this probe stopped the moment `pokemon_count` rose, logged
        # `exited_clean=True` at frame 30, and handed to Manual. The box-transfer message
        # appeared AFTER that, with nothing driving, and the harness called it a 20,000-frame
        # hang. **That hang was the PROBE exiting mid-exit, not production wedging** — I nearly
        # reported it as the confirmed bug. The catch itself was genuinely fine (box 0 -> 1).
        #
        # A real answer needs the battle exit to be DRIVEN to completion, and "clean" must mean
        # sustained: the game is in the overworld, controllable, and STAYS that way — a single
        # matching frame is exactly what produced the false positive.
        settle, stable = 0, 0
        while settle < 4000 and stable < 120:
            settle += 1
            if get_game_state() is GameState.OVERWORLD and player_avatar_is_controllable():
                stable += 1
            else:
                stable = 0
                # Nothing else is driving this generator, so the probe must advance the
                # post-catch dialogue itself — including the box-transfer message.
                context.emulator.press_button("B")
            yield
        exit_frames = settle

        box_after = get_pokemon_storage().pokemon_count
        exited = get_game_state() is GameState.OVERWORLD and player_avatar_is_controllable()
        try:
            box_var = get_event_var("PC_BOX_TO_SEND_MON")
        except Exception:  # noqa: BLE001
            box_var = "unreadable"
        log(f"[boxcatch] RESULT caught={box_after > box_before} box_before={box_before} "
            f"box_after={box_after} exited_clean={exited} spin_frames={frames['n']} "
            f"exit_frames={exit_frames} box_var={box_var}")
        if box_after > box_before and not exited:
            log("[boxcatch] ‼ CAUGHT INTO THE BOX BUT THE EXIT NEVER SETTLED — this is the "
                "box-transfer message wedging the battle exit, driven, with a bound.")

        # ‼‼ THE DECISIVE PART: CAN THE BOT KEEP PLAYING AFTERWARDS?
        # Everything above only proves the catch stored a mon and the exit settled. It does NOT
        # prove the bot is usable afterwards — and "the probe stopped driving, then the harness
        # called it a hang" has already produced TWO false alarms here. So keep spinning and
        # require OBSERVABLE PROGRESS: a second box arrival, or the avatar actually moving.
        if box_after > box_before:
            start_pos = tuple(get_player_avatar().local_coordinates)
            moved, second = False, False
            f2 = {"n": 0}

            def _stop2() -> bool:
                f2["n"] += 1
                if f2["n"] > 60000:
                    return True
                try:
                    if tuple(get_player_avatar().local_coordinates) != start_pos:
                        return False  # movement is progress, but keep going for a 2nd catch
                except Exception:  # noqa: BLE001
                    pass
                try:
                    return get_pokemon_storage().pokemon_count > box_after
                except Exception:  # noqa: BLE001
                    return False

            try:
                yield from _story_spin(_stop2)
            except Exception as error:  # noqa: BLE001
                log(f"[boxcatch] post-catch spin raised {type(error).__name__}: {str(error)[:160]}")
            try:
                moved = tuple(get_player_avatar().local_coordinates) != start_pos
                second = get_pokemon_storage().pokemon_count > box_after
            except Exception:  # noqa: BLE001
                pass
            log(f"[boxcatch] AFTER-CATCH usable={moved or second} moved={moved} "
                f"second_catch={second} frames={f2['n']} box_now="
                f"{get_pokemon_storage().pokemon_count}")
        context.set_manual_mode()
        return


class TeachFullMode(BotMode):
    """DIAGNOSE `#24-hmteachloop` — drive `teach_hm_move` down the REPLACE-DIALOGUE path.

    ‼ WHY A NEW DRIVER. `--driver hmtest` teaches to a mon `ensure_hm_learner` just CAUGHT, so
    it has free move slots and the game learns the move instantly — no replace prompt at all.
    The changelog records that shape as **12/12 clean**, which is why four budget rounds never
    reproduced anything. The 7 recorded failures are all on a mon with FOUR moves, where the
    flow must answer `Task_ReplaceMoveYesNo` and pick a slot in the summary screen. This driver
    forces exactly that: it teaches to a party mon that is compatible AND already has 4 moves.

    Reads the `TEACH EXIT` / `TEACH OK` telemetry added 2026-08-07 — which exit fired, at what
    frame, with what task set. **Diagnosis only; it changes no behaviour.**

        PYTHONUTF8=1 TEACH_ITEM=HM06 py -3.12 story_harness.py boxwithdraw.ss1 \
            --driver teachfull --frames 200000 --profile tf1

    Emits: [teachfull] RESULT learned=<bool> target=<species> replaced=<move> frames=<n>
    """

    @staticmethod
    def name():
        return "TeachFull"

    def on_battle_started(self, encounter):
        # ‼ COUNT THE BATTLE HERE, AND ONLY HERE. This hook is called by the framework on the
        # MODE INSTANCE, so it fires even while the mode's own generator is suspended — which
        # is exactly what the `TEACH_AFTER_BATTLE` spin could not see. See the long note at that
        # block for the measurement.
        self._battles_seen = getattr(self, "_battles_seen", 0) + 1
        # ‼ TRAINER battles are counted SEPARATELY, because the production failure's tail is a
        # trainer PRIZE-MONEY message (`'... got $3100 for winning!'`,
        # `BattleScript_PayDayMoneyAndPickUpItems`) and every wild-battle fixture so far taught
        # fine. `encounter is None` is this codebase's trainer test — see the strategy branch.
        if encounter is None:
            self._trainers_seen = getattr(self, "_trainers_seen", 0) + 1

        # ‼ `TEACH_AFTER_CATCH` needs the wild CAUGHT, so it uses the same production strategy
        # the story bot's counter branch returns. Trainers still fall through to the branch
        # below — a catch strategy in a trainer battle is not a thing.
        if getattr(self, "_catch_wilds", False) and encounter is not None:
            from plugins.custom_modes.story_mode import StoryCatchStrategy

            return StoryCatchStrategy()

        # ‼ TRAINER battles must use the PRODUCTION strategy. `DefaultBattleStrategy` refuses a
        # trainer battle at low HP ("cannot battle due to HP below threshold, and flee is not
        # allowed") -> BotModeError -> Manual, which killed the first AFTER_GYM run at f25831.
        # `LevelUpTravelBattleStrategy` exists precisely because it NEVER flees a trainer.
        # Identical fix to the one `boxwithdraw` needed; wilds keep Default (fleeing is fine).
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

            return LevelUpTravelBattleStrategy()
        return DefaultBattleStrategy()

    def run(self):
        import os

        from modules.items import get_item_bag, get_item_by_name
        from modules.pokemon_party import get_party
        from modules.story.early_game import teach_hm_move, wait_until_truly_controllable

        yield from wait_until_truly_controllable()

        # ‼ `#24-teachmsgstall` FIXTURE (2026-08-08). `TEACH_INJECT=marshtomp` writes the EXACT
        # party shape every one of the 9 teach failures in batch `20260807-160545` had — a
        # Marshtomp-line mon with four moves, one of which is an HM:
        #     moves=['Take Down', 'Mud Shot', 'Rock Smash', 'Muddy Water']   move=Surf
        # No committed save carries that shape (checked: `boxwithdraw.ss1`'s only Surf-compatible
        # mon already knows Surf), and hunting for one is slower and less exact than building it.
        # ‼ The Rock Smash slot is the point, not decoration: `replace_slot` EXCLUDES HM moves,
        # so an HM in the moveset shrinks the eligible set and is a prime suspect for the stall.
        if os.environ.get("TEACH_INJECT", "").strip().lower() == "marshtomp":
            from modules.debug_utilities import debug_create_pokemon, debug_write_party
            from modules.modes.util.sleep import wait_for_n_frames
            from modules.pokemon import LearnedMove, get_move_by_name, get_species_by_name

            # ‼ LEVEL IS A FIXTURE KNOB, NOT A GAME FACT. With TEACH_AFTER_GYM the probe must
            # actually WIN the Norman fight before the teach is reachable, and
            # prenorman_fodder_grind.ss1 cannot (Whismur L18 / Ninjask L27 vs L27-31) — run 2
            # wedged in the gym at f61848 and never reached the teach at all. L45 lets the
            # fixture clear the gym so the thing under test (the battle TAIL) is reached.
            # The failing SHAPE is unchanged: four moves, one of them an HM.
            mon = debug_create_pokemon(
                species=get_species_by_name("Marshtomp"),
                level=int(os.environ.get("TEACH_INJECT_LEVEL", "30")),
                moves=[LearnedMove.create(get_move_by_name(m))
                       for m in ("Take Down", "Mud Shot", "Rock Smash", "Muddy Water")],
                nickname="STALLME",
            )
            # ‼ KEEP THE PARTY FULL AND PUT THE TARGET AT SLOT 4. Run 1 of this fixture wrote a
            # ONE-mon party and the teach SUCCEEDED in 457 frames — so the moveset alone does not
            # reproduce the stall. The batch records mostly read `slot=4`, i.e. a full party with
            # the target in a later slot, which is what makes `scroll_to_party_menu_index` do real
            # work. Substitute in place rather than rebuilding: the other five mons stay exactly
            # as the save has them, so the only changed variable is the target.
            from types import SimpleNamespace as _NS
            _slot = int(os.environ.get("TEACH_INJECT_SLOT", "4"))
            _party = [m for m in get_party() if m is not None]
            _rows = [_NS(data=m.data) for m in _party]
            while len(_rows) <= _slot:
                _rows.append(_NS(data=mon.data))
            _rows[_slot] = _NS(data=mon.data)
            debug_write_party(_rows)
            # ‼ YIELD BEFORE READING THE PARTY BACK. `get_party()` is cached per frame, so the
            # selection loop below sees the PRE-injection party otherwise — run 1 of this
            # fixture printed the old six-mon party and aborted with "no party mon is
            # compatible" on a save that now held exactly the target. Same trap as the
            # `boxwithdraw` heal-fixture logging stale HP (08-MISTAKES 2026-08-07).
            yield from wait_for_n_frames(10)
            log(f"[teachfull] FIXTURE: injected Marshtomp L{mon.level} "
                "[Take Down, Mud Shot, Rock Smash, Muddy Water] — the batch's failing shape")

        # ‼‼ `#24-teachmsgstall` DECISIVE PROBE (2026-08-08). `TEACH_AFTER_GYM=petalburg` fights
        # Norman FIRST, then teaches — which is exactly Segment 12c (`story_mode.py`:
        # `do_petalburg_gym()` then `ensure_hm_learner(HM03)` -> `teach_hm_move`).
        #
        # WHY THIS AND NOT ANOTHER PARTY VARIANT. Two hypotheses were eliminated on 2026-08-08 by
        # direct repro from a clean overworld — the failing MOVESET succeeds in 457 frames and a
        # full party with the target at slot 4 succeeds in 463. So it is the CALLER CONTEXT, and
        # `teach_hm_move`'s own comment already named it: *"all 7 start with the NORMAN BATTLE
        # TAIL still resident (callback=ReturnFromBattleToOverworld), which stretches the
        # dialogue chain past 3,000 frames."* A battle tail is RUNTIME state and cannot be
        # loaded from a save — the fight has to actually happen in the probe.
        #
        # Run from `prenorman_fodder_grind.ss1`. HM03 is GIVEN for beating Norman, so the bag
        # control below doubles as proof the gym leg really completed.
        # ‼‼ THE CHEAP VERSION OF THE SAME EXPERIMENT (2026-08-08). The hypothesis is that a
        # BATTLE TAIL (callback=ReturnFromBattleToOverworld) is still resident when the teach
        # starts — and that does NOT require Norman specifically, only a battle that just ended.
        # TEACH_AFTER_GYM needs the probe to WIN a gym first and wedged three times trying
        # (f61848, f56868) without ever reaching the teach. This spins for any wild battle,
        # then teaches THE INSTANT it ends, with no settle. Same variable, one-line fixture.
        if os.environ.get("TEACH_AFTER_BATTLE", "").strip() in ("1", "true", "yes"):
            from modules.story.early_game import _story_spin
            from modules.battle_handler import battle_is_active

            # ‼‼ THE DETECTOR WAS BLIND, NOT THE SPIN — CORRECTED 2026-08-09, FROM THE LOG.
            # Attempt 6 reported `battle_seen=False frames=2466` and was written down as "the
            # spin produced no encounter". `harness_afterbattle.log` says otherwise:
            # **197 `CONTROLLER -> BattleListener.fight` transitions**, with Marshtomp's EXP
            # climbing 21760 -> 24240 across them. Encounters were never the problem.
            #
            # The old condition polled `battle_is_active()` from inside `_story_spin`'s
            # stop-condition — and the mode's generator is NOT pumped while `BattleListener`
            # owns the controller stack. Only the top of the stack is advanced, so the callback
            # ran on ~2,466 of ~44,000 frames and every one of those frames was, by
            # construction, a frame where no battle was active. It could not have returned True.
            #
            # `on_battle_started` is called by the framework ON THE MODE INSTANCE, so it fires
            # while the generator is suspended. Counting there and reading the count here means
            # the first pump AFTER the battle ends stops the spin — which is precisely the
            # battle-tail-resident moment this fixture is trying to create.
            # ‼ The `not battle_is_active()` guard is load-bearing: without it a stop could land
            # between `on_battle_started` and the listener claiming the stack, and the teach
            # would run INSIDE a battle — a different bug wearing this one's clothes.
            budget = int(os.environ.get("TEACH_SPIN_PUMPS", "40000"))
            log("[teachfull] AFTER-BATTLE: spinning for a wild so a battle tail is resident…")
            seen = {"n": 0}
            self._battles_seen = 0

            def _stop_after_battle() -> bool:
                seen["n"] += 1
                if seen["n"] > budget:
                    return True
                if getattr(self, "_battles_seen", 0) < 1:
                    return False
                try:
                    return not battle_is_active()   # first pump after the battle ends
                except Exception:  # noqa: BLE001
                    return False

            try:
                yield from _story_spin(_stop_after_battle)
                log(f"[teachfull] AFTER-BATTLE: battles={getattr(self, '_battles_seen', 0)} "
                    f"pumps={seen['n']}/{budget} — teaching IMMEDIATELY, no settle")
            except Exception as error:  # noqa: BLE001
                log(f"[teachfull] AFTER-BATTLE spin raised {type(error).__name__}: {str(error)[:160]}")

        # ‼‼ FIXTURE 7 — TEACH IMMEDIATELY AFTER A **CATCH**, NOT AFTER A BATTLE (2026-08-09).
        # WHY THIS AND NOT ANOTHER BATTLE VARIANT. `TEACH_AFTER_BATTLE` has now run twice with a
        # battle tail genuinely resident (`cb=ReturnFromBattleToOverworld`) and the teach
        # SUCCEEDED both times — so "a battle tail is resident" does not, on its own, reproduce
        # `#24-teachmsgstall`. The punch list's description of the production caller names a
        # different tail: `ensure_hm_learner` *"returns the instant the catch registers while
        # 'Give a nickname to the captured X?' is still on screen"*. A CATCH tail and a BATTLE
        # tail are not the same screen, and only one of them is what production does.
        #
        # The catch is detected AFTER the battle ends (party/box count change), which is exactly
        # when the nickname prompt is up — the hazard, not a workaround for it.
        if os.environ.get("TEACH_AFTER_CATCH", "").strip() in ("1", "true", "yes"):
            from modules.pokemon_party import get_party as _gp
            from modules.pokemon_storage import get_pokemon_storage as _gps
            from modules.story.early_game import _story_spin

            budget = int(os.environ.get("TEACH_SPIN_PUMPS", "40000"))

            def _counts() -> tuple[int, int]:
                try:
                    return len([m for m in _gp() if m is not None]), _gps().pokemon_count
                except Exception:  # noqa: BLE001
                    return -1, -1

            # ‼ A FIXTURE MUST BE ABLE TO CREATE ITS CONDITION, AND BOTH HALVES ARE CHECKED.
            # Run 1 of this fixture spun through **125 battles** on `boxwithdraw.ss1` and caught
            # nothing, because that save's bag holds **zero Poké Balls** — measured, not guessed.
            # The `caught=False` guard below turned that into "NOT evidence" instead of a fourth
            # confident non-result. Balls are checked up front for the same reason, and the walk
            # to VERIFIED grass is the same step `--driver boxcatch` needs (a tile picked by eye
            # cost that probe two runs on a non-grass summit tile).
            try:
                from modules.items import get_item_bag

                balls = sum(slot.quantity for slot in get_item_bag().poke_balls)
            except Exception:  # noqa: BLE001
                balls = -1
            if balls == 0:
                log("[teachfull] AFTER-CATCH ABORT — the bag holds NO Poké Balls, so this save "
                    "cannot catch anything and the run could only produce a false negative. "
                    "Use a save with balls (post_winona.ss1 / post_mtpyre.ss1 hold 16).")
                context.set_manual_mode()
                return
            grass_raw = os.environ.get("TEACH_GRASS", "").strip()
            if grass_raw:
                from modules.map_data import MapRSE as _MapRSE
                from modules.story.early_game import _navigate_riding_out as _nav

                gname, _, gtile = grass_raw.partition(":")
                gx, _, gy = gtile.partition(",")
                gmap, gpos = _MapRSE[gname.strip()], (int(gx), int(gy))
                log(f"[teachfull] AFTER-CATCH: walking to verified grass {gmap.name}{gpos}…")
                try:
                    yield from _nav(gmap, gpos, avoid_encounters=False, tries=24)
                except Exception as error:  # noqa: BLE001
                    log(f"[teachfull] AFTER-CATCH ABORT — could not reach the grass: "
                        f"{type(error).__name__}: {str(error)[:180]}")
                    context.set_manual_mode()
                    return

            # ‼ ARM CATCHING ONLY *AFTER* THE WALK — this cost run 2 its entire point. With the
            # flag set before the walk, a wild caught IN TRANSIT (a Nincada) filled the party to
            # 6, so the catch under test could only be a BOX send and the tail on screen was
            # "transferred to SOMEONE'S PC" rather than "Give a nickname to the captured X?".
            # The nickname prompt is the production hazard, and it only appears for a PARTY
            # catch. Arm late, and the party still has room when it matters.
            self._catch_wilds = True          # read by on_battle_started, above

            before = _counts()
            log(f"[teachfull] AFTER-CATCH: spinning to CATCH a wild (party,box)={before} "
                f"balls={balls} — the teach then runs with the catch tail still resident")
            if before[0] >= 6:
                log("[teachfull] ‼ PARTY IS FULL — this run can only test the BOX-SEND tail, not "
                    "production's nickname prompt. Use a save with party room to test that.")
            pumps = {"n": 0}

            def _stop_after_catch() -> bool:
                pumps["n"] += 1
                if pumps["n"] > budget:
                    return True
                return _counts() != before

            try:
                yield from _story_spin(_stop_after_catch)
                after = _counts()
                log(f"[teachfull] AFTER-CATCH: caught={after != before} (party,box) {before} -> "
                    f"{after} battles={getattr(self, '_battles_seen', 0)} pumps={pumps['n']}/{budget}")
                if after == before:
                    log("[teachfull] ‼ NO CATCH — this run is NOT evidence about the teach. "
                        "Fix the fixture (ball supply / catchable wilds) before reading a result.")
            except Exception as error:  # noqa: BLE001
                log(f"[teachfull] AFTER-CATCH spin raised {type(error).__name__}: {str(error)[:160]}")

        # ‼‼ FIXTURE 9 — TEACH IMMEDIATELY AFTER A **TRAINER** BATTLE (2026-08-09).
        # This is the tail the production failures actually carry, read out of the batch's own
        # debug logs (`x4-runs/20260807-160545`):
        #     callback=ReturnFromBattleToOverworld  instr=BattleScript_PayDayMoneyAndPickUpItems
        #     battle_text='H2 got $3100 for winning!'
        #     tasks=['Task_ContinueTaskAfterMessagePrints', 'ListMenuDummyTask']
        # Fixtures 6/7/8 all used WILD battles and all taught successfully, so "which tail" is
        # the last untested variable.
        #
        # ‼ DO NOT DO THIS BY WINNING A GYM. Attempts 3-5 tried and wedged in the gym three
        # times (f61848, f56868) without ever reaching the teach. ANY trainer is enough, so this
        # walks a patrol between two tiles and lets `TrainerApproachListener` do the work.
        if os.environ.get("TEACH_AFTER_TRAINER", "").strip() in ("1", "true", "yes"):
            from modules.map_data import MapRSE as _MapRSE
            from modules.story.early_game import _navigate_riding_out as _nav

            def _parse(raw, default):
                name, _, tile = (raw or default).partition(":")
                x, _, y = tile.partition(",")
                return _MapRSE[name.strip()], (int(x), int(y))

            a_map, a_tile = _parse(os.environ.get("TEACH_PATROL_A"), "ROUTE116:11,7")
            b_map, b_tile = _parse(os.environ.get("TEACH_PATROL_B"), "ROUTE116:47,9")
            laps = int(os.environ.get("TEACH_PATROL_LAPS", "4"))
            self._trainers_seen = 0
            log(f"[teachfull] AFTER-TRAINER: patrolling {a_map.name}{a_tile} <-> {b_map.name}{b_tile} "
                f"for up to {laps} laps until a TRAINER engages…")
            for lap in range(1, laps + 1):
                for dest_map, dest_tile in ((a_map, a_tile), (b_map, b_tile)):
                    if getattr(self, "_trainers_seen", 0) > 0:
                        break
                    try:
                        yield from _nav(dest_map, dest_tile, avoid_encounters=True, tries=24)
                    except Exception as error:  # noqa: BLE001
                        log(f"[teachfull] AFTER-TRAINER lap {lap} leg failed: "
                            f"{type(error).__name__}: {str(error)[:140]}")
                log(f"[teachfull] AFTER-TRAINER lap {lap}: trainers={getattr(self, '_trainers_seen', 0)} "
                    f"battles={getattr(self, '_battles_seen', 0)}")
                if getattr(self, "_trainers_seen", 0) > 0:
                    break

            trainers = getattr(self, "_trainers_seen", 0)
            log(f"[teachfull] AFTER-TRAINER: trainers={trainers} — teaching IMMEDIATELY, no settle")
            if trainers == 0:
                # ‼ Same guard as the catch fixture: a run that never created its condition is
                # NOT evidence about the teach, and must not be read as one.
                log("[teachfull] ‼ NO TRAINER ENGAGED — this run is NOT evidence. The patrol maps "
                    "probably have no undefeated trainers left; pick a route the save has not "
                    "cleared (TEACH_PATROL_A / TEACH_PATROL_B).")

        if os.environ.get("TEACH_AFTER_GYM", "").strip().lower() == "petalburg":
            from modules.story.early_game import do_petalburg_gym

            # FIXTURE: `prenorman_fodder_grind.ss1` is a GRIND save, so the party arrives hurt
            # and loses the gym before the teach is ever reached. Same HP/status restore the
            # `boxwithdraw` fixture uses; the variable under test is the post-battle TAIL, not
            # whether a battered party can win Norman.
            try:
                from types import SimpleNamespace as _NS2

                from modules.debug_utilities import debug_write_party as _dwp
                from modules.modes.util.sleep import wait_for_n_frames as _wfn

                _rows2 = []
                for _m in get_party():
                    if _m is None:
                        continue
                    _d = bytearray(_m.data)
                    if len(_d) >= 90:
                        _d[86:88] = _d[88:90]
                        _d[80:84] = bytes(4)   # clear the status bitfield
                    _rows2.append(_NS2(data=bytes(_d)))
                _dwp(_rows2)
                yield from _wfn(10)
                log(f"[teachfull] AFTER-GYM fixture: healed {len(_rows2)} party mons")
            except Exception as _e:  # noqa: BLE001
                log(f"[teachfull] AFTER-GYM heal fixture failed: {type(_e).__name__}: {_e}")

            log("[teachfull] AFTER-GYM: fighting Norman first so the battle tail is resident…")
            try:
                yield from do_petalburg_gym()
                log("[teachfull] AFTER-GYM: gym returned — teaching IMMEDIATELY, no settle")
            except Exception as error:  # noqa: BLE001
                log(f"[teachfull] AFTER-GYM: gym raised {type(error).__name__}: {str(error)[:200]}")

        item_name = os.environ.get("TEACH_ITEM", "HM06").strip()
        item = get_item_by_name(item_name)
        move = item.tm_hm_move()
        # ‼ PROVE THE FIX'S PREMISE BEFORE THE FIX IS WRITTEN. The proposed repair gates
        # `normalize_to_overworld`'s settle on "a message is still printing"
        # (`Task_ContinueTaskAfterMessagePrints`). That only helps if the message chain is
        # ALREADY RUNNING when the teach takes over — if it only starts later, after the bag is
        # open, the gate would settle before there is anything to see and the fix would be
        # INERT. This line is the measurement that decides it, taken at the hand-off instant.
        try:
            from modules.player import player_avatar_is_controllable as _ctrl

            _t = sorted(t.symbol for t in get_tasks())
            log(f"[teachfull] HANDOFF-STATE controllable={_ctrl()} "
                f"cb={get_main_battle_callback()} instr={get_current_battle_script_instruction()}")
            log(f"[teachfull] HANDOFF-STATE message_task_active="
                f"{'Task_ContinueTaskAfterMessagePrints' in _t} tasks={_t}")
        except Exception as _error:  # noqa: BLE001
            log(f"[teachfull] HANDOFF-STATE unreadable: {type(_error).__name__}: {_error}")

        log(f"[teachfull] item={item_name} teaches {getattr(move, 'name', '?')}")

        # ‼ POSITIVE CONTROL: the bag must actually hold it. Without this a missing HM looks
        # exactly like a broken teach flow — the bag scroll simply never finds the item and the
        # flow dies at `Task_CallYesOrNoCallback never appeared`, which reads as the bug.
        # ‼ AND THE CONTROL ITSELF NEEDS ONE. Run 1 of this driver reported "HM06 is not in the
        # TM/HM case" on a save that has it: I wrote `get_item_bag().tm_hm_case`, the pocket is
        # `tms_hms` (`modules/items.py:368`), and a bare `except` turned the AttributeError into
        # a confident False. Use the intended `quantity_of()` API and let an error be LOUD — a
        # guard that reports a clean negative when it is itself broken is worse than no guard.
        have = get_item_bag().quantity_of(item)
        log(f"[teachfull] bag holds {have}x {item_name}")
        if have <= 0:
            log(f"[teachfull] ABORT — {item_name} is not in the bag on this save. "
                f"A missing item mimics the bug exactly; pick a save that has it.")
            context.set_manual_mode()
            return

        # The DISCRIMINATING target: compatible, four moves already, does not know it yet.
        # ‼ `TEACH_MIN_MOVES=1` selects a mon with a FREE SLOT instead — the positive control for
        # the OTHER branch. `#24-teachpathrace`'s fix gates the instant-learn exit on a genuinely
        # free slot, so "the replace path still works" is only half a proof: a gate that is too
        # tight would strand every free-slot teach in the 900-frame loop instead, and the replace
        # test cannot see that.
        min_moves = int(os.environ.get("TEACH_MIN_MOVES", "4"))
        want_slot = os.environ.get("TEACH_SLOT")
        target, why = None, []
        for i, mon in enumerate(get_party()):
            if mon is None or mon.is_egg:
                continue
            moves = [l for l in mon.moves if l is not None]
            knows = any(l.move.name == move.name for l in moves)
            compat = mon.species.can_learn_tm_hm(item)
            why.append(f"{i}:{mon.species.name} moves={len(moves)} compat={compat} knows={knows}")
            if want_slot is not None:
                if i == int(want_slot):
                    target = i
            elif compat and not knows and len(moves) >= min_moves and target is None:
                target = i
        log(f"[teachfull] party — {why}")
        log(f"[teachfull] selection: min_moves={min_moves} want_slot={want_slot}")
        if target is None:
            log("[teachfull] ABORT — no party mon is compatible, ignorant of the move AND has "
                "4 moves. That combination IS the test; without it this driver measures the "
                "instant-learn path that `hmtest` already covers.")
            context.set_manual_mode()
            return

        mon = get_party()[target]
        before = [l.move.name for l in mon.moves if l is not None]
        log(f"[teachfull] target=slot {target} {mon.species.name} L{mon.level} moves={before}")

        try:
            yield from teach_hm_move(item, target)
            log("[teachfull] teach_hm_move returned without raising")
        except Exception as error:  # noqa: BLE001
            log(f"[teachfull] teach_hm_move RAISED {type(error).__name__}: {str(error)[:250]}")

        after = [l.move.name for l in get_party()[target].moves if l is not None]
        learned = move.name in after
        lost = [m for m in before if m not in after]
        log(f"[teachfull] RESULT learned={learned} target={mon.species.name} "
            f"replaced={lost} before={before} after={after}")
        log("[teachfull] ‼ Read the `TEACH EXIT` / `TEACH OK` lines in the debug log for the "
            "exit reason, ride_frames and stall_peak.")
        context.set_manual_mode()
        return


class MagmaDoorMode(BotMode):
    """`#24-magmahideout`: can the bot ENTER the Magma Hideout? Scripted movement, not the planner.

    ‼ WHY SCRIPTED. The tile planner cannot route to the hideout door at JAGGED_PASS (16,18) from
    ANY entry — measured 2026-08-10 from both MT_CHIMNEY warps, the ROUTE112 warp, and the bot's
    own in-descent position, every time with a passing control. Worse, a catchment scan found
    **only 3 tiles in the whole map that can reach the door** — `(16,17)/(16,18)/(16,19)`, its own
    column — with **zero** overlap with the 272 tiles the bot can reach. A 3-tile island is not
    game design, it is a modelling artifact (the KI-24 class).

    ‼ THE ELEVATION MAP IS WHAT GIVES IT AWAY, and it is why this driver is 3 button presses:
        (15,19) elev=3 REACHABLE | (16,19) elev=3 NOT reachable | (17,19) elev=3 REACHABLE
                                 | (16,18) elev=0 = THE DOOR    | (16,20) elev=3 REACHABLE
    `(16,19)` is walkable and at the SAME elevation as three reachable neighbours, and the planner
    still refuses it. So: navigate normally to `(16,20)` — which the planner CAN reach — then walk
    NORTH twice by hand, onto `(16,19)` and then onto the door.

        PYTHONUTF8=1 py -3.12 story_harness.py jagged_descent.ss1 --driver magmadoor --frames 300000

    Emits: [magmadoor] RESULT reached_2016=<bool> stepped_1619=<bool> entered=<map> badges=<list>
    ‼ ERA: `jagged_descent.ss1` is badges 1-3, BEFORE the Magma Emblem. If the warp does not fire
    the REACHABILITY result still stands and is the thing under test — read the two booleans, not
    just `entered`.
    """

    @staticmethod
    def name():
        return "MagmaDoor"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

            return LevelUpTravelBattleStrategy()
        return DefaultBattleStrategy()

    def run(self):
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag
        from modules.modes.util.sleep import wait_for_n_frames
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

        yield from wait_until_truly_controllable()

        def here():
            a = get_player_avatar()
            return tuple(a.map_group_and_number), tuple(a.local_coordinates)

        log(f"[magmadoor] start {here()}")
        reached = False
        try:
            yield from _navigate_riding_out(MapRSE.JAGGED_PASS, (16, 20), tries=24)
            reached = here()[1] == (16, 20)
        except Exception as error:  # noqa: BLE001
            log(f"[magmadoor] navigation to (16,20) FAILED: {type(error).__name__}: {str(error)[:160]}")
        log(f"[magmadoor] after navigate: {here()} reached_2016={reached}")

        # ‼ TRY EVERY APPROACH TO (16,19), because the first one FAILED and that was informative.
        # Pressing Up from (16,20) 12x did not move the avatar, so there is a real south-facing
        # LEDGE on that edge — the planner was right about it and my elevation reasoning was wrong.
        # (16,19) also touches (15,19) and (17,19), both of which the planner CAN reach, so the
        # remaining question is whether either side can be walked in.
        approaches = [((16, 20), "Up"), ((15, 19), "Right"), ((17, 19), "Left")]
        stepped = False
        for tile, button in approaches:
            if stepped:
                break
            try:
                yield from _navigate_riding_out(MapRSE.JAGGED_PASS, tile, tries=16)
            except Exception as error:  # noqa: BLE001
                log(f"[magmadoor] could not reach staging tile {tile}: {type(error).__name__}")
                continue
            if here()[1] != tile:
                log(f"[magmadoor] staging {tile} not reached (at {here()[1]})")
                continue
            for _ in range(10):
                context.emulator.press_button(button)
                yield from wait_for_n_frames(8)
                if here()[1] == (16, 19):
                    stepped = True
                    break
            log(f"[magmadoor] approach from {tile} pressing {button}: "
                f"now {here()[1]} stepped={stepped}")

        if stepped:
            for attempt in range(16):
                context.emulator.press_button("Up")
                yield from wait_for_n_frames(8)
                if here()[0] != tuple(MapRSE.JAGGED_PASS.value):
                    break

        try:
            final_map = MapRSE(here()[0]).name
        except Exception:  # noqa: BLE001
            final_map = str(here()[0])
        badges = [n for n in range(1, 9) if get_event_flag(f"BADGE0{n}_GET")]
        log(f"[magmadoor] RESULT reached_2016={reached} stepped_1619={stepped} "
            f"entered={final_map} at={here()[1]} badges={badges}")
        context.set_manual_mode()
        return


class MagmaTravelMode(BotMode):
    """`#24-magmahideout` INCREMENT 1 — drive the real travel leg to the hideout door.

    WHAT IS UNDER TEST: `modules.story.early_game.travel_to_magma_hideout_door()`, i.e. the
    production routine, not a hand-rolled probe path. That distinction is the whole point —
    the one measured failure against this chapter is an `--driver anchorcapture` run from
    `post_mtpyre.ss1` that whited out at f24808, and that driver has no prep and no heal.
    This one goes through the normal heal/prep path, which is the difference being measured.

        PYTHONUTF8=1 py -3.12 story_harness.py post_mtpyre.ss1 --driver magmatravel --frames 900000

    ‼ ERA: it MUST be run from a post-Emblem anchor. `probe_magma_anchor.py` reports
    `post_mtpyre.ss1` as READY (guard flag True, MT_PYRE_STATE=1, Emblem in bag) and
    `jagged_descent.ss1` as the wrong era. Running this from a pre-Emblem save measures the
    Team Magma guard, which is exactly the error that cost seven probes on 2026-08-10.

    ACCEPTANCE — BINARY, no statistics: `arrived=True`, i.e. standing on JAGGED_PASS (16,20).

    ON SUCCESS IT CAPTURES AN ANCHOR (`saves/magma_door.ss1`) so increments 2 and 3 can be
    developed against the door in seconds instead of re-driving the whole journey. Set
    `MAGMA_TRAVEL_CAPTURE=0` to suppress.

    Emits: [magmatravel] RESULT arrived=<bool> map=<enum> at=<tile> guard_hidden=<bool>
           party_alive=<n>/<n> frames=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "MagmaTravel"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            # Trainers on the pass are fought with the story's own travel strategy, so the
            # run measures the trip the BOT would make, not an idealised one.
            from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

            return LevelUpTravelBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        """‼ MATCH PRODUCTION. `BotMode.on_whiteout` defaults to **False**, which drops the bot
        to Manual — and StoryMode OVERRIDES it to True and recovers (`story_mode.py:1221`).

        Without this override the first two runs of this driver (2026-08-10) both ended at the
        identical frame f23674 on ROUTE123 and were read as "the travel leg fails". They were
        reading the DRIVER's default, not the route: in the real bot a whiteout is a survivable
        event that respawns a FULL party at the last Pokémon Center. This is precisely the
        "probe with the SAME call the production path uses" rule (08-MISTAKES 2026-07-30).

        The whiteout count is REPORTED, never hidden — the party this chapter inherits from
        Ch14 is 3/6 fainted, so how many whiteouts the trip costs is a real result."""
        MagmaTravelMode._whiteouts += 1
        log(f"[magmatravel] WHITEOUT #{MagmaTravelMode._whiteouts} — recovering, as StoryMode does")
        return True

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var
        from modules.player import get_player_avatar
        from modules.pokemon_party import get_party
        from modules.story.early_game import (
            MAGMA_HIDEOUT_DOOR_APPROACH,
            travel_to_magma_hideout_door,
            wait_until_truly_controllable,
        )

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        def map_name(group_and_number):
            try:
                return MapRSE(group_and_number).name
            except ValueError:
                return str(group_and_number)

        # ‼ ERA ASSERTION FIRST, and LOUDLY. A run from the wrong save produces a confident
        # failure about terrain, which is precisely the wrong conclusion this chapter has
        # already produced twice.
        guard_hidden = get_event_flag("HIDE_JAGGED_PASS_MAGMA_GUARD")
        pyre_state = get_event_var("MT_PYRE_STATE")
        log(f"[magmatravel] START {map_name(here()[0])} {here()[1]} "
            f"guard_hidden={guard_hidden} MT_PYRE_STATE={pyre_state}")
        if not guard_hidden:
            log("[magmatravel] ‼ WRONG ERA — the Magma guard is still on (16,19). This run "
                "would measure the guard, not the route. Use a post-Emblem anchor.")

        arrived = False
        error_text = ""
        # ‼ RETRY, because `travel_to_magma_hideout_door()` is resume-safe and a whiteout is a
        # NORMAL event for this party — it respawns a full team at the last Pokémon Center, from
        # which the trip is genuinely easier. StoryMode's own loop re-enters a chapter the same
        # way. Bounded at 4 so a hopeless party cannot spin: the ATTEMPT COUNT is a result.
        attempts = 0
        for attempt in range(1, 5):
            attempts = attempt
            try:
                yield from wait_until_truly_controllable()
                yield from travel_to_magma_hideout_door()
                arrived = (
                    here()[0] == tuple(MapRSE.JAGGED_PASS.value)
                    and here()[1] == MAGMA_HIDEOUT_DOOR_APPROACH
                )
                if arrived:
                    error_text = ""
                    break
                error_text = f"attempt {attempt} finished at {map_name(here()[0])} {here()[1]}"
                log(f"[magmatravel] {error_text}")
            except Exception as error:  # noqa: BLE001 - the failure IS the measurement
                error_text = f"{type(error).__name__}: {str(error)[:220]}"
                log(f"[magmatravel] attempt {attempt} FAILED: {error_text}")
            log(f"[magmatravel] retrying from {map_name(here()[0])} {here()[1]} "
                f"(whiteouts so far: {MagmaTravelMode._whiteouts})")

        party = get_party()
        alive = sum(1 for mon in party if mon.current_hp > 0)
        # ‼ `opened` is the REAL acceptance, not `arrived`. The door at (16,18) is covered by
        # a rock-wall metatile until `JaggedPass_EventScript_OpenMagmaHideout` sets
        # VAR_JAGGED_PASS_STATE to 2, and NO static path check can see that wall — standing
        # beside a sealed door would otherwise read as success.
        jagged_state = get_event_var("JAGGED_PASS_STATE")
        opened = jagged_state >= 2
        log(f"[magmatravel] RESULT arrived={arrived} opened={opened} "
            f"JAGGED_PASS_STATE={jagged_state} map={map_name(here()[0])} at={here()[1]} "
            f"guard_hidden={guard_hidden} party_alive={alive}/{len(party)} "
            f"whiteouts={MagmaTravelMode._whiteouts} attempts={attempts} "
            f"frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        arrived = arrived and opened

        if arrived and os.environ.get("MAGMA_TRAVEL_CAPTURE", "1") != "0":
            out = SAVES / "magma_door.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[magmatravel] captured anchor -> {out}")

        context.set_manual_mode()
        return


class MossdeepTravelMode(BotMode):
    """§Ch18 leg 1 — cross Lilycove -> Mossdeep and stand INSIDE the gym, then capture the anchor.

        PYTHONUTF8=1 py -3.12 story_harness.py post_aqua.ss1 --driver mossdeeptravel \
            --frames 500000 --profile ch18a

    ‼ THIS EXISTS FOR TWO REASONS AT ONCE, and the second is why it is worth its own driver.
    (1) It is §Ch18's first leg: the party has to get to Mossdeep before anything else happens.
    (2) It unblocks **KI-58**. The gym maze could not be reconned because `map_path` blocks every
        tile carrying an object template whose object is not in `active_objects` — and
        `active_objects` comes from the CURRENTLY LOADED map. Reconning a **36-object** gym from a
        save inside the Aqua Hideout turned all 21 statue tiles into pessimistic walls. A save
        STANDING IN THE GYM makes them live objects at their real positions, which is the only way
        the route question can be asked honestly.

    ANCHOR: `saves/post_aqua.ss1` — post-Ch17, party ~90%, Master Ball held.
    ROUTE: `MOSSDEEP_CITY (38,9)` is the gym door (ROM warp table).

    ACCEPTANCE: standing on `MOSSDEEP_CITY_GYM`, controllable. Captures
    `saves/in_mossdeep_gym.ss1` on success only.

    ‼ WHAT IS MOST LIKELY TO FAIL, said in advance: the crossing needs **Surf** over Routes
    124/125, and this is the first leg in the project to go that way. A failure here is a TRAVEL
    result, not a gym result — the log distinguishes them.

    Emits: [ch18] RESULT in_gym=<bool> map=<enum> at=<tile> controllable=<bool> whiteouts=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "MossdeepTravel"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        MossdeepTravelMode._whiteouts += 1
        log(f"[ch18] WHITEOUT #{MossdeepTravelMode._whiteouts} - recovering, as StoryMode does")
        return True

    def run(self):
        import os

        from modules.map_data import MapRSE, PokemonCenter
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.modes.util.higher_level_actions import heal_in_pokemon_center
        from modules.story.early_game import (
            _enter_warp_by_navigation,
            _navigate_riding_out,
            wait_until_truly_controllable,
        )

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001 - report the raw tuple rather than crash
                return f"?{mgn}({type(error).__name__})"

        GYM_DOOR = (38, 9)  # MOSSDEEP_CITY warp 1 -> MOSSDEEP_CITY_GYM

        def in_gym() -> bool:
            return here()[0] == MapRSE.MOSSDEEP_CITY_GYM.value

        mgn, tile = here()
        log(f"[ch18] START {map_name(mgn)}{tile}")

        error_text = ""
        try:
            # ‼ HEAL FIRST — the §Ch16 lesson applied at build time, not after losing a run.
            # Lilycove's centre is on the way out; a long Surf crossing on a damaged party is
            # exactly the shape that whited out on the Slateport haul.
            try:
                log("[ch18] healing at Lilycove before the crossing...")
                yield from _navigate_riding_out(MapRSE.LILYCOVE_CITY, (24, 15))
                yield from heal_in_pokemon_center(PokemonCenter.LilycoveCity)
                yield from wait_until_truly_controllable()
            except Exception as error:  # noqa: BLE001 - a lost heal stop is not a lost run, but
                # it is always REPORTED, so "healed" and "could not" never look alike.
                log(f"[ch18] heal SKIPPED - {type(error).__name__}: {str(error)[:160]}")

            log("[ch18] crossing to Mossdeep (needs Surf over Routes 124/125)...")
            yield from _navigate_riding_out(MapRSE.MOSSDEEP_CITY, (38, 10))
            yield from wait_until_truly_controllable()
            log(f"[ch18] reached {map_name(here()[0])}{here()[1]}; entering the gym...")

            yield from _enter_warp_by_navigation(
                in_gym, MapRSE.MOSSDEEP_CITY, GYM_DOOR, label="Mossdeep Gym door"
            )
            yield from wait_until_truly_controllable()
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[ch18] FAILED: {error_text}")

        mgn, tile = here()
        try:
            ctrl = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001
            ctrl = f"<unreadable: {type(error).__name__}>"
        ok = in_gym() and ctrl is True
        log(f"[ch18] RESULT in_gym={in_gym()} map={map_name(mgn)} at={tile} controllable={ctrl} "
            f"whiteouts={MossdeepTravelMode._whiteouts} frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        log(f"[ch18] ACCEPTANCE: {'PASS' if ok else 'FAIL'} (needs to be standing in the gym, controllable)")

        if ok and os.environ.get("CH18_CAPTURE", "1") != "0":
            out = SAVES / "in_mossdeep_gym.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[ch18] captured anchor -> {out}")

        context.set_manual_mode()
        return


class MossdeepGymMode(BotMode):
    """§Ch18 leg 2 — solve the rotating-tile statue puzzle and reach Tate & Liza.

        PYTHONUTF8=1 py -3.12 story_harness.py in_mossdeep_gym.ss1 --driver mossdeepgym             --frames 400000 --profile ch18b

    ANCHOR: `saves/in_mossdeep_gym.ss1`, captured by `--driver mossdeeptravel` on a PASS. It stands
    on `MOSSDEEP_CITY_GYM` at the entrance, with the puzzle provably in its START configuration
    (entering the gym reloads every object template from ROM).

    WHAT IT DRIVES: `modules.story.mossdeep_gym.walk_to_the_leaders()`, which solves the puzzle on
    the model validated by `probe_gym_simulate.py` (11/11 objects predicted on a live press) and
    re-solves after every interruption.

    ACCEPTANCE: standing on one of the leader-approach tiles `(23,8)/(24,8)`, controllable. That is
    deliberately NOT "beat the gym" — this leg is the puzzle, and grading it separately keeps a
    navigation failure distinguishable from a battle failure.

    ‼ WHAT IS MOST LIKELY TO FAIL, said in advance. **Gym trainer battles are expected**, not a
    derail: nine trainers stand on the rotating pads and every rotation re-aims them. The run
    should show several `interrupted ... riding it out` lines followed by a fresh plan. What would
    be a genuine fault is a `drifted from the game` abort, which means the simulated statue map and
    the real one disagree — the model, not the gym, would then be wrong.

    Emits: [ch18b] RESULT at_leaders=<bool> map=<enum> at=<tile> controllable=<bool> whiteouts=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "MossdeepGym"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        MossdeepGymMode._whiteouts += 1
        log(f"[ch18b] WHITEOUT #{MossdeepGymMode._whiteouts} - recovering, as StoryMode does")
        return True

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.story.early_game import wait_until_truly_controllable
        from modules.story.mossdeep_gym import LEADER_APPROACH_TILES, walk_to_the_leaders

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001 - report the raw tuple rather than crash
                return f"?{mgn}({type(error).__name__})"

        def at_leaders() -> bool:
            mgn, tile = here()
            return mgn == MapRSE.MOSSDEEP_CITY_GYM.value and tile in LEADER_APPROACH_TILES

        mgn, tile = here()
        log(f"[ch18b] START {map_name(mgn)}{tile}")

        error_text = ""
        try:
            yield from walk_to_the_leaders()
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[ch18b] FAILED: {error_text}")

        mgn, tile = here()
        try:
            ctrl = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001
            ctrl = f"<unreadable: {type(error).__name__}>"
        ok = at_leaders() and ctrl is True
        log(f"[ch18b] RESULT at_leaders={at_leaders()} map={map_name(mgn)} at={tile} "
            f"controllable={ctrl} whiteouts={MossdeepGymMode._whiteouts} "
            f"frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        log(f"[ch18b] ACCEPTANCE: {'PASS' if ok else 'FAIL'} "
            f"(needs to be standing on {sorted(LEADER_APPROACH_TILES)}, controllable)")

        if ok and os.environ.get("CH18B_CAPTURE", "1") != "0":
            out = SAVES / "at_mossdeep_leaders.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[ch18b] captured anchor -> {out}")

        context.set_manual_mode()
        return


class MossdeepBadgeMode(BotMode):
    """Ch18 END TO END - drive `do_mossdeep_gym_chapter()` and grade it on the Mind Badge.

        PYTHONUTF8=1 py -3.12 story_harness.py at_mossdeep_leaders.ss1 --driver mossdeepbadge \
            --frames 400000 --profile ch18c

    ANCHORS: `saves/at_mossdeep_leaders.ss1` (standing at (23,8), puzzle already solved - the fast
    way to exercise the BATTLE) or `saves/in_mossdeep_gym.ss1` (at the gym door - exercises the
    whole chapter, puzzle included). The chapter is resume-safe and handles both.

    ACCEPTANCE IS BOTH HALVES: `BADGE07_GET` AND controllable. Grading on the flag alone would call
    a `lockall`ed avatar a success, because the badge is set MID-SCRIPT - the
    `EventScript_ActivateStrength` trap that KI-56 was built on.

    WHAT IS MOST LIKELY TO FAIL, said in advance. Tate & Liza are a DOUBLE battle and the game sends
    out the first TWO party slots. On the current anchor that is Sceptile L47 and **Zigzagoon L15**,
    which will faint almost immediately; the run is expected to win anyway on the strength of the
    rest, but a whiteout is the realistic failure. A whiteout is EXPENSIVE here: it leaves the gym,
    and leaving RESETS the statue puzzle, so the chapter re-enters and re-solves all 117 steps. It
    allows three attempts before failing.

    Emits: [ch18c] RESULT badge=<bool> map=<enum> at=<tile> controllable=<bool> whiteouts=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "MossdeepBadge"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        MossdeepBadgeMode._whiteouts += 1
        log(f"[ch18c] WHITEOUT #{MossdeepBadgeMode._whiteouts} - recovering, as StoryMode does")
        return True

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.memory import get_event_flag
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party
        from modules.story.early_game import wait_until_truly_controllable
        from modules.story.mossdeep_gym import do_mossdeep_gym_chapter

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001 - report the raw tuple rather than crash
                return f"?{mgn}({type(error).__name__})"

        mgn, tile = here()
        try:
            party = " ".join(f"{m.species.name}:L{m.level}:{m.current_hp}/{m.total_hp}"
                             for m in get_party() if m is not None)
        except Exception as error:  # noqa: BLE001 - an unreadable party is reported, not hidden
            party = f"<unreadable: {type(error).__name__}>"
        log(f"[ch18c] START {map_name(mgn)}{tile} badge={get_event_flag('BADGE07_GET')}")
        log(f"[ch18c] PARTY {party}")

        error_text = ""
        try:
            yield from do_mossdeep_gym_chapter()
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[ch18c] FAILED: {error_text}")

        mgn, tile = here()
        try:
            ctrl = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001
            ctrl = f"<unreadable: {type(error).__name__}>"
        badge = get_event_flag("BADGE07_GET")
        # ‼ THE TEST MUST INCLUDE "AND THE BOT CAN CONTINUE". Grading on badge+controllable alone
        # passed a version of this chapter that left the avatar on (23,8) - an eleven-tile collision
        # island whose only exit is a coord event. Measured: calculate_path((23,8) -> (7,35)) raises.
        # That is KI-56's prevention rule, and it had to be learned twice.
        out_of_gym = mgn == MapRSE.MOSSDEEP_CITY.value
        ok = badge and ctrl is True and out_of_gym
        log(f"[ch18c] RESULT badge={badge} map={map_name(mgn)} at={tile} controllable={ctrl} "
            f"whiteouts={MossdeepBadgeMode._whiteouts} frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        log(f"[ch18c] ACCEPTANCE: {'PASS' if ok else 'FAIL'} (needs BADGE07_GET AND controllable "
            f"AND out of the gym; out_of_gym={out_of_gym})")

        if ok and os.environ.get("CH18C_CAPTURE", "1") != "0":
            out = SAVES / "post_mossdeep_gym.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[ch18c] captured anchor -> {out}")

        context.set_manual_mode()
        return


class StoryWhiteoutRecoveryMixin:
    """Makes a DRIVER behave like `StoryMode` on a whiteout — all four parts, or none of them.

    ‼‼ WHY THIS EXISTS (KI-67). Production signals a whiteout with a PROCESS-GLOBAL abort latch:
    `StoryMode.on_whiteout` sets it, `_check_abort()` raises `StoryAbort` inside whatever wait loop
    is running, and **only `StoryMode.run` ever clears it**. The eleven harness drivers mirrored
    exactly ONE of those four things — `return True` — and never set the latch. Consequence:
    `_check_abort()` was DEAD CODE under test, so every "the retry loop is whiteout recovery" claim
    in the chapter docstrings was untested prose. The bug fixed in KI-67 had been invisible for
    precisely this reason: **in the harness the retry loops ran in their working configuration
    while production ran the broken one.**

    ‼‼ AND WHY IT IS A MIXIN RATHER THAN A ONE-LINE EDIT PER DRIVER. Two independent reviews warned
    that adding `set_story_abort(True)` to a driver WITHOUT also mirroring the clear-and-retry loop
    turns the latch into a ONE-WAY DOOR: nothing else clears it, so every later `_check_abort()`
    raises for ever and drivers that pass today would go red over CORRECT production code, while
    committed anchors quietly stopped refreshing. Half a mirror is worse than none. Putting all four
    parts in one place is what stops the halves drifting apart again.

    THE FOUR PARTS, mirroring `story_mode.py`:
      1. `on_whiteout` sets the latch AND `_whiteout_pending`, and returns True;
      2. the chapter runs inside a clear-and-retry loop that clears the latch at the top;
      3. the whiteout branch clears the latch BEFORE navigating, then rides the respawn out
         exactly as production does (controllable -> leave the Poké Center -> settle -> controllable);
      4. the recovery count is reported, so a fabricated-failure regression is visible in the log.

    ‼ AND THE LATCH IS CLEARED IN A `finally`. It is a module-global in `early_game`, shared by every
    probe and driver in the process. Leaving it set on the way out would make the NEXT thing that
    runs abort instantly for no visible reason — a bug that would look like anything but this.
    """

    _whiteout_pending = False
    _whiteouts = 0
    _recoveries = 0

    def __init_subclass__(cls, **kwargs):
        """‼ REFUSE A DRIVER THAT SILENTLY UN-MIXES ITSELF.

        Ten other drivers still define their own `on_whiteout`. Adding this mixin to one WITHOUT
        deleting that method makes the subclass method win under the MRO: the latch is never set,
        and the driver *looks* converted while behaving exactly as before. That invisibility is the
        precise reason KI-67 survived unnoticed for so long, so it is made impossible rather than
        written down as a rule."""
        super().__init_subclass__(**kwargs)
        if "on_whiteout" in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} mixes in StoryWhiteoutRecoveryMixin but defines its own "
                "on_whiteout(), which would override the mixin's and silently stop setting the "
                "abort latch. Delete the driver's on_whiteout - the mixin IS the behaviour."
            )

    def on_whiteout(self) -> bool:
        # ‼ MIRRORS `StoryMode.on_whiteout` — the latch is the half every driver was missing.
        # ‼ CALLED FROM THE LISTENER'S STACK, not the mode generator, so anything that raises here
        # kills the run before the RESULT line is ever printed. `tag` is therefore read defensively:
        # an adopter that forgot to define one would otherwise die with an AttributeError *after*
        # the latch had already been set.
        from modules.story.early_game import set_story_abort

        set_story_abort(True)
        self._whiteout_pending = True
        type(self)._whiteouts += 1
        tag = getattr(self, "tag", type(self).__name__)
        log(f"[{tag}] WHITEOUT #{type(self)._whiteouts} - latch set, recovering as StoryMode does "
            f"(frame {context.emulator.get_frame_count()})")
        return True

    def drive_with_recovery(self, make_generator, *, max_recoveries: int = 3):
        """Run `make_generator()` to completion, recovering from whiteouts the way production does.

        Returns `None` on success, or the `BotModeError` that ended it. ‼ A NON-whiteout failure is
        returned IMMEDIATELY and never retried: that is the driver's measurement, and retrying it
        would only hide it."""
        from modules.memory import GameState, game_has_started, get_game_state
        from modules.modes import BotModeError
        from modules.modes.util.walking import wait_for_player_avatar_to_be_controllable
        from modules.story.early_game import exit_building_after_whiteout, set_story_abort

        tag = getattr(self, "tag", type(self).__name__)
        # ‼ BUDGET IS A DELTA, NOT AN ABSOLUTE. `_recoveries` is a CLASS counter that is never
        # reset, so comparing it directly to a per-call `max_recoveries` would let a second call
        # to this helper inherit the first call's spend and give up immediately.
        recoveries_at_entry = type(self)._recoveries
        last_error = None
        try:
            for attempt in range(1, max_recoveries + 2):
                set_story_abort(False)
                self._whiteout_pending = False
                try:
                    yield from make_generator()
                    return None
                except Exception as error:  # noqa: BLE001 - ‼ DELIBERATELY BROADER THAN BotModeError.
                    # `PathFindingError` is a `RuntimeError`, NOT a `BotModeError`, so a whiteout
                    # laundered into one would escape this loop entirely, be graded as a genuine
                    # failure, and then the `finally` below would wipe the latch so nothing
                    # downstream could tell what had happened. Catching broadly is safe here
                    # precisely because a non-whiteout error is RETURNED rather than retried.
                    last_error = error
                    if not self._whiteout_pending:
                        # A genuine failure. Do NOT retry — the driver grades it.
                        return error
                    type(self)._recoveries += 1
                    log(f"[{tag}] RECOVERY #{type(self)._recoveries} after attempt {attempt} at "
                        f"frame {context.emulator.get_frame_count()}: "
                        f"{type(error).__name__}: {str(error)[:160]}")
                    if type(self)._recoveries - recoveries_at_entry > max_recoveries:
                        return error

                    # ‼ CLEAR THE LATCH BEFORE NAVIGATING. The recovery walk itself calls
                    # `_check_abort()`, so recovering with the latch still set would abort the
                    # recovery — the same shape as the bug this whole thing is about.
                    set_story_abort(False)
                    try:
                        yield from wait_for_player_avatar_to_be_controllable()
                        # The respawn lands INSIDE a Poké Center; step out so map checks work.
                        # (`exit_building_after_whiteout` is a documented no-op when we are not.)
                        yield from exit_building_after_whiteout()
                        settle = 0
                        while settle < 600 and not (
                            game_has_started() and get_game_state() is GameState.OVERWORLD
                        ):
                            settle += 1
                            yield
                        yield from wait_for_player_avatar_to_be_controllable()
                    except BotModeError:
                        raise
                    except Exception:  # noqa: BLE001 - mirrors StoryMode: a transient hiccup in the
                        yield          # recovery walk must not end the run
            # ‼ FALLING OUT OF THE LOOP MUST NOT READ AS SUCCESS. Returning `None` here would be a
            # silent green — the worst outcome in this file, and the exact "default outcome is the
            # SUCCESS value" pattern in `08-MISTAKES.md`. Unreachable today (the budget check fires
            # first), which is why it is worth being explicit about.
            return last_error
        finally:
            # ‼ NEVER LEAVE THE PROCESS-GLOBAL LATCH SET. See the class docstring.
            set_story_abort(False)


class SpaceCenter1Mode(BotMode):
    """§Ch19 LEGS 1-3 - reach Steven's floor of the Mossdeep Space Center, and capture the anchor.

        PYTHONUTF8=1 py -3.12 story_harness.py post_mossdeep_gym.ss1 --driver spacecenter1 \
            --frames 900000 --profile ch19a

    ANCHOR IN: `saves/post_mossdeep_gym.ss1`, captured by `--driver mossdeepbadge` on a PASS. It
    stands in MOSSDEEP_CITY (38,10) with 7 badges and - ‼ deliberately recorded - a party at 66%
    HP with one Pokemon fainted, which is why leg 1 heals before it walks anywhere.
    ANCHOR OUT: `saves/at_steven_2f.ss1`, so the party-selection menu (leg 5, the one genuinely
    unknown thing in this chapter) can be instrumented over and over without replaying the walk.

    ‼ WHY THE CHAPTER IS SPLIT HERE RATHER THAN DRIVEN WHOLE. Legs 1-3 are ordinary story work -
    walk, ride a forced cutscene, fight grunts - and they are the LONG part. Leg 5 opens
    `ChooseHalfPartyForBattle`, which nothing in this codebase has driven, and figuring that out
    needs many short attempts from a fixed state, not one long one. Driving the whole chapter to
    reach the unknown would pay the entire travel cost per experiment.

    ‼ THE ACCEPTANCE INCLUDES "AND THE BOT CAN CONTINUE", not merely a var value. §Ch15 and §Ch18
    each passed a binary test while leaving the run permanently stranded (KI-56, then §Ch18's
    eleven-tile island the same session). So this asserts a REAL `calculate_path` from where we
    stand to Steven's approach tile: if the three grunts left the floor in a state where Steven
    cannot be reached, that is a FAIL here rather than a mystery in leg 4.

    Emits: [ch19a] RESULT state_var=<n> map=<enum> at=<tile> controllable=<bool> whiteouts=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "SpaceCenter1"

    def on_battle_started(self, encounter):
        # ‼ MIRRORS StoryMode's own choice, because a driver that fights differently from the
        # production mode is measuring a bot the user does not run.
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        SpaceCenter1Mode._whiteouts += 1
        log(f"[ch19a] WHITEOUT #{SpaceCenter1Mode._whiteouts} - recovering, as StoryMode does")
        return True

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.memory import get_event_var
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party
        from modules.story.early_game import wait_until_truly_controllable
        from modules.story.space_center import (
            STATE_VAR,
            STEVEN_APPROACHES_2F,
            clear_the_three_grunts,
            cross_first_floor,
            walk_into_the_space_center,
        )

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001 - report the raw tuple rather than crash
                return f"?{mgn}({type(error).__name__})"

        mgn, tile = here()
        try:
            party = " ".join(f"{m.species.name}:L{m.level}:{m.current_hp}/{m.total_hp}"
                             for m in get_party() if m is not None)
        except Exception as error:  # noqa: BLE001 - an unreadable party is reported, not hidden
            party = f"<unreadable: {type(error).__name__}>"
        log(f"[ch19a] START {map_name(mgn)}{tile} {STATE_VAR}={get_event_var(STATE_VAR)}")
        log(f"[ch19a] PARTY {party}")

        error_text = ""
        try:
            yield from walk_into_the_space_center()
            yield from cross_first_floor()
            yield from clear_the_three_grunts()
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[ch19a] FAILED: {error_text}")

        mgn, tile = here()
        try:
            ctrl = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001
            ctrl = f"<unreadable: {type(error).__name__}>"
        state = get_event_var(STATE_VAR)
        on_2f = mgn == MapRSE.MOSSDEEP_CITY_SPACE_CENTER_2F.value

        # ‼ "CAN THE BOT CONTINUE" - asked with a real path calculation, not asserted in prose.
        # Steven stands on a collision tile, so the reachable target is an APPROACH tile beside
        # him; either one will do, and needing neither would mean leg 4 could never start.
        # ‼ `calculate_path` takes MapLocation OBJECTS from `get_map_data(map, tile)`, not raw
        # tuples, and lives in `modules.map_path`. Both were wrong in the first draft of this
        # driver; a tuple would have raised inside the guard below and reported the grade as
        # "uncomputable" rather than as a real reachability answer.
        # ‼ KI-60: `calculate_path` never validates its SOURCE, so this is evidence about the
        # DESTINATION only - which is why `tile` is the avatar's measured position, not an assumed one.
        reach = "not-attempted"
        if on_2f:
            try:
                from modules.map import get_map_data
                from modules.map_path import calculate_path

                here_loc = get_map_data(MapRSE.MOSSDEEP_CITY_SPACE_CENTER_2F, tile)
                reasons = []
                for approach, _facing in STEVEN_APPROACHES_2F:
                    try:
                        path = calculate_path(
                            here_loc,
                            get_map_data(MapRSE.MOSSDEEP_CITY_SPACE_CENTER_2F, approach),
                        )
                        reasons.append(f"{approach}:OK({len(path)}wp)")
                    except Exception as error:  # noqa: BLE001 - a failure here is the finding
                        reasons.append(f"{approach}:{type(error).__name__}")
                reach = " ".join(reasons)
            except Exception as error:  # noqa: BLE001 - never let the probe crash the grade
                reach = f"<uncomputable: {type(error).__name__}: {str(error)[:120]}>"
        can_continue = ":OK(" in reach

        ok = on_2f and state >= 2 and ctrl is True and can_continue
        log(f"[ch19a] RESULT {STATE_VAR}={state} map={map_name(mgn)} at={tile} "
            f"controllable={ctrl} whiteouts={SpaceCenter1Mode._whiteouts} "
            f"frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        log(f"[ch19a] REACH-STEVEN {reach}")
        log(f"[ch19a] ACCEPTANCE: {'PASS' if ok else 'FAIL'} (needs on 2F AND {STATE_VAR}>=2 AND "
            f"controllable AND a real path to Steven; on_2f={on_2f} can_continue={can_continue})")

        if ok and os.environ.get("CH19A_CAPTURE", "1") != "0":
            out = SAVES / "at_steven_2f.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[ch19a] captured anchor -> {out}")

        context.set_manual_mode()
        return


class SpaceCenter2Mode(StoryWhiteoutRecoveryMixin, BotMode):
    """§Ch19 LEG 5 - Steven's two talks, the PARTY-SELECTION MENU, and the multi battle.

        PYTHONUTF8=1 py -3.12 story_harness.py at_steven_2f.ss1 --driver spacecenter2 \
            --frames 600000 --profile ch19b

    ANCHOR: `saves/at_steven_2f.ss1`, captured by `--driver spacecenter1` on a PASS. It stands on
    SPACE_CENTER_2F (13,2) with `MOSSDEEP_SPACE_CENTER_STATE = 2` - the three grunts already beaten.

    ‼ THIS IS THE ONE GENUINELY UNKNOWN THING IN THE CHAPTER. `ChooseHalfPartyForBattle` has never
    been driven by this codebase. The decomp says the menu is entered with A (submenu) then A
    (ENTER) per Pokemon, that THE CURSOR DOES NOT ADVANCE between picks, and that CONFIRM is cursor
    slot 6 - so a blind A-mash toggles one slot on and off for ever (`ACTIONS_NO_ENTRY` deselects)
    with a healthy screen and no error. Two independent agents read that from cited source. This
    driver is what turns it from a claim into a measurement, so it logs the SELECTION ITSELF
    (`gSelectedOrderFromParty`) rather than only the outcome.

    ‼ WHY A DRIVER AND NOT A PROBE. A hand-driven generator has no battle listeners and cannot win
    a fight (`modules/battle_fault.py:5`); this beat ends in a six-Pokemon multi battle. Probes are
    for logic and guards; anything that must survive a battle needs a real driver.

    WHAT IS MOST LIKELY TO FAIL, SAID IN ADVANCE (so a pass means something):
      1. the party menu never opens (the second Steven talk mis-answered), or
      2. it opens and the cursor/ENTER sequence does not register a pick, or
      3. picks register but CONFIRM is never reached and the menu sits open, or
      4. the battle is LOST - which is a legitimate outcome here, not a crash: the script calls
         `SetCB2WhiteOut` itself, halves the money and warps to the last heal location, leaving
         the var at 2 so the beat can be retried.

    Emits: [ch19b] SELECTED <gSelectedOrderFromParty> / RESULT state_var=<n> ... / ACCEPTANCE
    """

    _whiteouts = 0
    tag = "ch19b"

    @staticmethod
    def name():
        return "SpaceCenter2"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var, read_symbol
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party
        from modules.story.early_game import wait_until_truly_controllable
        from modules.story.space_center import (
            DONE_STATE,
            STATE_VAR,
            STEVEN_FLAG,
            battle_party_slots,
            fight_alongside_steven,
        )

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001
                return f"?{mgn}({type(error).__name__})"

        mgn, tile = here()
        try:
            party = " ".join(f"{m.species.name}:L{m.level}:{m.current_hp}/{m.total_hp}"
                             for m in get_party() if m is not None)
        except Exception as error:  # noqa: BLE001
            party = f"<unreadable: {type(error).__name__}>"
        log(f"[ch19b] START {map_name(mgn)}{tile} {STATE_VAR}={get_event_var(STATE_VAR)} "
            f"{STEVEN_FLAG}={get_event_flag(STEVEN_FLAG)}")
        log(f"[ch19b] PARTY {party}")
        # ‼ SAY WHAT WE INTEND TO PICK *BEFORE* THE RUN, so the log can be graded against an
        # intention rather than rationalised afterwards. The whole party is eligible only when
        # healed - the anchor arrives with Zigzagoon fainted, which the game itself refuses.
        try:
            log(f"[ch19b] INTENDED-PICKS slots={battle_party_slots()} (strongest first, max 3)")
        except Exception as error:  # noqa: BLE001
            log(f"[ch19b] INTENDED-PICKS <unreadable: {type(error).__name__}>")

        # ‼ DRIVEN THROUGH THE RECOVERY MIXIN, so this driver behaves like production on a loss.
        # Before KI-67 it called the chapter ONCE inside a bare `except`, with the abort latch never
        # set — i.e. it exercised the retry loops in a configuration production never runs.
        error_text = ""
        try:
            outcome = yield from self.drive_with_recovery(fight_alongside_steven, max_recoveries=2)
            if outcome is not None:
                error_text = f"{type(outcome).__name__}: {str(outcome)[:900]}"
                log(f"[ch19b] FAILED: {error_text}")
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[ch19b] FAILED: {error_text}")

        try:
            selected = list(read_symbol("gSelectedOrderFromParty")[:4])
        except Exception as error:  # noqa: BLE001
            selected = f"<unreadable: {type(error).__name__}>"
        log(f"[ch19b] SELECTED gSelectedOrderFromParty={selected} (stored as slot+1; 0 = empty)")

        mgn, tile = here()
        try:
            ctrl = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001
            ctrl = f"<unreadable: {type(error).__name__}>"
        state = get_event_var(STATE_VAR)
        ok = state >= DONE_STATE and ctrl is True
        log(f"[ch19b] RESULT {STATE_VAR}={state} map={map_name(mgn)} at={tile} "
            f"controllable={ctrl} whiteouts={SpaceCenter2Mode._whiteouts} "
            f"recoveries={SpaceCenter2Mode._recoveries} "
            f"frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        log(f"[ch19b] ACCEPTANCE: {'PASS' if ok else 'FAIL'} (needs {STATE_VAR}>={DONE_STATE} "
            f"AND controllable)")

        # ‼‼ NEVER CAPTURE AN ANCHOR FROM AN INJECTED RUN. `--inject-weak` replaces the party with a
        # lone Lv3 Poochyena; if such a run ever reached the completion var it would overwrite
        # `post_space_center.ss1` — a committed fixture that `--driver spacecenter` and
        # `FIXTURES.md5` depend on — with a save whose party is a joke. The failure would be
        # SILENT and would poison every downstream test. Injection is a property of the run, so the
        # guard belongs here rather than in a remembered flag on the command line.
        if ok and args.inject_weak:
            log("[ch19b] anchor capture SKIPPED - this run injected a party, so its save is not a "
                "valid fixture. (Guard added 2026-08-12; the risk was real, not theoretical.)")
        if ok and not args.inject_weak and os.environ.get("CH19B_CAPTURE", "1") != "0":
            out = SAVES / "post_space_center.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[ch19b] captured anchor -> {out}")

        context.set_manual_mode()
        return


class Ki66FaintMode(SpaceCenter2Mode):
    """KI-66 INSTRUMENT - the REAL Steven multi battle, with one of OUR OWN picks entered at 1 HP
    so it FAINTS and the after-faint replacement chooser ACTUALLY RUNS.

        PYTHONUTF8=1 py -3.12 story_harness.py at_steven_2f.ss1 --driver ki66faint \
            --frames 600000 --profile ki66

    ‼ WHY THIS EXISTS. KI-66's four unguarded full-party scans (`battle_handler.py:541-545`,
    `:588-598`, `:630-636`, `_util.py:522-587`) execute ONLY when one of the player's Pokemon
    faints inside a partner double battle. KI-66's own entry says *"none has ever run live (every
    §Ch19 drive had zero faints)"*, so the obvious before/after A/B on this item is VACUOUS: both
    arms are identical because the code under test never executes, which reads as "the fix is
    unnecessary" - a refutation of a true finding. This driver is what makes the code RUN.

    ‼ IT SUBCLASSES `SpaceCenter2Mode` (the `boxcounter2` inherit-and-re-prove pattern), so every
    run re-proves the whole party-selection + multi-battle beat before it proves anything new.

    HOW THE FAINT IS PRODUCED - FAITHFULLY, NOT BY POKING A BATTLE.
      MEASURED 2026-08-16: none of the 16 `POKEBOT_*` hooks can faint a mon or set HP, and
      `debug_write_party` writes `gPlayerParty` (out of battle), never `gBattleMons`. ⛔ So do NOT
      add a `gBattleMons` HP writer. Instead we set ONE of our own picks to 1 HP *before the battle
      starts* and let it faint in real combat. Nothing is written mid-battle.
      ‼ 1 HP, NOT 0. `GetBattleEntryEligibility` rejects a 0-HP mon and `battle_party_slots`
      (`space_center.py:503`) only offers eligible ones, so a fainted mon would never be SELECTED
      and therefore could never faint on the field.
      ‼ EXACTLY TWO BYTES CHANGE. `current_hp` is `data[86:88]` (`pokemon.py:1259-1263`), in the
      UNENCRYPTED party-stats region, so the mon stays byte-identical otherwise - including its
      ORIGINAL TRAINER ID, which is the field `ally_party_indices` keys on. Rebuilding the mon via
      `debug_create_pokemon` would have been the obvious route and is WORSE here: it would rewrite
      the very field the code under test reads.

    THE DISCRIMINATOR, AND WHY IT IS NOT THE HEADLINE.
      ⛔ KI-66's headline - "it may send out an ALLY's mon" - needs all three of OUR picks down,
      which is EXACTLY `Cmd_checkteamslost`'s LOSS condition for `TRAINER_STEVEN_PARTNER` (it sums
      HP over `gPlayerParty[0..2]`, our picks only). A repro aimed at the headline would WHITEOUT
      instead of demonstrating it. So we faint ONE mon, leave the other two healthy, and grade on
      what `:630-636` does while the battle CONTINUES:
        ⇒ does `alive_slots` contain any index belonging to STEVEN?
      That set is read from production's OWN telemetry (`[FAINT-CHOOSER]`, `battle_handler.py:651`)
      rather than from anything this driver re-derives, and the ally indices come from the real
      `ally_party_indices()` choke point.

    ‼ WHAT A PASS MEANS. PASS = THE INSTRUMENT WORKS (fixture staged, picks stable, and the faint
    chooser genuinely RAN). The BUG FINDING is reported separately as `KI66-FINDING`. A run that
    passes with `chooser_events=0` is impossible by construction - that is graded as FAIL, because
    a chooser that never ran cannot support any claim about it.

    ⛔⛔ SAFETY - THIS RUN INJECTS, SO IT MUST NEVER CAPTURE AN ANCHOR. `SpaceCenter2Mode` writes
    `saves/post_space_center.ss1` on a PASS. That file is NOT pinned in `preflight.py` or
    `FIXTURES.md5`, so an overwrite would be SILENT and permanent. We disable capture via
    `CH19B_CAPTURE=0` AND verify the file's sha256 is unchanged at the end - the guard is PROVEN,
    not asserted.
    """

    tag = "ki66"

    @staticmethod
    def name():
        return "Ki66Faint"

    def run(self):
        import hashlib
        import os
        import re

        from modules.memory import read_symbol, write_symbol
        from modules.pokemon_party import get_party
        from modules.story.early_game import wait_until_truly_controllable
        from modules.story.space_center import battle_party_slots

        # ---- SAFETY 1: an injected run may never overwrite a committed fixture ----------
        os.environ["CH19B_CAPTURE"] = "0"
        anchor = SAVES / "post_space_center.ss1"
        anchor_before = hashlib.sha256(anchor.read_bytes()).hexdigest() if anchor.is_file() else None
        log(f"[ki66] SAFETY anchor=post_space_center.ss1 sha256[:12]="
            f"{(anchor_before or '<absent>')[:12]} — capture DISABLED (CH19B_CAPTURE=0) because "
            f"this run INJECTS; re-hashed at the end so the guard is proven, not claimed.")

        # ---- capture PRODUCTION's own faint-chooser telemetry ---------------------------
        from modules import debug_logger

        _orig_event = debug_logger.event
        chooser: list[tuple[str, object]] = []
        spaces: list[dict] = []

        def _recording_event(message, *, category="STORY"):
            text = str(message)
            # ‼ COUNT FAINTS, NOT EVENTS. Production emits TWO `[FAINT-CHOOSER]` events per faint
            # (`battle_handler.py:651` the alive_slots line and `:687` the index-spaces line). The
            # first cut of this driver counted both and reported "ALLY slots on 4 occasion(s)" for
            # what were TWO faints — a 2x overcount, caught by an adversarial review of the run.
            # Only the `alive_slots=` line starts a new faint record.
            # ‼ LOG BOTH EVENT TYPES, COUNT ONLY ONE. The `index spaces:` line carries the
            # `[orders DIVERGE]` / `[orders agree]` diagnostic, which is how a FOURTH index-space
            # problem would show itself. An earlier cut of this filter suppressed the LINE as well
            # as the COUNT, and the diagnostic silently vanished from the post-fix transcript.
            if "[FAINT-CHOOSER]" in text and "index spaces:" in text:
                log(f"[ki66] FAINT-CHOOSER (index spaces) :: {text}")
                # Capture the MENU-order candidate set + whether the orders diverge. The
                # fourth-index-space question is only DECIDABLE on a faint that diverges;
                # `[orders agree]` is pre-registered as INCONCLUSIVE, never support for H0.
                try:
                    import re as _re

                    _m = _re.search(r"->\s*\[([^\]]*)\]\(menu-order\)", text)
                    _menu = [int(x) for x in _m.group(1).split(",") if x.strip()] if _m else []
                    spaces.append({
                        "frame": context.emulator.get_frame_count(),
                        "menu_order": _menu,
                        "diverge": "[orders DIVERGE]" in text,
                        "press_index": len(a_presses),
                    })
                except Exception as _err:  # noqa: BLE001
                    # ‼ NAME THE NAME. The first cut logged only the exception CLASS, and
                    # "NameError" alone cost a run to diagnose — the same "a bare type is not a
                    # diagnosis" lesson KI-65 taught, reproduced inside the probe built to study it.
                    log(f"[ki66] index-space capture failed: {type(_err).__name__}: {_err}")
            if "[FAINT-CHOOSER]" in text and "index spaces:" not in text:
                try:
                    from modules.battle_state import get_battle_state
                    from modules.battle_strategies.default import ally_party_indices

                    allies = sorted(ally_party_indices(get_battle_state()))
                except Exception as error:  # noqa: BLE001 - instrumentation must never break a run
                    allies = f"<unreadable: {type(error).__name__}>"
                chooser.append((text, allies))
                log(f"[ki66] FAINT-CHOOSER #{len(chooser)} ally_party_indices={allies} :: {text}")
                # ‼ OBSERVE-ONLY PROBE (changes nothing). `_on_field` is built from
                # `battler.party_index` and compared RAW against a `get_party()` that
                # `UpdatePartyToBattleOrder` has already permuted. Before changing that
                # comparison we must know WHICH DIRECTION the mapping goes — guessing would
                # affect every battle, not just multi battles. Log raw AND mapped and let the
                # run say which one matches the mon that actually fainted.
                try:
                    from modules.battle_state import get_battle_state as _gbs

                    _bs = _gbs()
                    _raw, _mapped = [], []
                    for _side in (_bs.own_side.left_battler, _bs.own_side.right_battler):
                        if _side is not None and getattr(_side, "party_index", None) is not None:
                            _raw.append(_side.party_index)
                    for _r in _raw:
                        try:
                            _mapped.append(_bs.map_battle_party_index(_r))
                        except Exception:  # noqa: BLE001
                            _mapped.append(None)
                    log(f"[ki66] ONFIELD-PROBE raw={_raw} mapped={_mapped} "
                        f"(production currently uses RAW)")
                except Exception as _err:  # noqa: BLE001
                    log(f"[ki66] ONFIELD-PROBE unreadable: {type(_err).__name__}")
            return _orig_event(text, category=category)

        debug_logger.event = _recording_event

        # ‼ THE DATUM THE FIRST RUN LACKED: which slot the chooser ACTUALLY asked for.
        # `new_lead_index` is a local in `handle_fainted_pokemon`, so it appears in no log — and
        # without it the A/B has no discriminator, because `alive_slots` containing ally indices
        # is NOT the same as the bot ATTEMPTING one (measured: on faint #1 three ally slots sat in
        # `alive_slots` and cost 59 frames — free). `:600` calls `scroll_to_party_menu_index` by
        # BARE NAME, so rebinding the module global captures the request with NO production edit.
        import modules.battle_handler as _bh

        _orig_scroll = _bh.scroll_to_party_menu_index
        scrolls: list[tuple] = []

        def _recording_scroll(index, *a, **kw):
            try:
                from modules.battle_state import get_battle_state
                from modules.battle_strategies.default import ally_party_indices

                allies = sorted(ally_party_indices(get_battle_state()))
            except Exception:  # noqa: BLE001
                allies = []
            is_ally = index in allies
            scrolls.append((context.emulator.get_frame_count(), index, tuple(allies), is_ally))
            log(f"[ki66] CHOSEN new_lead_index={index} allies={allies} "
                f"IS_ALLY={is_ally}{'  ‼ the ROM refuses slots 1/4/5 in a multi battle' if is_ally else ''}")
            yield from _orig_scroll(index, *a, **kw)

        _bh.scroll_to_party_menu_index = _recording_scroll

        # ---- #24-faintchooser-fourthspace: the OBSERVE-ONLY PROBE ----------------------
        # ‼ ZERO PRODUCTION CHANGE. Everything below is captured by rebinding module globals
        # that `battle_handler` looks up at CALL time. It does not alter a single decision:
        # every wrapper records and then delegates. The observer control (identical milestone
        # frames vs the previous run) is what proves that, and it is asserted at the end.
        #
        # THE QUESTION: `alive_slots_menu` is `alive_slots` mapped through
        # `map_battle_party_index`. But `party_in_menu = get_party()` is read while the menu is
        # OPEN, i.e. already permuted by `UpdatePartyToBattleOrder` — so that may be a SECOND
        # conversion of an already-converted value (the same shape as KI-18/KI-34/KI-66).
        #   H0 mapping correct   => the game ACCEPTS a cursor that IS in `alive_slots_menu`,
        #                           with ZERO refusals first.
        #   H1 fourth index space=> it accepts one that is NOT in it, after >=1 REFUSAL.
        # The ROM votes: production already learns refusals structurally (`:747-750`).
        _probe_err = {"press": False, "cursor": False}
        menu_presses = {"n": 0}
        cursor_reads: list[tuple] = []      # (frame, cursor)
        a_presses: list[tuple] = []         # (frame, cursor, kind)  kind = select | dismiss
        _orig_press = context.emulator.press_button

        def _printer_armed() -> bool:
            try:
                from modules.tasks import task_is_active

                return bool(
                    task_is_active("Task_PrintAndWaitForText")
                    or task_is_active("Task_ReturnToChooseMonAfterText")
                )
            except Exception:  # noqa: BLE001
                return False

        def _counting_press(button):
            try:
                from modules.memory import GameState, get_game_state

                if get_game_state() == GameState.PARTY_MENU:
                    menu_presses["n"] += 1
                    if button == "A":
                        # ‼ MIRROR PRODUCTION'S OWN DISTINCTION (`:768-770`): an A pressed while
                        # the printer is armed DISMISSES "X has no energy left", it does not
                        # select. Counting those as attempts would inflate the refusal count and
                        # fake H1.
                        kind = "dismiss" if _printer_armed() else "select"
                        cur = cursor_reads[-1][1] if cursor_reads else None
                        a_presses.append((context.emulator.get_frame_count(), cur, kind))
            except Exception as _err:  # noqa: BLE001
                # ‼ ONE-SHOT LOUD. The first cut swallowed this, and an UNBOUND NAME inside the
                # handler made `A-presses=0` — a COMFORTING ZERO that looked like a finding.
                if not _probe_err["press"]:
                    _probe_err["press"] = True
                    log(f"[ki66] ‼ PROBE press-hook FAILED: {type(_err).__name__}: {_err}")
            return _orig_press(button)

        context.emulator.press_button = _counting_press

        # `battle_handler` imports this at module scope (`:22`) and calls it at `:741`, so
        # rebinding ITS global observes only the faint chooser's reads — not menuing.py's.
        _orig_cursor = _bh.get_party_menu_cursor_pos

        def _recording_cursor(*a, **kw):
            result = _orig_cursor(*a, **kw)
            try:
                cursor_reads.append((context.emulator.get_frame_count(), result["slot_id"]))
            except Exception as _err:  # noqa: BLE001
                if not _probe_err["cursor"]:
                    _probe_err["cursor"] = True
                    log(f"[ki66] ‼ PROBE cursor-hook FAILED: {type(_err).__name__}: {_err}")
            return result

        _bh.get_party_menu_cursor_pos = _recording_cursor

        yield from wait_until_truly_controllable()

        # ---- stage the fixture: our LEAD pick enters at 1 HP ----------------------------
        picks_before = []
        target = None
        staged_hp = None
        try:
            picks_before = battle_party_slots()
            target = picks_before[0] if picks_before else None
        except Exception as error:  # noqa: BLE001
            log(f"[ki66] STAGE could not read battle_party_slots: {type(error).__name__}: {error}")

        if target is not None:
            before = get_party()[target]
            raw = bytearray(read_symbol("gPlayerParty"))
            off = target * 100
            raw[off + 86 : off + 88] = (1).to_bytes(2, "little")
            write_symbol("gPlayerParty", bytes(raw))
            # ‼ INVALIDATE THE CACHE BEFORE READING BACK. `get_party()` is served from
            # `state_cache`, so the first version of this control read the PRE-WRITE value (133)
            # and reported `fixture_ok=False` while `[ch19b] PARTY` printed `1/133` three lines
            # later. The subject was correct and the CHECK was wrong — the exact failure this
            # project has logged repeatedly. Reset, then read through the production reader.
            from modules.state_cache import state_cache

            state_cache.reset()
            after = get_party()[target]
            staged_hp = after.current_hp if after is not None else None
            log(f"[ki66] STAGE slot {target} {before.species.name}:L{before.level} "
                f"HP {before.current_hp}/{before.total_hp} -> {staged_hp}/{after.total_hp} "
                f"(2 bytes at data[86:88]; everything else byte-identical)")

        # CONTROL: read the fixture BACK through the production reader, and confirm the staged
        # mon is STILL the lead pick — if the 1 HP demoted it, it never enters and never faints.
        picks_after = []
        try:
            picks_after = battle_party_slots()
        except Exception as error:  # noqa: BLE001
            log(f"[ki66] CONTROL picks unreadable: {type(error).__name__}")
        fixture_ok = staged_hp == 1 and bool(picks_after) and picks_after[0] == target
        log(f"[ki66] CONTROL picks {picks_before} -> {picks_after}  staged_hp={staged_hp}  "
            f"fixture_ok={fixture_ok}"
            + ("" if fixture_ok else "  ‼ the staged mon is NOT the lead pick — it cannot faint"))

        # ---- drive the REAL beat (re-proves party selection + the multi battle) ---------
        # ‼ THE REPORT MUST SURVIVE THE GENERATOR BEING CLOSED. `SpaceCenter2Mode.run()` ends with
        # `context.set_manual_mode()`, after which the harness clears the controller stack and
        # DESTROYS this generator — so code placed after the `yield from` is a RACE. It printed on
        # one run and vanished on the next, which looked like an empty result rather than a lost
        # one. A `finally` runs on GeneratorExit too, so the measurement is never silently lost.
        def _emit_report():

            # ---- report --------------------------------------------------------------------
            ally_hits: list[str] = []
            for text, allies in chooser:
                match = re.search(r"alive_slots=\[([^\]]*)\]", text)
                slots = (
                    [int(part) for part in match.group(1).split(",") if part.strip()]
                    if match
                    else []
                )
                if isinstance(allies, list):
                    overlap = sorted(set(slots) & set(allies))
                    if overlap:
                        ally_hits.append(f"alive_slots={slots} allies={allies} OVERLAP={overlap}")

            anchor_after = hashlib.sha256(anchor.read_bytes()).hexdigest() if anchor.is_file() else None
            anchor_intact = anchor_after == anchor_before

            log("")
            log(f"[ki66] faints={len(chooser)}  (LIVENESS: 0 means the faint chooser never ran and this "
                f"run proves NOTHING about KI-66)")
            log(f"[ki66] party-menu presses={menu_presses['n']}  scroll requests={len(scrolls)}")
            for frame, index, allies, is_ally in scrolls:
                log(f"[ki66]   f{frame} asked for slot {index} (allies={list(allies)}) "
                    f"{'‼ ALLY — the ROM refuses it' if is_ally else 'own mon'}")
            ally_asks = [s for s in scrolls if s[3]]
            if ally_asks:
                log(f"[ki66] ‼‼ KI66-ATTEMPT: the chooser ASKED FOR an ally slot {len(ally_asks)} time(s) "
                    f"— that is an attempt the ROM refuses unconditionally, not merely a candidate list.")
            elif scrolls:
                log("[ki66] ✅ KI66-ATTEMPT: every slot the chooser ASKED FOR was one of our own. "
                    "⛔ So ally slots sitting in `alive_slots` cost NOTHING on this trajectory — do not "
                    "'fix' the ally filter on the strength of this run.")
            log(f"[ki66] SAFETY anchor intact = {anchor_intact} "
                f"(before={(anchor_before or '<absent>')[:12]} after={(anchor_after or '<absent>')[:12]})")
            if ally_hits:
                log(f"[ki66] KI66-CANDIDATES: ally slots sat in `alive_slots` on {len(ally_hits)} of "
                    f"{len(chooser)} faint(s). ⚠ A CANDIDATE IS NOT AN ATTEMPT — see KI66-ATTEMPT above:")
                for hit in ally_hits:
                    log(f"[ki66]     {hit}")
            elif chooser:
                log("[ki66] ✅ KI66-FINDING: NO ally slot appeared in `alive_slots` on any faint. "
                    "⛔ On THIS fixture the hazard did not materialise — do NOT 'fix' it on the "
                    "strength of this run; the A/B would be vacuous. RE-DERIVE the discriminator.")
            else:
                log("[ki66] ⛔ KI66-FINDING: NOT MEASURED — the chooser never ran.")

            # ---- #24-faintchooser-fourthspace ADJUDICATION -------------------------------
            selects = [(f, c) for f, c, k in a_presses if k == "select"]
            dismisses = sum(1 for _f, _c, k in a_presses if k == "dismiss")
            log("")
            log(f"[ki66] PROBE cursor_reads={len(cursor_reads)} A-presses={len(a_presses)} "
                f"(select={len(selects)} dismiss={dismisses})")
            for sp in spaces:
                after = [c for f, c in selects if f >= sp["frame"]]
                accepted = after[-1] if after else None
                attempted = []
                for c in after:
                    if c not in attempted:
                        attempted.append(c)
                refusals = max(0, len(attempted) - 1)
                in_set = (accepted in sp["menu_order"]) if accepted is not None else None
                log(f"[ki66] PROBE f{sp['frame']} menu_order={sp['menu_order']} "
                    f"diverge={sp['diverge']} attempted={attempted} accepted={accepted} "
                    f"refusals={refusals} accepted_in_menu_order={in_set}")
                if not sp["diverge"]:
                    log("[ki66]   → INCONCLUSIVE for the fourth-index-space question "
                        "([orders agree]; pre-registered as NOT support for H0).")
                elif accepted is None:
                    log("[ki66]   → INCONCLUSIVE - no selection A-press recorded after this faint.")
                elif in_set:
                    log("[ki66]   → **H0 on the ACCEPTANCE clause**: the last cursor the SWEEP read "
                        "before the menu closed IS in `alive_slots_menu`. No fourth index space is "
                        "demonstrated on this faint.")
                else:
                    log("[ki66]   → **H1 on the ACCEPTANCE clause**: the accepted cursor is NOT in "
                        "`alive_slots_menu` - consistent with a FOURTH index space. VERIFY before acting.")
                # ‼ THE REFUSAL CLAUSE IS APPROXIMATE AND MUST NOT BE GRADED ON. Presses are counted
                # via `context.emulator.press_button`, which sees EVERY press made while the party menu
                # is up - including `scroll_to_party_menu_index`'s (menuing.py, NOT wrapped here). This
                # run recorded 129 \"select\" presses against only 5 sweep cursor reads, so most were not
                # sweep attempts at all. Report it, never conclude from it.
                log(f"[ki66]   (refusals={refusals} is APPROXIMATE - press attribution includes "
                    f"scroll_to_party_menu_index; grade only the ACCEPTANCE clause above)")

            ok = bool(fixture_ok and chooser and anchor_intact)
            log(f"[ki66] ACCEPTANCE: {'PASS' if ok else 'FAIL'} (INSTRUMENT health only — needs "
                f"fixture_ok AND chooser_events>=1 AND anchor intact. The BUG verdict is KI66-FINDING "
                f"above, and is deliberately NOT part of this line.)")

        try:
            yield from SpaceCenter2Mode.run(self)
        finally:
            _emit_report()
        return


class SpaceCenterMode(BotMode):
    """§Ch19 END TO END - drive `do_space_center_chapter()` and grade it the way the LADDER does.

        PYTHONUTF8=1 py -3.12 story_harness.py post_space_center.ss1 --driver spacecenter \
            --frames 400000 --profile ch19c          # leg 6 only, + proves resume-safety
        PYTHONUTF8=1 py -3.12 story_harness.py post_mossdeep_gym.ss1 --driver spacecenter \
            --frames 1500000 --profile ch19d         # the WHOLE chapter

    ‼ THE SAME DRIVER FROM TWO ANCHORS IS THE POINT. Every leg is resume-safe, so running it from
    `post_space_center.ss1` must SKIP straight to the Dive gift - which tests the resume guards and
    leg 6 at once - while running it from `post_mossdeep_gym.ss1` plays the whole beat. A chapter
    that only works from its first anchor is not resume-safe, and the ladder re-runs `_play` from
    wherever the player actually is.

    ‼ GRADED ON `RECEIVED_HM_DIVE`, NOT ON THE SPACE CENTER VAR - because that is what
    `chapters.py` grades chapter 19 on, and the two are set in DIFFERENT BUILDINGS. A §Ch19 that
    stopped at `MOSSDEEP_SPACE_CENTER_STATE == 3` would pass its own test while `current_chapter()`
    returned chapter 19 for ever; and on the re-run the 2F Steven has been `removeobject`'d, so
    there would be nobody left to talk to. Green acceptance, wedged ladder.

    ‼ AND IT ASSERTS THE ITEM, NOT ONLY THE FLAG. `EventScript_StevenGivesDive` does `giveitem` and
    then `setflag` with NO check of the result, so a full TM/HM pocket sets the flag while HM08 was
    never received - the chapter would grade green and §Ch20 would fail on "cannot use Dive".

    ‼ AND "THE BOT CAN CONTINUE". The acceptance requires being OUT of any interior and holding a
    real path to the next beat's departure point. §Ch15 and §Ch18 each passed a binary test while
    leaving the run stranded; that rule is the most re-learned one in this project.

    Emits: [ch19c] RESULT dive=<bool> hm08=<bool> map=<enum> at=<tile> controllable=<bool>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "SpaceCenter"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        SpaceCenterMode._whiteouts += 1
        log(f"[ch19c] WHITEOUT #{SpaceCenterMode._whiteouts} - recovering, as StoryMode does")
        return True

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party
        from modules.story.early_game import wait_until_truly_controllable
        from modules.story.space_center import (
            DIVE_FLAG,
            STATE_VAR,
            _has_hm08,
            do_space_center_chapter,
        )

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001
                return f"?{mgn}({type(error).__name__})"

        mgn, tile = here()
        try:
            party = " ".join(f"{m.species.name}:L{m.level}:{m.current_hp}/{m.total_hp}"
                             for m in get_party() if m is not None)
        except Exception as error:  # noqa: BLE001
            party = f"<unreadable: {type(error).__name__}>"
        log(f"[ch19c] START {map_name(mgn)}{tile} {STATE_VAR}={get_event_var(STATE_VAR)} "
            f"{DIVE_FLAG}={get_event_flag(DIVE_FLAG)}")
        log(f"[ch19c] PARTY {party}")

        error_text = ""
        try:
            yield from do_space_center_chapter()
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[ch19c] FAILED: {error_text}")

        mgn, tile = here()
        try:
            ctrl = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001
            ctrl = f"<unreadable: {type(error).__name__}>"
        dive = get_event_flag(DIVE_FLAG)
        hm08 = _has_hm08()

        # ‼ CAN THE BOT CONTINUE? Asked with a real path calculation from where we actually stand.
        # §Ch20 leaves from Mossdeep City, so the honest question is "are we outside, and can we
        # reach the south exit". Steven's house has ONE door; a chapter that ended inside it would
        # look complete and strand the ladder in a living room.
        outside = mgn == MapRSE.MOSSDEEP_CITY.value
        reach = "not-attempted"
        if outside:
            try:
                from modules.map import get_map_data
                from modules.map_path import calculate_path

                path = calculate_path(
                    get_map_data(MapRSE.MOSSDEEP_CITY, tile),
                    get_map_data(MapRSE.MOSSDEEP_CITY, (28, 17)),   # the Pokemon Center door
                )
                reach = f"OK({len(path)}wp to the Pokemon Center)"
            except Exception as error:  # noqa: BLE001 - a failure here IS the finding
                reach = f"{type(error).__name__}: {str(error)[:90]}"
        can_continue = reach.startswith("OK(")

        ok = dive and hm08 and ctrl is True and outside and can_continue
        log(f"[ch19c] RESULT dive={dive} hm08={hm08} {STATE_VAR}={get_event_var(STATE_VAR)} "
            f"map={map_name(mgn)} at={tile} controllable={ctrl} "
            f"whiteouts={SpaceCenterMode._whiteouts} frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        log(f"[ch19c] CAN-CONTINUE {reach}")
        log(f"[ch19c] ACCEPTANCE: {'PASS' if ok else 'FAIL'} (needs {DIVE_FLAG} AND HM08 in the bag "
            f"AND controllable AND outside AND a real path onward; outside={outside} "
            f"can_continue={can_continue})")

        if ok and os.environ.get("CH19C_CAPTURE", "1") != "0":
            out = SAVES / "post_dive.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[ch19c] captured anchor -> {out}")

        context.set_manual_mode()
        return


class AquaHideoutMode(BotMode):
    """§Ch17 - drive `do_aqua_hideout_chapter()` from the post-Ch16 anchor.

        PYTHONUTF8=1 py -3.12 story_harness.py post_harbor.ss1 --driver aquahideout \
            --frames 400000 --profile ch17a

    ANCHOR: `saves/post_harbor.ss1`, captured by `--driver slateporttheft` on a PASS. It stands in
    SLATEPORT_CITY_HARBOR with `SLATEPORT_HARBOR_STATE=2`, both
    `HIDE_AQUA_HIDEOUT_1F_GRUNT_*_BLOCKING_ENTRANCE` set (the way in is open) and — ‼ deliberately
    — a party at **100% HP**, which is why the chapter is not starting the way §Ch16 did.

    ACCEPTANCE IS BOTH HALVES: `FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE` **AND** controllable. The
    flag is set mid-script by `AquaHideout_B2F_EventScript_SubmarineEscape`, so grading on it
    alone would call a `lockall`ed avatar a success — the `EventScript_ActivateStrength` trap.

    ‼ THE THING MOST LIKELY TO FAIL, stated in advance so the result is read correctly: B1F is a
    **warp-panel maze** (21 of its 25 warps return to B1F) and the route was solved STATICALLY,
    blind to the six Aqua grunts standing in its corridors. If a hop lands somewhere unexpected,
    `_aqua_hop` says so with both the expected and the actual tile — that is the designed
    outcome, not a crash.

    Emits: [ch17] RESULT escaped=<bool> controllable=<bool> map=<enum> at=<tile> whiteouts=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "AquaHideout"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        AquaHideoutMode._whiteouts += 1
        log(f"[ch17] WHITEOUT #{AquaHideoutMode._whiteouts} - recovering, as StoryMode does")
        return True

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.memory import _event_flags, get_event_flag
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.story.early_game import do_aqua_hideout_chapter, wait_until_truly_controllable

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        # ‼ every driver in this file defines its own `map_name`; omitting it crashed MagmaExit
        # at frame 30 and the log then looked exactly like a hung bot.
        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001 - report the raw tuple rather than crash
                return f"?{mgn}({type(error).__name__})"

        DONE = "TEAM_AQUA_ESCAPED_IN_SUBMARINE"
        GATES = ("HIDE_AQUA_HIDEOUT_1F_GRUNT_1_BLOCKING_ENTRANCE",
                 "HIDE_AQUA_HIDEOUT_1F_GRUNT_2_BLOCKING_ENTRANCE")

        # ‼ NAME CONTROL FIRST — an unknown flag reads False without raising, so every line
        # below would be a confident lie about the era.
        unknown = [n for n in (DONE,) + GATES if n not in _event_flags]
        if unknown:
            log(f"[ch17] ABORT - unknown flag name(s) {unknown}; they read False SILENTLY.")
            context.set_manual_mode()
            return

        mgn, tile = here()
        log(f"[ch17] START {map_name(mgn)}{tile} {DONE}={get_event_flag(DONE)} "
            f"entrance_open={[get_event_flag(g) for g in GATES]}")
        if not all(get_event_flag(g) for g in GATES):
            log("[ch17] ‼ ERA WARNING - the hideout entrance is still blocked; Ch16 has not run. "
                "The chapter should refuse.")

        error_text = ""
        try:
            yield from do_aqua_hideout_chapter()
            log("[ch17] do_aqua_hideout_chapter returned without raising")
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[ch17] FAILED: {error_text}")

        mgn, tile = here()
        escaped = get_event_flag(DONE)
        try:
            ctrl = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001
            ctrl = f"<unreadable: {type(error).__name__}>"

        # ‼ THE MASTER BALL IS PART OF THE ACCEPTANCE (user directive 2026-08-12), and it is read
        # from THE BAG rather than from `FLAG_ITEM_AQUA_HIDEOUT_B1F_MASTER_BALL`: a full items
        # pocket makes `finditem` set no flag AND give no item, so the flag alone cannot tell
        # "collected" from "could not collect". The Nugget is reported too because it is the
        # stepping stone — if it is missing, the Master Ball was never reachable.
        from modules.story.early_game import _held_quantity

        try:
            master_balls = _held_quantity("Master Ball")
            nuggets = _held_quantity("Nugget")
        except Exception as error:  # noqa: BLE001 — a bag we cannot read is reported as such
            master_balls = nuggets = f"<unreadable: {type(error).__name__}>"

        log(f"[ch17] RESULT escaped={escaped} controllable={ctrl} map={map_name(mgn)} at={tile} "
            f"master_balls={master_balls} nuggets={nuggets} "
            f"whiteouts={AquaHideoutMode._whiteouts} frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        got_ball = isinstance(master_balls, int) and master_balls >= 1
        log(f"[ch17] ACCEPTANCE: {'PASS' if (escaped and ctrl is True and got_ball) else 'FAIL'} "
            f"(needs {DONE} AND controllable==True AND a MASTER BALL in the bag)")

        # Capture the post-Ch17 anchor on a PASS only, as `slateporttheft` does — it is the build
        # anchor for the next beat and expensive to reproduce.
        if escaped and ctrl is True and got_ball and os.environ.get("CH17_CAPTURE", "1") != "0":
            out = SAVES / "post_aqua.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[ch17] captured anchor -> {out}")

        context.set_manual_mode()
        return


class MagmaExitMode(BotMode):
    """KI-56 - drive `leave_magma_hideout()` from the post-Maxie anchor. THE EXIT LEG.

        PYTHONUTF8=1 py -3.12 verify_fixtures.py --assert post_maxie.ss1=19399688e730 && \
        PYTHONUTF8=1 py -3.12 story_harness.py post_maxie.ss1 --driver magmaexit \
            --frames 900000 --profile mhexit

    ‼ WHY THIS DRIVER EXISTS AT ALL. §Ch15's acceptance was BINARY on
    `GROUDON_AWAKENED_MAGMA_HIDEOUT`, a flag the game sets the instant Maxie falls - four floors
    underground. The chapter therefore passed its own test on runs that ended PERMANENTLY
    STRANDED (KI-56). This driver tests the half that was never asked: **can the bot get out.**

    ANCHOR: `saves/post_maxie.ss1` - standing on MAGMA_HIDEOUT_4F (15,21), Maxie beaten. That is
    exactly the state the strand begins from, so this is a free repro of the real failure.

    ACCEPTANCE IS BOTH HALVES: **out of the hideout AND controllable**, landing on JAGGED_PASS.
    Grading on "not in the hideout" alone would call a whiteout a success - a whiteout also
    leaves the dungeon, two towns away, having lost money. The landing map is what separates
    them, which is why it is asserted and not merely logged.

    ‼ NEGATIVE CONTROL, printed before the run: the bag must hold **0 Escape Ropes** at the
    start. Every anchor save reads 0 (`probe_escape_warp.py`), so a run that begins with one
    would be testing a bag that was already stocked rather than the pickup this leg exists for.

    Emits: [mhexit] RESULT out=<bool> map=<enum> at=<tile> controllable=<bool> ropes=<n> frames=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "MagmaExit"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            # The 3F_3R detour crosses grunt sight-lines; use the same strategy the chapter does.
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        MagmaExitMode._whiteouts += 1
        log(f"[mhexit] WHITEOUT #{MagmaExitMode._whiteouts} - recovering, as StoryMode does")
        return True

    def run(self):
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.story.early_game import (
            _escape_ropes_held,
            _inside_magma_hideout,
            HIDEOUT_ESCAPE_ROPE_FLAG,
            leave_magma_hideout,
            wait_until_truly_controllable,
        )

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        # ‼ `map_name` is a LOCAL helper in every driver in this file, not a module-level one.
        # Leaving it out cost a run: this driver crashed at frame 30 with `NameError: name
        # 'map_name' is not defined`, the harness dropped to Manual mode, and the log then filled
        # with 900k frames of heartbeats that looked like a hung bot rather than a typo.
        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001 - report the raw tuple rather than crash
                return f"?{mgn}({type(error).__name__})"

        mgn, tile = here()
        ropes_at_start = _escape_ropes_held()
        ball_taken = get_event_flag(HIDEOUT_ESCAPE_ROPE_FLAG)
        log(f"[mhexit] START {map_name(mgn)}{tile} inside={_inside_magma_hideout()} "
            f"ropes={ropes_at_start} ball_taken={ball_taken}")

        if not _inside_magma_hideout():
            log("[mhexit] ‼ WRONG STATE - this anchor is not inside the hideout, so the exit "
                "leg is a no-op and this run measures nothing.")
            context.set_manual_mode()
            return
        if ropes_at_start != 0:
            log(f"[mhexit] ‼ NEGATIVE CONTROL FAILED - the bag already holds {ropes_at_start} "
                "Escape Rope(s). This run cannot test the pickup.")

        error_text = ""
        try:
            yield from leave_magma_hideout()
            log("[mhexit] leave_magma_hideout returned without raising")
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[mhexit] FAILED: {error_text}")

        mgn, tile = here()
        out = not _inside_magma_hideout()
        landed_right = mgn == MapRSE.JAGGED_PASS.value
        try:
            controllable = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001
            controllable = f"<unreadable: {type(error).__name__}>"
        log(f"[mhexit] RESULT out={out} map={map_name(mgn)} at={tile} "
            f"controllable={controllable} landed_on_jagged_pass={landed_right} "
            f"ropes={_escape_ropes_held()} whiteouts={MagmaExitMode._whiteouts} "
            f"frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        log(f"[mhexit] VERDICT {'PASS' if (out and landed_right and controllable is True) else 'FAIL'}"
            " - acceptance is BOTH halves: outside AND controllable, on JAGGED_PASS.")

        context.set_manual_mode()
        return


class SlateportTheftMode(BotMode):
    """Ch16 - drive `do_slateport_harbor_theft()` from the post-Maxie anchor.

        PYTHONUTF8=1 py -3.12 verify_fixtures.py --assert post_maxie.ss1=19399688e730 &&         PYTHONUTF8=1 py -3.12 story_harness.py post_maxie.ss1 --driver slateporttheft             --frames 2500000 --profile ch16a

    ACCEPTANCE IS BOTH HALVES: `SLATEPORT_HARBOR_STATE == 2` **AND** the avatar controllable.
    The var is set roughly HALFWAY through the script, so grading on it alone would call a
    `lockall`ed avatar a success - the exact `EventScript_ActivateStrength` trap of 2026-08-10.

    Emits: [ch16] RESULT harbor_state=<n> controllable=<bool> map=<enum> at=<tile> frames=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name() -> str:
        return "Story"

    def on_whiteout(self) -> bool:
        # A harness driver must MIRROR the overrides of the mode it stands in for: StoryMode
        # returns True here (recover) while the default is False (drop to Manual). Two runs
        # stopped at the identical frame before that was noticed (04-HANDOFF).
        SlateportTheftMode._whiteouts += 1
        log(f"[ch16] WHITEOUT #{SlateportTheftMode._whiteouts} - recovering, as StoryMode does")
        return True

    # ‼ NO `-> Generator` ANNOTATION: `Generator` is never imported in this harness, and the
    # annotation is evaluated at class-definition time, so it is an import-time NameError that
    # kills the run before a single frame executes. No other mode here annotates it either.
    def run(self):
        from modules.map import get_map_data_for_current_position
        from modules.map_data import MapRSE
        from modules.memory import _event_vars, get_event_var
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.story.early_game import do_slateport_harbor_theft

        def here():
            a = get_player_avatar()
            return tuple(a.map_group_and_number), tuple(a.local_coordinates)

        def map_name(mgn):
            try:
                return MapRSE(mgn).name
            except Exception as error:  # noqa: BLE001 - report the raw tuple rather than crash
                return f"?{mgn}({type(error).__name__})"

        # ‼ NAME CONTROL FIRST. `get_event_var` returns -1 for an unknown name WITHOUT raising,
        # so a typo would read as "wrong era" for the whole run and be believed.
        if "SLATEPORT_HARBOR_STATE" not in _event_vars:
            log("[ch16] ABORT - 'SLATEPORT_HARBOR_STATE' is not a known var name; every reading "
                "below would be a silent -1. Fix the name before trusting anything.")
            context.set_manual_mode()
            return

        mgn, tile = here()
        start_state = get_event_var("SLATEPORT_HARBOR_STATE")
        log(f"[ch16] START {map_name(mgn)}{tile} SLATEPORT_HARBOR_STATE={start_state}")
        if start_state != 1:
            log(f"[ch16] ‼ ERA WARNING - expected 1, got {start_state}. The coord triggers are "
                f"inert unless this is 1; the chapter should refuse.")

        # ‼ CH15's HANDOVER, PERFORMED EXPLICITLY - NOT part of what this driver measures.
        # `post_maxie.ss1` stands on MAGMA_HIDEOUT_4F, but §Ch16's leg 1 is
        # `_navigate_riding_out(SLATEPORT_CITY, ...)` from wherever it is, and NO walk-out of the
        # hideout exists (KI-56: 18 of 20 warp-graph nodes reachable, the exit is not among
        # them). In production Segment 15 now ends OUTSIDE, so Ch16 never starts underground;
        # from this anchor the driver has to reproduce that hand-over itself, or leg 1 fails for
        # a Ch15 reason and the failure gets read as a Ch16 routing bug - which is exactly what
        # happened on the first §Ch16 run.
        # ‼ Ch16 itself is deliberately NOT taught about the Magma Hideout: leaving a dungeon is
        # the previous chapter's job, and a chapter that cleans up after its predecessor hides
        # the predecessor's bugs.
        from modules.story.early_game import _inside_magma_hideout, leave_magma_hideout

        if _inside_magma_hideout():
            log("[ch16] PRE-STEP: anchor is inside the Magma Hideout - running Ch15's exit "
                "(`leave_magma_hideout`) first. This is SETUP, not part of the Ch16 result.")
            try:
                yield from leave_magma_hideout()
            except Exception as error:  # noqa: BLE001 - a setup failure must be labelled as one
                log(f"[ch16] ABORT - the Ch15 EXIT failed, so Ch16 never started: "
                    f"{type(error).__name__}: {str(error)[:500]}")
                context.set_manual_mode()
                return
            mgn, tile = here()
            log(f"[ch16] PRE-STEP done - now at {map_name(mgn)}{tile}")

        error_text = ""
        try:
            yield from do_slateport_harbor_theft()
            log("[ch16] do_slateport_harbor_theft returned without raising")
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:900]}"
            log(f"[ch16] FAILED: {error_text}")

        mgn, tile = here()
        final = get_event_var("SLATEPORT_HARBOR_STATE")
        try:
            ctrl = player_avatar_is_controllable()
        except Exception as error:  # noqa: BLE001 - an unreadable avatar is reported, not hidden
            ctrl = f"?({type(error).__name__})"
        log(f"[ch16] RESULT harbor_state={final} controllable={ctrl} map={map_name(mgn)} "
            f"at={tile} whiteouts={SlateportTheftMode._whiteouts} "
            f"frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))
        log(f"[ch16] ACCEPTANCE: {'PASS' if (final == 2 and ctrl is True) else 'FAIL'} "
            f"(needs harbor_state==2 AND controllable==True)")

        # ‼ CAPTURE THE POST-CH16 ANCHOR, the same way `magmatravel` captures `magma_door.ss1`.
        # This state is the build anchor for the NEXT chapter (the Lilycove Aqua Hideout, whose
        # two blocking grunts the Aqua-escape scene has just cleared), and it is expensive to
        # reproduce: getting here means leaving the Magma Hideout, crossing the region and
        # riding the Stern scene. Captured ONLY on a pass, so a failed run can never overwrite a
        # good anchor with a broken one.
        # ‼ VOLATILE by construction — a driver re-captures it, so it must never be treated as a
        # pinned fixture (`FIXTURES.md5`'s distinction).
        # ‼ `os` is imported PER METHOD in this file, never at module scope — same trap as the
        # per-driver local `map_name` helper. Omitting it raised `NameError` AFTER the acceptance
        # line had already printed PASS, so the run looked successful and silently captured nothing.
        import os

        if final == 2 and ctrl is True and os.environ.get("CH16_CAPTURE", "1") != "0":
            out = SAVES / "post_harbor.ss1"
            out.write_bytes(context.emulator.get_save_state())
            log(f"[ch16] captured anchor -> {out}")

        context.set_manual_mode()
        return


class MagmaHideoutMode(BotMode):
    """`#24-magmahideout` INCREMENTS 2+3 — go IN and beat Maxie, from the door anchor.

    Runs the production `enter_magma_hideout()` then `do_magma_hideout()`.

        PYTHONUTF8=1 py -3.12 story_harness.py magma_door.ss1 --driver magmahideout --frames 900000

    ‼ ANCHOR: `saves/magma_door.ss1` is captured by `--driver magmatravel` on success — it stands
    on JAGGED_PASS (16,20) with VAR_JAGGED_PASS_STATE already 2, i.e. the entrance OPEN. Running
    this from anything earlier measures the rock wall, not the hideout.

    ACCEPTANCE — BINARY: `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT`. No statistics.

    ‼ THE THING MOST LIKELY TO FAIL, stated in advance so the result is read correctly: the
    static planner reaches only 44 tiles on 1F from the arrival (10,34) and calls all three
    onward warps unreachable. If this run dies on 1F that is the KI-24-class question answered
    the hard way; if it walks straight through, the static reading was the artifact.

    Emits: [magmahideout] RESULT groudon=<bool> map=<enum> at=<tile> floors=<visited> frames=<n>
    """

    _whiteouts = 0

    @staticmethod
    def name():
        return "MagmaHideout"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            # ‼ The hideout is wall-to-wall trainers (Tabitha + the numbered grunts + Maxie), so
            # use the STORY item strategy — the one that actually uses potions in a boss fight
            # (`#24-battleitems`). A weaker strategy here measures the strategy, not the chapter.
            from plugins.custom_modes.story_mode import StoryItemBattleStrategy

            return StoryItemBattleStrategy()
        return DefaultBattleStrategy()

    def on_whiteout(self) -> bool:
        # Same reason as MagmaTravelMode: the default is False, StoryMode overrides it to True.
        MagmaHideoutMode._whiteouts += 1
        log(f"[magmahideout] WHITEOUT #{MagmaHideoutMode._whiteouts} — recovering, as StoryMode does")
        return True

    def run(self):
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var
        from modules.player import get_player_avatar
        from modules.story.early_game import (
            do_magma_hideout,
            enter_magma_hideout,
            wait_until_truly_controllable,
        )

        yield from wait_until_truly_controllable()

        def here():
            avatar = get_player_avatar()
            return tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates)

        def map_name(group_and_number):
            try:
                return MapRSE(group_and_number).name
            except ValueError:
                return str(group_and_number)

        # ‼ ERA/STATE ASSERTION FIRST. `JAGGED_PASS_STATE < 2` means the entrance is still a
        # rock wall and every result below would be about the wall.
        jagged_state = get_event_var("JAGGED_PASS_STATE")
        log(f"[magmahideout] START {map_name(here()[0])} {here()[1]} "
            f"JAGGED_PASS_STATE={jagged_state}")
        if jagged_state < 2:
            log("[magmahideout] ‼ WRONG STATE — the entrance has not been opened; this run "
                "would measure the rock wall. Use an anchor captured by --driver magmatravel.")

        #: Which floors we actually set foot on — the diagnostic that says HOW FAR it got.
        floors: list[str] = []
        last_map = None

        error_text = ""
        try:
            yield from enter_magma_hideout()
            # ‼ Track the floors from inside the generator loop by sampling as it runs: the
            # chapter's own error names the map it stopped on, but a list of what was VISITED
            # is what distinguishes "1F is a dead end" from "died on 3F".
            gen = do_magma_hideout()
            while True:
                try:
                    next(gen)
                except StopIteration:
                    break
                current = here()[0]
                if current != last_map:
                    last_map = current
                    floors.append(map_name(current))
                yield
        except Exception as error:  # noqa: BLE001 - the failure IS the measurement
            error_text = f"{type(error).__name__}: {str(error)[:1200]}"
            log(f"[magmahideout] FAILED: {error_text}")
            # ‼ CAPTURE THE FAILURE SITE. Iterating on the 1F boulder puzzle by re-driving
            # the whole entry every time is minutes per attempt; a save at the point of
            # failure makes the next inspection offline and instant.
            try:
                _fail = SAVES / "magma_1f_fail.ss1"
                _fail.write_bytes(context.emulator.get_save_state())
                log(f"[magmahideout] captured the failure site -> {_fail}")
            except Exception:  # noqa: BLE001
                pass

        groudon = get_event_flag("GROUDON_AWAKENED_MAGMA_HIDEOUT")
        log(f"[magmahideout] RESULT groudon={groudon} map={map_name(here()[0])} at={here()[1]} "
            f"floors={floors} whiteouts={MagmaHideoutMode._whiteouts} "
            f"frames={context.emulator.get_frame_count()}"
            + (f" error=({error_text})" if error_text else ""))

        # ‼ CAPTURE THE POST-MAXIE ANCHOR (added 2026-08-11 for §Ch16). Maxie's defeat sets
        # `VAR_SLATEPORT_HARBOR_STATE = 1`, which is the gate on all four Slateport Harbor coord
        # triggers — so the NEXT beat cannot be developed at all without a save from this era, and
        # no committed save had it. `magmatravel` already captures its own anchor this way; this
        # mirrors it so the chain keeps producing the anchor the next chapter needs instead of
        # making someone re-drive a whole dungeon to get one.
        # ‼ GATED ON `groudon`, NOT on "the driver finished". A save captured after a FAILED run
        # would be the wrong era while looking exactly like the right one — which is the mistake
        # that cost seven probes on 2026-08-10 (`08-MISTAKES`: verify an anchor against the STORY
        # CLOCK, not the map).
        # ‼ ALWAYS SAY WHETHER THIS BLOCK RAN. On 2026-08-11 a run reported `groudon=True` and then
        # emitted NEITHER the success line NOR the failure line, and no anchor appeared — a
        # completely silent path that cost a chapter's worth of driving to notice. A branch whose
        # non-execution is invisible cannot be debugged from a log.
        # ‼ `import os` HERE because this method never had it — `os` was undefined at this line,
        # so the anchor-capture block raised `NameError` **only on the SUCCESS path**, after a full
        # Magma Hideout drive. Found by pyflakes (the gate added 2026-08-12), not by any run: every
        # failing run returned before reaching it, and a passing one would have died at the very
        # moment it had something worth saving. Pre-existing; unrelated to §Ch19.
        import os

        _cap_env = os.environ.get("MAGMA_HIDEOUT_CAPTURE", "1")
        log(f"[magmahideout] anchor capture: groudon={groudon} MAGMA_HIDEOUT_CAPTURE={_cap_env!r}")
        if groudon and _cap_env != "0":
            # ‼ WRITE THE SAVE **FIRST**, DIAGNOSTICS SECOND. The previous order read two event
            # vars before writing, so any error in the *telemetry* would have cost the *capture* —
            # and the capture is the expensive thing (a whole dungeon of driving), while the
            # numbers beside it are a convenience.
            out = SAVES / "post_maxie.ss1"
            try:
                out.write_bytes(context.emulator.get_save_state())
                log(f"[magmahideout] captured anchor -> {out}")
            except Exception as _error:  # noqa: BLE001 - capture must never fail the run
                log(f"[magmahideout] ‼ anchor WRITE failed: {type(_error).__name__}: {_error}")
            try:
                # ‼ NO `VAR_` PREFIX. The reader's table is keyed WITHOUT it
                # (`SLATEPORT_HARBOR_STATE`), and `get_event_var` returns **-1** for an unknown
                # name rather than raising — so the first version of this line read -1 in silence
                # and would have been believed. Verified against `modules.memory._event_vars` with
                # a ROM loaded; `probe_ch16_anchor.py`'s NAME CONTROL is what catches this class.
                _harbor = get_event_var("SLATEPORT_HARBOR_STATE")
                _city = get_event_var("SLATEPORT_CITY_STATE")
                log(f"[magmahideout] anchor era: SLATEPORT_HARBOR_STATE={_harbor} "
                    f"SLATEPORT_CITY_STATE={_city}")
                if _harbor != 1:
                    log(f"[magmahideout] ‼ EXPECTED SLATEPORT_HARBOR_STATE == 1 after Maxie, read "
                        f"{_harbor} (-1 means the NAME is wrong, not that the era is). Run "
                        f"probe_ch16_anchor.py before building the harbor beat on this anchor.")
            except Exception as _error:  # noqa: BLE001
                log(f"[magmahideout] anchor era unreadable: {type(_error).__name__}: {_error}")

        context.set_manual_mode()
        return


class AnchorCaptureMode(BotMode):
    """MAKE a save anchor at a named map/tile, starting from an existing one.

    ‼ WHY. `#24-r116sweep` has now failed twice for want of an anchor, and
    `probe_anchor_inventory.py` proved WHY the second pick was no better than the first:
    **no save in `saves/` stands in MAUVILLE_CITY with badge03 unheld**. The two that look
    like they do are in `MAUVILLE_CITY_GYM` (whose `map_name` label is literally "MAUVILLE
    CITY" — that label is what wrote the bad anchor down in the first place). When the anchor
    a measurement needs does not exist, the measurement is blocked until something MAKES it;
    until now nothing here could, so anchors were only ever scavenged from crash sites.

    It drives `_navigate_riding_out` — the same call the executor uses — so an anchor it
    produces is by construction one the bot could actually have walked to.

        PYTHONUTF8=1 CAPTURE_TARGET=MAUVILLE_CITY:22,6 CAPTURE_NAME=mauville_prewattson.ss1 \
            py -3.12 story_harness.py slateport.ss1 --driver anchorcapture --frames 600000

    ‼ It REFUSES to overwrite an existing anchor unless `CAPTURE_FORCE=1`. An anchor is
    evidence: several results in this project are only interpretable against the exact save
    they ran from, and silently replacing one rewrites the past.

    Emits: [capture] RESULT wrote=<path|None> arrived=<bool> map=<enum> tile=<x,y>
           controllable=<bool> badges=<list> party=<n>
    ‼ Verify the file afterwards with `probe_anchor_inventory.py --filter <name>` — this
    driver reports what it believes; the inventory reports what the file contains.
    """

    @staticmethod
    def name():
        return "AnchorCapture"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

            return LevelUpTravelBattleStrategy()
        return DefaultBattleStrategy()

    def run(self):
        import os
        import pathlib

        from modules.map_data import MapRSE
        from modules.memory import get_event_flag
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

        raw = os.environ.get("CAPTURE_TARGET", "MAUVILLE_CITY:22,6")
        name = os.environ.get("CAPTURE_NAME", "")
        force = os.environ.get("CAPTURE_FORCE", "") == "1"
        map_name, _, tile = raw.partition(":")
        x, _, y = tile.partition(",")
        target, ttile = MapRSE[map_name.strip()], (int(x), int(y))

        out = pathlib.Path(__file__).resolve().parent / "saves" / (name or f"capture_{map_name.lower()}.ss1")
        if out.exists() and not force:
            log(f"[capture] REFUSING to overwrite an existing anchor: {out.name} (set CAPTURE_FORCE=1 to replace)")
            context.set_manual_mode()
            return

        yield from wait_until_truly_controllable()
        start = get_player_avatar()
        log(f"[capture] start map={tuple(start.map_group_and_number)} tile={tuple(start.local_coordinates)} "
            f"-> {target.name}{ttile}")

        # ‼ ATTEMPT THE NAVIGATION MORE THAN ONCE, AND SAY SO PER ATTEMPT. The first run of this
        # driver aborted after 1,327 frames with "the field is idle and we are still at (16, 89)"
        # while `Task_DoDoorWarp` + `Task_AnimateDoor` were on the task list — i.e. the field was
        # NOT idle, it was mid door-warp. `#24-journey` part 3 already fixed exactly this shape
        # for BATTLE transitions; whether it is also a hole for DOOR transitions is a production
        # question, and this loop is the cheap A/B that says whether a second attempt would have
        # arrived. Attempt 1 IS the production behaviour, so the two arms are readable separately.
        attempts = int(os.environ.get("CAPTURE_ATTEMPTS", "3"))
        arrived = False
        for attempt in range(1, attempts + 1):
            try:
                yield from _navigate_riding_out(target, ttile, tries=24)
                arrived = tuple(get_player_avatar().map_group_and_number) == tuple(target.value)
                log(f"[capture] attempt {attempt}: arrived={arrived} at "
                    f"{tuple(get_player_avatar().local_coordinates)}")
            except Exception as error:
                log(f"[capture] attempt {attempt} FAILED: {type(error).__name__}: {str(error)[:600]}")
            if arrived:
                break
            # ride out whatever transition was running, then let the field settle before retrying
            for _ in range(180):
                context.emulator.press_button("B")
                yield
            yield from wait_until_truly_controllable()

        avatar = get_player_avatar()
        here = tuple(avatar.map_group_and_number)
        try:
            here_name = MapRSE(here).name
        except Exception:
            here_name = f"UNKNOWN{here}"
        controllable = player_avatar_is_controllable()
        badges = [n for n in range(1, 9) if get_event_flag(f"BADGE0{n}_GET")]
        party = [(mon.species.name, mon.level) for mon in get_party()]

        # ‼ Only a CONTROLLABLE overworld arrival is worth writing. An anchor captured mid-scene
        # makes every later navigation leg fail for one harness reason instead of a map reason —
        # exactly the confound `prenorman_fodder_grind.ss1` (which loads inside a wild battle)
        # created for `probe_counter_reachability.py`.
        wrote = None
        if arrived and controllable:
            out.write_bytes(context.emulator.get_save_state())
            wrote = out
        else:
            log("[capture] NOT writing — an anchor must be an arrived, controllable overworld.")

        log(f"[capture] RESULT wrote={wrote.name if wrote else None} arrived={arrived} map={here_name} "
            f"tile={tuple(avatar.local_coordinates)} controllable={controllable} badges={badges} "
            f"party={len(party)} {party}")
        context.set_manual_mode()
        return


class GroundSweepMode(BotMode):
    """`#24-r116sweep`: DRIVEN reach-and-leave evidence for a candidate HUNTING_GROUND.

    ‼ WHY A NEW DRIVER RATHER THAN `probe_counter_reachability.py`. That probe answers with
    `calculate_path` + `region_reach` — a STATIC oracle. This project's standing rule is that
    only a DRIVEN `_navigate_riding_out` counts as reach evidence: `calculate_path` cannot cross
    warps and says so in its own error text, and trusting it here nearly retired a working
    feature once already (08-MISTAKES 2026-07-30).

    ‼ AND THE BAR IS REACH **AND LEAVE**, not reach. That is what `HUNTING_GROUNDS` encodes and
    what makes FIERY_PATH the only entry that converts (5/5 for Machop). A hunt walks in, spins,
    and walks out; a ground it cannot leave strands the run.

        PYTHONUTF8=1 SWEEP_GROUND=ROUTE116:11,7 SWEEP_RETURN=MAUVILLE_CITY:22,6           py -3.12 story_harness.py mauville_wedge.ss1 --driver groundsweep --frames 600000

    Emits: [sweep] RESULT ground=<map> arrived=<bool> left=<bool> badge03=<bool>
    ‼ `badge03` is reported because it decides WHICH question was answered: Wattson's counter
    hunt fires BEFORE his badge, so a sweep run post-badge proves nothing about his rung.
    """

    @staticmethod
    def name():
        return "GroundSweep"

    def on_battle_started(self, encounter):
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

            return LevelUpTravelBattleStrategy()
        return DefaultBattleStrategy()

    def run(self):
        import os

        from modules.map_data import MapRSE
        from modules.memory import get_event_flag
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

        yield from wait_until_truly_controllable()

        def _parse(raw):
            name, _, tile = raw.partition(":")
            x, _, y = tile.partition(",")
            return MapRSE[name.strip()], (int(x), int(y))

        ground, gtile = _parse(os.environ.get("SWEEP_GROUND", "ROUTE116:11,7"))
        back, btile = _parse(os.environ.get("SWEEP_RETURN", "MAUVILLE_CITY:22,6"))

        try:
            badge03 = bool(get_event_flag("BADGE03_GET"))
        except Exception:
            badge03 = None
        start = tuple(get_player_avatar().map_group_and_number)
        log(f"[sweep] start map={start} badge03={badge03} -> ground {ground.name}{gtile}, return {back.name}{btile}")

        arrived = left = False
        try:
            yield from _navigate_riding_out(ground, gtile, tries=24)
            arrived = tuple(get_player_avatar().map_group_and_number) == tuple(ground.value)
            log(f"[sweep] leg 1 done: arrived={arrived} at {tuple(get_player_avatar().map_group_and_number)}")
        except Exception as error:
            log(f"[sweep] leg 1 FAILED: {type(error).__name__}: {str(error)[:200]}")

        if arrived:
            try:
                yield from _navigate_riding_out(back, btile, tries=24)
                left = tuple(get_player_avatar().map_group_and_number) == tuple(back.value)
                log(f"[sweep] leg 2 done: left={left}")
            except Exception as error:
                log(f"[sweep] leg 2 FAILED: {type(error).__name__}: {str(error)[:200]}")

        log(f"[sweep] RESULT ground={ground.name} arrived={arrived} left={left} badge03={badge03} "
            f"verdict={'ADD to HUNTING_GROUNDS' if (arrived and left) else 'DO NOT ADD'}")
        context.set_manual_mode()
        return


class BoxWithdrawMode(BotMode):
    """CAPABILITY TEST for the WITHDRAW half of `#24-pcoverflow` — the half that has NEVER run.

    THE CLAIM UNDER TEST. `--driver boxcatch` proved a full-party catch reaches the PC box.
    That is strictly WORSE than the old refusal unless the bot can get the mon back out, and
    `withdraw_from_box` has logged `withdrawing` **0 times in every batch** — the two known
    breaks (`box_views` calling a property; both catch branches requiring `party < 6`) are
    fixed, but the collect path itself is still unexecuted code.

    ‼ THIS DRIVES THE PRODUCTION CALL SITE, NOT A STAND-IN. `higher_level_actions.
    heal_in_pokemon_center` reads `context.bot_mode_instance._hunted_counter_pids` and calls
    `withdraw_from_box(_pids)` between the nurse and the exit. The harness makes THIS mode the
    `bot_mode_instance`, so setting `self._hunted_counter_pids` here is exactly what the story
    bot does after a counter hunt. Calling `withdraw_from_box` directly would prove the
    function works and NOT that the piggyback fires — which is the half that was broken.

    Run from a save with a FULL PARTY and at least one mon in the box.
    `profiles/repro-boxcatch6/current_state.ss1` is exactly that (the end state of the proven
    box-catch run: party 6, box 2), copied to `saves/boxwithdraw.ss1`.

        PYTHONUTF8=1 WITHDRAW_CENTER=LilycoveCity py -3.12 story_harness.py \
            boxwithdraw.ss1 --driver boxwithdraw --frames 400000 --profile w1

    Emits: [boxwithdraw] RESULT withdrew=<bool> party_before/after box_before/after
           target=<species> deposited=<bool> frames=<n>
    """

    @staticmethod
    def name():
        return "BoxWithdraw"

    def on_battle_started(self, encounter):
        # ‼ A strategy is REQUIRED even for a walking probe (`boxcatch` run 1 hung 20,000
        # frames on a trainer payout because it returned None), and the TRAINER one must be
        # the PRODUCTION one. Run 1 of THIS probe used `DefaultBattleStrategy` for everything
        # and died 1,926 frames in to a Route 121 trainer approach:
        #     BotModeError -> Manual: Your Pokémon cannot battle due to HP below threshold,
        #     and 'flee' is not allowed in a trainer battle.
        # The save is a previous probe's end state, so the party arrives hurt — and
        # `LevelUpTravelBattleStrategy` exists for exactly this ("NEVER flees a TRAINER
        # battle", story_mode.py:118). Using Default here measured the probe's strategy
        # choice, not the withdraw path.
        # WILD battles keep Default on purpose: fleeing a wild IS allowed and is what we want
        # while walking to a Poké Centre — the parent's level-the-lead behaviour is what
        # walked `boxcatch` run 3's L3 HM slave into a whiteout.
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

            return LevelUpTravelBattleStrategy()
        return DefaultBattleStrategy()

    def run(self):
        import os

        from modules.map_data import PokemonCenter
        from modules.modes.util.higher_level_actions import heal_in_pokemon_center
        from modules.player import get_player_avatar
        from modules.pokemon_party import get_party
        from modules.pokemon_storage import get_pokemon_storage
        from modules.story.early_game import wait_until_truly_controllable
        from modules.story.pc_trip import box_views, find_in_box

        yield from wait_until_truly_controllable()

        # ‼ FIXTURE SETUP, NOT A BEHAVIOUR CHANGE — and it is required for the test to MEAN
        # anything. The only save that satisfies "full party AND a non-empty box" is a previous
        # box-catch probe's END state, so the party arrives at ~critical HP. Runs 1 and 2 both
        # died on the Route 121 walk before reaching a PC at all (run 1: trainer refusal; run 2:
        # won one trainer, LOST the next, whiteout at f5333). Neither measured the withdraw.
        # The variable under test is "can the bot retrieve a boxed mon at the PC", not "can a
        # battered party survive a route", so we remove the irrelevant variable rather than
        # re-roll the walk and hope.
        #
        # HP + status ONLY, written to the PARTY struct's unencrypted tail (data[86:88] current
        # HP, data[88:90] max, data[80] status bitfield — `modules/pokemon.py:1196-1227`). PP is
        # inside the ENCRYPTED substructure and is deliberately left alone: re-encrypting to
        # top up PP would risk a checksum mismatch, and no PP is needed to talk to a nurse.
        # ‼ `debug_write_party` only ever reads `.data` off each element, so a byte-patched
        # shim is enough and nothing is reconstructed — recreating the mons with
        # `debug_create_pokemon` would silently change levels/moves/EVs and therefore change
        # which mon `find_dead_weight` picks to deposit, which is part of what we are testing.
        if os.environ.get("WITHDRAW_HEAL_FIXTURE", "1") == "1":
            try:
                from types import SimpleNamespace

                from modules.debug_utilities import debug_write_party

                patched, healed, shown = [], 0, []
                for mon in get_party():
                    if mon is None:
                        continue
                    d = bytearray(mon.data)
                    if len(d) >= 90:
                        if d[86:88] != d[88:90] or d[80] != 0:
                            healed += 1
                        shown.append(f"{mon.species.name} {mon.current_hp}->{mon.total_hp}")
                        d[86:88] = d[88:90]      # current HP := max HP
                        d[80:84] = b"\x00" * 4   # clear the status bitfield
                    patched.append(SimpleNamespace(data=bytes(d)))
                debug_write_party(patched)
                # ‼ Log the BEFORE->AFTER we just wrote, never a `get_party()` read-back:
                # the party is cached per frame and we have not yielded, so re-reading here
                # returns the PRE-write values and prints `0/124` over a mon we just healed.
                # Run 4's log said exactly that and looked like a failed write on a run that
                # then won four battles.
                log(f"[boxwithdraw] FIXTURE: restored HP/status on {healed} of {len(patched)} "
                    f"party mons — {shown}")
            except Exception as error:  # noqa: BLE001
                log(f"[boxwithdraw] FIXTURE heal FAILED ({type(error).__name__}: "
                    f"{str(error)[:200]}) — continuing, but a whiteout is now likely.")

        party_before = len([m for m in get_party() if m is not None])
        box_before = get_pokemon_storage().pokemon_count
        here = tuple(get_player_avatar().map_group_and_number)
        log(f"[boxwithdraw] start party={party_before} box={box_before} map={here}")

        if party_before < 6 or box_before < 1:
            log(f"[boxwithdraw] ABORT — need a FULL party AND a non-empty box; got "
                f"party={party_before} box={box_before}. The test is meaningless otherwise: "
                f"with room in the party the deposit-to-make-room branch never runs.")
            context.set_manual_mode()
            return

        # ‼ POSITIVE CONTROL BEFORE THE TRIP. `box_views()` raising `TypeError` is precisely
        # the break that made `withdrawing` 0, and it fails SILENTLY (`find_in_box` swallows
        # it and returns None, which reads identically to "the mon isn't there"). Assert the
        # box is readable and the PID resolves BEFORE spending a journey on it — a null result
        # at the end would otherwise be unattributable.
        views, mons = box_views()
        log(f"[boxwithdraw] box read: {len(views)} views / {len(mons)} mons — "
            f"{[f'{v.species}L{v.level}' for v in views][:6]}")
        if not mons:
            log("[boxwithdraw] ABORT — box_views() returned nothing while pokemon_count="
                f"{box_before}. The box READ is broken; the withdraw cannot be graded.")
            context.set_manual_mode()
            return

        target = mons[0]
        pid = target.personality_value
        tname = getattr(getattr(target, "species", None), "name", "?")
        log(f"[boxwithdraw] target={tname} L{target.level} pid={pid}")
        if find_in_box({pid}) is None:
            log("[boxwithdraw] ABORT — find_in_box() cannot re-find the PID it just read. "
                "PID lookup is broken; fix that before grading the trip.")
            context.set_manual_mode()
            return

        # THE PRODUCTION HANDSHAKE: this is the attribute `heal_in_pokemon_center` reads.
        self._hunted_counter_pids = {pid}

        centre = os.environ.get("WITHDRAW_CENTER", "LilycoveCity").strip()
        log(f"[boxwithdraw] calling heal_in_pokemon_center({centre}) with "
            f"_hunted_counter_pids={{{pid}}}")
        try:
            yield from heal_in_pokemon_center(PokemonCenter[centre])
            log("[boxwithdraw] heal_in_pokemon_center returned")
        except Exception as error:  # noqa: BLE001
            import traceback

            log(f"[boxwithdraw] heal raised {type(error).__name__}: {str(error)[:300]}\n"
                f"{traceback.format_exc()[-1200:]}")

        party_after_mons = [m for m in get_party() if m is not None]
        party_after = len(party_after_mons)
        box_after = get_pokemon_storage().pokemon_count
        withdrew = any(getattr(m, "personality_value", None) == pid for m in party_after_mons)
        log(f"[boxwithdraw] RESULT withdrew={withdrew} target={tname} "
            f"party_before={party_before} party_after={party_after} "
            f"box_before={box_before} box_after={box_after} "
            f"deposited={box_after >= box_before} map={tuple(get_player_avatar().map_group_and_number)}")
        if not withdrew:
            log("[boxwithdraw] ‼ THE TARGET IS STILL BOXED. Read the `Story: PC —` lines above: "
                "no line at all = the piggyback never fired; 'nothing is safe to deposit' = "
                "find_dead_weight refused; 'could not withdraw' = the PC interaction failed.")

        # ‼ AND THE BOT MUST STILL BE PLAYABLE — but prove it by DRIVING IT TO A POSITIVE
        # OUTCOME, never by absence of a stall (08-MISTAKES 2026-08-07: I "confirmed" a wedge
        # twice and both times it was my probe idling).
        #
        # ‼ RUN 3 OF THIS PROBE GOT THAT WRONG TOO, and it is worth recording: the check here
        # was `_story_spin` until `local_coordinates` changes. `spin` TURNS ON THE SPOT — it
        # changes FACING, not position — and we exit the Centre into LILYCOVE_CITY, a town with
        # no grass, so there was also no encounter to break the loop. The avatar sat at (24,15)
        # for 20,000 frames and the harness printed `HANG CONFIRMED` over a bot that was
        # perfectly healthy. **A liveness check whose success condition the driven action
        # cannot produce is not a liveness check.**
        #
        # So: do a SECOND full `heal_in_pokemon_center`. It navigates into the building, works
        # a scripted nurse dialogue and walks back out — progress no in-place spin can fake —
        # and it doubles as a real assertion, because the withdraw must now NO-OP: the PID is
        # in the party, so `find_in_box` returns None and the piggyback must return without
        # touching the PC. A second `withdrawing` line here would mean a duplicate-withdraw
        # loop, which is the regression shape to fear from a piggyback that fires every heal.
        second_ok, second_frames = False, 0
        try:
            before_map = tuple(get_player_avatar().map_group_and_number)
            yield from heal_in_pokemon_center(PokemonCenter[centre])
            second_ok = True
            log(f"[boxwithdraw] second heal returned; map {before_map} -> "
                f"{tuple(get_player_avatar().map_group_and_number)}")
        except Exception as error:  # noqa: BLE001
            log(f"[boxwithdraw] second heal raised {type(error).__name__}: {str(error)[:200]}")

        party_final = [m for m in get_party() if m is not None]
        still_has = any(getattr(m, "personality_value", None) == pid for m in party_final)
        box_final = get_pokemon_storage().pokemon_count
        log(f"[boxwithdraw] AFTER usable={second_ok} second_heal_ok={second_ok} "
            f"still_has_target={still_has} party={len(party_final)} box={box_final} "
            f"frames={second_frames}")
        context.set_manual_mode()
        return


class RosterMode(BotMode):
    """FIRST DRIVE of `modules/story/roster.py`'s `reorder_party()` — the party-ORDER capability.

    THE CLAIM UNDER TEST. `plan_reorder`/`plan_last_slot` are proven exhaustively offline
    (`repro_roster_reorder.py`, 720 permutations replayed). **The DRIVER has never run.**
    `RotatePokemon(i, j)` with `j != 0` has never been driven anywhere in this project: every
    story strategy returns `None` from `choose_new_lead_after_battle`, so the only listener that
    would have called it never fires, and the proven lead-change path
    (`change_lead_party_pokemon`) always passes `j == 0`. So the whole `select_replacement`
    cursor drive (`menuing.py:1044-1056`) plus `PartyMenuExit` are UNEXECUTED CODE.

    ‼ PHASE 1 EXISTS SOLELY TO FORCE `j != 0`. Pinning slot 0 alone only ever emits `(0, k)` →
    `RotatePokemon(k, 0)`, i.e. the already-proven shape. A spec that also pins slot 1 emits a
    second swap with `destination == 1`, which is the genuinely new path. The driver ASSERTS it
    saw a `j != 0` swap rather than assuming the plan produced one — a run that quietly emitted
    only `j == 0` swaps would look like a PASS while proving nothing.

    ‼ THE TRACE READS `gPartyMenu` RAW, NEVER `get_party_menu_cursor_pos()`. That helper has a
    SIDE EFFECT: on `slot_id == -1` it calls `context.set_manual_mode()` and still returns
    (`menu_parsers.py:164-166`). An observer that kills the run it is observing is not an
    observer. `_raw_party_menu()` below re-implements the parse with no side effect.

    Phases (each re-reads the party and verifies BY PID, never by slot):
      1. `j != 0`      — target `[pid[2], pid[0]]`; expects swaps (0,2) then (1,2).
      2. REGI SHAPE    — `plan_last_slot`: pin FIRST and LAST, middles order-preserved. This is
                         the shape the Regi tombs need (KI-69) and the reason the module exists.
      3. IDEMPOTENCE   — re-issue phase 2's exact target. Must return True having driven ZERO
                         swaps and pressed nothing. The cheap path is the one content hits most.
      4. RESTORE       — put the original order back, so the run does not end holding a party
                         nobody asked for and so the reorder is shown to be invertible.
      5. CAN-CONTINUE  — ‼ KI-56's rule, violated by §Ch15, §Ch18 AND §Ch19. Not "controllable":
                         a real `calculate_path` off the end tile AND an actual position change.
                         A wedged half-open menu leaves the avatar perfectly "controllable".

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver roster --frames 400000

    Emits: [roster] RESULT phases=<n/n> saw_j_nonzero=<bool> idempotent=<bool>
           restored=<bool> can_continue=<bool> manual=<bool> frames=<n>
    """

    #: Frames the whole reorder may take before the driver calls it a hang. `reorder_party` is
    #: itself bounded (MAX_SWAPS*attempts passes x SWAP_TIMEOUT_FRAMES), so overshooting this
    #: means the bound leaked — which is the KI-38 shape and must be reported, not waited out.
    PHASE_BUDGET_FRAMES = 90_000

    @staticmethod
    def name():
        return "Roster"

    def on_battle_started(self, encounter):
        # Same reasoning as BoxWithdrawMode: a driver without a strategy hangs on a payout, and
        # the TRAINER strategy must be the production one (it never flees a trainer battle).
        # Mossdeep City has no grass, so a wild battle here would itself be a finding.
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

            return LevelUpTravelBattleStrategy()
        return DefaultBattleStrategy()

    @staticmethod
    def _raw_party_menu() -> dict:
        """`gPartyMenu` WITHOUT `get_party_menu_cursor_pos`'s `set_manual_mode()` side effect."""
        import struct as _struct

        from modules.memory import get_symbol_name, read_symbol, unpack_uint32

        try:
            p = read_symbol("gPartyMenu")
            return {
                "taskfunc": get_symbol_name(unpack_uint32(p[4:8]) - 1),
                "slot_id": _struct.unpack("<b", p[9:10])[0],
                "slot_id_2": _struct.unpack("<b", p[10:11])[0],
                "action": _struct.unpack("<B", p[11:12])[0],
            }
        except Exception as error:  # noqa: BLE001 - the tracer must never break the run
            return {"taskfunc": f"<unreadable {type(error).__name__}>", "slot_id": -99,
                    "slot_id_2": -99, "action": -99}

    def _drive_traced(self, generator, label: str):
        """Run `reorder_party` frame by frame, logging every CHANGE in the menu state.

        ‼ WHY MANUAL ITERATION RATHER THAN `yield from`. The handoff asks for one trace that
        settles both open unknowns — the stale-cursor read and the exit-menu timing gap — and
        those are only visible per frame while the sub-generator runs. Driving it by hand costs
        nothing and needs no change to production code.
        """
        from modules.memory import get_game_state
        from modules.tasks import get_tasks

        seen, frames, result = None, 0, None
        transitions = 0
        while True:
            try:
                next(generator)
            except StopIteration as stop:
                result = stop.value
                break
            frames += 1
            if frames > self.PHASE_BUDGET_FRAMES:
                # ‼ REPORT, never wait it out. `reorder_party` is internally bounded; blowing
                # this budget means a bound leaked (KI-38's exact shape).
                generator.close()
                log(f"[roster] {label} ‼ BUDGET BLOWN at {frames} frames — reorder_party's own "
                    f"bound leaked. Last menu state: {seen}")
                return None, frames
            # Sample cheaply; log only on CHANGE, so the trace is readable rather than 90k lines.
            if frames % 2 == 0 or frames < 4:
                menu = self._raw_party_menu()
                try:
                    tasks = ",".join(sorted(t.symbol for t in get_tasks()))[:150]
                    state = get_game_state().name
                except Exception as error:  # noqa: BLE001
                    tasks, state = f"<{type(error).__name__}>", "?"
                key = (state, menu["taskfunc"], menu["slot_id"], menu["slot_id_2"],
                       menu["action"], tasks)
                if key != seen:
                    seen = key
                    transitions += 1
                    if transitions <= 120:  # bounded trace; the interesting part is the front
                        log(f"[roster] {label} f{frames:<6} state={state} "
                            f"taskfunc={menu['taskfunc']} slot_id={menu['slot_id']} "
                            f"slot_id_2={menu['slot_id_2']} action={menu['action']} "
                            f"tasks=[{tasks}]")
            yield
        log(f"[roster] {label} finished after {frames} frames, {transitions} state transitions, "
            f"returned {result!r}")
        return result, frames

    def run(self):
        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.memory import GameState, get_game_state
        from modules.menu_parsers import parse_start_menu
        from modules.player import get_player_avatar
        from modules.pokemon_party import get_party
        from modules.story.early_game import wait_until_truly_controllable
        from modules.story.roster import plan_last_slot, plan_reorder, reorder_party

        def party_now():
            return [(m.personality_value, m.species.name, m.level)
                    for m in get_party() if m is not None]

        def pids_now():
            return [p for p, _s, _l in party_now()]

        yield from wait_until_truly_controllable()

        start = party_now()
        original = [p for p, _s, _l in start]
        here = get_player_avatar()
        log(f"[roster] start map={here.map_group_and_number} at={here.local_coordinates} "
            f"party={[f'{s}L{l}#{p}' for p, s, l in start]}")

        if len(original) < 4:
            # ‼ A 3-mon party cannot produce a `j != 0` swap, so the run would PASS while
            # proving nothing. Refuse rather than measure the wrong thing.
            log(f"[roster] ABORT — need a party of at least 4 to force a `j != 0` swap; got "
                f"{len(original)}. The test is meaningless otherwise.")
            _ctx.set_manual_mode()
            return

        phases_ok, saw_j_nonzero, results = 0, False, {}

        # ---- PHASE 1: the never-driven `j != 0` swap -------------------------------------
        target1 = [original[2], original[0]]
        planned1 = plan_reorder(original, target1)
        log(f"[roster] PHASE1 target={target1} PLANNED-SWAPS={planned1} "
            f"(destination,source) -> RotatePokemon(source, destination)")
        # ‼ ASSERT THE PLAN IS THE ONE WE MEAN before spending a drive on it.
        if not any(dest != 0 for dest, _src in planned1):
            log("[roster] ‼ PHASE1 plan contains no `destination != 0` swap — this run cannot "
                "exercise the untested path. Not a pass.")
        ok1, f1 = yield from self._drive_traced(reorder_party(target1), "PHASE1")
        after1 = pids_now()
        landed1 = after1[:2] == target1
        saw_j_nonzero = any(dest != 0 for dest, _src in planned1) and landed1
        log(f"[roster] PHASE1 returned={ok1} landed={landed1} party={after1} frames={f1}")
        phases_ok += 1 if (ok1 is True and landed1) else 0
        results["phase1"] = (ok1, landed1, f1)

        # ---- PHASE 2: the REGI shape — first AND last pinned ------------------------------
        current2 = pids_now()
        target2 = plan_last_slot(current2, first_pid=current2[-1], last_pid=current2[0])
        planned2 = plan_reorder(current2, target2)
        log(f"[roster] PHASE2 (REGI shape) target={target2} PLANNED-SWAPS={planned2}")
        ok2, f2 = yield from self._drive_traced(reorder_party(target2), "PHASE2")
        after2 = pids_now()
        landed2 = after2[0] == target2[0] and after2[-1] == target2[-1]
        log(f"[roster] PHASE2 returned={ok2} landed={landed2} first={after2[0]} "
            f"last={after2[-1]} party={after2} frames={f2}")
        phases_ok += 1 if (ok2 is True and landed2) else 0
        results["phase2"] = (ok2, landed2, f2)

        # ---- PHASE 3: idempotence — the cheap path content actually hits -------------------
        ok3, f3 = yield from self._drive_traced(reorder_party(target2), "PHASE3")
        after3 = pids_now()
        # ‼ "Zero swaps" is measured as FRAMES, not as a returned flag: `reorder_party` returns
        # True from the `if not plan` branch without yielding at all, so a correct no-op costs a
        # handful of frames. Anything larger means it re-opened the menu for nothing.
        idempotent = ok3 is True and after3 == after2 and f3 < 60
        log(f"[roster] PHASE3 (idempotence) returned={ok3} unchanged={after3 == after2} "
            f"frames={f3} idempotent={idempotent}")
        phases_ok += 1 if idempotent else 0
        results["phase3"] = (ok3, after3 == after2, f3)

        # ---- PHASE 4: restore the original order ------------------------------------------
        ok4, f4 = yield from self._drive_traced(reorder_party(original), "PHASE4")
        after4 = pids_now()
        restored = after4 == original
        log(f"[roster] PHASE4 (restore) returned={ok4} restored={restored} frames={f4}")
        phases_ok += 1 if (ok4 is True and restored) else 0
        results["phase4"] = (ok4, restored, f4)

        # ---- PHASE 5: CAN-CONTINUE ---------------------------------------------------------
        # ‼ NOT `controllable`. §Ch15 ended four floors underground, §Ch18 on an eleven-tile
        # island and §Ch19 in a living room, all three "controllable". A half-open party menu
        # would be worse still. So: not Manual, OVERWORLD, start menu closed, a real
        # `calculate_path` off the end tile, AND the avatar must actually MOVE.
        manual = _ctx.bot_mode == "Manual"
        state = get_game_state()
        try:
            menu_open = bool(parse_start_menu()["open"])
        except Exception as error:  # noqa: BLE001
            menu_open = f"<{type(error).__name__}>"
        path_ok, path_len, step_target = False, 0, None
        try:
            from modules.map import get_map_data
            from modules.map_path import calculate_path

            avatar = get_player_avatar()
            path = calculate_path(
                get_map_data(MapRSE(tuple(avatar.map_group_and_number)),
                             avatar.local_coordinates),
                get_map_data(MapRSE.MOSSDEEP_CITY, (28, 17)),  # the Pokemon Center door
            )
            path_len = len(path)
            path_ok = path_len > 0
            # ‼ WALK TO A TILE ON THE REAL PATH, not to a coordinate I picked from memory. A
            # hard-coded target that happens to be unwalkable would report `moved=False` and
            # blame the party menu for the probe's own bad guess. Stop 3 waypoints in so the
            # walk cannot follow the door warp into the building.
            if path_len >= 4 and not any(w.is_warp for w in path[:3]):
                step_target = path[2].coordinates
        except Exception as error:  # noqa: BLE001
            log(f"[roster] CAN-CONTINUE calculate_path raised {type(error).__name__}: "
                f"{str(error)[:200]}")
        moved, before_xy = False, get_player_avatar().local_coordinates
        if step_target is None:
            log("[roster] CAN-CONTINUE ‼ no safe on-path step target; the movement half of the "
                "check cannot run and `moved` stays False.")
        else:
            try:
                from modules.modes.util.walking import navigate_to

                yield from navigate_to(MapRSE(tuple(get_player_avatar().map_group_and_number)),
                                       step_target)
                moved = get_player_avatar().local_coordinates != before_xy
            except Exception as error:  # noqa: BLE001
                log(f"[roster] CAN-CONTINUE navigate to {step_target} raised "
                    f"{type(error).__name__}: {str(error)[:200]}")
        can_continue = (not manual) and state == GameState.OVERWORLD and menu_open is False \
            and path_ok and moved
        log(f"[roster] CAN-CONTINUE manual={manual} state={state.name} start_menu_open={menu_open} "
            f"path_ok={path_ok} path_len={path_len} moved={moved} {before_xy}->"
            f"{get_player_avatar().local_coordinates}")

        # ---- PHASE 6: MEASURE THE SAME DEFECT IN PRODUCTION (`_rotate_lead_safely`) ---------
        # ‼ NOT A FIX — A MEASUREMENT. An adversarial review of the `reorder_party` fix found the
        # identical shape in `early_game.py:1629-1630`: the SUCCESS path returns with no settle
        # while the FAILURE path at :1637 does settle. Its callers walk immediately
        # (`do_rustboro_gym:1838`, every `_lead_best_matchup` site), and it runs every training
        # round — so it is the hottest path in the bot.
        #
        # It has never been seen firing, and the reviewer's explanation is a MARGIN, not a
        # guarantee: `change_lead_party_pokemon` ends with `wait_for_task_to_start_and_finish` +
        # `wait_for_n_frames(10)`, whereas `RotatePokemon`/`PartyMenuExit` exits on the strictly
        # weaker "OVERWORLD and start menu closed". Adding an unconditional settle would cost
        # ~30 frames (`stable_frames`) on every rotation of a hot path to fix something nobody
        # has measured. So MEASURE IT: read `player_avatar_is_controllable()` on the very frame
        # `_rotate_lead_safely` returns, which is exactly what its callers do.
        rotate_ctrl, rotate_ran = None, False
        try:
            from modules.player import player_avatar_is_controllable
            from modules.story.early_game import _rotate_lead_safely

            before_lead = pids_now()
            yield from _rotate_lead_safely(2)
            rotate_ctrl = player_avatar_is_controllable()   # SAME FRAME the caller would walk
            rotate_ran = True
            log(f"[roster] PHASE6 (_rotate_lead_safely MARGIN, production) "
                f"controllable_on_return={rotate_ctrl} party {before_lead} -> {pids_now()}")
        except Exception as error:  # noqa: BLE001 - a measurement must never fail the run
            log(f"[roster] PHASE6 raised {type(error).__name__}: {str(error)[:200]}")

        log(f"[roster] RESULT phases={phases_ok}/4 saw_j_nonzero={saw_j_nonzero} "
            f"idempotent={idempotent} restored={restored} can_continue={can_continue} "
            f"manual={manual} rotate_lead_controllable_on_return={rotate_ctrl} "
            f"rotate_lead_measured={rotate_ran} detail={results}")
        log(f"[roster] ACCEPTANCE: {'PASS' if (phases_ok == 4 and saw_j_nonzero and can_continue) else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class BoxWriteMode(BotMode):
    """‼ PROVE `debug_write_box_slot()` AGAINST A LIVE EMULATOR. ✅ **IT NOW HAS BEEN — this
    driver PASSED 2026-08-15.** What follows is why it was WRITTEN, not current state.

    WHY THIS EXISTS, AND WHY IT IS SEPARATE FROM (P4). `debug_write_box_slot` is the fixture half
    the (P4) Slugma/Winona repro needs — that repro requires a FULL party AND a boxed counter at
    the same time, which the bot cannot cheaply reach. Two things about it are already proven:
    its address arithmetic matches the reader line-for-line (`pokemon_storage.py:93-97,148-149`),
    and `pokemon.data[:80]` is a valid boxed record (`repro_box_counter_move_test.py` decodes a
    real encrypted party record's first 80 bytes to the same species, `is_valid=True`).
    ⛔ **What was NOT proven is that `write_bytes` at that address lands where the reader looks.**

    ‼ AND THAT GAP IS DANGEROUS SPECIFICALLY HERE. `box_counter_pid` wraps its whole body in
    `except: return None` (`counter_hunt.py:302-303`), so a record that fails to decode is
    INDISTINGUISHABLE from "no counter in the box" — which is exactly ARM A's expected answer in
    the (P4) A/B. A bad write would make that repro "reproduce" the user's bug while proving
    nothing. Proving the write here, ONCE, in isolation, removes that confound before any test
    depends on it. (Raised by adversarial review; the reviewer declined to block on it and asked
    for it before the driver is built.)

    ⛔ GRADED ON IDENTITY, NEVER ON A COUNT. A box-count delta could be produced by anything; the
    verdict is that the PID we wrote is readable back through the PRODUCTION reader, with the right
    species, level and move — and that it did NOT land in the party.

    Run:  PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver boxwrite --frames 200000
    Expect: wrote=True readback=True pid_match=True species_ok=True move_ok=True
            not_in_party=True  ACCEPTANCE: PASS
    """

    @staticmethod
    def name() -> str:
        return "BoxWrite"

    def run(self):
        from modules.context import context as _ctx
        from modules.debug_utilities import debug_create_pokemon, debug_write_box_slot
        from modules.pokemon import get_species_by_name
        from modules.pokemon_party import get_party
        from modules.pokemon_storage import get_pokemon_storage
        from modules.modes.util import wait_for_n_frames
        # ‼ NOT a module-level name in this harness — every driver imports it locally from
        # `modules.story.early_game`. Assuming it was global cost this driver its first run:
        # the harness caught the NameError, logged it, and the run completed with NO
        # `[boxwrite]` lines at all — a silent no-op that looked like a finished run.
        from modules.story.early_game import wait_until_truly_controllable

        yield from wait_until_truly_controllable()

        def box_pids():
            return {s.pokemon.personality_value
                    for b in get_pokemon_storage().boxes for s in (b.slots or [])}

        before = box_pids()
        log(f"[boxwrite] BEFORE: {len(before)} mon(s) in storage")

        # ‼ Slugma L15 — the (P4) fixture exactly: pure FIRE, and at L15 its natural learnset
        # includes ROCK THROW, which is the MOVE answer Winona needs. Built by the production
        # fabricator so the bytes are the ones the real code path produces.
        mon = debug_create_pokemon(species=get_species_by_name("Slugma"), level=15)
        pid = mon.personality_value
        knows_rock_throw = mon.knows_move("Rock Throw")
        log(f"[boxwrite] FIXTURE Slugma L{mon.level} pid={pid:08X} "
            f"rock_throw={knows_rock_throw} types={[t.name for t in mon.species.types]}")

        wrote, where = False, None
        try:
            where = debug_write_box_slot(mon)
            wrote = True
            log(f"[boxwrite] WROTE to box {where[0]} slot {where[1]}")
        except Exception as error:  # noqa: BLE001 — a refused write is a RESULT, not a crash
            log(f"[boxwrite] WRITE RAISED {type(error).__name__}: {str(error)[:200]}")

        # ‼‼ YIELD BEFORE READING BACK. `get_pokemon_storage()` is cached while `age_in_frames==0`
        # (`pokemon_storage.py:146-147`), so a same-frame read sees the PRE-write box and looks
        # exactly like a failed write. The party equivalent of this trap already burned a run.
        yield from wait_for_n_frames(2)

        after = box_pids()
        readback = pid in after and pid not in before
        found = None
        for b in get_pokemon_storage().boxes:
            for s in (b.slots or []):
                if s.pokemon.personality_value == pid:
                    found = s.pokemon
        species_ok = found is not None and found.species.name == "Slugma"
        move_ok = found is not None and found.knows_move("Rock Throw")
        level_ok = found is not None and found.level == 15
        # ⛔ It must be in the BOX, not the party — a write to the wrong address could plausibly
        # land in `gPlayerParty`, which is adjacent in the kind of mistake this is checking for.
        not_in_party = all(p.personality_value != pid for p in get_party())

        log(f"[boxwrite] READBACK pid_in_box={readback} species_ok={species_ok} "
            f"level_ok={level_ok} move_ok={move_ok} not_in_party={not_in_party} "
            f"storage_now={len(after)}")

        ok = bool(wrote and readback and species_ok and level_ok and move_ok and not_in_party)
        log(f"[boxwrite] RESULT wrote={wrote} at={where} readback={readback} "
            f"species_ok={species_ok} level_ok={level_ok} move_ok={move_ok} "
            f"not_in_party={not_in_party}")
        log(f"[boxwrite] ACCEPTANCE: {'PASS' if ok else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class PartyPidsMode(BotMode):
    """Dump the party and PC box by IDENTITY — species, level and PERSONALITY VALUE. Read-only.

    ‼ WHY A DRIVER AND NOT A PROBE. `probe_anchor_inventory.py` reports badges and map but not the
    party, and the harness's own `party=[...]` line carries species/level but **not PIDs** — and a
    PID is the only thing that can answer the question this exists for: **do a save's Ninjask and
    Shedinja share a personality value?** (KI-78: `CreateShedinja` memcpies its sibling and never
    rewrites the PID, so the twins are PID-identical for life, and that keys a RELEASE path.)

    ⛔ It CHANGES NOTHING — no writes, no navigation, no battles. Answering "what is in this save"
    must not perturb the save it is answering about.
    """

    @staticmethod
    def name() -> str:
        return "PartyPids"

    def run(self):
        from modules.context import context as _ctx
        from modules.pokemon_party import get_party
        from modules.pokemon_storage import get_pokemon_storage
        from modules.story.early_game import wait_until_truly_controllable

        yield from wait_until_truly_controllable()

        seen: "dict[int, list[str]]" = {}
        for p in get_party():
            log(f"[partypids] PARTY slot={p.index} {p.species.name:<12} L{p.level:<3} "
                f"pid={p.personality_value:08X} egg={p.is_egg}")
            seen.setdefault(p.personality_value, []).append(f"{p.species.name}(party{p.index})")
        n_box = 0
        for b in get_pokemon_storage().boxes:
            for s in (b.slots or []):
                mon = s.pokemon
                n_box += 1
                log(f"[partypids] BOX{b.number:<2} slot={s.slot_index:<2} {mon.species.name:<12} "
                    f"L{mon.level:<3} pid={mon.personality_value:08X}")
                seen.setdefault(mon.personality_value, []).append(
                    f"{mon.species.name}(box{b.number}.{s.slot_index})")

        # ‼ THE POINT. A shared PID across two DIFFERENT species is the KI-78 twin signature.
        collisions = {pid: who for pid, who in seen.items() if len(who) > 1}
        for pid, who in collisions.items():
            log(f"[partypids] ‼‼ PID COLLISION {pid:08X} shared by {who} — this is the KI-78 shape "
                f"(a Shedinja carries its Ninjask's personality value for life)")
        log(f"[partypids] RESULT party={len(list(get_party()))} boxed={n_box} "
            f"collisions={len(collisions)}")
        log(f"[partypids] ACCEPTANCE: PASS (read-only dump; it reports, it does not grade)")
        _ctx.set_manual_mode()
        return


class BoxCounterMode(BotMode):
    """(P4) STAGE 1 — `box_counter_pid` against a REAL PC BOX, both arms. THE DECISIVE CLAIM.

    ‼ WHAT NO EXISTING TEST COVERS. The user-observed Slugma/Winona derail's root cause is
    `box_counter_pid` having been TYPE-ONLY. That fix is gated — but `repro_box_counter_move_test`
    proves it against **`FakeStorage` with fabricated mons**. This driver is the first time the
    function runs against **real `gPokemonStorage` memory, on a real Pokémon the game's own reader
    decodes**, under both arms.

    ⛔ **STAGE 1 ONLY, AND THAT IS DELIBERATE.** It calls `box_counter_pid` directly and stops.
    It does NOT drive the heal/withdraw — that is Stage 2, `BoxCounter2Mode`, which **SUBCLASSES
    this class** and therefore RE-PROVES Stage 1 on every Stage 2 run (playbook §4c rule 2: copy a
    proven phase and it rots; subclass it and it cannot). Reason for the split: Stage 1 **cannot
    derail**, so ARM A — the arm that reproduces the bug — still emits a RESULT. Under KI-71 a
    derailed run has its generator abandoned and prints nothing at all, so putting the decisive
    claim behind the risky step would make the bug's own arm unreportable.
    ‼ The body lives in `_stage1()`, which does NOT call `set_manual_mode()`; only `run()` does.
    A subclass that called `super().run()` would drop to Manual before its own first line.

    ‼‼ THE ORDERING THAT MAKES OR BREAKS THIS TEST. `hunt()` snapshots `before_box_pids` at
    `counter_hunt.py:491` and passes it as `exclude_pids` at `:556`; `:288` skips any PID in that
    set. **A Slugma injected BEFORE the snapshot is filtered out and the function returns
    `None` in BOTH arms** — ARM A would "reproduce" the bug for entirely the wrong reason and ARM B
    would fail. So the snapshot is taken FIRST, the injection happens AFTER, and
    `slugma_pid not in before_box_pids` is ASSERTED and printed. ⛔ The tempting shortcut — passing
    an empty exclude set — would delete the production guard from the test.
    (These citations read `:476-477`/`:542`/`:284-285` until 2026-08-15; the file had moved and the
    numbers were stale in four places. Verified against the file, not copied forward.)

    ⛔ WHY SLUGMA AND NOT ANY BOXED MON. Slugma is **pure FIRE**; Winona needs
    Rock/Ice/Dragon/Electric. The type branch (`:290`) must therefore be provably INERT, or the
    move branch is never measured and both arms pass. The fixture's own types are asserted disjoint
    from `needed`. And the verdict is `== slugma_pid`, never `is not None`: the function returns the
    FIRST match in box order, so any other qualifying mon would make ARM B green without the move
    branch ever running.

    ⛔⛔ THE SOLE-CANDIDATE CONTROL IS NOT "THE BOX IS EMPTY" (corrected 2026-08-15, by measurement).
    It used to assert `occupants == [pid]`, which passes only because `post_dive.ss1`'s 14 boxes are
    ALL EMPTY (measured, `probe_box_contents.py`). `ch13_fortree_door.ss1` — Stage 2's anchor when
    this control was written, since replaced by `fortree_gym_wedge.ss1`, whose boxes are ALSO empty,
    so ⚠ **this control is correct but is no longer EXERCISED by Stage 2's current anchor** — holds
    **Castform L25 `pid=6ADF9056`** at box0.slot0 — pure Normal, so no TYPE match, but it knows
    **Powder Snow (Ice, damaging)**, so it qualifies on the MOVE branch and sits AHEAD of anything
    injected. The old control would have ABORTED there. ‼ Production is not fooled — the Castform
    is in the box BEFORE the run, hence in `before_box_pids`, hence excluded at `:288`. So the
    control now asks PRODUCTION the question instead of re-deriving it:
        `sole = box_counter_pid(NEEDED, exclude_pids=before | {slugma_pid}) is None`
    *If nothing else can be returned once the Slugma is taken away, the Slugma is the only thing
    that could have been returned.* Zero re-implementation (re-deriving "does this bystander
    qualify?" in the driver is the exact sin that let `repro_box_counter_move_test` test a COPY of
    the fault instead of the real hook), and it is the right question in BOTH arms: under ARM B it
    rules out type AND move bystanders; under ARM A it rules out TYPE bystanders, which is exactly
    what ARM A's expected `None` needs. Bystanders are still printed — but for DIAGNOSIS only, and
    the verdict never depends on driver-side logic.

    ARMS (`POKEBOT_BOXCOUNTER_TYPEONLY_A`, a permanent hook — never edit code to inject a fault):
        unset  = ARM B, the shipped fix  -> must return the Slugma's PID
        "1"    = ARM A, pre-fix type-only -> must return None

    Run:  POKEBOT_BOXCOUNTER_TYPEONLY_A=  PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 \\
              --driver boxcounter --frames 200000
    Expect ARM B: arm=B fixture_ok=True disjoint=True not_excluded=True not_in_party=True
                  needed_ok=True sole=True pid_match=True     ACCEPTANCE: PASS
    Expect ARM A: arm=A ... pid_match=True (its expectation is `None`)  ACCEPTANCE: PASS
    ‼ BOTH ARMS PASS when the code is correct — `pid_match` means "matched THIS ARM's expectation".

    Two controls added 2026-08-15, both from an adversarial pass over the Stage 2 plan:
    * `not_in_party` — `debug_create_pokemon` does NOT guarantee a fresh PID: it starts from the
      template's `personality_value` (`debug_utilities.py:350-357`, `0x00000000` when
      `original_pokemon is None`) and only re-rolls if nature/gender/shiny disagree. A fixture PID
      that already exists in the party would make Stage 2's "it reached the party" check read TRUE
      before the heal even ran. Asserted against party AND box, printed either way.
    * `needed_ok` — `NEEDED` is re-derived from the LIVE type chart seeded with Winona's real
      `ace_types = ("Dragon", "Flying")` (`story_mode.py`'s Winona `cfg`) using the same
      `>= 2.0` rule as `_boss_plan_is_hopeless` (`:1600-1606`), then compared to the literal above,
      so a type-data change is LOUD instead of silently making the fixture meaningless.
      ⛔ `_boss_plan_is_hopeless()` itself CANNOT be called for this: it returns `(False, [])`
      until losses have PLATEAUED (`:1507`, `:1512`), and a fresh anchor has zero losses.
    """

    @staticmethod
    def name() -> str:
        return "BoxCounter"

    #: ⛔⛔ **NOT `{Rock, Ice, Dragon, Electric}` — MEASURED 2026-08-15, and the older set is WRONG.**
    #: Winona's ace is **Altaria L33, Dragon/Flying**, and `_boss_plan_is_hopeless` derives `needed`
    #: from `ace_types` ALONE (`story_mode.py:1600-1606`), requiring the product across BOTH ace
    #: types to be `>= 2.0`. Electric is **0.5x into Dragon** and 2.0x into Flying — product
    #: **1.0**, i.e. NEUTRAL on Altaria — so production never yields it. The live chart agrees:
    #: the first run of the `needed_ok` control printed `derived=['Dragon','Ice','Rock']` and
    #: ABORTED the fixture rather than testing a set production would never pass.
    #: ‼ The old claim is not crazy, just mis-scoped: Electric IS 2.0x on her other four mons
    #: (Swablu/Tropius/Pelipper/Skarmory are all Flying) — but the ACE is what `cfg` names.
    #: It is repeated in `counter_hunt.py:250` and in the P4 design note; both are corrected.
    NEEDED_EXPECTED = {"Rock", "Ice", "Dragon"}
    #: The `cfg["ace_types"]` of the Winona fight in `story_mode.py`. If that dict ever changes,
    #: `needed_ok` still passes (both sides move together) — so the STATIC gate
    #: `repro_boxcounter_needed_parity.py` asserts this tuple against the production source.
    ACE_TYPES = ("Dragon", "Flying")

    @staticmethod
    def _derive_needed(ace_type_names) -> set:
        """The attacking types that are >= 2.0x against ALL of `ace_type_names`.

        ‼ Deliberately the SAME rule as `_boss_plan_is_hopeless` (`story_mode.py:1600-1606`),
        read off the LIVE type chart so a type-data change is loud. ⛔ We cannot call that
        function itself: it short-circuits to `(False, [])` until losses have plateaued
        (`:1507` needs `losses >= PLATEAU_LOSS_THRESHOLD`, `:1512` needs >=6 KO-history
        entries), and a fresh anchor has zero losses.
        """
        from modules.pokemon import _types_by_name, get_type_by_name

        aces = [get_type_by_name(n) for n in ace_type_names]
        out = set()
        for atk_name, atk_type in _types_by_name.items():
            eff = 1.0
            for t in aces:
                eff *= atk_type.get_effectiveness_against(t)
            if eff >= 2.0:
                out.add(atk_name)
        return out

    def _stage1(self, tag: str = "boxcounter"):
        """Steps 1-4 of the design note's §5 chain. Sets `self.s1_*`; returns True on PASS.

        ⛔ DOES NOT call `set_manual_mode()` and DOES NOT print `ACCEPTANCE:` — those belong to
        whoever owns the run. A subclass that inherited a terminator here would drop to Manual
        before its own first line, and (KI-71) that failure is SILENT: no exception, no crash,
        just a healthy-looking idle. `run()` below is the only Stage 1 terminator.
        """
        import os as _os

        from modules.debug_utilities import debug_create_pokemon, debug_write_box_slot
        from modules.pokemon import get_species_by_name
        from modules.pokemon_party import get_party
        from modules.pokemon_storage import get_pokemon_storage
        from modules.modes.util import wait_for_n_frames
        from modules.story.counter_hunt import _box_pids, box_counter_pid
        from modules.story.early_game import wait_until_truly_controllable

        arm = "A" if _os.environ.get("POKEBOT_BOXCOUNTER_TYPEONLY_A", "0") == "1" else "B"
        self.s1_arm = arm
        self.s1_pid = None
        self.s1_got = None
        self.s1_before = frozenset()

        yield from wait_until_truly_controllable()

        # ---- 0. THE OPERATIVE `needed` IS THE DERIVED ONE — what production would actually pass.
        #         The literal is only the EXPECTATION it is checked against, so a type-data change
        #         is loud instead of silently making the fixture meaningless.
        NEEDED = self._derive_needed(self.ACE_TYPES)
        needed_ok = NEEDED == self.NEEDED_EXPECTED
        self.s1_needed = NEEDED
        log(f"[{tag}] ARM={arm} (POKEBOT_BOXCOUNTER_TYPEONLY_A="
            f"{_os.environ.get('POKEBOT_BOXCOUNTER_TYPEONLY_A', '<unset>')!r}) needed={sorted(NEEDED)}")
        log(f"[{tag}] NEEDED-DERIVATION ace_types={self.ACE_TYPES} -> derived={sorted(NEEDED)} ; "
            f"expected={sorted(self.NEEDED_EXPECTED)} ; needed_ok={needed_ok}")

        # ---- 1. SNAPSHOT FIRST. See the docstring: injecting before this makes the test lie. ----
        before = _box_pids()
        self.s1_before = before
        log(f"[{tag}] SNAPSHOT before_box_pids={len(before)} entries "
            f"({sorted(format(p, '08X') for p in before)}) — taken BEFORE injection, exactly as "
            f"hunt() does at counter_hunt.py:491")

        # ---- 2. INJECT the fixture ----
        mon = debug_create_pokemon(species=get_species_by_name("Slugma"), level=15)
        pid = mon.personality_value
        self.s1_pid = pid
        self.s1_mon = mon
        try:
            where = debug_write_box_slot(mon)
        except Exception as error:  # noqa: BLE001 — a refused write is an ABORT, not a FAIL
            log(f"[{tag}] ‼ FIXTURE ABORT — write raised {type(error).__name__}: {error}")
            return False
        yield from wait_for_n_frames(2)   # storage is cached per frame; read-back needs a yield

        # ---- 3. READ-BACK CONTROL. ⛔ MANDATORY. `box_counter_pid` swallows every exception into
        #         `return None`, so a fixture that failed to decode is INDISTINGUISHABLE from ARM
        #         A's expected miss. Without this, ARM A "passes" on a broken fixture.
        found = None
        for b in get_pokemon_storage().boxes:
            for s in (b.slots or []):
                if s.pokemon.personality_value == pid:
                    found = s.pokemon
        types = [] if found is None else [t.name for t in found.species.types]
        fixture_ok = bool(found is not None and found.species.name == "Slugma"
                          and found.level == 15 and found.knows_move("Rock Throw"))
        disjoint = bool(found is not None and not (set(types) & NEEDED))
        not_excluded = pid not in before
        # ‼ THE FIXTURE'S PID MUST BE NEW. `debug_create_pokemon` starts from the template's
        # `personality_value` (`debug_utilities.py:350-357`; `0x00000000` when `original_pokemon
        # is None`) and only re-rolls it if nature/gender/shiny disagree — it does NOT guarantee
        # a PID nothing else already owns. If the party already held this PID, Stage 2's "the
        # Slugma reached the party" check would read TRUE before the heal ever ran. ⛔ And this
        # check matters somewhere real: `ch13_fortree_door.ss1` already contains a REAL PID
        # collision (Shedinja+Ninjask both `42207D6F`). ⚠ Stage 2's CURRENT anchor
        # (`fortree_gym_wedge.ss1`) has no such twins, so this check is a guard rather than a
        # demonstration there — keep it: the collision save is still used by collision tests.
        party_pids = {m.personality_value for m in get_party() if m is not None}
        not_in_party = pid not in party_pids
        log(f"[{tag}] FIXTURE at box{where} pid={pid:08X} species="
            f"{None if found is None else found.species.name} level="
            f"{None if found is None else found.level} rock_throw="
            f"{None if found is None else found.knows_move('Rock Throw')} types={types}")
        log(f"[{tag}] CONTROLS fixture_ok={fixture_ok} disjoint_from_needed={disjoint} "
            f"not_in_before_box_pids={not_excluded} not_in_party={not_in_party} "
            f"needed_ok={needed_ok}")
        if not (fixture_ok and disjoint and not_excluded and not_in_party and needed_ok):
            # ‼ ABORT with a message DISTINCT from a test failure. A fixture defect graded as FAIL
            # would be read as "the fix is broken", which is the wrong conclusion entirely.
            log(f"[{tag}] ‼ FIXTURE ABORT — the controls above did not hold, so neither arm's "
                "answer would mean anything. This is a FIXTURE defect, NOT a verdict on the fix.")
            return False

        # ⛔ SOLE-CANDIDATE CONTROL — asked of PRODUCTION, not re-derived. See the class docstring:
        # the anchor's box is NOT empty (Castform `6ADF9056`, which qualifies on Powder Snow), so
        # `occupants == [pid]` was wrong. If nothing can be returned once the Slugma is ALSO
        # excluded, then the Slugma is the only thing that could have been returned.
        shadow = box_counter_pid(NEEDED, exclude_pids=(set(before) | {pid}))
        sole = shadow is None
        bystanders = [(s.pokemon.personality_value, s.pokemon.species.name)
                      for b in get_pokemon_storage().boxes for s in (b.slots or [])
                      if s.pokemon.personality_value != pid]
        log(f"[{tag}] SOLE-CANDIDATE box_counter_pid(needed, exclude=before|{{fixture}}) -> "
            f"{'None' if shadow is None else format(shadow, '08X')} ; sole={sole}")
        log(f"[{tag}] BYSTANDERS (diagnosis only, never the verdict): "
            + (", ".join(f"{n}:{p:08X}{' EXCLUDED' if p in before else ' NOT-EXCLUDED'}"
                         for p, n in bystanders) or "(none)"))

        # ---- 4. THE CALL, with the REAL production exclude set ----
        got = box_counter_pid(NEEDED, exclude_pids=before)
        self.s1_got = got
        expected = None if arm == "A" else pid
        pid_match = got == expected
        log(f"[{tag}] CALL box_counter_pid(needed, exclude_pids=before) -> "
            f"{'None' if got is None else format(got, '08X')} ; ARM {arm} expected "
            f"{'None' if expected is None else format(expected, '08X')} ; match={pid_match}")

        ok = bool(fixture_ok and disjoint and not_excluded and not_in_party and needed_ok
                  and sole and pid_match)
        log(f"[{tag}] RESULT arm={arm} fixture_ok={fixture_ok} disjoint={disjoint} "
            f"not_excluded={not_excluded} not_in_party={not_in_party} needed_ok={needed_ok} "
            f"sole={sole} pid_match={pid_match}")
        return ok

    def run(self):
        from modules.context import context as _ctx

        ok = yield from self._stage1("boxcounter")
        log(f"[boxcounter] ACCEPTANCE: {'PASS' if ok else 'FAIL'}")
        log("[boxcounter] ‼ STAGE 1 ONLY — the heal/withdraw half is `--driver boxcounter2`.")
        _ctx.set_manual_mode()
        return


class BoxCounter2Mode(BoxCounterMode):
    """(P4) STAGE 2 — the REAL heal collects the counter, or (ARM A) provably does not.

    ‼ WHAT THIS ADDS OVER STAGE 1. Stage 1 proves `box_counter_pid` returns the right PID.
    It does NOT prove the bot then USES it. This drives the production
    `heal_in_pokemon_center(PokemonCenter.FortreeCity)` — with its three PC piggybacks — and
    grades §5 steps 5-7 of `ai-research-notes/2026-08-15-p4-boxcounter-repro-design.md`:
    the Slugma MOVED box→party (identity, both directions), it still knows Rock Throw, it takes
    slot 0, and a SECOND heal's withdraw NO-OPs *for the right reason*.

    ‼‼ WHY THE PID MUST COME FROM PRODUCTION, AND WHAT THAT BUYS. `boxwithdraw` HAND-SETS
    `_hunted_counter_pids`, bypassing `box_counter_pid` entirely — **that is exactly why the
    existing driver never caught the user's bug**. Here the set is filled ONLY with what
    `box_counter_pid` returned:
        `self._hunted_counter_pids = set() if got is None else {got}`
    ⇒ ARM A reproduces the user's derail ORGANICALLY and end-to-end: `got is None` → empty set →
    `counter_withdraw_outcome()` False (`higher_level_actions.py:337`) → the SKIP is logged and
    `withdraw_from_box` is never called (`:342-344`) → the heal completes and the counter STAYS
    BOXED. Nothing in the driver simulates that; production does it.
    ⛔ **WHAT THIS STILL DOES NOT PROVE:** the `hunt()` → `story_mode.py:1750` registration wiring.
    The Slugma is INJECTED, and the PID is published by the driver rather than by a real catch.
    Stage 2 tests everything DOWNSTREAM of registration, and nothing upstream of it.

    ⛔ SUBCLASS, NOT COPY (playbook §4c rule 2) — every Stage 2 run re-proves Stage 1 first, on
    this anchor, so the two cannot drift. It calls `_stage1()`, never `super().run()`: `run()`
    ends in `set_manual_mode()`, and inheriting that would drop the bot to Manual before Stage 2's
    first line — silently, since KI-71 means an abandoned generator raises nothing at all.

    ‼‼ ANCHOR: `saves/fortree_gym_wedge.ss1` (badges 12345, Winona UNBEATEN, party FULL at 6 so
    the make-room deposit path is exercised). ⛔ NOT `post_dive.ss1` — that save is POST-Winona, so
    the counter rung cannot fire.
    ⛔⛔ AND **NOT** `ch13_fortree_door.ss1`, THOUGH THIS DOCSTRING NAMED IT FOR A DAY. That save is
    on **ROUTE120**, and the run died on its FIRST leg: `Cannot reach FORTREE_CITY: it is not
    walkable from ROUTE120`. That is **KI-24**, documented in our own `region_reach.py:7-11` —
    Routes 118/119/120 are dual-elevation-bridge maps `calculate_path` reads as WALLS. Every
    Winona-era anchor we own is on ROUTE119/120 EXCEPT this wedge. The feared gym-exit leg (the
    reason the swap was resisted) cost nothing when measured.
    ⚠ WHAT THE WEDGE GIVES UP: it has NO Shedinja/Ninjask twins and its **boxes are EMPTY**
    (measured: `before_box_pids=0 entries ([])`), so Stage 2 no longer runs over a live KI-78 PID
    collision, and the sole-candidate control below is no longer EXERCISED by this anchor even
    though it is still correct. `ch13_fortree_door.ss1` stays the anchor for any test whose SUBJECT
    is that collision.

    ⛔ EVERY CLAIM IS AN IDENTITY. `withdraw_from_box` NEVER RAISES (`pc_trip.py:475-478`), so "no
    exception" is not evidence; and `pc_trip.py:472-473` PRINTS "{name} is in the party" after
    reading only `len(get_party())` — a COUNT wearing an identity's clothes. Never grade on that
    line. Counts here are REPORTED only: on a successful withdraw every count is unchanged,
    because the make-room deposit cancels the withdraw.

    ARMS: the same permanent `POKEBOT_BOXCOUNTER_TYPEONLY_A` hook Stage 1 uses.
        unset = ARM B — the counter is collected and leads.
        "1"   = ARM A — the counter stays boxed. THE USER'S BUG, END TO END.
    Both arms PASS when the code is correct; each grades its OWN expectation.

    Run:  PYTHONUTF8=1 py -3.12 story_harness.py fortree_gym_wedge.ss1 \\
              --driver boxcounter2 --frames 400000
    Expect ARM B: STEPS 5,6,7 all -> True, ACCEPTANCE: PASS
    Expect ARM A: hunted_counter_pids=set(), still_boxed=True, in_party=False, ACCEPTANCE: PASS

    ⛔ THE GYM LEG IS OFF BY DEFAULT (`POKEBOT_BOXCOUNTER2_GYM=1` to enable) and is REPORTED,
    NEVER GRADED (§5 step 8). An L15 Slugma will likely lose to Altaria L33, and a whiteout drops
    to Manual where KI-71 abandons the generator and NOTHING prints — so the `ACCEPTANCE:` line is
    emitted BEFORE any gym attempt, exactly as Stage 1 is emitted before Stage 2's risky leg.
    """

    @staticmethod
    def name() -> str:
        return "BoxCounter2"

    def run(self):
        import os as _os

        from modules.context import context as _ctx
        from modules.map_data import PokemonCenter
        from modules.modes.util import wait_for_n_frames
        from modules.modes.util.higher_level_actions import heal_in_pokemon_center
        from modules.player import get_player_avatar
        from modules.pokemon_party import get_party
        from modules.pokemon_storage import get_pokemon_storage
        from modules.story.early_game import _lead_best_matchup
        from modules.story.pc_trip import find_in_box

        TAG = "boxcounter2"

        def party_map():
            """{(pid, species): "Species L<n>"} — the KI-78 identity, never index, never bare PID.

            ⛔⛔ KEYED ON `(personality_value, species.name)`, AND THAT IS NOT PEDANTRY. Keyed on
            PID alone this dict SILENTLY LOSES A POKÉMON: `ch13_fortree_door` — this driver's
            anchor on its FIRST drive, since replaced by `fortree_gym_wedge.ss1` — holds a real
            Shedinja+Ninjask pair BOTH with `pid=42207D6F` (a Shedinja inherits its Ninjask's PID),
            so a PID-keyed map reported a FULL PARTY OF 6 AS 5 on that drive. ⚠ The current anchor
            has no twins, so the key is a GUARD here, not a demonstration — do not "simplify" it.
            That is exactly the collision KI-78 was filed for, and the identity fix it shipped is
            `(personality, species)` — the same key used here.
            """
            return {(m.personality_value, m.species.name): f"{m.species.name} L{m.level}"
                    for m in get_party() if m is not None}

        SLUG = "Slugma"

        def step(n, what: str) -> None:
            # ‼ A HEARTBEAT, not decoration. If the generator is abandoned mid-flight (KI-71:
            # no exception, no crash, the process just idles), the LAST STEP printed is the only
            # thing that says where it died. Silence must never be readable as success.
            log(f"[{TAG}] STEP {n}/8 — {what}")

        # ---- STAGE 1 RE-PROVES ITSELF FIRST, on this anchor, under this arm. ----
        ok1 = yield from self._stage1(TAG)
        log(f"[{TAG}] STAGE-1 GATE -> {'PASS' if ok1 else 'FAIL'}")
        if not ok1:
            # ⛔ Distinct from a Stage 2 verdict: Stage 2 was never attempted, so it is neither
            # proven nor refuted. Saying "FAIL" alone would read as "the withdraw is broken".
            log(f"[{TAG}] ACCEPTANCE: FAIL — Stage 1 did not hold, so Stage 2 was NOT ATTEMPTED. "
                f"This is a verdict on the FIXTURE/Stage 1, NOT on the heal/withdraw path.")
            _ctx.set_manual_mode()
            return

        arm, pid, got, mon = self.s1_arm, self.s1_pid, self.s1_got, self.s1_mon

        # ---- PUBLISH ONLY WHAT PRODUCTION RETURNED. See the class docstring. ----
        self._hunted_counter_pids = set() if got is None else {got}
        log(f"[{TAG}] PUBLISHED _hunted_counter_pids="
            f"{sorted(format(p, '08X') for p in self._hunted_counter_pids)} "
            f"(from box_counter_pid's return value ONLY — never hand-set from the fixture)")

        before_party = party_map()
        boxed_before = get_pokemon_storage().contains_pokemon(mon)
        avatar = get_player_avatar()
        # PRE-RISK ATTRIBUTION (the `ch20room9` pattern): everything needed to attribute a silent
        # death, printed BEFORE the leg that can cause one.
        log(f"[{TAG}] PRE-RISK arm={arm} map={avatar.map_group_and_number} "
            f"pos={avatar.local_coordinates} fixture_pid={pid:08X} boxed_before={boxed_before} "
            f"party_before={before_party}")

        step(5, "the REAL heal — heal_in_pokemon_center(FortreeCity), with its PC piggybacks")
        yield from heal_in_pokemon_center(PokemonCenter.FortreeCity)
        # ‼ storage AND party are cached per frame (`pokemon_storage.py:146-147`); a same-frame
        # read after the PC interaction sees the PRE-withdraw state. Yield before every check.
        yield from wait_for_n_frames(2)

        after_party = party_map()
        in_party = (pid, SLUG) in after_party
        still_boxed = get_pokemon_storage().contains_pokemon(mon)
        party_copy = next((m for m in get_party()
                           if m is not None and m.personality_value == pid
                           and m.species.name == "Slugma"), None)
        # ⛔ "MOVED" needs BOTH halves. In the party alone could be a copy; gone from the box
        # alone could be a release. Only the pair proves a move.
        moved = bool(party_copy is not None and in_party and not still_boxed)
        deposited = sorted(set(before_party) - set(after_party))
        log(f"[{TAG}] AFTER-HEAL in_party={in_party} still_boxed={still_boxed} moved={moved}")
        log(f"[{TAG}] DEPOSITED-TO-MAKE-ROOM {[before_party[k] for k in deposited]} "
            f"(pids {[format(p, '08X') for p, _s in deposited]}) — REPORTED, not graded. "
            f"‼ `find_dead_weight` picks this, and nothing stops it choosing a twin.")
        log(f"[{TAG}] PARTY-COUNT before={len(before_party)} after={len(after_party)} — ⛔ REPORTED "
            f"ONLY: a successful withdraw leaves every count unchanged, because the make-room "
            f"deposit cancels it. A count cannot tell success from doing nothing.")

        if arm == "A":
            # ---- ARM A: the user's bug, reproduced by production. Assert the POSITIVE facts of
            #      the failure, never merely the absence of a success.
            hunted_empty = self._hunted_counter_pids == set()
            a_ok = bool(hunted_empty and still_boxed and not in_party)
            log(f"[{TAG}] ARM-A RESULT hunted_counter_pids_empty={hunted_empty} "
                f"still_boxed={still_boxed} not_in_party={not in_party}")
            log(f"[{TAG}] ARM A is the DERAIL REPRODUCED: box_counter_pid returned None, so the "
                f"heal's counter-withdraw piggyback had nothing to act on and correctly — and "
                f"therefore INVISIBLY — did nothing. The counter is still in the box.")
            log(f"[{TAG}] ACCEPTANCE: {'PASS' if a_ok else 'FAIL'}")
            _ctx.set_manual_mode()
            return

        # ---- ARM B: steps 6 and 7. ----
        step(6, "the withdrawn Slugma must still know Rock Throw")
        knows = bool(party_copy is not None and party_copy.knows_move("Rock Throw"))
        log(f"[{TAG}] MOVESET-SURVIVED knows_rock_throw={knows}")

        step("7a", "lead selection — WITH a hunted_pids=None control, so the step CAN fail")
        # ⛔ WITHOUT THE CONTROL THIS STEP CANNOT FAIL. `lead_rank_key` sorts
        # (wonder_guard, can_attack, incoming, is_hunted_counter, -level) — `is_hunted_counter`
        # only breaks a tie on `incoming`. If the Slugma already had the best matchup it would
        # take slot 0 with an EMPTY hunted set, and the assertion would prove nothing about the
        # mechanism. So: run it once with no hunted set, record who leads, then run it for real.
        def lead_id():
            """(pid, species, label) of whoever is in slot 0 — identity, never the index itself."""
            head = get_party()[0]
            return (head.personality_value, head.species.name,
                    f"{head.species.name} L{head.level}")

        yield from _lead_best_matchup(["Flying"], hunted_pids=None)
        yield from wait_for_n_frames(2)
        c_pid, c_species, c_label = lead_id()
        yield from _lead_best_matchup(["Flying"], hunted_pids=self._hunted_counter_pids)
        yield from wait_for_n_frames(2)
        r_pid, r_species, r_label = lead_id()
        lead_is_counter = bool(r_pid == pid and r_species == SLUG)
        control_was_counter = bool(c_pid == pid and c_species == SLUG)
        lead_decisive = bool(not control_was_counter and lead_is_counter)
        log(f"[{TAG}] LEAD control(hunted=None)={c_pid:08X} ({c_label}) ; "
            f"real(hunted={{fixture}})={r_pid:08X} ({r_label}) ; "
            f"lead_is_counter={lead_is_counter}")
        log(f"[{TAG}] LEAD-MECHANISM-DECISIVE={lead_decisive} — REPORTED. False means the Slugma "
            f"would have led anyway, so this run does not attribute slot 0 to hunted_pids.")

        step("7b", "a SECOND full heal — the withdraw must NO-OP, and for the RIGHT reason")
        pids_before_h2 = set(party_map())
        yield from heal_in_pokemon_center(PokemonCenter.FortreeCity)
        yield from wait_for_n_frames(2)
        pids_after_h2 = set(party_map())
        unchanged = pids_after_h2 == pids_before_h2
        # ⛔ A NO-OP HAS INNOCENT CAUSES — an unreadable box (`box_views` swallows every error into
        # `([], [])`), or a full party with nothing safe to deposit. `_hunted_counter_pids` is
        # never cleared, so `counter_withdraw_outcome` still says "withdraw" and the console looks
        # identical. ⇒ ATTRIBUTE it: the mon is in the PARTY, and `find_in_box` says the BOX no
        # longer has it. That is "already collected", not "we failed to look".
        still_in_party_h2 = (pid, SLUG) in pids_after_h2
        find_says = find_in_box(self._hunted_counter_pids)
        noop_attributed = bool(unchanged and still_in_party_h2 and find_says is None)
        log(f"[{TAG}] SECOND-HEAL party_unchanged={unchanged} still_in_party={still_in_party_h2} "
            f"find_in_box={'None' if find_says is None else find_says.species.name} "
            f"noop_attributed={noop_attributed}")

        ok = bool(moved and knows and lead_is_counter and noop_attributed)
        log(f"[{TAG}] RESULT arm=B moved={moved} knows_rock_throw={knows} "
            f"lead_is_counter={lead_is_counter} noop_attributed={noop_attributed} "
            f"(reported: lead_decisive={lead_decisive})")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if ok else 'FAIL'}")

        # ---- STEP 8 — REPORTED, NEVER GRADED, AND OFF BY DEFAULT. Everything above is already
        #      decided and printed; nothing below can change the verdict.
        if _os.environ.get("POKEBOT_BOXCOUNTER2_GYM", "0") == "1":
            step(8, "the gym leg — REPORTED ONLY, may whiteout, may derail to Manual (KI-71)")
            try:
                from modules.story.early_game import do_fortree_gym

                yield from do_fortree_gym()
                log(f"[{TAG}] GYM-LEG returned without raising — REPORTED ONLY. Whether the badge "
                    f"was won is NOT graded here and NOT inferred from this line.")
            except Exception as error:  # noqa: BLE001 — an ungraded observation must not rewrite
                # the verdict already printed above.
                log(f"[{TAG}] GYM-LEG raised {type(error).__name__}: {error} — REPORTED, the "
                    f"ACCEPTANCE above stands.")
        else:
            log(f"[{TAG}] STEP 8/8 — gym leg SKIPPED (set POKEBOT_BOXCOUNTER2_GYM=1 to run it). "
                f"It is reported-not-graded by design.")

        _ctx.set_manual_mode()
        return


class _Ki80Discriminated(Exception):
    """Raised FROM INSIDE the console proxy the instant a TERMINAL branch signature prints.

    ‼ THIS IS THE WHOLE REASON THE DRIVER IS SAFE, and it exists because the obvious design was
    REFUTED. `next(gen)` runs to the first `yield`, and `story_mode.py:1949`'s print is NOT the end
    of the arm: control continues to `:2087 yield from train_team(...)`, which calls
    `early_game.py:2003 set_swap_train(True)` and — via `_rotate_lead_safely` →
    `menuing.py:308` — `context.emulator.press_button("Start")` **before its first yield**.
    So "one next() per arm mutates nothing" was false on the ONE arm carrying the regression.
    Raising here unwinds `_prepare_for_fight` at `:1948`, before `:1961`, so `train_team` is never
    reached at all. ⛔ Do not "simplify" this into a plain flag — a flag cannot stop the generator.
    """


class Ki80LadderMode(BotMode):
    """KI-80 — `grass_is_fodder` is the SOLE gate on the counter-ladder, PROVEN BY DRIVING.

    ‼ WHAT IS UNDER TEST, EXACTLY. `story_mode.py:1899`:
        `grass_is_fodder = ("grass" not in cfg) or (wild_max is not None and wild_max + 8 < team_max)`
    and `:1901` makes that one boolean the sole gate on `_boss_plan_is_hopeless` (`:1907`) AND
    `_counter_ladder` (`:1914`). One flag carries two unrelated meanings — *"this boss has no
    patch"* and *"this boss's patch is far below the team"* — so **giving a boss a training area
    silently deletes its KI-23 counter machinery**, behind a healthy-looking
    `"training harder before re-attempting"` line. The SUBJECT is the GATE: which branch production
    takes. Nothing else.

    ⛔ THIS IS NOT `repro_boss_grass_gate.py` (suite #24). That gate is STRUCTURAL — it reads the
    AST and FORBIDS a `grass` key on the at-risk bosses while the coupling stands. It proves the
    edit is not made. This driver proves what would HAPPEN if it were. Both are needed; neither
    replaces the other. ⇒ this driver builds its cfgs IN THE DRIVER and edits no production file,
    so the two never fight.

    ‼‼ THREE ARMS, NOT TWO — and the third is what makes the result mean anything.
        NOGRASS       no `grass` key            -> grass_is_fodder TRUE  (1st disjunct) -> LADDER
        GRASS_FODDER  Route 102, wild_max 4     -> grass_is_fodder TRUE  (2nd disjunct) -> LADDER
        GRASS_STRONG  Route 119, wild_max 27    -> grass_is_fodder FALSE                -> ESCALATION
    A two-arm A/B would only show "a `grass` key removes the ladder" and could not distinguish the
    key's PRESENCE from the level ARITHMETIC. GRASS_FODDER shows a patch that IS fodder KEEPS the
    machinery — so the discriminator is the arithmetic, which is the actual defect.
    ‼ ARMS 1 AND 2 ARE OBSERVATIONALLY IDENTICAL BY DESIGN. That sameness IS the finding. It also
    means the driver cannot OBSERVE that arm 2 carried a key — it asserts the cfg it passed, and
    says so rather than implying more.

    ⛔⛔ THE FIXTURE, AND WHY BOTH PREVIOUSLY-NAMED SAVES ARE UNUSABLE.
    ANCHOR: `saves/batch2_run04_wedge.ss1` — measured NO_ANSWER, `team_max = 28`
    (Marshtomp/Swellow/Mightyena L28, Nincada L10).
      ⛔ NOT `fortree_gym_wedge.ss1` — its Castform's Powder Snow scores 160 >= 75, so
         `_boss_plan_is_hopeless` returns NOT hopeless (condition 7 fails) and the ladder can never
         fire from it.
      ⛔ NOT `ch13_fortree_door.ss1` — Blaziken L39 makes `27 + 8 = 35 < 39` TRUE, so
         `grass_is_fodder` is TRUE IN BOTH ARMS: the A/B is VACUOUS and would read as a REFUTATION
         of a true finding. (KI-80's condition 9. This save was NAMED as the fixture until a
         cold-start agent computed the discriminator on it.)
      ⚠ NOT `batch3_run03_wedge.ss1` — NO_ANSWER but `team_max = 35`, exactly ON the boundary
         (`35 < 35` false by one level). One level-up flips the experiment silently.
    ‼ NOT WINONA-ERA (badges 123). Fine for a DECISION-level A/B — the branch reads party levels,
    party moves, the grass map's encounter table and the seeded loss history, never a badge — but
    ⛔ DO NOT REPORT THIS AS A FAITHFUL WINONA SCENARIO. (And note `_counter_catch_message` ->
    `_counter_area_allowed` -> `is_map_reachable` DOES read badge flags, so W3's candidate list is
    badge-dependent even though the branch decision is not.)

    ⛔ `losses` IS SEEDED AT 8 — INSIDE 6..11, AND THAT BAND IS LOAD-BEARING AT BOTH ENDS.
    At 2-5 the ladder cannot fire whatever the grass key is (`PLATEAU_LOSS_THRESHOLD = 6`), so the
    A/B would show no difference. At 12+ `hard_plateau` goes True and `:1573` iterates an EMPTY
    TUPLE, so `hopeless` is True REGARDLESS OF THE PARTY — the right answer for a completely
    different reason, and the run would go green proving nothing about the no-answer path.

    WITNESSES — they must AGREE; disagreement is a FAIL, never a tie-break:
      W1 console proxy   — records every print reached through the module global, and TRIPS.
                           ⚠ NOT "every print": `_counter_area_allowed:902` and
                           `_log_story_event:3742` re-import `console` function-locally.
      W2 `_counter_ladder` spy — records ENTRY, returns False without hunting. ⛔ MUST be a
                           GENERATOR function: `:1914` is `yield from`, and a plain `def` returning
                           False raises TypeError, which reads as "the run errored".
      W3 the `BotModeError` — its message embeds the `losses` PRODUCTION used, so the seed is
                           checked against production's arithmetic, not the driver's belief.
      W4 delegating observer on `_boss_plan_is_hopeless` — calls the REAL method, records the
                           verdict, substitutes nothing. ⛔ Captures the bound method BEFORE
                           rebinding, or it recurses for ever.

    ⛔ STATED SCOPE LIMIT. W2 replaces the ladder's BODY, and every arm is cut off at its decision.
    This proves the gate is REACHED. It proves nothing about what the hunt then does — deliberately,
    because the hunt travels, and travel is risk this test does not need.

    Run:  PYTHONUTF8=1 py -3.12 story_harness.py batch2_run04_wedge.ss1 \\
              --driver ki80ladder --frames 2000
    ⛔⛔ KI-80 WAS DECOUPLED 2026-08-16, SO THE EXPECTATIONS BELOW ARE INVERTED FROM THEIR
    ORIGINAL FORM. Read them in that order or you will grade a healthy tree as broken:
      * bare command (the OLD, COUPLED expectation) -> ACCEPTANCE: **FAIL**, GRASS_STRONG reads
        `-> LADDER expected PLAIN_ESCALATION`. That FAIL is the PROOF the decoupling changed
        behaviour; it is the healthy answer.
      * POKEBOT_KI80_DECOUPLED=1 -> ACCEPTANCE: **PASS**, all three arms reach the LADDER.
      * POKEBOT_KI80_ARM4=1 (needs `fortree_gym_wedge.ss1`) -> PASS, OUTCOME=PLAIN_ESCALATION.
        Unchanged by the fix BY DESIGN — that invariance is the mirror-regression guard.
    ‼ Until 2026-08-16 these lines read "Expect (coupled, i.e. TODAY) ... ACCEPTANCE: PASS", which
    the fix falsified. A cold-start audit caught it. ⇒ **an `Expect:` line is a CLAIM about the
    code, and it goes stale the moment the code it describes changes — move it with the fix.**
    """

    @staticmethod
    def name() -> str:
        return "Ki80Ladder"

    def run(self):
        import ast as _ast
        import os as _os
        import pathlib as _pathlib
        import random as _random

        from modules.context import context as _ctx
        from modules.map import get_wild_encounters_for_map
        from modules.map_data import MapRSE, PokemonCenter
        from modules.modes.util import wait_for_n_frames
        from modules.player import get_player_avatar
        from modules.pokemon_party import get_party
        from modules.story import early_game as _eg
        from plugins.custom_modes import story_mode as _sm

        TAG = "ki80ladder"
        LOSSES = 8            # inside 6..11 — see the class docstring, BOTH ends matter
        SEED = 80             # `:1819` randint and `:1941` choice are unseeded in production
        FODDER_GAP = 8        # the `+ 8` in `:1899`, restated so the assertions below are readable

        # ⛔ STALE-EXPECTATION FIX 2026-08-26: this line read the env flag — but the flag is RETIRED
        # (zero hits in sandbox-pokebot/): the KI-80 decoupling was PROMOTED 2026-08-16 and is now
        # UNCONDITIONAL in production, so keying the expectation on an unset flag asserted the
        # COUPLED era forever. Found when the `#26` second-wind work re-ran this driver — its
        # FIRST run since the promotion: nothing in the standing suite runs it, so its Expect
        # lines rotted exactly as `#24-reprosweepratchet` predicts ("what the suite does not
        # run, rots"). Its own docstring rule — "an Expect: line is a CLAIM about the code;
        # move it with the fix" — was violated by the promotion commit. GRASS_STRONG's
        # coupled-era witnesses (W2 "must NOT reach the ladder", W4 "should short-circuit")
        # are era-gated below for the same reason.
        decoupled = True  # the SHIPPED behaviour; verified: the flag has 0 production hits
        # ⛔ ARM 4 IS A SEPARATE RUN ON A DIFFERENT SAVE, so arms 1-3's anti-vacuity check does not
        # apply to it — that check asks whether ROUTE119 flips `grass_is_fodder` for a NO_ANSWER
        # party, a question arm 4 never poses. It has its OWN two controls instead (A: the party
        # really HAS an answer; B: condition 9 INVERTED against VICTORY_ROAD_1F). Left ungated,
        # arm 4 fails on a check about arms it does not run — a FAIL that means nothing, which is
        # exactly how a reader learns to ignore a verdict.
        arm4 = _os.environ.get("POKEBOT_KI80_ARM4") == "1"
        fails: list[str] = []

        def bad(msg: str) -> None:
            fails.append(msg)
            log(f"[{TAG}] ‼ {msg}")

        yield from wait_for_n_frames(10)   # let the loaded state settle before reading party memory
        _random.seed(SEED)
        log(f"[{TAG}] seeded random with {SEED} (production `:1819`/`:1941` are unseeded; the "
            f"branch is unaffected but how far an arm WOULD run is not)")
        log(f"[{TAG}] EXPECTATION = {'ARM 4 (PLAIN_ESCALATION, before AND after the fix)' if arm4 else ('DECOUPLED (all three -> LADDER)' if decoupled else 'COUPLED (today: GRASS_STRONG -> ESCALATION)')} "
            f"(POKEBOT_KI80_DECOUPLED={_os.environ.get('POKEBOT_KI80_DECOUPLED', '<unset>')!r})")

        # ---- 1. MEASURE THE FIXTURE LIVE. Never trust the table in the docs. --------------------
        avatar = get_player_avatar()
        party = [m for m in get_party() if m is not None]
        team_max = max((m.level for m in party if not m.is_egg), default=0)
        log(f"[{TAG}] FIXTURE map={tuple(avatar.map_group_and_number)} "
            f"pos={tuple(avatar.local_coordinates)} party="
            f"{[(m.species.name, m.level) for m in party]} team_max={team_max}")

        def wild_land_max(map_enum):
            """Production's own reader, called exactly as `:1886-1890` calls it."""
            enc = get_wild_encounters_for_map(*map_enum.value)
            if enc is None or not enc.land_encounters:
                return None
            return max(e.max_level for e in enc.land_encounters)

        # ⛔ ROUTE119 is the patch winona_fight's OWN comment names (`story_mode.py:3531`:
        # "Route 119 is the Fortree-side band"). She has NO `grass` key today — that absence is
        # the ONLY reason her counter ladder still fires, which is the whole of KI-80.
        wild_strong = wild_land_max(MapRSE.ROUTE119)
        wild_fodder = wild_land_max(MapRSE.ROUTE102)   # a genuinely weak patch
        log(f"[{TAG}] MEASURED wild_max: ROUTE119={wild_strong} ROUTE102={wild_fodder} "
            f"(both read through production's `get_wild_encounters_for_map`)")

        # ---- 2. ANTI-VACUITY. ⛔ THE ARMS MUST PROVABLY DIFFER, COMPUTED HERE, NOT ASSUMED. ------
        # This block exists because this project has twice specified an A/B whose arms were
        # IDENTICAL, which would have read as a refutation of a true finding.
        if wild_strong is None or wild_fodder is None:
            # ⛔ NOT a pedantic None-check: `:1891` swallows this with a bare `except: pass`, leaving
            # wild_max None, which makes grass_is_fodder FALSE — so a missing table would turn
            # GRASS_FODDER silently into a SECOND GRASS_STRONG and the control would vanish.
            bad(f"a land-encounter table did not read (ROUTE119={wild_strong} ROUTE102={wild_fodder}) "
                f"— `:1891`'s bare except would leave wild_max None and COLLAPSE the arms")
        else:
            strong_flips = not (wild_strong + FODDER_GAP < team_max)   # grass_is_fodder -> False
            fodder_keeps = (wild_fodder + FODDER_GAP < team_max)       # grass_is_fodder -> True
            log(f"[{TAG}] DISCRIMINATOR ROUTE119: {wild_strong}+{FODDER_GAP}={wild_strong + FODDER_GAP} "
                f"vs team_max={team_max} -> grass_is_fodder flips to False? {strong_flips}")
            log(f"[{TAG}] DISCRIMINATOR ROUTE102: {wild_fodder}+{FODDER_GAP}={wild_fodder + FODDER_GAP} "
                f"vs team_max={team_max} -> stays fodder? {fodder_keeps}")
            if arm4:
                log(f"[{TAG}] (arms 1-3 anti-vacuity NOT graded — this is an ARM 4 run; arm 4 has "
                    f"its own CONTROL-A/CONTROL-B below)")
            else:
                if not strong_flips:
                    bad(f"THE A/B WOULD BE VACUOUS: ROUTE119 does not flip `grass_is_fodder` at "
                        f"team_max={team_max} (need team_max <= {wild_strong + FODDER_GAP}). "
                        f"This is KI-80 condition 9 — pick a fixture with a LOWER team_max.")
                if not fodder_keeps:
                    bad(f"THE CONTROL IS DEAD: ROUTE102 does not stay fodder at team_max={team_max} "
                        f"(need team_max > {wild_fodder + FODDER_GAP})")

        # ---- 3. THE cfg, CROSS-CHECKED AGAINST THE REAL LITERAL IN THE SOURCE AST. --------------
        # `winona_fight` is METHOD-LOCAL (`story_mode.py:3532`) and cannot be imported, so it is
        # replicated. ⛔ A replica that silently rots is worse than no replica — hence the check.
        base_cfg = {
            "name": "Winona",
            "keys": [MapRSE.FORTREE_CITY_GYM.value, MapRSE.FORTREE_CITY.value],
            "band": (29, 33),
            "ace_types": ("Dragon", "Flying"),
            "ace_level": 33,
            "heal": PokemonCenter.FortreeCity,   # `:1993` reads this on the GRASS_STRONG path
        }
        try:
            src = _pathlib.Path(_sm.__file__).read_text(encoding="utf-8-sig")
            literal = None
            for node in _ast.walk(_ast.parse(src)):
                if (isinstance(node, _ast.Assign) and len(node.targets) == 1
                        and isinstance(node.targets[0], _ast.Name)
                        and node.targets[0].id == "winona_fight"
                        and isinstance(node.value, _ast.Dict)):
                    literal = node.value
                    break
            if literal is None:
                bad("could not find the `winona_fight` literal in the source AST — the replica is "
                    "UNVERIFIED, so this run's cfg may not be production's")
            else:
                ast_keys = {k.value for k in literal.keys if isinstance(k, _ast.Constant)}
                unparsed = _ast.unparse(literal)
                if ast_keys != set(base_cfg):
                    bad(f"REPLICA DRIFT: winona_fight keys {sorted(ast_keys)} != replica "
                        f"{sorted(base_cfg)}")
                for needle in ("'band': (29, 33)", "'ace_types': ('Dragon', 'Flying')",
                               "'ace_level': 33"):
                    if needle not in unparsed:
                        bad(f"REPLICA DRIFT: {needle!r} not in the real literal")
                if "'grass'" in unparsed:
                    bad("winona_fight HAS a `grass` key in source — the regression this driver "
                        "measures has SHIPPED; `repro_boss_grass_gate.py` should have caught it")
                log(f"[{TAG}] AST CROSS-CHECK ok — replica matches `winona_fight` at "
                    f"{_pathlib.Path(_sm.__file__).name} (keys={sorted(ast_keys)}, no `grass` key)")
        except Exception as error:  # noqa: BLE001 — a failed cross-check must FAIL, never pass quietly
            bad(f"AST cross-check raised {type(error).__name__}: {error}")

        arms = [
            ("NOGRASS", dict(base_cfg), "LADDER"),
            ("GRASS_FODDER", {**base_cfg, "grass": (MapRSE.ROUTE102, (9, 2))}, "LADDER"),
            # ⛔ GRASS_STRONG RUNS LAST ON PURPOSE: it is the only arm that could leak state past
            # its decision if the tripwire ever missed, so it cannot contaminate the others.
            ("GRASS_STRONG", {**base_cfg, "grass": (MapRSE.ROUTE119, (21, 109))},
             "LADDER" if decoupled else "PLAIN_ESCALATION"),
        ]

        # ---- 4. THE WITNESSES. ------------------------------------------------------------------
        real_console = _sm.console
        ladder_calls: list[dict] = []
        hopeless_calls: list[dict] = []

        TRIPWIRES = (
            ("PLAIN_ESCALATION", "training harder before"),      # `:1949` — THE REGRESSION
            ("BOSS_TRAINING_MODE", "boss-training mode"),        # `:1927` — hopeless came back False
            ("ZERO_KO_FALLBACK", "boss attempts KO'd nothing"),  # `:1932` — the seed is wrong
        )

        class _Proxy:
            """Records, FORWARDS, then trips. Forwarding first keeps the line in the real log."""

            def __init__(self, real, sink):
                self._real, self._sink = real, sink

            def print(self, *a, **kw):
                text = " ".join(str(x) for x in a)
                self._sink.append(text)
                self._real.print(*a, **kw)
                for name, needle in TRIPWIRES:
                    if needle in text:
                        raise _Ki80Discriminated(name)

            def __getattr__(self, item):   # anything that is not `print` behaves as the real console
                return getattr(self._real, item)

        def ladder_spy(cfg, losses, needed):
            """⛔ A GENERATOR FUNCTION — `:1914` is `yield from`. The unreachable yield is what
            makes it one; without it `yield from False` raises TypeError."""
            ladder_calls.append({
                "losses": losses,
                "needed": list(needed),
                "cfg_has_grass": "grass" in cfg,
            })
            return False
            yield  # noqa: unreachable — REQUIRED. Do not delete.

        # ---- 5. DRIVE EACH ARM. -----------------------------------------------------------------
        def snapshot(mode):
            av = get_player_avatar()
            return {
                "map": tuple(av.map_group_and_number),
                "pos": tuple(av.local_coordinates),
                # ORDERED, and keyed on (pid, species) — a lead rotation reorders slots, and a
                # SET of pids is blind to that. KI-78: a Shedinja shares its Ninjask's PID.
                "party": [(m.personality_value, m.species.name, m.level)
                          for m in get_party() if m is not None],
                "swap_train": _eg.swap_train_active(),
                "message": getattr(_ctx, "message", None),
                "unreachable": sorted(str(x) for x in getattr(mode, "_training_unreachable", ()) or ()),
            }

        # ---- 3b. ARM 4 — THE MIRROR-REGRESSION ARM. Separate run: it needs a DIFFERENT save. ----
        # ⛔⛔ WHY THIS EXISTS. The naive KI-80 fix ("delete `grass_is_fodder and` from `:1901`")
        # hands `boss_mode = True` (`:1925`, the NOT-hopeless path) to every boss with a STRONG
        # patch AND a credible answer, and `:1937`'s `not boss_mode` then SUPPRESSES their plain
        # grass escalation. That is KI-23's mirror regression arriving through KI-80's fix.
        # ‼ ARMS 1-3 CANNOT SEE IT: they all use a NO_ANSWER party, so `hopeless` is True, the
        # ladder fires and `_prepare_for_fight` RETURNS at `:1924` — `:1925` is never reached.
        # ⛔ AND THE OBVIOUS FIXTURE IS VACUOUS — the third time this exact trap has been walked
        # into. `fortree_gym_wedge.ss1` is HAS_ANSWER (condition 7's inverse, which is what arm 4
        # wants) but its `team_max` is 39, and against ROUTE119's `wild_max` 27,
        # `27 + 8 = 35 < 39` is TRUE ⇒ `grass_is_fodder` is True ANYWAY and the "strong patch"
        # arm is silently a FODDER arm. ⇒ arm 4 needs a map whose land `wild_max >= team_max - 8`.
        # ✅ MEASURED 2026-08-16 across every `TRAINING_GRASS` map plus 9 candidates: the ONLY one
        # that clears 31 is VICTORY_ROAD_1F at 40 (Routes 121/123 peak at 28, ROUTE119 at 27).
        # ⚠ It is not a PLAUSIBLE training area for Winona — arm 4 is a DECISION-level test of the
        # branch, exactly as arms 1-3 are not a faithful Winona scenario. Say so; do not dress it up.
        if arm4:
            log(f"[{TAG}] ══ ARM 4 ONLY — the MIRROR-REGRESSION arm (POKEBOT_KI80_ARM4=1) ══")
            log(f"[{TAG}] ⛔ This arm needs a HAS_ANSWER save (e.g. fortree_gym_wedge.ss1), NOT the "
                f"NO_ANSWER anchor arms 1-3 use. Both controls below are measured, not assumed.")
            mode4 = _sm.StoryMode()
            key4 = MapRSE.FORTREE_CITY_GYM.value
            mode4._defeat_counts[key4] = LOSSES
            mode4._loss_ko_history[key4] = [(i, 1) for i in range(1, LOSSES + 1)]

            # CONTROL A — the party must genuinely HAVE an answer, or this arm tests nothing.
            # Calls the REAL predicate; no observer, no substitution.
            hopeless4, needed4 = mode4._boss_plan_is_hopeless(base_cfg)
            log(f"[{TAG}] ARM4 CONTROL-A `_boss_plan_is_hopeless` -> hopeless={hopeless4} "
                f"needed={needed4} (must be hopeless=False: arm 4 is the HAS-ANSWER case)")
            if hopeless4:
                bad("ARM4: this save is NO_ANSWER (hopeless=True), so it cannot exercise the "
                    "`:1925 boss_mode` path at all — use a HAS_ANSWER save such as "
                    "fortree_gym_wedge.ss1")

            # CONTROL B — condition 9, INVERTED, measured live. Without this the arm is vacuous.
            wild4 = wild_land_max(MapRSE.VICTORY_ROAD_1F)
            log(f"[{TAG}] ARM4 CONTROL-B VICTORY_ROAD_1F wild_max={wild4} vs team_max={team_max} "
                f"-> grass_is_fodder False? {wild4 is not None and not (wild4 + FODDER_GAP < team_max)}")
            if wild4 is None or (wild4 + FODDER_GAP < team_max):
                bad(f"ARM4 IS VACUOUS: VICTORY_ROAD_1F wild_max={wild4} does not make "
                    f"`grass_is_fodder` False at team_max={team_max} (need wild_max >= "
                    f"{team_max - FODDER_GAP}). ⛔ This is condition 9 again — pick a HIGHER map "
                    f"or a LOWER-level HAS_ANSWER save.")

            # ⚠ Only `cfg["grass"][0]` is read before the tripwire fires (`:1887`); the coordinate
            # pair is never touched on this path, so it is a placeholder AND IS LABELLED ONE.
            cfg4 = {**base_cfg, "grass": (MapRSE.VICTORY_ROAD_1F, (0, 0))}
            mode4._counter_ladder = ladder_spy
            ladder_calls.clear()
            sink4: list[str] = []
            before4 = snapshot(mode4)
            outcome4, detail4 = "UNSET", ""
            gen4 = mode4._prepare_for_fight(cfg4)
            _sm.console = _Proxy(real_console, sink4)
            try:
                next(gen4)
                outcome4 = "YIELDED_WITHOUT_DISCRIMINATING"
            except _Ki80Discriminated as trip:
                outcome4 = str(trip)
            except BotModeError as error:
                outcome4, detail4 = "LADDER", str(error)
            except StopIteration:
                outcome4 = "RETURNED_WITHOUT_DISCRIMINATING"
            except Exception as error:  # noqa: BLE001
                outcome4, detail4 = f"UNEXPECTED_{type(error).__name__}", str(error)
            finally:
                try:
                    gen4.close()
                except Exception as error:  # noqa: BLE001
                    log(f"[{TAG}] ARM4 gen.close() raised {type(error).__name__}: {error}")
                _sm.console = real_console
            drift4 = {k: (before4[k], snapshot(mode4)[k]) for k in before4
                      if before4[k] != snapshot(mode4)[k]}
            log(f"[{TAG}] ARM4 OUTCOME={outcome4} ladder_entered={bool(ladder_calls)} "
                f"INVARIANCE drift={drift4 if drift4 else 'none'}")

            # ‼ THE ASSERTION IS FIX-SHAPE-AGNOSTIC AND IS THE SAME BEFORE AND AFTER THE FIX.
            # A boss with a strong patch and a real answer must keep its plain grass escalation,
            # whatever shape the decoupling takes. That is the ONLY thing arm 4 grades.
            if outcome4 == "BOSS_TRAINING_MODE":
                bad("⛔⛔ ARM4: KI-23's MIRROR REGRESSION HAS LANDED — a boss with a STRONG patch "
                    "AND a credible answer entered BOSS-TRAINING MODE, so `:1937`'s plain grass "
                    "escalation is SUPPRESSED. This is exactly what decoupling `:1901` naively "
                    "does. The KI-80 fix must not set `boss_mode` from the not-hopeless path when "
                    "`grass_is_fodder` is False.")
            elif outcome4 != "PLAIN_ESCALATION":
                bad(f"ARM4: expected 'PLAIN_ESCALATION' (before AND after the fix), got "
                    f"{outcome4!r}")
            if ladder_calls:
                bad("ARM4: the counter ladder was entered, but this party HAS an answer — the "
                    "hopeless predicate is wrong or the seed is")
            if drift4:
                bad(f"ARM4: STATE CHANGED across the arm — {drift4}")
            log(f"[{TAG}] ACCEPTANCE: {'PASS' if not fails else 'FAIL'}"
                + ("" if not fails else f" — {len(fails)} problem(s): " + " | ".join(fails)))
            _ctx.set_manual_mode()
            return

        results = []
        for arm_name, cfg, expected in arms:
            mode = _sm.StoryMode()
            key = MapRSE.FORTREE_CITY_GYM.value
            mode._defeat_counts[key] = LOSSES
            mode._loss_ko_history[key] = [(i, 1) for i in range(1, LOSSES + 1)]
            # ⛔ PRE-CONSUME THE `#26-manualderails` SECOND WIND (2026-08-26). This driver's arms
            # measure the POST-WIND raise regime; without this line the wind intercepts at the
            # raise site and every LADDER expectation reads RETURNED_WITHOUT_DISCRIMINATING.
            # ‼ Predicted BY THE ARM DESIGN before the fix shipped, then CONFIRMED red, then fixed
            # — an `Expect:` line is a CLAIM about the code and moves WITH the code (:5886 rule).
            mode._second_winds.add(key)

            real_hopeless = mode._boss_plan_is_hopeless      # ⛔ BOUND, captured BEFORE rebinding

            def hopeless_observer(cfg_arg, _real=real_hopeless):
                verdict = _real(cfg_arg)          # the REAL predicate decides; this only watches
                hopeless_calls.append({"hopeless": bool(verdict[0]), "needed": list(verdict[1])})
                return verdict

            mode._boss_plan_is_hopeless = hopeless_observer
            mode._counter_ladder = ladder_spy

            ladder_calls.clear()
            hopeless_calls.clear()
            sink: list[str] = []
            before = snapshot(mode)

            outcome, detail = "UNSET", ""
            gen = mode._prepare_for_fight(cfg)
            _sm.console = _Proxy(real_console, sink)
            try:
                next(gen)
                outcome = "YIELDED_WITHOUT_DISCRIMINATING"
            except _Ki80Discriminated as trip:
                outcome = str(trip)
            except BotModeError as error:
                outcome, detail = "LADDER", str(error)
            except StopIteration:
                outcome = "RETURNED_WITHOUT_DISCRIMINATING"
            except Exception as error:  # noqa: BLE001 — reported as its own outcome, never as PASS
                outcome, detail = f"UNEXPECTED_{type(error).__name__}", str(error)
            finally:
                # ⛔ BOTH of these, always. close() runs train_team's `finally: set_swap_train(False)`
                # if the tripwire were ever missed; restoring console must not depend on it.
                try:
                    gen.close()
                except Exception as error:  # noqa: BLE001
                    log(f"[{TAG}] {arm_name}: gen.close() raised {type(error).__name__}: {error}")
                _sm.console = real_console

            after = snapshot(mode)
            drifted = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
            reached_ladder = bool(ladder_calls)
            results.append({
                "arm": arm_name, "outcome": outcome, "expected": expected,
                "ladder": reached_ladder, "hopeless": list(hopeless_calls),
                "drift": drifted, "detail": detail, "prints": len(sink),
            })

            log(f"[{TAG}] ── ARM {arm_name} (cfg keys={sorted(cfg)}) ──")
            log(f"[{TAG}]    OUTCOME={outcome} expected={expected}")
            log(f"[{TAG}]    W2 ladder_entered={reached_ladder} calls={ladder_calls}")
            log(f"[{TAG}]    W4 hopeless={hopeless_calls}")
            if detail:
                log(f"[{TAG}]    W3 raise={detail[:300]}")
            log(f"[{TAG}]    INVARIANCE drift={drifted if drifted else 'none'}")

            # --- per-arm grading: every witness must agree with every other one ---
            if expected == "LADDER":
                if outcome != "LADDER":
                    bad(f"{arm_name}: expected the counter-ladder branch, got {outcome!r}")
                if not reached_ladder:
                    bad(f"{arm_name}: W2 never saw `_counter_ladder` entered")
                if not hopeless_calls:
                    bad(f"{arm_name}: W4 never saw `_boss_plan_is_hopeless` called — the gate "
                        f"short-circuited before it")
                elif not hopeless_calls[-1]["hopeless"]:
                    bad(f"{arm_name}: `_boss_plan_is_hopeless` returned NOT hopeless — the fixture "
                        f"has a credible answer (condition 7), so the ladder cannot fire")
                if detail and f"{LOSSES} losses" not in detail:
                    # W3: production's OWN arithmetic, not the driver's belief about the seed.
                    bad(f"{arm_name}: the raise does not report {LOSSES} losses — production "
                        f"computed a different count from the seeded history: {detail[:200]!r}")
            else:
                if outcome != expected:
                    bad(f"{arm_name}: expected {expected!r}, got {outcome!r}")
                if reached_ladder:
                    bad(f"{arm_name}: W2 saw the ladder entered, but this arm must NOT reach it")
                if hopeless_calls:
                    bad(f"{arm_name}: W4 saw `_boss_plan_is_hopeless` called, but `grass_is_fodder` "
                        f"should have short-circuited before it")
            if drifted:
                bad(f"{arm_name}: STATE CHANGED across the arm — {drifted}. The tripwire should "
                    f"have stopped it before `train_team`.")

        # ---- 6. THE FINDING, STATED AS A COMPARISON. --------------------------------------------
        by_arm = {r["arm"]: r for r in results}
        nograss, fodder, strong = by_arm["NOGRASS"], by_arm["GRASS_FODDER"], by_arm["GRASS_STRONG"]
        log(f"[{TAG}] ══ MATRIX ══")
        for r in results:
            log(f"[{TAG}]   {r['arm']:<13} -> {r['outcome']:<22} ladder={r['ladder']} "
                f"(expected {r['expected']})")

        if not decoupled:
            # The defect, stated as the comparison that shows it. Both halves must hold: identical
            # parties, identical loss history, identical boss — ONLY the cfg's grass key differs.
            if nograss["ladder"] and fodder["ladder"] and not strong["ladder"]:
                log(f"[{TAG}] ✅ KI-80 REPRODUCED: same party, same seeded losses, same boss — the "
                    f"ONLY difference is the cfg's `grass` key. A FODDER patch KEEPS the counter "
                    f"machinery; the patch her own cfg comment names (Route 119, `story_mode.py:3531`, "
                    f"wild_max={wild_strong}) DELETES "
                    f"it, silently, behind `training harder before re-attempting`.")
            else:
                bad("KI-80 was NOT reproduced by the matrix above — read the per-arm lines before "
                    "touching `story_mode.py`; the CHECK is wrong at least as often as the subject")

        log(f"[{TAG}] ACCEPTANCE: {'PASS' if not fails else 'FAIL'}"
            + ("" if not fails else f" — {len(fails)} problem(s): " + " | ".join(fails)))
        _ctx.set_manual_mode()
        return


class Ch20DiveMode(BotMode):
    """‼ THE FIRST DRIVEN DIVE IN THIS PROJECT — KI-68 step 1, Mossdeep → SEAFLOOR_CAVERN_ENTRANCE.

    WHAT THIS MEASURES. `dive()` and `surface_from_dive()` both exist
    (`higher_level_actions.py:682` / `:705`) and have **no caller in `modules/story/` at all**.
    KI-68 says the planner will never emit a Dive waypoint — by design, because a dive is a MOVE
    on a deep-water tile, not a warp — so a chapter must drive the transition itself. This proves
    whether that actually works, and produces the coordinates a chapter would need.

    THE ROUTE IS MEASURED, NOT RECALLED (`probe_ch20_topology.py`):
        ROUTE128 (38,27) Deep Water  -> dive()              -> UNDERWATER_ROUTE128 (38,27)
        navigate 1 waypoint          -> (38,26) Water Door  -> UNDERWATER_SEAFLOOR_CAVERN (6,7)
        swim into the pool           -> surface_from_dive() -> SEAFLOOR_CAVERN_ENTRANCE (10,17)

    ‼ THE LAST LEG IS NOT IN THE MAP DATA. `UNDERWATER_SEAFLOOR_CAVERN` has no connection and no
    warp into the entrance; the edge is created at RUNTIME by
    `Underwater_SeafloorCavern_OnResume: setdivewarp MAP_SEAFLOOR_CAVERN_ENTRANCE, 10, 17`.
    No warp-graph or path scan can ever see it — which is why this has to be driven.

    ‼ KI-72 IS ARMED HERE, AND THIS DRIVER OBEYS ITS RULE. `calculate_path` has never heard of
    `Underwater Blocked Above` / `Seaweed No Surfacing`, so it will happily route you to a tile you
    cannot surface from. **The surfacing tile is therefore chosen explicitly and its `tile_type` is
    asserted before `surface_from_dive()` is called** — never left to the planner.

    ‼ AND IT PROVES THE WAY OUT IN THE SAME RUN. §Ch15 ended four floors underground, §Ch18 on an
    eleven-tile island, §Ch19 in a living room — all three "controllable". An underwater cavern is
    the best place yet to strand a run, so the acceptance requires the RETURN dive as well.

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20dive --frames 900000

    Emits: [ch20dive] RESULT legs=<n/6> at_entrance=<bool> got_out=<bool> can_continue=<bool>
    """

    #: Measured, not guessed — `probe_ch20_topology.py`. (38,26) is NOT deep water on the surface.
    DIVE_TILE = (38, 27)
    CAVERN_DOOR = (38, 26)          # UNDERWATER_ROUTE128, tile_type 'Water Door'
    POOL_TILE = (6, 6)              # inside UNDERWATER_SEAFLOOR_CAVERN's 18-tile open pool
    ENTRANCE_WATER = (10, 18)       # SEAFLOOR_CAVERN_ENTRANCE Deep Water — the way back out
    CAVERN_EXIT = (6, 7)            # UNDERWATER_SEAFLOOR_CAVERN 'Water South Arrow Warp' -> R128

    @staticmethod
    def name():
        return "Ch20Dive"

    def on_battle_started(self, encounter):
        # Same rule as every other driver here: a driver without a strategy hangs on a payout, and
        # the TRAINER strategy must be the production one (it never flees a trainer battle).
        # ‼ Underwater tiles are nearly all encounter tiles — `avoid_encounters` only minimises
        # exposure, it cannot remove it — so wild battles on this leg are expected, not surprising.
        from modules.battle_strategies import DefaultBattleStrategy

        if encounter is None:
            from plugins.custom_modes.story_mode import LevelUpTravelBattleStrategy

            return LevelUpTravelBattleStrategy()
        return DefaultBattleStrategy()

    @staticmethod
    def _where():
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar

        avatar = get_player_avatar()
        try:
            name = MapRSE(tuple(avatar.map_group_and_number)).name
        except Exception:  # noqa: BLE001 - an unknown map id is itself a finding, not a crash
            name = str(tuple(avatar.map_group_and_number))
        return name, avatar.local_coordinates

    @staticmethod
    def _underwater():
        from modules.player import AvatarFlags, get_player_avatar

        return AvatarFlags.Underwater in get_player_avatar().flags

    @staticmethod
    def _tile_type():
        from modules.map import get_map_data_for_current_position

        return get_map_data_for_current_position().tile_type

    def _inject_dive_fixture(self):
        """Heal the party and give ONE slot the Dive move. Sets `self.fixture_ok`.

        ‼ EXTRACTED FROM `run()` 2026-08-13 SO `--driver ch20room1` REUSES IT RATHER THAN
        COPYING IT. This session's headline lesson is that `probe_shoal_tide.py` had COPIED the
        pathfinder's model and so carried its bug — agreeing with production while both were
        wrong. A second copy of the cavern ingress would rot the same way. Behaviour is
        unchanged, and that was re-proven by re-running `--driver ch20dive` to `legs=6/6
        ACCEPTANCE: PASS` after the extraction.
        ‼ It keeps logging under `[ch20dive]` no matter who calls it, because it IS the ch20dive
        fixture; a log line should name the thing that ran, not the caller.
        """
        from modules.pokemon_party import get_party

        self.fixture_ok = False

        # ---- FIXTURE (documented; NOT a behaviour change) --------------------------------
        # Two variables are removed on purpose, because the question here is "does the ROUTE
        # work", not "can a battered party survive an ocean":
        #   (a) HP/status — `post_dive.ss1` arrives at 72% with ONE FAINTED mon, and
        #       `probe_anchor_inventory.py` already flags it "CANNOT SURVIVE A JOURNEY".
        #   (b) nobody in the party knows Dive (measured by `probe_dive_routing.py`), which is
        #       KI-63 — a real blocker for the CHAPTER, but not the thing under test here.
        # ‼ KI-68 sanctions exactly this: "inject Dive … near-zero risk — no deposit, no new data
        # row, no party change". So: heal in place, and give ONE existing slot the move.
        # ‼ THIS DOES NOT MAKE §Ch20 UNBLOCKED. Acquiring a Dive learner is still open work.
        try:
            from types import SimpleNamespace

            from modules.debug_utilities import debug_create_pokemon, debug_write_party
            from modules.pokemon import LearnedMove, get_move_by_name, get_species_by_name

            keepers, replaced = [], None
            for index, mon in enumerate(get_party()):
                if mon is None:
                    continue
                if index == 3:  # Skitty L17 — the party's least useful slot
                    replaced = f"{mon.species.name} L{mon.level}"
                    keepers.append(
                        debug_create_pokemon(
                            species=get_species_by_name("Wailmer"),
                            level=40,
                            nickname="DIVER",
                            moves=[
                                LearnedMove.create(get_move_by_name("Dive")),
                                LearnedMove.create(get_move_by_name("Surf")),
                                LearnedMove.create(get_move_by_name("Water Gun")),
                                LearnedMove.create(get_move_by_name("Rollout")),
                            ],
                        )
                    )
                    continue
                data = bytearray(mon.data)
                if len(data) >= 90:
                    data[86:88] = data[88:90]     # current HP := max HP
                    data[80:84] = b"\x00" * 4     # clear the status bitfield
                keepers.append(SimpleNamespace(data=bytes(data)))
            debug_write_party(keepers)
            log(f"[ch20dive] FIXTURE: healed the party and replaced slot 3 ({replaced}) with "
                f"Wailmer L40 knowing Dive+Surf. ‼ This measures the ROUTE, not the acquisition "
                f"of a Dive learner — KI-63 is still open.")
            self.fixture_ok = True
        except Exception as error:  # noqa: BLE001
            log(f"[ch20dive] FIXTURE FAILED ({type(error).__name__}: {str(error)[:200]}) — "
                f"aborting, because without Dive the run cannot measure anything.")
            return

        yield  # let the party write settle before anything reads it

    def _ingress(self):
        """LEGS 1-5: Mossdeep → ROUTE128 → dive → the cavern → SURFACE at the ENTRANCE.

        Sets `self.legs` (0-5), `self.notes`, `self.at_entrance` and `self.leg1_ok`. It does NOT
        print a RESULT/ACCEPTANCE line and does NOT drop to Manual — the caller owns the verdict,
        because `--driver ch20room1` continues past here and `--driver ch20dive` does not.

        ‼ `leg1_ok` is separate from `legs` on purpose: a LEG1 failure invalidates every later
        measurement (they are all measured FROM that tile), whereas a later failure is a finding.
        """
        from modules.map_data import MapRSE
        from modules.modes.util.higher_level_actions import dive, surface_from_dive
        from modules.modes.util.walking import navigate_to
        from modules.story.early_game import _navigate_riding_out

        legs, notes = 0, {}
        self.legs, self.notes, self.at_entrance, self.leg1_ok = 0, notes, False, False

        # ---- LEG 1: the long sea journey (PREDICTED to be the riskiest leg) --------------
        log(f"[ch20dive] LEG1 sailing {self._where()} -> ROUTE128 {self.DIVE_TILE}")
        try:
            yield from _navigate_riding_out(MapRSE.ROUTE128, self.DIVE_TILE)
        except Exception as error:  # noqa: BLE001
            log(f"[ch20dive] LEG1 FAILED {type(error).__name__}: {str(error)[:300]}")
        where = self._where()
        tile = self._tile_type()
        arrived = where == ("ROUTE128", self.DIVE_TILE)
        legs += 1 if arrived else 0
        notes["leg1"] = (where, tile, arrived)
        log(f"[ch20dive] LEG1 at={where} tile_type={tile!r} arrived={arrived}")
        if not arrived:
            self.legs, self.notes = legs, notes
            return

        # ---- LEG 2: THE DIVE ------------------------------------------------------------
        try:
            yield from dive()
            log("[ch20dive] LEG2 dive() returned")
        except Exception as error:  # noqa: BLE001
            log(f"[ch20dive] LEG2 dive() raised {type(error).__name__}: {str(error)[:300]}")
        where = self._where()
        under = self._underwater()
        ok2 = under and where == ("UNDERWATER_ROUTE128", self.DIVE_TILE)
        legs += 1 if ok2 else 0
        notes["leg2"] = (where, under, ok2)
        log(f"[ch20dive] LEG2 at={where} underwater={under} ok={ok2} "
            f"(‼ same (x,y) as the surface tile is the DECOMP-confirmed behaviour)")

        # ---- LEG 3: navigate to the Water Door; the warp should follow automatically -----
        if ok2:
            try:
                yield from navigate_to(MapRSE.UNDERWATER_ROUTE128, self.CAVERN_DOOR, False)
            except Exception as error:  # noqa: BLE001
                log(f"[ch20dive] LEG3 raised {type(error).__name__}: {str(error)[:300]}")
        where = self._where()
        ok3 = where[0] == "UNDERWATER_SEAFLOOR_CAVERN"
        legs += 1 if ok3 else 0
        notes["leg3"] = (where, ok3)
        log(f"[ch20dive] LEG3 at={where} in_cavern={ok3}")

        # ---- LEG 4: swim to a surfaceable POOL tile — ‼ KI-72, chosen explicitly ---------
        ok4 = False
        if ok3:
            try:
                yield from navigate_to(MapRSE.UNDERWATER_SEAFLOOR_CAVERN, self.POOL_TILE, False)
            except Exception as error:  # noqa: BLE001
                log(f"[ch20dive] LEG4 raised {type(error).__name__}: {str(error)[:300]}")
            where = self._where()
            tile = self._tile_type()
            # ‼ THE KI-72 GUARD. `surface_from_dive()` refuses on these two types, and the planner
            # cannot see them — so assert BEFORE spending the call, and say which tile failed.
            surfaceable = tile not in ("Underwater Blocked Above", "Seaweed No Surfacing")
            ok4 = where == ("UNDERWATER_SEAFLOOR_CAVERN", self.POOL_TILE) and surfaceable
            notes["leg4"] = (where, tile, surfaceable)
            log(f"[ch20dive] LEG4 at={where} tile_type={tile!r} surfaceable={surfaceable} ok={ok4}")
        legs += 1 if ok4 else 0

        # ---- LEG 5: SURFACE — the leg no static analysis can see -------------------------
        ok5 = False
        if ok4:
            try:
                yield from surface_from_dive()
                log("[ch20dive] LEG5 surface_from_dive() returned")
            except Exception as error:  # noqa: BLE001
                log(f"[ch20dive] LEG5 raised {type(error).__name__}: {str(error)[:300]}")
            where = self._where()
            ok5 = where[0] == "SEAFLOOR_CAVERN_ENTRANCE"
            notes["leg5"] = (where, self._underwater(), ok5)
            log(f"[ch20dive] LEG5 at={where} underwater={self._underwater()} "
                f"at_entrance={ok5} (predicted (10,17) from the RUNTIME setdivewarp)")
        legs += 1 if ok5 else 0
        self.legs, self.notes, self.at_entrance, self.leg1_ok = legs, notes, ok5, True

    def run(self):
        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.modes.util.higher_level_actions import dive, surface_from_dive
        from modules.modes.util.walking import navigate_to
        from modules.player import get_player_avatar
        from modules.story.early_game import wait_until_truly_controllable

        yield from wait_until_truly_controllable()

        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            _ctx.set_manual_mode()
            return

        yield from self._ingress()
        legs, notes, at_entrance = self.legs, self.notes, self.at_entrance
        if not self.leg1_ok:
            log("[ch20dive] ‼ STOPPING — every later leg is measured FROM this tile, so "
                "continuing would measure the wrong thing.")
            log(f"[ch20dive] RESULT legs={legs}/6 at_entrance=False got_out=False "
                f"can_continue=False detail={notes}")
            log("[ch20dive] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()
            return

        # ---- LEG 6: ‼ PROVE THE WAY OUT, IN THE SAME RUN ---------------------------------
        # KI-56's rule, and this project's most re-learned lesson. An underwater cavern is the
        # best place yet to strand a run, so "we got in" is not the result — "we can leave" is.
        # ‼ MEASURED ON RUN 1, AND MY FIRST ASSERTION WAS WRONG BY ONE HOP. Diving at the
        # entrance's (10,18) does NOT return you to ROUTE128 — it drops you back into
        # UNDERWATER_SEAFLOOR_CAVERN at (6,5), i.e. the POOL. The static warp table reads
        # "(10,18) -> UNDERWATER_ROUTE128 (38,26)", but the live dive warp is the runtime one
        # again. So the way out is THREE hops, and the last two are ordinary navigation:
        #     (10,18) dive -> POOL (6,5) -> navigate (6,7) 'Water South Arrow Warp'
        #                                -> UNDERWATER_ROUTE128 (38,26)
        got_out = False
        if at_entrance:
            try:
                yield from navigate_to(MapRSE.SEAFLOOR_CAVERN_ENTRANCE, self.ENTRANCE_WATER)
                log(f"[ch20dive] LEG6 on the exit water tile: {self._where()} "
                    f"tile_type={self._tile_type()!r}")
                yield from dive()
                log(f"[ch20dive] LEG6 dived back down to {self._where()}")
                yield from navigate_to(MapRSE.UNDERWATER_SEAFLOOR_CAVERN, self.CAVERN_EXIT, False)
            except Exception as error:  # noqa: BLE001
                log(f"[ch20dive] LEG6 raised {type(error).__name__}: {str(error)[:300]}")
            where = self._where()
            got_out = self._underwater() and where[0] == "UNDERWATER_ROUTE128"
            notes["leg6"] = (where, got_out)
            log(f"[ch20dive] LEG6 at={where} got_out={got_out}")
        legs += 1 if got_out else 0

        # ---- CAN-CONTINUE ----------------------------------------------------------------
        # ‼ THE TARGET IS DERIVED FROM A REAL PATH ON THE MAP WE ARE ACTUALLY ON. Run 1 used the
        # hardcoded ROUTE128 tile (38,27) regardless of map and hit `IndexError: list index out of
        # range` — (38,27) does not exist on a 14x9 underwater map. That is EXACTLY the mistake I
        # wrote a prevention rule against in `--driver roster` this morning ("walk to a tile on the
        # real path, not a coordinate I picked from memory") and then made anyway a few hours later.
        # ‼ THE REAL NON-STRAND PROOF IS SURFACING BACK INTO THE OPEN OCEAN, not shuffling a tile.
        # Run 2 ended on UNDERWATER_ROUTE128 (38,27) and my check asked it to walk to (38,27) —
        # the tile it was already on — so the path came back empty and it reported `moved=False`
        # over a run that was in perfect shape. Third correction to this same block; the ROUTE has
        # been right since run 1. So: surface, land back on ROUTE128, and take a real step there.
        # That is the strongest end state available — the bot is back in the water it started from
        # and can sail anywhere.
        surfaced, moved = False, False
        before = get_player_avatar().local_coordinates
        try:
            if self._underwater():
                tile = self._tile_type()
                if tile in ("Underwater Blocked Above", "Seaweed No Surfacing"):
                    log(f"[ch20dive] CAN-CONTINUE ‼ KI-72: cannot surface from {tile!r}.")
                else:
                    yield from surface_from_dive()
                    surfaced = self._where()[0] == "ROUTE128"
                    log(f"[ch20dive] CAN-CONTINUE surfaced to {self._where()} ok={surfaced}")
            if surfaced:
                yield from navigate_to(MapRSE.ROUTE128, (37, 27))
                moved = get_player_avatar().local_coordinates != before
        except Exception as error:  # noqa: BLE001
            log(f"[ch20dive] CAN-CONTINUE raised {type(error).__name__}: {str(error)[:200]}")
        can_continue = surfaced and moved and _ctx.bot_mode != "Manual"
        log(f"[ch20dive] CAN-CONTINUE surfaced={surfaced} moved={moved} {before}->"
            f"{get_player_avatar().local_coordinates} at={self._where()} "
            f"manual={_ctx.bot_mode == 'Manual'}")

        log(f"[ch20dive] RESULT legs={legs}/6 at_entrance={at_entrance} got_out={got_out} "
            f"can_continue={can_continue} detail={notes}")
        log(f"[ch20dive] ACCEPTANCE: "
            f"{'PASS' if (legs == 6 and at_entrance and got_out and can_continue) else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class Ch20Room1Mode(Ch20DiveMode):
    """§Ch20 increment 1 — get INSIDE the cavern, MEASURE Room 1 with LIVE objects, then solve it.

    ‼ WHY THIS EXISTS, AND WHAT IT CONVERTS. `probe_ch20_interior.py` built the cavern's Area
    Atlas from OUTSIDE (the avatar was in Mossdeep), and it says so in its own output at
    section 3b: with no cavern objects loaded, `is_tile_accessible` blocks every object-template
    tile, so **every NO-PATH it reported is a LOWER BOUND, not a map fact**. The handoff's next
    action is therefore a MEASUREMENT, not more planning. This driver takes it from inside.

    THE A/B THAT IS THE POINT OF THE RUN (measured on the SAME tiles, live objects both times):
        BEFORE  calculate_path(arrival -> ROOM1 (11,11))   PREDICTED: NO-PATH (corridor sealed)
        AFTER   the same call, post Rock Smash + one push  PREDICTED: OK
    A one-armed "it worked" would prove nothing here — the corridor could have been open all
    along and the whole boulder story wrong.

    ‼ THE ROOM 1 SEQUENCE IS ARBITRATED, NOT CHOSEN. Two sources disagreed:
      * upstream `puzzle_solver.py:370-376` (shipped, reportedly working for Emerald) pushes the
        `(5,11)` boulder **DOWN** from `(5,10)`;
      * our own build spec (`ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`)
        claims an *exhaustive* search proves the only route needs it pushed **NORTH**.
    A decomp + our-own-ROM arbitration (2026-08-13) ruled **UPSTREAM CORRECT**: both directions
    are legal (`(5,10)` and `(5,12)` are both `collision=0 elevation=3 'Cave'`), so the spec's
    *uniqueness* claim is false — its search was not exhaustive. South is what ships, and it
    needs no staging detour. ⇒ **Treat that spec's Room 1 paragraph as unreliable, and do not
    trust its Room 2 / Room 8 "exhaustive" sequences either until each is arbitrated the same
    way.** The object table it is driven from (decomp + our ROM, agreeing):
        local_id 1  PUSHABLE_BOULDER  (5,11)   FLAG_TEMP_11
        local_id 2  PUSHABLE_BOULDER  (12,11)  FLAG_TEMP_12
        local_id 3  BREAKABLE_ROCK    (5,10)   FLAG_TEMP_13
        local_id 4  AQUA_MEMBER_M     (8,6)    Grunt1   — on the row-7 walk, sight 2, rotates
        local_id 5  AQUA_MEMBER_M     (15,10)  Grunt2   — off-path

    ‼ BOTH PUSHES GO THROUGH `strength_push`, NOT `walk_one_tile`. Upstream's second push is a
    bare `walk_one_tile("Right")`, which is UNBOUNDED by its own docstring and judges nothing.
    `strength_push` is this project's bounded, world-judged primitive: it pins the boulder by
    `local_id` (a push moves the PLAYER onto the vacated tile, so "is the old tile empty" reads
    false on a push that worked) and requires the boulder to be on the DESTINATION.

    ‼ PUZZLE STATE RESETS ON MAP RE-ENTRY (`FLAG_TEMP_*`), so nothing here may cache "solved" —
    but `FLAG_SYS_USE_STRENGTH` persists, which is why only the FIRST push pays for the prompt.

    ‼ THE STANDING RULE: "and the bot can continue". Three chapters have shipped stranded, so
    the acceptance takes a REAL step in Room 2, onto a neighbour derived from the tile the run
    actually reached — never a coordinate picked from memory (that mistake has been made in this
    file twice, and the second time was hours after its own prevention rule was written).

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room1 --frames 1500000

    Emits: [ch20room1] RESULT in_room1=<b> ab_before=<b> ab_after=<b> in_room2=<b> can_continue=<b>
    """

    #: ‼ CLASS-LEVEL DEFAULT ON PURPOSE. `_can_continue_step` is the only writer of `moved`, so
    #: any caller that skips it (a failure branch) would read an unset attribute and crash. The
    #: run-level code ALSO sets it explicitly — this is the backstop for the next subclass, not
    #: the fix. A default of False is safe because "we never took a step" and "the step failed"
    #: mean the same thing to every verdict here.
    moved = False

    ROOM1_WARP_UP = (10, 1)       # SEAFLOOR_CAVERN_ENTRANCE — the north exit into ROOM1
    ROCK_APPROACH = (4, 10)       # face Right at BREAKABLE_ROCK (5,10)
    BOULDER1_APPROACH = (5, 10)   # face Down;  boulder local_id 1 (5,11) -> (5,12)
    BOULDER2_APPROACH = (11, 11)  # face Right; boulder local_id 2 (12,11) -> (13,11)
    ROOM2_DOOR = (6, 2)           # 'Non-Animated Door' -> SEAFLOOR_CAVERN_ROOM2
    #: The A/B target: the far (east) end of the row-11 corridor. Sealed until the rock is
    #: smashed AND boulder 1 is out of (5,11), because (6,10) and (6,12) are both collision=1.
    CORRIDOR_PROBE = (11, 11)

    @staticmethod
    def name():
        return "Ch20Room1"

    @staticmethod
    def _dump_objects(tag: str, map_enum) -> dict:
        """Every LIVE object BELONGING TO `map_enum`, by identity. Returns {local_id: (x,y)}.

        ‼ This is the whole reason the run has to be INSIDE the room: `get_map_objects()` reads
        `gObjectEvents`, which only holds what the game has actually loaded.

        ‼ AND IT IS FILTERED BY MAP, NOT JUST BY `local_id`. `get_map_objects()` returns every
        ACTIVE slot — which includes the player and can include objects belonging to an adjacent
        or previous map — and `local_id` is only unique WITHIN a map. An unfiltered dict would let
        a stranger's `local_id=3` answer "is the rock still there?", which is this session's own
        headline failure shape: an instrument that does not measure what it claims. Every line is
        still PRINTED, filtered or not, so the raw reading survives the judgement."""
        from modules.map import get_map_objects

        found = {}
        try:
            objects = get_map_objects()
        except Exception as error:  # noqa: BLE001 - a failed read is a finding, not a crash
            log(f"[ch20room1] {tag} OBJECT DUMP FAILED {type(error).__name__}: {str(error)[:200]}")
            return found
        wanted = map_enum.value if hasattr(map_enum, "value") else tuple(map_enum)
        log(f"[ch20room1] {tag} LIVE OBJECTS n={len(objects)} (counting only map={wanted})")
        for obj in objects:
            try:
                owner = tuple(obj.map_group_and_number)
                mine = owner == tuple(wanted) and "isPlayer" not in obj.flags
                if mine:
                    found[obj.local_id] = tuple(obj.current_coords)
                log(f"[ch20room1] {tag}   {'*' if mine else ' '} local_id={obj.local_id:<3} "
                    f"gfx={obj.graphics_id:<4} at={tuple(obj.current_coords)} "
                    f"initial={tuple(obj.initial_coords)} map={owner} "
                    f"facing={obj.facing_direction}")
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room1] {tag}   <unreadable object> {type(error).__name__}: "
                    f"{str(error)[:120]}")
        return found

    @staticmethod
    def _path_ok(map_enum, source, destination) -> tuple[bool, str]:
        """Does a REAL `calculate_path` exist from `source` to `destination` RIGHT NOW?

        ‼ KI-60's guard first: an unwalkable SOURCE makes any answer meaningless, so the source
        tile's collision is reported alongside the verdict rather than assumed."""
        from modules.map import get_map_data
        from modules.map_path import calculate_path

        try:
            collision = get_map_data(map_enum, source).collision
        except Exception as error:  # noqa: BLE001
            collision = f"<unreadable {type(error).__name__}>"
        try:
            path = calculate_path((map_enum, source), (map_enum, destination))
            return True, f"OK len={len(path)} (source collision={collision})"
        except Exception as error:  # noqa: BLE001
            return False, (f"{type(error).__name__}: {str(error)[:140]} "
                           f"(source collision={collision})")

    def _enter_room1(self):
        """ENTRANCE -> ROOM1 through the north warp. Sets `self.in_room1`, `self.r1_arrival`."""
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out

        # The entrance pool needs Surf; `_navigate_riding_out` owns that transition, and the north
        # tile is a warp, so the map change is expected to happen DURING the walk. A raise here is
        # therefore not automatically a failure - the position is what decides.
        try:
            yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ENTRANCE, self.ROOM1_WARP_UP)
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room1] LEGA raised {type(error).__name__}: {str(error)[:300]} "
                f"(a warp firing mid-walk can look like this - the position below decides)")
        where = self._where()
        self.in_room1 = where[0] == "SEAFLOOR_CAVERN_ROOM1"
        self.r1_arrival = get_player_avatar().local_coordinates
        log(f"[ch20room1] LEGA at={where} in_room1={self.in_room1} "
            f"(PREDICTED SEAFLOOR_CAVERN_ROOM1 (5,18))")

    def _solve_room1(self):
        """MEASURE the live room, then Rock Smash + two pushes, then the (6,2) door into ROOM2.

        Sets `self.r1`, a dict of every graded sub-result.

        ‼ THIS IS A METHOD SO THE ROOM 2 DRIVER CAN RE-RUN IT. Puzzle state is `FLAG_TEMP_*` and
        **resets on every map load**, so there is no such thing as arriving in Room 2 with Room 1
        already solved - every deeper drive pays for this room again. (`FLAG_SYS_USE_STRENGTH` is
        the exception: it is never cleared, so only the first push of a SAVE pays for the prompt.)
        """
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out, _smash_rock, strength_push

        room1 = MapRSE.SEAFLOOR_CAVERN_ROOM1
        self.r1 = {}

        # ---- ‼ FAULT INJECTION HOOK: `POKEBOT_CH20_FAULT=room1` ---------------------------
        # The happy path cannot exercise an error path, and this driver's whole failure branch
        # (smash raises / a push raises => never reach ROOM2) had NEVER been executed — three
        # green runs all went `pushed2=True in_room2=True`. An adversarial review found an
        # `AttributeError` waiting on exactly that branch, which would have crashed the run
        # BEFORE it could print ACCEPTANCE or drop to Manual — the "never silently derail" rule,
        # broken on the one path nobody had run.
        # ‼ THIS IS A PERMANENT, DOCUMENTED HOOK, NOT A TEMPORARY EDIT. Editing the file to
        # inject a fault and editing it back is how this project detonated an unrelated stash
        # once already; a gated hook is reproducible, greppable and cannot be left half-reverted.
        # It is OFF unless the env var is set, so it cannot affect a normal run.
        import os as _os

        if _os.environ.get("POKEBOT_CH20_FAULT") == "room1":
            log("[ch20room1] ‼ FAULT INJECTION ACTIVE (POKEBOT_CH20_FAULT=room1) — forcing the "
                "Room 1 solve to fail so the FAILURE branch is exercised. A run in this mode "
                "MUST still print a clean `ACCEPTANCE: FAIL` and drop to Manual.")
            self.r1.update({"objects_before": {}, "ab": {}, "ab_before": None, "ab_after": None,
                            "smashed": False, "pushed1": False, "pushed2": False,
                            "in_room2": False, "legC": self._where(), "fault_injected": True})
            return
            yield  # noqa: unreachable - keeps this a generator on every path

        # ---- MEASURE-A: the live truth, BEFORE anything is touched ------------------------
        arrival = self.r1_arrival
        self.r1["objects_before"] = self._dump_objects("BEFORE", room1)
        ab_before, before_detail = self._path_ok(room1, arrival, self.CORRIDOR_PROBE)
        log(f"[ch20room1] A/B BEFORE {arrival} -> {self.CORRIDOR_PROBE}: {before_detail}")
        log(f"[ch20room1] A/B BEFORE path_exists={ab_before} "
            f"(PREDICTED False - the corridor is sealed by rock (5,10) + boulder (5,11))")

        # ---- the arbitrated solve ---------------------------------------------------------
        smashed = pushed1 = pushed2 = False
        try:
            yield from _smash_rock(room1, self.ROCK_APPROACH, "Right")
            smashed = True
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room1] SMASH raised {type(error).__name__}: {str(error)[:300]}")
        after_smash = self._dump_objects("AFTER-SMASH", room1)
        log(f"[ch20room1] SMASH ok={smashed} rock local_id=3 present="
            f"{3 in after_smash} (PREDICTED absent)")

        if smashed:
            try:
                yield from strength_push(room1, self.BOULDER1_APPROACH, "Down")
                pushed1 = True
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room1] PUSH1 raised {type(error).__name__}: {str(error)[:300]}")
        after_push1 = self._dump_objects("AFTER-PUSH1", room1)
        log(f"[ch20room1] PUSH1 ok={pushed1} boulder local_id=1 at={after_push1.get(1)} "
            f"(PREDICTED (5,12))")

        # ---- MEASURE-B: the OTHER arm of the A/B, same call, same target ------------------
        here = get_player_avatar().local_coordinates
        ab_after, after_detail = self._path_ok(room1, here, self.CORRIDOR_PROBE)
        log(f"[ch20room1] A/B AFTER  {here} -> {self.CORRIDOR_PROBE}: {after_detail}")
        log(f"[ch20room1] A/B AFTER  path_exists={ab_after} (PREDICTED True)")

        if pushed1:
            try:
                yield from strength_push(room1, self.BOULDER2_APPROACH, "Right")
                pushed2 = True
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room1] PUSH2 raised {type(error).__name__}: {str(error)[:300]}")
        after_push2 = self._dump_objects("AFTER-PUSH2", room1)
        log(f"[ch20room1] PUSH2 ok={pushed2} boulder local_id=2 at={after_push2.get(2)} "
            f"(PREDICTED (13,11))")

        # ---- ROOM1 -> ROOM2 through the (6,2) door ---------------------------------------
        # ‼ The row-7 walk passes Grunt1 at (8,6), sight radius 2 and rotating, so a trainer
        # battle here is PREDICTED, not a surprise. `_navigate_riding_out` rides it out.
        if pushed2:
            try:
                yield from _navigate_riding_out(room1, self.ROOM2_DOOR)
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room1] LEGC raised {type(error).__name__}: {str(error)[:300]} "
                    f"(the door warp firing mid-walk can look like this)")
        where = self._where()
        in_room2 = where[0] == "SEAFLOOR_CAVERN_ROOM2"
        log(f"[ch20room1] LEGC at={where} in_room2={in_room2} "
            f"(PREDICTED SEAFLOOR_CAVERN_ROOM2 (10,7))")

        self.r1.update({
            "ab": {"before": (arrival, ab_before, before_detail),
                   "after": (here, ab_after, after_detail)},
            "ab_before": ab_before, "ab_after": ab_after,
            "smashed": smashed, "pushed1": pushed1, "pushed2": pushed2,
            "in_room2": in_room2, "legC": where,
        })

    def _can_continue_step(self, map_enum, tag: str):
        """Take a REAL step onto a live-derived, NON-WARP neighbour. Sets `self.moved`.

        ‼ Never a remembered coordinate - that mistake was made twice in this file, the second
        time hours after its own prevention rule was written. Warp and door tiles are excluded so
        that "it moved" cannot be satisfied by falling back out of the room."""
        from modules.map import get_map_data
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out

        self.moved = False
        start = get_player_avatar().local_coordinates
        step_target = None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            candidate = (start[0] + dx, start[1] + dy)
            try:
                tile = get_map_data(map_enum, candidate)
            except Exception:  # noqa: BLE001 - off-map candidates are simply not candidates
                continue
            kind = str(tile.tile_type)
            # ‼ "Warp"/"Door" alone is NOT the full set of map transitions: `Ladder`,
            # `Escalator Up` and `Escalator Down` (modules/map.py) contain neither substring and
            # would let a "we can still move" check be satisfied by LEAVING the room — the exact
            # thing the check exists to rule out. Flagged by adversarial review as a latent gap;
            # closed here rather than left to depend on which maps happen to have one.
            if tile.collision == 0 and not any(
                word in kind for word in ("Warp", "Door", "Ladder", "Escalator")
            ):
                step_target = candidate
                log(f"[{tag}] CAN-CONTINUE stepping {start} -> {candidate} tile_type={kind!r}")
                break
        if step_target is None:
            log(f"[{tag}] CAN-CONTINUE ‼ no non-warp walkable neighbour of {start} - "
                f"that is itself the finding.")
        else:
            try:
                yield from _navigate_riding_out(map_enum, step_target)
                self.moved = get_player_avatar().local_coordinates != start
            except Exception as error:  # noqa: BLE001
                log(f"[{tag}] CAN-CONTINUE raised {type(error).__name__}: {str(error)[:200]}")
        log(f"[{tag}] CAN-CONTINUE moved={self.moved} {start}->"
            f"{get_player_avatar().local_coordinates}")

    def run(self):
        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.story.early_game import wait_until_truly_controllable

        notes = {}
        yield from wait_until_truly_controllable()

        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            log("[ch20room1] RESULT in_room1=False ab_before=None ab_after=None in_room2=False "
                "can_continue=False detail=fixture-failed")
            log("[ch20room1] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()
            return

        # ---- INGRESS: the PROVEN ch20dive legs 1-5, reused rather than copied --------------
        yield from self._ingress()
        notes["ingress"] = self.notes
        if not (self.leg1_ok and self.at_entrance):
            log(f"[ch20room1] ‼ STOPPING - the ingress did not surface in the cavern "
                f"(legs={self.legs}/5 at_entrance={self.at_entrance}). Every measurement below "
                f"is taken from INSIDE, so continuing would measure nothing.")
            log(f"[ch20room1] RESULT in_room1=False ab_before=None ab_after=None in_room2=False "
                f"can_continue=False detail={notes}")
            log("[ch20room1] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()
            return
        log(f"[ch20room1] INGRESS OK at={self._where()} (ch20dive legs {self.legs}/5)")

        yield from self._enter_room1()
        notes["legA"] = self.r1_arrival
        if not self.in_room1:
            log(f"[ch20room1] RESULT in_room1=False ab_before=None ab_after=None in_room2=False "
                f"can_continue=False detail={notes}")
            log("[ch20room1] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()
            return

        yield from self._solve_room1()
        notes["room1"] = self.r1

        # ‼ `self.moved` MUST EXIST EVEN IF THE STEP IS NEVER ATTEMPTED. It is assigned only
        # inside `_can_continue_step`, so on the failure branch (Room 1 did not reach the door)
        # the read below used to raise `AttributeError` — crashing BEFORE the RESULT and
        # ACCEPTANCE lines and before `set_manual_mode()`, i.e. derailing instead of failing.
        # Found by adversarial review, then REPRODUCED with `POKEBOT_CH20_FAULT=room1`:
        #   f4511: *** EXCEPTION: 'Ch20Room1Mode' object has no attribute 'moved'
        # Three green runs never touched this branch — the happy path cannot exercise an error
        # path, which is the most re-learned lesson in this project.
        self.moved = False
        if self.r1["in_room2"]:
            yield from self._can_continue_step(MapRSE.SEAFLOOR_CAVERN_ROOM2, "ch20room1")
        can_continue = self.moved and _ctx.bot_mode != "Manual"

        # ‼ `ab_before is False` is an ASSERTED part of the verdict, not a nice-to-have: if the
        # corridor was already reachable, the run proved nothing about the puzzle at all.
        passed = (self.in_room1 and (not self.r1["ab_before"]) and self.r1["ab_after"]
                  and self.r1["smashed"] and self.r1["pushed1"] and self.r1["pushed2"]
                  and self.r1["in_room2"] and can_continue)
        log(f"[ch20room1] RESULT in_room1={self.in_room1} ab_before={self.r1['ab_before']} "
            f"ab_after={self.r1['ab_after']} smashed={self.r1['smashed']} "
            f"pushed1={self.r1['pushed1']} pushed2={self.r1['pushed2']} "
            f"in_room2={self.r1['in_room2']} can_continue={can_continue}")
        log(f"[ch20room1] DETAIL {notes}")
        log(f"[ch20room1] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class Ch20Room2Mode(Ch20Room1Mode):
    """§Ch20 increment 2 — ROOM 2, the three-push corridor, into the ROOM 6 current maze.

    ‼ IT RE-SOLVES ROOM 1 EVERY TIME, AND THAT IS NOT WASTE. Room 1's rock and boulders are
    `FLAG_TEMP_*` objects that respawn on every map load, so "arrive in Room 2 with Room 1 already
    solved" does not exist. Room 1 is inherited from `Ch20Room1Mode` as `_enter_room1()` +
    `_solve_room1()`, so this driver also RE-PROVES Room 1 on every run rather than assuming it.

    THE ROUTE IS ARBITRATED, LIKE ROOM 1'S — and unlike Room 1's, this one came out CLEAN.
    The decomp (`data/maps/SeafloorCavern_Room2/map.json`) and our own ROM reader agree on all
    **8 objects**, and upstream `puzzle_solver.py:395-402` is confirmed **step for step**; our build
    spec's Room 2 line agrees too. Objects (all `MOVEMENT_TYPE_LOOK_AROUND`, `TRAINER_TYPE_NONE`):

        id 4  PUSHABLE_BOULDER (4,5)  FLAG_TEMP_15   <- the corridor plug; needs THREE pushes north
        id 6  BREAKABLE_ROCK   (8,7)  FLAG_TEMP_18   <- the only east<->west link REACHABLE from
                                                        the arrival tile (rows 4-6 are walled at
                                                        x=8,9); row 3 is a second corridor but is
                                                        unreachable until after this solve
        ids 1,2,3,5,8 boulders and id 7 rock — all off the Kyogre path

    ‼ **THREE PUSHES, AND EXACTLY THREE.** `(4,4)`, `(4,3)`, `(4,2)` are each `collision=0
    elevation=3 'Cave'`; `(4,1)` is `collision=1 elevation=0` ⇒ **a fourth push is ILLEGAL and
    would fail SILENTLY in-game** (`TryPushBoulder` does nothing and prints nothing). Measured
    reachability of the ROOM6 door `(6,1)` after each push: 1 push → NO, 2 pushes → NO (`(4,4)` is
    a dead end, `(3,4)`/`(5,4)` are `collision=1`), **3 pushes → YES**. The boulder has zero slack.

    ‼ **NEVER PRESS DOWN ON THE ARRIVAL TILE.** `(10,7)` is both where Room 1 drops you AND a
    `South Arrow Warp` straight back to Room 1 — and going back resets every `FLAG_TEMP_*` object
    in BOTH rooms. The first move is Left.

    ‼ **NO TRAINERS AND NO SCRIPTS IN THIS ROOM** (`scripts.inc` is `.byte 0`; `coord_events` and
    `bg_events` are empty) — but **wild encounters are live on every route tile** (`gSeafloorCavern
    _Room2` land mons, Zubat L30+). A battle can fire BETWEEN two pushes, so every push is issued
    through `strength_push`, which re-navigates to its own approach tile and is idempotent — never
    a blind `walk_one_tile` that assumes the avatar stayed put.

    THE A/B IS THREE-POINT, NOT TWO, AND THE MIDDLE POINT IS THE INTERESTING ONE:
        M1  at arrival (10,7)      -> (6,2)   PREDICTED NO-PATH  (rock AND boulder seal it)
        M2  after the smash, (4,6) -> (6,2)   PREDICTED NO-PATH  (‼ the smash ALONE is not enough)
        M3  after 3 pushes, (4,3)  -> (6,2)   PREDICTED OK
    M2 exists so a PASS cannot be explained by "the rock was the only obstacle" — it attributes the
    opening to the PUSHES specifically. `(6,2)` was chosen because it is plain `'Cave'`, is not an
    object-template tile (no `dynamic_object_id` noise) and is not a warp tile.

    ‼ CAN-CONTINUE IS DIFFERENT HERE, ON PURPOSE. Room 6 is an open-water CURRENT maze: stepping
    onto a current SLIDES you, so "walk to an adjacent tile" can legitimately fail while the bot is
    in perfect shape. The GATE is therefore a real `calculate_path` from the Room 6 arrival to the
    room's exit `(4,1)` — which is also leg 5 of the build spec, and which
    `probe_ch20_currents.py` predicted routable from OUTSIDE the cavern. Making it the gate turns
    that planner-level prediction into an in-room measurement. The adjacent-step attempt still
    runs, but is REPORTED, not graded. ⚠ Neither proves the EXECUTOR can cross a current — that is
    still unproven (KI-76), and this driver does not claim it.

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room2 --frames 2000000

    Emits: [ch20room2] RESULT room1_ok=<b> m1=<b> m2=<b> m3=<b> pushes=<n>/3 in_room6=<b>
           can_continue=<b>
    """

    ROOM2_SMASH_APPROACH = (9, 7)     # stand here, face Left -> BREAKABLE_ROCK id 6 at (8,7)
    #: The three pushes, in order: (approach_tile, face). Each moves boulder id 4 one tile north
    #: and leaves the player on the tile it vacated — which is the NEXT approach tile.
    ROOM2_PUSHES = (((4, 6), "Up"), ((4, 5), "Up"), ((4, 4), "Up"))
    ROOM2_AB_TARGET = (6, 2)          # plain 'Cave', not an object tile, not a warp
    ROOM6_DOOR = (6, 1)               # 'Non-Animated Door' -> SEAFLOOR_CAVERN_ROOM6 (11,21)
    ROOM6_EXIT = (4, 1)               # the build spec's leg-5 target, out of the current maze

    @staticmethod
    def name():
        return "Ch20Room2"

    @staticmethod
    def _strength_flag() -> bool:
        """`FLAG_SYS_USE_STRENGTH` right now.

        ‼ THIS IS A DELIBERATE, DISCRIMINATING MEASUREMENT, not telemetry. Two sources in our own
        repo disagree about it:
          * `modules/story/early_game.py:7638-7645` and `:7799` say it is *"NEVER CLEARED ... once
            per SAVE, not once per map"*, on the strength of a decomp-wide search for `clearflag`;
          * an adversarial decomp pass says `ClearTempFieldEventData()` (`src/event_data.c:39-48`)
            calls `FlagClear(FLAG_SYS_USE_STRENGTH)` and is invoked from `LoadMapFromWarp`
            (`src/overworld.c:848`) — i.e. **on every warp**.
        The two are reconcilable: our search looked for the SCRIPT MACRO `clearflag`, and this is
        the C function `FlagClear`, so a macro-only search would miss it by construction.
        ‼ Either way the production CODE is safe — `strength_push` re-checks the flag on every
        call and re-activates — so this measures a DOC claim, not a defect. Warping ROOM1 -> ROOM2
        is a free, decisive test: read it on arrival.
        """
        from modules.memory import get_event_flag

        return get_event_flag("SYS_USE_STRENGTH")



    def _solve_room2(self):
        """MEASURE Room 2 live, smash `(8,7)`, push boulder id 4 north EXACTLY three times, and
        take the `(6,1)` door into ROOM 6. Sets `self.r2`.

        ‼ A METHOD for the same reason `_solve_room1` is: every DEEPER cavern drive has to redo
        this room from scratch, because its rock and boulder are `FLAG_TEMP_*` objects that
        respawn on every map load. A subclass inherits the solve AND re-proves it on every run.
        """
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out, _smash_rock, strength_push

        room2 = MapRSE.SEAFLOOR_CAVERN_ROOM2
        notes = {}
        self.r2 = notes
        # ---- ‼ THE STRENGTH-FLAG MEASUREMENT — free, and it settles a documented disagreement -
        # Room 1 activated Strength (its first push pays the prompt). We have just WARPED into
        # Room 2. If our own `early_game.py` comment is right, the flag is still set; if the
        # adversarial decomp pass is right, `LoadMapFromWarp -> ClearTempFieldEventData` cleared
        # it and Room 2's first push must pay the prompt again.
        try:
            strength_after_warp = self._strength_flag()
        except Exception as error:  # noqa: BLE001 - a failed read is a finding, not a crash
            strength_after_warp = None
            log(f"[ch20room2] STRENGTH-FLAG read raised {type(error).__name__}: "
                f"{str(error)[:200]} — reported as None, NOT as False (an unread flag is not a "
                f"cleared flag, and conflating them would fabricate the very result being tested)")
        log(f"[ch20room2] STRENGTH-FLAG after the ROOM1->ROOM2 warp: {strength_after_warp} "
            f"(our early_game.py comment PREDICTS True = 'never cleared, once per SAVE'; the "
            f"decomp pass PREDICTS False = cleared by ClearTempFieldEventData on every warp)")
        notes["strength_flag_after_warp"] = strength_after_warp

        # ---- M1: sealed at the arrival tile --------------------------------------------------
        arrival = get_player_avatar().local_coordinates
        self._dump_objects("R2-ARRIVAL", room2)
        m1_open, m1_detail = self._path_ok(room2, arrival, self.ROOM2_AB_TARGET)
        log(f"[ch20room2] M1 {arrival} -> {self.ROOM2_AB_TARGET}: {m1_detail}")
        log(f"[ch20room2] M1 path_exists={m1_open} (PREDICTED False — rock (8,7) AND boulder (4,5))")

        # ---- LEG 1: step Left off the warp tile, then smash ---------------------------------
        # ‼ (10,7) is a 'South Arrow Warp' back to ROOM1. Going back resets every FLAG_TEMP_*
        # object in BOTH rooms, so the very first move must be away from it.
        smashed = False
        try:
            yield from _navigate_riding_out(room2, self.ROOM2_SMASH_APPROACH)
            yield from _smash_rock(room2, self.ROOM2_SMASH_APPROACH, "Left")
            smashed = True
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room2] SMASH raised {type(error).__name__}: {str(error)[:300]}")
        after_smash = self._dump_objects("R2-AFTER-SMASH", room2)
        log(f"[ch20room2] SMASH ok={smashed} rock local_id=6 present={6 in after_smash} "
            f"(PREDICTED absent)")

        # ---- M2: ‼ THE MIDDLE ARM — the smash ALONE must NOT open it ------------------------
        m2_open, m2_detail = None, "not attempted"
        if smashed:
            try:
                yield from _navigate_riding_out(room2, self.ROOM2_PUSHES[0][0])
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room2] M2 approach raised {type(error).__name__}: {str(error)[:250]}")
            here = get_player_avatar().local_coordinates
            m2_open, m2_detail = self._path_ok(room2, here, self.ROOM2_AB_TARGET)
            log(f"[ch20room2] M2 {here} -> {self.ROOM2_AB_TARGET}: {m2_detail}")
            log(f"[ch20room2] M2 path_exists={m2_open} (PREDICTED False — ‼ this arm is what "
                f"attributes the opening to the PUSHES rather than to the smash)")

        # ---- LEG 2: the three pushes, and EXACTLY three -------------------------------------
        # ‼ A FOURTH PUSH IS ILLEGAL — (4,1) is collision=1 — and would fail SILENTLY. The loop is
        # a fixed tuple rather than "push until it moves" for exactly that reason.
        pushes = 0
        if smashed:
            for index, (approach, face) in enumerate(self.ROOM2_PUSHES, start=1):
                try:
                    yield from strength_push(room2, approach, face)
                    pushes += 1
                except Exception as error:  # noqa: BLE001
                    log(f"[ch20room2] PUSH{index} raised {type(error).__name__}: "
                        f"{str(error)[:300]}")
                    break
                seen = self._dump_objects(f"R2-AFTER-PUSH{index}", room2)
                expected = (4, 5 - index)
                log(f"[ch20room2] PUSH{index} ok boulder local_id=4 at={seen.get(4)} "
                    f"(PREDICTED {expected})")
        log(f"[ch20room2] PUSHES {pushes}/3")
        try:
            _after = self._strength_flag()
        except Exception as error:  # noqa: BLE001
            _after = f"<unreadable {type(error).__name__}>"
        log(f"[ch20room2] STRENGTH-FLAG after the Room 2 pushes: {_after} "
            f"(it must be True here whichever source was right — `strength_push` re-activates)")

        # ---- M3: the far arm -----------------------------------------------------------------
        here = get_player_avatar().local_coordinates
        m3_open, m3_detail = self._path_ok(room2, here, self.ROOM2_AB_TARGET)
        log(f"[ch20room2] M3 {here} -> {self.ROOM2_AB_TARGET}: {m3_detail}")
        log(f"[ch20room2] M3 path_exists={m3_open} (PREDICTED True)")
        notes["ab"] = {"m1": (arrival, m1_open, m1_detail), "m2": (m2_open, m2_detail),
                       "m3": (here, m3_open, m3_detail)}

        # ---- LEG 3: the (6,1) door into ROOM 6 ----------------------------------------------
        if pushes == 3:
            try:
                yield from _navigate_riding_out(room2, self.ROOM6_DOOR)
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room2] LEG3 raised {type(error).__name__}: {str(error)[:300]} "
                    f"(the door warp firing mid-walk can look like this)")
        where = self._where()
        in_room6 = where[0] == "SEAFLOOR_CAVERN_ROOM6"
        notes["leg3"] = where
        log(f"[ch20room2] LEG3 at={where} in_room6={in_room6} "
            f"(PREDICTED SEAFLOOR_CAVERN_ROOM6 (11,21))")

        notes.update({"m1": m1_open, "m2": m2_open, "m3": m3_open, "pushes": pushes,
                      "smashed": smashed, "in_room6": in_room6, "where": where,
                      "strength_flag_after_warp": strength_after_warp})

    def run(self):
        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import wait_until_truly_controllable

        room6 = MapRSE.SEAFLOOR_CAVERN_ROOM6
        notes = {}

        def _bail(reason: str):
            log(f"[ch20room2] ‼ STOPPING — {reason}")
            log(f"[ch20room2] RESULT room1_ok={notes.get('room1_ok', False)} m1=None m2=None "
                f"m3=None pushes=0/3 in_room6=False can_continue=False detail={notes}")
            log("[ch20room2] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()

        yield from wait_until_truly_controllable()
        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            _bail("the Dive fixture failed, so the cavern is unreachable")
            return
        yield from self._ingress()
        notes["ingress"] = self.notes
        if not (self.leg1_ok and self.at_entrance):
            _bail(f"the ingress did not surface in the cavern (legs={self.legs}/5)")
            return
        yield from self._enter_room1()
        if not self.in_room1:
            _bail("never reached ROOM1")
            return
        yield from self._solve_room1()
        room1_ok = bool(self.r1["in_room2"] and self.r1["pushed2"] and not self.r1["ab_before"]
                        and self.r1["ab_after"])
        notes["room1_ok"] = room1_ok
        log(f"[ch20room2] ROOM1 re-solved ok={room1_ok} (it resets on every map load — this is a "
            f"re-proof, not a cache)")
        if not self.r1["in_room2"]:
            _bail("Room 1 did not deliver us into ROOM2")
            return

        yield from self._solve_room2()
        r2 = self.r2
        notes["room2"] = r2
        m1_open, m2_open, m3_open = r2["m1"], r2["m2"], r2["m3"]
        pushes, in_room6 = r2["pushes"], r2["in_room6"]

        # ---- CAN-CONTINUE: a PATH through the current maze, not a step ----------------------
        # ‼ Room 6 is open water full of currents; stepping onto one SLIDES you, so an
        # adjacent-tile walk can fail while the bot is perfectly fine. The GATE is a real
        # `calculate_path` to the room's exit (4,1) — the build spec's leg-5 target, which
        # `probe_ch20_currents.py` predicted routable from OUTSIDE the cavern. This turns that
        # prediction into an in-room measurement. ⚠ A PLAN IS NOT A WALK: crossing a current has
        # still never been executed (KI-76), and nothing here claims otherwise.
        route_out, route_detail = False, "not attempted"
        if in_room6:
            here6 = get_player_avatar().local_coordinates
            log(f"[ch20room2] ROOM6 arrival={here6} tile_type={self._tile_type()!r}")
            route_out, route_detail = self._path_ok(room6, here6, self.ROOM6_EXIT)
            log(f"[ch20room2] CAN-CONTINUE {here6} -> {self.ROOM6_EXIT}: {route_detail}")
            # Reported, NOT graded — see the docstring.
            yield from self._can_continue_step(room6, "ch20room2")
            log(f"[ch20room2] CAN-CONTINUE (ungraded) adjacent-step moved={self.moved} "
                f"now at={self._where()} tile_type={self._tile_type()!r}")
        can_continue = route_out and _ctx.bot_mode != "Manual"
        notes["room6"] = (route_out, route_detail)

        passed = (room1_ok and (not m1_open) and (m2_open is False) and m3_open
                  and pushes == 3 and in_room6 and can_continue)
        log(f"[ch20room2] RESULT room1_ok={room1_ok} m1={m1_open} m2={m2_open} m3={m3_open} "
            f"pushes={pushes}/3 in_room6={in_room6} can_continue={can_continue}")
        log(f"[ch20room2] DETAIL {notes}")
        log(f"[ch20room2] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class Ch20Room6Mode(Ch20Room2Mode):
    """‼ THE FIRST EXECUTED CURRENT CROSSING IN THIS PROJECT — ROOM 6, then into ROOM 3.

    WHY THIS IS ITS OWN INCREMENT AND NOT PART OF A ROOM 3 DRIVER. Everything about Rooms 6/7 so
    far is **PLANNER-LEVEL ONLY**: `probe_ch20_currents.py` put 4 pre-registered predictions to
    `calculate_path` and got 4/4, and `--driver ch20room2` reproduced one of them from inside the
    room (`(11,21) -> (4,1)` = `OK len=13`). **A PLAN IS NOT A WALK.** No current has ever been
    executed here, the EXECUTOR has never crossed one, and KI-76's correctness half is still open.
    Bundling that unknown with Room 3's would have made a failure unattributable — so this drives
    the crossing and nothing else, and Room 3 gets its own driver afterwards.

    WHAT A CURRENT DOES: stepping onto `MB_*WARD_CURRENT` triggers `DoForcedMovement`
    (`src/field_player_avatar.c:443`) and SLIDES the avatar until it hits something. Our planner
    models this as multi-tile edges (`forced_movement_to`), which is why 13 waypoints can cover a
    27-tile Manhattan trip. ✅ Reassuring, from the decomp: a current that shoves you into a wall
    returns control **on that tile, the same frame** — swept over all 108 Room-6 current tiles,
    **zero infinite loops**. ⚠ That is the TERRAIN side; whether OUR executor agrees is what this
    measures.

    ‼ ROOM 6 IS ONE-WAY. `(11,21) -> (4,1)` works; the reverse does not. If the crossing succeeds
    the bot CANNOT come back the way it came — the retreat is Room 6's other warp `(14,8)`.
    ‼ KI-76's OPEN half is armed in exactly this room: a slide that ENDS ON A WARP is never
    penalised, A* is ~9x biased toward long slides under `avoid_encounters`, and `(14,8)` is a
    water-level door that **9 of the room's 108 chains end on**. Our route is one of the four
    already asserted trap-free by `probe_ch20_currents.py` section 3b — but that assertion is per
    ROUTE, so it is re-checked live here rather than assumed.

    ‼ AND THE ROOM HAS WATER ENCOUNTERS. `gSeafloorCavern_Room6` has a full `water_mons` table —
    the build spec said the cavern's encounters were "on land in Rooms 1-8", which is wrong. A
    battle can interrupt a slide, so nothing may assume the avatar stayed where a plan put it.

    THE ACCEPTANCE, in order of what it proves:
      1. `crossed`    — the avatar actually reaches `ROOM6 (4,1)` by WALKING, not by planning.
      2. `in_room3`   — the `(4,15)` warp fires and we land in `SEAFLOOR_CAVERN_ROOM3`.
      3. `room3_walk` — ‼ a live cross-check of the Room 3 arbitration: `calculate_path((4,15) ->
         (8,1))` must return a path **that contains `(6,5)`**. That single assertion confirms BOTH
         that Room 3 is crossable PUSH-FREE (so its 7-boulder puzzle really is optional) AND that
         the push-free line really does enter the trainer sight tile — the two claims the Room 3
         note rests on, neither of which has been checked live.
      4. `can_continue` — a real step in Room 3.

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room6 --frames 2500000

    Emits: [ch20room6] RESULT room2_ok=<b> crossed=<b> in_room3=<b> room3_walk=<b> can_continue=<b>
    """

    ROOM6_ENTRY = (11, 21)       # where Room 2's (6,1) door drops us
    ROOM3_ARRIVAL = (4, 15)      # ROOM6 (4,1) -> SEAFLOOR_CAVERN_ROOM3 (4,15)
    ROOM3_EXIT = (8, 1)          # ROOM3's 'Non-Animated Door' -> ROOM8 (5,12)
    ROOM3_SIGHT_TILE = (6, 5)    # the tile the push-free line must enter (both trainers see it)

    @staticmethod
    def name():
        return "Ch20Room6"

    def _cross_room6(self, notes: dict):
        """Walk the ROOM 6 CURRENT MAZE to `(4,1)` and take the transition into ROOM 3.

        Sets `self.crossed` and `self.in_room3`.

        ‼ A METHOD so the Room 3 driver INHERITS the crossing instead of copying it — the same
        rule that produced `_ingress`, `_solve_room1` and `_solve_room2`. Every deeper drive
        re-proves every room beneath it, because they are all `FLAG_TEMP_*` rooms that reset on
        every map load, so there is no such thing as arriving with a lower room already solved.
        """
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out

        room6 = MapRSE.SEAFLOOR_CAVERN_ROOM6
        self.crossed = self.in_room3 = False
        in_room3 = False

        # ---- THE CROSSING: the first current ever WALKED in this project -------------------
        entry = get_player_avatar().local_coordinates
        log(f"[ch20room6] ROOM6 entry={entry} tile_type={self._tile_type()!r} (PREDICTED (11,21))")
        planned, plan_detail = self._path_ok(room6, entry, self.ROOM6_EXIT)
        log(f"[ch20room6] PLAN {entry} -> {self.ROOM6_EXIT}: {plan_detail}")
        log(f"[ch20room6] PLAN exists={planned} — ‼ this is the PLAN. The walk is next, and the "
            f"whole point of this run is that the two can disagree.")
        try:
            yield from _navigate_riding_out(room6, self.ROOM6_EXIT)
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room6] CROSSING raised {type(error).__name__}: {str(error)[:300]}")
        where = self._where()
        here = get_player_avatar().local_coordinates
        # ‼ "CROSSED" MUST TOLERATE HAVING ALREADY WARPED. If (4,1) turns out to be a step-on
        # warp rather than an arrow warp, arriving there lands us in ROOM3 and a strict
        # `where == (ROOM6, (4,1))` test would read False over a crossing that WORKED PERFECTLY.
        # That is the "assert the outcome, not the position you expected" rule; this driver exists
        # to measure the CROSSING, and reaching Room 3 is a strictly stronger proof of it.
        crossed = (where == ("SEAFLOOR_CAVERN_ROOM6", self.ROOM6_EXIT)
                   or where[0] == "SEAFLOOR_CAVERN_ROOM3")
        notes["crossing"] = (entry, planned, where)
        log(f"[ch20room6] CROSSING at={where} crossed={crossed} tile_type={self._tile_type()!r}")
        if not crossed:
            log(f"[ch20room6] ‼ THE PLAN AND THE WALK DISAGREE (planned={planned}, ended at "
                f"{here}). That is a REAL FINDING about the executor, not a route problem — "
                f"KI-76 says a slide model that plans is not a slide model that walks.")

        # ---- ROOM 6 -> ROOM 3 --------------------------------------------------------------
        # ‼ (4,1) is a warp tile; arriving on it may or may not fire the transition on its own,
        # so the map is re-read and the result is reported either way rather than assumed.
        # ‼ AN ARROW WARP NEEDS A **HELD** DIRECTION, NOT A NAVIGATE. `TryArrowWarp`
        # (`src/field_control_avatar.c:688-700`) fires only while `heldDirection` matches the
        # player's facing, so standing on the tile does nothing and `navigate_to` onto the tile we
        # are already on is a no-op. The direction is DERIVED FROM THE TILE'S OWN NAME rather than
        # guessed — `map.py` names them "North/South/East/West Arrow Warp" — so this is correct
        # whichever kind (4,1) turns out to be, and a plain door needs no help at all.
        if crossed:
            where = self._where()
            if where[0] != "SEAFLOOR_CAVERN_ROOM3":
                kind = str(self._tile_type())
                hold = next((d for d in ("North", "South", "East", "West") if d in kind), None)
                direction = {"North": "Up", "South": "Down",
                             "East": "Right", "West": "Left"}.get(hold)
                log(f"[ch20room6] WARP tile_type={kind!r} -> arrow direction={direction!r}")
                try:
                    if direction is not None:
                        from modules.story.early_game import _walk_through_warp

                        yield from _walk_through_warp(direction, room6.value)
                    else:
                        yield from _navigate_riding_out(room6, self.ROOM6_EXIT)
                except Exception as error:  # noqa: BLE001
                    log(f"[ch20room6] WARP raised {type(error).__name__}: {str(error)[:250]}")
                where = self._where()
            in_room3 = where[0] == "SEAFLOOR_CAVERN_ROOM3"
            notes["room3_arrival"] = where
            log(f"[ch20room6] ROOM3 at={where} in_room3={in_room3} (PREDICTED (4,15))")

        self.crossed, self.in_room3 = crossed, in_room3

    def run(self):
        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import wait_until_truly_controllable

        room3 = MapRSE.SEAFLOOR_CAVERN_ROOM3
        notes = {}
        room2_ok = crossed = in_room3 = room3_walk = False

        def _bail(reason: str):
            log(f"[ch20room6] ‼ STOPPING — {reason}")
            log(f"[ch20room6] RESULT room2_ok={room2_ok} crossed=False in_room3=False "
                f"room3_walk=False can_continue=False detail={notes}")
            log("[ch20room6] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()

        yield from wait_until_truly_controllable()
        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            _bail("the Dive fixture failed, so the cavern is unreachable")
            return
        yield from self._ingress()
        if not (self.leg1_ok and self.at_entrance):
            _bail(f"the ingress did not surface in the cavern (legs={self.legs}/5)")
            return
        yield from self._enter_room1()
        if not self.in_room1:
            _bail("never reached ROOM1")
            return
        yield from self._solve_room1()
        if not self.r1["in_room2"]:
            _bail("Room 1 did not deliver us into ROOM2")
            return
        yield from self._solve_room2()
        room2_ok = bool(self.r2["in_room6"] and self.r2["pushes"] == 3)
        notes["room1"] = {k: self.r1[k] for k in ("ab_before", "ab_after", "pushed2", "in_room2")}
        notes["room2"] = {k: self.r2[k] for k in ("m1", "m2", "m3", "pushes", "in_room6")}
        log(f"[ch20room6] ROOMS 1+2 re-solved ok={room2_ok} (both reset on every map load)")
        if not self.r2["in_room6"]:
            _bail("Room 2 did not deliver us into ROOM6")
            return

        yield from self._cross_room6(notes)
        crossed, in_room3 = self.crossed, self.in_room3

        # ---- ‼ THE LIVE CROSS-CHECK OF THE ROOM 3 ARBITRATION ------------------------------
        # The Room 3 note claims (a) (4,15)->(8,1) is reachable PUSH-FREE, so the 7-boulder puzzle
        # is optional, and (b) that line unavoidably enters a trainer sight tile. NEITHER has been
        # checked live. One `calculate_path` settles both, from inside the room, for free.
        if in_room3:
            start = get_player_avatar().local_coordinates
            try:
                from modules.map_path import calculate_path

                path = calculate_path((room3, start), (room3, self.ROOM3_EXIT))
                tiles = [tuple(getattr(wp, "coordinates", ()) or ()) for wp in path]
                hits_sight = self.ROOM3_SIGHT_TILE in tiles
                room3_walk = bool(path) and hits_sight
                log(f"[ch20room6] ROOM3-WALK {start} -> {self.ROOM3_EXIT}: OK len={len(path)} "
                    f"contains{'' if hits_sight else ' NO'} {self.ROOM3_SIGHT_TILE}")
                log(f"[ch20room6] ROOM3-WALK push_free_reachable=True enters_sight={hits_sight} "
                    f"(PREDICTED both True: the puzzle is OPTIONAL, and the walk MUST take the "
                    f"double battle)")
                notes["room3_walk"] = (len(path), hits_sight, tiles[:24])
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room6] ROOM3-WALK raised {type(error).__name__}: {str(error)[:250]} "
                    f"— ‼ if this is a PathFindingError the Room 3 arbitration is REFUTED and the "
                    f"7-boulder puzzle is MANDATORY after all.")
                notes["room3_walk"] = f"{type(error).__name__}"

        # ---- CAN-CONTINUE -------------------------------------------------------------------
        self.moved = False
        if in_room3:
            yield from self._can_continue_step(room3, "ch20room6")
        can_continue = self.moved and _ctx.bot_mode != "Manual"

        passed = (room2_ok and crossed and in_room3 and room3_walk and can_continue)
        log(f"[ch20room6] RESULT room2_ok={room2_ok} crossed={crossed} in_room3={in_room3} "
            f"room3_walk={room3_walk} can_continue={can_continue}")
        log(f"[ch20room6] DETAIL {notes}")
        log(f"[ch20room6] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class Ki76WarpMode(Ch20Room6Mode):
    """`#24-ki76correctness` — DOES A CURRENT SLIDE REALLY END ON A WARP AND EJECT US FROM THE MAP?

    ⛔ THIS IS A CONFIRMATION, NOT A FIX. KI-76's "ends-on-a-warp" defect is STATIC ANALYSIS: the
    planner charges its 1,000,000 warp penalty against the NEIGHBOUR (`map_path.py:972`) and only
    afterwards substitutes the slide DESTINATION for it (`:1013`), so a chain that terminates ON a
    warp is never penalised and never marked `is_warp`. Nobody has watched it happen.

    THE TWO ARMS, and they differ on MAP IDENTITY alone — the cheapest possible assertion:
      ARM M (our model)  final map SEAFLOOR_CAVERN_ROOM6, tile (14,8), still Surfing
      ARM R (the game)   final map SEAFLOOR_CAVERN_ENTRANCE (the (14,8) Non-Animated Door fires)

    ‼ EVERY COORDINATE BELOW WAS MEASURED, NOT READ OFF A DOC — `probe_room6_warp_entries.py`,
    evidence `evidence/2026-08-17-ki76-room6-warp-entries.stdout.txt`:
      * nine chains end on (14,8); their entry tiles are enumerated there;
      * ⛔ `(14,9)` — the tile KI-76 and the punch list both NAMED — is UNSTAGEABLE. Room 6 is
        ONE-WAY, and 14 of the 15 candidate staging tiles have NO PATH from Room 6's entry. A
        driver written from the docs would have failed at runtime after ~15 minutes of setup;
      * EXACTLY ONE usable staging tile: (8,12), 5 waypoints, no waypoint on a current, none on
        a warp. It steps EAST onto (9,12), an Eastward Current whose chain runs NINE steps.

    ⛔ STAGE-AND-STEP, NEVER `navigate_to` AN ENTRY TILE. Asking the planner to path ONTO a current
    tile is asking the very code under test to answer the question: `:1013` substitutes the slide
    destination for it. So we path to plain water and press the button ourselves.

    ‼ AND THE STEP IS OUR OWN, BOUNDED, INSTRUMENTED ONE — NOT `walk_one_tile`. That helper has two
    unbounded `while` loops and its own docstring warns it "will create an endless loop if trying to
    run into a wall". Riding a current into a map transition is exactly where a never-terminating
    wait would hang the harness. This stepper is frame-capped, and it SAMPLES THE TRAJECTORY, so the
    evidence is the slide itself rather than an endpoint we have to take on trust.

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive_ki76.ss1 --driver ki76warp --frames 2500000

    ⚠ Drive the PINNED `post_dive_ki76.ss1`, never `post_dive.ss1` — the latter is re-captured by
    `--driver spacecenter` on every PASS and is listed VOLATILE.
    """

    # ‼‼ A WILD ENCOUNTER MID-SLIDE WOULD FAKE A VERDICT — guard added 2026-08-17 (pass 2 audit).
    # `Ch20Room6Mode`'s own docstring warns this room HAS water encounters. If a battle fires during
    # the ride, `local_coordinates` FREEZES; the settle loop's `stable > 180` then reads that as
    # "the slide finished", and if the freeze happens to sit on (14,8) the run would report ARM M —
    # a verdict for a slide that never resolved. ⇒ any battle during `_ride` forces arm "?" and
    # ACCEPTANCE FAIL. ⛔ The RUN is what gets invalidated, never the finding.
    # ⛔ INSTANCE attribute, reset in `run()`. A CLASS attribute would leak across two runs in one
    # process and quietly fail the SECOND run for the FIRST run's battle.
    _battled = False

    def on_battle_started(self, encounter=None):
        """Any battle invalidates THE RUN — never the finding."""
        self._battled = True
        log("[ki76] ‼ BATTLE STARTED — this run can no longer grade the slide; a battle FREEZES "
            "`local_coordinates`, which the settle loop cannot tell apart from a finished slide.")
        return super().on_battle_started(encounter)

    STAGING = (8, 12)
    ENTRY_TILE = (9, 12)
    PRESS = "Right"                 # EAST, from (8,12) onto (9,12)
    PRED_TERMINUS = (14, 8)         # what PRODUCTION says the chain ends on
    STEP_CAP_FRAMES = 900           # ~15s; a 9-tile slide is far under this
    SETTLE_CAP_FRAMES = 900

    def _sample(self):
        """(map_name, tile, surfing) — the three values the acceptance rests on."""
        from modules.player import AvatarFlags, get_player_avatar

        name, tile = self._where()
        try:
            surf = AvatarFlags.Surfing in get_player_avatar().flags
        except Exception as error:  # noqa: BLE001 - a failure to read it IS the finding
            surf = f"unreadable({type(error).__name__})"
        return name, tile, surf

    def _ride(self, notes: dict):
        """Stage on (8,12), step EAST once, and RECORD THE WHOLE SLIDE."""
        import os

        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.story.early_game import _navigate_riding_out

        room6 = MapRSE.SEAFLOOR_CAVERN_ROOM6
        self.staged = self.stepped = False
        self.trail = []

        start = self._sample()
        log(f"[ki76] ROOM6 arrival {start} (PREDICTED (11,21))")

        planned, detail = self._path_ok(room6, start[1], self.STAGING)
        log(f"[ki76] PLAN {start[1]} -> staging {self.STAGING}: {detail}")
        try:
            yield from _navigate_riding_out(room6, self.STAGING)
        except Exception as error:  # noqa: BLE001 - a failure here IS the finding
            log(f"[ki76] STAGING raised {type(error).__name__}: {str(error)[:250]}")

        here = self._sample()
        # ‼‼ THE POSITIVE CONTROL, AND IT GATES EVERYTHING BELOW. If we never reached (8,12) then
        # "we are still in ROOM6 at the end" is not a measurement of ARM M — it is a measurement of
        # a run that never started. 08-MISTAKES 2026-08-17: a zero from an instrument that could not
        # have produced a non-zero is not evidence. So this refuses rather than reporting a verdict.
        self.staged = (here[0] == "SEAFLOOR_CAVERN_ROOM6" and tuple(here[1]) == self.STAGING)
        log(f"[ki76] STAGED at={here} on_target={self.staged} tile_type={self._tile_type()!r}")
        if not self.staged:
            log("[ki76] ‼ NOT ON THE STAGING TILE — the ride is NOT attempted and NO verdict is "
                "reported. A final position measured from the wrong start proves nothing about "
                "either arm.")
            return

        before = self._sample()
        log(f"[ki76] RIDE pressing {self.PRESS} (EAST) from {before[1]} onto {self.ENTRY_TILE}; "
            f"production predicts the chain ends on {self.PRED_TERMINUS} after 9 steps.")

        def _note(sample, tag):
            key = (sample[0], tuple(sample[1]))
            if not self.trail or key != (self.trail[-1][0], tuple(self.trail[-1][1])):
                self.trail.append(sample)
                log(f"[ki76]   {tag} {sample[0]} {tuple(sample[1])} surfing={sample[2]}")
                return True
            return False

        # ---- our own BOUNDED, INSTRUMENTED step -------------------------------------------
        # ‼‼ THE CONTROL ARM, AND IT EXISTS BECAUSE THE OBVIOUS OBJECTION IS A GOOD ONE.
        # The default arm HOLDS the direction for the whole slide. A sceptic is entitled to ask
        # whether the warp fired because the CURRENT delivered us onto (14,8), or because a held
        # button kept pressing once we got there. `KI76_RELEASE_EARLY=1` releases the button the
        # INSTANT the avatar first moves, so the rest of the ride is unassisted. If ARM R still
        # results, the button is EXONERATED and the current is the only remaining cause.
        # ⇒ "without X the effect survives" is a CLAIM until an arm with X removed is run
        # (08-MISTAKES / SESSION DISCIPLINE rule 8). This is that arm.
        release_early = os.environ.get("KI76_RELEASE_EARLY", "0") == "1"
        log(f"[ki76] ARM-CONTROL KI76_RELEASE_EARLY={'1 (button released as soon as we move)' if release_early else '0 (button held through the slide)'}")
        _ctx.emulator.hold_button(self.PRESS)
        held = True
        frames = 0
        moved = False
        while frames < self.STEP_CAP_FRAMES:
            frames += 1
            yield
            s = self._sample()
            _note(s, f"f+{frames}")
            if (s[0], tuple(s[1])) != (before[0], tuple(before[1])):
                if not moved and release_early and held:
                    _ctx.emulator.release_button(self.PRESS)
                    held = False
                    log(f"[ki76]   RELEASED at f+{frames} on first movement — the rest of this "
                        f"slide is UNASSISTED")
                moved = True
            if moved and s[0] != "SEAFLOOR_CAVERN_ROOM6":
                break   # we left the map: that IS arm R, and there is nothing more to wait for
        if held:
            _ctx.emulator.release_button(self.PRESS)

        # Let the slide finish. Bounded, and it stops early once the position has been stable.
        settle = 0
        stable = 0
        while settle < self.SETTLE_CAP_FRAMES:
            settle += 1
            yield
            s = self._sample()
            stable = 0 if _note(s, f"settle+{settle}") else stable + 1
            if stable > 180:
                break

        self.stepped = moved
        notes["trail"] = [(t[0], tuple(t[1]), t[2]) for t in self.trail][:40]
        log(f"[ki76] RIDE moved={moved} step_frames={frames} settle_frames={settle} "
            f"distinct_positions={len(self.trail)}")

    def run(self):
        import hashlib
        import os

        from modules.context import context as _ctx

        notes = {}
        self._battled = False   # ⛔ per-RUN, not per-process

        # ---- ANCHOR GUARD (copied from Ki66FaintMode, which PROVED it) --------------------
        # ‼ Hash before AND after and LOG BOTH, so the guard is proven rather than claimed.
        anchor = SAVES / "post_dive_ki76.ss1"
        anchor_before = hashlib.sha256(anchor.read_bytes()).hexdigest() if anchor.is_file() else None
        # ⛔ CH19C_CAPTURE=0 stops `spacecenter` re-capturing `post_dive.ss1` — a DIFFERENT file.
        # It does NOT protect `post_dive_ki76.ss1`; nothing writes that, and the sha256 compare
        # below is DETECTIVE, not preventive. ‼ This log used to say "so nothing can re-capture an
        # anchor during this run", which claimed prevention it does not provide (found by an audit
        # agent, 2026-08-17). A guard that overstates itself is worse than one that is merely weak.
        os.environ["CH19C_CAPTURE"] = "0"
        log(f"[ki76] SAFETY anchor=post_dive_ki76.ss1 sha256[:12]="
            f"{(anchor_before or '<absent>')[:12]} — the PINNED copy (md5 a00378595409). "
            f"⚠ DETECTION, not prevention: the hash is re-read at the end and compared. "
            f"(CH19C_CAPTURE=0 is set too, but that guards `post_dive.ss1`, not this file.)")

        def _bail(reason: str):
            log(f"[ki76] BAIL {reason}")
            log("[ki76] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()

        # ‼‼ THE PARENT DOES THESE TWO FIRST AND THEY ARE NOT OPTIONAL. Run 2 of this driver
        # reached ROUTE128 and then stalled for 20,000 frames because I had reproduced the parent
        # run()'s LOOP but not its PREAMBLE: without the injected Dive fixture there is no leg 2,
        # so the ingress cannot surface in the cavern. ⛔ When you fork a run(), diff it against the
        # original from its FIRST statement, not from the step you care about.
        from modules.story.early_game import wait_until_truly_controllable

        yield from wait_until_truly_controllable()
        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            _bail("the Dive fixture failed, so the cavern is unreachable")
            return
        yield from self._ingress()
        if not (self.leg1_ok and self.at_entrance):
            _bail(f"the ingress did not surface in the cavern (legs={self.legs}/5)")
            return
        yield from self._enter_room1()
        if not self.in_room1:
            _bail("never reached ROOM1")
            return
        yield from self._solve_room1()
        if not self.r1["in_room2"]:
            _bail("Room 1 did not deliver us into ROOM2")
            return
        yield from self._solve_room2()
        if not self.r2["in_room6"]:
            _bail("Room 2 did not deliver us into ROOM6")
            return
        log("[ki76] ROOMS 1+2 re-solved (both reset on every map load)")

        yield from self._ride(notes)

        final = self._sample()
        anchor_after = hashlib.sha256(anchor.read_bytes()).hexdigest() if anchor.is_file() else None
        anchor_intact = anchor_after == anchor_before

        # ---- THE VERDICT -------------------------------------------------------------------
        # ⛔ GRADED ON MAP IDENTITY, the ONLY field the two arms are guaranteed to differ on. Tile
        # and surf state are RECORDED for the write-up and never used to decide.
        # ‼ `not self._battled` IS PART OF EVERY ARM, and it is here because the first draft of this
        # guard SET the flag and never READ it — a decorative guard, caught in the same session that
        # added it. ⛔ A flag that no branch consults protects nothing.
        gradeable = bool(self.staged and self.stepped and not self._battled)
        left_room6 = bool(gradeable and final[0] != "SEAFLOOR_CAVERN_ROOM6")
        held_at_terminus = bool(gradeable
                                and final[0] == "SEAFLOOR_CAVERN_ROOM6"
                                and tuple(final[1]) == self.PRED_TERMINUS)
        if left_room6:
            arm = "R"
            arm_text = "R (the game WARPS — KI-76's ends-on-a-warp defect is CONFIRMED LIVE)"
        elif held_at_terminus:
            arm = "M"
            arm_text = "M (our model — the slide ENDED ON the warp tile without firing it)"
        else:
            arm = "?"
            arm_text = "NEITHER — read the trail; do not report a verdict from this run"

        log(f"[ki76] FINAL map={final[0]} tile={tuple(final[1])} surfing={final[2]}")
        log(f"[ki76] ARM = {arm_text}")
        log(f"[ki76] SAFETY anchor intact = {anchor_intact} "
            f"(before={(anchor_before or '<absent>')[:12]} after={(anchor_after or '<absent>')[:12]})")
        log(f"[ki76] DETAIL {notes}")

        # ‼ ACCEPTANCE GRADES THE INSTRUMENT, NOT THE ANSWER. Either arm is a legitimate scientific
        # result; what invalidates the RUN is failing to stage, failing to move, or touching the
        # anchor. ⛔ A driver that only passes when it likes the answer is not an experiment.
        passed = bool(self.staged and self.stepped and anchor_intact
                      and not self._battled and arm in ("R", "M"))
        log(f"[ki76] RESULT staged={self.staged} stepped={self.stepped} "
            f"anchor_intact={anchor_intact} battled={self._battled} arm={arm}")
        log(f"[ki76] ACCEPTANCE: {'PASS' if passed else 'FAIL'} (grades the INSTRUMENT: staged AND "
            f"stepped AND anchor intact AND landed on one of the two predicted arms)")
        _ctx.set_manual_mode()
        return


class Ch20Room3Mode(Ch20Room6Mode):
    """§Ch20 ROOM 3 — the WALK route, and the first live test of the DOUBLE-BATTLE claim.

    ‼ THE ROUTE IS THE ARBITRATED ONE, AND IT DELIBERATELY DOES **NOT** SOLVE THE PUZZLE.
    `ai-research-notes/2026-08-13-ch20-room3-arbitration.md`: `(4,15) -> (8,1)` is reachable
    **PUSH-FREE in 18 steps** — confirmed LIVE by `--driver ch20room6`, which measured
    `calculate_path((4,15) -> (8,1))` = `OK len=18` **containing `(6,5)`** from inside the room.
    Room 3's 7-boulder checkerboard is therefore **OPTIONAL**: it buys only the avoidance of one
    trainer fight, at the cost of **five irreversible pushes** in a room a mid-sequence derail can
    WEDGE. We win that fight (L40-49 vs L35-37), so the reversible route is the right one.
    ⛔ An earlier agent pass called our build spec "REFUTED" here and was **itself wrong**; the
    correction is in the arbitration note and in `08-MISTAKES.md`.

    ‼ THE CLAIM THIS DRIVER EXISTS TO TEST: it is **ONE DOUBLE BATTLE, NOT TWO SINGLES.**
    `CheckForTrainersWantingBattle` (`src/trainer_see.c:191-218`) does not stop at the first
    trainer — with **>=2 usable Pokemon** it collects both and `battle_setup.c:1272-1275` starts a
    double. Shelly `(9,5)` sight 6 and Grunt5 `(5,5)` sight 4 both cover `{(6,5),(7,5),(8,5)}`,
    and sight here is a **1-tile-wide LINE, not a cone** (`==` on y, no tolerance), with
    `FACE_LEFT`/`FACE_RIGHT` movement types that **never rotate**. That is all decomp-derived and
    **has never been observed live** — so this run counts battles and records
    `battle_state.is_double_battle` at each one. **ONE battle that reports `is_double=True` is the
    prediction; TWO singles refutes the decomp reading.**

    ‼ PRECONDITION, AND IT CHANGES THE OUTCOME RATHER THAN JUST GUARDING IT: with **fewer than 2
    usable** Pokemon the engine fires **two sequential singles** instead. So the count is asserted
    BEFORE entering the sight line and reported with the result — otherwise a "two singles" reading
    would be unattributable between "the decomp is wrong" and "our party was too weak to qualify".
    (`modules/story/mossdeep_gym.py:315-369` already rides a double battle out behind exactly this
    kind of gate.)

    ‼ A DEFEATED TRAINER STILL OCCUPIES ITS TILE. The trainer flags are separate from
    `FLAG_HIDE_SEAFLOOR_CAVERN_AQUA_GRUNTS` (set only when Kyogre escapes), and
    `TrainerMoveToPlayer` WALKS each trainer toward the player — Shelly is predicted to end on
    `(7,5)`. So the post-battle continuation is re-planned from the live position, never from the
    plan made before the battle.

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room3 --frames 3000000

    Emits: [ch20room3] RESULT crossed=<b> usable=<n> battles=<n> saw_double=<b> in_room8=<b>
           can_continue=<b>
    """

    ROOM8_ARRIVAL = (5, 12)      # ROOM3 (8,1) -> SEAFLOOR_CAVERN_ROOM8 (5,12)

    @staticmethod
    def name():
        return "Ch20Room3"

    def on_battle_started(self, encounter):
        """Count battles and record whether the game made this one a DOUBLE.

        ‼ THIS IS THE MEASUREMENT, not bookkeeping. `is_double_battle` is read HERE, at the
        moment the battle starts, because it is the only point at which the question is
        answerable — afterwards there is a defeated-trainer flag but no record of how many
        trainers were in the fight. Reading it late is how a count that nets to the right number
        can describe the wrong event."""
        try:
            from modules.battle_state import get_battle_state

            is_double = bool(get_battle_state().is_double_battle)
        except Exception as error:  # noqa: BLE001 - a failed read is a finding, not a crash
            is_double = f"<unreadable {type(error).__name__}>"
        kind = "wild" if encounter is not None else "trainer"
        self.battle_log.append((kind, is_double, self._where()))
        log(f"[ch20room3] BATTLE #{len(self.battle_log)} kind={kind} is_double={is_double} "
            f"at={self._where()}")
        return super().on_battle_started(encounter)

    @staticmethod
    def _usable_count() -> int:
        """Party members that can still fight — the threshold the DOUBLE battle depends on."""
        from modules.pokemon_party import get_party

        return sum(1 for mon in get_party()
                   if mon is not None and not mon.is_egg and mon.current_hp > 0)

    def _cross_room3(self, notes: dict):
        """The ROOM 3 WALK (18 steps, zero pushes, through the sight line) + the double-battle
        discriminator. Sets `self.usable`, `self.in_room8`, `self.saw_double` and
        `self.r3_trainer_battles`.

        ‼ EXTRACTED VERBATIM FROM `run()` 2026-08-14 so `--driver ch20room8` INHERITS the proven
        walk instead of copying it — the same rule that produced `_ingress`, `_solve_room1`,
        `_solve_room2` and `_cross_room6`. Neutrality is re-proven by re-running
        `--driver ch20room3` after the extraction. Logs stay under `[ch20room3]` no matter who
        calls it — a log line names the thing that ran, not the caller.
        """
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out

        room3 = MapRSE.SEAFLOOR_CAVERN_ROOM3

        # ---- ‼ THE PRECONDITION IS PART OF THE MEASUREMENT ---------------------------------
        usable = self._usable_count()
        notes["usable_before"] = usable
        log(f"[ch20room3] PRECONDITION usable={usable} "
            f"({'OK — the DOUBLE battle can form' if usable >= 2 else 'BELOW 2 — the engine will '
               'fire TWO SEQUENTIAL SINGLES instead, and a two-battle reading would then say '
               'nothing about the decomp'})")

        # ---- THE WALK: 18 steps, ZERO pushes, straight through the sight line ---------------
        # ‼ The route MUST enter (6,5). That is not a hazard to route around here — it is the
        # chapter's cheapest way through, and the fight is one we win.
        start = get_player_avatar().local_coordinates
        try:
            yield from _navigate_riding_out(room3, self.ROOM3_EXIT)
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room3] WALK raised {type(error).__name__}: {str(error)[:300]} "
                f"(the (8,1) door warp firing mid-walk can look like this)")
        where = self._where()
        in_room8 = where[0] == "SEAFLOOR_CAVERN_ROOM8"
        notes["walk"] = (start, where)
        log(f"[ch20room3] WALK {start} -> {where} in_room8={in_room8} "
            f"(PREDICTED SEAFLOOR_CAVERN_ROOM8 {self.ROOM8_ARRIVAL})")

        # ---- THE DISCRIMINATOR --------------------------------------------------------------
        # ‼ SCOPED TO ROOM 3, AND IT WAS NOT ON THE FIRST RUN — THAT WAS A REAL INSTRUMENT BUG.
        # The first version counted trainer battles RUN-WIDE, so it swept in the Room 1 Aqua grunt
        # (predicted, and fought every single run) and printed
        #   "2 SEPARATE trainer battles — the 'one double battle' claim is REFUTED"
        # over data that CONFIRMED the claim: exactly one Room 3 trainer battle, `is_double=True`,
        # at exactly (6,5). A verdict line that names the wrong event is worse than no verdict —
        # it would have been copied into the docs as a refutation. The battle log records the MAP
        # per battle, so the scoping is available and was simply not applied.
        all_trainers = [b for b in self.battle_log if b[0] == "trainer"]
        trainer_battles = [b for b in all_trainers if b[2][0] == "SEAFLOOR_CAVERN_ROOM3"]
        saw_double = any(b[1] is True for b in trainer_battles)
        log(f"[ch20room3] BATTLES total={len(self.battle_log)} trainer_anywhere={len(all_trainers)} "
            f"trainer_in_ROOM3={len(trainer_battles)} saw_double={saw_double}")
        log(f"[ch20room3] BATTLE-LOG {self.battle_log}")
        if len(trainer_battles) == 1 and saw_double:
            log("[ch20room3] ✅ ONE trainer battle, reported DOUBLE — the decomp reading of "
                "`trainer_see.c:214-217` is CONFIRMED LIVE.")
        elif len(trainer_battles) >= 2:
            log(f"[ch20room3] ‼ {len(trainer_battles)} SEPARATE trainer battles IN ROOM 3 — the "
                f"'one double battle' claim is REFUTED for this party/route (usable={usable}). "
                f"That is a real correction to the Room 3 arbitration, not a run failure.")
        elif not trainer_battles:
            log("[ch20room3] ‼ ZERO trainer battles — either the route avoided the sight line "
                "(contradicting the measured path containing (6,5)) or the grunts are HIDDEN. "
                "Check FLAG_HIDE_SEAFLOOR_CAVERN_AQUA_GRUNTS before believing either.")
        notes["battles"] = self.battle_log

        self.usable = usable
        self.in_room8 = in_room8
        self.saw_double = saw_double
        self.r3_trainer_battles = trainer_battles

    def run(self):
        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import wait_until_truly_controllable

        room8 = MapRSE.SEAFLOOR_CAVERN_ROOM8
        notes = {}
        self.battle_log = []
        usable = 0
        in_room8 = False

        def _bail(reason: str):
            log(f"[ch20room3] ‼ STOPPING — {reason}")
            log(f"[ch20room3] RESULT crossed=False usable={usable} battles=0 saw_double=False "
                f"in_room8=False can_continue=False detail={notes}")
            log("[ch20room3] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()

        yield from wait_until_truly_controllable()
        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            _bail("the Dive fixture failed, so the cavern is unreachable")
            return
        yield from self._ingress()
        if not (self.leg1_ok and self.at_entrance):
            _bail(f"the ingress did not surface in the cavern (legs={self.legs}/5)")
            return
        yield from self._enter_room1()
        if not self.in_room1:
            _bail("never reached ROOM1")
            return
        yield from self._solve_room1()
        if not self.r1.get("in_room2"):
            _bail("Room 1 did not deliver us into ROOM2")
            return
        yield from self._solve_room2()
        if not self.r2.get("in_room6"):
            _bail("Room 2 did not deliver us into ROOM6")
            return
        yield from self._cross_room6(notes)
        if not self.in_room3:
            _bail("the ROOM 6 current crossing did not deliver us into ROOM3")
            return
        log(f"[ch20room3] ROOMS 1+2+6 re-proven; standing in {self._where()}")

        # ---- the walk + the double-battle discriminator, extracted (see `_cross_room3`) -----
        yield from self._cross_room3(notes)
        usable, in_room8 = self.usable, self.in_room8
        trainer_battles, saw_double = self.r3_trainer_battles, self.saw_double

        # ---- CAN-CONTINUE --------------------------------------------------------------------
        self.moved = False
        if in_room8:
            log(f"[ch20room3] ROOM8 at={get_player_avatar().local_coordinates} "
                f"tile_type={self._tile_type()!r}")
            yield from self._can_continue_step(room8, "ch20room3")
        can_continue = self.moved and _ctx.bot_mode != "Manual"

        # ‼ `saw_double` is REPORTED but NOT graded. The run's job is to deliver the bot into
        # Room 8; the battle shape is a MEASUREMENT of a decomp claim, and grading on it would
        # turn "we learned the claim was wrong" into "the run failed" — which is exactly how a
        # negative result gets buried instead of recorded.
        passed = (self.in_room3 and in_room8 and can_continue)
        log(f"[ch20room3] RESULT crossed={self.crossed} usable={usable} "
            f"battles={len(trainer_battles)} saw_double={saw_double} in_room8={in_room8} "
            f"can_continue={can_continue}")
        log(f"[ch20room3] DETAIL {notes}")
        log(f"[ch20room3] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class Ch20Room8Mode(Ch20Room3Mode):
    """§Ch20 ROOM 8 — twelve boulders, OUR adjudicated 9-push sequence, into ROOM 9.

    ‼ THE SEQUENCE IS ADJUDICATED, NOT CHOSEN. Ours (9 pushes) over upstream's 10 — upstream's
    touches an extra boulder for nothing. Full table + hazards:
    `ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md`; the pre-registered
    predictions for THIS driver: `ai-research-notes/2026-08-14-ch20-room8-drive-predictions.md`.
    An independent offline refutation pass was dispatched against the table BEFORE this drive.

    ⛔ STEP 9 FACES LEFT, NEVER UP. A boulder pushed north from (5,4) lands on (5,3) — the ONLY
    tile connecting the room to the (5,2) exit — and can then never be moved off it, because the
    side-push stands (4,3)/(6,3) are themselves occupied by then. Both sources dodge this without
    saying why; this driver says why so a future "simplification" cannot reintroduce it.

    ✅ A JAM IS RECOVERABLE, AND THE HANDLER IS WIRED, NOT IMPROVISED: exit to Room 3 via the
    (5,12) arrow warp (‼ HOLD Down — `TryArrowWarp` fires only on a HELD direction), re-enter
    through Room 3's (8,1) door, and all twelve boulders respawn from the map header
    (`FLAG_TEMP_*`), while Room 3's trainers STAY defeated. The driver retries the sequence ONCE
    after a recovery; a second jam is a FAIL with the recovery at least proven.
    ‼ Exercise the handler with `POKEBOT_CH20_FAULT=room8`: attempt 1 abandons the sequence
    before push 5, so recovery + retry runs for real — the happy path cannot exercise an error
    path, which is the most re-learned lesson in this project.

    ‼ KI-77 (the 20x17 despawn window) predicts the ARRIVAL object dump at (5,12) is SHORT:
    rows y<=4 are outside `y ∈ [py-7, py+9]`, so the northern boulders are INVISIBLE THERE, not
    absent. The visible-count assertion is therefore taken from the staging tile (5,8) — from
    which every row of this 11x14 room is in range — never from arrival.

    ‼ EVERY PUSH GOES THROUGH `strength_push` — bounded, idempotent, re-navigates to its own
    approach tile (so a wild Zubat between pushes cannot desynchronise the plan), verifies the
    boulder BY `local_id` ON THE DESTINATION, and raises LOUD on a refused push. A refused push
    in this room would otherwise hang forever (upstream's eleven blind `walk_one_tile` calls).

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room8 --frames 4000000

    Emits: [ch20room8] RESULT room3_ok=<b> pushes=<n>/9 attempts=<n> recovered=<b> exit_path=<b>
           in_room9=<b> can_continue=<b>
    """

    #: Backstop for failure branches, same rule as `moved` on Ch20Room1Mode.
    recovered = False

    ROOM8_STAGING = (5, 8)        # north of the Jump South ledge row; all 12 boulders in window
    #: The adjudicated 9-push sequence: (approach_tile, face). `strength_push` derives the
    #: boulder tile (approach+1) and destination (approach+2) itself and navigates to each
    #: approach on its own, which is what makes the two "navigate, then push" rows (3 and 7)
    #: need no special casing here.
    ROOM8_PUSHES = (
        ((5, 8), "Up"),      # 1: boulder (5,7) -> (5,6)
        ((5, 7), "Left"),    # 2: boulder (4,7) -> (3,7)
        ((4, 6), "Right"),   # 3: boulder (5,6) -> (6,6)   (the push-1 boulder, again)
        ((5, 6), "Up"),      # 4: boulder (5,5) -> (5,4)
        ((5, 5), "Left"),    # 5: boulder (4,5) -> (3,5)
        ((4, 5), "Up"),      # 6: boulder (4,4) -> (4,3)
        ((5, 5), "Right"),   # 7: boulder (6,5) -> (7,5)
        ((6, 5), "Up"),      # 8: boulder (6,4) -> (6,3)
        ((6, 4), "Left"),    # 9: boulder (5,4) -> (4,4)  ⛔ LEFT — Up would seal (5,3) forever
    )
    ROOM9_DOOR = (5, 2)           # 'Non-Animated Door' -> SEAFLOOR_CAVERN_ROOM9
    ROOM3_RETREAT = (5, 12)       # 'South Arrow Warp' back to ROOM3 (8,1) — the jam recovery
    ROOM9_ARRIVAL = (5, 4)        # predicted arrival; its own arrow warp needs a HELD direction

    _STEP = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}

    @staticmethod
    def name():
        return "Ch20Room8"

    def _recover_room8_jam(self, notes: dict, attempt: int):
        """The wired failure handler: ROOM8 -> ROOM3 -> ROOM8, so all twelve `FLAG_TEMP_*`
        boulders respawn from the map header. Sets `self.recovered`.

        ‼ NEVER improvise near (5,3) — the adjudication is explicit that recovery is exit and
        re-entry, nothing else. Room 3's trainer flags persist, so re-entry costs no battle."""
        from modules.map_data import MapRSE
        from modules.story.early_game import _navigate_riding_out, _walk_through_warp

        room8 = MapRSE.SEAFLOOR_CAVERN_ROOM8
        room3 = MapRSE.SEAFLOOR_CAVERN_ROOM3
        self.recovered = False
        log(f"[ch20room8] RECOVERY (attempt {attempt}): exiting via {self.ROOM3_RETREAT}, "
            f"re-entering through ROOM3 {self.ROOM3_EXIT}; all twelve boulders respawn from "
            f"the map header")
        try:
            yield from _navigate_riding_out(room8, self.ROOM3_RETREAT)
            # ‼ THE HOLD DIRECTION IS DERIVED FROM THE TILE'S OWN NAME, NOT HARDCODED — the same
            # rule (and comment) as `_cross_room6`: `TryArrowWarp` fires only while the direction
            # is HELD, `map.py` names these tiles "North/South/East/West Arrow Warp", and deriving
            # keeps this correct whichever kind (5,12) turns out to be. Flagged by adversarial
            # review: a hardcoded "Down" would break silently (recovered=False, no retry) if the
            # static reading of this tile were ever wrong. A plain step-on warp has already fired
            # by now, and the map check below decides either way.
            if self._where()[0] == "SEAFLOOR_CAVERN_ROOM8":
                kind = str(self._tile_type())
                hold = next((d for d in ("North", "South", "East", "West") if d in kind), None)
                direction = {"North": "Up", "South": "Down",
                             "East": "Right", "West": "Left"}.get(hold)
                log(f"[ch20room8] RECOVERY exit tile_type={kind!r} -> arrow direction="
                    f"{direction!r} (PREDICTED 'South Arrow Warp' -> 'Down')")
                if direction is not None:
                    yield from _walk_through_warp(direction, room8.value)
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room8] RECOVERY exit raised {type(error).__name__}: {str(error)[:250]}")
        where = self._where()
        if where[0] != "SEAFLOOR_CAVERN_ROOM3":
            log(f"[ch20room8] RECOVERY ‼ did not reach ROOM3 (at={where}) — recovery FAILED")
            notes[f"recovery{attempt}"] = ("exit-failed", where)
            return
        try:
            yield from _navigate_riding_out(room3, self.ROOM3_EXIT)
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room8] RECOVERY re-entry raised {type(error).__name__}: "
                f"{str(error)[:250]} (the (8,1) door warp firing mid-walk can look like this)")
        where = self._where()
        back = where[0] == "SEAFLOOR_CAVERN_ROOM8"
        seen = self._dump_objects("R8-RESPAWN", room8) if back else {}
        # ‼ The respawn check is honest about KI-77: from (5,12) only rows y>=5 are in window,
        # so "some boulders visible again" is the strongest claim this dump can make. The RETRY
        # is what proves the respawn — every push re-verifies its boulder by local_id.
        self.recovered = back and len(seen) > 0
        notes[f"recovery{attempt}"] = (where, len(seen))
        log(f"[ch20room8] RECOVERY back_in_room8={back} boulders_visible={len(seen)} "
            f"recovered={self.recovered}")

    def _solve_room8(self, notes: dict):
        """Stage at (5,8), run the 9-push sequence (retrying ONCE via the recovery handler),
        then require a real `calculate_path` to the (5,2) exit. Sets `self.r8`."""
        import os as _os

        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out, strength_push

        room8 = MapRSE.SEAFLOOR_CAVERN_ROOM8
        self.r8 = {}
        fault_armed = _os.environ.get("POKEBOT_CH20_FAULT") == "room8"
        if fault_armed:
            log("[ch20room8] ‼ FAULT INJECTION ARMED (POKEBOT_CH20_FAULT=room8) — attempt 1 "
                "will abandon the sequence before push 5 to exercise the RECOVERY handler. A "
                "run in this mode must still print an honest RESULT and never derail.")

        arrival = get_player_avatar().local_coordinates
        arrival_seen = self._dump_objects("R8-ARRIVAL", room8)
        log(f"[ch20room8] ARRIVAL at={arrival} tile_type={self._tile_type()!r} "
            f"boulders_visible={len(arrival_seen)} (PREDICTED FEWER than 12 — KI-77's window "
            f"cuts rows y<=4 from (5,12); that is the WINDOW, not missing objects)")
        self.r8["arrival"] = (arrival, len(arrival_seen))

        pushes, attempts = 0, 0
        exit_ok, exit_detail = False, "not attempted"
        for attempt in (1, 2):
            attempts = attempt
            fault_this = fault_armed and attempt == 1
            jam = None

            # ---- step 0: staging — the ledge row (4,10)-(6,10) is Jump South, one-way, so the
            # planner must cross row 10 at x=3 or x=7. Asserted by ARRIVING, not by inspecting
            # the plan: a mis-modelled ledge shows up as a failed or bounced walk.
            staged = False
            try:
                yield from _navigate_riding_out(room8, self.ROOM8_STAGING)
                staged = get_player_avatar().local_coordinates == self.ROOM8_STAGING
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room8] STAGING raised {type(error).__name__}: {str(error)[:300]}")
            seen = self._dump_objects(f"R8-STAGED-{attempt}", room8)
            log(f"[ch20room8] STAGED ok={staged} boulders_visible={len(seen)} "
                f"(PREDICTED 12 — every row of this 11x14 room is in window from "
                f"{self.ROOM8_STAGING})")
            self.r8[f"staged{attempt}"] = (staged, len(seen))

            if staged:
                for index, (approach, face) in enumerate(self.ROOM8_PUSHES, start=1):
                    if fault_this and index == 5:
                        jam = "fault-injected stop before push 5"
                        log("[ch20room8] ‼ FAULT: abandoning the sequence before push 5 on "
                            "purpose — the recovery handler is the thing under test now.")
                        break
                    dx, dy = self._STEP[face]
                    src = (approach[0] + dx, approach[1] + dy)
                    dst = (src[0] + dx, src[1] + dy)
                    try:
                        yield from strength_push(room8, approach, face)
                        pushes += 1
                    except Exception as error:  # noqa: BLE001
                        jam = f"push {index} raised {type(error).__name__}"
                        log(f"[ch20room8] PUSH{index} raised {type(error).__name__}: "
                            f"{str(error)[:300]}")
                        break
                    seen = self._dump_objects(f"R8-AFTER-PUSH{index}", room8)
                    log(f"[ch20room8] PUSH{index} ok stand={approach} face={face} boulder "
                        f"{src}->{dst} on_destination={dst in seen.values()}")
            else:
                jam = "never reached the staging tile"

            if jam is None and pushes == len(self.ROOM8_PUSHES):
                here = get_player_avatar().local_coordinates
                seen = self._dump_objects("R8-SOLVED", room8)
                sealed = (5, 3) in seen.values()
                exit_ok, exit_detail = self._path_ok(room8, here, self.ROOM9_DOOR)
                log(f"[ch20room8] EXIT-PATH {here} -> {self.ROOM9_DOOR}: {exit_detail}")
                log(f"[ch20room8] EXIT-PATH ok={exit_ok} boulder_on_(5,3)={sealed} "
                    f"(PREDICTED True / False — a boulder on (5,3) is the permanent seal)")
                self.r8[f"attempt{attempt}"] = ("complete", pushes, exit_ok)
                if exit_ok:
                    break
                jam = "sequence complete but the exit path did not open"

            self.r8[f"attempt{attempt}"] = ("jam", pushes, jam)
            log(f"[ch20room8] ATTEMPT {attempt} FAILED after {pushes} pushes: {jam}")
            if attempt == 1:
                yield from self._recover_room8_jam(self.r8, attempt)
                if not self.recovered:
                    log("[ch20room8] ‼ RECOVERY FAILED — no retry is possible.")
                    break
                pushes = 0

        self.r8.update({"pushes": pushes, "attempts": attempts, "exit_ok": exit_ok,
                        "exit_detail": exit_detail})

    def run(self):
        import os as _os

        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

        room9 = MapRSE.SEAFLOOR_CAVERN_ROOM9
        notes = {}
        self.battle_log = []
        in_room9 = False

        def _bail(reason: str):
            log(f"[ch20room8] ‼ STOPPING — {reason}")
            log(f"[ch20room8] RESULT room3_ok=False pushes=0/9 attempts=0 recovered=False "
                f"exit_path=False in_room9=False can_continue=False detail={notes}")
            log("[ch20room8] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()

        yield from wait_until_truly_controllable()
        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            _bail("the Dive fixture failed, so the cavern is unreachable")
            return
        yield from self._ingress()
        if not (self.leg1_ok and self.at_entrance):
            _bail(f"the ingress did not surface in the cavern (legs={self.legs}/5)")
            return
        yield from self._enter_room1()
        if not self.in_room1:
            _bail("never reached ROOM1")
            return
        yield from self._solve_room1()
        if not self.r1.get("in_room2"):
            _bail("Room 1 did not deliver us into ROOM2")
            return
        yield from self._solve_room2()
        if not self.r2.get("in_room6"):
            _bail("Room 2 did not deliver us into ROOM6")
            return
        yield from self._cross_room6(notes)
        if not self.in_room3:
            _bail("the ROOM 6 current crossing did not deliver us into ROOM3")
            return
        yield from self._cross_room3(notes)
        room3_ok = bool(self.in_room8)
        if not self.in_room8:
            _bail("Room 3 did not deliver us into ROOM8")
            return
        log(f"[ch20room8] ROOMS 1+2+6+3 re-proven; standing in {self._where()}")

        yield from self._solve_room8(notes)
        notes["room8"] = self.r8
        pushes, attempts = self.r8["pushes"], self.r8["attempts"]
        exit_ok = self.r8["exit_ok"]

        # ---- ROOM8 -> ROOM9 through the (5,2) door -----------------------------------------
        if exit_ok:
            try:
                yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM8, self.ROOM9_DOOR)
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room8] ROOM9-LEG raised {type(error).__name__}: {str(error)[:300]} "
                    f"(the (5,2) door warp firing mid-walk can look like this)")
        where = self._where()
        in_room9 = where[0] == "SEAFLOOR_CAVERN_ROOM9"
        notes["room9"] = where
        log(f"[ch20room8] ROOM9 at={where} in_room9={in_room9} (PREDICTED "
            f"{self.ROOM9_ARRIVAL}; its South Arrow Warp must NOT bounce us back — an arrow "
            f"warp needs a HELD direction)")

        # ---- CAN-CONTINUE -------------------------------------------------------------------
        self.moved = False
        if in_room9:
            log(f"[ch20room8] ROOM9 at={get_player_avatar().local_coordinates} "
                f"tile_type={self._tile_type()!r}")
            yield from self._can_continue_step(room9, "ch20room8")
        can_continue = self.moved and _ctx.bot_mode != "Manual"

        # ‼ In fault mode the recovery IS part of the verdict — an unexercised handler is prose,
        # not a handler. In a normal run `recovered` stays False (nothing jammed) and is
        # REPORTED, not graded.
        fault_armed = _os.environ.get("POKEBOT_CH20_FAULT") == "room8"
        passed = (room3_ok and pushes == 9 and exit_ok and in_room9 and can_continue
                  and (self.recovered if fault_armed else True))
        log(f"[ch20room8] RESULT room3_ok={room3_ok} pushes={pushes}/9 attempts={attempts} "
            f"recovered={self.recovered} exit_path={exit_ok} in_room9={in_room9} "
            f"can_continue={can_continue}")
        log(f"[ch20room8] DETAIL {notes}")
        log(f"[ch20room8] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class Ch20Room9Mode(Ch20Room8Mode):
    """§Ch20 ROOM 9 — Archie, KYOGRE'S AWAKENING, the forced warp, and the atoll escape.

    ‼ THE CHAIN IS DECOMP-RECONNED, NOT RECALLED (independent agent, 2026-08-14, every beat
    cited; predictions pre-registered in
    `ai-research-notes/2026-08-14-ch20-room9-drive-predictions.md`). The three facts this
    driver is built around:
      1. The `(17,42)` trigger's gate is **`VAR_SEAFLOOR_CAVERN_STATE == 0`**
         (`Room9/map.json:130`) — asserted BEFORE the walk. ⛔ `(16,42)` is the SPARKLE target
         (`scripts.inc:38`), not the trigger.
      2. **Room 9 has NO wild encounter table and zero sight cones** — the 62-step walk is
         uninterruptible; Archie is `addobject`-ed by the scene itself.
      3. ⛔ **THE FIRST `releaseall` IS A TRAP.** Room 9's script tail executes on Route 128
         BEFORE the OnFrame scene (`VAR_ROUTE128_STATE == 1`) re-locks with Steven. All
         post-cutscene movement is gated on **`VAR_ROUTE128_STATE == 2`**
         (`Route128/scripts.inc:77`, one command before the final `releaseall`), NEVER on
         "looks controllable".

    THE GRADING, per the build spec AND the recon agreeing: `VAR_ROUTE128_STATE == 2`, never
    the Kyogre flag — the flag is set (`Room9/scripts.inc:128`) BEFORE the forced
    `warp MAP_ROUTE128, 38, 22` (`:138`), so a flag-graded run reports success from inside two
    nested cutscenes. The flag IS asserted here — at the moment the map changes, where it is a
    mid-warp invariant, not a completion signal.

    ‼ THE EXIT IS THE MEASURED ATOLL ESCAPE (Blocker 2, `probe_route128_landing.py`, 9/9):
    the landing tile `(38,22)` has ZERO surfable neighbours, the western-shore launches strand
    the run in a 41-tile closed lagoon, and the ONE-STEP rule is: **south to `(38,23)`, face
    Down, Surf onto `(38,24)`** — a confirmed launch into the 1,766-tile open ocean. The
    can-continue is a real step ON the ocean plus a real `calculate_path` back to the dive tile
    `(38,27)`.

    ‼ LOSING TO ARCHIE = whiteout to the last heal location with the script context dead —
    `VAR_SEAFLOOR_CAVERN_STATE` stays 0, no vars/flags written. The milestone loop detects
    "map is neither ROOM9 nor ROUTE128" and bails LOUD; dungeon re-entry is the CHAPTER's
    design decision, not something a driver improvises.

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room9 --frames 6000000

    Emits: [ch20room9] RESULT rooms_ok=<b> triggered=<b> battles_r9=<n> kyogre_flag=<b>
           var2=<b> landed=<b> escaped=<b> ocean_path=<b> can_continue=<b>
    """

    ROOM9_TRIGGER = (17, 42)      # the coord event; (16,42) is only the sparkle
    ROUTE128_LANDING = (38, 22)   # forced-warp destination, shallow sandbar
    ESCAPE_STAND = (38, 23)       # one step south of the landing
    ESCAPE_WATER = (38, 24)       # the confirmed open-ocean launch
    OCEAN_PROBE = (38, 27)        # the ch20dive DIVE_TILE — same open-ocean component

    @staticmethod
    def name():
        return "Ch20Room9"

    @staticmethod
    def _var(name: str):
        """An event var, or a string describing why it could not be read — an unread var must
        never be conflated with a value (the ch20room2 STRENGTH-FLAG rule)."""
        from modules.memory import get_event_var

        try:
            return get_event_var(name)
        except Exception as error:  # noqa: BLE001
            return f"<unreadable {type(error).__name__}>"

    @staticmethod
    def _flag(name: str):
        from modules.memory import get_event_flag

        try:
            return get_event_flag(name)
        except Exception as error:  # noqa: BLE001
            return f"<unreadable {type(error).__name__}>"

    def _ride_until(self, label: str, predicate, budget_frames: int):
        """A-ride the cutscene chain until `predicate()` or the budget runs out. Bounded and
        LOUD on failure, per the never-hang rule. Sets `self.milestone_ok`.

        ‼ The whiteout guard is built in: if the map is neither ROOM9 nor ROUTE128 the chain is
        dead (a loss warps to the last heal location) and waiting longer cannot help.
        ‼ The mode generator is FROZEN during battles (the BattleListener owns those frames),
        so this loop simply resumes after the Archie fight — it needs no battle handling.

        ‼ THE BUTTON IS GATED, NOT MASHED — the museum-greeter rule (`08-MISTAKES.md`): **A next
        to an NPC is not "advance text", it STARTS a conversation**, and milestone 3 spans the
        documented control seam between Room 9's tail `releaseall` and the Route 128 OnFrame
        re-lock, with Archie/Maxie/Steven on adjacent tiles. So: **A only when a text printer is
        actually waiting on input; B otherwise** — B advances/dismisses identically but can never
        initiate. Flagged by adversarial review before the first run; same fix shape as the
        proven sail helper (`is_waiting_for_input()` gate)."""
        from modules.context import context as _ctx
        from modules.modes.util.sleep import wait_for_n_frames
        from modules.tasks import is_waiting_for_input

        self.milestone_ok = False
        frames = 0
        while frames < budget_frames:
            if predicate():
                self.milestone_ok = True
                log(f"[ch20room9] MILESTONE {label} reached after ~{frames} loop-frames")
                return
            where = self._where()
            if where[0] not in ("SEAFLOOR_CAVERN_ROOM9", "ROUTE128"):
                log(f"[ch20room9] ‼ MILESTONE {label} ABORTED — map is {where}, which is "
                    f"neither ROOM9 nor ROUTE128. That is the WHITEOUT signature (money "
                    f"halved, script context dead, VAR_SEAFLOOR_CAVERN_STATE still 0).")
                return
            try:
                waiting = is_waiting_for_input()
            except Exception:  # noqa: BLE001 - an unreadable printer state must not stop the ride
                waiting = False
            _ctx.emulator.press_button("A" if waiting else "B")
            yield
            yield from wait_for_n_frames(3)
            frames += 4
        log(f"[ch20room9] ‼ MILESTONE {label} NOT reached within {budget_frames} frames — "
            f"at={self._where()} r128_var={self._var('ROUTE128_STATE')} "
            f"scs_var={self._var('SEAFLOOR_CAVERN_STATE')}")

    def run(self):
        from modules.context import context as _ctx
        from modules.map_data import MapRSE
        from modules.player import AvatarFlags, get_player_avatar
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

        room9 = MapRSE.SEAFLOOR_CAVERN_ROOM9
        route128 = MapRSE.ROUTE128
        notes = {}
        self.battle_log = []
        triggered = kyogre_flag = var2 = landed = escaped = ocean_path = False

        def _bail(reason: str):
            log(f"[ch20room9] ‼ STOPPING — {reason}")
            log(f"[ch20room9] RESULT rooms_ok=False triggered={triggered} battles_r9=0 "
                f"kyogre_flag={kyogre_flag} var2={var2} landed={landed} escaped={escaped} "
                f"ocean_path={ocean_path} can_continue=False detail={notes}")
            log("[ch20room9] ACCEPTANCE: FAIL")
            _ctx.set_manual_mode()

        yield from wait_until_truly_controllable()
        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            _bail("the Dive fixture failed, so the cavern is unreachable")
            return
        yield from self._ingress()
        if not (self.leg1_ok and self.at_entrance):
            _bail(f"the ingress did not surface in the cavern (legs={self.legs}/5)")
            return
        yield from self._enter_room1()
        if not self.in_room1:
            _bail("never reached ROOM1")
            return
        yield from self._solve_room1()
        if not self.r1.get("in_room2"):
            _bail("Room 1 did not deliver us into ROOM2")
            return
        yield from self._solve_room2()
        if not self.r2.get("in_room6"):
            _bail("Room 2 did not deliver us into ROOM6")
            return
        yield from self._cross_room6(notes)
        if not self.in_room3:
            _bail("the ROOM 6 current crossing did not deliver us into ROOM3")
            return
        yield from self._cross_room3(notes)
        if not self.in_room8:
            _bail("Room 3 did not deliver us into ROOM8")
            return
        yield from self._solve_room8(notes)
        notes["room8"] = {k: self.r8[k] for k in ("pushes", "attempts", "exit_ok")}
        if not self.r8["exit_ok"]:
            _bail("Room 8 did not open its exit")
            return
        try:
            yield from _navigate_riding_out(MapRSE.SEAFLOOR_CAVERN_ROOM8, self.ROOM9_DOOR)
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room9] ROOM9-LEG raised {type(error).__name__}: {str(error)[:300]} "
                f"(the (5,2) door warp firing mid-walk can look like this)")
        rooms_ok = self._where()[0] == "SEAFLOOR_CAVERN_ROOM9"
        if not rooms_ok:
            _bail(f"the (5,2) door did not deliver us into ROOM9 (at={self._where()})")
            return
        log(f"[ch20room9] ROOMS 1+2+6+3+8 re-proven; standing in {self._where()}")

        # ---- ‼ THE ARM CHECK IS PART OF THE MEASUREMENT --------------------------------------
        # VAR_SEAFLOOR_CAVERN_STATE gates the (17,42) trigger (== 0 means armed). If it is not
        # 0, the walk would cross the tile and fire NOTHING — and a "the scene never started"
        # reading would be unattributable between "trigger broken" and "trigger retired".
        scs = self._var("SEAFLOOR_CAVERN_STATE")
        notes["arm"] = scs
        log(f"[ch20room9] ARM-CHECK VAR_SEAFLOOR_CAVERN_STATE={scs} (PREDICTED 0 = armed; "
            f"1 would mean the scene already ran and the walk below fires nothing)")

        # ---- READINESS SNAPSHOT: the one stochastic element in this chain is the Archie
        # fight, and a loss whiteouts to the heal location with the mode generator ABANDONED
        # (the WhiteoutListener sets Manual; main.py drops the controller) — so the driver
        # CANNOT self-report a loss. This line is the attribution a lost run leaves behind:
        # measured 2026-08-14 run 2, the fight was LOST (1W/1L) and the only record was the
        # listener's transcript. Chapter design must budget for that (retry policy / readiness).
        from modules.pokemon_party import get_party as _get_party

        hp_lines = [f"{m.species.name} L{m.level} {m.current_hp}/{m.total_hp}"
                    for m in _get_party() if m is not None]
        log(f"[ch20room9] PRE-ARCHIE PARTY {hp_lines} usable={self._usable_count()} "
            f"(‼ if this run never prints a RESULT, the run was LOST to Archie and the "
            f"whiteout listener dropped to Manual — that is the loss signature, and this "
            f"line is what makes it attributable)")

        # ---- THE WALK: 62 steps, no wilds, no sight cones, one solid Kyogre ------------------
        start = get_player_avatar().local_coordinates
        try:
            yield from _navigate_riding_out(room9, self.ROOM9_TRIGGER)
        except Exception as error:  # noqa: BLE001
            log(f"[ch20room9] WALK raised {type(error).__name__}: {str(error)[:300]} "
                f"(the trigger's lockall firing mid-walk can look like this)")
        log(f"[ch20room9] WALK {start} -> {self._where()} (the trigger locks the player ON "
            f"{self.ROOM9_TRIGGER}, so arrival and scene-start are the same event)")

        # ---- MILESTONE 1: the Archie battle --------------------------------------------------
        yield from self._ride_until(
            "ARCHIE-BATTLE",
            lambda: any(b for b in self.battle_log if b[2][0] == "SEAFLOOR_CAVERN_ROOM9"),
            budget_frames=20000)
        r9_battles = [b for b in self.battle_log if b[2][0] == "SEAFLOOR_CAVERN_ROOM9"]
        triggered = bool(r9_battles)
        notes["archie"] = r9_battles
        log(f"[ch20room9] ARCHIE battles_r9={len(r9_battles)} detail={r9_battles} "
            f"(PREDICTED exactly one, kind=trainer, is_double=False — "
            f"trainerbattle_no_intro, .doubleBattle=FALSE)")

        # ---- MILESTONE 2: the forced warp — and the mid-warp invariants ----------------------
        yield from self._ride_until(
            "WARP-TO-ROUTE128", lambda: self._where()[0] == "ROUTE128", budget_frames=60000)
        if self.milestone_ok:
            kyogre_flag = self._flag("KYOGRE_ESCAPED_SEAFLOOR_CAVERN")
            pos = get_player_avatar().local_coordinates
            landed = pos == self.ROUTE128_LANDING
            notes["mid_warp"] = {"kyogre": kyogre_flag, "scs": self._var("SEAFLOOR_CAVERN_STATE"),
                                 "r128": self._var("ROUTE128_STATE"), "pos": pos}
            log(f"[ch20room9] MID-WARP kyogre_flag={kyogre_flag} "
                f"scs={notes['mid_warp']['scs']} r128={notes['mid_warp']['r128']} pos={pos} "
                f"(PREDICTED True / 1 / 1 / {self.ROUTE128_LANDING} — all written BEFORE the "
                f"warp, Room9/scripts.inc:115-137)")

        # ---- MILESTONE 3: VAR_ROUTE128_STATE == 2 — the ONLY trustworthy release signal ------
        yield from self._ride_until(
            "VAR2-CONTROL", lambda: self._var("ROUTE128_STATE") == 2, budget_frames=60000)
        var2 = self.milestone_ok
        facing = get_player_avatar().facing_direction
        notes["release"] = (var2, facing)
        log(f"[ch20room9] RELEASE var2={var2} facing={facing!r} (facing PREDICTED 'Up' from "
            f"WalkInPlaceFasterUp at Route128/scripts.inc:61 — REPORTED, not graded: this is "
            f"the one previously-unmeasured claim)")

        # ---- THE ATOLL ESCAPE: the measured one-step rule ------------------------------------
        # ‼ (38,22) has ZERO surfable neighbours — "Surf from where you land" does nothing in
        # any direction and reads as a hung leg. And 28 of the atoll's launches strand the run
        # in a closed lagoon. The rule is one step SOUTH, then Surf onto (38,24). KI-72's rule
        # holds here too: the surface/launch tile is chosen EXPLICITLY, never by the planner.
        if var2:
            yield from wait_until_truly_controllable()
            try:
                yield from _navigate_riding_out(route128, self.ESCAPE_STAND)
                yield from _navigate_riding_out(route128, self.ESCAPE_WATER)
            except Exception as error:  # noqa: BLE001
                log(f"[ch20room9] ESCAPE raised {type(error).__name__}: {str(error)[:300]}")
            avatar = get_player_avatar()
            surfing = AvatarFlags.Surfing in avatar.flags
            here = avatar.local_coordinates
            escaped = surfing and self._where() == ("ROUTE128", self.ESCAPE_WATER)
            log(f"[ch20room9] ESCAPE at={self._where()} surfing={surfing} escaped={escaped} "
                f"(PREDICTED ('ROUTE128', {self.ESCAPE_WATER}) on Surf — the confirmed "
                f"open-ocean launch)")
            # ‼ The lagoon is the trap the probe measured: prove we are in the OPEN component
            # with a real path to the dive tile — the same water the chapter sailed in on.
            ocean_path, ocean_detail = self._path_ok(route128, here, self.OCEAN_PROBE)
            log(f"[ch20room9] OCEAN-PATH {here} -> {self.OCEAN_PROBE}: {ocean_detail}")
            log(f"[ch20room9] OCEAN-PATH ok={ocean_path} (PREDICTED True — (38,24) is in the "
                f"1,766-tile open component, not the 41-tile lagoon)")
            notes["escape"] = (self._where(), surfing, ocean_path)

        # ---- CAN-CONTINUE -------------------------------------------------------------------
        self.moved = False
        if escaped:
            yield from self._can_continue_step(route128, "ch20room9")
        can_continue = self.moved and _ctx.bot_mode != "Manual"

        # ‼ `facing` and the battle SHAPE are REPORTED, not graded (the facing was never
        # measured before; grading an unmeasured prediction turns "we learned something" into
        # "the run failed"). The battle COUNT is graded via `triggered`; winning is graded
        # implicitly by reaching ROUTE128 at all (a loss warps to the heal location).
        passed = (rooms_ok and triggered and (kyogre_flag is True) and var2 and landed
                  and escaped and ocean_path and can_continue)
        log(f"[ch20room9] RESULT rooms_ok={rooms_ok} triggered={triggered} "
            f"battles_r9={len(r9_battles)} kyogre_flag={kyogre_flag} var2={var2} "
            f"landed={landed} escaped={escaped} ocean_path={ocean_path} "
            f"can_continue={can_continue}")
        log(f"[ch20room9] DETAIL {notes}")
        log(f"[ch20room9] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        _ctx.set_manual_mode()
        return


class SecondWindMode(BotMode):
    """`#26-manualderails` — the SECOND-WIND arm: does the Winona raise regime grant one fresh cycle?

    ‼ BUILT BEFORE THE FIX, BY RULE. This arm's TODAY half must be measured on unmodified
    production code first; the fix ships only if AFTER differs exactly as computed. Design +
    hand-computed discriminator: the 2026-08-26 arm-design report (`#26-manualderails`).

    THE SEEDED STATE (ki80ladder's house pattern, `batch2_run04_wedge.ss1` — measured NO_ANSWER):
    8 flat losses at FORTREE_CITY_GYM + the counter ladder marked CONSUMED. That is the post-hunt
    regime the batches measure: hopeless=True, ladder returns False at its consumed-gate.

    PHASE A ("the burn"): `_prepare_for_fight(winona_fight)` FIVE times on the SAME instance —
    production's derail-retry loop, minus the travel. Grades per cycle, ON STATE where possible:
      RAISE            BotModeError; W3 requires production's own loss arithmetic in the message,
                       and the sink must hold the ladder's "already hunted" line (the witness that
                       the CONSUMED path ran — a missing witness on a RAISE cycle is a loud FAIL).
      SECOND_WIND      StopIteration AND `_loss_ko_history[key]` emptied (graded on STATE).
      PLAIN_ESCALATION / BOSS_TRAINING_MODE / ZERO_KO_FALLBACK — tripwires, as ki80ladder.
    PHASE B ("the re-arm control"): 8 FRESH flat losses + defeat_counts=16, one more cycle.
    ⛔ MUST RAISE IN BOTH ERAS — the 2026-07-30 honest-stop ruling surviving is part of the spec.

    EXPECTED TODAY:  A = RAISE x5 (byte-identical), B = RAISE.
    EXPECTED AFTER:  A = SECOND_WIND then PLAIN_ESCALATION x4 (zero raises), B = RAISE.
    Anti-vacuity: W4 (a delegating observer on the REAL `_boss_plan_is_hopeless`) must report
    hopeless=True on cycle 1, else the anchor/seed no longer produces the regime and everything
    below is vacuous — FAIL loudly, do not grade.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py batch2_run04_wedge.ss1 --driver secondwind --frames 2000
    """

    @staticmethod
    def name() -> str:
        return "SecondWind"

    def run(self):
        import ast as _ast
        import pathlib as _pathlib
        import random as _random

        import plugins.custom_modes.story_mode as _sm
        from modules.context import context as _ctx
        from modules.map_data import MapRSE, PokemonCenter
        from modules.modes import BotModeError
        from modules.pokemon_party import get_party

        TAG = "secondwind"
        fails: list[str] = []

        def bad(msg: str) -> None:
            fails.append(msg)
            log(f"[{TAG}] ‼ {msg}")

        base_cfg = {
            "name": "Winona",
            "keys": [MapRSE.FORTREE_CITY_GYM.value, MapRSE.FORTREE_CITY.value],
            "band": (29, 33),
            "ace_types": ("Dragon", "Flying"),
            "ace_level": 33,
            "heal": PokemonCenter.FortreeCity,
        }
        # AST cross-check: the replica must BE production literal (ki80ladder rule).
        try:
            src = _pathlib.Path(_sm.__file__).read_text(encoding="utf-8-sig")
            literal = None
            for node in _ast.walk(_ast.parse(src)):
                if (isinstance(node, _ast.Assign) and len(node.targets) == 1
                        and isinstance(node.targets[0], _ast.Name)
                        and node.targets[0].id == "winona_fight"
                        and isinstance(node.value, _ast.Dict)):
                    literal = node.value
                    break
            if literal is None:
                bad("could not find `winona_fight` in the source AST — the replica is UNVERIFIED")
            else:
                ast_keys = {k.value for k in literal.keys if isinstance(k, _ast.Constant)}
                if ast_keys != set(base_cfg):
                    bad("REPLICA DRIFT: winona_fight keys %s != %s"
                        % (sorted(ast_keys), sorted(base_cfg)))
        except Exception as error:  # noqa: BLE001
            bad("AST cross-check raised %s: %s" % (type(error).__name__, error))

        log(f"[{TAG}] party: {[(m.species.name, m.level) for m in get_party() if m is not None]}")

        TRIPWIRES = (
            ("PLAIN_ESCALATION", "training harder before"),
            ("BOSS_TRAINING_MODE", "boss-training mode"),
            ("ZERO_KO_FALLBACK", "boss attempts KO'd nothing"),
        )

        class _Tripped(Exception):
            pass

        real_console = _sm.console
        sink: list[str] = []

        class _Proxy:
            def __init__(self, real, s):
                self._real, self._sink = real, s

            def print(self, *a, **kw):
                text = " ".join(str(x) for x in a)
                self._sink.append(text)
                self._real.print(*a, **kw)
                for name, needle in TRIPWIRES:
                    if needle in text:
                        raise _Tripped(name)

        mode = _sm.StoryMode()
        key = MapRSE.FORTREE_CITY_GYM.value
        mode._defeat_counts[key] = 8
        mode._loss_ko_history[key] = [(i, 1) for i in range(1, 9)]
        mode._counter_hunts[key] = "seeded: consumed"

        hopeless_calls: list[bool] = []
        real_hopeless = mode._boss_plan_is_hopeless

        def hopeless_observer(cfg_arg, _real=real_hopeless):
            verdict = _real(cfg_arg)
            hopeless_calls.append(bool(verdict[0]))
            return verdict

        mode._boss_plan_is_hopeless = hopeless_observer
        _random.seed(2608)

        def one_cycle(label: str) -> tuple[str, str]:
            sink.clear()
            gen = mode._prepare_for_fight(dict(base_cfg))
            _sm.console = _Proxy(real_console, sink)
            outcome, detail = "UNSET", ""
            try:
                next(gen)
                outcome = "YIELDED_WITHOUT_DISCRIMINATING"
            except _Tripped as trip:
                outcome = str(trip)
            except BotModeError as error:
                outcome, detail = "RAISE", str(error)
            except StopIteration:
                emptied = not mode._loss_ko_history.get(key)
                # ⛔ BOTH state facts, directly (a Tier 1 risk note: grading on `emptied` alone
                # proved the marker only INDIRECTLY via B-REARM; assert it here too).
                marked = key in getattr(mode, "_second_winds", set())
                outcome = ("SECOND_WIND" if (emptied and marked)
                           else "RETURNED_WITHOUT_DISCRIMINATING")
                if emptied and not marked:
                    bad(f"{label}: history emptied but the wind marker is ABSENT — the fix's "
                        "check-then-write ordering is broken")
            except Exception as error:  # noqa: BLE001
                outcome, detail = "UNEXPECTED_%s" % type(error).__name__, str(error)
            finally:
                try:
                    gen.close()
                except Exception:  # noqa: BLE001 — closing must never mask the outcome
                    pass
                _sm.console = real_console
            witness = any("already hunted a counter" in s for s in sink)
            log(f"[{TAG}] {label}: {outcome}"
                + (" (%s)" % detail[:110] if detail else "")
                + f" hunt_witness={witness} history_len={len(mode._loss_ko_history.get(key) or [])}")
            if outcome == "RAISE":
                if "8 losses" not in detail and "16 losses" not in detail:
                    bad("%s: RAISE without production loss arithmetic — got %s" % (label, detail[:90]))
                if not witness:
                    bad("%s: RAISE without the ladder consumed-gate witness — the seed did not "
                        "take; the ladder may have actually hunted" % label)
            return outcome, detail

        # ---- PHASE A ----
        outcomes = [one_cycle("A%d" % i)[0] for i in range(1, 6)]
        if not hopeless_calls or not hopeless_calls[0]:
            bad("ANTI-VACUITY: hopeless was not True on cycle 1 — the anchor/seed no longer "
                "produces the raise regime; NOTHING below discriminates")

        # ---- PHASE B ----
        mode._loss_ko_history.setdefault(key, [])
        mode._loss_ko_history[key] += [(i, 1) for i in range(9, 17)]
        mode._defeat_counts[key] = 16
        b_outcome, _ = one_cycle("B-REARM")

        today = outcomes == ["RAISE"] * 5 and b_outcome == "RAISE"
        after = (outcomes[0] == "SECOND_WIND"
                 and outcomes[1:] == ["PLAIN_ESCALATION"] * 4
                 and b_outcome == "RAISE")
        log(f"[{TAG}] RESULT phaseA={outcomes} phaseB={b_outcome} "
            f"era={'TODAY' if today else 'AFTER' if after else 'NEITHER'}")
        if not (today or after):
            bad("outcomes match NEITHER computed era — the discriminator hand-trace is wrong "
                "or the code changed shape; investigate before any fix ships")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if not fails else 'FAIL'}"
            + ("" if not fails else " — %d problem(s): " % len(fails) + " | ".join(fails)))
        _ctx.set_manual_mode()
        return
        yield  # generator protocol


class Ch21DiveMode(BotMode):
    """§Ch21 LEG 1 — the dive into Sootopolis. Drives the PRODUCTION entry point.

    ‼ IT CALLS `modules.story.sootopolis.enter_sootopolis()`. Copying the leg's steps into this
    driver would prove the COPY works and tell us nothing about what `_play()` will run — the rule
    `boxwithdraw` earned and `ch20chapter` follows.

    ⛔ ACCEPTANCE IS NOT "we are in Sootopolis". It is "we are in Sootopolis AND THE BOT CAN
    CONTINUE" — three chapters in this project shipped stranded while passing their own tests.
    ‼ The CONTINUATION target was WRONG for two drives and is now measured: it is the POKE CENTER,
    not the Cave of Origin. The cave is unreachable on foot at every stage (Steven's escort warps you
    in), so asserting a path there graded the run against something the game does not provide.

    Anchor: `saves/post_ch20.ss1` (ROUTE128 (38,24), ROUTE128_STATE=2, SOOTOPOLIS_CITY_STATE=1).
    ⚠ That anchor has 1 FAINTED party member at 80% HP — the honest post-cavern state. An early
    whiteout here is the FIXTURE, not a leg-1 bug.

    Emits: [ch21dive] RESULT reached=<b> at=<tile> arrived=<b> cave_path=<b> state=<n>
        where `arrived` means SOOTOPOLIS_CITY_STATE >= 2 -- i.e. the arrival CUTSCENE finished, not
        merely that the map loaded. Drive 1 failed exactly there.
    """

    @staticmethod
    def name() -> str:
        return "Ch21Dive"

    def run(self):
        from modules.map_data import MapRSE
        from modules.map_path import calculate_path
        from modules.memory import get_event_var
        from modules.player import get_player_avatar
        from modules.story import sootopolis as ch21

        reached = False
        try:
            yield from ch21.enter_sootopolis()
            reached = True
        except Exception as error:  # noqa: BLE001 - a failure is a RESULT here, not a crash
            log(f"[ch21dive] LEG FAILED: {type(error).__name__}: {str(error)[:600]}")

        avatar = get_player_avatar()
        try:
            here_map = MapRSE(tuple(avatar.map_group_and_number))
            here_name = here_map.name
        except Exception:
            here_map, here_name = None, f"UNKNOWN{tuple(avatar.map_group_and_number)}"
        at = tuple(avatar.local_coordinates)
        in_city = here_map is MapRSE.SOOTOPOLIS_CITY
        try:
            state = get_event_var("SOOTOPOLIS_CITY_STATE")
        except Exception:
            state = "?"
        # ⛔ GRADE ON THE VAR, NOT ON THE MAP, AND NOT ON A PREDICTED TILE.
        # Drive 1 reported `reached=True at=SOOTOPOLIS_CITY(29,53) state=1` -- ON the map with the
        # arrival cutscene still running (`SootopolisCity_EventScript_LegendariesSceneFromDive` was
        # live at f18014). An acceptance of "are we in Sootopolis?" would have called that a PASS.
        # The scene warps the player, so the resting tile is the GAME's choice: REPORT it, never
        # assert a hard-coded prediction.
        arrived = in_city and isinstance(state, int) and state >= 2

        # ‼ "AND THE BOT CAN CONTINUE" -- AND THE FIRST VERSION OF THIS CHECK WAS WRONG.
        # Drive 1 and 2 asserted a walkable path to the Cave of Origin door (31,16). MEASURED from
        # `post_sootopolis_arrival.ss1`: the ENTIRE column (31,16)..(31,22) is unreachable, and so is
        # every other land target except the Poke Center. ⛔ AN EARLIER VERSION OF THIS COMMENT SAID
        # "ZERO NPCs loaded, so it is NOT the Expert body-block". THAT INFERENCE IS INVALID and a
        # Tier 1 review caught it: `get_map_objects()` is a CAMERA-RANGE WINDOW, and (29,53) is 30+
        # tiles from (31,18) -- an NPC there would not be loaded WHETHER OR NOT IT EXISTS.
        # ✅✅ THE CAUSE IS MEASURED NOW (2026-08-27, `--driver ch21leg2probe`) -- it is the
        # STEVEN (20,36) + BOY2 (19,37) TWO-TILE BODY-BLOCK through map_path's
        # loadedness-not-occupancy rule (`map_path.py:843-853`), NOT the Expert alone and NOT an
        # elevation rule (that guess is refuted). Proof = the flip: from (29,53) the column
        # refuses; from (21,36), with both NPCs camera-loaded, the SAME queries path --
        # (31,16) 98 wp, (31,22) 94 wp. (The old "52-tile island" figure here is UNVERIFIED --
        # the leg-2 spec measured ~350; re-derive before trusting either number.)
        # What settles the DESIGN is the decomp: Steven LEADS the player there
        # and his script ends `warp MAP_CAVE_OF_ORIGIN_ENTRANCE, 9, 20`. ⇒ THE GAME NEVER WALKS YOU
        # IN, so requiring a path there asserted something Pokemon Emerald does not provide.
        # ⛔ The bar is not being lowered: it is being pointed at the REAL next action. The party
        # arrives here with a FAINTED member (see this anchor's inventory row), so the bot's actual
        # next move is the Poke Center -- and THAT path is what must exist.
        center_path, center_detail = False, "not attempted (not in the city)"
        cave_path, cave_detail = False, "not attempted (not in the city)"
        if in_city:
            try:
                p_ = calculate_path((MapRSE.SOOTOPOLIS_CITY, at), (MapRSE.SOOTOPOLIS_CITY, (43, 31)))
                center_path, center_detail = True, f"OK {at} -> (43, 31), {len(p_)} waypoints"
            except Exception as perr:  # noqa: BLE001 - a failed probe is a RESULT
                center_detail = f"{type(perr).__name__}: {str(perr)[:160]}"
            try:
                calculate_path((MapRSE.SOOTOPOLIS_CITY, at), (MapRSE.SOOTOPOLIS_CITY, (31, 16)))
                cave_path, cave_detail = True, f"OK {at} -> (31, 16)"
            except Exception as perr:  # noqa: BLE001 - REPORTED, not graded; False is EXPECTED here
                cave_detail = f"{type(perr).__name__} (EXPECTED -- Steven warps you in)"

        log(f"[ch21dive] RESULT reached={reached} at={here_name}{at} arrived={arrived} "
            f"center_path={center_path} cave_path={cave_path} state={state}")
        log(f"[ch21dive] POKE-CENTER PATH {center_detail}")
        log(f"[ch21dive] CAVE-OF-ORIGIN PATH {cave_detail}")
        log("[ch21dive] ‼ cave_path=False is EXPECTED and is NOT graded. The cause is MEASURED "
            "(2026-08-27, --driver ch21leg2probe): the Steven(20,36)+Boy2(19,37) two-tile "
            "body-block via map_path's loadedness rule -- from (21,36) with both NPCs loaded the "
            "same queries PATH. What justifies not grading it is the DECOMP: Steven's escort ends "
            "`warp MAP_CAVE_OF_ORIGIN_ENTRANCE, 9, 20`, so the bot is never required to walk there.")
        passed = reached and arrived and center_path
        log(f"[ch21dive] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")

        # ‼ CAPTURE ON `arrived`, NOT ON `passed` -- and the difference is deliberate.
        # `CH20_CAPTURE` writes only on full acceptance because §Ch20's acceptance IS its end state.
        # Here, `arrived` (in the city, SOOTOPOLIS_CITY_STATE >= 2, cutscene finished) is already a
        # well-defined, controllable, reproducible state worth pinning -- while `cave_path` is a
        # CONTINUATION check for a leg that is not built yet and whose premise is under review (the
        # Cave of Origin entrance is NPC-body-blocked until Steven's escort, and Steven WARPS you in,
        # so a walkable path to (31,16) may never be required at all).
        # ⛔ Refusing to capture until an unrelated check passes would deny leg 2 its fixture.
        _cap = _os.environ.get("CH21_CAPTURE", "").strip()
        if _cap:
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not arrived:
                log(f"[ch21dive] CAPTURE SKIPPED -- not arrived (state={state}); refusing to write {_cap}")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[ch21dive] CAPTURE REFUSED -- {_cap} exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[ch21dive] CAPTURE WROTE {_out.name} ({_out.stat().st_size} bytes) at {at} "
                    f"state={state} -- ‼ verify with probe_anchor_inventory.py, not this line")

        context.set_manual_mode()


class Ch21Leg2ProbeMode(BotMode):
    """§Ch21 LEG 2 — the PRE-BUILD probes (§4.1/4.2/4.4/4.5/4.6 of the leg-2 build spec).

    ‼ WHY THIS EXISTS BEFORE ANY ESCORT CODE: every reachability number in
    `ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md` is a RE-IMPLEMENTATION of the tile
    model, not the bot's own `calculate_path` — three agents agreeing is corroboration, not
    measurement (this project's measured rule). The spec's own instruction is that these probes
    run FIRST. The driver walks exactly ONE leg (arrival tile → (21,36)) and otherwise only reads.

    ⛔ PREDICTIONS FILED FIRST (the §Ch20 cavern method), from the spec:
      P1 (§4.1)  guides=False hide_steven=False state=2. `guides=True` = leg 2a ALREADY SPENT —
                 a RESULT that changes the whole spec, not a crash.
      P2 (§4.2a) from the arrival tile: get_map_objects() lists NO Steven (camera window);
                 paths: (21,36) OK, (20,37) OK, (43,31) OK;
                 (20,36)/(19,36)/(20,35)/(31,22)/(31,16) all REFUSE.
      P3 (§4.2b) from (21,36): Steven LOADED at (20,36), Boy2 at (19,37), AND (31,22) now
                 PATHS — the body-block FLIP, the dossier's sharpest discriminator. If it
                 flips, the §0.4 doc corrections (harness comment + 12-STORYMODE:3657) are OWED
                 IN THE SAME COMMIT as this probe's results.
      P4 (§4.4)  arrival facing at (21,36): UNPREDICTED (two tiles tie at distance) — record it,
                 plus whether the surf-exit left a WALKING avatar.
      P5 (§4.6)  the brief's party line ("fainted at 54%") is internally inconsistent — record
                 real (pid, species, hp/total) tuples. IDENTITY, never slot or count.
      P6 (§4.5)  Steven's numeric local_id read LIVE from (21,36) — it is INFERRED as 7 in the
                 spec and must never be hard-coded from that inference.

    ACCEPTANCE = the PRECONDITIONS hold (SOOTOPOLIS_CITY, state==2, controllable — else the run
    is VACUOUS and says so) AND every probe EXECUTED to a reading. ⛔ A reading that contradicts
    a prediction is a RESULT to report, never a driver failure — reality cannot "fail" a probe;
    only not-measuring can.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_sootopolis_arrival.ss1 --driver ch21leg2probe
    """

    @staticmethod
    def name() -> str:
        return "Ch21Leg2Probe"

    def run(self):
        from modules.map import get_map_objects
        from modules.map_data import MapRSE
        from modules.map_path import calculate_path
        from modules.memory import get_event_flag, get_event_var
        from modules.modes.util.walking import navigate_to
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party

        TAG = "ch21leg2probe"
        probes_run: list[str] = []

        def path_matrix(label: str) -> None:
            at = tuple(get_player_avatar().local_coordinates)
            for t in [(20, 36), (21, 36), (20, 37), (19, 36), (20, 35), (31, 22), (31, 16), (43, 31)]:
                try:
                    p = calculate_path((MapRSE.SOOTOPOLIS_CITY, at), (MapRSE.SOOTOPOLIS_CITY, t))
                    log(f"[{TAG}] P-{label} {at}->{t} OK {len(p)} wp")
                except Exception as perr:  # noqa: BLE001 - a refusal IS the reading here
                    log(f"[{TAG}] P-{label} {at}->{t} {type(perr).__name__}")

        def objects(label: str) -> list[tuple[int, tuple[int, int]]]:
            got = [(o.local_id, tuple(o.current_coords)) for o in get_map_objects()]
            log(f"[{TAG}] OBJ-{label} {got}")
            return got

        # ---- PRECONDITIONS (anti-vacuity: a probe on the wrong state measures nothing) ----
        # ‼ SETTLE FIRST — the smoke test measured `controllable=False` at frame 0 on the pinned
        # fixture: a freshly loaded save state needs frames before the avatar answers. Bounded,
        # loud on timeout (the helper raises), and the same call the escort build will open with.
        from modules.story.early_game import wait_until_truly_controllable

        yield from wait_until_truly_controllable()

        avatar = get_player_avatar()
        try:
            here = MapRSE(tuple(avatar.map_group_and_number))
        except Exception:  # noqa: BLE001 - report the raw tuple rather than crash pre-reading
            here = None
        state = get_event_var("SOOTOPOLIS_CITY_STATE")
        if here is not MapRSE.SOOTOPOLIS_CITY or state != 2 or not player_avatar_is_controllable():
            log(f"[{TAG}] ‼ VACUOUS: map={here} state={state} "
                f"controllable={player_avatar_is_controllable()} — fixture is not the spec's premise")
            log(f"[{TAG}] ACCEPTANCE: FAIL")
            context.set_manual_mode()
            return

        # ---- P1 — flags (§4.1). Names verified against modules/data/event_flags/emerald.txt
        # in the spec; a MISSPELLED name reads False forever (memory.py:336), so this probe's
        # commit must run audit_flag_names.py (standing gate does).
        guides = get_event_flag("STEVEN_GUIDES_TO_CAVE_OF_ORIGIN")
        hide_steven = get_event_flag("HIDE_SOOTOPOLIS_CITY_STEVEN")
        log(f"[{TAG}] P1 guides={guides} hide_steven={hide_steven} state={state} "
            f"(PREDICTED False/False/2)")
        probes_run.append("P1")
        if guides:
            log(f"[{TAG}] ‼ P1 RESULT: leg 2a is ALREADY SPENT on this fixture — the spec's "
                f"Steven position and the escort plan DO NOT APPLY. Stop and re-plan.")
            log(f"[{TAG}] ACCEPTANCE: PASS (probe measured; the RESULT changes the build)")
            context.set_manual_mode()
            return

        # ---- P5 — the party, by IDENTITY (§4.6) ----
        party = [(m.personality_value, m.species.name, m.current_hp, m.total_hp)
                 for m in get_party() if m is not None]
        log(f"[{TAG}] P5 party={party}")
        probes_run.append("P5")

        # ---- P2 — objects + path matrix from the ARRIVAL tile (§4.2a) ----
        objects("arrival")
        path_matrix("arrival")
        probes_run.append("P2")

        # ---- the one walk: arrival -> (21,36) (§4.3 — the load-bearing precondition of the
        # whole escort step, measured by the bot's OWN planner+walker, not a re-implementation) ----
        walked = False
        try:
            yield from navigate_to(MapRSE.SOOTOPOLIS_CITY, (21, 36))
            walked = True
        except Exception as error:  # noqa: BLE001 - a refusal/timeout is a RESULT
            log(f"[{TAG}] ‼ WALK FAILED: {type(error).__name__}: {str(error)[:300]}")

        avatar = get_player_avatar()
        at = tuple(avatar.local_coordinates)
        # P4 — facing + locomotion state on arrival (§4.4)
        log(f"[{TAG}] P4 walked={walked} at={at} facing={avatar.facing_direction} "
            f"controllable={player_avatar_is_controllable()}")
        probes_run.append("P4")

        if walked and at == (21, 36):
            # ---- P3 — the FLIP (§4.2b) + P6 — Steven's live local_id (§4.5) ----
            got = objects("at-21-36")
            steven = [lid for lid, coords in got if coords == (20, 36)]
            log(f"[{TAG}] P3 steven_loaded={bool(steven)} "
                f"P6 steven_local_id={steven[0] if steven else None} "
                f"boy2_at_19_37={any(c == (19, 37) for _, c in got)} (PREDICTED True/?/True)")
            path_matrix("at-21-36")
            probes_run.extend(["P3", "P6"])
        else:
            log(f"[{TAG}] ‼ P3/P6 NOT REACHED — the walk did not land on (21,36); the readings "
                f"above are still valid, the flip test is not run")

        # ---- OPTIONAL P7 (§4.7, CH21_HEAL_PROBE=1) — where does `heal_in_pokemon_center`
        # leave the bot on a PC NOBODY has driven, do its three piggyback blocks behave, and
        # does the post-heal tile path back to the Steven approach? Needs the §0.1 enum member
        # (`PokemonCenter.SootopolisCity`, added 2026-08-27). Runs AFTER the flip test on
        # purpose: the flip needs the pristine un-walked city, the heal does not.
        if _os.environ.get("CH21_HEAL_PROBE", "").strip() == "1":
            from modules.map_data import PokemonCenter
            from modules.modes.util.higher_level_actions import heal_in_pokemon_center

            healed = False
            try:
                yield from heal_in_pokemon_center(PokemonCenter.SootopolisCity)
                healed = True
            except Exception as error:  # noqa: BLE001 - a failed heal is a RESULT
                log(f"[{TAG}] ‼ HEAL RAISED: {type(error).__name__}: {str(error)[:300]}")
            avatar = get_player_avatar()
            post = tuple(avatar.local_coordinates)
            try:
                post_map = MapRSE(tuple(avatar.map_group_and_number)).name
            except Exception:  # noqa: BLE001
                post_map = str(tuple(avatar.map_group_and_number))
            party_after = [(m.personality_value, m.species.name, m.current_hp, m.total_hp)
                           for m in get_party() if m is not None]
            all_full = all(hp == total for _, _, hp, total in party_after)
            log(f"[{TAG}] P7 healed={healed} post={post_map}{post} all_full_hp={all_full} "
                f"party={party_after}")
            if post_map == "SOOTOPOLIS_CITY":
                try:
                    p = calculate_path((MapRSE.SOOTOPOLIS_CITY, post),
                                       (MapRSE.SOOTOPOLIS_CITY, (21, 36)))
                    log(f"[{TAG}] P7 path post-heal->(21,36) OK {len(p)} wp")
                except Exception as perr:  # noqa: BLE001 - a refusal IS the reading
                    log(f"[{TAG}] P7 path post-heal->(21,36) "
                        f"{type(perr).__name__}: {str(perr)[:160]}")
            probes_run.append("P7")

        done = set(probes_run)
        passed = {"P1", "P2", "P4", "P5"}.issubset(done)
        log(f"[{TAG}] probes run: {sorted(done)} (P3/P6 conditional on the walk)")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        context.set_manual_mode()


class Ch21EscortMode(BotMode):
    """§Ch21 LEG 2a — Steven's escort. Drives the PRODUCTION `sootopolis.steven_escort()`.

    ‼ IT CALLS THE PRODUCTION ENTRY POINT (the `boxwithdraw`/`ch21dive` rule): a copy would prove
    the copy. Every precondition was measured first by `--driver ch21leg2probe` (2026-08-27):
    heal proven on this exact PC, both approach tiles pathed by the real planner, arrival facing
    Left = a handled branch, Steven live at (20,36) local_id 7.

    ACCEPTANCE = the leg-2 spec §2 predicate, re-read HERE (never trusting the module's own
    message): `STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` AND on CAVE_OF_ORIGIN_ENTRANCE AND controllable.
    Also REPORTS (not asserts): the landing tile (decomp says (9,20)), the escort frame cost
    (§4.8 — the budget was a guess of 30000; replace it with this measurement), and the party
    by PID after the ride.

    ⛔ THE ESCORT IS ONE-SHOT PER SAVE (spec §3.1). A FAILED run may still have consumed it
    (flag set, warp missed) — the RESULT line prints the flag either way; if flag=True without
    arrival, DO NOT re-drive from the same in-memory state: reload the fixture.

    Capture: CH21_CAPTURE=<name>.ss1 writes saves/<name> ON FULL ACCEPTANCE ONLY — this leg's
    end state IS the seam fixture leg 2b starts from (`post_steven_escort.ss1` by convention).

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_sootopolis_arrival.ss1 --driver ch21escort
    """

    @staticmethod
    def name() -> str:
        return "Ch21Escort"

    def run(self):
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party
        from modules.story import sootopolis as ch21

        TAG = "ch21escort"
        frame_before = context.emulator.get_frame_count()
        reached = False
        try:
            yield from ch21.steven_escort()
            reached = True
        except Exception as error:  # noqa: BLE001 - a failure is a RESULT here, not a crash
            log(f"[{TAG}] LEG FAILED: {type(error).__name__}: {str(error)[:600]}")
        frames_spent = context.emulator.get_frame_count() - frame_before

        avatar = get_player_avatar()
        at = tuple(avatar.local_coordinates)
        try:
            here_name = MapRSE(tuple(avatar.map_group_and_number)).name
        except Exception:  # noqa: BLE001
            here_name = f"UNKNOWN{tuple(avatar.map_group_and_number)}"
        flag = get_event_flag("STEVEN_GUIDES_TO_CAVE_OF_ORIGIN")
        on_entrance = here_name == "CAVE_OF_ORIGIN_ENTRANCE"
        controllable = player_avatar_is_controllable()
        state = get_event_var("SOOTOPOLIS_CITY_STATE")
        party = [(m.personality_value, m.species.name, m.current_hp, m.total_hp)
                 for m in get_party() if m is not None]
        passed = reached and flag and on_entrance and controllable

        log(f"[{TAG}] RESULT reached={reached} flag={flag} at={here_name}{at} "
            f"controllable={controllable} state={state} frames={frames_spent}")
        log(f"[{TAG}] party after: {party}")
        log(f"[{TAG}] landing tile: decomp predicts (9,20); measured {at} — if these differ, "
            f"correct the SPEC, not the game")
        if flag and not passed:
            log(f"[{TAG}] ‼ THE ESCORT IS CONSUMED (flag set) WITHOUT FULL ACCEPTANCE — "
                f"do NOT re-drive this save state; reload the fixture.")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")

        _cap = _os.environ.get("CH21_CAPTURE", "").strip()
        if _cap:
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not passed:
                log(f"[{TAG}] CAPTURE SKIPPED — not accepted; refusing to write {_cap}")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[{TAG}] CAPTURE REFUSED — {_cap} exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[{TAG}] CAPTURE WROTE {_out.name} ({_out.stat().st_size} bytes) at {at} "
                    f"— ‼ verify with probe_anchor_inventory.py, not this line")

        context.set_manual_mode()


class Ch21CaveMode(BotMode):
    """§Ch21 LEG 2b — the Cave of Origin descent + Wallace. Drives PRODUCTION `cave_of_origin()`.

    Anchor: `saves/post_steven_escort.ss1` (PINNED — Entrance (9,20), escort flag set, state 2,
    party 100%). ACCEPTANCE = the leg-2 spec §2 leg-2b predicate re-read HERE:
    `SOOTOPOLIS_CITY_STATE == 3` AND `WALLACE_GOES_TO_SKY_PILLAR` — never Wallace's absence,
    never the chapter flag. Also REPORTS: the end tile (the script has `release`, NO warp — the
    bot stays on B1F), whether Wallace's object is gone (expected — `removeobject` hides him
    permanently) and the frame cost. ⚠ It does NOT count wild encounters: an earlier version of
    this line claimed it did (spec §4.10) and no such code was ever written, which is why §4.10
    stayed OPEN. `--driver ch21pocket` counts them properly, via the `on_battle_started` hook.

    Fault arm (spec §4.9): POKEBOT_CH21_FAULT_WRONGANSWER=1 answers index 0 once — proves the
    wrong-answer RE-ARM is detected (attempt 2) and recovered to state 3.

    Capture: CH21_CAPTURE=<name>.ss1 writes saves/<name> on FULL ACCEPTANCE — the leg-3 fixture
    (`post_wallace.ss1` by convention; leg 3 opens with the pocket-exit PROBE, spec §3.4/§5).

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_steven_escort.ss1 --driver ch21cave
    """

    @staticmethod
    def name() -> str:
        return "Ch21Cave"

    def run(self):
        from modules.map import get_map_objects
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.story import sootopolis as ch21

        TAG = "ch21cave"
        frame_before = context.emulator.get_frame_count()
        reached = False
        try:
            yield from ch21.cave_of_origin()
            reached = True
        except Exception as error:  # noqa: BLE001 - a failure is a RESULT here, not a crash
            log(f"[{TAG}] LEG FAILED: {type(error).__name__}: {str(error)[:600]}")
        frames_spent = context.emulator.get_frame_count() - frame_before

        avatar = get_player_avatar()
        at = tuple(avatar.local_coordinates)
        try:
            here_name = MapRSE(tuple(avatar.map_group_and_number)).name
        except Exception:  # noqa: BLE001
            here_name = f"UNKNOWN{tuple(avatar.map_group_and_number)}"
        state = get_event_var("SOOTOPOLIS_CITY_STATE")
        flag = get_event_flag("WALLACE_GOES_TO_SKY_PILLAR")
        passed = reached and state == 3 and flag
        wallace_visible = any(
            tuple(o.current_coords) == (9, 13) for o in get_map_objects()
        ) if here_name == "CAVE_OF_ORIGIN_B1F" else None

        log(f"[{TAG}] RESULT reached={reached} state={state} wallace_flag={flag} "
            f"at={here_name}{at} controllable={player_avatar_is_controllable()} "
            f"frames={frames_spent}")
        log(f"[{TAG}] wallace_object_still_visible={wallace_visible} (expected False after "
            f"success — removeobject hides him PERMANENTLY; his absence is never the grade)")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")

        _cap = _os.environ.get("CH21_CAPTURE", "").strip()
        if _cap:
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not passed:
                log(f"[{TAG}] CAPTURE SKIPPED — not accepted; refusing to write {_cap}")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[{TAG}] CAPTURE REFUSED — {_cap} exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[{TAG}] CAPTURE WROTE {_out.name} ({_out.stat().st_size} bytes) at {at} "
                    f"— ‼ verify with probe_anchor_inventory.py, not this line")

        context.set_manual_mode()


class Ch21PocketExitMode(BotMode):
    """§Ch21 LEG 3, STEP 0 — THE POCKET-EXIT PROBE. A MEASUREMENT, NOT A BUILD.

    ‼ The handoff queue opens leg 3 with this probe because spec §3.4/§5 call the walk back out
    of the Sootopolis pocket "the single largest un-measured risk in this whole area". The STATIC
    half is already settled by `probe_ch21_pocket_exit.py` (run it first — it is seconds, this is
    minutes) with four passing controls:
      * the (9,20) exit warp lands on SOOTOPOLIS_CITY (31,16)   [ROM warp table, control-checked]
      * from (31,16) with NOTHING loaded the pocket is SEALED   [(43,31)/(29,53)/(21,36) refuse]
      * marking Steven loaded at his state-3 tile (32,18) OPENS it, 123 wp to the Poke Center
      * 90 of the 122 city waypoints on that route are RE-PLAN-FATAL — a forced re-plan taken
        anywhere in the first 90 refuses, and the first safe waypoint is (20,36) itself.

    ⇒ WHAT ONLY A DRIVE CAN ADD, and therefore all this probe is for:
      L1  §4.11 LIVE — does the (9,20) warp really land the AVATAR on (31,16)? (ROM-read, never
          observed; the spec calls it "leg 3's first fact".)
      L2  §4.10 — wild-encounter pressure over the 61-waypoint return. Counted via the
          `on_battle_started` HOOK, not by polling: a driver generator does not get frames during
          a battle, so a poll could never have answered positive (playbook §0b Q4).
      L3  the LIVE optimistic arm — standing on (31,16), with Steven genuinely loaded at (32,18),
          does `calculate_path` out of the pocket succeed, and at what cost?
      L4  does the walk-out actually COMPLETE? ⛔ It is driven with `follow_waypoints` over a
          path computed ONCE, never `navigate_to`: `navigate_to`'s outer loop restarts a FRESH
          plan on a waypoint timeout, and a fresh plan taken inside the danger zone refuses.
          That choice is the whole point of the measurement — see `POKEBOT_CH21_POCKET_ARM`.

    ARMS (`POKEBOT_CH21_POCKET_ARM`, default `follow`):
      follow    compute once at (31,16), then `follow_waypoints` — the SAFE design under test.
      navigate  a single `navigate_to(SOOTOPOLIS_CITY, (43,31))` — the NAIVE design. Kept so the
                two designs can be compared on the same fixture. ⚠ Expected to work MOST of the
                time (nothing forces a re-plan on a clean run), so a PASS here is NOT evidence
                the naive design is safe — the danger is a tail risk, and one trajectory is a
                determinism check, never a replication.

    ⚠ HONEST PRIOR, recorded so a PASS is not over-read: this walk has ALREADY been done live
    once, by accident. The escort-v1 bug (2026-08-27) rode past its bail, pathed back through the
    (9,20) warp and ended at SOOTOPOLIS_CITY (20,37) — the far side of the choke — at state 2,
    where `SetEnterCaveOfOriginObjPos` has placed Steven identically to state 3. Its route was
    never logged, so it corroborates rather than proves.

    ACCEPTANCE = the preconditions hold (else the run is VACUOUS and says so) AND every leg
    EXECUTED to a reading. ⛔ A reading that contradicts a prediction is a RESULT, never a driver
    failure — reality cannot fail a probe; only not-measuring can.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21pocket
    """

    @staticmethod
    def name() -> str:
        return "Ch21PocketExit"

    def __init__(self):
        super().__init__()
        # ‼ INSTRUMENT THE ACTION, NOT THE INPUT. This counts battles the game actually STARTED.
        self.encounters = 0
        self.encounter_maps: list[str] = []
        # ⛔ A WHITEOUT WOULD SILENTLY CONVERT THIS PROBE INTO A MEASUREMENT OF THE RESPAWN POINT
        # — the landing/pocket readings would then describe a Poke Center, not the cave exit, and
        # every number below would be about the wrong place. Latch it and FAIL on it.
        self.whiteouts = 0

    def on_whiteout(self) -> bool:
        self.whiteouts += 1
        log("[ch21pocket] ‼ WHITEOUT — every reading after this point is about the RESPAWN "
            "point, not the cave exit. ACCEPTANCE fails on this.")
        return False

    def on_battle_started(self, encounter):
        self.encounters += 1
        try:
            from modules.player import get_player_avatar

            self.encounter_maps.append(str(tuple(get_player_avatar().map_group_and_number)))
        except Exception:  # noqa: BLE001 - the count is what matters; the map is a nicety
            self.encounter_maps.append("?")
        return super().on_battle_started(encounter)

    def run(self):
        from modules.map import get_map_objects
        from modules.map_data import MapRSE
        from modules.map_path import calculate_path
        from modules.memory import get_event_flag, get_event_var
        from modules.modes.util.walking import follow_waypoints, navigate_to
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable

        TAG = "ch21pocket"
        ARM = _os.environ.get("POKEBOT_CH21_POCKET_ARM", "follow").strip() or "follow"
        WARP_TARGET = (31, 16)   # the warp EVENT tile, per the ROM table and the decomp
        LANDING = (31, 17)       # ⛔ where the avatar RESTS — MEASURED 2026-08-27. v1 graded on
                                 # WARP_TARGET and therefore printed `landing_ok=False` on a
                                 # perfectly CORRECT run; an adversarial review caught it.
        PC_FRONT = (43, 32)      # ⛔ NOT (43,31): that is the Poke Center DOOR, a warp tile, and
                                 # `calculate_path` follows a warp when it IS the destination — so
                                 # v1 ended INSIDE the building, which silently skipped the
                                 # "and the bot can continue" check while ACCEPTANCE still said PASS.
        legs_done: list[str] = []
        readings: list[str] = []

        def where() -> tuple[str, tuple[int, int]]:
            avatar = get_player_avatar()
            try:
                name = MapRSE(tuple(avatar.map_group_and_number)).name
            except Exception:  # noqa: BLE001
                name = f"UNKNOWN{tuple(avatar.map_group_and_number)}"
            return name, tuple(avatar.local_coordinates)

        def matrix(label: str, source: tuple[int, int] | None = None) -> None:
            # ‼ THE CUT TILES ARE TARGETS ON PURPOSE: without them a refusal cannot be ATTRIBUTED.
            # `source` may be pinned so two matrices differ in ONE variable (loadedness), not two.
            at = source if source is not None else where()[1]
            readings.append(f"M-{label}")
            for target in [PC_FRONT, (29, 53), (21, 36), (20, 36), (19, 37), (31, 22)]:
                try:
                    path = calculate_path((MapRSE.SOOTOPOLIS_CITY, at),
                                          (MapRSE.SOOTOPOLIS_CITY, target))
                    log(f"[{TAG}] M-{label} {at}->{target} OK {len(path)} wp")
                except Exception as error:  # noqa: BLE001 - a refusal IS the reading
                    log(f"[{TAG}] M-{label} {at}->{target} {type(error).__name__}")

        yield from wait_until_truly_controllable()

        # ---- PRECONDITIONS (anti-vacuity: a probe on the wrong era measures nothing) ----
        here, at = where()
        state = get_event_var("SOOTOPOLIS_CITY_STATE")
        wallace = get_event_flag("WALLACE_GOES_TO_SKY_PILLAR")
        log(f"[{TAG}] PRE at={here}{at} state={state} wallace_flag={wallace} arm={ARM}")
        if here != "CAVE_OF_ORIGIN_B1F" or state != 3 or not wallace:
            log(f"[{TAG}] ‼ VACUOUS: fixture is not leg 3's premise (expected CAVE_OF_ORIGIN_B1F, "
                f"state 3, WALLACE_GOES_TO_SKY_PILLAR set)")
            log(f"[{TAG}] ACCEPTANCE: FAIL")
            context.set_manual_mode()
            return

        frame0 = context.emulator.get_frame_count()

        # ‼ THE PESSIMISTIC ARM, TAKEN FOR FREE BEFORE WE LEAVE. Standing on B1F, NO Sootopolis
        # object can be camera-loaded, so this is the "nothing loaded" regime the static probe
        # models — measured here rather than assumed. An adversarial review pointed out that the
        # near-arm ALONE is guaranteed to say "the pocket is open" and so proves nothing on its own.
        pre = [(o.local_id, tuple(o.current_coords)) for o in get_map_objects()]
        log(f"[{TAG}] L0 FAR ARM from B1F — objects loaded: {pre} "
            f"(player-only expected: {len(pre) == 1})")
        for target in [PC_FRONT, (29, 53)]:
            try:
                n = len(calculate_path((MapRSE.SOOTOPOLIS_CITY, LANDING),
                                       (MapRSE.SOOTOPOLIS_CITY, target)))
                log(f"[{TAG}] L0 far {LANDING}->{target} OK {n} wp — ‼ UNEXPECTED: the pocket "
                    f"reads OPEN with nothing loaded")
            except Exception as error:  # noqa: BLE001 - the refusal IS the expected reading
                log(f"[{TAG}] L0 far {LANDING}->{target} {type(error).__name__} "
                    f"(expected: the pocket is SEALED when Steven is unloaded)")
        readings.append("L0")

        # ---- L1/L2 — the intra-cave return, one warp at a time. `calculate_path` does NOT span
        # maps (measured: it raises "Source and destination are ..."), so this MUST be per-map.
        # Static waypoint counts, for comparison: 21 / 24 / 16.
        for label, src_map, warp_tile, want_map in [
            ("B1F->1F", MapRSE.CAVE_OF_ORIGIN_B1F, (9, 3), "CAVE_OF_ORIGIN_1F"),
            ("1F->ENTR", MapRSE.CAVE_OF_ORIGIN_1F, (11, 17), "CAVE_OF_ORIGIN_ENTRANCE"),
            ("ENTR->CITY", MapRSE.CAVE_OF_ORIGIN_ENTRANCE, (9, 20), "SOOTOPOLIS_CITY"),
        ]:
            before = context.emulator.get_frame_count()
            try:
                yield from _navigate_riding_out(src_map, warp_tile, tries=6)
            except Exception as error:  # noqa: BLE001 - a failure is a RESULT
                log(f"[{TAG}] ‼ LEG {label} FAILED: {type(error).__name__}: {str(error)[:300]}")
                log(f"[{TAG}] ACCEPTANCE: FAIL")
                context.set_manual_mode()
                return
            name, tile = where()
            spent = context.emulator.get_frame_count() - before
            log(f"[{TAG}] L1 {label}: landed {name}{tile} frames={spent} "
                f"encounters_so_far={self.encounters} (expected map {want_map})")
            legs_done.append(label)
            if name != want_map:
                log(f"[{TAG}] ‼ L1 {label} landed on the WRONG MAP — stopping; the readings above "
                    f"stand, the ones below are not run")
                log(f"[{TAG}] ACCEPTANCE: FAIL")
                context.set_manual_mode()
                return

        # ---- §4.11, LIVE. The tile the ROM warp table says is (31,16), never before observed. ----
        name, landed = where()
        # ⛔ A WARP TABLE GIVES THE WARP *EVENT* TILE, NOT WHERE THE AVATAR COMES TO REST.
        # Measured 2026-08-27: two of the three return warps auto-step the player one tile clear
        # of the doorway ((9,5)->rests (9,6); (31,16)->rests (31,17)) while B1F->1F does not
        # ((14,5) exactly). So a MISMATCH here is NOT the ROM read being wrong — it is the
        # door-exit step, and it is exactly the fact no table or decomp JSON can supply.
        log(f"[{TAG}] ‼ L1/§4.11 RESTING TILE (LIVE): {name}{landed} — warp-table target is "
            f"{WARP_TARGET}, MEASURED resting tile is {LANDING}: "
            f"{'MATCHES the measured expectation' if landed == LANDING else 'DIFFERS FROM BOTH — re-measure'}"
            f" ⇒ ⛔ leg 3 keys on the RESTING tile, never on the warp target")

        # ---- L3 — the LIVE optimistic arm: is the pocket open with Steven genuinely loaded? ----
        objects = [(o.local_id, tuple(o.current_coords)) for o in get_map_objects()]
        log(f"[{TAG}] L3 objects loaded at the landing tile: {objects}")
        log(f"[{TAG}] L3 steven(7) loaded={any(lid == 7 for lid, _ in objects)} "
            f"(static prediction: loaded at (32,18), which OPENS the pocket)")
        matrix("landing", source=landed)

        # ---- L4 — does the walk out COMPLETE? ----
        walked = False
        planned = None
        before = context.emulator.get_frame_count()
        try:
            if ARM == "navigate":
                yield from navigate_to(MapRSE.SOOTOPOLIS_CITY, PC_FRONT)
            else:
                # ⛔ COMPUTE ONCE, HERE, WHERE STEVEN IS LOADED — then follow it blind.
                # `follow_waypoints` raises on a per-waypoint timeout but NEVER re-plans, which is
                # exactly the property the 90-waypoint danger zone requires.
                path = calculate_path((MapRSE.SOOTOPOLIS_CITY, landed),
                                      (MapRSE.SOOTOPOLIS_CITY, PC_FRONT))
                planned = len(path)
                log(f"[{TAG}] L4 planned {planned} waypoints at the landing tile, "
                    f"following them WITHOUT re-planning")
                yield from follow_waypoints(path)
            walked = True
        except Exception as error:  # noqa: BLE001 - a failure is the RESULT this probe exists for
            log(f"[{TAG}] ‼ L4 WALK-OUT FAILED ({ARM}): {type(error).__name__}: {str(error)[:300]}")

        name, final = where()
        spent = context.emulator.get_frame_count() - before
        log(f"[{TAG}] L4 arm={ARM} walked={walked} planned={planned} end={name}{final} "
            f"frames={spent} controllable={player_avatar_is_controllable()}")
        legs_done.append("L4")

        # ---- and can it CONTINUE? (the §Ch15/18/19 rule: a leg that ends stranded still passes
        # its own test unless you ask for a REAL path off the end tile) ----
        if name == "SOOTOPOLIS_CITY":
            matrix("end")
        else:
            log(f"[{TAG}] ‼ M-end NOT RUN — the run ended on {name}, not SOOTOPOLIS_CITY, so the "
                f"'can it continue?' question cannot be asked here. This is a MISSING READING, and "
                f"ACCEPTANCE below fails on it rather than passing in silence.")

        # ---- OPTIONAL L5 (CH21_LAYOUT_PROBE=1) — IS THE PLANNER BLIND TO RUNTIME LAYOUT SWAPS?
        # §3.8 says the planner reads the STATIC ROM layout while the game swaps Sootopolis to
        # LAYOUT_SOOTOPOLIS_CITY_LEGENDS_BATTLE at states 1-4. In Sootopolis that was measured
        # BENIGN (28 differing blocks, all in the arena). On the SKY PILLAR it would be
        # LOAD-BEARING: production reads 38 cracked tiles on 2F and 34 on 4F while the atlas's
        # *_Clean measurements say 2F has ZERO. ‼ THE "NO crack-free route" READING THAT STOOD
        # HERE WAS REFUTED 2026-08-27 as an answer to the WRONG QUESTION: those are the POST-GAME
        # cracks, and the story runs on CLEAN, where every leg HAS a crack-free route.
        # This settles the general question on a map we can actually stand on.
        # `get_map_data_for_current_position()` reads the LIVE `gMapHeader` (map.py:1750);
        # `get_map_data(map, coords)` reads the STATIC ROM header (map.py:751). If their layout
        # bytes differ HERE, the planner is blind to swaps everywhere.
        if _os.environ.get("CH21_LAYOUT_PROBE", "").strip() == "1" and name == "SOOTOPOLIS_CITY":
            from modules.map import get_map_data, get_map_data_for_current_position

            try:
                live = get_map_data_for_current_position()
                static = get_map_data(MapRSE.SOOTOPOLIS_CITY, final)
                live_l = getattr(live, "_map_layout", None)
                static_l = getattr(static, "_map_layout", None)
                same = bytes(live_l) == bytes(static_l) if (live_l and static_l) else None
                log(f"[{TAG}] L5 LAYOUT live_size={getattr(live, 'map_size', '?')} "
                    f"static_size={getattr(static, 'map_size', '?')} layout_bytes_equal={same} "
                    f"state={get_event_var('SOOTOPOLIS_CITY_STATE')}")
                log(f"[{TAG}] L5 ⇒ {'PLANNER IS BLIND to the runtime swap' if same is False else 'no swap detected at this state'}"
                    f" — ⛔ read narrowly: this is ONE map at ONE state.")
            except Exception as error:  # noqa: BLE001 - a failed diagnostic is a RESULT
                log(f"[{TAG}] L5 LAYOUT PROBE RAISED: {type(error).__name__}: {str(error)[:200]}")
            readings.append("L5")

        total = context.emulator.get_frame_count() - frame0
        log(f"[{TAG}] L2/§4.10 ENCOUNTERS over the whole return: {self.encounters} "
            f"(maps: {self.encounter_maps}) — count it as pressure, never as a rate")
        log(f"[{TAG}] RESULT legs={legs_done} landing={landed} landing_ok={landed == LANDING} "
            f"walked_out={walked} end={name}{final} encounters={self.encounters} "
            f"whiteouts={self.whiteouts} frames={total}")
        # ⛔ THE GRADE ENUMERATES THE READINGS THAT ACTUALLY HAPPENED. v1 counted `legs_done`,
        # which appended "L4" unconditionally — so it passed even when the end-matrix was silently
        # skipped because the bot had walked into a building. A grade must assert something the run
        # does not already satisfy.
        required = {"L0", "M-landing", "M-end"}
        got = set(readings)
        missing = sorted(required - got)
        ok = not missing and len(legs_done) >= 3 and self.whiteouts == 0
        log(f"[{TAG}] readings={sorted(got)} missing={missing} "
            f"(the grade is DID EVERY READING HAPPEN, not did the walk succeed)")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if ok else 'FAIL'}")
        context.set_manual_mode()




class Ch21ApproachMode(BotMode):
    """§Ch21 LEG 3 — THE APPROACH, driven end to end from `post_wallace.ss1`.

    ‼ IT CALLS THE PRODUCTION ENTRY POINT (`sootopolis.approach_sky_pillar`), never a copy. A copy
    would only ever prove the copy — the `boxwithdraw` / `ch21dive` rule stated in all three
    existing §Ch21 driver docstrings.

    WHAT THE LEG DOES, from the PINNED fixture (CAVE_OF_ORIGIN_B1F (9,14), state 3):
      cave return (3 warps) -> the Sootopolis POCKET (plan once, follow blind) -> heal (by PID)
      -> walk to the dive tile -> dive -> underwater arrow warp -> surface on Route 126
      -> a 322-waypoint six-map swim -> the BLIND STEP onto (40,19) -> the staging tile (28,15)
      -> 16 HAND-WALKED steps our own planner calls unreachable -> the door -> SKY_PILLAR_ENTRANCE.

    ⛔ ACCEPTANCE IS NOT "THE WALK FINISHED". §Ch15, §Ch18 and §Ch19 each PASSED their own test
    while leaving the bot STRANDED, so the grade is:
        every READING actually happened   AND   whiteouts == 0   AND   the bot can CONTINUE
    where "can CONTINUE" is a real `calculate_path` from the tile the run REACHED to
    SKY_PILLAR_ENTRANCE (14,3), requiring all three of `bool(path)`, `path[-1].map == ENTRANCE`
    and `not path[-1].is_warp`. ⛔ The three conjuncts are load-bearing and MEASURED: the same call
    aimed at (14,4) returns a path of the same length with `is_warp=True` ending on
    SKY_PILLAR_OUTSIDE (17,13), so a two-conjunct check would "prove" continuation by walking into
    leg 4's Wallace cutscene.

    ⛔ THE READINGS ARE BUILT BY THE PRODUCTION FUNCTION AT THE POINT EACH IS TAKEN, and this
    driver only grades what it is handed. It must never add a label itself — `Ch21PocketExitMode`
    v1 appended its last label unconditionally and passed a run in which the reading was skipped.

    FAULT ARMS (each exists because the happy path CANNOT reach the branch):
      POKEBOT_CH21_FAULT_POCKETSTALL=1  truncate the pocket path mid-danger-zone and raise a
                                        waypoint timeout. PASS requires pocket_attempts == 2 AND
                                        the run still reaching the Poke Center front tile. This is
                                        the ONLY way to observe the pocket recovery, which is the
                                        one designed-but-unproven component of the leg.
      POKEBOT_CH21_FAULT_BLINDWALL=1    substitute the wrong direction at door-approach step 0.
                                        MUST fail loudly naming the step index, and MUST NOT hang.
      POKEBOT_CH21_FAULT_POCKETWALKBACK=1  (⛔ set TOGETHER WITH POCKETSTALL — it only fires
                                        while a recovery is running) stall the recovery's OWN
                                        walk back; MUST produce the NAMED 'stranded' BotModeError,
                                        never a raw TimedOutTryingToReachWaypointError. Added by an
                                        adversarial review that found the walk-back unguarded — an
                                        arm nobody knows to run decays into dead code.
    ⛔ Do NOT drop an arm because the clean run passed — leg 2a shipped a bail that was dead code
    for exactly that reason, and it cost a drive.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 120000
    ‼ THE FRAME BUDGET ABOVE IS AN ESTIMATE DERIVED FROM TWO ANCHORS (13.4 frames/waypoint in the
    city, from the 121-wp pocket drive at 1,624 frames; ~120 frames/waypoint for ocean travel WITH
    battles, from leg 1). ⛔ REPLACE IT WITH THE MEASUREMENT from drive 1's `frames=` line — a run
    that dies ON its budget yields NO reading, which is the worst possible outcome.
    """

    @staticmethod
    def name() -> str:
        return "Ch21Approach"

    def __init__(self):
        super().__init__()
        # ‼ COUNTED VIA THE HOOK, NOT BY POLLING. A mode generator receives NO frames while a
        # battle runs, so a poll inside the leg could never have answered this — and the swim
        # crosses six routes with 39 undefeated trainers, which is the number this drive exists
        # to measure.
        self.encounters = 0
        self.encounter_maps: list[str] = []
        # ⛔ A WHITEOUT SILENTLY TURNS EVERY LATER READING INTO A STATEMENT ABOUT THE POKE CENTER.
        # There is no Poke Center between Sootopolis and the Sky Pillar, so a whiteout out there
        # also costs the entire swim.
        # ‼ BE PRECISE ABOUT WHAT THIS LATCH DOES. `on_whiteout` returning False hands the run back
        # to MANUAL mode, so the driver generator is dropped and this block never reaches its
        # RESULT/ACCEPTANCE lines. ⇒ the honest claim is "a whiteout ends the run with NO ACCEPTANCE
        # LINE AT ALL", not "ACCEPTANCE fails on a whiteout". The counter is still worth keeping:
        # the hook prints its own ‼ line, which is the only trace such a run leaves.
        self.whiteouts = 0

    def on_whiteout(self) -> bool:
        # ⛔⛔ RETURNS **True**, UNLIKE EVERY OTHER §Ch21 DRIVER, AND THE DIFFERENCE IS THE WHOLE
        # POINT. Returning False means "I do not handle this", which hands the run to MANUAL and
        # DISCARDS the driver generator — so the RESULT/ACCEPTANCE block below never executes and
        # the whiteout counter it was supposed to feed is thrown away with it. The log then ends
        # with no verdict at all, and a reader files it as "crashed", not "the leg failed".
        # ⇒ claim the event, latch the story abort, and let the leg unwind through its own
        # `_check_abort()` loop heads so a verdict actually PRINTS with whiteouts=1.
        self.whiteouts += 1
        log("[ch21approach] ‼ WHITEOUT — every reading after this point would describe the RESPAWN "
            "point, not the approach. Latching the story abort so the leg unwinds and this run "
            "still prints a verdict.")
        try:
            from modules.story.early_game import set_story_abort

            set_story_abort(True)
        except Exception as error:  # noqa: BLE001 - never let the hook itself end the run
            log(f"[ch21approach] ‼ could not latch the story abort: {type(error).__name__}: {error}")
            return False
        return True

    def on_battle_started(self, encounter):
        self.encounters += 1
        try:
            from modules.player import get_player_avatar

            self.encounter_maps.append(str(tuple(get_player_avatar().map_group_and_number)))
        except Exception:  # noqa: BLE001 - the count is what matters; the map is a nicety
            self.encounter_maps.append("?")
        return super().on_battle_started(encounter)

    def run(self):
        from modules.map_data import MapRSE
        from modules.memory import get_event_flag, get_event_var
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.story import sootopolis as ch21

        TAG = "ch21approach"
        frames_before = context.emulator.get_frame_count()

        def where() -> tuple[str, tuple[int, int]]:
            avatar = get_player_avatar()
            coordinates = tuple(avatar.local_coordinates)
            try:
                return MapRSE(tuple(avatar.map_group_and_number)).name, coordinates
            except Exception:  # noqa: BLE001
                return f"UNKNOWN{tuple(avatar.map_group_and_number)}", coordinates

        start_name, start_at = where()
        log(f"[{TAG}] PRE at={start_name}{start_at} "
            f"state={get_event_var('SOOTOPOLIS_CITY_STATE')} "
            f"pillar_state={get_event_var('SKY_PILLAR_STATE')} "
            f"wallace_flag={bool(get_event_flag('WALLACE_GOES_TO_SKY_PILLAR'))}")

        # ⛔⛔ THE DRIVER OWNS THE REPORT DICT AND HANDS IT IN. If the leg raises, a dict it
        # RETURNED would never arrive — and drive 1 (2026-09-01) proved that is not hypothetical:
        # it printed `readings=[] missing=[all thirteen]` (thirteen AT THE TIME; the exported
        # set is 14 now — R-CONTROL joined later) on a run whose console showed R-CAVE,
        # R-POCKET and R-HEAL taken, because the readings died with the generator. The log is the
        # artefact a future agent reads; a failed run must still say how far it got.
        report: dict = {}
        failure = None
        try:
            yield from ch21.approach_sky_pillar(report)
        except Exception as error:  # noqa: BLE001 - the driver REPORTS failures, it does not hide them
            failure = f"{type(error).__name__}: {str(error)[:600]}"
            log(f"[{TAG}] LEG FAILED: {failure}")

        readings = set(report.get("readings") or ())
        here_name, at = where()
        reached = here_name == "SKY_PILLAR_ENTRANCE"

        # ⛔ THE REQUIRED SET IS IMPORTED FROM THE LEG, NEVER COPIED HERE. A private copy is the
        # P5 shape — one fact in two places — and it fails in the worst direction: rename a label
        # in the leg and this driver reports `missing=['R-BLIND']` on a PERFECT run, whose obvious
        # repair is to edit the list here, which SILENTLY DELETES A REQUIRED READING.
        required = set(ch21.LEG3_READINGS)
        missing = sorted(required - readings)
        continue_ok = bool(report.get("continue_ok"))
        state = get_event_var("SOOTOPOLIS_CITY_STATE")
        pillar_state = get_event_var("SKY_PILLAR_STATE")
        # ⛔ `state == 3 and pillar_state == 0` is NOT vacuous decoration: leg 3 crossing into leg 4
        # would advance one of them, and that is the specific way this leg could "succeed" while
        # having eaten the next leg's opening cutscene.
        # ⛔⛔ THE VACUITY GATE. Point this driver at its OWN captured fixture and the leg's resume
        # branch returns in one frame: reached=True, on the right map, state 3, pillar 0, full HP,
        # continuation provable — EVERY end-state conjunct satisfied by a run that did nothing.
        # `start_map` is the one conjunct that is FALSE at frame 0 on any fixture but the intended
        # one, so it is what stops a no-op from grading as a PASS.
        premise_ok = start_name == "CAVE_OF_ORIGIN_B1F" and not report.get("resumed")
        if not premise_ok:
            log(f"[{TAG}] ‼ VACUOUS PREMISE — this driver must start on CAVE_OF_ORIGIN_B1F (it "
                f"started on {start_name}, resumed={report.get('resumed')}). A run from the leg's "
                "own output fixture satisfies every end-state check while doing nothing.")

        # ⛔ GRADE THE METHOD, NOT ONLY THE DESTINATION. A leg that reached the door by re-planning
        # north of y=14 on Route 131 — where our planner returns a confident route through solid
        # rock — is not the same leg as one that hand-walked it, and the end state cannot tell them
        # apart. EXACTLY two planner calls are permitted on that map: the swim and the staging walk.
        method_ok = (
            report.get("planner_calls_on_route131") == 2
            and report.get("blind_steps_taken", 0) >= 1
            and report.get("tail_tiles_confirmed") == report.get("tail_tiles_expected")
            and not report.get("r131_live_walls")
        )
        passed = (
            failure is None
            and premise_ok
            and method_ok
            and reached
            and not missing
            and self.whiteouts == 0
            and continue_ok
            and bool(report.get("control_refused"))
            and state == 3
            and pillar_state == 0
        )
        # ⛔ CAPTURE IS GATED SEPARATELY, AND DELIBERATELY MORE NARROWLY THAN `passed`. A raise
        # AFTER arrival — in a diagnostic, or a late assert — makes `failure` non-None and would
        # otherwise refuse to save a fixture for a bot that is standing on SKY_PILLAR_ENTRANCE with
        # its continuation proven, costing another one-shot ~50,000-frame swim through a pocket
        # that allows one crossing per visit.
        capturable = (
            reached
            and continue_ok
            and bool(report.get("control_refused"))
            and self.whiteouts == 0
            and premise_ok
        )

        total = context.emulator.get_frame_count() - frames_before
        log(f"[{TAG}] RESULT reached={reached} at={here_name}{at} "
            f"pocket_attempts={report.get('pocket_attempts')} rest={report.get('rest')} "
            f"rest_matches_prediction={report.get('rest_matches_prediction')} "
            f"controllable={player_avatar_is_controllable()} "
            f"encounters={self.encounters} maps={self.encounter_maps} "
            f"whiteouts={self.whiteouts} frames={total}")
        log(f"[{TAG}] ROUTE131 LIVE-GRID WALLS on tiles this leg walks: "
            f"{report.get('r131_live_walls')} (⛔ must be an empty list; read from gBackupMapLayout, "
            "the grid the GAME walks on, not from our planner's layout)")
        log(f"[{TAG}] UNDERWATER_ROUTE126 warp resting tile: {report.get('uw_rest')} "
            "(the warp TARGET is (45,65); a difference is a resting-tile FINDING, not a failure)")
        log(f"[{TAG}] CONTINUE continue_wp={report.get('continue_wp')} "
            f"continue_is_warp={report.get('continue_is_warp')} continue_ok={continue_ok} "
            f"(target (14,3); measured expectation 21 wp, is_warp=False — ⛔ (14,4) is the TRAP)")
        log(f"[{TAG}] ROUTE131 LAYOUT {report.get('r131_layout')} "
            f"planner_agrees_with_game={report.get('r131_planner_agrees')} "
            "(⛔ agreement here would CONTRADICT the premise the hand-walked tail was built for; "
            "it is a FINDING for the docs, not a run failure)")
        log(f"[{TAG}] END STATE state={state} pillar_state={pillar_state} "
            "(both must be UNCHANGED at 3 and 0 — state 4 is written by leg 4's door scene)")
        log(f"[{TAG}] METHOD planner_calls_on_route131={report.get('planner_calls_on_route131')} "
            f"(exactly 2 permitted) blind_steps_taken={report.get('blind_steps_taken')} "
            f"tail_tiles_confirmed={report.get('tail_tiles_confirmed')}"
            f"/{report.get('tail_tiles_expected')} method_ok={method_ok} premise_ok={premise_ok}")
        log(f"[{TAG}] CONTROL control_refused={report.get('control_refused')} "
            "(⛔ the planner must still be able to REFUSE; a reachability check with no matching "
            "refusal is a coin that only has heads)")
        log(f"[{TAG}] readings={sorted(readings)} missing={missing} "
            "(the grade is DID EVERY READING HAPPEN **and can the bot CONTINUE**, not merely "
            "did the walk finish)")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")

        _cap = _os.environ.get("CH21_CAPTURE", "").strip()
        if _cap:
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not capturable:
                log(f"[{TAG}] CAPTURE SKIPPED — not capturable (reached={reached} "
                    f"continue_ok={continue_ok} control_refused={report.get('control_refused')} "
                    f"whiteouts={self.whiteouts} premise_ok={premise_ok}); refusing to write {_cap}")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[{TAG}] CAPTURE REFUSED — {_cap} exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[{TAG}] CAPTURE WROTE {_out.name} ({_out.stat().st_size} bytes) at {at} "
                    f"— ‼ verify with probe_anchor_inventory.py, not this line")

        context.set_manual_mode()



class Ch21ClimbMode(BotMode):
    """§Ch21 LEG 4 — THE SKY PILLAR: Wallace scene, the climb, RAYQUAZA, and the DESCENT.

    ‼ IT CALLS THE PRODUCTION ENTRY POINT (`sootopolis.climb_sky_pillar`), never a copy — the
    standing rule of every §Ch21 driver.

    ⛔⛔ TWO TRUE ONE-SHOTS LIVE ON THIS LEG, in order: crossing ENTRANCE (14,4) fires OUTSIDE's
    Wallace ON_FRAME scene (state 3->4, Wallace removed); stepping TOP (14,9) wakes RAYQUAZA
    (state 4->5, SKY_PILLAR_STATE 0->1, CRY_DONE 1). Neither replays. A failed drive that spent
    one costs a FULL leg-3 re-run (~34k frames + the one-crossing pocket) to rewind — which is why
    the leg supports env-gated MID-LEG captures (CH21_CAPTURE_WALLACE / CH21_CAPTURE_SUMMIT) and
    the RESUME phases those fixtures feed. ⛔ Only a FULL run (starting at vars 3/0/0 on the
    ENTRANCE) can PASS; a resumed run reports honestly and grades FAIL by premise.

    THE GRADE (house rule 8 — §Ch15/18/19 each PASSED their own test while STRANDED):
      every reading happened AND the ORDER trace matches AND both falls happened AND all six
      floors were pinned+matched to their CLEAN layouts AND the bot ENDS on the ENTRANCE with a
      real non-warp path to (6,15) AND the planner still REFUSES (6,17) AND the three vars read
      (5,1,1) AND whiteouts == 0.
    ⛔ WHY POSITION+PATH AND NOT VARS ALONE: a whiteout after the summit respawns in Sootopolis
    where the vars ALSO read (5,1,1) — a var-keyed predicate would grade a WHITEOUT as a PASS
    (the leg-4 recon's grader trap). The vars corroborate; the position and the path decide.

    FAULT ARMS (each driver-proof, env-read inside the leg; the happy path reaches none):
      POKEBOT_CH21_FAULT_NOFALL=1      step the WRONG way at the ascent fall stand: the map-change
                                       witness must raise NAMED, bounded, no hang. FAIL.
      POKEBOT_CH21_FAULT_SUMMITSTOP=1  return at the summit — the §Ch15/18/19 shape exactly.
                                       ⛔ THE MOST IMPORTANT ARM ON THE LEG: it must FAIL, with
                                       missing= naming every descent reading.
      POKEBOT_CH21_FAULT_POCKETEXIT=1  descend via the planner-visible 4F (7,1) staircase instead
                                       of the fall: the leg must NAME the livelock ("LIVELOCK, not
                                       a refusal") from inside the sealed pocket. FAIL.
      POKEBOT_CH21_FAULT_DROPREADING=1 do the descent fall but suppress R-FALL2 at its take point:
                                       missing=['R-FALL2'], FAIL — proves the readings gate is live.
      POKEBOT_CH21_FAULT_CONTROLOPEN=1 aim R-CONTROL at a REACHABLE tile: control_refused=False,
                                       FAIL — a control that cannot fail is decoration.
      POKEBOT_CH21_FAULT_BADBLOCKDATA=1 corrupt the EXPECTED CLEAN blockdata for 1F: the leg's
                                       hardest-leaned-on gate (`_pin_and_verify_floor`, the layout-
                                       mismatch refusal leg 3 paid a drive to learn) must RAISE
                                       BotModeError naming SKY_PILLAR_1F, bounded, before any walk.
                                       FAIL — proves that gate fires on its own FAILURE path.
      (no env var) THE VACUITY ARM     point this driver at its own output fixture: the preflight
                                       reads vars (5,1,1) -> phase 'post-summit' -> premise FAIL.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_skypillar_door.ss1 --driver ch21climb --frames 60000
    ‼ THE FRAME BUDGET IS AN ESTIMATE (leg 3 measured 13.4 f/wp walking; this leg is ~250 indoor
    waypoints + two cutscenes + two falls; 1F/3F/5F carry encounter rate 10). ⛔ REPLACE IT WITH
    THE MEASUREMENT from drive 1's frames= line.
    """

    @staticmethod
    def name() -> str:
        return "Ch21Climb"

    def __init__(self):
        super().__init__()
        # counted via the HOOK — a mode generator gets no frames during a battle (1F/3F/5F have
        # land encounters at rate 10; 2F/4F/TOP have no table).
        self.encounters = 0
        self.encounter_maps: list[str] = []
        self.whiteouts = 0

    def on_whiteout(self) -> bool:
        # ⛔ RETURNS True + LATCHES THE ABORT (leg 3's B1 fix): returning False would hand the run
        # to Manual and discard this generator, so the RESULT/ACCEPTANCE block would never print.
        # On THIS leg a whiteout is also an unrecoverable strand (a state-4/5 respawn in Sootopolis
        # that no leg owns), so the verdict printing is the only evidence the run leaves.
        self.whiteouts += 1
        log("[ch21climb] ‼ WHITEOUT — the run respawns in Sootopolis at a state NO LEG OWNS; "
            "latching the story abort so a verdict still prints.")
        try:
            from modules.story.early_game import set_story_abort

            set_story_abort(True)
        except Exception as error:  # noqa: BLE001 - never let the hook itself end the run
            log(f"[ch21climb] ‼ could not latch the abort: {type(error).__name__}: {error}")
            return False
        return True

    def on_battle_started(self, encounter):
        self.encounters += 1
        try:
            from modules.player import get_player_avatar

            self.encounter_maps.append(str(tuple(get_player_avatar().map_group_and_number)))
        except Exception:  # noqa: BLE001 - the count is what matters
            self.encounter_maps.append("?")
        return super().on_battle_started(encounter)

    def run(self):
        from modules.map_data import MapRSE
        from modules.memory import get_event_var
        from modules.player import get_player_avatar, player_avatar_is_controllable
        from modules.story import sootopolis as ch21

        TAG = "ch21climb"
        frames_before = context.emulator.get_frame_count()

        def where() -> tuple[str, tuple[int, int]]:
            avatar = get_player_avatar()
            coordinates = tuple(avatar.local_coordinates)
            try:
                return MapRSE(tuple(avatar.map_group_and_number)).name, coordinates
            except Exception:  # noqa: BLE001
                return f"UNKNOWN{tuple(avatar.map_group_and_number)}", coordinates

        start_name, start_at = where()
        start_vars = (get_event_var("SOOTOPOLIS_CITY_STATE"), get_event_var("SKY_PILLAR_STATE"),
                      get_event_var("SKY_PILLAR_RAYQUAZA_CRY_DONE"))
        log(f"[{TAG}] PRE at={start_name}{start_at} vars={start_vars} "
            f"(full run requires (3, 0, 0) on SKY_PILLAR_ENTRANCE)")

        # ⛔ THE DRIVER OWNS THE REPORT DICT AND HANDS IT IN — a dict RETURNED by a raising
        # generator never arrives, and the failed run is the one whose partial readings matter.
        report: dict = {}
        failure = None
        try:
            yield from ch21.climb_sky_pillar(report)
        except Exception as error:  # noqa: BLE001 - the driver REPORTS failures, never hides them
            failure = f"{type(error).__name__}: {str(error)[:600]}"
            log(f"[{TAG}] LEG FAILED: {failure}")

        readings = set(report.get("readings") or ())
        trace = list(report.get("trace") or ())
        here_name, at = where()
        reached = here_name == "SKY_PILLAR_ENTRANCE"
        end_vars = (get_event_var("SOOTOPOLIS_CITY_STATE"), get_event_var("SKY_PILLAR_STATE"),
                    get_event_var("SKY_PILLAR_RAYQUAZA_CRY_DONE"))

        # ⛔ required set IMPORTED from the leg — a private copy is the P5 shape.
        required = set(ch21.LEG4_READINGS)
        missing = sorted(required - readings)

        # ⛔ ORDER IS PART OF THE PREDICATE: LEG4_ORDER must be a subsequence of the trace.
        # A readings SET cannot distinguish "descended, then proved continuation" from the reverse.
        order_iter = iter(trace)
        order_ok = all(any(step == want for step in order_iter) for want in ch21.LEG4_ORDER)

        # ⛔ THE VACUITY GATE. Leg 4 starts AND ends on SKY_PILLAR_ENTRANCE, so — unlike leg 3 —
        # the map name cannot discriminate a no-op. The STARTING VARS are the only conjunct false
        # on the leg's own output fixture (which reads (5,1,1)).
        premise_ok = (start_vars == (3, 0, 0) and start_name == "SKY_PILLAR_ENTRANCE"
                      and report.get("phase") == "full")
        if not premise_ok:
            log(f"[{TAG}] ‼ VACUOUS/RESUMED PREMISE — start_vars={start_vars}, "
                f"start={start_name}, phase={report.get('phase')}. Only a full run from (3,0,0) "
                "on the ENTRANCE can PASS; a run from the leg's own output fixture satisfies every "
                "END-state check while doing nothing.")

        falls = list(report.get("falls") or ())
        floors = list(report.get("floors") or ())
        method_ok = (
            len(falls) == 2
            and {f[0] for f in floors} >= {"SKY_PILLAR_1F", "SKY_PILLAR_2F", "SKY_PILLAR_3F",
                                           "SKY_PILLAR_4F", "SKY_PILLAR_5F", "SKY_PILLAR_TOP"}
            and order_ok
        )
        continue_ok = bool(report.get("continue_ok"))
        passed = (
            failure is None
            and premise_ok
            and method_ok
            and reached
            and not missing
            and self.whiteouts == 0
            and continue_ok
            and bool(report.get("control_refused"))
            and end_vars == (5, 1, 1)
        )
        # capture gate — narrower than `passed` (a raise AFTER arrival must not cost the fixture).
        capturable = (
            reached and continue_ok and bool(report.get("control_refused"))
            and self.whiteouts == 0 and premise_ok and end_vars == (5, 1, 1)
        )

        total = context.emulator.get_frame_count() - frames_before
        log(f"[{TAG}] RESULT reached={reached} at={here_name}{at} phase={report.get('phase')} "
            f"falls={falls} floors_pinned={len(floors)} "
            f"post_wallace_tile={report.get('post_wallace_tile')} "
            f"(predictions (14,7)/(14,6): matches={report.get('post_wallace_matches')}) "
            f"top_rest={report.get('top_rest')} exit_rest={report.get('exit_rest')} "
            f"encounters={self.encounters} maps={self.encounter_maps} "
            f"whiteouts={self.whiteouts} frames={total}")
        log(f"[{TAG}] FLOORS {floors} (each entry: name, LIVE blockdata — must equal the CLEAN "
            f"column of the atlas per-floor table; the leg RAISES on mismatch)")
        log(f"[{TAG}] VARS start={start_vars} summit={report.get('summit_vars')} end={end_vars} "
            f"(the leg is graded on POSITION+PATH; vars corroborate — a whiteout also reads "
            f"(5,1,1) from Sootopolis, which is why they cannot decide alone)")
        log(f"[{TAG}] TRAP {report.get('trap')} (stair reachable AND pocket sealed = the livelock "
            f"measured in place, the WHY of the second fall)")
        log(f"[{TAG}] CONTINUE continue_wp={report.get('continue_wp')} continue_ok={continue_ok} "
            f"control_refused={report.get('control_refused')} (target (6,15); ⛔ (6,16) is the "
            f"live exit warp and is never aimed at)")
        log(f"[{TAG}] ORDER order_ok={order_ok} trace={trace}")
        log(f"[{TAG}] METHOD premise_ok={premise_ok} method_ok={method_ok} "
            f"falls={len(falls)}/2 floors={len(floors)}")
        log(f"[{TAG}] readings={sorted(readings)} missing={missing} "
            f"(the grade is DID EVERY READING HAPPEN, IN ORDER, **and can the bot CONTINUE**)")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")

        _cap = _os.environ.get("CH21_CAPTURE", "").strip()
        if _cap:
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not capturable:
                log(f"[{TAG}] CAPTURE SKIPPED — not capturable (reached={reached} "
                    f"continue_ok={continue_ok} control_refused={report.get('control_refused')} "
                    f"whiteouts={self.whiteouts} premise_ok={premise_ok} end_vars={end_vars})")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[{TAG}] CAPTURE REFUSED — {_cap} exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[{TAG}] CAPTURE WROTE {_out.name} ({_out.stat().st_size} bytes) at {at} "
                    f"— ‼ verify with probe_anchor_inventory.py, not this line")

        context.set_manual_mode()


class Ch21Leg5ProbeMode(BotMode):
    """§Ch21 LEG 5 — the PART C LIVE PROBES (the queue's "VALIDATE, then BUILD").

    ‼ PREDICTIONS ARE FILED FIRST, IN A COMMITTED FILE, NOT IN THIS DOCSTRING:
    `PROJECT KNOWLEDGE/ai-research-notes/2026-09-02-ch21-leg5-PARTC-PREDICTIONS.md`. Every reading
    below is graded against it AFTER the run. ⛔ A reading that contradicts a prediction is a
    RESULT, never a driver failure — reality cannot fail a probe; only not-measuring can.

    WHAT IT MEASURES, IN ORDER (the leg is NOT built yet; this driver walks nothing it does not
    have to, presses `A` at NO NPC, and writes NO state):
      P0  premise + pre-readings on SKY_PILLAR_ENTRANCE (14,3): vars, flags, party BY PID, the
          HM07 bag count, the respawn WarpData, and the `can_surf`/`can_dive` PRECONDITIONS.
          ⛔ P0 gates `can_surf` because without BADGE05+Surf the P2 arm-B path degrades to a
          refusal and the A/B would differ for the WRONG reason (refuter finding F2).
      P1  the exit: plan (14,3)->(6,15) [refusing any plan through the (14,4) seam warp], then the
          held-Down (6,16) door to ROUTE131, and the RESTING TILE it leaves.
      P2  ⛔ THE GATE THE QUEUE PUTS FIRST — the ROUTE131 LIVE-PIN A/B. Arm A plans the return
          swim on the STATIC layout the planner seeded itself with; arm B plans it after
          `_pin_planner_to_live_layout(ROUTE131)`. THE DISCRIMINATOR IS THE **Surf-ACTION COUNT**
          (map_path.py:916 seeds the source node's elevation from the LAYOUT, so a static "deep
          water" source makes the planner believe it is ALREADY surfing and emit no mount).
          ⛔ NOT the live-wall count: ocean is collision 0 in BOTH layouts, so a wall-only
          discriminator reads INCONCLUSIVE forever (refuter finding F2).
      P3  the return swim ROUTE131 -> ROUTE126 (45,66), the dive, and the underwater crossing.
      P4  the surface + THE RAYQUAZA-ARRIVAL SCENE (one-shot #3), then a BOUNDED SETTLE.
          ⛔⛔ THE SETTLE IS THE WHOLE POINT OF P4 (refuter finding F1, CRITICAL): the scene sets
          SKY_PILLAR_STATE 2 roughly 120 frames AND ONE `warpwhitefade` BEFORE it ends, and the
          avatar reads CONTROLLABLE under `lockall` — so `_ride_summit_scene` + the usual
          `wait_until_truly_controllable()` both return MID-SCENE. Any tile read or planner pin
          taken there describes a state the bot never rests in.
      P5  the state-5 Sootopolis layout: the Sootopolis pin (predicted a NO-OP), a WHOLE-MAP live
          -vs-static collision diff, the object templates read from SaveBlock1 (with a control),
          the loaded-object dump, and a path matrix with a NEGATIVE CONTROL verified against the
          LIVE grid before it is used.
      P6  ONE walk (rest -> (33,36), Maxie's south approach) and the object dump from there —
          the three HM07 NPCs are outside the spawn window from the rest tile, so an empty P5
          object list is EXPECTED and only P6 can see them (refuter finding F3).

    CONTROL ARM (a SECOND run, never the main one):
      CH21_PROBE_NOPIN131=1  skip the ROUTE131 pin and try to swim anyway with tries=2.
                             PREDICTED: it FAILS on ROUTE131 at the water's edge, on foot — the
                             live reproduction of KI-73 that the pin exists to prevent. ⛔ Without
                             this arm, "the pin is load-bearing" is a CLAIM (house rule 8).

    ACCEPTANCE = P0..P5 each EXECUTED to a reading (P6 conditional on the P5 walk being planned)
    AND whiteouts == 0. The premise gate makes a run on the wrong fixture say VACUOUS and stop.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_rayquaza_gone.ss1 --driver ch21leg5probe \
             --frames 120000 --log leg5probe.log
    ‼ ALL LOG TEXT IN THIS DRIVER IS ASCII ON PURPOSE — 2026-09-01 cost a gate a red-herring crash
    when a non-ASCII character on a SUCCESS path hit the cp1252 console.
    """

    #: The P2N control arm ends the run DELIBERATELY, so it needs its own grade.
    CONTROL_ARM_DONE = "P2N control arm complete"

    @staticmethod
    def name() -> str:
        return "Ch21Leg5Probe"

    def __init__(self):
        super().__init__()
        self.encounters = 0
        self.encounter_maps: list[str] = []
        self.whiteouts = 0
        self.probes_run: list[str] = []
        self.stop_reason: str | None = None
        self.settle_ok = False
        self.scene_failure: str | None = None
        self.failure: str | None = None

    def on_whiteout(self) -> bool:
        # ⛔ True + latch: returning False hands the run to Manual and DISCARDS this generator,
        # so the RESULT/ACCEPTANCE block would never print (leg 3's B1 fix).
        self.whiteouts += 1
        log("[ch21leg5probe] !! WHITEOUT - latching the story abort so a verdict still prints.")
        try:
            from modules.story.early_game import set_story_abort

            set_story_abort(True)
        except Exception as error:  # noqa: BLE001 - never let the hook itself end the run
            log(f"[ch21leg5probe] !! could not latch the abort: {type(error).__name__}: {error}")
            return False
        return True

    def on_battle_started(self, encounter):
        self.encounters += 1
        try:
            from modules.player import get_player_avatar

            self.encounter_maps.append(
                f"{tuple(get_player_avatar().map_group_and_number)}@"
                f"{context.emulator.get_frame_count()}"
            )
        except Exception:  # noqa: BLE001 - the count is what matters
            self.encounter_maps.append("?")
        return super().on_battle_started(encounter)

    def run(self):
        """A THIN WRAPPER: the probe body runs inside ONE try/except so a verdict ALWAYS prints.

        ⛔⛔ THIS SHAPE IS NOT DECORATION, AND ITS ABSENCE WAS A REAL DEFECT FOUND BY ADVERSARIAL
        REVIEW OF THIS VERY CLASS (2026-09-02, before the drive). Without it, ONE lost wild battle
        during the P3 surf makes `on_whiteout` latch `StoryAbort`; the next `_check_abort()` inside
        `_navigate_riding_out` raises it; the exception escapes this generator; the harness catches
        `BotModeError` and calls `set_manual_mode()`, which CLEARS the controller stack and discards
        the generator — so P4/P5/P6 and the ACCEPTANCE line never print, and `on_whiteout`'s own
        comment ("latching the abort so a verdict still prints") is a LIE. `Ch21ClimbMode` has had
        this wrapper since leg 3's B1 fix; this class was written without it and inherited the
        comment anyway. ⇒ **a hook that promises a verdict is only as true as the catch that
        lets the verdict run.**
        """
        TAG = "ch21leg5probe"
        frames_before = context.emulator.get_frame_count()
        try:
            yield from self._probe()
        except Exception as error:  # noqa: BLE001 - the driver REPORTS failures, never hides them
            self.failure = f"{type(error).__name__}: {str(error)[:600]}"
            log(f"[{TAG}] !! PROBE RAISED: {self.failure}")

        done = set(self.probes_run)
        if self.stop_reason == self.CONTROL_ARM_DONE:
            # The control arm STOPS on purpose after P2N; its grade is "the reading happened".
            passed = ({"P0", "P1", "P2N"}.issubset(done) and self.whiteouts == 0
                      and self.failure is None)
        else:
            passed = (
                {"P0", "P1", "P2", "P3", "P4", "P5"}.issubset(done)
                and self.whiteouts == 0
                and self.failure is None
                and self.stop_reason is None
                # ⛔ settle_ok AND scene_failure ARE PART OF THE GRADE, not just logged. The same
                # review found that without them a timed-out settle still printed PASS over P5/P6
                # readings taken on the CRISIS-state layout - a false PASS that looks clean.
                and self.settle_ok
                and self.scene_failure is None
            )
        log(f"[{TAG}] probes run: {sorted(done)} (P6 conditional on the P5 matrix) "
            f"whiteouts={self.whiteouts} encounters={self.encounters} {self.encounter_maps} "
            f"frames={context.emulator.get_frame_count() - frames_before}")
        log(f"[{TAG}] VERDICT INPUTS stop_reason={self.stop_reason!r} failure={self.failure!r} "
            f"settle_ok={self.settle_ok} scene_failure={self.scene_failure!r}")
        log(f"[{TAG}] GRADE: this probe measures; it does not decide. Compare every line above "
            f"against ai-research-notes/2026-09-02-ch21-leg5-PARTC-PREDICTIONS.md.")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        context.set_manual_mode()

    def _probe(self):
        import struct as _struct

        import modules.map as _map_module
        from modules.map import (
            get_map_data,
            get_map_data_for_current_position,
            get_map_objects,
        )
        from modules.map_data import MapRSE
        from modules.map_path import PathFindingError, WaypointAction, calculate_path
        from modules.memory import get_event_flag, get_save_block, read_symbol, unpack_uint32
        from modules.modes.util.higher_level_actions import dive, surface_from_dive
        from modules.modes.util.walking import navigate_to
        from modules.player import AvatarFlags, get_player_avatar, player_avatar_is_controllable
        from modules.pokemon_party import get_party
        from modules.story.early_game import (
            _check_abort,
            _navigate_riding_out,
            wait_until_truly_controllable,
        )
        from modules.story.seafloor_cavern import _var
        from modules.story.sootopolis import (
            _live_collision_grid,
            _live_wall_tiles,
            _pin_planner_to_live_layout,
            _ride_summit_scene,
            _route131_layout_reading,
        )
        from modules.tasks import get_global_script_context, is_waiting_for_input

        TAG = "ch21leg5probe"
        # ⛔ THE SAME LIST OBJECT the verdict reads - never rebind it, only append.
        probes_run = self.probes_run
        nopin_arm = _os.environ.get("CH21_PROBE_NOPIN131", "").strip() == "1"

        # ---------------------------------------------------------------- small local instruments
        def where() -> tuple[str, tuple[int, int]]:
            avatar = get_player_avatar()
            coordinates = tuple(avatar.local_coordinates)
            try:
                return MapRSE(tuple(avatar.map_group_and_number)).name, coordinates
            except Exception:  # noqa: BLE001
                return f"UNKNOWN{tuple(avatar.map_group_and_number)}", coordinates

        def budgeted(generator, budget: int, label: str):
            """Drive `generator` with a HARD frame ceiling.

            ⛔ EVERY yielding call in this probe goes through here. `navigate_to` and
            `_navigate_riding_out` have internal timeouts, but a probe that inherits somebody
            else's bound is a probe that can silently eat the whole --frames budget and leave
            NO verdict. The ceiling raises NAMED, which is a reading.
            """
            spent = 0
            while True:
                try:
                    value = next(generator)
                except StopIteration:
                    return
                spent += 1
                if spent > budget:
                    generator.close()
                    raise RuntimeError(f"frame budget {budget} exhausted during {label}")
                yield value

        def describe(path) -> list[tuple]:
            return [
                (tuple(w.map), tuple(w.coordinates), w.is_warp, w.is_water_tile,
                 None if w.action is None else w.action.name)
                for w in path
            ]

        def static_collision_grid(map_enum):
            """The map's OWN STATIC (ROM header) collision grid, whatever the planner cache holds.

            ‼ WHY NOT `get_map_data(...).collision`: `MapLocation._map_layout` reads through
            `modules.map._map_layout_cache`, which THIS PROBE DELIBERATELY POISONS with the live
            layout (that is what the pin IS). After a pin, `get_map_data` would return the LIVE
            grid and the "live vs static" diff would compare a grid against ITSELF and read 0.
            ⇒ go to the static header pointer directly. Decode identical to map.py:773-781 and to
            `_live_collision_grid`; the only difference is the SOURCE and that the static blockdata
            carries NO border margin (map.py:769 indexes it with no offset).
            """
            header = _map_module._map_header_cache[context.rom.id][map_enum.value]
            layout = context.emulator.read_bytes(unpack_uint32(header[:4]), 24)
            width = unpack_uint32(layout[0:4])
            height = unpack_uint32(layout[4:8])
            raw = context.emulator.read_bytes(unpack_uint32(layout[12:16]), width * height * 2)
            grid = {}
            for y in range(height):
                for x in range(width):
                    index = (y * width + x) * 2
                    block = raw[index] | (raw[index + 1] << 8)
                    grid[(x, y)] = (block & 0x0C00) >> 10
            return grid, width, height

        def warp_data(offset: int) -> tuple:
            # WarpData: s8 mapGroup, s8 mapNum, s8 warpId, (pad), s16 x, s16 y
            return _struct.unpack("<bbbxhh", get_save_block(1, offset, 8))

        def objects(label: str) -> list[tuple[int, tuple[int, int]]]:
            got = sorted((o.local_id, tuple(o.current_coords)) for o in get_map_objects())
            log(f"[{TAG}] OBJ-{label} {got}")
            return got

        def path_matrix(label: str, targets, control) -> dict:
            here_map, at = where()
            results = {}
            for target in list(targets) + [control]:
                try:
                    path = calculate_path((MapRSE.SOOTOPOLIS_CITY, at),
                                          (MapRSE.SOOTOPOLIS_CITY, target))
                    results[target] = len(path)
                    log(f"[{TAG}] P-{label} {at}->{target} OK {len(path)} wp")
                except Exception as perr:  # noqa: BLE001 - a refusal IS the reading here
                    results[target] = f"{type(perr).__name__}"
                    log(f"[{TAG}] P-{label} {at}->{target} {type(perr).__name__}")
            log(f"[{TAG}] P-{label} CONTROL {control} -> {results[control]} "
                f"(a control that PATHS proves nothing; it is verified against the LIVE grid "
                f"before it is chosen)")
            return results

        # ============================ P0 - PREMISE + PRE-READINGS ============================
        yield from budgeted(wait_until_truly_controllable(), 3000, "P0 settle")

        here_map, at = where()
        city = _var("SOOTOPOLIS_CITY_STATE")
        sky = _var("SKY_PILLAR_STATE")
        cry = _var("SKY_PILLAR_RAYQUAZA_CRY_DONE")
        hm_flag = get_event_flag("RECEIVED_HM_WATERFALL")
        leave_flag = get_event_flag("SOOTOPOLIS_ARCHIE_MAXIE_LEAVE")
        controllable = player_avatar_is_controllable()

        party = get_party()
        has_surf = party.has_pokemon_with_move("Surf")
        has_dive = party.has_pokemon_with_move("Dive")
        badge5 = get_event_flag("BADGE05_GET")
        badge7 = get_event_flag("BADGE07_GET")

        log(f"[{TAG}] P0 at={here_map}{at} vars(CITY,SKY,CRY)=({city},{sky},{cry}) "
            f"controllable={controllable} (PREDICTED SKY_PILLAR_ENTRANCE(14,3) / 5,1,1 / True)")
        log(f"[{TAG}] P0 flags HM_WATERFALL={hm_flag} ARCHIE_MAXIE_LEAVE={leave_flag} "
            f"KYOGRE_ESCAPED={get_event_flag('KYOGRE_ESCAPED_SEAFLOOR_CAVERN')} "
            f"LEGENDARIES_IN_SOOTOPOLIS={get_event_flag('LEGENDARIES_IN_SOOTOPOLIS')} "
            f"MET_ARCHIE={get_event_flag('MET_ARCHIE_SOOTOPOLIS')} "
            f"MET_MAXIE={get_event_flag('MET_MAXIE_SOOTOPOLIS')} "
            f"WALLACE_STATE={_var('SOOTOPOLIS_WALLACE_STATE')} "
            f"(PREDICTED False/False/True/True/False/False/0)")
        log(f"[{TAG}] P0 can_surf_precondition badge05={badge5} party_has_surf={has_surf} | "
            f"can_dive_precondition badge07={badge7} party_has_dive={has_dive} "
            f"(both MUST be True/True or the P2 A/B differs for the wrong reason)")

        try:
            from modules.items import get_item_bag, get_item_by_name

            hm07 = get_item_by_name("HM07")
            hm07_qty = get_item_bag().quantity_of(hm07)
            log(f"[{TAG}] P0 HM07 index={hm07.index} qty={hm07_qty} (PREDICTED 345 / 0)")
        except Exception as error:  # noqa: BLE001 - a bag read must never end the probe
            hm07_qty = None
            log(f"[{TAG}] P0 HM07 read FAILED: {type(error).__name__}: {error}")

        log(f"[{TAG}] P0 party={[(m.personality_value, m.species.name, m.current_hp, m.total_hp) for m in party if m is not None]}")
        log(f"[{TAG}] P0 warpdata location(+0x04)={warp_data(0x04)} "
            f"lastHeal(+0x1C)={warp_data(0x1C)} "
            f"(CONTROL: location's (group,num) must equal the LIVE map "
            f"{tuple(get_player_avatar().map_group_and_number)}; lastHeal PREDICTED (0,7,-1,43,32))")
        probes_run.append("P0")

        premise_ok = (
            here_map == "SKY_PILLAR_ENTRANCE"
            and at == (14, 3)
            and (city, sky, cry) == (5, 1, 1)
            and hm_flag is False
            and leave_flag is False
            and controllable
            and badge5 and has_surf and badge7 and has_dive
        )
        if not premise_ok:
            log(f"[{TAG}] !! VACUOUS - the fixture is not leg 5's premise (see the P0 lines "
                f"above). Every downstream reading would describe a state the leg does not start "
                f"in, so nothing is measured.")
            self.stop_reason = "VACUOUS premise"
            return

        # ============================ P1 - THE EXIT TO ROUTE131 ==============================
        entrance = MapRSE.SKY_PILLAR_ENTRANCE
        try:
            exit_plan = calculate_path((entrance, at), (entrance, (6, 15)))
        except Exception as error:  # noqa: BLE001 - a refusal here IS the reading
            log(f"[{TAG}] P1 PLAN REFUSED {at}->(6,15): {type(error).__name__}: {str(error)[:200]}")
            self.stop_reason = "P1 exit plan refused"
            return

        off_map = [w for w in exit_plan if tuple(w.map) != entrance.value]
        seam = [i for i, w in enumerate(exit_plan) if tuple(w.coordinates) == (14, 4)]
        log(f"[{TAG}] P1 plan {at}->(6,15) {len(exit_plan)} wp off_map={len(off_map)} "
            f"seam_14_4_at={seam} (PREDICTED all on ENTRANCE, seam absent)")
        if seam:
            log(f"[{TAG}] !! P1 REFUSING TO WALK - the plan routes over (14,4), the SOUTH ARROW "
                f"WARP back to SKY_PILLAR_OUTSIDE. Walking it would re-enter the tower and cost "
                f"the fixture. This is a RESULT the leg build must handle, not a driver bug.")
            self.stop_reason = "P1 plan routes over the (14,4) seam warp"
            return

        yield from budgeted(navigate_to(entrance, (6, 15)), 4000, "P1 approach (6,15)")
        yield from budgeted(navigate_to(entrance, (6, 16)), 4000, "P1 door (6,16)")
        yield from budgeted(wait_until_truly_controllable(), 3000, "P1 settle")
        here_map, rest131 = where()
        avatar = get_player_avatar()
        log(f"[{TAG}] P1 REST at={here_map}{rest131} facing={avatar.facing_direction} "
            f"flags={avatar.flags!r} tile_type="
            f"{getattr(get_map_data_for_current_position(), 'tile_type', None)!r} "
            f"(PREDICTED ROUTE131 (36,7), Down, on foot, sand)")
        probes_run.append("P1")
        if here_map != "ROUTE131":
            log(f"[{TAG}] !! P1 did not land on ROUTE131 - every downstream probe is about that "
                f"map, so the run stops here with the readings it has.")
            self.stop_reason = f"P1 landed on {here_map}, not ROUTE131"
            return

        # ====================== P2 - THE ROUTE131 LIVE-PIN A/B (GATE 1) ======================
        reading_before, agree_before = _route131_layout_reading()
        log(f"[{TAG}] P2 layout BEFORE pin: {reading_before} (PREDICTED agree=False)")

        def swim_plan(label: str) -> tuple:
            try:
                path = calculate_path((MapRSE.ROUTE131, rest131), (MapRSE.ROUTE126, (45, 66)))
            except Exception as error:  # noqa: BLE001 - a refusal IS an arm's reading
                log(f"[{TAG}] P2 arm {label}: REFUSED {type(error).__name__}: {str(error)[:200]}")
                return None, None, None
            surfs = [i for i, w in enumerate(path) if w.action is WaypointAction.Surf]
            on131 = [tuple(w.coordinates) for w in path if tuple(w.map) == MapRSE.ROUTE131.value]
            walls = _live_wall_tiles(MapRSE.ROUTE131, on131)
            first = describe(path[:1])
            log(f"[{TAG}] P2 arm {label}: {len(path)} wp surf_actions={len(surfs)} at={surfs[:4]} "
                f"first_wp={first} on131={len(on131)} live_walls_on_131={walls[:8]} "
                f"(n={len(walls)})")
            return path, len(surfs), len(walls)

        planner_elev_before = get_map_data(MapRSE.ROUTE131, rest131).elevation
        path_a, surfs_a, walls_a = swim_plan("A (static, as the planner seeded itself)")

        if nopin_arm:
            log(f"[{TAG}] P2N CONTROL ARM (CH21_PROBE_NOPIN131=1): NOT pinning. PREDICTED the swim "
                f"FAILS on ROUTE131 at the water's edge, on foot - the live KI-73 reproduction.")
            nopin_failed = False
            try:
                yield from budgeted(
                    _navigate_riding_out(MapRSE.ROUTE126, (45, 66), tries=2), 12000, "P2N swim"
                )
            except Exception as error:  # noqa: BLE001 - the FAILURE is the reading
                nopin_failed = True
                log(f"[{TAG}] P2N swim FAILED as predicted: {type(error).__name__}: "
                    f"{str(error)[:300]}")
            end_map, end_at = where()
            end_avatar = get_player_avatar()
            log(f"[{TAG}] P2N RESULT failed={nopin_failed} at={end_map}{end_at} "
                f"facing={end_avatar.facing_direction} flags={end_avatar.flags!r} "
                f"(PREDICTED failed=True, ROUTE131 (36,8), Down, on foot)")
            probes_run.append("P2N")
            # ⛔ The control arm ENDS here on purpose; `run()` grades it on its own predicate
            # ("the reading happened"), never on the swim working.
            self.stop_reason = self.CONTROL_ARM_DONE
            return

        pin_note = _pin_planner_to_live_layout(MapRSE.ROUTE131)
        log(f"[{TAG}] P2 PIN {pin_note}")
        reading_after, agree_after = _route131_layout_reading()
        log(f"[{TAG}] P2 layout AFTER pin: {reading_after} (PREDICTED agree=True)")
        planner_elev_after = get_map_data(MapRSE.ROUTE131, rest131).elevation
        path_b, surfs_b, walls_b = swim_plan("B (pinned to the LIVE header)")

        divergence = None
        if path_a is not None and path_b is not None:
            described_a, described_b = describe(path_a), describe(path_b)
            for index in range(min(len(described_a), len(described_b))):
                if described_a[index] != described_b[index]:
                    divergence = index
                    break
            if divergence is None and len(described_a) != len(described_b):
                divergence = min(len(described_a), len(described_b))
        differ = (surfs_a != surfs_b) or (walls_a != walls_b) or (divergence is not None) or (
            (path_a is None) != (path_b is None)
        )
        log(f"[{TAG}] P2 SOURCE-TILE ELEVATION planner_before={planner_elev_before} "
            f"planner_after={planner_elev_after} (PREDICTED 1 -> 3; map_path.py:916 seeds the "
            f"start node from THIS value, which is why a static 'deep water' source emits no "
            f"Surf mount)")
        log(f"[{TAG}] P2 DISCRIMINATOR surf_actions A={surfs_a} B={surfs_b} | "
            f"live_walls A={walls_a} B={walls_b} | first_divergent_wp={divergence} | "
            f"ARMS_DIFFER={differ} (PREDICTED A=0 B=1 -> DIFFER; identical arms would be "
            f"INCONCLUSIVE, not a refutation)")
        probes_run.append("P2")

        if _os.environ.get("POKEBOT_CH21_FAULT_PROBERAISE", "").strip() == "1":
            # ⛔ FAULT ARM (house rule 6: FAULT-TEST EVERY GATE). This raises where a lost battle
            # would raise `StoryAbort` - deep inside the probe, after real readings. It PASSES the
            # test by making the run print `!! PROBE RAISED`, the P0/P1/P2 readings, and
            # `ACCEPTANCE: FAIL`. Before the 2026-09-02 fix this same raise printed NOTHING.
            raise RuntimeError("Ch21 leg5 FAULT PROBERAISE: simulating a mid-probe abort")

        # ============================ P3 - THE RETURN SWIM + DIVE ============================
        yield from budgeted(
            _navigate_riding_out(MapRSE.ROUTE126, (45, 66), tries=30), 60000, "P3 swim"
        )
        here_map, at = where()
        tile_type = getattr(get_map_data_for_current_position(), "tile_type", None)
        log(f"[{TAG}] P3 SWIM arrived at={here_map}{at} tile_type={tile_type!r} "
            f"encounters_so_far={self.encounters} {self.encounter_maps}")
        if here_map != "ROUTE126" or at != (45, 66):
            log(f"[{TAG}] !! P3 did not reach the dive tile - stopping with the readings taken.")
            self.stop_reason = f"P3 stopped at {here_map}{at}, not the dive tile"
            return
        if tile_type not in ("Deep Water", "Interior Deep Water", "Semi-Deep Water",
                             "Sootopolis Deep Water"):
            log(f"[{TAG}] !! P3 refusing to dive - tile_type {tile_type!r} is not divable.")
            self.stop_reason = f"P3 dive tile is {tile_type!r}, not divable"
            return

        yield from budgeted(dive(), 3000, "P3 dive")
        yield from budgeted(
            navigate_to(MapRSE.UNDERWATER_ROUTE126, (45, 65), False), 6000, "P3 uw door"
        )
        here_map, uw_at = where()
        log(f"[{TAG}] P3 UNDERWATER arrived at={here_map}{uw_at} (PREDICTED "
            f"UNDERWATER_SOOTOPOLIS_CITY (9,8))")
        if here_map != "UNDERWATER_SOOTOPOLIS_CITY":
            log(f"[{TAG}] !! P3 the dive door did not land underwater in Sootopolis.")
            self.stop_reason = f"P3 dive door landed on {here_map}"
            return
        yield from budgeted(
            navigate_to(MapRSE.UNDERWATER_SOOTOPOLIS_CITY, (9, 7), False), 6000, "P3 emerge tile"
        )
        here_map, uw_at = where()
        uw_tile_type = getattr(get_map_data_for_current_position(), "tile_type", None)
        log(f"[{TAG}] P3 EMERGE-TILE at={here_map}{uw_at} tile_type={uw_tile_type!r} "
            f"(PREDICTED (9,7) 'Deep Water')")
        probes_run.append("P3")
        if uw_at != (9, 7) or uw_tile_type != "Deep Water":
            log(f"[{TAG}] !! P3 not on the hand-picked emerge tile - refusing to surface (KI-72: "
                f"25 of this map's 31 walkable tiles emerge under the crater wall and the GAME "
                f"will not stop it).")
            self.stop_reason = f"P3 not on the emerge tile ({uw_at}, {uw_tile_type!r})"
            return

        # ==================== P4 - SURFACE + THE RAYQUAZA-ARRIVAL SCENE ======================
        yield from budgeted(surface_from_dive(), 4000, "P4 surface")
        here_map, city_at = where()
        log(f"[{TAG}] P4 R-EMERGE uw_tile={uw_at} city_tile={city_at} map={here_map} "
            f"(PREDICTED SOOTOPOLIS_CITY (29,53) for ANY uw tile - the fixed `setdivewarp`, NOT "
            f"an (x,y)-preserving emerge. If this reads (29,53) the KI-72 wording in "
            f"sootopolis.py:25-32 is a DOC BUG owed a fix with the leg.)")
        if here_map != "SOOTOPOLIS_CITY":
            log(f"[{TAG}] !! P4 surfaced but not in SOOTOPOLIS_CITY.")
            self.stop_reason = f"P4 surfaced onto {here_map}"
            return

        try:
            yield from budgeted(
                _ride_summit_scene("SKY_PILLAR_STATE", 2, budget_frames=30000), 31000, "P4 scene"
            )
        except Exception as error:  # noqa: BLE001 - a stalled one-shot is a RESULT
            self.scene_failure = f"{type(error).__name__}: {str(error)[:300]}"
            log(f"[{TAG}] !! P4 SCENE RIDE FAILED: {self.scene_failure}")
        mid_map, mid_at = where()
        script_mid = get_global_script_context().is_active
        # ⛔ THE HEADLINE CARRIES THE CAVEAT. On the failure path the var may never have reached 2,
        # so "the instant SKY_PILLAR_STATE reached 2" would be a claim the value does not support.
        moment = ("the instant SKY_PILLAR_STATE reached 2" if self.scene_failure is None
                  else "AFTER THE SCENE RIDE FAILED - NOT proven to be mid-scene")
        log(f"[{TAG}] P4 MID-SCENE ({moment}) at={mid_map}{mid_at} "
            f"script_active={script_mid} controllable={player_avatar_is_controllable()} "
            f"(PREDICTED (29,49), script ACTIVE, controllable True *under lockall* - which is "
            f"exactly why the settle below exists and why no tile may be read here)")

        # ---- THE SETTLE (refuter finding F1). Four conjuncts, bounded, no state writes. ----
        static_header = _map_module._map_header_cache[context.rom.id][MapRSE.SOOTOPOLIS_CITY.value]
        settle_frames = 0
        # ⛔ FAULT ARM (house rule 6): a budget of 0 means the settle can NEVER succeed, which is
        # exactly the state the gate below exists to catch. It PASSES by refusing P5/P6 - i.e. by
        # NOT pinning the planner to the crisis-state layout and NOT printing PASS.
        settle_budget = 0 if _os.environ.get(
            "POKEBOT_CH21_FAULT_SCENESTOP", "").strip() == "1" else 6000
        while settle_frames < settle_budget:
            _check_abort()  # ⛔ FIRST statement of the loop body, outside any try
            if (
                not get_global_script_context().is_active
                and _var("SKY_PILLAR_STATE") == 3
                and read_symbol("gMapHeader")[:4] == static_header[:4]
                and player_avatar_is_controllable()
            ):
                self.settle_ok = True
                break
            if is_waiting_for_input():
                context.emulator.press_button("B")
            yield
            settle_frames += 1
        log(f"[{TAG}] P4 SETTLE ok={self.settle_ok} frames={settle_frames} "
            f"script_active={get_global_script_context().is_active} "
            f"SKY_PILLAR_STATE={_var('SKY_PILLAR_STATE')} "
            f"live_header=0x{unpack_uint32(read_symbol('gMapHeader')[:4]):08X} "
            f"static_header=0x{unpack_uint32(static_header[:4]):08X} "
            f"(all four conjuncts must hold: script quiet AND var==3 AND the LIVE header is back "
            f"to the map's own NORMAL layout AND controllable)")
        if self.settle_ok:
            yield from budgeted(wait_until_truly_controllable(), 3000, "P4 post-settle")

        here_map, rest_city = where()
        avatar = get_player_avatar()
        log(f"[{TAG}] P4 REST at={here_map}{rest_city} facing={avatar.facing_direction} "
            f"flags={avatar.flags!r} vars(CITY,SKY,CRY)=({_var('SOOTOPOLIS_CITY_STATE')},"
            f"{_var('SKY_PILLAR_STATE')},{_var('SKY_PILLAR_RAYQUAZA_CRY_DONE')}) "
            f"LEGENDARIES_IN_SOOTOPOLIS={get_event_flag('LEGENDARIES_IN_SOOTOPOLIS')} "
            f"HIDE_ARCHIE={get_event_flag('HIDE_SOOTOPOLIS_CITY_ARCHIE')} "
            f"HIDE_MAXIE={get_event_flag('HIDE_SOOTOPOLIS_CITY_MAXIE')} "
            f"(PREDICTED (29,53) Up, 5/3/1, False, False/False)")
        probes_run.append("P4")

        capturable = (
            self.settle_ok and here_map == "SOOTOPOLIS_CITY" and _var("SKY_PILLAR_STATE") == 3
            and self.whiteouts == 0 and self.scene_failure is None
        )
        _cap = _os.environ.get("CH21_CAPTURE_ARRIVAL", "").strip()
        if _cap:
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not capturable:
                log(f"[{TAG}] CAPTURE SKIPPED - not capturable (settle_ok={self.settle_ok} "
                    f"map={here_map} sky={_var('SKY_PILLAR_STATE')} whiteouts={self.whiteouts} "
                    f"scene_failure={self.scene_failure!r})")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[{TAG}] CAPTURE REFUSED - {_cap} exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[{TAG}] CAPTURE WROTE {_out} ({_out.stat().st_size} bytes) at "
                    f"{here_map}{rest_city} - !! verify with probe_anchor_inventory.py, never "
                    f"with this line")

        # ⛔⛔ THE SETTLE GATE - EVERYTHING BELOW IS ABOUT THE **STATE-5 NORMAL** LAYOUT.
        # Found by adversarial review before this driver ever ran: without this gate a timed-out
        # settle (or a raised scene ride) fell straight through into
        # `_pin_planner_to_live_layout(SOOTOPOLIS_CITY)`, whose ONLY guard is "am I on this map" —
        # so mid-scene it would pin the planner to `LAYOUT_SOOTOPOLIS_CITY_LEGENDS_BATTLE` (the
        # crisis layout that runs at states 1-4) and every P5/P6 reading would describe the WRONG
        # map while the run still printed PASS. ⇒ a FALSE PASS that looks clean is worse than a
        # crash, and this project has shipped that shape before (§Ch15/18/19 each PASSED stranded).
        if not self.settle_ok or self.scene_failure is not None:
            log(f"[{TAG}] !! P5/P6 REFUSED - the arrival never settled (settle_ok="
                f"{self.settle_ok} scene_failure={self.scene_failure!r}). Pinning or reading the "
                f"layout now would measure the CRISIS-state map and label it state 5.")
            self.stop_reason = "P4 settle failed; P5/P6 refused rather than measure the wrong map"
            return

        # ================ P5 - THE STATE-5 LAYOUT, THE TEMPLATES, THE MATRIX =================
        static_grid, width, height = static_collision_grid(MapRSE.SOOTOPOLIS_CITY)
        soot_pin = _pin_planner_to_live_layout(MapRSE.SOOTOPOLIS_CITY)
        log(f"[{TAG}] P5 PIN {soot_pin} (PREDICTED a NO-OP: same blockdata on both sides. A pin "
            f"that changes nothing is NOT a fix and must never be reported as one.)")
        live_grid = _live_collision_grid(MapRSE.SOOTOPOLIS_CITY)
        deltas = sorted(t for t in static_grid if live_grid.get(t) != static_grid[t])
        # ⛔ THE COUNT ALONE IS NOT THE READING. "10 tiles differ" cannot tell a caller whether the
        # planner is about to walk into a live WALL (static 0 / live 1 - the KI-73 failure) or is
        # merely refusing a tile the game would allow (static 1 / live 0 - harmless). Print the
        # DIRECTION per tile, and count the dangerous direction separately.
        detail = [(t, static_grid[t], live_grid.get(t)) for t in deltas]
        opens_to_us = [t for t, s, l in detail if s == 0 and l != 0]
        log(f"[{TAG}] P5 COLLISION DIFF map={width}x{height} live_vs_static_deltas={len(deltas)} "
            f"OPEN-to-planner/WALL-live={len(opens_to_us)} {opens_to_us} "
            f"(PREDICTED 0 - a nonzero count is a FINDING about the 'DIRTY post-crisis layout' "
            f"claim in 04-HANDOFF; only the OPEN-to-planner/WALL-live direction can strand a walk)")
        log(f"[{TAG}] P5 COLLISION DIFF DETAIL (tile, static, live) {detail}")

        templates = get_save_block(1, 0xC70, 64 * 24)
        parsed = []
        for i in range(64):
            block = templates[i * 24:(i + 1) * 24]
            local_id = block[0]
            if local_id == 0:
                continue
            parsed.append((
                local_id,
                block[1],
                _struct.unpack("<h", block[4:6])[0],
                _struct.unpack("<h", block[6:8])[0],
                _struct.unpack("<H", block[0x14:0x16])[0],
            ))
        by_id = {entry[0]: entry for entry in parsed}
        log(f"[{TAG}] P5 TEMPLATES n={len(parsed)} ids={sorted(by_id)} "
            f"(CONTROL: exactly 18 entries with ids 1..18 - the map.json count. A different count "
            f"means this offset is not objectEventTemplates and NO position below is trustworthy.)")
        log(f"[{TAG}] P5 TEMPLATE-CONTROL id2(Woman4, never moved by any script)="
            f"{by_id.get(2)} (map.json says x=47 y=33; a reading of 54/40 would mean these "
            f"coordinates carry the +7 MAP_OFFSET and every prediction below shifts with it)")
        log(f"[{TAG}] P5 TEMPLATES steven7={by_id.get(7)} maxie16={by_id.get(16)} "
            f"archie17={by_id.get(17)} wallace18={by_id.get(18)} "
            f"(PREDICTED x,y = (29,33) (33,35) (34,35) (31,33) after SetOutsideGymObjPos; "
            f"map.json ROM defaults are (20,36) (29,33) (31,33) (31,18))")
        objects("at-rest")
        log(f"[{TAG}] P5 NOTE an EMPTY object list here is PREDICTED, not a finding: objects "
            f"spawn only within roughly [y-7, y+9] of the player and the NPCs sit ~20 tiles north.")

        control_tile = (33, 34)
        control_live = live_grid.get(control_tile)
        if control_live == 0:
            candidates = [t for t in ((33, 34), (32, 34), (34, 33), (30, 34), (35, 34))
                          if live_grid.get(t, 0) != 0]
            log(f"[{TAG}] !! P5 the intended negative control {control_tile} is collision "
                f"{control_live} in the LIVE grid - it is NOT a wall. Substituting "
                f"{candidates[0] if candidates else None} and SAYING SO; a control that can path "
                f"is decoration.")
            if candidates:
                control_tile = candidates[0]
        log(f"[{TAG}] P5 CONTROL-TILE {control_tile} live_collision={live_grid.get(control_tile)}")
        matrix_rest = path_matrix("rest", [(33, 36), (32, 35), (34, 36), (34, 34), (31, 34),
                                           (43, 32)], control_tile)
        probes_run.append("P5")

        # ========================= P6 - ONE WALK TO THE NPC APPROACH =========================
        if isinstance(matrix_rest.get((33, 36)), int):
            try:
                plan = calculate_path((MapRSE.SOOTOPOLIS_CITY, rest_city),
                                      (MapRSE.SOOTOPOLIS_CITY, (33, 36)))
                walls = _live_wall_tiles(MapRSE.SOOTOPOLIS_CITY,
                                         [tuple(w.coordinates) for w in plan])
                log(f"[{TAG}] P6 PLAN {len(plan)} wp live_walls={walls} (PREDICTED 0)")
            except Exception as error:  # noqa: BLE001
                log(f"[{TAG}] P6 plan re-read failed: {type(error).__name__}: {str(error)[:200]}")
            walked = False
            try:
                yield from budgeted(
                    _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, (33, 36), tries=6), 12000,
                    "P6 walk"
                )
                walked = True
            except Exception as error:  # noqa: BLE001 - a failed walk is a RESULT
                log(f"[{TAG}] !! P6 WALK FAILED: {type(error).__name__}: {str(error)[:300]}")
            here_map, at = where()
            log(f"[{TAG}] P6 walked={walked} at={here_map}{at} "
                f"facing={get_player_avatar().facing_direction}")
            objects("at-33-36")
            log(f"[{TAG}] P6 (PREDICTED loaded: 16@(33,35) 17@(34,35) 18@(31,33) 7@(29,33))")
            path_matrix("at-33-36", [(34, 36), (34, 34), (31, 34), (32, 35)], control_tile)
            probes_run.append("P6")
        else:
            log(f"[{TAG}] !! P6 SKIPPED - the rest tile could not plan to (33,36) "
                f"({matrix_rest.get((33, 36))}); that refusal is itself the finding.")

        # ⛔ NO VERDICT HERE. `run()` owns the single ACCEPTANCE line, so that a raise anywhere
        # above still reaches it. A second verdict site is how a partial run prints PASS.


class Ch21ReturnMode(BotMode):
    """§Ch21 LEG 5 — THE RETURN AND HM07 WATERFALL. Drives `sootopolis.return_and_get_waterfall`.

    ‼ IT CALLS THE PRODUCTION ENTRY POINT, never a copy — the standing rule of every §Ch21 driver.

    THE GRADE (house rule 8 — §Ch15/§Ch18/§Ch19 each PASSED their own test while STRANDED):
      every reading happened AND the ORDER trace matches AND `RECEIVED_HM_WATERFALL` is SET AND
      **HM07 is in the bag by ITEM ID** AND the bot ends on SOOTOPOLIS_CITY with a live
      `calculate_path` to the continuation target AND the planner still REFUSES the control tile
      AND whiteouts == 0.
    ⛔ WHY THE ITEM AND NOT JUST THE FLAG: `giveitem ITEM_HM_WATERFALL` and
    `setflag FLAG_RECEIVED_HM_WATERFALL` are ADJACENT decomp lines but not the same fact — a full
    bag fails the first and not the second. The flag corroborates; the item and the path decide.

    ⛔ ONE-SHOTS ON THIS LEG, in order: the Rayquaza ARRIVAL cutscene (SKY_PILLAR_STATE 1->2->3),
    the two leader talks (the SECOND sets 0x9E and `warpsilent`s the player to (31,34)), and
    Wallace's gift. None replay. The leg captures `CH21_CAPTURE_ARRIVAL` between the arrival and
    the talks so the NPC half can be iterated without re-swimming.

    FAULT ARMS (env-read inside the LEG, so they are driver-proof; the happy path reaches none):
      POKEBOT_CH21_FAULT_NOPIN131=1    skip the ROUTE131 pin: the swim must fail NAMED, bounded.
      POKEBOT_CH21_FAULT_SETTLESKIP=1  skip the arrival settle: the gate must RAISE before anything
                                       pins or reads the city layout.
      POKEBOT_CH21_FAULT_SCENESTOP=1   return at the arrival — the §Ch15/18/19 shape exactly.
                                       ⛔ THE MOST IMPORTANT ARM: it must FAIL with missing= naming
                                       every NPC and HM07 reading.
      POKEBOT_CH21_FAULT_NPCMISS=1     face away on the first Maxie approach: the missed-press bail
                                       must fire and the retry must recover. PASS is still expected.
      POKEBOT_CH21_FAULT_DROPREADING=1 suppress R-HM07 at its take point: missing=['R-HM07'], FAIL.
      POKEBOT_CH21_FAULT_CONTROLOPEN=1 aim R-CONTROL at a reachable tile: control_refused=False,
                                       FAIL — a control that cannot fail is decoration.
      (no env var) THE VACUITY ARM     point this driver at its OWN output fixture: the leg's
                                       preflight sees `RECEIVED_HM_WATERFALL` already SET and
                                       raises "this leg is SPENT" -> premise FAIL.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_rayquaza_gone.ss1 --driver ch21return \
             --frames 60000
    ‼ THE BUDGET IS AN ESTIMATE ANCHORED ON A MEASUREMENT: the PART C probe walked the identical
    route (exit, swim, dive, arrival, one city walk) in **16,297 frames** with 7 encounters. The
    three talks and the second city walk are the only additions. ⛔ REPLACE IT with drive 1's
    `frames=` line.
    """

    @staticmethod
    def name() -> str:
        return "Ch21Return"

    def __init__(self):
        super().__init__()
        self.encounters = 0
        self.encounter_maps: list[str] = []
        self.whiteouts = 0

    def on_whiteout(self) -> bool:
        # ⛔ True + latch (leg 3's B1 fix): returning False hands the run to Manual and DISCARDS
        # this generator, so the RESULT/ACCEPTANCE block would never print. On THIS leg a whiteout
        # respawns at the Sootopolis PC — inside the leg's own map, with the vars unchanged — which
        # is exactly why the grade is POSITION + PATH + ITEM and never vars alone.
        self.whiteouts += 1
        log("[ch21return] !! WHITEOUT - respawning at the Sootopolis PC; latching the story abort "
            "so a verdict still prints.")
        try:
            from modules.story.early_game import set_story_abort

            set_story_abort(True)
        except Exception as error:  # noqa: BLE001 - never let the hook itself end the run
            log(f"[ch21return] !! could not latch the abort: {type(error).__name__}: {error}")
            return False
        return True

    def on_battle_started(self, encounter):
        self.encounters += 1
        try:
            from modules.player import get_player_avatar

            self.encounter_maps.append(str(tuple(get_player_avatar().map_group_and_number)))
        except Exception:  # noqa: BLE001 - the count is what matters
            self.encounter_maps.append("?")
        return super().on_battle_started(encounter)

    def run(self):
        from modules.map_data import MapRSE
        from modules.memory import get_event_var
        from modules.player import get_player_avatar
        from modules.story import sootopolis as ch21

        TAG = "ch21return"
        frames_before = context.emulator.get_frame_count()

        def where() -> tuple[str, tuple[int, int]]:
            avatar = get_player_avatar()
            coordinates = tuple(avatar.local_coordinates)
            try:
                return MapRSE(tuple(avatar.map_group_and_number)).name, coordinates
            except Exception:  # noqa: BLE001
                return f"UNKNOWN{tuple(avatar.map_group_and_number)}", coordinates

        start_name, start_at = where()
        start_vars = (get_event_var("SOOTOPOLIS_CITY_STATE"), get_event_var("SKY_PILLAR_STATE"),
                      get_event_var("SKY_PILLAR_RAYQUAZA_CRY_DONE"))
        start_hm = ch21.waterfall_received()
        start_bag = ch21._hm07_in_bag()
        log(f"[{TAG}] PRE at={start_name}{start_at} vars={start_vars} hm_flag={start_hm} "
            f"hm07_in_bag={start_bag} leaders_left={ch21.leaders_have_left()} "
            f"wallace_state={get_event_var('SOOTOPOLIS_WALLACE_STATE')} "
            f"(a full run requires SKY_PILLAR_ENTRANCE, (5,1,1), flag CLEAR, bag 0)")
        # ⛔ THE GYM DOOR IS THE CHAPTER'S REAL CONTINUATION TARGET: (31,32) warps to
        # SOOTOPOLIS_CITY_GYM_1F, i.e. Juan, i.e. the NEXT chapter — and Wallace stands on (31,33),
        # directly south of it, until his gift script moves him aside.
        try:
            from modules.map_path import calculate_path as _cp

            _here = (MapRSE(tuple(get_player_avatar().map_group_and_number)),
                     tuple(get_player_avatar().local_coordinates))
            _p = _cp(_here, (MapRSE.SOOTOPOLIS_CITY, (31, 32)))
            log(f"[{TAG}] PRE gym-door (31,32) reachable: OK {len(_p)} wp")
        except Exception as _e:  # noqa: BLE001 - a refusal IS the reading
            log(f"[{TAG}] PRE gym-door (31,32) reachable: {type(_e).__name__}: {str(_e)[:200]}")

        # ⛔ THE DRIVER OWNS THE REPORT DICT AND HANDS IT IN — a dict RETURNED by a raising
        # generator never arrives, and the failed run is the one whose partial readings matter.
        report: dict = {}
        failure = None
        try:
            yield from ch21.return_and_get_waterfall(report)
        except Exception as error:  # noqa: BLE001 - the driver REPORTS failures, never hides them
            failure = f"{type(error).__name__}: {str(error)[:600]}"
            log(f"[{TAG}] LEG FAILED: {failure}")

        readings = set(report.get("readings") or ())
        trace = list(report.get("trace") or ())
        here_name, at = where()
        end_vars = (get_event_var("SOOTOPOLIS_CITY_STATE"), get_event_var("SKY_PILLAR_STATE"),
                    get_event_var("SKY_PILLAR_RAYQUAZA_CRY_DONE"))

        # ⛔ required set IMPORTED from the leg — a private copy is the P5 shape (a fact in two
        # places, one of them updated).
        required = set(ch21.LEG5_READINGS)
        missing = sorted(required - readings)

        # ⛔ ORDER IS PART OF THE PREDICATE: a readings SET cannot distinguish "got HM07, then
        # proved it can continue" from the reverse.
        order_iter = iter(trace)
        order_ok = all(any(step == want for step in order_iter) for want in ch21.LEG5_ORDER)

        # ⛔ THE VACUITY GATE. The leg's own OUTPUT fixture has the HM flag SET, which is the one
        # conjunct false there — and the leg itself raises on it, so this also asserts that raise
        # actually happened rather than trusting it.
        premise_ok = (
            start_name == "SKY_PILLAR_ENTRANCE"
            and start_vars[0] == 5 and start_vars[1] == 1
            and start_hm is False and start_bag == 0
            and report.get("phase") == "full"
        )
        if not premise_ok:
            log(f"[{TAG}] !! VACUOUS/RESUMED PREMISE - start={start_name}{start_at} "
                f"vars={start_vars} hm_flag={start_hm} bag={start_bag} "
                f"phase={report.get('phase')}. Only a full run from the leg-4 output fixture can "
                "PASS; a run from this leg's OWN output satisfies every end-state check while "
                "doing nothing.")

        hm_flag = ch21.waterfall_received()
        hm_bag = ch21._hm07_in_bag()
        continue_ok = bool(report.get("continue_ok"))
        control_refused = bool(report.get("control_refused"))
        passed = (
            failure is None
            and premise_ok
            and order_ok
            and not missing
            and hm_flag
            and hm_bag >= 1
            and here_name == "SOOTOPOLIS_CITY"
            and continue_ok
            and control_refused
            and self.whiteouts == 0
        )
        # capture gate — NARROWER than `passed` (a raise AFTER the gift must not cost the fixture,
        # and a fixture without the HM would be a trap for the next session).
        capturable = (
            hm_flag and hm_bag >= 1 and here_name == "SOOTOPOLIS_CITY"
            and self.whiteouts == 0 and premise_ok
        )

        total = context.emulator.get_frame_count() - frames_before
        log(f"[{TAG}] RESULT at={here_name}{at} phase={report.get('phase')} "
            f"hm_flag={hm_flag} hm07_in_bag={hm_bag} "
            f"wallace_state={report.get('wallace_state_after')} "
            f"gym_door_wp={report.get('gym_wp')} "
            f"encounters={self.encounters} maps={self.encounter_maps} "
            f"whiteouts={self.whiteouts} frames={total}")
        log(f"[{TAG}] ROUTE route131_rest={report.get('route131_rest')} "
            f"emerge={report.get('emerge')} mid_scene={report.get('mid_scene_tile')} "
            f"city_rest={report.get('city_rest')} warp_landing={report.get('warp_landing')} "
            f"(PART C measured (36,7) / ((9,7),(29,53)) / (29,49) / (29,53); the warp landing is "
            f"the DECOMP's (31,34) and had never been observed live before this leg)")
        log(f"[{TAG}] PINS {report.get('pins')} (the ROUTE131 pin is LOAD-BEARING - measured by an "
            f"arm with it REMOVED; the Sootopolis pins are expected NO-OPs and are never a fix)")
        log(f"[{TAG}] VARS start={start_vars} end={end_vars} "
            f"(the leg is graded on ITEM + POSITION + PATH; vars corroborate - a whiteout respawns "
            f"in this very city, which is why they cannot decide alone)")
        log(f"[{TAG}] CONTINUE continue_wp={report.get('continue_wp')} continue_ok={continue_ok} "
            f"control_refused={control_refused}")
        log(f"[{TAG}] ORDER order_ok={order_ok} trace={trace}")
        log(f"[{TAG}] METHOD premise_ok={premise_ok} failure={failure}")
        log(f"[{TAG}] readings={sorted(readings)} missing={missing} "
            f"(the grade is DID EVERY READING HAPPEN, IN ORDER, **and does the bot HOLD THE HM and "
            f"can it CONTINUE**)")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")

        _cap = _os.environ.get("CH21_CAPTURE", "").strip()
        if _cap:
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not capturable:
                log(f"[{TAG}] CAPTURE SKIPPED - not capturable (hm_flag={hm_flag} bag={hm_bag} "
                    f"at={here_name} whiteouts={self.whiteouts} premise_ok={premise_ok})")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[{TAG}] CAPTURE REFUSED - {_cap} exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[{TAG}] CAPTURE WROTE {_out.name} ({_out.stat().st_size} bytes) at {at} "
                    f"- !! verify with probe_anchor_inventory.py, not this line")

        context.set_manual_mode()


class Ch21ChapterMode(BotMode):
    """§Ch21 AS A CHAPTER — drives `sootopolis.do_sootopolis_chapter()`, not a copy of it.

    ‼ THE POINT OF THIS DRIVER IS THE ASSEMBLY, NOT THE LEGS. Every leg is already proven on its
    own fixture (`ch21dive` / `ch21escort` / `ch21cave` / `ch21approach` / `ch21climb` /
    `ch21return`). What has NEVER been run is the ORCHESTRATION — and §Ch20's experience is that
    the glue is where the blockers live: an adversarial review of THAT chapter's assembly found
    FOUR, all in the glue and none in the rooms.

    ⛔⛔ NOTHING HAS EVER DRIVEN LEGS 1 -> 5 IN SEQUENCE. Every fixture in the tree is a per-leg
    pin, so this driver's FIRST RUN is also the first measurement of:
      * the chapter's total frame cost (the known legs alone sum to >64,000: leg 3 = 34,122,
        leg 5 = 20,705, leg 4 = 10,079 — legs 1/2a/2b have never been timed);
      * whether the party SURVIVES the whole chapter. `post_ch20.ss1` starts with ONE FAINTED
        member at 80% HP, the only heals are leg 2a's and leg 3's (`sootopolis.py:409`, `:1463`),
        and there is NO Poke Center after leg 3 — legs 4 and 5 are pinned at 91%.
    ⇒ a FAIL on the first drive is a MEASUREMENT, not necessarily a defect. Read the readings.

    THE GRADE (house rule 8 — §Ch15/§Ch18/§Ch19 each PASSED their own test while STRANDED):
      the chapter predicate holds (flag AND `SOOTOPOLIS_WALLACE_STATE != 0`) AND HM07 is in the bag
      BY ITEM ID AND the bot stands on SOOTOPOLIS_CITY AND **a real `calculate_path` reaches the
      GYM DOOR (31,32)** AND the Poke Center (43,32) is reachable AND whiteouts == 0.
    ⛔ THE GYM-DOOR PATH IS THE LOAD-BEARING CONJUNCT, and it is the one leg-5 drive 1 would have
    failed: that run held HM07, printed PASS, and had SEALED §Ch22's entrance because Wallace never
    stepped off (31,33). "The bot can still path somewhere" is not the predicate; "the bot can
    reach what the NEXT chapter starts at" is.

    ⚠ A WHITEOUT IS TERMINAL **IN THIS HARNESS**, and that is not what production does. `on_whiteout`
    latches the story abort, the chapter re-raises it (KI-67), and the run ends with a verdict. In
    production `StoryMode.run` clears the latch and re-enters the chapter, bounded at 40 recoveries
    (`story_mode.py:2624`). ⇒ do NOT read a whiteout here as "the chapter cannot recover".

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_ch20.ss1 --driver ch21chapter --frames 250000
    ‼ THE BUDGET IS A GUESS ANCHORED ON A FLOOR, not a measurement. ⛔ REPLACE IT with drive 1's
    `frames=` line.
    """

    @staticmethod
    def name() -> str:
        return "Ch21Chapter"

    def __init__(self):
        super().__init__()
        self.encounters = 0
        self.encounter_maps: list[str] = []
        self.whiteouts = 0

    def on_whiteout(self) -> bool:
        # ⛔ True + latch: returning False hands the run to Manual and DISCARDS this generator, so
        # the RESULT/ACCEPTANCE block would never print.
        self.whiteouts += 1
        log(f"[ch21chapter] !! WHITEOUT #{self.whiteouts} - latching the story abort so a verdict "
            "still prints. (In PRODUCTION this is recoverable: StoryMode.run clears the latch and "
            "re-enters the chapter, bounded at 40 recoveries. Here it is terminal by design.)")
        try:
            from modules.story.early_game import set_story_abort

            set_story_abort(True)
        except Exception as error:  # noqa: BLE001 - never let the hook itself end the run
            log(f"[ch21chapter] !! could not latch the abort: {type(error).__name__}: {error}")
            return False
        return True

    def on_battle_started(self, encounter):
        self.encounters += 1
        try:
            from modules.player import get_player_avatar

            self.encounter_maps.append(str(tuple(get_player_avatar().map_group_and_number)))
        except Exception:  # noqa: BLE001 - the count is what matters
            self.encounter_maps.append("?")
        return super().on_battle_started(encounter)

    def run(self):
        from modules.map_data import MapRSE
        from modules.map_path import PathFindingError, calculate_path
        from modules.memory import get_event_var
        from modules.player import get_player_avatar
        from modules.pokemon_party import get_party
        from modules.story import sootopolis as ch21

        TAG = "ch21chapter"
        frames_before = context.emulator.get_frame_count()

        def where() -> tuple[str, tuple[int, int]]:
            avatar = get_player_avatar()
            coordinates = tuple(avatar.local_coordinates)
            try:
                return MapRSE(tuple(avatar.map_group_and_number)).name, coordinates
            except Exception:  # noqa: BLE001
                return f"UNKNOWN{tuple(avatar.map_group_and_number)}", coordinates

        start_name, start_at = where()
        start_vars = (get_event_var("SOOTOPOLIS_CITY_STATE"), get_event_var("SKY_PILLAR_STATE"))
        start_party = [(m.personality_value, m.species.name, m.current_hp, m.total_hp)
                       for m in get_party() if m is not None]
        # ⛔ THE VACUITY GATE, AND IT IS NOT HYPOTHETICAL — THE FIRST SMOKE TEST OF THIS DRIVER
        # TRIPPED IT. Pointed at the chapter's OWN end fixture (`post_hm07.ss1`), the orchestrator
        # correctly returns immediately (`if ch21_chapter_done(): return`, resume-safe) and every
        # END-state conjunct below is satisfied — so the run printed `ACCEPTANCE: PASS` having
        # executed ZERO frames. A grade that a no-op satisfies is not a grade.
        start_done = ch21.ch21_chapter_done()
        log(f"[{TAG}] PRE at={start_name}{start_at} vars(CITY,SKY)={start_vars} "
            f"done={start_done} hm_flag={ch21.waterfall_received()} "
            f"party={start_party}")
        log(f"[{TAG}] PRE ‼ the party's STARTING health is part of the measurement: this chapter "
            f"has only two heals (legs 2a and 3) and NO Poke Center after leg 3.")

        failure = None
        try:
            yield from ch21.do_sootopolis_chapter()
        except Exception as error:  # noqa: BLE001 - the driver REPORTS failures, never hides them
            failure = f"{type(error).__name__}: {str(error)[:800]}"
            log(f"[{TAG}] CHAPTER FAILED: {failure}")

        here_name, at = where()
        done = ch21.ch21_chapter_done()
        hm_flag = ch21.waterfall_received()
        hm_bag = ch21._hm07_in_bag()
        wallace_state = get_event_var("SOOTOPOLIS_WALLACE_STATE")
        end_vars = (get_event_var("SOOTOPOLIS_CITY_STATE"), get_event_var("SKY_PILLAR_STATE"))
        end_party = [(m.personality_value, m.species.name, m.current_hp, m.total_hp)
                     for m in get_party() if m is not None]

        # ⛔ COMPUTED INLINE, from the tile the run ACTUALLY reached — never a hardcoded source.
        def reachable(target) -> object:
            if here_name != "SOOTOPOLIS_CITY":
                return f"not-in-city({here_name})"
            try:
                return len(calculate_path((MapRSE.SOOTOPOLIS_CITY, at),
                                          (MapRSE.SOOTOPOLIS_CITY, target)))
            except (PathFindingError, KeyError, IndexError, ValueError, RuntimeError) as error:
                return f"{type(error).__name__}"

        gym_path = reachable(ch21.L5_GYM_DOOR)
        continue_path = reachable(ch21.L5_CONTINUE)

        # ⛔ `premise_ok` is a CONJUNCT of the grade, not a warning: only a run that STARTED with
        # the chapter unfinished can pass it.
        premise_ok = not start_done
        if not premise_ok:
            log(f"[{TAG}] !! VACUOUS - the chapter was ALREADY DONE at frame 0 "
                f"(at={start_name}{start_at}). The orchestrator's resume-safe early return is "
                f"CORRECT behaviour, but this run measured nothing: every end-state conjunct below "
                f"was true before it started.")
        passed = (
            failure is None
            and premise_ok
            and done
            and hm_bag >= 1
            and wallace_state != 0
            and here_name == "SOOTOPOLIS_CITY"
            and isinstance(gym_path, int)
            and isinstance(continue_path, int)
            and self.whiteouts == 0
        )

        total = context.emulator.get_frame_count() - frames_before
        log(f"[{TAG}] RESULT done={done} hm_flag={hm_flag} hm07_in_bag={hm_bag} "
            f"wallace_state={wallace_state} at={here_name}{at} "
            f"vars start={start_vars} end={end_vars} "
            f"encounters={self.encounters} whiteouts={self.whiteouts} frames={total}")
        log(f"[{TAG}] CONTINUE gym_door{ch21.L5_GYM_DOOR}={gym_path} "
            f"poke_center{ch21.L5_CONTINUE}={continue_path} "
            f"(⛔ THE GYM DOOR IS THE LOAD-BEARING ONE — it is what §Ch22 starts at, and it is the "
            f"check leg-5 drive 1 would have failed while printing PASS)")
        log(f"[{TAG}] PARTY start={start_party}")
        log(f"[{TAG}] PARTY end={end_party} (‼ the chapter has two heals and no Poke Center after "
            f"leg 3 — a chipped or fainted end party is a MEASUREMENT this drive exists to take)")
        log(f"[{TAG}] MAPS encounters_on={self.encounter_maps}")
        log(f"[{TAG}] METHOD premise_ok={premise_ok} (False = the chapter was already done at "
            f"frame 0 and this run proves nothing)")
        log(f"[{TAG}] FAILURE {failure}")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")

        _cap = _os.environ.get("CH21_CAPTURE", "").strip()
        if _cap:
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not passed:
                log(f"[{TAG}] CAPTURE SKIPPED - the run did not pass (done={done} bag={hm_bag} "
                    f"wallace_state={wallace_state} at={here_name} whiteouts={self.whiteouts})")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[{TAG}] CAPTURE REFUSED - {_cap} exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[{TAG}] CAPTURE WROTE {_out.name} ({_out.stat().st_size} bytes) at {at} "
                    f"- !! verify with probe_anchor_inventory.py, not this line")

        context.set_manual_mode()


class Ch22ProbeMode(BotMode):
    """§Ch22 PART A — the read-mostly probe that decides how the chapter gets built.

    ‼ IT ANSWERS THREE QUESTIONS THAT CANNOT BE SETTLED ON PAPER, and predictions for every reading
    were filed BEFORE it ran in `ai-research-notes/2026-09-02-ch22-PARTA-PREDICTIONS.md`.

    ⛔⛔ P3 IS THE POINT: AN EMPIRICAL A/B OF AN INSTRUMENT WE ALREADY TRUST TOO MUCH.
    `_live_collision_grid` + `probe_live_mapgrid.py` cracked KI-73 for §Ch21 and are described in
    `02-ARCHITECTURE.md` as "the oracle for can the bot actually step there". In THIS gym they are a
    FALSE NEGATIVE BY CONSTRUCTION — verified statically at three links (our reader keeps only
    `(block & 0x0C00) >> 10`; `ScrCmd_setmetatile` ORs `MAPGRID_IMPASSABLE` only when its 4th arg is
    TRUE; the gym passes FALSE on all of them). Static verification is an argument. **P3 takes ONE
    ice step and shows the metatile grid changing while the collision grid does not.** That is the
    difference between "I reasoned it out" and "I measured it", and this project's history says the
    first one is where the mistakes live.

    ⛔ A reading that contradicts a prediction is a RESULT, never a driver failure — including the
    FALSIFIER: if the collision diff also moves, my static analysis was wrong and the KI-73 note
    written today needs correcting.

    SAFETY / REVERSIBILITY: exactly ONE ice tile is stepped on, and the puzzle resets on every map
    change (`ClearTempFieldEventData()` + `OnTransition`), which P5 verifies by re-entering. No
    state writes, no fixture capture, no battles sought, nobody talked to.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1 --driver ch22probe --frames 40000
    """

    @staticmethod
    def name() -> str:
        return "Ch22Probe"

    def __init__(self):
        super().__init__()
        self.encounters = 0
        self.whiteouts = 0
        self.probes_run: list[str] = []
        self.stop_reason: str | None = None
        self.failure: str | None = None
        # the P3 headline conjuncts — initialised False so a run that never reaches P3 cannot pass
        self.stepped = False
        self.mt_moved = False
        self.col_moved = False

    def on_whiteout(self) -> bool:
        self.whiteouts += 1
        log("[ch22probe] !! WHITEOUT - latching the story abort so a verdict still prints.")
        try:
            from modules.story.early_game import set_story_abort

            set_story_abort(True)
        except Exception as error:  # noqa: BLE001
            log(f"[ch22probe] !! could not latch the abort: {type(error).__name__}: {error}")
            return False
        return True

    def on_battle_started(self, encounter):
        self.encounters += 1
        return super().on_battle_started(encounter)

    def run(self):
        """Thin wrapper so a raise anywhere still prints a verdict (the leg-5 probe's lesson)."""
        TAG = "ch22probe"
        frames_before = context.emulator.get_frame_count()
        try:
            yield from self._probe()
        except Exception as error:  # noqa: BLE001 - the driver REPORTS failures, never hides them
            self.failure = f"{type(error).__name__}: {str(error)[:600]}"
            log(f"[{TAG}] !! PROBE RAISED: {self.failure}")

        done = set(self.probes_run)
        # ⛔ THE GRADE REQUIRES THE HEADLINE MEASUREMENT ITSELF, not just that P3's block ran:
        # the ice step must have HAPPENED (`stepped`) and the metatile grid must have MOVED.
        # `col_moved` is deliberately NOT a pass condition — it is the FALSIFIER: if the collision
        # grid also moved, my static analysis was wrong and that is a RESULT to report, not a fail.
        passed = (
            {"P0", "P1", "P2", "P3", "P4", "P5"}.issubset(done)
            and self.whiteouts == 0
            and self.failure is None
            and self.stop_reason is None
            and self.stepped
            and self.mt_moved
        )
        log(f"[{TAG}] probes run: {sorted(done)} whiteouts={self.whiteouts} "
            f"encounters={self.encounters} "
            f"frames={context.emulator.get_frame_count() - frames_before}")
        log(f"[{TAG}] VERDICT INPUTS stop_reason={self.stop_reason!r} failure={self.failure!r} "
            f"stepped={self.stepped} metatile_moved={self.mt_moved} collision_moved={self.col_moved} "
            f"(collision_moved is the FALSIFIER, not a pass condition: if it is True my static "
            f"analysis was wrong and KI-73's new paragraph needs correcting)")
        log(f"[{TAG}] GRADE: this probe MEASURES; being right was never the bar. Compare every line "
            f"to ai-research-notes/2026-09-02-ch22-PARTA-PREDICTIONS.md.")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        context.set_manual_mode()

    def _probe(self):
        from modules.map import get_map_data
        from modules.map_data import MapRSE, PokemonCenter
        from modules.map_path import PathFindingError, calculate_path
        from modules.memory import get_event_flag, get_event_var
        from modules.modes.util.higher_level_actions import heal_in_pokemon_center
        from modules.player import get_player, get_player_avatar
        from modules.pokemon_party import get_party
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable
        from modules.story.sootopolis import (
            _live_collision_grid,
            _live_metatile_grid,
            _bounded_step,
        )

        TAG = "ch22probe"
        GYM = MapRSE.SOOTOPOLIS_CITY_GYM_1F
        THIN_ICE = (0x20D, 0x215)
        CRACKED, BROKEN, LOCKED_STAIRS = 0x20E, 0x206, 0x20F

        def where():
            a = get_player_avatar()
            try:
                return MapRSE(tuple(a.map_group_and_number)).name, tuple(a.local_coordinates)
            except Exception:  # noqa: BLE001
                return f"UNKNOWN{tuple(a.map_group_and_number)}", tuple(a.local_coordinates)

        def budgeted(gen, budget, label):
            n = 0
            while True:
                try:
                    v = next(gen)
                except StopIteration:
                    return
                n += 1
                if n > budget:
                    gen.close()
                    raise RuntimeError(f"frame budget {budget} exhausted during {label}")
                yield v

        def static_metatiles(map_enum):
            """The map's own STATIC metatile ids, straight from the ROM header."""
            import modules.map as _map_module
            from modules.memory import unpack_uint32

            header = _map_module._map_header_cache[context.rom.id][map_enum.value]
            layout = context.emulator.read_bytes(unpack_uint32(header[:4]), 24)
            w = unpack_uint32(layout[0:4])
            h = unpack_uint32(layout[4:8])
            raw = context.emulator.read_bytes(unpack_uint32(layout[12:16]), w * h * 2)
            out = {}
            for y in range(h):
                for x in range(w):
                    i = (y * w + x) * 2
                    out[(x, y)] = (raw[i] | (raw[i + 1] << 8)) & 0x03FF
            return out

        def static_collision(map_enum):
            import modules.map as _map_module
            from modules.memory import unpack_uint32

            header = _map_module._map_header_cache[context.rom.id][map_enum.value]
            layout = context.emulator.read_bytes(unpack_uint32(header[:4]), 24)
            w = unpack_uint32(layout[0:4])
            h = unpack_uint32(layout[4:8])
            raw = context.emulator.read_bytes(unpack_uint32(layout[12:16]), w * h * 2)
            out = {}
            for y in range(h):
                for x in range(w):
                    i = (y * w + x) * 2
                    out[(x, y)] = ((raw[i] | (raw[i + 1] << 8)) & 0x0C00) >> 10
            return out

        # ============================= P0 — PREMISE + INVENTORY ==============================
        yield from budgeted(wait_until_truly_controllable(), 3000, "P0 settle")
        here_map, at = where()
        badge8 = get_event_flag("BADGE08_GET")
        party = [(m.personality_value, m.species.name, m.current_hp, m.total_hp)
                 for m in get_party() if m is not None]
        hp_now = sum(p[2] for p in party)
        hp_max = sum(p[3] for p in party)
        fainted = [p[0] for p in party if p[2] == 0]
        log(f"[{TAG}] P0 at={here_map}{at} BADGE08={badge8} party_hp={hp_now}/{hp_max} "
            f"fainted_pids={fainted} party={party}")
        try:
            money = get_player().money
        except Exception as error:  # noqa: BLE001
            money = f"UNREADABLE({type(error).__name__})"
        log(f"[{TAG}] P0 MONEY={money} (UNPREDICTED — one of the numbers this probe exists to get)")
        try:
            from modules.items import get_item_bag, get_item_by_name

            bag = get_item_bag()
            counts = {n: bag.quantity_of(get_item_by_name(n))
                      for n in ("Potion", "Super Potion", "Hyper Potion", "Revive", "Full Heal",
                                "Full Restore", "X Attack", "Escape Rope")}
            log(f"[{TAG}] P0 BAG {counts} (⛔ Escape Rope is DEAD WEIGHT here: both gym floors are "
                f"`allow_escaping: false`)")
        except Exception as error:  # noqa: BLE001
            log(f"[{TAG}] P0 BAG read failed: {type(error).__name__}: {error}")
        self.probes_run.append("P0")

        if here_map != "SOOTOPOLIS_CITY" or badge8:
            log(f"[{TAG}] !! VACUOUS — need SOOTOPOLIS_CITY with BADGE08 clear; got {here_map}, "
                f"badge8={badge8}.")
            self.stop_reason = "vacuous premise"
            return

        # ==================================== P1 — HEAL ======================================
        before_pids = {p[0]: (p[2], p[3]) for p in party}
        yield from budgeted(heal_in_pokemon_center(PokemonCenter.SootopolisCity), 20000, "P1 heal")
        yield from budgeted(wait_until_truly_controllable(), 3000, "P1 settle")
        after = {m.personality_value: (m.current_hp, m.total_hp)
                 for m in get_party() if m is not None}
        # ⛔ PID-KEYED, never a count — a count that nets to zero reads TRUE when nothing happened.
        not_full = [pid for pid in before_pids if pid in after and after[pid][0] != after[pid][1]]
        missing = [pid for pid in before_pids if pid not in after]
        here_map, post_heal = where()
        log(f"[{TAG}] P1 HEAL at={here_map}{post_heal} not_full={not_full} missing={missing} "
            f"party_hp={sum(v[0] for v in after.values())}/{sum(v[1] for v in after.values())}")
        self.probes_run.append("P1")

        # ================================ P2 — ENTER THE GYM =================================
        try:
            apron = calculate_path((MapRSE.SOOTOPOLIS_CITY, post_heal),
                                   (MapRSE.SOOTOPOLIS_CITY, (31, 32)))
            log(f"[{TAG}] P2 path to the gym apron (31,32): OK {len(apron)} wp")
        except Exception as error:  # noqa: BLE001 - a refusal IS the reading
            log(f"[{TAG}] P2 path to the gym apron: {type(error).__name__}: {str(error)[:200]}")
        yield from budgeted(
            _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, (31, 32), tries=6), 12000, "P2 to apron")
        yield from budgeted(
            _navigate_riding_out(GYM, (8, 25), tries=4), 8000, "P2 into the gym")
        yield from budgeted(wait_until_truly_controllable(), 3000, "P2 settle")
        here_map, gym_at = where()
        ice_count_on_entry = get_event_var("ICE_STEP_COUNT")
        log(f"[{TAG}] P2 INSIDE at={here_map}{gym_at} ICE_STEP_COUNT={ice_count_on_entry} "
            f"(PREDICTED GYM_1F, arrival tile REPORTED not asserted, count 1)")
        self.probes_run.append("P2")
        if here_map != "SOOTOPOLIS_CITY_GYM_1F":
            log(f"[{TAG}] !! P2 did not enter the gym — everything below is about that map.")
            self.stop_reason = f"P2 landed on {here_map}"
            return

        # ================= P3 — THE HEADLINE: IS THE COLLISION READER BLIND? =================
        live_mt = _live_metatile_grid(GYM)
        stat_mt = static_metatiles(GYM)
        live_col = _live_collision_grid(GYM)
        stat_col = static_collision(GYM)

        thin = sorted(t for t, v in live_mt.items() if v in THIN_ICE)
        stairs = sorted(t for t, v in live_mt.items() if v == LOCKED_STAIRS)
        # sections = contiguous bands of y, split by the locked-stair rows
        bands: dict[int, int] = {}
        for (x, y) in thin:
            bands[y] = bands.get(y, 0) + 1
        log(f"[{TAG}] P3 THIN ICE n={len(thin)} (PREDICTED 64) rows={sorted(bands)} "
            f"per_row={[bands[y] for y in sorted(bands)]}")
        log(f"[{TAG}] P3 LOCKED STAIRS (0x20F) n={len(stairs)} at={stairs}")
        # ⛔ THE FULL COORDINATE LIST, not just a count. `solve_gym_ice.py` generates the route from
        # the DECOMP layout; this is the LIVE tile set the game actually runs, and the two must be
        # compared TILE BY TILE before the bot walks a generated route. A matching COUNT is not a
        # matching SET — that is the "positive control proves a scan is not blind, it says nothing
        # about over-reporting" lesson (08-MISTAKES 2026-08-27).
        log(f"[{TAG}] P3 THIN-ICE COORDS (live, for diffing against solve_gym_ice.py) {thin}")

        mt_diff_before = sorted(t for t in stat_mt if live_mt.get(t) != stat_mt[t])
        col_diff_before = sorted(t for t in stat_col if live_col.get(t) != stat_col[t])
        log(f"[{TAG}] P3 AT ENTRY metatile_diff={len(mt_diff_before)} "
            f"collision_diff={len(col_diff_before)} (PREDICTED 0 and 0 — nothing stepped on yet)")

        # --- derive the step target from the LIVE grid; ⛔ hardcode no coordinates ---
        px, py = gym_at
        candidates = [t for t in thin if t[0] == px and t[1] < py]
        target = max(candidates, key=lambda t: t[1]) if candidates else None
        log(f"[{TAG}] P3 STEP TARGET {target} (derived: the southernmost thin-ice tile in the "
            f"player's own column, never hardcoded)")
        stepped = False
        if _os.environ.get("POKEBOT_CH22_FAULT_NOSTEP", "").strip() == "1":
            # ⛔ FAULT ARM (house rule 6): suppress the ice step although everything else is fine.
            # The tightened grade MUST go FAIL. Before the Tier 1 fix this arm would have PASSED.
            log(f"[{TAG}] FAULT NOSTEP: skipping the ice step — P3 must NOT be recorded and the "
                f"run must FAIL, proving the grade requires the measurement and not just the block.")
            target = None
        if target is None:
            log(f"[{TAG}] !! P3 no thin ice in the player's column — the A/B cannot be run from "
                f"here. That is a RESULT about the layout, not a driver fault.")
        else:
            # walk to the tile just south of it, then take ONE bounded step north onto the ice
            approach = (target[0], target[1] + 1)
            try:
                if tuple(gym_at) != approach:
                    yield from budgeted(_navigate_riding_out(GYM, approach, tries=4), 6000,
                                        "P3 approach")
                yield from budgeted(
                    _bounded_step("Up", expect=target, map_enum=GYM), 1200, "P3 the ONE ice step")
                stepped = True
            except Exception as error:  # noqa: BLE001 - a failed step is a RESULT
                log(f"[{TAG}] !! P3 the ice step failed: {type(error).__name__}: {str(error)[:250]}")

        live_mt2 = _live_metatile_grid(GYM)
        live_col2 = _live_collision_grid(GYM)
        mt_diff_after = sorted(t for t in stat_mt if live_mt2.get(t) != stat_mt[t])
        col_diff_after = sorted(t for t in stat_col if live_col2.get(t) != stat_col[t])
        ice_count_after = get_event_var("ICE_STEP_COUNT")
        log(f"[{TAG}] P3 AFTER ONE STEP stepped={stepped} at={where()[1]} "
            f"ICE_STEP_COUNT {ice_count_on_entry} -> {ice_count_after} (PREDICTED 1 -> 2)")
        log(f"[{TAG}] P3 metatile_diff={len(mt_diff_after)} at={mt_diff_after[:6]} "
            f"values={[(t, hex(stat_mt[t]), hex(live_mt2[t])) for t in mt_diff_after[:4]]}")
        log(f"[{TAG}] P3 ⛔ collision_diff={len(col_diff_after)} at={col_diff_after[:6]}")
        verdict = ("BLIND — CONFIRMED" if len(mt_diff_after) > 0 and len(col_diff_after) == 0
                   else "NOT blind / inconclusive — see the falsifier in the predictions note")
        log(f"[{TAG}] P3 VERDICT: the collision reader is {verdict}. "
            f"(metatile moved={len(mt_diff_after) > 0}, collision moved={len(col_diff_after) > 0}) "
            f"⇒ if BLIND, `probe_live_mapgrid.py` would PASS on a broken model, MEASURED not argued.")
        # ⛔ P3 IS RECORDED ONLY IF THE MEASUREMENT ACTUALLY HAPPENED. A Tier 1 reviewer found this
        # appended unconditionally — so a run where no ice tile was found, or where the step raised,
        # still marked P3 "done" and could reach ACCEPTANCE: PASS having measured NOTHING. That is
        # this project's "A CANDIDATE IS NOT AN ATTEMPT" shape, and it is the rule I had written
        # into the `unlazy` skill hours earlier. The headline conjuncts are stored for the verdict.
        self.stepped = stepped
        self.mt_moved = len(mt_diff_after) > 0
        self.col_moved = len(col_diff_after) > 0
        if stepped and self.mt_moved:
            self.probes_run.append("P3")
        else:
            log(f"[{TAG}] !! P3 NOT RECORDED — stepped={stepped} metatile_moved={self.mt_moved}. "
                f"The A/B did not happen, so P3 measured nothing and the grade must not count it.")

        # ========================= P4 — IS THE PLANNER BLIND TOO? ===========================
        here_now = where()[1]
        try:
            juan_path = calculate_path((GYM, here_now), (GYM, (8, 3)))
            walls = [t for t in (tuple(w.coordinates) for w in juan_path)
                     if live_col2.get(t, 0) != 0]
            log(f"[{TAG}] P4 calculate_path({here_now} -> Juan (8,3)): **SUCCEEDS**, "
                f"{len(juan_path)} wp, live_walls_on_it={len(walls)} "
                f"⇒ the planner proposes a route through LOCKED STAIRS and un-walked ice, and the "
                f"collision oracle calls it clean. The route MUST be a table, not a plan.")
        except Exception as error:  # noqa: BLE001 - a refusal is also a reading
            log(f"[{TAG}] P4 calculate_path(-> Juan (8,3)): {type(error).__name__}: "
                f"{str(error)[:220]} (PREDICTED it would SUCCEED — a refusal is a RESULT)")
        self.probes_run.append("P4")

        # ==================== P5 — LEAVE, AND CONFIRM THE PUZZLE RESETS ======================
        try:
            yield from budgeted(_navigate_riding_out(GYM, (8, 25), tries=4), 8000, "P5 to the exit")
            yield from budgeted(
                _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, (31, 33), tries=4), 8000, "P5 out")
        except Exception as error:  # noqa: BLE001
            log(f"[{TAG}] !! P5 exit walk failed: {type(error).__name__}: {str(error)[:250]}")
        yield from budgeted(wait_until_truly_controllable(), 3000, "P5 settle")
        out_map, out_at = where()
        log(f"[{TAG}] P5 OUT at={out_map}{out_at}")
        if out_map == "SOOTOPOLIS_CITY":
            try:
                yield from budgeted(_navigate_riding_out(GYM, (8, 25), tries=4), 8000, "P5 re-enter")
                yield from budgeted(wait_until_truly_controllable(), 3000, "P5 re-settle")
                if where()[0] == "SOOTOPOLIS_CITY_GYM_1F":
                    live_mt3 = _live_metatile_grid(GYM)
                    reset_diff = sorted(t for t in stat_mt if live_mt3.get(t) != stat_mt[t])
                    log(f"[{TAG}] P5 RE-ENTERED ICE_STEP_COUNT={get_event_var('ICE_STEP_COUNT')} "
                        f"metatile_diff={len(reset_diff)} (PREDICTED 1 and 0 — every entry gets "
                        f"VIRGIN ICE, which is what makes a precomputed route table safe)")
                    yield from budgeted(_navigate_riding_out(GYM, (8, 25), tries=4), 8000,
                                        "P5 leave again")
                    yield from budgeted(
                        _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, (31, 33), tries=4), 8000,
                        "P5 out again")
            except Exception as error:  # noqa: BLE001
                log(f"[{TAG}] !! P5 re-entry check failed: {type(error).__name__}: "
                    f"{str(error)[:250]}")
        self.probes_run.append("P5")

        final_map, final_at = where()
        try:
            cont = calculate_path((MapRSE.SOOTOPOLIS_CITY, final_at),
                                  (MapRSE.SOOTOPOLIS_CITY, (31, 32)))
            log(f"[{TAG}] CONTINUE from {final_map}{final_at} -> gym apron (31,32): OK {len(cont)} wp")
        except Exception as error:  # noqa: BLE001
            log(f"[{TAG}] CONTINUE from {final_map}{final_at} -> gym apron: "
                f"{type(error).__name__}: {str(error)[:200]}")


class Ch22IceMode(BotMode):
    """§Ch22 — WALK THE ICE PUZZLE. Drives the PRODUCTION `sootopolis_gym.walk_the_ice()`.

    ‼ WHAT THIS PROVES THAT NOTHING BEFORE IT DID. The route table's INPUT was verified on
    2026-09-02 (decomp vs the live `gBackupMapLayout` = 64/64 tiles, zero differences both ways),
    but **the route has never been WALKED**. Two sources agreeing is corroboration; a walk is proof.

    ⛔ PREDICTIONS, FILED BEFORE THE FIRST RUN:
      steps=64; sections end at (8,17)/(8,12)/(8,6) with ICE_STEP_COUNT 8/28/67; end_tile=(8,6),
      end_count=67; then three bounded steps up the now-open stairs to JUAN_STAND (8,3);
      whiteouts=0; encounters=0 (a gym has no wild encounters). Frame cost UNPREDICTED — the walk is
      64 tiles plus three ~40-frame unlock delays, and nobody has measured it.
    ⛔ A reading that contradicts a prediction is a RESULT. The one thing that would be a DEFECT is
    a fall — and the leg refuses to step onto anything that is not thin ice, so a fall would mean
    the pre-step check is wrong, not that the route is unlucky.

    THE GRADE: the leg completed AND `ICE_STEP_COUNT == 67` AND the bot stands on JUAN_STAND (8,3)
    AND whiteouts == 0. ⛔ Position ALONE is not the grade — `ICE_STEP_COUNT` is what the game's own
    unlock thresholds are counted against, so the var is the action and the tile is the plan.
    ⛔ AND THE BOT DOES NOT TALK TO JUAN. This leg ends one tile in front of him; the fight is its
    own leg, and the party is measured NOT to win it yet.

    ⚠ A FALL IS RECOVERABLE AND COSTS ONLY THE WALK — the puzzle resets on every entry (MEASURED).
    So a failed run is cheap, and re-running is safe.

    FAULT ARM:
      POKEBOT_CH22_FAULT_BADROUTE=1  corrupt one tile of the embedded route before walking. The
                                     pre-step check MUST refuse, NAMED and bounded, BEFORE stepping
                                     — proving the check is what protects the walk, not luck.

    Run: PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1 --driver ch22ice --frames 60000
    """

    @staticmethod
    def name() -> str:
        return "Ch22Ice"

    def __init__(self):
        super().__init__()
        self.encounters = 0
        self.whiteouts = 0

    def on_whiteout(self) -> bool:
        self.whiteouts += 1
        log("[ch22ice] !! WHITEOUT - latching the story abort so a verdict still prints.")
        try:
            from modules.story.early_game import set_story_abort

            set_story_abort(True)
        except Exception as error:  # noqa: BLE001
            log(f"[ch22ice] !! could not latch the abort: {type(error).__name__}: {error}")
            return False
        return True

    def on_battle_started(self, encounter):
        self.encounters += 1
        return super().on_battle_started(encounter)

    def run(self):
        from modules.map_data import MapRSE
        from modules.memory import get_event_var
        from modules.player import get_player_avatar
        from modules.story import sootopolis_gym as gym
        from modules.story.early_game import _navigate_riding_out, wait_until_truly_controllable
        from modules.story.sootopolis import _bounded_step

        TAG = "ch22ice"
        frames_before = context.emulator.get_frame_count()

        def where():
            a = get_player_avatar()
            try:
                return MapRSE(tuple(a.map_group_and_number)).name, tuple(a.local_coordinates)
            except Exception:  # noqa: BLE001
                return f"UNKNOWN{tuple(a.map_group_and_number)}", tuple(a.local_coordinates)

        start_name, start_at = where()
        log(f"[{TAG}] PRE at={start_name}{start_at} ICE_STEP_COUNT="
            f"{get_event_var('ICE_STEP_COUNT')} route_tiles={len(gym.ice_route_tiles())}")

        report: dict = {}
        failure = None
        try:
            # get into the gym if we are not already there (the city walk is planner-safe)
            if start_name == "SOOTOPOLIS_CITY":
                yield from _navigate_riding_out(MapRSE.SOOTOPOLIS_CITY, (31, 32), tries=6)
                yield from _navigate_riding_out(gym.GYM_1F, gym.GYM_ENTRANCE, tries=4)
                yield from wait_until_truly_controllable()

            if _os.environ.get("POKEBOT_CH22_FAULT_BADROUTE", "").strip() == "1":
                # ⛔ FAULT ARM: corrupt ONE tile of the embedded route. The pre-walk set check must
                # refuse BEFORE any stepping. Process-local; the module is re-imported per run.
                bad = list(gym.ICE_ROUTE)
                first = list(bad[0])
                first[3] = (first[3][0] + 5, first[3][1])
                bad[0] = tuple(first)
                gym.ICE_ROUTE = tuple(bad)
                log(f"[{TAG}] FAULT BADROUTE: moved one route tile off the ice — the pre-walk "
                    f"check MUST refuse, named and bounded, before a single step.")

            yield from gym.walk_the_ice(report)

            # the stairs above section 3 are OPEN now; three bounded steps to Juan's front tile.
            # ⛔ NOT `navigate_to` — the planner is provably wrong inside this gym.
            for _ in range(3):
                here = tuple(get_player_avatar().local_coordinates)
                yield from _bounded_step("Up", expect=(here[0], here[1] - 1), map_enum=gym.GYM_1F)
            yield from wait_until_truly_controllable()
        except Exception as error:  # noqa: BLE001 - the driver REPORTS failures, never hides them
            failure = f"{type(error).__name__}: {str(error)[:600]}"
            log(f"[{TAG}] LEG FAILED: {failure}")

        here_name, at = where()
        count = get_event_var("ICE_STEP_COUNT")
        passed = (
            failure is None
            and count == gym.ICE_COMPLETE_COUNT
            and here_name == "SOOTOPOLIS_CITY_GYM_1F"
            and at == gym.JUAN_STAND
            and self.whiteouts == 0
        )
        total = context.emulator.get_frame_count() - frames_before
        log(f"[{TAG}] RESULT at={here_name}{at} ICE_STEP_COUNT={count} steps={report.get('steps')} "
            f"end_tile={report.get('end_tile')} end_count={report.get('end_count')} "
            f"encounters={self.encounters} whiteouts={self.whiteouts} frames={total}")
        log(f"[{TAG}] SECTIONS {report.get('sections')} "
            f"(each: index, tiles, end tile, ICE_STEP_COUNT — MEASURED (8,17)/9, (8,12)/29, (8,6)/68; "
            f"the PREDICTION was 8/28/67, the raw decomp thresholds — each unlock's own addvar "
            f"lands in the same beat as the crossing step, so the rest value is threshold+1)")
        log(f"[{TAG}] FAILURE {failure}")
        log(f"[{TAG}] GRADE: the var is the ACTION and the tile is the PLAN — both are required. "
            f"⛔ The bot does NOT talk to Juan here; the fight is its own leg.")
        log(f"[{TAG}] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")
        context.set_manual_mode()


class Ch20ChapterMode(Ch20DiveMode):
    """§Ch20 AS A CHAPTER — drives the PRODUCTION function, not a copy of it.

    ‼ THE POINT OF THIS DRIVER IS THE ASSEMBLY, NOT THE ROOMS. Every room was already proven by
    `ch20dive/room1/room2/room6/room3/room8/room9`. What has NEVER been driven is
    `modules.story.seafloor_cavern.do_seafloor_cavern_chapter()` — the orchestration glue: the
    retry loop, the resume branch, the jam-recovery wiring and the preflight. An adversarial review
    found FOUR blockers in exactly that glue, so it is the part that needs a drive.

    ⛔ IT CALLS THE PRODUCTION ENTRY POINT. Copying the chapter's steps into this driver would
    prove the copy works and tell us nothing about what `_play()` will run (`boxwithdraw`'s rule).

    ⚠ DIVE IS STILL INJECTED HERE, DELIBERATELY AND NARROWLY. Organic acquisition is a SEPARATE
    proven thing (`--driver divelearner`) and is now wired as Segment 19b; injecting it keeps this
    drive pointed at the cavern instead of re-testing the hunt. ⛔ That makes this an ASSEMBLY test,
    not an end-to-end story test — do not quote its PASS as proof the bot can reach the cavern by
    playing.

    FAULT HOOKS, to prove the two recovery paths a review found missing rather than assuming them:
      POKEBOT_CH20_FAULT=chapter_push   force the FIRST Room 8 `strength_push` to raise, which must
                                        drive `_recover_room8_jam()` and still finish.
      POKEBOT_CH20_FAULT=chapter_escape force a failure INSIDE the atoll escape, with the var
                                        already at 2 — attempt 2 must take the ESCAPE-ONLY
                                        resume rather than re-dive.
      POKEBOT_CH20_FAULT=chapter_resume force a `BotModeError` right after the Room 9 trigger fires,
                                        which must make attempt 2 take the Route 128 recovery
                                        INSTEAD of re-diving (the trigger is disarmed by then).

    Run:  PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20chapter --frames 6000000
    Emits: [ch20chapter] RESULT done=<b> var2=<b> surfing=<b> at=<tile> ocean_path=<b>
    """

    @staticmethod
    def name():
        return "Ch20Chapter"

    def run(self):
        # ‼ EVERYTHING IS IMPORTED LOCALLY, which is this file's convention for `modules.*` — the
        # harness is imported before a ROM is loaded, so module-scope game imports break it.
        from modules.map_data import MapRSE
        from modules.modes import BotModeError
        from modules.player import AvatarFlags, get_player_avatar
        from modules.story import seafloor_cavern as chapter
        from modules.story.early_game import wait_until_truly_controllable

        # ‼ `_os`, not `os` — this module imports `os as _os` (:15). A bare `os` here cost a
        # 25-minute background drive that died on frame 1 with a NameError.
        # ⇒ SMOKE-TEST A NEW DRIVER WITH A TINY `--frames` BEFORE COMMITTING TO A LONG RUN. And note
        # `repro_undefined_names.py` scans `modules/story/`, NOT `tools/story-dev/`, so this class
        # of bug is NOT gated here.
        fault = _os.environ.get("POKEBOT_CH20_FAULT", "")
        yield from wait_until_truly_controllable()
        yield from self._inject_dive_fixture()
        if not self.fixture_ok:
            log("[ch20chapter] RESULT done=False var2=False surfing=False at=? ocean_path=False")
            log("[ch20chapter] ACCEPTANCE: FAIL — the Dive fixture failed; the cavern is unreachable")
            context.set_manual_mode()
            return

        # ‼ INSTRUMENT THE ACTION, NOT THE OUTCOME. The first fault run PASSED, which implies the
        # jam recovery ran — but only by control-flow inference, because the chapter reports a jam
        # through `context.message` and the run's own grep filter dropped it. "A candidate is not an
        # attempt": wrap the real recovery so the RESULT line can state whether it actually fired.
        recovery = {"count": 0}
        resume = {"count": 0}
        _real_finish = chapter._finish_on_route128

        def _counted_finish(*a, **kw):
            resume["count"] += 1
            log(f"[ch20chapter] ROUTE128 RESUME RECOVERY FIRED (#{resume['count']})")
            return _real_finish(*a, **kw)

        chapter._finish_on_route128 = _counted_finish
        escapes = {"count": 0}
        _real_escape_leg = chapter._escape_the_atoll

        def _counted_escape(*a, **kw):
            escapes["count"] += 1
            log(f"[ch20chapter] ATOLL ESCAPE LEG RAN (#{escapes['count']})")
            return _real_escape_leg(*a, **kw)

        chapter._escape_the_atoll = _counted_escape
        _real_recover = chapter._recover_room8_jam

        def _counted_recover(*a, **kw):
            recovery["count"] += 1
            log(f"[ch20chapter] ROOM8 JAM RECOVERY FIRED (#{recovery['count']})")
            return _real_recover(*a, **kw)

        chapter._recover_room8_jam = _counted_recover

        if fault == "chapter_escape":
            # ⛔ THE THIRD WINDOW, and it is the one an adversarial review named as MISSING EVIDENCE.
            # Fail INSIDE the atoll escape, i.e. AFTER `ROUTE128_STATE` has already reached 2. At
            # that instant NEITHER other resume predicate helps: `seafloor_cavern_done()` is False
            # (still on the landing tile) and `route128_scene_outstanding()` is False (the var is 2,
            # not 1). Without `escape_outstanding()` the retry loop would RE-DIVE ~25 minutes into a
            # permanently-disarmed trigger, up to three times, and then hard-fail.
            _real_escape = chapter._escape_the_atoll
            esc_state = {"fired": False}

            def _faulty_escape(*a, **kw):
                if not esc_state["fired"]:
                    esc_state["fired"] = True
                    log("[ch20chapter] ‼ FAULT: raising inside the atoll escape, with the var already "
                        "at 2 — attempt 2 must take the ESCAPE-ONLY resume, not re-dive.")
                    raise BotModeError("fault-injected failure during the atoll escape")
                return _real_escape(*a, **kw)

            chapter._escape_the_atoll = _faulty_escape

        if fault == "chapter_resume":
            # ⛔ THIS HOOK WAS DOCUMENTED BEFORE IT EXISTED. For one commit the docstring advertised
            # `chapter_resume` and nothing implemented it — so running it would have produced an
            # ordinary CLEAN run that silently READ AS PROOF of the resume path. A test hook that
            # does not exist is worse than none: it manufactures a false PASS.
            # Fail the SECOND milestone, i.e. AFTER the Room 9 trigger has fired and the forced warp
            # has landed us on Route 128. At that instant SEAFLOOR_CAVERN_STATE is 1 (the trigger is
            # disarmed FOREVER) and ROUTE128_STATE is 1 — precisely the state where re-diving can
            # never work and `_finish_on_route128()` is the only route through.
            _real_ride = chapter._ride_until
            ride_state = {"fired": False}

            def _faulty_ride(label, predicate, budget_frames):
                if not ride_state["fired"] and "ROUTE128 scene" in label:
                    ride_state["fired"] = True
                    log("[ch20chapter] ‼ FAULT: raising AFTER the Room 9 trigger fired — attempt 2 "
                        "must take the Route 128 recovery, NOT re-dive into a disarmed trigger.")
                    raise BotModeError("fault-injected failure after the Kyogre trigger")
                return _real_ride(label, predicate, budget_frames)

            chapter._ride_until = _faulty_ride

        if fault == "chapter_push":
            # Wrap the REAL `strength_push` the chapter imports, and fail its first Room 8 call.
            import modules.story.early_game as _eg

            original = _eg.strength_push
            state = {"fired": False}

            def _faulty(map_enum, approach, face, **kwargs):
                if not state["fired"] and approach == chapter.ROOM8_PUSHES[0][0]:
                    state["fired"] = True
                    log("[ch20chapter] ‼ FAULT: failing the first Room 8 push on purpose — the "
                        "jam-recovery path is the thing under test.")
                    raise BotModeError("fault-injected Room 8 push failure")
                return original(map_enum, approach, face, **kwargs)

            _eg.strength_push = _faulty

        try:
            yield from chapter.do_seafloor_cavern_chapter()
        except Exception as error:  # noqa: BLE001 - the driver REPORTS; it never hides
            log(f"[ch20chapter] CHAPTER RAISED {type(error).__name__}: {str(error)[:400]}")

        done = chapter.seafloor_cavern_done()
        var2 = chapter._var("ROUTE128_STATE")
        try:
            avatar = get_player_avatar()
            surfing = AvatarFlags.Surfing in avatar.flags
            at = tuple(avatar.local_coordinates)
        except Exception:  # noqa: BLE001
            surfing, at = False, None
        # ‼ INLINED, not `self._path_ok(...)`: that helper lives on `Ch20Room1Mode`, not on the
        # `Ch20DiveMode` base this class extends — calling it cost a full 25-minute drive whose
        # CHAPTER SUCCEEDED but whose ACCEPTANCE line never printed. The reporting must never be
        # able to fail after the thing under test has passed.
        if at is None:
            ocean_path, ocean_detail = False, "no position"
        else:
            try:
                from modules.map_path import calculate_path as _cp

                _cp((MapRSE.ROUTE128, at), (MapRSE.ROUTE128, chapter.OCEAN_PROBE))
                ocean_path, ocean_detail = True, f"OK {at} -> {chapter.OCEAN_PROBE}"
            except Exception as _perr:  # noqa: BLE001 - a failed probe is a RESULT, not a crash
                ocean_path, ocean_detail = False, f"{type(_perr).__name__}: {str(_perr)[:160]}"

        log(f"[ch20chapter] RESULT done={done} var2={var2} surfing={surfing} at={at} "
            f"ocean_path={ocean_path} room8_recoveries={recovery['count']} "
            f"route128_resumes={resume['count']} escape_legs={escapes['count']}")
        log(f"[ch20chapter] OCEAN-PATH {ocean_detail}")
        # ‼ ACCEPTANCE INCLUDES "AND THE BOT CAN CONTINUE". Three chapters in this project shipped
        # stranded while passing their own tests; the ocean path off the launch tile is that check.
        passed = bool(done) and var2 == 2 and surfing and at == chapter.ESCAPE_WATER and ocean_path
        log(f"[ch20chapter] ACCEPTANCE: {'PASS' if passed else 'FAIL'}")

        # ‼ `#24-ch21anchor` — OPTIONALLY SNAPSHOT A POST-Ch20 ANCHOR. There is no save anchor after
        # the Seafloor Cavern (77 saves; the frontier stops at `post_dive.ss1`), so every §Ch21
        # experiment otherwise replays a ~25-minute Ch20 drive before it starts.
        #
        # ⛔ IT WRITES ONLY ON `passed`, AND THAT IS THE WHOLE DESIGN. `passed` already means
        # "arrived, controllable, surfing on the launch tile, AND a real `calculate_path` proves the
        # open ocean" — i.e. exactly the bar `AnchorCaptureMode` states for a usable anchor ("an
        # anchor captured mid-scene makes every later navigation leg fail for one harness reason
        # instead of a map reason"). A FAIL run must never leave a file that a later session mistakes
        # for a good fixture.
        # ⛔ AND THE DISCRIMINATOR IS THE VAR, NOT THE MAP. ROUTE128 is stood on BOTH before the dive
        # and after the escape, so a map-only capture target cannot tell the two apart; `var2 == 2`
        # (i.e. `ROUTE128_STATE == 2`) is what makes this anchor POST-cavern.
        # ‼ Verify the written file with `probe_anchor_inventory.py`, never with this log — the
        # driver reports what it believes, the probe reports what the file contains (playbook §2b).
        _cap = _os.environ.get("CH20_CAPTURE", "").strip()
        if _cap:
            # ‼ LOCAL import: this module imports `os as _os` but NOT `pathlib` at module level.
            # `repro_undefined_names.py` caught exactly that here on 2026-08-24 — the SAME bug class
            # (a name used on a branch no green run reaches) that burned a 25-minute drive earlier
            # the same day. The fix that mattered was not the import, it was RUNNING THE GATE FIRST.
            import pathlib as _pathlib

            _out = _pathlib.Path(__file__).resolve().parent / "saves" / _cap
            if not passed:
                log(f"[ch20chapter] CAPTURE SKIPPED — acceptance did not pass; refusing to write {_cap}")
            elif _out.exists() and _os.environ.get("CAPTURE_FORCE", "") != "1":
                log(f"[ch20chapter] CAPTURE REFUSED — {_cap} already exists (set CAPTURE_FORCE=1 to replace)")
            else:
                _out.parent.mkdir(parents=True, exist_ok=True)
                _out.write_bytes(context.emulator.get_save_state())
                log(f"[ch20chapter] CAPTURE WROTE {_out.name} ({_out.stat().st_size} bytes) "
                    f"at {at} var2={var2} — ‼ verify with probe_anchor_inventory.py, not this line")

        context.set_manual_mode()


class DiveLearnerMode(BotMode):
    """KI-63 — acquire a REAL Dive learner: free a slot, hunt, catch, teach, verify.

    ‼ THIS IS THE LAST THING BETWEEN THE BOT AND §Ch20. `--driver ch20dive` proved the whole
    Mossdeep → Seafloor Cavern dive route, but it INJECTED Dive with a debug write. Nothing here
    injects anything: every move must be learned by playing.

    ‼ THE ORDER IS ADVERSARIALLY CORRECTED, and the obvious order is wrong twice over. Spec:
    `ai-research-notes/2026-08-13-ki63-dive-learner-acquisition-plan.md`.
      1. **`ensure_hm_learner` FIRST, not a deposit first.** It checks `hm_learner_slot` at
         `early_game.py:4338-4340` — *before* the party-full check at `:4342-4348` — so an
         unconditional deposit would cost a PC trip and a team member even when no catch was
         ever needed.
      2. Only on the specific "party is full" failure, free ONE slot via the new
         `pc_trip.deposit_one_dead_weight()`, piggybacked on a heal.
         ‼ **NOT `withdraw_from_box`** — it opens `find_in_box(pids) → if None: return`, so with
         nothing yet boxed it does NOTHING. ‼ **NOT `deposit_dead_weight_if_worth_it`** — it is a
         SILENT NO-OP behind `POKEBOT_PC_ROTATION`, which is pinned 0 and measured harmful.
         Our own handoff named the first of those as the path to use; it cannot do the job.
      3. Retry `ensure_hm_learner` — this does the bounded hunt (40,000-frame deadline) + catch.
      4. Before teaching, check the returned slot does not ALREADY know Dive (`items.py:196-197`
         raises a confusing "already knows it" on that happy path).
      5. ‼ **ASSERT BY RE-READING THE PARTY, NEVER BY A CLEAN RETURN.** The teach primitives are
         generators with no return value and no post-teach verification. The only trustworthy
         gate is the mon's actual moveset plus `can_dive()`.

    MEASURED before building (`probe_dive_learner_plan.py`, 4 controls, all PASS):
    19 Poké Balls / $54,334 (so `#24-ballstarve` does not bite here); the only Dive ground is
    `ROUTE117 (31,16) ['Marill']` — **10% of the land table at L13, 1,055 waypoints away**;
    `find_dead_weight` picks **Skitty L17** and EXEMPTS Zigzagoon, our sole Surf carrier.

    ‼ ROUND ONE USES THE EXISTING GROUND ON PURPOSE. Shoal Cave's Spheal is better on every axis
    (50%, L26-32, catch rate 255, 103 waypoints + a door), but `_hm_hunting_grounds` iterates
    `TRAINING_GRASS`, and adding a Shoal row there **flips `best_training_area` for every team
    from ~L30 up**. Proving the CHAIN and changing the GROUND TABLE are two variables; this
    driver moves one.

        PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver divelearner --frames 3000000

    Emits: [divelearner] RESULT freed_slot=<bool> caught=<bool> knows_dive=<bool>
           can_dive=<bool> surf_intact=<bool>
    """

    @staticmethod
    def name():
        return "DiveLearner"

    def on_battle_started(self, encounter):
        # ‼ THE PRODUCTION STORY HANDLER, not a stand-in — the CATCH depends on it.
        # `story_mode.py:2150-2168` is what turns an encounter with a Dive learner into
        # `StoryCatchStrategy`, keyed on `early_game.HM_CATCH_TARGET_DEX`, which
        # `ensure_hm_learner` sets. A driver that supplied its own strategy would walk to the
        # grass, meet a Marill and FIGHT it — passing every step except the one under test.
        from plugins.custom_modes.story_mode import StoryMode

        shim = SimpleNamespace(_catch_team_target=4, _should_catch=lambda e: False)
        return StoryMode.on_battle_started(shim, encounter)

    @staticmethod
    def _balls():
        from modules.items import get_item_bag

        return sum(s.quantity for s in get_item_bag().poke_balls)

    @staticmethod
    def _party_moves():
        from modules.pokemon_party import get_party

        out = []
        for i, m in enumerate(get_party()):
            if m is None:
                continue
            out.append(f"{i}:{m.species.name}L{m.level}[" +
                       ",".join(l.move.name for l in m.moves if l is not None) + "]")
        return out

    @staticmethod
    def _knows(move_name):
        """True if ANY party member knows the move. The only trustworthy teach assertion."""
        from modules.pokemon_party import get_party

        for m in get_party():
            if m is None:
                continue
            for l in m.moves:
                if l is not None and l.move.name == move_name:
                    return True
        return False

    def run(self):
        from modules.context import context as _ctx
        from modules.items import get_item_by_name
        from modules.map_data import PokemonCenter
        from modules.pokemon_party import get_party
        from modules.story import early_game
        from modules.story.early_game import (
            ensure_hm_learner_making_room,
            hm_learner_slot,
            teach_hm_move,
            wait_until_truly_controllable,
        )

        yield from wait_until_truly_controllable()
        hm08 = get_item_by_name("HM08")
        notes = {}

        log(f"[divelearner] start party={self._party_moves()}")
        log(f"[divelearner] balls={self._balls()} knows_dive_already={self._knows('Dive')} "
            f"hm_learner_slot(HM08)={hm_learner_slot(hm08)}")

        # ---- THE PRODUCTION PATH, IN ONE CALL --------------------------------------------
        # ‼ THIS NOW DRIVES `ensure_hm_learner_making_room`, NOT A STAND-IN. This driver
        # originally carried its own try / deposit / retry logic — which proved the CAPABILITY but
        # left `_needs_party_slot` with no production setter, so a real `StoryMode` run still
        # derailed. That logic now lives in `modules/story/early_game.py` and is wired into both
        # production call sites; the driver exercises the SAME function the story bot calls, which
        # is the only way this test means anything (the `boxwithdraw` rule: drive the production
        # call site, never a copy of it).
        #
        # Everything the old STEP1/2/3 asserted is still asserted, just from the outside:
        # a slot must be freed, a learner must be caught, and balls are logged either side
        # because the catch gate re-checks `balls > 1` on EVERY encounter and silently stops
        # catching if they run out.
        before_party = len([m for m in get_party() if m is not None])
        # ‼ CAPTURE PIDs, NOT JUST A COUNT. The party ends at 6 either way — one deposited, one
        # caught — so a count comparison would report `freed=True` even if NOTHING happened. This
        # is the "assert by PID, never by slot/count" rule the roster work established the same
        # day, and I had violated it here on the first pass.
        before_pids = {m.personality_value for m in get_party() if m is not None}
        balls_before = self._balls()
        log(f"[divelearner] CALL ensure_hm_learner_making_room(HM08) — party={before_party} "
            f"balls={balls_before}")
        slot = None
        try:
            slot = yield from ensure_hm_learner_making_room(hm08, (PokemonCenter.MossdeepCity,))
            log(f"[divelearner] returned slot={slot}")
        except Exception as error:  # noqa: BLE001
            log(f"[divelearner] raised {type(error).__name__}: {str(error)[:300]}")
        after_party = len([m for m in get_party() if m is not None])
        after_pids = {m.personality_value for m in get_party() if m is not None}
        # A Pokemon that was in the party at the start and is not there now was DEPOSITED.
        deposited = sorted(before_pids - after_pids)
        # A Pokemon that is there now and was not before was CAUGHT.
        gained = sorted(after_pids - before_pids)
        freed = len(deposited) == 1          # exactly one, never more (#24-pc's regression shape)
        caught = slot is not None and len(gained) == 1
        notes["party"] = (before_party, after_party, {"deposited": deposited, "gained": gained})
        notes["freed"] = freed
        notes["caught"] = caught
        log(f"[divelearner] party {before_party} -> {after_party} "
            f"deposited_pids={deposited} gained_pids={gained} freed={freed} caught={caught} "
            f"balls {balls_before} -> {self._balls()} "
            f"HM_CATCH_TARGET_DEX={early_game.HM_CATCH_TARGET_DEX}")
        log(f"[divelearner] party now {self._party_moves()}")

        # ---- STEP 4: teach, but only if it is actually needed ---------------------------
        taught_attempted = False
        if slot is not None:
            party = get_party()
            already = (slot < len(party) and party[slot] is not None
                       and any(l is not None and l.move.name == "Dive" for l in party[slot].moves))
            if already:
                log(f"[divelearner] STEP4 slot {slot} ALREADY knows Dive — skipping the teach "
                    f"(calling it anyway raises a confusing 'already knows it')")
            else:
                taught_attempted = True
                log(f"[divelearner] STEP4 teaching Dive to slot {slot} "
                    f"({party[slot].species.name if slot < len(party) and party[slot] else '?'})")
                try:
                    yield from teach_hm_move(hm08, slot)
                    log("[divelearner] STEP4 teach_hm_move returned "
                        "(‼ a clean return is NOT proof — verified below by reading the moveset)")
                except Exception as error:  # noqa: BLE001
                    log(f"[divelearner] STEP4 raised {type(error).__name__}: {str(error)[:300]}")
        notes["teach_attempted"] = taught_attempted

        # ---- VERIFY: read the party, never a return value -------------------------------
        knows_dive = self._knows("Dive")
        surf_intact = self._knows("Surf")     # the self-inflicted-strand check
        # ‼ `can_dive()` IS NOT IMPORTABLE — it is a nested closure inside `calculate_path`
        # (`map_path.py:690`, `nonlocal _can_dive`), so KI-68's "can_dive() exists, zero callers"
        # describes a private helper, not an API. Caught by the import-symbol check BEFORE this
        # run, not by a failed one. So compute the SAME predicate it computes, verbatim:
        #     context.rom.is_rse and get_event_flag("BADGE07_GET")
        #                        and get_party().has_pokemon_with_move("Dive")
        try:
            from modules.memory import get_event_flag

            dive_ok = bool(
                _ctx.rom.is_rse
                and get_event_flag("BADGE07_GET")
                and get_party().has_pokemon_with_move("Dive")
            )
        except Exception as error:  # noqa: BLE001
            dive_ok = f"<{type(error).__name__}>"
        log(f"[divelearner] VERIFY knows_dive={knows_dive} can_dive={dive_ok} "
            f"surf_intact={surf_intact} party={self._party_moves()}")

        # ---- CAN-CONTINUE: derived from where we ACTUALLY are ---------------------------
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar

        moved, before_xy = False, get_player_avatar().local_coordinates
        try:
            from modules.map import get_map_data
            from modules.map_path import calculate_path
            from modules.modes.util.walking import navigate_to

            avatar = get_player_avatar()
            here_map = MapRSE(tuple(avatar.map_group_and_number))
            # Step one tile along a REAL path to a tile we are NOT standing on.
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                target = (before_xy[0] + dx, before_xy[1] + dy)
                try:
                    path = calculate_path(get_map_data(here_map, before_xy),
                                          get_map_data(here_map, target))
                except Exception:  # noqa: BLE001 - try the next direction
                    continue
                if path and not any(w.is_warp for w in path):
                    yield from navigate_to(here_map, target)
                    moved = get_player_avatar().local_coordinates != before_xy
                    break
        except Exception as error:  # noqa: BLE001
            log(f"[divelearner] CAN-CONTINUE raised {type(error).__name__}: {str(error)[:200]}")
        can_continue = moved and _ctx.bot_mode != "Manual"
        log(f"[divelearner] CAN-CONTINUE moved={moved} {before_xy}->"
            f"{get_player_avatar().local_coordinates} at={self._where_now()} "
            f"manual={_ctx.bot_mode == 'Manual'}")

        log(f"[divelearner] RESULT freed_slot={freed} caught={caught} knows_dive={knows_dive} "
            f"can_dive={dive_ok} surf_intact={surf_intact} can_continue={can_continue} "
            f"detail={notes}")
        log(f"[divelearner] ACCEPTANCE: "
            f"{'PASS' if (knows_dive and dive_ok is True and surf_intact and can_continue) else 'FAIL'}")
        _ctx.set_manual_mode()
        return

    @staticmethod
    def _where_now():
        from modules.map_data import MapRSE
        from modules.player import get_player_avatar

        avatar = get_player_avatar()
        try:
            return MapRSE(tuple(avatar.map_group_and_number)).name, avatar.local_coordinates
        except Exception:  # noqa: BLE001
            return tuple(avatar.map_group_and_number), avatar.local_coordinates


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
        elif args.driver == "boxcatch":
            context.bot_mode_instance = BoxCatchMode()
        elif args.driver == "boxwithdraw":
            context.bot_mode_instance = BoxWithdrawMode()
        elif args.driver == "roster":
            context.bot_mode_instance = RosterMode()
        elif args.driver == "partypids":
            context.bot_mode_instance = PartyPidsMode()
        elif args.driver == "boxcounter":
            context.bot_mode_instance = BoxCounterMode()
        elif args.driver == "boxcounter2":
            context.bot_mode_instance = BoxCounter2Mode()
        elif args.driver == "boxwrite":
            context.bot_mode_instance = BoxWriteMode()
        elif args.driver == "ki80ladder":
            context.bot_mode_instance = Ki80LadderMode()
        elif args.driver == "secondwind":
            context.bot_mode_instance = SecondWindMode()
        elif args.driver == "ch20dive":
            context.bot_mode_instance = Ch20DiveMode()
        elif args.driver == "ch20room1":
            context.bot_mode_instance = Ch20Room1Mode()
        elif args.driver == "ch20room2":
            context.bot_mode_instance = Ch20Room2Mode()
        elif args.driver == "ki76warp":
            context.bot_mode_instance = Ki76WarpMode()
        elif args.driver == "ch20room6":
            context.bot_mode_instance = Ch20Room6Mode()
        elif args.driver == "ch20room3":
            context.bot_mode_instance = Ch20Room3Mode()
        elif args.driver == "ch20room8":
            context.bot_mode_instance = Ch20Room8Mode()
        elif args.driver == "ch20room9":
            context.bot_mode_instance = Ch20Room9Mode()
        elif args.driver == "ch20chapter":
            context.bot_mode_instance = Ch20ChapterMode()
        elif args.driver == "ch21dive":
            context.bot_mode_instance = Ch21DiveMode()
        elif args.driver == "ch21leg2probe":
            context.bot_mode_instance = Ch21Leg2ProbeMode()
        elif args.driver == "ch21escort":
            context.bot_mode_instance = Ch21EscortMode()
        elif args.driver == "ch21cave":
            context.bot_mode_instance = Ch21CaveMode()
        elif args.driver == "ch21pocket":
            context.bot_mode_instance = Ch21PocketExitMode()
        elif args.driver == "ch21approach":
            context.bot_mode_instance = Ch21ApproachMode()
        elif args.driver == "ch21climb":
            context.bot_mode_instance = Ch21ClimbMode()
        elif args.driver == "ch21leg5probe":
            context.bot_mode_instance = Ch21Leg5ProbeMode()
        elif args.driver == "ch21return":
            context.bot_mode_instance = Ch21ReturnMode()
        elif args.driver == "ch21chapter":
            context.bot_mode_instance = Ch21ChapterMode()
        elif args.driver == "ch22probe":
            context.bot_mode_instance = Ch22ProbeMode()
        elif args.driver == "ch22ice":
            context.bot_mode_instance = Ch22IceMode()
        elif args.driver == "divelearner":
            context.bot_mode_instance = DiveLearnerMode()
        elif args.driver == "groundsweep":
            context.bot_mode_instance = GroundSweepMode()
        elif args.driver == "anchorcapture":
            context.bot_mode_instance = AnchorCaptureMode()
        elif args.driver == "magmadoor":
            context.bot_mode_instance = MagmaDoorMode()
        elif args.driver == "magmatravel":
            context.bot_mode_instance = MagmaTravelMode()
        elif args.driver == "magmahideout":
            context.bot_mode_instance = MagmaHideoutMode()
        elif args.driver == "magmaexit":
            context.bot_mode_instance = MagmaExitMode()
        elif args.driver == "aquahideout":
            context.bot_mode_instance = AquaHideoutMode()
        elif args.driver == "mossdeeptravel":
            context.bot_mode_instance = MossdeepTravelMode()
        elif args.driver == "mossdeepgym":
            context.bot_mode_instance = MossdeepGymMode()
        elif args.driver == "mossdeepbadge":
            context.bot_mode_instance = MossdeepBadgeMode()
        elif args.driver == "spacecenter1":
            context.bot_mode_instance = SpaceCenter1Mode()
        elif args.driver == "spacecenter2":
            context.bot_mode_instance = SpaceCenter2Mode()
        elif args.driver == "ki66faint":
            context.bot_mode_instance = Ki66FaintMode()
        elif args.driver == "spacecenter":
            context.bot_mode_instance = SpaceCenterMode()
        elif args.driver == "slateporttheft":
            context.bot_mode_instance = SlateportTheftMode()
        elif args.driver == "teachfull":
            context.bot_mode_instance = TeachFullMode()
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
        elif args.driver == "anchorstory":
            from plugins.custom_modes.story_mode import StoryMode as _SM

            class _AnchorStory(_SM):
                """Let the REAL story bot play until it is standing where an anchor is needed,
                then snapshot. `--driver anchorcapture` navigates there directly and is cheaper;
                use THIS when direct navigation cannot get there but the bot demonstrably can.

                ‼ THAT IS NOT HYPOTHETICAL — it is why this exists. `anchorcapture` could not
                walk SLATEPORT -> MAUVILLE_CITY at all: `_navigate_riding_out` failed 3/3
                identically at ROUTE110 (16, 89) with *"not walkable from ROUTE110, and none of
                the 6 candidate warp route(s) start at a tile that can be walked to from here"*
                — it only ever considered Mauville's six building DOORS and never the plain
                map connection. Story mode makes that trip every single run. So the bot's own
                route is the instrument, and a save it produced is by construction a state the
                bot can actually be in.

                    PYTHONUTF8=1 CAPTURE_TARGET=MAUVILLE_CITY CAPTURE_NAME=mauville_prewattson.ss1 \\
                        CAPTURE_FORBID_FLAG=BADGE03_GET \\
                        py -3.12 story_harness.py slateport.ss1 --driver anchorstory --frames 900000

                ‼ `CAPTURE_FORBID_FLAG` is the whole point of the pre-badge case: the window is
                "in Mauville, before Wattson", and it CLOSES the moment the badge is won. Without
                the guard a slow snapshot silently captures a post-badge save that then answers a
                different question than the one asked — which is exactly how `#24-r116sweep` lost
                two runs to anchors that were the wrong era.
                """

                def run(self):
                    import os

                    from modules.map_data import MapRSE
                    from modules.memory import GameState, get_event_flag, get_game_state
                    from modules.player import get_player_avatar, player_avatar_is_controllable

                    want = MapRSE[os.environ.get("CAPTURE_TARGET", "MAUVILLE_CITY").split(":")[0].strip()]
                    name = os.environ.get("CAPTURE_NAME", f"capture_{want.name.lower()}.ss1")
                    forbid = os.environ.get("CAPTURE_FORBID_FLAG", "")
                    settle = int(os.environ.get("CAPTURE_SETTLE", "60"))
                    force = os.environ.get("CAPTURE_FORCE", "") == "1"
                    out = Path(__file__).resolve().parent / "saves" / name

                    if out.exists() and not force:
                        log(f"[anchorstory] REFUSING to overwrite {out.name} (set CAPTURE_FORCE=1)")
                        context.set_manual_mode()
                        return

                    log(f"[anchorstory] hunting for an anchor on {want.name}"
                        f"{f' while {forbid} is UNSET' if forbid else ''}, settle={settle}f")
                    held = 0
                    frames = 0
                    for _ in super().run():
                        frames += 1
                        yield
                        # the forbidden flag closing the window is a RESULT, not a silent miss
                        if forbid and frames % 30 == 0:
                            try:
                                if get_event_flag(forbid):
                                    log(f"[anchorstory] RESULT wrote=None — {forbid} became SET at "
                                        f"frame {frames} before the anchor was captured. The window "
                                        f"is closed; start from an EARLIER save.")
                                    context.set_manual_mode()
                                    return
                            except Exception:
                                pass
                        try:
                            if get_game_state() is not GameState.OVERWORLD or not player_avatar_is_controllable():
                                held = 0
                                continue
                            avatar = get_player_avatar()
                            if tuple(avatar.map_group_and_number) != tuple(want.value):
                                held = 0
                                continue
                        except Exception:
                            held = 0
                            continue
                        held += 1
                        if held < settle:
                            continue
                        out.write_bytes(context.emulator.get_save_state())
                        badges = [n for n in range(1, 9) if get_event_flag(f"BADGE0{n}_GET")]
                        log(f"[anchorstory] RESULT wrote={out.name} map={want.name} "
                            f"tile={tuple(get_player_avatar().local_coordinates)} badges={badges} "
                            f"frames={frames}")
                        log("[anchorstory] ‼ verify it with: py -3.12 probe_anchor_inventory.py "
                            f"--filter {out.stem}")
                        context.set_manual_mode()
                        return
                    log(f"[anchorstory] RESULT wrote=None — story mode ended after {frames} frames "
                        f"without ever standing controllable on {want.name}.")
                    context.set_manual_mode()

            context.bot_mode_instance = _AnchorStory()
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
            # ‼ FIXED 2026-08-26: this imported from `modules.game`, where the function has never
            # lived in this fork (`modules.text_printer:92`), so EVERY STUCK-OW line printed
            # `textprinter=<err cannot import name ...>` and the field was a DEAD INSTRUMENT —
            # found by the `#26-mossdeeppuzzlespeed` profiling pass reading a real run log. The
            # try/except made it fail silent-but-visible, which is why it survived: a broken
            # diagnostic that still prints SOMETHING never trips a gate.
            from modules.text_printer import get_text_printer as _gtp

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

# PARTY ACCOUNTING STAGE 0 (`modules/party_accounting.py`, `06-DECISIONS-LOG.md` RULING D).
# ‼ THIS IS THE MEASUREMENT STAGE 0 EXISTS TO PRODUCE: over a whole driven run, did A
# (`gPlayerPartyCount`) ever actually differ from B (`len(get_party())`)? Reporting it here rather
# than from bot code keeps Stage 0's promise that NO call site is wired — the harness is a test
# tool, not a decision path. ‼ Read the SAMPLE COUNTS on the summary line: a zero beside "0 scans"
# is not a measurement, and this project has twice believed a negative from a detector that could
# not have returned positive.
try:
    from modules import party_accounting

    for line in party_accounting.summary_lines():
        log(line)
except Exception as e:
    log(f"[PARTY-ACCT] err {e} — treat this run as UNMEASURED for party accounting, not as clean")

# ‼‼ AND APPEND IT TO A DURABLE LEDGER, because THE LOG IS NOT ONE.
# ⛔ HISTORICAL, AND STILL THE REASON THIS LEDGER EXISTS: `LOG` used to be `harness_<build>.log` —
# one fixed name per build, opened `"w"` — so **every drive TRUNCATED the previous one**, and
# (P3b)'s criterion ("≥5 drives across ≥3 drivers") was UNREACHABLE by log-scanning: the collector
# could only ever see the most recent run. Found 2026-08-15 by asking whether the tool shipped the
# day before could actually produce the reading it demands. It could not.
# ✅ The collision is FIXED as of 2026-08-16 (`#24-orphans` (4)) — log names are now unique per run.
# ‼ THE LEDGER STAYS ANYWAY, and not out of inertia: unique logs make the history *recoverable*,
# not *aggregated*. A criterion over many drives should read one append-only file, never glob a
# directory of transcripts whose retention nobody guarantees (`*.log` is gitignored).
# ⇒ The measurement now accumulates in its OWN append-only file, independent of the harness log.
# ‼ APPEND MODE ONLY — `open(..., "a")` never reads the existing bytes, so this cannot round-trip-
# corrupt the ledger the way a read-modify-write would (`08-MISTAKES.md`, twice).
# ⛔ And it is written OUTSIDE the try above on purpose: if the summary itself failed, the run must
# still be recorded — as UNMEASURED. A run that vanishes from the ledger is indistinguishable from
# a run that never happened, which is how a broken observer would quietly improve the statistics.
try:
    import json as _json
    import time as _time

    from modules import party_accounting as _pa

    _recomputes, _scans = _pa.sample_counts()
    _entry = {
        "when": _time.strftime("%Y-%m-%dT%H:%M:%S"),
        "driver": getattr(args, "driver", None) or "<none>",
        # ‼ WHICH FORK PRODUCED THIS ROW. Added 2026-08-15 during the promotion verification: a
        # `--build custom` drive and a sandbox drive were previously INDISTINGUISHABLE in the
        # ledger, so a promotion-verification run would have silently joined the (P3b) population
        # as though it were another sandbox sample. Attribution beats a bigger n.
        "build": getattr(args, "build", "sandbox"),
        "state": str(getattr(args, "state", "")),
        "frames_run": step + 1,
        "recomputes": _recomputes,
        "scans": _scans,
        "divergences": _pa.observed(),
        # ‼ The observer's own fault latch lives in `pokemon_party`, not here — read it from the
        # module that sets it rather than inferring it. A run whose observer broke is UNMEASURED
        # and must not be counted as a clean drive by the collector.
        "observer_broke": bool(
            getattr(__import__("modules.pokemon_party", fromlist=["x"]),
                    "_accounting_fault_reported", False)),
    }
    with open(SCRATCH / "party_accounting_ledger.jsonl", "a", encoding="utf-8") as _ledger:
        _ledger.write(_json.dumps(_entry) + "\n")
    log(f"[PARTY-ACCT] ledger += {_entry['driver']} {_recomputes} recomputes "
        f"(party_accounting_ledger.jsonl)")
except Exception as e:
    # A ledger failure must be LOUD: a silently missing row makes the population look smaller and
    # cleaner than it is, which is the exact bias (P3b) is trying to avoid.
    log(f"[PARTY-ACCT] ‼ LEDGER WRITE FAILED ({e!r}) — this run is NOT counted toward (P3b). "
        f"Do not treat the collector's totals as complete for this session.")
logf.close()
