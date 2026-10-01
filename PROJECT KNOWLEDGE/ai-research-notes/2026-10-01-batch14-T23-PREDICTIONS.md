# 2026-10-01 — design v2 step 14, T2 + T3 (the grading tools): BUILD SPEC + PREDICTIONS (filed BEFORE any code)

⛔ **THE CAVEAT IS THE HEADLINE.** These are MEASUREMENT tools (`tools/story-dev` only). They grade tonight's batch;
they prove nothing about the bot by themselves. They are built while the batch runs, on the worktree, and are merged to
`main` only after it ends: the freeze (`04`) forbids any commit, pull or merge in the main checkout from 9:00 PM LA until
then.

**Parent:** `2026-10-01-batch14-DESIGN.md`: §3 T2/T3 define the tools, and §5's statistics are FROZEN there (K\*,
δ = .08 at 16 lanes, the C1 → C2 sequence, the harm flags at one-sided .05). This file adds only what the code needs:
the exact ids, line shapes and file layout.

## Step 0: what the author read (FILE:LINE or a real line, 2026-10-01)

- **K\* trainer ids**, from the decomp `include/constants/opponents.h`, fetched with `gh api` (lines 269-272, 525-540,
  601, 606):

| key | ids |
|---|---|
| ROXANNE | 265 |
| BRAWLY | 266 |
| WATTSON | 267 |
| FLANNERY | 268 |
| RIVAL_ROUTE_110 | 521, 524, 527 (Brendan × Mudkip, Treecko, Torchic) and 530, 533, 536 (May × the same) |
| TABITHA_MT_CHIMNEY | 597 |
| MAXIE_MT_CHIMNEY | 602 |

  Groups: leaders = the first four; rivals = RIVAL_ROUTE_110; Magma/Aqua = the last two.
  Checked live: today's smoke logs show `opp=265 class=0x20(LEADER)` on all 16 lanes.
- **The real line shapes**, from `endless-s14smoke-H4-random`, 2026-10-01:
  - `f58102 [TRAINER] end opp=532 class=0x32(PkMn_TRAINER) value=15 lvl_last=5 first=True base=300 res=Won money=3000->3300 delta=300 mult=1 heal_stock=- map=0,18`
  - `f2788 [STEP] 'Intro: holding 7f before confirming (RNG decorrelation)...'`
  - `f13041 [STEP] 'Story: choosing Treecko!'`
  - The FIRST `[hb]` line has `ids=[]`, so run identity is the first `[hb]` whose `ids=[…]` is NON-EMPTY:
    `ids=['<Species>#<PID8>:…`.
- **The runner's records:**
  - `ARMS.json` holds `lanes[*].{tag, slot, arm, starter, profile}` and `arms_text`.
  - `summary.json` holds `lanes_detail[tag].{cut_log, alive_at_stop, lanes_lost…}`.
  - A batch dir's logs sit at `L\d\d/debug-logs/*.log`, collected at the END; live, they sit at
    `sandbox-pokebot/profiles/endless-<tag>-H<n>-<starter>/debug-logs/*.log` (main checkout).
- **`battle_log.py` already has** `split_battles`, `parse_trainer`, `outcome_bucket` (a Draw = lost),
  `hp_item_count` and `parse_heal_stock`. Its `x4_logs` globs `L0*` under the CURRENT checkout. Its `attempt_summary`
  already says `first=` cannot mark a first attempt.

## T2 — `tools/story-dev/battle_log.py` (additions; existing behaviour unchanged)

- **`parse_env_all(lines) -> dict | None`:** the run header's `env-all:` dict (`ast.literal_eval`), or None.
- **`arm_of(lines, arms: dict) -> str`:** the arm name whose dict EQUALS the header's; `"?"` if none matches, and
  `"ambiguous"` if several do.
- **`run_identity(lines) -> dict`:**
  - `species` and `pid` come from the first `[hb]` line with a non-empty `ids=`.
  - `hold` comes from the `Intro: holding Nf` STEP line (0 when absent).
  - `chosen` comes from `Story: choosing X!`.
  - Missing values are `None`, never guessed.
- **`log_capped(lines) -> bool`:** true if the line contains the cap marker
  `event log size cap reached` (`debug_logger.py:463-468`).
- **`batch_logs(batch_dir) -> list`:** every `L\d\d/debug-logs/*.log` (any lane count), sorted.
- **`live_logs(tag, profiles=None) -> list`:** every `endless-<tag>-H*/debug-logs/*.log` under the MAIN checkout's
  sandbox profiles (`main_checkout()`).
