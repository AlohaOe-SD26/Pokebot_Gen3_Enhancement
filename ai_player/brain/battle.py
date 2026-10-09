"""The AI's BATTLE DECIDER (build step 4; design draft §2.3 "battle decider", §10.1; HUMAN-PLAY-DESIGN pillar 3).
Framework-free: it decides from an `Observation` and the AI's own knowledge files (`knowledge/facts.py`); the skill that
presses the buttons is `skills/battle.py`. RULING 35: the bot's `battle_strategies/*`, `battle_handler.py`,
`battle_action_selection.py`, `battle_move_replacing.py` and `story/*` were read as TEACHING material only, and the purity
gate refuses every one of them; nothing here is copied from them.

WHAT A PERSON DOES IN A BATTLE, AND HOW EACH PART IS DONE HERE
  * PICKS A MOVE BY ITS WORTH AGAINST THIS FOE (`move_value`): type effectiveness of the MOVE's type against the foe's
    types x STAB (1.5 when the move's type is one of the user's) x power x hit chance, minus a RECOIL penalty that grows as
    the user's own HP falls (`recoil_penalty`: Take Down / Submission 1/4 of the damage dealt, Double-Edge 1/3, Jump Kick's
    half-damage on a miss, Explosion's faint; the fractions are the decomp's, `gates/verify_knowledge.py`). Since the
    step-4 verifier's round the recoil is charged on the HP the hit can actually TAKE (`recoil_risk`): a hit takes at most
    what the foe has left (`Cmd_datahpupdate` caps gHpDealt at the target's HP), Jump Kick's miss recoil is capped at half
    the target's max HP, and a recoil that would knock the user out costs the move's whole worth. A status move is worth 0
    in a fight: it is never chosen BY HABIT, only when nothing that hurts is left.
  * IS NOT A MACHINE: among the moves about as good as the best (within the personality's `near_best` share), it picks one
    on a seeded, value-weighted draw (`choose_move`); a clearly better move is chosen every time.
  * SWITCHES when its Pokemon is badly matched (the foe's types hit it hard, or its own moves barely touch the foe) and a
    healthy party member is MUCH better against this foe (`matchup`); at most `MAX_SWITCHES` times a battle, never back
    and forth against one foe.
  * HEALS in an IMPORTANT battle (a trainer's): a healing item when its Pokemon is low and the foe is not about to fall,
    at most `MAX_HEALS` a battle.
  * RUNS from a wild battle it does not want: training, when its Pokemon is low or the foe far stronger; travelling, by
    its temperament.
  * CATCHES a species it has not caught yet (by the Pokedex's OWNED list, what the player's Pokedex shows) when its
    personality wants it (`Temperament.catch_new`, one seeded draw per species and run): it WEAKENS the foe first with a
    move that cannot knock it out (the most damage that still leaves the bar above `KO_MARGIN` at the best roll: weak
    moves when the bar is low), then THROWS a ball (a Poke Ball for an easy catch, a Great Ball for a hard one or after
    two misses), at most `MAX_THROWS` balls and `MAX_WEAKEN_TURNS` weakening turns.
  * ANSWERS the battle's questions by their WORDS (`answer`): "Use next POKéMON?" yes while one can fight; "Will ...
    change POKéMON?" by the switch rule and its temperament; a nickname: no; learning a move: by `learn_choice`, which
    keeps the four moves worth most to that Pokemon (an HM is never forgotten) and says why.
  * CHOOSES who goes in when its Pokemon faints (`replacement`): the healthy member best matched against the foe(s),
    never one already ON THE FIELD. The party menu covers the battle (the eyes see no battle view there), so, as a person
    does, the decider REMEMBERS the field (`see`: the last look at the battle, who stands there and whom it faces) and
    the members it sent in or the game refused since (`sent`, `refuse`). Found by the step-4 verifier: in a double
    battle the partner fainted, the party-menu look had no battle view, and the decider sent in the Pokemon already
    standing on the field (the game refused it and the battle stuck); in a single battle the replacement was ranked by
    level and HP alone.
Every choice it makes has a REASON string; the skill logs it with the press.

FAULT SWITCHES (`Faults`, test side only): `ignore_types` values every move as if every type matchup were neutral and
every Pokemon untyped (no STAB) (the TYPE arm's fault); `ignore_recoil` drops the recoil penalty (the RECOIL fault);
`uncapped_recoil` charges the recoil on the move's whole worth (the step-4 rule: no cap at the foe's HP, no Jump Kick
cap, no self-faint check); `forget_field` makes the replacement see only the look on screen (the step-4 bug);
`ignore_refusal` makes the skill watch the party menu's refusal ("... is already in battle!") instead of reading it.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from ai_player.eyes.observation import BattleMon, BattleView, MonSummary, MoveSlot, Observation
from ai_player.eyes.view import HP_BAR_PIXELS
from ai_player.knowledge.facts import MoveFact, move_fact, species_fact, stab, type_multiplier

__all__ = [
    "GREAT_BALLS",
    "HM_MOVES",
    "KO_MARGIN",
    "MAX_HEALS",
    "MAX_SWITCHES",
    "MAX_THROWS",
    "MAX_WEAKEN_TURNS",
    "TEMPERAMENTS",
    "BattleFaults",
    "BattleMind",
    "Decision",
    "LearnChoice",
    "MoveValue",
    "Temperament",
    "TypeSay",
    "damage_fraction",
    "estimate_stat",
    "general_value",
    "learn_choice",
    "matchup",
    "move_key",
    "move_value",
    "needs_rest",
    "recoil_penalty",
    "recoil_risk",
]

#: Weakening for a catch: a move is safe when, at its best damage roll, the foe's bar keeps this share (of 48 pixels).
KO_MARGIN = 0.08
#: Bounds of one battle.
MAX_THROWS = 10
MAX_WEAKEN_TURNS = 4
MAX_SWITCHES = 2
MAX_HEALS = 2
MAX_RUN_TRIES = 6
#: A Pokemon this many levels above the foe is not switched out for a bad type matchup.
OUTLEVELS = 5
#: Better balls, in the order a person reaches for them on a hard catch (a Master Ball is never used by habit).
GREAT_BALLS = ("Ultra Ball", "Great Ball")
#: HM moves: the game refuses to forget them in a level-up (`IsHMMove2`).
HM_MOVES = frozenset({"Cut", "Fly", "Surf", "Strength", "Flash", "Rock Smash", "Waterfall", "Dive"})
#: Rough worth of moves whose damage is not the power formula's (`knowledge` fixed_damage), as an equivalent power.
FIXED_POWER = {"SONICBOOM": 30, "DRAGON_RAGE": 55, "SUPER_FANG": 50, "ENDEAVOR": 30, "COUNTER": 40, "MIRROR_COAT": 40,
               "BIDE": 40, "PSYWAVE": None, "LEVEL_DAMAGE": None, "OHKO": 0}
#: Worth of a status move when a move is LEARNED (never in a fight's choice: a status move is not chosen by habit).
STATUS_WORTH = {"SLEEP": 18, "PARALYZE": 16, "TOXIC": 14, "POISON": 10, "CONFUSE": 10, "LEECH_SEED": 12,
                "ATTACK_UP_2": 14, "SPECIAL_ATTACK_UP_2": 14, "DRAGON_DANCE": 16, "BULK_UP": 14, "CALM_MIND": 14,
                "EVASION_UP": 9, "MINIMIZE": 9, "RESTORE_HP": 14, "SOFTBOILED": 14, "MORNING_SUN": 12, "SYNTHESIS": 12,
                "MOONLIGHT": 12, "REST": 10, "PROTECT": 8, "SUBSTITUTE": 10, "REFLECT": 9, "LIGHT_SCREEN": 9,
                "ATTACK_UP": 9, "DEFENSE_UP": 5, "DEFENSE_UP_2": 7, "SPEED_UP_2": 9, "FOCUS_ENERGY": 4, "ATTACK_DOWN": 4,
                "DEFENSE_DOWN": 4, "ACCURACY_DOWN": 5, "SPEED_DOWN": 4, "ATTACK_DOWN_2": 6, "DEFENSE_DOWN_2": 6,
                "FORESIGHT": 2, "ROAR": 3, "TELEPORT": 1, "SPLASH": 0}
STATUS_DEFAULT = 4


@dataclass(frozen=True)
class Temperament:
    """How a personality battles (taste, not strategy; plausible values, not measured from people)."""

    near_best: float  # moves within this share of the best are about as good (a seeded, value-weighted draw among them)
    catch_new: float  # the chance it wants a species it has not caught (one draw per species per run)
    run_travel: float  # the chance it runs from a wild battle it does not want while travelling
    switch_willing: float  # the chance it says YES to "Will ... change POKéMON?" when the switch rule finds a better one
    heal_below: float  # its Pokemon's HP share under which it heals in an important battle
    run_low: float  # training: its Pokemon's HP share under which it runs from a wild battle


TEMPERAMENTS: dict[str, Temperament] = {
    "Catcher": Temperament(near_best=0.80, catch_new=1.0, run_travel=0.6, switch_willing=0.5, heal_below=0.25, run_low=0.25),
    "Story": Temperament(near_best=0.85, catch_new=0.6, run_travel=0.8, switch_willing=0.3, heal_below=0.30, run_low=0.30),
    "Trainer": Temperament(near_best=0.90, catch_new=0.75, run_travel=0.2, switch_willing=0.8, heal_below=0.25, run_low=0.20),
}


@dataclass(frozen=True)
class BattleFaults:
    """FAULT switches of the decider (test side: `gates/live_step4.py`, `gates/test_battle.py`); none on the happy path."""

    ignore_types: bool = False  # every matchup neutral and no STAB: the TYPE arm's fault
    ignore_recoil: bool = False  # no recoil penalty: the RECOIL fault
    #: (the step-4 verifier's round) the recoil charged on the move's whole worth, as step 4 did: no cap at the HP the hit
    #: can take, no Jump Kick cap, no self-faint check (the RECOIL-FAULT plan of `gates/rate_step4.py`)
    uncapped_recoil: bool = False
    #: (the step-4 verifier's round) the replacement after a faint sees only the look on screen, as step 4 did: the party
    #: menu shows no battle view, so nobody is "on the field" and no foe is in view (the FIELD fault)
    forget_field: bool = False
    #: (the step-4 verifier's round) the skill does not read the party menu's refusal ("... is already in battle!"): it
    #: watches the menu until its bound, as step 4 did (the REFUSE fault)
    ignore_refusal: bool = False


@dataclass(frozen=True)
class MoveValue:
    slot: int
    name: str
    value: float
    base: float
    effectiveness: float
    stab: float
    hit_chance: float
    power: float
    recoil: float
    status: bool

    def line(self) -> str:
        if self.status:
            return f"{self.name}: a status move (0)"
        return (f"{self.name}: {self.value:.1f} = x{self.effectiveness:g} type x{self.stab:g} STAB x {self.power:g} power x "
                f"{self.hit_chance:.2f} hit{f' - {self.recoil:.1f} recoil' if self.recoil else ''}")


@dataclass(frozen=True)
class Decision:
    """What to do at the battle's action menu (`action`: fight, ball, switch, item, run), and why."""

    action: str
    reason: str
    move_slot: int | None = None
    move_name: str | None = None
    ball: str | None = None
    switch_pid: int | None = None
    item: str | None = None
    target_pid: int | None = None
    values: tuple[str, ...] = ()
    #: a double battle: the battler POSITION the move is aimed at (1 the foe's left, 3 its right), None in a single one
    target: int | None = None
    #: (the step-4 verifier's round: "TYPE 'rate across seeds' is not a rate") what the TYPE CHART changed in this choice of
    #: the best move, told with it (`TypeSay`); None for a choice that is not "the best move" (a weakening hit for a catch)
    types: "TypeSay | None" = None


