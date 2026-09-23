# -*- coding: utf-8 -*-
"""⭐ CAN THE BOT WALK THE LAST MILE FROM EACH FLY LANDING TO EACH SPIN TILE? (`#24-flyladder`)

WHY NOW. The per-trainee Fly ladder needs six last miles: land in a town, walk to the ground's spin
tile. ✅ Already measured (`probe_fly_unlocked.py`): every anchor town is UNLOCKED, and — per-fixture
— two of the three pinned saves can actually fly. ⇒ the remaining question is the WALK.

⭐ AND IT IS COMPUTABLE WITHOUT FLYING, because `calculate_path(source, destination, ...)` takes an
**explicit source** (`modules/map_path.py:724`). So every last mile can be asked for statically.

════════════════════════════════════════════════════════════════════════════════════════════════
‼ THIS PROBE WAS REWRITTEN 2026-09-23 AFTER ITS FIRST VERSION REPORTED 5/6 PASS ON THREE FAULTS.
Recording them here because each is a way a green tick can mean nothing, and all three were mine:

 ⛔ (1) THE ORIGIN WAS A PROXY — AND IT DID NOT HAVE TO BE. v1 used each town's `PokemonCenter`
    DOOR tile, and said in its own docstring that the true Fly landing "is not recorded anywhere in
    this repo". **That was false.** The landings are in the decomp's heal-location table, and every
    one of the six is exactly `door + (0, +1)` — verified 2026-09-23 against
    `pret/pokeemerald:src/data/heal_locations.json` for all six anchors, zero mismatches.
    ‼ The repo had ALREADY encoded this: `victory_road.py:147-148` derives `EG_PC_APRON` as
    `(x, y + 1)` from the Poké Center's own tile. ⇒ the fact was in the tree and I used a proxy.

 ⛔⛔ (2) THE DOOR TILE IS A **WARP**, SO IT IS ACTIVELY WRONG AS AN ORIGIN, NOT MERELY IMPRECISE.
    `calculate_path` FOLLOWS a warp when one is used as an endpoint. A leg computed from the door
    can therefore resolve THROUGH the Poké Center entrance rather than across the town. The apron
    tile below it is ordinary ground and is where Fly actually deposits the player.

 ⛔⛔ (3) THE PASSES COULD NOT BE TOLD APART FROM "THE PLANNER SWAM THERE." v1 called
    `calculate_path` without `no_surfing`, whose default is **`no_surfing=False`**
    (`map_path.py:728`), against a party that HOLDS Surf. ⇒ a PASS meant "walkable **or** swimmable",
    which is not the question — the bot lands on foot and Surf costs a menu, a mount and a different
    encounter table. **A control that cannot fail differently from the treatment is not a control.**
════════════════════════════════════════════════════════════════════════════════════════════════

WHAT THIS RUN MEASURES PER RUNG — four readings, so a PASS says which KIND of pass it is:
  A. `no_surfing=False` — the permissive arm. Waypoints, or NO PATH.
  B. `no_surfing=True`  — ⭐ THE DECISIVE ARM. This is what a bot on foot can actually do.
  C. a census of WATER tiles and `WaypointAction.Surf` steps on arm A's path — so "it swam" is
     visible as a number, not an inference.
  D. a census of ARMED on-enter script triggers crossed on arm B's path
     (`tile.on_enter_event_triggers` vs `get_event_var_by_number`, the exact test
     `map_path.py:1034-1037` applies). ‼ `avoid_scripted_events` adds `cost += 10000` — a PENALTY,
     NOT A WALL — so a path may cross one anyway, and the walker would fire it.

⛔⛔ WHAT NO ARM HERE CAN SEE — TRAINER SIGHT CONES. `avoid_scripted_events` consults ONLY
`on_enter_event_triggers`; spotting is a per-frame scan in the decomp's `trainer_see.c`. The
pathfinder is **structurally blind** to it — `victory_road.py:2765-2770` says so and hardcodes a
bypass waypoint to work around it. ⇒ a clean result here does NOT mean the walk is battle-free, and
these five routes are trainer country. Tracked separately; do not let a green column imply it.

⚠ AND THE STANDING LIMIT: `calculate_path` cannot use warps or Fly. A route needing a door is
reported unreachable though a human walks it — a property of the instrument, not of the map.

READ-ONLY: loads one save state for ROM context, then computes paths. Nothing is walked or written.
"""
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

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

from modules.map import get_map_data
from modules.map_data import MapRSE, PokemonCenter
from modules.map_path import PathFindingError, WaypointAction, calculate_path
from modules.memory import get_event_var_by_number

