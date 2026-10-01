# 2026-10-01 — design v2 step 14 (the Phase 3 batch A/B): recon angle `stats`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `step14-batch-recon`). Every load-bearing claim is verified by the author before the design relies on it.

**NOTE: v2 Step 14, statistical power (read-only; this is a NOTE, not truth)**

**Headline (the caveat).** One 12-14 h batch split into 2 lanes per arm (D1) can detect only large differences. Under D1, per-group key-battle win rates and ordinary whiteouts are **descriptive only**. The Elite Four cannot be assessed in either design. D1 also cannot run today without a launcher change, and its arms would be confounded with the starter.

**Method.** The batch0926/0927 logs predate `[TRAINER]`. The rebuilt probes, run read-only, confirm this: 40 logs, 43,380 battles, all UNCLASSIFIED; 114 `[ITEM] using` / 111 consumed / 3 cures; 129,980 turn records and 4,788 `vs ?`. So I classified key battles offline:
- **Party match:** the foe's (species, level) set from `[TURN]` lines had to be a subset of a key trainer's party in the decomp (`pret/pokeemerald` `trainers.h` + `trainer_parties.h`, 854 trainers), and of no non-key party.
- **Leaders and Elite Four:** the battle also had to be in that trainer's room.
- **Other key trainers:** at least 2 foes seen, or a 1-mon party, or a loss showing only the lead. Never on RanAway, Teleported or Caught (wild-only outcomes).
- **Cross-checks against the FINAL notes:**
  - key + ordinary losses (Draw counted as lost) = 1,121 for batch0926 (FINAL :32 says 1,121) and 768 for batch0927 (FINAL :303-308: 769 recoveries, 1 of them a field whiteout with no loss);
  - Tate & Liza has 3 Draws;
  - Wally-in-Victory-Road pairs (16 / 12) equal the runs that loaded Victory Road;
  - "not eventually won" matches the FINAL honest stops (Juan 3, Winona 1, T&L 2 + 1 in progress).
- The classification itself is INFERRED; the totals above are VERIFIED.

### 1. What one batch produces
Baselines: batch0926 is 62.8 lane-h and 38 runs (FINAL :21, :30). batch0927 is 56.5 lane-h and 35 runs (FINAL :251, :72). That is 0.605-0.619 runs per lane-hour.

| group | battles/lane-h | (run, trainer) pairs/lane-h | 12-14 h × 4 lanes (48-56 lane-h): battles / pairs |
|---|---|---|---|
| leaders | 13.2-16.9 | 3.75-4.09 | 635-945 / 180-229 |
| rivals | 3.98-4.28 | 3.03-3.11 | 191-240 / 145-174 |
| Magma/Aqua | 4.21-5.22 | 3.22-3.85 | 202-292 / 155-216 |
| Elite Four | 0-0.035 | 0-0.035 | 0-2 / 0-2 |

- **Runs per batch:** 29-35. The D1 arm gets about 16 runs; each D2 arm gets about 32.
- **⚠ Discrepancy:** `2026-09-26-rulings19-20-PLAN.md:71-73` says "~50 runs per arm per 12h×4 lanes". The measured figure is about 29-35 runs for the WHOLE batch. My reading of that line is INFERRED.

### 2. Baselines (batch0926 / batch0927, VERIFIED counts, INFERRED classification)
- **Leaders:** won/(won+lost) .227 / .265; first-attempt win .385 / .448; eventually won .938 / .934.
  - First-attempt win per leader: Roxanne .89/.94, Brawly .81/.69, Wattson .17/.13, Flannery .46/.47, Norman .09/.22, Winona .03/.05, Tate & Liza .12/.26, Juan .27/.50.
- **Rivals:** won/(won+lost) .725 / .756; first-attempt win .856 / .836.
- **Magma/Aqua:** won/(won+lost) .738 / .765; first-attempt win .855 / .841.
- **Elite Four:** 0 battles / 2 battles (Sidney won, Phoebe lost).
- **Arm A already uses items in key battles:** 110 uses in 76 of 1,657 key battles (batch0926), and 26 in 19 of 1,212 (batch0927).
- **A-N5 re-derived:** batch0927 has 70 ordinary uses in 49 battles plus 26 key uses in 19 battles, total 96. The v2 note's "67 in 47" (`DESIGN-v2.md:703`) is 3 short. Of those ordinary item battles, 48 of 49 (and 64 of 67 in batch0926) were won.

