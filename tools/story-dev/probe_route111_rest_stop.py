"""Verify the claim: is there a full-heal NPC/bed inside ROUTE111_OLD_LADYS_REST_STOP
(map group/number (18, 1)), and if so is it reachable/useful for the ROUTE111 training
area at tile (25, 55)?

Modeled on tools/story-dev/repro_fodder_grass.py for boot boilerplate and
tools/story-dev/maprecon.py for the static map dump.

STEPS
  1. Static dump of (18, 1): dimensions, every object event (coords/graphics/script/flag),
     every bg_event, every coord_event, every warp. Also the ROUTE111 (0, 26) warp(s) that
     lead into this building, so we know the outside door tile.
  2. Load fallarbor.ss1 (Fallarbor-side, verified below), confirm party state, then WARP the
     player directly onto the rest-stop map (statue-testing the interaction does not require
     literally walking there -- we only need to be standing on/adjacent to the interactable
     with a damaged party). Damage the party by direct memory write to gPlayerParty (documented
     below), talk to / interact with whatever is there, answer any yes/no with A, and read
     party HP/status before and after.
  3. Repeat the interaction a second time to check repeatability / gating.
  4. calculate_path from the ROUTE111 training tile (25, 55) to the rest stop's outside door,
     and compare against the path to Fallarbor's Pokemon Center.

This probe does NOT edit production files. It overwrites profiles/repro-fresh/current_state.ss1
on exit (per project convention) -- any state worth keeping was copied to saves/ first.
"""
import pathlib as _pl
import sys

_REPO = _pl.Path(__file__).resolve().parents[2]
_SANDBOX = str(_REPO / "sandbox-pokebot")
_SAVES = _REPO / "tools" / "story-dev" / "saves"
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.profiles import load_profile_by_name
from modules.game import set_rom

profile = load_profile_by_name("repro-fresh")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.stats import StatsDatabase

context.stats = StatsDatabase(profile)  # handle_battle()/RunAwayStrategy touch context.stats;
# this probe drives modules directly (no main.py bot loop), so it's never initialised otherwise.

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0
context.bot_mode = "Story"

# ============================================================================
print("=" * 78)
print("STEP 1: STATIC DUMP of ROUTE111_OLD_LADYS_REST_STOP (18, 1)")
print("=" * 78)

