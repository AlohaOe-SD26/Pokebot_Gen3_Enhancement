"""§Ch18 — SOLVE the Mossdeep Gym on the validated model, and cross-check the answer.

‼ WHY THIS IS A SEARCH AND NOT A TRANSCRIPTION. Two independent research agents produced a 116-step
route through this gym, and they agree with each other and with a published walkthrough. By this
project's standing rule that makes it a NOTE, not the answer — so the route is DERIVED here from the
model that `probe_gym_simulate.py` validated against the game, and the agents' route is used only as
a cross-check on what the search finds.

WHAT THE SEARCH MODELS, all of which are forced rather than optional:
  * a SWITCH rotates its colour the instant you step on it — three switches are unavoidable transit
    tiles, so the bot rotates purple and blue just by walking;
  * a WARP pad moves you the instant you step on it;
  * `(21,6)` is a coord event that throws you back to the entrance hall — not a warp event, not
    flag-gated, and a real edge the search must be able to see and decline;
  * walkability is collision PLUS the live objects, because the objects ARE the puzzle.

CONTROLS:
  [1] WARP TABLE — the six same-map warp pairings must match the ones read independently from the
      decomp's `warp_events`. A misread warp table would produce a confident route to nowhere.
  [2] A ROUTE EXISTS, and every switch press it makes is on a tile the arrow dump calls a switch.
  [3] CROSS-CHECK — the search's switch ORDER is compared against the agents' route. Agreement is
      reassuring; disagreement is interesting; neither is proof. The search is what we believe,
      because the search runs on the model the emulator validated.
  [4] REPLAY — the returned route is replayed through the simulator from the initial state and must
      end on a leader-approach tile. This catches a route that is internally inconsistent.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gym_solve.py
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

from modules.player import get_player_avatar
from modules.story.mossdeep_gym_puzzle import (
    COLOUR_NAMES,
    COORD_WARPS,
    LEADER_APPROACH_TILES,
    build_puzzle_from_emulator,
    read_internal_warps,
    solve_route,
)

ANCHOR = REPO / "tools" / "story-dev" / "saves" / "in_mossdeep_gym.ss1"

#: Read independently from the decomp's `warp_events` — a control on our own ROM read, not an input.
EXPECTED_WARP_PAIRS = {
    ((1, 33), (20, 24)), ((20, 24), (1, 33)),
    ((23, 20), (9, 18)), ((9, 18), (23, 20)),
    ((7, 18), (8, 12)), ((8, 12), (7, 18)),
    ((11, 3), (11, 35)), ((11, 35), (11, 3)),
    ((13, 32), (21, 10)), ((21, 10), (13, 32)),
    ((3, 28), (1, 23)), ((1, 23), (3, 28)),
}

#: The agents' switch order, for cross-check only. NEVER used as an input to the search.
AGENT_SWITCH_ORDER = ["Purple", "Green", "Green", "Purple", "Purple",
                      "Blue", "Blue", "Blue", "Blue", "Blue", "Blue",
                      "Red", "Red", "Red", "Blue", "Blue"]

line = "=" * 96

context.emulator.load_save_state(ANCHOR.read_bytes())
for _ in range(60):
    context.emulator.run_single_frame()

puzzle = build_puzzle_from_emulator()
warps = read_internal_warps()
start = tuple(get_player_avatar().local_coordinates)

print(line)
print("MOSSDEEP GYM — solving on the validated model")
print(line)
print(f"\nstart : {start}")
print(f"goal  : any of {sorted(LEADER_APPROACH_TILES)} (then face NORTH and press A)")
print(f"objects {len(puzzle.objects)} | arrows {len(puzzle.arrows)} | switches {len(puzzle.switches)}"
      f" | internal warps {len(warps)}")

print("\n" + line)
print("CONTROL [1] — the warp table we read vs the decomp's warp_events")
print(line)
print()
found_pairs = {(source, target) for source, target in warps.items()}
missing = EXPECTED_WARP_PAIRS - found_pairs
extra = found_pairs - EXPECTED_WARP_PAIRS
for source, target in sorted(warps.items()):
    mark = "OK" if (source, target) in EXPECTED_WARP_PAIRS else "‼ UNEXPECTED"
    print(f"  {str(source):<9} -> {str(target):<9} {mark}")
print(f"\n  missing pairs: {sorted(missing) or 'none'}")
print(f"  extra pairs  : {sorted(extra) or 'none'}")
control1 = not missing and not extra
print(f"  [1] {'OK' if control1 else 'FAIL — a misread warp table produces a confident route to nowhere'}")
print(f"\n  plus the non-warp coord link {COORD_WARPS} — modelled as an edge so the search can decline it")

print("\n" + line)
print("SEARCHING")
print(line)
route = solve_route(puzzle, start, warps)
if route is None:
    print("\n  ‼ NO ROUTE FOUND. Do not paper over this with the agents' route — the model and the")
    print("    game disagree somewhere, and the model is the thing that just passed validation.")
    sys.exit(1)

switch_steps = [step for step in route if step.kind == "switch"]
warp_steps = [step for step in route if step.kind == "warp"]
print(f"\n  ✅ route found: {len(route)} steps, "
      f"{len(switch_steps)} switch press(es), {len(warp_steps)} warp(s)")

print("\n" + line)
print("THE ROUTE")
print(line)
print()
position = start
for index, step in enumerate(route, 1):
    if step.kind == "walk":
        continue
    label = (f"press {COLOUR_NAMES.get(step.colour, step.colour)}" if step.kind == "switch"
             else f"WARP -> {step.landed}")
    print(f"  step {index:>3}  {str(step.tile):<9} {label}")
print(f"\n  final tile: {route[-1].landed}")

print("\n" + line)
print("CONTROL [2] — every 'switch' step really is on a switch tile")
print(line)
bad_switches = [step.tile for step in switch_steps if step.tile not in puzzle.switches]
print(f"\n  switch presses: {len(switch_steps)}   on a non-switch tile: {len(bad_switches)}")
control2 = not bad_switches
print(f"  [2] {'OK' if control2 else f'FAIL — {bad_switches}'}")

print("\n" + line)
print("CONTROL [3] — CROSS-CHECK against the agents' route (a note, never the answer)")
print(line)
ours = [COLOUR_NAMES.get(step.colour, str(step.colour)) for step in switch_steps]
print(f"\n  search : {ours}")
print(f"  agents : {AGENT_SWITCH_ORDER}")
same = ours == AGENT_SWITCH_ORDER
print(f"\n  identical order: {same}")
print(f"  per-colour totals — search {({c: ours.count(c) for c in sorted(set(ours))})}")
print(f"                      agents {({c: AGENT_SWITCH_ORDER.count(c) for c in sorted(set(AGENT_SWITCH_ORDER))})}")
print("\n  ‼ This control is INFORMATIVE, not pass/fail. The search runs on the model the emulator")
print("    validated; the agents' route was derived offline from the same decomp facts twice over.")
print("    If they disagree, prefer the search and go and drive it.")

print("\n" + line)
print("CONTROL [4] — replay the route through the simulator")
print(line)
state = puzzle.initial_state
position = start
faults = []
for index, step in enumerate(route, 1):
    if not puzzle.is_walkable(step.tile, state):
        faults.append(f"step {index}: {step.tile} is not walkable in the state the route reaches")
        break
    if step.kind == "switch":
        state = puzzle.press(state, step.colour)
    position = step.landed
print(f"\n  replay ended at {position}   faults: {len(faults)}")
for fault in faults:
    print(f"    {fault}")
control4 = not faults and position in LEADER_APPROACH_TILES
print(f"  [4] {'OK — the route is internally consistent and reaches a leader tile' if control4 else 'FAIL'}")

print("\n" + line)
print("VERDICT")
print(line)
ok = control1 and control2 and control4
print(f"\n  [1] warp table    : {'OK' if control1 else 'FAIL'}")
print(f"  [2] switch tiles  : {'OK' if control2 else 'FAIL'}")
print(f"  [4] replay        : {'OK' if control4 else 'FAIL'}")
print(f"\n  {len(route)} steps to {route[-1].landed}.")
print(f"  {'PASS — ready to DRIVE. Until it is driven, this is still a plan.' if ok else 'FAIL'}")
print(line)
