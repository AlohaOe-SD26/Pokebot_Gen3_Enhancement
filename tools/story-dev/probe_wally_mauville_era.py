"""Which fixture is parked BEFORE the Mauville gym-door Wally — and is the flag read even honest?

‼ WHY THIS EXISTS (2026-09-13). 87% of run deaths (124 of 143 ended runs) are an 18,000-frame
watchdog at MAUVILLE_CITY, story stage "9: Mauville & the Bike". Across 41 batches from 2026-07-31
to 2026-09-10 the bot beat Wally on ~100% of the runs that met him; from commit `03b11b5b` onward
that collapsed to ~13%. To A/B the cause I need a fixture parked BEFORE that fight.

⛔ TWO TRAPS THIS PROBE EXISTS TO AVOID, both already paid for in this repo:
  1. **A FIXTURE CHOSEN BY NAME IS A GUESS.** `wally_done.ss1` sounds like the anchor and is NOT:
     it is the PETALBURG tutorial Wally (`badges=-`, PETALBURG_CITY_GYM). `probe_anchor_inventory`
     already burned two runs on name-picked anchors; see its docstring.
  2. **`get_event_flag` RETURNS FALSE FOR A NAME THAT DOES NOT EXIST.** A typo'd flag name reads
     as "not yet done" on EVERY save, which is exactly the answer I am hoping for — so the read
     would confirm my hypothesis by being broken. ⇒ the name is asserted against `_event_flags`
     BEFORE any save is read, and the run dies if it is absent.

⭐ AND A CONTROL PAIR, because "False everywhere" is indistinguishable from a dead read:
  a save that MUST have the flag SET (post-Wattson, badges=123 — Wattson cannot be beaten before
  Wally is) is read alongside the candidates. If the control does not come back True, this probe's
  verdict is worthless and it says so instead of reporting a result.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_wally_mauville_era.py
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

from modules.memory import _event_flags, get_event_flag
from modules.player import get_player_avatar

SAVES = pathlib.Path(__file__).resolve().parent / "saves"
LINE = "=" * 94

WALLY_FLAG = "DEFEATED_WALLY_MAUVILLE"

# (save, what we EXPECT of the Wally flag, why)
CANDIDATES = [
    ("mauville_prewattson.ss1", None, "badges=12, in MAUVILLE_CITY — the hoped-for A/B anchor"),
    ("stern_done.ss1", None, "badges=12, Slateport museum — one beat EARLIER, pre-Mauville"),
    ("slateport.ss1", None, "badges=12, Slateport — alternative pre-Mauville anchor"),
    ("batch3_run03_wedge.ss1", None, "badges=1234 in MAUVILLE — later era, sanity only"),
    # ⭐ THE CONTROL: Wattson is Gym 3. Wally gates his door, so badges=123 CANNOT be reached
    #    without the Wally flag. This MUST read True or the whole probe is lying.
    ("rocksmash_got.ss1", True, "CONTROL — badges=123 (post-Wattson): flag MUST already be set"),
]


def main() -> int:
    # --- gate 1: the flag NAME must exist, or every read below is a silent False ----------------
    names = sorted(n for n in _event_flags if "WALLY" in n.upper())
    print(LINE)
    print(f"  flags whose name contains WALLY ({len(names)}):")
    for n in names:
        print(f"     {n}")
    if WALLY_FLAG not in _event_flags:
        print(f"\n  ⛔ ABORT: {WALLY_FLAG!r} is NOT a real flag name. Every read would be a silent")
        print("     False — i.e. it would 'confirm' that no save has beaten Wally. Pick from above.")
        return 2
    print(f"\n  ✅ {WALLY_FLAG!r} is a real flag name — reads below are meaningful.")

    rows = []
    for save, expect, why in CANDIDATES:
        path = SAVES / save
        if not path.is_file():
            rows.append((save, "MISSING", "", "", expect, why))
            continue
        context.emulator.load_save_state(path.read_bytes())
        for _ in range(30):
            context.emulator.run_single_frame()
        avatar = get_player_avatar()
        flag = get_event_flag(WALLY_FLAG)
        badges = "".join(str(n) for n in range(1, 9) if get_event_flag(f"BADGE0{n}_GET")) or "-"
        where = f"{avatar.map_group_and_number} {avatar.local_coordinates}"
        try:
            where = f"{avatar.map_location.map_name} {avatar.local_coordinates}"
        except Exception:
            pass
        rows.append((save, where, badges, flag, expect, why))

    print(LINE)
    print(f"  {'save':28} {'badges':8} {'wallyFlag':10} {'where'}")
    for save, where, badges, flag, expect, why in rows:
        print(f"  {save:28} {str(badges):8} {str(flag):10} {where}")
        print(f"  {'':28} └─ {why}")

    # --- gate 2: the CONTROL must be True, else the read is dead and nothing here is usable -----
    print(LINE)
    ctl = [r for r in rows if r[4] is True]
    if not ctl:
        print("  ⛔ no control row ran — verdict WITHHELD.")
        return 2
    if not all(r[3] is True for r in ctl):
        print("  ⛔ CONTROL FAILED: a post-Wattson save reports the Wally flag UNSET.")
        print("     That is impossible in-game, so the READ is broken, not the saves.")
        print("     ⇒ VERDICT WITHHELD. Do not pick an anchor from this output.")
        return 1
    print("  ✅ control passed: the post-Wattson save reports the Wally flag SET, so a False")
    print("     below is a real 'not yet fought', not a dead read.")

    usable = [r for r in rows if r[3] is False and r[1] not in ("MISSING",)]
    print(LINE)
    if usable:
        print("  ⭐ ANCHORS PARKED BEFORE THE MAUVILLE WALLY FIGHT (flag False, control green):")
        for r in usable:
            print(f"     {r[0]:28} badges={r[2]:8} at {r[1]}")
    else:
        print("  ⚠ NO candidate is parked before the fight — every one already has the flag set.")
        print("    ⇒ the A/B needs a fixture captured earlier, or a fresh run to the gym door.")
    print(LINE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
