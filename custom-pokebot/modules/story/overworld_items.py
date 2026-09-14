"""`#24-e4healing` — decide WHO to heal, and WITH WHAT, from the bag OUTSIDE battle.

WHY THIS EXISTS, measured rather than assumed. §Ch23 leg 11 bought the Elite Four's healing:
**Hyper Potion ×30 · Full Restore ×3 · Full Heal ×8 · Revive ×3**. Then `probe_ch24_readiness.py`
read the bag back and found that **11 of those 44 items cannot be used by any code path we have**:
`modules/story/battle_items.py:85` filters on `param > 0`, and `Full Heal`, `Revive` and `Antidote`
all carry `parameter == 0` in `modules/data/items.json`. That filter is CORRECT for its own module —
`battle_items` is deliberately scoped to HP restoration in battle, and says so — but it leaves the
gauntlet with:

  * **no way to revive anything.** A faint is permanent for all five fights.
  * **no way to cure status.** *(This clause read "Gen-3 freeze never thaws on its own"
    until 2026-09-13 — FALSE for Emerald, which self-thaws 20% per ATTEMPTED MOVE; see
    `battle_util.c`, `CANCELER_FROZEN`. Freeze is EXPENSIVE, not permanent.)*
    Glacia's Sealeo carries Attract,
    Phoebe has Confuse Ray and Will-O-Wisp, and both Tentacruel and Milotic carry Toxic.
  * **no way to top up HP between rooms.** Damage carries from Sidney all the way to Wallace.

⛔ THE ELITE FOUR IS A ONE-WAY GAUNTLET WITH NO NURSE (user directive 2026-09-04, and the routing
recon confirms every backward warp sits on `MB_NORMAL` and therefore never fires). Items ARE legal
there — `battle_main.c:4221-4239` blocks only LINK / FRONTIER / E-READER / RECORDED. ⇒ **the bag is
the entire healing system, and this module is the half of it that runs between rooms.**

THE POLICY, and the reasoning behind each rule:
  1. **NEVER A NO-OP.** A Potion on a full-HP mon and a Full Heal on a statusless mon are both
     refused by the game ("It won't have any effect!"), and a bot that tries one either burns a turn
     or hangs waiting for a state that never arrives. Every plan this module emits must CHANGE
     something. This is rule 1 because it is the one that costs a run.
  2. **REVIVE BEFORE HEALING.** A fainted Pokémon contributes nothing; a hurt one still fights.
     With three Revives against five fights, a Revive spent late is worth more than HP spent early.
  3. **⭐ REVIVE BY BATTLE VALUE, NOT BY SLOT ORDER.** `#24-ch23wally` records the faint-replacement
     ranking feeding a **L19 Zigzagoon** into fights. Spending one of three Revives on the HM mule
     instead of the L53 Sceptile is the same mistake with a scarcer resource. ⇒ rank by level.
  4. **CHEAPEST SUFFICIENT HP ITEM**, so a Full Restore is never burned on a scratch — there are
     only three, and they are the sole cure for `status + low HP` in one action.
  5. **STATUS IS CURED WITH `Full Heal` WHERE POSSIBLE**, keeping Full Restores for the compound
     case. ⚠ A Full Restore used purely as a status cure wastes its HP half.
  6. **BOUNDED.** `max_actions` caps a single healing session. Two healers with no bound is the
     KI-34 shape; here the risk is different but the guard is the same — a between-rooms heal that
     never terminates is a hung run in a place with no escape.

‼ THIS MODULE IS PURE — no emulator, no game state, no I/O — so it can be tested exhaustively in
milliseconds. The part that opens the bag and drives the party menu lives elsewhere; the two are
separated for exactly the reason `battle_items.py` is, and that separation is what let the battle
policy be proven correct without a ROM.
"""

from dataclasses import dataclass

#: Heal a Pokémon whose HP is at or below this fraction. Above it, an item is not worth the action.
#: ⚠ DELIBERATELY HIGHER THAN `battle_items.HEAL_AT_FRACTION` (0.35). In battle, healing costs a
#: TURN and the opponent attacks into it, so the bar is high. Between rooms an action costs nothing
#: but the item — and walking into Drake at 60% is how a gauntlet is lost. ⇒ different question,
#: different threshold. Do not "harmonise" these two numbers.
TOP_UP_BELOW = 0.90

#: The ROM's sentinel in `items.json` `parameter` meaning "restore all HP".
FULL_RESTORE_PARAMETER = 255

#: Items whose `parameter` is 0 but which are NOT HP items. Named so a reader is never left thinking
#: `parameter == 0` means "broken" — it means "this item's effect is not measured in HP".
STATUS_ONLY = ("Full Heal", "Antidote", "Awakening", "Burn Heal", "Ice Heal", "Paralyze Heal")

