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
        import random

        from modules.memory import get_event_flag
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
        #     lab → train → rival → Pokédex. (Runs from the truck; gated by the
        #     Pokédex flag so a resumed game past this point skips it.) ---
        if not _done("RECEIVED_POKEDEX_FROM_BIRCH"):
            yield from walk_off_truck_and_into_house()
            yield from go_upstairs_and_set_clock()
            yield from descend_and_leave_players_house()
            yield from visit_rivals_house()
            yield from help_birch_and_choose_starter(cfg.starter)
            yield from finish_birch_lab(cfg.starter_nickname)
            target_level = random.randint(8, 10)
            console.print(f"[cyan]Story: training the starter to Lv {target_level} before the rival.[/]")
            yield from travel_to_route103()
            yield from train_lead_to_level(target_level)
            yield from fight_route103_rival()
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
        _in_rustboro = lambda: _cur_map() == rustboro or _done("BADGE01_GET")
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

        # --- Segment 4: Gym 1 — Roxanne (Stone Badge). ---
        if not _done("BADGE01_GET"):
            yield from do_rustboro_gym()
        else:
            console.print("[dim]Story: Stone Badge already earned — Gym 1 skipped.[/]")
        _guard("Gym 1 (Roxanne)", lambda: _done("BADGE01_GET"))

        context.message = (
            "Story: caught up to the end of the built content (through Gym 1 / "
            "Stone Badge). The next chapter (Devon Goods -> Rusturf Tunnel -> "
            "Dewford) isn't built yet; handing to manual."
        )
        console.print(f"[bold green]{context.message}")
        context.set_manual_mode()
        return
