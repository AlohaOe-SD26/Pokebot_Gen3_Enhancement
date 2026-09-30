"""Design v2 step 11 (M1b): the `[DMGAUDIT]` RAW reads — OBSERVE-ONLY, behind `POKEBOT_R25_DMGAUDIT=1`.

WHY. Step 12 (weaken-to-catch) will trust `calculate_move_damage_range`'s crit maximum not to KO a wanted Pokémon, so
step 11 measures how far the real damage strays from it, live. The design
(`ai-research-notes/2026-09-30-dmgcalc11-DESIGN.md` F3) puts only RAW reads here, plus the live prediction for the
move the GAME records as chosen; every verdict is computed OFFLINE by `tools/story-dev/audit_damage_calc.py`, which is
pure and gated, so a classifier bug costs a re-audit, never a re-batch. The line format is
`ai-research-notes/2026-09-30-dmgcalc11-recon/m1_line_format.md` (v=1).

⛔ THE CONTRACT (the same-HEAD inertness proof rests on each one):
- every public function reads the flag on EVERY call (the design's third stated exception to v2's per-run read:
  the battle-action module has no StoryMode, and the harness drivers bypass StoryMode);
- no yield, no button press, and NO `get_battle_state()` (KI-108: a second cached call in a frame can hand a stale party
  order to a later caller in that frame); the prediction reuses the handler's own `battle_state` object;
- nothing here raises: a failure becomes ONE `ERR` line;
- with the flag unset, nothing is read and nothing is logged.
"""
import os

FLAG = "POKEBOT_R25_DMGAUDIT"
#: M1b-FAULT: `bide` reports slot 0's value in position 1 (the reader pointed at the wrong battler). Graded only.
FAULT_BIDE0 = "POKEBOT_R25_FAULT_DMGAUDIT_BIDE0"
_SELECTION_STATES = ("HandleTurnActionSelectionState", "sub_8012324")
_EWRAM = (0x02000000, 0x02040000)
#: A BEFORE waiting for its AFTER. Module level on purpose: the selection handler is re-entered within one selection,
#: and a function local would die across those re-entries (`battle_action_selection.py`'s own KI-93 notes).
_pending = False


def _on() -> bool:
    return os.environ.get(FLAG, "").strip() == "1"


def _log(message: str) -> None:
    from modules import debug_logger

    debug_logger.event(message, category="DMGAUDIT")


def _err(where: str, error: BaseException) -> None:
    try:
        _log(f"ERR v=1 where={where} err={type(error).__name__}")
    except Exception:  # noqa: BLE001 - telemetry must never affect a battle
        pass


def _raw(*, flash_fire: bool) -> str:
    """The RAW fields (m1_line_format.md), by pure `read_symbol` reads."""
    from modules.context import context
    from modules.memory import read_symbol, unpack_uint16, unpack_uint32

    bide = read_symbol("gBideDmg", size=0x10)
    bide4 = [int.from_bytes(bide[i * 4:i * 4 + 4], "little", signed=True) for i in range(4)]
    if os.environ.get(FAULT_BIDE0, "").strip() == "1":
        bide4[1] = bide4[0]
    moves = read_symbol("gChosenMoveByBattler", size=8)
    sides = read_symbol("gSideStatuses", size=4)
    status3 = read_symbol("gStatuses3", size=8)
    disable = read_symbol("gDisableStructs", size=0x38)
    mons = read_symbol("gBattleMons", size=0xB0)
    ff = "null"
    if flash_fire:
        resources = unpack_uint32(read_symbol("gBattleResources", size=4))
        if _EWRAM[0] <= resources < _EWRAM[1]:
            flags_ptr = unpack_uint32(context.emulator.read_bytes(resources + 4, 4))
            if _EWRAM[0] <= flags_ptr < _EWRAM[1]:
                ff = ",".join(str(unpack_uint32(context.emulator.read_bytes(flags_ptr + 4 * b, 4))) for b in range(2))
    return " ".join((
        f"t={read_symbol('gBattleResults', offset=0x13, size=1)[0]}",
        f"out={read_symbol('gBattleOutcome', size=1)[0]}",
        f"flags={unpack_uint32(read_symbol('gBattleTypeFlags', size=4)):08x}",
        "act=" + ",".join(str(x) for x in read_symbol("gChosenActionByBattler", size=4)),
        "mv=" + ",".join(str(unpack_uint16(moves[i * 2:i * 2 + 2])) for i in range(4)),
        "bide=" + ",".join(str(x) for x in bide4),
        f"weather={unpack_uint16(read_symbol('gBattleWeather', size=2))}",
        "side=" + ",".join(str(unpack_uint16(sides[i * 2:i * 2 + 2])) for i in range(2)),
        "s3=" + ",".join(f"{unpack_uint32(status3[i * 4:i * 4 + 4]):08x}" for i in range(2)),
        "dis=" + ",".join(disable[i * 0x1C:(i + 1) * 0x1C].hex() for i in range(2)),
        "mons=" + ",".join(mons[i * 0x58:(i + 1) * 0x58].hex() for i in range(2)),
        f"ff={ff}",
    ))


