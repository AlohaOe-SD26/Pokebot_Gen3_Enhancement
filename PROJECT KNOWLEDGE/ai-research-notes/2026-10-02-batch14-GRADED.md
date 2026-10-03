# 2026-10-02 — design v2 step 14: the A/B batch GRADED (`20261001-210001`)

⛔ **THE CAVEAT IS THE HEADLINE.**
- **As registered, the frozen grader reads C2 = HIGHER: arm B won more key first attempts.** But that verdict rests on
  a GRADER DEFECT. The frozen run-identity reader wrongly excluded 27 of the 78 runs, unevenly across arms (A 16,
  B 11).
- **With the identity corrected, the same statistics read NOT LOWER, not HIGHER.** Δ = +0.037, 95% CI
  [−0.018, +0.093]. This is an EXPLORATORY re-grade: the fix was made after seeing the data, so whether it counts as
  confirmatory is the USER's call.
- **The batch also found a B-only HARM.** 7 of 14 arm-B Mudkip runs hit a wall at Norman, against 0 of 13 in arm A,
  through a box-first counter path that is ON in both arms. It is not a package flag; only the fault switch
  `POKEBOT_R20_FAULT_NOBOXCOUNTER` turns it off.
- **The damage-calculator acceptance (M1b) FAILS by one sample out of 194,304.** That sample sits at the bound of a
  known divergence.
- ⇒ **The package should NOT be promoted as-is.**

**Parent:** `2026-10-01-batch14-DESIGN.md` (§4 the stops, §5 the pre-registered expectations, §6 power).

**Evidence:**
- `tools/story-dev/evidence/2026-10-02-batch14-GRADE-OUTPUTS.txt`: the frozen tools' full outputs, the M1b audit
  summary, and the corrected re-grade.
- `tools/story-dev/evidence/2026-10-02-batch14-INVESTIGATIONS.txt`: three independent read-only agents, verbatim. The
  coordinator re-verified their load-bearing claims: the identity code, the box-first accept, and the re-grade, re-run.

## The batch

- **The run:** 16 lanes (A = H1-H8, B = H9-H16), 780.5 min (9:00 PM 2026-10-01 to 10:00 AM 2026-10-02), tag `s14`,
  one build `f4509da1` on every lane. `#27-battleeq` (KI-108) was NOT merged, so the batch ran the unfixed
  `BattleState.__eq__`.
- **Verdict OK:** 0 arm-integrity violations, no lanes lost, stopped at the deadline. **STOP-1 and STOP-2 did not
  fire.**
- **78 logs:** 40 A and 38 B, one log = one run.
- **Throughput:** about 620 frames/s per lane. Complete runs per lane-hour: A 0.212, B 0.221 (⛔ graded runs only; with all 78 runs A .308, B .289, see the ERRATUM). The plan assumed about
  57 runs per arm and got 40 / 38.

## Correctness (E1-E5): the checks read ALL 78 logs

| # | Grade | Reading |
|---|---|---|
| E1 | **PASS** | 0 violating lines over 4,239 B non-key battles and 115,970 wild battles (both arms); 0 fail-open exemptions |
| E2 | **PASS** | 6,000 B `[KEYBATTLE]` lines, 0 violations, 0 fail-open. 18 key trainer battles had no line (a summary, per DESIGN) |
| E3 | **PASS** (its loss-filing half had 0 trials) | 0 forbidden texts in either arm; B's first Rustboro heal logged both lines in 38 of 38 runs. Counts only: B `[CATCH] trainee` 331, `[DEXCATCH-NOBAIL]` 24; A 0 and 0 |
| E4 | **NOT ASSESSED** | 4 B runs reached a Tate & Liza first attempt holding an HP item (the threshold is 5). 1 `[DBLITEM] use` in those attempts; 11 across all B battles |
| E5 | **PASS** | 11 `after` readings; the partner's HP rose in 0. ⚠ The batch ran the unfixed KI-108 code, so doubles `[TURN n]` labels can lag one turn. With 0 rises listed, nothing depended on them |

