"""Story Mode (#24) — plays Emerald's story from a fresh save or continues an
existing one, building a team toward the Elite Four.

Built in verifiable chunks (see PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md):
  * Chapter 0 (the New Game intro) — IMPLEMENTED. Title -> New Game -> Birch's
    speech -> gender -> name -> lands in the moving truck.
  * Existing saves — the read-only detector reports the current chapter so the
    bot can resume at the right place (chapter execution beyond 0 is WIP).

On start:
  * If the game is still at the title/main menu (a fresh, save-less boot), the
    intro is run using the name/gender from ``<profile>/story.yml``.
  * If a game is already loaded (existing progress), the current chapter is
    detected and reported; execution of chapters > 0 is not built yet, so the
    bot hands back to manual after reporting.
"""

from typing import Generator

from modules.console import console
from modules.context import context
from modules.memory import GameState, game_has_started, get_game_state
from modules.modes import BattleAction, BotMode
from modules.battle_strategies import BattleStrategyUtil, TurnAction
from modules.battle_strategies.level_up import LevelUpLeadBattleStrategy


class LevelUpTravelBattleStrategy(LevelUpLeadBattleStrategy):
    """Fights to win like LevelUpLead, but NEVER flees a TRAINER battle.

    Story travel crosses routes that have trainers, and at this point the party
    is often a SINGLE Pokémon — so when its HP dips, the parent strategy tries
    to flee/rotate, and in a trainer battle (which you cannot flee) that raises
    ``RuntimeError: Tried to run away from a trainer battle`` (ML-8). Here a
    trainer battle always fights on with the strongest move instead; the caller
    heals to full first so the lead can win. WILD battles keep the parent
    behaviour (flee at low HP — the training loop heals for that)."""

    def decide_turn(self, battle_state):
        if battle_state.is_trainer_battle:
            util = BattleStrategyUtil(battle_state)
            move = util.get_strongest_move_against(
                battle_state.own_side.active_battler, battle_state.opponent.active_battler
            )
            if move is not None:
                return TurnAction.use_move(move)
        return super().decide_turn(battle_state)

    def which_move_should_be_replaced(self, pokemon, new_move) -> int:
        """Story move-learning policy — keep every Pokémon COMBAT-CAPABLE.

        Called when a Pokémon with 4 moves is about to learn a new one (the stock
        config default `new_move: cancel` would just decline everything, so the
        starter would never improve — hence this override). Returns 0-3 to
        overwrite that slot, or 4 to DECLINE (keep the current moves).

        PRIORITY / RULES (in order):
          1. Never replace an HM move (can't anyway, and Cut/Surf/... are needed
             for field use); never learn a block-listed move.
          2. GUARANTEE combat capability: a damaging move is NEVER replaced by a
             status move, so a Pokémon can't end up with only non-combat moves.
             (Damaging-move count never decreases.)
          3. New STATUS move: accept it only by overwriting an existing (non-HM)
             STATUS slot; if every non-HM slot is a damaging move, DECLINE — don't
             trade attacking power for utility.
          4. New DAMAGING move: (a) upgrade a non-combat/status slot first (pure
             win). Else, among damaging slots, PRESERVE TYPE COVERAGE:
             - if the new move's type is ALREADY covered, only overwrite a WEAKER
               same-type move (a STAB/power upgrade); otherwise DECLINE — don't
               churn or lose a different type for a redundant one;
             - if the new move adds a type we LACK, free a redundant-type slot
               first (so no unique type is lost), else replace the weakest move.

        "Effective power" = base power x (Attack or Sp.Atk) x STAB — the same
        yardstick the stock `learn_best` uses, so choices stay sensible.
        Status-move *utility* ranking (e.g. valuing Sleep Powder over Growl) is a
        future refinement (punch-list #24-team); for now combat moves win."""
        DECLINE = 4
        if new_move.name in context.config.battle.banned_moves:
            return DECLINE

        moves = [lm.move if lm is not None else None for lm in pokemon.moves]

        def is_hm(m):
            return m is not None and m.tm_hm is not None and m.tm_hm.name.startswith("HM")

        def is_damaging(m):
            return m is not None and m.base_power > 0

        def effective_power(m):
            if m is None or not is_damaging(m):
                return 0.0
            if m.type.kind == "Physical":
                stat = pokemon.stats.attack
            elif m.type.kind == "Special":
                stat = pokemon.stats.special_attack
            else:
                stat = 1
            stab = 1.5 if m.type in pokemon.species.types else 1.0
            return m.base_power * stat * stab

        status_slots = [i for i, m in enumerate(moves) if m is not None and not is_damaging(m) and not is_hm(m)]
        damaging_slots = [i for i, m in enumerate(moves) if is_damaging(m) and not is_hm(m)]

        # New STATUS move: only ever replace another status slot (never a
        # damaging move or an HM). If no spare status slot, keep our attacks.
        if not is_damaging(new_move):
            return status_slots[0] if status_slots else DECLINE

        # New DAMAGING move.
        # (a) Overwrite a non-combat slot first — strictly upgrades the kit.
        if status_slots:
            return status_slots[0]
        # Every non-HM slot is now a damaging move; never touch an HM.
        if not damaging_slots:
            return DECLINE
        new_power = effective_power(new_move)
        current_types = [moves[i].type for i in damaging_slots]

        if new_move.type in current_types:
            # Redundant type: only take it to UPGRADE a weaker same-type move;
            # otherwise decline (don't lose a different type for a redundant one).
            weaker_same_type = [
                i for i in damaging_slots
                if moves[i].type == new_move.type and effective_power(moves[i]) < new_power
            ]
            if weaker_same_type:
                return min(weaker_same_type, key=lambda i: effective_power(moves[i]))
            return DECLINE

        # New TYPE coverage: free a redundant-type slot first (keep every unique
        # type), else replace the weakest damaging move.
        type_counts: dict = {}
        for t in current_types:
            type_counts[t] = type_counts.get(t, 0) + 1
        redundant_slots = [i for i in damaging_slots if type_counts[moves[i].type] > 1]
        pool = redundant_slots if redundant_slots else damaging_slots
        return min(pool, key=lambda i: effective_power(moves[i]))

    def should_allow_evolution(self, pokemon, party_index) -> bool:
        # A story auto-completer WANTS its team to evolve — stronger for gyms, and
        # it fixes the Lv-up handler collision the user hit at Treecko Lv16
        # (evolves + learns Pursuit at the same level): with the stock
        # `stop_evolution` default the evolution is force-CANCELLED, and the
        # cancelled-evolution + move-learn handoff can spin without stopping the
        # bot. Letting the evolution COMPLETE runs the well-tested evolve→learn
        # path instead. Always allow (this overrides `stop_evolution` for Story
        # battles). Ties to #24-evo / #24-team.
        return True


