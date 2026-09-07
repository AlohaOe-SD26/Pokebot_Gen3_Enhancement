# -*- coding: utf-8 -*-
"""probe_hm_coverage.py — ANYTHING THE STORY REQUIRES SOMEONE TO KNOW MUST HAVE A STEP THAT TEACHES IT.

USAGE
    py -3.12 probe_hm_coverage.py                     # bare -> --self-test (gate mode)
    py -3.12 probe_hm_coverage.py --self-test
    py -3.12 probe_hm_coverage.py --build sandbox|custom     # audit a real tree

⛔⛔ WHY THIS EXISTS — THE MOST EXPENSIVE GAP IN THE PROJECT'S HISTORY, AND IT WAS STRUCTURAL.
§Ch23 asserted a **Waterfall** carrier in its preflight. §Ch21 put HM07 in the bag. **Nothing in
production ever taught it.** Across 37 stored batches the 8th badge was reached six times and ALL SIX
died on that assertion; nothing ever passed it.

‼ AND IT WAS INVISIBLE TO EVERY EXISTING CHECK, for a reason worth stating: §Ch23 was built, driven
and green — from FIXTURES that were captured downstream of a HARNESS DRIVER (`Ch23TeachMode`) which
did the teach. The chapter passed its own tests for days while the route that reaches it was
impassable. ⇒ **a fixture encodes everything the step before it did, including steps that exist only
in the harness.** No behavioural test can see that; only a structural one can.

THE INVARIANT, and it is deliberately narrow so it stays believed:
    { field moves the story ASSERTS a carrier for }  ⊆  { field moves the story TEACHES }
A move on the left with nothing on the right is a wall the bot cannot pass, by construction.

⛔ WHAT THIS DOES **NOT** CHECK, said out loud so nobody mistakes green for safe:
  * that the teach SUCCEEDS (a party may have no compatible mon with a free slot — that is
    `#24-hm07funnel`, a POLICY problem this gate cannot see);
  * that the teach happens BEFORE the requirement (ordering is a ladder question);
  * that the move is still known later (nothing removes HMs in Gen 3, so this is safe today).
  It checks EXISTENCE only. Existence was the bug.
"""
import argparse
import ast
import pathlib
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
BAR = "=" * 96

#: HM number -> the field-move name the story asserts by.
HM_MOVES = {
    "HM01": "Cut", "HM02": "Fly", "HM03": "Surf", "HM04": "Strength",
    "HM05": "Flash", "HM06": "Rock Smash", "HM07": "Waterfall", "HM08": "Dive",
}
MOVE_NAMES = set(HM_MOVES.values())
SCAN = ("modules/story", "plugins/custom_modes")

#: ⭐ FUNCTION SCOPE, NOT A LINE WINDOW. A first version used regexes with a 40-line lookback and
#: produced a FALSE NEGATIVE on the very bug this gate exists to catch: the real §Ch23 preflight
#: expresses its requirement as a LOOP over a tuple —
#:     missing = [m for m in ("Surf", "Dive", "Waterfall") if carriers[m] is None]
#: — which no subscript pattern matches, and a real teach sat 67 lines below the "HM07" literal that
#: names it. ⇒ the governing structure is the FUNCTION: a teach and the item it teaches live in one.
#: AST also makes comments structurally invisible, which is stricter than filtering them by hand.
REQUIRE_MARKERS = ("field_move_carriers", "_party_knows_")
TEACH_CALL = "teach_hm_move"


