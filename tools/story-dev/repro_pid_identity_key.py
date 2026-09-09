"""REPRO + GATE — KI-78: a personality value is NOT a unique identity, and a RELEASE was keyed on it.

‼‼ THE HAZARD, DECOMP-VERIFIED. `CreateShedinja` (`src/evolution_scene.c:548-583`) builds Shedinja
with `CopyMon`, a plain memcpy (`src/pokemon.c:4419-4422`), and **does not overwrite the personality
or the OT ID**. So a Shedinja and the Ninjask it came from share a PID for life — and Gen 3 places
the twin at `gPlayerParty[gPlayerPartyCount]`, i.e. immediately AFTER its sibling.

`Party.get_index_for_pokemon` scanned for the FIRST `data[:4]` match, and it is what
`pc_interaction.py` uses to decide which party slot an action operates on — for DEPOSIT (`:464`)
and for **RELEASE (`:505`, permanent, no undo)**. With that pair in the party:
    "box the Shedinja"      -> boxed the NINJASK
    "release the Shedinja"  -> DESTROYED the NINJASK
deterministically in that direction, because the twin is always the later slot.

‼ THE TRIGGER IS COMMON. In Gen 3 the ONLY precondition is a free party slot
(`evolution_scene.c:551`) — there is **no spare-Poké-Ball rule**; that is Gen 4+, and our own
`modules/obtainability.py:88` display string is wrong about it.

WHAT THIS PROVES, AND HOW. A fault-injected A/B on a FABRICATED TWIN PAIR, no emulator, no ROM:
  * ARM A (the OLD PID-only rule, inlined here): asked for the SHEDINJA it must return the
    NINJASK's slot. If it does not, this repro is not reproducing the bug and its PASS is
    meaningless.
  * ARM B (the SHIPPED code): must return the Shedinja's own slot.
  * CONTROL A — DISCRIMINATION: a pair with DIFFERENT PIDs must resolve correctly under BOTH arms,
    so the harness cannot be passing by accident.
  * CONTROL B — HONESTY: a fabricated same-PID SAME-SPECIES pair (KI-78's residual R2, reachable
    via the debug utilities) must STILL be ambiguous, and must SAY SO. We do not claim a uniqueness
    we do not have.
  * R6 — the new failure mode the composite key introduces: a mon that EVOLVED since the caller
    captured its object no longer matches on species. It must be re-resolved from the live party
    and reported — never silently dropped, and ⛔ never fallen back to "the first PID match".

‼ THE FIXTURE IS BUILT WITH REAL GEN 3 ENCRYPTION, not duck-typed stand-ins. `Pokemon.species`
reads a substructure that is XOR-encrypted with `personality ^ OT id` and re-ordered by
`personality % 24`, so a fake object with a `.species` attribute would test this file's idea of the
interface rather than the real decode path. These are genuine `Pokemon` objects over genuine bytes.

Exit 0 = all checks pass. Exit 1 = a check failed (details printed).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_pid_identity_key.py [--build sandbox|custom]
"""

import argparse
import pathlib
import struct
import sys
# ⛔ A default Windows console is cp1252. This file PRINTS non-ASCII, and without this the
# crash lands AFTER the work is done — so it looks like a real failure. Swept 2026-09-08
# after `run_gates.py` itself shipped with this bug while fixing it in three other files.
sys.stdout.reconfigure(encoding="utf-8")


_ap = argparse.ArgumentParser(add_help=True)
_ap.add_argument("--build", default="sandbox", choices=["sandbox", "custom"],
                 help="which fork to test (default sandbox; use custom to verify a promotion)")
_ARGS, _ = _ap.parse_known_args()

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / f"{_ARGS.build}-pokebot"))

BAR = "=" * 96

#: Species indices, from our own `modules/data/species.json` (list position IS the internal index).
NINCADA, NINJASK, SHEDINJA = 301, 302, 303

#: Chosen so both twins share it, exactly as the game leaves them.
TWIN_PID = 0x1F2E3D4C
TWIN_OTID = 0x00BEEF01
OTHER_PID = 0x0A0B0C0D


