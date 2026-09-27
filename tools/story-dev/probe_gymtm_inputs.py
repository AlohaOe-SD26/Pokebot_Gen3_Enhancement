r"""OBSERVE-ONLY: which Fortree-era fixtures would USER RULING 19's TM teach fire on? (2026-09-26)

WHY: a drive of the gym-TM teach is vacuous on a fixture without the TMs in the bag or without a TRAINED team member that
can learn one. This prints, per fixture: map, badges, the TM/HM pocket, and for TM34 Shock Wave / TM50 Overheat / TM39
Rock Tomb every party member that can learn it (by ITEM — a string reads False), with level and moves.
CONTROLS: a phantom flag is refused; `can_learn_tm_hm` must be True for a known learner somewhere (else it is broken).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gymtm_inputs.py [fixture.ss1 ...]
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

PROFILE = "gymtmprobe"
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
DEFAULT = ["fortree_gym_wedge.ss1", "devon_scope_got.ss1", "ch13_fortree_door.ss1", "ch13_r10_wedge.ss1",
           "ch13_r3_wedge.ss1", "norman_done.ss1"]
TMS = ("TM34", "TM50", "TM39")


def flag(name: str) -> bool:
    if name not in memory._event_flags:
        raise KeyError(f"flag {name!r} is NOT in the flag table — refusing to report a phantom False")
    return bool(get_event_flag(name))


def main() -> int:
    from modules.items import get_item_bag, get_item_by_name

    names = sys.argv[1:] or DEFAULT
    print("=" * 100)
    print("OBSERVE-ONLY — USER RULING 19 inputs per fixture (TM34 Shock Wave / TM50 Overheat / TM39 Rock Tomb)")
    print("=" * 100)
    try:
        flag("THIS_FLAG_DOES_NOT_EXIST_2026_09_26")
        print("  CONTROL FAILED: a phantom flag name was accepted")
        return 1
    except KeyError:
        print("  ok   control: a phantom flag name is REFUSED")
    items = {t: get_item_by_name(t) for t in TMS}
    any_learner = False
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
        try:
            mname = MapRSE(tuple(av.map_group_and_number)).name
        except Exception:  # noqa: BLE001 - an unknown map is printed as such
            mname = str(tuple(av.map_group_and_number))
        badges = [n for n in range(1, 9) if flag(f"BADGE0{n}_GET")]
        print(f"  at {mname} {tuple(av.local_coordinates)} badges={badges} money={get_player().money}")
        pocket = [f"{s.item.name}x{s.quantity}" for s in get_item_bag().tms_hms]
        print(f"  TM/HM pocket: {pocket}")
        party = [m for m in get_party() if m is not None and not m.is_egg]
        top = max((m.level for m in party), default=0)
        for m in party:
            moves = [mv.move.name for mv in m.moves if mv is not None]
            can = [t for t, it in items.items() if m.species.can_learn_tm_hm(it)]
            any_learner = any_learner or bool(can)
            print(f"    {m.species.name:<11} L{m.level:<3} (top-{top - m.level:>2}) can={can} moves={moves}")
        # What the RULING 19 planner WOULD choose here, for every possible wall (observe-only; nothing is taught).
        from modules.story import gym_tm_teach as G

        owned, tm_items = G.owned_tms()
        views = [G.mon_view(i, p, tm_items) for i, p in enumerate(get_party()) if p is not None]
        prot = G.protected_pids(None)
        for boss in ("Winona", "Juan"):
            roster = G.GYM_ROSTERS[boss]
            for wall in (m.species for m in roster):
                plan, why = G.plan_teach(boss, roster, wall, views, owned, set(), prot)
                what = (f"{plan.tm} {plan.move} -> {plan.species} replacing {plan.replaced} "
                        f"[share {plan.share:.0%}, clean {plan.drawback_free}, cov {plan.coverage}]") if plan else "NO PLAN"
                print(f"    PLAN {boss:<7} wall={wall:<10} {what}")
                if plan is None:
                    print(f"         why: {why[:5]}")
    print()
    print("  CONTROL " + ("ok: at least one learner seen (can_learn_tm_hm works)" if any_learner else
                          "FAILED: no learner anywhere — check can_learn_tm_hm before trusting this table"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
