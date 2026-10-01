# 2026-10-01 — design v2 step 14 (the Phase 3 batch A/B): recon angle `adversary`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `step14-batch-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Step 14 adversarial review (read-only note, worktree 28db1cf0)

**Verdict:** the batch should not be started on the spec as written. Five blockers would let it produce a misleading result, a vacuous one, or one that cannot be attributed to an arm. Each has a cheap fix. "Verified" means I read the file or line myself; "Inferred" means it is reasoned from code or notes and was not run.

## Blockers

**K1. If the A/B is split per lane on 4 lanes, the arm is confounded with the starter.**
- Verified: every lane pins one starter (`sandbox-pokebot/modules/endless_x4.py:53`, P1 Torchic, P2 Mudkip, P3 Treecko, P4 random). Any 2/2 split gives the two arms different starters.
- Verified: starter effects are large and documented (`tools/story-dev/x4_headless.py:114-116`: Treecko stalls at Wattson in 11 of 14 runs, Mudkip never does). The batch0927 end classes also differ by lane.
- Mitigation: never run 2 lanes per arm on 4 lanes. Use one of these instead:
  - 8 concurrent lanes, so each arm gets one lane per starter. `x4_headless.py --lanes 8` already cycles starters this way (`:111-113`).
  - Alternate the arm per run inside each lane. Every B flag is read per run or per call (`story_mode.py:2432-2459`, `:825`, `:880`; `higher_level_actions.py:526,533`), but the switch must happen before the run's debug log opens, so the header shows the right arm.
  - Two full 4-lane batches (but see S11).

**K2. Arm B's environment cannot be executed as written.** "OPENFENCE per the Phase 3 plan" names more than one plan.
- Verified: the R20 Phase 3 arm A2 is "B, P2-a, P2-a2, P2-b and P2-c on" (`ai-research-notes/2026-09-27-ruling20-phase2-BUILDSPEC.md:136-140`). That would also turn on `POKEBOT_R20_TEAM6` and `POKEBOT_R20_HUNTFIRST`, which step 14 does not list.
- Verified: the Phase 1 design's Phase 3 has its own arms (A0/A1/A2) and its own primary metric, the finish rate plus a per-rung funnel (`2026-09-27-ruling20-phase1-DESIGN.md:236-262`).
- Mitigation: write each arm as a literal, complete dictionary of env vars, including `POKEBOT_FODDER_RULE`. `POKEBOT_RNG_DECORRELATION_FRAMES` must be unset in both arms: a fixed value makes every run identical (`modules/story/intro.py:81-89`).

**K3. OPENFENCE in arm B confounds the acceptance metric (key-battle win rate).**
- Verified: lead choice ranks `incoming` damage above level (`modules/story/team_policy.py:291-297`).
- Verified: "a fresh catch leads … the spec's §5 OPEN risk" (`2026-09-28-r20P2b-GRADED.md:45-46`). It was seen live: an L8 Taillow led against the L13 rival Wingull (`2026-09-29-r24catchtrain-GRADED.md:~21-24`).
- Verified: `#24-partycap` cost 36 points of finish rate (registry `29:167`).
- Inferred: B's key battles would partly measure lead choice, not items. And if B collapses at the Surf rung, its late key groups are only the strong survivors, which inflates B's rates.
- Verified: the R20 plan assumed about 50 runs per arm per 12 h × 4 lanes (`2026-09-26-rulings19-20-PLAN.md:73-74`). Measured throughput is 35 runs **in total** per 14 h × 4 lanes (batch0927 FINAL `:75`).
- Mitigation: take OPENFENCE out of step 14 and run the R20 Phase 3 with its own primary metric. The alternative is a third arm C (B without OPENFENCE).

**K4. Nothing in the analysis checks which arm a log belongs to, and the environment leaks into lanes.**
- Verified: both launchers copy the parent's environment (`endless_x4.py:173`; `x4_headless.py:628-629`).
- Verified: each log header records every `POKEBOT_*` var on an `env-all:` line (`modules/debug_logger.py:~259-267`). But `battle_log.scan_logs` selects only by day and lane substring and never reads it (`tools/story-dev/battle_log.py:741-757`).
- Verified: this repo's own A/B launcher warns that an inherited var makes both arms ON, and that the result then reads as "the feature does nothing" (`Run-Maintain-AB-Batch.bat:15-21`).
- Mitigation:
  - A launcher that clears every `POKEBOT_*` and then sets the arm's allowlist.
  - Extend `x4_headless.check_headers` (`:~655`) to assert `env-all` equals the arm's dictionary live, aborting a wrong lane early.
  - Give the probes an `--expect-env` option that refuses any mismatched log.

