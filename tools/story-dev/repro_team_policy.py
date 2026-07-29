"""Acceptance: the dead-weight predicate and rotation planner (#24-trainmap+, design §2/§4).

FROM REAL DATA — the user's x4 bundle `20260729-062040`, 363 badge-moment team snapshots.
The cases asserted below are REAL PARTIES the bot actually fielded, not invented ones:

  * P1 reached the **Feather Badge with a team max of L48 while carrying a Zigzagoon L8.**
  * P1 caught a **Makuhita — a FIGHTING type, exactly Norman's counter — and carried it from
    L8 to L9 across FIVE badges** while the team went L22 → L42.
  * 35% of badge moments carried ≥1 mon 15+ levels below the team max; up to FIVE at once.
  * 12 derails in that bundle were "No party mon can learn Surf and the party is full".

Root cause the predicate is meant to expose: `_catch_team_target = 4` fills the party with
early catches, story GIFTS push it to 5-6, and **no story code path has ever touched the PC**
(the only `interact_with_pc` caller in the repo is stock `modules/modes/daycare.py`, which
only releases). Nothing can leave the party, so dead weight is permanent.

No emulator needed — `team_policy` is a pure module by design.
"""
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

from modules.story.team_policy import (  # noqa: E402
    MonView, dead_weight, find_dead_weight, rotation_plan,
    DEAD_WEIGHT_LEVEL_GAP,
)

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print(f"  FAIL {msg}")
    else:
        print(f"  ok   {msg}")


TACKLE = ("Tackle", 35)
SURF = ("Surf", 95)
CUT = ("Cut", 50)
GROWL = ("Growl", 0)
ARM_THRUST = ("Arm Thrust", 15)


print("== ‼ THE REAL CASE: P1 at Feather, team max L48, carrying Zigzagoon L8 ==")
party = [
    MonView("Blaziken", 48, [TACKLE]),
    MonView("Exploud", 40, [TACKLE]),
    MonView("Combusken", 32, [TACKLE]),
    MonView("Mightyena", 33, [TACKLE]),
    MonView("Zigzagoon", 8, [TACKLE]),
    MonView("Castform", 27, [TACKLE]),
]
r = dead_weight(party, 4)
check(r is not None, f"Zigzagoon L8 in an L48 party is flagged (got {r!r})")
check("unrecoverable by construction" in (r or ""), "and the reason names WHY it is unrecoverable")
check(dead_weight(party, 0) is None, "the L48 lead is not flagged")
check(dead_weight(party, 1) is None, "Exploud L40 (8 behind) is NOT flagged — exactly at the gap")
found = find_dead_weight(party)
idxs = [i for i, _ in found]
check(4 in idxs, f"find_dead_weight includes the Zigzagoon (got {idxs})")
check(idxs[0] == 4, "and reports the worst (lowest-level) first")

print("\n== ‼ THE MAKUHITA CASE: the counter was in the party, untrained, for five badges ==")
# Real: Makuhita L9 while the team max was L42. It is Norman's answer and it never became one.
norman_party = [
    MonView("Blaziken", 42, [TACKLE]),
    MonView("Swellow", 38, [TACKLE]),
    MonView("Makuhita", 9, [ARM_THRUST]),
    MonView("Loudred", 35, [TACKLE]),
]
r = dead_weight(norman_party, 2)
check(r is not None, f"Makuhita L9 in an L42 party is flagged as dead weight (got {r!r})")
print("     -> the fix is NOT to box it: it is the Norman counter. This is the signal that")
print("        the counter ladder must TRAIN a caught answer, not merely hold it (design §5).")

print("\n== the level threshold is derived, not arbitrary ==")
check(DEAD_WEIGHT_LEVEL_GAP == 8,
      f"DEAD_WEIGHT_LEVEL_GAP is 8 (got {DEAD_WEIGHT_LEVEL_GAP})")
edge = [MonView("A", 20, [TACKLE]), MonView("B", 12, [TACKLE])]
check(dead_weight(edge, 1) is None, "exactly 8 behind is NOT dead weight (matches TRAIN_CATCHUP_GAP=6 + margin)")
edge2 = [MonView("A", 20, [TACKLE]), MonView("B", 11, [TACKLE])]
check(dead_weight(edge2, 1) is not None, "9 behind IS dead weight")

print("\n== uselessness: no damaging move and no HM ==")
useless = [MonView("A", 20, [TACKLE]), MonView("Magikarp", 18, [("Splash", 0)])]
check(dead_weight(useless, 1) is not None, "a mon with only a 0-power move is flagged")
check("no damaging move" in dead_weight(useless, 1), "and the reason says so")

print("\n== ‼ EXEMPTION: never box the party's ONLY carrier of an HM ==")
# This is the exact wall P1 hit 12 times: party full, no Surf learner, run over.
hm_party = [
    MonView("Blaziken", 40, [TACKLE]),
    MonView("Wailmer", 5, [SURF]),          # far behind AND the only Surf carrier
]
check(dead_weight(hm_party, 1) is None,
      "the sole Surf carrier is EXEMPT even 35 levels behind (boxing it soft-locks the run)")
shared = [
    MonView("Blaziken", 40, [TACKLE, SURF]),
    MonView("Wailmer", 5, [SURF]),          # now redundant
]
check(dead_weight(shared, 1) is not None,
      "but once Surf is covered elsewhere it is no longer exempt")

