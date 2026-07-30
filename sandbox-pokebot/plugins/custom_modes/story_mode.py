"""Story Mode (#24) — plays Emerald's story from a fresh save or continues an
existing one, building a team toward the Elite Four.

Built in verifiable chunks (see PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md):
  * Chapter 0 (the New Game intro) — IMPLEMENTED. Title -> New Game -> Birch's
    speech -> gender -> name -> lands in the moving truck.
  * Existing saves — the read-only detector reports the current chapter so the
    bot can resume at the right place (chapter execution beyond 0 is WIP).

On start:
  * If the game is still at the title/main menu (a fresh, save-less boot), the
    intro is run using the name/gender from ``<profile>/story.yml``.
  * If a game is already loaded (existing progress), the current chapter is
    detected and reported; execution of chapters > 0 is not built yet, so the
    bot hands back to manual after reporting.
"""

from types import SimpleNamespace
from typing import Generator

from modules.console import console
from modules.context import context
from modules.memory import GameState, game_has_started, get_game_state
from modules.modes import BattleAction, BotMode
from modules.battle_strategies import BattleStrategyUtil, TurnAction
from modules.battle_strategies.catch import CatchStrategy
from modules.battle_strategies.level_up import LevelUpLeadBattleStrategy
from modules.battle_strategies.run_away import RunAwayStrategy


class StoryFleeStrategy(RunAwayStrategy):
    """Flee a WILD battle without tripping the post-battle lead rotation.

    ‼ CRASHED A LIVE RUN (batch 20260726-052205 run03, fixed same day). Stock
    `RunAwayStrategy.choose_new_lead_after_battle()` returns **False**, though it is
    annotated `int | None`. The framework only ever drove that class from
    `BattleListener.run_away_from_battle()`, which does NOT rotate leads, so the odd
    return value was harmless and invisible. SURVIVAL MODE returns a flee strategy from
    `on_battle_started` instead, which routes it through `BattleListener.fight()` — and
    that path does:

        if strategy.choose_new_lead_after_battle() is not None:
            yield from self.rotate_lead_pokemon(...)

    `False is not None`, so it rotated to party index `False`, and `RotatePokemon`
    raised `RuntimeError: Cannot rotate Pokémon #False with itself` right after
    "Got away safely!" — dropping the run to Manual with no controller on the stack.

    Returning a proper `None` says "keep the current lead", which is what fleeing wants.
    Done as a SUBCLASS rather than by editing the upstream file, so the framework's own
    flee path keeps its existing behaviour exactly.
    """

    def choose_new_lead_after_battle(self) -> int | None:
        return None


class StoryCatchStrategy(CatchStrategy):
    """Catch strategy for the Story bot that NEVER drops to Manual when out of Poké
    Balls. The stock CatchStrategy calls `switch_to_manual()` the moment it can't
    throw a ball — but opportunistic pre-gym catching can burn through the 5 starter
    balls on bad catch RNG before the team is full, which stranded the bot in Manual
    (user-seen). Here, if no ball can be thrown, we FLEE and carry on instead; the
    story then stops catching (the `_should_catch` floor) until balls are restocked
    at a mart before the gym. (User directive: out of balls → finish the battle,
    never break.)"""

    def decide_turn(self, battle_state):
        try:
            if self._get_best_poke_ball(battle_state) is None:
                context.message = "Story: out of Poké Balls — fleeing this catch and moving on."
                return TurnAction.run_away()
        except Exception:
            pass
        return super().decide_turn(battle_state)


class StoryShinyCatchStrategy(StoryCatchStrategy):
    """Catch strategy for a WILD SHINY in Story mode (user directive 2026-07-22: shinies
    are rare collectibles — a real run's debug log showed a Shiny Poochyena being FOUGHT
    with 32 balls in the bag, because the old contingency only ever fought through).

    ALWAYS attempts the catch while any allowed ball remains — even an already-owned
    species, even with a full party (the catch goes to the PC box, vanilla behavior),
    at any story stage. The ONE behavioral difference from the parent: if balls run out
    MID-battle, a shiny is NOT fled (the parent's rule for ordinary team-catching) and
    NEVER dropped to Manual (the stock base's rule) — it is fought through like a normal
    battle (attack with the strongest usable move; Struggle if nothing has PP), per the
    user's spec: attempt until success, whiteout, or out of balls — then just fight."""

    def decide_turn(self, battle_state):
        try:
            if self._get_best_poke_ball(battle_state) is None:
                context.message = "Story: ran out of usable Poké Balls mid-shiny — fighting it through."
                util = BattleStrategyUtil(battle_state)
                active = battle_state.own_side.active_battler
                move = util.get_strongest_move_against(active, battle_state.opponent.active_battler)
                if move is not None:
                    return TurnAction.use_move(move)
                if active is not None:
                    for i, learned in enumerate(active.moves):
                        if learned is not None and util.move_is_usable(learned):
                            return TurnAction.use_move(i)
                    # PP-only last resort — see the single-battle branch's comment.
                    for i, learned in enumerate(active.moves):
                        if learned is not None and learned.pp > 0:
                            return TurnAction.use_move(i)
                return TurnAction.use_move(0)  # every move truly at 0 PP → the game Struggles
        except Exception:
            pass
        # Balls available: the grandparent CatchStrategy does the real work (status move
        # when catch odds are poor, then throw the best ALLOWED ball — the #40 allowlist
        # already protects the Master Ball by default). Deliberately skip the parent's
        # decide_turn so its out-of-balls flee branch can never fire for a shiny.
        return CatchStrategy.decide_turn(self, battle_state)


class LevelUpTravelBattleStrategy(LevelUpLeadBattleStrategy):
    """Fights to win like LevelUpLead, but NEVER flees a TRAINER battle.

    Story travel crosses routes that have trainers, and at this point the party
    is often a SINGLE Pokémon — so when its HP dips, the parent strategy tries
    to flee/rotate, and in a trainer battle (which you cannot flee) that raises
    ``RuntimeError: Tried to run away from a trainer battle`` (ML-8). Here a
    trainer battle always fights on with the strongest move instead; the caller
    heals to full first so the lead can win. WILD battles keep the parent
    behaviour (flee at low HP — the training loop heals for that)."""

    def choose_new_lead_after_faint(self, battle_state):
        """MATCHUP-AWARE replacement pick (user discussion 2026-07-23, Wattson analysis):
        the stock chooser sends the highest-HP living mon — which in the Wattson run
        meant full-HP Swellow and Ninjask (both Electric-weak) walking into
        Thunderbolts, attempt after attempt. The game asks us to CHOOSE, so choose
        like a player: prefer the mon the opponent hits least effectively (worst-case
        STAB from the opponent's types), then the one whose own usable moves hit the
        opponent hardest, then HP fraction, then level. Falls back to the stock pick
        on any surprise (missing data → the parent's HP rule)."""
        try:
            from modules.pokemon_party import get_party as _gp

            # Opponent type PAIRS on the field right now (both actives in a double).
            # Kept as per-battler pairs: effectiveness against a dual-type is the
            # PRODUCT over its two types (Ground vs Flying/Electric is 0x, not 2x).
            foe_pairs = []
            for battler in (
                getattr(battle_state.opponent, "left_battler", None),
                getattr(battle_state.opponent, "right_battler", None),
            ):
                if battler is not None:
                    try:
                        foe_pairs.append(list(battler.species.types))
                    except Exception:
                        pass
            foe_types = [t for pair in foe_pairs for t in pair]
            if not foe_types:
                return super().choose_new_lead_after_faint(battle_state)

            def _excluded(index) -> bool:
                if not battle_state.is_double_battle:
                    return False
                for battler in (battle_state.own_side.left_battler, battle_state.own_side.right_battler):
                    if battler is not None and battler.party_index == index:
                        return True
                return False

            best_index, best_key = None, None
            for index, mon in enumerate(_gp()):
                if mon is None or mon.is_egg or mon.current_hp <= 0 or _excluded(index):
                    continue
                try:
                    mon_types = mon.species.types
                except Exception:
                    mon_types = []
                # Defensive: the worst the foe's STAB can do to this mon (lower = better).
                incoming = 0.0
                for ft in foe_types:
                    m = 1.0
                    for t in mon_types:
                        m *= ft.get_effectiveness_against(t)
                    incoming = max(incoming, m)
                # Offensive: the best effectiveness among its usable damaging moves,
                # judged against each opponent's full type pair.
                outgoing = 0.0
                for learned in mon.moves:
                    if learned is None or learned.pp == 0 or learned.move.base_power == 0:
                        continue
                    for pair in foe_pairs:
                        m = 1.0
                        for t in pair:
                            m *= learned.move.type.get_effectiveness_against(t)
                        outgoing = max(outgoing, m)
                hp_fraction = mon.current_hp / max(1, mon.total_hp)
                key = (incoming, -outgoing, -hp_fraction, -mon.level)
                if best_key is None or key < best_key:
                    best_index, best_key = index, key
            if best_index is not None:
                return best_index
        except Exception:
            pass
        return super().choose_new_lead_after_faint(battle_state)

    def decide_turn(self, battle_state):
        if battle_state.is_trainer_battle:
            util = BattleStrategyUtil(battle_state)
            active = battle_state.own_side.active_battler
            move = util.get_strongest_move_against(active, battle_state.opponent.active_battler)
            if move is not None:
                return TurnAction.use_move(move)
            # No "strongest" (damaging, in-PP) move. A trainer / gym-leader / Elite-Four
            # battle CANNOT be fled and must NEVER stall (user directive 2026-07-21). Do NOT
            # fall through to the parent's rotate/flee path:
            #   • fleeing a trainer battle raises ("can't run from a trainer"), and
            #   • rotating into a weak/underlevelled bench can HANG the in-battle party-menu
            #     switch (battle_action_selection.py — "while PARTY_MENU: press A") — this is
            #     the Roxanne hang the user hit with Torchic (Fire) vs Rock + an L6-7 bench.
            # Instead keep ATTACKING with any move that still has PP (the game auto-uses
            # STRUGGLE if none), so the fight plays through to a win or a clean whiteout
            # (which triggers StoryMode's recovery). When the active mon faints,
            # handle_fainted_pokemon brings in the next one — we never proactively rotate in
            # a trainer battle, which sidesteps the party-menu-switch hang entirely.
            if active is not None:
                for i, learned in enumerate(active.moves):
                    if learned is not None and util.move_is_usable(learned):
                        return TurnAction.use_move(i)
                # ‼ SECOND PASS ON *PP ALONE* (2026-07-24, batch2 treecko hang at f1.2M:
                # `instr=BattleScript_SelectingMoveWithNoPP`,
                # `bt="There's no PP left for this move"`, inside
                # `EventScript_DoTrainerBattle` — 15,000 frames of no progress).
                # `move_is_usable` is STRICTER than "has PP" (it also rejects e.g.
                # disabled/zero-power moves), so a mon can fail every usability check
                # while still holding moves with PP. The old fallback then selected
                # SLOT 0 blindly — and Gen 3 does NOT silently substitute Struggle for
                # that: it prints "There's no PP left for this move!" and bounces
                # straight back to move selection. In an unfleeable trainer battle that
                # is an infinite loop. Struggle is only auto-used when EVERY move is out
                # of PP, in which case the game never shows the menu at all. So: pick
                # any move that genuinely has PP before falling back.
                for i, learned in enumerate(active.moves):
                    if learned is not None and learned.pp > 0:
                        return TurnAction.use_move(i)
            return TurnAction.use_move(0)  # every move truly at 0 PP → the game Struggles
        return super().decide_turn(battle_state)

    def decide_turn_in_double_battle(self, battle_state, battler_index):
        """Trainer DOUBLE battles must ATTACK THROUGH exactly like singles. They are very
        reachable: Emerald starts a TRUE double battle whenever TWO trainers spot you at
        once (e.g. walking between the Rustboro gym Youngsters), plus scripted pairs like
        Gabby & Ty. The inherited Default double path calls _handle_lead_cannot_battle
        when the actives are weak, and with the stock 'flee' config that RAISES in a
        trainer battle → Manual mid-battle (the user-reported "double battle bug";
        reproduced + chain-fixed via the KI-12 faint-bench repro 2026-07-22). Here:
        strongest usable move at whichever opponent is present; any in-PP move as
        fallback; Struggle at 0 PP; never flee, never rotate, never stall."""
        if not battle_state.is_trainer_battle:
            return super().decide_turn_in_double_battle(battle_state, battler_index)
        util = BattleStrategyUtil(battle_state)
        battler = (
            battle_state.own_side.left_battler if battler_index == 0 else battle_state.own_side.right_battler
        )
        left_opp = battle_state.opponent.left_battler
        right_opp = battle_state.opponent.right_battler
        # ALIVE, not merely present: a FAINTED opponent still has a battler object, and
        # targeting it raises "Cannot attack the left-side opponent Pokémon because
        # there isn't one" — an uncatchable mid-battle mode death (batch runs 01+03,
        # 2026-07-22, both at the same trainer pair once one opponent went down).
        left_alive = left_opp is not None and getattr(left_opp, "current_hp", 0) > 0
        right_alive = right_opp is not None and getattr(right_opp, "current_hp", 0) > 0

        def _default_target(move_index: int):
            if right_alive and not left_alive:
                return TurnAction.use_move_against_right_side_opponent(move_index)
            return TurnAction.use_move(move_index)

        if battler is None:
            return _default_target(0)
        if left_alive:
            move = util.get_strongest_move_against(battler, left_opp)
            if move is not None:
                return TurnAction.use_move(move)
        if right_alive:
            move = util.get_strongest_move_against(battler, right_opp)
            if move is not None:
                return TurnAction.use_move_against_right_side_opponent(move)
        for i, learned in enumerate(battler.moves):
            if learned is not None and util.move_is_usable(learned):
                return _default_target(i)
        # Same PP-only last resort as the single-battle branch above — see the long
        # comment there. Selecting a 0-PP move does NOT make the game Struggle; it
        # prints "There's no PP left for this move!" and re-opens the menu, which in an
        # unfleeable trainer DOUBLE battle (e.g. the Rustboro gym Youngster pair) is the
        # same infinite loop.
        for i, learned in enumerate(battler.moves):
            if learned is not None and learned.pp > 0:
                return _default_target(i)
        return _default_target(0)  # every move truly at 0 PP → the game Struggles

    def which_move_should_be_replaced(self, pokemon, new_move) -> int:
        """Story move-learning policy — keep every Pokémon COMBAT-CAPABLE.

        Called when a Pokémon with 4 moves is about to learn a new one (the stock
        config default `new_move: cancel` would just decline everything, so the
        starter would never improve — hence this override). Returns 0-3 to
        overwrite that slot, or 4 to DECLINE (keep the current moves).

        PRIORITY / RULES (in order):
          1. Never replace an HM move (can't anyway, and Cut/Surf/... are needed
             for field use); never learn a block-listed move.
          2. GUARANTEE combat capability: a damaging move is NEVER replaced by a
             status move, so a Pokémon can't end up with only non-combat moves.
             (Damaging-move count never decreases.)
          3. New STATUS move: accept it only by overwriting an existing (non-HM)
             STATUS slot; if every non-HM slot is a damaging move, DECLINE — don't
             trade attacking power for utility.
          4. New DAMAGING move: (a) upgrade a non-combat/status slot first (pure
             win). Else, among damaging slots, PRESERVE TYPE COVERAGE:
             - if the new move's type is ALREADY covered, only overwrite a WEAKER
               same-type move (a STAB/power upgrade); otherwise DECLINE — don't
               churn or lose a different type for a redundant one;
             - if the new move adds a type we LACK, free a redundant-type slot
               first (so no unique type is lost), else replace the weakest move.

        "Effective power" = base power x (Attack or Sp.Atk) x STAB — the same
        yardstick the stock `learn_best` uses, so choices stay sensible.
        Status-move *utility* ranking (e.g. valuing Sleep Powder over Growl) is a
        future refinement (punch-list #24-team); for now combat moves win."""
        DECLINE = 4
        if new_move.name in context.config.battle.banned_moves:
            return DECLINE

        moves = [lm.move if lm is not None else None for lm in pokemon.moves]

        def is_hm(m):
            return m is not None and m.tm_hm is not None and m.tm_hm.name.startswith("HM")

        def is_damaging(m):
            return m is not None and m.base_power > 0

        def effective_power(m):
            if m is None or not is_damaging(m):
                return 0.0
            if m.type.kind == "Physical":
                stat = pokemon.stats.attack
            elif m.type.kind == "Special":
                stat = pokemon.stats.special_attack
            else:
                stat = 1
            stab = 1.5 if m.type in pokemon.species.types else 1.0
            return m.base_power * stat * stab

        status_slots = [i for i, m in enumerate(moves) if m is not None and not is_damaging(m) and not is_hm(m)]
        damaging_slots = [i for i, m in enumerate(moves) if is_damaging(m) and not is_hm(m)]

        # New STATUS move: only ever replace another status slot (never a
        # damaging move or an HM). If no spare status slot, keep our attacks.
        if not is_damaging(new_move):
            return status_slots[0] if status_slots else DECLINE

        # New DAMAGING move.
        # (a) Overwrite a non-combat slot first — strictly upgrades the kit.
        if status_slots:
            return status_slots[0]
        # Every non-HM slot is now a damaging move; never touch an HM.
        if not damaging_slots:
            return DECLINE
        new_power = effective_power(new_move)
        current_types = [moves[i].type for i in damaging_slots]

        if new_move.type in current_types:
            # Redundant type: only take it to UPGRADE a weaker same-type move;
            # otherwise decline (don't lose a different type for a redundant one).
            weaker_same_type = [
                i for i in damaging_slots
                if moves[i].type == new_move.type and effective_power(moves[i]) < new_power
            ]
            if weaker_same_type:
                return min(weaker_same_type, key=lambda i: effective_power(moves[i]))
            return DECLINE

        # New TYPE coverage: free a redundant-type slot first (keep every unique
        # type), else replace the weakest damaging move.
        type_counts: dict = {}
        for t in current_types:
            type_counts[t] = type_counts.get(t, 0) + 1
        redundant_slots = [i for i in damaging_slots if type_counts[moves[i].type] > 1]
        pool = redundant_slots if redundant_slots else damaging_slots
        return min(pool, key=lambda i: effective_power(moves[i]))

    def should_allow_evolution(self, pokemon, party_index) -> bool:
        # A story auto-completer WANTS its team to evolve — stronger for gyms, and
        # it fixes the Lv-up handler collision the user hit at Treecko Lv16
        # (evolves + learns Pursuit at the same level): with the stock
        # `stop_evolution` default the evolution is force-CANCELLED, and the
        # cancelled-evolution + move-learn handoff can spin without stopping the
        # bot. Letting the evolution COMPLETE runs the well-tested evolve→learn
        # path instead. Always allow (this overrides `stop_evolution` for Story
        # battles). Ties to #24-evo / #24-team.
        return True


class SwapTrainBattleStrategy(LevelUpTravelBattleStrategy):
    """SWAP-TRAINING (user directive 2026-07-21). Level a weak team member by having a
    stronger team-mate secure the KO while the trainee (which was sent out first)
    banks its Gen-3 shared-EXP — no fainting, minimal healing.

    Two triggers, both switching to a team-mate that can SAFELY finish the fight
    (out-levels the foe + healthy), preferring the strongest:

      1. UNDER-LEVELLED — the trainee is >= ``UNDERLEVEL_MARGIN`` levels below the
         foe: switch turn 1, before it takes any damage.
      2. CAN'T CONTINUE — the trainee fought a close-level foe and dropped to low HP
         (or ran out of usable moves): rather than FLEE for zero XP (old behaviour),
         switch so the team-mate finishes and the trainee keeps its XP share; the
         training loop then heals normally. (User: swap instead of flee.)

    If NO team-mate can safely finish, we fall through to the parent — which flees on
    low HP (safe) or solos a same-or-lower foe for FULL XP."""

    #: switch pre-emptively when the trainee is this many levels (or more) below the
    #: foe. Low (2) so it doesn't fight-and-flee winnable-looking-but-losing battles.
    UNDERLEVEL_MARGIN = 2

    def decide_turn(self, battle_state):
        try:
            active = battle_state.own_side.active_battler
            foe = battle_state.opponent.active_battler
            if active is not None and foe is not None:
                util = BattleStrategyUtil(battle_state)
                underleveled = active.level + self.UNDERLEVEL_MARGIN <= foe.level
                # Same tests the parent flees on: too little HP, or no usable move.
                cant_continue = not self._pokemon_has_enough_hp(active) or not any(
                    util.move_is_usable(move) for move in active.moves
                )
                if (underleveled or cant_continue) and util.can_switch():
                    finisher = self._capable_finisher(battle_state, util, foe.level)
                    if finisher is not None:
                        return TurnAction.rotate_lead(finisher)
                    # else: no safe finisher — fall through (parent flees / solos).
        except Exception:
            pass
        return super().decide_turn(battle_state)

    def _capable_finisher(self, battle_state, util, foe_level: int):
        """Party index of the strongest HEALTHY team-mate that can SAFELY finish this
        battle — it can damage the foe and has enough HP (both ensured by
        ``get_potential_rotation_targets``) AND out-levels the foe. ``None`` if none
        qualifies (caller then flees / lets the trainee solo)."""
        from modules.pokemon_party import get_party

        party = get_party()
        safe = [
            i
            for i in util.get_potential_rotation_targets(battle_state)
            if party[i].level >= foe_level
        ]
        if not safe:
            return None
        return max(safe, key=lambda i: (party[i].level, party[i].current_hp))


