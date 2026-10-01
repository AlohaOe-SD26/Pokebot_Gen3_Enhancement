# 2026-09-30 — design v2 step 13 (KB-2, healing items in DOUBLE battles) GRADED: every behaviour prediction held (40 of 42 checks as filed; the 2 literal failures are wording slips in the predictions, both pass when corrected); the cursor fix and the identity guard are each shown load-bearing; the same grade on the commit that folds the gate's adversarial pass (2 production fixes, no gameplay change)

⛔ **THE CAVEAT IS THE HEADLINE.**
- This grades CORRECTNESS: in a double, an item now lands on the Pokémon that asked for it, judged by identity (PID),
  and the partner's turn survives it. It does NOT show that items change a fight's outcome (step 14's FREQUENCY
  question), and Tate & Liza's thin bag (one Potion) still makes that unlikely there.
- v1 is narrow by design: non-multi doubles, each battler heals only ITSELF, HP items only. The Space Center multi,
  partner heals and status cures are later items (design D1, D2, D10).
- Each family is ONE seeded trajectory, replayed (CLAUDE.md rule 8). The two OFF runs of each family were separated in
  time and matched each other (KI-112).

**Inputs:**
- Predictions: `2026-09-30-doubleitems13-PREDICTIONS.md`, committed `ab398449` BEFORE any production code.
- Build: `799e6adf`. Design: `2026-09-30-doubleitems13-DESIGN.md`.
- Evidence (`tools/story-dev/evidence/`): `2026-09-30-doubleitems13-STEP0.txt` (the base-code reads),
  `2026-09-30-doubleitems13-ARMS.txt` (the runner, every arm's battle-window lines, the hashes, the grade, the grader and
  runner, verbatim), `-ADVERSARIAL.txt` and `-FOLD.txt` (the gate's adversarial pass and its fold), and `-RERUN.txt` (the
  arms re-run on the folded commit `889b9319`, with the run-to-run comparison).

## THE RESULT, ARM BY ARM

**Family P — Route 123's first two-trainer double (`post_mtpyre.ss1`), the default policy, no lever.**

| # | Arm | Filed | Result |
|---|---|---|---|
| P1 | X-BASE ×2, P-OFF ×2 | all four `logsha 928db5621b3d2f7c`; no `DBLITEM` | ✅ all four identical, 371 lines; none |
| P2 | P-OBS | = P-OFF without `DBLITEM`; first would at f3149372, Sceptile, Hyper Potion; `bpo_pos = side`; `disc=1` | ✅ exactly; 26 rows, `bpo=120345` (= [1,2,0,3,4,5]) on every row, so the production dereference of `gBattleStruct` reads the true order |
| P3 | P-ON | = P-OFF before f3149372; the use, menu and after lines; the partner's FIGHT survives | ✅ `menu … slot=0 menu_pid=863B0917 ok=1 a_pressed=1`; `after … hp=21->117 … partner=Swellow#0B30A747 hp=18->18 Hyper Potion=1->0 healed=0->1`; Swellow's Wing Attack (f3149862, with byte 0 on BAG) and turn 1 ran; no KI-45 |
| P4 | P-KEY | `[KEYBATTLE] key=False`; no item; gameplay = P-OFF | ✅ `key=False allow=False reason=not_a_key_class` |
| P5 | P-CUR | the item lands; then KI-45 `never reached index 0 … (last read: 1)` | ✅ exactly ⇒ **the cursor fix (C1) is load-bearing** |
| P6 | P-SLOT | refused twice (`slot=1 menu_pid=Swellow ok=0 a_pressed=0`), nothing changes, then the disable | ✅ substance; ⚠ **FAILED AS FILED on one quoted line** (below) |
| P7 | P-NOG | A pressed on Swellow: Swellow 18→109, Sceptile 21→21, Hyper Potion 1→0 | ✅ exactly ⇒ **the guard is load-bearing**; and the old bag verdict then logs `✔ CONSUMED` with Sceptile at 15/117, blind to the wrong target |

**Family T — Tate & Liza (`d13_tateliza.ss1`), `KEYITEMS=1`, `HEAL_AT_FRACTION=0.8` in every arm.**

