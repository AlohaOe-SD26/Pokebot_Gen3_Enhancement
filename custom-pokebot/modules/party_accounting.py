"""PARTY ACCOUNTING — STAGE 0: the READERS and a DIVERGENCE LOG. Wires no decision.

‼ WHY THIS MODULE EXISTS (user-designed; `06-DECISIONS-LOG.md` RULING D, 2026-08-14).
Three different quantities are used interchangeably across the bot today, and conflating them is
the ROOT beneath the Slugma derail (P1) and KI-78 (P2):

    A  what the GAME says is filled   `gPlayerPartyCount`               — the game's own authority
    B  what the bot can READ          `len(get_party())`                — can be LESS than A
    C  what the bot BELIEVES it put   (does not exist, and Stage 0 does NOT build it)

**B can be less than A** because `get_party()` COMPACTS: it loops `range(gPlayerPartyCount)` and
`continue`s any slot whose 100 bytes are (near-)all zero (`pokemon_party.py:219-221`). Every
Pokémon after such a hole then sits at a list position that is NOT its physical `gPlayerParty`
slot — the exact divergence that made `get_index_for_pokemon` return a list position to a
consumer driving a PHYSICAL cursor (DEPOSIT, and RELEASE, which is permanent).

The user's framing, verbatim: *"maybe we robustly enhance the Party detection/count logic so it
counts filled spaces vs empty spaces (not whether it logs the pokemon as caught or moved to the
party, that is still valuable ... but should be a separate function"*.

⛔ **WHAT STAGE 0 DELIBERATELY DOES NOT DO.** It changes NO call site and NO decision. Not one of
the 207 party-count reads in the tree is re-pointed at these readers. The reason is stated in the
handoff and is a direct application of this project's own pre-flight question *"could my detector
have returned POSITIVE at all?"*: **we do not know yet whether A ever actually differs from B in a
real run.** Stage 0 exists to ANSWER that, cheaply and passively, before anything depends on it.
Migrating the ~35 capacity-shaped call sites is Stage 1 and needs this measurement first.

⛔ **AND INDEX/CURSOR CALL SITES MUST NEVER MOVE TO A.** If A > B, an index derived from A is
OUT OF RANGE for the compacted list `get_party()` returns — and the most likely place to find out
is MID-BATTLE, in the faint chooser. A is a CAPACITY answer ("is there a free slot?"); B is an
ITERATION answer ("what can I address?"). They are not interchangeable in either direction.

‼ **C IS NOT BUILT HERE, ON PURPOSE.** A "what the bot believes it has" ledger is genuinely
wanted (RULING D calls it valuable) but it is a *separate* function by the user's own design, and
a belief ledger that disagrees with the game is only diagnosable once we can measure the GAME's
two numbers. C comes after this measurement, not with it.

--------------------------------------------------------------------------------------------
WHAT IS MEASURED, AND HOW EXACTLY EACH CLASS IS OBSERVED (honesty about coverage matters here —
a class observed by SAMPLING must never be reported as if it were observed exhaustively):

  HOLE      a (near-)empty slot at index < A          ⇒ A > B.  **EXACT** — observed from inside
            `get_party()`'s own skip branch, so every occurrence is seen, at zero extra cost.
  OVERFLOW  A > 6, i.e. the count byte is not sane.   **EXACT** — `get_party()` has already read A.
  INVALID   a slot that is neither decodable nor      **EXACT** — recorded immediately before
            empty; `get_party()` raises on it.        `get_party()` raises, so the raise is dated.
  STALE     a non-empty slot at index >= A.           ⛔ **SAMPLED**, not exhaustive. It cannot be
            The game ignores these bytes; they are    seen without scanning slots `get_party()`
            not party members. Measured because a     never reads, so it is checked once every
            naive "count the non-empty slots" reader  `_STALE_SCAN_INTERVAL` recomputes. A zero
            — which is the obvious way to write the   here means "not seen in the samples taken",
            filled-vs-empty reader RULING D asks for  NEVER "does not happen". The sample count is
            — would COUNT them and be WRONG.          printed beside it for exactly this reason.

Nothing in this module may raise into its caller: it is telemetry hanging off the party reader,
and a crash here would break every party read in the bot. Every outward call is guarded, and each
guard SAYS something or carries an explicit justification (`repro_no_silent_except.py`'s rule).

Gate: `tools/story-dev/repro_party_accounting.py` (no emulator, fabricated memory, fault-tested
in both directions — it proves the observer FIRES on each class and, just as importantly, that it
stays SILENT on a healthy party).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from modules.memory import read_symbol

#: Physical size of `gPlayerParty` — six 100-byte records. Not configurable; it is the game's.
PARTY_SIZE = 6

#: Bytes per party record.
PARTY_RECORD_SIZE = 100

#: How many `get_party()` RECOMPUTES between full six-slot scans (the only way to see STALE).
#: ✅ **MEASURED, not assumed** (an adversarial review flagged this as an unverifiable claim, and
#: it was): a full `--driver ch20dive` run reported **25,523 recomputes over 25,523 frames**, i.e.
#: exactly one per frame — the `state_cache.party.age_in_frames == 0` early return holds. So 300 is
#: ~5 seconds of emulation: negligible cost, frequent enough that a persistent stale slot cannot
#: hide. ‼ This is a SAMPLE RATE, and the summary reports how many samples were actually taken.
_STALE_SCAN_INTERVAL = 300

#: Hard cap on DISTINCT signatures kept in the tally. ⛔ Not decoration: a signature embeds the
#: count byte and, for STALE, a subset of six slots — so genuinely corrupted memory (an unstable
#: count byte) has a signature space in the thousands, not the handful the common case suggests.
#: Once saturated the tally stops accepting NEW signatures and SAYS SO in the summary; it keeps
#: counting the ones it already has. ‼ Silently dropping them would make a saturated log
#: indistinguishable from a quiet one, which is this project's "a check that cannot see must SAY
#: so, never pass" rule. Raised by an adversarial review of Stage 0.
_MAX_SIGNATURES = 200


def _slot_is_empty(record: bytes) -> bool:
    """Is this 100-byte record an empty slot?

    ‼ MIRRORS `pokemon_party.py:220` EXACTLY (`.count(b"\\x00") >= 99`) and must keep mirroring it.
    If this module used a stricter or looser emptiness test than the reader it is measuring, the
    two would disagree about what a hole IS and the divergence log would be measuring the
    difference between two predicates rather than a real party anomaly.
    """
    return record.count(b"\x00") >= 99


@dataclass(frozen=True)
class PartyAccounting:
    """A single reading of the three slot-level quantities. A snapshot, never cached."""

    #: A — what the GAME says is filled. The authority for "is there a free slot?".
    game_count: int

    #: B — what the bot can READ, i.e. `len(get_party())`. `None` when the caller did not supply
    #: it (reading it here would recurse into `get_party()`).
    readable_count: int | None

    #: Physical occupancy of all six slots, independent of A. Index i is slot i.
    occupied: tuple[bool, ...]

    #: Indices < A that are EMPTY. These are the holes that make B < A.
    holes: tuple[int, ...]

    #: Indices >= A that are OCCUPIED. Bytes the game does not count as party members.
    stale: tuple[int, ...]

    @property
    def occupied_count(self) -> int:
        """How many of the six physical slots hold something.

        ⛔ **THIS IS NOT THE PARTY SIZE AND MUST NOT BE USED AS ONE.** It counts stale bytes past
        `gPlayerPartyCount` that the game does not consider party members. It exists to MEASURE
        how wrong the naive "just count the filled slots" reader would be.
        """
        return sum(1 for occupied in self.occupied if occupied)

    @property
    def overflow(self) -> bool:
        """Is the count byte outside the range the hardware can hold?"""
        return self.game_count > PARTY_SIZE or self.game_count < 0

    @property
    def diverges(self) -> bool:
        return bool(self.holes) or bool(self.stale) or self.overflow

    def describe(self) -> str:
        return (
            f"A(game)={self.game_count} B(readable)="
            f"{'?' if self.readable_count is None else self.readable_count} "
            f"occupied={self.occupied_count} holes={list(self.holes)} stale={list(self.stale)}"
        )


def game_party_count() -> int:
    """**A** — how many party slots the GAME says are filled (`gPlayerPartyCount`).

    This is the authority for CAPACITY questions: *is the party full? is there room for a caught
    Pokémon, an egg, or a Shedinja the bot did not ask for?* The game itself gates
    `CreateShedinja` on `gPlayerPartyCount < PARTY_SIZE`, so this is literally the number that
    decides whether a sixth party member can appear without the bot doing anything.

    ⛔ NEVER use this as a loop bound or a list index over `get_party()` — see the module header.
    """
    return read_symbol("gPlayerPartyCount", size=1)[0]


def party_slot_occupancy() -> tuple[bool, ...]:
    """Physical filled/empty state of each of the six `gPlayerParty` slots, ignoring A.

    This is the literal "counts filled spaces vs empty spaces" reader RULING D asked for. It is
    exported for MEASUREMENT and diagnostics. ⛔ It is deliberately NOT a party-size reader: see
    `PartyAccounting.occupied_count`.
    """
    block = read_symbol("gPlayerParty", offset=0, size=PARTY_SIZE * PARTY_RECORD_SIZE)
    return tuple(
        not _slot_is_empty(block[index * PARTY_RECORD_SIZE : (index + 1) * PARTY_RECORD_SIZE])
        for index in range(PARTY_SIZE)
    )


def read_party_accounting(readable_count: int | None = None) -> PartyAccounting:
    """Take one full reading of A, the physical occupancy, and the divergences between them.

    `readable_count` (B) is passed IN rather than read, because reading it means calling
    `get_party()` — which is the function this module is instrumenting. Recursing into it from
    its own telemetry is how a cheap observer becomes an infinite loop.
    """
    game_count = game_party_count()
    occupied = party_slot_occupancy()
    countable = min(max(game_count, 0), PARTY_SIZE)
    holes = tuple(index for index in range(countable) if not occupied[index])
    stale = tuple(index for index in range(countable, PARTY_SIZE) if occupied[index])
    return PartyAccounting(
        game_count=game_count,
        readable_count=readable_count,
        occupied=occupied,
        holes=holes,
        stale=stale,
    )


# ------------------------------------------------------------------------------------------------
# THE DIVERGENCE LOG
#
# One in-process tally per bot run. Each distinct signature announces itself ONCE and then only
# increments — a per-frame reader can hit the same anomaly thousands of times, and a log that
# repeats itself is a log nobody reads. ‼ The COUNT is kept, so "seen once" and "seen 40,000
# times" remain distinguishable; that difference is most of what Stage 1 needs to know.
# ------------------------------------------------------------------------------------------------


@dataclass
class _DivergenceTally:
    #: signature -> times seen
    counts: dict[str, int] = field(default_factory=dict)
    #: signature -> the first description, kept verbatim for the summary
    first_seen: dict[str, str] = field(default_factory=dict)
    #: How many full six-slot scans have actually been performed (STALE's sample size).
    stale_scans: int = 0
    #: How many times `get_party()` recomputed. The denominator for everything above.
    recomputes: int = 0
    #: Distinct signatures REFUSED because the tally hit `_MAX_SIGNATURES`. Reported, never hidden.
    dropped_signatures: int = 0


_tally = _DivergenceTally()


def reset_party_accounting() -> None:
    """Start a fresh tally. For the gate, and for a bot run that resets the emulator."""
    global _tally
    _tally = _DivergenceTally()


def _announce(message: str) -> None:
    """Say something, once, on both channels. ‼ Telemetry must never break the party reader."""
    try:
        from modules.console import console

        console.print(f"[bold yellow]{message}[/]")
    except Exception:  # noqa: BLE001 — the console is optional (headless, tests); a missing
        # console must not turn a party read into a crash. The debug log below is the durable
        # record, and it is attempted independently for exactly that reason.
        pass
    try:
        from modules import debug_logger

        debug_logger.event(message, category="PARTY-ACCT")
    except Exception:  # noqa: BLE001 — same contract: the run log is best-effort telemetry, and
        # `debug_logger.event` is already a no-op when logging is disabled. A failure here is a
        # lost diagnostic line, never a reason to break the caller.
        pass


def record_divergence(kind: str, detail: str) -> int:
    """Record one observation of a divergence class. Returns how many times it has now been seen.

    Announces LOUDLY on the first sighting of each distinct signature and stays quiet afterwards.
    """
    signature = f"{kind}:{detail}"
    if signature not in _tally.counts and len(_tally.counts) >= _MAX_SIGNATURES:
        # SATURATED. Refuse the new signature, but never silently: a truncated log that looks
        # complete is worse than no log, and the summary reports the drop count.
        _tally.dropped_signatures += 1
        if _tally.dropped_signatures == 1:
            _announce(
                f"[PARTY-ACCT] ‼ TALLY SATURATED at {_MAX_SIGNATURES} distinct signatures. "
                f"Further NEW signatures are counted as dropped, not recorded. Existing ones keep "
                f"counting. ⛔ This many distinct signatures is itself the finding — treat this "
                f"run's party memory as unstable rather than reading the tally as complete."
            )
        return 0
    seen = _tally.counts.get(signature, 0) + 1
    _tally.counts[signature] = seen
    if seen == 1:
        _tally.first_seen[signature] = detail
        _announce(f"[PARTY-ACCT] {kind} — {detail} (first sighting; Stage 0 is OBSERVING ONLY)")
    return seen


def note_recompute() -> bool:
    """Called once per `get_party()` RECOMPUTE. Returns whether this one should scan all six slots.

    Keeping the counter here rather than in `pokemon_party` keeps the reader's hook to a single
    line and keeps every accounting decision in one file.
    """
    _tally.recomputes += 1
    due = _tally.recomputes % _STALE_SCAN_INTERVAL == 1
    if due:
        _tally.stale_scans += 1
    return due


def observed() -> dict[str, int]:
    """The tally so far: signature -> times seen. A copy; callers cannot corrupt the log."""
    return dict(_tally.counts)


def sample_counts() -> tuple[int, int]:
    """`(get_party() recomputes, full six-slot scans)` — the denominators for the tally.

    ‼ Report these beside any zero. "STALE: 0 in 12 scans" is a measurement; a bare "STALE: 0"
    is an unfalsifiable claim, and this project has twice believed a negative from a detector
    that could not have returned positive.
    """
    return _tally.recomputes, _tally.stale_scans


def summary_lines() -> list[str]:
    """A human-readable report of the run's party accounting. Safe to call at any time."""
    recomputes, scans = sample_counts()
    lines = [
        f"[PARTY-ACCT] STAGE 0 SUMMARY — {recomputes} get_party() recomputes, "
        f"{scans} full six-slot scans (STALE is sampled at 1/{_STALE_SCAN_INTERVAL}, "
        f"HOLE/OVERFLOW/INVALID are exact)."
    ]
    if _tally.dropped_signatures:
        lines.append(
            f"[PARTY-ACCT] ‼ SATURATED — {_tally.dropped_signatures} distinct signature(s) were "
            f"DROPPED after the {_MAX_SIGNATURES} cap. The list below is INCOMPLETE."
        )
    if not _tally.counts:
        lines.append(
            "[PARTY-ACCT] NO DIVERGENCE OBSERVED. ‼ Read this as 'A never differed from B in what "
            "was sampled', NOT as 'A cannot differ from B'."
        )
        return lines
    for signature, count in sorted(_tally.counts.items(), key=lambda item: -item[1]):
        lines.append(f"[PARTY-ACCT]   {signature}  x{count}")
    return lines
