r"""GATE (no emulator) — USER RULING 27, design v2 step 6 (KB): with `POKEBOT_R27_KEYITEMS=1`, `StoryItemBattleStrategy`
uses healing items ONLY against a KEY trainer class; OFF is byte-identical; the gate fails OPEN (2026-09-29).

WHY: the user ruled (`06`, RULING 27): *"use healing items during battles (gym leaders, story "bosses" and elite 4
only)"*. `_maybe_use_item` used them in EVERY single trainer battle. The key set (`trainer_identity.
KEY_TRAINER_CLASSES`) is a proposal pending the user's Q3, so it is data the answer can change.
  V1  the PURE verdict: OFF allows everything; ON allows each of the 8 key classes; ON refuses 0x05/0x09/0x03/0x02;
      an unreadable id or class, or no side, is ALLOWED (fail open); two sides allow if ANY side is key.
  V2  boss reconciliation (from the ROM, by trainer ID): every `_prepare_for_fight` opponent and every named story
      boss reads a KEY class — Roxanne-Juan (265-272), the Rustboro/Route 110 rival fights, Wally, Maxie, Archie,
      Tabitha, Matt, Shelly, the Elite Four, Wallace — and Marcel (11) and a hideout grunt (717) do NOT.
  I1  the REAL `_maybe_use_item` (gate #60's fakes; the opponent reader stubbed): at 10/100 HP with a Hyper Potion,
      OFF uses it; ON + a non-key class (0x05) returns None; ON + a key class (0x20) uses it.
  I2  OFF does ZERO opponent reads (the reader raises if touched) and logs no `[KEYBATTLE]` line.
  I3  ON reads the opponent ONCE per battle (two turns → one read, one `[KEYBATTLE]` line).
  I4  ON + `POKEBOT_R27_FAULT_RAISE=1` (production arm): the item STILL fires and the line reads `FAIL_OPEN` — a
      recovery arm, it must PASS.
  A1  AST: in `_maybe_use_item` the gate call sits AFTER the Trainer-return `if` and BEFORE the `medicine =`
      assignment; the method has exactly one os import, `import os as _os`, as its first statement.
  A2  both flags and both fault envs are registered in 29.
FAULT ARMS (the unmutated subject passes first; each must turn EXACTLY its own set red):
  F1  `POKEBOT_R27_FAULT_ALLORDINARY=1` (production): every class reads 0x05 → {I1} (the key row is refused).
  F2  a mutant verdict that ALWAYS allows → {V1, I1}.
  F3  a mutant verdict that fails CLOSED on an unreadable side → {V1}.
  F4  a mutant with the gate call only in a COMMENT → {I1, I3, I4, A1} (with no gate, the RAISE arm has nothing to
      fail open FROM, so I4's FAIL_OPEN line never appears).
  F5  a mutant with RIVAL (0x32) dropped from the key set → {V1, V2}.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_key_battle_items.py
"""
from __future__ import annotations

import ast
import contextlib
import io
import os
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
TI_PATH = ROOT / "sandbox-pokebot" / "modules" / "story" / "trainer_identity.py"
ROM_PATH = ROOT / "sandbox-pokebot" / "roms" / "Pokemon - Emerald Version (USA, Europe).gba"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FLAG = "POKEBOT_R27_KEYITEMS"
FAULTS = ("POKEBOT_R27_FAULT_RAISE", "POKEBOT_R27_FAULT_ALLORDINARY")
failures: list = []

from modules.game import set_rom  # noqa: E402
from modules.roms import load_rom_data  # noqa: E402

set_rom(load_rom_data(ROM_PATH))
ROM = ROM_PATH.read_bytes()


def read_rom(address: int, size: int) -> bytes:
    return ROM[address - 0x0800_0000:address - 0x0800_0000 + size]


# --- gate #60's fakes (the strategy's base __init__ reads get_party(); patch BEFORE importing it) ---
class FakeItem:
    def __init__(self, name, parameter, battle_use):
        self.name, self.parameter, self.battle_use = name, parameter, battle_use


class FakeSlot:
    def __init__(self, item, quantity):
        self.item, self.quantity = item, quantity


class FakeBag:
    def __init__(self, slots):
        self.items = slots


class FakeStatus:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"StatusCondition.{self.name}"


