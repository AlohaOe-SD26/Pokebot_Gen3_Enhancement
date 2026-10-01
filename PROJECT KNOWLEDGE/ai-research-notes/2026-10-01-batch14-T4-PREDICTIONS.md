# 2026-10-01 — design v2 step 14, T4 (the batch's correctness checks and descriptive counters): BUILD SPEC + PREDICTIONS (filed BEFORE any code)

⛔ **THE CAVEAT IS THE HEADLINE.** T4 is MEASUREMENT tooling (`tools/story-dev` only). It turns the batch logs into the
DESIGN's correctness invariants (E1-E5), its STOP-3 read, and its DESCRIPTIVE tables. None of it is a confirmatory
reading: those are C1-C5 in `compare_arms.py` (T3). It is built on the worktree WHILE the batch runs (from 9:00 PM LA)
and merged to `main` only after the batch ends (the freeze).

**Parent:** `2026-10-01-batch14-DESIGN.md`: §4 (STOP-3), §5 (E1-E5 and the "Descriptive" list), §3 T4. The recon note
`2026-10-01-batch14-recon/b14_recon_expectations.md` §B lists every emitter and its line shape. **Reuse:**
`battle_log.py` (T2: run records, `arm_of`, `first_attempts`, the parsers for `[KEYBATTLE]`, `[DBLITEM]` and
`[TRAINER]`), and `compare_arms.py`'s run loading (the arm refusal, cut / lost / capped status). Never a second parser
for something T2 already parses.

## T4a — `tools/story-dev/batch14_checks.py` (the correctness invariants and STOP-3)

Input: the same as `compare_arms.py` (a batch dir, or `--tag`), loading runs through the same code. Each check prints
PASS / FINDING / NOT ASSESSED with the lines it rests on. The exit code is 0 when it computes; FINDINGs are reported,
not errors.

