# -*- coding: utf-8 -*-
"""GATE #73 — EVERY ITEM NAME IN AN ITEM POLICY TABLE MUST RESOLVE TO A REAL ITEM.

⛔⛔ THE BUG THIS EXISTS TO PREVENT, FOUND 2026-09-24 BY A RECON AGENT AND VERIFIED AGAINST OUR OWN
DATA. `modules/story/overworld_items.py` names **`"Paralyze Heal"`** in two places — `STATUS_ONLY`
(`:62`) and the `healing_items` fallback allowlist (`:152`). **There is no such item.** Gen-3's item
is spelled **`"Parlyz Heal"`**, which is what `modules/data/items.json` actually contains.

⇒ `held.get("Paralyze Heal", 0)` can only ever return **0**, so that entry is DEAD. And the
allowlist's own docstring says *"an item not named here is not used"* — so the misspelling does not
fail loudly, it **silently removes a real item from the bot's options.**

‼ WHY THIS IS THE DANGEROUS SHAPE RATHER THAN A TYPO. `pokemon_league.py`'s header already records
two previous instances of exactly this class — *"Repel selected because `parameter > 0`"* and
*"an allowlist silently empty because `field_use` is an enum"*. Each was a table that looked right
and matched nothing. A name that resolves to nothing produces **a missing action, never an error**,
and the gauntlet is the one place in the game where a missing heal cannot be retried: five fights,
no nurse past the lobby door, and no way back.

⛔ AND NO EXISTING GATE COVERED IT. `repro_item_noop_detector.py` gates the no-op detector's STATE
MACHINE; `repro_battle_items.py` runs pure-function and static-source checks over the battle policy.
Neither asks the flat question *"is this string an item?"*.

────────────────────────────────────────────────────────────────────────────────────────────────────
WHAT IT CHECKS
────────────────────────────────────────────────────────────────────────────────────────────────────
AST-parses the scoped files and collects string literals from ITEM POLICY TABLES only:
  * module-level assignments whose name matches `_TABLE_NAMES` (e.g. `STATUS_ONLY`, `LEAGUE_BASKET`,
    anything ending `_ITEMS` / `_BASKET` / `_HEALING`), and
  * default values of parameters named in `_PARAM_NAMES` (e.g. `healing_items`),
then asserts every string resolves to a name in `modules/data/items.json`.

⛔ SCOPED TO TABLES, NOT TO EVERY STRING. Scanning every literal would flag prose, log text and map
names, and a gate with false positives teaches the reader to bypass it (CLAUDE.md rule 6). The
trade is deliberate: this cannot see an item name built at runtime or passed in from a caller.

FAULT ARMS:
    --fault phantom    inject a name that is not an item        → must FAIL
    --fault prose      a non-item string OUTSIDE a policy table → must PASS (no false positive)
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SANDBOX = REPO / "sandbox-pokebot"
ITEMS_JSON = SANDBOX / "modules" / "data" / "items.json"

#: The files that carry item policy. Narrow on purpose — see the docstring.
SCOPED = [
    "modules/story/overworld_items.py",
    "modules/story/pokemon_league.py",
    "modules/story/victory_road.py",
    "modules/battle_items.py",
]

_TABLE_RE = re.compile(r"^(STATUS_ONLY|LEAGUE_BASKET|.*_ITEMS|.*_BASKET|.*_HEALING|.*_CURES)$")
_PARAM_NAMES = {"healing_items", "allowlist", "items"}


def canonical_item_names() -> set[str]:
    raw = json.loads(ITEMS_JSON.read_text(encoding="utf-8", errors="replace"))
    names: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in ("name", "Name") and isinstance(v, str):
                    names.add(v)
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(raw)
    if isinstance(raw, dict):
        names.update(k for k in raw.keys() if isinstance(k, str))
    return names


def _strings_in(node) -> list[tuple[str, int]]:
    out = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            out.append((sub.value, getattr(sub, "lineno", 0)))
    return out


def policy_strings(path: pathlib.Path) -> list[tuple[str, int]]:
    """String literals that live inside an item POLICY TABLE."""
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    found: list[tuple[str, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and _TABLE_RE.match(tgt.id):
                    found += _strings_in(node.value)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            defaults = list(args.defaults) + [d for d in args.kw_defaults if d is not None]
            named = [a.arg for a in list(args.args) + list(args.kwonlyargs)]
            for d in defaults:
                if any(n in _PARAM_NAMES for n in named):
                    found += _strings_in(d)
            for stmt in node.body:
                if isinstance(stmt, ast.If):
                    for sub in ast.walk(stmt):
                        if isinstance(sub, ast.Assign):
                            for tgt in sub.targets:
                                if isinstance(tgt, ast.Name) and tgt.id in _PARAM_NAMES:
                                    found += _strings_in(sub.value)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fault", choices=["phantom", "prose"])
    args = ap.parse_args()

    bar = "=" * 100
    print(bar)
    print("GATE #73 — EVERY ITEM NAME IN A POLICY TABLE RESOLVES TO A REAL ITEM")
    print(bar)

    if not ITEMS_JSON.exists():
        print(f"  ⛔ cannot find {ITEMS_JSON}")
        return 1

    items = canonical_item_names()
    print(f"  items.json carries {len(items)} distinct item name(s)")

    problems: list[str] = []
    scanned = 0
    for rel in SCOPED:
        p = SANDBOX / rel
        if not p.exists():
            print(f"  ⚠ scoped file missing, skipped: {rel}")
            continue
        scanned += 1
        found = policy_strings(p)
        if args.fault == "phantom" and rel.endswith("overworld_items.py"):
            found = found + [("Definitely Not An Item", 0)]
        for s, line in found:
            # Only strings that LOOK like item names are candidates; a policy table can legitimately
            # hold a flag name or a short key. An item name is Title Case words.
            if not re.match(r"^[A-Z][A-Za-z]+(?: [A-Z0-9][A-Za-z0-9]*)*$", s):
                continue
            if s not in items:
                problems.append(f"{rel}:{line}  “{s}” is NOT in items.json")

    print(f"  scanned {scanned} scoped file(s)")
    print()

    if args.fault == "prose":
        # ‼ THE FALSE-POSITIVE ARM: a non-item Title-Case string that is NOT inside a policy table
        # must not be flagged. `SCOPED` files are full of them (map names, log text, docstrings).
        if problems:
            print("  ⛔ FAULT ARM `prose` FAILED — the gate flagged something outside a policy table.")
            for q in problems:
                print(f"      {q}")
            return 1
        print("  ✅ FAULT ARM `prose` PASSED — Title-Case prose outside a policy table is ignored.")
        print(bar)
        return 0

    if problems:
        print("  ⛔ FAILED — an item policy table names something that is not an item:")
        for q in sorted(set(problems)):
            print(f"      {q}")
        print()
        print("  ⇒ A name that resolves to nothing produces A MISSING ACTION, NEVER AN ERROR. In an")
        print("     allowlist whose own rule is “an item not named here is not used”, a misspelling")
        print("     SILENTLY REMOVES a real item from the bot's options. Fix the spelling against")
        print("     `modules/data/items.json` — do not delete the entry to make the gate green.")
        print(bar)
        return 1

    if args.fault == "phantom":
        print("  ⛔ FAULT ARM `phantom` FAILED — an injected non-item was not caught.")
        print(bar)
        return 1

    print("  ✅ PASS — every item name in every scoped policy table resolves.")
    print(bar)
    return 0


if __name__ == "__main__":
    sys.exit(main())
