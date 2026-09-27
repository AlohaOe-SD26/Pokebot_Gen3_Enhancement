r"""GATE — USER RULING 19: teach an OWNED TM when a gym keeps winning (`#26-gymtmteach`, 2026-09-26), DESIGN 4.

WHY: the planner decides what a SINGLE-USE item is spent on and which move a trained mon loses. Three earlier designs
were refuted before any drive (a decomp read, two observe-only runs on real fixtures, an adversarial review); every
check below pins one of the rules that came out of that, so a later edit cannot quietly restore a refuted design.

  G1  THE WALL (PURE): `faints_by_foe` counts, per foe species, how many of OUR mons it was facing at their last
      decision; `wall_species` sums that over the last RECENT_LOSSES leader losses, needs two, ignores non-roster
      species, and breaks a tie toward the most recent loss. ⛔ Not the KO count (design 1), not the last foe (design 3).
  G1b THE RECORDER + FILING (text/AST): `battle_action_selection` writes `TURN_FOE` species AND the decision log INSIDE
      the [TURN] instrumentation's try; `on_battle_started` resets both and names the battle (`boss_for_enemy_party`);
      `on_battle_ended` files faints ONLY for a leader battle and marks taught moves seen (`note_boss_battle`);
      `reset_per_run_state` resets the new per-run fields.
  G1c THE RECORDER RUNS (BEHAVIOUR, not position): the REAL body of the [TURN] instrumentation's try is extracted and
      executed as a function with stub battle objects and NO except — it must not raise, must append exactly one
      decision naming the chosen move and the foe, and must still emit its `[TURN` event. ‼ Added after an adversarial
      review found the first recorder read `_what` BEFORE its assignment: an UnboundLocalError on every decision,
      swallowed by the try — killing the recorder AND the pre-existing [TURN] telemetry for every battle, while G1b
      (an "is it inside the try" check) passed. A position check cannot see a binding-ORDER bug; running it can.
  G2  THE SLOT (PURE): empty > status > strictly dominated > weakest non-STAB; NEVER an HM, NEVER an undominated STAB
      move, NEVER the last damaging move.
  G3  THE PAIR (PURE, synthetic Torchic-core party vs Skarmory): a plan exists and goes to LOUDRED (the only mon in the
      best-resisting group that can learn a 2x TM); Blaziken (2x incoming) is refused as "never fielded"; a mon with a
      CREDIBLE answer is refused, but a neutral STAB move is NOT an answer; a status TM, a banned move, a non-plain-hit
      effect, a latched TM, a hunted counter, a mon below the floor and a hopeless duel are each refused BY NAME.
  G4  WIRING (AST): the hook sits in `_prepare_for_fight` under `losses >= 2`, after maintenance, before boss mode.
  G5  DATA: roster keys are fight-config names; every species exists; levels and IVs are sane; no double-battle boss.
  G6  FAIL-OPEN + LATCH + WAIT (stubbed): an error is REPORTED, never raised; the latch is written BEFORE the act; a
      second teach for the same boss WAITS until the first taught move is seen used; losses < 2 / no roster ⇒ not armed.
  G7  the arms are read in production and registered in 29.
  G8  NOT A LEVER-KILLER (text + a stubbed call): `_boss_plan_is_hopeless` skips taught moves — a party whose ONLY answer
      to the ace is a TAUGHT Rock Tomb is still judged hopeless; `pc_trip` protects taught PIDs from deposits.
  G9  `boss_for_enemy_party`: Winona's exact roster ⇒ "Winona"; a gym trainer sharing species ⇒ None.
  G10 THE TEACH-AWARE CLOSE (AST): `_leave_teach_menus` reads the learn-move state INSIDE its one loop, answers A on
      ConfirmCancellation, and never hands off to the plain B-only close (MEASURED: that hand-off ping-ponged the two
      prompts and left PARTY_MENU — drive Q4, 2026-09-26).
FAULT ARMS (built in): a slot chooser that overwrites an HM (G2); a last-foe-only wall (G1); the recorder outside the try
(G1b); the recorder ABOVE `_what` — the shipped bug (G1c); the hook after boss mode (G4); a planner without the reach filter (G3); a hopeless scan that counts taught moves
(G8); the two-phase close that failed drive Q4 (G10); a planner that raises (G6 must still pass — it is the recovery
being proven).

Run: cd tools/story-dev && PYTHONUTF8=1 py -3.12 probe_gymtm_teach.py
"""
from __future__ import annotations

import ast
import io
import os
import pathlib
import sys
import tokenize
import types

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "sandbox-pokebot"))
sys.stdout.reconfigure(encoding="utf-8")

from modules.story import gym_tm_teach as G  # noqa: E402

STORY = ROOT / "sandbox-pokebot" / "plugins" / "custom_modes" / "story_mode.py"
BAS = ROOT / "sandbox-pokebot" / "modules" / "battle_action_selection.py"
PCTRIP = ROOT / "sandbox-pokebot" / "modules" / "story" / "pc_trip.py"
MODULE = ROOT / "sandbox-pokebot" / "modules" / "story" / "gym_tm_teach.py"
REGISTRY = ROOT / "PROJECT KNOWLEDGE" / "29-DISABLED-FEATURES-REGISTRY.md"
failures: list = []


