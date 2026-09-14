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

print()
print("=" * 80)
print("`#24-e4healing` STEP 3 — THE PARAMETER==0 ITEMS (status cures and revives)")
print("=" * 80)
# ⛔ WHY THESE CHECKS EXIST. `06-DECISIONS-LOG.md` (2026-09-04): "the policy filters on `param > 0`
# ... Full Heal / Revive / Antidote all carry `parameter == 0` ⇒ 11 of the 44 items just bought are
# unusable by any code path we have". The bot spent ₽54,300 on a basket it could not open.
from modules.story.battle_items import (  # noqa: E402
    choose_status_or_revive_item, TURN_COSTING_STATUSES,
    STATUS_CURE_ITEMS, SLEEP_CURE_ITEMS, FREEZE_CURE_ITEMS, REVIVE_ITEMS,
)

# ⛔⛔ EVERY NAME THE POLICY SELECTS BY MUST EXIST IN `items.json` — AND THIS IS A STATIC CHECK, SO
# THE GATE STAYS PURE. I originally DISCLOSED this hazard instead of fixing it, claiming a pure gate
# could not see item names; a Tier 1 reviewer pointed out that the "REAL DATA" block ~100 lines above
# already reads `items.json` directly with no emulator. ⇒ the guard was cheap all along, and
# "documented limitation" was the wrong answer when a fix was demonstrated in the same file.
# ‼ WHY IT MATTERS: selection is BY NAME (the only honest way — `parameter` is a union type), so a
# renamed item makes the policy SILENTLY INERT while all 53 FakeItem checks still pass. Not
# hypothetical: `"Paralyze Heal"` does NOT exist in this data — the real spelling is `"Parlyz Heal"`.
for _policy_name in (*STATUS_CURE_ITEMS, *SLEEP_CURE_ITEMS, *FREEZE_CURE_ITEMS, *REVIVE_ITEMS):
    _entry = by_name.get(_policy_name)
    check(f"policy name {_policy_name!r} exists in items.json and is medicine",
          _entry is not None and _entry.get("battle_use") == "healing",
          "MISSING from items.json — the policy would be silently inert" if _entry is None
          else f"battle_use={_entry.get('battle_use')!r}")
check("⛔ the misspelling that motivates this check is genuinely absent",
      "Paralyze Heal" not in by_name and "Parlyz Heal" in by_name,
      "if this ever flips, re-read the hazard note in battle_items.py")

FULLHEAL, REVIVE, MAXREVIVE = (FakeItem(n) for n in ("Full Heal", "Revive", "Max Revive"))
AWAKEN, ICEHEAL, ANTIDOTE = (FakeItem(n) for n in ("Awakening", "Ice Heal", "Antidote"))
# ⛔⛔ THE CONFUSING NEIGHBOURS, AND THEY ARE THE POINT OF THIS BLOCK.
# `overworld_items.py` records the live-drive failure this test exists to prevent: filtering by
# `parameter > 0` selected **Repel**, whose parameter is 100 — *one hundred STEPS*. The note's own
# lesson: "the gate missed it because its item universe was CLEANER THAN REALITY. A policy test must
# include the confusing neighbours the real bag contains." So the bag below holds them.
REPEL, ETHER, XATTACK = (FakeItem(n) for n in ("Repel", "Ether", "X Attack"))
BAG = opts((FULLHEAL, 8, 0), (REVIVE, 3, 0), (POTION, 5, 20), (HYPER, 30, 200),
           (REPEL, 4, 100), (ETHER, 2, 10), (XATTACK, 1, 0))

# --- POSITIVE CONTROL FIRST — if this fails, every "declines" check below proves nothing ---------
ctl = choose_status_or_revive_item("Sleep", 3, BAG)
check("CONTROL: asleep with a Full Heal held -> returns it",
      getattr(ctl, "name", None) == "Full Heal", repr(ctl))
if getattr(ctl, "name", None) != "Full Heal":
    print()
    print("‼ CONTROL FAILED — the declines below prove nothing. Stop here.")
    sys.exit(1)

check("Freeze is cured too (Emerald self-thaws ~20%/attempted move: EXPENSIVE, not permanent)",
      getattr(choose_status_or_revive_item("Freeze", 3, BAG), "name", None) == "Full Heal")
