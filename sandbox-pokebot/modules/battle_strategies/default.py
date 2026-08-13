from typing import Optional

from modules.battle_state import BattleState, BattlePokemon, get_battle_state
from modules.context import context
from modules.modes._interface import BotModeError
from modules.pokemon import Pokemon, Move, LearnedMove, get_ability_by_name
from modules.pokemon_party import get_party
from ._interface import BattleStrategy, TurnAction, SafariTurnAction
from ._util import BattleStrategyUtil


class DefaultBattleStrategy(BattleStrategy):
    def __init__(self):
        self._first_non_fainted_party_index_before_battle = get_party().first_non_fainted.index

    def party_can_battle(self) -> bool:
        return any(self.pokemon_can_battle(pokemon) for pokemon in get_party())

    def pokemon_can_battle(self, pokemon: Pokemon) -> bool:
        if pokemon.is_egg or not self._pokemon_has_enough_hp(pokemon):
            return False

        return any(self._move_is_usable(move) for move in pokemon.moves)

    def which_move_should_be_replaced(self, pokemon: Pokemon, new_move: Move) -> int:
        # SINGLE decision point for move-learning, used by every leveling bot
        # (all inherit DefaultBattleStrategy). Returns 0-3 = replace that slot,
        # or 4 = decline (keep current moves). Config `battle.new_move`:
        #   "cancel" (fork default) -> always decline, hunt is never interrupted
        #   "stop"                  -> drop to Manual on a new move
        #   "learn_best"            -> power-based auto-replace (below)
        # FUTURE-INTELLIGENCE SEAM: smarter "is this move worth keeping / what
        # to replace" logic belongs in the `learn_best` branch below (or a new
        # `new_move` value); the config gate + this method are the only place
        # the whole bot decides move learning.
        if context.config.battle.new_move == "stop":
            context.message = f"{pokemon.name} is attempting to learn {new_move.name}. Switching to manual mode."
            context.set_manual_mode()
            return 4

        if context.config.battle.new_move == "cancel":
            return 4

        # Do not learn move if new move is banned.
        if new_move.name in context.config.battle.banned_moves:
            context.message = f"{new_move.name} is on the block list, so {pokemon.name} will skip learning it."
            return 4

        # FORK (2026-07-22, KI-13): never LEARN a 0-power move. The bot's strategies
        # only ever select damaging moves, so a status move is a dead slot — and the
        # auto-replace cost Marshtomp its only Ground attack (Mud-slap) for MUD SPORT
        # right before an all-Electric gym (run 10 lost to Wattson 8 times on it).
        if new_move.base_power == 0:
            context.message = f"{new_move.name} has no attack power, so {pokemon.name} will skip learning it."
            return 4

        move_choices = [*[move.move for move in pokemon.moves], new_move]

        # Get the effective power of each move
        move_powers = []
        for move in move_choices:
            if move.name in context.config.battle.banned_moves:
                move_powers.append(0)
                continue

            # Never attempt to replace HMs because that won't work.
            if move.tm_hm is not None and move.tm_hm.name.startswith("HM"):
                move_powers.append(9999)
                continue

            match move.type.kind:
                case "Physical":
                    stat_multiplier = pokemon.stats.attack
                case "Special":
                    stat_multiplier = pokemon.stats.special_attack
                case _:
                    stat_multiplier = 1

            same_type_attack_bonus = 1
            if move.type in pokemon.species.types:
                same_type_attack_bonus = 1.5

            move_powers.append(move.base_power * stat_multiplier * same_type_attack_bonus)

        # Find the weakest move of the bunch
        weakest_move = move_powers.index(min(move_powers))

        # Try and aim for good coverage: It's generally better to have a wide array of move types
        # than 4 moves of the same type.
        redundant_type_moves = []
        existing_move_types = {}
        for move_index in range(len(move_choices)):
            move = move_choices[move_index]
            if move.base_power == 0:
                continue
            if move.type not in existing_move_types:
                existing_move_types[move.type] = move_index
            else:
                if not redundant_type_moves:
                    redundant_type_moves.append(existing_move_types[move.type])
                redundant_type_moves.append(move_index)

        if move_powers[weakest_move] > 0 and redundant_type_moves:
            redundant_move_powers = [move_powers[move_index] for move_index in redundant_type_moves]
            redundant_move = redundant_type_moves[redundant_move_powers.index(min(redundant_move_powers))]
            context.message = f"Replacing move {move_choices[redundant_move].name} because a stronger move of that type is already known, in order to maximise coverage."
            return redundant_move

        context.message = f"Replacing move {move_choices[weakest_move].name} because it is the weakest one (calculated power: {move_powers[weakest_move]})"

        return weakest_move

    def should_allow_evolution(self, pokemon: Pokemon, party_index: int) -> bool:
        if context.bot_mode_instance is None:
            return True
        else:
            return (
                context.bot_mode_instance.on_pokemon_evolving_after_battle(pokemon, party_index)
                and not context.config.battle.stop_evolution
            )

    def should_flee_after_faint(self, battle_state: BattleState) -> bool:
        if context.config.battle.faint_action == "stop":
            context.message = "Active Pokémon fainted. Switching to manual mode."
            context.set_manual_mode()
        elif context.config.battle.faint_action == "flee":
            if battle_state.is_trainer_battle:
                context.message = "Active Pokémon fainted. `faint_action` is set to `flee`, but this is a trainer battle. Switching to manual mode."
                context.set_manual_mode()
            return True
        elif not self.party_can_battle():
            return True
        else:
            return False

    def choose_new_lead_after_faint(self, battle_state: BattleState) -> int:
        new_lead: int | None = None
        new_lead_current_hp: int = 0
        party = get_party()

        # ‼‼ IN A MULTI BATTLE, HALF OF `gPlayerParty` BELONGS TO THE ALLY — AND THEY SCORE BEST.
        # `SPECIAL_BATTLE_STEVEN` (the Mossdeep Space Center) runs
        # `ReducePlayerPartyToSelectedMons` and then `FillPartnerParty`, which writes Steven's
        # Metang L42 / Skarmory L43 / Aggron L44 into `gPlayerParty[3..5]` and sets the party count
        # to 6. `get_party()` therefore returns SIX Pokémon, only the first three of which are ours.
        # The loop below excludes just the two mons currently ON THE FIELD, so the ally's benched
        # pair are always candidates — and because the rule is "highest current HP wins", his fresh
        # max-IV L42-44 mons BEAT our damaged party every time. The game then refuses the switch
        # ("Can't switch with ALLY!") and the party menu is handed a choice it will never accept.
        # `MULTI_PARTY_SIZE` is 3, which is why the cut is at 3.
        # ‼ The property to test this with already existed and had ZERO callers anywhere in the
        # tree — the guard was written and then never wired up. §Ch19 is the first content in this
        # project to reach a multi battle, so this has been latent rather than harmless.
        own_party_size = len(party)
        if battle_state.is_double_battle_with_partner:
            own_party_size = min(own_party_size, 3)

        for index in range(own_party_size):
            pokemon = party[index]
            if battle_state.is_double_battle and (
                (
                    battle_state.own_side.left_battler is not None
                    and battle_state.own_side.left_battler.party_index == index
                )
                or (
                    battle_state.own_side.right_battler is not None
                    and battle_state.own_side.right_battler.party_index == index
                )
            ):
                continue
            if not pokemon.is_egg and pokemon.current_hp > 0 and pokemon.current_hp > new_lead_current_hp:
                new_lead = index
                new_lead_current_hp = pokemon.current_hp
        return new_lead

    def choose_new_lead_after_battle(self) -> int | None:
        party = get_party()
        if not self.pokemon_can_battle(party[self._first_non_fainted_party_index_before_battle]):
            util = BattleStrategyUtil(get_battle_state())
            return util.select_rotation_target()

        return None

    def decide_turn(self, battle_state: BattleState) -> tuple["TurnAction", Optional[any]]:
        """
        Decides the action to take for the current turn based on the battle state.
        """
        util = BattleStrategyUtil(battle_state)

        if not util.pokemon_has_enough_hp(battle_state.own_side.active_battler):
            return self._handle_lead_cannot_battle(battle_state, util, reason="HP below threshold")

        strongest_move = util.get_strongest_move_against(
            battle_state.own_side.active_battler, battle_state.opponent.active_battler
        )
        if strongest_move is not None:
            return TurnAction.use_move(strongest_move)

        return self._handle_lead_cannot_battle(battle_state, util, reason="No damaging moves available")

    def decide_turn_in_double_battle(self, battle_state: BattleState, battler_index: int) -> tuple["TurnAction", any]:
        util = BattleStrategyUtil(battle_state)
        battler = battle_state.own_side.left_battler if battler_index == 0 else battle_state.own_side.right_battler
        partner = battle_state.own_side.right_battler if battler_index == 0 else battle_state.own_side.left_battler
        pokemon = get_party()[battler.party_index]
        partner_pokemon = get_party()[partner.party_index] if partner is not None else None

        if not util.pokemon_has_enough_hp(pokemon):
            if partner_pokemon is None or not util.pokemon_has_enough_hp(partner_pokemon):
                # FORK FIX (2026-07-22): the stock call omitted the REQUIRED `reason`
                # argument — a TypeError here crashed the battle listener and dropped the
                # bot to Manual MID-DOUBLE-BATTLE (the user-reported "double battle bug";
                # reproduced via the KI-12 faint-bench harness repro).
                return self._handle_lead_cannot_battle(battle_state, util, reason="HP below threshold (double battle)")

        left_opponent = battle_state.opponent.left_battler
        right_opponent = battle_state.opponent.right_battler

        def first_available_move():
            for index, learned_move in enumerate(battler.moves):
                if (
                    learned_move is not None
                    and learned_move.pp > 0
                    and battler.disabled_move is None
                    or battler.disabled_move is not learned_move.move
                ):
                    return index
            return 0

        if left_opponent is not None:
            strongest_move = util.get_strongest_move_against(battler, left_opponent)
            if strongest_move is not None:
                return TurnAction.use_move_against_left_side_opponent(strongest_move)
            else:
                return TurnAction.use_move_against_left_side_opponent(first_available_move())

        if right_opponent is not None:
            strongest_move = util.get_strongest_move_against(battler, right_opponent)
            if strongest_move is not None:
                return TurnAction.use_move_against_right_side_opponent(strongest_move)
            else:
                return TurnAction.use_move_against_right_side_opponent(first_available_move())

        return self._handle_lead_cannot_battle(battle_state, util, reason="No damaging moves available")

    def decide_turn_in_safari_zone(self, battle_state: BattleState) -> tuple["SafariTurnAction", any]:
        return SafariTurnAction.switch_to_manual()

    def _move_is_usable(self, move: LearnedMove):
        return (
            move is not None
            and move.move.base_power > 0
            and move.pp > 0
            and move.move.name not in context.config.battle.banned_moves
        )

    def _pokemon_has_enough_hp(self, pokemon: Pokemon | BattlePokemon):
        return pokemon.current_hp_percentage > context.config.battle.hp_threshold

    # ‼‼ KI-52 (user directive, 2026-08-11): NEVER WEDGE MID-BATTLE. FIGHT IT OUT.
    #
    # WHAT HAPPENED. Driving the Magma Hideout, a wild **Torkoal** ground the lead down and the
    # bot stopped dead with FIVE HEALTHY POKÉMON ON THE BENCH:
    #     Bot stopped: Your Pokémon cannot battle due to HP below threshold, and escape is
    #     not possible.
    #     party=['Sceptile L46 10/128', 'Zigzagoon 24/24', 'Swellow 112/112',
    #            'Skitty 45/45', 'Mightyena 127/127', 'Castform 100/100']
    # It then sat in Manual, MID-BATTLE, for 18,000+ frames. Reproduced byte-identically twice.
    #
    # ‼ THE POLICY ONLY EVER LOOKED AT THE LEAD. `lead_cannot_battle_action` is `flee` (the
    # upstream default) and asks "can the LEAD fight?", never "can ANYONE fight?". When flee then
    # turned out to be impossible there was no third option, so it raised.
    #
    # THE USER'S DIRECTIVE: add a fallback that simply carries the fight through to a natural win
    # or loss rather than getting wedged. A lost battle is a recoverable event this project
    # already handles (whiteout recovery); a bot frozen inside a battle is not — nothing can
    # recover it, because the derail riders ride SCRIPTS and a battle is not one.
    #
    # ‼ WHY THIS IS SAFE FROM THE "unbounded loop" FAMILY (KI-34's shape): this does NOT loop. It
    # returns ONE action for ONE turn, exactly like every other branch. The bound is the battle
    # itself, which always terminates in a win, a loss or a successful escape.
    #
    # ‼ ORDER MATTERS AND IS DELIBERATE: rotate (keep fighting with a healthy mon) → flee (leave
    # cheaply) → FIGHT ON (never freeze). Escaping is preferred over fighting with a dying lead
    # because fleeing costs nothing, but being UNABLE to escape must not be fatal.
    def _handle_lead_cannot_battle(
        self, battle_state: BattleState, util: BattleStrategyUtil, reason: str
    ) -> tuple["TurnAction", Optional[any]]:
        """
        Handles situations where the lead Pokémon cannot battle due to low HP or lack of damaging moves.
        """
        lead_action = context.config.battle.lead_cannot_battle_action

        # FAULT INJECTION for the A/B: restore the pre-fix behaviour (raise instead of fighting
        # on), so the wedge can be re-measured without reverting code. Default 0 = fixed.
        import os as _os

        legacy = _os.environ.get("POKEBOT_LEADCANTBATTLE_A", "0") == "1"

        if lead_action == "flee":
            return self._handle_flee(battle_state, util, reason, legacy=legacy)

        if lead_action == "rotate":
            return self._handle_rotate(battle_state, util, legacy=legacy)

        if legacy:
            raise BotModeError(f"Your Pokémon cannot battle due to {reason}, switching to manual mode...")
        return self._fight_on(battle_state, util, reason, why="lead_cannot_battle_action is 'stop'")

    def _fight_on(
        self, battle_state: BattleState, util: BattleStrategyUtil, reason: str, why: str
    ) -> tuple["TurnAction", Optional[any]]:
        """LAST RESORT: keep battling until the fight resolves naturally. Never raises.

        Picks the strongest move it can find; if the strategy can't rank one (no PP, every move
        banned, an unreadable move table) it falls back to move slot 0 — the game itself
        substitutes Struggle when nothing is usable, which still ENDS the battle. The one thing
        this must never do is hand back an action the caller can't execute.
        """
        try:
            move = util.get_strongest_move_against(
                battle_state.own_side.active_battler, battle_state.opponent.active_battler
            )
        except Exception:  # noqa: BLE001 - a ranking error must not become a wedge
            move = None
        if move is None:
            move = 0
        # LOUD, because this is the branch that used to end the run. `[BATTLE]` keeps it in the
        # same surface as the per-turn telemetry, so a batch can count how often it fires.
        try:
            from modules import debug_logger

            debug_logger.event(
                f"[KI-52] lead cannot battle ({reason}); {why} -> FIGHTING ON with move slot "
                f"{move} instead of stopping",
                category="BATTLE",
            )
        except Exception:  # noqa: BLE001
            pass
        return TurnAction.use_move(move)

    def _handle_flee(
        self, battle_state: BattleState, util: BattleStrategyUtil, reason: str, legacy: bool = False
    ) -> tuple["TurnAction", Optional[any]]:
        """
        Handles the flee action when the lead Pokémon cannot battle.
        """
        # ‼ KI-52: a TRAINER battle can never be fled (decomp `TryRunFromBattle`: the
        # `BATTLE_TYPE_TRAINER` branch never reaches the run formula). That is not an error
        # condition — it is the normal state of every gym, rival and boss fight. **Rotate if we
        # can, otherwise fight.** Raising here used to end the run inside built story content.
        if battle_state.is_trainer_battle:
            if legacy:
                raise BotModeError(
                    f"Your Pokémon cannot battle due to {reason}, and 'flee' is not allowed in a trainer battle."
                )
            if len(util.get_potential_rotation_targets(battle_state)) > 0 and util.can_switch():
                return TurnAction.rotate_lead(util.select_rotation_target(battle_state))
            return self._fight_on(battle_state, util, reason, why="trainer battle, cannot flee")

        best_escape_method = util.get_best_escape_method()
        if best_escape_method is not None:
            return best_escape_method

        if legacy:
            raise BotModeError(f"Your Pokémon cannot battle due to {reason}, and escape is not possible.")
        # Escape is impossible THIS TURN. Prefer a healthy mon; otherwise fight it out.
        # ‼ Do NOT keep re-attempting the run: when the block is a TRAPPING ability or move it is
        # permanent for as long as that battler is out, so retrying is a guaranteed wasted turn
        # while the lead keeps taking damage. See `_escape_block_reason` for what can cause it.
        if len(util.get_potential_rotation_targets(battle_state)) > 0 and util.can_switch():
            return TurnAction.rotate_lead(util.select_rotation_target(battle_state))
        return self._fight_on(
            battle_state, util, reason, why=f"escape impossible ({self._escape_block_reason(battle_state, util)})"
        )

    @staticmethod
    def _escape_block_reason(battle_state: BattleState, util: BattleStrategyUtil) -> str:
        """Name WHY escape/switching is blocked, for the log. Never raises.

        ‼‼ THE GEN 3 TRAPPING SET, decomp-verified 2026-08-11 against `pret/pokeemerald`
        (`src/battle_util.c` `TryRunFromBattle`, `src/battle_script_commands.c`
        `Cmd_jumpifcantswitch`). Both switching and fleeing are blocked by:
          * **STATUS2_ESCAPE_PREVENTION** — set by `EFFECT_MEAN_LOOK`: **Mean Look, Block,
            Spider Web**.
          * **STATUS2_WRAPPED** — the partial-trapping moves: **Wrap, Bind, Fire Spin, Clamp,
            Whirlpool, Sand Tomb**.
          * **STATUS3_ROOTED** — **Ingrain** (self-inflicted; traps the USER).
          * Trapping ABILITIES on the opponent: **Shadow Tag** (all), **Arena Trap** (except
            Flying types and Levitate holders), **Magnet Pull** (Steel types only).
        Guaranteed ESCAPE, by contrast: the **Run Away** ability, or a **Smoke Ball** held item.

        ‼ MESSAGES the game prints, so a human reading a log can recognise these
        (`src/battle_message.c`, exact strings):
            "{MON} prevents\\nescape with {ABILITY}!"   <- a trapping ABILITY
            "Can't escape!"                             <- a failed run attempt
            "{MON} can't escape!"                       <- attacker trapped (wrapped/mean-looked)
            "{MON} can't\\nescape now!"                 <- target just trapped by Mean Look etc.

        ‼ SUCTION CUPS IS **NOT** IN THIS LIST AND THAT IS DELIBERATE. It prevents being FORCED
        out (Roar / Whirlwind); it does not stop voluntary switching or running, and the existing
        `get_best_escape_method` already models it correctly by refusing to use Roar against a
        Suction Cups holder. ‼ UNVERIFIED: its Gen 3 implementation was NOT located in the decomp
        during this pass — treat the "prevents forced switch only" reading as the working model,
        not as decomp-confirmed.
        """
        try:
            battler = battle_state.own_side.active_battler
            temps = {getattr(t, "name", str(t)) for t in (battler.status_temporary or [])}
            for name, label in (
                ("EscapePrevention", "Mean Look / Block / Spider Web"),
                ("Wrapped", "a partial-trapping move (Wrap/Bind/Fire Spin/Clamp/Whirlpool/Sand Tomb)"),
                ("Rooted", "Ingrain"),
            ):
                if name in temps:
                    return label
            for ability in ("Shadow Tag", "Arena Trap", "Magnet Pull"):
                try:
                    if battle_state.opponent.has_ability(get_ability_by_name(ability)):
                        return f"the opponent's {ability}"
                except Exception:  # noqa: BLE001
                    continue
            # ‼ NOT trapped, yet the run still scored 0. That is the Gen 3 run formula's own u8
            # WRAPAROUND — decomp `TryRunFromBattle`: `u8 speedVar = (speed*128)/oppSpeed +
            # runTries*30;`. It really can land on 0, and the game then just fails that ONE
            # attempt (`runTries++` changes the next one). Our reader turns that single-turn 0
            # into "impossible", which is why this branch can fire on a mon that is plainly
            # faster than its opponent.
            return "no trap found — likely the run formula's u8 wraparound, which is per-turn, not permanent"
        except Exception as error:  # noqa: BLE001
            return f"unreadable ({type(error).__name__})"

    def _handle_rotate(
        self, battle_state: BattleState, util: BattleStrategyUtil, legacy: bool = False
    ) -> tuple["TurnAction", Optional[any]]:
        """
        Handles the rotate action when the lead Pokémon cannot battle.
        """
        if len(util.get_potential_rotation_targets(battle_state)) > 0 and util.can_switch():
            return TurnAction.rotate_lead(util.select_rotation_target(battle_state))

        if legacy:
            raise BotModeError(
                "Your Pokémon cannot battle, 'lead_cannot_battle_action' is set to 'rotate', but no eligible Pokémon are available for switching."
            )
        # ‼ KI-52: no eligible switch is the NORMAL end-state of a hard fight (everyone else
        # fainted, or a trapping ability is holding this mon in). Fight it out.
        return self._fight_on(
            battle_state,
            util,
            "no eligible Pokémon to switch to",
            why=f"rotate blocked ({self._escape_block_reason(battle_state, util)})",
        )
