"""`#24-battleitems` — decide WHETHER and WHICH healing item to use in a battle.

USER DIRECTIVE 2026-08-09: *"I want the bot to use items intelligently and strategically."*

WHY THIS EXISTS, measured rather than assumed. Batch `20260809-155844` (16,749 battles) showed
**bosses healing and the bot never doing so**: Norman's `Slaking` was restored **27 times, median
+81 HP, max +119** (`24 -> 143`, `13 -> 123`, `8 -> 117`) while the party did 6-8 chip damage a
turn, and **61.8% of boss-length battles** show an opponent healing. Boss losses end **~88% of all
non-finishing runs**. A super-effective attacker cannot beat an opponent that out-heals it; using
our own items is the missing half of that fight.

‼ EVERY NUMBER HERE COMES FROM THE ROM, NOT FROM MEMORY (standing project rule). Heal amounts are
read from `modules/data/items.json`, where a battle-usable healing item carries
`battle_use == "healing"` and `parameter` = HP restored (`Potion` 20, `Super Potion` 50,
`Hyper Potion` 200), with `255` as the game's "restore everything" sentinel (`Max Potion`,
`Full Restore`). `Full Heal` is `parameter == 0` — a STATUS cure, not an HP item, and is excluded
here on purpose: status handling is a separate feature and mixing it in would make this one
untestable.

THE POLICY, and the reasoning behind each rule — this is the "strategically" half of the request:
  1. **Only when it matters.** Above `HEAL_AT_FRACTION` the turn is better spent attacking.
  2. **Cheapest SUFFICIENT item.** Prefer the smallest heal that covers what is missing, so a
     `Full Restore` is never burned on a scratch. Only if nothing covers it do we take the
     largest available.
  3. **Never heal into a losing race.** If the best heal we hold is smaller than the biggest hit
     we have actually taken this battle, healing donates a turn and we still lose the exchange —
     so attack instead. This is what stops the bot trading potions against a boss that hits
     harder than our items heal.
  4. **BOUNDED per battle.** ‼ Load-bearing: the opponent heals too, and two healers with no bound
     is an infinite battle — the KI-34 shape that once burned 23.9M frames. `max_uses` caps it.
  5. **Never spend the last of an item on a trivial margin** is deliberately NOT a rule: the bot
     restocks, and a lost run costs more than a potion.

This module is PURE — no emulator, no game state, no I/O — so `repro_battle_items.py` can test the
policy exhaustively in milliseconds. The integration that reads the bag and the battle lives in
`story_mode.py`.
"""

#: Heal below this fraction of max HP; above it, attacking is worth more than the turn spent.
HEAL_AT_FRACTION = 0.35

#: The game's sentinel in `items.json` `parameter` meaning "restore all HP".
FULL_RESTORE_PARAMETER = 255

#: Item uses allowed per battle. ‼ A bound, not a preference — see rule 4 in the module docstring.
MAX_ITEM_USES_PER_BATTLE = 4


def effective_heal(parameter: int, total_hp: int) -> int:
    """HP an item with this `parameter` would actually restore on a mon with `total_hp`."""
    if parameter >= FULL_RESTORE_PARAMETER:
        return total_hp
    return max(0, parameter)