def build_mon(pid: int, otid: int, species: int) -> bytes:
    """A genuine 100-byte party record: real substructure order, real XOR encryption.

    Mirrors `Pokemon._decrypted_data` (`modules/pokemon.py`) in reverse — logical substructure `i`
    lives at raw offset `32 + order[i] * 12`, and every 32-bit word is XORed with
    `personality ^ OT id`. Only GROWTH matters here (species is its first halfword); the rest are
    zeroes, which is legal and keeps the fixture minimal.
    """
    from modules.pokemon import POKEMON_DATA_SUBSTRUCTS_ORDER

    order = POKEMON_DATA_SUBSTRUCTS_ORDER[pid % 24]
    key = pid ^ otid

    growth = struct.pack("<H", species) + b"\x00" * 10   # species, then item/exp/pp/friendship
    logical = [growth, b"\x00" * 12, b"\x00" * 12, b"\x00" * 12]

    raw_substructs = [b"\x00" * 12] * 4
    for logical_index, chunk in enumerate(logical):
        encrypted = b"".join(
            struct.pack("<I", struct.unpack_from("<I", chunk, w * 4)[0] ^ key) for w in range(3)
        )
        raw_substructs[order[logical_index]] = encrypted

    header = struct.pack("<II", pid, otid) + b"\x00" * 24      # 32 bytes
    return header + b"".join(raw_substructs) + b"\x00" * 20    # 32 + 48 + 20 = 100


def old_rule_index(party_list, wanted) -> "int | None":
    """ARM A — the PID-only scan exactly as `get_index_for_pokemon` shipped before Stage 1.

    Inlined rather than reached by reverting the file, so the A/B is one run and cannot drift out
    of sync with a stash."""
    for index, mon in enumerate(party_list):
        if mon.data[:4] == wanted.data[:4]:
            return index
    return None


