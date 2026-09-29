"""GATE — USER RULING 25, design v2 step 8 (RC): the cap of 3 (`POKEBOT_R25_CAP`) and the rare exemption
(`POKEBOT_R25_RARE`), through the REAL helpers `r25_rarity_verdict` / `r25_catch_inputs` into the REAL `decide_dex_catch`.

WHY. The exemption lets a RARE species through the attempt cap and the expected-throws refusal without limit, and the
user accepted the whiteouts that can cost (06). So two failure shapes matter and each has rows here:
  * the exemption leaks: it fires before another gate (RAREEARLY), for an ordinary species (RAREALL), or with the flag
    off (RAREUNGATED). ⇒ K3, K6 and K7 must hold.
  * ‼ the exemption is SILENTLY INERT: `_should_catch` holds an `EncounterInfo`, and `rarity.encounter_rarity` on the
    wrapper reads rare=False with an adapter_error note and never raises (the step 8 recon ran it). Stub-based rows
    cannot see that. ⇒ K11 EXECUTES the real `StoryMode._should_catch` on a shim with stubbed live reads, for OFF, RARE
    and CAP, and A1 pins its wiring by AST. ⚠ K9 only shows the REAL `encounter_rarity` works on a Pokemon and not on
    the wrapper: it builds its own `getattr(enc, "pokemon", None)`, so it cannot see the ADAPTER (the step 8 review
    measured that six adapter mutants left every K/A row green before K11 existed).

ROWS
  K1-K10  literal fence rows (the fence's full-party admit case, one field overridden per row). K6 compares each gate's
          reason for a RARE target with that same gate's reason for an ordinary one: the exemption must not change it.
  K11     the REAL adapter `StoryMode._should_catch` on a shim: OFF refuses at the cap with NO rarity read; RARE admits
          a rare target and logs its suffix; CAP admits at 2; RARE gives an ordinary target nothing.
  A1-A6   wiring: the AST pin (every argument of the verdict and inputs calls), OFF gives the old inputs with no read,
          the defaults, the per-run flag ASSIGNMENTS, the log suffix, and the three log sites.
  M1-M13  source mutants of `story_mode.py`, each with the EXACT set of rows it must turn red; N1 a comment-only edit
          that must turn nothing red.

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_r25_catch_cap.py        (exit 1 on any failure)
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import sys
import types
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / "sandbox-pokebot"))
SM_PATH = REPO / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"

import plugins.custom_modes.story_mode as SM  # noqa: E402
from modules import rarity  # noqa: E402
from modules.pokemon import Pokemon, get_species_by_index, get_species_by_national_dex  # noqa: E402

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {label}{('  — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(label)


class Mon:
    """A stand-in `Pokemon` borrowing the REAL `gender` property (the probe_rarity_predicate.py pattern)."""

    gender = Pokemon.gender

    def __init__(self, national=None, pv=0, internal=None):
        self.species = get_species_by_index(internal) if internal is not None else get_species_by_national_dex(national)
        self.personality_value = pv
        self.is_shiny = False
        self.is_empty = False
        self.is_valid = True
        self.is_egg = False


RARE_V = rarity.RareVerdict(True, "RARE", ("rate",))
ORD_V = rarity.RareVerdict(False, None, ())


def stub(verdict):
    return lambda _pokemon: verdict


def raising(_pokemon):
    raise RuntimeError("rarity fault")


def base(m):
    """The fence's full-party admit case (probe_dex_catch_fence.py's BASE), built from module `m`'s constants."""
    return dict(is_wild=True, is_shiny=False, has_pokedex=True, pre_badge1=False, party_slots_used=m.PARTY_CAPACITY,
                battler_count=m.PARTY_CAPACITY, party_target=4, resource_block=None,
                spare_balls=m.DEX_CATCH_BALL_RESERVE + 5, hunt_armed=False, training=False, boxed_count=12,
                party_healthy=True, species_dex=358, owned_dex=frozenset({1, 4, 7}),
                party_dex=frozenset({1, 4, 7, 261, 183, 351}), attempts=0)


