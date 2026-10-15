# Step 5 findings handed to step 5.1 (verbatim from the step-5 workflow, 2026-10-14)

## The final verifier (tree 6172ff8932690719)

### FAILURES
- RULING 37 Q6 ("never idle: it never stands still") is broken by two recurring stalls. In each one a screen is waiting for a button press, the stall is logged under a reason that is not true, and the pre-registered check (no standing still under the catch-all reason) cannot see it. (a) PROF. BIRCH's bag: after A on the starter, the navigator's scene handler (navigator.py:1010-1013) gives the 'Do you choose this POKéMON?' yes/no back to on_menu('choose_starter'). Its wait_for_ui then stands for 600 frames: '...PROF. BIRCH's bag: MUDKIP: the choose_starter did not open within 600 frames', then '[AI-GOALS] goal use done: talked; then stuck: an unexpected choose_starter on screen'. Live arm CH1M: A pressed at f34499, YES pressed at f35142 (643 frames); CH1T took 39 frames. Sweep seeds 301-310: 20 of 40 runs (5 of 10 in each of CH1, NOTRAIN, DEADREST and NOHINTS). (b) The play loop picks a goal on the frame a scene's map change lands. In CH1M, 'goal chat' came at f40019, 2 frames after 'MAP ROUTE101 -> LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB ... (a scene, f40017)'. hands/dialogue.py talk() then logs 'busy 1200f | waiting until the player is free to talk' while PROF. BIRCH's text waits for A (digest 'text waits=A/B(text printer 0 CLEAR)'). The first lab page is read at f41314, 1,295 frames after the milestone; in CH1T and CH1C it is about 165 frames. This happens in 13 of 40 sweep runs plus CH1M live. Both stalls are bounded and the story still completes; they are human-pacing defects, not hangs.

### WEAK PROOFS
- The live and sweep 'standing still' checks count only the catch-all reason, so a stall of 600 to 1200 frames under any named reason passes (the failure above). A check is needed that flags a busy or idle stretch of N frames or more while the screen waits for a button.
- The training target max(fight_levels)+margin is untested on a fight with several levels. My mutant using min(...) passes all 59 test_goals tests. The live CH2 log shows 'the Catcher's target L7' for ROUTE 102's [3, 4, 5], and ROXANNE's [12, 15] would differ by 3; BossLevelTests computes max() itself instead of asking the goal manager.
- Two of the round-2 claims about earlier suites have no evidence file on tree 6172ff8932690719: 'step-3 ROAM rows identical' and 'step-4 WILD/CATCH verdict lines identical'. They rest on the builder's report. I re-ran the revert_step3 subset (all 5 CAUGHT) and test_world, test_battle, test_hands and test_eyes ('Ran 352 tests ... OK'), but not those two replays.
- Some milestone lines say 'done' while quoting a proof that does not hold. For example '[AI-GOALS] MILESTONE ch1_intro done at f8643 ...: VAR_LITTLEROOT_INTRO_STATE=0 (>= 1)' and 'ch2_route102 done ...: VISITED_PETALBURG_CITY=0' are waypoint passes but are not labelled as such.
- Battle lines contradict each other (step-4 decider): 'a species it has not caught: it WANTS it (Story: catch_new 0.6)' is printed before it has any balls, and in CH1T f87162 'it WANTS it' is followed by 'run: travelling, and this wild Zigzagoon is not one it wants'.
- Builder-admitted thin spots stand: the training bounds (60 steps, 3 won) were carried over, not re-derived, and three sweep seeds won exactly 4; MAX_LOSSES 3 was never reached by an unaltered run (only a cap of 1, in a copy); live arms run on the host clock (one trajectory each).
- Stale labels: the step-5 UNITS evidence is titled 'AI PLAYER BUILD STEP 4.1 ROUND 3' (run_units.py:59 default); rate_step5.py:33 still names seeds 201-210 as the newest held-out set (admitted).

### SUMMARY
I verified the builder's step-5 round-2 claims on tree sha256:6172ff8932690719, recomputed and unchanged. Every core claim holds. all_pass is false for one reason: a pacing failure the builder's checks miss. In half of all runs the AI stands still for 600 to 1200 frames in front of a screen waiting for a button, under a reason that is not true. This breaks RULING 37's "never idle".

