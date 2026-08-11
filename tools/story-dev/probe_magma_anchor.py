"""`#24-magmahideout` increment 0: does the build anchor actually stand at the right point
on the STORY CLOCK, and is the hideout door reachable in that era?

WHY THIS EXISTS. On 2026-08-10 seven probes answered a post-Mt-Pyre question from badges-1-3
saves and produced two confident wrong conclusions before the decomp settled it (`08-MISTAKES`
2026-08-10). The prevention rule that came out of it is: **name the flag that gates the content
and assert it on the anchor BEFORE building anything.** This probe is that assertion, run as a
CONTRAST between the two eras so that a reader can see the flag change rather than take one
reading on faith.

WHAT IT CHECKS, on `post_mtpyre.ss1` (the build anchor) against `jagged_descent.ss1` (a
badges-1-3 save, i.e. the WRONG era, used here as the negative arm):
  1. `FLAG_HIDE_JAGGED_PASS_MAGMA_GUARD` — the flag that removes the Team Magma guard from
     `(16,19)`, the door column's only entry.
  2. `VAR_MT_PYRE_STATE` and the **Magma Emblem** key item — the two things the decomp says the
     summit scene hands over.
  3. Static reachability of the door itself: `JAGGED_PASS (16,20) -> (16,18)`.

‼ CONTROLS, because a probe that reports False is indistinguishable from a probe that cannot
see (`get_event_flag` returns **False for an unknown flag name**, silently — a phantom name
would read exactly like a clear flag):
  * NAME CONTROL — the flag name must be present in `modules.memory._event_flags`. If it is
    not, every reading below is meaningless and the probe says UNTRUSTED instead of an answer.
  * ERA CONTROL — the two saves must DISAGREE on the guard flag. Agreement means the reader is
    not tracking the thing it claims to track.
  * PATH CONTROL — a trivially-reachable target on the same map must plan, proving the planner
    answers at all from the approach tile.

‼ READ THE PATH RESULT NARROWLY. `calculate_path` is a static planner that reads dual-elevation
terrain and ledges as walls; it has called a reachable place unreachable before (KI-24). A YES
here means "worth driving", not "proven". The driven proof is the travel-leg run.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_magma_anchor.py
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
context.bot_mode = "Story"

from modules.items import get_item_bag
from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import _event_flags, get_event_flag, get_event_var
from modules.player import get_player_avatar

SAVES = pathlib.Path(__file__).resolve().parent / "saves"

GUARD_FLAG = "HIDE_JAGGED_PASS_MAGMA_GUARD"      # 847 — decomp JaggedPass/map.json
PYRE_VAR = "MT_PYRE_STATE"                        # 185 — set to 1 by the summit scene
DOOR = (16, 18)                                   # JAGGED_PASS -> MAGMA_HIDEOUT_1F (warp id 4)
APPROACH = (16, 20)                               # the planner-reachable tile below the column
CONTROL_TILE = (14, 18)                           # the nearest reachable tile; must always plan

ANCHOR = "post_mtpyre.ss1"        # the BUILD anchor — expected post-Emblem
WRONG_ERA = "jagged_descent.ss1"  # badges 1-3 — expected pre-Emblem, guard present

line = "=" * 88


def read_era(save_name: str) -> dict:
    """Load `save_name` and read the three era markers out of live memory."""
    row: dict = {"save": save_name}
    path = SAVES / save_name
    if not path.is_file():
        row["error"] = "missing"
        return row
    context.emulator.load_save_state(path.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()

    try:
        avatar = get_player_avatar()
        row["map_enum"] = MapRSE(tuple(avatar.map_group_and_number)).name
        row["tile"] = tuple(avatar.local_coordinates)
    except Exception as error:  # noqa: BLE001 - a probe reports, it does not crash
        row["map_enum"] = f"?({type(error).__name__})"
        row["tile"] = None

    row["guard_hidden"] = get_event_flag(GUARD_FLAG)
    row["pyre_state"] = get_event_var(PYRE_VAR)
    try:
        row["emblem"] = any(
            "magma" in slot.item.name.lower() and "emblem" in slot.item.name.lower()
            for slot in get_item_bag().key_items
        )
    except Exception as error:  # noqa: BLE001
        row["emblem"] = f"?({type(error).__name__})"
    row["badges"] = [n for n in range(1, 9) if get_event_flag(f"BADGE0{n}_GET")]
    return row


def plan(start: tuple[int, int], end: tuple[int, int]) -> str:
    """Static plan WITHIN Jagged Pass. Returns 'OK, N waypoints' or the failure reason."""
    try:
        start_tile = get_map_data(MapRSE.JAGGED_PASS, start)
        end_tile = get_map_data(MapRSE.JAGGED_PASS, end)
        return f"OK, {len(calculate_path(start_tile, end_tile))} waypoints"
    except PathFindingError as error:
        return f"FAIL ({error})"
    except Exception as error:  # noqa: BLE001
        return f"FAIL ({type(error).__name__}: {error})"


print(line)
print("NAME CONTROL — the gating flag name must resolve, or every reading below is noise")
print(line)
name_ok = GUARD_FLAG in _event_flags
print(f"  '{GUARD_FLAG}' in modules.memory._event_flags: {name_ok}")
var_ok = get_event_var(PYRE_VAR) != -1 or True  # value checked per-save below; -1 means unknown
print(f"  NAME CONTROL {'PASS' if name_ok else 'FAIL'}")

print()
print(line)
print("ERA CONTRAST — the build anchor vs a known-wrong-era save")
print(line)
rows = [read_era(ANCHOR), read_era(WRONG_ERA)]
for row in rows:
    if "error" in row:
        print(f"  {row['save']:<24} {row['error']}")
        continue
    print(
        f"  {row['save']:<24} badges={''.join(str(b) for b in row['badges']) or '-':<8}"
        f" {row['map_enum']} {row['tile']}"
    )
    print(
        f"  {'':<24} {GUARD_FLAG}={row['guard_hidden']}"
        f"  {PYRE_VAR}={row['pyre_state']}  magma_emblem={row['emblem']}"
    )

anchor, wrong = rows[0], rows[1]
era_ok = (
    "error" not in anchor
    and "error" not in wrong
    and anchor.get("guard_hidden") != wrong.get("guard_hidden")
)
print(f"  ERA CONTROL {'PASS' if era_ok else 'FAIL'} — the two saves"
      f" {'disagree' if era_ok else 'AGREE, so the reader is not tracking the guard'}")

print()
print(line)
print("DOOR REACHABILITY (static) — measured in the ANCHOR's era")
print(line)
context.emulator.load_save_state((SAVES / ANCHOR).read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()
control = plan(APPROACH, CONTROL_TILE)
door = plan(APPROACH, DOOR)
print(f"  CONTROL  {APPROACH} -> {CONTROL_TILE}  {control}")
print(f"  DOOR     {APPROACH} -> {DOOR}  {door}")
path_ok = control.startswith("OK")
print(f"  PATH CONTROL {'PASS' if path_ok else 'FAIL'}")

print()
print(line)
ready = (
    name_ok
    and era_ok
    and path_ok
    and anchor.get("guard_hidden") is True
    and anchor.get("pyre_state", -1) >= 1
    and anchor.get("emblem") is True
)
print(f"VERDICT: anchor '{ANCHOR}' is {'READY' if ready else 'NOT READY'} to build §Ch15 against.")
if not ready:
    print("  ‼ Do NOT build from it. Capture a post-Emblem anchor first.")
print(line)
