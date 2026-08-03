"""#24-pc: the PC rotation must piggyback a heal, no-op when not worth it, and never raise.
NO EMULATOR — the decision half is pure and the action half is checked structurally.

WHY. Batch5 (`x4-runs/20260801-075805`) blocked the counter chain outright 5 times with

    Story: cannot hunt a counter — the party is full, so a catch would go to the PC box
           (needs #24-pc). Stopping honestly.

and 13 of that batch's 18 non-finishes (72%) were the counter chain stopping for want of an
answer it could not go and get. `team_policy` already DECIDED what to rotate; nothing
executed it, because that module deliberately excludes the action.

WHAT THIS PINS
  1. the tile really is a PC in the ROM's own map data (not recalled);
  2. a healthy party is left alone — no PC visit is burned;
  3. the Makuhita case from `team_policy`'s header actually frees a slot;
  4. the deposit never drops the party below `MIN_PARTY_AFTER_ROTATION`;
  5. the wiring is a PIGGYBACK — the call sits between the nurse and the exit inside
     `heal_in_pokemon_center`, not in a routine that travels to a PC on purpose;
  6. failures degrade instead of raising.
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

from modules.story import pc_trip  # noqa: E402
from modules.story.team_policy import (  # noqa: E402
    MIN_PARTY_AFTER_ROTATION,
    MonView,
    rotation_plan,
)

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def mon(name, level, moves=(("Tackle", 35),)):
    return MonView(name, level, tuple(moves))


print("1. the PC tile matches what the ROM map data says")
# probe_pc_tile.py scanned six Poké Centre 1F maps: PC at (10,1), approachable from (10,2)
# facing Up. Upstream daycare.py independently uses (10,2)/Up.
check("PC_TILE is (10, 1)", pc_trip.PC_TILE == (10, 1), str(pc_trip.PC_TILE))
check("PC_STAND_TILE is (10, 2)", pc_trip.PC_STAND_TILE == (10, 2), str(pc_trip.PC_STAND_TILE))
check("PC_FACING is Up", pc_trip.PC_FACING == "Up", pc_trip.PC_FACING)

print("2. a healthy party is left alone (no PC visit burned)")
healthy = [mon("Swampert", 35), mon("Swellow", 33), mon("Machoke", 31), mon("Ninjask", 30)]
plan = rotation_plan(healthy)
check("worth_it is False for a level party", not plan["worth_it"], str(plan["deposit"]))

print("3. the Makuhita case — dead weight frees a slot")
# team_policy's own header: a L8 Makuhita carried across five badges while the team hit L42.
full = [mon("Swampert", 42), mon("Swellow", 40), mon("Ninjask", 38),
        mon("Machoke", 36), mon("Makuhita", 8), mon("Zigzagoon", 8)]
plan = rotation_plan(full)
check("worth_it is True", plan["worth_it"])
check("at least one slot is freed", len(plan["deposit"]) >= 1, f"deposit={plan['deposit']}")
names = [full[i].species for i in plan["deposit"]]
check("it deposits the low-level dead weight, not a battler",
      all(n in ("Makuhita", "Zigzagoon") for n in names), str(names))

print(f"4. the party never drops below MIN_PARTY_AFTER_ROTATION ({MIN_PARTY_AFTER_ROTATION})")
worst = [mon("Swampert", 42), mon("Zigzagoon", 6), mon("Wurmple", 5), mon("Poochyena", 6)]
plan = rotation_plan(worst)
left = len(worst) - len(plan["deposit"])
check("a party of chaff is not emptied", left >= MIN_PARTY_AFTER_ROTATION,
      f"{len(worst)} - {len(plan['deposit'])} = {left}")

print("5. ‼ it is wired as a PIGGYBACK, between the nurse and the exit")
src = (SANDBOX / "modules" / "modes" / "util" / "higher_level_actions.py").read_text(
    encoding="utf-8", errors="replace"
)
check("heal_in_pokemon_center calls the rotation",
      "deposit_dead_weight_if_worth_it" in src)
heal = re.search(r"def heal_in_pokemon_center\(.*?(?=\ndef )", src, re.S)
check("the call is inside heal_in_pokemon_center", heal is not None and
      "deposit_dead_weight_if_worth_it" in heal.group(0))
if heal:
    body = heal.group(0)
    i_nurse = body.find("wait_for_yes_no_question")   # the heal itself
    i_rot = body.find("deposit_dead_weight_if_worth_it")
    i_exit = body.find("Get out — robustly")
    check("ordering is nurse -> rotate -> exit",
          -1 < i_nurse < i_rot < i_exit,
          f"nurse@{i_nurse} rotate@{i_rot} exit@{i_exit}")

print("6. failures degrade rather than raising")
pt = (SANDBOX / "modules" / "story" / "pc_trip.py").read_text(encoding="utf-8", errors="replace")
check("the action wraps its PC work in try/except", "except Exception" in pt)
check("the heal-side call is also guarded",
      heal is not None and re.search(
          r"try:\s*\n\s*from modules\.story\.pc_trip import deposit_dead_weight_if_worth_it",
          heal.group(0)) is not None)
# A stale-index deposit is the classic bug here: depositing shifts later indices down.
check("it resolves Pokemon OBJECTS before depositing, not indices",
      "deposit_pokemon_to_box(mon)" in pt and "targets = [party[i]" in pt)

print("7. ‼ THE REGRESSION GUARD — only a FULL party is rotated")
# Batch6 (`x4-runs/20260802-160603`) finished 2 of 37 runs, down from 16 of 34, because this
# ran on EVERY heal: `PC rotation done — party is now 3` appeared 73 times out of 75. With
# MIN_PARTY_AFTER_ROTATION=3 the bot lived on a permanent three-mon party and wedged in gyms
# (global watchdog 1 -> 67). team_policy decided correctly; the WIRING was wrong.
class _Sp:
    def __init__(self, name): self.name = name

class _Mv:
    def __init__(self, name, power): self.name, self.base_power = name, power

class _LM:
    def __init__(self, mv): self.move = mv

class _P:
    """Stand-in party member. ‼ It must satisfy `view_from_party` too — species AND moves —
    or `plan_deposits` swallows the AttributeError and returns an empty plan, which reads
    exactly like the gate working. That false PASS is why this double is spelled out."""
    is_egg = False
    def __init__(self, lvl, name="Mon"):
        self.level, self.species = lvl, _Sp(name)
        self.moves = (_LM(_Mv("Tackle", 35)),)

check("ROTATE_ONLY_WHEN_PARTY_AT_LEAST is 6 (resource_blocker's own threshold)",
      pc_trip.ROTATE_ONLY_WHEN_PARTY_AT_LEAST == 6,
      str(pc_trip.ROTATE_ONLY_WHEN_PARTY_AT_LEAST))
for n in (3, 4, 5):
    got = pc_trip.plan_deposits([_P(40)] + [_P(4)] * (n - 1))
    check(f"a {n}-mon party is NOT rotated", not got["worth_it"], str(got["deposit"]))
# A full party of mostly chaff must still be rotated - that is the whole point.
got = pc_trip.plan_deposits([_P(42), _P(40), _P(38), _P(36), _P(8), _P(8)])
check("a FULL party is still rotated", got["worth_it"], str(got["deposit"]))

print("8. plan_deposits degrades on a malformed party instead of raising")
got = pc_trip.plan_deposits(None)
check("returns an empty, not-worth-it plan", got == {"deposit": [], "withdraw": [],
                                                     "reasons": {}, "worth_it": False}, str(got))

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
