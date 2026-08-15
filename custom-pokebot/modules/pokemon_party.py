from typing import Generator

from modules.context import context
from modules.memory import read_symbol, get_event_var
from modules.pokemon import Pokemon, Move, Species, Ability, same_pokemon
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

        ✅ **STAGE 1 (2026-08-14): the match is now `(personality, species)` via the shared
        `same_pokemon` predicate** — the same key `pokemon_storage.get_slot_for_pokemon` has always
        used. Proven by `tools/story-dev/repro_pid_identity_key.py`: on a fabricated twin pair the
        OLD key returns the WRONG slot and the new one returns the right one, with controls.

        ‼ **R6 — THE NEW FAILURE MODE THE COMPOSITE KEY INTRODUCES, HANDLED DELIBERATELY.**
        A mon that EVOLVES between the moment the caller captured its object and the moment this
        runs now MISSES, where a PID-only match would have hit. For a destructive path a loud miss
        beats a silent wrong target — but a bare miss would also turn working flows into aborts.
        So: a unique PID hit whose species disagrees is **re-resolved from the live party** and
        reported, never silently accepted and never quietly dropped. ⛔ **What must NEVER happen
        is falling back to "the first PID match"** — that is precisely the old bug.
        """
        matches = [index for index, party_pokemon in enumerate(self._pokemon)
                   if same_pokemon(party_pokemon, pokemon)]

        if not matches:
            # ‼ R6: nothing matched on (PID, species). Before failing, ask whether exactly ONE mon
            # carries this PID — that is the evolved-since-capture case, and it is recoverable and
            # unambiguous. More than one PID hit with no species match is genuinely ambiguous and
            # must NOT be guessed at, because the caller may be about to release something.
            pid_only = [index for index, party_pokemon in enumerate(self._pokemon)
                        if party_pokemon.data[:4] == pokemon.data[:4]]
            if len(pid_only) == 1:
                position = pid_only[0]
                index = self._pokemon[position].index
                self._warn(
                    f"‼ KI-78/R6: no (PID, species) match for {pokemon.species.name}, but exactly "
                    f"ONE party Pokémon carries that personality value — slot {index} is now "
                    f"{self._pokemon[position].species.name}. It evolved since the caller captured "
                    f"it. Re-resolving to slot {index} from the LIVE party."
                )
                return index
            raise RuntimeError("This Pokémon is not in the player's party.")

        if len(matches) > 1:
            # Residual ambiguity the composite key cannot close (KI-78 R2: the debug utilities can
            # fabricate two identical-PID identical-species mons). A silent "no" is
            # indistinguishable from "the feature is not running", so it announces itself.
            self._warn(
                f"‼ KI-78: {len(matches)} party Pokémon share BOTH personality value "
                f"{pokemon.data[:4].hex()} AND species {pokemon.species.name} (slots "
                f"{[self._pokemon[m].index for m in matches]}). The composite key cannot separate "
                f"them; returning slot {self._pokemon[matches[0]].index}. Any DEPOSIT or RELEASE "
                f"resolved through this call may act on the wrong Pokémon."
            )
        # ‼‼ RETURN THE **PHYSICAL** SLOT, NOT THE LIST POSITION (fixed 2026-08-14, found by an
        # adversarial audit of party accounting — hours after KI-78 Stage 1 shipped WITHOUT it).
        # `self._pokemon` is COMPACTED: `get_party()` loops `range(gPlayerPartyCount)` and
        # `continue`s any slot whose 100 bytes are all zero (`:204-208`), so a HOLE makes the list
        # position and the real `gPlayerParty` slot diverge for every mon after it. `PartyPokemon`
        # has carried the true slot all along (`:182`) and this function ignored it.
        # ⛔ WHY IT MATTERS: the consumers are `pc_interaction.py` DEPOSIT (`:464`) and **RELEASE
        # (`:505`, permanent)**, which drive a cursor over the PHYSICAL party. A list position
        # handed to them selects the wrong Pokémon — the same harm KI-78 exists to stop, arriving
        # through a different door.
        # ⚠ HONEST REACHABILITY: holes are rare, and the game's own `CompactPartySlots` pushes them
        # to the TAIL (where positions still align), so this is defence rather than a reproduced
        # failure. It costs one attribute lookup and is identical when no hole exists.
        return self._pokemon[matches[0]].index

    @staticmethod
    def _warn(message: str) -> None:
        """Announce an identity ambiguity. Telemetry must never break the caller."""
        try:
            from modules.console import console

            console.print(f"[bold red]{message}[/]")
        except Exception:  # noqa: BLE001
            pass

    def to_list(self) -> list[dict]:
        return [pokemon.to_dict() for pokemon in self._pokemon]


def get_party_size() -> int:
    """**B** — how many party Pokémon this bot can actually READ.

    ‼ This is NOT necessarily what the game says the party holds. `get_party()` COMPACTS, so a
    near-empty slot below `gPlayerPartyCount` is skipped and this number comes out LOWER. Use it
    for ITERATION and INDEXING (it is the length of the list you will index into); for CAPACITY
    questions — *is the party full? is there room for a catch, an egg, or a Shedinja?* — the
    game's own authority is `party_accounting.game_party_count()`.
    ⛔ Stage 0 has re-pointed NO call site; see `modules/party_accounting.py` for why not.
    """
    return len(get_party())


#: Set once, so a broken observer complains exactly one time instead of on every party read.
_accounting_fault_reported = False


def _report_accounting_fault(error: BaseException) -> None:
    """A broken observer must SAY it is broken — a silent one reports 'no divergence' forever."""
    global _accounting_fault_reported
    if _accounting_fault_reported:
        return
    _accounting_fault_reported = True
    try:
        from modules.console import console

        console.print(
            f"[bold red]‼ [PARTY-ACCT] the Stage 0 party-accounting observer FAILED "
            f"({type(error).__name__}: {error}). Party reads are UNAFFECTED, but treat any "
            f"'no divergence observed' summary from this run as UNMEASURED, not as clean.[/]"
        )
    except Exception:  # noqa: BLE001 — reporting a telemetry fault must not itself become one.
        pass


def _account_recompute(game_count: int) -> None:
    """‼ STAGE 0 PARTY ACCOUNTING (`modules/party_accounting.py`) — OBSERVATION ONLY.

    Runs once per `get_party()` recompute, right after `gPlayerPartyCount` (**A**) is read. It
    records the count-byte sanity check — exact and free, the byte is already in hand — and, on a
    sampled subset of recomputes, a full six-slot scan, which is the only way to see occupied
    slots PAST the count. ⛔ Nothing below consumes its result. Stage 0 answers *"does A ever
    actually differ from B in a real run?"* before any decision is re-pointed at A.
    """
    try:
        from modules import party_accounting

        scan_due = party_accounting.note_recompute()
        if game_count > party_accounting.PARTY_SIZE:
            party_accounting.record_divergence(
                "OVERFLOW",
                f"gPlayerPartyCount={game_count} exceeds the {party_accounting.PARTY_SIZE} "
                f"physical slots, so this reader is about to read past the end of gPlayerParty "
                f"(pre-existing behaviour, deliberately unchanged by Stage 0)",
            )
        if scan_due:
            accounting = party_accounting.read_party_accounting()
            if accounting.stale:
                party_accounting.record_divergence(
                    "STALE",
                    f"slots {list(accounting.stale)} hold data past gPlayerPartyCount="
                    f"{game_count}; the game does NOT count them as party members, so a naive "
                    f"'count the filled slots' reader would over-count here",
                )
    except Exception as error:  # noqa: BLE001 — accounting is telemetry hanging off the party
        # reader, and every party read in the bot goes through here. A fault must not break the
        # read; it is swallowed, but reported LOUDLY once, because a silently broken observer
        # would keep answering "no divergence" and the negative would be believed.
        _report_accounting_fault(error)


def _account_slot_anomaly(kind: str, index: int, game_count: int, detail: str) -> None:
    """‼ STAGE 0 PARTY ACCOUNTING — OBSERVATION ONLY. Records one anomalous physical slot.

    Hung off `get_party()`'s OWN branches, so a HOLE is observed EXACTLY — every occurrence, at
    zero extra memory reads — rather than sampled. Changes no control flow: each branch behaves
    exactly as it did before this call was added.
    """
    try:
        from modules import party_accounting

        party_accounting.record_divergence(
            kind, f"slot {index} of gPlayerPartyCount={game_count}: {detail}"
        )
    except Exception as error:  # noqa: BLE001 — same contract as `_account_recompute`: telemetry
        # may not break a party read, and a broken observer must announce itself rather than
        # quietly degrading into a permanent clean bill of health.
        _report_accounting_fault(error)


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

    # ‼ STAGE 0 PARTY ACCOUNTING — OBSERVATION ONLY (`modules/party_accounting.py`). This call and
    # the two `_account_slot_anomaly` calls below are the ONLY additions; they read memory and log,
    # and no branch below consults them. `number_of_pokemon_in_party` is quantity **A**; the length
    # of `list_of_pokemon` at the end of this function is quantity **B**.
    _account_recompute(number_of_pokemon_in_party)

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
                # ‼ THIS `continue` IS THE ENTIRE REASON B CAN BE LESS THAN A. The slot is counted
                # by the game and skipped by us, so every Pokémon after it sits at a list position
                # that is NOT its physical `gPlayerParty` slot. Observed exactly, here, for free.
                _account_slot_anomaly(
                    "HOLE",
                    index,
                    number_of_pokemon_in_party,
                    "counted by the game but (near-)all zero, so it is skipped — B is now < A and "
                    "every later Pokémon's list position no longer equals its physical slot",
                )
                continue
            else:
                _account_slot_anomaly(
                    "INVALID",
                    index,
                    number_of_pokemon_in_party,
                    "neither decodable nor empty after two frames — get_party() is about to raise",
                )
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
