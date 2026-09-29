"""Trainer identity + prize money, read the way the GAME computes them (design v2 step 5, TID/T1, 2026-09-29).

WHY: RULINGS 26/27 (money-making; healing items in key battles only) need to know WHICH trainer a battle is against and
what it pays. Nothing in this codebase read trainer identity before (`gym_tm_teach.boss_for_enemy_party` matches a
species set; it reads no ID). This module is READ-ONLY and log-only: `story_mode._t1_start/_t1_end` turn it into the
always-on `[TRAINER] start/end` lines (the 06:7902 precedent: telemetry, no flag).

Every constant below is cited to pret/pokeemerald and was verified against our ROM by an independent agent and the
orchestrator (`ai-research-notes/2026-09-29-t1trainer-PREDICTIONS.md`):
  * `struct Trainer` (`include/data.h:80-92`), 0x28 bytes: partyFlags +0x00, trainerClass +0x01, partySize +0x20,
    party pointer +0x24. `TRAINERS_COUNT = 855` (`include/constants/opponents.h:864`); sym `gTrainers` = 855 × 0x28.
  * TrainerMon structs (`include/data.h:35-65`): `u16 iv; u8 lvl; …` ⇒ level at +2; compiled stride 16 with a custom
    moveset (`F_TRAINER_PARTY_CUSTOM_MOVESET = 1 << 0`), else 8.
  * `gTrainerMoneyTable` (`src/battle_main.c:474-532`): `struct TrainerMoney {u8 classId; u8 value;}` compiles to a
    4-BYTE stride (56 entries, sym size 0xe0), terminated by `{0xFF, 5}` — an unlisted class pays 5.
  * The payout (`src/battle_script_commands.c:5578-5645`): `4 × lastMonLevel × moneyMultiplier × value`, where
    lastMonLevel = `party[partySize-1].lvl` of the ROM party; ×2 only for DOUBLE without TWO_OPPONENTS; a two-opponent
    battle SUMS A's and B's rewards. `moneyMultiplier` is 2 only after a player-side Amulet Coin holder SWITCHES IN
    (`battle_util.c:3294-3296`), not merely when one is held.
  * Defeated flags: `TRAINER_FLAGS_START = 0x500` (`include/constants/flags.h:1343`); set AFTER the battle
    (`SetBattledTrainersFlags`), so a read at battle START tells a first fight (per rematch tier: a rematch rewrites A
    to its own tier ID).
  * ⚠ `gTrainerBattleOpponent_B` is only written by the B param tables and only cleared by a sighting reset, so a stale
    B SURVIVES into later single battles: B is read ONLY when the battle type has `TwoOpponents`.
FAULT ARMS (production env reads; never set in a real run; gate `probe_trainer_identity_T1.py`):
  `POKEBOT_T1_FAULT_FIRSTMON=1` reads party[0]; `POKEBOT_T1_FAULT_STRIDE2=1` scans the money table in 2-byte steps.
"""

from __future__ import annotations

import os

TRAINERS_COUNT = 855
TRAINER_STRUCT_SIZE = 0x28
OFF_PARTY_FLAGS = 0x00
OFF_CLASS = 0x01
OFF_PARTY_SIZE = 0x20
OFF_PARTY_PTR = 0x24
F_TRAINER_PARTY_CUSTOM_MOVESET = 1 << 0
MON_LEVEL_OFFSET = 2
TRAINER_FLAGS_START = 0x500
MONEY_ENTRY_SIZE = 4
MONEY_TERMINATOR = 0xFF
UNLISTED_CLASS_VALUE = 5
CLASS_NAME_LEN = 13
CLASS_COUNT = 66
ROM_START, ROM_END = 0x0800_0000, 0x0A00_0000

#: IDENTITY constants only (`include/constants/trainers.h:288-353`, verified). Which of these are "key battles" is
#: design v2 step 6's decision (pending the user's Q3) — deliberately NOT encoded here.
TRAINER_CLASS = {
    "TEAM_AQUA": 0x03, "COOLTRAINER": 0x05, "TEAM_MAGMA": 0x09, "AQUA_ADMIN": 0x0B, "AQUA_LEADER": 0x0D,
    "RICH_BOY": 0x16, "ELITE_FOUR": 0x1F, "LEADER": 0x20, "YOUNGSTER": 0x25, "CHAMPION": 0x26, "MAGMA_ADMIN": 0x31,
    "RIVAL": 0x32, "MAGMA_LEADER": 0x35,
}


def _symbol(name: str) -> tuple[int, int]:
    from modules.game import get_symbol

    return get_symbol(name)


def _read_rom(address: int, size: int) -> bytes:
    from modules.context import context

    return context.emulator.read_bytes(address, size)