| check | rule (DESIGN §5) | what it lists |
|---|---|---|
| **E1** | B: 0 `[ITEM] using` and 0 `[DBLITEM] use` in battles classified NON-KEY offline (`[TRAINER]` class not in `KEY_TRAINER_CLASSES`), except battles whose `[KEYBATTLE]` reason is a fail-open one (`fail_open_*` or `FAIL_OPEN(…)`). Both arms: 0 such lines in WILD battles (no `[TRAINER]` line) | every exempted fail-open battle and every violating line |
| **E2** | B: at most one `[KEYBATTLE]` per battle; its `key=` equals the offline class; any `reason=flag_off` is a violation. Trainer battles with no `[KEYBATTLE]` are counted, as a summary | violations |
| **E3** | A: none of the monitor's B-only texts; B: none of its A-only texts (the arms file's `monitor` lists). B: every `[CATCH] end kind=dex … end=lost` is followed in the same battle or run by `[CATCH] loss-filed kind=dex`. B: each run's FIRST Pokémon Center heal IN RUSTBORO logs a `why=topoff` line and a `[KIT-BUY]` line. `[CATCH] trainee` and `[DEXCATCH-NOBAIL]`: counts per arm only | each miss |
| **E4** | B: at least 1 `[DBLITEM] use` IF at least 5 distinct B runs reached a Tate & Liza FIRST attempt holding at least 1 HP item (`hp_item_count` on its `[TRAINER] start heal_stock`). Otherwise NOT ASSESSED. On a zero, list every such battle with any battler at or below 35% HP while an HP item was held | the T&L first attempts and their bags |
| **E5** | B: every `[DBLITEM] after` reading where the PARTNER's HP rose although the partner was not healed that turn, listed for reading BY HAND (never auto-counted as a defect) | the battle, its turn and both HP readings |
| **STOP-3** | the run-end signatures per arm (`x4_headless._derail_reason` over each lane's `stdout.txt`); for every signature in at least 2 B runs and 0 A runs, the last ~200 debug-log lines before each of those derails, scanned for a package tag (`[ITEM] using`, `[DBLITEM]`, `[KIT-BUY]`, `why=topoff`, `[KEYBATTLE]`, `[DEXCATCH-NOBAIL]`, `[CATCH] trainee`) | the signature, its runs and the tags found; "STOP-3 pattern: yes / no" |

## T4b — `tools/story-dev/batch14_tables.py` (the DESCRIPTIVE tables; no verdict word anywhere)

Per arm, from the same runs:

| table | content |
|---|---|
| **D-funnel** | runs started → met X → beat X on the first try → beat X eventually, for EVERY key trainer (not only K\*); attempts before an honest stop; badges reached; frames to each badge; frame-cap ends; cut and lost runs |
| **D-attempt** | won / (won + lost) per attempt, per key group |
| **D-boss** | Tate & Liza, Winona, Norman and Juan: first-attempt rates with run counts; the Elite Four as "NOT ASSESSED (n)" |
| **D-lead** | the share of key first attempts whose lead (the first `[TURN]` own species) was caught in that run after the Stone Badge, plus C2's per-trainer rates without them. Labelled "conditioned on a post-treatment variable" |
| **D-loss** | Lost + Draw split three ways: non-key trainer battles, wild catch battles (`[CATCH] end … end=lost`), other wild battles. Victory Road battles by map |
| **D-leg11** | runs that loaded EVER GRANDE CITY (16,10), and the money-refusal derails matching BOTH texts (the old "the basket costs ₽…" and the current "the missing basket lines … short by") |
| **D-fence** | `[DEXFENCE]` reasons as DISTINCT (species, reason) pairs per run, numbers stripped, by era (before / after Sootopolis), labelled "distinct pairs, not frequency" |
| **D-economy** | `[BALLS-BUY]` lines: BOTH prefixes, `why=topoff…` by ball with ₽ spent, `why=mandatory`; `[KIT-BUY]` by item; T1 `delta` per map; money at leg 11 |
| **D-rare** | `[CATCH]` battles and their ends per rare species (the ` rare=` suffix in B; arm A has none, so A is joined offline through `sandbox-pokebot/modules/rarity.py`) |
| **D-M1b** | `[DMGAUDIT]` samples pooled over both arms, de-duplicated by content, written as one file `audit_damage_calc.py` can read (or its pooling), with the sample count |
| **D-weaken** | `[WEAKEN-OBS] would=` counts by stage, per arm |
| **D-throughput** | frames per run, runs per lane-hour per arm (from `summary.json` spawns), log sizes, any capped log |

## The gate — `tools/story-dev/probe_batch14_checks.py` (appended to `run_gates.py`)

- **Rows on REAL line shapes,** quoted from committed evidence or the smoke and path-test batches, with the same
  provenance check `probe_compare_arms.py` uses.
- **One row per E rule in BOTH directions:** a planted violation is reported, and the clean case reads PASS. E4 reads
  NOT ASSESSED below 5 runs. E5 lists without counting.
- **STOP-3:** a planted B-only signature with a package tag in its tail reads "yes"; the same signature in an A run too
  reads "no".
- **T4b:** each table's counts on a hand-built fixture match exact numbers. D-fence prints its "not frequency" label;
  D-lead prints its post-treatment label.
- **Mutants with exact red sets** (as in `probe_compare_arms.py`), then an INDEPENDENT adversarial pass, as always.

## PREDICTIONS

| # | Run | Prediction | Falsified by |
|---|---|---|---|
| T4-1 | `probe_batch14_checks.py`; `run_gates.py` | every row passes; every mutant reddens exactly its set; the full suite passes | any FAIL |
| T4-2 | an independent adversarial pass | every non-equivalent mutant of an E rule, of STOP-3's 2-vs-0 test and of a table's count reddens a row | a non-equivalent survivor |
| T4-3 | `batch14_checks.py` on the SMOKE batch `x4-runs/20261001-090649` (15 min, early game) | E1 PASS (0 non-key item uses in B); E2 PASS; E3 PASS on its arm-identity half (the live monitor saw 0 hits), and the Rustboro heal half holds on every B lane that healed in Rustboro (T1-4 saw `why=topoff` and `[KIT-BUY]` on 8 of 8); E4 NOT ASSESSED (no Tate & Liza); E5 nothing listed; STOP-3 "no" (no run ended) | any FINDING; E4 assessed |
| T4-4 | `batch14_tables.py` on the same batch | it runs and prints every table; D-funnel shows Roxanne met by 8/8 per arm with first-try wins A 7, B 7 (as T3 found); D-boss and the Elite Four read NOT ASSESSED; D-leg11 has 0 runs at (16,10) | a crash; numbers that disagree with T3's |

## GRADED (2026-10-01, ~2:15 PM LA; T4 DONE: built `ca9e5510`, attacked, folded `c4c0bc78`)

⛔ **Headline: T4-2 FAILED AS FILED. The independent pass found 21 non-equivalent survivors and a STOP-3 that could
not tell a package fault from a coincidence; all of it is folded.** T4-1, T4-3 and T4-4 held. None of the findings
blocked the night batch, because T4 only READS its logs.

| # | Grade | What the evidence shows |
|---|---|---|
| T4-1 | **HELD on its final runs, with a caveat** | After the fold: `probe_batch14_checks.py` ALL PASS (78 rows, 141 mutants, 105 quoted lines); the full suite, re-run by the coordinator on the folded worktree: `ALL 140 ENFORCING GATES PASS (595.8s total)` (144 entries). ⚠ The mutants' expected red sets were the builder's own predictions: 77 of 91 matched on the build's first run and 136 of 141 on the fold's first run. Each miss was read and its set corrected (they are marked FOLD-PREDICTION in the gate), so "every mutant reddens exactly its set" is a property of the corrected sets, not of the first guesses. |
| T4-2 | **FAILED AS FILED** | Evidence: `tools/story-dev/evidence/2026-10-01-batch14-T4-ADVERSARIAL.txt`. The mutant hunter tried 83 mutants and killed 51, leaving 21 real gaps plus 5 builder survivors. Of the gate's 8 mutants predicted to redden nothing, 5 were not equivalent. After the fold, the coordinator re-ran the hunter's own mutants against the folded code (`rehunt.py`, scratch): 21 KILLED. The 5 survivors are the 5 the hunter itself called equivalent. 6 anchors were rewritten by a ruling, and their twins are killed in the gate. |
| T4-3 | **HELD** | Smoke batch `20261001-090649`: E1 PASS (132 B non-key battles, 0 violating lines); E2 PASS (149 `[KEYBATTLE]` lines, 0 violations); E3 PASS, with its headline now carrying "loss-filing half had 0 trials" (Rustboro heal: 8 of 8 first heals logged both lines); E4 NOT ASSESSED (0 qualifying runs); E5 NOT ASSESSED (0 `after` readings, so nothing listed); STOP-3 no (0 non-finished run ends). The independent re-computation found no disagreement. |
| T4-4 | **HELD** | D-funnel: ROXANNE met 8/8 per arm, first-try wins 7/8 in each, equal to `compare_arms`. D-boss: Tate & Liza, Winona, Norman, Juan and the Elite Four NOT ASSESSED (0). D-leg11: 0 runs at (16,10) in either arm. No crash. |

### What the independent pass changed (the coordinator's rulings, binding on the fold)

1. **STOP-3 counts ACTING package tags only** (spec reviewer F3, plus a correction the coordinator read from the emit
   sites). The filed list matched lines that record the package deciding to do nothing, and those print at almost
   every B heal. The pinned list and its reason are in DESIGN §4. The tool also prints how many qualifying signatures
   had no acting tag.
2. **E4 is graded on the qualifying Tate & Liza FIRST attempts** under DESIGN §5's corrected falsifier (the builder
   found the filed one inverted). On a zero it lists each own battler's lowest HP fraction. A battler at or below 0.35
   while holding an HP item makes the status `FINDING (READ BY HAND)`, carrying production's rule-3 caveat (a heal
   into a losing race is declined). `choose_healing_item` is NOT simulated.
