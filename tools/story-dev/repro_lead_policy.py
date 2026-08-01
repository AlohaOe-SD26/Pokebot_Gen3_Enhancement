"""#24-leadpolicy (user ruling A+C): never lead a 1-HP Wonder Guard mon into a boss, and
prefer a lead that can actually damage the foe. NO EMULATOR — the rule is a pure sort key.

WHAT WENT WRONG (batch5, `x4-runs/20260801-075805`). The counter chain finally worked end to
end: 7 of 9 counters trained, `Machop L15 -> L29`, evolving into **Machoke**. And the badge
funnel did not move at all (Heat→Balance 83% → 79%). The reason:

    leads chosen for Norman — SHEDINJA x9, MARSHTOMP x4, SWAMPERT x4, BLAZIKEN x2 …
    MACHOKE: ZERO.

`_lead_best_matchup(["Normal"])` scored only defence, `min(incoming_multiplier, -level)`.
Shedinja is Bug/Ghost, so Normal → 0×, which wins that score outright. Then Slaking's Faint
Attack (Dark) is 2× on Ghost and one-shots its single hit point — invisible to a model that
does not read movepools. `#24-leadpolicy` had already predicted exactly this.

THE RULING WAS A+C AND THIS PINS EXACTLY THAT:
  (a) require the lead to also have a ≥neutral attacking option;
  (c) special-case 1-HP Wonder Guard mons.

‼ OPTION (b) — "weight the level gap so a resistant chaff mon can't bench a much stronger
one" — WAS NOT SELECTED. The Route 110 rival case (Whismur L15 led over Marshtomp L24) is
deliberately unchanged, and check 4 below PINS that it stays unchanged, so nobody "helpfully"
fixes it without a ruling.

‼ AND THE HONEST LIMIT, MEASURED HERE: on batch5's REAL Norman party, A+C stops the Shedinja
lead but still does NOT field the counter — Marshtomp L35 outranks Machoke L29 because
`can_attack` is binary and gives Machoke's 2× STAB no credit. Check 5 records that. Whether
super-effectiveness should outrank raw level is a NEW question, not covered by A+C.
"""

from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.story.team_policy import best_lead_index, lead_rank_key  # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


def mon(name, incoming, can_attack, glass, level):
    return {"name": name, "incoming": incoming, "can_attack": can_attack,
            "glass_wonder_guard": glass, "level": level}


print("1. (c) the batch5 Norman party — Shedinja must NOT be the lead")
# Exactly what the logs show: Shedinja L20 (Bug/Ghost, Normal->0x), the trained Machoke L29,
# and the team's strongest, Marshtomp L35.
party = [
    mon("Shedinja", 0.0, True, True, 20),
    mon("Machoke", 1.0, True, False, 29),
    mon("Marshtomp", 1.0, True, False, 35),
]
pick = best_lead_index(party)
print(f"       picked {party[pick]['name']}")
check("Shedinja is not chosen", party[pick]["name"] != "Shedinja")
check("the chosen lead can attack", party[pick]["can_attack"])

print("2. (c) but Shedinja IS still chosen when it is the only option")
# The rule must be a SORT TERM, not a filter — a filter could leave no lead at all.
only = [mon("Shedinja", 0.0, True, True, 20)]
check("a lone Wonder Guard mon is still led", best_lead_index(only) == 0)
check("an empty party yields None rather than raising", best_lead_index([]) is None)

print("3. (a) a mon that cannot damage the foe loses to one that can")
pair = [
    mon("Wall", 0.5, False, False, 40),      # resists better, cannot hurt it
    mon("Attacker", 1.0, True, False, 25),   # neutral, but can actually win
]
pick = best_lead_index(pair)
print(f"       picked {pair[pick]['name']}")
check("the attacker is preferred over the un-armed wall", pair[pick]["name"] == "Attacker")

print("4. ‼ (b) WAS NOT RULED — the Rustboro/Route-110 behaviour must be UNCHANGED")
# Whismur resists the Grovyle and can hit it neutrally; Marshtomp is 4x weak. The old rule
# led Whismur, and A+C must keep doing so. If this ever flips, someone implemented (b)
# without a ruling.
rustboro = [
    mon("Whismur", 1.0, True, False, 15),
    mon("Marshtomp", 4.0, True, False, 24),
]
pick = best_lead_index(rustboro)
check(
    "Whismur still leads over the 4x-weak Marshtomp (option (b) NOT implemented)",
    rustboro[pick]["name"] == "Whismur",
    f"picked {rustboro[pick]['name']}",
)

print("5. the HONEST LIMIT of A+C — it does not yet field the trained counter")
# Recorded as an assertion so the limitation cannot be quietly forgotten or overclaimed.
pick = best_lead_index(party)
check(
    "A+C picks the strongest neutral mon, NOT the super-effective counter",
    party[pick]["name"] == "Marshtomp",
    "Machoke's 2x STAB gets no credit because `can_attack` is binary — giving "
    "super-effectiveness weight is a NEW decision, not part of ruling A+C",
)

print("6. the key is ordered as documented")
# (c) dominates (a) dominates incoming dominates level.
check("glass Wonder Guard outranks every other term",
      lead_rank_key(incoming=0.0, can_attack=True, glass_wonder_guard=True, level=99)
      > lead_rank_key(incoming=4.0, can_attack=False, glass_wonder_guard=False, level=1))
check("can_attack outranks the incoming multiplier",
      lead_rank_key(incoming=0.25, can_attack=False, glass_wonder_guard=False, level=99)
      > lead_rank_key(incoming=4.0, can_attack=True, glass_wonder_guard=False, level=1))
check("incoming outranks the level tie-break",
      lead_rank_key(incoming=2.0, can_attack=True, glass_wonder_guard=False, level=99)
      > lead_rank_key(incoming=1.0, can_attack=True, glass_wonder_guard=False, level=1))

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
