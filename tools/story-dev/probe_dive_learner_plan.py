"""§Ch21 UNBLOCK — MEASURE whether a DIVE-learner hunt is possible at all on `post_dive.ss1`.

‼ WHY THIS EXISTS. §Ch21 needs a party member that KNOWS Dive. HM08 is already in the bag, so the
plan reads "free a slot, walk to a hunting ground, catch a learner". Every word of that rests on
facts nobody has MEASURED:

  1. **BALLS.** Punch-list `#24-ballstarve` says "Cannot hunt a Surf learner: no Poké Balls". If the
     bag really is empty, the hunt cannot even start — so this probe counts the POKE_BALLS pocket
     and the wallet FIRST, and prices a mart trip when the count is zero.
  2. **THE GROUND.** Docs claim `_hm_hunting_grounds(HM08)` returns `(ROUTE117, (31,16), ['Marill'])`.
     This probe CALLS THE REAL FUNCTION instead of quoting the doc, because `_hm_hunting_grounds`
     is data-driven off `TRAINING_GRASS` x ROM encounter tables and either input can have moved.
  3. **THE SPECIES.** "Can learn Dive" must come from `modules/data`'s per-species TM/HM learnset,
     not from memory — and the encounter SLOT RATE and LEVEL BAND decide whether the hunt is a
     five-minute spin or an hour.
  4. **THE ALTERNATIVE.** The docs record Spheal in SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM at ~50% of the
     LAND table, L26-32, catch rate 255. Verified here from the same ROM tables, side by side.
  5. **THE VICTIM.** `find_dead_weight` must not choose Zigzagoon L15 — our ONLY Surf carrier, and
     Surf is how the bot reaches any of this.
  6. **REACHABILITY.** A ground we cannot walk to is not a ground. `calculate_path` is asked, and
     the exact exception is printed when it says no.

‼ POSITIVE CONTROLS ARE BUILT IN so a null result is ATTRIBUTABLE. Every "zero / none / False" in
this probe sits next to a control that must come back non-null:
  * bag reader        -> the ITEMS + TMS pockets are printed; if those are non-empty, "0 balls" is
                         a real empty ball pocket and not a broken reader.
  * learnset reader   -> Zigzagoon (a known NON-learner of Dive) and Wailmer (a known learner) are
                         checked alongside the candidates.
  * encounter reader  -> ROUTE117's land table is dumped; a non-empty table proves the reader works
                         even if some other map returns None.
  * pathfinder        -> a short intra-Mossdeep hop must PATH; if the control fails, every other
                         PathFindingError in section 6 is uninterpretable and is labelled as such.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dive_learner_plan.py
      PYTHONUTF8=1 py -3.12 probe_dive_learner_plan.py --anchor post_dive.ss1
"""

import argparse
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

parser = argparse.ArgumentParser()
parser.add_argument("--anchor", default="post_dive.ss1")
args = parser.parse_args()

ANCHOR = REPO / "tools" / "story-dev" / "saves" / args.anchor
context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(4):
    context.emulator.run_single_frame()

from modules.items import get_item_bag, get_item_by_name
from modules.map import get_wild_encounters_for_map
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.player import get_player, get_player_avatar
from modules.pokemon import get_species_by_name
from modules.pokemon_party import get_party
from modules.story import team_policy
from modules.story.early_game import (
    POKE_BALL_PRICE,
    MONEY_RESERVE,
    _hm_hunting_grounds,
    _total_poke_balls,
    affordable_poke_balls,
    hm_learner_slot,
)

BAR = "=" * 100


def head(title):
    print(f"\n{BAR}\n{title}\n{BAR}\n")


avatar = get_player_avatar()
HERE = (tuple(avatar.map_group_and_number), tuple(avatar.local_coordinates))
print(f"anchor: {args.anchor}")
print(f"avatar: {MapRSE(tuple(avatar.map_group_and_number)).name} "
      f"{tuple(avatar.local_coordinates)}   (‼ asserted, not assumed — KI-60)")

party = get_party()
print(f"\nparty ({len([m for m in party if m is not None])}/6):")
for index, mon in enumerate(party):
    if mon is None:
        continue
    moves = ", ".join(m.move.name for m in mon.moves if m is not None)
    print(f"  {index}  {mon.species.name:<11} L{mon.level:<3} {mon.current_hp}/{mon.total_hp:<4} {moves}")

# =============================================================================================
head("1 — ‼ POKE BALL INVENTORY AND MONEY (the #24-ballstarve question: is a hunt possible AT ALL?)")

