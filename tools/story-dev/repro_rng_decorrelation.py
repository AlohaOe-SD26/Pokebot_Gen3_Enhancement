"""Prove the naming-screen RNG decorrelation knob (#24-x4 / story intro).

WHY IT EXISTS (verified against pokeemerald @ 83df84e4, 2026-07-26 — not assumed):
Emerald's `gRngValue` is 0 at every hard reset, is NOT RTC-seeded (`SeedRngWithRtc` is
inside `#ifdef BUGFIX`, and `include/config.h:48` leaves BUGFIX undefined), and its only
single-player reseed is `SeedRng(REG_TM1CNT_L)` when the player's name is CONFIRMED
(`src/main.c:208-214` + `src/naming_screen.c:412,701`). So two runs of our intro driven by
the same frame-aligned script produce a bit-identical game — four x4 lanes would be ONE
sample, not four — unless something varies the cycles between naming-screen open and
confirm. That is what `intro._rng_decorrelation_frames()` does.

This cannot run the emulator on a dev box, so it checks the knob's contract and the
arithmetic the design rests on.
"""
import math
import os
import sys
import types
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

for name in ("mgba", "mgba.audio", "mgba.core", "mgba.gba", "mgba.image",
             "mgba.log", "mgba.png", "mgba.vfs"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["mgba"].ffi = types.SimpleNamespace()
sys.modules["mgba"].lib = types.SimpleNamespace()
sys.modules["mgba"].libmgba_version_string = lambda: "stub"

from modules.story import intro  # noqa: E402

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


ENV = intro._RNG_DECORRELATION_ENV
os.environ.pop(ENV, None)

print("== the default is a random pause inside the documented bound ==")
values = {intro._rng_decorrelation_frames() for _ in range(400)}
check(all(0 <= v <= intro.RNG_DECORRELATION_MAX_FRAMES for v in values),
      f"every value is within 0..{intro.RNG_DECORRELATION_MAX_FRAMES}")
check(len(values) > 50, f"it actually varies ({len(values)} distinct values in 400 draws)")

print("\n== the env override pins it (for reproducing a bug from a cold start) ==")
os.environ[ENV] = "0"
check({intro._rng_decorrelation_frames() for _ in range(50)} == {0},
      "POKEBOT_RNG_DECORRELATION_FRAMES=0 disables it entirely — fully deterministic runs")
os.environ[ENV] = "37"
check({intro._rng_decorrelation_frames() for _ in range(50)} == {37}, "an explicit value is honoured exactly")
os.environ[ENV] = "-5"
check({intro._rng_decorrelation_frames() for _ in range(20)} == {0}, "a negative value clamps to 0")
os.environ[ENV] = "not-a-number"
values = {intro._rng_decorrelation_frames() for _ in range(200)}
check(all(0 <= v <= intro.RNG_DECORRELATION_MAX_FRAMES for v in values),
      "garbage in the env falls back to the random default instead of raising")
os.environ.pop(ENV, None)

print("\n== the arithmetic the design rests on ==")
# One GBA frame = 228 scanlines x 1232 cycles. The seed is a u16 read from Timer 1
# running at 1 tick/cycle, so each idle frame shifts the seed by (cycles mod 2^16).
CYCLES_PER_FRAME = 228 * 1232
SHIFT = CYCLES_PER_FRAME % 65536
check(CYCLES_PER_FRAME == 280_896, f"a GBA frame is 280,896 cycles (got {CYCLES_PER_FRAME:,})")
check(SHIFT == 18_752, f"so one idle frame shifts the seed by 18,752 (got {SHIFT:,})")

stride = math.gcd(SHIFT, 65536)
distinct = 65536 // stride
check(stride == 64, f"gcd(18752, 65536) == 64 (got {stride})")
check(distinct == 1024, f"so the reachable seeds cycle every 1,024 frames (got {distinct})")
check(intro.RNG_DECORRELATION_MAX_FRAMES < distinct,
      f"the default bound ({intro.RNG_DECORRELATION_MAX_FRAMES}) stays inside one cycle, "
      f"so every value in range is a DISTINCT seed")

seeds = {(f * SHIFT) % 65536 for f in range(intro.RNG_DECORRELATION_MAX_FRAMES + 1)}
check(len(seeds) == intro.RNG_DECORRELATION_MAX_FRAMES + 1,
      f"all {intro.RNG_DECORRELATION_MAX_FRAMES + 1} reachable pauses give distinct seeds "
      f"(got {len(seeds)})")
closest = min(abs(a - b) for a in seeds for b in seeds if a != b)
print(f"  note: the two closest reachable seeds are {closest} apart (a multiple of the "
      f"{stride}-step lattice)")

# ‼ Seed DISTANCE is not the property that matters, and an earlier version of this test
# asserted a minimum gap — a metric invented rather than derived. What matters is that the
# resulting STREAMS diverge: `Random()` returns the HIGH 16 bits of
# ISO_RANDOMIZE1(state) = 1103515245*state + 24691, which scrambles neighbouring seeds
# immediately. So check the outputs, not the inputs.
MASK = 0xFFFFFFFF


def lcg_stream(seed, steps):
    state = seed
    out = []
    for _ in range(steps):
        state = (1103515245 * state + 24691) & MASK
        out.append(state >> 16)
    return out


pair = sorted(seeds)[:2]
a_stream, b_stream = lcg_stream(pair[0], 20), lcg_stream(pair[1], 20)
check(a_stream[0] != b_stream[0],
      f"the two CLOSEST seeds diverge on the very first draw ({a_stream[0]} vs {b_stream[0]})")
check(sum(1 for x, y in zip(a_stream, b_stream) if x == y) == 0,
      "and share no value across the first 20 draws")

all_first = {lcg_stream(s, 1)[0] for s in seeds}
check(len(all_first) == len(seeds),
      f"all {len(seeds)} reachable pauses give a different FIRST draw (got {len(all_first)})")

print("\n== the delay is wired in AFTER typing and BEFORE the confirm ==")
# The seed is taken when the name is CONFIRMED, so a pause placed anywhere earlier is
# discarded by SeedRng. Assert the ORDER in the source rather than trusting the comment.
source = (SANDBOX / "modules" / "story" / "intro.py").read_text(encoding="utf-8")
i_type = source.index("type_in_naming_screen(name")
i_delay = source.index("_rng_decorrelation_frames()", i_type)
i_confirm = source.index("confirming the name and riding", i_delay)
check(i_type < i_delay < i_confirm,
      "order in intro.py is: type name -> decorrelation pause -> confirm")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
