"""
Macro (Custom) — replays a recorded macro frame-accurately (sandbox A2).

Pick the macro (and loop on/off) in the GUI's MACROS card, then press Play —
or select this mode from the bot-mode menu after choosing a macro. The
selection is stored in `profiles/<name>/macros/_selected.yml`.

Battles interrupt macros (the default battle pipeline — shiny checks, catch
filters, stats — still runs). Afterwards:
  - loop mode:  the macro RESTARTS from step 1 (the world state after a
                battle rarely matches wherever mid-macro you were);
  - once mode:  the mode stops and the bot returns to Manual.
A once-mode macro that finishes normally also returns the bot to Manual
(otherwise the main loop would re-instantiate the mode and replay it).
"""

from typing import Generator

from modules.context import context
from modules.macros import MacroError, load_macro, load_selection, list_macros, macros_dir
from modules.modes import BotMode, BotModeError


class MacroPlayerMode(BotMode):
    @staticmethod
    def name() -> str:
        return "Macro (Custom)"

    @staticmethod
    def is_selectable() -> bool:
        return context.profile is not None and len(list_macros(context.profile.path)) > 0

    def __init__(self):
        super().__init__()
        self._battle_interrupted = False

    def on_battle_started(self, encounter):
        self._battle_interrupted = True
        return None  # default battle pipeline (shiny checks etc.) stays active

    def run(self) -> Generator:
        macro_name, loop = load_selection(context.profile.path)
        if macro_name is None:
            raise BotModeError(
                "No macro selected. Pick one in the MACROS card (or create "
                "`macros/_selected.yml` in the profile folder)."
            )
        macro_path = macros_dir(context.profile.path) / f"{macro_name}.yml"
        try:
            macro = load_macro(macro_path)
        except MacroError as error:
            raise BotModeError(str(error))

        context.message = f"Replaying macro `{macro.name}` ({'looping' if loop else 'once'})…"
        while True:
            self._battle_interrupted = False
            restart = False
            for step in macro.steps:
                bitfield = step.to_bitfield()
                if bitfield:
                    context.emulator.hold_button(inputs=bitfield)
                try:
                    for _ in range(step.frames):
                        yield
                        if self._battle_interrupted:
                            break
                finally:
                    if bitfield:
                        context.emulator.release_button(inputs=bitfield)
                if self._battle_interrupted:
                    if loop:
                        context.message = f"Battle over — restarting macro `{macro.name}`."
                        restart = True
                        break
                    context.message = f"Macro `{macro.name}` interrupted by a battle — stopping."
                    # Without this, the main loop would re-instantiate the mode as
                    # soon as its controller stack empties and replay the macro again.
                    context.set_manual_mode()
                    return
            if restart:
                continue
            if not loop:
                context.message = f"Macro `{macro.name}` finished."
                context.set_manual_mode()
                return
