"""A/B proof for the TEACH-UNDER-DIALOGUE hang (ch13_run1.log f9931).

THE BUG: `ensure_hm_learner` returns the instant a caught mon registers, while the catch
AFTERMATH is still on screen ("Give a nickname to the captured ZIGZAGOON?"). The old
`teach_hm_move` called `wait_until_truly_controllable()` — which by design presses
NOTHING — and immediately opened the BAG via `StartMenuNavigator("BAG")`. The bag cannot
open under a pending dialogue, so the whole teach wedged in BAG_MENU until the watchdog.

THE FIX (already applied in sandbox-pokebot/modules/story/early_game.py): `teach_hm_move`
now calls `normalize_to_overworld()` (B-rides menus/dialogue to a clean overworld) BEFORE
`wait_until_truly_controllable()` and the bag-open. `ensure_hm_learner` also normalizes
before handing back its slot — belt and suspenders.

Fault injection, no emulator: patch `early_game.normalize_to_overworld`,
`early_game.wait_until_truly_controllable`, and `modules.menuing.StartMenuNavigator` to a
minimal model of "a dialogue is pending" (`state["dialogue_open"]`). Drive the REAL
`teach_hm_move` generator up to (and only to) the bag-open attempt — the fake
`StartMenuNavigator("BAG").step()` raises a sentinel the instant it runs, recording
whether a dialogue was still open at that moment. This needs no stubbing of anything
past the bag-open call (no task waits, no scroll-to-item) because the bug is entirely
about ORDERING: does the bag get asked to open before or after the dialogue is cleared.

  A (bug bypassed back in / fault-injected): `normalize_to_overworld` is patched to a
     no-op that does NOT clear the dialogue (models "the call isn't there" / "it silently
     does nothing") -> bag-open attempt sees dialogue_open=True -> FAILS.
  B (fix as shipped): `normalize_to_overworld` is patched to the real *shape* of the fix
     (clears the dialogue) -> bag-open attempt sees dialogue_open=False -> SUCCEEDS, and
     we assert normalize ran strictly before the bag-open attempt.
  CONTROL: no dialogue pending to begin with -> the (fixed) flow still reaches the bag
     and succeeds; the extra normalize call does not regress the healthy path.

Run:  py -3.12 tools/story-dev/repro_teach_under_dialogue.py
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

import modules.menuing as menuing
from modules.story import early_game as eg


# ---- sentinels that let us stop the drive exactly at the bag-open checkpoint ----
class _BagOpenFailed(Exception):
    """Models: the bag refused to open because a dialogue box is still pending."""


class _BagOpenedOK(Exception):
    """Models: the bag opened cleanly. Raised (not returned) so this repro does not have
    to stub the rest of teach_hm_move (task waits, scroll-to-item, etc.) — the bug is
    entirely about what state the game is in the instant the bag is asked to open."""


def make_state(*, dialogue_open: bool):
    return {"dialogue_open": dialogue_open, "order": []}


def install(state, *, normalize_clears_dialogue: bool):
    """Wire the fault injection for one scenario. Returns nothing; mutates `state["order"]`
    as the drive proceeds so we can assert ordering afterwards."""

    def fake_normalize():
        state["order"].append("normalize_ran")
        if normalize_clears_dialogue:
            state["dialogue_open"] = False
        return
        yield  # pragma: no cover - unreachable, keeps this a generator function

    def fake_wait_controllable():
        state["order"].append("wait_controllable_ran")
        # presses nothing, by design (matches the real function's contract)
        return
        yield  # pragma: no cover

    class FakeStartMenuNavigator:
        def __init__(self, which):
            self.which = which

        def step(self):
            state["order"].append(("bag_open_attempt", state["dialogue_open"]))
            if state["dialogue_open"]:
                raise _BagOpenFailed(
                    "BAG cannot open: a dialogue box ('Give a nickname...?') is still "
                    "pending on screen"
                )
            raise _BagOpenedOK("bag opened cleanly onto a normalized overworld")
            yield  # pragma: no cover

    eg.normalize_to_overworld = fake_normalize
    eg.wait_until_truly_controllable = fake_wait_controllable
    menuing.StartMenuNavigator = FakeStartMenuNavigator


def make_item_and_mon():
    move = SimpleNamespace(name="Surf", base_power=0)
    item = SimpleNamespace(name="HM03", tm_hm_move=lambda: move)
    species = SimpleNamespace(name="Zigzagoon", can_learn_tm_hm=lambda _item: True)
    mon = SimpleNamespace(species=species, moves=[None, None, None, None])
    return item, mon


def drive(gen, cap=50):
    frames = 0
    try:
        while frames < cap:
            next(gen)
            frames += 1
    except StopIteration:
        return frames, "returned", None
    except Exception as e:  # noqa: BLE001 - we want the raw exception for inspection
        return frames, f"raised {type(e).__name__}: {e}", e
    return frames, "cap hit (never reached bag-open)", None


def run_scenario(label, *, dialogue_open_initially: bool, normalize_clears_dialogue: bool):
    item, mon = make_item_and_mon()
    eg.get_party = lambda: [mon]
    state = make_state(dialogue_open=dialogue_open_initially)
    install(state, normalize_clears_dialogue=normalize_clears_dialogue)

    frames, outcome, exc = drive(eg.teach_hm_move(item, 0))
    print(f"[{label}] {outcome} (order={state['order']})")
    return state, outcome, exc


print("=" * 78)

# ---- A: pre-fix behavior (normalize call bypassed / made a no-op) ----
# Models "ensure_hm_learner just returned with the nickname prompt still up, and
# teach_hm_move went straight from wait_until_truly_controllable() to the bag."
state_a, outcome_a, exc_a = run_scenario(
    "A pre-fix", dialogue_open_initially=True, normalize_clears_dialogue=False
)
assert isinstance(exc_a, _BagOpenFailed), f"expected the bag-open to FAIL under a pending dialogue, got: {outcome_a}"
assert state_a["order"][0] == "normalize_ran", "no-op normalize still ran (as a call), it just didn't clear anything"
assert state_a["order"][-1] == ("bag_open_attempt", True), "bag-open must have been attempted WHILE dialogue_open=True"
print("  -> CONFIRMED: bag-open attempted onto a still-pending dialogue -> fails, as reported in ch13_run1 f9931.")

print("-" * 78)

# ---- B: fix as shipped (normalize actually clears the pending dialogue first) ----
state_b, outcome_b, exc_b = run_scenario(
    "B fixed", dialogue_open_initially=True, normalize_clears_dialogue=True
)
assert isinstance(exc_b, _BagOpenedOK), f"expected the bag-open to SUCCEED after normalize, got: {outcome_b}"
norm_idx = state_b["order"].index("normalize_ran")
bag_idx = next(i for i, e in enumerate(state_b["order"]) if isinstance(e, tuple) and e[0] == "bag_open_attempt")
assert norm_idx < bag_idx, "normalize_to_overworld must run BEFORE the bag-open attempt"
assert state_b["order"][bag_idx] == ("bag_open_attempt", False), "bag-open must see dialogue_open=False after normalize"
print("  -> CONFIRMED: normalize_to_overworld ran before the bag-open, dialogue cleared, bag opens cleanly.")

print("-" * 78)

# ---- CONTROL: no dialogue pending at all (the healthy path) ----
state_c, outcome_c, exc_c = run_scenario(
    "CONTROL healthy", dialogue_open_initially=False, normalize_clears_dialogue=True
)
assert isinstance(exc_c, _BagOpenedOK), f"healthy path must still reach and open the bag, got: {outcome_c}"
assert state_c["order"][0] == "normalize_ran", "normalize still runs unconditionally, harmlessly, on the healthy path"
assert state_c["order"][-1] == ("bag_open_attempt", False), "bag-open sees dialogue_open=False throughout"
print("  -> CONFIRMED: with no dialogue pending, the extra normalize call does not regress the healthy path.")

print("=" * 78)
print(
    "ALL PASS: teach_hm_move's bag-open now only fires after normalize_to_overworld has "
    "cleared any pending catch-aftermath dialogue (A fails / B and CONTROL succeed)."
)
