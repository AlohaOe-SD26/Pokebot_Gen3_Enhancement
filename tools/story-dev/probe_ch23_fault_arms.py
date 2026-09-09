"""GATE — every §Ch23 fault arm is REGISTERED, and every registered arm is REAL.

WHY THIS EXISTS (measured 2026-09-04, and it cost a live run).
`victory_road._fault(arm)` builds its env name with an f-string:
`os.environ.get(f"POKEBOT_CH23_FAULT_{arm}")`. So an arm that is never registered — or is
mistyped — reads a variable nobody sets and returns **False forever**. ⛔ **A FAULT HOOK THAT
CANNOT FIRE IS WORSE THAN NO FAULT HOOK, because it reads as tested while testing nothing.**

Seven arms were in use and **only one** was registered; `NOLEAD5` (leg 5's "do not lead the
strongest battler into the Wally fight") had been dead the entire time. It surfaced only when a
runtime guard was added and a real drive blew up on it. ⇒ **A RUNTIME RAISE ONLY FIRES IF SOMEONE
HAPPENS TO DRIVE THAT LEG.** This gate is the static half, and it runs in seconds.

It checks three things, all statically:
  1. every `_fault("X")` call site has an entry in `FAULT_ARMS`   (the bug that bit us)
  2. every `FAULT_ARMS` entry is actually CALLED somewhere        (a registered arm nobody reads
     is a lie in the other direction — it advertises a switch that does nothing)
  3. every `FAULT_ARMS` env name maps to `POKEBOT_CH23_FAULT_<ARM>` exactly, and has a row in
     `29-DISABLED-FEATURES-REGISTRY.md`                           (`lint_docs` R6's other half)

FAULT TEST (rule: a gate that cannot fail is decoration):
    POKEBOT_CH23ARMS_FAULT=unregistered  -> pretend a call site uses an arm nobody registered;
                                            CHECK 1 must go RED and the probe must exit 1
    POKEBOT_CH23ARMS_FAULT=orphan        -> pretend an arm is registered but never called;
                                            CHECK 2 must go RED and the probe must exit 1
    POKEBOT_CH23ARMS_FAULT=noregistry    -> pretend an arm is missing its registry row;
                                            CHECK 3 must go RED and the probe must exit 1
‼ It must also NOT fire on mentions in comments or docstrings — a gate with false positives
teaches the reader to bypass it. `_fault("NOHEAL")` inside a comment is not a call site, and the
AST walk below is what makes that distinction reliable (a regex over the file would not).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_ch23_fault_arms.py
"""

from __future__ import annotations

import ast
import os
import pathlib
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "sandbox-pokebot" / "modules" / "story" / "victory_road.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
PREFIX = "POKEBOT_CH23_FAULT_"

FAULT = os.environ.get("POKEBOT_CH23ARMS_FAULT", "").strip()
failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    print(f"  {'✅ PASS' if ok else '❌ FAIL'} — {label}")
    if detail:
        print(f"           {detail}")
    if not ok:
        failures.append(label)


def registered_arms(tree: ast.Module) -> dict:
    """Read `FAULT_ARMS` as a literal. ⛔ Never import the module — it pulls the whole bot in."""
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "FAULT_ARMS":
            return ast.literal_eval(node.value)
    raise SystemExit("probe: FAULT_ARMS not found in victory_road.py — has it been renamed?")


def called_arms(tree: ast.Module) -> set:
    """Every `_fault("X")` CALL — via the AST, so comments and docstrings are invisible to it."""
    out = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name) and node.func.id == "_fault"
                and node.args and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            out.add(node.args[0].value)
    return out


def main() -> int:
    src = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    registry_text = REGISTRY.read_text(encoding="utf-8")

    arms = dict(registered_arms(tree))
    used = set(called_arms(tree))

    if FAULT == "unregistered":
        used.add("PHANTOMARM")                      # a call site nobody registered
    elif FAULT == "orphan":
        arms["ORPHANARM"] = PREFIX + "ORPHANARM"    # a registration nobody calls
    elif FAULT == "noregistry":
        arms["UNDOCARM"] = PREFIX + "UNDOCARM"      # registered + called, but no doc row
        used.add("UNDOCARM")
    if FAULT:
        print(f"‼ FAULT ARM ACTIVE: POKEBOT_CH23ARMS_FAULT={FAULT} — this probe MUST report FAIL.\n")

    print(f"registered ({len(arms)}): {sorted(arms)}")
    print(f"called     ({len(used)}): {sorted(used)}\n")

    # ---- CHECK 1: every call site is registered (the bug that actually bit) --------------------
    unregistered = sorted(used - set(arms))
    check(not unregistered,
          "every `_fault(...)` call site has a FAULT_ARMS entry",
          f"UNREGISTERED — these read an env var nobody sets and can NEVER fire: {unregistered}"
          if unregistered else f"all {len(used)} call sites registered")

    # ---- CHECK 2: every registered arm is really called ----------------------------------------
    orphans = sorted(set(arms) - used)
    check(not orphans,
          "every FAULT_ARMS entry is called somewhere",
          f"ORPHANED — advertised in FAULT_ARMS but no `_fault()` reads them: {orphans}"
          if orphans else f"all {len(arms)} registered arms are called")

    # ---- CHECK 3: names are canonical AND documented --------------------------------------------
    misnamed = sorted(a for a, env in arms.items() if env != PREFIX + a)
    check(not misnamed,
          f"every env name is exactly {PREFIX}<ARM>",
          f"MISNAMED (the f-string in `_fault` would build a different name): {misnamed}"
          if misnamed else "all names canonical")

    undocumented = sorted(env for env in arms.values() if env not in registry_text)
    check(not undocumented,
          "every arm has a row in 29-DISABLED-FEATURES-REGISTRY.md",
          f"UNDOCUMENTED — `lint_docs` R6 wants these findable: {undocumented}"
          if undocumented else f"all {len(arms)} arms documented")

    print()
    if failures:
        print(f"❌ {len(failures)} CHECK(S) FAILED: {failures}")
        if not FAULT:
            print("⇒ A fault arm that is not registered CANNOT FIRE. Add it to `FAULT_ARMS` in "
                  "victory_road.py (and give it a registry row) — do NOT delete the call site to "
                  "make this green.")
        return 1
    if FAULT:
        print("❌ THE FAULT ARM DID NOT TRIP THIS GATE — the gate cannot fail, so it proves nothing.")
        return 1
    print(f"✅ ALL CHECKS PASS — {len(arms)} fault arms, every one registered, called and documented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