def _strings_in(node) -> list[str]:
    return [n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _calls_in(node) -> set[str]:
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            name = getattr(f, "id", None) or getattr(f, "attr", None)
            if name:
                out.add(name)
    return out


def audit(root: pathlib.Path) -> tuple[dict, dict, list]:
    """(required{move: [sites]}, taught{move: [sites]}, files_scanned) — by FUNCTION, via AST."""
    required: dict[str, list[str]] = {}
    taught: dict[str, list[str]] = {}
    files = []
    for sub in SCAN:
        base = root / sub
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*.py")):
            files.append(f)
            try:
                tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
            except (OSError, SyntaxError):
                continue
            rel = f.relative_to(root).as_posix()
            for fn in [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
                src = ast.dump(fn)
                site = f"{rel}:{fn.lineno} ({fn.name})"
                strings = _strings_in(fn)
                # REQUIREMENT: this function consults carriers / _party_knows_*, and names moves.
                if any(m in src for m in REQUIRE_MARKERS):
                    for s in strings:
                        if s in MOVE_NAMES:
                            required.setdefault(s, []).append(site)
                    for n in ast.walk(fn):
                        if isinstance(n, ast.Call):
                            nm = getattr(n.func, "id", "") or getattr(n.func, "attr", "")
                            if nm.startswith("_party_knows_"):
                                mv = " ".join(w.capitalize()
                                              for w in nm[len("_party_knows_"):].split("_") if w)
                                if mv in MOVE_NAMES:
                                    required.setdefault(mv, []).append(site)
                # TEACH: this function calls teach_hm_move, and names an HM.
                if TEACH_CALL in _calls_in(fn):
                    hms = [HM_MOVES[s] for s in strings if s in HM_MOVES]
                    if hms:
                        for mv in set(hms):
                            taught.setdefault(mv, []).append(site)
                    else:
                        taught.setdefault("<unresolved>", []).append(site)
    # dedupe, keep order
    for d in (required, taught):
        for k, v in d.items():
            seen, out = set(), []
            for s in v:
                if s not in seen:
                    seen.add(s)
                    out.append(s)
            d[k] = out
    return required, taught, files


def report(root: pathlib.Path, label: str) -> int:
    required, taught, files = audit(root)
    print(BAR)
    print(f"HM COVERAGE — every field move the story REQUIRES must have a step that TEACHES it")
    print(f"BUILD UNDER TEST: {label}  ({len(files)} file(s) scanned under {', '.join(SCAN)})")
    print(BAR)
    if not required:
        # ⛔ NOT A PASS. Finding no requirements means the patterns stopped matching, which is a
        # broken instrument, not a healthy tree. Silence here is exactly how HM07 survived.
        print("  ⛔ NO REQUIREMENTS FOUND AT ALL — the scan patterns no longer match this tree.")
        print("     That is an INSTRUMENT failure, not a clean bill of health. Fix the patterns.")
        return 1
    missing = {}
    for mv, sites in sorted(required.items()):
        have = taught.get(mv, [])
        mark = "OK  " if have else "MISS"
        print(f"  {mark} {mv:<11} required at {len(sites)} site(s)  ->  taught at {len(have)}")
        if have:
            print(f"         teach: {', '.join(have[:3])}")
        else:
            missing[mv] = sites
            for s in sites[:4]:
                print(f"         ⛔ required: {s}")
    unresolved = taught.get("<unresolved>", [])
    if unresolved:
        print(f"\n  ⚠ {len(unresolved)} teach call(s) whose HM could not be resolved: "
              f"{', '.join(unresolved[:3])}")
        print("     Not a failure by itself — but a teach nobody can attribute cannot satisfy the")
        print("     invariant either. Name the HM near the call.")
    print("\n" + "-" * 96)
    if missing:
        print(f"FAILED — {len(missing)} field move(s) REQUIRED but never TAUGHT: "
              f"{', '.join(sorted(missing))}")
        print("  ⇒ This is a WALL the bot cannot pass. It is what ended every 8-badge run in the")
        print("    project's history (HM07 Waterfall, found 2026-09-07 after 37 batches).")
        print(BAR)
        return 1
    print(f"PASS — all {len(required)} required field move(s) have a teach site.")
    print(BAR)
    return 0


# ---------------------------------------------------------------------------------------------
# --self-test — synthetic trees, so this is gate-able on a fresh clone
# ---------------------------------------------------------------------------------------------
def _tree(tmp: pathlib.Path, story: str, plugin: str = "") -> pathlib.Path:
    root = tmp / "t"
    (root / "modules" / "story").mkdir(parents=True, exist_ok=True)
    (root / "plugins" / "custom_modes").mkdir(parents=True, exist_ok=True)
    (root / "modules" / "story" / "s.py").write_text(story, encoding="utf-8")
    (root / "plugins" / "custom_modes" / "p.py").write_text(plugin, encoding="utf-8")
    return root


GOOD = '''
def pre():
    if field_move_carriers()["Waterfall"] is None:
        raise BotModeError("need it")

def teach():
    hm07 = get_item_by_name("HM07")
    yield from teach_hm_move(hm07, 0)
'''

MISSING = '''
def pre():
    if field_move_carriers()["Waterfall"] is None:
        raise BotModeError("need it")
'''

COMMENT_ONLY = '''
def pre():
    # field_move_carriers()["Waterfall"] is checked elsewhere; teach_hm_move("HM07") is not here
    return True
'''

TWO_REQ = '''
def pre():
    if field_move_carriers()["Waterfall"] is None or not _party_knows_surf():
        raise BotModeError("need both")

def teach():
    hm07 = get_item_by_name("HM07")
    yield from teach_hm_move(hm07, 0)
'''


def _self_test() -> int:
    cases = [
        ("required AND taught -> PASS", GOOD, "", 0),
        ("⛔ required, NEVER taught (the HM07 bug) -> FAIL", MISSING, "", 1),
        ("‼ mentions in COMMENTS only -> no requirement, no wolf", COMMENT_ONLY, "", 1),
        ("⛔ two required, one taught -> FAIL on the uncovered one", TWO_REQ, "", 1),
    ]
    print(BAR)
    print("probe_hm_coverage.py --self-test — four synthetic trees")
    print(BAR)
    failures = 0
    with tempfile.TemporaryDirectory() as td:
        for label, story, plugin, want in cases:
            root = _tree(pathlib.Path(td) / label.replace(" ", "_")[:20], story, plugin)
            rc = subprocess.run(
                [sys.executable, str(pathlib.Path(__file__).resolve()), "--root", str(root)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            ok = rc.returncode == want
            failures += 0 if ok else 1
            print(f"  {'PASS' if ok else 'RED '}  exit={rc.returncode} (want {want})  {label}")
            if not ok:
                print("\n".join("        " + l for l in rc.stdout.strip().splitlines()[-8:]))
    print("-" * 96)
    print("SELF-TEST: " + ("PASS" if not failures else f"FAIL ({failures} case(s))"))
    return 1 if failures else 0


ap = argparse.ArgumentParser(add_help=True)
ap.add_argument("--build", default=None, choices=["sandbox", "custom"])
ap.add_argument("--root", default=None, help="audit an arbitrary tree (used by --self-test)")
ap.add_argument("--self-test", action="store_true")
args, _ = ap.parse_known_args()

# ⛔ A GATE MUST RUN WITH NO ARGUMENTS — `run_gates.py` invokes each entry bare.
if args.root:
    raise SystemExit(report(pathlib.Path(args.root), args.root))
if args.build:
    raise SystemExit(report(REPO / f"{args.build}-pokebot", f"{args.build}-pokebot"))
if args.self_test:
    raise SystemExit(_self_test())

# ⛔⛔ BARE = SELF-TEST **AND** AUDIT THE REAL TREE. A gate whose default mode only runs synthetic
# arms proves the CHECKER works and NOTHING about the code — and bare is the mode `run_gates.py`
# uses, so it is the only mode that actually guards anything.
# ‼ SANDBOX, not custom: custom fails today for a KNOWN, correct reason (the fix is unpromoted, and
# drift is expected while a batch runs). A gate that is red for a good reason teaches the reader to
# ignore it, which this project rates worse than no gate. Audit custom explicitly with --build custom
# when verifying a promotion.
_rc = _self_test()
print()
_rc |= report(REPO / "sandbox-pokebot", "sandbox-pokebot")
raise SystemExit(_rc)
