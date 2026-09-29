r"""GATE (no emulator) — design v2 step 5 (TID/T1): trainer identity + prize money, read the way the GAME computes them,
and the always-on `[TRAINER] start/end` lines that can never change a battle (2026-09-29).

WHY: RULINGS 26/27 need WHICH trainer a battle is against and what it pays; nothing read trainer identity before.
Every number is from pret/pokeemerald and our ROM (`ai-research-notes/2026-09-29-t1trainer-PREDICTIONS.md`). The ROM is
read straight from the `.gba` file (symbols via `set_rom`), so this gate needs no emulator.
  S1  constants equal the decomp; sym sizes: `gTrainers` = 855 × 0x28, `gTrainerMoneyTable` = 56 × 4.
  R1  ROM rows: 265 ROXANNE_1 class 0x20, 11 MARCEL 0x05, 261 SIDNEY 0x1F.
  R2  `last_mon_level`: 265 → 15 (levels 12/12/15, stride 16) and 116 (a Magma Grunt, stride 8) → 30 (26/28/30).
  R3  money values: LEADER 25, YOUNGSTER 4, RICH_BOY 50, an unlisted class (0x01) 5, and CLASS 0 → 5.
  P1  payout rows: ROXANNE_1 ₽1,500; CALVIN_1 ₽80; DAWSON ₽1,600; a DOUBLE doubles; TWO_OPPONENTS gets no ×2.
  B1  `read_opponent_trainers`: B is read ONLY with TwoOpponents (a stale B survives into single battles).
  W1  `_t1_start`: a Wally-tutorial battle type (encounter None, no Trainer bit) makes NO snapshot and NO line;
      W2 a wild battle makes none; W3 a trainer battle makes one snapshot and one `start` line;
      W4 a POST-BATTLE scene re-entering the hook (0 enemy mons alive — measured live: a trainer win that evolves a mon
      calls `on_battle_started` again at f150064) makes NO snapshot and one `skip reason=no_enemy_alive` line;
      W5 an unreadable snapshot (it raises) is LOGGED as `start unreadable`, with no context and no raise.
  E1  `on_battle_ended` with an OPEN `_t1_ctx` and a RAISING logger still counts the defeat (T1 cannot skip it).
  L1  the end line uses `res=` (never `outcome=`) and no field value contains a space.
  A1  the three fault envs are registered in 29.
FAULT ARMS (the unmutated subject passes first; each must turn EXACTLY its own set red):
  F1  `POKEBOT_T1_FAULT_FIRSTMON=1` (production): reads party[0] → {R2}.
  F2  `POKEBOT_T1_FAULT_STRIDE2=1` (production): 2-byte money stride → {R3} (only the class-0 row differs).
  F3  `POKEBOT_T1_FAULT_WILDTOO=1` (production): wild battles snapshot → {W2}.
  F4  a stand-in `_t1_end` that RAISES → {E1} (the placement before the Lost block is why the guard matters).
  F5  a source mutant reading B whatever the battle type → {B1}.
  F6  a source mutant printing `outcome=` → {L1}.
  F7  a `story_mode` source mutant without the post-battle guard → {W4} (it logged a phantom `delta=0 mult=0` pair).
  F8  a `story_mode` source mutant whose `_t1_start` guard misses the snapshot's error → {W5} (added after the review:
      "neither helper can raise" had a case for `_t1_end` only).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_trainer_identity_T1.py
"""
from __future__ import annotations

import contextlib
import io
import os
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

ROM_PATH = ROOT / "sandbox-pokebot" / "roms" / "Pokemon - Emerald Version (USA, Europe).gba"
TI_PATH = ROOT / "sandbox-pokebot" / "modules" / "story" / "trainer_identity.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FAULTS = ("POKEBOT_T1_FAULT_FIRSTMON", "POKEBOT_T1_FAULT_STRIDE2", "POKEBOT_T1_FAULT_WILDTOO")
failures: list = []

from modules.game import get_symbol, set_rom  # noqa: E402
from modules.roms import load_rom_data  # noqa: E402

set_rom(load_rom_data(ROM_PATH))
ROM = ROM_PATH.read_bytes()

