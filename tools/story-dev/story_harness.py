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

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ap = argparse.ArgumentParser()
ap.add_argument("state", help=".ss1 save state to load (basename in scratchpad or full path)")
ap.add_argument("--inject-treecko", action="store_true", help="inject a Lv15 Treecko at exp_for_16 - 1 as lead")
ap.add_argument("--inject-weak", action="store_true", help="inject a lone Lv3 Poochyena (loses everything → forces a whiteout, for defeat-recovery testing)")
ap.add_argument("--set-balls", type=int, default=None, help="force the Poké Ball count (test out-of-balls provisioning)")
ap.add_argument("--inject-at", type=int, default=8, help="frame to inject the party at")
ap.add_argument("--frames", type=int, default=60000)
ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"])
ap.add_argument("--profile", default="repro-ml")
ap.add_argument("--driver", default="spin", choices=["spin", "story", "rival", "ch5recon", "martrecon", "martbuy", "healtest", "traintest", "gymtest", "pokenavtut", "pokenavclear", "pokenavskip", "pokenavfaith", "sailrecon", "rivalretry", "saildewford"])
ap.add_argument(
    "--break-state",
    action="store_true",
    help="FAULT INJECTION: simulate the user's env — make get_learn_move_state never "
    "report AskWhetherToLearn (returns Unknown) and force is_waiting_for_input False, "
    "so ONLY the on-screen text can drive the yes/no. Old code hangs; the fix must not.",
)
ap.add_argument("--log", default=None)
ap.add_argument("--video", action="store_true", help="enable the BG/OBJ renderer (needed to drive the PokéNav app)")
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
context.video = bool(getattr(args, "video", False))  # renderer on when --video (PokéNav app needs it)
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
    """Isolated test: heal at Oldale PC and observe enter → heal → EXIT (the suspect)."""

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
            log("[heal] DONE — healed and exited cleanly")
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
            _pb = "Poké Ball"
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

        log(f"[clr] phase2: tutorial active? {triggered} — advancing intro + selecting POKENAV (index 3)")
        if triggered:
            yield from wait_for_multiple_choice_question(3)
            log(f"[clr] after multichoice-select: VAR_RESULT={get_event_var('VAR_RESULT')} "
                f"gs={get_game_state()} tasks={_tasks()}")
            for i in range(30):
                step += 1
                _dump("post-select", step)
                yield

            log("[clr] phase3: FORCE_CALL_READY — drive Match Call with A; log gs/script transitions")
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

        # ENABLE the renderer — the PokeNav app won't advance without it.
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

        # Phase 2: SCRIPTED probe — reach the main menu, screenshot, then run a button
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
        log("[retry] calling fight_rustboro_rival — expect it to step onto y=53 and RE-ENGAGE")
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
                log(f"[sail] *** MULTICHOICE up at f{step} — 'where are we bound?' ***")
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
    win — proving the Scientist tutorial never fires and the rival still triggers."""

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
        #    — the far tile (40,8) had no path (Route 116 has blocked tiles).
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
        # 2b. Cross Route 116 east toward the tunnel door approach (47,9) — the door
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
        #    Approach from the west — its line of sight triggers the battle. Navigate
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
    the trainer battle — the exact ML-11 edge case (move-learn as the trainer
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
    log("[inject] lone Poochyena Lv3 (will lose → whiteout)")


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


# ---- optional fault injection: simulate the user's failing environment -------
if args.break_state:
    import modules.battle_move_replacing as _bmr
    import modules.tasks as _tasks_mod

    _orig_gls = _bmr.get_learn_move_state

    def _broken_gls():
        s = _orig_gls()
        # The Emerald battle "Delete a move?" Yes/No is detected ONLY by a fragile
        # script-offset; simulate that offset NEVER matching → state stuck Unknown.
        if s == _bmr.LearnMoveState.AskWhetherToLearn:
            return _bmr.LearnMoveState.Unknown
        return s

    _bmr.get_learn_move_state = _broken_gls
    # is_waiting_for_input reads the field printer → unreliable in battle; force the
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
injected = not (args.inject_treecko or args.inject_weak)

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
_WANT_POST_RIVAL_SAVE = bool(_os_hook.environ.get("SAVE_POST_RIVAL"))
for step in range(args.frames):
    context.frame = step

    # Capture the post-rival save once the rival is defeated — ONLY when explicitly asked
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
                log(f"f{step}: *** DEFEATED_RIVAL_RUSTBORO stable — saved post_rival.ss1 ***")
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
            pb = get_item_by_name("Poké Ball")
            debug_write_item_bag(
                items=ne(bag.items), key_items=ne(bag.key_items),
                poke_balls=([ItemSlot(pb, args.set_balls)] if args.set_balls > 0 else []),
                tms_hms=ne(bag.tms_hms), berries=ne(bag.berries),
            )
            log(f"[setup] set Poké Balls to {args.set_balls}")
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
        elif args.driver == "pokenavfaith":
            context.bot_mode_instance = PokenavFaithMode()
        elif args.driver == "martbuy":
            context.bot_mode_instance = MartBuyMode()
        elif args.driver == "healtest":
            context.bot_mode_instance = HealTestMode()
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
        log(f"f{step}: battle_is_active -> {ba}  party=[{party_snapshot()}]")
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
    sig = (
        ctrl,
        game_state.name if hasattr(game_state, "name") else str(game_state),
        get_current_battle_script_instruction() if ba else "",
        ml,
        ps,
    )
    if sig == last_sig:
        no_progress += 1
    else:
        no_progress = 0
        last_sig = sig
    # STUCK-OVERWORLD DIAGNOSTIC: the reliable "is the game actually blocked"
    # signal is player_avatar_is_controllable() (gDisplayedStringBattle/gBattleMainFunc
    # go STALE after a battle, so they lie). Log a compact trace on change whenever
    # we're in the overworld, NOT in a battle, but NOT controllable — the real hang.
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
    if no_progress == 900 and not globals().get("_stuck_saved"):
        globals()["_stuck_saved"] = True
        try:
            import pathlib

            _sp = SAVES / "midstuck.ss1"
            _sp.write_bytes(context.emulator.get_save_state())
            log(f"f{step}: SAVED mid-stuck state to midstuck.ss1 (bt={(battle_text() or '')!r})")
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

            _tasks = [t.name for t in _gt()]
        except Exception:
            _tasks = "?"
        _dsig = (get_main_battle_callback(), get_current_battle_script_instruction(), _tpstate, ctrl, ps)
        if _dsig != globals().get("_last_dsig"):
            globals()["_last_dsig"] = _dsig
            log(f"f{step}: STUCK-OW cb={get_main_battle_callback()} instr={get_current_battle_script_instruction()} "
                f"textprinter={_tpstate} tasks={_tasks} ctrl={ctrl} bt={(battle_text() or '')!r} party=[{ps}]")
    if no_progress in (1200, 3000, 8000, 15000):
        log(
            f"f{step}: !!! NO-PROGRESS x{no_progress} sig={sig} "
            f"instr={get_current_battle_script_instruction()} cb={get_main_battle_callback()} "
            f"tasks={active_ml_tasks()} bt={battle_text()!r} bot_mode={context.bot_mode}"
        )
    if no_progress >= 20000:
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
