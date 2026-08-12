"""Does the chapter registry name the RIGHT next beat around the Mossdeep gym?

‼ WHY THIS EXISTS. `modules/story/chapters.py` is the machine-readable story ladder, and
`modules/story/progress.py` reports "the current chapter" as **the first chapter in that list whose
milestone is not yet met**. `_compute_badges_before()` likewise derives how many badges a chapter is
attempted with by walking the same list. So the ORDER of that list is not cosmetic — two consumers
read meaning out of it.

The registry lists **"Mossdeep & Space Center" (milestone `RECEIVED_HM_DIVE`) BEFORE "Gym 7 — Tate &
Liza" (milestone `BADGE07_GET`)**. That order cannot be right: the Space Center's Team Magma and
Steven are HIDDEN until the gym is beaten. `MossdeepCity_Gym_EventScript_TateAndLizaDefeated`
(`data/maps/MossdeepCity_Gym/scripts.inc:73-76`) is what clears
`FLAG_HIDE_MOSSDEEP_CITY_TEAM_MAGMA`, `FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_1F_TEAM_MAGMA`,
`FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_2F_TEAM_MAGMA` and
`FLAG_HIDE_MOSSDEEP_CITY_SPACE_CENTER_2F_STEVEN`. Before the badge there is literally nobody at the
Space Center to fight.

Rather than argue from the decomp, this probe ASKS THE DETECTOR, on two real saves that bracket the
gym:
  * `post_aqua.ss1`  — 6 badges, Dive not received. The correct next beat is **the GYM**.
  * `post_mossdeep_gym.ss1` — 7 badges, Dive not received. The correct next beat is **the SPACE
    CENTER**.
A registry in the right order names each of those correctly. The current one cannot: whatever it
says for the second save, it must say the same thing for the first.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_chapter_order.py
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

from modules.memory import get_event_flag
from modules.story.chapters import BADGES_BEFORE, CHAPTERS
from modules.story.progress import detect_live

SAVES = REPO / "tools" / "story-dev" / "saves"
line = "=" * 96

#: ‼ ONLY THE SECOND CASE IS ASSERTED, and the reason is worth stating. `current_chapter()` brackets
#: by BADGE LEVEL and then returns the first UNMET chapter in that bracket — so at six badges the
#: answer is whichever six-badge milestone is unmet earliest, which is a question about milestone
#: accuracy further back in the ladder, not about this ordering bug. Asserting on it would make the
#: probe fail for a reason it does not test. (It currently reports ch16 "To Lilycove" on a save that
#: has plainly been to Lilycove — a separate, real question, filed rather than fixed here.)
CASES = [
    ("post_aqua.ss1", None, "6 badges, no Dive — informational only; see the note above"),
    ("post_mossdeep_gym.ss1", "Mossdeep & Space Center", "7 badges, no Dive: the SPACE CENTER is next"),
]

#: A HIDE_ flag reading True means the object is HIDDEN. This is the EVIDENCE for the correct order,
#: measured in our own harness rather than taken on trust from the decomp.
GATE_FLAGS = [
    "HIDE_MOSSDEEP_CITY_SPACE_CENTER_1F_TEAM_MAGMA",
    "HIDE_MOSSDEEP_CITY_SPACE_CENTER_2F_TEAM_MAGMA",
    "HIDE_MOSSDEEP_CITY_SPACE_CENTER_2F_STEVEN",
]

print(line)
print("CHAPTER REGISTRY ORDER — does the detector name the right next beat?")
print(line)

print("\nthe registry's own order around the gym:")
for chapter in CHAPTERS:
    if chapter.order in (22, 23, 24, 25):
        print(f"  order {chapter.order}  ch{chapter.key:<3} {chapter.name:<34} "
              f"milestone={chapter.complete.name:<32} badges_before={BADGES_BEFORE[chapter.key]}")

results = []
for save_name, expected, why in CASES:
    path = SAVES / save_name
    if not path.exists():
        print(f"\n  ‼ {save_name} missing — skipping")
        continue
    context.emulator.load_save_state(path.read_bytes())
    for _ in range(60):
        context.emulator.run_single_frame()
    progress = detect_live()
    badges = sum(1 for n in range(1, 9) if get_event_flag(f"BADGE0{n}_GET"))
    dive = get_event_flag("RECEIVED_HM_DIVE")
    hidden = [name for name in GATE_FLAGS if get_event_flag(name)]
    print(f"\n  {save_name}")
    print(f"    badges={badges}  RECEIVED_HM_DIVE={dive}   ({why})")
    print(f"    Space Center objects HIDDEN: {len(hidden)}/{len(GATE_FLAGS)} — Team Magma and Steven "
          f"{'do NOT exist yet' if hidden else 'are present'}")
    print(f"    detector says : ch{progress.chapter_key} '{progress.chapter_name}'")
    if expected is None:
        print("    (not asserted — see the note on CASES)")
        continue
    ok = progress.chapter_name == expected
    results.append((save_name, ok))
    print(f"    should say    : '{expected}'")
    print(f"    -> {'OK' if ok else 'WRONG'}")

print("\n" + line)
print("VERDICT")
print(line)
wrong = [name for name, ok in results if not ok]
print(f"\n  {len(results) - len(wrong)} / {len(results)} saves get the right next beat")
if wrong:
    print(f"  ‼ WRONG for: {wrong}")
    print("\n  This is the ordering bug: the registry lists the Space Center before the gym, so the")
    print("  detector names a beat whose NPCs the game has not yet spawned. `badges_before` is")
    print("  derived from the same order, so it is wrong too — the Space Center is attempted with")
    print("  SEVEN badges, not six.")
else:
    print("  The registry order is consistent with the game's own gating.")
print(line)
sys.exit(0 if not wrong else 1)
