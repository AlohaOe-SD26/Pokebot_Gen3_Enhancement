"""USER RULING 19 (2026-09-26): when a gym leader KEEPS WINNING, teach an OWNED TM that hits the foe that beats us.

⭐ WHAT THIS IS FOR. The bot collects gym TMs (Wattson's TM34 Shock Wave, Flannery's TM50 Overheat, Roxanne's TM39 Rock
Tomb, ...) and never uses them. The user ruled "teach an owned TM" (and NOT: Surf-on-battler, protect-answers).
Scope: Winona and Juan — the SINGLE-battle bosses whose fight config carries a `name`; the recon found no owned
super-effective TM at gyms 1-5, and Tate & Liza is a DOUBLE battle (two foes out; the turn record sees one).
⚠ MEASURED 2026-09-26 (145 Winona losses in that day's batch, the foe we faced last): Skarmory 71, ALTARIA 64,
Pelipper 5, Tropius 4, Swablu 1 — the wall is PER RUN and half the runs are walled by Altaria, not Skarmory. Juan:
Kingdra 40, Crawdaunt 5 — nothing we own is super-effective on Kingdra, so Juan is mostly out of reach.

THE SHAPE (a planner that is PURE and gated offline, and one bounded, fail-open action) — DESIGN 4. Designs 1-3 were
refuted before any drive by a decomp read, two observe-only runs on real fixtures, and an adversarial review
(`ai-research-notes/2026-09-26-ruling19-gymtm-GRADED.md`):
  1. THE WALL, BY IDENTITY, WEIGHTED BY OUR FAINTS, FROM THE LEADER'S OWN BATTLES. Every decision the battle loop
     makes is recorded with the foe it faced (`battle_action_selection.TURN_FOE["log"]`); a lost battle whose enemy
     party IS the leader's roster (checked at battle start) files, per foe species, how many of our mons it was facing
     when they went down (`_loss_foe_history`). The wall = the species with the most of our faints over the last
     `RECENT_LOSSES` such losses, needing at least two.
     ⛔ NOT the KO COUNT (design 1): only a trainer's LEAD is party order; every replacement is the AI's pick
     (`battle_ai_switch_items.c` `GetMostSuitableMonToSwitchInto`). ⛔ NOT the last foe alone (design 3): Skarmory can
     down four of ours and Altaria the fifth. ⛔ NOT any battle on the gym map: Winona's gym trainers use Skarmory,
     Tropius, Pelipper and Swablu too.
  2. THE RECIPIENT MUST ACTUALLY FACE THE WALL. The lead and the faint replacement are USER-RULED and rank DEFENCE
     first (`rank_replacement`: `(cannot_damage, incoming, -outgoing, ...)`). Every Winona mon is part-Flying, so a
     Grass or Fire/Fighting mon (2x incoming) is fielded LAST — on real fixtures 10 of 14 design-3 plans went to such
     a mon. ⇒ only a battler in the MINIMUM-incoming group against the wall's types may receive the TM (the ruled
     key's own defensive term, used as a predictor, not changed).
  3. THE PAIR MUST WIN SOMETHING. A small Gen-3 duel estimate (`duel_share`): the recipient's expected damage to the
     wall before the wall's best move KOs it, over the wall's HP (trainer IVs and the decomp's own movesets). Below
     `MIN_SHARE` it is not taught. Ranked by share, then drawback-free (never misses, no self drop), then coverage.
     ⚠ It ignores the leader's two Hyper Potions and in-battle stat stages — it is a filter against HOPELESS teaches,
     not a win predictor.
  4. THE SLOT — empty > non-HM status > a strictly dominated move > the weakest non-STAB move (`choose_slot`). Never
     an HM move (the game refuses), never an undominated STAB move, never the last damaging move.
  5. THE ACT — `pokemon_league.teach_move_from_bag` ONLY (its cursors are verified; `teach_hm_or_tm` confirms index 0
     blind — KI-88/89), inside a real-frame budget, only from a controllable overworld with no script running, and the
     menus closed after by a TEACH-AWARE close (`_leave_teach_menus`: B alone cannot leave the learn-move Yes/No pair —
     each NO opens the other). ANY failure is logged and the fight goes on as today.
  6. NOT A LEVER-KILLER. A taught move is recorded (`mode._gym_tm_taught_moves`) and does NOT count as a credible
     answer in `_boss_plan_is_hopeless`, so the counter ladder and the honest stop are untouched by the teach; its PID
     is protected from make-room deposits (`pc_trip`). A second teach for the same boss waits until the first taught
     move has been SEEN chosen against its wall (`note_boss_battle`).

⛔ TMs are SINGLE-USE in Gen 3 (`party_menu.c`). Hence the per-(boss, TM) latch, written BEFORE the act, and a
verification by IDENTITY afterwards (the recipient's PID knows the move; the TM count dropped by one).
Arms (registered in `29`): `POKEBOT_GYMTM_FAULT_NOTEACH` (plan and latch, skip the act — the A/B arm) and
`POKEBOT_GYMTM_FAULT_BUDGET=<frames>` (the budget expires mid-teach — drives the menu-close recovery).
"""
from __future__ import annotations