**K5. Selecting logs by day merges batches and arms. This has already happened.**
- Verified: the itemprobes "batch0927 corpus" (window 20260927..28, 40 logs) includes 5 batch0926 logs: P1 002315 and 030532, P2 004830, P3 022041, P4 010740. batch0926 ran until 03:29:07 on 09-27 (`2026-09-26-batch0926-FINAL.md:~28`). So I2's "114 requests" (`2026-09-30-itemprobes-DESIGN.md:63`) is not batch0927's figure.
- Verified: the day is the only time key in the selection (`battle_log.py:748-752`; `analyze_endless_batch.py:392-393`). Two back-to-back batches would mix on the changeover day.
- Mitigation: select by `env-all` + build + `HHMMSS` start stamp, or by x4_headless stamp folders.

## Should-fix

**S1. The acceptance test has no primary statistic, margin, sample size or power, so "not lower" cannot fail meaningfully** (spec `:702`).
- Verified: about 35 runs per 14 h, of which only 30 have distinct teams (FINAL `:11`, `:350`). 17 of 31 ended runs reached 6 or more badges (FINAL `:78-81`). There was 1 Elite Four entry in 35 runs.
- Inferred: two batches give about 17 Tate & Liza first attempts per arm; a per-lane split gives about 8. At 17, a 95% CI is roughly ±20-24 points.
- Mitigation:
  - Primary metric: the per-trainer FIRST-attempt win rate, stratified by opponent with fixed weights.
  - State the smallest detectable difference and the non-inferiority margin up front. The project's own rule says this ("State the power honestly", phase1-DESIGN `~:262`).
  - Treat the Elite Four group as descriptive only.

**S2. Survivorship and mix of trainers.**
- Verified: the per-group table pools all trainers (`battle_log.py:649-657`) and has no runs-started denominator.
- Inferred: B's funnel will differ. KEYITEMS removes items from ordinary battles, and "67 of 96 uses" were there, "many in Victory Road, which has no Poké Center" (spec `:815`). The catch flags' whiteout loops were accepted (`r25cap-GRADED.md:56-69`).
- Mitigation: report per arm the funnel (runs started → met X → beat X first try → beat X eventually), plus "runs that beat X / runs started".

**S3. An accounting difference changes how many attempts each arm gets.**
- Verified: with CATCHHURT on, the C4 change files lost dex catches outside `_defeat_counts` (`29:171`). Without it, catch losses count toward the boss on that map (`r24oversurvival-GRADED.md:50-52`).
- Inferred: arm A gives up on bosses sooner, so B's "eventually won" and per-attempt rates rise from bookkeeping, not items.
- Verified: in both arms a Draw is not counted as a defeat (KI-116, `05:3257`). Tate & Liza loops dominate per-attempt rates (158 defeats; one run had 28, `battle_log.py:584`).
- Mitigation: make first-attempt the primary; report "attempts before honest stop" on its own.

**S4. Repeated trajectories are not independent samples (KI-112 cuts both ways).**
- Verified: the seed spread is 0-120 frames, about 121 seeds (`06:708-716`; `intro.py:78-89`). The chosen value is printed to stdout only, not the debug log (`intro.py:181-186`).
- Inferred: P1r1 = P1r3 = P1r7 being identical is about 1% likely with 121 seeds, so the effective seed count may be smaller.
- Inferred: M1b's "300 clean samples" would double-count replayed runs. `audit_damage_calc.py:1054` also reads only one log at a time.
- Mitigation: cluster runs by trajectory (starter PID or the Stone Badge PID set), report the number of distinct runs, and bootstrap at run level. De-duplicate M1b samples by content. Optionally, give both arms the same list of seeds so runs pair up.

**S5. The `heal_stock` field is the raw bag, including the reserved League basket.**
- Verified: "Raw bag on purpose — no RULING 18 reserve filter" (`modules/story/trainer_identity.py:199-206`).
- Verified: the reserve is armed from `SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` until the Elite Four (`league_reserve.py:47-49`, `:129-141`), and in-battle use cannot spend it (`:153-171`).
- Inferred: at Juan and Victory Road the field is swamped by unusable items. Elsewhere "B has more" is true by construction.
- Mitigation: compute usable stock as raw minus `basket()` while the reserve is armed. Report it by attempt index (to see Tate & Liza loops draining the kit). Downgrade it to a manipulation check.

**S6. "0 `[ITEM] using` in non-key battles" contradicts the merged fail-open gate.**
- Verified: the gate fails open (`trainer_identity.py:70-79`; `29:184`). An item allowed on an unreadable read in a battle the offline classifier calls non-key would show as a false failure.
- Verified: the offline and online sides use the same `KEY_TRAINER_CLASSES` (`battle_log.py:83-103`). So "agreement" catches read failures, not a wrong key set.
- Mitigation: exempt `reason=FAIL_OPEN(...)` battles and list them; report unclassified battles apart.