def fence(m, cap_on, rare_on, rarity_fn, pokemon=None, **over):
    """decide_dex_catch(**base, **over, **r25_catch_inputs(cap_on, r25_rarity_verdict(rare_on, rarity_fn, pokemon)))."""
    kw = dict(base(m), **over)
    kw.update(m.r25_catch_inputs(cap_on, m.r25_rarity_verdict(rare_on, rarity_fn, pokemon)))
    return m.decide_dex_catch(**kw)


def k_rows(m, tag=""):
    """The K rows over module `m`. Returns the labels that failed."""
    failed: list[str] = []

    def row(label, got, want_catch, want_reason_part):
        ok = got[0] == want_catch and want_reason_part in got[1]
        if not ok:
            failed.append(label.split()[0])
        if not tag:
            check(label, ok, f"got {got}")

    row("K1a ordinary, attempts 2, CAP off -> refused (already attempted)",
        fence(m, False, True, stub(ORD_V), attempts=2), False, "already attempted")
    row("K1b ordinary, attempts 2, CAP on -> admitted", fence(m, True, True, stub(ORD_V), attempts=2), True, "dex catch")
    row("K2a ordinary, attempts 3, CAP off -> refused", fence(m, False, True, stub(ORD_V), attempts=3), False, "already attempted")
    row("K2b ordinary, attempts 3, CAP on -> refused", fence(m, True, True, stub(ORD_V), attempts=3), False, "already attempted")
    row("K3 RARE off (CAP off), a species the stub marks rare, attempts 2 -> refused",
        fence(m, False, False, stub(RARE_V), attempts=2), False, "already attempted")
    row("K4 RARE on, rare, attempts 50 -> admitted", fence(m, True, True, stub(RARE_V), attempts=50), True, "dex catch")
    row("K5a RARE on, rare, expected throws 16.0 -> admitted",
        fence(m, False, True, stub(RARE_V), expected_throws=16.0), True, "dex catch")
    row("K5b RARE off, rare, expected throws 16.0 -> refused (throws)",
        fence(m, False, False, stub(RARE_V), expected_throws=16.0), False, "expected throws")
    # K6: each other gate, for a rare target at attempts 50, gives exactly the reason it gives an ordinary target.
    gates = {
        "runway (party 5, fence closed)": dict(party_slots_used=5, battler_count=5),
        "armed hunt": dict(hunt_armed=True),
        "walking hunt (party 5, fence open)": dict(open_fence=True, party_slots_used=5, battler_count=5, hunt_walking=True),
        "PC full": dict(boxed_count=m.PC_STORAGE_SLOTS),
        "10-ball reserve (spare 5)": dict(spare_balls=5),
        "training": dict(training=True),
        "health": dict(party_healthy=False),
    }
    for name, over in gates.items():
        ordinary = fence(m, False, False, stub(ORD_V), **over)
        got = fence(m, True, True, stub(RARE_V), attempts=50, **over)
        ok = (not got[0]) and got == ordinary and "already attempted" not in got[1]
        if not ok:
            failed.append(f"K6 {name}")
        if not tag:
            check(f"K6 RARE on, rare, attempts 50: the {name} gate still refuses, with its own reason", ok,
                  f"rare {got} / ordinary {ordinary}")
    row("K7 RARE on, ORDINARY, expected throws 16.0 -> refused (throws)",
        fence(m, False, True, stub(ORD_V), expected_throws=16.0), False, "expected throws")
    try:
        v = m.r25_rarity_verdict(True, raising, None)
        got = fence(m, False, True, raising, attempts=2)
        ok = (v.rare, str(v.note).startswith("helper_error:RuntimeError")) == (False, True) and not got[0]
    except Exception as error:  # noqa: BLE001
        ok, v, got = False, f"RAISED {error!r}", None
    if not ok:
        failed.append("K8")
    if not tag:
        check("K8 RARE on, the rarity function raises -> not rare (helper_error), refused at the cap, no raise", ok,
              f"verdict {v}; fence {got}")
    # K9: the REAL encounter_rarity through the helper, on the adapter's own expression over an EncounterInfo shape.
    enc = SimpleNamespace(pokemon=Mon(358, 0x10), is_shiny=False)       # Chimecho, rate-rare (2%)
    v_mon = m.r25_rarity_verdict(True, rarity.encounter_rarity, getattr(enc, "pokemon", None))
    ok = (v_mon.rare, v_mon.note) == (True, None) and fence(m, False, True, rarity.encounter_rarity,
                                                             getattr(enc, "pokemon", None), attempts=5)[0]
    if not ok:
        failed.append("K9")
    if not tag:
        check("K9 the REAL encounter_rarity on `encounter.pokemon` (Chimecho) -> rare, admitted past the cap", ok, str(v_mon))
    v_wrap = m.r25_rarity_verdict(True, rarity.encounter_rarity, enc)
    ok = (v_wrap.rare, str(v_wrap.note).startswith("adapter_error")) == (False, True)
    if not ok:
        failed.append("K9b")
    if not tag:
        check("K9b ...and on the EncounterInfo itself it reads NOT rare (the trap A1 pins against)", ok, str(v_wrap))
    # K10: a phantom species-0 opponent (national reads 151 = Mew) must not become a 'legendary' past the throws gate.
    v0 = m.r25_rarity_verdict(True, rarity.encounter_rarity, Mon(internal=0))
    got = fence(m, False, True, rarity.encounter_rarity, Mon(internal=0), expected_throws=float("inf"))
    ok = (v0.rare, v0.note) == (False, "no_species") and not got[0]
    if not ok:
        failed.append("K10")
    if not tag:
        check("K10 species index 0 with RARE on -> not rare (no_species), refused by the throws gate", ok, f"{v0} / {got}")
    return failed


