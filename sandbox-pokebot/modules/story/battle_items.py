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