import modules.battle_state as BST  # noqa: E402
import modules.story.trainer_identity as TI  # noqa: E402
import plugins.custom_modes.story_mode as SM  # noqa: E402
from modules.battle_state import BattleType  # noqa: E402
from modules.battle_state import BattleOutcome  # noqa: E402


def read_rom(address: int, size: int) -> bytes:
    off = address - 0x0800_0000
    return ROM[off:off + size]


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


@contextlib.contextmanager
def env(**kv):
    saved = {k: os.environ.get(k) for k in FAULTS}
    try:
        for k in FAULTS:
            os.environ.pop(k, None)
        os.environ.update(kv)
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class Patch:
    def __init__(self, mod, **attrs):
        self.mod, self.attrs, self.saved = mod, attrs, {}

    def __enter__(self):
        for k, v in self.attrs.items():
            self.saved[k] = getattr(self.mod, k)
            setattr(self.mod, k, v)

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            setattr(self.mod, k, v)


def _boom(*_a, **_k):
    raise RuntimeError("telemetry exploded")


SAMPLE_CTX = {"sides": [{"id": 265, "cls": 0x20, "name": "LEADER", "value": 25, "lvl": 15, "base": 1500,
                         "first": True}], "base": 1500, "double": False, "two": False, "money": 8628,
              "heal": "Super_Potion:2", "map": (11, 3)}


