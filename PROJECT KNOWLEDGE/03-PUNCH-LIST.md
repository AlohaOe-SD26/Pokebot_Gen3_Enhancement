# Punch List â€” Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue.
> Item format: `- [ ] #N â€” description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).
> Full future-idea catalog: `09-FEATURE-BRAINSTORM.md`.

### Marker states (documented 2026-07-27 — the file uses THREE, not two)
| marker | meaning | count |
|---|---|---|
| `- [ ]` | open — not started, or started and not landed | 80 |
| `- [~]` | **partial** — built but not fully verified/promoted, or v1 done with follow-ups | 17 |
| `- [x]` | done | 37 |

‼ `- [~]` is load-bearing and was previously undocumented: several `[~]` items read as
"DONE" in their text (e.g. `#24-move`, `#24-resume`) while still carrying open follow-ups.
Do not treat `[~]` as either finished or unstarted without reading the entry.

**Status audit 2026-07-27** (`#doc-audit-1`, partial — see `#doc-audit-2`): 98 distinct
`#`-ids carry a checkbox; exactly **one** id had a genuinely conflicting status
(`#24-pokenav-faithful`, now cross-linked — it is a legitimate RECURRENCE, not a
bookkeeping error). No item marked `[x]` was found whose code is missing. A full
open-vs-built sweep of all 80 open items has **not** been done.

## Now (active focus)

### ‼ SESSION END 2026-08-05 — THE CURRENT TOP OF THE LIST
Full state + rationale in `04-HANDOFF.md` "YOU ARE HERE". Suite 78/78; last batch 52.0%.

- [x] `#24-partycap` — **MEASURED AND REVERTED 2026-08-05. DO NOT RAISE THE CAP AGAIN.**
      Batch `20260805-122057` (`be104e9c`, VERDICT OK, 0 violations): **52.0% → 15.8%**.
      The badge funnel put the ENTIRE loss on one rung — **Balance→Feather 76% → 21% (z=3.06)**
      — with every earlier rung flat, so **a deeper team is FREE through five badges**.
      Cause is **HM coverage, not strength**: 10 of 16 non-finishes are `No party mon can learn
      Surf and the party is full` (**0 occurrences in all 14 prior batches**). The empty slots
      are the RUNWAY that HM/counter catches land on — at cap 4 the team still reaches a mean
      **5.85** by Feather. Both constants back to 4, each with a do-not-raise comment.
      Full detail: `07-CHANGELOG.md` + `08-MISTAKES.md` 2026-08-05.

- [ ] `#24-hmslots` — **NEW, NEEDS A USER RULING. The real lever behind `#24-partycap`.**
      The user wants visibly deeper teams; the cap is the wrong way to get them. Options:
      **(1) reserve slots** — keep the wild fill at 4 and let HM learners / counters claim the
      rest (what already happens organically, 4.00 → 5.85); lowest risk, arguably already done.
      **(2) make room on demand** — let the HM path deposit a non-essential mon so a Surf
      learner can board. ‼ This is what the guard's own message asks for ("needs PC box
      management") but it is the shape of `POKEBOT_PC_ROTATION`, **disabled for costing ~19
      points by depositing team members** — read that before building it.
      **(3) cap 5** — one free seat for the Surf learner; plausible, unmeasured, needs a batch.

- [ ] `#24-pcoverflow-proof` — **STILL UNPROVEN, and batch `20260805-122057` could not prove it.**
      `withdrawing` logged **0** times all batch: the Surf guard derailed runs before any
      full-party catch reached the box-overflow path. Bundling it with the cap measured the
      BUNDLE, not the part. It needs its own targeted probe from a save with a full party.

- [x] `#24-pcoverflow` — **BUILT 2026-08-05** (user ruling: build the real thing, not a raised
      constant). `resource_blocker` no longer refuses a full party (ball gate untouched);
      `pc_trip.box_views/find_in_box/withdraw_from_box` read the PC, find a mon **by PID**, and
      collect it at the next heal. Frees exactly ONE slot, never deposits its own target.
      `repro_pc_overflow.py`. **NOT live-proven.**

- [ ] `#24-cavethread` — **THE BLOCKER FOR ALL STORY CONTENT PAST WINONA.**
      ‼ **RE-SCOPED 2026-08-05 — DO NOT BUILD THE CHAIN TABLE YET. MEASURE FIRST.**

      The item used to read "`_CAVE_EXITS`/`_CAVE_ENTRANCES` are SINGLE-HOP, therefore build a
      multi-hop chain table". **The premise behind that conclusion is stale.** Those two tables
      date from 2026-07-26 and their justifying comment says *"the global navigator can NOT
      cross warp levels"* — which was true then and **was fixed on 2026-07-31 by `#24-journey`**.
      `navigate_to_anywhere` is now a multi-hop, self-replanning, live-validated warp navigator,
      and `_navigate_riding_out` (what the training/hunting paths already call) wraps it.

      **STATIC RECON DONE (2026-08-05, no emulator** — replayed `WarpGraph.map_route` against
      the committed ROM cache `cache/warp_graph_BPEE0.json`; script in the changelog entry):
      the graph **already knows every route in question, in BOTH directions** —
      | route | hops |
      |---|---|
      | `ROUTE106 -> GRANITE_CAVE_B2F` | 3 |
      | `GRANITE_CAVE_B2F -> DEWFORD_TOWN` (the leg that dropped 2 real-HW runs) | 4 |
      | `ROUTE122 -> MT_PYRE_SUMMIT` | 3 |
      | `JAGGED_PASS -> MAGMA_HIDEOUT_4F` | 4 |

      ‼ **WHAT THIS DOES AND DOES NOT PROVE.** It refutes "the route data is missing" — the
      thing a hand-built chain table would supply. It does **NOT** prove the bot can WALK it:
      `map_route`'s own docstring warns its connection edges can be **PHANTOMS** (the measured
      Verdanturf->Route116 case). Route known ≠ route walkable. That is the same
      one-measurement-fits-all error KI-39 already cost this project a day on.

      **THE REAL RISK, NAMED:** `_walk_warp_chain` documents a **ONE-WAY LEDGE** on Granite Cave
      1F — within-floor reachability is **DIRECTIONAL**, so the graph's single `GRANITE_CAVE_1F`
      node is really two disjoint sections, which a MAP-granular planner cannot see. The generic
      navigator's `used_warps` + revisit-deprioritisation is a *plausible but unproven* mitigation.

      ⏭ **NEXT ACTION — run the probe, it is already written** (`--driver cavethread`, added to
      `story_harness.py` 2026-08-05; destination tiles come from the warp graph's own ROM
      `to_coords`, so nothing is guessed):
      ```
      cd tools/story-dev
      PYTHONUTF8=1 py -3.12 story_harness.py saves/dewford.ss1 --driver cavethread \
          --frames 600000 --profile repro-cave1
      ```
      **Granite Cave is the deliberate test case, not a convenience:** same 3-warp depth as Mt.
      Pyre Summit, already parked for this, and it carries the hardest known hazard (the ledge).
      If the generic navigator threads Granite Cave in AND back out, `#24-cavethread` collapses
      from "build a chain system" to "delete the two stale tables" — and Mt. Pyre unblocks.
      If it fails, the log names which leg and where, and THAT is the thing to fix.
      ‼ Needs the box; do not run it while a batch is using the lanes.

- [ ] `#24-mtpyre` — first chapter past Winona. 3 hops, one branch; the 2F-6F tower is a
      skippable side dungeon. Blocked on `#24-cavethread`.

- [ ] `#24-magmahideout` — **DEFERRED.** Door at JAGGED_PASS (16,18) is unreachable from the
      ROUTE112 side (one-way ledges; a 2026-07-26 probe already failed to path there). Only
      approach is ROUTE112 → cable car → MT_CHIMNEY → descend ⇒ ~8 warps + a scripted ride.

### ‼ THREE FLAGS THAT MUST STAY `0` (each hides a MEASURED regression)
`POKEBOT_LEAD_DEMOTE_WONDER_GUARD` (~20 pts) · `POKEBOT_AREA_ITEM_GATE` (~7 pts) ·
`POKEBOT_PC_ROTATION` (~19 pts of the last rung). All three REMOVED something and were
justified by counting failures without counting successes. Do not re-enable without a batch.



### ‼ READY TO APPLY THE MOMENT BATCH `20260802-160603` LANDS (~19:06 PDT 2026-08-02)

- [ ] `#24-leadcounter` — **USER RULING 2026-08-02: super-effectiveness outranks raw level
      ONLY for a mon the counter chain caught for THIS boss.** Not a general rule (that option
      was offered and declined; so was the level-gap variant, which is option (b) of
      `#24-leadpolicy` and was already ruled out). Rationale + rejected alternatives in
      `06-DECISIONS-LOG.md` 2026-08-02.

      **THE EXACT CHANGE:**
      1. `team_policy.lead_rank_key()` gains an OPTIONAL `is_hunted_counter: bool = False`,
         and the key becomes:
         ```python
         (glass_wonder_guard, not can_attack, incoming, not is_hunted_counter, -level)
         ```
         ‼ **AFTER `incoming`, BEFORE the level tie-break.** It promotes the counter over an
         EQUALLY SAFE mon; it must never let a 4×-weak counter lead. Getting this backwards is
         the plausible way the fix becomes a new bug — `repro_lead_hunted_counter.py` check 3
         pins it.
      2. `best_lead_index()` passes the candidate's `is_hunted_counter` through.
      3. Record WHICH mon was hunted for this boss. `StoryMode._counter_hunts[key]` already
         tracks the attempt; store the caught mon's **PID/personality value**, not its slot —
         a party index goes stale the moment anything reorders or deposits (the same hazard
         `pc_trip` guards against).
      4. `early_game._lead_best_matchup()` takes an optional `hunted_pid=None` and sets the
         term for the matching party mon; the Norman/Wattson/Winona prep passes it.
      5. `repro_lead_hunted_counter.py` goes green (currently RED by design). Re-run the suite.

      **Why it matters:** batch5 caught, travelled for and trained a counter to L29 and then
      led **Marshtomp L35** instead, because Machoke and Marshtomp tie on every term the key
      measures and level breaks it. The chain only fires after ~6 losses, so for that boss the
      strongest mon is already PROVEN insufficient.

### ‼ BATCH 5 LANDED — the blocker moved a THIRD time, to the LEAD

- [x] `#24-leadpolicy` — **A+C BUILT 2026-08-01.** Pure `team_policy.lead_rank_key()` /
      `best_lead_index()`; `_lead_best_matchup` defers to it. Sort terms not filters (a lone
      Shedinja is still led); both predicates fail SAFE. Option (b) NOT ruled, NOT built —
      `repro_lead_policy.py` check 4 pins the unchanged Whismur-over-Marshtomp behaviour.
      ‼ **MEASURED LIMIT (check 5): this does NOT field the trained counter.** On batch5's
      real party it stops the Shedinja lead and then picks **Marshtomp L35 over Machoke
      L29**, because `can_attack` is binary and 2× STAB earns no credit. **OPEN DECISION —
      should super-effectiveness outrank raw level? That is a NEW question outside A+C and
      is the last link in the chain.** Original diagnosis below.

      `#24-leadpolicy` — **the counter chain's blocker as of batch5. Ruling A+C.** Batch5 proved the chain works end to end — 7 of 9 counters trained,
      `Machop L15 -> L29` evolving to **Machoke** — and then **MACHOKE WAS LED INTO NORMAN
      ZERO TIMES**. Leads chosen: SHEDINJA ×9, MARSHTOMP ×4, SWAMPERT ×4, BLAZIKEN ×2.
      `_lead_best_matchup(["Normal"])` scores `min(incoming_multiplier, -level)`, so Shedinja
      (Bug/Ghost, Normal → 0×) always wins and the trained counter sits in the bag. The entry
      below PREDICTED this exact batch. Catching and training a type counter and then not
      fielding it is the cost of the whole chain with the benefit of none of it.
      **Build (a) require the lead to also have a ≥neutral attacking option + (c) special-case
      1-HP Wonder Guard mons.** ‼ Then size expectations before re-measuring: the chain fires
      on only ~10 of 29 Heat-reaching runs, so even a perfect fix moves the overall
      Heat→Balance rung 79% → ~93% AT BEST. Use the **counter-hunt-runs-only** conditional as
      the instrument (batch4 5/9 → batch5 6/10, z=0.20 — the whole-batch rung dilutes it 3:1).

### ‼ APPLIED 2026-08-01 AFTER BATCH `20260801-075805` LANDED

- [x] `#24-relocfloor` — **DONE 2026-08-01.** Extracted as the pure
      `training_areas.relocation_floor(local_max, trainee_levels, gap)` and wired into
      `_prepare_for_fight`. Repro green, full suite 69/69. Original diagnosis below.

      `#24-relocfloor` — **the training-relocation floor is keyed on the WRONG MON.**
      Diagnosed + repro'd 2026-08-01; the code edit was deliberately held because
      `x4_headless.py:843` relaunches a dead lane's process and a restarted lane would
      re-import mid-batch, mixing two code versions into one measurement.

      `story_mode.py` `_prepare_for_fight`:
      ```python
      floor = max(local_max, team_max_now - self.FODDER_LEVEL_GAP)
      better = best_training_area(team_max_now, min_wild_max=floor, allow=_allow)
      ```
      `team_max_now` is the party's STRONGEST mon, but `need` (the mons being trained) is
      the stragglers — a real batch4 Norman party is `Marshtomp L35 / Ninjask L30 /
      Swellow L32 / Poochyena L12 / Shedinja L20`. Keying the floor to L35 demands wilds
      above L23 and so rejects **ROUTE111 (L19-22)**, the one reachable area, though it is
      near-ideal for a L20 trainee. Measured: `no better area is available` fired **167×**
      in batch4, every one `local grass (max L4)` (ROUTE102), teams L32-41.

      ‼ **ONLY THE FLOOR IS WRONG — do not "key it all to the trainee".** `train_team` runs
      with SWAP-TRAIN on, so a STRONGER team-mate does the fighting; the winnability/scoring
      argument (`best_training_area`'s first parameter) is correctly `team_max_now`.

      **THE EXACT CHANGE:**
      1. Add to `modules/story/training_areas.py`:
         ```python
         def relocation_floor(local_max: int, trainee_levels, fodder_gap: int) -> int:
             """Minimum wild level worth relocating FOR, keyed to the mons being trained."""
             if not trainee_levels:
                 return local_max
             return max(local_max, max(trainee_levels) - fodder_gap)
         ```
      2. In `story_mode.py` `_prepare_for_fight`, replace the `floor = …` line with
         `floor = relocation_floor(local_max, [party[i].level for i in need], self.FODDER_LEVEL_GAP)`
         (leave `best_training_area(team_max_now, …)` unchanged).
      3. `repro_relocation_floor_wrong_mon.py` check 4 goes green. Re-run the full suite.

      **Effect, measured with the real tables** (`allow` restricted to what is reachable
      near Petalburg):
      | party | floor now | pick now | trainee floor | pick |
      |---|---|---|---|---|
      | L35, stragglers L12/L20 | 23 | **None** | 8 | **ROUTE111 L19-22** |
      | L36, straggler L12 | 24 | **None** | 4 | **ROUTE111 L19-22** |
      | L33, stragglers L20/L27 | 21 | ROUTE111 | 15 | ROUTE111 |

      ‼ **NECESSARY BUT PROBABLY NOT SUFFICIENT AT PETALBURG, and say so rather than
      overclaim.** When every richer area is reachable both floors agree and the fix changes
      nothing. From Petalburg even ROUTE111 is often unreachable — which is why some L32-34
      runs refused too. Its real value is unlocking the agreed **pre-emptive training** plan
      (train near Lavaridge, where ROUTE111/ROUTE117 demonstrably ARE reachable, before
      travelling to Petalburg at all). Expect little from this fix alone in a batch.

### ‼ BATCH 4 LANDED 2026-07-31 23:15 — the counter chain's blocker MOVED to KI-44

- [x] `#24-counters-travel` (**KI-44**) — **FIXED 2026-08-01, awaiting a batch for the OUTCOME
      proof.** It was never a routing bug: `train_counter` used the BOSS's grass, so a Machop
      caught in FIERY_PATH was sent to ROUTE102 — eight maps away AND **L3-4 wilds** (the
      "~25 xp a kill, i.e. never" patch `story_mode.py:739` already documents). The obvious
      repair is also wrong: FIERY_PATH/ROUTE112/JAGGED_PASS are all `NO_RETURN_GROUNDS` (the
      heal leg fails), so there was **no legal training ground at all** — a structural hole.
      Fixed by `counter_training_ground()` deferring to `best_training_area`. Live-probed from
      `lavaridge.ss1`: relocates to ROUTE117 (31,16) L13-14, heal Verdanturf.
      `repro_counter_training_ground.py` pins the property. **Still unproven:** the probe stood
      on LAVARIDGE_TOWN not FIERY_PATH, and the outcome needs a batch — read `Heat→Balance`
      vs batch4's 24/29 (83%) and count `counter training failed` (was 7/7).

      *The original diagnosis, kept because it is the evidence:*
      `#24-counters-travel` — **‼ THE COUNTER CHAIN'S BLOCKER.** Counter
      training now starts (the budget fix works: refusal 4 → 0, affordable target fires 7×)
      and then **fails 7 of 7** — 6× `Could not reach (9, 2) on MapRSE.ROUTE102 … not walkable
      from ROUTE103`, 1× whiteout. **Zero counters trained**, so batch4's badge funnel is flat
      at every rung (Heat→Balance z = 0.52). Exposed, NOT caused, by `affordable_training_target`
      — before it the gate refused before any travel was attempted. **Do not revert that fix.**
      Probe from the ACTUAL captured position (ROUTE103, x≈45) plus a control tile that DOES
      path; suspect KI-24's `calculate_path` unsoundness, not a sealed route. Do NOT "fix" by
      raising retries — the error already reasons that retrying cannot help.

- [x] `#24-navready-budget` (**KI-43**) — **DONE 2026-07-31.** Fixed via a dedicated
      `_TRANSIENT_WAIT_FRAMES = 600`. Proven twice: `repro_watchdog_budget_collision.py` green
      with a both-ways fault injection, and a live A/B (`gym1_done.ss1 --driver martbuy
      BUYN=30`, 40k frames) — **OLD arm 0 purchases, NEW arm 3 purchases + 3 Premier Balls**,
      money 8628 → 2628. Original diagnosis below.

      **The original diagnosis, kept because it is the evidence:**
      `#24-navready-budget` (**KI-43**) — **`_navigate_when_ready`'s escape hatch is budgeted
      at EXACTLY the watchdog's 18,000 frames, so the `break` is dead code and the derail
      always wins by one frame.** Diagnosed 2026-07-31 from stored logs: 35 of 72 watchdog
      fires are inside `RUSTBORO_CITY_MART` right after `bought Poké Balls`, 31 in
      `LAVARIDGE_TOWN` after the Heat Badge — stationary wedges, NOT the "long journeys"
      the handoff assumed. The mart restock completes **0 of 36** times (baseline 33/33), so
      every restock buys 10 balls instead of 30 and loses 2 free Premier Balls.
      **Fix:** lower the wrapper's cap to ~600 frames (the battle transition it exists for
      clears in a few), so `navigate_to` raises its honest error and `_navigate_riding_out`
      spends a retry. **Prove with a live A/B** — the Rustboro restock is a cheap, 36/36
      failing site today. `repro_watchdog_budget_collision.py` is RED until it is fixed.
      *(That repro is now GREEN — see the DONE line above.)*

