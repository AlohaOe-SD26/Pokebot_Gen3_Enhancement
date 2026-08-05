"""#24-pcoverflow: a full party must no longer REFUSE a catch — the mon goes to the box and
is collected later. NO EMULATOR.

USER RULING 2026-08-05: build the real thing rather than raise a constant. Until now:

    resource_blocker() -> "the party is full, so a catch would go to the PC box (needs #24-pc)"

That refusal fired **5 times in batch5**, blocking the counter chain outright, and it is the
reason a user watching a live run sees teams that never grow.

‼ THE TWO HALVES MUST SHIP TOGETHER. Relaxing the refusal ALONE would be strictly WORSE than
the refusal: the counter would be caught — paid for with a cross-Hoenn journey — and then sit
in the box unusable. So this file asserts both:
  * `resource_blocker` no longer refuses on a full party (but STILL refuses with no balls);
  * `pc_trip.withdraw_from_box` exists, is wired into the heal, frees exactly ONE slot, and
    never deposits the very mon it came to collect.

‼ FREEING EXACTLY ONE SLOT IS NOT AN ARBITRARY CHOICE. `#24-pc` thinned parties by ~1 mon per
run and cost ~19 points of the Balance→Feather rung (08-MISTAKES 2026-08-05). A withdraw that
deposits generously would reintroduce that regression by a different door.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"
sys.path.insert(0, str(SANDBOX))

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


from modules.story import counter_hunt, pc_trip  # noqa: E402

print("1. ‼ a FULL PARTY no longer refuses the catch")
# ‼ Checked by AST, not text search. The removed rule is still described in a COMMENT right
# there, so a `"party is full" in source` test passes while the behaviour is either way — it
# did exactly that on the first attempt at this check.
import inspect  # noqa: E402

tree = ast.parse(inspect.getsource(counter_hunt.resource_blocker).lstrip())
returns = [ast.unparse(n.value) if n.value else "None"
           for n in ast.walk(tree) if isinstance(n, ast.Return)]
check("no executable return mentions a full party",
      not any("party is full" in r for r in returns), str(returns))
check("the party count is no longer consulted at all",
      "_party_count" not in ast.unparse(tree))

print("2. but the BALL gate is untouched — a catch still needs a ball")
check("it still refuses with no spare balls",
      any("no spare" in r for r in returns), str(returns))
check("the last-ball reserve rule is intact", any("last ball is reserved" in r for r in returns))

print("3. the collection half exists")
check("box_views() is available", callable(pc_trip.box_views))
check("find_in_box() is available", callable(pc_trip.find_in_box))
check("withdraw_from_box() is available", callable(pc_trip.withdraw_from_box))

print("4. ‼ it is WIRED — an uncollected catch is worse than no catch")
heal_src = (SANDBOX / "modules" / "modes" / "util" / "higher_level_actions.py").read_text(
    encoding="utf-8", errors="replace")
fn = re.search(r"def heal_in_pokemon_center\(.*?(?=\ndef )", heal_src, re.S)
check("heal_in_pokemon_center located", fn is not None)
if fn:
    body = fn.group(0)
    check("the heal calls withdraw_from_box", "withdraw_from_box" in body)
    check("it passes the hunted-counter PIDs", "_hunted_counter_pids" in body)
    i_nurse = body.find("wait_for_yes_no_question")
    i_wd = body.find("withdraw_from_box")
    i_exit = body.find("Get out — robustly")
    check("ordering is nurse -> collect -> exit", -1 < i_nurse < i_wd < i_exit,
          f"nurse@{i_nurse} withdraw@{i_wd} exit@{i_exit}")

print("5. ‼ it frees exactly ONE slot, and never deposits its own target")
wd = ast.parse((SANDBOX / "modules" / "story" / "pc_trip.py").read_text(
    encoding="utf-8", errors="replace"))
src_wd = next((ast.unparse(n) for n in ast.walk(wd)
               if isinstance(n, ast.FunctionDef) and n.name == "withdraw_from_box"), "")
check("it only deposits when the party is full", "len(alive) >= 6" in src_wd)
check("it breaks after ONE deposit rather than looping", src_wd.count("break") >= 1)
check("it skips the mon it came to collect",
      "personality_value in (pids" in src_wd or "continue" in src_wd)
check("it gives up cleanly when nothing is safe to deposit", "leaving it boxed" in src_wd)

print("6. everything degrades with no emulator")
check("box_views returns empty pairs", pc_trip.box_views() == ([], []))
check("find_in_box returns None", pc_trip.find_in_box({1, 2}) is None)
check("find_in_box on an empty pid set returns None", pc_trip.find_in_box(set()) is None)

print()
if FAILURES:
    print(f"REPRO: {len(FAILURES)} FAILING CHECK(S) — {', '.join(FAILURES)}")
    sys.exit(1)
print("REPRO: all checks pass.")
