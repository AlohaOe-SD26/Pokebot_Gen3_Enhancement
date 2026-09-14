"""GATE — a successful STATUS CURE must never be read as a failed item by the no-op detector.

‼‼ THE BUG THIS EXISTS TO PREVENT, caught by a Tier 1 reviewer BEFORE it shipped (2026-09-13).
`StoryItemBattleStrategy._maybe_use_item` carries a no-op detector built for a measured problem: the
battle item menu does not reliably execute, so a request that does not RAISE OUR HP by the next
decision is treated as a miss — first miss flips the index space, second sets
`_items_ineffective = True`, which disables **all** item use for the rest of that battle.

⛔ A STATUS CURE NEVER RAISES HP. So when `#24-e4healing` step 3 wired status cures into the same
method, every SUCCESSFUL cure looked like a failure:
    turn N   : mon is asleep  -> Full Heal cures it     -> HP unchanged -> "no effect", flip (1st)
    turn N+k : mon is frozen  -> Ice Heal cures it      -> HP unchanged -> "no effect", DISABLE ALL
⇒ the bot would lose HP-emergency healing for the remainder of an Elite Four fight **because two
cures worked**. Two cures in one battle is not exotic — `pokemon_league.py`'s own driver stages a
FROZEN Sceptile precisely because freeze and sleep both occur.
‼ THE 72 CHECKS IN `repro_battle_items.py` COULD NOT SEE THIS. They are pure-function and
static-source checks; this is a TURN-OVER-TURN STATE MACHINE. ⇒ *a policy can be perfect and its
integration still broken; gate the state machine separately.*

WHAT THIS DRIVES: the real `StoryItemBattleStrategy._maybe_use_item`, with the emulator-facing
edges faked (bag, party, battle state). No ROM, no emulator — milliseconds.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_item_noop_detector.py
"""
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))

checks: "list[tuple[bool, str]]" = []
bag_holder: dict = {}


def check(label, ok, detail=""):
    checks.append((bool(ok), label))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")


# ---------------------------------------------------------------- fakes
class FakeStatus:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"StatusCondition.{self.name}"


class FakeItem:
    def __init__(self, name, parameter, battle_use):
        self.name = name
        self.parameter = parameter
        self.battle_use = battle_use

    def __repr__(self):
        return f"<{self.name}>"


class FakeSlot:
    def __init__(self, item, quantity):
        self.item = item
        self.quantity = quantity


class FakeBag:
    def __init__(self, slots):
        self.items = slots


class FakeMon:
    """Stands in for a BattlePokemon. ⛔ Exposes `status_permanent`, NOT `status_condition` — using
    the wrong name is the dead-path bug `repro_battle_items.py` gates statically."""

    def __init__(self, party_index=0, hp=100, total=100, status="Healthy"):
        self.party_index = party_index
        self.current_hp = hp
        self.total_hp = total
        self.status_permanent = FakeStatus(status)
        self.is_egg = False
        self.species = type("S", (), {"name": "Testmon"})()


class FakeSide:
    def __init__(self, mon):
        self.left_battler = mon


class FakeBattleState:
    def __init__(self, mon, battle_type):
        self.own_side = FakeSide(mon)
        self.type = battle_type


class FakeParty(list):
    """The strategy's base `__init__` reads `get_party().first_non_fainted.index`, so the fake must
    be list-like AND carry that property. ⛔ Patched BEFORE importing the strategy, because
    `default.py` does `from modules.pokemon_party import get_party` and would otherwise hold its own
    binding to the real one."""

    @property
    def first_non_fainted(self):
        for m in self:
            if m is not None and m.current_hp > 0:
                return m
        return None


