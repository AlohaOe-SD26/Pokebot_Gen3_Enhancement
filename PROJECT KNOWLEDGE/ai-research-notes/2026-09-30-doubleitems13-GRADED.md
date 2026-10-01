# 2026-09-30 — design v2 step 13 (KB-2, healing items in DOUBLE battles) GRADED: every behaviour prediction held (as filed, 38 of 40 checks; the 2 failures are wording slips in the predictions, and their 2 corrected checks pass); the cursor fix and the identity guard are each shown load-bearing; the same grade on the commit that folds the gate's adversarial pass (3 fixes; no gameplay change on these two trajectories, whose paths the fixes never reached)

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
- Build: `799e6adf`; fold `889b9319`. Design: `2026-09-30-doubleitems13-DESIGN.md`.
- Evidence (`tools/story-dev/evidence/`):
  - `2026-09-30-doubleitems13-STEP0.txt` (the base-code reads);
  - `-ARMS.txt` (the arms on `799e6adf`) and `-RERUN.txt` (the arms on `889b9319`, with the run-to-run comparison):
    the runner, every arm's battle-window lines, the hashes, the grade, the grader and runner, verbatim. Both were
    REGENERATED after the build review (F2, F5) with the fixed grader; no run was repeated;
  - `-ADVERSARIAL.txt` and `-FOLD.txt` (the gate's adversarial pass and its fold);
  - `-REVIEW.txt` (the build's three-lens review) and `-REVIEW-FIX.txt` (its code fixes and their proof).
- **Grading method:** HP and bag values come only from the `[DBLITEM] after` lines. P3's and T3's `healed=+1` were graded
  SEMANTICALLY (the code prints `healed=0->1`, as the builder flagged before the arms ran: the check is `after = before
  + 1`), while P6's quoted line was graded literally first; both treatments are disclosed (review F6).

## THE RESULT, ARM BY ARM

**Family P — Route 123's first two-trainer double (`post_mtpyre.ss1`), the default policy, no lever.**

| # | Arm | Filed | Result |
|---|---|---|---|
| P1 | X-BASE ×2, P-OFF ×2 | all four `logsha 928db5621b3d2f7c`; no `DBLITEM` | ✅ all four identical (371 frame-stamped lines); none |
| P2 | P-OBS | = P-OFF without `DBLITEM`; first would at f3149372, Sceptile, Hyper Potion; `bpo_pos = side`; `disc=1` | ✅ exactly. 26 OBS rows in the run, `bpo_pos = side` on every one. `bpo=120345` (= [1,2,0,3,4,5]) on the first double's 12 rows and the second double's first 3, then `420315` after the second double's faint swap (6 rows), and `240135` in the third double (5 rows) (review F3); so the production dereference of `gBattleStruct` reads the true order as it changes |
| P3 | P-ON | = P-OFF before f3149372; the use, menu and after lines; the partner's FIGHT survives | ✅ `menu … slot=0 menu_pid=863B0917 ok=1 a_pressed=1`; `after … hp=21->117 … partner=Swellow#0B30A747 hp=18->18 Hyper Potion=1->0 healed=0->1`; Swellow's Wing Attack (f3149862, with byte 0 on BAG) and turn 1 ran; no KI-45 |
| P4 | P-KEY | `[KEYBATTLE] key=False`; no item; gameplay = P-OFF | ✅ `key=False allow=False reason=not_a_key_class` |
| P5 | P-CUR | the item lands; then KI-45 `never reached index 0 … (last read: 1)` | ✅ exactly ⇒ **the cursor fix (C1) is load-bearing** |
| P6 | P-SLOT | refused twice (`slot=1 menu_pid=Swellow ok=0 a_pressed=0`), nothing changes, then the disable | ✅ substance; ⚠ **FAILED AS FILED on one quoted line** (below) |
| P7 | P-NOG | A pressed on Swellow: Swellow 18→109, Sceptile 21→21, Hyper Potion 1→0 | ✅ exactly ⇒ **the guard is load-bearing**; and the old bag verdict then logs `✔ CONSUMED` with Sceptile at 15/117, blind to the wrong target |

**Family T — Tate & Liza (`d13_tateliza.ss1`), `KEYITEMS=1`, `HEAL_AT_FRACTION=0.8` in every arm.**

| # | Arm | Filed | Result |
|---|---|---|---|
| T1 | T-OFF ×2 | equal; = S0-RESUME through the battle | ✅ `f0fe5b25459a5596` ×2; identical to the base code inside the battle window f3452776-f3464107. ⚠ Disclosed (review F7): S0-RESUME ran with `KEYITEMS` unset and the default fraction, and only the battle window was compared, as filed (both settings are inert there: a flag-unset double never reaches the item policy) |
| T2 | T-OBS | = T-OFF without `DBLITEM`; first would at f3456183, Mightyena, Potion, `key=1`; `disc` 1 on side 1 from turn 1, 0 on side 0 | ✅ exactly; `bpo=042315` (= [0,4,2,3,1,5], the faint swap carried as history) |
| T3 | T-ON | = T-OFF before f3456183; the use, menu (`slot=1`) and after lines; the next FIGHT; `[KEYBATTLE] key=True` | ✅ substance: `menu g=2 battler_in_menu=2 … slot=1 menu_pid=5C96EA9B ok=1 a_pressed=1`; `after … hp=99->119 … partner=Sceptile#863B0917 hp=116->116 Potion=1->0`; Mightyena's next decision was a FIGHT (Bite, f3458022, its cursor left on BAG by the item) with no KI-45 (this check now EVALUATES; it was the constant True before review F5); ⚠ **FAILED AS FILED on its first clause** (below) |

## THE TWO LITERAL FAILURES, AND WHY NEITHER IS THE CODE'S

- **P6:** the prediction quoted the disable line as `not consumed twice; disabling items`. The code prints `the item was
  NOT consumed twice; disabling items for the rest of this battle` (capitals; the builder flagged the wording before the
  arms ran). The behaviour it names (a second refusal, then the disable, f3150014) happened.
- **T3:** the row says "= T-OFF before f3456183" under the filed rule "every frame-stamped line identical", and the SAME
  row predicts a `[KEYBATTLE] … key=True` line. That line is logged at the battle's first decision (f3453544): the flag-1
  path calls the key gate, the flag-unset path never does. So the row contradicted itself. Every OTHER line before
  f3456183 is identical.
- **The count:** as filed, 40 checks, 38 PASS, 2 FAIL (these two); the 2 corrected checks, named as such, both PASS.

## WHAT THIS SHOWS AND WHAT IT DOES NOT

- **Shows:** both index spaces are right in a live double for BOTH battlers (the right battler's party index 4 at menu
  slot 1, the left battler's party index 1 at menu slot 0, read off the cursor's own slot and PID); an item never reached
  another Pokémon; the partner's same-turn and next-turn actions survive an item; the flag-unset build is the base code
  on both trajectories; and the key gate composes (a non-key double gets no item, Tate & Liza does).
- **Does not show:** anything about win rates; the multi; status cures; partner heals; a heal chosen at the default 0.35
  at Tate & Liza (the arms used 0.8: at 0.35 the fixture's one Potion loses rule 3's race).
- **Not measured: WHY battler 0's first A of a doubles turn is dropped** (review G1). P-ON shows that it is (the action
  menu was still up after it), and two cursor presses in the same window were lost too. The design's Step-0 explanation
  ("the Fight menu opens later than the 6-frame wait") is probably the same dropped-input effect. The decomp offers a
  candidate (the opponent's AI choosing in the same pass as battler 0), INFERRED only. SF-2 makes the bag flow robust to
  it either way.

## THE ADVERSARIAL PASS ON THE GATE, ITS FOLD, AND THE ARMS RE-RUN ON `889b9319`

- **The pass** (`evidence/2026-09-30-doubleitems13-ADVERSARIAL.txt`; two mutant hunters and a defect hunter, none of
  whom built the gate): 144 new mutants, 41 real gate gaps, and NO blocker in the code. The most important gap: no row
  proved the guard reads the PID at the cursor's ACTUAL slot (DQ14's scroll stopped on Cancel, so its range check refused
  first); a guard reading the PID at the aimed slot survived, and live it would hand battler 2's item to its partner.
- **Three fixes** (`-FOLD.txt`: two defects and a nit; each fix's rows are red on the literal `799e6adf` files and green
  on `889b9319`):
  - SF-1 (defect): a double still asked the cure policy with a Full Restore in its list, so a sleeping Pokémon would
    spend the scarcest item where singles uses a Full Heal. A double now asks NO cure policy (D10 as intended).
  - SF-2 (defect): the doubles bag-open budget had a 16-frame margin (P-ON: the bag opened 74 frames into a 90-frame
    budget). A flag-on double now re-presses only while the battler's action menu is up, then waits up to 150 frames
    without pressing.
  - N2 (nit): the flag-unset path tests the env before importing anything.
- **The gate after the fold:** 91 rows, 3 faults whose red sets are still exactly the pre-registered ones, 124 mutants
  (3 of them run under a fault, which the first runner could not see).
- **The arms re-run on `889b9319`** (`-RERUN.txt`): the SAME grade (as filed, 38 of 40; the same 2 FAILED AS FILED).
  7 of the 12 logs are identical to `799e6adf`'s on every frame-stamped line except `[PARTY-ACCT]` (review F8): the four
  flag-unset arms, the two observe arms and P-KEY (flag 1 in a non-key double, so no item). The 5 acting arms differ ONLY
  in their `[ITEM-FLOW]` bag-open lines (SF-2's rewording and the presses it no longer makes); every other line, frames
  included, is identical. ⇒ **no gameplay change on these two trajectories**: they never reached SF-1's path (no status
  at a decision) or SF-2's (no bag took more than 90 frames). The fixes DO change behaviour where those paths are reached
  (review F4).
- **Residuals, recorded:** singles keeps the old 3 × 30 bag-open loop (not measured failing; one singles sample opened
  in 43 frames); the bag-count verdict is per item type, not per requester (reachable only through a failed bag-open);
  item names keep their spaces in the `use` / `after` lines; a bag-did-not-open return logs no `menu` / `after` pair.

## THE BUILD'S THREE-LENS REVIEW (`evidence/2026-09-30-doubleitems13-REVIEW.txt`; every blocker/should-fix to a refuter)

- **No production defect.** Production and mechanics lenses: nits only, folded (`-REVIEW-FIX.txt`):
  - N1: observe now uses a SILENT reserve filter (the real one could log `[RESERVE]` and set its warn latch in the
    League-reserve era);
  - N3: SF-2's after-acceptance give-up logs its own stage (the generic "will re-decide" line was wrong there);
  - G2: the gate's fake no longer re-opens a battler's action menu after a successful medicine;
  - N2/F13: C1's "inert with the flag unset" is SCOPED: it holds for Story's strategies (their trainer doubles only
    FIGHT). Under upstream's `DefaultBattleStrategy` with the `rotate` config, a RotateLead by battler 0 leaves byte 0 =
    2, and there C1 changes flag-unset presses: it turns a latent KI-45 into a working FIGHT. A fix there, not a no-op.
- **The grade lens, five should-fix, all upheld and FIXED in the docs and the grader:** F1 (the queue head said "no
  production code" and "BUILT" in one sentence), F2 (the as-filed count), F3 (the `bpo` claim), F4 (the headline's
  scope), F5 (the vacuous next-FIGHT check). Nits F6-F12 and G1 folded: the disclosures above; the registry row (F10);
  the handoff's stamp (F11); the two must-stay-green repros outside the suite re-run on the final code (F12,
  `-REVIEW-FIX.txt`).