class StoryMode(BotMode):
    @staticmethod
    def name() -> str:
        return "Story"

    @staticmethod
    def is_selectable() -> bool:
        # Story mode can start from the title screen (fresh game) or in-game,
        # so it is always offered; run() sorts out which path applies.
        return True

    @staticmethod
    def is_selectable_from_title_screen() -> bool:
        # Unlike stock modes, Story Mode is MEANT to start at the title/main
        # menu — that's where it runs the New Game intro.
        return True

    def __init__(self):
        super().__init__()
        # DEFEAT RECOVERY (user directive 2026-07-21). Consecutive losses are counted
        # per LOCATION (map) so repeated faints at the same obstacle mean a power/level
        # problem → trigger a retrain. These live on the instance and survive whiteout
        # restarts because run() loops in place (it does NOT bounce through Manual).
        self._defeat_counts: dict = {}
        self._whiteout_pending = False
        self._last_defeat_key = None
        self._derails = 0  # consecutive non-whiteout derails (self-correct before Manual)
        self._last_derail_sig = None  # progress fingerprint at the last derail (see run())
        # Organic team-building (user directive 2026-07-21): catch NEW species while
        # travelling to Gym 1 until the party has this many members (starter + helpers).
        self._catch_team_target = 4

    def on_battle_ended(self, outcome) -> None:
        from modules.battle_state import BattleOutcome

        if outcome is BattleOutcome.Lost:
            key = self._location_key()
            self._defeat_counts[key] = self._defeat_counts.get(key, 0) + 1
            self._last_defeat_key = key
            console.print(
                f"[yellow]Story: lost a battle at map {key} "
                f"(defeat #{self._defeat_counts[key]} here).[/]"
            )

    def on_whiteout(self) -> bool:
        # We handle the whiteout ourselves — do NOT drop to Manual (and the watchdog
        # is hands-off for Story, so no save-state reload). Flag an abort so the
        # running segment bails out promptly; run() then re-orients from the respawn
        # Poké Center and resumes the segmented playthrough from where we left off.
        from modules.story.early_game import set_story_abort

        self._whiteout_pending = True
        set_story_abort(True)
        console.print(
            "[bold yellow]Story: whited out — recovering (navigating the respawn and "
            "resuming from where I left off; no save-state reload).[/]"
        )
        return True

    def _location_key(self):
        try:
            from modules.map import get_map_data_for_current_position

            d = get_map_data_for_current_position()
            return (d.map_group, d.map_number)
        except Exception:
            return None

    def defeat_count_at(self, location_key) -> int:
        return self._defeat_counts.get(location_key, 0)

    def _progress_sig(self):
        """A MONOTONIC fingerprint of story progress from the PARTY structure:
        size, lead level, and total accumulated EXP. These only ever move forward
        and — unlike event flags, which flicker while read during a battle→overworld
        transition — read reliably at any moment. run() compares it across derails
        to tell a transient hiccup mid-progress (a battle finished, a level or a
        Pokémon was gained → reset the derail budget) from a truly stuck loop
        (nothing advances → escalate to Manual). Deliberately excludes flags so a
        flickering flag can never fake progress and mask a genuine freeze."""
        try:
            from modules.pokemon_party import get_party

            party = get_party()
            lead_level = party[0].level if party else 0
            total_exp = sum(getattr(p, "total_exp", 0) for p in party)
            return (len(party), lead_level, total_exp)
        except Exception:
            return None

    def _log_localization(self, note: str) -> None:
        """Report WHERE WE ARE — story stage (from the flag-based detector) + physical
        map — so a derail is diagnosable and self-correction is visible, instead of a
        silent drop to Manual (user directive 2026-07-21)."""
        try:
            from modules.story import detect_live

            prog = detect_live()
            stage = f"{prog.chapter_key}: {prog.chapter_name}"
        except Exception:
            stage = "unknown stage"
        console.print(f"[yellow]Story localization — {note} | stage: {stage} | map {self._location_key()}[/]")

    def _should_catch(self, encounter) -> bool:
        """Pre-Gym-1 organic team-building (user directive 2026-07-21): catch a wild
        of a NEW species (never a dup we've already caught, never one already in the
        party) while there's room in the party. Only before the first gym, only once
        we have the Pokédex + Poké Balls, never a shiny (fight through — contingency)."""
        try:
            from modules.memory import get_event_flag
            from modules.pokemon_party import get_party
            from modules.pokedex import get_pokedex
            from modules.items import get_item_bag

            if encounter is None:  # trainer battle — never "catch"
                return False
            if getattr(encounter, "is_shiny", False):
                return False
            if get_event_flag("BADGE01_GET"):  # only before the first gym
                return False
            if not get_event_flag("RECEIVED_POKEDEX_FROM_BIRCH"):  # need balls + dex
                return False
            # RESOURCE-AWARE (planning doc §3): never ATTEMPT a catch without balls —
            # that's what broke the bot. Keep 1 in reserve; the catch phase restocks
            # (buys) or stops gracefully. Fight the wild instead when out of balls.
            if sum(s.quantity for s in get_item_bag().poke_balls) <= 1:
                return False
            party = [p for p in get_party() if p is not None and not p.is_egg]
            if len(party) >= self._catch_team_target:
                return False
            species = getattr(getattr(encounter, "pokemon", None), "species", None)
            if species is None:
                return False
            # Species objects aren't hashable — compare by national dex number.
            owned = {s.national_dex_number for s in get_pokedex().owned_species}
            party_dex = {p.species.national_dex_number for p in party}
            dex = species.national_dex_number
            return dex not in owned and dex not in party_dex
        except Exception:
            return False

    def _prepare_for_fight(self, cfg: dict) -> Generator:
        """Before a major fight, train the team to a sensible level (user directive
        2026-07-21). PROACTIVE: a target within the fight's level band (organic,
        randomized). REACTIVE: if we've already LOST here ≥2 times, escalate the
        target and train harder before re-attempting — the "+levels" strategy and
        the team scope are both randomized to look human/organic."""
        import random

        from modules.pokemon_party import get_party
        from modules.story.early_game import train_team

        losses = max((self._defeat_counts.get(k, 0) for k in cfg["keys"]), default=0)
        lo, hi = cfg["band"]
        target = random.randint(lo, hi)  # organic proactive target within the band
        if losses >= 2:
            levels = [p.level for p in get_party() if p is not None and not p.is_egg]
            team_max = max(levels, default=0)
            team_avg = (sum(levels) // len(levels)) if levels else 0
            choice = random.choice(["plus5_max", "plus5_avg", "escalate_band"])
            if choice == "plus5_max":
                target = max(target, team_max + 5)
            elif choice == "plus5_avg":
                target = max(target, team_avg + 5)
            else:
                target = max(target, hi + 2 * (losses - 1))
            console.print(
                f"[bold yellow]Story: lost here {losses}× — training harder before "
                f"re-attempting (target Lv {target}, {choice}).[/]"
            )
        scope = random.choice(["whole", "lead"])  # randomize team scope (organic)

        levels = [p.level for p in get_party() if p is not None and not p.is_egg]
        lead_level = get_party()[0].level if get_party() else 0
        need = (lead_level < target) if scope == "lead" else any(l < target for l in levels)
        if need:
            console.print(f"[cyan]Story: prepping for the fight — training to Lv {target} ({scope}).[/]")
            yield from train_team(target, scope=scope, grass=cfg["grass"], heal_center=cfg["heal"])
        else:
            console.print(f"[dim]Story: team already ≥ Lv {target} — no prep training needed.[/]")

    def on_battle_started(self, encounter):
        # Story battles (the first Birch battle, training, the rival) are meant
        # to be FOUGHT and won with the default battle strategy — never run from
        # or auto-caught. The BattleListener handles the fight while run() pauses.
        #
        # SHINY CONTINGENCY: if the wild in the scripted first battle (or any
        # story battle) happens to be shiny — extremely rare — we must NOT try
        # to catch it and must NOT stop; the story has to progress normally.
        # Returning Fight guarantees this: the default "shiny → stop the bot"
        # logic lives in handle_encounter(), which the framework only calls when
        # on_battle_started returns None. By returning Fight we bypass it
        # entirely (and the first battle is a Tutorial encounter, which the
        # framework forces to CustomAction anyway — also no halt).
        try:
            if encounter is not None and encounter.is_shiny:
                from modules.console import console

                species = getattr(getattr(encounter, "pokemon", None), "species", None)
                name = getattr(species, "name", "Pokémon")
                console.print(
                    f"[bold yellow]Story Mode: a SHINY {name} appeared in a story "
                    f"battle — fighting through as normal (NOT catching, NOT "
                    f"stopping), per the contingency.[/]"
                )
                context.message = (
                    f"Story: a shiny {name} appeared in a story battle — fighting "
                    "through (not catching)."
                )
        except Exception:
            pass
        # PRE-GYM-1 CATCHING (user directive 2026-07-21): build an organic team by
        # catching NEW species (never a dup) while travelling to the first gym.
        try:
            if self._should_catch(encounter):
                from modules.console import console
                from modules.modes import BattleAction

                sp = getattr(getattr(encounter, "pokemon", None), "species", None)
                console.print(f"[bold green]Story: catching a new {getattr(sp, 'name', '?')} for the team![/]")
                return BattleAction.Catch
        except Exception:
            pass
        # Fight to WIN and level the lead (strongest move; flees only at low HP,
        # which the training loop covers by healing). The travel variant also
        # refuses to flee a TRAINER battle (single-mon party can't — see ML-8),
        # fighting on instead; used for training wilds, the rival, and route
        # trainers. The scripted first battle is a Tutorial (framework-handled).
        return LevelUpTravelBattleStrategy()

    def run(self) -> Generator:
        # DEFEAT / WHITEOUT RECOVERY (user directive 2026-07-21): the segmented resume
        # (`_play`) runs inside a restart loop. On a whiteout, on_whiteout() flags an
        # abort → the running segment bails → we catch it here, re-orient from the
        # respawn point, and re-run `_play` (which skips finished segments and
        # re-attempts the failed one). GENUINE (non-whiteout) errors propagate to
        # Manual exactly as before. No save states are ever reloaded.
        from modules.modes import BotModeError
        from modules.story.early_game import set_story_abort, exit_building_after_whiteout
        from modules.modes.util.walking import wait_for_player_avatar_to_be_controllable

        recoveries = 0
        while True:
            set_story_abort(False)
            self._whiteout_pending = False
            try:
                yield from self._play()
                return
            except BotModeError as err:
                from modules.memory import game_has_started, get_game_state, GameState

                if not self._whiteout_pending:
                    # NON-WHITEOUT DERAIL (user directive 2026-07-21): don't drop
                    # straight to Manual — re-localise (log where we are in the story
                    # AND on the map) and retry the segmented resume a bounded number
                    # of times. The resume re-detects the stage from flags + position,
                    # so a transient nav/scene hiccup self-corrects. Only hand to
                    # Manual if it keeps failing (a genuine, persistent problem).
                    # Reset the budget when we've made real progress since the last
                    # derail: a long segment (training, a chapter) can throw a few
                    # unrelated transient hiccups, and those must NOT accumulate into
                    # a false drop to Manual. Only CONSECUTIVE no-progress derails —
                    # a genuine stuck loop — escalate.
                    sig = self._progress_sig()
                    if sig != self._last_derail_sig:
                        self._derails = 0
                        self._last_derail_sig = sig
                    self._derails += 1
                    self._log_localization(f"derail #{self._derails}: {err}")
                    try:
                        from modules import debug_logger

                        debug_logger.event(f"DERAIL #{self._derails}: {err}")
                    except Exception:
                        pass
                    if self._derails > 4:
                        raise
                    set_story_abort(False)
                    try:
                        # Patiently ride out the post-battle transition before retrying.
                        # These stalls SELF-HEAL (the overworld becomes controllable on
                        # its own) but the controllable flag flickers first, so waiting
                        # for a STABLE controllable window here lets a SINGLE recovery
                        # ride out the whole stall instead of burning many rapid derail
                        # cycles toward Manual.
                        from modules.story.early_game import wait_until_truly_controllable

                        yield from wait_until_truly_controllable(timeout_frames=3000)
                        yield from exit_building_after_whiteout()
                        settle = 0
                        while settle < 300 and not (
                            game_has_started() and get_game_state() is GameState.OVERWORLD
                        ):
                            settle += 1
                            yield
                    except Exception:
                        yield
                    continue  # re-run _play(): re-localise from flags + position
                # --- WHITEOUT recovery ---
                recoveries += 1
                self._derails = 0  # reaching a fight = progress; reset the derail budget
                try:
                    from modules import debug_logger

                    debug_logger.event(f"WHITEOUT recovery #{recoveries}")
                except Exception:
                    pass
                if recoveries > 40:
                    raise BotModeError(
                        "Story: too many whiteout recoveries in a row — stopping so I "
                        "don't loop forever. Check the team/route."
                    )
                self._whiteout_pending = False
                set_story_abort(False)
                console.print(
                    "[cyan]Story: recovered from the whiteout — re-orienting at the "
                    "respawn point and resuming.[/]"
                )

                try:
                    yield from wait_for_player_avatar_to_be_controllable()
                    # Respawn lands us INSIDE the Poké Center — step out to the town
                    # so the segmented resume's map checks work (else it backtracks).
                    yield from exit_building_after_whiteout()
                    # SETTLE: right after the exit warp the game is transiently
                    # "not started" / in a non-overworld state — re-running _play now
                    # would misfire its title check into the New-Game intro. Wait for
                    # a stable started+overworld state first.
                    settle = 0
                    while settle < 600 and not (
                        game_has_started() and get_game_state() is GameState.OVERWORLD
                    ):
                        settle += 1
                        yield
                    yield from wait_for_player_avatar_to_be_controllable()
                except BotModeError:
                    raise
                except Exception:
                    yield
                # loop → re-run the segmented resume from the respawn point

    def _play(self) -> Generator:
        import random

        from modules.memory import get_event_flag
        from modules.map import get_map_data_for_current_position
        from modules.map_data import MapRSE
        from modules.story import detect_live
        from modules.story.config import get_story_config
        from modules.story.intro import run_intro
        from modules.story.early_game import (
            cross_petalburg_woods,
            descend_and_leave_players_house,
            do_petalburg_gym_and_wally_tutorial,
            do_rustboro_gym,
            finish_birch_lab,
            fight_route103_rival,
            go_upstairs_and_set_clock,
            help_birch_and_choose_starter,
            recover_devon_goods,
            return_to_lab_and_get_pokedex,
            train_lead_to_level,
            travel_route104_north_to_rustboro,
            travel_to_petalburg,
            travel_to_petalburg_woods,
            travel_to_route103,
            visit_rivals_house,
            walk_off_truck_and_into_house,
        )

        cfg = get_story_config(context.profile.path)

        def _done(flag: str) -> bool:
            try:
                return bool(get_event_flag(flag))
            except Exception:
                return False

        def _cur_map():
            try:
                d = get_map_data_for_current_position()
                return (d.map_group, d.map_number)
            except Exception:
                return None

        def _has_starter() -> bool:
            """True once the player owns a (non-egg) Pokémon — i.e. we are PAST the
            scripted intro. Lets a mid-Segment-1 recovery skip the truck→lab cutscene
            and resume at training rather than trying (and failing) to re-run the
            intro from wherever we respawned."""
            try:
                from modules.pokemon_party import get_party

                return any(not getattr(p, "is_egg", False) for p in get_party())
            except Exception:
                return False

        from modules.modes import BotModeError

        def _guard(label: str, done_check) -> None:
            """SELF-CORRECTION (§SC): after a segment, confirm it actually reached
            its completion signal. If not, the bot silently derailed (a mis-warp,
            a lost battle/blackout, or a skipped beat) — STOP with a diagnostic
            rather than blindly marching on and compounding the error. Re-running
            Story then resumes correctly from the REAL state (§RS)."""
            if done_check():
                return
            try:
                prog = detect_live()
                where = f"{prog.chapter_key}: {prog.chapter_name}"
            except Exception:
                where = "unknown"
            raise BotModeError(
                f"Story self-check: '{label}' didn't reach its completion signal "
                f"(now {where}, map {_cur_map()}). Stopping so I don't derail "
                "further — just run Story again and it resumes correctly from here."
            )

        # RESUME MODEL: the story is linear, so we run each SEGMENT only if its
        # completion signal isn't already set — a fresh game runs everything; a
        # resumed save (or one you hand-played partway) skips what's done and
        # continues from the right place. See design §RS. (Segments self-locate
        # via navigation; the Woods segment also picks its sub-entry by current
        # map so a resume mid-Woods doesn't backtrack to Petalburg.) After each
        # segment a _guard() self-check confirms it truly completed (§SC).
        at_title = get_game_state() is GameState.TITLE_SCREEN or not game_has_started()
        if not at_title:
            try:
                progress = detect_live()
                console.print(
                    f"[bold cyan]Story Mode — resuming[/] (detected {progress.chapter_key}: "
                    f"{progress.chapter_name}); skipping what's already done."
                )
            except Exception:
                pass

        # --- Chapter 0: New Game intro. Title screen only — mid-intro isn't a
        #     resumable point (it must run from the truck). A title screen WITH an
        #     existing save should be loaded via Continue first (TODO §RS). ---
        if at_title:
            console.print(
                f"[bold cyan]Story Mode — new game[/] as [bold]{cfg.character_name}[/] ({cfg.gender})."
            )
            yield from run_intro(cfg.character_name, cfg.gender)

        # --- Segment 1: truck → house → clock → rival → starter → first battle →
        #     lab → train → rival → Pokédex. Gated by the Pokédex flag so a resumed
        #     game past this point skips it. INTERNALLY split into two parts so a
        #     mid-Segment-1 recovery (whiteout/derail during training) resumes
        #     correctly instead of re-running the scripted intro from the truck —
        #     which can't navigate back to the house and loops/derails (user-seen
        #     "stuck at the Oldale Poké Center after respawn"). ---
        if not _done("RECEIVED_POKEDEX_FROM_BIRCH"):
            if not _has_starter():
                # Part A — the scripted intro (truck → clock → rival house →
                # starter → first battle → lab → up to Route 103). This is a linear
                # cutscene run that ONLY works from the truck, so it is NOT a
                # resumable point: run it only while the starter doesn't exist yet.
                yield from walk_off_truck_and_into_house()
                yield from go_upstairs_and_set_clock()
                yield from descend_and_leave_players_house()
                yield from visit_rivals_house()
                yield from help_birch_and_choose_starter(cfg.starter)
                yield from finish_birch_lab(cfg.starter_nickname)
                yield from travel_to_route103()
            else:
                console.print(
                    "[dim]Story: resuming with a starter but no Pokédex — skipping the "
                    "scripted intro, back to training on Route 103.[/]"
                )
            # Part B — train → rival → Pokédex. RESUMABLE from anywhere: each step
            # self-locates (navigate_to_anywhere / _navigate_through_scripts) and is
            # gated by its own flag, so a recovery here picks up at the right place.
            if not _done("DEFEATED_RIVAL_ROUTE103"):
                target_level = random.randint(8, 10)
                console.print(f"[cyan]Story: training the starter to Lv {target_level} before the rival.[/]")
                yield from train_lead_to_level(target_level)
                yield from fight_route103_rival()
            else:
                console.print("[dim]Story: rival already beaten — heading back for the Pokédex.[/]")
            yield from return_to_lab_and_get_pokedex()
        else:
            console.print("[dim]Story: already have the Pokédex — skipping the intro chapters.[/]")
        _guard("intro → Pokédex", lambda: _done("RECEIVED_POKEDEX_FROM_BIRCH"))

        # --- Segment 2: Petalburg City — Dad (Norman) + Wally catching tutorial.
        #     Completion signal: Wally's mum leaves Petalburg (HIDE_..._WALLYS_MOM);
        #     the "intended" THANKED_FOR_PLAYING_WITH_WALLY is never set (ML-9). ---
        if not _done("HIDE_PETALBURG_CITY_WALLYS_MOM"):
            yield from travel_to_petalburg()
            yield from do_petalburg_gym_and_wally_tutorial()
        else:
            console.print("[dim]Story: Petalburg / Wally tutorial already done — skipping.[/]")
        _guard("Petalburg / Wally", lambda: _done("HIDE_PETALBURG_CITY_WALLYS_MOM"))

        # --- Segment 3: Route 104 → Petalburg Woods → Rustboro. Enter at the
        #     right sub-step by current map so a mid-Woods resume doesn't backtrack. ---
        rustboro = MapRSE.RUSTBORO_CITY.value
        woods = MapRSE.PETALBURG_WOODS.value
        _in_rustboro = lambda: _cur_map() == rustboro or _done("BADGE01_GET")
        if _in_rustboro():
            console.print("[dim]Story: already in Rustboro — skipping the Woods travel.[/]")
        elif _cur_map() == woods:
            console.print("[cyan]Story: resuming inside Petalburg Woods — finishing the crossing.[/]")
            yield from cross_petalburg_woods()
            yield from travel_route104_north_to_rustboro()
        else:
            yield from travel_to_petalburg_woods()
            yield from cross_petalburg_woods()
            yield from travel_route104_north_to_rustboro()
        _guard("Route 104 → Rustboro", _in_rustboro)

        # --- Segment 4: Gym 1 — Roxanne (Stone Badge). Train the team to a sensible
        #     level FIRST (threshold ≈ boss ace + margin, plus a retrain if we've
        #     already lost here — user directive 2026-07-21). ---
        if not _done("BADGE01_GET"):
            from modules.map_data import PokemonCenter
            from modules.story.early_game import RUSTBORO_TRAINING_GRASS, catch_starter_team

            roxanne_fight = {
                "keys": [MapRSE.RUSTBORO_CITY_GYM.value, MapRSE.RUSTBORO_CITY.value],
                "band": (13, 17),  # user: team between Lv 13-17 before Roxanne
                "grass": RUSTBORO_TRAINING_GRASS,
                "heal": PokemonCenter.RustboroCity,
            }
            # Build an organic team (catch new species) BEFORE training + the gym.
            yield from catch_starter_team(self._catch_team_target)
            yield from self._prepare_for_fight(roxanne_fight)
            yield from do_rustboro_gym()
        else:
            console.print("[dim]Story: Stone Badge already earned — Gym 1 skipped.[/]")
        _guard("Gym 1 (Roxanne)", lambda: _done("BADGE01_GET"))

        # --- Segment 5a: Devon Goods errand — chase the thief to Rusturf Tunnel and
        #     recover the goods (+ free Peeko). Completion: RECOVERED_DEVON_GOODS.
        #     (The return leg — Devon Corp president → PokéNav — and the Rustboro
        #     rival are the next build; see design §Ch5.) ---
        if not _done("RECOVERED_DEVON_GOODS"):
            yield from recover_devon_goods()
        else:
            console.print("[dim]Story: Devon Goods already recovered — skipping.[/]")
        _guard("Devon Goods (Rusturf Tunnel)", lambda: _done("RECOVERED_DEVON_GOODS"))

        context.message = (
            "Story: caught up to the end of the built content (through recovering the "
            "Devon Goods in Rusturf Tunnel). The rest of Chapter 5 (return to Devon "
            "Corp for the PokéNav -> Rustboro rival) isn't built yet; handing to manual."
        )
        console.print(f"[bold green]{context.message}")
        context.set_manual_mode()
        return