- **`x4_logs` resolves stamps under the MAIN checkout** (`main_checkout()/tools/story-dev/x4-runs`), for any lane count.
- **`resolve_sources` refuses zero logs** (an error, exit 2), and gains `--tag` (live mode) and `--batch-dir`.
- **`first_attempts(battles, ids_of: dict) -> dict`:** for each key, the EARLIEST battle whose `[TRAINER] start` opp
  is in that key's ids AND that has a `[TRAINER] end`. Its outcome is `outcome_bucket` (won / lost; a Draw is lost).
  `first=` is NOT used.

## T3 — `tools/story-dev/compare_arms.py` (new; pure core, CLI around it)

**Input:** a batch dir (`x4-runs/<stamp>`, which needs `ARMS.json`) or `--tag` (live).

**Each log becomes ONE run record:**
- lane tag and slot, from the log's directory;
- the arm, from `arm_of` against `ARMS.json`'s arms. ⛔ A log whose arm disagrees with the lane's `ARMS.json` arm is
  REFUSED (counted and listed), never re-assigned;
- species, pid and cluster key `(arm, species, pid)`;
- status: `cut` (its file name is the lane's `cut_log`), `capped`, or `complete`;
- per K\* key: reached (bool), first-attempt won (bool or None), and the first attempt's `heal_stock` HP count;
- the non-key trainer battles' outcome counts.

**The statistics** (DESIGN §5, verbatim rules):

| reading | definition | verdict |
|---|---|---|
| **C1** | per run, the mean `hp_item_count` over its K\* first attempts; per arm, the mean over runs | PASS if the lower bound of B − A's two-sided 95% CI is above 0; otherwise C2 is DESCRIPTIVE |
| **C2** | p[a, X, s] = won first / fought, by realized species s ∈ {Torchic, Mudkip, Treecko}; p[a, X] = the mean over species present in BOTH arms for X; θ[a] = the mean over K\*; Δ = θB − θA | δ = `--delta` (default .08): NOT LOWER if lower95 > −δ; then HIGHER if lower95 > 0; else INCONCLUSIVE; "NOT LOWER, but statistically lower" when the 95% CI lies inside (−δ, 0) |
| **C2 LOWER** (a harm flag) | upper90 of Δ below 0 | — |
| **Reach** | per X: the meet rate per arm over runs NOT censored before X (a cut, capped or lost run that never met X is excluded); B − A with a 90% CI | REACH DIFFERS if any CI excludes 0 |
| **Composite** (always printed) | P(reached X and won the first attempt), averaged over K\*, with the same species weighting | — |
| **C5** | per arm, (Lost + Draw) / battles over NON-KEY trainer battles, a ratio of sums | REGRESSION if lower90 > 0; IMPROVED if upper90 < 0 |
| **Per group** (descriptive) | θ over each group's K\* trainers, with CIs | — |

- **The bootstrap:**
  - `--draws` draws (default 10,000), seeded (`--seed`, default 14, recorded);
  - strata are arm × species; clusters are resampled whole within their stratum, with replacement;
  - percentile CIs.
  - numpy if available, otherwise pure Python (the same seeded result is NOT required across the two).
- **Output:** a text report plus `--json OUT`. Exit 0 when the grade is computed (whatever the verdicts), 1 when an
  instrument control fails (zero runs, a refused log, an arm with no runs), and 2 for usage errors.

## The gate — `tools/story-dev/probe_compare_arms.py` (appended to `run_gates.py`)

**Synthetic runs with the real structure:** 8 lanes per arm, two per starter (the random lane's species drawn); 11-seed
pools per lane; same-species-PID replays; about 6 runs per lane; K\* first-attempt rates from the baseline
(`evidence/2026-10-01-batch14-POWER.txt`: Roxanne .92, Brawly .75, Wattson .15, Flannery .46, rival .36, Tabitha .97,
Maxie .72).

| # | Planted | Expected | Bound |
|---|---|---|---|
| CA1 | Δ = 0, 400 seeds, 400 draws | P(NOT LOWER) in [.70, .93] | §6 says about .82 at 45 clusters; ± Monte Carlo and the model |
| CA2 | Δ = −.08 (flip first-attempt wins in B with probability .08/θ), 1,000 seeds, 400 draws | NOT LOWER at most 41 of 1,000 | the binomial 99.9% upper bound at p = .025 |
| CA3 | Δ = −.20 and +.20, 50 seeds | LOWER ≥ 45 of 50; HIGHER ≥ 45 of 50 | — |
| CA4 | B's reach of Wattson cut by .35 | REACH DIFFERS on Wattson in ≥ 40 of 50 | — |
| CA5 | a run that loses Roxanne twice, then wins | first attempt = LOST | — |
| CA6 | two runs with one (species, pid) | always resampled together (one cluster) | — |
| CA7 | a log whose env-all is the OTHER arm's | REFUSED and listed; exit 1 | — |
| CA8 | C5 on hand-built counts | exactly the ratio of sums; REGRESSION fires on a planted +.03 at 30 seeds × 100 runs per arm | — |
| CA9 | C1 fails (no heal difference) | C2 printed as DESCRIPTIVE | — |
| CA10 | real line shapes (the four quoted above) | parse exactly | — |

**Then:** an adversarial mutant pass, as always.

## PREDICTIONS (graded when the tools are built; the batch is graded separately, in `…-batch14-GRADED.md`)

| # | Run | Prediction | Falsified by |
|---|---|---|---|
| T23-1 | `probe_compare_arms.py` | every row CA1-CA10 passes; the full suite passes | any FAIL |
| T23-2 | an adversarial mutant pass | every non-equivalent mutant of the estimand, the strata, the clustering, the verdict rules, the reach censoring, C5's ratio of sums, the first-attempt definition and the arm refusal reddens a row | a surviving non-equivalent mutant |
| T23-3 | `compare_arms.py` on the smoke batch `x4-runs/20261001-090649` | it parses all 16 logs (one run per lane, every run `cut`) with 0 refused; every run's species is read; Roxanne's first attempt is found on every lane whose first `opp=265` battle has a `[TRAINER] end` (all 16 lanes fought her, H7 and H15 twice, so those two lost the first attempt); C2 is INCONCLUSIVE with very wide CIs (n = 16); exit 0 | a refused log; a missing species; a missed first attempt; a crash |
| T23-4 | the same on the fault batch `x4-runs/20261001-090513` (aborted in 0.8 min) | exit 1 with the instrument control "arm with no usable runs" or similar, NOT a confident verdict | any verdict word printed as confirmatory |

## GRADED (2026-10-01; evidence `tools/story-dev/evidence/2026-10-01-batch14-T23-ADVERSARIAL.txt`)

- **T23-1 HELD (after the fold):** `probe_compare_arms.py` gives ALL PASS (69 rows, 129 mutants, 17 quoted lines;
  every fast row is in some mutant's red set). The full suite passes: all 139 enforcing gates, 143 entries.
- **T23-2 FAILED AS FILED.**
  - The builder's own pass held: 70 of 70 matched after it redesigned CS1.
  - The INDEPENDENT pass did not hold. Of 88 mutants, the builder's rows killed 59; 25 non-equivalent survivors were
    gate gaps (CS7's 90% CIs never straddled 0, no cut log with a wrong arm, no censored meeting…).
  - The statistics reviewer found a conditional BLOCKER: an automatically ABORTED batch would still be graded
    CONFIRMATORY, although DESIGN §4 voids it. It also found that K\* could silently shrink to its estimable subset
    (DESIGN S1's truncation case, reopened), and that an interrupted collection was graded silently.
  - The formulas themselves were right. An independent grader written from the DESIGN alone matched 598 of 598 values
    on the smoke batch, and 634 of 634 on two planted-edge variants.
  - **All of it is folded:** STOP ⇒ VOID; K\* NOT ESTIMABLE unless all 7 are; REACH DIFFERS on the C2 line;
    completeness controls; EXPLORATORY when an analysis choice is overridden; the JSON verdict field; the starter
    strata; a run cut mid-attempt is CENSORED; and the hunter's 17 rows.
- **T23-3 FAILED AS FILED on its wording.** The smoke batch parses 16 runs with 0 refused, every species is read, and
  Roxanne's first attempts are found (H7 and H15 lost). But C2 prints "DESCRIPTIVE — NOT ESTIMABLE over the frozen K\*
  (1 of 7); C1 did not pass", not "INCONCLUSIVE". The filed wording predated both the C1 gate's effect and F2. It also
  said nothing of H2, which reached Brawly and the Route 110 rival and lost both first attempts.
- **T23-4 HELD:** the fault batch exits 1: "C1-C2 VOID: STOP ARM HEADER ASSERTION FAILED (DESIGN §4)" and "INSTRUMENT
  CONTROL FAILED — NO GRADE", with H1's leaked log REFUSED.
- **Two of the builder's spec disagreements were right and are recorded:**
  - **§6's ".82" is optimistic.** The gate's calibrated model gives P(NOT LOWER | Δ = 0) ≈ .77 at 45 clusters (CA1:
    309 of 400), with the bootstrap SD within about 5% of the true one. The realized power tonight may be nearer .75.
  - **Zero logs:** "refuse zero logs" now applies only to a stamp, `--tag` and `--batch-dir`. The `--logs` and `--since`
    modes keep their pinned exit 1.
- **A note on the process:** the builder broke the shell-quoting rule once during the fold, piping a read-only timing
  script into `py -` with a heredoc. It wrote no file. The hook (`#27-shellhook`) goes live today.
