"""How many levels boss-training mode tops the team up before re-fighting a boss it keeps losing to.

`StoryMode._prepare_for_fight` enters boss-training mode after 2+ losses when the local wilds are fodder (8+ levels
under the team) and the boss attempts still KO something. Its rule was a fixed `team_max + 1` ("the boss battle is
the trainer"). The AI learner (`ai-agent/`, 2026-10-03) measured Tate & Liza at 11.2 losses per run with the team's
average level flat between the first loss and the win, so this top-up becomes a knob the learner can A/B.

`POKEBOT_BOSSMODE_TOPUP` (registry `29`): unset = 1, the old behaviour exactly. Any integer 1-10 is honoured; anything
else falls back to 1. Read on every call, so a lane's environment decides it. The training this triggers is the same
target-level training the non-boss-mode path already runs every game (`team_max + 5` after 2 losses).
"""
from __future__ import annotations

import os

ENV = "POKEBOT_BOSSMODE_TOPUP"
DEFAULT, LOW, HIGH = 1, 1, 10


def topup_levels(environ=None) -> int:
    raw = str((os.environ if environ is None else environ).get(ENV, "")).strip()
    # Plain digits only (no try/except: story code keeps no swallowing handlers, `repro_no_silent_except.py`).
    if not raw.isdigit():
        return DEFAULT
    n = int(raw)
    return n if LOW <= n <= HIGH else DEFAULT
