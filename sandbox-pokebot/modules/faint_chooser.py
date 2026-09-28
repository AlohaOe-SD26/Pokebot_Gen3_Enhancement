"""WHO to send out after a faint, decided by IDENTITY, never by index conversion (`#27-ki47range`, KI-47, 2026-09-28).

WHY THIS MODULE EXISTS. `battle_handler.handle_fainted_pokemon` converted party indexes between "field order" and
"menu order" in three places, and that function has now had FOUR index-space bugs (KI-18, KI-34, KI-66, KI-47). The
fourth, measured with `--driver ki47oor` (`ai-research-notes/2026-09-28-ki47range-PREDICTIONS*.md`):

- The handler mapped indexes through `gBattlePartyCurrentOrder` as snapshotted at its entry. After an ENEMY send-out
  that global holds the ENEMY's order: `SwitchPartyOrder()` (battle_main.c) copies ANY battler's order into it, with
  no side check. The player's own menu re-copies the player's order only when it opens.
- The recovery sweep then mapped slots that were ALREADY in menu order a second time. At party 4 that produced menu
  slots 4/5, which the cursor can never reach; after the only reachable candidate was refused, it pressed Down until
  the 3,000-frame KI-47 watchdog (unfixed `Foor`: 685 Downs, 3,045 frames).
- A second, quieter consequence: with a perfectly NATURAL order (the player switched once), the double map sends the
  WRONG living mon (arm `Swp`).

THE RULE HERE (CLAUDE.md rule 3: assert identity, never position). Remember WHO the strategy chose, as
`(personality value, species index)`, and once the in-battle menu is open, find that identity in `get_party()`. The
decomp (a NOTE, quoted in the predictions addendum) says `OpenPartyMenuInBattle` calls `UpdatePartyToBattleOrder()`
synchronously, so while the menu is open `gPlayerParty[i]` IS menu slot i and `gPartyMenu.slotId` indexes it. No
order is consulted, so a stale or foreign `gBattlePartyCurrentOrder` cannot matter.

WHY SPECIES IS PART OF THE KEY. A Shedinja is a byte copy of the Nincada it came from (`CreateShedinja`), so in a real
game a Ninjask and its Shedinja share a personality value AND an OT ID. The story party carries a Nincada.

PURE: no emulator reads, so `tools/story-dev/probe_faint_chooser_identity.py` can test it with plain objects.
"""

from typing import Iterable, Optional


def mon_identity(mon) -> Optional[tuple[int, int]]:
    """`(personality value, species index)`, or None for an empty slot or unreadable data."""
    if mon is None:
        return None
    try:
        return int(mon.personality_value), int(mon.species.index)
    except Exception:  # noqa: BLE001 - unreadable data is "no identity", never a crash mid-battle
        return None


def field_identities(battlers: Iterable) -> set[tuple[int, int]]:
    """Identities of OUR battlers on the field (from `gBattleMons`), fainted ones included. Pass
    `(own_side.left_battler, own_side.right_battler)`; None entries are skipped."""
    result = set()
    for battler in battlers:
        ident = mon_identity(battler)
        if ident is not None:
            result.add(ident)
    return result


def _can_be_sent(mon) -> bool:
    """A living, non-egg mon. Unreadable data is "no", never a crash mid-battle."""
    if mon is None:
        return False
    try:
        return not mon.is_egg and mon.current_hp > 0
    except Exception:  # noqa: BLE001
        return False


def faint_chooser_plan(party_in_menu, on_field: set, chosen: Optional[tuple[int, int]]):
    """Plan the choice IN MENU ORDER. `party_in_menu` must be `get_party()` read while the in-battle party menu is open.

    Returns `(target, candidates, on_field_slots)`:
      candidates      menu slots of living, non-egg mons whose identity is not on the field; by construction every
                      one is `< len(party_in_menu)`, so an unreachable slot cannot arise;
      target          the menu slot holding `chosen` if that slot is a candidate, else None (the caller falls back);
      on_field_slots  menu slots whose identity is on the field (logged, and excluded from `candidates`).
    """
    on_field_slots = set()
    for slot, mon in enumerate(party_in_menu):
        ident = mon_identity(mon)
        if ident is not None and ident in on_field:
            on_field_slots.add(slot)
    candidates = {slot for slot, mon in enumerate(party_in_menu) if _can_be_sent(mon) and slot not in on_field_slots}
    target = None
    if chosen is not None:
        for slot, mon in enumerate(party_in_menu):
            if slot in candidates and mon_identity(mon) == chosen:
                target = slot
                break
    return target, candidates, on_field_slots