RAW QUOTES FROM MY OWN RUNS:
- check_purity: "VERDICT: PASS"
- test_goals: "Ran 59 tests in 0.426s / OK"
- shared suites (test_world, test_battle, test_hands, test_eyes): "Ran 352 tests in 79.669s / OK"
- extract_milestones --verify: "[VERIFY] OVERALL PASS"
- revert_step5 subset: G46, G47 and G50 all "-> CAUGHT", "OVERALL: PASS"
- revert_step3 subset: "5 mutants CAUGHT as predicted ... OVERALL: PASS"

TWO REVERTS OF MY OWN (my edits in a scratch copy):
- MAX_LOSSES off by one (>= changed to >): caught by PlayLoopTests.test_battles_lost_inside_goals_end_the_play_loop and LossTests.
- Whole-word matching with the trailing word boundary removed: caught by HintTests.test_heard_words_match_whole_words.
- A min-for-max change to the training target was NOT caught (listed as a weak proof).

EVIDENCE FILES I QUOTED (not re-run):
- live_step5: "OVERALL PASS"; each of CH1T, CH1C, CH1M and CH2 has "VERDICT: PASS" with verdict=CLEAN.
- RATE: "VERDICT: PASS".
- REVERT: "52 mutants CAUGHT as predicted ... OVERALL: PASS".
The live and rate suites were not re-run, as the task scope says.

REAL NEW GAME:
- The launcher ran with --fresh.
- Each arm's log shows "looking at the main_menu: ['NEW GAME', 'OPTION']" (no CONTINUE), then Birch's speech read and the name typed ('Luna', 'Milo').

INDEPENDENT FLAG READ:
- Flag numbers come from pret flags.h, fetched by me: RECEIVED_POKEDEX_FROM_BIRCH 0x8E4, SYS_POKEDEX_GET 0x861, ADVENTURE_STARTED 0x74, DEFEATED_RIVAL_ROUTE103 0x82.
- I read them raw at save block 1 + 0x1270 (offset from global.h) from each arm's end_state.ss1, using no ai_player code and no milestones.json numbers. All are 1 in CH1T, CH1C and CH1M, and the framework's get_event_flag agrees.
- GAME_STAT wild battles 13 / 13 / 21 and trainer battles 1 / 1 / 1: the rival was beaten first try, by the game's own flag and counter.
- The state files' md5s equal the evidence's.

TRAINING BEFORE THE RIVAL, recounted from the action logs:
- Live: CH1T 155 tile steps and 11 wild battles won (2 roams), CH1C 120 and 6, CH1M 266 and 11. Every roam ends before the rival's "would like to battle" page.
- Sweep CH1, seeds 301-310: wins [4, 10, 14, 7, 7, 17, 4, 9, 18, 4], exactly the game's own count. NOTRAIN: 0 in all 10 seeds.

NO BOT CODE:
- brain/, skills/, knowledge/ and mode.py import no modules.* and nothing from story.
- goals.py is a goal manager driven by priorities. It shares no routine, coordinate or navigation leg with early_game.py (whose routines are hard-coded navigate_to calls). Only the data matches, with its provenance (sha256 of the teacher file).
- The eyes' additions are read-only: save-block flag and var bytes, and the player's gender byte.