def adapter_rows(m, tag=""):
    """K11: EXECUTE the real `m.StoryMode._should_catch` on a shim, with every live read stubbed (a full, healthy party
    after gym 1, 30 spare balls, nothing armed), and record what it decides, logs and stashes."""
    failed: list[str] = []
    import modules.items as _items
    import modules.memory as _memory
    import modules.pokedex as _pokedex
    import modules.pokemon_party as _pparty
    from modules.story import counter_hunt as _ch
    from modules.story import early_game as _eg

    party = [Mon(n, 0) for n in (1, 4, 7, 261, 183, 351)]
    for p in party:
        p.current_hp = p.total_hp = 10
    stubs = [
        (_memory, "get_event_flag", lambda name: True),
        (_pparty, "get_party", lambda: list(party)),
        (_pokedex, "get_pokedex", lambda: SimpleNamespace(owned_species=[p.species for p in party])),
        (_items, "get_item_bag", lambda: SimpleNamespace(number_of_balls_except_master_ball=30, poke_balls=[])),
        (_ch, "resource_blocker", lambda: None),
        (_ch, "is_armed", lambda: False),
        (_ch, "_box_count", lambda: 12),
        (_eg, "HM_CATCH_TARGET_DEX", None),
        (_eg, "swap_train_active", lambda: False),
        (_eg, "hunt_walk_active", lambda: False),
    ]
    reads: list = []
    real_rarity = rarity.encounter_rarity
    stubs.append((rarity, "encounter_rarity", lambda p: reads.append(p) or real_rarity(p)))
    logged: list = []
    stubs.append((m, "_log_story_event", lambda line, tag_: logged.append(line)))
    saved = [(mod, name, getattr(mod, name)) for mod, name, _ in stubs]

    def run(rare_flag, cap_flag, national):
        shim = SimpleNamespace(_catch_team_target=4, _dex_catch_attempts={national: 2}, _open_fence=False,
                               _hunt_first=False, _r24_catchhurt=False, _r24_catchtrain=False,
                               _r25_cap=cap_flag, _r25_rare=rare_flag)
        reads.clear()
        logged.clear()
        got = m.StoryMode._should_catch(shim, SimpleNamespace(pokemon=Mon(national, 0x10), is_shiny=False))
        return got, shim, list(logged), len(reads)

    try:
        for mod, name, value in stubs:
            setattr(mod, name, value)
        results = {
            "K11a": run(False, False, 358),   # Chimecho (rate-rare), flags OFF
            "K11b": run(True, False, 358),    # RARE on
            "K11c": run(False, True, 358),    # CAP on
            "K11d": run(True, False, 263),    # RARE on, Zigzagoon (ordinary)
        }
    finally:
        for mod, name, value in saved:
            setattr(mod, name, value)

    def arow(key, label, ok, detail):
        if not ok:
            failed.append(key)
        if not tag:
            check(f"{key} {label}", ok, detail)

    got, shim, lines, n = results["K11a"]
    arow("K11a", "REAL adapter, flags OFF, a rare target at attempts 2 -> refused at the cap, the rarity predicate NEVER "
         "read, no suffix", not got and "already attempted" in shim._dex_catch_last_reason and n == 0
         and shim._r25_last_verdict is None and lines and not lines[0].endswith("note=-"), f"{got} {lines} reads={n}")
    got, shim, lines, n = results["K11b"]
    arow("K11b", "REAL adapter, RARE on -> admitted past the cap, asked about the POKEMON, suffix rare=rate tier=RARE",
         got and n == 1 and getattr(shim._r25_last_verdict, "rare", False)
         and lines and lines[0].endswith(" rare=rate tier=RARE note=-"), f"{got} {lines} reads={n}")
    got, shim, lines, n = results["K11c"]
    arow("K11c", "REAL adapter, CAP on -> admitted at attempts 2, no read, no suffix",
         got and n == 0 and lines and "note=" not in lines[0], f"{got} {lines} reads={n}")
    got, shim, lines, n = results["K11d"]
    arow("K11d", "REAL adapter, RARE on, an ORDINARY target -> refused at the cap, suffix rare=- tier=- note=-",
         not got and "already attempted" in shim._dex_catch_last_reason and lines
         and lines[0].endswith(" rare=- tier=- note=-"), f"{got} {lines} reads={n}")
    return failed


