# 2026-09-26 — `#26-ch24organic` R1 (THE READINESS REFUSAL) — PRE-REGISTERED PREDICTIONS (written BEFORE any drive)

> R1 = `prepare_and_open_the_league` now RAISES `§Ch24 R1: REFUSING to enter the Elite Four …` when, after
> training, any party member is below `floor` or the League basket (`LEAGUE_BASKET`) is short — BEFORE
> "GET INSIDE", i.e. before a guard is talked to. The decision is the pure `ch24_readiness_shortfall()`.
> Built on branch `wt/ch24organic` (the user's batch `#26-batch0926` freezes `sandbox-pokebot/` on `main`).
> Driver: `--driver ch24entry` with the new `CH24_ENTRY_EXPECT=refuse:<floor|basket>` grade.
> New production fault arms: `POKEBOT_CH24_FAULT_NOTRAIN=1` (skip training — lets R1 be driven at the
> production floor in minutes), `POKEBOT_CH24_FAULT_NOREADY=1` (skip-the-fix: R1 disarmed).

## THE DISCRIMINATOR, COMPUTED ON THE NAMED FIXTURES BEFORE THE DRIVE (observe-only probe `probe_ch24_readiness_inputs.py`)

| fixture (md5) | position | `below` at the arm's floor | basket (HP/FR/FH/Rev vs 30/3/8/3) | `ENTERED_ELITE_FOUR` |
|---|---|---|---|---|
| `post_league_shop.ss1` (`1564948368f6`) | EVER_GRANDE_CITY (18,6) | floor 65 → **6**: Zigzagoon L19, Castform L36, Wailord L47, Swellow L48, Mightyena L48, Sceptile L53 · floor 19 → **0** | 30/3/8/3 — **exact, not short** | False (driver premise asserts it) |
| `post_ever_grande.ss1` (`18203e997edc`) | EVER_GRANDE_CITY (18,42) | floor 1 → **0** | **0/0/0/0 — short on all four** | False |

⇒ the arms differ in exactly the input R1 reads: A/B vs C differ ONLY in `floor` (6 below vs 0 below, same
basket, same fixture); D isolates the basket conjunct (0 below, empty basket).

## PREDICTIONS

| arm | fixture · env | prediction | falsifier |
|---|---|---|---|
| **A** REFUSE-FLOOR | `post_league_shop` · floor 65 (production default) · `NOTRAIN=1` · `EXPECT=refuse:floor` | `ACCEPTANCE: PASS`. failure = `§Ch24 R1: REFUSING to enter the Elite Four at …EVER_GRANDE_CITY…(18, 6) — 6 mōn below the L65 floor: Zigzagoon#33CB74C3 L19, Castform#C978D14E L36, …` with **no** basket reason; `E1-LATCHED` taken, `E1-READY`/`E1-INSIDE` absent; `flag_final=False`; `final_at` EVER_GRANDE_CITY (18,6); the train sub-report shows `fault_notrain=True`; 0 whiteouts; a few thousand frames at most | no raise (R1 not wired); a raise for a different reason; the flag True; any `E1-INSIDE` |
| **B** SKIP-THE-FIX | A + `POKEBOT_CH24_FAULT_NOREADY=1` | `ACCEPTANCE: FAIL` with conjuncts `raised_R1=False`, `door_still_shut=False`, `never_inside=False` — and the leg's own readings show **`E1-GUARDS` and `E1-AT-DOOR` TAKEN**: with R1 disarmed the bot talks the guards aside and stands at the open door with all six below L65 ⇒ **R1 is what stops it** | B passes (R1 not load-bearing), or B fails BEFORE the door for an unrelated reason (then the arm shows nothing — inconclusive, not a confirmation) |
| **C** CONTROL | `post_league_shop` · floor 19 · `EXPECT=enter` | `ACCEPTANCE: PASS` — all five `E1-*` readings + `T-PREMISE` + `T-CONTINUE`, `readiness_refusal=[]`, `E1-READY` taken ⇒ R1 does NOT fire on a party that meets the floor with a full basket | any R1 raise; any missing reading |
| **D** REFUSE-BASKET | `post_ever_grande` · floor 1 · `EXPECT=refuse:basket` (no NOTRAIN — nothing is below floor 1, so training self-skips) | `ACCEPTANCE: PASS`; exactly ONE reason: `League basket short: Hyper Potion 0/30, Full Restore 0/3, Full Heal 0/8, Revive 0/3`; refused at EVER_GRANDE_CITY (18,42); `flag_final=False` | a level reason appears; no raise; a raise elsewhere |

**G (static gate, `probe_ch24_readiness.py`):** the pure decision on synthetic inputs (empty/short/exact/
extra items; below list named by PID); the R1 raise sits BEFORE the leg's first move toward the door and
BEFORE the guard talk (AST order); the R1 block contains **no `yield`** (so the ordinary trajectory is
unchanged by construction — no frames are added); both new arms are read in production and registered.
Fault arms of the gate itself: a decision that ignores the basket must FAIL, and an R1 moved below the
door walk must FAIL.

## WHAT THIS WILL NOT SETTLE
* Whether organic parties REACH R1 on Ever Grande at all: the return bridge (gap 2), Fly teach (gap 3) and
  the no-Fly plateau walk-off (gap 4) are separate items. Today a party trained off the north plateau
  never gets back to (18,6); R1 only guarantees the gauntlet is never STARTED under-levelled.
* ⚠ POLICY, flagged to the user: at the production floor R1 would refuse the very party that WON the
  gauntlet (`post_ch24_atdoor_L75`: 4×L75 + Zigzagoon L19 + Castform L36) if training could not lift the
  two stragglers. That is USER RULING 12's floor applied literally; relaxing it is the user's call.