def choose_healing_item(
    current_hp: int,
    total_hp: int,
    options: "list[tuple[object, int, int]]",
    *,
    worst_hit_taken: int = 0,
    uses_so_far: int = 0,
    max_uses: int = MAX_ITEM_USES_PER_BATTLE,
    heal_at_fraction: float = HEAL_AT_FRACTION,
) -> "object | None":
    """Pick a healing item, or None to act normally.

    :param options: ``(item, quantity, parameter)`` for each battle-usable healing item held,
                    where ``parameter`` is the ROM's heal amount (255 = full).
    :param worst_hit_taken: the largest single HP loss observed this battle. Rule 3 uses it; 0
                            disables that rule (the first turn, when nothing has been observed).
    :param uses_so_far: items already used this battle, for the bound.
    """
    if total_hp <= 0 or current_hp <= 0:
        return None  # fainted or nonsense input — the faint chooser owns that path
    if uses_so_far >= max_uses:
        return None
    if current_hp / total_hp > heal_at_fraction:
        return None

    missing = total_hp - current_hp
    if missing <= 0:
        return None

    usable = [(item, qty, param) for item, qty, param in options if qty > 0 and param > 0]
    if not usable:
        return None

    # Rule 3 — do not heal into a losing race.
    best_possible = max(effective_heal(param, total_hp) for _, _, param in usable)
    if worst_hit_taken and best_possible < worst_hit_taken:
        return None

    # Rule 2 — cheapest sufficient, else the largest available.
    sufficient = [(effective_heal(p, total_hp), item) for item, _, p in usable
                  if effective_heal(p, total_hp) >= missing]
    if sufficient:
        # smallest heal that still covers the gap; ties broken by name for determinism
        sufficient.sort(key=lambda pair: (pair[0], getattr(pair[1], "name", "")))
        return sufficient[0][1]

    largest = [(effective_heal(p, total_hp), item) for item, _, p in usable]
    largest.sort(key=lambda pair: (-pair[0], getattr(pair[1], "name", "")))
    return largest[0][1]


# ==================================================================================================
# `#24-e4healing` STEP 3 — THE IN-BATTLE QUESTION: items whose `parameter` is 0
# ==================================================================================================
#: Statuses that COST THE TURN ANYWAY. ⛔ This set is the whole argument for curing in battle, and it
#: is deliberately small. Sleep and Freeze prevent acting, so a turn spent curing is strictly better
#: than a turn lost — the trade is free. Poison / Burn / Paralysis CHIP but still let the mon attack,
#: so spending a turn on them trades a guaranteed attack for a small HP saving, which rule 1 of this
#: module ("a turn spent healing is a turn not attacking") says is usually a loss.
#: ‼ Gen-3 FREEZE never thaws on its own (it needs a Fire-type hit or a thaw move), so an un-cured
#: freeze is a permanent loss of that Pokémon for the rest of the battle — which is exactly why
#: `pokemon_league.py`'s own driver stages a FROZEN Sceptile as its discriminator.
TURN_COSTING_STATUSES = frozenset({"Sleep", "Freeze"})
#: The same set, casefolded — the comparison actually used. ⛔ DERIVED, never typed a second time:
#: two hand-maintained copies of one set is how a widening lands in only one of them.
_TURN_COSTING_FOLDED = frozenset(s.casefold() for s in TURN_COSTING_STATUSES)

#: Item names that cure status. ⛔ BY NAME, NOT BY `parameter` — and that is the point of this whole
#: function. `overworld_items.py` records the live-drive lesson: `parameter` IS A UNION TYPE (HP for
#: a potion, **STEPS for a Repel**, 0 for a status cure), so a number alone cannot tell you what an
#: item does. The old in-battle filter `param > 0` excluded every one of these.
#: ✅ ALL SEVEN NAMES BELOW WERE VERIFIED AGAINST THE LIVE ITEM TABLE ON 2026-09-13 — every one
#: resolves via `get_item_by_name` and every one reports `battle_use == healing`.
#: ✅ AND A RENAME IS NOW GATED — statically, so the gate stays pure. `repro_battle_items.py` asserts
#: every name below resolves in `modules/data/items.json` AND reports `battle_use == "healing"`.
#: ‼‼ I FIRST SHIPPED THIS AS A DOCUMENTED BLIND SPOT, claiming a pure gate could not see item
#: names. A Tier 1 reviewer pointed out that the gate's own "REAL DATA" block ALREADY reads
#: `items.json` directly with no emulator — the guard was cheap the whole time. ⇒ **"documented
#: limitation" was the wrong answer when a fix was demonstrated 100 lines up in the same file.**
#: ⛔ WHY IT MATTERS: selection is BY NAME (the only honest way — `parameter` is a union type), so a
#: rename would make this policy SILENTLY INERT while every FakeItem check still passed. Not
#: hypothetical: **`"Paralyze Heal"` does not exist — the real spelling is `"Parlyz Heal"`**. Had
#: paralysis been in `TURN_COSTING_STATUSES`, the obvious spelling would have shipped dead.
#: Fault-tested: renaming one entry below reds the gate with "MISSING from items.json".
#: ⇒ **If you add a name here, resolve it against the live table first.** The purity of the gate is
#: worth keeping (it runs in milliseconds); the cost is that this one property is unguarded, and
#: saying so is better than pretending the gate covers it.
STATUS_CURE_ITEMS = ("Full Heal", "Full Restore", "Lava Cookie")
SLEEP_CURE_ITEMS = ("Awakening",)
FREEZE_CURE_ITEMS = ("Ice Heal",)
REVIVE_ITEMS = ("Revive", "Max Revive")


