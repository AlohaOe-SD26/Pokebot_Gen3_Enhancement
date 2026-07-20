"""
Living Dex (Custom) — work through a list of target species autonomously (#23).

For each uncaught target it travels (warp-aware global navigation) to the best
wild spot, hunts there, and CATCHES the first one of that species — then
advances to the next target. Configure the run from the dashboard's Hunt tab
(Living Dex panel): "all uncaught wild" or a custom picked list.

Catch intent (OPPORTUNISTIC, #43): the goal is to COMPLETE the dex, so a wild
battle against ANY un-owned species that is part of the run's plan is caught
automatically — not only the species currently being travelled to. The target
only steers where the bot walks; every uncaught wanted species it runs into
along the way is grabbed. Everything else goes through the bot's normal
pipeline, so shinies of any species are still caught and your custom catch
filters still apply. The run stops cleanly when the list is exhausted or if
box/party space runs out (so a catch is never lost).
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
        self._run: dict | None = None
        # Targets deferred THIS session because the player lacks a capability
        # (e.g. Surf / a specific rod) — sid -> reason. Not persisted to `done`,
        # so a later run (after earning the badge/rod) retries them.
        self._deferred: dict = {}

    def on_battle_started(self, encounter):
        # OPPORTUNISTIC catch (#43): catch ANY un-owned species that is part of
        # this run's plan — not just the driving target. The driving target only
        # steers travel; bonus catches happen right here and are reflected
        # automatically (is_owned reads the live Pokédex, so progress advances
        # and the species is never re-targeted). Trainer battles (encounter is
        # None) are never auto-caught. Anything not wanted falls through to the
        # default pipeline, so shinies / custom catch filters still apply.
        try:
            if encounter is None:
                return None
            run = self._run if self._run is not None else living_dex.load_run()
            if run is None:
                return None
            opponent_index = encounter.pokemon.species.index
            if living_dex.is_wanted(opponent_index, run) and not living_dex.is_owned(opponent_index):
                # Only commit to a catch we can actually store, so one is never
                # lost; if full, the run loop's per-target space check pauses.
                if self._can_fit_pokemon():
                    return BattleAction.Catch
                return None
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
        self._run = run  # cached so on_battle_started checks the plan without a disk read
        self._deferred = {}
        assert_player_has_poke_balls()

        from modules.pokemon import get_species_by_index

        while True:
            sid = self._pick_target(run)
            if sid is None:
                break  # every target owned/done/deferred

            self._current_target_index = sid
            try:
                species = get_species_by_index(sid)
                species_name = species.name
            except Exception:
                species_name = f"#{sid}"

            # #42 capability gate: pick the best location whose ENCOUNTER METHOD
            # the player can actually use now (e.g. don't pick a Surf slot with
            # no Surf, or a Super-Rod slot with no Super Rod). Defer — not
            # permanently skip — a target that needs a capability we lack.
            location, reason = living_dex.best_reachable_location(sid)
            if location is None:
                if reason == "no wild location":
                    self._skip(run, sid, f"{species_name}: no wild location")
                else:
                    self._deferred[sid] = reason
                    context.message = f"Living Dex: {species_name} deferred — {reason}"
                    self._alert(f"Living Dex deferring {species_name} — {reason}")
                continue

            method = location.get("method", "Grass")
            target_map = tuple(location["map"])
            map_name = location.get("map_name", f"{target_map[0]}.{target_map[1]}")
            tile = location.get("tile") or encounter_index.find_encounter_tile(target_map, method)
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

        # Exhausted (owned/done/deferred all consumed).
        if self._deferred:
            reasons = "; ".join(sorted(set(self._deferred.values())))
            context.message = (
                f"Living Dex: caught everything reachable. {len(self._deferred)} target(s) deferred — {reasons}."
            )
            self._alert(f"Living Dex done for now — {len(self._deferred)} deferred (e.g. {reasons}).")
        else:
            context.message = "Living Dex run complete — every wild target owned."
            self._alert("Living Dex run complete!")
        context.set_manual_mode()

    # -- helpers --
    def _pick_target(self, run: dict) -> int | None:
        """First target that is not owned, not done, and not deferred this
        session (deferred = a capability the player lacks; retried next run)."""
        owned = living_dex.owned_indices()
        done = set(run.get("done", []))
        for sid in run.get("targets", []):
            if sid in owned or sid in done or sid in self._deferred:
                continue
            return sid
        return None

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
        # No bookkeeping needed for opportunistic catches: is_owned reads the
        # live Pokédex, so a bonus catch is immediately reflected in progress()
        # and excluded by next_target_index() — and a FAILED catch (fled/fainted)
        # simply leaves the species un-owned, so it stays wanted for a later
        # encounter. Outcome-gating is therefore implicit and correct.
        pass
