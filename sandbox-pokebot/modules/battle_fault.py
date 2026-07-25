"""A hand-off channel for battle-handler faults that a bot mode can RECOVER from.

WHY THIS EXISTS (#24-movelearn-recovery, 2026-07-25)
---------------------------------------------------
Battle handling does not run *inside* the bot mode's generator. The BattleListener
pushes `fight()` onto `context.controller_stack`, and `main_loop` only ever advances
the TOP of that stack. Mode and battle handler are therefore SIBLINGS, not nested —
so a `BotModeError` raised inside the battle handler propagates straight to
`main_loop`, which sets Manual. `StoryMode.run()`'s `except BotModeError` derail
recovery cannot see it, no matter how well written it is.

Measured cost: a single unanswerable move-learn offer killed 2 of the 5 night5
cold-start runs outright, at f1.54M and f1.56M — losing ~1.5 million frames of
progress over what should have been one skipped level-up.

The fix is not to catch the error somewhere else; it is to stop RAISING across that
boundary. The battle handler records the fault here and returns; the mode picks it up
on the next frame it holds control and re-raises it inside its own recoverable scope.

‼ OPT-IN ON PURPOSE. `request_mode_recovery()` returns False when the running mode has
not declared `handles_battle_faults = True`, and the caller must then raise exactly as
before. Every stock mode keeps today's behaviour; only a mode that promises to CONSUME
the fault is allowed to defer it. An unconsumed fault would be far worse than a Manual
drop — `handle_battle` short-circuits while one is pending, so a fault nobody claims
would make every future battle exit instantly.
"""

from modules.context import context

_PENDING: str | None = None


def request_mode_recovery(reason: str) -> bool:
    """Ask the running bot mode to take this fault as a recoverable derail.

    :return: True if the mode accepted it (caller should return quietly), False if
             no mode can handle it (caller MUST raise, preserving old behaviour).
    """
    global _PENDING
    mode = context.bot_mode_instance
    if mode is None or not getattr(mode, "handles_battle_faults", False):
        return False
    _PENDING = reason
    return True


def battle_fault_pending() -> bool:
    return _PENDING is not None


def take_pending_fault() -> str | None:
    """Pop the pending fault. The mode that declared support MUST call this every
    frame it runs, so a fault can never sit unclaimed."""
    global _PENDING
    reason, _PENDING = _PENDING, None
    return reason


def clear_pending_fault() -> None:
    """Drop any stale fault — called when a mode starts, so a fault recorded just
    before a mode switch cannot leak into the next run."""
    global _PENDING
    _PENDING = None
