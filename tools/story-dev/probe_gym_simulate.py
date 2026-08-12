"""§Ch18 — VALIDATE THE STATUE SIMULATOR AGAINST THE GAME, press by press.

‼ WHY THIS EXISTS. `modules/story/mossdeep_gym_puzzle.py` claims it can predict where every statue
lands after a switch press. A route planner is about to be built on that claim, and this project has
already paid four times over for building on an unvalidated map model (KI-58). So before any route
is planned: press the switch for real, and require the simulator to have called it exactly.

WHAT IT DOES — a closed loop that tests the model with the model:
  * walk to the yellow switch at (3,30) using a path found over the SIMULATED walkable set;
  * step on it, let the game move the statues, and read the live object positions back;
  * compare against `puzzle.press(state, YELLOW)`;
  * repeat four times, which is one full cycle of the pad, then check the state came home.

‼ THE WALK IS ITSELF A TEST. The path is planned over `puzzle.is_walkable`, i.e. collision PLUS the
simulated object positions. If the simulator has a statue in the wrong place, the walk desynchronises
— the avatar fails to arrive on the tile the plan expected — and the probe reports exactly which
step disagreed. A model that can route you across its own map is being checked twice.

‼ ONLY LOADED OBJECTS CAN BE COMPARED. `get_map_objects()` returns the objects the game currently
has loaded, which is a SUBSET of the 36 templates. Comparing a full simulated state against a partial
live list would fail for reasons that have nothing to do with the model, so the comparison is keyed
on `local_id` and covers only the objects actually present. The count of compared objects is printed,
because a comparison over zero objects would otherwise pass silently.

‼ THE WALK MUST NOT CROSS ANOTHER SWITCH. Nine tiles are floor switches and they re-fire every time
they are stepped on. A path that clips one would rotate a colour the test never asked for and the
mismatch would look like a model bug. Switch tiles other than the target are excluded from the path.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gym_simulate.py
      PYTHONUTF8=1 py -3.12 probe_gym_simulate.py --presses 4 --switch 3,30
"""

import argparse
import pathlib
import sys
from collections import deque

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

from modules.map import get_map_objects
from modules.map_data import MapRSE
from modules.player import get_player_avatar, player_avatar_is_standing_still
from modules.tasks import get_global_script_context
from modules.story.mossdeep_gym_puzzle import COLOUR_NAMES, build_puzzle_from_emulator

parser = argparse.ArgumentParser()
parser.add_argument("--anchor", default="in_mossdeep_gym.ss1")
parser.add_argument("--presses", type=int, default=4, help="how many times to hit the switch")
parser.add_argument("--switch", default="3,30", help="which switch tile to test, 'x,y'")
args = parser.parse_args()

ANCHOR = REPO / "tools" / "story-dev" / "saves" / args.anchor
SWITCH = tuple(int(part) for part in args.switch.split(","))
GYM = MapRSE.MOSSDEEP_CITY_GYM
DELTAS = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}

line = "=" * 96


def settle(frames: int = 300, *, minimum: int = 0) -> None:
    """Run until the avatar AND every loaded object have been still for a while.

    ‼ POSITIONS BEING STABLE IS NOT THE SAME AS BEING ABLE TO MOVE, and mistaking the two cost two
    runs here. Stepping on a switch starts a script that moves the statues while the avatar stands
    perfectly still; once the statues stop, everything LOOKS settled, but the script is still holding
    the player through its turn/free/release tail. A press issued there is swallowed, and the symptom
    ("could not step off the switch") points nowhere near the cause.

    So do not infer readiness from stillness — ask the game. `player_avatar_is_standing_still()` is
    the codebase's own predicate: overworld state, no held movement, not frozen, not mid-door.

    ‼ AND EVEN THAT IS NOT ENOUGH ON A SWITCH TILE, which is the third version of this bug. Landing
    on a coord_event tile leaves a short window where the step has finished but the script has not
    yet taken hold: the avatar reads as standing still, the wait returns, and the press that follows
    is eaten by the script that starts a moment later. `minimum` holds the wait open long enough for
    the script to declare itself. A readiness check can only tell you the game is ready NOW — it
    cannot tell you nothing is about to start."""
    stable = 0
    for frame in range(frames):
        context.emulator.run_single_frame()
        try:
            ready = player_avatar_is_standing_still()
        except Exception:  # noqa: BLE001 — unreadable mid-script; keep running rather than guess
            stable = 0
            continue
        if ready:
            stable += 1
            if stable >= 20 and frame >= minimum:
                return
        else:
            stable = 0