def check(cond, msg, sink=None):
    sink = failures if sink is None else sink
    if not cond:
        sink.append(msg)
    if sink is failures:
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")


def _strip_comments(src: str) -> str:
    return tokenize.untokenize(t for t in tokenize.generate_tokens(io.StringIO(src).readline)
                               if t.type != tokenize.COMMENT)


def _method(src: str, name: str) -> str:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return _strip_comments(ast.get_source_segment(src, node) or "")
    return ""


def M(name, type_, power, hm=False, prio=0):
    return G.MoveView(name=name, type=type_, power=power, is_hm=hm, priority=prio)


WINONA = G.GYM_ROSTERS["Winona"]


# ---- G1 ------------------------------------------------------------------------------------------------------------

def g1(faints_fn, wall_fn, sink=None):
    log = [(1, "Blaziken", "UseMove:Blaze Kick", "Swablu"), (1, "Blaziken", "UseMove:Blaze Kick", "Skarmory"),
           (2, "Loudred", "UseMove:Stomp", "Skarmory"), (3, "Mightyena", "UseMove:Bite", "Skarmory"),
           (4, "Swellow", "UseMove:Wing Attack", "Skarmory"), (5, "Ninjask", "UseMove:Fury Cutter", "Altaria")]
    check(faints_fn(log) == {"Skarmory": 4, "Altaria": 1},
          "G1 faints_by_foe: each of OUR mons counts once, against the foe of its LAST decision", sink)
    four_then_one = [{"Skarmory": 4, "Altaria": 1}, {"Skarmory": 4, "Altaria": 1}]
    check(wall_fn(four_then_one, WINONA) == "Skarmory",
          "G1 Skarmory downs four, Altaria finishes the fifth ⇒ the wall is SKARMORY (not the last foe)", sink)
    check(wall_fn([{"Skarmory": 3}], WINONA) is None, f"G1 one loss is not enough (needs {G.MIN_LOSSES_FOR_A_WALL})",
          sink)
    check(wall_fn([{"Skarmory": 2}, {"Altaria": 2}], WINONA) == "Altaria", "G1 a tie goes to the MOST RECENT loss", sink)
    check(wall_fn([{"Doduo": 5}, {"Skarmory": 1}, {"Kingdra": 4}, {"Skarmory": 1}], WINONA) == "Skarmory",
          "G1 species outside the roster are ignored", sink)
    check(wall_fn([{"Altaria": 5}, {"Altaria": 5}, {"Skarmory": 2}, {"Skarmory": 2}, {"Skarmory": 2}], WINONA)
          == "Skarmory", f"G1 only the last {G.RECENT_LOSSES} leader losses count", sink)
    check(wall_fn([], WINONA) is None and wall_fn([{}, {}], WINONA) is None, "G1 nothing recorded ⇒ None", sink)


def g1b(bas: str, story: str, sink=None):
    inside = False
    for node in ast.walk(ast.parse(bas)):
        if isinstance(node, ast.Try) and node.handlers:
            seg = ast.get_source_segment(bas, node) or ""
            if ('TURN_FOE["species"] = ' in seg and 'TURN_FOE["log"].append(' in seg and "[TURN " in seg
                    and "TURN_FOE_LOG_MAX" in seg):
                inside = True
    check(inside, "G1b the species AND the bounded decision log are written INSIDE the [TURN] instrumentation's try", sink)
    started, ended = _method(story, "on_battle_started"), _method(story, "on_battle_ended")
    per_run = _method(story, "reset_per_run_state")
    check('TURN_FOE["species"] = None' in started and 'TURN_FOE["log"] = []' in started
          and "boss_for_enemy_party(" in started and "if encounter is None:" in started,
          "G1b on_battle_started resets the recorder and names a TRAINER battle's boss from the enemy party", sink)
    check('if getattr(self, "_boss_battle", None):' in ended and "faints_by_foe(" in ended and "note_boss_battle(" in ended
          and "self._boss_battle = None" in ended,
          "G1b on_battle_ended files faints ONLY for a leader battle, marks taught moves seen, clears the battle", sink)
    check(all(f in per_run for f in ("self._loss_foe_history", "self._gym_tm_taught", "self._gym_tm_taught_moves",
                                     "self._boss_battle")), "G1b reset_per_run_state resets every new per-run field", sink)


