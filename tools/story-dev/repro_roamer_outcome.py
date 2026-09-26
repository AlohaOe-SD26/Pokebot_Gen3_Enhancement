r"""GATE — the roamer's fatal-outcome rule must be the PARITY the game evaluates, not a name list.

WHY THIS EXISTS (2026-09-25)
----------------------------
Our bot fights to WIN. Winning a roamer battle permanently deactivates Latias/Latios — no reload,
no respawn. `src/battle_main.c` decides it with, in the VANILLA build (`//#define BUGFIX` is
commented out at `include/config.h:48`, so `#ifndef BUGFIX` is the live branch):

    if ((gBattleOutcome & B_OUTCOME_WON) || gBattleOutcome == B_OUTCOME_CAUGHT)
        SetRoamerInactive();

`B_OUTCOME_WON == 1`, so this is a **PARITY TEST**: every ODD outcome is fatal.

⛔ AN EARLIER RESEARCH PASS LISTED "WON / DREW / PLAYER_TELEPORTED" AND MISSED **FORFEITED (9)**.
A three-name list would have shipped a hole. ⇒ this gate pins the PROPERTY, and check R2 exists
specifically to fail any re-write that degenerates back into an enumeration.

WHAT IT CHECKS
  R1  The full 1..10 table matches the game's rule exactly, outcome by outcome.
  R2  ⭐ THE ANTI-ENUMERATION ARM — `FORFEITED (9)` and `CAUGHT (7)` must be fatal. These are the two
      the "obvious" three-name list omits, so a regression to it fails HERE and nowhere else.
  R3  COUNTER-INTUITIVE CASES, asserted explicitly so nobody "fixes" them later:
      LOST (2) is SAFE, MON_FLED (6) is SAFE, and RAN (4) is SAFE — while DREW (3) is FATAL.
  R4  UNREADABLE IS NOT SAFE — `None` and garbage must read as FATAL. The loss is irreversible, so
      "I could not tell" must never be reported as "it survived".
  R5  The name table is complete for 1..10 and `outcome_name` never returns a bare integer.

⛔ ALL OFFLINE — pure arithmetic against a decomp-derived table. No emulator, no ROM.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent / "sandbox-pokebot"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


#: outcome -> fatal?  Derived from `(outcome & 1)`, which IS the expression the retail ROM runs.
EXPECTED = {
    1: True,    # WON
    2: False,   # LOST                 — whiting out does NOT destroy it
    3: True,    # DREW                 — a mutual KO counts as a win here
    4: False,   # RAN                  — the ONLY safe player-chosen exit
    5: True,    # PLAYER_TELEPORTED    — Roar / Teleport; the decomp calls it a bug
    6: False,   # MON_FLED             — the roamer fleeing on its own is fine
    7: True,    # CAUGHT               — fatal to the ENCOUNTER, but it is the goal
    8: False,   # NO_SAFARI_BALLS
    9: True,    # FORFEITED            — ⭐ the one the name-list missed
    10: False,  # MON_TELEPORTED
}


def run() -> int:
    print("=" * 96)
    print("GATE — a roamer dies to any ODD outcome; the rule is PARITY, not a list of names")
    print("=" * 96)

    try:
        from modules.story.protected_encounters import (
            B_OUTCOME_NAMES,
            outcome_name,
            roamer_outcome_is_fatal as fatal,
        )
    except Exception as error:  # noqa: BLE001
        print(f"  ⛔ cannot import `protected_encounters`: {error!r}")
        print("RESULT: FAIL — the module under test is absent.")
        return 1

    # R1 — the whole table
    wrong = [(o, fatal(o), want) for o, want in EXPECTED.items() if fatal(o) is not want]
    check("R1 the full 1..10 table matches the game's parity rule", not wrong,
          f"mismatches (outcome, got, want) = {wrong}")

    # R2 — the anti-enumeration arm
    check("R2 ANTI-ENUMERATION: FORFEITED (9) is fatal", fatal(9) is True,
          "a 'WON/DREW/PLAYER_TELEPORTED' list would say False here")
    check("R2b ANTI-ENUMERATION: CAUGHT (7) is fatal to the encounter", fatal(7) is True)

    # R3 — the counter-intuitive ones, pinned
    check("R3 LOST (2) is SAFE — whiting out does not destroy the roamer", fatal(2) is False)
    check("R3b MON_FLED (6) is SAFE — the roamer fleeing on its own is fine", fatal(6) is False)
    check("R3c RAN (4) is SAFE — the only safe player-CHOSEN exit", fatal(4) is False)
    check("R3d DREW (3) is FATAL — a mutual KO counts", fatal(3) is True)

    # R4 — unreadable is not safe
    check("R4 None reads as FATAL (an irreversible loss must not be optimistic)",
          fatal(None) is True)
    check("R4b garbage reads as FATAL", fatal("nonsense") is True)

    # R5 — the name table
    missing = [o for o in range(1, 11) if o not in B_OUTCOME_NAMES]
    check("R5 the name table covers 1..10", not missing, f"missing {missing}")
    check("R5b outcome_name never returns a bare integer",
          "PLAYER_TELEPORTED" in outcome_name(5) and "<unreadable>" == outcome_name(None),
          f"outcome_name(5)={outcome_name(5)!r} outcome_name(None)={outcome_name(None)!r}")

    # ---------------------------------------------------------------------------------------
    # THE THREE CLASSES. ⭐ The checks that matter are the INVERSIONS: they are what a single
    # "safe outcomes" table would get wrong, and getting them wrong is an irreversible loss.
    # ---------------------------------------------------------------------------------------
    try:
        from modules.story.protected_encounters import (
            ANY_RETURN_KILLS_SAFE_OUTCOMES,
            FLIES_AWAY_SAFE_OUTCOMES,
            ROAMER_SAFE_OUTCOMES,
            outcome_is_safe_for as safe,
        )
    except Exception as error:  # noqa: BLE001
        check("C0 the three class tables import", False, repr(error))
        print("=" * 96)
        print(f"RESULT: FAIL — {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1

    # C1 — having three tables is only meaningful if they DIFFER
    check("C1 the three safe-sets are genuinely distinct",
          len({ROAMER_SAFE_OUTCOMES, FLIES_AWAY_SAFE_OUTCOMES, ANY_RETURN_KILLS_SAFE_OUTCOMES}) == 3,
          "if any two are equal, one table is redundant and the split is theatre")

    # C2 — ⭐ THE INVERSION ON `RAN` (4): verified on SkyPillar_Top vs BattleFrontier_OutsideEast
    check("C2 INVERSION: RAN(4) is SAFE for flies_away but FATAL for any_return_kills",
          safe("flies_away", 4) is True and safe("any_return_kills", 4) is False,
          f'flies_away={safe("flies_away", 4)} any_return_kills={safe("any_return_kills", 4)}')

    # C3 — ⭐ THE INVERSION ON `PLAYER_TELEPORTED` (5): fatal to a roamer, safe to a flies_away
    check("C3 INVERSION: PLAYER_TELEPORTED(5) is FATAL for roamer but SAFE for flies_away",
          safe("roamer", 5) is False and safe("flies_away", 5) is True,
          f'roamer={safe("roamer", 5)} flies_away={safe("flies_away", 5)}')

    # C4 — ⭐ THE FALL-THROUGH TRAP: MON_FLED is safe for a roamer and fatal for BOTH statics,
    #      because both scripts fall through to `setflag` for any outcome without an explicit branch.
    check("C4 FALL-THROUGH: MON_FLED(6) SAFE for roamer, FATAL for both statics",
          safe("roamer", 6) is True and safe("flies_away", 6) is False
          and safe("any_return_kills", 6) is False,
          f'roamer={safe("roamer", 6)} flies={safe("flies_away", 6)} any={safe("any_return_kills", 6)}')

    # C5 — the one universal escape
    check("C5 LOST(2) is safe for ALL THREE — a whiteout discards the script",
          all(safe(c, 2) for c in ("roamer", "flies_away", "any_return_kills")))

    # C6 — ⛔ NO DEFAULT CLASS. Every candidate default is wrong for one of the three.
    check("C6 an UNKNOWN class is unsafe, never a guess", safe("mystery", 4) is False)
    check("C6b an unreadable outcome is unsafe for every class",
          not any(safe(c, None) for c in ("roamer", "flies_away", "any_return_kills")))

    # C7 — losing on purpose really is the ONLY play against an unbeatable class-2B static
    check("C7 any_return_kills is safe ONLY on the two whiteout outcomes",
          ANY_RETURN_KILLS_SAFE_OUTCOMES == frozenset({2, 3}),
          f"got {sorted(ANY_RETURN_KILLS_SAFE_OUTCOMES)}")

    # ---------------------------------------------------------------------------------------
    # MEMBERSHIP. A species in the WRONG bucket is an irreversible loss; a species in TWO
    # buckets is a contradiction the guard would resolve arbitrarily.
    # ---------------------------------------------------------------------------------------
    try:
        from modules.story.protected_encounters import (
            REACHABLE_ANY_RETURN_KILLS,
            REACHABLE_FLIES_AWAY,
            UNREACHABLE_EVENT_ISLAND,
            UNVERIFIED_ANY_RETURN_KILLS,
            WEATHER_CAVE_SPECIES,
        )
    except Exception as error:  # noqa: BLE001
        check("M0 the membership tables import", False, repr(error))
        print("=" * 96)
        print(f"RESULT: FAIL — {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1

    flies = set(REACHABLE_FLIES_AWAY)
    kills = set(REACHABLE_ANY_RETURN_KILLS)

    # M1 — a species must not be in two classes at once
    check("M1 flies_away and any_return_kills are DISJOINT", not (flies & kills),
          f"both: {sorted(flies & kills)}")

    # M2 — ⭐ the moot-tier guard: no event-island species may appear in a REACHABLE table.
    #      If one ever does, someone has wired a guard for a battle that cannot occur — and,
    #      worse, may have imported the Hall-of-Fame "recoverable" reasoning with it.
    leaked = (flies | kills | set(UNVERIFIED_ANY_RETURN_KILLS)) & UNREACHABLE_EVENT_ISLAND
    check("M2 no EVENT-ISLAND species leaked into a reachable table", not leaked,
          f"leaked: {sorted(leaked)}")

    # M3 — the weather-cave species are a SUBSET of flies_away (they are legendaries that flee)
    check("M3 WEATHER_CAVE_SPECIES is a subset of REACHABLE_FLIES_AWAY",
          WEATHER_CAVE_SPECIES <= flies, f"stray: {sorted(WEATHER_CAVE_SPECIES - flies)}")

    # M4 — non-vacuity: the tables must not be empty, or every membership check above passes
    #      trivially while guarding nothing.
    check("M4 NON-VACUITY: every membership table has entries",
          bool(flies) and bool(kills) and bool(UNREACHABLE_EVENT_ISLAND),
          f"flies={len(flies)} kills={len(kills)} unreachable={len(UNREACHABLE_EVENT_ISLAND)}")

    # M5 — the verified exemplars must still be present and in the right bucket
    check("M5 the two VERIFIED exemplars are in their verified buckets",
          "RAYQUAZA" in flies and "SUDOWOODO" in kills,
          f"RAYQUAZA in flies={'RAYQUAZA' in flies} SUDOWOODO in kills={'SUDOWOODO' in kills}")

    print("=" * 96)
    if FAILURES:
        print(f"RESULT: FAIL — {len(FAILURES)} check(s): {', '.join(FAILURES)}")
        return 1
    print("RESULT: ALL PASS — parity, the three inversions, and the membership split all intact.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