#: Actions allowed in one between-rooms healing session. A bound, not a preference (rule 6).
MAX_ACTIONS_PER_SESSION = 12


@dataclass(frozen=True)
class Target:
    """One party member, as far as this module is concerned. ⛔ Primitives only — keeping game
    objects out is what makes the policy testable without a ROM."""

    index: int
    name: str
    level: int
    current_hp: int
    total_hp: int
    status: str | None = None  # None / "PSN" / "TOX" / "BRN" / "PAR" / "SLP" / "FRZ"

    @property
    def fainted(self) -> bool:
        return self.current_hp <= 0

    @property
    def fraction(self) -> float:
        return 0.0 if self.total_hp <= 0 else self.current_hp / self.total_hp


@dataclass(frozen=True)
class Action:
    """One item to use on one party member, and WHY — the reason is carried so a driver can log
    an attribution rather than just a button sequence."""

    party_index: int
    item_name: str
    reason: str
    #: What must be true afterwards for this action to have WORKED. ⛔ The consequence, not the call.
    expect: str


def effective_heal(parameter: int, total_hp: int) -> int:
    """HP an item with this `parameter` would actually restore on a mon with `total_hp`.

    ‼ Note `min(parameter, missing)` is the game's behaviour, so a 200-point Hyper Potion on a
    139 HP Sceptile restores at most 139 — which is why the roster analysis's "30 potions is plenty"
    and "a potion is nearly a wasted turn on a small mon" are BOTH true.
    """
    if parameter >= FULL_RESTORE_PARAMETER:
        return total_hp
    return max(0, parameter)