def a_rows(m, src, tag=""):
    failed: list[str] = []

    def arow(label, ok, detail=""):
        if not ok:
            failed.append(label.split()[0])
        if not tag:
            check(label, ok, detail)

    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_should_catch"), None)
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "decide_dex_catch"] if fn else []
    star = [k for c in calls for k in c.keywords if k.arg is None]
    verdict_calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "r25_rarity_verdict"] if fn else []
    subject = [n for n in ast.walk(fn) if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "_r25_subject"
                                                                               for t in n.targets)] if fn else []
    arow("A1 `_should_catch` passes `**r25_catch_inputs(...)` to decide_dex_catch, and asks r25_rarity_verdict about "
         "`getattr(encounter, 'pokemon', None)` (the wrapper only under the fault arm)",
         len(calls) == 1 and len(star) == 1
         and ast.unparse(star[0].value) == "r25_catch_inputs(getattr(self, '_r25_cap', False), _r25_verdict)"
         and len(verdict_calls) == 1 and ast.unparse(verdict_calls[0].args[0]) == "getattr(self, '_r25_rare', False)"
         and ast.unparse(verdict_calls[0].args[1]) == "_rarity.encounter_rarity"
         and ast.unparse(verdict_calls[0].args[2]) == "_r25_subject" and len(subject) == 1
         and ast.unparse(subject[0].value).endswith("else getattr(encounter, 'pokemon', None)")
         and "POKEBOT_R25_FAULT_RAREWRAPPER" in ast.unparse(subject[0].value),
         ast.unparse(subject[0].value) if subject else "no _r25_subject assignment")
    calls_made = []
    none_v = m.r25_rarity_verdict(False, lambda p: calls_made.append(p), object())
    arow("A2 both flags OFF -> exactly the old inputs, and the rarity function is NEVER called",
         m.r25_catch_inputs(False, None) == {"max_attempts": m.DEX_CATCH_MAX_ATTEMPTS, "rare": False}
         and none_v is None and not calls_made)
    sig = inspect.signature(m.decide_dex_catch).parameters
    arow("A3 decide_dex_catch defaults: max_attempts = DEX_CATCH_MAX_ATTEMPTS, rare = False",
         sig["max_attempts"].default == m.DEX_CATCH_MAX_ATTEMPTS and sig["rare"].default is False)
    reset_fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "reset_per_run_state"), None)
    reset_src = ast.get_source_segment(src, reset_fn) if reset_fn else ""   # from the SOURCE, so mutants are read too
    arow("A4 the flags are read per run in reset_per_run_state, each into ITS OWN attribute",
         'self._r25_cap = _os_team6.environ.get("POKEBOT_R25_CAP") == "1"' in reset_src
         and 'self._r25_rare = _os_team6.environ.get("POKEBOT_R25_RARE") == "1"' in reset_src)
    uv = rarity.RareVerdict(True, "ULTRA", ("variant",))
    bad = SimpleNamespace(_r25_rare=True, _r25_last_verdict=SimpleNamespace())   # no .reasons: must not raise
    arow("A5 the log suffix: OFF '', ON with a verdict, ON unread, and never raises",
         m._r25_log_suffix(SimpleNamespace(_r25_rare=False, _r25_last_verdict=uv)) == ""
         and m._r25_log_suffix(SimpleNamespace(_r25_rare=True, _r25_last_verdict=uv)) == " rare=variant tier=ULTRA note=-"
         and m._r25_log_suffix(SimpleNamespace(_r25_rare=True, _r25_last_verdict=None)) == " rare=- tier=- note=unread"
         and m._r25_log_suffix(bad) == "")
    arow("A6 the three log sites append the suffix ([DEXFENCE], [DEXCATCH] attempt, [CATCH] start for dex/team)",
         '_log_story_event(line + _r25_log_suffix(self), "DEXFENCE")' in src
         and "{'box' if _full else 'party'}{_r25_log_suffix(self)}" in src
         and "_r25_log_suffix(mode) if kind in ('dex', 'team') else ''" in src)
    return failed