bag = get_item_bag()
balls = bag.poke_balls
print("  POKE_BALLS pocket:")
if not balls:
    print("    (EMPTY — zero balls of any kind)")
for slot in balls:
    print(f"    {slot.item.name:<16} x{slot.quantity:<3}  (mart price {slot.item.price})")
total_balls = sum(s.quantity for s in balls)
print(f"\n  TOTAL BALLS          : {total_balls}   (`_total_poke_balls()` says {_total_poke_balls()})")

money = get_player().money
print(f"  MONEY                : ${money}")
print(f"  affordable_poke_balls(): {affordable_poke_balls()}  "
      f"(= (money - reserve {MONEY_RESERVE}) // price {POKE_BALL_PRICE})")

print("\n  ‼ POSITIVE CONTROL for the bag reader — other pockets must be NON-empty, otherwise a")
print("    zero ball count would be indistinguishable from an unreadable bag:")
for label, pocket in (("items", bag.items), ("key_items", bag.key_items),
                      ("tms_hms", bag.tms_hms), ("berries", bag.berries)):
    sample = ", ".join(f"{s.item.name} x{s.quantity}" for s in pocket[:5])
    print(f"    {label:<10} {len(pocket):>3} slot(s)   {sample}{' …' if len(pocket) > 5 else ''}")
control_bag_ok = bool(bag.items or bag.key_items or bag.tms_hms)
print(f"    [{'CONTROL PASS' if control_bag_ok else '‼ CONTROL FAIL'}] bag reader returns data: {control_bag_ok}")

print("\n  MART TRIP PRICING (a hunt needs balls; how much would stocking up cost?):")
for count in (1, 5, 10, 20, 30):
    cost = count * POKE_BALL_PRICE
    verdict = "AFFORDABLE" if money - cost >= MONEY_RESERVE else "‼ would breach the $500 reserve"
    if cost > money:
        verdict = "‼ CANNOT AFFORD"
    print(f"    {count:>2} Poke Balls = ${cost:<6} -> {verdict}")
print(f"\n  [{'BALLS PRESENT' if total_balls else '‼ ZERO BALLS'}] "
      f"{'a hunt can spend a ball today' if total_balls else 'a hunt is IMPOSSIBLE without a mart trip first'}")

# =============================================================================================
head("2 — WHAT DOES `_hm_hunting_grounds` ACTUALLY RETURN FOR DIVE? (the real call, not the doc)")

hm08 = get_item_by_name("HM08")
hm03 = get_item_by_name("HM03")
print(f"  HM08 -> move           : {hm08.tm_hm_move().name}   (‼ confirms HM08 IS Dive on this ROM)")
print(f"  HM03 -> move           : {hm03.tm_hm_move().name}")
print(f"  HM08 in bag            : {bag.quantity_of(hm08)}")
print(f"  hm_learner_slot(HM08)  : {hm_learner_slot(hm08)}   (None = nobody in the party can learn Dive)")

grounds = _hm_hunting_grounds(hm08)
print(f"\n  _hm_hunting_grounds(HM08) -> {len(grounds)} ground(s):")
if not grounds:
    print("    (NONE — no TRAINING_GRASS entry's LAND table hosts a Dive learner)")
for map_enum, tile, names in grounds:
    print(f"    {map_enum.name:<28} tile {tile}   {names}")

print("\n  ‼ CONTROL — the same function for SURF (HM03), which is known to return grounds. If this")
print("    is non-empty while Dive is empty, an empty Dive result is a REAL fact about learnsets,")
print("    not a broken lookup:")
surf_grounds = _hm_hunting_grounds(hm03)
print(f"    _hm_hunting_grounds(HM03) -> {len(surf_grounds)} ground(s)")
for map_enum, tile, names in surf_grounds:
    print(f"      {map_enum.name:<28} tile {tile}   {names}")

# =============================================================================================
head("3 — DO THE NAMED SPECIES GENUINELY LEARN DIVE? (from modules/data learnsets, plus SURF)")


def learn_report(species_name):
    """(learns_dive, learns_surf, level_up_dive_or_surf, catch_rate) straight from the ROM data."""
    species = get_species_by_name(species_name)
    dive = species.can_learn_tm_hm(hm08)
    surf = species.can_learn_tm_hm(hm03)
    lvlups = [f"{e.move.name}@L{e.level}" for e in species.learnset.level_up
              if e.move.name in ("Dive", "Surf")]
    return species, dive, surf, lvlups


candidate_names = []
for _map_enum, _tile, names in grounds:
    for name in names:
        if name not in candidate_names:
            candidate_names.append(name)