def plan_healing(
    targets: "list[Target]",
    bag: "dict[str, int]",
    item_parameters: "dict[str, int]",
    *,
    healing_items: "set[str] | None" = None,
    top_up_below: float = TOP_UP_BELOW,
    max_actions: int = MAX_ACTIONS_PER_SESSION,
) -> "list[Action]":
    """Return the ordered list of item uses that would make this party fight-ready.

    :param targets: the party, as `Target`s.
    :param bag: `{item name: quantity}` — what we actually hold. ⛔ Read the bag; never assume.
    :param item_parameters: `{item name: parameter}` straight from `items.json`.
    :param healing_items: ⛔⛔ **NAMES THAT ARE ACTUALLY MEDICINE** — the caller derives this from
        `items.json` (`field_use == "healing"`). **REQUIRED IN PRACTICE.** Omitting it falls back to
        a conservative built-in allowlist rather than trusting `parameter`.

    ‼‼ WHY `healing_items` EXISTS — A LIVE DRIVE CAUGHT THIS, THE GATE DID NOT (2026-09-04).
    The first version filtered healers with `parameter > 0`, and on the real bag that selected
    **`Repel`**, whose `parameter` is **100** — *one hundred STEPS*, not one hundred HP. The plan
    read `(4, 'Repel', 'Mightyena at 0/144')` and the run failed at the menu, because a no-target
    item never opens the party menu at all.
    ⇒ ⛔ **`parameter` IS A UNION TYPE. Its meaning depends on the item**: HP for a potion, steps
    for a Repel, 0 for a status cure. **A number alone cannot tell you what an item does** — you
    need its KIND. This is the mirror image of `battle_items.py:85`, which wrongly EXCLUDES valid
    items with the same test; both bugs come from reading one field as if it were self-describing.
    ⭐ And the gate missed it for an instructive reason: **its item universe was cleaner than
    reality.** `PARAMS` held only medicine, so no trap existed to fall into. A policy test must
    include the confusing neighbours the real bag contains.

    ⛔ EVERY returned action CHANGES something (rule 1). An empty list means "nothing to do", which
    is a valid and common answer — and a caller must treat it as success, not as a failure to plan.
    """
    #: The fallback allowlist. Deliberately conservative: an item not named here is not used, which
    #: costs at worst a missed heal — while a wrong guess wastes a scarce item AND stalls a menu.
    if healing_items is None:
        healing_items = {"Potion", "Super Potion", "Hyper Potion", "Max Potion", "Full Restore",
                         "Revive", "Max Revive", "Full Heal", "Antidote", "Awakening",
                         "Burn Heal", "Ice Heal", "Paralyze Heal", "Fresh Water", "Soda Pop",
                         "Lemonade", "Moomoo Milk", "Energy Powder", "Energy Root", "Heal Powder",
                         "Revival Herb", "Lava Cookie", "Berry Juice", "Sacred Ash"}
    plan: "list[Action]" = []
    held = dict(bag)  # local copy: planning must not pretend to spend what a later step needs

    def take(name: str) -> bool:
        if held.get(name, 0) <= 0:
            return False
        held[name] -= 1
        return True

    # ---- rule 2 + 3 — REVIVE FIRST, AND BY BATTLE VALUE ------------------------------------------
    # ⛔ Sorted by LEVEL DESCENDING, so three Revives go to the three Pokémon most able to use them.
    # Slot order would spend one on whatever fainted first, which in this party is routinely the
    # L19 HM mule — the `#24-ch23wally` mistake, with a resource we cannot re-buy mid-gauntlet.
    for mon in sorted((m for m in targets if m.fainted), key=lambda m: -m.level):
        if len(plan) >= max_actions:
            break
        item = "Revive" if held.get("Revive", 0) > 0 else ("Max Revive" if held.get("Max Revive", 0) > 0 else None)
        if item is None or not take(item):
            continue
        plan.append(Action(
            mon.index, item,
            reason=f"{mon.name} L{mon.level} is FAINTED and is the highest-level mon still down",
            # ⚠ Revive returns a mon at HALF HP, so the post-condition is "alive", not "healthy".
            # The HP pass below then tops it up — which is why revives are planned FIRST.
            expect=f"party[{mon.index}].current_hp > 0",
        ))

    # ---- rule 5 — STATUS, CURED WITH THE CHEAP THING ---------------------------------------------
    for mon in targets:
        if len(plan) >= max_actions:
            break
        if mon.status is None or mon.fainted:
            continue  # ⛔ a fainted mon's status is irrelevant until it is revived
        cure = next((n for n in STATUS_ONLY if held.get(n, 0) > 0), None)
        if cure is None:
            # ⚠ Fall back to a Full Restore ONLY if nothing cheaper exists. It is the sole item that
            # fixes status, and there are three of them for five fights.
            cure = "Full Restore" if held.get("Full Restore", 0) > 0 else None
        if cure is None or not take(cure):
            continue
        plan.append(Action(
            mon.index, cure,
            reason=f"{mon.name} has {mon.status}"
                   + (" (⚠ FRZ — ~20%/attempted-move self-thaw: EXPENSIVE, not permanent)"
                      if mon.status == "FRZ" else ""),
            expect=f"party[{mon.index}].status is None",
        ))

    # ---- rule 1 + 4 — HP, CHEAPEST SUFFICIENT, AND NEVER A NO-OP ---------------------------------
    for mon in targets:
        if len(plan) >= max_actions:
            break
        # ⛔ A mon revived above is still at half HP in the GAME, but `targets` is a snapshot taken
        # BEFORE any of this ran. Treat a planned-revive mon as needing HP: it always does.
        revived = any(a.party_index == mon.index and a.item_name in ("Revive", "Max Revive") for a in plan)
        if not revived:
            if mon.fainted:
                continue  # could not be revived — no HP item works on a fainted mon
            if mon.fraction > top_up_below:
                continue  # rule 1: healing here would be a refused no-op or a wasted item

        missing = mon.total_hp - mon.current_hp if not revived else mon.total_hp // 2
        # ⛔ THE ALLOWLIST IS THE FILTER, NOT THE PARAMETER. `n in healing_items` is what keeps a
        # Repel (parameter 100 = STEPS) out of this list. See the docstring: a live drive planned
        # exactly that and the leg died at a menu that never opened.
        options = [(n, q, item_parameters.get(n, 0)) for n, q in held.items()
                   if q > 0 and n in healing_items]
        healers = [(effective_heal(p, mon.total_hp), n) for n, _, p in options
                   if p > 0 and n not in STATUS_ONLY]
        if not healers:
            continue
        sufficient = sorted((h for h in healers if h[0] >= missing), key=lambda h: (h[0], h[1]))
        pick = sufficient[0][1] if sufficient else sorted(healers, key=lambda h: (-h[0], h[1]))[0][1]
        if not take(pick):
            continue
        plan.append(Action(
            mon.index, pick,
            reason=f"{mon.name} at {mon.current_hp}/{mon.total_hp}"
                   + (" (just revived, returns at half HP)" if revived else ""),
            expect=f"party[{mon.index}].current_hp increased",
        ))

    return plan


def party_is_gauntlet_ready(targets: "list[Target]", *, top_up_below: float = TOP_UP_BELOW) -> bool:
    """True when nobody is fainted, nobody is statused, and everybody is above the top-up bar.

    ⛔ This is the ACCEPTANCE question for a between-rooms heal, and it is deliberately stricter
    than "did the items get used" — the Elite Four does not care how many Potions were consumed.
    """
    return all(
        (not m.fainted) and m.status is None and m.fraction > top_up_below
        for m in targets
    )