@dataclass(frozen=True)
class TypeSay:
    """(the step-4 verifier's round) The type chart's part in one choice of a move (`BattleMind._type_say`): the moves about
    as good as the best WITH the chart (`near`, the near-best set the draw picks from), the best with every matchup neutral
    and no STAB (`blind`: what a person who knew no types would take), and how many moves could hurt. DECISIVE when `blind`
    is not in `near`: the chart turns the type-blind choice into a poor one (`gates/rate_step4.py` TYPE-DECISIONS counts
    these, and what the GAME shows chosen)."""

    near: tuple[str, ...]
    blind: str
    hurting: int

    @property
    def decisive(self) -> bool:
        return bool(self.near) and self.blind not in self.near

    def line(self) -> str:
        return (f"{{types: about as good with the chart {list(self.near)}; with no types the best {self.blind}; {self.hurting} "
                f"that hurt{'; DECISIVE' if self.decisive else ''}}}")


@dataclass(frozen=True)
class LearnChoice:
    learn: bool
    forget: str | None  # the move to forget (its name), None when it does not learn
    reason: str


def move_key(name: str) -> str:
    """A move or species name as the screen prints it ("MUD-SLAP", "POKé BALL") and as the knowledge spells it."""
    return re.sub(r"[^a-z0-9]", "", name.casefold().replace("é", "e"))


def _fact(move: MoveSlot) -> MoveFact | None:
    return move_fact(move.name)