def g1c(bas: str, sink=None):
    """Run the real try-body of the [TURN] instrumentation with stubs, with no except around it."""
    import textwrap

    import modules.battle_action_selection as BASM
    import modules.debug_logger as DL
    from modules.battle_strategies import TurnAction

    body_src = None
    for node in ast.walk(ast.parse(bas)):
        if isinstance(node, ast.Try) and node.handlers:
            seg = ast.get_source_segment(bas, node) or ""
            if 'TURN_FOE["log"].append(' in seg and "[TURN " in seg:
                first, last = node.body[0], node.body[-1]
                lines = bas.splitlines()
                body_src = "\n".join(lines[first.lineno - 1:last.end_lineno])
    if body_src is None:
        check(False, "G1c the [TURN] instrumentation try-body was found", sink)
        return
    fn_src = "def _turn_body(battle_state, action, index, battler_index):\n" + textwrap.indent(
        textwrap.dedent(body_src), "    ")
    ns = dict(vars(BASM))
    events = []
    real_event = DL.event
    saved = (dict(BASM.TURN_FOE), list(BASM.TURN_FOE.get("log") or ()))
    try:
        DL.event = lambda msg, *a, **k: events.append(str(msg))
        BASM.TURN_FOE["species"] = None
        BASM.TURN_FOE["log"] = []
        exec(compile(fn_src, "<turn-try-body>", "exec"), ns)
        mon = types.SimpleNamespace(
            species=types.SimpleNamespace(name="Loudred"), personality_value=0xB2768B68, level=31, current_hp=90,
            total_hp=97, status_permanent=None, status_temporary=[],
            moves=[types.SimpleNamespace(move=types.SimpleNamespace(name="Shock Wave"), pp=20)])
        foe = types.SimpleNamespace(species=types.SimpleNamespace(name="Skarmory"), level=31, current_hp=89,
                                    total_hp=89, status_permanent=None, status_temporary=[])
        state = types.SimpleNamespace(own_side=types.SimpleNamespace(left_battler=mon, right_battler=None),
                                      opponent=types.SimpleNamespace(left_battler=foe), current_turn=3)
        raised = None
        try:
            ns["_turn_body"](state, TurnAction.UseMove, 0, 0)
        except Exception as error:  # noqa: BLE001 - the failure under test
            raised = error
        log = list(BASM.TURN_FOE["log"])
        # A FULL log must drop its OLDEST entry and keep this decision (the wall is read from each mon's LAST one).
        BASM.TURN_FOE["log"] = [("old", "Old", "UseMove:Old", "Swablu")] * BASM.TURN_FOE_LOG_MAX
        try:
            ns["_turn_body"](state, TurnAction.UseMove, 0, 0)
        except Exception:  # noqa: BLE001 - reported through the checks below
            pass
        full = list(BASM.TURN_FOE["log"])
    finally:
        DL.event = real_event
        BASM.TURN_FOE["species"], BASM.TURN_FOE["log"] = saved[0].get("species"), saved[1]
    check(raised is None, f"G1c the real try-body runs WITHOUT raising (raised: {type(raised).__name__ if raised else None})",
          sink)
    check(len(log) == 1 and log[0][0] == 0xB2768B68 and "Shock Wave" in str(log[0][2]) and log[0][3] == "Skarmory",
          f"G1c it appends ONE decision: our pid, the chosen move, the foe ({log[:1]})", sink)
    check(any("[TURN 3]" in e and "Shock Wave" in e and "Skarmory" in e for e in events),
          f"G1c the pre-existing [TURN] event still fires ({len(events)} event(s))", sink)
    check(len(full) == BASM.TURN_FOE_LOG_MAX and full[-1][3] == "Skarmory",
          "G1c a FULL log drops its oldest entry and KEEPS the newest decision (never freezes at the cap)", sink)


# ---- G2 ------------------------------------------------------------------------------------------------------------

def g2(fn, sink=None):
    check(fn((M("Tackle", "Normal", 35), None, None, None), ("Normal",)) == (1, "<empty>"), "G2 an empty slot first", sink)
    check(fn((M("Cut", "Normal", 50, hm=True), M("Growl", "Normal", 0), M("Bite", "Dark", 60), M("Tackle", "Normal", 35)),
             ("Normal",)) == (1, "Growl"), "G2 a status move before any damaging move", sink)
    loudred = (M("Pound", "Normal", 40), M("Uproar", "Normal", 50), M("Astonish", "Ghost", 30), M("Stomp", "Normal", 65))
    check(fn(loudred, ("Normal",)) == (0, "Pound"), "G2 a strictly DOMINATED move (Pound beside Stomp) first", sink)
    sceptile = (M("Rock Smash", "Fighting", 20, hm=True), M("Pursuit", "Dark", 40), M("Leaf Blade", "Grass", 70),
                M("Quick Attack", "Normal", 40, prio=1))
    check(fn(sceptile, ("Grass",)) == (1, "Pursuit"),
          "G2 four types, no status: the weakest non-STAB; a priority move loses the tie", sink)
    blaziken = (M("Scratch", "Normal", 40), M("Blaze Kick", "Fire", 85), M("Double Kick", "Fighting", 30),
                M("Rock Smash", "Fighting", 20, hm=True))
    check(fn(blaziken, ("Fire", "Fighting")) == (0, "Scratch"),
          "G2 Blaziken keeps Double Kick (STAB, not dominated by the weaker Rock Smash); Scratch goes", sink)
    all_hm = (M("Surf", "Water", 95, hm=True), M("Strength", "Normal", 80, hm=True), M("Cut", "Normal", 50, hm=True),
              M("Rock Smash", "Fighting", 20, hm=True))
    check(fn(all_hm, ("Water",)) is None, "G2 NEVER an HM move — four HMs ⇒ no slot", sink)
    only_stab = (M("Leaf Blade", "Grass", 70), M("Rock Smash", "Fighting", 20, hm=True), M("Cut", "Normal", 50, hm=True),
                 M("Strength", "Normal", 80, hm=True))
    check(fn(only_stab, ("Grass",)) is None, "G2 NEVER an undominated STAB move", sink)