def mutant(name, old, new):
    src = SM_PATH.read_text(encoding="utf-8")
    n = src.count(old)
    if n != 1:
        raise AssertionError(f"mutant anchor for {name!r} found {n} times: {old!r}")
    mod = types.ModuleType(f"mut_r25_{name}")
    mod.__file__ = str(SM_PATH)
    sys.modules[mod.__name__] = mod
    msrc = src.replace(old, new)
    exec(compile(msrc, f"<mutant {name}>", "exec"), mod.__dict__)
    return mod, msrc


def main() -> int:
    src = SM_PATH.read_text(encoding="utf-8")
    print("K — fence rows through the real helpers")
    k_rows(SM)
    print("\nK11 — the REAL adapter, executed on a shim")
    adapter_rows(SM)
    print("\nA — wiring")
    a_rows(SM, src)

    print("\nM — mutants (each must turn EXACTLY its named rows red)")
    K6 = {f"K6 {g}" for g in ("runway (party 5, fence closed)", "armed hunt", "walking hunt (party 5, fence open)",
                               "PC full", "10-ball reserve (spare 5)", "training", "health")}
    cases = [
        # (M1/M2's extra rows were identified on the first mutant run, and each is a real consequence: RAREEARLY also
        # changes the ADMIT reason K4/K5a check; RAREALL also makes OFF read rare (A2) and admits K5b's RARE-off row.)
        ("M1 RAREEARLY: the exemption admits before the other gates -> every K6 row, and K4/K5a (the admit reason)",
         "rareearly", "    # ---- POST-GYM-1: THE DEX FENCE ---",
         "    if rare:\n        return True, 'FAULT: rare early'\n    # ---- POST-GYM-1: THE DEX FENCE ---",
         K6 | {"K4", "K5a"}),
        ("M2 RAREALL: every verdict counts as rare -> K1a K2a K2b K3 K5b K7 K8 K10, A2, K11a K11d",
         "rareall", '"rare": bool(getattr(verdict, "rare", False)),', '"rare": True,',
         {"K1a", "K2a", "K2b", "K3", "K5b", "K7", "K8", "K10", "A2", "K11a", "K11d"}),
        ("M3 RAREUNGATED: the verdict is read with the flag OFF -> K3 K5b, A2, K11a K11c (a read with RARE off)",
         "rareungated", "    if not rare_on:\n        return None\n", "    if False:\n        return None\n",
         {"K3", "K5b", "A2", "K11a", "K11c"}),
        ("M4 CAP2: the cap stays at 2 with CAP on -> K1b K11c", "cap2",
         '"max_attempts": R25_MAX_ATTEMPTS if cap_on else DEX_CATCH_MAX_ATTEMPTS,',
         '"max_attempts": DEX_CATCH_MAX_ATTEMPTS,', {"K1b", "K11c"}),
        ("M5 NOATTEMPTS: a rare target still meets the cap -> K4 K9 K11b", "noattempts",
         "    if not rare and attempts >= max_attempts:", "    if attempts >= max_attempts:", {"K4", "K9", "K11b"}),
        ("M6 NOTHROWS: a rare target still meets the throws gate -> K5a", "nothrows",
         "expected_throws > DEX_CATCH_MAX_EXPECTED_THROWS and not rare\n",
         "expected_throws > DEX_CATCH_MAX_EXPECTED_THROWS\n", {"K5a"}),
        # ⚠ M7 was pre-registered (2026-09-29-r25cap-PREDICTIONS.md) to turn "the AST row AND the real-rarity row" red,
        # but K9 never ran the adapter, so only A1 went red: that prediction FAILED as written (the graded note says so).
        # K11 (added in the review) runs the real adapter, and is now red under it too.
        ("M7 WRAPPER: the adapter asks about the EncounterInfo -> A1, K11b (rare read as not rare) and K11d (its note)",
         "wrapper", 'else getattr(encounter, "pokemon", None))', "else encounter)", {"A1", "K11b", "K11d"}),
        # The adapter mutants the step 8 review showed were invisible before K11 (its X1, X2, X3, X4, X5, X6):
        ("M8 the verdict is read with RARE OFF (in the adapter) -> A1, K11a, K11c", "adapter_readoff",
         'r25_rarity_verdict(getattr(self, "_r25_rare", False), _rarity.encounter_rarity, _r25_subject)',
         "r25_rarity_verdict(True, _rarity.encounter_rarity, _r25_subject)", {"A1", "K11a", "K11c"}),
        ("M9 the verdict is dropped from the fence inputs -> A1, K11b", "adapter_dropverdict",
         '**r25_catch_inputs(getattr(self, "_r25_cap", False), _r25_verdict),',
         '**r25_catch_inputs(getattr(self, "_r25_cap", False), None),', {"A1", "K11b"}),
        ("M10 the cap reads the RARE flag -> A1, K11c, K11d", "adapter_capfromrare",
         '**r25_catch_inputs(getattr(self, "_r25_cap", False), _r25_verdict),',
         '**r25_catch_inputs(getattr(self, "_r25_rare", False), _r25_verdict),', {"A1", "K11c", "K11d"}),
        ("M11 reset_per_run_state fills _r25_cap from the RARE env -> A4", "reset_swapped",
         'self._r25_cap = _os_team6.environ.get("POKEBOT_R25_CAP") == "1"',
         'self._r25_cap = _os_team6.environ.get("POKEBOT_R25_RARE") == "1"', {"A4"}),
        ("M12 the verdict is never stashed (the log suffix reads 'unread') -> K11b, K11d", "adapter_nostash",
         "            self._r25_last_verdict = _r25_verdict\n", "            pass\n", {"K11b", "K11d"}),
        ("M13 the cap is always ON in the adapter -> A1, K11a, K11d", "adapter_capalways",
         '**r25_catch_inputs(getattr(self, "_r25_cap", False), _r25_verdict),',
         "**r25_catch_inputs(True, _r25_verdict),", {"A1", "K11a", "K11d"}),
        ("N1 a comment edit near the wiring turns NOTHING red", "comment",
         "# RULING 25 (design v2 step 8): the cap of 3 and the rare exemption (flags, default OFF), from ONE pure helper.",
         "# (edited) RULING 25: r25_catch_inputs( is named in this comment only.", set()),
    ]
    for label, name, old, new, want in cases:
        try:
            mod, msrc = mutant(name, old, new)
            red = set(k_rows(mod, "m")) | set(a_rows(mod, msrc, "m")) | set(adapter_rows(mod, "m"))
            check(label, red == want, f"red {sorted(red)}" + ("" if red == want else f" (want {sorted(want)})"))
        except Exception as error:  # noqa: BLE001
            check(label, False, f"{type(error).__name__}: {error}")

    print()
    if FAILURES:
        print(f"FAILED {len(FAILURES)} check(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
