"""TEST SIDE (boss preparation BP-1, 2026-11-09): the readiness verdict and the plan from a START STATE's eyes, and the
party-order hand driven on a throwaway emulator.

    py -3.12 -B ai_player/gates/probe_bossprep.py verdict --start STATE.ss1 [--personality Story] [--seed N] [--boss NAME]
        the A/B's DISCRIMINATOR (spec section 5.4), computed before any run: the eyes' one look at the start state (the
        party with its summary stats, the marks), the current milestone, then `GoalManager.boss_prep` exactly as the play
        brain runs it (the run's own `<seed>:bossprep` stream): the next leader, the verdict, the options, the plan.
        Prints "BOSSPREP {json}" and the [AI-BOSSPREP] lines.
    py -3.12 -B ai_player/gates/probe_bossprep.py lead --start STATE.ss1 --pid HEX [--fault shift_slot]
        T10, the party-order hand (`hands/party_order.py` lead_with) played on the emulator with the AI's own eyes and
        hands; the game's party read AFTER by a SECOND PATH (the framework's party reader, `hands_harness.truth`):
        PASS when the first slot's PID is the one asked for and the PIDs are the same multiset. FAULT `shift_slot`: the
        hand's first cursor target one slot too far (the spec's `reorder_by_slot`), so another Pokemon goes first.
        Prints "LEAD {json}".

    (round 2, USER RULING 59, spec `ai-research-notes/2026-11-09-BOSS-PREP-BP1-RAISE-SPEC.md` sections 5.3-5.4)
    py -3.12 -B ai_player/gates/probe_bossprep.py raise --start STATE.ss1 --world world.jsonl [--seed N]
        the A/B's DISCRIMINATOR, offline: the plan (`boss_prep`, the seed's own stream), the raise map from `raise_maps`
        with its cap and partner, `fight_safe`'s class for the trainee at its level and projected to Dustox L12 against
        every land slot of that map, the bag's field potions, the nearest centre's links from that map, and (GATE SIDE,
        never the AI's) the expected EXP a battle there and the battles to L10, L16 and L20. Prints "RAISE {json}".
    py -3.12 -B ai_player/gates/probe_bossprep.py raise-battle --start STATE.ss1 --world world.jsonl --seed N
            [--fault no_switch_train] [--fault-c] [--save-end PATH]
        P1: the raise goal played by the round's own code (`GoalRunner._raise`: the trainee first, the walk, the roam), ONE
        battle a session, again on an Abra (it teleports) or a run, at most 5 battles. Read by a SECOND PATH (the
        framework's party, `hands_harness.truth`) before and after each battle: (a) the turn-1 decision, (b) the trainee's
        and the partner's EXP steps against `gates/exp_rule.py` switch_share (the decomp's yield, the foe's level), (c)
        the game's slot 0 after it is still the trainee. FAULT `no_switch_train`: the partner put first and the trainee
        never (+0 for the trainee, the full E for the partner); `--fault-c`: `lead_with(partner)` before (c)'s read
        (the check must report FAIL). Prints "RAISEBATTLE {json}".
    py -3.12 -B ai_player/gates/probe_bossprep.py potion --start STATE.ss1 --pid HEX [--item NAME] [--fault shift_slot]
        P2: `hands/field_item.py` use_on played on the emulator; the target's HP, the item's count and the PID multiset
        read after by the framework (`hands_harness.truth`): PASS when the HP rose by min(20, missing) for a Potion, the
        count fell by the number used, and the multiset is the same. CONTROL `--item` not in the bag: False, no press.
        FAULT `shift_slot`: the party cursor target one row off (the HP of the target does not rise: FAIL).

The emulator is the framework's (`probe_eyes.boot`, the fixture profile); run from a stage whose `sandbox-pokebot` is the
build root. Nothing is saved: the state is loaded into a throwaway emulator and dropped (`--save-end` keeps P1's end).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _boot(start: Path):
    from ai_player.gates.hands_harness import PROFILE
    from ai_player.gates.probe_eyes import boot

    context = boot(PROFILE)
    context.emulator.load_save_state(start.read_bytes())
    for _ in range(2):
        context.emulator.run_single_frame()
    return context


def verdict(start: Path, personality: str, seed: int, boss: str | None = None) -> dict:
    _boot(start)  # first: it puts the framework (the build root's `modules`) on the path the eyes import from
    from ai_player.brain.goals import GoalManager
    from ai_player.host.eyes import FrameworkEyes
    from ai_player.knowledge.story import load_story
    from ai_player.personality import PersonalityState

    seen = FrameworkEyes().look()
    story = load_story(seen.player.gender if seen.player is not None else None)
    index, milestone = story.current(dict(seen.progress.marks))
    lines: list[str] = []
    manager = GoalManager(story, PersonalityState(personality, random.Random(f"{seed}:drift"), drift_on=False),
                          random.Random(f"{seed}:goals"))
    manager.say = lines.append
    manager.bossprep_rng = random.Random(f"{seed}:bossprep")
    plan = manager.boss_prep(seen, index)
    record = plan[3] if plan is not None else None
    party = [(m.species, m.level, m.hp, m.max_hp, f"{m.pid:08x}", [s.name for s in m.moves], list(m.stats))
             for m in seen.party or ()]
    out = {"start": str(start), "personality": personality, "seed": seed, "milestone": milestone.id if milestone else None,
           "map": seen.player.map_const if seen.player else None, "party": party,
           "boss": list(plan[:3]) if plan is not None else None, "record": record}
    if boss is not None:
        # (T12a, a REPORT) the verdict of this party against a NAMED leader, the game's first member leading
        from ai_player.brain.bossprep import members_of, verdict as judge
        from ai_player.knowledge.atlas import boss_party

        members = members_of(seen)
        named = judge(members, members[0].pid if members else None, boss_party(boss), personality)
        out["against"] = {"boss": boss, "class": named.cls, "line": named.line()}
    for line in lines:
        print(line)
    return out


def lead(start: Path, pid: int, fault: str | None) -> dict:
    context = _boot(start)  # first: the framework on the path
    from ai_player.gates.hands_harness import HarnessControls, truth
    from ai_player.hands import party_order
    from ai_player.hands.pad import Hands
    from ai_player.host.eyes import FrameworkEyes

    before = truth(context).get("party_exp")
    lines: list[str] = []
    hands = Hands(FrameworkEyes(), HarnessControls(context.emulator), random.Random("1:pacing"), random.Random("1:choices"),
                  None, lines.append)
    if fault == "shift_slot":
        real = party_order.move_cursor
        shifted = {"done": False}

        def move_cursor(hands_, kind, target, why):
            if kind == "party" and not shifted["done"]:
                shifted["done"] = True
                target += 1  # FAULT: the member's slot shifted by one
            return (yield from real(hands_, kind, target, why))

        party_order.move_cursor = move_cursor
    steps = party_order.lead_with(hands, pid, "probe_bossprep: the trainee first")
    frames, result = 0, None
    while frames < 20_000:
        try:
            next(steps)
        except StopIteration as done:
            result = done.value
            break
        context.emulator.run_single_frame()
        frames += 1
    after = truth(context).get("party_exp")
    pids_before = [row[0] for row in before or []]
    pids_after = [row[0] for row in after or []]
    ok = bool(pids_after) and pids_after[0] == f"{pid:08x}" and sorted(pids_after) == sorted(pids_before)
    return {"start": str(start), "pid": f"{pid:08x}", "fault": fault, "hand_said": result, "frames": frames,
            "presses": hands.pad.presses, "party_before": before, "party_after": after,
            "game_first_is_pid": bool(pids_after) and pids_after[0] == f"{pid:08x}",
            "same_multiset": sorted(pids_after) == sorted(pids_before), "verdict": "PASS" if ok else "FAIL",
            "lines": lines[-12:]}


# ------------------------------------------------------------------------------------------- round 2 (USER RULING 59)
def _play_pieces(context, world_path: Path, seed: int, personality: str = "Story") -> dict:
    """The play brain's own pieces (`mode.py` HandsBrain._play's, the subset a raise needs) on the booted emulator: the
    AI's eyes and hands, the world memory from `world_path`, the navigator, the battle mind (its battler the battle
    skill), the goal manager (the run's own streams, `<seed>:goals`, `<seed>:bossprep`) and the goal runner."""
    from ai_player.brain.battle import BattleMind
    from ai_player.brain.explore import weights_for
    from ai_player.brain.goals import GoalManager, GoalRunner
    from ai_player.brain.navigator import Navigator
    from ai_player.gates.hands_harness import HarnessControls
    from ai_player.hands.pad import Hands
    from ai_player.host.eyes import FrameworkEyes
    from ai_player.knowledge.story import load_story
    from ai_player.personality import PersonalityState
    from ai_player.skills.battle import play_battle
    from ai_player.skills.story import answer_question
    from ai_player.world.memory import read_world

    lines: list[str] = []
    hands = Hands(FrameworkEyes(), HarnessControls(context.emulator), random.Random(f"{seed}:pacing"),
                  random.Random(f"{seed}:choices"), None, lines.append)
    world = read_world(world_path)
    hands.watchers.append(world.observe)
    nav = Navigator(hands, world, random.Random(f"{seed}:choices"), weights_for(personality).grass_cost, personality)
    mind = BattleMind(personality, random.Random(f"{seed}:battle"), "travel")
    nav.battler = lambda: play_battle(hands, mind, f"battle ({mind.purpose})")
    nav.answer = answer_question
    look = hands.look()
    story = load_story(look.player.gender if look.player is not None else None)
    manager = GoalManager(story, PersonalityState(personality, random.Random(f"{seed}:drift"), drift_on=False),
                          random.Random(f"{seed}:goals"))
    manager.bossprep_rng = random.Random(f"{seed}:bossprep")
    manager.say = hands.tell
    manager.memory.landmarks = world.landmarks
    hands.watchers.append(manager.notice)
    runner = GoalRunner(hands, nav, manager, mind, hands.tell)

    def visited(const: str) -> bool:
        return any(memory.const == const and memory.visits for memory in world.maps.values())

    index, milestone = manager.milestone(look, visited)
    plan = manager.boss_prep(look, index)
    return {"hands": hands, "world": world, "nav": nav, "mind": mind, "manager": manager, "runner": runner, "lines": lines,
            "look": look, "index": index, "milestone": milestone, "plan": plan}


def _links(world, start_const: str, target_key: str | None) -> int | None:
    """Known links (warps, connections, rides) from the map `start_const` to the map key `target_key`, by maps (the
    fallback of `brain/goals.py` world_distance), or None."""
    from ai_player.brain.explore import ways_from

    if target_key is None:
        return None
    start = next((key for key, memory in world.maps.items() if memory.const == start_const), None)
    if start is None:
        return None
    seen, frontier = {start}, [(start, 0)]
    while frontier:
        here, depth = frontier.pop(0)
        if here == target_key:
            return depth
        for kind, link in ways_from(world, here):
            target = link.get("to") if kind in ("warp", "ride") else link.get("target")
            if target is not None and target not in seen:
                seen.add(target)
                frontier.append((target, depth + 1))
    return None


def _land(map_const: str) -> list[tuple[str, int, float]]:
    """(species, level, chance %) of every land slot level of a map, from the seasoned encounters file (gate side)."""
    from ai_player.knowledge.facts import species_named

    data = json.loads((REPO / "ai_player" / "knowledge" / "seasoned" / "encounters.json").read_text(encoding="utf-8"))
    out = []
    for entry in data["maps"]:
        if str(entry.get("map") or "").removeprefix("MAP_") != map_const or entry["availability"] != "normal":
            continue
        for slot in ((entry.get("methods") or {}).get("land") or {}).get("slots") or ():
            levels = range(slot["min_level"], slot["max_level"] + 1)
            for level in levels:
                out.append((species_named(slot["species"].removeprefix("SPECIES_").replace("_", " ")), level,
                            slot["chance_pct"] / len(levels)))
    return out


def raise_report(start: Path, world_path: Path, seed: int, personality: str = "Story") -> dict:
    """The A/B's discriminator (module docstring, `raise`)."""
    context = _boot(start)  # noqa: F841 - the framework on the path, the state loaded
    from ai_player.brain import bossprep as bp
    from ai_player.brain.goals import FIELD_POTIONS
    from ai_player.gates import exp_rule
    from ai_player.knowledge.seasoned import land_levels

    pieces = _play_pieces(context, world_path, seed, personality)
    manager, world, look, plan = pieces["manager"], pieces["world"], pieces["look"], pieces["plan"]
    record = plan[3] if plan is not None else None
    out: dict = {"start": str(start), "seed": seed, "milestone": pieces["milestone"].id if pieces["milestone"] else None,
                 "map": look.player.map_const if look.player else None,
                 "party": [(m.species, m.level, m.hp, m.max_hp, f"{m.pid:08x}", m.experience) for m in look.party or ()],
                 "boss": list(plan[:3]) if plan is not None else None, "record": record}
    trainee = next((m for m in look.party or () if record is not None and m.pid == record.get("trainee")), None)
    if trainee is None:
        out["stop"] = "no plan or no trainee"
        return out
    cap, cap_why = manager.raise_cap(look, trainee)
    maps = manager.raise_maps(world, cap)
    where = maps[0] if maps else None
    out.update(cap=cap, cap_why=cap_why, raise_maps=maps, raise_map=where,
               raise_map_levels=land_levels(where) if where else None)
    member = bp.member_now(look, trainee.pid)
    dustox = next((d for d in bp.project(member, 12) if d.species == "Dustox"), None) if member.level < 12 else None
    classes = []
    for species, level, chance in _land(where or ""):
        now = bp.fight_safe(member, species, level, 1.0, member.hp)
        at12 = bp.fight_safe(dustox, species, level, 1.0, dustox.max_hp) if dustox is not None else (None, "")
        classes.append({"foe": f"{species} L{level}", "chance": round(chance, 2),
                        "trainee_now": "own" if now[0] else "switch", "dustox_l12": None if at12[0] is None else
                        ("own" if at12[0] else "switch"), "why_now": now[1], "why_l12": at12[1]})
    out["fight_safe"] = classes
    out["field_potions"] = [(name, count) for name, count in (look.bag.healing if look.bag else ()) if name in FIELD_POTIONS]
    centre = manager.heal_place(world, reachable=True)
    key = manager._place_key(world, centre) if centre is not None else None
    links = _links(world, where, key) if where else None
    out["centre"] = {"place": centre[3] if centre else None, "links_from_raise_map": links,
                     "near": links is not None and links <= 2}
    # GATE SIDE (the developers' numbers, never the AI's): the decomp's yields and growth
    per_own, per_switch, per_own_noabra, per_switch_noabra, rates = 0.0, 0.0, 0.0, 0.0, 0.0
    for species, level, chance in _land(where or ""):
        y = exp_rule.decomp_yield(species)
        if y is None:
            continue
        e, half = exp_rule.full_exp(y, level), exp_rule.switch_share(y, level)
        per_own += chance / 100 * e
        per_switch += chance / 100 * half
        if species != "Abra":
            per_own_noabra += chance / 100 * e
            per_switch_noabra += chance / 100 * half
            rates += chance / 100
    growth = exp_rule.decomp_growth(trainee.species)
    have = trainee.experience
    gate: dict = {"growth": growth, "exp_now": have, "per_battle_own": round(per_own, 1),
                  "per_battle_switch": round(per_switch, 1), "per_battle_own_without_abra": round(per_own_noabra, 1),
                  "per_battle_switch_without_abra": round(per_switch_noabra, 1)}
    if growth is not None and per_switch_noabra > 0:
        need10 = (exp_rule.total_exp(growth, 10) or 0) - have
        gate["switch_battles_to_L10"] = round(need10 / per_switch_noabra, 1)
        # phase 2 from L12 (a Dustox): its own winnable fights at the full E, the rest switch-trained at E/2
        mixed = 0.0
        for row, (species, level, chance) in zip(classes, _land(where or "")):
            y = exp_rule.decomp_yield(species)
            if y is None or species == "Abra":
                continue
            share = exp_rule.full_exp(y, level) if row["dustox_l12"] == "own" else exp_rule.switch_share(y, level)
            mixed += chance / 100 * share
        at12 = exp_rule.total_exp(growth, 12) or 0
        base = max(0, at12 - have) / per_switch_noabra
        for target in (16, 20):
            gate[f"battles_to_L{target}"] = round(base + ((exp_rule.total_exp(growth, target) or 0) - max(have, at12))
                                                   / max(mixed, 1e-9), 1)
        gate["phase2_per_battle"] = round(mixed, 1)
    out["gate_side"] = gate
    out["lines"] = [line for line in pieces["lines"] if "[AI-BOSSPREP]" in line][-8:]
    return out


def raise_battle(start: Path, world_path: Path, seed: int, fault: str | None, fault_c: bool, save_end: Path | None,
                 battles_max: int = 5, frames_max: int = 60_000) -> dict:
    """P1 (module docstring, `raise-battle`)."""
    context = _boot(start)
    from ai_player.brain import goals as goals_module
    from ai_player.gates import exp_rule
    from ai_player.gates.hands_harness import truth
    from ai_player.hands.party_order import lead_with

    pieces = _play_pieces(context, world_path, seed)
    hands, nav, mind, manager, runner, world = (pieces[k] for k in ("hands", "nav", "mind", "manager", "runner", "world"))
    record = pieces["plan"][3] if pieces["plan"] is not None else None
    if record is None or record.get("status") != "active":
        return {"verdict": "STOP", "why": f"no active plan ({record})"}
    trainee = int(record["trainee"])
    first = truth(context)
    party0 = first.get("party_exp") or []
    others = [row for row in party0 if row[0] != f"{trainee:08x}"]
    partner_row = max(others, key=lambda row: (row[3], row[2])) if others else None
    partner = int(partner_row[0], 16) if partner_row else None

    def drive(steps, budget: int) -> object:
        for _ in range(budget):
            try:
                next(steps)
            except StopIteration as done:
                return done.value
            context.emulator.run_single_frame()
        return "probe: the frame budget ran out"

    samples: list[dict] = []
    current: dict = {}

    def sampler(look) -> None:
        if look.battle is not None:
            if not current:
                current.update(before=truth(context).get("party_exp"), began=look.frame, decisions=[])
            ui = look.screen.ui
            if ui is not None and ui.kind == "battle_action" and "foe" not in current and look.battle.foe:
                foe = look.battle.foe[0]
                current.update(foe=(foe.species, foe.level), lead=f"{look.battle.own[0].pid:08x}" if look.battle.own
                               and look.battle.own[0].pid is not None else None)
        elif current and look.screen.game_state == "OVERWORLD":
            current.update(after=truth(context).get("party_exp"), ended=look.frame, outcome=look.last_battle_outcome)
            samples.append(dict(current))
            current.clear()

    real_decide = mind.decide

    def decide(look, battler=None, redecide=False):
        decision = real_decide(look, battler, redecide)
        if current:
            current["decisions"].append((mind.memory.turns, decision.action, f"{decision.switch_pid:08x}"
                                         if decision.switch_pid is not None else None, decision.reason[:160]))
        return decision

    mind.decide = decide
    hands.watchers.append(sampler)
    real_hooks = runner.roam_hooks

    def one_battle(*args, **kwargs):
        real_hooks(*args, **kwargs)
        nav.battle_limit = len(nav.battle_outcomes) + 1  # ONE battle a session (P1)

    runner.roam_hooks = one_battle
    real_lead = goals_module.lead_with
    if fault == "no_switch_train":
        # FAULT: the partner put FIRST and the trainee never: the raise's own lead_with is made a no-op
        drive(lead_with(hands, partner, "probe FAULT no_switch_train: the partner first"), 20_000)

        def no_lead(hands_, pid, why):
            yield from hands_.pad.idle(1, "probe FAULT no_switch_train: the trainee is not put first")
            return True

        goals_module.lead_with = no_lead
    sessions = []
    try:
        for _ in range(battles_max):
            look = hands.look()
            plan = manager.boss_prep(look, pieces["index"])
            goal = manager._raise_goal(look, world, plan)
            if goal is None:
                sessions.append("no raise goal")
                break
            # through the runner's own `pursue` (it sets the battle purpose "raise", as the play brain does: the first P1
            # run called `_raise` directly and its battles were fought as "travel", a probe bug, ledger #116 void)
            index = pieces["index"]
            result = drive(runner.pursue(goal, pieces["milestone"], index, lambda seen: index), frames_max)
            sessions.append(str(result)[:200])
            useful = [s for s in samples if s.get("foe") and s["foe"][0] != "Abra" and s.get("outcome") == 1]
            if useful:
                break
    finally:
        goals_module.lead_with = real_lead
    if fault_c:
        drive(lead_with(hands, partner, "probe FAULT (c): the partner first before the read"), 20_000)
    end = truth(context)
    battles = []
    for sample in samples:
        before = {row[0]: row for row in sample.get("before") or []}
        after = {row[0]: row for row in sample.get("after") or []}
        steps = {pid: after[pid][2] - before[pid][2] for pid in after if pid in before}
        foe = sample.get("foe")
        y = exp_rule.decomp_yield(foe[0]) if foe else None
        battles.append({"foe": foe, "outcome": sample.get("outcome"), "lead": sample.get("lead"),
                        "decisions": sample.get("decisions"), "exp_steps": steps, "yield": y,
                        "E": exp_rule.full_exp(y, foe[1]) if y and foe else None,
                        "E_half": exp_rule.switch_share(y, foe[1]) if y and foe else None})
    useful = next((b for b in battles if b["foe"] and b["foe"][0] != "Abra" and b["outcome"] == 1), None)
    t, p = f"{trainee:08x}", f"{partner:08x}" if partner is not None else None
    checks: dict = {}
    if useful is not None:
        first_decision = (useful["decisions"] or [None])[0]
        checks["a_turn1_switch_to_partner"] = bool(first_decision and first_decision[1] == "switch"
                                                   and first_decision[2] == p)
        checks["b_trainee_step"] = useful["exp_steps"].get(t)
        checks["b_partner_step"] = useful["exp_steps"].get(p)
        checks["b_expected_each"] = useful["E_half"]
        checks["b_holds"] = (useful["exp_steps"].get(t) == useful["E_half"] and useful["exp_steps"].get(p) == useful["E_half"])
    slot0 = (end.get("party_exp") or [[None]])[0][0]
    checks["c_slot0"] = slot0
    checks["c_holds"] = slot0 == t
    if save_end is not None:
        save_end.write_bytes(context.emulator.get_save_state())
    verdict_ok = bool(checks.get("a_turn1_switch_to_partner")) and bool(checks.get("b_holds")) and checks["c_holds"]
    return {"start": str(start), "seed": seed, "fault": fault, "fault_c": fault_c, "trainee": t, "partner": p,
            "record": {k: record.get(k) for k in ("plan", "target", "status", "battles", "frames", "sessions", "stalls",
                                                  "own_fights", "switch_fights", "raise_runs", "lead_before")},
            "sessions": sessions, "battles": battles, "checks": checks,
            "verdict": "PASS" if verdict_ok else "FAIL",
            "party_end": end.get("party_exp"), "items_end": end.get("items"),
            "lines": [line for line in pieces["lines"] if "[AI-BOSSPREP]" in line or "battle: turn" in line][-30:]}


def potion(start: Path, pid: int, item: str | None, fault: str | None, up_to: float = 1.0, most: int = 1) -> dict:
    """P2 (module docstring, `potion`): by default ONE item, up to the full HP (the spec's P2: +min(20, missing), the count
    down 1); the raise's own goal uses `POTION_TO` and `POTIONS_PER_GOAL`."""
    context = _boot(start)
    from ai_player.gates.hands_harness import HarnessControls, truth
    from ai_player.hands import field_item
    from ai_player.hands.pad import Hands
    from ai_player.host.eyes import FrameworkEyes

    before = truth(context)
    lines: list[str] = []
    hands = Hands(FrameworkEyes(), HarnessControls(context.emulator), random.Random("1:pacing"), random.Random("1:choices"),
                  None, lines.append)
    if fault == "shift_slot":
        real = field_item.move_cursor
        shifted = {"done": False}

        def move_cursor(hands_, kind, target, why):
            if kind == "party" and not shifted["done"]:
                shifted["done"] = True
                target = target - 1 if target > 0 else target + 1  # FAULT: the member's row shifted by one
            return (yield from real(hands_, kind, target, why))

        field_item.move_cursor = move_cursor
    items = (item,) if item else ("Potion", "Super Potion")
    steps = field_item.use_on(hands, pid, items, up_to, most, "probe_bossprep: a Potion for the trainee")
    frames, result = 0, None
    while frames < 30_000:
        try:
            next(steps)
        except StopIteration as done:
            result = done.value
            break
        context.emulator.run_single_frame()
        frames += 1
    after = truth(context)
    target = f"{pid:08x}"
    hp_before = next((m[1] for m in zip([r[0] for r in before.get("party_exp") or []], before.get("party") or [])
                      if m[0] == target), None)
    hp_after = next((m[1] for m in zip([r[0] for r in after.get("party_exp") or []], after.get("party") or [])
                     if m[0] == target), None)
    used = (result or (False, 0, ""))[1]
    count = {name: before.get("items", {}).get(name, 0) - after.get("items", {}).get(name, 0)
             for name in set(before.get("items") or {}) | set(after.get("items") or {})}
    pids_same = sorted(r[0] for r in before.get("party_exp") or []) == sorted(r[0] for r in after.get("party_exp") or [])
    missing = (hp_before[2] - hp_before[1]) if hp_before else None
    rose = (hp_after[1] - hp_before[1]) if hp_before and hp_after else None
    ok = bool(result and result[0]) and rose is not None and rose > 0 and sum(count.values()) == used and pids_same
    return {"start": str(start), "pid": target, "item": item, "fault": fault, "hand_said": result, "frames": frames,
            "presses": hands.pad.presses, "hp_before": hp_before, "hp_after": hp_after, "missing": missing, "rose": rose,
            "count_fell": count, "pids_same": pids_same, "verdict": "PASS" if ok else "FAIL",
            "items_before": before.get("items"), "items_after": after.get("items"), "lines": lines[-12:]}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("verdict", "lead", "raise", "raise-battle", "potion"))
    parser.add_argument("--start", type=Path, required=True)
    parser.add_argument("--world", type=Path, help="raise, raise-battle: the start's world.jsonl")
    parser.add_argument("--personality", default="Story")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--pid", help="lead, potion: the PID (hex)")
    parser.add_argument("--item", help="potion: the item to use (a CONTROL with one the bag lacks)")
    parser.add_argument("--fault", choices=("shift_slot", "no_switch_train"))
    parser.add_argument("--fault-c", action="store_true", help="raise-battle: the partner put first before (c)'s read")
    parser.add_argument("--save-end", type=Path, help="raise-battle: save the end state here")
    parser.add_argument("--boss", help="verdict: also judge the party against this NAMED leader (T12a's report)")
    args = parser.parse_args()
    if args.mode == "verdict":
        print("BOSSPREP " + json.dumps(verdict(args.start, args.personality, args.seed, args.boss), ensure_ascii=False,
                                       default=str))
    elif args.mode == "lead":
        print("LEAD " + json.dumps(lead(args.start, int(args.pid, 16), args.fault), ensure_ascii=False, default=str))
    elif args.mode == "raise":
        print("RAISE " + json.dumps(raise_report(args.start, args.world, args.seed, args.personality), ensure_ascii=False,
                                    default=str))
    elif args.mode == "raise-battle":
        print("RAISEBATTLE " + json.dumps(raise_battle(args.start, args.world, args.seed, args.fault, args.fault_c,
                                                       args.save_end), ensure_ascii=False, default=str))
    else:
        print("POTION " + json.dumps(potion(args.start, int(args.pid, 16), args.item, args.fault), ensure_ascii=False,
                                     default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
