# Chapters 6-7 (the sail to DEWFORD through BRAWLY): build report, 2026-11-05 to 07

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). It collects the workflows' own reports for chapters 6-7 on
> branch `wip/ch6-ch7` (worktree `wf_e7452923-f06-3`), in order: the wiring (base `979754bf`, commit `4b84131a`) and its
> adversarial check of the cloud draft, KI-134's verification (`43485a36`), then the chapter 6 stop rounds 1-9 with one
> independent verifier each (commits `2bce9c0c`, `66acbd1c`, `07913cde`, `bbb68eb9`, `c41db547`, `095ea511`,
> `adf6c246`, `986a5816`, `059a65ff` and round 9's; round 8's verifier read FAIL and round 9 fixed its MAJOR). Every live claim is development (one trajectory per seed, never a rate); the ledger ids
> on this branch from #96 overlap `main`'s #96-#101 and are renumbered at the merge. This copy came to `main` with the chapter 6-7 merge (its docs pass is dated 2026-11-14, and `07` records the merge with the full lane's line); the ledger ids it cites from #96 on are the ids the branches wrote, and the table below gives each one's id on `main` (every renumbered entry keeps its branch id in `was`). The cloud draft that the wiring checked is appendix A.
> After round 9 come probe 11, round 10, and boss preparation BP-1 on side branch `wip/ch6-bp1`: round 1 (verifier
> FAIL), round 2 (2026-11-11, verifier CONDITIONAL PASS with two MAJOR trainee-safety findings, V2-M1 and V2-M2) and
> round 3 (2026-11-11, verifier CONDITIONAL PASS: V2-M1 and V2-M2 closed on six development runs; two new MAJORs, V3-M1
> a heal loop when the partner fails its line at full HP, and V3-M2 the guard's fallback sending a member that cannot
> win). Round 4 (2026-11-12, verifier CONDITIONAL PASS): V3-M1 and V3-M2 closed; 0 trainee faints outside BRAWLY's fight
> in 9 of 9 development runs (the builder's 6 and the verifier's 3) and no heal loop; BADGE02 in 4 of the builder's 6
> (Wurmple plan 3 of 3, Grovyle plan 1 of 3: prediction P-G6 MISSED, against round 3's 6 of 6 on other seeds), diagnosed
> as the seeds: on three new Grovyle-plan seeds the verifier's paired A/B gave round 4 3 of 3 and round 3 1 of 3. One
> MAJOR, V4-M1 (the builder's headline did not carry the miss; the lead reworded it in this copy). Open design
> questions: the raise's budget ends below the key move's level, a lost boss fight changes nothing before the next try,
> the heal before a boss ignores PP, and a trainee between its floor and a safe win is never rested (V4-m3).
> Round 4's closing pass (2026-11-12, offline only, verifier CONDITIONAL PASS with no MAJOR): no play code changed
> (play digest still 840ece09384cb6b8); four round-4 rules that had no test now have one (V4-m4), and the full mutant
> run on the closing tree read 161 CAUGHT and 2 REDUNDANT of 163; the verifier's paired A/B and four corrections are
> branch evidence, and the P-G6 diagnosis is filed as a note. Two MINORs are carried to the next round: VC-m1 (the cap
> test's control does not pin the at-cap boundary) and VC-m2 (the last resort's run bound can bind in play, which
> leaves a design question).
> P11-1 (2026-11-11, side branch `wip/ch6-p11` from `18c3d51b`, built beside BP-1 round 3): the way through
> GRANITE CAVE's dark floors from static map knowledge (`knowledge/world/ways.json`); verifier CONDITIONAL PASS with one
> MAJOR, V1 (the extractor ignores the one-way muddy slope, so one way in `ways.json` is unreachable on foot).
> P11-2 (2026-11-12, verifier CONDITIONAL PASS): the muddy slope modelled and V1 to V6 closed; the shipped file went
> from 7 maps to 2 (GRANITE CAVE B1F and B2F; VICTORY ROAD and the unused CAVE OF ORIGIN maps are left out until an
> HM-aware walk); `f1069d9d` and the new play code made identical decision streams on 3 seeds (one trajectory per seed,
> replayed, not a rate); the detour after the crossing is diagnosed as a test-start artifact (the B1F starts carry no
> goal memory), so P11-1's "FIX reached STEVEN sooner in only 3 of 6" does not measure the AI. One MAJOR, VV1
> (`maps[].id` is still a subtree leaf in `check_fairness`, so a developer key nested inside it passes RULE B).
> P11-2's closing pass (2026-11-12, offline only, verifier PASS with no MAJOR or MINOR): VV1 to VV4 closed (no entry
> of `ways.json`'s fairness block is a subtree now; 1,069 plants, 0 holes). No play code changed, but the play digest
> moved from 87d5b014f8189cfe to 1c96c11fbbf253f7, because `ways.json`'s developer-only `_check` block changed shape
> (the rest parses equal, and the loader never reads `_check`). Mutants: 61 CAUGHT and 3 REDUNDANT of 64. The extractor
> still neither models nor refuses five things; none changes today's two maps, and each must be handled before any
> VICTORY ROAD way ships. The branch's 24 chapter packs were regenerated in the same commit.

### The ledger ids at the merge (`id_table.py`)

| branch | ids on the branch | ids on main | shift |
|---|---|---|---|
| `wip/ch6-ch7` | #96-#111 | #102-#117 | +6 |
| `wip/ch6-bp1` | #112-#131 | #118-#137 | +6 |
| `wip/ch6-p11` | #112-#120 | #138-#146 | +26 |

## Chapters 6-7 builder report (worktree wf_e7452923-f06-3, base 979754bf, nothing committed)

**Headline (with its caveat):** chapters 6 and 7 (8 milestones, 36 in all) are wired, verified and gate-green, but the first development probe reached **0 of 3** cottages: all three runs stopped at the FIRST new milestone, `ch6_briney_house`, because of the route planner (KI-134), so the sail, Steven and Brawly are **untested live**. The probe prediction (cottage found in 2 of 3) was wrong.

### What was wired (all eight were confirmed by the names check, or fixed and re-confirmed here)
- `ch6_briney_house`, `ch6_dewford`, `ch6_old_rod` (opt), `ch7_steven`, `ch7_flash` (opt), `ch7_gym_trainers` (opt), `ch7_brawly`, `ch7_exp_share` (opt), AUTHORED into `extract_milestones.py` (never copied), plus 7 trainers (TAKAO, JOCELYN, LAURA, BRENDEN, CRISTIAN, LILITH, BRAWLY_1) and 5 looks (mr_briney, old_rod_fisherman, steven, brawly, mr_stone). Fixes to the draft: looks in the repo schema (`decomp`); the gym trainers' `decomp` script; `map: None` on the 'cottage' and 'STEVEN in DEWFORD' hints; `taught_by`; GRANITE_CAVE_B2F and PETALBURG_WOODS in `maps`; the notes corrected (Dewford Pokemon Centre 'stone cavern' pointer, the early landing proof, the dark floors walkable unlit, the Briney cottage reachable only via the woods).
- **`ch7_steven` is ONE talk step** (names check F1, MAJOR): the draft's four steps make the real `story_step` answer 'go DEWFORD_TOWN' on ROUTE 106 and on B1F/B2F. `Chapter67Tests` runs the real `story_step` on both shapes (FAULT = the draft regresses, CONTROL = the one step never does); mutant G474 restores the draft. `ch6_dewford` is one talk step too (its second step was dead code). No `told` on STEVEN's step: it explores until it has been to the room's map (a probe question, now unanswered).
- `eyes/view.py` +15 flags; `campaign_skeleton.json` 3 ids -> 8; `campaign.json` and `bosses.json` regenerated (76 entries, `verify_world` 0 mismatches), 48 chapter packs regenerated; docstrings and README (a Chapters 6-7 section). Chapters 1-5: the digests of `milestones[:28]`, the 13 looks by name, first 21 trainers, gendered maps and provenance are equal on the committed file and the new one; `trainers.json`/`maps.json` unchanged.
- New: env `POKEBOT_DECOMP` makes `extract_milestones.py --verify` read the pinned clone (prints its HEAD); both `gh api` and pinned runs PASS; `--plant` 8 -> 14.

### Gates (see `tests`)
test_goals 341 OK, test_kb2 124, test_host 37, test_saving 151, test_eyes 66, selftest_chapter_pack 137/137, fairness 0 breaches, purity PASS, ledger PASS, full regression lane PASS (34 suites, 5751.2 s), mutants G470-G475 CAUGHT as predicted. `run_gates --quick` 140/143: the 3 FAILs were the R8 byte ceilings (since raised with recorded reasons; lint_docs now ALL PASS) and `probe_fly_disjunct` (git-ignored `repro-fresh` profile, absent in a worktree; re-run on main). **Tier 1 reviewer not run** (no agent tool): the orchestrator must run it (P1-P5) before committing.

### The probe (ledger #96, seeds 6301-6303, DEVELOPMENT)
Starts: probe-C1/C2/C3 (Story/Catcher/Trainer) end states + world.jsonl, target `ch7_brawly`, 1.2 M frames. Purity CLEAN 3/3. None set MR_BRINEY_SAILING_INTRO; exits 'no progress for 120,025 / 120,342 / 127,264 frames'. The measured stop: in the woods at (14,5) the planner says 'toward the goal (2 link(s) known)' and exits back UP to ROUTE 104; on the north strip it says 'back to PETALBURG_WOODS'; the goal ends 'stuck: ping-pong' 18/45/49 times (Trainer run: 172 crossings). Reading (not A/B-proven): `route_to` is map-level, ROUTE 104 is one node with two parts, and the cottage is in the south part reachable only through the woods' south doors. Filed as KI-134 with a fix direction; recorded in 06, 07, 08.

### Docs written
04 (resume point, queue item 4, cloud note, banner), 05 (KI-134, KI-130 update), 06, 07, 08 appended, rulings overlay and index regenerated, ceilings raised for 04 and 05. 01/02/03 not edited (no sentence there stated the chapter state).

### Cautions for the orchestrator
- Graded registrations hash `milestones.json`: do not edit it between registering and running the graded ch5 batch (schema check F11). `live_chain.py` still needs `FRAMES_BY_CHAPTER[6]/[7]`, `PROOF_NOTES`, fresh seeds, and test_live_chain edits (the fake `ch6_x` chapter) in its own later registration.
- Merge conflicts to expect in 04-HANDOFF.md, 05-KNOWN-ISSUES.md, 06/07/08 (appends) and `doc_size_ceilings.json`, `ledger.json`, `rulings-overlay.json`.
- The lane's evidence files carry this uncommitted tree's identity; docs/ceiling edits after the lane were outside the covered scope but re-check `regression_due` after the commit.
- Scratch: all scripts and outputs are under `scratchpad/s53/ch6/`; the kept C1 `world.jsonl` (224 MB) is in `out/probe6/probe6-C1/`. The stage copy is deleted; the mgba junction and the fixture-profile copy were removed from the worktree.

## Adversarial check of the cloud draft, chapters 6 and 7 (read only)

Base: main at c0d14b95. Decomp: `C:/Remote Projects/_decomp/pokeemerald` at 731ad5bf (`git rev-parse HEAD` printed that SHA, the same one the cloud used). Draft read with `git show origin/claude/milestones-ch5-ch8-o0janq:...` into the scratchpad. Scripts and outputs: `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/ch6/` (`check_names.py`, `check_text.py`, `flood.py`, `flood2.py`, `probe_steps.py`, `probe_variants.py`, `hexlist.py`). Nothing in the repo was changed (`git status --short` empty after the probes, run with PYTHONDONTWRITEBYTECODE=1).

### Verdict in one paragraph
Seven of the eight milestones survive every attempt to refute them. **One does not: `ch7_steven` (GRANITE CAVE, the letter, the POKeNAV registration).** Its names and proofs are right, but its step list makes the AI walk back out of the cave: I called the real `GoalManager.story_step` on the draft merged into main's milestones and it returned `go DEWFORD_TOWN` on ROUTE106, GRANITE_CAVE_B1F and GRANITE_CAVE_B2F. The cave route also needs B2F, which the draft leaves out. Everything else is MINOR or NIT.

### Names, numbers, setters (all 15 flags, 7 trainers)
- `check_names.py` evaluated every flag from the pinned `include/constants/flags.h` (SYSTEM_FLAGS and TRAINER_FLAGS_START expressions included) and compared with the draft and with the bot table `sandbox-pokebot/modules/data/event_flags/emerald.txt`: **15 of 15 equal, 0 mismatches** (147, 2161, 257, 189, 305, 109, 1265, 2152, 272, and the six gym trainers 1459, 1705, 1706, 1852, 1854, 1853).
- Census of every line in 1,542 decomp files (`data`, `src`; .inc/.c/.h/.json) that mentions each flag: each proof flag has exactly ONE setter, in the script the draft names (MR_BRINEY_SAILING_INTRO Route104_MrBrineysHouse:32; VISITED_DEWFORD_TOWN DewfordTown:6; RECEIVED_OLD_ROD DewfordTown:84; DELIVERED_STEVEN_LETTER StevensRoom:10; REGISTERED_STEVEN_POKENAV StevensRoom:22; RECEIVED_HM_FLASH GraniteCave_1F:10; DEFEATED_DEWFORD_GYM and BADGE02_GET DewfordTown_Gym:150-151; RECEIVED_EXP_SHARE DevonCorp_3F:162). The other hits are readers (`goto_if_set`, match-call tables, region_map.c). So none fires earlier or elsewhere.
- `tools/story-dev/audit_flag_names.py` printed "all names valid" (36 files, 339 names, exit 0), but it scans only the bot's story modules, not the draft, so on its own it proves nothing about these names. The equivalent check for the draft is the 15-of-15 comparison above.
- Trainers: opponents.h ids TAKAO 179, JOCELYN 425, LAURA 426, BRENDEN 572, LILITH 573, CRISTIAN 574, BRAWLY_1 266; flag = 0x500 + id gives the draft's numbers. trainers.h classes and parties match (all six one Pokemon, Lv 13: MACHOP, MEDITITE, MEDITITE, MACHOP, MEDITITE, MAKUHITA). BRAWLY_1: MACHOP 16, MEDITITE 16, MAKUHITA 19 (Sitrus Berry). Dewford Gym map.json has exactly six TRAINER_TYPE_NORMAL objects whose scripts call these six constants, and `CountTrainersDefeated` counts exactly them.
- Hint quotes are verbatim .string labels and every `words`/`told` occurs in them (`check_text.py`). Looks: EXPERT_M 21, GENTLEMAN 48, FISHERMAN 50, BRAWLY 126, STEVEN 134 equal event_objects.h and each is unique on its map (the 3F has two GENTLEMAN objects with the same script, which is fine).

### Order and gating, from the scripts
- MR. BRINEY's cottage: his objects are hidden at New Game (new_game.inc:132-134), re-hidden at the theft (RustboroCity:294-295) and only unhidden at DevonCorp_3F:63-64 (Mr. Stone's scene, reached by the warp straight after the goods are returned, RustboroCity:561-570). So he cannot sail before the DEVON GOODS are returned, and nothing else gates the sail.
- FLAG_MR_BRINEY_SAILING_INTRO is set (line 32) BEFORE the yes/no (line 34); NO leads to a decline and the next talk is a yes/no again. `call_if_unset` ends in `goto`, so it never falls through. The draft's reading is right: the flag proves "talked", not "sailed".
- Sail: always to DEWFORD first. Route 104 -> 105 -> 106 -> Dewford are connected maps, so `DewfordTown_OnTransition` runs when the camera crosses (fieldmap.c:623, overworld.c:807): VISITED_DEWFORD_TOWN is real, but early (mid-cutscene), F5.
- DEWFORD to SLATEPORT needs DELIVERED_STEVEN_LETTER (DewfordTown:12), as the draft says; going back to Petalburg works without it. EXP. SHARE and the Match Call line also need the letter.
- Gym: nothing gates the door (8,17) or BRAWLY (no flag test in DewfordTown_Gym; one flood-fill component). Gym trainers, FLASH, OLD ROD can be done in any order; BRAWLY can come before STEVEN (then `current()` stays on ch7_steven, which is fine). FLASH outside battle needs BADGE02 (party_menu.c:121).
- Steven's room is never hidden (FLAG_HIDE_GRANITE_CAVE_STEVEN is only named in map.json) and his script has no guard; harmless for a flag proof.

### The cave, measured (flood fill on the pinned layouts)
1F has three components: the Route 106 door, the HIKER and the warp (17,11) are together; Steven's door (5,10) and the warp (35,3) are in another. B1F comp 1 holds (4,21) and (28,21); comp 3 holds (25,13) and (29,13); B2F comp 5 holds (28,21) and (29,13). Therefore the only no-HM route is 1F -> B1F -> B2F -> B1F -> 1F -> room. B1F/B2F are dark but walkable. The cave mouth is reachable on foot from Dewford (`flood2.py`). The draft says only "1F's warps to B1F lead to it".

### What I could not check offline
Whether the AI's blind exploration finds the cave door and crosses the unlit loop, whether the first sail's Dad call is pressed through, and whether the dark gym is crossed. These need an emulator probe, not a read.

### Confirmed (tried to refute, could not)
ch6_briney_house, ch6_dewford, ch6_old_rod, ch7_flash, ch7_gym_trainers, ch7_brawly, ch7_exp_share: names, numbers, single setter, hint text, told words, trainers, looks, order. ch7_steven: names, numbers, setters, hint and order confirmed; steps and maps refuted (F1, F2).

## KI-134 verification (the verifier, 2026-11-05)

**Verdict: CONDITIONAL PASS.** The fix is correct and its claims hold. Four MINOR and five NIT findings, no MAJOR. Conditions before merge: add a test that kills mutant V10 (K134-V2), and reconcile the ping-pong numbers (K134-V5). K134-V1 (the cross-map wall flip-flop) should be fixed or filed as a known issue.

**Method.** I worked on `git archive 43485a36`, extracted to `s53/ki134/verify/repo` (read-only git; I never touched the worktree's working tree). All my scripts and outputs are in `s53/ki134/verify/`. I made no commits and staged nothing.

**What the B arm actually ran.** The mutant harness kept two tree snapshots, at 18:49 and 19:25. Comparing them, the B arm's `explore.py` equals the commit's except for one docstring line. `navigator.py` differs only by the `in_map_walls` export.

### (1) Correctness

- **Route 104 really is two parts (decomp check).** A flood fill of the decomp layout from the north strip (19,1) reaches neither the cottage's stand tile (17,51) nor the woods' south-door stand tiles. From (17,51), the north strip is not reached.
- **The woods is one part.** Its cut trees (19,10)-(19,11) shut off only an item pocket. ROUTE 104's cut tree (35,22) does the same.
- **Connection offsets and signs are right on real crossings.** Every recorded crossing in the three chapter-5 memories was predicted from the other records:
  - forward: 838 predictions, all exact;
  - from the far side (sign -1): 934 predictions, all exact, including non-zero x and y offsets (PETALBURG<->ROUTE 104 is (40,50)/(-40,-50));
  - `landings()` contains the real arrival for 159 of 159 crossings.
- **No loops, no climbing.** There are finitely many (map, entry) nodes, each queued once. Ledges are refused by `step_from`, which is the same rule the walker uses.
- **Every caller is covered.** The only caller of `route_to` is `candidates`. The other unchanged goal-driven paths (travel, carry_on, choose_target, lost_way) all reach it through `candidates`.
- **Found: the walls apply only to the source map (K134-V1).** I demonstrated a deterministic flip-flop on test_w1's own fixture.
- **Found: `world_distance` ranking still treats a map as one place (K134-V3).** From the north strip, the nearest-centre pick is Petalburg's, 4 links away, instead of Rustboro's, 2 links away.
- **No route a person could walk was refused.** In the real chapter-5 memories, starting from every part the AI ever stood in, there were 0 refusals (the result of (6) below).

### (2) The claims, re-derived from the raw files

- **Cottage entries (action digests).** Entries were 50, 3 and 3. Each run's FIRST entry came after RUSTBORO -> ROUTE 104 north strip -> the woods' north door -> the woods' south door (16,38) -> ROUTE 104 (10,38) -> cottage (17,50). My first-record frames are f752421, f639573 and f822858; the builder's are 22 frames later each.
- **Ping-pong goal ends.** B arm 0/0/0, A arm 31/56/58.
- **Live decision.** In B C1 at f759549, from the woods the route target was the south door (16,37).
- **Flags (truth harness on each end state).** MR_BRINEY_SAILING_INTRO went 0 -> 1 in C2 and C3 and stayed 0 in C1. The A arm is 0/0/0 and the starts are 0. VISITED_DEWFORD_TOWN is 0 everywhere. Each end-state frame equals the start frame plus the real frames, and its md5 differs from the start's.
- **Purity.** CLEAN in 3 of 3 runs, with 0 bot calls and 0 writes.
- **The offline repro reproduces exactly** on the archive copy.
- **Conclusion.** "3 of 3 entered the cottage by the woods' south door" holds, and so does "2 of 3 set the sail-intro flag". The caveats on the wording are K134-V5, K134-V6 and K134-V7.

### (3) Fairness

`route_to` reads only the AI's own seen memory:
- tiles from its looks;
- links learned at transitions;
- edges learned at crossings;
- bumps;
- what is on screen now (objects and scene walls).

check_fairness PASS (0 breaches), check_purity PASS.

### (4) Mutants

I wrote 12 mutants, recorded their predictions before running them (sha256 9de63575...), and ran them through revert_step5's own runner. All 12 predictions held:
- **Caught:** V1, V8, V9.
- **Survived:** V2, V4, V5, V6, V7, V10, V11, V13, V16.
- **The survivor that matters is V10.** It brings KI-134 back for a goal that is the connected map itself, and no test notices (K134-V2).
- **Other survivors:** see K134-V4.
- **Runner checks:** the builder's G485 was CAUGHT again on the copy, and G0 passed.

### (5) Cost

Measured on the B arm's 48-map end memory, per call: median 40 ms, p99 109 ms, max 147 ms. That is acceptable at roughly 550-800 decisions per run, but it grows with the number of maps and parts known (K134-V9).

### (6) Chapters 1-5

**The sweep.** On each of the three chapter-5 chain-end memories, I compared the search by maps against the region search from every part the AI stood in (one start per strongly connected component of the navigator's own step graph) to every known map. That is 5,801 (part, goal) pairs:
- 2,988 routes are identical;
- 2,813 differ, and every one of them goes through ROUTE 104, the woods, or a real 36-tile corridor in RUSTBORO's south-east that leads only down into ROUTE 104 (checked against the decomp);
- 0 routes that pass only through one-part maps differ, so test_c1's claim of route-for-route equality holds on these real memories;
- in all 2,813 differing cases the OLD route cannot be walked in the region model, and the NEW one can.

That walkability check reuses the model under test. It is anchored by the decomp ground truth for ROUTE 104 and for the RUSTBORO corridor.

**Effect on the story.** Chapter 1-5 routing changes only for walks through ROUTE 104 and the woods once both woods doors are known. In story order this hardly happens: chapter 3's first walk knows no route, and chapters 4-5 stay north. The visible exception is healing or shopping from the north strip, which now walks through the woods to Petalburg (K134-V3).

**Other gates on the copy.** test_goals 353 OK, test_world OK, test_live_ki128 OK, check_paths PASS, ledger --check PASS. I did not re-run call_census (it needs git HEAD) or test_kb2.

### Cleanup

- **Staging.** My truth-harness stage (`verify/tstage`) was removed with its junctions unlinked first.
- **Main sandbox unchanged.** Its linked folders' file counts are the same before and after (modules 4461, plugins 43, mgba 44, roms 2), and no file in its modules folder is newer than the stage.
- **No world.jsonl copied.** I read world.jsonl files where they were; nothing new under 300 MB is kept by me.
- **Temporary mutant copies.** My own copies were removed by the runner. Six `ai_player_step5_mutant_*` folders created at 20:39 are another process's (a run still in progress), not mine, and I left them alone.

### Files

All under `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/ki134/verify/`:
- flipflop.py
- survivor_effects.py
- rank_check.py
- run_mutants.py, mutants_verifier.out
- verifier_mutant_predictions.txt
- sweep_ch15.py, sweep_validate.py, sweep_C1.json, sweep_C2.json, sweep_C3.json
- landing_check.py
- arm_facts.py
- truth_states.py, truth_stage.py
- cost_probe2.py
- decomp_parts.py
- patch_compare.py
- repro_verifier.out

## Chapter 6 stops and the KI-134 follow-ups (the builder, 2026-11-06)

A second builder finished this round. The first builder was cut off by a usage limit after it had:
- built both chapter-6 fixes;
- run both live A/Bs (#99, #100);
- launched probe7 (#101).

The lead committed that work as 2bce9c0c. Everything below is uncommitted in worktree wf_e7452923-f06-3. Nothing is staged.

### What was recovered from the cut-off
- **Probe7, C1 (seed 6314):** interrupted when its orchestrator died. It had played 647,844 frames (last record f1394241, GRANITE CAVE B1F) and left no end state.
  - From the game itself: its last in-game save (21:33:59, play time 5:44:44) holds MR_BRINEY_SAILING_INTRO, VISITED_DEWFORD_TOWN and DELIVERED_STEVEN_LETTER, and no badge 2.
- **Probe7, C2 and C3:** ended by themselves. Each said YES to MR. BRINEY's "sail back to PETALBURG?" and ended "stuck: no progress" on the mainland.
- **Ledger #101:** finished truthfully: 2 of 3 ended, C1 interrupted. The seeds stay spent and were not re-run.

### The two stops (the first builder's fixes, unchanged)
- **MR. BRINEY walks round his table.** The talk skill now watches his way, waits beside it, and speaks when he steps in front.
  - #100: the B arm's first talk landed in both seeds.
  - The A arm was slower, not stuck: it talked at its 3rd and 5th goals, then stood at DAD's call.
- **The end of a call in the field.** The eyes now read the call's own window and the sound effects, so the AI presses once when the game waits for A or B.
  - #99: both A arms sat at the call to the 30,000-frame bound. Both B arms pressed once (87 and 105 frames in) and went on.
- **Both A/Bs:** each pair had the same start state and seed, and every prediction held.
- **New in this round:** two controls on the real game.
  - The sail after DAD's call: a scene that really locks the controls. No wait for 917 frames, only the script's own 3 waits, and DEWFORD reached.
  - The chapter-5 POKeNAV call, compared frame by frame with the old eyes: 1,766 frames, 0 differences.
- **Mutants:** CH6H9 and CH6H10 were added, and both are caught.

### The KI-134 verifier's findings, fixed and tested offline
- **V1:** every map's walls go into the route, so a decision in the woods sees ROUTE 104's scene wall too.
- **V2:** the test that kills V10.
- **V3:** places are ranked by the links of the route from where the player stands. From the north strip, RUSTBORO's centre is now the nearest.
- **V4:** tests for V5, V6, V11, V13 and V16.
- **NIT V8:** the landings cache is keyed by the part.
- **Tests:** 10 new tests (test_goals is now 375).
- **Mutants:** G518-G538, all caught. G519 was caught after a corrected prediction, written down before the re-run.
- **Caveats:**
  - A map that no walk from the player is known to reach still counts by maps.
  - The ranking search costs about 155 ms at 62 maps, measured under load.
  - None of this has a live A/B.

### Probe8 (#102, new seeds 6317-6319, the final code)
- All 3 runs ended by themselves, purity CLEAN.
- All 3 reached DEWFORD, with MR. BRINEY talked to at the first try and one press at every call's end.
- None delivered STEVEN's LETTER. That prediction (Q4) failed; probe7 had 1 of 3.
- C1 and C2 again sailed back and bounced on the RUSTBORO/ROUTE 104 crossing.
- C3 spent 1,150,422 frames on the island and ended at the foot of a muddy slope in GRANITE CAVE.

### New stops (reported, not fixed)
- **NS1:** a YES to "sail back to PETALBURG?" (4 of 6 probe runs).
- **NS2:** no way back to the island. The sail is remembered as a scene, and route_to finds no route.
- **NS3:** STEVEN's room entered and left during an errand.
- **NS4:** BRAWLY's gym waits for the words "BRAWLY".
- **NS6 (new):** the muddy slope on GRANITE CAVE B1F. The decomp only lets you up on the MACH BIKE, but the AI plans up it thousands of times. It also ends probe7's C1 and all four A/B B runs.

### Gates
- All PASS on the final tree: test_goals, test_kb2, test_world, test_saving, test_eyes, test_hands, test_battle, test_check_purity, test_step53_a2, test_host, check_fairness, check_purity, call_census, check_paths, ledger --check.
- Evidence files written:
  - 2026-11-05-ch6-stops-live-ab.txt (#99, #100)
  - 2026-11-05-ch6-stops-development-probe.txt (#101)
  - 2026-11-06-ch6-stops-development-probe-2.txt (#102)
  - 2026-11-06-ki134-verifier-follow-ups.txt

### Cleanup
- Both stages are deleted, junctions first. The main sandbox's counts are unchanged: modules 4461, plugins 43, mgba 44, roms 2.
- The worktree's mgba junction and its fixture copy were removed.
- No ai-c6s* profile exists in the main sandbox.

## Chapter 6 stops verification (the verifier, 2026-11-06)

**Verdict: PASS.** Every claim I checked holds when re-derived from the decomp, the raw logs and the game's own saved state. I found no code defect. The 8 findings are all NITs: wording, digests, and untested low-impact guards.

**What I checked against.** The worktree wf_e7452923-f06-3 was copied without .git to `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/ch6stops/verify2/repo`. All my scripts and outputs are in `verify2/`. I did not modify the worktree: its git status is unchanged and no file in it changed after I started.

### The causes, re-derived from the pinned decomp
- **STOP 1 (MR. BRINEY).** Route104_MrBrineysHouse sets MR. BRINEY to MOVEMENT_TYPE_WALK_SEQUENCE_DOWN_LEFT_UP_RIGHT at (9,3) and PEEKO to WALK_SEQUENCE_LEFT_UP_RIGHT_DOWN.
  - MoveNextDirectionInSequence takes the next step with no pause, and walks in place when the way is blocked.
  - The navigator's summary contains "N battles", so the old test `"battle" in outcome` fired on every stuck walk.
  - #98 C1 had 54 talk goals for him and none landed: 28 'interrupted on the way', 19 'unreachable', 7 'did not answer'.
- **STOP 2 (the end of a call).** In match_call.c, MatchCall_PrintMessage (state 5) waits for `!RunMatchCallTextPrinter(tWindowId) && !IsSEPlaying() && JOY_NEW(A|B)`.
  - IsSEPlaying is exactly the rule in sound_effect_playing.
  - The eyes' text_printer_wait already covers the `\p` waits on every printer.
- **NS6 (the muddy slope).** ForcedMovement_MuddySlope forces the player south unless moving north at PLAYER_SPEED_FASTEST.
  - In both kept memories, (9,9) and (9,10) are MUDDY_SLOPE and recorded as walkable, with no bumps.
  - (9,10) was visited 7,536 times in probe8 C3 and 3,471 times in probe7 C1.
- **NS2 (no way back to the island).** On probe7 C1's memory, route_to by maps from ROUTE104 or PETALBURG to DEWFORD or STEVEN's room returns None in all four cases.

### Flags read from the GAME, with my own reader
- I wrote my own reader, `state_flags.py`, which takes flag numbers from flags.h and opponents.h. It reads the savestate's gbAs chunk through gSaveBlock1Ptr, or the .sav sectors.
- All 18 states and saves match the builder:
  - **Probe7 C1's last battery save** (counter 20, play time 5:44:44, DEWFORD Pokemon Center): SAILING_INTRO, DELIVERED_STEVEN_LETTER, REGISTERED_STEVEN_POKENAV, BADGE01 and VISITED_DEWFORD are set; BADGE02 is not.
  - **Probe8:** all 3 runs have the intro and DEWFORD flags, and none has the letter or BADGE02. C3 has TRAINER_JOCELYN, BRENDEN and LILITH and ends on GRANITE_CAVE_B1F.
  - **A/B A arms:** they end on their start maps (ROUTE105 or the woods), with no DEWFORD.
  - **A/B B arms:** all four end on GRANITE_CAVE_B1F with DEWFORD set.

### The live claims, re-derived from the runs' own records
- **#99 (STOP 2).**
  - A arms: 99 and 99 STUCK records, and no press at the call.
  - B arms: one press per call, 87 and 105 frames in. B-K1 had 3 calls with 1 press each.
- **#100 (STOP 1).**
  - B arms: the first talk goal for MR. BRINEY landed, with the intro flag 3,598 and 3,578 frames in.
  - A arms: they talked to him at their 3rd and 5th goals, at +9,861 and +20,156 frames.
- **Probes 7 and 8.** In 6 of 6 runs the first MR. BRINEY talk landed, each call ended with exactly 1 press, and there were 0 STUCK records.
- **Probe8 bouncing.** The ping-pong ends at the RUSTBORO / ROUTE 104 crossing were 144+143 (C1) and 115+113 (C2).
- **NS1.** The YES to 'sail back to petalburg?' came from QUESTION_RULES' default answer.
- **Pairs.** Each A/B pair had the same start md5 and seed.

### Predictions, seeds and ledger
- Every prediction file's sha256 equals the recorded hash. Each was written before its first job:
  - abcall: 20:48:32, before 20:49:09
  - abtalk: 20:48:42, before 20:53:30
  - probe7: 21:02:13, before 21:02:40
  - probe8: 05:09:48, before 05:13:25
  - the mutant predictions: before their runs
- Addendum 1 (G519) and addendum 2 were written after the runs that prompted them, and say so.
- **Seeds.** Seeds 6290-6340 appear only in #96-#102 of this lineage. I checked every ledger: main, every worktree, pokebot-wt-*, the learner's clone and the scratch copies. No range was re-run.
- **Ledger #101** reads truthfully: 2 of 3 runs ended, C1 was interrupted, and its flags come from the save. Only its 'ended' field holds the closure time (V-N6).

### Gates (my copy)
- These passed: test_goals 375, test_kb2 124, test_world 132, test_saving 151, test_eyes 73 (including LiveCallEndTests), test_battle 107, test_check_purity 30, test_step53_a2 34 (5 skipped), check_fairness, check_purity, check_paths and ledger --check.
- Two failures came from my environment, not the code:
  - test_hands ProvenanceTests needs .git. Run read-only in the worktree, it passes 2/2.
  - test_host ResetRefusalTests hit a wall-clock limit while the machine was loaded. On a quiet machine test_host passes 37/37.
- call_census, run read-only in the worktree: since HEAD 28 sites, 0 missing; since 43485a36, 91 sites, 0 missing.

### Mutants
- **revert_step5:** G0, plus G470-G538, plus G21, G26, G32, G42 and G71. All 74 were caught, G0 passed, and the frozen tree digest was c9ecb688b349a89c (the same as the builder's run 3).
- **revert_r1:** R0, CH6H1-6, CH6H8-10, C216 and F022. All 11 were caught, and R0 passed.
- **My own 10 mutants** (hashed first): 4 were caught. 6 low-impact guards survive (V-N4).

### My own tests
- I wrote 5 extra simulation tests on test_goals' cottage simulation, in `test_verifier_walkers.py`.
- With the new code:
  - a back-and-forth walker (no pause between steps) was talked to from 8 of 8 phases;
  - a 28-step round (448 frames, longer than WALKER_WATCH) from 10 of 10;
  - a standing person while two walkers cross the room from 6 of 6;
  - the shortest wanderer delay (48 frames per tile) was read as 'standing'.
- FAULT arm, with the old approach: 4 of 8 and 0 of 10.

### Chapters 1-5 controls on real memories
- **Routes, K134-V1 (`compare_routes.py`).**
  - Old route_to (43485a36) was compared with new route_to under the maps mapping, from every map, 2-3 visited tiles each, to every map.
  - The other maps' things came from the decomp's object_events (a superset of what a run can see), because a loaded memory has no objects_now.
  - Memories: the three chapter-5 chain ends at 3 snapshots each, the KI-134 B arm's C1, and probe8 C3.
  - Result: 46,278 route calls, 0 differences, and 0 differences between the old and the refactored code given the same single set of walls.
  - FAULT arm (a wall row across PETALBURG WOODS): 160 of 1,104 routes differ, so the instrument can see a difference.
- **Ranking, K134-V3 (`rank_compare.py`, through the real GoalManager).**
  - About 7,000 positions on 6 memories.
  - Every heal and mart choice that changed is PETALBURG -> RUSTBORO from ROUTE 104's north part or the flower shop: 300 on the chapter 5-6 memories and 151 on the chapter 1-5 memories. Every one is nearer by the new count.
  - Nothing came out WORSE, and no choice was a place no walk from the player's tile reaches. So the builder's flagged caveat never occurred.
  - lead_toward did not change anywhere.
- **Cost.** region_hops on probe7 C1's 62-map memory took a median of 128 ms and a maximum of 174 ms.

### Fairness
- The new reads are object tiles and facing, the call task's state and its window's printer, and the two sound-effect players' status words (what a person hears).
- They are all in host/eyes.py, the one place the purity gate allows read_symbol.
- check_fairness and check_purity pass.

### Caveats that stay
- The KI-134 follow-ups have no live A/B.
- The talk change touches every chapter 1-5 talk, but its regression evidence is offline only: tests, my simulation tests, and the route and rank controls. run_regression --full was not run.
- The probes are development runs, one trajectory per start.

### Cleanup
- My copy's mgba junction was removed first, then its fixture profile copy.
- No junction is left in verify2; the scratch extract armA_check was deleted.
- The main sandbox's counts are unchanged: modules 4461, plugins 43, mgba 44, roms 2 (the same before and after).
- My mutant runs left no folders in %TEMP%.
- Nothing was committed or staged, and no git command that changes anything was run.

## Chapter 6 stops, round 3 (the builders, 2026-11-06)

A second builder finished this round. The first builder was cut off by a usage limit at about 08:20, after writing the round's code, most of its tests, the starts and the batch runner. The lead committed that partial work as 07913cde on wip/ch6-ch7. The second builder closed ledger #103, finished the tests, wrote and ran the mutants, reviewed the fairness-gate change, ran the gates, re-ran the live A/B on new seeds, ran the probe and cleaned up. Nothing is committed. The work sits uncommitted in worktree wf_e7452923-f06-3.

**#103 (abr3, seeds 6320-6325) was interrupted. It gives no A/B result.**
- Its orchestrator died with the first builder after starting 3 of its 12 jobs.
- One run ended through the harness: B-S1q-6320. It answered NO, stayed on the island and ended in GRANITE CAVE B1F.
- A-S1q-6320 finished its play: it answered YES and ended on ROUTE 116. But its harness result was never written, so its harness checks never ran.
- A-S1q-6321 was interrupted, and 9 jobs never started.
- The entry is closed with that verdict. Its seeds were not re-run.

**What the round changed (all play code is the first builder's):**
- **NS1, the sail-back question.** A question whose words offer a trip to a named town is answered by where the AI's goal is. Every other question is answered as before; the test covers every yes/no page in the decomp.
- **NS2, no way back to the island.**
  - When answering YES to a trip offer carries the player away by scenes alone, that trip is kept as a ride in world memory. Routes and distances then use the ride as a link.
  - The RUSTBORO / ROUTE 104 crossing ping-pong was a defect of its own. A road was planned through the map beyond another edge. A road is now walked to over its own side only.
- **NS3, STEVEN's room.** A walk that is not the story's own stops when the story's next person comes into view. Errands that are not urgent wait.
- **NS4, BRAWLY and errands.** The knowledge base knows which leader holds which gym. The AI uses it once it has stood inside that gym. Errands never target a mart or grass that no known way leads to.
- **NS6, the muddy slope.** A step undone by a slide is learned like a bump. This uses only what the screen shows; no MACH BIKE knowledge was used.
- **The last verifier's NITs.** V-N4's six guards are pinned, V-N5 is decided and stated, and the wording NITs are fixed.

**The fairness-gate change.** The atlas may now load world/bosses.json, and every key of that file is classified. Measured:
- It removes no developer-only key and leaves the hidden keys unchanged.
- It adds four developer-only keys.
- It makes naming the file in deciding code a breach.
- New breaches of its kind fail, and the old fault tests still pass.
- Gate mutants CH7F1 and CH7F2 are caught.

**Proof offline.** Tests have a FAULT and a CONTROL for every guard.
- The second builder added t3b, t10, g7, r2 'never ends', s7 and k_f3b, and strengthened s2, g5 and p2.
- 90 new mutants ran, with predictions hashed before each run. All were caught, except four predicted and confirmed REDUNDANT with reasons.
- Run 1 had two misses, both recorded:
  - G571 survived because test_p2 was vacuous; the test was fixed.
  - CH6S8 was wrongly predicted REDUNDANT and the prediction was corrected.
- Four older mutants whose anchor lines the round changed were re-anchored and caught.
- The call census since 66acbd1c passes with 24 reasoned waivers. Every gate passes.

**Live A/B #105 (new seeds 6326-6331; arm A = 66acbd1c, arm B = the round's code; same start and seed per pair).** All seven predictions held in every pair. Read from the GAME and the runs' own records:
- **NS1:** A answered YES and left the island both times. B answered NO and stayed.
- **NS2:** B rode back to DEWFORD and delivered STEVEN's letter (the game's flag) both times. A never reached DEWFORD.
- **NS6:** A stood on the slope tile about 600 times without leaving B1F. B slid twice, put the way aside and left. In one pair B then delivered the letter.

Caveat: two pairs per stop, one trajectory each, short runs, development only.

**Development probe #104 (new seeds 6332-6334, from the three chapter-5 ends).**
- All 3 runs delivered the letter.
- C2 and C3 earned BADGE02 (the game's flags) and reached the target.
- C1 lost to BRAWLY three times with one strong Pokemon and five weak ones. The run ended at MAX_LOSSES. This is a new stop, not fixed.
- Prediction Q2 was not tested: no run met the sail-back question.
- Caveat: these seeds differ from the earlier probes, so the better outcome is not causal evidence by itself. It is one trajectory per start and never a rate.

**Cleanup.** Both stages were torn down, junctions first. The main sandbox's counts are unchanged: modules 4461, plugins 43, mgba 44, roms 2. No junction is left, and no world.jsonl is 300 MB or larger.

**Evidence.** ai_player/evidence/2026-11-06-ch6-stops-round3-live-ab.txt and 2026-11-06-ch6-stops-development-probe-3.txt. Progress is logged in s53/ch6stops3/STATE.md.

## Chapter 6 stops, round 3: verification (the verifier, 2026-11-06)

**Verdict: CONDITIONAL PASS.** The round's main claims hold when re-derived from the raw records, the game's flags and the decomp. One regression in play was introduced by NS4 and was not reported (V3-1, MAJOR): it must be fixed before the round is accepted. N1's stated cause is wrong (V3-2) and must be corrected. The rest are MINOR or NIT.

I worked on a copy of worktree wf_e7452923-f06-3 (no .git) at s53/ch6stops3/verify/repo. I committed and staged nothing. I made no live run, so no seed was used. Progress is in s53/ch6stops3/STATE.md, and all outputs are in s53/ch6stops3/verify/.

**The fairness-gate change.** I planted one breach of each kind the gate guards (gate_plants.py; predictions hashed first). All 21 plants behaved as predicted:
- 19 real breaches fail with the rule named:
  - RULE A: a marks read, a flag-name string, getattr of flags.
  - B1: bosses.json and maps.json named in deciding code.
  - B2: the badge flag, rematches, ref, order, entry, notes, a hidden key in the atlas.
  - B3, and RULE C.
  - Keys planted under a boss, its party and its badge, and at top level.
- The control passes, and a docstring mention passes.
- The change removes no developer-only key and leaves the hidden keys unchanged.
- No real breach passes because of the change.
- Gaps, as predicted:
  - boss['fight'] and boss['id'] pass. This is the documented by-name limit, but `fight` is not named in it (V3-6).
  - Two holes are older than the round (V3-9).
- Classifying the bosses' held items as AI matches USER RULING 44.

**Causes re-derived from the pinned decomp:**
- **NS1:** data/maps/DewfordTown/scripts.inc:12 and :44-45. With the letter undelivered, the MSGBOX_YESNO "sail back to PETALBURG?" sails on YES.
- **NS6:** src/field_player_avatar.c:567-580, ForcedMovement_MuddySlope. Unless the player goes north at the fastest speed, it is forced SOUTH.
- **NS2:** the sail is an applymovement-and-warp scene.
- **NS4:** the gym sign reads "LEADER: BRAWLY".
- **MR. BRINEY's house:** three yes/no offers, by flag, then a multichoice once both deliveries are done.

**The travel-question rule.** I ran trip_offer on every page of every text in the decomp (trip_census.py), not only the last page of MSGBOX_YESNO.
- Exactly six yes/no texts are trip offers: MR. BRINEY's five and the SOUTHERN ISLAND sailor's.
- The other ten matches are statements, never yes/no.
- The one message-plus-yesnobox question that t2 does not read is not a trip offer.
- None of 8,181 C string literals is a trip offer.
- So every other question in chapters 1-7 is answered as before: the nurse, the shop, the rival, the PokeNav, STEVEN and the gym. I found no question the rule now answers wrongly.

**Rides:**
- A ride is armed only by a YES to one of those six offers, so a cutscene warp, a fall or a whiteout cannot record one.
- Old memories load as before (VT5).
- In the probe, the first sail was kept as house -> DEWFORD (11, 9) in 3 of 3 runs.
- GoalRunner.ride calls a talk that left a menu open "rode" (V3-4, chapter 8 or later).

**Muddy slope and roads:**
- A ledge, a battle, a scene and a whiteout cannot make a false slide: the mutants and tests hold, and VM1 is CAUGHT.
- On probe9 C1's chapter 1-5 memory (48 maps) and its end memory (61 maps), the crossing change alters road plans on ROUTE104 only. 2,072 of 34,760 start-road pairs are lost there (the cross-map plans); there are 0 on any other map and none became dearer.

**Tests and mutants:**
- I re-ran the round's suites; all pass. test_hands fails only because the copy has no .git.
- My mutants (predictions hashed first):
  - VM1, VM4, VM5 and VM6 are CAUGHT. I wrongly predicted that VM4-VM6 would survive: the tests are stronger than I expected.
  - VM2, VM3 and VM7 survive, which are test gaps (V3-7).
- I did not re-run the builder's 90 mutants. Their outputs are internally consistent.
- One census waiver still states a refuted claim (V3-5).

**Live A/B #105, re-derived from the raw records without the builder's judge (my_judge_abr3b.py).** Read from the GAME and the runs' own records:
- P1-P7 hold in every pair (2 of 2 each), and each end state's md5 matches its L5 check.
- **NS1:** A pressed YES and ended off the island both times; B pressed NO and stayed.
- **NS2:** in both pairs, B logged "rode" from 17:0, stood in DEWFORD afterwards, and the GAME set DELIVERED_STEVEN_LETTER. A never reached DEWFORD.
- **NS6:** A had 623 and 579 records on the slope tile; B slid twice, had 4 records there, and left.
- The predictions were hashed at 09:51, before the 10:11 launch.
- Seeds 6320-6334 are each used only by their own entry; 6335-6345 are free in 408 ledgers.
- Ledger #103's verdict reads truthfully, checked against the salvage files and B-S1q-6320's result.
- Caveat: S2's memory was given its ride (V3-8).

**Probe #104, re-derived from the records:**
- Q1, Q3, Q4, Q5 and Q6 hold (3 of 3); Q2 was not tested.
- BADGE02 in C2 and C3, read from the game's flags.
- NS3's stop came before STEVEN's talk in 3 of 3 runs.

**The MAJOR (V3-1).** When no grass can be reached, NS4 makes no train goal and never marks the fight "ready". That same flag gates the heal before a known fight.
- On the island, the only grass the AI knows is on the mainland, so it never heals before BRAWLY.
- Live: C3 talked to BRAWLY at 77% party HP and C2 at 89.9%, with ch7_brawly ready False in all 3 runs.
- Offline A/B (VT1): the round's code never heals; with the clause neutralised, the second decision heals.
- The round's own test_g5 and mutant G607 pin the defect in place.

**N1 (V3-2).** C1 was not judged ready by level. It was short by steps (0 of 80), and training was suppressed because no grass was reachable.

**Risk (V3-3, MINOR).** With the leader in view in his gym and the party short, a training goal's walk is stopped at its first look (VT8). Not seen live.

**Cleanup.** No staging, no junction and no world.jsonl of 300 MB or more were left. The main sandbox's counts are unchanged: modules 4461, plugins 43, mgba 44, roms 2. verify/repo (about 572 MB) is kept for re-checks and may be deleted.

Development runs are one trajectory per start, never a rate.

## Chapter 6 stops, round 4 (the builder, 2026-11-06)

I fixed the round-3 verifier's findings in worktree wf_e7452923-f06-3, investigated N1 and probe #104's two observations, ran a live A/B for V3-1 and a new development probe. Nothing is committed. Progress is logged in s53/ch6stops4/STATE.md.

**V3-1 (MAJOR): the heal before a known fight never fired where the AI cannot train.** Fixed.
- Cause: the heal waited for the party to be judged ready. On the island no grass can be reached, so it never was.
- Change: "trained" and "ready for the fight" are now separate. When the party cannot train where it stands (grass seen, no known way to any), it heals before the fight anyway. The training record still says it did not train.
- Proof offline: reproduced on the base first. The verifier's VT1 is now a FAULT/CONTROL test, test_g5 asserts the heal, and three new mutants are caught. G607 was re-run and caught.
- Live A/B #106, seeds 6335-6336: same start and seed per pair. The start is DEWFORD's gym with STEVEN done, no badge, and the party at 86.1%. It was built on the test side with the AI's own brains and no memory write.
  - Read from the game's party data at the start of each BRAWLY battle: arm B (this round's code) healed at DEWFORD's POKéMON CENTER and began its first BRAWLY fight at 100% in both pairs.
  - Arm A (the base) began it at 86.1% in both.
  - Caveat: 2 pairs, one trajectory each. Both arms lost the fight, so this shows the heal firing, not a win.

**V3-2: N1's stated cause was wrong.** Corrected in the probe-3 evidence. Training was short by steps (0 of 80) and suppressed because no grass is reachable from the island. The party was never judged ready by level.

**N1: why C1 lost to BRAWLY three times.** Read from the records:
- HP was not the problem: fight 1 began at 95.4%, fights 2 and 3 at 100%.
- Level was not the problem: Grovyle was L21-22 against BRAWLY's 16/16/19.
- The cause is the party and the battle. Grovyle carried every fight alone with 20-40 power moves and used two Potions in fight 1. The five L3-L6 behind it fainted at once.
- Training in GRANITE CAVE would have added about 0.4 of a level for the Story's one session. On the test side, 12 cave battles took Grovyle from L21 to L22.
- So no cave training was built, and the battle brain was not changed. It is listed as a new stop.
- Probe #107 confirms it: C1 healed and fought BRAWLY three times at 100%, and lost all three.

**V3-3: the "story person in view" stop was given to training walks.** Fixed. A training or catching walk is no longer stopped while the next step is a fight; it still stops when the next step is a talk (STEVEN).
- Tests: the verifier's VT8, plus a driven walk in a simulated gym with BRAWLY in view. The go walk stops at once; the training walk walks on 12 steps.
- Two mutants caught. Not seen live.

**V3-4: a ride reported "rode" while still on the same map.** Fixed. A ride now counts as taken only once the map changes. A talk that ends on the same map, free or held by a menu, puts the ride aside.
- Tests: the verifier's VT9 plus two controls. Mutants caught, and G591 was re-anchored.
- Seen in probe #107: C2 rode twice, each time after the map changed.

**V3-5 to V3-8 (NITs):**
- V3-5: the CH6S8 census waiver is reworded; the reset is load-bearing.
- V3-6: test_k_f3c pins the keys the atlas reads from bosses.json (role, name, battled_on, bosses), and the gate's docstring names `fight`.
- V3-7: the closed-ride retry, the reopen and SPEAKER_REACH 2 are pinned by tests. Their mutants are caught.
- V3-8: NS2's caveat is in its outcome lines. Probe #107 C2 then saw a ride recorded and reused in one run, once.

**V3-9:** noted only, for a later round.

**Probe #104's two observations:**
- "The battle: budget" after BADGE02 was set is the mechanism behind KI-131. The battle skill waited for the player to be free, so the leader's own scene after the battle ran inside the skill's budget and watchdog: 5,411 frames with an evolution in C2, and the badge fanfare in C3.
  - Fixed: a battle the game says is over (gBattleOutcome set, the battle off the screen) is now reported by its outcome.
  - Offline FAULT/CONTROL tests and two mutants. In probe #107, both BRAWLY wins are logged "won".
  - KI-131's own grunt case was not re-run.
- "Ping-pong on DEWFORD's edges and at the gym door": the records show none. The navigator's ping-pong rule ended 0 goals.
  - At the edge there is one 46-64 frame look-around flip across DEWFORD's top edge, never repeated.
  - At the door there are only re-entries after whiteouts.
  - This is listed as a new stop, not a defect.

**Development probe #107** (seeds 6337-6339, the probe8/9 starts, target ch7_brawly, 1,200,000 frames; one trajectory per start, never a rate). Read from the game:
- All 3 delivered STEVEN's letter.
- C2 (Catcher) and C3 (Trainer) earned BADGE02. C2 won on its third fight, after riding its recorded ride back from RUSTBORO twice.
- C1 (Story) lost to BRAWLY three times at 100% and ended at MAX_LOSSES.
- Every first BRAWLY fight began at 93.9% or more, against 77.2% and 89.9% in probe #104.
- All five predictions held. These seeds differ from probe #104's, so the gain is not causal evidence by itself.
- New stops:
  - the Story's party loses to BRAWLY at full HP;
  - a talk goal ends "stuck" during the badge fanfare (the 300-frame watchdog);
  - training from ROUTE 104's north strip finds "no seen grass can be reached";
  - a heal walk out of GRANITE CAVE runs out of its 9,000-frame budget.

**Gates on the final tree:**
- Every unit suite named passes, plus FairnessTests and test_evidence.
- check_fairness, check_purity, check_paths and ledger --check pass.
- call_census passes after two reasoned waivers. It first failed on skills/battle.py's unchanged caller and its log lines.
- Mutants: revert_step5 caught 12 of 12 and revert_r1 2 of 2, with both controls passing. Every anchor is unique.

**Cleanup:** the stage was torn down, junctions first. The main sandbox's counts are unchanged (4461/43/44/2), and every kept world.jsonl is under 300 MB.

**Evidence:**
- ai_player/evidence/2026-11-06-ch7-stops-round4-live-ab.txt
- ai_player/evidence/2026-11-06-ch6-stops-development-probe-4.txt

## Chapter 6 stops, round 4: verification (the verifier, 2026-11-06)

**Verdict: CONDITIONAL PASS.**

Every fix I checked holds, and the builder's numbers re-derive from the raw records. Two conditions apply:
- one MAJOR: a run-ending wedge that the round's own A/B shows, missing from the new-stops list;
- one MINOR: the new heal can head for a centre no known way leads to.

I worked on a copy of the worktree (s53/ch6stops4/verify/repo, play digest fdc7b44e, the same as the A/B's arm B). I made no live run, no stage and no junction. Progress is in verify/STATE.md.

**What I re-derived from the raw records (verify/vjudge.py)**
- **A/B #106:** P1 to P4 held in 2 of 2 pairs. Read from the game's party data on the first trainer-266 record:
  - arm B began its first BRAWLY fight at 100% (f953798, f953710), after 102 records in DEWFORD's POKéMON CENTER;
  - arm A began it at 86.1% (f949521, f949508), with no heal and 0 centre records.
  - All 4 runs: purity CLEAN, exit 0, L5.THIS_RUN PASS.
  - Arm B's 6th fight was cut off by the frame budget. The builder's "lost 5 of 5" counts completed fights only.
- **Probe #107:** every flag, frame count, end map and BRAWLY fight HP matches the builder's report:
  - C1 100/100/100, all lost;
  - C2 93.9/100/100, won on the third;
  - C3 98.7, won.
  - Probe #104's 95.4%, 89.9% and 77.2% also match.
- **Order and seeds:** the prediction hashes match the files. The files are dated 21:12, before the first job at 21:13, and the ledger's bounds_sha256 values agree. Seeds 6335-6339 appear only in this worktree's ledger (#106, #107); main (max id 95) and lc-c2 (max id 99) hold none. No spent range was re-run.

**Tests, gates and mutants re-run on the copy**
- test_goals 421, test_battle 110, test_kb2 126 and FairnessTests 9 all pass.
- test_evidence passes 25 of 27. The 2 failures need .git, which the copy does not have.
- check_fairness, check_purity and check_paths pass.
- The builder's mutants: revert_step5 G0 plus G591, G607 and G614-G623 are all CAUGHT, and FROZEN TREE passes. revert_r1 R0 (599) plus CH6S14 and CH6S15 are CAUGHT.

**My own tests and mutants** (predictions hashed first: prediction_verify4.txt, sha256 542def81)

V3-1:
- **Chapters 1-5 unchanged:** in 12 scenarios (the rival, ROXANNE, the grunt; Story and Trainer; 75% and 50%; grass reachable), the round's first 3 goals are identical to the base's in kind, map and reason.
- **Real memories:** over the three chapter-5 chain ends (48, 32 and 48 maps), grass_target is never "out of reach". Over I1's memory, it is "out of reach" on the 13 island maps and on ROUTE105, a sea route reached only by the boat scene.
- **Training places:** every map with tall grass seen in these memories has a land table in the pinned decomp.

Mutants:
- VM3 and VM4 are CAUGHT, as predicted.
- VM2 is equivalent, as predicted.
- VM5 was caught by existing tests in test_goals. I had predicted it would survive; that prediction was wrong.
- VM1 and VM6 survive the builder's suites, as predicted (finding VR4-3).

V3-3:
- The tests hold.
- The milestone-level check matches a step-level one for every current milestone, because each fight milestone's talk step is the fighter.
- It was not seen live: no train or catch walk had a leader in view.

V3-4:
- Probe #107 C2 logged "rode" twice, each time after the map changed.
- A talk held on the same map now closes the ride. The menu itself stays open, though (see VR4-1).

The battle end (OBS-2):
- The new path fired twice live, both BRAWLY wins.
- gBattleOutcome is reset at battle start (battle_main.c BattleStartClearSetData), so a mid-battle bag or party screen reads 0. My VT-B1 confirms such a screen is still reported as "the battle: ...".

N1:
- The cave's table is confirmed: GRANITE_CAVE_1F rate 10, L6-L10, 10×16/2880 = 5.6% a step.
- The 12 cave battles took Grovyle from L21 to L22 (make_island_start2c.out).
- The decision not to build cave training stands.

**Findings**
- **VR4-1 (MAJOR): a missing new stop.** Both arm-A runs of #106 whited out to RUSTBORO and sailed back to DEWFORD's dock. A curiosity chat there picked MR. BRINEY, whose menu [PETALBURG, SLATEPORT, EXIT] stays on screen once STEVEN's letter is delivered (decomp DewfordTown_EventScript_Briney). The AI cannot answer it.
  - The menu was on screen for the rest of each run: 20,167 and 15,360 frames, about 97% of each run's action records. Only STORY_PATIENCE (120,000 frames) would end such a run.
  - It is KI-132's class, filed as "low impact"; in chapter 7 it ends the run.
  - The round's code takes the same path; only goals.py and battle.py differ from the base. It is not caused by the round, and it does not affect V3-1's A/B.
  - Chapter 8's sail to SLATEPORT goes through the same menu.
- **VR4-2 (MINOR): the new heal can go to an unreachable centre.** In the gym, with the only known centre on the mainland, the round's code heals toward RUSTBORO's centre, which no known way reaches. With each heal failing, it does so 6 times in 30 decisions. The base does not. It is unlikely in practice, because every real run here knew DEWFORD's centre.
- **VR4-3 (NIT):** the battle-end branch is pinned only for "won". VM1 (a screen off the battle with gBattleOutcome 0 read as won) and VM6 (a held loss not counted) both survive test_battle.
- **VR4-4 (NIT):** "This is the mechanism of KI-131" needs its caveat. The records agree: in three earlier grunt battles that ended "the battle: budget", the screen showed the field's text, not the battle.
- **VR4-5 (NIT):** test_k_f3c pins one reading shape of bosses.json only. Record it with V3-9.

**Conditions for PASS**
- List VR4-1 as a new stop, in the A/B evidence and against KI-132.
- Restrict the before-fight top-up to reachable centres (VR4-2), with VT-R1 as its FAULT test.

**Cleanup**
- I built no stage and made no junction; a scan found 0 reparse points under verify/.
- The main sandbox's counts are unchanged: modules 4461, plugins 43, mgba 44, roms 2, and 0 ai-c6s4-* profiles.
- The worktree was not modified.

**Files** (under s53/ch6stops4/verify/)
- STATE.md
- prediction_verify4.txt and its sha256
- vjudge.py and its .out files
- wedge.py
- budget_screens.py
- scen4.py with scen_R and scen_B (.json, .out)
- vt_r5.py and vt_r5.out
- vmutants4.py and vmutants4.out
- rerun_step5.out, rerun_r1.out and gate_*.out
- repo/ai_player/gates/test_verify4.py

## Chapter 6 stops, round 5 (the builder, 2026-11-06)

**Where the work is.** The worktree wf_e7452923-f06-3 (branch wip/ch6-ch7), on top of c41db547. Nothing is committed. Progress is in s53/ch6stops5/STATE.md.

**VR4-1 (MAJOR): MR. BRINEY's dock menu. Fixed, and shown live in 2 of 2 pairs (development only).**

Headline, with its caveat: after a chat with MR. BRINEY, the old code stays held on his menu until the run's frame bound. The new code backs out of the menu within about 20 frames and plays on. This is 2 pairs, one trajectory each, from a test-side start. The seeds were chosen offline so that the chat happens.

- **Cause.** A field multichoice that no page named was "left to the caller". The play loop then returned "stuck: an unexpected multichoice on screen" once a frame until its bound. The menu is DewfordTown_EventScript_Briney's MULTI_BRINEY_ON_DEWFORD. It appears once STEVEN's letter is delivered, and B is allowed on it.
- **Reproduced first.** I re-ran the round-4 verifier's wedge.py on #106's records. I also ran the new tests on c41db547; there they fail as expected:
  - test_m1 stays "stuck" instead of freeing the player;
  - test_m5's real play loop runs to "no progress for 120010 frames".
- **The rule.** A field menu that nothing names, in a scene the AI opened itself, is backed out of.
  - "Opened itself" means the last press the AI made while free was its own A. This is read from its own presses, never from game state.
  - It presses B and reads the screen to see whether the menu left. If B is refused, it chooses the option that reads EXIT or CANCEL.
  - The talk that opened the menu then counts as a failed chat.
- **Forced menus.** A menu is forced if:
  - it is still, or again, on screen after the cancel; or
  - the cancel does not take it off the screen; or
  - it is in a scene the AI did not open. A run that begins inside a scene counts here.

  For a forced menu the AI presses nothing and says so once. The run then ends at once with that stop: no frame passes and there is no second play-out. This end is proven offline only.
- **Unchanged.** A menu that the words name is still chosen (the POKeNAV tutorial, test_m10). App menus are unchanged.
- **Tests.** test_goals Round5MenuTests m1 to m11 (FAULT and CONTROL halves), and InstructedTests g4b, g4c and c3 updated. NS1's and NS2's tests pass unchanged; both are yes/no questions.
- **Live A/B, ledger #108.**
  - Seeds 6341-6342. The prediction was hashed and registered before the runs.
  - Start D1 was made on the test side with the AI's own hands brains and no memory write: from I1, heal at the nurse, then walk to the dock tile beside him.
  - Offline, both arms' first decision on these seeds is the chat with him. Seed 6340 was not used.
  - Read from the records' digests:

    | Seed | Arm A (c41db547) | Arm B (round 5) |
    |---|---|---|
    | 6341 | menu on every record to the end, 19,471 frames, never off the dock tile | off the screen after 21 frames, the game's own "You just tell me..." page read next, then moved on |
    | 6342 | menu on every record to the end, 19,467 frames, never off the dock tile | off the screen after 19 frames, then moved on |

  - All 4 runs: purity CLEAN, exit 0, L5.THIS_RUN PASS.

**VR4-2 (MINOR): fixed offline, more narrowly than asked.**

- **The change.** V3-1's top-up, where the AI cannot train, now uses only a centre that a known way leads to; otherwise it does not heal. It is used only when the party is neither in danger nor under its heal line.
- **Why narrower.** My first version also held the trained party's heal before a fight to a known way. Mutant run 1's control failed on two existing tests that pin that chapters 1-5 heal. I narrowed the rule.
- **Tests.**
  - Round5HealTests r1 is the FAULT, the verifier's VT-R1 and VT-R2. Its CONTROL is DEWFORD's centre, which a known way leads to.
  - r2 is a CONTROL: a party in danger, or under its heal line, still heads for the unreachable centre.
  - r3 checks heal_place itself.
  - The verifier's scen4.py gives the same chapters 1-5 results on both trees.
- **Open.** The wider rule needs a ruling if it is wanted.

**VR4-3 (NIT).** test_battle has two new tests:
- e4 (FAULT): a lost battle whose whiteout holds the screen reads "lost".
- e5 (CONTROL): VT-B1.

They catch the verifier's VM6 and VM1 as CH6S17 and CH6S16.

**VR4-4 (NIT).** The wording now reads "the likely mechanism of KI-131: its records agree; its own case not re-run". This is in skills/battle.py, test_battle.py and the round-4 evidence. That evidence file also now records VR4-1 against #106's arm A.

**VR4-5.** Noted with V3-9 for the fairness-gate round.

**Mutants.** Predictions were hashed before each run.
- Run 1: its controls failed (the wide VR4-2). It was superseded.
- Run 2: G624-G643 and re-anchored G10 caught; G467, G469, G614 and G615 re-run and caught; CH6S16 and CH6S17 caught; both controls PASS.
- Run 3: these are the census's deleting mutants. G644, G645, G646 and G648 caught; G647 REDUNDANT, as predicted.

**Gates on the final tree: all PASS.**
- Suites: test_goals 435, test_kb2 126, test_world 139, test_saving 151, test_eyes 75, test_hands 57, test_battle 112, test_check_purity 30, test_step53_a2 34 (5 skipped), test_host 37, FairnessTests 9, test_evidence 27.
- Checks: check_fairness, check_purity, call_census (0 missing, with 3 reasoned waivers), check_paths, ledger --check.
- Mutant anchors: 1,252, all unique.

**New stops (not fixed).**
- **P5-1.** After backing out of the menu, arm B went to the gym, but its search for BRAWLY ping-ponged through the gym's door, three times a run. It never fought him within 20,000 frames.
- **Places on BRINEY's menu.** Choosing a place there when a ride is wanted is not built; chapter 8's sail to SLATEPORT needs it.
- **Forced menus in later chapters.** A forced menu that nothing names now ends the run at once. None is known in chapters 1-7.

**Cleanup.**
- The stage was removed, junctions first.
- The main sandbox's counts are unchanged: modules 4,461, plugins 43, mgba 44, roms 2. There are 0 ai-c6s5 profiles and no junctions left.
- The main checkout's git status is clean.
- Kept world.jsonl files are 1.5 MB to 136 MB.

**PROJECT KNOWLEDGE was not edited.** KI-132 in 05, the rule in 06, and 07 need updating at the merge.

## Chapter 6 stops, round 5: verification (the verifier, 2026-11-06)

**Verdict: CONDITIONAL PASS.**
- VR4-1 is fixed as claimed. The live A/B holds when re-derived from the raw records.
- VR4-2's narrowing has a MAJOR regression (V5-1). It is offline and at the decision level, and it must be fixed before the merge.

**What was checked.**
- I copied the round's uncommitted tree (worktree wf_e7452923-f06-3 on c41db547, 16,919 files, no .git) to `s53/ch6stops5/verify/repo`.
- I extracted the base with `git archive c41db547` (read-only).
- The copy's play-code digest equals arm B's, 1da3fd6c622518a1. The base's equals arm A's, 7330fa25. So the code reviewed here is the code that ran live.
- Besides the 11 files in the round's diff, the copy differs from the base only in line endings.
- Progress is in `verify/STATE.md`.

**V5-1 (MAJOR): a top-up no longer looks for the town's own centre.**
- What happens: V3-1's top-up (the party not hurt, and it cannot train) now uses `heal_place(reachable=True)`. When the only known centres have no known way to them, that returns None. The `find_center` branch ("a town has one, so it looks here") runs only when `where` is not None, so it is skipped as well.
- Test VT5-1 (predictions hashed 75ab8939 before any run):
  - The state: outdoors in DEWFORD, BRAWLY next, cannot train, party at 75%, only RUSTBORO's centre known, DEWFORD's not seen.
  - The base: `find_center DEWFORD_TOWN`.
  - Round 5: `go DEWFORD_TOWN_GYM`, with no heal.
  - The control (under the heal line): `find_center` on both trees.
- Caveat: how often a run is in this state is not measured. The centre door (2,10) cannot be seen from the dock tile (11,9). The #106 and #108 starts already knew the centre.
- Fix: decide `find_center` on `heal_place(world)`, and keep `reachable=True` for the heal goal only.

**The menu rule against the pinned decomp.** These are all the field multichoices (`Task_HandleMultichoiceInput`) a chapter 1-7 run can meet (`verify/census_menus.py`):

| Menu | What the new rule does | Is that what a person does? |
|---|---|---|
| MR. BRINEY on DEWFORD's dock (MULTI_BRINEY_ON_DEWFORD, after the letter, B allowed) | cancelled with B | yes for a chat. For a wanted ride back (an errand, or the optional EXP. SHARE) a person picks PETALBURG; that is not built, and the base wedged (V5-4) |
| The OLD ROD fisherman's second talk (MULTI_HOWS_FISHING, B IGNORED, no EXIT) | one B, then forced: **the run ends** | no, a person answers either option. The base wedged too. Not disclosed (V5-2) |
| MR. BRINEY's cottage (MULTI_BRINEY_OFF_DEWFORD) | cancelled | only after both deliveries: chapter 8 and later |
| The POKeNAV tutorial's forced START menu | chosen by its words (POKeNAV) | yes (m10) |
| The fossil choice on DEVON 2F | cancelled | needs two fossils: cannot be reached |
| The POKeMON SCHOOL blackboard (a grid) | refused and wedged, as before | it is a sign the AI never presses A on: cannot be reached |
| A POKeMON CENTER PC, the 2F Direct Corner attendant (no adapter), PETALBURG's profile man | cancelled | yes |

- No chapter 1-7 menu loops back on B. A menu shown again after its cancel ends the run (m3), never loops.
- No hidden state is read: the rule uses the pad's own presses, `player_free`, and the menu's kind and options.

**VR4-2, the other checks.**
- Danger heals and heals under the heal line are unchanged (r2, and VT5-1's control).
- The narrowing is accurate: `cannot_train` requires `not ready`.
- The census waivers: 3 added, none removed (the 518-line diff is formatting).

**The live A/B (#108), re-derived.** I read each record's digest and the harness's end read (`verify/vjudge.py`).

| Run | What the records show |
|---|---|
| A 6341 | menu from f951084 on 58,420 of 58,420 records and the last; 0 presses after it; never off (11, 9); held 19,471 frames |
| A 6342 | menu from f951088 on 58,408 of 58,408 records; held 19,467 frames |
| B 6341 | a B press at f951085, the menu gone at f951105 (21 frames), A on the cancel page at f951500; 102 places; ended in the gym (3,3) at (5,27) |
| B 6342 | menu gone after 19 frames; 111 places; ended at (8,17) |

- All 4 runs: purity CLEAN, exit 0, L5.THIS_RUN PASS. P1-P4 hold.
- Order: the prediction was written at 22:50:21 and hashed at 22:50:38; the runs started at 22:50:53. The ledger's bounds hash matches.
- Seeds 6341-6342 appear only in #108 (402 ledgers). 6340 is free.
- One figure is wrong (V5-3): "entered the gym 10 and 11 times". The records show 21 entries in each run.
- The VR4-1 line added to the round-4 evidence holds against #106's records (60,509 and 46,087; f986258 and f991065). Its record totals are off by 10 (V5-7).

**Tests and mutants.**
- The builder's classes, plus ErrandTests, TunnelGruntTests, BattleEndHeldTests and my tests: 65 OK.
- e1-e5 also pass on the base, as claimed.
- The builder's mutants, re-run on the copy:
  - revert_step5: G0 PASS (435 tests), 29 CAUGHT and G647 REDUNDANT, as predicted. The frozen-tree digest 8f8c8daf equals the builder's run 3.
  - revert_r1: R0 PASS, CH6S16 and CH6S17 CAUGHT.
- The builder's three mutant predictions were each hashed before their run.
- My own mutants (hashed first):
  - VM1-VM4 and VM6: CAUGHT, as predicted.
  - VM5 (no "cancel" in CANCEL_WORDS): I predicted it would survive, but it was CAUGHT, and only by the stop's wording (V5-5, a miss in my prediction).

**Other notes (NIT).**
- A scene the game chains on with no free look counts as opened by the AI (V5-6). There is no chapter 1-7 case.

**Hard limits.**
- No commit, no staging, no git write, no live run, no seed used.
- No staging dir or junction was made. Nothing was written outside `verify/`. The main sandbox was not touched.
- The worktree is unchanged (16 entries).
- The main checkout (HEAD e4cd1617) now shows 69 staged evidence entries: 51 added, 18 modified. This verifier did not make them.

**Files** (under `s53/ch6stops5/verify/`):
- `predictions_v5.txt` and `.sha256`
- `vtests/test_verify5.py`
- `run_verify.py`, `out_r5_tests.txt`, `out_base_tests.txt`, `out_mutants.txt`
- `census_menus.py` and `.out`
- `vjudge.py` and `.out`
- `check106.py`
- `rerun_step5.out`, `rerun_r1.out`
- `STATE.md`

## Chapter 6 stops, round 6 (the builder, 2026-11-07)

**Where the work is.** The changes are in worktree wf_e7452923-f06-3 (branch wip/ch6-ch7), on top of 095ea511, and are not committed. Progress is logged in s53/ch6stops6/STATE.md.

**P5-1: find BRAWLY ping-ponged through the gym door. Fixed, and the live A/B held in 2 of 2 pairs.**

Caveat first: this is 2 pairs, one trajectory each, development only, from a test-side start. The seeds were chosen by the offline discriminator. On those seeds, B began its first fight with BRAWLY about 3,670 frames after the start. A never fought him in 20,000 frames. B lost both of those fights. That is P4-1, which this round did not touch.

- **Cause.** I read it from #108's records (diag/diag_p51.py) and the log.
  - The start's world memory knew all 652 tiles of the gym, but the run had never seen BRAWLY. So it had no sighting and could not "seek" him the way #106 did.
  - The find therefore had no place left to visit on the gym. Its fallback picked the way back out of the door. In town, the same rule sent it back in, until the ping-pong rule stopped the find.
  - Each B run made 21 entries onto the gym's map, and none got above row 26.
- **The rule.** A find for the leader the AI has come to fight, in that leader's own gym, with nothing left to see there, walks to the back of the gym (`gym_back`).
  - This is static knowledge: a leader stands at the back, opposite the door.
  - It is offered until reached, never when the navigator has excluded it, and never while there are still places to see.
  - Chapter 2's NORMAN is a talk with no fight, so he is unchanged.
- **Driven tests.** These are on DEWFORD's real layout, taken from D1's memory, with the real GoalRunner and Navigator. The fault test fails on 095ea511 with the same ping-pong. The first-visit controls (ROXANNE, BRAWLY) give identical trajectories on both trees.
- **Live run #109.** Seeds 6351-6352, start D2 (DEWFORD (8, 18), outside the gym door). I made D2 on the test side from D1 with the AI's own goto, with no memory write. All 4 runs were CLEAN, exit 0, L5.THIS_RUN PASS.

  | Arm | Seed 6351 | Seed 6352 |
  |---|---|---|
  | A (095ea511) | no BRAWLY fight; 19 gym entries; highest row 12 | no BRAWLY fight; 27 gym entries; highest row 26 |
  | B (round 6) | BRAWLY fight began at frame +3,675, 100% HP | BRAWLY fight began at frame +3,668, 100% HP |

**V5-1 (MAJOR): fixed, proven offline.**
- The look for a town's own centre is again decided on every centre the AI knows. Only the walk to a centre is held to a known way.
- The verifier's VT5-1 is now the fault test t1. On 095ea511 it gave 'go DEWFORD_TOWN_GYM'; now it gives find_center, then no heal.
- Controls: a reachable centre still heals; a town already looked in gives no heal; a party in danger or under its heal line is unchanged.

**V5-2 (MINOR): fixed by the lead's rule, offline only.**
- **The rule.** A question the AI cannot decline is answered with the option the cursor starts on: a field menu in a scene it opened, which ignores B and has no EXIT or CANCEL. It is counted as an answer, not a back-out, and said once. A loop of the same menu, or a scene the AI did not open, still ends the run.
- **Census.** I extended the verifier's census to chapter 8. It found 50 menus that ignore B. On maps chapters 1-8 can reach there are three:
  - the fisherman: answered ('Excellent');
  - SLATEPORT's battle tent: kept forced, because GO ON starts a battle;
  - MOM's TV question after the Hall of Fame: kept forced, because it is a one-way choice.
- **Kept forced by menu id:** MULTI_GO_ON_REST_RETIRE and the three other GO ON menus, MULTI_TV_LATI, and MULTI_TENT.

**V5-3 to V5-7.**
- V5-3: the evidence now says 21 gym entries in each run, with the definition.
- V5-4: the BRINEY stop also names chapter 7's optional EXP. SHARE trip and errand rides.
- V5-5: a new test chooses an option labelled CANCEL.
- V5-6: the SceneOpener docstring states the chained-scene limit.
- V5-7: the evidence now says "framed records" with the corrected totals.

**Mutants.** I wrote and hashed the predictions before the run, plus revision b for G225, an older mutant whose anchor this round broke.
- revert_step5: G0 PASS, and 31 caught as predicted:
  - G649-G670 (new);
  - G110, G648 and G225 (re-anchored);
  - G627 and G639-G643 (re-run).
- revert_r1: R0 PASS (this round adds no revert_r1 mutant).
- All 1,275 anchors are unique.

**Gates on the final tree: all PASS.**
- Suites: test_goals 452, test_kb2 126, test_world 139, test_saving 151, test_eyes 75, test_hands 57, test_battle 112, test_check_purity 30, test_step53_a2 34, test_host 37, FairnessTests 9, test_evidence 27.
- Checks: check_fairness, check_purity, call_census (4 reasoned waivers), check_paths, and ledger --check.
- I corrected one docstring after the full gate run. test_goals, check_fairness, check_purity, call_census, the anchor check and test_evidence were re-run on that tree and passed.
- run_regression.py was not run.

**New stops (not fixed).**
- **N6-1 (a fairness gap).** DEWFORD's dark gym has a lit circle of 24 px with no trainer beaten. The eyes still report people across their whole 15x10-tile window, so the AI sees further in the dark than a person could.
- **P4-1** is still open.
- **The P5-1 start state** was built on the test side. How often a real run reaches it is not measured.
- **A repeated identical question** in one scene is still forced. FORTREE's HIDDEN POWER giver does this (chapter 10 or later).
- **Later menus that are not excluded** are answered with their first option (the MAUVILLE bike shop and others). None was looked at closely.
- **BRINEY's places menu** is still not built.
- **Seeds:** 6343-6362 were consulted offline. The next free seed is 6363.

**Cleanup.**
- The stage was removed, junctions first.
- The main sandbox counts are unchanged: plugins 43, mgba 44, roms 2 (modules 4,461). No ai-c6s6 profiles and no junctions are left.
- I deleted arm A's world.jsonl files after judging and kept arm B's (5.8 MB each).
- The main checkout shows only its pre-existing ledger.json change from the graded run. This round wrote nothing there.
- PROJECT KNOWLEDGE was not edited.

## Chapter 6 stops, round 6: verification (the verifier, 2026-11-07)

**Verdict: PASS. There is no MAJOR.**
- V5-1, V5-2 and P5-1 hold in chapters 1-8, and the corrections V5-3 to V5-7 are right.
- #109's live claim holds when re-derived from the game's own records.
- There is one new MINOR in this round's code (VR6-1). The other findings are MINOR or NIT.
- Caveat: #109 is still 2 pairs, one trajectory each, from a start built on the test side. It is development evidence, not a rate.

**What I checked, and how**
- **The code.** The worktree wf_e7452923-f06-3 (095ea511 plus the uncommitted diff) was copied without .git into s53/ch6stops6/verify/repo. 095ea511's ai_player was taken by git archive. I worked only in verify/ and changed nothing in the worktree or the main checkout.
- **Tests.** The builder's Round5 and Round6 classes pass on the copy (31 tests). The full test_goals and test_world pass too: 591 OK.
- **The base.** On 095ea511 (r6_base.out):
  - the fault tests fail: t1, q1, p1 and p3;
  - so do q2, q7 and m3, which test the new rule itself;
  - p5 to p7 error, because their symbols do not exist there;
  - every control passes.

**The answer rule (V5-2): census re-derived on my own**
- My census (vcensus.py) reads every multichoice, multichoicedefault and multichoicegrid in the pinned decomp's data/. It found **50 B-ignored menus**, the same count as the builder's.
- The C-side menus (PC, SS TIDAL, the POKéNAV tutorial) all pass FALSE, so they allow B.
- On the maps chapters 1-8 can reach there are three B-ignored menus:
  - **DEWFORD's fisherman** (MULTI_HOWS_FISHING). It is answered 'Excellent', which only shows a reply page. A person would do the same.
  - **SLATEPORT's battle tent corridor** (MULTI_GO_ON_REST_RETIRE). GO ON starts a battle, so it stays forced. That is right.
  - **MOM's TV question after the Hall of Fame** (MULTI_TV_LATI). It is a one-way choice, so it stays forced. That is right.
- **One walk past SLATEPORT** (ROUTE 110 and MAUVILLE):
  - MULTI_TENT is excluded.
  - MAUVILLE's bike choice would be answered MACH. That is harmless, because the shop swaps bikes.
- **The other B-ignored menus** in later chapters start on an option that does not spend money, give anything away, trade, battle or commit:
  - Battle Dome: OPPONENT (the opponent's information)
  - Trick House: the quizzes
  - FORTREE: Right/Left
  - LILYCOVE museum: Saw it
  - Battle Tower interview: Satisfied
- **Menus that only look B-ignored.** A menu could seem to ignore B if B led straight back to it. My check for that (vbloop.py) found such menus only in the Battle Frontier.
- **The AI's B press is safe.** It presses B only once the menu accepts input (multichoice_delay is read). So a B-allowed menu is never misread as one that ignores B, and gets answered by mistake.
- **No loop.** A chat that ends in an answer still puts the person in `talked`, so the AI does not talk to him again.
- VT6-7 resolves each NO_ANSWER_MENUS id's options from the decomp's own strings, and matches them in any case. VT6-9 recomputes the chapter 1-8 census. Both pass.

**V5-1 (the top-up's look for a town's centre)**
- `known` decides the look and `where` decides the walk. This restores c41db547's look and keeps VR4-2's refusal: Round5 r1 and t2 pass.
- VT6-4 (ROUTE 106, only an unreachable centre known) gives no heal and no look, on both trees.
- **Still missing (VR6-4, MINOR, unchanged since c41db547).** A top-up that starts inside the town's gym never looks for the town's centre.

**P5-1 (the back of the gym)**
- **The ping-pong (V5-3).** From #108's raw digests: 21 entries onto the gym's map in each B run, never above row 26. Confirmed.
- **The real layouts.** From the decomp's own layouts, gym_back lands on ROXANNE's own tile (5, 2) and BRAWLY's own tile (4, 3).
- **My tests.** Both fail on the base (ping-pong) and pass on round 6:
  - VT6-2: ROXANNE's real layout.
  - VT6-1: a dark-gym model, where the eyes see a person only on the 8 tiles round the player. This shows the fix does not depend on the eyes seeing through darkness.
- **A gym already beaten** is not wired (VT6-8).
- **Later gyms (VR6-2, MINOR).** The rule does not reach the leader in MAUVILLE, FORTREE or PETALBURG. That is chapter 9 or later, and only when the gym is fully known with no sighting.
- **New defect (VR6-1, MINOR).** Once the gym's back is excluded, the same find offers "the back of the gym" on DEWFORD_TOWN (VT6-3). It is bounded, rare, and easy to fix.
- **Imprecise but unreachable (VR6-5, NIT).** `_fights_its_leader` checks that some fight is next, not that it is with this leader.

**#109, re-derived from the game's records** (vjudge2.py, from the eyes' digest of every record: map, tile, `trainer=`, party HP)

| Arm | Seed 6351 | Seed 6352 |
|---|---|---|
| A (095ea511) | 19 gym entries, highest row 12, no trainer-266 battle | 27 gym entries, highest row 26, no trainer-266 battle |
| B (round 6) | BRAWLY's battle began f954713 (+3,675 frames), 151/151 HP, from (4, 4); whiteout; a second battle began f970926 | Battle began f954706 (+3,668 frames), 151/151 HP; whiteout; a second battle began f970405 |

- All 4 runs: purity CLEAN, exit 0, L5.THIS_RUN PASS. Both arms' code digests were the same before and after the batch.
- **Order of events.** The prediction file was written at 00:44:18 and hashed at 00:44:42 (sha256 64c0009d... matches). The ledger registered #109 at 00:44:43, before the first job.
- **Seeds.** 6351-6352 appear only in #109, across 185 ledgers. 6343-6350 and 6353-6372 are free. I ran no live batch, so no seed was spent and the next free seed is still 6363.
- **V5-7.** #106's arm A has 62,157 and 47,903 lines, of which 62,147 and 47,893 have a frame, and 60,509 and 46,087 show the multichoice. Confirmed.

**Mutants**
- **The builder's set, re-run on my copy.** revert_step5: the G0 control passes and all 31 are caught as predicted, frozen tree PASS. revert_r1: the R0 control passes (630 tests).
- **My own (VM1-VM5).** I wrote and hashed the predictions before running them (predictions_v6.txt c0f7b58d...).
  - VM3 (no door-column tie-break) is caught by p5 and VT6-1, as predicted.
  - VM2 (any reached target disarms the back) survives, as predicted. That is a test gap (VR6-6).
  - VM4 (equivalent) and VM5 (decision count) survive, as predicted.
  - VM1 (always answer option 0) was also caught by q7. **My prediction missed that** (VR6-7). In the game VM1 changes nothing, because every B-ignored menu starts on option 0.

**Out of the round's scope (VR6-3)**
- N6-1 is confirmed from the decomp: DEWFORD's gym is at flash level 7 (24 px), and GRANITE CAVE B1F and B2F are dark (requires_flash).
- The eyes read people and tiles that the dark screen does not show. Under RULING 40 that is MAJOR-class, but it is older than this round.
- The lead should rule on it before chapter 7 is graded.

**Cleanup**
- verify/repo, verify/base and verify/basework are deleted. No junctions were made.
- The main sandbox counts are unchanged: plugins 43, mgba 44, roms 2.
- The main checkout's git status is clean, and the worktree is as the builder left it.
- C: has 62.1 GB free.
- Left behind: verify/ scripts and outputs (374 KB) and STATE.md.

## Chapter 6 stops, round 7 (the builder, 2026-11-07)

**Result: N6-1, VR6-1, VR6-4 and VR6-5 are fixed, and VR6-6's gaps are closed. Every gate passes.**
- Caveats:
  - Only N6-1 was checked live: 2 runs from a start built on the test side. That is development evidence, not a rate.
  - Both live runs lost to BRAWLY again (P4-1, out of scope).
- Nothing is committed (hard limit). The worktree wf_e7452923-f06-3 is at adf6c246 plus 14 modified files and 3 new ones.

**N6-1 (VR6-3): the eyes no longer see in the dark (USER RULING 40)**
- **Reproduced first.** From #109's records (repro_n61.py), 150 of 154 gym records in each arm-B run listed someone outside the lit circle, up to 12 tiles away. On adf6c246's host code, test_eyes d2 FAILS.
- **Correction.** Start D2 already has one gym trainer beaten (CRISTIAN). The gym there is at flash level 6 (32 px, 12 tiles), not level 7 (24 px). The probe measured this before the live prediction was written.
- **The fix** applies the screen's own drawing rule from the decomp:
  - `sFlashLevelToRadius` and `SetFlashScanlineEffectWindowBoundaries`, line for line.
  - The level comes from save block 1's `flashLevel` byte.
  - On a dark map, a tile outside the circle is None in the view, and the world memory does not learn it. Objects and signs outside it are not listed. `View.lit` gives the radius, and the digest shows `lit=Npx`.
  - What the AI already knows and its static knowledge (gym_back) stay.
- **Census of dark maps (pinned decomp):**

| Map | Reachable in chapters 1-8? | What the AI now sees |
|---|---|---|
| DEWFORD_TOWN_GYM | Yes | 9 to 69 tiles, by trainers beaten |
| GRANITE_CAVE_B1F, B2F | Yes, on chapter 7's way to STEVEN | 9 tiles until FLASH, then 69 |
| VICTORY_ROAD_B1F, B2F | No (endgame) | n/a |
| Three unused CAVE_OF_ORIGIN maps | No (they warp only to each other) | n/a |

- **Offline probe:** both code roots, the same savestates, the same frames.
  - CONTROL: 88 of 88 looks on lit maps are byte-identical (21 chapter 1-6 fixtures and D2).
  - FAULT, the gym entered from D2:
    - adf6c246 listed 2 people and 4 signs outside the circle, and all 165 tiles.
    - Round 7 sees lit=32, 12 tiles and nothing outside.
  - GRANITE B1F fixture: 165 tiles before, 9 now (lit=24). The live muddy-slope test still passes there.
- **Live check (#110, seeds 6363-6364, from D2):**
  - BRAWLY's battle (trainer 266) began at +3,721 and +3,766 frames (round 6: +3,675 and +3,668).
  - No gym record listed anything outside its circle.
  - People beside the player were listed.
  - Purity CLEAN.
  - All five predictions held, and the prediction was hashed first.

**VR6-1: the back of the gym is offered only on that leader's gym**
- `gym_back(gym=...)` returns nothing on any other map.
- The runner binds it to the gym the find began on.
- Reproduced on adf6c246 with VT6-3, which offers (5, 3) on the town.

**VR6-4: a top-up inside a town's gym looks for that town's centre**
- It walks out to the town first.
- It finds the town by the known way out, or else by the gym's own name.
- Only the top-up does this. A hurt party still heads for the centre it knows.
- Reproduced on adf6c246: the first goal there was 'find'.

**VR6-5: the find must be for the leader of the next fight**
- `_fights_its_leader` now needs the leader among the fight's trainers (`Milestone.fight_trainers`, from milestones.json).
- Reproduced on adf6c246: a find for ROXANNE while BRAWLY's fight is next read True.

**VR6-6: two test gaps closed**
- New tests pin that only reaching the BACK disarms it (VM2).
- New tests pin that an answer counts toward MAX_DECISIONS (VM5).
- Both pass on adf6c246 too: these were gaps in the tests, not defects.

**Mutants (predictions hashed before each run)**
- revert_step5:
  - G0 passes.
  - 39 CAUGHT: G671-G688 new; G110, G138, G412, G649, G661 and G669 re-anchored; the rest re-run.
  - G668 is REDUNDANT, as predicted.
- revert_r1: R0 passes, and CH6S18-CH6S35 are CAUGHT.
- 1,311 anchors, every one unique.
- The call-site census passes, with 11 reasoned waivers.

**Gates**
- These pass:
  - test_goals 461, kb2 126, world 139, saving 151, eyes 78, hands 57, battle 112
  - check_purity tests 30, step53_a2 34, host 37, FairnessTests 9, test_evidence 27
  - check_fairness, check_purity, call_census, check_paths, ledger --check (110 entries)
- run_regression.py was not run.

**New risks and limits**
- N7-1: a full chapter-7 walk through the dark Granite Cave floors has not been run with the new eyes. With 9 tiles of sight there, it may be slow or get stuck.
- N7-2: at the circle's rim the AI sees slightly less than the screen, never more.
- N7-3: while the gym brightens after a trainer, the eyes keep the smaller circle until the script sets the new level. The Battle Pyramid's own light radius is not modelled.

**Cleanup**
- The stage is torn down, junctions first.
- The main sandbox's counts are unchanged: plugins 43, mgba 44, roms 2 entries by rglob (modules 4461). No ai-c7s7 profiles are left.
- The base copy is deleted.
- The main checkout's git status is clean.
- C: has 58 GB free.
- Notes are in s53/ch6stops7/STATE.md.

## Chapter 6 stops, round 7: verification (the verifier, 2026-11-07)

**Verdict: CONDITIONAL PASS, with 1 MAJOR, 2 MINOR and 1 NIT.**
- The condition is the MAJOR, V7-1: people partly in the light are not seen.
- The round's main fix holds. On a dark map the eyes no longer list people or learn tiles outside the light.
- The circle matches the game's own pixel for pixel.
- The two live runs' records support the round's claims, apart from one wording point (V7-4).

**How I checked**
- I worked on a copy of the worktree (adf6c246 plus the uncommitted round).
- My predictions were written and hashed before any run: `s53/ch6stops7/verify/v_predictions.txt`, sha256 b0697aa9..., at 02:55:44.
- I did not run any live batch, so no seeds were used.

**The dark rule against the pinned decomp (731ad5b)**
- Which maps are dark, re-derived:
  - `requires_flash` is set on GRANITE_CAVE_B1F and B2F, VICTORY_ROAD_B1F and B2F, and three unused CAVE_OF_ORIGIN maps.
  - `setflashlevel` is used only in DEWFORD's gym (levels 0-7, by gym trainers beaten) and in the FLASH script (level 1).
  - The game resets the level to 0 on every lit map it loads.
- The code matches the decomp:
  - The radius table `{200, 72, 64, 56, 48, 40, 32, 24, 0}`.
  - `SetFlashScanlineEffectWindowBoundaries`, line for line.
  - `flashLevel` at byte 0x30 of save block 1.
  - The window registers: inside the circle every layer is drawn; outside it only the text layer.
- My ground-truth probe (v_probe.py: a throwaway emulator, the rendered screen and RAM) confirms the circle:
  - VP1: the game's own scanline buffer equals `flash_window` on every scanline, in all 192 samples (24 and 32 px).
  - VP2: the player's sprite is drawn at (112,56), 16x32, so the circle's centre is the middle of the player's tile.
  - VP3: there are 0 lit pixels outside the window. Shifting it one scanline either way gives 2 to 64.
  - VP4: at rest, no tile the eyes give has 0 lit pixels, and no dark tile is more than 60% lit.
- Lit maps:
  - They are unchanged by construction: `lit` is None and dropped from the record.
  - The builder's probe compared 88 of 88 looks; I did not re-run it.
- Memory and static knowledge are not wiped:
  - `absorb` only skips dark tiles.
  - The people seen earlier on a map stay remembered.
  - `gym_back` is untouched.

**V7-1 (MAJOR): people partly in the light are not seen**
- A person counts only when the middle of their feet tile is lit.
- In the gym at (6,22) the guide stands two tiles down and one left of the player.
  - 327 of the 512 pixels of his sprite are lit, and the screen shows his head and body (`verify/png/gym-s6Up-rest.png`).
  - The eyes list nobody.
- There is a ring like this at every level. Examples:
  - 24 px: a person two tiles straight down, 268 px lit.
  - 32 px: (2,0) and (0,3) are in the ring, besides (+-1,2) and (+-2,1).
  - 72 px (FLASH used): (0,5).
- At 32 px, a person two tiles to the right is not seen, but one two tiles to the left is, with the same light.
- Live, in #110: 16 records per run where the guide or the trainer BRENDEN was mostly in the light and not listed.
- The builder's N7-2 calls this "a head" or "a few pixels".
- Fix: judge a person by their head or feet tile, or by how many of their sprite's pixels are lit. Make the rule symmetric, and add tests at 24 and 32 px.

**V7-2 (MINOR): mid-step looks see one row ahead**
- During a step, the eyes centre the circle on the destination tile.
- For up to about 8 frames they list a person, and tiles, that the screen has not drawn yet.
  - 8 walking frames listed the guide with 0 lit pixels.
  - 54 of 180 walking looks gave a tile with 0 lit pixels.
- The navigator's decision looks fall at the start of a step.
- Everything seen is on screen by the end of that same step, so this is a reaction-time lead, not hidden information.

**VR6-1, VR6-4, VR6-5 and VR6-6**
- Reproduced on adf6c246's play code (`v_base.out`):
  - d2, g1, g3, h1, h2 (the gym case) and h4 FAIL; d1 and g4 ERROR.
  - The controls pass there: d3, g2, h3 and m1.
- I saw no gym back or look offered where a person would not make one, and none missing where one would.
- Two survivors (V7-3, test gaps only):
  - VM-D: the ROUTE filter in `_building_town` is unpinned.
  - VM-E: the walk out's stop on arriving in the town is unpinned, probably near-equivalent.
- My other mutants were caught: VM-A (I had predicted it would survive), VM-B and VM-C.
- The suites pass on the copy: test_eyes 78, test_goals 461, test_world 139, test_kb2 126, test_check_purity 30.

**The live check (#110), re-derived from the raw records, the decomp's gym objects and the end states**
- Registration:
  - The prediction's sha256 matches.
  - Its file was written at 02:22:59 and the runs were registered at 02:23:16.
  - Seeds 6363-6364 appear in #110 only (185 ledgers), so no spent range was re-run.
- P1: BRAWLY's battle began at +3,721 and +3,766 frames, at 100% HP, with no other battle first.
- The end states, read from end_state.ss1, show BADGE02 and BRAWLY's trainer flag unset in both runs.
- P2: in 271 and 269 gym records, the people and statues listed are exactly the decomp's whose feet tile is lit, with 0 mismatches.
- P3 to P5 hold: no `lit=` off the gym, and purity CLEAN.
- Caveat: two runs, one trajectory each. This is not a rate.

**Cleanup**
- No stage was built and there are no junctions.
- The copy is deleted. `verify/` keeps 0.22 MB of scripts, outputs and PNGs.
- The main sandbox's counts are unchanged: plugins 43, mgba 44, roms 2.
- The main checkout's git status is clean.
- The worktree is untouched.
- C: has 61.4 GB free.
- Progress notes: `s53/ch6stops7/verify/STATE.md`.

## Chapter 6 stops, round 8 (the builder, 2026-11-07)

Worktree wf_e7452923-f06-3 (wip/ch6-ch7), starting from 986a5816. Nothing is committed or staged. All work was offline; there was no live batch.

Headline, with its caveat: on a dark map the eyes now see a person by the sprite the screen draws. The circle also stays where the screen draws it while a step is in progress. This was checked frame by frame on real emulator frames from one gym walk at 32 px, plus a cave state at rest, and in unit tests. It is not a live run and says nothing about how play changes.

V7-1 (MAJOR), fixed.
- Reproduced first on 986a5816. probe8.py looked on every frame of the verifier's walk into DEWFORD's gym, which is at 32 px from D2. It measured against the game's WIN0H buffer and each sprite's drawn rectangle. In 67 of 192 dark looks, a person with at least 124 lit pixels of their sprite was not listed. The new unit tests d4 and d5 also fail on the base.
- The new rule: a person is seen when at least SEEN_PIXELS = 124 pixels of their drawn sprite rectangle are lit. The rectangle comes from gSprites and gSpriteCoordOffsetX/Y, through the existing read_symbol door.
- Why 124: it is derived, not chosen. It is the fewest lit pixels of any tile that the tile rule sees, at any flash level. So a person needs exactly the light a tile needs.
- What follows from that:
  - anyone whose feet tile is seen is still seen;
  - the ring round 7 missed is now seen (up to 72% of a sprite was lit there);
  - a grazed sprite is not seen;
  - mirror places get the same verdict.
- Tiles keep their own middle-pixel rule. Signs keep it too, because a sign is drawn as a tile. Lit maps read nothing new.

V7-2 (MINOR), fixed.
- Reproduced first on 986a5816. All 105 mid-step looks saw a tile whose drawn middle pixel was dark. In 54 looks a tile was seen with 0 lit pixels, and in 8 looks the guide was listed with 0 lit pixels.
- The fix places the circle by where the screen draws the player's tile. It uses gFieldCamera's pixel offset inside the step, with the same rule as SetSpritePosToMapCoords (step_offset). People need no shift, because their drawn sprite already includes the scroll.

V7-3 (MINOR): two tests added. The code was already correct and is unchanged.
- h2 now requires the walk out of the gym to end on arriving in the town. This catches VM-E.
- New h5: a top-up in MR. BRINEY's cottage, whose only known way out is ROUTE 104, does not look for a POKéMON CENTER on the route. This catches VM-D. With a way out to DEWFORD_TOWN instead, it looks for DEWFORD's centre (the control).

V7-4 (NIT): the round-7 evidence file is reworded. It now says that people whose feet tile is lit were listed, and that a ring of people partly in the light was not. P3 is marked "HELD as worded".

Proof:
- Unit tests:
  - test_eyes DarkTests d4, d5 and d6, plus the d3 control, which now runs with the new reads left out of the fake memory.
  - test_goals h2 and h5.
  - On the base: d4 ERROR, d5 FAIL, d6 FAIL; d1 to d3 pass.
- Real frames, with predictions hashed first (359221d3...); all five held:
  - Arm B: V71, MORE, ZERO and every tile mismatch are 0 over 192 dark looks, including 105 mid-step.
  - At rest, B drops none of A's people and adds 50.
  - The lit control is byte-identical on 88 of 88 looks over 22 states.
- Mutants, with predictions hashed first (24196844...):
  - revert_step5: G689 and G690 caught, G0 PASS (462 tests).
  - revert_r1: CH6S36 to CH6S49 caught, plus CH6S19, CH6S20, CH6S21 and CH6S31, which were re-anchored. R0 PASS (640 tests).
  - call_census since HEAD: 0 MISSING, no new waiver.
  - 1,327 anchors, all unique.

Gates on the final tree, all PASS:
- test_eyes 81, test_goals 462, test_world 139, test_host 37, test_evidence 27 and FairnessTests 9.
- check_fairness, check_purity, call_census, check_paths and ledger --check (110 entries).

Limits:
- N8-1: the count includes the sprite's own transparent pixels.
- N8-2: the tile rule's exactly-half-lit asymmetry at the widest row is kept.
- N8-3: the effect on play is unmeasured, and N7-1 still stands.

Cleanup:
- The stage was torn down with its junctions unlinked first, and base/ was deleted.
- The main sandbox's counts are unchanged: plugins 43, mgba 44, roms 2 (and modules 4461), by rglob.
- The main checkout is clean. C: has 61.3 GB free.

Progress file: s53/ch6stops8/STATE.md.

## Chapter 6 stops, round 8: verification (the verifier, 2026-11-07)

Verdict: FAIL, on V7-1 only. V7-2, V7-3 and V7-4 are confirmed.

Headline, with its caveat: the new person rule (at least 124 lit pixels of the sprite's RECTANGLE) lists people that the screen does not draw at all. The top 10 to 11 rows of every 16x32 person sprite are transparent. A person below the player has only those rows in the light. On a real frame at 32 px (D2's level), a person drawn where (0,3) is drawn is listed with 140 counted pixels and 0 drawn pixels. That frame places the guide's sprite there by a probe-only write. On real frames at 24 px, the gym guide at (-1,2) was listed with 8 drawn pixels in 50 rest-phase looks. That is one trajectory, not a rate. Round 7's rule listed none of these. This is a RULING 40 breach in the opposite direction from V7-1.

What I ran: everything offline, on a copy of the worktree without .git (986a5816 plus the builder's uncommitted round). Predictions were written and hashed before any run: v8_predictions.txt, sha256 f7aa7e79aec5f593....

- Probe (v8_probe.py), on real emulator frames:
  - three arms: the gym at 32 px from D2 (191 dark looks, 99 mid-step); the gym at 24 px, with trainer flag 574 cleared in the probe only (191 looks); and GRANITE B1F at 24 px (57 looks, with no person in them);
  - ground truth: the game's WIN0H buffer, gSprites, and the rendered screen;
  - a person's drawn pixels are the pixels that change when only that object is hidden (its ObjectEvent invisible bit, 3 frames).
- V8-1 follow-ups:
  - v8_mask.py measured the real sprite masks. Its model, built on those masks, matches the probe's measured values exactly.
  - v8_place.py checked (0,3) at 32 px on a real frame, with a control.
- v8_mutants.py: 7 mutants of my own.
- v8_heal.py: the round-7 verifier's VM-D and VM-E against the new tests.

Results against my predictions:
- VP8-1 HOLDS: in 439 dark looks, the eyes' person verdict equals my own count (RAM window plus gSprites, at least 124) every time.
- VP8-2: no listed person had 0 drawn pixels in the natural walk. Its ">= 30" part FAILED, with 8 drawn pixels (V8-1).
- VP8-3 HOLDS: no unlisted person had more than 73 drawn pixels.
- VP8-4 HOLDS: 0 tile mismatches (seen with a dark drawn middle pixel, unseen with a lit one, or seen with 0 lit pixels) in 382 looks with a standing reference. That includes 198 mid-step looks, at both 24 and 32 px. This extends the builder's evidence, which covered 24 px mid-step only in unit tests.
- VP8-5 HOLDS: on 92 lit DEWFORD TOWN looks the eyes read none of gSprites, gSpriteCoordOffsetX/Y or gFieldCamera, and called neither new function. My first census pooled 23 dark gym looks into the lit count. That was an instrument error, corrected by attributing reads per look (v8_look.out).
- VP8-6 HOLDS at rest. VP8-6b HELD: 6 mid-step exceptions (V8-2).
- VP8-7 HOLDS: 124 is the fewest lit pixels of a seen tile at rest (r 32, tile (0,-2)), from my own window.
- VP8-8 HOLDS: the gym loads at 24 px with the trainer flag cleared.

Findings:
- V8-1 (MAJOR): a person is listed when the screen draws none of them.
  - The real masks of the guide and the player start at rows 11 and 10 of their 32-row rectangles.
  - With the real mask, the model (exact on (-1,2): 162/8 at 24 px and 327/109 at 32 px) gives 0 drawn pixels for listings at (0,3) at 32 px, (0,4) at 48, (0,5) at 64 and (-2,5) at 72.
  - It gives 1 to 29 drawn pixels for listings at (+-1,2) at 24, (+-1,3) at 40 and several places at 48 and 72.
  - test_d5 asserts that (0,3) at 32 px IS listed, so the test pins the defect.
  - The claim "a person needs exactly the light a tile needs" does not hold on real frames, and N8-1 understates the problem.
  - Fix: count drawn (opaque) pixels, from the sprite frame's graphics or at least its drawn rows, and re-derive the threshold. Then flip d5's (0,3) expectation, add a real-mask FAULT and CONTROL, and re-probe.
- V8-2 (MINOR): "anyone whose feet tile is seen is still seen" holds only at rest. Mid-step, in 6 person-looks of one trajectory (1 to 4 frames each), the feet tile was seen and the person was not listed (rectangle 104-122, 61-73 drawn pixels).
- V8-3 (MINOR): my mutant VM8-A (x2/y2 dropped from _drawn_lit) SURVIVED all 81 tests of test_eyes, as predicted. The fake sprites never set x2 or y2. On real frames they were 0 for every person.

Confirmed:
- V7-2 is fixed. The circle stays where the screen draws it while walking, at 24 and 32 px, on real frames (VP8-4).
- V7-3 is fixed. VM-D is caught by h5 and VM-E by h2. R0 PASS before and after.
- V7-4: the round-7 evidence wording now says what P3 tested.
- Lit maps read nothing new (VP8-5).
- Mutants VM8-B to VM8-G were all CAUGHT as predicted:
  - VM8-B (needs more than 124) by d6;
  - VM8-C (the camera read on a lit map) by d3;
  - VM8-D (step_offset's sign flipped) by d6;
  - VM8-E (height taken from X) by d2, d5 and d6;
  - VM8-F (the window read one row low) by d4;
  - VM8-G (the X offset used for Y) by d2, d5 and d6.
- R0 PASS before and after; the whole test_eyes ran 81 OK.
- test_evidence: 25 of 27 pass in the copy. The other 2 need `git rev-parse`, and the copy has no .git (an environment limit, not a defect). The builder reports 27 OK on the worktree.

Not done:
- No live batch, and no seeds were used.
- No person was observed standing naturally at (0,3) at 32 px, because walls block that place on this walk. The 0-pixel case was shown by moving the sprite only. Every pixel counted there is the game's own drawing.

Cleanup:
- verify/repo is deleted, with 0 junctions or links found first. No stage was built.
- The main sandbox's counts are unchanged: plugins 43, mgba 44, roms 2 (rglob).
- The main checkout's git status is clean. The worktree is untouched (8 modified files and 1 new one, as the builder left it).
- C: has 62.3 GB free. verify/ keeps 0.45 MB of scripts, outputs and png8/.
- Progress file: s53/ch6stops8/verify/STATE.md.

## Chapter 6 stops, round 9 (the builder, 2026-11-07)

Headline: on the game's own frames, the dark eyes no longer list a person when the screen draws none of them. One caveat: a pixel that the map draws over the sprite (the top of a wall) is still counted. On a probe-only placement onto a wall tile, that caveat let a person be listed with 0 pixels on the screen. In the natural walk, no listed person had 0 pixels on the screen.

What changed (the worktree, uncommitted, on top of 059a65ff):
- `host/eyes.py` `_drawn_lit` counts the pixels the sprite's current animation frame draws, not its 16x32 rectangle. It returns (lit, drawn).
  - The frame is the image of the animation's current command, which the game copies into VRAM.
  - It is read from the cartridge through the existing doors. No VRAM door was added, because the framework's read_bytes has none.
  - The frame is read at the OAM size and flips, with palette index 0 transparent.
- `eyes/view.py` adds `sprite_mask`, `drawn_pixels` and `person_seen`. A person is listed when some of their drawn pixels are lit and at least `SEEN_SHARE` of them are.
  - `SEEN_SHARE` is 74/227, derived: the least lit share of a standing person whose feet tile the tile rule sees, at rest, at every level and place.
  - It comes from the guide's real frame. The player's frame gives 74/216.
  - It is a share and not a count because an item ball draws only 76 pixels.
- When the frame cannot be read, the eyes count nothing, so the AI sees less, never more. That covers affine, hidden or 256-colour sprites, OAM shape 3, and a command that is not a frame.
- `SEEN_PIXELS` is gone, and the README rows are reworded.

Reproduced first, on HEAD with probe9.py: at 32 px, the guide drawn at (0,3) was listed with 140 pixels counted and 0 on the screen.

Real-frame results on round 9 (predictions hashed first):
- Placements:
  - At 32 px, (0,3) is not listed (0 lit).
  - The CONTROL (-1,2) at 32 px is listed, with 109 counted and 109 on the screen.
  - At 24 px, (-1,2) is not listed (8 counted, 8 on the screen).
  - Flips and x2/y2 match the screen wherever nothing covers the sprite.
- Natural walk (439 dark looks, 1,058 person-looks, one trajectory):
  - No listed person had 0 pixels on the screen.
  - At rest, the count equals the screen in 158 of 158 looks.
  - Compared with round 8 on the same walk: 63 listings dropped (8 to 75 pixels on the screen), 0 added.
  - My prediction "never more on the screen at rest" FAILED as written. 6 looks two frames after a step differed by 1 to 14 pixels, because the eyes read memory one frame ahead of the screen.
- Lit control: 88 of 88 lit looks over 22 states are byte-identical to 986a5816.

V8-2 is stated and pinned, not closed. Mid-step, for 1 to 4 frames, a standing person on a tile the shifted tile rule sees can be unlisted. There were 7 such looks on the walk, with 65 to 73 of 227 pixels lit. Test d11 pins one of them at the exact count. At rest there are none.

V8-3 is fixed: test d10 sets x2 and y2. Mutants CH6S61 to CH6S63 (including the verifier's VM8-A) are caught.

Tests (DarkTests):
- d4 renamed, d5 reworded.
- New: d7 (the share, derived), d8 (the V8-1 FAULT: it fails on round 8's eyes), d9 (frame, flips and guards), d10, d11.

Mutants: 23 of 23 caught as predicted, R0 PASS, FROZEN TREE PASS. They are 14 new, 5 re-anchored, 1 with a renamed test, and 3 rerun.

Gates: all PASS. test_eyes 86, test_goals 462, test_world 139, test_host 37, test_evidence 27, FairnessTests 9; check_fairness, check_purity, call_census (19 sites, 0 missing), check_paths. All 1,342 anchors are unique.

New stops:
- N9-1: map layers and overlapping sprites are not modelled.
- N9-2: fewer people are listed than in round 8, and the effect on play has not been run.
- N9-3: the share is derived from two frames.
- N9-4: the eyes read memory one frame ahead of the screen.

Not done: no commit or staging; no live batch; PROJECT KNOWLEDGE not edited; untouched round-7 and round-8 mutants not rerun.

Cleanup: the main sandbox is unchanged (plugins 43, mgba 44, roms 2), the main checkout is clean, there are 0 junctions, and C: has 62.2 GB free. Progress: s53/ch6stops9/STATE.md.

## Chapter 6 stops, round 9: verification (the verifier, 2026-11-07)

Verdict: CONDITIONAL PASS. I found no MAJOR. The code does what the builder says. The two MINORs are a missing test and one mislabelled number in the report.

What I checked (on a copy of the worktree without .git, now deleted; the worktree and the main checkout are untouched):
- The diff of view.py, host/eyes.py and the README against 059a65ff.
  - A person is listed only when `drawn_pixels` of the decoded frame finds at least 1 lit pixel and at least 74/227 of the drawn pixels are lit. The eyes can therefore list someone with 0 screen pixels only when the frame or the place they count differs from the screen.
  - The struct Sprite offsets match the decomp: anims 0x08, images 0x0C, animNum 0x2A, animCmdIndex 0x2B.
  - The flip bits (attr1 bits 12 and 13) and the affine, hidden and 256-colour guards (attr0 & 0x2300) are right.
  - The 12 OBJ_SIZES entries match the GBA table.
  - All 245 object event graphics in the pinned decomp have tileTag = TAG_NONE, so `images` is always a valid cartridge table. On these maps the new `_rom_bytes` reads cannot raise and drop a look's objects.
- A lit map: `_drawn_lit` runs only when the radius is set. Outside the dark branch the diff changes only imports. No SEEN_PIXELS reference is left anywhere in the worktree.
- Tests on the copy: test_eyes ran 86 tests OK, and DarkTests ran 11 OK.

Mutants (predictions written and hashed first: prediction_vm9.txt, sha256 bf2362a2...):
- VM9-A drops animNum from the animation read. It SURVIVED test_eyes (86 OK) and test_host (37 OK), as predicted. Every fake sprite has animNum 0, so no test can tell the difference. This is V9-1.
- VM9-B drops animCmdIndex. It was CAUGHT, with 7 test failures, as predicted.

Real-frame data (the builder's walk, re-read rather than re-run):
- The fewest screen pixels of a listed person, 60 at gym32 s1Up after2 (0,-2), is the one-frame lag.
  - The eyes count 60 at after1 and 74 at after2.
  - From after3 on, the eyes and the screen both read 74.
- The report and N9-1 put this down to a wall. That is V9-2. No wall covering shows in the natural walk at rest; the only evidence for N9-1 is the probe-only placement.
- No listed person had 0 pixels on the screen, so the headline's claim holds.

Findings:
- V9-1 (MINOR): add a test with animNum 1, and add VM9-A to the mutant file with prediction CAUGHT.
- V9-2 (MINOR): reword the stop text and the report: the 60 is the lag (N9-4), not a wall.
- V9-3 (NIT): no test pins the OBJ_SIZES entries other than 16x32. I checked them all and they are correct.

Not done:
- No emulator run. The round asked for no live batch, and the builder's real-frame files answered what I needed.
- I did not rerun the builder's 23 mutants.
- I did not attack V8-2 (pinned) or N9-1 (documented) further. One argument, not measured: a person's head rows hold about 57 drawn pixels, fewer than the 74 needed. So a wall covering only the tile above a person cannot give a listing with 0 on the screen. N9-1 should therefore be out of reach in natural play on these maps.

Cleanup:
- The copy is deleted.
- I made no staging and no junction, and ran no emulator.
- The main checkout is clean, and the worktree is unchanged (5 modified files and 1 new zip).
- C: has 58 GB free.
- Files: s53/ch6stops9/verify/ (STATE.md, prediction_vm9.txt and its .sha256, vm9.py, vm9.out).

## Chapters 6-7, development probe 11 (2026-11-07)

This is a development probe: one trajectory per start, never a rate, never graded. It ran as ledger #111, batch probe11, with seeds 6365-6367.

**Setup.** The code was b7c11490 (stop rounds 1-9). In round 7 the eyes changed: on a dark map they now see only the lit circle the screen draws. The probe used the same starts, target and budget as #107 (probe10, round 4's code):
- starts: the three chapter-5 chain ends, C1 Story, C2 Catcher and C3 Trainer, byte-identical to #107's
- target: ch7_brawly
- budget: 1,200,000 frames, 9,000 s of wall time

The prediction was hashed and the ledger entry registered before the runs. The batch took 05:03-05:11, and all three runs ended by themselves (exit 0, purity CLEAN, L5.THIS_RUN PASS).

**From the game.**
- C1 (Story):
  - Delivered STEVEN's letter.
  - Lost to BRAWLY three times at 100% HP (Grovyle L22 and five L3-L6). After each fight the game shows a whiteout to DEWFORD.
  - Ended with 'stuck: 3 battles lost' after 167,065 frames, with no BADGE02.
- C2 (Catcher):
  - Lost its first BRAWLY fight at 100% and won its second (the badge count went from 1 to 2).
  - BADGE02 after 195,229 frames.
- C3 (Trainer):
  - Beat BRAWLY in its first fight (Marshtomp L25).
  - BADGE02 after 194,349 frames.

All three got through the dark GRANITE_CAVE_B1F/B2F without FLASH. Each crossed from the 1F (17,11) ladder side to the (35,3) side and then reached STEVEN's room.

| Start | Frames in B1F/B2F | Passes | Wild battles inside | #107 frames |
|---|---|---|---|---|
| C1 | 57,624 | 1 | 29 | 21,945 |
| C2 | 93,947 | 4 (the first three turned back; the first ended in a heal walk) | 45 | 12,811 |
| C3 | 77,029 | 1 | 34 | 6,832 |

**Versus #107.** BADGE02 came out the same on every start (C1 no, C2 yes, C3 yes). The cave crossing was 2.6 to 11.3 times slower. The prediction held in every part.

**New stops (reported, not fixed):**
- **P11-1, all three runs: the dark cave is slow.**
  - The cave records carry 'lit=24px' (2,164, 2,815 and 1,951 records; 0 in #107).
  - The explorer steps from one one-tile frontier to the next: 255, 234 and 235 frontier decisions, against 15, 13 and 14 in #107.
  - The go goal toward STEVEN ran out its 9,000-frame budget inside the cave 4, 6 and 5 times (1, 1 and 0 in #107).
  - This is not an A/B: the seeds and rounds 5-9 also differ.
- **P11-2, C2: 'lost' decisions in the cave.** They targeted leftover tiles on PETALBURG, OLDALE, ROUTE 103 and ROUTE 104, and the run took one ladder up and down twice (about 400 frames).
- **P11-3, C2: a detour after a heal.** It spent about 17,900 frames looking around DEWFORD, ROUTE 106 and ROUTE 107 before going back into the cave.
- **P4-1 is unchanged:** the Story party still loses to BRAWLY at full HP.

**Files.**
- Evidence: ai_player/evidence/2026-11-07-ch6-stops-development-probe-11.txt in worktree wf_e7452923-f06-3.
- Tools and records: s53/ch6probe11/ (arms11.py, judge11.py, judge_probe11.json, judge_107.json, STATE.md).

**Cleanup.** The world.jsonl files (52-61 MB) were deleted after judging. The stage was torn down with the junctions unlinked first. The main sandbox counts are unchanged (plugins 43, mgba 44, roms 2, modules 4461). The main checkout is clean. In the worktree, ledger.json and the new evidence file are uncommitted (no commit, no staging). C: has 62.5 GB free.

## Chapter 6 stops, round 10 (the builder, 2026-11-08)

All three findings from round 9's verifier are closed. I changed only tests and wording: the AI's code is unchanged, and the diff to view.py is a comment.

V9-1 (MINOR), closed:
- Before this round, no test set a sprite's animNum (the animation it is playing).
- The fake cartridge now has a second animation, animation 1: FRAME(1), FRAME(0), FRAME(2), END.
- The new test d12 puts four people on (0,1) at 24 px:
  - animation 1, command 0: the guide is drawn, 227 of 227, and he is listed;
  - animation 1, command 1: nothing is drawn, and he is not listed;
  - two controls on animation 0.
- If the code read animation 0 instead, the first two would swap.
- The verifier's mutant VM9-A (renamed CH6S64) is now CAUGHT, as predicted, by d12 and d14.

V9-2 (MINOR), confirmed and reworded:
- I re-read round 9's walk data (pB_walk.jsonl) without running the emulator.
- Both at-rest looks where the screen drew fewer pixels than the eyes counted are the one-frame lag (N9-4):
  - gym32 s1Up after2 (0,-2): the screen drew 60. The eyes counted 60 one frame earlier, and the next frame drew 74.
  - gym24 s4Up after2 (-1,0): the screen drew 224. The eyes counted 224 one frame earlier, and the next frame drew 225.
- Over the whole walk, the screen drew fewer than the eyes in 74 person-looks:
  - 71 equal the eyes' count one frame earlier (the lag);
  - 3 do not. All three are walk0, the first frame of a step, at 2 to 12 pixels fewer. The lag does not explain them, and nothing shows them to be walls.
- So no wall was measured covering a person in the natural walk. The only evidence for N9-1 is the probe-only placement.
- view.py's limits comment now says this.
- Nothing in the worktree's ai_player/evidence/ or docstrings said 'wall' for the 60. The wrong wording is only in round 9's build_result.json and in the CH6-CH7 report. Corrected text for the lead to use:
  - P9-1: "0 listed people at 0 screen pixels (the fewest, 60, is the one-frame lag N9-4: the next frame drew 74)."
  - N9-1: "In the natural walk, no wall was measured covering a person. The two at-rest looks where the screen drew fewer were the one-frame lag. Of 74 such looks in the whole walk, 71 were the lag, and 3 were on a step's first frame, unexplained. The only evidence for this limit is the probe-only placement onto a wall tile."

V9-3 (NIT), closed:
- The new test d13 checks OBJ_SIZES against the game's own table, sOamDimensions in src/sprite.c, transcribed from the pinned decomp.
- The new test d14 runs a 16x16 item ball through the host:
  - OAM shape 0, size 1, centerToCornerVec (-8,-8), 76 drawn pixels;
  - on (0,1) at 24 px it is listed, with 76 of 76 pixels lit.
- Mutant CH6S65 reads 16x16 as 8x16. It was CAUGHT by d13 and d14.
- Mutant CH6S66 gives the horizontal 64x32 entry the size 32x64. It was CAUGHT by d13.

Test helper: host_view gains three optional settings, 'anim', 'oam' and 'corner'. With the defaults, tests d1 to d11 run exactly as before.

Proof:
- I wrote and hashed the predictions before the run: prediction_mutants10.txt, sha256 656dfa048362f80b...
- revert_r1 ran the R0 control and the 3 new mutants:
  - R0 CONTROL PASS (640 tests);
  - 3 of 3 CAUGHT as predicted;
  - FROZEN TREE PASS.
- test_eyes: 89 OK. test_evidence: 27 OK.
- Mutant anchors: 1345, all unique. The call-site census since HEAD: PASS.

Worktree (no commit, no staging):
- Modified: ai_player/gates/test_eyes.py, ai_player/eyes/view.py (comment only), ai_player/gates/revert_r1_mutants.json (CH6S64 to CH6S66).
- New: ai_player/evidence/trees/09d458e747de24ac.zip, revert_r1's tree snapshot, as in rounds 8 and 9.
- The main checkout is untouched.
- My files are in s53/ch6stops10/: STATE.md, lag_check.py and .out, lag_all.py and .out, mutants10.py, prediction_mutants10.txt and its .sha256, mutants10_r1.out, gates10.py, gates/.

Not done:
- No emulator run.
- I did not look further into the 3 step-start looks the lag does not explain.

## Chapter 6 stops, round 10: verification (the verifier, 2026-11-08)

Verdict: PASS. I found nothing to fix.

What I checked (worktree wf_e7452923-f06-3 on f299a1e7, uncommitted; I copied it without .git, worked on the copy, then deleted the copy):

The AI's behaviour is unchanged:
- The diff touches view.py, test_eyes.py and revert_r1_mutants.json, plus a new untracked tree snapshot zip. host/eyes.py has no diff.
- Every changed line in view.py is a `#:` comment.
- In test_eyes.py, the host_view defaults give the same bytes as before. The sprite's y is top + 32 + (-16) = top + 16, as it was. The corner bytes are still 0xF8 and 0xF0. animNum @0x2A defaults to 0. Animation 0 and its frames are unchanged. Animation 1 and the ball frame are only added.

The tests pass on the tree and fail on their mutants. I hashed my predictions before any run: s53/ch6stops10/verify/prediction_verify10.txt, sha256 81bd680b2009091d...
- Unmutated tree: test_eyes ran 89 tests, OK.
- VM9-A (CH6S64, `+ 4 * sprite[0x2A]` dropped): CAUGHT by exactly d12 and d14, as predicted. In d12, guides 1 and 2 swap. In d14, animation 0's command 2 is END, so the ball counts nothing.
- CH6S65 ((0,1) read as 8x16): CAUGHT by exactly d13 and d14, as predicted.
- CH6S66 ((1,3) given 32x64): CAUGHT by exactly d13, as predicted.
- Each mutant's edit matched its file exactly once.

d13's table is the decomp's own:
- The test's transcription equals src/sprite.c sOamDimensions32 / sOamDimensions in the pinned decomp, lines 220-242: square, then horizontal, then vertical, indexed by SPRITE_SIZE.
- d14's OAM bits (attr0 0x0000, attr1 0x4000) are shape 0, size 1, which is 16x16.

The V9-2 wording matches round 9's pB_walk.jsonl. I re-read it with my own script:
- The fewest screen pixels of any listed person in the whole walk is 60: gym32 gym-s1Up-after2 (0,-2), eyes 74 lit, at rest.
  - The eyes counted 60 on the frame before (after1).
  - The next frame (after3) drew 74.
- Exactly two at-rest person-looks drew fewer than the eyes counted: that one, and gym24 gym-s4Up-after2 (-1,0) at 224 of 225. The frame before had eyes 224, and the next frame drew 225.
- So the comment's claims hold: no wall was measured covering a person at rest, and the only evidence for limit (2) is the probe-only placement.
- The builder's counts also match the records: 74 fewer-looks, 71 explained by the lag, and 3 on a step's first frame (walk0) that the lag does not explain.

Not checked:
- I did not re-run test_evidence, the anchors census or revert_r1's full R0 control.
- I did not check whether the item ball really draws 76 pixels in the game. The test only needs its own mask's count.

Files: s53/ch6stops10/verify/ holds copy_tree.py, run_mutants.py and run_mutants.out, wording_check.py, and prediction_verify10.txt with its .sha256. The copy is deleted. The worktree and the main checkout are unchanged (the main checkout still shows only its cost-ledger.jsonl change).

## Boss preparation BP-1 (the builder, 2026-11-09)

BP-1 is built in worktree wf_e7452923-f06-3 on 18c3d51b. It is uncommitted and nothing is staged. The spec was followed except where listed below. The offline proof holds. The live A/B shows the plan does not yet do what the spec intended: the raise is spent long before its target.

Reproduced first, on 18c3d51b. Today's training rule calls C1 ready for BRAWLY (Story target L20, strongest L21-22). In #111's C1 record all six members were sent against MACHOP in each of three fights, and each fight was lost (gBattleOutcome 2).

What was built:
- The readiness verdict (brain/bossprep.py): a deterministic duel scored with the battle brain's own move_value and rough_share both ways. It covers the verdict powers, exact fixed damage, Focus Punch, held berries (RULING 44) and full-HP members.
- The projection by evolution and level-up moves.
- The options at cost L^2-l^2 and one draw from a new <seed>:bossprep stream.
- The raise goal and runner, with the trainee led first by a new gated party-order hand.
- The M4 trainee rest, the M5 budget and the after-loss rule.
- The record, persisted in game memory.
- The loaders seasoned.py and atlas.boss_party, gated by check_fairness.

The plan is acted on only for BRAWLY, by Story and Catcher runs, and only when that fight is the next NAMED fight. This guard is mine: the spec's next-boss rule alone would act in chapter 5.

Offline proof:
- test_bossprep: 54 tests, each rule with a FAULT and a CONTROL arm.
- revert_bossprep: predictions hashed before each run. Final run: 35 mutants CAUGHT, 2 REDUNDANT offline, and both of those killed live by T10.
- The re-anchored older mutants were caught again.
- 21 of 21 gates exit 0.
- The spec's section-2 numbers rested on an accidental tie-break by move name. The shipped rule (the faster move on a tie, the worst case) moves five cells: Wurmple's target becomes 19 with typical stats and 20 with the real summary stats. A fault arm reproduces every spec number.

Live, one trajectory per seed and arm, never a rate:
- The parent never earned BADGE02: 0 of 6 runs, 18 BRAWLY fights lost.
- Round 1 (#112) found a bug in my raise watch. It read a battle's lead on the first look, where the game still holds the previous battle's battler, so false "not leading" reads spent every raise's budget. It is fixed, tested and mutant-killed.
- Round 2 (#114), the fixed code: the plan was made on 3 of 3 runs, and the trainee led all 48 raise battles. The raise was spent on all three at 63-92k frames: stalls twice, no grass within reach once. The trainee met BRAWLY as Cascoon L9, Dustox L10 and Dustox L10. BADGE02 1 of 3. In that win the records put the trainee on the field when MACHOP's bar reached 0 (who knocked a foe out is not read), but Grovyle was L24 against the parent's L22, so the win is confounded: by B's longer play after the spent raise, not by the leaks (they gave a tenth of it) and not by training (none ran). (Corrected 2026-11-11, round 2, V-M2.)

New stops:
- 12 stalls at L4, each a session of +0 EXP with the trainee at 1/18 HP: V-M1's loop (no heal between a session that ended "the trainee is low" and the next raise), not the session length. (Corrected 2026-11-11, round 2, V-M2.)
- The failure cooldown let the story sail away from the grass.
- A spent plan leaves the trainee leading: a Cascoon L9 led three lost fights.
- B's longer play after the spent raise raised Grovyle; the leaks gave a tenth of it and no training goal ran. (Corrected 2026-11-11, round 2, V-M2.)

The chapters 1-5 replay control (#113, #115) matched the parent's decision streams in 6 of 6 pairs, with equal frames, marks and parties. The fault arm diverged in both rounds. End-state md5 cannot be compared, because the launcher's game clock is the host's.

Evidence: ai_player/evidence/2026-11-09-bossprep-bp1-live-ab.txt and 2026-11-09-bossprep-REVERT.txt. Ledger #112-#115. Seeds 6371-6382 spent. The stage was cleaned. The main sandbox counts are unchanged (modules 4461, plugins 43, mgba 44, roms 2), and the main checkout is untouched.

## Boss preparation BP-1: verification (the verifier, 2026-11-09)

Verdict: FAIL. The readiness verdict, its numbers, the scope guard and the chapters 1-5 invariance all hold. The raise loop has a bug, and two of the builder's live explanations are not supported by the records.

What I re-derived, without relying on the builder's own scripts or summaries:
- BRAWLY_1 in the pinned decomp (`src/data/trainer_parties.h:3391-3413`) equals bosses.json and boss_party: MACHOP L16, MEDITITE L16, MAKUHITA L19 with a Sitrus Berry (holdEffectParam 30 in items.h).
- I recomputed C1's numbers with a separate duel (verify/v_c1_decomp.py). Moves, types, the type chart, evolutions and learnsets are parsed from the decomp; only learn_choice and FIXED_POWER are imported. Under the shipped tie-break (the faster move):
  - C1 at its fight is NOT READY, with MACHOP at 0.25.
  - C2 at L23 and L24 is CLOSE, with MAKUHITA at 0.49.
  - C3 is READY at 0.58.
  - Dustox L18 beats MACHOP with 21 of 53 HP left.
  - The options are Wurmple L19 (352), Grovyle L30 (459) and Shroomish L27 (704). Poochyena and Seedot never get there, and Cascoon is not eligible.
  - With a tie-break by move name, the same duel reproduces the spec's section 2 exactly: Wurmple L18 (315), Shroomish L24 (551), Poochyena L30 (864), MAKUHITA 0.35. The builder's tie-break deviation is real.
- The scope guard acts only from ch6_briney_house on. The spec's next-boss rule alone would act at all seven chapter-5 milestones, so the builder's next-named-fight guard is needed. Offline (V5), Story and Catcher choose the same goal as with ACT_ON empty at all 25 non-optional chapter 1-5 milestones.
- The live control: I compared the kept logs line by line myself. A equals B in all 6 pairs; only paths, ids, timing, 3 extra records and one set-ordering log line differ. F differs. The pairs cover chapter 1 to the Pokedex and chapter 5 from after ROXANNE, not chapters 2-4.
- The game's flags, from the launcher's after-truth:
  - A earned BADGE02 in 0 of 6 runs.
  - B round 1: 6371 yes, 6372 yes, 6373 no.
  - B round 2: 6377 no, 6378 no, 6379 yes.
- Seeds 6371-6382 appear only in the builder's ledger (#112-#115). The prediction files were hashed at 07:53 and 08:37, before the batches began at 08:07 and 08:38, and the hashes equal the ledger's bounds_sha256. Seeds 6365 and 6337 were not re-run.
- The builder's 37 mutants, re-run in my copy: P0 PASS, 35 CAUGHT, 2 REDUNDANT.
- Gates in my copy: 19 of 21 exit 0. test_hands and test_evidence fail only on git-provenance tests, because my copy has no .git; in the builder's worktree run both are OK.
- The eyes change touches only the field menu's SWITCH: the decomp sets PARTY_ACTION_SWITCH only in CursorCb_Switch.

MAJOR 1. The raise never heals a trainee stopped at under a third of its HP.
- After a raise session ends on "the trainee is low", the next goal is another raise, with no heal in between: 3 times on 6377, 10 on 6378 and 11 on 6379.
- The Wurmple at 1/18 HP runs from every battle and gains 0 EXP. These are the 12 stalls that spent the budget on 6378 and 6379.
- Reproduced offline, with predictions hashed first: with the plan active and Wurmple at 1/18 or 5/18, the next goal is raise. CONTROL: fainted gives find_center; healthy gives raise.
- Cause: goals.py's `hurt` looks at the whole party's HP and its strongest member, never at the trainee. trainee_rest stops the roam, but nothing heals the trainee, although the spec says "stop and heal".

MAJOR 2. The records do not support the builder's explanations.
- The trainee was L4 in every stall session, not "about L5-10". When the plan was spent it was L5, L4 and L4; it reached L9-L10 only afterwards, by leading the story's own battles.
- There was no step-5 training after the spend: the B runs have 0 train goals.
- Leaked raise battles gave Grovyle 251 EXP on 6379. By my estimate (Medium Slow growth, not looked up) it needs about 3,750 for L21 to L24. Its extra levels came from B's longer play after the spend: 22-23 heal goals against A's 1.
- The confound stands, but this changes the remedy.

MINOR findings:
- On the party's side, fixed damage ignores immunity. A Night Shade user against a Normal-type boss Pokemon is scored at 22 points a hit and READY, where the right verdict is NOT READY. BRAWLY is not affected, but the logged verdicts that calibrate BP-2 are.
- The special move powers (Low Kick 60, multi-hit) apply to the boss's moves only. The party's own Low Kick is weighed at power 1, and Double Kick as one hit.
- Test gaps: the raise runner's frames and stalls counting can be deleted, and state.base switched to state.active, with all 54 tests still passing. My 8 mutant predictions all held. The active personality drifted to Trainer mid-raise on 6379, so the base rule matters live.
- A spent plan leaves the trainee first. The re-lead on a done plan has no limit from reorder_fails. The done path never ran live.
- On 6379 MAKUHITA did not fall to Poochyena: Poochyena took no turn, so "fell to Poochyena" is only who was on the field. In the same fight the battle brain switched the Dustox out against MEDITITE by typing, against the verdict's model.

Next: fix MAJOR 1 with a FAULT/CONTROL test and a mutant. Correct BP1-L1 and BP1-L4 and the report. Then repeat the live A/B on new seeds from 6383 (free in every ledger).

Evidence (scratch, s53/bp1/verify): STATE.md, v_c1_decomp.py, v_tests.py with v_predictions.txt (sha256 50140d07), v_mutants.py (sha256 c0596f31) and v_mutants.out, v_raise_seq.py, v_goalcount.py, v_control.py, v_ledger.py, gates_out.txt.

Clean-up: the verifier ran no live batch and spent no seed. The copy was deleted (there were no links inside it). The worktree's status is as it was at the start. The main checkout is clean, and the main sandbox counts are unchanged (modules 4461, plugins 43, mgba 44, roms 2). 72 GB free.

## Boss preparation BP-1, round 2 (the builder, 2026-11-11)

Built on branch wip/ch6-bp1 (worktree wf_e7452923-f06-3, HEAD 69ce148e). Nothing is committed. This round implements the raise as USER RULING 59 describes it: "some mix that makes logical sense" of switch-training, the trainee's own winnable fights, and healing at a POKéMON CENTER or with a Potion. It follows the spec ai-research-notes/2026-11-09-BOSS-PREP-BP1-RAISE-SPEC.md.

**Reproduced first.** V-M1 on 69ce148e: the plan is active and Wurmple is at 1/18 or 5/18. The next goal was "raise", and a session that ended "is low (5/18)" was followed by another raise (7 of 7 predictions, hashed first).

**What was built.**
- **The experience rule**, as the pinned decomp states it (Cmd_getexp, gSentPokesToOpponent; checked in the decomp): every member sent out and still standing shares evenly, and a member switched out keeps its share.
- **In a raise battle**, the trainee leads:
  - it fights only when fight_safe says it wins in 3 hits or fewer and keeps a third of its HP;
  - otherwise it is switched out once, on turn 1, for a partner that wins safely;
  - a later rescue switch is allowed, and so is a run;
  - the replacement after a faint is never the trainee while another member can fight, and "Use next POKéMON?" is answered NO when only the trainee is left.
- **Between battles**, a trainee under a third (and, my addition, a knock-out partner under half) makes the party rest. A centre is used when one is 2 links away or nearer; when it is farther, a Potion from the bag is used through the new field-item hand. The raise never begins under the floor.
- **The raise map** is the highest one the partner clears with 5 levels to spare. Each map has its own failure cooldown.
- **The budget** counts the frames of heal goals, and a stall now means "no EXP gained". New record fields are counted.
- **When the plan ends** (V-m5), it settles the lead. A spent plan re-judges the lead and gives the usual lead back unless the trainee's verdict is strictly better. A done plan's re-lead is bounded.
- **V-m1**: the party's fixed damage now scores 0 against an immune type.
- **V-M2**: the round-1 sentences are corrected in the evidence, the build result, the report section and ledger #113/#115.

**Tests.** test_bossprep has 114 tests, covering R1-R9 plus PartnerWornTests and LearnerTests, each with FAULT and CONTROL arms. FieldItemTests are in test_hands. Mutants: 38 new ones, with predictions hashed before each run. The final run gave P0 PASS and 73 CAUGHT plus 2 REDUNDANT (live-only), as predicted. On the final tree all 21 gates exit 0.

**The discriminator found the spec's seeds unusable.** 6383, 6384 and 6385 all draw "raise Grovyle L21 -> L30". The near-best set holds Wurmple L20 at cost 391 and Grovyle L30 at 459, within the cutoff of 460.0, so about half of all seeds plan to raise Grovyle. That is the spec's STOP condition. I used new seeds whose offline draw is the spec's Wurmple plan. The A/B below is therefore conditioned on that plan, and the Grovyle branch is untested.

**Live pre-checks** (#117, seed 6390; #116 is VOID because of a bug in my own probe):
- P1: turn 1 switched to Grovyle. Wurmple +23 and Grovyle +23 against a Poochyena L6, which is E 47 from the decomp's yield 55, halved, read from the game's party. Slot 0 after the battle was the trainee. Both fault arms failed as predicted.
- P2: a Potion raised Grovyle from 54 to 57 (min(20, missing)), and the count fell from 8 to 7. Its control and fault arms behaved as predicted.

**The first A/B found a bug (#118, seeds 6397-6399).** The raise worked as designed:
- switch-trained on the first battle in 3 of 3;
- 70-72 switch-trained battles;
- every low ending healed before the next raise;
- 63 of 63 EXP pages equal to E/2.

But all three B runs got stuck before BRAWLY. The trainee, switched out, reached Dustox L13 and was asked to learn GUST. The battle skill had lost the page naming the learner (its 40-page window fills with partial prints), took Grovyle on the field for the learner, and looped forever on "Stop learning GUST?". This bug dates from step 4 and was exposed by switch-training. I reproduced it offline (4 of 4 predictions), fixed it in skills/battle.py, tested it and killed it with mutants. The result is INCONCLUSIVE for the badge.

**The A/B after the fix (#120, seeds 6400-6402).**
- A (no plan) earned BADGE02 in 0 of 3 runs, losing 9 BRAWLY fights with Grovyle L22.
- B2 earned it in 3 of 3, each on its first fight with BRAWLY.
- The raise was spent on frames (450,784 to 464,737) after 123-130 battles.
- The trainee met BRAWLY as a Dustox L15 in all three runs, and GUST was learned by the right Pokemon.
- The settle gave Grovyle the lead back, so Grovyle led every fight.
- By the last move before each bar read 0, the trainee knocked out 2, 2 and 3 of BRAWLY's 3 Pokemon.
- B2's Grovyle was L24 against A's L22: A + 2, exactly the pre-registered bound.

By the spec's reading rule, the raise changed the outcome on these trajectories. The caveats: the result is conditioned on the Wurmple plan; the partner's +2 levels are a confound at the edge of the bound; and these are development runs, one trajectory per seed, so this is not a rate.

**The chapters 1-5 replay control.**
- #119: B's decision streams were identical to 69ce148e's in 3 of 3 pairs.
- #121, after the fix: identical in L1 and C1L4. C2L4 differs at record 1,051, where one map change took 11 frames instead of 10 with identical AI inputs before it. I read that as the host clock, and it is a prediction miss as worded.
- The fault arms diverged in both controls.
- Coverage: chapter 1 to the Pokedex, and chapter 5 after ROXANNE. Chapters 2-4 are covered only by the guard, offline.
- Purity was CLEAN in 26 of 26 launches.

**New stops:**
- the Grovyle plan branch;
- Grovyle at A + 2;
- the settled lead goes back to Grovyle;
- the shift question's context rests on the same 40-page window;
- the potion goal, E2 and E3 have not run live.

**Evidence:** ai_player/evidence/2026-11-11-bossprep-bp1r2-live-ab.txt and 2026-11-11-bossprep-REVERT.txt. Ledger #116-#121. The run book is s53/bp1r2/STATE.md.

**Clean-up:** the stage was removed with its junctions unlinked first, and 162 MB of outputs were deleted. The main sandbox counts are unchanged (modules 4461, plugins 43, mgba 44, roms 2). C: has 71.5 GB free, and the main checkout is clean.

## Boss preparation BP-1, round 2: verification (the verifier, 2026-11-11)

**Verdict: CONDITIONAL PASS.** The round's main claims re-derive from the game's records:
- the experience rule;
- switch-training that never lets the trainee be hit;
- V-M1 closed;
- the A/B win on the builder's seeds.

Two MAJOR defects in the trainee's safety, which is the point of USER RULING 59, must be fixed and proven before the branch is merged:
- the raise's run mode lets the trainee faint (V2-M1);
- the trainee leads every travel battle of the plan, including the walk to heal it (V2-M2).

Neither defect is in the builder's evidence. These are development runs: one trajectory per seed, never a rate.

**What I checked, and how**

The work was done in a copy of the worktree without .git (`s53/bp1r2/verify/repo`, deleted afterwards). The run book is `s53/bp1r2/verify/STATE.md`.

- **The experience rule**, re-read in the pinned decomp: `Cmd_getexp` in `src/battle_script_commands.c:3255-3454`, and `Reset`/`Update`/`OpponentSwitchInResetSentPokesToOpponentValue` in `src/battle_util.c:913-958`.
  - E = expYield x level / 7, in integer arithmetic.
  - Every member that was sent out and has HP shares it, E / n. A fainted member gets nothing and is not counted.
  - A member switched out keeps its bit, so it keeps its share.
  - The spec reads this correctly.
- **E/2, a second path.** `exp_check.py` reads the yields directly from `species_info.h`. On the kept `.battles.json` extracts:
  - B2's switch-trained two-member gains equal E/2 in 82 of 82, 89 of 89 and 83 of 83 battles;
  - own fights give the full E (47, 40 and 38 battles).
- **Switch-training never hurt the trainee.** It lost HP in 0 of 491 switch-trained battles over the 6 B runs (`trainee_hits.py`).
- **V-M1 closed** (`vm1_check.py`):
  - B2: 5, 5 and 6 sessions ended low or worn, and each was healed before the next raise.
  - B: 6, 5 and 4, the same.
  - 0 sessions began under a third.
- **The A/B, re-read** from the extracts and the launcher's after-truth flags:
  - A: 0 of 3 BADGE02. Grovyle was L22 at all 9 first records.
  - B2: 3 of 3 BADGE02, each on its first BRAWLY fight.
  - The trainee was a Dustox L15 at the first record in all 3.
  - Grovyle was L24, which is A + 2, exactly at the bound.
  - Knockouts, by who was on the field and the last decision: the trainee made 2, 2 and 3. On 6401, Poochyena took MAKUHITA.
  - Grovyle led every win and fainted early: on 6400 after MACHOP, on 6401 and 6402 before MACHOP fell. So the +2 levels did not carry the fights.
  - E1's re-judge, rebuilt offline with typical stats: Grovyle leading gives CLOSE, Dustox leading gives NOT READY. That is not a tie.
- **Seeds.** `seed_audit.py` read 187 ledgers. Each seed of 6383-6386, 6390-6393 and 6397-6402 is covered by exactly one entry, #116-#121, and only in the round-2 worktree's ledger.
  - Every prediction file's sha256 equals its ledger `bounds_sha256`.
  - Every prediction's mtime precedes its launch: ab 08:04:59 before 08:05:35, ab2 08:50:21 before 08:50:57.
  - Choosing seeds by their offline plan draw is disclosed. It conditions the result on the Wurmple plan and does not bias arm A.
- **Controls**, from the kept `.stream.json` files:
  - #119: 3 of 3 identical.
  - #121: L1 and C1L4 identical.
  - #121 C2L4: all 50 differing records differ only in frame numbers inside the reasons. The decision sequence is identical throughout, so the builder's reading is better supported than it says.
  - Purity was CLEAN in 26 of 26 launches.
- **Gates on the copy.** 19 of 21 exit 0. The only failures are test_hands ProvenanceTests and test_evidence KeepEarlier/Snapshot, both on `git rev-parse` because the copy has no .git. The builder's worktree logs show both OK.
- **Mutants.**
  - The builder's mutants, re-run (hash 09e87755): 73 CAUGHT plus 2 REDUNDANT of 75, PASS.
  - My 19 mutants (`vmutants.py`, sha256 8b3a7060..., hashed first): 11 CAUGHT and 8 REDUNDANT, as predicted.
  - Ruled out: a hidden-state read (check_fairness PASS; `fight_safe` uses the bar, level, species, static learnsets and typical stats), bot code in the AI's play, and an unbounded raise or plan flip-flop (the raise was spent on frames at 450-465k; spent is final; the settle is bounded).

**V2-M1 (MAJOR): the raise's run mode.**

The builder's addition `partner_worn` rests the party only when the partner is under half its HP. `raise_partner` takes a partner only when it keeps a third of its max HP after the worst case. So a Grovyle at 29-34/57 is "not worn" and also "not a partner" against Nincada L7, Taillow L7-8 and Skitty L7-8, which are 22% of ROUTE116's land slots. The raise then runs.

In the run mode, the battle brain answers every refused escape with "run again", up to MAX_RUN_TRIES (6). There is no rescue in that mode, so the slow trainee stays on the field under its floor.

Live, #120 6402: Wurmple at 12/23 against Nincada L7, and Cascoon at 14/26 against Taillow L7. Each had 3-4 refused runs, then fainted. In all, B2 had 25 raise run battles: the trainee was hit in 4 and fainted in 2.

Reproduced offline: 6 of 6 predictions held (c93b79cc..., hashed first). No test plays a later turn of the run mode; my mutant `run_no_retry` was REDUNDANT.

Fix:
- rescue to the best healthy member that can win, once a run is refused or the trainee is under its floor;
- make the rest line match the partner's safety against the map's top slot;
- add test R3n and a mutant for each;
- predict 0 trainee faints in raise battles in the next live check.

**V2-M2 (MAJOR): the trainee leads every other battle of the plan.**

The trainee is kept in slot 0 between sessions (spec section 1.3). Round 2's heal walks therefore lead with it. #118 6397 is the clearest case:
- the heal goal said "the trainee Wurmple L5 is low (3/21)";
- on the walk it led against a Poochyena L6;
- 2 runs were refused, and it fainted.

The final code is unchanged on this path. In all, there were 5 trainee faints in travel battles over the 6 B runs:
- 6400: on a heal walk at 11/23, where the travel brain fought a Taillow L6;
- 6401, 6397 and 6399: on pick_ups;
- 6397: the heal walk above.

Fix: while a plan is active, either switch the trainee out on turn 1 of a non-raise wild battle (at least under its floor), or restore `lead_before` between sessions. Add FAULT and CONTROL tests and a mutant, and count these faints live.

**Minor findings**
- **V2-m1:** the headline ("fights only the battles it wins safely") and the evidence leave out the 7 faints, the rescue that never fired live (0 in 6 runs), and that P2 healed Grovyle +3 rather than a low trainee.
- **V2-m2:** "chapters 2-4 by the guard only" does not hold for the `skills/battle.py` learn fix, which has no guard. By my reading it changes play only where the old code named the wrong learner. Still, no chapters 2-4 replay was run, and neither was `run_regression --full`.
- **V2-m3:** eight rules have no offline test: `partner_any_hp`, `learns_now_any`, `potion_ignores_heal_line`, `run_no_retry`, `settle_any_lead`, `use_on_no_pid_check`, `learning_any_move` and `settle_while_hurt`.

**Nits**
- **V2-n1:** some tests need .git. `FieldBagModel` uses up a Potion on a full member, which the game refuses.
- **V2-n2:** #121's C2L4 is the same decisions throughout, one frame late.

**Conditions for the merge**
1. V2-M1 and V2-M2 fixed, each with FAULT and CONTROL tests and mutants (predictions hashed first).
2. The evidence corrected per V2-m1 and V2-m2.
3. A live re-check on NEW seeds (6403 and up are free; check each ledger again) that counts trainee faints in raise and travel battles from the records.

The Grovyle-plan branch (about half of all seeds), the potion goal inside a raise, and E2/E3 stay untested live, as the builder reported.

**Housekeeping**
- I ran no live batch. The kept records and the offline reproduction settle every finding, and no seed was spent.
- I made no junctions. The 582 MB copy was deleted.
- The main sandbox counts are unchanged: modules 4461, plugins 43, mgba 44, roms 2.
- The worktree status is unchanged (13 modified, 4 new, 2 archive folders). The main checkout is clean. C: has 67 GB free.

The verifier's scripts and outputs are in `C:/Remote Projects/_ai_lab/s53/bp1r2/verify/`: `trainee_hits.py`, `repro_m1.py`, `vmutants.py` and `vmutants_run1.out`, `exp_check.py`, `stream_diff.py`, `brawly_read.py`, `seed_audit.py`, and `STATE.md`.

## Boss preparation BP-1, round 3 (the builder, 2026-11-11)

This round was resumed after a cut. A first builder started at 10:22 and was stopped by a usage limit at about 11:20. Its detached live chain (pid 43892) kept running and finished at 12:04. A resumed builder took over at 11:54. It relaunched nothing and did not change the code. It checked the worktree against the frozen stage: the play digest 360ff20c and the provenance digest 6701eab79b5bf870 are unchanged since 11:01, and only gates/ledger.json differs, holding the chain's own entries. It then judged the batches, ran the full lane and the final gates, and removed the stage. The run book is s53/bp1r3/STATE.md. Nothing is committed: the worktree sits at c5146e53 with the round's edits uncommitted.

**What was built (D1-D6, by the first builder).**
- **D1 (V2-M1).** There is now one partner line, `bossprep.partner_fit`: half its HP plus a safe win. The battle's turn-1 partner and the raise's rest line both use it, and the rest line now checks every wild species on the raise map (the new static fact `seasoned.land_slots`). `fight_safe` gains a "keep" setting; 0 means "can it win, still standing", the rescue's question. In a raise battle, a refused run or a trainee under its floor is answered with a rescue (`rescue_member`): the healthiest member that can win. When the trainee is under its floor and nobody can win, the rescue falls back to any member that can come in.
- **D2 (V2-M2).** While a plan is active, the goal runner tells the battle brain whom to protect, in every goal except the raise and the boss fight's own talk. The trainee is switched out on turn 1 when it is under its floor, or in a wild battle when it would not win safely. On a later turn under the floor it is rescued.
- **D3.** Tests and mutants for run_no_retry, settle_any_lead, use_on_no_pid_check and learning_any_move.
- **D4.** Tests that need .git skip cleanly without a repository. The field-bag model refuses a Potion on a full member and keeps it, as the game does (checked in the decomp).
- **D5.** The shift question cannot lose its foe. It is one message whose first page names the foe, and the eyes read that message from its start (checked in the decomp and in host/eyes.py). The code change only moves the expression into a function. Live, all 29 shift questions in the B3 runs named the next foe.
- **Reproduced first.** V2-M1 and V2-M2 were reproduced on c5146e53, with 10 of 10 hashed predictions holding.

**A bug in the judge, found and fixed.** The first builder's judge followed one Wurmple-line member by "least change". At 6406's fourth battle it switched to the party's other Cascoon L5, which never fights. Its own end check flagged this in all three Wurmple runs. It was fixed before any verdict was recorded: every member of the plan's species line is now tracked at once by identity, from the game's PID read at the start, and checked against the PID read at the end. The old tracker is kept as the fault arm.

**Three instruments give one answer.**
- (a) Every record's party read, by identity. A planted faint is counted exactly once. 0 ambiguous steps, and exact agreement at the end in 6 of 6 runs.
- (b) The pre-registered method: each battle's first and last party.
- (c) Round 2's verifier counter, unchanged. On round 2's logs it reproduces the 7 faints it reported.

**The live A/B.** These are development runs, one trajectory per seed, never a rate.
- **Wurmple plan, ab3w (#122, seeds 6406-6408).** A: 0 of 3 BADGE02. B3: 3 of 3.
- **Grovyle plan, ab3g (#123, seeds 6411-6413, the first live runs of this branch).** A: 0 of 3. B3: 3 of 3, each winning its second BRAWLY fight. Grovyle was L27-28 at the first fight, against A's L22-23.
- **Trainee safety.** In all six B3 runs the trainee fainted 0 times in raise battles and 0 times in the plan's other battles (the BRAWLY fight is excluded). Round 2's six B runs had 7. No member sent in by a switch fainted.

**What these runs do not show.**
- The raise battle's rescue never fired live, because the game refused 0 runs.
- The guard's later-turn rescue never fired live.
- Potions were never used.

**Prediction misses.**
- The Grovyle level: L27-28, against the predicted L24-26.
- Grovyle BADGE02: 3 of 3, against the predicted at most 1.
- The 6406 Dustox level: L17, against the predicted L13-L16.

**The chapters 1-5 replay control (#124).** C and B3 are identical, with frames, on L1, C1L4 and C2L4. The fault arm differs from B3 from record 257.

**Observed, not changed.** B3's code was frozen for the runs, so a fix would need new seeds.
- The Grovyle raise ran out of PP and fought with Struggle 8-9 times a run. The raise never looks at PP.
- A battle that starts while a raise goal is being decided is fought with neither the raise rules nor the guard. This happened 4 times in 6 runs, with no faint.
- Once (6413), the guard's fallback sent Poochyena L6, which was not sure to win, in for Grovyle at 31%. Poochyena won on 1 HP.
- The developer verdict looks pessimistic for the Grovyle plan.

**Mutants.** The round's mutant file was hashed before its first run. It catches 101 mutants as predicted and leaves 2 redundant as predicted, of 103. That held at 11:01 and again on the final tree.

**The full regression lane failed, on timeouts only.**
- Every unit suite passed, and so did the frozen-tree check.
- Four revert drivers timed out under the load of the PC, with the bot tuner and a parallel builder running.
- Re-run alone, all four pass: bossprep, r1, step3 and step5.

**Final gates.** All 21 exit 0 on the final tree.

The evidence is ai_player/evidence/2026-11-11-bossprep-bp1r3-live-ab.txt. The judged records, including every run's actions.jsonl, are kept in s53/bp1r3/out for the verifier.

## Boss preparation BP-1, round 3: verification (the verifier, 2026-11-11)

**Verdict: CONDITIONAL PASS.** The round's claims hold when checked against the game's own records, so V2-M1 and V2-M2 are closed on these trajectories. The code adds two new MAJOR problems that must be fixed offline, with tests, before this round is merged:
- **V3-M1, a heal loop.** This round's rest line (D1) causes it.
- **V3-M2, the guard's fallback.** It sends a member that cannot win in place of a trainee that can. This happened once live.

These are development runs, one trajectory per seed, never a rate.

**How I checked.** I copied the uncommitted worktree, without .git, into s53/bp1r3/verify/repo and worked there. I wrote my own instruments and did not reuse the builder's. Every prediction was hashed before its run. The run book is s53/bp1r3/verify/STATE.md. I ran no live batch: the kept records and the offline reproductions settle every finding. Seeds 6409, 6410 and 6414-6430 are untouched.

**What I confirmed.**
- **The code the runs used.** The worktree's play digest now is 360ff20c, equal to the frozen B3 arm's. Every play file was last modified at 10:38-10:46, before the 11:12 stage. revert_bossprep.py's sha256 (c13efc0f) equals the hashed copy from 11:01.
- **The seeds.** I searched 189 ledger files: main, every worktree including ch6-p11, the lab, the old scratch and the learner clone.
  - Each of 6403-6408 and 6411-6413 is in exactly one entry (#122-#124), and only in this worktree's ledger.
  - The entries' bounds_sha256 values equal the prediction files' hashes.
  - The prediction files were written at 11:11:21, before each batch started.
- **Trainee faints, counted by my own identity tracker** (vcount.py). It reads every record's party from the game and tracks every member at once by a full assignment. It is seeded from, and checked against, the framework's PID reads.
  - In the six B3 runs the trainee fainted 0 times outside BRAWLY's fight.
  - No member of any kind fainted while a plan was active.
  - The BRAWLY-fight faints were found as predicted: 6408, 6411, 6412 and 6413.
  - Across the 12 runs there were 0 ambiguous steps and the end check agreed in 12 of 12.
  - Every faint by identity matches one of the game's own 'X fainted!' texts, one to one.
  - A faint I planted in a raise battle, and separately in a heal-walk battle, was counted exactly once each.
  - No raise battle began with the trainee under its floor. The trainee's lowest share was 46-49% in the Wurmple runs and 31-32% in the Grovyle runs.
- **The A/B, re-derived from the flags.**
  - Wurmple plan: A 0 of 3 BADGE02, B3 3 of 3. 6406 and 6407 won their first BRAWLY fight; 6408 won its second. Dustox was L17/16/16.
  - Grovyle plan: A 0 of 3, B3 3 of 3, each run winning its second fight. Grovyle was L27/28/28.
- **The chapters 1-5 control.** I compared the raw records, not only the decision streams, leaving out the host's timing field.
  - L1 and C1L4 are identical in every field.
  - C2L4 differs in one log line, a dict printed in another order. 0 decisions differ.
  - The fault arm F3 first differs from B3 at raw record 1584.
- **Gates and mutants.** All 21 gates exit 0 on the copy without .git, and the git-dependent tests skip cleanly (D4 holds). The builder's mutants, re-run on the copy: P0 PASS (148 tests), 101 CAUGHT and 2 REDUNDANT, as predicted.
- **D5.** The shift message (sText_EnemyAboutToSwitchPkmn) and the 'It won't have any effect' refusal match the decomp.
- **No hidden state and no bot code.** check_fairness, check_purity and the call census pass. Purity is CLEAN in 12 of 12 runs.

**MAJOR findings.**
- **V3-M1, a heal loop (a regression from D1).** When the knock-out partner fails the partner line even at full HP, partner_worn never clears. next_goal then heals on every decision, and the budget check, which sits inside _raise_goal after HEAL, is never reached.
  - The reproduction, with predictions hashed first: a Grovyle L17 46/46 at full HP with the Wurmple plan healed on 5 of 5 decisions, and still did with the budget exceeded.
  - Controls: a Grovyle L21 raises, and so does round 2's code, which also spends the plan when over budget.
  - A nurse heal on a full party returns 'healed', so only the play loop's 120,000-frame patience ends the run, stuck.
  - A Grovyle at L14-L17 fails the line against ROUTE116's Taillow L8, and ROUTE116 is the first-ranked raise map at that level.
  - The live runs did not reach it because C1's partner was L21. No test covers it.
- **V3-M2, the guard's fallback.** In 6413, battle 106, Grovyle L25 was at 21/68 against a Taillow L6. The guard sent Poochyena L6, which ended the battle at 1/21.
  - By the rescue's own question (fight_safe with keep 0), the trainee wins in one hit, leaving 12/68, and Poochyena cannot win.
  - The lead's D2 asked for 'the healthiest member that wins'. The builder disclosed the deviation as a question.
  - No offline test covers this path.

**MINOR findings.**
- **V3-m1, trainer battles are unprotected.**
  - During a raise goal, a trainer battle has neither the raise's rules nor the guard nor the ordinary switch. A Wurmple L5 fights a Zigzagoon L12 and keeps fighting at 3/21.
  - Outside a raise, the guard acts in a trainer battle only under the floor, so a full Wurmple L5 fights a Zigzagoon L12 whose worst hit is 25.
  - Every one of the 905 battles fought during the six active plans was wild, so neither case happened live.
- **V3-m2, the seam is wider than reported.** A battle between goals uses the previous goal's guard and purpose. Four such battles followed a raise goal, all won, none fainted. The exposure covers any goal decided right after a raise, not only a raise goal.
- **V3-m3, PP.** The raise ignores PP, so the Grovyle trainee used Struggle in 9/8/9 raise battles. This predates round 3 and the builder disclosed it.
- **V3-m4, coverage.** The paths that never fired live are proven offline only. My 19 mutants gave 6 CAUGHT and 13 REDUNDANT, every prediction held. The REDUNDANT ones mark 13 rules with no test, including V3-M1 and V3-M2.

**NIT findings.**
- **V3-n1.** The headline's '7 in round 2's six runs' compares six Wurmple-plan runs with three Wurmple-plan and three Grovyle-plan runs. The like-for-like figure is 0 in 3 against 7 in 6. The Wurmple zero came without the raise ever entering its run mode, so the rest line prevented the V2-M1 situation; the rescue did not handle it.
- **V3-n2.** The fallback battle is battle 106, not 105. '29 of 29' covers all nine B3 runs (24 in the A/B and 5 in the control). 'Fully identical' holds for the decisions; one log line's dict order differs.

**What the next round needs.**
- Fix V3-M1 and V3-M2, each with a test and a mutant.
- Re-run the A/B on new seeds.
- Decide whether trainer battles (V3-m1) and the seam (V3-m2) belong in round 4.

**Clean-up.**
- I removed verify/repo (584 MB) after a link check that found 0 links. I made no junction.
- The worktree is unchanged: HEAD c5146e53, 13 modified and 17 untracked files. The main checkout is untouched, and the main sandbox counts are unchanged (plugins 43, mgba 44, roms 2).
- C: has 66.1 GB free.
- The builder's s53/bp1r3/out (about 156 MB, the 19 runs' records) is left for the lead to keep or delete.
- verify/ keeps only the scripts, predictions and outputs (1.9 MB).

## Boss preparation BP-1, round 4 (the builder, 2026-11-12)

Round 4 closes round 3's verifier findings (V3-M1, V3-M2, V3-m1 to V3-m4, V3-n1, V3-n2), following the lead's design calls E1-E7 (06, 2026-11-11, "The fix round after BP-1 round 3 and P11-1"). The work is in the worktree `wf_e7452923-f06-3` on 975964c7 (branch wip/ch6-bp1). It is not committed. These are development runs, one trajectory per seed, so nothing here is a rate.

**Headline (reworded by the lead after the verifier's V4-M1 and V4-n2; the builder's own wording is kept in `s53/bp1r4/result/build_report_section.md`).** In all six live runs the trainee fainted 0 times outside BRAWLY's fight, and there was no heal loop. BADGE02 came in 4 of 6: 3 of 3 Wurmple-plan runs and 1 of 3 Grovyle-plan runs, so prediction P-G6 (at least 2 of 3) MISSED, against round 3's 6 of 6 on other seeds. The diagnosis reads the miss as (S), the seeds, not a round-4 regression. The verifier's paired A/B on three new Grovyle-plan seeds points the same way: round 4 won BADGE02 in 3 of 3 and round 3 in 1 of 3. The gates and the full mutant run passed on the final tree; one live prediction missed.

Faints were counted by PID, and the end check agreed with the game's own read in 6 of 6. One caveat: E5 changed the trainee's PP when it arrived at BRAWLY in two runs (6426 and 6427). There is no sign that it changed an outcome, but the records cannot show what full PP would have done. What they show: the first fight was lost in all six of the builder's Grovyle-plan runs of both rounds, with or without those moves; a lost fight at L27-28 gains 613 EXP either way; and the missing moves were Quick Attack (the same type and power as Pound) and Pursuit (resisted by MACHOP and MAKUHITA). No play code changed after the 19:50 freeze. The final play digest, 840ece09384cb6b8, is the one the live runs played.

**Two cuts.** A session usage limit cut the first builder at about 8:30 PM on 2026-11-11, while it waited on mutant run 1. Its detached live chain and mutant run finished on their own (20:44:43, 20:47:32). The limit cut the second builder at about 9:22 AM on 2026-11-12, while the full mutant run was going; that run also finished on its own, PASS, at 09:52:38. A third builder took over at 1:50 PM. Nothing was relaunched and nothing was lost. The run book is `s53/bp1r4/STATE.md`.

**Reproduced first** (on 975964c7; prediction hashed 18:58:25). All 17 readings held:
- V3-M1: a Grovyle L17 at full HP is sent to heal 5 of 5 times, and the plan is never spent.
- V3-M2: the 6413 fixture switches to Poochyena although the trainee wins the fight itself.
- V3-m1: a trainer battle outside a raise is fought where it should switch.
- V3-m2: a battle right after a raise goal has purpose "raise" and no guard.
- V3-m3: `fight_safe` gives the same answer at 0 PP and at 20 PP.

On the round-4 tree every one of these readings moved as designed.

**What was built.**
- **E1:** the partner is judged at full HP, once per map and level. A map where it fails is not used for switch-training. The budget is checked before any rest.
- **E2:** with no member sure to win, the order is: the trainee's own sure win first, then a run in a wild battle, and only then (under its floor) a member that cannot win.
- **E3:** the guard's test also applies in trainer battles, from static knowledge only, including a raise goal's trainer battles.
- **E4:** the guard and purpose reset at each goal's end.
- **E5:** a move at 0 PP is no move. A raise session ends and the party heals when every move that hurts is out of PP.
- **E6:** the tests and mutants below.
- **E7:** 18 correction lines appended to round 3's live evidence file; nothing above them changed.

**Offline proof.**
- `test_bossprep` grew from 141 to 187 tests, all OK.
- Mutant run 1 caught 152 of 155 mutants as predicted, with 2 REDUNDANT as predicted: one miss, so it FAILED. The miss was `own_fallback_unmade`: its named test reached another branch's fallback call first. It was closed with tests only, and the predictions were re-hashed at 09:06:54 before any further run.
- The five new or changed mutants alone (msel1): 5 of 5 caught.
- **The full final-tree run (mutants2): 157 caught and 2 REDUNDANT, both as predicted, of 159. PASS.**
- The round-3 verifier's 19 mutants, adapted: 19 of 19 caught, including all 13 that round 3 found REDUNDANT. 9 of the 19 predictions were not blind.

**Live runs** (start probe-C1, target ch7_brawly; every prediction hashed before its runs).
- **#125 ab4w (6414-6416), Wurmple plan:** P-W1 to P-W8 all held. BADGE02 3 of 3. Heal goals 9, 9 and 8, none of them a heal of a full party.
- **#126 ab4g (6426, 6427) and #127 ab4g2 (6429), Grovyle plan:** P-G1 to P-G5, P-G7 and P-G8 held.
  - Struggle battles 0, 0 and 1, against round 3's 9, 8 and 9.
  - A raise session ended for PP, and the next goal was a heal, in 3 of 3.
  - The one line the judge flagged for P-G7 (6427, frame 953180) was a run, not a switch: Grovyle with no PP ran from a wild Abra. That is E2 working live.
  - P-G6 MISSED: BADGE02 in 1 of 3.
- **#128 control4 (6417-6419):** P-C1 to P-C5 all held.
  - 975964c7 and the round-4 tree give identical decision streams, frames included (749, 542 and 907 records).
  - The fault arm diverges after the first verdict line.
  - Purity CLEAN in 7 of 7.
- **E1's live pair was skipped:** no seed in the range lets E1 fire (offline discriminator), so E1 is proven offline only.
- **E3 and E2's step (c) never ran live either (added by the lead after the verifier's V4-m2; the count of step (a) corrected by the lead on 2026-11-12 after the closing pass's VC-n1: this line read "once").** Over the 9 round-4 runs (the builder's 6 and the verifier's 3) every guard line, 32 in all, is in a wild battle: no trainer battle came up during an active plan. So E3 (the guard in trainer battles) is proven offline only (tests, mutants, the verifier's probes X2, X3 and X5), and so is E2's step (c), sending a member that cannot win. Live, E2's step (a) ran in 2 battle decisions, both in the verifier's seed-6424 run: the guard's first turn in battle 17 (Grovyle L22 at 33/60 against a Nincada L7, won), and turn 2 of battle 20, a raise battle's own fight gone badly (against a Nincada L6, won). Step (b), the run, ran in 2: battle 96 of 6427 and battle 96 of the verifier's 6421. The counts are from each run's log (`s53/bp1r4c/e2_count.py`, and again by the closing verifier's own script).

**P-G6, diagnosed** (`s53/bp1r4/PG6-DIAGNOSIS.md`; read-only on the kept records).
- **Leaf Blade is strongly associated with the win; it is not a law (reworded by the lead after the verifier's V4-m1).** In both rounds' Grovyle-plan records a BRAWLY fight was mostly won when Grovyle reached L29 (Leaf Blade) before MAKUHITA, and mostly lost when it did not. In the builder's 15 fights every lost fight gained exactly 613 EXP, and every won fight 967. This was checked by PID, with a 6 of 6 self-check against the game's own experience read. Of those 15, fights starting at 18798 EXP or more were won 3 of 3; below that, 1 of 12 (round 3's 6411 won its second fight at 17433 EXP). With the verifier's 12 paired-A/B fights added, 27 in all: 5 of 5 won at or above the line, 3 of 22 below it. Two of the verifier's fights were won below the line without Leaf Blade (round 4's 6421 at 18422 EXP and 6424 at 17715).
- **The shortfall came after the raise.** Round 4's raise ended with no less experience than round 3's (16283-16405 against 15796-16361). The gap opened on the way from the raise to the gym: round 4 gained 594-1306 EXP there, round 3 1024-2501, because round 3's longer stretches included Centre trips.
- **No round-4 change ran there or in the fights:** 0 of its lines in all six runs, against 320-328 lines a run in the raise itself (the positive control).
- **Same decisions in both trees.** An offline replay of all 323 events of the 15 fights gave identical decisions through both trees. A planted difference was detected in 14 of 15 fights.

So no play code was changed for P-G6.

**Gates on the final tree.** All exit 0:
- test_bossprep, test_goals, test_battle, test_world, test_eyes, test_kb2, test_saving, test_hands, test_host, test_check_purity, test_step53_a2, test_evidence, test_safety_gates FairnessTests, test_run_regression and test_check_anchors.
- check_fairness, check_purity, call_census, check_paths and check_anchors.
- `ledger.py --check`.

**Housekeeping.**
- The live evidence file `ai_player/evidence/2026-11-11-bossprep-bp1r4-live.txt` is written. It holds the result for each ledger entry #125-#128; the entries themselves keep the usual "read the evidence" verdict.
- The stage was removed with its junctions unlinked first. The judged runs' actions.jsonl are kept in `s53/bp1r4/out`.
- The main sandbox is unchanged: plugins 43, mgba 44, roms 2 entries. C: has 59.4 GB free.

**For the lead.**
1. The Grovyle plan's 160-battle budget ends the raise at L27, 3006-3615 EXP short of Leaf Blade (about 52-66 more raise battles). Should the budget or target be sized to the key move's level?
2. After a lost boss fight the player walks straight back with the same team. 6426 and 6427 used their three tries 537 and 592 EXP short. Should a loss lead to more training before the next try?
3. The pre-boss top-up counts HP only. 6426 and 6427 entered their first fight with some moves out of PP. Should PP count?
4. For the commit: mutant run 1 rewrote round 3's `2026-11-11-bossprep-REVERT.txt`, so it now records the FAIL. Round 3's version is archived, and the final tree's proof is `2026-11-12-bossprep-REVERT.txt`.

## Boss preparation BP-1, round 4: verification (the verifier, 2026-11-12)

**Verdict: CONDITIONAL PASS.**
- V3-M1 (the heal loop) and V3-M2 (the guard's fallback) are closed. I reproduced both on 975964c7, both are gone on the round-4 tree, and each fault switch brings its bug back.
- Live, round 4 had 0 trainee faints outside BRAWLY's fight in 9 of 9 runs (the builder's 6 and my 3), counted by PID identity, and no heal loop.
- P-G6's miss is **not** a round-4 regression. On three new Grovyle-plan seeds, the paired runs gave BADGE02 3 of 3 for round 4 and 1 of 3 for round 3.
- One MAJOR is a documentation fix: the report's headline does not carry BADGE02 4 of 6 and the P-G6 miss.
- These are development runs, one trajectory per seed and arm: nothing here is a rate.

**What I checked, and how.** I worked on a copy of the worktree (no .git), which is now deleted.

Provenance and the two cuts:
- All 13 recorded sha256 values match: the repro prediction, both revert_bossprep hashes, the 4 live predictions, test_bossprep, vmutants_r4, both replay predictions and the live evidence file.
- Each prediction was hashed before its run:
  - the live predictions (file time 19:59:06) before the first run started at 20:00:20, each ledger entry recording its hash;
  - the mutant predictions at 19:50:27, before run 1 at 19:50:33;
  - the re-hash at 09:06:54, before vmut1, msel1 and mutants2;
  - the replay prediction before its base and planted arms, as it states.
- Nothing was relaunched, and no run was cut. Mutant run 1's FAIL is reported as a FAIL.
- The final tree's play digest is 840ece09384cb6b8, the same as the live B4 arm's. Its newest play file is 19:47:41, before the 19:50:27 freeze.

Seeds:
- 6414-6419, 6426, 6427 and 6429 appear only in round 4's own entries (#125-#128), registered at each batch's start.
- Mine (6421, 6424, 6430) were free in 199 ledgers before I registered them.

Reproduction (prediction sha256 572e5807..., hashed first):
- On 975964c7:
  - H1: a Grovyle L17 at full HP is sent to heal 5 of 5 times.
  - H2: the plan is still active with frames at 10**7.
  - G1: Poochyena is switched in for the 6413 trainee.
- On round 4:
  - R1: the raise goes to PETALBURG_WOODS 5 of 5 times.
  - R2: over budget, the plan is spent.
  - RG1: the 6413 trainee fights its own sure win.
- Fault switches: partner_full_unchecked brings the loop back (R4); adding budget_after_rest keeps the plan active (R5); fallback_first brings Poochyena back (RG1F).
- Probes X1-X7 held: a run at 4/68, the fallback after a refused run, the trainer-battle guard inside and outside a raise, fight_safe and the heal both counting PP.
- One prediction failed: X3's base clause. Base also switched there, by the ordinary matchup rule, so that fixture does not test E3 on base.

Gates and mutants, all re-run on my copy:
- All 21 gates exit 0. test_bossprep ran 187 tests, OK. With no .git, test_hands skipped 1 test and test_step53_a2 skipped 5.
- The builder's revert_bossprep: 157 CAUGHT and 2 REDUNDANT as predicted, of 159. PASS.
- The builder's 19 adapted round-3 mutants: 19 of 19 CAUGHT. 7 of round 3's 13 REDUNDANT apply unchanged; I read the 6 re-anchored ones and each breaks the same rule.
- My own 22 mutants (sha256 8645f29c..., hashed first): 18 CAUGHT and 4 REDUNDANT, all as predicted.

**The builder's live runs, re-judged from the game's records:**
- Faints, with round 3's verifier's identity counter: 0 outside BRAWLY's fight in 6 of 6. The end check agreed in 6 of 6, and a planted faint was counted once.
- Heal goals: 9/9/8 (Wurmple) and 1/2/3 (Grovyle). The only heals with the whole party at full HP were the 3 PP rests. No two heal goals came in a row without a battle between them.
- Struggle pages: 0/0/0/0/0/1. Each of the 3 PP rests led to a heal.
- The P-G7 line is a run.
- Control: the streams are identical (749/542/907 records), and the fault arm diverges at record 243.

**P-G6: my attempt to refute (S).**
- In the code, no round-4 path runs in the boss fight (no guard, purpose "train") or after the plan is SPENT (the plan must be "active").
- My own read of the records matches the builder's EXP table: the PID self-check passed 6 of 6, and the EXP at SPENT and at fight 1 are the same.
- Every run from a wild battle on the way to the gym was the Story persona's "not one it wants". None was about PP.
- E5 did change the arrival PP. 6426 began fight 1 with only Pound and Absorb, and 6427 with Pound, Absorb and Quick Attack. Fights 2 and 3 had full PP, after the whiteout.
- Then my **paired A/B** (prediction sha256 fd33651a..., hashed first): round 3 (975964c7) against round 4 on the same seeds 6421, 6424 and 6430, from probe-C1, started 10 s apart.
  - The streams were identical up to the first battle. Then round 4's own changes split them: at 6421 f783210, round 3 had a battle with purpose "raise" where round 4 had "travel" (E4).
  - BADGE02: round 4 3 of 3, round 3 1 of 3.
  - Raise EXP: round 4 +9492, +9096 and +9463; round 3 +9159, +2804 and +7852.
  - Round 4 had 0 trainee faints outside BRAWLY's fight in 3 of 3.
  - V-1 to V-4 and V-6 to V-8 held. V-5 MISSED: two fights were won without Leaf Blade.
- So round 4 did not make the boss fight worse, and the seeds reading stands.

**Findings.**
- **V4-M1 (MAJOR):** the headline needs BADGE02 4 of 6 and P-G6 MISSED, with its caveat.
- **V4-m1:** the Leaf Blade rule is a strong tendency, not a law. Fights at or above 18798 EXP were won 5 of 5; fights below it 3 of 22.
- **V4-m2:** E3 and E2 step (c) never ran live; say so, as for E1.
- **V4-m3:** latent, from before this round, but measured. A trainee between its floor and a safe win is never rested and runs from almost every battle. On round 3's arm it burned 115 of 161 raise battles (6424). The rule is still in round 4 (shown offline); round 4 never entered that band in 9 runs. This is for the lead, next to DESIGN 1.
- **V4-m4:** four round-4 rules have no test, among them E1's under-the-cap filter.
- **NITs:**
  - E2 step (a) keeps the trainee in with one rough hit plus 1 HP to spare. That is the design as written, and live it fired once, at 33/60. **[Lead's correction, 2026-11-12, after the closing pass's VC-n1: step (a) ran in 2 live battle decisions, both in the verifier's seed-6424 run, battles 17 and 20. The decision at 33/60 is battle 17's. The count is from each run's log, by the closing builder and again by the closing verifier.]**
  - The E5 caveat is a counterfactual: say "no sign that it changed an outcome".
  - For the commit: restore round 3's REVERT.txt from the archive, which matches 975964c7 with line endings normalised.

**For the lead.**
- Carry my ledger entries #129-#131 (seeds 6421, 6424, 6430, now spent) from s53/bp1r4/verify/ledger_vab_entries.json into the branch's ledger.
- Unspent seeds of the range: 6409, 6410, 6420, 6422, 6423, 6425, 6428. All draw the Wurmple plan; no Grovyle-plan seed is left.

**Housekeeping.**
- My stage was removed with its junctions unlinked first. Its 6 world.jsonl files (42.7-67.9 MB) went with it.
- The copy and the mutant temp folder are deleted. s53/bp1r4/verify/out keeps my 6 runs' actions.jsonl.
- The main sandbox is unchanged: plugins 43, mgba 44, roms 2. The main checkout is clean, and the worktree is as the builder left it. C: has 59.0 GB free.
- The run book is s53/bp1r4/verify/STATE.md.

## Boss preparation BP-1, round 4: the closing pass (the builder, 2026-11-12)

**Headline.** The closing pass is done. No play code changed: the play digest is still 840ece09384cb6b8. Four round-4 rules that had no test now have one, and each rule's mutant is caught. This is proven offline only, by tests and mutants. No live run, no emulator and no new seed were used. The full mutant run on the closing tree passed with 161 CAUGHT and 2 REDUNDANT, of 163. All 21 gates and Tier 0 pass. The verifier's paired A/B is now branch evidence, and four corrections were appended to round 4's live evidence. One count disagrees with the verifier's own: E2 step (a) ran in 2 live decisions, not 1. The lead's report still says "once". Nothing is committed. The lead's follow-up items were not started.

- **C1, the ledger.** The first builder carried the verifier's #129-#131 (seeds 6421, 6424, 6430) into the branch's ledger, as `verify/ledger_vab_entries.json` records them. I checked this again from the files:
  - `ledger.py --check` reports 131 entries, PASS.
  - `seeds_free.py` lists all three seeds as spent.
  - Their bounds hash equals `sha256(prediction_vab.txt)`, `fd33651a...`.
- **C2, four rules with no test (V4-m4).** First, the gap on d4794135's tests: each of the verifier's four mutants passed all 825 tests of test_bossprep, test_hands, test_goals and test_battle. The new tests are in `ClosingTests`, and each mutant is registered in `revert_bossprep.py` as CAUGHT by its test.
  - (a) The cap. Kirlia L20 has cap 15. ROUTE112, top level 16, is over the cap, even though the healed Kirlia would be fit there. The raise stays on ROUTE116 in "own" mode. Control: Kirlia L21 has cap 16, so ROUTE112 is at the cap, and it is chosen in "mix" mode.
  - (b) A PP that was not read is still usable; a PP read as 0 is not. Both halves are pinned.
  - (c) The order of the two checks was measured first. When the trainee is both low and out of PP, the code's order gives a Potion when the centre is far, then the centre. The swapped order walks to the centre at 5/18. The code's order is pinned.
  - (d) `_last_resort` was called directly. At 5 runs it runs. At 6 runs it does not run. The state can be reached directly, so the mutant is CAUGHT and no pair mutant was needed.
  - The catch run caught all 4, each failing only its own test.
- **C3, the corrections.** One dated CORRECTION block was appended to `2026-11-11-bossprep-bp1r4-live.txt`. Nothing above it changed. The file made all four claims:
  - (1) The headline now gives the total: BADGE02 in 4 of 6, P-G6 MISSED, against round 3's 6 of 6. The paired A/B gave round 4 3 of 3 and round 3 1 of 3.
  - (2) Leaf Blade is strongly associated with the win; it is not a law. Over 27 fights, 5 of 5 were won at or above 18798 EXP, and 3 of 22 below it. All three wins below the line came without Leaf Blade.
  - (3) E3 and E2 step (c) never ran live: all 32 guard lines are in wild battles. E2 step (a) ran in 2 decisions and step (b) in 2.
  - (4) For E5, there is "no sign that it changed an outcome", with the reasons. This replaces the counterfactual.
  - The ledger holds no evidence hashes, so nothing else needed to change.
- **C4, the A/B as branch evidence.** New file `ai_player/evidence/2026-11-12-bossprep-bp1r4-verify-ab.txt`, written by script from the verifier's files. It gives:
  - who ran the A/B and when, and the prediction's hash (taken at 14:34:39);
  - each arm's commit and play digest;
  - per seed and arm: BADGE02, losses to BRAWLY, the raise's EXP, faints outside the boss fight by PID, and purity;
  - which of the verifier's predictions held (7) and which missed (V-5);
  - where the raw records are in the lab.
  One line is my own, and it is marked: the play digest ties B4 to d4794135. #129-#131 now point at this file.
- **C5, the diagnosis as a note.** New file `ai-research-notes/2026-11-12-BP1-PG6-DIAGNOSIS.md`. Its first paragraph says it is a NOTE, who wrote it, what tried to refute it and what stays unproven. V4-m1 is corrected in place and marked; so is V4-n2. Every line is under 1200 characters.
- **C6, which file proves which commit.** `c6_revert_table.py` recomputes each round's tree digest from `git diff <parent> <commit>`, in provenance's own scope. Each committed round matches exactly one file:

| Tree | HEAD + digest | The file that proves it | Mutants (CAUGHT + REDUNDANT) | OVERALL |
|---|---|---|---|---|
| round 1, 69ce148e | 18c3d51b + 19176520fd219899 | 2026-11-09-bossprep-REVERT.txt | 35 + 2 of 37 | PASS |
| round 2, c5146e53 | 69ce148e + 05fc87fa4bfa5900 | archive/05fc87fa4bfa5900-69ce148e/2026-11-11-bossprep-REVERT.txt | 73 + 2 of 75 | PASS |
| round 3, 975964c7 | c5146e53 + 6701eab79b5bf870 | archive/6701eab79b5bf870-c5146e53/2026-11-11-bossprep-REVERT.txt | 101 + 2 of 103 | PASS |
| round 4, d4794135 | 975964c7 + 03a471a697f2df77 | archive/03a471a697f2df77-975964c7/2026-11-12-bossprep-REVERT.txt (moved there by this pass's run) | 157 + 2 of 159 | PASS |
| closing tree (uncommitted) | d4794135 + 1f3d41913ffa4e0b | 2026-11-12-bossprep-REVERT.txt | 161 + 2 of 163 | PASS |
| NO committed tree: mutant run 1 | 975964c7 + 3707fc5fa1abfa32 | 2026-11-11-bossprep-REVERT.txt | 152 + 2 of 155, 1 miss | FAIL |
| NO committed tree: earlier intermediate runs | 69ce148e + 0fd10c61781d6b4b, 94d2f6c6dc9ae148; 18c3d51b + f7184354facf4506, ff14c5e419050875 | archive/<digest>-<HEAD>/ | 73 + 2 of 75; 69 + 2 of 71; 34 + 2 of 36; 34 + 2 of 36 | PASS |

  The closing tree's row holds only if the commit changes exactly these two in-scope files, `test_bossprep.py` and `revert_bossprep.py`.
- **C7, the final tree.** The predictions were hashed before any run: `prediction_catch.txt f0458ef7...`, `revert_bossprep.py 76137c6a...`, `test_bossprep.py 6b0f6df7...`. The full run ran detached from 19:35 to 20:19: 161 CAUGHT and 2 REDUNDANT of 163, PASS. All 21 gates exit 0, and Tier 0 passes. `git diff --stat d4794135 -- ai_player/brain ai_player/knowledge` is empty. The play digest is 840ece09384cb6b8, computed as round 4 computed it (`make_arm_r4.tree_digest`, play files only). The run book is `s53/bp1r4c/STATE.md`.

## Boss preparation BP-1, round 4: the closing pass, verification (the verifier, 2026-11-12)

**Headline.** CONDITIONAL PASS. I found no MAJOR, two MINORs and three NITs.
- **No play code changed.** I checked the bytes, not git's summary: all 13 files under ai_player/brain plus the .py files under ai_player/knowledge equal d4794135's blobs once line endings are normalised. No file was added or missing, and none was modified after 16:30. The play digest is 840ece09384cb6b8 on the worktree and on my copy.
- **The new tests catch broken rules.** I broke each of the four rules a second way myself, with predictions hashed first. The four ClosingTests caught every break of the rule they name.
- **Gates.** All 21 gates and Tier 0 pass on my copy of the final tree.
- **Numbers.** Every number I re-derived from the raw files holds.
- **Caveats.** Both MINORs are claims in test docstrings or the deviation text, not behaviour. Fix them in the report and the handoff, not in test_bossprep.py: any byte change there moves the digest off the REVERT file's 1f3d41913ffa4e0b, and that would need a new 44-minute mutant run.
- **Not proven here.** This is offline proof only. Nothing was run live, and I used no emulator and no seed.

**The cut.** The first builder ran from 16:34 to about 16:50. It applied C1 and wrote three recon scripts, and it started no job: no lab file is dated between 16:50:33 and 19:18:45, and no pid file predates 19:23.
- Every hashed file matches the hash its STATE line recorded, and was written before the run it predicts:

| File | sha256 | Written | Its run started |
|---|---|---|---|
| prediction_gap.txt | 37ddfa2f... | 19:22:27 | gap, 19:23:01 |
| prediction_catch.txt | f0458ef7... | 19:32:48 | catch, 19:33:11 |
| revert_bossprep.py (worktree and hashed copy) | 76137c6a... | 19:31:55 | full, 19:35:19 |
| test_bossprep.py (worktree and hashed copy) | 6b0f6df7... | 19:30:42 | full, 19:35:19 |
| gap_run.py | 0e5761a9... | before the gap run | gap, 19:23:01 |
| vmutants_v4_defs.py | 8645f29c... | 14:50:23 (unchanged) | gap, 19:23:01 |

- Nothing was re-hashed, and no result comes from a job the cut killed.
- The worktree's provenance digest now is HEAD d4794135 + 1f3d41913ffa4e0b (2 files, 15196 bytes, 0 untracked). That equals the full run's code line, so the full run ran on the final tree and was not re-run.

**My mutants.** Prediction prediction_vmut.txt, sha256 4f60b152..., hashed at 20:38:12 before the run. The run, job_vmut.out, ran 198 tests per copy (test_bossprep plus the FieldItemTests of test_hands).
- **Controls.** P0 passed every test. A comment that only mentions the boundary fails no test.
- **Caught as predicted, each among its failing tests:**
  - (a) va2: raise_maps ranks an at-cap map with the over-cap maps.
  - (b) vb1: a PP read as 0 counts as usable.
  - (b) vb2: out_of_pp treats an unread PP as no PP.
  - (c) vc1: _potion_goal refuses a trainee that is out of PP. Only test (c) fails.
  - (d) vd1: the bound is off by one (`<=`). Only test (d) fails.
  - (d) vd2: the run is not counted.
- **va1, a `>=` boundary in _raise_choice.** Test (a) survives it, which is VC-m1. My prediction that it would survive all 198 MISSED: RaiseMapTests.test_r6a catches it.
- **The registered mutants.** The four registered v4_ mutants have edits identical to vmutants_v4_defs.py, and 164 entries are registered including P0.

**C1, the ledger.** Entries #129-#131 equal ledger_vab_entries.json in every field except `evidence`, which C4 re-pointed to the new file (the file exists).
- Each older line is unchanged; #128 only gained its comma. Ids 1-131 are contiguous.
- Seeds 6421, 6424 and 6430 are in #129, #130 and #131.
- bounds_sha256 = sha256(prediction_vab.txt) = fd33651a...

**C3, the correction.** d4794135's blob is an exact prefix of the new file once line endings are normalised. 40 lines were appended, none non-ASCII.
- **Correction 1.** BADGE02 4 of 6; round 3 6 of 6 (P-B6 and P-G5 both '3 of 3').
- **Correction 2.** 27 fights: 5 of 5 won at or above 18798, 3 of 22 below it (v_leaf.py, independent). The three wins below the line are 6411 f2 at 17433, 6421-B4 f1 at 18422 and 6424-B4 f2 at 17715. 'Leaf Blade' appears in neither verifier winning log beyond lines 13-14.
- **Correction 3.** 32 guard lines, all '(wild)'. E2 (a) 2: 6424 battles 17 and 20. E2 (b) 2: battle 96 of 6427 and battle 96 of 6421. E2 (c) 0. Counted by v_e2.py, independently.
- **Correction 4.** Read against e5_check.out and v_judge_vab.json usable1. The scope NIT is VC-n2.

**C4, the new evidence file.** Every number matches v_judge_vab.json, v_judge_vab.out and the verifier's STATE.md lines 13-32:
- per seed and arm: BADGE02, the fights and their EXP, SPENT EXP and frames, faints by PID, the end frames, the first difference;
- B4 3 of 3 against C4 1 of 3; V-1 to V-8;
- 197 ledgers; 14:34:39, 14:34:54, pid 36552; 15:16 and 15:53;
- 115 of 161, +2804 and +9096.

Its headline carries its caveats.

**C5, the note.** It is a NOTE, ASCII, and its longest line is 123 characters. Its corrections match V4-m1 and V4-n2. The unmarked edits are VC-n3.

**C6, the table.** I recomputed each committed round's digest on its parent with provenance.tree_digest, in v_c6.py:

| Round | Digest on its parent |
|---|---|
| 69ce148e | 19176520fd219899 (added files untracked) |
| c5146e53 | 05fc87fa4bfa5900 |
| 975964c7 | 6701eab79b5bf870 |
| d4794135 | 03a471a697f2df77 |

Each matches exactly the file the table names. Every row's HEAD, digest, counts and OVERALL equal the 10 REVERT files.

**C7, the archive.** The archived copy equals d4794135's committed REVERT file once line endings are normalised. job_full.out line 167 records the driver's own keep_earlier move. All 921 of d4794135's evidence files are present.

**Shared files.** Only seven files were written in the worktree after 16:30, all expected. provenance.py and the run_regression files are untouched. Every changed tracked file is in git diff 18c3d51b..d4794135.

**Gates on my copy.**
- Test suites, all OK: test_bossprep 191 (including the 4 ClosingTests), test_goals 462, test_battle 112, test_world 139, test_eyes 89, test_kb2 128, test_saving 151, test_hands 64, test_host 37, test_check_purity 30, test_step53_a2 34, test_evidence 27, Fairness 9, test_run_regression 53 and test_check_anchors 7.
- Checks, all PASS: check_fairness, check_purity, call_census, check_paths, check_anchors (1736 mutants, 1761 edits) and ledger (131 entries).
- Tier 0: all 7 checks exit 0.

**Findings.**
- **VC-m1 (MINOR).** Test (a)'s control does not pin the at-cap boundary.
- **VC-m2 (MINOR).** Test (d)'s docstring is wrong that every caller passes run_ok True only before any run. v_runok_probe.py shows the guard's first decision calling `_last_resort(run_ok=True)` after the lead's refused run (runs 1 to 2). The bound can therefore bind in play, and the lead should decide whether E2 (b) should then come before (c).
- **VC-n1 (NIT).** Line 2038 of the build report also says 'fired once', not only line 1941.
- **VC-n2 (NIT).** The 613-EXP sentence needs its scope: one of the 27 fights, vabg2-C4 fight 1, gained 0.
- **VC-n3 (NIT).** Two edits in the note carry no CORRECTED marker.

**Conditions for the commit.**
- Commit exactly the two in-scope files at their hashed bytes, so the closing tree's REVERT row holds.
- Carry VC-m1 and VC-m2 in the report and the handoff.

**Other.**
- The main checkout's PROJECT KNOWLEDGE/cost-ledger.jsonl was modified at 20:50:09. That is after the builder's last line (20:28:56) and is not mine.
- A temp folder, ai_player_bossprep_mutant_0rn4dd43, dated 2026-11-11, is not this pass's and was left alone.
- My copy was deleted (16985 files). Nothing of mine is running.
- The run book is s53/bp1r4c/verify/STATE.md.

## Boss preparation BP-1, round 4: the closing pass, the lead's notes at the commit (2026-11-12)

The closing pass's verifier read CONDITIONAL PASS with two conditions: commit exactly the two in-scope files at their hashed bytes, and carry VC-m1 and VC-m2 in the report and the handoff. Both are met here. Nothing below was run live.

- **The commit holds the hashed bytes.** `test_bossprep.py` (sha256 6b0f6df7...) and `revert_bossprep.py` (76137c6a...) are committed as the full mutant run read them. Just before the commit the worktree's provenance digest was HEAD d4794135 + 1f3d41913ffa4e0b over 2 files, the code line of `2026-11-12-bossprep-REVERT.txt` (161 CAUGHT and 2 REDUNDANT of 163). Neither file was edited after that run.
- **VC-m1 (MINOR), carried, not fixed.** The cap test's CONTROL does not pin the at-cap boundary that its docstring says it pins: the verifier's mutant va1 (`levels[1] >= cap` in `_raise_choice`) survives `ClosingTests.test_the_raise_stays_under_the_cap`. Another test catches va1 (`RaiseMapTests.test_r6a_the_partners_cap`), so the rule itself is still guarded. The test file is not edited now, because any byte change moves the digest off the REVERT file and needs a new 44-minute mutant run. Next BP round: add GRANITE_CAVE_1F as a third map to the control, register va1 as CAUGHT, and re-run the mutants.
- **VC-m2 (MINOR), carried, with a design question.** Test (d)'s docstring says every caller passes `run_ok` True only when no run was made in the battle. That is false: the guard's first decision passes `run_ok=True` unconditionally, and the run count covers a run by any member. The verifier's probe shows `_last_resort(run_ok=True)` after the lead's refused run. So the last resort's run bound can bind in play. The behaviour is as tested; the docstring is wrong. Open for the next round: when another member's run was already refused in this battle, should a trainee still try the run (E2 step b) before step (c)? The docstring is reworded when the test file next changes.
- **VC-n1 (NIT), fixed in this copy.** "E2 step (a) fired once" stood in two places of this report: the lead's own line under round 4's build section, and the round-4 verifier's NIT. Both now carry the count from the records: 2 battle decisions, both in the verifier's seed-6424 run (battles 17 and 20). The verifier's own sentence is kept and the correction is marked beside it.
- **VC-n2 (NIT), scope stated.** "Every lost fight gained 613 EXP" is true of the builder's 15 fights. It is not true of all 27: in the verifier's A/B, round 3's arm on seed 6424 lost its first fight and gained 0 (10588 EXP before fight 1 and before fight 2). One scope line was appended to `2026-11-11-bossprep-bp1r4-live.txt` (nothing above it changed), and the note's first section says the same.
- **VC-n3 (NIT), stated in the note.** The note `2026-11-12-BP1-PG6-DIAGNOSIS.md` now names its two unmarked edits: the verdict's "lose ... win" reads "lost ... won", and the Files list was extended.
- **Not done, for the next BP round (BP-2).** V4-m3 (a trainee between its floor and a safe win is never rested), V4-n1, the raise's budget ending below the key move's level, what changes after a lost boss fight, a heal before a boss that counts PP, and the live judge that cannot tell a run from a switch.

## P11-1, the dark GRANITE CAVE crossing (the builder, 2026-11-11)

This round was resumed after a cut. The first builder stopped at about 11:32 because of a usage limit. Its work was still uncommitted in the worktree ch6-p11, and STATE.md listed what it had done. I resumed at 11:56 and finished at 13:45. Before changing anything I checked that the worktree matched STATE.md, recorded the cut in STATE.md, and discarded nothing.

**Headline, with its caveat.** With the final code the AI crosses the dark GRANITE CAVE floors much faster. It still reached STEVEN sooner overall in only 3 of 6 live pairs. In the other three, after the crossing, the AI on lit 1F went back over the one-way ledge for an item ball that was already gone, left the cave, and crossed the dark a second time. These are development runs: one run per seed, never a rate.

**What was built.**
- A static fact: the way through each requires_flash map, computed by a test-side extractor from the pinned decomp's layouts (extract_ways.py). It is shipped as knowledge/world/ways.json and read by a single loader, knowledge/ways.py.
- The fact is classified leaf by leaf in check_fairness RULE B. A developer key planted under a way makes the gate fail.
- On a dark map, the explorer walks toward the ladder the fact names. While that ladder is unseen, it plans through the unseen tiles at the navigator's existing UNKNOWN_COST and re-plans as the lit circle shows walls. If no plan exists, there is no target.
- Once the named ladder is in sight, it outranks the frontier (option A). Other ladders stay plain doors, because one of them, (8,5), leads to a dead end.
- The AI still sees only the lit circle, and nothing static is written into its memory.

**Three rounds.**
- Round 1 (the first builder) never fired live. In #114, FIX equaled FAULT frame for frame in 3 of 3 pairs. The walk toward STEVEN has no goal map ("by looking around: not told yet"), and round 1 only looked for a way toward a goal.
- Round 2 added a way through for walks with no goal: the way toward the farthest map from the ladder the player arrived by.
- Round 2b is mine. I followed the way-through marks from arrival to arrival, using each ladder's destination in maps.json. In round 2a's file, 21 of 29 marks pointed straight back at the ladder the player arrived by, and 11 starting points looped for ever. One example is VICTORY ROAD B1F (30,25) and B2F (30,25) pointing at each other. The extractor now gives no way through in that case. GRANITE's crossing (4,21) to (28,21), (28,21) to (29,13), (29,13) to (25,13) is unchanged. A test now checks this; it failed on round 2a's file (22 failures) and passes on 2b.

**Live A/B.** FIX against FAULT (the same code with ways.json removed), run from #113's B1F starts.
- On every pair the discriminator was checked first on the FAULT arm.
- #115 (round 2a) and #116 (final code) give six pairs. #116's pair C3 is vacuous by the pre-registered judge, because FAULT's first B2F stay never lit the exit at all.
- FIX's first B2F stay took 101 to 141 steps; FAULT took 204 to 347.
- FIX's B1F stay that arrives at (29,13) took 4 steps in 6 of 6; FAULT took 32 to 44.
- FIX's first B1F stay took 50 to 80 steps and always left by the named ladder.
- Dark steps and dark wild battles were fewer for FIX in 6 of 6.
- The first frame on 1F after the crossing came earlier for FIX in 6 of 6, by 28k to 117k frames.
- Every FIX dark stay began with a `way` decide. No `way` decide happened off the dark maps, and none named the ladder its stay arrived by.
- All 12 runs had CLEAN purity, were ended by the AI at ch7_steven, and delivered the letter.

**The misses.**
- My prediction P1 (B2F at most 135 steps) missed once, at 141.
- The diagnosis's line, "B2F at most about 120 steps", was exceeded in 3 of 6 pairs (127, 141, 127).
- No run went above 150, so the escalation to option C is not indicated.
- Overall time to STEVEN was earlier for FIX in only 3 of 6. The cause was the detour after the crossing: a `pick_up` errand for the item ball at 1F (17,7), which the game reported was no longer there, followed by a goal-less look-around that left the cave for DEWFORD. It happened after the crossing in FIX 4 of 6 and FAULT 1 of 6. It is a separate defect, because the fact never applies on 1F. Whether the faster crossing makes it likelier is a frequency question these runs cannot answer.

**Controls.**
- Lit maps (#117): ROUTE 106 and GRANITE 1F decision streams were identical with frames up to B1F in 3 of 3 pairs, then differed at the first B1F decide.
- Chapters 1-5 replay (#118): the base and FIX were identical with frames on L1 (566 records) and C1L4 (739 records). The planted fault arm differed at record 58, so the comparison can see a one-draw change.
- C2L4 (#119) missed the "identical" prediction as worded. Every AI record (6,091 of them, with every button press and its frame) was identical through the door warp out of RUSTBORO's Pokemon Center. Then the game finished that map load one frame sooner in FIX.
- The cause is argued, not shown, because no A-vs-A run was made. The game clock comes from the host clock, and the pinned decomp's DoTimeBasedEvents (src/clock.c:26-34) reads it on map loads but skips it inside a Pokemon Center. BP-1 recorded the same split on the same leg.

**Proof.**
- Reproduced first: dark_sim's numbers; and the base vs the fact-removed code walk the dark model identically in 15 of 15 legs.
- test_ways has 20 tests. They include two new ones: the shipped file and test fixture must equal a fresh extraction from the pinned decomp, and the never-back, never-loop check.
- Mutants, revert_p11.py v3, hashed before running: on the final tree, 28 caught and 2 redundant, exactly as predicted; the P0 control ran 159 tests.
- v2's run is not evidence. Its frozen-tree check failed because I edited the worktree while it ran.
- Gates on the final tree: 20 of 20 suites pass with the frozen-tree check. Two fixes came out of the first, unstaged gate run:
  - test_kb2 had 3 real failures (the first builder never ran it), fixed by extending its lists of world files and loaders;
  - that exposed one docstring in ways.py naming maps.json, which a loader may not do. I reworded it; the code is AST-identical to what ran live.

**Generality.** The fact covers the 7 requires_flash maps.
- After round 2b it marks 8 ways through: GRANITE's three, which are tested live; GRANITE's two side entries; one on VICTORY ROAD; and two in unused CAVE OF ORIGIN maps. All but GRANITE's three are untested live.
- VICTORY ROAD's facts come from an on-foot walk with no Surf, Strength or Rock Smash. They need an HM-aware extractor before the AI reaches it.

**Merge.** Expect conflicts with wip/ch6-bp1 at the same registration lines: MUTANT_SOURCES, RUNNERS, REVERTS, SUITES, LOADERS, the anchor count (both branches go from 7 to 8; merged it must read 9 of 9), test_kb2, and ledger ids #112 to #119. Every conflict resolves by keeping both sides. goals.py, battle.py, bossprep.py and atlas.py are untouched.

**Housekeeping.** The live stage and base were removed with their junctions unlinked first. The main sandbox's counts are unchanged (modules 4461, plugins 43, mgba 44, roms 2). The per-run records in s53/p11r1/out (94 MB) are kept for the verifier. Nothing was committed.

## P11-1, the dark GRANITE CAVE crossing: verification (the verifier, 2026-11-11)

**Verdict: CONDITIONAL PASS.** Every live claim checks out exactly against the raw records, and the forward crossing's way-through fact is right. One goal-keyed fact is wrong: B1F (4,21) -> (8,5) "toward B2F". The cause is a one-way muddy slope the extractor does not model. Fixing it is the condition. It is mechanical and does not change the through marks. All runs cited are development runs: one trajectory per seed, never a rate.

**Method.** The code was copied without .git into p11r1/verify/repo and deleted at the end. I read the worktree only, never changed it, and made no commit.

**What holds, checked independently**
- **The code the live runs used.**
  - I rebuilt the ledger's code digest of live arm B, 55a895d38c8e5143 for #116 to #119, from today's worktree. I undid only the edits logged after 12:26: one docstring line in ways.py, test_kb2.py back to HEAD in CRLF, and ledger entries #116 to #119. The digest matches exactly.
  - The round-2b ways.py has sha256 a6ac87c2. It is AST-identical to today's file once docstrings are stripped; only line 7 differs.
  - explore.py, navigator.py and ways.json match the v3 hashes.
  - My copy's frozen-tree digest, 564433ece20fc1e7, equals the builder's final gate run.
- **Seeds.** I read 202 ledgers: main, every worktree except the working copy of wf_e7452923-f06-3, and every branch tip through git show, including BP-1's c5146e53.
  - Seeds 6431-6451 appear only in ch6-p11's #112 to #119.
  - Each prediction file's sha256 equals its entry's bounds, and each batch log prints the ENTRY before its first start.
  - 6452-6460 are still free. I used none of them.
- **The step counts, recounted from the position digests** (recount.py, my own): all of these equal the builder's figures.
  - B2F, first stay: FIX 127/101/103/141/127/103 steps; FAULT 247/259/347/215/251/204.
  - B1F stay arriving at (29,13): FIX 4 in 6 of 6; FAULT 36/42/44/32/44/44.
  - First B1F stay: FIX 78/80/72/56/50/50, always leaving by (28,21).
  - Dark steps and dark battles; the first frame on 1F after the crossing (FIX earlier by 41,188 / 30,726 / 54,009 / 28,376 / 47,444 / 116,740 frames); the STEVEN frames ("FIX sooner in 3 of 6"); the detours after the crossing (FIX 4 of 6, FAULT 1 of 6).
  - #114: FIX equals FAULT.
- **Way decides.** All 126 `way` decides are on 24:8 or 24:9. None names the ladder its stay arrived by, and every one names a real ladder.
  - Purity is CLEAN in all 31 runs, with ai_bot_calls 0.
  - Every A/B run was ended by the AI with DELIVERED_STEVEN_LETTER 1 (the game's marks).
- **Controls, compared on full records** (stream_cmp.py; the eyes' timing and the order of printed sets normalised):
  - Lit: 450, 266 and 432 records identical through the first B1F record.
  - L1: A equals B on 4,301 of 4,301 records. C1L4: A equals B on 8,504 of 8,504.
  - K differs from A at record 215.
  - C2L4: A equals B for 6,091 records, then the game takes 19 frames against 18 on the map load after the Pokemon Center door. The decomp citations (clock.c:26-34, overworld.c:802/853) check out. The clock cause is argued, not shown.
  - On lit maps P11's code returns at `dark()` before any draw.
- **The fact.**
  - With the builder's door convention, my own on-foot walk agrees with ways.json on every way and all 8 through marks, except the one entry below.
  - GRANITE's crossing (4,21) -> (28,21) -> (29,13) -> (25,13) is correct: 42, 61 and 4 steps, then 37 on 1F to STEVEN.
  - Following the marks never cycles.
- **Tests and gates.**
  - test_ways: 20 OK.
  - The builder's revert_p11 v3, re-run: P0 passes 159 tests; 28 CAUGHT and 2 REDUNDANT as predicted.
  - These pass in my copy: test_kb2, test_safety_gates, check_fairness, check_purity, check_anchors (8 runners, 1,603 mutants), test_check_anchors, ledger_check (119 entries), check_paths.

**Findings**
- **V1, MAJOR: the slope.**
  - B1F (9,9) and (9,10) are MB_MUDDY_SLOPE, the only link between B1F's south part and its north part. src/field_player_avatar.c:567-581 forces a walk south on foot, so the slope only goes down.
  - extract_ways has no forced-movement rule, so it ships "from (4,21) take (8,5) toward B2F" (a 24-step walk), which is unreachable on foot. The project already measured this live: the granite_b1f_slope fixture (stuck for 120,132 frames) and the test_eyes live slope test.
  - test_ways pins the wrong fact in two tests, and the fixture draws the slope as two-way floor.
  - Probe VP2 (predicted and hashed first): adding the slope rule changes only this arrival. The 8 marks are unchanged, the walk to B2F goes from 24 to 42 steps, and exactly those two tests fail.
  - Reach: only goal-keyed walks whose goal accepts B2F use this fact.
- **V2, MINOR: the way replaces the route.**
  - An exit that is both the way's ladder and the route's first hop becomes kind "way", and lost_way keeps only "route".
  - Probe VP1: on B1F, arrived by (28,21), lost_way returns the route without the fact and None with it.
  - Mutant VM7 shows no unit test depends on the substitution.
- **V3, MINOR: a planted key passes the fairness gate.** A developer key nested inside the `toward` leaf passes RULE B (VM1). The same key as a sibling fails (VM1c). This is the house convention for leaves, not new with P11.
- **V4, MINOR: VICTORY ROAD's mark.** It is live although it was derived on foot, for a player without HMs. With a crude HM model the mark would be (8,3) rather than (30,25). The builder disclosed this as P11-y.
- **V5, NIT: `_check` is readable.** The walk lengths are META, so the gate does not stop a loader reading them; only the test_ways AST pin does (VM2).
- **V6, NIT: the AI's words quoted as the game's.** The report calls the AI's "no item ball ... any more" goal_end line "the game says". The item's flag was not read.

**My predictions.** All were hashed before running (b6caa84a). VM0, VM1, VM1c, VM2, VM7, VP1 and VP2 held. VM5 missed: an RNG draw on lit maps only is CAUGHT by test_goals KI129PartBTests (5 tests). So the unit suites can see a lit-map stream change, which is in the builder's favour.

**Not done**
- No live run. Every live claim was decidable from the records.
- No A-vs-A run for C2L4.
- The P11-x detour was confirmed from the digests but not diagnosed.

**Housekeeping**
- I deleted my copy (17,189 entries). It contained no junctions, and I created none.
- The main sandbox's counts are unchanged: modules 4461, plugins 43, mgba 44, roms 2, and no ai-p11 profile.
- The worktree is unchanged (22 status lines, no file newer than 13:46).
- In the main checkout, the only change is the pre-existing cost-ledger line, which is not mine. C: has 63 GB free.
- Kept for the lead:
  - the builder's p11r1/out/ (94 MB, judged, can be deleted);
  - starts_p11/;
  - my scripts and outputs in p11r1/verify/ (0.4 MB), with STATE.md as the run book.

## P11-2, the dark GRANITE CAVE crossing's fixes (the builder, 2026-11-12)

**What it is.** P11-2 closes the six findings of P11-1's verifier (CONDITIONAL PASS: MAJOR V1, MINOR V2 to V4, NIT V5 and V6) and diagnoses the detour after the crossing (P11-x). It is built in the worktree `ch6-p11` (branch `wip/ch6-p11`, over `f1069d9d`) and is not committed. Three builders worked on it. A session usage limit cut the first at about 8:27 PM on 2026-11-11 and the second at about 9:22 AM on 2026-11-12. Nothing was lost. The run book is `s53/p11r2/STATE.md`.

**Headline and caveat.** The fixes change no through mark in GRANITE CAVE and no decision on its forward crossing. In a live check on 3 seeds, f1069d9d and the new play code made identical decision streams. This is development work: one trajectory per seed, replayed under both codes, not a rate. The detour after the crossing comes from the test starts, not from the AI's code, so it is not fixed here. P11-1's caveat "FIX reached STEVEN sooner in only 3 of 6" rests on that artifact and does not measure the AI.

**Reproduced first.** The verifier's VP2 was run on a copy of `f1069d9d` with only the muddy slope modelled; the prediction was hashed first (`prediction_r0.txt`, bf66765f). The regenerated `ways.json` differed in one place: B1F's ways from (4, 21) lost the (8, 5) way toward B2F, and the walk from (4, 21) to B2F grew from 24 to 42 steps. The 8 through marks did not change. `test_ways` failed exactly the two tests that pinned (8, 5).

**What changed.**
- **F1 (V1).** `gates/extract_ways.py` now models the muddy slope. On foot, a step onto MB_MUDDY_SLOPE slides the player south, one tile a step, until they are off the slope or blocked. On foot the player never climbs it. Each rule is cited at the pinned decomp 731ad5bf: `src/field_player_avatar.c` 144-163, 332-350, 412-427, 443-471 and 567-581, `src/bike.c` 1022-1037, and `src/event_object_movement.c` 7673. The second builder read every cited range at that commit.
- The extractor now REFUSES a dark map, loudly and naming the map and the tile, in two cases: its walks land on a forced movement it does not model, or its ways or walk lengths change when the player is assumed to have every field HM. Each search is run twice, on foot and with every HM, and the cuttable tree joined the HM obstacles. A refused map is left out of `ways.json`, so to the AI it is not dark and the explorer decides there as it did before P11-1.
- The test fixture draws the slope one-way. `ways.json` and the fixture were regenerated (`--check` SAME, SAME). The two tests that pinned the wrong fact now say that from (4, 21) the way toward B2F is (28, 21).
- Option A is kept for the named ladder only, with its true reason. On the forward crossing, no unnamed ladder is ever in sight. On the slope's other side, arriving at (8, 5) up from B2F, the unused ladder (4, 21) leads back to 1F, away from STEVEN. If every lit ladder beat the frontier, the AI would take it.
- The ModelTests docstring and the extractor's "every one cited" claim are corrected. The model legs were re-measured on the one-way slope: FIX's first B1F stay took 46-70 steps against FAULT's 86-200.
- **F2 (V2).** In `brain/explore.py`, an exit that is both the route's first hop and the way's ladder now keeps the route's role. So `goals.lost_way`, which walks known routes only, still finds it. The verifier's VP1 is now a unit test.
- **F3 (V3).** In `check_fairness`, `ways.json`'s five leaves are now subtree False. A developer key nested inside a leaf now fails RULE B, as a sibling key does. VM1's plant sits beside the sibling plant in FairnessTests. maps.json and bosses.json are unchanged; that is a follow-up.
- **F4 (V4).** These are the seven requires_flash maps and what the extractor now does with each:
  - GRANITE CAVE B1F: shipped, 13 ways.
  - GRANITE CAVE B2F: shipped, 7 ways. The walks for both GRANITE maps meet B2F's 7 breakable rocks, which change no way and no walk length.
  - VICTORY ROAD B1F: left out, for two reasons. Its ways depend on the HMs (9 obstacles met), and its walk reaches MB_ICE at (6, 11) on the Hall of Fame. That ice is real: an independent read of the layout found 190 MB_ICE tiles.
  - VICTORY ROAD B2F: left out, because its ways depend on the HMs (4 obstacles met).
  - The three unused CAVE OF ORIGIN maps: left out, because their ways depend on Surf and Waterfall.
  - The file went from 7 maps, 45 ways, 8 through marks and 137 walk lengths to 2, 20, 5 and 42. A test pins that no VICTORY ROAD way is shipped.
- **F5 (V5).** `_check` and everything under it are now DEVELOPER, so RULE B2 refuses a loader that reads `walk_lengths`. A docstring that only mentions it does not trigger the refusal. `_source` and `_files` stay META.
- **F6 (V6).** A correction is appended to `2026-11-11-p11-dark-cave-live-ab.txt`. The line "not picked up" was the AI's own record, not the game's words. The flag `FLAG_ITEM_GRANITE_CAVE_1F_ESCAPE_ROPE` was read from #116 C1's kept end state: it is 1, so the ball was gone. The reader was checked first against the harness's own mark for FLAG_DELIVERED_STEVEN_LETTER.
- **F7 (P11-x): diagnosed, not fixed** (`s53/p11r2/P11X-DIAGNOSIS.md`).
  - The start maker's own play picked the ball up before every B1F start: the flag is 1 in all three B1F start states and 0 in the three G1F ones.
  - The B1F starts restore the AI's world memory, which still lists the ball, but start a new goal memory, which does not record the pick-up.
  - Reproduced offline on the real start memory and the real code: the errand chooser returns (17, 7) with the new goal memory and None with the pick-up recorded.
  - All 5 errands in #115/#116 ended at an empty tile. Every errand run then left the cave over 1F's one-way ledges and crossed the dark again. No run without an errand left the cave.
  - The three pairs where FIX reached STEVEN later than FAULT are exactly the three where only FIX ran the errand.
  - One probe line the diagnosis cites was wrong: its tile is a wall. The second builder re-probed the floor tiles beside STEVEN's door, and the sentence stands. A dated correction is appended to the diagnosis.

**Proof.**
- **Tests.** `test_ways` has 27 tests (20 before): 7 added, 2 rewritten, FairnessTests extended.
- **FAULT side.** Each new test was run on f1069d9d's code, with the prediction hashed first. Only the F2 test fails on the old explorer. The three fairness tests fail on the old `check_fairness`. 11 tests fail on the old extractor, file and fixture, against 10 predicted; the extra is a correct failure, recorded as MISSED AS WORDED. All 27 pass on the final code.
- **Mutants.** `revert_p11.py` v5 run 2, with its predictions and the tree hashed first. P0 passes 166 tests. 45 mutants were CAUGHT and 3 REDUNDANT ALONE, as predicted, of 48. OVERALL PASS. Before it, v4's run held 47 of 48 predictions and read FAIL on one prediction's wording. That error stands in the record, and v5 corrected only that prediction and one docstring paragraph.
- **Gates.** Gates run 3 on the final tree: 20 of 20 suites exit 0, FROZEN TREE PASS, OVERALL PASS. Evidence: `2026-11-12-p11-UNITS.txt` and `2026-11-12-p11-REVERT.txt`. At 1:51 PM today the tree was still the one both runs hashed.
- **Live, #120** (seeds 6452-6454, prediction hashed first). Arm A was f1069d9d; arm B was the new play code. Both ran from P11-1's B1F starts.
  - Identical up to the first frame on 1F, with frames: 961, 821 and 716 records.
  - Identical by kind and choice: 20, 16 and 15 decisions.
  - Each dark stay's first decision was "way" in both arms.
  - Purity CLEAN, with 0 bot calls in 6 of 6.
  - Observed but not predicted: identical to the end. All six runs reached STEVEN (the game's flag, read by the harness).
  - The C1 pair ran the stale errand in both arms.
  - At 1:57 PM today the play code was still 87d5b014, the code arm B played.
- **No chapters 1-5 replay control.** F2 cannot change a decision on a lit map: `dark_way` returns None off a dark map.

**Housekeeping.**
- The worktree's sandbox staging was taken down at 9:15 AM today. `git status` shows nothing of it.
- Nine git-ignored copies of pokebot's default profile files are left in the worktree sandbox. They were created on 2026-11-11, before this round, and are not its.
- The main sandbox is unchanged: plugins 43, mgba 44, roms 2.
- No mutant temp copies remain. The lab folder holds 9.9 MB, with no links and no world.jsonl. The judged runs' actions.jsonl are kept in `s53/p11r2/out/id`.
- C: has 55 GiB free.

**Where the cuts fell.**
- First cut: about 8:27 PM on 2026-11-11, while mutants v5 run 1 and gates run 2 ran as background shells of that session. Both died with it: cut, not failed.
- Second cut: about 9:22 AM on 2026-11-12. Both jobs had already been re-run detached and had passed, and the staging was already down.

**New stops.**
1. The kit fix: start files must carry the AI's goal memory, then the B1F starts must be re-made. Until then, use the G1F starts for anything past the crossing.
2. P11-x2: should an errand over a one-way ledge be weighed, or should the AI know as static knowledge that STEVEN is in the back room? The builder recommends measuring first.
3. maps.json's and bosses.json's leaves: the same nested-key hole that V3 found in ways.json.
4. P11-y stands, now narrower: an HM-aware walk, plus ice, for VICTORY ROAD.
5. At commit: the tracked 2026-11-11 p11 REVERT and UNITS evidence files hold the v4 tree's runs.

## P11-2, the dark GRANITE CAVE crossing's fixes: verification (the verifier, 2026-11-12)

**Verdict: CONDITIONAL PASS.** One MAJOR, one MINOR and two NITs.

The shipped ways are right. I re-derived them independently from the pinned decomp, and all 20 ways and all 5 through marks agree.

The MAJOR is a one-line gap in F3: ways.json's `maps[].id` is still a subtree leaf, so a developer key nested inside it passes RULE B.

The live claims and the P11-x diagnosis are supported by the raw records and by the game's own flags.

Caveat: these are development records, one trajectory per seed. I made no live run of my own.

**What was verified.**
- A copy of the worktree ch6-p11 (f1069d9d plus the uncommitted P11-2 tree), made at 2:08 PM without .git.
- Its 9 hashed files equal `prediction_mutants_v5.sha256`. Its gate run's frozen-tree digest, d7f759c05cfd8c75, equals the builder's gates run 3.
- My predictions were hashed before every run: `vpredictions.txt` (e984b473, 2:28 PM) and `vpredictions2.txt` (f22e5b1e, 2:36 PM).
- Scripts, outputs and the run book STATE.md are in `C:/Remote Projects/_ai_lab/s53/p11r2/verify/`.

**The ways, re-derived independently.**
- I wrote my own layout reader and walk (`vgrid.py`, `vways.py`) before reading extract_ways.py's code. Each rule is taken from the pinned decomp:
  - collision, one-way walls and elevation: `event_object_movement.c` 893-905, 4641-4706, 7673, 7725;
  - ledges: `event_object_movement.c` 7631 and `field_player_avatar.c` 693;
  - the muddy slope: `field_player_avatar.c` 412-427, 443-471, 567-581, and `bike.c` 1022-1037;
  - warps;
  - the cracked floor's fall: `field_tasks.c` 801-840 and `cave_hole.inc`.
- **Result:** every take, every toward list and every through mark of GRANITE CAVE B1F and B2F agrees (`vcompare.py`: 20 ways, 5 marks, ALL AGREE). Walk lengths differ only for ledge jumps: I count a jump as 1 step, the extractor as 2. Those lengths live only in the developer-only `_check`.
- **Controls:**
  - On f1069d9d's file the comparator finds exactly V1: B1F (4, 21) toward B2F by (8, 5).
  - With the slope walked both ways, my walk reproduces V1's 24 steps.
- **Variants:**
  - Removing the breakable rocks, letting item balls be walked through, or treating people as walls changes nothing.
  - Treating the cracked floor as the fall it is changes only the (29, 2) pocket arrivals, which no one on foot can reach. From B2F (29, 2), a fall would also lead toward 1F, STEVEN's room and ROUTE 106. No take changes and no through mark changes.
- No GRANITE walk lands on a forced movement other than the slope, on any map it crosses.
- The Hall of Fame's ice is real: my reader finds 190 MB_ICE tiles, (6, 11) among them.

**The refusals, plant-tested in memory** (the decomp is never written).
- Ice on a B1F floor tile refuses both GRANITE maps. So does ice on the lit 1F at (35, 4).
- Ice on a wall tile refuses nothing.
- A breakable rock or a cuttable tree in B1F's 1-wide corridor at (3, 17) refuses both maps.
- A standing person on that same tile is shipped unchanged. A warp event planted on a plain cave tile is used as a step warp. These are VV2's latent gaps.

**Fairness.**
- RULE B: a developer key nested inside from, take, leads_to, through or toward FAILS, as it should. So does a sibling key under a way or under a map.
- The same nested plant inside `maps[].id` PASSES (VV1). On f1069d9d, VM1's plant passes too, so V3 was real on the base.
- RULE B2 refuses a loader that reads `_check` or `walk_lengths`.
- It now also refuses deciding code that reads `x.get("MAP_GRANITE_CAVE_B1F")`, which it did not on f1069d9d (VV3).

**The builder's tests and mutants, re-run on my copy.**
- The gates of the diff: 10 of 10 suites exit 0: test_ways 27, test_world 139, test_goals 462, check_fairness, check_purity, call_census, check_paths, check_anchors (8 runners, 1621 mutants), test_check_anchors 7, and ledger 120.
- `revert_p11` v5: P0 passes 166 tests. 45 mutants were CAUGHT and 3 REDUNDANT ALONE, as predicted, of 48. OVERALL PASS.
- The builder's base matrix had run on a test_ways.py edited about a minute later. I re-ran its four arms on the final file, and all came out as predicted: CTRL fails none, BX 1, BF 3, BE the same 11.
- My own mutants: setting from, take, leads_to or through back to a subtree is each CAUGHT. Two slide branches survive (VV4).

**Live #120, read from the raw records.**
- In each of the 3 pairs, arms A and B are identical up to the first record on 1F (961, 821 and 716 records) and over the whole streams (5,080, 1,120 and 936 records), frames and extras included.
- Each dark stay's first kinded decision is `way` in both arms.
- Purity is CLEAN and bot calls are 0 in 6 of 6.
- DELIVERED_STEVEN_LETTER went from 0 to 1 in all six by the harness's marks, and my own flag reader reads 1 in all six end states.
- The C1 pair ran the stale errand in both arms.
- Seeds 6452-6454 appear only in #120 (213 ledgers checked). The batch log prints the entry and prediction a3937784 before the first start.

**P11-x, re-read.**
- My own flag reader is checked against two controls: the save's map, and the STEVEN flag against the harness's marks. Both are OK in 17 of 17 states.
- It reads FLAG_ITEM_GRANITE_CAVE_1F_ESCAPE_ROPE as 0 at the three ROUTE 106 starts and the three G1F starts, and 1 at the three B1F starts.
- The B1F starts' world memories list 1F's ball at "17,7". The G1F ones list none.
- The arms pass AI_PLAYER_WORLD and no AI_PLAYER_MEMORY.
- The builder's offline repro reproduces on the P11-2 code.
- From the raw records:
  - The errand ran in exactly ab2-B-C2, ab2-B-C3, ab2-F-C2, ab3-B-C1 and ab3-B-C2. Each ended at an empty tile.
  - FIX was later than FAULT exactly in ab2 C3, ab3 C1 and ab3 C2.
- One of my predictions missed as worded. Two FAULT runs (ab3-F-C2, ab3-F-C3) were on ROUTE 106 BEFORE their crossing, after climbing back up the ladder they came down. Anchored, as the diagnosis anchors it, on the crossing's arrival at 1F (35, 3), only the 5 errand runs leave the cave afterwards. The diagnosis stands.
- In #117, all 6 lit-control runs picked the ball up on the way in, and none went back for it.

**Process across the two cuts.**
- Each prediction file's sha256 equals its .sha256 file and the value in the builder's STATE.md. Each was written before its run. None was re-hashed.
- Both cut runs hold partial output only:
  - mutants v5 run 1: its start lines;
  - gates run 2: 3 of 20 suites.
  Both are reported as cut. Their re-runs are complete, with 10 of 10 hashes OK at both ends.
- The archived pair of P11-1 evidence files equals the committed blobs, byte for byte once CRLF is turned to LF.
- F6's appended correction matches my own reads.

**Findings.**
- **VV1 (MAJOR):** `maps[].id` is still a subtree leaf. Fix: subtree False, plus "id" in the leaf test with a nested plant.
- **VV2 (MINOR):** the extractor's headline claims more than it does. A standing person, and a warp event on a tile that is not a step warp, are neither modelled nor refused. No effect today; this must be fixed before P11-y ships VICTORY ROAD.
- **VV3 (NIT):** seven map consts are now developer-only names, so RULE B2 would refuse code that reads one as a key (a latent false positive).
- **VV4 (NIT):** two slide branches are untested: a warp under a slope, and an HM obstacle under a slope.

**Housekeeping.**
- The copy is deleted (17,167 entries, no link inside), and so are the temp mutant copies.
- The main sandbox is unchanged: plugins 43, mgba 44, roms 2.
- `verify/` holds 0.4 MB and no world.jsonl. C: has 57.9 GB free.
- The worktree's git status is unchanged, and the main checkout is clean.
- No live run was made and no seed was registered, so 6455-6480 stay free.

## P11-2: the closing pass (the builder, 2026-11-12)

The closing pass closes the verifier's four findings: VV1 (MAJOR), VV2 (MINOR), VV3 and VV4 (NITs). It also files the P11-x diagnosis as a note. The changes are in test-side code and data only. No play code changed: under ai_player/brain and ai_player/knowledge, only ways.json differs from 1cf3ae6a, and only inside its developer part, _check. But ways.json is in the play digest, so the play digest moved from 87d5b014f8189cfe (#120's arm B) to 1c96c11fbbf253f7. The rest of ways.json parses identical to 1cf3ae6a's, and the loader is byte-identical and never reads _check. So #120's identity result still describes this file's decisions. Every proof is offline: no live run, no seed. The gate run drove the emulator in process for its unit suites, as P11-2's gates run 3 did. Mutants v6: 61 CAUGHT and 3 REDUNDANT of 64, as predicted, with the prediction hashed first. Gates: 20 of 20 exit 0. Tier 0: PASS. Nothing is committed. The extractor still neither models nor refuses five things (below). None of them changes today's two maps, and each must be handled before any VICTORY ROAD way ships. One proof file is incomplete: fault.out records which tests failed in the F3 arm but not why.

- **D1 (VV1, the fairness leaf).**
  - Reproduced on 1cf3ae6a (repro_base, 17 of 17 HELD): a dict nested inside maps[].id, count, _kind or a _files sha256 passes RULE B.
  - The fix: no entry of ways.json's block is a subtree now. _check's children are named one by one. The keys of _files and of walk_lengths are narrowed to their shapes.
  - The leaf test now plants a developer key in every entry that holds a value (19 plants). It has two controls: the unplanted file passes, and a value that mentions a developer key passes.
  - FAULT F1 (1cf3ae6a's check_fairness.py): only the leaf test fails. Its 14 failing subtests cover the 10 entries a subtree swallowed on 1cf3ae6a; no way leaf fails. **[Reworded by the lead after the verifier's VC1: it read "are the 10 entries that were subtrees". Only 4 entries were subtrees on 1cf3ae6a; 6 of the 10 did not exist there and were covered by `_check` or `_*`.]**
  - CONTROL F0: the copy unchanged, 166 tests pass.
  - 12 mutants: each of the 10 flags set back to True, and each of the 2 wildcards widened back to *. Each is CAUGHT by the leaf test.
  - Every entry of the block, with its class and subtree flag. No entry is left a subtree.

| Entry | Class | Subtree | Holds |
|---|---|---|---|
| _check | developer | False | a dict (three children) |
| _check.walk_lengths | developer | False | a dict keyed map\|x,y\|map |
| _check.walk_lengths.MAP_*\|*,*\|MAP_* | developer | False | a number |
| _check.left_out | developer | False | [map, [why]] pairs |
| _check.hm_obstacles | developer | False | [map, [obstacle]] pairs |
| _files | meta | False | a dict keyed by path |
| _files.*/* | meta | False | a sha256 |
| _* | meta | False | a string (_source, _kind, _made_by, _reader, _notes) |
| count | meta | False | a number |
| maps, maps[], maps[].ways, maps[].ways[] | ai | False | containers |
| maps[].id | ai | False | a string |
| maps[].ways[].from, take | ai | False | a pair of numbers |
| maps[].ways[].leads_to | ai | False | a string |
| maps[].ways[].toward | ai | False | a list of strings |
| maps[].ways[].through | ai | False | a string or null |

- **D2 (VV4, the slope's two branches).**
  - On 1cf3ae6a, the verifier's VMe and VMf each survive all 166 tests (d2base.out, prediction hashed first).
  - Two hand-made cases are added. A warp under a slope is used, at 2 steps. A rock under a slope stops the slide on foot and is recorded as met; the every-HM walk slides onto the rock's tile.
  - slide_warp_ends (VMe) and slide_through_rock (VMf) are both CAUGHT by the forced-movement test.
- **D3 (VV3, map consts as developer-only key names).**
  - Reproduced on 1cf3ae6a: 7 of the 72 developer-only names are map consts, and the probe x.get("MAP_GRANITE_CAVE_B1F") is refused.
  - The data's shape is fixed. The extractor writes left_out and hm_obstacles as [map, [..]] pairs, and ways.json was regenerated by it (--check SAME, SAME). Pairs add no key names; dict records would have made 'reasons' and 'obstacles' developer-only.
  - The tests:
    - Deciding code that reads a map const as a key is not refused.
    - A loader that reads _check, walk_lengths, left_out or hm_obstacles is still refused.
    - No map const is a developer-only name (65 names now, 0 of them map consts).
  - FAULT F3 (1cf3ae6a's check_fairness.py and ways.json together): exactly the 5 predicted tests fail.
  - Controls: d3_controls_final.out, 10 of 10 HELD.
    - The file less _check equals 1cf3ae6a's, and _check holds the same facts.
    - The fixture and knowledge/ways.py are byte-identical to 1cf3ae6a's.
    - ways.py names none of _check's keys.
    - Play digest: as in the headline.
  - 2 mutants: the writer keying either list by map const again. Each is CAUGHT by the extraction-equality test.
- **D4 (VV2, the extractor's headline).**
  - The docstring now separates two lists: WHAT IT REFUSES (TWO KINDS), and WHAT IT NEITHER MODELS NOR REFUSES TODAY.
  - The five items, each confirmed from the code:
    - a standing person (walls hold HM obstacles only);
    - a warp event on a tile that is no warp (every warp event is used on a step);
    - coord events (never read);
    - every step callback except the cracked floor;
    - the ledge landing (stricter than ShouldJumpLedge).
  - The first two are also the verifier's plants VE6 and VE7.
  - d4_confirm.out: on the five maps the GRANITE CAVE searches cross, there are 0 coord events, the only step callback is the cracked floor, no landing is refused, and every warp tile is a ladder, a door or an arrow warp.
  - The docstring says each item must be modelled or refused, with a plant test, before P11-y.
- **D5 (the P11-x note).**
  - Filed as PROJECT KNOWLEDGE/ai-research-notes/2026-11-12-P11-X-DETOUR-DIAGNOSIS.md. The body is byte for byte, the correction included. The longest line is 123 characters.
  - The new first paragraph says:
    - it is a NOTE, and who wrote it: P11-2's first builder, with the third builder's correction;
    - what the verifier re-read, including its prediction that missed as worded, and that the diagnosis stands;
    - what follows: the kit must save and restore the goal memory with a start, the B1F starts must be re-made, and P11-1's "3 of 6" is confounded by the test starts.
- **D6 (which file proves which commit).**
  - d6_evidence.py reads every p11 REVERT and UNITS file under evidence/ and archive/. It then recomputes each commit's digest with provenance's own rule.
  - P11-1's commit measured with its 6 new files untracked gives 044dacd1e4965f57. P11-2's commit gives 9c2c02b1b678e7be.
  - My runs moved P11-2's 2026-11-12 pair under archive/ by keep_earlier, as expected.

| Tree | Files that prove it |
|---|---|
| f1069d9d (P11-1), digest 044dacd1e4965f57 | archive/044dacd1e4965f57-18c3d51b/2026-11-11-p11-REVERT.txt (PASS, 28 CAUGHT + 2 REDUNDANT of 30), and the UNITS file there (PASS) |
| 1cf3ae6a (P11-2), digest 9c2c02b1b678e7be | archive/9c2c02b1b678e7be-f1069d9d/2026-11-12-p11-REVERT.txt (PASS, 45 + 3 of 48), and the UNITS file there (PASS). Moved there tonight; untracked, so commit it. |
| the closing tree (uncommitted at 1cf3ae6a), digest 5453e8e32e7bff3c | 2026-11-12-p11-REVERT.txt (PASS, 61 + 3 of 64) and 2026-11-12-p11-UNITS.txt (PASS) |
| NO committed tree: the intermediate tree 75619fd3df39c661 | 2026-11-11-p11-REVERT.txt (mutants v4 run 1, FAIL, 44 + 3 of 48) and 2026-11-11-p11-UNITS.txt (gates run 1, PASS) |
| NO committed tree: P11-1's earlier trees | archive/5da56a3912b12087-18c3d51b (REVERT PASS, UNITS FAIL), archive/a7066fb4e7ee4fa5-18c3d51b and archive/b0952b41c95c1ff4-18c3d51b (REVERT only) |

- **D7 (the final tree).**
  - Predictions hashed before their runs: pred_repro_base c2dcf211, pred_d2_base aaff9d8c, pred_fault 165cddff, pred_mutants_v6 5bbc4541 (with 10 tree files, all OK at the start and the end).
  - revert_p11 v6 (detached, 7:43 to 8:36 PM): PASS.
  - Gate driver (20 suites, detached, 7:43 to 8:09 PM): every suite exit 0, FROZEN TREE PASS.
  - check_anchors: PASS. ledger.py --check: PASS (120 entries). Tier 0: PASS.
  - git diff --stat 1cf3ae6a -- ai_player/brain ai_player/knowledge shows ways.json only, changed only inside _check (D3, control 1).
  - The sandbox staging was taken down and the main sandbox's counts are unchanged.
  - Run book: C:/Remote Projects/_ai_lab/s53/p11r2c/STATE.md.

## P11-2: the closing pass, verification (the verifier, 2026-11-12)

**Verdict: PASS.** The pass closes VV1 to VV4 and files the P11-x note. Under ai_player/brain and ai_player/knowledge, only ways.json differs from 1cf3ae6a, and only inside `_check`. I found nothing MAJOR or MINOR. There are three NITs (below).

**How it was checked.** All work was offline: no live run, no emulator, no seed. I ran on a copy of the uncommitted worktree, deleted at the end (17,169 entries). Predictions were hashed before each run:
- v_pred1 b002b086, with v_ruleb.py, v_b2.py and v_extract.py;
- v_pred2 cf9f1b02, with v_gates.py;
- v_pred3 c9449c56, with v_arrow_walk.py.

Every prediction HELD. The scripts and outputs are in C:/Remote Projects/_ai_lab/s53/p11r2c/verify/, and STATE.md there is the run book.

**RULE B, every position of ways.json planted one at a time (v_ruleb.py).** N nests a developer key inside every scalar, list elements and the [map, [..]] pairs included. S adds every developer name as a sibling in every dict. L appends a dict to every list.
- **Closing tree:** 1,069 plants (N 829, S 151, L 89).
  - 0 holes.
  - 1 plant passes, classified DEVELOPER, by design: a new walk-shaped key under `_check.walk_lengths`.
  - The other 1,068 FAIL as unclassified.
- **Gap on 1cf3ae6a:** 1,055 plants.
  - 586 holes, all where predicted: 572 nested under `_files` sha256s, 6 siblings under `_files`, the 5 `_x` strings, `count`, and the 2 `maps[i].id`.
  - The 107 plants under `_check` are DEVELOPER.
  - 362 FAIL.

**RULE B2, using each arm's own check() on a package copy (v_b2.py).**
- **Closing tree:**
  - Deciding code that reads `_check`, `walk_lengths`, `left_out`, `hm_obstacles` or any of the 42 walk keys is refused: all 46, by subscript and by .get.
  - The loader is refused 4 of 4.
  - Every map const of the file (10) read as a key: 0 refused.
  - The control passes.
  - 65 names are developer-only, and none is a map const.
- **1cf3ae6a:** 72 developer-only names. Exactly the 7 map consts are refused (GRANITE B1F and B2F, VICTORY ROAD B1F and B2F, the 3 CAVE OF ORIGIN).

**The extractor's reworded headline, planted on the pinned decomp (v_extract.py): 32 of 32 HELD.**
- **Controls:** the unplanted output equals the shipped maps and `_check`, and ice on a wall changes nothing.
- **REFUSED (two kinds):**
  - Ice at B1F (20, 12) and at 1F (35, 4).
  - Each of the 17 forced behaviours other than the slope, at B1F (3, 17). The 12 that are not water are refused with FORCED MOVEMENT naming the tile. The 5 that are water (4 currents, the waterfall) are refused with "HMs:", because on foot they are water. That is the old wording's list and the outcome is still a refusal.
  - A rock, a tree or a boulder there: refused with "HMs:".
- **NEITHER MODELLED NOR REFUSED (five):**
  - a hiker at (3, 17): shipped unchanged;
  - a warp event on the MB_CAVE tile (5, 20): taken toward STEVEN's room;
  - a coord event: shipped unchanged;
  - MB_CRACKED_ICE, MB_THIN_ICE, MB_ASHGRASS, MB_FORTREE_BRIDGE: each shipped unchanged;
  - a hand-made ledge: the jump is taken when it lands on floor (2 steps), and refused when it lands on a rock or a wall.
- **The arrow-warp clause the builder added (v_arrow_walk.py).** 1F's (37, 12) and (5, 10) are MB_SOUTH_ARROW_WARP, and (37, 12) has open floor on both sides. I made the walk use an arrow tile on a press toward its arrow, and walk across it otherwise. The maps and all 42 walk lengths are unchanged, so "NONE OF THEM CHANGES TODAY'S TWO MAPS" holds for it too.

**ways.json and the hard limits (v_compare.py, vcompare.py).**
- The parsed file equals 1cf3ae6a's outside `_check`: all 20 ways, toward lists and through marks.
- The text hunks are new lines 626-719, inside `_check` (581-720).
- `walk_lengths` is equal (42). left_out (5 pairs) and hm_obstacles (7 pairs) are each equal to the old dict, sorted, one per map.
- The P11-2 verifier's vcompare.py on the regenerated file: ALL AGREE (20 ways, 5 through marks).
- Nothing changed under brain/. No knowledge .py changed. provenance.py and the run_regression files are unchanged.
- Every changed tracked file is one the branch's rounds changed (18c3d51b..1cf3ae6a). No file was renamed or deleted.
- check_fairness.py's hunks (old 319-327) are inside the ways.json block and its comment (old 312-338).

**Gates re-run on my copy (v_gates.py).**
- test_ways: 27 OK. test_world: 139 OK. Together that is 166, the mutant runs' P0.
- check_fairness: PASS, 0 breaches.
- extract_ways --check: SAME for ways.json and the fixture.
- check_anchors: PASS (revert_p11 65 mutants, 65 edits; 8 of 8 runners).
- test_check_anchors: 7 OK.
- Tier 0: 7 of 7 exit 0.

**Mutants: not re-run, because the builder's run was on the final tree.**
- The 11 hashes in pred_mutants_v6.sha256 match the worktree at my start and at my end. mutants_v6.out has "OK" for all 11 at its start (7:43:57 PM) and its end (8:36:48 PM).
- The prediction was written at 7:43:37 PM, before the run.
- The table holds 65 entries: P0 plus 64 mutants with 65 edits (fair_check_after_meta has two edits). Every one ran.
- Result: 61 CAUGHT and 3 REDUNDANT, as predicted.

**Across the cut (the first builder was cut at about 4:50 PM).**
- Each of the 4 prediction files' sha256 equals its STATE line and its .sha256 file, and each was written before its output:
  - repro: 04:47:13 PM, against an output created at 04:48:09 PM;
  - d2: 04:48:50 PM, against a launch at 04:49:21 PM;
  - fault: 07:32:24 PM, against 07:32:26 PM;
  - mutants: 07:43:37 PM, against 07:43:57 PM.
- d2base was launched detached before the cut and ended "exit 0 at 16:51:15". The cut killed no job. Nothing was re-run or re-hashed.

**Evidence and "which file proves which commit" (v_evidence*.py, v_d6.py).**
- archive/9c2c02b1b678e7be-f1069d9d/ holds 1cf3ae6a's committed pair. Each file is the same blob (d5266fb46adb, 7e242d993d8d); the raw bytes differ only by the CRLF checkout.
- keep_earlier moved them, not a hand: the "[EVIDENCE] kept" lines are in mutants_v6.out and in gates_c1.out line 60.
- All 904 tracked evidence files are present.
- I recomputed each digest with provenance's tree_digest:
  - f1069d9d from 18c3d51b, its 6 new files untracked: 044dacd1e4965f57;
  - 1cf3ae6a: 9c2c02b1b678e7be;
  - the closing tree: 5453e8e32e7bff3c.
  - 75619fd3df39c661 (the 2026-11-11 pair) is no commit.
- The builder's table matches the files' code lines and verdicts.

**Play digest (v_digest.py).**
- 1c96c11fbbf253f7 now. With 1cf3ae6a's ways.json in place it is 87d5b014f8189cfe, the play digest the identity evidence names for arm B.
- The loader reads `data["maps"]` only, and no other play code reads ways.json or scans the folder. So #120's identity result still describes this file's decisions.

**The note (v_note.py).**
- Its body is the source s53/p11r2/P11X-DIAGNOSIS.md byte for byte, after an 18-line header. The longest line is 123 characters, and the Correction section is at the end.
- The header's facts match the records: the run book's 19:07 line, and the P11-2 verifier's "P11-x, re-read" (17 of 17, the five errand runs, ab3-F-C2 and ab3-F-C3, the three later-FIX pairs).

**NITs.**
- **VC1:** the report's F1 wording ("the 10 entries that were subtrees") drops pred_fault's caveat. Only 4 entries were subtrees on 1cf3ae6a.
- **VC2:** two run-book times are approximate ("~04:48 PM", "~07:50 PM"). The file times support them.
- **VC3:** the gate driver drove the emulator in process. The builder disclosed it, and the lead should rule on whether "no emulator" covers that.

**At commit (the lead).**
- Commit the untracked archive/9c2c02b1b678e7be-f1069d9d/ together with the rewritten 2026-11-12 pair. It is now the only proof of 1cf3ae6a.
- The note still needs its stub marker in the authoritative doc, and docs 03 to 08 need updating.
- In the main checkout, PROJECT KNOWLEDGE/cost-ledger.jsonl was modified at 8:50:09 PM, after this verification started. Neither this pass nor I wrote it.

**Housekeeping.**
- The copy is deleted; verify/ is 0.31 MB; C: has 55.7 GB free.
- The worktree's git status is the same as at my start, and the worktree's sandbox has no junction left.
- I wrote nothing in the main checkout or the worktree, and touched neither wf_e7452923-f06-3 nor pokebot-learner.

## P11-2: the closing pass, the lead's notes at the commit (2026-11-12)

The closing pass's verifier read PASS, with three NITs and two things to do at the commit. Nothing below was run live.

- **The commit holds the tree the proofs ran on.** Just before the commit the worktree's provenance digest was HEAD 1cf3ae6a + 5453e8e32e7bff3c over 5 files (`check_fairness.py`, `extract_ways.py`, `revert_p11.py`, `test_ways.py`, `ways.json`), the code line of the 2026-11-12 REVERT and UNITS pair (61 CAUGHT and 3 REDUNDANT of 64). The pair that proves 1cf3ae6a itself, moved by the drivers to `archive/9c2c02b1b678e7be-f1069d9d/`, is committed with it.
- **The 24 chapter packs were regenerated (the merge plan review's M1).** `ways.json` is a seventh file under `knowledge/world`, so each pack's recorded `result` line changes from "W1 scanned 6" to "W1 scanned 7". The branch's packs had not been regenerated since P11-1, and `make_chapter_pack.py --all --check` read 24 files differing. After the regeneration it reads CHECK: PASS, and `selftest_chapter_pack.py` reads 137 of 137 arms PASS. One line changed per file, nothing else. The packs are outside every evidence digest (the digest covers `ai_player` only).
- **VC1 (NIT), fixed in this copy.** The builder's F1 line now says the 14 failing subtests cover the 10 entries a subtree swallowed on 1cf3ae6a. Only 4 entries were subtrees there; 6 of the 10 did not exist.
- **VC2 (NIT), corrected in the run book.** Two run-book times were approximate. A dated CORRECTION line in `s53/p11r2c/STATE.md` gives the file times: the repro output was created at 4:48:09 PM, and `d6_evidence.py` was written at 7:45:24 PM. The two original lines are kept.
- **VC3 (NIT), the lead's ruling.** The gate driver drove the emulator in process for its unit suites, although the pass's limits said "no emulator". The builder disclosed it. Ruling: in a closing pass, "no emulator" means no live run and no seed. The in-process unit suites of the round's own gate driver are allowed, with the sandbox staged for them and taken down after. Future prompts say it in those words.
- **Not done, for P11-y.** The extractor neither models nor refuses five things: a standing person, a warp event on a tile that is no warp, coord events, every step callback except the cracked floor, and the ledge landing. None changes today's two maps. Each must be modelled or refused, with a plant test, before any VICTORY ROAD way ships. Also open: the test kit must save and restore the goal memory with a start, and the B1F starts must be re-made (the P11-x note).

## Appendix A. The cloud job's static draft for chapters 5-8 (as the wiring received it)

### MILESTONES-CH5-CH8 report (cloud job, static, no emulator)

Decomp: pret/pokeemerald @ `731ad5bfd6e6f265508d0efcca0ba42f9dcf5881` (commit date 2026-10-01; `git clone --depth 1`). Output: `ai_player/knowledge/seasoned/milestones_ch5_ch8_DRAFT.json` (20 milestones, 16 trainers, 7 looks). Status file: `cloud/MILESTONES-STATUS.md`. **Total wall time: 11 minutes by the session clock** (start of the first command to this report; the brief planned 45 to 60, the job needed less because the decomp scripts were read directly and the DRAFT was generated by a script from them).

### How it was made (and what was checked)
- A throw-away stdlib script (kept in the session scratchpad, not committed; the repo rule was new data files only) holds a hand-written spec per milestone and builds the JSON from the decomp: flag and var numbers are evaluated from `include/constants/flags.h` / `vars.h` (the `SYSTEM_FLAGS` expressions too), trainer ids from `opponents.h`, levels and species from `src/data/trainers.h` + `trainer_parties.h`, hint text quoted from the `.string` labels, setter lines found by scanning every `data/**/*.inc` and `src/**/*.c` for `setflag/clearflag/setvar/addvar/copyvar/trainerbattle*`. It FAILS the run if a name, label or map is not found, if the bot's tables (`sandbox-pokebot/modules/data/event_{flags,vars}/emerald.txt`) disagree with the decomp number, if a proof is not set by the file named in `decomp`, if a hint's `words` are not in its quoted text, or if a step's `told` words are not in a text of the script it names. Final run: **0 problems**.
- Map names: `include/constants/map_groups.h` does not exist at this SHA, so each MAP_ name was matched to the `"id"` of a `data/maps/*/map.json`.
- In-memory load test: `milestones.json` + the DRAFT merged (nothing written) and loaded with `ai_player.knowledge.story.Story` for BOY and GIRL: no duplicate ids; walking the story with every proof marked as it comes goes `ch4_roxanne -> ch5_stolen_goods -> ch5_rusturf_grunt -> ch5_return_goods -> ch5_devon_corp -> ch5_pokenav_tutorial -> ch5_rival_meet -> ch6_briney_house -> ch6_dewford -> ch7_steven -> ch7_brawly -> ch8_sail_slateport -> ch8_dock -> ch8_stern -> ch8_scott`; optional milestones are skipped by `current()` as designed.
- NOT done: `extract_milestones.py --verify` was not run on the DRAFT (it is not wired into that script; nothing else was touched), nothing was run in an emulator, and the bot (`taught_by` is empty).

### Chapter boundaries (a difference from the task wording)
The task text groups the Briney boat, Dewford, Brawly and Granite Cave under "chapter 5". The repo's own definition (`ai_player/knowledge/world/campaign.json`, `PROJECT KNOWLEDGE/chapter-packs/ch5..ch8.md`) is: **5** = Devon goods / Rusturf / Devon Corp / rival (orders 21-23), **6** = sail to Dewford (24), **7** = Granite Cave + Brawly (25-26), **8** = sail to Slateport + Capt. Stern (27-28), and the rival on Route 110 is chapter 9. The DRAFT follows campaign.json.

### Corrections to the earlier recon (`claude/ch5-recon-rnkfao`, CH5-REPORT.md)
1. It says the Rusturf grunt is "lvl16 GEODUDE, GEODUDE, MACHOP". That party is **MIKE_2**, an optional HIKER in the same tunnel (defeated-flag 1915 in chapter-packs/ch5.md). The scripted grunt, TRAINER_GRUNT_RUSTURF_TUNNEL (RusturfTunnel/scripts.inc:292), has one **POOCHYENA Lv 11** (src/data/trainer_parties.h:166).
2. It says "Dewford landing sets VAR_BOARD_BRINEY_BOAT_STATE=2". Line DewfordTown/scripts.inc:133 is in `DewfordTown_EventScript_SailToPetalburg` (the trip BACK); the arrival from Petalburg runs Route104/scripts.inc:394 `setvar VAR_BOARD_BRINEY_BOAT_STATE, 0`. The boat var is therefore not a proof of having landed; `FLAG_VISITED_DEWFORD_TOWN` (set by DewfordTown_OnTransition, scripts.inc:6) is.
3. It lists the stolen-goods flag as a progress marker; FLAG_DEVON_GOODS_STOLEN is set at RustboroCity/scripts.inc:287 and cleared at RusturfTunnel/scripts.inc:321, so it cannot prove anything after the tunnel. The DRAFT uses VAR_RUSTBORO_CITY_STATE / VAR_RUSTURF_TUNNEL_STATE instead.

### Per chapter: milestones in story order, with sources
Paths are relative to the decomp root. "written at" lists EVERY script line that touches the var (this is the multi-setter census); the `decomp` field of each DRAFT milestone names the one file that sets the proof for the milestone.

### Chapter 5: DEVON GOODS, RUSTURF TUNNEL, DEVON CORP, the rival

### ch5_stolen_goods: RUSTBORO CITY: the DEVON employee is robbed by a TEAM AQUA GRUNT

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- VAR_RUSTBORO_CITY_STATE >= 2 (number 16474, include/constants/vars.h:110); written at Route104:50 (`8`); Route104_MrBrineysHouse:78 (`8`); RustboroCity:88 (`7`); RustboroCity:288 (`2`); RustboroCity:482 (`3`); RustboroCity:563 (`5`); RustboroCity:741 (`8`); RustboroCity:809 (`8`); RustboroCity_DevonCorp_3F:68 (`6`); RustboroCity_Gym:20 (`1`); RusturfTunnel:323 (`4`)
- VAR_RUSTURF_TUNNEL_STATE >= 2 (number 16538, include/constants/vars.h:174); written at RustboroCity:289 (`2`); RusturfTunnel:267 (`3`)
Hint: data/maps/RustboroCity/scripts.inc:992 RustboroCity_Text_OutOfTheWay; data/maps/RustboroCity/scripts.inc:996 RustboroCity_Text_WaitDontTakeMyGoods  | words None, map RUSTBORO_CITY

### ch5_goods_employee (optional): The DEVON employee asks for help getting the DEVON GOODS back

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_INTERACTED_WITH_DEVON_EMPLOYEE_GOODS_STOLEN = 159 (include/constants/flags.h:181); set at data/maps/RustboroCity/scripts.inc:481
- VAR_RUSTBORO_CITY_STATE >= 3 (number 16474, include/constants/vars.h:110); written at the same places as listed at its first use above
Hint: data/maps/RustboroCity/scripts.inc:1000 RustboroCity_Text_HelpMeIWasRobbed  | words 'DEVON GOODS', map RUSTBORO_CITY

### ch5_rusturf_grunt: RUSTURF TUNNEL: beat the TEAM AQUA GRUNT and take back the DEVON GOODS

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_RECOVERED_DEVON_GOODS = 143 (include/constants/flags.h:165); set at data/maps/RusturfTunnel/scripts.inc:322
- VAR_RUSTBORO_CITY_STATE >= 4 (number 16474, include/constants/vars.h:110); written at the same places as listed at its first use above
- VAR_BRINEY_HOUSE_STATE >= 1 (number 16528, include/constants/vars.h:164); written at RusturfTunnel:324 (`1`)
- TRAINER_GRUNT_RUSTURF_TUNNEL: id 16, defeated-flag 1296, class TEAM_AQUA, src/data/trainers.h:196, party sParty_GruntRusturfTunnel (src/data/trainer_parties.h:166) levels [11] POOCHYENA; battle started at data/maps/RusturfTunnel/scripts.inc:292
Hint: data/maps/RustboroCity/scripts.inc:1009 RustboroCity_Text_ShadyCharacterTookOffTowardsTunnel  | words 'tunnel', map RUSTURF_TUNNEL
Fight levels (union [11]): GRUNT_RUSTURF_TUNNEL [11]

### ch5_return_goods: Return the DEVON GOODS to the DEVON employee

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_RETURNED_DEVON_GOODS = 144 (include/constants/flags.h:166); set at data/maps/RustboroCity/scripts.inc:561
- VAR_RUSTBORO_CITY_STATE >= 5 (number 16474, include/constants/vars.h:110); written at the same places as listed at its first use above
Hint: data/maps/RustboroCity/scripts.inc:1000 RustboroCity_Text_HelpMeIWasRobbed  | words 'DEVON GOODS', map RUSTBORO_CITY

### ch5_devon_corp: DEVON CORP 3F: MR. STONE's favor (the LETTER for STEVEN) and the POKéNAV

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_RECEIVED_POKENAV = 188 (include/constants/flags.h:210); set at data/maps/RustboroCity_DevonCorp_3F/scripts.inc:54
- FLAG_SYS_POKENAV_GET = 2146 (include/constants/flags.h:1352); set at data/maps/RustboroCity_DevonCorp_3F/scripts.inc:53
- VAR_DEVON_CORP_3F_STATE >= 1 (number 16527, include/constants/vars.h:163); written at RustboroCity_DevonCorp_3F:67 (`1`)
- VAR_RUSTBORO_CITY_STATE >= 6 (number 16474, include/constants/vars.h:110); written at the same places as listed at its first use above
Hint: data/maps/RustboroCity_DevonCorp_3F/scripts.inc:281 RustboroCity_DevonCorp_3F_Text_WordWithPresidentComeWithMe  | words None, map RUSTBORO_CITY_DEVON_CORP_3F

### ch5_pokenav_tutorial: Leaving DEVON CORP: the scientist adds MATCH CALL and the player must open the POKéNAV from the START menu

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_HAS_MATCH_CALL = 303 (include/constants/flags.h:329); set at data/maps/RustboroCity/scripts.inc:46
- FLAG_ADDED_MATCH_CALL_TO_POKENAV = 304 (include/constants/flags.h:330); set at data/maps/RustboroCity/scripts.inc:69
- VAR_RUSTBORO_CITY_STATE >= 7 (number 16474, include/constants/vars.h:110); written at the same places as listed at its first use above
- VAR_ROUTE104_STATE >= 1 (number 16483, include/constants/vars.h:119); written at Route104:51 (`2`); Route104_MrBrineysHouse:79 (`2`); RustboroCity:33 (`1`); RustboroCity:742 (`2`); RustboroCity:810 (`2`)
Hint: data/maps/RustboroCity/scripts.inc:1177 RustboroCity_Text_PleaseSelectPokenav  | words 'POKéNAV', map RUSTBORO_CITY

### ch5_rival_meet: South RUSTBORO: the rival (MAY or BRENDAN) meets the player and mentions MR. BRINEY

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_MET_RIVAL_RUSTBORO = 288 (include/constants/flags.h:314); set at data/maps/RustboroCity/scripts.inc:731; data/maps/RustboroCity/scripts.inc:799
- FLAG_ENABLE_RIVAL_MATCH_CALL = 253 (include/constants/flags.h:279); set at data/maps/Route104/scripts.inc:99; data/maps/Route104/scripts.inc:184; data/maps/RustboroCity/scripts.inc:740; data/maps/RustboroCity/scripts.inc:808
- VAR_RUSTBORO_CITY_STATE >= 8 (number 16474, include/constants/vars.h:110); written at the same places as listed at its first use above
Hint: data/maps/RustboroCity/scripts.inc:1042 RustboroCity_Text_MayPassedBrineyWantToBattle; also data/maps/RustboroCity/scripts.inc:1089 RustboroCity_Text_BrendanPassedBrineyWantToBattle contains 'cottage'  | words 'cottage', map ROUTE104_MR_BRINEYS_HOUSE

### ch5_rival_battle (optional): The rival's battle outside RUSTBORO (declinable)

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_DEFEATED_RIVAL_RUSTBORO = 211 (include/constants/flags.h:233); set at data/maps/RustboroCity/scripts.inc:780; data/maps/RustboroCity/scripts.inc:786; data/maps/RustboroCity/scripts.inc:792; data/maps/RustboroCity/scripts.inc:841; data/maps/RustboroCity/scripts.inc:847; data/maps/RustboroCity/scripts.inc:853
Hint: data/maps/RustboroCity/scripts.inc:1058 RustboroCity_Text_MayWantToBattle  | words None, map RUSTBORO_CITY
Fight levels (union [13, 15]): MAY_RUSTBORO_TREECKO [13, 15], MAY_RUSTBORO_TORCHIC [13, 15], MAY_RUSTBORO_MUDKIP [13, 15], BRENDAN_RUSTBORO_TREECKO [13, 15], BRENDAN_RUSTBORO_TORCHIC [13, 15], BRENDAN_RUSTBORO_MUDKIP [13, 15]


### Chapter 6: sail to DEWFORD

### ch6_briney_house: ROUTE 104: MR. BRINEY's cottage (he offers to sail to DEWFORD)

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_MR_BRINEY_SAILING_INTRO = 147 (include/constants/flags.h:169); set at data/maps/Route104_MrBrineysHouse/scripts.inc:32
Hint: data/maps/RustboroCity/scripts.inc:1042 RustboroCity_Text_MayPassedBrineyWantToBattle  | words 'cottage', map ROUTE104_MR_BRINEYS_HOUSE

### ch6_dewford: Sail with MR. BRINEY to DEWFORD TOWN

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_VISITED_DEWFORD_TOWN = 2161 (include/constants/flags.h:1372); set at data/maps/DewfordTown/scripts.inc:6
Hint: data/maps/RustboroCity_DevonCorp_3F/scripts.inc:193 RustboroCity_DevonCorp_3F_Text_MrStoneIHaveFavor  | words 'DEWFORD TOWN', map DEWFORD_TOWN

### ch6_old_rod (optional): DEWFORD TOWN: the fisherman's OLD ROD

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_RECEIVED_OLD_ROD = 257 (include/constants/flags.h:283); set at data/maps/DewfordTown/scripts.inc:84
Hint: data/maps/DewfordTown/scripts.inc:686 DewfordTown_Text_GettingItchToFish  | words None, map DEWFORD_TOWN


### Chapter 7: GRANITE CAVE (STEVEN) and BRAWLY

### ch7_steven: GRANITE CAVE: deliver MR. STONE's LETTER to STEVEN

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_DELIVERED_STEVEN_LETTER = 189 (include/constants/flags.h:211); set at data/maps/GraniteCave_StevensRoom/scripts.inc:10
- FLAG_REGISTERED_STEVEN_POKENAV = 305 (include/constants/flags.h:331); set at data/maps/GraniteCave_StevensRoom/scripts.inc:22
Hint: data/maps/RustboroCity_DevonCorp_3F/scripts.inc:193 RustboroCity_DevonCorp_3F_Text_MrStoneIHaveFavor  | words 'STEVEN in DEWFORD', map DEWFORD_TOWN

### ch7_flash (optional): GRANITE CAVE 1F: the HIKER's HM FLASH

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_RECEIVED_HM_FLASH = 109 (include/constants/flags.h:129); set at data/maps/GraniteCave_1F/scripts.inc:10
Hint: data/maps/GraniteCave_1F/scripts.inc:20 GraniteCave_1F_Text_GetsDarkAheadHereYouGo  | words None, map GRANITE_CAVE_1F

### ch7_gym_trainers (optional): The DEWFORD GYM's trainers

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- TRAINER_TAKAO: id 179, defeated-flag 1459, class BLACK_BELT, src/data/trainers.h:2152, party sParty_Takao (src/data/trainer_parties.h:2155) levels [13] MACHOP; battle started at data/maps/DewfordTown_Gym/scripts.inc:191
- TRAINER_JOCELYN: id 425, defeated-flag 1705, class BATTLE_GIRL, src/data/trainers.h:5104, party sParty_Jocelyn (src/data/trainer_parties.h:5592) levels [13] MEDITITE; battle started at data/maps/DewfordTown_Gym/scripts.inc:201
- TRAINER_LAURA: id 426, defeated-flag 1706, class BATTLE_GIRL, src/data/trainers.h:5116, party sParty_Laura (src/data/trainer_parties.h:5600) levels [13] MEDITITE; battle started at data/maps/DewfordTown_Gym/scripts.inc:211
- TRAINER_BRENDEN: id 572, defeated-flag 1852, class SAILOR, src/data/trainers.h:6868, party sParty_Brenden (src/data/trainer_parties.h:7662) levels [13] MACHOP; battle started at data/maps/DewfordTown_Gym/scripts.inc:221
- TRAINER_CRISTIAN: id 574, defeated-flag 1854, class BLACK_BELT, src/data/trainers.h:6892, party sParty_Cristian (src/data/trainer_parties.h:7678) levels [13] MAKUHITA; battle started at data/maps/DewfordTown_Gym/scripts.inc:231
- TRAINER_LILITH: id 573, defeated-flag 1853, class BATTLE_GIRL, src/data/trainers.h:6880, party sParty_Lilith (src/data/trainer_parties.h:7670) levels [13] MEDITITE; battle started at data/maps/DewfordTown_Gym/scripts.inc:241
Hint: data/maps/DewfordTown/scripts.inc:631 DewfordTown_Text_GymSign  | words 'BRAWLY', map DEWFORD_TOWN_GYM
Fight levels (union [13]): TAKAO [13], JOCELYN [13], LAURA [13], BRENDEN [13], CRISTIAN [13], LILITH [13]

### ch7_brawly: BRAWLY: the KNUCKLE BADGE

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_DEFEATED_DEWFORD_GYM = 1265 (include/constants/flags.h:1320); set at data/maps/DewfordTown_Gym/scripts.inc:150
- FLAG_BADGE02_GET = 2152 (include/constants/flags.h:1360); set at data/maps/DewfordTown_Gym/scripts.inc:151
Hint: data/maps/DewfordTown/scripts.inc:631 DewfordTown_Text_GymSign  | words 'BRAWLY', map DEWFORD_TOWN_GYM
Fight levels (union [16, 19]): BRAWLY_1 [16, 16, 19]

### ch7_exp_share (optional): Back in RUSTBORO: MR. STONE thanks the player for the LETTER (EXP. SHARE)

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_RECEIVED_EXP_SHARE = 272 (include/constants/flags.h:298); set at data/maps/RustboroCity_DevonCorp_3F/scripts.inc:162
Hint: data/maps/RustboroCity_DevonCorp_3F/scripts.inc:237 RustboroCity_DevonCorp_3F_Text_CountingOnYou  | words None, map RUSTBORO_CITY_DEVON_CORP_3F


### Chapter 8: sail to SLATEPORT and CAPT. STERN

### ch8_sail_slateport: Sail with MR. BRINEY from DEWFORD to SLATEPORT CITY

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_VISITED_SLATEPORT_CITY = 2167 (include/constants/flags.h:1378); set at data/maps/SlateportCity/scripts.inc:14
Hint: data/maps/RustboroCity_DevonCorp_3F/scripts.inc:193 RustboroCity_DevonCorp_3F_Text_MrStoneIHaveFavor  | words 'SLATEPORT', map SLATEPORT_CITY

### ch8_dock: STERN'S SHIPYARD: DOCK cannot use the DEVON GOODS, CAPT. STERN went off

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_DOCK_REJECTED_DEVON_GOODS = 148 (include/constants/flags.h:170); set at data/maps/SlateportCity_SternsShipyard_1F/scripts.inc:15
Hint: data/maps/RustboroCity_DevonCorp_3F/scripts.inc:193 RustboroCity_DevonCorp_3F_Text_MrStoneIHaveFavor  | words 'SHIPYARD', map SLATEPORT_CITY_STERNS_SHIPYARD_1F

### ch8_stern: OCEANIC MUSEUM: deliver the DEVON GOODS to CAPT. STERN and beat two TEAM AQUA GRUNTs

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_DELIVERED_DEVON_GOODS = 149 (include/constants/flags.h:171); set at data/maps/SlateportCity_OceanicMuseum_2F/scripts.inc:72
- VAR_SLATEPORT_OUTSIDE_MUSEUM_STATE >= 1 (number 16594, include/constants/vars.h:230); written at MauvilleCity_Gym:91 (`3`); SlateportCity:81 (`2`); SlateportCity:853 (`3`); SlateportCity_OceanicMuseum_2F:75 (`1`)
- TRAINER_GRUNT_MUSEUM_1: id 20, defeated-flag 1300, class TEAM_AQUA, src/data/trainers.h:244, party sParty_GruntMuseum1 (src/data/trainer_parties.h:218) levels [15] CARVANHA; battle started at data/maps/SlateportCity_OceanicMuseum_2F/scripts.inc:27
- TRAINER_GRUNT_MUSEUM_2: id 21, defeated-flag 1301, class TEAM_AQUA, src/data/trainers.h:256, party sParty_GruntMuseum2 (src/data/trainer_parties.h:226) levels [14, 14] ZUBAT/CARVANHA; battle started at data/maps/SlateportCity_OceanicMuseum_2F/scripts.inc:33
Hint: data/maps/SlateportCity/scripts.inc:964 SlateportCity_Text_EveryoneCallsHimCaptStern  | words 'MUSEUM', map SLATEPORT_CITY_OCEANIC_MUSEUM_1F
Fight levels (union [14, 15]): GRUNT_MUSEUM_1 [15], GRUNT_MUSEUM_2 [14, 14]

### ch8_scott: SLATEPORT CITY, outside the museum: SCOTT thanks the player and registers in the POKéNAV

Proofs (number; where the game sets it; `decomp` file in the DRAFT is the first):
- FLAG_ENABLE_SCOTT_MATCH_CALL = 215 (include/constants/flags.h:237); set at data/maps/SlateportCity/scripts.inc:73
- VAR_SLATEPORT_OUTSIDE_MUSEUM_STATE >= 2 (number 16594, include/constants/vars.h:230); written at the same places as listed at its first use above
Hint: data/maps/SlateportCity/scripts.inc:1281 SlateportCity_Text_YouDroveTeamAquaAway  | words None, map SLATEPORT_CITY

### The 7 "looks" added (what a person recognises on screen; from map.json `graphics_id`, value from include/constants/event_objects.h)
| look | gfx id | decomp constant | object (map, script) |
|---|---|---|---|
| mr_briney | 21 | OBJ_EVENT_GFX_EXPERT_M | Route104_MrBrineysHouse, Route104_MrBrineysHouse_EventScript_Briney |
| steven | 134 | OBJ_EVENT_GFX_STEVEN | GraniteCave_StevensRoom, ..._EventScript_Steven |
| brawly | 126 | OBJ_EVENT_GFX_BRAWLY | DewfordTown_Gym, DewfordTown_Gym_EventScript_Brawly |
| old_rod_fisherman | 50 | OBJ_EVENT_GFX_FISHERMAN | DewfordTown, DewfordTown_EventScript_OldRodFisherman |
| mr_stone | 48 | OBJ_EVENT_GFX_GENTLEMAN | RustboroCity_DevonCorp_3F, ..._EventScript_MrStone |
| dock | 19 | OBJ_EVENT_GFX_MAN_1 | SlateportCity_SternsShipyard_1F, ..._EventScript_Dock |
| capt_stern | 46 | OBJ_EVENT_GFX_SCIENTIST_1 | SlateportCity_OceanicMuseum_2F, ..._EventScript_CaptStern |

Other map.json facts quoted in the notes: the RustboroCity coord events (StolenGoodsTrigger0 data/maps/RustboroCity/map.json:342, HelpGetGoodsTrigger0 :387, ReturnGoodsTrigger0 :423, RivalTrigger0 :459, each with its `var`/`var_value` and x,y), Route104 RivalTrigger (Route104/map.json:545), Route116 BrineyTrigger (:440), GraniteCave_B1F `"requires_flash": true` (GraniteCave_B1F/map.json:7) and 1F `false` (:7), the 1F -> Steven's room warp (GraniteCave_1F/map.json:70).

### Milestones whose proof is UNCERTAIN, and why
1. **Var-only proofs on VAR_RUSTBORO_CITY_STATE** (ch5_stolen_goods, ch5_goods_employee, ch5_rusturf_grunt, ch5_return_goods, ch5_devon_corp, ch5_pokenav_tutorial, ch5_rival_meet): the var is written at 11 places (listed under ch5_stolen_goods) and two of them jump straight to 8 (Route104/scripts.inc:50 and Route104_MrBrineysHouse/scripts.inc:78). I could not find a way to reach those two before states 5-7 (Briney's house objects are hidden from the theft, RustboroCity/scripts.inc:294-295, until DevonCorp_3F:63-64), and the milestones that are flag-backed (all but ch5_stolen_goods and the var half of ch5_goods_employee) cannot be fooled by it; but the two var-only ones read as done in any later state, which is the intent (a monotonic counter), not a measured fact.
2. **ch5_rival_meet**: FLAG_MET_RIVAL_RUSTBORO is set at two lines (RustboroCity/scripts.inc:731 MAY branch, :799 BRENDAN branch) and FLAG_ENABLE_RIVAL_MATCH_CALL at four (RustboroCity:740, :808, Route104:99, :184) - the same event for the two genders and the two places the rival can be met, so consistent; the state-8 var is also written without the meeting by the two jump-to-8 lines in (1).
3. **ch5_rival_battle** is marked optional on my reading that the battle is a YES/NO prompt and that sailing hides the rival (Route104_MrBrineysHouse/scripts.inc:12 hides the Rustboro rival on every entry once the POKéNAV is held, and :80 on sailing (FLAG_HIDE_RUSTBORO_CITY_RIVAL)); not run. All six variants set the same flag (DEFEATED_RIVAL_RUSTBORO at RustboroCity/scripts.inc:780, 786, 792, 841, 847, 853), so the proof is the flag, not a trainer.
4. **ch6_briney_house**: FLAG_MR_BRINEY_SAILING_INTRO (Route104_MrBrineysHouse/scripts.inc:32) is set BEFORE the yes/no, so it proves "talked to MR. BRINEY", not "sailed". Sailing has no durable flag; the arrival proof is ch6_dewford's VISITED_DEWFORD_TOWN.
5. **ch7_steven**: no line of dialogue names GRANITE CAVE (grep -i granite over data/maps/*/scripts.inc, data/scripts, data/text finds only STEVEN's later METEOR FALLS and Match Call lines). The route (ROUTE 106 mouth, 1F, dark B1F, 1F door at (5,10)) is read from the warps; whether B1F can be crossed without FLASH was not run (FLASH needs BADGE02, i.e. BRAWLY first, but a dark map normally only limits the view).
6. **ch8_dock**: that DOCK's script also sets FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA (SlateportCity_SternsShipyard_1F/scripts.inc:16) and that the 11 TEAM AQUA objects in SlateportCity/map.json hide with it is read from the data; that they physically block the museum door was not run. If they do not, ch8_dock is not a gate and should become optional.
7. **Looks by graphics id are not unique** (mr_briney is the generic EXPERT_M sprite, the fisherman the generic FISHERMAN, DOCK the generic MAN_1, STERN a generic SCIENTIST_1): the eyes need the map as well as the figure.
8. **ch7_brawly**: FLAG_RECEIVED_TM_BULK_UP is set in two places in the gym script (DewfordTown_Gym/scripts.inc:174 and :181) and not at all if the bag is full, so it is deliberately NOT a proof.
9. **ch8_stern**: VAR_SLATEPORT_OUTSIDE_MUSEUM_STATE is written at four places (SlateportCity_OceanicMuseum_2F:75 ->1, SlateportCity:81 ->2, SlateportCity:853 ->3, MauvilleCity_Gym:91 ->3); the proofs use >= 1 and >= 2, which the later writes only raise.
10. **MR. BRINEY at DEWFORD offers SLATEPORT only after FLAG_DELIVERED_STEVEN_LETTER** (DewfordTown/scripts.inc:12), so chapter 7's STEVEN must precede ch8_sail_slateport; the campaign order already has it that way.

### Not found (written as null / left out, never invented)
- **No line of dialogue names GRANITE CAVE**, so ch7_steven's hint points at DEWFORD (MR. STONE: "a LETTER to STEVEN in DEWFORD", DevonCorp_3F) and the cave steps carry no `told` words.
- **No line tells the player to bring the DEVON GOODS back** to the employee (ch5_return_goods reuses the employee's "I have to get the DEVON GOODS back!" text; the return is triggered by coord events / talking to him).
- **No line names where CAPT. STERN is**: the DOCK says "CAPT. STERN went off somewhere" (SlateportCity_SternsShipyard_1F/scripts.inc, label ..._Text_MeetDockDeliverToStern) and a Slateport townsperson says he "built the MUSEUM" (SlateportCity/scripts.inc:965, label ..._Text_EveryoneCallsHimCaptStern); ch8_stern uses the latter, and the museum 2F steps carry no `told`.
- `waypoint`: null for every new milestone (none chosen). `taught_by`: empty for every new milestone (no bot function was mapped). `gendered_maps`: {} (no new gendered map; the rival's two texts differ by gender but share one script).
- Left out on purpose: HM STRENGTH from WANDA's boyfriend (FLAG_RECEIVED_HM_STRENGTH, RusturfTunnel/scripts.inc:57; a later errand after a boulder is broken), TM STEEL WING / TM BULK UP / the GREAT BALL (item gifts, no flag of their own that is a clean proof), the ROUTE 116/104/106/107/109 optional trainers (see the chapter packs).
- Wild levels, move sets and held items were not captured (only trainer party levels and species).

### Levels the chapters need (from src/data/trainer_parties.h; for the train-before-a-fight errand)
Rusturf GRUNT Lv 11 (one POOCHYENA); rival Lv 13 and 15 (all six variants: 13, 15); Dewford gym trainers Lv 13 (one mon each); **BRAWLY Lv 16, 16, 19** (MACHOP, MEDITITE, MAKUHITA with SITRUS BERRY); museum GRUNTs Lv 15 and 14, 14. The next boss is chapter 9's rival on Route 110 (campaign level band 18-20).
