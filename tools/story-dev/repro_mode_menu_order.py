"""Proof for the Bot-mode popup ORDERING (`dashboard_gui.build_mode_menu_plan`).

USER REQUEST 2026-07-30: *"I want all of them to be at the top of the list including the
'Park' and end options for the x4 runs so its easier to find them (currently I have to
scroll around to activate them and end/park them)."*

Before: `Manual` -> ~23 upstream modes -> a block of greyed-out modes -> Debug Logging ->
Endless Debug-Reset -> Endless Loop x4 -> Park x4. The two controls used most often while
a batch is running — park it, stop it — were the LAST TWO ENTRIES in the menu.

This is a pure-function test on purpose. The ordering used to live inside `_open_mode_menu`,
a Tk callback, where the only way to observe it was to open a window and look; extracting
`build_mode_menu_plan` means the ORDER is now testable and cannot silently drift back.

WHAT THIS PROVES (no Tk, no emulator, no window):
  1. Manual is first, and is ENABLED even though it is not a registered bot mode (it is
     absent from the registry, so the plain selectability test would have greyed out the
     one entry that must always work).
  2. Every `Story*` mode appears ABOVE every non-Story mode.
  3. The x4 controls — Endless Debug-Reset, Endless Loop x4, Park x4 — sit in the Story
     block, above the other modes. This is the whole request.
  4. ‼ A Story mode that is NOT selectable right now STAYS in the Story block, greyed out,
     instead of dropping into the disabled block at the bottom. An entry that MOVES with
     game state is the scrolling problem wearing a different hat.
  5. ‼ `Park x4` is ALWAYS present — greyed out when no batch runs — so the block's height
     never changes and nothing below it shifts. (This reverses a deliberate 2026-07-26
     choice to hide it unless meaningful; hiding it is what made the layout move.)
  6. Park is ENABLED exactly when a batch is running, and the x4 toggle says "Stop" then.
  7. The active mode is emitted once, unclickable, whether it is a Story mode or not.
  8. No entry is ever duplicated, and every referenced action key exists.
  9. Story modes are discovered by PREFIX, so a brand-new `Story (…)` mode is hoisted the
     day it is added — no hand-written list to rot (08-MISTAKES 2026-07-30).

Run: py -3.12 tools/story-dev/repro_mode_menu_order.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.gui.dashboard_gui import (
    ACTION_DEBUG_LOG,
    ACTION_ENDLESS_RESET,
    ACTION_X4_PARK,
    ACTION_X4_TOGGLE,
    build_mode_menu_plan,
)

failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  {'PASS' if condition else 'FAIL'}  {label}{(' — ' + detail) if detail else ''}")
    if not condition:
        failures.append(label)


# A realistic registry: the four Story modes among a sample of upstream ones, in the order
# `get_bot_modes()` would hand them over (Story is NOT first — that is the point).
MODES = [
    "Spin", "Bunny Hop", "Fishing", "Story", "Sweet Scent", "Roamer Reset",
    "Story (DEBUG)", "Starters", "Story (DEBUG - RESET)", "Daycare",
    "Story (ENDLESS RESET)", "Game Corner", "Hunt (Custom)",
]
STORY = [m for m in MODES if m.startswith("Story")]


def plan_for(**kwargs):
    params = dict(current_mode="Manual", selectable=set(MODES), x4_running=False)
    params.update(kwargs)
    return build_mode_menu_plan(MODES, **params)


def labels(plan):
    """Every visible label, in order."""
    out = []
    for entry in plan:
        if entry[0] == "separator":
            continue
        out.append(entry[1])
    return out


def index_of(plan, label):
    return labels(plan).index(label)


def entry_for(plan, label):
    for entry in plan:
        if entry[0] != "separator" and entry[1] == label:
            return entry
    return None


print("=" * 78)
print("CASE 1 — Manual first and always enabled; Story block above everything else")
print("=" * 78)
plan = plan_for()
print("  order:", " | ".join(labels(plan)))
check("1. Manual is the first entry", labels(plan)[0] == "Manual", labels(plan)[0])
# ‼ Check enabled-ness from a plan where Manual is NOT the current mode. With
# current_mode="Manual" it is correctly emitted as the bold, unclickable ("active", …)
# entry, so that plan cannot answer "would Manual be clickable when you need it?".
away = plan_for(current_mode="Spin")
manual = entry_for(away, "Manual")
check("   ...and when NOT current it is ENABLED (it is absent from the registry, "
      "so the plain selectability test would grey out the one entry that must always work)",
      manual[0] == "mode" and manual[3] is True, str(manual))
check("   ...and when it IS current it is the bold, unclickable entry",
      entry_for(plan, "Manual")[0] == "active", str(entry_for(plan, "Manual")))

story_positions = [index_of(plan, m) for m in STORY]
other_positions = [index_of(plan, m) for m in MODES if not m.startswith("Story")]
check("2. every Story mode is above every non-Story mode",
      max(story_positions) < min(other_positions),
      f"story max {max(story_positions)} < others min {min(other_positions)}")

print()
print("=" * 78)
print("CASE 2 — the actual request: the x4 controls are at the top")
print("=" * 78)
for label in ("Endless Debug-Reset Runs…", "Endless Loop ×4…", "Park ×4 & Collect Logs…"):
    check(f"3. '{label}' sits above the other modes",
          index_of(plan, label) < min(other_positions),
          f"at {index_of(plan, label)}, others start at {min(other_positions)}")

print()
print("=" * 78)
print("CASE 3 — the block never MOVES, whatever the game state")
print("=" * 78)
# Only `Story` itself selectable (the title-screen case: other modes need an overworld).
partial = plan_for(selectable={"Story"})
print("  order:", " | ".join(labels(partial)))
for mode in STORY:
    check(f"4. '{mode}' stays in the Story block even when not selectable",
          index_of(partial, mode) < min(index_of(partial, m) for m in MODES
                                        if not m.startswith("Story")),
          f"at {index_of(partial, mode)}")
greyed = entry_for(partial, "Story (DEBUG)")
check("   ...and it renders greyed out rather than clickable",
      greyed[0] == "mode" and greyed[3] is False, str(greyed))

park_idle = entry_for(plan, "Park ×4 & Collect Logs…")
check("5. Park ×4 is PRESENT with no batch running (layout stays put)", park_idle is not None)
check("   ...but DISABLED", park_idle is not None and park_idle[3] is False, str(park_idle))

print()
print("=" * 78)
print("CASE 4 — during a batch: Park enabled, toggle reads 'Stop'")
print("=" * 78)
running = plan_for(x4_running=True)
park_running = entry_for(running, "Park ×4 & Collect Logs…")
check("6. Park ×4 is ENABLED while a batch runs",
      park_running is not None and park_running[3] is True, str(park_running))
check("   ...and the toggle reads 'Stop Endless Loop ×4'",
      entry_for(running, "Stop Endless Loop ×4") is not None,
      " | ".join(labels(running)[:8]))
check("   ...and 'Endless Loop ×4…' is no longer offered",
      entry_for(running, "Endless Loop ×4…") is None)

print()
print("=" * 78)
print("CASE 5 — the active mode, duplicates, and action keys")
print("=" * 78)
for current in ("Story (ENDLESS RESET)", "Spin", "Manual"):
    active_plan = plan_for(current_mode=current)
    actives = [e for e in active_plan if e[0] == "active"]
    check(f"7. current mode '{current}' is emitted once and unclickable",
          len(actives) == 1 and actives[0][1] == current, str(actives))
    seen = labels(active_plan)
    check(f"8. no duplicate entries with '{current}' active",
          len(seen) == len(set(seen)),
          f"{len(seen)} entries, {len(set(seen))} unique")

keys = {e[2] for e in plan if e[0] == "command"} | {e[2] for e in plan if e[0] == "checkbutton"}
check("   every action key is one the renderer knows",
      keys <= {ACTION_ENDLESS_RESET, ACTION_X4_TOGGLE, ACTION_X4_PARK, ACTION_DEBUG_LOG},
      str(keys))

print()
print("=" * 78)
print("CASE 6 — a NEW Story mode is hoisted automatically (prefix, not a hand-list)")
print("=" * 78)
future = MODES + ["Story (SOME FUTURE VARIANT)"]
future_plan = build_mode_menu_plan(
    future, current_mode="Manual", selectable=set(future), x4_running=False
)
future_labels = labels(future_plan)
check("9. an unforeseen Story mode lands in the Story block with no code change",
      future_labels.index("Story (SOME FUTURE VARIANT)")
      < min(future_labels.index(m) for m in future if not m.startswith("Story")),
      f"at {future_labels.index('Story (SOME FUTURE VARIANT)')}")

print()
print("=" * 78)
print(f"RESULT: {'ALL PASS' if not failures else str(len(failures)) + ' FAILURE(S)'}")
for f in failures:
    print(f"  FAILED: {f}")
print("=" * 78)
sys.exit(1 if failures else 0)