print("\n== EXEMPTION: the favourite is never dead weight ==")
fav = [MonView("A", 40, [TACKLE]), MonView("Pikachu", 5, [TACKLE], is_favourite=True)]
check(dead_weight(fav, 1) is None, "a favourite is never flagged")

print("\n== contribution test needs REAL data, and must not guess without it ==")
noshow = [MonView("A", 40, [TACKLE]), MonView("B", 38, [TACKLE], battles=6, kos=0, survivals=0)]
check(dead_weight(noshow, 1) is not None, "6 battles, 0 KOs, 0 survivals is flagged")
unknown = [MonView("A", 40, [TACKLE]), MonView("B", 38, [TACKLE])]
check(dead_weight(unknown, 1) is None,
      "with NO battle data recorded (all zeros) it is NOT flagged — absence of data is not evidence")

print("\n== rotation_plan is piggyback-only: it reports worth_it, it does not detour ==")
plan = rotation_plan(party)
check(plan["worth_it"] is True, "a party with dead weight is worth a rotation")
check(4 in plan["deposit"], f"the Zigzagoon is deposited (got {plan['deposit']})")
clean = [MonView("A", 40, [TACKLE]), MonView("B", 38, [TACKLE])]
check(rotation_plan(clean)["worth_it"] is False,
      "a healthy party produces NO rotation — the caller must not burn a PC visit")

print("\n== ‼ THE CAP: the predicate states a FACT; the plan makes a DECISION ==")
# Replaying the raw predicate over all 363 real parties from the 2026-07-29 bundle would
# box 3+ mons in 41% of them and cut 132 observed four-mon parties to ONE — the "lone
# starter can't rotate" condition behind the Roxanne hang (KI-8). Capped, it never does.
from modules.story.team_policy import (  # noqa: E402
    MIN_PARTY_AFTER_ROTATION, MAX_DEPOSITS_PER_ROTATION, find_dead_weight as _fdw,
)
check(MIN_PARTY_AFTER_ROTATION == 3, f"MIN_PARTY_AFTER_ROTATION is 3 (got {MIN_PARTY_AFTER_ROTATION})")
check(MAX_DEPOSITS_PER_ROTATION == 2, f"MAX_DEPOSITS_PER_ROTATION is 2 (got {MAX_DEPOSITS_PER_ROTATION})")

# The real P1-at-Feather party: the FACT is 4 dead-weight mons; the DECISION is 2.
check(len(_fdw(party)) == 4, f"the predicate still reports all 4 as dead weight (got {len(_fdw(party))})")
pl = rotation_plan(party)
check(len(pl["deposit"]) == 2, f"but the plan deposits only 2 (got {len(pl['deposit'])})")
check(pl["deposit"][0] == 4, f"worst-first: the Zigzagoon L8 goes first (got {pl['deposit']})")
check(len(party) - len(pl["deposit"]) >= MIN_PARTY_AFTER_ROTATION,
      "and at least 3 mons remain")

# A four-mon party with three dead-weight members must not be gutted.
four = [MonView("Blaziken", 40, [TACKLE]), MonView("A", 10, [TACKLE]),
        MonView("B", 9, [TACKLE]), MonView("C", 8, [TACKLE])]
p5 = rotation_plan(four)
check(len(four) - len(p5["deposit"]) >= MIN_PARTY_AFTER_ROTATION,
      f"a 4-mon party keeps >=3 (deposited {len(p5['deposit'])})")
check(len(p5["deposit"]) == 1, f"so only the single worst is boxed this visit (got {p5['deposit']})")

# A three-mon party has no room to spare at all.
three = [MonView("Blaziken", 40, [TACKLE]), MonView("A", 9, [TACKLE]), MonView("B", 8, [TACKLE])]
check(rotation_plan(three)["deposit"] == [],
      "a 3-mon party deposits NOTHING — there is no room to spare")

print("\n== a rotation never empties the party of battle-capable mons ==")
allbad = [MonView("A", 40, [("Splash", 0)]), MonView("B", 5, [TACKLE])]
p2 = rotation_plan(allbad)
capable_left = [i for i in range(len(allbad))
                if i not in p2["deposit"] and allbad[i].has_damaging_move()]
check(len(capable_left) >= 1,
      f"at least one battle-capable mon is kept (deposit={p2['deposit']})")

print("\n== withdraw only fires when the party has NO sweeper for the fight ==")
score = lambda v: 100.0 if v.species == "Machoke" else 0.0
box = [MonView("Machoke", 30, [ARM_THRUST])]
weak = [MonView("A", 40, [TACKLE]), MonView("B", 38, [TACKLE])]
p3 = rotation_plan(weak, box, sweep_score=score, sweep_floor=80.0)
check(p3["withdraw"] == [0], f"withdraws the box answer when nothing in party sweeps (got {p3['withdraw']})")
strong = [MonView("Machoke", 40, [ARM_THRUST])]
p4 = rotation_plan(strong, box, sweep_score=score, sweep_floor=80.0)
check(p4["withdraw"] == [], "does NOT withdraw when the party already has a sweeper")

print()
if failures:
    print(f"FAIL ({len(failures)})")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print("PASS")
