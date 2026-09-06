from modules.battle_state import BattleState
from modules.battle_strategies import DefaultBattleStrategy, TurnAction, BattleStrategyUtil
from modules.battle_strategies.default import ally_party_indices
from modules.context import context
from modules.pokemon import Pokemon, StatusCondition
from modules.pokemon_party import get_party


class LevelUpLeadBattleStrategy(DefaultBattleStrategy):

    def choose_new_lead_after_battle(self) -> int | None:
        return None

    def decide_turn(self, battle_state: BattleState) -> tuple["TurnAction", any]:
        """
        Decides the turn's action based on the current battle state.
        """
        util = BattleStrategyUtil(battle_state)
        current_battler = battle_state.own_side.active_battler

        def handle_lead_cannot_battle() -> tuple["TurnAction", any]:
            action = context.config.battle.lead_cannot_battle_action
            if action == "flee":
                return self._escape(battle_state)
            elif action == "rotate" and util.can_switch():
                if len(util.get_potential_rotation_targets(battle_state)) > 0:
                    return TurnAction.rotate_lead(util.select_rotation_target(battle_state))
            return self._escape(battle_state)

        if not any(util.move_is_usable(move) for move in current_battler.moves) or not super()._pokemon_has_enough_hp(
            current_battler
        ):
            return handle_lead_cannot_battle()

        strongest_move = util.get_strongest_move_against(
            battle_state.own_side.active_battler, battle_state.opponent.active_battler
        )
        if strongest_move is None:
            return handle_lead_cannot_battle()
        return TurnAction.use_move(strongest_move)

    def choose_new_lead_after_faint(self, battle_state: BattleState) -> int:
        new_lead: int | None = None
        new_lead_current_hp: int = 0
        new_lead_level: int = 0
        # ‼‼ THIS IS THE CHOOSER THE STORY BOT ACTUALLY USES, and the KI-64 guard was originally
        # put only on `DefaultBattleStrategy` — where it was DEAD CODE for the story path. The MRO
        # is `StoryItemBattleStrategy` -> `LevelUpTravelBattleStrategy` -> `LevelUpLeadBattleStrategy`
        # (this class) -> `DefaultBattleStrategy`, and the story override's own `super()` fallback
        # lands HERE, not on the base. So a fix applied one level too low never ran. Found by an
        # adversarial review, not by the repro — which had asserted the base class directly and so
        # could not see which class the framework would actually call.
        ally = ally_party_indices(battle_state)

        for index, pokemon in enumerate(get_party()):
            if index in ally:
                continue
            # In a DOUBLE battle, skip the Pokémon already ON THE FIELD (our other active
            # battler): it can't be picked as the replacement, and returning its index
            # strands the bot on the "choose a Pokémon" menu. The base DefaultBattleStrategy
            # already excludes the active battlers; this override previously dropped that
            # check, so a faint in a double battle could hang selecting the partner.
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
            if pokemon.current_hp > 0 and not pokemon.is_egg and self.pokemon_can_battle(pokemon):
                # ‼ BREAK TIES BY LEVEL (2026-07-25, user's double-battle report, KI-18).
                # The score is raw `current_hp` and the comparison was a strict `>`, so on an
                # EQUAL-HP tie the earlier party index always won and a later one could never
                # be chosen. The user's exact observation: Beautifly L23 (67/67, index 3) never
                # came in while Mightyena L21 (67/67, index 2) kept winning the tie — same HP
                # number, lower level, earlier slot. Raw HP also ignores level completely, so a
                # tie between mons of different strength was decided purely by slot order.
                # Keeping `current_hp` as the PRIMARY metric (it is proven behaviour across
                # every mode that inherits this strategy) and adding level as the tiebreaker is
                # the minimal correct change: strictly better on ties, identical otherwise.
                _score = (pokemon.current_hp, pokemon.level)
                if _score > (new_lead_current_hp, new_lead_level):
                    new_lead = index
                    new_lead_current_hp = pokemon.current_hp
                    new_lead_level = pokemon.level
        if new_lead is not None:
            return new_lead
        else:
            return super().choose_new_lead_after_faint(battle_state)

    def party_can_battle(self) -> bool:
        party = get_party()

        for pokemon in party.non_fainted_pokemon:
            if super()._pokemon_has_enough_hp(pokemon) and pokemon.status_condition is StatusCondition.Healthy:
                for move in pokemon.moves:
                    if (
                        move is not None
                        and move.move.base_power > 0
                        and move.pp > 0
                        and move.move.name not in context.config.battle.banned_moves
                    ):
                        return True
        return False

    def pokemon_can_battle(self, pokemon: Pokemon) -> bool:
        return self._can_battle(pokemon)

    def party_can_battle(self) -> bool:
        return any(self._can_battle(pokemon) for pokemon in get_party().non_fainted_pokemon)

    def _can_battle(self, pokemon: Pokemon) -> bool:
        return (
            pokemon is not None
            and super()._pokemon_has_enough_hp(pokemon)
            and pokemon.status_condition is StatusCondition.Healthy
            and any(
                move is not None
                and move.move.base_power > 0
                and move.pp > 0
                and move.move.name not in context.config.battle.banned_moves
                for move in pokemon.moves
            )
        )

    def _escape(self, battle_state: BattleState):
        util = BattleStrategyUtil(battle_state)
        best_escape_method = util.get_best_escape_method()

        if best_escape_method is not None:
            return best_escape_method
        # ⛔ `#26-fleefreeze` (2026-08-26): this used to `return TurnAction.run_away()` — a blind
        # fallback ON THE VERY BRANCH WHERE `get_best_escape_method()` HAS JUST DETERMINED, trap-
        # aware and correctly, that escape is IMPOSSIBLE (Wrapped/Rooted/EscapePrevention, trapping
        # abilities). The game then refuses the run at selection time
        # (`BattleScript_PrintCantEscapeFromBattle` + a button-wait), the handler's text-printer
        # branch yields forever, KI-47 nets it at 3,001 frames, and the derail cascade burns to
        # Manual. MEASURED killing 3 of 8 lanes in batch 20260826-063456 (wild Torkoal Fire Spin —
        # learned at L17, so every Magma Hideout Torkoal has it — trapping a sub-20%-HP lead:
        # `[TURN 3] Loudred L36 14/116 [Wrapped] -> RunAway` → frozen). The craft rule is
        # "un-fleeable battles must fight through": delegate to the inherited, trap-aware,
        # fault-tested KI-52 `_handle_flee` — rotate to a healthy mon, else `_fight_on`. The
        # escape-POSSIBLE path above is byte-unchanged.
        return self._handle_flee(battle_state, util, "being trapped (escape is impossible)")
