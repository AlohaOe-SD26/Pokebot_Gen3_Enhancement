"""KI-56 regression guard: §Ch15 must still be able to LEAVE the Magma Hideout.

‼ WHY THIS EXISTS. Ch15 was graded BINARY on `GROUDON_AWAKENED_MAGMA_HIDEOUT`, which the game
sets the instant Maxie falls, four floors underground. The chapter therefore **passed its own
acceptance test on runs that ended permanently stranded** (KI-56): 1F's entrance pocket is joined
to the rest of the floor only by two Strength pushes, and boulder positions reset on map reload,
so the bot comes back down on the wrong side of a wall it can no longer re-open. A BFS over the
whole eight-map warp graph reaches 18 of 20 nodes from that tile and misses only the exit warp and
Jagged Pass — there is no walk-out at all.

The fix is the Escape Rope the dungeon itself provides. These checks pin the parts of it that are
**silent** when broken — a dropped exit call still sets the flag, and a "corrected" flag name still
compiles, runs, and reads False forever.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_hideout_exit.py
Exit: 0 = all checks pass; 1 = at least one failed.

‼ No emulator, no ROM: this is a STRUCTURAL guard, so it is cheap enough to run every time. It
proves the wiring and the constants, NOT that the escape works — that is `--driver magmaexit`.
"""

import ast
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
EARLY_GAME = REPO / "sandbox-pokebot" / "modules" / "story" / "early_game.py"
FLAG_TABLE = REPO / "sandbox-pokebot" / "modules" / "data" / "event_flags" / "emerald.txt"
HARNESS = pathlib.Path(__file__).resolve().parent / "story_harness.py"

FAILURES: list[str] = []


def check(what: str, passed: bool, why: str = "") -> None:
    print(f"  {'OK  ' if passed else 'FAIL'}  {what}")
    if why:
        print(f"          {why}")
    if not passed:
        FAILURES.append(what)


source = EARLY_GAME.read_text(encoding="utf-8")
tree = ast.parse(source)

#: module-level constants we can evaluate without importing (importing needs a ROM + emulator)
consts: dict[str, object] = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        try:
            consts[node.targets[0].id] = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            pass

functions = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}

print(__doc__.strip().splitlines()[0])
print()

# ---------------------------------------------------------------- 1. the wiring
print("1. THE EXIT IS WIRED INTO THE CHAPTER")
chapter = functions.get("do_magma_hideout_chapter")
check("`do_magma_hideout_chapter` exists", chapter is not None)

if chapter is not None:
    # ‼ IT MUST BE THE LAST TOP-LEVEL STATEMENT, NOT MERELY PRESENT. The whole bug was a chapter
    # that returned successfully while still underground; if the exit sits inside the
    # `if not _groudon_awakened():` block, a run RESUMED after the flag was set skips it and is
    # stranded exactly as before — and nothing about that is visible in a grep for the name.
    last = chapter.body[-1]
    is_exit_call = (
        isinstance(last, ast.Expr)
        and isinstance(last.value, ast.YieldFrom)
        and isinstance(last.value.value, ast.Call)
        and isinstance(last.value.value.func, ast.Name)
        and last.value.value.func.id == "leave_magma_hideout"
    )
    check(
        "the chapter ENDS with `yield from leave_magma_hideout()`, at top level",
        is_exit_call,
        "if this is nested inside the flag guard, a resumed run stays stranded (KI-56)",
    )

    early_returns = [n for n in chapter.body if isinstance(n, ast.Return)]
    check(
        "the chapter has no top-level early `return` that could skip the exit",
        not early_returns,
        "`if _groudon_awakened(): return` is exactly the shape that stranded the bot",
    )

for name in ("leave_magma_hideout", "collect_hideout_escape_rope", "use_escape_rope_to_leave_hideout"):
    check(f"`{name}` is defined", name in functions)

# ---------------------------------------------------------------- 2. the misspelled flag
print("\n2. ‼ THE MISSPELLED FLAG — the highest-value check here")
MISSPELLED = "ITEM_MAGMA_HIDEOUT_3F_3R_ECAPE_ROPE"
CORRECTED = "ITEM_MAGMA_HIDEOUT_3F_3R_ESCAPE_ROPE"
table = FLAG_TABLE.read_text(encoding="utf-8")
table_names = {parts[1] for line in table.splitlines() if len(parts := line.split()) >= 2}

