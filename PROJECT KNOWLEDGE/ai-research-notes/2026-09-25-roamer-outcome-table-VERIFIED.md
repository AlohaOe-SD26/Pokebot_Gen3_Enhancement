# WHICH BATTLE OUTCOMES DESTROY A ROAMER — verified from the decomp, by me

**Date:** 2026-09-25. **Status:** ✅ **VERIFIED BY ME**, not agent-reported. Every line below was
read directly from `pret/pokeemerald@master`. This is the foundation for the never-KO guard.

---

## THE CODE, VERBATIM (`src/battle_main.c`, the `BATTLE_TYPE_ROAMER` block)

```c
    if (gBattleTypeFlags & BATTLE_TYPE_ROAMER)
    {
        UpdateRoamerHPStatus(&gEnemyParty[0]);

#ifndef BUGFIX
        // Bug: When Roar is used by a roamer, gBattleOutcome is B_OUTCOME_PLAYER_TELEPORTED (5),
        // which deactivates the roamer.
        if ((gBattleOutcome & B_OUTCOME_WON) || gBattleOutcome == B_OUTCOME_CAUGHT)
#else
        if ((gBattleOutcome == B_OUTCOME_WON) || gBattleOutcome == B_OUTCOME_CAUGHT ||
            gBattleOutcome == B_OUTCOME_DREW)
#endif
            SetRoamerInactive();
    }
```

⛔⛔ **IT IS `#ifndef`, NOT `#ifdef` — READ IT TWICE.** I misread this on first glance and drew the
opposite conclusion. `include/config.h:48` has **`//#define BUGFIX`** — commented out — so `BUGFIX`
is **NOT** defined, `#ifndef BUGFIX` is TRUE, and **the BITWISE branch is the live one.**
‼ The decomp's own comment names the consequence: a roamer using **Roar** yields outcome 5, which
deactivates it. That is acknowledged vanilla behaviour, not a decomp artefact.

## THE VALUES (`include/constants/battle.h:100-110`)

```
B_OUTCOME_WON 1   LOST 2   DREW 3   RAN 4   PLAYER_TELEPORTED 5
MON_FLED 6        CAUGHT 7          NO_SAFARI_BALLS 8          FORFEITED 9   MON_TELEPORTED 10
```

## ⇒ THE TABLE. `B_OUTCOME_WON == 1`, so `outcome & B_OUTCOME_WON` is simply **"is it ODD?"**

| outcome | value | odd? | roamer destroyed |
|---|---|---|---|
| `WON` | 1 | ✔ | **YES** |
| `LOST` | 2 | ✘ | no |
| `DREW` | 3 | ✔ | **YES** — a mutual KO counts |
| **`RAN`** | **4** | ✘ | **NO — the only safe player-CHOSEN exit** |
| `PLAYER_TELEPORTED` | 5 | ✔ | **YES** — Roar/Teleport, the documented bug |
| `MON_FLED` | 6 | ✘ | no — the roamer fleeing on its own is fine |
| `CAUGHT` | 7 | ✔ | yes (also matched explicitly) — but this is the GOAL |
| `NO_SAFARI_BALLS` | 8 | ✘ | no |
| **`FORFEITED`** | **9** | ✔ | **YES** |
| `MON_TELEPORTED` | 10 | ✘ | no |

## ⛔ THE ONE THE EARLIER AGENT MISSED

It listed WON / DREW / PLAYER_TELEPORTED. **`FORFEITED` (9) is also odd and therefore also fatal.**
⇒ *"the odd ones"* is the rule; an enumerated list of three is not, and would have left a hole.
‼ **Prefer the PROPERTY to the enumeration**: a guard written as `outcome in (1, 3, 5)` is wrong
today and would rot; `outcome & 1` is the code the game actually runs.

## ⇒ WHAT THIS MEANS FOR THE GUARD

1. **The only safe player-chosen exit from a roamer battle is `RAN` (4)** — i.e. `run_away()`.
   Roar, Teleport and forfeiting are all fatal, and all three *read* as harmless escapes.
2. **A mutual KO is fatal** (`DREW`), so a guard that only inspects the chosen move is insufficient:
   recoil, Destiny Bond, Explosion and end-of-turn residual damage can all produce it.
3. **Losing is safe** (`LOST`, 2). Counter-intuitive, and worth stating: whiting out does not
   destroy the roamer.
4. The rule to encode is **the parity**, not a list of names.

⚠ **SCOPE: this block is `BATTLE_TYPE_ROAMER` ONLY.** The scripted statics (Rayquaza, the Regis,
Groudon/Kyogre, Sudowoodo) are governed by their own map scripts, NOT by this code. Their rules are
a separate question and must not be assumed to follow this table.