def cases(ti=TI, sm=SM, sink=None) -> set:
    red: set = set()

    def rec(tag, ok, msg):
        if not ok:
            red.add(tag)
        check(ok, f"{tag} {msg}", sink)

    # R1-R3 — the ROM rows.
    got = {tid: ti.trainer_class(tid, read_rom) for tid in (265, 11, 261)}
    rec("R1", got == {265: 0x20, 11: 0x05, 261: 0x1F}, f"classes 265/11/261 = {got} (want 0x20/0x05/0x1F)")
    lv = (ti.last_mon_level(265, read_rom), ti.last_mon_level(116, read_rom))
    rec("R2", lv == (15, 30), f"last_mon_level 265 (stride 16) / 116 (stride 8) = {lv} (want 15, 30)")
    table = ti.money_table(read_rom)
    vals = {c: ti.money_value_for_class(table, c) for c in (0x20, 0x25, 0x16, 0x01, 0x00)}
    rec("R3", vals == {0x20: 25, 0x25: 4, 0x16: 50, 0x01: 5, 0x00: 5},
        f"money LEADER/YOUNGSTER/RICH_BOY/unlisted/class-0 = {vals} (want 25/4/50/5/5)")
    # P1 — the formula.
    rows = (ti.payout(25, 15, False, False), ti.payout(4, 5, False, False), ti.payout(50, 8, False, False),
            ti.payout(25, 15, True, False), ti.payout(25, 15, True, True))
    rec("P1", rows == (1500, 80, 1600, 3000, 1500), f"payouts {rows} (want 1500, 80, 1600, 3000 double, 1500 two-opp)")
    # B1 — B only with TwoOpponents.
    import modules.memory as MEM

    fake = {"gTrainerBattleOpponent_A": (265).to_bytes(2, "little"),
            "gTrainerBattleOpponent_B": (261).to_bytes(2, "little")}
    with Patch(MEM, read_symbol=lambda name, offset=0, size=0: fake[name]):
        b1 = (ti.read_opponent_trainers(False), ti.read_opponent_trainers(True))
    rec("B1", b1 == ((265, None), (265, 261)), f"(single, two-opponent) = {b1} (want ((265, None), (265, 261)))")
    # W1-W3 — which battles snapshot. `snapshot` is stubbed so no emulator is needed.
    logs: list = []

    def run_start(battle_type, encounter, alive=1, snap=None):
        stub = types.SimpleNamespace(_location_key=lambda: (0, 31))
        logs.clear()
        # `_t1_start` imports the REAL module, so its `snapshot`/`enemy_alive` are the ones to stub (not a mutant's).
        with Patch(BST, get_battle_type=lambda: battle_type), \
                Patch(TI, snapshot=snap or (lambda bt: dict(SAMPLE_CTX)), enemy_alive=lambda: alive), \
                Patch(sm, _log_story_event=lambda text, cat="": logs.append((cat, text))):
            sm._t1_start(stub, encounter)
        return getattr(stub, "_t1_ctx", None), list(logs)

    ctx, lines = run_start(BattleType.WallyTutorial, None)
    rec("W1", ctx is None and not lines, f"Wally's tutorial (encounter None, no Trainer bit): ctx={ctx is not None} "
                                         f"lines={len(lines)} (want none)")
    ctx, lines = run_start(BattleType(0), types.SimpleNamespace(pokemon=None))
    rec("W2", ctx is None and not lines, f"a wild battle: ctx={ctx is not None} lines={len(lines)} (want none)")
    ctx, lines = run_start(BattleType.Trainer, None)
    rec("W3", ctx is not None and len(lines) == 1 and lines[0][0] == "TRAINER" and lines[0][1].startswith("start "),
        f"a trainer battle: ctx={ctx is not None} lines={[c for c, _ in lines]} (want one TRAINER start line)")
    ctx, lines = run_start(BattleType.Trainer, None, alive=0)
    rec("W4", ctx is None and len(lines) == 1 and "skip reason=no_enemy_alive" in lines[0][1],
        f"a post-battle scene re-entering the hook (0 enemy alive): ctx={ctx is not None} "
        f"lines={[t[:40] for _, t in lines]} (want no context and one skip line — measured live at f150064)")
    # W5 — `_t1_start` cannot raise: an unreadable snapshot is LOGGED, the hook continues (review finding 2026-09-29).
    raised = None
    try:
        ctx, lines = run_start(BattleType.Trainer, None, snap=_boom)
    except Exception as error:  # noqa: BLE001 - the gate reports it
        raised, ctx, lines = error, None, []
    rec("W5", raised is None and ctx is None and len(lines) == 1 and lines[0][1].startswith("start unreadable"),
        f"a raising snapshot: raised={raised!r} ctx={ctx is not None} lines={[t[:30] for _, t in lines]} "
        f"(want no raise, no context, one 'start unreadable' line)")
    # E1 — an open context + a raising logger cannot skip defeat counting.
    stub = types.SimpleNamespace(_location_key=lambda: (0, 8), _defeat_counts={}, _last_defeat_key=None, _loss_seq=0,
                                 _loss_ko_history={}, _catch_ctx=None, _boss_battle=None, _t1_ctx=dict(SAMPLE_CTX))
    raised = None
    with Patch(sm, _log_story_event=_boom), contextlib.redirect_stdout(io.StringIO()):
        try:
            sm.StoryMode.on_battle_ended(stub, BattleOutcome.Lost)
        except Exception as error:  # noqa: BLE001 - the gate reports it
            raised = error
    rec("E1", raised is None and stub._defeat_counts.get((0, 8)) == 1,
        f"an open [TRAINER] context + a raising logger: raised={raised!r}, defeats={stub._defeat_counts} (want 1)")
    # L1 — the end line's shape.
    line = ti.format_end(dict(SAMPLE_CTX), BattleOutcome.Won, 10128, "Super_Potion:2")
    fields = line.split(" ")[1:]
    rec("L1", "res=Won" in line and "outcome=" not in line and all(f.count("=") == 1 for f in fields)
        and "delta=1500" in line and "mult=1" in line,
        f"end line uses res=, one key=value per token, delta 1500 mult 1 ({line[:110]}…)")
    return red


def mutant_module(src: str, name: str):
    mod = types.ModuleType(name)
    mod.__file__ = str(TI_PATH)
    exec(compile(src, name, "exec"), mod.__dict__)
    return mod


