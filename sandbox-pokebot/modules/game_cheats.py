"""
Game cheat manager (SANDBOX feature).

GAME cheats — modify the RUNNING game via memory writes — as opposed to
upstream's `cheats.yml`, which toggles bot BEHAVIOUR. Everything here is built
on the bot's own verified write toolkit (`modules/debug_utilities.py`,
`modules/memory.py`), the same code the stock Debug menu uses.

Design + safety model: see `CHEATS-DESIGN.md`. In short: one-shot ACTIONS
require the overworld and rebuild data through the valid-Pokémon generator;
persistent TOGGLES are re-applied by a listener; every operation is fully
exception-guarded so a cheat can never crash the frame loop or half-write.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from modules.context import context
from modules.runtime import get_base_path

CONFIG_FILENAME = "game_cheats.yml"

DEFAULT_TOGGLES: dict = {
    "infinite_money": False,
    "auto_heal_party": False,
    "force_wild_species": False,
    "force_wild_species_name": "Bulbasaur",
    "force_wild_species_level": 5,
    "guaranteed_shiny_wild": False,
    # Adjustable money (#31): lock money to a user-typed value each tick.
    "lock_money": False,
    "locked_money_value": 0,
}

MONEY_TARGET = 900_000
MONEY_MAX = 999_999  # Gen-3 money cap

_log = logging.getLogger("game_cheats")
_log.setLevel(logging.INFO)


def _ensure_log_handler() -> None:
    if _log.handlers:
        return
    try:
        log_dir = get_base_path() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(log_dir / "game_cheats.log", maxBytes=512_000, backupCount=2, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s"))
        _log.addHandler(handler)
    except Exception:
        pass  # logging must never block a cheat


def _coerce(value, default):
    """Coerce a loaded YAML value to the default's type, falling back on the
    default when it cannot be coerced (malformed config must never crash)."""
    if isinstance(default, bool):
        return bool(value) if isinstance(value, bool) else default
    if isinstance(default, int):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    if isinstance(default, str):
        return str(value) if isinstance(value, (str, int, float)) else default
    return value if value is not None else default


class CheatManager:
    def __init__(self) -> None:
        _ensure_log_handler()
        self._toggles: dict = dict(DEFAULT_TOGGLES)
        self._config_loaded_for: str | None = None

    # ------------------------------------------------------------------ config
    def load_config(self) -> None:
        """Global game_cheats.yml, then per-profile override (whole-file),
        coerced key-by-key against DEFAULT_TOGGLES. Robust to a missing or
        malformed file."""
        merged = dict(DEFAULT_TOGGLES)
        for path in self._config_paths():
            data = self._read_yaml(path)
            toggles = data.get("toggles") if isinstance(data, dict) else None
            if isinstance(toggles, dict):
                for key, default in DEFAULT_TOGGLES.items():
                    if key in toggles:
                        merged[key] = _coerce(toggles[key], default)
        self._toggles = merged
        try:
            self._config_loaded_for = context.profile.path.name if context.profile is not None else None
        except Exception:
            self._config_loaded_for = None

    def _config_paths(self) -> list[Path]:
        paths = [get_base_path() / CONFIG_FILENAME]
        try:
            if context.profile is not None:
                paths.append(context.profile.path / CONFIG_FILENAME)
        except Exception:
            pass
        return paths

    @staticmethod
    def _read_yaml(path: Path) -> dict:
        try:
            import yaml

            if not path.is_file():
                return {}
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as error:
            _log.warning("Could not read %s: %s", path, error)
            return {}

    def get(self, key: str):
        return self._toggles.get(key, DEFAULT_TOGGLES.get(key))

    def set_toggle(self, key: str, value) -> None:
        """Update a toggle and persist it to the PER-PROFILE config (never the
        shared global template)."""
        if key not in DEFAULT_TOGGLES:
            return
        self._toggles[key] = _coerce(value, DEFAULT_TOGGLES[key])
        self._persist()

    def _persist(self) -> None:
        try:
            import yaml

            if context.profile is None:
                return
            path = context.profile.path / CONFIG_FILENAME
            path.write_text(yaml.safe_dump({"toggles": self._toggles}, sort_keys=False), encoding="utf-8")
        except Exception as error:
            _log.warning("Could not persist cheat toggles: %s", error)

    def any_toggle_active(self) -> bool:
        return bool(
            self.get("infinite_money")
            or self.get("auto_heal_party")
            or self.get("force_wild_species")
            or self.get("guaranteed_shiny_wild")
            or self.get("lock_money")
        )

    # ------------------------------------------------------------------ money
    def _money_offset(self) -> int:
        return 0x490 if context.rom.is_rse else 0x290

    def get_current_money(self):
        """The character's current money, or None if it can't be read (e.g. no
        save loaded / not in the overworld). Used to pre-fill the money field."""
        try:
            if not self._in_overworld():
                return None
            from modules.memory import decrypt32, get_save_block, unpack_uint32

            return decrypt32(unpack_uint32(get_save_block(1, self._money_offset(), 4)))
        except Exception:
            return None

    def set_money(self, value) -> str:
        """One-shot: write a specific money value (overworld-gated)."""
        try:
            amount = max(0, min(MONEY_MAX, int(value)))
        except (TypeError, ValueError):
            return "Enter a whole number for money."

        def _write() -> str:
            from modules.memory import decrypt32, pack_uint32, write_to_save_block

            write_to_save_block(pack_uint32(decrypt32(amount)), 1, self._money_offset())
            return ""

        return self._action(_write, f"Money set to {amount:,}.")

    # ------------------------------------------------------------- safe state
    @staticmethod
    def _in_overworld() -> bool:
        from modules.memory import GameState, get_game_state

        return get_game_state() is GameState.OVERWORLD

    # --------------------------------------------------------- party rebuild
    def _rebuild_party(self, override) -> str:
        """Rebuild each (non-egg) party member through debug_create_pokemon,
        applying `override(mon) -> dict` of kwargs. Returns "" on success or a
        user-facing error string."""
        from modules.debug_utilities import debug_create_pokemon, debug_write_party
        from modules.pokemon_party import get_party

        party = [mon for mon in get_party() if not mon.is_empty]
        if not party:
            return "Party is empty — nothing to change."

        new_party = []
        for mon in party:
            if mon.is_egg:
                new_party.append(mon)
                continue
            kwargs = dict(
                species=mon.species,
                level=mon.level,
                original_pokemon=mon,
                nickname=mon.nickname,
                is_shiny=mon.is_shiny,
                gender=mon.gender,
                nature=mon.nature,
                held_item=mon.held_item,
                friendship=mon.friendship,
                moves=[move for move in mon.moves if move is not None],
                ivs=mon.ivs,
                evs=mon.evs,
                current_hp=mon.current_hp,
                status_condition=mon.status_condition,
                has_second_ability=mon.ability is not mon.species.abilities[0],
                experience=mon.total_exp,
            )
            kwargs.update(override(mon))
            new_party.append(debug_create_pokemon(**kwargs))
        debug_write_party(new_party)
        return ""

    # --------------------------------------------------------- party actions
    def heal_party(self) -> str:
        return self._action(
            lambda: self._rebuild_party(
                lambda mon: {"current_hp": mon.total_hp, "status_condition": _healthy()}
            ),
            "Party healed (full HP, status cleared).",
        )

    def max_level(self) -> str:
        return self._action(
            lambda: self._rebuild_party(lambda mon: {"level": 100}),
            "Party set to level 100.",
        )

    def perfect_ivs(self) -> str:
        return self._action(
            lambda: self._rebuild_party(lambda mon: {"ivs": _perfect_ivs()}),
            "Party given perfect IVs (31 across the board).",
        )

    def max_friendship(self) -> str:
        return self._action(
            lambda: self._rebuild_party(lambda mon: {"friendship": 255}),
            "Party friendship maxed (255).",
        )

    # ---------------------------------------------------------- item/money actions
    def max_money(self) -> str:
        from modules.debug_utilities import debug_give_max_coins_and_money

        return self._action(lambda: (debug_give_max_coins_and_money(), "")[1], "Money & coins maxed.")

    def give_item_pack(self) -> str:
        from modules.debug_utilities import debug_give_test_item_pack

        return self._action(lambda: (debug_give_test_item_pack(), "")[1], "Gave the full item pack.")

    def give_item(self, item_name: str, quantity: int) -> str:
        return self._action(lambda: self._give_item(item_name, quantity), f"Gave {quantity}× {item_name}.")

    def max_poke_balls(self) -> str:
        return self._action(self._max_poke_balls, "Poké Ball pocket filled.")

    def _give_item(self, item_name: str, quantity: int) -> str:
        from modules.debug_utilities import debug_write_item_bag
        from modules.items import ItemPocket, get_item_bag, get_item_by_name, ItemSlot

        item = get_item_by_name(item_name)
        if item is None:
            return f"Unknown item: {item_name}"
        bag = get_item_bag()
        pockets = {
            "items": list(bag.items),
            "key_items": list(bag.key_items),
            "poke_balls": list(bag.poke_balls),
            "tms_hms": list(bag.tms_hms),
            "berries": list(bag.berries),
        }
        target = {
            ItemPocket.Items: "items",
            ItemPocket.KeyItems: "key_items",
            ItemPocket.PokeBalls: "poke_balls",
            ItemPocket.TmsAndHms: "tms_hms",
            ItemPocket.Berries: "berries",
        }[item.pocket]
        pocket = pockets[target]
        for index, slot in enumerate(pocket):
            if slot.item.index == item.index:
                pocket[index] = ItemSlot(item, quantity)
                break
        else:
            pocket.append(ItemSlot(item, quantity))
        debug_write_item_bag(
            items=pockets["items"],
            key_items=pockets["key_items"],
            poke_balls=pockets["poke_balls"],
            tms_hms=pockets["tms_hms"],
            berries=pockets["berries"],
        )
        return ""

    def _max_poke_balls(self) -> str:
        from modules.debug_utilities import debug_write_item_bag
        from modules.items import ItemPocket, _items_by_index, get_item_bag, ItemSlot

        bag = get_item_bag()
        stack = 999 if context.rom.is_frlg else 99
        balls = [
            ItemSlot(item, stack)
            for item in _items_by_index
            if item.pocket is ItemPocket.PokeBalls and item.index != 0 and not item.name.startswith("?")
        ]
        debug_write_item_bag(
            items=list(bag.items),
            key_items=list(bag.key_items),
            poke_balls=balls[: ItemPocket.PokeBalls.capacity],
            tms_hms=list(bag.tms_hms),
            berries=list(bag.berries),
        )
        return ""

    def _action(self, func, success_message: str) -> str:
        """Run a one-shot cheat: require the overworld, run `func` (returns ""
        on success or an error string), and turn the result into a single
        user-facing line. Never raises."""
        try:
            if not self._in_overworld():
                return "Go to the overworld first (not safe to write here)."
            error = func()
            if error:
                return error
            return success_message
        except Exception as error:  # noqa: BLE001 - a cheat must never crash the caller
            _log.exception("Cheat action failed")
            return f"Cheat failed: {error}"

    # ------------------------------------------------------- persistent toggles
    def apply_persistent_toggles(self) -> None:
        """Called by the listener on a throttled cadence. Overworld-only, fully
        guarded."""
        try:
            if not (self.get("infinite_money") or self.get("auto_heal_party") or self.get("lock_money")):
                return
            if not self._in_overworld():
                return
            # Lock takes precedence over infinite (both write money): a locked
            # value is the user's explicit number, infinite just tops up to max.
            if self.get("lock_money"):
                self._lock_money_value()
            elif self.get("infinite_money"):
                self._keep_money()
            if self.get("auto_heal_party"):
                self._keep_party_healed()
        except Exception:
            _log.exception("Persistent cheat toggle failed")

    def _lock_money_value(self) -> None:
        from modules.memory import decrypt32, get_save_block, pack_uint32, unpack_uint32, write_to_save_block

        try:
            target = max(0, min(MONEY_MAX, int(self.get("locked_money_value"))))
        except (TypeError, ValueError):
            return
        offset = self._money_offset()
        current = decrypt32(unpack_uint32(get_save_block(1, offset, 4)))
        if current != target:
            write_to_save_block(pack_uint32(decrypt32(target)), 1, offset)

    def _keep_money(self) -> None:
        from modules.memory import decrypt32, get_save_block, pack_uint32, unpack_uint32, write_to_save_block

        money_offset = 0x490 if context.rom.is_rse else 0x290
        current = decrypt32(unpack_uint32(get_save_block(1, money_offset, 4)))
        if current < MONEY_TARGET:
            write_to_save_block(pack_uint32(decrypt32(MONEY_TARGET)), 1, money_offset)

    def _keep_party_healed(self) -> None:
        # HP / status live OUTSIDE the encrypted region (bytes 80-90 of each
        # 100-byte party slot), so this is a safe surgical write, no re-encrypt.
        from modules.memory import pack_uint16, read_symbol, unpack_uint16, write_symbol

        count = read_symbol("gPlayerPartyCount")[0]
        if count == 0:
            return
        party = read_symbol("gPlayerParty", 0, count * 100)
        for slot in range(count):
            base = slot * 100
            is_egg_flag = party[base + 19]  # 0x02 normal, 0x06 egg
            if is_egg_flag == 0x06:
                continue
            max_hp = unpack_uint16(party[base + 88 : base + 90])
            current_hp = unpack_uint16(party[base + 86 : base + 88])
            status = party[base + 80 : base + 84]
            if max_hp == 0:
                continue
            if current_hp < max_hp:
                write_symbol("gPlayerParty", pack_uint16(max_hp), base + 86)
            if status != b"\x00\x00\x00\x00":
                write_symbol("gPlayerParty", b"\x00\x00\x00\x00", base + 80)

    # --------------------------------------------------------- wild overrides
    def on_wild_battle_start(self) -> None:
        """Mirror of the stock ForceShinyEncounterListener: at battle start,
        if the opponent is a wild mon, apply the force-species / shiny cheats."""
        try:
            force_species = bool(self.get("force_wild_species"))
            force_shiny = bool(self.get("guaranteed_shiny_wild"))
            if not (force_species or force_shiny):
                return

            from modules.debug_utilities import debug_create_pokemon
            from modules.memory import write_symbol
            from modules.player import get_player
            from modules.pokemon import get_opponent, get_species_by_name

            opponent = get_opponent()
            if opponent is None:
                return
            player = get_player()
            ot = opponent.original_trainer
            # Wild mons carry the player's OT id/secret id; trainer mons do not.
            if not (ot.id == player.trainer_id and ot.secret_id == player.secret_id):
                return

            if force_species:
                species = get_species_by_name(str(self.get("force_wild_species_name")))
                level = max(1, min(100, int(self.get("force_wild_species_level"))))
                new_opponent = debug_create_pokemon(species=species, level=level, is_shiny=force_shiny)
            else:
                if opponent.is_shiny:
                    return
                new_opponent = debug_create_pokemon(
                    species=opponent.species,
                    level=opponent.level,
                    original_pokemon=opponent,
                    is_shiny=True,
                    gender=opponent.gender,
                    held_item=opponent.held_item,
                    has_second_ability=opponent.ability is not opponent.species.abilities[0],
                    nature=opponent.nature,
                    experience=opponent.total_exp,
                    friendship=opponent.friendship,
                    moves=[move for move in opponent.moves if move is not None],
                    ivs=opponent.ivs,
                    evs=opponent.evs,
                    current_hp=opponent.current_hp,
                    status_condition=opponent.status_condition,
                )
            write_symbol("gEnemyParty", new_opponent.data)
        except Exception:
            _log.exception("Wild-encounter cheat failed")


def _healthy():
    from modules.pokemon import StatusCondition

    return StatusCondition.Healthy


def _perfect_ivs():
    from modules.pokemon import StatsValues

    return StatsValues(31, 31, 31, 31, 31, 31)


# Module-level singleton (mirrors the macro recorder / backup manager pattern).
cheat_manager = CheatManager()
