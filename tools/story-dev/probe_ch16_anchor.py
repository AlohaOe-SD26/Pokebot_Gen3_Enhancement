"""§Ch16 increment 0: is `post_maxie.ss1` on the right point of the STORY CLOCK for the
Slateport Harbor submarine beat, and is the trigger column reachable in that era?

WHY THIS EXISTS. Every one of the four `SLATEPORT_CITY_HARBOR` coord triggers is gated on
`VAR_SLATEPORT_HARBOR_STATE == 1` (decomp `SlateportCity_Harbor/map.json`). A save one beat
early reads 0 and the scene simply never fires — which looks exactly like a navigation bug, and
is the mistake that cost seven probes on 2026-08-10 (`08-MISTAKES`: *name the flag that gates the
content and assert it on the anchor BEFORE building anything*). This probe is that assertion, run
as a CONTRAST between two eras so a reader watches the var CHANGE rather than trusting one number.

WHAT IT CHECKS, on `post_maxie.ss1` (the build anchor) against `magma_door.ss1` (one beat
earlier — Maxie not yet beaten — the negative arm):
  1. `VAR_SLATEPORT_HARBOR_STATE` — must be **1** on the anchor and **not 1** on the wrong era.
     This is the gate; nothing else matters if it is wrong.
  2. `VAR_SLATEPORT_CITY_STATE` and `FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT` — the other two things
     Maxie's defeat sets, read as corroboration that the era is what it claims.
  3. `FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1/2_BLOCKING_ENTRANCE` — these are set BY the harbor scene,
     so on a correct anchor they must still be **UNSET**. ‼ This is the "the beat has not happened
     yet" control: an anchor taken AFTER the scene would pass check 1 in the wrong direction
     (`VAR_..._HARBOR_STATE` would be 2) and is caught here too.
  4. Static reachability inside `SLATEPORT_CITY_HARBOR`: door `(11,14)` -> trigger 3 `(8,14)`.

‼ CONTROLS, because a probe that reports a plausible number is indistinguishable from a probe
that cannot see. `get_event_var` returns **-1** for an unknown NAME and `get_event_flag` returns
**False** — silently — so a typo reads exactly like a legitimate "not set yet":
  * NAME CONTROL — every var/flag name used must resolve. If one does not, the probe prints
    UNTRUSTED and refuses to answer instead of reporting a confident -1/False.
  * ERA CONTROL — the two saves must DISAGREE on `VAR_SLATEPORT_HARBOR_STATE`. Agreement means
    the reader is not tracking the thing it claims to track.
  * PATH CONTROL — a trivially-reachable tile on the same map must plan, proving the planner
    answers at all from the door.

‼ READ THE PATH RESULT NARROWLY. `calculate_path` is static and has called a reachable place
unreachable before (KI-24), and — more relevant here — it has also called a WALLED tile reachable
(the Jagged Pass door read "2 waypoints" while sealed by a `setmetatile`). A YES means "worth
driving", not "proven". The driven proof is the scene run.

‼ AND `OnTransition` REWRITES THIS MAP. `SlateportCity_Harbor_OnTransition` hides the patrons and
moves Capt. Stern to `(12,13)` when the era is right, so `map.json`'s object list is NOT what will
be standing there. Do not derive walkability around objects from the static file.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch16_anchor.py
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

from modules.map import get_map_data
from modules.map_data import MapRSE
from modules.map_path import PathFindingError, calculate_path
from modules.memory import _event_flags, _event_vars, get_event_flag, get_event_var
from modules.player import get_player_avatar

SAVES = pathlib.Path(__file__).resolve().parent / "saves"

HARBOR_VAR = "SLATEPORT_HARBOR_STATE"   # the GATE on all four coord triggers
CITY_VAR = "SLATEPORT_CITY_STATE"       # set to 1 by the same Maxie script
GROUDON_FLAG = "GROUDON_AWAKENED_MAGMA_HIDEOUT"
AQUA_BLOCK_FLAGS = (
    "HIDE_AQUA_HIDEOUT_1F_GRUNT_1_BLOCKING_ENTRANCE",
    "HIDE_AQUA_HIDEOUT_1F_GRUNT_2_BLOCKING_ENTRANCE",
)

DOOR = (11, 14)          # SLATEPORT_CITY_HARBOR -> SLATEPORT_CITY (warp id 8)
TRIGGER3 = (8, 14)       # AquaEscapeTrigger3 — it applymovements the player INTO the scene
CONTROL_TILE = (12, 14)  # the other half of the same doorway; must always plan

ANCHOR = "post_maxie.ss1"      # the BUILD anchor — expected VAR_SLATEPORT_HARBOR_STATE == 1
WRONG_ERA = "magma_door.ss1"   # one beat earlier, Maxie not yet beaten — expected != 1

line = "=" * 88


def read_era(save_name: str) -> dict:
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
        # ‼ THE ENUM, NEVER `map_name` — that is a display LABEL and reads "MAUVILLE CITY" for
        # MAUVILLE_CITY_GYM. Reporting identity as the label has written a bad anchor down before.
        row["map_enum"] = MapRSE(tuple(avatar.map_group_and_number)).name
        row["tile"] = tuple(avatar.local_coordinates)
    except Exception as error:  # noqa: BLE001 - a probe reports, it does not crash
        row["map_enum"] = f"?({type(error).__name__})"
        row["tile"] = None

    row["harbor_state"] = get_event_var(HARBOR_VAR)
    row["city_state"] = get_event_var(CITY_VAR)
    row["groudon"] = get_event_flag(GROUDON_FLAG)
    row["aqua_unblocked"] = [f for f in AQUA_BLOCK_FLAGS if get_event_flag(f)]
    row["badges"] = [n for n in range(1, 9) if get_event_flag(f"BADGE0{n}_GET")]
    return row


def plan(start: tuple[int, int], end: tuple[int, int]) -> str:
    try:
        a = get_map_data(MapRSE.SLATEPORT_CITY_HARBOR, start)
        b = get_map_data(MapRSE.SLATEPORT_CITY_HARBOR, end)
        return f"OK, {len(calculate_path(a, b))} waypoints"
    except PathFindingError as error:
        return f"FAIL ({error})"
    except Exception as error:  # noqa: BLE001
        return f"FAIL ({type(error).__name__}: {error})"


print(line)
print("§Ch16 ANCHOR PROBE — Slateport Harbor submarine theft")
print(line)

# ---- NAME CONTROL, first: an unresolvable name makes every reading below a lie ----
print("\n0. NAME CONTROL — do these vars/flags exist in the reader's tables?")
bad_names: list[str] = []
for name in (HARBOR_VAR, CITY_VAR):
    ok = name in _event_vars
    print(f"   var  {name:<28} {'OK' if ok else '‼ NOT A KNOWN NAME (would read -1)'}")
    if not ok:
        bad_names.append(name)
for name in (GROUDON_FLAG, *AQUA_BLOCK_FLAGS):
    ok = name in _event_flags
    print(f"   flag {name:<48} {'OK' if ok else '‼ NOT A KNOWN NAME (would read False)'}")
    if not ok:
        bad_names.append(name)
if bad_names:
    print(f"\n‼ UNTRUSTED — {len(bad_names)} name(s) do not resolve: {bad_names}")
    print("  Every reading below would be a silent default, not a measurement. Fix the names")
    print("  (`audit_flag_names.py`) before believing anything this probe prints.")
    raise SystemExit(2)

rows = [read_era(ANCHOR), read_era(WRONG_ERA)]

print("\n1. THE ERA, read on both saves")
for r in rows:
    if r.get("error"):
        print(f"   {r['save']:<20} ‼ {r['error']}")
        continue
    print(f"   {r['save']:<20} map={r['map_enum']}{r['tile']} badges={r['badges']}")
    print(f"   {'':<20} {HARBOR_VAR}={r['harbor_state']}  {CITY_VAR}={r['city_state']}  "
          f"groudon={r['groudon']}  aqua_entrance_already_open={r['aqua_unblocked']}")

anchor, wrong = rows[0], rows[1]
verdict: list[str] = []

if anchor.get("error"):
    print(f"\n‼ THE ANCHOR IS MISSING ({ANCHOR}). Make it with:")
    print("    PYTHONUTF8=1 py -3.12 story_harness.py magma_door.ss1 --driver magmahideout \\")
    print("        --frames 2500000 --profile mh-anchor")
    print("  It is captured only on `groudon=True`, so a failed run cannot produce a bad one.")
    raise SystemExit(1)

print("\n2. THE GATE — every harbor coord trigger requires VAR_SLATEPORT_HARBOR_STATE == 1")
gate_ok = anchor["harbor_state"] == 1
print(f"   anchor reads {anchor['harbor_state']}  ->  {'PASS' if gate_ok else '‼ FAIL'}")
if not gate_ok:
    verdict.append(
        f"{HARBOR_VAR} is {anchor['harbor_state']}, not 1"
        + ("  (== 2 means the scene ALREADY RAN on this save)"
           if anchor["harbor_state"] == 2 else "")
    )

print("\n3. ERA CONTROL — the two saves must DISAGREE, or the reader sees nothing")
if wrong.get("error"):
    print(f"   ‼ {WRONG_ERA} missing — NO ERA CONTROL. Treat check 2 as unconfirmed.")
    verdict.append("no era control (the negative-arm save is missing)")
else:
    differ = anchor["harbor_state"] != wrong["harbor_state"]
    print(f"   {ANCHOR}={anchor['harbor_state']}  vs  {WRONG_ERA}={wrong['harbor_state']}"
          f"  ->  {'PASS (they differ)' if differ else '‼ FAIL (identical)'}")
    if not differ:
        verdict.append("the era control failed — both saves read the same value, so this "
                       "probe is not tracking the var it claims to")

print("\n4. THE BEAT HAS NOT HAPPENED YET — the Aqua Hideout entrance must still be BLOCKED")
print("   (the harbor scene is what sets these; if they are set, the anchor is one beat LATE)")
fresh = not anchor["aqua_unblocked"]
print(f"   set flags: {anchor['aqua_unblocked'] or 'none'}  ->  {'PASS' if fresh else '‼ FAIL'}")
if not fresh:
    verdict.append(f"the harbor scene already ran: {anchor['aqua_unblocked']}")

print("\n5. CORROBORATION — the other two things Maxie's defeat sets")
print(f"   groudon={anchor['groudon']}  {CITY_VAR}={anchor['city_state']}"
      f"  ->  {'PASS' if anchor['groudon'] and anchor['city_state'] == 1 else 'note'}")
if not anchor["groudon"]:
    verdict.append("GROUDON_AWAKENED_MAGMA_HIDEOUT is not set — this is not a post-Maxie save")

print("\n6. STATIC REACH inside SLATEPORT_CITY_HARBOR (planner sanity, NOT proof)")
print(f"   PATH CONTROL  door{DOOR} -> {CONTROL_TILE}: {plan(DOOR, CONTROL_TILE)}")
print(f"   door{DOOR} -> trigger3{TRIGGER3}: {plan(DOOR, TRIGGER3)}")
print("   ‼ A static YES means 'worth driving', not 'proven' — the Jagged Pass door read")
print("     '2 waypoints' while sealed shut by a setmetatile.")

print("\n" + line)
if verdict:
    print("VERDICT: DO NOT BUILD §Ch16 ON THIS ANCHOR —")
    for v in verdict:
        print(f"  * {v}")
    raise SystemExit(1)
print(f"VERDICT: READY. {ANCHOR} is the correct era for §Ch16 "
      f"({HARBOR_VAR}=1, scene not yet run, era control passed).")
print(line)