import math
import os
from collections import Counter
from dataclasses import dataclass, field
from typing import Generator

from modules.context import context


@dataclass(frozen=True)
class WallMove:
    name: str
    type: str
    power: int


@dataclass(frozen=True)
class RosterMon:
    species: str
    level: int
    iv: int  # the fixed IV every stat gets: `trainer .iv * 31 / 255` (`battle_main.c` CreateNPCTrainerParty)
    moves: tuple[WallMove, ...]  # DAMAGING moves only (status moves cannot KO a recipient)


def _w(name: str, type_: str, power: int) -> WallMove:
    return WallMove(name, type_, power)


#: The leaders' FIRST-fight parties from the decomp (`src/data/trainer_parties.h`: `sParty_Winona1` :3508,
#: `sParty_Juan1` :3577; header `src/data/trainers.h`; read by a Claude agent 2026-09-26, pokeemerald HEAD c925b848).
#: Keyed by the fight config's `name`. ⚠ The ORDER is membership only — not the send-out order after the lead.
#: Fury Attack (2-5 hits) is entered at 15 x 3; Solar Beam at its full 120 (it charges a turn — this OVERSTATES the
#: wall, which only makes the duel estimate more conservative). Flail (variable power) is left out.
#: ⛔ Tate & Liza (`sParty_TateAndLiza1`, `.doubleBattle = TRUE`) is deliberately ABSENT: two foes are out at once and
#: the turn record sees only the left one, so no loss could name its wall honestly.
GYM_ROSTERS: dict[str, tuple[RosterMon, ...]] = {
    "Winona": (
        RosterMon("Swablu", 29, 25, (_w("Aerial Ace", "Flying", 60),)),
        RosterMon("Tropius", 29, 25, (_w("Aerial Ace", "Flying", 60), _w("Solar Beam", "Grass", 120))),
        RosterMon("Pelipper", 30, 25, (_w("Water Gun", "Water", 40), _w("Aerial Ace", "Flying", 60))),
        RosterMon("Skarmory", 31, 26, (_w("Fury Attack", "Normal", 45), _w("Steel Wing", "Steel", 70),
                                       _w("Aerial Ace", "Flying", 60))),
        RosterMon("Altaria", 33, 31, (_w("Earthquake", "Ground", 100), _w("Dragon Breath", "Dragon", 60),
                                      _w("Aerial Ace", "Flying", 60))),
    ),
    "Juan": (
        RosterMon("Luvdisc", 41, 24, (_w("Water Pulse", "Water", 60),)),
        RosterMon("Whiscash", 41, 24, (_w("Water Pulse", "Water", 60), _w("Earthquake", "Ground", 100))),
        RosterMon("Sealeo", 43, 24, (_w("Body Slam", "Normal", 85), _w("Aurora Beam", "Ice", 65),
                                     _w("Water Pulse", "Water", 60))),
        RosterMon("Crawdaunt", 43, 24, (_w("Water Pulse", "Water", 60), _w("Crabhammer", "Water", 90))),
        RosterMon("Kingdra", 46, 30, (_w("Water Pulse", "Water", 60), _w("Ice Beam", "Ice", 95))),
    ),
}

#: The badge each boss awards — a taught recipient's deposit protection ends when it is earned (`protected_taught_pids`).
BOSS_BADGE = {"Winona": "BADGE06_GET", "Juan": "BADGE08_GET"}
#: A second teach for the same boss waits until the first taught move is SEEN chosen against its wall — but not for
#: ever: after this many further LEADER losses without seeing it, the wait is released (the recipient may simply never
#: face the wall; waiting forever would silently foreclose the rest of the ruling for that boss).
WAIT_RELEASE_LOSSES = 3

#: The planner looks at this many most-recent LEADER losses to name the wall, and needs at least two of them.
RECENT_LOSSES = 3
MIN_LOSSES_FOR_A_WALL = 2
#: The recipient's level floor is `max(wall level - WALL_LEVEL_SLACK, top level - LEVEL_WINDOW)`. LEVEL_WINDOW equals
#: `team_policy.DEAD_WEIGHT_LEVEL_GAP`, which is why a taught PID is also protected from deposits (`pc_trip`).
LEVEL_WINDOW = 8
WALL_LEVEL_SLACK = 2
#: A teach whose recipient cannot deal at least this share of the wall's HP before it faints is not worth a TM.
MIN_SHARE = 0.5
#: `story_mode.StoryMode.CREDIBLE_ANSWER_POWER` — the same bar: power x effectiveness x STAB. A 20-power 2x move is
#: not an answer (Rock Smash vs Norman lost 27 times running).
CREDIBLE_ANSWER_POWER = 75
#: `teach_move_from_bag` walks the bag, the party menu and the forget screen; a healthy teach took 1,842 frames.
TEACH_BUDGET = 12_000
#: Effects of a plain hit (with or without a secondary effect). Anything else — Focus Punch, Hyper Beam's recharge,
#: Dig/Fly, Solar Beam's charge, variable-power moves — is never worth a single-use TM here.
PLAIN_HIT_EFFECTS = ("HIT", "ALWAYS_HIT", "OVERHEAT", "EARTHQUAKE", "BRICK_BREAK", "THUNDER", "ABSORB", "FACADE",
                     "SECRET_POWER", "THIEF")
