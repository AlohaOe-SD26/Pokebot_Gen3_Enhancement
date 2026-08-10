"""`#24-battleitems`: does the healing-item policy do the intelligent thing? NO EMULATOR.

The policy is pure (`modules/story/battle_items.py`), so every rule can be tested exhaustively in
milliseconds instead of inside a 3-hour batch. Each case below names the RULE it defends and the
failure it would represent, because a test whose intent is not written down gets "fixed" by
someone deleting it.

‼ POSITIVE CONTROL FIRST: a plainly-should-heal case must return an item. If that fails, every
"policy correctly declines" case below is passing for the wrong reason — a function that always
returns None satisfies half this suite.

‼ AND ONE REAL-DATA CHECK: the heal amounts are read from `modules/data/items.json` rather than
written here, so this suite also fails if the ROM data stops saying what the policy assumes
(`Potion` 20 / `Super Potion` 50 / `Hyper Potion` 200 / `Full Restore` 255).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_battle_items.py
"""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

from modules.story.battle_items import (  # noqa: E402
    FULL_RESTORE_PARAMETER,
    choose_healing_item,
    effective_heal,
)

checks = []


def check(label, ok, detail=""):
    checks.append((ok, label))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")


class FakeItem:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"<{self.name}>"


POTION, SUPER, HYPER, FULL = (FakeItem(n) for n in ("Potion", "Super Potion", "Hyper Potion", "Full Restore"))


def opts(*triples):
    return list(triples)


print("=" * 80)
print("REAL DATA — the heal amounts the policy reasons about come from items.json")
print("=" * 80)
data = json.loads((REPO / "sandbox-pokebot" / "modules" / "data" / "items.json").read_text(encoding="utf-8"))
by_name = {entry["name"]: entry for entry in data if isinstance(entry, dict) and entry.get("name")}
for name, expected in (("Potion", 20), ("Super Potion", 50), ("Hyper Potion", 200), ("Full Restore", 255)):
    entry = by_name.get(name, {})
    check(f"{name}: battle_use=healing, parameter={expected}",
          entry.get("battle_use") == "healing" and entry.get("parameter") == expected,
          f"got battle_use={entry.get('battle_use')!r} parameter={entry.get('parameter')!r}")
check("Full Heal is a STATUS item (parameter 0) and is therefore out of scope here",
      by_name.get("Full Heal", {}).get("parameter") == 0,
      f"got {by_name.get('Full Heal', {}).get('parameter')!r}")

print()
print("=" * 80)
print("POSITIVE CONTROL — a mon that plainly needs healing gets an item")
print("=" * 80)
control = choose_healing_item(10, 100, opts((POTION, 5, 20), (SUPER, 2, 50)))
check("badly hurt + items held -> returns an item", control is not None, repr(control))
if control is None:
    print("\n‼ CONTROL FAILED — the 'declines correctly' cases below prove nothing. Stop here.")
    sys.exit(1)

print()
print("=" * 80)
print("RULE 1 — only when it matters (above the threshold, attack instead)")
print("=" * 80)
check("healthy mon (80/100) -> no item",
      choose_healing_item(80, 100, opts((POTION, 5, 20))) is None)
check("at the threshold (35/100) -> heals", choose_healing_item(35, 100, opts((POTION, 5, 20))) is not None)
check("just above it (36/100) -> declines", choose_healing_item(36, 100, opts((POTION, 5, 20))) is None)

print()
print("=" * 80)
print("RULE 2 — cheapest SUFFICIENT item, so a Full Restore is not burned on a scratch")
print("=" * 80)
# ‼ THE FIRST VERSION OF THIS CASE WAS WRONG AND THE SUITE CAUGHT IT. It used 75/100, which is
# above the 35% threshold, so rule 1 declined and the "cheapest sufficient" logic never ran — the
# test was asserting rule 2 against a case that rule 1 owns. A case must be below the threshold
# for rule 2 to be under test at all.
# 18/60 = 30%: missing 42, so Potion(20) cannot cover it, Super(50) can, Full(255) can.
got = choose_healing_item(18, 60, opts((POTION, 5, 20), (SUPER, 5, 50), (FULL, 5, 255)))
check("missing 42 with Potion/Super/Full held -> picks Super Potion (smallest that covers)",
      got is SUPER, repr(got))
got = choose_healing_item(20, 100, opts((POTION, 5, 20), (SUPER, 5, 50), (FULL, 5, 255)))
check("missing 80, only Full Restore covers it -> picks Full Restore", got is FULL, repr(got))
got = choose_healing_item(20, 100, opts((POTION, 5, 20), (SUPER, 5, 50)))
check("missing 80, nothing covers it -> takes the LARGEST available (Super Potion)",
      got is SUPER, repr(got))
got = choose_healing_item(30, 100, opts((POTION, 9, 20), (HYPER, 1, 200)))
check("missing 70 with Potion/Hyper -> Hyper (Potion cannot cover, largest wins)",
      got is HYPER, repr(got))

print()
print("=" * 80)
print("RULE 3 — never heal into a losing race")
print("=" * 80)
check("best heal 20, but hits land for 45 -> declines and attacks instead",
      choose_healing_item(30, 100, opts((POTION, 5, 20)), worst_hit_taken=45) is None)
check("best heal 200, hits land for 45 -> heals",
      choose_healing_item(30, 100, opts((HYPER, 1, 200)), worst_hit_taken=45) is not None)
check("no observed hit yet (0) -> the rule is inert, not a blocker",
      choose_healing_item(30, 100, opts((POTION, 5, 20)), worst_hit_taken=0) is not None)

print()
print("=" * 80)
print("RULE 4 — BOUNDED per battle (the anti-infinite-heal-war bound)")
print("=" * 80)
check("under the bound -> heals", choose_healing_item(10, 100, opts((SUPER, 9, 50)), uses_so_far=3, max_uses=4) is not None)
check("AT the bound -> declines", choose_healing_item(10, 100, opts((SUPER, 9, 50)), uses_so_far=4, max_uses=4) is None)
check("over the bound -> declines", choose_healing_item(10, 100, opts((SUPER, 9, 50)), uses_so_far=9, max_uses=4) is None)

print()
print("=" * 80)
print("DEGENERATE INPUTS — must never raise, never pick nonsense")
print("=" * 80)
check("no items held -> None", choose_healing_item(10, 100, opts()) is None)
check("zero quantities -> None", choose_healing_item(10, 100, opts((POTION, 0, 20))) is None)
check("status-only item (parameter 0) is ignored", choose_healing_item(10, 100, opts((FakeItem("Full Heal"), 5, 0))) is None)
check("already fainted -> None (the faint chooser owns that)", choose_healing_item(0, 100, opts((SUPER, 5, 50))) is None)
check("full HP -> None", choose_healing_item(100, 100, opts((SUPER, 5, 50))) is None)
check("nonsense total_hp -> None, no exception", choose_healing_item(5, 0, opts((SUPER, 5, 50))) is None)
check("effective_heal caps a full-restore at the mon's max HP",
      effective_heal(FULL_RESTORE_PARAMETER, 77) == 77, str(effective_heal(FULL_RESTORE_PARAMETER, 77)))
check("effective_heal passes a normal parameter through", effective_heal(50, 300) == 50)

failed = [label for ok, label in checks if not ok]
print()
if failed:
    print(f"RESULT: {len(failed)} FAILED of {len(checks)}")
    for label in failed:
        print(f"   - {label}")
    sys.exit(1)
print(f"RESULT: ALL PASS ({len(checks)} checks)")
