"""Listener isolation: while the AI plays, no framework listener runs; on exit they all come back.

WHY (design draft §2.2 "THE LISTENER PROBLEM", §10.1-2, RULING 37 Q2 = strict): every frame, BEFORE
the mode runs, `modules/main.py` calls every entry of `context.bot_listeners`. Several of them push
BOT code that presses buttons (`BattleListener` turns every trainer battle into the bot's
`DefaultBattleStrategy`), the cheats plugin writes memory, and the watchdog can load save states or
switch to Manual. So on mode entry the AI REMOVES every listener it does not own, from its own side,
without editing the framework, and it restores the exact original list (same list object, same
members) when the mode exits, including on a crash.

The AI owns exactly one listener: `GuardListener`, its lifecycle heartbeat. It is a listener, rather
than code in the mode's generator, because listeners keep running even when the generator is
starved (a foreign handler on top of the controller stack) or discarded (the framework switched to
Manual). That makes it the one place that can always end the process instead of letting it park.

WHY `ListenerIsolation` IS SEALED AND SLOTTED: its entry and exit descriptions go into the run's
verdict file (`attribution.py`), which is the evidence that isolation held. With `__slots__` no
instance attribute can shadow `restore()` or `report()`, and the `Sealed` metaclass refuses
class-level replacement, so the AI's own code cannot hand the lifecycle a forged description.

KNOWN WINDOW: when the emulator is reset, `main.py` rebuilds `context.bot_listeners` from scratch.
The framework's listeners then run for that one frame before `enforce()` (called from the mode's next
step) removes them again. Step 0 never resets; any foreign action in that window is still COUNTED by
`attribution.py`, so it cannot go unseen.
"""

from __future__ import annotations

from collections.abc import Callable

from modules.context import context
from modules.modes._interface import BotListener

from ai_player.platform.attribution import Sealed

__all__ = ["GuardListener", "ListenerIsolation", "describe"]


class GuardListener(BotListener):
    """The AI's only listener. Calls the session back once per frame, whoever holds the controller."""

    def __init__(self, on_frame: Callable[[], None]) -> None:
        self._on_frame = on_frame

    def handle_frame(self, bot_mode, frame) -> None:
        self._on_frame()


def describe(listeners: list) -> str:
    names = ",".join(type(listener).__name__ for listener in listeners)
    return f"n={len(listeners)} types=[{names}]"


class ListenerIsolation(metaclass=Sealed):
    __slots__ = (
        "_guard", "_keep_foreign", "_extra", "_on_tamper", "_guard_restored", "_original_list",
        "_original_members", "_active_list", "_reapplied", "_foreign_removed_later", "_entry", "_active",
        "_exit",
    )

    def __init__(
        self,
        guard: GuardListener,
        keep_foreign: bool,
        extra: list | None = None,
        on_tamper: Callable[[str], None] | None = None,
    ) -> None:
        """
        :param guard: the AI's own listener; always installed.
        :param keep_foreign: FAULT `AI_PLAYER_FAULT_KEEP_LISTENERS` only: leave the framework's
                             listeners in place, so the purity counters can be shown to fire.
        :param extra: FAULT `AI_PLAYER_FAULT_MANUAL` only: listeners appended after the guard.
        :param on_tamper: told when the guard had to be put back (someone removed it), so the
                          purity verdict counts it: without the guard nothing ends a parked run.
        """
        self._guard = guard
        self._keep_foreign = keep_foreign
        self._extra = list(extra or [])
        self._on_tamper = on_tamper
        self._guard_restored = 0
        self._original_list: list | None = None
        self._original_members: list = []
        self._active_list: list | None = None
        self._reapplied = 0
        self._foreign_removed_later = 0
        self._entry = ""
        self._active = ""
        self._exit = ""

    def _build_active(self, framework_list: list) -> list:
        kept = list(framework_list) if self._keep_foreign else []
        return kept + [self._guard] + self._extra

    def apply(self) -> tuple[str, str]:
        """Swap the framework's list for the AI's own. Returns (entry description, active description)."""
        if self._original_list is not None:
            raise RuntimeError("isolation is already applied")
        self._original_list = context.bot_listeners
        self._original_members = list(self._original_list)
        self._active_list = self._build_active(self._original_members)
        context.bot_listeners = self._active_list
        self._entry = f"{describe(self._original_members)} list_id={id(self._original_list):#x}"
        self._active = describe(self._active_list)
        return self._entry, self._active

    def enforce(self) -> str | None:
        """Re-assert isolation once per AI step. Returns a log line when it had to act, else None."""
        if self._active_list is None:
            return None
        current = context.bot_listeners
        if current is not self._active_list:
            # The framework replaced the list (emulator reset, `main.py`). Its new list is now the one
            # to give back on exit.
            self._original_list = current
            self._original_members = list(current)
            self._active_list = self._build_active(self._original_members)
            context.bot_listeners = self._active_list
            self._reapplied += 1
            return f"[AI-ISOLATION] reapplied after the framework rebuilt its listeners: {describe(self._original_members)}"
        if all(listener is not self._guard for listener in current):
            current.append(self._guard)
            self._guard_restored += 1
            if self._on_tamper is not None:
                self._on_tamper("the AI's guard listener was removed from its listener list")
            return "[AI-ISOLATION] the guard listener was missing and has been put back"
        if self._keep_foreign:
            return None
        allowed = [self._guard] + self._extra
        intruders = [listener for listener in current if all(listener is not mine for mine in allowed)]
        if intruders:
            # Something appended to the AI's list (plugins may do that). Remove it, and say so.
            for listener in intruders:
                current.remove(listener)
            self._foreign_removed_later += len(intruders)
            return f"[AI-ISOLATION] removed listeners added during the run: {describe(intruders)}"
        return None

    def restore(self) -> str:
        """Give the framework back its own list. Returns the evidence line for the log."""
        if self._original_list is None:
            self._exit = "nothing-to-restore (isolation was never applied)"
            return f"[AI-ISOLATION] exit {self._exit}"
        if self._active_list is None:
            return f"[AI-ISOLATION] exit already restored: {self._exit}"
        # Read BEFORE swapping back: was the AI's own list still the live one right up to the exit?
        isolation_held = context.bot_listeners is self._active_list
        context.bot_listeners = self._original_list
        # Did anything mutate the framework's list in place while it was set aside?
        members_unchanged = len(self._original_list) == len(self._original_members) and all(
            a is b for a, b in zip(self._original_list, self._original_members)
        )
        guard_removed = all(listener is not self._guard for listener in context.bot_listeners)
        self._active_list = None
        self._exit = (
            f"restored {describe(self._original_list)} "
            f"list_id={id(self._original_list):#x} isolation_held_until_exit={isolation_held} "
            f"members_unchanged={members_unchanged} guard_removed={guard_removed} reapplied={self._reapplied} "
            f"guard_restored={self._guard_restored} foreign_removed_later={self._foreign_removed_later}"
        )
        return f"[AI-ISOLATION] exit {self._exit}"

    def report(self) -> dict[str, str]:
        """The three descriptions, for the verdict file."""
        return {"entry": self._entry, "active": self._active, "exit": self._exit}