def trainer_row(trainer_id: int, read_rom=None, symbol=None) -> "bytes | None":
    """The 0x28-byte `gTrainers[trainer_id]` row, or None for an id outside 1..854 (row 855 is garbage in the ROM)."""
    if not isinstance(trainer_id, int) or not 0 < trainer_id < TRAINERS_COUNT:
        return None
    base, _size = (symbol or _symbol)("gTrainers")
    return (read_rom or _read_rom)(base + trainer_id * TRAINER_STRUCT_SIZE, TRAINER_STRUCT_SIZE)


def last_mon_level(trainer_id: int, read_rom=None, symbol=None) -> "int | None":
    """`party[partySize - 1].lvl` of the trainer's ROM party, exactly as `GetTrainerMoneyToGive` reads it — NOT from
    `gEnemyParty`, which caps each trainer at 3 mons in a two-opponent battle. None when unreadable."""
    row = trainer_row(trainer_id, read_rom, symbol)
    if row is None or len(row) < TRAINER_STRUCT_SIZE:
        return None
    flags, size = row[OFF_PARTY_FLAGS], row[OFF_PARTY_SIZE]
    ptr = int.from_bytes(row[OFF_PARTY_PTR:OFF_PARTY_PTR + 4], "little")
    if not 1 <= size <= 6 or not ROM_START <= ptr < ROM_END:
        return None
    stride = 16 if flags & F_TRAINER_PARTY_CUSTOM_MOVESET else 8
    index = 0 if os.environ.get("POKEBOT_T1_FAULT_FIRSTMON") == "1" else size - 1
    return (read_rom or _read_rom)(ptr + index * stride + MON_LEVEL_OFFSET, 1)[0]


def trainer_class(trainer_id: int, read_rom=None, symbol=None) -> "int | None":
    row = trainer_row(trainer_id, read_rom, symbol)
    return None if row is None else row[OFF_CLASS]


def money_value_for_class(table: bytes, trainer_class_id: int) -> int:
    """PURE: the class's money value from the raw `gTrainerMoneyTable` bytes — 4-byte entries up to the 0xFF
    terminator, an unlisted class pays the terminator's 5 (`battle_script_commands.c:5618-5622`). A 2-byte stride reads
    every padding pair as a class-0 entry worth 0; it differs from the truth ONLY for class 0 (verified over 0-254)."""
    step = 2 if os.environ.get("POKEBOT_T1_FAULT_STRIDE2") == "1" else MONEY_ENTRY_SIZE
    for i in range(0, len(table) - 1, step):
        cls, value = table[i], table[i + 1]
        if cls == MONEY_TERMINATOR or cls == trainer_class_id:
            return value
    return UNLISTED_CLASS_VALUE


def money_table(read_rom=None, symbol=None) -> bytes:
    base, size = (symbol or _symbol)("gTrainerMoneyTable")
    return (read_rom or _read_rom)(base, size)


def payout(value: int, last_level: int, double: bool, two_opponents: bool, multiplier: int = 1) -> int:
    """PURE: one trainer's reward, `GetTrainerMoneyToGive` (`battle_script_commands.c:5624-5629`). TWO_OPPONENTS is
    tested FIRST and gets no ×2 (each side is paid separately and summed by the caller); DOUBLE alone gets ×2."""
    base = 4 * last_level * multiplier * value
    if two_opponents:
        return base
    return base * 2 if double else base


def class_name(trainer_class_id: int, read_rom=None, symbol=None) -> str:
    """The ROM class name with spaces as `_` (37 of 66 names contain a space, which breaks `key=value` parsers). Not
    unique (0x00 and 0x32 both read "PkMn TRAINER"): the hex class id is the identity, this is only a label."""
    if not isinstance(trainer_class_id, int) or not 0 <= trainer_class_id < CLASS_COUNT:
        return "?"
    from modules.game import decode_string

    base, _size = (symbol or _symbol)("gTrainerClassNames")
    raw = (read_rom or _read_rom)(base + trainer_class_id * CLASS_NAME_LEN, CLASS_NAME_LEN)
    return "_".join(decode_string(raw).split()) or "?"


def read_opponent_trainers(two_opponents: bool) -> "tuple[int | None, int | None]":
    """(A, B) from RAM; B only in a TWO_OPPONENTS battle (a stale B survives into later single battles). An id outside
    1..854 (e.g. `TRAINER_SECRET_BASE` = 1024) is None."""
    from modules.memory import read_symbol, unpack_uint16

    def _valid(tid: int) -> "int | None":
        return tid if 0 < tid < TRAINERS_COUNT else None

    a = _valid(unpack_uint16(read_symbol("gTrainerBattleOpponent_A")))
    b = _valid(unpack_uint16(read_symbol("gTrainerBattleOpponent_B"))) if two_opponents else None
    return a, b


