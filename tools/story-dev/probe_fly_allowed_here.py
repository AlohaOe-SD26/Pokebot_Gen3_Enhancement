# -*- coding: utf-8 -*-
"""CAN THE BOT ACTUALLY FLY FROM WHERE A FIXTURE IS PARKED? Gen 3 refuses Fly in caves and indoors.

⛔⛔ WHY THIS EXISTS, AND IT IS THE §Ch24 CHAPTER'S **FIRST MOVE**. The finished gauntlet party,
`post_e4ice_FINAL.ss1`, is parked at **VICTORY_ROAD_1F (15,39)** — the grind tile — and the plan for
reaching the League door was *"it is ONE Fly away"*. It is not, from there: **VICTORY_ROAD_1F is
`map_type=Underground`, and Fly is refused on it.**

‼‼ AND `fly_to_destination` WOULD NOT HAVE TOLD US. Its three guards (`pokemon_league.py:1222-1236`)
are: a party member knows Fly, `BADGE06_GET` is set, and the destination flag is set. **None of them
asks whether the CURRENT MAP allows Fly.** All three pass in a cave, and the failure then happens
inside the field-move menu, far from the cause.

⭐ THE ALLOW-LIST IS NOT "outdoors", AND GUESSING IT IS HOW I GOT THIS WRONG FIRST TIME.
VERIFIED at source — `src/overworld.c:1366-1375`:

    bool8 Overworld_MapTypeAllowsTeleportAndFly(u8 mapType)
    {
        if (mapType == MAP_TYPE_ROUTE
         || mapType == MAP_TYPE_TOWN
         || mapType == MAP_TYPE_OCEAN_ROUTE
         || mapType == MAP_TYPE_CITY)
            return TRUE;
        ...

⇒ **exactly four types.** `Underground` (caves) and `Indoor` are both refused, and so is
`Underwater`. My first version of this check tested `map_type == "Indoor"` and therefore reported
**"✅ yes"** for a cave — a FALSE GREEN on the one fixture the question was asked about. That is the
third time in one day a predicate of mine tested a narrower thing than the claim; the fix is to
encode the decomp's list verbatim rather than a paraphrase of it.

    cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_fly_allowed_here.py [save.ss1 ...]
Exit 0 always — this is a READING, not a gate. It answers "can I Fly from here", per fixture.
"""
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0

from modules.map import get_map_data_for_current_position
from modules.map_data import MapRSE
from modules.player import get_player_avatar

SAVES = REPO / "tools" / "story-dev" / "saves"
BAR = "=" * 100

#: ⛔ THE DECOMP'S LIST, VERBATIM — `src/overworld.c:1366-1375`. NOT "is it outdoors".
#: Our `map_type` renders these as strings; both spellings of the ocean route are accepted because
#: the renderer's exact form is not worth guessing at.
FLY_ALLOWED = ("Route", "Town", "City", "Ocean Route", "OceanRoute", "Ocean_Route")

DEFAULT = ("post_e4ice_FINAL.ss1", "post_ch24_atdoor.ss1", "post_ch24ready.ss1",
           "post_sidney_door_open.ss1", "post_league_shop.ss1")


def main() -> int:
    names = sys.argv[1:] or list(DEFAULT)
    print(BAR)
    print("  CAN FLY BE USED FROM HERE?  (decomp allow-list: Route / Town / City / Ocean Route)")
    print(BAR)
    for name in names:
        f = SAVES / name
        if not f.is_file():
            print(f"  {name:<28} (missing)")
            continue
        context.emulator.load_save_state(f.read_bytes())
        for _ in range(20):
            context.emulator.run_single_frame()
        avatar = get_player_avatar()
        try:
            where = MapRSE(avatar.map_group_and_number).name
        except Exception:  # noqa: BLE001 — an unknown map id is a reading, not a crash
            where = str(avatar.map_group_and_number)
        try:
            map_type = get_map_data_for_current_position().map_type
        except Exception as error:  # noqa: BLE001
            map_type = f"ERR:{type(error).__name__}"
        ok = map_type in FLY_ALLOWED
        verdict = "✅ yes" if ok else f"⛔ NO — Fly is refused on map_type={map_type}"
        print(f"  {name:<28} {where:<34} {avatar.local_coordinates!s:<9} "
              f"map_type={map_type:<12} {verdict}")
    print(BAR)
    print("  ‼ `fly_to_destination` guards on: knows Fly / BADGE06 / destination unlocked.")
    print("    It does NOT guard on the current map allowing Fly — see the docstring.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