def _party() -> str:
    from modules.memory import read_symbol, unpack_uint16, unpack_uint32

    party = read_symbol("gEnemyParty", size=600)
    return "party=" + ",".join(
        f"{unpack_uint32(party[i * 100:i * 100 + 4]):08x}:{unpack_uint16(party[i * 100 + 0x56:i * 100 + 0x58])}"
        for i in range(6))


def _badges() -> int:
    from modules.memory import get_event_flag

    return sum(1 << i for i in range(8) if get_event_flag(f"BADGE0{i + 1}_GET"))


def _prediction(battle_state) -> str:
    """`pred=` and `eff=` for the move the GAME records as our chosen move (never the strategy's index)."""
    from modules.memory import read_symbol, unpack_uint16

    action = read_symbol("gChosenActionByBattler", size=1)[0]
    move_id = unpack_uint16(read_symbol("gChosenMoveByBattler", size=2))
    if action != 0 or move_id == 0:
        return "pred=none base=none eff=-"
    from modules.battle_strategies._util import BattleStrategyUtil
    from modules.pokemon import get_move_by_index

    move = get_move_by_index(move_id)
    try:
        util = BattleStrategyUtil(battle_state)
        attacker, defender = battle_state.own_side.left_battler, battle_state.opponent.left_battler
        if attacker is None or defender is None:
            # an absent left battler (a fainted slot in a DOUBLE, measured in the smoke run): nothing to predict
            return f"pred=err:Absent base=none eff={move.effect}"
        plain = util.calculate_move_damage_range(move, attacker, defender)
        crit = util.calculate_move_damage_range(move, attacker, defender, is_critical_hit=True)
        pred = f"{plain.min},{plain.max},{crit.min},{crit.max}"
        # the calculator's own BASE term (non-crit, crit), so the offline audit can replay the decomp-ordered port from
        # it: a live check of the ORACLE against the game's real damage (the design review's SR-7)
        base = (f"{util._calculate_base_move_damage(move, attacker, defender, False)},"
                f"{util._calculate_base_move_damage(move, attacker, defender, True)}")
    except Exception as error:  # noqa: BLE001 - a prediction that raises is a result to log, not a battle to break
        pred = f"err:{type(error).__name__}"
        base = "none"
    return f"pred={pred} base={base} eff={move.effect}"


def on_battle_start() -> None:
    """`battle_handler.handle_battle`, before its loop: the control line; any stale BEFORE is dropped."""
    global _pending
    if not _on():
        return
    _pending = False
    try:
        _log("CTL v=1")
    except Exception as error:  # noqa: BLE001 - telemetry must never affect a battle
        _err("ctl", error)


def on_selection_entry() -> None:
    """The first selection entry after a BEFORE: its AFTER (`kind=entry`)."""
    global _pending
    if not _on() or not _pending:
        return
    _pending = False
    try:
        _log(f"AFTER v=1 kind=entry {_raw(flash_fire=True)} {_party()}")
    except Exception as error:  # noqa: BLE001 - telemetry must never affect a battle
        _err("after-entry", error)


def on_selection_exit(battle_state) -> None:
    """The selection handler's loop fall-through: a BEFORE, only once the game has LEFT the selection states (choices
    final, no action run yet, so no HP has changed)."""
    global _pending
    if not _on():
        return
    try:
        from modules.battle_state import battle_is_active, get_main_battle_callback

        if not battle_is_active() or get_main_battle_callback() in _SELECTION_STATES:
            return
        _log(f"BEFORE v=1 {_raw(flash_fire=True)} badges={_badges()} {_prediction(battle_state)}")
        _pending = True
    except Exception as error:  # noqa: BLE001 - telemetry must never affect a battle
        _err("before", error)


def on_battle_end() -> None:
    """`battle_handler.handle_battle`, after its loop: the AFTER of a battle's last turn (`kind=end`). ⛔ No Flash Fire
    read: `gBattleResources` is freed by then (the Step-0 reads: NULL at every battle end)."""
    global _pending
    if not _on() or not _pending:
        return
    _pending = False
    try:
        _log(f"AFTER v=1 kind=end {_raw(flash_fire=False)} {_party()}")
    except Exception as error:  # noqa: BLE001 - telemetry must never affect a battle
        _err("after-end", error)