- [ ] `#24-wdcanary-dedupe` — `summarize_lane` counts `global watchdog` in stdout AND the
      debug log, so every reported figure is ~2× (`9 → 143` is really `5 → 72`). Dedupe the
      source, then `--resummarise` **all four** batches so they are read by one instrument.
      ‼ Specific to this canary — `GAVE UP` is debug-only, `BADGE:`/`losses` stdout-only.

### ‼ BATCH REVIEW 2026-07-26 (bundle `20260726-231412`) — two catastrophic bugs found & FIXED
The x4 bundle showed the batch was **silently producing almost no usable data**, while
reporting most runs as successes. Both root causes are fixed in sandbox with A/B repros.

- [x] `#24-x4-staleslate` — **per-run state never reset between runs.** DONE 2026-07-26.
      `StoryEndlessResetMode.run()` loops on the SAME mode object, so `StoryMode.__init__`
      ran once per BATCH — under a comment asserting the opposite. Measured effects:
      `_rival_attempts` (cap 3) tripped on run 4 in every lane, so **runs 4+ quit at the
      Rustboro rival without fighting** (16/20 P1, 6/9 P2, 5/8 P3 — P1 run 8's log has ZERO
      lost battles yet reports "couldn't beat the rival in 3 tries"); `_defeat_counts`
      carried losses across runs (MT_CHIMNEY #7→#8, FORTREE #8→#9), so boss give-up
      thresholds fired on borrowed defeats — P4 run 2 derailed as "6 losses" after 3.
      FIX: `StoryMode.reset_per_run_state()`, called per run by the endless loop.
      REPRO: `tools/story-dev/repro_endless_per_run_state.py` (A: FAIL on HEAD → B: PASS).
- [x] `#24-x4-honestoutcome` — **failed runs reported as "finished".** DONE 2026-07-26.
      `outcome` defaulted to `"finished"`; only a raised `BotModeError` changed it, but a
      derail can instead call `set_manual_mode()` and return normally. All 16 P1 "finished"
      runs were dead (several "finished (0 frames)"). A batch summary read ~80% success
      against a true ~20%. FIX: a `try/except/else` that detects the hand-to-Manual exit and
      reports `stopped:`. Covered by the same repro.
- [x] `#24-x4-runindex` — **`run_index` still advanced by 2 per run.** DONE 2026-07-26.
      The previous adjacency-based dedupe could never work: the mode signals BEFORE
      `super().run()` while the hard reset happens INSIDE it, so thousands of polls separate
      the two calls. FIX: ownership — `reset_for_new_run(..., authoritative=True)` makes
      main.py's frame-counter fallback stand down.
      REPRO: `tools/story-dev/repro_badgelog_run_index.py`.

### ‼ BATCH REVIEW 2026-07-27 (bundle `20260727-063751`) — PRE-FIX DATA + a new failsafe hole
That batch launched before the fixes above existed, from a working copy that had not been
pulled, so it re-confirms them rather than testing them. It did expose one NEW bug:

- [x] `#24-x4-framebudget` — **the per-run frame cap could not stop a runaway run.** DONE
      2026-07-27. `MAX_FRAMES_PER_RUN` was only checked AFTER `super().run()` returned, so a
      run that never returns never reached it. Three of four lanes spent the night in ONE
      run — P3 hung **27M frames / ~6.5 h** at the Weather Institute (`controllable=False`,
      frozen position, and ZERO STUCK dumps, i.e. the global watchdog was itself what
      wedged); P1 19.9M and P2 13.4M frames in grind loops that are genuinely BUSY, so no
      progress detector can ever see them. ~16 of 29 lane-hours lost. P4 run 12 reported the
      cap after burning 2x it. FIX: `_run_with_frame_budget()` enforces the budget every
      2048 yields from inside the run, re-basing when the frame counter goes backwards at
      the mid-run hard reset. REPRO: `tools/story-dev/repro_endless_frame_budget.py`.
- [ ] `#24-weatherinstitute-hang` — the specific hang P3 hit: `do_weather_institute` →
      `_ride_out_all_scenes` (`early_game.py:5548`), then `state=3 controllable=False` for
      27M frames. The frame budget now BOUNDS it (the run derails and the batch continues),
      but the underlying scene wait is still wrong. Needs the first post-fix batch to see
      whether it recurs and how often before spending time on it.
- [ ] `#24-grindconverge` — P1/P2 ground for 13-20M frames without reaching a level floor
      (Route 103 wilds are L2-3; Route 116 L6-7). A training target that the local grass
      cannot deliver in reasonable time should be detected and abandoned, not pursued
      forever. Related to `#24-route110cap`: both are "the bot will not give up" bugs.
- [ ] `#24-canary11` — P4 broke the 1:1 losses:whiteouts ratio twice (run 1: 39 W vs 38 L;
      run 8 opens with a whiteout before any loss). Two events in 52. Most consistent with a
      whiteout crossing a run boundary rather than poison damage; the new per-run reset may
      already cover it. RE-CHECK on the first post-fix batch before investigating.

### ✅ ALL FOUR HARNESS FIXES VALIDATED LIVE — 2026-07-29 (five bundles)
`#24-x4-staleslate`, `#24-x4-honestoutcome`, `#24-x4-runindex`, `#24-x4-framebudget` are
confirmed working in production. `couldn't beat the Rustboro rival` went **31 → 0**; max
single-run frames now 1.9M–3.1M (all under the 3.5M cap, the 27M/30M hangs are gone);
`run_index` stride 1 in all four lanes. **16 runs reached the Feather Badge in one batch**
(P1×5, P2×5, P4×4, P3×2) — previously a once-per-batch event. Detail: `07-CHANGELOG.md`
2026-07-29.

### ✅ USER RULINGS 2026-07-29 — all six open questions answered
Full text + rationale: `06-DECISIONS-LOG.md` 2026-07-29. Summary:
`#24-counters` phase 2 → **A+C** (price both, then catch-and-train a Fighting type)
**plus new scope: area/species/level mapping + party>4 + PC rotation** (see `#24-trainmap+`
below); `#24-leadpolicy` → **A+C**; `#24-route110cap` → **A** (prep, NO cap);
KI-24b → **A** (fix the mock, re-baseline, show the diff); `#doc-policy-05` → **A**
(keep-and-mark until promotion); repo size → **leave it**.

### `#24-dexhunt` — catch EVERY new species, and hunt between gyms (user proposal 2026-07-29)
**NOT SCHEDULED — proposed, understood, and deliberately deferred by the user** ("we don't have
to implement it now… after I send these logs we should be at a good point to continue the
story").

**The proposal.** Catch every new species the bot meets, and deliberately hunt for unseen ones
between gyms. Rationale: (a) it is what a human player does, so runs look realistic; (b) the
encounters generated *while* hunting are XP, so hunting doubles as training and the dex fills
for free; (c) more encounters = more shiny chances.

**‼ Why (b) is the strongest argument, with measured backing.** Training is currently a
PURE-COST activity: bundle `20260729-151635` shows **78 heal round trips in one run** and
training is the single largest consumer of run frames. Hunting in level-matched areas converts
that same spend into XP **plus** dex progress **plus** shiny lottery tickets. It does not add a
cost so much as add yield to a cost already being paid.

**Most of the machinery already exists — this is assembly, not invention:**
| piece | what it already does |
|---|---|
| `modules/encounter_index.py` | whole-game reverse index: species → [{map, method, rate%, level range}] |
| `plugins/custom_modes/hunt_mode.py` | "travel to a target species' best wild spot, then hunt it" |
| `plugins/custom_modes/living_dex_mode.py` | "work through a list of target species autonomously" (#23) |
| `StoryShinyCatchStrategy` (`story_mode.py:84`) | already always-catches shinies, **even with a full party** (goes to the PC) |
| `21-TEAM-POLICY-DESIGN.md` §1 | already specifies *"Drop the `BADGE01_GET` gate. Raise `_catch_team_target` 4 → 6, allow overflow to the box."* |

**Exactly two gates block it today**, both in `_should_catch` (`story_mode.py`):
1. `if get_event_flag("BADGE01_GET"): return False` — catching stops after Gym 1.
2. `if len(party) >= self._catch_team_target: return False` — the cap of 4.
The other gates are sound and should stay: needs the Pokédex, needs >1 ball, never a duplicate,
never a shiny (the shiny branch pre-empts).

**‼ HARD DEPENDENCIES — do NOT build this first, it will starve:**
- **Ball + money economy.** Already failing at the current catch rate: this run logged *"out of
  Poké Balls — fleeing this catch and moving on"* and a derail *"Cannot hunt a Surf learner: no
  Poké Balls and no money to buy any."* Trainer battles are the ONLY income in Hoenn (no
  scripted cash gifts). Catching everything multiplies ball spend. → `#24-provisions` first.
- **PC / party management.** Catching everything guarantees a full party and constant box
  traffic. `team_policy.py` is built but **unwired**, and dead weight is already at 35% of badge
  moments. → `#24-trainmap+` item (3) first.
- **Menu-wedge exposure.** Every catch is more party-menu and nickname-prompt interaction, and
  **KI-34 (after-faint chooser livelock) is OPEN**. Multiplying menu traffic while a menu
  livelock is unfixed raises the derail rate. → settle KI-34 first.
- **Run length vs the frame budget.** A completed run is already ~3.06M frames against a
  (just-raised) 5M cap. Hunting between gyms will add substantially. Decide deliberately
  whether to accept fewer, richer runs per night or to cap hunting per chapter.

**‼ ONE GENUINE DESIGN CHOICE FOR THE USER — this proposal and doc 21 disagree.**
`21-TEAM-POLICY-DESIGN.md` §1 specifies a **scored, randomised** catch roll
(`p = 0.30 + 0.50*curiosity + …`) *specifically so runs differ from one another*. The user now
asks for **always-catch-new**, which is deterministic. Both are defensible: always-catch is more
human and gets variety from WHICH species the RNG offers; the scored roll makes two runs on the
same route diverge. **They cannot both be the rule — ask before building.**

### `#24-catchcap` — the bot catches only THREE Pokémon (user-observed 2026-07-30, cause CONFIRMED)
**NOT SCHEDULED — bundle with `#24-dexhunt`.** The user noticed the party never fills.
**Cause, verified in code:** `self._catch_team_target = 4` (`story_mode.py:845`) is a
**PARTY-SIZE** target, not a catch count, and the gate is
`if len(party) >= self._catch_team_target: return False` (`:960`) where `party` **includes the
starter**. So the bot stops at starter + 3 catches. Exactly the 3 observed.
**Fix already specified** in `21-TEAM-POLICY-DESIGN.md` §1: *"Drop the `BADGE01_GET` gate. Raise
`_catch_team_target` 4 → 6, allow overflow to the box."* One constant plus one gate — but see
`#24-dexhunt`'s HARD DEPENDENCIES (ball economy, PC/party management, menu-wedge exposure)
before shipping it, or the bot will starve on Poké Balls and clog its party with dead weight.

### `#24-menutext` — text-detection fallback for a refused party-menu selection (user proposal 2026-07-30)
**NOT SCHEDULED — deliberately deferred so KI-34 can be validated alone.**
Read `gDisplayedStringBattle` for the game's "already in battle" refusal and pick a different
mon. Sound, and there is precedent: `handle_battle._move_learn_text_showing()` already does
text-driven detection *because the internal task state is flaky*. It is also **strictly more
general** than the KI-34 index fix — it would catch ANY refusal reason (already-active, fainted,
egg), not just the on-field one.
‼ **The exact string MUST be read from the pokeemerald decomp, never recalled** — this project
does not write game facts from memory.
‼ **Why NOT now:** shipping it alongside the KI-34 index fix would make it impossible to tell
which one fixed double battles. Run the index fix alone; if `[FAINT-CHOOSER] … GAVE UP` lines
persist, this earns its place with evidence.

### ‼ A USER ASSUMPTION THE DATA REFUTES — do not build on it
The user proposed: *"in a double battle, the first 2 pokemon slots in the party are Battle slot
1 and Battle slot 2, slots 3-4 are benched."* True at the START of a double battle, **false by
the time the after-faint chooser runs** — which is the only time it matters.
Measured across **4,116 double-battle samples** in bundle `20260730-062818`:

| on-field pair (party-order) | count |
|---|---|
| `[2, 4]` | **3,975** |
| `[0, 1]` | 76 (**1.8%**) |
| `[1, 2]` / `[0, 2]` / `[1, 3]` / `[0, 3]` / `[1, 4]` / `[2, 3]` / `[1, 5]` / `[2, 5]` | 65 combined |

A replacement **keeps its own party slot** — the game tracks which party index occupies each
battler position rather than reordering the party. Hardcoding "slots 0-1 are active" would
recreate the KI-34 bug in a new place: inferring an index relationship instead of reading it.
Always read it via `BattleState.map_battle_party_index()` / `gBattlerPartyIndexes`.

### `#24-maintain` — the bot should MAINTAIN its team, not cram before exams (user proposal 2026-07-29)
**NOT SCHEDULED — noted as a potential, to discuss after the next log batch.**

**The proposal.** The bot should level its Pokémon "logically and organically" — keep the team
growing together, rather than only grinding to a floor immediately before a boss.

**‼ This is not a new idea — it is the unbuilt half of the 2026-07-21 directive.**
`modules/story/training_areas.py`'s own module docstring records it verbatim:
> *"USER DIRECTIVE (2026-07-21, Option 1): to train an under-levelled team member EFFICIENTLY,
> send it to a grass area whose wild Pokémon are around its own level, so it wins WINNABLE
> fights for FULL XP — rather than swap-training (half XP) everywhere."*
> *"STATUS: data + query helper only. NOT yet wired into `train_team` — punch-list #24-trainmap."*
`best_training_grass(mon_level)` is already **per-mon** — exactly the maintenance primitive —
and it has never been called.

**The measured symptom it would cure** (all from real logs):
- **35% of badge moments** carry ≥1 mon **15+ levels** below the team max; up to five at once.
- A **Makuhita went L8 → L9 across FIVE badges** while the team went L22 → L42 — and Makuhita
  is a Fighting type, i.e. Norman's counter, sitting in the party unusable.
- A completed run finished carrying **Shedinja L21 beside Blaziken L44**.
The starter takes nearly all the XP; the bench rots. Current training is target-driven and
reactive ("cram to a floor before this boss"), which is the opposite of maintenance.

**Why level-matched maintenance is efficient, not just tidy.** The calibrated model is
`xp/battle = 50.2 × wild_level / 7` — XP depends ONLY on the defeated wild's level, never on
the trainee's. So a low mon in a high-level area earns full XP per KO **but cannot win**, while
swap-training pays **half**. Sending each under-levelled mon to *its own* level-matched area to
win fights outright is strictly better than both. That is precisely what the 2026-07-21
directive asked for.

**‼ IT CONFLICTS WITH `team_policy`, AND THAT TENSION IS THE INTERESTING PART.**
`team_policy.dead_weight()` (built 2026-07-29) says *box* anything >8 levels behind, on the
grounds that `_prepare_for_fight` stops catching a mon up at `TRAIN_CATCHUP_GAP = 6` so it is
"unrecoverable by construction". **Maintenance would make that premise false** — a mon is only
unrecoverable because nothing ever levels it. Likely resolution: maintenance is the CURE,
boxing is for the genuinely hopeless (a L3 Zigzagoon caught at the wrong moment). If
maintenance works, the 35% dead-weight rate should fall — which is a **measurable success
criterion**, and the honest way to test the pair against each other.

**Interacts with `#24-dexhunt` above:** hunting for new species generates exactly the
level-matched encounters maintenance needs. Done together they are one activity, not two.

### ‼‼ THE BIG ONE — `#24-trainmap+` : area-aware training, party>4, PC rotation
**User directive 2026-07-29.** The bot trains in whatever grass is next to the objective,
often below L5, so XP is near worthless — and Norman is the 5th gym but sits in the STARTING
region, where "train near the gym" is actively wrong.

‼ **The data layer ALREADY EXISTS — this is wiring + policy, not a new map.** Verified
2026-07-29 before proposing any build:
- `modules/encounter_index.py` — whole-game reverse index from the ROM's `gWildMonHeaders`:
  species → [{map, method, rate%, level range}], cached per ROM. Built for Hunt Planner (#9).
- `modules/story/training_areas.py` — verified spin tiles + wild bands,
  `best_training_area()`, `best_training_grass()`, `estimate_frames_to_level()`.
- `modules/story/counter_plan.py` — already ranks reachable, cost-priced counter encounters.

**The three concrete gaps:**
- [ ] **(1) `train_team` never picks an area.** `early_game.py:1738` —
      `grass: tuple = RUSTBORO_TRAINING_GRASS` is a caller-supplied constant; it never calls
      `best_training_area`. Its own docstring admits this. **Wire it.**
- [~] **(2) `FODDER_LEVEL_GAP = 12` compares the WRONG QUANTITIES — ANALYSED 2026-07-29,
      DELIBERATELY NOT CHANGED.** See **KI-31** for the full write-up and the measured table.
      Short version: the gate tests wild-level vs TEAM-level, but the project's own calibrated
      model says `xp/battle = 50.2 × wild_level / 7` — XP depends only on the WILD level. The
      failure window is teams **below ~L17** (because `5+12=17`); a L15 team on Route 102
      forgoes a **2.8×** speedup and never moves.
      **Blocked on two things, both real:**
      1. The conservatism is DELIBERATE — `repro_fodder_grass.py` says *"the whole point of the
         conservative gap: proven-good prep must not move"*, and L10-17 is exactly
         Roxanne/Brawly/Wattson.
      2. **That repro needs a real `mgba`** (it loads a ROM + `saves/norman_done.ss1`) and is
         one of the 5 environmental failures on the dev box. **Validate on the batch machine.**
      Proposed replacement (no new constant, no travel measurement needed): relocate when
      `estimate_frames_to_level(...local_max) − estimate_frames_to_level(...better_hi)` is a
      large win — e.g. the better area at least HALVES the grind, i.e. `better_hi ≥ 2×local_max`.
- [ ] **(3) party cap 4 → 6 + PC rotation — ALREADY DESIGNED, BUILD IT.**
      ‼ The user flagged this as "needs further discussion". **That discussion already
      happened on 2026-07-26 and is written up build-ready in `21-TEAM-POLICY-DESIGN.md`**,
      which specifies exactly what was asked for: raise `_catch_team_target` 4 → 6 with
      overflow to the box (§1), a scored catch roll behind hard floors (§1), a dead-weight
      predicate in a new pure `modules/story/team_policy.py` (§2), **rotation that piggybacks
      on heal trips and never detours for its own sake** (§4), a counter ladder that checks
      the BOX first (§5), a never-randomise safety list (§6) — including *"boxing the only
      Surf carrier soft-locks the run"*, which is the same wall P1 hit on 2026-07-29 — and a
      no-emulator test plan (§7).
      **The machinery also exists:** `modules/modes/util/pc_interaction.py` provides
      `interact_with_pc(actions)` with deposit/withdraw/move-box primitives.
      **And the game fact is already settled in our own code:** `story_mode.py:84` —
      *"even with a full party (the catch goes to the PC box, vanilla behavior)"* — a path
      the shiny-catch strategy already exercises in real runs. No probe needed.
      So this is ASSEMBLY against an existing spec, not a new design. Re-read `21` first;
      only bring the user a question `21` does not already answer.

- [x] **`#24-reprorot` — DONE 2026-07-30. The 4 "environmental / needs mgba" failures were
      four DIFFERENT rots, and none needed an emulator it did not have.** All four launched
      mGBA 0.10.2 fine; all four now pass. `repro_boss_training` (stub `self` missing
      `_boss_plan_is_hopeless`), `repro_double_faint` (stub mon missing `.level`),
      `repro_navigate_failfast` (asserted a STRING where the code correctly raises a
      BotModeError SUBCLASS), `repro_sufficiency` (four compounding fixture faults —
      no `grass` in the cfg, no `total_exp`, no `MAX_PREP_TRAINING_FRAMES`, and **no
      emulator at all**, so the ROM encounter tables were unreadable).
      **No production behaviour was wrong in any of them.**
      ‼ **The lasting lesson is `repro_sufficiency`:** two of its four faults produced NO
      crash, because the lookahead sits inside `except Exception: pass` — a missing stub
      attribute became a silently WRONG VERDICT. That is a RECURRENCE of the exact failure
      `_boss_plan_is_hopeless`' own comment warns about. Both stubs are now `_StoryModeStub`,
      which HARVESTS every UPPERCASE constant instead of hand-listing them and raises a
      self-explaining error when the code grows a new dependency. **Copy that pattern into
      any new repro that stands in for `StoryMode`.**

- [x] **`#24-menuorder` — DONE 2026-07-30. Story block + ×4 controls hoisted to the TOP of
      the Bot-mode popup** (user request: *"I have to scroll around to activate them and
      end/park them"*). `Park ×4` and `Stop Endless Loop ×4` used to be the LAST TWO entries,
      below the greyed-out modes. New order: Manual → **STORY** (4 modes + Endless
      Debug-Reset + Endless Loop ×4 + Park ×4) → OTHER MODES → disabled → Debug Logging.
      Ordering extracted from the Tk callback into the pure
      `dashboard_gui.build_mode_menu_plan()`; `repro_mode_menu_order.py` (14 checks, no Tk,
      no emulator) asserts it so it cannot drift back.
      ‼ Entries keep a FIXED position — a non-selectable Story mode is greyed IN PLACE
      rather than dropping to the bottom, and `Park ×4` is always shown (greyed when idle).
      Hiding it was the 2026-07-26 choice and it is what made the layout move.
      Story modes matched by PREFIX, so a future `Story (…)` is hoisted automatically.

- [x] **`#24-x4headless` — DONE 2026-07-31. Headless ENDLESS-RESET batch runner**
      (`tools/story-dev/x4_headless.py`, repro `repro_x4_headless.py`, 55 checks, no emulator).
      Runs N parallel lanes of the USER'S mode — `Story (ENDLESS RESET)`, headless — instead of
      livetest's plain `Story`, so finish rates measured here are finally comparable to the
      user's bundles (plain `Story` ENDS a run on a `BotModeError`; `ENDLESS RESET` swallows it
      and starts a fresh run, so livetest has always been the harsher measurement).
      `--lanes N` (default 4 = the dashboard's split; 8 = **2 per starter + 2 random**, which
      doubles per-starter sample size — needed for starter-specific bugs like
      `#24-starter-gym3`). Bounded by `--minutes` and/or `--runs` (refuses to run unbounded).
      Output `x4-runs/<stamp>/` with `MANIFEST.txt`, `summary.json`, per-lane stdout + the
      debug logs **from this window only**, plus root `INDEX.md`/`LATEST.txt` recording each
      batch's **COMMIT HASH**.
      ‼ **Emulation is ASSERTED, not re-set:** every run's RUN HEADER must read
      `emulation: speed=0 video=True`, checked for the WHOLE batch (the historical bug is
      "run 1 fine, run 2 at 1x"); a violation aborts loudly. Empirically confirmed on a 2-lane
      smoke batch at **~1,211 fps/lane**. Shipped with a fix for `--endless-target`, which was
      parsed and then discarded by every frontend except the tile lane.

- [x] **`#24-journey` — DONE 2026-07-31. Warp planning at MAP granularity.**
      ‼ **AND THE DIAGNOSIS BELOW IS WRONG — read `05-KNOWN-ISSUES.md` "KI-39 — CORRECTED"
      before believing any of it.** Measured live, `calculate_path` DOES span whole connected
      components (every one of these maps is `level=459`) and reachability is PARTIAL, not
      zero: ROUTE110 17/125 tiles, ROUTE111 11/173, ROUTE117 22/41, VERDANTURF 14/23. The four
      blocked trips had FOUR causes and only one was route planning.
      **The genuine bug:** `WarpGraph.plan()` works at REGION granularity and returns `[]` for
      any same-region pair, and the whole overworld is one region — so a warp that is the ONLY
      physical link between two "connected" maps could never be planned. Proof case:
      Verdanturf declares a map connection to Route 116, but 0 of 40 sampled Route 116 tiles
      are walkable from Verdanturf and the real link is the Rusturf Tunnel warp.
      **Shipped:** `WarpGraph.warp_candidates()` + `map_distance()` + kept map-level
      adjacency (`CACHE_VERSION` 1→2); `navigate_to_anywhere` walks if it can, else validates
      each candidate warp's first leg with `calculate_path` before committing, remembering
      warps taken; the "did the warp fire?" check now compares MAPS, not regions (it would
      have reported every same-region warp as a locked door).
      **Proof:** `repro_journey_planner.py` (27 checks, no emulator) +
      `probe_journey_live.py` / `story_harness.py --driver journey` — OLD arm
      `arrived=False map=MAUVILLE_CITY`, NEW arm `arrived=True map=ROUTE116` in 33,725 frames.
      ‼ **It does NOT unblock `#24-counters`** — see the new `#24-smashroute` below.

- [x] **`#24-smashroute` — DONE 2026-07-31. The bot clears a field-move obstacle that seals a
      journey, and can now reach FIERY_PATH from Mauville.** Live A/B
      (`story_harness.py --driver smashroute`, `rocksmash_taught.ss1`): OLD arm
      `arrived=False map=MAUVILLE_CITY`; **NEW arm `arrived=True map=FIERY_PATH`, 45,305
      frames.** `modules/story/obstacle_clearing.py` reads the ROM's own object events (no
      coordinate table to rot — symbol names COUNTED off the ROM: StrengthBoulder 59,
      RockSmash 44, CutTree 33), gates on move+badge+a reachable approach tile, derives the
      stand tile and facing, and delegates to the already-hardened `_smash_rock`. Hooked into
      `_navigate_riding_out` **before** its fail-fast guard — smashing the rock changes the
      world, which is the premise that guard tests.
      ‼ **Only Rock Smash is actionable.** Cut is known-but-never-validated; **Strength is
      excluded deliberately** — a boulder is PUSHED, not removed, so the "object is gone"
      success test can never fire. Both recorded in `KNOWN_BUT_UNSUPPORTED` with reasons.
      ‼ **Shipped with a re-entrancy bug and the sweep caught it** — `clear_obstacle` →
      `_smash_rock` → `_navigate_riding_out` runs through the hook itself. Guarded now; see
      `08-MISTAKES` 2026-07-31. Repro: `repro_obstacle_clearing.py` (24 checks, no emulator).

- [ ] ~~**‼ `#24-smashroute` — clear a ROCK SMASH obstacle that seals a journey (new,
      2026-07-31; see KI-41). This, not route planning, is what gates the counter chain.**~~
      (original entry, kept for the measurement)
      Measured: ROUTE111 reachability from Mauville has a hard floor at y≈100–101 across
      columns 17–20 — the twin-rocks choke `early_game.travel_lavaridge_to_petalburg` already
      documents at **(18,101)** (and which RESPAWNS on map reload). Consequence: ROUTE112 is
      **0/76** reachable from Mauville, and FIERY_PATH's only two doors are on Route 112 — so
      Machop, the counter the ladder names for Norman, is unreachable. After the `#24-journey`
      fix a warp route to Fiery Path IS found (2 candidates) and **neither first leg is
      walkable**. The story only gets past this because two travel functions hand-code a
      `_smash_rock` at that exact coordinate; nothing generic does.
      **Shape:** when a journey leg fails, ask whether a smashable rock / cuttable tree sits on
      the blocked corridor; if the party has the move and badge, clear it and re-plan.
      `_smash_rock` exists and is idempotent. ‼ Bound it — a respawning rock must not become an
      infinite smash-and-retry loop. Coordinates from map data or the decomp, never memory.

- [ ] ~~**‼ `#24-journey` — CROSS-MAP OVERWORLD ROUTE PLANNING (new, 2026-07-30; see KI-39).
      This is now the biggest structural blocker in the project.**~~ **(SUPERSEDED — the text
      below is the 2026-07-30 diagnosis, kept only because the handoff and KI-39 quote it.
      It is wrong; see above.)** The bot cannot plan a
      journey to a place more than a directly-connected map away. Measured from Mauville:
      ROUTE117 (adjacent) OK 72 waypoints; ROUTE110 (joined via a gate BUILDING = a warp)
      FAIL; ROUTE116 FAIL; ROUTE111-north FAIL. Cause: `region_of()` puts the WHOLE Hoenn
      overworld in region **0**, so `navigate_to_anywhere` always takes its same-region
      branch and never consults the warp planner — even when a valid warp route exists
      (`graph.plan(MAUVILLE→FIERY_PATH)` returns one). Long trips work today only because
      the story chapters hand-code them leg by leg (`_hold_walk_route`).
      **Gates:** `#24-counters` phase 2 (destinations are mostly out of range),
      `#24-dexhunt`, `#24-pc` (box trips), `#24-catchcap`, and the whole team/PC-reserve
      plan — all of them assume "travel to a known place on request".
      **Shape of the fix:** BFS map-connections + warp edges → ordered legs → execute leg by
      leg re-planning from the real position after each (the shape the cross-region branch
      already uses). Needs sub-map partitions (Route 111 north/south are one map but not
      mutually walkable), capability gates (Surf/Fly/Go-Goggles) and a per-leg frame budget.
      ‼ **Do NOT try gateway waypoints** — tried and refuted 2026-07-30
      (`probe_counter_gateway.py`): a same-region gateway is routed by the same broken
      branch and fails identically.

- [~] **‼‼ `#24-menutext` — THE REAL FIX for KI-38/KI-40. NOW THE #1 ITEM (2026-07-30).**
      Runs stopped finishing entirely (48% → 0%) because the after-faint chooser cannot select
      a living replacement: measured `NO ELIGIBLE REPLACEMENT` = **0** while `GAVE UP` runs at
      **~22/hour**, i.e. a valid target always existed and was never chosen. KI-38's own
      evidence says the CURSOR MODEL is wrong (`presses={'Down': 3, 'A': 273}`,
      `cursors_seen=[0,2,3,7]` in a 4-mon party, 7 probably CANCEL) — and no number of retries
      fixes a wrong model.
      **Build:** read the party-menu TEXT so the bot knows what the cursor is actually on,
      instead of inferring it from indices. ‼ **The strings MUST come from the decomp**
      (`gh api repos/pret/pokeemerald/contents/...`), never from memory — that rule has already
      been broken once today (08-MISTAKES, the Hoenn route claim).
      ✅ **STRINGS ALREADY FETCHED AND VERIFIED 2026-07-30** from `src/strings.c` — use these,
      do not re-derive or guess:
      | symbol | text |
      |---|---|
      | `gText_SendOut` | `SEND OUT` |
      | `gText_Shift` | `SHIFT` |
      | `gText_Switch2` / `gText_Switch` | `SWITCH` |
      | `gText_Summary5` | `SUMMARY` |
      | `gText_Cancel` / `gText_Cancel2` | `CANCEL` |
      | `gText_Enter` | `ENTER` |
      | `gText_DoWhatWithPokemon` | `Do what with this {PKMN}?` — shown when the ACTION menu is open over a chosen mon |
      ✅ **INSTRUMENTATION ALREADY SHIPPED:** the `GAVE UP` log line now also records the live
      `gDisplayedStringBattle` and `gStringVar4` (tagged `[#24-menutext]`), diagnostic-only.
      **The next batch's logs should therefore SHOW what the screen said at each failure** —
      read those before writing the chooser, rather than reasoning from indices again.
      **MITIGATION (A) SHIPPED 2026-07-30:** `FAINT_CHOOSER_GIVEUP_LIMIT` 3 → 20, clamped to
      200, tunable via `POKEBOT_FAINT_GIVEUP_LIMIT` (`repro_faint_giveup_limit.py`).
      ‼ **If the finish rate recovers, that is the MITIGATION working, not this item done.**
- [x] **`#24-giveuplimit` — DONE 2026-07-30 (mitigation A for KI-38/KI-40).** See above.
      Test caught a real hole pre-ship: the env override was validated but not CLAMPED, so a
      fat-fingered value gave an effectively unbounded chooser and silently reintroduced the
      KI-36 hazard the finite limit exists to prevent.

### ‼ #1 EXECUTION PRIORITY — the counter chain is now 72% of all derails
- [~] **`#24-counters` phase 2 — BUILT 2026-07-30, AWAITING LIVE VALIDATION.**
      **STEP 1 — the hunting-ground gate** (`hunt_ground_tile` / `huntable` /
      `best_huntable`; `repro_counter_huntable.py`, ALL PASS). Had to land first: the cost
      ranking puts **Victory Road Hariyama at rank 1** for Norman, so an executor built on
      `cands[0]` would have walked a mid-game team into the E4 approach.
      Destinations: Norman → **Machop @ FIERY_PATH (18,19)**, Wattson →
      **Sandshrew @ ROUTE111 (25,55)**, Winona → **Electrike @ ROUTE118 (29,15)**.
      **STEP 2 — the executor.** `modules/story/counter_hunt.py` (arm → hunt → train),
      `StoryMode._counter_ladder`, and a catch-on-sight branch in `on_battle_started`.
      `repro_counter_hunt.py` — **15 checks, ALL PASS.**
      ‼ **Bounded by PER-RUN STATE (`_counter_hunts`), one hunt per boss per run** — a
      retry or frame budget CANNOT bound this, because `_prepare_for_fight` is re-entered
      by the run loop after every lost attempt (the KI-34 shape). The attempt is recorded
      BEFORE the hunt so a derailed hunt still consumes its chance.
      ‼ **The terminal raise is untouched** — every failure path still stops honestly.
      **STEP 2b — destination FALLBACK.** `probe_counter_reachability.py` drove the REAL
      navigation and found the TOP destination UNREACHABLE for 2 of 3 bosses (ROUTE111 is
      Fallarbor-side; ROUTE118 is the KI-24 bridge case) while Norman's FIERY_PATH (18,19)
      **ARRIVED in 2,922 frames**. The ladder now walks the ranked huntable list up to
      `COUNTER_HUNT_MAX_DESTINATIONS = 3`. ‼ Cheap failures cascade, expensive ones do not.
      ⏭ **WHAT IS OWED: a LIVE run.** Nothing here proves the bot can walk to Fiery Path
      from Petalburg, catch a Machop and beat Norman with it. Watch for: does the hunt
      reach (18,19)? does the catch-on-sight branch fire? does `train_counter` accept or
      decline the estimate? and — the regression to fear — does a boss that used to stop
      honestly now loop? Grep new logs for `counter hunt` and `already hunted a counter`.
      Of 36 derails in the newest bundle, **~26 are "boss: N losses with no super-effective
      answer to X. Need one of: Y"** — the chain diagnoses correctly and then ENDS THE RUN.
      Breakdown: Electric→needs Ground ×17, Normal→needs Fighting ×9, Winona ×3.
      `counter_plan.find_counter_candidates` already names reachable species and tiles
      (`story_mode.py:611`, raised at `:1347`); `story_mode.py:619` states plainly that it is
      "PLANNING/LOGGING ONLY — this does not travel, catch, or train anything". Building the
      travel-and-catch step converts ~72% of derails into continued runs. Nothing else on
      this list is close in value.
- [ ] **`#24-starter-gym3` — Gym 3 viability is decided by the starter (new, 2026-07-29).**
      P3/Treecko stalls at 2 badges in **11 of 14 runs**, and **10 of its 11 derails are
      Wattson**. P2/Mudkip never hits this: Marshtomp is Water/**Ground** — immune to Electric
      and super-effective back. Torchic/random sit between. Only Mudkip is self-sufficient at
      Wattson. This is a *consequence* of `#24-counters` phase 2, not a separate fix — but it
      is the sharpest measurement of why that item matters, and it is exactly the
      starter-specific failure the ×4 instrument was built to expose.
- [ ] **`#24-pc` / Surf resource walls (new derail classes, 2026-07-29).** Seen for the first
      time in P1: *"No party mon can learn Surf and the party is full — needs PC box
      management (#24-pc)"* ×2, and *"Cannot hunt a Surf learner: no Poké Balls and no money
      to buy any"* ×1. Resource exhaustion, not combat failure — related to
      `#24-provisions` (money/items) and `#24-partyvariety` (a full party of dead weight).

### ‼ DOCUMENTATION CORRECTNESS AUDIT — 2026-07-27
- [x] `#doc-audit-1` — **docs 00/01/02/05/14 re-verified against code.** DONE 2026-07-27.
      Biggest find: `02-ARCHITECTURE.md`'s folder map omitted **`sandbox-pokebot/`, where all
      work happens** (plus `tools/`, `PROJECT KIT/`, `REMOTE START/`, `cloud-backups/`), while
      its own prose cited sandbox-only modules — the doc contradicted itself. `01` gave the
      active copy no intent section and its "Future: custom automations, installer, custom
      interface" placeholder was stale (all three built). Also corrected: recommended Python
      is 3.13 not 3.12; libmgba path; the "116 files" figure (matched no copy — it is 118);
      `KNOWN_GATES` holds 3 edges not 1. Added KI-25…KI-29 to `05`. Added §2b/§2c to the
      playbook. Method + agent calibration: `06-DECISIONS-LOG.md` 2026-07-27.
- [~] `#doc-audit-2` — **`03-PUNCH-LIST.md` status audit (THIS FILE) — PARTIAL.** The agent
      running it was killed by a weekly usage limit on 2026-07-27; redone by hand 2026-07-29
      for the CONSISTENCY half only.
      **Done:** 134 items across 98 distinct `#`-ids; the undocumented third marker `- [~]`
      (17 items) is now defined at the top of this file; exactly one id had a conflicting
      status (`#24-pokenav-faithful`) and it proved to be a legitimate recurrence, now
      cross-linked in both directions; no `- [x]` item was found whose code is missing.
      **Still open:** the expensive half — walking all **80** open items and checking each
      against `sandbox-pokebot/` for "already built". Calibration case if resumed:
      `#24-regionreach` is `[~]` and its oracle IS wired (`story_mode.py:553`/`:606`), so
      only the KI-24b hop-count nuance remains — i.e. `[~]` is correct there, and a naive
      "it's wired, mark it done" sweep would be wrong. Expect more items like that.
- [ ] `#doc-audit-3` — **`12-STORYMODE-DESIGN.md` (2,886 lines) never audited.** Check Area
      Atlas coords/flags against `modules/map_data.py` + the decomp, and promote any
      `⚠ VALIDATE LIVE` item that live runs have since validated.
- [~] `#doc-audit-4` — **`ai-research-notes/` integrity — SPOT-CHECKED 2026-07-29, not
      exhaustive.** The directory is 84 files / ~9,400 lines; a full claim-by-claim sweep was
      NOT done.
      **Checked and PASSING:** (a) `00-READ-THIS-FIRST.md` states the rule, the per-claim
      verification gates, and its own track record; (b) stub markers exist in the authoritative
      docs that matter — `12-STORYMODE-DESIGN.md:4-10` carries a proper header stub, and
      `03`/`04`/`05`/`22`/`23` all reference the directory; (c) **the one documented Gemini
      error was correctly contained** — the note claimed no healing house exists on the
      Route 112/113 corridor, `sandbox-pokebot/modules/map_data.py:1059` has
      `ROUTE111_OLD_LADYS_REST_STOP = (18, 1)`, and
      `18-RESEARCH-HEALPOINTS-AND-LEGENDARIES.md:27-31` records the claim tagged
      `(INFERENCE)` and rebuts it with our own map data. `05-KNOWN-ISSUES.md:368` holds the
      verified detail. The marker-and-rebut discipline held.
      **Still open:** no systematic check that every *other* note's claims are either
      stub-marked or verified. Highest-risk class per the 2026-07-25 measurement is Gemini's
      **architecture advice** (all three of its "your bot must hardcode an interrupt here"
      constraints rested on permanence that does not exist) — sweep the design docs
      (`19`–`23`) for actionable advice traceable to a note rather than to code.
- [ ] `#doc-policy-05` — **user ruling wanted:** should `05-KNOWN-ISSUES.md` delete an entry
      when it is fixed in `sandbox-pokebot/`, or keep it until promotion to `custom-pokebot/`?
      Currently retained-and-marked. See `06-DECISIONS-LOG.md` 2026-07-27 (provisional).

**STILL OPEN from the same review — design calls, NOT yet built (need the user's ruling):**
- [ ] `#24-leadpolicy` — **the matchup lead is purely defensive and benches the winner.**
      `_lead_best_matchup` (`early_game.py:1587`) picks `min(incoming_multiplier, -level)` —
      it models only the foe ace's STAB types, and ignores whether the chosen lead can deal
      damage or survive a level gap. Verified to reproduce every observed lead exactly:
      P2 led **Whismur L15** into the Route 110 rival **13 times** while **Marshtomp L24**
      sat in slot 2 (Marshtomp is 4× weak to the Grovyle, so it is correctly excluded — but
      Whismur cannot win either). P4 led **Shedinja L20** vs Norman (Normal→Ghost = 0×, a
      genuinely clever Wonder Guard read) and lost to Slaking's **Faint Attack (Dark)**,
      which the model cannot see because it does not read movepools.
      ‼ This is NOT the old `train_team` lead-restore bug — that fix is intact and its repro
      still passes; the matchup call simply runs afterwards and overrides it.
      OPTIONS (user's call): (a) require the lead to also have a ≥neutral attacking option;
      (b) weight the level gap so a resistant chaff mon can't bench a much stronger one;
      (c) special-case 1-HP Wonder Guard mons; (d) leave as-is and fix via provisions.
- [ ] `#24-route110cap` — **the Route 110 rival gets no prep and no cap.** Unlike every other
      boss it calls neither `_prepare_for_fight` (no proactive band training, no reactive
      escalation) nor an attempt cap, so P2 burned **13 whiteouts** there in one run.
      ‼ DELIBERATELY NOT FIXED BLIND: a naive cap would have KILLED that run, which went on
      to reach Fortree after those 13 losses. Adding prep needs a Route 110 training-grass
      tile, which is a game fact that must be verified (live probe / decomp), not recalled.

- [ ] **#24 — STORY AUTO-PLAYER.** The only active work. A cold start reaches
      **Badge 6 (Winona) = end of built content** (38 maps, ~2.48M frames, 0 derails).
      Sub-items live in `## Story bot (#24) — open backlog` below; the current order is:
      1. `#24-whiteout` (attrition dominates; the successful run still took 80)
      2. `#24-counters` phase 2 (the chain NAMES a counter; acting on it isn't built)
      3. `#24-regionreach` gate table + the blocked training-gate switch (KI-24b)
      (`#24-movelearn-recovery` — DONE 2026-07-25, see Done below.)
      Next unbuilt chapters: **Mt. Pyre**, then the **Magma hideout**.
- [ ] #V â€” Post-promotion verification sweep (PARKED behind #24): independent adversarial pass
      on the promoted features that only had builder self-verification (not
      an independent pass) â€” #8 global pathfinding, #12 shiny alerts, #18
      update notice, #20 cloud-sync, and the 2026-07-19 GUI polish (tabs /
      full-dex picker / XP bars / topmost dialogs). Interrupted twice by
      credit limits; run it against custom-pokebot before relying on the
      save-touching bits (cloud-sync ships off-by-default, so inert).

- [ ] #24-x4 — **ENDLESS LOOP ×4** (user request 2026-07-26): four independent
      `Story (ENDLESS RESET)` bots at once, one process + profile + starter each
      (P1 torchic / P2 mudkip / P3 treecko / P4 random), tiled 2×2 in the
      dashboard's video area, looping forever and restarting independently.
      A TEST INSTRUMENT — it exists to raise the rate of reviewable failure data
      and guarantee starter coverage.
      **Phase 1 BUILT in sandbox (2026-07-26), tests green, LIVE RUN NOT YET DONE**
      — this dev box has no `mgba`, so nothing involving a real emulator has been
      exercised. See 04-HANDOFF for the exact live confirms the user must run.
      **Phase 2a DONE 2026-07-26** — the party strip / party tab / hover tooltip
      follow the focused lane (`modules/remote_party.py` rebuilds stand-ins from the
      lane's status blob; the renderer is unchanged). Live confirm still owed.
      **#24-x4-logs DONE 2026-07-26** — `Emulator > Park x4 & Collect Logs...`
      (batch-only menu item): parks every lane, bundles all four lanes' logs into
      one verified zip under `profiles/x4 LOGS/`, archives the originals to each
      profile's `debug-logs/Old/` only AFTER the zip verifies. Added the
      parent->child command channel that phase 2b will reuse. Live confirm owed.
      Phase 2b (agreed with the user, NOT built): the watch/CONTROL toggle — click a
      tile then drive it, forwarding `press_button`/`hold_button`/`release_button`
      over a per-lane input pipe (`modules/libmgba.py` already exposes exactly that
      surface, so the channel is strings, not input-model surgery).
- [ ] #24-badges — **TRAINER-CARD / BADGE CASE overlay** (user request 2026-07-26):
      a Bag-icon button under the 6th party slot opens an overlay to the right laid
      out like the in-game badge case — 8 badges, black silhouette until earned —
      and hovering/clicking one shows that gym leader's details plus THE TEAM THAT
      BEAT THEM. User said it may be tabled; the UI is tabled, the capture is NOT.
      **DONE:** `modules/badge_log.py` records the party at the instant each
      `BADGE0N_GET` flag flips, to `<profile>/badge-log.json`, re-arming on emulator
      reset so every run of an x4 batch is captured. Shipped first because it can
      only record badges earned AFTER it is on — waiting would have thrown away
      every x4 run's badge data (06-DECISIONS-LOG).
      **UI DONE 2026-07-26** — Bag button under the 6th ball + the 2x4 badge-case
      overlay (silhouette until earned, hover/click for leader detail + the team
      that won). Leader table decomp-verified in `modules/badge_case.py`; the 8th
      leader is JUAN, not Wallace (that error shipped first — 08-MISTAKES).
      Live confirm owed. **REMAINING:** real Bag artwork (the icon is PIL-drawn;
      the repo ships none); and choosing WHICH run's team to show when a badge has
      many recorded wins — currently the latest, with a count of the rest.
- [ ] #24-badges-live — **Make the badge case LIVE, like the party strip**
      (user request 2026-07-26). Today `_badge_case_source()` already reads the
      FOCUSED x4 lane, so opening the Bag after clicking P3's tile shows P3 — but
      the contents are a SNAPSHOT taken in `open_badge_case()` and cached in
      `_badge_case_entries_cache`. Two consequences to fix:
        (a) clicking a different tile while the case is OPEN does not switch it —
            `_x4_click` refreshes the party (`_refresh_party` + `_refresh_party_strip`)
            but not the case;
        (b) it does not tick over as badges are earned during a run.
      Wanted: the case tracks focus changes and refreshes on a cadence, the way the
      party strip does off `_refresh_sidebar`.
      ‼ Design constraint that produced the snapshot in the first place: the entries
      come from `badge_log.read_log()`, i.e. a DISK READ of `badge-log.json`, and
      `_show_badge_detail` runs on every hover — a naive "just read it live" turns
      mouse movement into file I/O. Refresh on focus-change and on the KPI/sidebar
      cadence (or when the lane's published badge set changes), NOT per hover.
      Cheap seam available: lanes already publish `badges` in their status blob, so
      "has anything changed?" is answerable without touching the disk.
      Assets are NOT a blocker: all 8 Hoenn badge sprites already exist at
      `modules/web/static/sprites/badges/` (Stone, Knuckle, Dynamo, Heat, Balance,
      Feather, Mind, Rain). The only missing art is a Bag icon.

## Under discussion (user 2026-07-26, NOT agreed scope — see `19-TEAM-BUILDING-DISCUSSION.md`)
> ‼ Do NOT start these. Each has open questions that must be answered with the user first;
> the design note records them. Promote to the active list once resolved.
- [ ] #24-gymtrainers — **Battle gym/town trainers BEFORE grinding wild, at every gym.**
      Raised for Dewford (bot trains in the cave; user says it should be on "the second
      floor" AND should clear the island + gym trainers first for XP and money). Directly
      attacks the #1 failure in batch `20260726-181825`: attrition, not gym leaders (P2
      whited out 41× on Route 110 and derailed). ‼ Open: WHICH floor (Granite Cave 1F/B1F/
      B2F); always vs only-when-underlevelled; town-wide vs arc-wide trainer scope.
      **ANSWERED 2026-07-26: train on Granite Cave B1F AND B2F; fight trainers ALWAYS.**
      ‼ **ALL FACTS NOW DECOMP-VERIFIED** (see `19-TEAM-BUILDING-DISCUSSION.md` §8) and the
      spin tiles are recorded in `training_areas.py` PENDING_GRASS: **B1F (3,18) L9-11**,
      **B2F (28,17) L10-12**, neither gated by any HM/item/flag. B1F's 62 cracked-floor
      tiles are all UNREACHABLE ON FOOT (north of an unclimbable muddy slope).
      ‼ **BLOCKED ON ONE THING:** `_CAVE_EXITS` / `_CAVE_ENTRANCES` are SINGLE-HOP tables,
      and B1F/B2F are 2-3 hops deep from Route 106. Promoting them without making that
      threading chain-aware breaks the post-training HEAL — the global navigator cannot
      cross warp levels, and that exact failure already dropped two real-hardware runs to
      Manual (2026-07-22). **Next step: make cave entry/exit chain-aware, then promote,
      then validate live.** Deliberately NOT done blind — this is navigation code.
      ‼ **PRIORITY NOTE:** this spot only fires after ≥2 Brawly losses, and batch
      `20260726-201838` had 2-3 Dewford losses in the whole batch. Runs are dying at
      MAUVILLE (Wattson) and PETALBURG (Norman), not Dewford. Worth doing because the user
      asked and the data is now free, but it is not where the failures are.
- [ ] #24-partyvariety — **Fill the party and vary what is caught; PC deposit/withdraw.**
      ‼ **ROOT CAUSE FOUND (recon 2026-07-26) — it is not emergent, it is two conditions.**
      `_should_catch` (`story_mode.py:899-937`) requires `not BADGE01_GET` AND
      `len(party) < _catch_team_target` where **`_catch_team_target = 4`** (`:811`). So the
      bot catches FOUR mons before the Stone Badge and then never catches again for the
      rest of the run. Part 1 is nearly a one-line change.
      ‼ **PC automation ALREADY EXISTS and is unused:** `modules/pokemon_storage.py` (full
      box READ) + `modules/modes/util/pc_interaction.py` (804 lines: withdraw / deposit /
      release), whose only consumer is `daycare.py`. `#24-pc`'s "map the PC UI" is already
      done — what is missing is navigation to a PC and a keep/box POLICY. The shiny path
      already proves party-full→box works (`story_mode.py:1456-1482`).
      ‼ **CONFIRMED ONE ITEM WITH `#24-counters` PHASE 2** — the counter chain currently
      diagnoses and then RAISES `BotModeError` (`story_mode.py:1309-1313`); that raise is
      the seam where fetching would hook in, and `HM_CATCH_TARGET_DEX` (`:1485-1511`) is a
      working "catch species X on sight" primitive to reuse. Blocked on counter tiles being
      mapped (every candidate has `tile: None`).
      Also: **dead weight is invisible by construction** — `_battler_slots()` only asks
      "not an egg, has a move with base_power > 0", so a L5 CASCOON in a L24 party passes,
      and `_prepare_for_fight` then excludes it from training. Cheap first win: bench or
      deposit anything more than N levels below the lead.
- [ ] #24-personality — **A two-axis bot "personality" (user answer 2026-07-26).** The
      user wants BOTH testing-diversity and competence, selected by a personality that
      swings and drifts during play so it looks organic. Recommendation in the design
      note: TWO axes (`curiosity` = what it collects/fields, `caution` = how much risk it
      takes), because one axis forces "more varied" to also mean "more reckless".
      Drift should be EVENT-DRIVEN (whiteout -> caution up; clean streak -> caution down),
      not a random walk. ‼ TRAP: "cautious" must NOT mean "grind longer" — P2 whited out
      41x on Route 110 while training, so that loop would worsen the dominant failure.
      Must be a pure function of (seed, events) so it is testable without an emulator, and
      the rolled values must reach the logs so personality can be correlated with outcome.
- [ ] #24-favourite — **Roll a "favourite" species per run.** Prefer to catch/keep it,
      unless it is a disadvantage for the fight about to be entered. Cheap run-to-run
      variance that is independent of the RNG decorrelation already in place.
      **ANSWERED 2026-07-26:** "disadvantage" = a TYPE CHECK, applied to gym leaders /
      rival / Wally / Elite Four, PLUS reactively when a trainer keeps beating the bot
      (hang that off the existing `_defeat_counts`, `story_mode.py:813`). TWO favourites
      per run: one regular, one LEGENDARY. Pool = anything obtainable in Emerald —
      ‼ derive it from `modules/obtainability.py` + `emerald_obtainability.json`, never a
      hand-written list, and check whether that model counts event-only species (Mew,
      Deoxys, Jirachi, Ho-Oh, Lugia) as obtainable. Honest note: every Hoenn legendary is a
      late-game static, and the frontier is ~Badge 3, so the legendary favourite will do
      NOTHING for run diversity yet — build it, log it, expect nothing from it for now.
      ‼ The rival / Wally / E4 rosters are NOT yet decomp-verified (gym leaders are, in
      `modules/badge_case.py`); they need that before the type check can use them.
      Still open: preference strength; per-run vs per-lane (recommend per run).

## Next (user-set order 2026-07-19: #30 â†’ #31 â†’ #32, THEN the first wave below)
> #30/#31/#32 are BUILT + ADVERSARIALLY VERIFIED in sandbox (clean pass:
> money cheat byte-safe 56/56, GUI nav 28/28, no code bugs). AWAITING USER
> OK to promote to custom. In-game confirms still pending (filled-slot
> composites, hover with real stats, money effect, controller feel on Ally).
- [ ] #30 â€” Handheld & GUI refinements (user-specified 2026-07-19):
      (a) Persistent "Handheld Mode" button â€” move it out of the Play/
      Controls tab into an always-visible header (in the drawer: right of
      the "TOOLS" text; desktop: a header row above the tabs) so it shows on
      every tab.
      (b) Handheld menu relocation â€” in handheld mode the Tk top menu
      (Emulator/Profile/View/Help) must NOT appear at all (even with the
      drawer open; reverses the earlier "menu shows with drawer" behavior
      for handheld). Surface those commands as buttons/sections inside the
      PLAY tab instead. Desktop keeps the normal menu bar.
      (c) Left Party Section â€” a vertical party strip to the LEFT of the
      emulator video, in BOTH desktop and handheld: 6 slots, 1 mon/row.
      Empty slot = PokÃ© Ball sprite; filled slot = the mon's sprite
      composited over its caught-ball sprite (ball BEHIND, from
      `pokemon.poke_ball`; ball art at sprites/items/<Ball>.png).
      (d) Hover stats â€” hovering (mouse) over a Left Party slot shows ALL
      that mon's stats (level/IVs/nature/ability/moves/â€¦) in a tooltip;
      SAME hover-stats on the Party tab rows; must also be reachable via the
      gamepad-GUI navigation (#32).
- [ ] #31 â€” Adjustable money cheat: in the CHEATS card, a money entry
      pre-filled with the character's CURRENT money (read live), editable to
      any value, + a "Lock" toggle that freezes money at the typed value
      (on = keep re-applying that exact value; off = stop). Refines the
      existing Max/Infinite money.
- [ ] #32 â€” â˜… Gamepad-driven GUI navigation (roadmap F2, PRIORITIZED by
      user to come right after #30/#31): drive the dashboard with the ROG/
      Xbox controller (D-pad/stick move focus across tabs/cards/buttons/
      party, A activates, incl. triggering the party hover-stats). Distinct
      from the existing in-GAME gamepad input (Manual mode).

## Adjustments (user-requested 2026-07-19)
- [x] #36 â€” Left Party balls enlarged 52â†’104px (ball visible behind mon)
      (ce66eb78).
- [x] #37 â€” Party hover tooltip restyled PokÃ©mon-themed (type badges, IV
      grid, moves, sprite) (ce66eb78).
- [x] #38 â€” Gamepad GUI-nav gated to drawer-open only (no more gameplay
      interruption) (ce66eb78).
- [x] #39 â€” Auto-DECLINE new move learning (default `new_move: cancel`;
      seam for future move-intelligence at
      DefaultBattleStrategy.which_move_should_be_replaced) (25fac025).
      User's placed battle.yml also set to cancel.
- [x] #40 â€” Catch-ball allowlist (d5573234): "CATCH BALLS" card (checkbox+
      icon per ball) filters catch.py::_get_best_poke_ball; catch_balls.yml
      global+per-profile; default protects Master Ball. Live-verified on the
      real save. (Live catch in a real battle still pending.)
- [~] #36b â€” Party balls enlarged further to 140px (~2.7Ã—); reads clearly
      behind smaller mons, big sprites (Celebi/Sceptile) still partly cover.
      Capped by column height â€” could go scrollable for a true 5Ã— if the
      user wants. (d5573234)
- [x] #S â€” User's real save placed: "Nick - Emerald" (progressed) +
      "-restored" + global configs into custom/sandbox profiles/
      (gitignored). LIVE TEST on real party running.

## User rulings + new round (2026-07-19)
- [x] RULINGS: Latias+Latios BOTH obtainable (218/386); Surskit unobtainable
      (c2707bad).
- [x] #46 â€” Hover tooltip ball ~3Ã— (fixed thumbnail no-op bug) (c2707bad).
- [x] #47 â€” Opportunistic catch: any SHINY (even owned) caught (c2707bad).
- [x] PROMOTE-2 â€” whole batch promoted to custom w/ extensive intent docs
      (DIVERGENCE-LOG aâ€“i + DOCUMENTATION/05-hunting-and-livingdex.md);
      live-verified on the real save; 29b9aae5.
- [ ] #24 â€” STORY-MODE BOT (design-first, multi-pass/triple-check): play
      from a fresh save (user-set name; Oak intro/gender/name; Littleroot
      start) OR continue existing; goal = beat Elite 4 + complete the game
      (eventually pokedex); CHUNKED into chapters; must build+maintain a
      team; enumerate EVERY key event/interaction/item/requirement to
      progress + how to obtain progression items. Design â†’ 12-STORYMODE-
      DESIGN.md, several verification passes before building.
      - PROGRESS (2026-07-20): a fresh game auto-plays through **GYM 1 (Stone
        Badge)** â€” introâ†’starterâ†’first battleâ†’PokÃ©dexâ†’trainâ†’rivalâ†’Petalburgâ†’
        Dad/Wallyâ†’Route104â†’Petalburg Woods (Aqua scene)â†’Rustboroâ†’Roxanne.
        Legs 1-2 promoted to custom; legs 3-4 + Gym 1 in sandbox (awaiting
        testâ†’promote). Fixed the Woods-door stall (ML-9) in BOTH builds. NEXT:
        Chapter 4 (deliver Devon Goods â†’ Rusturf Tunnel â†’ Dewford / Gym 2).
        Low-pri OPEN: chapters.py Ch2 completion-flag bug.
      - PROGRESS (2026-07-24 overnight): fresh runs auto-play through GYM 4
        (Heat Badge) organically (3/5 lanes, batch 20260724-004252). Ch12
        BUILT + WIRED (Segment 12a/b/c: Lavaridge-Petalburg direct route,
        Wanda-wall smashes, sign-script gym doors, Norman, auto Surf handoff,
        teach Surf) - live-iterating from flannery_done (travel proven, gym
        chain walking). KI-15 FIXED (3 proven fixes); KI-17 opened (after-
        faint reshow freeze, 2 states captured, Gemini-diagnosed DMA race,
        sweep hardened per the analysis - validation pending).
- [~] #24-move â€” SMART MOVE-LEARNING (user 2026-07-20): DONE â€” Story strategy
      `which_move_should_be_replaced` override keeps every PokÃ©mon combat-capable
      (never trades a damaging move for a status move), preserves type coverage,
      and skips no-gain moves; overrides the stock `new_move: cancel` decline.
      In both builds, unit-verified. REMAINING (folds into #24-team): status-move
      UTILITY ranking (value Sleep Powder/heal over Growl) rather than treating
      all status moves as equal.
- [~] #24-resume â€” RESUME-FROM-ANYWHERE (user 2026-07-20): v1 DONE â€” segmented
      flag-gated run() resumes from a fresh game / resumed save / hand-played
      state, skipping finished segments (fixed the "thinks I need Wally"
      mis-detection via the HIDE_PETALBURG_CITY_WALLYS_MOM flag). REMAINING:
      finer per-STEP resume with each step self-locating from any tile; FAST
      travel (Fly/Teleport/Escape Rope when available, gated by HMs/badges/items
      per #42); title-screen-with-save auto-Continue; reliable completion flags
      for chapters past Gym 1. Design Â§RS.
- [ ] #24-autosave â€” AUTO CHAPTER SAVE-STATE (sandbox testing aid; user
      2026-07-20). After each scripted chapter/segment completes in StoryMode
      (SANDBOX ONLY), auto-save a save state named by chapter into `states/` so
      chapters can be tested/resumed fast. TOGGLE in the Play tab, DEFAULT ON,
      safely toggleable on/off even while the bot runs (the story generator reads
      the flag at SEGMENT BOUNDARIES, so flipping it never interrupts). Implement
      by hooking the segment boundaries already in `StoryMode.run()` (Â§RS).
      **APPLY ONLY AFTER the user green-lights the current story build** (it
      touches run()); until then this is a note. Save quickly at a boundary
      (get_save_state + write) â€” negligible one-frame pause.
- [x] #24-loadpage â€” LOAD-STATE POPUP PAGINATION (user 2026-07-20): DONE both
      builds. `load_state_window.py` now shows 5 states/page and lazily renders
      only the current page's thumbnails (Prev/Next + arrow/PageUp-Down + page
      label; nav auto-hidden for one page). Fixes the slow-open with a full
      `states/` folder (was decoding up to 128 PNGs at once).
- [ ] #24-defeat â€” DEFEAT RESPONSE (user 2026-07-20; design Â§DR). What the bot
      does when it LOSES a battle, as a settings-popup choice:
      (A) "Reload save state" = today's watchdog behaviour, made a toggle; verify
      the resume-after-reload rough edges (the segmented resume Â§RS already fixes
      most â€” the old run() stranded the bot on any restart; also ensure watchdog
      snapshots are CLEAN OVERWORLD states, never mid-battle/scene).
      (B) "Play through & retry" = ride out the whiteout â†’ respawn (PokÃ© Center /
      early houses) â†’ recalc position + story segment (Â§RS) â†’ MATCHUP ASSESS (avg
      enemy vs own level, team size, type/move coverage) â†’ train/adjust team
      (#24-team) if outmatched â†’ escalate on repeated loss â†’ retry. Mode B = Â§RS +
      matchup gate + #24-team, one engine. Sub-parts: a small matchup scorer;
      whiteout ride-out; failure/attempt tracking per objective.
- [~] #24-evo â€” EVOLUTION policy (user 2026-07-20): CURRENT (sandbox+custom) =
      ALLOW ALL evolutions (`should_allow_evolution â†’ True`, overriding the stock
      `stop_evolution`) â€” fixes the Lv16 evolve+move-learn hang and strengthens
      the team. POPUP options to add (#24-ui): **allow all (default on) / random
      evolution / no evolution**. Robustness the bot must have (verify): RECOGNIZE
      when an evolution happens, navigate the evolution CUTSCENE, and handle the
      accept/deny of a new move + deleting an old one to replace it (uses the
      stock evolveâ†’learn path + `which_move_should_be_replaced`). "Random" mode =
      per-PokÃ©mon coin-flip whether to evolve (organic team variety, ties #24-team).
- [ ] #24-team â€” ORGANIC TEAM-BUILDING / helper acquisition (user 2026-07-20;
      design in 12-STORYMODE-DESIGN Â§TB). Bot builds a team to beat gyms/trainers
      but decides to catch "helpers" ORGANICALLY: a rising "recruit urge" that
      grows with failed/struggled battles (increasing re-rolls/odds), weighted by
      real team gaps (type matchup vs the fight, team type-diversity, move
      coverage), pulling candidates from the obtainability+reachability data
      (#41/#42). Random/human-like, not a min-maxer. Needed for Torchic-vs-Roxanne
      and later type-hard gyms; implement when a gym requires it.
- [ ] #24-shops â€” MAP SHOPS AS REACHED (user 2026-07-21; planning doc Â§4). Each mart
      has its own layout AND stock/order; the buy code is already shop-agnostic
      (universal task-driven flow + `_mart_item_row` reads stock live). So map each
      shop's ENTRY facts (mart map, clerk-approach tile, facing) when first reached,
      verify live, add an Atlas row. SPECIAL: **Lilycove Department Store** is
      MULTI-FLOOR (per-floor shop + stock, elevator nav); the **Elite Four PokÃ©
      Center** has a shop + mart; Slateport stalls / TM sellers use non-standard
      menus. Do NOT map all shops up front (unreachable â†’ can't verify).
- [ ] #24-pc â€” PC / BOX TEAM MANAGEMENT (user 2026-07-21; planning doc Â§4b). Advanced
      team development via the PokÃ©mon Storage PC: store / move / withdraw PokÃ©mon
      (and items). Map PC access points (every PokÃ© Center + player's-house PC) and
      the PC UI (Deposit/Withdraw/Move, box navigation, partyâ†”box swaps, item
      storage). Enables swapping in a better-matched mon per gym and parking
      over-levelled/redundant catches. Build when a fight needs it; ties #24-team /
      Â§7 matchup awareness. PokÃ© Centers are otherwise near-identical (generic code
      handles them) â€” only map PC/layout exceptions (e.g. the E4 PokÃ© Center).
- [x] #24-resume â€” SEGMENT 1 RESUME BUG FIXED (2026-07-21). Pre-PokÃ©dex
      recovery/resume re-ran the scripted intro from the truck â†’ derail loop
      ("stuck after respawn"). Split Segment 1: scripted intro gated on
      `_has_starter()`; trainâ†’rivalâ†’PokÃ©dex resumable + flag-gated. Derail budget
      hardened (monotonic party `_progress_sig`; patient recovery). Verified in
      harness. Sandbox (early_game.py, story_mode.py). See CHANGELOG/MISTAKES 07-21.
- [x] #24-freeze â€” OLDALE PC FREEZE **FIXED** (user 2026-07-21). Root cause (from the
      user's real-bot debug log's generator call stack): heal returned while the
      overworld was transiently non-controllable â†’ healâ†’go-to-rival navigate choked â†’
      derail â†’ re-heal â†’ endless heal/leave/re-enter loop â†’ Manual. FIX:
      heal_in_pokemon_center waits for a STABLE controllable overworld after the exit
      warp. Downstream: StoryCatchStrategy flees instead of Manual when out of balls.
      Validated route103â†’Rustboroâ†’Route116 catching, 0 derails/Manual. Old note below
      kept for history.
      ~~POST-BATTLE TRANSITION FREEZE (the likely real "stuck at Oldale PC").~~ After a training battle (flee/level-up/move-learn, e.g.
      Mudkip Water Gun @L10) the return-to-overworld transition leaves the overworld
      non-controllable while the bot acts (navigate / walk to the Oldale nurse) â†’ can
      hard-freeze (nurse heal dialogue never starts). REAL (harness == real
      main_loop), timing/starter-sensitive (default starter "random"; Treecko passed,
      Mudkip hits it). Offline repro hampered by save-state reload artifacts. NEXT:
      user validates on real PC (force `starter: mudkip`, fresh game) and reports;
      then decide a deeper "settle before acting" fix (heal_in_pokemon_center nurse
      interaction + story navigations) vs a training-flow workaround.
- [x] #24-debuglog â€” DEBUG LOGGING TOGGLE (user 2026-07-21). Opt-in "Debug Logging"
      in the Run (bot-mode) menu (both GUIs), default off â†’ `modules/debug_logger.py`
      writes an extensive structured log to `<profile>/debug-logs/` (event stream +
      stuck dumps with the generator call stack). For diagnosing Bug #2 (#24-freeze)
      from a shared real-bot log. Built + validated in sandbox. See CHANGELOG 07-21.
- [x] #24-swaptrain â€” SWAP-TRAINING **DONE** (user 2026-07-21). Fixes the
      under-levelled-mon training loop: `SwapTrainBattleStrategy` switches a trainee
      that's â‰¥2 levels below the wild foe to the strongest team-mate turn 1 (shares
      XP, no fainting/heal-churn). Gated around `train_team`. Validated Poochyena
      L4â†’L7, 0 heals/faints. Commit ef812c0e.
- [~] #24-trainmap â€” AREA-APPROPRIATE TRAINING (user 2026-07-21, Option 1).
      **ROUTING HALF DONE (2026-07-24):** `modules/story/training_areas.py` carries
      `TRAINING_GRASS` (10 areas with VERIFIED spin tiles + level bands), `AREA_PREREQ`
      (surf/region gates), `best_training_area(team_level, min_wild_max=, allow=)` and
      `estimate_frames_to_level()`. `_prepare_for_fight` calls it with the
      `_training_area_allowed` reachability predicate and RELOCATES via
      `_goto_training_area` (warp-aware), healing at the PC nearest THAT area — this is
      what stopped the Norman fodder grind. Swap-train (#24-swaptrain) remains the
      anywhere fallback.
      **REMAINING: the `PENDING_GRASS` spin tiles** — Route 104, Petalburg Woods,
      Rusturf Tunnel and Granite Cave 1F still have `None` tiles, so they can never be
      proposed. Fill each as the map is reached (two-way sweep from a real story anchor,
      per the Route 111/114 lesson: same-map connectivity does NOT imply the story can
      get there), then move the entry into `TRAINING_GRASS`.
      Related: `#24-regionreach` (the reachability predicate itself), `#24-watertrain`,
      `#24-healverify`.
      ‼ **NOW ENFORCED IN CODE — see `training_areas.NO_RETURN_GROUNDS`** (2026-07-26).
      This paragraph is history; the table is the authority, and both training pickers
      refuse those maps before any reachability check. It was moved into code because
      this prose was re-derived from scratch by a probe cycle on 2026-07-26 (08-MISTAKES).
      ‼ LAVARIDGE HAS NO REACHABLE TRAINING GRASS (two-way sweep 2026-07-23,
      `tools/story-dev/jaggedgrass_probe.py`): Jagged Pass cannot be re-entered from
      the town (one-way ledges) and Route 112's lower grass has no return path. So
      Segment 11d (Flannery) preps with a Water lead + heal and NO grind; a L29-31
      team wins but is marginal (one whiteout in validation run 11). First concrete
      customer for this item.
- [ ] #24-ui â€” STORY-BOT PRE-RUN SETTINGS POPUP (user 2026-07-20). A popup/menu
      shown BEFORE the Story bot runs to set: player name; starter nickname mode
      (none / defined / random); starter choice (specific / random); + other
      settings TBD. Front-end for the existing `<profile>/story.yml`
      (character_name/gender/starter/starter_nickname already read by
      modules/story/config.py). WORK ON THIS ONLY AFTER the bot is finished and
      tested 100% (user directive). Popup also hosts the #24-autosave toggle
      (auto chapter save-state, default on) and the #24-defeat "Defeat response"
      section (Reload-save-state vs Play-through-and-retry + sub-toggles).

## Living-Dex deepening (user-requested 2026-07-19; DESIGN-FIRST, no cutting corners)
- [ ] #41 â€” Obtainability model: classify every species â€” wild / evolution
      (method+from) / in-game trade / gift / static / roamer / event â€” so the
      Living Dex knows trade-evolutions and evolve-only / trade-only mons
      (must obtain pre-evo + evolve, or manual trade), not just "no wild â†’
      skip". (design: 11-LIVINGDEX-DESIGN.md)
- [ ] #42 â€” Reachability/requirement gating: hunt + living-dex must skip a
      target when the area/encounter needs a capability the player lacks
      (Surf/Cut/Rock Smash/Dive/Waterfall HMs, the right fishing rod, badges
      for HM use, story-flag area access). Read owned HMs/rods/badges/flags
      from the save.
- [x] #43 â€” Living Dex OPPORTUNISTIC catching: catch ANY wanted-uncaught
      species en route (target only drives travel); live-dex-driven
      advancement; 22/22 units (a8840769).
- [x] #44 â€” Party ball rework: strip now clean mon sprites (no ball
      backdrop); caught ball moved to the hover tooltip as an icon+name row.
      Live-verified on the real save (9c2b1f94).
- [x] #41-evo/#42-easy â€” obtainability (evolution) + capability gating
      built (ceb7343e; 30/30 units; live save read Old/Good/Super Rod;
      panel shows 128 wild/147 evolve/102 special-trade). obtainability.py
      + capabilities.py.
- [x] #41-research â€” compiled + fact-checked Emerald obtainability lists
      (gift 7/static 8/roamer 1/event 6/breeding 3/special 1/unobtainable 79;
      in-game trades rescue nothing). Census sums to 386; "show both"
      denominators exposed (217/386 obtainable without trading). 16/16 units.
      modules/data/emerald_obtainability.json + obtainability.py. Fact-check
      report + citations: 11-LIVINGDEX-DESIGN.md (Phase #41-research). REMAINING
      for full #41: wire living_dex_mode target selection to plan_for's gate +
      route gift/static/roamer to reset modes; auto-evolve helper.
- [ ] #42-hard â€” HM-gated cross-map reachability in the nav graph (v2).
- [ ] #45 â€” (FUTURE, with story-mode bot #24) enumerate story instances the
      bot can automate, and let hunt/living-dex progress the story to unlock
      areas/capabilities needed for dex completion.

## Now-ish (user-added 2026-07-19, ahead of first wave)
- [ ] #33 â€” GUI fixes (in sandbox): Left Party Section ALWAYS visible in
      both modes regardless of drawer state; unified open/close â€” PokÃ©ball
      opens the side tool menu + a Close/Hide collapses it in BOTH handheld
      AND desktop (desktop can hide tools to see more emulator).
- [ ] #34 â€” Living POKÃ‰DEX tab: search all Emerald species; caught mark +
      shinies-caught count (from stats.db) + full dex info (types/abilities/
      base stats/dex#/category/flavor) + learnable moves (level-up/TM/HM/
      tutor/egg) â€” offline Bulbapedia. Needs battle sprite + dex artwork.
      RESEARCH-FIRST (see 10-DEX-RESEARCH.md): inventory bot data â†’ gap-fill
      â†’ fact-check â†’ THEN build.
- [ ] #35 â€” ITEM-DEX tab: search all items; total-collected-historically +
      currently-held counters + item info + map locations + used/held/
      dropped-by PokÃ©mon. Needs item sprite + inventory image. Same
      research-first flow as #34 (10-DEX-RESEARCH.md).

## First wave (after #30-#32 + #33-#35 â€” agreed direction 2026-07-19)
- [ ] #22 â€” â˜… Watchdog / auto-recovery: BUILT IN SANDBOX 2026-07-19
      (c7d25305; encounter-stall + drop-to-Manual + frame-freeze detection,
      bounded recovery ladder [re-assert â†’ savestate-reload w/ safety backup
      â†’ give up to Manual], overworld-gated, alerts, GUI status line; 17/17
      self-tests + recovery-path safety confirmed). Remaining: live-hunt
      softlock recovery needs a progressed save; independent adversarial
      pass to bundle with the batch verification before promotion.
- [ ] #9 â€” Hunt planner: v1 + v2 BUILT IN SANDBOX 2026-07-19 (6141d96f,
      4df17747). Encounter index from ROM (132 species/805 locations,
      19/19 fact-check); Hunt tab shows ranked locations + mode; v2 adds an
      encounter-tile finder + "Hunt (Custom)" mode = one-click travel (via
      global nav) + hunt. KI-6 tab overcrowding FIXED (two-row tab bar).
      REMAINING: live navigate+hunt on a progressed save; Rock Smash has no
      auto-tile finder (degrades to manual). Independent adversarial pass at
      promotion time.
- [ ] #23 â€” Living-Dex orchestrator: v1 BUILT IN SANDBOX 2026-07-19
      (34c5f461; living_dex.py target derivation + "Living Dex (Custom)"
      mode: travelâ†’huntâ†’catch-first-uncaughtâ†’advance; catch-intent verified;
      16/16 units + real-ROM fact-check 132 targets). REMAINING: live
      autonomous run needs a progressed save; screenshot harness needs a fix
      after #33 layout change; independent adversarial pass at promotion.
- [ ] #25 â€” PokÃ©mon detail + PC box viewer: click a party/box mon â†’ full
      stats (IVs/nature/ability/moves); browse PC boxes with sprites. (M)
- [ ] #11 â€” Analytics suite: v1 BUILT IN SANDBOX 2026-07-19 (8094bb05;
      analytics.py + ANALYTICS card in Stats tab: encounter-rate sparkline,
      luck meter [actual vs binomial 1/8192, Ïƒ/z/verdict], sortable+
      filterable stats browser w/ sprites; 26/26 units). REMAINING:
      meaningful values need a populated stats.db (real hunt); independent
      pass at promotion.
- [ ] #27 â€” Battery-aware mode (ROG Ally): throttle speed/fps on low
      battery, pause on critical, resume on charge. (S-M)
- [ ] #28 â€” Polished mobile remote: phone-optimized web dashboard view to
      monitor 24/7 hunts (builds on the existing HTTP API). (M)

## Later / icebox (catalog in 09-FEATURE-BRAINSTORM.md; user re-orders/culls)
- [ ] #24 â€” Story auto-player (trainer/gym battler) â€” most ambitious, most
      transformative: progress the game to bootstrap a save to any hunt. (L)
- [ ] #26 â€” Theme system (selectable color themes; palette is centralized). (S-M)
- [ ] #29 â€” Box manager / auto-release by IV/nature/shiny filter (prevents
      full-box stalls in long hunts). (M)
- [ ] #13 â€” Macro composer v2: chain macros + repeat counts + conditions. (M-L)
- [ ] #14 â€” Profile manager UI (create/duplicate/rename/delete). (S-M)
- [ ] #15 â€” Config editor GUI (catch_block/battle/cheats + CCF builder). (M)
- [ ] #16 â€” PKHeX quick-export (.pk3 of any party/box mon). (S)
- [ ] #17 â€” Multi-instance manager (several profiles, aggregating board). (L)
- [ ] #19 â€” Stream overlay theme refresh (OBS overlay â†’ dashboard style). (S-M)
- [ ] #6 â€” Idea backlog: everything else in 09-FEATURE-BRAINSTORM.md
      (egg-hatch optimizer, catch profiles, Nuzlocke, goals panel, log
      viewer, setup wizard, keybinding editor, shiny gallery, hunt-summary
      cards, cross-session history, stream chat, webhooks, crash-safe
      savestate ring, health monitor, scheduled hunts, gamepad-driven GUI,
      RNG manip, cheat presets, plugin loader UI).

## Promoted to custom 2026-07-19 (built; awaiting user in-game confirmation)
- [~] #3 â€” Custom automations + Patrol (v3 multi-map/global-nav). Awaiting
      user's in-game play-test.
- [~] #7 â€” Sandbox enhancement round (backup/restore + cloud, macros,
      multi-map Patrol, GUI pack) â€” built, adversarially verified (16-bug
      round), promoted.
- [~] #8 â€” Warp-aware global pathfinding â€” promoted; user cross-warp walk pending.
- [~] #10 â€” Gamepad + handheld menu-hide â€” promoted; user real-pad test pending.
- [~] #12 â€” Shiny alerts â€” promoted; user sees a live shiny fire it pending.
- [~] #18 â€” Auto-update notice â€” promoted; observe on a stale checkout pending.
- [~] #20 â€” Cloud save-sync v2 (off by default) â€” promoted; desktopâ†”Ally run pending.
- [~] #21 â€” Game cheat menu (+ tabbed GUI, full-dex sprite picker, XP bars,
      topmost dialogs) â€” promoted; user in-game effect test pending.

## Story bot (#24) — open backlog
> Two groups: the PRIORITY block was added 2026-07-25 by the doc audit (these IDs were
> referenced all over the changelog/handoff but had no punch-list entry at all). The rest
> were sitting under `## Done` while still open (`- [ ]`) and were moved here the same
> day — not reworded, only relocated.

### Priority block (added 2026-07-25 — previously referenced but unlisted)
- [~] **#24-whiteout — MEASURED 2026-07-25; half fixed, half is now `#24-counters` phase 2.**
      ‼ It is **not** attrition in the general sense. Census of all 5 night5 runs (~128
      losses; losses:whiteouts are 1:1 — no potion/revive layer exists, so a loss always
      whites out): **~83% of losses are GYM LEADERS** — `PETALBURG_CITY_GYM` 38 (Norman),
      `MAUVILLE_CITY_GYM` 24 (Wattson), `FORTREE_CITY_GYM` 20 (Winona),
      `LAVARIDGE_TOWN_GYM_1F` 18 (Flannery), ROUTE110 10, Dewford+Rustboro 6. Travel and
      wild encounters are noise by comparison.
      **What boss-as-training-vehicle actually delivers** (run3, Norman, traced): 27
      attempts / **508,000 frames** (~19k each) / **+2-4 levels total** / **KOs flat at
      1-2 of 4 for all 27** / a L15 Shroomish carried untrained the whole way.
      **DONE:** the plateau detector was **power-blind** and could never have fired on
      Norman — its "we have an answer" veto accepted **Rock Smash (20 power)**, the HM
      the bot must carry, because Fighting is 2.0x vs Normal. Now requires
      `base_power x effectiveness x STAB >= CREDIBLE_ANSWER_POWER` (60). A/B on the real
      party: `(False, []) -> (True, ['Fighting'])`. Its silent `except` now warns.
      (Note the night5 logs PRE-DATE the whole counter chain — 07:36 vs 09:47-13:27 — so
      those 27 attempts had no guard at all, and would still have had none without this.)
      **LIVE-CONFIRMED 2026-07-25** (batch `20260725-194810`, 5 fresh lanes): the guard
      fired on Norman at **exactly 6 losses** in 2 runs (was 27), Petalburg-gym losses
      38 -> 14 batch-wide, and **1/5 reached the frontier** (baseline 0/5).
      **✅ TRAVEL ATTRITION FIXED 2026-07-26 — SURVIVAL MODE.** run01 lost **25 times on
      ROUTE110** (largest single cluster, 31 of 66 batch-wide). Root cause was NOT training:
      with no `train_team` session, `on_battle_started` falls through to
      `LevelUpTravelBattleStrategy`, which fights every wild to level the lead and "flees only
      at low HP, which the training loop covers by healing" — but a TRAVEL leg has no training
      loop and so never heals. After `SURVIVAL_WHITEOUT_THRESHOLD` (3) defeats on a map, wild
      battles there are FLED. Narrow by design and asserted in `repro_survival_mode.py` (7
      cases): wild only (trainers are un-fleeable, boss path untouched), never during
      `train_team`, per-map. On the real run01 state it flees — 22 of those 25 whiteouts
      would not have happened.
      **REMAINING:** the bot now STOPS with a named counter instead of grinding forever.
      Actually travelling/catching/training it is `#24-counters` phase 2 — the two items
      are the same problem from opposite ends. Also still unbuilt: a potions/healing
      layer (`#24-provisions`) so a loss is not automatically a whiteout, and benching
      dead-weight party members (a L15 in a L30+ team is a free loss).
- [ ] **#24-pokenav-faithful — the FAITHFUL PokéNav tutorial is being skipped 8 runs out of 9.**
      ‼ **This is a RECURRENCE of the `[x]` entry in `## Done` (2026-07-22), not a duplicate.**
      That entry closed the first sighting as "user ran VIDEO OFF — the renderer-gated fallback
      fired as designed" and explicitly said *"check why the faithful path didn't engage next
      time it recurs"*. It recurred; this is that check. The same id intentionally appears twice.
      Measured across the user's real-hardware logs (2026-07-26): ONE run played it faithfully
      ("PokéNav Match-Call tutorial (calling Mr. Stone)... done (called Mr. Stone)"), the other
      EIGHT fell back to "clearing the forced PokéNav Match-Call tutorial (state-write to vanilla
      end-state)". Not a breakage — the fallback reproduces vanilla's exact end-state and never
      hangs, so runs continue — but the standing faithfulness directive makes the state-write a
      LAST RESORT, and it has quietly become the norm on real hardware where the renderer IS on
      (which is the condition the faithful path needs). The 1 success proves the faithful path
      still works, so this is a trigger/stall-detection question, not a dead feature.
      Start by logging WHY the fallback fired (renderer state, which stall bound tripped) —
      today nothing records the reason, so the choice is invisible.
- [ ] **#24-npcheal — heal at an NPC, not only at a Poké Center.** Re-pair the Route 111
      training band to `ROUTE111_OLD_LADYS_REST_STOP` (decomp-cited: a full, ungated,
      repeatable heal — **96 steps vs 213** to Fallarbor). Blocked on a heal-at-NPC
      helper: every current heal path assumes a Poké Center layout (KI-19).
- [~] **#24-counters — CATCH A TYPE COUNTER when the boss plan cannot converge (KI-23).**
      **Phase 1 DONE (2026-07-25):** `_boss_plan_is_hopeless` detects non-convergence
      (6 losses + flat KOs + nothing hitting the boss's `ace_types` for ≥2.0), computes
      the needed types from the real type chart, and `counter_plan.find_counter_candidates`
      ranks catch targets over the whole-game encounter index, gated by
      `_counter_area_allowed` → `region_reach`. Proven from the Winona-era save: it names
      **Electrike on ROUTE118 (29,15), L24-26, 30% — REACHABLE**, where the old predicate
      returned zero. Fail-safe in all three planner outcomes (`repro_counter_wiring.py`).
      **Phase 2 NOT STARTED:** actually travelling to the target, catching it, and training
      it. Today the bot converts an unbounded loop into a bounded stop that NAMES the fix;
      acting on it is the next step and needs a live run to validate, not a repro.
      **SPEC + ECONOMICS: `12-STORYMODE-DESIGN.md` §CC2 (+ its 2026-07-26 update).**
      Blocker #2 (ranking) is CLOSED — candidates now sort by ESTIMATED COST (frames to
      find + frames to train to the team's level) instead of encounter rate; measured
      effect on the real save: Machop/Jagged Pass 75,949 vs Makuhita/Granite Cave 315,260,
      i.e. the old order preferred the 4.2x more expensive option.
      ‼ **BLOCKERS (1), (3) and (4) ARE CLOSED — 2026-07-30.** All three were the same
      bug wearing three hats, and the fix is one fail-closed predicate:
      `training_areas.hunt_ground_tile()` (whitelist: `TRAINING_GRASS` + the new
      `HUNTING_GROUNDS`) → `counter_plan` candidates carry `huntable` →
      `counter_plan.best_huntable()` is the ONLY selector an executor may call.
      Proof `repro_counter_huntable.py` (offline, real ROM tables, ALL PASS).
      (1) **Tiles — the premise was WRONG.** "Every candidate has `tile: None`" is false:
          Wattson's ROUTE111 (25,55) and Winona's ROUTE118 (29,15) answers both carry
          swept tiles. Only the *Fighting* answers lacked one, and FIERY_PATH **(18,19)**
          is now recorded in `HUNTING_GROUNDS` — the tile `story_harness --driver
          fierycave` actually walked; legs 1+2 PASS, only the heal leg fails, and a
          catch-and-leave hunt never walks it. **All three derail classes now resolve to
          a swept, walkable destination.**
      (3)+(4) **Victory Road / story interiors — solved by the whitelist, not by
          `KNOWN_GATES`.** The blacklist route would be an ever-growing list of game facts
          written from memory (forbidden). And reachability could never have gated it:
          run live from the Winona-era save, `_counter_area_allowed` reports **Magma
          Hideout, Shoal Cave and the Safari Zone as `reachable`**, 10/10 candidates.
          Confirmed hazard, not a theoretical one: rank 1 for Norman is **Hariyama @
          VICTORY_ROAD_B1F L38-42**, because the cost model prices "train it to the team's
          level" at ~0 for a wild already above the team — so it PREFERS endgame maps.
          Jagged Pass proves the gate has teeth: it ranks ABOVE Fiery Path (134,702 vs
          250,297 frames) and is refused via `NO_RETURN_GROUNDS`.
      ‼ **REMAINING BLOCKER: (2) the executor itself** — travel to `best_huntable()`'s
          tile, catch (a `COUNTER_CATCH_TARGET_DEX` catch-on-sight branch mirroring
          `HM_CATCH_TARGET_DEX`), and TRAIN the catch. See `21-TEAM-POLICY-DESIGN.md` §5.
          ‼ The train step is NOT optional garnish: catching a L15 Machop for a L30 team
          and not training it converts today's bounded, honest stop into an unbounded
          loop, because `_boss_plan_is_hopeless` then answers "not hopeless" for ever
          after. Bound the OUTCOME (playbook rule 3).
      ‼ **Value check before building:** priced against the measured cost of the current
      behaviour (run05 lost to Norman 21x ~ 399,000 frames; run3 27x = 508,000), a Machop
      costs 98,877 and a Makuhita 363,982 — but the only counter the LIVE predicate
      accepted was the Makuhita, i.e. ~9% better than doing nothing. **Phase 2's value is
      gated by reachability, not ranking** — widen reachability first or it buys little.
- [~] **#24-regionreach — region-scale reachability oracle.** ‼ **A WRONG *YES* COST 2 OF 5
      LIVE RUNS (2026-07-25) — now bounded.** `_training_area_allowed`'s cost model said a
      wrong yes "costs ONE wasted walk, fails RECOVERABLY and loudly"; in batch
      `20260725-194810` it cost the RUN, twice, because the picker is DETERMINISTIC and every
      derail re-picked the same unreachable ROUTE111 (25,55) from Mauville (that tile is
      FALLARBOR-SIDE ONLY — north of the Go-Goggles desert — while `is_map_reachable` is
      correctly True for the map). FIXED generally, not per-tile: new
      `UnreachableDestinationError(BotModeError)` + `StoryMode._training_unreachable`, keyed
      `(standing map, target map, tile)` so a directional ground survives elsewhere
      (`repro_training_unreachable.py`, 5 cases). This bounds EVERY future `KNOWN_GATES` gap
      to one wasted walk — which is the point of (a) below.
      **BUILT + PROVEN**
      (`modules/story/region_reach.py`, `repro_region_reach.py`): a graph from the ROM's own
      `MapConnections` + warps, capability gates, and `why_unreachable()` reasons that keep
      "no connection path" / "needs Surf at A↔B" / "reachable but N hops away" as three
      distinct facts. **STILL OPEN:**
      (a) **`KNOWN_GATES` must GROW** — it holds ONE hand-verified entry (Dewford's two sea
      edges), so any gate not derivable from ROM data reads as UNGATED. This oracle fails
      OPEN where the old one failed CLOSED; that is the right direction for a planner but
      must be grown before it gates anything irreversible.
      (b) ~~Only one caller is wired~~ **DONE 2026-07-25 — BOTH callers now use it.**
      `_training_area_allowed` was switched off `calculate_path`; the Winona candidate list
      went from `[False × 10]` to `[True × 5, False × 5]` (Route 118 Electrike reachable).
      Landing it exposed a partial-mock bug in `repro_fodder_grass._stand_at()` that had been
      giving false confidence to every training-logic change for two days (see 08-MISTAKES).
      (c) ~~`repro_counter_plan.py:200` red~~ **RESOLVED 2026-07-25 (user ruling):** the
      non-vacuity check moved off the wide type set (where it required an unreachable entry to
      exist, and so inverted when the predicate was fixed) onto the WINONA set, asserted to
      span both branches — the property the sort proof actually needs. Full repro suite 5/5.
- [ ] #24-edgecost — finer travel cost than a flat 1-hop edge (**DEFERRED**). Uniform
      weighting compresses "same landmass cluster" (1-4 hops) — measured from ROUTE120,
      Lilycove (2) reads as CLOSER than Route 118 (3), the actual answer — because one ROM
      connection can span a whole sea route. If finer granularity is ever needed: weight
      each edge by the source map's traversal length, or price travel in FRAMES so it
      composes with `training_areas.estimate_frames_to_level`. **Not needed until hop count
      demonstrably mis-ranks something** — today `max_hops` is only ever a filter (KI-24b).
- [ ] #24-fortreelive — close the Fortree Kecleon-chokepoint proof properly. The current
      evidence is a strong FAULT-INJECTION proof (flag 969 injected → (25,8) walkable), not
      a live post-flush save. Capture a checkpoint keyed on flag 969 and re-run §6/7
      WITHOUT injection to close it. Residual verification debt only — the live playthrough
      already sets the flag first via `get_devon_scope`.

### Moved out of `## Done` (still open)
- [ ] #24-sanity â€” SELF-CORRECTION / SANITY-CHECK (user 2026-07-20; design Â§SC).
      Story mode must never get permanently derailed: re-validate at every segment
      boundary (did the completion flag actually set? else retry/skip-ahead),
      handle out-of-place execution (self-locate), handle non-monotonic progress
      (reload/blackout moving backward), detect mid-run derailment (expected vs
      actual segment) and re-sync, bounded retries + escalation (ties Â§DR/#24-team),
      stall watch as last resort (Watchdog #22). Unifies Â§RS + Â§DR + #24-team into
      one state-machine engine. Also bounds the Treecko-Lv16 "stuck but not stopped"
      loop class.
- [ ] #24-interrupt â€” INTERRUPTION INTELLIGENCE (user 2026-07-22): the bot should
      KNOW when its current task was interrupted and by WHAT (training spin â†’
      trainer sight-line battle; navigation â†’ PokÃ©Nav call ring; heal walk â†’
      scripted scene; etc.) and resume the task accordingly instead of relying on
      the generic derail/retry loop. Today large parts are handled implicitly
      (battle listeners resume travel; _ride_out_scripted_scene; the derail
      recovery re-runs _play) â€” this item is the DELIBERATE design pass: a small
      "current intent" state (what am I doing + resume point) + an interruption
      classifier, so recovery is targeted rather than re-derived. Design first
      (fits the decision-brain seam in doc 13 Â§future).
- [ ] #24-movelock â€” BATTLE ENGINE: move-blocking/locking effects (user
      2026-07-22): Disable (last move unusable), Encore (locked INTO a move for
      N turns), and kin (Taunt â€” status moves blocked; Torment â€” can't repeat;
      Imprison; Choice-item lock later). The turn chooser (get_strongest_move_
      against / move_is_usable) currently ignores these volatile statuses, so a
      blocked move can be selected â†’ wasted turns (the game refuses the input).
      Fix: read the battler's volatile status/disable struct and filter the
      usable-move set; if EVERYTHING is blocked, Struggle happens naturally.
      Validate vs a Roxanne/Brawly-era Disable user (e.g. wild Whismur has none â€”
      find a story trainer with Disable/Encore, or fault-inject the volatile
      struct in the harness).
- [ ] #24-ch8b-museum â€” Oceanic Museum entry gating (KI-11): resolve how the
      Aqua crowd clears so Stern is reachable; then Devon Goods â†’ Stern
      (deliver_devon_goods_to_stern is built). BLOCKS Ch8b/Ch9.
- [ ] #24-freshbatch-rustboro â€” batch run03 (fresh game) 2026-07-22 played
      extensively but HUNG in Rustboro (11,3)=(5,3) area after ~450k frames
      (Torchic start, 4-mon team). Under-investigated; capture a repro from the
      run03 log if it recurs in a future batch.
- [ ] #24-train-efficiency — the same run spent ~240k frames on the pre-rival
      level-floor (L10) and ~200k on the Brawly band (L15) with swap-training.
      Bounded + productive, but slow. Related: an ABRA catch (Teleport-only, can''t
      attack) rode along the whole run at L7 — confirm battler-slot exclusion is
      airtight and consider skipping Abra-class catches for team slots, or routing
      lows to level-matched grass (#24-trainmap).
- [ ] #24-npc-talk-speed — Briney talk-dance polish (user log review 2026-07-22):
      BOTH user-observed oddities are the same subsystem, `_talk_to_wandering_npc`
      (observe a patrol lap -> park beside the route -> face-tap on transit):
      (a) cottage Briney (~3,600 frames of visible maneuvering before the talk at
      (6,2) in Route104_MrBrineysHouse), and (b) post-Brawly "erratic movement
      right of the gym" = the DOCK Briney ambush near (12,9) (~5-7k frames across
      four transient stucks at sail_to_slateport's dock-talk step; it completed
      and sailed — slow, not broken). FIX DESIGN: add a `known_spot` fast-path —
      navigate STRAIGHT to the recorded successful parking tile per NPC (extract
      the exact tiles from validated-run debug logs), wait bounded (~1 lap) for
      the NPC to transit adjacent, face-tap+A; on one failure fall back to the
      full observe-then-park. Keeps the proven adaptive path as the safety net.
- [ ] #24-hm-slaves — HM CARRIER ARCHITECTURE (user directive 2026-07-22 night):
      HMs are infinite-use but unremovable without the Lilycove MOVE DELETER
      (free; the Heart Scale is for Fallarbor''s Move RELEARNER — different NPC).
      Near-term policy: Marshtomp carries Rock Smash + later Strength (learns
      both; physical-type moves suit its Attack — a working mule, not a dead
      slot). Longer-term: dedicated HM slave(s) (Zigzagoon: Cut/Rock Smash/
      Strength/Surf) parked in the POKEMON PC — which requires PC deposit/
      withdraw MACHINERY (party-slot management UI flow) built BEFORE the
      Surf-era chapters (~Ch13+, Route 118 gate). Also: some moves are
      overworld-usable from the party menu (Dig, Teleport, Flash, Sweet Scent)
      — useful shortcuts (Teleport-to-PC, Dig-out-of-caves) worth wiring into
      travel logic once carriers exist.
- [ ] #24-knowledge-base — DEEP GAME KNOWLEDGE BASE (user directive 2026-07-22
      night): per-chapter, during mapping: route items (visible + HIDDEN, both
      in decomp map.jsons), puzzles, secrets, legendary unlock chains + catch
      strategies (Regis braille gates, Sky Pillar/Rayquaza, Groudon/Kyogre story
      beats), gym rosters. Machine layer: the bot''s modules/data already holds
      full species/moves/learnsets/TM-compat — the MOVE-PRIORITY SYSTEM v2
      (#24-movelock: STAB + type coverage + Gen3 physical/special-BY-TYPE
      stat-matching + utility ranking) should QUERY it, not hand-author lists.
- [ ] #24-event-pokemon — EVENT LEGENDARIES, endgame (user directive 2026-07-22
      night): Deoxys (Birth Island via AURORATICKET), Mew (Faraway Island via
      OLD SEA MAP), Jirachi (external event), Latios/Latias roamer choice + the
      EON TICKET (Southern Island second Lati). These need event-only items that
      vanilla distributed via Mystery Gift / e-Reader — the bot must obtain them
      in a way that LOOKS earned and stays quasi-canon (user framing): candidate
      mechanisms to discuss LATER — Mystery Gift spoofing (emulating the
      distribution the game natively supports — most authentic), a scripted
      "delivery man" trigger, or a direct bag write (last resort). Same
      plan/map/test loop as story chapters + a design discussion with the user
      on the acquisition theater BEFORE building. Endgame content — schedule
      after the main story skeleton reaches the Elite Four.
- [ ] #24-provisions — HEALING-ITEM PROVISIONING + STRATEGIC HEALING (user
      directive 2026-07-23): alongside Poké Balls, buy POTIONS (the best tier
      available at the local mart — Potion→Super→Hyper→Full Restore as the
      frontier advances) and keep a sensible stock; then use them with intent:
      in-battle healing when a sweep is worth saving, between-battle healing in
      places with no PC (Victory Road, THE ELITE FOUR — vanilla players stock up
      at the League mart precisely for this). Extends the buy-at-mart machinery
      (shop-agnostic `_mart_item_row` already reads stock live). Design note:
      gate on money reserve like balls; a heal-item strategy layer slots into
      the battle strategies where flee/switch decisions already live.
      !!! PRIORITY RAISED 2026-07-26 (user directive) - AND THE DATA AGREES EMPHATICALLY.
      The old note said "NOT urgent (the fight/train/retry loop carries the mid-game)".
      Batch 20260726-201838 refutes it: LOSSES AND WHITEOUTS ARE 1:1 IN EVERY LANE --
      P1 27 losses / 27 whiteouts, P2 43/44, P3 10/10, P4 12/12. With no potion or revive
      layer, EVERY battle loss becomes a full whiteout: respawn at the last Center, walk
      all the way back, re-fight. A heal-item layer is the single change that breaks that
      1:1, converting the most expensive failure in the game (whiteout + travel) into the
      cheapest (one turn spent on a Potion).
      Build order: (1) BUY -- extend the existing mart machinery, gate on a money reserve
      as Poke Balls already do; (2) USE IN BATTLE -- a heal threshold in the battle-strategy
      layer where flee/switch already decide; (3) USE BETWEEN BATTLES where there is no PC.
      Steps 1+2 alone should measurably cut whiteouts, and that is a DIRECTLY MEASURABLE
      hypothesis: compare whiteouts-per-loss before and after.
      Money is not the blocker -- the Dewford arc alone has 4,924 PokeDollars on foot that
      the bot currently walks past (19-TEAM-BUILDING-DISCUSSION.md 8.2), and the Lilycove
      Dept Store 2F sells up to MAX POTION + Revive (Aqua-hideout recon 2026-07-26). NOT urgent
      (the fight→train→retry loop carries the mid-game) — required before the E4.
- [ ] #24-grasswander - ORGANIC MOVEMENT WHILE TRAINING (user request 2026-07-26).
      Today the bot trains by SPINNING IN PLACE - `spin()`
      (`modules/modes/util/higher_level_actions.py:158`) turns on the spot, wrapped by
      `_story_spin` (`early_game.py:124`) for the whiteout-abort and no-progress watchdog.
      The user wants it to WANDER the grass with human-like movement, mixing in occasional
      spins, so training looks organic instead of robotic.
      !! THIS IS THE SAFE PLACE TO PUT RANDOM MOVEMENT, and the risk profile is INVERTED
      versus travel meandering (#24-meander):
        * On a TRAVEL leg, extra steps mean more wild encounters, which means more battles,
          more damage and more whiteouts. Our dominant failure is travel attrition, so
          meandering there is actively dangerous.
        * While TRAINING, extra steps mean more encounters - which is the entire POINT.
          Wandering costs nothing we did not already want.
      SEAM ALREADY PROVEN: `run_in_circle` (`modules/modes/util/walking.py:706`) shows
      `follow_waypoints` accepts an ARBITRARY waypoint generator. A bounded random-walk
      generator drops straight into that seam - no pathfinder change at all.
      MUST PRESERVE (all three already exist and all three have scar tissue behind them):
        * the whiteout abort in `_story_spin`, or a mid-training whiteout spins forever;
        * the no-EXP-progress watchdog, which is what un-sticks a bot that wandered out of
          the grass - it already handles exactly this failure and must keep working;
        * the leftover-script clear, since an active script SUPPRESSES wild encounters.
      REAL RISKS to bound:
        * wandering OUT of the encounter region (watchdog catches it, but wasted frames);
        * wandering into a TRAINER SIGHT CONE next to the training patch - an unwanted,
          unfleeable battle;
        * hazard tiles - ledges (one-way, drops you out of the area) and Granite Cave B1F
          cracked floors. Confine the walk to a verified safe tile set, not "anywhere
          walkable".
      !! VERIFY FIRST, DO NOT ASSUME: does turning in place generate encounters at the same
      rate as stepping? If spinning is already step-equivalent, wandering is neutral on
      training speed and purely cosmetic; if stepping is faster, wandering is a genuine
      throughput WIN as well. Check `CheckForWildBattle` / the field state machine in the
      decomp before designing around either answer - this decides whether the feature pays
      for itself or merely looks nicer.
      Design sketch: a seeded bounded random walk over the region's MB_CAVE / tall-grass
      tiles, biased to stay near the centre, with occasional in-place spins and short
      pauses; region supplied by the caller (we already derive safe tile sets - see the
      Granite Cave work in `19-TEAM-BUILDING-DISCUSSION.md` 8.1).
- [ ] #24-items - GROUND + HIDDEN ITEM PICKUP (user request 2026-07-26). The bot walks
      past every item ball and every hidden item in the game. Two mechanisms, handled
      differently:
        (a) VISIBLE ITEM BALLS - real object events at a known tile; pickup is "navigate
            there, press A". The Ch14 recon alone found Carbos (Route121 55,10), Revive
            (60,10), Zinc (38,13), Max Potion (MtPyre Exterior 27,15), TM48 (19,40), Sea
            Incense, Lax Incense, TM30 - all on routes the bot already walks. The Aqua
            hideout holds a MASTER BALL (B1F 15,9) + Nugget, behind a solved warp path.
        (b) HIDDEN ITEMS - no object event; need the ITEMFINDER and a press on the exact
            tile. Requires the Itemfinder in the bag plus a per-map coordinate table from
            the decomp (`hiddenitem` script commands in data/maps/*/scripts.inc).
      !! SYNERGY, and the reason to build this alongside #24-provisions: many ground items
      ARE Potions and Revives, so pickup directly feeds the layer that breaks the
      loss->whiteout 1:1. Do (a) first: navigation + a press, reuses everything that exists.
      !! CORRECTED by later recon (22-CAPABILITY-RECON.md C1): PICKUPS ARE SAFE. Item balls
      (finditem/Std_FindItem) and hidden items both call checkitemspace FIRST; on a full bag
      the ball STAYS with its flag unset, so the pickup is simply retryable. No bag guard is
      needed for pickup logic.
      The strand vector is GIFT scenes only - giveitem/Std_ObtainItem calls additem with NO
      pre-check, sets VAR_RESULT=FALSE and prints nothing, and 38 sites never test it.
      Those are concentrated in KEY ITEMS (cap 30) and TM/HM (cap 64) - including EVERY HM
      (Cut, Flash, Strength, Rock Smash, Surf, Fly, Dive, Waterfall) and the Magma Emblem.
      The general Items pocket has NO unchecked story grant on the path, so stockpiling
      Potions cannot strand a run. Rule: keep KEY ITEMS and TM/HM headroom before gift scenes.
      !! The ITEMFINDER IS NOT REQUIRED to COLLECT a hidden item - only to detect one
      (field_control_avatar.c:346-353 checks the flag alone). The bot can harvest hidden
      items straight from a coordinate table without ever obtaining it.
      On-path healing already mapped: REVIVE at Route117 (9,1) and Route109 (16,23, hidden),
      MAX REVIVE at Petalburg (19,2), Hyper Potions on Route118/119, plus Rare Candies on
      Granite Cave B2F (29,4) and Route110 (26,47).
      Open: detour for items, or only collect what is on the existing path? Recommend
      on-path only first, then let the `curiosity` personality axis price the detour
      (19-TEAM-BUILDING-DISCUSSION.md 5).
- [ ] #24-tms — TM ACQUISITION + USAGE (user directive 2026-07-23): TMs arrive as
      gym rewards (TM39 Roxanne, TM08 Brawly...), ground items, and mart stock;
      the bot should track what's in the bag, know single-use vs HM reuse, and
      teach them via the SAME validated teach flow (teach_hm_move already takes
      any TM item + hm_learner_slot generalizes — the missing piece is the
      DECISION layer: which TM to which mon, driven by the move-priority system
      (#24-movelock v2) and later the per-Pokémon profiles (#24-pokeprofiles)).
- [ ] #24-pokeprofiles — PER-POKÉMON BATTLE PROFILES, deep-research program (user
      directive 2026-07-23): build a detailed profile for EVERY Emerald-obtainable
      species (217 + evolution lines; census in emerald_obtainability.json):
      goal moveset(s) with priority order, how each move is obtained (level-up /
      TM+where / HM / tutor), training plan (when to evolve, what to delay),
      battle role (sweeper/wall/HM mule), and priority tiers so the bot knows
      WHICH mon to invest in. Execution model per the user: OVERNIGHT AUTONOMOUS
      RESEARCH in batches (10-20 species — tune for accuracy over speed), with
      self-generated Gemini assistant prompts BOTH when stuck AND routinely for
      cross-referencing/verification of my own conclusions; results verified
      against modules/data (learnsets/TM-compat are already in the bot) before
      being written. Output doubles as the reference layer for the sibling
      Pokémon Emerald AI project (Pokemon_Emerald_AI_Notes.md). Prereq for the
      full #24-tms decision layer and the "proper battling" endgame; schedule
      after the story skeleton is deeper.
- [ ] #24-economy — CASHFLOW MAINTENANCE (user directive 2026-07-23, extends the
      planning doc's money-reality note): keep a healthy balance for balls +
      potions + TMs across the whole run — trainer payouts (the main income; no
      Vs Seeker in Emerald), Amulet Coin when obtainable, selling vendor trash
      (Nuggets/Pearls/Stardust from Pickup — Zigzagoon/Linoone party slot is a
      passive income engine), and mart budgeting against the reserve. Design
      with #24-provisions; both consult one Resource Ledger (doc 13 spec).
- [ ] #24-trainersweep — EXHAUST UNFOUGHT ROUTE TRAINERS BEFORE GRINDING (from the
      2026-07-23 boss-training discussion + Gemini consult): before any wild-grass
      escalation, sweep the one-time optional trainers reachable at the current
      frontier (Wattson stage: Route 111 south Winstrate family, Route 110 cycling
      road + surface leftovers, Route 117, Trick House puzzle 1-2) — big one-time
      XP+money a faithful player takes first. Needs: per-route trainer tables
      (decomp object events, sight-lines), a "fought yet?" check (trainer flags —
      readable), and routing. Later: PokéNav Match Call REMATCHES (255-step trigger,
      call answering, scaled teams) as the true repeatable mid-game XP engine.
- [ ] #24-gemini-org — "COMPANY-STYLE" GEMINI ORCHESTRATION (user 2026-07-23, timing
      left to the agent → deferred to a quiet/overnight slot): formalize the ad-hoc
      multi-agent consult pattern (design-critique agent + adversarial agent worked
      well for the sufficiency gate) into reusable roles (researcher / critic /
      verifier / synthesizer) with standard prompts, cross-checking rules, and when
      to escalate models (3.1-pro vs flash). Candidate first use: the #24-pokeprofiles
      overnight batches. Refine WITH Gemini agents when picked up.