def main() -> int:
    print("S — constants and symbol sizes")
    consts = (TI.TRAINERS_COUNT, TI.TRAINER_STRUCT_SIZE, TI.OFF_CLASS, TI.OFF_PARTY_SIZE, TI.OFF_PARTY_PTR,
              TI.TRAINER_FLAGS_START, TI.MONEY_ENTRY_SIZE, TI.UNLISTED_CLASS_VALUE)
    sizes = (get_symbol("gTrainers")[1], get_symbol("gTrainerMoneyTable")[1])
    check(consts == (855, 0x28, 0x01, 0x20, 0x24, 0x500, 4, 5) and sizes == (855 * 0x28, 56 * 4)
          and TI.TRAINER_CLASS["LEADER"] == 0x20 and TI.TRAINER_CLASS["ELITE_FOUR"] == 0x1F
          and TI.TRAINER_CLASS["RIVAL"] == 0x32 and TI.TRAINER_CLASS["MAGMA_LEADER"] == 0x35,
          f"S1 constants {consts} and sym sizes {sizes} equal the decomp")
    print("R/P/B/W/E/L — cases")
    with env():
        cases()
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(all(f in reg for f in FAULTS), "A1 the three fault envs are registered in 29")

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    for tag, fault, want in (("F1", "POKEBOT_T1_FAULT_FIRSTMON", {"R2"}), ("F2", "POKEBOT_T1_FAULT_STRIDE2", {"R3"}),
                             ("F3", "POKEBOT_T1_FAULT_WILDTOO", {"W2"})):
        with env(**{fault: "1"}):
            red = cases(TI, SM, [])
        check(base_ok and red == want, f"{tag} {fault}=1 turns exactly {sorted(want)} red (red: {sorted(red)})")
    with env(), Patch(SM, _t1_end=_boom):
        red = cases(TI, SM, [])
    check(base_ok and red == {"E1"}, f"F4 a raising _t1_end turns exactly ['E1'] red (red: {sorted(red)})")
    src = TI_PATH.read_text(encoding="utf-8")
    anchor = 'read_symbol("gTrainerBattleOpponent_B"))) if two_opponents else None'
    m5 = src.replace(anchor, 'read_symbol("gTrainerBattleOpponent_B")))', 1) if src.count(anchor) == 1 else None
    with env():
        red = cases(mutant_module(m5, "ti_f5"), SM, []) if m5 else {"(anchor missing)"}
    check(base_ok and red == {"B1"}, f"F5 B read whatever the battle type turns exactly ['B1'] red (red: {sorted(red)})")
    anchor6 = 'f"end {_side_fields(ctx)} base={base if base is not None else \'?\'} res={_clean(res)} "'
    m6 = (src.replace(anchor6, 'f"end {_side_fields(ctx)} base={base if base is not None else \'?\'} outcome={res} "', 1)
          if src.count(anchor6) == 1 else None)
    with env():
        red = cases(mutant_module(m6, "ti_f6"), SM, []) if m6 else {"(anchor missing)"}
    check(base_ok and red == {"L1"}, f"F6 an outcome= end line turns exactly ['L1'] red (red: {sorted(red)})")
    sm_path = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
    sm_src = sm_path.read_text(encoding="utf-8")
    guard = "        if alive == 0:\n"
    guard = guard.replace("\n", "\r\n") if "\r\n" in sm_src else guard
    if sm_src.count(guard) == 1:
        sm_mut = types.ModuleType("sm_f7")
        sm_mut.__file__ = str(sm_path)
        exec(compile(sm_src.replace(guard, guard.replace("alive == 0", "False"), 1), "sm_f7", "exec"), sm_mut.__dict__)
        with env():
            red = cases(TI, sm_mut, [])
    else:
        red = {"(anchor missing)"}
    check(base_ok and red == {"W4"}, f"F7 a _t1_start without the post-battle guard turns exactly ['W4'] red "
                                     f"(red: {sorted(red)})")
    handler = '        _log_story_event(_ti.format_start(ctx), "TRAINER")\n    except Exception as exc:'
    handler = handler.replace("\n", "\r\n") if "\r\n" in sm_src else handler
    if sm_src.count(handler) == 1:
        sm_mut8 = types.ModuleType("sm_f8")
        sm_mut8.__file__ = str(sm_path)
        exec(compile(sm_src.replace(handler, handler.replace("except Exception as exc:",
                                                             "except ZeroDivisionError as exc:"), 1),
                     "sm_f8", "exec"), sm_mut8.__dict__)
        with env():
            red = cases(TI, sm_mut8, [])
    else:
        red = {"(anchor missing)"}
    check(base_ok and red == {"W5"}, f"F8 a _t1_start whose guard misses the snapshot's error turns exactly ['W5'] red "
                                     f"(red: {sorted(red)})")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — trainer identity and prize money read as the game does; the [TRAINER] lines cannot change a battle")
    return 0


if __name__ == "__main__":
    sys.exit(main())
