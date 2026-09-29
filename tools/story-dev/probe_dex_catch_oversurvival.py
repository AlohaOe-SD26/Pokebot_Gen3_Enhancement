r"""GATE (stub-driven) — USER RULING 24 step 4: with `POKEBOT_R24_OVERSURVIVAL=1` a WANTED species is caught even on a map
where survival mode (3+ defeats on the map) flees every wild; an UNWANTED species still meets survival mode (2026-09-29).

WHY: the user ruled (`06`, 2026-09-28): *"catching should always be available if the bot encounters a pokemon that it
wants to catch"*. `on_battle_started` ran survival mode BEFORE the dex-catch commit, so on a map with 3+ defeats a
wanted species was fled unevaluated. The commit is now `_dex_catch_commit`; ON calls it before survival mode, OFF after
it, exactly as always. (How OFTEN a wanted species meets survival mode is a batch question.)
Every case drives the REAL `StoryMode.on_battle_started` on a stubbed instance: `_should_catch` stubbed (wanted /
unwanted), `_location_key` stubbed with 3 (or 0) defeats, swap-training off, no HM or counter hunt armed.
  S1  ON,  3 defeats, wanted:   a CATCH strategy.          S2 OFF, 3 defeats, wanted: `StoryFleeStrategy` (the old order).
  S3  ON,  3 defeats, unwanted: `StoryFleeStrategy`.        S4 OFF, 3 defeats, unwanted: `StoryFleeStrategy`.
  S5  ON,  0 defeats, wanted:   a catch strategy.           S6 OFF, 0 defeats, wanted: a catch strategy.
  S7  ON,  0 defeats, unwanted: neither a catch nor a flee (falls through, as OFF does).
  S8-S10  ON, 3 defeats, WANTED, and also a shiny / an HM-hunt target / a counter-hunt target: the shiny, HM and
      counter branches still commit FIRST (the code's scope sentence "Shiny, HM and counter catches ran above and stay
      first"). The discriminator is the BRANCH IDENTITY, the `kind` handed to `_r20_catch_start` (rule 7: the action,
      not a class name two branches share).
  S11 OFF, a SHIM `self` (the `repro_ki65_unbound_party_index.py` shape: a bare namespace with only `_should_catch` and
      `_catch_team_target`), wanted: NO raise, and exactly the pre-change reading — `StoryItemBattleStrategy`, no commit
      (the shim has no `_dex_catch_attempts`, so the commit's own `try` swallows that and falls through; measured on
      HEAD `9a4fbbeb`'s code, 2026-09-29). Harness drivers and repros call `StoryMode.on_battle_started(shim, …)`; the
      first version called `self._dex_catch_commit` outside any `try` and raised AttributeError there (the suite's
      `repro_ki65_unbound_party_index.py` went red).
  A1  `reset_per_run_state` reads the flag.   A2 `on_battle_started` calls `_dex_catch_commit` exactly twice, and the
      helper keeps its LOCAL `from modules.console import console` (the UnboundLocalError trap, 08).
  A3  both flags are registered in 29.
FAULT ARMS (built in; the unmutated subject must pass first; each must turn EXACTLY its own set red):
  F1  `POKEBOT_R24_FAULT_SKIPSURVIVAL=1` (in production code) also skips survival mode for unwanted species: {S3}.
  F2  a source mutant without the early (ON) call: {S1, S5} (ON then never runs the commit at all).
  F3  a widening mutant that hoists the early call above the shiny branch: {S8, S9, S10}.
  F4  a widening mutant that runs the early call whatever the flag (OFF then catches before survival mode): {S2}.
  F5  a mutant calling `self._dex_catch_commit(encounter)` (the first version) at the OFF site: {S11}.

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_dex_catch_oversurvival.py
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

import modules.battle_strategies.default as DEFAULT  # noqa: E402
import modules.story.early_game as EG  # noqa: E402
import plugins.custom_modes.story_mode as SM  # noqa: E402

SM_PATH = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
FLAG, FAULT = "POKEBOT_R24_OVERSURVIVAL", "POKEBOT_R24_FAULT_SKIPSURVIVAL"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


@contextlib.contextmanager
def env(**kv):
    saved = {k: os.environ.get(k) for k in (FLAG, FAULT)}
    try:
        for k in (FLAG, FAULT):
            os.environ.pop(k, None)
        os.environ.update(kv)
        yield
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def outcome(mod, flag_on: bool, defeats: int, wanted: bool, fault: bool = False, extra: str = "") -> tuple:
    """Drive the real `on_battle_started` on a stubbed instance; return (strategy class, committed catch `kind`).
    `extra` is "" or one of "shiny" / "hm" / "counter" (the encounter is also that branch's target)."""
    import modules.items as ITEMS
    import modules.pokemon_party as PARTY
    import modules.story.counter_hunt as CH

    kv = {FLAG: "1"} if flag_on else {}
    if fault:
        kv[FAULT] = "1"
    fake_party = types.SimpleNamespace(first_non_fainted=types.SimpleNamespace(index=0))
    bag = types.SimpleNamespace(poke_balls=[types.SimpleNamespace(quantity=5)])
    kinds: list = []
    saved = (DEFAULT.get_party, EG._SWAP_TRAIN, set(EG.HM_CATCH_TARGET_DEX), set(CH.COUNTER_CATCH_TARGET_DEX),
             ITEMS.get_item_bag, PARTY.get_party, mod.context, mod._r20_catch_start)
    try:
        DEFAULT.get_party = lambda: fake_party
        EG._SWAP_TRAIN = False
        EG.HM_CATCH_TARGET_DEX = {312} if extra == "hm" else set()
        ITEMS.get_item_bag = lambda: bag
        PARTY.get_party = lambda: [types.SimpleNamespace()]
        mod._r20_catch_start = lambda mode, kind, enc, dex=None: kinds.append(kind)
        with env(**kv):
            m = mod.StoryMode.__new__(mod.StoryMode)
            mod.StoryMode.reset_per_run_state(m)
        mod.context = types.SimpleNamespace(message="", bot_mode_instance=m)
        # AFTER the reset: `reset_per_run_state` disarms the counter hunt (a driver that armed it first disarmed itself).
        CH.COUNTER_CATCH_TARGET_DEX = {312} if extra == "counter" else set()
        m._location_key = lambda: (0, 25)
        m._defeat_counts[(0, 25)] = defeats
        m._should_catch = lambda enc: wanted
        enc = types.SimpleNamespace(is_shiny=(extra == "shiny"), type=types.SimpleNamespace(name="Wild"),
                                    pokemon=types.SimpleNamespace(level=20, species=types.SimpleNamespace(
                                        name="Minun", national_dex_number=312)))
        with env(**kv), contextlib.redirect_stdout(io.StringIO()):
            strat = mod.StoryMode.on_battle_started(m, enc)
        return (type(strat).__name__ if strat is not None else "None"), ",".join(kinds) or "-"
    finally:
        (DEFAULT.get_party, EG._SWAP_TRAIN, EG.HM_CATCH_TARGET_DEX, CH.COUNTER_CATCH_TARGET_DEX,
         ITEMS.get_item_bag, PARTY.get_party, mod.context, mod._r20_catch_start) = saved


CATCH = {"StoryCatchStrategy", "StoryDexCatchStrategy"}
DEXK = {"team", "dex"}
CASES = [  # tag, flag ON, defeats, wanted, extra, predicate on (class, kind), the wanted reading
    ("S1", True, 3, True, "", lambda c, k: c in CATCH and k in DEXK, "a dex catch"),
    ("S2", False, 3, True, "", lambda c, k: c == "StoryFleeStrategy" and k == "-", "StoryFleeStrategy, no catch"),
    ("S3", True, 3, False, "", lambda c, k: c == "StoryFleeStrategy" and k == "-", "StoryFleeStrategy, no catch"),
    ("S4", False, 3, False, "", lambda c, k: c == "StoryFleeStrategy" and k == "-", "StoryFleeStrategy, no catch"),
    ("S5", True, 0, True, "", lambda c, k: c in CATCH and k in DEXK, "a dex catch"),
    ("S6", False, 0, True, "", lambda c, k: c in CATCH and k in DEXK, "a dex catch"),
    ("S7", True, 0, False, "", lambda c, k: c not in CATCH and c != "StoryFleeStrategy" and k == "-",
     "neither a catch nor a flee"),
    ("S8", True, 3, True, "shiny", lambda c, k: c == "StoryShinyCatchStrategy" and k == "shiny", "the SHINY branch"),
    ("S9", True, 3, True, "hm", lambda c, k: c == "StoryCatchStrategy" and k == "hm", "the HM branch"),
    ("S10", True, 3, True, "counter", lambda c, k: c == "StoryCatchStrategy" and k == "counter",
     "the COUNTER branch"),
]


def shim_outcome(mod) -> tuple:
    """S11: the repro/harness shim shape. Returns (strategy class or the exception's name, committed kind)."""
    import modules.items as ITEMS
    import modules.pokemon_party as PARTY

    bag = types.SimpleNamespace(poke_balls=[types.SimpleNamespace(quantity=5)])
    kinds: list = []
    saved = (DEFAULT.get_party, EG._SWAP_TRAIN, set(EG.HM_CATCH_TARGET_DEX), ITEMS.get_item_bag, PARTY.get_party,
             mod.context, mod._r20_catch_start)
    try:
        DEFAULT.get_party = lambda: types.SimpleNamespace(first_non_fainted=types.SimpleNamespace(index=0))
        EG._SWAP_TRAIN = False
        EG.HM_CATCH_TARGET_DEX = set()
        ITEMS.get_item_bag = lambda: bag
        PARTY.get_party = lambda: [types.SimpleNamespace()]
        mod._r20_catch_start = lambda mode, kind, enc, dex=None: kinds.append(kind)
        shim = types.SimpleNamespace(_catch_team_target=4)
        shim._should_catch = lambda enc: True
        mod.context = types.SimpleNamespace(message="", bot_mode_instance=shim)
        enc = types.SimpleNamespace(is_shiny=False, type=types.SimpleNamespace(name="Wild"),
                                    pokemon=types.SimpleNamespace(level=20, species=types.SimpleNamespace(
                                        name="Minun", national_dex_number=312)))
        with env(), contextlib.redirect_stdout(io.StringIO()):
            try:
                strat = mod.StoryMode.on_battle_started(shim, enc)
            except Exception as e:  # noqa: BLE001 - the reading IS whether it raised
                return f"RAISED {type(e).__name__}", ",".join(kinds) or "-"
        return (type(strat).__name__ if strat is not None else "None"), ",".join(kinds) or "-"
    finally:
        (DEFAULT.get_party, EG._SWAP_TRAIN, EG.HM_CATCH_TARGET_DEX, ITEMS.get_item_bag, PARTY.get_party,
         mod.context, mod._r20_catch_start) = saved


def run_cases(mod=SM, sink=None, fault=False) -> set:
    red = set()
    cls, kind = shim_outcome(mod)
    ok = cls == "StoryItemBattleStrategy" and kind == "-"
    if not ok:
        red.add("S11")
    check(ok, f"S11 flag=OFF a SHIM self (repro shape), wanted: {cls} kind={kind} (want no raise and the pre-change "
              f"reading StoryItemBattleStrategy, kind=-)", sink)
    for tag, flag_on, defeats, wanted, extra, ok_fn, want in CASES:
        cls, kind = outcome(mod, flag_on, defeats, wanted, fault, extra)
        ok = ok_fn(cls, kind)
        if not ok:
            red.add(tag)
        check(ok, f"{tag} flag={'ON' if flag_on else 'OFF'} defeats={defeats} wanted={wanted}"
                  f"{' ' + extra if extra else ''}: {cls} kind={kind} (want {want})", sink)
    return red


def structure(src: str, sink=None):
    tree = ast.parse(src)
    obs = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "on_battle_started"), None)
    calls = sum(1 for c in ast.walk(obs) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr == "_dex_catch_commit") if obs else 0
    helper = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_dex_catch_commit"), None)
    local_console = helper is not None and any(
        isinstance(n, ast.ImportFrom) and n.module == "modules.console" and any(a.name == "console" for a in n.names)
        for n in ast.walk(helper))
    check(calls == 2 and local_console, f"A2 on_battle_started calls _dex_catch_commit twice ({calls}); the helper keeps "
                                        f"its local console import ({local_console})", sink)


