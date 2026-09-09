"""REPRO + GATE — PARTY ACCOUNTING STAGE 0: A (`gPlayerPartyCount`) is not B (`len(get_party())`).

‼‼ THE FAMILY THIS MEASURES (user-designed; `06-DECISIONS-LOG.md` RULING D, 2026-08-14). Three
quantities are used interchangeably across the bot:
    A  what the GAME says is filled   `gPlayerPartyCount`
    B  what the bot can READ          `len(get_party())`  — can be LESS than A
    C  what the bot BELIEVES it put   (does not exist; deliberately NOT built by Stage 0)
`get_party()` COMPACTS — it loops `range(gPlayerPartyCount)` and `continue`s any (near-)all-zero
slot — so a HOLE makes B < A and makes every later Pokémon's list position differ from its
physical `gPlayerParty` slot. That divergence is the root beneath the Slugma derail (P1) and the
wrong-target RELEASE (KI-78 / P2).

WHAT STAGE 0 CLAIMS, AND THEREFORE WHAT THIS GATE MUST PROVE. Stage 0 adds READERS and a
DIVERGENCE LOG and **wires no call site**. So there are exactly two claims:
    (1) the observer SEES each divergence class, from inside the REAL `get_party()`; and
    (2) it changes NOTHING — same return value, and it cannot break a party read.

⛔ **THE FIXTURE DRIVES THE SHIPPED `get_party()`, NOT A COPY OF ITS LOGIC.** Fabricated
`gPlayerParty` / `gPlayerPartyCount` memory is injected behind `read_symbol`, with a stub emulator
supplying the `peek_frame()` retry path an empty slot actually takes. A gate that re-implemented
the loop would be testing this file's idea of the reader. ‼ And the fixture holds GENUINE Gen 3
party records — real substructure ordering, real `personality ^ OT id` XOR, a real checksum and a
real `SANITY_HAS_SPECIES` bit — because `is_empty` and `is_valid` are precisely the predicates
under test and a duck-typed stand-in would sail past both.

THE CHECKS:
  * HOLE     — a zero slot below the count is SEEN, and `get_party()` still returns the survivors
               at their PHYSICAL slots (0 and 2, not 0 and 1).
  * OVERFLOW — a count byte of 7 is SEEN.
  * STALE    — an occupied slot ABOVE the count is SEEN by the sampled six-slot scan.
  * INVALID  — a slot that is neither decodable nor empty is SEEN, and `get_party()` still raises.
  * ⛔ CONTROL — FALSE POSITIVES. A healthy three-Pokémon party must record **NOTHING**. This is
               the check that keeps the gate honest: a detector that fires on everything is
               bypassed exactly like a noisy reviewer (`CLAUDE.md` rule 6).
  * ⛔ CONTROL — NO BEHAVIOUR CHANGE. The same fixtures are run with the observer hooks stubbed
               to no-ops, and the returned parties must be IDENTICAL. This is the whole Stage 0
               promise, so it is asserted rather than asserted-in-prose.
  * ⛔ FAULT INJECTION — a BROKEN observer must not break a party read, and must SAY it is broken.
               `record_divergence` is made to raise; `get_party()` must still return the right
               party, and the fault must be REPORTED (a silently broken observer would answer
               "no divergence" forever and the negative would be believed).
  * DEDUP    — the same signature seen 50 times announces once and counts 50, so "seen once" and
               "seen constantly" stay distinguishable.

Exit 0 = all checks pass. Exit 1 = a check failed (details printed).

Run:  cd tools/story-dev && PYTHONUTF8=1 py -3.12 repro_party_accounting.py [--build sandbox|custom]
"""

import argparse
import contextlib
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

PARTY_RECORD_SIZE = 100
PARTY_SIZE = 6

#: Species INTERNAL indices, read out of our own `modules/data/species.json` (list position IS the
#: internal index). ⛔ NOT National Dex numbers — Gen 3's internal table keeps 252-276 as unused
#: `?` placeholders and starts the Hoenn species at 277. This gate first shipped with the National
#: numbers (252/261/263) and its species check PASSED ANYWAY, because a `?` placeholder echoes back
#: the index it was asked for. See the hardened assertion below and `08-MISTAKES.md` (2026-08-14).
TREECKO, POOCHYENA, ZIGZAGOON = 277, 286, 288

