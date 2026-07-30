"""Proof for the #24-counters PHASE 2 EXECUTOR — the counter ladder, the catch-on-sight
branch, and (most importantly) THE BOUND.

Phase 1 diagnosed a boss it could not beat, named the counter, and ended the run — ~72%
of all derails in the 2026-07-29 batch. Phase 2 goes and gets it. That turns a bounded,
honest STOP into machinery that walks, spends balls and grinds, so the thing that most
needs proving is not that it works — it is that **it cannot run away**.

WHAT THIS PROVES — the real `_counter_ladder` and the real `StoryMode.on_battle_started`,
driven with the planner, the hunt and the trainer stubbed. It runs a headless emulator on
`norman_done.ss1`: no frames of gameplay are driven, but the battle-strategy constructors
on the fall-through paths read the live party, so a real save has to be under them (see
the note at the emulator set-up below — omitting it made the POSITIVE case silently fail).

  THE BOUND
  1. A successful hunt returns True, and the terminal `BotModeError` does NOT fire.
  2. ‼ A SECOND hopeless verdict for the SAME boss RAISES — even though the hunt would
     succeed again. This is the KI-34 shape: `_prepare_for_fight` is re-entered by the
     run loop after every lost attempt, so any per-call retry or frame budget becomes
     per-attempt, i.e. unbounded. The bound has to be per-RUN state, and this is the
     case that proves it is.
  3. The attempt is recorded BEFORE the hunt runs, so a hunt that DERAILS mid-flight
     (whiteout, navigation failure) still consumes its one chance instead of looping.
  4. `reset_per_run_state()` clears it — the NEXT run gets a fresh chance (the 2026-07-26
     per-run-state bug, which killed runs 4+ in every lane, is exactly this mistake).

  THE FALL-THROUGHS — every failure path reaches the SAME honest raise
  5. no huntable candidate  -> raises.  6. party full -> raises.
  7. no spare Poké Ball     -> raises.  8. planner throws -> raises (never a crash).
  9. hunt finds nothing     -> raises.

  THE CATCH-ON-SIGHT BRANCH (real `StoryMode.on_battle_started`)
 10. armed + target species + party room + a SPARE ball -> `StoryCatchStrategy`.
 11. a NON-target species is not caught; 12. a full party is not caught;
 13. one ball (the reserve) is not spent; 14. disarmed -> not caught.

  ARM / DISARM HYGIENE
 15. `hunt()` disarms in a `finally` even when the spin raises — a hunt that dies armed
     would keep spending balls on Machop for the rest of the run.

‼ NOT PROVEN HERE: that the bot can actually walk to Fiery Path from Petalburg, catch a
Machop and beat Norman with it. That needs a live run. What is proven is that every way
this can fail ends at the honest stop, and that it cannot loop.

Run: py -3.12 tools/story-dev/repro_counter_hunt.py
"""
import pathlib
import sys
from types import SimpleNamespace

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

_profile = load_profile_by_name("repro-ml")
context.profile = _profile
context.config.load(_profile.path, strict=False)
set_rom(_profile.rom)

# ‼ A REAL EMULATOR + SAVE STATE IS REQUIRED, even though this repro drives stubs.
# `on_battle_started`'s FALL-THROUGH paths construct real battle strategies
# (`StoryCatchStrategy`, `LevelUpTravelBattleStrategy`), whose `__init__` reads the live
# party through `state_cache`, which needs `context.emulator.get_frame_count()`. Without
# one, every negative case dies in the constructor instead of returning a verdict — and
# worse, `StoryCatchStrategy()` raising inside `on_battle_started`'s `except Exception:
# pass` made the POSITIVE case silently fall through too, so the branch looked broken
# when it was not. (Same trap as repro_sufficiency, 08-MISTAKES 2026-07-30.)
#
# Note the deliberate asymmetry that makes the stubs below work: the branch under test
# imports `get_party`/`get_item_bag` INSIDE the function, so it resolves them from the
# module at call time and sees the patches; `battle_strategies/default.py` did
# `from modules.pokemon_party import get_party` at import time, so its constructor keeps
# the REAL one and reads the real save. That is what lets one test fake a full party
# without breaking the strategy it falls through to.
from modules.libmgba import LibmgbaEmulator