**S7. The "fewer reserve refusals" prediction is fragile.**
- Verified: the only restock points are Rustboro and Sootopolis (`29:194`); a mid-game one is "named for later" (spec `:717`). B's other flags admit more catches. v1 itself predicted lifted refusals convert into reserve refusals (`2026-09-28-r23-25-DESIGN.md:~394`).
- Verified: `[DEXFENCE]` logs once per (species, reason) per run (FINAL `:406`), and RARE's later admissions log nothing (`r25cap-GRADED.md:70-72`).
- Mitigation: count per encounter from `[DEXCATCH]`, split by era (early, mid-game, after Sootopolis), and predict a direction per era.

**S8. Run length and censoring.**
- Verified: the base cap is 7,000,000 frames until §Ch23 (`story_mode.py:7255`, `:7284-7294`). 8-badge runs took 4.68-7.05M frames, and P1r2 hit the cap (FINAL `:78-81`).
- Inferred: B's extra catches, errands and ordinary losses push more runs over the cap. That censors late key battles in B only.
- Mitigation:
  - Pre-register frames to each badge and frame-cap ends per arm.
  - Give each arm equal lane-hours (`x4_headless --minutes/--runs`, `:965-1008`), or run concurrently so a user park cuts both arms equally.
  - Count battles from in-progress runs, and report how many were cut.

**S9. There is no interim safety read or stop rule for a 12-14 h spend.**
- Verified: DOUBLEITEMS was graded on one trajectory per family, at a heal threshold of 0.8, not the default 0.35 (`doubleitems13-GRADED.md:40`, `:65-66`). Why battler 0's first A press is dropped is unexplained (`:67-71`).
- Inferred: in the batch it would run hundreds of times at Tate & Liza.
- Mitigation: run a 1-2 h B smoke test, or read the batch at about 2 h. Count `never reached index`, `KI-47 PARK`, `[DBLITEM] err`, `menu … ok=0`, `topoff-failed`, and frame caps, against pre-registered abort thresholds.

**S10. B's definition depends on unanswered user questions.**
- Verified: Q1 (ball amounts, `29:194`) and Q3 (key set, `06:8270`, `06:8280`) are still pending. The spec says "as answered by Q3" (`:698`).
- Mitigation: ask Q1 and Q3 first, or state which result rows a different answer would invalidate.

**S11. Two separate batches add a time/build confound and a code freeze of about 28 h.**
- Verified: lanes respawn against on-disk code (`endless_x4.py:203-227`), and the `build:` header changes on docs-only commits (`batch0926-FINAL.md:9-15`).
- Verified: the profile state that drifts unexplained across forks (264 vs 253 battles) carries over between arms (handoff, the P4 note).
- Mitigation: check that `git diff A..B -- sandbox-pokebot` is empty; snapshot and restore the lane profiles' save and stats files before each arm.

**S12. The baselines conflict.**
- Verified: three figures exist for batch0927 item use: 93 (67 + 26), 96 (spec `:703`, `:815`) and 114 (I2, contaminated, see K5).
- Mitigation: grade B against the concurrent arm A only; use batch0926 and batch0927 as context, re-derived with exact timestamps (from `081744` onward).

**S13. Ordinary-battle whiteouts have no prediction, and two mechanisms are mixed together.**
- Verified: whiteout-recovery lines are unreliable for attribution (44 of 769 were delayed, FINAL `:310`).
- Mitigation: count Lost/Draw per battle, split into non-key trainer battles (the KEYITEMS effect) and wild catch battles by `[CATCH] kind` (the catch-flag effect). Pre-register a harm threshold.

**S14. Several secondary metrics have no tool.** Nothing batch-level reads `[BALLS-BUY]` or `[KIT-BUY]`; only gates do. Write those counters, gated, before the batch.

## Nits
- **N1.** x4_headless profiles are named `endless-H*` (`x4_headless.py:131-143`), but `scan_logs` looks for `endless-P*` (`battle_log.py:741`). Use stamp mode. `x4_logs` matches `L0*` only (`:767`), which breaks at 10 or more lanes.
- **N2.** DMGAUDIT made up 50,901 of 112,725 bytes in the M1b ON log (88 lines, about 578 bytes each). Inferred: about +5-7 MB on long runs, still under the 30 MiB cap. Past that cap, battle events are silently dropped after a single marker line (`debug_logger.py:44`, `:463-468`). Flag any log that contains that marker.
- **N3.** Known probe limits, descriptive only: a doubles `[TURN]` line names only the left foe; identical duplicate foes can read as a heal; each decision prints 2-3 identical `[TURN]` lines (`itemprobes-DESIGN.md:91-93`).
- **N4.** The Space Center multi is a key battle but outside DOUBLEITEMS' scope. Report it separately from the Magma/Aqua group.
- **N5.** Pre-register that `[DBLITEM] use` at Tate & Liza is greater than 0. Zero means the doubles part is vacuous, not a "no effect" result.
- **N6.** DMGAUDIT and weaken-observe are wrapped in try/except (`dmgaudit.py:40-45`, `:130-180`), so a behaviour change is unlikely. They do cost wall time per turn, so measure lane throughput.