def _power(fact: MoveFact | None, move: MoveSlot, user_level: int) -> float:
    """The power a person weighs a move by: its printed power, or an equivalent for a fixed-damage move (Seismic Toss and
    Night Shade deal the user's level; Psywave about that)."""
    if fact is None:
        return float(move.power)
    if fact.fixed_damage:
        worth = FIXED_POWER.get(fact.effect)
        if worth is None:
            return float(min(100, max(20, user_level * 1.2)))
        return float(worth)
    return float(fact.power)


@dataclass(frozen=True)
class RecoilRisk:
    """(the step-4 verifier's round) What a recoil move's hit would actually cost its user against THIS foe, from the
    damage estimate (`damage_fraction`): `landed` the share of its damage the foe can take (a hit takes at most what the
    foe has left: `src/battle_script_commands.c` Cmd_datahpupdate sets gHpDealt to the damage or the target's HP, whichever
    is less, and the recoil is gHpDealt / 4 or / 3); `miss_capped` the share of Jump Kick's miss recoil that counts (half
    the damage it would have dealt, at most half the target's max HP: `DMG_RECOIL_FROM_MISS`); `faints_user` when the
    recoil, in HP, is at least the user's HP left. The defaults are "no estimate": the recoil of the whole worth."""

    landed: float = 1.0
    miss_capped: float = 1.0
    faints_user: bool = False
    recoil_hp: float | None = None


NO_ESTIMATE = RecoilRisk()


def recoil_penalty(fact: MoveFact | None, damage_worth: float, hp_share: float, full_worth: float | None = None,
                   risk: RecoilRisk = NO_ESTIMATE) -> float:
    """What the move costs its user, in the same units as its worth, weighed by how much HP the user has left: half at
    full HP, three times at none (a person risks recoil when healthy and not when one hit from fainting).
      * recoil of the damage dealt (Take Down 1/4, Double-Edge 1/3): that share of the worth the hit can LAND
        (`risk.landed`: against a foe with less HP left than the hit deals, the recoil is a share of what it has left);
      * recoil on a miss (Jump Kick, Hi Jump Kick: half the damage it would have dealt, at most half the target's max
        HP): the miss chance x half the worth it would have had (`full_worth`, the worth before the hit chance), capped
        (`risk.miss_capped`);
      * a recoil that would knock the user out (`risk.faints_user`): its whole worth (the hit's, or on a miss the miss
        chance of it), as a self-KO move;
      * self-KO (Selfdestruct, Explosion): its whole worth, unless the user is about to faint anyway (then 40 %)."""
    if fact is None:
        return 0.0
    weight = 0.5 + 2.5 * (1.0 - max(0.0, min(1.0, hp_share)))
    if fact.recoil_kind == "of_damage_dealt":
        if risk.faints_user:
            return damage_worth
        return damage_worth * fact.recoil_fraction * risk.landed * weight
    if fact.recoil_kind == "if_it_misses":
        whole = full_worth if full_worth is not None else damage_worth
        if risk.faints_user:
            return whole * (1.0 - fact.hit_chance)
        return whole * (1.0 - fact.hit_chance) * fact.recoil_fraction * risk.miss_capped * weight
    if fact.self_ko:
        return damage_worth * (1.0 if hp_share > 0.15 else 0.4)
    return 0.0


def move_value(slot: int, move: MoveSlot, user_types: tuple[str, ...], user_level: int, hp_share: float,
               foe_types: tuple[str, ...], faults: BattleFaults = BattleFaults(),
               risk: RecoilRisk = NO_ESTIMATE) -> MoveValue | None:
    """A move's worth against this foe (module docstring); None when it cannot be used (no PP left). `risk`: what its
    recoil would cost against this foe (`recoil_risk`; the default: no estimate, the recoil of the whole worth)."""
    if move.pp is not None and move.pp <= 0:
        return None
    fact = _fact(move)
    mtype = fact.type if fact is not None else move.type
    power = _power(fact, move, user_level)
    if (fact is not None and fact.category == "status") or power <= 0:
        return MoveValue(slot, move.name, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, True)
    if fact is not None and fact.two_turn:
        power *= 0.5  # it takes two turns (or a turn's warning)
    if fact is not None and fact.recharge:
        power *= 0.6  # the user rests the next turn
    effectiveness = 1.0 if faults.ignore_types else type_multiplier(mtype, foe_types)
    if fact is not None and fact.fixed_damage and effectiveness > 0:
        effectiveness = 1.0  # fixed damage ignores the matchup (an immunity still holds)
    bonus = 1.0 if faults.ignore_types else stab(mtype, user_types)
    hit = fact.hit_chance if fact is not None else 1.0
    full = effectiveness * bonus * power
    base = full * hit
    if faults.uncapped_recoil:
        risk = NO_ESTIMATE  # FAULT: the step-4 rule (the recoil of the whole worth)
    penalty = 0.0 if faults.ignore_recoil else recoil_penalty(fact, base, hp_share, full, risk)
    return MoveValue(slot, move.name, base - penalty, base, effectiveness, bonus, hit, power, penalty, False)


def estimate_stat(base: int, level: int, hp: bool = False) -> int:
    """A Pokemon's stat as a person would guess it from its species and level (average IVs, no EVs, a neutral nature:
    `src/pokemon.c` CalculateMonStats with IV 15, EV 0)."""
    if hp:
        return (2 * base + 15) * level // 100 + level + 10
    return (2 * base + 15) * level // 100 + 5


