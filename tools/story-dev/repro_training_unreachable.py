"""REPRO for #24-regionreach — a wrong YES from the reachability oracle must cost ONE
WALK, not the RUN.

EVIDENCE (live batch 20260725-194810, 2 of 5 fresh runs died on this, identically):
    BotModeError -> Manual: Could not reach (25, 55) on MapRSE.ROUTE111: the field is
    idle and we are still at (22, 6), so retrying cannot change the result
    (Could not find a path from (22/6 @ MAUVILLE_CITY) to (25/55 @ ROUTE111).)

WHY IT HAPPENED. `training_areas.py` documents that tile as FALLARBOR-SIDE ONLY — it sits
NORTH of the Go-Goggles desert, which splits Route 111 into two disconnected halves — yet
`AREA_PREREQ` gates ROUTE111 as `"region"`, and `_training_area_allowed` answers "region"
with `region_reach.is_map_reachable(ROUTE111)`. That is TRUE from Mauville (the southern
half connects), so the gate passes and the walk then dies at the desert.

‼ The predicate's own docstring predicted a wrong YES would "cost ONE wasted walk, which
navigation then fails RECOVERABLY and loudly". The batch disproved it: the picker is
DETERMINISTIC, so every derail re-ran `_play`, re-picked the SAME unreachable tile and
failed identically, until the derail budget dropped the run to Manual. A wrong YES cost
the whole run.

WHAT THIS PROVES (pure decision test, no emulator — the same stand-in style as
`repro_boss_plateau.py`): after ONE failed relocation, the picker stops proposing that
ground FROM THAT STANDING POSITION, and — because reachability is directional — still
proposes it from a position it IS reachable from.

  1. BEFORE any failure, standing in Mauville: Route 111 is proposed (the live bug).
  2. The relocation raises `UnreachableDestinationError`; StoryMode records it.
  3. AFTER, standing in Mauville: Route 111 is NO LONGER proposed -> the deterministic
     death loop is broken.
  4. AFTER, standing in FALLARBOR: Route 111 IS still proposed -> the memory is keyed to
     where we stood and does not throw away a genuinely good training ground.
  5. `UnreachableDestinationError` is still a `BotModeError`, so every existing
     `except BotModeError` (StoryMode's derail recovery) keeps catching it.

Run: py -3.12 tools/story-dev/repro_training_unreachable.py
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.map_data import MapRSE
from modules.modes import BotModeError
from modules.story import training_areas
from modules.story.early_game import UnreachableDestinationError
import plugins.custom_modes.story_mode as sm

ROUTE111_TILE = (25, 55)
MAUVILLE = tuple(MapRSE.MAUVILLE_CITY.value)
FALLARBOR = tuple(MapRSE.FALLARBOR_TOWN.value)

failures = []


def check(label, cond):
    print(f"    {'PASS' if cond else 'FAIL'}  {label}")
    if not cond:
        failures.append(label)


class FakeStory:
    """Carries only the instance state the methods under test touch."""

    _here = MAUVILLE

    def __init__(self):
        self._training_unreachable = set()

    # the real methods, bound to this stand-in
    _note_training_unreachable = sm.StoryMode._note_training_unreachable
    _training_blocked = sm.StoryMode._training_blocked

    def _here_map(self):
        return self._here


def propose(story, team_level=34):
    """Run the REAL picker with the REAL predicate + the run-scoped blacklist, exactly as
    `_prepare_for_fight` composes them."""
    return training_areas.best_training_area(
        team_level,
        min_wild_max=0,
        allow=lambda m, t, p: (
            # `_training_area_allowed` needs live game state, so stand in for it with the
            # answer it demonstrably gave in the batch: ROUTE111 "region" -> True from
            # Mauville (region_reach says the MAP is reachable; the TILE is not).
            (p in (None, "region"))
            and not story._training_blocked(m, t)
        ),
    )


print("=" * 78)
print("CASE 1 -- BEFORE any failure, standing in MAUVILLE: Route 111 is proposed")
print("=" * 78)
story = FakeStory()
story._here = MAUVILLE
picked = propose(story)
print(f"    -> picked {picked[0].name if picked else None} {picked[1] if picked else ''}")
check(
    "Route 111 (25,55) is proposed from Mauville -- reproduces the live bug",
    picked is not None and picked[0] is MapRSE.ROUTE111 and tuple(picked[1]) == ROUTE111_TILE,
)

print()
print("=" * 78)
print("CASE 2 -- the failed relocation is recorded from a typed nav failure")
print("=" * 78)
try:
    raise UnreachableDestinationError(
        "Could not reach (25, 55) on MapRSE.ROUTE111: the field is idle and we are still "
        "at (22, 6), so retrying cannot change the result."
    )
except UnreachableDestinationError:
    story._note_training_unreachable(MapRSE.ROUTE111, ROUTE111_TILE)
print(f"    -> blacklist = {story._training_unreachable}")
check(
    "the (standing map, target map, tile) triple was recorded",
    (MAUVILLE, tuple(MapRSE.ROUTE111.value), ROUTE111_TILE) in story._training_unreachable,
)

print()
print("=" * 78)
print("CASE 3 -- AFTER, standing in MAUVILLE: Route 111 is NO LONGER proposed")
print("=" * 78)
story._here = MAUVILLE
picked_after = propose(story)
print(f"    -> picked {picked_after[0].name if picked_after else None} "
      f"{picked_after[1] if picked_after else ''}")
check(
    "the deterministic death loop is broken (Route 111 not re-proposed from Mauville)",
    picked_after is None or not (
        picked_after[0] is MapRSE.ROUTE111 and tuple(picked_after[1]) == ROUTE111_TILE
    ),
)

print()
print("=" * 78)
print("CASE 4 -- AFTER, standing in FALLARBOR: Route 111 IS still proposed")
print("=" * 78)
story._here = FALLARBOR
picked_fallarbor = propose(story)
print(f"    -> picked {picked_fallarbor[0].name if picked_fallarbor else None} "
      f"{picked_fallarbor[1] if picked_fallarbor else ''}")
check(
    "reachability is directional -- a good ground is not thrown away run-wide",
    picked_fallarbor is not None
    and picked_fallarbor[0] is MapRSE.ROUTE111
    and tuple(picked_fallarbor[1]) == ROUTE111_TILE,
)

print()
print("=" * 78)
print("CASE 5 -- UnreachableDestinationError is still a BotModeError")
print("=" * 78)
check(
    "existing `except BotModeError` handlers (derail recovery) still catch it",
    issubclass(UnreachableDestinationError, BotModeError),
)

print()
print("-" * 78)
if failures:
    print(f"FAILURES ({len(failures)}):")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS: a wrong YES from the reachability oracle now costs ONE walk, not the run,")
print("and the memory is keyed to where we stood so a directional ground survives.")
