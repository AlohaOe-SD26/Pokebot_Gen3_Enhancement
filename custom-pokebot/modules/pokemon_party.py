from typing import Generator

from modules.context import context
from modules.memory import read_symbol, get_event_var
from modules.pokemon import Pokemon, Move, Species, Ability
from modules.state_cache import state_cache


class PartyPokemon(Pokemon):
    def __init__(self, data: bytes, index: int):
        super().__init__(data)
        self.index = index


class Party:
    def __init__(self, pokemon: list[PartyPokemon]):
        self._pokemon = pokemon

    def __eq__(self, other):
        if isinstance(other, Party):
            return len(other._pokemon) == len(self._pokemon) and all(
                [other[n] == self[n] for n in range(len(self._pokemon))]
            )
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Party):
            return len(other._pokemon) != len(self._pokemon) or any(
                [other[n] != self[n] for n in range(len(self._pokemon))]
            )
        else:
            return NotImplemented

    def __contains__(self, item):
        if isinstance(item, Pokemon):
            return item in self._pokemon
        elif isinstance(item, Species):
            return any([pokemon.species is item for pokemon in self._pokemon])
        else:
            return NotImplemented

    def __iter__(self) -> Generator[PartyPokemon, None, None]:
        yield from self._pokemon

    def __len__(self) -> int:
        return len(self._pokemon)

    def __getitem__(self, item: int | slice):
        return self._pokemon[item]

    @property
    def contains_eggs(self) -> bool:
        return any([pokemon.is_egg for pokemon in self._pokemon])

    @property
    def eggs(self) -> list[PartyPokemon]:
        return [pokemon for pokemon in self._pokemon if pokemon.is_egg]

    @property
    def non_eggs(self) -> list[PartyPokemon]:
        return [pokemon for pokemon in self._pokemon if not pokemon.is_egg]

    @property
    def non_fainted_pokemon(self) -> list[PartyPokemon]:
        return list(filter(lambda pokemon: not pokemon.is_egg and pokemon.current_hp > 0, self._pokemon))

    @property
    def first_non_fainted(self) -> PartyPokemon | None:
        non_fainted_pokemon = self.non_fainted_pokemon
        if len(non_fainted_pokemon) > 0:
            return self.non_fainted_pokemon[0]
        else:
            return None

    def has_pokemon_with_move(self, move: Move | str, with_pp_remaining: bool = False) -> bool:
        return any(pokemon.knows_move(move, with_pp_remaining) and not pokemon.is_egg for pokemon in self._pokemon)

    def first_pokemon_with_move(self, move: Move | str, with_pp_remaining: bool = False) -> PartyPokemon | None:
        for pokemon in self._pokemon:
            if not pokemon.is_egg and pokemon.knows_move(move, with_pp_remaining):
                return pokemon
        return None

    def has_pokemon_with_ability(self, ability: Ability | str) -> bool:
        ability_name = ability.name if isinstance(ability, Ability) else str(ability)
        return any(pokemon.ability.name == ability_name and not pokemon.is_egg for pokemon in self._pokemon)

    def first_pokemon_with_ability(self, ability: Ability | str) -> PartyPokemon | None:
        ability_name = ability.name if isinstance(ability, Ability) else str(ability)
        for pokemon in self._pokemon:
            if not pokemon.is_egg and pokemon.ability.name == ability_name:
                return pokemon
        return None

    def get_index_for_pokemon(self, pokemon: Pokemon) -> int:
        """Party slot of `pokemon`, matched on its PERSONALITY VALUE.

        ‼‼ KI-78 — **A PERSONALITY VALUE IS NOT A UNIQUE IDENTITY IN GEN 3.** `CreateShedinja`
        (`src/evolution_scene.c:548-583`) builds Shedinja with `CopyMon`, a plain memcpy
        (`src/pokemon.c:4419-4422`), and **does not overwrite the personality or the OT ID** — so a
        Shedinja and the Ninjask it came from carry the SAME PID for life. This function returns
        the FIRST match, and `CreateShedinja` places the twin AFTER its sibling, so with that pair
        in the party a request aimed at the Shedinja resolves to the **Ninjask**.
        ⛔ That matters because of who calls this: `pc_interaction.py:464` (DEPOSIT) and
        **`:505` (RELEASE — permanent, no undo)**. "Box the Shedinja" boxes the Ninjask; "release
        the Shedinja" **destroys the Ninjask**.

        ‼ STAGE 0 OF THE FIX (2026-08-14): **DETECT ONLY — behaviour is deliberately UNCHANGED.**
        The ruled fix is to match on `(personality, species)`, which `pokemon_storage.py:128`
        already does for the box side; but this lookup feeds a destructive path, so the first step
        is to find out how often the ambiguity actually occurs in real runs rather than to change
        an irreversible operation on a theory. This logs LOUD and still returns `matches[0]`,
        exactly as before. **Do not "finish" this by silently switching the key** — the follow-up
        must land with its own fault-injected A/B (a fabricated twin pair: the OLD key picks the
        wrong slot, the NEW key picks the right one) and with the R6 rule from KI-78: on a species
        mismatch with a unique PID hit, re-resolve from the live party rather than falling back to
        the first hit.
        """
        matches = [index for index, party_pokemon in enumerate(self._pokemon)
                   if pokemon.data[:4] == party_pokemon.data[:4]]
        if not matches:
            raise RuntimeError("This Pokémon is not in the player's party.")
        if len(matches) > 1:
            # ‼ A silent "no" is indistinguishable from "the feature is not running" — this
            # project has lost time to that shape repeatedly, so an ambiguity announces itself.
            try:
                from modules.console import console

                detail = ", ".join(
                    f"slot {i}={self._pokemon[i].species.name}" for i in matches
                )
                console.print(
                    f"[bold red]‼ KI-78: {len(matches)} party Pokémon share personality value "
                    f"{pokemon.data[:4].hex()} ({detail}). Returning slot {matches[0]} as before — "
                    f"but any DEPOSIT or RELEASE resolved through this call may act on the wrong "
                    f"Pokémon. Requested species: {pokemon.species.name}.[/]"
                )
            except Exception:  # noqa: BLE001 - telemetry must never break the caller
                pass
        return matches[0]

    def to_list(self) -> list[dict]:
        return [pokemon.to_dict() for pokemon in self._pokemon]


