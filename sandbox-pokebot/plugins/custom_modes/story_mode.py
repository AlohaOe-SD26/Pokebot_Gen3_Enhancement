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
from modules.modes import BotMode


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

        context.message = (
            "Story Chapter 0 complete — you're in the moving truck. The next "
            "chunk (step off, room/clock, starter, first battle) isn't built "
            "yet; handing back to manual."
        )
        console.print(f"[bold green]{context.message}")
        context.set_manual_mode()
        return
