"""`#24-movepoolcounters`: a counter is a MOVE, not a TYPE. NO EMULATOR — source + cache only.

WHY (user directive 2026-08-07): "some pokemon can learn moves of types that can be a counter so
its not just the pokemon type… know the difference between damaging moves, passive/defensive/
stat boosting/debuff moves and area/effect moves as well as status moves with no damage".

MEASURED CONSEQUENCE — this is not a nicety, it was a total blocker:
Across all ELEVEN huntable grounds, Winona's needed types (Rock/Ice/Dragon) appear **exactly
once**: Geodude on ROUTE111 via **Rock Smash** — and `counter_plan` accepts `method == "Grass"`
only. **Grass-method matches: 0.** With pure species typing Winona has ZERO huntable candidates,
which is why `no huntable counter candidate` was 10 occurrences in one batch and why
`no super-effective answer` is now 75% of all non-finishes.

Movepool-aware, she gets two, both Grass, both on grounds the bot already walks, and both caught
ALREADY KNOWING the move:
    Baltoy @ ROUTE111   Grass 24% L19-21 — Rock Tomb  learned at L15
    Slugma @ FIERY_PATH Grass 10% L15    — Rock Throw learned at L15
(FIERY_PATH is where Norman's hunt already succeeds 6 of 7 times.)

‼ THE UNFILTERED VERSION IS WORSE THAN PURE TYPING and this file pins the three gates that stop
it: raw "can learn a move of a needed type" yields +82 for Winona and +47 for Norman, almost all
TM13 Ice Beam / TM14 Blizzard (single-use TMs we do not own) and HM06 Rock Smash at **20 power**
— the exact case the credible-power floor exists to reject.
"""
from __future__ import annotations
import ast, pathlib, re, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
CP = REPO / "sandbox-pokebot" / "modules" / "story" / "counter_plan.py"
FAILURES: list[str] = []

def check(label, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)

src = CP.read_text(encoding="utf-8")
ast.parse(src)

print("1. the type-only rejection is gone")
check("no bare `if not hit_types: continue`",
      not re.search(r"if not hit_types:\s*\n\s*continue\b", src),
      "that single line is what gave Winona zero candidates")
check("rejection now requires BOTH no type match AND no move answer",
      "if not hit_types and move_answer is None:" in src)

print()
print("2. the three mandatory gates are present on the move path")
blk = re.search(r"move_answer = None\n(.*?)\n            if not hit_types and move_answer is None:", src, re.S)
check("the move-answer block can be located", blk is not None)
b = blk.group(1) if blk else ""
check("GATE 1 damaging only — rejects base_power <= 0", "mv.base_power <= 0" in b,
      "stat-change / field-effect / pure-status moves cannot answer a type weakness")
check("GATE 2 level-up learnset only (no TM/tutor assumptions)",
      "species.learnset.level_up" in b and "tm_hm" not in b,
      "Gen 3 TMs are single-use and we may not own them")
check("GATE 2b it must already know the move when caught",
      "entry.level > _loc_max_level" in b)
check("GATE 3 credible power floor applied",
      "_CREDIBLE_ANSWER_POWER" in b)
check("effectiveness is applied, not assumed", "* 2.0 *" in b)
check("STAB is applied", "stab" in b)

print()
print("3. the decision is auditable")
check("candidates record WHY they qualified (`answer_via`)", '"answer_via"' in src)
check("a move answer names the move and its level", 'f"move:{move_answer[1].name}@L{move_answer[0]}"' in src)

print()
print("4. ‼ HUNTABILITY OUTRANKS TYPE COVERAGE in `tier`")
# Without this the movepool fix is INERT. Measured before it: Winona's list sorted to 43
# candidates led by Geodude in MAGMA_HIDEOUT (type match, no spin tile, unhuntable) with the one
# genuinely huntable candidate — Slugma @ FIERY_PATH — at **rank 42**. Callers pass
# max_results=5, so `best_huntable` never saw it and the run reported "no huntable candidate".
tier = re.search(r"tier = \((.*?)\n                \)", src, re.S)
check("the tier expression can be located", tier is not None)
t = tier.group(1) if tier else ""
check("huntability is a tier term", "hunt_tile is not None" in t)
check("it outranks type coverage",
      t.find("100_000_000.0") != -1 and t.find("100_000_000.0") < t.find("len(hit_types)"),
      "an unhuntable candidate must never sort above a huntable one — no caller can use it")
check("reachability still outranks everything", t.find("1_000_000_000.0") < t.find("100_000_000.0"))
check("type coverage still ranks above a mere training tile",
      t.find("len(hit_types)") < t.find("100_000.0 if tile"))
check("hunt_tile is computed BEFORE tier uses it",
      src.find("hunt_tile = hunt_ground_tile(map_enum)") < src.find("tier = ("))

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)} check(s):")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
print("ALL PASS")
