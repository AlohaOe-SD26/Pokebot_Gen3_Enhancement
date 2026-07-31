"""#24-smashroute / KI-41 — does the obstacle finder pick the RIGHT rock, live?

`modules/story/obstacle_clearing.py` reads the ROM's object events, keeps the ones whose
script is a field move obstacle, and offers only those it can both REACH and CLEAR. This
probe checks it against the choke KI-41 measured, on a real emulator, and checks the two
ways it could be wrong:

  * a wrong YES — offering a rock the bot cannot stand next to, or cannot smash. That is the
    expensive error (a long walk to nowhere; KI-24b, the refuted gateway waypoints), so the
    capability arm is tested by DENYING the capability and requiring the answer to flip.
  * a wrong NO — refusing the rock that `early_game.travel_lavaridge_to_petalburg` already
    hard-codes at (18,101), which would leave the counter chain blocked.

Run: PYTHONUTF8=1 py -3.12 tools/story-dev/probe_smash_plan.py
"""

import pathlib
import sys

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
context.bot_mode = "Manual"

from modules.map_data import MapRSE
from modules.player import get_player_avatar
from modules.story import obstacle_clearing as oc

SAVES = REPO / "tools" / "story-dev" / "saves"
R111 = tuple(MapRSE.ROUTE111.value)
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def main() -> int:
    context.emulator.load_save_state((SAVES / "rocksmash_taught.ss1").read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    a = get_player_avatar()
    print(f"PLAYER {MapRSE(tuple(a.map_group_and_number)).name} {tuple(a.local_coordinates)}\n")

    print("0. the script table is DERIVED FROM THE ROM, not recalled")
    # Counted across every RSE map, 2026-07-31: StrengthBoulder 59, RockSmash 44,
    # CutTree 33. Re-counted here so the table cannot drift from the game it describes.
    import collections
    from modules.map import get_map_data

    counts = collections.Counter()
    for member in MapRSE:
        try:
            md = get_map_data(member.value, (0, 0))
        except Exception:  # noqa: BLE001
            continue
        for obj in getattr(md, "objects", ()) or ():
            sym = getattr(obj, "script_symbol", None) or ""
            if sym.startswith("EventScript_") and any(
                k in sym.lower() for k in ("rocksmash", "cuttree", "strength", "boulder")
            ):
                counts[sym] += 1
    print(f"   {dict(counts)}")
    for sym in oc.CLEARABLE_SCRIPTS:
        check(f"actionable symbol {sym} really exists in this ROM", counts.get(sym, 0) > 0,
              f"{counts.get(sym, 0)} objects")
    for sym in oc.KNOWN_BUT_UNSUPPORTED:
        check(f"documented-but-unsupported symbol {sym} really exists too "
              f"(so the note is about a real thing)", counts.get(sym, 0) > 0,
              f"{counts.get(sym, 0)} objects")
    check("no symbol is in both tables",
          not (set(oc.CLEARABLE_SCRIPTS) & set(oc.KNOWN_BUT_UNSUPPORTED)))
    # ‼ Strength must stay OUT: a boulder is PUSHED, not removed, so the "object is gone"
    # success test can never fire. Pin it, or a future session adds it as an easy win.
    check("EventScript_StrengthBoulder is NOT actionable (a boulder is pushed, not removed)",
          "EventScript_StrengthBoulder" not in oc.CLEARABLE_SCRIPTS)

    print("\n1. discovery — the ROM's object events name the rocks")
    found = oc.obstacles_on_map(R111)
    tiles = {t for t, _ in found}
    print(f"   {len(found)} actionable obstacle(s) on ROUTE111: {sorted(tiles)}")
    check("the (18,101) rock is found", (18, 101) in tiles)
    check("the (19,100) rock is found", (19, 100) in tiles)
    check("only ACTIONABLE scripts are returned (the Cut tree at (22,21) is filtered out)",
          all(s in oc.CLEARABLE_SCRIPTS for _, s in found), str({s for _, s in found}))

    print("\n2. planning — it picks a rock it can reach AND clear")
    plan = oc.find_clearable_obstacle(R111, prefer_toward=(18, 60))
    print(f"   plan: {plan.describe() if plan else 'None'}")
    check("a plan is produced", plan is not None)
    if plan:
        # ‼ The corridor runs NORTH from Mauville, so the approach must be from the SOUTH:
        # stand at y+1 and face Up. `early_game` hard-codes the mirror image of this —
        # stage (18,100) facing Down — because it walks the corridor southbound.
        check("it targets the (18,101) rock (the one the story hard-codes)",
              plan.tile == (18, 101), str(plan.tile))
        check("the stand tile is directly SOUTH of the rock", plan.stand_tile == (18, 102),
              str(plan.stand_tile))
        check("...and it faces Up (northbound travel)", plan.face == "Up", plan.face)
        check("the move is Rock Smash", plan.move == "Rock Smash")
        check("the stand tile really is reachable right now",
              oc._reachable(R111, plan.stand_tile))
        check("the rock tile itself is NOT reachable (else there'd be nothing to clear)",
              not oc._reachable(R111, plan.tile))

    print("\n3. the wrong-YES arm — deny the capability, the plan must vanish")
    real = oc._have_capability
    oc._have_capability = lambda move, badge: False
    try:
        denied = oc.find_clearable_obstacle(R111, prefer_toward=(18, 60))
    finally:
        oc._have_capability = real
    check("no plan without the move/badge", denied is None, repr(denied))
    check("...and the plan comes back once the capability does",
          oc.find_clearable_obstacle(R111, prefer_toward=(18, 60)) is not None)

    print("\n4. a map with no clearable obstacles yields no plan")
    check("MAUVILLE_CITY has none", oc.find_clearable_obstacle(tuple(MapRSE.MAUVILLE_CITY.value)) is None)
    check("a bogus map is handled without raising",
          oc.find_clearable_obstacle((99, 99)) is None)

    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
