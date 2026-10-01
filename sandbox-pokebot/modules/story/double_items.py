"""Design v2 step 13 (KB-2, healing items in DOUBLE battles): the PURE logic (`doubleitems13-DESIGN.md` C6).

WHY. `StoryItemBattleStrategy` healed only in single battles: a double fell through to the parent's attack-only branch
(design V4), and the executor that carries an item out knew nothing about WHICH of our two Pokémon was choosing (V1, V5).
This module holds every decision of the double-battle item path that can be stated without the emulator, so the gate
`tools/story-dev/probe_double_items.py` can pin each one on plain inputs (rows DP01-DP07 of
`ai-research-notes/2026-09-30-doubleitems13-PREDICTIONS.md`, filed before this file existed).

⛔ THE CONTRACT
- PURE: no emulator, no memory read, no import of `modules.items` / `modules.battle_state` (both pull the emulator
  context in). The callers — `StoryItemBattleStrategy.decide_turn_in_double_battle` (story_mode.py) and the executor
  `battle_action_use_item` (battle_action_selection.py) — do the raw reads and hand the bytes here.
- The flag is `POKEBOT_R27_DOUBLEITEMS`, read PER CALL by the callers (design D5: the Mossdeep harness drivers build
  the strategy themselves and never run `reset_per_run_state`, the `POKEBOT_R27_KEYITEMS` precedent).
- The three FAULT names live here so the gate and the registry can name one constant; each is READ inside production
  (C7), never here: `CURSOR0` in `battle_menuing.py`, `WRONGSLOT` and `NOGUARD` in `battle_action_selection.py`.
"""

from __future__ import annotations

from modules.story.battle_items import HEAL_AT_FRACTION, MAX_ITEM_USES_PER_BATTLE, effective_heal

#: The feature flag (D5). `observe` logs one `[DBLITEM-OBS]` line per decision and changes nothing; `1` acts; any
#: other value — `0`, `yes`, `ON`, ` 1` — is OFF, exactly like unset (DP01).
FLAG = "POKEBOT_R27_DOUBLEITEMS"
#: C7 fault arms (never set in a real run; registered in `29-DISABLED-FEATURES-REGISTRY.md`).
FAULT_CURSOR0 = "POKEBOT_R27_FAULT_DBL_CURSOR0"      # C1 reads byte 0 of gActionSelectionCursor for every battler
FAULT_WRONGSLOT = "POKEBOT_R27_FAULT_DBL_WRONGSLOT"  # the executor drives the party cursor to the PARTNER's slot
FAULT_NOGUARD = "POKEBOT_R27_FAULT_DBL_NOGUARD"      # D4's PID comparison is skipped: A is pressed whatever the PID

OFF, OBSERVE, ON = "off", "observe", "on"

#: `gBattleTypeFlags` bits (`modules/battle_state.py:44-65`, design V7; pret `include/constants/battle.h`).
BATTLE_TYPE_DOUBLE = 1 << 0
BATTLE_TYPE_TRAINER = 1 << 3
BATTLE_TYPE_MULTI = 1 << 6
BATTLE_TYPE_INGAME_PARTNER = 1 << 22

#: `battlerPartyOrders[4][3]` sits at `*gBattleStruct + 0x60` (derived from `include/battle.h` and CONFIRMED live in
#: Step 0, S0-4: the two player arrays changed on a replacement and the two opponent arrays did not). ⛔ `gBattleStruct`
#: is a 4-byte POINTER: `read_symbol` does not follow it (KI-115), so the caller dereferences it first.
BPO_OFFSET = 0x60
BPO_STRIDE = 3

#: `ItemBattleUse.Healing.value` (`modules/items.py:76`). Compared by VALUE so this module never imports `modules.items`;
#: the gate's parity row DQ03 pins that it selects exactly what `_maybe_use_item`'s `is ItemBattleUse.Healing` selects.
HEALING_BATTLE_USE = "healing"

#: D3: the singles fields that describe ONE Pokémon. In a double each becomes a ledger PER (PID, species), swapped into
#: the instance around `_maybe_use_item` and back out in a `finally`. ⛔ `_item_uses`, `_index_space_flipped`,
#: `_items_ineffective` and `_r27_verdict` are deliberately NOT here: they stay PER BATTLE, shared by both battlers (the
#: cap of 4, the one retry, the disable and the key verdict bound the whole battle, never one Pokémon).
LEDGER_FIELDS = ("_hp_seen", "_worst_hit", "_hp_when_item_requested", "_status_when_item_requested",
                 "_item_qty_when_requested")


def new_ledger() -> dict:
    """A fresh per-Pokémon ledger: the values `StoryItemBattleStrategy.__init__` gives those five fields."""
    return {"_hp_seen": {}, "_worst_hit": 0, "_hp_when_item_requested": None, "_status_when_item_requested": None,
            "_item_qty_when_requested": None}


def mode(env) -> str:
    """The flag's value as OFF / OBSERVE / ON (DP01). EXACT match, no strip and no case folding: `" 1"` and `"ON"` are
    OFF, so a typo can never switch a behaviour change on."""
    value = None if env is None else env.get(FLAG)
    if value == "observe":
        return OBSERVE
    if value == "1":
        return ON
    return OFF


def in_scope(type_bits) -> bool:
    """D1: a TRAINER DOUBLE that is neither a MULTI nor has an IN-GAME PARTNER (DP02). Takes the raw `gBattleTypeFlags`
    int or a `BattleType` flag (its `.value`). The Space Center multi is out: there the bot controls battler 0 only and
    Steven's Pokémon sit in our party array (D1); wild doubles are out (the singles path never heals in a wild)."""
    bits = int(getattr(type_bits, "value", type_bits))
    if not bits & BATTLE_TYPE_TRAINER or not bits & BATTLE_TYPE_DOUBLE:
        return False
    return not bits & (BATTLE_TYPE_MULTI | BATTLE_TYPE_INGAME_PARTNER)