def player_tile() -> tuple[int, int]:
    return tuple(get_player_avatar().local_coordinates)


def live_objects() -> dict[int, tuple[int, int]]:
    """local_id -> current tile, for every object the game has loaded right now."""
    return {
        obj.local_id: tuple(obj.current_coords)
        for obj in get_map_objects()
        if "isPlayer" not in obj.flags
    }


def plan(start, goal, state, allow_switches) -> list[tuple[int, int]] | None:
    """BFS over the SIMULATED walkable set. `allow_switches` holds the tiles we may legally step on.

    Every other switch is excluded — stepping on one fires it, which would rotate a colour this test
    did not ask for and make a model mismatch look like a model bug."""
    if start == goal:
        return []
    queue, came = deque([start]), {start: None}
    while queue:
        tile = queue.popleft()
        for dx, dy in DELTAS.values():
            nxt = (tile[0] + dx, tile[1] + dy)
            if nxt in came or not puzzle.is_walkable(nxt, state):
                continue
            if nxt in puzzle.switches and nxt not in allow_switches:
                continue
            came[nxt] = tile
            if nxt == goal:
                path = [nxt]
                while came[path[-1]] is not None:
                    path.append(came[path[-1]])
                return list(reversed(path))[1:]
            queue.append(nxt)
    return None


def step_to(neighbour: tuple[int, int]) -> bool:
    """Move one tile. Press, settle; if we only turned, press again — never twice blind.

    ‼ Two blind presses move TWO tiles whenever the avatar already faced that way, which steps
    straight over a tile. In a room where nine tiles are switches, skipping a tile can silently fire
    one. This bug already cost `probe_gym_bruteforce.py` its first run."""
    here = player_tile()
    direction = next(
        name for name, (dx, dy) in DELTAS.items()
        if (here[0] + dx, here[1] + dy) == neighbour
    )
    context.emulator.press_button(direction)
    settle()
    if player_tile() == here:
        context.emulator.press_button(direction)
        settle()
    return player_tile() == neighbour


context.emulator.load_save_state(ANCHOR.read_bytes())
settle()
puzzle = build_puzzle_from_emulator()

print(line)
print("MOSSDEEP GYM — does the simulator predict the game?")
print(line)
print(f"\nanchor : {ANCHOR.name}")
print(f"start  : {player_tile()}")
print(f"switch : {SWITCH} (colour {COLOUR_NAMES.get(puzzle.switches.get(SWITCH), '?')})")
print(f"objects: {len(puzzle.objects)} templates | arrows: {len(puzzle.arrows)} | "
      f"switches: {len(puzzle.switches)}")

if SWITCH not in puzzle.switches:
    print(f"\n‼ {SWITCH} is not a switch tile. Known switches: {sorted(puzzle.switches)}")
    sys.exit(1)
colour = puzzle.switches[SWITCH]

# ---------------------------------------------------------------- control 0: the starting state
state = puzzle.initial_state
live = live_objects()
by_id = {obj.local_id: index for index, obj in enumerate(puzzle.objects)}
mismatched = {lid: (pos, state[by_id[lid]]) for lid, pos in live.items()
              if lid in by_id and pos != state[by_id[lid]]}