check(
    f"the code uses the decomp's spelling `{MISSPELLED}`",
    consts.get("HIDEOUT_ESCAPE_ROPE_FLAG") == MISSPELLED,
    "the decomp misspells ESCAPE as ECAPE and our flag table carries the typo through",
)
check(f"`{MISSPELLED}` resolves in the flag table", MISSPELLED in table_names)
check(
    f"the 'corrected' spelling `{CORRECTED}` does NOT exist",
    CORRECTED not in table_names,
    "‼ an unknown flag name reads False SILENTLY — spelled 'right', this check becomes a "
    "permanent lie meaning 'the item ball is still there', and the bot re-walks to an empty tile",
)

# ---------------------------------------------------------------- 3. the measured constants
print("\n3. THE CONSTANTS MATCH WHAT WAS MEASURED (probe_hideout_warp_graph.py)")
check(
    "the approach tile is (9,20) — the ONLY reachable neighbour of the item ball",
    consts.get("HIDEOUT_ESCAPE_ROPE_APPROACH") == (9, 20),
    "(9,18), (8,19) and (10,19) are all unreachable from both of 3F_3R's warp arrival tiles",
)
check("the facing is Up", consts.get("HIDEOUT_ESCAPE_ROPE_FACING") == "Up")
check("the item ball tile is (9,19)", consts.get("HIDEOUT_ESCAPE_ROPE_TILE") == (9, 19))
check(
    "the 4F -> 3F_3R detour warp is (20,21)",
    consts.get("HIDEOUT_4F_TO_3F_3R") == (20, 21),
    "the inbound route (1F (25,34) -> 2F_1R -> 3F_1R -> 4F) never touches 3F_3R, so the rope "
    "is a deliberate one-warp detour off 4F",
)

# ---------------------------------------------------------------- 4. graded on the bag
print("\n4. THE PICKUP IS GRADED ON THE BAG, NOT ON THE FLAG")
collect = functions.get("collect_hideout_escape_rope")
collect_src = ast.get_source_segment(source, collect) if collect else ""

# ‼ THE PICKUP LOGIC MOVED (2026-08-12, `#24-grounditems`). It used to be inlined here; it now
# lives in the shared `collect_item_ball`, which the Master Ball also uses. These checks follow it
# — and the delegation check below is what stops a future edit quietly forking a second copy,
# which is the whole reason the helper exists.
generic = functions.get("collect_item_ball")
generic_src = ast.get_source_segment(source, generic) if generic else ""
check("the shared `collect_item_ball` helper exists", generic is not None)
check(
    "`collect_hideout_escape_rope` DELEGATES to it rather than keeping its own copy",
    "collect_item_ball(" in (collect_src or ""),
)
check(
    "the A-press loop is graded on a BAG DELTA, not on the flag",
    "_held_quantity(item_name) > before" in (generic_src or ""),
    "with a FULL items pocket `finditem` sets no flag and gives no item — a flag-based test "
    "would hang forever on a ball that can never be collected",
)
check(
    "a set flag with no bag change is reported as the full-pocket case",
    "FULL" in (generic_src or ""),
)
check(
    "an unknown flag name is refused rather than read as 'still there'",
    "_event_flags" in (generic_src or ""),
)

# ---------------------------------------------------------------- 5. bounded loops
print("\n5. EVERY LOOP IS BOUNDED (never hang — standing project rule)")
for name in ("collect_item_ball", "use_escape_rope_to_leave_hideout"):
    fn = functions.get(name)
    if fn is None:
        continue
    unbounded = [
        n for n in ast.walk(fn)
        if isinstance(n, ast.While) and isinstance(n.test, ast.Constant) and n.test.value is True
    ]
    check(f"`{name}` has no `while True`", not unbounded)
    ranges = [
        n for n in ast.walk(fn)
        if isinstance(n, ast.For) and isinstance(n.iter, ast.Call)
        and isinstance(n.iter.func, ast.Name) and n.iter.func.id == "range"
    ]
    check(f"`{name}` bounds its wait with a `range(...)`", bool(ranges))

# ---------------------------------------------------------------- 6. the driver
print("\n6. THE DRIVEN TEST STILL EXISTS")
harness = HARNESS.read_text(encoding="utf-8-sig")
check("the `magmaexit` driver is registered", '"magmaexit"' in harness and "MagmaExitMode" in harness)
check(
    "its acceptance is BOTH halves, not just 'not in the hideout'",
    "landed_on_jagged_pass" in harness,
    "a WHITEOUT also leaves the dungeon — two towns away, having lost money. The landing map "
    "is the only thing that separates an escape from a derail",
)

print()
if FAILURES:
    print(f"FAILED {len(FAILURES)} check(s):")
    for failure in FAILURES:
        print(f"  - {failure}")
    sys.exit(1)
print("ALL PASS")
