r"""OBSERVE-ONLY: what does each fixture hold that USER RULING 18's early purchase + League reserve read? (2026-09-26)

WHY THIS EXISTS. `modules/story/league_reserve.py` arms the reserve from game state (the Juan-era flag, the Elite-Four
entry flag, the champion flag, being on a sealed §Ch24 map) and plans a purchase from the bag and the wallet.
Predictions for `--driver earlybasket` and the reserve arms must be computed from fixtures, not assumed.

WHAT IT PRINTS per fixture: map/tile, money, badges 7/8; the four flags (each ASSERTED to exist first); the bag's
basket-line stock (summed across stacks); production's own `reserve_active()`, `reserved_quantities()`,
`in_early_basket_era()` and `early_basket_plan()` at Sootopolis prices.

CONTROLS: a phantom flag name must be REFUSED; the pre-era fixture must read the reserve OFF, the sealed-map fixture OFF.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_reserve_inputs.py [fixture.ss1 ...]
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

PROFILE = "reserveprobe"
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
DEFAULT = ["post_mtpyre.ss1", "post_hm07.ss1", "post_badge8.ss1", "post_league_shop.ss1", "post_phoebe_L75.ss1",
           "post_hof_cleared.ss1"]
FLAGS = ["BADGE07_GET", "BADGE08_GET", "SOOTOPOLIS_ARCHIE_MAXIE_LEAVE", "ENTERED_ELITE_FOUR", "IS_CHAMPION"]


def flag(name: str) -> bool:
    if name not in memory._event_flags:
        raise KeyError(f"flag {name!r} is NOT in the flag table — refusing to report a phantom False")
    return bool(get_event_flag(name))


def main() -> int:
    from modules.items import get_item_by_name
    from modules.story import league_reserve as LR

    names = sys.argv[1:] or DEFAULT
    print("=" * 100)
    print("OBSERVE-ONLY — USER RULING 18 reserve + early-purchase inputs per fixture")
    print(f"LEAGUE_BASKET = {LR.basket()}   BUY_ORDER = {LR.BUY_ORDER}   CASH_FLOOR = {LR.CASH_FLOOR}")
    print("=" * 100)
    try:
        flag("THIS_FLAG_DOES_NOT_EXIST_2026_09_26")
        print("  ⛔ CONTROL FAILED: a phantom flag name was accepted — every flag below is suspect")
        return 1
    except KeyError:
        print("  ok   control: a phantom flag name is REFUSED (not read as False)")
    prices = {n: get_item_by_name(n).price for n in LR.basket()}
    print(f"  prices (items.json) = {prices}")

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
        money = get_player().money
        print(f"  at {mname} {tuple(av.local_coordinates)} state={get_game_state().name} money=₽{money:,}")
        print("  flags: " + ", ".join(f"{f}={flag(f)}" for f in FLAGS))
        stock = LR._stock_by_name(list(LR.basket()))
        print(f"  basket stock = {stock}")
        print(f"  reserve_active() = {LR.reserve_active()}   reserved_quantities() = {LR.reserved_quantities()}")
        print(f"  on sealed map = {LR._on_sealed_map()}   in_early_basket_era() = {LR.in_early_basket_era()}")
        plan = LR.early_basket_plan(stock, money, prices)
        cost = sum(prices[n] * q for n, q in plan)
        print(f"  early_basket_plan() = {plan}  cost ₽{cost:,} -> leaves ₽{money - cost:,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