SAVES = _ROOT / "tools" / "story-dev" / "saves"
#: A late-game save, so any story-gated obstacle is already cleared. The PARTY matters for exactly
#: one thing — `calculate_path` reads it to decide whether Surf is available — which is why arm B
#: pins `no_surfing=True` rather than trusting the fixture to lack a surfer.
FIXTURE = "post_ch24_atdoor_L75.ss1"


def _landing(center: PokemonCenter) -> tuple:
    """The tile Fly actually deposits the player on: the Poké Center door, one row SOUTH.

    ⛔ NOT the door itself — that is a WARP, and `calculate_path` follows a warp used as an
    endpoint, so a leg computed from it can resolve inside the building.
    ✅ VERIFIED 2026-09-23 for all six anchors against the decomp's heal-location table
    (`pret/pokeemerald:src/data/heal_locations.json`): every landing is exactly door + (0, +1),
    6/6, zero mismatches. Same derivation the repo already uses at `victory_road.py:147-148`.
    """
    src_map, src_tile = center.value
    x, y = tuple(src_tile)
    return src_map, (x, y + 1)


#: rung, ground, spin tile, anchor Poké Center. Origins are DERIVED by `_landing`, not hardcoded,
#: so this table cannot drift out of step with `map_data.py`.
LADDER = [
    ("L15-20", MapRSE.ROUTE117, (31, 16), PokemonCenter.VerdanturfTown),
    ("L21-24", MapRSE.ROUTE111, (25, 55), PokemonCenter.FallarborTown),
    ("L25-26", MapRSE.ROUTE115, (6, 53), PokemonCenter.RustboroCity),
    ("L27", MapRSE.ROUTE118, (29, 15), PokemonCenter.MauvilleCity),
    ("L28-38", MapRSE.ROUTE121, (44, 14), PokemonCenter.LilycoveCity),
    ("L39-75", MapRSE.VICTORY_ROAD_1F, (15, 39), PokemonCenter.EvergrandeCity),
]

print("=" * 112)
print("THE LAST MILE: real Fly landing → spin tile, measured BOTH with and without Surf")
print("=" * 112)

path = SAVES / FIXTURE
if not path.exists():
    raise SystemExit(f"⛔ MISSING FIXTURE: {path}")
context.emulator.load_save_state(path.read_bytes())
for _ in range(40):
    context.emulator.run_single_frame()
print(f"  ROM context from: {FIXTURE}")
print("  origins = Poké Center door + (0,+1)  [decomp heal-location table, 6/6 verified]")
print("  ⛔ blind spot this cannot see: TRAINER SIGHT CONES — see the module docstring.")
print()


def _water_census(waypoints) -> tuple:
    """(water tiles, Surf-action steps) on a computed path — so 'it swam' is a number, not a guess."""
    water = sum(1 for w in waypoints if w.is_water_tile)
    surfs = sum(1 for w in waypoints if w.action is WaypointAction.Surf)
    return water, surfs


_ARMED_CACHE: dict = {}


