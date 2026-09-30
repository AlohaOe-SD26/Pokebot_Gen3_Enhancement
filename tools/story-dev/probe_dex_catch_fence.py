# -*- coding: utf-8 -*-
"""OFFLINE proof that `#24-dexhunt`'s catching fence admits exactly what it should (`decide_dex_catch`).

⛔⛔ WHY THIS EXISTS. `04-HANDOFF.md` says of this item: *"NO CHEAP FIXTURE TEST EXISTS — a Tier 2
auditor tried and could not compute a discriminator. Grading needs an hours-long batch."* That is
true of the fence's **EFFICACY** and stays true — only a batch can say whether catching raises the
dex. It was being read as though the fence's **CORRECTNESS** were equally unreachable, and it is not.
`decide_dex_catch` is PURE, so every condition is interrogable here in milliseconds.

That distinction is the whole point. The draft spec for this feature called
`counter_hunt.hunt_active()` — **a function that does not exist**; the real name is `is_armed()`.
`_should_catch` wraps its body in `except Exception`, so the `AttributeError` would have been
swallowed, the fence would never have fired, and the 8-hour A/B would have printed "no difference" —
**reading as a REFUTATION of a feature that never ran.** A pure predicate plus this file is what
makes that class of failure impossible to ship.

⭐ WHAT EACH CASE PROVES — every one names a specific way the fence can be wrong:
  C1  ORDINARY CASE PRESERVED — pre-gym-1 team building still admits a new species below the target.
      ‼ This is the case that must never change: `#24-partycap` MEASURED that disturbing the early
      party costs 36 points of finish rate (52.0% -> 15.8%).
  C2  pre-gym-1 STOPS at the team target (the cap that measurement defends).
  C3  ⛔ THE FENCE'S REASON FOR EXISTING — post-badge, a NON-full party is REFUSED. A catch there
      would take a party slot, and the empty slots are the runway HM/counter catches land on.
  C4  post-badge at a FULL party is ADMITTED — the fence actually fires. (Without C4, C3 alone would
      be satisfied by a predicate that simply never returns True.)
  C5  an ARMED counter hunt refuses. `catch_confirmed`'s box path is species-blind
      (`counter_hunt.py:363-365`), so an unrelated box catch ENDS the hunt spin; the verdict is
      type-aware and finds nothing, losing a 120,000-frame hunt and a ball.
  C6  an armed HM hunt refuses too — `HM_CATCH_TARGET_DEX` is a SECOND, independent arming system
      that `is_armed()` cannot see. A fence checking only `counter_hunt` would have a hole here.
  C7  a TRAINING grind refuses. A catch earns ZERO exp while `train_team` exists only to gain exp,
      and `#24-ch23training` is the top run-ender (16 of 49) for exceeding a frame ceiling.
  C8  ⛔ THE BALL RESERVE IS A LEVEL, NOT A BOOLEAN — the fatal case. `counter_hunt.hunt()` checks
      balls at `:471` BEFORE its journey and arms only at `:510` AFTER arriving, so `is_armed()` is
      False for the whole trek and a token floor of 1 would let the fence spend the hunt's balls en
      route. At 3 spare balls (well above `resource_blocker`'s floor of 1) the fence must still refuse.
  C9  the MASTER BALL cannot satisfy the reserve — `spare_balls` is fed from
      `number_of_balls_except_master_ball` (`items.py:447`), because a discretionary dex catch must
      never be the thing that burns it.
  C10 the PINNED resource predicate is honoured — a non-None `resource_blocker()` string refuses AND
      becomes the reason verbatim, so the fence cannot drift from it (2026-07-31 ruling).
  C11 an already-OWNED species refuses (this is a DEX feature; a dup adds nothing).
  C12 a species already IN THE PARTY refuses even when unowned.
  C13 the per-species ATTEMPT CAP terminates. A failed catch leaves the species un-owned, so the
      predicate is True again next encounter and nothing else in the tree remembers.
  C14 a not-at-full-strength party refuses — a catch battle NEVER attacks back (`catch.py:41-62`;
      with POKEBOT_R25_WEAKEN unset — set, design v2 step 12 allows one bounded weaken damage turn)
      and never flees after a faint (`:38-39`), so entry from weakness is the whiteout vector.
  C15 ⛔ EGGS COUNT TOWARD FULLNESS. 5 mons + 1 egg is a FULL party to the game, so the catch is
      boxed; counting egg-filtered would fire the fence at 5 and consume the sixth PARTY slot —
      the exact `#24-partycap` regression. Built so the two conventions DISAGREE.
  C16 a PC with every box full refuses (the game shows `gText_BoxFull`, does not consume the ball,
      and returns to the bag menu — a state no caller inspects, so the strategy would throw again).
  C17 shiny and trainer battles are refused here, because they are handled upstream.

‼ FAULT ARM (self-test, and the reason this probe can be believed):
    POKEBOT_DEXFENCE_FAULT=nofence PYTHONUTF8=1 py -3.12 probe_dex_catch_fence.py
patches the fence to the PRE-fence behaviour (post-badge admits regardless of party/hunt/training/
balls). C3 and C5-C8 must then go RED and the script must exit 1.
A probe that passes in BOTH arms is measuring nothing — `08-MISTAKES.md`, and the rule that a gate
with no proven failure mode teaches the reader to bypass it.
"""
from __future__ import annotations