# The documented alternative + the controls.
for extra in ("Spheal", "Marill", "Wailmer", "Zigzagoon"):
    if extra not in candidate_names:
        candidate_names.append(extra)

print(f"  {'species':<12} {'DIVE?':<7} {'SURF?':<7} {'catch rate':<11} level-up Dive/Surf")
for name in candidate_names:
    try:
        species, dive, surf, lvlups = learn_report(name)
    except Exception as error:  # noqa: BLE001 - an unreadable species is reported, never assumed
        print(f"  {name:<12} <could not read: {type(error).__name__}: {error}>")
        continue
    print(f"  {name:<12} {str(dive):<7} {str(surf):<7} {species.catch_rate:<11} {lvlups or '-'}")

print("\n  ‼ CONTROLS — Wailmer is a KNOWN Dive learner and Zigzagoon a KNOWN non-learner. If the")
print("     column above reads True for Wailmer and False for Zigzagoon, the learnset reader is")
print("     discriminating and a False for any candidate is a real fact.")
try:
    ctl_ok = (get_species_by_name("Wailmer").can_learn_tm_hm(hm08)
              and not get_species_by_name("Zigzagoon").can_learn_tm_hm(hm08))
except Exception as error:  # noqa: BLE001
    ctl_ok = False
    print(f"     <control could not run: {type(error).__name__}: {error}>")
print(f"     [{'CONTROL PASS' if ctl_ok else '‼ CONTROL FAIL'}] learnset reader discriminates: {ctl_ok}")

# =============================================================================================
head("4 — ENCOUNTER TABLES: the named ground vs. the documented SHOAL CAVE alternative")


def dump_table(map_enum, note=""):
    """Print the LAND table of `map_enum`, aggregated per species. Returns the aggregate dict."""
    print(f"  {map_enum.name}  {note}")
    try:
        enc = get_wild_encounters_for_map(*map_enum.value)
    except Exception as error:  # noqa: BLE001 - unreadable is reported, never assumed empty
        print(f"    <could not read encounters: {type(error).__name__}: {error}>")
        return None
    if enc is None:
        print("    <no encounter data for this map (get_wild_encounters_for_map returned None)>")
        return None
    print(f"    base rates: land={enc.land_encounter_rate} surf={enc.surf_encounter_rate} "
          f"rock_smash={enc.rock_smash_encounter_rate} fishing={enc.fishing_encounter_rate}")
    aggregate = {}
    for entry in enc.land_encounters:
        if entry.species is None:
            continue
        row = aggregate.setdefault(entry.species.name,
                                   {"rate": 0, "lo": entry.min_level, "hi": entry.max_level,
                                    "species": entry.species})
        row["rate"] += entry.encounter_rate
        row["lo"] = min(row["lo"], entry.min_level)
        row["hi"] = max(row["hi"], entry.max_level)
    if not aggregate:
        print("    <LAND table is EMPTY — this map has no land encounters>")
    for name, row in sorted(aggregate.items(), key=lambda kv: -kv[1]["rate"]):
        species = row["species"]
        print(f"    {name:<12} {row['rate']:>3}% of the LAND table   L{row['lo']}-{row['hi']:<3} "
              f"catch_rate {species.catch_rate:<4} Dive={species.can_learn_tm_hm(hm08)} "
              f"Surf={species.can_learn_tm_hm(hm03)}")
    return aggregate


named_maps = [map_enum for map_enum, _tile, _names in grounds]
if not named_maps:
    print("  (no ground was named in section 2 — nothing to dump here)")
for map_enum in named_maps:
    dump_table(map_enum, "(named by `_hm_hunting_grounds(HM08)`)")
    print()

print("  ‼ CONTROL — ROUTE117 (the doc's claimed ground) is dumped unconditionally, so an empty")
print("    table anywhere else is attributable to that map and not to a broken reader:")
route117 = dump_table(MapRSE.ROUTE117, "(unconditional control dump)")
print(f"    [{'CONTROL PASS' if route117 else '‼ CONTROL FAIL'}] encounter reader returns data: {bool(route117)}")

print("\n  THE DOCUMENTED ALTERNATIVE — claim: Spheal ~50% of the LAND table, L26-32, catch rate 255:")
shoal = dump_table(MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM, "(the doc's Spheal ground)")
if shoal:
    spheal = shoal.get("Spheal")
    if spheal is None:
        print("\n    ‼ CLAIM REFUTED: Spheal does NOT appear in this map's LAND table.")
    else:
        print(f"\n    CLAIM CHECK: rate {spheal['rate']}% (claimed ~50), levels L{spheal['lo']}-{spheal['hi']} "
              f"(claimed 26-32), catch_rate {spheal['species'].catch_rate} (claimed 255)")