# ---- G3 ------------------------------------------------------------------------------------------------------------

def _mon(i, species, level, types_, moves, learn, *, atk=60, spa=60, hp=100, dfn=60, spd=60, spe=60, pid=None):
    return G.MonView(index=i, pid=pid if pid is not None else 0x1000 + i, species=species, level=level, types=types_,
                     attack=atk, special_attack=spa, moves=moves, learnable_tms=frozenset(learn), hp=hp, defence=dfn,
                     special_defence=spd, speed=spe)


TMS = [G.TmView("TM34", "Shock Wave", "Electric", 60, 1.0, "ALWAYS_HIT"),
       G.TmView("TM50", "Overheat", "Fire", 140, 0.9, "OVERHEAT"),
       G.TmView("TM39", "Rock Tomb", "Rock", 50, 0.8, "SPEED_DOWN_HIT"),
       G.TmView("TM08", "Bulk Up", "Fighting", 0, 1.0, "BULK_UP")]


def _torchic_party():
    """Stats from the real `devon_scope_got.ss1` party (the fixture the drive uses), rounded."""
    return [
        _mon(0, "Blaziken", 39, ("Fire", "Fighting"),
             (M("Scratch", "Normal", 40), M("Blaze Kick", "Fire", 85), M("Double Kick", "Fighting", 30),
              M("Rock Smash", "Fighting", 20, hm=True)), {"TM50", "TM39"}, atk=120, spa=108, hp=125, dfn=72, spd=72,
             spe=80),
        _mon(1, "Loudred", 31, ("Normal",),
             (M("Pound", "Normal", 40), M("Uproar", "Normal", 50), M("Astonish", "Ghost", 30), M("Stomp", "Normal", 65)),
             {"TM34", "TM50"}, atk=55, spa=54, hp=97, dfn=36, spd=36, spe=39),
        _mon(2, "Mightyena", 35, ("Dark",),
             (M("Tackle", "Normal", 35), M("Scary Face", "Normal", 0), M("Sand-attack", "Ground", 0),
              M("Bite", "Dark", 60)), set(), atk=80, spa=50, hp=105, dfn=60, spd=55, spe=65),
        _mon(3, "Zigzagoon", 3, ("Normal",), (M("Tackle", "Normal", 35), M("Growl", "Normal", 0),
                                              M("Surf", "Water", 95, hm=True), None), {"TM34"}, hp=15),
    ]