class FakeMon:
    def __init__(self, party_index=0, hp=100, total=100):
        self.party_index, self.current_hp, self.total_hp = party_index, hp, total
        self.status_permanent = FakeStatus("Healthy")
        self.is_egg = False
        self.species = type("S", (), {"name": "Testmon"})()


class FakeParty(list):
    @property
    def first_non_fainted(self):
        return next((m for m in self if m is not None and m.current_hp > 0), None)


import modules.items as ITEMS  # noqa: E402
import modules.pokemon_party as PARTY  # noqa: E402
from modules.battle_state import BattleType  # noqa: E402
from modules.items import ItemBattleUse  # noqa: E402

_roster = FakeParty([FakeMon(0), FakeMon(1), FakeMon(2)])
for _i, _m in enumerate(_roster):
    _m.index = _i
PARTY.get_party = lambda: _roster
HYPER = FakeItem("Hyper Potion", 200, ItemBattleUse.Healing)
ITEMS.get_item_bag = lambda: FakeBag([FakeSlot(HYPER, 5)])

import modules.story.trainer_identity as TI  # noqa: E402
import plugins.custom_modes.story_mode as SM  # noqa: E402


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


@contextlib.contextmanager
def env(**kv):
    names = (FLAG,) + FAULTS
    saved = {k: os.environ.get(k) for k in names}
    try:
        for k in names:
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


class FakeBattleState:
    def __init__(self, hp=10, total=100):
        self.own_side = types.SimpleNamespace(left_battler=FakeMon(0, hp, total))
        self.type = {BattleType.Trainer}


# Trainer IDs verified on the ROM (design v2 step 6 audit; decomp `opponents.h`).
KEY_BOSS_IDS = {
    "leaders Roxanne-Juan": [265, 266, 267, 268, 269, 270, 271, 272],
    "rival (Rustboro)": [592, 593, 599, 600, 768, 769], "rival (Route 110)": [521, 524, 527, 530, 533, 536],
    "Wally": [656, 519, 657, 658, 659, 660], "Maxie": [601, 602, 734], "Archie": [34],
    "Tabitha": [514, 597, 732], "Matt": [30], "Shelly": [32, 33], "Elite Four": [261, 262, 263, 264],
    "Wallace": [335],
}
NON_KEY_IDS = {"Marcel (COOLTRAINER)": 11, "a hideout grunt (TEAM_MAGMA)": 717}