print("\n" + line)
print("CONTROL [0] — does the anchor really start from the UNROTATED template positions?")
print(line)
print(f"\n  loaded objects compared: {len(live)}   mismatched: {len(mismatched)}")
for lid, (actual, predicted) in sorted(mismatched.items()):
    print(f"    id {lid:>3}: game {actual}  template {predicted}")
control0 = not mismatched and len(live) > 0
print(f"  [0] {'OK — entering the gym does reset the puzzle' if control0 else 'FAIL'}")

# ---------------------------------------------------------------- the press loop
print("\n" + line)
print(f"PRESSING {COLOUR_NAMES.get(colour, colour)} AT {SWITCH}, {args.presses} TIMES")
print(line)

results = []
for press_number in range(1, args.presses + 1):
    # ‼ A ROTATION RE-AIMS THE TRAINERS, AND THEY CHALLENGE YOU. Nine of the gym's trainers stand on
    # arrow pads, so `moverotatingtileobjects` moves them and `turnrotatingtileobjects` turns them
    # 90° counter-clockwise. Pressing yellow at (3,30) slides Maura from (4,29) to (4,30) — directly
    # beside the player on the switch — and turns her to face them. The trainer intro script starts,
    # field controls lock, and every subsequent button press is swallowed.
    #
    # This is not a probe bug and not a model bug: it is how the gym works, and the executor has to
    # fight these battles. It is reported here as its own outcome because the symptom otherwise
    # reads as "the avatar refuses to walk", which points nowhere near the cause.
    script = get_global_script_context()
    if script is not None and script.is_active:
        print(f"\n  press {press_number}: the rotation triggered a script — {script.stack}")
        print("     A rotated trainer has line of sight on the switch tile. Expected, not a fault:")
        print("     the executor must fight gym trainers as part of solving the puzzle.")
        results.append((press_number, "TRAINER", 0, 0))
        break

    here = player_tile()
    # ‼ Step OFF the switch before re-pressing it: standing still does not re-fire a coord_event.
    if here == SWITCH:
        neighbours = [
            (here[0] + dx, here[1] + dy) for dx, dy in DELTAS.values()
            if puzzle.is_walkable((here[0] + dx, here[1] + dy), state)
            and (here[0] + dx, here[1] + dy) not in puzzle.switches
        ]
        if not neighbours or not step_to(neighbours[0]):
            print(f"\n  press {press_number}: could not step off the switch — aborting")
            print(f"      avatar at {player_tile()}   switch {SWITCH}")
            print(f"      candidate step-off tiles: {neighbours}")
            print(f"      simulated occupancy near by: "
                  f"{sorted(t for t in state if abs(t[0] - SWITCH[0]) <= 2 and abs(t[1] - SWITCH[1]) <= 2)}")
            print(f"      live objects: {sorted(live_objects().items())}")
            # ‼ ALWAYS PRINT THE SCRIPT STACK when the avatar will not move. "Cannot walk" has
            # many causes that look identical from outside the game; the script stack names the real
            # one in a single line. Here it read `EventScript_ShowTrainerIntroMsg`, which turned a
            # suspected geometry bug into a known game mechanic in one run.
            from modules.memory import get_game_state, get_game_state_symbol
            from modules.player import get_player_map_object
            blocking = get_global_script_context()
            print(f"      game state       : {get_game_state()}  callback {get_game_state_symbol()}")
            print(f"      script active    : {blocking.is_active if blocking else None}")
            print(f"      script stack     : {blocking.stack if blocking else None}")
            print(f"      player map flags : {get_player_map_object().flags}")
            print(f"      standing still   : {player_avatar_is_standing_still()}")
            break
        here = player_tile()

    path = plan(here, SWITCH, state, {SWITCH})
    if path is None:
        print(f"\n  press {press_number}: NO PATH from {here} to {SWITCH} over the simulated map")
        break

    desynced = None
    for tile in path:
        if not step_to(tile):
            desynced = (tile, player_tile())
            break
    if desynced is not None:
        print(f"\n  press {press_number}: ‼ WALK DESYNC — plan said {desynced[0]}, "
              f"avatar is at {desynced[1]}")
        print("     The simulated map and the real map disagree. That is a MODEL BUG, and it is")
        print("     the failure this probe exists to catch.")
        results.append((press_number, "DESYNC", 0, 0))
        break

    # ‼ `minimum` here is the fix for the eaten-press bug described in `settle`: hold the wait open
    # past the moment the coord_event script takes hold, then wait for it to release the player.
    settle(900, minimum=150)
    predicted = puzzle.press(state, colour)
    live = live_objects()
    compared = {lid: pos for lid, pos in live.items() if lid in by_id}
    wrong = {lid: (pos, predicted[by_id[lid]]) for lid, pos in compared.items()
             if pos != predicted[by_id[lid]]}
    verdict = "MATCH" if not wrong and compared else "MISMATCH"
    results.append((press_number, verdict, len(compared), len(wrong)))
    print(f"\n  press {press_number}: compared {len(compared)} loaded object(s) -> {verdict}")
    for lid, (actual, guess) in sorted(wrong.items()):
        print(f"      id {lid:>3}: game {actual}   simulator {guess}")
    state = predicted