HINTS ARE PERSON-LEVEL:
- A map is unlocked only by whole words the AI actually read on screen. Reasons quote those pages ("Oh, BRENDAN went out to ROUTE 103 ...").
- A hint with no words is used only for a place the AI has already been. No coordinates or routes are loaded (the clock's measured x and y are never read).

LOOPS ARE BOUNDED:
- Every errand has a budget: GO 9000, FIND 4000, LOOK 2400 frames, APPROACH 4000, SCENE_ROUNDS 12, roam 4×steps, starter moves 8×30.
- The play loop is bounded by STORY_PATIENCE and MAX_LOSSES, both proven through the real loop.

THE FAILURE (two stalls):
- The starter's yes/no stalls 600 frames in 20 of 40 sweep runs and in live CH1M: the yes/no is handed to on_menu('choose_starter'), and wait_for_ui then times out.
- A goal chosen on the frame a scene's map change lands makes talk() wait 1200 frames while a text waits for A: 13 of 40 sweep runs and live CH1M.

Scratch scripts are in C:/Users/Ripto/AppData/Local/Temp/claude/C--Remote-Projects-Pokebot-Gen3-Enhancement/01ddd963-7a1a-4b49-8ecd-33397f5304e2/scratchpad/ (read_flags.py, count_training.py, my_mutants.py, long_waits.py, idle_check.py). No emulator process of mine or of the builder is still running; the processes still running belong to the pokebot-learner and the user's install_sandbox.

## The adversarial review

**Step 5 adversarial check: six findings, most severe first**

**1. HIGH: it plays like a speedrun, and nothing grades for that.** `goals.py` has no explore errand. Step 8 says "LOOK AROUND nothing else", so exploring only happens when the target map is unknown. Once a route is known, `ROUTE_VALUE` 100 outweighs any frontier (at most about 31), so the AI walks straight there. In live run CH1C (Catcher) the goals were go 10, follow 3, use 3, talk 2, heal 2, train 1, find 1. There were 0 catch, 0 chat and 0 look_around goals. Design §5 L260 says "always interleaves explore, catch, item and train intents". §7 L316 asks for an "intent mix" metric. `rate_step5.py` and `live_step5.py` measure neither intent mix nor how much runs with different seeds differ.
*Fix:* add a seeded, personality-weighted EXPLORE errand for each new outdoor map (Story included), and an occasional detour that is not the shortest way in `travel_intent`. Grade intent share and seed divergence, with a fault arm (errands off) that proves the metric moves.

**2. HIGH: chapter 4 will stop as "stuck" while it is still training.** `mode.py:404` checks `hands.pad.frames - changed_at > STORY_PATIENCE`, and `changed_at` resets only when a milestone passes. In chapter 1, Trainer runs already spend about 80–95k of the 120k frames in one milestone: CH1M's first train goal is at f47692, and the sweep's Trainer seeds beat the rival at f127–142k. That was for an L5 rival. Before ROXANNE the Trainer target is L18, with up to `TRAIN_SESSIONS` 8 × 150 steps.
*Fix:* also reset patience whenever a goal succeeds and makes progress (training steps or levels gained, a heal), and keep the stop for goals that keep failing.

**3. MED: some of the bot's script is still in the steps.** The steps for `ch1_rival_house` are go 1F → go 2F → `use rivals_poke_ball`. The game never tells the player to examine that ball; the AI goes to it only because the data says so. The item errand would do the same naturally, but it is blocked by `has_party`. Separately, `ask` goes to the rival's house with no `hint_known` check (`goals.py:587-589`). One milestone-level word ("next door") unlocks every step's map.
*Fix:* drop the `use` step and let item curiosity work before the AI has a party. Gate each step's map on its own heard words or on a visit.

**4. MED: it uses things a person could not know.** `fight_levels` covers fights nobody announced. The live CH2 reason reads: "the next fight (West of Oldale: ROUTE 102 and its trainers…) has levels [3, 4, 5]". The same applies to the woods grunt (L9) and to JOSH and TOMMY. The design only allows the leaders' levels (L206: "train to about the leader's level"). Two errands also depend on flags the player cannot see: shopping on `ADVENTURE_STARTED`, and healing at home on `RESCUED_BIRCH`.
*Fix:* keep fight levels only for fights the game names (the rival, ROXANNE). Decide to shop by reading the mart's list, and learn that MOM heals by talking to her.

**5. LOW–MED: it can loop on a goal it can never reach.** `_story_goal` never calls `_allowed`; only `seek` does. A find, use, talk or go that keeps failing therefore repeats until `STORY_PATIENCE`, which is about 33 minutes of game time. The docstring's "the next decision chooses another" is not true for story goals. Also, `ch4_gym_trainers` needs both JOSH and TOMMY beaten. TOMMY stands at (3,9) facing LEFT and sees 3 tiles (decomp `RustboroCity_Gym/map.json`). If the path to ROXANNE avoids him, ROXANNE never becomes a goal. I have not checked the gym layout, so this part is plausible, not shown.
*Fix:* apply the cooldown to story goals. Make gym trainers optional and prove `ch4_roxanne` on the badge alone.

**6. LOW: some proofs are thinner than they look.**
- CH2 is one Catcher trajectory replayed. `FULL-CH2` repeats CH2's f107850 and 138,555 frames, so it is not a second, independent run.
- Chapters 3 and 4 have never been run (the README says so).
- No live check confirms that every go goal with a map came after the page that named it. Mutant G30 only proves this in unit tests.

*Fix:* add a check to `rate_step5` over the log: each go goal with a map must come after the page that told it.

The sweep's A/B results themselves hold: NOHINTS reached 0 of 10, NOTRAIN showed 0 training windows, and DEADREST and STOPDEAD both told the fault apart from the fix.