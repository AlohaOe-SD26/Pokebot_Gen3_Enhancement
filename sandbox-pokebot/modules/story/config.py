"""Story-mode settings, read from ``<profile>/story.yml``.

Keeps the player's chosen character name and gender (used by the New Game
intro) out of code. If the file is missing it is created with commented
defaults so the user can edit it, and defaults are used until then.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.console import console

DEFAULT_NAME = "NICK"
DEFAULT_GENDER = "boy"
_FILENAME = "story.yml"

_TEMPLATE = """\
# Story-mode settings (used when starting a NEW GAME).
# character_name: your player character's name (max 7 letters).
# gender: "boy" or "girl".
character_name: {name}
gender: {gender}
"""


@dataclass
class StoryConfig:
    character_name: str = DEFAULT_NAME
    gender: str = DEFAULT_GENDER


def _sanitize(cfg: StoryConfig) -> StoryConfig:
    name = (str(cfg.character_name or "").strip() or DEFAULT_NAME)[:7]
    gender = str(cfg.gender or "").strip().lower()
    if gender not in ("boy", "girl"):
        gender = DEFAULT_GENDER
    return StoryConfig(character_name=name, gender=gender)


def get_story_config(profile_path: Path) -> StoryConfig:
    """Load story settings for a profile, writing a default file if absent."""
    path = profile_path / _FILENAME
    if not path.is_file():
        try:
            path.write_text(_TEMPLATE.format(name=DEFAULT_NAME, gender=DEFAULT_GENDER))
            console.print(
                f"[yellow]Created {path} with default story settings "
                f"(name={DEFAULT_NAME}, gender={DEFAULT_GENDER}). Edit it to change them."
            )
        except Exception:
            pass
        return StoryConfig()

    try:
        from ruamel.yaml import YAML

        data = YAML(typ="safe").load(path.read_text()) or {}
        return _sanitize(
            StoryConfig(
                character_name=data.get("character_name", DEFAULT_NAME),
                gender=data.get("gender", DEFAULT_GENDER),
            )
        )
    except Exception as exc:
        console.print(f"[red]Could not read {path} ({exc}); using story defaults.")
        return StoryConfig()