| # | Arm | Filed | Result |
|---|---|---|---|
| T1 | T-OFF ×2 | equal; = S0-RESUME through the battle | ✅ `f0fe5b25459a5596` ×2; identical to the base code through the battle |
| T2 | T-OBS | = T-OFF without `DBLITEM`; first would at f3456183, Mightyena, Potion, `key=1`; `disc` 1 on side 1 from turn 1, 0 on side 0 | ✅ exactly; `bpo=042315` (= [0,4,2,3,1,5], the faint swap carried as history) |
| T3 | T-ON | = T-OFF before f3456183; the use, menu (`slot=1`) and after lines; the next FIGHT; `[KEYBATTLE] key=True` | ✅ substance: `menu g=2 battler_in_menu=2 … slot=1 menu_pid=5C96EA9B ok=1 a_pressed=1`; `after … hp=99->119 … partner=Sceptile#863B0917 hp=116->116 Potion=1->0`; Mightyena's Bite next turn (byte 2 on BAG) ran; ⚠ **FAILED AS FILED on its first clause** (below) |

## THE TWO LITERAL FAILURES, AND WHY NEITHER IS THE CODE'S

- **P6:** the prediction quoted the disable line as `not consumed twice; disabling items`. The code prints `the item was
  NOT consumed twice; disabling items for the rest of this battle` (capitals; the builder flagged the wording before the
  arms ran). The behaviour it names (a second refusal, then the disable, f3150014) happened.
- **T3:** the row says "= T-OFF before f3456183" under the filed rule "every frame-stamped line identical", and the SAME
  row predicts a `[KEYBATTLE] … key=True` line. That line is logged at the battle's first decision (f3453544): the flag-1
  path calls the key gate, the flag-unset path never does. So the row contradicted itself. Every OTHER line before
  f3456183 is identical.
- Both are recorded as FAILED AS FILED in the grade; the corrected checks (named as such) pass.

## WHAT THIS SHOWS AND WHAT IT DOES NOT

- **Shows:** both index spaces are right in a live double for BOTH battlers (the right battler's party index 4 at menu
  slot 1, the left battler's party index 1 at menu slot 0, read off the cursor's own slot and PID); an item never reached
  another Pokémon; the partner's same-turn and next-turn actions survive an item; the flag-unset build is the base code
  on both trajectories; and the key gate composes (a non-key double gets no item, Tate & Liza does).
- **Does not show:** anything about win rates; the multi; status cures; partner heals; a heal chosen at the default 0.35
  at Tate & Liza (the arms used 0.8: at 0.35 the fixture's one Potion loses rule 3's race).

## THE ADVERSARIAL PASS ON THE GATE, ITS FOLD, AND THE ARMS RE-RUN ON `889b9319`

- **The pass** (`evidence/2026-09-30-doubleitems13-ADVERSARIAL.txt`; two mutant hunters and a defect hunter, none of
  whom built the gate): 144 new mutants, 41 real gate gaps, and NO blocker in the code. The most important gap: no row
  proved the guard reads the PID at the cursor's ACTUAL slot (DQ14's scroll stopped on Cancel, so its range check refused
  first); a guard reading the PID at the aimed slot survived, and live it would hand battler 2's item to its partner.
- **Two production defects, both FIXED** (`-FOLD.txt`; each fix's rows are red on the literal `799e6adf` files and green
  on `889b9319`):
  - SF-1: a double still asked the cure policy with a Full Restore in its list, so a sleeping Pokémon would spend the
    scarcest item where singles uses a Full Heal. A double now asks NO cure policy (D10 as intended).
  - SF-2: the doubles bag-open budget had a 16-frame margin (P-ON: the bag opened 74 frames into a 90-frame budget). A
    flag-on double now re-presses only while the battler's action menu is up, then waits up to 150 frames without
    pressing. The re-run shows why the first A timed out: it was DROPPED (the menu was still up after it).
  - Plus N2: the flag-unset path tests the env before importing anything.
- **The gate after the fold:** 91 rows, 3 faults whose red sets are still exactly the pre-registered ones, 124 mutants
  (3 of them run under a fault, which the first runner could not see).
- **The arms re-run on `889b9319`** (`-RERUN.txt`): the SAME grade (42 checks; the same 2 FAILED AS FILED, both
  wording slips). 7 of the 12 logs are byte-identical to `799e6adf`'s (every flag-unset and observe arm); the 5 acting
  arms differ ONLY in their `[ITEM-FLOW]` bag-open lines (SF-2's rewording and the presses it no longer makes), and every
  other line, frames included, is identical. ⇒ the fold changed no gameplay on these trajectories.
- **Residuals, recorded:** singles keeps the old 3 × 30 bag-open loop (not measured failing; one singles sample opened
  in 43 frames); the bag-count verdict is per item type, not per requester (reachable only through a failed bag-open);
  item names keep their spaces in the `use` / `after` lines; a bag-did-not-open return logs no `menu` / `after` pair.
