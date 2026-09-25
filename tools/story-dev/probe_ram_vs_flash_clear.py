"""`#24-gameclearflag` — DO RAM AND FLASH AGREE ABOUT "THE GAME IS CLEARED"? OBSERVE-ONLY, OFFLINE.

P2 threw up an unpredicted reading: on `post_hall4_door.ss1`, `start_flash_game_clear = True` while
`start_champion = False` and `start_game_clear = False`. ⇒ the SAVE FILE claimed a cleared game on a
save that had not beaten the Champion.

⛔ THAT MATTERS BECAUSE THE TWO READS ANSWER DIFFERENT QUESTIONS AND ARE EASY TO CONFUSE:
  * `flag("SYS_GAME_CLEAR")`      -> RAM   (what `chapters.py:288` uses today)
  * `get_save_data().get_event_flag(...)` -> THE SAVE FILE, and `story_harness.py:19930` calls that
    *"a legitimate precondition gate"*.
If flash can be TRUE while RAM is FALSE, a flash-based gate reports a finished chapter on a save
that never finished it — and `#24-gameclearflag` is OPEN, so this lands squarely in its scope.

This reads BOTH, from the pinned fixtures, without running a frame of story.
‼ It reads a known-FALSE and a known-TRUE flag as CONTROLS, so a reader that returns a constant
cannot be mistaken for a working one.
"""
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

REPO = pathlib.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context  # noqa: E402
from modules.game import set_rom  # noqa: E402
from modules.profiles import load_profile_by_name  # noqa: E402

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.libmgba import LibmgbaEmulator  # noqa: E402

context.emulator = LibmgbaEmulator(profile, lambda: None)
context.audio = False
context.video = False
context.emulation_speed = 0
context.bot_mode = "Story"

from modules.memory import get_event_flag  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
BAR = "=" * 104

#: known-TRUE by this point in the story, and known-FALSE at every point — the controls.
CONTROLS = ["BADGE08_GET", "SYS_PC_LANETTE"]
SUBJECTS = ["SYS_GAME_CLEAR", "IS_CHAMPION"]

FIXTURES = [
    "post_hall4_door.ss1",
    "post_drake_L75.ss1",
    "post_glacia_L75.ss1",
    "post_sidney_L75.ss1",
    "post_ch24_atdoor_L75.ss1",
]


def ram(name):
    try:
        return bool(get_event_flag(name))
    except Exception as error:  # noqa: BLE001
        return f"<err {type(error).__name__}>"


def flash(name):
    try:
        from modules.save_data import get_save_data

        sd = get_save_data()
        if sd is None:
            return "<no save data>"
        return bool(sd.get_event_flag(name))
    except Exception as error:  # noqa: BLE001
        return f"<err {type(error).__name__}>"


print(BAR)
print("  `#24-gameclearflag` — RAM vs FLASH, read from the PINNED FIXTURES. OBSERVE-ONLY.")
print("  ⛔ A DISAGREEMENT IS THE FINDING: flash TRUE while RAM FALSE means a flash-based gate")
print("     would report a cleared game on a save that has not beaten the Champion.")
print(BAR)
hdr = f"  {'fixture':<28}" + "".join(f"{n[:18]:>20}" for n in SUBJECTS + CONTROLS)
print(hdr)
for fx in FIXTURES:
    p = SAVES / fx
    if not p.is_file():
        print(f"  {fx:<28} MISSING")
        continue
    context.emulator.load_save_state(p.read_bytes())
    for _ in range(30):
        context.emulator.run_single_frame()
    cells = []
    for n in SUBJECTS + CONTROLS:
        r, f = ram(n), flash(n)
        mark = "" if r == f else "  <DIFFER>"
        cells.append(f"{f'R={r} F={f}':>20}{mark}")
    print(f"  {fx:<28}" + "".join(cells))
print(BAR)
print("  ⛔ WHAT THIS DOES NOT SETTLE: which read is 'right'. They answer DIFFERENT questions —")
print("     RAM is the live game, flash is what a reboot would restore. The finding is only that")
print("     they CAN disagree, so a predicate must say WHICH it means and why.")
print(BAR)
