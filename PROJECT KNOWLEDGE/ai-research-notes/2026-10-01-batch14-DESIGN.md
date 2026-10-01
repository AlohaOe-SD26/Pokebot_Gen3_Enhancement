# 2026-10-01 — design v2 step 14 (the Phase 3 batch A/B): DESIGN + PRE-REGISTERED EXPECTATIONS (filed BEFORE any tool or run)

⛔ **THE CAVEAT IS THE HEADLINE.** One night's batch can show only LARGE differences. This step is built to do four things:
1. catch the package's CORRECTNESS failures at scale;
2. confirm that the package actually changed the bag at key battles (C1);
3. say whether B's FIRST-attempt win rate at the key trainers that nearly every run reaches is NOT LOWER than A's by more
   than a stated margin (C2), and flag large harm (C2 LOWER, C5 REGRESSION);
4. measure everything else (later bosses, ordinary losses, money, catching) DESCRIPTIVELY.

It answers "does the package help", never which flag did it (v2:707). Later bosses (Norman onward) and the Elite Four
are descriptive only: too few runs reach them, and reaching them is itself changed by the arm.
⇒ **Expected at the recommended 16 lanes:** a package with no effect reads NOT LOWER about 82% of the time (margin
.08) and INCONCLUSIVE otherwise; a realistic item effect will rarely read HIGHER; a regression is flagged with power .79
if half of today's ordinary item battles turned into losses, and .44 at 30% (§6).
⛔ **Nothing ran before the user said go** (USER RULING 28, §7).