### 3. Detectable differences
Method: resample runs (the cluster unit) for each arm under the null, 4,000 draws per baseline batch.
- MDD = 2.80 × SD (two-sided α = .05, 80% power).
- NI = 2.49 × SD: the smallest "not lower by more than δ" margin a batch can support when the arms are truly equal.

| metric | D1 MDD (16 runs/arm) | D2 MDD (32 runs/arm) | NI margin D1 / D2 |
|---|---|---|---|
| leaders won/(won+lost) | .10-.15 | .07-.10 | .09-.13 / .06-.09 |
| leaders first-attempt win | .16-.17 | .11-.12 | .14-.15 / .10 |
| leaders eventually won | .08 | .05-.06 | .07 / .05 |
| rivals won/(won+lost) | .26 | .19 | .23 / .17 |
| rivals first-attempt win | .09-.12 | .07-.08 | .08-.10 / .06-.07 |
| Magma/Aqua won/(won+lost) | .23-.26 | .16-.19 | .20-.23 / .14-.17 |
| Magma/Aqua first-attempt win | .09-.13 | .06-.09 | .08-.12 / .05-.08 |
| single boss, first-attempt win | T&L .41-.61, Winona .20-.30, Norman .31-.47, Juan .60-.77 | ×0.7 | — |
| ordinary losses per million frames (base .73-.79) | .37-.40 (≈51% relative) | .25-.28 (≈35%) | — |
| `[DEXFENCE]` reserve lines per run (batch0927, base 10.2, SD 11.05) | 9.8 | 6.8 | — |
| any run-level continuous metric (e.g. heal_stock) | d = 2.8·√(2/16) = 0.99 SD | 0.70 SD | — |

**Arithmetic check (leaders, first-attempt win):**
- Pooled p = 194/469 = .414.
- Naive SE = √(2 × .414 × .586 / 100) = .0697, so MDD = .195.
- The bootstrap gives .155-.171, which is lower because the group mixes extreme bosses (Roxanne about .9, Winona about .04).

**Design effect:** the per-battle rate has a design effect of 1.6-2.5. For batch0927 leaders, naive SE = .0338 against bootstrap .053. One run took 29 attempts at Tate & Liza. So the per-battle won/(won+lost) table is a summary, not a test statistic.

**Further inflation:** 5 of batch0927's 35 runs replay another run's team (FINAL :347), which adds about ×1.08 to every MDD. D2 also has an unmeasured between-batch component (KI-112). Both are INFERRED.

### 4. Which v2 §Step 14 expectations a batch can answer (`DESIGN-v2.md:700-706`)
- **"0 `[ITEM] using` in non-key battles" — ANSWERABLE in one batch.**
  - A exposes about 2.0-2.4 ordinary uses per run, so about 32 expected per arm in D1.
  - Seeing 0 in B bounds a leak at under ~3/32 ≈ 9% of A's rate (D2: about 5%).
  - Wild battles are already 0 in both arms (`story_mode.py:873`).
  - This is a correctness item a driver already proved. The batch measures how often the fail-open paths fire, so each non-zero line must be read against its `[KEYBATTLE]` reason.