def get_party_size() -> int:
    return len(get_party())


def get_party() -> Party:
    """
    :return: The player's party of Pokémon.
    """

    if state_cache.party.age_in_frames == 0:
        return state_cache.party.value

    def read_party_pokemon(party_index: int) -> PartyPokemon | None:
        party_pokemon = PartyPokemon(read_symbol("gPlayerParty", offset=party_index * 100, size=100), party_index)
        return party_pokemon if not party_pokemon.is_empty and party_pokemon.is_valid else None

    list_of_pokemon = []
    number_of_pokemon_in_party = read_symbol("gPlayerPartyCount", size=1)[0]
    for index in range(number_of_pokemon_in_party):
        pokemon = read_party_pokemon(index)

        # It's possible for party data to be written while we are trying to read it, in which case
        # the checksum would be wrong and `parse_pokemon()` returns `None`.
        #
        # In order to still get a valid result, we will 'peek' into next frame's memory by
        # (1) advancing the emulation by one frame, (2) reading the memory, (3) restoring the previous
        # frame's state, so we don't mess with frame accuracy.
        if pokemon is None:
            retries = 5
            with context.emulator.peek_frame():
                while retries > 0 and pokemon is None:
                    retries -= 1
                    pokemon = read_party_pokemon(index)
                    if pokemon is None:
                        context.emulator._core.run_frame()
        if pokemon is None:
            if read_symbol("gPlayerParty", offset=index * 100, size=100).count(b"\x00") >= 99:
                continue
            else:
                raise RuntimeError(f"Party Pokémon #{index + 1} was invalid for two frames in a row.")

        list_of_pokemon.append(pokemon)

    party = Party(list_of_pokemon)
    state_cache.party = party

    return party


def get_opponent_party() -> Party | None:
    """
    Gets the opponent's party (obviously only makes sense to check when in a battle.)
    :return: The full party of the opponent, or `None` if there is no valid opponent at the moment.
    """
    if state_cache.opponent.age_in_frames == 0:
        return state_cache.opponent.value

    list_of_pokemon = []
    data = read_symbol("gEnemyParty")
    for index in range(6):
        offset = index * 100
        pokemon = PartyPokemon(data[offset : offset + 100], index)
        if pokemon is None:
            if index == 0:
                return None
            else:
                continue
        list_of_pokemon.append(pokemon)

    party = Party(list_of_pokemon)
    state_cache.opponent = party

    return party


def get_current_repel_level() -> int:
    """
    :return: The minimum level that wild encounters can have, given the current Repel
             state and the level of the first non-fainted Pokémon.
    """
    first_non_fainted_party_member = get_party().first_non_fainted
    if first_non_fainted_party_member is None:
        return 0
    else:
        return get_party().first_non_fainted.level if get_event_var("REPEL_STEP_COUNT") > 0 else 0
