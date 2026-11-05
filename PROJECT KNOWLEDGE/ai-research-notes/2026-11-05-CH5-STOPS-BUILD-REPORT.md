# Chapter 5's two stops: build report (2026-11-05, DEVELOPMENT, not graded)

> A NOTE, not a source of truth (`00-READ-THIS-FIRST.md`). It collects the `ch5-stops` workflow's own outputs: two
> designs (their recon), an adversarial critic, the builder (worktree `wf_5eff42ad-346-4`) and an independent
> verifier. The code it describes is on `main` only once `07` records the merge. The evidence for the builder's live
> runs is `ai_player/evidence/2026-11-05-ch5-stops-development.txt`; the verifier's runs are ledger #92-#95, whose
> artefacts were in a session scratchpad and are summarised here (they were not kept).

## 1. The builder's report

### Chapter 5's two stops: built and proven live (DEVELOPMENT, not graded)

**Headline: both stops are fixed.** Starting from the three BADGE-1 chain ends, the new code reached `ch5_rival_meet` and beat the rival in **3 of 3** runs (ledger #91). The 2026-11-01 probe stopped in 3 of 3. Each start is one sample, not a rate. The tunnel grunt needed no AI-player code: only data (`milestones.json`) and gate code (a verify check, an 8th plant, a rewritten pin, tests, a mutant). The forced menu needed new AI-player code: `skills/instructed.py`, the POKéNAV eyes and the player's name.

### What was built
- **`skills/instructed.py`, the instructed choice.** A menu a scene forces is chosen by the words read since the player was last free:
  - **How an option is named.** A page names an option when it says every word of the label (words of 3+ letters, the player's own name left out). Pages are read newest first. If two options are named, nothing is chosen.
  - **Where it plays.** `mode._story_menu` passes it script multichoices and the POKéNAV's three menus. A field menu nothing names is the same stop as before. A POKéNAV menu nothing names is backed out of with B. A grid is refused.
  - **Bounds.** EPISODE_BUDGET, MAX_DECISIONS, B_REFUSALS and FIELD_CHOICES_MAX, plus STILL_PASSES_MAX, which the mutant proof showed was needed.
  - **Faults.** `AI_PLAYER_FAULT_NO_INSTRUCTED` and `AI_PLAYER_FAULT_INSTRUCTED_MISSTEP`.
- **Eyes.**
  - `pokenav_view` / `pokenav_wait`: the main menu (all three tutorial handlers), the MATCH CALL list by name, the entry's CALL/CANCEL, and the call-exit wait. They read `gPokenavResources`; the handlers are named by `get_symbol_name`, because two of them are static functions in two files.
  - "the POKéNAV" is now a named scene.
  - `multichoice_grid` is a reclassification, and the grid keeps its options and cursor.
  - `PlayerState.name`. The mode and the handler names are never exposed to the brain.
- **Grunt.**
  - `looks.aqua_member` (gfx 117 and 118).
  - The step is now `[go RUSTURF_TUNNEL, talk aqua_member]`.
  - `--verify` checks that a step's figure stands on its map. The plants went from 7 to 8, and exactly 8 were found.
  - `campaign.json` and the 48 chapter packs were regenerated; only a sha changed.

### Critic findings (all applied; MENU-2 applied as a rebuttal)
- **MENU-1 (MAJOR), applied.**
  - The instruction is the transcript of field pages since the player was last free. A re-capture adds to it; it never replaces it.
  - `used` is cleared only for the kind that was re-captured.
  - The unit test shows the difference: under replace, the POKéNAV main menu names nothing; under append, it names MATCH CALL.
  - L4 was rewritten to predict VAR 6→7 and the full order. It ran live twice: SAVE, POKéNAV, MATCH CALL, MR. STONE, CALL, B, B, with VAR 6→7.
- **MENU-2, rebutted with evidence.** Under the followed-once rule G3 is REDUNDANT on the live scene: the call's pages name only MR. STONE, who is already used. G3's FAULT/CONTROL is a synthetic unit pair: a call page that names the HOENN MAP is chosen only when app pages count. Mutant G447 is CAUGHT. L3 was not run.
- **MENU-3, applied.** E7 is now described as a reclassification, and the kind tuple in screens.py includes `multichoice_grid`. One residual difference: on the blackboard, the stop's text changes from "unexpected multichoice" to "unexpected multichoice_grid". There is still no press.
- **MENU-4, applied.** The message-box buffer is used only by a run that began inside the scene. The CONTROL test shows a stale buffer names nothing once the player has been free. Mutants G456 and G457 are CAUGHT.
- **MENU-5, applied.** The handler set covers HandleMainMenuInput, the Tutorial handler and the EndTutorial handler, with subtests. Live runs chose under the Tutorial handler and backed out under EndTutorial.
- **MENU-6, applied.** Every batch has seeds, run counts and falsifiers, registered by sha256 before its runs. C4 is labelled an eyes-leak determinism check.
- **GRUNT-1, applied.** Each C2 run has a vacuity guard and reports frames to its first tunnel look.
- **GRUNT-2, applied.** The chapter-1 legs are labelled identical by construction. Three chapter-3 legs (the woods) were added.
- **GRUNT-3, applied.** The headline now says the grunt needed no AI-player code (census: goals.py unchanged).

### Offline proof
- **Unit suites, all OK:** test_goals 320, test_eyes 63, test_hands 57, test_world 132, test_kb2 123, test_host 37.
- **Static gates, all PASS:** purity, fairness (0 breaches), census (0 MISSING), ledger, and the milestones/world/packs checks.
- **The new tests on the base code:** 12 FAIL and 28 ERROR of 46. Every FAULT side fails there.
- **Mutants:** 35 new step-5 mutants and 4 host mutants, all CAUGHT.
- **Lanes:** the full lane is **REGRESSION: PASS (34 suites, 4,987.9 s)**. Within it, revert_step5 had 458 CAUGHT and 2 REDUNDANT of 460, and revert_r1 had 559 CAUGHT and 1 REDUNDANT of 560. The quick lane PASSed (21 suites).

### Live proof (seeds 6001-6036, ledger #86-#91)
| Batch | Arm | Result |
|---|---|---|
| menu / menu2 (C1 forced menu) | new code | 6 of 6, VAR 6→7 in 3,013-3,113 frames, exact choice order, 1 call-exit press each |
| menu / menu2 (C1 forced menu) | base + FAULT | 0 of 5; each spun 30,000 one-frame stops |
| menu / menu2 (C1 forced menu) | misstep | 2 of 2, VAR 6→7 |
| grunt C3 (tunnel) | new step | 3 of 3 in 9,237-15,597 frames, each by `talk:aqua_member` |
| grunt C3 (tunnel) | base | 1 of 3, by a chat |
| grunt C2 (Route 116) | new step | 2 of 2 non-vacuous (48,748 and 68,521 frames); seed 6016 VACUOUS |
| grunt C2 (Route 116) | base | 0 of 3 |
| control (chapters 1-4) | A vs B | 6 of 6 pairs identical (decide, goal, goal_end, presses, totals, end marks) |
| probe (chain ends) | new code | 3 of 3 reached `ch5_rival_meet` |

Purity was CLEAN in every run.

**One prediction failed:** grunt P5's world-size clause held in 10 of 12, not 12 of 12. Seed 6016 (one trajectory in both arms) wrote a 774 MB world.jsonl. It was measured and not kept. This is the Route 116 churn the grunt design's section 10 names.

Evidence: `ai_player/evidence/2026-11-05-ch5-stops-development.txt`, with each prediction quoted verbatim, the judged lines, notes on the failure, the rescue and the woods inference, and the drivers. The `2026-11-05-regression-*` files hold the full lane's evidence.

### Stops and what was left out of scope

- Stop 1 (the forced START menu and the POKeNAV MATCH CALL tutorial after ch5_devon_corp) is RESOLVED by skills/instructed.py plus the POKeNAV eyes. From the C1 end state the new code passed in 6 of 6 runs; base code and the FAULT switch passed in 0 of 5. From the chain ends, 3 of 3 runs passed ch5_pokenav_tutorial.
- Stop 2 (the ch5_rusturf_grunt `follow` step that steered nowhere) is RESOLVED by data: a talk step to looks.aqua_member. From the tunnel 3 of 3 runs passed (base 1 of 3, by a chat); from Route 116, 2 of 2 non-vacuous runs passed (base 0 of 3). From the chain ends, 3 of 3 runs beat the grunt.
- Not fixed, seen on the way (out of scope): (a) the base code's unexpected-menu stop spins one play-loop pass a frame. (b) A Route 116 trajectory (seed 6016) wrote a 774 MB world.jsonl in 200,000 frames and never decided inside the tunnel; this is the after-battle break churn the grunt design's section 10 names. (c) Every grunt battle ends the battle skill with 'the battle: budget' while the game records the win. (d) The call's first frame still decodes garbage text; it is never read, because app pages are never an instruction. (e) PROJECT KNOWLEDGE 03/04/06/07 were not edited (left for the wrap-up).

### Ledger entries (builder)

- #86 ch5stops_smoke, development, seed 6001, prediction sha256 5b00c8cc4ced8f3155f780351c24e25eb73983a44904ae0a9d600b9dae598218 (done: S1-S3 held)
- #87 ch5stops_menu, development, seeds 6002-6006, prediction sha256 8b3982267ea530c3e76feb67a5cbab78871b3ea0803eee613641db2366642eb3 (done)
- #88 ch5stops_menu2, development, seeds 6007-6010, prediction sha256 1d3b1ea7b4ad7b7b82c883d2e29f3ea26ddc6412387a793f7186a83be09404df (done)
- #89 ch5stops_grunt, development, seeds 6011-6016, prediction sha256 c9f4a621ba60f3fabe9706aed0b981a44dff90a44731417978c0fd44e2354a69 (done; P5 failed on world size)
- #90 ch5stops_control, development, seeds 6031-6036, prediction sha256 5a318c1b6b382bf2742b37ef73ba5f13ab78a88bb5a18b47d117502667e75d87 (done)
- #91 ch5stops_probe, development, seeds 6021-6023, prediction sha256 f7860a8fe79deda777c80b04903caa9e92643c26c9052b233ee6d22c117ada71 (done)

## 2. The critic's findings (before the build; the builder applied or rebutted each, section 1)

### MENU-1 (MAJOR): A re-captured 'Please select the POKeNAV.' wipes the instruction, so the AI gets stuck for good inside the tutorial POKeNAV, and L4's prediction would still read PASS

- **Target:** MENU 1.2 (re-capture replaces the instruction) + 6 L4
- **Evidence:** Section 1.2 says a field capture whose pages differ is a NEW instruction: the pages are replaced and `used` is reset. On the loop path (RustboroCity/scripts.inc 62-66: msgbox PleaseSelectPokenav, then goto MatchCallTutorial) the instruction becomes the single page 'Please select the POKeNAV.'. I ran the design's own prototype rule (proto_named.named) on that page, via review/loop_recapture.py. Forced menu: POKeNAV. POKeNAV main menu with POKeNAV used: None. MATCH CALL list: None. Options: None. The prototype's own loop case passes only because it APPENDS the page (SCENE + LOOP gives MATCH CALL), which contradicts 1.2. With nothing named, step 6 presses B. In FORCE_CALL_READY the decomp refuses B on the main menu (pokenav_menu_handler.c:261 HandleMainMenuInputTutorial: B and any A other than MATCH CALL give PlaySE(SE_FAILURE)) and on the list (pokenav_match_call_list.c:120 'Cant exit Match Call menu before calling Mr Stone').
  So the bound of 2 refused Bs returns False INSIDE the app. The next play_out pass dispatches on_menu again with the same app-blind instruction, which loops until the play-loop bound, the same failure shape as today's 99,643 spins. L4 ('picking BAG first ... The AI then chooses POKeNAV on the newly captured instruction') predicts only the first choice, so its fixture would show PASS while the run never reaches VAR 7.
- **Fix asked for:** Keep every page read since the scene began (since the player was last free) as the instruction: append a re-capture, do not replace. Reset `used` only for the menu kind re-captured. Better still, key `used` by (kind, label, page). Rewrite L4 to predict VAR_RUSTBORO_CITY_STATE 6 -> 7 and the full choice order, not just POKeNAV. Add a unit test for the loop: the main menu after a 'Please select' capture must name MATCH CALL.

### MENU-2 (MINOR): L3's prediction 'CALL chosen at least twice' does not follow from the design's own capture rule

- **Target:** MENU 6 L3 (FAULT G3) and the G3 guard row
- **Evidence:** MR. STONE's call text (data/text/match_call.inc MatchCall_Text_MrStone1) contains 'called' and 'calling' but never the whole word 'call'. review/g3_mutant.py runs the prototype with the call pages captured as a new instruction (1.2's replace semantics). List: MR. STONE named again ('MR. STONE: Oh? Milo!'). Options: None. So CALL is chosen ONCE: the mutant re-opens MR. STONE, nothing is named, B cancels, then the list is used up. Only an APPEND mutant that also resets `used` gives CALL again ('Please give our PRESIDENT a call.'). As specified, the FAULT arm can come out 'wrong', or read as the guard being redundant, depending on mutant details the design leaves out.
- **Fix asked for:** Specify the mutant exactly: capture inside apps, with replace or append semantics. Predict what that mutant actually produces (for replace: 'MR. STONE chosen twice, CALL once'), or measure the discriminator with the prototype before registering.

### MENU-3 (MINOR): E7 is not new: it reclassifies a kind the eyes already report as 'multichoice' on a screen chapter 4 can reach

- **Target:** MENU 2 E7 (multichoice_grid 'new') and 5 C3
- **Evidence:** eyes/screens.py:251 and eyes/view.py:423 already map Task_HandleMultichoiceGridInput to 'multichoice'. host/eyes.py:543-545 reads its option names. screens.py:626 builds options and cursor only for the kind 'multichoice', so a renamed kind also loses its options and cursor unless that line changes. The Rustboro school blackboard is on a chapter-4 map. Today it reaches _story_menu('multichoice') and stops. After E7 the kind string, and so the stop's reason text, changes. Control C3 lists 'the blackboard grid' as returning False, but with E7 the grid never reaches named_option at all. Without E7 it would reach the new skill with a 1-D cursor over a 2-D grid. ui_kinds_ch1to4.py over the 12 chain-probe runs shows no 'multichoice' kind at all, so the live C4 cannot see this.
- **Fix asked for:** Describe E7 as a reclassification and update screens.py:626 with it. Add a unit CONTROL for the blackboard grid: today 'multichoice' leads to the same stop, after E7 'multichoice_grid' is refused with no press. Keep the G6 FAULT.

### MENU-4 (MINOR): The forced menu does NOT stand under the message: closemessage runs first, so the instruction is read from a buffer that is no longer on screen

- **Target:** MENU 1.2 'the last message, which the menu stands under'
- **Evidence:** RustboroCity/scripts.inc:57-60 runs msgbox AddedMatchCallPleaseCallMrStone, then closemessage, then delay 20, then the menu. The end-state probe (menu/probe_end_state.out, f856173) shows text_box_open false and waits_for_button false while `text` still holds all 5 pages. So the rule reads a stale message buffer. At other field multichoices whose message was closed (or never printed), the 'instruction' could be an unrelated earlier text. The design calls this 'only what the screen shows'. It is what the screen showed earlier, which is defensible under ruling 40 as memory, but it is not what the design claims.
- **Fix asked for:** State it as 'the last message the player read before the menu'. Bound it: capture only when the message was printed after the player was last free, or within N frames before the menu opened. Add a CONTROL where a stale, unrelated message stands in the buffer and nothing may be chosen.

### MENU-5 (MINOR): 'Its callback is that screen's input handler' is ambiguous, and the tutorial uses two other main-menu handlers

- **Target:** MENU 2 'Input rule for E2-E4'
- **Evidence:** recon_summary.txt shows the main menu's callback as HANDLEMAINMENUINPUTTUTORIAL (cursor @0, @1, @2) before the call and HANDLEMAINMENUINPUTENDTUTORIAL (@2) after it, never HandleMainMenuInput. The decomp selects among these three by mode (pokenav_menu_handler.c:191-199). The design also says no '...Tutorial' handler name may reach the brain. A build that whitelists only HandleMainMenuInput would report accepts False for the whole tutorial, so `choose` never presses.
- **Fix asked for:** Name the accepted set explicitly: {HandleMainMenuInput, HandleMainMenuInputTutorial, HandleMainMenuInputEndTutorial} for pokenav_menu. Expose only accepts_input. Add U2 cases on the tutorial and end-tutorial bytes.

### MENU-6 (MINOR): The live proof names no seeds, run counts or 'wrong if' for L2-L4, and C4 cannot exercise the new dispatch

- **Target:** MENU 6 (ledger) and 5 C4
- **Evidence:** Section 6 says 'register in the ledger with the prediction's sha256 BEFORE the runs' but gives no seed range or run count, and states wrong-if conditions only implicitly for L1. ledger.json's last entries use 5983-5989. C4 replays a chapter-4 leg. ui_kinds_ch1to4.py (12 runs) tallies 0 'multichoice' and no POKeNAV kind, so C4 is a determinism check of the eyes changes only (E1's name read, E6, E7), never of the new branch. That is fine, but it should be said.
- **Fix asked for:** Name the seeds and runs per arm and a falsifier for each of L1-L4. State that C4 tests 'no leak from the eyes changes' and that U1/C1-C3 are the dispatch controls.

### GRUNT-1 (MINOR): The C2L5 arms have no computed discriminator and no vacuity guard, so a P2 miss could be vacuous

- **Target:** GRUNT 6.2-6.4 (C2L5 arms)
- **Evidence:** 6.3 computes the discriminator only for C3L5. For C2L5 (Route 116 at (14,10)) the design's own 6.5 argument says decide records are identical outside RUSTURF_TUNNEL, so with equal seeds A and B are one trajectory until the first tunnel arrival. The carried C2L4 world has no Route 116 or tunnel: 0 matches for '"0:31"' and '"24:4"' in its world.jsonl, and 'tunnel' was never heard. In the probe, C2 needed about 200,206 frames from the theft to its first tunnel arrival (f477,461 to f677,667, from tunnel_scan), while the budget is 200,000 frames. A B run that never enters the tunnel fails P2 with the change never exercised.
- **Fix asked for:** Add a per-run vacuity guard: B's run must reach RUSTURF_TUNNEL and decide there at least once, otherwise it is reported as VACUOUS, not wrong. Report frames to first arrival. Or start the C2 arm from a tunnel-arrival state.

### GRUNT-2 (NIT): Six of the seven control arms are identical by construction

- **Target:** GRUNT 8 (live decision-record CONTROL)
- **Evidence:** The new look acts only through notice() writing sightings (goals.py:1192-1194) and through reads keyed on the CURRENT step's look (goals.py:1370, 1557, 1598). The design itself adds the chapter-3 arm 'so the woods grunt (gfx 117) is on screen', which means the six chapter 1-2 arms never show gfx 117/118, so nothing differs in them by construction (session rule 4: a check must assert something the run does not already satisfy).
- **Fix asked for:** Keep the chapter-3 arm, which is the one that exercises notice(). Label the six chapter 1-2 arms as a cheap determinism check, or drop them.

### GRUNT-3 (NIT): 'Data only ... no code change' is broader than true

- **Target:** GRUNT 0 headline
- **Evidence:** The same design changes gate code: extract_milestones.verify's new 'look on its step's map' check and its 8th plant (7), a G-mutant in revert_step5.py (5), and a rewritten test_chapters_1_to_4_are_untouched (C6). The precise claim, backed by 'call_census must be byte-identical', is that no AI-player code changes.
- **Fix asked for:** Say 'no AI-player code change; the gates gain a verify check, a mutant and a rewritten pin'.

## 3. The independent verifier's report

### Independent verification of the chapter-5 stops build (worktree wf_5eff42ad-346-4)

**Verdict: both stops are fixed and the fix replicates live on new seeds.** I found no bot code, no hidden-state read and no one-place hack in the decision path. There are no MAJOR findings. Three MINOR findings are test gaps or evidence wording (F1-F3), and two are NITs. I did not modify the worktree. Its AI-code digest is still `40b1db185bdba453`, the same as the evidence's stage armB.

All my work is under `C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/2cb1657d-9e66-4a34-afd4-cbf84eb4a4a8/scratchpad/s53/ch5stops/verify/`: scripts `v_*.py`, predictions `prediction_v*.txt`, outputs in `out/`.

### Offline checks (a robocopy of the worktree)
| Check | Result |
|---|---|
| test_goals | 320 OK |
| test_eyes | 63 OK |
| test_hands | 57 OK |
| test_world | 132 OK |
| test_kb2 (POKEBOT_DECOMP pinned) | 123 OK |
| test_host | 37 OK |
| check_purity | PASS |
| check_fairness | PASS (0 breaches) |
| call_census | 60 sites, 0 MISSING |
| ledger --check | 91 entries, PASS |
| extract_milestones / extract_world / make_chapter_pack --all --check | PASS |
| extract_milestones --verify (gh api) | PASS, "5 step looks on their maps", Route 103 rival noted as set at runtime |
| --verify --plant | "PASS (the plants were found, and nothing else)" |

- **New tests on the base code.** I ran `git archive e70a8469 ai_player` with the new test files copied in: 46 tests, `failures=12, errors=28`, which reproduces the claim. Every FAULT-side test fails there. The tests that pass on the base are TunnelGruntTests.c2 and 11 of the 12 Chapter5Tests.
- **Builder's mutants.** I re-ran `revert_step5` on G435, G439, G447, G456, G457, G458, G462, G463 and G464: 9 of 9 CAUGHT, FROZEN TREE PASS. The tree digest `ba378d5bd88c9cf0` equals the one in the full-lane evidence, so that lane ran on this tree.
- **My own mutants** (not in G430-G464), against the new test classes:
  - CAUGHT: X1 (pages read oldest first), X2 (MIN_WORD 2), X3 (a page appended on every look), X5 (call-exit wait ignores state), X6 (a field menu nothing names gets a B), X9 (a grid never reaches the skill), X10 (special-entry name off by one), X14 (the followed-option add deleted), X16 (every B counted as refused), X17 (own name never read), X18 (menu type shifted), X4c (main-menu input guard).
  - SURVIVED all 440 tests of goals + eyes + hands (CONTROL X0 OK): X4 and X4b (the list's and the options' input guard), X11 (list cursor window offset), X7, X13 and X15 (findings F1 and F2).
- **Decomp check.** Every struct offset the host reads matches the pinned decomp: PokenavResources substructs at 0x10, Pokenav_Menu callback at 0xC, Pokenav_MatchCallMenu numRegistered 0xA / callback 0x18 / entries 0x1C, PokenavList windowState at 0x888. Substruct ids are 1, 5 and 17 of 19. The MC_HEADER order matches MATCH_CALL_NAMES.

### Rulings
- **Ruling 35:** check_purity PASS on the tree, and every live launch reported purity CLEAN.
- **Ruling 40:**
  - The brain receives only kind, options, cursor and accepts_input. The tutorial's `mode` is never read.
  - The handler names only gate accepts_input.
  - The player's name is the player's own.
  - Borderline: MENU-4 reads the message box after `closemessage`, for runs that start mid-scene only (F3).
- **D1:** the skill is a general "option named by the words read" rule. The grunt fix is data: a `talk` step with a static look, the same mechanism as the rival, NORMAN and ROXANNE.
  - In my B2 run the talk goal was set with the grunt on screen: player at (7,5), `sees=[npc(7,0),...]`, which is the grunt at (14,5).

### Live replication
Four batches on new seeds, my own stage, at most 4 runs at once, everything read from the game, L5.THIS_RUN PASS in all 17 runs.

**VMENU (#92), start C1L5, 30,000 frames**

| Run | Result |
|---|---|
| B1-B3 (6101-6103) | VAR 6→7 in 3,090, 3,084 and 3,090 frames. Instructed records: choose ×4, back ×2. 1 press gated on "the call has ended". 0 unexpected-multichoice lines. |
| A1 (base, 6101) | VAR stays 6; 30,000 unexpected-multichoice stops |
| F (FAULT_NO_INSTRUCTED, 6104) | VAR stays 6; 30,000 stops |
| MW (pokenav_wait call deleted, 6105) | VAR stays 6. "STUCK: nothing on screen changed for 900 frames… the POKéNAV". The waived call is load-bearing. |

Purity CLEAN 6 of 6.

**VGRUNT (#93), start C3L5, 60,000 frames**
- B (6111-6113): 3 of 3 set TRAINER_GRUNT_RUSTURF_TUNNEL 1 and RECOVERED_DEVON_GOODS 1, in 11,644, 9,864 and 9,228 frames. The goal before each battle was `talk:aqua_member`.
- A (base): 1 of 3 proven (seed 6113), by `chat:24:4|6`.
- Purity CLEAN 6 of 6.

**VPROBE (#94), new code from the chain ends C1L4, C2L4 and C3L4, target ch5_rival_meet, 600,000 frames**
- 3 of 3 reached ch5_rival_meet, in 172,781, 215,704 and 167,204 frames. VAR ended at 8 and the grunt was beaten in all 3.
- Every "is named by" line says "(the pages read since the player was last free)". The player names were Milo, ELI and Luna, and the upper-case ELI was handled too.
- 0 unexpected-multichoice lines; purity CLEAN 3 of 3.
- The rival was beaten in 2 of 3 (that was not predicted).

**VCONTROL (#95), C1L2 to ch3_rustboro, seed 6131, A vs B**
- Identical: 794 of 794 compared records, 7,047 total records each, 147,369 frames each, end marks equal.
- B made 0 instructed records and passed ch3_woods, where the woods grunt is on screen.
- Purity CLEAN 2 of 2.

**Clean-up.** The stage is deleted, the junctions were unlinked first, and the main sandbox's file counts are unchanged. No "ai-vfy" paths are left in the main sandbox. The verify copy's junctions are torn down.

### Evidence headlines against their bodies
- Consistent: menu 6 of 6 against base and FAULT 0 of 5; grunt 3 of 3 against base 1 of 3 by a chat; 2 of 2 non-vacuous from Route 116; P5's failed world-size clause is reported honestly; probe 3 of 3; control 6 of 6.
- Full lane: units (31) + 3 revert suites = 34 suites, 4,987.9 s; revert_step5 458 + 2 of 460; revert_r1 559 + 1 of 560. All match.
- Exceptions: the C1L5 menu arms all relied on MENU-4's fallback and nothing says so (F3), and two test counts in the build claim are off (F4).

### Verifier findings

- **F1 (MINOR): Untested guards and arithmetic in the POKeNAV eyes: the list's and the options' 'takes input' guard, the list cursor's window offset, and the ordinary-trainer entry name.** Verifier mutants (verify/v_mut.py), each in a copy laid out like the full repo and run against test_goals + test_eyes + test_hands (440 tests; the no-change CONTROL X0 passes all 440). X4 (pokenav_list accepts_input=valid, Task_Pokenav state ignored): SURVIVED. X4b (the same for pokenav_options): SURVIVED. X11 (list_cursor = selectedIndexOffset only, windowTopIndex dropped): SURVIVED. X4c (the same guard on the main menu): CAUGHT by test_u2_the_main_menu_in_each_of_its_tutorial_handlers, the only test that uses STATE_LOOPING. test_eyes.py:910-919 builds the list and the options only with STATE_INPUT, and test_u2_the_host_follows_gpokenavresources uses windowTopIndex 0 and one special entry, so the gRematchTable/gTrainers branch of host/eyes.py _match_call_name is never run offline.
  Live, the tutorial's list holds only 'MR. STONE', so neither path was exercised there either. The proof bar asks for a FAULT and a CONTROL for every guard. These are latent today but load-bearing for any later MATCH CALL list longer than one screen, or one holding a rematch trainer. *Fix:* In PokenavEyesTests, add STATE_LOOPING halves for pokenav_list and pokenav_options (accepts_input False), a host test with windowTopIndex != 0 (e.g. top 3, offset 1 -> cursor 4), and an ordinary entry named through gRematchTable/gTrainers. Add each as a revert_step5 or revert_r1 mutant.
- **F2 (MINOR): Three boundaries in skills/instructed.py survive every suite.** Same harness, 440 tests, all OK with each mutant: X7 (_in_field without `not screen.fading`), X13 (instruction_now returns self.pages + joined, so MENU-4's buffer reads as NEWER than the pages read since), and X15 (the re-capture test `len(pages) > self.at_field` changed to `>=`, which clears a field menu's followed pairs on every return). None of the 35 mutants G430-G464 touches these lines (revert_step5.py:1955-2097). All three are latent on the tutorial scene, where the joined buffer and the pages agree. *Fix:* Add a unit case for each: a fading look is not 'in the field'; a joined message naming option X with a newer read page naming Y chooses Y; a field menu returning with no new pages keeps its followed pairs. Register each as a revert_step5 mutant.
- **F3 (MINOR): Every C1L5 menu-batch run took its instruction from MENU-4's message-buffer fallback, not the real read-along path, and the evidence never says so.** Verifier VMENU (ledger #92), B1-B3: every 'is named by' line ends '(the message the field menu stood under (the run began inside this scene) and the pages read since)'. The builder's smoke, menu and menu2 arms start from the same C1L5 state (inside the forced-menu scene), so the headline 'from the C1 end state the new code passed in 6 of 6' rests on that fallback. The fallback reads the message box's buffer after `closemessage` (RustboroCity/scripts.inc:57-60), text not drawn at that moment. instructed.py:24-28 acknowledges that the fallback is used only for a run that began inside a scene. The real path (pages read since the player was free) was exercised only by the 3 probe runs (#91) and my 3 (VPROBE #94), where every line ends '(the pages read since the player was last free)'.
  Neither the evidence file nor README.md:2087-2097 mentions MENU-4. *Fix:* Say in the evidence headline and the README proof paragraph that the C1L5 arms exercise the fallback and that the probe runs carry the real path. Record in 06 the ruling-40 reasoning for reading the closed message box (it was shown before the run began, and only a run starting mid-scene uses it).
- **F4 (NIT): Two test counts in the build claim are off.** The claim says 'InstructedTests (17 tests)'. unittest.TestLoader counts InstructedTests 16, TunnelGruntTests 10, Chapter5Tests 12 and PokenavEyesTests 7 (16 + 10 + 1 + 12 + 7 = 46, matching '46 tests'). On the base code 11 of 12 Chapter5Tests pass (only test_chapters_1_to_4_are_untouched fails), not 'the 10 unchanged Chapter5Tests'. The totals FAILED (failures=12, errors=28) were reproduced exactly (9+3 failures, 21+7 errors). *Fix:* Correct the numbers wherever the claim is copied (handoff or changelog at wrap-up): InstructedTests 16; on the base code, TunnelGruntTests.c2 and 11 Chapter5Tests pass.
- **F5 (NIT): eyes/view.py still names the grid 'multichoice' while read_ui now calls it 'multichoice_grid'.** ai_player/eyes/view.py:422-423 MENU_TASKS maps both Task_HandleMultichoiceInput and Task_HandleMultichoiceGridInput to 'multichoice' (ScreenState.menu). eyes/screens.py:269 now reports the grid's ui.kind as 'multichoice_grid'. Only observation.py:407 (a log string) reads screen.menu, so no decision changes. *Fix:* Map the grid task to 'multichoice_grid' in view.py MENU_TASKS too, or note in screens.py's E7 docstring that the coarse `menu` field keeps the old name.

### Ledger entries (verifier; copied into `ai_player/gates/ledger.json` at the merge)

- #92 story verifier_vmenu development seeds 6101-6105 (verify copy's ledger, prediction_vmenu.txt sha256 f27853344bfe966a702ee67286b8728f045e1cc0c411a7f6c5d6c2f05baba45b), done
- #93 story verifier_vgrunt development seeds 6111-6113 (prediction_vgrunt.txt sha256 fee3f85c56e73267ca552f4dec8ad17fdd598ca1999732463df16547c0ab1383), done
- #94 story verifier_vprobe development seeds 6121-6123 (prediction_vprobe.txt sha256 c3482037dd8d3a252b58bb1228f8c8de3322720878d1ecab56b72f499bf0dd87), done
- #95 story verifier_vcontrol development seed 6131 (prediction_vcontrol.txt sha256 bf17301b973643eb9395e153fdb3867d97fd53fef1ddf0e8807fccd7d9f41d96), done

## 4. The designs' recon (read-only; the design documents themselves were the workflow's inputs to the critic)

### menu

- Base checked: `git log -1` gives e70a8469. This was a read-only design task. Nothing in the repo was edited and nothing was committed. Every script and output is under scratchpad/s53/ch5stops/menu/: peek_actions.py, scan_menu_obs.py, ui_kinds_ch1to4.py, show_probe.py, recon_pokenav.py, summarize_recon.py, recon_events.py, proto_named.py, plus their outputs (recon_pokenav.jsonl, recon_summary.txt, probe_end_state.out, c1_end_state.ss1).
- Where the stop is raised: `ai_player/brain/navigator.py:1155-1158`. `Navigator.handle` gets 'menu:multichoice' from `advance` and asks `on_menu`. `mode.py:1007-1022` (`_story_menu`) knows choose_starter, clock, mart_menu/mart_buy and save_dialog/save_yes_no/start_menu, and returns False for anything else. The navigator then returns 'stuck: an unexpected multichoice on screen'. `play_out` and the play loop (`mode.py:860-866`) call it again, one frame per pass.
- The C1 probe, streamed from its actions.jsonl (111,930 records). The 5 scientist pages were read and pressed through at records 12232-12275 (f753971-f756504). The first stop is at record 12278 (f756529), with the menu still 'multichoice(busy)'. After that, 99,643 'what was on screen ended: stuck: an unexpected multichoice on screen' records, and only 3 distinct screen digests. A single 'await' shows a screen that waited 99,642 frames for a press while the AI did nothing. The run ended '100000 passes of the play loop'.
- THE EYES ALREADY SEE THE FORCED START MENU, measured live. `gates/probe_eyes.py` was run on a copy of the C1 end state (end_state.ss1, md5 343860d7df3cf52b5ec387d88a1e9369, read at f856173). The eyes report ui kind 'multichoice', options ['POKéDEX','POKéMON','BAG','POKéNAV','','SAVE','OPTION','EXIT'], cursor 0, accepts_input True. The text is the 5 pages joined by ¶, ending in 'Test it out. Please give our PRESIDENT a call.' The truth has Task_HandleMultichoiceInput active and no problems. The options come from `sMultichoiceLists[86]` (`host/eyes.py:545,732`). The blank at index 4 is gText_Blank, where the game draws the player's name. Conclusion: no new eyes are needed for the forced menu. Only a decision is missing.
- Decomp, forced START menu: `RustboroCity/scripts.inc:68-93`. `ScriptMenu_CreateStartMenuForPokenavTutorial` builds `InitMultichoiceNoWrap(FALSE, 8, window, MULTI_FORCED_START_MENU=86)` (`script_menu.c:686-711`). Every case except 3 (and B, MULTI_B_PRESSED) goes to 'Please select the POKéNAV.' (scripts.inc:1177-1178) and back to the menu. Case 3 runs `OpenPokenavForTutorial` (pokenav.c:333-362, mode POKENAV_MODE_FORCE_CALL_READY), then sets VAR_RUSTBORO_CITY_STATE to 7.
- Decomp, the POKéNAV: `pokenav_menu_handler.c:259-288` (HandleMainMenuInputTutorial) accepts only MATCH CALL and treats B as a failure sound. `pokenav_match_call_list.c:111-123`: B in the list is refused while FORCE_CALL_READY. :148-160: CALL switches the mode to FORCE_CALL_EXIT. :198-207: A or B closes a finished call. `HandleMainMenuInputEndTutorial` (menu_handler.c:290-315): B or SWITCH OFF leaves, and `Task_Pokenav` state 5 returns to the field script (pokenav.c:488-499). `Task_Pokenav` calls the screen's input callback only in state 3, never while a looped task runs (pokenav.c:452-482).
- THE POKéNAV IS INVISIBLE TO TODAY'S EYES, measured. recon_pokenav.py is a test-side scripted harness in a throwaway emulator, not an AI run. It started from the end-state copy. Over 567 recon records inside CB2_InitPokenavForTutorial/CB2_Pokenav, the eyes reported game_state UNKNOWN, screen 'other', ui None and scene None. waits_for_button was False in 560 records and True in 7 (the call's paged text). `advance` would log the catch-all busy reason and stop after STALL_FRAMES 300.
- Recon timeline, from game frames. A on the forced menu at about f856211. CB2_InitPokenavForTutorial at f856215. CB2_Pokenav, main-menu handler set, looped task still running at f856245. The main menu takes input (no Task_RunLoopedTask) at f856275, menuType 1 (MAP, CONDITION, MATCH CALL, SWITCH OFF), cursorPos 0. Down, Down moves cursorPos 0->1->2. The match call list takes input at f857250 with numRegistered 1, entries [(special 1, mapsec 10, header 0 = MR. STONE)], numSpecial 21, list top 0 / selectedOffset 0. B in the list at f857811 changed nothing. A on the entry opens the options [0,2] = CALL, CANCEL (maxOptionId 1, no check page). CALL at f857855. The call's pages were read through printer waits, 7 A presses. The call-exit wait (CB2_HandleCallExitInput, no looped task) ran f859067-f859897, 167 records over 830 frames, with eyes waits False the whole time.
  Then A, B (back to the main menu, HandleMainMenuInputEndTutorial@2, f860079), B (leaves; CB2_ReturnToFieldLocal at f860100), and A on the scientist's last page. End: f861611, VAR_RUSTBORO_CITY_STATE 6 -> 7, after 21 harness presses over 5,438 frames.
- Measured POKéNAV memory layout, with the offsets checked by the recon reads. gPokenavResources: currentMenuIndex @4 (0 main menu, 11 match call, 4 main menu with the cursor on MATCH CALL), mode @8 (1 then 2; hidden, must never reach the brain), substructPtrs @0x10. Substruct 1 Pokenav_Menu: menuType @0, cursorPos @2, callback @0xC. Substruct 5 Pokenav_MatchCallMenu: optionCursorPos @0, maxOptionId @2, matchCallOptions @4, numRegistered @0xA, numSpecialTrainers @0xC, callback @0x18, entries @0x1C. Substruct 17 PokenavList: windowState @0x888 (windowTopIndex, listLength, entriesOffscreen, selectedIndexOffset, entriesOnscreen). The button labels are images (graphics/pokenav/options/hoenn_map.png, match_call.png, condition.png, switch_off.png, ribbons.png). The list name strings are in strings.c ('MR. STONE' :1775, 'PROF. BIRCH' :23, 'MOM' :1783, 'DAD' :1782).
- An eyes defect seen in the recon: on the call's first frame (f857855) the eyes' `text` decoded garbage ('=₽êË)₽êË0₽...'). Apparently a printer pointer is decoded as text. It does not matter to the skill, which never takes app pages as instructions, but the reading log would carry it.
- Chapter 1-4 controls: ui_kinds_ch1to4.py streamed the 12 chain-probe runs (C1L1-C3L4). The ui kinds counted: battle_action 3487, battle_move 1334, save_dialog 354, battle_yes_no 346, save_yes_no 308, yes_no 183, mart_menu 168, bag 148, mart_buy 111, start_menu 92, bag_action 82, mart_quantity 71, naming 66, party 40, battle_target 39, move_forget 32, intro_movie 27, choose_starter 14, title 12, main_menu 12, gender 11, clock 9. multichoice: 0. Any POKéNAV kind: 0. So the new dispatch has no screen to fire on in chapters 1-4.
- A prototype of the choice rule (proto_named.py, design check only, not AI code) was run on the pages exactly as the eyes read them live. The forced menu picks POKéNAV (from 'Milo, our PRESIDENT STONE should be registered in your POKéNAV.'). The loop's 'Please select the POKéNAV.' picks POKéNAV. The main menu picks MATCH CALL ('Using the MATCH CALL feature, ...'). The list picks MR. STONE ('...PRESIDENT STONE...'). The options pick CALL ('...give our PRESIDENT a call.'). After the call, with those options used, the list and the main menu both give 'nothing named', so the skill backs out. Controls PC, blackboard, Briney, fossil and fishing: nothing named in each. The fault arms that discriminate: blank label kept chooses '' on the forced menu; the player's name kept chooses "MILO'S PC"; app pages kept chooses MR. STONE again after the call. Two candidate faults are REDUNDANT on this scene: substring matching still picks POKéNAV, and oldest-first still picks CALL.
- Gates read: `check_fairness.py` (RULE A flag door, B knowledge, C play time), `check_purity.py` (`re` is allowlisted at :449, every new AI file passes through it), `call_census.py` (every new call site needs a deleting or guarding mutant, or a waiver). Existing test hooks: `test_goals.py:1893-1923` drives `brain._story_menu` with fake hands, and :6724 asserts the PokeNAV milestone keeps the step kind 'follow' (this design keeps that). `hands/menus.py` choose/move_cursor read the cursor each step and press A only when the cursor is on the target.

### grunt

- Base checked: git HEAD e70a8469, working tree clean after every script (git status --short printed nothing). Nothing in the repo was written; all scripts and outputs are under scratchpad/s53/ch5stops/grunt/.
- The mechanism already exists and is general: a `talk` step with a `look` (ai_player/knowledge/story.py Step; brain/goals.py `_story_step_goal` :1548-1565) turns into `find` (stay on the step's map until something matching the look is on screen, FIND_FRAMES 4000), then `seek` (the last sighting), then `talk` (skills/story.py talk_to: walk up, face, A, play out the battle and the scene). It already serves ch1_rival_route103 (look rival), ch2_dad (norman) and ch4_roxanne (roxanne). The chapter-3 woods grunt and the Rustboro employee do NOT steer the AI to a person: both are `follow` steps over coord triggers (PetalburgWoods (26|27,23) VAR_PETALBURG_WOODS_STATE 0; RustboroCity StolenGoods x=23 y=20..24 and HelpGetGoods (29..30, 9..12)), so any walk across them plays the scene.
- Decomp (pinned clone 731ad5b): the grunt is object LOCALID_RUSTURF_TUNNEL_GRUNT (6th object, local id 6), OBJ_EVENT_GFX_AQUA_MEMBER_M = 117, template (14,5), FACE_LEFT, TRAINER_TYPE_NONE (no sight trigger: he must be talked to), script RusturfTunnel_EventScript_Grunt (lock, faceplayer, msgbox, trainerbattle_no_intro TRAINER_GRUNT_RUSTURF_TUNNEL, giveitem DEVON_GOODS, the BRINEY/PEEKO scene, setflag RECOVERED_DEVON_GOODS, VAR_RUSTBORO_CITY_STATE 4, VAR_BRINEY_HOUSE_STATE 1). OnTransition at VAR_RUSTURF_TUNNEL_STATE 2 moves him to (13,5) and PEEKO (WINGULL gfx 211) to (13,4); coord triggers (9,4) and (9,5) at state 2 play 'What, are you coming? Come and get some, then!', back both up one tile right and set state 3. Every figure on RUSTURF_TUNNEL: AQUA_MEMBER_M 117 (the only Aqua figure), BLACK_BELT 44, BREAKABLE_ROCK 86, EXPERT_M 21, HIKER 55, ITEM_BALL 59, WINGULL 211, WOMAN_2 20.
  Other AQUA_MEMBER_M objects near: PETALBURG_WOODS (26,17) and RUSTBORO_CITY (13,21), both script 0x0 (scene actors). Map type MAP_TYPE_UNDERGROUND, requires_flash False.
- Probe logs (s53/ch5/out/probe, streamed): C2 and C3 both ended with RUSTURF_TUNNEL_STATE 3, so both crossed the back-up trigger 5 tiles from the grunt. C3's action records show `sees=[npc(4,1),npc(4,0)]` from (10,4), i.e. the grunt at (14,5) and PEEKO at (14,4) on screen, and the explorer's own record `target people (13, 5) ... someone not met yet, at (14, 5)` with who=6, then 'the people at (13, 5) is not worth going to any more: the player has been beside them: met'. Both C2 (line 1775) and C3 (line ~1026) then CHATTED PEEKO at (14,4) from (13,4), never the grunt. C1 won the fight by a CHAT draw ('draw 0.00 < the Story's 0.18, raised to 0.90', walk to (13,5), 'talked; then stuck: the battle: budget', MILESTONE ch5_rusturf_grunt done at f715838), live evidence that talk_to from (13,5) starts this fight.
- Probe end positions (streamed actions.jsonl): C1 last overworld RUSTBORO CITY (12,17) (C1 is past the grunt); C2 ROUTE 116 (14,10); C3 RUSTURF TUNNEL (4,10), the west door, 10 tiles from the grunt (out of view). Tunnel records: C2 3,087, C3 2,934; most visited tunnel tile (4,10): 1,952 and 1,855 records. The C2/C3 world.jsonl were NOT kept (305,986,975 and 319,315,085 B); the nearest memories are the chain probe's C2L4/C3L4 world.jsonl (2,385,390 and 4,899,024 B) in sandbox-pokebot/profiles/ai-chain-probe-{2,3}/ai_player_runs/*-C?L4/.
- OFFLINE A/B on TODAY's GoalManager (offline_ab.py, the real milestones.json vs the same data with ONE look and ONE step changed IN MEMORY, no code change): grunt+PEEKO on screen: A follow, B talk talk:aqua_member target (local 6, gfx 117); nobody on screen: A follow, B find:aqua_member; a sighting at (14,5): A follow, B seek:aqua_member; only PEEKO on screen: A follow, B find (PEEKO is never taken for him); on RUSTBORO_CITY with an Aqua figure on screen: A go:RUSTURF_TUNNEL, B go:RUSTURF_TUNNEL (map scoping holds); in the tunnel with 'tunnel' never heard: A follow, B talk. Chat with only the grunt near and boredom saturated: A picks (6,117), B picks None (the story's own person is no chat). `_story_here` with 'tunnel' heard True, with nothing heard False. milestones[:20] equal and the 12 old looks equal between A and B.
- OFFLINE heal check (offline_heal.py): party at 85% HP in the tunnel, grunt level known from a ROUTE 116 trainer seen at L9, training done, Rustboro's centre known: A follow; B HEAL ('the party is at 85% of its HP; a known fight is next: the POKeMON CENTER it knows (RUSTBORO_CITY_POKEMON_CENTER_1F)'). At 95%: B talk. The talk step makes `fight_next` (goals.py :1213, go or talk) true INSIDE the tunnel, so HEAL_BEFORE_FIGHT 0.9 now applies there. In the probe the go phase already did this: heal goals 'a known fight is next' C1 1, C2 2, C3 4.
- Digest CONTROL (looks_on_maps.py): test_goals Chapter5Tests.test_chapters_1_to_4_are_untouched pins the WHOLE looks block (de26718a...): on HEAD it matches (True); with a 13th look added the whole-block digest no longer matches (False: the test would FAIL), while the digest of the 12 OLD looks by name with the 13th present still equals the SAME pinned value (True). milestones[:20] digest is unaffected (the grunt is entry 22).
- Looks on their maps (pinned decomp): ch1_birch birchs_bag on ROUTE101 (7,14); ch2_dad norman (4,2); ch4_roxanne roxanne (5,2); ch1_clock is a metatile look (4 bg events); ch1_rival_route103's rival is OBJ_EVENT_GFX_VAR_0 at (10,3) (a runtime figure, so a static 'look on its map' check must report VAR figures, not fail them); the proposed aqua look on RUSTURF_TUNNEL: (14,5).
- ROUTE 116 story-break (break_stops.py over the logs, from the moment ch5_rusturf_grunt became the story): breaks C1 5, C2 85, C3 63, almost all 'after a battle on ROUTE116' at odds 0.90 (C2 81 of 85, C3 60 of 63: CURIOUS_ODDS_CAP 0.9 times boredom saturated at 1). The goal the next decision chose: 'go' again in C2 79 of 85 and C3 61 of 63. Go-to-tunnel walks ended by a break: C2 85 vs 127 otherwise, C3 63 vs 116. It is churn (a break nothing uses), not a stop: both runs reached the tunnel many times. It never fires inside a find walk (walk_battle_break is for goal.kind == 'go' only).
- Regeneration chain a change to milestones.json drags: campaign.json pins milestones.json's sha (only file that does: d4b934f8b3cf79fe found only in ai_player/knowledge/world/campaign.json), and every chapter pack pins campaign.json's sha (6112bbc3bc59a748 found in PROJECT KNOWLEDGE/chapter-packs/ch1..). So: extract_milestones.py (write, --check, --verify), extract_world.py (campaign _inputs), tools/make_chapter_pack.py (re-pin), then test_kb2, selftest_chapter_pack. check_fairness already classifies looks.*.gfx/what/decomp and milestones[].steps, so no new key needs a class. Ledger: 85 entries; development seeds 5991-6009 were free when read (5990 is entry #69).

### open questions the designers left

- ["Where should the player's own name come from? I recommend a new eyes field, `PlayerState.name`, read from SaveBlock2 playerName. A person sees it everywhere, and it also works for a run continued from a saved state. The alternative is the name the AI typed in its intro, which a continued run does not have. Either way, rule G2 needs a name.", "Where should the instruction come from? I recommend the eyes' last message (`screen.text`), captured when a field multichoice opens. It is the smallest change and works from the C1 end state, as measured. The cost is that a multichoice with no message of its own could inherit a stale earlier message. The alternative is a small memory, in Hands, of the pages read in this scene. It is more robust, but from a state loaded at the menu it would be empty, so the live proof would need an earlier fixture.
  Should the build add that memory now or later?", "When a field multichoice names no option (the PC, Briney's 'where are we bound?', the blackboard), the design keeps today's stop and does not press B. Is that the wanted behaviour, given that the AI never chooses an option by its own intent there? This design only follows what the prompt names; choosing by intent would be a separate skill.", 'Should the POKéNAV reader cover only the three screens this tutorial uses (main menu, match call list, call options), plus the call-exit wait? That is what I recommend. Or should it also cover the full app now: HOENN MAP, CONDITION, RIBBONS and the check pages, which a person may open later in the game?', "The play loop spun 99,643 times, one frame each, on one identical stop before its 100,000-pass bound ended the C1 run.
  Should a run end after N identical stops in a row? That is a separate change to the play loop's bound, not part of this skill.", "Which ledger entries and development seeds should L1-L4 use? And does the 'Please select the POKéNAV.' fixture (L4, made by a test-side harness that picks BAG) count as a development fixture under the existing rules?"]
- ['Look scope: `aqua_member` gfx [117, 118] (a person recognises the uniform, not the gender; reusable for later chapters) or the minimal [117] (OBJ_EVENT_GFX_AQUA_MEMBER_M only)? Either is the only Aqua figure on RUSTURF_TUNNEL; the wider one also records sightings of female members elsewhere (no decision reads them unless a step names the look).', "Heal-before-the-fight now applies INSIDE the tunnel (offline: at 85% HP the new step walks back to RUSTBORO's centre before a Poochyena L11 when the lead is L26). Accept it as a careful player's habit and only bound it in the live prediction (P4: at most 2 such heals after the first tunnel arrival), or file a general rule (e.g. heal before a SEEN-level fight only when it is a real threat to the party) as its own item?", "Live fixtures: the probe's C2L5/C3L5 world.jsonl were not kept (over 300 MB), so the end-state arms must carry the chapter-4 world memory (the AI 'forgets' Route 116, the tunnel and the word 'tunnel').
  Is that acceptable as the primary live proof, or should the replay from the probe's own C2L4/C3L4 starts with seeds 5987/5988 (section 6.5: identical decide records until the first tunnel arrival, then the divergence) be the primary one? Re-using development seeds has precedent (#71 and #81 overlap) but needs a new ledger entry.", 'Should the ROUTE 116 break churn (79 of 85 and 61 of 63 breaks followed by the same go) become its own item now, or wait to see whether it still shows after the talk step removes the tunnel ping-pong?', 'Test C6 changes how `test_chapters_1_to_4_are_untouched` digests the looks (the 12 old looks BY NAME, same pinned constant) instead of re-pinning the whole block. Is that the preferred way to keep the chapters 1-4 CONTROL honest when chapter-5 looks are appended?']