**Status:** DESIGN, adversarially reviewed and folded (§9); the user's answers are USER RULING 28 (§7). T1 is being
built; no lane started.
**Recon** (NOTES, not truth): `2026-10-01-batch14-recon/b14_recon_{machinery,flags,stats,expectations,adversary}.md`;
the design's review: `…/b14_design_review.md` (four angles, about 40 findings).
**Plan of record:** `2026-09-29-r23-27-DESIGN-v2.md` §Step 14 (:687-707); `06` 2026-09-30 (arm B adds DOUBLEITEMS) and
2026-10-01 (per-lane flags or two batches is the user's call).

## 0. What the author verified at FILE:LINE (the recon's and the review's load-bearing claims)

- **A lane is ONE process for many runs:** `x4_headless.py` launches `pokebot.py … --endless-target N` once per lane
  (`lane_command`, :611-625) with `env = dict(os.environ)` (:628-629). So the flags are fixed per LANE, never per run.
- **Starters cycle modulo 4** (`LANE_STARTERS`, :118; `lane_starter`, :127-128). The "random" lane picks a new starter
  EVERY RUN (`early_game.py:1037`, per the review; batch0927's P4 realized Treecko 6, Torchic 2, Mudkip 1).
- **`--build` defaults to `custom`** (:957), and the custom fork has none of R23-R27, so **`--build sandbox` is mandatory**.
- **The dirty check is the whole tree** (`git_commit`, :600-609). The main checkout always carries the two volatile
  files, so today every batch reads as unattributable.
- **Logs reach the batch folder only at the END:** `collect_logs` runs after the main loop. During a batch,
  `x4-runs/<stamp>/L0n/` holds only `stdout.txt`; the live logs are in the lane PROFILES' `debug-logs/` (review R1, F3).
- **Stale lane state:** `sandbox-pokebot/profiles/endless-H1..H32-*` already exist with `stats.db`, `badge-log.json` and
  `current_save.sav` from the 2026-09-11..13 batches.
- **Flags:** R20/R24/R25 are read once per run, and only an exact `"1"` is ON (`story_mode.py:2428-2459`); `KEYITEMS`
  and `DOUBLEITEMS` per call (:880; `double_items.py:63-71`); `BALLRESTOCK` / `KITTOPOFF` per heal, where `"0"` maps to OFF
  with no error (`stock_topoff.py:75-95`, `:210-216`). The review traced every reader: **an explicit `"0"` is OFF in
  all of them**, and no sandbox code writes a `POKEBOT_*` variable.
- **Every run log's header has an `env-all:` line** (a dict of every `POKEBOT_*` variable, `debug_logger.py:262-266`) and
  a `build:` line (the commit, `:190-197`). The header is written before the game resets and is about 1.2 KB.
- **A log is capped at 30 MiB** (`debug_logger.py:44`). Recent logs grow about 0.5-0.6 MB per million frames.
- **`[KEYBATTLE]`** is logged on the first decision of EVERY trainer battle fought by the item strategy, key or not (the
  gate sits at the top of `_maybe_use_item`, `story_mode.py:873-881`, and is skipped entirely with KEYITEMS OFF). Its
  reasons are `fail_open_no_opponent`, `fail_open_unreadable`, `key_class`, `not_a_key_class` (`trainer_identity.py:70-85`)
  and `FAIL_OPEN(<exception>)` (`story_mode.py:6455`). `flag_off` cannot reach a log line.
- **`heal_stock`** is the raw bag, every item whose battle use is Healing, cures and Revives included
  (`trainer_identity.py:199-206`). `battle_log.hp_item_count` (:311) counts only items with `parameter > 0`, the filter
  production's HP policy uses.
- **The RULING 18 reserve arms with `SOOTOPOLIS_ARCHIE_MAXIE_LEAVE`** (`league_reserve.py:47`).
- **`WEAKEN_CALC`:** "Only `observe` + CALC (W-OBSCALC, a frequency) is sanctioned now" (`29`:202).
- **The run's starter and RNG hold are in the debug log:** the first `[hb] … ids=['<Species>#<PID8>:…` line, and
  `[STEP] 'Intro: holding Nf before confirming (RNG decorrelation)…'` (no line when the hold is 0; `intro.py:176-186`).
  ⚠ The recon said the hold reached stdout only; that was wrong.
- **The starter PID is a coarse identity.** In batch0927, 35 runs had 24 distinct (lane, PID) pairs. Holds of 103-111
  frames gave the same PID, one PID was a Mudkip in one lane and a Treecko in another, and same-PID runs diverge by the
  fifth key trainer in 13 of 14 groups (review S4, F1). In-game name entry is part of the seed (`intro.py`'s header), so
  a lane's NAME fixes its seed pool.
- **The machine:** Ryzen 9 5950X, 16 cores / 32 threads, 128 GB.
  - 8-lane headless batches ran here about 40 times through 2026-09-10, at 682-717 frames/s per lane in September.
  - 32-lane batches ran on 2026-09-11..13 at about 500 frames/s per lane (about 15.8k in total, CPU-saturated), with 0
    restarts in every summary.
  - StoryMode's global watchdog counts FRAMES (18,000; `story_mode.py:4558-4567`), so CPU load alone does not trip it.
- **Throughput:** about 0.55 runs per lane-hour at 8 headless lanes (≈ 0.92 × the GUI's 0.6; batch0927: 35 runs in
  56.5 lane-h). ⚠ The R20 plan's "~50 runs per arm per 12 h × 4 lanes" is about three times too high.
- **The main checkout auto-pulls** at session start/resume/clear/compact whenever its tree is clean and behind origin
  (`.claude/hooks/session-sync.ps1:36-53`). It is dirty today (the ledger file), which is the only thing preventing it.

## 1. The arms: literal and complete

**Every arm lists ALL 18 variables below; nothing else with `POKEBOT_` reaches a lane.**

| variable | A | B | why |
|---|---|---|---|
| `POKEBOT_R25_DMGAUDIT` | 1 | 1 | v2: M1b data in both arms; observe-only |
| `POKEBOT_R25_WEAKEN` | observe | observe | v2: weaken-frequency data; logs, never acts |
| `POKEBOT_R25_WEAKEN_CALC` | 1 | 1 | D2 |
| `POKEBOT_MAINTAIN` | 1 | 1 | the production default, pinned (`Run-Maintain-AB-Batch.bat` sets 0 for its OFF arm) |
| `POKEBOT_BOX_OVERFLOW_CATCH` | 1 | 1 | the production default, pinned |
| `POKEBOT_R24_CATCHHURT`, `_CATCHTRAIN`, `_OVERSURVIVAL`, `_NOFAINTBAIL` | 0 | 1 | v1 steps 2-5 |
| `POKEBOT_R25_CAP`, `POKEBOT_R25_RARE` | 0 | 1 | RULING 25 |
| `POKEBOT_R23_BALLRESTOCK` | 0 | 1 | RULING 23 |
| `POKEBOT_R27_KEYITEMS`, `POKEBOT_R26_KITTOPOFF`, `POKEBOT_R27_DOUBLEITEMS` | 0 | 1 | RULINGS 26-27; KIT needs KEYITEMS (else a named skip) |
| `POKEBOT_R20_OPENFENCE` | 0 | 1 | D3 |
| `POKEBOT_R20_TEAM6`, `POKEBOT_R20_HUNTFIRST` | 0 | 0 | D1 |

- **D1. `TEAM6` and `HUNTFIRST` stay OFF in B.** v2's list names only OPENFENCE. `#24-partycap` measured −36 points of
  finish rate for the same kind of change (`29`:165); plan (a) gave TEAM6 its own arm for that reason.
- **D2. `WEAKEN_CALC=1` in both arms.** Step 14 runs `observe` to get weaken frequencies. Stage 1 alone "WILL ALMOST NEVER
  ACT" (`29`:201), so without CALC that data would be near-empty. observe+CALC is the one sanctioned use (`29`:202), and
  W-OBSCALC played the same game as W-OBS on its trajectory (`weaken12-GRADED`:34). Being in both arms, it cannot bias A
  against B. ⚠ Stage 2 uses the UNFIXED calculator (`#27-dmgcalcfix`): this is a frequency, not a safety claim.
- **D3. OPENFENCE stays in B.** All three Phase 3 plans turn it on in the treatment arm, and RARE/CAP do almost nothing
  without it (v2:419-421). Its known risk (a fresh catch leading a key battle) confounds the key-battle metric. M-24 (§2)
  separates it; otherwise D-lead (§5) reports it.
- **D4. The open v2 questions run AS BUILT:** the key set is `KEY_TRAINER_CLASSES` (Q3's proposal) and the top-off
  amounts are 20 / 30 / ₽6,000 (Q1's). A different answer later invalidates C1-C2 (Q3) and the economy rows (Q1) for
  this batch. The user confirms this with the go-ahead.
- **D5. Only the 18 keys are ALLOWED** (an allowlist, not a denylist; review R6). Every key must appear literally in the
  build's source, so a typo is refused. Any key containing `FAULT`, ending in `_A` or `_ARM<n>`, or
  `POKEBOT_RNG_DECORRELATION_FRAMES` is refused.
- **D6. Behaviour variables without the prefix are stripped from every lane** and listed in the start manifest:
  `TEACH_MISS_WINDOW`, `TEACH_CANCEL_FORGET`, `CAPTURE_FORCE`, `CH21_CAPTURE_*`, `SAVE_POST_RIVAL` (review R7). The T1 gate
  scans the build for `environ.get("<NAME>")` reads without the `POKEBOT_` prefix, so a new one cannot slip past.

## 2. The mechanism: N concurrent headless lanes, one night, arms balanced lane-for-lane

`x4_headless.py --build sandbox --arms <file> --profile-tag s14 --minutes 780 --lanes N`, with arms assigned in blocks:
arm A = the first N/k lanes, arm B = the next N/k (and C after). **Within-arm position i has the same starter in every
arm, and the same IN-GAME NAME** (review R10), so each starter's lanes in A and B draw from the same seed pools. Names
differ WITHIN an arm, aiming at one seed pool per lane. ⚠ Not guaranteed: in the baseline, lanes P2 and P4 shared a
pool despite different names (POWER evidence, `collide.py`); the clusters absorb it, and §6's sensitivity row prices it.
The random lane is post-stratified by its REALIZED starter (§5).

- **M-16 (recommended): 2 arms × 8 lanes** (each arm has two lanes each of Torchic, Mudkip, Treecko and random).
  About 57 runs and 45 clusters per arm; C2's margin δ = .08 with 80% power (§6). Moderate load: about 620 frames/s
  per lane (interpolated).
- **M-8: 2 arms × 4 lanes.** The lightest load. About 32 runs and 24 clusters per arm; C2's margin must widen to
  δ = .11 for 80% power, and C5 is weaker (§6).
- **M-24: 3 arms × 8 lanes** (C = B with `OPENFENCE=0`). It separates OPENFENCE's effect on key battles from the items'
  (K3) at almost the same power per comparison as M-16 (about 52 runs per arm; δ = .08). It runs the CPU close to
  saturation (about 560 frames/s per lane, interpolated; 32 lanes have run here). B vs A stays the one confirmatory
  comparison; C's comparisons are descriptive.
- **M-2x4: two 4-lane GUI nights, one per arm.** No tool change. It costs two nights, confounds the arm with the night
  (KI-112 drift), needs the code frozen across both, and needs the dashboard's environment set by hand. Not recommended.
- **Rejected:** a 2/2 split on 4 lanes (the arm is then the starter); per-run alternation (a production change to the
  endless loop).

**Why concurrent:** a user park, a machine hiccup or a slow hour cuts every arm equally, and all arms get equal
lane-hours under one deadline.

## 3. Tools (their definitions are fixed HERE; T1 blocks the batch, T2-T4 block GRADING and may be built during it)

### T1 — `x4_headless.py` (blocks the batch)

- **(a) `--arms FILE`, JSON:**
  ```
  {"arms": {"A": {<the 18 keys>}, "B": {<the 18 keys>}},
   "monitor": {"A": {"forbid": [...]}, "B": {"forbid": [...], "require": {"<substring>": <seconds>, ...}}}}
  ```
  - Lanes are assigned to arms in blocks (§2).
  - Each lane's environment is `os.environ`, minus EVERY `POKEBOT_*` and the D6 names, plus its arm's dict.
  - **Pre-flight refuses:**
    - a key outside D5, or a key missing from the build's source;
    - arms with different key sets, or identical arms;
    - an N that does not divide evenly;
    - a non-string value;
    - `--arms` with `--build custom`;
    - a tag that is empty, starts with `P`, or contains a path separator;
    - a profile that already exists under the tag.
- **(b) Live header check, FAIL-CLOSED.** Once a run log's header is complete, its `env-all:` must parse
  (`ast.literal_eval`) to a dict EQUAL to the lane's arm. Its `build:` must equal the commit recorded at the start. A
  missing line, an unparseable line, a non-dict value or a mismatch ABORTS the batch, whatever `--on-bad-header` says
  (review R8, AI-5, F9).
- **(c) `--profile-tag TAG`:** profiles named `endless-TAG-H{n}-<starter>`, created fresh from the template. Nothing is
  deleted, and no stale state carries in.
- **(d) A START manifest, written before the first spawn:** `<stamp>/ARMS.json` holds the arms file verbatim, its sha256,
  each lane's arm, starter, name and profile, the stripped inherited variables, and sha256 of `profiles/*.yml` and
  `customcatchfilters.py` (review R1, R5, R9).
- **(e) Robust end.**
  - The main loop runs inside try/finally, so the lanes are always stopped.
  - Each spawn records its start time, exit time and exit code.
  - At the deadline, each lane records `alive_at_deadline` and the log it had OPEN, which is the CUT run.
  - The console is teed to `<stamp>/x4h.txt` (review R5).
- **(f) Freeze watch, every 60 s.** HEAD must be unchanged, and so must `git status --porcelain --untracked-files=all --
  sandbox-pokebot tools/story-dev/x4_headless.py`. Any change aborts the batch (review R4, R9). The dirty check behind
  the "unattributable" warning is SCOPED to those paths; the full porcelain is still recorded.
- **(g) The live integrity monitor, from the arms file's `monitor`.** Every tick, each lane's newest log is read
  incrementally and matched as a plain SUBSTRING over the whole line (review AI-4).
  - A `forbid` hit aborts the batch.
  - A `require` substring missing from a lane at its deadline aborts the batch.
  - This makes STOP-1 and STOP-2 (§4) work unattended overnight.
- **(h) Records:** the arm goes into `summary.json`'s lane rows and `--resummarise`'s carry-forward list, and the INDEX
  row is marked multi-arm. Existing call signatures keep working (`lane_env()`, `lane_profile_name(i)`; review R11).
- **Gate:** rows appended to `repro_x4_headless.py`, with a mutant for each refusal, the fail-closed header cases, the
  freeze watch, the monitor, and the D6 source scan. An adversarial mutant pass, as always.

### T2 — `battle_log.py` (blocks grading)

- **(a) `arm_of(log)`**, from `env-all:`. A log that matches no arm, or more than one, is REFUSED (counted, listed).
- **(b) Sources.**
  - A stamp resolves under the MAIN checkout's `tools/story-dev/x4-runs/`, for any lane count (`L\d\d`), and zero logs
    is an error (review R3).
  - A LIVE mode reads `<main>/sandbox-pokebot/profiles/endless-<tag>-H*/debug-logs/*.log`.
- **(c) The cap marker:** a capped log is flagged, and its tail is reported as cut, never as zero.
- **(d) Run identity.**
  - Species and PID come from the first `[hb] … ids=` line, and the hold from the `Intro: holding Nf` STEP line
    (none = 0; kept for audit only).
  - Whether the run ended, was cut at the deadline, or was lost to a lane death comes from T1's records.
- **(e) The first attempt** is the earliest `[TRAINER] start` per (run, trainer id) with a matching end. The `first=`
  field is NOT used: it is True on every lost re-attempt too (review S10). A gate row covers a run that loses twice
  and then wins.

### T3 — `compare_arms.py` (blocks grading): §5's statistics on T2

- **Gate, on synthetic runs with the real structure** (same-species-PID clusters, a random lane, about 6-8 runs per
  lane), over a FIXED seed list:
  - planted Δ = −δ: NOT LOWER at most .025 plus the binomial upper bound over 1,000 seeds;
  - planted Δ = 0: P(NOT LOWER) equals §6's stated power, within Monte Carlo error;
  - planted ±.2: LOWER / HIGHER;
  - reach shifts: the REACH DIFFERS warning fires.
  - (review S7, F5).

### T4 — counters (built DURING the batch on the worktree, before grading; definitions fixed in §5)

- `[KEYBATTLE]` allow/reason per offline class, and each non-key `[ITEM] using` joined to its battle's verdict;
- STOP-3's tool: run-end signatures per arm (`x4_headless._derail_reason` over each lane's `stdout.txt`), and the
  debug-log tail before each derail scanned for package tags (review R2);
- the economy: `[BALLS-BUY]` (both prefixes), `[KIT-BUY]`, T1 `delta` per map, `[MONEY]`;
- `[DEXFENCE]` reasons as distinct pairs; `[CATCH]` per rare species; `[WEAKEN-OBS]` by stage;
- M1b pooling, de-duplicated by content; the leg-11 counter (both refusal texts); the funnel; the lead covariate.

The v2 probes `probe_item_index_space.py` and `probe_boss_healing.py` are kept as CROSS-CHECKS (E1's counts, per-group
tables). T2/T3 replace them for the confirmatory readings (review F10).

## 4. Running it: smoke, the freeze, the stop rules

- **Smoke first (about 15 min, all N lanes, tag `s14smoke`, discarded).** It must show:
  - every lane's `env-all` and `build:` passing;
  - each B lane's ` rare=` and `[KEYBATTLE]`;
  - each A lane's runway refusal text (the first LIVE proof that an explicit `"0"` is OFF);
  - per-lane frames per second.

  The real batch starts only after it passes, under tag `s14` (review R13).
- **The freeze.**
  - The batch runs the MAIN checkout's `sandbox-pokebot` at commit C, which is main's HEAD after T1-T3 merge.
  - No merge to main, and no Claude session started in the main checkout, until the batch ends. The main checkout
    stays dirty (the ledger file), so its hook never pulls.
  - T1(f) aborts within a minute if anything moves anyway, and T1(b) catches a run that loaded a different commit.
- **STOP-1, arm integrity (automated, T1(g)), any of:**
  - an A-lane line containing `[KEYBATTLE]`, `[KIT-BUY]`, `[DBLITEM]`, `why=topoff`, ` rare=`, `[DEXCATCH-NOBAIL]`,
    `[CATCH] trainee`, `[CATCH] loss-filed` or `dex catch #` + `(joins the party)`;
  - a B-lane line containing `consume the HM/counter runway`, `a training grind is in progress` or `party is not at
    full strength` (texts only A can print; review AI-2).

  ⇒ abort; the sample is void.
- **STOP-2, vacuity (automated):** every B lane prints ` rare=` and `[KEYBATTLE]` within 60 minutes of its first run
  (they normally appear about 20 s and about 1.5 min in; review AI-1, F8).
- **STOP-3, a new failure (manual, at every read someone makes; T4's tool).** A run-end signature appears in at least
  2 B runs and 0 A runs, AND a package tag (`[ITEM] using`, `[DBLITEM]`, `[KIT-BUY]`, `why=topoff`, `[KEYBATTLE]`,
  `[DEXCATCH-NOBAIL]`, `[CATCH] trainee`) precedes those derails in the last ~200 debug-log lines. ⇒ park the batch and
  diagnose with a driver (the batch is not a debugger). A STOP-3 pattern first seen after the batch is a defect to
  diagnose, and the readings carry a note.
- **Not a stop:** B is slower than A, or B loses more ordinary battles. Those are findings.
- ⛔ **Pre-registered consequences** (review S9):
  - any STOP voids C1-C2, which become descriptive;
  - a restart is a NEW batch under a new tag, never pooled;
  - a user park stands, with the MDD for the realized n;
  - no read may change δ, `--minutes` or any analysis choice;
  - reads look only at safety and manipulation, never at an efficacy number.

## 5. PRE-REGISTERED EXPECTATIONS (graded in `2026-10-0X-batch14-GRADED.md`)

### The statistics

- **The unit is the run.** Clusters are (arm, realized species, starter PID). They are resampled together and NEVER
  de-duplicated.
- **The bootstrap** draws 10,000 resamples of clusters within strata of arm × realized species. Percentile CIs.
- **First attempts are T2(e)'s.** A Draw counts as a loss. A run cut by the deadline contributes only the first attempts
  it completed, and funnel denominators exclude runs cut before reaching the trainer.
- ⛔ **"A non-significant result is NOT confirmation."** Every rule below is applied to the CI computed from the data; no
  reading uses an observed effect to decide its own power.

### Correctness: deterministic invariants (one violation is a finding to diagnose)

| # | Expectation | Falsified by |
|---|---|---|
| E1 | B: 0 `[ITEM] using` and 0 `[DBLITEM] use` in battles classified NON-KEY offline, except battles whose `[KEYBATTLE]` reason is a fail-open one (each listed). Both arms: 0 in WILD battles | any such line outside a fail-open battle |
| E2 | B: at most one `[KEYBATTLE]` line per battle, and its `key=` equals the offline class (plumbing only: both use the same reader). Trainer battles with no line are counted, by strategy | a second line; a disagreement; any `reason=flag_off` |
| E3 | Arm identity holds at every observable trigger: | |
| | - A: none of STOP-1's B-only texts; B: none of its A-only texts | any such line |
| | - B: every `[CATCH] end kind=dex … end=lost` is followed by `[CATCH] loss-filed kind=dex` | one without |
| | - B: each run's FIRST Pokémon Center heal in Rustboro logs a `why=topoff…` line and a `[KIT-BUY]` line. (Only the first: after a failed errand, later heals in that city return silently, `stock_topoff.py:409-416`) | one without |
| | - `[CATCH] trainee` and `[DEXCATCH-NOBAIL]`: counts per arm only (their triggers are not observable in the log) | — |
| E4 | B uses double-battle items when it can: at least 1 `[DBLITEM]` use IF 5 or more distinct B runs reached a Tate & Liza FIRST attempt holding at least 1 HP item. Otherwise NOT ASSESSED | 0 uses. A zero is blamed on the 0.35 threshold only if every such battle also shows a battler at or below 35% HP with an HP item in the bag; otherwise it is a defect |
| E5 | B: 0 confirmed wrong targets (an `after` line where the partner's HP rose although the partner was not healed that turn); each reading is read by hand | one confirmed |

### Confirmatory: a fixed sequence (review S5)

**Step 1 — C1, the manipulation check (v2's "more heal_stock").**
- The statistic: per run, the mean `battle_log.hp_item_count(heal_stock)` over that run's FIRST attempts at the K\*
  trainers (step 2; all are fought long before the RULING 18 reserve arms, so the raw bag is the usable bag). Then
  the mean over runs. Using K\* keeps C1 off the reach bias that S1 found.
- `heal_stock=-` counts as 0. A missing or unreadable field is excluded and counted.
- Test: B − A > 0, one-sided α = .025.
- **If C1 fails, step 2 is DESCRIPTIVE:** the package did not change the bag, so a non-inferiority reading would say
  nothing about its mechanism.

**Step 2 — C2, the acceptance metric (v2's "key win rate not lower"), on a FIXED trainer set K\*.**
- **How K\* was chosen (from the baseline, before any data; review S1, S3).** Every key trainer (excluding the Space
  Center multi and the Elite Four) that BOTH:
  - was reached by at least 80% of runs in BOTH batch0926 and batch0927;
  - had a first-attempt win rate at or below .95 in at least one of them, so it can move.

  K\* = **Roxanne, Brawly, Wattson, Flannery** (leaders), **the Route 110 rival** (rivals), **Tabitha and Maxie at
  Mt. Chimney** (Magma/Aqua). Reach .81-1.00 and first-attempt .13-.94 in the baseline (POWER evidence, `kstar.py`;
  Tabitha only just qualifies on both criteria). Excluded: three rival/Wally fights at 1.00/1.00; Norman, Winona,
  the Route 119 rival and Shelly (Weather Institute), which fewer than 80% of batch0927's runs reached; every later
  trainer; the Space Center multi and the Elite Four by rule. **K\* is FROZEN here**, never re-derived from step 14's
  data.
- **Why K\*:** the trainers nearly every run reaches, so conditioning on reaching them barely depends on the arm.
- **The estimate.**
  - For each trainer X in K\* and each realized starter s ∈ {Torchic, Mudkip, Treecko}: p[arm, X, s] = (runs of s that
    fought X and won the first attempt) / (runs of s that fought X).
  - p[arm, X] is the equal-weight mean over the species with at least one such run in BOTH arms.
  - θ[arm] is the equal-weight mean over K\*, and Δ = θ[B] − θ[A].
- **The verdicts** (one-sided α = .025, the lower bound of a two-sided 95% CI), with margin **δ = .08 for M-16 and
  M-24, .11 for M-8** (each the margin with 80% power at Δ = 0, §6):
  - **NOT LOWER** if the lower bound is above −δ;
  - then, by closed testing at no extra α, **HIGHER** if the lower bound is above 0;
  - otherwise **INCONCLUSIVE**.
  - Precedence (review S11): when the CI lies inside (−δ, 0), the reading is "NOT LOWER, but statistically lower".
- **The reach check.** For every X in K\*, the meet rate B − A with its 90% CI. If any CI excludes 0, C2 carries
  **REACH DIFFERS**. The check is weak (it detects reach drops of about .10 only at the trainers every run reaches, §6),
  so the unconditional composite is ALWAYS printed beside C2: P(the run reaches X AND wins the first try), over runs
  not cut before X.

### Harm flags: unadjusted, one-sided α = .05 (the lower or upper bound of a two-sided 90% CI)

- **C2 LOWER:** the upper bound of Δ is below 0.
- **C5 REGRESSION, the question the batch answers (v2's "ordinary whiteouts").**
  - The statistic: per arm, (Lost + Draw) / battles over NON-KEY TRAINER battles, a ratio of sums resampled by cluster.
  - REGRESSION if the lower bound of B − A is above 0; IMPROVED if the upper bound is below 0.
  - The expected direction is B ≥ A, from the PACKAGE (KEYITEMS removes items there, and the other flags change teams;
    review S6). Power at M-16: .44 if 30% of the baseline's ordinary item battles became losses, .79 at 50% (§6).
  - ⛔ Its absence is NOT "no harm".
- **Per-group LOWER flags** (leaders, rivals, Magma/Aqua, each restricted to K\*): reported, descriptive.

### Descriptive (no verdict word)

- **D-group:** per-group and per-trainer first-attempt rates for EVERY key trainer, with CIs and reach (the later bosses
  Winona, Tate & Liza and Juan here). The Elite Four: NOT ASSESSED.
- **D-funnel, per arm:** runs started → met X → beat X on the first try → beat X eventually; attempts before an honest
  stop; badges; frames to each badge; frame-cap ends; cut runs.
- **D-attempt:** won/(won+lost) per attempt, per group. This is a summary (its design effect is 1.6-2.5).
- **D-lead (K3):** the share of key first attempts whose lead was caught after the Stone Badge, per arm, and C2 recomputed
  without them. ⚠ This conditions on a variable OPENFENCE causes (post-treatment), so it is biased toward B; the
  excluded share is printed beside it (review S11).
- **D-loss:** ordinary losses split three ways: non-key trainer battles, wild catch battles (`[CATCH] … end=lost`), other
  wild battles. Victory Road is reported per map, as input to RULING 18's REOPEN clause (06:7404-7405).
- **D-leg11:** money refusals, matching both texts, over runs that loaded EVER GRANDE CITY (16,10), per arm.
  - ⛔ v2's "B does NOT have more leg-11 money refusals" is WITHDRAWN as a test: about 11 runs per arm reach leg 11,
    so only a catastrophe would show (review F10). It is reported.
- **D-fence:** `[DEXFENCE]` reasons per run, as DISTINCT PAIRS, by era.
  - ⛔ v2's "fewer reserve refusals" is WITHDRAWN as a directional prediction. The runway refusal returns before the
    reserve check, and OPENFENCE moves B's encounters INTO the reserve gate.
- **D-economy:** `[BALLS-BUY] why=topoff` by ball and ₽ (the joint ball+kit budget: package-level, not BALLRESTOCK alone);
  `[KIT-BUY]`; T1 income per map; money at leg 11.
- **D-rare:** catch battles and whiteouts per rare species (telemetry; no REOPEN, v2 `[R-S1]`).
- **D-M1b:** `[DMGAUDIT]` samples pooled across arms, de-duplicated by content (for `#27-dmgcalcfix` / ACCEPT_MARGIN).
- **D-weaken:** `[WEAKEN-OBS] would=` counts by stage, per arm.
- **D-throughput:** frames per second and runs per lane-hour per arm, log sizes, any capped log.

## 6. Power (the review's and the power agent's computations; INFERRED until the smoke run measures fps)

Sources: the review's simulations (`2026-10-01-batch14-recon/b14_design_review.md`) and a dedicated power study by a
read-only agent, kept with its scripts in `tools/story-dev/evidence/2026-10-01-batch14-POWER.txt`. Everything below is
INFERRED from a simulation model except the rows marked VERIFIED.

- **The baseline (VERIFIED, 73 runs in batch0926 + batch0927):** completed runs average 4.57M frames, so about .55
  completed runs per lane-hour at 700 frames/s. The PID collision rate within a batch is .09, modelled as one seed pool
  of about 11 per lane. The pooled first-attempt θ over K\* is .631. Even batch0927 − batch0926 reads Δ = −.022,
  95% CI [−.085, +.031]: that is the noise this test must see through.
- **C2 at Δ = 0 (2,000 simulations each; Monte Carlo error about ±.02):**

| design | runs per arm | clusters per arm | SD of Δ | P(NOT LOWER) at δ = .06 / .08 / .10 / .12 | δ for 80% power |
|---|---|---|---|---|---|
| M-8 | 32 | 24 | .036 | .35 / .56 / .77 / .90 | .105 |
| **M-16** | **57** | **45** | **.026** | **.54 / .82 / .95 / .99** | **.079** |
| M-24 (per arm) | 52 | 42 | .028 | .51 / .79 / .93 / .99 | .081 |

  - Sensitivity for M-16: if same-species lanes share one seed pool (as P2 and P4 did), 37 clusters and δ80 = .085.
  - **The false-NOT-LOWER rate at a planted Δ = −δ** is .023-.032 for M-16 at δ = .08, against the nominal .025.
  - So at M-16 a package with NO effect reads NOT LOWER about 82% of the time, and INCONCLUSIVE otherwise. A realistic
    item effect (0-10 points; A already uses items in singles key battles) will rarely read HIGHER.
- **C5, the REGRESSION flag (one-sided α = .05):**
  - VERIFIED baseline: 237 losses in 7,761 non-key trainer battles (.0305), and 116 ordinary battles with an item use,
    112 of them won.
  - Power, if a fraction f of those item battles turned into losses:

| f | added rate | M-8 | M-16 |
|---|---|---|---|
| 0 (false alarm) | — | .05 | .04 |
| .3 | +.0043 | .31 | .44 |
| .5 | +.0072 | .57 | .79 |
| 1.0 | +.0143 | .92 | .99 |

- **The reach check at M-16 (90% rule, 80% power):** it detects a drop of about .10 at Roxanne, Brawly and the Route 110
  rival (reach 1.0), and only about .17-.19 at the other four. batch0927's own drop from batch0926 at those four was
  .13-.16, so it would NOT reliably be flagged. That is why the composite is always printed.
- **Throughput is the main unknown.** The smoke run measures frames/s per lane. A shortfall rescales the runs per arm
  proportionally; the margins stay as pre-registered, and the realized MDD is reported beside them.

## 7. Questions for the user — ✅ ANSWERED 2026-10-01 (USER RULING 28, `06`)

- **Q-S14a, how many lanes:** **M-16** (16 lanes, two arms).
- **Q-S14b, when:** **tonight if ready.** If the 15-minute smoke run passes, the batch starts WITHOUT asking again. It
  needs the machine left on, no GUI batch running, and no Claude session opened in the main checkout until it ends.
- **Q-S14c, the open proposals:** **run AS BUILT** (the key set, Q3; the ball top-off amounts, Q1).

## 8. Not in this step

- the upstream sync (parked);
- `#27-dmgcalcfix` (DMGAUDIT measures the unfixed calculator; known);
- weaken ON; per-flag attribution (only M-24 separates OPENFENCE);
- `#27-drawdefeat` (production still does not count a Draw as a defeat in either arm; the MEASUREMENT does).

## 9. The review, folded (`b14_design_review.md`)

| finding | what changed |
|---|---|
| S1 (BLOCKER) truncation by death in C2 | C2 now uses a FIXED trainer set K\* of high-reach, movable trainers chosen from the baseline, plus a reach check and the unconditional composite; later bosses are descriptive |
| S2, F6 power overstated; the one-sided level; "below its MDD" | §6 restated under the actual rule; δ chosen for stated power; the post-hoc wording removed |
| S3 ceiling trainers dilute δ | K\* excludes trainers at .95 or above in both baselines |
| S4, F1, F2 cluster key; the stdout cross-check; hold location | clusters (arm, species, PID), never de-duplicated; strata arm × species; hold from the debug log, for audit only |
| S5, F5 Holm undefined | a fixed sequence (C1 gatekeeps C2), harm flags unadjusted; α and every unit fixed |
| S6 C5's power and unit | ratio of sums by cluster; power simulated; direction attributed to the package |
| S7, F5 the T3 gate | plants −δ over 1,000 fixed seeds with a binomial bound; plants 0 against the stated power |
| S8 C1 counted cures and had no unit | `hp_item_count`; per-run mean; missing values counted |
| S9 stop consequences undefined | pre-registered (§4) |
| S10 `first=` is True on re-attempts | T2(e) defines the first attempt |
| S11 verdict precedence; D-lead is post-treatment | both stated |
| R1, F3 no live log source | T2(b) live mode; T1(g) monitors live, unattended |
| R2 STOP-3 could never fire | the package-tag test moved to the debug tail before each derail |
| R3 stamp mode reads the worktree | resolves under the main checkout; zero logs is an error |
| R4 auto-pull mid-batch | the freeze rules plus T1(f) and T1(b)'s `build:` check |
| R5 no try/finally, no start record | T1(d), T1(e) |
| R6 the denylist misses names | an allowlist plus a source check (D5) |
| R7 unprefixed behaviour variables | stripped and recorded; a gate scan (D6) |
| R8, AI-5, F9 a missing `env-all` passed as "unknown" | fail-closed, aborting whatever `--on-bad-header` says |
| R9 the dirty scope missed the runner and untracked files | T1(f)'s scope; the config hashes |
| R10 lane names differ by arm | paired names across arms, distinct within an arm (§2) |
| R11 the arm is lost on resummarise | T1(h) |
| R12 the throughput baseline and a citation | September 8-lane figures; `story_mode.py:4558-4567` |
| R13 no smoke run | §4 |
| AI-1, F8 STOP-2 was late and narrow | ` rare=` and `[KEYBATTLE]` within 60 min, automated |
| AI-2 OPENFENCE had no marker; no reverse check | `dex catch #… (joins the party)` and three A-only texts in STOP-1 |
| AI-3 E3's B half could not fail | observable triggers per family, or counts only |
| AI-4 markers outside the category slot | plain substring matching, gated |
| AI-6 `flag_off` cannot occur | dropped; a `flag_off` line is an E2 violation |
| F4 the random lane's starter mix | post-stratified by REALIZED species |
| F7 E4's denominator | distinct runs with an HP item at a T&L first attempt |
| F10 silent departures from v2 | the v2 probes are kept as cross-checks; leg-11 is withdrawn explicitly |