def cases(ti=TI, sm=SM, sink=None) -> set:
    red: set = set()

    def rec(tag, ok, msg):
        if not ok:
            red.add(tag)
        check(ok, f"{tag} {msg}", sink)

    kv = ti.key_battle_verdict
    v1 = [
        all(kv(False, [(1, c)])[0] for c in (0x05, 0x09, 0x20)),
        all(kv(True, [(1, c)])[0] for c in (0x20, 0x1F, 0x26, 0x32, 0x35, 0x0D, 0x31, 0x0B)),
        not any(kv(True, [(1, c)])[0] for c in (0x05, 0x09, 0x03, 0x02)),
        kv(True, [(None, None)])[0] and kv(True, [(5, None)])[0] and kv(True, [])[0],
        kv(True, [(1, 0x05), (2, 0x20)])[0] and not kv(True, [(1, 0x05), (2, 0x09)])[0],
    ]
    rec("V1", all(v1), f"pure verdict rows (OFF, 8 key, 4 refused, fail-open, two sides) = {v1}")
    bad = [f"{who}:{tid}=0x{ti.trainer_class(tid, read_rom):02X}" for who, ids in KEY_BOSS_IDS.items() for tid in ids
           if ti.trainer_class(tid, read_rom) not in ti.KEY_TRAINER_CLASSES]
    bad += [f"{who}:{tid} is KEY" for who, tid in NON_KEY_IDS.items()
            if ti.trainer_class(tid, read_rom) in ti.KEY_TRAINER_CLASSES]
    rec("V2", not bad, f"every boss ID reads a key class, Marcel/grunt do not (violations: {bad})")

    logs: list = []
    reads = {"n": 0}

    def run(flag_on, cls, turns=1, reader_raises=False, extra=None):
        logs.clear()
        reads["n"] = 0

        def reader(two):
            reads["n"] += 1
            if reader_raises:
                raise AssertionError("the opponent reader was touched")
            return 767, None

        kv_env = {FLAG: "1"} if flag_on else {}
        kv_env.update(extra or {})
        out = []
        # `_r27_key_gate` imports the REAL module, so a mutant `ti`'s verdict and key set are patched onto it here.
        with env(**kv_env), Patch(TI, read_opponent_trainers=reader, trainer_class=lambda tid, *a, **k: cls,
                                  key_battle_verdict=ti.key_battle_verdict,
                                  KEY_TRAINER_CLASSES=ti.KEY_TRAINER_CLASSES), \
                Patch(sm, _log_story_event=lambda text, cat="": logs.append((cat, text))), \
                contextlib.redirect_stdout(io.StringIO()):
            s = sm.StoryItemBattleStrategy()
            for _ in range(turns):
                out.append(s._maybe_use_item(FakeBattleState()))
        kb = [t for c, t in logs if c == "KEYBATTLE"]
        return out, kb

    off, _ = run(False, 0x05)
    on_ord, kb_ord = run(True, 0x05)
    on_key, kb_key = run(True, 0x20)
    rec("I1", off[0] is not None and on_ord[0] is None and on_key[0] is not None,
        f"OFF uses the item ({off[0] is not None}); ON + 0x05 refuses ({on_ord[0] is None}, {kb_ord}); "
        f"ON + 0x20 uses it ({on_key[0] is not None})")
    off2, kb_off = run(False, 0x05, reader_raises=True)
    rec("I2", off2[0] is not None and not kb_off and reads["n"] == 0,
        f"OFF: item={off2[0] is not None} reads={reads['n']} KEYBATTLE lines={len(kb_off)} (want item, 0, 0)")
    _two, kb_two = run(True, 0x20, turns=2)
    rec("I3", reads["n"] == 1 and len(kb_two) == 1, f"ON over two turns: reads={reads['n']} lines={len(kb_two)} "
                                                   f"(want 1, 1)")
    raised, kb_raise = run(True, 0x05, extra={"POKEBOT_R27_FAULT_RAISE": "1"})
    rec("I4", raised[0] is not None and len(kb_raise) == 1 and "FAIL_OPEN" in kb_raise[0],
        f"FAULT_RAISE: item still fires ({raised[0] is not None}), line {kb_raise}")
    return red


def structure(src: str, sink=None):
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_maybe_use_item"), None)
    body = fn.body if fn else []
    idx_trainer = next((i for i, st in enumerate(body) if isinstance(st, ast.If)
                        and "Trainer" in ast.unparse(st.test)), None)
    idx_gate = next((i for i, st in enumerate(body) if isinstance(st, ast.If)
                     and "_r27_key_gate" in ast.unparse(st.test)), None)
    idx_med = next((i for i, st in enumerate(body) if isinstance(st, ast.Assign)
                    and any(getattr(t, "id", None) == "medicine" for t in st.targets)), None)
    os_imports = [st for st in ast.walk(fn) if isinstance(st, ast.Import)
                  and any(a.name == "os" for a in st.names)] if fn else []
    first_ok = bool(body) and isinstance(body[0], ast.Import) and ast.unparse(body[0]) == "import os as _os"
    ok = (None not in (idx_trainer, idx_gate, idx_med) and idx_trainer < idx_gate < idx_med
          and len(os_imports) == 1 and first_ok)
    check(ok, f"A1 gate after the Trainer return and before `medicine =` (indices {idx_trainer} < {idx_gate} < "
              f"{idx_med}); one os import, `import os as _os` first ({len(os_imports)}, {first_ok})", sink)
    return ok


def mutant(path: pathlib.Path, src: str, name: str):
    mod = types.ModuleType(name)
    mod.__file__ = str(path)
    exec(compile(src, name, "exec"), mod.__dict__)
    return mod


