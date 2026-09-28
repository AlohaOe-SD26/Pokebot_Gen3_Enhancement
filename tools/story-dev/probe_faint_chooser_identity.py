r"""GATE (pure + static) — the after-faint chooser decides by IDENTITY, never by index conversion (`#27-ki47range`,
KI-47, 2026-09-28).

WHY: `handle_fainted_pokemon` mapped party indexes through a `gBattlePartyCurrentOrder` snapshot that can hold the
ENEMY's order (`SwitchPartyOrder` has no side check), and its sweep mapped menu slots a SECOND time. MEASURED with
`--driver ki47oor`: an injected stale order froze the chooser at a 4-member party (slots 4/5 unreachable; 685 Downs,
3,045 frames, KI-47 watchdog), and a NATURAL order after one switch sends the wrong mon. The fix
(`modules/faint_chooser.py`) records WHO was chosen and finds that identity in the menu-order party.

  P   the pure plan on the shapes that matter: Foor (4-member party, stale-order victim), Swp (natural non-identity
      menu), a Ninjask/Shedinja DUPLICATE PID, a double battle (living partner on the field), an egg, a chosen mon
      absent or fainted, holes in the party, and every candidate in range.
  W   wiring, by AST (comments and docstrings cannot satisfy or trip it): inside `handle_fainted_pokemon`, every
      `map_battle_party_index` and `_to_menu_order` call sits in the BODY of an `if` testing `_stalemap`; the handler
      calls `faint_chooser_plan` at least twice (the primary target and the sweep), outside those bodies; it reads
      `POKEBOT_KI47_FAULT_STALEMAP`, and that arm is registered in 29.
FAULT ARMS (built in; each must FAIL, except F5, which must PASS):
  F1  plan mutant: identity by PID only (the duplicate-PID case must fail);
  F2  plan mutant: the old double map of the candidates through the order (the Swp case must fail);
  F3  source mutant: an UNGUARDED `map_battle_party_index` call added to the handler;
  F4  source mutant: the `faint_chooser_plan` calls renamed away;
  F5  source mutant: `map_battle_party_index(` only MENTIONED in a comment outside the guard (must NOT fire).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_faint_chooser_identity.py
"""
import ast
import importlib.util
import pathlib
import sys
from types import SimpleNamespace as NS

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
FC = REPO / "sandbox-pokebot" / "modules" / "faint_chooser.py"
BH = REPO / "sandbox-pokebot" / "modules" / "battle_handler.py"
REGISTRY = REPO / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
ARM = "POKEBOT_KI47_FAULT_STALEMAP"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _load(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("faint_chooser_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mon(pid, species, hp=10, egg=False):
    return NS(personality_value=pid, species=NS(index=species), current_hp=hp, is_egg=egg)


# Species indexes are arbitrary distinct ints here; only equality matters.
SHED, POOCH, NINC, WHIS, NINJ, EGG = 303, 286, 301, 311, 302, 412
S = mon(0xAAAA0001, SHED, hp=0)
P, N, W = mon(0x5815089E, POOCH), mon(0x4457D0FB, NINC), mon(0x7E9BB3BA, WHIS)


def plan_table(fc, sink=None):
    ident = fc.mon_identity
    # P1 Foor shape: menu order == field order; the fainted lead is on the field; Whismur chosen.
    t, c, f = fc.faint_chooser_plan([S, P, N, W], fc.field_identities([S, None]), ident(W))
    check((t, c, f) == (3, {1, 2, 3}, {0}), f"P1 Foor shape -> target 3, candidates {{1,2,3}} (got {t}, {c}, {f})", sink)
    # P2 Swp shape: after one switch the MENU shows [Shed, Ninc, Whis, Pooch]; Whismur (field slot 0) is menu slot 2.
    t, c, f = fc.faint_chooser_plan([S, N, W, P], fc.field_identities([S]), ident(W))
    check((t, c) == (2, {1, 2, 3}), f"P2 Swp shape -> target 2 (Whismur's MENU slot), candidates {{1,2,3}} (got {t}, {c})",
          sink)
    # P3 duplicate PID: a Ninjask on the field and its Shedinja on the bench share a PID (CreateShedinja copies it).
    ninjask, shedinja = mon(0x12345678, NINJ), mon(0x12345678, SHED)
    t, c, f = fc.faint_chooser_plan([ninjask, shedinja, S], fc.field_identities([ninjask]), ident(shedinja))
    check((t, c, f) == (1, {1}, {0}), f"P3 Ninjask/Shedinja duplicate PID -> the Shedinja stays a candidate "
          f"(got {t}, {c}, {f})", sink)
    # P4 double battle: slot 0 fainted and slot 1 the living partner, both on the field; Nincada chosen.
    a0 = mon(0x1, POOCH, hp=0)
    t, c, f = fc.faint_chooser_plan([a0, W, N, P], fc.field_identities([a0, W]), ident(N))
    check((t, c, f) == (2, {2, 3}, {0, 1}), f"P4 double battle -> the living partner is excluded (got {t}, {c}, {f})",
          sink)
    # P5 an egg is never a candidate, even when chosen.
    egg = mon(0x2, EGG, egg=True)
    t, c, f = fc.faint_chooser_plan([S, egg, W], fc.field_identities([S]), ident(egg))
    check((t, c) == (None, {2}), f"P5 egg chosen -> no target, candidates {{2}} (got {t}, {c})", sink)
    # P6 the chosen mon is absent, or fainted: no target (the caller falls back to a candidate).
    t, c, _ = fc.faint_chooser_plan([S, P], fc.field_identities([S]), ident(W))
    check(t is None and c == {1}, f"P6a chosen absent -> no target (got {t}, {c})", sink)
    t, c, _ = fc.faint_chooser_plan([S, P], fc.field_identities([S]), ident(S))
    check(t is None, f"P6b chosen fainted -> no target (got {t})", sink)
    # P7 holes and garbage never crash and never become candidates.
    t, c, f = fc.faint_chooser_plan([S, None, NS(), W], fc.field_identities([S, None, NS()]), ident(W))
    check((t, c) == (3, {3}), f"P7 holes/unreadable entries skipped (got {t}, {c})", sink)
    # P8 every candidate is in range, whatever the party.
    parties = [[S, P, N, W], [S, N, W, P], [S, W], [S, P, N, W, mon(9, 1), mon(10, 2)]]
    ok = all(all(0 <= s < len(pt) for s in fc.faint_chooser_plan(pt, fc.field_identities([S]), None)[1]) for pt in parties)
    check(ok, "P8 every candidate slot < len(party_in_menu)", sink)


def _handler(tree):
    return next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "handle_fainted_pokemon"),
                None)


