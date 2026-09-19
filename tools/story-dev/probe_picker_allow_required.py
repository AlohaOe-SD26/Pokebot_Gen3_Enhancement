# -*- coding: utf-8 -*-
"""⛔ GATE: NO PRODUCTION CALLER MAY ASK A TRAINING PICKER WITHOUT A REACHABILITY PREDICATE.

THE HAZARD THIS EXISTS TO MAKE IMPOSSIBLE. `training_areas.py` has two pickers that behave
DIFFERENTLY at `allow=None`, and the difference is deliberate:
  * `best_training_area` treats `allow=None` as *"refuse every area that HAS a prereq"* — the
    conservative default.
  * `best_training_grass` keeps its historical behaviour — **no filtering at all** — because it is
    also injected as `decide_maintenance`'s `ground_for`, and narrowing it would change that pure
    decision's answers. ✅ MEASURED 2026-09-19: narrowing it changes **83 of 99 levels** and makes
    every one of them WORSE. **Do not "fix" that asymmetry; it is load-bearing.**

⇒ ON 2026-09-19 `VICTORY_ROAD_1F` was promoted into `TRAINING_GRASS` with an `AREA_PREREQ` row. The
prereq keeps `best_training_area(allow=None)` conservative — MEASURED, it answers Victory Road at
**zero** levels. But `best_training_grass(allow=None)` now answers **VICTORY_ROAD_1F from L35 up**,
because that function does not consult `AREA_PREREQ` at all.

⭐ THAT IS HARMLESS **ONLY** BECAUSE NO PRODUCTION CALLER USES THAT SHAPE. All four pass a real
predicate today. **This gate is what keeps that true**, and it is the third guard the promotion
needed — a STRUCTURAL one. ⛔ The obvious behavioural alternative,
`assert best_training_grass(40) is not VICTORY_ROAD_1F`, is **self-refuting**: it is false the day
the row lands. A guard that cannot be satisfied is not a guard.

⚠ THIS GATE HAS NO PRE-EXISTING DEFECT TO CATCH — it passes on the tree it was written against, and
that is the point: it is a RATCHET, not a repair. ⇒ **its FAULT ARM is the only proof it works**,
which is why the arm is not optional here.

WHY AST AND NOT GREP: a regex would fire on `best_training_grass` inside a comment, a docstring, or
this very file's prose. The project's own rule is that a gate with false positives teaches the
reader to bypass it. This walks the syntax tree and only ever inspects real call nodes.

FAULT ARM: `POKEBOT_PICKER_FAULT_INJECT=1` appends a synthetic offending call to the scan and the
gate must FAIL naming it.
"""
import ast
import os
import pathlib as _pl
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001 - a console that cannot be reconfigured is not a reason to abort
    pass

ROOT = _pl.Path(r"C:\Remote Projects\Pokebot_Gen3_Enhancement") / "sandbox-pokebot"
#: PRODUCTION only. `tools/story-dev` probes legitimately call the pickers bare to MEASURE them —
#: that is how the asymmetry above was established, and forbidding it would forbid the evidence.
SCAN = [ROOT / "modules", ROOT / "plugins"]
PICKERS = {"best_training_area", "best_training_grass"}

#: ⛔⛔ WHAT THIS GATE CAN AND CANNOT SEE — STATED HONESTLY, BECAUSE A TIER 1 REVIEW BROKE
#: VERSION 1'S CLAIM. It walks call nodes and resolves the callee by NAME, so it catches
#: `best_training_grass(...)`, `ta.best_training_grass(...)`, and — added after that review —
#: calls through an `import ... as` ALIAS. ⚠ It still cannot follow a call built at RUNTIME:
#: `functools.partial`, a dict of dispatch functions, `getattr(mod, name)`. Those are invisible
#: to any purely syntactic check, and pretending otherwise is how a gate earns distrust.
#: ⇒ **THE HONEST GUARANTEE: no production caller reaches a picker by a NAME THIS FILE CAN
#: RESOLVE without passing an `allow` predicate.** That is a ratchet against the accident that
#: actually happens — someone copies a call and drops the kwarg — not a proof of impossibility.
#: ✅ PROVEN NECESSARY: a reviewer dropped an aliased import AND a dict dispatch into the tree
#: and v1 passed clean over 207 files. The alias half is now caught; the runtime half is
#: documented rather than hidden.

print("=" * 100)
print("GATE: every production call to a training picker must pass an `allow` predicate")
print("=" * 100)


def _alias_names(tree):
    """Local names bound to a picker by `from ... import best_training_grass as g`.

    ‼ ADDED after a Tier 1 review proved v1 blind to exactly this shape: an aliased import
    plus a bare call passed the gate clean while being a real, unguarded caller.
    """
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name in PICKERS and a.asname:
                    out.add(a.asname)
    return out


def _callee(node):
    """The called name, whether `f(...)` or `mod.f(...)`. None for runtime-built calls."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


offenders = []
scanned = 0
for base in SCAN:
    for path in sorted(base.rglob("*.py")):
        scanned += 1
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as error:  # noqa: PERF203 - a file we cannot parse is a finding
            offenders.append((path, 0, f"could not parse: {error}"))
            continue
        aliases = _alias_names(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _callee(node)
            if name not in PICKERS and name not in aliases:
                continue
            kw = {k.arg for k in node.keywords if k.arg}
            if "allow" not in kw:
                # ‼ `**kwargs` forwarding could supply it; do not accuse a caller we cannot read.
                if any(k.arg is None for k in node.keywords):
                    continue
                _via = "" if name in PICKERS else f" [via alias of a picker]"
                offenders.append((path, node.lineno,
                                  f"{name}(...) with NO `allow=` argument{_via}"))
                continue
            for k in node.keywords:
                if k.arg == "allow" and isinstance(k.value, ast.Constant) and k.value.value is None:
                    offenders.append((path, node.lineno, f"{name}(..., allow=None)"))

if os.environ.get("POKEBOT_PICKER_FAULT_INJECT", "").strip() in ("1", "true", "yes"):
    offenders.append((ROOT / "modules" / "story" / "<synthetic>.py", 1,
                      "best_training_grass(40, allow=None)  [FAULT ARM — injected, not real]"))
    print("  ⚠ FAULT ARM ACTIVE: a synthetic offending call was injected")

print(f"  scanned {scanned} production file(s) under modules/ and plugins/")
print()

if offenders:
    print("⛔ FAIL — a production caller can receive an area the conservative default would refuse:")
    for path, line, what in offenders:
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            rel = path
        print(f"  • {rel}:{line}  {what}")
    print()
    print("  WHY THIS IS A DEFECT: `best_training_grass` does NO prereq filtering at `allow=None`,")
    print("  so such a caller can be handed VICTORY_ROAD_1F (L36-40 wilds) for ANY trainee from L35")
    print("  up, at any story point — including long before Badge 8 makes it reachable.")
    print("  THE FIX IS THE CALLER, NOT THE PICKER: pass a real reachability predicate")
    print("  (`_training_area_allowed` / `_counter_area_allowed` / `_maint_allow`).")
    print()
    print("  ‼ AND WHAT THIS GATE DOES NOT COVER: calls built at runtime (functools.partial, a")
    print("    dict of dispatch functions, getattr) are invisible to a syntactic check. Fixing a")
    print("    finding here does not make the property universally true — see the scope note.")
    print("=" * 100)
    raise SystemExit(1)

print(f"  ✅ PASS — every production call to {sorted(PICKERS)} passes an `allow` predicate.")
print("=" * 100)
