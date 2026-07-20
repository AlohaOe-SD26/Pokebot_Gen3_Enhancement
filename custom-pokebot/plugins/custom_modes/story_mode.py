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
        # which the training loop covers by healing). Used for training wilds and
        # the rival; the scripted first battle is a Tutorial (framework-handled).
        from modules.battle_strategies.level_up import LevelUpLeadBattleStrategy

        return LevelUpLeadBattleStrategy()

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
            finish_birch_lab,
            fight_route103_rival,
            go_upstairs_and_set_clock,
            help_birch_and_choose_starter,
            train_lead_to_level,
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
        # Lv 8-10, then battle the rival.
        target_level = random.randint(8, 10)
        console.print(f"[cyan]Story: training the starter to Lv {target_level} before the rival.[/]")
        yield from travel_to_route103()
        yield from train_lead_to_level(target_level)
        yield from fight_route103_rival()

        context.message = (
            "Story: trained the starter and beat the rival on Route 103! "
            "That's the end of the currently-built story; handing to manual."
        )
        console.print(f"[bold green]{context.message}")
        context.set_manual_mode()
        return
