"""How a party Pokemon is stored in Emerald's memory, decoded by the AI's own code. Framework-free.

WHY THE AI DECODES THE PARTY ITSELF (build step 1): the framework's `get_party()` LOOKS AHEAD one frame
(`peek_frame`) when it meets a half-written party and keeps a telemetry tally; a person cannot look
into the next frame. So the eyes (`ai_player/host/eyes.py`) read the raw 100 bytes of each slot and
decode them here; a torn read is reported, and the AI looks again on its next look. The species and
move NAMES are looked up afterwards by the host side (game facts from the framework's data tables).

The layout is `include/pokemon.h` (struct BoxPokemon, struct Pokemon) and the decryption
`src/pokemon.c` (DecryptBoxMon, GetSubstruct, CalculateBoxMonChecksum). `gates/test_eyes.py` checks
the decoder against the FRAMEWORK's independent decoder for all 24 substructure orders.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["PARTY_MON_SIZE", "RawMon", "SUBSTRUCT_POSITIONS", "decode_party_mon", "present_pids", "substruct_positions"]

#: sizeof(struct Pokemon).
PARTY_MON_SIZE = 100
#: `include/pokemon.h` struct BoxPokemon: the unencrypted bit-field byte @19, `hasSpecies` bit 1 (set by
#: `SetBoxMonData(MON_DATA_SPECIES)`, cleared with the whole slot by `ZeroBoxMonData`).
_FLAGS_AT, _HAS_SPECIES = 19, 0x02


def present_pids(raw: bytes, slots: int = 6) -> frozenset[int]:
    """The PIDs of the occupied slots of a raw party (`gPlayerParty` / `gEnemyParty`, 100 bytes a slot),
    from the unencrypted header only: a slot counts when its `hasSpecies` bit is set. No decryption, so a
    slot the game is writing (a torn read) still gives its PID. Used to tell a battler that belongs to THIS
    battle from a stale one (`host/eyes.py` _battle, step 1.1)."""
    return frozenset(
        int.from_bytes(raw[slot * PARTY_MON_SIZE:slot * PARTY_MON_SIZE + 4], "little")
        for slot in range(slots)
        if len(raw) >= (slot + 1) * PARTY_MON_SIZE and raw[slot * PARTY_MON_SIZE + _FLAGS_AT] & _HAS_SPECIES
    )
#: `src/pokemon.c` GetSubstruct, the SUBSTRUCT_CASE table verbatim: for personality % 24, the POSITION
#: (0-3) of the growth, attacks, EVs and misc substructures among the four 12-byte encrypted blocks.
SUBSTRUCT_POSITIONS: tuple[tuple[int, int, int, int], ...] = (
    (0, 1, 2, 3), (0, 1, 3, 2), (0, 2, 1, 3), (0, 3, 1, 2), (0, 2, 3, 1), (0, 3, 2, 1),
    (1, 0, 2, 3), (1, 0, 3, 2), (2, 0, 1, 3), (3, 0, 1, 2), (2, 0, 3, 1), (3, 0, 2, 1),
    (1, 2, 0, 3), (1, 3, 0, 2), (2, 1, 0, 3), (3, 1, 0, 2), (2, 3, 0, 1), (3, 2, 0, 1),
    (1, 2, 3, 0), (1, 3, 2, 0), (2, 1, 3, 0), (3, 1, 2, 0), (2, 3, 1, 0), (3, 2, 1, 0),
)


def substruct_positions(personality: int) -> tuple[int, int, int, int]:
    """(growth, attacks, EVs, misc) block positions for this personality value."""
    return SUBSTRUCT_POSITIONS[personality % 24]


@dataclass(frozen=True)
class RawMon:
    """One decoded party slot, numbers only (names come from the game's data tables)."""

    personality: int
    ot_id: int
    species_id: int
    moves: tuple[int, ...]  # move ids, 0 = empty
    pp: tuple[int, ...]
    pp_bonuses: int  # 2 bits per move slot
    is_egg: bool
    status_bits: int
    level: int
    hp: int
    max_hp: int
    experience: int = 0  # total experience points (the growth substructure @4; step 3: progress counts experience gained)


def _u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "little")


def _u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 4], "little")


def decode_party_mon(data: bytes) -> RawMon | str:
    """Decode 100 bytes of `gPlayerParty`. Returns a reason (a str) instead of a RawMon when the slot
    cannot be trusted: wrong size, or the checksum does not match (the game was writing it)."""
    if len(data) != PARTY_MON_SIZE:
        return f"{len(data)} bytes, not {PARTY_MON_SIZE}"
    personality, ot_id = _u32(data, 0), _u32(data, 4)
    key = personality ^ ot_id
    secure = b"".join((_u32(data, 32 + 4 * i) ^ key).to_bytes(4, "little") for i in range(12))
    checksum = sum(_u16(secure, 2 * i) for i in range(24)) & 0xFFFF
    if checksum != _u16(data, 28):
        return "the checksum does not match (a half-written slot: look again next frame)"
    growth, attacks, _, misc = (12 * position for position in substruct_positions(personality))
    return RawMon(
        personality=personality,
        ot_id=ot_id,
        species_id=_u16(secure, growth),
        moves=tuple(_u16(secure, attacks + 2 * index) for index in range(4)),
        pp=tuple(secure[attacks + 8 + index] for index in range(4)),
        pp_bonuses=secure[growth + 8],
        is_egg=bool(data[19] & 0x04) or bool((_u32(secure, misc + 4) >> 30) & 1),
        status_bits=_u32(data, 80) & 0xFF,
        level=data[84],
        hp=_u16(data, 86),
        max_hp=_u16(data, 88),
        experience=_u32(secure, growth + 4),
    )