## Confirmatory (DESIGN §5): FROZEN as registered, and CORRECTED (exploratory)

| Reading | FROZEN grader (A 24 runs / 21 clusters, B 27 / 22) | CORRECTED identity, EXPLORATORY (A 40 / 37, B 38 / 33) |
|---|---|---|
| **C1** manipulation (HP items held at K\* first attempts) | A 0.024, B 0.450, B − A +0.426, 95% CI [+0.291, +0.541] → **PASS** | A 0.032, B 0.930, B − A +0.898, 95% CI [+0.442, +1.479] → **PASS** |
| **C2** first-attempt win rate over the frozen K\* | θA 0.593, θB 0.681, **Δ +0.087**, 95% CI [+0.017, +0.159] → **HIGHER** | θA 0.625, θB 0.662, **Δ +0.037**, 95% CI [−0.018, +0.093] → **NOT LOWER** |
| Reach (90% CI per K\* trainer) | no CI excludes 0 | no CI excludes 0 |
| **C2 LOWER** harm flag | none (90% CI [+0.030, +0.148]) | none (90% CI [−0.009, +0.085]) |
| **C5** ordinary-trainer losses (B − A) | −0.0045, 90% CI [−0.0113, +0.0029] → no flag | −0.0014, 90% CI [−0.0071, +0.0048] → no flag |
| Per-group, 90% CI (descriptive) | leaders +0.057 [−0.016, +0.136]; rivals +0.253 [+0.080, +0.421]; Magma/Aqua +0.066 [−0.006, +0.139] | leaders +0.036 [−0.024, +0.102]; rivals +0.103 [−0.063, +0.262]; Magma/Aqua +0.006 [−0.061, +0.072] |

- **Neither grade raises a harm flag.** C5's absence of a flag is NOT "no harm" (DESIGN §5), and the Norman wall below
  is a harm C5 does not measure: Norman is a key trainer outside K\*.
- **The STOP rules:** none fired automatically. STOP-3 reads "no" by its rule, but its one qualifying signature is a
  package-caused failure (next section). Per DESIGN §4, "a STOP-3 pattern first seen after the batch is a defect to
  diagnose, and the readings carry a note". This is that note. No `--void` was passed: nobody parked the batch.

### The grader defect behind the frozen verdict (F8)

- **Where it is:** `battle_log.run_identity` (`tools/story-dev/battle_log.py:739-764`) takes a run's species and PID from
  the FIRST `[hb]` line with a non-empty `ids=`. This is the frozen spec's own rule (`2026-10-01-batch14-T23-PREDICTIONS.md`).
- **How it misreads:**
  - Once a lane's run reaches the Hall of Fame, every later reset in that lane boots from the in-game save, which
    holds the champion party.
  - One `[hb]` fires after "Intro: New Game" but BEFORE the new game clears the party. In L02's
    `…-20261002-010951.log`: line 83 `ids=['Swampert#41027B14:L78…`, line 86 `[PARTY] size 6 -> 0`, line 298
    `'Story: choosing Mudkip!'`, line 311 `ids=['Mudkip#68D2F871:L5…`.
  - So the run's identity reads as the saved champion's lead (Swampert, Blaziken, Mightyena, Swellow or Ninjask), and
    DECISION F8 excludes it as "not a starter".
- **Scope:**
  - The 27 excluded logs are EXACTLY the 27 such boots.
  - All 27 are genuine new games: a New Game step, a party clear, a choosing line, a fresh starter.
  - No INCLUDED run carries a stale identity: in the other 51 logs, the frozen identity equals the post-choose one.
- **Why it moved the verdict:** the exclusion fell unevenly (A 16, B 11) and correlated with outcome. The excluded A
  runs pooled θ .653 against the kept A runs' .620; the excluded B runs .644 against the kept B runs' .677. So excluding
  them inflated Δ.
- **The correction (scratch only):**
  - It takes the identity from the first `[hb]` after `Story: choosing X!`. A second definition, the first `[hb]` after
    the party clear, agrees on 78 of 78 logs.
  - Draws, seed and δ are unchanged.
  - An unpatched control run of the same driver reproduces the frozen output line for line.