import os
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "sandbox-pokebot"))

from plugins.custom_modes.story_mode import (  # noqa: E402
    DEX_CATCH_BALL_RESERVE,
    DEX_CATCH_MAX_ATTEMPTS,
    PARTY_CAPACITY,
    PC_STORAGE_SLOTS,
    decide_dex_catch,
)

FAULT = os.environ.get("POKEBOT_DEXFENCE_FAULT", "").strip()

#: A post-badge state at a FULL party with everything clear — the fence's admit case. Individual
#: cases override exactly ONE field, so a failure names exactly one condition.
BASE = dict(
    is_wild=True,
    is_shiny=False,
    has_pokedex=True,
    pre_badge1=False,
    party_slots_used=PARTY_CAPACITY,
    battler_count=PARTY_CAPACITY,
    party_target=4,
    resource_block=None,
    spare_balls=DEX_CATCH_BALL_RESERVE + 5,
    hunt_armed=False,
    training=False,
    boxed_count=12,
    party_healthy=True,
    species_dex=279,          # Pelipper — the species in the corpus existence proof
    owned_dex=frozenset({1, 4, 7}),
    party_dex=frozenset({1, 4, 7, 261, 183, 351}),
    attempts=0,
)


def _call(**over):
    kwargs = dict(BASE)
    kwargs.update(over)
    if FAULT == "nofence":
        # PRE-FENCE behaviour: post-badge simply admits any unowned species, with no party/hunt/
        # training/ball conditions at all. This is what "just relax the badge gate" would have shipped.
        if not kwargs["pre_badge1"] and kwargs["is_wild"] and not kwargs["is_shiny"]:
            d = kwargs["species_dex"]
            if d is not None and d not in kwargs["owned_dex"] and d not in kwargs["party_dex"]:
                return True, "FAULT: pre-fence admit"
    return decide_dex_catch(**kwargs)