#: Effects that lower the USER's own stat after the hit — the greedy chooser spends them on the first foe they top.
SELF_DROP_EFFECTS = ("OVERHEAT", "SUPERPOWER")
#: Never Overheat onto the Torchic line before it knows Blaze Kick: the learn policy would then decline Blaze Kick
#: (Blaze Kick is offered once, at the L36 evolution to Blaziken — `species.json`).
TORCHIC_LINE = ("Torchic", "Combusken", "Blaziken")


def bench_species() -> tuple[str, ...]:
    """`victory_road.BENCH_SPECIES` — carried for HMs / field duty, never trained as fighters. Imported, not copied."""
    from modules.story.victory_road import BENCH_SPECIES

    return tuple(BENCH_SPECIES)


@dataclass(frozen=True)
class MoveView:
    name: str
    type: str
    power: int
    is_hm: bool
    priority: int = 0


@dataclass(frozen=True)
class MonView:
    """What the planner needs to know about one party member — plain data, so the planner is testable offline."""

    index: int
    pid: int
    species: str
    level: int
    types: tuple[str, ...]
    attack: int
    special_attack: int
    moves: tuple[MoveView | None, ...]
    learnable_tms: frozenset[str]
    is_egg: bool = False
    hp: int = 100
    defence: int = 50
    special_defence: int = 50
    speed: int = 50


@dataclass(frozen=True)
class TmView:
    tm: str
    move: str
    type: str
    power: int
    accuracy: float
    effect: str


@dataclass
class TeachPlan:
    boss: str
    tm: str
    move: str
    party_index: int
    pid: int
    species: str
    slot: int
    replaced: str
    wall: str
    share: float
    drawback_free: bool
    coverage: int
    reasons: list[str] = field(default_factory=list)


# ---- type and damage maths (pure over the game's own type chart and base stats) ----------------------------------------

def _type(name: str):
    from modules.pokemon import get_type_by_name

    return get_type_by_name(name)


def _species(name: str):
    from modules.pokemon import get_species_by_name

    return get_species_by_name(name)


def multiplier(move_type: str, defender_types: tuple[str, ...]) -> float:
    m = 1.0
    for t in defender_types:
        m *= _type(move_type).get_effectiveness_against(_type(t))
    return m


def effectiveness(move_type: str, defender_species: str) -> float:
    """The multiplier of `move_type` on `defender_species`, from the real type chart. Levitate makes Ground 0 (trainer
    mons always carry ability slot 0 — `CreateNPCTrainerParty` — and every Levitate species has it there)."""
    species = _species(defender_species)
    if move_type == "Ground" and species.abilities and species.abilities[0].name == "Levitate":
        return 0.0
    return multiplier(move_type, tuple(t.name for t in species.types))


def incoming(wall: str, mon_types: tuple[str, ...]) -> float:
    """`rank_replacement`'s DEFENSIVE term, verbatim in meaning: the worst the wall's TYPES do to `mon_types`."""
    return max(multiplier(t.name, mon_types) for t in _species(wall).types)


def wall_stats(mon: RosterMon) -> dict:
    """Gen-3 stats of a trainer mon: fixed IV, zero EVs, neutral nature (the nature is personality-derived and not
    modelled — a ±10% error on one stat)."""
    b = _species(mon.species).base_stats
    lv, iv = mon.level, mon.iv
    other = lambda base: (2 * base + iv) * lv // 100 + 5  # noqa: E731
    return {"hp": (2 * b.hp + iv) * lv // 100 + lv + 10, "attack": other(b.attack), "defence": other(b.defence),
            "special_attack": other(b.special_attack), "special_defence": other(b.special_defence),
            "speed": other(b.speed)}