- [ ] #24-rare-catch — RARITY-TIERED OPPORTUNISTIC CATCHING (user 2026-07-23, future):
      extend the catch branch beyond team-building phases: RARE species (low
      encounter-slot %, version exclusives, one-shot statics) should be caught on
      sight when NOT yet owned, in ANY phase (training, traveling) — party room +
      spare balls permitting, same gating style as the HM-learner hunt. An ULTRA-RARE
      tier (the user's example: a MALE Skitty — a 2%-slot species × 25% male gender
      roll) is attempted on EVERY encounter, shiny-style, even if the species is
      already owned. Needs: a rarity classifier (encounter-table slot % from the ROM
      data × gender-ratio math — all derivable, no hand lists), tier thresholds to
      agree with the user, and integration ordering vs the shiny branch (shiny stays
      first). Pairs with #43 opportunistic catching + the Living-Dex orchestrator.
- [ ] #24-hm-multi — TEACH AN HM TO ADDITIONAL APPLICABLE MONS (user 2026-07-23,
      future): after the primary teach, consider teaching the HM to OTHER party mons
      when it is a genuine upgrade over one of their current moves ("if they are
      present and if it is a higher priority over their current moves" — the user's
      framing). NOTE the research nuance before building: per the graded pokeprofiles
      registry, Rock Smash-class HMs are an HM TAX (weak move, undeletable without
      the Lilycove Move Deleter) — "applicable" must mean "the decision layer says
      it beats a current move" (#24-tms/#24-movelock), not merely "compatible", or
      we poison battlers' movesets. Strength (80BP) is the counter-example where
      multi-teach genuinely pays. Build after the TM decision layer exists.