def choose_status_or_revive_item(
    status_name: str,
    non_fainted_count: int,
    options: "list[tuple[object, int, int]]",
    *,
    uses_so_far: int = 0,
    max_uses: int = MAX_ITEM_USES_PER_BATTLE,
    allow_revive: bool = False,
) -> "object | None":
    """Pick a STATUS CURE or a REVIVE, or None to act normally. The sibling of
    `choose_healing_item`, for the items whose `parameter` is 0.

    ⛔⛔ `allow_revive=False` EXISTS BECAUSE THE TWO ANSWERS HAVE DIFFERENT TARGETS, AND ONLY ONE OF
    THE TWO TARGETS IS PROVEN. A status cure is used on the **ACTIVE battler** — the same
    `mon.party_index` the HP policy already lands reliably. A **REVIVE is used on a FAINTED,
    NON-ACTIVE party member**, which is a DIFFERENT INDEX SPACE, and this is the single most
    bug-prone corner of this codebase: `handle_fainted_pokemon` has had **three** index-space bugs
    (KI-18, KI-34, KI-66), and CLAUDE.md rule 10 says to *"run an OBSERVE-ONLY probe printing both
    coordinates beside a ground truth derived independently, THEN apply it"*. The in-battle caller
    even carries an empirical heuristic for this (`story_mode.py`: party-order landed 19/19 when the
    target was slot 0, battle-order 9/10 when it was above slot 0) — and a fainted mon is by
    definition NOT the active one, so it falls in the half that heuristic is least sure about.
    ⇒ **The POLICY here is sound either way; what is unproven is the CALLER's ability to aim.**
    ⛔⛔ **THE DEFAULT IS `False`, AND THAT IS DELIBERATE.** A Tier 1 reviewer pointed out that a
    default of `True` means *"nothing in the signature stops a future caller from using the default
    and silently reintroducing the unproven revive-targeting path"*. A safe default costs the
    eventual, probe-backed caller one explicit keyword; an unsafe default costs a silent regression
    into the corner of this codebase with three prior bugs. ⇒ **opt IN to the risky half.**
    `KI-100` records the observe-only index probe that would justify flipping it.

    ‼‼ WHY THIS EXISTS AND WHY IT IS SEPARATE (`#24-e4healing` step 3, 2026-09-13).
    `06-DECISIONS-LOG.md` records the measured blocker: *"the policy filters on `param > 0`
    (`battle_items.py:85`), and Full Heal / Revive / Antidote all carry `parameter == 0` ⇒ **11 of
    the 44 items just bought are unusable by any code path we have**"*. The bot spent **₽54,300** on
    a gauntlet basket that included **Full Heal ×8 and Revive ×3** and could not use one of them
    mid-fight. Step 1 fixed the OUT-of-battle half (`overworld_items.plan_healing`); this is the
    in-battle half.
    ⛔ IT IS A SEPARATE FUNCTION ON PURPOSE. `choose_healing_item` is an HP-restoration policy whose
    every rule is expressed in HP (`missing`, `effective_heal`, `worst_hit_taken`). A status cure
    restores no HP, so folding it in would mean `effective_heal` returning 0 for an item we DO want —
    i.e. teaching the HP policy to lie. Two policies, one caller, is the same shape the module
    already uses for in-battle vs overworld thresholds.

    THE POLICY — deliberately narrow, because this runs in EVERY trainer battle in the game:
      1. **Cure only a status that COSTS THE TURN ANYWAY** (Sleep, Freeze — see
         `TURN_COSTING_STATUSES`). Curing poison/burn/paralysis trades a certain attack for a little
         HP, which rule 1 of this module already rejects. ⇒ this fires rarely and only when free.
      2. **Revive only when the active Pokémon is effectively the LAST one** (`non_fainted_count <= 1`).
         A Revive costs a turn and returns the mon **at half HP on the BENCH** — worth it only when
         the alternative is a whiteout. ⛔ Never revive "to have a spare": that is a turn donated to
         the opponent.
      3. **Prefer the CHEAPEST item that does the job.** A Full Restore also cures status, but it is
         the scarcest thing in the basket (×3 vs Full Heal ×8) and `choose_healing_item` needs it for
         the HP emergencies — so a dedicated cure wins over Full Restore when both are held.
      4. **The same per-battle bound applies** (`MAX_ITEM_USES_PER_BATTLE`), shared with the HP
         policy via `uses_so_far`, so the two together can never exceed the cap. ⛔ That bound is what
         makes a revive loop (revive → faint → revive) terminate.

    :param status_name: the active Pokémon's status, as `StatusCondition.name` — "Healthy", "Sleep",
                        "Freeze", "Poison", "Burn", "Paralysis", "BadPoison".
    :param non_fainted_count: how many party members can still fight, INCLUDING the active one.
    :param options: ``(item, quantity, parameter)`` as `choose_healing_item` takes them.
    ⇒ returns the item to use, or None. ⛔ A None here is a normal, common answer.
    """
    if uses_so_far >= max_uses:
        return None

    # ⛔ NORMALISE THE STATUS — MEASURED NECESSARY, NOT DEFENSIVE PROGRAMMING (2026-09-13).
    # The codebase's status is a `StatusCondition` ENUM, and this policy compares plain strings. A
    # caller that passes the enum itself, or `str(enum)` (which is "StatusCondition.Sleep"), got
    # **None — silently no cure, no error**, verified by running all three forms. That is the exact
    # "goes inert and every test still passes" shape this module's own comments warn about, so the
    # function accepts all three rather than trusting the caller to remember.
    # ⛔ `.name` IS READ INSIDE A TRY. A status object whose `.name` is a PROPERTY THAT RAISES would
    # otherwise propagate out of a PURE policy function — measured: a raising `.name` escaped as a
    # RuntimeError. The caller does wrap this (`decide_turn` catches Exception), but a pure policy
    # that raises on its own input is a landmine for the next caller, which may not.
    try:
        raw = getattr(status_name, "name", status_name)   # StatusCondition.Sleep -> "Sleep"
    except Exception:  # noqa: BLE001 — an unreadable status is "no status we act on", never a crash
        return None
    # ⛔ CASEFOLD. A caller passing "sleep" instead of "Sleep" got None — silently no cure, no error.
    # The comparison set is two literals that collide with nothing, so matching case-insensitively
    # closes a silent-failure path at no risk. (`.rsplit` first: "StatusCondition.Sleep" -> "Sleep".)
    status = str(raw).rsplit(".", 1)[-1].casefold()

    held = {}
    for item, qty, _param in options:
        if qty > 0:
            held[str(getattr(item, "name", item))] = item

    # --- rule 1 — cure a turn-costing status -----------------------------------------------------
    if status in _TURN_COSTING_FOLDED:
        specific = SLEEP_CURE_ITEMS if status == "sleep" else FREEZE_CURE_ITEMS
        # rule 3: the dedicated cure first, then the general one, then the scarce Full Restore last.
        for name in (*specific, "Full Heal", "Lava Cookie", "Full Restore"):
            if name in held:
                return held[name]
        return None

    # --- rule 2 — revive only as the alternative to a whiteout -----------------------------------
    # ⛔ `allow_revive` is checked HERE and not at the top, deliberately: a caller that forbids
    # revives must still get its status cure above. Gating the whole function would silently
    # disable rule 1 as well — the "one flag, two behaviours" shape that hid the Wonder Guard
    # demotion inside an unrelated revert flag.
    if allow_revive and non_fainted_count <= 1:
        for name in REVIVE_ITEMS:
            if name in held:
                return held[name]

    return None
