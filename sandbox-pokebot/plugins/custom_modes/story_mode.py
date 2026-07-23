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

from typing import Generator

from modules.console import console
from modules.context import context
from modules.memory import GameState, game_has_started, get_game_state
from modules.modes import BattleAction, BotMode
from modules.battle_strategies import BattleStrategyUtil, TurnAction
from modules.battle_strategies.catch import CatchStrategy
from modules.battle_strategies.level_up import LevelUpLeadBattleStrategy


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
                return TurnAction.use_move(0)  # nothing usable → the game uses Struggle
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
            return TurnAction.use_move(0)  # nothing usable → the game uses Struggle
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
        return _default_target(0)  # nothing usable → the game uses Struggle

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


class StoryMode(BotMode):
    #: Pre-gym training only readies a battler that's already within this many levels
    #: of the target band; fresh catches further below are left to level organically
    #: rather than grinding them up via half-XP swap-training (user 2026-07-21).
    TRAIN_CATCHUP_GAP = 6

    #: How many times to (re)train + attempt the Rustboro rival before giving up and handing
    #: to manual — bounds the whiteout→retrain loop so an underleveled/bad-matchup team can't
    #: spin forever (each attempt escalates the training band via `_prepare_for_fight`).
    RIVAL_MAX_ATTEMPTS = 3

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
        # DEFEAT RECOVERY (user directive 2026-07-21). Consecutive losses are counted
        # per LOCATION (map) so repeated faints at the same obstacle mean a power/level
        # problem → trigger a retrain. These live on the instance and survive whiteout
        # restarts because run() loops in place (it does NOT bounce through Manual).
        self._defeat_counts: dict = {}
        self._whiteout_pending = False
        self._last_defeat_key = None
        self._derails = 0  # consecutive non-whiteout derails (self-correct before Manual)
        self._last_derail_sig = None  # progress fingerprint at the last derail (see run())
        # Organic team-building (user directive 2026-07-21): catch NEW species while
        # travelling to Gym 1 until the party has this many members (starter + helpers).
        self._catch_team_target = 4

    def on_battle_ended(self, outcome) -> None:
        from modules.battle_state import BattleOutcome

        if outcome is BattleOutcome.Lost:
            key = self._location_key()
            self._defeat_counts[key] = self._defeat_counts.get(key, 0) + 1
            self._last_defeat_key = key
            console.print(
                f"[yellow]Story: lost a battle at map {key} "
                f"(defeat #{self._defeat_counts[key]} here).[/]"
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

    def _prepare_for_fight(self, cfg: dict) -> Generator:
        """Before a major fight, train the team to a sensible level (user directive
        2026-07-21). PROACTIVE: a target within the fight's level band (organic,
        randomized). REACTIVE: if we've already LOST here ≥2 times, escalate the
        target and train harder before re-attempting — the "+levels" strategy and
        the team scope are both randomized to look human/organic."""
        import random

        from modules.pokemon_party import get_party
        from modules.story.early_game import train_team

        losses = max((self._defeat_counts.get(k, 0) for k in cfg["keys"]), default=0)
        lo, hi = cfg["band"]
        target = random.randint(lo, hi)  # organic proactive target within the band
        if losses >= 2:
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
        if need:
            console.print(
                f"[cyan]Story: prepping — training {len(need)} battler(s) to Lv {target} "
                f"(fresh low catches left to level organically).[/]"
            )
            yield from train_team(target, slots=to_train, grass=cfg["grass"], heal_center=cfg["heal"])
        else:
            console.print(f"[dim]Story: the team's battlers are already ≥ Lv {target} — no prep training.[/]")

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
                    try:
                        next(_play_gen)
                    except StopIteration:
                        return
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
        if not _done("DEFEATED_RIVAL_RUSTBORO"):
            self._rival_attempts = getattr(self, "_rival_attempts", 0) + 1
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
            console.print("[dim]Story: Rustboro rival already defeated — skipping.[/]")
        _guard("Rustboro rival", lambda: _done("DEFEATED_RIVAL_RUSTBORO"))

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

        # END OF BUILT CONTENT. Next build (Ch10b/c): teach HM06 → Route 111 south
        # (rocks) → Route 112 → Fiery Path → Route 113 → Fallarbor (§Ch10 route spec).
        context.message = (
            "Story: HM06 Rock Smash in hand — end of built content. NEXT (WIP): teach "
            "it, smash through Route 111, Fiery Path -> Fallarbor. Handing to manual."
        )
        console.print(f"[bold green]{context.message}")
        context.set_manual_mode()
        return


class StoryDebugMode(StoryMode):
    """"Story (DEBUG)" (user request 2026-07-22): exactly Story, but with the opt-in
    Debug Logging switched ON automatically at start. Runs from ANY point — the title
    screen, a loaded save, or mid-route — via Story's native segmented resume (flags +
    position); nothing else differs. Exists to make real-hardware test runs one click."""

    @staticmethod
    def name() -> str:
        return "Story (DEBUG)"

    def run(self):
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