def is_first_fight(trainer_id: "int | None") -> "bool | None":
    """True when the trainer's defeated flag (0x500 + id) is unset — read at battle START (it is set after a win)."""
    if trainer_id is None:
        return None
    from modules.memory import get_event_flag_by_number

    return not get_event_flag_by_number(TRAINER_FLAGS_START + trainer_id)


def _clean(text: str) -> str:
    return "_".join(str(text).split())


def _map_field(value) -> str:
    """`g,n` — a map key tuple prints as `(g, n)`, and that SPACE broke the one-field-per-token rule (gate L1 caught it)."""
    if isinstance(value, (tuple, list)):
        return ",".join(str(v) for v in value)
    return _clean(value)


def heal_stock() -> str:
    """The raw bag's HEALING items (`battle_use is Healing`, the filter `_maybe_use_item` uses), as `Name:qty,…`, names
    without spaces; `-` when there are none. Raw bag on purpose — no RULING 18 reserve filter."""
    from modules.items import ItemBattleUse, get_item_bag

    items = [f"{_clean(s.item.name)}:{s.quantity}" for s in get_item_bag().items
             if s.item.battle_use is ItemBattleUse.Healing]
    return ",".join(items) or "-"


def enemy_alive() -> "int | None":
    """How many enemy mons have HP. 0 marks a POST-BATTLE scene that re-entered the battle hook (a trainer win that
    evolves a mon calls `on_battle_started` again with the beaten party still loaded); a real start has at least one.
    None when unreadable."""
    try:
        from modules.pokemon_party import get_opponent_party

        return sum(1 for m in (get_opponent_party() or [])
                   if m is not None and not getattr(m, "is_empty", False) and m.current_hp > 0)
    except Exception:  # noqa: BLE001 - unreadable ⇒ None, and the caller logs the battle as before (never hides one)
        return None


def snapshot(battle_type) -> dict:
    """Everything the `[TRAINER] start` line reports, read at battle start. `battle_type` is a `BattleType` flag set."""
    from modules.battle_state import BattleType
    from modules.player import get_player

    two = BattleType.TwoOpponents in battle_type
    double = BattleType.Double in battle_type
    a, b = read_opponent_trainers(two)
    table = money_table()
    sides = []
    for tid in (a, b):
        if tid is None:
            continue
        cls = trainer_class(tid)
        lvl = last_mon_level(tid)
        value = money_value_for_class(table, cls) if cls is not None else None
        base = payout(value, lvl, double, two) if value is not None and lvl is not None else None
        sides.append({"id": tid, "cls": cls, "name": class_name(cls) if cls is not None else "?", "value": value,
                      "lvl": lvl, "base": base, "first": is_first_fight(tid)})
    total = sum(s["base"] for s in sides) if sides and all(s["base"] is not None for s in sides) else None
    return {"sides": sides, "base": total, "double": double, "two": two, "money": get_player().money,
            "heal": heal_stock()}


def _joined(sides: list, key: str) -> str:
    """One field across the sides, `+`-joined (`opp=A+B`); `?` for an unreadable value."""
    return "+".join("?" if s[key] is None else str(s[key]) for s in sides)


def _side_fields(ctx: dict) -> str:
    sides = ctx["sides"]
    if not sides:
        return "opp=? class=? value=? lvl_last=? first=?"
    classes = "+".join("?" if s["cls"] is None else f"0x{s['cls']:02X}({s['name']})" for s in sides)
    return (f"opp={_joined(sides, 'id')} class={classes} value={_joined(sides, 'value')} "
            f"lvl_last={_joined(sides, 'lvl')} first={_joined(sides, 'first')}")


def format_start(ctx: dict) -> str:
    return (f"start {_side_fields(ctx)} base={ctx['base'] if ctx['base'] is not None else '?'} "
            f"double={ctx['double']} two={ctx['two']} money={ctx['money']} heal_stock={ctx['heal']} "
            f"map={_map_field(ctx.get('map', '?'))} enemy_alive={ctx.get('enemy_alive', '?')}")


def format_end(ctx: dict, outcome, money_after: int, heal_after: str) -> str:
    """The `[TRAINER] end` line. `res=`, NEVER `outcome=` (two batch parsers count `outcome=BattleOutcome`)."""
    delta = money_after - ctx["money"]
    base = ctx["base"]
    if base:
        mult = delta // base if delta % base == 0 else round(delta / base, 2)
    else:
        mult = "?"
    res = getattr(outcome, "name", outcome)
    return (f"end {_side_fields(ctx)} base={base if base is not None else '?'} res={_clean(res)} "
            f"money={ctx['money']}->{money_after} delta={delta} mult={mult} heal_stock={heal_after} "
            f"map={_map_field(ctx.get('map', '?'))}")