- **"More heal_stock at key-battle start" — ANSWERABLE if the effect is at least about 1 between-run SD (D1) or 0.7 SD (D2).**
  - There is no baseline: these logs have no heal_stock.
  - Use first attempts, analysed by run.
  - The effect is probably large (INFERRED from A's key-battle item use being only 1.6-4.6% of key battles).
- **"Key win rate not lower, per group" — DESCRIPTIVE ONLY under D1.**
  - D1 can rule out only drops larger than about 14-15 pp for leaders and about 8-12 pp for rivals and Magma/Aqua.
  - Single bosses (T&L with DOUBLEITEMS, Winona, Juan) are unassessable in both designs.
  - The Elite Four must read "NOT ASSESSED (n = 0-2)", never "not lower".
  - B's effect is second-order: A already uses items in singles key battles. So a realistic 0-10 pp effect is below D1's power and borderline for D2.
  - Selection: the arms reach different bosses with different parties, so stratify by trainer and report pairs per arm.
- **"Ordinary whiteouts — the question the batch answers" — mostly DESCRIPTIVE.**
  - The largest effect KEYITEMS could cause is every ordinary item battle becoming a loss: +0.33-0.37 per million frames (49/146.9M; 67/180.5M frames).
  - Power at fraction f of those battles turning into losses:

    | design | f = 1 | f = 0.5 | f = 0.3 |
    |---|---|---|---|
    | D1 | .72 | .24 | .11 |
    | D2 | .96 | .44 | .19 |

  - The comparison is also confounded: RULING 24's catch flags deliberately add catch-battle whiteouts (06:8037-8041).
  - **Better primary:** the loss rate in NON-KEY trainer battles (`[TRAINER]` class), which is where `_maybe_use_item` acts.
    - Baseline proxy (battles showing 2 or more foes): 38-44 losses in 1,429-1,802 battles (2.4-2.7%).
    - Poisson approximation, INFERRED:

      | design | f = 1 | f = 0.5 | f = 0.3 |
      |---|---|---|---|
      | D1 | .87-.97 | .41-.58 | .19-.28 |
      | D2 | — | .69-.86 | .34-.49 |

- **"Fewer `[DEXFENCE]` reserve refusals" — NOT directionally testable as written.**
  - This is VERIFIED from the code. The runway refusal returns at `story_mode.py:2110`, before the reserve check at `:2143`.
  - OPENFENCE in B removes the runway refusal at parties under 6, so B's encounters reach the reserve gate that A's never do.
  - The "last ball is reserved" reason (`counter_hunt.py:478`) fires before the runway refusal and is not affected.
  - Report it per reason, descriptively.
- **"No more leg-11 money refusals" (baseline 1 of 11) — DESCRIPTIVE ONLY.**
  - About 5-7 runs per arm (D1) or about 11 (D2) reach leg 11.
  - One-sided Fisher p < .05 needs B at 5/6 or more against A at 1/6, or 6/11 or more against 1/11. Only a catastrophic regression would show.
- **Ball buys, money, T1 income, wanted-species refusals, rare-species whiteouts, the weaken observer:** telemetry.
- **M1b:** an exposure count pooled across both arms (0 over the bound in N clean samples bounds the miss rate below 3/N). It is not an A/B.

### 5. Design constraints found
- **Per-lane flags do not exist (VERIFIED).** Every lane copies the parent's environment (`sandbox-pokebot/modules/endless_x4.py:173`), and each lane's starter is fixed: P1 Torchic, P2 Mudkip, P3 Treecko, P4 random (`:53`).
  - So a 2+2 split also splits starters.
  - Measured 2-vs-2 lane splits with no treatment differ by up to ±.09 (leaders first-attempt win), ±.12 (Magma/Aqua first-attempt win), ±.41 (T&L first-attempt win) and ±1.1 (ordinary losses per run).
  - Those differences are within sampling noise, so a starter effect can be neither shown nor excluded.
- **Preferred designs (INFERRED):**
  - D2: two batches, all 4 lanes per arm. No code change; about 24-28 h of the user's machine time.
  - Or a crossover: two batches, each split 2/2, arms swapped between batches. It needs per-lane env, and gives D2's sample size plus concurrency.
- **The design must pre-register (CLAUDE.md rule 9):**
  - the unit: the (run, trainer) first attempt, stratified by trainer;
  - one primary metric per expectation, with Holm correction across about 13 tests (about 0.65 false positives are expected if every effect is null);
  - the NI margins above;
  - the sentence: "a non-significant result is NOT confirmation; groups and bosses below MDD are descriptive only."
  - Step 14 answers "does the package help", not attribution (`DESIGN-v2.md:707`).

**Scratch (read-only analysis), in `C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\01ddd963-7a1a-4b49-8ecd-33397f5304e2\scratchpad\s14power\`:**
- `keybattles2.py`: the classifier.
- `runstats.py` / `runstats.json`: per-run counts.
- `power.py`: the bootstrap.
- `trainers.h` / `trainer_parties.h`: the decomp files.