# ---------------------------------------------------------------- control 2: the period-4 property
# ‼ AN OFFLINE CONTROL, AND LABELLED AS ONE. The live loop above can only reach the yellow switch
# before a rotated trainer interrupts it, so four consecutive LIVE presses are not obtainable from
# this anchor. What can be checked without the emulator is the property the whole plan rests on:
# every colour's arrows form closed 4-cycles, so four presses of any colour must be the identity.
# If that fails, the arrow field was misread and no route planned on it can be trusted.
print("\n" + line)
print("CONTROL [2] — four presses of any colour must return every object to where it started")
print(line)
print()
period_failures = []
for band in sorted({colour for colour in puzzle.switches.values()}):
    cycled = puzzle.initial_state
    for _ in range(4):
        cycled = puzzle.press(cycled, band)
    identity = cycled == puzzle.initial_state
    moved_by_one = sum(1 for a, b in zip(puzzle.press(puzzle.initial_state, band),
                                         puzzle.initial_state) if a != b)
    if not identity:
        period_failures.append(band)
    print(f"  {COLOUR_NAMES.get(band, band):<7} moves {moved_by_one:>2} object(s) per press   "
          f"4 presses = identity: {'OK' if identity else 'FAIL'}")
print(f"\n  [2] {'OK' if not period_failures else f'FAIL for {period_failures}'}")

print("\n" + line)
print("VERDICT")
print(line)
matches = sum(1 for _, verdict, _, _ in results if verdict == "MATCH")
# ‼ A TRAINER CHALLENGE IS NOT A WRONG PREDICTION. Counting it as one would make the probe report
# the model as broken every time the gym behaves exactly as the gym behaves.
graded = [entry for entry in results if entry[1] != "TRAINER"]
interrupted = [entry for entry in results if entry[1] == "TRAINER"]
print(f"\n  control [0] anchor starts unrotated : {'OK' if control0 else 'FAIL'}")
print(f"  control [2] four presses = identity : {'OK' if not period_failures else 'FAIL'}")
print(f"  live presses predicted correctly    : {matches} / {len(graded)}")
if interrupted:
    print(f"  live presses cut short by a trainer  : {len(interrupted)} "
          f"(expected — rotation re-aims the gym trainers)")
ok = control0 and not period_failures and graded and matches == len(graded)
print(f"\n  {'PASS — the simulator may be used to plan a route.' if ok else 'FAIL — do NOT plan a route on this model yet.'}")
print("\n  Scope of the live evidence: %d press(es) against the real game, identity-keyed on" % matches)
print("  local_id. The period-4 property is SIMULATED, not driven, and is labelled as such.")
print(line)
