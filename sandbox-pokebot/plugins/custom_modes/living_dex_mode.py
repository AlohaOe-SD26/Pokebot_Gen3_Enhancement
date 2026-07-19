"""
Living Dex (Custom) — work through a list of target species autonomously (#23).

For each uncaught target it travels (warp-aware global navigation) to the best
wild spot, hunts there, and CATCHES the first one of that species — then
advances to the next target. Configure the run from the dashboard's Hunt tab
(Living Dex panel): "all uncaught wild" or a custom picked list.

Catch intent: a wild battle against the CURRENT target species (that you don't
already own) is caught automatically; everything else goes through the bot's
normal pipeline, so shinies of any species are still caught and your custom
catch filters still apply. The run stops cleanly when the list is exhausted or
if box/party space runs out (so a catch is never lost).
"""

from typing import Generator

from modules import living_dex
from modules import encounter_index
from modules.battle_state import BattleOutcome
from modules.context import context
from modules.modes import BattleAction, BotMode, BotModeError
from modules.modes._asserts import assert_player_has_poke_balls
from modules.modes.util import apply_white_flute_if_available, fish, spin
from modules.modes.util.global_navigation import navigate_to_anywhere

_FISHING_METHODS = ("Old Rod", "Good Rod", "Super Rod")


class LivingDexMode(BotMode):
    @staticmethod
    def name() -> str:
        return "Living Dex (Custom)"

    @staticmethod
    def is_selectable() -> bool:
        # Selectable whenever a run is configured for this profile.
        return living_dex.load_run() is not None

    def __init__(self):
        super().__init__()
        self._current_target_index: int | None = None

    def on_battle_started(self, encounter):
        # Catch the current target species (if not already owned); otherwise
        # let the default pipeline decide (it still catches shinies / CCF).
        try:
            if encounter is None or self._current_target_index is None:
                return None
            opponent = encounter.pokemon
            if opponent.species.index == self._current_target_index and not living_dex.is_owned(
                self._current_target_index
            ):
                return BattleAction.Catch
        except Exception:
            pass
        return None

    def run(self) -> Generator:
        run = living_dex.load_run()
        if run is None or not run.get("targets"):
            raise BotModeError(
                "No Living Dex run configured — open the dashboard's Hunt tab and start one "
                "(all-uncaught or a custom list)."
            )
        assert_player_has_poke_balls()

        from modules.pokemon import get_species_by_index

        while True:
            sid = living_dex.next_target_index(run)
            if sid is None:
                break  # every target owned/done

            self._current_target_index = sid
            try:
                species = get_species_by_index(sid)
                species_name = species.name
            except Exception:
                species_name = f"#{sid}"

            locations = encounter_index.locations_for_species(sid)
            if not locations:
                self._skip(run, sid, f"{species_name}: no wild location")
                continue

            best = locations[0]
            method = best.get("method", "Grass")
            target_map = tuple(best["map"])
            map_name = best.get("map_name", f"{target_map[0]}.{target_map[1]}")
            tile = best.get("tile") or encounter_index.find_encounter_tile(target_map, method)
            if tile is None:
                self._skip(run, sid, f"{species_name}: no reachable {method} tile on {map_name}")
                continue

            # Box/party space guard — stop cleanly rather than lose a catch.
            if not self._can_fit_pokemon():
                context.message = "Living Dex paused: boxes/party full. Free up space and restart."
                self._alert("Living Dex paused — boxes full.")
                context.set_manual_mode()
                return

            context.message = f"Living Dex: {species_name} — {map_name} ({method})"
            try:
                yield from navigate_to_anywhere(target_map, tuple(tile), avoid_encounters=True)
            except BotModeError as error:
                self._skip(run, sid, f"{species_name}: unreachable ({error})")
                continue

            yield from apply_white_flute_if_available()

            def _caught_target(target_sid=sid) -> bool:
                return living_dex.is_owned(target_sid)

            if method in _FISHING_METHODS:
                yield from fish(stop_condition=_caught_target, loop=True)
            else:
                yield from spin(stop_condition=_caught_target)

            # spin/fish returned -> the target is owned. Record and advance.
            if sid not in run["done"]:
                run["done"].append(sid)
            living_dex.save_run(run)
            self._alert(f"Living Dex: caught {species_name}!")

        # Exhausted.
        context.message = "Living Dex run complete — every wild target owned."
        self._alert("Living Dex run complete!")
        context.set_manual_mode()

    # -- helpers --
    def _can_fit_pokemon(self) -> bool:
        try:
            from modules.modes._asserts import assert_boxes_or_party_can_fit_pokemon

            assert_boxes_or_party_can_fit_pokemon()
            return True
        except Exception:
            return False

    def _skip(self, run: dict, sid: int, reason: str) -> None:
        if sid not in run["done"]:
            run["done"].append(sid)  # 'done' also carries skipped so we advance past them
        run.setdefault("skipped", []).append({"index": sid, "reason": reason})
        living_dex.save_run(run)
        try:
            self._alert(f"Living Dex skipped — {reason}")
        except Exception:
            pass

    def _alert(self, message: str) -> None:
        try:
            from modules.console import console

            console.print(f"[cyan]{message}[/]")
        except Exception:
            pass
        try:
            from plugins import shiny_alert_plugin  # reuse toast path if present

            notify = getattr(shiny_alert_plugin, "_notify", None)
            if callable(notify):
                notify("Living Dex", message)
        except Exception:
            pass

    def on_battle_ended(self, outcome: "BattleOutcome") -> None:
        pass