def _armed_triggers(map_gan: tuple) -> dict:
    """{(x, y): var_number} for every ARMED, PENALISED coord event on a map.

    ⛔⛔ THIS FUNCTION IS THE SECOND VERSION. THE FIRST ONE COULD NOT FIRE, AND SAID NOTHING WHILE
    FAILING. It did `get_map_data(...).on_enter_event_triggers` — but that attribute does NOT
    belong to `MapLocation`. It is a field of the PATHFINDER's own node type (`map_path.py:66`,
    populated at `:381-385`). So every lookup raised `AttributeError`, a bare `except: continue`
    swallowed all of them, and the census reported a clean sheet on five maps — including ROUTE110,
    which is dense with scripted events. ⇒ **a silent zero from a broken instrument is
    indistinguishable from a real zero**, which is precisely how `#24-pcoverflow`'s
    `getattr(..., lambda: [])` hid a dead `box_views()` for weeks. Defensive `except` around a
    reading is how a probe lies.
    ✅ VACUITY-TESTED after the fix: ROUTE111 reports 34 armed, ROUTE117/ROUTE115 report 0. A census
    that returns a non-zero somewhere has demonstrated it can count.

    ‼ AND THE FILTER IS THE PLANNER'S, NOT MINE: `map_path.py:113` builds its trigger table from
    `map_data.coord_events` while **excluding `type == "weather"`**. ⇒ weather coord events are
    invisible to `avoid_scripted_events` BY DESIGN and are reported here separately rather than
    counted as crossings — ROUTE113 is 19 weather events and zero penalised ones.

    ‼ `avoid_scripted_events` is a `cost += 10000` PENALTY, not a wall: when the cheapest route
    crosses a trigger anyway the planner returns it, and a walker would FIRE the script.
    """
    key = tuple(map_gan)
    if key in _ARMED_CACHE:
        return _ARMED_CACHE[key]
    out = {}
    try:
        for event in get_map_data(key, (0, 0)).coord_events:
            if event.type == "weather":
                continue
            var = event.trigger_var_number
            if get_event_var_by_number(var) == event.trigger_value:
                # ⛔⛔ A NEGATIVE VAR NUMBER IS A PHANTOM, NOT AN ARMED TRIGGER — AND THE PRODUCTION
                # PLANNER IS FOOLED BY IT TOO. `MapCoordEvent.trigger_var_number` is
                # `uint16 - 0x4000` (`map.py:605-607`), so a `TRIGGER_RUN_IMMEDIATELY` (== 0) event
                # yields **-16384**. `get_event_var_by_number` then computes
                # `vars_offset + var_number * 2` with NO guard (`memory.py:400-408`) — for Emerald
                # that is `0x139C - 32768`, a NEGATIVE save-block offset. MEASURED 2026-09-23: it
                # raises nothing and returns **0**, which equals the event's `trigger_value` of 0,
                # so the tile reads ARMED. ⇒ on ROUTE111, 24 of 34 coord events are these ambient
                # sandstorm/sun tiles and `map_path.py:1034-1037` adds **+10000 to every one of
                # them**. Tracked as `#24-phantomtrigger`.
                out[tuple(event.local_coordinates)] = ("phantom" if var < 0 else "real", var)
    except Exception as error:  # noqa: BLE001
        # ⛔ NOT silent. A census that cannot read its own source must SAY so, because the caller
        # cannot tell "no triggers" from "no readings" once this returns {}.
        print(f"      ⚠ trigger census could not read {key}: {type(error).__name__}: {error}")
    _ARMED_CACHE[key] = out
    return out


def _trigger_census(waypoints) -> list:
    """Armed, penalised trigger tiles the given path actually STEPS ON."""
    hits = []
    for w in waypoints:
        armed = _armed_triggers(w.map)
        if tuple(w.coordinates) in armed:
            hits.append((w.map, tuple(w.coordinates), armed[tuple(w.coordinates)]))
    return hits


def _maps_crossed(waypoints) -> str:
    maps = []
    for w in waypoints:
        nm = tuple(w.map)
        if not maps or maps[-1] != nm:
            maps.append(nm)
    out = " -> ".join(MapRSE(m).name for m in maps[:4])
    return out + (" -> ..." if len(maps) > 4 else "")


def _try(src, dst, *, no_surfing: bool):
    try:
        return calculate_path(src, dst, no_surfing=no_surfing), None
    except PathFindingError as error:
        return None, f"NO PATH: {str(error)[:70]}"
    except Exception as error:  # noqa: BLE001 - any other failure IS the reading
        return None, f"{type(error).__name__}: {str(error)[:60]}"