def g3(plan_fn, sink=None):
    plan, why = plan_fn("Winona", WINONA, "Skarmory", _torchic_party(), TMS, set(), set())
    check(plan is not None and plan.species == "Loudred" and plan.tm in ("TM34", "TM50") and plan.replaced == "Pound",
          f"G3 Skarmory wall ⇒ a 2x TM → LOUDRED replacing Pound (got "
          f"{None if plan is None else (plan.tm, plan.species, plan.replaced, plan.share)})", sink)
    check(any("Blaziken would never be fielded against Skarmory" in w for w in why),
          "G3 REACH: Blaziken (2x incoming from Flying) is refused as never fielded", sink)
    check(any("Zigzagoon" in w and ("bench" in w or "floor" in w) for w in why),
          "G3 the L3 Zigzagoon is refused (bench / floor) with a reason", sink)
    check(any("TM08" in w and "not a damaging move" in w for w in why), "G3 a status TM is refused by name", sink)
    swablu_party = _torchic_party()
    plan, why = plan_fn("Winona", WINONA, "Swablu", swablu_party, TMS, set(), set())
    check(not any("Mightyena already has a credible answer" in w for w in why),
          "G3 a NEUTRAL STAB move (Mightyena's Bite vs Swablu) is NOT a credible answer — 2x is required", sink)
    answered = _torchic_party()
    answered[1] = _mon(1, "Loudred", 31, ("Normal",), (M("Thunder Punch", "Electric", 75), M("Uproar", "Normal", 50),
                                                       M("Astonish", "Ghost", 30), M("Stomp", "Normal", 65)),
                       {"TM34", "TM50"}, atk=55, spa=54, hp=97, dfn=36, spd=36, spe=39)
    plan, why = plan_fn("Winona", WINONA, "Skarmory", answered, TMS, set(), set())
    check(plan is None and any("Loudred already has a credible answer" in w for w in why),
          "G3 a mon that already has a CREDIBLE 2x answer is refused", sink)
    plan, why = plan_fn("Winona", WINONA, "Skarmory", _torchic_party(), TMS, {("Winona", "TM34"), ("Winona", "TM50")},
                        set())
    check(plan is None and any("already tried" in w for w in why), "G3 a LATCHED (boss, TM) is never re-planned", sink)
    plan, why = plan_fn("Winona", WINONA, "Skarmory", _torchic_party(), TMS, set(), {0x1001})
    check((plan is None or plan.species != "Loudred") and any("hunted counter" in w for w in why),
          "G3 a HUNTED COUNTER (by PID) is never the recipient, and the refusal names it", sink)
    plan, why = plan_fn("Winona", WINONA, "Skarmory", _torchic_party(), TMS, set(), set(), ("Shock Wave", "Overheat"))
    check(plan is None and any("banned move" in w for w in why), "G3 a BANNED move is never taught", sink)
    fp = [G.TmView("TM01", "Focus Punch", "Fighting", 150, 1.0, "FOCUS_PUNCH")]
    plan, why = plan_fn("Winona", WINONA, "Skarmory", _torchic_party(), fp, set(), set())
    check(plan is None and any("not a plain hit" in w for w in why), "G3 a non-plain-hit effect is never taught", sink)
    low = _torchic_party()
    low[1] = _mon(1, "Loudred", 28, ("Normal",), low[1].moves, {"TM34", "TM50"}, atk=50, spa=48, hp=85, dfn=32, spd=32,
                  spe=35)
    plan, why = plan_fn("Winona", WINONA, "Skarmory", low, TMS, set(), set())
    check(plan is None and any("below the floor" in w for w in why), "G3 a recipient below the level floor is refused",
          sink)
    frail = _torchic_party()
    frail[1] = _mon(1, "Loudred", 31, ("Normal",), frail[1].moves, {"TM34"}, atk=55, spa=12, hp=20, dfn=10, spd=10,
                    spe=5)
    plan, why = plan_fn("Winona", WINONA, "Skarmory", frail, TMS, set(), set())
    check(plan is None and any("deals only" in w for w in why), "G3 a HOPELESS duel (share < MIN_SHARE) is refused", sink)
    combusken = [_mon(0, "Combusken", 33, ("Fire", "Fighting"),
                      (M("Scratch", "Normal", 40), M("Ember", "Fire", 40), M("Double Kick", "Fighting", 30),
                       M("Peck", "Flying", 35)), {"TM50"}),
                 _mon(1, "Grumpig", 33, ("Psychic",), (M("Psybeam", "Psychic", 65), None, None, None), set())]
    plan, why = plan_fn("Winona", WINONA, "Skarmory", combusken, TMS, set(), set())
    check(plan is None or plan.tm != "TM50" or plan.species != "Combusken",
          "G3 NEVER Overheat onto the Torchic line before Blaze Kick", sink)


# ---- G4 ------------------------------------------------------------------------------------------------------------

def g4(src: str, sink=None):
    body = _method(src, "_prepare_for_fight")
    call = "yield from maybe_teach_gym_tm(self, cfg, losses)"
    check(body.count(call) == 1, "G4 `_prepare_for_fight` calls `maybe_teach_gym_tm(self, cfg, losses)` exactly once",
          sink)
    i_call = body.find(call)
    i_guard = body.rfind("if losses >= 2 and cfg.get(\"name\"):", 0, max(i_call, 0))
    i_maint = body.find("yield from self._maintain_lagging_battler(target)")
    i_boss = body.find("boss_mode = False")
    i_ladder = body.find("self._counter_ladder(")
    check(i_call > 0 and 0 < i_guard < i_call, "G4 … under `if losses >= 2 and cfg.get(\"name\")`", sink)
    check(0 < i_maint < i_call, "G4 … AFTER `_maintain_lagging_battler`", sink)
    check(0 < i_call < i_boss and (i_ladder < 0 or i_call < i_ladder),
          "G4 … BEFORE the boss-mode / counter-ladder block", sink)


# ---- G5 ------------------------------------------------------------------------------------------------------------

def g5(src: str):
    from modules.pokemon import get_species_by_name

    names = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and k.value == "name" and isinstance(v, ast.Constant):
                    names.add(v.value)
    check(set(G.GYM_ROSTERS) <= names, f"G5 every roster key is a fight config `name` ({sorted(G.GYM_ROSTERS)})")
    check("Tate & Liza" not in G.GYM_ROSTERS, "G5 no DOUBLE-battle boss (Tate & Liza: the turn record sees one foe)")
    bad = []
    for boss, roster in G.GYM_ROSTERS.items():
        for m in roster:
            try:
                get_species_by_name(m.species)
            except Exception:  # noqa: BLE001 - reported below
                bad.append(f"{boss}:{m.species}")
            if not (1 <= m.level <= 100 and 0 <= m.iv <= 31 and m.moves):
                bad.append(f"{boss}:{m.species}@L{m.level}/iv{m.iv}")
    check(not bad, f"G5 every roster species exists; levels, IVs and damaging moves are sane ({bad or 'all'})")


# ---- G6 ------------------------------------------------------------------------------------------------------------

def _drain(gen):
    try:
        while True:
            next(gen)
    except StopIteration as stop:
        return stop.value


