"""Regression test: a recovery guard budgeted EXACTLY like the watchdog can never fire.
NO EMULATOR — both numbers are read straight out of the source files.

WHAT WENT WRONG (measured 2026-07-31 from stored batch logs; see 05-KNOWN-ISSUES KI-43).

`_navigate_when_ready` (added by `fea2bb19`, `#24-journey` part 3) wraps every
`navigate_to` call and WAITS for the overworld instead of letting `navigate_to` raise:

    while get_game_state() is not GameState.OVERWORLD or not player_avatar_is_controllable():
        waited += 1
        if waited > _MAX_NON_OVERWORLD_FRAMES:
            break            # "so a genuine softlock still surfaces rather than yielding for ever"
        yield

Its docstring promises the break makes a genuine softlock surface. It cannot:

    _MAX_NON_OVERWORLD_FRAMES = 60 * 60 * 5   = 18,000   (global_navigation.py)
    StoryMode global watchdog: _stall_frames >= 18,000    (story_mode.py)

THE SAME NUMBER. The wrapper presses no buttons and changes no state, so map, coords,
game state, progress signature and `context.message` all stay frozen while it waits —
which is precisely the watchdog's stall signature. The watchdog fires ON frame 18,000
(`>=`); the break needs frame 18,001 (`>`). The watchdog wins the race by one frame,
EVERY time. The escape hatch is unreachable code.

MEASURED CONSEQUENCE — this is not theoretical. Comparing the two stored batches:

    baseline  x4-runs/20260731-105549 (289d1710, no wrapper)  global watchdog:  5
    batch3    x4-runs/20260731-170603 (3875843c, wrapper)     global watchdog: 72

    RUSTBORO_CITY_MART, stage 3, right after "bought Poké Balls":
        baseline  33 / 33 purchase runs completed cleanly
        batch3    36 / 36 went straight to the watchdog derail — 100%

The bot buys Poké Balls in batches of ten to farm the free Premier Ball each purchase
gives. Baseline chained three purchases (0→10, 11→21, 22→32). Batch3 NEVER made a second
purchase: every one of its 36 buys is a first buy. The second `buy_poke_balls` call opens
with `_navigate_riding_out(mart_map, approach)` while the avatar is still settling out of
the shop UI and is therefore not controllable — the wrapper then sits on it for the full
18,000 frames and the watchdog derails the run.

So the cost is not only the ~1.2% of batch frames burned waiting. Every restock buys 10
balls instead of 30, loses 2 free Premier Balls, and spends a derail out of the budget
that protects against genuine stuck loops.

THE RULE THIS FILE PINS: any bounded wait that changes NOTHING while it waits must expire
comfortably INSIDE the watchdog's stall window, or the derail always pre-empts it and the
bound is decoration. Equal budgets are not "generous", they are unreachable.

‼ THIS TEST IS RED ON PURPOSE until the cap is lowered. Reproduce first, then fix.
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"

NAV = SANDBOX / "modules" / "modes" / "util" / "global_navigation.py"
STORY = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def _read(path: pathlib.Path) -> str:
    if not path.exists():
        raise SystemExit(f"repro cannot run: missing {path}")
    return path.read_text(encoding="utf-8")


nav_src = _read(NAV)
story_src = _read(STORY)

print("1. both budgets are still where this test thinks they are")

# `_MAX_NON_OVERWORLD_FRAMES = 60 * 60 * 5` — evaluate the literal arithmetic, don't
# import: importing the module drags in the emulator-facing package and this test is
# deliberately emulator-free.
m = re.search(r"^_MAX_NON_OVERWORLD_FRAMES\s*=\s*([0-9*\s]+)", nav_src, re.M)
check("global_navigation defines _MAX_NON_OVERWORLD_FRAMES", m is not None)
wrapper_cap = eval(m.group(1).strip(), {"__builtins__": {}}, {}) if m else None  # noqa: S307
print(f"       wrapper cap      = {wrapper_cap:,} frames" if wrapper_cap else "")

m2 = re.search(r"_stall_frames\s*>=\s*([0-9_]+)", story_src)
check("story_mode defines the global-watchdog stall threshold", m2 is not None)
watchdog = int(m2.group(1).replace("_", "")) if m2 else None
print(f"       watchdog stall   = {watchdog:,} frames" if watchdog else "")

# If the guard is ever deleted this test must not go quietly green.
check(
    "_navigate_when_ready still exists (this test guards ITS budget)",
    "_navigate_when_ready" in nav_src,
    "if it was removed on purpose, delete this repro and say so in 08-MISTAKES",
)
check(
    "the wrapper still waits without pressing anything",
    "player_avatar_is_controllable()" in nav_src and "waited > _MAX_NON_OVERWORLD_FRAMES" in nav_src,
)

print("2. ‼ THE DEFECT — the guard must expire BEFORE the watchdog, or it never runs")

if wrapper_cap is not None and watchdog is not None:
    check(
        "wrapper cap is strictly below the watchdog threshold",
        wrapper_cap < watchdog,
        f"{wrapper_cap:,} vs {watchdog:,} — equal or larger means the derail always "
        f"wins and the `break` is dead code",
    )
    # One frame of margin would technically pass the check above while still being
    # useless in practice: the point of the break is that `navigate_to` gets to raise
    # its own honest error ("not in the overworld") so `_navigate_riding_out` can spend
    # a retry on it. That needs real headroom, not a photo finish.
    check(
        "wrapper cap leaves real headroom (<= half the watchdog window)",
        wrapper_cap <= watchdog // 2,
        f"{wrapper_cap:,} vs {watchdog // 2:,}",
    )
    # A battle transition — the condition this wrapper was built for — clears in a few
    # frames. Anything on the order of a minute is not waiting out a transient, it is
    # hiding a stuck state that should be reported.
    check(
        "wrapper cap is sized for a transient, not for a softlock (<= 1,800 frames / 30s)",
        wrapper_cap <= 1_800,
        f"{wrapper_cap:,} frames = {wrapper_cap / 60:.0f}s; the transition it exists for "
        f"clears in a few frames",
    )

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