- **A second telemetry defect, same cause:** the stale-boot logs record `[BADGE] n=1..8` at f301 from the loaded save.
  It does not touch the frozen tables (those logs were excluded), but any re-inclusion must handle it.

## The B-only Norman wall (STOP-3's qualifying signature)

**The signature:** "this boss: N losses with no super-effective answer to Normal", in 7 B runs and 0 A runs (H10 runs
1, 2 and 4; H14 runs 1, 2, 3 and 5). All 7 are Mudkip runs, and no acting tag appeared in their last 200 lines.

**Over all 78 logs:**
- Norman was eventually beaten by A 36 of 36 runs that met him, and by B 27 of 35. The 8 that never won are the 7 walls
  plus 1 run cut by the deadline.
- Mudkip only: A 13 of 13, B 7 of 14.

**The mechanism.** It was observed with complete separation in this batch, but has not been shown causal by a driver
A/B. The agent's report holds the full line-level evidence; the coordinator re-verified the code.

1. B's package fills the party early. `POKEBOT_R20_OPENFENCE=1` was required in all 7 walls, and
   `POKEBOT_R24_CATCHHURT=1` in 5 of 7: post-badge-1 dex catches JOIN the party up to 6. An L6-10 Makuhita met in
   Granite Cave is then caught into the PC box. A's fence refuses it ("a catch would consume the HM/counter runway"):
   Makuhita caught by badge 4 in A 0 of 40 runs, B 25 of 38.
2. At Norman, the counter ladder's **box-first** step, which is ON in both arms (not a package flag; only a fault switch turns it off), picks that
   Makuhita.
   `counter_hunt.box_counter_choice` accepts a mon on TYPE ALONE (`if not (type_hit or credible): continue`). An L6-9
   Makuhita has no damaging Fighting move, and Arm Thrust (15 BP) is below the credible threshold. The box-first pick
   uses up the ladder's once-per-boss budget.
3. So the Fiery Path Machop hunt, which won every A Mudkip run that needed a counter, never happens. The run takes one
   "second wind", then stops honestly after 12-15 Norman fights.
4. The acting B line, `[DEXFENCE] CATCH … goes to the PC box`, sits 7,000-18,000 lines before the run end. **STOP-3's
   200-line tail cannot see it**, which is a blind spot in the STOP-3 design.

**What it is NOT:**
- a level or team-strength difference alone;
- money or balls at Norman;
- Fiery Path reachability;
- MAINTAIN alone (it is on in both arms);
- CATCHTRAIN.

**Other bosses:**
- One B "answer to Fire" wall (H11 run 1, a Numel counter with no credible move). One run, so it supports no B-only
  conclusion.
- Tate & Liza walls are A 2 / B 8, and the B ones show the same box-first-on-an-early-catch pattern. Not yet verified
  per boss.

**The decisive check (proposed, not run):** a direct-call driver at Norman in the `--driver counterbox` style. Arm X
injects an L8 Makuhita into the box; arm Y leaves it empty; arm Z is arm X with `POKEBOT_R20_FAULT_NOBOXCOUNTER=1`. The
readings are whether the hunt planner was entered and the `_counter_hunts` text. Details are in the INVESTIGATIONS
evidence.

## Descriptive (DESIGN §5; frozen tables over the 51 graded runs unless noted)

- **D-funnel:**
  - **Champions:** A 6 of the 8 runs that met Wallace, B 4 of 9. Elite Four first attempts were near-perfect in both
    arms; Wallace was the wall.
  - **Badges, max per run:** A {2: 1, 5: 7, 6: 2, 7: 2, 8: 12}; B {3: 1, 4: 6, 6: 5, 7: 3, 8: 12}. The six B runs at 4
    badges are the Norman wall.
- **D-boss, first attempts:**

  | Boss | A | B |
  |---|---|---|
  | Norman | 2/23 | 3/26 |
  | Winona | 1/19 | 0/20 |
  | Tate & Liza | 3/16 | 2/20 |
  | Juan | 4/14 | 3/14 |
  | Elite Four | NOT ASSESSED | NOT ASSESSED |