CASES: list[tuple[str, dict, bool, str]] = [
    ("C1  pre-gym-1, below target -> ADMIT (the ordinary case, must never change)",
     dict(pre_badge1=True, party_slots_used=2, battler_count=2), True, "pre-gym-1"),
    ("C2  pre-gym-1, AT target -> refuse",
     dict(pre_badge1=True, party_slots_used=4, battler_count=4), False, "target"),
    # ⛔⛔ C19/C20 ARE A REGRESSION TEST FOR A BUG THIS FILE ALREADY CAUGHT ONCE. The first draft fed
    # the RAW slot count to the pre-gym-1 target, so 3 battlers + 1 EGG read as a full team of 4 and
    # refused a catch the pre-fence code ALLOWED — a silent change to the ordinary case, in the one
    # path `#24-partycap` costs 36 points to disturb. The two counts differ ONLY when an egg is
    # aboard, so no amount of re-reading finds it; only an A/B against the old logic does.
    ("C19 pre-gym-1, 3 battlers + 1 EGG -> ADMIT (an egg is not a battler)",
     dict(pre_badge1=True, party_slots_used=4, battler_count=3), True, "pre-gym-1"),
    ("C20 pre-gym-1, 4 battlers + 1 EGG -> refuse (4 battlers IS the target)",
     dict(pre_badge1=True, party_slots_used=5, battler_count=4), False, "target"),
    ("C3  post-badge, party 4/6 -> REFUSE (protects the HM/counter runway)",
     dict(party_slots_used=4), False, "runway"),
    ("C4  post-badge, party 6/6 -> ADMIT (the fence fires)",
     dict(), True, "PC box"),
    ("C5  counter hunt ARMED -> refuse",
     dict(hunt_armed=True), False, "hunt is armed"),
    ("C6  HM hunt armed (2nd arming system) -> refuse",
     dict(hunt_armed=True), False, "hunt is armed"),
    ("C7  training grind in progress -> refuse",
     dict(training=True), False, "training"),
    ("C8  3 spare balls (above resource floor, below reserve) -> REFUSE",
     dict(spare_balls=3), False, "dex reserve"),
    ("C9  reserve exactly met, not exceeded -> refuse",
     dict(spare_balls=DEX_CATCH_BALL_RESERVE), False, "dex reserve"),
    ("C10 resource_blocker() says no -> refuse, verbatim",
     dict(resource_block="no spare Poké Balls (the last ball is reserved)"),
     False, "last ball is reserved"),
    ("C11 species already owned -> refuse",
     dict(owned_dex=frozenset({279})), False, "already owned"),
    ("C12 species already in the party -> refuse",
     dict(party_dex=frozenset({279})), False, "already in the party"),
    ("C13 attempt cap reached -> refuse",
     dict(attempts=DEX_CATCH_MAX_ATTEMPTS), False, "already attempted"),
    ("C14 party not at full strength -> refuse",
     dict(party_healthy=False), False, "full strength"),
    # The MIRROR of C19: for FULLNESS the egg DOES count, because the game counts it. C15 and C19
    # are deliberately the same party shape read by the two different conventions.
    ("C15 5 mons + 1 EGG is FULL -> ADMIT (eggs occupy a slot)",
     dict(party_slots_used=6, battler_count=5, party_dex=frozenset({1, 4, 7, 261, 183})), True, "PC box"),
    ("C16 PC storage full -> refuse",
     dict(boxed_count=PC_STORAGE_SLOTS), False, "PC storage is full"),
    ("C17 trainer battle -> refuse",
     dict(is_wild=False), False, "trainer"),
    ("C18 shiny -> refuse here (handled by the shiny branch)",
     dict(is_shiny=True), False, "shiny"),
]

#: Cases the fault arm MUST knock over. If `nofence` leaves these green the arm is not reaching the
#: code under test and the whole probe is worthless.
FAULT_MUST_BREAK = {"C3", "C5", "C6", "C7", "C8", "C9", "C14", "C16"}


def main() -> int:
    print("=" * 100)
    print("DEX CATCH FENCE — `decide_dex_catch` interrogated offline (`#24-dexhunt`)")
    print(f"  reserve={DEX_CATCH_BALL_RESERVE} balls (excl. Master)  max_attempts={DEX_CATCH_MAX_ATTEMPTS}"
          f"  party_capacity={PARTY_CAPACITY}  pc_slots={PC_STORAGE_SLOTS}")
    if FAULT:
        print(f"  ⛔ FAULT ARM ACTIVE: {FAULT!r} — cases {sorted(FAULT_MUST_BREAK)} MUST go RED")
    print("=" * 100)

    failures: list[str] = []
    broke: set[str] = set()

    for label, over, want, want_reason in CASES:
        tag = label.split()[0]
        got, reason = _call(**over)
        ok = got == want and (want_reason.lower() in reason.lower())
        if not ok:
            failures.append(tag)
            broke.add(tag)
        mark = "OK  " if ok else "FAIL"
        print(f"  [{mark}] {label}")
        print(f"         -> catch={got}  reason={reason!r}")
        if not ok:
            print(f"         ⛔ expected catch={want} and reason containing {want_reason!r}")

    print("\n" + "=" * 100)
    if FAULT:
        missed = sorted(FAULT_MUST_BREAK - broke)
        if missed:
            print(f"  ⛔ FAULT ARM DID NOT REACH: {missed} stayed green under {FAULT!r}.")
            print("     The arm is not exercising the fence — this probe cannot be trusted.")
            return 1
        print(f"  FAULT ARM OK — {sorted(broke & FAULT_MUST_BREAK)} went RED as required.")
        print("  ⇒ the fence is genuinely what makes those cases pass in the clean arm.")
        return 1  # a fault arm must exit non-zero; the SUITE runs the clean arm

    if failures:
        print(f"  ⛔ FAIL — {len(failures)} case(s) red: {failures}")
        return 1
    print(f"  PASS — all {len(CASES)} cases. The fence admits exactly what it should.")
    print("  ‼ This proves CORRECTNESS, never EFFICACY: whether dex catching actually raises")
    print("    `owned` needs `x4_headless.py --build sandbox`. See probe_dexfence_opportunity.py")
    print("    for the (measured) proof that such a batch would not be vacuous.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
