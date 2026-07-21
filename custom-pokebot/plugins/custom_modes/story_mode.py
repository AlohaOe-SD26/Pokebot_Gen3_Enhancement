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
from modules.battle_strategies.level_up import LevelUpLeadBattleStrategy


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
            move = util.get_strongest_move_against(
                battle_state.own_side.active_battler, battle_state.opponent.active_battler
            )
            if move is not None:
                return TurnAction.use_move(move)
        return super().decide_turn(battle_state)

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


class StoryMode(BotMode):
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

    def on_battle_started(self, encounter):
        # Story battles (the first Birch battle, training, the rival) are meant
        # to be FOUGHT and won with the default battle strategy — never run from
        # or auto-caught. The BattleListener handles the fight while run() pauses.
        #
        # SHINY CONTINGENCY: if the wild in the scripted first battle (or any
        # story battle) happens to be shiny — extremely rare — we must NOT try
        # to catch it and must NOT stop; the story has to progress normally.
        # Returning Fight guarantees this: the default "shiny → stop the bot"
        # logic lives in handle_encounter(), which the framework only calls when
        # on_battle_started returns None. By returning Fight we bypass it
        # entirely (and the first battle is a Tutorial encounter, which the
        # framework forces to CustomAction anyway — also no halt).
        try:
            if encounter is not None and encounter.is_shiny:
                from modules.console import console

                species = getattr(getattr(encounter, "pokemon", None), "species", None)
                name = getattr(species, "name", "Pokémon")
                console.print(
                    f"[bold yellow]Story Mode: a SHINY {name} appeared in a story "
                    f"battle — fighting through as normal (NOT catching, NOT "
                    f"stopping), per the contingency.[/]"
                )
                context.message = (
                    f"Story: a shiny {name} appeared in a story battle — fighting "
                    "through (not catching)."
                )
        except Exception:
            pass
        # Fight to WIN and level the lead (strongest move; flees only at low HP,
        # which the training loop covers by healing). The travel variant also
        # refuses to flee a TRAINER battle (single-mon party can't — see ML-8),
        # fighting on instead; used for training wilds, the rival, and route
        # trainers. The scripted first battle is a Tutorial (framework-handled).
        return LevelUpTravelBattleStrategy()

    def run(self) -> Generator:
        from modules.story import detect_live
        from modules.story.config import get_story_config
        from modules.story.intro import run_intro

        # --- Existing game already loaded: detect & report progress. --------
        if game_has_started() and get_game_state() is not GameState.TITLE_SCREEN:
            progress = detect_live()
            console.print("[bold cyan]Story Mode — detected progress:[/]")
            console.print(progress.summary())
            context.message = (
                f"Story: {progress.chapter_key} — {progress.chapter_name}. "
                "Chapter execution beyond the intro isn't built yet; back to manual."
            )
            # Chapter 0 here means we're already in-game but pre-adventure (e.g.
            # in the truck) — that's the end of what chunk 1 automates.
            context.set_manual_mode()
            return

        # --- Fresh boot (title/main menu): run the New Game intro. ----------
        cfg = get_story_config(context.profile.path)
        console.print(
            f"[bold cyan]Story Mode — new game[/] as [bold]{cfg.character_name}[/] "
            f"({cfg.gender}). Running the intro..."
        )
        yield from run_intro(cfg.character_name, cfg.gender)

        # --- Chapter 0 tail: step off the truck → Mom's greeting into the
        #     house → upstairs → set the wall clock. (Downstairs/Mom, Route 101,
        #     starter + first battle are WIP.) ------------------------------
        import random

        from modules.story.early_game import (
            descend_and_leave_players_house,
            do_petalburg_gym_and_wally_tutorial,
            finish_birch_lab,
            fight_route103_rival,
            go_upstairs_and_set_clock,
            help_birch_and_choose_starter,
            return_to_lab_and_get_pokedex,
            train_lead_to_level,
            travel_to_petalburg,
            travel_to_petalburg_woods,
            travel_to_route103,
            visit_rivals_house,
            walk_off_truck_and_into_house,
        )

        yield from walk_off_truck_and_into_house()
        yield from go_upstairs_and_set_clock()
        yield from descend_and_leave_players_house()
        yield from visit_rivals_house()
        yield from help_birch_and_choose_starter(cfg.starter)
        yield from finish_birch_lab(cfg.starter_nickname)

        # Head to Route 103 (training en route), grind the starter to a random
        # Lv 8-10, battle the rival, then return to Birch for the Pokédex.
        target_level = random.randint(8, 10)
        console.print(f"[cyan]Story: training the starter to Lv {target_level} before the rival.[/]")
        yield from travel_to_route103()
        yield from train_lead_to_level(target_level)
        yield from fight_route103_rival()
        yield from return_to_lab_and_get_pokedex()
        yield from travel_to_petalburg()
        yield from do_petalburg_gym_and_wally_tutorial()

        # Chapter 3: heal, cross west to Route 104 (Scott cutscene), beat the
        # route trainer, and enter Petalburg Woods.
        yield from travel_to_petalburg_woods()

        context.message = (
            "Story: reached Petalburg Woods (via Route 104). The rest (crossing "
            "the Woods past the Aqua-grunt scene -> Rustboro -> Gym 1) is still "
            "being built; handing to manual."
        )
        console.print(f"[bold green]{context.message}")
        context.set_manual_mode()
        return
