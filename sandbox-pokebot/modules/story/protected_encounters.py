"""Encounters a run can DESTROY by winning — and the outcome parity that decides it.

⛔⛔ WHY THIS MODULE EXISTS. Our bot fights to WIN. In Emerald, winning some battles permanently
forecloses a Pokédex entry: there is no reload, no respawn, and nothing in the battle strategy
knows it today. This module holds the VERIFIED game facts; it decides nothing about behaviour yet.

✅ EVERY FACT HERE WAS READ FROM `pret/pokeemerald@master` DIRECTLY, not taken from a report. The
working note with the verbatim source is
`PROJECT KNOWLEDGE/ai-research-notes/2026-09-25-roamer-outcome-table-VERIFIED.md`.

‼ NOTHING IMPORTS THIS YET, ON PURPOSE. It is pure and offline-testable; wiring a guard into move
selection is a separate change with its own evidence, because a guard that refuses the wrong battles
is its own bug.
"""

from __future__ import annotations

#: `include/constants/battle.h:100-110`. Kept as a table so a log line can NAME an outcome instead
#: of printing a bare integer — a number alone in a transcript is a fact nobody can act on.
B_OUTCOME_NAMES: dict[int, str] = {
    1: "WON",
    2: "LOST",
    3: "DREW",
    4: "RAN",
    5: "PLAYER_TELEPORTED",
    6: "MON_FLED",
    7: "CAUGHT",
    8: "NO_SAFARI_BALLS",
    9: "FORFEITED",
    10: "MON_TELEPORTED",
    128: "LINK_BATTLE_RAN",
}

#: `B_OUTCOME_WON`. The roamer test is BITWISE against this, so it is really a parity test.
B_OUTCOME_WON = 1

#: The ONLY exit a player can CHOOSE that does not deactivate a roamer.
B_OUTCOME_RAN = 4


def roamer_outcome_is_fatal(outcome: int | None) -> bool:
    """Does this battle outcome permanently deactivate a ROAMER (Latias/Latios)?

    ⭐ **THE RULE IS PARITY, NOT A LIST.** `src/battle_main.c` runs, in the VANILLA build:

        #ifndef BUGFIX
            if ((gBattleOutcome & B_OUTCOME_WON) || gBattleOutcome == B_OUTCOME_CAUGHT)
        #else
            ... == WON || == CAUGHT || == DREW
        #endif
                SetRoamerInactive();

    and `include/config.h:48` has **`//#define BUGFIX`** — commented out. So `#ifndef BUGFIX` is
    TRUE and **the BITWISE branch is live**. With `B_OUTCOME_WON == 1`, `outcome & 1` is simply
    *"is the outcome ODD?"*.

    ⇒ FATAL: `WON` 1, `DREW` 3, `PLAYER_TELEPORTED` 5, `CAUGHT` 7, `FORFEITED` 9.
    ⇒ SAFE:  `LOST` 2, **`RAN` 4**, `MON_FLED` 6, `NO_SAFARI_BALLS` 8, `MON_TELEPORTED` 10.

    ⛔⛔ **WRITE THE PROPERTY, NEVER THE ENUMERATION.** An earlier research pass listed
    WON/DREW/PLAYER_TELEPORTED and **missed `FORFEITED`** — a three-name list would have shipped a
    hole. `outcome & 1` is the expression the game itself evaluates; anything else is a paraphrase
    that can drift.

    ‼ THREE CONSEQUENCES WORTH STATING, because each contradicts an intuition:
    * **A MUTUAL KO IS FATAL** (`DREW`). So inspecting only the chosen move is not enough — recoil,
      Destiny Bond, Explosion and end-of-turn residual damage can all produce it.
    * **ROAR AND TELEPORT ARE FATAL** (`PLAYER_TELEPORTED`), and both read as harmless escapes. The
      decomp labels this a bug in its own comment; it is nonetheless what the retail ROM does.
      ⇒ the ONLY safe player-chosen exit is `RAN` (4), i.e. `run_away()`.
    * **LOSING IS SAFE** (`LOST` 2). Whiting out does NOT destroy the roamer.

    ⚠ SCOPE: this is the `BATTLE_TYPE_ROAMER` block ONLY. The scripted statics (Rayquaza, the three
    Regis, Groudon/Kyogre, Sudowoodo) are governed by their own map scripts and must NOT be assumed
    to follow this table.

    :param outcome: `gBattleOutcome` as read from memory. `None` means "not readable".
    :return: True if this outcome deactivates the roamer permanently.
    """
    if outcome is None:
        # ⛔ AN UNREADABLE OUTCOME IS NOT "SAFE". Returning False here would let a caller conclude
        # the encounter survived when it cannot know that. The conservative reading of "I could not
        # tell" is "assume the worst", because the loss being guarded against is IRREVERSIBLE.
        return True
    try:
        return bool(int(outcome) & B_OUTCOME_WON)
    except (TypeError, ValueError):
        # Same reasoning as above: a value we cannot interpret is not evidence of safety.
        return True


def outcome_name(outcome: int | None) -> str:
    """`5` -> `"PLAYER_TELEPORTED (5)"`. For logs — a bare integer is a fact nobody can act on."""
    if outcome is None:
        return "<unreadable>"
    try:
        value = int(outcome)
    except (TypeError, ValueError):
        return f"<uninterpretable {outcome!r}>"
    return f"{B_OUTCOME_NAMES.get(value, 'UNKNOWN')} ({value})"