def main() -> int:
    from modules.items import ItemBattleUse
    from modules.battle_state import BattleType
    import modules.items as items_mod
    import modules.pokemon_party as party_mod

    _roster = FakeParty([FakeMon(0), FakeMon(1), FakeMon(2)])
    for _i, _m in enumerate(_roster):
        _m.index = _i
    party_mod.get_party = lambda: _roster          # patch BEFORE the strategy is imported
    items_mod.get_item_bag = lambda: bag_holder["bag"]

    from plugins.custom_modes.story_mode import StoryItemBattleStrategy

    HYPER = FakeItem("Hyper Potion", 200, ItemBattleUse.Healing)
    FULLHEAL = FakeItem("Full Heal", 0, ItemBattleUse.Healing)
    ICEHEAL = FakeItem("Ice Heal", 0, ItemBattleUse.Healing)
    bag_holder["bag"] = FakeBag([FakeSlot(HYPER, 30), FakeSlot(FULLHEAL, 8), FakeSlot(ICEHEAL, 4)])

    print("=" * 84)
    print("THE REGRESSION: two successful status cures in ONE battle")
    print("=" * 84)
    s = StoryItemBattleStrategy()

    # --- turn 1: asleep, holding a Full Heal -> the policy must ask for it -----------------------
    mon = FakeMon(status="Sleep")
    action = s._maybe_use_item(FakeBattleState(mon, {BattleType.Trainer}))
    check("CONTROL: an asleep mon with a Full Heal held -> an item action is returned",
          action is not None, repr(action))
    if action is None:
        print("\n‼ CONTROL FAILED — every check below would prove nothing. Stop here.")
        return 1
    check("  ... and it recorded a STATUS request, not an HP one",
          s._status_when_item_requested is not None and s._hp_when_item_requested is None,
          f"status={s._status_when_item_requested} hp={s._hp_when_item_requested}")

    # --- turn 2: the cure WORKED (status gone) but HP is unchanged ------------------------------
    mon2 = FakeMon(status="Healthy")          # cured; HP identical
    s._maybe_use_item(FakeBattleState(mon2, {BattleType.Trainer}))
    check("⛔ a WORKING cure does NOT flip the index space (HP did not rise, and must not matter)",
          s._index_space_flipped is False, f"flipped={s._index_space_flipped}")
    check("⛔ ... and does NOT disable items",
          s._items_ineffective is False, f"ineffective={s._items_ineffective}")

    # --- turn 3: frozen later in the SAME battle, cured again ------------------------------------
    mon3 = FakeMon(status="Freeze")
    a3 = s._maybe_use_item(FakeBattleState(mon3, {BattleType.Trainer}))
    check("a second status (Freeze) in the same battle still gets an item",
          a3 is not None, repr(a3))
    mon4 = FakeMon(status="Healthy")
    s._maybe_use_item(FakeBattleState(mon4, {BattleType.Trainer}))
    check("⛔⛔ AFTER TWO SUCCESSFUL CURES, ITEMS ARE STILL ENABLED (the whole point of this gate)",
          s._items_ineffective is False,
          "this was the shipped-bug scenario: two cures disabled HP healing for the rest of the fight")

    # --- and the HP path must still work afterwards ----------------------------------------------
    hurt = FakeMon(hp=10, total=100, status="Healthy")
    a5 = s._maybe_use_item(FakeBattleState(hurt, {BattleType.Trainer}))
    check("⭐ the HP-emergency path STILL WORKS after two cures",
          a5 is not None, repr(a5))
    check("  ... and an HP request records an HP marker, not a status one",
          s._hp_when_item_requested is not None, f"hp={s._hp_when_item_requested}")

    print()
    print("=" * 84)
    print("THE HP DETECTOR IS UNTOUCHED — a genuinely failed HP item must still be caught")
    print("=" * 84)
    s2 = StoryItemBattleStrategy()
    hurt1 = FakeMon(hp=10, total=100)
    check("CONTROL: a badly hurt mon asks for an item",
          s2._maybe_use_item(FakeBattleState(hurt1, {BattleType.Trainer})) is not None)
    s2._maybe_use_item(FakeBattleState(FakeMon(hp=10, total=100), {BattleType.Trainer}))
    check("an HP item that did NOT raise HP still flips the index space (miss #1)",
          s2._index_space_flipped is True, f"flipped={s2._index_space_flipped}")
    s2._maybe_use_item(FakeBattleState(FakeMon(hp=10, total=100), {BattleType.Trainer}))
    check("⭐ and a SECOND HP miss still disables items — the proven guard is intact",
          s2._items_ineffective is True, f"ineffective={s2._items_ineffective}")

    failed = [label for ok, label in checks if not ok]
    print()
    if failed:
        print(f"RESULT: {len(failed)} FAILED of {len(checks)}")
        for label in failed:
            print(f"   - {label}")
        return 1
    print(f"RESULT: ALL PASS ({len(checks)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
