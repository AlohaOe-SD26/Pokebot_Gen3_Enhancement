r"""GATE (ROM) — §Ch23 leg 5 must NOT re-fire from the League plateau, and MUST still fire from the south (2026-09-26).

WHY (`ai-research-notes/2026-09-26-ch23money-RECON.md` §4): after a refusal at the League door (18,6), a re-entry of the
§Ch23 chapter skipped legs 1-4 and training, and the old leg-5 guard `not at_b1f_doorstep() and (EG or VR1F)` then
FIRED from the plateau, aiming at the Victory Road apron (18,42), which is unreachable from there — the chapter raised
instead of going on to legs 10-11. The fix is `victory_road.leg5_should_fire()`: with Wally beaten AND no path to the
apron (`on_league_plateau()`), the bot is past leg 5.

  C1  PLATEAU fixtures (Wally beaten, on the League side): the fixed guard SKIPS leg 5;
  C2  the `POKEBOT_CH23_FAULT_REENTRY` arm restores the old guard, which FIRES there (the arm bites; the fix is
      load-bearing);
  C3  SOUTH controls MUST still fire leg 5 — `ki90_whiteout_at_evergrande` (Wally beaten, respawned at the south Poké
      Center: the case `wally_beaten()` alone would get WRONG) and `post_ever_grande` (Wally not yet beaten);
  C4  the readings behind each verdict (`wally_beaten`, `on_league_plateau`) match the fixture's known position;
  C5  an UNREADABLE position (`POKEBOT_CH23_FAULT_PLATEAUREAD` raises inside the read) does NOT escape the guard: on a
      plateau fixture `on_league_plateau()` returns False and leg 5 FIRES — the pre-fix behaviour, never a crash
      (adversarial review 2026-09-26: `get_player_location()` can raise a plain RuntimeError mid map change).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch23_leg5_reentry.py
"""
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import create_profile, load_profile_by_name, profile_directory_exists  # noqa: E402
from modules.roms import list_available_roms  # noqa: E402

PROFILE = "leg5reentryprobe"
if not profile_directory_exists(PROFILE):
    create_profile(PROFILE, list_available_roms()[0])
profile = load_profile_by_name(PROFILE)
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)
from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"
# ⛔ A registered emulator gate must run UNTHROTTLED (`probe_gate_unthrottled.py`).
context.emulation_speed = 0

from modules.map_data import MapRSE  # noqa: E402
from modules.player import get_player_avatar  # noqa: E402
from modules.story import victory_road as VR  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
#: (fixture, side, expected with the fix, expected with the REENTRY arm, expected wally_beaten, expected plateau)
CASES = [
    ("post_league_heal.ss1", "plateau", False, True, True, True),
    ("post_ch24_atdoor.ss1", "plateau", False, True, True, True),
    ("post_league_shop.ss1", "plateau", False, True, True, True),
    ("ki90_whiteout_at_evergrande.ss1", "south", True, True, True, False),
    ("post_ever_grande.ss1", "south", True, True, False, False),
]
failures: list = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
    print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def main() -> int:
    print("=" * 100)
    print("GATE (ROM) — §Ch23 leg 5 re-entry: skip on the plateau, fire in the south")
    print("=" * 100)
    for name, side, want_fix, want_arm, want_wally, want_plateau in CASES:
        path = SAVES / name
        if not path.exists():
            check(False, f"{name}: fixture MISSING")
            continue
        context.emulator.load_save_state(path.read_bytes())
        for _ in range(30):
            context.emulator.run_single_frame()
        av = get_player_avatar()
        try:
            where = f"{MapRSE(tuple(av.map_group_and_number)).name} {tuple(av.local_coordinates)}"
        except ValueError:
            where = str((tuple(av.map_group_and_number), tuple(av.local_coordinates)))
        os.environ.pop("POKEBOT_CH23_FAULT_REENTRY", None)
        wally, plateau, fix = VR.wally_beaten(), VR.on_league_plateau(), VR.leg5_should_fire()
        os.environ["POKEBOT_CH23_FAULT_REENTRY"] = "1"
        try:
            arm = VR.leg5_should_fire()
        finally:
            os.environ.pop("POKEBOT_CH23_FAULT_REENTRY", None)
        print(f"\n  {name} — {where} ({side}): wally_beaten={wally} on_league_plateau={plateau} "
              f"leg5(fix)={fix} leg5(REENTRY arm)={arm}")
        check((wally, plateau) == (want_wally, want_plateau),
              f"C4 {name}: readings (wally_beaten, plateau) = {(wally, plateau)}, expected {(want_wally, want_plateau)}")
        if side == "plateau":
            check(fix is False, f"C1 {name}: the fixed guard SKIPS leg 5 on the plateau")
            check(arm is True, f"C2 {name}: the REENTRY arm restores the old guard, which FIRES here")
            os.environ["POKEBOT_CH23_FAULT_PLATEAUREAD"] = "1"
            try:
                broken = (VR.on_league_plateau(), VR.leg5_should_fire())
                check(broken == (False, True), f"C5 {name}: an unreadable position fails toward the old guard "
                                               f"(plateau, leg5) = {broken}, expected (False, True)")
            except Exception as error:  # noqa: BLE001 - that IS the failure C5 exists to catch
                check(False, f"C5 {name}: the broken read ESCAPED the guard ({type(error).__name__})")
            finally:
                os.environ.pop("POKEBOT_CH23_FAULT_PLATEAUREAD", None)
        else:
            check(fix is True and arm is True, f"C3 {name}: leg 5 still FIRES in the south (both ways)")
    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