context.emulator = LibmgbaEmulator(_profile, lambda: None)
context.audio = False
context.video = False
context.bot_mode = "Story"
context.emulator.load_save_state((REPO / "tools/story-dev/saves/norman_done.ss1").read_bytes())
for _ in range(30):
    context.emulator.run_single_frame()

from modules.modes import BotModeError

import modules.story.counter_hunt as counter_hunt
import modules.story.counter_plan as counter_plan
import plugins.custom_modes.story_mode as sm

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  {'PASS' if condition else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not condition:
        failures.append(label)


NORMAN = {
    "keys": [(0, 7)],
    "name": "Norman",
    "band": (28, 32),
    "ace_types": ("Normal",),
    "grass": ("GRASS_MAP", (1, 1)),
    "heal": "HEAL",
}
NEEDED = ["Fighting"]

MACHOP = {
    "species_name": "Machop",
    "types": ["Fighting"],
    "map_enum": SimpleNamespace(name="FIERY_PATH", pretty_name="Fiery Path"),
    "tile": None,
    "hunt_tile": (18, 19),
    "level_band": (15, 16),
    "encounter_rate": 15,
    "reachable": True,
    "huntable": True,
    "est_frames": 250297.0,
}
# What the ranking actually returns first for Norman — see repro_counter_huntable.
HARIYAMA = dict(MACHOP, species_name="Hariyama", hunt_tile=None, huntable=False,
                map_enum=SimpleNamespace(name="VICTORY_ROAD_B1F", pretty_name="Victory Road"),
                level_band=(38, 42), est_frames=4094.0)


class _Mode(SimpleNamespace):
    """A stand-in `self` carrying the real methods under test.

    Harvests every UPPERCASE constant and binds the REAL `_counter_ladder` /
    `reset_per_run_state`, per the `_StoryModeStub` pattern (08-MISTAKES 2026-07-30):
    hand-listed stubs rot, and a re-stubbed method tests a copy of the logic.
    """

    def __getattr__(self, name):
        raise AttributeError(
            f"repro_counter_hunt's stand-in `self` has no {name!r} — `_counter_ladder` "
            f"grew a dependency on StoryMode.{name}. Constants are harvested "
            f"automatically (must be UPPERCASE); bind real methods, never re-stub them."
        )


def make_mode() -> "_Mode":
    mode = _Mode(**{k: getattr(sm.StoryMode, k) for k in dir(sm.StoryMode) if k.isupper()})
    mode._counter_hunts = {}
    mode._counter_ladder = lambda cfg, losses, needed: sm.StoryMode._counter_ladder(
        mode, cfg, losses, needed
    )
    return mode


def drive(gen):
    """Run a generator to completion and return its `return` value."""
    try:
        while True:
            next(gen)
    except StopIteration as stop:
        return stop.value


def run_ladder(mode, *, candidates=MACHOP, hunt_result=0, planner_raises=False,
               blocker="__none__", hunt_raises=False, trained=True):
    """Drive the REAL `_counter_ladder` with the planner/hunt/trainer stubbed."""
    def fake_find(needed, allow=None, max_results=5):
        if planner_raises:
            raise RuntimeError("planner exploded")
        # Always include the un-huntable rank-1, so `best_huntable` is what does the work.
        return [HARIYAMA] + ([candidates] if candidates else [])

    def fake_hunt(candidate, needed):
        calls["hunt"] += 1
        if hunt_raises:
            raise BotModeError("navigation died mid-hunt")
        return hunt_result
        yield  # pragma: no cover - makes this a generator

    def fake_train(slot, cfg):
        calls["train"] += 1
        return trained
        yield  # pragma: no cover

    calls = {"hunt": 0, "train": 0}
    orig = (counter_plan.find_counter_candidates, counter_hunt.hunt,
            counter_hunt.train_counter, counter_hunt.hunt_blockers)
    counter_plan.find_counter_candidates = fake_find
    counter_hunt.hunt = fake_hunt
    counter_hunt.train_counter = fake_train
    # ‼ Only SIMULATE a blocker when the case asks for one. Replacing `hunt_blockers`
    # unconditionally was wrong: it is the real function that rejects a None candidate,
    # so stubbing it out let a "no huntable candidate" case walk into the hunt with
    # `candidate=None`. Keep the real guard in the loop for every other case.
    if blocker == "__none__":
        # ‼ FORCE "no blocker". Needed because `hunt_blockers` fails SAFE: with no live
        # party read it assumes the party is FULL, so on this harness the real guard
        # blocks everything — and case 9 ("the hunt finds nothing") would then pass for
        # entirely the wrong reason, never reaching the hunt at all.
        counter_hunt.hunt_blockers = lambda c: None
    elif blocker is not None:
        counter_hunt.hunt_blockers = lambda c: blocker
    try:
        acted = drive(mode._counter_ladder(NORMAN, 6, NEEDED))
        return acted, calls
    finally:
        (counter_plan.find_counter_candidates, counter_hunt.hunt,
         counter_hunt.train_counter, counter_hunt.hunt_blockers) = orig


print("=" * 78)
print("THE BOUND — the part that matters")
print("=" * 78)
mode = make_mode()
acted, calls = run_ladder(mode)
check("1. a successful hunt returns True (the run continues, no raise)", acted is True,
      f"hunt called {calls['hunt']}x, train called {calls['train']}x")
check("   ...and it TRAINED the catch (rung 3 is not optional)", calls["train"] == 1)

acted2, calls2 = run_ladder(mode)  # SAME mode object -> same run
check("2. ‼ a SECOND hopeless verdict for the same boss does NOT hunt again",
      acted2 is False and calls2["hunt"] == 0,
      f"acted={acted2}, hunt called {calls2['hunt']}x -> falls through to the honest raise")

mode3 = make_mode()
try:
    run_ladder(mode3, hunt_raises=True)
except BotModeError:
    pass
check("3. a hunt that DERAILS still consumed its one chance", bool(mode3._counter_hunts),
      f"_counter_hunts={mode3._counter_hunts}")
acted3, calls3 = run_ladder(mode3)
check("   ...so the re-entry after the derail does not hunt again",
      acted3 is False and calls3["hunt"] == 0)

sm.StoryMode.reset_per_run_state(mode3)
check("4. reset_per_run_state clears it — the NEXT run gets a fresh chance",
      mode3._counter_hunts == {})
acted4, calls4 = run_ladder(mode3)
check("   ...proven by hunting again after the reset", acted4 is True and calls4["hunt"] == 1)

print()
print("=" * 78)
print("THE FALL-THROUGHS — every failure path reaches the honest raise")
print("=" * 78)
for label, kwargs in (
    ("5. no huntable candidate", dict(candidates=None, blocker=None)),
    ("6. party full", dict(blocker="the party is full, so a catch would go to the PC box")),
    ("7. no spare Poké Ball", dict(blocker="no spare Poké Balls (the last ball is reserved)")),
    ("8. the planner throws", dict(planner_raises=True, blocker=None)),
    ("9. the hunt finds nothing", dict(hunt_result=None)),
):
    fresh = make_mode()
    acted, _ = run_ladder(fresh, **kwargs)
    check(f"{label} -> ladder returns False (caller raises)", acted is False,
          f"recorded: {fresh._counter_hunts}")

print()
print("=" * 78)
print("THE CATCH-ON-SIGHT BRANCH — real StoryMode.on_battle_started")
print("=" * 78)
import modules.items as items_mod
import modules.pokemon_party as party_mod
import modules.story.early_game as eg


def encounter_for(dex, name="Machop", shiny=False):
    return SimpleNamespace(
        is_shiny=shiny,
        type=SimpleNamespace(name="Wild"),
        pokemon=SimpleNamespace(species=SimpleNamespace(national_dex_number=dex, name=name)),
    )


def battle_started(dex, *, armed_dex=(66,), party_size=3, balls=5, shiny=False):
    counter_hunt.COUNTER_CATCH_TARGET_DEX = set(armed_dex)
    orig = (party_mod.get_party, items_mod.get_item_bag, eg.HM_CATCH_TARGET_DEX)
    party_mod.get_party = lambda: [SimpleNamespace(level=30)] * party_size
    items_mod.get_item_bag = lambda: SimpleNamespace(
        poke_balls=[SimpleNamespace(quantity=balls)]
    )
    eg.HM_CATCH_TARGET_DEX = set()  # keep the HM branch out of the way
    try:
        self = SimpleNamespace(
            _defeat_counts={}, _location_key=lambda: (0, 0),
            SURVIVAL_WHITEOUT_THRESHOLD=sm.StoryMode.SURVIVAL_WHITEOUT_THRESHOLD,
        )
        return sm.StoryMode.on_battle_started(self, encounter_for(dex, shiny=shiny))
    finally:
        party_mod.get_party, items_mod.get_item_bag, eg.HM_CATCH_TARGET_DEX = orig
        counter_hunt.disarm()


def is_catch(result) -> bool:
    return isinstance(result, sm.StoryCatchStrategy) and not isinstance(
        result, sm.StoryShinyCatchStrategy
    )


check("10. armed + target + room + spare ball -> StoryCatchStrategy",
      is_catch(battle_started(66)), type(battle_started(66)).__name__)
check("11. a NON-target species is not counter-caught",
      not is_catch(battle_started(261)), type(battle_started(261)).__name__)
check("12. a FULL party is not counter-caught",
      not is_catch(battle_started(66, party_size=6)))
check("13. the RESERVE ball is not spent (balls == 1)",
      not is_catch(battle_started(66, balls=1)))
check("14. disarmed -> not counter-caught", not is_catch(battle_started(66, armed_dex=())))

print()
print("=" * 78)
print("ARM / DISARM HYGIENE")
print("=" * 78)
counter_hunt.arm(["Machop"])
check("arm() resolves a real species to its dex number",
      bool(counter_hunt.COUNTER_CATCH_TARGET_DEX) and counter_hunt.is_armed(),
      str(counter_hunt.COUNTER_CATCH_TARGET_DEX))
counter_hunt.disarm()
check("disarm() clears it", not counter_hunt.is_armed())
counter_hunt.arm(["NotARealPokemon"])
check("arm() with an unresolvable name does not raise, and arms nothing",
      not counter_hunt.is_armed())

# 15. hunt() must disarm in its `finally` even when the spin blows up.
orig_eg = {name: getattr(eg, name) for name in
           ("_navigate_riding_out", "_story_spin", "normalize_to_overworld",
            "wait_until_truly_controllable", "provision_poke_balls")}


def _noop_gen(*a, **k):
    return
    yield  # pragma: no cover


def _exploding_spin(*a, **k):
    raise BotModeError("the spin died")
    yield  # pragma: no cover


try:
    for name in orig_eg:
        setattr(eg, name, _noop_gen)
    eg._story_spin = _exploding_spin
    items_orig = items_mod.get_item_bag
    party_orig = party_mod.get_party
    items_mod.get_item_bag = lambda: SimpleNamespace(poke_balls=[SimpleNamespace(quantity=5)])
    party_mod.get_party = lambda: [SimpleNamespace(level=30, is_egg=False,
                                                   species=SimpleNamespace(types=()))] * 3
    raised = None
    try:
        drive(counter_hunt.hunt(MACHOP, NEEDED))
    except BotModeError as error:
        raised = error
    check("15. hunt() propagates the failure (it does not swallow a derail)", raised is not None,
          str(raised))
    check("    ...and DISARMED on the way out (the `finally`)", not counter_hunt.is_armed(),
          str(counter_hunt.COUNTER_CATCH_TARGET_DEX))
finally:
    for name, fn in orig_eg.items():
        setattr(eg, name, fn)
    items_mod.get_item_bag = items_orig
    party_mod.get_party = party_orig
    counter_hunt.disarm()

print()
print("=" * 78)
print(f"RESULT: {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'}")
for f in failures:
    print(f"  FAILED: {f}")
print("=" * 78)
sys.exit(1 if failures else 0)