def main() -> int:
    failures = []

    def check(label, condition, detail=""):
        status = "PASS" if condition else "FAIL"
        print(f"  {status}  {label}{('  — ' + detail) if detail else ''}")
        if not condition:
            failures.append(label)

    print(BAR)
    print("REPRO — KI-78: PID is not a unique identity (Shedinja shares its Ninjask's)")
    print(f"BUILD UNDER TEST: {_ARGS.build}-pokebot")
    print(BAR)

    import modules.pokemon as pokemon_mod
    from modules.pokemon import Pokemon, same_pokemon
    from modules.pokemon_party import Party, PartyPokemon

    # ‼ Prove we imported the fork we CLAIM to test — an instrument that cannot see what it is
    # pointed at is this project's most-logged failure family.
    if f"{_ARGS.build}-pokebot" not in str(pathlib.Path(pokemon_mod.__file__).resolve()):
        print(f"  FAIL  imported modules.pokemon from {pokemon_mod.__file__}")
        return 1
    print(f"  (importing from {_ARGS.build}-pokebot — verified)")

    ninjask = Pokemon(build_mon(TWIN_PID, TWIN_OTID, NINJASK))
    shedinja = Pokemon(build_mon(TWIN_PID, TWIN_OTID, SHEDINJA))
    unrelated = Pokemon(build_mon(OTHER_PID, TWIN_OTID, NINJASK))

    print("\n0 — THE FIXTURE IS REAL: species must decode out of genuine encrypted bytes")
    check("Ninjask fixture decodes to species 302",
          ninjask.species.index == NINJASK, f"got {ninjask.species.index}")
    check("Shedinja fixture decodes to species 303",
          shedinja.species.index == SHEDINJA, f"got {shedinja.species.index}")
    check("‼ the twins genuinely SHARE a personality value (the whole hazard)",
          ninjask.data[:4] == shedinja.data[:4],
          f"{ninjask.data[:4].hex()} vs {shedinja.data[:4].hex()}")
    check("...and their OT ids match too, as CopyMon leaves them",
          ninjask.data[4:8] == shedinja.data[4:8])

    # Gen 3 places the spawned twin AFTER its sibling — reproduce that ordering exactly.
    party = Party([PartyPokemon(ninjask.data, 0), PartyPokemon(shedinja.data, 1)])

    print("\n1 — ARM A: the OLD PID-only rule must return the WRONG slot (positive control)")
    print("    If this passes, the repro is not reproducing the bug.")
    arm_a = old_rule_index([ninjask, shedinja], shedinja)
    check("asked for the SHEDINJA, the old rule returns the NINJASK's slot 0",
          arm_a == 0, f"got {arm_a!r}")

    print("\n2 — ARM B: the SHIPPED code must return the Shedinja's own slot")
    arm_b = party.get_index_for_pokemon(shedinja)
    check("get_index_for_pokemon(shedinja) == 1", arm_b == 1, f"got {arm_b!r}")
    check("get_index_for_pokemon(ninjask) == 0",
          party.get_index_for_pokemon(ninjask) == 0)

    print("\n3 — CONTROL A (discrimination): a DIFFERENT-PID pair resolves under BOTH arms")
    plain = Party([PartyPokemon(ninjask.data, 0), PartyPokemon(unrelated.data, 1)])
    check("old rule finds the unrelated mon at slot 1",
          old_rule_index([ninjask, unrelated], unrelated) == 1)
    check("new rule finds the unrelated mon at slot 1",
          plain.get_index_for_pokemon(unrelated) == 1)

    print("\n4 — CONTROL B (honesty): same PID AND same species is STILL ambiguous, and says so")
    twin_clone = Pokemon(build_mon(TWIN_PID, TWIN_OTID, NINJASK))
    clones = Party([PartyPokemon(ninjask.data, 0), PartyPokemon(twin_clone.data, 1)])
    check("an identical pair still resolves to the first slot (we claim no uniqueness we lack)",
          clones.get_index_for_pokemon(twin_clone) == 0)

    print("\n5 — R6: a mon that EVOLVED since capture is RE-RESOLVED, not dropped")
    print("    ⛔ and it must never fall back to 'the first PID match'.")
    evolved_only = Party([PartyPokemon(ninjask.data, 0)])
    # The caller holds a pre-evolution Nincada object; the live party now holds the Ninjask.
    nincada = Pokemon(build_mon(TWIN_PID, TWIN_OTID, NINCADA))
    r6 = evolved_only.get_index_for_pokemon(nincada)
    check("a unique PID hit with a changed species re-resolves to that slot",
          r6 == 0, f"got {r6!r}")
    # ...but with the twin pair present, a species miss is genuinely ambiguous and must RAISE.
    try:
        party.get_index_for_pokemon(nincada)
        check("‼ an AMBIGUOUS species miss must RAISE, not guess", False,
              "it returned a slot instead of raising")
    except RuntimeError:
        check("‼ an AMBIGUOUS species miss RAISES rather than guessing", True)

    print("\n5b — ‼ the returned index must be the PHYSICAL slot, not the LIST POSITION")
    print("     `get_party()` COMPACTS: it loops range(gPlayerPartyCount) and skips an all-zero")
    print("     slot, so a HOLE makes list position != gPlayerParty slot for every mon after it —")
    print("     and the consumers (DEPOSIT, and RELEASE which is permanent) drive a cursor over")
    print("     the PHYSICAL party.")
    # Slot 0 is a hole: the party list holds only the mons from physical slots 1 and 2.
    holed = Party([PartyPokemon(ninjask.data, 1), PartyPokemon(shedinja.data, 2)])
    check("with a hole at slot 0, the Ninjask resolves to PHYSICAL slot 1 (not position 0)",
          holed.get_index_for_pokemon(ninjask) == 1,
          f"got {holed.get_index_for_pokemon(ninjask)!r}")
    check("...and the Shedinja to PHYSICAL slot 2 (not position 1)",
          holed.get_index_for_pokemon(shedinja) == 2,
          f"got {holed.get_index_for_pokemon(shedinja)!r}")
    # R6 must return a physical slot too, not a position.
    holed_one = Party([PartyPokemon(ninjask.data, 3)])
    check("R6's re-resolve also returns the PHYSICAL slot",
          holed_one.get_index_for_pokemon(nincada) == 3,
          f"got {holed_one.get_index_for_pokemon(nincada)!r}")

    print("\n6 — the shared predicate itself")
    check("same_pokemon(ninjask, shedinja) is False despite the shared PID",
          same_pokemon(ninjask, shedinja) is False)
    check("same_pokemon(ninjask, ninjask) is True", same_pokemon(ninjask, ninjask) is True)

    print("\n7 — PC STORAGE must use the same key (its two neighbours had drifted)")
    from modules.pokemon_storage import PokemonStorage

    check("contains_pokemon and get_slot_for_pokemon both go through same_pokemon",
          "same_pokemon" in PokemonStorage.contains_pokemon.__code__.co_names
          and "same_pokemon" in PokemonStorage.get_slot_for_pokemon.__code__.co_names)

    print("\n" + BAR)
    if failures:
        print(f"FAILED {len(failures)} check(s): " + "; ".join(failures))
        print(BAR)
        return 1
    print("ALL CHECKS PASS — identity is (personality, species); the twins are separable.")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