def gen3_damage(level: int, power: int, attack: int, defence: int, stab: bool, mult: float) -> float:
    """The mean of Gen 3's damage roll (`pokemon.c` CalculateBaseDamage, then x0.85-1.00): no crit, no weather."""
    base = ((2 * level // 5 + 2) * power * attack // max(1, defence)) // 50 + 2
    return base * (1.5 if stab else 1.0) * mult * 0.925


def duel_share(mon: MonView, tm: TmView, wall: RosterMon) -> float:
    """The share of the wall's HP the recipient is expected to deal with `tm` before the wall's best move KOs it.

    The recipient enters after a faint (a free switch-in). Faster ⇒ it acts every turn it survives; slower ⇒ one turn
    fewer. Overheat's second and later hits are at -2 SpA (half). Accuracy multiplies. Capped at 1.0."""
    ws = wall_stats(wall)
    wall_types = tuple(t.name for t in _species(wall.species).types)
    physical = _type(tm.type).is_physical
    ours = gen3_damage(mon.level, tm.power, mon.attack if physical else mon.special_attack,
                       ws["defence"] if physical else ws["special_defence"], tm.type in mon.types,
                       effectiveness(tm.type, wall.species))
    theirs = 0.0
    for wm in wall.moves:
        wphys = _type(wm.type).is_physical
        theirs = max(theirs, gen3_damage(wall.level, wm.power, ws["attack"] if wphys else ws["special_attack"],
                                         mon.defence if wphys else mon.special_defence, wm.type in wall_types,
                                         multiplier(wm.type, mon.types)))
    hits_to_ko_us = math.ceil(mon.hp / theirs) if theirs > 0 else 6
    attacks = min(6, hits_to_ko_us if mon.speed > ws["speed"] else hits_to_ko_us - 1)
    dealt = 0.0
    for n in range(max(0, attacks)):
        dealt += ours * (0.5 if (n > 0 and tm.effect in SELF_DROP_EFFECTS) else 1.0) * tm.accuracy
    return round(min(1.0, dealt / max(1, ws["hp"])), 2)


def credible_answer(mv: MoveView, mon_types: tuple[str, ...], wall: str) -> bool:
    """`_boss_plan_is_hopeless`'s bar, against the WALL: SUPER-EFFECTIVE (>= 2x) and power x effectiveness x STAB >=
    CREDIBLE_ANSWER_POWER. ⚠ Both halves: the first draft dropped the 2x test and read Mightyena's neutral STAB Bite
    (60 x 1 x 1.5 = 90) as "an answer to Swablu" — caught by the observe-only run, not by the gate."""
    if mv is None or mv.power <= 0:
        return False
    eff = effectiveness(mv.type, wall)
    return eff >= 2.0 and mv.power * eff * (1.5 if mv.type in mon_types else 1.0) >= CREDIBLE_ANSWER_POWER


# ---- the wall ----------------------------------------------------------------------------------------------------------

def faints_by_foe(decisions: list) -> dict:
    """From one battle's decision log `[(our_pid, our_species, action, foe_species), ...]`: for each of OUR mons, the
    foe it was facing at its LAST decision — in a lost battle every one of ours went down, so that is (to within an AI
    switch between our last decision and the KO) the foe that downed it. Returns {foe species: our faints}."""
    last: dict = {}
    for our_pid, _species, _action, foe in decisions:
        if foe:
            last[our_pid] = foe
    return dict(Counter(last.values()))


def wall_species(losses: list, roster: tuple[RosterMon, ...]) -> str | None:
    """The species with the most of OUR faints over the last `RECENT_LOSSES` LEADER losses. `losses` is a list of
    {foe species: faints} per loss. Needs `MIN_LOSSES_FOR_A_WALL` losses with a roster foe in them; a tie goes to the
    foe of the MOST RECENT loss. Species outside the roster are ignored — never guess a wall."""
    members = {m.species for m in roster}
    usable = [{f: n for f, n in loss.items() if f in members} for loss in losses]
    usable = [u for u in usable if u][-RECENT_LOSSES:]
    if len(usable) < MIN_LOSSES_FOR_A_WALL:
        return None
    total: Counter = Counter()
    for u in usable:
        total.update(u)
    best = max(total.values())
    tied = {f for f, n in total.items() if n == best}
    for u in reversed(usable):
        for f, _n in sorted(u.items(), key=lambda kv: -kv[1]):
            if f in tied:
                return f
    return sorted(tied)[0]


# ---- the slot ----------------------------------------------------------------------------------------------------------

def choose_slot(moves: tuple[MoveView | None, ...], mon_types: tuple[str, ...] = ()) -> tuple[int, str] | None:
    """Which move slot the TM may overwrite: (index, what it replaces) or None when every choice would harm the mon.

    Order: (1) an EMPTY slot; (2) a non-HM STATUS move; (3) a non-HM damaging move that is STRICTLY DOMINATED — another
    kept damaging move (an HM counts) has the same type and at least its power, so nothing is lost (Loudred's Pound
    beside Stomp); (4) the weakest non-HM damaging move that is NOT a STAB move (a priority move loses a tie — it
    finishes weakened foes). NEVER: an HM move (the game refuses to forget one), a STAB move that nothing dominates,
    or the last damaging move.
    ⚠ Steps 3-4 are the SECOND slot design. The first ("any move whose type another shares") failed the observe-only
    run two ways on 2026-09-26: Sceptile [Rock Smash, Pursuit, Leaf Blade, Quick Attack] — four types, no status — could
    never learn; and Blaziken would have lost Double Kick (Fighting STAB, 30) because Rock Smash (Fighting, 20) "shares
    its type", keeping Scratch. It matches the level-up learn policy (`which_move_should_be_replaced`) on every fixture
    case measured; where they could differ, the learn policy re-decides at the next level-up anyway."""
    for i in range(4):
        if i >= len(moves) or moves[i] is None:
            return i, "<empty>"
    for i, mv in enumerate(moves):
        if mv is not None and not mv.is_hm and mv.power == 0:
            return i, mv.name
    damaging = [(i, mv) for i, mv in enumerate(moves) if mv is not None and mv.power > 0]
    if len(damaging) <= 1:
        return None
    dominated = [(mv.power, mv.priority > 0, i, mv.name) for i, mv in damaging
                 if not mv.is_hm and any(j != i and o.type == mv.type and o.power >= mv.power for j, o in damaging)]
    if dominated:
        _power, _prio, i, name = min(dominated)
        return i, name
    off_type = [(mv.power, mv.priority > 0, i, mv.name) for i, mv in damaging
                if not mv.is_hm and mv.type not in mon_types]
    if off_type:
        _power, _prio, i, name = min(off_type)
        return i, name
    return None


# ---- the planner -------------------------------------------------------------------------------------------------------

def plan_teach(boss: str, roster: tuple[RosterMon, ...], wall: str, party: list[MonView], owned: list[TmView],
               latched: set, excluded_pids: set, banned: tuple[str, ...] = ()) -> tuple[TeachPlan | None, list[str]]:
    """PURE. The best (TM, recipient, slot) against the wall, or (None, reasons). `reasons` explains every refusal so a
    run that does NOT teach says why in its log — a silent no-op is indistinguishable from a broken hook."""
    reasons: list[str] = []
    wall_mon = next(m for m in roster if m.species == wall)
    battlers = [m for m in party if not m.is_egg and any(mv is not None and mv.power > 0 for mv in m.moves)]
    if not battlers:
        return None, ["no battler in the party"]
    top = max(m.level for m in battlers)
    floor = max(wall_mon.level - WALL_LEVEL_SLACK, top - LEVEL_WINDOW)
    tms = []
    for tm in owned:
        if (boss, tm.tm) in latched:
            reasons.append(f"{tm.tm} already tried against {boss} this run")
        elif tm.power <= 0:
            reasons.append(f"{tm.tm} ({tm.move}) is not a damaging move")
        elif tm.move in banned:
            reasons.append(f"{tm.tm} ({tm.move}) is a banned move — the battle strategy never selects it")
        elif not (tm.effect in PLAIN_HIT_EFFECTS or tm.effect.endswith("_HIT")):
            reasons.append(f"{tm.tm} ({tm.move}) is not a plain hit ({tm.effect})")
        elif effectiveness(tm.type, wall) < 2.0:
            reasons.append(f"{tm.tm} ({tm.move}) is not super-effective on {wall}")
        else:
            tms.append(tm)
    if not tms:
        return None, reasons or ["no owned TM"]
    # REACH: the ruled replacement key ranks `incoming` first, so only the best-resisting group is ever sent in.
    reach = min(incoming(wall, m.types) for m in battlers)
    best: TeachPlan | None = None
    best_key = None
    for mon in battlers:
        if mon.pid in excluded_pids:
            reasons.append(f"{mon.species} is a hunted counter (protected)")
            continue
        if mon.species in bench_species():
            reasons.append(f"{mon.species} is a bench species")
            continue
        if mon.level < floor:
            reasons.append(f"{mon.species} L{mon.level} is below the floor L{floor} (wall L{wall_mon.level}, top L{top})")
            continue
        if incoming(wall, mon.types) > reach:
            reasons.append(f"{mon.species} would never be fielded against {wall} (incoming "
                           f"{incoming(wall, mon.types):.1f} > the best {reach:.1f})")
            continue
        if any(credible_answer(mv, mon.types, wall) for mv in mon.moves):
            reasons.append(f"{mon.species} already has a credible answer to {wall}")
            continue
        slot = choose_slot(mon.moves, mon.types)
        if slot is None:
            reasons.append(f"{mon.species} has no slot it can safely give up")
            continue
        for tm in tms:
            if tm.tm not in mon.learnable_tms:
                continue
            if any(mv is not None and mv.name == tm.move for mv in mon.moves):
                continue
            if tm.tm == "TM50" and mon.species in TORCHIC_LINE and not any(
                    mv is not None and mv.name == "Blaze Kick" for mv in mon.moves):
                reasons.append(f"{mon.species} must not take Overheat before Blaze Kick")
                continue
            share = duel_share(mon, tm, wall_mon)
            if share < MIN_SHARE:
                reasons.append(f"{tm.tm} on {mon.species} deals only {share:.0%} of {wall}'s HP before it faints")
                continue
            coverage = sum(1 for m in roster if effectiveness(tm.type, m.species) >= 2.0)
            drawback_free = tm.accuracy >= 1.0 and tm.effect not in SELF_DROP_EFFECTS
            key = (share, drawback_free, coverage)
            if best_key is None or key > best_key:
                best_key = key
                best = TeachPlan(boss=boss, tm=tm.tm, move=tm.move, party_index=mon.index, pid=mon.pid,
                                 species=mon.species, slot=slot[0], replaced=slot[1], wall=wall, share=share,
                                 drawback_free=drawback_free, coverage=coverage)
    if best is None:
        reasons.append(f"no eligible battler can take {[t.tm for t in tms]} usefully")
        return None, reasons
    best.reasons = reasons
    return best, reasons


# ---- live adapters -----------------------------------------------------------------------------------------------------

def _move_view(learned) -> MoveView | None:
    from modules.items import get_item_by_move_id

    if learned is None or learned.move is None:
        return None
    as_item = get_item_by_move_id(learned.move.index)
    return MoveView(name=learned.move.name, type=learned.move.type.name, power=learned.move.base_power,
                    is_hm=bool(as_item is not None and as_item.name.startswith("HM")),
                    priority=int(learned.move.priority))


def mon_view(index: int, pokemon, tm_items: dict) -> MonView:
    moves = tuple(_move_view(m) for m in list(pokemon.moves)[:4])
    learnable = frozenset(name for name, item in tm_items.items() if pokemon.species.can_learn_tm_hm(item))
    st = pokemon.stats
    return MonView(index=index, pid=pokemon.personality_value, species=pokemon.species.name, level=pokemon.level,
                   types=tuple(t.name for t in pokemon.species.types), attack=st.attack,
                   special_attack=st.special_attack, moves=moves, learnable_tms=learnable, is_egg=pokemon.is_egg,
                   hp=st.hp, defence=st.defence, special_defence=st.special_defence, speed=st.speed)


def owned_tms() -> tuple[list[TmView], dict]:
    """The TMs in the bag (quantity > 0) as views, plus name -> Item for `can_learn_tm_hm` (it takes the ITEM — a
    string reads False). The move comes from the item itself (`Item.tm_hm_move()`)."""
    from modules.items import get_item_bag

    views, items = [], {}
    for slot in get_item_bag().tms_hms:
        if slot.quantity <= 0 or not slot.item.name.startswith("TM"):
            continue
        mv = slot.item.tm_hm_move()
        if mv is None:
            continue
        views.append(TmView(tm=slot.item.name, move=mv.name, type=mv.type.name, power=mv.base_power,
                            accuracy=mv.accuracy if mv.accuracy > 0 else 1.0, effect=mv.effect))
        items[slot.item.name] = slot.item
    return views, items


def protected_pids(mode) -> set:
    """PIDs the teach must not touch: the HUNTED COUNTERS (`_hunted_counter_pids`) — each was caught for a matchup of
    its own, and the lead policy already promotes it for that fight.

    ⛔ NOT "HM carriers" — the recon suggested excluding them and the first observe-only run (2026-09-26,
    `probe_gymtm_inputs.py` on `fortree_gym_wedge.ss1`) showed why that is wrong: Sceptile, the LEAD, knows Rock Smash,
    so the rule excluded the one mon on the team that could learn anything. The protection an HM carrier needs is that
    its HM moves are never overwritten, and `choose_slot` already guarantees that (the game refuses anyway)."""
    return set(getattr(mode, "_hunted_counter_pids", ()) or ())


def protected_taught_pids(mode) -> set:
    """PIDs of mons that received a gym TM this run whose boss is NOT yet beaten — `pc_trip` must not box them (they sit
    at the dead-weight level boundary by design). Once the boss's badge is earned the protection ends: the TM did its
    job, and a later deposit is an ordinary team decision again. An unreadable flag keeps the protection (fail safe)."""
    from modules.memory import get_event_flag

    out = set()
    for (pid, _move), info in (getattr(mode, "_gym_tm_taught_moves", None) or {}).items():
        badge = BOSS_BADGE.get(info.get("boss"))
        try:
            beaten = bool(badge and get_event_flag(badge))
        except Exception:  # noqa: BLE001 - unreadable ⇒ keep protecting (the safe side for a single-use TM)
            beaten = False
        if not beaten:
            out.add(pid)
    return out


def boss_for_enemy_party(species_names) -> str | None:
    """The boss whose roster IS this enemy party (same species set), else None — a gym TRAINER that shares a species
    (Winona's trainers use Skarmory, Tropius, Pelipper, Swablu) is not the leader."""
    names = {s for s in species_names if s}
    for boss, roster in GYM_ROSTERS.items():
        if names == {m.species for m in roster}:
            return boss
    return None


def leader_losses_for(mode, cfg: dict) -> list:
    """{foe species: our faints} for every lost LEADER battle at this boss's map keys, oldest first."""
    entries = sorted(entry for k in cfg.get("keys", ()) for entry in getattr(mode, "_loss_foe_history", {}).get(k, ()))
    return [faints for _seq, boss, faints in entries if boss == cfg.get("name")]


def note_boss_battle(mode, boss: str | None, decisions: list) -> None:
    """After a LEADER battle (won or lost): mark each taught move SEEN if the log shows its recipient choosing it
    against its wall. PURE over the log; never raises into the battle hook."""
    taught = getattr(mode, "_gym_tm_taught_moves", None)
    if not taught or not boss:
        return
    for (pid, move), info in taught.items():
        if info.get("boss") != boss or info.get("used"):
            continue
        if any(our_pid == pid and move in str(action) and foe == info.get("wall")
               for our_pid, _sp, action, foe in decisions):
            info["used"] = True


def _controllable_overworld() -> bool:
    from modules.memory import GameState, get_game_state
    from modules.player import player_avatar_is_controllable
    from modules.tasks import get_global_script_context

    return (get_game_state() is GameState.OVERWORLD and player_avatar_is_controllable()
            and not get_global_script_context().is_active)


def maybe_teach_gym_tm(mode, cfg: dict, losses: int, report: dict | None = None) -> Generator:
    """The hook `StoryMode._prepare_for_fight` calls when `losses >= 2`. Fails OPEN: any error is logged and the fight
    preparation continues exactly as before this ruling existed."""
    from modules import debug_logger
    from modules.console import console
    from modules.pokemon_party import get_party
    from modules.story.early_game import reraise_if_aborting

    report = {} if report is None else report
    boss = cfg.get("name")
    report["boss"] = boss
    # The LAST decision stays readable on the mode (`--driver gymtm` grades it; a live debugger can print it).
    try:
        mode._gym_tm_report = report
    except Exception:  # noqa: BLE001 - a read-only stub; the debug event below still carries the decision
        pass
    if losses < 2 or boss not in GYM_ROSTERS:
        report["outcome"] = "not armed"
        return
    latched: set = getattr(mode, "_gym_tm_taught", None)
    if latched is None:
        latched = set()
        mode._gym_tm_taught = latched
    taught_moves: dict = getattr(mode, "_gym_tm_taught_moves", None)
    if taught_moves is None:
        taught_moves = {}
        mode._gym_tm_taught_moves = taught_moves
    try:
        roster = GYM_ROSTERS[boss]
        history = leader_losses_for(mode, cfg)
        waiting = []
        for (_p, m), i in taught_moves.items():
            if i.get("boss") != boss or i.get("used") or i.get("released"):
                continue
            if len(history) - int(i.get("losses_at_teach", 0)) >= WAIT_RELEASE_LOSSES:
                i["released"] = True  # not seen used after WAIT_RELEASE_LOSSES more leader losses — stop waiting
                report.setdefault("released", []).append(f"{m} on {i.get('species')}")
                continue
            waiting.append(f"{m} on {i.get('species')} vs {i.get('wall')}")
        if waiting:
            report["outcome"] = f"waiting: the taught {waiting[0]} has not been seen used yet"
            return
        wall = wall_species(history, roster)
        report["faints"] = history[-RECENT_LOSSES:]
        report["wall"] = wall
        if wall is None:
            report["outcome"] = f"no wall yet ({len(history)} recorded leader loss(es); needs {MIN_LOSSES_FOR_A_WALL})"
            return
        owned, items = owned_tms()
        party = [mon_view(i, p, items) for i, p in enumerate(get_party()) if p is not None]
        banned = tuple(getattr(getattr(context.config, "battle", None), "banned_moves", ()) or ())
        plan, reasons = plan_teach(boss, roster, wall, party, owned, latched, protected_pids(mode), banned)
        report["reasons"] = reasons
        if plan is None:
            report["outcome"] = "no plan"
            return
        report["plan"] = (f"{plan.tm} {plan.move} -> {plan.species} (slot {plan.party_index}, pid {plan.pid:08x}) "
                          f"replacing {plan.replaced} [share {plan.share:.0%}, drawback-free {plan.drawback_free}, "
                          f"coverage {plan.coverage}]")
        if not _controllable_overworld():
            report["outcome"] = "not in a controllable overworld — skipped (no latch)"
            return
        # ⛔ LATCH BEFORE THE ACT: a single-use TM must never be re-attempted by a derail retry of the same fight.
        latched.add((boss, plan.tm))
        if os.environ.get("POKEBOT_GYMTM_FAULT_NOTEACH") == "1":
            report["outcome"] = "planned, act skipped (POKEBOT_GYMTM_FAULT_NOTEACH)"
            return
        report["outcome"] = yield from _teach(plan, items[plan.tm], report)
        if report["outcome"].startswith("taught"):
            taught_moves[(plan.pid, plan.move)] = {"boss": boss, "wall": plan.wall, "species": plan.species,
                                                   "used": False, "losses_at_teach": len(history)}
    except Exception as error:  # noqa: BLE001 - RULING 19 fails OPEN: a teach that cannot happen must not cost the run
        reraise_if_aborting(error)
        report["outcome"] = "error"
        report["error"] = f"{type(error).__name__}: {str(error)[:200]}"
    finally:
        try:
            debug_logger.event(
                f"boss={boss} losses={losses} faints={report.get('faints')} wall={report.get('wall')} "
                f"outcome={report.get('outcome')!r} plan={report.get('plan')} error={report.get('error')} "
                f"why={(report.get('reasons') or [])[:8]}", category="GYM_TM")
        except Exception:  # noqa: BLE001 - telemetry must never break the story; a missing line is visible
            pass
    console.print(f"[cyan]Story: gym-TM teach vs {boss} — {report.get('outcome')}"
                  f"{': ' + report['plan'] if report.get('plan') else ''}.[/]")


def _leave_teach_menus() -> Generator:
    """Back out of a half-finished TEACH to a controllable overworld, bounded. ⛔ B ALONE CANNOT: on the learn-move pair,
    B answers NO, and each NO opens the other prompt (`party_menu.c`: "Delete a move?" NO → "Stop trying to teach?";
    that NO → "Delete a move?" again). So EVERY press re-reads the learn-move state: YES (A) on "Stop trying to teach?"
    — which stops the teach and consumes no TM — and B everywhere else, until the overworld is back.
    ‼ MEASURED 2026-09-26 (`--driver gymtm`, Q4, budget 600): the first version answered the prompts only until the
    first frame with no dialogue, then handed to the plain B-only close. There is a message frame BETWEEN the two
    prompts, so it handed over at once, and the plain close ping-ponged them until it gave up in PARTY_MENU. ⇒ One
    loop, the state read on every iteration, never "prompts first, then the ordinary close"."""
    from modules.battle_move_replacing import LearnMoveState, get_learn_move_state
    from modules.memory import GameState, get_game_state
    from modules.menuing import is_fade_active
    from modules.modes.util.sleep import wait_for_n_frames
    from modules.modes.util.tasks_scripts import wait_for_task_to_start_and_finish
    from modules.story.early_game import wait_until_truly_controllable
    from modules.tasks import task_is_active

    for _ in range(150):
        state = get_game_state()
        if state is GameState.OVERWORLD and not is_fade_active() and not task_is_active("Task_ShowStartMenu"):
            break
        try:
            learn = get_learn_move_state()
        except Exception:  # noqa: BLE001 - an unreadable learn state is treated as "no prompt" (B is then correct)
            learn = None
        if learn is LearnMoveState.ConfirmCancellation:
            context.emulator.press_button("A")
        elif state is GameState.BAG_MENU and not is_fade_active() and learn in (None, LearnMoveState.DialogueNotActive):
            # ⭐ The proven exit (`pokemon_league.heal_party_from_bag`): B until the start menu, B until it closes.
            yield from wait_for_task_to_start_and_finish("Task_ShowStartMenu", "B")
            continue
        else:
            context.emulator.press_button("B")
        yield from wait_for_n_frames(10)
    yield from wait_until_truly_controllable()


def _teach(plan: TeachPlan, item, report: dict) -> Generator:
    """The bounded act, verified by IDENTITY. Returns the outcome string."""
    from modules.items import get_item_bag
    from modules.pokemon_party import get_party
    from modules.story.early_game import _yield_bounded_by_frames, reraise_if_aborting
    from modules.story.pokemon_league import teach_move_from_bag

    before = get_item_bag().quantity_of(item)
    budget = int(os.environ.get("POKEBOT_GYMTM_FAULT_BUDGET") or TEACH_BUDGET)
    report["budget"] = budget
    try:
        report["finished"] = yield from _yield_bounded_by_frames(
            teach_move_from_bag(item, plan.party_index, plan.slot), budget)
    except Exception as error:  # noqa: BLE001 - recorded; the menu close below runs either way
        reraise_if_aborting(error)
        report["teach_error"] = f"{type(error).__name__}: {str(error)[:200]}"
    # ⛔ An expired budget closes the teach from OUTSIDE, so its own cleanup never ran — the bag, the party menu, the
    # forget screen or the learn-move prompts can still be up. Close them, bounded, before the story walks anywhere.
    try:
        yield from _yield_bounded_by_frames(_leave_teach_menus(), 4_000)
    except Exception as error:  # noqa: BLE001 - recorded; the verification below judges the end state
        reraise_if_aborting(error)
        report["leave_menus_error"] = f"{type(error).__name__}: {str(error)[:160]}"
    # IDENTITY, never position: find the recipient by PID (a slot can move) and read what it knows NOW.
    holder = next((p for p in get_party() if p is not None and p.personality_value == plan.pid), None)
    knows = holder is not None and any(m is not None and m.move is not None and m.move.name == plan.move
                                       for m in holder.moves)
    after = get_item_bag().quantity_of(item)
    report["tm_count"] = (before, after)
    if knows and after == before - 1:
        return "taught"
    if knows:
        return f"taught, but the TM count went {before} -> {after}"
    return "not taught" + (" (budget expired)" if report.get("finished") is False else "")