- **D-attempt, won / (won + lost) per attempt:**

  | Group | A | B |
  |---|---|---|
  | leaders | 23.1% | 19.3% |
  | rivals | 78.3% | 83.7% |
  | Magma/Aqua | 69.8% | 81.4% |
  | Elite Four | 87.3% | 88.0% |

  A summary statistic: looping runs weigh more.
- **D-lead (post-treatment, biased toward B):** key first attempts led by a species caught after the Stone Badge: A
  1 of 487, B 33 of 551 (6%). Without them, C2's per-trainer B rates move little, except the Route 110 rival's:
  .534 → .611.
- **D-loss:**

  | Battle class | A | B |
  |---|---|---|
  | non-key trainer | 81/2,762 | 77/3,103 |
  | wild catch | 2/189 | 0/469 |
  | other wild | 3/34,477 | 1/46,850 |

  Victory Road: A 0 lost; B 2 of 19,793 on 1F.
- **D-leg11:** 11 runs per arm loaded Ever Grande (16,10); 1 money-refusal derail per arm.
- **D-fence:** distinct (species, reason) pairs before Sootopolis A 1,234, B 1,211. B's open fence replaces A's "runway"
  refusals (535 → 0) with dex catches, both to the box (207) and joining the party (61).
- **D-economy:**
  - B's package spent ₽157,400 over 115 paying errands (22 joint ball+kit): 315 Poké Balls and 17 Ultra Balls topped
    off, and 104 Super Potions bought.
  - Money at leg 11, medians: A ₽36,185, B ₽38,375.
- **D-M1b (damage-calculator acceptance):**
  - 194,304 clean whitelisted hits: **ACCEPTANCE FAIL** on exactly 1 sample over crit_max + 3. That sample is f214702,
    a critical-hit Absorb: 132 observed against crit_max 128, so +4 HP.
  - +4 is the known D1 divergence's documented bound: the crit ×2 is applied after STAB and type (`#27-dmgcalcfix`;
    the audit's header says "M1a bound 4").
  - ⇒ Step 12's stage 2 (`POKEBOT_R25_WEAKEN_CALC`) stays OFF, as pre-registered.
  - ~~⚠ The pool came from the 51 graded runs only; the 27 wrongly excluded logs are not in it.~~ ⛔ **WRONG (see the ERRATUM below):** the pool read ALL 78 logs.
- **D-throughput:** about 616 / 624 frames/s per lane (A / B), 104 lane-hours per arm, no capped logs.
- **D-rare and D-weaken:** in the GRADE-OUTPUTS evidence; nothing notable was read from them.

## The realized MDD (DESIGN §4 and §6)

The power study's scripts were re-run unchanged. They reproduce the plan exactly: 56.6 runs per arm, δ80 .0785,
P(NOT LOWER | Δ = 0) .817.

| Grade | MDD80 for HIGHER | P(NOT LOWER \| Δ = 0) |
|---|---|---|
| Frozen n (24 / 27 runs) | ≈ .11-.12 (simulation), .100-.106 (plug-in) | ≈ .52-.58 |
| Corrected n (40 / 38) | ≈ .085-.093 (simulation), .078-.081 (plug-in) | ≈ .72-.83 |

- Both MDDs exceed the pre-registered δ = .08, because the batch produced about 40 runs per arm rather than 57.
- At the frozen n the percentile bootstrap is somewhat anti-conservative: a false HIGHER about .036 of the time,
  against a nominal .025.

## What this means, and what the user decides

1. **On key first attempts, the package is NOT worse, and is probably slightly better** (corrected Δ +3.7 points, 95% CI
   −1.8 to +9.3). The registered "HIGHER" does not survive the identity fix. Whether the corrected reading becomes the
   confirmatory one is a **USER decision**: the fix came after seeing the data, which DESIGN §4 forbids for analysis
   choices, though here it repairs a misread rather than choosing a different analysis.
