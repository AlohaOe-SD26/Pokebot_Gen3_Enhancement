"""GATE — the KI-63 party-slot wiring is intact, end to end, in PRODUCTION.

WHY THIS EXISTS. KI-63's fix was built, driven to a PASS, documented and PROMOTED while
`_needs_party_slot` had **no setter anywhere in production**. Every piece existed and the chain
was still dead: in a real `StoryMode` run the piggyback never fired and `ensure_hm_learner` still
derailed the whole run. Nothing caught that — not a test, not a gate, not a green driver. It was
found by an adversarial review reading the diff.

‼ That is the exact failure shape this gate exists to prevent: **a chain of individually-correct
parts with one link missing.** Each assertion below is one link.

It is a STATIC gate on purpose — it costs a second, needs no emulator, and can run in the standing
suite. It cannot prove the chain WORKS (only a drive does that, `--driver divelearner`); it proves
the chain is still CONNECTED.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_hm_slot_wiring.py
Exits 1 on any broken link.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[2] / "sandbox-pokebot"
EARLY = SANDBOX / "modules" / "story" / "early_game.py"
STORY_MODE = SANDBOX / "plugins" / "custom_modes" / "story_mode.py"
HEAL = SANDBOX / "modules" / "modes" / "util" / "higher_level_actions.py"
PC_TRIP = SANDBOX / "modules" / "story" / "pc_trip.py"

WRAPPER = "ensure_hm_learner_making_room"
FLAG = "_needs_party_slot"

failures: list[str] = []
checks = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    if detail:
        print(f"        {detail}")
    if not ok:
        failures.append(label)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


print("=" * 96)
print("GATE — KI-63 party-slot wiring (a chain of correct parts with one link missing is DEAD)")
print("=" * 96)

# ‼ CONTROL FIRST. If the files themselves are missing or unparseable, every FAIL below would be
# an artifact of that rather than a real broken link.
print("\n0 — CONTROLS (so a FAIL below is attributable to the wiring, not to a bad read)")
for path in (EARLY, STORY_MODE, HEAL, PC_TRIP):
    check(f"readable + parses: {path.name}", path.is_file() and bool(ast.parse(read(path))))

early_src = read(EARLY)
mode_src = read(STORY_MODE)
heal_src = read(HEAL)
pc_src = read(PC_TRIP)

print("\n1 — THE WRAPPER EXISTS AND BEHAVES AS SPECIFIED")
early_tree = ast.parse(early_src)
wrapper = next((n for n in ast.walk(early_tree)
                if isinstance(n, ast.FunctionDef) and n.name == WRAPPER), None)
check(f"`{WRAPPER}` is defined in early_game.py", wrapper is not None)

if wrapper is not None:
    wsrc = ast.get_source_segment(early_src, wrapper) or ""
    # It must deposit ONLY for the party-full case. Any other failure deposits a team member for
    # the wrong diagnosis and leaves the run strictly worse off than the honest derail.
    check("it gates on the 'party is full' message specifically",
          '"party is full" not in str(error)' in wsrc,
          "otherwise it would box a Pokemon to 'fix' an unrelated failure")
    check("it re-raises anything else unchanged", "            raise\n" in wsrc)
    # KI-67: a whiteout unwind must never be swallowed by a broad except.
    check("it calls reraise_if_aborting FIRST in the handler (KI-67)",
          "reraise_if_aborting(error)" in wsrc)
    check(f"it SETS {FLAG}", f'setattr(mode, "{FLAG}", True)' in wsrc)
    # If the flag is left armed it fires on EVERY later heal - the measured harm that keeps
    # POKEBOT_PC_ROTATION pinned at 0.
    check(f"it CLEARS {FLAG} in a finally (never leave the hook armed)",
          f'setattr(mode, "{FLAG}", False)' in wsrc and "finally:" in wsrc)
    check("it verifies a slot was actually freed before retrying",
          "if after >= before:" in wsrc,
          "a truthful postcondition, not 'the PC call returned'")
    check("it re-raises the ORIGINAL error when nothing was freed",
          "raise original" in wsrc,
          "inventing a new message would send the reader after the wrong bug")
    check("it retries EXACTLY ONCE (no loop around the retry)",
          wsrc.count("yield from ensure_hm_learner(item)") == 2
          and "while" not in wsrc.split("freed a slot")[-1],
          "a loop would deposit a second team member on the next pass")

print("\n2 — PRODUCTION ACTUALLY CALLS IT (the link that was missing)")
mode_tree = ast.parse(mode_src)
called = {n.func.id for n in ast.walk(mode_tree)
          if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
check(f"story_mode.py calls `{WRAPPER}`", WRAPPER in called)
check("story_mode.py no longer calls bare `ensure_hm_learner`",
      "ensure_hm_learner" not in called,
      "a bare call is the pre-KI-63 behaviour: a full party ends the run")
n_sites = mode_src.count(f"yield from {WRAPPER}(")
check("both known HM call sites are wired (Rock Smash + Surf)", n_sites >= 2,
      f"found {n_sites}; expected 2 (HM06 at ~3232, HM03 at ~3437)")

print("\n3 — THE PIGGYBACK STILL READS THE FLAG")
check(f"heal_in_pokemon_center reads {FLAG}", f'"{FLAG}", False' in heal_src)
check("…and calls deposit_one_dead_weight", "deposit_one_dead_weight()" in heal_src)

print("\n4 — THE DEPOSIT PRIMITIVE IS STILL THE UNGATED, ONE-SHOT ONE")
# ‼ EXTRACT WITH AST, NOT `str.split`. The first draft of this gate sliced the file on
# `"def deposit_one_dead_weight"` and searched the result for `POKEBOT_PC_ROTATION` — and FAILED,
# because the function's DOCSTRING names that flag while explaining why the OTHER deposit path is
# gated off. A gate that fires on prose is worse than no gate: it trains the reader to ignore it.
pc_tree = ast.parse(pc_src)
depositor = next((n for n in ast.walk(pc_tree)
                  if isinstance(n, ast.FunctionDef) and n.name == "deposit_one_dead_weight"), None)
check("deposit_one_dead_weight exists", depositor is not None)

if depositor is not None:
    # Strip the docstring, then look only at executable code.
    body = [n for n in depositor.body
            if not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                    and isinstance(n.value.value, str))]
    code = "\n".join(ast.get_source_segment(pc_src, n) or "" for n in body)
    check("it is NOT gated on an env flag (POKEBOT_PC_ROTATION or any other)",
          "environ" not in code,
          "that flag is pinned 0 and measured harmful; gating here would make it a silent no-op")
    check("it counts OCCUPIED slots, not 'alive' (an egg occupies a slot)",
          "_occupied" in code and "is_egg" not in code,
          "counting non-egg mons made a 5-mons+1-egg party report 'already has room'")
    check("it deposits at most ONE Pokemon",
          code.count("deposit_pokemon_to_box") == 1,
          "thinning the team is what made #24-pc a regression (~1 mon/run)")

print("\n" + "=" * 96)
print(f"RESULT: {'ALL PASS' if not failures else 'FAIL'}  ({checks - len(failures)}/{checks} checks)")
if failures:
    print("\nBROKEN LINKS:")
    for f in failures:
        print(f"  - {f}")
    print("\n‼ A chain of individually-correct parts with one link missing is DEAD. Fix the link.")
print("=" * 96)
sys.exit(1 if failures else 0)
