r"""GATE — the PC withdraw's room check must use THE CONSUMER'S predicate (KI-102).

WHY THIS EXISTS
---------------
`withdraw_from_box` decides whether it must deposit-to-make-room, and then hands the withdraw to
`pc_interaction._do_withdraw_actions`, which refuses outright when the party is full. Until
2026-09-25 the two disagreed by exactly one case:

    producer  (pc_trip)         `alive = [... not is_egg]`     -> EGGS EXCLUDED
    consumer  (pc_interaction)  `get_party_size() == 6`        -> EGGS INCLUDED
                                (get_party_size() IS len(get_party()))

⇒ a party of **5 mon + 1 egg** read as "room available" to the producer, so no deposit was queued,
and the withdraw then RAISED *"Cannot withdraw any Pokémon because the party already contains 6"* —
**after the PC journey had already been spent.**

‼ THIS IS THE SIBLING OF A BUG THIS PROJECT ALREADY CAUGHT. `08-MISTAKES.md` records the identical
defect in `deposit_one_dead_weight`, caught by adversarial review *before it ever met an egg*, with
the rule that fixes both:
    "When a function exists to satisfy ONE specific caller's precondition, copy that caller's
     predicate VERBATIM rather than writing an equivalent-looking one. 'Alive' and 'occupies a
     slot' differ by exactly one case — an egg — and that case is invisible until it happens."

WHAT IT CHECKS
  W1  5 mon + 1 egg -> NO room (a deposit must be queued). The fix.
  W2  HISTORICAL CONTROL — the OLD egg-filtered predicate, computed here, says "room". This pins
      the exact disagreement so the bug cannot quietly return wearing a different name. ⛔ If W2
      ever stops disagreeing, this gate has stopped testing anything and must be re-derived.
  W3  NARROWNESS — with no egg, old and new agree for every size 0..7. The fix must change exactly
      one case and nothing else.
  W4  6 mon -> NO room.     W5  4 mon -> room.     W6  0 mon -> room.
  W7  CONSUMER PARITY — the function must equal `len(party) < 6` EXACTLY, including the absence of
      a `p is not None` filter, because `get_party_size()` does not filter either. An
      "equivalent-looking" predicate is the thing the rule above forbids.

⛔ ALL OFFLINE. No emulator, no ROM: the function is pure and takes the party list.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent / "sandbox-pokebot"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


class Mon:
    def __init__(self, egg: bool = False):
        self.is_egg = egg


def old_predicate_says_room(party) -> bool:
    """The PRE-FIX producer test, reproduced verbatim: `alive` excluded eggs, and the code made
    room only `if len(alive) >= 6`. ⇒ "room" is the negation."""
    alive = [i for i, p in enumerate(party) if p is not None and not getattr(p, "is_egg", False)]
    return not (len(alive) >= 6)


def run() -> int:
    print("=" * 96)
    print("GATE — the PC withdraw's room check must use the CONSUMER's predicate (KI-102)")
    print("=" * 96)

    try:
        from modules.story.pc_trip import party_has_room_for_withdraw as room
    except Exception as error:  # noqa: BLE001
        print(f"  ⛔ cannot import `party_has_room_for_withdraw`: {error!r}")
        print("RESULT: FAIL — the function under test is absent; KI-102's fix is not present.")
        return 1

    five_plus_egg = [Mon()] * 5 + [Mon(egg=True)]

    # W1 — the fix
    check("W1 5 mon + 1 egg -> NO room (deposit must be queued)",
          room(five_plus_egg) is False, f"room={room(five_plus_egg)}")

    # W2 — historical control: the OLD predicate disagreed, and that disagreement IS the bug
    old = old_predicate_says_room(five_plus_egg)
    check("W2 HISTORICAL CONTROL: the old egg-filtered predicate says 'room' (the bug)",
          old is True and room(five_plus_egg) is False,
          f"old={old} new={room(five_plus_egg)} — they must DISAGREE here")

    # W3 — narrowness: without an egg they must agree everywhere
    disagreements = [n for n in range(8)
                     if old_predicate_says_room([Mon()] * n) != room([Mon()] * n)]
    check("W3 NARROWNESS: no egg -> old and new agree for sizes 0..7",
          not disagreements, f"disagree at sizes {disagreements}")

    # W4/W5/W6 — the ordinary cases
    check("W4 6 mon -> NO room", room([Mon()] * 6) is False)
    check("W5 4 mon -> room", room([Mon()] * 4) is True)
    check("W6 empty party -> room", room([]) is True)

    # W7 — consumer parity, including the ABSENCE of a None filter
    mismatches = []
    for n in range(8):
        p = [Mon()] * n
        if room(p) != (len(p) < 6):
            mismatches.append(("plain", n))
    with_none = [Mon(), None, Mon(), None, Mon(), None]  # len 6 -> consumer refuses
    if room(with_none) != (len(with_none) < 6):
        mismatches.append(("with None slots", len(with_none)))
    check("W7 CONSUMER PARITY: equals `len(party) < 6` exactly (no None filter)",
          not mismatches, f"mismatches {mismatches}")

    print("=" * 96)
    if FAILURES:
        print(f"RESULT: FAIL — {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print("RESULT: ALL PASS — the producer and the consumer now agree, including on eggs.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
