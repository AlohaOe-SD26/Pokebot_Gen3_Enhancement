"""Listener isolation: while the AI plays, no framework listener runs; on exit they all come back.

WHY (design draft §2.2 "THE LISTENER PROBLEM", §10.1-2, RULING 37 Q2 = strict): every frame, BEFORE
the mode runs, `modules/main.py` calls every entry of `context.bot_listeners`. Several of them push
BOT code that presses buttons (`BattleListener` turns every trainer battle into the bot's
`DefaultBattleStrategy`), the cheats plugin writes memory, and the watchdog can load save states or
switch to Manual. So on mode entry the AI REMOVES every listener it does not own, from its own side,
without editing the framework, and it restores the exact original list (same list object, same
members) when the mode exits, including on a crash.

THE REBUILD DOOR (step 0.1, the adversarial review's finding 1). When the frame counter goes
backwards (an emulator reset, or a save state loaded from an earlier frame), `main.py` runs
`context.bot_listeners = get_bot_listeners(context.rom)`: a FRESH list of fresh framework listeners,
without the AI's guard. In step 0 those listeners then ran for a frame before the AI could re-isolate,
and one frame is enough: on a battle state `BattleListener` pushes the bot's battle handler on top of
the AI, the AI's generator is never stepped again, and with the guard gone nothing ends the starved
run. So while the AI runs, the name `main.py` resolves, `modules.main.get_bot_listeners`, is re-bound
to return the AI's OWN active list: the rebuild hands back the same list, no framework listener is
even constructed, and isolation holds through a reset. The original function is put back on exit.
The instrument independently checks before every real frame that the guard is still in the live list
(`attribution.py`, `isolation_lost`), so if this door is ever bypassed the run ends as a recorded
BREACH instead of starving silently.

The AI owns exactly one listener: `GuardListener`, its lifecycle heartbeat. It is a listener, rather
than code in the mode's generator, because listeners keep running even when the generator is
starved (a foreign handler on top of the controller stack) or discarded (the framework switched to
Manual). That makes it the one place that can always end the process instead of letting it park.

WHY `ListenerIsolation` AND `GuardListener` ARE GUARDED, SEALED AND SLOTTED: the isolation's entry and
exit descriptions go into the run's verdict file (`attribution.py`), which is the evidence that
isolation held, and the guard listener's callback is the lifecycle's heartbeat (park, budget, wall
clock, interrupt). With `__slots__` no instance attribute can shadow `restore()` or `report()`, the
`Sealed` metaclass refuses class-level replacement, and `Guarded` refuses (and COUNTS) any attribute
write from outside this file, so the AI's own code can neither hand the lifecycle a forged description
(`isolation._exit = ...`) nor silence the guard (`guard._on_frame = ...`). The hook keeps its OWN
record of the framework's list from before the AI started and prints what the framework holds at
process exit (`[AI-HOOK]`), so restoration is also observed by code that is not this file.
"""

from __future__ import annotations

from collections.abc import Callable

import modules.main as framework_main
from modules.context import context
from modules.modes._interface import BotListener

from ai_player.host.attribution import Guarded, seal_module

__all__ = ["GuardListener", "ListenerIsolation", "describe"]


class GuardListener(BotListener, Guarded):
    """The AI's only listener. Calls the session back once per frame, whoever holds the controller."""

    __slots__ = ("_on_frame",)

    def __init__(self, on_frame: Callable[[], None]) -> None:
        self._on_frame = on_frame

    def handle_frame(self, bot_mode, frame) -> None:
        self._on_frame()


def describe(listeners: list) -> str:
    names = ",".join(type(listener).__name__ for listener in listeners)
    return f"n={len(listeners)} types=[{names}]"