def g6():
    from modules.map_data import MapRSE

    key = MapRSE.FORTREE_CITY_GYM.value
    cfg = {"name": "Winona", "keys": [key]}

    def fresh():
        return types.SimpleNamespace(
            _loss_foe_history={key: [(1, "Winona", {"Skarmory": 4, "Altaria": 1}), (2, "Winona", {"Skarmory": 5})]},
            _hunted_counter_pids=set(), _gym_tm_taught=set(), _gym_tm_taught_moves={})

    real = (G.owned_tms, G.mon_view, G._controllable_overworld)
    import modules.pokemon_party as PP

    real_party = PP.get_party
    try:
        def boom():
            raise RuntimeError("bag unreadable")

        G.owned_tms = boom
        G._controllable_overworld = lambda: True
        mode, rep, raised = fresh(), {}, None
        try:
            _drain(G.maybe_teach_gym_tm(mode, cfg, 2, rep))
        except Exception as error:  # noqa: BLE001 - the failure under test
            raised = error
        check(raised is None and rep.get("outcome") == "error" and "RuntimeError" in str(rep.get("error")),
              "G6 an error inside the planner is REPORTED (outcome=error), never raised — fail-open")
        party = _torchic_party()
        G.owned_tms = lambda: (TMS, {t.tm: t.tm for t in TMS})
        G.mon_view = lambda i, p, items: party[i]
        PP.get_party = lambda: [object() for _ in party]
        os.environ["POKEBOT_GYMTM_FAULT_NOTEACH"] = "1"
        mode, rep = fresh(), {}
        _drain(G.maybe_teach_gym_tm(mode, cfg, 2, rep))
        planned_tm = str(rep.get("plan", "")).split(" ")[0]
        check(bool(planned_tm) and ("Winona", planned_tm) in mode._gym_tm_taught
              and str(rep.get("outcome", "")).startswith("planned, act skipped"),
              f"G6 the latch is written BEFORE the act (NOTEACH: latched {planned_tm}, not acted)")
        mode, rep = fresh(), {}
        mode._gym_tm_taught_moves[(0x1001, "Shock Wave")] = {"boss": "Winona", "wall": "Skarmory", "species": "Loudred",
                                                              "used": False}
        _drain(G.maybe_teach_gym_tm(mode, cfg, 2, rep))
        check(str(rep.get("outcome", "")).startswith("waiting") and not rep.get("plan"),
              "G6 a second teach for the same boss WAITS until the first taught move is seen used")
        G.note_boss_battle(mode, "Winona", [(0x1001, "Loudred", "UseMove:Shock Wave(pp19)", "Skarmory")])
        check(mode._gym_tm_taught_moves[(0x1001, "Shock Wave")]["used"] is True,
              "G6 note_boss_battle marks it SEEN when the log shows it chosen vs its wall")
        mode2 = fresh()
        mode2._gym_tm_taught_moves[(0x1001, "Shock Wave")] = {"boss": "Winona", "wall": "Skarmory", "used": False}
        G.note_boss_battle(mode2, "Winona", [(0x1001, "Loudred", "UseMove:Shock Wave(pp19)", "Altaria")])
        check(mode2._gym_tm_taught_moves[(0x1001, "Shock Wave")]["used"] is False,
              "G6 … and NOT when it was chosen against a different foe")
        mode, rep = fresh(), {}
        mode._loss_foe_history[key] += [(3, "Winona", {"Skarmory": 5}), (4, "Winona", {"Skarmory": 5})]
        mode._gym_tm_taught_moves[(0x1001, "Shock Wave")] = {"boss": "Winona", "wall": "Skarmory", "species": "Loudred",
                                                              "used": False, "losses_at_teach": 1}
        _drain(G.maybe_teach_gym_tm(mode, cfg, 2, rep))
        check(not str(rep.get("outcome", "")).startswith("waiting") and rep.get("released"),
              f"G6 … but the wait is RELEASED after {G.WAIT_RELEASE_LOSSES} more leader losses without seeing it "
              f"(outcome {rep.get('outcome')!r})")
        mode, rep = fresh(), {}
        _drain(G.maybe_teach_gym_tm(mode, cfg, 1, rep))
        check(rep.get("outcome") == "not armed", "G6 losses < 2 ⇒ not armed")
        mode, rep = fresh(), {}
        _drain(G.maybe_teach_gym_tm(mode, {"name": "Roxanne", "keys": [key]}, 5, rep))
        check(rep.get("outcome") == "not armed", "G6 a boss without a roster ⇒ not armed")
        mode, rep = fresh(), {}
        mode._loss_foe_history = {key: [(1, None, {"Skarmory": 5}), (2, None, {"Skarmory": 5})]}
        _drain(G.maybe_teach_gym_tm(mode, cfg, 2, rep))
        check(str(rep.get("outcome", "")).startswith("no wall yet"),
              "G6 losses to the GYM'S TRAINERS (not the leader) never name a wall")
        G._controllable_overworld = lambda: False
        mode, rep = fresh(), {}
        os.environ.pop("POKEBOT_GYMTM_FAULT_NOTEACH", None)
        _drain(G.maybe_teach_gym_tm(mode, cfg, 2, rep))
        check(str(rep.get("outcome", "")).startswith("not in a controllable overworld") and not mode._gym_tm_taught,
              "G6 not controllable ⇒ skipped WITHOUT spending the latch")
    finally:
        os.environ.pop("POKEBOT_GYMTM_FAULT_NOTEACH", None)
        G.owned_tms, G.mon_view, G._controllable_overworld = real
        PP.get_party = real_party