print("\n  For completeness, the OTHER Shoal Cave rooms (the entrance room is only one of several):")
for room in ("SHOAL_CAVE_LOW_TIDE_INNER_ROOM", "SHOAL_CAVE_LOW_TIDE_STAIRS_ROOM",
             "SHOAL_CAVE_LOW_TIDE_LOWER_ROOM", "SHOAL_CAVE_LOW_TIDE_ICE_ROOM"):
    dump_table(getattr(MapRSE, room))
    print()

# =============================================================================================
head("5 — WHICH PARTY MEMBER WOULD BE DEPOSITED, and is our only Surf carrier spared?")

views = team_policy.view_from_party(party)
# ‼ `find_dead_weight` returns [(index, reason)] — TUPLES, not bare indices (the lesson recorded
# in probe_slot_free_plan.py). Reading the return SHAPE is the cheapest bug in this file.
worst = team_policy.find_dead_weight(views)
print("  find_dead_weight (worst first):")
if not worst:
    print("    (none — nothing is considered a passenger)")
for index, reason in worst:
    name = party[index].species.name if party[index] is not None else "?"
    print(f"    slot {index}  {name:<11} {reason}")

print("\n  sole-HM-carrier exemption (outranks every heuristic):")
any_exempt = False
for index in range(len(views)):
    sole = team_policy._only_hm_carrier(views, index)
    if sole:
        any_exempt = True
        name = party[index].species.name if party[index] is not None else "?"
        print(f"    slot {index}  {name:<11} EXEMPT — sole carrier of {sorted(sole)}")
if not any_exempt:
    print("    (none exempt)")

surf_carriers = [
    index for index, mon in enumerate(party)
    if mon is not None and any(m is not None and m.move.name == "Surf" for m in mon.moves)
]
print(f"\n  Surf carriers in the party: {surf_carriers} "
      f"({[party[i].species.name + ' L' + str(party[i].level) for i in surf_carriers]})")

victim = worst[0][0] if worst else None
victim_name = party[victim].species.name if victim is not None else None
victim_level = party[victim].level if victim is not None else None
print(f"  ONE-SHOT victim would be  : slot {victim} ({victim_name} L{victim_level})")
spared_ok = victim is not None and victim not in surf_carriers
print(f"\n  [{'SURF CARRIER SPARED' if spared_ok else '‼ DANGER / UNDECIDED'}] "
      f"the deposit does NOT take a Surf carrier: {spared_ok}")

# =============================================================================================
head("6 — REACHABILITY from MOSSDEEP_CITY (19,11) to each hunting ground")

SOURCE = (MapRSE.MOSSDEEP_CITY.value, (19, 11))
print(f"  source (as specified): MOSSDEEP_CITY (19, 11)")
print(f"  (the avatar is actually at {MapRSE(HERE[0]).name} {HERE[1]} — both are tested)\n")


def try_path(label, source, destination):
    try:
        path = calculate_path(source, destination)
    except PathFindingError as error:
        print(f"    {label:<52} ‼ PathFindingError: {error}")
        return None
    except Exception as error:  # noqa: BLE001 - any failure is reported verbatim, never swallowed
        print(f"    {label:<52} ‼ {type(error).__name__}: {error}")
        return None
    print(f"    {label:<52} OK — {len(path)} waypoints")
    return path


print("  ‼ POSITIVE CONTROL FIRST. If this short intra-Mossdeep hop does not path, every failure")
print("    below is uninterpretable (broken source tile / unloaded map), not a real 'unreachable':")
control_path = try_path("MOSSDEEP_CITY (19,11) -> (19,12)  [control]",
                        SOURCE, (MapRSE.MOSSDEEP_CITY.value, (19, 12)))
control_path2 = try_path("avatar -> MOSSDEEP_CITY (19,11)   [control]", HERE, SOURCE)
print(f"    [{'CONTROL PASS' if control_path else '‼ CONTROL FAIL'}] the pathfinder works from this source: "
      f"{bool(control_path)}\n")

targets = [(map_enum, tile, f"named ground ({names})") for map_enum, tile, names in grounds]

