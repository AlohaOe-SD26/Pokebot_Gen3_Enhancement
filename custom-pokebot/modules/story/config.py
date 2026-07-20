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
DEFAULT_STARTER = "random"          # random | treecko | torchic | mudkip
DEFAULT_NICKNAME_MODE = "none"      # none | random | <a literal nickname string>
_STARTERS = ("treecko", "torchic", "mudkip")
_FILENAME = "story.yml"

_TEMPLATE = """\
# Story-mode settings (used when starting a NEW GAME).
# character_name: your player character's name (max 7 letters).
# gender: "boy" or "girl".
# starter: which starter to choose - "random", or "treecko"/"torchic"/"mudkip".
# starter_nickname: "none" (keep the species name), "random" (a random nickname),
#                   or any literal name (max 10 letters) to always use.
character_name: {name}
gender: {gender}
starter: {starter}
starter_nickname: {nickname}
"""


@dataclass
class StoryConfig:
    character_name: str = DEFAULT_NAME
    gender: str = DEFAULT_GENDER
    starter: str = DEFAULT_STARTER
    starter_nickname: str = DEFAULT_NICKNAME_MODE


def _sanitize(cfg: StoryConfig) -> StoryConfig:
    name = (str(cfg.character_name or "").strip() or DEFAULT_NAME)[:7]
    gender = str(cfg.gender or "").strip().lower()
    if gender not in ("boy", "girl"):
        gender = DEFAULT_GENDER
    starter = str(cfg.starter or "").strip().lower()
    if starter not in ("random", *_STARTERS):
        starter = DEFAULT_STARTER
    # nickname: keep "none"/"random" as-is (lowercased); otherwise a literal name.
    nickname_raw = str(cfg.starter_nickname or "").strip()
    if nickname_raw.lower() in ("none", "random", ""):
        nickname = nickname_raw.lower() or DEFAULT_NICKNAME_MODE
    else:
        nickname = nickname_raw[:10]
    return StoryConfig(character_name=name, gender=gender, starter=starter, starter_nickname=nickname)


def get_story_config(profile_path: Path) -> StoryConfig:
    """Load story settings for a profile, writing a default file if absent."""
    path = profile_path / _FILENAME
    if not path.is_file():
        try:
            path.write_text(_TEMPLATE.format(
                name=DEFAULT_NAME, gender=DEFAULT_GENDER,
                starter=DEFAULT_STARTER, nickname=DEFAULT_NICKNAME_MODE))
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
                starter=data.get("starter", DEFAULT_STARTER),
                starter_nickname=data.get("starter_nickname", DEFAULT_NICKNAME_MODE),
            )
        )
    except Exception as exc:
        console.print(f"[red]Could not read {path} ({exc}); using story defaults.")
        return StoryConfig()
