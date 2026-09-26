r"""OBSERVE-ONLY: what does each candidate fixture hold that USER RULING 17's Amulet Coin leg reads? (2026-09-26)

WHY THIS EXISTS. `modules/story/amulet_coin.py` gates on four flags, two house-state vars, the player's gender (which
house), bag space, and the party (who holds it). Predictions for `--driver amuletcoin` must be computed from the
fixture, not assumed — a vacuous A/B has been handed off before (CLAUDE.md, Tier 2 (4)).

WHAT IT PRINTS per fixture: map/tile/state; the flags (each ASSERTED to exist in the flag table first — a phantom
name reads False forever); `VAR_LITTLEROOT_HOUSES_STATE_{MAY,BRENDAN}`; gender ⇒ house; ITEMS-pocket room for the
coin and any coin already held; production's own `amulet_coin_pending()` and `pick_holder()`.

CONTROLS: a phantom flag name must be REFUSED; BADGE01_GET must read True on every fixture listed (all are late).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_amulet_inputs.py [fixture.ss1 ...]
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

PROFILE = "amuletprobe"
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
from modules.memory import get_event_flag, get_event_var, get_game_state  # noqa: E402
from modules.player import get_player, get_player_avatar  # noqa: E402
from modules.pokemon_party import get_party  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
DEFAULT = ["norman_done.ss1", "post_mtpyre.ss1"]
FLAGS = ["BADGE01_GET", "BADGE05_GET", "BADGE06_GET", "HAS_MATCH_CALL", "ENABLE_MOM_MATCH_CALL",
         "RECEIVED_AMULET_COIN", "RECEIVED_HM_SURF"]


def flag(name: str) -> bool:
    if name not in memory._event_flags:
        raise KeyError(f"flag {name!r} is NOT in the flag table — refusing to report a phantom False")
    return bool(get_event_flag(name))


def main() -> int:
    from modules.items import get_item_bag
    from modules.story import amulet_coin as AC

    names = sys.argv[1:] or DEFAULT
    print("=" * 100)
    print("OBSERVE-ONLY — USER RULING 17 Amulet Coin inputs per fixture")
    print("=" * 100)
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
        av = get_player_avatar()
        mp = tuple(av.map_group_and_number)
        try:
            mname = MapRSE(mp).name
        except Exception:  # noqa: BLE001 - an unknown map is PRINTED as such, never guessed
            mname = f"UNKNOWN{mp}"
        print(f"  at {mname} {tuple(av.local_coordinates)} state={get_game_state().name} "
              f"money=₽{get_player().money:,} gender={get_player().gender}")
        values = {f: flag(f) for f in FLAGS}
        print("  flags: " + ", ".join(f"{k}={v}" for k, v in values.items()))
        if not values["BADGE01_GET"]:
            print("  ⚠ CONTROL: BADGE01_GET is False on a late fixture — check the reader")
        print(f"  vars: HOUSES_STATE_MAY={get_event_var('LITTLEROOT_HOUSES_STATE_MAY')} "
              f"HOUSES_STATE_BRENDAN={get_event_var('LITTLEROOT_HOUSES_STATE_BRENDAN')} "
              f"(module reads {AC._houses_state()})")
        bag = get_item_bag()
        coin = AC._coin()
        print(f"  bag: Amulet Coin x{bag.quantity_of(coin)}  room_for_coin={bag.has_space_for(coin)}  "
              f"ITEMS pocket={[f'{s.item.name}x{s.quantity}' for s in bag.items]}")
        party = get_party()
        for i, mon in enumerate(party):
            if mon is None:
                continue
            held = getattr(getattr(mon, "held_item", None), "name", None)
            print(f"    [{i}] {mon.species.name:<11}#{mon.personality_value:08X} L{mon.level:<3} "
                  f"HP {mon.current_hp:>3}/{mon.total_hp:<3} held={held} egg={mon.is_egg}")
        print(f"  amulet_coin_pending() = {AC.amulet_coin_pending()}   pick_holder() = {AC.pick_holder(party)}   "
              f"coin_holder() = {AC.coin_holder()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