# ---- G7 ------------------------------------------------------------------------------------------------------------

def g7():
    code = _strip_comments(MODULE.read_text(encoding="utf-8"))
    reg = REGISTRY.read_text(encoding="utf-8")
    for arm in ("POKEBOT_GYMTM_FAULT_NOTEACH", "POKEBOT_GYMTM_FAULT_BUDGET"):
        check(f'os.environ.get("{arm}")' in code and f"`{arm}`" in reg,
              f"G7 {arm} is read in production and registered in 29")


# ---- G8 ------------------------------------------------------------------------------------------------------------

def g8(story_src: str, sink=None):
    body = _method(story_src, "_boss_plan_is_hopeless")
    check("_gym_tm_taught_moves" in body and "if learned.move.name in _taught:" in body,
          "G8 `_boss_plan_is_hopeless` skips moves the gym-TM teach delivered", sink)
    pc = _strip_comments(PCTRIP.read_text(encoding="utf-8"))
    check("protected |= protected_taught_pids(" in pc,
          "G8 `pc_trip` protects a taught PID from make-room deposits", sink)
    import modules.memory as MEM

    real_flag = MEM.get_event_flag
    mode = types.SimpleNamespace(_gym_tm_taught_moves={(7, "Overheat"): {"boss": "Winona"}})
    try:
        MEM.get_event_flag = lambda name: False
        unbeaten = G.protected_taught_pids(mode)
        MEM.get_event_flag = lambda name: name == "BADGE06_GET"
        beaten = G.protected_taught_pids(mode)

        def boom(name):
            raise RuntimeError("unreadable")

        MEM.get_event_flag = boom
        unreadable = G.protected_taught_pids(mode)
    finally:
        MEM.get_event_flag = real_flag
    check(unbeaten == {7} and beaten == set() and unreadable == {7},
          f"G8 the protection lasts until the boss's badge (unbeaten {unbeaten}, beaten {beaten}, unreadable "
          f"{unreadable} — an unreadable flag keeps it)", sink)


def g8_live(sink=None):
    """Run the REAL `_boss_plan_is_hopeless` on a stand-in party whose only answer to Winona's ace is a TAUGHT Rock Tomb."""
    import plugins.custom_modes.story_mode as SM
    import modules.pokemon_party as PP
    import modules.story.early_game as EG
    from modules.map_data import MapRSE
    from modules.pokemon import get_move_by_name, get_species_by_name

    key = MapRSE.FORTREE_CITY_GYM.value
    rock = types.SimpleNamespace(move=get_move_by_name("Rock Tomb"), pp=10)
    tackle = types.SimpleNamespace(move=get_move_by_name("Tackle"), pp=35)
    mon = types.SimpleNamespace(species=get_species_by_name("Marshtomp"), moves=[rock, tackle, None, None],
                                personality_value=0xABCD)
    mode = SM.StoryMode.__new__(SM.StoryMode)
    mode._defeat_counts = {key: 8}
    mode._loss_ko_history = {key: [(i, 1) for i in range(1, 9)]}
    mode._gym_tm_taught_moves = {}
    cfg = {"name": "Winona", "keys": [key], "ace_types": ("Dragon", "Flying")}
    real_party, real_battlers = PP.get_party, EG._battler_slots
    try:
        PP.get_party = lambda: [mon]
        EG._battler_slots = lambda: [0]
        untaught = SM.StoryMode._boss_plan_is_hopeless(mode, cfg)
        mode._gym_tm_taught_moves = {(0xABCD, "Rock Tomb"): {"boss": "Winona", "wall": "Altaria", "used": False}}
        taught = SM.StoryMode._boss_plan_is_hopeless(mode, cfg)
    finally:
        PP.get_party, EG._battler_slots = real_party, real_battlers
    check(untaught[0] is False and taught[0] is True,
          f"G8 LIVE: a natural Rock Tomb is a credible answer (hopeless={untaught[0]}), the same move TAUGHT is not "
          f"(hopeless={taught[0]})", sink)


# ---- G9 ------------------------------------------------------------------------------------------------------------

def g9():
    check(G.boss_for_enemy_party([m.species for m in WINONA]) == "Winona", "G9 Winona's exact roster ⇒ Winona")
    check(G.boss_for_enemy_party(["Doduo", "Skarmory", "Tropius"]) is None,
          "G9 a gym TRAINER sharing her species (Jared: Doduo/Skarmory/Tropius) ⇒ None")
    check(G.boss_for_enemy_party(["Skarmory"]) is None, "G9 one shared species ⇒ None")