check("a DEDICATED cure is preferred over the general Full Heal (rule 3)",
      getattr(choose_status_or_revive_item("Sleep", 3, opts((AWAKEN, 2, 0), (FULLHEAL, 8, 0))),
              "name", None) == "Awakening")
check("Ice Heal preferred for Freeze",
      getattr(choose_status_or_revive_item("Freeze", 3, opts((ICEHEAL, 2, 0), (FULLHEAL, 8, 0))),
              "name", None) == "Ice Heal")
# --- the DECLINES — each one is a turn NOT donated to the opponent -------------------------------
for st in ("Poison", "BadPoison", "Burn", "Paralysis"):
    check(f"{st} CHIPS but still lets us act -> declines (rule 1)",
          choose_status_or_revive_item(st, 3, BAG) is None)
check("Healthy with mons in reserve -> no revive (rule 2)",
      choose_status_or_revive_item("Healthy", 3, BAG) is None)
check("Healthy on the LAST mon, revives EXPLICITLY ENABLED -> revives",
      getattr(choose_status_or_revive_item("Healthy", 1, BAG, allow_revive=True),
              "name", None) == "Revive")
# ⛔⛔ THE DEFAULT MUST BE THE SAFE ONE. A Tier 1 reviewer flagged that `allow_revive=True` by default
# means nothing in the signature stops a future caller from silently re-entering the unproven
# revive-TARGETING path (KI-100; the index space behind KI-18/KI-34/KI-66). Opt IN to the risky half.
check("⛔ the DEFAULT does NOT revive — the risky half is opt-in (KI-100)",
      choose_status_or_revive_item("Healthy", 1, BAG) is None)
check("the per-battle cap is SHARED with the HP policy",
      choose_status_or_revive_item("Sleep", 3, BAG, uses_so_far=4) is None)
check("asleep but holding NO cure -> None, no exception",
      choose_status_or_revive_item("Sleep", 3, opts((POTION, 5, 20), (REPEL, 4, 100))) is None)
check("zero quantity is not 'held'",
      choose_status_or_revive_item("Sleep", 3, opts((FULLHEAL, 0, 0))) is None)
# --- ⛔ THE TRAP ITSELF ---------------------------------------------------------------------------
check("⛔ REPEL (parameter 100 = STEPS) is never chosen for a status",
      getattr(choose_status_or_revive_item("Sleep", 3, opts((REPEL, 4, 100))), "name", None) != "Repel")
check("⛔ REPEL is never chosen as a revive either",
      getattr(choose_status_or_revive_item("Healthy", 1, opts((REPEL, 4, 100))), "name", None) != "Repel")
check("⛔ an X Attack (parameter 0, NOT medicine) is never chosen",
      choose_status_or_revive_item("Sleep", 1, opts((XATTACK, 1, 0))) is None)
check("the turn-costing set is exactly Sleep+Freeze (widening it needs a new ruling)",
      set(TURN_COSTING_STATUSES) == {"Sleep", "Freeze"}, str(sorted(TURN_COSTING_STATUSES)))
# --- ⛔ allow_revive: the two answers have DIFFERENT TARGETS and only one is proven ---------------
# A status cure aims at the ACTIVE battler (the index the HP policy already lands 19/19 at slot 0).
# A revive aims at a FAINTED, NON-ACTIVE member — the index space behind KI-18 / KI-34 / KI-66.
# These two checks pin that the flag suppresses ONLY the revive, never the cure.
check("allow_revive=False suppresses the revive",
      choose_status_or_revive_item("Healthy", 1, BAG, allow_revive=False) is None)
# --- ⛔ THE STATUS ARGUMENT ACCEPTS ALL THREE FORMS A CALLER MIGHT PASS ---------------------------
# The codebase's status is a `StatusCondition` ENUM; this policy compares strings. Before hardening,
# passing the enum (or `str(enum)` = "StatusCondition.Sleep") returned None — SILENTLY no cure and
# no error. These three checks pin that all three forms work, because the failure mode was invisible.


class _FakeStatus:  # stands in for StatusCondition.Sleep without importing the ROM-backed enum
    name = "Sleep"

    def __str__(self):
        return "StatusCondition.Sleep"


check("status as a plain string cures",
      getattr(choose_status_or_revive_item("Sleep", 3, BAG), "name", None) == "Full Heal")
check("status as an ENUM-like object (has .name) cures",
      getattr(choose_status_or_revive_item(_FakeStatus(), 3, BAG), "name", None) == "Full Heal")