#: Max map transitions (`region_reach` hops — connections AND warps, 1 each) a TRAINING
#: detour may cost. Local hops (a route next door to the town we're in) pass; far-flung
#: treks do not. A sanity FILTER, never a rank — see _training_area_allowed.
_MAX_TRAINING_TRAVEL_LEGS = 4


def _wild_land_max(map_enum) -> "int | None":
    """Strongest LAND wild level on a map, or None if it has no land table / can't be
    read. Used to judge whether a training patch is fodder for the current team."""
    try:
        from modules.map import get_wild_encounters_for_map

        enc = get_wild_encounters_for_map(*map_enum.value)
        if enc is None or not enc.land_encounters:
            return None
        return max(e.max_level for e in enc.land_encounters)
    except Exception:
        return None


def _party_can_surf() -> bool:
    """Does a party mon actually know Surf? (The field-move gate for the water routes —
    the badge alone is not enough, `map_path.can_surf()` requires the move too.)"""
    try:
        from modules.pokemon_party import get_party as _gp

        return any(
            learned is not None and learned.move.name == "Surf"
            for mon in _gp()
            if mon is not None and not mon.is_egg
            for learned in mon.moves
        )
    except Exception:
        return False


def _training_area_allowed(map_enum, tile, prereq) -> bool:
    """Reachability predicate for `training_areas.best_training_area`.

    TWO gates:
    1. **HM prerequisite** (learned the hard way 2026-07-24) — the richest bands (Routes
       115/118/119/121) sit across water; without Surf actually KNOWN by a party mon they
       are unreachable, and a level-fit-only picker happily proposed Route 121 (past
       Lilycove) to a pre-Surf team.
    2. **Reachable FROM WHERE WE STAND** — a static per-area flag is not enough, because a
       single map can be split into disconnected pieces: Route 111's grass sits NORTH of the
       Go-Goggles desert, so it is reachable from Fallarbor but NOT from Mauville or
       Petalburg (probed: no Mauville-side Route 111 grass exists at all). That question is
       answered by `region_reach.is_map_reachable(..., max_hops=_MAX_TRAINING_TRAVEL_LEGS)`
       — built from the ROM's own MapConnections + warps; a cheap graph search, no emulation.

    ‼ WHY `region_reach` AND NOT `calculate_path` (user decision, 2026-07-25 — KI-24, which
    was fixed for counter-candidate selection first and left open here). Both oracles are
    wrong sometimes; their failure modes are NOT symmetric, and that asymmetry IS the whole
    argument:
      * A wrong **NO** from `calculate_path` is INVISIBLE and costs a whole run. It reads the
        Route 118/119/120 dual-elevation bridges as WALLS (it fails even on a same-map walk
        inside Route 119, y=5 -> y=135), so it calls a genuinely-correct training band
        unreachable. Nothing raises, nothing is logged, the option is simply never proposed,
        and the bot quietly grinds the local fodder patch instead — that is what produced the
        ~2,000,000-frame L3-4 grind in front of Norman.
      * A wrong **YES** from `region_reach` costs ONE wasted walk, which navigation then
        fails RECOVERABLY and loudly. Its `KNOWN_GATES` table holds one hand-verified entry
        (the two Dewford sea edges), so any capability gate not yet tabled reads as passable
        — i.e. it errs toward yes, by construction.
    Cheap-and-visible beats invisible-and-fatal, so the training gate now uses the same
    oracle the counter gate already does (see `_counter_area_allowed`).

    ‼ RESIDUAL RISK, stated plainly: `KNOWN_GATES` MUST GROW. Every gate not yet in it is a
    potential wasted trek. Add an entry whenever a relocation is observed walking into a
    wall, and keep the hop budget small — 4 keeps the same-landmass cluster and cuts the
    far-flung (measured hop counts: tools/story-dev/repro_region_reach.py).

    Fails CLOSED on any error: if the oracle cannot answer, we do not relocate.
    """
    if prereq == "surf" and not _party_can_surf():
        return False
    if prereq not in (None, "surf", "region"):
        return False  # unknown prerequisite → fail closed
    # "region" carries no extra requirement here — it exists so the conservative
    # allow=None default refuses the area; the live reachability check below is its gate.
    try:
        from modules.map import get_map_data_for_current_position
        from modules.story import region_reach

        here = tuple(get_map_data_for_current_position().map_group_and_number)
        target = tuple(map_enum.value)
        if here == target:
            # Already on the map — nothing to travel, so nothing to prove. Deliberately NOT
            # tile-checked with `calculate_path`: it is unsound even WITHIN one map on the
            # bridge maps, so a "last mile" check here would re-import the exact false
            # negative this predicate just stopped trusting.
            return True
        return bool(region_reach.is_map_reachable(map_enum, max_hops=_MAX_TRAINING_TRAVEL_LEGS))
    except Exception:
        return False


#: Hop budget for COUNTER-CATCH candidates (`_counter_area_allowed`).
#: ‼ 8, RAISED FROM 4 ON MEASUREMENT (2026-07-26). From the real pre-Norman anchor
#: (`saves/prenorman_fodder_grind.ss1`, Route 102, party avg L27) every Fighting-counter
#: map sits at 5-7 hops — FIERY_PATH 7, JAGGED_PASS 7, GRANITE_CAVE_1F 5 — so a bound of
#: 4 admitted only the NEAREST one and excluded the cheap ones. That is the
#: encounter-rate error again: a proximity proxy overriding measured cost.
#: The arithmetic: reaching FIERY_PATH costs ~3 hops more walking than GRANITE_CAVE, and
#: even at a generous ~5,000 frames per map crossing that is ~15,000 frames — against a
#: **174,000-frame** difference in training cost (Makuhita 363,982 vs Machop 190,589).
#: The filter was off by an order of magnitude against its own purpose.
#: WHY 8 AND NOT MORE, measured from the same anchor: 8 admits FIERY_PATH/JAGGED_PASS (7)
#: and MT_PYRE (8) while still excluding SAFARI_ZONE (10-11) — a paid, step-limited
#: minigame area the bot cannot farm — and PACIFIDLOG (10 from ROUTE120), which is what
#: the original bound existed to cut. Maps admitted from this anchor: 4 -> 52, 6 -> 123,
#: 8 -> 175, 10 -> 226.
#: Safe to loosen only because two other guards now exist: candidates are ranked by
#: measured COST (so a far map must also be cheap to win), and `_training_unreachable`
#: bounds a wrong YES to one wasted walk instead of the run.
#: ‼ Travel cost is still NOT in the cost model — no measured frames-per-hop figure
#: exists in this codebase. Add one and fold it in, then this bound can go away.
COUNTER_MAX_HOPS = 8


def _counter_area_allowed(map_enum, tile, prereq) -> bool:
    """`allow=` predicate for `counter_plan.find_counter_candidates`, used ONLY from
    `_boss_plan_is_hopeless`'s counter-catch wiring (KI-23 -> #24-counters).

    Deliberately NOT `_training_area_allowed`: that predicate's same-region test is
    tile-level `calculate_path`, which reads the Route 118/119/120 dual-elevation
    bridges as WALLS and therefore reported Route 118 — the real Winona answer — as
    unreachable (KI-24). `region_reach.is_map_reachable` answers reachability from the
    ROM's own MapConnections + warps instead, which is sound at region scale.

    ‼ `max_hops` RAISED 4 -> 8 (2026-07-26, measured — see `COUNTER_MAX_HOPS`). At 4 the
    filter was excluding the CHEAP counters and admitting an expensive one purely because
    it sat nearer, which is the encounter-rate mistake wearing a different hat.

    The original note, still true about what the bound is FOR:
    a documented sanity FILTER, not a rank: measured hops from
    ROUTE120 are Fortree 1, Route119 2, Lilycove 2, Route118 3, Mossdeep 4,
    Pacifidlog 10 — 4 keeps the same-landmass cluster and cuts the far-flung.
    Hop count must NOT be used to rank; `counter_plan`'s own criteria (type coverage
    -> verified tile -> encounter rate -> level fit) do that (KI-24b). Fails safe:
    any oracle error is treated as unreachable, never lets an exception escape.
    """
    try:
        from modules.story import region_reach

        return bool(region_reach.is_map_reachable(map_enum, max_hops=COUNTER_MAX_HOPS))
    except Exception:
        return False


def _counter_catch_message(cfg: dict, losses: int, needed: list[str]) -> str:
    """Builds the `BotModeError` message for a hopeless boss plan (KI-23 -> #24-counters):
    the type-only diagnosis PLUS, if the counter-catch planner can name one, a concrete
    catch target (species + map + tile + level band) rather than just a type list.

    Connects the three previously-standalone pieces: `_boss_plan_is_hopeless` (the
    diagnosis) -> `counter_plan.find_counter_candidates` (ranks catch targets) ->
    `region_reach.is_map_reachable` (the reachability oracle, via `_counter_area_allowed`).
    PLANNING/LOGGING ONLY — this does not travel, catch, or train anything.

    Fails SAFE throughout: if the planner or the reachability oracle errors or returns
    nothing, this falls back to the type-only message. A crash here would turn a
    diagnosed stop into an undiagnosed one, which is strictly worse.
    """
    boss_name = cfg.get("name", "this boss")
    ace_desc = "/".join(cfg.get("ace_types", ())) or "its ace type(s)"
    base_msg = (
        f"{boss_name}: {losses} losses with no super-effective answer to "
        f"{ace_desc}. Need one of: {', '.join(needed)}. Grinding levels "
        f"will not fix this."
    )
    try:
        from modules.story import counter_plan

        candidates = counter_plan.find_counter_candidates(
            needed, allow=_counter_area_allowed, max_results=5
        )
        if candidates:
            summary = counter_plan.summarise_candidates(candidates)
            # Full list to the debug log FIRST — it must land even if the raised
            # message ends up truncated somewhere downstream.
            console.print(
                f"[bold cyan]Story: counter-catch candidates for {boss_name} "
                f"({ace_desc}):[/]\n{summary}"
            )
            base_msg += " Nearest reachable counters: " + summary.replace("\n", "; ")
    except Exception as error:
        console.print(
            f"[yellow]Story: counter-catch planner failed ({error}) — "
            f"falling back to the type-only diagnosis.[/]"
        )
    return base_msg


#: Where to heal while training in each area. Training far from the boss's own Poké Center
#: means the heal trips must be LOCAL to the training ground, or the bot walks the region
#: every time HP dips (the cave-heal lesson, 2026-07-22). Unlisted areas fall back to the
#: boss's configured centre.
def _training_area_heal_map() -> dict:
    from modules.map_data import MapRSE, PokemonCenter

    return {
        MapRSE.ROUTE101: PokemonCenter.OldaleTown,
        MapRSE.ROUTE102: PokemonCenter.PetalburgCity,
        MapRSE.ROUTE103: PokemonCenter.OldaleTown,
        MapRSE.ROUTE116: PokemonCenter.RustboroCity,
        MapRSE.ROUTE117: PokemonCenter.VerdanturfTown,
        MapRSE.ROUTE110: PokemonCenter.MauvilleCity,
        # ‼ Fallarbor, NOT Mauville: Route 111's training tile is NORTH of the
        # Go-Goggles desert. Verified 2026-07-24 — Fallarbor is the ONLY Poké Center
        # reachable from that tile.
        MapRSE.ROUTE111: PokemonCenter.FallarborTown,
        MapRSE.ROUTE112: PokemonCenter.LavaridgeTown,
        # FIERY_PATH is a counter-hunting ground (Machop, the Norman answer). Its south
        # door is Route 112 (11,36), so Lavaridge is the natural heal — and it is the same
        # side `_CAVE_EXITS` surfaces the bot on, so the heal trip is a short walk rather
        # than a trek around the mountain.
        MapRSE.FIERY_PATH: PokemonCenter.LavaridgeTown,
        MapRSE.ROUTE113: PokemonCenter.FallarborTown,
        MapRSE.ROUTE114: PokemonCenter.FallarborTown,
        MapRSE.ROUTE115: PokemonCenter.RustboroCity,
        MapRSE.ROUTE118: PokemonCenter.MauvilleCity,
        # ⚠ ROUTE119/121 pairings are UNVALIDATED: both areas are Surf-gated, so no
        # pre-Surf save can path from their tiles to any Poké Center (verified: Route 119
        # (21,109) reaches NONE). Re-verify from a post-Surf checkpoint before trusting
        # these — the repro skips them for exactly this reason.
        MapRSE.ROUTE119: PokemonCenter.FortreeCity,
        MapRSE.ROUTE121: PokemonCenter.LilycoveCity,
    }