def g10(module_src: str, sink=None):
    fn = None
    for node in ast.walk(ast.parse(module_src)):
        if isinstance(node, ast.FunctionDef) and node.name == "_leave_teach_menus":
            fn = node
    loops = [n for n in ast.walk(fn) if isinstance(n, ast.For)] if fn else []
    reads_inside = any("get_learn_move_state()" in (ast.get_source_segment(module_src, lp) or "") and
                       "ConfirmCancellation" in (ast.get_source_segment(module_src, lp) or "") for lp in loops)
    body = _strip_comments(ast.get_source_segment(module_src, fn) or "") if fn else ""
    check(fn is not None and reads_inside, "G10 the close reads the learn-move state INSIDE its loop (every press)", sink)
    check(fn is not None and "_leave_menus(" not in body,
          "G10 … and never hands off to the plain B-only close (`_leave_menus`)", sink)


def main() -> int:
    print("=" * 92)
    print("GATE — USER RULING 19 (design 4): the gym-TM teach planner, its recorder, wiring and fail-open act")
    print("=" * 92)
    src = STORY.read_text(encoding="utf-8")
    bas = BAS.read_text(encoding="utf-8")
    print("\n== G1 the wall ==")
    g1(G.faints_by_foe, G.wall_species)
    g1b(bas, src)
    g1c(bas)
    print("\n== G2 the slot ==")
    g2(G.choose_slot)
    print("\n== G3 the pair ==")
    g3(G.plan_teach)
    print("\n== G4 wiring ==")
    g4(src)
    print("\n== G5 data ==")
    g5(src)
    print("\n== G6 fail-open, the latch, the wait ==")
    g6()
    print("\n== G7 arms ==")
    g7()
    print("\n== G8 not a lever-killer ==")
    g8(src)
    g8_live()
    print("\n== G9 the leader, not her trainers ==")
    g9()
    print("\n== G10 the teach-aware close ==")
    module_src = MODULE.read_text(encoding="utf-8")
    g10(module_src)

    print("\n== FAULT ARMS: the gate must FAIL when the thing it guards is broken ==")
    sink: list = []

    def hm_ok(moves, mon_types=()):
        for i, mv in enumerate(moves):
            if mv is None:
                return i, "<empty>"
        return 0, moves[0].name

    g2(hm_ok, sink)
    check(bool(sink), f"FAULT a slot chooser that overwrites an HM FAILS G2 ({len(sink)} caught)")
    sink = []
    g1(G.faints_by_foe, lambda losses, roster: (next(iter(losses[-1]), None) if losses else None), sink)
    check(bool(sink), f"FAULT a last-foe-only wall FAILS G1 ({len(sink)} caught)")
    sink = []
    line = '            TURN_FOE["species"] = getattr(getattr(_foe, "species", None), "name", None)\n'
    g1b(bas.replace(line, "", 1).replace("def _ki93_forget(", 'TURN_FOE["species"] = None\n\n\ndef _ki93_forget(', 1),
        src, sink)
    check(bool(sink) and line in bas, f"FAULT the recorder moved OUTSIDE the instrumentation's try FAILS G1b ({len(sink)})")
    sink = []
    rec_start = bas.index("            # USER RULING 19 (2026-09-26): the foe we act against, BY SPECIES, and this decision")
    rec_end = bas.index("                del TURN_FOE[\"log\"][0]\n", rec_start) + len(
        "                del TURN_FOE[\"log\"][0]\n")
    recorder = bas[rec_start:rec_end]
    shipped_bug = bas.replace(recorder, "", 1).replace(
        "            _what = getattr(action, \"name\", str(action))\n",
        recorder + "            _what = getattr(action, \"name\", str(action))\n", 1)
    g1c(shipped_bug, sink)
    check(bool(sink) and shipped_bug != bas, f"FAULT the recorder ABOVE `_what` (the shipped bug) FAILS G1c ({len(sink)})")
    sink = []
    moved = src.replace("            yield from maybe_teach_gym_tm(self, cfg, losses)\n", "", 1).replace(
        "        boss_mode = False\n", "        boss_mode = False\n        yield from maybe_teach_gym_tm(self, cfg, losses)\n", 1)
    g4(moved, sink)
    check(bool(sink), f"FAULT the hook moved AFTER the boss-mode block FAILS G4 ({len(sink)} caught)")
    sink = []
    real_incoming = G.incoming
    try:
        G.incoming = lambda wall, types_: 1.0  # the reach filter disabled: every mon looks fielded
        g3(G.plan_teach, sink)
    finally:
        G.incoming = real_incoming
    check(bool(sink), f"FAULT a planner WITHOUT the reach filter FAILS G3 ({len(sink)} caught)")
    sink = []
    g8(src.replace("                    if learned.move.name in _taught:\n                        continue\n", "", 1), sink)
    check(bool(sink), f"FAULT a hopeless scan that counts taught moves FAILS G8 ({len(sink)} caught)")

    sink = []
    two_phase = module_src.replace("    yield from wait_until_truly_controllable()\n\n\ndef _teach(",
                                   "    yield from _leave_menus()\n\n\ndef _teach(", 1)
    g10(two_phase, sink)
    check(bool(sink) and two_phase != module_src, f"FAULT the two-phase close (hand-off to _leave_menus) FAILS G10 ({len(sink)})")

    print()
    if failures:
        print(f"FAIL ({len(failures)})")
        for f in failures:
            print("  " + f)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