def damage_fraction(move: MoveSlot, user: MonSummary | None, user_battler: BattleMon, foe: BattleMon,
                    faults: BattleFaults = BattleFaults()) -> tuple[float, float] | None:
    """The share of the foe's max HP one hit of `move` takes, (lowest roll, highest roll), by the game's damage formula
    (`src/pokemon.c` CalculateBaseDamage: ((2L/5+2) x power x A / D) / 50 + 2, x STAB x type, x 85-100 %) with the user's
    own stats (the summary screen's) and the foe's guessed from its species and level (`estimate_stat`); no critical hit.
    None for a status move or one whose foe is unknown."""
    fact = _fact(move)
    power = _power(fact, move, user_battler.level)
    if power <= 0 or (fact is not None and fact.category == "status"):
        return None
    foe_species = species_fact(foe.species)
    if foe_species is None:
        return None
    mtype = fact.type if fact is not None else move.type
    physical = (fact.category == "physical") if fact is not None else True
    if user is not None and len(user.stats) == 5:
        attack = user.stats[0] if physical else user.stats[3]
    else:
        mine = species_fact(user_battler.species)
        attack = estimate_stat((mine.attack if physical else mine.sp_attack) if mine else 50, user_battler.level)
    defense = estimate_stat(foe_species.defense if physical else foe_species.sp_defense, foe.level)
    hp = estimate_stat(foe_species.hp, foe.level, hp=True)
    if fact is not None and fact.fixed_damage:
        flat = {"SONICBOOM": 20, "DRAGON_RAGE": 40, "LEVEL_DAMAGE": user_battler.level, "PSYWAVE": user_battler.level}
        if fact.effect in flat:
            share = flat[fact.effect] / hp
            return share, share
        return None
    effectiveness = 1.0 if faults.ignore_types else type_multiplier(mtype, foe.types)
    bonus = 1.0 if faults.ignore_types else stab(mtype, user_battler.types)
    damage = ((2 * user_battler.level // 5 + 2) * power * attack / max(1, defense)) / 50 + 2
    damage *= bonus * effectiveness
    return damage * 0.85 / hp, damage / hp


def recoil_risk(move: MoveSlot, user: MonSummary | None, user_battler: BattleMon, foe: BattleMon,
                faults: BattleFaults = BattleFaults()) -> RecoilRisk:
    """(the step-4 verifier's round) What a recoil move would cost its user against `foe` (`RecoilRisk`), from one hit's
    average damage roll as a share of the foe's max HP (`damage_fraction`) and the foe's bar: Take Down's recoil is a
    quarter of the HP the hit TAKES, at most what the bar has left; Jump Kick's miss recoil half the damage it would have
    dealt, at most half the foe's max HP; in HP (the foe's max HP guessed from its species and level, as the damage is)
    against the user's HP left. `NO_ESTIMATE` for a move without recoil or a foe it cannot estimate."""
    fact = _fact(move)
    if fact is None or fact.recoil_kind is None:
        return NO_ESTIMATE
    guess = damage_fraction(move, user, user_battler, foe, faults)
    foe_species = species_fact(foe.species)
    if guess is None or foe_species is None:
        return NO_ESTIMATE
    share = (guess[0] + guess[1]) / 2
    if share <= 0:
        return NO_ESTIMATE
    left = max(0.0, foe.hp_bar / HP_BAR_PIXELS)
    foe_max = estimate_stat(foe_species.hp, foe.level, hp=True)
    landed, miss_capped = 1.0, 1.0
    if fact.recoil_kind == "of_damage_dealt":
        landed = min(1.0, left / share)
        recoil_hp = max(1.0, foe_max * min(share, left) * fact.recoil_fraction)
    else:
        if fact.recoil_capped:
            miss_capped = min(1.0, 1.0 / share)
        recoil_hp = foe_max * share * fact.recoil_fraction * miss_capped
    faints = user_battler.hp is not None and recoil_hp >= user_battler.hp
    return RecoilRisk(landed, miss_capped, faints, recoil_hp)


def matchup(types: tuple[str, ...], moves: tuple[MoveSlot, ...], level: int, foe: BattleMon,
            faults: BattleFaults = BattleFaults()) -> tuple[float, float, float]:
    """How well a Pokemon of `types` with `moves` fares against `foe`: (score, its best move's worth, the foe's worst
    threat to it). The threat is the foe's OWN types against it (a person expects a Pokemon to use moves of its type), or
    a move the foe has used, whichever is worse; the score is the best worth over the threat, scaled by how the two
    LEVELS compare ((level / foe level) ^ 1.5, between 0.3 and 1.5: a person does not send a much weaker Pokemon in
    because its type is right; measured 2026-10-08 on Route 116, without it the AI swapped its L14 Mudkip for a L6
    Whismur against a L9 Shroomish)."""
    best = 0.0
    for slot, move in enumerate(moves):
        value = move_value(slot, move, types, level, 1.0, foe.types, faults)
        if value is not None and not value.status:
            best = max(best, value.value)
    threats = [type_multiplier(t, types) for t in foe.types]
    threats += [type_multiplier(m.type, types) for m in foe.moves if m.power > 0]
    threat = 1.0 if faults.ignore_types else max(threats or [1.0])
    levels = min(1.5, max(0.3, (level / max(1, foe.level)) ** 1.5))
    return best / max(threat, 0.25) * levels, best, threat


def general_value(name: str, user_types: tuple[str, ...], user_level: int) -> float:
    """A move's worth to its Pokemon in GENERAL (no foe in view), for deciding what to keep when it learns a move: a
    damaging move by power x hit chance x STAB (two-turn and recharge moves less; recoil weighed at full HP), a status
    move by a small worth of its effect (`STATUS_WORTH`)."""
    fact = move_fact(name)
    if fact is None:
        return 0.0
    power = _power(fact, MoveSlot(name, fact.type, fact.power, None, None), user_level)
    if fact.category == "status" or power <= 0:
        return float(STATUS_WORTH.get(fact.effect, STATUS_DEFAULT))
    if fact.two_turn:
        power *= 0.5
    if fact.recharge:
        power *= 0.6
    full = power * stab(fact.type, user_types)
    base = full * fact.hit_chance
    return base - recoil_penalty(fact, base, 1.0, full)


def needs_rest(party: tuple[MonSummary, ...] | None) -> str | None:
    """Whether a person would stop TRAINING now and look for a Pokemon Center (step 5's goals take it there): its
    strongest Pokemon (the one doing the work, the highest level) has fainted or is under a third of its HP, or the party
    has less than a third of its HP left in all. None while it can go on."""
    mons = [m for m in party or () if not m.is_egg]
    if not mons:
        return None
    strongest = max(mons, key=lambda m: (m.level, m.max_hp))
    if strongest.hp <= 0:
        return f"its strongest Pokemon, {strongest.species} L{strongest.level}, has fainted"
    if strongest.hp < strongest.max_hp / 3:
        return f"its strongest Pokemon, {strongest.species} L{strongest.level}, is low ({strongest.hp}/{strongest.max_hp})"
    total, most = sum(max(0, m.hp) for m in mons), sum(m.max_hp for m in mons)
    if most and total < most / 3:
        return f"the party has {total} of {most} HP left"
    return None


def learn_choice(mon: MonSummary, new_move: str) -> LearnChoice:
    """Learn `new_move` (forgetting the known move worth least to this Pokemon) only when it is worth clearly more than
    that move (15 % and 5 points more): a person does not churn a moveset for a trifle. A new damaging TYPE the Pokemon has
    no move of is worth a little more (coverage). An HM is never forgotten (the game refuses it)."""
    new_fact = move_fact(new_move)
    if new_fact is None:
        return LearnChoice(False, None, f"{new_move} is not a move it knows anything about: keep the moves it has")
    known = [m.name for m in mon.moves]
    worth = {name: general_value(name, mon.types, mon.level) for name in known}
    new_worth = general_value(new_move, mon.types, mon.level)
    damaging_types = {move_fact(n).type for n in known if move_fact(n) is not None and move_fact(n).category != "status"}
    if new_fact.category != "status" and new_fact.type not in damaging_types:
        new_worth *= 1.15
    forgettable = [n for n in known if n not in HM_MOVES]
    if not forgettable:
        return LearnChoice(False, None, f"every move it knows is an HM: keep them ({known})")
    weakest = min(forgettable, key=lambda n: (worth[n], n))
    table = ", ".join(f"{n} {worth[n]:.0f}" for n in known)
    if new_worth > worth[weakest] * 1.15 + 5:
        return LearnChoice(True, weakest, f"{new_move} ({new_worth:.0f}) is worth clearly more than {weakest} "
                                          f"({worth[weakest]:.0f}), the weakest of [{table}]: forget {weakest}")
    return LearnChoice(False, None, f"{new_move} ({new_worth:.0f}) is not worth clearly more than {weakest} "
                                    f"({worth[weakest]:.0f}), the weakest of [{table}]: keep the four it has")


@dataclass
class _Memory:
    """What the decider remembers within ONE battle."""

    foe_key: str = ""
    turns: int = 0
    throws: int = 0
    weaken_turns: int = 0
    switches: int = 0
    switched_against: set = field(default_factory=set)
    heals: int = 0
    runs: int = 0
    want_catch: bool = False
    new_species: bool = False
    last_bar: int | None = None
    last_move: str | None = None
    #: the bar each of its moves took off this foe (a person learns "Tackle took a third of its HP")
    observed: dict = field(default_factory=dict)


class BattleMind:
    """The decider for one run: its personality's temperament, the run's CHOICES stream (`rng`: the move draws, the catch
    wishes, the switch answers), the PURPOSE of the battles ("train": fight wild battles for experience; "travel": run
    from those it does not want), and what it remembers within the battle being fought (`begin` starts a battle)."""

    def __init__(self, personality: str, rng: random.Random, purpose: str = "train",
                 faults: BattleFaults = BattleFaults()) -> None:
        self.personality = personality if personality in TEMPERAMENTS else "Story"
        self.temper = TEMPERAMENTS[self.personality]
        self.rng = rng
        self.purpose = purpose
        self.faults = faults
        self.memory = _Memory()
        #: species -> the run's wish to catch it (drawn once, seeded)
        self.wishes: dict[str, bool] = {}
        self.log: list[str] = []
        #: (the step-4 verifier's round) THE FIELD AS LAST SEEN (`see`): the party menu covers the battle and its look has
        #: no battle view, so who stands on the field and whom it faces are REMEMBERED from the last look at the battle
        self.field: BattleView | None = None
        #: PIDs sent in (`sent`) or refused by the game (`refuse`, with its words) since the last action menu: not yet seen
        #: on the field, or not able to go in
        self.sent_since: set[int] = set()
        self.refused: dict[int, str] = {}

    # ------------------------------------------------------------------ what it remembers of the field
    def enter(self) -> None:
        """A battle is on screen (the skill starts): nothing remembered of a field yet."""
        self.field, self.sent_since, self.refused = None, set(), {}

    def see(self, look: Observation) -> None:
        """Every look the hands take during a battle (a watcher of `skills/battle.py`): a look AT the battle (a battle view)
        is the field as it stands now; at the action menu a new turn begins, and what was sent in or refused before it is
        on the field now (or no longer refused)."""
        if look.battle is None:
            return
        self.field = look.battle
        ui = look.screen.ui if look.screen is not None else None
        if ui is not None and ui.kind == "battle_action":
            self.sent_since, self.refused = set(), {}

    def sent(self, pid: int) -> None:
        """The game took `pid` in (SEND OUT): it is on the field from now on, though no look has shown it there yet."""
        self.sent_since.add(pid)

    def refuse(self, pid: int, words: str) -> None:
        """The game refused `pid` ("... is already in battle!", "... has no energy left to battle!"): never chosen again
        until the next turn."""
        self.refused[pid] = words

    def on_field(self, look: Observation) -> tuple[BattleView | None, bool]:
        """(the field the replacement is chosen against, whether it is REMEMBERED): the look's own battle view, or, when
        the look has none (the party menu covers the battle), the last one seen (FAULT `forget_field`: none)."""
        if look.battle is not None:
            return look.battle, False
        if self.faults.forget_field or self.field is None:
            return None, False
        return self.field, True

    # ------------------------------------------------------------------ a battle begins
    def begin(self, look: Observation) -> str:
        """A new battle (its first look with a foe): remember the foe; for a WILD species not in the Pokedex's OWNED list,
        decide (once per species per run) whether this personality wants it."""
        self.memory = _Memory()
        battle = look.battle
        foe = battle.foe[0] if battle is not None and battle.foe else None
        if battle is None or foe is None:
            return "a battle with no foe in view yet"
        self.memory.foe_key = f"{foe.species}:{foe.level}"
        owned = set(look.progress.owned_dex) if look.progress is not None else set()
        self.memory.new_species = battle.kind == "wild" and foe.dex not in owned
        if self.memory.new_species:
            if foe.species not in self.wishes:
                self.wishes[foe.species] = self.rng.random() < self.temper.catch_new
            self.memory.want_catch = self.wishes[foe.species]
        what = (f"a {battle.kind} battle against {foe.species} L{foe.level} ({'/'.join(foe.types)})"
                + (f"; a species it has not caught: {'it WANTS it' if self.memory.want_catch else 'it lets this one go'} "
                   f"({self.personality}: catch_new {self.temper.catch_new})" if self.memory.new_species else ""))
        return what

    def next_foe(self, look: Observation) -> None:
        """The foe changed (a trainer sent out its next Pokemon): what it learned about the last foe is forgotten; the
        battle's counts (balls, switches, heals) stay."""
        battle = look.battle
        foe = battle.foe[0] if battle is not None and battle.foe else None
        mem = self.memory
        mem.foe_key = f"{foe.species}:{foe.level}" if foe is not None else ""
        mem.last_bar, mem.last_move, mem.observed, mem.weaken_turns = None, None, {}, 0

    # ------------------------------------------------------------------ the action menu
    def decide(self, look: Observation, battler: int | None = None) -> Decision:
        """The decision at the action menu of the player's battler at `battler` (its position; None: the first)."""
        battle = look.battle
        if battle is None or not battle.own:
            return Decision("fight", "no battle view: the first usable move", move_slot=0)
        own = next((m for m in battle.own if battler is not None and m.battler == battler), battle.own[0])
        if battle.double and len(battle.foe) > 1:
            self.memory.turns += 1
            return self._fight_double(own, battle.foe, look)
        foe = battle.foe[0] if battle.foe else None
        mem = self.memory
        mem.turns += 1
        self._observe(foe)
        hp_share = own.hp / own.max_hp if own.hp is not None and own.max_hp else 1.0
        if foe is None:
            return self._fight(own, None, look, "the foe is not in view: its strongest move")
        values = self._values(own, foe, hp_share, look)
        if battle.kind == "wild" and mem.want_catch:
            decision = self._catch(look, own, foe, hp_share, values)
            if decision is not None:
                return decision
        if battle.kind == "wild":
            decision = self._run_or_not(own, foe, hp_share)
            if decision is not None:
                return decision
        decision = self._switch(look, own, foe)
        if decision is not None:
            return decision
        if battle.kind == "trainer":
            decision = self._heal(look, own, foe, hp_share)
            if decision is not None:
                return decision
        return self._fight(own, foe, look, "", values)

    def _observe(self, foe: BattleMon | None) -> None:
        """What its last move took off the foe's bar (calibrates the damage guess of the next weakening move)."""
        mem = self.memory
        if foe is None:
            return
        if mem.last_bar is not None and mem.last_move is not None and foe.hp_bar <= mem.last_bar:
            mem.observed[mem.last_move] = (mem.last_bar - foe.hp_bar) / HP_BAR_PIXELS
        mem.last_bar = foe.hp_bar
        mem.last_move = None

    def _values(self, own: BattleMon, foe: BattleMon, hp_share: float, look: Observation | None) -> list[MoveValue]:
        user = next((m for m in (look.party if look is not None else None) or () if m.pid == own.pid), None)
        out = []
        for slot, move in enumerate(own.moves):
            risk = recoil_risk(move, user, own, foe, self.faults)
            value = move_value(slot, move, own.types, own.level, hp_share, foe.types, self.faults, risk)
            if value is not None:
                out.append(value)
        return out

    def choose_move(self, values: list[MoveValue]) -> tuple[MoveValue | None, str]:
        """The move: a seeded, value-weighted draw among those within `near_best` of the best (a clear winner is chosen
        every time); with nothing that hurts, any move it still can use (a status move only then)."""
        hurting = [v for v in values if not v.status and v.value > 0]
        if not hurting:
            usable = [v for v in values]
            if not usable:
                return None, "no move has PP left: FIGHT (the game makes it STRUGGLE)"
            pick = self.rng.choice(usable)
            return pick, f"nothing it has can hurt this foe: {pick.name} (a status move, as a last resort)"
        best = max(v.value for v in hurting)
        floor = self.temper.near_best * best
        near = [v for v in hurting if v.value >= floor]
        if len(near) == 1:
            return near[0], f"{near[0].name} is clearly the best"
        weights = [v.value - floor + 0.05 * best for v in near]
        pick = self.rng.choices(near, weights=weights, k=1)[0]
        return pick, (f"{pick.name}, drawn among the about-as-good {[v.name for v in near]} (within "
                      f"{self.temper.near_best:.0%} of the best, weighted by worth)")

    def _fight(self, own: BattleMon, foe: BattleMon | None, look: Observation, why: str,
               values: list[MoveValue] | None = None) -> Decision:
        hp_share = own.hp / own.max_hp if own.hp is not None and own.max_hp else 1.0
        if values is None:
            if foe is not None:
                values = self._values(own, foe, hp_share, look)
            else:
                values = [move_value(s, m, own.types, own.level, hp_share, (), self.faults) for s, m in enumerate(own.moves)]
                values = [v for v in values if v is not None]
        pick, reason = self.choose_move(values)
        lines = tuple(v.line() for v in values)
        if pick is None:
            return Decision("fight", reason, move_slot=None, values=lines)
        self.memory.last_move = pick.name
        say = self._type_say(values, lambda faults: self._values_with(own, foe, hp_share, look, faults)) if foe is not None else None
        return Decision("fight", f"{why + ': ' if why else ''}{reason}", move_slot=pick.slot, move_name=pick.name,
                        values=lines, types=say)

    def _values_with(self, own: BattleMon, foe: BattleMon, hp_share: float, look: Observation | None,
                     faults: BattleFaults) -> list[MoveValue]:
        """`_values` with other fault switches (the type chart's counterfactual, `_type_say`)."""
        mine, self.faults = self.faults, faults
        try:
            return self._values(own, foe, hp_share, look)
        finally:
            self.faults = mine

    def _type_say(self, values: list, valued_with) -> "TypeSay | None":
        """(the step-4 verifier's round) What the TYPE CHART did to this choice (`TypeSay`): the near-best set WITH the chart
        and the best with no types, whichever of the two the decider played with (under the `ignore_types` fault the chart's
        side is the counterfactual). `values`: the MoveValues it chose from; `valued_with(faults)`: the same, with other
        switches. Told with the choice; it changes nothing chosen."""
        from dataclasses import replace as _replace

        typed = values if not self.faults.ignore_types else valued_with(_replace(self.faults, ignore_types=False))
        blind = values if self.faults.ignore_types else valued_with(_replace(self.faults, ignore_types=True))
        hurting = [v for v in typed if not v.status and v.value > 0]
        blind_hurting = [v for v in blind if not v.status and v.value > 0]
        if not hurting or not blind_hurting:
            return None
        best = max(v.value for v in hurting)
        near = tuple(sorted({v.name for v in hurting if v.value >= self.temper.near_best * best}))
        top = max(blind_hurting, key=lambda v: (v.value, -v.slot))
        # `hurting`: the moves that attack at all (with no types: every damaging move with PP), what a type-blind person
        # chooses among (the chance a random one of them is in `near` is the chance figure of the sweep)
        return TypeSay(near, top.name, len({v.name for v in blind_hurting}))

    def _fight_double(self, own: BattleMon, foes: tuple[BattleMon, ...], look: Observation | None = None) -> Decision:
        """A DOUBLE battle (two foes on the field): every (move, foe) pair is valued against that foe; a move that hits
        both foes at once by its worth against each, halved (Gen 3 halves it: `src/pokemon.c` CalculateBaseDamage, `if
        ((gBattleTypeFlags & BATTLE_TYPE_DOUBLE) && gBattleMoves[move].target == MOVE_TARGET_BOTH &&
        CountAliveMonsInBattle(BATTLE_ALIVE_DEF_SIDE) == 2) damage /= 2`), and one that also hits its own partner
        (MOVE_TARGET_FOES_AND_ALLY: Earthquake) at three quarters, a rough charge for the partner's share; the same
        near-best draw picks one. In a double battle the decider does not switch, heal, catch or run (a known limit of
        step 4: a trainer's double battle cannot be run from, and wild double battles do not happen in Emerald)."""
        hp_share = own.hp / own.max_hp if own.hp is not None and own.max_hp else 1.0
        user = next((m for m in (look.party if look is not None else None) or () if m.pid == own.pid), None)
        candidates, lines = self._double_candidates(own, foes, hp_share, user, self.faults)
        pick, reason = self.choose_move([v for v, _ in candidates])
        if pick is None:
            return Decision("fight", reason, values=tuple(lines))
        target = next(t for v, t in candidates if v is pick)
        aimed = next((f.species for f in foes if f.battler == target), None)
        say = self._type_say([v for v, _ in candidates],
                             lambda faults: [v for v, _ in self._double_candidates(own, foes, hp_share, user, faults)[0]])
        return Decision("fight", f"a double battle: {reason}{f' at {aimed}' if aimed else ''}", move_slot=pick.slot,
                        move_name=pick.name, values=tuple(lines), target=target, types=say)

    def _double_candidates(self, own: BattleMon, foes: tuple[BattleMon, ...], hp_share: float, user: MonSummary | None,
                           faults: BattleFaults) -> tuple[list[tuple[MoveValue, int | None]], list[str]]:
        """Every (move, foe) pair of a double battle valued against that foe, a spread move once for both (`_fight_double`),
        with the fault switches `faults` (the decider's own, or the type chart's counterfactual)."""
        candidates: list[tuple[MoveValue, int | None]] = []
        lines = []
        for slot, move in enumerate(own.moves):
            fact = move_fact(move.name)
            spread = fact is not None and fact.target in ("BOTH", "FOES_AND_ALLY")
            per_foe = []
            for foe in foes:
                value = move_value(slot, move, own.types, own.level, hp_share, foe.types, faults,
                                   recoil_risk(move, user, own, foe, faults))
                if value is not None:
                    per_foe.append((value, foe))
            if not per_foe:
                continue
            if spread or per_foe[0][0].status:
                share = 1.0 if not spread else (0.5 if fact.target == "BOTH" else 0.75)
                total = sum(v.value for v, _ in per_foe) * share
                first = per_foe[0][0]
                merged = MoveValue(first.slot, first.name, total, total, first.effectiveness, first.stab, first.hit_chance,
                                   first.power, first.recoil, first.status)
                candidates.append((merged, None))
                lines.append(f"{merged.name} (both foes): {total:.1f}")
                continue
            for value, foe in per_foe:
                candidates.append((value, foe.battler))
                lines.append(f"{value.line()} -> {foe.species}")
        return candidates, lines

    # ------------------------------------------------------------------ catching
    def _catch(self, look: Observation, own: BattleMon, foe: BattleMon, hp_share: float,
               values: list[MoveValue]) -> Decision | None:
        mem = self.memory
        balls = [(name, count) for name, count in (look.bag.balls if look.bag is not None else ()) if count > 0
                 and name != "Master Ball"]
        if not balls or mem.throws >= MAX_THROWS:
            mem.want_catch = False
            self.log.append(f"no ball left to throw ({mem.throws} thrown): it fights or runs instead")
            return None
        bar = foe.hp_bar / HP_BAR_PIXELS
        if bar > 0.5 and mem.weaken_turns < MAX_WEAKEN_TURNS and hp_share >= 0.3:
            move, why = self._weakening_move(look, own, foe, bar, values)
            if move is not None:
                mem.weaken_turns += 1
                mem.last_move = move.name
                return Decision("fight", f"to CATCH {foe.species}: weaken it first ({why})", move_slot=move.slot,
                                move_name=move.name, values=tuple(v.line() for v in values))
            reason = f"to CATCH {foe.species}: {why}: throw now"
        else:
            reason = (f"to CATCH {foe.species}: its bar is at {bar:.0%}" if bar <= 0.5 else
                      f"to CATCH {foe.species}: {mem.weaken_turns} weakening turns already" if mem.weaken_turns >= MAX_WEAKEN_TURNS
                      else f"to CATCH {foe.species}: its own HP is low ({hp_share:.0%}): throw before it is too late")
        ball = self._ball(balls, foe)
        mem.throws += 1
        return Decision("ball", f"{reason}: throw a {ball} (ball {mem.throws}, {sum(c for _, c in balls)} in the bag)",
                        ball=ball)

    def _weakening_move(self, look: Observation, own: BattleMon, foe: BattleMon, bar: float,
                        values: list[MoveValue]) -> tuple[MoveValue | None, str]:
        """The move that takes the most off the foe's bar while, at its best roll, leaving at least `KO_MARGIN`: so a
        weaker move when the bar is already low. None when every move could knock it out."""
        user = next((m for m in look.party or () if m.pid == own.pid), None)
        safe = []
        for value in values:
            if value.status or value.value <= 0:
                continue
            move = own.moves[value.slot]
            guess = damage_fraction(move, user, own, foe, self.faults)
            if guess is None:
                continue
            low, high = guess
            seen = self.memory.observed.get(move.name)
            if seen is not None and seen > 0:
                high = max(high, seen * 1.15)  # it saw what this move does to this foe
                low = min(low, seen)
            if bar - high >= KO_MARGIN:
                safe.append((low + high, value, low, high))
        if not safe:
            return None, f"every move could knock it out (its bar {bar:.0%})"
        safe.sort(key=lambda s: (-s[0], s[1].slot))
        _, value, low, high = safe[0]
        return value, f"{value.name} takes {low:.0%}-{high:.0%} of its HP and its bar is at {bar:.0%}: it cannot knock it out"

    def _ball(self, balls: list[tuple[str, int]], foe: BattleMon) -> str:
        """A Poke Ball for an easy catch; a better ball for a hard one (catch rate under 100) or after two misses."""
        names = [name for name, _ in balls]
        species = species_fact(foe.species)
        hard = species is not None and species.catch_rate < 100
        if hard or self.memory.throws >= 2:
            for better in GREAT_BALLS:
                if better in names:
                    return better
        for plain in ("Poké Ball", "Premier Ball"):
            if plain in names:
                return plain
        return names[0]

    # ------------------------------------------------------------------ running
    def _run_or_not(self, own: BattleMon, foe: BattleMon, hp_share: float) -> Decision | None:
        mem = self.memory
        if mem.runs >= MAX_RUN_TRIES:
            return None
        bar = foe.hp_bar / HP_BAR_PIXELS
        reason = None
        if self.purpose == "train":
            if hp_share < self.temper.run_low and bar > 0.3:
                reason = f"its {own.species} is low ({hp_share:.0%}) and the foe is not ({bar:.0%}): not worth the risk"
            elif foe.level - own.level >= 6:
                reason = f"{foe.species} L{foe.level} is far stronger than its {own.species} L{own.level}"
        elif mem.turns == 1:
            if self.rng.random() < self.temper.run_travel:
                reason = f"travelling, and this wild {foe.species} is not one it wants ({self.personality})"
        if reason is None:
            return None
        mem.runs += 1
        return Decision("run", reason)

    # ------------------------------------------------------------------ switching
    def _switch(self, look: Observation, own: BattleMon, foe: BattleMon) -> Decision | None:
        mem = self.memory
        if mem.switches >= MAX_SWITCHES or foe.species in mem.switched_against:
            return None
        if look.battle is not None and look.battle.double:
            return None  # step 4 does not switch in a double battle (`_fight_double`)
        better = self.better_member(look, own, foe)
        if better is None:
            return None
        member, why = better
        mem.switches += 1
        mem.switched_against.add(foe.species)
        return Decision("switch", why, switch_pid=member.pid)

    def better_member(self, look: Observation, own: BattleMon, foe: BattleMon) -> tuple[MonSummary, str] | None:
        """A healthy party member MUCH better against `foe` than the Pokemon out, when the one out is badly matched (the
        foe hits it super-effectively, or its best move does half the worth of a neutral one)."""
        mine = matchup(own.types, own.moves, own.level, foe, self.faults)
        badly = mine[2] >= 2.0 or mine[1] < 0.5 * self._neutral_worth(own)
        # a Pokemon FAR above the foe's level is not in danger from a bad matchup (measured 2026-10-08 on Route 116: the
        # AI swapped its L16 Grovyle out against L6-7 Taillows for its L6-8 Normal types)
        if not badly or own.level >= foe.level + OUTLEVELS:
            return None
        best = None
        out = ({m.pid for m in (look.battle.own if look.battle is not None else ()) if m.pid is not None} | {own.pid}
               | set(self.refused))
        for member in look.party or ():
            if member.pid in out or member.hp <= 0 or member.is_egg or member.hp < 0.5 * member.max_hp:
                continue
            theirs = matchup(member.types, member.moves, member.level, foe, self.faults)
            if theirs[0] >= 2.0 * max(mine[0], 1.0) and (best is None or theirs[0] > best[1][0]):
                best = (member, theirs)
        if best is None:
            return None
        member, theirs = best
        return member, (f"{own.species} is badly matched against {foe.species} ({'/'.join(foe.types)}: threat x{mine[2]:g}, "
                        f"its best move worth {mine[1]:.0f}); {member.species} is much better (best move worth "
                        f"{theirs[1]:.0f}, threat x{theirs[2]:g}): switch")

    def _neutral_worth(self, own: BattleMon) -> float:
        best = 0.0
        for slot, move in enumerate(own.moves):
            value = move_value(slot, move, own.types, own.level, 1.0, (), self.faults)
            if value is not None and not value.status:
                best = max(best, value.value)
        return best

    # ------------------------------------------------------------------ healing
    def _heal(self, look: Observation, own: BattleMon, foe: BattleMon, hp_share: float) -> Decision | None:
        mem = self.memory
        if mem.heals >= MAX_HEALS or hp_share >= self.temper.heal_below or own.hp is None or own.hp <= 0:
            return None
        if foe.hp_bar / HP_BAR_PIXELS <= 0.2:
            return None  # the foe is about to fall: finish it
        items = [name for name, count in (look.bag.healing if look.bag is not None else ()) if count > 0
                 and name in ("Potion", "Super Potion", "Hyper Potion", "Max Potion", "Full Restore", "Fresh Water",
                              "Soda Pop", "Lemonade", "Moomoo Milk", "Oran Berry", "Sitrus Berry")]
        if not items:
            return None
        mem.heals += 1
        return Decision("item", f"an important battle (a trainer's) and its {own.species} is low ({hp_share:.0%}): "
                                f"heal with a {items[0]}", item=items[0], target_pid=own.pid)

    # ------------------------------------------------------------------ fainting, questions
    def replacement(self, look: Observation, forced: bool = True) -> tuple[int | None, str]:
        """Who goes in (by PID): the healthy member best matched against the foe(s) still standing (`matchup`, its mean
        over the foes of a double battle; with no foe standing, the level), scaled by its HP share; never a member ON THE
        FIELD (the battle view's own battlers: a double battle's partner still stands there), one sent in since the last
        turn began, or one the game refused (`on_field`, `sent`, `refuse`). The party menu's look has no battle view: the
        field is the one REMEMBERED from the last look at the battle, and the reason says so."""
        battle, remembered = self.on_field(look)
        foes = [f for f in (battle.foe if battle is not None else ()) if f.hp_bar > 0]
        standing = {m.pid: m.species for m in (battle.own if battle is not None else ()) if m.pid is not None}
        out = set(standing) | self.sent_since | set(self.refused)
        best = None
        for member in look.party or ():
            if member.hp <= 0 or member.is_egg or member.pid in out:
                continue
            if foes:
                score = sum(matchup(member.types, member.moves, member.level, f, self.faults)[0] for f in foes) / len(foes)
            else:
                score = float(member.level)
            score *= 0.5 + 0.5 * member.hp / max(1, member.max_hp)
            if best is None or score > best[1]:
                best = (member, score)
        if best is None:
            return None, "no Pokemon left that can fight"
        member, score = best
        against = f" against {' and '.join(f.species for f in foes)}" if foes else " (no foe standing: by level)"
        field = [f"{name} on the field" for pid, name in standing.items()
                 if any(m.pid == pid and m.hp > 0 for m in look.party or ())]
        field += [f"{pid:08x} sent in" for pid in sorted(self.sent_since)]
        field += [f"{pid:08x} refused ({words})" for pid, words in self.refused.items()]
        seen = (" (the field REMEMBERED from the last look at the battle: the party menu covers it)" if remembered
                else " (no battle view: the field unknown)" if battle is None else "")
        return member.pid, (f"{member.species} L{member.level} ({member.hp}/{member.max_hp} HP) is the best left{against}"
                            f"{'; not ' + ', '.join(field) if field else ''}{seen}")

    def answer(self, question: str, look: Observation, learn: LearnChoice | None = None) -> tuple[bool, str]:
        """The battle's yes/no, by its words (module docstring)."""
        words = question.casefold()
        if "use next" in words:
            pid, why = self.replacement(look)
            return (pid is not None), (f"yes: {why}" if pid is not None else f"no: {why}")
        if "change" in words and "pok" in words:
            battle = look.battle
            own = battle.own[0] if battle is not None and battle.own else None
            foe = battle.foe[0] if battle is not None and battle.foe else None
            if own is None or foe is None:
                return False, "no: it cannot see who is out"
            better = self.better_member(look, own, foe)
            if better is None:
                return False, f"no: {own.species} is not badly matched against {foe.species}"
            willing = self.rng.random() < self.temper.switch_willing
            return willing, (f"{'yes' if willing else 'no'}: {better[1]} ({self.personality}: switch_willing "
                             f"{self.temper.switch_willing})")
        if "nickname" in words:
            return False, "no: it keeps the species' name"
        if "make room" in words or "delete a move" in words:
            if learn is None:
                return False, "no: it does not know which move it would learn"
            return learn.learn, ("yes: " if learn.learn else "no: ") + learn.reason
        if "stop learning" in words:
            if learn is None:
                return True, "yes: it does not know which move it would learn"
            return (not learn.learn), ("no: " if learn.learn else "yes: ") + learn.reason
        return False, f"no: a question it does not know ({question!r}): it agrees to nothing it does not know"