# The Shoal Cave has no swept spin tile, so derive a REAL tile inside it from the warp graph
# rather than inventing one — an invented tile would make an unreachable verdict meaningless.
shoal_tiles = []
try:
    from modules.warp_graph import get_warp_graph

    graph = get_warp_graph()
    for edge in graph.edges:
        if edge.to_map == MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM.value:
            shoal_tiles.append((edge.from_map, edge.from_coords, edge.to_coords))
    print("  warps INTO SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM (used to derive a real destination tile):")
    if not shoal_tiles:
        print("    (none found in the warp graph)")
    for from_map, from_coords, to_coords in shoal_tiles:
        try:
            from_name = MapRSE(from_map).name
        except Exception:  # noqa: BLE001
            from_name = str(from_map)
        print(f"    {from_name} {from_coords}  ->  entrance room {to_coords}")
    route = graph.map_route(MapRSE.MOSSDEEP_CITY.value, MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM.value)
    print(f"\n  warp-graph map_route MOSSDEEP -> SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM: "
          f"{[MapRSE(m).name for m in route] if route else route}")
    for map_enum, _tile, _names in grounds:
        r = graph.map_route(MapRSE.MOSSDEEP_CITY.value, map_enum.value)
        print(f"  warp-graph map_route MOSSDEEP -> {map_enum.name}: "
              f"{len(r) if r else r} map hop(s)")
    print(f"  same warp region? MOSSDEEP={graph.region_of(MapRSE.MOSSDEEP_CITY.value)} "
          f"SHOAL_ENTRANCE={graph.region_of(MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM.value)} "
          f"ROUTE117={graph.region_of(MapRSE.ROUTE117.value)} "
          f"ROUTE125={graph.region_of(MapRSE.ROUTE125.value)}")
except Exception as error:  # noqa: BLE001 - a broken warp graph is reported, not assumed empty
    print(f"  <could not read the warp graph: {type(error).__name__}: {error}>")

for from_map, from_coords, to_coords in shoal_tiles[:2]:
    targets.append((MapRSE.SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM, to_coords,
                    "shoal entrance room (arrival tile of a real warp)"))
    try:
        targets.append((MapRSE(from_map), from_coords, "the Shoal Cave DOOR (first leg, needs Surf)"))
    except Exception:  # noqa: BLE001
        pass

print("\n  calculate_path attempts (a warp-crossing trip is EXPECTED to fail here — `calculate_path`")
print("  cannot use warps; that is why the warp-graph rows above are printed alongside):")
for map_enum, tile, why in targets:
    try_path(f"MOSSDEEP (19,11) -> {map_enum.name} {tile}", SOURCE, (map_enum.value, tuple(tile)))
    try_path(f"avatar          -> {map_enum.name} {tile}", HERE, (map_enum.value, tuple(tile)))

print("\n  And the MART (section 1's contingency) — can we even get to a shop from here?")
try:
    from modules.warp_graph import get_warp_graph as _gwg

    mart_doors = [e for e in _gwg().edges
                  if e.to_map == MapRSE.MOSSDEEP_CITY_MART.value
                  and e.from_map == MapRSE.MOSSDEEP_CITY.value]
    if not mart_doors:
        print("    (no MOSSDEEP_CITY -> MOSSDEEP_CITY_MART warp found in the graph)")
    for edge in mart_doors[:2]:
        try_path(f"MOSSDEEP (19,11) -> MART DOOR {edge.from_coords}", SOURCE,
                 (MapRSE.MOSSDEEP_CITY.value, tuple(edge.from_coords)))
except Exception as error:  # noqa: BLE001
    print(f"    <could not look up the mart door: {type(error).__name__}: {error}>")

# =============================================================================================
head("VERDICT")

print(f"  balls in bag              : {total_balls}"
      f"{'   ‼ #24-ballstarve CONFIRMED' if total_balls == 0 else ''}")
print(f"  money                     : ${money}  (affordable balls: {affordable_poke_balls()})")
print(f"  hunting grounds for DIVE  : {len(grounds)}  {[g[0].name for g in grounds]}")
print(f"  deposit victim            : slot {victim} ({victim_name} L{victim_level})")
print(f"  Surf carrier spared       : {spared_ok}")
print(f"  controls                  : bag={control_bag_ok} learnset={ctl_ok} "
      f"encounters={bool(route117)} pathfinder={bool(control_path)}")
print("\n‼ NOT ANSWERED HERE, and must not be assumed:")
print("  * whether any Shoal Cave tile is a SPIN tile — no two-way sweep was done, and this project")
print("    demotes grounds derived statically (the Route 114 lesson);")
print("  * whether the mart actually STOCKS Poké Balls (that reads sMartInfo with a shop menu open);")
print("  * whether a driven navigation can cross the warps that `calculate_path` cannot.")