def mutant_module(src: str):
    mod = types.ModuleType("story_mode_mutant")
    mod.__file__ = str(SM_PATH)
    exec(compile(src, "story_mode_mutant", "exec"), mod.__dict__)
    return mod


def main() -> int:
    print("S — the real on_battle_started, stubbed")
    run_cases()
    with env():
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        off = m._r24_oversurvival
    with env(**{FLAG: "1"}):
        m = SM.StoryMode.__new__(SM.StoryMode)
        SM.StoryMode.reset_per_run_state(m)
        on = m._r24_oversurvival
    check(off is False and on is True, f"A1 reset_per_run_state: unset -> {off}, {FLAG}=1 -> {on}")
    src = SM_PATH.read_text(encoding="utf-8")
    structure(src)
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(FLAG in reg and FAULT in reg, f"A3 {FLAG} and {FAULT} are registered in 29")

    print("F — fault arms (each requires the unmutated subject to pass first)")
    base_ok = not failures
    red = run_cases(SM, [], fault=True)
    check(base_ok and red == {"S3"}, f"F1 {FAULT}=1 turns exactly {{S3}} red (red: {sorted(red)})")
    nl = "\r\n" if "\r\n" in src else "\n"
    early_call = ("            _dex_strategy = StoryMode._dex_catch_commit(self, encounter)\n"
                  "            if _dex_strategy is not None:\n"
                  "                return _dex_strategy\n"
                  "            _r24_skip_survival = ").replace("\n", nl)
    red = (run_cases(mutant_module(src.replace(early_call, "            _r24_skip_survival = ", 1)), [])
           if src.count(early_call) == 1 else {"(anchor missing)"})
    check(base_ok and red == {"S1", "S5"}, f"F2 a mutant without the early ON call turns exactly {{S1, S5}} red "
                                            f"(red: {sorted(red)})")
    shiny_anchor = ("        try:\n"
                    "            if encounter is not None and encounter.is_shiny:\n").replace("\n", nl)
    hoist = ("        if getattr(self, \"_r24_oversurvival\", False):\n"
             "            _hoisted = StoryMode._dex_catch_commit(self, encounter)\n"
             "            if _hoisted is not None:\n"
             "                return _hoisted\n").replace("\n", nl)
    red = (run_cases(mutant_module(src.replace(shiny_anchor, hoist + shiny_anchor, 1)), [])
           if src.count(shiny_anchor) == 1 else {"(anchor missing)"})
    check(base_ok and red == {"S8", "S9", "S10"}, f"F3 a mutant hoisting the early call above the shiny branch turns "
                                                   f"exactly {{S8, S9, S10}} red (red: {sorted(red)})")

    flag_gate = ("        if getattr(self, \"_r24_oversurvival\", False):" + nl +
                 "            _dex_strategy = StoryMode._dex_catch_commit(self, encounter)")
    red = (run_cases(mutant_module(src.replace(flag_gate, flag_gate.replace(
        'getattr(self, "_r24_oversurvival", False)', "True"), 1)), [])
           if src.count(flag_gate) == 1 else {"(anchor missing)"})
    check(base_ok and red == {"S2"}, f"F4 a mutant running the early call whatever the flag turns exactly {{S2}} red "
                                      f"(red: {sorted(red)})")
    off_call = ("        if not getattr(self, \"_r24_oversurvival\", False):" + nl +
                "            _dex_strategy = StoryMode._dex_catch_commit(self, encounter)")
    red = (run_cases(mutant_module(src.replace(off_call, off_call.replace(
        "StoryMode._dex_catch_commit(self, encounter)", "self._dex_catch_commit(encounter)"), 1)), [])
           if src.count(off_call) == 1 else {"(anchor missing)"})
    check(base_ok and red == {"S11"}, f"F5 a mutant calling self._dex_catch_commit at the OFF site turns exactly {{S11}} "
                                       f"red (red: {sorted(red)})")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — with POKEBOT_R24_OVERSURVIVAL a wanted species is caught before survival mode flees; OFF is unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
