# -*- coding: utf-8 -*-
"""GATE — `team_is_ready` must NEVER return READY when the battler set is empty.

⛔⛔ THE DEFECT THIS LOCKS DOWN. `victory_road.team_is_ready` builds its verdict by APPENDING to
`reasons` while looping over `battler_identities()`. If that dict is empty the loop body never runs,
`reasons` stays `[]`, and the function returns **`(True, [])`** — a party containing nothing that can
fight the Elite Four is certified READY, silently, and §Ch23 returns early having trained nobody.

⭐ THIS IS A CHECK THAT ANSWERS WITHOUT ASKING — the same shape as two defects already on record in
this very function: the `POKEBOT_CH23_TRAIN_TARGET=53` flag that reached only half the function
(`PRE reasons=[]`, `train_estimate_total = None`), and the Crunch test that stopped asking at exactly
L47. All three grade PASS by never evaluating.

‼ WHY IT IS GATED NOW, BEFORE ANYONE NEEDS IT. The only untested fix direction left on
`#24-lowlevelmules` is making `battler_identities` bench by ROLE instead of by the hardcoded
`BENCH_SPECIES` triple. A role predicate that is one clause too broad EMPTIES the set — and without
this guard that bug surfaces as a **passing run**, which is the single most expensive failure mode
this project has (see §Ch15/§Ch18/§Ch19: three legs that PASSED their own acceptance tests while
stranding the bot). ⇒ the guard must exist BEFORE the predicate is touched.

⭐ The guard is FAIL-SAFE BY CONSTRUCTION: it can only convert a silent `True` into a loud `False`,
never the reverse, so it cannot mask a real readiness.

WHAT THIS GATE DOES. Imports the REAL `victory_road` module (it imports without a ROM) and exercises
the REAL `team_is_ready` with `battler_identities` / `get_party` monkeypatched. Exit 0 = PASS.
"""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))


class _Move:
    def __init__(self, name):
        self.move = type("M", (), {"name": name})()


class _Mon:
    """Minimal stand-in — only the attributes `team_is_ready` actually reads."""
    def __init__(self, name, level, moves=()):
        self.species = type("S", (), {"name": name})()
        self.level = level
        self.is_egg = False
        self.moves = [_Move(m) for m in moves]


def _run_arms(VR) -> "list[str]":
    failures = []
    real_ids, real_party = VR.battler_identities, VR.get_party
    try:
        # ---- ARM 1 (THE FAULT): empty battler set must REFUSE, not report ready ----------------
        VR.battler_identities = lambda: {}
        VR.get_party = lambda: [_Mon("Zigzagoon", 12), _Mon("Castform", 30)]
        ready, reasons = VR.team_is_ready()
        if ready or not reasons:
            failures.append(
                f"⛔ EMPTY BATTLER SET GRADED READY — returned ({ready}, {reasons}). This is the "
                f"exact silent-PASS the guard exists to prevent.")

        # ---- ARM 2 (no-fire): a real under-levelled battler still reports NOT ready ------------
        VR.battler_identities = lambda: {(0xAA, "Marill"): (2, 13)}
        VR.get_party = lambda: [_Mon("Sceptile", 50), _Mon("Marill", 13)]
        ready, reasons = VR.team_is_ready()
        if ready or not any("Marill" in r for r in reasons):
            failures.append(f"⛔ an under-levelled battler was not reported: ({ready}, {reasons})")

        # ---- ARM 3 (no-fire): a genuinely ready team must STILL pass ---------------------------
        # ⭐ THE MOST IMPORTANT NO-FIRE ARM. A guard that makes everything fail is not a guard.
        VR.battler_identities = lambda: {(0xBB, "Sceptile"): (0, 50)}
        VR.get_party = lambda: [_Mon("Sceptile", 50)]
        ready, reasons = VR.team_is_ready()
        if not ready or reasons:
            failures.append(f"⛔ FALSE POSITIVE — a ready team was refused: ({ready}, {reasons})")

        # ---- ARM 4 (no-fire): the Mightyena/Crunch rule must survive untouched -----------------
        VR.battler_identities = lambda: {(0xCC, "Mightyena"): (0, 50)}
        VR.get_party = lambda: [_Mon("Mightyena", 50, moves=("Bite", "Tackle"))]
        ready, reasons = VR.team_is_ready()
        if ready or not any("Crunch" in r for r in reasons):
            failures.append(f"⛔ the Crunch requirement regressed: ({ready}, {reasons})")
    finally:
        VR.battler_identities, VR.get_party = real_ids, real_party
    return failures


def main() -> int:
    print("=" * 94)
    print("GATE — `team_is_ready` must never grade READY on an empty battler set")
    print("=" * 94)
    try:
        import modules.story.victory_road as VR
    except Exception as e:  # noqa: BLE001
        print(f"\n  ⛔ could not import victory_road: {type(e).__name__}: {e}")
        print("=" * 94)
        return 1

    failures = _run_arms(VR)
    print(f"\n  arms: 4 (1 fault, 3 no-fire — incl. 'a ready team still passes')")
    for f in failures:
        print(f"    {f}")

    print("\n" + "-" * 94)
    if failures:
        print("FAILED — a readiness check that answers without asking certifies a broken run.")
        print("=" * 94)
        return 1
    print("✅ PASS — an empty battler set refuses loudly; real verdicts are unchanged.")
    print("=" * 94)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
