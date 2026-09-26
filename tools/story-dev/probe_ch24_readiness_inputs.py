r"""OBSERVE-ONLY: what does each §Ch24-entry fixture actually hold? (`#26-ch24organic`, step 1)

WHY THIS EXISTS (2026-09-26). `#26-ch24organic` R1 is a READINESS REFUSAL outside the one-way Elite Four:
raise on Ever Grande (18,6) unless every party member meets `CH24_LEVEL_FLOOR` and the League basket is
complete. A Tier 2 cold start could not BEGIN it: the recon (`ai-research-notes/2026-09-26-ch24-production-
fly-RECON.md`) never READ the candidate fixtures, so the R1 discriminator ("fires on the under-levelled one,
not on the ready one") was unproven. This prints, per fixture, every input R1 and the Fly bridge would read.

WHAT IT PRINTS: map/tile/state, badges, money; per PID: species, level, HP, moves+PP, whether it knows Fly,
whether it CAN learn Fly; `ch24_trainees_below_floor()` (production's own predicate); the League basket vs
`LEAGUE_BASKET` (production's own reader); flags LANDMARK_POKEMON_LEAGUE / RECEIVED_HM_FLY / BADGE06_GET /
IS_CHAMPION / SYS_GAME_CLEAR — each ASSERTED to exist in the flag table first (a phantom name reads False
forever); HM02 in the bag.

CONTROLS (rule: prove the instrument can see something you already know): BADGE08_GET must read True on
every late fixture, and a name that is NOT in the flag table must be REFUSED, not silently read False.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch24_readiness_inputs.py [fixture.ss1 ...]
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

PROFILE = "ch24probe-readiness"
if not profile_directory_exists(PROFILE):
    create_profile(PROFILE, list_available_roms()[0])
profile = load_profile_by_name(PROFILE)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"

from modules import memory  # noqa: E402
from modules.map_data import MapRSE  # noqa: E402
from modules.memory import GameState, get_event_flag, get_game_state  # noqa: E402
from modules.player import get_player, get_player_avatar  # noqa: E402
from modules.pokemon_party import get_party  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
DEFAULT = ["post_league_shop.ss1", "post_ch24ready.ss1", "post_ch24_atdoor.ss1", "post_fly.ss1",
           "post_moveset.ss1", "post_ever_grande.ss1"]
FLAGS = ["LANDMARK_POKEMON_LEAGUE", "RECEIVED_HM_FLY", "BADGE06_GET", "BADGE08_GET",
         "IS_CHAMPION", "SYS_GAME_CLEAR", "ENTERED_ELITE_FOUR"]


def flag(name: str):
    if name not in memory._event_flags:
        raise KeyError(f"flag {name!r} is NOT in the flag table — refusing to report a phantom False")
    return bool(get_event_flag(name))


def main() -> int:
    from modules.items import get_item_bag
    from modules.pokemon import get_move_by_name
    from modules.story import pokemon_league as PL
    from modules.story import victory_road as VR

    names = sys.argv[1:] or DEFAULT
    print("=" * 100)
    print("OBSERVE-ONLY — §Ch24 readiness inputs per fixture (`#26-ch24organic` step 1)")
    print(f"CH24_LEVEL_FLOOR = {PL.CH24_LEVEL_FLOOR}   LEAGUE_BASKET = {VR.LEAGUE_BASKET}")
    print("=" * 100)
    # ⛔ NEGATIVE CONTROL FIRST: a phantom name must be refused, not read as False.
    try:
        flag("THIS_FLAG_DOES_NOT_EXIST_2026_09_26")
        print("  ⛔ CONTROL FAILED: a phantom flag name was accepted — every flag below is suspect")
        return 1
    except KeyError:
        print("  ok   control: a phantom flag name is REFUSED (not read as False)")

    for name in names:
        path = SAVES / name
        print(f"\n--- {name} ---")
        if not path.exists():
            print("  (missing)")
            continue
        context.emulator.load_save_state(path.read_bytes())
        for _ in range(30):
            context.emulator.run_single_frame()
        state = get_game_state()
        av = get_player_avatar()
        mp = tuple(av.map_group_and_number)
        try:
            mname = MapRSE(mp).name
        except Exception:  # noqa: BLE001
            mname = f"UNKNOWN{mp}"
        badges = [n for n in range(1, 9) if flag(f"BADGE0{n}_GET")]
        print(f"  at {mname} {tuple(av.local_coordinates)}  state={state.name}  badges={badges}  "
              f"money=₽{get_player().money:,}")
        if 8 not in badges:
            print("  ⚠ CONTROL: BADGE08_GET is False on a fixture expected to be late — check the reader")
        print("  flags: " + ", ".join(f"{f}={flag(f)}" for f in FLAGS))
        hm02 = False
        try:
            bag = get_item_bag()
            hm02 = any(getattr(s.item, "name", "") in ("HM02", "HM02 Fly") and s.quantity > 0
                       for s in list(bag.tms_hms))
        except Exception as error:  # noqa: BLE001
            print(f"  (bag unreadable: {error})")
        print(f"  HM02 in bag: {hm02}")
        for mon in get_party():
            if mon is None:
                continue
            moves = [f"{m.move.name}:{m.pp}" for m in mon.moves if m is not None]
            knows_fly = any(m is not None and m.move.name == "Fly" for m in mon.moves)
            # ⛔ `can_learn_tm_hm` takes an Item or Move OBJECT; a string silently returns False (the
            #   phantom-name shape again). Positive control below: Swellow must read True.
            can_fly = bool(mon.species.can_learn_tm_hm(get_move_by_name("Fly")))
            print(f"    {mon.species.name:<11}#{mon.personality_value:08X} L{mon.level:<3} "
                  f"HP {mon.current_hp:>3}/{mon.total_hp:<3} knowsFly={knows_fly} canLearnFly={can_fly} "
                  f"moves={moves}")
        below = PL.ch24_trainees_below_floor()
        print(f"  ch24_trainees_below_floor() = {[(f'{sp}#{pid:08X}', lv) for pid, sp, lv in below]}")
        stock = VR.bag_healing_stock()
        short = {n: q - stock.get(n, 0) for n, q in VR.LEAGUE_BASKET if stock.get(n, 0) < q}
        print(f"  basket stock = { {n: stock.get(n, 0) for n, _q in VR.LEAGUE_BASKET} }  short={short or 'none'}")
        print(f"  ⇒ R1 would {'REFUSE' if (below or short) else 'PASS'} here "
              f"(below_floor={len(below)}, basket_short={bool(short)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
