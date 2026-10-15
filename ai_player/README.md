# ai_player: the Emerald AI that plays the game itself

`ai_player` is a program that plays Pokemon Emerald **with its own code**: walking, exploring,
battling, menus and decisions (USER RULING 35). The story bot is only its teacher; no bot code runs in
its play loop. It reads the game by memory injection and presses the buttons itself (RULING 36).
It is built to become a **single standalone program** that loads the ROM itself and can run
unattended as an art piece (RULING 37 Q1), so the brain (`mode.py`) is framework-free and sees the
game only through abstract interfaces, everything framework-specific sits in `host/`, and no path to
the bot is hard-coded.

Design: `PROJECT KNOWLEDGE/ai-research-notes/2026-10-07-ai-player-v1-DESIGN-DRAFT.md` (sections 10
and 11 win over 2-9) and `ai-agent/HUMAN-PLAY-DESIGN.md`.

**Where it is now: build step 5.1, the verifier's SECOND round** (section "Step 5.1, the verifier's second round" below;
final tree `d3d34871df0ac077`). The two failures and eight weak proofs are answered, and everything on that tree PASSED:
* the graded sweep on NEW held-out seeds 801-820, now with chapter 2 (WALLY's tutorial, 20 of 20; the intent-mix floor
  41-59 % in every chapter-2 run; the beeline's chapter 2 under it in 19 of 20);
* the six live arms, CH2T among them at 40 %;
* 137 of 137 mutants caught, the units and the milestone checks;
* the full regression of steps 0-4, every evidence file naming that tree.

‼ **A first graded pass FAILED one check, and is kept.** It ran on tree `d0c949e96d355afe`, held-out seeds 701-720: CH2's
floor in seed 706 measured 28.7 %. Its cause is fixed (G137, G138) and the Story's and Trainer's balance raised. Chapters 3
and 4 are still unplayed (the known limits).

**Before that, build step 5.1, the verifier's round** (section "Step 5.1, the verifier's round" below; its tree
`a883634ab24c3792`). The step-5.1 verifier's nine weak proofs and one rule violation are answered:
* the curiosity the story did not need is now graded in EVERY run, and the beeline control fails it;
* the errands' own divergence and the tiles no beeline stood on are measured;
* a battle-free no-speedrun time is added;
* the DETOUR is fixed (11 of the first round's 12 graded CH1 detours had ended at once), and a look-around debt added;
* "a new place" now means new to the carried world memory;
* the second path reads battles (fault arm STALL3);
* the training bounds are re-derived, and MAX_LOSSES 3 is proven (fault arm LOSE3);
* a story goal put aside comes back after 6,000 frames, and a walk its battles ate walks on.
‼ **Not all green:** the live arm CH2T fails the pre-registered intent-mix floor (28 % against 30 %), and the full
regression of steps 0-4 has not been re-run on this tree (both in that section). The first round's text follows.

**Build step 5.1, the story played HUMAN-LIKE** (section "The story, human-like (build step 5.1)" below;
first round's tree `c450adc2865848e4`): the step-5 verifier's FAILURE is fixed (two stand-stills of 600 and
1,200 frames in front of a screen that waited for a press: the starter's yes/no and a scene's text) and graded now as a
PROPERTY, by the AI's own record of every look and by a second path in the sweep: no screen waits for a press 300 frames
with none, whatever the reason given. The story is no longer a beeline (review #1): a personality-weighted LOOK-AROUND on
outdoor maps, DETOURS off the way, item curiosity (the rival's POKé BALL is found by it, not by a scripted step), chats,
measured as an INTENT MIX, a SEED DIVERGENCE and a beeline control (`AI_PLAYER_FAULT_NO_ERRANDS`). STORY_PATIENCE counts
from the last REAL progress (review #2); every step's map needs its OWN words or a visit, only fights the game names are
trained for, shopping is by the mart's list and home healing by MOM's words (review #3, #4); a failing story goal waits a
cooldown and the gym's trainers are optional (review #5). Below that, the step-5 text (unchanged):

**Build step 5, the AI plays the STORY itself** (section "The story (build step 5)" below): a new brain,
`AI_PLAYER_BRAIN=play`, plays from a real New Game toward a target milestone (`AI_PLAYER_TARGET`, default `ch1_pokedex`)
of the story to badge 1 (4 chapters, 20 milestones in `knowledge/milestones.json`, each proven by the game's own flags and
vars, every number checked against pret/pokeemerald). A GOAL MANAGER (`brain/goals.py`) reads where the story is and
chooses one goal at a time, always with a logged reason: the milestone's next step (go where the game SAID, ask the people
when it has not said, talk, use a thing, follow a scene) or a person's errand (heal when hurt, buy POKé BALLS once the
adventure has started, TRAIN by roaming before a known fight, pick up an item ball in view, catch new species, chat), by
the personality's weights (`personality.py`: Catcher, Story, Trainer, with a step-based DRIFT and a FAVOURITE Pokemon).
Chapter 1 (truck to POKéDEX) is played through; chapter 2 (to WALLY's tutorial) is the stretch; chapters 3 and 4 exist
as data only. The proofs are in that section.

**Build step 4, the AI's OWN BATTLES** (section "The battles (build step 4)" below): a new brain,
`AI_PLAYER_BRAIN=battle`, FIGHTS every battle with the AI's own decider (`brain/battle.py`) and hands (`skills/battle.py`):
a move chosen by its worth against THIS foe (type effectiveness x STAB x power x hit chance, minus a recoil penalty that
grows as its own HP falls), a seeded draw among the about-as-good moves, a switch when badly matched, a Potion in a
trainer's battle, RUN from a wild battle it does not want, and for a species it has not caught: weaken without knocking
out, then throw. It drives every battle menu by READING its cursor (FIGHT / BAG / POKéMON / RUN, the move grid, a double
battle's target, the bag's pockets, the party menu, every yes/no, the summary screen's forget-a-move list), sends in the
next Pokemon when one faints, learns a move by keeping the four worth most, and lets an evolution happen. Its game facts
are the AI's OWN knowledge files (`knowledge/`: the type chart, 354 moves with their recoil class, 386 species), extracted
from the bot's DATA with provenance and checked entry by entry against pret/pokeemerald (`gates/verify_knowledge.py`).
Proven live through the real launcher under the unchanged purity audit (`gates/live_step4.py`, 12 arms: a wild battle
won, a catch, a trainer, the rival, a walk up to the rival and a talk, the type chart in a double battle and its fault,
a faint and the next Pokemon sent in, a move learned, and since the verifier's round a double battle's partner fainting,
its step-4 fault, and a battle resumed on the party menu's refusal), by 82 unit tests (`gates/test_battle.py`), 43 mutants
(`gates/revert_step4.py`) and a seed sweep (`gates/rate_step4.py`, 185 in-process runs, each read by the GAME's own battle
every frame). The step-3 world brains still flee (their proofs stand).

**Build step 4.1, the step-4 verifier's and adversarial review's nine findings fixed** (section "Step 4.1" below;
everything on ONE tree, named there): the SHIFT question ("MAY is about to use TREECKO. Will ... change POKéMON?") is
judged about the foe its WORDS name, not the fainted one the battle view still holds, and the member chosen there is the
one sent; a move the game REFUSES is out for the turn (it was chosen again until the 150-menu bound); SWITCH, HEAL and RUN
are played live, each from a fixture made by button presses (`gates/make_step41_fixtures.py`) and each read by the game
(HEAL's first development run found the skill stuck after a Potion the game had already used: fixed); what a person
cannot see is gone from the choices (the foe's types are its species', a hit is a rough eighth, the ball by what is seen);
a small chance by temperament of a safe OPENING stat or status move, and a sleep or paralysis move to help a catch;
OVERKILL is not valued (moves that all finish the foe compare by hit chance and recoil); the explorer charges a place
chosen on the move for DOUBLING BACK on its journey (TOWN-Trainer's journeys 0.46 of their steps beyond the shortest known
way, now 0.32; 0.45 -> 0.33 on held-out seeds), with per-plan bounds and CROP's laps bounded, ‼ BUT the held-out
replication REFUTED two of those per-plan bounds (TOWN, TOWN-Catcher), TOWN-Catcher's journeys grew with the charge
(0.15 -> 0.22 held out) and the exploring plans' reversals went over the step-3.2 bound there (1.07 per 100 steps, bound
1.0); the step-4 sweep's new STATUS bound failed held out too (2, bound 3): see "Step 4.1"; the type chart's A/B has a second matchup and TYPE-DECISIONS
is labelled a hands check; the evidence archive keeps only the cited files plus an index (54 MB -> 1.5 MB). Proven by
`gates/live_step4.py` (19 arms: SHIFT, SHIFTX, HEAL, SWITCH, RUN, OVERKILL, OVERKILLX new), `gates/test_battle.py` (97),
`gates/revert_step4.py` (57 mutants, B44-B57 new), `gates/rate_step4.py` (its new plans, each by the game),
`gates/test_world.py` JourneyTests, `gates/revert_step3.py` (W90-W92) and the sweep's JOURNEY A/B (`gates/rate_step3.py`).
(That paragraph is step 4.1's first tree, kept as history: the journey charge, JourneyTests, W90-W92 and the JOURNEY A/B
are GONE since round 2.)

**Step 4.1 round 2, the verifier's failures fixed** (section "Step 4.1 round 2"): THE JOURNEY CHARGE IS REMOVED and the
doubling back is fixed where it came from, in the walk: the Trainer walks UP TO people it has not met (a people place, not
a pull to unseen tiles near them), someone standing further along the plan no longer breaks it and someone on its next
steps is waited for, and a detour bends instead of going two tiles aside and back (TOWN-Trainer's journeys 0.46 -> 0.25 of
their steps beyond the shortest known way, held out 0.45 -> 0.23, more people met in fewer steps). The opener is judged as
a RATE of the chances the decider SAYS it had; the refusal of a move (finding 2) and a catch's Sing are PLAYED live (arms
REFUSED, REFUSEDX, CATCHS, CATCHSX), the Trainer's walk too (TOWNT, TOWNTR). Seeds 1-10 and 101-110 are now development
seeds; the held-out replication, seeds 201-210, held everywhere (`rate_step3.py` and `rate_step4.py` both PASS), ‼ BUT
ONLY THERE: the step-4.1 verifier's second round played seeds 301-310 and `rate_step4.py` FAILED 3 of its 32 checks
(RECOIL-FAULT, REFUSED, REFUSED-FAULT: count bounds a chance process misses 11 % and 17 % of the time), and found the
foe's base stats still in the damage estimate: see round 3.

**Step 4.1 round 3, the step-4.1 verifier's second round fixed** (section "Step 4.1 round 3"): the damage estimate no
longer reads the FOE's base stats (a foe is guessed as a typical Pokemon of its level, the median of all 386 species, and
corrected by what its own hits are SEEN to take off the bar); every bound on a count of a chance event is now set where a
sample fails it with at most 0.1 % probability under a model the grader names (the decider's own chance for a draw, a
temperament, a fought seed; the 95 % lower bound of the development rate for the game's dice); the carried PID is played
where it matters (`rival_rustboro_hurt.ss1`: a party menu ranking again by level would send the Poochyena; arms SHIFTC,
SHIFTCX); an INDEPENDENT type matchup (Joey's Machop: Pursuit never with the chart, a draw at 1/2 without); a second source
of opener chances (OPENER-WILD); the journeys' excess split into the walking and the re-targeting; the evidence order made
harmless (`provenance.keep_earlier`) and the archive's uncited never-committed files packed (9.8 MB -> 4.5 MB, then 5.9 MB
with this round's two stopped graded passes in it); the
live_step2 leftover check made this run's only. Seeds 1.., 101.., 201.., 301.. are development seeds. ‼ The first
held-out run (seeds 401..) FAILED one check by a GRADER bug (TYPE-FAULT DOUBLE-FAINT pooled the PIDs of two send-ins in
one battle: seed 422, the first time both of the player's Pokemon fell); fixed, those seeds re-graded, and THE HELD-OUT
REPLICATION of the fixed grader, seeds 501.., PASSED (36 of 36). `rate_step3.py`'s first held-out run (401-410) FAILED one
of round 2's revert predictions (a tolerance of 0.03 a 10-seed sample misses one time in five); every revert prediction
was then re-registered by a 50-seed bootstrap, and its held-out replication, seeds 501-510, PASSED. Only the suites this
round touched were re-run; the full regression is the end of step 4.1's.

**The step-4 verifier's SECOND round** (sections "Step 3.2, the step-4 verifier's FAILURE and second round of weak
proofs" and "Step 4, the verifier's second round" below; everything on ONE tree, named there): the FAILURE, step 3.2's
finding 4 not fixed (the AI still made a new decision nearly every step, because a frontier at the screen's edge is seen
past at the next step), is fixed in the AI's code: a decision is CARRIED ON to the place that took its target's place, and
a new one is made only when nothing of it is left or something is clearly better; its visible cost (every journey's steps
beyond the shortest known way) is bounded, live and in the sweep, with an A/B against the step-3.2 rule. Found and fixed
on the way: a doormat is ONE way out, and a way back to a floor seen all of is no option while the front door leads on.
Findings 3 and 5 now have live arms (FORGET, REOPEN, and their reverts); every choice of the best move tells what the type
chart changed in it, and the sweep counts those choices against the GAME's own record of the move chosen each turn; a
refused switch is unit-tested; the gym-leader-level training is named NOT BUILT. Every trajectory number was re-registered
from development passes moved out of the evidence folder before the graded runs.

**The step-4 verifier's round** (sections "Step 4, the verifier's round" and "Step 3.2, the step-4 verifier's weak
proofs" below; everything on the tree `sha256:a14d81a107a65b76`, archived in `evidence/archive/a14d81a107a65b76/`): the replacement after a faint REMEMBERS the field through
the party menu (it sent the Grovyle standing on the field in a double battle and the battle stuck; it ranked every
replacement by level and HP), a refusal in the party menu is READ, the recoil is charged on the HP a hit can take, the
sweep and the in-battle live arms are graded by the GAME's battle read each frame, and a ring check sees the laps the
nothing-new check could not.

**Before that, build step 3.2, the step-3.1 adversarial review's human-likeness findings fixed** (section "Step 3.2"
below; its final runs' evidence is in `evidence/archive/3ea1b655920e8c61/`, moved there unchanged before step 4's runs
rewrote the file names): turning round is charged ONCE per decision and the decision's plan is FOLLOWED, so the AI turns back where step 3.1
walked laps (the step-3.1 rule reverted walks 342 steps beyond the shortest known ways in the sweep, this code 6; SCENEX's
worst walk with it reverted is 25 steps where 3 would do); LAPS and the walk against the shortest KNOWN way per target are
graded beside the reversals (pre-registered bounds on TOWN, ROUTE, SCENEX, SCENEX9, held at every clock instant); a bump
is forgotten once the way lets the player through, and dropped when its tile's look changes; a target chosen on the move
keeps the heading with no whim (88% of such choices kept it on the TOWN plans, 61% with the whim); a closed door reopens
on news a person could see, not on a count of the save's flags. Proven by `gates/test_world.py` (108 tests),
`gates/revert_step3.py` (74 mutants, W62-W75 this step's), `gates/live_step3.py` (34 arms, SCENEXL new) and
`gates/rate_step3.py` (its LAPS and WHIM reverts), all on the tree `sha256:3ea1b655920e8c61`.

**Before that, build step 3.1, the step-3 adversarial review's findings fixed, its verifier's nine weak proofs answered,
and that verifier's second round of eight answered** (section "Step 3.1, the verifier's second round" below: the warp-table
guard is now BEHAVIOURAL, every read the real eyes make checked against every map's warp array, `gates/warp_reads.py`; the
twin is known by her WORDS, at most 3 push-backs before news instead of 4; NEW WORDS heard in a scene that leaves the player
be are PROGRESS, so after meeting May the explorer tries the twin again, she lets it pass, and the explorer arm SCENEX now
runs to its own end on Route 101, answered there by the game; live reverts for the per-side bump and for finding 2 at
another seed; every pre-registered number machine-checked (`PREDICTED`), which at its first graded run found that THE
GAME READS THE HOST'S CLOCK, so three launcher arms' trajectories depend on when they are played (arm CLOCKS; every
in-process run now pins the cartridge's clock); the evidence folder's top level holds only evidence of the current tree,
`provenance.py --check-evidence`). Before that round (sections "Step 3.1" and "Step 3.1, the
verifier's round" below): the explorer no longer knows where a map ENDS
from negative coordinates (a tile past an edge is a road only once a crossing was SEEN: the same memory numbered +50 makes
the same choices); a frontier target the walk has made worthless is dropped on the move and turning back costs extra
(reversals on the AI's own steps, five exploring plans x 10 seeds: 11 in 2,119 steps, against 89 in 2,795 and 252 stale
targets walked onto with these two rules reverted, `evidence/2026-10-08-step3-RATE.txt` REVERT); a scene that keeps
sending the player back (Littleroot's twin) gives its target up after the second time, and the TILE it sent the player
back from is not stepped on again, so the explorer's next target behind her is out of reach and it looks elsewhere; a
bump belongs to the SIDE it came from (the player's room's one-way tile is now crossed east-west); exits are known by how
they LOOK (the eyes no longer read the ROM's warp table; a door that does not open is remembered closed, until the story
moves on or 10 minutes pass); the gate's crop window is written as literals; an exit's stand tile is always a seen tile;
ROAM reports both spin ratios. Every live grade of these now tells the fixed code from the reverted one: revert arms
HOUSER, TOWNR, ROUTER, EDGER, SCENER, SCENEXR beside their real arms, and replications at another seed through the launcher
(TOWN9, ROUTE9). Proven by `gates/live_step3.py` (22 arms), `gates/test_world.py` (79 tests), `gates/revert_step3.py` (51
mutants, W30-W51 this step's) and the seed sweep with its own revert A/B (`gates/rate_step3.py`).

**Build step 3, the WORLD MODEL and the AI's OWN NAVIGATOR** (section "The world and the navigator
(build step 3)" below): the AI WALKS, with its own code and its own hands, over a memory of what it has SEEN. It
remembers every tile its 15 x 11 window has shown (and from where), learns warps when it uses them and map connections
when it walks off an edge, learns a hidden wall by bumping into it once, explores the frontier of what it has seen
with its personality's taste, roams grass without spinning, and flees wild battles by choosing RUN with the cursor
read. Proven live through the real launcher under the unchanged purity audit (`gates/live_step3.py`, 11 arms: out of
the player's house, through Littleroot knowing nothing, up Route 101 to Oldale, 150 roaming steps in grass with 13
battles fled and a 0.7% spin ratio, the crop's fault arm, a stairs ping-pong ended as `stuck:`, a hidden wall bumped
once and avoided after, its revert, a trainer battle declined with a reason, an experience gain moving an intent's
novelty clock and its revert), by unit tests against a grid model of the overworld (`gates/test_world.py`, 46 tests)
and by 29 mutants of the real code (`gates/revert_step3.py`); a seed sweep (`gates/rate_step3.py`, 10 seeds per plan,
in-process) measures how often each walk succeeds. The step-3 verifier's five weak proofs were answered in a second
round (section "Step 3, the verifier's weak proofs" below): the explorer picks among about-equal places on a seeded
WHIM (seeds now choose different targets, not only different paths), the end position is checked by the GAME'S OWN
BEHAVIOUR (`gates/game_answer.py`), progress counts experience, the roaming metrics count every press, and the crop's
fault arm no longer leans on a step count. Its re-verification listed five more weak proofs, answered in a third
round (section "Step 3, the verifier's second round" below): CROP checks the goal map by save block 1, STUCK's end tile
is answered by the game (the controls locked) and the ROM (where the stairs leave the player), a live arm shows an
experience gain moving an intent's novelty clock (XP, and its revert XPR), the ROAM grader shows every press that did
not move the player was pre-empted by a battle, and the evidence pins the predictions it was graded against. (Since
step 3.1 some of these facts changed: see "Step 3.1" below. The tables of this section and the two after it quote
step 3's own final run; step 3.1's run rewrote the evidence files under the same names, so step 3's text is in git at
commit 12b25140.)

**Build step 2, the HANDS** (section "The hands (build step 2)" below): the AI presses the
buttons ITSELF, at a person's pace, for text and menus. It plays a New Game from the title screen to the
moving truck (gender and name chosen by its personality, the name TYPED on the keyboard), heals at a Pokemon
Center nurse, buys Poke Balls at a mart and sets the wall clock in the player's room. Every A that moves a
text on is pressed only when the eyes say the game waits for it, and every cursor is moved by READING it. The
eyes now also see the open menu and its cursor, the keyboard, the clock, the mart's list and quantity, and
the text on screen. Proven live through the real launcher under the unchanged purity audit
(`gates/live_step2.py`: 4 skills, 3 fault arms that show the harm a naive driver does), and by unit
tests on screens the eyes really saw (`gates/test_hands.py`). STEP 2.1 (section "Step 2.1" below) answered the
step-2 verifier's weak proofs: every A press of every skill is now checked against the GAME'S behaviour in forks
of its frame (arms WBI, WBN, WBM, WBC, with a control and a fault arm), every A press of a real run is classified,
no idle stretch is logged under a catch-all reason (the eyes see fades and scenes), the clock's fault arm is
pinned, a warp that differs in y only is played live (`live_step1.py` WARPY), and a 20-seed RATE arm measures
how often each skill succeeds. Its second round (section "Step 2.1, the step-2 review's items") added a stall detector
(an unknown prompt is reported `stuck:` after 300 unchanged frames, not watched for 3 minutes), a working-tree digest in
every evidence file, the pad's frames asserted against the instrument's, every START / B / SELECT press checked against
the game (a fade means "not taking input"), an exact name check, immediate failure reports (which uncovered the gender
menu's sprite slide), and a revert proof for the host's torn-party rule. Each skill is its own brain
(`AI_PLAYER_BRAIN=intro|nurse|mart|clock`); the nurse, the mart and the clock start from fixtures that stand in front
of them (step 3's navigator walks, but no brain yet chains a walk and a skill: that is step 5's goals).

**Step 1.1, the EYES after their adversarial review** (section "The eyes" below): the AI reads the game into
an immutable `Observation` (what is on screen, the party, the PC boxes, the bag, progress, a battle's two
sides), writes an ACTION LOG, and prints the lines the learner's scorer reads. A second brain, the WATCHER
(`AI_PLAYER_BRAIN=watcher`), looks every N frames and presses nothing; it is how the eyes were proven against
ground truth live (`gates/live_step1.py`, 21 arms since step 2.1 added WARPY) under the unchanged purity audit. The default brain is still
step 0's placeholder. Step 1.1 (section "Step 1.1" below) fixed the six findings of the step-1 review and two
more its new live arms found, each with a test or arm that fails when the fix is reverted.

**Step 0.1, purity scaffolding after its adversarial review.** The placeholder brain presses nothing,
waits `--frames` frames and gives up with reason `step0-placeholder`.
What step 0 delivers is the boundary every later step stands on: listener isolation (now including
the framework's listener-REBUILD door), action attribution with a sink audit and a bot-code monitor,
a verdict file only the instrument can write, a lifecycle that can never park, and two gates (static
and live) that were each broken by independent verifiers and then fixed. Step 0.1 fixed the ten
findings of the adversarial review of step 0; each fix has a live arm or a unit test that FAILS when
the fix is reverted (the mutant arms `M*` and the mutant halves of `gates/test_host.py`). Its second
round fixed what the verifier of those fixes found: a hung brain could not be stopped from its console
(`IH`), a `peek_frame` held open on the main thread switched the live audit off (`XW`, `M8`, `M8c`),
the lifecycle's state was writable unseen (`XK`), and three findings lacked the proof the review asked
for (debug mode live: `G`, `M6`; a FOREIGN rewind: `RLF`, `M1r`; a real revert of the hook: `test_host`).
Its third round fixed the two notes that verifier left: the INTERRUPT-WATCH RACE (a main thread that
woke up while the watch thread was finishing the run ran its next frame unaudited, or after the
verdict as a false `ran-after-finish` BREACH, and the watch called it "stuck" without measuring; now the
instrument's frame fence holds that frame back and the watch says what it measured: `IG`, `IR`, `M9`,
`M9w`, `M9r`, `test_host` `FrameFenceTests`), and the REGISTRY ROUTE (`_REGISTRY.payload_of(counters)
.add("real_frames", None, None, 5)` was accepted uncounted and could turn an UNVERIFIED run CLEAN; now
the registry and the counter stores answer only the instrument's own file: `XK`, `M3`, `test_host`
`UnverifiedToCleanTests`).

## Run it

From the repo root (the folder that contains `ai_player/`):

```
py -3.12 -m ai_player run --profile NAME [--frames N] [--wall-seconds S] [--fresh | --state PATH]
                          [--run-dir DIR] [--allow-ungated]
```

* **gates first**: runs `gates/check_purity.py` on THIS package and the hook it will start, prints
  `[AI-GATE] exit=N verdict=PASS|FAIL package=...`, and refuses to launch on a FAIL (exit 7) unless
  `--allow-ungated` is given (only the fault arms do that, on purpose);
* creates `sandbox-pokebot/profiles/NAME/` if missing: copies ONLY `metadata.yml` (the ROM binding)
  from an existing profile and writes a `.ai_player_profile` marker (as
  `tools/story-dev/x4_headless.py` `ensure_lane_profile` does for lanes);
* **the HTTP server is OFF for every run**: on every run of an ai_player-owned profile the launcher
  REWRITES its `http.yml` with `enable: false` and says so in the header
  (`[AI-RUN] http_server=off (forced: ...)`). The sandbox's global `profiles/http.yml` switches the
  server ON (a fork divergence), and its `work_queue` callbacks would run framework code between the
  AI's frames. A profile the launcher does not own is left alone, and the session then refuses to
  start (exit 9) if the server is on;
* `--fresh` deletes the profile's `current_state.ss1` and `current_save.sav`, so the game boots to the
  title screen and New Game; `--state PATH` copies a save state to `current_state.ss1`, which the
  emulator loads at startup (`modules/libmgba.py`, `LibmgbaEmulator.__init__`). Both refuse to touch
  a profile without the marker, so a person's own profile is never changed;
* starts `sandbox-pokebot/pokebot.py NAME -m "AI Player" -s 0 -na -hl` (the batch runner's flags:
  unthrottled, muted, headless) in a child process, with `PYTHONPATH`, `PYTHONHOME`,
  `PYTHONPYCACHEPREFIX` and `PYTHONSTARTUP` removed from its environment (they would load code from
  places the gate never read), and echoes its output;
* **two wall clocks**: a few seconds before `--wall-seconds` (10%, 5-30 s) the mode ends ITSELF with
  `reason=wall-clock code=124` and still writes its verdict; if it is stuck and cannot, the launcher
  kills the whole process tree at `--wall-seconds` (exit 124) and prints `[AI-RUN] NO PURITY VERDICT`.
  Ctrl+C in the launcher's console kills the tree too (exit 130, `[AI-RUN] INTERRUPTED`): the child
  has no console of its own, so it never sees that Ctrl+C;
* **grades the run from the verdict file**: reads `<run_dir>/purity.json` (written by the instrument,
  see below) and prints `[AI-RUN] verdict file: verdict=... exit_reason=... exit_code=...`. It exits
  with the child's exit code, except that a child exiting 0 without a CLEAN verdict file for the gated
  package makes it exit 8.

Options travel to the mode as environment variables (`ai_player/options.py`): `AI_PLAYER_FRAMES`,
`AI_PLAYER_RUN_DIR` (the run's `ai_player.log`, `actions.jsonl` and `purity.json` land there),
`AI_PLAYER_PACKAGE_ROOT` (the hook APPENDS it to `sys.path`, after the standard library),
`AI_PLAYER_WALL_DEADLINE`. `--build-root` / `AI_PLAYER_BUILD_ROOT` points at a different framework folder.
Build step 1: `AI_PLAYER_BRAIN=placeholder|watcher` (default placeholder) and `AI_PLAYER_WATCH_EVERY=N`
(default 60) choose the brain; the launcher passes its environment to the child, so

```
AI_PLAYER_BRAIN=watcher py -3.12 -m ai_player run --profile ai-step1-eyes --frames 600 --state tools/story-dev/saves/route116team.ss1
```

watches a save for 600 frames: `[AI-EYES]` digests on stdout, the Observations in `<run_dir>/actions.jsonl`.

Build step 2: the HANDS brains, `AI_PLAYER_BRAIN=intro|nurse|mart|clock`, each play one skill and give up with
its outcome (`[AI-EXIT] reason=intro: in the truck; intended Rosa (GIRL) code=0`). Their options (read by the
brain itself through `options.py` `HandsOptions`, because the host is finished: see "The hands"):
`AI_PLAYER_SEED=N` (the run's seed; unset: drawn from the clock and logged), `AI_PLAYER_PERSONALITY=Catcher|
Story|Trainer` (unset: drawn from the seed), `AI_PLAYER_MART_ITEM` (default `POKé BALL`), `AI_PLAYER_MART_COUNT`
(default 5), `AI_PLAYER_CLOCK=HH:MM` (default: the computer's local time). For example

```
AI_PLAYER_BRAIN=intro AI_PLAYER_SEED=3 py -3.12 -m ai_player run --profile ai-step2-hands --frames 16000 --wall-seconds 900 --fresh
AI_PLAYER_BRAIN=mart AI_PLAYER_MART_COUNT=5 py -3.12 -m ai_player run --profile ai-step2-hands --frames 8000 --state ai_player/gates/fixtures/mart_rustboro.ss1
```

plays a New Game to the truck (seed 3: Catcher, GIRL, "Rosa"), and buys 5 Poke Balls in the Rustboro Mart.

Build step 3: the WORLD brains, `AI_PLAYER_BRAIN=explore|roam|goto` (`options.WORLD_BRAINS`), played by the same
`HandsBrain` with a world memory and the navigator. Their options: `AI_PLAYER_GOAL_MAP` (explore until the player
stands on this map, named as the eyes name it: `LITTLEROOT_TOWN`, `ROUTE101`, `OLDALE_TOWN`; unset: explore until
stuck or out of frames), `AI_PLAYER_ROAM_STEPS` (default 120), `AI_PLAYER_GOTO` (`x,y;x,y`: errands to tiles of the
current map), `AI_PLAYER_WORLD` (a `world.jsonl` a previous run wrote: start from its last snapshot), and
`AI_PLAYER_INTENT_FRAMES` (the intent's own budget; default the run's frames - 600). `AI_PLAYER_PERSONALITY` picks the
explorer's taste. For example

```
AI_PLAYER_BRAIN=explore AI_PLAYER_GOAL_MAP=ROUTE101 AI_PLAYER_PERSONALITY=Story AI_PLAYER_SEED=3 py -3.12 -m ai_player run --profile ai-step3-world --frames 20000 --state tools/story-dev/saves/pokedex_done.ss1
AI_PLAYER_BRAIN=roam AI_PLAYER_ROAM_STEPS=150 AI_PLAYER_PERSONALITY=Catcher py -3.12 -m ai_player run --profile ai-step3-world --frames 40000 --state ai_player/gates/fixtures/route101_south.ss1
```

walks out of Birch's lab, through Littleroot (knowing nothing of it) and onto Route 101; and roams Route 101's grass
for 150 steps, fleeing what it meets. The run writes `<run_dir>/world.jsonl` (the memory, a snapshot line at every map
change and at the end) beside its action log.

Build step 4: the BATTLE brain, `AI_PLAYER_BRAIN=battle` (a world brain too: the same memory and navigator). It plays the
battle on screen at the start, then walks up to and talks to the person at `AI_PLAYER_TALK_TO` (`x,y` on the current
map: a trainer, the rival), then roams the grass and FIGHTS what comes, until `AI_PLAYER_BATTLES` battles (default 1) have
ended; it ends with `battles: N played: [outcomes]` (the game's own `gBattleOutcome`: won, lost, ran, caught, ...), or
`rest: ...` when a person would stop training and look for a Pokemon Center (its strongest Pokemon fainted or under a
third of its HP), or `stuck: ...` (a lost battle is `stuck: the battle was lost`). `AI_PLAYER_PURPOSE=train|travel`
(default train: wild battles fought for experience, run from when its Pokemon is low or the foe far stronger; travel: a
wild battle it does not want is run from by its temperament). `AI_PLAYER_PERSONALITY` sets the temperament (how near the
best a move must be to be drawn, how much it wants a new species, how willing it is to switch, when it heals). For example

```
AI_PLAYER_BRAIN=battle AI_PLAYER_BATTLES=4 AI_PLAYER_PERSONALITY=Story AI_PLAYER_SEED=3 py -3.12 -m ai_player run --profile ai-step4-battle --frames 40000 --state ai_player/gates/fixtures/route101_south.ss1
AI_PLAYER_BRAIN=battle AI_PLAYER_TALK_TO=10,3 AI_PLAYER_SEED=1 py -3.12 -m ai_player run --profile ai-step4-battle --frames 20000 --state tools/story-dev/saves/route103.ss1
```

roams Route 101's grass and plays four wild battles; and walks up to May on Route 103, talks to her and plays the rival's
battle. The in-process harness runs the same brain: `py -3.12 ai_player/gates/hands_harness.py battle --state PATH --seed N
--battles N [--talk-to X,Y] [--fault ignore_types|ignore_recoil|uncapped_recoil|forget_field|ignore_refusal, or several
joined by commas] [--battle-log] --game-clock 2026-10-08T06:00` (`--battle-log`: the GAME's battle read after every frame,
test side: each battler's chosen move, each HP change with its user, move and target, each Pokemon that came onto a
position). The launcher's fault switches are `AI_PLAYER_FAULT_IGNORE_TYPES`, `_IGNORE_RECOIL`, `_UNCAPPED_RECOIL`,
`_FORGET_FIELD`, `_IGNORE_REFUSAL` (`options.py`), and since step 4.1 `_OVERKILL` (every move valued uncapped: step 4's
valuation), `_SHIFT_FAINTED` (the shift question answered about the fainted foe, step 4's answer) and `_FORGET_UNUSABLE` (a
refused move chosen again, step 4's loop); the harness takes them as `--fault overkill|shift_fainted|forget_unusable`; and
since step 4.1 round 2 `_NO_CATCH_STATUS` (no sleep or paralysis move to help a catch) and `_IGNORE_PP` (the decider blind
to its moves' PP, so the GAME refuses a move with none: finding 2 played live), `--fault no_catch_status|ignore_pp`. For
example

```
AI_PLAYER_BRAIN=battle AI_PLAYER_PERSONALITY=Trainer AI_PLAYER_SEED=1 py -3.12 -m ai_player run --profile ai-step4-battle --frames 30000 --state ai_player/gates/fixtures/rival_rustboro.ss1
```

plays Rustboro's rival with the Marshtomp leading: when her Wingull falls and the game asks "MAY is about to use TREECKO.
Will ... change POKéMON?", the AI switches to its Taillow (step 4.1's fixtures: `gates/make_step41_fixtures.py`).

Build step 5: the PLAY brain, `AI_PLAYER_BRAIN=play` (a world brain: the same memory, navigator and battle decider). It
plays the story toward `AI_PLAYER_TARGET` (a milestone id of `knowledge/milestones.json`; default `ch1_pokedex`; e.g.
`ch2_wally`, `ch4_roxanne`) and ends with `play: done: <target> reached`, or `play: stuck: no progress for N frames
(... since <milestone>)` (`mode.py` STORY_PATIENCE, since step 5.1 counted from the last REAL progress; step 5 said "no
milestone for N frames"), `play: ... battles lost` (MAX_LOSSES), or the frame budget. From a fresh
boot it plays the intro itself (the title screen, the AI's name and gender, the truck). `AI_PLAYER_STARTER=TREECKO|
TORCHIC|MUDKIP` names the starter (unset: the personality's lean, drawn from the seed); `AI_PLAYER_PERSONALITY`,
`AI_PLAYER_SEED`, `AI_PLAYER_CLOCK` (the time it sets on the wall clock) and `AI_PLAYER_WORLD` (a `world.jsonl` a previous
run wrote, its recognised POKéMON CENTER and MART doors included) work as before. For example

```
AI_PLAYER_BRAIN=play AI_PLAYER_STARTER=TORCHIC AI_PLAYER_PERSONALITY=Catcher AI_PLAYER_SEED=12 AI_PLAYER_CLOCK=10:00 py -3.12 -m ai_player run --profile ai-step5-play --frames 330000 --wall-seconds 3600 --fresh
AI_PLAYER_BRAIN=play AI_PLAYER_TARGET=ch2_wally AI_PLAYER_WORLD=<that run's dir>/world.jsonl AI_PLAYER_SEED=12 py -3.12 -m ai_player run --profile ai-step5-play --frames 330000 --wall-seconds 3600 --state <that run's end state>
```

plays a New Game to the POKéDEX with a Torchic, then chapter 2 from where it stopped. The in-process harness runs the same
brain: `py -3.12 ai_player/gates/play_harness.py --fresh --seed N --personality P --starter S --target T --frames F
--game-clock 2026-10-14T10:00 --clock 10:00 [--fault no_hints|no_training|no_errands] [--state PATH --world-in WORLD]
[--save-end PATH] [--run-dir DIR] [--checkpoints DIR]` (the cartridge's clock PINNED, so a seed replays; its recorder reads
the game's marks and counters every 30 frames by a second path; since step 5.1 its `WaitRecorder` reads every 10 frames
whether the GAME waits for a press, by the framework's own reads, beside the presses: `waits_game` in its PLAY line; `truth
STATE` reads a saved state the same way). Step 5.1's beeline control: `AI_PLAYER_FAULT_NO_ERRANDS=1` (`--fault no_errands`).
Since the step-5.1 verifier's second round the sweep plays chapter 2 too: `py -3.12 ai_player/gates/rate_step5.py --plans
CH1,ERRANDS_OFF,CH2,CH2_OFF --seeds 9 --first-seed 41` goes on from each chapter-1 run's own end state and world memory to
WALLY's tutorial, in the same worker; every graded driver keeps its tree (`py -3.12 ai_player/gates/provenance.py
--snapshot`, `--compare A B`).

## Layout

| file | what it is for |
|---|---|
| `mode.py` | the BRAIN, framework-free: `Brain.play(controls, eyes)` over the abstract `Controls` / `Eyes` interfaces; returns its give-up reason (step 0: a placeholder; step 1 adds `WatcherBrain`; step 2 adds `HandsBrain`, reached through `Brain` because the session is finished; step 3 its world brains, the memory and its `world.jsonl`) |
| `world/memory.py` | step 3: the WORLD MODEL (framework-free): per map every tile SEEN and where it was seen from, visits, people and item balls, tiles learned blocked by bumping, learned edges; the warp graph (used, and the way back inferred), the connections and every map change (warp or connection, the AI's or a scene's); persistence (`to_dict`, `snapshot`, `read_world`); since step 3.2 bumps forgotten (`forget_bump`, `take_dropped_bumps`) and the NEWS a person could see that reopens a closed door (`news`, `heard`); since the step-4 verifier's second round a DOORMAT is one way out (`mat_tiles`); since step 4.1 round 2 WHO each person on screen is (`persons`, by the object's local id), who stands on the screen now (`people_now`) and who the player has MET (`met`: stood within `MEET_RADIUS` tiles of them) |
| `brain/navigator.py` | step 3: the AI's OWN NAVIGATOR (framework-free): A* over the memory (unknown tiles optimistic but costly, ledges one way, exits used on purpose), walking in held chunks with a look between, bumps learned, people waited for, warps and doors used by the right press, interruptions (a battle fled, a scene read through); every `Intent` bounded by a budget progress does not reset, progress = NOVELTY, `stuck:<reason>` (no novelty, a ping-pong, nothing left, a trainer battle); since step 3.2 a decision's PLAN followed (`Plan`, `_next_step`: turning round charged once, `TURN_ROUND_COST`; a clearly better way switched to, `PLAN_SWITCH_MARGIN`) and the heading told to the explorer (`heading`, `choosing_on_the_move`); since step 4.1 round 2 someone standing on the followed plan further on than `PERSON_AHEAD` steps does not break it and someone on its next steps is WAITED for (`WAIT`, `PERSON_PLAN_WAITS`), a detour BENDS the way (`DETOUR_EXTRA`), a person met makes a PEOPLE target stale (`stale_reason`, `Target.who`, `people_tries`) |
| `brain/explore.py` | step 3: where to go next: the frontier, roads past an edge, unused exits, grass and people, scored by the PERSONALITY's weights (`WEIGHTS`), a known route to the goal, a WHIM among about-equal places (`pick`, `CHOICE_MARGIN`), never idle (it wanders); `explore_intent`, `goto_intent`; since step 3.2 a choice ON THE MOVE keeps the heading (`pick_on_the_move`, `ahead`); since the step-4 verifier's second round a decision is CARRIED ON past a target the walk made stale (`carry_on`, `opened`, `further`, `beyond`, `CARRY_RADIUS`, `CARRY_SWITCH_MARGIN`); step 4.1's journey charge is GONE since step 4.1 round 2 (its verifier: it made TOWN-Catcher worse); since round 2 the Trainer's taste for people is a PEOPLE place, the seen tile beside a person not met yet, walked up to once (`PEOPLE_RECENT`; `navigator.MEET_TRIES`), not a bonus on unseen tiles near people |
| `brain/battle.py` | step 4: the AI's OWN BATTLE DECIDER (framework-free): a move's worth (`move_value`: type x STAB x power x hit chance, minus `recoil_penalty`), the near-best draw (`choose_move`), switching (`matchup`, `better_member`), healing in a trainer's battle, running, the catch (weaken under `KO_MARGIN`, then the ball), who goes in after a faint (`replacement`), the battle's questions by their words (`answer`), which move to forget (`learn_choice`), when training should stop (`needs_rest`); the personality's `Temperament`; the FAULT switches `BattleFaults`; since the step-4 verifier's second round every choice of the best move tells what the type chart changed in it (`TypeSay`); since step 4.1 the shift question about the foe its words name (`incoming`, `_shift`, `shift_to`), the moves the game refused this turn (`cannot_use`), the types a person knows (`seen_types`), a rough sense of a hit (`rough_share`, `damage_fraction`), finishers worth as the strongest (`_ko_worth`), safe openers and a catch's sleep or paralysis (`_opener`, `_catch_status`, `_safe_for_status`), the ball by visible cues (`_ball`); since step 4.1 round 2 an opener the draw passes over is SAID with the move chosen ("no opener this time": the sweep counts the rule's chances), a species named with a full stop or a sign read whole (`incoming`: MR. MIME, NIDORAN♀), and the FAULTS `no_catch_status` and `ignore_pp` (the arms CATCHSX, REFUSED) |
| `skills/battle.py` | step 4: playing a battle to its end (`play_battle`): every text advanced on the eyes' waits, every battle menu chosen by reading its cursor (the action and move grids, a double battle's target, the bag's pocket and item and USE, the party menu and SHIFT / SEND OUT, the yes/no, the summary screen's forget-a-move list), every decision logged with its reason; the outcome is the game's `gBattleOutcome` |
| `knowledge/` | step 4: the AI's OWN game facts, `types.json` (the Gen-3 chart), `moves.json` (354 moves: type, power, accuracy, PP, effect, priority, target, category, recoil class), `species.json` (386 species: types, base stats, catch rate, experience yield), each with its provenance (the bot's data file it was extracted from and that file's sha256); `facts.py` reads them (the play loop never reads the bot's data) |
| `brain/goals.py` | step 5: the GOAL MANAGER (framework-free): which milestone the marks prove (`milestone`, a waypoint passed on its map), ONE goal at a time with its reason in a fixed order, HEAL, SHOP, TRAIN, ITEM, CATCH, CHAT, then the STORY step (`next_goal`, `_story_goal`: go where the words heard say, `ask` the people of a place when nothing was said, `seek` someone seen earlier where they stood, `find` them, `use`/`talk`/`follow`), the doors it recognises by their look (`notice`, kept in the world memory), the training target from the fight's levels and the personality's margin (`prep`), a goal that failed twice put aside (`FAIL_LIMIT`, `COOLDOWN_DECISIONS`; a heal not, when the party is in danger); the way to an unknown place (`lead_toward`: out to the open map with most left to see, or a building's own town; `travel_intent`); the roam's rest (`training_rest`, installed by `GoalRunner.roam_hooks`), the losses (`battles_lost`); and `GoalRunner`, which plays each goal with the navigator, roaming and the story skills; step 5.1: the look-around (`may_look_around`, kind `explore`) and the detour (`_detour`), the new-map stop, item curiosity (`_remembered_ball`), each step's own words (`step_known`), the fights a person knows (`fight_levels`, `training_target`), the mart by its list (`no_balls`), home healing by experience (`home_heals`, `_saw_mom_heal`), finding a centre (`find_center`), hurt walks out of the grass, the story's cooldown (`aside:`) and the scene walls carried within a milestone; step 5.1's verifier's round: a new place is new to the carried world memory (`_Memory.known_before`), the look-around debt (`LOOK_DEBT`) and every draw told (`say`), the detour walks to a place it chose (`DETOUR_MIN_TILES`, `DETOUR_TRIES`), a story goal put aside comes back after `STORY_ASIDE_FRAMES`, and a walk whose battles ate its budget walks on (`_walk_on_after_battles`, `_BattleClock`, `GO_BATTLE_EXTENSIONS`); the verifier's second round: a GYM by its door's look (`door_of`, `is_gym`, `GoalRunner._to_building`), the nearest place to heal or shop (`_nearest_place`; a door past a crossed edge is not that map's, a door that cannot be walked into is forgotten, `DOOR_UNUSABLE`), a town's own centre looked for first (`find_center` with `via`), the BALANCE (`spent`, `owed`, `OWED_STOP`, `AGAIN_MAX`, the curiosity minimum), its first POKé BALLS tried, the story's own person no chat, `DANGER_RETRIES`, `ASIDE_LOOK_MIN`, and whose rule judged a fight's training done (`fight_prep` `judged_by`) |
| `skills/story.py` | step 5: the story's person-level skills: talk to someone seen (beside or across a counter), use a thing, pick up an item ball (read what was found), walk into a door, the nurse and the clerk (found by their look), the starter chosen in the bag by its cursor, a scene's yes/no answered by its words (`answer_question`, `QUESTION_RULES`), a scene played to its end (`play_out`) |
| `knowledge/milestones.json`, `knowledge/story.py`, `knowledge/wild_species.json` | step 5: the story to badge 1 as DATA (20 milestones in 4 chapters: proofs, maps, steps, the game's own hint, the fight's levels), extracted from the bot's `story/early_game.py` (teaching material, named with its sha256) by `gates/extract_milestones.py` and checked against pret/pokeemerald by its `--verify`; `story.py` reads it (which milestone the marks prove, the player's own gender's houses); the species a person meets in the wild (the favourite's pool) |
| `skills/roam_train.py`, `skills/flee.py` | step 3: training by ROAMING through seen grass (training steps, every press an attempt, the spin ratio over the training steps, distinct tiles, encounters fled); a WILD battle fled by choosing RUN on the cursor read (a trainer battle: the reason, nothing pressed) |
| `hands/pad.py` | step 2: the PAD (every press a jittered hold and gap, a gate it names, logged; reading and thinking delays; never an idle without a reason) and `Hands`, what every skill holds (eyes, pad, the choices stream, the faults, the log) |
| `hands/dialogue.py` | step 2: advance text only on the eyes' waits, stop at every menu; start a conversation only while the player is free (`talk`); step 5.1: what on screen waits for a press (`awaits_press`) and `talk(give_way=True)`, which gives a screen that waits for a press back to its caller at once (the story skills use it; the default is step 2's rule) |
| `hands/waiting.py` | step 5.1: `WaitWatch`, a hands watcher the play brain installs: every stretch a screen waited for a press with none (a text waiting for A/B, a menu taking input), whatever busy reason the pad gave meanwhile; the stretches of 60 frames or more go to the action log (`decision` "await"), the longest to the end record (the graders' STALL PROPERTY) |
| `hands/menus.py` | step 2: move a cursor by reading it, choose by intent, answer a yes/no, type a name, set the clock, the "How many?" box, and the nurse (`nurse_heal`) and the mart (`mart_buy`); the step-5.1 verifier's second round: with `give_way` (the story's skills; the step-2 default unchanged) a screen that waits for a press before the talk is handed back at once (`GAVE_WAY`) |
| `skills/intro.py`, `skills/clock.py` | step 2: the New Game intro from the title screen to the truck; the wall clock in the player's room |
| `personality.py` | step 2: the base personality (Catcher, Story, Trainer) and the intro's two choices, gender and name, by a personality-weighted draw from the seed; step 5: each personality's ERRAND weights (`Errands`, `ERRANDS`: training margin and minimum, catching, balls, healing, chatting), the step-based DRIFT to another personality and back (`PersonalityState`, `DRIFT_EVERY`, `DRIFT_CHANCE`, `DRIFT_STEPS`, every drift logged), the starter's lean (`choose_starter`) and the FAVOURITE Pokemon (`choose_favourite`, a wild species; the shiny hunt is deferred) |
| `eyes/screens.py` | step 2: the eyes' perception of menus and text (framework-free): which menu is open by its input task, its cursor, the keyboard's layout, the charmap, the tasks that wait for A/B |
| `eyes/observation.py` | the immutable `Observation` and its parts (framework-free): what one look sees |
| `eyes/view.py` | the AI's perception rules (framework-free): the on-screen window, tile behaviours, object kinds, the screen, when a text waits for a button (`text_printer_wait`), the story flags; tables from pret/pokeemerald |
| `eyes/party.py` | how a party Pokemon is stored, decoded by the AI's own code (framework-free) |
| `host/eyes.py` | the ONLY file that reads the game: implements `Eyes.look()` through read-only framework doors |
| `memory_log.py` | the ACTION LOG records and the SCORER LINES, built from Observations (framework-free) |
| `host/session.py` | the run inside the framework: start-up refusals (debug mode, HTTP on), Ctrl+C handlers and the interrupt watch thread, the guard callback (park, frame budget, wall clock, interrupt), listener wiring, and driving the brain one frame per `yield` |
| `host/controller.py` | the ONLY place the AI presses buttons or lets frames pass (implements `Controls`) |
| `host/isolation.py` | removes every framework listener the AI does not own, owns `modules.main.get_bot_listeners` (the rebuild door) while the AI runs, restores both on exit |
| `host/attribution.py` | the instrument: counts inputs, writes, loads, clock changes, frames and bot-code calls by origin, audits the sinks, that isolation held and that it saw every main-loop frame, writes the verdict file, seals the host modules, provides `Guarded`, arms the exit watchdog, and holds the FRAME FENCE (no thread but the finishing one runs a frame while the run is being finished) |
| `host/lifecycle.py` | the single exit door (single-entry across threads); exit codes |
| `host/launcher.py` | the CLI side (launcher process): the gate, the profile, HTTP off, the child process, the wall clocks, the verdict file |
| `options.py`, `runlog.py` | run options from the environment; the AI's own log and its action log file (`RecordFile`) |
| `evidence/` | every live and mutant proof's evidence file of the CURRENT tree, at the top level (each names the tree's digest: `provenance.py --check-evidence`); since step 4.1 the archive keeps only the earlier trees' files a document or a commit message CITES, in `evidence/archive/<digest>/`, and lists every other one in `evidence/archive/INDEX.md` (its `git show` line: it stays in git history); the policy is `archive/README.md`, applied by `gates/prune_evidence.py` |
| `gates/` | TEST SIDE: the purity gate and its fault tests, the host unit tests, the live proof drivers (`live_step0.py`, `live_step1.py`, `live_step2.py`), the eyes' unit tests (`test_eyes.py`) and ground-truth probe (`probe_eyes.py`), step 1.1's played scenarios (`probe_step11.py`) and revert proof (`revert_step11.py`), step 2's hands unit tests (`test_hands.py`), mutant proof (`revert_step2.py`) and in-process harness (`hands_harness.py`: the same brain on a throwaway emulator, its recorder, and `truth`, the second-path read of a saved state), step 2.1's press-behaviour probe (`probe_presses.py`: every A, START, B and SELECT press of a skill checked against the game in forks of its frame) and the evidence's code line (`provenance.py`: HEAD and a digest of the working tree), a state inspector, the four fixture builders (`make_trainer_fixture.py`, `make_defeat_text_fixture.py`, `make_mart_fixture.py`, `make_clock_fixture.py`: each PLAYS a save to the state it needs and prints what it did; `fixtures/` holds the results, their build printouts and the screens the eyes recorded, `hands_recorded_*.json`), the console-signal helper; step 3's world unit tests (`test_world.py`: a grid model of the overworld), mutant proof (`revert_step3.py`), live proof (`live_step3.py`), seed sweep (`rate_step3.py`), the GAME'S ANSWER to where the player stands (`game_answer.py`: by its behaviour, from a saved state) and fixture builder (`make_step3_fixtures.py`: `house_2f_clockset.ss1`, `route101_south.ss1` and its `route101_south.world.jsonl`, `route101_xp.ss1` and its `route101_xp.world.jsonl`, and since step 3.1 `littleroot_twin.ss1`); `hands_harness.py` also runs the world brains and its `truth` now reads save block 1's `pos`, the game's own step and battle counters and each party Pokemon's PID and total experience (`party_exp`); step 3.1's gate-side screen window as literals (`window.py`) and the ROM's warp table against the exits the eyes see by their look (`exit_looks.py`); its verifier's second round: every read of the real eyes against every map's warp array, with three plants (`warp_reads.py`); step 4's knowledge extractor (`extract_knowledge.py`: the bot's data in, `knowledge/*.json` out, `--check`) and its check against pret/pokeemerald (`verify_knowledge.py`, `--plant` its fault half), the battle unit tests (`test_battle.py`), mutant proof (`revert_step4.py`), live proof (`live_step4.py`), seed sweep (`rate_step4.py`) and fixture builder (`make_step4_fixtures.py`: `geodude_grovyle.ss1`, `learn_r116.ss1`, `faint_r116.ss1`, `rival_r103.ss1`, each PLAYED by the AI's own battle brain, and `recoil_r102.look.json`, the AI's own look in a real battle); `hands_harness.py battle` and its `truth` now also read each party Pokemon's moves and OT id, the player's id, `gBattleOutcome`, the trainers' defeated flags and the PC boxes; the step-4 verifier's second round: `make_step32_fixtures.py` (`house_2f_bumps.world.jsonl`, `littleroot_closed.world.jsonl`: the AI's own memories with ONE thing planted, test side, for the live arms FORGET and REOPEN); step 4.1: `make_step41_fixtures.py` (`rival_rustboro.ss1`, `heal_r103.ss1`, `switch_joey.ss1`, `run_r116.ss1`: the party order changed by START-menu presses, every walk, purchase and battle before the saved frame the AI's own goto, mart and battle brains or a named test-side press) and the evidence archive's policy (`prune_evidence.py`); step 5: the milestone extractor and its check against pret/pokeemerald (`extract_milestones.py`: `--check`, `--verify`, `--verify --plant` its fault half, `--wild`, `--items` the item balls' flags for the grader, `fixtures/item_flags.json`), the in-process story harness and its second-path recorder (`play_harness.py`), the goal unit tests (`test_goals.py`), mutant proof (`revert_step5.py`), live proof (`live_step5.py`) and seed sweep (`rate_step5.py`) |
| `../sandbox-pokebot/plugins/custom_modes/ai_player_mode.py` | the hook: registers "AI Player", APPENDS the repo root to `sys.path`, and keeps its own before/after record of the framework's listeners (`[AI-HOOK]`); no game logic |

The subpackage is `host/`, not `platform/` (step 0's name): `platform` would shadow the standard
library's module for anything that put `ai_player/` on `sys.path`. The gate now refuses any top-level
module or folder of the package named like a standard-library module.

## The purity contract

1. **No bot code in the play loop, checked statically** (`gates/check_purity.py`, an AST walk that is
   an allowlist all the way down, the standard library included):
   * (a) framework imports only through listed DOORS, per file, and only along the attribute paths
     each door lists (the controller may use `context.emulator.press_button/hold_button/release_button`
     and nothing else; isolation may read and assign `modules.main.get_bot_listeners` and nothing else
     of `modules.main`; the eyes, `host/eyes.py` only, seventeen READ functions (step 2 added `modules.game.get_symbol`, a
     symbol-table lookup; step 3 `modules.game.get_symbol_name`, the reverse lookup by address, to name the battle
     controller's function: the gate's door says why `get_symbol` cannot) and
     `context.emulator.read_bytes/get_frame_count`, `context.rom.is_emerald`, each door documented in
     the gate with what it reads and why it cannot act); standard-library modules only from a list, each used ONLY as
     `module.<attribute>` with the attribute on its SURFACE (explicit for `sys`, `os`, `pathlib`,
     `traceback`, `signal` (the session only), `atexit` (the hook only), ...; otherwise a public
     attribute that is not a module, not reflective and not from `operator`/`inspect`/`importlib`/`sys`,
     judged against this Python); imports between AI modules only of names their `__all__` lists and
     defines, from files the gate read; the bot's brain refused as a backstop; no top-level module or
     folder named like a standard-library module;
   * (b) no name that writes memory, loads or resets the emulator, changes the game clock, or advances
     frames; button names only in `host/controller.py`; `match` class-pattern attributes and `getattr`
     constants count;
   * (c) the play loop imports neither the test side nor the launcher side; the launcher side does
     not import the framework; the BRAIN (`mode.py`) does not import the host side;
   * (d) no reflection: `__import__`, `exec`, `eval`, `vars`, `setattr`, `getattr` with a name chosen
     at run time, private attributes of other objects, dunders, import-system / tracing / frame
     attributes, `str.format` with attribute or index fields;
   * (e) the files the import system can load are the files the gate read: source parsed from its
     bytes (coding cookies honored), no bytecode or extension modules, no links, nothing but genuine
     cache files in `__pycache__`, and every cache file CPython would load instead of its source
     proven to hold exactly that source's code;
   * (f) only `runlog.py` and the instrument write files; nothing assigns to, or deletes, an attribute
     or item of anything it imported (a shared library, a framework object, another AI module's
     class); the hook may only `sys.path.append`;
   * (g) each host module's `__all__` is pinned in the gate, the instrument's bytes are pinned by
     sha256 (`--instrument-digest`, after a review), its run-time bot-code list must cover every
     module the backstop refuses, only the lifecycle may name its finalizers and exit watchdog, and
     only the session its isolation check (`watch_guard`). `threading` is on three narrow surfaces:
     the instrument (`local`, `Timer`, `current_thread`, `main_thread`, and `RLock`, `get_ident` for
     the frame fence), the session (`Thread`, the
     interrupt watch) and the lifecycle (`Lock`, `get_ident`, single-entry `finish`); only the
     instrument may read `context.frame`.
   The instrument (`host/attribution.py`) is exempt from (b), (d) and (f) only, because it has to
   wrap those very functions; that is why its bytes are pinned.
2. **No framework listener plays for the AI.** On entry the session removes every listener it does
   not own (it owns one: its `GuardListener`) and restores the framework's exact list on exit. This
   happens in the hook's constructor, before the framework's first listener pass. While the AI runs,
   `modules.main.get_bot_listeners` (what `main.py` calls to REBUILD its listeners after a reset or a
   state load from an earlier frame) returns the AI's own list, so no framework listener is even
   built, not for one frame. Before every real frame the instrument checks the guard is in the live
   list; if it is not, the run ends `reason=isolation-lost code=6` before that frame runs: a starved
   AI is a recorded BREACH, never a silent one. The hook independently prints the framework's list
   before the AI starts and at process exit (`[AI-HOOK] ... same_list_object=True members_unchanged=True`).
3. **Measured in every run, at the doors, at the sinks, and in the bot's own code.** The doors count
   every call to the framework's input, write (incl. the game clock's `core.rtc` methods), load and
   frame functions by origin; a foreign press also records the chain of bot functions that made it.
   The sinks catch what no door saw: keys latched with no counted press, or `_prev_pressed_inputs`
   changed between frames (`unattributed_inputs`); WRAM/IWRAM, or the game clock's native setting,
   changed between frames (`unattributed_state_changes`); frames outside the main loop
   (`extra_frames`); a removed wrapper, a new core callback, a rebound name in a sealed host module,
   a look-ahead (`peek_frame`) still open when a real frame runs, or a main-loop frame that ran without
   a sink audit (`instrument_tampered`); a real frame without the AI's guard (`isolation_lost`). A frame
   the main loop runs is ALWAYS audited, whatever look-ahead is open (a verifier held one open on the
   main thread and switched the whole audit off), and `context.frame` (one per main-loop pass) must
   advance by exactly one between audited frames: an independent count of the frames the audit must
   have seen. A `sys.monitoring`
   hook counts every function of the bot's decision code that starts while AI code is on the stack
   (`ai_bot_calls`): bot code that only COMPUTES (the pathfinder) leaves nothing at the doors or sinks.
4. **The verdict is a file, not a line.** At the end, the lifecycle's `finish` (and only it: the
   instrument refuses any other caller and counts it as tampering) has the instrument write
   `<run_dir>/purity.json` from its own counters: verdict, counters, origins, exit reason and code,
   the isolation descriptions, the package that ran. The counts live in a CLOSURE no attribute leads
   to and only grow; the instrument's REGISTRY (a module attribute anyone can name) and each counter
   store answer only code of the instrument's own file, and count every other caller (a positive count
   added through the registry turned an UNVERIFIED run CLEAN before round 3); the instrument's objects
   hold nothing, refuse attribute writes from outside its
   file and count each attempt; its classes are sealed; the host modules are sealed (rebinding a module
   attribute is refused and counted, and a write that goes around that, `vars(module)[...]`, is caught
   by a per-frame fingerprint). The objects that decide how a run ENDS, the lifecycle, the session, the
   listener isolation and the guard listener, are `Guarded` (`attribution.py`): slotted, sealed, and
   writable only from the file that defines their class, so `lifecycle._verdict_path = None`,
   `session.frame_cap = ...` or `guard._on_frame = ...` from AI code are refused and counted. The
   `run_frame` wrapper stays on as a tripwire: a real frame after the
   verdict rewrites the file as BREACH (`ran_after_finish`) and ends the process. The printed
   `[AI-PURITY] ... verdict=CLEAN|BREACH|UNVERIFIED` line is for people; any code can print one.
5. **Never parks.** Every ending is `[AI-EXIT] reason=... code=N`, a verdict file and the process
   exiting: 0 clean give-up; 2 crash (or a stray `SystemExit` from the brain); 3 parked/abandoned/
   restarted by the framework; 4 frame budget (a starved AI); 5 the brain returned without giving up;
   6 purity breach or unverified (also `isolation-lost` and `ran-after-finish`); 9 refused to start
   (the framework's debug mode, which parks a failing mode in `debug_stepping_mode`, or the HTTP server
   on); 124 wall clock; 130 interrupted (Ctrl+C / Ctrl+Break only set a flag; the guard ends the run
   with a verdict on the next frame, `reason=interrupted`; if no frame reaches the guard within 10 s,
   because the brain or anything else on the main thread is stuck, the session's INTERRUPT WATCH thread
   ends the run itself, `reason=interrupted-unresponsive`, with a verdict, and its line says what it
   MEASURED: `no frame ran at all since the watch saw the signal`, or `the main thread is NOT stuck: K
   frames ran ...`). `finish` is single-entry:
   the first thread to reach it writes the verdict and ends the process; a second thread waits for
   that. And while one thread finishes, no other thread runs a frame (the instrument's FRAME FENCE):
   the finish waits, bounded, for a frame already in flight, and a frame started on any other thread
   (a main thread that woke up late from a long call) waits for the process to end instead of running
   (`[AI-LIFECYCLE] ... waits for the process to end instead of running`); the verdict file records
   which thread finished (`finish`). After `finish`, an EXIT WATCHDOG (a daemon timer) ends the process with `os._exit` if it is
   still alive 20 s later (a non-daemon framework thread, the HTTP server's, would otherwise hold the
   interpreter open for ever), or AT ONCE when `finish` ran off the main thread, where `sys.exit` ends
   only that thread. The launcher adds 7 (the gate refused the package) and 8 (exit 0 without a CLEAN
   verdict file).

```
py -3.12 ai_player/gates/check_purity.py          # static gate (exit 0 = PASS)
py -3.12 ai_player/gates/test_check_purity.py     # its fault tests (both verifiers' probes, and the step-0.1 rows)
py -3.12 ai_player/gates/test_host.py             # unit proofs: findings 3, 4, 6, 8 (both threads), the guarded objects, the registry, the frame fence; each with its mutant
py -3.12 ai_player/gates/live_step0.py            # live proof, 63 arms (27 of step 0, 36 of step 0.1 incl. 16 mutants), ~15 min
py -3.12 ai_player/gates/test_eyes.py             # step 1 + 1.1 unit proofs (56 tests, each rule with its fault half), ~1 s
py -3.12 ai_player/gates/revert_step11.py         # step 1.1: each fix REVERTED in a copy of the package fails its predicted test (14 reverts + a control; R5c since step 2.1), ~1 min
py -3.12 ai_player/gates/live_step1.py            # step 1 + 1.1 live proof, 21 arms (the eyes against ground truth, XW: the waits fix reverted, XG: each truth check's fault half; WARP, SW, BS, BLT, BLW: step 1.1's scenarios PLAYED, with revert copies; WARPY (step 2.1): a warp differing in y only), ~25 min
py -3.12 ai_player/gates/probe_step11.py SCENARIO # one step-1.1 scenario (warp, warp_y, sign, start, trainer, catch, replay) in a throwaway emulator
py -3.12 ai_player/gates/make_defeat_text_fixture.py   # rebuilds E10's fixture by PLAYING E5's battle (then re-pin its md5)
py -3.12 ai_player/gates/test_hands.py            # step 2 + 2.1 unit proofs (56 tests, on screens the eyes recorded; each rule with its fault half), ~1 s
py -3.12 ai_player/gates/revert_step2.py          # step 2 + 2.1: each check of the REAL hands code broken in a copy (44 mutants + a control): 39 caught, 5 redundant alone (with the reason), ~4 min
py -3.12 ai_player/gates/live_step2.py            # step 2 + 2.1 live proof, 17 arms (INTRO, NURSE, MART, CLOCK; the fault arms XU, XBN, XBC; step 2.1: WBI, WBN, WBM, WBC every A, START, B and SELECT press against the game, WBX its control, XTW, XFD its faults, XSTALL / XSTALLR the stall detector and its revert, RATE 20 seeds per skill), seed 3, ~40 min
py -3.12 ai_player/gates/live_step2.py --seed 9 --arms INTRO,XU,XBN,NURSE,MART,CLOCK,XBC,WBI,WBN,WBM,WBC,WBX,XTW,XFD,XSTALL,XSTALLR --evidence-tag step2-seed9-at-step3
                                                  # the REPLICATION, seed 9, on the step-3 tree (README "Which seed-9 files are which")
py -3.12 ai_player/gates/probe_presses.py BRAIN --fresh | --state PATH [--seed N] [--fault ...] [--clock HH:MM]
                                                  # step 2.1: one skill in-process, every A press checked against the game in forks of its frame,
                                                  # and (the review's item 4) every START, B and SELECT press: was it TAKEN?
py -3.12 ai_player/gates/provenance.py            # step 2.1: the CODE line of the evidence for THIS tree (compare its working-tree digest with an evidence file's)
py -3.12 ai_player/gates/hands_harness.py BRAIN --fresh | --state PATH [--seed N] [--fault ungated_a|blind_count] [--record PATH]
                                                  # one hands brain in-process (development; not a purity proof); `truth STATE` reads a state
py -3.12 ai_player/gates/make_mart_fixture.py     # rebuilds the MART fixture by walking rustboro.ss1 into the mart (then re-pin its md5)
py -3.12 ai_player/gates/make_clock_fixture.py    # rebuilds the CLOCK fixture: the AI's own intro (seed 7), then walked to the clock (re-pin)
py -3.12 ai_player/gates/test_world.py            # step 3 + 3.1 + 3.2 + 4.1 unit proofs (132 tests since step 4.1 round 2, against a grid model of the overworld, and the graders' rules; each with its fault half), ~2 min
py -3.12 ai_player/gates/revert_step3.py [W1,W2] [--workers N]
                                                  # step 3 + 3.1 + 3.2 + 4.1: each rule of the REAL navigator / memory / explorer / roam / flee / probe / grader broken in a copy
                                                  # (94 mutants + a control since step 4.1 round 2; W62-W75 step 3.2's, W93-W98 round 2's): 93 caught, 1 redundant alone (the reason), ~19 min with --workers 12
py -3.12 ai_player/gates/live_step3.py            # step 3 + 3.1 + 3.2 live proof, 34 arms (HOUSE, TOWN, ROUTE, ROAM, CROP, STUCK, BUMP, BUMPR, TRN, XP, XPR, SCENE,
                                                  # SCENER, EXITS; the step-3.1 verifier's round: SCENEX, SCENEXR, HOUSER, TOWNR, ROUTER, EDGER, and the seed-9
                                                  # replications TOWN9, ROUTE9; its second round: SCENENR, WARPREAD, BUMPSR, TOWN9R, ROUTE9R, HOUSE9, BUMP8,
                                                  # BUMPSR8, SCENEX9, F2AB, CLOCKS; step 3.2: SCENEXL; the step-4 verifier's second round: SCENEXC,
                                                  # FORGET, FORGETR, REOPEN, REOPENR; step 4.1 round 2: TOWNT, TOWNTR: 41 arms), seed 3, ~16 min; every number in its PREDICTED table
                                                  # machine-checked; its in-process arms pin the cartridge's clock (GAME_CLOCK), its launcher arms read the host's
py -3.12 ai_player/gates/warp_reads.py            # step 3.1 (the verifier's second round): the REAL eyes on 7 starts, every memory read recorded, against
                                                  # every map's warp array; and three plants in copies (an attribute, a getattr, a raw read), each caught (arm WARPREAD)
py -3.12 ai_player/gates/rate_step3.py [--plans HOUSE,TOWN,...] [--seeds 10] [--workers 4]
                                                  # step 3 + 3.1: the SEED SWEEP, 10 plans x 10 seeds in-process, each graded by its second-path truth;
                                                  # also the targets each seed chose, CROP-SEP (TOWN vs CROP seed by seed), the reversal bounds, the
                                                  # REVERTS (finding 2's rules and the scene's count per tile reverted in a copy: the A/B), the scenes,
                                                  # ROUTE's flee, the seed-3 replay and the roaming metrics; since step 3.2 the LAPS and the walks against
                                                  # the shortest known ways per run, the targets chosen on the move, and the LAPS and WHIM reverts;
                                                  # since the step-4 verifier's second round the CHURN per plan and its revert A/B, LAP RINGS, and
                                                  # SCENE-EXPLORE's reversals and journeys bounded; ~11 min with --workers 10. --first-seed 201 plays
                                                  # HELD-OUT seeds (no development run played them) against the same bounds: a replication, where
                                                  # seeds 1-10 replay the development sweeps (rate_step4.py takes --first-seed too). Since step 4.1
                                                  # round 2 seeds 101-110 are DEVELOPMENT seeds too (the bounds' bootstrap drew from 1-10 and 101-110)
py -3.12 ai_player/gates/game_answer.py STATE GROUP NUMBER X Y [--after-warp GROUP NUMBER X Y | --after-connection GROUP NUMBER X Y DIRECTION]
                                                  # step 3: where the GAME says the player stands, by its behaviour (hold a direction; its own step
                                                  # counter and loaded map against the ROM layout's prediction at the claimed tile); with no
                                                  # walking line, or a trial the game did not step at all: can the player move at all (LOCKED), and
                                                  # where the ROM says the last warp (or, since step 3.1's second round, map edge) left it
py -3.12 ai_player/gates/make_step3_fixtures.py [--only house|route|xp|twin]   # rebuilds house_2f_clockset.ss1 (the AI's clock skill),
                                                  # route101_south.ss1 + its world.jsonl (the AI's own TOWN walk), route101_xp.ss1 + its
                                                  # world.jsonl (the AI's errands, then test-side presses to a won battle), littleroot_twin.ss1 (the
                                                  # AI's own HOUSE walk: the fixture of SCENE, SCENEX and SCENE-EXPLORE); then re-pin in live_step3.py
py -3.12 ai_player/gates/provenance.py --check-evidence
                                                  # every evidence file at the top of ai_player/evidence/ names THIS tree's digest (earlier trees'
                                                  # CITED files are kept in evidence/archive/<digest>/, the rest indexed in evidence/archive/INDEX.md)
py -3.12 ai_player/gates/make_step41_fixtures.py [--only rival|heal|switch|run|sing] [--seeds 1-20]
                                                  # step 4.1: rebuilds rival_rustboro.ss1, heal_r103.ss1, switch_joey.ss1, run_r116.ss1 by playing
                                                  # (then re-pin their md5s in live_step4.py); round 2: sing_r117.ss1 (a Skitty with SING put first,
                                                  # the AI's explore brain from Mauville to Route 117, a wild Oddish not caught yet)
py -3.12 ai_player/gates/prune_evidence.py [--retire DIGEST] [--apply] | --reindex
                                                  # step 4.1: the archive policy (a dry run without --apply): keep the cited files, index and
                                                  # delete the rest (each tracked and unchanged, so git keeps it); --retire the last tree's top level
```

## Fault and control switches

Read inside the AI's own code, never set on the happy path:

| variable | effect | the arms that use it |
|---|---|---|
| `AI_PLAYER_FAULT_KEEP_LISTENERS=1` | skip listener removal | B (wild battle), BT (trainer battle), W (cheats plugin on) |
| `AI_PLAYER_FAULT_RAISE=1` | the brain raises after 30 steps | C |
| `AI_PLAYER_FAULT_MANUAL=1` | a listener raises; `main.py` switches to Manual | M |
| `AI_PLAYER_FAULT_HANG=1` | the brain blocks the main thread (bounded at 300 s) | T2 (hard wall clock) |
| `AI_PLAYER_FAULT_NO_REBIND=1` | isolation does not take the framework's rebuild door | RLX, M1 |
| `AI_PLAYER_FAULT_SKIP_RESTORE=1` | isolation does not give the framework its list back | DX |
| `AI_PLAYER_CONTROL_TAP=1` | CONTROL: the placeholder taps B every 60 steps | P |
| `AI_PLAYER_FAULT_NO_CROP=1` | the eyes do not crop to the screen (step 1: objects and signs; since step 3 also EVERY tile of the live grid, the map and its margin) | E2X (live_step1), CROP (live_step3) |
| (a COPY) | step 3: `WorldMemory.learn_bump` remembers nothing | BUMPR (live_step3, in-process `hands_harness.py`) |
| (a COPY) | step 3.1: the scene rules off (per target and per tile) / the count per tile off | SCENER / SCENEXR (live_step3); the sweep's SCENE-TILE revert |
| (a COPY) | step 3.1, the verifier's round: finding 2's two rules off (`live_step3.STALE_MUTATIONS`) | HOUSER, TOWNR, ROUTER (live_step3); the sweep's FINDING-2 revert |
| (a COPY) | step 3.1, the verifier's round: a map's ends from negative coordinates again (`live_step3.EDGE_MUTATION`) | EDGER (live_step3) |
| (a COPY) | step 3.1, the verifier's second round: a scene not known by its words (`SCENEWORDS_MUTATION`) / new words not progress (`NEWS_MUTATION`) | SCENEXR / SCENENR (live_step3); the sweep's SCENE-WORDS / SCENE-NEWS reverts |
| (a COPY) | step 3.1, the verifier's second round: one bump walls a tile from every side again (`BUMPSIDE_MUTATION`) | BUMPSR, BUMPSR8 (live_step3) |
| (a COPY) | step 3.1, the verifier's second round: a warp-table read planted in `host/eyes.py` `_map_facts` (`warp_reads.PLANTS`: an attribute, a getattr, a raw read) | WARPREAD (live_step3, `gates/warp_reads.py`) |
| (a COPY) | step 3.2: the turn-back cost charged on every replan, no plan followed (the step-3.1 rule, `live_step3.LAPS_MUTATION`) | SCENEXL (live_step3); the sweep's LAPS revert |
| (a COPY) | step 3.2: a target chosen on the move picked on a whim again (`live_step3.WHIM_MUTATION`) | the sweep's WHIM revert |
| `AI_PLAYER_FAULT_IGNORE_TYPES=1` | step 4: the battle decider values every type matchup as neutral and gives no STAB | TYPEX (live_step4); the sweep's TYPE-FAULT; `test_battle.py` TypeTests |
| `AI_PLAYER_FAULT_IGNORE_RECOIL=1` | step 4: the battle decider drops the recoil penalty | the sweep's RECOIL-FAULT; `test_battle.py` RecoilTests, RecordedRecoilTests |
| (a COPY) | step 4: one rule of the decider, the skill, the eyes' new waits or the type chart broken (`revert_step4.MUTANTS` B1-B30) | `revert_step4.py` (`test_battle.py` from the copy) |
| `AI_PLAYER_FAULT_OVERKILL=1` | step 4.1: every move valued uncapped (step 4: a stronger move wins even when a weaker one finishes the foe) | OVERKILLX (live_step4); the sweep's OVERKILL-FAULT, and RECOIL / RECOIL-FAULT run under it; `test_battle.py` RecordedRecoilTests, OverkillTests |
| `AI_PLAYER_FAULT_SHIFT_FAINTED=1` | step 4.1: the shift question answered about the foe on the field (the fainted one) and the party menu ranked by level (step 4) | SHIFTX (live_step4); the sweep's SHIFT-FAULT; `test_battle.py` ShiftTests, SkillTests |
| `AI_PLAYER_FAULT_FORGET_UNUSABLE=1` | step 4.1: a move the game refused not remembered for the turn (step 4: chosen again until the 150-menu bound) | REFUSEDX (live_step4, with `_IGNORE_PP`); the sweep's REFUSED-FAULT; `test_battle.py` UnusableTests, SkillTests |
| `AI_PLAYER_FAULT_IGNORE_PP=1` | step 4.1 round 2: the decider blind to the PP its moves have left, so it chooses moves with none and the GAME refuses them through the code that refuses a Disabled move (finding 2's refusal, played live) | REFUSED, REFUSEDX (live_step4); the sweep's REFUSED, REFUSED-FAULT |
| `AI_PLAYER_FAULT_NO_CATCH_STATUS=1` | step 4.1 round 2: no sleep or paralysis move to help a catch (step 4) | CATCHSX (live_step4); the sweep's SING-FAULT; `test_battle.py` OpenerTests |
| (a COPY) | step 4.1 round 2: THE STEP-4 EXPLORER'S WALK (`live_step3.WALK_MUTATIONS`: the people pull on unseen tiles near people, a person on the plan breaking it at once, a detour two aside and back); step 4.1's journey charge and its `JOURNEY_MUTATION` are gone | TOWNTR (live_step3); the sweep's WALK revert (`rate_step3.py`) |
| `AI_PLAYER_FAULT_NO_HINTS=1` | step 5: the goal manager never uses what the game SAID (no "go to ROUTE 103" from the rival's mom, no "PETALBURG GYM" from the TV): it explores and asks for nothing | the sweep's NOHINTS (`rate_step5.py`); `test_goals.py` HintTests |
| `AI_PLAYER_FAULT_NO_TRAINING=1` | step 5: no training before a known fight (the rival goes un-prepared) | the sweep's NOTRAIN (`rate_step5.py`); `test_goals.py` ErrandTests |
| (a COPY) | step 5: one rule of the goal manager, the story reader, the personality, the story skills, the route rules, the milestone marks, the play loop or the roam's report broken (`revert_step5.MUTANTS` G1-G52) | `revert_step5.py` (`test_goals.py` from the copy) |
| (a COPY) | step 5 round 2: MAX_LOSSES 1 (`CAP1`), alone and with the play loop's loss count removed (G46) | the sweep's phase 2, STOP and STOPDEAD (`rate_step5.py`) |
| `AI_PLAYER_FAULT_NO_ERRANDS=1` | step 5.1: the BEELINE control: no look-around, no detour, no stop on a map whose look-around is due, no chat, no catching roam | the sweep's ERRANDS_OFF (`rate_step5.py`); `test_goals.py` ExploreTests |
| (a COPY) | step 5.1: the starter bag watched for the bag alone (G53: the verifier's stall (a)); `talk` waiting out a scene's text with no settling and no second look (G55, G56, G57, G86: stall (b)) | the sweep's STALL1, STALL2 (`rate_step5.py`) |
| (a COPY) | step 5.1: `STORY_PATIENCE` 40,000 (`PATIENCE_SMALL`), alone and with the step-5 rule back (G67: only a milestone resets it) | the sweep's PATIENCE, PATIENCE_OLD (`rate_step5.py`, the Trainer's seeds) |
| (a COPY) | step 5.1, the verifier's round: the battle skill waits 600 frames at the action menu before it acts (`STALL3`: a battle's wait for a press, which the second path did not read until this round) | the sweep's STALL3 (`rate_step5.py`, the Story's seeds) |
| (a COPY) | step 5.1, the verifier's round: once its battler is L7, the decider uses its status move (slot 1) every turn of a wild battle and never runs (`LOSE3`): the play loop's real `MAX_LOSSES` (3) must end the run | the sweep's LOSE3 (`rate_step5.py`, the Catcher's seeds) |
| `AI_PLAYER_FAULT_UNGATED_A=1` | the dialogue driver presses A on its cadence with no wait gate and never stops for a menu (step 2) | XU (live_step2) |
| `AI_PLAYER_FAULT_BLIND_COUNT=1` | the menu driver moves every cursor by a count from the top, without reading it (step 2); since step 2.1 it still waits for a menu to take input before its A (it is blind to the CURSOR only: an A dropped in the gender menu's sprite slide now ends the intro, the review's item 6) | XBN, XBC (live_step2) |
| (a COPY of the package, not a switch) | step 2.1: the eyes' TASK_WAITS list a timer task (`Task_NewGameBirchSpeech_WaitToShowBirch`) as a wait | XTW (live_step2): the press-behaviour probe must flag every A pressed on it |
| (a COPY) | step 2.1, the review's item 4: the eyes' fade rule reverted (`eyes/screens.py` read_ui: a fading movie "takes input") | XFD (live_step2): the probe must flag the START the game drops in a fade |
| (a COPY) | step 2.1, the review's item 1: `Task_HandleYesNoInput` out of UI_TASKS, so the nurse's yes/no is a menu the eyes do not know; XSTALLR also takes the stall detector out | XSTALL, XSTALLR (live_step2, in-process `hands_harness.py`) |

A forbidden action cannot be a switch in the real package (the static gate would rightly fail it), so
the PLANT arms copy the package to a temporary folder, add a `_plant.py` that does one forbidden thing
from inside the AI's play loop (`host/session.py` `_steps` calls it once per brain step), and run that
copy through the real launcher (with `--allow-ungated`) and hook. Each must fail the static gate AND be
caught live: `XP`, `XH` (inputs through no door), `XM`, `XN` (memory through no door), `XL`, `XS`
(loads), `XF` (an extra frame), `XT` (a callback inside the frame), `XB` (the bot's pathfinder run from
the brain), `XG` (a press found by a frame walk), `XK` (a breach, then twenty attempts to hide it, on
the counters, the instrument, the lifecycle, the session, the isolation and the guard listener),
`XC`, `XQ` (the game clock, through its door and natively), `XV` (`_prev_pressed_inputs`), `XW` (a
`peek_frame` held open on the main thread, then A through no door: the verifier's V5), `XWT` (a
look-ahead held open by ANOTHER thread while the main thread runs an extra frame), `RL` (a rewind
by the AI that makes `main.py` rebuild its listeners) and `RLF` (the same rewind by FOREIGN code that
the main loop runs from its `work_queue`). `XE`, `XY`, `XZ` attack the evidence instead (a fake
lifecycle printing a forged CLEAN verdict, swapped in with `object.__setattr__` because the plain
assignment is refused now; a stray `SystemExit`; catching the lifecycle's own exit), and `XR` proves
the launcher refuses an ungated package. `XO` is the do-nothing control. `IG` and `IR` (round 3) run a
TEST-SIDE plant that only observes and slows the console (every stdout line takes 20 ms while the run
is being finished, which widens the finish's window so the race is met every run; an observer thread
reads the emulator's own frame counter from the moment the finish begins): in `IG` a FAULT mutation
makes the guard ignore Ctrl+Break, so frames keep running while the watch finishes (the verifier's
VIB); in `IR` the brain blocks the main thread until the finish has begun and then returns, so the
main loop's next step is a frame (the real-code race). `M9` / `M9r` revert the frame fence on each,
and `M9w` the watch's measured wording. `H`, `H2` (HTTP), `IB`, `IC`
(Ctrl+Break, Ctrl+C in a console of the framework's own), `IH` (Ctrl+Break to a HUNG brain: the
verifier's V4), `G` (the framework in debug mode: a test-side `-c` wrapper re-sets `context.debug`
right before the main loop, which headless mode forces off) and `BT`, `BT2` (a trainer battle, from
`gates/fixtures/trainer_battle_r116.ss1`, built by `gates/make_trainer_fixture.py`) are step 0.1's.
The MUTANT arms `M1`, `M1r`, `M3`, `M5r`, `M5p`, `M5h`, `M5w`, `M6`, `M7`, `M7h`, `M7x`, `M8`, `M8t`, `M9`, `M9w`, `M9r` each
revert one fix in a temporary copy and pass only when the arm that guards that fix FAILS on it; `M8`
also shows the frame-continuity check still catching V5, and `M8c` (both layers reverted) reproduces
V5 as CLEAN, so each layer is shown to be load-bearing.

Evidence of the live proof: `ai_player/evidence/<date>-step01-<ARM>.txt` (step 0's own runs:
`<date>-step0-<ARM>.txt`). Since the step-3.1 verifier's second round the folder's top level holds the evidence of the
CURRENT tree only (`provenance.py --check-evidence`): `live_step0.py --arms A,A2,B,C`'s four files; the full step-0 and
step-0.1 runs of 2026-10-07 (no digest line: they predate `provenance.py`) were in `evidence/archive/no-digest/`.

‼ SINCE STEP 4.1 (the archive policy, `evidence/archive/README.md`): an earlier tree's evidence file stays in
`evidence/archive/<digest>/` only when a document or a commit message names it; this README's references by PATTERN
(`evidence/archive/no-digest/2026-10-07-step2-<ARM>.txt`, "archived in `evidence/archive/<digest>/`") now lead to
`evidence/archive/INDEX.md`, where each such file has one line with the `git show <commit>:<path>` that prints it (git
keeps every one: the tool deletes a file only when git tracks it unchanged).

## The story, human-like (build step 5.1)

‼ Sections A-F and "The proof of the first round" below are the FIRST round's (tree `c450adc2865848e4`, its evidence now in
`evidence/archive/c450adc2865848e4/`). "Step 5.1, the verifier's round" after them supersedes their metrics and proof:
read it for what holds now.

Step 5.1 answers the step-5 verifier's FAILURE and the step-5 adversarial review's six findings (both verbatim in the round's
input), on ONE tree: working-tree digest `c450adc2865848e4` (the first round's `2026-10-14-step51-*.txt` evidence files name it). USER
RULING 37 Q6 ("HUMAN pacing, but always goal-directed and never idle ... detours are allowed") and RULING 32 ("never a
speedrun") are what each part serves; RULING 35 holds (the AI's own code plays; the purity gate unchanged, `check_purity`
PASS; no host-side door or read was added: every change is in the AI's brain, hands, skills, knowledge and gates, and the
second path's framework reads live in the harness, `gates/play_harness.py`, never in the AI).

### A. Pacing: never standing in front of a screen that waits for a press

* **(a) The starter's yes/no** (the verifier: A on a ball at f34499, YES at f35142 in arm CH1M; 20 of 40 sweep runs). After
  the A the bag shows BUSY while the ball opens, so the scene handed it back to the play brain's menu, whose
  `wait_for_ui("choose_starter")` watched for the bag ALONE 600 frames while the yes/no that followed waited. Fix:
  `skills/story.py` `bag_or_its_question` returns as soon as anything on the bag TAKES INPUT (the bag again, or its
  question) or the bag is gone; `choose_starter` then hands the question back at once. Live now: A to YES 39 / 48 / 61 frames
  (CH1T, CH1C, CH1M; step 5's CH1M 643).
* **(b) A goal chosen on the frame a scene's map change landed** (the verifier: 'goal chat' 2 frames after PROF. BIRCH's
  scene put the player in his lab; `talk` then waited 1,200 frames "until the player is free" while his text waited for
  A; 13 of 40 sweep runs). Three layers, each with its own mutant: the play loop lets the screen stay free `SETTLE_FREE`
  (30) frames after a map change before it chooses a goal (`mode.py`; G56); after the decision's thinking pause it looks
  again and, a scene having begun, plays it first (the goal is recorded "dropped", not failed; G57); `talk(give_way=True)`
  (`hands/dialogue.py`, used by the story skills only; the step-2 default is unchanged) returns at once when what is on
  screen waits for a press, and `talk_to` plays that scene (G54, G55, G86). Live now: the lab's arrival to its first page
  read 156 / 158 / 151 frames (step 5's CH1M 1,295).
* **(c) The PROPERTY, not a reason label.** `hands/waiting.py` `WaitWatch` (installed by the play brain, told every look)
  measures every stretch in which the screen WAITED FOR A PRESS (`awaits_press`: a text waiting for A/B, a menu taking
  input) and no press came, whatever busy reason the pad gave meanwhile (it records them all). Its stretches of 60 frames or
  more are written to the action log (`decision` "await"), the longest to the end record. In the sweep a SECOND PATH reads
  the game every 10 frames by the framework's own code (`gates/play_harness.py` `WaitRecorder`: the tasks that poll a
  button, and `modules.tasks.is_waiting_for_input` on the overworld) beside the presses. **The bound, pre-registered:
  `AWAIT_MAX` = 300 frames**: the pad's longest deliberate pause before a press is its reading cap (`Pacing.read_max`, 150
  frames); MEASURED, the longest stretch in every development run of the real code was 150 by both paths; 300 is twice the
  cap, far under the stalls (600-644 and 1,141-1,210 frames). Live (`live_step5.py`) by the AI's record; the sweep
  (`rate_step5.py`) by both, and the two paths must AGREE run by run.
* **The sweep for other stalls of this shape**: 99 development runs (step51dev1-dev7 and their ERRANDS_OFF controls, 9 CH1
  seeds each, on the code of their day), the graded sweep's 40 runs of the real code (CH1, NOTRAIN, NOHINTS, ERRANDS_OFF)
  and the five live arms: the longest is 150 frames everywhere by the AI's record, and 150 by the game's in the graded sweep. One second-path reading was a false alarm and is
  documented in `play_harness.waits_now`: during a wild battle's opening the framework's read of text printer 0 said
  "waiting" for 510 frames before "Wild WURMPLE appeared!" was printed (a printer state left from before the battle); the
  second path reads text waits on the overworld only (the battle skill's waits stay in the AI's record).

### B. Explore, don't beeline (review #1, RULINGS 32 and 37)

* **LOOK AROUND** (`brain/goals.py` `may_look_around`, goal kind `explore`): on an OUTDOOR map whose draw is due, one
  seeded draw against the personality's `look_around` (Catcher 0.8, Trainer 0.7, Story 0.55: the Story player too, less),
  then `look_frames` (4,200 / 3,600 / 3,000) of looking round that map, keeping to it; never in danger, never the intro,
  and not where the story's own next thing is told and HERE (measured in development: it looked round ROUTE 101 while PROF.
  BIRCH cried "Help! In my BAG!", and he cried "Don't leave me like this!"; G85). A walk (`go`, `look_around`) that arrives on
  an outdoor map whose draw is due STOPS there so the next decision may make it (`NEW_MAP_STOP`; G66, G87: step51dev2-4
  stopped only on maps never visited and the draw was rarely due). The order is now HEAL, SHOP, ITEM, EXPLORE, TRAIN, CATCH,
  CHAT, STORY (an item ball before training: a training roam stops for one, so training first ended every session at once).
* **DETOURS** (goal kind `detour`, `GoalRunner._detour`): a `go` with a known map across an outdoor map, one draw a map and
  milestone against `detour` (0.5 / 0.45 / 0.35): one place OFF the way (a frontier, grass, someone not met: never the way
  on, back, or into a building), within `detour_frames` (1,500 / 1,500 / 1,200).
* **Item curiosity**: an item ball in view is picked up before the party too (G64), and one it SAW earlier on this map is
  walked back to (`_remembered_ball`, `_back_to_ball`; G65). **Chatting** now and then is step 5's errand (Trainer most).
* **The beeline control** `AI_PLAYER_FAULT_NO_ERRANDS` / `--fault no_errands`: none of the above, no chat, no catching roam.
* **Metrics, pre-registered** (`rate_step5.py` BOUNDS, from the development sweeps; the README's numbers are the graded
  sweep's, seeds 401-410): the INTENT MIX (`intent_mix`: the share of the goals' frames on errands, in EVERY run >= 0.30:
  0.46-0.62; on CURIOSITY, `explore`, `detour`, `chat`, `catch`, `pick_up`, each personality's mean >= 0.06: Catcher 0.108,
  Trainer 0.114, Story 0.117); SEED DIVERGENCE (`divergence`: every pair of runs of one personality, goal sequences 0.515
  and paths 0.438, bound >= 0.30 each, no identical pair); the beeline control MOVES them (curiosity drops by 0.080, the mean
  of the paired seeds, bound >= 0.04; goal-sequence divergence 0.446, bound below CH1's; paths 0.455, reported); NO SPEEDRUN (the frames
  to the POKéDEX outside the NEEDS, training, healing, finding a centre and shopping, which the control keeps too and whose
  length is the battles' dice: CH1 over the control pooled 1.061, bound >= 1.0, every run within its 300,000 budget).
  ‼ **The literal "frames to the POKéDEX above the beeline" is REPORTED, not bounded**: in development it measured 0.987 and
  1.006 (the errands' extra time is within the training's run-to-run noise, and looking round a place makes later walks
  shorter); on the graded seeds the total was 1.05. The no-speedrun claim rests on the outside-the-needs ratio.

### C. Patience counts from real progress (review #2)

`mode.py`: `STORY_PATIENCE` now counts from the last REAL PROGRESS (`HandsBrain._progress`): a milestone, battles WON while
training, a level gained, a map never seen before, a catch (the POKéDEX's owned count), an item picked up or bought, a
heal (at most `HEAL_RESETS_MAX` = 3 a milestone, so heal, get hurt, heal again cannot reset it forever). Goals that keep
FAILING make no progress and are still stopped ("stuck: no progress for N frames ..."). Through the real loop
(`PlayLoopTests`): a training stint of 8 sessions, 160,000 frames, each winning a battle, is played to its end and the goals
after it are stopped at the patience (G67 is the step-5 rule back: it stops after 6 sessions); failing goals report no
progress; the heal cap (G68). In the game, the sweep's patience A/B on the Trainer's seeds 402, 405, 408 with
`STORY_PATIENCE` 40,000 in a copy: the real rule reached the POKéDEX in 3 of 3 with training stints of 56,318-70,957 frames
(longer than the patience); the step-5 rule (G67) stopped 3 of 3, each WHILE TRAINING (its last goal a training session).

### D. Person-fair (review #3, #4)

* **Each STEP's own words or a visit** (`Step.told`, `GoalManager.step_known`; `gates/extract_milestones.py` writes them and
  `--verify` finds all 19 in the decomp): upstairs in the rival's house needs the rival's mom's "is upstairs, I think",
  never MOM's "next door" (G69); the `ask` step goes only to a place it has BEEN (G70).
* **The rival's POKé BALL is no scripted step any more** (`ch1_rival_house` steps: go 1F, go 2F): it lies on the floor with an
  item ball's look, and item curiosity walks up to it, which plays the rival's scene (all 10 graded CH1 runs and the 3 live
  arms: "goal pick_up: an item ball on the ground at (5, 4)", (3, 4) in BRENDAN's house, before MILESTONE ch1_rival_house;
  G71 restores the step and is caught).
* **Fight levels only for fights the game NAMES** (`Milestone.fight_named`: the rival, ROXANNE; RULING 33 "train to the
  leader's level"), any other trainer's only as SEEN in a trainer's battle on the milestone's maps (`seen_levels`; G72); the
  target is the STRONGEST level plus the margin, asked of the goal manager (`training_target`; the verifier's min() mutant is
  G73, caught).
* **Shopping by the mart's LIST**: no flag; a list with no POKé BALLS is remembered and that mart tried again only once the
  story moved on (`no_balls`; G12 re-targeted). In chapter 1 each graded CH1 run (10 of 10) and live arm (3 of 3) visited
  the OLDALE MART, read "POTION, ANTIDOTE, PARLYZ HEAL, AWAKENING", left the list (`skills/story.py` `leave_shop`) and bought
  POTIONS (twice a run: before the rival and once the story had moved on, still before the POKéDEX opens the balls' sale).
* **Home healing by experience**: MOM's words ("If anything happens, you can come home.", "I think you should rest a bit.")
  or a heal SEEN after talking to her (`home_heals`; G76, G77), never FLAG_RESCUED_BIRCH. ‼ Found in development (step51dev1,
  3 whiteouts in 9): MOM says "come home" only with the RUNNING SHOES, after the POKéDEX, so before the rival a hurt AI knew
  nowhere to heal and walked on at 1-5 HP. Three fixes: in DANGER with no place known it LOOKS for a POKéMON CENTER
  (`find_center`; G82), a TRAVELLING battle with its Pokemon LOW is run from on any turn whatever the temperament
  (`brain/battle.py` `_run_or_not`; G83), and ANY walk while hurt keeps out of the tall grass (`GoalRunner.pursue`; G84).
  Whiteouts in the graded CH1 seeds: 0 of 10.

### E. Loops (review #5)

A STORY goal that failed `FAIL_LIMIT` times waits the same cooldown as `seek` (12 decisions) and the decision says so and
LOOKS AROUND meanwhile (`_story_goal`, key `aside:<goal>`; G78). The gym's trainers are OPTIONAL (`ch4_gym_trainers`
`"optional": true`): never the current milestone; ROXANNE is proven by her badge alone (G74). ‼ Development also found the
twin's loop: after looking round LITTLEROOT, every walk to the rival's house chose the frontier past the twin, who sent the
player back twice per walk until the patience ran out (3 of 9 runs, step51dev5). The tiles a scene sent the player back
from are now CARRIED from goal to goal within a milestone (`Navigator.carried_scene_walls`, an opt-in attribute the play
brain sets; None for every earlier brain; G88, G89).

### F. The small items

`test_goals.py` asks the goal manager for the training target on ROXANNE's [12, 15] (G73); milestone lines say how a
milestone passed ("passed as a WAYPOINT (it stood on INSIDE_OF_TRUCK; its save proofs do not hold yet)", "passed as
OPTIONAL"; G79); a battle line says "it would like it, but it has no POKé BALL" and the run reason "it has no POKé BALL for
this wild ..." (G80); `run_units.py`'s title and `rate_step5.py`'s seed comment name step 5.1; the play loop, `_bounded` and
the harness's loop are `for` loops over their bounds (`PLAY_PASSES_MAX`, `STILL_PASSES_MAX`); `SmallTests.test_the_step5_
regexes_with_both_cases` prints `ROAM_LINE`, `OUTDOOR` and the whole-word pattern's characters with a positive and a
negative case each, and the grader's goal-after-page check both ways (G81).

### The proof of the first round (tree `c450adc2865848e4`: superseded by the verifier's round below)

Kept as history. These numbers are the first round's tree's; its evidence files were moved to
`evidence/archive/c450adc2865848e4/` when the verifier's round wrote its own (`provenance.keep_earlier`).

| proof | what it shows | result (first round: `evidence/archive/c450adc2865848e4/2026-10-14-step51-*.txt`) |
|---|---|---|
| `live_step5.py` CH1T, CH1C, CH1M | chapter 1 from a REAL New Game through the real launcher, one per starter and personality (seeds 11, 12, 13) | OVERALL PASS, purity CLEAN; `done: ch1_pokedex reached` in 148,032 / 132,547 / 151,408 frames; the game's flags all 1; THE STALL PROPERTY: the longest wait for a press 150 frames in each (211 / 199 / 218 stretches of 60 or more noted); every go goal after its page; intent mix 65 % / 56 % / 55 %; goals include `explore` 2 / 3 / 1, `detour` 0 / 2 / 2, `chat` 3 / 2 / 4, `find_center` 0 / 0 / 2; trained 274 / 239 / 206 steps, 21 / 11 / 14 wild battles WON in the training roams; spins 1 in 719 steps |
| `live_step5.py` CH2 | chapter 2 from CH1C's own end (Catcher, seed 12) | PASS, 143,152 frames: WALLY's tutorial (VAR_PETALBURG_GYM_STATE 2); +4 captures, 4 new PIDs of the player's OT; +2 POKéMON CENTER heals; FLAG_ITEM_ROUTE_102_POTION; 10 POKé BALLS bought |
| `live_step5.py` CH2T | a SECOND, INDEPENDENT chapter 2: from CH1T's own end (Story, seed 11) | PASS, 82,140 frames: WALLY's tutorial; +1 capture; +1 heal; 5 POKé BALLS bought; items 0 (reported). ‼ Its claims were pre-registered from an in-process development run that turned out to be THE SAME TRAJECTORY (the in-process CH1 of Story seed 11 ended at the same 148,032 frames as the live CH1T, and the chapter-2 run from it at the same 82,140): one trajectory, replayed (CLAUDE.md rule 8); it is independent of CH2, not a held-out sample |
| `rate_step5.py` (NEW held-out seeds 401-410, 78 runs + 4 in phase 2) | how often; what each fault costs | VERDICT PASS on every pre-registered check: CH1 POKéDEX 10 of 10, the rival at the first try 10 of 10, whiteouts 0; THE STALL PROPERTY 150 frames by both paths in all 40 runs of the real code; STALL1 fails it in 8 of 10 (617-643 frames), STALL2 in 3 of 10 (1,141-1,210); the paths agree in 80 of 80; every go goal after its page; the intent mix, divergence, beeline A/B and no-speedrun as in B; PATIENCE / PATIENCE_OLD as in C; and step 5's checks unchanged (NOTRAIN +2.1 levels, DEADREST 53 breaches over 64, NOHINTS 0 of 10, STOP and STOPDEAD, losses agree in 78 of 78) |
| `revert_step5.py` | each rule carries weight | 88 of 88 mutants CAUGHT as predicted (G53-G89 new; G7, G12, G13, G30, G31, G32, G41, G49 re-anchored to the 5.1 code). ‼ G86 was first registered REDUNDANT ALONE ("`talk` with give_way covers it"); the mutant proof found the prediction WRONG (with the person off the screen `talk_to` answers "not on screen any more" and never plays the scene) and it is CAUGHT |
| `test_goals.py` | the rules unit by unit | 94 tests OK (35 new: PacingTests, ExploreTests, PersonFairTests, LoopGoalTests, SceneWallTests, SmallTests, PlayLoopTests' progress and pacing) |
| `extract_milestones.py --verify` / `--plant` | every fact against pret/pokeemerald, now the steps' own words too | OVERALL PASS (19 steps' own words in their scripts); the three plants found and nothing else |
| `run_units.py` | the static gate and every unit suite | OVERALL PASS |

### Step 5.1, the verifier's round (2026-10-14)

The step-5.1 verifier found no failure, nine weak proofs and one rule violation (verbatim in the round's input). Each is
answered below. The fixes were developed on seeds 1-9 and 21-29 (the sweeps `step51vdev1` and `step51vdev2`, kept
outside `evidence/`: they are development). Seeds 11, 12 and 13, the live arms', were never played in process.

**Two graded passes, on two trees that differ in GATES and comments only (no AI behaviour changed between them):**
* Tree `dee96b6ddadb6b11`, graded on NEW held-out seeds 501-520 (twenty, see 3), plus the six live arms. Its evidence is
  kept in `evidence/archive/dee96b6ddadb6b11/`. **It FAILED three pre-registered checks:**
  * Two were this round's OWN new checks, each wrong in itself, not in the AI. The re-derived training bound (see 8) was
    taken from the BASE personality, but 2 of 20 runs (506, 516) had DRIFTED into the Story personality during the
    rival's milestone and trained to the Story's minimum. LOSE3 (see 8) graded a run, seed 503, that never reached a
    third loss: a wild battle its status move could not lose within the battle skill's 150 menus.
  * The third is the live arm CH2T's INTENT MIX floor, 28 % against 30 % (see the known limits).
* Tree `a883634ab24c3792`, the FINAL one: every `2026-10-14-step51-*.txt` evidence file at the top of `evidence/` names
  it. Both checks are corrected, each with a unit test and a mutant (G105, G106), and four code comments carrying a
  miscount are corrected (see 4). It is graded on NEW held-out seeds 601-620: VERDICT PASS, every check. The live arms
  were run again on the same AI code. CH1T, CH1M, CH2T and CH2M REPLAYED their `dee96b6` trajectories to the frame
  (148,032 / 158,657 / 90,814 / 134,105: CLAUDE.md rule 8, one trajectory replayed, no second sample), so CH2T FAILS the
  floor again, 28 %. CH1C did NOT replay: 117,428 frames against 136,721. The AI code
  and the arm's settings were the same, and a launcher run's cartridge clock is the host's: that is the likeliest
  difference, not proven. So CH1C, and CH2 from its end (130,440 against 149,447), are new trajectories.

The first round's files are in `evidence/archive/c450adc2865848e4/`.

**The rule violation: a result stated for a tree whose evidence came from another.** The first round's "Known limits"
said the full regression of steps 0-4 had passed on `c450adc2865848e4`, `rate_step4` (36 of 36) included. It had been run
there WITHOUT `--evidence`, so `2026-10-14-step4-RATE.txt` still named `6172ff8932690719` (as did `step4-SURVEY` and
`step2-seed9-RATE`; `provenance.py --check-evidence` counted 18 files of another tree). The verifier re-ran
`rate_step4.py` on c450 and got 36 of 36 PASS, every verdict line the same as the 6172ff file, so the claim was true but
had no evidence of its own. ⇒ This README now states a suite's result only for the tree its evidence file names. **The
full regression of steps 0-4 has NOT been re-run on this round's trees.** Under the round's process it runs ONCE, at the
end of step 5.1. Until then, `provenance.py --check-evidence` lists every step 0-4 file as another tree's.

**1. The intent mix did not separate errands from the beeline** (the verifier: "errand share >= 0.30 in EVERY run" was met
by the ERRANDS_OFF control in 10 of 10 runs; training, healing and shopping dominate it). `MIX_MIN` is kept as it was
registered, now labelled a FLOOR. It is no longer the claim. The claim is CURIOSITY THE STORY DID NOT NEED
(`rate_step5.intent_mix` `free_share`): a curiosity goal in which a milestone passed is the story's own, and is not
counted (the rival's POKé BALL, see 4). The bounds: at least `FREE_RUN_MIN` 0.02 of the goals' frames in EVERY CH1 run,
each personality's mean at least `FREE_MEAN_MIN` 0.05, and THE BEELINE FAILS IT in at least 80 % of its runs.
On 501-520 every CH1 run measured 0.030-0.138 (seed 502 the least, 3,321 frames); the personality means were Trainer
0.106, Story 0.057 and Catcher 0.094; ERRANDS_OFF measured 0.0 in 20 of 20. The 601-620 numbers are in the proof table.

**2. Seed divergence was met by the beeline control too** (goals 0.446 and paths 0.455 under ERRANDS_OFF; paths diverged
MORE without errands). The goals/paths divergence is kept, and its line now says what it shows: pillar 5's "seeds differ",
which dice and personality give the control as well. The ERRANDS' OWN divergence has two new checks:
* THE ERRANDS DIFFER BY SEED. The curiosity decisions in order (`curiosity_sequence`: `kind@map`) of every pair of CH1
  runs of one personality must differ, mean edit distance at least `CUR_DIV_MIN` 0.5. The beeline control has none: 0.
* OFF THE BEELINE (`off_beeline`). These are the tiles a run stood on that NO control run stood on. Each control run is
  measured the same way against the OTHER control runs: the beeline's own seed-to-seed spread, the null. CH1 must have
  more in at least 60 % of the paired seeds and at least 1.3x pooled.
On 501-520: the curiosity sequences 0.729, no pair the same, the control 0.0; off the beeline, CH1 had more in 18 of 20
seeds, 3.58x pooled, against a corridor of 915 tiles. The pre-registered goals/paths divergence: CH1 0.518 / 0.443, the
control 0.309 / 0.412. On 601-620: 0.682; 20 of 20 at 3.79x; 0.553 / 0.459 against the control's 0.367 / 0.407. ‼ The
paths still diverge about as much without errands (0.407 against 0.459). The errands' part is in the two new checks, not
in that one.

**3. The no-speedrun margin was within the noise** (pooled 1.061 against a bound of 1.0, about 1.3 standard errors; CH1
faster than the beeline in 3 of 10 seeds). MEASURED this round: the frames OUTSIDE the needs are dominated by the BATTLES
met on the way. Their number and length are the grass's dice, and they swung single seeds by up to 37,000 frames. Two
more effects push the other way: the errands ADD 4,000-19,000 frames, and a place looked round is walked faster later. On
the development seeds 21-29 the pre-registered ratio measured 0.995, under its bound. Three answers:
* The bound is KEPT exactly as registered (never loosened), and the sweep has TWENTY held-out seeds, twice the pairs.
* NO SPEEDRUN, WITHOUT THE GRASS'S DICE (`time_to_dex`): the AI's own frames to the POKéDEX outside the needs AND outside
  the battles met on the way (its walking, talking and looking). It must be at least `NOBATTLE_RATIO_MIN` 1.02 pooled,
  and CH1 the slower in at least 60 % of the paired seeds. In development it measured 1.069 (9 of 9) and 1.058 (7 of 9),
  with the per-seed ratio's spread 0.035-0.076. The first round's code, recounted on 401-410, gave 1.065 (8 of 10).
* The line now prints the decomposition per seed: what the errands add, and what the rest of the way took more or less.
On 501-520 the kept bound measured 1.095 pooled, CH1 the slower in 16 of 20 seeds. Without the grass's dice it measured
1.088, the slower in 18 of 20. On 601-620 the kept bound measured only **1.026**, CH1 the slower in **9 of 20** seeds:
it passed, but this is the noise the verifier named. Without the dice it measured 1.065, the slower in 15 of 20. ‼ So
the claim that the AI is SLOWER than a beeline rests on the battle-free check and on the behaviour checks of 1 and 2,
not on the kept bound. The literal TOTAL frames to the POKéDEX stay reported only (1.025 on 601-620): the training's
length is the battles' dice too.

**4. Per-run curiosity could be almost zero, and the rival's POKé BALL counted as curiosity in both arms.** The ball is
excluded (1). The verifier's seed 410 (a Catcher with no look round) showed a deeper cause. The graded sweep's kept logs
were read for every detour: **11 of the 12 DETOURS of its CH1 runs had ended at once.** Over every plan of that sweep it
was 56 of 63: 51 "stuck: 51 decisions in a row without a frame passing (every target fails at once)" and 5 "nothing off
the way". (A first count, "15 of 16", written into four code comments of `dee96b6` before this recount, is corrected in
the final tree.) The detour chose an explorer's FRONTIER, which went stale after one step (seen past), and chose it again
and again. Fixed (`GoalRunner._detour`): the detour walks TO the chosen place and stands there
(a `wander` target on its tile, which never goes stale), at least `DETOUR_MIN_TILES` (6) away. A place it cannot reach is
swapped for another, at most `DETOUR_TRIES` (3) in all (G93, G94, G95). The development sweep step51vdev1 then found a
Story run (seed 4) whose three look-around draws all chose nothing: 212 frames of curiosity in the run. A person who has
gone past `LOOK_DEBT` (2) new places in a row without a look round now looks round the next one without a draw, and says
so (G102). Every draw that chooses nothing is TOLD now too ("it goes on without looking round (draw 0.70 >= the Story's
0.55; 1 in a row)", "no detour on ROUTE101 this time"; G98), so the rates can be read from the log.

**5. Two documented rules had no test** (the verifier's own mutants MY3 and MY4, not caught). Two new tests now carry them:
`VerifierRoundTests.test_no_look_around_while_in_danger` (G90) covers README B's "never in danger", and
`test_the_bag_gone_is_handed_back_at_once` (G91) covers `bag_or_its_question`'s "the bag is gone" return, which fired in
none of the graded runs, so only a unit test can carry it.

**6. "Explore a new place" was false in a run that carries on** (CH2T: "a new place, LITTLEROOT_TOWN", its home town). The
look-around's draws were a per-process set. The world memory is carried between sessions, but the goal manager's memory
is not. Now a map the WORLD MEMORY had stood on when the session's first decision was made is no new place
(`_Memory.known_before`; G92). The `personality.py` and `brain/goals.py` texts say so. The live arms check it: A NEW
PLACE IS NEW, every look-around draw (made or not) names a map the world memory it started from had not stood on. In
the three chapter-2 arms on `dee96b6` the draws named only PETALBURG_CITY and ROUTE102, with 12 maps known at the start
(LITTLEROOT and OLDALE among them).

**7. The game-side second path did not cover battles.** `play_harness.waits_now` now reads a battle's own waits. A battle
text waits for A/B when a battler's controller waits on the text printer (`CompleteOnInactiveTextPrinter`) while printer
0 waits (active, state CLEAR or SCROLL_START). The player's controller polls the pad in the action menu, the move grid, a
target or the yes/no (`HandleInputChooseAction`, `HandleInputChooseMove`, `HandleInputChooseTarget`,
`HandleMoveSwitching`, `PlayerHandleYesNoInput`). Three input tasks were added too: the party menu's list and actions,
and the bag's list. The controller condition is what tells a battle's own text from the stale printer state that gave the
first round's 510-frame false alarm (no controller waits on the printer then). A new fault arm proves the reads are not
blind. STALL3 is a copy whose battle skill waits 600 frames at the action menu, and it must FAIL the stall property by
BOTH paths. Development: 3 of 3, AI 645 and game 640 frames each; the two paths agreed in 24 of 24 runs. On 501-520:
STALL3 7 of 7 (AI 643-645, game 640). The two paths agreed in 169 of 169 runs. Every run of the real code was 150
frames by both paths. On 601-620: STALL3 7 of 7 (644-645 / 640), agreement in 170 of 170, the real code 150 by both.

**8. Still open from step 5:**
* **The training bounds were carried over.** They are RE-DERIVED now. The steps bound is the design's own rule: a person
  roams at least `train_min_steps` before a known fight, so the bound is that minimum times 0.9 (Story 72, Catcher 90,
  Trainer 135; `rate_step5.train_steps_min`; G101). It is tighter than the carried 60 for all three. Measured on the 20
  graded runs of seeds 301-310 and 401-410, the game's steps over the personality's minimum were 1.04-1.95. The WON
  bound, 3, is now one under the measured minimum (4-18; NOTRAIN 0 in all 20). ‼ **On 501-520 the steps bound FAILED in 2
  of 20 runs (506: 90 by the game, 88 by its roam reports, against the Catcher's 90; 516: 83 against the Trainer's
  135).** Both runs had DRIFTED into the Story personality during the rival's milestone (`personality.py` DRIFT), and the
  Story's own minimum, 80, judged them trained. The bound had been taken from the BASE personality. Corrected
  (`train_steps_min_run`, G105): it is now the lowest minimum among the personalities a run played AS during that
  milestone (the ACTIVE personality of its goals there), the base's when none drifted. For a drifted run that loosens it
  (516: 135 to 72), and it is never under the carried 60. It is graded on the new seeds 601-620, never on the seeds that
  failed it: 20 of 20 PASS. ‼ There it DECIDED one run, 609, a Trainer that also played as the Story, with 115 steps,
  which the base Trainer's 135 would have failed. Six of the twenty played as two personalities in that milestone. The
  live arms keep the base personality's minimum, which is stricter, and the three CH1 arms pass it.
* **MAX_LOSSES 3 was never reached by an unaltered run.** LOSE3 is a copy whose decider, once its battler is L7, uses its
  status move every turn of a wild battle and never runs. The play loop's REAL `MAX_LOSSES` (3) must end the run within
  6,000 frames of the game's third loss, with the run's report, its told losses and the game's all 3. Development: 3 of
  3 (seeds 2, 5, 8: "play: stuck: 3 battles lost (MAX_LOSSES 3)", 652, 639 and 669 frames after the game's third loss).
  On 501-520, 5 of 6 runs ended exactly so, 630-664 frames after the third loss. ‼ **The sixth, seed 503, FAILED the
  check as registered.** It lost twice, then met a wild battle its status move could not lose within the battle skill's
  150 menus ("the battle did not end within 150 menus", three times), and its patience ended it with 2 losses. Such a run
  tests nothing of the stop. Corrected (G106): the stop is graded on every run the GAME recorded a third loss in, and the
  arm must reach one in at least `LOSE3_REACH_MIN` (60 %) of its runs. On 601-620: 7 of 7 reached it, and each ended
  "3 battles lost (MAX_LOSSES 3)" 631-666 frames after the game's third loss.
* **CH2T replayed its development trajectory.** On these trees no in-process run of seeds 11-13 was made. A THIRD chapter
  2, CH2M (the Trainer's, from CH1M's end, seed 13), was registered in `live_step5.PREDICTED` before ANY run of its
  trajectory, and on `dee96b6` it PASSED its unseen claims (see the proof table).
* **Each live arm is one trajectory on the host clock.** That is what a live arm is, and the frequencies are the sweep's
  (CLAUDE.md rule 9). ‼ CH1T on these trees is the first round's CH1T REPLAYED: the same 148,032 frames, the same 274
  training steps and 21 battles won. None of this round's changes fired in it: its two detour draws and one look-around
  draw chose nothing, no walk ran out of frames, and the debt never reached 2. One trajectory, replayed (rule 8), so it is
  no second sample of chapter 1. On the final tree CH1M, CH2T and CH2M replayed theirs too. CH1C did not (the host's
  clock), so CH1C and CH2 there are new trajectories.
* **Chapters 3 and 4 have never been played.** "Optional gym trainers" and "ROXANNE by her badge alone" are still proven
  in unit tests only. They are the next build step's to play.

**9. The story-goal cooldown counted DECISIONS** (CH2: 10 looks round in a row, about 32,000 frames, while the walk to
PETALBURG waited). Two fixes:
* A story goal put aside now comes back after `COOLDOWN_DECISIONS` decisions OR `STORY_ASIDE_FRAMES` (6,000) frames,
  whichever comes first, and says so (G96).
* The root cause: those two walks had met 8 and 13 battles on ROUTE 102, which ate their 9,000 frames, so they were put
  aside as FAILING. A `go` whose budget ran out while its battles took 600 frames or more now walks on for the frames
  they took, at most its own budget again and at most twice (`GO_BATTLE_EXTENSIONS`; G97).
Graded as A STORY GOAL PUT ASIDE COMES BACK: no streak of asides longer than `ASIDE_STREAK_MAX` 10,800 frames (the
6,000, the look round under way, one battle in it), in every live arm and every sweep run of the real code. On 501-520
asides came only in NOHINTS runs (a step it is never told the map of): the longest streak was 8,188 frames (7,345 on
601-620). In the live
arms on `dee96b6`, CH2M had one streak, `go:PETALBURG_CITY_GYM`: 3 asides, 9,856 frames. CH2T's walk to PETALBURG CITY
walked on twice ("its battles took 12264 of them: it walks on for 9000 more") and arrived, where the first round's CH2
had put two such walks aside.

#### The proof (final tree `a883634ab24c3792`; the failed pass on `dee96b6ddadb6b11` in its archive)

| proof | what it shows | result (`ai_player/evidence/2026-10-14-step51-*.txt`, all naming `a883634ab24c3792`) |
|---|---|---|
| `rate_step5.py` on NEW held-out seeds 601-620 (166 runs + 4 in phase 2) | the round's checks and every earlier one, pre-registered in `BOUNDS` | **VERDICT PASS, every check.** CH1 POKéDEX 20 of 20, the rival at the first try 20 of 20, whiteouts 0. TRAINED by the game, with the drift-corrected bound: 20 of 20; it decided one run, 609 (a Trainer that also played as the Story: 115 steps against the base 135). NOTRAIN 0 of 20, +1.6 levels paired. THE STALL PROPERTY 150 frames by both paths in all 80 real runs; STALL1 14 of 20 (610-643), STALL2 4 of 20 (1,186-1,210), STALL3 7 of 7 (644-645 / 640); the paths agree in 170 of 170. Asides: longest 7,345 frames (NOHINTS), bound 10,800. CURIOSITY THE STORY DID NOT NEED in every run 0.043-0.134 (3,738-19,163 frames); means Story 0.065, Catcher 0.098, Trainer 0.095; the beeline 0.0 in 20 of 20. OFF THE BEELINE: CH1 more in 20 of 20, 3.79x, corridor 917. The errands differ: 0.682, no pair the same. Goals/paths divergence 0.553 / 0.459 (control 0.367 / 0.407). NO SPEEDRUN: the kept bound 1.026, CH1 the slower in only 9 of 20 (reported); without the grass's dice 1.065, the slower in 15 of 20; the total 1.025 (reported). LOSE3: 7 of 7 reached a third loss, each ended "3 battles lost (MAX_LOSSES 3)" 631-666 frames after it. PATIENCE 6 of 6 reached, training stints 51,475-71,947 frames; PATIENCE_OLD stopped 6 of 6, 4 of them while training. DEADREST 115 breaches over 137; NOHINTS 0 of 20; STOP and STOPDEAD (NOHINTS 611, STALL1 609); losses agree in 168 of 168 |
| (archive) `rate_step5.py` on 501-520, tree `dee96b6` (`evidence/archive/dee96b6ddadb6b11/2026-10-14-step51-RATE.txt`; its live arms beside it, CH2T's `2026-10-14-step51-CH2T.txt` the FAIL) | the same checks before their two corrections | **VERDICT FAIL**: the training bound by the base personality (506, 516 drifted) and LOSE3 (503 never reached a third loss). Every other check PASSED; the numbers are in the sections above |
| `live_step5.py` CH1T, CH1C, CH1M | chapter 1 from a REAL New Game through the real launcher (seeds 11, 12, 13) | PASS 3 of 3, purity CLEAN (0 foreign presses, writes and loads; 0 bot calls). `done: ch1_pokedex reached` in 148,032 / 117,428 / 158,657 frames; the game's flags all 1. The stall property 150 frames each. Curiosity the story did not need 6.7 % / 17.7 % / 4.7 %; a new place is new (3 draws each). Trained 274 / 163 / 251 steps (bounds 72 / 90 / 135), 21 / 8 / 19 wild battles WON in the roams. Spins 1 in 688 steps. CH1T and CH1M replay `dee96b6`'s runs; CH1C does not |
| `live_step5.py` CH2 | chapter 2 from CH1C's end (Catcher) | PASS, 130,440 frames: WALLY's tutorial (VAR_PETALBURG_GYM_STATE 2); +4 captures, 4 new PIDs of the player's OT; +1 heal; FLAG_ITEM_ROUTE_102_POTION; curiosity the story did not need 33.8 % |
| `live_step5.py` CH2T | chapter 2 from CH1T's end (Story) | **FAIL: the intent-mix floor, 28 % against 30 %** (the known limits). Its other checks PASS: WALLY's tutorial, +1 capture, +1 heal, the ROUTE 102 POTION, the stall property 150, curiosity 7.3 %, a new place is new |
| `live_step5.py` CH2M | a THIRD chapter 2, registered unseen: from CH1M's end (Trainer) | PASS, 134,105 frames: WALLY's tutorial; +4 captures; +2 heals; the ROUTE 102 POTION; one aside streak, 9,856 frames; curiosity 30.2 % |
| `revert_step5.py` | each rule carries weight | 105 of 105 mutants CAUGHT as predicted (G90-G106 this round's; G60 and G61 re-anchored to the look-around debt) |
| `test_goals.py` | the rules unit by unit | 109 tests OK (`VerifierRoundTests`: 15 new) |
| `extract_milestones.py --verify` / `--plant` | every fact against pret/pokeemerald | OVERALL PASS; the three plants found and nothing else |
| `run_units.py` | the static gate and every unit suite | OVERALL PASS (`check_purity` PASS) |

### Known limits of step 5.1, as the verifier's round left them (superseded by the second round's, below)

* ‼ **The live arm CH2T FAILS the pre-registered intent-mix floor**: 28 % of its goals' frames on errands against 30 %,
  on both trees (the final run replayed `dee96b6`'s to the frame, 90,814). Frames by kind: go 58,364, chat 12,157, talk
  6,641, explore 4,788, shop 4,753, heal 3,447, pick_up 664. The first round's CH2T measured 34 %. The floor (`MIX_MIN`: at least 30 % of the
  goals' frames on errands, in every run) was set from chapter-1 runs, and the verifier showed it cannot separate errands
  from the beeline. CH2T is the Story player in chapter 2. Chapter 2 names no fight, so it does no training, and most of
  its goals' frames went to the story's own walks:
  * ROUTE 102 with its trainers and grass: one walk of 23,473 frames.
  * About 24,000 frames of walks toward PETALBURG's GYM, searching the town door by door. It recognises a centre's and a
    mart's door by their look, but not a gym's.
  * Two walks back to OLDALE, to heal and to shop, though PETALBURG has both (it had not seen them yet).
  Its curiosity the story did not need was 7.3 % (bound 2 %). The floor is NOT re-bounded here: a bound is never loosened
  to pass. Candidates for the next round: recognising a gym by its look (the building and its sign are on screen), and
  looking for a centre in the town it stands in before walking back to one it knows.
* **The full regression of steps 0-4 has NOT been run on this tree** (the rule violation, above).
* **Chapters 3 and 4 have never been played** (8).
* **A live arm is one trajectory.** CH1T replays the first round's (8). On the final tree four of the six arms replayed
  their `dee96b6` runs, so the final live evidence is largely the same trajectories run twice, not new samples.
  ‼ CH1C diverged, from a cause not proven: the cartridge's clock is the host's in a launcher run.
* **The kept time bound includes the battles' dice.** On the development seeds 21-29 it measured 0.995, under its 1.0.
  It passed on 501-520 (1.095) and only just on 601-620 (1.026, the slower in 9 of 20). A failure of it would be the
  grass's dice, which the battle-free check removes (1.088 and 1.065).
* **OFF THE BEELINE's corridor is the sweep's own control runs** (20 runs, 915 tiles on 501-520). Fewer control runs give
  a smaller corridor and larger counts. It counts tiles only, not when a place was visited.
* **The drift correction of the training bound** takes the LOWEST minimum among the personalities a run played as during
  the rival's milestone. Which personality judged it trained is not logged, so this is the looser reading.
* **LOSE3's mutant cannot always lose.** A wild battle its status move cannot lose within the battle skill's 150 menus
  happened in one run of six on 501-520. The check grades the runs that reached a third loss, and the arm must reach one
  in 60 % of its runs.
* **The second path's battle reads** are the player's controller polling the pad, a battler's controller waiting on the
  text printer, and the party menu's and bag's input tasks. Their names are the symbol table's. Any other screen inside a
  battle (the summary screen, the forget-a-move list) is the AI's own record alone.
* `LOOK_DEBT` (2), `DETOUR_MIN_TILES` (6), `STORY_ASIDE_FRAMES` (6,000) and `GO_BATTLE_*` are taste and bounds, not
  measured from people.

### Step 5.1, the verifier's second round (2026-10-14/15)

The step-5.1 verifier graded tree `a883634ab24c3792` `all_pass: false` on two failures (the live arm CH2T under the
intent-mix floor; the full regression of steps 0-4 not run on that tree) and eight weak proofs. Each is answered below, on
ONE final tree, working-tree digest `d3d34871df0ac077` (every `2026-10-15-step51-*.txt` at the top of `evidence/` and every
steps 0-4 file of the full regression names it; the tree itself is kept, `evidence/trees/d3d34871df0ac077.zip`; the first
graded pass's tree `d0c949e96d355afe`, which FAILED one check, below). Every rule below has a unit test
(`gates/test_goals.py` `SecondRoundTests`, and `PlayLoopTests` for the verifier's V9) and a mutant (`gates/revert_step5.py`
G107-G138). The fixes were developed on NEW development seeds, chapter 1 AND chapter 2: 31-39 (`step51wdev1`, before the
fixes it found), 41-49 (`step51wdev2`), 51-59 (`step51wdev3`), and after the first graded pass (below) 61-72
(`step51wdev4`) and 81-92 (`step51wdev5`, the AI code graded), kept outside `evidence/`; the first graded pass played NEW
held-out seeds 701-720, the final one NEW held-out seeds 801-820; the live arms' seeds 11-13 were never played in process.

**FAILURE 1: CH2T under the intent-mix floor (28 %; honestly 16 %).** Three parts.
1. *The grader is honest* (`rate_step5.goal_spans`, `intent_mix`). The play loop now writes every goal's END (`goal_end`,
   `mode.py`; a goal DROPPED because a scene began while it decided included): a goal's frames end there. CH2T's dropped
   `chat` at f227827 had been graded as the 11,019 frames of WALLY's tutorial that followed it. What the loop played after a
   goal ended is no goal's frames (`between_goals`, reported, and the share with them counted as the story's,
   `errand_share_with_scenes`, reported beside the graded one). A curiosity goal in which the story moved on is the story's
   in the ERRAND share too, not only in the curiosity the story did not need (the verifier: "MIX_MIN counts story-owned
   curiosity goals as errands"); a milestone record is a goal's only within `END_SLACK` (60) frames of its end (the loop
   writes it on its next pass with no frame passing; development found the beeline's rival POKé BALL counted as free
   curiosity without this). On CH2T's own log (no end records) the honest share is 16.3 %, the verifier's recount. G122,
   G123, G124, G125.
2. *Chapter 2 is played like a person* (`brain/goals.py`; CH2T's 58,364 frames of `go` were mostly a door-by-door search of
   PETALBURG for its GYM, about 25,700 frames, and two walks back to OLDALE past PETALBURG's centre and mart):
   * a GYM is RECOGNISED by its door, `looks.gym_door`: METATILE_General_Door_Gym (0x1CD), the general tileset's, read under
     the warps to MAP_PETALBURG_CITY_GYM (15, 8) and MAP_RUSTBORO_CITY_GYM (27, 19) in pret's layouts and checked by
     `extract_milestones.py --verify` (12 looks). A walk to a gym ends as soon as its door is SEEN and goes in by it
     (`GoalRunner._to_building`); in the development sweeps dev2 and dev3 all 18 chapter-2 runs went in by the door's
     look, each walk to the gym 173-8,354 frames (median 899). G107, G108;
   * the NEAREST place to heal or to shop, one it has been in or one whose door it has seen (`_nearest_place`; step 5 took
     any place it had been IN first, however far); hurt in a TOWN whose POKéMON CENTER it has not seen, it looks for it
     there first, once (`find_center` with `via`, `CENTER_LOOK_FRAMES` 3,000). G109, G110, G126;
   * the BALANCE (`GoalManager.spent`, `owed`; `personality.py` `Errands.balance` and `curious_min`): a person keeps a share
     of a session's time (its goals and the scenes between them, once it has a Pokemon) for errands, Catcher 50 %, Trainer
     48 %, Story 45 %, and of it some for CURIOSITY alone, Catcher 12 %, the others 10 %. Under either, the curiosity draws
     (look round, catch, chat, detour) pass without the dice and say so ("draw 0.95, but 28 % of this session's 47,782 goal
     frames went to errands, under the Story's 40 %: a break from the story", a development run's line when the Story's was
     40 %), a walk that arrives on another outdoor map
     stops there once a milestone (`OWED_STOP`), and with no draw due it looks round where it stands some more (at most
     `AGAIN_MAX` 2 a map and milestone). Never under the beeline control. G111-G116, G132, G136;
   * its first POKé BALLS are tried: a POKéDEX holding only its first Pokemon passes the catch draw (development seed 31's
     Story player went through chapter 2 with five balls and caught nothing). G133.
3. *Chapter 2 is in the sweep* (`rate_step5.py` plans CH2 and CH2_OFF, `CHAPTER2`, `run_chain`): every CH1 (and
   ERRANDS_OFF) run that reached the POKéDEX goes on, in its own worker, from ITS OWN end state and world memory to WALLY's
   tutorial. Graded there: WALLY by the game, the intent-mix floor and the curiosity the story did not need in EVERY run, a
   new place new to the memory it started from, the beeline's chapter 2 under the floor, the chapter-2 time without the
   grass's dice, and with every real plan the stall property by BOTH paths, the asides, the pages and the losses.
   (`chapter2_verdicts`; the bounds pre-registered from the development sweeps, `BOUNDS` CH2_*.)

**Found by the development sweeps and fixed** (each with its test and mutant):
* dev1 seeds 33, 36, 37, 38: OLDALE's centre door, seen from ROUTE 102 across its right edge, was kept on ROUTE 102 at
  (56, 16). As the NEAREST place it was a door nobody could reach, and a party in danger tried it again every 20-40 frames
  until the patience ran out: two runs stopped on "no progress for 120,000 frames", and the game's second path read a
  stale "text waits" for 120,020 frames in them (no press came) while the AI's record said 150: the two paths DISAGREED and
  the agreement check failed, as it should. Fixed: a door past an edge it has crossed is the next map's (G127); a door it
  cannot walk into is forgotten (`DOOR_UNUSABLE`, G128); in danger a heal is tried again at most `DANGER_RETRIES` (3)
  times in a row (G129).
* dev1 seeds 37, 39: DAD chosen as a "chat" under the balance, a story-owned goal under an errand's name: the person the
  story's step names is no chat (G130).
* dev1 seed 32: a look round put aside for a story goal, begun 617 frames before the breather's end, ran 6,444 frames among
  the grass's battles (a streak of 11,827 over `ASIDE_STREAK_MAX`): an aside look round lasts only the breather left, and
  with under `ASIDE_LOOK_MIN` (600) left the story goal comes back (G131).
* dev2 seed 42: the stall property caught a NEW stall, by both paths (AI 1,203, game 1,200 frames): the poison's "TREECKO
  fainted…" came up as the AI reached the nurse, and `nurse_heal`'s talk stood waiting for the player to be free. With
  `give_way` (`hands/menus.py`, story skills only; the step-2 default unchanged) the nurse and the clerk hand a waiting
  screen back at once, it is played, and they are asked again (G134, G135).
* dev2: the time to the POKéDEX outside the needs fell within the beeline's noise (0.975, the kept bound FAILED; without the
  grass's dice 1.028 with 5 of 9 slower). Chapter 1's training filled the balance with needs while its curiosity was 4 %
  in some runs: the curiosity minimum (G136). dev3: 1.137 (8 of 9) and 1.163 (9 of 9).

**The first graded pass FAILED one check, and was kept.** Tree `d0c949e96d355afe` (its files are archived in
`evidence/archive/d0c949e96d355afe/`, the tree in `evidence/trees/d0c949e96d355afe.zip`) was graded on held-out seeds
701-720: every check PASSED but one, CH2's intent-mix floor in EVERY run: seed 706, a Story player, 28.7 % (the other 19
runs 0.38-0.64). Read from its log: the gym's door was already KNOWN when it set out from OLDALE's POKéMON CENTER, so
`_to_building` went straight to `_go_inside`, whose walk to PETALBURG had none of the go's own stops: the stops a break
owed (its balance said "34 % of this session's 41,252 goal frames went to errands, under the Story's 40 %") never came,
and the talk to DAD and WALLY's scene ended chapter 2 under the floor. 19 of that sweep's 22 gym walks had begun with the
door known, 12 of them from another map (OLDALE or ROUTE 102). And earlier, a look round PETALBURG of 5,012 frames had not passed its centre, so
the town was taken for one with none (the `explored` rule) and the heal was a walk back to OLDALE. Two fixes, each with
its test and mutant: the way to a known gym's town is a walk like any other, its stops held, then in by the door (G137);
only a town SEEN ALL OF (`WorldMemory.promise` 0) and looked round has no centre to look for (G138). The six live arms on
`d0c949e` had all PASSED (archived beside it). Everything was run again on the final tree below: new held-out seeds
801-820, the six live arms, the mutants and the units.

**FAILURE 2: the full regression of steps 0-4** ran ONCE, on the final tree (the proof table below).

**The weak proofs:**
1. *Chapter 2's stall property rested on the AI's eyes alone.* The sweep's CH2 and CH2_OFF runs are real plans: the stall
   property by BOTH paths over chapter 2's screens (the marts' menus, the PETALBURG gym, WALLY's tutorial). A launcher run
   (the live arms) still has only the AI's record while it plays.
2. *The no-speedrun margin was thin* (1.024 total, 9 of 20 by the kept bound). The curiosity minimum (above), and chapter
   2's own check, CH2 over CH2_OFF without the grass's dice (development 1.491 and 1.369). Graded numbers in the table.
3. *The drift correction was the loosest reading.* The goal manager now LOGS whose rule judged the training done
   (`fight_prep` `judged_by`, `min_steps`) and the bound is that personality's own minimum (`train_steps_min_run`; the
   lowest of those it played as only for a log without it). G120, G121.
4. *Two mutants were not caught* (the verifier's V3 and V9): `test_a_walk_walks_on_twice_when_its_battles_ate_it_twice`
   (three walks, two extensions) and `test_a_scene_soon_after_a_map_change_comes_before_any_goal` (a scene SETTLE_FREE - 10
   frames after the map change is played before any goal is chosen). G117, G118.
5. *"A level gained" was the party's SUM* (WALLY's lent Zigzagoon: "10 -> 15"). Now one Pokemon, by its PID, above the
   highest level it was seen at (`mode.py` `_progress`). G119.
6. *The live arms were largely replays; "the trees differ only in gates" could not be checked.* The AI changed, so all six
   arms are new trajectories against `a883634`'s (five of them ended on the same frame on the two graded trees of this
   round, the table's caveat). Every graded driver now KEEPS its tree (`provenance.snapshot_tree`: `evidence/trees/
   <digest>.zip`, the diff against HEAD and the untracked files, its digest recomputed from its own contents;
   `provenance.py --compare A B` lists the files two kept trees differ in; `test_evidence.py` SnapshotTests).
7. *MIX_MIN counted story-owned curiosity as errands*: fixed in the grader (FAILURE 1, part 1).
8. *Chapters 3 and 4 have never been played.* Still true (the known limits). No save holds the badge without the gym's
   trainers beaten, so "ROXANNE by her badge alone" cannot be shown on a real save either: `gym1_done.ss1`,
   `r20_badge1_party1_gym.ss1`, `ki_ch12_gymdoor.ss1` and `ki15_gymdoor_wedge.ss1` have TRAINER_JOSH, TRAINER_TOMMY,
   TRAINER_ROXANNE_1, DEFEATED_RUSTBORO_GYM and BADGE01_GET all 1, `rustboro.ss1` and `r20_pregym1_party4_r116.ss1` all 0
   (the harness's second-path read, 2026-10-15).

#### The proof (final tree `d3d34871df0ac077`)

| proof | what it shows | result (`ai_player/evidence/2026-10-15-*.txt`, all naming `d3d34871df0ac077`) |
|---|---|---|
| `rate_step5.py` on NEW held-out seeds 801-820, chapter 1 AND chapter 2 (213 runs; `2026-10-15-step51-RATE.txt`) | every check of the rounds before, and chapter 2's, pre-registered in `BOUNDS` (none changed after the first graded pass) | **VERDICT PASS, every check.** CH1: POKéDEX 20 of 20, the rival at the first try 20 of 20, whiteouts 0. TRAINED by the game 20 of 20 against the bound of the personality whose rule JUDGED it (801 played as Story and Trainer, judged by the Trainer's: bound 135, 207 steps; 819 the same two, judged by the Story's: 72, 130). NOTRAIN 0 of 20, +1.5 levels paired. Spins 4 in 3,230 steps. THE STALL PROPERTY over 120 real runs, chapter 2's included: AI 150, game 180 frames; STALL1 16 of 20, STALL2 9 of 20, STALL3 7 of 7; the paths agree in 213 of 213. Asides: longest 6,220 (bound 10,800). CURIOSITY THE STORY DID NOT NEED in every CH1 run 7.1-18.2 % (means Trainer 13.5 %, Story 11.6 %, Catcher 15.6 %); the beeline 0.0 in 20 of 20. OFF THE BEELINE 20 of 20, 6.82x (corridor 905). The errands differ 0.596; goals / paths 0.544 / 0.445 (control 0.376 / 0.417). NO SPEEDRUN: kept bound 1.135, the slower in 16 of 20; without the grass's dice 1.141, 19 of 20. LOSE3 5 of 6. PATIENCE 7 of 7 reached, stints 58,157-96,508 frames; PATIENCE_OLD stopped 7 of 7, 5 while training. DEADREST 131 over 159; NOHINTS 0 of 20; STOP / STOPDEAD 3 / 3; losses agree in 210 of 210. **CH2**: WALLY's tutorial 20 of 20 (63,784-174,264 frames); the intent-mix floor in EVERY run 40.6-59.1 % (the Story's 40.6-49.5 %; with the scenes counted as the story's 34.6-53.1 %, reported); curiosity the story did not need 19.4-52.4 %; a new place new in all 40 draws; whiteouts 0; CH2_OFF under the floor in 19 of 20 (814 at 30.05 %); the chapter-2 time without the grass's dice 1.403, the slower in 20 of 20 |
| (archive) `rate_step5.py` on 701-720, tree `d0c949e` (`evidence/archive/d0c949e96d355afe/2026-10-15-step51-RATE.txt`) | the same checks before G137, G138 and the balance raise | **VERDICT FAIL**: CH2's floor in seed 706 (Story), 28.7 % (above). Every other check PASSED, among them WALLY 20 of 20 and CH2_OFF under the floor 16 of 20 |
| `live_step5.py` CH1T, CH1C, CH1M | chapter 1 from a REAL New Game through the real launcher (seeds 11, 12, 13) | PASS 3 of 3, purity CLEAN (0 foreign presses, writes and loads; 0 bot calls). `done: ch1_pokedex reached` in 143,957 / 116,754 / 170,501 frames. The stall property 150 frames each. Errands 71.5 / 65.0 / 64.3 % of the goals' frames; curiosity the story did not need 12.4 / 20.8 / 14.8 %. Trained 274 / 163 / 251 steps; 17 / 8 / 19 wild battles won in the roams; spins 1 in 688 steps |
| `live_step5.py` CH2 | chapter 2 from CH1C's end (Catcher) | PASS, 129,349 frames: WALLY's tutorial; +4 captures; +1 heal; FLAG_ITEM_ROUTE_102_POTION; errands 48.1 % (44.0 % with the scenes); curiosity 35.1 % |
| `live_step5.py` CH2T | chapter 2 from CH1T's end (Story): the arm that FAILED | **PASS**, 69,411 frames: errands **40.2 %** (33.9 % with the scenes; bound 30 %), against 28 % on the verifier's tree (16.3 % honestly). WALLY's tutorial, +1 capture, +1 heal; curiosity 29.3 %; the stall property 150 |
| `live_step5.py` CH2M | chapter 2 from CH1M's end (Trainer) | PASS, 181,977 frames: WALLY's tutorial; +5 captures; +2 heals; the ROUTE 102 POTION; errands 50.8 %; curiosity 47.2 % |
| (live, the caveat) | | Five of the six arms ended on the SAME frame as their runs on `d0c949e` (that tree's arms all PASSED too; archived beside its sweep): most likely the same trajectories, which the balance raise and G137/G138 did not reach (the logs were not diffed). CH2M diverged (182,980 frames there). One trajectory each; the frequencies are the sweep's |
| `revert_step5.py` (`2026-10-15-step51-REVERT.txt`) | each rule carries weight | 137 of 137 mutants CAUGHT as predicted (G107-G138 this round's; G10, G43, G60, G61, G63, G85, G87, G96, G102 and G111 re-anchored) |
| `test_goals.py` | the rules unit by unit | 136 tests OK (`SecondRoundTests`, and `PlayLoopTests` for V9) |
| `extract_milestones.py --verify` / `--plant` | every fact against pret/pokeemerald, the gym's door among the 12 looks | OVERALL PASS; the three plants found and nothing else |
| `run_units.py` (`2026-10-15-step51-UNITS.txt`) | the static gate and every unit suite | OVERALL PASS: `check_purity` PASS; test_check_purity 29, test_host 20, test_eyes 56, test_hands 57, test_world 132, test_battle 107, test_evidence 10, test_goals 136 |
| **the full regression of steps 0-4** (FAILURE 2), once, on this tree | nothing earlier broke | **PASS, every driver exit 0.** `live_step0` OVERALL PASS; `live_step1` PASS; `live_step2` PASS (and `--seed 9` PASS); `live_step3` PASS; `live_step4` PASS; `revert_step11` PASS; `revert_step2` 39 CAUGHT + 5 REDUNDANT ALONE as predicted, of 44; `revert_step3` 93 + 1 of 94; `revert_step4` 62 of 62; `rate_step3` OVERALL PASS; `rate_step4` 36 of 36 PASS; `survey_party_moves` written (a survey, no verdict). 191 evidence files of steps 0-4 dated 2026-10-15, every one naming `d3d34871df0ac077`; 190 with their verdict PASS, and the survey, which has none |

### Known limits of step 5.1 (the second round)

* **Chapters 3 and 4 have never been played** (weak proof 8): "optional gym trainers" and "ROXANNE by her badge alone"
  are unit-tested only, and no save shows them either. The gym's door is recognised in RUSTBORO by the same metatile (read
  from pret's layout), not yet seen live. They are the next build step's to play.
* **The BALANCE makes the floor partly the AI's own aim.** The graded floor (`MIX_MIN`, 30 % of the goals' frames) and the
  AI's balance (45-50 % of its time, scenes included) measure nearly the same thing, by design: a person keeps a share of
  their time for things besides the story (design draft §5, "even the Story personality takes them"). What separates the
  AI from a beeline is graded apart from it: the beeline's chapter 2 under the floor (CH2_OFF), the curiosity the story did
  not need in EVERY run, the off-the-beeline tiles and the no-speedrun times. The balance values are taste, chosen above the
  floor with room for the story stretch that ENDS a session (the walk to DAD, his talk, WALLY's scene: no break can follow
  them): in development, at 36 % the Story's chapter 2 ended at 31 % and 35 % (dev1), at 40 % at 34-39 % (dev4: its own
  count 51 % before the last stretch, 34 % after it), so the Story's is 45 % and the Trainer's 48 % (dev5, seeds 81-92:
  every chapter-2 run 42-65 %, the Story's 42-51 %; the beeline's 0-25 %).
* **The honest share excludes the scenes between goals** (no goal's frames). With them counted as the story's time the
  share is lower: it is reported beside the graded one in every live evidence file and every chapter-2 sweep line (the
  graded numbers are in the table). (CH2T's old log has no end records: there the honest share falls back to "to the next
  goal", 16.3 %.)
* **A launcher run's stall property is the AI's own record**; the game's second path reads chapter 1 and chapter 2 only in
  the sweep. Inside a battle the summary screen and the forget-a-move list are the AI's record alone.
* **A live arm is one trajectory on the host's clock.** This round's are NEW trajectories against `a883634`'s (the AI
  changed), but five of the six ended on the same frame as on the first graded pass's tree `d0c949e`, so the final live
  evidence is largely those trajectories run twice. Each is one sample; the frequencies are the sweep's.
* **The balance was raised after a graded failure** (Story 40 % -> 45 %, Trainer 45 % -> 48 %), with the gym-walk fix. It
  is taste, measured on two NEW development sweeps (61-72, 81-92) and graded on NEW held-out seeds (801-820); no bound
  changed. The Story's chapter 2 still ends nearest the floor (40.6 % at the lowest), because the session ENDS on the
  story's own stretch.
* **The curiosity minimum is taste too** (Catcher 12 %, the others 10 %). Development measured chapter 1's no-speedrun time
  at 0.975 without it (dev2) and 1.137 with it (dev3); the graded number is in the table.
* `BALANCE_MIN_FRAMES` (12,000), `AGAIN_MAX` (2), `CENTER_LOOK_FRAMES` (3,000), `DANGER_RETRIES` (3), `ASIDE_LOOK_MIN`
  (600) and `END_SLACK` (60) are bounds chosen, not measured from people.
* The earlier rounds' limits that still hold: OFF THE BEELINE's corridor is the sweep's own control runs; LOSE3's mutant
  cannot always lose (graded on the runs that reached a third loss); `LOOK_DEBT`, `DETOUR_MIN_TILES`, `STORY_ASIDE_FRAMES`
  and `GO_BATTLE_*` are taste.

## The story (build step 5)

The AI plays the STORY itself (design draft §2.3 "goal manager", §6 step 5; HUMAN-PLAY-DESIGN pillars 1, 4 and 5; USER
RULING 37: badge 1 in 4 chapters). RULING 35 holds: the bot's `story/*` routines are teaching material, read only by the
TEST-side extractor; the play loop runs the AI's own code over the AI's own data, and the purity gate is unchanged (the
eyes gained READ-ONLY reads only: below).

### What it knows: `knowledge/milestones.json`, and how that was checked

20 milestones, chapter 1 (the truck, MOM, the wall clock, the rival's house, PROF. BIRCH on ROUTE 101, the starter, the
lab, the rival on ROUTE 103, the POKéDEX), chapter 2 (OLDALE, ROUTE 102, PETALBURG, DAD at the gym, WALLY's tutorial),
chapter 3 (ROUTE 104, PETALBURG WOODS and the AQUA grunt, RUSTBORO) and chapter 4 (the gym's trainers, ROXANNE). Each
names the game's own PROOF (flags and vars, e.g. `FLAG_DEFEATED_RIVAL_ROUTE103`, `VAR_BIRCH_LAB_STATE >= 3`), its maps,
its steps (go, ask, talk, use, follow), the HINT the game itself gives (the words and who says them: the rival's mom "{RIVAL}
went out to ROUTE 103", MOM's "next door", the TV's "PETALBURG GYM", DAD's "Head for RUSTBORO CITY ... the GYM LEADER,
ROXANNE") and the levels of the fight ahead. A hint's map is a place its words NAME (or the map whose own script says them),
never one the game does not say: `test_goals.py` checks every hint (since the step-5 verifier's round, which found ROUTE
102 and ROUTE 104 named as goals that no dialogue names; both are now waypoints passed on the way to PETALBURG and
RUSTBORO CITY, the places the game names). The intro's
milestone is a WAYPOINT (its flag is set by a coord event INSIDE the truck, so it passes on that map). Written by
`gates/extract_milestones.py` from the bot's `story/early_game.py` (each milestone names the lines it was taught by and the
file's sha256); `--verify` checks, through `gh api` against pret/pokeemerald: every flag and var number, that a script
SETS each proof, every trainer id and party level, every look's graphics id and metatile, and that every hint's words are
in the game's text; `--verify --plant` plants three wrong facts (a flag number, a party level, a graphics id) and must
find exactly those. The wall clock's metatile differs from the ROM layout's (the houses' decorations), so it was MEASURED
live per house (BRENDAN's 2F (5,1) 0x28F, MAY's 2F (3,1) 0x22F).

What the eyes gained (read only): `Progress.marks` (the milestones' flags and vars from save block 1 at the decomp-checked
numbers, `eyes/view.py` `MILESTONE_FLAGS`, `MILESTONE_VARS`, `milestone_marks`), `PlayerState.gender` (the player's own
sprite), the starter screen's two menus (`Task_HandleStarterChooseInput` with its cursor, the confirm yes/no), and five
measured scenes: the starter choice opening and closing, the first battle's start (`CB2_ChooseStarter`,
`CB2_StarterChoose`, `CB2_GiveStarter`, `CB2_StartFirstBattle`) and one frame per ledge jump or map edge crossed (a
settling position: `hands/dialogue.py` busy_reason). Before them each chapter-1 run stood still about 8 times under the
catch-all reason; since, none in 27 runs (sweep `step5dev4`).

### The goal manager: `brain/goals.py`

At every decision: which milestone the marks prove done (a proof NOT READ is never progress), then ONE goal with its
reason, in this order:
* **HEAL** when a Pokemon fainted or the party is under the personality's `heal_below` (Catcher 50 %, Story 60 %, Trainer
  45 %), or, trained and ready for a known fight, under 90 % (`HEAL_BEFORE_FIGHT`): the nearest
  POKéMON CENTER it knows (a door it RECOGNISED by its look, kept in the world memory so a later run remembers it), else
  home, where MOM heals; the nurse is found by her look at the counter. On the way it keeps out of the tall grass where
  it can (`HURT_GRASS_COST`). A heal that failed twice is put aside like any goal, EXCEPT when the party is in danger (a
  Pokemon fainted, or the strongest under a third: `needs_rest`): then it heals again at once.
* **SHOP** for POKé BALLS once the adventure has started (`FLAG_ADVENTURE_STARTED`), when fewer than the personality's
  `balls_low` and the money is there: the MART it recognised.
* **TRAIN** before a known fight (the milestone's fight levels): to its strongest level + the personality's margin (Trainer
  +3, Catcher +2, Story +1) and at least its minimum of roaming steps (Trainer 150, Catcher 100, Story 80), in sessions
  of roaming the nearest grass; at most `TRAIN_SESSIONS` (then it is "ready", and says why). Never far below: a Story
  player still trains to the fight's level + 1. Never while hurt. A roam STOPS after a battle that left the party under
  the personality's `heal_below` (`training_rest`, asked by the navigator after every battle: `battle_rest`), so the next
  decision heals. Under the no-training fault the heal before the fight still happens (the fault removes training only).
* **ITEM**: an item ball on screen, not tried yet (a roam and a walk STOP for one that comes into view).
* **CATCH** a species it has not caught (Catcher most), with balls in the bag.
* **CHAT** with someone nearby not met yet (Trainer most).
* **STORY**: the milestone's next step. `go` where the game SAID (the words must have been READ, as WHOLE words: "LAB" is
  not heard in "not available"; none: it explores, and where the milestone says who would know, it `ask`s the people
  there; a hint with NO words, the truck's open door or a sign it never read, is headed for only once the AI has been
  there itself; the goal's reason quotes the page it READ, the most recent that says the words, never the milestone's
  stored line), `seek` someone it saw earlier on this map where
  they stood, `find` them, `talk` to who looks like them, `use` a thing (PROF. BIRCH's bag, the clock), `follow` a scene.
  Heading for a map it has not been to, it walks first to the open map with the most left to see (`lead_toward`), or to
  a building's own town ("PETALBURG GYM" is in PETALBURG CITY).

A goal that failed twice is put aside for 12 decisions; the run ends by itself when no milestone came for
`STORY_PATIENCE` frames (checked on every pass of the loop, a screen that never frees included), or when `MAX_LOSSES`
battles were LOST (every battle the navigator's battler played, inside a goal or in a scene: `mode.py` `_count_losses`,
each loss told "a battle was LOST (n of at most 3)"; the end line reports the loop's count and never recounts it), with
that reason. Both ends are driven through the real loop by `test_goals.py` PlayLoopTests. Every goal is told
(`[AI-GOALS] goal <kind>: <reason>`) and logged as a `goal` record; every milestone as `[AI-GOALS] MILESTONE <id> done at
f<frame>`. A training roam's report says how its battles ENDED (won, caught, lost, and "fled" for the ones RUN from).

### The personality: `personality.py`

Errand weights per personality (`ERRANDS`), a DRIFT every `DRIFT_EVERY` steps with chance `DRIFT_CHANCE` to another
personality for `DRIFT_STEPS` steps and back (logged `[AI-PERSONALITY]`), a starter drawn by a slight lean
(`STARTER_LEAN`: TREECKO, TORCHIC, MUDKIP weights per personality; `AI_PLAYER_STARTER` overrides) and a FAVOURITE species
drawn from the wild ones (logged; the shiny hunt is deferred).

### The proof (one tree: working-tree digest `6172ff8932690719`, every step-5 file below names it)

Every claim is graded by the GAME through a second path (the harness's own reads of save block 1's flags, vars and
counters, the framework's party decoder, save block 2's name and gender, and in the sweep the game's own battle outcomes,
`gBattleOutcome` with `gBattleTypeFlags`, and its own step counter over time), never by the AI's eyes; the AI's told lines
are only cross-checked against it. This is the tree of the step-5 verifier's ROUND 2 (its section below); round 1's tree
was `c3eb4fd9579e6d78` and the first tree `59521c7ebf62dc70` (their files are in `evidence/archive/<digest>/`).

| proof | what it shows | result (evidence `ai_player/evidence/2026-10-14-step5-*.txt`) |
|---|---|---|
| `live_step5.py` CH1T, CH1C, CH1M | chapter 1 from a REAL New Game through the real launcher (title, naming, the clock), one per starter and per personality (seeds 11, 12, 13) | all PASS, purity CLEAN, `play: done: ch1_pokedex reached` in 105,754 / 95,266 / 138,155 frames (bound 300,000); the game's flags RECEIVED_POKEDEX_FROM_BIRCH, SYS_POKEDEX_GET, ADVENTURE_STARTED, DEFEATED_RIVAL_ROUTE103, SET_WALL_CLOCK all 1; the starter named is the first Pokemon, the player's own by OT; TRAINED (round 2: inside its TRAINING roams for the rival, 2 / 1 / 3 of them): 155 / 120 / 266 roaming steps and 11 / 6 / 11 wild battles WON there (between the starter and the rival in all, reported: 11 / 8 / 19 won); THE REST RULE 0 breaches over 2 / 0 / 2 occasions (roams stopped by a rest 2 / 0 / 2); its END LINE's losses (0) == its log's == the play loop's TOLD losses (0), its training counts (met 11 / 6 / 11, won 11 / 6 / 11) == its own log; its told wild battles == GAME_STAT_WILD_BATTLES (13, 13, 21); MOM's heals by the game's GAME_STAT_RESTED_AT_HOME 1 / 1 / 3; spins 1 / 0 / 1 (2 in 541 steps, 0.37 %); no catch-all; never without a goal; its reasons quote the pages it READ ("Oh, BRENDAN went out to ROUTE 103 ...", "We should head back to the LAB." in CH1T, a GIRL's run) |
| `live_step5.py` CH2 (stretch) | chapter 2 from the CH1C arm's own end state and world memory | PASS, CLEAN, `done: ch2_wally reached` in 138,555 frames: HIDE_PETALBURG_CITY_WALLYS_MOM 1 and VAR_PETALBURG_GYM_STATE 2; GAME_STAT_POKEMON_CAPTURES +5 with 5 new PIDs of the player's OT; GAME_STAT_USED_POKECENTER +2; FLAG_ITEM_ROUTE_102_POTION set (on the SECOND walk to it: a trainer's battle took the first, round 1's section); 10 POKé BALLS bought at OLDALE's MART (money 3300 -> 1256); the rest rule 0 breaches over 2 occasions; its losses 0 == told 0 |
| `rate_step5.py` (NEW held-out seeds 301-310, in-process, clock pinned; 40 runs + 4 in phase 2) | how OFTEN; what each fault costs | VERDICT PASS. CH1: the POKéDEX 10 of 10, the rival at the FIRST try 10 of 10; TRAINED BY THE GAME in every seed (round 2): inside the windows its log says it roamed to train before the rival's flag, the game's own step counter rose 88-293 (its roam reports 86-290) and the game says 4-18 wild battles were WON there (bounds 60 and 3); whiteouts 0, the rest rule 0 breaches over 14 occasions, spins 8 in 1,603 steps (0.50 %), the catch-all 0, the recorder saw every battle end. THE TRAINED CHECK TELLS TRAINING FROM NONE: it passes 10 of 10 CH1 seeds and 0 of 10 NOTRAIN seeds (no training window: the game's steps and won battles there 0 in every seed, though NOTRAIN won 0-15 wild battles elsewhere before the rival). ALL PLANS: the AI's report == its TOLD losses == the game's in 42 of 42 runs (the game's: CH1 0, NOTRAIN 3, NOHINTS 0, DEADREST 0, STOP 2). NOTRAIN: wild battles won before the rival 63 vs 132; the strongest level at the rival's flag PAIRED by seed +1.1 (every seed +1 or +2); the HP the fight left, paired, +0.10 (reported); first-try 8 of 10 vs 10 of 10 (reported). DEADREST (the rest fix removed): 53 battles fought on under heal_below over 66 occasions (the real code 0). NOHINTS: 0 of 10 reach the POKéDEX, every one ending `play: stuck: no milestone for ~120,000 frames (since <milestone>)`. STOP (phase 2: the two NOTRAIN runs the game recorded a loss in, 307 and 310, replayed with MAX_LOSSES 1): both end `play: stuck: 1 battles lost (MAX_LOSSES 1)` 682 / 679 frames after the game's record of the loss, at the same frame as the base runs' (f59490, f56400); STOPDEAD (the loop's count also removed, G46): neither stops (both reach the POKéDEX, 28,798 / 40,628 frames later), report and told 0 while the game lost 1 / 2 |
| `test_goals.py` | the rules, unit by unit: the milestone table and the marks, milestone detection, the hints (words heard as WHOLE words, the page READ quoted, the pages kept, a `go` with its words unheard, a wordless hint only for a place it has been, every hint's map NAMED by what is said, asking, hints off), the errands by personality (the training target from the boss levels, the session bound, no training hurt, a heal again in danger, the heal before the fight under the no-training fault), the rest rule (by personality, installed and cleared, asked with no battle limit, the battle's kind during the battle, a walk to heal kept out of the grass, an item walk a battle ate tried again), a roam's battles by how they ended, the losses (in goals, MAX_LOSSES), THE PLAY LOOP ITSELF (MAX_LOSSES and STORY_PATIENCE through `HandsBrain._play`), the drift, the choices, the ways, someone seen sought where they stood, the doors kept with the memory | 59 tests OK |
| `revert_step5.py` | each rule carries weight: one broken in a COPY, its predicted test fails | 52 of 52 mutants CAUGHT as predicted (7 new in round 2: G46-G52, G46 and G47 the verifier's V6 and V4), the unchanged copy passes |
| `extract_milestones.py --verify` / `--verify --plant` | every flag and var number, every proof's setter, trainer id and party level, look, metatile and hint word (13) against pret/pokeemerald | OVERALL PASS; with three planted wrong facts, exactly those three found |
| `run_units.py` (`2026-10-14-step5-UNITS.txt`) | the static gate and every unit suite of every step on this tree | OVERALL PASS (check_purity, test_check_purity 29, test_host 20, test_eyes 56, test_hands 57, test_world 132, test_battle 107, test_evidence 9, test_goals 59, both extractors' `--check`) |

**Determinism, not replication** (CLAUDE.md rule 8): the three live CH1 arms and the CH2 arm ran the same frames on this
tree as on round 1's (105,754 / 95,266 / 138,155 / 138,555): the whole-word hint rule changed nothing they met. Each is
one trajectory, replayed. The sweep played NEW held-out seeds (301-310), since this round's fixes were made with 201-210's
results known. In phase 2 the STOP and STOPDEAD runs met their loss at the base run's own frame: one trajectory replayed
to it, then the A/B of the loop's count.

**The full regression of steps 0-4 has NOT been run on this tree.** Round 2 changed one shared file, `skills/roam_train.py`
(its report counts how the battles a battler played ended; with no battler, build step 3, its line and record are
unchanged by construction). Checked on this tree: the step-3 ROAM plan (`rate_step3.py --plans ROAM --dev --no-reverts`,
10 seeds) gave rows and metric records IDENTICAL to `2026-10-14-step3-RATE.txt`; the step-4 WILD and CATCH plans (they
roam with the battler) gave verdict lines identical to `2026-10-14-step4-RATE.txt` (its two pooled checks FAIL on a
2-plan subset, as their bounds are sized for every plan); `revert_step3.py` W16, W19, W21, W22, W41 (the mutants in this
file) CAUGHT; all 278 mutant anchors of revert_step11/2/3/4/5 occur exactly once. The live and rate suites of steps 0-4
in full are left to the one full regression at the end. (The step-4.1 tree's `2026-10-09-*` files are still at the top
level: `prune_evidence.py --retire` was NOT applied, for the reason the first round gave.)

**How the development sweeps got there** (seeds 1-9, `step5dev1` to `step5dev5`; each fix measured, then re-swept): the
first chapter-1 run walked into PROF. BIRCH's scene link (a map change a SCENE made is no way to walk); sweep 2 reached the
POKéDEX in 3 of 9: four seeds had walked past MAY on ROUTE 103 while training and, told to find her, looked everywhere but
there (`seek`: someone seen is sought where they stood), two went up and down between OLDALE and ROUTE 101 because a walk
across a map's edge with a fade had been remembered as a WARP from a grass tile (`looks_like_exit`: a "warp" only from a
tile that looks like a way out); sweep 3 stood still under the catch-all 33 times (the starter screen and the first battle's
start, then one frame per ledge jump or map edge: named, `probe_callbacks`-measured); sweep 4 reached 9 of 9 but graded
one seed as "never trained" because the RECORDER read the rival's flag on a frame the game was moving its save blocks
(`StoryRecorder`: no sample while `gMain.vblankCallback` is NULL, and a change must be confirmed by the next sample); the
chapter-2 runs went home to MOM past OLDALE's centre (the recognised doors were not kept between runs), explored ROUTE
102's grass for the PETALBURG GYM (a building is looked for in its own town), roamed past two item balls, and gave up the
one it tried when a battle stopped the walk (a roam stops for an item ball in view; an interrupted walk is tried again);
sweep 5 (and the graded sweep) PASS. `live_step5.py`'s leftover check first counted 17 processes of OTHER projects on this
machine (a check for any `pokebot.py`): it now counts only its own profile's.

### Step 5, the verifier's round (2026-10-14)

The verifier graded the first tree `all_pass: false` on three failures and seven weak proofs. Each, what was wrong, the
fix, and what now proves it (tests in `test_goals.py`, mutants in `revert_step5.py`, sweep plans in `rate_step5.py`):

* **FAILURE: the training roam's heal-below stop was DEAD.** The roam installed `nav.battle_rest` but cleared the battle
  limit, and the navigator asked the rest only WITH a limit, so the rule never fired (the Story arm fled 8 battles in a row
  at 5/23 HP; the Trainer arm whited out twice on the walk home). Fix: the navigator asks `battle_rest` whenever it is set
  (the step-4 battle brain sets it only together with its limit, so its behaviour is unchanged by construction); the rule
  is `goals.training_rest` (under the personality's `heal_below`, or `needs_rest`), installed and cleared by
  `GoalRunner.roam_hooks`. Proof: RestTests (asked with no limit; by personality; installed and cleared), mutants G35, G36
  (the verifier's V3), G40; the sweep's REST RULE check (0 breaches over 17 occasions in CH1, and the DEADREST plan, the
  fix removed in a copy, 49 breaches over 58), the live arms' (0 over 4).
  The verifier's evidence also named the WALK HOME. Fixing the rule did not stop those whiteouts: the development sweeps
  after it (step5dev6, step5dev7) still whited out 3 times in 9, every one a wild battle met at 2-5 HP, six of them
  (DEADREST's included) on a walk home that ran out its 9,000 frames on ROUTE 101. The cause: MOM walks the player into
  the new house in a SCENE, and every scene's map change was refused as a way to walk, so the AI knew NO way home. Three
  fixes, each with its test and mutant: a scene's map change through a DOOR is that door (`route_to`, `world_distance`;
  WayTests, G42; still none from where the player merely stood, G21, G26); a heal put aside after two failures is tried
  again at once when the party is in DANGER, and nobody trains hurt (ErrandTests, G43, G44: seed 3 had then trained six
  sessions at 2/26 HP, each stopped by the rest at its first battle); on the way to heal it keeps out of the tall grass
  (`HURT_GRASS_COST`, G41). After them: 0 whiteouts in 9 (step5dev8) and 0 in 10 (graded), and the pre-registered bound
  `CH1_WHITEOUTS_MAX` 2. Whiteouts were 0 in DEADREST too once the way home was known (step5dev8): the measured effect of
  the REST rule is the roams it stops, not fewer whiteouts.
* **FAILURE: MAX_LOSSES did not bound in-goal losses, and the loss counts were false.** Only the main loop's `play_out`
  counted a loss. Fix: `mode.py` `_count_losses` at the top of every pass counts every battle the battler played and lost
  (`goals.battles_lost` over `Navigator.battle_log`), told, ending the run at `MAX_LOSSES`; `_play_end` recounted (round
  2 removed that recount: it hid a loop that had stopped counting, next section). Proof:
  LossTests, G38, G39; the sweep's ALL PLANS check, the AI's count == the GAME's (`gBattleOutcome` LOST, the new
  `StoryRecorder` battles) in 40 of 40 runs, with real losses among them (NOTRAIN 1, DEADREST 1; the development sweeps 9);
  the live arms' "its end line's losses == its log's".
* **FAILURE (minor): `prep['wild']` was always 0.** The battle's kind was read on its first frame, before the battle view
  exists. Fix: a watcher on the hands' looks takes the first battle view the battler's own looks show (it presses nothing);
  the battle record now carries its kind, outcome, start frame and the party's HP at start and end. Proof: RestTests, G37;
  the live arms' "its end line's training == its log's" (met 11 / 6 / 11 in the three CH1 arms, more than 0 required).
* **Weak: the hint-words rule was unproven at its own site.** HintTests now play a `go` whose words are unheard (no map,
  the words awaited) and a hint with NO words (headed for only once the AI has been there: a new rule, `hint_known`).
  G30 is the verifier's V2 and is caught; G31.
* **Weak: `TRAIN_SESSIONS` was untested.** ErrandTests plays one session short of the bound and at it (ready, "sessions
  roamed: no endless grind"); G33 is the verifier's V4 and is caught.
* **Weak: "wild battles before the rival" counted PROF. BIRCH's and the fled ones.** The sweep now counts wild battles
  WON between the starter's mark and the rival's flag by the GAME's outcomes (bound >= 3; 7-27 measured); the live arms
  count WON battles between the starter and rival milestones (11 / 8 / 19).
* **Weak: the NOTRAIN HP effect was confounded** (the fault also removed the heal before the fight, which waited on
  training's "ready"). Fix: under `train_off` the party is ready at once, so it heals before the fight (ErrandTests, G34).
  The comparison is PAIRED by seed: the level effect holds (+1.7, every seed 0 to +3); the HP effect does NOT (+0.04,
  reported, not bounded). The first round's 0.51 vs 0.65 was the missing heal, not the training.
* **Weak: `STORY_PATIENCE` was checked only when the player was free.** It is now checked on every pass of the loop.
  (Round 1 left it a code change read; round 2 drives the loop itself: next section.)
* **Weak: the hint data named maps the game never says** (ROUTE 102 for MOM's "PETALBURG GYM"; ROUTE 104 with no words at
  all). Read from the decomp (`PetalburgCity_Gym_Text_DadGoCollectBadges`): DAD says "Head for RUSTBORO CITY ... challenge
  the GYM LEADER, ROXANNE". ROUTE 102's step now heads for PETALBURG CITY (ROUTE 102 stays the waypoint passed on the way);
  ROUTE 104 and the woods head for RUSTBORO CITY on DAD's words; the gym's milestones on "ROXANNE". HintTests checks every
  hint's map is NAMED by what is said or is the map whose own script says it (G32 restores the verifier's case and is
  caught); `--verify` finds the 13 hint words in the decomp.
* **Weak: each live arm reads the host clock.** Unchanged: the launcher (the finished host side) has no clock pin, and the
  sweep's runs pin it. This round's live CH1 arms happened to run the same frames as the tree before (above).
* **Found by the live CH2 arm of this round, not by the verifier:** a ROUTE 102 trainer's battle took a walk to the POTION
  and its 4,000 frames; the walk ended "unreachable" and the ball was given up, so the arm FAILED its item claim on tree
  `4c99079e6160ae9b`. A battle met on a walk to an item is now an interruption (tried again, up to `ITEM_TRIES`): the
  item test and G45; the CH2 arm on this tree walked back and picked it up.

### Step 5, the verifier's round 2 (2026-10-14)

The verifier graded round 1's tree (`c3eb4fd9579e6d78`) `all_pass: true` with seven weak proofs. Each, the fix, and what
now proves it:

* **The MAX_LOSSES wiring was unproven.** Its mutant V6 (the loop's `_count_losses` call replaced by None) passed every
  test and the sweep: `_play_end` RECOUNTED the losses, so the "AI's losses == the game's" check agreed anyway, and no
  grader read the loop's told lines. Fixes: `_play_end` no longer recounts (every way out of the loop leaves it after that
  pass's count, so a recount could only hide a dead count; a disagreement is told, not mended); `PlayLoopTests` drives the
  REAL `HandsBrain._play` loop (its goal manager real; a stand-in goal runner whose every goal loses a battle) and must end
  `stuck: 3 battles lost (MAX_LOSSES 3)` after exactly three goals, each loss told "(n of at most 3)"; the graders now
  require report == TOLD losses == the game's (the sweep, every plan) and end line == log == told (the live arms). End to
  end in the game: the sweep's PHASE 2 replays every run the game recorded a loss in with MAX_LOSSES 1 (STOP: it stops at
  that loss, 682 / 679 frames after it) and with the loop's count also removed (STOPDEAD: it goes on, report 0 against the
  game's 1 / 2). Mutant G46 is V6, CAUGHT.
* **STORY_PATIENCE was untested.** `PlayLoopTests` drives the loop on a screen that never frees (a stand-in `play_out` that
  never ends it): it must end on the patience at the first pass past it, having chosen no goal; and on goals that never move
  the story. Mutant G47 is V4 (the old "only when free" rule): the loop never ends, CAUGHT by the test's frame budget.
* **The game-side training check did not tell training from none** ("won >= 3 between the starter and the rival" was met
  by NOTRAIN in 6 of 10 seeds: walks win battles too). Fix: `play_harness` now records the game's own step counter
  (GAME_STAT_STEPS) over time (`StoryRecorder.steps`, read by `steps_counted`, which takes only rises the game can make),
  and the sweep counts, INSIDE the windows the AI's log says it roamed to train (`rate_step5.training_windows`), the
  game's steps and the wild battles the game says were won. CH1 passes in 10 of 10, NOTRAIN in 0 of 10 (no window). The
  live arms count the wild battles won inside their training roams (a live run has no second path while it plays; their
  told wild battles == GAME_STAT_WILD_BATTLES over the run). The bounds (60 steps, 3 won) are round 1's, carried over; the
  kept action logs of the development and earlier graded seeds measured 110-279 steps and 5-21 won in the windows, NOTRAIN
  0 and 0. On seeds 301-310 the game counted 88-293 and 4-18 (three seeds at 4: a thin margin over 3).
* **The hint words matched substrings** ("LAB" in "available", "BAG" in "baggage", "clock" in "o'clock"). Fix:
  `goals._names` matches WHOLE words (letters, digits and the apostrophe are word characters). HintTests, G48. No live
  trajectory changed (the arms ran the same frames as round 1).
* **The goal reasons quoted the milestone's stored line**, not the page read ("MAY: Well, it's time to head back to the
  LAB." in a run whose rival was BRENDAN). Fix: the goal manager keeps the pages it READ with when (`notice`, the world
  memory's own condition) and the reason quotes the most recent page that says the words (`heard_page`, `quote`); CH1T now
  logs "We should head back to the LAB." and "Oh, BRENDAN went out to ROUTE 103 ...". HintTests, G49, G51, G52.
* **The roam report's "fled" counted every battle that ended with no stop** ("5 wild encounters, 4 fled" for 5 won).
  Fix: with a battler, `RoamReport.count` reads the navigator's record of each battle: "fled" is the battles RUN from, and
  the line and record add won, caught, lost and the trainers' battles (CH1T now: "5 wild encounters, 0 fled, 5 won").
  With no battler (step 3) the line and record are unchanged (the step-3 ROAM rows replay identically). RestTests on
  `test_world.EncounterGame` with a battler, G50.
* **The earlier suites ran only as units.** This round changed `skills/roam_train.py` only (of the shared files); its
  step-3 and step-4 consumers were replayed on this tree (the proof section above). The full regression stays at the end.

### Known limits of step 5

* **The NOTRAIN arm's predicted win-rate drop is NOT measurable here**: the rival's L5 starter is beaten untrained at the
  first try 8 times in 10 (seeds 301-310; 9 in 10 on 201-210), trained 10 of 10. The training's effect is graded on the
  fight's margin instead: the strongest level at the rival's flag, paired by seed (+1.1 on 301-310, +1.7 on 201-210). The
  HP the fight left shows no clear effect once both arms heal before the fight (+0.10 and +0.04, reported). A real
  win-rate effect needs a harder fight (the ROUTE 102 trainers, ROXANNE).
* **`STORY_PATIENCE` on a screen that never frees** is proven through the real loop with a stand-in screen
  (`PlayLoopTests`, G47); no live or sweep run has met such a screen.
* **`MAX_LOSSES` 3 itself** has not been reached by an unaltered run (whiteouts are rare: none in the CH1 seeds since the
  way home was found). The stop is proven through the real loop (`PlayLoopTests`, G46), and end to end in the game at a
  cap of 1 (the sweep's STOP plan; STOPDEAD, the loop's count removed, does not stop).
* **Chapters 3 and 4 are DATA only**: their milestones, proofs, hints and fight levels are extracted and verified, but no
  run plays them; `AI_PLAYER_TARGET=ch4_roxanne` is accepted and untested.
* **The live arms run on the HOST clock** (the cartridge reads it in a launcher run): each is one trajectory, not
  replayable; the sweep's runs pin the clock and replay (`play_harness.py --game-clock`). Identical numbers between two
  development sweeps of unchanged chapter-1 code are a determinism check, never a replication.
* **Chapter 2 is one live run** (the stretch) plus four development runs; the only item ball picked up in any of them is
  the ROUTE 102 POTION (one per run, in the runs that picked one up), so "an item picked up" rests on that one ball.
* **The long errands are slow, not stuck**: a `go` across ROUTE 102 often runs out its 9,000 frames to its battles and is
  chosen again; before a POKéMON CENTER is known, a heal is a walk home to MOM. A whiteout is still possible on such a
  walk (a single battle can take a party from above `heal_below` to a few HP): 0 in the 19 chapter-1 seeds since the way
  home was found, 3 in 9 before.
* **The milestone marks are a memory read** of the game's own flags (the eyes' abstraction of "a person knows the story
  moved on"); the hints are only the words the game itself says, and with `AI_PLAYER_FAULT_NO_HINTS` the AI does not
  find its way (the NOHINTS sweep).
* The FAVOURITE Pokemon is drawn and logged; the shiny hunt is deferred.

## The battles (build step 4)

The AI's OWN battles (design draft §2.3 "battle decider", §10.1; HUMAN-PLAY-DESIGN pillar 3). RULING 35: the bot's
`modules/battle_strategies/*`, `battle_handler.py`, `battle_action_selection.py`, `battle_move_replacing.py` and `story/*`
were read as TEACHING material only; the purity gate refuses every one of them, and `test_battle.py`
`FrameworkFreeTests` checks no AI file even names them. The bot's DATA taught the game's FACTS, extracted into the AI's
own files with provenance.

### What it knows: `knowledge/`, and how that was checked

`gates/extract_knowledge.py` reads the bot's `sandbox-pokebot/modules/data/{types,moves,species}.json` (never its code)
and writes `knowledge/{types,moves,species}.json`, each naming its source file and that file's sha256 (`--check`: a written
file differs from a fresh extraction -> exit 1). Learnsets, evolutions, encounter tables and trainer parties are left out
ON PURPOSE: a person meets those by playing. `gates/verify_knowledge.py` then reads the GAME's own source through `gh api
repos/pret/pokeemerald/contents/...` and compares EVERY entry: the chart against `src/battle_main.c` gTypeEffectiveness
(112 triples, and every pair the decomp does not list must be 1.0 in ours), all 354 moves (type, power, accuracy, PP,
effect, priority, target) against `src/data/battle_moves.h`, all 386 species (types, six base stats, catch rate,
experience yield) against `src/data/pokemon/species_info.h`, and the recoil arithmetic against the decomp's own lines
(`src/battle_script_commands.c`: 1/4 and 1/3 of the HP dealt; Jump Kick's miss recoil is half the damage it would have
dealt, capped at half the TARGET's max HP; Explosion faints the user). Its fault half `--plant` changes three facts in
memory and must report exactly those three. Evidence `evidence/2026-10-08-step4-KNOWLEDGE.txt` and `-KNOWLEDGEX.txt`.

### The decider: `brain/battle.py`

* A move's WORTH against this foe (`move_value`): type effectiveness x STAB (1.5) x power x hit chance, minus a RECOIL
  penalty in the same units (`recoil_penalty`: the recoil's share of the worth, Take Down 1/4, Double-Edge 1/3, weighted
  0.5 + 2.5 x (1 - its HP share), so the same Take Down costs five times more at 20 % HP than at full; Jump Kick's miss
  recoil charged at its miss chance on half the worth it would have had; a self-KO move charged its whole worth). Since
  the step-4 verifier's round the recoil is charged on what the hit can actually TAKE (`recoil_risk`, from the damage
  estimate): a hit takes at most what the foe's bar has left (the game: `Cmd_datahpupdate` caps gHpDealt at the target's
  HP, and the recoil is gHpDealt / 4 or / 3), Jump Kick's miss recoil is capped at half the target's max HP, and a recoil
  that would knock the user out (in HP, against its HP left) costs the move's whole worth. Measured: against the recorded
  15-HP Poochyena the recoil is 3.75 HP by the estimate and 3 by the game (74 -> 71); step 4 charged 21.6 of 76.5 worth.
  A STATUS move is worth 0 in a fight: never chosen by habit, only when nothing that hurts has PP.
* Not a machine: among the moves within its personality's `near_best` share of the best, a seeded value-weighted draw
  (`choose_move`); a clearly better move is chosen every time.
* SWITCH when badly matched and a healthy member is MUCH better against this foe (`matchup`, with a level factor), never
  when its Pokemon outlevels the foe by `OUTLEVELS` (5), at most `MAX_SWITCHES` a battle, never back and forth.
* HEAL with a Potion-like item only in a TRAINER's battle, when its Pokemon is under its temperament's `heal_below` and
  the foe is not about to fall, at most `MAX_HEALS`.
* RUN from a wild battle: training, when its Pokemon is low (`run_low`) and the foe is not, or the foe is 6+ levels above;
  travelling, by its temperament (`run_travel`). Never from a trainer.
* CATCH a species the Pokedex does not OWN, when its personality wants it (one seeded draw per species per run, `catch_new`):
  WEAKEN with the strongest move that cannot knock the foe out at its best damage roll (the bar must keep `KO_MARGIN`, 8 %;
  the damage is a Gen-3 formula estimate on average stats, calibrated by what its last hit took off the bar; since step 4.1
  a rough eighth, and since round 3 the FOE a typical Pokemon of its level, not its species), then THROW:
  a Poke Ball for an easy catch, a Great Ball for a hard one or after two misses, at most `MAX_THROWS`.
* Its questions by their WORDS (`answer`): "Use next POKéMON?" yes while one can fight; "Will ... change POKéMON?" by the
  switch rule; a nickname no; learning a move by `learn_choice` (keep the four worth most to that Pokemon, a new move must
  be worth 15 % and 5 points more than the weakest; an HM is never forgotten).
* After a faint, who goes in (`replacement`): the healthy member best matched against the foe(s) still standing (the
  `matchup` score, its mean over a double battle's two foes, scaled by its HP share), by PID, never one ON THE FIELD. The
  party menu covers the battle and its look carries NO battle view (the eyes read one only in game state BATTLE), so the
  decider REMEMBERS the field from its last look at the battle (`see`: who stands there, whom it faces), whom it sent in
  since the turn began (`sent`: a double battle that lost both opens the party menu twice before any look shows the first
  one there) and whom the game refused (`refuse`), and says so ("Taillow L6 (11/21 HP) is the best left against Shroomish
  (the field REMEMBERED from the last look at the battle: the party menu covers it)"). Until the verifier's round that look
  alone was used: in a double battle the partner fainted and the Grovyle standing on the field was sent in (the game
  refused it, and the battle stuck), and every single battle's replacement was ranked by level and HP only.
* A DOUBLE battle (`_fight_double`): every (move, foe) pair valued against that foe, a spread move halved (Gen 3:
  `CalculateBaseDamage`), and the move aimed at the foe it hurts most. No switching, healing, catching or running there.
* When training should stop (`needs_rest`): its strongest Pokemon fainted or under a third of its HP, or the party under a
  third in all; the battle brain then ends with `rest:` (step 5's goals take it to a Pokemon Center).

### The hands in a battle: `skills/battle.py` and the eyes' new reads

The eyes now see the MOVE grid, a double battle's TARGET choice and the battle's YES/NO (the controller function of the
battler whose turn it is, NAMED through `get_symbol_name`, and its cursor), the level-up stats box and other key waits of
the battle script, the evolution scene's and the summary screen's forget-a-move states, the bag's items by pocket, the
party menu's actions, each party Pokemon's stats, each battler's PID and position (`host/eyes.py` module docstring: BUILD
STEP 4; no new door). The skill advances every text only on a wait, chooses every option by reading the cursor, logs every
decision with its reason and the values it weighed (`[AI-HANDS] battle: turn 1: fight Absorb: ... [Fury Cutter: 10.0 = x0.5
type ...]`), and reports the game's own outcome. Every loop is bounded (`BATTLE_STEPS` menus, `TEXT_BUDGET` frames a
stretch of text, `ITEM_STEPS` presses in the bag, `SEND_IN_TRIES` choices in the party menu). Since the verifier's round
the skill shows the decider every look it takes (a watcher, `BattleMind.see`), and when the game still REFUSES a choice in
the party menu ("GROVYLE is already in battle!", "CASTFORM has no energy left to battle!": text printer 6, a WAIT over a
party list that takes no input) it READS the words (`_read_message`: the reading delay, then A on the look's wait), tells
the decider who was refused (the member it chose, or the one under the menu's cursor when the battle was resumed on the
message, checked against the name the words begin with) and chooses again; a refused SWITCH goes back to the battle's menu
with B. Until then the skill watched that message for `MENU_SETTLE_BUDGET` frames and gave up. (`gates/live_step2.py`
`classify_a` now counts an A on a wait over a BUSY menu, `ui=party(busy)[`, as a wait: the game's A goes to the text.)

### The proof

**Live, through the real launcher** (`gates/live_step4.py`, every arm graded on PURITY (CLEAN, every breach counter 0,
`ai_presses` == 2 x the pad's presses, the pad's frames == `real_frames`, `ai_bot_calls` 0), the HANDS (every press gated,
every A a wait, a menu confirm on its look or a talk, no catch-all idle) and THE GAME by a second path from the state the
run left (`hands_harness.py truth`: party by PID, OT ids, `gBattleOutcome`, defeated flags, battle counters); the
in-battle arms' frames and presses PRE-REGISTERED from a development run and machine-checked). Since the verifier's round
every arm that starts IN a battle (TYPE, TYPEX, FAINT, DFAINT, DFAINTX, REFUSE) is also REPLAYED in-process from the same
fixture, seed and faults with the GAME's battle read after every frame (`hands_harness.py --battle-log`: each battler's
chosen move, each HP change with its user, move and target, each Pokemon that came onto a position); the replay counts only
when its frames and presses equal the launcher's (one trajectory, replayed: CLAUDE.md rule 8), and the moves and send-ins
are then graded from the game's record. Evidence `evidence/2026-10-08-step4-<ARM>.txt`:

| arm | fixture, seed | what the game says (second path) |
|---|---|---|
| WILD | `route101_south.ss1`, Story, seed 3, 4 battles | `battles: 4 played: ['won', 'won', 'caught', 'won']`; the Mudkip (PID 550a9be6) 418 -> 463 experience, L8 -> L9; the game's wild-battle count +4 == the battles played; FIGHT chosen 8 times |
| CATCH | the same, Catcher, 1 battle | `gBattleOutcome` 7; ONE new PID (04016319) with the player's id 22640; Poke Balls 5 -> 4 == 1 thrown; first "to CATCH Poochyena: weaken it first (Tackle takes 66%-78% of its HP and its bar is at 100%: it cannot knock it out)" |
| TRAINER | `trainer_battle_r116.ss1` (Joey just begun) | won; Joey's flag 322 False -> True; Grovyle 2545 -> 2714 experience; 3811 frames, 14 presses as pre-registered |
| RIVAL | `rival_r103.ss1`, seed 5 (CHOSEN: a won seed, see the limits) | won; DEFEATED_RIVAL_ROUTE103 and May's flag 529 False -> True; 6103 frames, 21 presses as pre-registered |
| CHALLENGE | `route103.ss1`, seed 1, `AI_PLAYER_TALK_TO=10,3` | the AI walked up to May and TALKED (one talk A), the trainer-battle count +1, the battle played to its end: LOST, and the game agrees (the rival flag still clear); the run ends `stuck: the battle was lost` |
| TYPE | `geodude_grovyle.ss1` (a DOUBLE battle: a Geodude and a Shroomish against Grovyle and Nincada) | Grovyle's first move ABSORB aimed at the Geodude (worth 120 against Pursuit 40, Quick Attack 20); BY THE GAME (the replay, 11458 frames and 48 presses == the launcher's): `Grovyle's first hit [('Grovyle', 'Absorb', 'Geodude')] is ABSORB on the Geodude, and every hit it landed on the Geodude was Absorb`; won, CLARK 631 and JOHNSON 754 set |
| TYPEX | the same, `AI_PLAYER_FAULT_IGNORE_TYPES=1` | its first move Quick Attack at the Shroomish; Absorb never aimed at the Geodude (Pursuit was); no x4 or x0.5 in its told values; BY THE GAME: `Absorb never hit the Geodude: [('Grovyle', 'Quick Attack', 'Shroomish'), ('Grovyle', 'Pursuit', 'Geodude'), ...]`; purity still CLEAN |
| FAINT | `faint_r116.ss1` (Karen just begun), seed 1 | the Mudkip's HP 0 by the second path; `Taillow L6 (11/21 HP) is the best left against Shroomish (the field REMEMBERED from the last look at the battle: the party menu covers it)` (Flying against Grass; step 4 sent the full Nincada, ranked by level and HP), the party cursor read down to slot 4, SEND OUT; BY THE GAME: `after the Mudkip's HP 0 at position 0, [(0, 'Taillow', 'ae39815d')] came onto it == the decider's choice`; won, Karen's flag 280 set; 9503 frames, 30 presses (re-registered: 11113 / 28 with the Nincada) |
| LEARN | `learn_r116.ss1`, seed 1 | the Mudkip 1978 -> 2036 experience, L14 -> L15; moves now Tackle, BIDE, Mud-slap, Water Gun ("Bide (40) is worth clearly more than Growl (4)"); the forget list's cursor read onto GROWL; 3918 frames, 19 presses |
| DFAINT | `geodude_grovyle.ss1`, seed 6, `AI_PLAYER_FAULT_IGNORE_TYPES=1` (the verifier's own reproduction: the types fault only makes the PARTNER Nincada fall; the replacement rule is the real one) | `Skitty L8 (27/27 HP) is the best left against Geodude and Lotad; not Grovyle on the field (the field REMEMBERED ...)`; the game refused nothing; BY THE GAME: `the Nincada's HP 0 at position 2, then [(2, 'Skitty', '7f7652d1')] came onto position 2 while [('550a9be6', 37, 'Grovyle')] stood at position 0`; WON (631, 754 set); 17536 frames, 95 presses |
| DFAINTX | the same with `AI_PLAYER_FAULT_FORGET_FIELD=1 AI_PLAYER_FAULT_IGNORE_REFUSAL=1` (the step-4 code) | `Grovyle L17 (37/49 HP) is the best left (no foe standing: by level) (no battle view: the field unknown)`, then `stuck: the battle: no Pokemon could be sent in`: the verifier's bug through the real launcher; BY THE GAME: nobody came onto the field; purity CLEAN |
| REFUSE | `tools/story-dev/saves/ki17_partymenu_wedge.ss1` (the story bot's KI-17 wedge: saved ON the battle party menu's "SKITTY is already in battle!", Mauville's gym), seed 1 | `the party says 'SKITTY is already in battle!': Skitty (5cccd8be) cannot go in`; ONE A on `text printer 6 WAIT` over `ui=party(busy)[0]`; `Mightyena L20 (60/60 HP) is the best left ...; not 5cccd8be refused`; BY THE GAME: `[(2, 'Mightyena', '5c96ea9b')] came onto the field`; WON (`gBattleOutcome` 1); 10182 frames, 52 presses |

Every arm PASS, its purity CLEAN (`ai_bot_calls` 0: the bot's battle code never ran) and every press gated; 34 of 34
pre-registered numbers held; no emulator left running. The in-battle arms replay exactly (the game reads no clock in a
battle); WILD, CATCH and CHALLENGE walk the overworld, where the host clock matters, so only their claims were registered.
`CHALLENGE` proves the walk, the talk and a battle played to its end, not a win. `TYPE` shows ONE decision ("Absorb is
clearly the best") replayed; the type chart's evidence is the A/B with TYPEX and the sweep's TYPE-FAULT.

**The seed sweep** (`gates/rate_step4.py`, in-process, the cartridge's clock pinned, seeds 1-10 unless named; evidence
`evidence/2026-10-08-step4-RATE.txt`). Since the verifier's round every run is read by TWO second paths, the end state
(`truth`) and the GAME's own battle each frame (`--battle-log`); the AI's told lines only cross-check (what it said it chose
against what the game did); each verdict names the path it rests on; and EVERY run of every plan must end by itself (a
lost battle counts as ended), except the two fault plans whose prediction is the stuck end (`ENDED: 150 of 150`):

| plan | result over seeds (the path) | bound |
|---|---|---|
| TYPE | BY THE GAME (`gChosenMoveByBattler[0]`, the first hit's target): Absorb at the Geodude in **10 of 10**, the told move agrees in every seed, every battle won. ONE decision ("clearly the best") replayed: not a chance argument | 10 of 10 |
| TYPE-FAULT (types ignored, 30 seeds) | BY THE GAME: Absorb at the Geodude in **0 of 30**; every battle ended by itself (the verifier found seed 6 STUCK here) | 0 |
| TYPE / TYPE-FAULT DOUBLE-FAINT | BY THE GAME (who came onto the player's positions after a faint): the partner fell in 0 of 10 / **2 of 30** seeds (6 and 23); in both the Pokemon the decider NAMED came in (Skitty, never the Grovyle standing beside it), the game refused nothing, the battle ended by itself | all |
| FIELD-FAULT (the field forgotten, 30 seeds) | the game REFUSED the one on the field in **seeds 6 and 23**, the AI read the words and another came in; every battle ended by itself | all end |
| FIELD-STEP4 (field forgotten + refusal ignored: the step-4 code, 30 seeds) | `the battle: no Pokemon could be sent in` in **seeds [6, 23], exactly the seeds FIELD-FAULT was refused in**: the verifier's stuck battle reproduced, and each layer of the fix alone ends it | as FIELD-FAULT |
| RECOIL (`ch13_r119_wedge.ss1`: Marshtomp L32 74/99 with Take Down against a 15-HP Poochyena) | BY THE GAME: Take Down **10 of 10**; the recoil the game charged `[3] HP` (a quarter of the 15 the hit could take) | >= 9 |
| RECOIL-FAULT (`uncapped_recoil`, the step-4 rule: the recoil of the whole worth, 21.6 of 76.5) | BY THE GAME: Take Down **2 of 10** (54.9 against Water Gun's 60) | <= 5 |
| WILD (4 battles each) | BY THE TRUTH: **10 of 10** runs won a wild battle by fighting and raised the Mudkip's experience; the game counted 4 wild battles in each | 10 of 10 |
| CATCH | BY THE TRUTH (`gBattleOutcome` 7, ONE new PID with the player's OT): **9 of 10** caught; balls spent per seed `[1, 1, 1, 1, 1, 1, 1, 1, 0, 4]` (seed 10 needed 4; step 4's README said "one ball each": wrong); seed 9's Wurmple fell to the weakening Tackle the decider judged safe at 48-56 %: "A critical hit!" | >= 8, the rest a weakening KO |
| TRAINER | BY THE TRUTH: **10 of 10** won, Joey's flag set | 10 of 10 |
| RIVAL | BY THE TRUTH: WIN RATE **2 of 10** (seeds 5 and 10); every battle played to its end (outcome 1 or 2) | reported |
| FAINT | BY THE GAME: the lead fainted in 6 of 10 seeds; in **6 of 6** the Pokemon the decider named (Taillow, "against" the Shroomish it remembered) came onto battler 0, and the battle went on to its end (won) | all |
| LEARN (5 seeds) | BY THE TRUTH: **5 of 5**: Bide learned, Growl forgotten | all |
| REFUSE (5 seeds, `ki17_partymenu_wedge.ss1`) | BY THE GAME: in every seed the words read (A on their wait), Mightyena came onto the field by its PID, nothing else refused, won | all |
| REFUSE-FAULT (`ignore_refusal`, the step-4 skill) | `the party on screen neither took input nor closed` in **5 of 5** | all |

**Unit tests** (`gates/test_battle.py`, 80): the eyes' new reads on recorded task data, the knowledge files, a move's worth,
the type chart and its fault, the recoil rule at every HP share, the near-best draw, the catch (no weakening move that could
knock it out, the ball, the bound), switching, running, healing, the questions, learning, a double battle's aim and spread,
and the skill on a screen model (both grids read, a ball from the ball pocket, a switch by PID through SHIFT, the yes/no on
the option wanted), each with a fault half. Since the verifier's round: RECOIL on the RECORDED look of a real battle
(`fixtures/recoil_r102.look.json`, the 15-HP Poochyena) through the decider's own valuation: its recoil 3.75 HP, Take Down at
full HP and at 20 %, NEVER at 3 HP (the recoil would faint the Marshtomp); FAULTS: the step-4 rule never at 20 %, the
recoil ignored at 3 HP; a sturdy Taillow: the whole hit lands and Water Gun at 20 %; Jump Kick's miss recoil capped at half
the target's max HP; a recoil that would faint the user costs the whole worth. `FieldTests` on the look the live party
menu actually gives (no battle view, `party_menu`): a double battle's partner falls and the Grovyle still standing is not
sent (FAULT `forget_field`: it is, the verifier's bug); a single battle's replacement against the remembered foe (Taillow;
FAULT: the Nincada by level and HP); both fell: the second choice is not the first; a refused member not chosen again until
the next turn. `SkillTests` on the screen model, whose party menu now REFUSES a Pokemon on the field (printer 6, a WAIT):
the field remembered through the party menu (nothing refused); FAULT `forget_field`: refused, the words read, A on the
wait, another goes in; FAULTS `forget_field` + `ignore_refusal`: `the battle: no Pokemon could be sent in`; both fell: two
menus, two different Pokemon, nothing refused; a battle resumed ON the refusal: the cursor's member refused (one message
only), the other sent (FAULT `ignore_refusal`: `neither took input nor closed`).

**Mutants** (`gates/revert_step4.py`, evidence `evidence/2026-10-08-step4-REVERT.txt`): 30 rules of the real code, each
broken alone in a copy of the package (B1 the type chart ignored, B2 no STAB, B3 no recoil penalty, B4 a penalty that does
not grow as HP falls, B5 a status move valued like a damaging one, B6 no near-best draw, B7 no KO check while weakening,
B8 never a better ball, B9 no bound on throws, B10 every wild species counted new, B11 no level guard on switching, B12 a
switch in a double battle, B13 a fainted Pokemon sent in, B14 training never runs, B15 healing in any battle, B16 "Use next
POKéMON?" always no, B17 no learning margin, B18 an HM forgettable, B19 a double battle aimed at the last foe, B20 no spread
halving, B21 a grid's A on any cursor, B22 the party member by slot not PID, B23 the bag's pocket not switched, B24 every
yes/no on YES, B25 the party list taking input whatever task runs, B26 / B27 the level-up box and the caught Pokemon's dex
page not waits, B28 a grid's waiting frames counted as presses, B29 training on with its strongest fainted, B30 a dual
type's second type ignored); and since the verifier's round B31 the field not remembered (the step-4 bug), B32 the party
menu's refusal not read, B33 the decider forgets whom it sent in, B34 the skill does not tell it, B35 a refused member
chosen again, B36 the recoil charged on the whole hit though the foe has less left, B37 Jump Kick's miss recoil not capped,
B38 a recoil that would faint the user not charged as such, B39 a refusal on screen before any choice not told to the
decider, B40 refusals never forgotten at a new turn, B41 the skill not showing the decider its looks: **41 of 41 CAUGHT** by
their predicted tests, and the unchanged copy passes all 80. (B15 was NOT caught at first in step 4: the wild half of its
test met a Mudkip so low that training ran before any heal was weighed; the test now puts the foe's bar where only the
battle's KIND keeps the Potion in the bag, with a trainer twin that does heal. B39 was NOT caught at first in this round:
the unit test's Skitty at 40/52 lost to the Mightyena by level and HP even unrefused; the test now gives it full HP, so only
the refusal keeps it out.)

**Everything on ONE tree, `sha256:a14d81a107a65b76`** (the step-4 verifier's round; `gates/provenance.py`;
`--check-evidence`: `114 evidence files at the top of evidence/; 114 name this tree's digest a14d81a107a65b76; other: 0 [] ->
PASS`): `check_purity.py` PASS; `test_check_purity` 29, `test_host` 20, `test_eyes` 56, `test_hands` 56, `test_world` 111,
`test_battle` 80, all OK (`evidence/2026-10-08-step4-UNITS.txt`); `extract_knowledge.py --check` up to date;
`verify_knowledge.py` (112 gTypeEffectiveness triples, 354 moves, 386 species, the recoil lines: 0 mismatches) and its plant
(exactly the 3 planted) PASS; `live_step0.py --arms A,A2,B,C`, `live_step1.py` (21 arms), `live_step2.py` and its seed-9 replication,
`live_step3.py` (34 arms, 162 of 162 pre-registered numbers held: this round moved no step-3 trajectory), `rate_step3.py`
(100 of 100 as intended, every bound and revert prediction held), `revert_step3.py` (76 caught, W13 redundant alone, of
77), `revert_step2.py` (39 caught, 5 redundant alone, of 44), `revert_step11.py`, `live_step4.py` (12 arms, 34 of 34
pre-registered numbers), `rate_step4.py` (18 of 18), `revert_step4.py` (41 of 41): every one PASS, no emulator left
running, `git status -- sandbox-pokebot` empty. (Build step 4's own runs, tree `sha256:83a4581da76e0739`, are in
`evidence/archive/83a4581da76e0739/`, but for two files this round's development runs wrote over before they were archived:
`evidence/archive/README.md` says which.)

### Step 4, the verifier's round (2026-10-08)

The step-4 verifier found two FAILURES and twelve weak proofs. Each fix is in the AI's code or in a grader, each with a
test that fails on its revert (`revert_step4.py` B31-B41, `revert_step3.py` W76-W78) and, where it can be played, a live arm
or a sweep plan; the numbers were pre-registered from development runs of this code before the graded runs above.

| the verifier said | the fix | proven by (final tree) |
|---|---|---|
| FAILURE: "in a DOUBLE battle, when the partner faints, the AI sends in the Pokemon that is already on the field, and the battle gets stuck ... `replacement()` excludes `look.battle.own`, but the party-menu look has no battle view" (TYPE-FAULT seed 6) | `brain/battle.py`: the decider REMEMBERS the field from its last look at the battle (`see`, shown every look by the skill), whom it sent in (`sent`) and whom the game refused (`refuse`); `replacement` excludes them all. `skills/battle.py`: a refusal on screen is READ (A on its wait) and another is chosen (`SEND_IN_TRIES`), so a refusal can no longer strand a battle | live DFAINT (Skitty in, the game shows it at position 2 beside the standing Grovyle, won) and DFAINTX (the step-4 code: stuck, as found); live REFUSE (resumed on the story bot's own refusal wedge: read, Mightyena in, won); RATE DOUBLE-FAINT (seeds 6 and 23 of 30), FIELD-FAULT (refused, read, ended), FIELD-STEP4 (stuck in exactly those seeds), REFUSE 5 of 5 and its fault 5 of 5 stuck; FieldTests, SkillTests; B31-B35, B39-B41 |
| FAILURE: "the README says 'After a faint, who goes in: the healthy member best matched against the foe' ... The look at the party menu has no battle view, so `replacement` ranks by level x HP share only"; the unit test passed a look WITH a foe, "a screen the live party menu never shows" | the same memory: the replacement is ranked against the foe(s) REMEMBERED, and its reason says so; the unit tests now use the party-menu look the live game gives (`party_menu`: no battle view) | live FAINT: `Taillow L6 (11/21 HP) is the best left against Shroomish (the field REMEMBERED ...)`, the game shows the Taillow come in (step 4 sent the Nincada); RATE FAINT 6 of 6; `FieldTests.test_a_single_battles_replacement_is_matched_against_the_remembered_foe` (FAULT: the Nincada) |
| "the new CYCLE check (`laps`) does not tell the fix from the revert"; "steps-vs-shortest is measured per DECISION ... near 0 by construction" | RINGS (graded) and JOURNEYS (reported): "Step 3.2, the step-4 verifier's weak proofs" | there |
| finding 4 "only partly fixed: targets still churn"; findings 3 and 5 "proven only by unit tests and mutants"; SCENE-EXPLORE's reversals "2.91 per 100 steps" | stated, not changed (there, and in "Known limits of step 3"); FIXED in the second round below | there |
| "TYPE, 'by chance ... P = 9.31e-10': ... one deterministic decision replayed 10 times (CLAUDE.md rule 8) ... The valid evidence is the fault A/B" | the chance figure is gone from `rate_step4.py` and this README; TYPE says it is one decision replayed, and the A/B is TYPE 10 of 10 against TYPE-FAULT 0 of 30, by the game | RATE `TYPE A/B (by the game): Absorb at the Geodude REAL 10 of 10, FAULT 0 of 30` |
| "rate_step4's docstring claims each run graded by its SECOND-PATH truth ... In fact TYPE, TYPE-FAULT, RECOIL, RECOIL-FAULT, RIVAL and FAINT are graded from the AI's own told lines ... `ended_by_itself` is not applied to the TYPE or RECOIL plans" | `hands_harness.py --battle-log` (`BattleRecorder`: the game's battle read each frame, test side); every plan graded by the game or the truth, each verdict naming its path, the told lines only cross-checked; `ENDED` on every plan | RATE `ENDED ... 150 of 150`; every verdict line begins `BY THE GAME` or `BY THE TRUTH` |
| "Live arms TYPE and TYPEX grade the move choice only from the AI's told lines; live_step4 makes no game read of the move or its target" | THE REPLAY (`live_step4.py`): the in-battle arms replayed in-process with the battle log, counted only when frames and presses equal the launcher's | TYPE `BY THE GAME (the replay): Grovyle's first hit [('Grovyle', 'Absorb', 'Geodude')]`; TYPEX `Absorb never hit the Geodude` |
| "`recoil_penalty` charges the fraction of the move's WORTH, not of the HP actually dealt (no cap at the foe's remaining HP), and it ignores the Jump Kick cap stored in moves.json. On the 15-HP Poochyena the real recoil was 3 HP, while the AI charged 21.5 of 76.5 worth" | `recoil_risk`: the recoil on what the hit can take (at most the foe's bar), Jump Kick's miss recoil capped at half the target's max HP (`MoveFact.recoil_capped`), a recoil that would faint the user = the whole worth. The RECOIL plan's A/B is now the cap: the real decider against the step-4 rule (`uncapped_recoil`) | RATE RECOIL `Take Down in 10 of 10 ... the recoil the GAME charged for it [3] HP`, RECOIL-FAULT `2 of 10`; RecordedRecoilTests (never at 3 HP; the step-4 rule never at 20 %), RecoilTests; B36-B38 |
| "README step-4 CATCH row says '9 of 10 caught (one ball each)', but ... seed 10 used 4 balls" | corrected | RATE `balls spent per seed [1, 1, 1, 1, 1, 1, 1, 1, 0, 4]` |
| "I did NOT re-run the launcher drivers (live_step0 to live_step4)" | all re-run on the final tree | "Everything on ONE tree" above |

Two things this round did not do: no fixture loses BOTH battlers of a double battle in one turn (the second party menu is
unit-tested only), and the refused-SWITCH path (B back to the battle's menu) is reached by no test (Known limits below).

### Step 4, the verifier's second round (2026-10-09)

The re-run found every step-4 arm holding by its own reads, and these weak proofs; each is answered in code or a grader, or
said to be not done:

| the verifier said | what changed | proven by (final tree) |
|---|---|---|
| "TYPE 'rate across seeds' is not a rate. The first decision is deterministic ... one counterfactual A/B replayed ... Only one matchup is played live" | every choice of the best move now TELLS what the type chart changed in it (`brain/battle.py` TypeSay: the moves about as good WITH the chart, the best with NO types, the moves that attack; DECISIVE when the type-blind best is not about as good with the chart), and the sweep's TYPE-DECISIONS pairs EVERY such choice of every turn of every battle with the move the GAME shows chosen that turn (`gChosenMoveByBattler`, cleared at every turn's end) | `rate_step4.py` TYPE-DECISIONS (the graded numbers: "Everything on ONE tree" below); `TypeTests.test_the_choice_says_what_the_type_chart_changed`, mutant B43. Still a rate over few MATCHUPS: the saves give few battles where the chart turns the strongest move into a poor one, and none was made |
| RECOIL's live A/B "covers only the cap"; low HP, Jump Kick's miss cap and the self-faint rule "have no live arm" | not done: no fixture has a recoil move at low HP (Known limits) | unit tests and mutants B36-B38, as before |
| "both battlers fainting in one turn and the refused-SWITCH B path ... and healing" have no live arm | the refused SWITCH now has a unit test on the screen model (the words read, the decider told, B on the party menu's look, then FIGHT; FAULT `ignore_refusal`); both-fainting and healing: not done live (Known limits) | `SkillTests.test_a_refused_switch_goes_back_to_the_battles_menu_and_fights`, mutant B42 |
| "'Train to roughly the gym leader's level before challenging' is neither implemented nor named as deferred" | named as NOT BUILT, with what exists and what step 5 adds (Known limits, first bullet) | this README |
| evidence hygiene: two files of an earlier tree lost | a subset run of `revert_step3.py` no longer writes into `evidence/`; the round's predecessor archived first | `evidence/archive/README.md` |
| "My re-runs of the in-process sweeps ... are determinism replays, not replications" | both sweeps take `--first-seed`: seeds 1.. are the development seeds (each sweep's header now says the graded run REPLAYS them), seeds from 101 are HELD OUT, graded by the same pre-registered bounds | the two held-out files below; what did not replicate is said there |

**Everything on ONE tree, `sha256:7b4322c9ac0df2e1`** (the step-4 verifier's second round; `gates/provenance.py`;
`--check-evidence` over the evidence folder, quoted in the round's report): `check_purity.py` PASS; `test_check_purity` 29,
`test_host` 20, `test_eyes` 56, `test_hands` 56, `test_world` 122, `test_battle` 82, all OK (`evidence/2026-10-09-step4-UNITS.txt`);
`extract_knowledge.py --check` up to date; `verify_knowledge.py` 0 mismatches and its plant (exactly the 3 planted) PASS;
`live_step0.py --arms A,A2,B,C` (4 arms), `live_step1.py` (21 arms), `live_step2.py` (17 arms) and its seed-9 replication;
`live_step3.py` (39 arms, 214 of 214 pre-registered numbers held); `rate_step3.py` (100 of 100 as intended, every bound and
every revert prediction held, CHURN A/B "DECISIONS REVERTED 1471 ... REAL 629 ... ONE-STEP WALKS REVERTED 965 of 1429, REAL
145 of 618 ... plans over the bounds when reverted 5 of 5 ... steps REVERTED 2934, REAL 2997 ... every journey's share beyond
REVERTED 0.29 ..., REAL 0.27 -> the prediction HELD"); `revert_step3.py` (87 caught, W13 redundant alone, of 88);
`revert_step2.py` (39 caught, 5 redundant alone, of 44); `revert_step11.py`; `live_step4.py` (12 arms, 34 of 34 pre-registered
numbers); `rate_step4.py` (19 of 19: TYPE-DECISIONS "of 391 choices of the best move over 95 runs of the real plans, 81 were
DECISIVE ... 4 distinct matchups ... the GAME shows a move of the chart's near-best set chosen in 81 (100%) ... a type-blind
random pick ... 38%"; the type-blind plans 0 of 843); `revert_step4.py` (43 of 43): every one PASS, no emulator left running,
`git status -- sandbox-pokebot` empty.

THE GRADED SWEEPS REPLAY THEIR DEVELOPMENT PASSES (seeds 1-10 are the seeds the bounds were registered from, and the final
code plays them identically: CLAUDE.md rule 8). The REPLICATIONS are the HELD-OUT sweeps, seeds 101-110 (101-130 where a plan
runs 30), on the same tree, and both files say FAIL. Said here, not loosened:
* `2026-10-09-step3-RATE-SEEDS101-110.txt`: 100 of 100 runs as intended; THIS ROUND'S CLAIMS REPLICATED: the CHURN bounds on
  every plan and the CHURN A/B ("DECISIONS REVERTED 1389 ..., REAL 581 ... ONE-STEP WALKS REVERTED 912 of 1347, REAL 125 of
  575 ... 5 of 5 ... every journey's share beyond REVERTED 0.29, REAL 0.28 -> HELD"), LAP RINGS 0 (bound 4), SCENE-EXPLORE's
  bounds (3.25 reversals per 100, bound 3.5; journeys 0.35, bound 0.45), SCENE-WORDS, SCENE-NEWS (10 of 10 reach Route 101),
  LAPS. THREE OLDER PREDICTIONS DID NOT: (1) the per-run reversal bound (2) on TOWN seed 102, 3 reversals, each A -> B -> A on
  the town's open ground: one walks to a personality DETOUR two tiles off the way and back (`Navigator._detour`, drawn for the
  decision and kept when it carried on), the other two step aside and back on the way to a frontier (one a new decision's,
  one carried on; the cause not isolated: a person standing in the way, a wall for the plan, then gone, fits; not verified); the pooled rate over the
  exploring plans held (0.91 per 100, bound 1.0); (2) FINDING-2's revert "plans with a run over 2 when reverted: 3 of 5
  (predicted >= 4)", while its discriminators held (REVERTED 3.27 per 100 and 263 stale targets walked onto, REAL 0.91 and 0);
  (3) WHIM's "at least 15 points more": 75% against 63%, 12 points.
* `2026-10-09-step4-RATE-SEEDS101.txt`: 17 of 19. Every behaviour replicated (TYPE-DECISIONS 83 decisive of 382, 100% in the
  chart's set; TYPE, TYPE-FAULT, RECOIL, WILD, CATCH 9 of 10, TRAINER, RIVAL 5 of 10, FAINT, LEARN, REFUSE). FIELD-FAULT and
  FIELD-STEP4 FAIL AS VACUOUS: their case (the forgotten-field replacement sending the Pokemon still on the field) did not
  occur in seeds 101-130 ("refused the one on the field in 0 seeds"; the partner fell in 1 of 30, seed 129, Skitty sent in).

### Step 4.1: the step-4 verifier's and adversarial review's findings (2026-10-09)

Each finding is fixed in the AI's code, each with a unit test and a mutant that FAILS on its revert (`revert_step4.py`
B44-B57, `revert_step3.py` W90-W92) and, where it can be played, a live arm read by the GAME (THE REPLAY, `--battle-log`)
and a sweep plan. Every pre-registered number came from development runs of this code before the graded runs.

| the finding | the fix | proven by (final tree) |
|---|---|---|
| 1 (HIGH) "The SHIFT prompt ('Will ... change POKéMON?') is answered about the FAINTED foe: per battle_scripts_1.s the yes/no comes before the next foe loads" | `brain/battle.py` `_shift`: the incoming species is read from the question's words (`incoming`: "about to use TREECKO."; `knowledge/facts.py` species_named), the foe judged is built from SPECIES facts (its level, unseen, guessed as the last foe's, so the far-outlevels guard asks for 3 more levels), and a YES carries the chosen member's PID into the party menu (`shift_to`; `replacement` sends it instead of ranking again by level); the skill gives the decider the pages before the question | live SHIFT (`rival_rustboro.ss1`: Rustboro's rival, Wingull then Treecko, against the Marshtomp put first): `YES (yes: Marshtomp is badly matched against Treecko (Grass: threat x4 ...); Taillow is much better ... (the words say TREECKO comes next ...))`, `who goes in: Taillow L17 (45/45 HP), the switch it decided at the question`, and BY THE GAME the Taillow (a8dbcf1b) came onto position 0 after the Wingull fainted and BEFORE the Treecko came out; won, MAY's flag set. SHIFTX (step 4's answer): NO about the fainted Wingull, nobody came onto position 0. The sweep's SHIFT: in 10 of 10 seeds the question was judged about the species the game then sent out, YES in 8 (bound 6), every YES's member in by PID before the foe; SHIFT-FAULT: judged about the foe that had just fainted in 10 of 10. `ShiftTests` (3), `SkillTests.test_the_shift_question_sends_...`; B44, B45 |
| 2 (HIGH) "A disabled/unselectable move loops ('decide again' picks the same move) until 150 menus" | `BattleMind.cannot_use`: when the move grid comes back after a move was chosen (`TrySetCantSelectMoveBattleScript` brings it straight back: decomp `src/battle_main.c`), that move is unusable for the rest of the turn, excluded from every value; cleared at the next action menu | `UnusableTests`; `SkillTests.test_a_refused_move_is_not_chosen_again_that_turn` (the model refuses ABSORB: another move, won; FAULT `forget_unusable`: "the battle did not end within 150 menus"); B46, B47. No fixture has a Disabled move (Known limits); ROUND 2 plays the refusal live through the 0-PP path of the same game code (live REFUSED, REFUSEDX; the sweep's REFUSED, REFUSED-FAULT: "Step 4.1 round 2") |
| 3 (MED) "Switch, heal and run never ran live" | three live arms, each from a fixture PLAYED by button presses (`gates/make_step41_fixtures.py`); HEAL's first development run found a bug no unit test had: after the Potion the party menu's message ("MUDKIP's HP was restored by 17 point(s).") waited for A over a busy list, and the skill gave up ("the battle: the Potion could not be given": the Potion used, the HP restored, the battle stuck). Fixed: `skills/battle.py` `_give_item` READS the message. Two one-frame callbacks of that path got scene names (`eyes/screens.py`: no catch-all idle) | live HEAL (`heal_r103.ss1`: Route 103's rival after the AI bought 2 Potions at Oldale's mart; Mudkip L6 9/23): the Potion used at 26 %, POTION 2 -> 1 BY THE TRUTH, the Mudkip's HP 6 -> 23 at position 0 BY THE GAME (max unchanged), WON (the rival is won 2 of 10 without Potions; 10 of 10 in the sweep's HEAL). SWITCH (`switch_joey.ss1`: the Poochyena put first against Joey's Machop): `switch: Poochyena is badly matched against Machop (Fighting: threat x2 ...); Mudkip is much better`, BY THE GAME the Mudkip (550a9be6) came onto position 0 with the Poochyena standing; won; 10 of 10 in the sweep. RUN (`run_r116.ss1`: a wild battle begun with the Poochyena at 29 % while training): `run: its Poochyena is low (29%)`, gBattleOutcome 4; 10 of 10 in the sweep. `SkillTests.test_a_potion_is_given_and_its_message_read`; B48 |
| 4 (MED) "Hidden information: the ball choice uses catch_rate; damage_fraction's exact formula with an 8% KO margin; foe types from live gBattleMons" | the ball by what a person SEES (`_ball`: two misses, the foe still strong, a species that seems rare to it); a hit is a ROUGH sense (`rough_share`: to the nearest eighth of the foe's HP; `damage_fraction` = that, give or take an eighth; a weakening move is safe when the rough worst leaves the bar something); the types a person knows (`seen_types`: the species', for both sides) | `CatchTests.test_the_ball_by_what_a_person_sees_not_the_catch_rate` (a weakened Sableye, catch rate 45, and a Wurmple, 255: the same ball); `HiddenInfoTests` (a Color-Changed Kecleon judged a Normal type; every estimate an eighth give or take one); B8, B49, B50, B51. The sweep's CATCH unchanged: 9 of 10, the rest a weakening hit's critical |
| 5 (MED) "Robotic battling: 'clearly the best' 307 of 550; never a status move" | `Temperament.opener` (Story 0.12, Catcher 0.20, Trainer 0.25): on its first turn against a foe, one seeded draw, an OPENING stat or status move, only when SAFE (`_safe_for_status`: its HP at least 70 %, no x2 threat by the foe's species or seen moves, the foe at most 2 levels above it, the foe's bar at least 60 %); `_catch_status`: a sleep or paralysis move before the throws (twice at most, its HP at least half, never Thunder Wave on a Ground type) | `OpenerTests` (300 seeds per temperament; never later, never unsafe; the catch's Stun Spore); B53-B57. The sweep's STATUS: 3 status moves chosen by choice over 255 runs (Growl twice, Focus Energy), each shown chosen by the game at full HP; "clearly the best" 618 of 1,674 fight choices (37 %; step 4: 307 of 550, 56 %). Thin: the fixtures' leads seldom have a status move on a safe first turn (Known limits). ‼ ROUND 2: the STATUS count bound FAILED held out and the 37 % was not like for like (the verifier, replicated: on the same 8 plans and seeds HEAD 302 of 367, 82 %, this code 267 of 368, 73 %); the opener is now judged as a RATE on its own plan and the sweep's Sing is played (CATCHS): "Step 4.1 round 2" |
| 6 (MED) "Overkill valued: damage never capped at the foe's remaining HP, so Take Down (85 %, recoil) beat Water Gun (100 %, no recoil) when both KO" | `_ko_worth`: a move whose rough damage is at least what the foe's bar has left FINISHES it and is worth as much as the strongest move (`move_value` `ko_worth`), so finishers compare by hit chance and recoil | the recorded case (`fixtures/recoil_r102.look.json`, the 15-HP Poochyena): `RecordedRecoilTests.test_overkill_every_move_finishes_it_so_take_down_never` (every damaging move told "finishes it"; Take Down never at 99, 20 or 3 HP); `OverkillTests`; live OVERKILL (`ch13_r119_wedge.ss1`): the first move not Take Down by the game; OVERKILLX (FAULT `overkill`, step 4): Take Down; the sweep's OVERKILL A/B: Take Down REAL 0 of 10, step 4's valuation 10 of 10; B52. The recoil cap keeps its A/B under FAULT `overkill` (RECOIL 10 of 10, the recoil the game charged [3] HP; RECOIL-FAULT 2 of 10) |
| 7 (MED) "Navigation: TOWN-Trainer's journey share 0.45 against a loose 0.5 bound; CROP's 14 laps unbounded; the churn 'fix' mostly relabels decisions" | ‼ SUPERSEDED BY ROUND 2 (the charge REMOVED, the causes fixed in the walk; "Step 4.1 round 2"); what step 4.1 did, kept as history: THE WALK, NOT THE LABELS: `Navigator.journey` (begun where a decision is made standing, its steps counted) and `brain/explore.py` `JOURNEY_WEIGHT`: a place chosen or carried on ON THE MOVE is charged what its journey would walk beyond the shortest way from where it began, past `JOURNEY_SLACK` (4: with none, a carried decision two steps off the line lost to a place across town and TOWN-Catcher's journeys grew from 0.07 to 0.19); per-plan churn bounds (`rate_step3.py` CHURN_PLAN_BOUNDS) and the live arms' journey bounds tightened (TOWN 0.40, ROUTE 0.20, SCENEX 0.50, from 0.45, 0.25, 0.55); CROP's laps bounded (`CROP_LAPS_MAX` 25) | the sweep's JOURNEY A/B (the charge off in a copy, the step-4 explorer): TOWN-Trainer's every journey 0.46 of its steps beyond the shortest known way (252 of 550) REVERTED, 0.32 (138 of 437) REAL; the lapped plans together 0.27 and 0.25; per-plan journey bounds TOWN 0.12, ROUTE 0.08, TOWN-Catcher 0.14, TOWN-Trainer 0.36, SCENE-EXPLORE 0.40, HOUSE 0.32 (each a little above its plan's development value; every plan shared 0.50 before; ‼ TOWN's and TOWN-Catcher's REFUTED by the held-out seeds, 0.21 and 0.22: below); CROP 23 laps (bound 25); `JourneyTests` (3), W90-W92; every live_step3 trajectory unchanged (214 of 214 pre-registered numbers held: no live arm meets a doubling back) |
| 8 (LOW) "TYPE proof: add a second matchup to the type-blind A/B and label TYPE-DECISIONS as a hands check" | the sweep's TYPE SECOND MATCHUP: the Nincada (battler 2) against the Shroomish, Leech Life (Bug x2, STAB: 60) over Scratch (40) only by the chart; TYPE-DECISIONS renamed "(a HANDS CHECK)" with the reason (the decider draws only from the chart's near-best set, so the game showing such a move proves the told choice reached the game, not the chart) | BY THE GAME (gChosenMoveByBattler[2]): Leech Life at the Shroomish REAL 10 of 10, the type-blind fault 0 of 30 (Scratch every time); the first matchup unchanged (Absorb at the Geodude 10 of 10 against 0 of 30) |
| 9 "Evidence pruning: ai_player/evidence/archive is 54 MB" | `gates/prune_evidence.py` and the policy in `evidence/archive/README.md`: the archive keeps only the files a document or a commit message cites by name; every other earlier-tree file is one line of `evidence/archive/INDEX.md` (path, size, sha256, its `git show` command) and is deleted, only when git tracks it unchanged | applied at HEAD `7a70a445`: 23 cited files kept (5 moved from the retired tree `7b4322c9ac0df2e1`'s top level), 884 indexed and deleted; the archive 54 MB -> 1.5 MB. ROUND 2 (the verifier: the INDEX's sizes and hashes were the CRLF working copies', not the LF blobs `git show` prints): every line recomputed from its blob (`--reindex`: 884 checked, 778 rewritten), and 884 of 884 now match `git show` byte for byte |

**Everything above on ONE tree, `sha256:8b742931d35fa205`** (HEAD `7a70a445` plus the working tree; its evidence files,
cited below by name, are in `evidence/archive/8b742931d35fa205/` since round 2 retired that tree (all but 12,
which round 2's graded runs had already written over: `evidence/archive/README.md`; since round 3 the files cited by their
full names stay there as files and the rest are in its `uncited.zip`), each suite run ONCE after the last code
change: `check_purity.py` PASS; units `test_check_purity` 29, `test_host` 20, `test_eyes` 56, `test_hands` 56,
`test_world` 126, `test_battle` 97, all OK (`2026-10-09-step4-UNITS.txt`); the knowledge files up to date and checked
against pret (`step4-KNOWLEDGE.txt`, its plants found: `step4-KNOWLEDGEX.txt`); mutants `revert_step11.py` PASS,
`revert_step2.py` 39 caught and 5 redundant alone as predicted of 44, `revert_step3.py` 90 and 1 of 91, `revert_step4.py`
57 of 57; live through the launcher `live_step0.py` 4 arms, `live_step1.py` 21, `live_step2.py` 17 and its seed-9
replication 16, `live_step3.py` 39 (214 of 214 pre-registered numbers held), `live_step4.py` 19 (57 of 57 held), no
emulator left running; the sweeps `rate_step3.py` 100 of 100 runs as intended, every bound and revert as predicted
(`step3-RATE.txt`), `rate_step4.py` 28 of 28 (`step4-RATE.txt`).

‼ **THE HELD-OUT REPLICATION (seeds 101-110, played by no development run before it) did NOT hold everywhere**, and the
failures are left as they are (re-tuning on them would make them development seeds):
* `rate_step3.py --first-seed 101` (`2026-10-09-step3-RATE-SEEDS101-110.txt`): OVERALL FAIL. NEW in step 4.1: the
  per-plan journey bounds of TOWN (0.12) and TOWN-Catcher (0.14), set a little above seeds 1-10's values (0.07, 0.09),
  are REFUTED: 0.21 and 0.22. TOWN's 0.21 is the same with the charge off (the previous tree's held-out run: 0.21), so its
  bound was fitted to the development seeds; TOWN-Catcher's grew with the charge (0.15 with it off, 0.22 on: seeds 102,
  103 and 106, where the charge sends the Catcher east before it turns for the town's north exit, the TOWN trajectory),
  and its seed 102 now has 3 reversals, which puts the exploring plans together at 1.07 per 100 steps against the step-3.2
  bound of 1.0 (the previous tree's held-out run: 0.91). What replicated: TOWN-Trainer's journeys 0.45 -> 0.33 (the
  JOURNEY A/B's prediction HELD), CROP 14 laps (bound 25), every plan's runs as intended. Already failing on the previous
  tree's held-out run and unchanged: TOWN's seed 102 with 3 reversals (per-run bound 2) and the FINDING-2 revert
  prediction (3 of 5 plans over 2 when reverted, predicted at least 4).
* `rate_step4.py --first-seed 101` (`2026-10-09-step4-RATE-SEEDS101.txt`): 25 of 28. NEW: STATUS 2 status moves by choice
  (bound at least 3; Growl twice, at full HP, the game showing each): the openers are rare by design and the bound was
  set at the development count. Already failing on the previous tree's held-out run and unchanged: FIELD-FAULT and
  FIELD-STEP4 (no held-out seed has the partner fall where the step-4 replacement picks the one on the field: 0 seeds, so
  nothing to reproduce). What replicated: TYPE 10 of 10 against 0 of 30, the SECOND MATCHUP 10 of 10 against 0 of 30,
  SHIFT YES 7 of 10 (bound 6) against 0 of 10, HEAL, SWITCH, RUN, OVERKILL 0 of 10 against 10 of 10, RECOIL 10 of 10
  against 3 of 10.
* Tried AFTER the held-out run, in COPIES only (the tree unchanged, so nothing above was re-run): charging only a place
  NEARER the journey's start (TOWN-Trainer 0.53, worse than no charge), `JOURNEY_SLACK` 6 or 8, `JOURNEY_WEIGHT` 0.5: none
  moved TOWN-Catcher's held-out seed 102 (28 of 56 beyond in every variant but the charge off). The charge's trade is
  measured, not fixed: TOWN-Trainer much better on both seed sets, TOWN-Catcher a little worse on both (0.07 -> 0.09,
  0.15 -> 0.22), TOWN unchanged.

### Step 4.1 round 2: the step-4.1 verifier's failures and weak proofs (2026-10-09)

The verifier FAILED step 4.1 on finding 7 (the journey bounds refuted held out, the pooled reversals over their bound,
the charge making TOWN-Catcher worse, the bounds fitted to the development seeds) and on finding 5's STATUS (2 openers
held out against a bound of 3; the development count had counted SHIFT and SHIFT-FAULT's replayed first turns twice),
with three failures carried over (TOWN's held-out seed 102 at 3 reversals, the FINDING-2 revert's prediction, FIELD-FAULT
and FIELD-STEP4 vacuous held out) and nine weak proofs. ‼ **SEEDS 1-10 AND 101-110 ARE NOW DEVELOPMENT SEEDS** (every
bound below was set from a 20-seed bootstrap over both sets); **THE HELD-OUT REPLICATION IS SEEDS 201-210**, played by no
run before the graded one.

| what failed or was weak | what was done | proven by (final tree) |
|---|---|---|
| Finding 7: the journey charge (TOWN 0.21 > 0.12, TOWN-Catcher 0.22 > 0.14 held out; pooled reversals 1.07 > 1.0; the Catcher made worse; bounds fitted) | THE CHARGE IS REMOVED. Run by run, the doubling back had three causes in the WALK, each fixed there: (a) the Trainer's people taste was a bonus on UNSEEN tiles near a person, which pulled it to the far side of fences and back; now a PEOPLE place, the seen tile beside a person not met yet (`world/memory.py` persons, met, `MEET_RADIUS`; `brain/explore.py` people candidates, `PEOPLE_RECENT`; `brain/navigator.py` `MEET_TRIES`, a met person's target stale); (b) anyone standing ANYWHERE on the followed plan broke it at once, so the walk turned round; now only someone on the next `PERSON_AHEAD` steps does, and they are WAITED for (`WAIT`, `PERSON_PLAN_WAITS`) before the walk goes round; (c) a detour went two tiles aside and back; now it bends (`DETOUR_EXTRA`). The people weight was measured, not tasted (1.5: met 69 of 80 in 816 steps, journeys 0.27; the old pull 57 of 80 in 1043, 0.43; 1.75-2.5 worse) | the sweep's WALK A/B (the step-4 explorer's walk in a copy, `live_step3.WALK_MUTATIONS`), seeds 1-10: TOWN-Trainer's journeys 0.46 (252 of 550) REVERTED, 0.25 (92 of 362) REAL, people met 57 of 74 against 63 of 70, steps 550 against 362, no plan worse; HELD OUT 201-210: 0.45 -> 0.23, met 63 of 76 against 63 of 72, steps 565 -> 373. Per-plan journey shares held out (bound): HOUSE 0.26 (0.37), TOWN 0.10 (0.31), ROUTE 0.10 (0.11), TOWN-Catcher 0.08 (0.23), TOWN-Trainer 0.23 (0.37), SCENE-EXPLORE 0.36 (0.41); the exploring plans' reversals together 4 in 1,469 steps held out (0.27 per 100; bound 1.0), 3 in 1,413 on seeds 1-10; CROP 25 laps held out (bound 37). Live: TOWNT (the Trainer through the launcher) and TOWNTR (its walk reverted); `PeopleTests`, `WaitTests`, `BendTests`, the 40-seed people test; W93-W98 |
| Finding 5 STATUS (2 < 3 held out; SHIFT and SHIFT-FAULT double-counted) | The opener is judged as a RATE: the decider SAYS every chance the rule had ("an OPENING move" drawn, or "no opener this time ... (personality: opener p)" passed over), the sweep counts the chances on the REAL plans only (a fault plan replays its real plan's first turn and is never counted) and checks the drawn count is within 3 standard deviations of the temperament's chance; a plan with many chances (OPENER: Rustboro's rival, Trainer, 30 seeds). "Clearly the best" is reported LIKE FOR LIKE | `rate_step4.py` STATUS, seeds 1-10: 74 chances, 18 drawn against 18.4 expected (3 sigma 11.1), every drawn opener shown chosen by the game at full HP; CLEARLY THE BEST on the step-4 sweep's 8 plans: 267 of 368 (73 %; HEAD on the same plans and seeds 302 of 367, 82 %: openers and finishers replace some "clearly" choices); B59; `OpenerTests.test_every_chance_of_an_opener_is_said_drawn_or_passed_over` |
| TOWN seed 102's 3 reversals; FINDING-2's prediction (3 of 5, predicted at least 4) | not re-tuned on the seeds that refuted it: after the walk's fixes above, seed 102 had 2 reversals on TOWN (the per-run bound) and 1 on TOWN-Catcher in the development sweep (the exploring plans together 16 in 3,004 steps over the 20 development seeds, 0.53 per 100), and the prediction was re-registered from the 20-seed bootstrap (`FINDING2_PLANS_OVER` 2: at least 2 plans over 2 in 100 % of the bootstrap draws) | seeds 1-10 4 of 5 plans, held out 5 of 5 (predicted at least 2); reverted 3.25 and 3.26 per 100 steps against 0.21 and 0.27 real |
| FIELD-FAULT and FIELD-STEP4 vacuous held out | the FIELD plans run on the seeds where TYPE-FAULT's partner FELL (this sweep's own falls) plus a fixed ANCHOR seed (6) where the fall is known, so the check is never empty; which seeds came from the sweep's own falls is said | seeds 1-10: refused in seeds 6 and 7 (7 the sweep's own), FIELD-STEP4 stuck in exactly those |
| Weak: like-for-like "clearly the best" | the verifier's A/B replicated in a scratch copy and the sweep now reports it beside its own count | above |
| Weak: finding 4, base stats | not changed; a Known limit (the rough sense of a species' strength is what a player has) | Known limits |
| Weak: RUN's gBattleOutcome had no value before the run (the fixture already read 4) | the recorder reads gBattleOutcome EVERY frame (`hands_harness.py` BattleRecorder `outcome_start`, `outcomes`); RUN passes only if a 0 comes before the last value 4. Measured: the truth BEFORE the run reads the fixture's stale 4, the replay's FIRST frame already reads 0 (the battle's own clear, `BattleStartClearSetData`, runs in that frame), then 4 when it ran (frame 695). ‼ WORDING: `live_step4.py`'s docstring calls the first recorded value "the fixture's old 4" and its check message labels the sequence `[0, 4]` "the fixture's old value, the battle's own clear to 0, then 4"; the 4 before is the TRUTH's reading printed in the evidence ("TRUTH of the fixture BEFORE the run": `"battle_outcome": 4`), not the replay's first value. Left as is so the graded tree stays one tree; the check itself is right | sweep RUN 10 of 10 `[0, 4]`; live RUN (`step4-RUN.txt`: before 4, replay `[0, 4]`) |
| Weak: finding 2 had no live arm | the refusal played live through the 0-PP path of the same game code (`AI_PLAYER_FAULT_IGNORE_PP`: the decider blind to PP) from a story-bot save in a wild battle (Wailord L61: Surf, Water Spout, Waterfall at 0 PP, Dive 10) | live REFUSED and REFUSEDX; the sweep's REFUSED: in 4 of the 4 seeds that fought, the grid came back for three moves with 0 PP by the truth, only Dive taken by the game, won; REFUSED-FAULT (step 4's rule): the grid back 133-134 times and no move taken until the frame bound |
| Weak: the catch's sleep or paralysis move never ran live | `make_step41_fixtures.py --only sing` builds `sing_r117.ss1` (a Skitty with SING put first by START-menu presses; the AI's explore brain from Mauville to Route 117; the first frame of a wild battle against an Oddish not caught) | live CATCHS (Sing taken, the Oddish asleep by the game, caught) and CATCHSX (FAULT `no_catch_status`: never); the sweep's SING: Sing taken 10 of 10, asleep 7 (bound 3: Sing hits 55 %), caught 10; SING-FAULT 0 of 10 |
| Weak: no live arm meets a doubling back | TOWNT: the Trainer from `pokedex_done.ss1` to Route 101 through the launcher; it walks up to people and waits for someone in the way | live TOWNT and TOWNTR (numbers in "the proof" below) |
| Weak: finding 9, INDEX hashes of the CRLF copies | `prune_evidence.py --reindex` | 884 of 884 lines match `git show` |
| Weak: `incoming()` cut "MR. MIME" at its full stop; NIDORAN♀ | the longest species name the words hold, cut at `.!?` only after it; ♀ and ♂ read as letters | `ShiftTests.test_a_species_whose_name_has_a_full_stop_or_a_sign_is_read_whole`; B58 |
| Weak: `make_step41_fixtures.py`'s docstring | corrected (HEAL's fixture is `heal_r103.ss1`; `--only` lists every fixture) | |

THE PROOF, every suite once on ONE tree, `sha256:d272da770b442dc4` (HEAD `7a70a445` plus the working tree; since round 3
its evidence files are in `evidence/archive/d272da770b442dc4/`: the four cited by their full names as files, every other
one in that folder's `uncited.zip`, one `INDEX.md` line each), after the last code change: `check_purity.py` PASS; units `test_check_purity` 29, `test_host` 20, `test_eyes` 56, `test_hands` 56,
`test_world` 132, `test_battle` 99, all OK (`2026-10-09-step4-UNITS.txt`); the knowledge files up to date and checked
against pret (`step4-KNOWLEDGE.txt`, its plants found: `step4-KNOWLEDGEX.txt`); mutants `revert_step11.py` PASS,
`revert_step2.py` PASS, `revert_step3.py` 93 caught and 1 redundant alone as predicted of 94, `revert_step4.py` 59 of
59; the sweeps `rate_step3.py` seeds 1-10 PASS (`step3-RATE.txt`) and HELD OUT 201-210 PASS
(`step3-RATE-SEEDS201-210.txt`), `rate_step4.py` seeds 1-10 32 of 32 (`step4-RATE.txt`) and HELD OUT 201-210
32 of 32 (`step4-RATE-SEEDS201.txt`); live through the launcher `live_step0.py` 4 arms, `live_step1.py` 21,
`live_step2.py` 17 and its seed-9 replication 16, `live_step3.py` 41 (237 of 237 pre-registered numbers held),
`live_step4.py` 23 (73 of 73 held), every one PASS with no emulator left running; `provenance.py --check-evidence` 132
of 132. ‼ `live_step2.py` and its replication were run TWICE: the first time every arm passed but OVERALL said FAIL,
because the sweeps chain ran beside them and their leftover-process check counts any `hands_harness.py` (the sweep's
battles) as theirs; re-run alone, PASS (the evidence files are the second run's). New live numbers: TOWNT (the Trainer,
Birch's lab to Route 101, seed 3): every journey 10 beyond of 37 walked, 3 decisions to walk up to someone, 7 of the 7
people seen MET, 3 waits for someone in the way, 0 reversals, and the game's own step counter +39 against 37 steps the
looks confirmed; TOWNTR (its walk reverted): 26 beyond of 52, nobody walked up to, 5 met by passing. REFUSED: the truth
gives Surf, Water Spout and Waterfall 0 PP and Dive 10; the grid came back for each of the three, the game took only
Dive, won; REFUSEDX: the grid back 134 times, no move taken, stopped by the 40,000-frame bound (‼ the arm's one-line title
in the summary says "until the 150-menu bound": the bound that ends it at this budget is the frame bound, as its check
line says). CATCHS: Sing taken twice by the game, the Oddish asleep from frame 4010, caught at 7086 (a new PID in a box,
the player's id); CATCHSX: no Sing, never asleep, caught.

**THE HELD-OUT REPLICATION (seeds 201-210) HELD EVERYWHERE** (‼ on seeds 201-210 only: the verifier's second round played
seeds 301-310, no run's before, and `rate_step4.py` FAILED 3 of 32 there: RECOIL-FAULT "Take Down in 8 of 10 seeds (bound
<= 5)", REFUSED and REFUSED-FAULT "2 of the 2 seeds where it FOUGHT (bound: every one, at least 3)"; the behaviour held in
every seed where it applied, the bounds were fragile: "Step 4.1 round 3"): every per-plan bound, the reversal bounds (the exploring
plans 0.27 per 100 steps, bound 1.0; no run over 2), the WALK A/B (TOWN-Trainer 0.45 -> 0.23) and the FINDING-2 prediction
(5 of 5 plans) in `rate_step3.py`; in `rate_step4.py` STATUS (79 chances, 26 openers drawn against 18.8 expected, within 3
sigma = 11.3), SING (taken 9 of 10, asleep 7), SING-FAULT 0 of 10, REFUSED (5 of the 5 seeds that fought) and REFUSED-FAULT
(5 of 5), FIELD-FAULT and FIELD-STEP4 (refused in seeds 6, the anchor, and 218, this sweep's own fall), SHIFT YES 7 of 10,
TYPE and its second matchup 10 of 10 against 0 of 30, HEAL, SWITCH and RUN 10 of 10, OVERKILL 0 of 10 against 10 of 10;
CLEARLY THE BEST 260 of 357 (73 %, as on seeds 1-10).

### Step 4.1 round 3: the step-4.1 verifier's second round (2026-10-09)

The verifier FAILED round 2 twice: NEW held-out seeds (301-310, which no run had played) failed 3 of `rate_step4.py`'s 32
checks, and the foe's base stats still fed the damage estimate. It also listed eight weak proofs and two rule violations.
Every item is answered below in code, a gate or a measurement; what could not be built is said. ‼ **SEEDS 1.., 101..,
201.. AND 301.. ARE ALL DEVELOPMENT SEEDS NOW; THE HELD-OUT REPLICATION OF THIS ROUND IS SEEDS 401..**, played by no run
before the graded one. ‼ THAT HELD-OUT RUN FAILED ONE CHECK, and the failure was the GRADER's (below: seed 422); with the
grader fixed and the AI's code unchanged, seeds 401.. were re-graded and a second held-out replication, **SEEDS 501..**, was
played for `rate_step4.py`; `rate_step3.py`'s first held-out run (401-410) failed too, a fragile round-2 tolerance, and after
its revert predictions were re-registered **seeds 501-510** were its held-out replication. Both second replications PASS.
Only the suites this round touched were re-run (the task's process); the full regression of every step runs once at the end
of step 4.1.

| what failed or was weak | what was done | proven by (this round's tree) |
|---|---|---|
| FAILURE: "NEW HELD-OUT SEEDS FAIL rate_step4 (seeds 301-310) ... RECOIL-FAULT ... a weighted draw with p about 0.37. A bound of 5 or fewer fails about 11% of 10-seed samples ... REFUSED ... a floor of 3 fought seeds fails about 17% of samples ... What fails are fragile pre-registered bounds" | EVERY bound on a count of a CHANCE event is set where a sample fails it with at most 0.1 % probability under a model the grader names and prints (`rate_step4.py` `FALSE_FAIL`, `floor_for`, `window_for`, `dev_floor`): a rate the decider's OWN RULE sets is judged by that rule's binomial window (RECOIL-FAULT: the step-4 rule's draw between Take Down and Water Gun, its chance 0.365 computed from the worths the decider TOLD, `draw_chance`, now 30 seeds; SHIFT's YES: the Trainer's switch_willing 0.8 over the questions where the switch rule found a better member; REFUSED and REFUSED-FAULT: the Story decider lets a new species go with chance 0.4, now 30 seeds each, floor 4 fought; STATUS: 3.29 standard deviations); a rate with no rule behind it (the game's dice) by the binomial floor at the 95 % lower confidence bound of its rate over every development seed (`DEV_RATES`: CATCH 74 of 80, now 20 seeds a sweep; HEAL, RUN, WILD, TRAINER 40 of 40; FAINT 40 of 80, now 20 seeds; SING taken 38 of 40, asleep 28 of 40); one decision replayed, or correctness in every seed where a case occurred, stays "every seed". All four development sweeps of this round's code PASS 35 of 35 (seeds 1.., 101.., 201.., 301..; RECOIL-FAULT 11, 11, 8, 17 of 30, window 3-20) | the held-out sweep, seeds 401.. (below) |
| FAILURE: "HIDDEN INFORMATION IS STILL USED ... `defense = estimate_stat(foe_species.defense ...)`, `hp = estimate_stat(foe_species.hp, foe.level, hp=True)` ... The foe's base stats still feed _formula_share, then rough_share, then the KO and finisher checks and the recoil HP" | `brain/battle.py` reads a species' TYPES and NAME only: the foe is guessed as a TYPICAL Pokemon of its LEVEL (`TYPICAL_BASE`: the median base stat of all 386 species, the same numbers for every foe; `foe_max_hp`), and that guess is CORRECTED by what its own hits are SEEN to take off this foe's bar (`_seen_factor`: the last hit seen over the guess for that move, kept within 0.4-2.5; `_observe` records it). The user's attack is its own summary's stat. No fault switch puts base stats back (that would leave the hidden read in the AI's code): mutants do, in a copy | `HiddenInfoTests`: four Normal types of one level with the most different base stats (Chansey, Snorlax, Whismur, Zigzagoon) get the same guess, max HP and recoil (B60: the species' stats back, CAUGHT); `TYPICAL_BASE` equals the knowledge file's medians; after SEEING Tackle take 60 % of a Wurmple it weakens with Mud-slap, after seeing Take Down take half a Taillow it "finishes it" (B61: CAUGHT); the hit seen is the bar's drop after its move (B62: CAUGHT). The recorded recoil: 4.25 HP by the guess (17 HP for a L3 typical Pokemon), 3.75 by the species, the game 3. THE COST, MEASURED (a development A/B in a copy, not a gate): the CATCH plan over 80 seeds caught 74 with the typical guess and 74 with the species' base stats (mutant B60), the SAME six seeds lost (9, 15, 101, 113, 208, 314: a weakening hit that knocked the foe out). One live trajectory moved: DFAINT, 15640 / 82 -> 17536 / 95 frames and presses (re-registered; step 4's own numbers) |
| Weak: "Finding 1, the PID carried to the party menu, cannot fail live ... In this fixture the by-level fallback ... also picks the L17 Taillow" | a fixture where it CAN fail: `rival_rustboro_hurt.ss1` (`make_step41_fixtures.py --only rival_hurt`: the Taillow put first and hurt by the AI's own battle brain on Route 116's wild Pokemon to 36/45, so by level x HP share it ranks 15.3 under the Poochyena's 16.0, while at half its HP or more the question still finds it much better against the Treecko); FAULT `forget_shift` (decided at the question, NOT carried: the party menu ranks by level) | live SHIFTC: YES about the TREECKO, "who goes in: Taillow ... the switch it decided at the question", and BY THE GAME the Taillow (a8dbcf1b) came onto position 0 before the Treecko; SHIFTCX: the same YES, "Poochyena L16 (42/42 HP) is the best left (no foe standing: by level)", BY THE GAME the POOCHYENA (2b19ca91) came in. The sweep's SHIFT-CARRY / -FAULT: in every YES seed the Taillow (real) and the Poochyena (fault), by the game; `ShiftTests` (the fault half), B45 |
| Weak: "Finding 7: the walk fix moves only TOWN-Trainer ... The churn rule still does not shorten walks ... TOWN 0.31, TOWN-Catcher 0.23 and HOUSE 0.37 are 2-3x the held-out values and above the step-4 walk's own values, so reverting the walk on those plans would still pass. On 301-310: SCENE-EXPLORE 0.39 against a bound of 0.41, CROP 33 laps against 37" | MEASURED FIRST: every journey's excess SPLIT into THE WALKING (each walk's own steps beyond the shortest known way to where it ended) and THE RE-TARGETING (the rest). Over 40 development seeds the walking is 0 to 1 % of the steps on every plan (HOUSE 0 of 454, TOWN 4 of 1,263, ROUTE 4 of 1,501, TOWN-Catcher 6 of 1,210, TOWN-Trainer 14 of 1,566, SCENE-EXPLORE 40 of 4,590): the walk to each target IS the shortest known way, and every journey's excess is the cost of changing target when one goes stale (seen past, nothing left there, met) or another is clearly better. The round-2 walk fix removed a cause of RE-TARGETING (the Trainer's pull to unseen tiles near people) that only TOWN-Trainer had: on the other plans the step-4 walk's journeys equal these within the noise, so no journey bound can tell those two walks apart. Done: the walking share BOUNDED per plan (`WALKING_SHARE_MAX` 0.04; the LAPS revert, the step-3.1 walk, reports it reverted and real); every per-plan bound re-registered by the same bootstrap, finally over 50 development seeds (journeys HOUSE 0.40, TOWN 0.32, ROUTE 0.12, TOWN-Catcher 0.25, TOWN-Trainer 0.37, SCENE-EXPLORE 0.43, each at its 99.99th percentile so the 18 bounds TOGETHER fail 0.08 % of 10-seed samples; CROP 42 laps; SCENE-EXPLORE's reversals 3.8 per 100); the WALK A/B prints, plan by plan, whether that plan's bound tells the step-4 walk apart. And (after this round's first held-out run FAILED the WALK A/B's round-2 tolerance, below) EVERY revert prediction of `rate_step3.py` re-registered by one bootstrap of the same 50 seeds (`REVERT_SAMPLE`: each fails at most 0.1 % of samples; the ROAM spins judged over the seeds together). Not done: a walk change on the other plans (their walking is already the shortest known way; their re-targeting is the explorer learning a room or a frontier as it walks). The churn rule's claim is fewer decisions and one-step walks at no extra cost (its A/B), not shorter journeys | `rate_step3.py` (the held-out 401-410 below); the 40-seed development rows (`--rows`): a 10-seed pooled journey share is that noisy on ONE code (TOWN 0.07, 0.20, 0.10, 0.17 on the four sets); the step-4 walk per set: TOWN-Trainer 0.46, 0.45, 0.45, 0.48 against 0.25, 0.29, 0.23, 0.28, every other plan within 0.03 |
| Weak: "Finding 5: the opener rate comes almost entirely from one fixture ... Paralysis to help a catch is unit-tested only. 'Clearly the best' is 73% ... a modest change" | a second, independent source of opener chances: plan OPENER-WILD (the Route 116 team's Mudkip, Growl, Story, three wild battles a run, 20 seeds: about 50 chances a sweep); STATUS now requires chances from at least two FIXTURES with 20 each. A SURVEY of every save and fixture's party moves (`gates/survey_party_moves.py`): the only sleep or paralysis move in any party is a Skitty's SING; no state has a paralysis move, so paralysis for a catch stays unit-tested (a fixture would need a Shroomish or Electrike caught and trained: not built). "Clearly the best" is reported, not changed: 75-78 % on the four development sweeps' step-4 plans (HEAD 82 %) | the sweep's STATUS (below); `evidence/<date>-step4-SURVEY.txt` |
| Weak: "Finding 8: the 'second matchup' ... is a different battler in the same double battle and fixture ... not an independent battle" | TYPE INDEPENDENT MATCHUP: TRAINER's single battle (`trainer_battle_r116.ss1`, Route 116, Grovyle against Joey's Machop) and a new plan TRAINER-TYPE-FAULT (types ignored, 30 seeds): with the chart PURSUIT (Dark, resisted by Fighting: 20) is never the first move and QUICK ATTACK is "clearly the best"; type-blind the two are worth 40 each, a draw at 1/2 by the told worths, judged by its window | the sweep (below); development: Quick Attack 10 of 10 every set, Pursuit type-blind 16 of 30, window 6-24 |
| Weak: "Finding 2 is played live only through the 0-PP path ... no Disabled, Taunted or Tormented move is played" | looked for, not found: the survey reads the PLAYER's moves (a Mightyena's TAUNT in 32 states, which refuses the FOE's moves, not the AI's); a refused move of the AI's needs a FOE that uses Disable, Taunt or Torment, and a save holds no foe's moves, so no fixture was built; the refusal stays played through the 0-PP path of the same game code | Known limits; `evidence/<date>-step4-SURVEY.txt` |
| Weak: "Finding 9: the archive is back to 9.8 MB ... The 115 files (8.2 MB) of the never-committed tree 8b742931d35fa205 are kept wholesale ... The prune_evidence.py gap with the `[VERIFY] code:` prefix is not fixed" | `prune_evidence.py`: an uncited file of a tree git does not hold is PACKED into its folder's `uncited.zip` (every member checked byte for byte before the file is deleted), one INDEX line each; a tagged code line is read | applied: 238 files of the two never-committed trees packed (17.7 MB as files, 2.1 MB packed), the archive 9.8 MB -> 4.5 MB with round 2's tree inside it; at the end of the round 5.9 MB, with this round's two stopped graded passes archived by `keep_earlier` and their 93 uncited files packed (`evidence/archive/README.md`); `test_evidence.py` PackTests, CodeLineTests |
| Weak: "Known-wrong text left in a gate. live_step4.py RUN's check says '[0, 4]: the fixture's old value, the battle's own clear to 0, then 4': three labels for two values. REFUSEDX's arm title says 'until the 150-menu bound' although it stops at the 40,000-frame bound" | both corrected, with their docstring lines | live RUN, REFUSEDX (below) |
| Weak: "live_step2's graded evidence comes from a second run ... the check is still not fixed to be specific to its own processes" | `live_step2.py`: every process the driver starts carries THIS run's mark in its environment (`DRIVER_MARK`), and a leftover is a matching process with that mark; a SELFTEST at every start (two idle `hands_harness.py` processes, one with this run's mark and one another driver's: found, not counted) | live_step2 (below), its SELFTEST line |
| RULE: "Evidence-policy order broken ... `--retire` ran after round 2's graded chains had started, so 12 top-level evidence files ... were overwritten. They are unrecoverable" | the slip made harmless for the future: every evidence writer calls `provenance.keep_earlier(path)` before it writes, which MOVES a top-level file of another tree to `archive/<its digest>/` (a taken name gets a suffix); the units' evidence, until now a shell redirect no guard could see, is written by a runner (`gates/run_units.py`) through it. And this round retired the round-2 tree BEFORE writing anything (`--retire d272da770b442dc4 --apply`). The 12 lost files are not recoverable (that tree was never committed) | `test_evidence.py` KeepEarlierTests (with the fault half: without the keep the earlier bytes are gone) |
| RULE: "REFUSEDX's arm title in live_step4.py still claims 'the game takes no move until the 150-menu bound'" | corrected (the title, the grader's docstring, the module docstring) | live REFUSEDX (below) |

THE PROOF, the suites this round touched, each run ONCE on ONE tree, **`sha256:d81c4a52572b6e37`** (HEAD `7a70a445` plus
the working tree), after the last code change (`provenance.py --check-evidence`: every top-level evidence file names it).
The round-2 tree was retired first (`evidence/archive/README.md`). TWO EARLIER GRADED PASSES of this round, each stopped by
a held-out failure, were archived by `keep_earlier` as they were written over: the tree `sha256:ce43362fc87b102e`
(`rate_step4.py`'s grader bug, below) and the tree `sha256:6044f57f1cfdcb92` (`rate_step3.py`'s fragile WALK tolerance,
below). Between those trees and this one only gate files changed (`rate_step4.py`, then `rate_step3.py`): the AI's code
is the same, and every in-battle and in-process trajectory replays identically (the numbers below equal theirs):
* units (`gates/run_units.py`, `2026-10-09-step4-UNITS.txt`): `check_purity.py` PASS; `test_battle` 103, `test_world` 132,
  `test_evidence` 9, all OK; the knowledge files up to date. Mutants (`2026-10-09-step4-REVERT.txt`): **62 of 62 CAUGHT**
  (B60-B62 new; B45's anchor follows the carry's new condition), the unchanged copy passes all 103. The survey
  (`2026-10-09-step4-SURVEY.txt`): 190 states read, the sleep or paralysis moves in any party: Sing (21 Skittys) only.
* `live_step4.py`, 25 arms through the real launcher (SHIFTC and SHIFTCX new; DFAINT re-registered): every arm PASS, its
  purity CLEAN, **81 of 81 pre-registered numbers held**, no emulator left running. SHIFTC: "who goes in: Taillow L17 (36/45
  HP), the switch it decided at the question", BY THE GAME the Taillow (a8dbcf1b) onto position 0 before the Treecko;
  SHIFTCX: "Poochyena L16 (42/42 HP) is the best left (no foe standing: by level)", BY THE GAME the Poochyena (2b19ca91).
  RUN's check now reads "[0, 4]: 0 (the battle's own clear ... already done in the replay's first frame), then 4 (ran), the
  last; the fixture BEFORE the run reads 4 by the truth"; REFUSEDX's title names the 40,000-frame bound.
* `rate_step4.py` seeds 1.. (`2026-10-09-step4-RATE.txt`, the development seeds REPLAYED): **36 of 36** (the new SELFTEST
  of the double-faint check included). RECOIL-FAULT 11 of 30 against its draw's window 3-20; SHIFT YES 8 of the 9 questions
  where the rule found a better member (window 3-9); STATUS 128 chances, 23 openers against 24.7 expected, chances from two
  fixtures (Rustboro's rival 72, the Route 116 team 55); CATCH 18 of 20 (floor 12); REFUSED every one of the 11 seeds that
  fought (floor 4); TYPE INDEPENDENT MATCHUP Quick Attack 10 of 10, type-blind Pursuit 16 of 30 (window 6-24); SHIFT-CARRY
  the Taillow in every YES, its fault the Poochyena in every YES; "clearly the best" 339 of 455 on the step-4 plans (75 %).
* THE HELD-OUT RUN, seeds 401.. (played by no run before; `evidence/archive/ce43362fc87b102e/2026-10-09-step4-RATE-SEEDS401.txt`):
  **FAIL, 34 of 35**: "[FAIL] TYPE-FAULT DOUBLE-FAINT ... a player's Pokemon fell in 2 of 30 seeds ... [(422, ['Skitty',
  'Whismur'], [(0, 'Skitty'), (2, 'Whismur')], 0), (428, ...)]". By the game every part of the behaviour held (the named
  Pokemon came in, nothing refused, the battle ended): seed 422 is the first sweep seed where BOTH of the player's Pokemon
  fell, the Skitty onto position 0 and then the Whismur onto position 2 beside it, and the check (written in the step-4
  verifier's round) compared every send-in's PID with every send-in's neighbour, so the Skitty, sent in first and standing
  beside the second, read as "the one standing beside it". A GRADER bug, fixed send-in by send-in (`not_beside`, with a
  SELFTEST of the three shapes at every run). The AI's code did not change, so the same seeds replay identically: RE-GRADED
  (`2026-10-09-step4-RATE-SEEDS401.txt`): **36 of 36**, the same trajectories (RECOIL-FAULT 11 of 30, SHIFT YES 6, SHIFT-CARRY
  the Taillow / the Poochyena in every YES, CATCH 19 of 20). That re-grade is not a replication: THE HELD-OUT REPLICATION
  of the fixed grader, **seeds 501.. (`2026-10-09-step4-RATE-SEEDS501.txt`), played by no run before it on the tree
  `6044f57f1cfdcb92` (its `rate_step4.py` is this tree's): PASS, 36 of 36**, and replayed on this tree: the same.
  RECOIL-FAULT 9 of 30 (window 3-20); SHIFT YES 8 of the 9 questions (window 3-9), SHIFT-CARRY the Taillow in every YES and
  its fault the Poochyena in 9 of 10; REFUSED every one of the 14 seeds that fought; TYPE INDEPENDENT MATCHUP type-blind
  Pursuit 14 of 30 (window 6-24) against 0 with the chart; STATUS 121 chances from two fixtures (70 and 51), 19 openers
  against 23.6 expected; CATCH 19 of 20; FAINT 9 of 20 seeds, every replacement the named one; SING taken 9, asleep 9;
  "clearly the best" 317 of 445 on the step-4 plans (71 %).
* `rate_step3.py` seeds 1-10 (`2026-10-09-step3-RATE.txt`, the development seeds replayed): PASS, 100 of 100 runs as
  intended, every bound and revert as predicted; the WALKING share 0 to 0.017 on every plan (bound 0.04), the LAPS revert's
  0.081 (HOUSE) and 0.224 (SCENE-EXPLORE) over it; the BOUND lines: TOWN-Trainer's journey bound tells the step-4 walk apart
  (0.25 against 0.46), no other plan's can (the two walks within 0.01). THE HELD-OUT RUN, seeds 401-410 (played by no run
  before; `evidence/archive/6044f57f1cfdcb92/2026-10-09-step3-RATE-SEEDS401-410.txt`): **FAIL**, one prediction: the WALK A/B's "no lapped
  plan's share more than WALK_TOLERANCE (0.03) over the step-4 walk's": TOWN 0.17 (56 of 327) against 0.13 (42 of 313),
  0.04 over. Every bound of this round held there (per-plan journeys, the walking share, CROP 0 to 42, SCENE-EXPLORE's
  reversals) and every other revert prediction (FINDING-2, SCENE-WORDS, SCENE-NEWS, LAPS, WHIM, CHURN, the WALK A/B's
  TOWN-Trainer drop 0.48 -> 0.23 with more people met in fewer steps). WALK_TOLERANCE was round 2's "three times the largest
  difference seen" over 20 seeds: the same kind of fragile registration this round removed from `rate_step4.py`, left in
  `rate_step3.py`'s REVERT predictions. SO EVERY ONE OF THEM WAS RE-REGISTERED (`REVERT_SAMPLE`): the per-seed rows of every
  plan and every revert over 50 development seeds (1-10 ... 401-410, the spent held-out set among them), 20,000 draws of 10
  seeds, a seed's real and reverted runs paired, each prediction where a draw fails it at most 0.1 % of the time. What the
  bootstrap showed of round 2's registrations: the WALK tolerance (0.03) failed 20 % of draws and its "met no fewer people"
  9 %; SCENE-WORDS' "at least 8 of 10" 4 %; WHIM's 5 points 1.25 %; LAPS' 20 rings 0.4 %; CHURN's steps ratio about 1 %;
  ROAM's every-seed "< 2 %" spin criterion 18 % (seed 104 of the development seeds: 3 spins in 150 steps, exactly 2 %).
  Re-registered: TOWN-Trainer's drop at least 0.06, its people met PER 100 STEPS more than the step-4 walk's (17.4 against
  10.4 on seeds 1-10), the OTHER lapped plans together at most 0.03 dearer, each plan alone at most 0.13; SCENE-WORDS at least
  6; WHIM at least 1 point; LAPS at least 19 rings; CHURN's steps at most 1.13 x; ROAM's spins over the seeds together under
  2 % with no seed over 5 of 150; and the 18 per-plan journey, decision and one-step bounds at the percentile where they fail
  0.08 % TOGETHER. Seeds 401-410 RE-GRADED on this tree (`2026-10-09-step3-RATE-SEEDS401-410.txt`, a determinism replay of
  the development set they now are): PASS. **THE HELD-OUT REPLICATION, seeds 501-510
  (`2026-10-09-step3-RATE-SEEDS501-510.txt`), played by no run before it: PASS**, 100 of 100 runs as intended, every bound
  and every revert prediction held: TOWN-Trainer 0.45 -> 0.24 with 18.0 against 12.2 people met per 100 steps; the other plans
  together 0.24 against 0.23; LAPS 346 steps beyond against 4, 27 lap rings in 11 runs; WHIM 76 % against 66 %; CHURN
  decisions 1,329 against 567; SCENE-WORDS 10 of 10; the exploring plans' reversals 0.34 per 100; CROP 18 laps; ROAM 3 spins
  in 1,500 steps.
* `live_step2.py` (its leftover check changed), 17 arms and its seed-9 replication: **both PASS on their FIRST run, with
  `rate_step3.py`'s sweep running beside them** (the very case that made round 2's first run say FAIL): "leftover emulator
  processes: none", and the SELFTEST "leftover_processes on two idle 'hands_harness.py' processes (this run's mark: found;
  another driver's: not counted): PASS". `live_step3.py` TOWN and TOWNT (its journeys' split is new; no check of it moved):
  PASS, 30 of 30 pre-registered numbers held. No emulator left running.

### Known limits of step 4

* **"Train to roughly the gym leader's level before challenging" is NOT BUILT** (HUMAN-PLAY-DESIGN pillar 3's first
  clause; the design draft's `train_to(level)` is one of step 5's goals; named here since the step-4 verifier's second round
  found it neither built nor named). What step 4 has: the battle brain trains for a NUMBER of battles (`AI_PLAYER_BATTLES`)
  and stops where a person would rest (`needs_rest`: its strongest Pokemon fainted or under a third of its HP). What it
  lacks: a LEVEL target, any knowledge of a leader's party (the design's `bosses.json`, from pret's trainer parties, is
  step 5's), and the chain train -> Pokemon Center -> challenge. The visible cost is measured: RIVAL from `rival_r103.ss1`
  wins 2 of 10 seeds and CHALLENGE (the walk-up challenge at 13/23 HP) loses: challenging unprepared.
* **The rival from Route 103's save is usually LOST**: Mudkip L6 at 13/23 HP against a full Treecko is won in 2 of 10
  seeds (the sweep). Arm RIVAL plays seed 5, a won seed CHOSEN for it and said so; arm CHALLENGE (seed 1) loses, and the
  game agrees (DEFEATED_RIVAL_ROUTE103 stays clear). A person would heal first: chaining a heal before a challenge is step
  5's goals. (Step 4.1) With two Potions bought first (arm HEAL's fixture, the Mudkip at 9/23), the same rival is won in 10
  of 10 seeds of the sweep: the Potion at 26 % HP turns it.
* **Status moves (since step 4.1)**: a status move is still worth 0 in the move worth; it is chosen only as a safe OPENER
  (a small chance by temperament on the first turn against a foe), to help a CATCH (sleep or paralysis), or when nothing
  that hurts has PP. The openers are a small chance, not a strategy: no set-up chains, no stat stages remembered. Since
  step 4.1 round 2 the sweep judges the opener as a RATE (each chance said "drawn" or "passed over"; the drawn count
  within 3 standard deviations of the temperament's chance), not a count, and a catch's sleep move is played live (arm
  CATCHS: a Skitty's Sing, the Oddish asleep by the game before the catch; `sing_r117.ss1`). Paralysis for a catch (Stun
  Spore, Thunder Wave) is still proven by unit tests and mutants only: since round 3 that is MEASURED, not assumed (a
  survey of all 190 saves and fixtures by the framework's decoder, `gates/survey_party_moves.py`: the only sleep or
  paralysis move in any party is a Skitty's SING, in 21 states; none has a paralysis move; a fixture would need a
  Shroomish or Electrike caught and trained, not built). Since round 3 the opener's chances come from two fixtures (Rustboro's
  rival and the Route 116 team's wild battles, plan OPENER-WILD), and STATUS requires both.
  The foe's own moves are unknown to it (no learnsets): a matchup is judged by the foe's SPECIES types and the moves it has
  been seen to use.
* **The foe's base stats are NOT used since step 4.1 round 3** (round 2 had kept them and called it a limit; its verifier:
  "hidden information is still used ... `defense = estimate_stat(foe_species.defense ...)`, `hp = estimate_stat(foe_species.hp
  ...)`"). The cost, measured: a foe is guessed as a TYPICAL Pokemon of its level (the median of all 386 species), which is
  sturdier than most early wild Pokemon (a Poochyena's base HP is 35, the median 63), so before its first hit is seen the
  AI underestimates what a hit takes off a frail foe: the sweep's CATCH lost seeds to a weakening Tackle the rough guess
  called safe (see the round-3 numbers); after the first hit the seen correction takes over. A person who has played a
  while would know Poochyena are frail; the AI learns it per foe from the bar, not across battles (not built).
* **The shift question's next foe** is judged by its species (from the words) at a GUESSED level (the last foe's); the
  far-outlevels guard asks for 3 more levels than with a seen level. A nicknamed foe could not be read (trainers' Pokemon
  have none in Emerald). The words are read from the pages the eyes showed before the question: a question with no such page
  is answered NO ("it cannot tell who comes next").
* **A refused move** (Disabled, Taunt, Torment, no PP) is excluded for the turn on the GRID'S RETURN (the game's behaviour,
  `src/battle_util.c` TrySetCantSelectMoveBattleScript, which refuses a Disabled move and a move with 0 PP by the same
  code), not by reading the words. Since step 4.1 round 2 the refusal is PLAYED live (arm REFUSED and the sweep's REFUSED:
  the decider made blind to PP by a FAULT switch, `AI_PLAYER_FAULT_IGNORE_PP`, chooses moves with 0 PP and the game sends
  the grid back); no fixture has a Disabled, Taunted or Tormented move, so those causes are the same code path, not
  separately played (round 3's survey: a save holds the player's moves, not a foe's; the player's own Taunt, a Mightyena's
  in 32 states, refuses the FOE's moves). Without the fault the decider never chooses a move with 0 PP.
* **A battle resumed on the party menu** (no look at the battle yet, as `ki17_partymenu_wedge.ss1`) has no field to
  remember: the replacement is ranked by level and HP ("no battle view: the field unknown"), and the game's refusal is
  what keeps the one on the field out (arm REFUSE).
* **Evolution and Struggle are not exercised live.** An EVOLUTION is let happen (nothing pressed; its texts advanced on
  their waits), but no fixture within one battle of an evolution was found (a survey of the 172 saves and 12 fixtures).
  With no PP left the decider presses FIGHT and lets the game use Struggle (untested). (Healing and a refused move were in
  this bullet until step 4.1: healing is now the live arm HEAL, a refused move is fixed and proven on the screen model.)
* **A weakening hit can still knock the foe out**: the KO check uses the best NORMAL damage roll; a critical hit doubles it
  (1 in 16), as it would for a person (the sweep: 1 of 10 CATCH seeds, seed 9, whose screen read "A critical hit!").
* **A double battle**: no switching, healing or running; an ally is never targeted; doubles are only trainers' in Emerald.
  A partner's faint is handled (arm DFAINT, the sweep's DOUBLE-FAINT); BOTH battlers fainting at once (two party menus) is
  unit-tested only (`SkillTests.test_both_fell_two_party_menus_two_different_pokemon`, mutants B33, B34): no fixture loses
  both in one turn.
* **A refused SWITCH** (the game refusing a Pokemon chosen to SHIFT in) goes back to the battle's menu with B: since the
  step-4 verifier's second round a UNIT test reaches it (`SkillTests.test_a_refused_switch_goes_back_to_the_battles_menu_
  and_fights`: the words read, the decider told, B on the party menu's look, then FIGHT; FAULT `ignore_refusal`; mutant
  B42); no live arm does (the decider never chooses a member on the field to switch to, and no fixture traps the player's
  Pokemon; a refusal after a faint is proven live by REFUSE and DFAINTX's fault half).
* **Recoil at LOW HP, Jump Kick's miss cap and a recoil that would faint the user are proven by unit tests and mutants
  only** (`RecoilTests`, `RecordedRecoilTests` on the recorded look of a real battle; B36-B38). The one recoil rule played
  live is the cap on the HP a hit can take (RECOIL: the game charged `[3]` HP). Looked for this round and not found: a
  fixture with a recoil move at low HP. The saves start in only three battles (all against a Wurmple), and chaining wild
  battles from `ch13_r119_wedge.ss1` to wear the Marshtomp down stopped at Route 119's first scene ("roam: stuck: a scene").
* **Healing is played live once** (arm HEAL and the sweep's HEAL, one battle: Route 103's rival with two Potions the AI
  bought). The heal decision is the step-4 rule (a Potion-like item in a trainer's battle under `heal_below`, the foe not
  about to fall); which item, and healing a member that is not out, are not exercised.
* **The recoil's HP is an estimate** of the damage (a ROUGH sense since step 4.1, `rough_share`) and of the foe's max HP
  (since round 3 a typical Pokemon of its level, `foe_max_hp`): against a foe it would knock out it is 4.25 HP (3.75 by the
  species' base HP until round 2) where the game charged 3; a recoil that would
  faint the user is judged on that estimate. Since step 4.1 a move that would FINISH the foe (its rough damage at least the
  bar's share) is worth as the strongest move, so finishers compare by hit chance and recoil; "finishes" is the rough
  sense too, so a move a person thinks finishes it may leave a sliver (arm SWITCH's development run: the Mudkip's Water Gun
  told "finishes it" a turn before Joey's Machop fell).
* **The step-3 world brains still flee** every wild battle (their proofs stand); only the `battle` brain fights.
* Damage is an ESTIMATE (average IVs, no EVs, no abilities, held items or weather), and since step 4.1 only its ROUGH
  sense is used (to the nearest eighth of the foe's HP, give or take an eighth), to keep a catch alive, to charge a recoil
  and to see a finisher; since round 3 the foe in it is a typical Pokemon of its level, corrected by the hits seen on it
  (`_seen_factor`, kept within 0.4-2.5); the move worth itself is still type x STAB x power x hit chance.
* The ball is chosen by visible cues (step 4.1); "seems rare" is the AI's own count of the wild species it has met this
  run (the first meeting after 4 wild battles), not the game's encounter rates.

## The world and the navigator (build step 3)

The AI's world model and its own navigator (design draft §2.3 "world model / map memory", "navigator", §6 build step 3,
§10.4 "novelty only", §10.7 "the crop"; HUMAN-PLAY-DESIGN pillar 3 "roaming, never spinning"; RULING 35: the bot's
`map_path.py`, `walking.py`, `global_navigation.py` and `story/*` were read as teaching material only, and the purity
gate refuses every one of them). Framework-free: everything below sees the game through the hands' `Eyes.look()` and
presses through the pad, so the instrument counts every press as the AI's.

**The memory** (`world/memory.py`). It is told EVERY look the hands take (`Hands.watchers`), so what the eyes showed
during a scene, a menu or a battle is remembered too. Per map, in that map's own coordinates: every tile the 15 x 11
window ever showed, as the eyes reported it (blocked, water, tall grass, encounters, a ledge and its jump direction, a
door, a warp, elevation, behaviour), with the frame and the TILE THE PLAYER STOOD ON when it was first seen
(`TileFact.seen_from`): "it knows only what it saw" is a property of the memory itself, checked by every live arm.
Visits per tile; people and item balls seen; ways in LEARNED BLOCKED BY BUMPING, per tile AND side (since step 3.1;
since step 3.2 FORGOTTEN when a step gets the player in that way, and dropped when the tile's look changes);
door-looking tiles found CLOSED (reopened after NEWS a person could see since, or after 36,000 frames: the step-3.1
verifier's round; since step 3.2 the news is words never read before on the overworld, a map never stood on, a new
Pokemon by PID, where it was a count of the save's story flags); the map's EDGES, all four, learned only at a crossing SEEN (since step 3.1: the
coordinates alone say nothing a person sees, so before a crossing a tile past an edge is just a tile). Across maps: the WARP
GRAPH (`(map, tile) -> (map, arrival)`, learned when used, and the warp tile at or beside the arrival recorded as the
inferred way BACK, as a person knows the door they came out of), the CONNECTIONS (with their offset; known both ways),
and every map change, classified by what the looks between showed: a fade, the map loading or a settling position is a
WARP, a seamless change a CONNECTION; and by who caused it: the AI's own step or warp (the navigator says what it is
doing: `intend`), or a SCENE (Mom sending the player back upstairs). It never reads the map's layout or the ROM's map
data. Persisted as JSON lines (`<run_dir>/world.jsonl`, through `runlog.RecordFile`, the gate's file writer); a later
run starts from a file's last line (`AI_PLAYER_WORLD`, `read_world`, read mode only): arm ROUTE starts from the memory
of arm TOWN's walk.

**The navigator** (`brain/navigator.py`). A* over the memory: a known tile costs 1 (plus the personality's grass cost
while travelling: Story 2, Catcher and Trainer 0), an UNKNOWN tile 3 (optimistic: it may be walkable, so the plan
walks toward what has not been seen; dearer, so a seen way round is preferred), a wall, water or a tile someone stands on
is refused, a tile bumped from one SIDE costs 10 more from that side and is refused from it after a second bump (other
sides stay open: step 3.1), a LEDGE is entered only in its jump direction and lands one tile beyond it, and a warp or
a door is never walked THROUGH: it is USED on purpose (`use_exit`): stand next to it and press toward it, into the wall
behind it (a door in a front wall, stairs against the back wall, a mat at the bottom of a room, which warps when pressed
on while stood on). TURNING ROUND (straight back, or a U-turn) is charged ONCE per decision (since step 3.2; step 3.1
charged 4 tiles on the first step of EVERY replan, which walked laps): 4 tiles in WHERE to go (the explorer's scores) and
1 tile in the decision's first plan (a tie-breaker between ways of one length, never a reason to walk further). That plan
is FOLLOWED, redone (uncharged) only when the memory says it no longer goes (a wall seen, a bump, someone standing on it)
and dropped for a fresh one only when that is 4 tiles better (a shortcut come into view); a seeded noise per target (+0 to 25 %
per tile) varies the way between runs and targets, and now and then (15 %, seeded) a small DETOUR through a seen tile
beside it. WALKING: one tile at a time, the D-pad held in chunks of 8 frames with a look between them (back-to-back
holds of one button are one continuous hold, so the walk does not stutter): the save block's tile changes 8 frames into
a step and every 16 after (measured 2026-10-08 on `pokedex_done.ss1`). Every look can stop the walk: the player moved;
a map change began (a fade, the map loading: watched until the new map has settled); a battle or a scene began; or
nothing moved for 32 frames: a BUMP. A bump beside a person is a person in the way (a short wait, another way: never
learned); otherwise the tile is learned blocked and the plan goes round it from then on. Every hold names its gate
("walk up: (7, 2) -> (7, 1) (seen NORMAL), toward the ...; the player free"), pressed on a look of the overworld with
nothing waiting and no menu.

**Intents** (`Intent`, `Navigator.run`). Every intent has a FRAME BUDGET that progress does NOT reset, and its progress
is NOVELTY only (`Novelty`: a tile or a map first seen during the intent, a story flag newly set, a new Pokemon by
PID, more items, EXPERIENCE gained by a party Pokemon, by PID: the eyes now report each party Pokemon's total
experience, decoded from the bytes they already read; every novelty that is not a place is TOLD with its particulars
and the clock it moved: `[AI-WORLD] novelty at f71924: experience gained (PID 550a9be6: 441 -> 456): progress (the
intent's clock f71324 -> f71924)`). It ends with its goal reached, or `stuck:<reason>`: no novelty for 3,000 frames; one warp used 3
times with nothing new since its second use (a PING-PONG through one door); nothing left to try; a target already
found unreachable chosen again; a trainer battle (out of scope); or `budget:` when its frames run out. Interruptions:
a wild battle is fled (`skills/flee.py`), a scene is read through with A only on the eyes' waits (`hands/dialogue.py`
advance; a yes/no in a scene is answered NO: an explorer agrees to nothing it does not know). A scene met on the way to a
target counts against that target, and (since the step-3.1 verifier's round) against the TILE it began on when it put the
player somewhere else: two with no PROGRESS since the first (a story flag, a Pokemon, items, experience; a tile seen in
passing is not progress) give the target up and make the tile one the AI does not step on again in the intent (lifted
by progress). Since that verifier's second round a scene is also known by its WORDS (the first page it waited on): the
same words twice on one map, sending the player back, and EVERY tile that scene began on is given up (Littleroot's twin
guards two tiles: at most 3 push-backs before news, where per tile it was 4); and NEW WORDS heard in a scene that left the
player where it found them (May's mother, May: "Huh? Who... Who are you?") are PROGRESS (`Novelty.heard`, dated when the
scene ends), which makes the given-up tiles and the targets they cut off worth a try again; met ONCE more with the same
words and nothing new since, they are given up again at once.

**Where to go** (`brain/explore.py`). Candidates, every one a tile the AI has SEEN (an exit's stand tile included, since
step 3.1): the FRONTIER (seen walkable tiles beside unseen ones), ROADS (walkable tiles seen past an edge whose crossing
the AI has SEEN: step 3.1), DOORS (exits not used yet, by their LOOK), BACK (an exit known
to lead to a visited map: worth little, more while that map still has something unseen, which is how a seen-all house
is left by its door rather than its stairs), a ROUTE (an exit known to lead, through known links, to the intent's goal
map), GRASS and PEOPLE. Score = 10 x value - the walk to it + the pull away from where it came into this map (frontier
and roads only) + a seeded jitter < 1.5. The target is then a WHIM AMONG EQUALS (`pick`): every candidate within
`CHOICE_MARGIN` = 4 points (four tiles of walking) of the best is about as good, and the run's choices stream draws one,
the better more often (weight 1 + its lead over the margin's floor); a clear winner (a route to the goal: 100 points) is
chosen every time. That whim is a choice made STANDING (at the start, at a target reached); a target chosen WHILE WALKING
(the last one dropped as stale) keeps the HEADING (since step 3.2, `pick_on_the_move`): the best place ahead of the player
(in the half of the map it walks into) unless another beats it by more than `CHOICE_MARGIN`, with no draw and no jitter.
The PERSONALITY weights (taste, not a plan):

| | frontier | road | door | back | grass | people | away / tile | grass cost |
|---|---|---|---|---|---|---|---|---|
| Story | 1.0 | 4.0 | 0.8 | 0.15 | 0 | 0 | 0.3 | 2.0 |
| Catcher | 1.0 | 2.0 | 0.6 | 0.15 | 3.0 | 0 | 0.1 | 0 |
| Trainer | 1.0 | 2.0 | 0.8 | 0.15 | 2.5 | 1.5 | 0.1 | 0 |

NEVER IDLE: with nothing new in sight it WANDERS to the least-visited seen tile; the pauses it takes are short and have
a reason ("deciding where to go: the frontier at (14, 11) (...)", "taking in a new place: OLDALE_TOWN").

**Roaming** (`skills/roam_train.py`): over the seen tall grass and its rim, each training step the least-visited
neighbour (+ grass, + keeping the direction, + ways on, - dead ends, - within 2 tiles of a person, + jitter), NEVER the
tile it came from unless that is the only way (and when the only way on is a PERSON, it first waits up to 2 s for them to
step aside), and a HOP to grass not stood on yet once the best step is a tile stood on 3 times.
Metrics: TRAINING STEPS (steps that moved the player), ATTEMPTS (every training step pressed: the `roam ...` gates in
the action log, those a wild battle pre-empted included, counted apart as `interrupted` and resolved from where the
player stands once the battle is fled), the SPIN RATIO (steps that did not move, or moved back onto the tile of two
steps before) over the TRAINING STEPS (the stricter denominator; over the attempts too, for the record), the distinct
tiles, the most-visited tile, encounters met and fled. **Fleeing** (`skills/flee.py`): the battle's text
advanced on its waits; on the action menu, RUN by reading the 2 x 2 cursor (Right, Down, A on RUN); a TRAINER battle
returns its reason with nothing pressed on the menu.

**What the eyes added (read only).** The battle's ACTION menu (`eyes/screens.py` BATTLE_ACTIONS, `ui=battle_action`):
the player's controller function `gBattlerControllerFuncs[0]` NAMED by the symbol table (one new door,
`modules.game.get_symbol_name`: `HandleInputChooseAction` is static in two files and `get_symbol` returned the Safari
one, 0x081593D8, while the player's ran at 0x08057588) and `gActionSelectionCursor[0]`; a Safari battle is not this
menu. `gMain.callback2 == BattleMainCB2` names the scene "a battle" (its animations hold still up to ~80 frames, so the
stall detector gives it the named-scene allowance). Under `AI_PLAYER_FAULT_NO_CROP` the view now holds every tile of the
live grid (the CROP arm's fault).

**Proofs.** `gates/live_step3.py`: every launcher arm graded for PURITY (CLEAN, `ai_presses` == 2 x the pad's presses,
the pad's frames == the instrument's `real_frames`, every breach counter 0, `ai_bot_calls=0`), THE GAME by a second path
from the state the run left (`hands_harness.py truth`: save block 1's map and `pos`, its flags and variables, the game's
OWN counters `gameStats[GAME_STAT_STEPS / WILD_BATTLES / TRAINER_BATTLES]` XOR the key, `get_party()`), the state
asserted to be this run's, THE CROP on the AI's own memory and every target it chose, THE HANDS (every A a wait, a
menu confirm or a talk by its look; every walking hold on a look of the overworld, 8 frames; no catch-all idle), and
(since the verifier's round) THE GAME'S ANSWER to where the player stands (`gates/game_answer.py`, below), every arm
but TRN. Predictions were written into its docstring before the graded runs; evidence
`evidence/2026-10-08-step3-<ARM>.txt` (the final round's run; the table quotes it):

| arm | start | what happened (quoted from the evidence) |
|---|---|---|
| HOUSE | `house_2f_clockset.ss1` (the player's room, the clock set), goal LITTLEROOT_TOWN, Story | `TRUTH after (save block 1): map [0, 9] == LITTLEROOT_TOWN [0, 9] at [5, 9]; VAR_LITTLEROOT_INTRO_STATE 7 == 7 (the TV scene was played through)`; the memory: `('LITTLEROOT_TOWN_BRENDANS_HOUSE_2F', 'LITTLEROOT_TOWN_BRENDANS_HOUSE_1F', 'warp', 'ai'), ('LITTLEROOT_TOWN_BRENDANS_HOUSE_1F', 'LITTLEROOT_TOWN', 'warp', 'ai')`; 3,344 frames, 52 presses (8 A, each on a wait), `all 766 known tiles of 3 maps lie inside the 15 x 11 window of the tile they were first seen from`; THE GAME'S ANSWER: `hold Down: the ROM predicts 3 step(s), then a stop at [5, 13] (Normal, collision 1); the game: 3 step(s) ... -> agrees \| hold Left: the ROM predicts 5 step(s), then a stop at [-1, 9] (the map's edge, no connection); the game: 5 step(s)`, `rule out 5 of the 5 neighbouring tiles`; the fault claim [4, 9]: `Left: the ROM predicts 4 ... the game: 5 -> DISAGREES` |
| TOWN | `pokedex_done.ss1` (Birch's lab), goal ROUTE101, knowing nothing | `map [1, 4] (Birch's lab [1, 4]) -> [0, 16] (ROUTE101 [0, 16]) at [11, 19]`; `SYS_B_DASH False -> True: Mom's Running Shoes scene was played through on the way`; `('LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB', 'LITTLEROOT_TOWN', 'warp', 'ai', 'down'), ('LITTLEROOT_TOWN', 'ROUTE101', 'connection', 'ai', 'up')`, the offset `[0, 20]`; `the game's OWN step counter (gameStats[GAME_STAT_STEPS]): 576 -> 615 (+39) >= the AI's walking steps 39`; `every one of the 7 targets the AI chose was a tile it had SEEN`; 4,969 frames, 92 presses (the whim: the first town target east, (14, 18)); THE GAME'S ANSWER: `hold Down: the ROM predicts 1 step(s), then the map becomes [0, 9]; the game: 1 step(s) ..., map changed to [0, 9] -> agrees \| hold Left: ... 1 step(s), then a stop at [9, 19] ...; the game: 1 step(s)`; the fault claim [10, 18]: both DISAGREE |
| ROUTE | `route101_south.ss1` + its memory (TOWN's walk), goal OLDALE_TOWN | `the memory of the TOWN walk was LOADED ...: 3 maps`; `map [0, 16] (ROUTE101) -> [0, 10] (OLDALE_TOWN [0, 10]) at [11, 19]`, `Route 101's north edge, a CONNECTION going up`; `the road back south (to Littleroot, known from the loaded memory) was never chosen as a new road`; `every wild battle met was FLED: the game's own wild-battle count 10 -> 11 (+1) == the battles the AI met 1 == fled 1` (a battle met on this trajectory now: the flee is non-vacuous here too); `the party (get_party): [['Mudkip', 19, 28]] -> [['Mudkip', 19, 28]]: nobody fainted`; 2,083 frames, 108 presses; THE GAME'S ANSWER: `Down: ... 1 step(s), then the map becomes [0, 16]; the game: 1 step(s) ... -> agrees \| hold Left: ... 7 step(s) ...; the game: 7 step(s)`, `rule out 5 of the 5` |
| ROAM | `route101_south.ss1`, 150 steps, Catcher, knowing nothing | `150 training steps (want 150), spin ratio 1/150 = 0.006666666666666667 over the TRAINING STEPS (the stricter denominator ...); over every press 1/163 = 0.006135`; `the AI's attempts 163 == the roam ... presses in the action log 163; of them interrupted by a battle 13 == re-derived 13`; `RE-DERIVED from the looks' digests alone ...: 150 steps that moved the player, 1 reversals + 0 in place = 1 spins, 78 distinct tiles; the path from the digests == the AI's path: True`; `the game's OWN step counter: 621 -> 779 (+158), + 1 step in flight when the state was saved ... == the walk to the grass 9 (of 9 walk presses) + the 150 training steps`; `the game's OWN wild-battle count 10 -> 23 (+13) == the AI's encounters 13 == fled 13`; `the end tile by save block 1 [14, 5] == the AI's last path tile [14, 5]`; (the second round) `every press that did not move the player was PRE-EMPTED by a battle, not spun: 13 such presses, the battle on screen [16] pad frames after each ...; the player on the same tile and FACING the same way until the battle in every one ...; presses that left the player standing with NO battle: 0`; 16,646 frames, 399 presses; THE GAME'S ANSWER (deep in the grass): `hold Down: ... 1 step(s), then a stop at [14, 7] ...; the game: 1 step(s) \| hold Right: ... 3 step(s) ...; the game: 3 step(s)` (Up met a wild battle and was skipped), `rule out 8 of the 8` |
| CROP (fault) | the TOWN start and goal, `AI_PLAYER_FAULT_NO_CROP=1` | purity still CLEAN; `2641 of 3136 known tiles lie OUTSIDE the window of the tile they were first seen from (the real arms: 0)`; `the first target on LITTLEROOT_TOWN: a road at [11, -1] from [7, 17], first 'seen' from [7, 16]: inside that window: False (a road it could not have seen ...)`; (the second round) `TRUTH (save block 1): map [1, 4] (Birch's lab [1, 4]) -> [0, 16] (ROUTE101 [0, 16]) at [10, 19]`; the walk's length is only a note now, `NOT a discriminator: 26 walking steps and 2 decisions on the way (the real TOWN arm of this session, the same seed: 33 and 7)`; THE GAME'S ANSWER at its end (ROUTE101 [10, 19]): agrees, the fault claim disagrees |
| STUCK | `clock_room.ss1` (the clock NOT set), goal LITTLEROOT_TOWN: Mom sends the player back up | `explore: stuck: ping-pong: the warp 1:1\|7,1 used 3 times (f12992..f14154) with nothing new since its second use, f13590`; `no hang: it gave up by itself after 1519 of 12000 frames`; `the stairs used by the AI exactly 3 times ([12992, 13590, 14154]), the scene's warps back recorded as the scene's (2)`; `VAR_LITTLEROOT_INTRO_STATE 5 (5), FLAG_SET_WALL_CLOCK False`; THE GAME'S ANSWER (the second round): no walking line from (8, 3), so `LOCKED: each direction held 120 frames from the state left moves nothing and counts no step ... -> locked True` and `THE ARRIVAL by the ROM: the warp the AI used last [[1, 1], [7, 1]] ... lands on [1, 0] [8, 2] (Non-Animated Door), and the exit step [0, 1] leaves the player on [8, 3] -> agrees True`; `the AI pressed NOTHING from that arrival (f14154) on: none`; the fault claim [7, 3]: `by the arrival False, by walking False` |
| BUMP | `house_2f_clockset.ss1`, errands (0,4), (2,4), (0,4) | `BUMP: moving down from (1, 3) ... did not move the player: (1, 4) is learned blocked (the eyes showed IMPASSABLE_SOUTH_AND_NORTH, elevation 3; held 32 frames)`; `pressed toward (1, 4) once (the bump, f15383) and NEVER after it was learned (f15415)`; `errand 2, (0,4) -> (2,4): 4 steps (the only 2-step way is through (1, 4): avoided, round it in 4)`; WHY by a second path: `(1, 4) has collision 0 (the eyes call it walkable) and behaviour 'Impassable North and South'`; the end tile `[0, 4]` by save block 1; THE GAME'S ANSWER: `hold Down: the ROM predicts 3 step(s), then a stop at [0, 8] (the map's edge, no connection); the game: 3 step(s) ... \| hold Left: ... 0 step(s) ...; the game: 0 step(s)`, `rule out 4 of the 4` |
| BUMPR (revert) | the same, a COPY whose `learn_bump` remembers nothing (in-process) | `HARM: 94 bumps into the same tile (1, 4)`; `errand 1 was never done: the player ended at [1, 3]`; `goto: stuck: nothing new ... for 3008 frames`, `3123 of 6000 frames` |
| TRN | `trainer_battle_r116.ss1` (a trainer battle begun) | `explore: stuck: a trainer battle: out of scope for step 3 (a trainer cannot be fled, and fighting is step 4's battle decider)`; `NOTHING pressed on the battle's action menu`; 1 A, on the battle's opening text wait; 596 frames |
| XP (second round) | `route101_xp.ss1` (a wild battle won, the experience not yet given) + its memory, goto 120 errands between (6,15) and (7,15) | `the AI told ONE novelty in the whole intent, and it is the experience, by IDENTITY: ["novelty at f71924: experience gained (PID 550a9be6: 441 -> 456): progress (the intent's clock f71324 -> f71924)"]`; `the intent's CLOCK moved from its start f71324 to the experience gain f71924 ..., 600 frames on, once the battle was over`; `BEHAVIOUR: the intent ended 'stuck: nothing new' 3000 frames after the LAST novelty f71924 ...: 3600 frames after the intent's start`; `TRUTH (the framework's get_party, total_exp by PID): {'550a9be6': 441} -> {'550a9be6': 456}`; `the game's wild-battle count 12 -> 12`; `tiles learned 291 at the start, 291 at the end`; 3,600 frames, 137 presses; THE GAME'S ANSWER at (7, 15): `hold Up: ... 8 step(s) ...; the game: 8 step(s) ... \| hold Right: ... 4 step(s) ...; the game: 4 step(s)` |
| XPR (revert) | the same, a COPY whose `Novelty.update` ignores experience (in-process) | `HARM: with experience not novelty the intent never saw anything new: 'goto: stuck: nothing new ... for 3032 frames, the last at f71324: none ...'; novelty lines: none`; `A/B on the same fixture and seed: the intent lasted 3032 frames here and 3600 with the experience counted (XP): the gain alone moved the stuck verdict 568 frames later`; `the game DID give the experience here too (get_party): {'550a9be6': 441} -> {'550a9be6': 456}` |

`gates/test_world.py` (46 tests; the 7 added by the verifier's round and the 7 of its second round are in their sections below) drives the REAL navigator against `GridGame`, a grid model of the overworld that
reacts to the D-pad the way the measured game does (each class and its fault half in the file's docstring): the memory
learns only what was on screen (FAULT: the crop off learns tiles no window showed); A* refuses walls, people, ledges
sideways and warps, prices the unknown (FAULT: priced like a known tile, it plans straight through the unseen), and
seeded noise varies the path, never its length bound; a hidden wall is bumped ONCE and avoided on every later errand
(FAULT: not remembered, it walks in place against it for most of a minute); doors, stairs and mats are used and the
warp graph learned, a road is a connection with its offset and edges, a scene's warp is the scene's; the budget is not
reset by novelty, nothing new is stuck within its window, a stairs ping-pong is stuck at the third use, an unreachable
errand is stuck, never a loop; the real explorer's every target was seen, while the crop off beelines (the true
shortest walk onto the road tile it chose) to a road it could not see; Story picks the road, Catcher and Trainer the grass, Trainer the side with
people; the door just come out of is worth only `Weights.back` while the map has something to see; an exclusion belongs
to one map; never idle; roaming in an open meadow never steps straight back (3 seeds x 200 steps), and a two-tile spin
is measured as ~100 %; flee reaches RUN by reading the cursor and declines a trainer battle with nothing pressed.
`gates/revert_step3.py` breaks ONE rule of the real code per copy and runs `test_world.py` there (evidence
`evidence/2026-10-08-step3-REVERT.txt`, the final round: `28 mutants CAUGHT as predicted, 1 REDUNDANT ALONE as
predicted (each with its reason), of 29`; W20-W23 are the verifier's round and W24-W29 its second round, below): mutants CAUGHT by their predicted tests (the ledge's direction, exits
walked through, the unknown's price, the bump not remembered, the budget reset by novelty, no ping-pong rule, no novelty
window, every change a connection, `settle` waiting through an arrival scene, flee's cursor and trainer checks, a
target already unreachable chosen again, Story's road and Trainer's people weights, the step straight back while
roaming, the way just come in valued, an exclusion without its map, no wait for a person in the only way on), and 1
REDUNDANT ALONE with its reason (the guard
against decisions that let no frame pass: every decision path today lets a frame pass or ends the intent; it is the
backstop for a future one).

**The fixtures** (`gates/make_step3_fixtures.py`, button presses only, md5s pinned in `live_step3.py`):
`house_2f_clockset.ss1` is `clock_room.ss1` played on by the AI's own CLOCK skill (seed 3, 13:37: the house is closed
until the clock is set, which is exactly what STUCK runs into); `route101_south.ss1` and `route101_south.world.jsonl` are
`pokedex_done.ss1` played on by the AI's own navigator (TOWN's run): the state, and the memory it wrote.
`route101_xp.ss1` and `route101_xp.world.jsonl` (the second round, arms XP and XPR) are `route101_south.ss1` played on by
the AI's own errands (7,15), (5,15), (6,15) (the memory it wrote), then by TEST-SIDE presses (no memory write) to a
second wild battle on (5,15), fought with the first move and saved on the frame the foe's HP reached 0
(`route101_xp.build.json`: `"experience_at_battle_start": {"550a9be6": ["Mudkip", 441, 9]}`, played on after the save:
`"gained": {"550a9be6": [441, 456]}, "levels": {"550a9be6": [9, 9]}`).

**Found while building, and fixed:**
* `get_symbol("HandleInputChooseAction")` named the Safari controller's function: the action menu was never seen and
  the first wild battle stalled until the stall detector stopped it (900 frames). Now the eyes NAME the running function
  by its address (the step-3 door).
* Watching a warp waited for the player to be FREE, so a scene that starts on arrival (Mom on 1F) was watched through,
  warp back included, inside one `use_exit`: the ping-pong went uncounted and the intent ended "nothing new" 3,000
  frames later. `settle` now stops at the map change (mutant W9 reverts it; caught).
* An exit BACK into a building outscored the town's frontier (the "away" pull was added to it, and the frontier's value
  was too small for its usual 5-7 tile walk): the AI shuttled through May's house's door until the ping-pong rule
  stopped it. The pull now applies to frontier and roads only, the frontier is worth 1.33-2.33 x 10 tiles, and a back
  exit is worth more only while the map behind it has something unseen.
* A connection crossed from A to B was not known from B: on Route 101 the road south (Littleroot, just walked) scored as
  a new road. Connections are now known both ways.
* Roaming stayed inside one 20-tile patch (25 distinct tiles in 120 steps, spin ratio 3.3 %: dead ends and a person):
  the hop to unwalked grass, the dead-end and person penalties.
* A chosen target already found unreachable could be chosen again with no frame passing (found by the unit test's
  model): refused, and a guard against decisions with no frame passing.
* FOUND BY THE SEED SWEEP (below), after the first graded runs: Catcher seed 1 went lab -> town -> lab -> town for the
  lab's last unseen tile (behind a counter, out of reach) until the ping-pong rule stopped it ("stuck: ping-pong", 972
  frames), and Trainer seed 6 likewise through the lab's door. Two fixes: the way JUST COME IN is worth only
  `Weights.back` while the current map has something to see (and a back exit's bonus now grows with how much is left
  there, full at 10 things), and an excluded target is excluded on ITS map only (the key named no map, so a tile that
  failed in the lab was refused in the town too). Unit tests and mutants W17, W18 (caught); the seed-3 arms' trajectories
  did not move (every arm's frames and presses as before). The same sweep's ROAM plan met its limit closely (seed 6: 3
  spins in 151, all at the corner (2,13) / (4,13) where Route 101's boy wanders): the walk now WAITS up to 2 s for a
  person in its only way on and keeps 2 tiles from people (unit tests on a ring of grass, mutant W19); the ten seeds now
  spin 0 or 1 times in 150 steps. This moved arm ROAM's trajectory (seed 3: 78 distinct tiles, 13 battles fled).

## Step 3, the verifier's weak proofs (2026-10-08, second round)

The step-3 verifier passed every suite and broke no rule, and listed five WEAK PROOFS and three notes. Each weak proof
now has a proof that can fail (a unit test with its fault half, a mutant of the real code, a live check with its own
fault-test); the predictions were written into `gates/live_step3.py`'s docstring ("AFTER THE STEP-3 VERIFIER") before
the graded run, from in-process runs of the same code, and every arm met them (frames and presses included). Every
evidence file of this round says `working-tree digest sha256:1446987412c17a51` (`py -3.12 ai_player/gates/provenance.py`
recomputes it).

| weak proof (the verifier's words, shortened) | what was done | proven by |
|---|---|---|
| 1. CROP's beeline check depends on the seed: "step count alone does not separate cropped from uncropped" (an honest TOWN seed walked 26 steps, CROP's own total) | the walk's length is no longer a check of the CROP arm: a NOTE, labelled "NOT a discriminator". The two checks that separate stay, sharpened: tiles known from outside every window (the memory), and the first town target NOT SEEN, i.e. not inside the window of the tile it was first seen from (the decision record's `in_window` is "in the window NOW", which an honest target seen two steps earlier need not be: the sweep's TOWN seeds 4 and 6). `gates/rate_step3.py` measures both, seed by seed, on 10 TOWN and 10 CROP runs (CROP-SEP). The unit test's beeline is now "the true shortest walk onto the road tile it CHOSE" | CROP `the first target on LITTLEROOT_TOWN: a road at [11, -1] from [7, 17], first 'seen' from [7, 16]: inside that window: False`; `NOT a discriminator: 26 walking steps and 2 decisions on the way (the real TOWN arm of this session, the same seed: 33 and 7)`; RATE `CROP-SEP: every TOWN seed knows 0 tiles from outside a window and its first town target was SEEN: True; every CROP seed knows > 100 from outside and its first town target was NOT seen: True; => the two discriminators separate all 10 + 10 runs: True` (each seed's line in the file; `rate_step3.py` exits 1 if they do not) |
| 2. path variety came from per-tile noise, not choices: TOWN seeds 3 and 7 chose the same seven targets | `brain/explore.py` `pick`, a WHIM AMONG EQUALS: every candidate within `CHOICE_MARGIN` = 4 points (four tiles of walking) of the best is about as good, and the run's choices stream draws one, the better more often; a clear winner (a route to the goal) is chosen every time. Measured first on the model: with only the score's jitter, 8 seeds' first targets on one town all lay north (17..19, 11) | `test_world.py` ExploreTests: `test_a_whim_among_equals` (40 seeds pick all three near places, the best most often, never the place 10 points behind; a route always), FAULT `margin 0: every seed picks the same`; `test_seeds_choose_different_ways_on_the_same_town` (the model: first targets west and north), FAULT `every seed heads north`; mutant W23 CAUGHT. Live: TOWN seed 3's first town target is now east, (14, 18) (`33 and 7` steps and decisions). RATE (`evidence/2026-10-08-step3-RATE.txt`): `TOWN: 10 different target sequences in 10 seeds; the first exploring choice's headings, by map: {'0:9': ['left', 'right', 'up'], '1:4': ['down']}; seeds 3 and 7 chose the same sequence: False`, and the same False on every plan |
| 3. the truth's position is the memory the eyes read (save block 1 `pos`; the eyes require the player object to agree) | `gates/game_answer.py`, THE GAME'S ANSWER: from the state the run left, in a throwaway emulator, it PREDICTS from the ROM's static map data at the claimed map and tile (collision, behaviour, elevation by the game's own rule, warps, coord events that would run, connections; never the live grid the eyes read) what holding one direction does: "K steps, then a stop" or "K steps, then the map becomes M"; then it HOLDS it and counts what the game does: its own step counter and the map it LOADED (`gMapHeader` against the ROM's header). One clean line per axis; a line through grass that meets a wild battle is skipped; people within a tile of the line make it unclean. Its FAULT-TEST runs in every arm: the same probe claiming a neighbouring tile it rules out must DISAGREE. Found while building it: the run stops 8 frames into its last step, so the probe first lets the saved state run on with no input (a step in flight ends; BUMP read "Left: 0 predicted, 1 counted" before that) | every launcher arm but TRN (the table above): HOUSE, TOWN, ROUTE, ROAM, CROP and BUMP agree and rule out every neighbouring tile the player could stand on (5/5, 3/3, 5/5, 8/8, 3/3, 4/4); each fault claim disagrees (e.g. TOWN `[10, 18]: hold Down: the ROM predicts 2 step(s), then the map becomes [0, 9]; the game: 1 step(s) -> DISAGREES`); STUCK was INCONCLUSIVE and said why (Mom beside the player, the stairs above): answered in the second round (below). Not the screen: the step counter and `gMapHeader` are memory too, but they are the game's REACTIONS to presses, predicted from the ROM at the claimed tile |
| 4. novelty counts tiles, maps, flags, PIDs and items, not XP (§10.4) | `Novelty` counts EXPERIENCE GAINED: a party Pokemon's total experience rising, by PID (a torn party read is neither a loss nor a gain). The eyes report it (`MonSummary.experience`, the growth substructure @4 of the bytes `_party` already decodes: no new read) | `test_world.py` NoveltyTests (`experience gained (1 Pokemon)` at f40; FAULT: experience ignored, the same looks are nothing new); `test_eyes.py` PartyDecoderTests compare it with the framework's `total_exp` for all 24 orders; mutant W20 CAUGHT. No step-3 arm gained experience then (it only flees): unit-proven only, until the second round's arm XP (below) |
| 5. ROAM's spin denominator `attempts` counted only the steps that moved (150), the action log holds 163 roam presses | `skills/roam_train.py`: ATTEMPTS = every training step PRESSED; a step a battle (or a scene) interrupted is counted as `interrupted` and resolved from where the player stands once the battle is fled (a step that moved the player into the battle is a training step, and "the tile it came from" is kept); the SPIN RATIO is over the TRAINING STEPS (the stricter denominator), over the attempts reported too. The grader RE-DERIVES the metrics from the looks' digests alone and checks them against the game's own step counter | ROAM `the AI's attempts 163 == the roam ... presses in the action log 163; of them interrupted by a battle 13 == re-derived 13`; `RE-DERIVED from the looks' digests alone ...: 150 steps ..., 1 reversals + 0 in place = 1 spins ... == the AI's path: True`; `621 -> 779 (+158), + 1 step in flight ... == the walk to the grass 9 ... + the 150 training steps`; `test_world.py` RoamTests `test_steps_that_ran_into_a_battle_are_counted` on `EncounterGame` (both timings of an encounter); mutants W21, W22 CAUGHT |

The notes: the three REVERT evidence files lacked the code line: `revert_step11.py`, `revert_step2.py` and
`revert_step3.py` now write it. `host/eyes.py`'s docstring said "the same doors (no new one)" and then named the new
door: it now says the step-3 door is new and what it is used for. The seed-9 citation: see "Which seed-9 files are
which" (step 2's section).

## Step 3, the verifier's second round (2026-10-08)

The step-3 verifier re-ran every suite on the second round's tree (all PASS, no rule broken) and listed five more WEAK
PROOFS. Each is answered below by a check that can fail, with its fault half (a unit test, a mutant of the real code,
or a live revert arm). Predictions for this round are in `gates/live_step3.py`'s docstring ("AFTER THE STEP-3
VERIFIER'S SECOND ROUND"), written from in-process runs before the graded run; the first graded run met all of them
but one fault-test of the INSTRUMENT (below, and in the docstring's "AFTER THIS ROUND'S FIRST GRADED RUN"); the second
and the final run met all (11 of 11 arms, every frame and press count as predicted). Every evidence file of the final
run says `working-tree digest sha256:2652e886e7844ce4` and `predictions: sha256:418a0dd9eb6bcace` (`provenance.py`
and `predictions_ref`'s one-line recompute check them).

| weak proof (the verifier's words, shortened) | what was done | proven by |
|---|---|---|
| 1. CROP never asserts that save block 1's map is ROUTE101; it rests on the navigator's own outcome string | `grade_CROP` checks the truth like TOWN: save block 1's map before (the lab) and after (ROUTE101) | CROP `TRUTH (save block 1): map [1, 4] (Birch's lab [1, 4]) -> [0, 16] (ROUTE101 [0, 16]) at [10, 19]: the faulted run did reach the goal` |
| 2. experience as novelty is unit-proven only: no live run shows an intent's novelty clock reset by an XP gain | (a) the navigator now TELLS every novelty that is not a place, with its particulars and the clock it moved (`[AI-WORLD] novelty at f...: experience gained (PID ...: a -> b): progress (the intent's clock fX -> fY)`; places are left out: they come at nearly every step); `hands_harness.py truth` reads each party Pokemon's PID and `total_exp` by the framework (`party_exp`). (b) a new fixture, `route101_xp.ss1` (`make_step3_fixtures.py --only xp`): the AI's own errands on Route 101 (its memory kept beside the state), then TEST-SIDE presses to a SECOND wild battle, saved on the frame the foe's HP reached 0, the experience not yet given (the first battle levelled the Mudkip up: a stats box the AI cannot read yet, see the limits). (c) arm XP: goto 120 errands between two KNOWN floor tiles, so the only novelty is the experience and the intent ends "stuck: nothing new"; its revert XPR: the same from a COPY whose `Novelty.update` ignores experience | XP `the AI told ONE novelty in the whole intent, and it is the experience, by IDENTITY: ["novelty at f71924: experience gained (PID 550a9be6: 441 -> 456): progress (the intent's clock f71324 -> f71924)"]`; `TRUTH (the framework's get_party, total_exp by PID): {'550a9be6': 441} -> {'550a9be6': 456}`; `BEHAVIOUR: the intent ended 'stuck: nothing new' 3000 frames after the LAST novelty f71924 ('experience gained (1 Pokemon)'), at f74924 ...: 3600 frames after the intent's start: the experience gain bought it 600 frames`; `NO PLACE was new ...: tiles learned 291 at the start, 291 at the end`; purity CLEAN, 137 presses. XPR `HARM: ... for 3032 frames, the last at f71324: none ...; novelty lines: none`; `A/B on the same fixture and seed: the intent lasted 3032 frames here and 3600 with the experience counted (XP): the gain alone moved the stuck verdict 568 frames later`. Unit: NoveltyTests `test_the_navigator_tells_the_experience_and_the_clock_it_moved` and its FAULT `test_fault_without_experience_the_clock_never_moves`; mutants W24, W25 CAUGHT |
| 3. STUCK's game answer is INCONCLUSIVE; only the loaded map header is checked, so its end tile [8, 3] has no behavioural confirmation | measured first: on that state NO press moves the player (Mom's `GoUpstairsToSetClock` scene: `lockall`, a `msgbox` waiting; every direction held 600 frames: nothing). `gates/game_answer.py` gained two answers for a state with no walking line: LOCKED (each direction held 120 frames: the game counts no step, the tile and the map do not change) and THE ARRIVAL (`--after-warp`: the ROM's warp table says where the warp the AI used last lands, and the decomp what the game does next: on a door or a non-animated door the player faces south and the exit task walks one step, `src/overworld.c` GetAdjustedInitialDirection, `src/field_screen_effect.c` SetUpWarpExitTask). The grader also checks the AI pressed nothing after that arrival, and an INCONCLUSIVE answer with nothing else now FAILS. Found by the first graded run: the fault claim (7, 3) had one walking line, "Up: 0 steps, then a wall", which a locked player also "agrees" with: a walking answer now needs a trial that predicts a STEP (`walking_agrees`) | STUCK `(1) LOCKED: each direction held 120 frames from the state left moves nothing and counts no step (Up: 0 steps, moved False, map changed False; ...) -> locked True`; `(2) THE ARRIVAL by the ROM: the warp the AI used last [[1, 1], [7, 1]] (pre-registered [[1, 1], [7, 1]]) lands on [1, 0] [8, 2] (Non-Animated Door), and the exit step [0, 1] leaves the player on [8, 3] -> agrees True`; `(3) the AI pressed NOTHING from that arrival (f14154) on: none`; `FAULT-TEST: the probe claiming [7, 3] instead -> by the arrival False, by walking False`. Unit: GameAnswerTests `test_the_exit_step`, `test_a_walking_answer_needs_a_step`; GraderTests `test_an_inconclusive_answer_with_nothing_else_fails`; mutants W26, W28, W29 CAUGHT |
| 4. no way to check the predictions were pre-registered before the graded run (the tree is uncommitted) | every evidence file's header now carries `predictions: sha256:... of live_step3.py's docstring`, read at the START of the run (`predictions_ref`; its docstring gives the one-line recompute): equal means the predictions in the file are the ones that run read. WHAT IT CANNOT SHOW: that they were written before a first look at a graded run. Only a commit made before the run can, and this round's worker may make no commit (no state-changing git); the other currency is a re-run by someone else after reading them, which the verifier did | each `evidence/2026-10-08-step3-<ARM>.txt`: `predictions: sha256:<digest> of live_step3.py's docstring (... characters), read at the start of this run` (the final run's digest, beside the working-tree digest on the `code:` line). NOT FIXED: the ordering proof (a commit) |
| 5. ROAM's spin ratio does not count the 13 presses a battle pre-empted: a choice of definition | the grader now SHOWS each such press was pre-empted, not spun, from the action log: the battle on screen within the press's own two chunks (pad frames), the player on the same tile AND facing the same way until it (a press the game took turns the player at once), one battle per press; and asserts 0 presses that left the player standing without a battle. The definition is the design's (draft §4 "walking in place is never a training action", §7 criterion 9 "spin ratio under 2% of training steps"); the strictest reading (every press that did not move the player a spin) is reported as a NOTE, not a criterion | ROAM `every press that did not move the player was PRE-EMPTED by a battle, not spun: 13 such presses, the battle on screen [16] pad frames after each (want <= 16 ...); the player on the same tile and FACING the same way until the battle in every one (else: none), 6 of them pressed AWAY from the way it faced ...; 13 distinct battles for 13 presses (one each), of the 13 met; presses that left the player standing with NO battle: 0`; NOTE `counting every press that did not move the player as a spin, 14/163 presses = 0.0859`. Unit: GraderTests `test_a_preempted_press_and_three_that_were_not`; mutant W27 CAUGHT |

FOUND while building the XP fixture: a level-up's STATS BOX (after "MUDKIP grew to LV. 9!") is a screen the eyes do
not read as a wait. The AI watched it and gave up after 900 frames, as the stall detector should (`flee: ...
STUCK: nothing on screen changed for 900 frames while watching: a battle`); reading it is the battle decider's (step
4), and the XP fixture's battle gives experience without a level (checked by its builder).

## Step 3.1: the step-3 adversarial review's findings, fixed (2026-10-08)

The review (CHANGELOG 2026-10-08, "Open: step 3.1") found that the explorer used knowledge no screen shows and walked in
ways a person would not. Each finding below has a fix in the AI's code and a proof that fails when the fix is reverted (a
unit test with its fault half in `gates/test_world.py`, a mutant in `gates/revert_step3.py`, and where it can be played,
a live arm of `gates/live_step3.py`). Predictions were written into `live_step3.py`'s docstring ("AFTER STEP 3.1")
before the graded run, from in-process development runs of the same code (seed 3) and a development seed sweep. Every
evidence file of this round says `working-tree digest sha256:b4c70735d1599fa2` and `predictions: sha256:3197e6dad9d2d6d6`
(every suite was re-run on that tree: `check_purity.py`; the five unit suites; `live_step0.py --arms A,A2,B,C`,
`live_step1.py`, `live_step2.py`, `live_step3.py` (14 arms, every frame and press count as predicted); `revert_step3.py`;
`rate_step3.py`).

| finding | the fix | proven by |
|---|---|---|
| 1 (HIGH) the explorer knew where a map ENDS from negative coordinates (`outside`: x < 0 or y < 0), scored those tiles as ROADS, and only on the top and left | `world/memory.py`: `outside` and `road_side` use only edges learned at a crossing SEEN, all four sides (`learn_edges`); an older memory re-learns its edges from its recorded crossings when read. Before a crossing, a tile past an edge is frontier like any tile | `test_world.py` ShiftTests: the same memory with every coordinate +50 gives the same choice (6 seeds, before and after a crossing); a tile past an edge never crossed is no road; MemoryTests (edges at a crossing, also from an old memory). Mutant W30 (the coordinates rule back) CAUGHT. Live TOWN / ROUTE `NO ROAD BEFORE A CROSSING ... (roads chosen: none; first crossings by map: {'0:9': 66750, '0:16': 66750}; too early: none)` |
| 2 (HIGH) stale frontier targets: A-B-A reversals (TOWN "(11,7)->(12,7)->(12,6)->(11,6)", ROUTE "(17,9)->(18,9)->(17,9)") | `brain/navigator.py`: a frontier target with nothing unseen beside it any more (or grass already walked) is dropped at once, the next chosen on the move (`stale_reason`); the plan's first step costs `TURN_BACK_COST` = 4 for turning straight back or completing a U-turn (`turn_costs`, in `astar` and the explorer's `distances`), cleared on arrival | ReversalTests (12 seeds of the town model): `<= 3` reversals and no stale target walked onto; FAULTS: no turn-back cost `>= 15`, no stale drop `>= 8` and every frontier target walked onto. Mutants W31, W32, and W42 for the grader, CAUGHT. Live: HOUSE, TOWN, ROUTE graded `REVERSALS ... 0 on the 41 steps the looks showed (want <= 1, pre-registered)` (TOWN; HOUSE 0 on 10, ROUTE 0 on 35; 23 and 22 targets dropped as stale). RATE: the exploring plans 11 reversals in 2,119 steps (bound 2 a run, met). (A "68 in 2,259 on the step-3 code" quoted here before was a scratch measurement no file of the tree reproduces: replaced by the sweep's REVERT A/B in its evidence, 89 in 2,795 with the two rules reverted, and the bounds tightened: "Step 3.1, the verifier's round" below) |
| 3 (MED) a repeating scene: a "scene" result kept its target, the ping-pong counted warps only | `Navigator._scene_met`: every scene met on the way to a target is counted for it; at `SCENE_REPEATS` = 2 with nothing new since the first, the target is given up (`stuck: ... cannot be reached (a scene stopped the way there 2 times ...)` for an errand) | SceneTests (a trigger that pushes the player back; FAULT: until the novelty window, `>= 8` scenes) and the pure rule (something new since the first scene keeps the target). Mutant W33 CAUGHT. Live arm SCENE (`littleroot_twin.ss1`, the twin's NeedPokemon trigger): `the scene met on the way to (10, 0) exactly TWICE, then the target given up`, `it gave up after 2471 frames`, `on [0, 9] at [10, 2] (pushed back ...), VAR_LITTLEROOT_TOWN_STATE 0`, purity CLEAN; its revert SCENER: `3 times ... ended only on the novelty window`, `3570 frames here, 2471 with the rule (SCENE): the rule saved 1099 frames` |
| 4 (MED) one bump = a permanent wall from every side (`bumped` keyed by tile, persisted) | `MapMemory.bumped` keyed by (tile, direction); `step_from` adds `BUMP_RETRY_COST` = 10 after one bump from that side and refuses it after `BUMP_GIVE_UP` = 2; other sides stay open; standing on a tile no longer clears its bumps; old files read back | WalkTests: a one-way tile (IMPASSABLE_SOUTH_AND_NORTH in the model) reached from its side and crossed east-west (FAULT: every side walled, stuck); the only way on retried once and given up after the second refusal (FAULT: one bump closes a way that opened); a hidden wall bumped at most once per side. Mutants W34, W35 CAUGHT. Live BUMP: `exactly one way in learned blocked by bumping: {'1:1': [((1, 4), 'down')]}`, `THE ONE-WAY TILE CROSSED FROM ITS OPEN SIDES: errand 2 ... [('right', (0, 4), (1, 4)), ('right', (1, 4), (2, 4))] ...; errand 3, back: [('left', (2, 4), (1, 4)), ('left', (1, 4), (0, 4))]`; BUMPR (no memory) still 94 bumps |
| 5 (LOW) warp tiles from the ROM's warp-event table, which nothing on screen shows | `host/eyes.py` no longer reads a map's warps: a tile's `warp` is its LOOK (`eyes/view.py` EXIT_BEHAVIORS, every look the game warps on but the Union Room's); an exit is used the way it looks (`navigator.EXIT_PRESS`: an arrow by its arrow, a door from below); one that does not open is remembered CLOSED (`MapMemory.closed`); where one leads is the warp graph, as before | FrameworkFreeTests (no host file reads `.warps`; FAULT: a planted read caught; the exit looks); ExitTests (a closed door tried once and never by a later intent, FAULT: tried again; an arrow mat by its arrow). Mutants W36, W37, W38 CAUGHT. Live arm EXITS (`gates/exit_looks.py`, test side): `every look the game warps on ... is in the eyes' table (missing: none), and no warp tile of the ROM with such a look is unseen (none)`, `all 29 warp tiles LOOK like exits`, FAULT-TEST without the doormat look `leaves 14 of their warp tiles unseen`; `1193 of 1313 warp tiles on 518 maps`. `live_step1.py`'s tile truth is now the framework's names for the exit looks, all arms PASS |
| 6 (LOW) the crop check imported VIEW_* from the eyes | `gates/window.py`: the screen's window as literals (7, 5, 5) from the hardware and the decomp; `live_step3.py`, `rate_step3.py` and `test_world.py` check against it | WindowTests: with the eyes' window widened to 9 the gate still flags a tile seen 8 columns away. Mutant W39 (the eyes' window back in the gate) CAUGHT |
| 7 warp-target grading | audited every gate (`game_answer.py`'s docstring): no grade compares a post-warp position with a raw warp target; THE ARRIVAL applies the exit step and is checked against save block 1's position after the transition | STUCK now also requires `the RAW landing [8, 2] is that position: False` (save block 1 says [8, 3]); unit `GameAnswerTests.test_the_exit_step`, mutant W26 (as before) |
| 8 an exit's stand tile could be UNSEEN (`_approaches` over `distances`) | `explore._approaches`: the stand tile must be known and walkable | ApproachTests: every candidate a seen walkable tile (a door whose only stand tile is unseen is no target yet; random memories of the explore model); FAULT: an unseen stand tile becomes a target. Mutant W40 CAUGHT |
| 9 the spin metric | `RoamReport`: the back-and-forth spin ratio (reversals + in place over training steps: the criterion < 2%) AND the strict non-moving-press ratio (in place + pre-empted over every press, reported), with `reversals`, `in_place`, `preempted`, `strict_ratio` | RoamTests on `EncounterGame` (both timings: the pre-empted presses are exactly the interrupted ones that did not move). Mutant W41 CAUGHT. Live ROAM `BOTH RATIOS ... BACK-AND-FORTH spin ratio 0.006667 = (1 reversals + 0 in place) / 150 training steps (the criterion, < 2%); STRICT non-moving-press ratio 0.079755 = (0 in place + 13 pre-empted by a battle) / 163 presses (reported, NOT a criterion ...)`, the same re-derived from the looks; RATE: every seed's back-and-forth ratio < 2% |
| 10 the sweep and the reverts on the final tree | re-run | `rate_step3.py`: `90 of 90 runs as intended` (HOUSE, TOWN, ROUTE, ROAM, STUCK, TOWN-Catcher, TOWN-Trainer, CROP, SCENE, 10 seeds each); `revert_step3.py`: see its evidence (W0 control, 42 mutants CAUGHT, W13 redundant alone as before) |

**Found while measuring, and fixed before the predictions were written:**
* Dropping stale targets ALONE made reversals worse on the town model (28 in 677 steps against 12 in 788 before): a
  target dropped on the move was replaced by one behind as often as ahead. The plan's first step now costs
  `TURN_BACK_COST` = 4 tiles when it turns straight back or completes a U-turn, and arriving at a target clears the
  heading (a person turns round freely where they stopped; the turn-back cost is for a plan changed on the move). Both
  rules: 2 in 730. The model A/B is `ReversalTests` and its two fault halves.
* With roads no longer known from the coordinates, the development sweep's TOWN-Catcher seed 8 went house -> town ->
  house until the ping-pong rule stopped it: Littleroot's far frontier (16 tiles) scored below the door just come out of
  (worth `Weights.back`). The way just come in is now no option at all while the map has somewhere new to go (mutant
  W43; `ExploreTests.test_not_straight_back_where_it_came_from`).
* The twin's scene takes ~1,100 frames a round, so with the scene rule off (SCENER) it runs 3 times in the novelty window,
  not the 4 first predicted for the revert arm; the check asks for more than the rule's 2.
* The CROP fault arm no longer beelines to a "road": with the whole map on screen and no crossing seen, its first town
  target is a door it could not have seen, and it reaches Route 101 by another way. Its discriminators (tiles known from
  outside every window; a first town target NOT SEEN) still separate it from TOWN on every seed (the sweep's CROP-SEP).

## Step 3.1, the verifier's round (2026-10-08)

The step-3.1 verifier passed every suite and broke no rule, and listed nine weak proofs and notes. Each is answered below by
a check that can fail, beside its fault (a revert arm on the same start and seed, a unit test with its fault half, a
mutant of the real code). Predictions are in `gates/live_step3.py`'s docstring ("AFTER THE STEP-3.1 VERIFIER"), written
from in-process development runs, a development sweep and a development pass of the driver on the new arms (its files
discarded) of the same code, before the graded run. Every evidence file of this round says `working-tree digest
sha256:2b316cce90537f5e` (`py -3.12 ai_player/gates/provenance.py`), and live_step3's `predictions: sha256:730f4e3bc7d59610`;
every suite was re-run on that tree (`check_purity.py`, the five unit suites, `live_step0.py --arms A,A2,B,C`,
`live_step1.py`, `live_step2.py`, `live_step3.py` with all 22 arms at the predicted frames and presses, `revert_step3.py`:
50 mutants caught and W13 redundant alone, `rate_step3.py`). The figures below are quoted from that evidence.

| weak proof (the verifier's words, shortened) | what was done | proven by |
|---|---|---|
| 1. finding 2's live reversal grades do not tell the fixed code from the reverted one at seed 3 (the revert shows 1 reversal on each of HOUSE, TOWN, ROUTE; the bound was 1), nor the sweep's per-run bound of 2 on ROUTE | the seed-3 bound is that trajectory's own count, 0 (`REVERSALS_SEED3`; another seed: 1); a second live check, NO STALE TARGET WALKED ONTO (`stale_arrivals`: the next decision made standing on a frontier target with no stale drop between, everything beside it seen by the memory's own first-seen frames); three REVERT ARMS with both rules off; the sweep's bounds 1 a run and 1 per 100 steps a plan | HOUSER, TOWNR, ROUTER each 1 reversal (the review's own two examples among them) and stale targets walked onto, against 0 and 0 on HOUSE, TOWN, ROUTE; the sweep's FINDING-2 revert: every exploring plan over the bound; unit `GraderTests.test_stale_arrivals_from_the_action_log_and_the_memory`, mutant W49 |
| 2. the baseline "68 reversals in 2,259 steps" is a scratch measurement, in no evidence file | the sweep runs the A/B itself: the same plans and seeds from a COPY with finding 2's two rules reverted, the same metric, written into its evidence with a pre-registered prediction | `evidence/2026-10-08-step3-RATE.txt` REVERTS: FINDING-2 (the figures there, quoted in "Where it is now") |
| 3. finding 1's live check "never fires" (roads chosen: none) | it now also requires the case it is about: targets past a map's REAL edge (the ROM's size, test side) before a crossing of THAT edge (per edge: ROUTE's loaded crossing of Route 101's bottom edge says nothing of its top), each chosen as what it looks like; its live fault is the revert arm EDGER | TOWN and ROUTE: frontier targets past the top edge, no road; EDGER: the road (10,-1), the same check FAILS; `GraderTests.test_targets_past_an_edge_before_a_crossing_of_that_edge`, mutants W50 (a crossing of any edge counted for all), W51 (no non-vacuity) |
| 4. SCENE is a scripted errand (one scenario replayed; "1 different target sequences in 10 seeds"), not targets the explorer chose | measured first: the explorer from the twin's fixture gave one frontier tile up after 2 scenes, then chose the next tile behind her, 3 to 5 scenes until the novelty window (seeds 1-6), and seed 4 met her 4 times for ONE target (a tile seen in passing excused the scene). Fix in `brain/navigator.py`: a scene is also counted for the TILE it began on when it put the player elsewhere; twice with no PROGRESS since the first (a flag, a Pokemon, items, experience) and the tile is not stepped on again in the intent (`scene_walls`, lifted by progress); a new arm SCENEX and its revert, and the sweep's SCENE-EXPLORE plan and SCENE-TILE revert; SCENE is labelled as one scripted scenario | SCENEX: the twin 2 times on each of (10,1) and (11,1), her targets the explorer's own, both tiles given up and never stepped on after, then it looks elsewhere; SCENEXR: 3 times on one tile; sweep SCENE-EXPLORE every seed and the revert's seeds over 2; `SceneTests` explorer, progress and lift tests, mutants W44, W45, W48 |
| 5. replays, not replications | the sweep's seed 3 is labelled the live arm's trajectory replayed (REPLAY section, frames compared with the live evidence of the same tree); real replications through the launcher at another seed | TOWN9, ROUTE9 (seed 9); the sweep's nine other seeds |
| 6. live_step0 and live_step2 not re-run by the verifier | all suites re-run on the final tree (the evidence of each carries its digest) | `evidence/2026-10-08-step01-{A,A2,B,C}.txt`, `evidence/2026-10-08-step2-*.txt` |
| 7. ROUTE seed 3 meets no wild battle: fleeing proven live only by ROAM | ROUTE9 through the launcher meets one and flees it (the check requires a battle); the sweep's ROUTE FLEE section, seed by seed | ROUTE9; RATE ROUTE FLEE (7 of 10 seeds meet a battle, each fled and counted by the game) |
| 8. a door found closed stays closed for good | `world/memory.py`: reopened once one of the eyes' story flags is newly set since it was found closed, or after `CLOSED_RETRY_FRAMES` = 36,000; the navigator tells it | `ExitTests.test_a_closed_door_is_tried_again_once_the_story_moves_on`, `..._after_a_while`, mutants W46, W47 |
| 9. the README's command block is stale | rewritten (79 tests, 51 mutants, 22 arms, 10 plans and the reverts) | this file |

## Step 3.1, the verifier's second round (2026-10-08)

The re-verification passed every suite, found no rule broken, and listed eight weak proofs. Each is answered below by a
check that can fail beside its fault (a revert arm on the same start and seed, a unit test with its fault half, a mutant
of the real code: W52-W61, and W28, W48 follow the code they break). Predictions are in `gates/live_step3.py`'s docstring ("AFTER THE STEP-3.1 VERIFIER'S GRADED
RUN", "AFTER THE STEP-3.1 VERIFIER'S SECOND ROUND", "AFTER THIS ROUND'S FIRST GRADED RUN") and, since this round, as
NUMBERS in its `PREDICTED` table, every one machine-checked against the run (a number that misses FAILS its arm). Every
evidence file of the final run names `working-tree digest sha256:b94ddc58ca95f8f7` (live_step3's also `predictions:
sha256:1ec90653b2a3c781`, its docstring and `PREDICTED` table), and the folder's top level holds no other (`py -3.12
ai_player/gates/provenance.py --check-evidence`: 95 files, PASS). Final run: live_step3 33 of 33 arms PASS, 124 of 124
pre-registered numbers held; revert_step3 60 mutants caught and W13 redundant alone, of 61; rate_step3 100 of 100 runs.

| weak proof (the verifier's words, shortened) | what was done | proven by |
|---|---|---|
| 1. FINDING 5's guard only checks syntax: a planted `getattr(location, 'warps')` passed it, and so would a raw read of gMapHeader's events | (a) the static check also flags a STRING CONSTANT naming the table (`getattr`, `hasattr`, a dict key) and the framework's `MapWarp`, and does not fire on a docstring or comment that mentions `location.warps`; (b) a BEHAVIOURAL guard, `gates/warp_reads.py`: the REAL eyes look at the game on 7 starts with every `context.emulator.read_bytes` call recorded (the one funnel of every read the eyes can make: their own, `read_symbol`, `MapLocation`), against the address range of EVERY map's warp array in the ROM (444); its three plants, each in a copy: the attribute, the verifier's getattr, and a raw read of the array followed from `gMapHeader`'s events pointer | arm WARPREAD: 0 reads overlapping a warp array on every start; 5 of the 7 starts stand on a map with warps (Route 101 has none); the recorder sees each map's MapEvents struct read, one pointer from its warp array; each plant caught on all 5 (`plant_raw_caught 5`), the static check flags the attribute and getattr plants and NOT the raw read (the scan is what sees it). Unit: `test_fault_the_verifiers_getattr_plant_is_caught`, `test_a_mention_in_a_docstring_or_a_comment_is_not_a_read`; mutants W56 (the verifier's plant), W57 (the string rule off) |
| 2. A PRE-REGISTERED PREDICTION DID NOT HOLD AND THIS IS NOT SAID ANYWHERE (ROUTER: "4 walked onto", measured 5) | said, in the docstring: the five targets, and that WHY the development count was 4 is not established (it was not kept; the copy and seed replayed give 5). And made impossible to repeat unsaid: every number pre-registered is in `PREDICTED` and `check_predictions` compares it with the run; a miss fails the arm, the summary counts them | each evidence file's "PRE-REGISTERED NUMBERS" check and its `MEASURED` line; the summary's count. Unit `test_a_pre_registered_number_that_does_not_hold_fails_the_arm` (ROUTER's own 4 against 5); mutant W60. THIS ROUND'S FIRST GRADED RUN USED IT: SCENEX9 failed on its numbers alone (14,462 predicted, 15,959 played), which found the CLOCK (row 9) |
| 3. FINDING 2's live check separates fixed from reverted by a single event per arm (0 reversals against 1) | each revert arm now says which discriminator its claim RESTS ON: the stale targets walked onto (0 with the rules, several without); the reversals are reported, and at seed 3 still break the real arm's bound (labelled one event); the A/B again at seed 9 (TOWN9R, ROUTE9R); arm F2AB adds every pair | F2AB: on all 5 pairs, seeds 3 and 9, 0 stale targets walked onto with the rules and > 0 without; in all 0 against 23; reversals 1 against 6 (TOWN9R 1 = TOWN9 1: no per-arm claim). The frequency is the sweep's REVERT A/B: 11 reversals in 2,119 steps and 0 walked onto, against 89 in 2,795 and 252 |
| 4. FINDING 4 has no live revert arm: BUMP's crossing check never ran against the reverted rule | arm BUMPSR: BUMP's start, errands and seed from a copy where one bump walls every side (W34's edit); BUMP's own check (`one_way_crossed`) graded on it; BUMP8 / BUMPSR8 the same A/B at seed 8 (of seeds 1-10 only 3 and 8 walk down into the one-way tile: measured) | BUMPSR: the same one bump `((1, 4), 'down')`, BUMP's check FAILS on it, errands 2 and 3 walked ROUND in 4 steps each, never onto (1, 4); the A/B: 2 + 2 steps straight through with the rule, 4 + 4 without; BUMPSR8 the same at seed 8 |
| 5. the twin guards two tiles, so the explorer meets her 4 times; SCENEX's budget was chosen to end outdoors; what happens after the twin is not graded by the game's answer | (a) a scene is known by its WORDS (`navigator.scene_words`: the first page it waited on): the same words that sent the player back twice give up EVERY tile that scene began on; (b) SCENEX runs to its OWN end (20,000 frames). That showed what the old budget hid: after the twin the explorer met May in her house (the story moved on: VAR_LITTLEROOT_TOWN_STATE 1, at which the twin lets the player pass) and stopped there "nothing new", because meeting May sets no flag the eyes call progress. (c) NEW WORDS heard in a scene that left the player be are PROGRESS (`Novelty.heard`, dated when the scene ends: May's scene runs 3,500 frames), which makes the twin's tiles and the targets they cut off worth a try again; met once more with the same words and nothing new since, she is given up again at once. (d) `game_answer.py` answers the end: on Route 101 Birch's rescue scene LOCKS the player, so a trial the game does not step asks LOCKED, and THE ARRIVAL across a map edge (`--after-connection`) | SCENEX (the graded run, the host's clock in the afternoon): "explore: done: explore to ROUTE101" in 14,343 frames; the twin sends the player back 3 times before any news (`{'(10, 1)': 2, '(11, 1)': 1}`; counted per tile it was 4), May's mother's "Oh, hello. And you are?" makes her tiles worth a try again (`her push-backs between the news [0]` on this clock), May's "Huh? Who... Who are you?" and the twin's "Um, hi!" (`VAR_LITTLEROOT_TOWN_STATE 0 -> 2`) let the player pass; THE GAME'S ANSWER: LOCKED (Birch's rescue), and the arrival across Littleroot's top edge from (11, 0) lands on (11, 19) == save block 1. SCENEX9: 3 before any news (`{'(10, 1)': 1, '(11, 1)': 3}`), once more after the mother's words (`[1, 0]`), then through, 15,959 frames. At the pinned clock (arm CLOCKS) SCENEX plays the morning's 16,293 frames with `[3, 1, 0]`: the twin rules hold at all 8 instants. SCENEXR (words rule off): 4 push-backs before any news, 7 in all, never past her; SCENENR (news not progress): 3 push-backs, stuck in May's house at state 1, the twin never tried again. Sweep: SCENE-EXPLORE every seed 2..3 push-backs before news, <= 1 after each; 6 of 10 reach Route 101 (the other 4 stop by the ping-pong rule at Brendan's house, "Known limits"); SCENE-WORDS revert: 10 of 10 over 3; SCENE-NEWS revert: every seed that reaches Route 101 stays off it. Unit: SceneTests (same words on a two-tile gap: 3; FAULT by tile only: 4; different words: two scenes; news lifts her, once more gives her up; FAULTS news not progress: 2, once not enough: 4), GameAnswerTests, GraderTests; mutants W52-W55, W58, W59 |
| 6. stale text: `eyes/view.py` says a closed door is never chosen again; the README's command block omits `--only twin` | both corrected | `eyes/view.py` EXIT_BEHAVIORS' comment (story flag or `CLOSED_RETRY_FRAMES`); the command block above |
| 7. older evidence files with other digests sit in `ai_player/evidence` | every suite re-run on the final tree, and the step-2 seed-9 replication (`--evidence-tag step2-seed9-at-step3`), `revert_step2.py` and `revert_step11.py` too; every file of an EARLIER tree moved, unchanged, to `evidence/archive/<its digest>/` (`archive/README.md` lists them); a check that can fail: `provenance.py --check-evidence` | its FAULT half, run before the move: `555 evidence files ...; 0 name this tree's digest ... -> FAIL`; after: PASS (the report's figures) |
| 8. the re-runs are replays of the same trajectories | said so (README "Known limits", CLAUDE.md rule 8); more replications at another seed through the launcher: HOUSE9, SCENEX9, BUMP8, each with its revert A/B at that seed where there is one (TOWN9R, ROUTE9R, BUMPSR8). And measured what "replay" means here: the game reads the HOST'S CLOCK (row 9), so a launcher run is the same run only within a window of the clock | HOUSE9, BUMP8, SCENEX9, TOWN9R, ROUTE9R, BUMPSR8 (their `PREDICTED` numbers from their own development runs) |
| 9. (FOUND by this round's own graded run) SCENEX9's trajectory changed between its development and graded runs, same code, fixture, seed and presses | CAUSE, MEASURED by an in-process A/B (the throwaway emulator's clock set test side; a development run, its figures in the docstring): the game reads its real-time clock (mGBA's RTC = the host's) at every map load, and berry growth draws random numbers: SCENEX9 plays 14,462 frames with the clock from 09:00 to 12:01 and 15,959 from 13:37 or 20:00; the host's clock offset by 6 hours, or the run slowed 4 ms a frame, changed nothing within a window. The graded form of that A/B is arm CLOCKS (SCENEX9 14,462 at 06:00 and 11:00, 15,959 at 12:30, 18:00 and the next morning, 14,647 from 2026-10-10). Every in-process run now PINS the cartridge's clock (`hands_harness.py --game-clock`, `live_step3.GAME_CLOCK`); arm CLOCKS runs every launcher arm at 8 instants over 12 days | CLOCKS: ROAM, SCENEX and SCENEX9 change with the clock (pre-registered `CLOCK_SENSITIVE`), the other 13 do not; those three register no launcher frames (their pinned numbers under CLOCKS), and their claims hold at every instant (the twin's push-backs, Route 101 reached, ROAM's 150 steps under 2% spins). Unit `test_the_clock_arm_registers_frames_only_where_every_clock_agrees`, mutant W61 |

## Step 3.2: the step-3.1 adversarial review's human-likeness findings, fixed (2026-10-08)

The review of step 3.1 (CHANGELOG 2026-10-08, "Open: step 3.2") found walks a person would not walk that the step-3.1
metrics could not see. Each finding has a fix in the AI's code and a proof that FAILS when the fix is reverted: a unit test
with its fault half (`gates/test_world.py`, 108 tests) and a mutant (`gates/revert_step3.py` W62-W75, plus W32, W37, W46
moved onto the new code), and where it can be played a live arm or a sweep revert. The numbers were PRE-REGISTERED from a
development pass of each driver on the same AI code, before the graded runs (`live_step3.py`'s docstring "AFTER STEP
3.2" and its `PREDICTED` table, `LAP_BOUNDS`; `rate_step3.py`'s `LAP_SWEEP_BOUNDS`, `LAPS_REVERT_OVER`,
`WHIM_REVERT_DROP`, `FINDING2_PLANS_OVER`). Every evidence file of the final run names `working-tree digest
sha256:3ea1b655920e8c61` (since build step 4 those files are in `evidence/archive/3ea1b655920e8c61/`, unchanged), live_step3's also `predictions: sha256:b801550cbda71ae9`. Final run: live_step3 34 of 34 arms
PASS, 154 of 154 pre-registered numbers held; revert_step3 73 mutants caught and W13 redundant alone, of 74; rate_step3 100
of 100 runs as intended, every bound met, every revert as predicted; and on the same tree `check_purity.py` PASS, the five
unit suites OK, `live_step0.py --arms A,A2,B,C`, `live_step1.py` (21 arms), `live_step2.py` (17) and its seed-9 replication
(16) PASS, `revert_step2.py` (39 caught, 5 redundant alone) and `revert_step11.py` PASS; `provenance.py --check-evidence`:
96 files, PASS.

| finding | the fix | proven by |
|---|---|---|
| 1 (HIGH) the turn-back cost charged on EVERY replan: each step forward made turning back dearer again, and the AI walked LAPS (SCENEX: 8 steps round a room where 2 would do) | `brain/navigator.py`: turning round (straight back, or a U-turn, now also one the plan completes on its own second step) is charged ONCE per decision: `TURN_BACK_COST` (4) in WHERE to go (the explorer's scores), `TURN_ROUND_COST` (1) in the decision's first plan, a tie-breaker between ways of one length. That plan (`Plan`) is FOLLOWED (`_next_step`): redone uncharged only when the memory says it no longer goes, dropped for a fresh one only when that is `PLAN_SWITCH_MARGIN` (4) better (a shortcut come into view). MEASURED before choosing the plan's charge (in-process, pinned clock, 10 seeds of HOUSE, TOWN, ROUTE, SCENEX): with 4 tiles charged once in the plan, the plan still bought its way round the charge (a U round one tile where turning back was 2 steps, and a step FORWARD then straight back) | `LapTests`: Littleroot's corner as SCENEX seed 3's memory held it (8 seeds: 2 steps, no lap; FAULT, the step-3.1 rule: a lap, 10 steps); three ways of one length, 20 seeds, none turns round (FAULTS: the plan replaced at every step; no turn charge); a shortcut come into view taken (FAULT: never switched). Mutants W62, W63, W74, W32 CAUGHT. Live SCENEX `the walks to 43 targets: 116 steps walked against 114 on the shortest KNOWN ways, 2 beyond them`; its revert arm SCENEXL (the step-3.1 rule, in-process) `162 steps walked against 114 ..., 48 beyond them, the worst target door [2, 3] (25 steps from [4, 4] to [2, 3], shortest 3)`: SCENEX's lap check FAILS on it. RATE `LAPS A/B ... steps beyond the shortest known ways REVERTED 342, REAL 6; runs over {'laps': 0, 'excess': 4, 'worst': 2} REVERTED 13 of 60 (predicted >= 8), REAL 0`. SCENE-EXPLORE now reaches Route 101 on 10 of 10 seeds (`SCENE-EXPLORE, AFTER THE TWIN`) |
| 2 (HIGH) the reversal metric counts only A-B-A and U-turns: laps score 0 | `gates/live_step3.py`: `laps` (back on a tile 4..12 steps later on the same map with NOTHING NEW between: no tile first seen by the memory, no novelty told), `target_walks` / `known_shortest` (the walk to each target from the tile decided on against the shortest way over what the memory knew by its end, bumps per side included; a walk with a detour reported, not graded), `lap_report`, `check_laps` against the pre-registered `LAP_BOUNDS` on TOWN, ROUTE, SCENEX, SCENEX9 (no lap; at most 2 steps beyond on a target, 4 in all: the only such steps measured are a walk round someone in the way, whom the memory does not know); reported on every other walking arm; per run in the sweep (`LAP_SWEEP_BOUNDS`); arm CLOCKS checks SCENEX's bounds at every instant | GraderTests `test_laps_in_a_walk`, `test_the_shortest_known_way`, `test_the_walk_to_each_target_against_the_shortest_known_way` (each rule with a fault: W70 nothing-new not asked, W71 tiles not yet seen used, W72 bumps ignored, W73 nothing graded passes, W75 a detour graded), `test_the_clock_arm_...` (a lap bound broken at one instant fails). Live TOWN `34 steps walked against 34 ..., 0 beyond them`, ROUTE `28 ... against 28`, SCENEX9 `128 ... against 126, 2 beyond` (the walk (14, 9) -> (11, 0) past the twin, 14 for 12), CLOCKS `SCENEX [('10-08T06:00', 0, 2, 2), ... ('10-20T12:00', 0, 2, 2)]`; RATE every lapped plan within the bounds (`SCENE-EXPLORE: laps 0, 6 steps beyond the shortest known ways over 1047 walked (the worst target 2)`) |
| 3 (MED) a bump never forgotten after walking through that way | `world/memory.py` `forget_bump` (the navigator calls it when a step got the player into a tile going `d`: that tile's bump for `d` is deleted, and told); `MapMemory.absorb` drops every bump of a tile whose look changed (`take_dropped_bumps`, told) | WalkTests `test_a_bump_is_forgotten_when_the_way_lets_the_player_through` (a tile that refused, then let the player through: the next errand straight through it, 4 steps; FAULT not forgotten: round, 8), `test_a_tile_that_looks_different_drops_its_bumps`, and `test_the_only_way_on_...` now expects the retried way's bump forgotten (0, where step 3.1 kept 1). Mutants W64, W65 CAUGHT. No live arm walks back through a way it bumped |
| 4 (MED) indecision: 22 of 23 targets dropped as stale and re-picked on a whim | `brain/explore.py` `pick_on_the_move`: a target chosen WHILE WALKING (`Navigator.choosing_on_the_move`) is the best place AHEAD (`ahead`: in the half of the map the player walks into, `Navigator.heading`) unless another beats it by more than `CHOICE_MARGIN`; no draw, no jitter (`candidates(jitter_on=False)`). The whim stays for choices made standing | HeadingTests (the heading kept within the margin, the clearly better taken; 20 seeds choose the same place on the move and several standing). Mutants W66, W67 CAUGHT; the town model's reversal fault half (no turn cost AND the whim on the move: 12 reversals in 662 steps, against 0 in 429). RATE `WHIM A/B ... the walk kept its heading REVERTED 402 of 662 (61%), REAL 592 of 671 (88%; predicted at least 15 points more); reversals REVERTED 25 in 1295 steps, REAL 2 in 1182`. Live, reported per arm: TOWN `TARGETS CHOSEN ON THE MOVE ...: 23; the first step after each kept the heading 20, turned aside 3, turned straight back 0` |
| 5 (LOW) doors reopen on a hidden count of story flags | `world/memory.py` `_news`: a closed door is retried after NEWS a person could see since it was found closed: words never read before on the overworld (`heard`), a map never stood on, a Pokemon of the player's never seen (by PID); or after 36,000 frames. `news`, `heard` persist | ExitTests `test_a_hidden_story_flag_alone_does_not_reopen_a_door` (FAULT: the flag count again, W69), `test_a_closed_door_is_tried_again_after_news_a_person_could_see` (FAULT: no reopening on news, W46), `test_news_is_what_a_person_could_see` (new words, a new map, a new Pokemon reopen; the same words, a battle's words, a story flag do not). No live arm meets a closed door |

**Three restatements, found by the development pass and pre-registered before the graded run** (`live_step3.py`'s
docstring says each, with the reason):
* `REVERSALS_PER_RUN` is 2 (was 1), and the sweep's per-100 bound is over the exploring plans together: a target behind is now
  reached by turning back where step 3.1 walked a lap (invisible to the reversal metric), and a run that explores two rooms to
  their end turns back at the end of each (RATE TOWN-Trainer seed 9). The discriminator of the step-3.1 finding 2 is unchanged:
  `FINDING-2 A/B ... REVERTED 89 reversals in 2875 steps (3.10 per 100, bound 1.0), 257 stale targets walked onto; REAL 6 in
  1677, 0 walked onto`.
* SCENEX's twin check asks for ONE target of the explorer's own (was two): kept on the move, the same target may be tried
  again until the per-target rule gives it up (RATE seeds 2 and 8: (10, -4) twice).
* SCENEXR no longer claims "never got past her": turning back, the words-reverted copy meets May too, and her news lifts the
  twin; the rule's harm stays the push-back (`4 without` against `3 push-backs with the rule`). ROUTE9's flee non-vacuity is
  over the pair ROUTE and ROUTE9 (`1 + 0 wild battle(s) met, each fled`: ROUTE at seed 3 meets one now). CLOCKS: SCENEX9 is no
  longer clock-sensitive (13,148 frames at every instant), so its launcher numbers are registered.

## Step 3.2, the step-4 verifier's weak proofs (2026-10-08)

(SUPERSEDED in part by the next section: the verifier's second round ruled the "finding 4" and "findings 3 and 5" rows
below NOT enough, and both were then fixed and proven live; the SCENE-EXPLORE row is now bounded. Kept as the record of
that round.)

The step-4 verifier re-ran step 3.2 too. Its walking code is UNCHANGED in this round (every pre-registered trajectory held:
`live_step3.py` 162 of 162 numbers); only the graders changed, and the claims below are restated where they said more than
the evidence. Pre-registered from the verifier's own recomputation of SCENEX and SCENEXL (seeds 3 and 7) and a development
sweep (`rate_step3.py`, its file moved out of the evidence folder), before the graded runs.

| the verifier said | what changed | the evidence (final tree) |
|---|---|---|
| "the new CYCLE check (`laps`) does not tell the fix from the revert ... SCENEXL's evidence says 'laps 0 with, 0 without' ... Every one is exempted by 'new tile between: True'" | `live_step3.rings`: back on a tile 4..12 steps later having walked ROUND (every tile between visited once), WHATEVER was seen on the way; an out-and-back (A B C B A) is a turn back, not a ring. Bounded at 1 a run (`LAP_BOUNDS`, `LAP_SWEEP_BOUNDS`) and 4 over the sweep's 60 lapped runs; the LAPS revert must ring at least 20 times in 8 runs. `laps` stays, for what it is: a lap with NOTHING new seen on the way. Tests `test_rings_in_a_walk`, `test_a_ring_that_saw_new_tiles_is_counted_by_the_report`, the CLOCKS test's ring half; mutants W76 (an out-and-back counted), W77 (`laps`' exemption: the verifier's point) CAUGHT | SCENEXL `4 RINGS [('1:1', [5, 3], 12), ('1:1', [5, 2], 12), ('0:9', [11, 4], 10), ('1:3', [1, 2], 10)]` and its A/B `RINGS ... 0 with, 4 without; laps with nothing new between 0 with, 0 without (every round the reverted code walked showed a new tile: that check alone cannot tell the two apart)`; SCENEX, TOWN, ROUTE, SCENEX9 `0 RINGS`; CLOCKS: SCENEX 0 rings at all 8 instants. RATE `LAPS A/B ... RINGS ... REVERTED 36 in 14 runs (predicted >= 20 in >= 8 runs), REAL 2 in 2 runs (predicted <= 4)` |
| (the same, honestly measured) the real code is not ring-free | the sweep's two real rings (SCENE-EXPLORE seeds 1 and 6, once each) were read move by move: each spans a TARGET that vanished (the frontier past the twin "cannot be reached that way", then a door; a frontier whose tiles were all seen on the way, then the way back), and every leg was the shortest known way to its own target ((12, 15) to the door (7, 17) in 7, the shortest; (5, 3) to (7, 2) in 3, the shortest). That is why the bound is 1 a run, not 0 | the reverted code rings within ONE target's walk (SCENEXL: "back (7, 2)" reached by a 12-step round) and where the steps-beyond metric sees nothing (RATE: ROUTE seed 9 reverted, 6 rings, 0 steps beyond any target) |
| "steps-vs-shortest is measured per DECISION, and the AI re-decides every 1-3 steps ... near 0 by construction wherever targets churn" | `live_step3.journeys`: a target chosen standing and every target re-picked on the move after it, joined, against the shortest known way from where it began to where it ended. REPORTED, not bounded: an exploring walk ends where it stopped, not at a destination, and the real code's journeys walk beyond that way too (a nook looked into and left). Test `test_journeys_join_the_targets_chosen_on_the_move`, mutant W78 | SCENEX `JOURNEYS ... 9 graded (20 targets), 80 steps walked against 60 ... 20 beyond`; RATE `JOURNEYS' steps beyond REVERTED 516, REAL 250 (predicted more reverted)`. The graded discriminators are the rings and the per-target steps (`REVERTED 342, REAL 6`) |
| finding 4 "only partly fixed: targets still churn" (25 stale drops in 42 steps) | nothing: the fix asked for was the HEADING after a re-pick on the move, and that is what changed (`kept the heading REVERTED 61%, REAL 88%`). A frontier target is dropped when its tiles are seen, so walking toward unseen ground re-picks often by design; the churn itself is a known limit (below) | RATE TOWN `stale_dropped` 23 at seed 3 (PREDICTED, held) |
| findings 3 and 5 are proven only by unit tests and mutants | unchanged, and said: no live arm walks back through a way it bumped or meets a closed door | `revert_step3.py` W64, W65, W69, W46 CAUGHT |
| SCENE-EXPLORE's reversals were "settled by exempting the plan" and rose to 2.91 per 100 steps | unchanged, and said: SCENE-EXPLORE is reported, not bounded (a scene sends the player back by design). Listed in seeds 1 and 6 (`live_step3.path_reversals` on their replays): 5 of their 8 reversals are inside the houses and the lab (4 one step in and straight back, 1 a U-turn), 3 in the town (1 U-turn, 2 one step and back); why each was taken was not read | RATE `SCENE-EXPLORE: 41 reversals in 1411 steps over 10 seeds (2.91 per 100 steps)`; the exploring plans together `6 reversals in 1677 steps (0.36 per 100 steps; bound 1.0)` |

## Step 3.2, the step-4 verifier's FAILURE and second round of weak proofs (2026-10-09)

The step-4 verifier's re-run found ONE checklist failure: "Step 3.2 finding 4 (MEDIUM, 'the AI changes target almost every
step (22 of 23 dropped as stale)') is NOT fixed ... my own recomputation of ... SCENEX shows the churn is still there: '47
walks ... decisions on the move 35 of 47'; walk length per decision 'mean 2.55', with 28 of the 47 walks a single step. Its
visible cost is not bounded". The cause: a frontier tile at the screen's edge is seen past at the very next step (the
screen scrolls), so every frontier target went stale within a step or two and every stale target was a NEW decision. Step
3.2 had made that decision keep the heading; it was still a decision a step.

THE FIX, in the AI's code (`brain/explore.py` carry_on, `brain/navigator.py` run): a frontier (or grass) target the walk
has made stale is CARRIED ON by the same decision to the place that took its place: the nearest frontier within
`CARRY_RADIUS` (3) tiles of it, on its side of the player, at least a tile further the way the unseen lay beside it and at
most a tile aside (a frontier sliding along the screen's edge is another place). No draw, no new decision, no thinking pause,
and the decision's plan stays uncharged. A new decision is made, on the move with the heading, only when nothing of it is
left there, or when another place is worth more than one tile of walking more (`CARRY_SWITCH_MARGIN`); every carry-on
TELLS where the step-3.2 rule would have gone instead (`carry_note`), and every refusal why. The margin was MEASURED, not
chosen: 0 walks like the step-3.2 rule with fewer decisions; at 2 the Catcher's and Trainer's walks grew; carried on with no
margin at all (or at `CHOICE_MARGIN`), the TOWN walk grew a third, a whole street swept past the road out of town.

Found by this round's development sweeps and fixed too (both make the walk more a person's; each with a test, a mutant and
a sweep): a DOORMAT is one way out (`world/memory.py` mat_tiles: the mat's other tile was taken for "an exit not used yet",
and 2 of 10 explorers left May's house by it before going upstairs to May), and a way back to a map SEEN ALL OF is no option
while another leads somewhere with something left to see (`brain/explore.py` not_back_to_seen_all: once a doormat counted as
one way out, the stairs to a floor seen all of, a step away, outscored the doormat four steps away, and the AI went up and
down until the ping-pong rule ended the intent).

| the verifier said | the fix | proven by (final tree) |
|---|---|---|
| FAILURE: finding 4 "NOT fixed ... 'decisions on the move 35 of 47' ... 28 of the 47 walks a single step. Its visible cost is not bounded: JOURNEYS" | the decision CARRIED ON (above) | `ChurnTests` (the place straight beyond; a place two tiles aside is another; something clearly better ends it; never beside or behind the player; the town model, 12 seeds: about a decision per 8 steps where the step-3.2 rule made one a step, the walks no more than a tenth longer; FAULTS); mutants W79-W81, W85; live CHURN bounds (`CHURN_BOUNDS`, pre-registered) on TOWN, ROUTE, SCENEX, TOWN9, ROUTE9, SCENEX9 and at every clock instant (CLOCKS), and the revert arm SCENEXC: SEE "Everything on ONE tree" BELOW FOR THE GRADED NUMBERS; the sweep's CHURN A/B (`rate_step3.py`) |
| "Steps-vs-shortest per target is close to vacuous wherever targets churn" | with decisions carried on, a decision's walk is many steps long, so the steps beyond its shortest known way are measured over real walks; and the VISIBLE COST, every journey's steps beyond the shortest known way, is now BOUNDED (`CHURN_BOUNDS` journey_share, `CHURN_SWEEP_BOUNDS`), over EVERY journey: with a decision a step nearly every journey held a detour (drawn per decision) and went ungraded, which flattered the step-3.2 rule (its graded journeys walked 168 of its 338 TOWN steps) | the CHURN checks; the sweep's CHURN A/B predicts the real code's journeys no dearer than the revert's |
| "`laps` ... cannot tell the fix from the revert ... Rings carry the whole discrimination" | `laps` stays a safety bound (no lap with nothing new seen) and says so; RINGS now count one loop once, and the bound is on LAP RINGS (`lap_ring`: a ring with a leg walked beyond the shortest way to its own target), every ring reported: the carried-on decisions walk EXCURSIONS (into a room up one column, out by the next, each leg the shortest way to its own target) | `GraderTests.test_a_lap_ring_has_a_leg_walked_round` (W82, W83); SCENEXL's lap check FAILS on its lap rings; the sweep's LAPS A/B on lap rings |
| findings 3 and 5 "proven only by unit tests and mutants ... No live arm walks back through a bumped way or meets a closed door" | live arms on the AI's own memories with ONE thing planted, test side (`make_step32_fixtures.py`): FORGET / FORGETR, REOPEN / REOPENR (no early map gives the AI either case to learn itself: the README's "Known limits") | FORGET: the retry into (0, 5), "forgotten", errand 4 straight through (2 steps) and the end tile by save block 1; FORGETR: 6 steps round. REOPEN: the reopen line names the twin's words, May's door used only after it, VAR_LITTLEROOT_TOWN_STATE 0 -> 2, ROUTE101; REOPENR: stuck, May never met |
| "SCENE-EXPLORE has 2.91 reversals per 100 steps and its journey excess is not bounded" | bounded, pre-registered (`SCENE_EXPLORE_REVERSALS_PER_100` 3.5, `SCENE_EXPLORE_JOURNEY_SHARE` 0.45) | RATE |
| "revert_step3.py writes its top-level evidence file even on a subset run" (two files of an earlier tree lost) | a subset writes beside the system's temporary files, never into `evidence/`; the step-4 verifier's round's files were archived BEFORE any run of this round | `evidence/archive/a14d81a107a65b76/` (114 files), `evidence/archive/README.md` |
| "My re-runs of the in-process sweeps ... are determinism replays, not replications" | said where it applies: each sweep's seed 3 is the live arm replayed; the other seeds are the sample | RATE's REPLAY section |

Restated, not loosened (each found by the development sweeps, written down before the graded runs): the twin after news is
checked at most once ON EACH TILE (`once_a_tile_after_news`: one seed met her twice on (10, 1) before any news and on (11, 1)
only after it, and the rule gave each up at its first meeting; the old "once in all" check failed it, W87); the graders that
read decisions also read the places a decision was carried on to (`stale_arrivals` W86, `edge_targets`, `check_crop`,
SCENEX's "the explorer's own targets").

## Known limits of step 3

* **(Step 4.1 round 3) A journey's steps beyond the shortest known way are RE-TARGETING, not walking**: split, the walk to
  each target is the shortest known way (0 to 1 % of the steps beyond it on every plan over 50 seeds; bounded,
  `WALKING_SHARE_MAX` 0.04), and the rest is the explorer changing its target when one goes stale (seen past, nothing left
  there, met) or another place is clearly better. HOUSE's 0.26 and SCENE-EXPLORE's 0.35 are mostly rooms walked into,
  looked over and left (a journey that ends next to where it began). Nothing reduces that re-targeting except a different
  explorer (one that sees a room whole from its door, as a person does, would be a change to the eyes' window, not to the
  walk): not built. A 10-seed pooled journey share is noisy on ONE code (TOWN 0.07 to 0.20 across seed sets), so its bounds
  sit well above the typical value, and on every plan but TOWN-Trainer the step-4 walk's journeys equal the real ones within
  that noise: no journey bound tells those two walks apart there (the WALK A/B's `BOUND` lines say so per plan).
* The navigator walks; no brain yet CHAINS a walk and a skill (walk to the nurse, then heal): that is step 5's goals.
  The world brains end at their goal map, their errands, their roaming steps or `stuck:`.
* Elevation is not planned over: a tile the eyes call walkable but the game refuses (an elevation step, a one-way
  tile) is learned by BUMPING. Since step 3.1 per SIDE: a one-way tile such as (1, 4) is crossed from its open sides
  (BUMP's errands 2 and 3), and a wall the eyes call floor is bumped at most once from each side tried (up to four
  bumps for a hidden wall approached from everywhere, where step 3 took one). A side bumped once is tried again only
  when every other way is dearer by 10 tiles; twice, never. The one-way look (IMPASSABLE_*) is not read as a cue yet.
  Since step 3.2 a bump is FORGOTTEN once a step gets the player into that tile that way (and every bump of a tile whose
  look changes is dropped): unit-proven (WalkTests, mutants W64, W65) and, since the step-4 verifier's second round, live
  (arm FORGET and its revert FORGETR), on a memory whose bump was PLANTED test side: no early map gives the AI a way that
  refuses it once and lets it through later (a bump next to a person is the person's, never learned).
  A side refused twice is never pressed again, so it is never walked through and never forgotten that way: only a
  changed look lifts it (a way that opens later with no change of look stays closed from that side).
* A map's EDGES, all four, are known only after a crossing is SEEN (step 3.1); until then a tile past them is just a
  tile, explored as frontier. So the explorer has no pull toward a town's exit as such: it leaves by the frontier it
  sees there (Littleroot's road north is frontier until crossed). A memory written before step 3.1 learns its top and
  left edges again from its recorded crossings when it is read.
* Exits are known by their LOOK (step 3.1): every look the game warps on but the Union Room's exit (its behaviour,
  MB_BRIDGE_OVER_OCEAN, is the bridges' too). A door-looking tile that did not open is remembered CLOSED until there is
  NEWS a person could see (since step 3.2: words never read before on the overworld, a map never stood on, a new Pokemon by
  PID; step 3.1 counted the save's story flags, which nothing on screen shows) or 36,000 frames pass (unit-proven, and
  since the step-4 verifier's second round live: arm REOPEN, May's door remembered closed (PLANTED test side: on the maps
  of Littleroot, Oldale, Petalburg and Routes 101-104 the ROM's only exit-looking tiles with no warp are three in the back
  wall of each of Oldale's and Petalburg's Pokemon Center 2F, and two mats of a prototype flower shop map (a scan of the
  ROM's layouts this round; whether the AI could reach and press the Pokemon Centers' was not tried)), reopened by the
  twin's words, and its revert REOPENR). Any new words count, a sign's too: a person who learns something may try the door
  again, and it is tried once and closed again if nothing changed.
  The grid model's walk-on warps start at
  the step's attempt; the game's at the step's end (the navigator's warp records are by the exit it USED, either way).
* Reversals are graded on the AI's own steps as the looks confirmed them (`live_step3.py` walk_path); a U-turn round a
  single blocked tile counts as one even when it was the only way. Roaming sweeps a patch in serpentines, which the
  same metric would call U-turns: roaming keeps its own spin criterion (A -> B -> A and walking in place). Since step 3.2
  a target behind is reached by TURNING BACK (where step 3.1 walked a lap the reversal metric could not see), so a run
  that explores a room to its end turns back there and the metric counts it: the per-run bound is 2 and the sweep's
  per-100 bound is over the exploring plans together. LAPS (back on a tile 4..12 steps later with nothing new between)
  and the steps beyond the shortest KNOWN way per target are graded beside it (`lap_report`). That shortest way is over
  the memory's tiles and bumps; people are not in the memory (they move), so a step round someone in the way counts as
  steps beyond it (the bounds allow 2 on a target, 4 a run: the measured cause of every such step in the sweep).
* The TOWN and ROUTE check "no road before a crossing" is met with no road chosen at all (once a crossing is seen, the
  road's side is a KNOWN connection, so its tiles are "back" or "route", not "road": the kind "road" is in practice for a
  memory whose edge was learned without its link). Since the step-3.1 verifier's round the check also requires the case
  it is about (targets past a map's real edge, by the ROM's size, before a crossing of THAT edge: TOWN 5, ROUTE 4, every
  one a frontier) and its live fault is the revert arm EDGER (the old coordinates rule: the road (10,-1), the check
  fails), beside ShiftTests and mutant W30.
* A scene that interrupts one target twice with nothing new gives that target up for the intent, and (since the
  step-3.1 verifier's round) a tile a scene began on and sent the player back from twice is not stepped on again in the
  intent. "Nothing new" is progress (a story flag, a Pokemon, items, experience, and since its second round new words
  heard in a scene that left the player be), not a tile seen in passing. Since the second round the twin is known by her
  WORDS, so the two tiles she guards, (10,1) and (11,1), are one scene: 3 push-backs before any news (twice on one tile,
  then the side-step onto the other, where the same words close both; per tile it was 4). The third is the side-step a
  person makes: the AI does not guess that a tile no scene began on is guarded too. The words are the FIRST PAGE a scene
  waited on: two different scenes that open with the same page would count as one (not met in the arms' maps).
* NEWS is any page never heard before in the intent, from a scene that did not send the player back or away: May's
  mother's greeting is news too, so the explorer may try the twin once more before May (at most one more push-back,
  then given up again at once; whether it walks there before meeting May depends on the run). The STORY is not read: the AI cannot tell news that changes the twin from news that does not. Measured
  (the sweep's SCENE-EXPLORE, 10 seeds to their own end): on step 3.1's code 6 reached Route 101 (May met, the twin
  passed) and the other 4 stopped by the PING-PONG rule between Brendan's house and the town before meeting May; since
  step 3.2 (the plan followed, the heading kept on the move) all 10 reach it (`SCENE-EXPLORE, AFTER THE TWIN`). Nothing
  makes the explorer go to May on purpose: it meets her because it explores May's house; step 5's goals are where a
  person's "go next door, then upstairs" belongs.
* Wild battles are only FLED (step 4 fights and catches). A trainer battle ends the intent with its reason; so would a
  trainer who spots the player (nothing on screen says who is a trainer).
* The ping-pong rule counts uses of one warp; a ping-pong through TWO different doors in turn is caught only by the
  novelty window (3,000 frames).
* Fleeing is proven live by ROAM (13 battles), by ROUTE9 (the ROUTE arm at seed 9 through the launcher: one wild battle
  met and fled, since the step-3.1 verifier's round), by ROUTER (in-process) and by the unit tests. ROUTE at seed 3
  meets none on step 3.1's trajectory (its flee check is then 0 == 0 == 0); the sweep's ROUTE FLEE section: 7 of 10
  seeds meet one, every one fled and counted by the game.
* THE GAME'S ANSWER (`gates/game_answer.py`) predicts only CLEAN lines (plain floor or tall grass, no warp, no live coord
  event, no person within a tile). With no such line it can still say whether the player can move at all (LOCKED) and,
  given the warp the player last used, where the ROM puts it (THE ARRIVAL: modelled for doors, non-animated doors and
  plain warps; a dynamic warp is not modelled). An INCONCLUSIVE answer with neither FAILS its arm. It reads memory too
  (the step counter, `gMapHeader`, save block 1's `pos`); what makes it another kind of evidence is that these are the
  game's reactions to presses, or the ROM's own data, predicted at the claimed tile.
* Experience as novelty is proven live by ONE arm (XP) on a fixture whose battle was won by TEST-SIDE presses: the AI
  does not fight until step 4, so in its own play only a battle it did not flee could give experience.
* A level-up's STATS BOX is not read as a wait by the eyes: a battle that levels a Pokemon up stalls the flee skill
  until the stall detector gives up (900 frames: `stuck:`). Found while building the XP fixture; the battle decider's
  (step 4) to read.
* The evidence pins the predictions each run read (`predictions:`), not that they were written before a first look at
  a graded run: that needs a commit made before the run.
* One launcher trajectory per arm (seed 3); re-running reproduces it exactly WITHIN ONE WINDOW OF THE HOST'S CLOCK (the
  bullet below: ROAM, SCENEX, SCENEX9 change across windows) (the in-process dev runs and the launcher runs have equal
  frames and presses for every arm; the step-3.1 verifier's re-run matched line for line): ONE TRAJECTORY,
  REPLAYED, a determinism check, not a replication (CLAUDE.md rule 8). The sweep's seed 3 is that same trajectory again
  (its REPLAY section says so and compares the frames with the live evidence of the same tree). The replications are
  the sweep's other nine seeds and, through the launcher, TOWN9 and ROUTE9 (seed 9, since the step-3.1 verifier's
  round), HOUSE9, SCENEX9 and BUMP8 (since its second round; BUMP's at seed 8 because of seeds 1-10 only 3 and 8 walk down
  into the one-way tile), each revert A/B again at that seed (TOWN9R, ROUTE9R, BUMPSR8). Every `PREDICTED` number of a
  replication arm was written from its own development run before the graded one: they are pre-registered, not
  re-derived.
* THE GAME READS THE HOST'S CLOCK (mGBA's real-time clock, the framework's default; measured in the step-3.1 verifier's
  second round): at every map load the berry trees grow by the minutes passed and draw from the game's random numbers, so
  a launcher run's trajectory can depend on WHEN it is played. Arm CLOCKS (8 instants over 12 days, the clock pinned
  in-process) finds ROAM, SCENEX and SCENEX9 change with it and the other 13 launcher arms do not; those three register no
  launcher frame counts, and CLOCKS checks their claims at every instant. A launcher run cannot pin the clock (the AI may
  not set it; the framework has no option for it); every in-process run does (`GAME_CLOCK`). Earlier rounds' "the
  verifier's re-run matched line for line" were re-runs within one window of the clock.
* The warp-table guard (`gates/warp_reads.py`) sees the reads the eyes make on its 7 starts (the arms' maps, Rustboro's
  mart, a battle); a read that only a map it never looks at would trigger is not exercised there. The static check covers
  every host file but names only; the two together are the guard, neither alone. The frequency answer is the SEED SWEEP (`gates/rate_step3.py`, `evidence/2026-10-08-step3-RATE.txt`, in-process
  `hands_harness.py`; the figures in the rest of this bullet are step 3's verifier round, the current ones are in
  "Step 3.1, the verifier's round"): HOUSE, TOWN, ROUTE, ROAM, STUCK, CROP 10 of 10 seeds each
  as intended, and TOWN with the Catcher and the Trainer taste 10 of 10 each (`80 of 80 runs as intended`; with 0
  failures in 10 a plan's failure rate is below ~30% at 95%: the rule of three); ROAM's ten seeds 0 or 1 spins in 150
  training steps (9 to 13 more presses each, the steps a battle pre-empted). It is not a launcher gate (the purity of
  the same code is the arms'). Before its two fixes the first sweep found 2 failures in 70 (README "Found while
  building"). Its CHOICES section: `TOWN: 10 different target sequences in 10 seeds; the first exploring choice's
  headings, by map: {'0:9': ['left', 'right', 'up'], ...}; seeds 3 and 7 chose the same sequence: False` (likewise
  every plan; STUCK 9 of 10, CROP 7 of 10: a beeline has few choices). Its CROP-SEP: `every TOWN seed knows 0 tiles from
  outside a window and its first town target was SEEN: True; every CROP seed knows > 100 from outside and its first
  town target was NOT seen: True; => the two discriminators separate all 10 + 10 runs: True`. (In this sweep the town
  steps happen not to overlap, TOWN 32-53 and CROP 22-26, but before the whim an honest seed walked 26 steps in all,
  CROP's own total then: the step count is still no check.)
* The personality weights and the roaming scores are plausible taste, not measured from people.
* (the step-4 verifier's second round) A DECISION IS CARRIED ON, but it is not a plan for a region: what it carries on to
  is the frontier that took the stale one's place (within `CARRY_RADIUS`, further the way the unseen lay, at most a tile
  aside), so a decision ends at a wall, a corner, a room's end, and a new one is made on the move there; and it ends
  whenever another place is worth more than one tile of walking more (`CARRY_SWITCH_MARGIN`). Chosen by measurement, not
  taste: with no margin at all (a decision held whatever comes) the TOWN walk grew a third (a street swept past the road
  out); with a margin of 2 the Catcher's and Trainer's walks grew. The TRAINER taste still re-decides more often than the
  others (people move; since step 4.1 round 2 its taste for people is a PEOPLE place, below, and no longer a bonus on
  unseen tiles near people): in round 2's development sweep its decisions on the move were 27.6 per 100 steps at most
  (its bound) against the other plans' 12.8-21.2.
* (the step-4 verifier's second round) The real code is not ring-free: RINGS (a loop walked) are counted and reported; the
  bound is on LAP RINGS, a ring with a leg walked beyond the shortest way to its own target. The real code's rings are
  excursions (into a room up one column, out by the next, every leg the shortest way to its own target).
* (the step-4 verifier's second round) Two ways out of a house were MISREAD, found by this round's development sweeps
  and fixed: the doormat's OTHER tile was taken for an exit not used yet (2 of 10 seeds left May's house by it before going
  upstairs to May, and never met her), and once a doormat counted as one way out, the stairs one step away to a floor
  SEEN ALL OF outscored the doormat four steps away (the AI went up and down until the ping-pong rule: CROP seed 1,
  SCENE-EXPLORE seeds 5 and 15 of 20). Now a doormat is one way out (`world/memory.py` mat_tiles) and a way back to a map
  seen all of is no option while another leads somewhere with something left (`brain/explore.py` not_back_to_seen_all):
  the 20-seed development sweep reached Route 101 on 20 of 20 SCENE-EXPLORE seeds, with the carry-on and without it.
* (step 4.1 round 2, finding 7) THE JOURNEY CHARGE IS GONE. Step 4.1 charged a place chosen on the move for doubling back
  on its journey; its held-out replication refuted two of the bounds it was graded by and showed it made TOWN-Catcher
  worse. Round 2 looked for WHY a walk doubled back, run by run, and fixed the causes in the walk itself (section "Step 4.1
  round 2"): the Trainer's taste for people pulled it to unseen tiles near a person it could not reach (now a PEOPLE place:
  the seen tile beside a person not met yet, walked up to once, `MEET_TRIES` attempts at most); a person standing on the
  followed plan further on broke it at once (now only one on the next `PERSON_AHEAD` steps does, and it is WAITED for,
  `PERSON_PLAN_WAITS` times, before the walk goes round); a detour went two tiles aside and back (now it BENDS: at most
  `DETOUR_EXTRA` steps longer than the way). What is still greedy: a decision on the move is still one place, not a plan for
  the whole journey, and a room looked round (its corners walked to and back) still counts as steps beyond the shortest
  way, by the measure's nature (SCENE-EXPLORE's journeys).
* (step 4.1 round 2) A PERSON MET is one the player has stood within `MEET_RADIUS` (3) tiles of, seen on the screen: a
  person walked past counts. A trainer who sees the player starts a battle by the game; a person who does not (a villager)
  is not talked to: walking up to someone is the Trainer taste's way to find trainers, not a conversation. Someone who
  walks off is remembered where last seen for `PEOPLE_RECENT` frames.
* (step 4.1 round 2) WAITING FOR SOMEONE is a short idle (`PERSON_WAIT`/3 frames, said "letting them pass"); if they have
  not moved after `PERSON_PLAN_WAITS` waits the walk goes round them as before. A person who never moves (a sign-like NPC)
  costs those waits once per plan.
* (step 4.1 round 2) ROAM seed 104 (a development seed this round) spun 2.0 % of its training steps in the development
  sweep (the others 0-1 %): `skills/roam_train.py` is unchanged; the walk's new rules move the game's random numbers, so
  which encounter comes where moved; an 86-seed A/B of the old and new walk gave the same spin rate. Said, not fixed.

## The hands (build step 2)

The AI's hands for text and menus (design draft §6 build order step 2; RULING 37 Q6: human pacing, goal-directed,
never idle). Framework-free: they see the game only through `Eyes.look()` and press only through the brain's
`Controls` (the host's controller), so the instrument counts every press as the AI's (`ai_presses`).

**The pad** (`hands/pad.py`). Every press is a HOLD of a seeded, jittered 3-7 frames followed by a jittered gap of
8-18 frames (a person's 50-300 ms, never the bot's one frame; shorter than the 16 frames a step takes and than
`gKeyRepeatStartDelay`, so one press is one key everywhere). Before the A that moves a text on, a READING delay:
0.3 s + 2.4 frames a character of the page that appeared since the last press, +-20 %, at most 2.5 s; before a
choice, a 0.23-0.75 s look at the menu. Nothing idles without a reason: `idle(frames, reason)` and
`busy(reason)` both take one and LOG it (consecutive busy frames with the same reason are one record:
"watching: a scene plays", "reading along: a text is printing", "watching: the yes_no is not taking input
yet"; since step 2.1 also the fade and the scene the eyes name, "watching: the screen fades (Professor Birch's
speech)", "watching: the map loading (...)", and a real run that logs the catch-all "watching: the game is
busy" fails its arm). Every press NAMES ITS GATE, what the eyes said on the look right before it (`press` refuses an empty
gate), and the action log keeps it beside the look's digest. The seed is split into a PACING stream and a
CHOICES stream, so pacing never changes a choice.

**The rule for A** (the museum-greeter lesson, `PROJECT KNOWLEDGE/08-MISTAKES.md` 2026-07-23). `dialogue.advance`
presses A only when the eyes say `waits_for_button` on a FRESH look right before the press (a text printer in
WAIT / CLEAR / SCROLL_START, the script's `waitbuttonpress`, or, new in step 2, a TASK that polls A/B with no
printer waiting: `eyes/screens.py` TASK_WAITS, e.g. the pause after "What's your name?" and the mart's "Here
you go!"), and it STOPS without pressing the moment a menu is on screen: a choice is made by intent, by the
caller. `dialogue.talk` presses the A that STARTS a conversation only while the player is free (overworld, no
script running, field controls unlocked, nothing on screen), facing the person or thing (across a COUNTER for
the nurse and the clerk). Every other A confirms a choice whose cursor a look has just shown ON the option.

**Cursors are read, never counted** (`hands/menus.py`). `move_cursor` looks, presses ONE step toward the target,
and looks again; `choose` presses A only when the look right before it shows the cursor on the option, and
presses again if the game dropped the A (at most 3). Why: the keyboard's cursor stays on the last key typed, the
start menu remembers its row, the wall clock's "Is this the correct time?" opens on NO, a script's yes/no
ignores input for 5 frames, a multichoice for 2 to 12. `type_name` switches the page with SELECT, steps the
cursor the shorter way round (the rows wrap through the button column, `src/naming_screen.c`
HandleDpadMovement), presses A on the key, READS the text after every press (B deletes a wrong letter), then
START and A on OK. `set_clock` holds the D-pad while the clock is far (`clock_hold_frames`: the hand speeds up,
6/3/2/1 frames a minute, `src/wallclock.c`) and steps the last minutes with short presses, reading the time
after each. `set_quantity` reads "x NN" (Up +1, Right +10).

**What the eyes see now** (`eyes/screens.py`, read by `host/eyes.py`). `ScreenState.ui` is a `MenuView`: the open
menu, recognised by the TASK that runs its input (a menu's cursor struct outlives the menu), its options and
cursor, and whether it takes input yet:

| ui | what is read (pret/pokeemerald) |
|---|---|
| `yes_no`, `gender`, `mart_menu`, `multichoice` | `sMenu` (`src/menu.c` struct Menu: cursorPos @2, max @4); a script yes/no's 5-frame delay (its task's data[2]); a multichoice's option texts from the ROM's `sMultichoiceLists` |
| `main_menu` | its task's data (`src/main_menu.c` tMenuType data[0], tCurrItem data[1]) |
| `start_menu` | `sStartMenuCursorPos`, `sNumStartMenuActions`, `sCurrentStartMenuActions` |
| `naming` | `sNamingScreen` (`src/naming_screen.c` struct NamingScreenData: textBuffer @0x1800, state @0x1E10, currentPage @0x1E22, cursorSpriteId @0x1E23, template @0x1E28) and the cursor sprite's data[0], data[1]; input only in STATE_HANDLE_INPUT with the input task enabled |
| `clock` | its task's data (`src/wallclock.c` tHours data[2], tMinutes data[3]; input only while the hand is on a minute) |
| `mart_buy`, `mart_quantity` | `sMartInfo` (itemList @8, itemCount @0xC), each item's name and price from the ROM's `gItems`; `sShopData` (selectedRow @0x2006, scrollOffset @0x2008, maxQuantity @0x200A); the quantity in its task's data[1] |
| `bag`, `party` | `gBagPosition` (pocket @5, cursor and scroll per pocket); `gPartyMenu.slotId` @9 |
| `title`, `intro_movie` | Task_TitleScreenPhase3 (takes A or START); the intro movie and the title's logo animation (any key skips) |

`ScreenState.text` is the message on screen as far as it has printed, decoded by the AI's own charmap (from
`gStringVar4`, `gDisplayedStringBattle` or a ROM string), and `script_running` / `controls_locked` say whether
an A next to a person would START something. One new READ-ONLY door: `modules.game.get_symbol` (a symbol
table lookup), to know which buffer a printer's `currentChar` points into. Step 2.1 adds `ScreenState.fading`
(`gPaletteFade.active`: bit 7 of byte 7, `include/palette.h`) and `ScreenState.scene` (what plays when nothing takes
input, in a person's words: `eyes/screens.py` SCENE_CALLBACKS by `gMain.callback2`, resolved once with `get_symbol`,
then SCENE_TASKS by a task's name, then SCENE_STATES), read through the same doors (no new one).

**The skills** (`skills/intro.py`, `skills/clock.py`, `hands/menus.py` nurse_heal and mart_buy), each with ONE
goal and one loop: `advance` toward the goal, and answer every `menu:<kind>` it stops at by intent. The intro:
skip the movie and the logo with START after a moment, START at the title, NEW GAME, Birch's pages read and
moved on, BOY or GIRL by the personality's weighted draw (`personality.py`: P(GIRL) 0.6 Catcher, 0.45 Story,
0.5 Trainer: taste, not strategy), the "your name?" task wait, the name drawn from the personality's list and
TYPED (mixed case, so the page switch is used), "So it's NAME?" answered YES only if the question names the
typed name (otherwise NO, and the intro asks again), then read to the truck and STOP (nothing is pressed in the
truck). The nurse: turn to her, talk, read, YES, read to the end, then check every party Pokemon is at full HP.
The mart: talk, BUY, the item by name in the list, the quantity read, YES to the price, B out of the list, QUIT,
read the goodbye, then check the bag rose by N and the money fell by N x the listed price. The clock: face it,
talk, read, set the computer's local time (logged first), YES (the cursor opens on NO), read Mom's scene to its
end. Each brain is bounded by `--frames` and ends with the skill's outcome as its reason.

**Why the brain reads its own options.** The host is finished (no change to `ai_player/host/` but the eyes in
step 2), and the session builds `Brain(settings, say)` for every brain but the watcher with step 0's
`BrainSettings`. So `mode.py` `Brain` reads `options.HandsOptions` (the same environment the session read) and
hands the run to a `HandsBrain` when `AI_PLAYER_BRAIN` names one; for `placeholder` nothing changes.

**Proofs.** `gates/live_step2.py` runs each arm through the real launcher (the gate first, the purity instrument,
the verdict file) and grades it three ways, every check quoting both values: PURITY (CLEAN, every breach counter
0, `ai_presses` equal to twice the pad's own count: a `hold_button` and a `release_button` per press, the run
ended by itself within its budget); the GAME by a second path, from the state the run LEFT (`hands_harness.py
truth`: save block 2's name and gender by the probe's charmap, `get_party()`'s HP, the probe's bag and money
decode, save block 1's flag and variable bits, `gLocalTime`, the ROM's price), never the AI's eyes; and the
HANDS from the action log (every press has its gate; every A that moved a text was pressed on a look whose
digest says `waits=A/B(<that reason>)`; the pace). EVERY arm, the fresh ones included, first ASSERTS that the state
graded is the one this run wrote (`check_after_is_this_run`: written after the run started, its frame counter the
start's plus the run's real frames +-5, a fixture arm's md5 not the fixture's; before, the fresh arms relied on the
launcher unlinking the old state without asserting it), and that check is fault-tested on 7 synthetic runs before
any arm (`[SELFTEST]`, quoted in every evidence file: a stale mtime, a frame +-3000, no file and the fixture's md5
each fail it). Evidence `evidence/archive/no-digest/2026-10-07-step2-<ARM>.txt`:

| arm | start | what happened (quoted from the evidence) |
|---|---|---|
| INTRO | `--fresh`, seed 3 | `[AI-HANDS] intro: personality Catcher (seed; seed 3): gender GIRL (drawn with P(GIRL)=0.6), name 'Rosa'`; TRUTH `name 'Rosa' gender 1 (GIRL) map [25, 40]` (the truck); 8,664 frames, 55 presses, `ai_presses=110`; 22 A on text waits, 22 reading delays of 42-150 frames; `the AI read the name question before answering it: 'So it’s Rosa?'`; choices `main_menu cursor on 0 (NEW GAME)`, `gender cursor on 1 (GIRL)`, the keys `'R' at (5,2) of the upper page` ... `'a' at (0,0) of the lower page`, `yes_no cursor on 0 (YES)` |
| XU (fault) | the same, `AI_PLAYER_FAULT_UNGATED_A=1` | the same intent logged; HARM `name 'AAAAAAA' (intended 'Rosa'), gender 0 (BOY; intended GIRL)`: the naive A took the gender menu's default and typed the top-left key until the name was full; `243 A presses, gates ['NONE (FAULT ungated A ...)']` |
| XBN (fault) | the same, `AI_PLAYER_FAULT_BLIND_COUNT=1` | the keyboard moved by counts from the top-left key while the cursor starts on the last key typed: HARM `the name in save block 2 is 'R.qq', not 'Rosa'` (the first letter right, the rest wrong); `So it’s R.qq?` read and answered NO four times; the truck never reached in 12,000 frames |
| NURSE | `post_league_lobby.ss1` | before `[['Mightyena', 202, 227]]` not whole; TRUTH after (`get_party`) every Pokemon at full HP, Mightyena 227/227; 7 presses: turn up, talk, 2 pages, `yes_no cursor on 0 (YES)`, 1 page, the script's wait |
| MART | `gates/fixtures/mart_rustboro.ss1` | TRUTH `POKé BALL 5 -> 10: +5`, `money 6680 -> 5680: -1000 (want 5 x the ROM's price 200)`; the quantity read `x1` ... `x5, the number wanted`; 17 presses |
| CLOCK | `gates/fixtures/clock_room.ss1` | the step-2.1 run: `the time to set: 23:26 (the computer's local time)`, in the run's window; TRUTH `FLAG_SET_WALL_CLOCK=True VAR_LITTLEROOT_INTRO_STATE=6 gLocalTime [0, 23, 26, 3]` (the fixture: False, 5); `yes_no cursor on 1 (NO), wanted 0 (YES): one step up`, then YES. (The step-2 run set 22:37: this arm's time, frames and presses follow the computer's clock.) |
| XBC (fault) | the clock fixture, `AI_PLAYER_FAULT_BLIND_COUNT=1`, since step 2.1 `AI_PLAYER_CLOCK=13:37` | HARM `FLAG_SET_WALL_CLOCK=False VAR_LITTLEROOT_INTRO_STATE=5`: "Is this the correct time?" answered with the cursor on NO 55 times (the count assumed it opens on YES), the same 55 on a re-run (with the computer's time it was 50, then 51, for seed 3) |

**The REPLICATION, seed 9** (`live_step2.py --seed 9`, evidence `evidence/archive/no-digest/2026-10-07-step2-seed9-<ARM>.txt`; its
predictions were written into the script's docstring BEFORE the graded runs, from the in-process harness). The
step-2 verifier noted that re-running seed 3 gives identical numbers: a determinism check, not a replication.
Seed 9 draws another personality and other pacing (every hold, gap, reading delay and think pause), so each arm
is a SECOND trajectory with the same pass criteria. 7 of 7 PASS, `[SELFTEST] ... PASS`, no leftover emulator:

| arm | seed 3 | seed 9 (quoted) |
|---|---|---|
| INTRO | Catcher, GIRL, 'Rosa'; 8,664 frames, 55 presses | `personality Trainer (seed; seed 9): gender GIRL (drawn with P(GIRL)=0.5), name 'Luna'`; TRUTH `name 'Luna' gender 1 (GIRL) map [25, 40]`; `presses=52 frames=8792`; `22 A presses advanced a text, each on a look whose digest says waits=A/B(<that reason>)`; `22 reading delays, 43-150 frames` |
| XU | 'AAAAAAA', BOY; 4,409 frames | `name 'AAAAAAA' (intended 'Luna'), gender 0 (BOY; intended GIRL)`; `presses=247 frames=4530` |
| XBN | 'R.qq' | `the name in save block 2 is 'BELLA', not 'Luna'`; asked `'So it’s L   ?'` four times, NO each time. 'BELLA' is the game's PRESET name, written before EVERY keyboard opening (`src/main_menu.c` NewGameBirchSpeech_SetDefaultPlayerName(Random() % NUM_PRESET_NAMES)) and left in the save because the run ends during a retry |
| NURSE | 1,964 frames | `healed`, `frames=1974`; TRUTH `['Mightyena', 227, 227]` ... every Pokemon at full HP; `4 A presses advanced a text` |
| MART | 1,441 frames | `bought`, `frames=1480`; TRUTH `POKé BALL 5 -> 10: +5`, `money 6680 -> 5680: -1000 (want 5 x the ROM's price 200)` |
| CLOCK | the computer's time (23:26 in the step-2.1 run) | the step-2.1 run: `the time to set: 23:36 (the computer's local time)`, TRUTH `gLocalTime [0, 23, 36, 3]` (step 2's run: 22:38) |
| XBC | NO 55 times (13:37 pinned) | `FLAG_SET_WALL_CLOCK=False VAR_LITTLEROOT_INTRO_STATE=5`; NO 54 times (13:37 pinned; step 2's run, the computer's time: 49) |

`gates/test_hands.py` (37 tests since step 2.1, which added SceneTests and PressKindTests, below): the step-2 files import no framework and no host (fault: a planted import is
caught); `read_ui` on the bytes the host reads (the gender menu's real `sMenu` bytes, the yes/no's input delay, the
main menu, the clock, the keyboard, the intro movie); the PAGE rule on a recorded CLEAR wait (fault: the rule before
its fix reads it as empty); the keyboard table against the decomp; the host's pointer range check; the pad (a press
needs a gate; reading 18-150 frames, growing with the text; seeded jitter); and the hands driven against small
MODELS of each menu (each names its decomp source) that start in screens the eyes really RECORDED in the game
(`gates/fixtures/hands_recorded_{intro,clock,mart,nurse}.json`, from `hands_harness.py --record`): A only on
waits and never on the choice (fault ungated: A while printing and on the choice); each page's reading delay
STARTS after the page has printed and covers the whole page; the clock's yes/no that opens on NO answered YES
(fault blind: NO); nothing pressed in the nurse yes/no's input delay, by `choose` and by `move_cursor` called
directly; the gender menu and a menu whose cursor starts ELSEWHERE (fault blind: SELL instead of BUY); `choose`'s
gate is its OWN look (given a `move_cursor` that says it moved and did not, no A lands); "Rosa" typed from the
opening keyboard and from a mid-name cursor (fault blind: a wrong name); a wrong letter ('Rox') and a keyboard
that opens with text ('Kai'; the decomp's one such keyboard is Walda's phrase, `copyExistingString = TRUE`)
deleted with B, exactly 1 and 3 times; the clock set to 21:47 (fault blind: never confirmed); the quantity to x5
and x23; no talk A while a script runs (fault: with the free check removed it lands on the script). The test file
honours `AI_PLAYER_TEST_SUPPORT_ROOT` (as `test_eyes.py` does), so it runs from a copy of the package.

**Each check of the REAL code carries weight, or is documented as redundant** (`gates/revert_step2.py`, evidence
`evidence/archive/no-digest/2026-10-07-step2-REVERT.txt`). The fault switches show the tests catch a NAIVE driver; the step-2
verifier mutated the real code and found four checks no test caught. The script now breaks ONE check per copy of
the package and runs `test_hands.py` there (step 2.1 added HS, HSo and HK: the named busy reason, the scene's
callback lookup, the A-press classes; each CAUGHT, so 21 caught of 25 now): the unchanged copy passes all its tests; 18 mutants of step 2 are CAUGHT by their
predicted tests (no stop at a menu; the first wait check of `advance`; both wait checks; `talk`'s free check and
its facing; `choose`'s cursor check; `move_cursor` not reading the cursor, and not waiting for input; the keyboard's
cursor moves, its B delete and its START to OK; the quantity; the clock's outer check, and both; a press without a
gate; an unbounded reading delay; both pointer range checks), and 4 are REDUNDANT ALONE, as predicted, each with
its reason in the evidence: `advance`'s second wait check (H2-gate: a wait the eyes report ends only on a press,
`src/text.c` TextPrinterWait / TextPrinterWaitWithDownArrow, `src/scrcmd.c` WaitForAorBPress, every TASK_WAITS
task), `choose`'s input check (H11: the same frame as `move_cursor`'s last look), and the re-checks after a
'think' pause of the keyboard's OK (H5c) and the clock's time (H8b: the cursor and the hand move only on a press
or a hold). Each redundant check stays, as the press's logged gate.

**The fixtures.** `gates/fixtures/mart_rustboro.ss1` (`make_mart_fixture.py`: `rustboro.ss1`, md5 pinned in the
builder, walked 13 steps into the mart and 4 up the aisle to (3,3), across the counter from the clerk; printout
`mart_rustboro.build.json`) and `gates/fixtures/clock_room.ss1` (`make_clock_fixture.py`: the AI's OWN intro, seed 7,
"Rowan", BOY, then by this builder's presses: out of the truck, A only on the eyes' waits through Mom's two scenes,
breadth-first steps over the tiles the eyes see, up the stairs to (5,2) under the clock; `VAR_LITTLEROOT_INTRO_STATE`
5, `FLAG_SET_WALL_CLOCK` clear; printout `clock_room.build.json`). Both are pinned by md5 in `live_step2.py`. ‼ A
REBUILD DOES NOT REPRODUCE THE BYTES: measured 2026-10-07, the rebuilt states differ from the pinned ones in 8 bytes
and in `gLocalTime` only (the emulator's real-time clock is in the state; frame, map, tile, party, money and bag are
equal), so a rebuild must be re-pinned. The nurse arm uses `tools/story-dev/saves/post_league_lobby.ss1` as it is
(`LEAGUE_NURSE_STAND`, the party not whole).

**Found while building, and fixed:**
* ‼ A GARBAGE POINTER KILLED THE PROCESS. The framework's `read_bytes` bounds EWRAM and IWRAM reads (it raises) but
  not a cartridge read (a raw memmove at `address - 0x08000000`). On the frame the naming screen allocated its data,
  the template pointer held garbage and the eyes' read of it was a Windows access violation, which no `try` catches.
  Every pointer the eyes follow is now range-checked first (`host/eyes.py` `_rom_bytes`, `_ewram_bytes`; also the
  map-header and tileset reads of step 1); `test_hands.py` proves the check refuses before any read.
* The page at a paragraph break read as EMPTY: a printer waiting in CLEAR has already consumed the `\p`
  (`eyes/screens.py` page_text; a recorded wait is its test, with the old rule as its fault half).
* The text under a menu: printers that finished stay inactive, and a rule that took any printer pointing into
  `gStringVar4` reported a stale message; now printer 0's last message (or the ROM string it printed).
* `talk` spent its four facing attempts waiting for a scene to end (found by its unit test); the wait for the
  player to be free now has its own bound.

## Step 2.1: the step-2 verifier's weak proofs, made strong (2026-10-07)

The step-2 verifier passed every arm and listed five WEAK PROOFS. Each now has a proof that can fail; the
predictions were written into `gates/live_step2.py`'s and `gates/live_step1.py`'s docstrings before the graded runs.

| weak proof | what was done | proven by (evidence `evidence/archive/no-digest/2026-10-07-step2-<ARM>.txt` unless named) |
|---|---|---|
| 1. "each text A was gated" was the log agreeing with itself (the gate and the digest are ONE look), and the two task waits new in step 2 had no behavioural proof | `gates/probe_presses.py`: the real skill in a throwaway emulator; before EVERY A press it saves the frame and asks the GAME in forks of it (the state reloaded before each): is a text still printing (an active printer advancing within 8 frames, no input); does anything move in 300 frames with no input (every active printer, the box, the main callback, the tasks, the script's pointer and status, the keyboard's text); does the SAME press move it; does B, pressed instead, do exactly the same (a continue, not a choice); for the A that starts a conversation, is the player free and does a script start. Every value is the probe's own raw read; the forked run must equal an unforked `hands_harness.py` run | WBI `30 A presses`, `8 menu, 22 wait ... Wrong: none`, `f5587 wait 'task Task_NewGameBirchSpeech_WaitPressBeforeNameChoice (': printing=False still=True A moved it at +1 ['tasks'] B-same=True`, `the forks changed nothing in the run: probe [..., 8664, 55] == unforked harness [..., 8664, 55]`; WBM `f119486 wait 'task Task_ReturnToItemListAfterItemPurchase (A or B)': printing=False still=True A moved it at +1 ['tasks'] B-same=True`; WBN, WBC (the script waits, the talks: `free=True started=True`). CONTROL WBX: the ungated fault under the same probe: `118 of 243 ungated A presses landed on a text still PRINTING, 208 on a screen that moved by itself`. FAULT XTW: a COPY of the eyes listing the timer task `Task_NewGameBirchSpeech_WaitToShowBirch` as a wait: `CAUGHT: 6 A presses gated on the fake wait, 6 flagged by the game's behaviour`, `the 22 other wait-gated presses of the same run are all proven` |
| 2. only NURSE limited the OTHER A presses (talk, menu confirms) | every real launcher arm (`check_gates`, `classify_a`) classifies EVERY A press from its look: a WAIT (`waits=A/B(<that gate>)`, no menu), a MENU confirm (that menu open and taking input, `ui=<kind>[`, nothing waiting) or a TALK (the overworld, nothing waiting, no menu); anything else fails. Still the log about itself; the GAME's side is weak proof 1's arms | INTRO `{'menu': 8, 'wait': 22}; any other: none`; NURSE `{'menu': 1, 'talk': 1, 'wait': 4}`; MART `{'menu': 5, 'talk': 1, 'wait': 3}`; CLOCK `{'menu': 2, 'talk': 1, 'wait': 7}`; `test_hands.py` PressKindTests with fault cases; `revert_step2.py` HK |
| 3. 530 frames of Birch's opening logged under the catch-all "watching: the game is busy (main_menu)" | the eyes report the FADE (`ScreenState.fading`, `gPaletteFade.active`) and the SCENE (`ScreenState.scene`, `eyes/screens.py` scene_of: the main callback, then a task, then the game state, in a person's words: "Professor Birch's speech", "the wall clock", "the map loading"); `busy_reason` names them. Every stretch the four skills stood still under the catch-all was measured first (a spy on `busy_reason`) and is now named | INTRO `55 stretches standing still, NONE under the catch-all`, the reasons `watching: Professor Birch's speech (it runs by itself: nothing on screen takes a press now)`, `watching: the screen fades (...)`; the same check on NURSE, MART, CLOCK; `test_hands.py` SceneTests (every measured stretch has a scene; every callback name is a symbol of the ROM; FAULT: no scene IS the catch-all); `revert_step2.py` HS, HSo |
| 4. the clock arms do not repeat (the time set is the computer's) | XBC's time is PINNED (`AI_PLAYER_CLOCK=13:37`): its harm does not depend on the time, so it now reproduces; CLOCK keeps the computer's time, the default a person uses, so ITS numbers still move with the hour (stated below) | XBC `the time to set: 13:37 (named by the run)`, `the cursor on NO 55 times` (predicted 55 from the in-process run) |
| 5. no live warp that differs only in y; two seeds are two trajectories, not a rate; the pacing is not measured from people | WARPY (`gates/live_step1.py`, `probe_step11.py warp_y`): a scratch search of every map's ROM warp events for a departure and an arrival tile that share x, near a fixture, found the League's 1F escalator (1, 7) -> 2F (1, 6), walked from the NURSE fixture. RATE: each skill once per seed 1-20 in-process, each graded by its second-path truth (the clock at a time spread over the day per seed). The pacing: not measurable here; still a known limit | `evidence/archive/no-digest/2026-10-07-step21-WARPY.txt`: `on all 15 of those frames the two tiles differ in y ONLY`, the eyes `settling` or `between screens` on each, `[MAP] ... -> EVER GRANDE CITY(16,14) pos=(1, 6)` at the first settled frame; WARPY-R4x (the x-only rule) CAUGHT live `[(8397753, [16, 14], [1, 7], [1, 6]), ...]`, and the same rule on arm WARP's Dewford door NOT caught (the gap closed). RATE: `intro: 20 of 20 seeds succeeded by the second-path truth ... frames 8372-8792`, `nurse: 20 of 20 ... frames 1912-1974`, `mart: 20 of 20 ... frames 1416-1534`, `clock: 20 of 20 ... frames 2455-3226` (each "below ~15% at 95% confidence, the rule of three") |

Seed 9 (`--seed 9`, evidence `evidence/archive/no-digest/2026-10-07-step2-seed9-<ARM>.txt`) ran every arm but RATE again: 13 of 13
PASS, e.g. WBI `the forks changed nothing in the run: probe ['intro: in the truck; intended Luna (GIRL)', 8792, 52]
== unforked harness [...]`, `8 menu, 22 wait`; WBM the task wait `f119517 ... still=True`; XTW `CAUGHT: 6 A presses
gated on the fake wait, 6 flagged`; XBC `the cursor on NO 54 times`. XBC seed 3 run again
(`evidence/archive/no-digest/2026-10-07-step2-repro-XBC.txt`): `55 times` again, the same frames.

**Which seed-9 files are which** (the step-3 verifier's note: the README cited `2026-10-07-...` while stale
`2026-10-08-step2-seed9-*` files lay beside them). Three sets, each a different tree:
* `evidence/archive/no-digest/2026-10-07-step2-seed9-<ARM>.txt` (23:35-23:38): step 2.1's FIRST round, quoted above. Their code line
  names no digest (`HEAD 9f859914; ai_player/ has UNCOMMITTED changes`): it predates `provenance.py`.
* `evidence/archive/no-digest/2026-10-08-step2-seed9-<ARM>.txt` (00:10-00:20, 14 files with a RATE): an intermediate run
  on the step-2.1 working tree BEFORE its second round (the same digest-less code line). Superseded, kept as they were,
  quoted nowhere.
* `evidence/2026-10-08-step2-seed9-at-step3-<ARM>.txt`: seed 9 re-run on the final tree. (Since the step-3.1 verifier's
  second round, on ITS final tree, `working-tree digest sha256:b94ddc58ca95f8f7`: 16 of 16 arms PASS, 0 failed checks, `leftover emulator processes:
none`. The run quoted in
  the rest of this bullet was on the step-3 verifier's round's tree, `sha256:1446987412c17a51`; the re-run rewrote its
  files under the same names, and that version is in git at commit 12b25140.) Every arm but RATE including step 2.1's
  second-round arms: 16 of 16
  PASS, 0 failed checks, `leftover emulator processes: none`. E.g. INTRO `personality Trainer (seed; seed 9): gender
  GIRL`, `the AI pad's own frame count 8762 == the instrument's real_frames 8762`; XBN `HARM, by the second path: the
  name in save block 2 is 'L   ', not 'Luna'`; XBC `the cursor on NO 54 times`; XTW `CAUGHT: 6 A presses gated on the
  fake wait, 6 flagged by the game's behaviour`; XFD `CAUGHT: 1 START / B / SELECT presses NOT taken by the game, each on
  a frame where a fade ran`; XSTALL `STUCK: nothing on screen changed for 300 frames`. (A first attempt ran concurrently
  with the step-3 seed sweep and its leftover-process check counted the SWEEP's `hands_harness.py` processes: 16 of 16
  arms passed, OVERALL FAIL on that check alone; re-run alone, OVERALL PASS. The files are the re-run's.)

The probe's forks never touch the run (`restored` on every press, and the forked run equals the unforked one in
outcome, frames and presses: a DETERMINISM check, CLAUDE.md rule 8). B-same is only asked of WAIT presses: on a
menu, A picks and B cancels (the mart's menu is the exception the probe shows: B there is QUIT, like the A the AI
pressed on QUIT).

## Step 2.1, the step-2 review's items (2026-10-08)

The adversarial review of steps 1.1 and 2 found nothing blocking and listed six items; the step-2 verifier added a
seventh weak proof. Each fix has a unit test that FAILS when it is reverted (`gates/revert_step2.py`: 44 mutants, 39
caught, 5 redundant alone with the reason; `gates/revert_step11.py` R5c), and the live ones an arm. The predictions
were written into `gates/live_step2.py`'s docstring BEFORE the graded run, from in-process development runs. Every
evidence file of this round said `working-tree digest sha256:57ee936bee9b962c`; the files of the same names were
re-written by the re-run of the whole set on the step-3 tree (the step-3 verifier's round), and said
`sha256:1446987412c17a51` (since then re-written again by every later round's re-run: they now name the current tree's
digest, `py -3.12 ai_player/gates/provenance.py` recomputes it for the tree as it stands); the
numbers quoted below held on that re-run (INTRO 8,742 frames, XBN 12,000, XBC 6,000, NURSE 1,964, MART 1,441; CLOCK
follows the computer's hour: 2,732).

| item | the fix | proven by (evidence `evidence/2026-10-08-step2-<ARM>.txt` unless named) |
|---|---|---|
| 1. an unrecognised prompt read as "watching a scene" for up to 3 minutes | `hands/dialogue.py` advance: a STALL DETECTOR. Every frame it stands still it compares everything the eyes see (`seen_now`: the Observation without its frame, cost and problems); unchanged for `STALL_FRAMES` = 300 frames it returns `stuck:<reason>` and says so; 900 (`STALL_FRAMES_SCENE`) while the eyes NAME the scene. Two limits because measured (seed 3, every busy frame of the four skills): the longest legitimate still stretches were 455 frames of "Professor Birch's speech" and 319 of "the nurse healing the party", both named; the longest unnamed one 58. The skills report a stuck `advance` as their outcome | `test_hands.py` StallTests (a locked script, no UI: stuck at exactly 300 frames, no press; named: 900; a screen that changes every 250 frames runs 3,000 and is not stuck); mutants HST, HSTn, HSTk caught. Live, XSTALL (a copy whose eyes do not know a script's yes/no: the nurse's question is an "unlisted menu"): `nurse: the nurse's dialogue ended in stuck:watching: a scene plays (a script runs, the controls are locked)`, `STUCK: nothing on screen changed for 300 frames ... menu=yes_no`, `1088 frames of 6000`. Its REVERT XSTALLR (the detector out too): `HARM: it watched the unknown menu for 5214 frames under the false reason`, `nurse: stopped: not finished within 6000 frames`. RATE: still 20 of 20 per skill (no false stall) |
| 2. the evidence named no tree ("HEAD x; UNCOMMITTED changes") | `gates/provenance.py`: the CODE line carries sha256 over `git diff HEAD --binary` and every untracked file (path and content) of the scope; evidence and Markdown left out (output and documents, not code under test); read-only git. All three live drivers use it | `test_hands.py` ProvenanceTests (two different trees, two lines; an untracked file's content counts; the same tree twice, the same line); mutant HPV caught. Every evidence file of this round, step 0's and step 1's included: `working-tree digest sha256:57ee936bee9b962c over git diff HEAD (14 files, 115770 bytes) and 1 untracked files` (step 2.1's run; the files re-written by the step-3 round's re-run say `sha256:1446987412c17a51 over git diff HEAD (21 files, 155973 bytes) and 19 untracked files`, the three REVERT files included since that round) |
| 3. the pad's frame count never compared with the instrument's | `live_step2.py` check_purity asserts the pad's `frames=` == `real_frames` on every launcher arm. It would have FAILED on the step-2 evidence: the two arms stopped by their budget logged 11,999 vs 12,000 (XBN) and 5,991 vs 6,000 (XBC), because the pad counted a press only once it finished. `hands/pad.py` `_count` now counts each frame as it is handed on (and still releases a held button when a skill is stopped) | INTRO `the AI pad's own frame count 8742 == the instrument's real_frames 8742`; XBN `12000 == 12000`; XBC `6000 == 6000`; NURSE 1964, MART 1441, CLOCK 2939, XU 4409; `test_hands.py` PadFrameTests (a press stopped after 4 of its 6 frames counts 4; the driver's check fails 5991 vs 6000); mutants HPF, HPI caught |
| 4. presses other than A never checked; a fade not "not taking input" | `eyes/screens.py` read_ui: while `gPaletteFade.active` NOTHING takes input (`src/intro.c` MainCB2_Intro ignores keys in a fade; `CB2_InitTitleScreen` runs no task while it fades in; the main menu, keyboard, shop and clock wait `if (!gPaletteFade.active)`); `host/eyes.py` reads the fade before the menu (no new door). `skills/intro.py` presses START only on a look that takes input. `gates/probe_presses.py` forks every START, B and SELECT too: TAKEN when the pressed run differs from the run with no input (task data, `sMenu`, the keyboard's state and cursor included) | WBI `EVERY START / B / SELECT press was TAKEN by the game ...: {'Select': 1, 'Start': 4}; dropped: none` (f260, f322, f369, f6099 START, f5798 SELECT, none on a fading frame); WBM `{'B': 1}`. FAULT XFD (a copy with the fade rule reverted): `CAUGHT: 1 START / B / SELECT presses NOT taken by the game, each on a frame where a fade ran: ['f211 Start ...: fading=True taken_at=None []']` (the review's own frame) and `the 5 presses of the same run on frames with no fade were all taken`. INTRO is now 8,742 frames and 54 presses (step 2: 8,664 and 55, one START of which the game dropped). `test_hands.py` FadeTests; mutants HFD, HFG caught, HFW redundant alone (the reason in the evidence) |
| 5. the intro could re-type a name it typed right | `skills/intro.py` name_in_question: "So it's NAME?" (`gText_Birch_SoItsPlayer`) names EXACTLY the typed name (it was a substring test: "Kai" is in "So it's Kaiden?"); a page the eyes cannot read as that question is answered from what `type_name` CONFIRMED (OK pressed only on a look whose text read exactly the name), or the skill stops with that reason | `test_hands.py` NameQuestionTests (exact compare; an unreadable question: typed once, YES; "So it's {name}a?": NO, then YES); mutants HNQ, HNK caught; INTRO `the AI read the name question before answering it: 'So it’s Rosa?'` |
| 6. sub-skill failures retried until outer counters ran out | the intro (NEW GAME, gender, the name, the name question), the nurse (her yes/no), the mart (the shop menu) and the clock ("Is this the correct time?") end AT ONCE with the failure as their outcome | `test_hands.py` SubSkillFailureTests (a menu that never takes input: one try, the reason, within one wait budget); mutants HF1-HF7 caught. ‼ FOUND THROUGH IT: `choose(gender)` FAILED in every real intro: moving the gender cursor switches its task to Birch's sprite slide (`src/main_menu.c` Task_NewGameBirchSpeech_ChooseGender -> SlideOutOldGenderSprite -> SlideInNewGenderSprite), and the eyes reported the menu CLOSED; the old loop chose again on its next turn and hid it. Now `eyes/screens.py` UI_BUSY_TASKS reports the menu on screen, not taking input (GenderSlideTests, mutant HGS). The blind-count fault waits for input before its A too (it is blind to the CURSOR only), so XBN shows the keyboard harm as in step 2: `the name in save block 2 is 'R.qq'`, `'So it’s R.qq?'` four times |
| 7. no revert proof of the host's torn-party -> None (the step-2 verifier's V3) | (no code change) `test_eyes.py` runs the HOST's own `_party` on a fake emulator memory: a party of two with the second slot torn is None and the problem names slot 2; two whole slots read both | `evidence/2026-10-08-step11-REVERT.txt` `[R5c] ... REVERTED to the host returns the slots it could read when one is torn ... -> CAUGHT` |

The whole set was re-run on the final tree: `check_purity.py` PASS; `test_check_purity.py` 29 OK; `test_host.py` 20
OK; `test_eyes.py` 56 OK; `test_hands.py` 56 OK; `revert_step11.py` and `revert_step2.py` OVERALL PASS; `live_step0.py
--arms A,A2,B,C` PASS (`evidence/2026-10-08-step01-*`); `live_step1.py` 21 of 21 arms, 603 checks, 0 failures; `live_step2.py`
17 of 17 arms, RATE `intro: 20 of 20` (frames 8406-8767), `nurse: 20 of 20`, `mart: 20 of 20`, `clock: 20 of 20`, no
leftover emulator.

## Known limits of step 2

* The stall detector (step 2.1) sees what the EYES see: a scene that animates only sprites, blends or sound looks still
  to it (Birch's opening: 455 frames). The 900-frame allowance for a NAMED scene comes from the four skills' longest
  measured stretches; a longer named scene in a later step would be reported stuck, and an unknown prompt during which
  something else on screen keeps changing would not be.
* The nurse, the mart and the clock start from fixtures in front of them, and the intro stops in the truck. Step 3's
  navigator now walks (stairs, doors, Mom's scenes read through: arm HOUSE), but no brain yet chains a walk and a
  skill; the clock fixture's builder still walks from the truck to the clock with test-side presses.
* Text printed INSTANTLY (speed 0: menu labels, the wall clock's "Is this the correct time?") never enters
  `sTextPrinters` (`src/text.c` AddTextPrinter renders it with a temporary printer), so `ScreenState.text` then shows
  the last message printed before it. With no printer active, `text` is "what was printed last", not proof that it
  is still drawn (the start menu opened with no message shows an old one). No skill depends on it except the
  intro's name check, whose question IS printed by printer 0.
* Menus are named only where a step-2 skill needs them or the task asked: the battle menus, the PC, the summary
  screen, list menus other than the mart's are not; the bag and party report a cursor row, no option names; a
  multichoice's names come from the ROM's table only for script multichoices.
* `eyes/screens.py` TASK_WAITS is a list of the waits met so far, not every task in the game that polls A/B.
* The mart's listed price is the ROM's; the half price of Slateport's sale (`IsPokeNewsActive`) is not modelled.
* The gender and name lean of each personality is a placeholder for variety (no game reason); the name lists are
  short. The clock is set to the computer's local time (as a person would): arm CLOCK's frames, presses and hand
  holds therefore differ between runs at different hours, and only its pass criteria are fixed. XBC (step 2.1),
  WBC and RATE pin the time and reproduce exactly.
* The pacing is a plausible human tempo, not a measured one (no recording of people was available); it is clearly
  slower than the bot's one-frame presses (the intro takes ~8,700 frames, ~2.4 minutes of game time).
* The launcher arms are TWO trajectories per arm, seeds 3 and 9; re-running one seed reproduces its numbers exactly
  (INTRO 8,664 frames, NURSE 1,964, MART 1,441, XBC 55 NO answers; the harness and the live run agree too), a
  determinism check (CLAUDE.md rule 8). The RATE arm (step 2.1) is the frequency answer: 20 seeds per skill,
  in-process (the skills' code; the purity of the same code is the launcher arms'): 20 of 20 for each, so a failure
  rate below ~15% at 95% confidence, not zero; 20 seeds cannot see a rarer failure, and the starts are the same
  three fixtures (another mart, nurse or clock room is untested).
* The behaviour probe (`probe_presses.py`) asks the game about the 300 frames after a WAIT; a wait that would end by
  itself LATER than that would pass it. None of the waits the hands press on can (each polls a button with no
  timeout, the decomp lines in `revert_step2.py` H2-gate), and the XTW fault shows a timer task is caught.
* Four checks of the hands are REDUNDANT ALONE (`gates/revert_step2.py` H2-gate, H11, H5c, H8b: each repeats a check
  made a moment earlier on a thing that changes only on the AI's own press). They stay as the presses' logged gates;
  no test can catch their removal alone, and the evidence says why.

## The eyes (build step 1)

The brain sees the game only through `Eyes.look()` (`mode.py`), which returns ONE immutable
`Observation` (`eyes/observation.py`) read at one frame, stamped with the emulator's frame counter. A
part that cannot be read this frame is None and says why in `problems`; a look never raises.

| part | what | read from |
|---|---|---|
| `frame` | the emulator's frame counter | `context.emulator.get_frame_count()` |
| `screen` | the framework's game state; `overworld` / `battle` / `text` / `menu` / `transition` / `title` / `other`; the open menu (start menu, yes/no, multichoice, bag, party, summary, naming, PC storage, starter choice, main menu); whether the overworld text box is open; whether the game waits for A/B, and WHY (`wait_reason`: `script waitbuttonpress`, or `text printer N WAIT / CLEAR / SCROLL_START`); whether a battle is running | `get_game_state`, `battle_is_active`, `sFieldMessageBoxMode`, the task list, the global script context (`WaitForAorBPress` while not shut down), all 32 `sTextPrinters` (a printer in RENDER_STATE_WAIT, the `{PAUSE_UNTIL_PRESS}` of every trainer's defeat text, or CLEAR / SCROLL_START, the down arrow) and `gTextFlags` (under autoScroll nothing waits for a button) |
| `player` | map (group, number, the region-map name the bot logs use, the map's own constant), position, facing, movement (walking, running, Mach / Acro bike, surfing, underwater), elevation, the VISIBLE 16-bit trainer id (step 1.1: the secret id is never reported); `settling`: during a warp the position is None (step 1.1, below) | `gPlayerAvatar` and the player's object event (raw), save block 1's pos and location, `get_map_data_for_current_position` (once per map, after checking that the live `gMapHeader` IS that map's ROM header from `gMapGroups`: a header left from another map is refused and reported), `get_map_enum`, `get_player` |
| `view` | the 15 x 11 tiles ON SCREEN (below), each with collision, elevation, behaviour, blocked, water, wild encounters (land / water), tall grass, ledge direction, door, warp, half-visible; the objects inside it (item balls, people, cut trees, rocks, boulders, berry trees; step 1.1: every person is an "npc", no trainer label before it engages) and signs (interactable tiles); a picture (`ascii`). None while the position settles | the LIVE grid `gBackupMapLayout` (the map + its 7-tile margin, which holds the connected maps), the tilesets' attributes and `sTileBitAttributes` (ROM, read once), the map's warps and bg events (ROM), `get_map_objects` |
| `party` | species, national dex number, level, HP, status, types, moves with PP, PID (identity), the visible OT id, egg. ‼ None = NOT READ (the title screen; a torn slot makes the WHOLE party None), () = no Pokemon (step 1.1) | raw `gPlayerParty`, decoded by the AI's own `eyes/party.py` (the framework's `get_party()` looks a frame AHEAD on a torn read); names from the data tables |
| `storage` | every Pokemon in the 14 PC boxes: box, slot, PID, the visible OT id, egg (step 1.1: a catch sent to a box is seen by identity); None = not read | `gPokemonStoragePtr`, each slot's UNENCRYPTED header (no decryption) |
| `bag`, `progress` | every ball and healing item with quantities; money, badges, Pokedex owned / seen (and the owned numbers), ten story flags for badge 1 (`eyes/view.py` STORY_FLAGS: each name checked against the framework's flag table, each id against the decomp, each MEANING against the decomp script that sets it) | `get_item_bag`, `get_player`, `get_pokedex`, `get_event_flag` |
| `battle` | wild or trainer, double, the type flags, the opponent trainer id, both sides' active Pokemon (species, level, live types). The player's own: HP numbers, the HP bar, every move with PP. A FOE as a person sees it (step 1.1): the HP BAR only (filled pixels of 48, `hp` / `max_hp` None), only the moves it has USED this battle (PP below max: `ppreduce` follows "used MOVE!"), no PP; and only once it is THIS battle's (its PID is an occupied slot of `gEnemyParty`) | `get_battle_state` (`gBattleMons`), `gBattleTypeFlags`, `gTrainerBattleOpponent_A`, raw `gEnemyParty` headers |
| `last_battle_outcome` | `gBattleOutcome` (0 in a battle, the result after it) | raw |

**The window, derived and measured.** The decomp draws virtual-map metatile (j, i) at screen
(16 j, 16 i - 40) while the player stands on (7, 7) (`src/field_camera.c`: the BG scroll is the pixel
offset plus the camera pans 0 and 32, plus 8), so the screen shows dx -7..+7 and dy -5..+5 around the
player, the rows dy = -5 and +5 half (`eyes/view.py` has the derivation with its citations). Arm GEO
MEASURES it on four overworld fixtures: the player sprite's tile is drawn at screen (112, 72), the pans
are (0, 32), the columns -7..+7 and rows -5..+5 are on screen with -5 and +5 half visible; its control
(a battle fixture) does not give (112, 72). The game keeps objects alive up to dx -9..+10, dy -7..+9
(`TrySpawnObjectEvents`): those, hidden items and invisible objects are NOT in an Observation (§10.7).

**The action log and the scorer lines** (`memory_log.py`). Every look of the watcher is one JSON line
in `<run_dir>/actions.jsonl` (`frame`, `digest`, `decision`, `action`, `reason`, and the compact
Observation: each tile as `[x, y, metatile, behavior, collision, elevation, flags]`, about 10 KB a look).
The run's log gets the bot's own line formats, so `ai-agent/scoring.py` `parse_log` scores an AI run
like a bot run: `[AI-STARTER] Story: choosing X!` FIRST (observed when the last party READ was empty and
now has one Pokemon, or inferred at run start: the player's own starter-family Pokemon, else `Unknown`),
`[MAP] A -> B(g,n)` (written at the first SETTLED look on the new map), `[DEX] owned a -> b`,
`[TRAINER] end opp=N last_seen=Name#N ... res=... money=a->b`, `[AI-BATTLE] end kind=wild sp=Name#N
res=... [tutorial=wally] [player_catch=yes|none|unknown]`, `[CATCH] end ... sp=Name#N end=caught res=Caught
dest=party|box pid=XXXXXXXX`, and the `[hb]` heartbeat every 3600 frames plus one when the brain ends
(`end=1`, from the last look with a settled position and a read party), from which the scorer takes the
run's end map, position, party and length. A battle is one record from its first look with both sides,
REFRESHED by every later one (the lines name the foe of its last look), and ENDS only on a look out of
the battle whose `gBattleOutcome` is a result and whose party, boxes and money could be read: no line
ever says `res=InProgress` (the scorer counts every `res` but `Won` as a loss). A CATCH is logged only
for a NEW PID of the player's (visible OT id) in the party or a box, and `dest` is where that PID is:
`gBattleOutcome == Caught` alone is not a catch (Wally's tutorial ends Caught; the Ralts is his).

**Cost of a look** (measured 2026-10-07 in the round-2 run whose evidence is on disk,
`evidence/archive/no-digest/2026-10-07-step1-*.txt`, with the learner's 16 lanes running alongside): in-process (the probe),
30 looks per fixture, one per frame: overworld medians 1.38 to 1.59 ms (means 1.39 to 1.60, worst look
1.85 ms), a battle or a full-screen menu (no view to read) medians 0.70 to 0.79 ms (worst 1.21 ms). In the
live runs, under the purity instrument, 10 looks each: overworld medians 1.54 to 1.76 ms, battle and menu
medians 0.82 to 0.91 ms, worst look 2.40 ms. The first look of a run also reads the ROM tables it keeps
(tilesets, tile flags, the map's events) and is usually the slowest. The numbers move with the machine's
load: the step-1 verifier's own re-run measured an overworld median of 1.95 ms and a worst look of
2.96 ms (E8). Reading all 32 text printers (1152 bytes) instead of one changed none of this measurably.
Step 1.1 (the PC boxes, the VBlank check, the enemy party's PIDs) in its live run, 10 looks each: overworld
medians 1.59 to 1.99 ms (worst 2.57 ms), battle and menu medians 0.87 to 1.06 ms (worst 1.67 ms).

**Proofs.** (Step 1.1's own are in the section "Step 1.1" below.) `gates/test_eyes.py` (32 unit tests in step 1: the framework-free files import neither the framework
nor the host side; the window's edges; the behaviour table against the decomp's values and the
framework's own table; the party decoder against the framework's table and decoder for all 24
substructure orders, with a swapped-row fault; every flag name, and every flag id equal in the
framework's table and the decomp, with a wrong-id fault; the probe's charmap and the item-name
comparison; the wait rule against the decomp's render states, with the pre-fix rule and the
printer-0-only rule as faults; the scorer reading the AI's lines, with two format faults).
`gates/live_step1.py` (15 arms, evidence `evidence/<date>-step1-<ARM>.txt`): ten fixtures (a town, two
routes with tall grass and an item ball off / on screen, a wild and a trainer battle, a trainer's DEFEAT
text, an open text box, a party menu, a map edge, the League lobby's full bag) through the real launcher
with the watcher; the first look against `gates/probe_eyes.py`'s ground truth on the SAME frame (asserted
in every arm), each fact by a SECOND PATH, never the eyes' bytes and code:

| fact | the truth the arms compare with |
|---|---|
| map | (group, number): the live header byte-identical to one header of the ROM's `gMapGroups`, walked by the probe; NAME: the ROM header's region-map section -> `gRegionMapEntries`, decoded by the probe's own charmap (the decomp's `charmap.txt`) |
| position | save block 1 `pos` |
| facing | on the overworld (6 fixtures), what is DRAWN: the player sprite's `animNum` (ANIM_STD order) and its OAM hFlip (only the east frame is flipped). In a battle or a full-screen menu the overworld sprites are freed and the game keeps no second copy: those lines say CONSISTENCY ONLY |
| in battle | `gMain.inBattle` (a bit the eyes do not read) |
| party | the framework's `get_party()` (its own decryption): species, level, HP, PID, every move with PP and max PP, the status (138 moves over the ten party fixtures, 25 of them with PP used; one status other than ok, E7's paralysed Skitty); and the raw level byte |
| battle sides | the SECOND COPY the game keeps: the party struct with the battler's PID (`gPlayerParty` / `gEnemyParty`, the framework's decryption: species, level, HP, max HP, status, moves with PP and max PP) and the species table's types. The probe's raw `gBattleMons` parse is the same bytes as the eyes, so its line says CONSISTENCY ONLY |
| trainer id | the trainer who STARTED the battle, without `gTrainerBattleOpponent_A`: `gSpecialVar_LastTalked` -> the map's ROM object template -> its script's `trainerbattle` argument (`Route116_EventScript_Joey`: 322); the ROM's `gTrainers[322]` is JOEY with the live enemy party, the only one of 855 with it; the decomp's `TRAINER_JOEY 322` |
| text box | `Task_DrawFieldMessage` in the probe's own task parse (the eyes read the box's mode byte) |
| waits for a button | BEHAVIOUR, in the probe's throwaway emulator, the eyes looking at EVERY frame: text on screen, 300 frames with no input move nothing, one A press moves that text. Before and after the press, every frame on which a text PRINTS by itself must read waits=False, every idle frame from which the screen sits still until the press (which then moves that text) waits=True, and after the press every frame a text then sits still for 30 frames waits=True. Measured: 301 waiting idle frames in each battle and the text box (E4, E5, E6, E10), 200 on the party menu's printer 6 (E7), 26 printing frames before the press (E7) and 10 to 46 after it (E1, E4, E5, E6, E10), 88 to 160 still frames after it (E1, E6, E10). E2, E3, E8, E9 have no text, and E7 none after the press |
| the defeat text | E10: printer 0 in state 1 with the two bytes it consumed last FC 09 (EXT_CTRL_CODE_PAUSE_UNTIL_PRESS) and its buffer reading Joey's defeat text from the decomp's `data/text/trainers.inc`; the fixture's build printout shows it was PLAYED (22 button presses from E5's fixture) |
| menu | `gPartyMenu.menuType` = 1 (in battle) and the named `gMain.callback2` |
| objects | a raw `gObjectEvents` parse with the probe's own window test, and WHAT IS DRAWN: each object's sprite on screen relative to the player's (E1, E2, E3, E6, E8, E9: every still object drawn on its coordinates; the objects the eyes see are exactly those drawn inside the window; E2's item ball is drawn at screen x 240, past the right edge) |
| the map-header check | its fault arm: another map's ROM header written over `gMapHeader` in the probe's emulator is refused (every arm with a probe) |
| `gTextFlags` bit order | in a battle the byte is 0x03 (E4, E5, E10): the bit-fields run from bit 0, so autoScroll is bit 2 as the eyes assume |
| tiles | the ROM layout, tileset attributes and warps decoded by the probe (metatile, behaviour, collision, elevation, warp) and the framework's `MapLocation` (encounters, water, tall grass; ledges and doors by the FRAMEWORK's behaviour names), across a connected edge too; ledges (8), doors and warps in the window |
| money, badges, story flags, Pokedex | the probe's decode of the save blocks: money XOR the key; flag bits at the decomp's ids; owned / seen by the game's own rule over the three seen copies |
| balls, healing items | the bag pockets decoded by the probe, names from the ROM's `gItems`, "healing" = the ROM's use function is `ItemUseOutOfBattle_Medicine` / `ItemUseInBattle_Medicine` (E9: 7 healing items and 5 others) |

plus each fixture's documentation; the crop (an item ball the game holds at dx = +8 is absent, the
trainer at dx = +1 present) and its FAULT arm (with `AI_PLAYER_FAULT_NO_CROP=1` the ball appears); a
CONTROL on every tile check (the window shifted one column mismatches); arm XW, the waits fix REVERTED in
copies of the package (the pre-fix states {2, 3}: caught on E10 and E7; printer 0 only: caught on E7,
passes on E10; the unchanged copy passes both); arm XG, the fault half of the truth checks: 36 copies of
graded arms with ONE value made wrong, on the eyes' side or on the TRUTH's side (the sprite, a flag bit, a
ROM tile, the script's trainer, the behaviour, the task list, the menu type, the probe's frame, a second
copy's HP and PP, an object's drawn position, the header check, `gTextFlags`, the defeat text's bytes),
each caught by its own check while the unchanged copy passes; the scorer on a real run; every run CLEAN
with `ai_presses=0` and `ai_bot_calls=0`.

**The eyes missed a wait, and the verifier found it from the decomp.** Until round 2 "waits for a button"
read only `sTextPrinters[0]` in states 2 and 3 (the down arrow). The decomp has a third waiting state,
RENDER_STATE_WAIT = 1 (`include/text.h`), which `{PAUSE_UNTIL_PRESS}` enters (`src/text.c`) and which
`src/battle_message.c` appends to every trainer's lose and win text and to the whiteout text: so after
every trainer v1 beats, Roxanne included, the eyes said "not waiting" while the game waited for A. The
first natural capture was then found in a fixture already graded: the party menu's "SKITTY is already in
battle!" waits in state 1 on PRINTER 6, which the eyes did not read at all. The rule now reads all 32
printers and states 1, 2, 3 (`eyes/view.py` `text_printer_wait`), proven on E10 (a trainer's defeat text,
made by playing E5's battle to its end) and E7, each half of the fix failing on revert (arm XW).

**A story flag was wrong, and the second path found it.** The Ch2 flag was `THANKED_FOR_PLAYING_WITH_WALLY`
("Wally's catching tutorial done"); the decomp sets it only when the player talks to Wally's DAD in
Wally's house, an optional chat, so it read False on every fixture, six badges included (this project's
ML-9, repeated). The tutorial sets only variables (`VAR_PETALBURG_CITY_STATE` 2 -> 3); its scene's one
flag, `HIDE_PETALBURG_CITY_WALLYS_MOM` (set in `PetalburgCity_Gym_EventScript_BeginWallyTutorial`), replaced
it, and every entry of `STORY_FLAGS` now names the decomp script that sets it.

## Step 1.1: the step-1 review's findings, fixed (2026-10-07)

Each fix has a unit test in `gates/test_eyes.py` that FAILS when the fix is reverted (`gates/revert_step11.py`
reverts each in a copy of the package: 13 of 13 caught, the unchanged copy passes all 55 tests; R4x and R4y,
added after the step-2 verifier's mutant V4, compare ONE coordinate each: the measured warp differs in x only,
so `SettlingTests.test_the_rule` now also has a y-only and a both-differ case), and the
host-side ones a live arm in `gates/live_step1.py` that PLAYS the case in the probe's throwaway emulator with
the eyes looking at every frame (`gates/probe_step11.py`), each with its own revert copy. Evidence:
`evidence/archive/no-digest/2026-10-07-step11-*.txt`.

| finding | the fix | proven by |
|---|---|---|
| 1 Wally's tutorial logged a player `[CATCH]` | a catch only for a NEW PID whose OT is the player's VISIBLE id, in the party or a PC box (the eyes now read the boxes, `storage`); `gBattleOutcome == Caught` alone is not one: `BattleScript_WallyBallThrow` sets it with no `givecaughtmon` | `CatchTests` (R1); BLW: a real catch through the bag and the nickname screen writes `[CATCH] ... dest=party pid=7D6D2751`, the foe's PID, which the framework's party then holds; `PC BOXES` in every arm (E3: 2 Pokemon) |
| 2 battle lines: a stale foe at the start, `res=InProgress` | the record is REFRESHED by every in-battle look; it ends only on a result, on a readable look; and the eyes report a foe battler only if its PID is a Pokemon of `gEnemyParty` | `BattleLineTests` (R2a, R2b); BS: for 9 frames of a new battle `gBattleMons` held the previous battle's Abra while the foe was Poochyena: the eyes report no foe there, the line says `sp=Poochyena#261`; the step-1 code in a copy (BS-X2) writes `sp=Abra#63`; BLT: `[TRAINER] end opp=322 ... res=Won money=6680->6824 delta=144`, the game's own "got ₽144" |
| 3 perception like a person | the foe's HP is the 48-pixel HP BAR (`hp`, `max_hp` None), its moves only those USED (PP below max), no PP; every person is an "npc"; the player's id and every OT id are the VISIBLE 16 bits | `PerceptionTests` (R3a-R3d); E4/E5/E10 against the second copy (bar by the decomp's GetScaledHPFraction); E10 against the battle's own texts, replayed ("Foe MACHOP used FOCUS ENERGY!", "... LEER!"); E2: Joey (raw trainerType 1) is an "npc", and the step-1 label in a copy (E2-X) calls him "trainer"; every arm: the full 32-bit id in no record |
| 4 warp staleness | the position is reported only when the player object's tile (- 7) equals save block 1's `pos`; otherwise `settling`, no position, no view; the `[MAP]` line waits for the settled position | `SettlingTests` (R4; R4x, R4y: one coordinate compared); WARP: 6 frames of Dewford's door warp mixed map (3,5) with tile (8,8): the eyes say settling (2 frames) or between screens (4) there, and on all 689 of 700 frames where they report a position it is the save block's pos on the map the live header is; the step-1 position in a copy (WARP-X) writes `[MAP] ... -> DEWFORD TOWN(3,5) pos=(8, 8)` |
| 5 party None vs (), dest by count | `party` None = not read (a torn slot makes the whole party None), () = no Pokemon; the starter is "observed" only after an empty party was READ; `dest` is where the new PID is | `PartyNoneTests`, `CatchTests` (R5a, R5b) |
| 6 the script's waitbuttonpress, untested | `eyes/view.py` script_waits_for_button, captured live | `ScriptWaitTests` (R6); SW: Dewford's sign ends in the script's waitbuttonpress (no printer active, the box mode already hidden): 300 idle frames move nothing, waits=True on all; one A ends it; the fixture's first frame (a finished script, status 2, mode Stopped, WaitForAorBPress left behind) reads False. Reverts: both checks removed (SW-X1) caught; each alone (SW-R1, SW-R2) NOT caught (each is redundant alone); the branch removed (SW-X2) caught |

**Found by the new live arms, and fixed:** (a) the stale foe in the Observation itself (above, BS);
(b) the SAVE BLOCKS MOVE between frames: `MoveSaveBlocks_ResetHeap` (every battle start and every map load)
copies both save blocks and the PC boxes out and back with `gMain.vblankCallback` NULL, and the copy spans a
frame boundary: at a trainer battle's end, on the frame the pointers moved, the Pokedex's third copy was
half restored and the eyes read 0 owned (`[DEX] owned 5 -> 0`, then `0 -> 5`). While the VBlank callback is
NULL the eyes now withhold the player, the boxes, the bag and the progress (a problem says so); BLT's revert
copy (BLT-X) writes the drop again.

## Known limits of step 1.1

* Wally's tutorial itself was not played live (no save stands before it; reaching it means the walk to
  Petalburg and Norman's scene): the rule is proven on a synthetic run and on a real catch (BLW), and the
  decomp's `BattleScript_WallyBallThrow` is the reason.
* No look out of the battle before its result was found in the game: on the nickname screen `in_battle`
  stays True (`gMain.callback1` is still BattleMainCB1) and the result is set before `in_battle` reads
  False (BLW). The "end only on a result" rule is a guarantee, unit-tested only.
* The catch arm's RNG: delay 1 catches (the third ball), delay 0 misses with all five: one trajectory,
  replayed (rule 8), not a catch rate.
* "Between screens" withholds about 15 frames around a battle's start and end, more than the move itself
  (other transition frames NULL the callback too). The re-encryption after the move
  (`ApplyNewEncryptionKeyToAllEncryptedData`, then the new key) runs with the callback restored; a frame
  boundary inside it would mis-decode money and bag quantities for a frame. Not seen; not guarded.
* At the script's `waitbuttonpress` the box is still on screen, but its mode is already HIDDEN, so `screen`
  reads `overworld` and `text_box_open` False there; `waits_for_button` (the one an A press is gated on)
  is True.
* A foe move is "seen" when its PP is below its maximum: a two-turn move's charging turn and a Focus
  Punch that lost focus take PP with their own message, Struggle takes none, and a Leppa Berry that
  restores PP hides the move again.
* The PC boxes are read every look (33,600 bytes, no decryption); a box Pokemon's species is not decoded.
* Step 2.1 closed the gap "no live warp that differs in y only": arm WARPY plays the League's escalator (tiles
  (1, 7) and (1, 6), x equal), and the x-only rule (R4x) is caught there live while it is NOT caught on WARP's
  Dewford door. On 13 of WARPY's 15 mixed frames the eyes withhold the player as "between screens" (the VBlank
  callback is NULL); the settling rule itself decides the other 2, which is where the mutants show.

## Known limits of step 1

* The watcher looks every N frames (60 in the proofs): anything shorter than N frames can be missed, and
  a change is logged at the look that sees it. A look costs ~10 KB of action log: an hour of game time
  watched every 60 frames is ~36 MB. On a fresh boot the first look is at frame 0, before the game has
  run a frame: it reports that as its one problem and sees nothing (the framework's caches are empty).
* (Resolved in step 1.1: the foe's exact HP and its moves were reported; now the HP bar and the moves used.)
* The window is the standing-still one: the partial 16th column / 12th row while the camera scrolls a
  step is not modelled. Objects on the half-visible rows are reported. "Signs" are a map's interactable
  tiles (signposts, PCs, bookshelves, a few invisible triggers), not only signposts.
* Menus are named only for the start menu, yes/no, multichoice and the whole-screen states; list menus
  (mart, PC item lists) and the battle's own menus are not named yet. `waits_for_button` covers a script
  waiting for A/B and every text printer in a waiting state; a wait that is a TASK polling the buttons
  with no text printer waiting (the level-up stats box, a menu's cursor) is not a "waits for a button"
  here (a menu is named in `menu` instead). The autoScroll branch (no wait under `gTextFlags.autoScroll`:
  `messageautoscroll` scripts, link and recorded battles) is unit-tested only: no fixture sets it. The
  whiteout text's state-1 wait is the decomp's (`sText_PlayerWhiteout2`), not a capture: no fixture stops
  there (`ki90_whiteout_at_evergrande.ss1` showed no text in 4000 idle frames: the step-1 verifier's probe).
* The behaviour test that classifies a frame as PRINTING or WAITING is behavioural, not exhaustive: a
  text in RENDER_STATE_PAUSE for 30 frames or more after the press would read as "still" (none occurs in
  the fixtures; before the press the stricter rule "still until the press, which then moves it" applies).
* Battle statuses are graded only as `ok` (no battle fixture holds a status); the party status is graded
  on E7's paralysed Skitty. Objects mid-step are checked only to lie within one tile of their coordinates,
  and are left out of the "crop by what is drawn" check (none occurred in the fixtures).
* Facing has no second copy during a battle or a full-screen menu (the overworld sprites are freed);
  there the arms check it only for consistency (the same byte, decoded by test code), and say so. The
  map NAME's truth is the same ROM string the framework decodes, read through the ROM table and decoded
  by the probe's own charmap: a second decoder, not a second copy. Money and the bag's quantities have no
  second copy in the game either: their truth is the probe's own decoder of the same save-block bytes.
* The map-header check compares the live `gMapHeader` with the ROM header from byte 4 on: the layout
  pointer (bytes 0-3) is re-pointed at load and may differ from the ROM's (`setmaplayoutindex`). It runs
  once per map the eyes meet (the facts are kept), so a header that goes stale LATER is not re-checked.
* The behaviour test that grades `waits_for_button` presses A in the probe's own emulator, so it shows
  what one press does from the fixture's frame, not what the watcher run saw later (the watcher presses
  nothing, and its looks stay on the frozen screen).
* Out-of-map tiles were verified only across a connected edge (arm E8, 22 tiles); corner tiles and an
  edge without a connection are reported as the live grid holds them, unverified. A warp of the NEXT
  map visible across an edge is not marked `warp` (the eyes know the current map's warps only; its door
  behaviour is still marked `door`).
* Healing items were checked on two bags (E3: 1 healing and 1 other; E9: 7 and 5); no fixture holds
  berries, so the berry pocket's classification is unmeasured.
* A run started from a SAVE scores only what happens IN the run, exactly like a bot run: the scorer
  takes the Pokedex from `[DEX]` lines (written on a change, as the bot's `debug_logger.py` does), badges
  from leader wins and money from trainer-battle ends, so a watcher run on a save scores dex 0, no
  badges and no money (arm SC and E1 assert this PARITY and quote the bot's line). A New Game run, v1's
  case, starts at 0 anyway.
* The framework readers the eyes call memoise into the framework's per-frame Python cache
  (`state_cache`); nothing in the game changes. What the eyes do with a framework object's attributes is
  not tracked statically (a value, rule a's limit); the live audit counts any write, press, load, frame or
  bot code it could cause, and was 0 in every step-1 run.

## Known limits of step 0.1

* Static analysis cannot see values: a name bound by ASSIGNMENT is not tracked (`cls = type(obj)`
  then `cls.x = 1` is not refused). The classes the verdict depends on are sealed at run time, and
  the verdict is a file only the instrument writes; any other class the AI changes is its own.
* Python has no private memory. The run-time defenses refuse and count every ATTRIBUTE-level route
  to the instrument's state and to the lifecycle's, the session's, the isolation's and the guard
  listener's (instance, class and module attributes, the counters' private storage, negative counts,
  and since round 3 every call into the instrument's registry and counter stores from outside its
  file) and catch a module namespace rewritten behind `__setattr__`; a closure's cells, `object.__setattr__`
  (arm XE uses it on purpose), code compiled under a host file's name (the owner and caller checks
  compare file names; `gates/test_host.py` uses this route on purpose to set up the instrument with no
  emulator), a function's `__code__` reached through private module names, `gc` and `ctypes` can still
  reach anything. The static gate refuses every spelling of those in the AI's own code. That is a list
  of known routes, not a proof.
* The library surfaces are computed from the running Python's standard library: run the gate with the
  bot's Python (3.12). The gate trusts the interpreter, the standard library, site-packages and the
  framework's own code; it judges only which framework code the AI may reach.
* Bot DATA read without running bot code (a constant table) is refused only statically.
* The live audit cannot see a native change to ONLY the CPU or I/O registers, video memory or the
  cartridge save. Every route to the emulator core the two verifiers found is refused statically.
* A run killed by the HARD wall clock has no verdict file; the launcher says so. So has a run whose
  launcher got Ctrl+C (the child is killed, not interrupted, because it has no console).
* Debug mode cannot occur in a plain headless start (`modules/gui/headless.py` forces it off); arm G
  reaches it through a test-side wrapper that re-sets `context.debug` right before the real main loop,
  and its mutant M6 shows what an unrefused debug run does. In a GUI the main loop runs in a worker
  thread, where no signal handler can be installed: the session logs that, and Ctrl+C there behaves
  as before (and a run finished on that thread ends the process at once).
* The interrupt watch needs the Python signal handler to have RUN once, which happens between two
  bytecodes of the main thread. A main thread blocked inside ONE C call (a native deadlock) never runs
  it, so Ctrl+C / Ctrl+Break cannot end that run; only an outside kill (the launcher's hard wall clock,
  or closing the console) does, without a verdict. A second Ctrl+C restoring the default action was
  rejected: it would end ordinary runs without a verdict (finding 7 again).
* The frame fence holds back FRAMES, the only way anything reaches the game. A main thread that wakes
  up during the watch's finish may still run Python for the few milliseconds until the exit watchdog's
  `os._exit`: the rest of its brain step, the doors (whose wrappers come off in the finish), and, if it
  starts a new main-loop pass after the finish gave the framework its listeners back, one pass of those
  listeners. None of it can reach a frame, and the process ends without saving its state; the verdict
  covers the run up to the finish, as it does when the main thread finishes (where the framework also
  gets its listeners back before the process ends). A frame stuck in NATIVE code longer than 5 s is not
  waited for: the finish proceeds and records `frame_in_flight` in the verdict file.
* Selecting "AI Player" by hand in a GUI works, but the AI's give-up then ends that bot process (by
  design: an AI run never parks), and without a run directory there is no verdict file.