3. **E5 lists every partner rise.** A same-turn use on the partner is printed as context and never used to exclude.
4. **D-economy has one package ₽ row, de-duplicated per errand.** The filed tables added a joint ball+kit errand's
   money to both rows. On the smoke batch: B ₽35,500 over 28 paying errands, 6 of them joint, which matches the
   independent re-computation.
5. **Momentary map reads are ignored** in E3's errand window and D-fence's era. A read to (255,255) or (3,0), or one
   reverted within 2 frames, is not an arrival.
6. **E2 tallies `key=` on fail-open lines** and never compares it.
7. **Headlines carry their caveats.** Both tools print the `C1-C2 VOID` line, and both accept `--void`.
8. **D-rare** prints both arms under one species-level rule. **D-lead's** label adds "evolved catches are missed".

### The builder's choices where the rulings were silent (each visible in the code's comments)

- A qualifying E4 battle with no own-battler HP read also reads `FINDING (READ BY HAND)`.
- "HP item held" means the start bag held one.
- Battlers are named by species, since `[TURN]` lines carry no PID.
- E5's context is a `use` on the partner whose decision turn equals the reading's.
- Package errands are the `why=topoff…` and `why=kit…` lines with money spent above 0; `mandatory` is not package.

### Deviation from this note's header

The header says T4 is merged "only after the batch ends". It finished BEFORE the 9:00 PM freeze, so it is merged
before it. It changes only `tools/story-dev` and documentation. The merge is checked to leave `sandbox-pokebot/`
byte-identical (`git diff --stat` empty), so the batch runs the same code either way.

### Next

The batch grade after the batch ends (~10:00 AM LA 2026-10-02). Run `compare_arms.py`, `batch14_checks.py` and
`batch14_tables.py` on the batch stamp, then write `2026-10-0X-batch14-GRADED.md`.
