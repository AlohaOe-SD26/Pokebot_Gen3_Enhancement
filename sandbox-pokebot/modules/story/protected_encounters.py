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
    * **OUR OWN TELEPORT IS FATAL** (`PLAYER_TELEPORTED`, 5) — and the decomp's comment gets the
      ACTOR BACKWARDS. `battle_main.c` says *"when Roar is used by a ROAMER"*, but the setter is
      `VARIOUS_SET_TELEPORT_OUTCOME`, which branches on `GetBattlerSide(gActiveBattler)`, and its
      only caller is `BattleScript_EffectTeleport` ending in **`setoutcomeonteleport BS_ATTACKER`**.
      ⇒ the side is the side of the mon that USED the move: **ours teleporting = 5 = FATAL; theirs
      teleporting = `MON_TELEPORTED` (10) = SAFE.** A reader trusting the comment over the code
      concludes our own Teleport is harmless. VERIFIED 2026-09-25 by reading both.
      ⚠ **ROAR IS UNVERIFIED AND BANNED ANYWAY.** `BattleScript_EffectRoar` does NOT call
      `setoutcomeonteleport`; it uses `forcerandomswitch`, whose wild-battle path I did not read to
      the end. The ban costs nothing; claiming it verified would be the error.
      ⇒ the ONLY safe player-chosen exit is `RAN` (4), i.e. `run_away()`.
    * **LOSING IS SAFE** (`LOST` 2). Whiting out does NOT destroy the roamer.

    ⛔⛔ SCOPE — AND THERE ARE **THREE CLASSES WITH DIFFERENT, PARTLY OPPOSITE SAFE SETS.** This
    function covers CLASS 1 ONLY. A single global "safe outcomes" constant WILL destroy something.
    *(Classes 2A/2B below are agent-reported from a 12-agent recon and NOT yet verified by me —
    they are recorded so nobody builds a one-size guard, not as facts to code against.)*

      CLASS 1  ROAMER (this function): safe = {LOST 2, RAN 4, MON_FLED 6, MON_TELEPORTED 10}.
      CLASS 2A SCRIPTED LEGENDARIES that "fly away" — Rayquaza, the three Regis, Groudon, Kyogre,
               Southern-Island Lati, Lugia, Ho-Oh, Deoxys, Mew. ⚠ **RAN *and* PLAYER_TELEPORTED are
               SAFE here** (they respawn) — the OPPOSITE of class 1 for outcome 5.
               ⭐ And a KO is only EXPENSIVE, not fatal, for Mew / Deoxys / Lugia / Ho-Oh /
               Southern-Island Lati: the Hall of Fame clears their DEFEATED flags on EVERY Elite
               Four re-clear. PERMANENT on a KO: Rayquaza, the Regis, Groudon, Kyogre.
      CLASS 2B STATICS where ANY return kills it — Sudowoodo, the three New Mauville Voltorb,
               the Route 120 Kecleon. ⛔ **FLEEING IS FATAL HERE.** Only LOST (2) and DREW (3) are
               safe, i.e. **the correct play against an unbeatable class-2B static is to LOSE ON
               PURPOSE** — the whiteout discards the script before any flag is written.
               ‼ AND IT IS INVISIBLE TO `gBattleTypeFlags`, which is literally 0 — byte-identical
               to an ordinary patch of grass. Species/map, never battle flags.

    :param outcome: `gBattleOutcome` as read from memory. `None` means "not readable".
    :return: True if this outcome deactivates the roamer permanently.
    """
    # ⛔ AN UNREADABLE OUTCOME IS NOT "SAFE". Reporting False here would let a caller conclude the
    # encounter survived when it cannot know that. The conservative reading of "I could not tell"
    # is "assume the worst", because the loss being guarded against is IRREVERSIBLE.
    # ‼ ASKED WITH `isinstance`, NOT `try/int()/except`: this is a TYPE question, and answering it
    # by exception would also swallow a genuine caller bug (an object with a broken `__int__`) into
    # the same branch as "the value was None". `bool` is excluded deliberately — `True & 1` is 1,
    # so a stray boolean would read as a FATAL outcome rather than as unreadable.
    if not isinstance(outcome, int) or isinstance(outcome, bool):
        return True
    return bool(outcome & B_OUTCOME_WON)


def outcome_name(outcome: int | None) -> str:
    """`5` -> `"PLAYER_TELEPORTED (5)"`. For logs — a bare integer is a fact nobody can act on."""
    if outcome is None:
        return "<unreadable>"
    if not isinstance(outcome, int) or isinstance(outcome, bool):
        return f"<uninterpretable {outcome!r}>"
    return f"{B_OUTCOME_NAMES.get(outcome, 'UNKNOWN')} ({outcome})"