EMPTY_SLOT = b"\x00" * PARTY_RECORD_SIZE


def build_mon(pid: int, otid: int, species: int) -> bytes:
    """A genuine 100-byte party record that `get_party()` will accept.

    Mirrors `Pokemon._decrypted_data` in reverse: logical substructure `i` lives at raw offset
    `32 + order[i] * 12`, every 32-bit word XORed with `personality ^ OT id`.
    ‼ Two bytes matter beyond that and are why a hand-rolled blob would be rejected:
      * byte 19 bit 1 — `SANITY_HAS_SPECIES`. Without it `is_empty` is True and the reader treats
        a perfectly good Pokémon as a HOLE, which would make this gate pass for the wrong reason.
      * bytes 28-29 — the checksum `is_valid` compares against the sum of the 24 decrypted
        halfwords of the substructure block. Computed here, never hardcoded.
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

    decrypted_block = b"".join(logical)
    checksum = sum(struct.unpack("<24H", decrypted_block)) & 0xFFFF

    header = bytearray(struct.pack("<II", pid, otid) + b"\x00" * 24)   # 32 bytes
    header[19] |= 0x02                                                 # SANITY_HAS_SPECIES
    header[28:30] = struct.pack("<H", checksum)

    return bytes(header) + b"".join(raw_substructs) + b"\x00" * 20     # 32 + 48 + 20 = 100


class FakeCore:
    """`context.emulator._core` — the empty-slot retry path calls `run_frame()` five times."""

    def run_frame(self) -> None:
        return None


class FakeEmulator:
    """The minimum `get_party()` and `state_cache` touch. No ROM, no libmgba.

    `get_frame_count` increments on every call so `state_cache.party.age_in_frames` is never 0 —
    otherwise the second scenario would silently return the FIRST scenario's cached party and
    every check after it would be grading a stale reading.
    """

    def __init__(self) -> None:
        self._core = FakeCore()
        self._frame = 0

    def get_frame_count(self) -> int:
        self._frame += 1
        return self._frame

    @contextlib.contextmanager
    def peek_frame(self, frames_to_advance: int = 1):
        yield


class FakeMemory:
    """Fabricated `gPlayerPartyCount` and `gPlayerParty`, injected behind `read_symbol`."""

    def __init__(self, count: int, slots: "list[bytes]") -> None:
        padded = list(slots) + [EMPTY_SLOT] * (PARTY_SIZE - len(slots))
        self.symbols = {
            "gPlayerPartyCount": bytes([count]),
            #: One extra slot of zeroes so an OVERFLOW count reads past the end without an
            #: IndexError — the real reader would find adjacent RAM there, not an exception.
            "gPlayerParty": b"".join(padded[:PARTY_SIZE]) + EMPTY_SLOT,
        }

    def read_symbol(self, name: str, offset: int = 0, size: int = 0) -> bytes:
        block = self.symbols[name]
        return block[offset : offset + size] if size else block[offset:]


def main() -> int:
    failures = []

    # ‼ The gate COUNTS ITS OWN CHECKS and prints the total. Written after a doc entry claimed "34
    # checks" when there were 33: a hand-typed count in prose is a number nobody re-derives, and
    # this project's standing rule is that the CODE is authoritative and the prose never is.
    performed = []

    def check(label, condition, detail=""):
        performed.append(label)
        status = "PASS" if condition else "FAIL"
        print(f"  {status}  {label}{('  — ' + detail) if detail else ''}")
        if not condition:
            failures.append(label)

    print(BAR)
    print("REPRO — PARTY ACCOUNTING STAGE 0: A (gPlayerPartyCount) vs B (len(get_party()))")
    print(f"BUILD UNDER TEST: {_ARGS.build}-pokebot")
    print(BAR)

    import modules.pokemon_party as party_mod
    from modules.context import context
    from modules import party_accounting

    # ‼ ASSERT WHICH FORK WE IMPORTED, BEFORE TESTING ANYTHING. A gate that always imports the
    # sandbox cannot tell you whether a promoted fix actually landed in the other fork — that
    # exact hole shipped once already (`07-CHANGELOG.md`, 2026-08-14 promotion entry).
    imported_from = pathlib.Path(party_mod.__file__).resolve()
    expected_root = (REPO / f"{_ARGS.build}-pokebot").resolve()
    print(f"  (importing from {expected_root.name} — "
          f"{'verified' if expected_root in imported_from.parents else '‼ WRONG FORK'})")
    check("the module under test came from the requested fork",
          expected_root in imported_from.parents, str(imported_from))

    context.emulator = FakeEmulator()

    real_read_symbol = party_mod.read_symbol
    real_accounting_read_symbol = party_accounting.read_symbol

    def run_scenario(count: int, slots: "list[bytes]", *, silence_observer: bool = False,
                     break_observer: bool = False):
        """Drive the REAL `get_party()` over fabricated memory. Returns (party, error, tally)."""
        memory = FakeMemory(count, slots)
        party_mod.read_symbol = memory.read_symbol
        party_accounting.read_symbol = memory.read_symbol
        party_accounting.reset_party_accounting()
        party_mod._accounting_fault_reported = False

        saved = {}
        if silence_observer:
            # The CONTROL ARM: the shipped hooks replaced by no-ops, so the only difference
            # between the arms is the observer itself.
            saved["_account_recompute"] = party_mod._account_recompute
            saved["_account_slot_anomaly"] = party_mod._account_slot_anomaly
            party_mod._account_recompute = lambda *a, **k: None
            party_mod._account_slot_anomaly = lambda *a, **k: None
        if break_observer:
            saved["record_divergence"] = party_accounting.record_divergence

            def _explode(*_a, **_k):
                raise ValueError("fault-injected observer failure")

            party_accounting.record_divergence = _explode

        error = None
        party = None
        try:
            party = party_mod.get_party()
        except Exception as caught:  # the INVALID scenario is SUPPOSED to raise; capture it.
            error = caught
        finally:
            for name, original in saved.items():
                if name == "record_divergence":
                    party_accounting.record_divergence = original
                else:
                    setattr(party_mod, name, original)
            party_mod.read_symbol = real_read_symbol
            party_accounting.read_symbol = real_accounting_read_symbol

        return party, error, party_accounting.observed()

    def kinds(tally) -> "set[str]":
        return {signature.split(":", 1)[0] for signature in tally}

    healthy = [build_mon(0x11111111, 0xAAAA0001, TREECKO),
               build_mon(0x22222222, 0xAAAA0002, POOCHYENA),
               build_mon(0x33333333, 0xAAAA0003, ZIGZAGOON)]

    # ---------------------------------------------------------------------------------------
    print("\n[ CONTROL — a healthy party must record NOTHING ]")
    # ---------------------------------------------------------------------------------------
    party, error, tally = run_scenario(3, healthy)
    check("the fixture is accepted by the REAL reader (3 Pokemon read back)",
          error is None and party is not None and len(party) == 3,
          f"error={error!r} len={None if party is None else len(party)}")
    check("‼ NO false positive: a healthy party records no divergence at all",
          tally == {}, f"tally={tally}")
    # ‼ THE NAME CHECK IS NOT DECORATION — IT IS WHAT STOPS THIS PASSING VACUOUSLY. An index that
    # addresses an unused `?` slot in the species table decodes back to the same index, so
    # comparing indices alone cannot distinguish "the encryption round-tripped" from "I fabricated
    # a Pokémon that does not exist". Asserting a REAL NAME is the positive control.
    decoded_names = [] if party is None else [p.species.name for p in party]
    check("species decode correctly, so is_valid/is_empty really were satisfied",
          party is not None and [p.species.index for p in party] == [TREECKO, POOCHYENA, ZIGZAGOON],
          str(decoded_names))
    check("‼ ...and they are REAL species, not the `?` placeholders that echo their own index",
          decoded_names == ["Treecko", "Poochyena", "Zigzagoon"], str(decoded_names))

    # ---------------------------------------------------------------------------------------
    print("\n[ HOLE — an empty slot BELOW the count: A=3, B=2 ]")
    # ---------------------------------------------------------------------------------------
    holed = [healthy[0], EMPTY_SLOT, healthy[2]]
    party, error, tally = run_scenario(3, holed)
    check("HOLE is observed from inside the real get_party()", "HOLE" in kinds(tally), str(tally))
    check("B is genuinely less than A (2 read from a count of 3)",
          error is None and party is not None and len(party) == 2,
          f"error={error!r} len={None if party is None else len(party)}")
    check("‼ the survivors keep their PHYSICAL slots (0 and 2, not 0 and 1)",
          party is not None and [p.index for p in party] == [0, 2],
          "" if party is None else str([p.index for p in party]))
    check("the hole is reported at the right slot", any(":slot 1 of" in s for s in tally), str(tally))
    check("no OTHER class fires on a plain hole", kinds(tally) == {"HOLE"}, str(kinds(tally)))

    # ---------------------------------------------------------------------------------------
    print("\n[ OVERFLOW — the count byte says 7, and there are six slots ]")
    # ---------------------------------------------------------------------------------------
    party, error, tally = run_scenario(7, healthy)
    check("OVERFLOW is observed", "OVERFLOW" in kinds(tally), str(tally))
    check("get_party() still returns the readable Pokemon rather than dying",
          error is None and party is not None and len(party) == 3,
          f"error={error!r} len={None if party is None else len(party)}")

    # ---------------------------------------------------------------------------------------
    print("\n[ STALE — an occupied slot ABOVE the count (sampled scan) ]")
    # ---------------------------------------------------------------------------------------
    stale_slots = [healthy[0], healthy[1], EMPTY_SLOT, EMPTY_SLOT, healthy[2], EMPTY_SLOT]
    party, error, tally = run_scenario(2, stale_slots)
    check("STALE is observed by the six-slot scan", "STALE" in kinds(tally), str(tally))
    check("the stale slot is named", any("slots [4]" in s for s in tally), str(tally))
    check("‼ STALE bytes are NOT counted as party members (B stays 2)",
          error is None and party is not None and len(party) == 2,
          f"len={None if party is None else len(party)}")
    accounting_now = None
    memory = FakeMemory(2, stale_slots)
    party_accounting.read_symbol = memory.read_symbol
    try:
        accounting_now = party_accounting.read_party_accounting(readable_count=2)
    finally:
        party_accounting.read_symbol = real_accounting_read_symbol
    check("the reader separates A from raw occupancy (A=2, occupied=3)",
          accounting_now is not None and accounting_now.game_count == 2
          and accounting_now.occupied_count == 3 and accounting_now.stale == (4,),
          "" if accounting_now is None else accounting_now.describe())

    # ---------------------------------------------------------------------------------------
    print("\n[ INVALID — neither decodable nor empty: the reader must still raise ]")
    # ---------------------------------------------------------------------------------------
    corrupt = bytearray(healthy[1])
    corrupt[28:30] = struct.pack("<H", 0xDEAD)   # a checksum that cannot match
    party, error, tally = run_scenario(3, [healthy[0], bytes(corrupt), healthy[2]])
    check("INVALID is observed", "INVALID" in kinds(tally), str(tally))
    check("‼ get_party() STILL RAISES — the observer did not swallow the failure",
          isinstance(error, RuntimeError), f"error={error!r}")

    # ---------------------------------------------------------------------------------------
    print("\n[ ⛔ CONTROL — NO BEHAVIOUR CHANGE: observer on vs observer stubbed out ]")
    # ---------------------------------------------------------------------------------------
    for label, count, slots in (("healthy", 3, healthy), ("holed", 3, holed),
                                ("overflow", 7, healthy), ("stale", 2, stale_slots)):
        with_obs, err_a, _ = run_scenario(count, slots)
        without_obs, err_b, empty_tally = run_scenario(count, slots, silence_observer=True)
        same = (
            type(err_a) is type(err_b)
            and (with_obs is None) == (without_obs is None)
            and (with_obs is None or (
                len(with_obs) == len(without_obs)
                and [p.index for p in with_obs] == [p.index for p in without_obs]
                and [p.data for p in with_obs] == [p.data for p in without_obs]
            ))
        )
        check(f"get_party() is byte-identical with and without the observer ({label})", same,
              f"len={None if with_obs is None else len(with_obs)} err={type(err_a).__name__}")
        if label == "holed":
            check("the stubbed control arm really did silence the observer", empty_tally == {},
                  str(empty_tally))

    # ---------------------------------------------------------------------------------------
    print("\n[ ⛔ FAULT INJECTION — a BROKEN observer must not break a party read, and must SAY so ]")
    # ---------------------------------------------------------------------------------------
    party, error, tally = run_scenario(3, holed, break_observer=True)
    check("a raising observer does NOT propagate into get_party()",
          error is None and party is not None and len(party) == 2,
          f"error={error!r} len={None if party is None else len(party)}")
    check("‼ the broken observer ANNOUNCED itself rather than reporting a clean bill of health",
          party_mod._accounting_fault_reported is True,
          f"_accounting_fault_reported={party_mod._accounting_fault_reported}")

    # ---------------------------------------------------------------------------------------
    print("\n[ DEDUP — announce once, count every time ]")
    # ---------------------------------------------------------------------------------------
    party_accounting.reset_party_accounting()
    for _ in range(50):
        party_accounting.record_divergence("HOLE", "slot 1 of gPlayerPartyCount=3: fabricated")
    tally = party_accounting.observed()
    check("50 sightings collapse to ONE signature", len(tally) == 1, str(list(tally)))
    check("...but the count is preserved (50, not 1)", list(tally.values()) == [50], str(tally))
    recomputes, scans = party_accounting.sample_counts()
    check("the summary reports its own sample size beside a zero",
          any("recomputes" in line for line in party_accounting.summary_lines()),
          f"recomputes={recomputes} scans={scans}")

    # ---------------------------------------------------------------------------------------
    print("\n[ ⛔ SATURATION — the tally is BOUNDED, and it must SAY when it truncates ]")
    # ---------------------------------------------------------------------------------------
    # Raised by an adversarial review: a signature embeds the count byte and a slot subset, so
    # corrupted memory can generate thousands of distinct ones. The cap is fine; a cap that
    # truncates SILENTLY is not — a saturated log would read exactly like a quiet one.
    party_accounting.reset_party_accounting()
    cap = party_accounting._MAX_SIGNATURES
    for n in range(cap + 25):
        party_accounting.record_divergence("HOLE", f"fabricated distinct signature {n}")
    tally = party_accounting.observed()
    check("the tally is BOUNDED at its cap rather than growing without limit",
          len(tally) == cap, f"len={len(tally)} cap={cap}")
    saturation = [line for line in party_accounting.summary_lines() if "SATURATED" in line]
    check("‼ ...and it SAYS it truncated — a silent cap is indistinguishable from a quiet run",
          len(saturation) == 1 and "25" in saturation[0], str(saturation))
    # The false-positive control for the cap: an already-known signature must keep counting even
    # while saturated, or a persistent anomaly would stop being measured exactly when it matters.
    before = party_accounting.observed()["HOLE:fabricated distinct signature 0"]
    party_accounting.record_divergence("HOLE", "fabricated distinct signature 0")
    after = party_accounting.observed()["HOLE:fabricated distinct signature 0"]
    check("a signature already in the tally keeps counting while saturated",
          after == before + 1, f"{before} -> {after}")
    party_accounting.reset_party_accounting()
    check("reset clears the saturation state too",
          party_accounting.observed() == {}
          and not any("SATURATED" in line for line in party_accounting.summary_lines()),
          str(party_accounting.observed()))

    # ---------------------------------------------------------------------------------------
    print("\n[ ⛔ STAGE 0 SCOPE — no call site may have been re-pointed at A ]")
    # ---------------------------------------------------------------------------------------
    consumers = []
    for path in sorted((REPO / f"{_ARGS.build}-pokebot" / "modules").rglob("*.py")):
        if path.name in ("party_accounting.py", "pokemon_party.py"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "party_accounting" in text or "game_party_count" in text:
            consumers.append(path.name)
    check("‼ Stage 0 wires NO consumer — the readers exist and nothing depends on them yet",
          consumers == [], f"unexpected consumers: {consumers}")

    print("\n" + BAR)
    if failures:
        print(f"FAILED — {len(failures)} of {len(performed)} check(s): {failures}")
        print(BAR)
        return 1
    print(f"ALL {len(performed)} CHECKS PASS")
    print(BAR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
