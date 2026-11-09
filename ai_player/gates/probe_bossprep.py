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

The emulator is the framework's (`probe_eyes.boot`, the fixture profile); run from a stage whose `sandbox-pokebot` is the
build root. Nothing is saved: the state is loaded into a throwaway emulator and dropped.
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


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("verdict", "lead"))
    parser.add_argument("--start", type=Path, required=True)
    parser.add_argument("--personality", default="Story")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--pid", help="lead: the PID (hex) to put first")
    parser.add_argument("--fault", choices=("shift_slot",))
    parser.add_argument("--boss", help="verdict: also judge the party against this NAMED leader (T12a's report)")
    args = parser.parse_args()
    if args.mode == "verdict":
        print("BOSSPREP " + json.dumps(verdict(args.start, args.personality, args.seed, args.boss), ensure_ascii=False,
                                       default=str))
    else:
        print("LEAD " + json.dumps(lead(args.start, int(args.pid, 16), args.fault), ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