def _is_stale_if(node) -> bool:
    return isinstance(node, ast.If) and any(isinstance(n, ast.Name) and n.id == "_stalemap" for n in ast.walk(node.test))


def _guarded_ids(fn) -> set:
    """ids of every node inside the BODY (not the orelse) of an `if` testing `_stalemap`."""
    ids = set()
    for n in ast.walk(fn):
        if _is_stale_if(n):
            for s in n.body:
                ids.update(id(x) for x in ast.walk(s))
    return ids


def _call_name(c) -> str:
    f = c.func
    return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")


def wiring(src: str, sink=None):
    fn = _handler(ast.parse(src))
    check(fn is not None, "W0 handle_fainted_pokemon found", sink)
    if fn is None:
        return
    guarded = _guarded_ids(fn)
    calls = [c for c in ast.walk(fn) if isinstance(c, ast.Call)]
    conv = [c for c in calls if _call_name(c) in ("map_battle_party_index", "_to_menu_order")]
    loose = [c.lineno for c in conv if id(c) not in guarded]
    check(not loose, f"W1 every index conversion in the handler is inside an `if _stalemap:` body (unguarded at {loose})",
          sink)
    plans = [c for c in calls if _call_name(c) == "faint_chooser_plan" and id(c) not in guarded]
    check(len(plans) >= 2, f"W2 the handler calls faint_chooser_plan outside the fault arm >= 2 times (got {len(plans)})",
          sink)
    reads_arm = any(isinstance(n, ast.Constant) and n.value == ARM for n in ast.walk(fn))
    check(reads_arm, f"W3 the handler reads {ARM}", sink)


def main() -> int:
    print("P — the pure plan")
    fc = _load(FC)
    plan_table(fc)
    print("W — wiring")
    src = BH.read_text(encoding="utf-8")
    wiring(src)
    reg = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    check(ARM in reg, f"W4 {ARM} is registered in 29-DISABLED-FEATURES-REGISTRY.md")

    print("F — fault arms (each requires the UNMUTATED subject to pass the same check first, so none is vacuous)")
    base_p: list = []
    plan_table(fc, base_p)
    base_w: list = []
    wiring(src, base_w)
    # F1: identity by PID only.
    m1 = _load(FC)
    m1.mon_identity = lambda x: None if x is None or not hasattr(x, "personality_value") else (x.personality_value, 0)
    sink: list = []
    plan_table(m1, sink)
    check(not base_p and any(s.startswith("P3") for s in sink),
          f"F1 a PID-only identity FAILS P3 (it failed: {[s[:3] for s in sink]})")
    # F2: the old sweep - candidates double-mapped through the battle order [2,1,0,3,4,5].
    m2 = _load(FC)
    real = m2.faint_chooser_plan
    order = [2, 1, 0, 3, 4, 5]

    def double_mapped(party, on_field, chosen):
        t, c, f = real(party, on_field, chosen)
        return t, {order.index(s) for s in c}, f

    m2.faint_chooser_plan = double_mapped
    sink = []
    plan_table(m2, sink)
    check(not base_p and any(s.startswith("P2") for s in sink),
          f"F2 a double-mapped sweep FAILS P2 (it failed: {[s[:3] for s in sink]})")
    fn = _handler(ast.parse(src))
    body_line = fn.body[-1].lineno if fn is not None else 1
    lines = src.splitlines()
    indent = " " * (len(lines[body_line - 1]) - len(lines[body_line - 1].lstrip()))
    # F3: an unguarded conversion at the end of the handler body.
    m3 = "\n".join(lines[:body_line - 1] + [f"{indent}new_lead_index = battle_state.map_battle_party_index(new_lead_index)"]
                   + lines[body_line - 1:])
    sink = []
    wiring(m3, sink)
    check(not base_w and any(s.startswith("W1") for s in sink), "F3 an unguarded map_battle_party_index FAILS W1")
    # F4: the plan calls renamed away.
    sink = []
    wiring(src.replace("faint_chooser_plan(", "faint_chooser_plan_x("), sink)
    check(not base_w and any(s.startswith("W2") for s in sink), "F4 removing the faint_chooser_plan calls FAILS W2")
    # F5: a comment mention outside the guard must NOT fire.
    m5 = "\n".join(lines[:body_line - 1] + [f"{indent}# never call battle_state.map_battle_party_index(i) here"]
                   + lines[body_line - 1:])
    sink = []
    wiring(m5, sink)
    check(not sink, f"F5 a comment that MENTIONS map_battle_party_index( passes W (got {sink})")

    print()
    if failures:
        print(f"FAIL — {len(failures)} check(s) failed")
        return 1
    print("PASS — the faint chooser decides by identity; every conversion is confined to the fault arm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