check("status as 'StatusCondition.Sleep' cures",
      getattr(choose_status_or_revive_item("StatusCondition.Sleep", 3, BAG), "name", None) == "Full Heal")
check("a chip status still declines in dotted form",
      choose_status_or_revive_item("StatusCondition.Poison", 3, BAG) is None)
# --- the two gaps a Tier 1 reviewer named, now closed ---------------------------------------------
check("a LOWERCASE status still cures (was silently None)",
      getattr(choose_status_or_revive_item("sleep", 3, BAG), "name", None) == "Full Heal")
check("mixed case too",
      getattr(choose_status_or_revive_item("FREEZE", 3, BAG), "name", None) == "Full Heal")
check("a lowercase CHIP status still declines (casefold must not widen the set)",
      choose_status_or_revive_item("poison", 3, BAG) is None)


class _RaisingStatus:
    @property
    def name(self):
        raise RuntimeError("a status object whose .name blows up")


check("⛔ a status whose .name RAISES returns None instead of propagating out of a PURE policy",
      choose_status_or_revive_item(_RaisingStatus(), 3, BAG) is None)
check("the folded set is DERIVED from the public one, not typed twice",
      {s.casefold() for s in TURN_COSTING_STATUSES} == {"sleep", "freeze"})

print()
print("=" * 80)
print("THE WIRING — static checks on story_mode.py, so a DEAD PATH cannot come back")
print("=" * 80)
# ⛔⛔ WHY THESE EXIST. The first draft of the wiring read `getattr(mon, "status_condition", None)`.
# `BattlePokemon` has NO `status_condition` — that property is on `Pokemon`. Behind a safe getattr
# the cure would have NEVER FIRED, silently, forever, with all 66 policy checks still green. These
# checks read the caller's source: pure (no ROM, no emulator), and they pin the three things that
# make the call live rather than decorative.
_wiring = (REPO / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py").read_text(
    encoding="utf-8", errors="replace")
check("the caller actually CALLS the status policy",
      "choose_status_or_revive_item(" in _wiring)
check("⛔ it passes `status_permanent` — the property BattlePokemon really has",
      "mon.status_permanent" in _wiring,
      "BattlePokemon has no `status_condition`; using that name makes the cure permanently dead")
check("⛔ it does NOT use the non-existent `status_condition` on the battle mon",
      'getattr(mon, "status_condition"' not in _wiring)
check("⛔ revives stay OFF at the call site until KI-100's index probe exists",
      "allow_revive=False" in _wiring)
check("the HP policy is still asked FIRST (an HP emergency outranks a status cure)",
      _wiring.index("choose_healing_item(") < _wiring.index("choose_status_or_revive_item("))
check("the status policy is given the UNFILTERED medicine list, not the parameter>0 one",
      "medicine,\n                uses_so_far=self._item_uses," in _wiring,
      "passing `options` here would re-create the parameter>0 bug this item exists to fix")
check("allow_revive=False STILL CURES STATUS (one flag must not disable two behaviours)",
      getattr(choose_status_or_revive_item("Sleep", 1, BAG, allow_revive=False),
              "name", None) == "Full Heal")
# --- and the HP policy must be UNCHANGED by all of this ------------------------------------------
check("REGRESSION GUARD: the HP policy still ignores parameter==0 items",
      choose_healing_item(10, 100, opts((FULLHEAL, 8, 0))) is None)
# ⚠ 10/100 would NOT prove this: the gap is 90, which a 20-HP Potion cannot cover, so the correct
# answer there is the Hyper Potion. (My first version of this check asserted "Potion" and FAILED —
# the SUBJECT was right and the CHECK was wrong, which is the third time in this project that has
# happened. Pick inputs where the intended winner is actually sufficient.)
check("REGRESSION GUARD: the HP policy still picks cheapest-SUFFICIENT",
      getattr(choose_healing_item(10, 30, opts((POTION, 5, 20), (HYPER, 30, 200))),
              "name", None) == "Potion",
      "at 10/30 the gap is 20, which a Potion covers exactly, so it must beat the Hyper Potion")

failed = [label for ok, label in checks if not ok]
print()
if failed:
    print(f"RESULT: {len(failed)} FAILED of {len(checks)}")
    for label in failed:
        print(f"   - {label}")
    sys.exit(1)
print(f"RESULT: ALL PASS ({len(checks)} checks)")