context.emulator.load_save_state((_SAVES / "fallarbor.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.map import get_map_data
from modules.map_data import MapRSE

REST_STOP = MapRSE.ROUTE111_OLD_LADYS_REST_STOP.value
FAMILY_HOUSE = MapRSE.ROUTE111_WINSTRATE_FAMILYS_HOUSE.value
ROUTE111 = MapRSE.ROUTE111.value


def sym(o):
    for a in ("script_symbol",):
        try:
            v = getattr(o, a)
            if v:
                return v
        except Exception:
            pass
    return "(no script)"


md = get_map_data(REST_STOP, (0, 0))
print(f"\nmap_group_and_number = {REST_STOP}  size(w,h) = {md.map_size}")

print("\n-- object events --")
if not md.objects:
    print("  (none)")
for o in md.objects:
    print(
        f"  OBJ local_id={o.local_id} coords={o.local_coordinates} graphics_id={o.graphics_id} "
        f"kind={o.kind} movement_type={o.movement_type} flag={o.flag_id} script={sym(o)}"
    )

print("\n-- bg_events (interactable tiles) --")
if not md.bg_events:
    print("  (none)")
for e in md.bg_events:
    try:
        print(
            f"  BG coords={e.local_coordinates} elevation={e.elevation} kind={e.kind} "
            f"facing={e.player_facing_direction} script={e.script_symbol}"
        )
    except Exception as ex:
        print(f"  BG ? ({ex}) :: {e.to_dict()}")

print("\n-- coord_events (tile-enter triggers) --")
if not md.coord_events:
    print("  (none)")
for e in md.coord_events:
    print(f"  COORD {e.to_dict()}")

print("\n-- warps (inside the rest stop) --")
for w in md.warps:
    try:
        dest = w.destination_location
        print(
            f"  WARP {w.local_coordinates} elev={w.elevation} -> "
            f"({w.destination_map_group},{w.destination_map_number}) {dest.map_name} "
            f"warp#{w.destination_warp_id} @ {dest.local_position}"
        )
    except Exception as ex:
        print(f"  WARP {w.local_coordinates} -> ERROR {ex}")

print("\n" + "-" * 78)
print("Cross-check: ROUTE111 warps that lead INTO the rest stop / family house")
print("-" * 78)
md_r111 = get_map_data(ROUTE111, (0, 0))
door_r111 = None
for w in md_r111.warps:
    try:
        dest = w.destination_location
        tag = ""
        if (w.destination_map_group, w.destination_map_number) == REST_STOP:
            tag = "  <-- REST STOP DOOR"
            door_r111 = w.local_coordinates
        elif (w.destination_map_group, w.destination_map_number) == FAMILY_HOUSE:
            tag = "  <-- WINSTRATE HOUSE DOOR"
        if tag:
            print(f"  ROUTE111 WARP {w.local_coordinates} -> {dest.map_name}{tag}")
    except Exception:
        pass
assert door_r111 is not None, "could not find the rest-stop door on ROUTE111"

# ============================================================================
print("\n" + "=" * 78)
print("STEP 2a: WALK there first (healthy party -- Fallarbor Town -> Route 113 ->")
print("Route 111 -> rest stop). Route 113's ash storm / NPCs fire real scripts en")
print("route, so this is driven as a retry loop: navigate_to() legitimately hands")
print("control back whenever a script fires (expecting_script=True), we drive that")
print("script to completion, then resume navigating.")
print("=" * 78)

from modules.pokemon_party import get_party
from modules.pokemon import StatusCondition, LearnedMove
from modules.debug_utilities import debug_create_pokemon, debug_write_party
from modules.player import get_player_avatar
from modules.map_path import calculate_path, PathFindingError
from modules.modes.util.walking import navigate_to
from modules.modes.util.higher_level_actions import talk_to_npc
from modules.tasks import get_global_script_context, is_waiting_for_input


def dump_party(label):
    print(f"\n-- {label} --")
    for i, mon in enumerate(get_party()):
        move_str = ", ".join(f"{m.move.name} {m.pp}/{m.total_pp}" for m in mon.moves if m is not None)
        print(
            f"  [{i}] {mon.species.name} Lv{mon.level} HP {mon.current_hp}/{mon.total_hp} "
            f"status={mon.status_condition.value} moves=[{move_str}]"
        )
    return get_party()


from modules.memory import get_game_state, GameState
from modules.battle_handler import handle_battle
from modules.battle_strategies.run_away import RunAwayStrategy


def drive_dialogue(cap=1200):
    """Mash A while a script/message is active, faithfully answering any yes/no with A."""
    frames = 0
    ctx = get_global_script_context()
    for _ in range(10):
        context.emulator.run_single_frame()
        frames += 1
    while frames < cap and (ctx.is_active or is_waiting_for_input()):
        context.emulator.press_button("A")
        context.emulator.run_single_frame()
        frames += 1
    return frames


import sys


def clear_en_route_obstacle(cap=1200, battle_cap=25000):
    """navigate_to() legitimately hands control back for anything it doesn't own: a
    triggered NPC/cutscene script, OR a real wild encounter starting mid-walk (Route 111/
    113 grass). Handle both faithfully -- dialogue gets mashed through with A, a wild
    battle is fled with the bot's own RunAwayStrategy (we don't care about this encounter,
    we're proving reachability) -- then hand control back to the navigate_to retry loop.

    ‼ battle_cap must be generous and handle_battle() must be allowed to run in ONE
    unbroken generator (never restarted mid-battle): diag_battle2.py proved a real flee
    resolves in ~640 frames end-to-end when driven continuously, but truncating the
    generator early and then raw-B-mashing the leftover BATTLE state (the first version of
    this probe did exactly that, capped at 4000) desyncs the intro/turn-order state machine
    and wedges it PERMANENTLY -- every subsequent attempt re-entered at frame 1 of
    'BattleIntroPrintPlayerSendsOut' and never advanced again (13 consecutive re-tries,
    ~150k frames burned, confirmed via a stuck current_state.ss1 snapshot). handle_battle()
    already has its own internal 6000-frame no-progress watchdog, so a high cap here is a
    pure backstop, not the primary bound."""
    gs = get_game_state()
    if gs in (GameState.BATTLE, GameState.BATTLE_STARTING):
        print("     -> wild encounter mid-walk: running away with the real RunAwayStrategy", flush=True)
        # handle_battle()'s loop condition is battle_is_active(), which is false during the
        # BATTLE_STARTING transition animation -- calling it too early makes it return
        # instantly having done nothing. Wait for the transition to actually finish first,
        # mirroring modules/modes/_listeners.py's own
        # `while get_game_state() != GameState.BATTLE: yield` before it calls handle_battle().
        settle_frames = 0
        while get_game_state() != GameState.BATTLE and settle_frames < cap:
            context.emulator.run_single_frame()
            settle_frames += 1
        battle_gen = handle_battle(RunAwayStrategy())
        battle_frames = 0
        try:
            for _ in battle_gen:
                context.emulator.run_single_frame()
                battle_frames += 1
                if battle_frames > battle_cap:
                    print(f"        handle_battle exceeded {battle_cap} frames, abandoning", flush=True)
                    break
        except Exception as e:
            print(f"        handle_battle raised: {type(e).__name__}: {e}", flush=True)
        frames = 0
        while get_game_state() != GameState.OVERWORLD and frames < cap:
            context.emulator.press_button("B")
            context.emulator.run_single_frame()
            frames += 1
        print(f"        back to overworld after {frames} extra frames (battle took {battle_frames})", flush=True)
        return True
    if get_global_script_context().is_active or is_waiting_for_input():
        used = drive_dialogue(cap)
        print(f"     -> drove a triggered script/dialogue for {used} frames")
        return True
    return False


dump_party("BEFORE any damage (as loaded from fallarbor.ss1)")

TOTAL_FRAME_BUDGET = 200_000  # hard stop so a wedge can't run forever; ~55 min of overworld time
total_frames = 0
attempts = 0
while True:
    attempts += 1
    avatar = get_player_avatar()
    if avatar.map_group_and_number == REST_STOP:
        break
    if attempts > 20:
        raise RuntimeError(f"gave up walking to the rest stop after {attempts} navigate_to() attempts")
    if total_frames > TOTAL_FRAME_BUDGET:
        raise RuntimeError(f"gave up walking to the rest stop after {total_frames} total frames (budget exceeded)")
    try:
        nav_gen = navigate_to(MapRSE.ROUTE111, door_r111, expecting_script=True, avoid_scripted_events=False)
        attempt_frames = 0
        for _ in nav_gen:
            context.emulator.run_single_frame()
            attempt_frames += 1
            total_frames += 1
            # ‼ navigate_to() itself does not intercept a wild battle that starts
            # MID-generator (only a battle already active when navigate_to() is first
            # called raises immediately). In the real bot this is caught every frame by
            # the surrounding listener stack (BattleListener), which this isolated probe
            # doesn't have -- so we replicate that here: bail out of the generator the
            # instant a battle starts and let clear_en_route_obstacle() flee it, instead
            # of spinning inside navigate_to (observed: 199514 frames stuck doing nothing
            # before this fix was added).
            if get_game_state() in (GameState.BATTLE, GameState.BATTLE_STARTING):
                print(f"     !! battle detected mid-navigate at frame {attempt_frames}, bailing out of navigate_to()", flush=True)
                # ‼ ROOT CAUSE (found live, 2026-07-25): navigate_to()/walk_to() calls
                # context.emulator.hold_button("B") to run, and abandoning its generator
                # via `break` (as we just did) never lets it release that hold. B stays
                # PHYSICALLY HELD DOWN straight into the battle, and handle_battle()'s own
                # per-frame press_button("B") calls land on top of an already-held B --
                # confirmed via a frozen current_state.ss1 snapshot: handle_battle() driven
                # freshly from that EXACT wedged state (button state reset) resolved the
                # same fight in 351 frames; through this probe's break-without-release it
                # never progressed past BattleIntroPrintPlayerSendsOut in 6000+. Release all
                # held inputs before handing off to the battle handler.
                context.emulator.reset_held_buttons()
                break
            if attempt_frames % 2000 == 0:
                av = get_player_avatar()
                print(f"     ... attempt {attempts}: {attempt_frames} frames, at {av.map_group_and_number} "
                      f"{av.local_coordinates}, total_frames={total_frames}", flush=True)
            if total_frames > TOTAL_FRAME_BUDGET:
                print("     !! frame budget exceeded mid-attempt, aborting", flush=True)
                break
    except Exception as e:
        print(f"   navigate_to attempt {attempts} raised: {type(e).__name__}: {e}", flush=True)
    context.emulator.reset_held_buttons()  # never hand off with a stale hold_button("B") in flight
    avatar = get_player_avatar()
    print(f"   navigate_to attempt {attempts} ended at {avatar.map_group_and_number} {avatar.local_coordinates} "
          f"game_state={get_game_state().name} script_active={get_global_script_context().is_active} "
          f"(attempt used {attempt_frames} frames, total {total_frames})", flush=True)
    clear_en_route_obstacle()

for _ in range(30):
    context.emulator.run_single_frame()

avatar = get_player_avatar()
here = avatar.map_group_and_number
print(f"   player now at map {here} local={avatar.local_coordinates} (expect {REST_STOP} = rest stop interior)")
assert here == REST_STOP, f"did not arrive inside the rest stop, at {here} instead"
dump_party("party state on arrival (still healthy -- confirms the walk itself didn't damage it)")

# ============================================================================
print("\n" + "=" * 78)
print("STEP 2b: NOW damage the party in place (documented direct write via")
print("debug_create_pokemon + debug_write_party -- both existing production")
print("helpers, properly re-encrypted, no hand-rolled memory writes)")
print("=" * 78)

before = get_party()
statuses = [StatusCondition.Poison, StatusCondition.Paralysis, StatusCondition.Burn, StatusCondition.Sleep]
damaged = []
for i, mon in enumerate(before):
    reduced_moves = [
        LearnedMove(move=m.move, total_pp=m.total_pp, pp=0 if j == 0 else max(0, m.pp - 2), pp_ups=m.pp_ups)
        for j, m in enumerate(mon.moves)
        if m is not None
    ]
    damaged.append(
        debug_create_pokemon(
            species=mon.species,
            level=mon.level,
            original_pokemon=mon,
            nature=mon.nature,
            ivs=mon.ivs,
            evs=mon.evs,
            held_item=mon.held_item,
            friendship=mon.friendship,
            moves=reduced_moves,
            current_hp=1,
            status_condition=statuses[i % len(statuses)],
        )
    )
debug_write_party(damaged)
context.emulator.run_single_frame()  # advance so state_cache.party (frame-keyed) re-reads

injected = dump_party("AFTER injected damage (HP=1, status set, PP partially spent) -- CONTROL: readback")
for i, mon in enumerate(injected):
    assert mon.current_hp == 1, f"mon {i} HP not injected: {mon.current_hp}"
    assert mon.status_condition != StatusCondition.Healthy, f"mon {i} status not injected"
    assert any(m.pp == 0 for m in mon.moves if m is not None), f"mon {i} PP not injected"
print("   readback confirms the injected damage really landed in game memory (not just our object)")

print("\n-- talking to the Old Lady (local_id=1) --")
gen = talk_to_npc(1)
try:
    for _ in gen:
        context.emulator.run_single_frame()
except Exception as e:
    print(f"   talk_to_npc raised: {type(e).__name__}: {e}")
frames_used = drive_dialogue()
print(f"   dialogue driven for {frames_used} frames")

after = dump_party("AFTER interaction #1 (talked to the Old Lady, mashed A through any prompts)")
full_heal = all(
    m.current_hp == m.total_hp and m.status_condition == StatusCondition.Healthy for m in after
)
pp_full = all(all((lm.pp == lm.total_pp) for lm in m.moves if lm is not None) for m in after)
print(f"\n   HP+status fully restored: {full_heal}")
print(f"   PP fully restored:        {pp_full}")

print("\n-- STEP 3: interact a SECOND time to check repeatability --")
gen2 = talk_to_npc(1)
try:
    for _ in gen2:
        context.emulator.run_single_frame()
except Exception as e:
    print(f"   talk_to_npc (2nd) raised: {type(e).__name__}: {e}")
frames_used2 = drive_dialogue()
print(f"   dialogue driven for {frames_used2} frames (2nd attempt)")
after2 = dump_party("AFTER interaction #2 (repeat, party already full)")
still_full = all(
    m.current_hp == m.total_hp and m.status_condition == StatusCondition.Healthy for m in after2
)
print(f"   still full after repeat (nothing broke / no odd gating observed): {still_full}")

# ============================================================================
print("\n" + "=" * 78)
print("STEP 4: reachability from the ROUTE111 training tile (25, 55)")
print("=" * 78)
TRAIN_TILE = (25, 55)
from modules.map_data import PokemonCenter

pc_map, pc_tile = PokemonCenter.FallarborTown.value

for label, dest in (
    ("training tile -> REST STOP door", (ROUTE111, door_r111)),
    ("REST STOP door -> training tile", None),
    ("training tile -> Fallarbor PC", (pc_map.value, pc_tile)),
):
    try:
        if label == "REST STOP door -> training tile":
            path = calculate_path((ROUTE111, door_r111), (ROUTE111, TRAIN_TILE), avoid_encounters=False, avoid_scripted_events=False)
        else:
            path = calculate_path((ROUTE111, TRAIN_TILE), dest, avoid_encounters=False, avoid_scripted_events=False)
        print(f"  {label}: OK, {len(path)} steps")
    except PathFindingError as e:
        print(f"  {label}: UNREACHABLE ({e})")
