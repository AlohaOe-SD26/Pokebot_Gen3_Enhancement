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

STEP 4.1 (the step-4 verifier's and adversarial review's findings, fixed):
  * THE SHIFT QUESTION ("TRAINER X is about to use TREECKO. Will ... change POKéMON?") is asked BEFORE the next foe is
    sent out (`data/battle_scripts_1.s` BattleScript_FaintedMonTryChoose: `printstring STRINGID_ENEMYABOUTTOSWITCHPKMN`,
    `yesnobox`, then the send-out), so the battle view still holds the FAINTED foe. The decider now reads the INCOMING
    species from the question's words (`incoming`), builds the foe it judges from SPECIES facts (its types; its level,
    which the words do not show, guessed as the last foe's), and when it says YES it CARRIES the chosen member's PID into
    the party menu that follows (`shift_to`: `replacement` sends that one, not the best by level against a fainted foe).
  * A move the game REFUSES (Disabled, Taunt, Torment, no PP: `TrySetCantSelectMoveBattleScript` brings the move grid
    straight back) is UNUSABLE for the rest of the turn (`cannot_use`, cleared at the next action menu), and excluded from
    every value, so "decide again" can no longer pick it again until the 150-menu bound.
  * Hidden information is gone from the choices: the foe's TYPES come from its species (a person knows a species, not
    a Color Change: `seen_types`); a hit's damage is a person's ROUGH sense (`damage_fraction`: to the nearest eighth of
    the foe's HP, give or take an eighth), not the exact formula with an 8 % margin; the ball is chosen by what a person
    SEES (misses so far, how weakened and whether asleep or paralyzed the foe is, how rare it seems to them), not by the
    hidden catch rate.
  * OVERKILL is not valued: a move that would FINISH the foe (its rough damage at least what the bar has left) is worth
    as much as the strongest move, so moves that all finish it compare by their hit chance and recoil (Water Gun over a
    Take Down that also finishes a 15-HP Poochyena). FAULT `overkill`: the step-4 valuation.
  * Not a machine: by its temperament (`Temperament.opener`), a small chance of an OPENING stat or status move on its
    first turn against a foe, only when that is SAFE (its HP high, the foe not hitting it super-effectively, not
    stronger, not about to fall: `_safe_for_status`); and when it wants to catch, a sleep or paralysis move it has is
    used once the foe is weakened, before the throws.

STEP 4.1 ROUND 3 (the step-4.1 verifier's second round: "the foe's base stats still feed _formula_share, then rough_share,
then the KO and finisher checks and the recoil HP"): the damage estimate no longer reads THIS foe's base stats. A person
sees the foe's LEVEL and its HP BAR and knows how sturdy Pokemon are ON THE WHOLE, not a species' base stats: every foe is
first guessed as a TYPICAL Pokemon of its level (`TYPICAL_BASE`: each stat the MEDIAN base stat over all 386 species, the
same numbers for every foe), and that guess is then CORRECTED by what its own hits are SEEN to take off this foe's bar
(`BattleMind._seen_factor`: "Tackle took half of it, not the third I thought: a frail one"). The user's own attack is
its own SUMMARY's stat (what the player sees on its summary screen). No fault switch puts the species' base stats back
(that would leave the hidden read in the AI's code): `gates/revert_step4.py` B60 and B61 do it in a copy.

FAULT SWITCHES (`Faults`, test side only): `ignore_types` values every move as if every type matchup were neutral and
every Pokemon untyped (no STAB) (the TYPE arm's fault); `ignore_recoil` drops the recoil penalty (the RECOIL fault);
`uncapped_recoil` charges the recoil on the move's whole worth (the step-4 rule: no cap at the foe's HP, no Jump Kick
cap, no self-faint check); `forget_field` makes the replacement see only the look on screen (the step-4 bug);
`ignore_refusal` makes the skill watch the party menu's refusal ("... is already in battle!") instead of reading it;
(step 4.1) `overkill` values every move uncapped (the step-4 valuation: a stronger move wins even when a weaker one
finishes the foe); `shift_fainted` answers the shift question about the foe on the field (the fainted one) and sends
the best by level, as step 4 did; `forget_unusable` lets "decide again" pick the refused move again, as step 4 did;
(round 3) `forget_shift` judges the question about the incoming foe but does NOT carry the member chosen there into the
party menu (ranked again, by level: the live carry's A/B).
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field, replace

from ai_player.eyes.observation import BattleMon, BattleView, MonSummary, MoveSlot, Observation
from ai_player.eyes.view import HP_BAR_PIXELS
from ai_player.knowledge.facts import MoveFact, move_fact, species_fact, species_named, stab, type_multiplier

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
    "TYPICAL_BASE",
    "damage_fraction",
    "estimate_stat",
    "foe_max_hp",
    "general_value",
    "incoming",
    "learn_choice",
    "matchup",
    "move_key",
    "move_value",
    "needs_rest",
    "recoil_penalty",
    "recoil_risk",
    "rough_share",
    "seen_types",
    "typical_stat",
]

#: (step 4.1, the review's "hidden information") A person's ROUGH sense of a hit: the share of the foe's HP it takes, to the
#: nearest eighth, give or take an eighth (`damage_fraction`).
ROUGH_STEP = 0.125
#: Weakening for a catch: a move is safe when, at the ROUGH WORST (its rough share plus an eighth), the foe's bar keeps
#: more than this (step 4: the exact formula's best roll with an 8 % margin, which no person can see).
KO_MARGIN = 0.0
#: (step 4.1 round 3, the verifier: "the foe's base stats still feed the damage estimate") A TYPICAL Pokemon, the guess for
#: every foe before a hit on it is seen: each stat the MEDIAN base stat over all 386 species of the knowledge file
#: (`gates/test_battle.py` HiddenInfoTests checks these numbers against `knowledge/species.json`, so they cannot drift).
#: The same numbers for every foe: a person knows how sturdy Pokemon are on the whole, not a species' base stats.
TYPICAL_BASE = {"hp": 63, "attack": 70, "defense": 65, "sp_attack": 65, "sp_defense": 65}
#: (round 3) The correction a SEEN hit makes to that guess (what the bar dropped over what the guess said) is kept within
#: these bounds: one bar is coarse (48 pixels), a damage roll varies by 15 %, and a critical hit doubles a hit.
SEEN_FACTOR_RANGE = (0.4, 2.5)
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
#: (step 4.1) OPENING moves a person sometimes makes on a safe first turn: lowering the foe's stats, raising its own, or
#: putting a status on the foe (the knowledge's effect names, `moves.json`).
OPENER_EFFECTS = frozenset({"ATTACK_DOWN", "DEFENSE_DOWN", "SPEED_DOWN", "ACCURACY_DOWN", "ATTACK_DOWN_2", "DEFENSE_DOWN_2",
                            "SPEED_DOWN_2", "SPECIAL_DEFENSE_DOWN_2", "ATTACK_UP", "ATTACK_UP_2", "DEFENSE_UP",
                            "DEFENSE_UP_2", "SPECIAL_ATTACK_UP", "SPECIAL_ATTACK_UP_2", "SPEED_UP_2", "BULK_UP",
                            "CALM_MIND", "DRAGON_DANCE", "FOCUS_ENERGY", "SLEEP", "PARALYZE", "POISON", "TOXIC",
                            "CONFUSE", "LEECH_SEED"})
#: (step 4.1) Statuses that make a catch easier (`src/battle_script_commands.c` Cmd_handleballthrow: asleep or frozen x2,
#: paralyzed, poisoned or burned x1.5): the moves a person uses to help a catch are sleep and paralysis.
CATCH_STATUS_EFFECTS = ("SLEEP", "PARALYZE")
#: (step 4.1) Tries of a catch-helping status move against one foe (it can miss).
MAX_STATUS_TRIES = 2
#: (step 4.1) The SAFE conditions for a status move (`_safe_for_status`): its own HP share at least this for an opener
#: (`OPENER_HP`) or a catch's status move (`CATCH_STATUS_HP`), the foe's bar at least `OPENER_FOE_BAR` (not about to fall),
#: the foe at most `OPENER_LEVELS` above it.
OPENER_HP = 0.7
CATCH_STATUS_HP = 0.5
OPENER_FOE_BAR = 0.6
OPENER_LEVELS = 2
#: (step 4.1) The shift question's next foe: its level is not shown, so the guard against switching out a Pokemon that far
#: outlevels the foe asks for this much more margin than `OUTLEVELS` over the last foe's level.
UNSEEN_LEVEL_SLACK = 3
#: (step 4.1) The shift question's words: `src/battle_message.c` sText_EnemyAboutToSwitchPkmn "{B_TRAINER1_CLASS}
#: {B_TRAINER1_NAME} is\nabout to use {B_BUFF2}.\pWill {B_PLAYER_NAME} change\nPOKéMON?" (the eyes join lines with a space).
_ABOUT_TO_USE = re.compile(r"about to use (.+?)[.!?]", re.I)


@dataclass(frozen=True)
class Temperament:
    """How a personality battles (taste, not strategy; plausible values, not measured from people)."""

    near_best: float  # moves within this share of the best are about as good (a seeded, value-weighted draw among them)
    catch_new: float  # the chance it wants a species it has not caught (one draw per species per run)
    run_travel: float  # the chance it runs from a wild battle it does not want while travelling
    switch_willing: float  # the chance it says YES to "Will ... change POKéMON?" when the switch rule finds a better one
    heal_below: float  # its Pokemon's HP share under which it heals in an important battle
    run_low: float  # training: its Pokemon's HP share under which it runs from a wild battle
    #: (step 4.1) the chance of an OPENING stat or status move on a safe first turn against a foe (one draw per foe)
    opener: float = 0.0


TEMPERAMENTS: dict[str, Temperament] = {
    "Catcher": Temperament(near_best=0.80, catch_new=1.0, run_travel=0.6, switch_willing=0.5, heal_below=0.25, run_low=0.25,
                           opener=0.20),
    "Story": Temperament(near_best=0.85, catch_new=0.6, run_travel=0.8, switch_willing=0.3, heal_below=0.30, run_low=0.30,
                         opener=0.12),
    "Trainer": Temperament(near_best=0.90, catch_new=0.75, run_travel=0.2, switch_willing=0.8, heal_below=0.25, run_low=0.20,
                           opener=0.25),
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
    #: (step 4.1) every move valued uncapped, as step 4 did: a move that FINISHES the foe is worth no more than its power
    #: says, so a stronger, riskier move beats a weaker one that also finishes it (the OVERKILL fault)
    overkill: bool = False
    #: (step 4.1) the shift question answered about the foe on the field (the FAINTED one) and the party menu after a YES
    #: ranked by level, as step 4 did (the SHIFT fault)
    shift_fainted: bool = False
    #: (step 4.1) a move the game refused this turn is not remembered: "decide again" may choose it again (the DISABLE fault)
    forget_unusable: bool = False
    #: (step 4.1 round 2) no sleep or paralysis move to help a catch, as step 4 had none (the CATCHS fault)
    no_catch_status: bool = False
    #: (step 4.1 round 2) the decider blind to the PP its moves have left: it may choose a move with none, which the GAME
    #: refuses through the same code as a Disabled move (`src/battle_util.c` TrySetCantSelectMoveBattleScript: Disable,
    #: Torment, Taunt, Imprison, a Choice item, no PP) and gives the move grid back (the REFUSED arms: finding 2 live)
    ignore_pp: bool = False
    #: (step 4.1 round 3, the verifier: "the PID carried to the party menu cannot fail live") the shift question is still
    #: judged about the INCOMING foe, but the member chosen there is NOT carried into the party menu: it ranks again, by
    #: level (the foe it remembers has fainted) (the SHIFTCX arm and the sweep's SHIFT-CARRY-FAULT)
    forget_shift: bool = False
    # ---- (boss preparation round 2, USER RULING 59, 2026-11-11) the raise's rules in a battle, each switched off
    #: no switch-training: a trainee that cannot win safely runs (BP-1 neither switched nor had a partner)
    raise_never_switch: bool = False
    #: the trainee switched out even when it would win safely (no own fights)
    raise_always_switch: bool = False
    #: the old order of a wild battle's choice: the run rule BEFORE the raise's turn (a L3 trainee runs from a foe 6 levels
    #: up where the partner wins)
    run_first: bool = False
    #: the replacement after a faint may be the trainee while another member can fight
    replacement_trainee_ok: bool = False
    #: the raise's switch made again on a later turn (more than two members share)
    second_switch: bool = False
    #: "Use next POKéMON?" answered YES with only the trainee left to fight
    trainee_sent_last: bool = False
    #: (round 2, the live #118 loop, `skills/battle.py`) the move learner named from the last 40 pages, else the battler on
    #: the field (no page kept apart, no "taught at its level now")
    learner_by_battler: bool = False
    #: (the same) the forget screen's four moves not checked against the member the choice was made for
    forget_unchecked: bool = False


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
    #: (step 4.1) it would FINISH the foe (its rough damage at least what the bar has left): worth as the strongest move
    finishes: bool = False

    def line(self) -> str:
        if self.status:
            return f"{self.name}: a status move (0)"
        return (f"{self.name}: {self.value:.1f} = x{self.effectiveness:g} type x{self.stab:g} STAB x {self.power:g} power x "
                f"{self.hit_chance:.2f} hit{f' - {self.recoil:.1f} recoil' if self.recoil else ''}"
                f"{' (finishes it: worth as the strongest)' if self.finishes else ''}")


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
               risk: RecoilRisk = NO_ESTIMATE, ko_worth: float | None = None, power: float | None = None) -> MoveValue | None:
    """A move's worth against this foe (module docstring); None when it cannot be used (no PP left). `risk`: what its
    recoil would cost against this foe (`recoil_risk`; the default: no estimate, the recoil of the whole worth).
    `ko_worth` (step 4.1): the move would FINISH the foe, and this is the worth of the strongest move against it; a move
    that finishes the foe is worth that much (before its hit chance and recoil), whatever its power (FAULT `overkill`:
    ignored, as step 4). `power` (boss preparation BP-1, 2026-11-09): the power to weigh it by instead of the printed one
    (`_power`): a boss's Low Kick, Reversal or Arm Thrust at the power the readiness verdict gives it
    (`brain/bossprep.py` verdict_slot); None (every caller before BP-1) changes nothing."""
    if move.pp is not None and move.pp <= 0 and not faults.ignore_pp:
        return None
    fact = _fact(move)
    mtype = fact.type if fact is not None else move.type
    power = _power(fact, move, user_level) if power is None else float(power)
    if (fact is not None and fact.category == "status") or power <= 0:
        return MoveValue(slot, move.name, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, True)
    turns = 1.0
    if fact is not None and fact.two_turn:
        turns *= 0.5  # it takes two turns (or a turn's warning)
    if fact is not None and fact.recharge:
        turns *= 0.6  # the user rests the next turn
    power *= turns
    effectiveness = 1.0 if faults.ignore_types else type_multiplier(mtype, foe_types)
    if fact is not None and fact.fixed_damage and effectiveness > 0:
        effectiveness = 1.0  # fixed damage ignores the matchup (an immunity still holds)
    bonus = 1.0 if faults.ignore_types else stab(mtype, user_types)
    hit = fact.hit_chance if fact is not None else 1.0
    full = effectiveness * bonus * power
    finishes = ko_worth is not None and effectiveness > 0 and not faults.overkill
    if finishes:
        full = max(full, ko_worth * turns)  # (step 4.1) no worth beyond finishing it: every finisher is the strongest
    base = full * hit
    if faults.uncapped_recoil:
        risk = NO_ESTIMATE  # FAULT: the step-4 rule (the recoil of the whole worth)
    penalty = 0.0 if faults.ignore_recoil else recoil_penalty(fact, base, hp_share, full, risk)
    return MoveValue(slot, move.name, base - penalty, base, effectiveness, bonus, hit, power, penalty, False, finishes)


def full_worth(move: MoveSlot, user_types: tuple[str, ...], user_level: int, foe_types: tuple[str, ...],
               faults: BattleFaults = BattleFaults()) -> float:
    """(step 4.1) A damaging move's worth before its hit chance and recoil (type x STAB x power), 0 for a status move or
    one with no PP: the scale `ko_worth` is taken from (the strongest move against this foe)."""
    value = move_value(0, move, user_types, user_level, 1.0, foe_types, replace(faults, ignore_recoil=True))
    if value is None or value.status:
        return 0.0
    return value.base / value.hit_chance if value.hit_chance > 0 else value.base


def estimate_stat(base: int, level: int, hp: bool = False) -> int:
    """A stat of a Pokemon with this BASE stat at this level (average IVs, no EVs, a neutral nature: `src/pokemon.c`
    CalculateMonStats with IV 15, EV 0). Since step 4.1 round 3 the decider calls it only with `TYPICAL_BASE`."""
    if hp:
        return (2 * base + 15) * level // 100 + level + 10
    return (2 * base + 15) * level // 100 + 5


def typical_stat(stat: str, level: int) -> int:
    """(step 4.1 round 3) A stat of a TYPICAL Pokemon of `level` (`TYPICAL_BASE`): what a person expects of a Pokemon it
    knows only by its level."""
    return estimate_stat(TYPICAL_BASE[stat], level, hp=stat == "hp")


def foe_max_hp(foe: BattleMon) -> int:
    """(step 4.1 round 3) The foe's max HP as a person guesses it: a typical Pokemon of the foe's LEVEL (the bar shows only
    the share it has left; its species' base HP is not what a person knows)."""
    return typical_stat("hp", foe.level)


def seen_types(mon: BattleMon) -> tuple[str, ...]:
    """(step 4.1, "foe types from SPECIES facts, not live gBattleMons types") The types a person knows a battler has:
    its SPECIES' (the Pokedex's), not the battle's live types (a Color Change, a Camouflage or Castform's weather form
    changes those, and nothing on screen says so). The live types only when the species is unknown."""
    fact = species_fact(mon.species)
    return fact.types if fact is not None else mon.types


def _formula_share(move: MoveSlot, user: MonSummary | None, user_battler: BattleMon, foe: BattleMon,
                   faults: BattleFaults = BattleFaults(), seen: float = 1.0, power: float | None = None) -> float | None:
    """The middle of the game's damage formula's rolls as a share of the foe's max HP (`src/pokemon.c`
    CalculateBaseDamage: ((2L/5+2) x power x A / D) / 50 + 2, x STAB x type, x 85-100 %), with the user's own attack (the
    summary screen's) and the foe guessed as a TYPICAL Pokemon of its level (step 4.1 round 3: `typical_stat`, never the
    foe's species' base stats), times `seen` (`BattleMind._seen_factor`: what its hits were seen to take off this foe,
    over this guess); no critical hit. Only the ROUGH sense made from it (`rough_share`) is used in a choice. None for a
    status move. `power` (BP-1): as `move_value`'s."""
    fact = _fact(move)
    power = _power(fact, move, user_battler.level) if power is None else float(power)
    if power <= 0 or (fact is not None and fact.category == "status"):
        return None
    mtype = fact.type if fact is not None else move.type
    physical = (fact.category == "physical") if fact is not None else True
    if user is not None and len(user.stats) == 5:
        attack = user.stats[0] if physical else user.stats[3]
    else:
        # its own summary unread (not met in a battle so far): a typical Pokemon of its level too
        attack = typical_stat("attack" if physical else "sp_attack", user_battler.level)
    defense = typical_stat("defense" if physical else "sp_defense", foe.level)
    hp = foe_max_hp(foe)
    if fact is not None and fact.fixed_damage:
        flat = {"SONICBOOM": 20, "DRAGON_RAGE": 40, "LEVEL_DAMAGE": user_battler.level, "PSYWAVE": user_battler.level}
        if fact.effect in flat:
            return flat[fact.effect] / hp * seen
        return None
    effectiveness = 1.0 if faults.ignore_types else type_multiplier(mtype, seen_types(foe))
    bonus = 1.0 if faults.ignore_types else stab(mtype, seen_types(user_battler))
    damage = ((2 * user_battler.level // 5 + 2) * power * attack / max(1, defense)) / 50 + 2
    damage *= bonus * effectiveness
    return damage * 0.925 / hp * seen


def rough_share(move: MoveSlot, user: MonSummary | None, user_battler: BattleMon, foe: BattleMon,
                faults: BattleFaults = BattleFaults(), seen: float = 1.0, power: float | None = None) -> float | None:
    """(step 4.1) A person's ROUGH sense of what one hit of `move` takes off the foe, as a share of its HP: to the nearest
    eighth (at least a sixteenth: "a scratch"). `seen`: the correction its hits on this foe were seen to make (round 3).
    None for a status move. `power` (BP-1): as `move_value`'s."""
    share = _formula_share(move, user, user_battler, foe, faults, seen, power)
    if share is None:
        return None
    if share <= 0:
        return 0.0
    return max(ROUGH_STEP / 2, round(share / ROUGH_STEP) * ROUGH_STEP)


def damage_fraction(move: MoveSlot, user: MonSummary | None, user_battler: BattleMon, foe: BattleMon,
                    faults: BattleFaults = BattleFaults(), seen: float = 1.0) -> tuple[float, float] | None:
    """The share of the foe's max HP one hit of `move` takes as a person would put it, (at least, at most): its ROUGH
    share (`rough_share`) give or take an eighth (step 4.1: step 4 used the exact formula's lowest and highest rolls and an
    8 % margin, which no person sees). None for a status move."""
    rough = rough_share(move, user, user_battler, foe, faults, seen)
    if rough is None:
        return None
    if rough <= 0:
        return 0.0, 0.0
    return max(rough / 2, rough - ROUGH_STEP), rough + ROUGH_STEP


def recoil_risk(move: MoveSlot, user: MonSummary | None, user_battler: BattleMon, foe: BattleMon,
                faults: BattleFaults = BattleFaults(), seen: float = 1.0) -> RecoilRisk:
    """(the step-4 verifier's round) What a recoil move would cost its user against `foe` (`RecoilRisk`), from one hit's
    average damage roll as a share of the foe's max HP (`damage_fraction`) and the foe's bar: Take Down's recoil is a
    quarter of the HP the hit TAKES, at most what the bar has left; Jump Kick's miss recoil half the damage it would have
    dealt, at most half the foe's max HP; in HP (the foe's max HP guessed as a typical Pokemon of its level, `foe_max_hp`,
    as the damage is: round 3) against the user's HP left. `NO_ESTIMATE` for a move without recoil."""
    fact = _fact(move)
    if fact is None or fact.recoil_kind is None:
        return NO_ESTIMATE
    share = rough_share(move, user, user_battler, foe, faults, seen)  # (step 4.1) the ROUGH sense of the hit
    if share is None or share <= 0:
        return NO_ESTIMATE
    left = max(0.0, foe.hp_bar / HP_BAR_PIXELS)
    foe_max = foe_max_hp(foe)
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
    foe_types = seen_types(foe)  # (step 4.1) the foe's SPECIES types
    for slot, move in enumerate(moves):
        value = move_value(slot, move, types, level, 1.0, foe_types, faults)
        if value is not None and not value.status:
            best = max(best, value.value)
    threats = [type_multiplier(t, types) for t in foe_types]
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


def incoming(words: str, last_foe: BattleMon | None) -> tuple[BattleMon | None, str]:
    """(step 4.1) The foe a trainer is ABOUT TO SEND OUT, as the shift question's words name it ("YOUNGSTER CALVIN is
    about to use ZIGZAGOON."), built from SPECIES facts: its types, a full bar, no moves seen; its LEVEL is not in the
    words, so the last foe's level stands in for it (a person expects a trainer's Pokemon to be about alike). (None, why)
    when the words name no species the knowledge has."""
    # (step 4.1 review, finding 5) the LAST "about to use" in the words: an older page still in the window (a missed
    # page) must not name the Pokemon (it once picked WURMPLE over NINCADA)
    matches = list(_ABOUT_TO_USE.finditer(words or ""))
    found = matches[-1] if matches else None
    if found is None:
        return None, "the words name no Pokemon about to be used"
    # (step 4.1 round 2, the verifier's minor: "a species with a period ('MR. MIME') becomes 'MR' and the question is
    # answered NO") the name ends at a full stop the NAME does not contain: of every cut of the rest of the words at a '.',
    # '!' or '?', the longest that names a species the knowledge has ("MR. MIME. Will ..." -> "MR. MIME")
    rest = (words or "")[found.start(1):]
    printed, name = found.group(1).strip(), None
    for cut in sorted({m.start() for m in re.finditer(r"[.!?]", rest)}, reverse=True):
        named = species_named(rest[:cut].strip())
        if named is not None:
            printed, name = rest[:cut].strip(), named
            break
    fact = species_fact(name) if name is not None else None
    if fact is None:
        return None, f"{printed!r} is not a species it knows"
    level = last_foe.level if last_foe is not None else 1
    foe = BattleMon(fact.name, fact.dex, level, None, None, HP_BAR_PIXELS, "ok", fact.types, (), None, 1)
    return foe, (f"the words say {printed} comes next ({'/'.join(fact.types)}; its level unseen, about "
                 f"L{level} like the last)")


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
    #: (build step 5.1) it wants this species but has no ball to throw (said so, never "it WANTS it")
    no_ball: bool = False
    new_species: bool = False
    last_bar: int | None = None
    last_move: str | None = None
    #: the bar each of its moves took off this foe (a person learns "Tackle took a third of its HP")
    observed: dict = field(default_factory=dict)
    #: (step 4.1 round 3) the LAST hit it saw land on this foe: (its move, the share of the bar it took)
    seen_hit: tuple[str, float] | None = None
    #: (step 4.1) decisions against THIS foe, whether the opener was drawn for it, the catch-helping status moves tried
    foe_turns: int = 0
    opener_drawn: bool = False
    status_tries: int = 0
    #: (boss preparation round 2) how a RAISE battle is fought: "own", "switch", "rescue", "run", "not the trainee" (None
    #: until its first decision), and whether the raise's one switch is made
    raise_mode: str | None = None
    raise_switched: bool = False


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
        #: (boss preparation BP-1, 2026-11-09) the PID of the Pokemon being RAISED while the purpose is "raise" (the goal
        #: runner sets and clears it): its battles are its own, so no switch to a stronger member and no catch
        self.trainee: int | None = None
        #: (round 2, USER RULING 59) how each raise battle was fought, one entry a battle ("own", "switch", "rescue",
        #: "run", "not the trainee"): the raise runner reads and clears it; where its one line a battle is told (the runner
        #: sets it); the boss preparation's FAULT switches (`brain/bossprep.py` BossprepFaults, test side; None: none)
        self.raise_modes: list[str] = []
        self.say = None
        self.bp_faults = None
        self.memory = _Memory()
        #: (step 4.1 round 2) an OPENER the draw passed over on this decision (said with the move chosen instead)
        self.opener_passed = ""
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
        #: (step 4.1) the member it decided to SWITCH TO at the shift question (carried into the party menu that follows)
        self.shift_to: int | None = None
        self.shift_why: str = ""
        #: (step 4.1) moves the game REFUSED this turn ((battler position, move name) -> the words), and the last move chosen
        self.unusable: dict[tuple[int, str], str] = {}
        #: the PIDs on the player's side when those refusals were made (a switch forgets them)
        self.unusable_owners: tuple[int, ...] = ()
        self.last_chosen: tuple[int, str] | None = None
        #: (step 4.1) how often it has met each wild species this run, and wild battles in all (how rare a species SEEMS)
        self.met: dict[str, int] = {}
        self.wild_met = 0

    # ------------------------------------------------------------------ what it remembers of the field
    def enter(self) -> None:
        """A battle is on screen (the skill starts): nothing remembered of a field yet."""
        self.field, self.sent_since, self.refused = None, set(), {}
        self.shift_to, self.shift_why, self.unusable, self.last_chosen = None, "", {}, None
        self.unusable_owners = ()

    def see(self, look: Observation) -> None:
        """Every look the hands take during a battle (a watcher of `skills/battle.py`): a look AT the battle (a battle view)
        is the field as it stands now; at the action menu a new turn begins, and what was sent in or refused before it is
        on the field now (or no longer refused), a move refused last turn may be used again, and a switch decided at the
        shift question is done."""
        if look.battle is None:
            return
        self.field = look.battle
        ui = look.screen.ui if look.screen is not None else None
        if ui is not None and ui.kind == "battle_action":
            self.sent_since, self.refused = set(), {}
            self.shift_to, self.shift_why = None, ""
            # (step 4.1 review, finding 4) a refused move (Disabled, Taunt, Torment) is REMEMBERED while the same
            # Pokemon stays in, as a person would; a switch (a different PID on the field) forgets it.
            out = tuple(sorted(m.pid for m in look.battle.own if m.pid is not None))
            if self.unusable_owners and out != self.unusable_owners:
                self.unusable = {}
            self.unusable_owners = out  # () = not known yet: adopted, never read as a switch

    def chose(self, battler: int | None, name: str | None) -> None:
        """(step 4.1) The move the hands just chose in the move grid (the one the game may refuse)."""
        self.last_chosen = (battler or 0, name) if name else None

    def cannot_use(self, words: str) -> str | None:
        """(step 4.1) The move grid came back after a move was chosen: the game REFUSED it (`TrySetCantSelectMoveBattleScript`:
        Disabled, Taunt, Torment, no PP; the selection script prints why, then the grid again). That move is unusable for
        the rest of this turn (FAULT `forget_unusable`: not remembered, as step 4). Returns its name (None: none chosen)."""
        if self.last_chosen is None:
            return None
        if not self.faults.forget_unusable:
            self.unusable[self.last_chosen] = words
        return self.last_chosen[1]

    def _usable(self, battler: int | None, move: MoveSlot) -> bool:
        return (battler or 0, move.name) not in self.unusable

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
        if battle.kind == "wild":
            # (step 4.1) how rare a species SEEMS to it: how often it has met it among the wild battles of this run
            self.met[foe.species] = self.met.get(foe.species, 0) + 1
            self.wild_met += 1
        owned = set(look.progress.owned_dex) if look.progress is not None else set()
        self.memory.new_species = battle.kind == "wild" and foe.dex not in owned
        if self.memory.new_species:
            if foe.species not in self.wishes:
                self.wishes[foe.species] = self.rng.random() < self.temper.catch_new
            # (BP-1, M4) a person RAISING one Pokemon fights its battles: no catch while raising (the wish is drawn as
            # ever, so the stream does not shift, and kept for a later meeting)
            self.memory.want_catch = self.wishes[foe.species] and self.purpose != "raise"
        # (build step 5.1, the step-5 verifier: "it WANTS it" was said with no ball in the bag, and then "run: this wild
        # Zigzagoon is not one it wants") the words say what it can do: a wish with no ball is said as one
        balls = any(count > 0 and name != "Master Ball" for name, count in (look.bag.balls if look.bag is not None else ()))
        self.memory.no_ball = self.memory.want_catch and not balls
        wish = ("it WANTS it" if balls else "it would like it, but it has no POKé BALL") if self.memory.want_catch \
            else "it lets this one go"
        what = (f"a {battle.kind} battle against {foe.species} L{foe.level} ({'/'.join(seen_types(foe))})"
                + (f"; a species it has not caught: {wish} ({self.personality}: catch_new {self.temper.catch_new})"
                   if self.memory.new_species else ""))
        return what

    def next_foe(self, look: Observation) -> None:
        """The foe changed (a trainer sent out its next Pokemon): what it learned about the last foe is forgotten; the
        battle's counts (balls, switches, heals) stay."""
        battle = look.battle
        foe = battle.foe[0] if battle is not None and battle.foe else None
        mem = self.memory
        mem.foe_key = f"{foe.species}:{foe.level}" if foe is not None else ""
        mem.last_bar, mem.last_move, mem.observed, mem.weaken_turns = None, None, {}, 0
        mem.foe_turns, mem.opener_drawn, mem.status_tries, mem.seen_hit = 0, False, 0, None

    # ------------------------------------------------------------------ the action menu
    def decide(self, look: Observation, battler: int | None = None, redecide: bool = False) -> Decision:
        """The decision at the action menu of the player's battler at `battler` (its position; None: the first).
        `redecide` (step 4.1 review): the game REFUSED the move this turn's decision chose, so this is the SAME turn
        decided again: the turn counts (turns, the foe's turns, weakening turns) do not move a second time."""
        mem = self.memory
        counts = (mem.turns, mem.foe_turns, mem.weaken_turns)
        decision = self._decide(look, battler)
        if redecide:
            mem.turns, mem.foe_turns, mem.weaken_turns = counts
        return decision

    def _decide(self, look: Observation, battler: int | None = None) -> Decision:
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
        mem.foe_turns += 1
        self._observe(foe)
        hp_share = own.hp / own.max_hp if own.hp is not None and own.max_hp else 1.0
        if foe is None:
            return self._fight(own, None, look, "the foe is not in view: its strongest move")
        values = self._values(own, foe, hp_share, look)
        if battle.kind == "wild" and not self.faults.run_first:
            # (boss preparation round 2, spec section 2.3 point 4) the RAISE's turn FIRST in a wild battle: before it the
            # run rule ran a L3 trainee from a foe 6 levels up, where its partner wins (FAULT `run_first`: the old order)
            decision = self._raise_turn(look, own, foe, hp_share)
            if decision is not None:
                return decision
        if battle.kind == "wild" and mem.want_catch:
            decision = self._catch(look, own, foe, hp_share, values)
            if decision is not None:
                return decision
        if battle.kind == "wild":
            decision = self._run_or_not(own, foe, hp_share)
            if decision is not None:
                return decision
        if battle.kind == "wild" and self.faults.run_first:
            decision = self._raise_turn(look, own, foe, hp_share)
            if decision is not None:
                return decision
        decision = self._switch(look, own, foe)
        if decision is not None:
            return decision
        if battle.kind == "trainer":
            decision = self._heal(look, own, foe, hp_share)
            if decision is not None:
                return decision
        decision = self._opener(own, foe, hp_share, values, battle.double)
        if decision is not None:
            return decision
        decision = self._fight(own, foe, look, "", values)
        if self.opener_passed:
            # (step 4.1 round 2, the verifier: the STATUS count could not tell a rare draw from a missing rule) an opener the
            # draw passed over is SAID with the move chosen instead, so the sweep can count every chance the rule had
            decision = replace(decision, reason=f"{decision.reason} [{self.opener_passed}]")
            self.opener_passed = ""
        return decision

    # ------------------------------------------------------------------ (step 4.1) status moves, when SAFE
    def _safe_for_status(self, own: BattleMon, foe: BattleMon, hp_share: float, least_hp: float,
                         opener: bool = True) -> str | None:
        """Why a turn spent on a status move is NOT safe now (None: it is): its own HP under `least_hp`, the foe hitting
        it super-effectively (its species' types or a move it was seen to use), the foe more than `OPENER_LEVELS` above
        it, or (an `opener`) the foe about to fall (its bar under `OPENER_FOE_BAR`: finish it instead). A person does not
        spend a turn on Growl when the foe could knock it out."""
        if hp_share < least_hp:
            return f"its HP is {hp_share:.0%} (under {least_hp:.0%})"
        types = seen_types(own)
        threats = [type_multiplier(t, types) for t in seen_types(foe)]
        threats += [type_multiplier(m.type, types) for m in foe.moves if m.power > 0]
        if not self.faults.ignore_types and max(threats or [1.0]) >= 2.0:
            return f"{foe.species} hits it super-effectively (x{max(threats):g})"
        if foe.level > own.level + OPENER_LEVELS:
            return f"{foe.species} L{foe.level} is stronger than its {own.species} L{own.level}"
        if opener and foe.hp_bar / HP_BAR_PIXELS < OPENER_FOE_BAR:
            return f"the foe's bar is at {foe.hp_bar / HP_BAR_PIXELS:.0%}: finish it"
        return None

    def _status_moves(self, own: BattleMon, foe: BattleMon, effects) -> list[tuple[int, MoveSlot, MoveFact]]:
        """The status moves of `own` with PP left, not refused this turn, whose effect is one of `effects` and that can
        take hold on this foe (a status on a foe that has none; Thunder Wave never on a Ground type, poison never on a
        Poison or Steel type: `src/battle_script_commands.c` Cmd_seteffectwithchance / the type checks of the effects)."""
        out = []
        for slot, move in enumerate(own.moves):
            fact = move_fact(move.name)
            if fact is None or fact.category != "status" or fact.effect not in effects:
                continue
            if (move.pp is not None and move.pp <= 0) or not self._usable(own.battler, move):
                continue
            types = seen_types(foe)
            if fact.effect in ("SLEEP", "PARALYZE", "POISON", "TOXIC", "CONFUSE") and foe.status not in ("ok", ""):
                if fact.effect != "CONFUSE":
                    continue
            if fact.effect == "PARALYZE" and fact.type == "Electric" and "Ground" in types:
                continue
            if fact.effect in ("POISON", "TOXIC") and ("Poison" in types or "Steel" in types):
                continue
            if fact.effect == "LEECH_SEED" and "Grass" in types:
                continue
            out.append((slot, move, fact))
        return out

    def _opener(self, own: BattleMon, foe: BattleMon, hp_share: float, values: list[MoveValue],
                double: bool = False) -> Decision | None:
        """(step 4.1, the review's "robotic battling: never a status move") On its FIRST turn against a foe, by its
        temperament's small chance (`Temperament.opener`, one seeded draw per foe), an OPENING stat or status move
        (`OPENER_EFFECTS`: Growl, Leer, String Shot, Harden, Stun Spore, ...), only when it is SAFE (`_safe_for_status`).
        Not in a double battle."""
        mem = self.memory
        if mem.foe_turns != 1 or mem.opener_drawn or self.temper.opener <= 0 or double:
            return None
        candidates = self._status_moves(own, foe, OPENER_EFFECTS)
        if not candidates or not any(not v.status and v.value > 0 for v in values):
            return None
        unsafe = self._safe_for_status(own, foe, hp_share, OPENER_HP)
        if unsafe is not None:
            return None
        mem.opener_drawn = True
        if self.rng.random() >= self.temper.opener:
            self.opener_passed = (f"no opener this time: {', '.join(m.name for _, m, _ in candidates)} possible and safe, the "
                                  f"draw over its chance ({self.personality}: opener {self.temper.opener})")
            return None
        weights = [float(STATUS_WORTH.get(fact.effect, STATUS_DEFAULT)) + 1.0 for _, _, fact in candidates]
        slot, move, fact = self.rng.choices(candidates, weights=weights, k=1)[0]
        mem.last_move = move.name
        return Decision("fight", f"an OPENING move: {move.name} ({fact.effect.lower().replace('_', ' ')}) on its first turn "
                                 f"against {foe.species}, while it is safe (its HP {hp_share:.0%}, the foe's bar "
                                 f"{foe.hp_bar / HP_BAR_PIXELS:.0%}, no x2 threat, not stronger; {self.personality}: "
                                 f"opener {self.temper.opener})", move_slot=slot, move_name=move.name,
                        values=tuple(v.line() for v in values))

    def _observe(self, foe: BattleMon | None) -> None:
        """What its last move took off the foe's bar (calibrates the damage guess of the next weakening move)."""
        mem = self.memory
        if foe is None:
            return
        if mem.last_bar is not None and mem.last_move is not None and foe.hp_bar <= mem.last_bar:
            mem.observed[mem.last_move] = (mem.last_bar - foe.hp_bar) / HP_BAR_PIXELS
            if foe.hp_bar < mem.last_bar:
                mem.seen_hit = (mem.last_move, mem.observed[mem.last_move])
        mem.last_bar = foe.hp_bar
        mem.last_move = None

    def _seen_factor(self, own: BattleMon, foe: BattleMon, user: MonSummary | None) -> float:
        """(step 4.1 round 3) How much harder (or softer) its hits land on THIS foe than on a typical Pokemon of its level:
        the last hit it SAW land (the bar's drop after its move, `_observe`) over what it guessed that move would take
        (`_formula_share` of the typical guess), kept within `SEEN_FACTOR_RANGE`; 1 until it has seen one. A person who
        does not know a species' stats learns them this way ("Tackle took half: a frail one")."""
        hit = self.memory.seen_hit
        if hit is None:
            return 1.0
        move = next((m for m in own.moves if m.name == hit[0]), None)
        guess = _formula_share(move, user, own, foe, self.faults) if move is not None else None
        if not guess or hit[1] <= 0:
            return 1.0
        low, high = SEEN_FACTOR_RANGE
        return min(high, max(low, hit[1] / guess))

    def _values(self, own: BattleMon, foe: BattleMon, hp_share: float, look: Observation | None) -> list[MoveValue]:
        """Every move's worth against `foe` (`move_value`), with the types a person knows (`seen_types`), the recoil it
        would really cost (`recoil_risk`), a move that would finish the foe worth as the strongest (`_ko_worth`), and
        (step 4.1) without the moves the game refused this turn (`cannot_use`). (Round 3) The damage behind the recoil and
        the finishers is the typical guess corrected by the hits seen on this foe (`_seen_factor`)."""
        user = next((m for m in (look.party if look is not None else None) or () if m.pid == own.pid), None)
        own_types, foe_types = seen_types(own), seen_types(foe)
        usable = [(slot, move) for slot, move in enumerate(own.moves) if self._usable(own.battler, move)]
        seen = self._seen_factor(own, foe, user)
        ko = self._ko_worth(own, foe, user, usable, own_types, foe_types, self.faults, seen)
        out = []
        for slot, move in usable:
            risk = recoil_risk(move, user, own, foe, self.faults, seen)
            value = move_value(slot, move, own_types, own.level, hp_share, foe_types, self.faults, risk, ko.get(slot))
            if value is not None:
                out.append(value)
        return out

    @staticmethod
    def _ko_worth(own: BattleMon, foe: BattleMon, user: MonSummary | None, moves: list[tuple[int, MoveSlot]],
                  own_types: tuple[str, ...], foe_types: tuple[str, ...], faults: BattleFaults,
                  seen: float = 1.0) -> dict[int, float]:
        """(step 4.1, "overkill is valued") slot -> the worth of the STRONGEST move against `foe` (type x STAB x power), for
        every move that would FINISH it: its rough damage (`rough_share`, corrected by the hits seen: `seen`) at least what
        the foe's bar has left. Such a move is worth as much as the strongest, so moves that all finish the foe compare by
        their hit chance and recoil."""
        left = foe.hp_bar / HP_BAR_PIXELS
        fulls = {slot: full_worth(move, own_types, own.level, foe_types, faults) for slot, move in moves}
        top = max(fulls.values(), default=0.0)
        if top <= 0 or left <= 0:
            return {}
        out = {}
        for slot, move in moves:
            if fulls[slot] <= 0:
                continue
            # (step 4.1 review, finding 3) FINISHES only on its LOW estimate: the rough share is rounded to an eighth, and
            # rounding up called a Tackle that does 0.19 a finisher against a 25 % bar (drawn 167 of 400 times)
            fraction = damage_fraction(move, user, own, foe, faults, seen)
            if fraction is not None and fraction[0] >= left:
                out[slot] = top
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
                values = [move_value(s, m, seen_types(own), own.level, hp_share, (), self.faults)
                          for s, m in enumerate(own.moves) if self._usable(own.battler, m)]
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
        own_types = seen_types(own)
        usable = [(slot, move) for slot, move in enumerate(own.moves) if self._usable(own.battler, move)]
        kos = {foe.battler: self._ko_worth(own, foe, user, usable, own_types, seen_types(foe), faults) for foe in foes}
        for slot, move in usable:
            fact = move_fact(move.name)
            spread = fact is not None and fact.target in ("BOTH", "FOES_AND_ALLY")
            per_foe = []
            for foe in foes:
                value = move_value(slot, move, own_types, own.level, hp_share, seen_types(foe), faults,
                                   recoil_risk(move, user, own, foe, faults), kos[foe.battler].get(slot))
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
        status = self._catch_status(own, foe, hp_share, values)
        if status is not None:
            return status
        ball, cue = self._ball(balls, foe)
        mem.throws += 1
        return Decision("ball", f"{reason}: throw a {ball} ({cue}; ball {mem.throws}, {sum(c for _, c in balls)} in the bag)",
                        ball=ball)

    def _catch_status(self, own: BattleMon, foe: BattleMon, hp_share: float, values: list[MoveValue]) -> Decision | None:
        """(step 4.1, "use sleep/paralysis to help a catch when available") Before the throws, a SLEEP or PARALYSIS move it
        has (`CATCH_STATUS_EFFECTS`: Sleep Powder, Hypnosis, Stun Spore, Thunder Wave, ...), on a foe that has no status
        and that the move can take hold on, at most `MAX_STATUS_TRIES` times (it can miss), and only while that turn is
        safe for it (`_safe_for_status`: not when the foe is about to knock it out)."""
        mem = self.memory
        if mem.status_tries >= MAX_STATUS_TRIES or foe.status not in ("ok", "") or self.faults.no_catch_status:
            return None
        candidates = self._status_moves(own, foe, CATCH_STATUS_EFFECTS)
        if not candidates:
            return None
        unsafe = self._safe_for_status(own, foe, hp_share, CATCH_STATUS_HP, opener=False)
        if unsafe is not None:
            self.log.append(f"no status move to help the catch: {unsafe}")
            return None
        # sleep helps a catch most (x2 against x1.5), then the surer move
        slot, move, fact = max(candidates, key=lambda c: (c[2].effect == "SLEEP", c[2].hit_chance, -c[0]))
        mem.status_tries += 1
        mem.last_move = move.name
        return Decision("fight", f"to CATCH {foe.species}: {move.name} first ({fact.effect.lower()} makes a ball hold "
                                 f"better; try {mem.status_tries} of {MAX_STATUS_TRIES})", move_slot=slot, move_name=move.name,
                        values=tuple(v.line() for v in values))

    def _weakening_move(self, look: Observation, own: BattleMon, foe: BattleMon, bar: float,
                        values: list[MoveValue]) -> tuple[MoveValue | None, str]:
        """The move that takes the most off the foe's bar while, at its best roll, leaving at least `KO_MARGIN`: so a
        weaker move when the bar is already low. None when every move could knock it out."""
        user = next((m for m in look.party or () if m.pid == own.pid), None)
        seen_factor = self._seen_factor(own, foe, user)  # (round 3) the typical guess corrected by the hits seen
        safe = []
        for value in values:
            if value.status or value.value <= 0:
                continue
            move = own.moves[value.slot]
            guess = damage_fraction(move, user, own, foe, self.faults, seen_factor)
            if guess is None:
                continue
            low, high = guess
            seen = self.memory.observed.get(move.name)
            if seen is not None and seen > 0:
                high = max(high, seen + ROUGH_STEP)  # it saw what this move does to this foe (give or take an eighth)
                low = min(low, seen)
            if bar - high > KO_MARGIN:
                safe.append((low + high, value, low, high))
        if not safe:
            return None, f"every move could knock it out (its bar {bar:.0%})"
        safe.sort(key=lambda s: (-s[0], s[1].slot))
        _, value, low, high = safe[0]
        return value, (f"{value.name} takes about {low:.0%}-{high:.0%} of its HP (a rough guess) and its bar is at {bar:.0%}: "
                       f"it cannot knock it out")

    def _ball(self, balls: list[tuple[str, int]], foe: BattleMon) -> tuple[str, str]:
        """(step 4.1, "the ball choice uses catch_rate (hidden)") The ball by what a person SEES: a better ball (Ultra, Great)
        after two misses, while the foe is still strong (its bar above half and no sleep or paralysis), or when the species
        SEEMS RARE to it (met for the first time after several wild battles of this run); otherwise a Poke Ball. Returns
        (the ball, the cue)."""
        names = [name for name, _ in balls]
        mem = self.memory
        bar = foe.hp_bar / HP_BAR_PIXELS
        cues = []
        if mem.throws >= 2:
            cues.append(f"{mem.throws} missed")
        if bar > 0.5 and foe.status not in ("sleep", "paralysis", "freeze"):
            cues.append(f"still strong (its bar {bar:.0%})")
        if self.met.get(foe.species, 0) <= 1 and self.wild_met >= 4:
            cues.append(f"a {foe.species} seems rare (the first in {self.wild_met} wild battles)")
        if cues:
            for better in GREAT_BALLS:
                if better in names:
                    return better, "a harder catch: " + ", ".join(cues)
        for plain in ("Poké Ball", "Premier Ball"):
            if plain in names:
                return plain, ("an easy catch" if not cues else "no better ball: " + ", ".join(cues))
        return names[0], "the only ball it has"

    # ------------------------------------------------------------------ running
    def _run_or_not(self, own: BattleMon, foe: BattleMon, hp_share: float) -> Decision | None:
        mem = self.memory
        if mem.runs >= MAX_RUN_TRIES:
            return None
        bar = foe.hp_bar / HP_BAR_PIXELS
        reason = None
        if self.purpose in ("train", "raise"):  # (BP-1) raising runs exactly as training does
            if hp_share < self.temper.run_low and bar > 0.3:
                reason = f"its {own.species} is low ({hp_share:.0%}) and the foe is not ({bar:.0%}): not worth the risk"
            elif foe.level - own.level >= 6:
                reason = f"{foe.species} L{foe.level} is far stronger than its {own.species} L{own.level}"
        elif hp_share < self.temper.run_low and bar > 0.3:
            # (build step 5.1: measured 2026-10-14, the step-5.1 development sweep, three whiteouts in nine seeds, each a
            # Trainer travelling at 1-5 HP of 22 who fought a wild Wurmple, since a travel's run was a temperament's draw on
            # the first turn only) travelling with its Pokemon LOW, a person runs, whatever its temperament, on any turn
            reason = f"travelling with its {own.species} low ({hp_share:.0%}) and the foe not ({bar:.0%}): not worth the risk"
        elif mem.turns == 1:
            if self.rng.random() < self.temper.run_travel:
                reason = (f"travelling, and it has no POKé BALL for this wild {foe.species} ({self.personality})"
                          if mem.no_ball else
                          f"travelling, and this wild {foe.species} is not one it wants ({self.personality})")
        if reason is None:
            return None
        mem.runs += 1
        return Decision("run", reason)

    # ------------------------------------------------------------------ switching
    def _switch(self, look: Observation, own: BattleMon, foe: BattleMon) -> Decision | None:
        mem = self.memory
        if self.purpose == "raise":
            return None  # (BP-1, M4) a switch to a stronger member would split the experience the trainee is there for
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

    def better_member(self, look: Observation, own: BattleMon, foe: BattleMon,
                      level_seen: bool = True) -> tuple[MonSummary, str] | None:
        """A healthy party member MUCH better against `foe` than the Pokemon out, when the one out is badly matched (the
        foe hits it super-effectively, or its best move does half the worth of a neutral one). `level_seen` False (step
        4.1: the shift question's next foe, whose level the words do not show): the far-outlevels guard asks for
        `UNSEEN_LEVEL_SLACK` more levels."""
        mine = matchup(seen_types(own), own.moves, own.level, foe, self.faults)
        badly = mine[2] >= 2.0 or mine[1] < 0.5 * self._neutral_worth(own)
        # a Pokemon FAR above the foe's level is not in danger from a bad matchup (measured 2026-10-08 on Route 116: the
        # AI swapped its L16 Grovyle out against L6-7 Taillows for its L6-8 Normal types)
        margin = OUTLEVELS + (0 if level_seen else UNSEEN_LEVEL_SLACK)
        if not badly or own.level >= foe.level + margin:
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
        return member, (f"{own.species} is badly matched against {foe.species} ({'/'.join(seen_types(foe))}: threat "
                        f"x{mine[2]:g}, its best move worth {mine[1]:.0f}); {member.species} is much better (best move worth "
                        f"{theirs[1]:.0f}, threat x{theirs[2]:g}): switch")

    # ------------------------------------------------------------------ (boss preparation round 2) the raise's turn
    def _raise_turn(self, look: Observation, own: BattleMon, foe: BattleMon, hp_share: float) -> Decision | None:
        """(USER RULING 59, spec section 2.3) A RAISE battle as a person raising a weak Pokemon fights it: on its first
        decision the trainee (leading) fights ITSELF when it would win and still stand well (`bossprep.fight_safe`: mode
        "own"); otherwise it is switched out at once for the strong member that knocks the foe out (`raise_partner`: mode
        "switch"), and keeps its share (`src/battle_script_commands.c` Cmd_getexp: every member SENT OUT and standing when
        the foe faints shares; switches go before moves, so it is not hit); with no partner it runs ("run"). On a later
        turn of an own fight a trainee under `TRAINEE_FLOOR` is RESCUED by the one switch ("rescue"); after the switch,
        never again (exactly two members share). Only in a single wild battle with the purpose "raise" and a trainee set;
        None otherwise (the ordinary rules decide). FAULTS `raise_never_switch`, `raise_always_switch`, `second_switch`."""
        mem = self.memory
        battle = look.battle
        if (self.purpose != "raise" or self.trainee is None or battle is None or battle.kind != "wild" or battle.double
                or (mem.raise_switched and not self.faults.second_switch)):
            return None
        from ai_player.brain.bossprep import NO_FAULTS, TRAINEE_FLOOR, fight_safe, member_now  # here: bossprep imports us

        faults = self.bp_faults if self.bp_faults is not None else NO_FAULTS
        bar = foe.hp_bar / HP_BAR_PIXELS
        if mem.raise_mode is None:
            if own.pid != self.trainee:
                mem.raise_mode = "not the trainee"
                self.raise_modes.append(mem.raise_mode)
                self._raise_say(f"{own.species} L{own.level} leads, not the trainee {self.trainee:08x}: the ordinary rules")
                return None
            trainee = member_now(look, self.trainee)
            if trainee is None:
                return None
            safe, why = fight_safe(trainee, foe.species, foe.level, bar, trainee.hp,
                                   tuple(m.name for m in foe.moves if m.name), faults)
            head = (f"{trainee.species} L{trainee.level} ({trainee.hp}/{trainee.max_hp}) vs {foe.species} L{foe.level}")
            if safe and not self.faults.raise_always_switch:
                mem.raise_mode = "own"
                self.raise_modes.append(mem.raise_mode)
                self._raise_say(f"{head}: own: it wins this itself ({why})")
                return None
            partner = None if self.faults.raise_never_switch else self.raise_partner(look, foe)
            if partner is None:
                mem.raise_mode = "run"
                self.raise_modes.append(mem.raise_mode)
                mem.runs += 1
                said = ("FAULT raise_never_switch: no switch" if self.faults.raise_never_switch
                        else "no member is healthy and wins it safely")
                self._raise_say(f"{head}: run: it cannot win safely ({why}) and {said}")
                return Decision("run", f"raising {trainee.species}: it cannot win safely ({why}) and {said}: run")
            member, partner_why = partner
            mem.raise_mode = "switch"
            mem.raise_switched = True
            self.raise_modes.append(mem.raise_mode)
            self._raise_say(f"{head}: switch to {member.species} L{member.level}: {why}; {partner_why}")
            return Decision("switch", f"{trainee.species} L{trainee.level} cannot win safely ({why}): {member.species} "
                                      f"knocks it out; {trainee.species} keeps its share (Cmd_getexp: every member sent out "
                                      f"and standing shares)", switch_pid=member.pid)
        if mem.raise_mode == "run":
            # (a run the game refused: "Can't escape!") still nobody to knock it out: run again, within MAX_RUN_TRIES
            if mem.runs >= MAX_RUN_TRIES:
                return None
            mem.runs += 1
            return Decision("run", "raising: still no member to knock it out: run again")
        if mem.raise_mode == "own":
            # THE RESCUE: an own fight that went badly, the trainee under the floor: the one switch (it keeps its share; a
            # run would earn nothing)
            if own.pid != self.trainee or hp_share >= TRAINEE_FLOOR:
                return None
            partner = self.raise_partner(look, foe)
            if partner is None:
                return None
            member, partner_why = partner
            mem.raise_mode = "rescue"
            mem.raise_switched = True
            if self.raise_modes:
                self.raise_modes[-1] = "rescue"
            self._raise_say(f"rescue: the trainee at {hp_share:.0%}: switch to {member.species} L{member.level} "
                            f"({partner_why})")
            return Decision("switch", f"the trainee is low ({hp_share:.0%}): {member.species} finishes it; the trainee "
                                      f"keeps its share and a run would earn nothing", switch_pid=member.pid)
        if self.faults.second_switch and mem.raise_mode in ("switch", "rescue"):
            # FAULT `second_switch`: the raise's switch made again, to another member that wins it (three would share)
            partner = self.raise_partner(look, foe, exclude={own.pid})
            if partner is None:
                return None
            return Decision("switch", f"FAULT second_switch: again, to {partner[0].species}", switch_pid=partner[0].pid)
        return None

    def raise_partner(self, look: Observation, foe: BattleMon,
                      exclude: set | None = None) -> tuple[MonSummary, str] | None:
        """(round 2, spec section 2.3 point 3) The STRONG member that knocks the foe out for the trainee: a party member
        other than the trainee, no egg, at HALF its HP or more (`better_member`'s health rule), not refused by the game,
        that wins the battle safely itself (`bossprep.fight_safe` at its HP now against the foe's bar); the best by
        `matchup`'s score (the one `replacement` uses), then the higher level, then the lower slot. None when none is."""
        from ai_player.brain.bossprep import NO_FAULTS, fight_safe, member_now  # here: bossprep imports us

        faults = self.bp_faults if self.bp_faults is not None else NO_FAULTS
        bar = foe.hp_bar / HP_BAR_PIXELS
        skip = {self.trainee} | set(self.refused) | set(exclude or ())
        best = None
        for slot, mon in enumerate(look.party or ()):
            if mon.pid in skip or mon.is_egg or mon.hp <= 0 or mon.hp < 0.5 * mon.max_hp:
                continue
            member = member_now(look, mon.pid)
            if member is None:
                continue
            safe, why = fight_safe(member, foe.species, foe.level, bar, mon.hp, tuple(m.name for m in foe.moves if m.name),
                                   faults)
            if not safe:
                continue
            score = matchup(mon.types, mon.moves, mon.level, foe, self.faults)[0]
            key = (score, mon.level, -slot)
            if best is None or key > best[0]:
                best = (key, mon, why)
        if best is None:
            return None
        return best[1], f"{best[1].species} L{best[1].level} ({best[1].hp}/{best[1].max_hp}) wins it: {best[2]}"

    def _raise_say(self, line: str) -> None:
        """(round 2, spec section 2.3 point 8) One line a raise battle, told where the raise runner says (`say`)."""
        if self.say is not None:
            self.say(f"[AI-BOSSPREP] raise battle: {line}")

    def _neutral_worth(self, own: BattleMon) -> float:
        best = 0.0
        for slot, move in enumerate(own.moves):
            value = move_value(slot, move, seen_types(own), own.level, 1.0, (), self.faults)
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
        chosen = self.shift_to
        if (chosen is not None and chosen not in out and not self.faults.shift_fainted
                and not self.faults.forget_shift):
            member = next((m for m in look.party or () if m.pid == chosen and m.hp > 0 and not m.is_egg), None)
            if member is not None:
                # (step 4.1) the switch it DECIDED at the shift question, against the foe the words named: carried here
                # (step 4 ranked again, by level: the foe it remembered had fainted)
                return member.pid, (f"{member.species} L{member.level} ({member.hp}/{member.max_hp} HP), the switch it decided "
                                    f"at the question ({self.shift_why})")
        best = None
        # (boss preparation round 2, spec section 2.3 point 5) RAISING: the trainee is never sent in while another member
        # that can fight is left (it shares by having been sent out; sending it against what beat the strong one is not
        # raising it). FAULT `replacement_trainee_ok`: as before
        able = [m for m in look.party or () if m.hp > 0 and not m.is_egg and m.pid not in out]
        if (self.purpose == "raise" and self.trainee is not None and not self.faults.replacement_trainee_ok
                and any(m.pid != self.trainee for m in able)):
            out = out | {self.trainee}
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

    def _only_the_trainee(self, look: Observation) -> bool:
        """(round 2) The trainee is the only member left that can fight (HP, no egg, not on the field, not refused)."""
        battle, _ = self.on_field(look)
        standing = {m.pid for m in (battle.own if battle is not None else ()) if m.pid is not None}
        out = standing | self.sent_since | set(self.refused)
        able = [m for m in look.party or () if m.hp > 0 and not m.is_egg and m.pid not in out]
        return bool(able) and all(m.pid == self.trainee for m in able)

    def _shift(self, question: str, look: Observation, context: str) -> tuple[bool, str]:
        """(step 4.1, finding 1) "TRAINER X is about to use TREECKO. Will ... change POKéMON?": the game asks BEFORE the
        next foe is sent out (`BattleScript_FaintedMonTryChoose`), so the battle view still shows the FAINTED foe. The
        foe judged is the one the WORDS name (`incoming`: species facts, the level guessed); a YES carries the chosen
        member's PID into the party menu that follows (`shift_to`, `replacement`). FAULT `shift_fainted`: step 4's
        answer, about the foe on the field."""
        battle = look.battle if look.battle is not None else self.field
        own = battle.own[0] if battle is not None and battle.own else None
        on_field = battle.foe[0] if battle is not None and battle.foe else None
        if own is None:
            return False, "no: it cannot see who is out"
        if self.faults.shift_fainted:
            foe, said, seen_level = on_field, "FAULT shift_fainted: the foe on the field", True
        else:
            foe, said = incoming(f"{context} {question}", on_field)
            seen_level = False
        if foe is None:
            return False, f"no: it cannot tell who comes next ({said})"
        better = self.better_member(look, own, foe, level_seen=seen_level)
        if better is None:
            return False, f"no: {own.species} is not badly matched against {foe.species} ({said})"
        willing = self.rng.random() < self.temper.switch_willing
        if willing and not self.faults.shift_fainted:
            # (FAULT `forget_shift`, round 3: decided here and then not carried; `replacement` ranks again, by level)
            self.shift_to, self.shift_why = better[0].pid, f"against {foe.species}, {said}"
        return willing, (f"{'yes' if willing else 'no'}: {better[1]} ({said}; {self.personality}: switch_willing "
                         f"{self.temper.switch_willing})")

    def answer(self, question: str, look: Observation, learn: LearnChoice | None = None,
               context: str = "") -> tuple[bool, str]:
        """The battle's yes/no, by its words (module docstring). `context`: the pages of text before the question (step
        4.1: the shift question names the next foe on the page before "Will ... change POKéMON?")."""
        words = question.casefold()
        if "use next" in words:
            if (self.purpose == "raise" and self.trainee is not None and not self.faults.trainee_sent_last
                    and self._only_the_trainee(look)):
                # (boss preparation round 2, spec section 2.3 point 6) a person raising a weak Pokemon RUNS rather than
                # send it against what beat its strong one; the game's own "Can't escape!" then forces the choice
                return False, ("no: only the trainee is left to fight, and it is not sent against what beat the others: "
                               "it runs")
            pid, why = self.replacement(look)
            return (pid is not None), (f"yes: {why}" if pid is not None else f"no: {why}")
        if "change" in words and "pok" in words:
            return self._shift(question, look, context)
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