def main() -> int:
    print("V/I — verdict, reconciliation, integration")
    cases()
    sm_src = SM_PATH.read_text(encoding="utf-8")
    print("A — structure and registry")
    structure(sm_src)
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(all(f in reg for f in (FLAG,) + FAULTS), f"A2 {FLAG} and both fault envs are registered in 29")

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    saved = os.environ.get("POKEBOT_R27_FAULT_ALLORDINARY")
    os.environ["POKEBOT_R27_FAULT_ALLORDINARY"] = "1"
    try:
        # `run()` resets the fault envs per call, so ALLORDINARY rides on `extra` — re-run I1 by hand.
        red = set()
        logs: list = []
        with Patch(TI, read_opponent_trainers=lambda two: (265, None), trainer_class=lambda tid, *a, **k: 0x20), \
                Patch(SM, _log_story_event=lambda text, cat="": logs.append((cat, text))), \
                contextlib.redirect_stdout(io.StringIO()):
            os.environ[FLAG] = "1"
            key_under_fault = SM.StoryItemBattleStrategy()._maybe_use_item(FakeBattleState())
        if key_under_fault is not None:
            red.add("(the key row still healed)")
        else:
            red.add("I1")
    finally:
        os.environ.pop(FLAG, None)
        if saved is None:
            os.environ.pop("POKEBOT_R27_FAULT_ALLORDINARY", None)
        else:
            os.environ["POKEBOT_R27_FAULT_ALLORDINARY"] = saved
    check(base_ok and red == {"I1"}, f"F1 POKEBOT_R27_FAULT_ALLORDINARY=1 refuses a key (0x20) opponent → exactly "
                                     f"['I1'] red (red: {sorted(red)})")
    ti_src = TI_PATH.read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in ti_src else "\n"
    a_always = '    if not flag_on:' + nl + '        return True, "flag_off"'
    m2 = ti_src.replace(a_always, '    return True, "mutant_always"' + nl + a_always, 1) if ti_src.count(a_always) == 1 \
        else None
    with env():
        red = cases(mutant(TI_PATH, m2, "ti_f2"), SM, []) if m2 else {"(anchor missing)"}
    check(base_ok and red == {"V1", "I1"}, f"F2 a verdict that always allows → exactly ['I1', 'V1'] red "
                                           f"(red: {sorted(red)})")
    a_open = '            return True, "fail_open_unreadable"'
    m3 = ti_src.replace(a_open, '            return False, "mutant_fail_closed"', 1) if ti_src.count(a_open) == 1 \
        else None
    with env():
        red = cases(mutant(TI_PATH, m3, "ti_f3"), SM, []) if m3 else {"(anchor missing)"}
    check(base_ok and red == {"V1"}, f"F3 a verdict that fails CLOSED on an unreadable side → exactly ['V1'] red "
                                     f"(red: {sorted(red)})")
    gate = '        if _os.environ.get("POKEBOT_R27_KEYITEMS") == "1" and not _r27_key_gate(self, battle_state):'
    gate_n = gate + nl + "            return None" + nl
    if sm_src.count(gate_n) == 1:
        m4_src = sm_src.replace(gate_n, "        # " + gate.strip() + nl + "        #     return None" + nl, 1)
        with env():
            red = cases(TI, mutant(SM_PATH, m4_src, "sm_f4"), [])
        if not structure(m4_src, []):
            red.add("A1")
    else:
        red = {"(anchor missing)"}
    check(base_ok and red == {"I1", "I3", "I4", "A1"}, f"F4 the gate only in a COMMENT → exactly ['A1', 'I1', 'I3', "
                                                       f"'I4'] red "
                                                 f"(red: {sorted(red)})")
    a_rival = '    TRAINER_CLASS["LEADER"], TRAINER_CLASS["ELITE_FOUR"], TRAINER_CLASS["CHAMPION"], TRAINER_CLASS["RIVAL"],'
    m5 = (ti_src.replace(a_rival, a_rival.replace(', TRAINER_CLASS["RIVAL"],', ','), 1)
          if ti_src.count(a_rival) == 1 else None)
    with env():
        red = cases(mutant(TI_PATH, m5, "ti_f5"), SM, []) if m5 else {"(anchor missing)"}
    check(base_ok and red == {"V1", "V2"}, f"F5 RIVAL (0x32) dropped from the key set → exactly ['V1', 'V2'] red "
                                           f"(red: {sorted(red)})")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — with POKEBOT_R27_KEYITEMS, healing items only against key trainer classes; OFF unchanged; fails open")
    return 0


if __name__ == "__main__":
    sys.exit(main())