rows = []
for rung, ground, tile, center in LADDER:
    src = _landing(center)
    dst = (ground, tuple(tile))
    swim_wp, swim_err = _try(src, dst, no_surfing=False)
    walk_wp, walk_err = _try(src, dst, no_surfing=True)

    print(f"─── {rung:<8} {ground.name} {tuple(tile)}")
    print(f"      from {MapRSE(tuple(src[0].value) if hasattr(src[0], 'value') else src[0]).name}"
          f"{src[1]}  (Fly landing)")

    if swim_wp is not None:
        water, surfs = _water_census(swim_wp)
        note = f"  ⚠ {water} water tile(s), {surfs} Surf step(s)" if water or surfs else "  (dry)"
        print(f"      A. surf allowed : ✅ {len(swim_wp):>4} wp{note}")
        print(f"                        via {_maps_crossed(swim_wp)}")
    else:
        print(f"      A. surf allowed : ⛔ {swim_err}")

    if walk_wp is not None:
        trig = _trigger_census(walk_wp)
        print(f"      B. WALKING ONLY : ✅ {len(walk_wp):>4} wp   ⭐ this is the real reading")
        # ⛔ ALWAYS PRINT THE DENOMINATOR. "0 crossed" is only informative next to "N exist on the
        # maps this path traverses" — without it, a broken census and a clean route look identical,
        # which is exactly how v1 of this reading passed while being incapable of counting.
        crossed_maps, seen = [], set()
        for w in walk_wp:
            k = tuple(w.map)
            if k not in seen:
                seen.add(k)
                crossed_maps.append(k)
        pool_real = sum(sum(1 for k2 in _armed_triggers(k).values() if k2[0] == "real")
                        for k in crossed_maps)
        pool_ph = sum(sum(1 for k2 in _armed_triggers(k).values() if k2[0] == "phantom")
                      for k in crossed_maps)
        real_hits = [h for h in trig if h[2][0] == "real"]
        ph_hits = [h for h in trig if h[2][0] == "phantom"]
        if real_hits:
            print(f"      D. ⚠ crosses {len(real_hits)} of {pool_real} REAL armed trigger(s) —"
                  f" a walker FIRES these:")
            for m, c, (_kind, var) in real_hits[:4]:
                print(f"           {MapRSE(tuple(m)).name} {c}  var #{var}")
            if len(real_hits) > 4:
                print(f"           … and {len(real_hits) - 4} more")
        else:
            print(f"      D. ✅ crosses 0 of {pool_real} REAL armed trigger(s) on its maps")
        if ph_hits or pool_ph:
            print(f"      D'. ⛔ {len(ph_hits)} of {pool_ph} PHANTOM trigger(s) crossed "
                  f"(`#24-phantomtrigger`) — negative var number, read from a negative save-block")
            print("           offset that silently returns 0. Harmless to WALK, but `calculate_path`")
            print("           still pays +10000 for each — the COST FUNCTION is wrong here.")
            print("           ⚠ Whether any returned ROUTE from this distortion actually differs is")
            print("             NOT measured; a +10000 penalty is survivable when nothing cheaper")
            print("             exists. Do not read this as a cause of ROUTE111's failure rate.")
    else:
        print(f"      B. WALKING ONLY : ⛔ {walk_err}")

    # ⭐ THE DISCRIMINATOR v1 COULD NOT COMPUTE: a rung that passes ONLY with Surf is a rung the
    # bot cannot walk, and v1 would have printed it as a plain green tick.
    if swim_wp is not None and walk_wp is None:
        print("      ⛔⛔ SURF-ONLY RUNG — arm A passed and arm B did not. v1 reported this shape")
        print("          as a PASS. The bot lands on foot; this last mile is NOT walkable.")
    print()
    rows.append((rung, ground.name, swim_wp, walk_wp, walk_err))

print("=" * 112)
walkable = [r for r in rows if r[3] is not None]
surf_only = [r for r in rows if r[2] is not None and r[3] is None]
dead = [r for r in rows if r[2] is None and r[3] is None]

print(f"  WALKABLE ON FOOT (arm B): {len(walkable)}/{len(LADDER)}")
for rung, name, _sw, wk, _e in walkable:
    print(f"     ✅ {rung:<9} {name:<18} {len(wk)} wp")
if surf_only:
    print()
    print(f"  ⛔⛔ SURF-ONLY — {len(surf_only)} rung(s) pass only when swimming is permitted:")
    for rung, name, sw, _wk, err in surf_only:
        print(f"     {rung:<9} {name:<18} surf {len(sw)} wp / walking {err}")
    print("     ⇒ the bot arrives on foot. Either the leg must mount Surf deliberately, or the")
    print("       rung needs a different anchor. Do NOT count these as walkable last miles.")
if dead:
    print()
    print(f"  ⛔ NO PATH IN EITHER ARM — {len(dead)} rung(s):")
    for rung, name, _sw, _wk, err in dead:
        print(f"     {rung:<9} {name:<18} {err}")
    print("     ⇒ EACH NEEDS A REASON BEFORE ITS LEG IS BUILT. Two innocent explanations exist and")
    print("       must be told apart: (a) the route crosses a WARP, which this instrument cannot")
    print("       use and `navigate_to_anywhere` CAN; or (b) the ground is genuinely cut off.")
    print("     ⛔ Do NOT assume (a). VICTORY_ROAD_1F is the known warp case (its entrance is a door")
    print("       warp, `victory_road.py:132`, and the `ch24caveheal` drive walked it both ways).")
    print("       The others are not, and would be real holes in the ladder.")
print()
print("  ‼ REMAINING BLIND SPOT, STATED SO NO GREEN COLUMN IMPLIES IT AWAY: trainer sight cones.")
print("    The planner cannot see them; these routes are full of them; a clean walk here is not a")
print("    battle-free walk. That is a separate measurement, not a caveat to wave at.")
print("=" * 112)
