"""A HUNTED COUNTER outranks a stronger neutral mon — but never overrides type safety.
NO EMULATOR — the rule is a pure sort key.

USER RULING 2026-08-02 (`06-DECISIONS-LOG`): super-effectiveness outranks raw level **only**
when the counter chain caught that mon for THIS boss. Not as a general rule.

WHY. `#24-leadpolicy` A+C stopped the bot leading a 1-HP Wonder Guard Shedinja into Norman
(9 of 9 runs in batch5). But `can_attack` is binary, so on the real party —
Shedinja L20 / **Machoke L29** / Marshtomp L35 — Machoke and Marshtomp tie on every term the
key measures and **level breaks the tie**. The counter the chain had just travelled for,
caught and trained to L29 was benched again, now by a stronger neutral mon. The chain only
fires after ~6 losses, so for that boss the strongest mon is already PROVEN insufficient.

‼ ORDERING IS THE WHOLE DESIGN:

    (glass_wonder_guard, not can_attack, incoming, not is_hunted_counter, -level)

`is_hunted_counter` sits AFTER `incoming` on purpose. It promotes the counter over an
EQUALLY SAFE mon; it must never let a counter that is 4x weak to the boss lead. Check 3
pins that, because getting it backwards is the plausible way this fix becomes a new bug.

‼ RED until the sandbox edit lands — deliberately held while batch 20260802-160603 runs,
because `x4_headless.py:843` relaunches dead lanes, which re-import from disk.
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


def mon(name, incoming, can_attack, glass, level, hunted=False):
    return {"name": name, "incoming": incoming, "can_attack": can_attack,
            "glass_wonder_guard": glass, "level": level, "is_hunted_counter": hunted}


import inspect  # noqa: E402

sig = inspect.signature(lead_rank_key)
HAS_TERM = "is_hunted_counter" in sig.parameters
check("lead_rank_key accepts is_hunted_counter", HAS_TERM,
      "NOT YET ADDED — edit held until batch 20260802-160603 lands" if not HAS_TERM else "")

if HAS_TERM:
    print("1. the batch5 Norman party — the trained counter now leads")
    party = [
        mon("Shedinja", 0.0, True, True, 20),
        mon("Machoke", 1.0, True, False, 29, hunted=True),   # caught + trained for THIS boss
        mon("Marshtomp", 1.0, True, False, 35),
    ]
    pick = best_lead_index(party)
    print(f"       picked {party[pick]['name']}")
    check("Machoke leads, not Marshtomp L35", party[pick]["name"] == "Machoke")
    check("and certainly not Shedinja", party[pick]["name"] != "Shedinja")

    print("2. without the flag, nothing changes (the ruling is SCOPED)")
    same = [dict(m, is_hunted_counter=False) for m in party]
    pick = best_lead_index(same)
    check("an unflagged L29 still loses to the stronger neutral L35",
          same[pick]["name"] == "Marshtomp", f"picked {same[pick]['name']}")

    print("3. ‼ it must NOT override type safety")
    # A hunted counter that is 4x weak to the boss must still lose on `incoming`.
    risky = [
        mon("GlassCounter", 4.0, True, False, 30, hunted=True),
        mon("SafeMon", 1.0, True, False, 25),
    ]
    pick = best_lead_index(risky)
    check("a 4x-weak hunted counter does NOT lead", risky[pick]["name"] == "SafeMon",
          f"picked {risky[pick]['name']}")

    print("4. it does not resurrect the Wonder Guard trap")
    trap = [
        mon("Shedinja", 0.0, True, True, 20, hunted=True),   # even if somehow flagged
        mon("Machoke", 1.0, True, False, 29),
    ]
    pick = best_lead_index(trap)
    check("a flagged 1-HP Wonder Guard mon still does not lead",
          trap[pick]["name"] != "Shedinja", f"picked {trap[pick]['name']}")

    print("5. the term sits between incoming and the level tie-break")
    check("is_hunted_counter beats a higher level",
          lead_rank_key(incoming=1.0, can_attack=True, glass_wonder_guard=False,
                        level=29, is_hunted_counter=True)
          < lead_rank_key(incoming=1.0, can_attack=True, glass_wonder_guard=False,
                          level=35, is_hunted_counter=False))
    check("but incoming still beats is_hunted_counter",
          lead_rank_key(incoming=1.0, can_attack=True, glass_wonder_guard=False,
                        level=25, is_hunted_counter=False)
          < lead_rank_key(incoming=4.0, can_attack=True, glass_wonder_guard=False,
                          level=30, is_hunted_counter=True))

    print("6. the flag is OPTIONAL — existing callers keep working")
    try:
        lead_rank_key(incoming=1.0, can_attack=True, glass_wonder_guard=False, level=20)
        check("is_hunted_counter defaults to False", True)
    except TypeError as error:
        check("is_hunted_counter defaults to False", False, str(error))

print("7. ‼ THE DECISION IS OBSERVABLE (batch7 could not be diagnosed without this)")
# 6 runs caught AND trained a Machop to L29 and every one still led something else into
# Norman - and nothing in the log said whether hunted_pids was empty, whether the mon was a
# candidate, or how it scored. A decision with no trace cannot be debugged from a batch.
import re as _re  # noqa: E402

eg = (REPO / "sandbox-pokebot" / "modules" / "story" / "early_game.py").read_text(
    encoding="utf-8", errors="replace")
fn = _re.search(r"def _lead_best_matchup\(.*?(?=\ndef )", eg, _re.S)
check("_lead_best_matchup is present", fn is not None)
if fn:
    body = fn.group(0)
    check("it logs the chosen lead", "Story: lead vs" in body)
    check("it logs the CANDIDATE SET, not just the winner", "from {" in body or "from " in body)
    check("it logs hunted_pids count (empty-set is the prime suspect)",
          "hunted_pids=" in body)
    check("it logs the per-mon inputs that drove the key",
          all(t in body for t in ("in=", "COUNTER", "NOATK")))
    check("logging cannot affect the choice (guarded)",
          _re.search(r"except Exception:.*?# noqa: BLE001 - logging must never", body, _re.S)
          is not None)

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
