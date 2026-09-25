r"""GATE — `boxed_hm_learner_pids` must find a carrier the run ALREADY OWNS, and must fail SAFE.

WHY THIS EXISTS (user directive 2026-09-25)
-------------------------------------------
The user: *"currently it just looks for what it already has and if there is nothing that it has in
the party that can be taught the move, it breaks. I want the bot to be able to freely use pokemon in
the pokemon PC."* `hm_learner_slot` searches the PARTY ONLY, so a usable carrier sitting in a PC box
is invisible and the bot hunts a new one — or derails with *"no swept training grass hosts a learner
species — extend training_areas.TRAINING_GRASS first"*.

⭐ THE CHEAP DESIGN THIS GUARDS: `pc_trip.box_views()` reads `get_pokemon_storage()` — the SAVE
BLOCKS, not a PC menu — so the question "do I already own a carrier?" costs NO journey. A Poké
Centre trip is made only when the answer is yes. If this function ever needs the bot to be standing
at a PC, that property is gone and every check costs a walk.

WHAT IT CHECKS
  B1  EMPTY/UNREADABLE BOX -> `[]`, never an exception. `box_views()` returns `([], [])` on a failed
      read *"a box we cannot read is a box we must not act on"*, and this must inherit that.
  B2  A LEARNER IS FOUND, and it is reported by **PID**.
  B3  A BOX OF NON-LEARNERS -> `[]`. ‼ The non-vacuity arm: B2 alone would pass a function that
      returned every PID it saw.
  B4  ORDERING — a mon that ALREADY KNOWS the move outranks a HIGHER-LEVEL one that does not.
      Teaching an HM to a mon that already has it wastes the only copy of some HMs.
  B5  EGGS ARE SKIPPED. An egg cannot be taught anything and cannot be withdrawn usefully.
  B6  IDENTITY IS PID, NEVER A BOX SLOT (project rule 3) — the returned ints are personality
      values. Slots renumber the moment anything is deposited or withdrawn.
  B7  ONE UNREADABLE MON MUST NOT HIDE THE READABLE ONES.

⛔ ALL OFFLINE. No emulator, no ROM: `box_views` is stubbed. That is the point of keeping the
function pure.
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


# ---------------------------------------------------------------- fakes
class FakeMove:
    def __init__(self, name):
        self.name = name


class FakeSlot:
    def __init__(self, move_name):
        self.move = FakeMove(move_name)


class FakeSpecies:
    def __init__(self, learns: bool):
        self._learns = learns

    def can_learn_tm_hm(self, _item) -> bool:
        return self._learns


class FakeMon:
    def __init__(self, pid, level, learns, knows=False, is_egg=False):
        self.personality_value = pid
        self.level = level
        self.species = FakeSpecies(learns)
        self.moves = [FakeSlot("Surf")] if knows else []
        self.is_egg = is_egg


class ExplodingMon(FakeMon):
    """A box entry whose species read throws — B7's subject."""

    def __init__(self):
        super().__init__(pid=999, level=50, learns=True)

    @property
    def species(self):  # noqa: D401
        raise RuntimeError("unreadable box entry")

    @species.setter
    def species(self, _value):
        pass


class FakeItem:
    def tm_hm_move(self):
        return FakeMove("Surf")


def run() -> int:
    print("=" * 92)
    print("GATE — `boxed_hm_learner_pids`: use the carrier we ALREADY OWN, and fail SAFE")
    print("=" * 92)

    from modules.story import early_game
    from modules.story import pc_trip

    item = FakeItem()

    def with_box(mons):
        """Point `box_views` at a fake box for one call."""
        pc_trip.box_views = lambda: ([None] * len(mons), mons)  # type: ignore[assignment]
        return early_game.boxed_hm_learner_pids(item)

    original = pc_trip.box_views
    try:
        # B1 — empty and unreadable
        check("B1 empty box -> []", with_box([]) == [])

        def _boom():
            raise RuntimeError("cannot read storage")

        pc_trip.box_views = _boom  # type: ignore[assignment]
        try:
            got = early_game.boxed_hm_learner_pids(item)
            check("B1 unreadable box -> [] (no raise)", got == [], f"got {got!r}")
        except Exception as error:  # noqa: BLE001
            check("B1 unreadable box -> [] (no raise)", False, f"raised {error!r}")

        # B2 — a learner is found, by PID
        got = with_box([FakeMon(pid=0xAABB, level=20, learns=True)])
        check("B2 a learner is found by PID", got == [0xAABB], f"got {got!r}")

        # B3 — NON-VACUITY: a box of non-learners yields nothing
        got = with_box([FakeMon(pid=1, level=90, learns=False),
                        FakeMon(pid=2, level=80, learns=False)])
        check("B3 non-learners -> [] (non-vacuity)", got == [], f"got {got!r}")

        # B4 — knows-it outranks higher level
        got = with_box([FakeMon(pid=10, level=90, learns=True, knows=False),
                        FakeMon(pid=11, level=5, learns=True, knows=True)])
        check("B4 already-knows outranks higher level", got and got[0] == 11, f"got {got!r}")

        # B5 — eggs skipped
        got = with_box([FakeMon(pid=20, level=50, learns=True, is_egg=True)])
        check("B5 eggs are skipped", got == [], f"got {got!r}")

        # B6 — identity is a PID, not a slot index
        got = with_box([FakeMon(pid=0, level=10, learns=False),
                        FakeMon(pid=0xDEAD, level=10, learns=True)])
        check("B6 identity is PID, not slot index", got == [0xDEAD],
              f"got {got!r} (a slot-indexed impl would say [1])")

        # B7 — one unreadable mon must not hide the readable ones
        got = with_box([ExplodingMon(), FakeMon(pid=0xBEEF, level=30, learns=True)])
        check("B7 an unreadable entry does not hide the rest", got == [0xBEEF], f"got {got!r}")
    finally:
        pc_trip.box_views = original  # type: ignore[assignment]

    print("=" * 92)
    if FAILURES:
        print(f"RESULT: FAIL — {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print("RESULT: ALL PASS — a boxed carrier is found by PID, and every failure mode is safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