def decode_bpo(raw) -> list:
    """Three nibble-packed bytes → six party indexes, HIGH nibble first (`party_menu.c:5911-5913`; the same packing
    `BattleState.map_battle_party_index` walks). `02 13 45` → [0, 2, 1, 3, 4, 5] (DP03)."""
    out: list = []
    for byte in bytes(raw)[:3]:
        out += [byte >> 4, byte & 0xF]
    return out


def active_positions(order) -> tuple:
    """The two ACTIVE party indexes of a non-multi double: positions 0 and 1 ONLY (G2). ⚠ The tail carries switch
    history — a switch SWAPS positions (reviews M2/S13-P7, measured in S0-4) — so it is never treated as ascending."""
    return order[0], order[1]


def battler_party_index(raw8, g: int) -> int:
    """`gBattlerPartyIndexes[g]` from its RAW 8 bytes: the array is u16[4], so battler g sits at byte 2g (review M3). A
    byte-stride read (`raw8[g]`) gives battler 2's index as byte 2 = the LOW byte of battler 1 — an OPPONENT's slot."""
    raw = bytes(raw8)
    return int.from_bytes(raw[2 * g:2 * g + 2], "little")


def self_ok(target_index: int, g: int, raw8) -> bool:
    """D2/D4's SELF binding (review M5): the party index the item is aimed at IS battler g's own active Pokémon
    (DP05). It holds by construction when the strategy aims at `mon.party_index`; it is kept as defence in depth so a
    side mix-up can never heal the partner."""
    return target_index is not None and battler_party_index(raw8, g) == target_index


def guard_ok(intended_pid, menu_pid, slot, count) -> bool:
    """D4's identity guard (DP04): pass ONLY when the cursor's ACTUAL slot is a real party slot (review M10: Cancel is
    7, and 6-7 read past the party) AND the PID found there is the PID read before the bag opened. An unreadable input
    (None) is a mismatch, never a pass (D9: the guard fails CLOSED)."""
    if intended_pid is None or menu_pid is None or slot is None or count is None:
        return False
    if not 0 <= slot < count:
        return False
    return menu_pid == intended_pid


def ledger_key(pid: int, species) -> tuple:
    """D3: a ledger is keyed by IDENTITY — (PID, species) — never by a slot or a party index (rule 3)."""
    return pid, species


def hp_only(options) -> list:
    """The HP items (`parameter > 0`): the filter `_maybe_use_item` applies before `choose_healing_item`, mirrored by
    `heal_options`. A Full Restore / Max Potion (255) stays: it is an HP item. ⚠ It is NOT D10's mechanism any more:
    since SF-1 (2026-09-30) a double asks no cure policy at all — this filter left a Full Restore in the cure list."""
    return [opt for opt in options if opt[2] > 0]


def _is_healing(item) -> bool:
    use = getattr(item, "battle_use", None)
    return str(getattr(use, "value", use)) == HEALING_BATTLE_USE


def heal_options(bag_items, reserve_filter=None) -> list:
    """`observe`'s mirror of the HP options `_maybe_use_item` hands `choose_healing_item` (story_mode.py, the
    `medicine` → RULING 18 reserve → `parameter > 0` chain). DQ03 is the PARITY row that pins the two equal.
    `reserve_filter` fails UNLOCKED exactly as the strategy's does: a broken reserve must never change which items
    exist, so on an error the unfiltered list stands."""
    medicine = [(slot.item, slot.quantity, slot.item.parameter) for slot in bag_items if _is_healing(slot.item)]
    if reserve_filter is not None:
        try:
            medicine = reserve_filter(medicine)
        except Exception:  # noqa: BLE001 - fail UNLOCKED, the strategy's own rule (story_mode.py, RULING 18 filter)
            pass
    return hp_only(medicine)


def heal_fraction_kw(raw: str) -> dict:
    """`POKEBOT_HEAL_AT_FRACTION` exactly as `_maybe_use_item` parses it: unset or malformed ⇒ `{}` (the module default),
    else `{"heal_at_fraction": float}`."""
    if not raw:
        return {}
    try:
        return {"heal_at_fraction": float(raw)}
    except ValueError:  # a malformed knob keeps the shipped default, exactly as `_maybe_use_item` treats it
        return {}


def hp_decline_reason(current_hp: int, total_hp: int, options, *, worst_hit_taken: int = 0, uses_so_far: int = 0,
                      heal_at_fraction: float = HEAL_AT_FRACTION, max_uses: int = MAX_ITEM_USES_PER_BATTLE) -> str:
    """TELEMETRY ONLY (the `why=` of a `[DBLITEM-OBS]` row that would use nothing): which of `choose_healing_item`'s
    early exits fired, in its own order. It never decides anything."""
    if total_hp <= 0 or current_hp <= 0:
        return "fainted"
    if uses_so_far >= max_uses:
        return "cap"
    if current_hp / total_hp > heal_at_fraction:
        return "above_fraction"
    usable = [(item, qty, param) for item, qty, param in options if qty > 0 and param > 0]
    if not usable:
        return "no_hp_item"
    best = max(effective_heal(param, total_hp) for _item, _qty, param in usable)
    if worst_hit_taken and best < worst_hit_taken:
        return "losing_race"
    return "declined"