2. **The package exposes a real harm: the Norman wall,** through a default-ON path that the package's early catches trigger. **Do not promote it as-is.** The fix
   direction is to require a credible move or a level floor for a type-only box-first pick, or to stop box-first from
   using up the once-per-boss budget when the boss still reads as hopeless. Prove it first with the proposed driver
   A/B.
3. **Damage calculator:** stage 2 stays OFF. Either fix D1 (`#27-dmgcalcfix`) and re-audit, or the user sets
   ACCEPT_MARGIN to 4 (it is a PROPOSAL awaiting the user).
4. **Tooling, before the next batch:**
   - fix `run_identity` (and the stale `[BADGE]` lines) with a gate;
   - give STOP-3 a whole-run view: the 200-line tail missed the acting line here.

## ERRATUM and ADDENDUM (2026-10-02, afternoon: `#27-gradeidentity`, KI-119; USER RULING 30)

**Erratum: two statements above were wrong.**
- **The M1b pool covered ALL 78 logs, not 51.** `batch14_checks.load`'s `visit` hook runs on every log, excluded ones
  included (`tools/story-dev/batch14_checks.py:652-657`). So E1-E5, STOP-3 and D-M1b were never affected by the
  exclusion. The fixed tools reproduce the pool byte for byte (SHA-1 `46e60f68…`, 194,304 accepted samples, the same
  1 FAIL sample).
- **Complete runs per lane-hour counted the graded runs only.** With all 78 runs: A .308, B .289.

**The operative result: USER RULING 30** (`06-DECISIONS-LOG.md`, 2026-10-02).
- The user delegated the decision to the coordinator, bounded by organic gameplay and the program's purpose. The
  corrected reading is the operative result, and the frozen "HIGHER" is WITHDRAWN.
- Why: the fix repairs a MISREAD of 27 genuine new games, not an analysis choice, and it is the more conservative
  reading.

**The re-grade with the fixed tools** (`tools/story-dev/evidence/2026-10-02-gradeidentity-REGRADE.txt`).
- It reproduces the scratch corrected re-grade line for line: 78 logs, A 40 / B 38, 0 excluded, clusters 37 / 33.
- C1 PASS, Δ +0.898. C2 NOT LOWER, Δ +0.037, 95% CI [−0.018, +0.093]. C5 Δ −0.0014. No harm flag.
- Its status line reads "OPERATIVE BY USER RULING 30 — graded by a grader revised after the batch". A batch with no
  ruling reads EXPLORATORY: the fail-closed GRADER_REVISIONS rule.

**The descriptive tables over ALL 78 runs.** Badges come from leader wins, because the bot never logged real
`[BADGE]` lines after a Hall-of-Fame boot.
- **Badges, max per run:** A {1: 1, 2: 1, 3: 2, 5: 8, 6: 2, 7: 3, 8: 23}; B {3: 2, 4: 9, 6: 10, 7: 3, 8: 14}.
- **D-lead:** key first attempts led by a post-Stone-Badge catch: A 1 of 801, B 40 of 726.
- **D-boss, first attempts:**

  | Boss | A | B |
  |---|---|---|
  | Norman | 2/36 | 5/35 |
  | Winona | 1/32 | 0/27 |
  | Tate & Liza | 7/28 | 3/26 |
  | Juan | 11/25 | 4/16 |

- **Champions:** Wallace was met by A 10 times, with 7 eventual wins (6 on the first attempt); B met him 9 times and won
  4.
- **D-attempt, A/B:**

  | Group | A | B |
  |---|---|---|
  | leaders | 25.2% | 19.9% |
  | rivals | 78.4% | 81.7% |
  | Magma/Aqua | 69.4% | 75.2% |
  | Elite Four | 87.2% | 88.0% |

**What the corrected data changes in the reading above:**
- The package is NOT worse at key first attempts (C2). But arm B trails at later bosses: Norman's wall (KI-118), and
  Tate & Liza (KI-122, mostly starter selection plus a stale-counter lead bug). B also has fewer champions.
- So "not worse at K\*" must not be read as "not worse overall". The promotion block stands until KI-118 and KI-122
  are fixed and re-measured.
