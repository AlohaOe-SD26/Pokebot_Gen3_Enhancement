r"""OBSERVE-ONLY: the REAL `StoryMode._should_catch` adapter on real fixtures, for encounters with species of different
catch rates (USER RULING 20 Phase 0, 2026-09-26).

WHY: `probe_dexcatch_rate.py` gates the pure pieces; this runs the ADAPTER end-to-end against a real bag, party, flags
and Pokédex (the rule: a component is proven only by a run that PRODUCES its inputs, never one that seeds them). Nothing
is caught or thrown — `_should_catch` is only evaluated. Prints each verdict, the expected-throws input, the DEXFENCE
line it logged, and a CONTROL: a species the fixture already owns must be refused as "already owned".

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dexcatch_rate_live.py [fixture.ss1 ...]
"""
import pathlib
import sys
import types

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

SAVES = REPO / "tools" / "story-dev" / "saves"
DEFAULT = ["post_winona.ss1", "post_mtpyre.ss1", "fortree_gym_wedge.ss1"]
# (species, catch rate per species.json) — low, mid, high
PROBES = ["Absol", "Zangoose", "Linoone", "Wingull"]


def main() -> int:
    import plugins.custom_modes.story_mode as SM
    from modules.items import get_item_bag
    from modules.pokedex import get_pokedex
    from modules.pokemon import get_species_by_name
    from modules.pokemon_party import get_party

    logged: list = []
    real_log = SM._log_story_event
    SM._log_story_event = lambda msg, cat="STORY", *a, **k: logged.append(f"[{cat}] {msg}")
    try:
        for name in sys.argv[1:] or DEFAULT:
            path = SAVES / name
            print(f"\n--- {name} ---")
            if not path.exists():
                print("  (missing)")
                continue
            context.emulator.load_save_state(path.read_bytes())
            for _ in range(30):
                context.emulator.run_single_frame()
            party = [p for p in get_party() if p is not None]
            bag = get_item_bag()
            print(f"  party {len(party)}: {[p.species.name for p in party]}  balls: "
                  f"{[(s.item.name, s.quantity) for s in bag.poke_balls]}")
            mode = SM.StoryMode()
            mode.reset_per_run_state()
            owned = sorted(get_pokedex().owned_species, key=lambda s: s.national_dex_number)
            control = owned[0].name if owned else None
            for sp_name in PROBES + ([control] if control else []):
                sp = get_species_by_name(sp_name)
                enc = types.SimpleNamespace(pokemon=types.SimpleNamespace(species=sp), is_shiny=False)
                before = len(logged)
                verdict = mode._should_catch(enc)
                et = SM._expected_throws_for(sp, bag)
                line = logged[before] if len(logged) > before else "(no line)"
                tag = "CONTROL " if sp_name == control else ""
                print(f"  {tag}{sp_name:<9} rate={sp.catch_rate:<3} expected={et if et is None else round(et, 1)!s:<6} "
                      f"catch={verdict!s:<5} reason={mode._dex_catch_last_reason!r}")
                print(f"           logged: {line}")
    finally:
        SM._log_story_event = real_log
    return 0


if __name__ == "__main__":
    sys.exit(main())
