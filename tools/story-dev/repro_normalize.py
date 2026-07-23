"""A/B proof for normalize_to_overworld (resume-from-anywhere, user 2026-07-23).

Fault-inject each awkward entry state the milestone feature can drop us into and
assert the normalizer settles to a controllable overworld by pressing only B (never
A — B can't start a conversation or take a destructive action):
  A. Stray START MENU open  -> B closes it -> settled.
  B. A message box up (script active, controllable) -> B advances -> settled.
  C. A Yes/No prompt up -> B cancels -> settled.
  D. A live BATTLE -> waits (presses nothing) until it ends -> settled.
  E. Already clean overworld -> returns immediately, no presses.
No emulator: the routine consumes only the state readers + button presses.
"""

import pathlib as _pl
import sys
from types import SimpleNamespace

_SANDBOX = str(_pl.Path(__file__).resolve().parents[2] / "sandbox-pokebot")
sys.path.insert(0, _SANDBOX)

from modules.context import context
from modules.game import set_rom
from modules.profiles import load_profile_by_name

profile = load_profile_by_name("repro-ml")
context.profile = profile
context.config.load(profile.path, strict=False)
set_rom(profile.rom)

from modules.memory import GameState
from modules.story import early_game


class Scenario:
    """Drives the generator with a scripted state that CLEARS after N B-presses."""

    def __init__(self, name, state, script, menu, clears_after, *, needs_button=True):
        self.name = name
        self.state = state
        self.script = script
        self.menu = menu
        self.clears_after = clears_after
        self.needs_button = needs_button
        self.b_presses = 0
        self.a_presses = 0
        self.frames = 0

    def cleared(self) -> bool:
        # A BATTLE clears on its own after `clears_after` FRAMES (a listener ends it,
        # not our button); every other awkward state clears after that many B presses.
        if self.state is GameState.BATTLE:
            return self.frames >= self.clears_after
        return self.b_presses >= self.clears_after

    def install(self):
        import modules.memory as memory
        import modules.player as player

        # The function imports get_game_state / game_has_started / controllable LOCALLY
        # from their source modules, so patch THOSE (not the early_game aliases).
        memory.get_game_state = lambda: (GameState.OVERWORLD if self.cleared() else self.state)
        memory.game_has_started = lambda: True
        player.player_avatar_is_controllable = lambda: self.cleared()
        active = SimpleNamespace(is_active=False)
        early_game.get_global_script_context = lambda: SimpleNamespace(
            is_active=(self.script and not self.cleared())
        )
        early_game.get_immediate_script_context = lambda: active
        early_game._menu_task_active = lambda: self.menu and not self.cleared()
        early_game._check_abort = lambda: None

        def press(btn):
            if btn == "B":
                self.b_presses += 1
            elif btn == "A":
                self.a_presses += 1

        context.emulator = SimpleNamespace(press_button=press, reset_held_buttons=lambda: None, get_frame_count=lambda: self.frames)

    def run(self):
        self.install()
        gen = early_game.normalize_to_overworld()
        try:
            while self.frames < 6000:
                next(gen)
                self.frames += 1
        except StopIteration:
            pass
        return self


results = []
for sc in [
    Scenario("A start-menu", GameState.OVERWORLD, False, True, 3),
    Scenario("B message-box", GameState.OVERWORLD, True, False, 4),
    Scenario("C yes/no", GameState.OVERWORLD, True, False, 2),
    Scenario("D battle", GameState.BATTLE, False, False, 40),
    Scenario("E clean", GameState.OVERWORLD, False, False, 0),
]:
    r = sc.run()
    settled = r.frames < 6000
    print(f"{r.name:14s}: settled={settled} B={r.b_presses} A={r.a_presses} frames={r.frames}")
    results.append(r)

assert all(r.frames < 6000 for r in results), "a scenario never settled"
assert all(r.a_presses == 0 for r in results), "the normalizer pressed A (must be B-only)"
assert results[3].b_presses == 0, "the battle scenario pressed buttons (should wait)"
assert results[4].b_presses == 0 and results[4].frames < 20, "clean overworld should be a near-instant no-op"
print("ALL PASS: every awkward entry state settles to overworld with B-only; battle waited; clean was instant.")