class StoryMode(BotMode):
    #: OPT IN to the battle-handler fault channel (#24-movelearn-recovery, 2026-07-25).
    #: A sub-handler that gives up (e.g. an unanswerable move-learn offer) records the
    #: fault via `modules.battle_fault` instead of raising across the controller stack
    #: into `main_loop` — which would drop the run to Manual, outside our recovery. We
    #: re-raise it inside run()'s try below, so it costs a DERAIL, not the whole run.
    #: This attribute is the promise that we consume it; nothing else may set it
    #: without also calling `take_pending_fault()` on every frame it holds control.
    handles_battle_faults = True

    #: Pre-gym training only readies a battler that's already within this many levels
    #: of the target band; fresh catches further below are left to level organically
    #: rather than grinding them up via half-XP swap-training (user 2026-07-21).
    TRAIN_CATCHUP_GAP = 6

    #: A boss's LOCAL grass counts as FODDER — worth relocating away from, or skipping
    #: entirely — once its strongest wild is this far below the team's best mon.
    #: ‼ Deliberately MORE conservative (12) than the reactive boss-training check (8):
    #: this fires PROACTIVELY, before any loss, so it must not disturb prep that already
    #: works. At 12 it stays silent for Roxanne (R116 L8 vs ~L17) and Wattson (R117 L14
    #: vs ~L24) — both validated across many runs — and fires for the pathological case
    #: it exists for: NORMAN, whose local patch is Route 102 at L4 against a L27-31 team
    #: (~25 xp a kill, i.e. never). User-reported 2026-07-24.
    FODDER_LEVEL_GAP = 12

    #: Frame budget for a SINGLE targeted grind decision (evo-lookahead or sweeper top-up) —
    #: ~3 minutes of emulator time, derived from the MEASURED FRAMES_PER_WILD_BATTLE (1433,
    #: see modules/story/training_areas.py) — roughly 174 wild battles' worth of budget.
    #: Both decisions used to be budgeted purely in LEVELS, but frames-per-level varies
    #: enormously with where you grind: a fresh run's evo-lookahead sent a L33 Combusken to
    #: Route 102's L3-5 wilds for 3 levels (~430,000 frames, measured) and helped blow the
    #: run's overall frame cap one level short. This constant is what lets that plan be
    #: REJECTED up front instead of committed to blind (punch-list #24).
    MAX_PREP_TRAINING_FRAMES = 250_000

    #: How many times to (re)train + attempt the Rustboro rival before giving up and handing
    #: to manual — bounds the whiteout→retrain loop so an underleveled/bad-matchup team can't
    #: spin forever (each attempt escalates the training band via `_prepare_for_fight`).
    RIVAL_MAX_ATTEMPTS = 3

    #: KI-23 (Winona): losses to the SAME boss before `_boss_plan_is_hopeless` will even
    #: consider calling the plan unwinnable. The observed failure ran to 41 losses (198
    #: attempts) grinding levels a Grass/Normal/Dark/Bug-Flying team could never spend on
    #: Flying; 6 is enough to separate bad luck from a wrong plan while costing far less
    #: than 41 whiteout cycles before we say so.
    PLATEAU_LOSS_THRESHOLD = 6

    #: Defeats on ONE map (this run) after which wild battles there are fled rather than
    #: fought — see the SURVIVAL MODE block in `on_battle_started`. 3, not 6: the boss
    #: threshold can afford patience because a lost boss attempt still banks EXP (Gen 3
    #: keeps mid-battle EXP through a whiteout), whereas a travel wipe banks almost
    #: nothing and costs the whole walk back from the respawn Poké Center. Measured
    #: worst case before this existed: **25 whiteouts on ROUTE110 in a single run**.
    SURVIVAL_WHITEOUT_THRESHOLD = 3

    #: Minimum EFFECTIVE power (base power x type effectiveness x STAB) for a move to
    #: count as a real answer to a boss's ace type in `_boss_plan_is_hopeless`.
    #: ‼ WITHOUT THIS THE DETECTOR IS POWER-BLIND AND SILENTLY DISABLES ITSELF ON
    #: NORMAN (measured, night5 run3, 2026-07-25). Norman's team is all NORMAL, and the
    #: only type super-effective against Normal is FIGHTING — so the party's sole
    #: "answer" was **Rock Smash**, the 20-base-power HM the bot is REQUIRED to carry to
    #: progress at all. 20 x 2.0 x 1.0 = 40: super-effective on paper, useless against a
    #: L31 Slaking. The old `eff >= 2.0` test accepted it, declared the plan not
    #: hopeless, and let the run make **27 losing attempts over 508,000 frames** with
    #: KOs flat at 1-2 of 4 the entire time. The boss most likely to plateau was the one
    #: the guard could never fire on.
    #: ‼ RAISED 60 -> 75 on measured evidence (batch 20260726-052205 run05). 60 was
    #: calibrated against Rock Smash on a NON-Fighting carrier (20 x 2.0 x 1.0 = 40) and
    #: missed the STAB case: **Combusken is Fire/FIGHTING**, so its Rock Smash scores
    #: 20 x 2.0 x 1.5 = **exactly 60** and passed on the boundary. The guard stayed
    #: silent and that run took **21 Norman losses** — the same failure the threshold
    #: exists to prevent, arriving through STAB instead of raw power.
    #: The two measured points bracket it: 60 (Combusken + Rock Smash) demonstrably does
    #: NOT beat Norman; 90 (Combusken + Double Kick) demonstrably does. 75 sits between
    #: them and still keeps ordinary answers — a plain 40-power super-effective move
    #: (80), Surf off a Water mon (95 x 2.0 x 1.5 = 285), Thunderbolt vs Winona (270).
    #: ‼ Do NOT "fix" this by excluding HM moves categorically: Surf/Strength/Waterfall
    #: are real attacking moves and are often the bot's best answer. Only Rock Smash and
    #: Cut are weak enough to be the problem, and the power floor already handles them.
    CREDIBLE_ANSWER_POWER = 75

    #: How many distinct counter DESTINATIONS one ladder invocation may try before giving
    #: up. Each rejected destination costs only a fail-fast navigation (~255 frames
    #: measured), so a small fallback list is nearly free — and it is necessary: driven
    #: navigation on 2026-07-30 showed the TOP huntable destination unreachable for two of
    #: the three measured bosses. Bounded because the ladder must terminate; the expensive
    #: failure (arrived, caught nothing) deliberately does NOT consume one of these.
    COUNTER_HUNT_MAX_DESTINATIONS = 3

    @staticmethod
    def name() -> str:
        return "Story"

    @staticmethod
    def is_selectable() -> bool:
        # Story mode can start from the title screen (fresh game) or in-game,
        # so it is always offered; run() sorts out which path applies.
        return True

    @staticmethod
    def is_selectable_from_title_screen() -> bool:
        # Unlike stock modes, Story Mode is MEANT to start at the title/main
        # menu — that's where it runs the New Game intro.
        return True

    def __init__(self):
        super().__init__()
        self.reset_per_run_state()

    def reset_per_run_state(self) -> None:
        """Clear every counter whose meaning is scoped to ONE playthrough.

        ‼ WHY THIS IS A METHOD AND NOT JUST `__init__` (real failure, user's x4 bundle
        `20260726-231412`). All of this state used to be assigned directly in `__init__`,
        under a comment that claimed "Instance state, not module state, so ENDLESS RESET's
        next run starts with a clean slate." **That was false.**
        `StoryEndlessResetMode.run()` loops `yield from super().run()` on the SAME mode
        object, so `__init__` runs once per BATCH — the counters accumulated across every
        run of an overnight batch. Two measured consequences:

          * `_rival_attempts` (cap 3) reached its cap after 3 runs, so **run 4 onward died
            at the Rustboro rival without ever fighting it** — P1 run 8's debug log contains
            ZERO `BattleOutcome.Lost` yet the run ended "couldn't beat the Rustboro rival in
            3 tries". It killed 16 of 20 P1 runs, 6 of 9 P2 runs, 5 of 8 P3 runs.
          * `_defeat_counts` carried each run's losses into the next, so the "give up on this
            boss" threshold tripped on borrowed losses: MT_CHIMNEY went `#7`(run 1) → `#8`
            (run 2), FORTREE_GYM `#8`(run 1) → `#9`(run 3), and P4 run 2 derailed as
            "6 losses" to Wattson after only THREE real losses that run.

        PREVENTION RULE: per-run state goes in here, never in `__init__`, and the endless
        loop calls this at the top of every run. A comment asserting a lifetime is not a
        mechanism that enforces it.
        """
        # DEFEAT RECOVERY (user directive 2026-07-21). Consecutive losses are counted
        # per LOCATION (map) so repeated faints at the same obstacle mean a power/level
        # problem → trigger a retrain. These survive whiteout restarts within a run,
        # because run() loops in place (it does NOT bounce through Manual).
        # Training grounds proven unreachable FROM a given standing map, this run
        # (#24-regionreach, 2026-07-25). Keyed (here_map, target_map, tile) because
        # reachability is directional and positional: Route 111's grass is genuinely
        # reachable from Fallarbor and genuinely not from Mauville, so a flat blacklist
        # would throw away a good area for the rest of the run.
        self._training_unreachable: set = set()
        self._defeat_counts: dict = {}
        self._loss_ko_history: dict = {}  # map key -> [(seq, opponent KOs) per lost attempt]
        self._loss_seq: int = 0
        self._whiteout_pending = False
        self._last_defeat_key = None
        self._derails = 0  # consecutive non-whiteout derails (self-correct before Manual)
        self._last_derail_sig = None  # progress fingerprint at the last derail (see run())
        # Boss/rival attempt caps. These are PER-RUN budgets: a thin team that cannot win
        # stops cleanly instead of looping forever, but the NEXT run must start fresh.
        self._rival_attempts = 0
        # Set only by the genuine end-of-built-content return, so the endless loop can tell
        # a real completion from a give-up — both hand to Manual and return normally.
        self._reached_end_of_content = False
        # Nudge debounce for the Ki15 wedge (see run()); positional, so per-run.
        self._ki15_nudge_stable = 0
        self._ki15_nudge_pos = None
        # Organic team-building (user directive 2026-07-21): catch NEW species while
        # travelling to Gym 1 until the party has this many members (starter + helpers).
        self._catch_team_target = 4
        # #24-counters phase 2: boss key -> what the counter hunt did, ONE entry per boss
        # per run. This dict IS the bound (see `_counter_ladder`) — a retry or frame
        # budget cannot bound it, because `_prepare_for_fight` is re-entered by the run
        # loop after every lost attempt, which turns any per-call budget into a per-attempt
        # one. Per-RUN by construction, so the next run gets a fresh chance.
        self._counter_hunts: dict = {}
        # A hunt that was interrupted mid-flight (whiteout, derail) must not leave the
        # catch-on-sight targets armed for the rest of the run.
        try:
            from modules.story import counter_hunt as _ch

            _ch.disarm()
        except Exception:
            pass

    def on_battle_ended(self, outcome) -> None:
        from modules.battle_state import BattleOutcome

        if outcome is BattleOutcome.Lost:
            key = self._location_key()
            self._defeat_counts[key] = self._defeat_counts.get(key, 0) + 1
            self._last_defeat_key = key
            # BOSS-TRAINING telemetry (user design 2026-07-23): how many of the
            # opponent's mons did we KO before losing? Read from the game's own
            # battle-results struct (gBattleResults.opponentFaintCounter, offset 1 —
            # decomp include/battle.h). Gen 3 keeps the XP from those KOs through
            # the whiteout, so a lost boss attempt with KOs is real training — the
            # prep logic uses this to decide "keep re-attempting" vs "grind grass".
            kos = 0
            try:
                from modules.memory import read_symbol

                kos = read_symbol("gBattleResults", offset=0x01, size=1)[0]
            except Exception:
                pass
            self._loss_seq += 1
            self._loss_ko_history.setdefault(key, []).append((self._loss_seq, kos))
            console.print(
                f"[yellow]Story: lost a battle at map {key} "
                f"(defeat #{self._defeat_counts[key]} here; KO'd {kos} of theirs first).[/]"
            )

    def on_whiteout(self) -> bool:
        # We handle the whiteout ourselves — do NOT drop to Manual (and the watchdog
        # is hands-off for Story, so no save-state reload). Flag an abort so the
        # running segment bails out promptly; run() then re-orients from the respawn
        # Poké Center and resumes the segmented playthrough from where we left off.
        from modules.story.early_game import set_story_abort

        self._whiteout_pending = True
        set_story_abort(True)
        console.print(
            "[bold yellow]Story: whited out — recovering (navigating the respawn and "
            "resuming from where I left off; no save-state reload).[/]"
        )
        return True

    def _location_key(self):
        try:
            from modules.map import get_map_data_for_current_position

            d = get_map_data_for_current_position()
            return (d.map_group, d.map_number)
        except Exception:
            return None

    def defeat_count_at(self, location_key) -> int:
        return self._defeat_counts.get(location_key, 0)

    def _progress_sig(self):
        """A MONOTONIC fingerprint of story progress from the PARTY structure:
        size, lead level, and total accumulated EXP. These only ever move forward
        and — unlike event flags, which flicker while read during a battle→overworld
        transition — read reliably at any moment. run() compares it across derails
        to tell a transient hiccup mid-progress (a battle finished, a level or a
        Pokémon was gained → reset the derail budget) from a truly stuck loop
        (nothing advances → escalate to Manual). Deliberately excludes flags so a
        flickering flag can never fake progress and mask a genuine freeze."""
        try:
            from modules.pokemon_party import get_party

            party = get_party()
            lead_level = party[0].level if party else 0
            total_exp = sum(getattr(p, "total_exp", 0) for p in party)
            return (len(party), lead_level, total_exp)
        except Exception:
            return None

    def _log_localization(self, note: str) -> None:
        """Report WHERE WE ARE — story stage (from the flag-based detector) + physical
        map — so a derail is diagnosable and self-correction is visible, instead of a
        silent drop to Manual (user directive 2026-07-21)."""
        try:
            from modules.story import detect_live

            prog = detect_live()
            stage = f"{prog.chapter_key}: {prog.chapter_name}"
        except Exception:
            stage = "unknown stage"
        console.print(f"[yellow]Story localization — {note} | stage: {stage} | map {self._location_key()}[/]")

    def _should_catch(self, encounter) -> bool:
        """Pre-Gym-1 organic team-building (user directive 2026-07-21): catch a wild
        of a NEW species (never a dup we've already caught, never one already in the
        party) while there's room in the party. Only before the first gym, only once
        we have the Pokédex + Poké Balls. Shinies return False here only because the
        SHINY branch in on_battle_started pre-empts this entirely (always-catch, user
        directive 2026-07-22) — this filter is for ordinary team-building catches."""
        try:
            from modules.memory import get_event_flag
            from modules.pokemon_party import get_party
            from modules.pokedex import get_pokedex
            from modules.items import get_item_bag

            if encounter is None:  # trainer battle — never "catch"
                return False
            if getattr(encounter, "is_shiny", False):
                return False
            if get_event_flag("BADGE01_GET"):  # only before the first gym
                return False
            if not get_event_flag("RECEIVED_POKEDEX_FROM_BIRCH"):  # need balls + dex
                return False
            # RESOURCE-AWARE (planning doc §3): never ATTEMPT a catch without balls —
            # that's what broke the bot. Keep 1 in reserve; the catch phase restocks
            # (buys) or stops gracefully. Fight the wild instead when out of balls.
            if sum(s.quantity for s in get_item_bag().poke_balls) <= 1:
                return False
            party = [p for p in get_party() if p is not None and not p.is_egg]
            if len(party) >= self._catch_team_target:
                return False
            species = getattr(getattr(encounter, "pokemon", None), "species", None)
            if species is None:
                return False
            # Species objects aren't hashable — compare by national dex number.
            owned = {s.national_dex_number for s in get_pokedex().owned_species}
            party_dex = {p.species.national_dex_number for p in party}
            dex = species.national_dex_number
            return dex not in owned and dex not in party_dex
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Sweeper-sufficiency gate (user directive 2026-07-23; two-agent Gemini
    # consult archived in tools/story-dev/research-gemini-sufficiency-consult-*).
    # The proactive band prep over-trains whenever one mon already beats the gym
    # (the user's Combusken-L20-vs-Roxanne case). The gate asks, from data a
    # faithful player also has: "do we have a sweeper?" — and only trains when
    # the answer is no (or nearly-yes: a targeted top-up). The REACTIVE net
    # (loss escalation + boss-training) stays the correctness guarantee, so a
    # wrong 'sufficient' call costs 1-2 self-correcting losses, not a run.
    # ------------------------------------------------------------------
    SWEEP_SCORE_FLOOR = 80  # BP x STAB x pair-effectiveness (consult: Mud Shot 82, Double Kick 90)

    # Gen 3: damage category is decided BY TYPE, not by move. A high-BP move off
    # the mon's WEAK attacking stat is a mirage (the Poochyena-Bite trap: Dark is
    # SPECIAL and Poochyena's SpA is dreadful — BPxSTABxeff alone scores it 90).
    _PHYSICAL_TYPES = frozenset(
        {"Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel"}
    )

    @classmethod
    def _sweep_score(cls, mon_types, moves, ace_types, atk=None, spa=None) -> float:
        """Best damage-potential among usable damaging moves vs the ACE's full type
        pair: BP x 1.5 STAB x product-effectiveness x stat-fit. Ace pair, not gym
        primary — Altaria/Kingdra-class aces defeat primary-type reasoning. Stat-fit
        scales a move by (relevant attacking stat / better attacking stat), so a
        special-typed move on a physical attacker scores what it actually hits for."""
        best = 0.0
        for learned in moves:
            if learned is None or learned.pp == 0 or learned.move.base_power == 0:
                continue
            eff = 1.0
            for t in ace_types:
                eff *= learned.move.type.get_effectiveness_against(t)
            stab = 1.5 if any(t.index == learned.move.type.index for t in mon_types) else 1.0
            fit = 1.0
            if atk and spa:
                relevant = atk if learned.move.type.name in cls._PHYSICAL_TYPES else spa
                fit = relevant / max(atk, spa)
            best = max(best, learned.move.base_power * stab * eff * fit)
        return best

    def _sufficiency_verdict(self, cfg: dict):
        """(kind, slot, level) — kind: 'sufficient' (skip prep), 'topup' (train ONE
        mon to `level`), or None (no sweeper in sight — band-prep as always)."""
        from modules.pokemon import get_species_by_index, get_type_by_name
        from modules.pokemon_party import get_party
        from modules.story.early_game import _battler_slots

        if "ace_types" not in cfg or cfg.get("double"):
            return None  # rivals/mixed fights + double battles: always band-prep
        try:
            ace_types = [get_type_by_name(n) for n in cfg["ace_types"]]
        except Exception:
            return None
        ace_level = cfg.get("ace_level", cfg["band"][1])
        need_level = ace_level - 1
        party = get_party()
        best = None  # (priority, -score, slot, kind, train_to)

        def _vulnerable(defender_types) -> bool:
            """Defensive veto (consult): a sweeper the ACE hits super-effectively is
            a coin-flip, not a plan — the Swellow-vs-Wattson trap."""
            for at in ace_types:
                eff = 1.0
                for t in defender_types:
                    eff *= at.get_effectiveness_against(t)
                if eff >= 2.0:
                    return True
            return False

        for i in _battler_slots():
            mon = party[i]
            try:
                mon_types = mon.species.types
            except Exception:
                continue
            entry = None
            if not _vulnerable(mon_types):
                atk = spa = None
                try:
                    atk, spa = mon.stats.attack, mon.stats.special_attack
                except Exception:
                    pass
                score = self._sweep_score(mon_types, mon.moves, ace_types, atk, spa)
                if score >= self.SWEEP_SCORE_FLOOR:
                    if mon.level >= need_level:
                        entry = (0, -score, i, "sufficient", None)
                    elif mon.level >= need_level - 2:
                        entry = (1, -score, i, "topup", need_level)  # close: top up JUST this mon
            if entry is None:
                # Imminent-threshold lookahead (the user's Torchic case): if this mon
                # EVOLVES within +3 levels and the EVOLVED FORM — judged on ITS types
                # (Torchic is Rock-weak and rightly vetoed; Combusken is Rock-neutral)
                # and its level-up moves by that level (Double Kick on evolution) —
                # would qualify, grind JUST this mon to the evolution level.
                try:
                    for evo in mon.species.evolutions:
                        if "LEVEL" not in str(evo.method).upper():
                            continue
                        evo_level = int(evo.method_param)
                        if not (mon.level < evo_level <= mon.level + 3):
                            continue
                        evolved = get_species_by_index(evo.target_species_index)
                        if _vulnerable(evolved.types):
                            continue
                        future = [
                            SimpleNamespace(move=e.move, pp=1)
                            for e in evolved.learnset.level_up
                            if e.level <= evo_level
                        ]
                        e_atk = e_spa = None
                        try:
                            e_atk = evolved.base_stats.attack
                            e_spa = evolved.base_stats.special_attack
                        except Exception:
                            pass
                        if self._sweep_score(evolved.types, future, ace_types, e_atk, e_spa) >= self.SWEEP_SCORE_FLOOR:
                            # FRAME-COST GATE (punch-list #24): `mon.level < evo_level <=
                            # mon.level + 3` above budgets in LEVELS, but the real cost is
                            # FRAMES — a fresh run's local grass was Route 102 L3-5 wilds,
                            # measured at 1433 frames/battle, and 3 "close" levels there
                            # cost ~430,000 frames. Estimate before committing to the plan;
                            # an unknown or over-budget estimate REJECTS it (fail safe).
                            from modules.story.training_areas import estimate_frames_to_level

                            wild_level = _wild_land_max(cfg["grass"][0]) if "grass" in cfg else None
                            est_frames = (
                                estimate_frames_to_level(mon, evo_level, wild_level)
                                if wild_level is not None
                                else None
                            )
                            if est_frames is None or est_frames > self.MAX_PREP_TRAINING_FRAMES:
                                console.print(
                                    f"[yellow]Story: evo-lookahead for {mon.species.name} -> "
                                    f"Lv{evo_level} rejected — estimated "
                                    f"{est_frames if est_frames is not None else 'UNKNOWN'} frames "
                                    f"exceeds budget ({self.MAX_PREP_TRAINING_FRAMES}).[/]"
                                )
                                continue
                            entry = (2, 0.0, i, "topup", evo_level)
                            break
                except Exception:
                    pass
            if entry is not None and (best is None or entry < best):
                best = entry
        if best is None:
            return None
        _prio, _negscore, slot, kind, train_to = best
        return (kind, slot, train_to)

    # ------------------------------------------------------------------
    # KI-23 — boss-training-mode plateau detector (Winona overnight run: 198
    # attempts, 41 losses, 41 whiteouts, never won; L42 Sceptile/L39 Loudred/
    # L36 Mightyena team had NO super-effective answer to Flying — Sceptile is
    # resisted, Ninjask is part-Flying itself, Shedinja is 1 HP — so grinding
    # more levels could never converge). Boss-training mode's existing "2
    # consecutive zero-KO attempts" guard never fires here because a strong
    # mon scores 1-2 KOs every time and still loses forever; this adds a
    # second, independent signal that catches exactly that case.
    # ------------------------------------------------------------------
    def _boss_plan_is_hopeless(self, cfg: dict) -> tuple[bool, list[str]]:
        """(hopeless, needed_type_names). True only when BOTH hold: (1) losses here have
        plateaued — the best KO count in the most recent 3 losses is not better than the
        best in the 3 before that — and (2) no battle-capable party mon has a damaging
        move that hits the boss's `ace_types` for >= 2.0 effectiveness. `needed_type_names`
        lists the attacking types that WOULD be super-effective, computed from the real
        type chart, never hardcoded. Fails safe: any read error returns (False, []) — a
        reader hiccup must never abort a fight."""
        try:
            losses = max((self._defeat_counts.get(k, 0) for k in cfg["keys"]), default=0)
            if losses < self.PLATEAU_LOSS_THRESHOLD:
                return False, []

            # --- plateau test: best-of-recent-3 losses vs. best-of-previous-3 ---
            history = sorted(entry for k in cfg["keys"] for entry in self._loss_ko_history.get(k, ()))
            if len(history) < 6:
                return False, []  # not enough history to call it — never guess
            recent_best = max(kos for _seq, kos in history[-3:])
            previous_best = max(kos for _seq, kos in history[-6:-3])
            if recent_best > previous_best:
                return False, []  # improving — the existing escalation path is working

            # --- no-answer test: does any battler have a super-effective damaging move? ---
            if "ace_types" not in cfg:
                return False, []
            from modules.pokemon import _types_by_name, get_type_by_name
            from modules.pokemon_party import get_party
            from modules.story.early_game import _battler_slots

            ace_types = [get_type_by_name(n) for n in cfg["ace_types"]]
            party = get_party()
            battlers = _battler_slots()
            if not battlers:
                return False, []
            for i in battlers:
                # STAB needs the carrier's own types; the decision repros pass
                # lightweight stand-ins with no `species`, so treat that as "no STAB"
                # rather than letting an AttributeError abort the whole diagnosis.
                try:
                    own_types = tuple(party[i].species.types)
                except Exception:
                    own_types = ()
                for learned in party[i].moves:
                    if learned is None or learned.pp == 0 or learned.move.base_power == 0:
                        continue
                    eff = 1.0
                    for t in ace_types:
                        eff *= learned.move.type.get_effectiveness_against(t)
                    if eff < 2.0:
                        continue
                    # ‼ SUPER-EFFECTIVE IS NOT THE SAME AS SUFFICIENT. Weight by real
                    # power before accepting it as an answer — a 20-power HM is 2.0x
                    # against Normal and still loses to Slaking 27 times running
                    # (see CREDIBLE_ANSWER_POWER). Being generous here does not make
                    # the bot try harder; it makes the bot never notice it is stuck.
                    stab = 1.5 if learned.move.type in own_types else 1.0
                    if learned.move.base_power * eff * stab >= self.CREDIBLE_ANSWER_POWER:
                        return False, []  # we DO have a credible answer — not hopeless

            # No answer in the party: work out what WOULD be super-effective by asking
            # the type chart directly (never hardcode a type-matchup table).
            needed = []
            for atk_name, atk_type in _types_by_name.items():
                eff = 1.0
                for t in ace_types:
                    eff *= atk_type.get_effectiveness_against(t)
                if eff >= 2.0:
                    needed.append(atk_name)
            return True, needed
        except Exception as error:
            # ‼ THIS `except` FAILS TOWARD "KEEP GRINDING FOREVER". Returning
            # "not hopeless" is the safe answer for a crash, but it is also exactly
            # what a WORKING detector returns — so a bug in here is indistinguishable
            # from a healthy boss plan and costs ~19,000 frames per losing attempt,
            # silently, forever. Caught once already: a stand-in `self` missing a class
            # constant swallowed an AttributeError and disabled the whole diagnosis.
            # Never let it be silent again.
            console.print(
                f"[yellow]Story: boss-plateau detector errored ({error!r}) — treating "
                f"the plan as viable, but this guard is NOT protecting the run.[/]"
            )
            return False, []

    def _counter_ladder(self, cfg: dict, losses: int, needed: list) -> Generator:
        """#24-counters phase 2 — ACT on a hopeless boss diagnosis. Yields as it works;
        returns True if it changed the party's answer to this boss, False to fall through
        to the honest terminal raise.

        THE BOUND, and why it is shaped this way. The hunt runs **once per boss per run**.
        That is not timidity — it is the only bound that actually terminates:

          * A retry budget would not work. The chain fires from inside `_prepare_for_fight`,
            which the run loop re-enters after every lost attempt, so "N tries" becomes N
            per re-entry, i.e. unbounded. (KI-34 burned 23.9M frames on exactly this shape:
            a bounded loop re-entered by its dispatcher is still infinite.)
          * A frame budget would not work either, for the same reason.

        So the bound is on the OUTCOME and recorded in per-run state: this boss gets one
        hunt, and whatever happens, the next hopeless verdict here falls straight through
        to the raise. `14-AGENT-PLAYBOOK.md` rule 3.

        ‼ The catch is only half the job — see `counter_hunt.train_counter`. Catching a
        L15 Machop for a L30 team and leaving it untrained would make
        `_boss_plan_is_hopeless` answer "not hopeless" for ever after (the party now has a
        Fighting move), converting this bounded stop into an unbounded loop.
        """
        from modules.story import counter_hunt, counter_plan
        from modules.story.early_game import UnreachableDestinationError

        key = tuple(cfg["keys"])[0] if cfg.get("keys") else cfg.get("name", "boss")
        if key in self._counter_hunts:
            console.print(
                f"[yellow]Story: already hunted a counter for {cfg.get('name', 'this boss')} "
                f"this run ({self._counter_hunts[key]}) — not trying again; stopping honestly.[/]"
            )
            return False
        # Record the attempt BEFORE doing any of it. If the hunt derails mid-way (a
        # whiteout, a navigation failure), the run recovers and re-enters here — and
        # without this the "once per run" bound would never be written down.
        self._counter_hunts[key] = "started"

        try:
            candidates = counter_plan.find_counter_candidates(
                needed, allow=_counter_area_allowed, max_results=10
            )
        except Exception as error:
            console.print(f"[yellow]Story: counter planner failed ({error!r}) — stopping honestly.[/]")
            self._counter_hunts[key] = "planner failed"
            return False

        # A resource wall applies to EVERY destination, so it ends the ladder outright —
        # walking somewhere else with a full party or one ball is pure waste.
        resource = counter_hunt.resource_blocker()
        if resource is not None:
            console.print(f"[yellow]Story: cannot hunt a counter — {resource}. Stopping honestly.[/]")
            self._counter_hunts[key] = f"blocked: {resource}"
            return False

        # ‼ huntable_candidates, NEVER candidates[0]. Rank 1 for Norman is a Victory Road
        # Hariyama L38-42 — the cost model prices a wild already above the team at ~0 to
        # train, so it ranks endgame maps as CHEAPEST. See counter_plan.huntable_candidates.
        #
        # ‼ AND NOT JUST THE BEST ONE EITHER. Measured 2026-07-30 by driving the real
        # navigation from real saves: Wattson's top huntable destination (ROUTE111 (25,55),
        # north of the Go-Goggles desert) and Winona's (ROUTE118 (29,15), the KI-24
        # dual-elevation-bridge case) BOTH fail to path, in 255 frames, while Norman's
        # FIERY_PATH (18,19) arrives in 2,922. Taking only the best meant two of three
        # bosses burned their one hunt on a place the bot cannot walk to.
        shortlist = counter_plan.huntable_candidates(candidates)[: self.COUNTER_HUNT_MAX_DESTINATIONS]
        if not shortlist:
            blocker = counter_hunt.destination_blocker(None)
            console.print(f"[yellow]Story: cannot hunt a counter — {blocker}. Stopping honestly.[/]")
            self._counter_hunts[key] = f"blocked: {blocker}"
            return False

        attempts = []
        for candidate in shortlist:
            map_enum, tile = candidate["map_enum"], candidate["hunt_tile"]
            # Already proven unreachable from where we stand, this run (#24-regionreach).
            if self._training_blocked(map_enum, tile):
                attempts.append(f"{candidate['species_name']}@{map_enum.name}: known-unreachable")
                continue
            try:
                slot = yield from counter_hunt.hunt(candidate, needed)
            except UnreachableDestinationError as error:
                # ‼ A NAVIGATION failure is CHEAP (255 frames, fail-fast) and specific to
                # ONE place, so it earns a fallback rather than ending the ladder. Record
                # it so nothing re-walks it later this run.
                self._note_training_unreachable(map_enum, tile)
                attempts.append(f"{candidate['species_name']}@{map_enum.name}: unreachable")
                console.print(
                    f"[yellow]Story: {map_enum.name} is not reachable from here "
                    f"({error}) — trying the next counter destination.[/]"
                )
                continue
            if slot is None:
                # ‼ ARRIVED AND CAUGHT NOTHING IS NOT THE SAME FAILURE, and must NOT
                # fall through to another destination. It already cost a full
                # HUNT_SPIN_BUDGET_FRAMES (120,000); doing it again somewhere else would
                # turn a bounded ladder into a multi-hundred-thousand-frame excursion.
                # Cheap failures cascade, expensive ones do not.
                attempts.append(f"{candidate['species_name']}@{map_enum.name}: none found")
                self._counter_hunts[key] = "; ".join(attempts)
                return False

            self._counter_hunts[key] = f"caught {candidate['species_name']}"
            yield from counter_hunt.train_counter(slot, cfg)
            return True

        self._counter_hunts[key] = "; ".join(attempts) or "no destination attempted"
        console.print(
            f"[yellow]Story: no counter destination worked ({self._counter_hunts[key]}) "
            f"— stopping honestly.[/]"
        )
        return False

    def _here_map(self):
        """The map we are standing on, as a (group, number) tuple — None if unreadable."""
        try:
            from modules.map import get_map_data_for_current_position

            return tuple(get_map_data_for_current_position().map_group_and_number)
        except Exception:
            return None

    def _note_training_unreachable(self, map_enum, tile) -> None:
        """Record that `tile` on `map_enum` could NOT be reached from where we stand."""
        here = self._here_map()
        if here is None:
            return  # can't key it safely — better to retry later than to blacklist wrongly
        self._training_unreachable.add((here, tuple(map_enum.value), tuple(tile)))
        console.print(
            f"[yellow]Story: {map_enum.name} {tuple(tile)} is not reachable from here — "
            f"dropping it as a training option for the rest of this run.[/]"
        )

    def _training_blocked(self, map_enum, tile) -> bool:
        here = self._here_map()
        if here is None:
            return False
        return (here, tuple(map_enum.value), tuple(tile)) in self._training_unreachable

    def _prepare_for_fight(self, cfg: dict) -> Generator:
        """Before a major fight, train the team to a sensible level (user directive
        2026-07-21). PROACTIVE: a target within the fight's level band (organic,
        randomized). REACTIVE: if we've already LOST here ≥2 times, escalate the
        target and train harder before re-attempting — the "+levels" strategy and
        the team scope are both randomized to look human/organic."""
        import random

        from modules.pokemon_party import get_party
        from modules.story.early_game import train_team, UnreachableDestinationError

        losses = max((self._defeat_counts.get(k, 0) for k in cfg["keys"]), default=0)
        lo, hi = cfg["band"]
        target = random.randint(lo, hi)  # organic proactive target within the band

        # --- SWEEPER-SUFFICIENCY GATE (proactive attempts only — once we are LOSING
        #     here, the reactive logic below owns the decision). ---
        if losses < 2:
            verdict = self._sufficiency_verdict(cfg)
            if verdict is not None:
                from modules.pokemon_party import get_party as _gp_v

                kind, slot, train_to = verdict
                name = _gp_v()[slot].species.name
                if kind == "sufficient":
                    console.print(
                        f"[cyan]Story: {name} already answers this gym (type + level "
                        f"sufficiency) — skipping team training.[/]"
                    )
                    return
                if kind == "topup" and "grass" in cfg:
                    # FRAME-COST GATE (punch-list #24): this branch used to call train_team
                    # with no cost estimate at all. Estimate first; an unknown or over-budget
                    # estimate SKIPS the top-up (fail safe) and falls through to the rest of
                    # `_prepare_for_fight` (boss-training mode etc.) instead of committing to
                    # a grind that could burn hundreds of thousands of frames.
                    from modules.story.training_areas import estimate_frames_to_level

                    wild_level = _wild_land_max(cfg["grass"][0])
                    est_frames = (
                        estimate_frames_to_level(_gp_v()[slot], train_to, wild_level)
                        if wild_level is not None
                        else None
                    )
                    if est_frames is None or est_frames > self.MAX_PREP_TRAINING_FRAMES:
                        console.print(
                            f"[yellow]Story: {name} top-up to Lv {train_to} rejected — "
                            f"estimated {est_frames if est_frames is not None else 'UNKNOWN'} "
                            f"frames exceeds budget ({self.MAX_PREP_TRAINING_FRAMES}); "
                            f"falling through to boss-training/band-prep.[/]"
                        )
                    else:
                        console.print(
                            f"[cyan]Story: {name} is the answer to this gym but needs "
                            f"Lv {train_to} — targeted top-up of just that mon.[/]"
                        )
                        yield from train_team(train_to, slots={slot}, grass=cfg["grass"], heal_center=cfg["heal"])
                        return

        # --- BOSS-TRAINING MODE (user design 2026-07-23, Wattson analysis + the Gemini
        #     consult): when we're LOSING here but the local grass is far below our
        #     level, wild grinding is the wrong tool — a L13 wild pays ~145 XP while
        #     KO'ing even two of the boss's mons in a LOST attempt pays ~1,200 XP
        #     (Gen 3 keeps mid-battle XP through a whiteout; whiteout money loss is
        #     level x badge-payout — cheap; there is no re-challenge limit). So: if
        #     recent lost attempts each KO'd at least one boss mon, keep re-attempting
        #     the boss as the PRIMARY training vehicle, with only a LIGHT top-up
        #     between attempts (+1 level cap, not the +5 escalation). The moment two
        #     consecutive attempts produce ZERO KOs, the boss can't teach us anything
        #     — fall through to the classic heavy escalation. ---
        boss_mode = False
        if losses >= 2:
            from modules.pokemon_party import get_party as _gp_levels

            _levels_now = [p.level for p in _gp_levels() if p is not None and not p.is_egg]
            team_max = max(_levels_now, default=0)
            wild_max = None
            try:
                from modules.map import get_wild_encounters_for_map

                if "grass" in cfg:
                    grass_map = cfg["grass"][0]
                    enc = get_wild_encounters_for_map(*grass_map.value)
                    if enc is not None and enc.land_encounters:
                        wild_max = max(e.max_level for e in enc.land_encounters)
            except Exception:
                pass
            recent = sorted(
                (entry for k in cfg["keys"] for entry in self._loss_ko_history.get(k, ())),
            )[-2:]
            recent_kos = [kos for _seq, kos in recent]
            # No grass configured at all (e.g. Lavaridge — no reachable training
            # grass exists) counts as fodder too: grass can't teach us either way.
            grass_is_fodder = ("grass" not in cfg) or (wild_max is not None and wild_max + 8 < team_max)
            boss_teaches = bool(recent_kos) and any(k >= 1 for k in recent_kos)
            if grass_is_fodder and boss_teaches:
                # KI-23 (Winona): a strong mon can KO 1-2 of the boss's mons EVERY
                # attempt and still lose forever if nothing in the party is
                # super-effective against it — the ZERO-KO guard above never fires
                # there, and boss-training mode would keep "teaching" us nothing
                # useful, run after run. Check BEFORE committing to another attempt.
                hopeless, needed = self._boss_plan_is_hopeless(cfg)
                if hopeless:
                    from modules.modes import BotModeError

                    # #24-counters PHASE 2: try to ACT on the diagnosis before stopping.
                    # Bounded to ONE attempt per boss per run (see `_counter_ladder`), and
                    # it falls through to the SAME raise below on every failure path.
                    acted = yield from self._counter_ladder(cfg, losses, needed)
                    if not acted:
                        # ‼ NEVER DELETE THIS RAISE. Silent non-progress is worse than an
                        # honest stop: before phase 1 existed this boss looped for ever,
                        # and the whole value of the diagnosis is that it ENDS the run
                        # with the reason attached.
                        raise BotModeError(_counter_catch_message(cfg, losses, needed))
                    # A rung fired. Re-prepare from the top so the new party member is
                    # taken into account by the sufficiency/boss-mode logic rather than
                    # by this stale pass — the party is not what it was when we entered.
                    return
                boss_mode = True
                target = team_max + 1  # light top-up only — the boss battle is the trainer
                console.print(
                    f"[bold cyan]Story: boss-training mode — local wilds (max L{wild_max}) are far "
                    f"below the team (L{team_max}); re-attempting the boss is the real training "
                    f"(recent attempts KO'd {recent_kos} of theirs). Light top-up to L{target} only.[/]"
                )
            elif grass_is_fodder and recent_kos and not boss_teaches:
                console.print(
                    f"[yellow]Story: last {len(recent_kos)} boss attempts KO'd nothing — "
                    f"the boss can't teach us; falling back to grass escalation.[/]"
                )
        if losses >= 2 and not boss_mode:
            levels = [p.level for p in get_party() if p is not None and not p.is_egg]
            team_max = max(levels, default=0)
            team_avg = (sum(levels) // len(levels)) if levels else 0
            choice = random.choice(["plus5_max", "plus5_avg", "escalate_band"])
            if choice == "plus5_max":
                target = max(target, team_max + 5)
            elif choice == "plus5_avg":
                target = max(target, team_avg + 5)
            else:
                target = max(target, hi + 2 * (losses - 1))
            console.print(
                f"[bold yellow]Story: lost here {losses}× — training harder before "
                f"re-attempting (target Lv {target}, {choice}).[/]"
            )
        # READY THE BATTLERS, don't grind every catch (user 2026-07-21). Bringing a
        # fresh Lv4-6 catch to gym level via half-XP swap-training is a huge grind and
        # unnecessary — our primary mon sweeps the gym. So train only the mons worth
        # readying now: the STRONGEST battler (our primary), plus any battler ALREADY
        # within `TRAIN_CATCHUP_GAP` levels of the target (close enough to finish
        # cheaply). Fresh far-below catches are left to level organically (#24-team).
        # When we've been LOSING here, add depth — also ready the top backups.
        from modules.story.early_game import _battler_slots

        party = get_party()
        battlers = _battler_slots()
        if not battlers:
            return
        strongest = max(battlers, key=lambda i: party[i].level)
        catchup = target - self.TRAIN_CATCHUP_GAP
        to_train = {i for i in battlers if party[i].level >= catchup}
        to_train.add(strongest)
        if losses >= 2:
            ranked = sorted(battlers, key=lambda i: party[i].level, reverse=True)
            to_train.update(ranked[: min(3, len(ranked))])

        need = [i for i in to_train if party[i].level < target]
        if not need:
            console.print(f"[dim]Story: the team's battlers are already ≥ Lv {target} — no prep training.[/]")
        elif "grass" not in cfg:
            # No training grass exists for this boss (e.g. Lavaridge). The re-attempt
            # itself is the only trainer available — boss-training mode's whole point.
            console.print("[dim]Story: no training grass here — re-attempting is the training.[/]")
        else:
            # --- LEVEL-APPROPRIATE RELOCATION (user directive 2026-07-24) ---------------
            # The per-boss `grass` is the LOCAL patch, which is right for most gyms but
            # pathological for NORMAN: his gym is the geographically EARLIEST one yet is
            # fought 5th, so "local" is Route 102 at L3-4 against a L27-31 team — ~25 xp a
            # kill, i.e. effectively never. Rather than grind fodder, look for a training
            # area actually matched to the team and go there (train_team travels
            # warp-aware via _goto_training_area, so a distant area is fine); heal at the
            # PC nearest THAT area, not the boss's, or the bot walks the region every
            # time HP dips. If nothing better exists, do NOT grind fodder at all — skip
            # prep and let the fight + boss-training telemetry own the levelling (a lost
            # boss attempt that KOs 2 mons pays ~1,200 xp; a L4 wild pays ~25).
            grass_map, grass_tile = cfg["grass"]
            heal_at_center = cfg["heal"]
            levels_now = [p.level for p in party if p is not None and not p.is_egg]
            team_max_now = max(levels_now, default=target)
            local_max = _wild_land_max(grass_map)
            # ‼ THE FODDER TEST IS NOW A PURE FUNCTION (KI-31, 2026-07-29).
            # `training_areas.local_patch_is_fodder` holds BOTH rules behind
            # `FODDER_RULE`, which defaults to "legacy" — the expression that used to be
            # inline here, unchanged. Under the default this block behaves exactly as
            # before, including doing NO extra area lookup. The alternative "xp_rate" rule
            # fixes a measured hole (teams below ~L17 can never relocate, because
            # 5 + 12 = 17) but moves early-game prep that `repro_fodder_grass.py` records
            # as proven-good — and that repro needs a real mgba, so it cannot be validated
            # on the dev box. Flip the flag only alongside an A/B on the batch machine.
            _allow = lambda m, t, p: (  # noqa: E731 - shared by the probe and the pick
                _training_area_allowed(m, t, p) and not self._training_blocked(m, t)
            )
            _is_fodder = False
            if local_max is not None:
                from modules.story import training_areas as _ta

                _probe_hi = None
                if _ta.FODDER_RULE == "xp_rate":
                    # Only this rule needs to know the alternative BEFORE deciding, so the
                    # legacy path keeps its original single-lookup shape.
                    try:
                        _probe = _ta.best_training_area(
                            team_max_now, min_wild_max=local_max, allow=_allow
                        )
                        _probe_hi = _probe[2][1] if _probe else None
                    except Exception:  # noqa: BLE001 - a probe failure must not block prep
                        _probe_hi = None
                _is_fodder = _ta.local_patch_is_fodder(
                    local_max, team_max_now, self.FODDER_LEVEL_GAP,
                    best_available_max=_probe_hi,
                )
            if _is_fodder:
                better = None
                try:
                    from modules.story.training_areas import best_training_area

                    # The replacement must beat the local patch AND not be fodder itself
                    # — otherwise we'd walk somewhere new to grind equally-worthless xp.
                    floor = max(local_max, team_max_now - self.FODDER_LEVEL_GAP)
                    # Skip anything this run has ALREADY walked into a wall trying to
                    # reach from where we now stand — see `_training_unreachable`.
                    better = best_training_area(
                        team_max_now,
                        min_wild_max=floor,
                        allow=_allow,
                    )
                except Exception:
                    better = None
                if better is not None:
                    b_map, b_tile, (b_lo, b_hi) = better
                    local_name = grass_map.name
                    grass_map, grass_tile = b_map, b_tile
                    heal_at_center = _training_area_heal_map().get(b_map, cfg["heal"])
                    _msg = (f"Story: {local_name} (max L{local_max}) is fodder for a "
                            f"L{team_max_now} team — relocating to {b_map.name} "
                            f"(L{b_lo}-{b_hi}) to train for real. [rule={_ta.FODDER_RULE}]")
                    console.print(f"[bold cyan]{_msg}[/]")
                    # ‼ ALSO INTO THE DEBUG LOG (2026-07-29). This decision was `console.print`
                    # ONLY, so it never reached a debug log — and a debug log is what gets
                    # shared for review. It made the KI-31 xp_rate A/B unevaluable from a
                    # single-lane run: the effect of the experiment was invisible in the one
                    # artefact describing the run. (x4 bundles ship stdout too, which is why
                    # the control arm was still measurable there — but a debug log should not
                    # depend on that.)
                    _log_story_event(_msg)
                else:
                    _msg = (f"Story: local grass (max L{local_max}) is fodder for a "
                            f"L{team_max_now} team and no better area is available — skipping "
                            f"the grind; the boss attempt itself is the training. "
                            f"[rule={_ta.FODDER_RULE}]")
                    console.print(f"[yellow]{_msg}[/]")
                    _log_story_event(_msg)
                    need = []
            if need:
                console.print(
                    f"[cyan]Story: prepping — training {len(need)} battler(s) to Lv {target} "
                    f"in {grass_map.name} (fresh low catches left to level organically).[/]"
                )
                try:
                    yield from train_team(
                        target, slots=to_train, grass=(grass_map, grass_tile), heal_center=heal_at_center
                    )
                except UnreachableDestinationError:
                    # The reachability oracle said yes and the map disagreed. Remember it
                    # so the next pick differs, THEN re-raise so the normal derail recovery
                    # still runs. Without the memory this is a deterministic death loop:
                    # re-running `_play` re-picks the identical unreachable tile every
                    # derail until the budget drops the run to Manual (2/5 runs, batch
                    # 20260725-194810, Route 111 (25,55) from Mauville).
                    self._note_training_unreachable(grass_map, grass_tile)
                    raise

    def on_battle_started(self, encounter):
        # Story battles (the first Birch battle, training, the rival) are meant
        # to be FOUGHT and won with the default battle strategy — never run from
        # or auto-caught. The BattleListener handles the fight while run() pauses.
        #
        # SHINY (user directive 2026-07-22 — supersedes the old fight-through
        # contingency): a wild shiny is a rare collectible and is ALWAYS worth a
        # catch attempt — even an already-caught species, even with a full party
        # (→ PC box), at any story stage. This check runs FIRST so it pre-empts
        # swap-training and ordinary team-catching. With no usable ball we fight
        # through as before (the user's explicit fallback). Either way we return
        # a strategy, which bypasses handle_encounter()'s default "shiny → stop
        # the bot" halt — the story must never stop. The scripted first battle is
        # a Tutorial encounter (the framework forces its flow; no catch possible),
        # so it keeps the fight-through path.
        try:
            if encounter is not None and encounter.is_shiny:
                from modules.console import console
                from modules.items import get_item_bag

                species = getattr(getattr(encounter, "pokemon", None), "species", None)
                name = getattr(species, "name", "Pokémon")
                is_tutorial = getattr(getattr(encounter, "type", None), "name", "") == "Tutorial"
                have_balls = False
                try:
                    have_balls = sum(s.quantity for s in get_item_bag().poke_balls) > 0
                except Exception:
                    pass
                if not is_tutorial and have_balls:
                    console.print(
                        f"[bold yellow]Story Mode: ✨ a SHINY {name} appeared — "
                        f"attempting to CATCH it (shinies are always worth a ball)![/]"
                    )
                    context.message = f"Story: ✨ shiny {name} — attempting the catch!"
                    return StoryShinyCatchStrategy()
                console.print(
                    f"[bold yellow]Story Mode: a SHINY {name} appeared but "
                    f"{'this is the scripted tutorial battle' if is_tutorial else 'there are no usable Poké Balls'}"
                    f" — fighting through (not stopping).[/]"
                )
                context.message = f"Story: shiny {name} — no catch possible here, fighting through."
                return LevelUpTravelBattleStrategy()
        except Exception:
            pass
        # HM-LEARNER HUNT (user directive 2026-07-23): while ensure_hm_learner is
        # spinning for a species that can learn a needed HM, catch it on sight —
        # any story stage, needs only party room and a spare ball.
        try:
            from modules.story import early_game as _eg

            if _eg.HM_CATCH_TARGET_DEX and encounter is not None and not getattr(encounter, "is_shiny", False):
                from modules.items import get_item_bag
                from modules.pokemon_party import get_party as _gp

                sp = getattr(getattr(encounter, "pokemon", None), "species", None)
                if (
                    sp is not None
                    and sp.national_dex_number in _eg.HM_CATCH_TARGET_DEX
                    and len([m for m in _gp() if m is not None]) < 6
                    and sum(sl.quantity for sl in get_item_bag().poke_balls) > 1
                ):
                    # ‼ local import required: later branches in this method import
                    # `console` locally, which makes the name function-local EVERYWHERE
                    # in the method — referencing the module-level one here raises
                    # UnboundLocalError (and the except silently ate the catch).
                    from modules.console import console

                    console.print(f"[bold green]Story: catching {sp.name} — it can learn the HM we need![/]")
                    return StoryCatchStrategy()
        except Exception:
            pass
        # COUNTER-CATCH HUNT (#24-counters phase 2): while `counter_hunt.hunt` is spinning
        # for the species that answers a boss we cannot beat, catch it on sight. Deliberate
        # clone of the HM branch above — same gates (party room, a SPARE ball, not a shiny),
        # same failure mode if they are skipped.
        try:
            from modules.story import counter_hunt as _chunt

            if (
                _chunt.COUNTER_CATCH_TARGET_DEX
                and encounter is not None
                and not getattr(encounter, "is_shiny", False)
            ):
                from modules.items import get_item_bag
                from modules.pokemon_party import get_party as _gp_c

                sp = getattr(getattr(encounter, "pokemon", None), "species", None)
                if (
                    sp is not None
                    and sp.national_dex_number in _chunt.COUNTER_CATCH_TARGET_DEX
                    and len([m for m in _gp_c() if m is not None]) < 6
                    and sum(sl.quantity for sl in get_item_bag().poke_balls) > 1
                ):
                    # ‼ LOCAL IMPORT REQUIRED — the same trap that silently ate the HM
                    # branch and survival mode (08-MISTAKES 2026-07-26, three times in one
                    # day). Other branches in this method import `console` locally, which
                    # makes the name function-local for the WHOLE method, so touching the
                    # module-level one here is an UnboundLocalError that the `except` below
                    # would swallow — the catch would simply never happen, silently.
                    from modules.console import console

                    console.print(
                        f"[bold green]Story: catching {sp.name} — it is the type counter "
                        f"this boss needs![/]"
                    )
                    return StoryCatchStrategy()
        except Exception:
            pass
        # ‼ SURVIVAL MODE (#24-whiteout, from live batch 20260725-194810). WILD battles
        # on a map that has already wiped us repeatedly stop being an XP opportunity and
        # become the thing to escape. run01 whited out **25 times on ROUTE110** — respawn
        # in Slateport, walk back north, wipe again — and nothing ever noticed, because
        # the default `LevelUpTravelBattleStrategy` fights every wild to level the lead.
        # Its own docstring says it "flees only at low HP, which the training loop covers
        # by healing" — but this is a TRAVEL leg, where no training loop and therefore no
        # healing exists, so HP only ever goes down across consecutive encounters.
        #
        # Scope is deliberately narrow:
        #   * WILD only (`encounter is not None`) — a trainer battle cannot be fled, and
        #     the boss/gym re-attempt path must stay exactly as it is.
        #   * NOT during `train_team` — there the swap strategy plus its heal loop are the
        #     correct answer, and fleeing would starve the grind it was sent to do.
        #   * Threshold is per-MAP defeats this run, so it cannot fire on a first bad
        #     encounter; it takes a demonstrated pattern.
        try:
            from modules.story.early_game import swap_train_active

            if (
                encounter is not None
                and not swap_train_active()
                and self._defeat_counts.get(self._location_key(), 0)
                >= self.SURVIVAL_WHITEOUT_THRESHOLD
            ):
                # ‼ StoryFleeStrategy, NOT the stock RunAwayStrategy — the stock one
                # returns False from choose_new_lead_after_battle(), which crashed a
                # live run through fight()'s rotation path. See the class docstring.
                # ‼ LOCAL IMPORT REQUIRED — same trap as the HM branch above, and it
                # caught this block too (2026-07-25): other branches in this method
                # import `console` locally, which makes the name function-local for the
                # WHOLE method, so touching the module-level one here is an
                # UnboundLocalError that the `except` below silently ate. The repro
                # showed survival mode simply "not firing"; nothing was logged.
                from modules.console import console

                console.print(
                    f"[bold yellow]Story: {self._defeat_counts.get(self._location_key(), 0)} "
                    f"defeats on this map already — fleeing wild battles to get through "
                    f"instead of levelling into another whiteout.[/]"
                )
                return StoryFleeStrategy()
        except Exception:
            pass
        # PRE-GYM-1 CATCHING (user directive 2026-07-21): build an organic team by
        # catching NEW species (never a dup) while travelling to the first gym.
        try:
            if self._should_catch(encounter):
                from modules.console import console

                sp = getattr(getattr(encounter, "pokemon", None), "species", None)
                console.print(f"[bold green]Story: catching a new {getattr(sp, 'name', '?')} for the team![/]")
                # Use the story catch strategy (flees when out of balls instead of
                # dropping to Manual — see StoryCatchStrategy).
                return StoryCatchStrategy()
        except Exception:
            pass
        # SWAP-TRAINING: while train_team is running, use the swap strategy so an
        # under-levelled lead is switched out to a stronger team-mate (shares XP, no
        # fainting) instead of grinding itself to death against higher-level wilds.
        try:
            from modules.story.early_game import swap_train_active

            if swap_train_active() and encounter is not None:
                return SwapTrainBattleStrategy()
        except Exception:
            pass
        # Fight to WIN and level the lead (strongest move; flees only at low HP,
        # which the training loop covers by healing). The travel variant also
        # refuses to flee a TRAINER battle (single-mon party can't — see ML-8),
        # fighting on instead; used for training wilds, the rival, and route
        # trainers. The scripted first battle is a Tutorial (framework-handled).
        return LevelUpTravelBattleStrategy()

    def run(self) -> Generator:
        # DEFEAT / WHITEOUT RECOVERY (user directive 2026-07-21): the segmented resume
        # (`_play`) runs inside a restart loop. On a whiteout, on_whiteout() flags an
        # abort → the running segment bails → we catch it here, re-orient from the
        # respawn point, and re-run `_play` (which skips finished segments and
        # re-attempts the failed one). GENUINE (non-whiteout) errors propagate to
        # Manual exactly as before. No save states are ever reloaded.
        from modules.modes import BotModeError
        from modules.story.early_game import set_story_abort, exit_building_after_whiteout
        from modules.modes.util.walking import wait_for_player_avatar_to_be_controllable
        from modules.battle_fault import take_pending_fault, clear_pending_fault

        # Never inherit a fault recorded just before this mode started.
        clear_pending_fault()

        recoveries = 0
        while True:
            set_story_abort(False)
            self._whiteout_pending = False
            try:
                # GLOBAL NEVER-HANG WATCHDOG (#24-interrupt, real-HW log 2026-07-22):
                # a wedged primitive can spin the mode generator forever with no error
                # (a trainer-intro msgbox opened mid-turn and ensure_facing_direction
                # pressed direction keys at a locked avatar for 85k frames — only the
                # debug logger noticed). Drive _play frame by frame and watch a broad
                # stall signature (map, position, game state, party, message): if
                # NOTHING changes for 18k mode-driven frames (~5 min; battles don't
                # count — a listener holds control then), raise a derail so run()'s
                # own recovery (B-ride scripts, re-orient, re-enter) takes over.
                _play_gen = self._play()
                _stall_sig = None
                _stall_frames = 0
                while True:
                    # RECOVERABLE BATTLE FAULT (#24-movelearn-recovery, 2026-07-25).
                    # The battle handler runs as a SIBLING generator on the controller
                    # stack, so an error it raises goes straight to main_loop → Manual
                    # and never reaches the `except BotModeError` below. Instead it
                    # parks the reason in `battle_fault`; we claim it HERE, inside the
                    # try, so a battle we cannot finish costs one derail (with the
                    # normal B-ride/re-orient/resume) instead of the entire run.
                    _fault = take_pending_fault()
                    if _fault is not None:
                        try:
                            _play_gen.close()
                        except Exception:
                            pass
                        raise BotModeError(f"Story: battle handler gave up — {_fault}")
                    try:
                        next(_play_gen)
                    except StopIteration:
                        return
                    # KI-15 post-battle message nudge: an inline battle fought/fled
                    # during navigation or training can leave a battle message ("grew
                    # to LV. N!", "won $N", "Got away safely!") waiting for A in the
                    # overworld while the running primitive (navigate/spin/facing)
                    # doesn't press it — stranding the resume until the 18k watchdog.
                    # It is BATTLE text (A clears it; B does not, proven on the (14,5)
                    # capture) with NO field script active.
                    # ‼ The signature must hold for a SUSTAINED stretch before we
                    # press, and we press ONCE per stretch: `cb` stays
                    # "ReturnFromBattle..." (stale) until the NEXT battle, and a live
                    # NPC dialogue's script context flickers inactive between message
                    # boxes — an every-frame nudge A-mashed the Rustboro nurse's
                    # dialogue into an endless re-open loop (this session's (7,4)
                    # capture; the museum-greeter lesson). The genuine stale wedge is
                    # rock-stable for hundreds of frames (probe: 400+ unchanged), so
                    # 90 consecutive matching frames identifies it safely, and one A
                    # clears it instantly (proven frame-0 on the (14,5) capture).
                    try:
                        from modules.tasks import (
                            is_waiting_for_input as _iwfi,
                            get_global_script_context as _ggsc,
                            get_immediate_script_context as _gisc,
                        )
                        from modules.battle_state import battle_is_active as _bia
                        from modules.memory import get_game_state as _ggs0, GameState as _GS0
                        from modules.player import get_player_avatar as _gpa15

                        # NO reader distinguishes this wedge from a field dialogue's
                        # parked WaitForAorBPress tail (identical stale native; both
                        # ignore B — probed on the captures; two rider-side designs
                        # failed, see 08-MISTAKES 2026-07-24). The wedge's ONE unique
                        # property: it BLOCKS ALL MOVEMENT. So the signature demands
                        # waiting + no scripts + POSITION FROZEN for 240 consecutive
                        # frames → a single A → 1200-frame cooldown. A dialogue tail
                        # can't match (the story flow keeps walking → position
                        # changes reset the count); a live dialogue's script context
                        # going active resets it too (the every-frame ancestor of
                        # this nudge A-mashed the nurse — ki15_nurse_wedge.ss1).
                        try:
                            _pos15 = tuple(_gpa15().local_coordinates)
                        except Exception:
                            _pos15 = None
                        if (
                            _pos15 is not None
                            and _pos15 == getattr(self, "_ki15_nudge_pos", None)
                            and _ggs0() is _GS0.OVERWORLD
                            and not _bia()
                            and _iwfi()
                            and not _ggsc().is_active
                            and not _gisc().is_active
                        ):
                            self._ki15_nudge_stable = getattr(self, "_ki15_nudge_stable", 0) + 1
                            if self._ki15_nudge_stable >= 240:
                                context.emulator.press_button("A")
                                self._ki15_nudge_stable = -1200  # long cooldown
                                # breadcrumb for run-log forensics (run 8: a wedge
                                # this nudge should own sat 20k frames — prove
                                # in future logs whether it fired)
                                console.print("[dim]Story: KI-15 nudge fired (stale post-battle message).[/]")
                        else:
                            _n = getattr(self, "_ki15_nudge_stable", 0)
                            self._ki15_nudge_stable = 0 if _n > 0 else min(_n + 1, 0)
                        self._ki15_nudge_pos = _pos15
                    except Exception:
                        pass
                    yield
                    try:
                        from modules.map import get_map_data_for_current_position
                        from modules.memory import get_game_state as _ggs
                        from modules.player import get_player_avatar as _gpa

                        _md = get_map_data_for_current_position()
                        _cur = (
                            (_md.map_group, _md.map_number),
                            tuple(_gpa().local_coordinates),
                            str(_ggs()),
                            self._progress_sig(),
                            context.message,
                        )
                    except Exception:
                        _cur = None
                    if _cur is not None and _cur == _stall_sig:
                        _stall_frames += 1
                        if _stall_frames >= 18000:
                            try:
                                _play_gen.close()
                            except Exception:
                                pass
                            raise BotModeError(
                                "Story: global watchdog — nothing progressed for 18,000 frames "
                                "(the current step is wedged); derailing into recovery."
                            )
                    else:
                        _stall_sig = _cur
                        _stall_frames = 0
            except BotModeError as err:
                from modules.memory import game_has_started, get_game_state, GameState

                if not self._whiteout_pending:
                    # NON-WHITEOUT DERAIL (user directive 2026-07-21): don't drop
                    # straight to Manual — re-localise (log where we are in the story
                    # AND on the map) and retry the segmented resume a bounded number
                    # of times. The resume re-detects the stage from flags + position,
                    # so a transient nav/scene hiccup self-corrects. Only hand to
                    # Manual if it keeps failing (a genuine, persistent problem).
                    # Reset the budget when we've made real progress since the last
                    # derail: a long segment (training, a chapter) can throw a few
                    # unrelated transient hiccups, and those must NOT accumulate into
                    # a false drop to Manual. Only CONSECUTIVE no-progress derails —
                    # a genuine stuck loop — escalate.
                    sig = self._progress_sig()
                    if sig != self._last_derail_sig:
                        self._derails = 0
                        self._last_derail_sig = sig
                    self._derails += 1
                    self._log_localization(f"derail #{self._derails}: {err}")
                    try:
                        from modules import debug_logger

                        debug_logger.event(f"DERAIL #{self._derails}: {err}")
                    except Exception:
                        pass
                    if self._derails > 4:
                        raise
                    set_story_abort(False)
                    try:
                        # FIRST close any OPEN scripted dialogue: waiting alone presses
                        # nothing, and an open msgbox (Briney's post-sail Letter reminder,
                        # real-HW 2026-07-22) keeps the avatar non-controllable FOREVER —
                        # the recovery itself was derail-looping on it. _ride_out_scripted_
                        # scene B-advances an active script and is a cheap no-op otherwise.
                        from modules.story.early_game import (
                            _ride_out_scripted_scene,
                            wait_until_truly_controllable,
                        )

                        yield from _ride_out_scripted_scene("B")
                        # Then patiently ride out the post-battle transition before
                        # retrying. These stalls SELF-HEAL (the overworld becomes
                        # controllable on its own) but the controllable flag flickers
                        # first, so waiting for a STABLE controllable window here lets a
                        # SINGLE recovery ride out the whole stall instead of burning many
                        # rapid derail cycles toward Manual.
                        # Close any STRAY MENU first (an open bag/party menu is not a
                        # script — nothing else in the recovery can close it, and a
                        # navigator driving under an open bag wedges forever; batch
                        # run02 2026-07-22). Bounded B-presses until the overworld.
                        from modules.memory import GameState as _GS
                        from modules.memory import get_game_state as _ggs2

                        for _f in range(900):
                            if _ggs2() is _GS.OVERWORLD:
                                break
                            context.emulator.press_button("B")
                            yield
                            yield
                        yield from wait_until_truly_controllable(timeout_frames=3000)
                        yield from exit_building_after_whiteout()
                        # Cave-stranded derails (a heal/nav plan-failed from INSIDE the
                        # training cave) must physically exit before the retry, or the
                        # segment re-fails identically forever (batch 20260722-182727).
                        # A cheap no-op anywhere else.
                        from modules.story.early_game import _exit_training_cave_if_inside

                        yield from _exit_training_cave_if_inside()
                        settle = 0
                        while settle < 300 and not (
                            game_has_started() and get_game_state() is GameState.OVERWORLD
                        ):
                            settle += 1
                            yield
                    except Exception:
                        yield
                    continue  # re-run _play(): re-localise from flags + position
                # --- WHITEOUT recovery ---
                recoveries += 1
                self._derails = 0  # reaching a fight = progress; reset the derail budget
                try:
                    from modules import debug_logger

                    debug_logger.event(f"WHITEOUT recovery #{recoveries}")
                except Exception:
                    pass
                if recoveries > 40:
                    raise BotModeError(
                        "Story: too many whiteout recoveries in a row — stopping so I "
                        "don't loop forever. Check the team/route."
                    )
                self._whiteout_pending = False
                set_story_abort(False)
                console.print(
                    "[cyan]Story: recovered from the whiteout — re-orienting at the "
                    "respawn point and resuming.[/]"
                )

                try:
                    yield from wait_for_player_avatar_to_be_controllable()
                    # Respawn lands us INSIDE the Poké Center — step out to the town
                    # so the segmented resume's map checks work (else it backtracks).
                    yield from exit_building_after_whiteout()
                    # SETTLE: right after the exit warp the game is transiently
                    # "not started" / in a non-overworld state — re-running _play now
                    # would misfire its title check into the New-Game intro. Wait for
                    # a stable started+overworld state first.
                    settle = 0
                    while settle < 600 and not (
                        game_has_started() and get_game_state() is GameState.OVERWORLD
                    ):
                        settle += 1
                        yield
                    yield from wait_for_player_avatar_to_be_controllable()
                except BotModeError:
                    raise
                except Exception:
                    yield
                # loop → re-run the segmented resume from the respawn point

    def _play(self) -> Generator:
        import random

        from modules.memory import get_event_flag, get_event_var
        from modules.map import get_map_data_for_current_position
        from modules.map_data import MapRSE
        from modules.story import detect_live
        from modules.story.config import get_story_config
        from modules.story.intro import run_intro
        from modules.story.early_game import (
            cross_petalburg_woods,
            descend_and_leave_players_house,
            do_petalburg_gym_and_wally_tutorial,
            do_rustboro_gym,
            finish_birch_lab,
            fight_route103_rival,
            go_upstairs_and_set_clock,
            help_birch_and_choose_starter,
            recover_devon_goods,
            return_devon_goods_and_get_pokenav,
            sail_to_dewford,
            deliver_stevens_letter,
            do_dewford_gym,
            sail_to_slateport,
            deliver_devon_goods_to_stern,
            travel_route110_and_fight_rival,
            fight_wally_mauville,
            do_mauville_gym,
            handle_pokenav_match_call_tutorial,
            fight_rustboro_rival,
            return_to_lab_and_get_pokedex,
            train_lead_to_level,
            travel_route104_north_to_rustboro,
            travel_to_petalburg,
            travel_to_petalburg_woods,
            travel_to_route103,
            visit_rivals_house,
            walk_off_truck_and_into_house,
        )

        cfg = get_story_config(context.profile.path)

        def _done(flag: str) -> bool:
            # FAIL LOUDLY on unknown flag names: get_event_flag() silently returns
            # False for a name that isn't in the table, which lets a typo'd/phantom
            # flag gate a segment into an eternal derail loop (Ch9a shipped with
            # "DEFEATED_RIVAL_ROUTE_110", which does not exist — run 5 hit Manual on
            # it). A wrong NAME is a build error, not a game state — surface it.
            from modules.memory import _event_flags

            if flag not in _event_flags:
                raise BotModeError(f"Story: flag name {flag!r} is not in the event-flag table (typo/phantom name).")
            try:
                return bool(get_event_flag(flag))
            except Exception:
                return False

        def _cur_map():
            try:
                d = get_map_data_for_current_position()
                return (d.map_group, d.map_number)
            except Exception:
                return None

        def _has_starter() -> bool:
            """True once the player owns a (non-egg) Pokémon — i.e. we are PAST the
            scripted intro. Lets a mid-Segment-1 recovery skip the truck→lab cutscene
            and resume at training rather than trying (and failing) to re-run the
            intro from wherever we respawned."""
            try:
                from modules.pokemon_party import get_party

                return any(not getattr(p, "is_egg", False) for p in get_party())
            except Exception:
                return False

        from modules.modes import BotModeError

        def _guard(label: str, done_check) -> None:
            """SELF-CORRECTION (§SC): after a segment, confirm it actually reached
            its completion signal. If not, the bot silently derailed (a mis-warp,
            a lost battle/blackout, or a skipped beat) — STOP with a diagnostic
            rather than blindly marching on and compounding the error. Re-running
            Story then resumes correctly from the REAL state (§RS)."""
            if done_check():
                return
            try:
                prog = detect_live()
                where = f"{prog.chapter_key}: {prog.chapter_name}"
            except Exception:
                where = "unknown"
            raise BotModeError(
                f"Story self-check: '{label}' didn't reach its completion signal "
                f"(now {where}, map {_cur_map()}). Stopping so I don't derail "
                "further — just run Story again and it resumes correctly from here."
            )

        # RESUME MODEL: the story is linear, so we run each SEGMENT only if its
        # completion signal isn't already set — a fresh game runs everything; a
        # resumed save (or one you hand-played partway) skips what's done and
        # continues from the right place. See design §RS. (Segments self-locate
        # via navigation; the Woods segment also picks its sub-entry by current
        # map so a resume mid-Woods doesn't backtrack to Petalburg.) After each
        # segment a _guard() self-check confirms it truly completed (§SC).
        at_title = get_game_state() is GameState.TITLE_SCREEN or not game_has_started()
        if not at_title:
            # RESUME-FROM-ANYWHERE (user directive 2026-07-23): normalize whatever
            # state we were entered in — a milestone loaded mid-menu, an open dialogue,
            # a live battle, a cutscene — to a stable controllable overworld BEFORE any
            # segment navigates. Without this a menu-saved state (the rocksmash_taught
            # milestone) wedges the first navigator under the open menu.
            from modules.story.early_game import normalize_to_overworld

            yield from normalize_to_overworld()
            try:
                progress = detect_live()
                console.print(
                    f"[bold cyan]Story Mode — resuming[/] (detected {progress.chapter_key}: "
                    f"{progress.chapter_name}); skipping what's already done."
                )
            except Exception:
                pass

        # --- Chapter 0: New Game intro. Title screen only — mid-intro isn't a
        #     resumable point (it must run from the truck). A title screen WITH an
        #     existing save should be loaded via Continue first (TODO §RS). ---
        if at_title:
            console.print(
                f"[bold cyan]Story Mode — new game[/] as [bold]{cfg.character_name}[/] ({cfg.gender})."
            )
            yield from run_intro(cfg.character_name, cfg.gender)

        # --- Segment 1: truck → house → clock → rival → starter → first battle →
        #     lab → train → rival → Pokédex. Gated by the Pokédex flag so a resumed
        #     game past this point skips it. INTERNALLY split into two parts so a
        #     mid-Segment-1 recovery (whiteout/derail during training) resumes
        #     correctly instead of re-running the scripted intro from the truck —
        #     which can't navigate back to the house and loops/derails (user-seen
        #     "stuck at the Oldale Poké Center after respawn"). ---
        if not _done("RECEIVED_POKEDEX_FROM_BIRCH"):
            if not _has_starter():
                # Part A — the scripted intro (truck → clock → rival house →
                # starter → first battle → lab → up to Route 103). This is a linear
                # cutscene run that ONLY works from the truck, so it is NOT a
                # resumable point: run it only while the starter doesn't exist yet.
                yield from walk_off_truck_and_into_house()
                yield from go_upstairs_and_set_clock()
                yield from descend_and_leave_players_house()
                yield from visit_rivals_house()
                yield from help_birch_and_choose_starter(cfg.starter)
                yield from finish_birch_lab(cfg.starter_nickname)
                yield from travel_to_route103()
            else:
                console.print(
                    "[dim]Story: resuming with a starter but no Pokédex — skipping the "
                    "scripted intro, back to training on Route 103.[/]"
                )
            # Part B — train → rival → Pokédex. RESUMABLE from anywhere: each step
            # self-locates (navigate_to_anywhere / _navigate_through_scripts) and is
            # gated by its own flag, so a recovery here picks up at the right place.
            if not _done("DEFEATED_RIVAL_ROUTE103"):
                target_level = random.randint(8, 10)
                console.print(f"[cyan]Story: training the starter to Lv {target_level} before the rival.[/]")
                yield from train_lead_to_level(target_level)
                yield from fight_route103_rival()
            else:
                console.print("[dim]Story: rival already beaten — heading back for the Pokédex.[/]")
            yield from return_to_lab_and_get_pokedex()
        else:
            console.print("[dim]Story: already have the Pokédex — skipping the intro chapters.[/]")
        _guard("intro → Pokédex", lambda: _done("RECEIVED_POKEDEX_FROM_BIRCH"))

        # --- Segment 2: Petalburg City — Dad (Norman) + Wally catching tutorial.
        #     Completion signal: Wally's mum leaves Petalburg (HIDE_..._WALLYS_MOM);
        #     the "intended" THANKED_FOR_PLAYING_WITH_WALLY is never set (ML-9). ---
        if not _done("HIDE_PETALBURG_CITY_WALLYS_MOM"):
            yield from travel_to_petalburg()
            yield from do_petalburg_gym_and_wally_tutorial()
        else:
            console.print("[dim]Story: Petalburg / Wally tutorial already done — skipping.[/]")
        _guard("Petalburg / Wally", lambda: _done("HIDE_PETALBURG_CITY_WALLYS_MOM"))

        # --- Segment 3: Route 104 → Petalburg Woods → Rustboro. Enter at the
        #     right sub-step by current map so a mid-Woods resume doesn't backtrack. ---
        rustboro = MapRSE.RUSTBORO_CITY.value
        woods = MapRSE.PETALBURG_WOODS.value
        route116 = MapRSE.ROUTE116.value
        rusturf = MapRSE.RUSTURF_TUNNEL.value

        def _in_rustboro() -> bool:
            # Anywhere in the Rustboro AREA means the Woods crossing is already done:
            # Rustboro city, ANY Rustboro building (map group 11 — gym/Devon/PC/mart/…),
            # Route 116 (the pre-gym catching/training grass — only reachable THROUGH
            # Rustboro), or Rusturf Tunnel (the Devon errand). Route 116 was the miss —
            # a save mid-catching there re-ran the Woods travel and derailed.
            cur = _cur_map()
            if cur is None:
                return _done("BADGE01_GET")
            return (
                cur == rustboro
                or cur[0] == 11
                or cur == route116
                or cur == rusturf
                or _done("BADGE01_GET")
            )

        if _in_rustboro():
            console.print("[dim]Story: already in Rustboro — skipping the Woods travel.[/]")
        elif _cur_map() == woods:
            console.print("[cyan]Story: resuming inside Petalburg Woods — finishing the crossing.[/]")
            yield from cross_petalburg_woods()
            yield from travel_route104_north_to_rustboro()
        else:
            yield from travel_to_petalburg_woods()
            yield from cross_petalburg_woods()
            yield from travel_route104_north_to_rustboro()
        _guard("Route 104 → Rustboro", _in_rustboro)

        # --- Segment 4: Gym 1 — Roxanne (Stone Badge). Train the team to a sensible
        #     level FIRST (threshold ≈ boss ace + margin, plus a retrain if we've
        #     already lost here — user directive 2026-07-21). ---
        if not _done("BADGE01_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import RUSTBORO_TRAINING_GRASS, catch_starter_team

            roxanne_fight = {
                "keys": [MapRSE.RUSTBORO_CITY_GYM.value, MapRSE.RUSTBORO_CITY.value],
                "band": (13, 17),  # user: team between Lv 13-17 before Roxanne
                "ace_types": ("Rock",), "ace_level": 15,  # Nosepass L15
                "grass": RUSTBORO_TRAINING_GRASS,
                "heal": PokemonCenter.RustboroCity,
            }
            # Build an organic team (catch new species) BEFORE training + the gym.
            yield from catch_starter_team(self._catch_team_target)
            yield from self._prepare_for_fight(roxanne_fight)
            yield from do_rustboro_gym()
        else:
            console.print("[dim]Story: Stone Badge already earned — Gym 1 skipped.[/]")
        _guard("Gym 1 (Roxanne)", lambda: _done("BADGE01_GET"))

        # --- Segment 5a: Devon Goods errand — chase the thief to Rusturf Tunnel and
        #     recover the goods (+ free Peeko). Completion: RECOVERED_DEVON_GOODS.
        #     (The return leg — Devon Corp president → PokéNav — and the Rustboro
        #     rival are the next build; see design §Ch5.) ---
        if not _done("RECOVERED_DEVON_GOODS"):
            yield from recover_devon_goods()
        else:
            console.print("[dim]Story: Devon Goods already recovered — skipping.[/]")
        _guard("Devon Goods (Rusturf Tunnel)", lambda: _done("RECOVERED_DEVON_GOODS"))

        # --- Segment 5b: return the goods to Mr. Stone → PokéNav + Letter → clear the
        #     forced PokéNav Match-Call tutorial → train → Rustboro rival.
        #     Completion signals: RECEIVED_POKENAV, then DEFEATED_RIVAL_RUSTBORO. ---
        if not _done("RECEIVED_POKENAV"):
            yield from return_devon_goods_and_get_pokenav()
        else:
            console.print("[dim]Story: PokéNav already received — skipping the Devon Corp errand.[/]")
        _guard("Devon Corp → PokéNav", lambda: _done("RECEIVED_POKENAV"))

        # Clear the forced PokéNav/Match-Call tutorial (Rustboro Scientist, fired from the
        # map ON_FRAME table while VAR_RUSTBORO_CITY_STATE==6). FAITHFUL path: actually call
        # Mr. Stone through the PokéNav app; falls back to a state-write to vanilla's exact
        # end-state when the renderer is off (headless) or the nav stalls
        # (handle_pokenav_match_call_tutorial). Completing it sets VAR_RUSTBORO_CITY_STATE=7,
        # which also arms the rival trigger.
        if get_event_var("RUSTBORO_CITY_STATE") < 7:
            yield from handle_pokenav_match_call_tutorial()

        # --- Segment 5c: Rustboro rival (south exit, y=53; gated on VAR_RUSTBORO_CITY_STATE==7,
        #     which the tutorial-clear set). This rival is TYPE-COUNTERED: a Mudkip start makes
        #     it lead a grass Grovyle vs our 4×-weak Marshtomp, so we (1) TRAIN to a rival band,
        #     (2) pick a MATCHUP-based lead (not lead-strongest), and (3) cap attempts so a
        #     thin team that can't win stops cleanly instead of looping forever. ---
        def _rustboro_rival_resolved() -> bool:
            # VANILLA TRUTH (decomp + live probe 2026-07-22): the RivalTrigger row
            # fires only at VAR_RUSTBORO_CITY_STATE==7 and the MEETING sets it to 8 —
            # win or LOSE there is no rematch (her talk script is just the Briney
            # hint), and progression does NOT require the win. Two batch runs hit
            # honest-Manual retry loops on a met-and-lost state before this was
            # understood. Resolved = beaten, or met-and-spent.
            if _done("DEFEATED_RIVAL_RUSTBORO"):
                return True
            try:
                from modules.memory import get_event_var

                return _done("MET_RIVAL_RUSTBORO") and get_event_var("RUSTBORO_CITY_STATE") >= 8
            except Exception:
                return False

        if not _rustboro_rival_resolved():
            # PER-RUN budget — `reset_per_run_state()` zeroes this at every run boundary.
            # It used to be a `getattr(self, ..., 0) + 1` on state that was only ever
            # initialised in `__init__`, which is why an endless batch went permanently
            # over cap on run 4 and never fought this rival again.
            self._rival_attempts += 1
            if self._rival_attempts > self.RIVAL_MAX_ATTEMPTS:
                context.message = (
                    f"Story: couldn't beat the Rustboro rival in {self.RIVAL_MAX_ATTEMPTS} tries "
                    "(likely underleveled / bad matchup) — handing to manual so you can level up."
                )
                console.print(f"[bold yellow]{context.message}")
                context.set_manual_mode()
                return
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                RUSTBORO_TRAINING_GRASS,
                _lead_best_matchup,
                train_team,
                heal_in_pokemon_center,
            )

            rival_fight = {
                "keys": [MapRSE.RUSTBORO_CITY.value],
                "band": (16, 19),  # rival ace ≈ Lv15-16; small margin (escalates on losses)
                "grass": RUSTBORO_TRAINING_GRASS,
                "heal": PokemonCenter.RustboroCity,
            }
            # (1) LEVEL FLOOR (user directive 2026-07-21): make sure EVERY party mon is at
            #     least Lv 10 before the rival — a thin L6-8 bench gets swept and whites us
            #     out. The floor escalates on retries so each attempt fields a stronger team.
            level_floor = 10 + 2 * (self._rival_attempts - 1)
            console.print(f"[cyan]Story: leveling the whole team to ≥ Lv {level_floor} before the rival…[/]")
            yield from train_team(level_floor, scope="whole",
                                  grass=RUSTBORO_TRAINING_GRASS, heal_center=PokemonCenter.RustboroCity)
            # (2) Ready the primary/near-band battlers (organic band training + loss escalation).
            yield from self._prepare_for_fight(rival_fight)
            # (3) Mudkip start -> rival leads a grass Grovyle: lead the mon that best resists Grass
            #     (NOT our 4×-weak Marshtomp). Taillow/Flying both resists Grass AND hits it 2×.
            yield from _lead_best_matchup(["Grass"])
            # (4) SAFE HEAL right before the fight (user directive) — enter at full HP.
            yield from heal_in_pokemon_center(PokemonCenter.RustboroCity)
            # (5) Fight. A loss whites out -> StoryMode recovery -> we re-enter here (attempt+1,
            #     higher floor) until RIVAL_MAX_ATTEMPTS, then stop cleanly. The rival re-engages
            #     correctly on retries now (fight_rustboro_rival no longer keys off the MET flag).
            yield from fight_rustboro_rival()
        else:
            console.print("[dim]Story: Rustboro rival already resolved (beaten, or met-and-lost — vanilla offers no rematch) — skipping.[/]")
        _guard("Rustboro rival (resolved)", _rustboro_rival_resolved)

        # --- Segment 6: sail to Dewford (Chapter 6). Rustboro → south onto Route 104 →
        #     back through Petalburg Woods (Route 104 is river-split) → south beach →
        #     Mr. Briney's cottage → talk (first sail = YES/NO) → sail cutscene → Dewford.
        #     sail_to_dewford is idempotent + keyed off the LIVE map, so a resume from
        #     anywhere along the route picks up mid-leg. Once the Dewford-arc flags
        #     (DELIVERED_STEVEN_LETTER / BADGE02) exist they gate this out for good. ---
        pre_sail_maps = (
            MapRSE.RUSTBORO_CITY.value,
            MapRSE.ROUTE104.value,
            MapRSE.PETALBURG_WOODS.value,
            MapRSE.ROUTE104_MR_BRINEYS_HOUSE.value,
        )
        if not _done("DELIVERED_STEVEN_LETTER") and not _done("BADGE02_GET"):
            # WHITELIST the pre-sail maps: "not in Dewford" is WRONG as a gate — a resume
            # from Route 106 / Granite Cave / the gym is already on the Dewford side, and
            # running the sail leg there marches off toward a cottage that can't be
            # reached (live-hit 2026-07-22: a Granite Cave derail re-entered the sail and
            # spun into Manual). Off-whitelist maps skip straight to the Dewford segments.
            if _cur_map() in pre_sail_maps:
                yield from sail_to_dewford()
                _guard("Sail to Dewford (Ch6)", lambda: _cur_map() == MapRSE.DEWFORD_TOWN.value)
            elif _cur_map() != MapRSE.DEWFORD_TOWN.value:
                console.print("[dim]Story: already on the Dewford side — sail leg skipped.[/]")

        # --- Segment 7a: Steven's Letter (Granite Cave, TM47). The story reason we came
        #     to Dewford — and Briney waits for it before offering the Slateport sail. ---
        if not _done("DELIVERED_STEVEN_LETTER"):
            yield from deliver_stevens_letter()
        else:
            console.print("[dim]Story: Steven's Letter already delivered — skipping Granite Cave.[/]")
        _guard("Steven's Letter (Granite Cave)", lambda: _done("DELIVERED_STEVEN_LETTER"))

        # --- Segment 7b: Gym 2 — Brawly (Knuckle Badge). Heal + Fighting-resistant lead
        #     (Taillow-class); floor-band only — Dewford has NO reachable training grass
        #     before Surf (Route 106 is surf-only, Granite Cave wilds are L6-10), so the
        #     natural post-rival team (≥L16) skips proactive grinding and the cave spot is
        #     the (slow but bounded) loss-escalation fallback. See design §Ch7. ---
        if not _done("BADGE02_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                GRANITE_CAVE_TRAINING_SPOT,
                _lead_best_matchup,
                heal_in_pokemon_center,
            )

            brawly_fight = {
                "keys": [MapRSE.DEWFORD_TOWN_GYM.value, MapRSE.DEWFORD_TOWN.value],
                "band": (14, 16),
                "ace_types": ("Fighting",), "ace_level": 19,  # Makuhita L19
                "grass": GRANITE_CAVE_TRAINING_SPOT,
                "heal": PokemonCenter.DewfordTown,
            }
            yield from self._prepare_for_fight(brawly_fight)
            # Training can END at the in-cave spin tile — thread the cave mouth first
            # or the direct heal plan-fails cross-warp ("not on connected maps") and
            # derail-loops to Manual (batch 20260722-182727: 3 of 5 runs died here).
            from modules.story.early_game import _exit_training_cave_if_inside

            yield from _exit_training_cave_if_inside()
            yield from heal_in_pokemon_center(PokemonCenter.DewfordTown)
            yield from _lead_best_matchup(["Fighting"])
            yield from do_dewford_gym()
        else:
            console.print("[dim]Story: Knuckle Badge already earned — Gym 2 skipped.[/]")
        _guard("Gym 2 (Brawly)", lambda: _done("BADGE02_GET"))

        # --- Segment 8a: sail Dewford → Slateport (Briney at the dock; Route 109 beach
        #     gauntlet; ends healed at the Slateport PC). Gated on being on the DEWFORD
        #     side (whitelist — see the Segment-6 lesson); a Slateport-side resume skips. ---
        dewford_side = (
            MapRSE.DEWFORD_TOWN.value,
            MapRSE.ROUTE106.value,
            MapRSE.GRANITE_CAVE_1F.value,
            MapRSE.GRANITE_CAVE_B1F.value,
            MapRSE.GRANITE_CAVE_B2F.value,
            MapRSE.GRANITE_CAVE_STEVENS_ROOM.value,
            MapRSE.ROUTE109.value,
        )
        cur = _cur_map()
        on_dewford_side = cur in dewford_side or (cur is not None and cur[0] == 3)  # group 3 = Dewford interiors
        if cur != MapRSE.SLATEPORT_CITY.value:
            if on_dewford_side:
                yield from sail_to_slateport()
                _guard("Sail to Slateport (Ch8a)", lambda: _cur_map() == MapRSE.SLATEPORT_CITY.value)
            else:
                console.print("[dim]Story: not on the Dewford side — Slateport sail skipped.[/]")

        # --- Segment 8b: Devon Goods → Capt. Stern (Oceanic Museum). KI-11 RESOLVED
        #     (2026-07-22, walkthrough + decomp): the museum entrance is grunt-sealed until
        #     you visit Stern's Shipyard and talk to Dock (sets FLAG_HIDE_SLATEPORT_CITY_
        #     TEAM_AQUA) — `deliver_devon_goods_to_stern` now does that first. Two
        #     un-fleeable grunt battles inside the scene (attack-through strategy); the
        #     scene heals the party and removes the Route 110 blockade for Ch9. ---
        museum_maps = (
            MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_1F.value,
            MapRSE.SLATEPORT_CITY_OCEANIC_MUSEUM_2F.value,
        )
        # Also (re-)enter the segment when RESUMING INSIDE the museum with the flag
        # already set (e.g. the stern_done checkpoint is captured on 2F the moment the
        # flag lands, before the exit legs) — the function then skips straight to its
        # museum-exit legs. Without this, a city-target heal from inside the museum
        # plan-fails ("not on connected maps") and derails to Manual (live-hit ch9_run1).
        if not _done("DELIVERED_DEVON_GOODS") or _cur_map() in museum_maps:
            yield from deliver_devon_goods_to_stern()
        else:
            console.print("[dim]Story: Devon Goods already delivered — museum skipped.[/]")
        _guard("Devon Goods → Capt. Stern (Ch8b)", lambda: _done("DELIVERED_DEVON_GOODS"))

        # --- Segment 9a: the Route 110 rival (mandatory choke-point; §Ch9). Heal + a
        #     type-aware lead first: the rival's ACE counters OUR starter (Mudkip start →
        #     their Grovyle/Grass; Torchic → Marshtomp/Water; Treecko → Combusken/Fire). ---
        # NOTE (2026-07-22): the rival's completion signal is VAR_ROUTE110_STATE >= 1 —
        # vanilla sets NO named flag here; "DEFEATED_RIVAL_ROUTE_110" was a phantom name
        # that silently read False forever and derail-looped this segment (run 5).
        from modules.story.early_game import route110_rival_beaten

        if not route110_rival_beaten():
            from modules.map_data import PokemonCenter
            from modules.story.early_game import _lead_best_matchup, heal_in_pokemon_center

            ace_type = "Grass"
            try:
                from modules.pokemon_party import get_party as _gp

                names = " ".join(p.species.name for p in _gp() if p is not None)
                if any(s in names for s in ("Torchic", "Combusken", "Blaziken")):
                    ace_type = "Water"
                elif any(s in names for s in ("Treecko", "Grovyle", "Sceptile")):
                    ace_type = "Fire"
            except Exception:
                pass
            yield from heal_in_pokemon_center(PokemonCenter.SlateportCity)
            yield from _lead_best_matchup([ace_type])
            yield from travel_route110_and_fight_rival()
        else:
            console.print("[dim]Story: Route 110 rival already beaten — skipping.[/]")
        _guard("Route 110 rival (Ch9a)", route110_rival_beaten)

        # --- Segment 9b: Mauville — Wally unblocks the gym door. ---
        if not _done("DEFEATED_WALLY_MAUVILLE"):
            yield from fight_wally_mauville()
        else:
            console.print("[dim]Story: Wally already beaten at Mauville — skipping.[/]")
        _guard("Wally at Mauville (Ch9b)", lambda: _done("DEFEATED_WALLY_MAUVILLE"))

        # --- Segment 9c: Gym 3 — Wattson (Dynamo Badge). PREP FIRST (KI-13: the maze
        #     solver was validated in run 10 but the unprepped team lost 8 straight
        #     challenges): band-train at Route 110's north grass, then an Electric-
        #     resistant lead (Marshtomp/Ground is immune), then a safe heal. The
        #     switch maze itself is solved by the live-grid solver. ---
        if not _done("BADGE03_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                ROUTE117_TRAINING_GRASS,
                _lead_best_matchup,
                heal_in_pokemon_center,
            )

            wattson_fight = {
                "keys": [MapRSE.MAUVILLE_CITY_GYM.value, MapRSE.MAUVILLE_CITY.value],
                "band": (20, 24),  # Wattson: Voltorb 20 / Electrike 20 / Magneton 22 / Manectric 24
                "ace_types": ("Electric",), "ace_level": 24,  # Manectric L24
                "grass": ROUTE117_TRAINING_GRASS,
                "heal": PokemonCenter.MauvilleCity,
            }
            yield from self._prepare_for_fight(wattson_fight)
            yield from _lead_best_matchup(["Electric"])
            yield from heal_in_pokemon_center(PokemonCenter.MauvilleCity)
            yield from do_mauville_gym()
        else:
            console.print("[dim]Story: Dynamo Badge already earned — Gym 3 skipped.[/]")
        _guard("Gym 3 (Wattson)", lambda: _done("BADGE03_GET"))

        # --- Segment 10a: HM06 Rock Smash (Mauville SE house; §Ch10). Gated only on
        #     the received flag; field use needs BADGE03, which Segment 9c earned. ---
        if not _done("RECEIVED_HM_ROCK_SMASH"):
            from modules.story.early_game import get_rock_smash_hm

            yield from get_rock_smash_hm()
        else:
            console.print("[dim]Story: HM06 Rock Smash already received — skipping.[/]")
        _guard("HM06 Rock Smash (Ch10a)", lambda: _done("RECEIVED_HM_ROCK_SMASH"))

        # --- Segment 10b: teach Rock Smash to a VALIDATED learner (user directive
        #     2026-07-23): pick the highest-level party mon that can actually learn it
        #     (the party menu shows an incompatible mon as NOT ABLE and refuses the
        #     selection — the old highest-level pick loops there). If nobody in the
        #     party qualifies, ensure_hm_learner hunts an accessible learner species
        #     (data-driven from the ROM's encounter tables + TM/HM learnsets) and
        #     catches one first. Seed of the HM-slave logic (#24-hm-slaves). ---
        def _party_knows_rock_smash() -> bool:
            try:
                from modules.pokemon_party import get_party as _gp

                return any(
                    learned is not None and learned.move.name == "Rock Smash"
                    for mon in _gp()
                    if mon is not None and not mon.is_egg
                    for learned in mon.moves
                )
            except Exception:
                return False

        if not _party_knows_rock_smash():
            from modules.items import get_item_by_name
            from modules.story.early_game import ensure_hm_learner, teach_hm_move

            _hm06 = get_item_by_name("HM06")
            _slot = yield from ensure_hm_learner(_hm06)
            yield from teach_hm_move(_hm06, _slot)
        else:
            console.print("[dim]Story: someone already knows Rock Smash — teach skipped.[/]")
        _guard("Teach Rock Smash (Ch10b)", _party_knows_rock_smash)

        # --- Segment 10c: Route 111 south (smash the rocks) → Fiery Path → Route 113
        #     → Fallarbor, ending healed at its PC (§Ch10 route spec). ---
        from modules.story.early_game import travel_to_fallarbor

        # ORIGIN-side whitelist (the Segment-6 travel-gate lesson): run the travel only
        # when we're actually on the PRE-Fallarbor side — a resume from R114/Meteor
        # Falls or beyond must NOT backtrack (run 2026-07-22 overnight tried to walk
        # Route 114 → Route 111 and plan-failed to Manual).
        pre_fallarbor = (
            MapRSE.MAUVILLE_CITY.value,
            MapRSE.MAUVILLE_CITY_GYM.value,
            MapRSE.MAUVILLE_CITY_POKEMON_CENTER_1F.value,
            MapRSE.MAUVILLE_CITY_HOUSE1.value,
            MapRSE.ROUTE110.value,
            MapRSE.ROUTE111.value,
            MapRSE.ROUTE112.value,
            MapRSE.FIERY_PATH.value,
            MapRSE.ROUTE113.value,
        )
        # ALSO progress-gated: the corridor maps (R111/R112/Fiery/R113) are shared by
        # the LATER Fallarbor→Cable-Car return trip, so a mid-return derail would
        # re-trigger this travel on maps alone (seen 2026-07-22 overnight: it then
        # "shortcut" into the Go-Goggles-gated desert and plan-failed). Once Ch11a's
        # flag exists, the Fallarbor trip already happened — never travel again.
        if _cur_map() in pre_fallarbor and not _done("HIDE_ROUTE_112_TEAM_MAGMA"):
            yield from travel_to_fallarbor()
        else:
            console.print("[dim]Story: Fallarbor travel not applicable from here — skipped.[/]")
        _guard(
            "Fallarbor travel resolved (Ch10c)",
            lambda: _cur_map() not in pre_fallarbor or _done("HIDE_ROUTE_112_TEAM_MAGMA"),
        )

        # --- Segment 11a: the Meteor Falls Magma cutscene (unblocks the Cable Car). ---
        from modules.story.early_game import do_meteor_falls_scene

        if not _done("HIDE_ROUTE_112_TEAM_MAGMA"):
            yield from do_meteor_falls_scene()
        else:
            console.print("[dim]Story: Meteor Falls scene already done — skipping.[/]")
        _guard("Meteor Falls scene (Ch11a)", lambda: _done("HIDE_ROUTE_112_TEAM_MAGMA"))

        # --- Segment 11b: Cable Car → Mt. Chimney Magma chain (Maxie) + meteorite.
        #     Prep: heal + water-favoring lead (Camerupt ace is 4× to Water). ---
        from modules.story.early_game import do_jagged_descent, do_mt_chimney

        if not _done("DEFEATED_EVIL_TEAM_MT_CHIMNEY"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import _lead_best_matchup, heal_in_pokemon_center

            yield from heal_in_pokemon_center(PokemonCenter.FallarborTown)
            yield from _lead_best_matchup(["Fire", "Poison"])
            yield from do_mt_chimney()
        else:
            console.print("[dim]Story: Mt. Chimney already cleared — skipping.[/]")
        _guard("Mt. Chimney (Ch11b)", lambda: _done("DEFEATED_EVIL_TEAM_MT_CHIMNEY"))

        # --- Segment 11c: Jagged Pass down to Lavaridge (heal = arrival). ---
        # Run whenever we're not yet at/past Lavaridge: do_jagged_descent now handles
        # BOTH origins — descend when on the mountain, and re-ride the cable car up
        # first when a mid-descent whiteout stranded us below (user's 2026-07-23 run).
        # ‼ The guard checks we actually REACHED Lavaridge (or already earned the Heat
        # Badge) — the old "off the mountain" guard falsely PASSED at the Fallarbor
        # respawn, so Flannery then ran from the wrong town and derailed.
        _at_or_past_lavaridge = lambda: _cur_map() == MapRSE.LAVARIDGE_TOWN.value or _done("BADGE04_GET")
        if not _at_or_past_lavaridge():
            yield from do_jagged_descent()
        else:
            console.print("[dim]Story: already at Lavaridge — Jagged descent skipped.[/]")
        _guard("Jagged descent resolved (Ch11c)", _at_or_past_lavaridge)

        # --- Segment 11d: Gym 4 — Flannery (Heat Badge). The trapdoor maze is solved
        #     from the ROM's map data (holes / geysers / jump-south ledges — see
        #     do_lavaridge_gym), so no hole-guessing remains.
        #     NO pre-grind here, deliberately: a two-way pathability sweep from
        #     Lavaridge (tools/story-dev/jaggedgrass_probe.py) found NO usable training
        #     grass — Jagged Pass cannot be re-entered from the town (one-way ledges)
        #     and Route 112's lower grass has no return path. Teams reach Lavaridge at
        #     L28-29 and Flannery's ace is L29, so we prep the cheap way: a WATER lead
        #     (all four of her mons are 2x to Water) and a full heal. If this proves
        #     thin in batches, the fix is a swept Lavaridge-area tile (#24-trainmap),
        #     not a blind grind target. ---
        if not _done("BADGE04_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                _lead_best_matchup,
                do_lavaridge_gym,
                heal_in_pokemon_center,
            )

            yield from _lead_best_matchup(["Fire"])
            yield from heal_in_pokemon_center(PokemonCenter.LavaridgeTown)
            yield from do_lavaridge_gym()
        else:
            console.print("[dim]Story: Heat Badge already earned — Gym 4 skipped.[/]")
        _guard("Gym 4 (Flannery)", lambda: _done("BADGE04_GET"))

        # --- Segment 12a: the long overland backtrack Lavaridge → Petalburg (§Ch12
        #     build spec; route static-probed 2026-07-24 — direct via Route 111 south,
        #     the desert is never on the path; the Rusturf wall opens via the Wanda
        #     quest's two Rock Smash rocks). ---
        from modules.story.early_game import do_petalburg_gym, travel_lavaridge_to_petalburg

        _at_petalburg = lambda: _cur_map() in (
            MapRSE.PETALBURG_CITY.value,
            MapRSE.PETALBURG_CITY_GYM.value,
            MapRSE.PETALBURG_CITY_POKEMON_CENTER_1F.value,
            MapRSE.PETALBURG_CITY_WALLYS_HOUSE.value,
            MapRSE.PETALBURG_CITY_MART.value,
        )
        if not _at_petalburg() and not _done("RECEIVED_HM_SURF"):
            yield from travel_lavaridge_to_petalburg()
        else:
            console.print("[dim]Story: already Petalburg-side (or Surf in hand) — travel skipped.[/]")
        _guard("Travel to Petalburg (Ch12a)", lambda: _at_petalburg() or _done("RECEIVED_HM_SURF"))

        # --- Segment 12b: Gym 5 — Norman (Balance Badge) + the HM03 Surf handoff.
        #     Slaking L31 (TRUANT) is the ace; attack-through + a Normal-answering
        #     lead. Route 102 grass is L3-4 fodder, so the sufficiency gate /
        #     boss-training telemetry owns the prep decision. ---
        if not _done("RECEIVED_HM_SURF"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import (
                PETALBURG_TRAINING_GRASS,
                _lead_best_matchup,
                heal_in_pokemon_center,
            )

            norman_fight = {
                "keys": [MapRSE.PETALBURG_CITY_GYM.value, MapRSE.PETALBURG_CITY.value],
                "band": (27, 31),  # Norman: Spinda 27 / Vigoroth 27 / Linoone 29 / Slaking 31
                "ace_types": ("Normal",), "ace_level": 31,  # Slaking L31 (Truant)
                "grass": PETALBURG_TRAINING_GRASS,
                "heal": PokemonCenter.PetalburgCity,
            }
            # Prep/heal only when OUTSIDE the gym: a mid-gym derail resume must walk
            # straight back up the (still-open) doors, not leave for the PC —
            # ch12_run3 looped to Manual healing from inside (pre the warp-aware
            # heal fix; the gate also spares pointless PC round-trips).
            if _cur_map() != MapRSE.PETALBURG_CITY_GYM.value:
                yield from self._prepare_for_fight(norman_fight)
                yield from _lead_best_matchup(["Normal"])
                yield from heal_in_pokemon_center(PokemonCenter.PetalburgCity)
            yield from do_petalburg_gym()
        else:
            console.print("[dim]Story: Surf already received — Gym 5 skipped.[/]")
        _guard("Gym 5 + Surf handoff (Ch12b)", lambda: _done("RECEIVED_HM_SURF"))

        # --- Segment 12c: teach Surf (Marshtomp is the natural carrier); the whole
        #     Ch13+ water arc (Route 118, Weather Institute, Fortree) needs it. ---
        def _party_knows_surf() -> bool:
            try:
                from modules.pokemon_party import get_party as _gp

                return any(
                    learned is not None and learned.move.name == "Surf"
                    for mon in _gp()
                    if mon is not None and not mon.is_egg
                    for learned in mon.moves
                )
            except Exception:
                return False

        if not _party_knows_surf():
            from modules.items import get_item_by_name
            from modules.story.early_game import ensure_hm_learner, teach_hm_move

            _hm03 = get_item_by_name("HM03")
            _slot = yield from ensure_hm_learner(_hm03)
            yield from teach_hm_move(_hm03, _slot)
        else:
            console.print("[dim]Story: someone already knows Surf — teach skipped.[/]")
        _guard("Teach Surf (Ch12c)", _party_knows_surf)

        # --- Segment 13a: the Surf arc — Mauville → Route 118 (Surf) → Route 119 →
        #     Weather Institute → rival (HM02 Fly) → Fortree (§Ch13 spec, flags
        #     audited; ⚠ SKELETON built 2026-07-24 overnight — the Surf crossing and
        #     interior tiles are first-run-validate leads, expect iteration). ---
        from modules.story.early_game import (
            do_weather_institute,
            fight_route119_rival_and_get_fly,
            travel_to_fortree,
        )

        _r119_cleared = lambda: _done("HIDE_ROUTE_119_TEAM_AQUA")
        if not _r119_cleared() or not _done("RECEIVED_HM_FLY"):
            # Travel runs first; if Route 119's content interrupts it (institute /
            # rival not yet done), the dedicated segments below own their pieces
            # from wherever the navigation stopped.
            if _cur_map() not in (MapRSE.ROUTE119.value, MapRSE.FORTREE_CITY.value):
                yield from travel_to_fortree()
            if not _r119_cleared():
                yield from do_weather_institute()
            _guard("Weather Institute (Ch13b)", _r119_cleared)
            if not _done("RECEIVED_HM_FLY"):
                yield from fight_route119_rival_and_get_fly()
            _guard("Route 119 rival / HM02 Fly (Ch13c)", lambda: _done("RECEIVED_HM_FLY"))
            yield from travel_to_fortree()
        else:
            console.print("[dim]Story: Route 119 already cleared — heading to Fortree.[/]")
            yield from travel_to_fortree()
        _guard(
            "Travel to Fortree (Ch13a)",
            lambda: _cur_map() in (
                MapRSE.FORTREE_CITY.value,
                MapRSE.FORTREE_CITY_POKEMON_CENTER_1F.value,
                MapRSE.FORTREE_CITY_GYM.value,
                MapRSE.ROUTE120.value,  # a 13d resume (Steven) is Fortree-side too
            ),
        )

        # --- Segments 13d/13e: Devon Scope (Route 120 Steven) → Fortree Gym
        #     (Winona, BADGE06). ⚠ SKELETONS (2026-07-24 overnight) — tiles probed,
        #     scenes first-run-validate. ---
        from modules.story.early_game import (
            _leave_route120_north_bridge,
            do_fortree_gym,
            get_devon_scope,
        )

        # A resume with the Scope already set skips get_devon_scope; if that resume
        # lands on the Route 120 bridge, escape it before ANY navigation (the gym
        # prep heal would otherwise NO-PATH to the Fortree PC — ch13_run14).
        yield from _leave_route120_north_bridge()

        # ‼ TWO JOBS, TWO FLAGS (2026-07-24 — caught by the post-fix Ch13d validation run).
        # get_devon_scope() does TWO things: (1) get the Scope from Steven, and (2) FLUSH the
        # Fortree gym-path Kecleon. Gating the call on RECEIVED_DEVON_SCOPE alone meant any
        # resume that already had the Scope — including EVERY derail recovery near Fortree,
        # since recovery re-runs this resume — skipped the flush too. The Kecleon then still
        # occupies (25,8), the single chokepoint tile to the gym door, and do_fortree_gym
        # NO-PATHs to (22,11) forever ("Could not find a path from (5/7 @ FORTREE_CITY)").
        # The validation run derailed 5 times on exactly this. Both sub-steps are already
        # idempotent inside get_devon_scope (it checks _have_scope() and _city_kecleon_present()
        # separately), so calling it whenever EITHER job is outstanding is safe and correct.
        _kecleon_flushed = _done("HIDE_FORTREE_CITY_KECLEON")
        if not _done("RECEIVED_DEVON_SCOPE") or not _kecleon_flushed:
            yield from get_devon_scope()
        else:
            console.print("[dim]Story: Devon Scope in the bag and the Kecleon already flushed.[/]")
        _guard("Devon Scope (Ch13d)", lambda: _done("RECEIVED_DEVON_SCOPE"))
        _guard("Fortree Kecleon flush (Ch13d)", lambda: _done("HIDE_FORTREE_CITY_KECLEON"))

        if not _done("BADGE06_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import _lead_best_matchup, heal_in_pokemon_center

            # ‼ WINONA MUST GO THROUGH _prepare_for_fight (KI-23, 2026-07-25). She previously
            # jumped straight to `do_fortree_gym()` with only a lead-swap and a heal, so she
            # never entered the prep/boss-training machinery at ALL — which meant the
            # non-convergence guard could not fire on the ONE boss that proved it was needed.
            # A user's overnight run made 198 attempts, lost 41 times and whited out 41 times
            # against her with a party that was far ABOVE her levels but had no
            # super-effective answer to Flying (Sceptile is resisted, Ninjask is itself part
            # Flying, Shedinja has 1 HP). Wiring her in gives that run a bounded, diagnosed
            # stop instead of an unbounded whiteout loop.
            #   `ace_types`: Altaria L33 is the ace — Dragon/Flying, and 4x weak to Ice.
            #   `grass`/`heal`: Route 119 is the Fortree-side band; Fortree has the PC.
            winona_fight = {
                "name": "Winona",
                "keys": [MapRSE.FORTREE_CITY_GYM.value, MapRSE.FORTREE_CITY.value],
                "band": (29, 33),  # Swablu 29 / Tropius 29 / Pelipper 30 / Skarmory 31 / Altaria 33
                "ace_types": ("Dragon", "Flying"), "ace_level": 33,
                "heal": PokemonCenter.FortreeCity,
            }
            if _cur_map() != MapRSE.FORTREE_CITY_GYM.value:
                yield from self._prepare_for_fight(winona_fight)
            yield from _lead_best_matchup(["Flying"])
            yield from heal_in_pokemon_center(PokemonCenter.FortreeCity)
            yield from do_fortree_gym()
        else:
            console.print("[dim]Story: Feather Badge already earned — Gym 6 skipped.[/]")
        _guard("Gym 6 (Winona)", lambda: _done("BADGE06_GET"))

        # END OF BUILT CONTENT. Next build (Ch14): Route 121 → Mt. Pyre exterior →
        # Magma Emblem → Jagged Pass hideout → Maxie (§Ch12+ leads — decomp-verify,
        # audit_flag_names, and probe every tile before wiring).
        context.message = (
            "Story: FEATHER BADGE earned - end of built content. "
            "NEXT (WIP): Mt. Pyre and the Magma hideout. Handing to manual."
        )
        console.print(f"[bold green]{context.message}")
        # ‼ Mark a GENUINE completion. Both this path and the give-up paths call
        # `set_manual_mode()` and return normally, so the endless loop cannot tell them
        # apart from the outside — and without this flag it would relabel real successes
        # as "stopped" (P2 run 1 of bundle `20260726-231412` reached exactly here and
        # earned the Feather Badge).
        self._reached_end_of_content = True
        context.set_manual_mode()
        return


def _log_story_event(message: str, category: str = "STORY") -> None:
    """Mirror a console decision into the DEBUG LOG.

    ‼ `console.print` and `modules/debug_logger.py` are SEPARATE STREAMS — the debug logger
    never sees console output. Any decision that only reaches the console is invisible in the
    artefact people actually share for review. Bitten three times now: the training-relocation
    rule banner, the relocation decision itself, and the after-faint chooser's filter state.
    If a decision matters to a reviewer, it goes through here as well.
    """
    try:
        from modules import debug_logger

        debug_logger.event(message, category=category)
    except Exception:  # noqa: BLE001 - logging must never end a run
        pass


#: Set to "0" to leave emulation speed/video exactly as the GUI or CLI configured them.
#: Anything else (or unset) applies the debug-run config below.
_TURBO_ENV = "POKEBOT_STORY_DEBUG_TURBO"


def _apply_debug_emulation_config() -> None:
    """Give a SINGLE-LANE debug Story run the same emulation config an x4 lane gets.

    ‼ WHY (user directive 2026-07-29): the user cannot run ENDLESS LOOP x4 on their work
    machine — it lacks the power for four emulators — but x4 lanes are configured far better
    for test runs than a hand-launched single bot, and they get there automatically:

        modules/endless_x4.py:160   "-s", "0",   # unthrottled, as requested
        modules/gui/tile_child.py:84  context.video = True  # REQUIRED

    A hand-launched debug run inherited whatever the GUI happened to have — the
    `20260729-122709` log shows `speed=1 video=True`, i.e. throttled, which made a
    2.78M-frame run take hours. So the debug modes now configure themselves.

    ‼ VIDEO IS FORCED **ON**, AND THAT IS DELIBERATE — it is what makes the FAITHFUL path
    work. The PokéNav Match-Call tutorial only advances with the renderer on; run
    `20260729-122709` (video=True) played it faithfully with no state-write fallback, while
    the user's earlier video-off runs fell back 8 times out of 9.

    ‼ THIS SUPERSEDES the 2026-07-26 "SPEED ONLY — NEVER TOUCH `context.video`" directive,
    and the distinction matters. That rule was written because the endless loop used to
    CAPTURE video at batch start and RE-PIN it every run — so a batch begun with video off
    kept it off for ever, silently degrading the faithful path. The harm was PINNING TO AN
    ARBITRARY VALUE, not writing the field. Forcing it ON, once, is the opposite: it is the
    value the faithful path requires, and it is what x4 already does.
    Ruling recorded in `06-DECISIONS-LOG.md` 2026-07-29.

    Escape hatch: `POKEBOT_STORY_DEBUG_TURBO=0` leaves both settings untouched. The resulting
    values are printed in every debug log's RUN HEADER (`emulation: speed=… video=…`), so
    there is never any doubt about what was applied.
    """
    import os

    from modules.console import console

    if os.environ.get(_TURBO_ENV, "1").strip().lower() in ("0", "false", "no", "off"):
        console.print(f"[dim]Story (DEBUG): {_TURBO_ENV}=0 — leaving speed/video as configured.[/]")
        return
    try:
        if context.emulation_speed != 0:
            context.emulation_speed = 0
        if not context.video:
            context.video = True
        console.print("[dim]Story (DEBUG): emulation set to unthrottled + video ON "
                      "(matches an x4 lane; POKEBOT_STORY_DEBUG_TURBO=0 to opt out).[/]")
    except Exception:  # noqa: BLE001 - never let a display setting stop a run
        pass


class StoryDebugMode(StoryMode):
    """"Story (DEBUG)" (user request 2026-07-22): exactly Story, but with the opt-in
    Debug Logging switched ON automatically at start. Runs from ANY point — the title
    screen, a loaded save, or mid-route — via Story's native segmented resume (flags +
    position); nothing else differs. Exists to make real-hardware test runs one click."""

    @staticmethod
    def name() -> str:
        return "Story (DEBUG)"

    def run(self):
        _apply_debug_emulation_config()
        try:
            from modules import debug_logger
            from modules.console import console

            path = debug_logger.enable()
            console.print(f"[bold cyan]Story (DEBUG): debug logging ON -> {path}[/]")
        except Exception:
            pass
        yield from super().run()


class StoryDebugResetMode(StoryMode):
    """"Story (DEBUG - RESET)" (user request 2026-07-22): debug logging ON, then a HARD
    EMULATOR RESET to the title screen, then Story from scratch — and NEW GAME is selected
    explicitly even when a save file exists (the plain intro's A-mash would pick CONTINUE,
    which sits on top of the main menu whenever there is a save). The existing save file is
    NOT erased by this — Emerald only overwrites it if/when the game saves in-game later.
    Exists to make fresh-run testing one click."""

    @staticmethod
    def name() -> str:
        return "Story (DEBUG - RESET)"

    def run(self):
        from modules.console import console
        from modules.memory import read_symbol
        from modules.modes import BotModeError
        from modules.modes.util.sleep import wait_for_n_frames
        from modules.tasks import task_is_active

        _apply_debug_emulation_config()
        try:
            from modules import debug_logger

            path = debug_logger.enable()
            console.print(f"[bold cyan]Story (DEBUG - RESET): debug logging ON -> {path}[/]")
        except Exception:
            pass

        # Hard reset to the boot screen. (State after this: copyright/intro -> title.)
        context.emulator.reset()
        yield

        # Drive to the MAIN MENU (bounded): A skips the copyright/intro/title screens.
        frames = 0
        while not task_is_active("Task_HandleMainMenuInput"):
            if frames % 4 == 0:
                context.emulator.press_button("A")
            frames += 1
            if frames > 3000:
                raise BotModeError("DEBUG-RESET: never reached the main menu after reset.")
            yield

        # With a save on file the menu is CONTINUE / NEW GAME / ... with the cursor on
        # CONTINUE — one Down puts it on NEW GAME. Without a save, NEW GAME is already on
        # top and pressing Down would select OPTION instead, so only move when a save
        # exists (gSaveFileStatus == 1 means SAVE_STATUS_OK, set by the menu itself).
        save_ok = False
        try:
            save_ok = int.from_bytes(read_symbol("gSaveFileStatus", size=2), "little") == 1
        except Exception:
            pass
        if save_ok:
            console.print("[cyan]Story (DEBUG - RESET): save file present — selecting NEW GAME explicitly.[/]")
            yield from wait_for_n_frames(10)
            context.emulator.press_button("Down")
            yield
            yield from wait_for_n_frames(6)

        # Hand over to Story: _play sees "at title / not started" and runs the intro,
        # whose A-mash now confirms the pre-selected NEW GAME.
        yield from super().run()


#: How many chained DEBUG-RESET runs "Story (ENDLESS RESET)" performs. 0 = run forever.
#: Set by the GUI's "Endless Debug-Reset Runs…" dialog before it selects the mode; defaults to
#: 10 so picking the mode straight from the dropdown still does something sensible.
ENDLESS_RESET_TARGET = 10

#: How many runs of the CURRENT batch have FINISHED. Read across the process boundary by
#: ENDLESS LOOP x4 (`modules/gui/tile_child.py`) so each tile can show its lane's run count
#: — a lane's progress is otherwise invisible from the dashboard, which has no access to a
#: child's `context`. Reset at batch start; purely informational, never a control input.
ENDLESS_RESET_COMPLETED = 0


class StoryEndlessResetMode(StoryDebugResetMode):
    """"Story (ENDLESS RESET)" (user request 2026-07-25): chained DEBUG-RESET runs, IN-PROCESS.

    ‼ WHY IN-PROCESS. The first attempt at this feature shelled out to
    `tools/story-dev/endless_runs.py` from a menu item; the dialogs appeared and nothing
    happened, because a separate headless harness is not what "endless debug reset runs" means.
    The user wants exactly what `Story (DEBUG - RESET)` already does — hard reset → NEW GAME →
    play the story — repeated back to back in THIS emulator: "effectively chained debug reset
    bots". So this mode just loops the parent's run().

    Each iteration ends when the story finishes (end of built content), derails with a
    `BotModeError`, or trips one of StoryMode's own bounds. `BotModeError` is SWALLOWED on
    purpose: a crash in run 3 must not cost runs 4..N of an overnight batch. The next run then
    begins with a hard reset, which is a clean slate by construction.

    Failsafes beyond the parent's:
      * a per-run FRAME CAP, so a run that neither finishes nor raises cannot hold the batch
        forever — StoryMode's global watchdog normally catches that, but not if the watchdog
        itself is what wedged;
      * the bot mode is forced back to this mode after every run, because a derail deep inside
        StoryMode can call `set_manual_mode()`, which would otherwise silently end the batch;
      * a per-run outcome line, so the console shows progress without opening a log.
    """

    #: Hard per-run frame cap, ENFORCED DURING the run (see `_run_with_frame_budget`).
    #:
    #: ‼ RAISED 3.5M -> 5M on 2026-07-29 (KI-35) BECAUSE IT WAS ABOUT TO KILL GOOD RUNS.
    #: The old value came with the note "the deepest real run to date reached the end of built
    #: content in ~2.24M frames, so this is ~1.5x headroom". Runs have since got much longer:
    #:     20260729-151635  3,058,007 frames — COMPLETED (six leaders incl. Winona, 462 wins)
    #:     20260727 bundle  3,117,110 / 3,063,506 / 2,946,810 / 2,932,778 — near-complete runs
    #: So a SUCCESSFUL run was using 87% of the cap and the real headroom was 1.14x, not 1.5x.
    #: One unluckier run — a few more heal round trips — and the budget would have terminated a
    #: winning run and reported it as wedged, throwing away exactly the data it exists to
    #: protect. 5M restores ~1.6x over the deepest observed run (3.12M).
    #:
    #: WHY RUNS GREW, measured in the same log: **78 heal round trips in one run**
    #: (Route 116<->Rustboro x34, Dewford<->Granite Cave x29, Route 117<->Mauville x15). With no
    #: potion layer every HP dip is a full Poké Center walk — `#24-provisions`. Expect to raise
    #: this again as more content is built, and re-derive it from the deepest COMPLETED run
    #: rather than guessing.
    #:
    #: ‼ Raising it is cheap NOW in a way it was not before: since KI-32, an in-battle wedge
    #: produces a STUCK dump (with the generator stack) after 18,000 frames, so the frame cap is
    #: no longer the only thing that notices a hang — it is just the thing that ENDS one. A
    #: wedge is diagnosed ~270x sooner than the cap fires.
    MAX_FRAMES_PER_RUN = 5_000_000

    @staticmethod
    def name() -> str:
        return "Story (ENDLESS RESET)"

    #: How often (in yields ~= frames) to re-check the per-run frame budget. The check is a
    #: single memory read; sampling keeps it free even at unthrottled speed.
    BUDGET_CHECK_INTERVAL = 2048

    def _run_with_frame_budget(self, inner, start_frame: int):
        """Drive the story generator, ENFORCING `MAX_FRAMES_PER_RUN` while it runs.

        ‼ WHY THIS EXISTS (user's x4 bundle `20260727-063751`). `MAX_FRAMES_PER_RUN` was
        only evaluated AFTER `super().run()` returned, so it could report a runaway run but
        never stop one — despite its own docstring promising "a run that neither finishes
        nor raises cannot hold the batch forever". In that bundle three of four lanes did
        exactly that, and the batch lost more than half its wall-clock to them:

          * P3 run 1 — HARD HUNG at the Weather Institute: `state=3 controllable=False`,
            position frozen at ROUTE 119(32,1) (10, 10), for **27 million frames / ~6.5 h**.
            Not one STUCK dump fired in that whole stretch, so the global watchdog never
            saw it either — the watchdog is exactly what wedged.
          * P1 run 7 — 19.9M frames spinning Route 103 and healing at Oldale, forever.
          * P2 run 35 — 13.4M frames doing the same on Route 116.
            (P1/P2 are LIVELOCKS, not hangs: they generate real encounters and battles, so
            no "no progress" detector can ever fire. Only a budget catches them.)

        P4 run 12 shows the old behaviour's other half: it did report `frame-cap
        (7,545,828 > 3,500,000)` — after burning more than twice the cap.

        The framework advances bot-mode generators with a bare `next()` (`modules/main.py`
        drives `context.controller_stack`), so stepping `inner` by hand is safe; there are
        no `send()` values to lose. `close()` is forwarded in a `finally` so a parked batch
        still unwinds the story generator cleanly.
        """
        from modules.modes import BotModeError

        budget_base = start_frame
        ticks = 0
        try:
            while True:
                try:
                    next(inner)
                except StopIteration:
                    return
                yield
                ticks += 1
                if ticks % self.BUDGET_CHECK_INTERVAL:
                    continue
                try:
                    now = context.emulator.get_frame_count()
                except Exception:
                    continue
                # The hard reset happens INSIDE the run, and `get_frame_count()` restarts
                # with the emulator — so the counter legitimately goes backwards early on.
                # Re-base instead of measuring a negative elapsed (the same trap that made
                # the old post-hoc cap silently unenforceable after a mid-run reset).
                if now < budget_base:
                    budget_base = 0
                elapsed = now - budget_base
                if elapsed > self.MAX_FRAMES_PER_RUN:
                    raise BotModeError(
                        f"per-run frame budget exhausted ({elapsed:,} > "
                        f"{self.MAX_FRAMES_PER_RUN:,}) — the run is wedged or looping; "
                        "resetting to the next run"
                    )
        finally:
            try:
                inner.close()
            except Exception:  # noqa: BLE001
                pass

    def run(self):
        from modules.console import console
        from modules.modes import BotModeError

        global ENDLESS_RESET_COMPLETED

        target = int(ENDLESS_RESET_TARGET)
        completed = 0
        ENDLESS_RESET_COMPLETED = 0
        outcomes: list[str] = []

        # ‼ CAPTURE AND RE-APPLY THE SPEED/VIDEO SETTINGS EVERY RUN (user report 2026-07-25:
        # "on its second run it was at normal speed, it should have been set to unlimited").
        # A derail calls `context.set_manual_mode()`, whose `enable_video_and_slow_down` default
        # sets `emulation_speed = 1` AND `video = True` (modules/context.py:128-139) — that is
        # correct for a human taking over, but it silently throttles the rest of an unattended
        # batch. The first version of this loop restored `bot_mode` and not the speed, so run 1
        # ran unthrottled and every run after it crawled at 1x. Remember what the batch STARTED
        # with and restore exactly that, rather than forcing a value the user did not choose.
        # ‼ SPEED ONLY — NEVER TOUCH `context.video` (user directive 2026-07-26).
        # This used to capture and re-apply `video` alongside the speed, which had two
        # bad effects. (1) It PINNED the renderer to whatever it was at batch start, so a
        # batch begun with video off kept it off for every subsequent run — and the
        # FAITHFUL PokéNav Match-Call tutorial only advances with the renderer ON, so it
        # silently degraded to the last-resort state-write fallback in **8 of 9** of the
        # user's real-hardware runs (#24-pokenav-faithful; the 1 success was a run whose
        # renderer was still on). (2) Worse, the `except` fell back to
        # `batch_video = False`, so a single failed read of `context.video` would force
        # the renderer OFF for the entire batch.
        # The SPEED restore stays — it fixes a real user report ("on its second run it was
        # at normal speed, it should have been set to unlimited"): a derail calls
        # `set_manual_mode()`, whose `enable_video_and_slow_down` default sets
        # `emulation_speed = 1`, which throttles the rest of an unattended batch.
        # Video is the user's to control; if they turn it on mid-batch it stays on.
        # ‼ APPLY THE DEBUG CONFIG **BEFORE** CAPTURING `batch_speed`. The capture below is
        # what every run's speed gets restored to after a `set_manual_mode()` drops it to 1x,
        # so if the config were applied afterwards the batch would be pinned to the OLD speed
        # and every run after the first would crawl — the exact 2026-07-25 bug this capture
        # was written to fix, reintroduced from the other direction.
        _apply_debug_emulation_config()
        try:
            batch_speed = context.emulation_speed
        except Exception:
            batch_speed = 0

        def _restore_speed() -> None:
            try:
                if context.emulation_speed != batch_speed:
                    context.emulation_speed = batch_speed
            except Exception:
                pass

        while target == 0 or completed < target:
            completed += 1
            label = f"{completed}/{'infinite' if target == 0 else target}"
            console.print(f"[bold cyan]=== ENDLESS RESET: starting run {label} ===[/]")
            # ‼ NAME THE EXPERIMENT IN THE LOG. An A/B whose variable is invisible in the
            # output is not an A/B — without this line a bundle gives no way to tell which
            # training-relocation rule produced it, and the comparison cannot be attributed
            # after the fact. Printed per run so it survives log rotation.
            try:
                from modules.story.training_areas import active_fodder_rule_banner

                _banner = active_fodder_rule_banner()
                console.print(f"[dim]{_banner}[/]")
                # ‼ ALSO INTO THE DEBUG LOG. `console.print` and the debug log are SEPARATE
                # STREAMS — `modules/debug_logger.py` never sees console output. The first
                # version of this banner printed to the console only, so a debug log (which
                # is what gets shared for review) carried NO record of which rule produced
                # it. A run's own log must be able to describe the run.
                try:
                    from modules import debug_logger

                    debug_logger.event(_banner, category="STORY")
                except Exception:  # noqa: BLE001
                    pass
            except Exception:  # noqa: BLE001 - a banner must never end a batch
                pass
            context.message = f"Endless reset: run {label}"
            start_frame = context.emulator.get_frame_count()
            # ‼ AUTHORITATIVE RUN BOUNDARY for the badge recorder. `modules/main.py` also
            # watches for the frame counter going backwards, but that proved unreliable —
            # the user's 2026-07-26 x4 bundle had P4 complete two runs with every badge
            # record still stamped `run_started_frame=0`. This mode KNOWS when a run
            # starts, so it says so, and per-run badge de-duplication becomes trustworthy.
            try:
                from modules import badge_log

                # `authoritative=True`: this mode KNOWS where its run boundaries are, so
                # main.py's frame-counter fallback must stand down. Without it both fired
                # and `run_index` advanced by two per run (1, 3, 5 … 37 across 19 runs).
                badge_log.reset_for_new_run(start_frame, authoritative=True)
            except Exception:
                pass
            # ‼ CLEAN SLATE PER RUN. Every counter scoped to one playthrough is zeroed
            # here. Without this the batch silently degrades: `_rival_attempts` hit its
            # cap of 3 after three runs and every later run gave up at the Rustboro rival
            # WITHOUT FIGHTING (P1: 16 of 20 runs), and `_defeat_counts` carried losses
            # forward so boss give-up thresholds tripped on borrowed defeats.
            # See `StoryMode.reset_per_run_state` for the measured evidence.
            self.reset_per_run_state()
            outcome = "finished"
            try:
                # The parent does the hard reset + NEW GAME, then hands to StoryMode.run().
                yield from self._run_with_frame_budget(super().run(), start_frame)
            except BotModeError as exc:
                outcome = f"derailed: {exc}"  # EXPECTED — never ends the batch
            except Exception as exc:  # noqa: BLE001
                outcome = f"crashed: {type(exc).__name__}: {exc}"
            else:
                # ‼ "finished" MUST MEAN FINISHED (user's x4 bundle `20260726-231412`).
                # `outcome` defaults to "finished" and only a raised BotModeError changed
                # it — but a derail deep inside StoryMode can instead call
                # `context.set_manual_mode()` and `return` normally. Every one of those
                # was reported as a SUCCESS: all 16 P1 "finished" runs in that bundle were
                # dead runs, several printed as "finished (0 frames)", and any summary of
                # the batch read ~80% success against a true ~20%. A run that handed
                # itself to Manual did not finish — say so.
                # ‼ The genuine end-of-content return ALSO calls set_manual_mode(), so the
                # mode flags a real completion explicitly — otherwise this would relabel
                # true successes as failures, which is the same crime in the other
                # direction. P2 run 1 of that bundle really did reach the Feather Badge.
                try:
                    handed_to_manual = context.bot_mode != self.name()
                except Exception:
                    handed_to_manual = False
                if handed_to_manual and not getattr(self, "_reached_end_of_content", False):
                    outcome = "stopped: handed to Manual mid-run (see the run's log for why)"
            # ‼ CLAMP. `get_frame_count()` is "frames since this emulation session began" and
            # it RESETS with the emulator, so if a reset happens inside a run this
            # subtraction goes negative — the user's 2026-07-26 20:18 bundle recorded
            # "finished (-959,198 frames)". A negative value also silently disabled the
            # MAX_FRAMES_PER_RUN wedge guard below, since nothing is ever > the cap.
            raw_frames = context.emulator.get_frame_count() - start_frame
            frames = raw_frames if raw_frames >= 0 else 0
            if raw_frames < 0:
                console.print(
                    "[yellow]=== ENDLESS RESET: the emulator reset mid-run, so this run's "
                    "frame count is unknown (reported as 0). ===[/]"
                )
            if frames > self.MAX_FRAMES_PER_RUN:
                outcome = f"frame-cap ({frames:,} > {self.MAX_FRAMES_PER_RUN:,})"
            outcomes.append(f"run {completed}: {outcome} ({frames:,} frames)")
            ENDLESS_RESET_COMPLETED = completed
            console.print(f"[cyan]=== ENDLESS RESET: run {label} -> {outcome} ({frames:,} frames) ===[/]")

            # A derail deep inside StoryMode can flip us to Manual; restore ourselves or the
            # next iteration runs under the wrong mode (or the batch just stops). Restore the
            # SPEED too — set_manual_mode() drops to 1x and turns video on, which is right for a
            # human but throttles an unattended batch for every remaining run.
            try:
                if context.bot_mode != self.name():
                    context.bot_mode = self.name()
            except Exception:
                pass
            _restore_speed()

        console.print("[bold green]=== ENDLESS RESET: batch complete ===[/]")
        for line in outcomes:
            console.print(f"  [green]{line}[/]")
        context.message = f"Endless reset: {completed} run(s) complete"
