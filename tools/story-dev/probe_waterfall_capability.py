# -*- coding: utf-8 -*-
"""\u26d4 DOES THE WATERFALL CAPABILITY GAP ACTUALLY BITE A REAL PARTY? (`#24-waterfallcap`)

WHY THIS EXISTS. `#24-waterfallcap` was found by READING code: `_resolve_caps`
(`region_reach.py:228-236`) builds its result by iterating `explicit`, which holds exactly four
keys \u2014 `surf`, `rock_smash`, `cut`, `strength` \u2014 while `:97` gates the only
EVER_GRANDE_CITY \u2194 VICTORY_ROAD_1F edge on `"waterfall"` and `:342` drops any edge whose gate is
missing from `caps`. \u21d2 the edge should be sealed for EVERY party at EVERY badge count.

\u203c READING IS NOT MEASURING, and this project's rule is that a claim code will depend on gets
verified in our own harness. This probe measures it on the real pinned \u00a7Ch24 fixtures.

\u2b50 IT ALSO ANSWERS THE QUESTION THAT GATES THE FIX rather than the diagnosis: **would the capability
resolve TRUE if `_resolve_caps` were taught about it?** `_live_capability("Waterfall")` requires a
party m\u014dn that knows Waterfall AND `BADGE08_GET`. If our \u00a7Ch24 parties carry no Waterfall user then
fixing `_resolve_caps` changes nothing for them and the fix needs a different shape. That was
previously answered by REASONING (*"you cannot reach Ever Grande without Waterfall, so the party
must have one"*) \u2014 exactly the kind of inference this project does not accept as evidence.

\u26d4\u26d4 ON THE CONTROL, AND A MISTAKE THIS PROBE ALREADY MADE ONCE (2026-09-18).
`is_map_reachable` is FAIL-SAFE: it swallows any internal error and returns False. \u21d2 a bare `False`
proves NOTHING on its own \u2014 it is equally consistent with *"the gate is sealed"* and *"the module
threw"*. So a control is mandatory. **My first control was `is_map_reachable(EVER_GRANDE_CITY)`,
and it was WRONG: from a fixture standing INSIDE Victory Road, Ever Grande is gated by the very
edge under test**, so the control sat inside the blast radius and reported a false alarm on a run
that was working perfectly. \u21d2 the control is now **geography-independent**: `reachable_maps()`
returns the origin at distance 0 and `{}` on error, so *"more than one map came back"* proves the
graph built and traversed at least one edge, without my having to guess what is reachable from
where. **Pick a control that cannot be affected by the thing you are testing.**

READ-ONLY: loads save states and reads memory. Nothing is walked, nothing is written.
"""
import pathlib as _pl
import sys

_ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(_ROOT / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

_p = load_profile_by_name("repro-fresh")
context.profile = _p
context.config.load(_p.path, strict=False)
set_rom(_p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_p, lambda: None)
context.audio = False
context.video = False

from modules.map_data import MapRSE
from modules.memory import get_event_flag
from modules.player import get_player_avatar
from modules.pokemon_party import get_party
from modules.story import region_reach

SAVES = _ROOT / "tools" / "story-dev" / "saves"

#: The two maps the `"waterfall"` edge joins. Both directions are read on every fixture, because
#: `_gate_key` (`:158-159`) is symmetric and the OUTBOUND seal is the one that strands a grind.
VR1F = MapRSE.VICTORY_ROAD_1F
EG = MapRSE.EVER_GRANDE_CITY


def _name_of(m) -> str:
    """Readable name for a graph node, which may be a raw (group, number) tuple."""
    try:
        return MapRSE(tuple(m)).name
    except Exception:  # noqa: BLE001 - an unrecognised node is data, not an error
        return str(tuple(m))


#: ⭐ The hop budget `_training_area_allowed` imposes (`story_mode.py:1101`, passed as `max_hops`
#: at `:1269`). An audit called it a SECOND blocker on the Victory Road training row but marked its
#: own hop count INFERRED-STRONG, never measured. ⇒ measure it: VICTORY_ROAD_1F is one edge from
#: EVER_GRANDE_CITY, so `hops(here -> EVER_GRANDE_CITY) + 1` is what the row would have to fit in.
MAX_TRAINING_TRAVEL_LEGS = 4

FIXTURES = ["post_ch24_atdoor_L75.ss1", "post_ch24_atdoor.ss1", "grind_stall_ppzero.ss1",
            "post_league_lobby.ss1"]

print("=" * 108)
print("DOES THE WATERFALL CAPABILITY GAP BITE A REAL PARTY?  \u2014 reading memory only")
print("=" * 108)

rows = []
for fixture in FIXTURES:
    path = SAVES / fixture
    print()
    print(f"\u2500\u2500\u2500 {fixture}")
    if not path.exists():
        print(f"  \u26a0 SKIPPED \u2014 no such fixture: {path}")
        continue
    context.emulator.load_save_state(path.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    avatar = get_player_avatar()
    here = tuple(avatar.map_group_and_number)
    try:
        here_map = MapRSE(here)
        here_name = here_map.name
    except ValueError:
        here_map, here_name = None, str(here)
    print(f"  standing        : {here_name} {tuple(avatar.local_coordinates)}")

    # --- the party, and who knows Waterfall -----------------------------------------------------
    party = get_party()
    knows = [m.species.name for m in party
             if any(lm.move is not None and lm.move.name == "Waterfall" for lm in m.moves)]
    print(f"  party           : {', '.join(f'{m.species.name} L{m.level}' for m in party)}")
    print(f"  knows Waterfall : {knows if knows else '\u26d4 NOBODY'}")
    print(f"  has_pokemon_with_move('Waterfall') = {party.has_pokemon_with_move('Waterfall')}"
          f"     BADGE08_GET = {get_event_flag('BADGE08_GET')}")

    # --- \u26d4 THE CONTROL, geography-independent: did the graph build and traverse anything? -------
    reach = region_reach.reachable_maps()
    live_graph = len(reach) > 1
    print(f"  \u26d4 CONTROL        : reachable_maps() returned {len(reach)} map(s) \u2192 "
          f"{'\u2705 graph is LIVE' if live_graph else '\u26d4 GRAPH IS DEAD (fail-safe empty)'}")
    # \u2b50 When the world collapses to a handful of maps, NAME them. The SIZE of the reachable set is
    # the real measure of this bug's blast radius, and "3" means nothing without the three names.
    if len(reach) <= 12:
        print(f"     \u203c THE WHOLE KNOWN WORLD FROM HERE: {sorted(_name_of(m) for m in reach)}")

    # --- what the FIX would produce -------------------------------------------------------------
    live_cap = region_reach._live_capability("Waterfall")
    print(f"  \u2b50 _live_capability('Waterfall') = {live_cap}   <- what a fixed `_resolve_caps` would use")

    # --- BOTH directions of the gated edge ------------------------------------------------------
    to_vr = region_reach.is_map_reachable(VR1F)
    to_eg = region_reach.is_map_reachable(EG)
    print(f"  is_map_reachable({VR1F.name}) = {to_vr}")
    print(f"  is_map_reachable({EG.name}) = {to_eg}")
    for label, target in (("-> VICTORY_ROAD_1F", VR1F), ("-> EVER_GRANDE_CITY", EG)):
        try:
            print(f"  why_unreachable {label:<20}: {region_reach.why_unreachable(target)}")
        except Exception as error:  # noqa: BLE001 - a failed read IS the reading
            print(f"  why_unreachable {label:<20}: <raised {type(error).__name__}: {error}>")

    # --- ⭐ THE HOP BUDGET, measured rather than inferred ----------------------------------------
    # `_training_area_allowed` requires the area be within `_MAX_TRAINING_TRAVEL_LEGS` hops. The
    # Victory Road row can only ever be accepted if VICTORY_ROAD_1F fits in that budget FROM HERE.
    # It is exactly one edge past EVER_GRANDE_CITY, so measure the distance to Ever Grande and add 1.
    dist = region_reach.reachable_map_distances()
    eg_hops = dist.get(tuple(EG.value), dist.get(EG, None))
    if eg_hops is None:
        would_be = None
        print(f"  ⭐ hops -> EVER_GRANDE_CITY : ⛔ unreachable (the sealed edge) — cannot derive")
    else:
        would_be = 0 if here == tuple(VR1F.value) else eg_hops + 1
        verdict = ("✅ FITS" if would_be <= MAX_TRAINING_TRAVEL_LEGS else "⛔ EXCEEDS")
        print(f"  ⭐ hops -> EVER_GRANDE_CITY : {eg_hops}   ⇒ VICTORY_ROAD_1F would be "
              f"{would_be} hop(s) once the gate opens, vs budget {MAX_TRAINING_TRAVEL_LEGS} "
              f"-> {verdict}")

    rows.append({"fixture": fixture, "here": here_name, "live_graph": live_graph,
                 "live_cap": live_cap, "to_vr": to_vr, "to_eg": to_eg,
                 "would_be_hops": would_be,
                 "inside_vr": here == tuple(VR1F.value)})

print()
print("=" * 108)
if not rows:
    print("  \u26d4 NO FIXTURE WAS READ \u2014 this run measured nothing.")
    raise SystemExit(1)

# \u26d4 CONTROL GATE FIRST. Without it, a False anywhere below is unreadable.
dead = [r["fixture"] for r in rows if not r["live_graph"]]
if dead:
    print(f"  \u26d4\u26d4 CONTROL FAILED on {dead} \u2014 `reachable_maps()` came back with <=1 map, which is its "
          f"fail-safe empty result. The module is erroring. \u21d2 **EVERY READING IN THIS RUN IS VOID**, "
          f"including any that appear to confirm the bug.")
    raise SystemExit(1)
print(f"  \u2705 CONTROL HOLDS on all {len(rows)} fixture(s): the graph built and traversed edges.")
print("     \u21d2 a False below is a REAL seal, not a swallowed error.")
print()

# --- the diagnosis ------------------------------------------------------------------------------
outside = [r for r in rows if not r["inside_vr"]]
inside = [r for r in rows if r["inside_vr"]]

if outside:
    blocked = [r["fixture"] for r in outside if not r["to_vr"]]
    armed = [r["fixture"] for r in outside if r["live_cap"]]
    print(f"  \u2b50 INBOUND (standing OUTSIDE Victory Road): VICTORY_ROAD_1F is UNREACHABLE on "
          f"{len(blocked)}/{len(outside)} fixture(s) \u2014 {blocked}")
    if armed:
        print(f"  \u26d4\u26d4 AND THE PARTY ACTUALLY HAS THE CAPABILITY: `_live_capability('Waterfall')` is "
              f"TRUE on {armed}. \u21d2 the refusal is NOT \u201cthis party cannot Waterfall\u201d \u2014 it is "
              f"`_resolve_caps` never asking. **THE BUG IS CONFIRMED BY MEASUREMENT, not by reading.**")

if inside:
    stranded = [r["fixture"] for r in inside if not r["to_eg"]]
    if stranded:
        print(f"  \u26d4\u26d4 OUTBOUND, AND THIS IS THE HALF THAT MATTERS FOR \u00a7Ch24: standing INSIDE Victory "
              f"Road, EVER_GRANDE_CITY reads UNREACHABLE on {stranded}. `_gate_key` is symmetric, so "
              f"the seal closes BOTH ways.")
        print(f"     \u21d2 a grind parked at `TRAIN_SPOT_1F` is told the map holding its POK\u00c9 CENTER "
              f"cannot be reached. \u2705 The `ch24caveheal` drive MEASURED that it CAN walk out \u2014 via "
              f"`navigate_to_anywhere`, which does not consult this graph. \u203c So the two instruments "
              f"DISAGREE, and any future code that gates the heal on `is_map_reachable` would break "
              f"a route that demonstrably works.")

print()
# --- \u2b50 the hop-budget verdict -------------------------------------------------------------------
hops = [(r["fixture"], r["would_be_hops"]) for r in rows if r["would_be_hops"] is not None]
if hops:
    worst = max(h for _f, h in hops)
    print(f"  \u2b50 HOP BUDGET (`_MAX_TRAINING_TRAVEL_LEGS = {MAX_TRAINING_TRAVEL_LEGS}`): once the "
          f"gate opens, VICTORY_ROAD_1F would sit at {dict(hops)} hop(s).")
    if worst <= MAX_TRAINING_TRAVEL_LEGS:
        print(f"     \u2705 WORST CASE {worst} <= {MAX_TRAINING_TRAVEL_LEGS} \u2192 the hop budget is NOT a "
              f"blocker for this row from any position measured here. \u203c An audit called it a second "
              f"blocker on an INFERRED hop count; measured, it is not one \u2014 for THESE positions.")
    else:
        print(f"     \u26d4 WORST CASE {worst} > {MAX_TRAINING_TRAVEL_LEGS} \u2192 the hop budget IS a second "
              f"blocker: fixing the capability alone would still leave the row refused from there.")
    print(f"     \u26a0 SCOPE: this is measured only from the fixtures above. A training decision taken "
          f"somewhere farther from Ever Grande could still exceed the budget.")

print()
print("  \u203c WHAT THIS PROBE DOES NOT SHOW: that the bot can WALK an opened edge. Reachability is a")
print("    MAP-granularity graph answer; `story_mode.py:1213` already records that it says YES for")
print("    maps whose specific TILE is not reachable. A drive is still the only proof of traversal.")
print("=" * 108)