- [ ] #24-flannery-grind (OBSERVATION, not a bug — 2026-07-23 milestone run): from the
      Lavaridge milestone (weak fixed team L29), Flannery took 3 boss-training whiteouts
      (L29→L32) before the win — grass-less gym + tanky Torkoal + optimistic sufficiency
      gate + team re-solves the trapdoor maze each retry (~22k frames/solve). Working as
      designed (reactive net ground out the win, 0 derails), but slow FROM A WEAK
      milestone team; a real fresh run arrives stronger. If it proves annoying later:
      a stronger prep floor for grass-less tanky-ace gyms, or full-team survivability
      in the sufficiency gate (consult flagged Torkoal's bulk+Sunny Day). Low priority.
- [ ] #24-rivalcap — `_rival_attempts` (story_mode.py §5c) increments on every _play
  re-entry, not on actual lost rival battles — a derail-y stretch near the rival can
  burn the 3-attempt budget without fighting once (seen on the goods_recovered thin-team
  save 2026-07-24). Key the counter on a genuine battle loss.
- [ ] #24-watertrain — WATER training tiles (user 2026-07-24): once Surf is obtained AND
      taught, surf encounters become a viable training band (level + typing permitting).
      Extend training_areas with water tiles + a "needs surf" prereq (the AREA_PREREQ
      mechanism already exists) and teach the picker to consider them.
- [ ] #24-healverify — re-verify the Surf-gated heal-centre pairings (Routes 115/118/119/121)
      from a POST-Surf checkpoint; repro_fodder_grass.py currently marks them PENDING because
      no pre-Surf save can path a water route. Route 119 (21,109) reached NO Poké Center.

## Done
- [x] **#24-movelearn-recovery — DONE 2026-07-25. The #1 open item; killed 2 of 5
      cold-start runs (~f1.55M each).** ‼ The filed diagnosis ("the recovery scope is
      the bug, not the move-learn logic") was only the LAST of four links — fixing just
      it would have produced a dead run with a nicer log line. Real chain, from the
      captures `saves/movelearn_hmwedge_{quickattack,slash}.ss1`: Combusken carries
      Rock Smash (an HM **and** its weakest move); a stray A from the "unrecognised
      text" branch answered YES to a prompt the bot had decided to DECLINE; a cursor
      read while the summary screen was still animating in was stale, so A landed on the
      HM slot; the game replied with `Task_HandleInputCantForgetHMsMoves`, **a symbol
      nothing in the codebase referenced**, misreported as the Yes/No; and the handler
      then sat in an UNBOUNDED "screen still opening" branch pressing **nothing for
      6,000 frames**. Fixed: `LearnMoveState.CantForgetHM` checked first; a branch that
      dismisses the refusal AND strikes the refused slot off; no A on an untrusted
      cursor; the wait bounded; and `modules/battle_fault.py` — an OPT-IN channel
      (`handles_battle_faults`) that carries a battle fault to the mode instead of
      raising across the controller stack, so it costs one DERAIL. A/B: WEDGED at
      f23,400 → RESOLVED at f258 / f224, movesets correctly unchanged; stock modes
      verified unchanged. Repros: `repro_movelearn_hm_wedge.py`,
      `repro_movelearn_fault_recovery.py` (3 arms).
- [x] **#24-fortreebadge — SATISFIED 2026-07-25: BADGE 6 WON from a cold start.** Filed
      2026-07-24 when the isolated Fortree drive lost to Winona and whited out — it called
      `do_fortree_gym()` directly with whatever party the save carried, and battle prep
      (lead selection + heal) is the CALLER's job. Confirmed the right way, by a full
      run rather than a gate fix: a fresh title-screen run reached the **Feather Badge =
      end of built content** (38 maps, ~2.48M frames, 0 derails).
- [x] **#24-fortreegates — DONE 2026-07-24: the Fortree Gym rotating-gate puzzle is
      solved LIVE.** `modules/story/fortree_gates.py` is a port of the decomp's
      `src/rotating_gate.c`, validated **4/4** against the emulator. Includes the
      parked-trainer escape: a trainer standing on the path is cleared by RESETTING the
      room (exit + re-enter forces the documented gate reset), not by waiting.
- [x] **#24-harness-savepath — DONE 2026-07-25: stall snapshots are per-run AND
      per-stall.** Two defects in one line. (a) The no-progress auto-save wrote a single
      shared `saves/midstuck.ss1`, so concurrent runs overwrote each other and the
      artifact belonged to no particular failure — that is precisely why the move-learn
      stall had no clean repro, and why one earlier investigation burned effort on a
      `midstuck.ss1` that was a whiteout state from a different map. (b) It fired ONCE
      per run, but a run usually stalls several times and the first stall is typically a
      recoverable hiccup — the interesting capture was the one never taken. Snapshots now
      land in `tools/story-dev/saves/stalls/`, which unblocked `#24-movelearn-recovery`.
- [x] **#24-harness-finish — DONE 2026-07-25: a SUCCESSFUL run no longer reports as a
      hang.** The first cold-start Badge 6 run reached the end of built content at
      f2,483,319, printed "end of built content — handing to manual", and then correctly
      stopped doing anything — so the harness's frame-based no-progress detector fired
      20,000 frames later and the log ended `HANG CONFIRMED`. `compare_runs.py` inherited
      the false signal and classified it `no-path` (a transient, recovered "Could not find
      a path" earlier in the log). The one run that worked looked like the worst kind of
      failure. Both tools now check the bot's own end-of-content message before calling a
      stop a hang.
- [x] #1 â€” Vendor upstream 40Cakes/pokebot-gen3 (subtree @ 5dd898f8) (2026-07-17).
- [x] #2 â€” Deep documentation pass + Pokemon_Emerald_AI_Notes.md (2026-07-17).
- [x] #4 â€” install.py V2 (setup/update/heal + ROM handling) â€” "worked!" (2026-07-18).
- [x] #5 â€” Native dashboard GUI + handheld mode â€” "worked!" (2026-07-18).
- [~] #24-textread â€” DIALOGUE AWARENESS: read on-screen text to drive interactions
      (user 2026-07-20; design Â§DA). FEASIBILITY CONFIRMED (decode_string of
      gDisplayedStringBattle / gStringVar4 reads exact text). STARTED: move-learn
      now uses text-driven detection (both builds) â€” UNIVERSAL (matches generic
      phrases + reads the offered move dynamically, not hardcoded to any move).
      â˜… ROOT CAUSE of the Lv16 hang FOUND & FIXED (ML-13): the Emerald battle Yes/No
      has no task and was detected only by a fragile script-offset; when it stayed
      `Unknown` the old code pressed nothing (is_waiting_for_input gate) â†’ froze.
      `handle_move_replacement_dialogue` rewritten fully text/task-driven;
      `handle_evolution_scene` hand-off hardened. PROVEN by fault-injection A/B on
      both builds (old stalls ~10.6k frames & fails to learn; fix resolves in 394 &
      learns Pursuit + evolves). Faithful repro harness: scratchpad/repro_movelearn.py.
      Still want the user's real-32Ã— confirmation. FULL SYSTEM (next big build):
      Reader (normalized current text + menu/cursor) -> Classifier (text -> interaction
      type) -> Responder (type + story progress + config -> answer; multi-valid
      decisions like fossil/starter = random). Gather conversation dumps {exact text,
      speaker, valid answers, how to answer} from runtime logging + pokeemerald script
      data; build a response table. Subsumes fragile scripted-scene ride-outs; robust
      + deterministic vs flaky task-state. Backstops: no-progress watchdog + advance-
      plain-text-with-A so nothing hard-freezes.

- [x] #24-evo-trainstall (FIXED 2026-07-22: interrupt-safe _rotate_lead_safely + _yield_bounded; proven on evostall.ss1; same fix covers the user's 110k-frame Joey stall) â€” `train_team`/`_story_spin` can hang right AFTER a
      trainee EVOLVES mid-training (batch run02 2026-07-22: Grovyle evolved +
      learned Fury Cutter on Route 116, then the spin never resumed â†’ 20k-frame
      HANG). Repro save: tools/story-dev/saves/evostall.ss1. Likely the
      post-evolution return-to-overworld transition isn''t ridden out before the
      next spin action (cf. the move-learn / dock-arrival family). Prove + fix.
- [x] #24-pokenav-faithful — ‼ SUPERSEDED: recurred 2026-07-26, see the OPEN entry above. (RESOLVED 2026-07-22: the user ran VIDEO OFF — the renderer-gated fallback fired exactly as designed; keep video off on the weaker test PC, the fallback covers it) — WATCH ITEM (user fresh-run log 2026-07-22 13:24): the
      PokéNav Match-Call tutorial took the STATE-WRITE FALLBACK on a real-GUI run
      (video on) — the faithful play-through previously worked on this hardware.
      By design the fallback is legal (never hang), but check why the faithful
      path didn''t engage (timing? renderer-gate read?) next time it recurs.
- [x] #24-wattson-strength — DONE 2026-07-22 (KI-13 resolved): 0-power move-learn
      guard + Segment 9c prep (Route 117 (31,16) band 20-24) + aftermath-quiet
      riding → run 14 beat Wattson end-to-end; `wattson_done.ss1` verified.
      Residual (folded into #24-movelock): audit the evolution-scene learn flow
      that dropped Marshtomp''s Mud Shot at L16 (moot for Wattson, still a
      move-quality gap).


- [x] #24-hm-learner — HM TEACH VALIDATION + LEARNER ACQUISITION (user report
      2026-07-23, DONE same day): Segment 10b used to teach the HIGHEST-LEVEL mon,
      which loops in the party menu (NOT ABLE) whenever that mon can't learn the
      HM. Now: `hm_learner_slot(item)` picks the best COMPATIBLE party mon;
      `ensure_hm_learner(item)` hunts + catches an accessible learner species when
      the party has none (grounds derived live from ROM encounter tables ×
      TM/HM learnsets — nothing hardcoded, works for every future HM);
      `teach_hm_move` hard-fails truthfully on an incompatible target. A/B-proven
      (repro_hm_learner.py + the hmtest harness driver: fault-injected
      "nobody compatible" → hunted Route 117 → caught Poochyena → taught it).
      Feeds directly into #24-hm-slaves (the acquisition half now exists).

### #24-endlessruns — ENDLESS DEBUG-RESET RUNS (user request, 2026-07-25)

**CLI form: DONE** — `tools/story-dev/endless_runs.py`, smoke-tested.
```
py -3.12 tools/story-dev/endless_runs.py                 # 10 runs, treecko
py -3.12 tools/story-dev/endless_runs.py --count 0       # INFINITE (Ctrl-C)
py -3.12 tools/story-dev/endless_runs.py --count 25 --starters all
```
Back-to-back FRESH runs, unthrottled, debug logging on, appending one row per run to
`tools/story-dev/endless-runs/LEDGER.md` (depth reached · outcome · frames · wall-clock · log).

**Failsafes — each exists because of a failure actually observed 2026-07-24/25:**
* `--run-timeout` (wall clock, default 5400s): the harness's watchdogs are FRAME-based, so a
  wedged emulator process advances no counter and fires nothing. Only an external wall-clock
  bound catches that.
* `--stall-timeout` (default 600s): kills a run whose LOG STOPS GROWING. A run can burn frames
  forever while making zero progress — the 2,000,000-frame fodder grind looked alive throughout.
* **A fresh profile per run, metadata COPIED from a template.** "FRESH boot from title" still
  loads the profile's battery save, which once produced three worthless runs that reported as
  fresh while starting in Fortree with a L39 party. ‼ metadata.yml must be COPIED, not
  synthesised — it carries the ROM reference, and a hand-written one makes every run die
  instantly with "Could not find ROM ``".
* **One bad run never aborts the batch** — every outcome is recorded and the loop continues.
* **Zero frames is never reported as success.** The first cut scraped a 5-second ROM-not-found
  death as `clean-finish`; an overnight batch of those would have read as green.

**`#24-endlessruns-gui` — DONE 2026-07-25, and it shipped as something better than the plan
above.** The plan was a menu item that shells out to this CLI module. That was built first and
FAILED in the user's hands: the dialogs appeared and nothing happened, because "endless debug
reset runs" means *this emulator*, not a separate headless harness.

So it shipped instead as **a real in-process bot mode: `Story (ENDLESS RESET)`**
(`StoryEndlessResetMode`, `plugins/custom_modes/story_mode.py`) — it simply loops
`Story (DEBUG - RESET)`'s `run()`, so every iteration is a hard reset → forced NEW GAME → play,
back to back in the running emulator. In BOTH builds. Count comes from the GUI's
"Endless Debug-Reset Runs…" item (`ENDLESS_RESET_TARGET`, default 10, `0` = forever).

In-process failsafes beyond the CLI's: a `BotModeError` in run 3 is SWALLOWED so runs 4..N still
happen; a hard 3.5M-frame-per-run cap (StoryMode's own watchdog can't catch a wedged watchdog);
the bot mode is re-asserted after every run because a derail can call `set_manual_mode()`; and
the batch's emulation speed + video settings are captured once and restored each run — the first
cut restored `bot_mode` but not the speed, so run 1 ran unthrottled and every run after it
crawled at 1× (user-reported, fixed in `aadad944`).

The CLI form above is NOT superseded — it keeps the fresh-profile-per-run and wall-clock/log-growth
failsafes that an in-process mode cannot have, and remains the right tool for a scripted batch.
