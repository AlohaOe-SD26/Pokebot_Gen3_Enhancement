"""
Poké Ball allowlist for catching (fork feature #40).

Lets the user control WHICH Poké Balls the bot may throw when catching.
The bot's `_get_best_poke_ball` (battle_strategies/catch.py) picks the best
ball BY multiplier from the bag; this module filters the candidates to the
allowed set so disallowed balls (default: Master Ball) are never thrown.

Config: `catch_balls.yml` at the bot root (global) with an optional
per-profile override at `profiles/<name>/catch_balls.yml`. Whole-file
override, like the other fork configs. Malformed / missing -> safe default
(all balls except Master Ball).
"""

from __future__ import annotations

import logging

log = logging.getLogger("catch_balls")

# All Gen-3 Poké Balls (names match modules/data/items.json).
ALL_BALLS: list = [
    "Poké Ball", "Great Ball", "Ultra Ball", "Master Ball", "Safari Ball",
    "Net Ball", "Dive Ball", "Nest Ball", "Repeat Ball", "Timer Ball",
    "Luxury Ball", "Premier Ball",
]

# Protected by default — the bot won't auto-throw these unless the user
# explicitly allows them (and the Master Ball also stays never-auto-thrown
# by catch.py's own -1 multiplier, so allowing it here is harmless).
DEFAULT_BLOCKED: set = {"Master Ball"}

_DEFAULT_ALLOWED: list = [b for b in ALL_BALLS if b not in DEFAULT_BLOCKED]


def _config_paths() -> list:
    """Global then per-profile config file paths (per-profile wins)."""
    from pathlib import Path

    paths: list = []
    try:
        from modules.runtime import get_base_path

        paths.append(Path(get_base_path()) / "catch_balls.yml")
    except Exception:
        pass
    try:
        from modules.context import context

        if context.profile is not None:
            paths.append(context.profile.path / "catch_balls.yml")
    except Exception:
        pass
    return paths


def allowed_ball_names() -> set:
    """The set of ball names the bot is allowed to throw. Falls back to
    'all except Master Ball' on any error, so catching never silently breaks."""
    allowed = list(_DEFAULT_ALLOWED)
    try:
        import yaml

        for path in _config_paths():
            if not path.is_file():
                continue
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("allowed_balls"), list):
                names = [str(n) for n in data["allowed_balls"] if str(n) in ALL_BALLS]
                if names:  # ignore an empty/garbage list -> keep default
                    allowed = names
    except Exception as error:
        log.warning("catch_balls config read failed, using default: %s", error)
    return set(allowed)


def is_ball_allowed(ball_name: str) -> bool:
    return ball_name in allowed_ball_names()


def set_allowed_ball_names(names: list) -> None:
    """Persist the allowlist to the per-profile config (or global if no
    profile). Used by the GUI editor."""
    try:
        import yaml

        from modules.context import context

        valid = [n for n in names if n in ALL_BALLS]
        if context.profile is not None:
            target = context.profile.path / "catch_balls.yml"
        else:
            from pathlib import Path
            from modules.runtime import get_base_path

            target = Path(get_base_path()) / "catch_balls.yml"
        target.write_text(
            "# Balls the bot may throw when catching (fork #40).\n"
            "allowed_balls:\n" + "".join(f"  - {n}\n" for n in valid),
            encoding="utf-8",
        )
    except Exception as error:
        log.warning("could not save catch_balls config: %s", error)
