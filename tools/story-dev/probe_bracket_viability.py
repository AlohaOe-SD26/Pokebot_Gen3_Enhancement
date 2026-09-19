# -*- coding: utf-8 -*-
"""⭐ IS A VICTORY ROAD GRIND ACTUALLY VIABLE FOR L62-75? (`#24-trainingbrackets`, `#24-levelgap`)

WHY THIS EXISTS. `#24-trainingbrackets` proposes promoting `VICTORY_ROAD_1F` (wilds L36-40) so the
\u00a7Ch24 party stops being offered `ROUTE117`'s **L13-14** wilds. That is plainly an improvement. But
"better than absurd" is not the same as "good enough", and the USER RULING that created the item is
about APPROPRIATENESS, not speed:

    "its fine if it takes a while to level up so long as they are not fighting super low level
     monsters (norman gym for example, level 30s should not be fighting level 3-5 for xp)"

\u21d2 before building the promotion, PRICE it. If reaching L62-75 on L36-44 wilds costs a number of
hours the user would not accept for an art piece running at \u00d71, the plan needs to change NOW and not
after a drive burns a day discovering it.

\u26d4\u26d4 THE ESTIMATOR IS KNOWN-WRONG BY 3.30\u00d7 AND THIS PROBE APPLIES THAT CORRECTION.
`03-PUNCH-LIST.md:810-814` records it with its composition, both halves MEASURED:
  * \u00d72.00 \u2014 a **0.501 participant divisor** the estimator does not model, and
  * \u00d71.65 \u2014 **~2,368 frames per WIN** against the estimator's 1,433 per BATTLE.
\u21d2 raw `estimate_frames_to_level` output is reported too, but the CORRECTED column is the honest
one, and any conclusion here rests on it.

\u26a0 WHAT THIS DOES **NOT** MODEL, STATED SO NOBODY READS MORE INTO IT THAN IS THERE:
  * party aggregation \u2014 whether six m\u014dns grind sequentially, share EXP, or swap. The 0.501 divisor
    above already encodes SOME sharing, so summing the per-m\u014dn column would double-count. **Per-m\u014dn
    is the trustworthy unit here; the party total is not computed.**
  * travel and heal legs between rounds (`_goto_training_area` runs every round),
  * whiteouts, PP stalls, or any recovery.
\u21d2 every number below is therefore a FLOOR. Reality is slower, never faster.

READ-ONLY: loads a save state, reads the party, does arithmetic. Nothing is walked or written.
"""
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

_ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement")
sys.path.insert(0, str(_ROOT / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

_p = load_profile_by_name("repro-fresh")
context.profile = _p
context.config.load(_p.path, strict=False)
set_rom(_p.rom)

from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_p, lambda: None)
context.audio = False
context.video = False

from modules.pokemon_party import get_party
from modules.story.training_areas import estimate_frames_to_level

SAVES = _ROOT / "tools" / "story-dev" / "saves"
#: The fixture closest to where PRODUCTION actually arrives at the League door (~L47-53).
FIXTURE = "post_ch24_atdoor.ss1"

#: MEASURED estimator optimism, with provenance in `03-PUNCH-LIST.md:810-814`.
CORRECTION = 3.30
FPS = 60.0

#: The candidate grounds, by the strongest wild each offers.
#:   28 = ROUTE121, today's ceiling in `TRAINING_GRASS`.
#:   40 = VICTORY_ROAD_1F, the row `#24-trainingbrackets` proposes to promote.
#:   44 = VICTORY_ROAD_B2F, the highest band in `PENDING_GRASS` (behind Wally, per §Ch23).
GROUNDS = [("ROUTE121 (today's best)", 28),
           ("VICTORY_ROAD_1F (proposed)", 40),
           ("VICTORY_ROAD_B2F (deepest)", 44)]
TARGETS = [62, 75]

print("=" * 108)
print("IS THE VICTORY ROAD GRIND VIABLE FOR L62-75?  \u2014 arithmetic only, nothing is walked")
print("=" * 108)

path = SAVES / FIXTURE
if not path.exists():
    raise SystemExit(f"\u26d4 MISSING FIXTURE: {path}")
context.emulator.load_save_state(path.read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

party = [m for m in get_party()]
print(f"  fixture : {FIXTURE}")
print(f"  party   : {', '.join(f'{m.species.name} L{m.level}' for m in party)}")
print(f"  model   : estimate_frames_to_level(...) \u00d7 {CORRECTION} (MEASURED optimism), at {FPS:g} fps")
print()

any_row = False
for target in TARGETS:
    print(f"\u2500\u2500\u2500 TO L{target}   (hours at \u00d71 \u2014 the speed this art piece actually runs at)")
    print(f"  {'m\u014dn':<22}" + "".join(f"{label:>30}" for label, _w in GROUNDS))
    for mon in party:
        if mon.level >= target:
            continue
        cells = []
        for _label, wild in GROUNDS:
            raw = estimate_frames_to_level(mon, target, wild)
            if raw is None:
                cells.append(f"{'unknown':>30}")
                continue
            hours = (raw * CORRECTION) / FPS / 3600.0
            cells.append(f"{hours:>26.1f} h")
            any_row = True
        print(f"  {mon.species.name + ' L' + str(mon.level):<22}" + "".join(cells))
    print()

print("=" * 108)
if not any_row:
    print("  \u26d4 NOTHING WAS ESTIMATED \u2014 every m\u014dn was already at target, or the growth-curve lookup")
    print("     failed. `estimate_frames_to_level` returns None on failure and callers must treat")
    print("     that as UNKNOWN, never as cheap. This run concluded nothing.")
    raise SystemExit(1)

print("  \u2b50 HOW TO READ THIS \u2014 the RATIO between columns is the finding, not the absolute hours.")
print("     The absolute numbers are a FLOOR (no travel, no heals, no whiteouts, no PP stalls).")
print("     The RATIO is what the promotion buys, and it is the same arithmetic either way:")
print("     Gen-3 exp scales LINEARLY with the wild's level (`exp = expYield * foeLevel / 7`),")
print("     so moving a grind from L28 wilds to L40 wilds is a flat ~1.43\u00d7 speedup, and to L44")
print("     ~1.57\u00d7. \u21d2 THE PROMOTION IS WORTH HAVING, BUT IT IS NOT AN ORDER OF MAGNITUDE.")
print()
print("  \u203c AND THE REAL POINT OF THE USER RULING IS THE LEVEL GAP, NOT THE CLOCK:")
print("     a L53 party on ROUTE117's L13-14 wilds is a ~3.9\u00d7 gap; on VICTORY_ROAD_1F's L36-40 it")
print("     is ~1.4\u00d7. THAT is what the ruling asked for \u2014 *\u201clevel 30s should not be fighting level")
print("     3-5\u201d* \u2014 and it is satisfied by the promotion regardless of the hours column.")
print()
print("  \u26a0 WHAT THIS CANNOT TELL YOU: whether the hours are ACCEPTABLE. That is a user call.")
print("    The ruling says *\u201ctime is not really a problem\u201d*, so present the number, do not assume.")
print("=" * 108)