class ListenerIsolation(Guarded):
    __slots__ = (
        "_guard", "_keep_foreign", "_rebind", "_skip_restore", "_extra", "_on_tamper", "_guard_restored",
        "_original_list", "_original_members", "_active_list", "_reapplied", "_foreign_removed_later",
        "_framework_factory", "_rebound", "_rebuilds_served", "_rebind_restored", "_entry", "_active", "_exit",
    )

    def __init__(
        self,
        guard: GuardListener,
        keep_foreign: bool,
        rebind: bool = True,
        skip_restore: bool = False,
        extra: list | None = None,
        on_tamper: Callable[[str], None] | None = None,
    ) -> None:
        """
        :param guard: the AI's own listener; always installed.
        :param keep_foreign: FAULT `AI_PLAYER_FAULT_KEEP_LISTENERS` only: leave the framework's
                             listeners in place, so the purity counters can be shown to fire.
        :param rebind: re-bind `modules.main.get_bot_listeners` while the AI runs (always, except
                       under FAULT `AI_PLAYER_FAULT_NO_REBIND`, which proves the instrument's
                       isolation check catches a rebuild the door did not stop).
        :param skip_restore: FAULT `AI_PLAYER_FAULT_SKIP_RESTORE` only: do not give the framework its
                             list back, so the hook's independent observation can be shown to fail.
        :param extra: FAULT `AI_PLAYER_FAULT_MANUAL` only: listeners appended after the guard.
        :param on_tamper: told when the guard or the rebuild door had to be put back (someone removed
                          it), so the purity verdict counts it.
        """
        self._guard = guard
        self._keep_foreign = keep_foreign
        self._rebind = rebind
        self._skip_restore = skip_restore
        self._extra = list(extra or [])
        self._on_tamper = on_tamper
        self._guard_restored = 0
        self._original_list: list | None = None
        self._original_members: list = []
        self._active_list: list | None = None
        self._reapplied = 0
        self._foreign_removed_later = 0
        self._framework_factory: Callable | None = None
        self._rebound: Callable | None = None
        self._rebuilds_served = 0
        self._rebind_restored = False
        self._entry = ""
        self._active = ""
        self._exit = ""

    def _build_active(self, framework_list: list) -> list:
        kept = list(framework_list) if self._keep_foreign else []
        return kept + [self._guard] + self._extra

    def _listeners_for_framework(self, rom=None) -> list:
        """What `modules/main.py` gets when it rebuilds its listeners (after a reset or a state load)
        while the AI plays: the AI's own active list, so no framework listener is built or run."""
        self._rebuilds_served += 1
        if self._active_list is not None:
            return self._active_list
        return self._framework_factory(rom)  # only reachable after restore, which un-binds this first

    def apply(self) -> tuple[str, str]:
        """Swap the framework's list for the AI's own. Returns (entry description, active description)."""
        if self._original_list is not None:
            raise RuntimeError("isolation is already applied")
        self._original_list = context.bot_listeners
        self._original_members = list(self._original_list)
        self._active_list = self._build_active(self._original_members)
        context.bot_listeners = self._active_list
        if self._rebind:
            self._framework_factory = framework_main.get_bot_listeners
            self._rebound = self._listeners_for_framework  # ONE bound method, kept, so identity can be checked
            framework_main.get_bot_listeners = self._rebound
        self._entry = f"{describe(self._original_members)} list_id={id(self._original_list):#x}"
        self._active = f"{describe(self._active_list)} rebuild_door={'AI' if self._rebind else 'FRAMEWORK (FAULT_NO_REBIND)'}"
        return self._entry, self._active

    def enforce(self) -> str | None:
        """Re-assert isolation once per AI step. Returns a log line when it had to act, else None."""
        if self._active_list is None:
            return None
        if self._rebind and framework_main.get_bot_listeners is not self._rebound:
            framework_main.get_bot_listeners = self._rebound
            if self._on_tamper is not None:
                self._on_tamper("modules.main.get_bot_listeners was replaced while the AI played")
            return "[AI-ISOLATION] the rebuild door (modules.main.get_bot_listeners) was replaced and has been put back"
        current = context.bot_listeners
        if current is not self._active_list:
            # The framework replaced the list (a rebuild the door did not serve). Its new list is now
            # the one to give back on exit.
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
        """Give the framework back its own list and its own rebuild function. Returns the evidence line."""
        if self._original_list is None:
            self._exit = "nothing-to-restore (isolation was never applied)"
            return f"[AI-ISOLATION] exit {self._exit}"
        if self._active_list is None:
            return f"[AI-ISOLATION] exit already restored: {self._exit}"
        door_held = None
        if self._rebind:
            door_held = framework_main.get_bot_listeners is self._rebound
            framework_main.get_bot_listeners = self._framework_factory
            self._rebind_restored = True
        # Read BEFORE swapping back: was the AI's own list still the live one right up to the exit?
        isolation_held = context.bot_listeners is self._active_list
        if self._skip_restore:
            self._active_list = None
            self._exit = (
                f"NOT RESTORED (FAULT_SKIP_RESTORE): the framework keeps {describe(context.bot_listeners)} "
                f"rebuilds_served={self._rebuilds_served} rebuild_door_restored={self._rebind_restored}"
            )
            return f"[AI-ISOLATION] exit {self._exit}"
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
            f"guard_restored={self._guard_restored} foreign_removed_later={self._foreign_removed_later} "
            f"rebuilds_served={self._rebuilds_served} rebuild_door_held_until_exit={door_held} "
            f"rebuild_door_restored={self._rebind_restored}"
        )
        return f"[AI-ISOLATION] exit {self._exit}"

    def report(self) -> dict[str, str]:
        """The three descriptions, for the verdict file."""
        return {"entry": self._entry, "active": self._active, "exit": self._exit}


seal_module(__name__)
