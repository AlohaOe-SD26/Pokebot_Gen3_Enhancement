"""GATE — a boss cfg may not gain a `"grass"` key while that silently disables its counter-ladder.

‼‼ WHY THIS EXISTS. `03-PUNCH-LIST.md`'s (P6) item asked for "TRAINING-AREA MAPS per gym AND per
boss", citing as its measured hole: *"Winona has no patch configured at all, so the whole
relocation machinery is skipped for her."* **Acting on that sentence would have caused a silent
regression**, and this gate exists so the next agent cannot.

THE MECHANISM (`plugins/custom_modes/story_mode.py`, verified by reading, 2026-08-15):

    grass_is_fodder = ("grass" not in cfg) or (wild_max is not None and wild_max + 8 < team_max)
    ...
    if grass_is_fodder and boss_teaches:
        hopeless, needed = self._boss_plan_is_hopeless(cfg)      # <-- the ONLY call site
        if hopeless:
            acted = yield from self._counter_ladder(cfg, losses, needed)   # <-- ditto

`grass_is_fodder` CONFLATES two different facts — *"this boss has no configured patch"* and
*"the configured patch is far below the team"* — and it is the sole gate on **KI-23's**
hopeless-detector and counter-catch ladder.

⇒ Winona's cfg having NO `"grass"` key is what makes `grass_is_fodder` unconditionally True, which
is the ONLY reason the counter machinery can fire for her. Give her the Route 119 patch the
adjacent comment suggests (band 24-27; `wild_max` is read from the ROM's land table) and for any
team at **L30-35** — i.e. exactly her band (29,33) — `27 + 8 = 35 < team_max` is FALSE, so
`grass_is_fodder` flips to False and the counter ladder is SKIPPED. Control falls through to the
plain `plus5_max/plus5_avg/escalate_band` escalation, which is precisely what KI-23 measured
failing **198 attempts / 41 losses / 41 whiteouts, never converging**, because that path does not
converge when the party has no super-effective answer.

⛔ **AND IT WOULD BE INVISIBLE.** The regression prints a perfectly healthy-looking line
(`"lost here N× — training harder before re-attempting"`). Nothing errors. You would only notice
that the counter-catch message never appears — an ABSENCE, which is exactly the class of failure
this project keeps getting caught by.

WHAT THIS GATE ASSERTS
  1. The coupling still exists (`"grass" not in cfg` appears in `grass_is_fodder`'s formula, and
     `_boss_plan_is_hopeless` is gated behind `grass_is_fodder`).
  2. IF it does, then the named at-risk fights still have NO `"grass"` key.
‼ **It is SELF-RETIRING**: if someone properly decouples the counter-ladder from `grass_is_fodder`,
check 1 goes false, the gate says so and stops enforcing check 2 — because the prohibition only
ever made sense as a consequence of the coupling. A rule that outlives its cause is how stale
"don't do X" lines accumulate (see `/reconcile`'s retirement duty).

⛔ WHAT THIS GATE IS *NOT*. It is not an argument that Winona should never train. It is the
statement that **giving her a patch and keeping her counter-ladder are currently mutually
exclusive**, so the two must be done together, with the KI-23 repro conditions driven — not by
editing a dict. ⛔ **READ KI-80's CONDITION TABLE FOR THOSE CONDITIONS.** An earlier version of
this docstring said "losses>=2 with kos>=1 and no type answer"; that is REFUTED and would build a
VACUOUS test (the ladder cannot fire below losses>=6; at 12+ `hard_plateau` passes it for the
wrong reason; and the fixture must also satisfy `team_max <= wild_max + 8` or both arms take the
same branch). See KI-80.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_boss_grass_gate.py
      PYTHONUTF8=1 py -3.12 repro_boss_grass_gate.py --self-test   # fault-tests the gate itself
Exit: 0 = OK, 1 = a violation (or the gate's own self-test failed).
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]

#: Fights whose counter-ladder depends on having NO `"grass"` key, with the reason.
#: ‼ Keyed on the ASSIGNMENT NAME in `story_mode.py`, not on a position or an index.
AT_RISK: dict[str, str] = {
    "winona_fight": (
        "KI-23 was FILED for Winona: a user's overnight run made 198 attempts, lost 41 times and "
        "whited out 41 times against her with a party far ABOVE her levels but with no "
        "super-effective answer to Flying. Her ace Altaria is Dragon/Flying and 4x weak to Ice; "
        "nothing in Route 119's band (24-27) answers that, so grinding there converges on nothing."
    ),
    "flannery_fight": (
        "Its grass-lessness is DELIBERATE and documented in the code: a probe "
        "(`jaggedgrass_probe.py`) found NO usable training grass reachable from Lavaridge, so the "
        "cfg buys the DETECTION and the ESCALATION without inventing a tile."
    ),
    "rival110_fight": (
        "Marked 'NO `grass` KEY ON PURPOSE' in the code. ROUTE110 is the #1-or-#2 defeat map in "
        "4 of 4 measured batches; the plateau detector and escalation are the whole point here, "
        "and they need only `keys`/`band`/`ace_*`."
    ),
}

STORY_MODE = REPO / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"


def _coupling_present(src: str) -> tuple[bool, list[str]]:
    """Is `_boss_plan_is_hopeless` still gated behind a `grass_is_fodder` that keys off
    `"grass" not in cfg`? Returns (present, evidence_lines).

    ‼ Parsed from the AST, not grepped, so a mention inside a COMMENT or a DOCSTRING cannot
    trigger it. A gate with false positives teaches the reader to bypass it, which is strictly
    worse than no gate.
    """
    tree = ast.parse(src)
    evidence: list[str] = []
    formula_couples = False
    hopeless_gated = False

    for node in ast.walk(tree):
        # (a) the assignment `grass_is_fodder = ("grass" not in cfg) or ...`
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "grass_is_fodder":
                    text = ast.unparse(node.value)
                    if "'grass' not in cfg" in text or '"grass" not in cfg' in text:
                        formula_couples = True
                        evidence.append(f"story_mode.py:{node.lineno}: grass_is_fodder = {text}")

        # (b) an `if grass_is_fodder and ...:` whose body reaches `_boss_plan_is_hopeless`
        if isinstance(node, ast.If):
            test = ast.unparse(node.test)
            if "grass_is_fodder" in test:
                body = "\n".join(ast.unparse(s) for s in node.body)
                if "_boss_plan_is_hopeless" in body:
                    hopeless_gated = True
                    evidence.append(
                        f"story_mode.py:{node.lineno}: `if {test}:` -> body calls "
                        f"_boss_plan_is_hopeless"
                    )
    return (formula_couples and hopeless_gated), evidence


def _fight_keys(src: str) -> dict[str, tuple[int, set[str]]]:
    """{assignment_name: (lineno, {dict keys})} for every `*_fight = {...}` dict.

    ‼ ALSO catches a key added AFTER construction — `winona_fight["grass"] = ...`,
    `.update({...})` and `.setdefault("grass", ...)`. A gate that only read the dict LITERAL would
    pass while the hazard is fully present, and a FALSE NEGATIVE here is far worse than a false
    positive: it would certify the exact edit this gate exists to stop. (`--self-test` cases
    A5/A6/A7 prove each of those three paths fires.)

    ⚠ KNOWN LIMIT, stated rather than hidden: it does NOT understand `dict(**kwargs)`-style
    construction or `{**BASE, "grass": ...}` unpacking. All eight `*_fight` dicts in
    `story_mode.py` are plain literal-key dicts today (checked), so nothing exploits this now —
    but if a future refactor builds them any other way, EXTEND THIS FUNCTION rather than assume
    the gate still covers them. A gate is only as good as its parser.
    """
    out: dict[str, tuple[int, set[str]]] = {}
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.endswith("_fight"):
                    keys = {k.value for k in node.value.keys
                            if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                    out[t.id] = (node.lineno, keys)

    # --- post-construction mutations ---
    for node in ast.walk(tree):
        # `name["grass"] = ...`
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                        and t.value.id in out and isinstance(t.slice, ast.Constant)
                        and isinstance(t.slice.value, str)):
                    lineno, keys = out[t.value.id]
                    out[t.value.id] = (lineno, keys | {t.slice.value})
        # `name.update({...})` / `name.setdefault("grass", ...)`
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            owner = node.func.value
            if isinstance(owner, ast.Name) and owner.id in out:
                lineno, keys = out[owner.id]
                if node.func.attr == "update":
                    for arg in node.args:
                        if isinstance(arg, ast.Dict):
                            keys = keys | {k.value for k in arg.keys
                                           if isinstance(k, ast.Constant)
                                           and isinstance(k.value, str)}
                    keys = keys | {kw.arg for kw in node.keywords if kw.arg}
                elif node.func.attr == "setdefault" and node.args:
                    a0 = node.args[0]
                    if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                        keys = keys | {a0.value}
                out[owner.id] = (lineno, keys)
    return out


def check(src: str) -> list[str]:
    coupled, evidence = _coupling_present(src)
    if not coupled:
        # SELF-RETIRING. The prohibition was only ever a consequence of the coupling.
        print("  NOTE: the counter-ladder is no longer gated on `grass_is_fodder` "
              "(the coupling this gate guards is GONE).")
        print("  => giving a boss a `grass` key no longer disables its counter machinery, so this "
              "gate now enforces nothing.")
        print("  ‼ DO NOT DELETE THIS GATE — ruling 2026-08-16, when the decoupling was promoted.")
        print("     It is inert TODAY, but it is SELF-ARMING: the check above re-derives the")
        print("     coupling from the live AST every run, so if anyone ever re-introduces it (by")
        print("     revert, by merge, or by 'simplifying' the split back into one boolean) this")
        print("     gate starts enforcing again on its own, for free, in 0.1s. Deleting it buys")
        print("     nothing and removes that net. ⇒ a self-retiring gate should be LEFT retired,")
        print("     not removed. (Superseded advice, from this same line: 'RETIRE THIS GATE and")
        print("     KI-80 together'.) The decoupling is recorded in 06-DECISIONS-LOG.md.")
        return []

    print("  coupling CONFIRMED (this is why the rule below applies):")
    for line in evidence:
        print(f"    {line}")

    problems: list[str] = []
    fights = _fight_keys(src)
    for name, why in AT_RISK.items():
        if name not in fights:
            problems.append(
                f"{name}: NOT FOUND in story_mode.py. This gate keys on the assignment name; if the "
                f"fight was renamed, update AT_RISK — do not delete the check."
            )
            continue
        lineno, keys = fights[name]
        has_grass = "grass" in keys
        print(f"    {name} (story_mode.py:{lineno}): grass_key={'PRESENT' if has_grass else 'absent'}")
        if has_grass:
            problems.append(
                f"{name} (story_mode.py:{lineno}) now has a \"grass\" key WHILE the counter-ladder "
                f"is still gated on `grass_is_fodder`. That flips `grass_is_fodder` to False for a "
                f"team above the patch's band + 8, which SKIPS `_boss_plan_is_hopeless` and the "
                f"counter ladder — silently, with a healthy-looking log line. WHY IT MATTERS HERE: "
                f"{why} => Decouple the counter-ladder FIRST and drive the KI-23 repro, then add "
                f"the patch. ⛔ READ KI-80's CONDITION TABLE IN 05-KNOWN-ISSUES.md BEFORE "
                f"BUILDING THAT REPRO — 'losses>=2, kos>=1, no type answer' is the REFUTED early "
                f"wording and a test built to it is VACUOUS: the ladder cannot fire below "
                f"losses>=6, at 12+ hard_plateau passes it for the WRONG reason, and the fixture "
                f"must ALSO satisfy team_max <= wild_max + 8 or grass_is_fodder never flips and "
                f"BOTH arms take the same branch."
            )
    return problems


# --------------------------------------------------------------------------------------------
# ‼ FAULT-TEST THE GATE ITSELF. A gate that has never failed may simply not be looking, and one
#   that fires on a mere mention teaches the reader to bypass it. Both directions are proven here.
# --------------------------------------------------------------------------------------------
_COUPLED_SRC = '''
def _prepare_for_fight(self, cfg):
    grass_is_fodder = ("grass" not in cfg) or (wild_max is not None and wild_max + 8 < team_max)
    if grass_is_fodder and boss_teaches:
        hopeless, needed = self._boss_plan_is_hopeless(cfg)
winona_fight = {"keys": [], "band": (29, 33), "heal": 1}
flannery_fight = {"keys": [], "band": (24, 29), "heal": 1}
rival110_fight = {"keys": [], "band": (18, 20), "heal": 1}
'''

_COUPLED_WITH_GRASS = _COUPLED_SRC.replace(
    'winona_fight = {"keys": [], "band": (29, 33), "heal": 1}',
    'winona_fight = {"keys": [], "band": (29, 33), "grass": (1, (2, 3)), "heal": 1}',
)

_DECOUPLED_WITH_GRASS = _COUPLED_WITH_GRASS.replace(
    'if grass_is_fodder and boss_teaches:', 'if boss_teaches:'
)

#: The false-positive case that matters: the trigger words appear ONLY in a comment/docstring.
_MENTIONS_ONLY = '''
def _prepare_for_fight(self, cfg):
    """Historically `grass_is_fodder = ("grass" not in cfg)` gated _boss_plan_is_hopeless."""
    # grass_is_fodder and _boss_plan_is_hopeless are discussed here but not used.
    return None
winona_fight = {"keys": [], "band": (29, 33), "grass": (1, (2, 3)), "heal": 1}
flannery_fight = {"keys": [], "band": (24, 29), "heal": 1}
rival110_fight = {"keys": [], "band": (18, 20), "heal": 1}
'''


#: ‼ FALSE-NEGATIVE cases. A gate that only reads the dict LITERAL would certify the exact edit
#: it exists to stop, if that edit were made one line later. These three prove it does not.
_SUBSCRIPT_ADD = _COUPLED_SRC + '\nwinona_fight["grass"] = (1, (2, 3))\n'
_UPDATE_ADD = _COUPLED_SRC + '\nwinona_fight.update({"grass": (1, (2, 3))})\n'
_SETDEFAULT_ADD = _COUPLED_SRC + '\nwinona_fight.setdefault("grass", (1, (2, 3)))\n'


def self_test() -> int:
    cases = [
        ("A1 coupled, no grass keys -> quiet", _COUPLED_SRC, False),
        ("A5 grass added AFTER construction (subscript) -> MUST FIRE", _SUBSCRIPT_ADD, True),
        ("A6 grass added via .update() -> MUST FIRE", _UPDATE_ADD, True),
        ("A7 grass added via .setdefault() -> MUST FIRE", _SETDEFAULT_ADD, True),
        ("A2 coupled + winona GAINS grass -> MUST FIRE", _COUPLED_WITH_GRASS, True),
        ("A3 decoupled + winona has grass -> quiet (self-retires)", _DECOUPLED_WITH_GRASS, False),
        ("A4 trigger words in COMMENTS/DOCSTRING only -> quiet (no false positive)",
         _MENTIONS_ONLY, False),
    ]
    bad = 0
    for label, src, must_fire in cases:
        fired = bool(check(src))
        ok = fired == must_fire
        bad += 0 if ok else 1
        print(f"  {'PASS' if ok else 'FAIL'}  {label}"
              f"  (fired={fired}, expected={must_fire})")
    print()
    print(f"SELF-TEST {'PASS' if bad == 0 else 'FAIL'} ({bad} deviation(s))")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true",
                    help="fault-test the gate itself, both directions; no repo read")
    args = ap.parse_args()

    print("=" * 92)
    print("GATE — a boss cfg may not gain a `grass` key while that disables its counter-ladder")
    print("=" * 92)

    if args.self_test:
        return self_test()

    if not STORY_MODE.is_file():
        print(f"  ‼ NOT FOUND: {STORY_MODE}")
        return 1

    problems = check(STORY_MODE.read_text(encoding="utf-8"))
    print("-" * 92)
    if problems:
        for p in problems:
            print(f"  FAIL  {p}")
        print("=" * 92)
        return 1
    print("  OK — no at-risk fight has a `grass` key while the coupling stands.")
    print("=" * 92)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
