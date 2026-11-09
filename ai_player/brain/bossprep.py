"""BOSS PREPARATION, first slice BP-1 (USER RULING 58, 2026-11-09): is the party READY for the next gym leader, and if
not, which ONE of its own Pokemon should it raise, to which level? Framework-free: it decides from the eyes' party and the
AI's static knowledge (`knowledge/atlas.py` boss_party, `knowledge/seasoned.py`, `knowledge/facts.py`).

WHY (spec `PROJECT KNOWLEDGE/ai-research-notes/2026-11-08-BOSS-PREP-BP1-SPEC.md`; the design and its critique M1-M5,
2026-11-07): the brain trained for a named fight by its STRONGEST level (`brain/goals.py` training_target: the strongest
Pokemon at the leader's top level plus a margin), so C1's Grovyle L22 read "ready" for BRAWLY's L16-19 Fighting team and
the party lost to MACHOP three times at full HP (probe #111). A seasoned player (USER RULINGS 40, 44, 58) knows the
leader's team, levels, moves and held items, judges the party AGAINST that team, and when it would lose picks one of its
own Pokemon whose typing resists and whose moves hit back (RULING 58's "bring a counter", RULING 33's type advantages of
both the Pokemon and its moves) and raises it.

THE VERDICT (`verdict`): a small deterministic DUEL, integer HP points, scored with the battle brain's OWN valuation both
ways (`brain/battle.py` move_value for the choice, rough_share for the damage: a person's rough sense, to an eighth):
  * the member's move each turn: its best by move_value against the boss Pokemon's SPECIES types (ties: the lower
    priority, then the lower slot); its damage: rough_share of the boss Pokemon's typical HP (`typical_stat`, rule 4.1);
  * the boss Pokemon's move: the one that does the most points to the member now (a person's worst case; no AI flags),
    with the VERDICT POWERS (`verdict_slot`: Low Kick 60, Reversal by its own HP share, Arm Thrust x3) and the exact
    rules of fixed damage (Seismic Toss: the user's level, whatever the typing, 0 to an immune type) and Focus Punch
    (0 on a turn the member hits first, `data/battle_scripts_1.s` jumpifnodamage);
  * the foe moves first unless its move's priority is lower (Vital Throw, Focus Punch); speed is not modelled; a held
    Sitrus / Oran Berry heals it once at half HP (RULING 44: the item is known);
  * a member that faints is replaced by the healthy one with the best (attack half / threat half) x HP share, HP carried
    over; 80 turns per boss Pokemon at most.
Classes: READY (every boss Pokemon falls with at least `CAUTION` of the party's HP left), CLOSE (they all fall with less,
or only the last stands at half its HP or less), NOT READY. Every member is judged at its FULL HP (a person heals before a
leader; see `members_of`).

THE PLAN (`options`, `choose_plan`): for each member with a damaging move NOW, the lowest level from its next one to the
team's top level + `RAISE_LEVEL_SPAN` at which the verdict, with that member PROJECTED there (`project`: its evolutions
and level-up moves, `learn_choice` deciding a fifth move; a branch the PID decides is judged by the WORSE branch) and
LEADING, reads READY; its cost `L^2 - level^2`; one draw from the run's own `<seed>:bossprep` stream among the options
within the personality's `near_best` share of the cheapest. Acted on only for a leader in `ACT_ON` by a Story or Catcher
run (`brain/goals.py` raise goal); a Trainer run LOGS what it would do (the in-run control).

NEVER READ HERE: the PC boxes (`look.storage`), a base stat, a catch rate, an experience yield, a growth rate, a wild
held item, a PID-derived trait, the RNG. `gates/check_fairness.py` and `gates/test_bossprep.py` pin it.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from ai_player.brain.battle import TEMPERAMENTS, BattleFaults, learn_choice, move_value, rough_share, typical_stat
from ai_player.eyes.observation import BattleMon, MonSummary, MoveSlot, Observation
from ai_player.knowledge.atlas import BossMon, gym_leaders
from ai_player.knowledge.seasoned import evolutions, level_up
from ai_player.knowledge.facts import move_fact, species_fact, type_multiplier
from ai_player.personality import ERRANDS

__all__ = [
    "ACT_ON",
    "ACTING",
    "BERRY_HP",
    "BUDGET",
    "CAUTION",
    "CLOSE",
    "FLAIL_TABLE",
    "LOW_KICK_POWER",
    "MULTI_HIT_FACTOR",
    "NOT_READY",
    "RAISE_LEVEL_SPAN",
    "READY",
    "BossprepFaults",
    "Member",
    "NO_FAULTS",
    "Option",
    "RaiseWatch",
    "TURN_CAP",
    "Verdict",
    "attack_half",
    "choose_plan",
    "described",
    "hit_points",
    "members_of",
    "near_best",
    "new_record",
    "next_boss",
    "options",
    "project",
    "spent_reason",
    "team_line",
    "threat_half",
    "trainee_rest",
    "types_of",
    "verdict",
    "verdict_slot",
    "with_target",
]

READY = "READY"
CLOSE = "CLOSE"
NOT_READY = "NOT READY"
_RANK = {NOT_READY: 0, CLOSE: 1, READY: 2}
#: the share of the party's HP that must be LEFT after the duel for READY (taste, the design's values)
CAUTION = {"Story": 0.25, "Catcher": 0.30, "Trainer": 0.40}
#: the leaders a plan is ACTED on for (the scope guard of the spec, section 0): the verdict is logged for every one;
#: widening this is BP-2, after the chapters 1-5 calibration (T12a)
ACT_ON = frozenset({"BRAWLY"})
#: the personalities that act on a plan; a Trainer run logs it (`state` "logged")
ACTING = ("Story", "Catcher")
#: the ONE budget per boss (M5): the first bound reached spends it ("no endless grind")
BUDGET = {
    "Story": {"battles": 160, "frames": 450_000, "stalls": 12, "reorder_fails": 3, "hunt_encounters": 0, "balls_thrown": 0},
    "Catcher": {"battles": 200, "frames": 550_000, "stalls": 12, "reorder_fails": 3, "hunt_encounters": 0,
                "balls_thrown": 0},
}
#: `src/battle_script_commands.c` sFlailHpScaleToPowerTable: (the user's HP scaled to 48, at most) -> power
FLAIL_TABLE = ((1, 200), (4, 150), (9, 100), (16, 80), (32, 40), (48, 20))
#: `src/data/items.h` holdEffectParam of the berries a boss may hold that heal at half HP (`src/battle_util.c`)
BERRY_HP = {"Sitrus Berry": 30, "Oran Berry": 10}
#: Low Kick by the target's weight (`src/battle_script_commands.c` sWeightToDamageTable): the weight is not in the
#: knowledge, so 60 (it over-rates Low Kick on light Pokemon: biased toward NOT READY)
LOW_KICK_POWER = 60
#: 2 to 5 hits (`src/battle_script_commands.c` Cmd_setmultihitcounter: 2 and 3 at 3/8 each, 4 and 5 at 1/8): mean 3.0
MULTI_HIT_FACTOR = 3.0
#: a raise is judged up to the team's top level plus this
RAISE_LEVEL_SPAN = 11
#: turns per boss Pokemon at most (no result = NOT READY)
TURN_CAP = 80
#: fixed damage the duel models (points): the user's level, or a flat number (`src/battle_script_commands.c`)
_FLAT = {"SONICBOOM": 20, "DRAGON_RAGE": 40}
_LEVEL_FLAT = ("LEVEL_DAMAGE", "PSYWAVE")


@dataclass(frozen=True)
class BossprepFaults:
    """FAULT switches (test side only: `gates/test_bossprep.py`); none on the happy path. Each is a rule of the spec
    switched off, so a test can show what the rule changes."""

    types_only: bool = False  # the attack half valued with no types (every matchup x1, no STAB)
    moves_only: bool = False  # the threat half ignored: every damaging boss move but fixed damage does 0
    fp_always: bool = False  # Focus Punch never fails
    fixed_resisted: bool = False  # Seismic Toss scaled by the type chart
    no_immunity: bool = False  # fixed damage hits a type immune to its move's type
    no_sitrus: bool = False  # the held berry ignored
    flail_flat: bool = False  # Reversal at its printed power (1)
    no_projection: bool = False  # a member at a higher level keeps its species and moves
    strongest_level: bool = False  # today's rule: READY when the strongest member >= the top level + the margin
    eligible_cocoon: bool = False  # a member with no damaging move may be raised
    cost_by_level_gap: bool = False  # the cost is the levels to gain, not their squares
    current_only: bool = False  # the next boss only when the CURRENT milestone is its fight (today's fight_next)
    #: the boss's moves tied on points chosen by NAME (the spec appendix's `max((points, name))`), not the faster one
    name_tie: bool = False


NO_FAULTS = BossprepFaults()


@dataclass(frozen=True)
class Member:
    """A party member as the verdict sees it: identity (PID), species, level, HP points, max HP, its moves by name, and
    its summary (the real stats) when judged at its own level; None when PROJECTED (typical stats)."""

    pid: int
    species: str
    level: int
    hp: int
    max_hp: int
    moves: tuple[str, ...]
    summary: MonSummary | None = None
    note: str = ""

    @property
    def types(self) -> tuple[str, ...]:
        return types_of(self.species)


@dataclass(frozen=True)
class Verdict:
    """The duel's result: the class, the party's HP left as a share of its max, what happened (log words), each boss
    Pokemon's knockout as (boss species, member PID, member species, member level), and the boss Pokemon left standing
    with its HP share when the party fell (None when none stood)."""

    cls: str
    party_left: float
    log: tuple[str, ...]
    kos: tuple[tuple[str, int, str, int], ...] = ()
    standing: tuple[str, float] | None = None

    def line(self) -> str:
        stood = f"; {self.standing[0]} stands at {self.standing[1]:.2f}" if self.standing else ""
        return f"{self.cls} (party left {self.party_left:.2f}{stood}): {'; '.join(self.log)}"


@dataclass(frozen=True)
class Option:
    """One way to READY: raise member `pid` from `level` to `target` (its worst branch then `projected`)."""

    pid: int
    species: str
    level: int
    target: int
    cost: int
    projected: str
    party_left: float

    @property
    def plan(self) -> str:
        return f"raise:{self.pid:08x}:{self.target}"


def types_of(species: str) -> tuple[str, ...]:
    """A species' types as a Pokedex shows them (the facts'), a type listed twice once."""
    fact = species_fact(species)
    return tuple(dict.fromkeys(fact.types)) if fact is not None else ()


def _slot(name: str) -> MoveSlot:
    fact = move_fact(name)
    return MoveSlot(name, fact.type if fact else "Normal", fact.power if fact else 0, None, None)


def _battler(species: str, level: int) -> BattleMon:
    return BattleMon(species, 0, level, None, None, 48, "", types_of(species), ())


def members_of(look: Observation) -> list[Member]:
    """The party as the eyes show it, in the game's order, each member at its FULL HP (a person judges the team it will
    bring to the leader, healed: the heal-before-a-fight rule, `brain/goals.py` HEAL_BEFORE_FIGHT; and the verdict's run
    is cached on a signature without HP, so the HP of one moment would freeze into it). Eggs left out."""
    out = []
    for mon in look.party or ():
        if mon.is_egg:
            continue
        out.append(Member(mon.pid, mon.species, mon.level, mon.max_hp, mon.max_hp, tuple(m.name for m in mon.moves), mon))
    return out


# ------------------------------------------------------------------------------------------- projection (M3)
def project(member: Member, level: int, faults: BossprepFaults = NO_FAULTS) -> list[Member]:
    """Every way `member` can be at `level`: its evolutions by level (two when the PID decides the branch, as Wurmple's),
    the level-up moves of the species it is at each level (a fifth move decided by `learn_choice`), and typical max HP;
    itself when `level` is not above its own. FAULT `no_projection`: the same species and moves at the higher level."""
    if level <= member.level:
        return [member]
    hp = typical_stat("hp", level)
    if faults.no_projection:
        return [Member(member.pid, member.species, level, hp, hp, member.moves, None, "no projection (FAULT)")]
    outs: list[tuple[str, list[str], list[str]]] = [(member.species, list(member.moves), [])]
    for lv in range(member.level + 1, level + 1):
        nxt = []
        for species, moves, path in outs:
            evolved = [into for method, at, into in evolutions(species)
                       if method.startswith("EVO_LEVEL") and at is not None and at <= lv]
            targets = [(into, path + [f"{into} L{lv}"]) for into in evolved] or [(species, path)]
            for into, way in targets:
                kept = list(moves)
                for at, new in level_up(into):
                    if at != lv or new in kept or move_fact(new) is None:
                        continue
                    if len(kept) < 4:
                        kept.append(new)
                        continue
                    summary = MonSummary(0, into, 0, lv, 1, 1, "", types_of(into), tuple(_slot(m) for m in kept), 0, 0,
                                         False)
                    choice = learn_choice(summary, new)
                    if choice.learn and choice.forget in kept:
                        kept[kept.index(choice.forget)] = new
                nxt.append((into, kept, way))
        outs = nxt
    return [Member(member.pid, species, level, hp, hp, tuple(moves), None, ", ".join(way)) for species, moves, way in outs]


# ------------------------------------------------------------------------------------------- the two halves (S1)
def verdict_slot(name: str, foe_share: float = 1.0, faults: BossprepFaults = NO_FAULTS) -> tuple[MoveSlot, float | None]:
    """A boss move as the verdict weighs it (m6): its slot, and the VERDICT POWER of a move whose power the printed one
    does not tell (None: the printed power): Low Kick `LOW_KICK_POWER`, Reversal / Flail by the user's HP share now
    (`FLAIL_TABLE`; FAULT `flail_flat`: printed), a multi-hit move x `MULTI_HIT_FACTOR`."""
    fact = move_fact(name)
    slot = _slot(name)
    if fact is None:
        return slot, None
    if fact.effect == "LOW_KICK":
        return slot, float(LOW_KICK_POWER)
    if fact.effect == "FLAIL" and not faults.flail_flat:
        scale = max(1, int(48 * max(0.0, min(1.0, foe_share))))
        return slot, float(next(power for cut, power in FLAIL_TABLE if scale <= cut))
    if fact.effect == "MULTI_HIT":
        return slot, fact.power * MULTI_HIT_FACTOR
    return slot, None


def _damaging(member: Member) -> list[tuple[int, str]]:
    """(slot, name) of the member's moves that HURT by the brain's own valuation (a status move, an unknown one: not)."""
    out = []
    for slot, name in enumerate(member.moves):
        value = move_value(slot, _slot(name), member.types, member.level, 1.0, ())
        if value is not None and not value.status:
            out.append((slot, name))
    return out


def attack_half(member: Member, boss: BossMon, hp_share: float = 1.0, faults: BossprepFaults = NO_FAULTS):
    """The member's best move against the boss Pokemon by `move_value` (type x STAB x power x hit chance, less recoil):
    its MoveValue, or None when nothing it knows hurts. Ties: the lower priority, then the lower slot (the pessimistic
    tie: Grovyle's Pound and Quick Attack). FAULT `types_only`: valued with no types."""
    battle_faults = BattleFaults(ignore_types=True) if faults.types_only else BattleFaults()
    best = None
    for slot, name in enumerate(member.moves):
        value = move_value(slot, _slot(name), member.types, member.level, hp_share, types_of(boss.species), battle_faults)
        if value is None or value.status:
            continue
        fact = move_fact(name)
        key = (value.value, -(fact.priority if fact else 0), -slot)
        if best is None or key > best[0]:
            best = (key, value)
    return best[1] if best else None


def threat_half(boss: BossMon, member: Member, boss_share: float = 1.0, faults: BossprepFaults = NO_FAULTS):
    """The boss Pokemon's strongest known damaging move against the member's typing by `move_value`, with the verdict
    powers (m6): its MoveValue, or None. A LOG word and the replacement's rank, never the class (S1)."""
    best = None
    for slot, name in enumerate(boss.moves):
        move, power = verdict_slot(name, boss_share, faults)
        value = move_value(slot, move, types_of(boss.species), boss.level, 1.0, member.types, power=power)
        if value is None or value.status:
            continue
        if best is None or value.value > best.value:
            best = value
    return best


def hit_points(boss: BossMon, member: Member, name: str, boss_share: float, member_damaging: bool, member_hp: int,
               faults: BossprepFaults = NO_FAULTS) -> int:
    """The HP points one hit of the boss move `name` takes off the member (M1, m1, m6: spec section 1.4): a status move 0;
    Focus Punch 0 when the member hits it first this turn (FAULT `fp_always`); fixed damage exactly (Seismic Toss the
    user's level whatever the typing, 0 to a type immune to the move: FAULTS `fixed_resisted`, `no_immunity`); otherwise
    the rough share of a typical Pokemon of the member's level (the boss's attack typical too, rule 4.1)."""
    fact = move_fact(name)
    if fact is None or fact.category == "status":
        return 0
    if fact.effect == "FOCUS_PUNCH" and member_damaging and not faults.fp_always:
        return 0
    mult = type_multiplier(fact.type, member.types)
    if fact.fixed_damage:
        if mult == 0 and not faults.no_immunity:
            return 0
        if fact.effect in _LEVEL_FLAT:
            flat = boss.level
        elif fact.effect == "SUPER_FANG":
            flat = max(1, member_hp // 2)
        else:
            flat = _FLAT.get(fact.effect, 0)  # Endeavor, Counter, Mirror Coat, Bide: not modelled
        if faults.fixed_resisted:
            flat = int(flat * mult)
        return flat
    if faults.moves_only:
        return 0
    move, power = verdict_slot(name, boss_share, faults)
    share = rough_share(move, None, _battler(boss.species, boss.level), _battler(member.species, member.level), power=power)
    return round((share or 0.0) * typical_stat("hp", member.level))


def _own_points(member: Member, boss: BossMon, name: str) -> int:
    """The HP points one hit of the member's move takes off the boss Pokemon (its typical HP), as a person roughly puts
    it (`rough_share`; the summary's real attack at the member's own level, typical when projected; Bide and a status
    move 0)."""
    share = rough_share(_slot(name), member.summary, _battler(member.species, member.level), _battler(boss.species, boss.level))
    return round((share or 0.0) * typical_stat("hp", boss.level))


# ------------------------------------------------------------------------------------------- the duel
def verdict(party: list[Member], lead_pid: int | None, team: tuple[BossMon, ...] | list[BossMon], personality: str,
            faults: BossprepFaults = NO_FAULTS) -> Verdict:
    """The readiness verdict of `party` (the lead first: `lead_pid`, else the game's first) against the boss's `team`
    (module docstring; spec section 1.5)."""
    personality = personality if personality in CAUTION else "Story"
    if not party or not team:
        return Verdict(NOT_READY, 0.0, ("no party or no team",))
    if faults.strongest_level:
        margin = ERRANDS[personality].train_margin
        top = max(boss.level for boss in team)
        strongest = max(member.level for member in party)
        cls = READY if strongest >= top + margin else NOT_READY
        return Verdict(cls, 1.0, (f"today's rule: the strongest L{strongest} against L{top} + {margin} (FAULT)",))
    hp = [member.hp for member in party]
    field_i = next((i for i, member in enumerate(party) if member.pid == lead_pid), 0)
    log: list[str] = []
    kos: list[tuple[str, int, str, int]] = []
    for number, boss in enumerate(team):
        boss_max = typical_stat("hp", boss.level)
        boss_hp = boss_max
        berry = None if faults.no_sitrus else BERRY_HP.get(boss.held_item or "")
        for _turn in range(TURN_CAP):
            share = boss_hp / boss_max
            if hp[field_i] <= 0:
                alive = [i for i in range(len(party)) if hp[i] > 0]
                if not alive:
                    log.append(f"all fainted against {boss.species} (its HP {share:.2f})")
                    last = number == len(team) - 1
                    return Verdict(CLOSE if last and share <= 0.5 else NOT_READY, 0.0, tuple(log), tuple(kos),
                                   (boss.species, round(share, 4)))

                def rank(i: int) -> float:
                    a = attack_half(party[i], boss, 1.0, faults)
                    t = threat_half(boss, party[i], 1.0, faults)
                    return (a.value if a else 0.0) / max(t.value if t else 1.0, 1.0) * (0.5 + 0.5 * hp[i] / party[i].max_hp)

                field_i = max(alive, key=rank)
            me = party[field_i]
            mine = attack_half(me, boss, hp[field_i] / me.max_hp, faults)
            dmg_out = _own_points(me, boss, mine.name) if mine is not None else 0
            options = []
            for name in boss.moves:
                fact = move_fact(name)
                points = hit_points(boss, me, name, share, mine is not None, hp[field_i], faults)
                options.append((points, fact.priority if fact else 0, name))
            # the most points; on a tie the FASTER move (it may knock the member out before it acts: the worst case);
            # FAULT `name_tie`: the spec appendix's tie-break by the move's NAME (its section 2 numbers were made so)
            dmg_in, p_foe, _used = max(options, key=(lambda o: (o[0], o[2])) if faults.name_tie else None)
            p_me = (move_fact(mine.name).priority if move_fact(mine.name) else 0) if mine is not None else 0
            order = ("foe", "me") if p_foe >= p_me else ("me", "foe")
            for who in order:
                if hp[field_i] <= 0 or boss_hp <= 0:
                    break
                if who == "foe":
                    hp[field_i] -= dmg_in
                else:
                    boss_hp -= dmg_out
                    if berry and 0 < boss_hp <= boss_max // 2:
                        boss_hp = min(boss_max, boss_hp + berry)
                        log.append(f"{boss.species}'s {boss.held_item} (+{berry})")
                        berry = None
            if boss_hp <= 0:
                kos.append((boss.species, me.pid, me.species, me.level))
                log.append(f"{boss.species} falls to {me.species} L{me.level} ({mine.name if mine else '-'})")
                break
        else:
            log.append(f"{boss.species}: no result in {TURN_CAP} turns")
            return Verdict(NOT_READY, 0.0, tuple(log), tuple(kos), (boss.species, round(boss_hp / boss_max, 4)))
    left = sum(max(0, h) for h in hp) / max(1, sum(member.max_hp for member in party))
    return Verdict(READY if left >= CAUTION[personality] else CLOSE, round(left, 4), tuple(log), tuple(kos))


# ------------------------------------------------------------------------------------------- the options and the plan
def options(party: list[Member], team: tuple[BossMon, ...] | list[BossMon], personality: str,
            faults: BossprepFaults = NO_FAULTS) -> tuple[list[Option], list[str]]:
    """Every member's way to READY (spec section 1.6): (the options, cheapest first; the log words for the members with
    none: not eligible, or never READY by the cap)."""
    top = max(boss.level for boss in team) + RAISE_LEVEL_SPAN
    out: list[Option] = []
    said: list[str] = []
    for index, member in enumerate(party):
        if not _damaging(member) and not faults.eligible_cocoon:
            said.append(f"{member.species} L{member.level}: no damaging move to win its own battles (switch training: BP-2)")
            continue
        for level in range(member.level + 1, top + 1):
            worst = None
            for projected in project(member, level, faults):
                trial = list(party)
                trial[index] = projected
                result = verdict(trial, projected.pid, team, personality, faults)
                key = (_RANK[result.cls], result.party_left)
                if worst is None or key < worst[0]:
                    worst = (key, result, projected)
            _, result, projected = worst
            if result.cls == READY:
                cost = level - member.level if faults.cost_by_level_gap else level * level - member.level * member.level
                out.append(Option(member.pid, member.species, member.level, level, cost,
                                  f"{projected.species} L{level} [{', '.join(projected.moves)}]", result.party_left))
                break
        else:
            said.append(f"{member.species} L{member.level}: never READY by L{top}")
    out.sort(key=lambda option: (option.cost, option.pid))
    return out, said


def choose_plan(rng: random.Random, near_best: float, found: list[Option], failed=()) -> tuple[Option | None, str]:
    """One draw among the options within `near_best` of the cheapest (RULING 33: varied among sensible picks), leaving
    out a plan that failed before (`failed`: the plan strings)."""
    left = [option for option in found if option.plan not in set(failed)]
    if not left:
        return None, "no option left"
    cheapest = min(option.cost for option in left)
    near = [option for option in left if option.cost <= cheapest / near_best]
    choice = rng.choice(near)
    return choice, (f"drawn among {[f'{o.species} L{o.target} ({o.cost})' for o in near]} (cost within "
                    f"{near_best:.0%} of the cheapest, {cheapest})")


def new_record() -> dict:
    """The per-boss record (spec section 3.3), kept in the goal manager's game memory (`fight_prep[<boss>]["bp"]`). Its
    stage is under `status` (the spec's `state`: active, done, spent, logged, none): `state` is a developer-only key
    name of the knowledge (`gates/check_fairness.py` RULE B2 refuses any read of it by name)."""
    return {"plan": "", "trainee": None, "target": 0, "status": "none", "battles": 0, "frames": 0, "sessions": 0,
            "stalls": 0, "reorder_fails": 0, "leak_battles": 0, "failed": [], "losses": 0, "hunt_encounters": 0,
            "balls_thrown": 0}


def spent_reason(record: dict, personality: str) -> str | None:
    """The first bound of the ONE per-boss budget the record has reached (M5), or None."""
    bounds = BUDGET.get(personality)
    if bounds is None:
        return None
    for key in ("battles", "frames", "stalls", "reorder_fails", "hunt_encounters", "balls_thrown"):
        if bounds[key] and record.get(key, 0) >= bounds[key]:
            return f"{key} {record.get(key, 0)} of at most {bounds[key]}"
    return None


def near_best(personality: str) -> float:
    return TEMPERAMENTS[personality if personality in TEMPERAMENTS else "Story"].near_best


# ------------------------------------------------------------------------------------------- which boss is next
def next_boss(milestones, index: int, faults: BossprepFaults = NO_FAULTS):
    """(milestone, leader name) of the first milestone at or after `index`, in the story's order, whose fight the game
    NAMES and whose maps hold a gym a leader holds (`knowledge/atlas.py` gym_leaders: "a seasoned player knows which
    leader holds which gym"); None when none is ahead. FAULT `current_only`: only the current milestone (today's
    `fight_next`)."""
    by_gym = {gym: name for name, gym in gym_leaders().items()}
    for milestone in milestones[max(0, index):]:
        if not getattr(milestone, "optional", False) and milestone.fight_named:
            for place in milestone.maps:
                if place in by_gym:
                    return milestone, by_gym[place]
        if faults.current_only:
            return None
    return None


def trainee_rest(look: Observation, pid: int, heal_below: float, active: str) -> str | None:
    """(M4) Why a RAISE roam stops after a battle: the trainee (by PID) fainted or under a third of its max HP; otherwise
    the training rule (`brain/goals.py` training_rest: the party under its heal line, the strongest down). Before BP-1 the
    rule was keyed on the STRONGEST only, so a fainted L3 trainee left the party at 89 % and Grovyle fought on."""
    from ai_player.brain.goals import training_rest  # here: goals imports this module

    trainee = next((m for m in look.party or () if m.pid == pid and not m.is_egg), None)
    if trainee is not None and trainee.hp <= 0:
        return f"the trainee {trainee.species} L{trainee.level} ({pid:08x}) has fainted"
    if trainee is not None and trainee.hp < trainee.max_hp / 3:
        return f"the trainee {trainee.species} L{trainee.level} is low ({trainee.hp}/{trainee.max_hp})"
    return training_rest(look, heal_below, active)


@dataclass
class RaiseWatch:
    """(M4, points 4 and 5) Watches a raise goal's battles: the own battler's PID at each battle's FIRST ACTION MENU (one
    whose lead is not the trainee ends the roam), and a battle the trainee fainted in (the replacement finished it: a LEAK
    of experience, counted). `tell` says each battle's lead.
    WHY THE ACTION MENU, NOT THE FIRST LOOK (measured 2026-11-09, the live A/B #112, B on 6371: the first battle look's own
    battler was GROVYLE, the Pokemon that had ended the PREVIOUS battle, though Wurmple led: the game keeps the last
    battle's battlers until the new one sends its Pokemon out, so three such stale reads spent the raise's budget on
    `reorder_fails` in two raise sessions): at the first action menu the Pokemon that leads is on the field."""

    trainee: int
    tell: Callable[[str], None]
    first: int | None = None
    battles: int = 0
    not_leading: int = 0
    leaks: int = 0

    def __call__(self, look: Observation) -> None:
        battle = look.battle
        if battle is None or not battle.own:
            return
        ui = look.screen.ui if look.screen is not None else None
        if ui is None or ui.kind != "battle_action":
            return  # before the first action menu the battlers may still be the last battle's
        if self.first is None and battle.own[0].pid is not None:
            self.first = battle.own[0].pid
            self.tell(f"[AI-BOSSPREP] raise battle: {battle.own[0].species} ({self.first:08x}) leads"
                      + ("" if self.first == self.trainee else f": NOT the trainee {self.trainee:08x}"))

    def after(self, look: Observation) -> str | None:
        """After a battle: the reason to stop the roam, if any (the trainee not leading)."""
        self.battles += 1
        first, self.first = self.first, None
        trainee = next((m for m in look.party or () if m.pid == self.trainee), None)
        if trainee is not None and trainee.hp <= 0:
            self.leaks += 1
        if first is not None and first != self.trainee:
            self.not_leading += 1
            return "the trainee is not leading"
        return None


def described(party: list[Member]) -> str:
    return ", ".join(f"{m.species} L{m.level} {m.max_hp} [{', '.join(m.moves)}]" for m in party)


def team_line(team) -> str:
    return ", ".join(f"{b.species} L{b.level}" + (f" @{b.held_item}" if b.held_item else "") for b in team)


def with_target(record: dict, target: int) -> dict:
    record = dict(record)
    record["target"] = target
    record["plan"] = f"raise:{int(record['trainee']):08x}:{target}"
    return record
