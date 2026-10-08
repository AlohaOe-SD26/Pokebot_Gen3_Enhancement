"""LIVE PROOF of AI-player build step 3 (the WORLD MODEL and the AI's OWN NAVIGATOR): the AI walks out of the
player's house, through Littleroot, up Route 101 to Oldale, roams a grass patch and flees what it meets, ITSELF,
through the real launcher, under the purity instrument; plus the fault arms that show each rule carries weight.

    py -3.12 ai_player/gates/live_step3.py [--arms HOUSE,TOWN,ROUTE,ROAM,CROP,STUCK,BUMP,BUMPR,TRN,XP,XPR,SCENE,SCENER,EXITS,
                                                  SCENEX,SCENEXR,SCENENR,HOUSER,TOWNR,ROUTER,EDGER,TOWN9,ROUTE9,WARPREAD,
                                                  BUMPSR,TOWN9R,ROUTE9R,HOUSE9,BUMP8,BUMPSR8,SCENEX9,F2AB,CLOCKS]
                                           [--seed 3] [--evidence-tag TAG]

Each launcher arm runs `py -3.12 -m ai_player run` (the gate first, the purity instrument, the verdict file) with a
WORLD brain (`AI_PLAYER_BRAIN=explore|roam|goto`, `ai_player/mode.py` HandsBrain, `ai_player/brain/`) and the pinned
seed 3. The grade has four parts, each check quoting both values:
  1. PURITY (`live_step2.check_purity`): the gate passed on the real package; the verdict file CLEAN; `ai_presses` == 2 x
     the pad's own presses and > 0; the pad's frames == the instrument's `real_frames`; every breach counter 0
     (`foreign_*`, `ai_writes`, `ai_loads`, `ai_bot_calls`: the bot's pathfinder never ran); the run ended by itself.
  2. THE GAME, by a SECOND PATH from the state the run LEFT (`gates/hands_harness.py truth`: save block 1's map and
     `pos`, its flags and the intro's variable, the game's OWN step and battle counters `gameStats[]` XOR the key, the
     party by the framework's `get_party()`), never the AI's eyes; the same on the fixture BEFORE the run; and the state
     graded is asserted to be this run's (written after it started, its frame the start's + the run's real frames, its
     md5 not the fixture's).
  3. THE PERCEPTION RULE (design draft §10.7, the crop): the AI's own memory (`<run_dir>/world.jsonl`, its last snapshot)
     knows ONLY tiles that were inside the 15 x 11 window of the tile it stood on when it first saw them; every target
     it chose (the action log's `decide` records) was such a tile.
  4. THE HANDS (`live_step2.check_gates`' rules, for walking): every press names its gate; every A is a text WAIT, a MENU
     confirm (incl. the battle's RUN) or a TALK by its look; every WALKING hold (gate "walk ...", "keep walking ...",
     "use the ...", "roam ...") is pressed on a look of the overworld with nothing waiting and no menu; no idle stretch
     under the catch-all reason; every walking hold is `CHUNK_FRAMES` long, every other press 3-7 frames.
  5. (since the step-3 verifier) THE GAME'S ANSWER to where the player stands (`gates/game_answer.py`), every arm but
     TRN: from the state the run left, holding a direction makes the game's own step counter and the map it LOADS do
     what the ROM's layout at save block 1's claimed tile predicts (a different KIND of evidence from the `pos` the eyes
     read too); the same probe claiming a neighbouring tile it rules out must DISAGREE (its fault-test). A tile with no
     clean line (people beside it) is INCONCLUSIVE and says so; (since the verifier's second round) it then FAILS
     unless the game is LOCKED and the ROM's ARRIVAL from the last warp the AI used is the claimed tile (STUCK).

PRE-REGISTERED PREDICTIONS (2026-10-08, written before the graded runs, from in-process development runs of the same
code on the same starts: `gates/hands_harness.py`, seed 3; the fixtures from `gates/make_step3_fixtures.py`):
HOUSE  `house_2f_clockset.ss1` (the player's room, clock set, VAR_LITTLEROOT_INTRO_STATE 6), explore to LITTLEROOT_TOWN,
       Story. PREDICT "explore: done: explore to LITTLEROOT_TOWN"; the stairs (7,1) used pressing up (2F -> 1F, a warp by
       the AI), the TV scene on 1F read through (A only on its waits), the mat used pressing down (1F -> LITTLEROOT_TOWN);
       truth map [1,1] -> [0,9], VAR 6 -> 7 (the scene played), steps 9 -> 29; dev 3,344 frames, 52 presses, 18 steps.
TOWN   `pokedex_done.ss1` (Birch's lab, Mudkip), explore to ROUTE101, Story, knowing NOTHING. PREDICT done; the lab's mat
       used pressing down, Littleroot explored from the frontier it saw, Mom's Running Shoes scene read through
       (SYS_B_DASH False -> True), the north road walked onto: a CONNECTION Littleroot (x, 0) up -> Route 101 (x, 19);
       truth map [1,4] -> [0,16]; dev 4,961 frames, 43 steps, 7 decisions, steps 576 -> 621.
ROUTE  `route101_south.ss1` + its memory `route101_south.world.jsonl` (the TOWN walk, played by the AI itself), explore to
       OLDALE_TOWN, Story. PREDICT done; the memory LOADED (3 maps); the road back south known as the way to a visited
       map (not taken); a CONNECTION Route 101 (x, 0) up -> Oldale (x, 19); truth map [0,16] -> [0,10]; every wild battle
       met FLED (the game's wild-battle count rises by exactly the AI's fled count: dev 10 -> 10, none met), the party's
       HP unchanged; dev 975 frames, 49 steps.
ROAM   `route101_south.ss1`, roam 150 training steps, Catcher, knowing nothing. PREDICT "roam: roamed: ..."; 150 training
       steps, spin ratio < 2% (dev 0.007: 1 spin), distinct tiles >= 40 (dev 84), >= 1 wild encounter, every one fled (dev
       9); the game's own counters: steps rise by >= 150 (dev 621 -> 779), wild battles by exactly the AI's encounters
       (dev 10 -> 19); the end tile by save block 1 == the AI's last path tile; truth map still [0,16].
CROP   FAULT `AI_PLAYER_FAULT_NO_CROP=1` (the eyes show the WHOLE map), the TOWN start and goal. PREDICT done, purity CLEAN;
       the HARM to the perception rule, visible in the memory: tiles known from OUTSIDE every window (dev: most of 1,946);
       the first target on LITTLEROOT_TOWN a ROAD off the screen (dev: (10,-1) from (7,16)); fewer decisions and fewer
       steps than TOWN (dev 2 and 26 vs 7 and 43): a beeline.
STUCK  `clock_room.ss1` (the clock NOT set), explore to LITTLEROOT_TOWN. Going down, Mom sends the player back up
       (`LittlerootTown_BrendansHouse_1F_EventScript_GoUpstairsToSetClock`): an unreachable goal. PREDICT "explore: stuck:
       ping-pong: the warp ... used 3 times ... with nothing new since its second use", well within the budget (dev 1,519
       of 12,000 frames), the stairs used by the AI exactly 3 times and the scene's warps back recorded as the scene's;
       truth VAR_LITTLEROOT_INTRO_STATE still 5, FLAG_SET_WALL_CLOCK still False.
BUMP   `house_2f_clockset.ss1`, goto (0,4) then (2,4) then (0,4). The tile (1,4) is IMPASSABLE_SOUTH_AND_NORTH with collision
       0: the eyes call it walkable. PREDICT done; ONE bump, moving down from (1,3) into (1,4), learned blocked; afterwards
       no press toward (1,4) again: errand 2, (0,4) -> (2,4), whose only 2-step way is through (1,4), takes 4 steps round
       it; the truth of WHY by a second path (the ROM layout read by the framework's MapLocation: behaviour and collision
       at (1,4)); end tile [0,4] by save block 1; dev 371 frames, 15 steps.
BUMPR  REVERT of BUMP: a COPY of the package whose `WorldMemory.learn_bump` remembers nothing, in-process
       (`hands_harness.py` from the copy). PREDICT the HARM: the same tile bumped again and again (>= 10 BUMP lines on
       (1,4)), errand 1 never done, the intent "stuck: nothing new ..." within its budget.
TRN    `trainer_battle_r116.ss1` (a trainer battle on Route 116 just begun): a trainer battle is out of scope for step 3.
       PREDICT "explore: stuck: a trainer battle: out of scope ..." with NO press on the action menu (dev: 1 A, on the
       battle's opening text wait), 596 frames.
Evidence: `ai_player/evidence/<date>-step3-<ARM>.txt`. Exit 0 only if every arm passed and no emulator is left.

AFTER THE FIRST GRADED RUN (2026-10-08, said here rather than folded into the predictions above): every arm passed its
pre-registered checks except TRN, on two checks of the GRADER, not of the AI: `check_hands` demanded walking holds of
an arm that by design never walks (the battle is on screen from the first frame). The check now takes `walking=False`
for TRN (no walking hold at all is then REQUIRED). BUMPR measured 94 bumps into (1,4) and gave up after 3,123 frames.
The memory's novelty counter now also counts the tiles absorbed when the way back is inferred at an arrival (they were
learned uncounted); it moved the CROP arm's count of learned tiles (1,946 -> 3,136) and no trajectory (every arm's
frames and presses equal its dev run's: HOUSE 3,344 / 52, TOWN 4,961 / 101, ROUTE 975 / 99, ROAM 12,210 / 375, CROP
4,640 / 71, STUCK 1,519 / 40, BUMP 371 / 33).
THEN A SEED SWEEP (in-process, 10 seeds per plan, `evidence/<date>-step3-RATE.txt`) found two explorer flaws and a
roaming one, fixed before the final graded run (README "Found while building"): a lab -> town -> lab ping-pong (Catcher
seed 1, Trainer seed 6: the way just come in is now worth only `Weights.back` while this map has something to see, and
an exclusion belongs to its map), and roaming's only reversals at the corner where Route 101's boy wanders (it now waits
for a person in its only way on, and keeps 2 tiles from people; the worst seed was 3 spins in 151). That moved arm
ROAM's trajectory: dev seed 3 now 16,646 frames, 399 presses, 78 distinct tiles, 1 spin, 13 wild battles fled (game
counter 10 -> 23), steps 621 -> 779; its pass criteria are unchanged. The other arms' trajectories did not move.

AFTER THE STEP-3 VERIFIER (2026-10-08, its five weak proofs; PRE-REGISTERED before this round's graded run, from
in-process development runs of the same code on the same starts: `gates/rate_step3.py` seeds 1-10 and, for seed 3, a
`hands_harness.py --save-end` run of each arm with `gates/game_answer.py` on its end state):
  * the WHIM AMONG EQUALS (`brain/explore.py` pick) moves the explorer's trajectories; HOUSE and TOWN now accept map
    changes between the first and the last (a seed may look into a room or a house); their other criteria stand.
    HOUSE seed 3 is unchanged: 3,344 frames, 52 presses, targets 2F frontier (5,7), the stairs (7,2), the mat (8,7).
    TOWN seed 3: PREDICT 4,969 frames, 92 presses, 37 steps, targets lab frontier (6,10), the door (6,11), town
    frontiers (14,18), (13,11), (12,6), (10,1), the road (11,-2). ROUTE seed 3: PREDICT 2,083 frames, 108 presses, 51
    steps, ONE wild battle met and fled (the game's count +1: the flee is now non-vacuous on this arm too), 6 targets.
    CROP seed 3: PREDICT 4,640 frames, 79 presses, its first town target the road (11,-1) from (7,17). STUCK seed 3:
    unchanged (1,519 frames, 40 presses). BUMP, BUMPR, TRN do not choose targets: unchanged.
  * CROP: the walk's length is no longer a check (a note: an honest TOWN seed can be as short); the first town target
    is checked NOT SEEN (not inside the window of the tile it was first seen from), not "not in the window now" (the
    sweep's honest TOWN seeds 4 and 6 chose a frontier seen from the lab's door, not in the window of the tile they
    stood on). `rate_step3.py` CROP-SEP: both discriminators over 10 TOWN and 10 CROP seeds.
  * ROAM: PREDICT the same trajectory (roaming does not use the explorer's choice): 16,646 frames, 399 presses; 150
    training steps, 163 presses = ATTEMPTS, 13 interrupted by a battle (pre-empted: they did not move the player), 1
    spin: 1/150 = 0.0067 over the training steps; the same re-derived from the digests; the game's step counter 621 ->
    779, + 1 step in flight == 9 walk moves + 150.
  * THE GAME'S ANSWER: PREDICT agree on HOUSE (Down 3 steps to a wall, Left 5 to the map's edge; rules out 5 of the 5
    tiles beside it the player could stand on), TOWN and CROP (Down: 1 step and the map becomes LITTLEROOT_TOWN; Left /
    Right: 1 step to a wall), ROUTE (Down: 1 step into ROUTE101; Left 7 to a wall), ROAM (Down 1, Right 3 to a wall;
    Up meets a wild battle and is skipped; rules out all 8), BUMP (Down 3 to the map's edge, Left 0); each fault claim
    disagrees. STUCK: INCONCLUSIVE (Mom beside the player, the stairs above), the loaded header the 1F's.

AFTER THE STEP-3 VERIFIER'S SECOND ROUND (2026-10-08, its five weak proofs; PRE-REGISTERED before this round's graded
run, from in-process development runs of the same code on the same starts, seed 3: `hands_harness.py` for XP, a COPY
for XPR, `game_answer.py` on STUCK's and XP's end states). The evidence header now carries `predictions:` (sha256 of
this docstring, read at the start of the run: `predictions_ref`). No trajectory of the arms above moves (the new
novelty line is told, it takes no frame): HOUSE 3,344 / 52, TOWN 4,969 / 92, ROUTE 2,083 / 108, ROAM 16,646 / 399,
CROP 4,640 / 79, STUCK 1,519 / 40, BUMP 371 / 33, TRN 596 frames.
  * CROP: TRUTH (save block 1) map [1,4] (the lab) -> [0,16] ROUTE101, now a check (it rested on the outcome string).
  * STUCK: an INCONCLUSIVE answer no longer passes on the loaded header alone. PREDICT: no walking line (as before); LOCKED:
    each direction held 120 frames from the state left counts 0 steps, the tile and the map unchanged (Mom's scene:
    `lockall`, a `msgbox` waiting); THE ARRIVAL by the ROM: the warp the AI used last, [1,1] (7,1) (the 2F stairs:
    `STUCK_WARP`), lands on [1,0] (8,2), a Non-Animated Door, the exit step (0,1) leaves the player on (8,3) == save block
    1's claim; the AI pressed nothing from that arrival on; the fault claim (7,3) disagrees (by the arrival, and its
    own walking trial: the controls are locked).
  * ROAM: the 13 presses that did not move the player are PRE-EMPTED: the battle on screen 16 pad frames after each (the
    press's own two chunks), no move and NO TURN before it (6 of the 13 pressed away from the way the player faced), 13
    distinct battles, 0 presses that left the player standing without one. The strictest reading (every press that did
    not move the player a spin), reported as a NOTE: 14/163 = 0.0859; the criterion stays 1/150 (the design's spin).
  * XP (new): `route101_xp.ss1` (`make_step3_fixtures.py --only xp`: the AI's own errands, then test-side presses to a
    SECOND wild battle, Wurmple L2, saved the frame its HP reached 0; the first battle levelled the Mudkip up, a stats box
    the AI cannot read yet: step 4), goto 120 errands between (6,15) and (7,15) with its own memory loaded. PREDICT
    "goto: stuck: nothing new ... for 3000 frames, the last at f71924: experience gained (1 Pokemon)", 3,600 frames, 137
    presses; ONE novelty line, "experience gained (PID 550a9be6: 441 -> 456)", the clock f71324 -> f71924 (600 frames
    on, once "battle: the battle ended"); the framework's get_party: PID 550a9be6 441 -> 456; wild battles 12 -> 12;
    291 tiles learned at the start and the end; the end tile (7,15) by save block 1 and the game's answer (Up 8 steps to
    a ledge, Right 4 to a wall).
  * XPR (new): REVERT of XP, in-process from a COPY whose `Novelty.update` ignores experience. PREDICT "goto: stuck:
    nothing new ... for 3032 frames, the last at f71324: none", 3,032 frames, 113 presses, no novelty line, the game's
    experience 441 -> 456 all the same; the A/B: 3,032 frames against XP's 3,600 (the gain moved the verdict 568 later).
  * NOT FIXABLE HERE: a proof that the predictions were written before a first look at a graded run needs a commit made
    before it, and this round's worker may make none. `predictions:` shows the predictions a run read; a re-run by
    someone else after reading them (the step-3 verifier's) is the replication.
AFTER THIS ROUND'S FIRST GRADED RUN (2026-10-08, `predictions: sha256:e30501a3689e2b1d`; said here, not folded into
the above): every arm met its predictions, frames and presses included, except ONE check of STUCK, a fault-test of the
INSTRUMENT: the probe claiming (7, 3) had one clean line, "Up: 0 steps, then a wall", and on a state where a scene
holds the controls the game counted 0 steps, so its walking answer AGREED ("by walking True (want False, not True)").
A prediction of no step cannot tell a player before a wall from one who cannot move: `game_answer.py`
`walking_agrees` now also requires a trial that predicts a STEP (unit test `test_a_walking_answer_needs_a_step`, mutant
W29). Every other arm's walking answer has a moving trial (HOUSE Down 3, TOWN and CROP Down 1, ROUTE Down 1, ROAM Down
1 / Right 3, BUMP Down 3, XP Up 8 / Right 4): PREDICT no other change; STUCK's fault claim now "by walking False".
THE SECOND GRADED RUN (`predictions: sha256:0e3682c982d6d2d4`): all 11 arms PASS, every frame and press count as
predicted (HOUSE 3,344 / 52, TOWN 4,969 / 92, ROUTE 2,083 / 108, ROAM 16,646 / 399, CROP 4,640 / 79, STUCK 1,519 / 40,
BUMP 371 / 33, TRN 596 / 1, XP 3,600 / 137, XPR 3,032 / 113, BUMPR 3,123 / 386), STUCK's fault claim "by the arrival
False, by walking False". This docstring was then edited only to say so and to correct grading part 5's sentence on
an INCONCLUSIVE answer; the final run reads the edited text (its own `predictions:` digest) and predicts the same.

AFTER STEP 3.1, THE STEP-3 ADVERSARIAL REVIEW (2026-10-08; PRE-REGISTERED before this round's graded run, from in-process
development runs of the same code on the same starts, seed 3, `gates/hands_harness.py`; the seed sweep `rate_step3.py`
on the same code: 90 of 90 runs as intended). What changed, and what each arm now predicts:
  * finding 1: a tile past an edge is a ROAD only once a crossing of that edge was SEEN (`world/memory.py` outside); the
    explorer leaves Littleroot and Route 101 by the frontier it sees past their top edge. NEW CHECK on TOWN and ROUTE: no
    target chosen as a road before a crossing of its map's edge (`check_no_road_before_a_crossing`).
  * finding 2: a stale frontier target is dropped on the move and turning back costs `TURN_BACK_COST`. NEW CHECK on
    HOUSE, TOWN and ROUTE: REVERSALS on the AI's own steps as the looks confirmed them (`walk_path`, `reversals`: A -> B
    -> A or a U-turn's third step) at most `REVERSALS_MAX` (1: near zero; since the verifier's round `REVERSALS_SEED3`, 0,
    below). PREDICT 0 on each (seed 3). Measured on the
    step-3 code by the same metric (a scratch A/B, seeds 1-10, five exploring plans): 68 reversals in 2,259 steps, among
    them the review's own TOWN seed 3 (11,7) -> (12,7) -> (12,6) -> (11,6) and ROUTE seed 3 (17,9) -> (18,9) -> (17,9);
    this code: 11 in 2,119.
  * finding 3: NEW ARM SCENE, `littleroot_twin.ss1` (`make_step3_fixtures.py --only twin`: the AI's own HOUSE walk on this
    code, saved where it ends; VAR_LITTLEROOT_TOWN_STATE 0), goto (10,4) then (10,0): the twin's coord event at (10,1)
    pushes the player back to (10,2) every time. PREDICT "goto: stuck: the goto at (10, 0) cannot be reached (a scene
    stopped the way there 2 times ... with nothing new since the first)", the scene told exactly twice, 2,471 frames, 37
    presses (6 A, each on a wait), truth on LITTLEROOT_TOWN at [10, 2], VAR_LITTLEROOT_TOWN_STATE still 0, purity CLEAN.
    NEW REVERT ARM SCENER (in-process, a COPY with the rule off): PREDICT the scene 3 times (a round of the twin's scene
    takes ~1,100 frames), "goto: stuck: nothing new ...", 3,570 frames; the A/B against SCENE: 1,099 frames saved.
  * finding 4: a bump belongs to the SIDE it came from. BUMP now PREDICTS the one-way tile (1,4) (IMPASSABLE_SOUTH_AND_
    NORTH) bumped ONCE going down (memory: ((1, 4), 'down') only), then CROSSED from its open sides: errand 2 (0,4) ->
    (1,4) -> (2,4) going right, errand 3 back going left (step 3 walked round it in 4); 307 frames, 25 presses (was 371 /
    33), end [0,4]. BUMPR unchanged: 94 bumps into (1,4), 3,123 frames.
  * finding 5: the eyes see exits by their LOOK, the warp table is test side only. NEW ARM EXITS (`gates/exit_looks.py`, a
    ROM scan, no AI): PREDICT every look the game warps on but the Union Room's in the eyes' table and no warp tile with
    such a look unseen; all 29 warp tiles of Littleroot, Route 101, Oldale and their buildings seen; 1,193 of 1,313 warp
    tiles over 518 maps (the rest: script destinations); FAULT-TEST: without the doormat look the arms' maps lose tiles.
  * finding 6: every crop check uses the gate's own literal window (`gates/window.py` 7 / 5 / 5).
  * finding 7 (audit): no grade compares a post-warp position with a raw warp target (`game_answer.py`'s docstring); STUCK's
    ARRIVAL check now also requires the raw landing (8,2) NOT to be save block 1's position after the transition (8,3).
  * finding 9: ROAM PREDICTS the same trajectory (16,646 frames, 399 presses) and BOTH ratios from the AI's report and from
    the looks: back-and-forth 1/150 = 0.0067 (1 reversal + 0 in place; the criterion, < 2%), strict non-moving 13/163 =
    0.0798 (0 in place + 13 pre-empted by a battle; reported, each pre-emption checked as before).
  * the other arms on this code, seed 3: HOUSE done, 3,176 frames, 36 presses (the 2F frontier dropped as stale on the
    move: 3 decisions); TOWN done, 4,864 frames, 101 presses, 25 decisions; ROUTE done, 633 frames, 71 presses (it meets
    no wild battle now: the game's count +0 == 0 met == 0 fled; fleeing is proven by ROAM's 13); CROP done (the fault arm
    reaches ROUTE101 by another way: it no longer knows a road from the coordinates), 5,156 frames, 94 presses, its first
    town target the door stand tile (5,9) NOT SEEN from where it was first 'seen' (the check no longer asks for a road);
    STUCK unchanged in outcome (ping-pong on 1:1|7,1), 1,357 frames, 24 presses; TRN 596 / 1, XP 3,600 / 137, XPR 3,032 /
    113 unchanged. Found while measuring and fixed before this registration (README "Step 3.1"): TOWN-Catcher seed 8
    went house -> town -> house (the far frontier scored below the door just come out of): the way just come in is now
    no option while the map has somewhere new to go (mutant W43).

AFTER THE STEP-3.1 VERIFIER (2026-10-08; its nine weak proofs; PRE-REGISTERED before this round's graded run, from
in-process development runs of the same code on the same starts, `gates/hands_harness.py` seed 3 (seed 9 for the
replications), a COPY of the package for each revert arm, and the development sweep `rate_step3.py` of this code: 100 of
100 runs as intended, both reverts as predicted). The text above about finding 2's baseline ("68 reversals in 2,259
steps on the step-3 code") was a scratch measurement no file of the tree reproduces: it is superseded by the sweep's
REVERT section (this code with finding 2's two rules reverted, the same plans and seeds, the same metric), PREDICTED: 89
reversals in 2,795 steps and 252 frontier targets walked onto with everything beside them seen, against 11 in 2,119 and
0 with the rules; all 5 exploring plans over the bound when reverted. What changed, and what each arm now predicts:
  * finding 2's live grade did not tell the fixed code from the reverted one at seed 3 (the bound 1; the revert shows 1).
    The seed-3 bound is now that trajectory's own count, 0 on HOUSE, TOWN and ROUTE (`REVERSALS_SEED3`; another seed is
    held to the sweep's per-run bound, now 1), and a second check: NO STALE TARGET WALKED ONTO (`stale_arrivals`: 0 of the
    frontier targets chosen, with targets dropped as stale on the way: HOUSE 1 dropped, TOWN 23, ROUTE 22). NEW REVERT
    ARMS HOUSER, TOWNR, ROUTER (in-process, a COPY with STALE_MUTATIONS): PREDICT HOUSER "explore: done", 3,344 frames, 52
    presses, 1 reversal in 18 steps ((5,6) -> (5,7) -> (5,6)) and 1 stale target walked onto ((5,7) on 2F); TOWNR done,
    4,945 frames, 89 presses, 1 reversal in 36 steps (the review's own u-turn (11,7) -> (12,7) -> (12,6) -> (11,6)), 4
    stale targets walked onto; ROUTER done, 2,083 frames, 108 presses, 1 reversal in 51 steps (the review's own (17,9) ->
    (18,9) -> (17,9)), 4 walked onto (it meets and flees one wild battle). Each breaks its real arm's bound 0, and the A/B
    against the real arm holds.
  * finding 1's live check "never fires": it now also requires the case it is about: targets chosen past a map's REAL
    edge (the ROM's size, `rom_map_sizes`, test side) before a crossing of THAT edge was seen, each chosen as what it looks
    like. PREDICT TOWN 5 such (frontier (11,-1), (10,-2), (11,-3), (11,-4), (11,-5) past Littleroot's top edge), ROUTE 4
    (frontier (15,-1), (8,-2), (12,-3), (4,-1) past Route 101's top edge: the loaded memory's crossing of its BOTTOM edge
    says nothing about the top one), roads among them none. NEW REVERT ARM EDGER (TOWN's start, a COPY with
    EDGE_MUTATION): PREDICT done, 4,880 frames, 103 presses, the road (10,-1) chosen past the uncrossed top edge, so the
    same check FAILS on it; the A/B: TOWN 5 such targets, no road.
  * finding 3 on targets the EXPLORER chose (the verifier: SCENE is a scripted errand): a scene is also counted for the
    tile it began on when it put the player elsewhere; at 2 there, nothing new (PROGRESS: a flag, a Pokemon, items,
    experience) since the first, the tile is not stepped on again in the intent. NEW ARM SCENEX (the explorer from
    `littleroot_twin.ss1` toward ROUTE101, 8,100 frames: it stops outdoors right after the second tile, where the game's
    answer concludes): PREDICT "explore: budget: 7500 frames ran out", 7,511 frames, 304 presses (12 A), 54 decisions; the
    twin by tile {(10,1): 2, (11,1): 2} (the AI's tile == the tile of the look of the walking press it cut short), her
    targets the explorer's own (10,-4) and (11,-4); (10,1) given up at f23710, (11,1) at f25892, neither stepped on after;
    a decision from then on, none behind her; truth on LITTLEROOT_TOWN at (9,2), VAR_LITTLEROOT_TOWN_STATE 0; the game's
    answer agrees. NEW REVERT ARM SCENEXR (a COPY with SCENEX_MUTATION): PREDICT "explore: stuck: nothing new", 6,413
    frames, the twin 3 times on (10,1). SCENE unchanged (2,471 frames, 37 presses; it now also gives (10,1) up); SCENER
    reverts BOTH rules now (per target and per tile: either alone still stops the errand) and is unchanged: 3,570 frames,
    the scene 3 times. THE SWEEP's new plan SCENE-EXPLORE (the same explorer, 9,000 frames, seeds 1-10): PREDICT 10 of 10 as
    intended, the twin at most 2 times a tile on every seed, 2 different targets of the explorer's own stopped on every
    seed, 4 different over the seeds; its SCENE-TILE revert: the twin 3 times on one tile on 10 of 10 seeds (the
    prediction asks for >= 8). ROUTE's FLEE section: 7 of 10 seeds meet a wild battle, each fled and counted by the game.
  * the closed door (the verifier: "stays closed for good"): reopened when a story flag is newly set since, or after
    36,000 frames (unit tests and mutants W46, W47; no arm meets a closed door).
  * ROUTE seed 3 meets no wild battle; NEW REPLICATION ARMS through the launcher at seed 9 (another trajectory, a
    replication, not a replay): TOWN9 PREDICT done, 4,962 frames, 105 presses, 1 reversal in 43 steps ((12,2) -> (13,2) ->
    (12,2); the bound at seed 9 is 1), 5 frontier targets past the top edge, no road, SYS_B_DASH set; ROUTE9 PREDICT done,
    1,820 frames, 89 presses, 0 reversals, ONE wild battle met and FLED (the game's count +1), 5 frontier targets past the
    top edge; both answered by the game.
  * every other arm's trajectory is unchanged (HOUSE 3,176 / 36, TOWN 4,864 / 101, ROUTE 633 / 71, ROAM 16,646 / 399, CROP
    5,156 / 94, STUCK 1,357 / 24, BUMP 307 / 25, TRN 596 / 1, XP 3,600 / 137, XPR 3,032 / 113, BUMPR 3,123, SCENE 2,471 /
    37, SCENER 3,570); the new checks on HOUSE, TOWN and ROUTE: 0 reversals, 0 stale targets walked onto.

AFTER THE STEP-3.1 VERIFIER'S GRADED RUN, SAID HERE (its second round found it unsaid): the prediction above for ROUTER,
"4 walked onto", DID NOT HOLD. The graded run measured 5 frontier targets walked onto with everything beside them seen:
(11,14), (4,13), (4,8), (18,9), (17,4) (the last one's final neighbour, (17,3), first seen at f67623, 64 frames before the
arrival at f67687). Its check asked only for ">= 1", so the arm passed and the miss went unsaid by its run and its README.
An in-process replay of that copy and seed today gives 5 again by the same grader; the development count of 4 was not
kept, so WHY it differed is not established. Since this round every number pre-registered is machine-checked
(`PREDICTED`, `check_predictions`): a number that does not hold FAILS its arm, and the summary counts them.

AFTER THE STEP-3.1 VERIFIER'S SECOND ROUND (2026-10-08, its eight weak proofs; PRE-REGISTERED before this round's graded
run, from a development pass of THIS driver on the same code (its 32 files moved out of the evidence folder: not graded),
in-process development runs (`gates/hands_harness.py`) and a development sweep (`rate_step3.py`)). The NUMBERS are the
`PREDICTED` table below this docstring (machine-checked; pinned with this docstring in `predictions:`). What changed:
  * FINDING 5's guard (it checked syntax only: a `getattr` read passed): NEW ARM WARPREAD (`gates/warp_reads.py`), the REAL
    eyes on 7 starts with every memory read recorded, against the ROM's 444 warp arrays. PREDICT 0 reads overlapping a
    warp array on every start; 5 of the 7 starts stand on a map with warps; the recorder sees each map's MapEvents struct
    read (the signs: one pointer from its warp array); its three plants (an attribute, the verifier's getattr, a raw read
    followed from gMapHeader's events pointer) each caught on the 5 starts with warps (Route 101 has none); the static
    check flags the first two and NOT the raw read (only the scan can see it, and the evidence says so).
  * the twin (finding 3) KNOWN BY HER WORDS ("Um, um, um!"), and NEWS AS PROGRESS: SCENEX now runs to the explorer's OWN
    end (20,000 frames). PREDICT "explore: done: explore to ROUTE101", 16,293 frames, 489 presses: before any news the twin
    sends the player back 3 times ((10,1) twice, then (11,1) once, where the same words close both); May's mother's "Oh,
    hello. And you are?" is news (both tiles worth a try again), the twin once more and both given up again at once; May's
    "Huh? Who... Who are you?" is news (VAR_LITTLEROOT_TOWN_STATE 1); the twin's "Um, hi!" lets the player pass (state 2);
    Route 101 at (11,19), where Birch's rescue scene LOCKS the player: the game's answer is LOCKED + THE ARRIVAL across
    Littleroot's top edge from (11,0) (`SCENEX_CROSSING`, `game_answer.py --after-connection`). SCENEX9 (seed 9, through the
    launcher): the same story, 3 push-backs and none after the news, 14,462 frames. NEW REVERT ARMS: SCENEXR now reverts the
    words rule (4 push-backs before any news, 7 in all, never past her); SCENENR (new words not progress): 3 push-backs,
    stuck in May's house at VAR_LITTLEROOT_TOWN_STATE 1 with the road open, the twin never tried again (the verifier's
    "inside May's house"). SCENER now turns off all three scene rules. THE SWEEP: SCENE-EXPLORE to its own end, the
    SCENE-WORDS and SCENE-NEWS reverts (their predictions in `rate_step3.py` REVERT_PREDICTIONS).
  * FINDING 4's live revert: NEW ARM BUMPSR (one bump walls every side, `revert_step3.py` W34's edit): PREDICT the same one
    bump ((1,4) going down), errands 2 and 3 walked ROUND (4 steps each), BUMP's own crossing check FAILS on it, 371 frames;
    BUMP8 / BUMPSR8 the A/B again at seed 8 (of seeds 1-10 only 3 and 8 walk down into the one-way tile: measured).
  * FINDING 2's A/B at another seed: NEW ARMS TOWN9R, ROUTE9R (the revert at seed 9) and F2AB (every pair together). THE
    CLAIM RESTS ON THE STALE TARGETS WALKED ONTO: PREDICT 0 with the rules on every pair, 23 in all without (HOUSER 1,
    TOWNR 4, ROUTER 5, TOWN9R 8, ROUTE9R 5); reversals 1 with, 6 without, reported (TOWN9R 1 = TOWN9 1: no per-arm claim).
  * HOUSE9: HOUSE at seed 9 through the launcher (3,207 frames, 0 reversals, 1 stale target dropped).
  * every arm that existed before: its trajectory unchanged (`PREDICTED`).
AFTER THIS ROUND'S FIRST GRADED RUN (2026-10-08, said here, not folded into the above): 31 of the 32 arms passed and 113
of the 117 pre-registered numbers held; SCENEX9 FAILED on its numbers alone (every behavioural check passed): predicted
14,462 frames, 439 presses, 3 push-backs [3, 0]; measured 15,959, 489, 4 [3, 1, 0]. The two runs had the same code,
fixture, seed and presses up to f22407, where a person of Littleroot stood elsewhere. CAUSE, MEASURED (an in-process A/B,
the cartridge's clock set by the test side in a throwaway emulator): the game reads the HOST'S CLOCK (mGBA's RTC) at every
map load, and the berry trees' growth over the minutes passed draws from the game's random numbers; with the clock
simulated from 09:00, 11:30, 11:59 or 12:01 SCENEX9 plays 14,462 frames, from 13:37 or 20:00 15,959 (the development pass
ran before about 12:10, the graded run after); the host's clock offset by +6 hours, or the run slowed 4 ms a frame, did not
change it within one window. So "re-running reproduces it exactly" holds only within a window of the clock. THE CHANGES:
every in-process run pins the cartridge's clock (`GAME_CLOCK`, `hands_harness.py --game-clock`); NEW ARM CLOCKS runs every
launcher arm in-process at 8 instants over 12 days: ROAM, SCENEX and SCENEX9 change with the clock (pre-registered
`CLOCK_SENSITIVE`), the other 13 do not; those three now register NO launcher frames or presses (their numbers under
CLOCKS, at the pinned clock, instead), and CLOCKS checks their claims hold at every instant (the twin's push-backs, Route
101 reached, ROAM's 150 steps and spin ratio). RE-REGISTERED from a second development pass of the in-process arms and
CLOCKS (every number held): PREDICTED below; nothing else changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ai_player.brain.navigator import CHUNK_FRAMES  # noqa: E402
from ai_player.gates.live_step2 import (  # noqa: E402
    check_purity, classify_a, clean_env, make_copy, run_json, truth_of,
)
from ai_player.gates.provenance import provenance as tree_provenance  # noqa: E402
from ai_player.hands.dialogue import GENERIC_BUSY  # noqa: E402
from ai_player.host import launcher  # noqa: E402
from ai_player.options import (  # noqa: E402
    ENV_BRAIN, ENV_FAULT_NO_CROP, ENV_GOAL_MAP, ENV_GOTO, ENV_PERSONALITY, ENV_ROAM_STEPS, ENV_SEED, ENV_WORLD,
)
from ai_player.world.memory import WorldMemory  # noqa: E402
#: (build step 3.1, the step-3 review's finding 6) the crop is checked against the SCREEN's window written down on the
#: test side as literals (`gates/window.py`), never the eyes' own VIEW_* (widening both used to pass)
from ai_player.gates.window import on_screen_from as in_window  # noqa: E402

SAVES = REPO / "tools" / "story-dev" / "saves"
GATES = Path(__file__).resolve().parent
EVIDENCE_DIR = REPO / "ai_player" / "evidence"
EVIDENCE_TAG = "step3"
HARNESS = GATES / "hands_harness.py"
#: The step-3 verifier's weak proof 3: the GAME's answer to where the player stands, by its behaviour.
GAME_ANSWER = GATES / "game_answer.py"
#: Arms that end where the player cannot walk (TRN: in a battle): no behavioural answer.
NO_ANSWER = ("TRN",)
PROFILE = "ai-step3-world"
SEED = 3
FRAME_SLACK = 5
SELFTEST_LINE = "[SELFTEST] not run"
#: (path, md5) PINNED.
FIXTURES: dict[str, tuple[Path, str]] = {
    "house_2f_clockset.ss1": (GATES / "fixtures" / "house_2f_clockset.ss1", "2cc0b61450870d34646f7583bfd0c787"),
    "pokedex_done.ss1": (SAVES / "pokedex_done.ss1", "380fba7a4bf4afdf2fc9a0ad158de29e"),
    "route101_south.ss1": (GATES / "fixtures" / "route101_south.ss1", "81bf318a1532c5364f60064530f9984b"),
    "route101_south.world.jsonl": (GATES / "fixtures" / "route101_south.world.jsonl", "dae9c609f1b55ad76fd7f310d9cc35f5"),
    "clock_room.ss1": (GATES / "fixtures" / "clock_room.ss1", "5d1d0ce0974470bf11040fc39f832041"),
    "trainer_battle_r116.ss1": (GATES / "fixtures" / "trainer_battle_r116.ss1", "f55f3c2ec6efb9fb20363e8ca92b73ba"),
    "route101_xp.ss1": (GATES / "fixtures" / "route101_xp.ss1", "ac5bc2645ad980386be12d2b4a8704e6"),
    "route101_xp.world.jsonl": (GATES / "fixtures" / "route101_xp.world.jsonl", "ce8287a37f03394b19fcb3e28f964feb"),
    # build step 3.1 (`make_step3_fixtures.py --only twin`): Littleroot after the player's first walk out of the house
    "littleroot_twin.ss1": (GATES / "fixtures" / "littleroot_twin.ss1", "fe4661736a30dd3f34b87c0db7ae1d10"),
}
#: Maps by (group, number) (`data/maps/map_groups.json`; the truth reads save block 1's location).
LITTLEROOT, ROUTE101, OLDALE, LAB, HOUSE_1F, HOUSE_2F = [0, 9], [0, 16], [0, 10], [1, 4], [1, 0], [1, 1]
#: BUMP's errands and its learned tile (2F of the player's house; `data/maps/LittlerootTown_BrendansHouse_2F`).
BUMP_ERRANDS, BUMP_TILE = "0,4;2,4;0,4", (1, 4)
#: The prefixes of a WALKING gate (`brain/navigator.py`, `skills/roam_train.py`).
WALK_GATES = ("walk ", "keep walking ", "use the ", "roam ")
#: BUMPR: the bump is told and NOT remembered (`world/memory.py` WorldMemory.learn_bump).
BUMPR_MUTATION = ("world/memory.py", "        memory.bumped[key] = info\n",
                  "        pass  # MUTANT BUMPR: the bump is not remembered\n")
#: (build step 3.1, finding 3) SCENE: errands past Littleroot's twin, who pushes a player with no Pokemon back from the
#: road every time (`make_step3_fixtures.py` twin); SCENER: the same with the scene-repeat rule off, in a COPY.
SCENE_ERRANDS, SCENE_TARGET, SCENE_PUSHED_TO = "10,4;10,0", (10, 0), [10, 2]
SCENER_MUTATION = ("brain/navigator.py", "        if len(hits) >= SCENE_REPEATS and novelty.last_progress <= hits[0]:\n",
                   "        if False:  # MUTANT SCENER: a repeating scene is never held against its target\n")
SCENE_LINE = f"a scene stopped the way to the goto at {SCENE_TARGET}"
#: (build step 3.1, finding 2) Reversals a walking arm may show. (The step-3.1 verifier's round: with the bound 1 the live
#: grade passed the REVERTED code too at seed 3, which shows 1 reversal on each of HOUSE, TOWN and ROUTE.) At seed 3 the
#: bound is the pre-registered count of this code's seed-3 trajectory, 0 on each ("AFTER THE STEP-3.1 VERIFIER" in the
#: docstring); the revert arms HOUSER, TOWNR and ROUTER play the same starts and seed with the rules reverted and must
#: break it. Another seed (the replication arms) is held to the sweep's per-run bound, `REVERSALS_PER_RUN`.
REVERSALS_SEED3 = {"HOUSE": 0, "TOWN": 0, "ROUTE": 0}
REVERSALS_PER_RUN = 1
#: (the step-3.1 verifier's round) finding 2 REVERTED, both rules (`gates/revert_step3.py` W31 + W32): a stale target is
#: kept until it is walked onto, and turning back costs nothing (the arms HOUSER, TOWNR, ROUTER; `rate_step3.py` REVERT)
STALE_MUTATIONS = (
    ("brain/navigator.py", "                stale = stale_reason(memory, target) if memory is not None else None\n",
     "                stale = None  # MUTANT (finding 2 reverted): a stale target is kept until it is walked onto\n"),
    ("brain/navigator.py", "        if not steps:\n            return {}\n",
     "        if True:  # MUTANT (finding 2 reverted): no cost for turning back\n            return {}\n"),
)
#: (the step-3.1 verifier's round) finding 1 REVERTED (`revert_step3.py` W30): a map's top and left ends known from
#: negative coordinates again (arm EDGER: the live check "no road before a crossing" must FAIL on it)
EDGE_MUTATION = ("world/memory.py", "        return any(past_edge(self.edges, xy, side) for side in self.edges)\n",
                 "        return xy[0] < 0 or xy[1] < 0 or any(past_edge(self.edges, xy, side) for side in self.edges)  # MUTANT (finding 1 reverted)\n")
#: (the step-3.1 verifier's round) SCENEX: the EXPLORER (not an errand) from the twin's fixture toward Route 101: the targets
#: behind the twin are its own choices; SCENEXR: the count per tile a scene began on off (`revert_step3.py` W44), in a COPY
SCENEX_MUTATION = ("brain/navigator.py",
                   "            if len(spots) >= SCENE_REPEATS and novelty.last_progress <= spots[0] and began not in walled:\n",
                   "            if False:  # MUTANT SCENEXR: no count per tile a scene began on\n")
#: (the step-3.1 verifier's second round) a scene known by its WORDS (`brain/navigator.py` scene_words) REVERTED: scenes
#: are counted per target and per tile only, as in the verifier's round (arm SCENEXR; `revert_step3.py` W52; the sweep's
#: SCENE-WORDS revert): the twin, who guards two tiles, is met twice on EACH
SCENEWORDS_MUTATION = ("brain/navigator.py", "            if words is not None:\n",
                       "            if False:  # MUTANT SCENEWORDS: a scene is not known by its words\n")
#: SCENER, the errand's revert, turns off every scene rule: per target, per tile and by its words (either one alone
#: still stops the errand)
SCENER_ALL = (SCENER_MUTATION, SCENEX_MUTATION, SCENEWORDS_MUTATION)
#: (the step-3.1 verifier's second round) NEW WORDS are not progress (`revert_step3.py` W53): meeting May lifts nothing,
#: so the explorer never tries the twin again (arm SCENENR; the sweep's SCENE-NEWS revert)
NEWS_MUTATION = ("brain/navigator.py", "                if stayed and novelty.heard(words, ended):\n",
                 "                if False:  # MUTANT SCENENR: new words heard are not progress\n")
#: The twin's coord events on LITTLEROOT_TOWN (`data/maps/LittlerootTown/map.json`: LittlerootTown_EventScript_
#: NeedPokemonTriggerLeft / Right at (10, 1) and (11, 1), VAR_LITTLEROOT_TOWN_STATE 0)
TWIN_TILES = ((10, 1), (11, 1))
#: (the step-3.1 verifier's second round: "the twin guards two tiles, so the explorer meets her 4 times in total") the
#: twin's scenes in ALL one explorer run may show: twice on the first tile, then once on the second, where the same
#: words close both (pre-registered, a literal: `SCENE_REPEATS` is the AI's own number, not the grade's)
TWIN_SCENES_IN_ALL = 3
#: (the step-3.1 verifier's second round: "FINDING 4 ... has no live revert arm") the per-SIDE bump REVERTED
#: (`revert_step3.py` W34): one bump from any side refuses the tile from every side, the step-3 rule (arm BUMPSR)
BUMPSIDE_MUTATION = ("brain/navigator.py", "    tried = memory.bumps(nxt, direction)\n",
                     "    tried = BUMP_GIVE_UP * max(memory.bumps(nxt, d) for d in DIRECTIONS)  # MUTANT BUMPSR: a bump walls every side\n")
#: (the step-3.1 verifier's second round: "FINDING 5's guard only checks syntax") the behavioural guard: every read the
#: real eyes make, against every map's warp array (`gates/warp_reads.py`, arm WARPREAD)
WARP_READS = GATES / "warp_reads.py"
#: (the step-3.1 verifier's second round, FOUND by its own graded run: SCENEX9 played 15,959 frames where its development
#: run, the same seed, fixture and code, played 14,462) THE GAME READS THE HOST'S CLOCK (mGBA's RTC: berry trees grow by
#: the minutes passed at every map load, and a tree reaching its berries draws from the game's random numbers), so a
#: launcher run's trajectory can depend on WHEN it is played. Every in-process run of this driver pins the cartridge's
#: clock to `GAME_CLOCK` (`hands_harness.py --game-clock`: it runs from there at the emulated speed), so it is the same run
#: whenever it is played; the launcher arms cannot (the AI may not set the clock, the framework has no option for it).
GAME_CLOCK = "2026-10-08T06:00"
#: Arm CLOCKS: every launcher arm in-process with the clock pinned at each of these instants (a day apart and more: the
#: berry trees' stages take hours to days), and the launcher arms MEASURED (development sweep, 2026-10-08) to change their
#: trajectory with the clock: their launcher runs register no frame or press counts in `PREDICTED`, only what holds at
#: any clock (their graders' checks), and their trajectory at `GAME_CLOCK` is registered under CLOCKS instead.
CLOCK_INSTANTS = ("2026-10-08T06:00", "2026-10-08T11:00", "2026-10-08T12:30", "2026-10-08T18:00", "2026-10-09T06:00",
                  "2026-10-10T12:00", "2026-10-14T12:00", "2026-10-20T12:00")
CLOCK_SENSITIVE = ("ROAM", "SCENEX", "SCENEX9")
#: (the step-3.1 verifier's second round: "A PRE-REGISTERED PREDICTION DID NOT HOLD AND THIS IS NOT SAID ANYWHERE") the
#: NUMBERS this round pre-registers (from the development pass named in the docstring's "AFTER THE STEP-3.1 VERIFIER'S
#: SECOND ROUND"), machine-checked by `check_predictions` on every arm listed: frames and presses (the trajectory), and
#: each measure a grader takes (`Run.measure`). A number that does not hold FAILS that arm's check "PRE-REGISTERED
#: NUMBERS", and the summary counts them. Read from the FILE at the start of the run and pinned in `predictions:`.
PREDICTED: dict[str, dict] = {
    "HOUSE": {"frames": 3176, "presses": 36, "reversals": 0, "stale_dropped": 1, "stale_walked": 0, "steps": 10},
    "TOWN": {"frames": 4864, "presses": 101, "reversals": 0, "stale_dropped": 23, "stale_walked": 0, "steps": 41},
    "ROUTE": {"frames": 633, "presses": 71, "reversals": 0, "stale_dropped": 22, "stale_walked": 0, "steps": 35},
    # ROAM, SCENEX, SCENEX9: CLOCK-SENSITIVE (arm CLOCKS): no frame or press count for a launcher run; see "CLOCKS"
    "CROP": {"frames": 5156, "presses": 94},
    "STUCK": {"frames": 1357, "presses": 24},
    "BUMP": {"bumps": 1, "frames": 307, "presses": 25},
    "BUMPR": {"frames": 3123, "presses": 386},
    "TRN": {"frames": 596, "presses": 1},
    "XP": {"frames": 3600, "presses": 137},
    "XPR": {"frames": 3032, "presses": 113},
    "SCENE": {"frames": 2471, "presses": 37},
    "SCENER": {"frames": 3570, "presses": 43},
    "SCENEXR": {"frames": 13316, "presses": 385, "twin_pushes": 7, "twin_segments": [4, 3]},
    "SCENENR": {"frames": 13066, "presses": 391, "twin_pushes": 3},
    "HOUSER": {"frames": 3344, "presses": 52, "reversals": 1, "stale_walked": 1, "steps": 18},
    "TOWNR": {"frames": 4945, "presses": 89, "reversals": 1, "stale_walked": 4, "steps": 36},
    "ROUTER": {"frames": 2083, "presses": 108, "reversals": 1, "stale_walked": 5, "steps": 51},
    "EDGER": {"frames": 4880, "presses": 103},
    "TOWN9": {"frames": 4962, "presses": 105, "reversals": 1, "stale_dropped": 27, "stale_walked": 0, "steps": 43},
    "ROUTE9": {"frames": 1820, "presses": 89, "reversals": 0, "stale_dropped": 24, "stale_walked": 0, "steps": 40},
    "WARPREAD": {"plant_attribute_caught": 5, "plant_getattr_caught": 5, "plant_raw_caught": 5},
    "BUMPSR": {"bumps": 1, "errand_steps": [4, 4], "frames": 371, "presses": 33},
    "TOWN9R": {"frames": 5742, "presses": 178, "reversals": 1, "stale_walked": 8, "steps": 83},
    "ROUTE9R": {"frames": 4220, "presses": 114, "reversals": 2, "stale_walked": 5, "steps": 48},
    "HOUSE9": {"frames": 3207, "presses": 36, "reversals": 0, "stale_dropped": 1, "stale_walked": 0, "steps": 10},
    "BUMP8": {"bumps": 1, "frames": 264, "presses": 25},
    "BUMPSR8": {"bumps": 1, "errand_steps": [4, 4], "frames": 328, "presses": 33},
    "F2AB": {"reversals_real": 1, "reversals_revert": 6, "stale_walked_real": 0, "stale_walked_revert": 23},
    # every launcher arm in-process with the cartridge's clock pinned at GAME_CLOCK (development clock sweep, 2026-10-08)
    "CLOCKS": {"clock_sensitive": ["ROAM", "SCENEX", "SCENEX9"],
               "HOUSE@pinned": [3176, 36], "TOWN@pinned": [4864, 101], "ROUTE@pinned": [633, 71], "ROAM@pinned": [16646, 399],
               "CROP@pinned": [5156, 94], "STUCK@pinned": [1357, 24], "BUMP@pinned": [307, 25], "TRN@pinned": [596, 1],
               "XP@pinned": [3600, 137], "SCENE@pinned": [2471, 37], "SCENEX@pinned": [16293, 489], "TOWN9@pinned": [4962, 105],
               "ROUTE9@pinned": [1820, 89], "HOUSE9@pinned": [3207, 36], "BUMP8@pinned": [264, 25],
               "SCENEX9@pinned": [14462, 439]},
}
#: The replication arms (another seed, the launcher): the arm they replay, and its seed
REPLICATION_SEED = 9
#: (the step-3.1 verifier's second round) BUMP's replication seed: of seeds 1-10 only 3 and 8 plan errand 1 down from
#: (1, 3) into the one-way tile (measured with `hands_harness.py`, 2026-10-08); at seed 9 nothing is bumped, which would
#: leave the per-side rule unexercised
BUMP_REPLICATION_SEED = 8
#: (build step 3.1, finding 5) EXITS: the ROM's warp table against the exits the eyes see by their look (test side).
EXIT_LOOKS = GATES / "exit_looks.py"
ARM_MAP_PREFIXES = ("LITTLEROOT_TOWN", "ROUTE101", "OLDALE_TOWN")
#: (the step-3 verifier's second round) STUCK: the warp the AI used last, PRE-REGISTERED (the 2F stairs), whose ROM
#: arrival `gates/game_answer.py --after-warp` predicts; the arms answered that way.
STUCK_WARP = ([1, 1], [7, 1])
#: (the step-3.1 verifier's second round) SCENEX's end: the explorer walks off Littleroot's top edge at (11, 0) (the twin's
#: GoSaveBirch tile: VAR_LITTLEROOT_TOWN_STATE 1 after May) into Route 101, where Birch's rescue scene locks the player on
#: arrival; THE ARRIVAL across that connection is what the game's answer checks (`game_answer.py --after-connection`)
SCENEX_CROSSING = ([0, 9], [11, 0], "up")
#: The arms answered by THE ARRIVAL when the game is LOCKED: the kind of the last crossing and its pre-registered value
ARRIVALS: dict[str, tuple[str, tuple]] = {"STUCK": ("warp", STUCK_WARP), "SCENEX": ("connection", SCENEX_CROSSING),
                                          "SCENEX9": ("connection", SCENEX_CROSSING)}
ARRIVAL_ARMS = tuple(ARRIVALS)
#: XP: errands back and forth between two KNOWN floor tiles beside the battle's grass (`make_step3_fixtures.py` xp:
#: the AI's own memory saw their windows), more than the novelty window can hold, so the intent ends "stuck: nothing
#: new" and its CLOCK is the subject; XPR: experience gained is not novelty (`brain/navigator.py` Novelty.update).
XP_ERRANDS = ";".join(["6,15", "7,15"] * 60)
XPR_MUTATION = ("brain/navigator.py", "            if gained:\n                new.append(f\"experience gained ({len(gained)} Pokemon)\")\n",
                "            if False:  # MUTANT XPR: experience gained is not novelty\n"
                "                new.append(f\"experience gained ({len(gained)} Pokemon)\")\n")
#: The navigator's novelty line (`brain/navigator.py` Navigator.run) and its stuck reason.
NOVELTY_PREFIX = "novelty at f"
STUCK_NOTHING_NEW = re.compile(r"stuck: nothing new \(.*?\) for (\d+) frames, the last at f(\d+): (.*?) \(\d+ steps")


@dataclass
class Arm:
    name: str
    title: str
    brain: str
    fixture: str
    frames: int
    wall: float
    env: dict[str, str] = field(default_factory=dict)
    kind: str = "launcher"  # or "harness" (in-process, from a COPY of the package)
    args: tuple[str, ...] = ()
    mutations: tuple = ()
    doc: str = ""
    #: (the step-3.1 verifier's round) the arm's own seed (None: the run's `--seed`), and the arm it replays or reverts
    #: (its grader's partner: a replication at another seed, or the A/B of a revert arm)
    seed: int | None = None
    base: str = ""

    @property
    def run_seed(self) -> int:
        return self.seed if self.seed is not None else SEED


@dataclass
class Run:
    arm: Arm
    command: list[str] = field(default_factory=list)
    exit_code: int = -1
    elapsed: float = 0.0
    started: float = 0.0
    stdout: str = ""
    run_dir: Path | None = None
    verdict: dict | None = None
    records: list[dict] = field(default_factory=list)
    ai_log: str = ""
    before: dict | None = None
    after: dict | None = None
    state_mtime: float | None = None
    world: dict | None = None
    harness: dict | None = None
    answer: dict | None = None  # gates/game_answer.py on the state left, for save block 1's claim
    answer_fault: dict | None = None  # the same probe claiming a neighbouring tile it rules out: must disagree
    checks: list[tuple[bool, str]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    #: (the step-3.1 verifier's second round) the numbers a grader measured that `PREDICTED` may pre-register, and each
    #: pre-registered number against its measure: (name, predicted, measured, held)
    measures: dict = field(default_factory=dict)
    predictions: list = field(default_factory=list)

    def check(self, ok: bool, text: str) -> None:
        self.checks.append((bool(ok), text))

    def measure(self, name: str, value) -> None:
        self.measures[name] = value

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(ok for ok, _ in self.checks)

    @property
    def outcome(self) -> str:
        return ((self.verdict or {}).get("facts") or {}).get("exit_reason") or (self.harness or {}).get("reason") or ""

    @property
    def presses(self) -> list[dict]:
        return [r for r in self.records if str(r.get("action", "")).startswith(("press ", "hold "))]


STORY = {ENV_PERSONALITY: "Story"}
ARMS: list[Arm] = [
    Arm("HOUSE", "leave the player's house: down the stairs, out the door into Littleroot", "explore", "house_2f_clockset.ss1",
        12000, 600.0, {ENV_GOAL_MAP: "LITTLEROOT_TOWN", **STORY}, doc="gates/make_step3_fixtures.py (house_2f_clockset.build.json)"),
    Arm("TOWN", "from Birch's lab, knowing nothing of Littleroot, explore to the road to Route 101", "explore", "pokedex_done.ss1",
        20000, 900.0, {ENV_GOAL_MAP: "ROUTE101", **STORY}, doc="tools/story-dev/saves/pokedex_done.ss1 (Birch's lab, the Pokedex got)"),
    Arm("ROUTE", "explore Route 101 to Oldale Town (a map connection), fleeing any wild battle, from the TOWN walk's memory",
        "explore", "route101_south.ss1", 24000, 900.0,
        {ENV_GOAL_MAP: "OLDALE_TOWN", ENV_WORLD: str(FIXTURES["route101_south.world.jsonl"][0]), **STORY},
        doc="gates/make_step3_fixtures.py (route101_south.build.json): the AI's own TOWN walk, its state and its memory"),
    Arm("ROAM", "roam-train 150 steps through Route 101's grass, fleeing every wild battle", "roam", "route101_south.ss1",
        40000, 1200.0, {ENV_ROAM_STEPS: "150", ENV_PERSONALITY: "Catcher"}, doc="as ROUTE (the state only: it knows nothing)"),
    Arm("CROP", "FAULT the crop off (the eyes show the whole map): the TOWN start and goal", "explore", "pokedex_done.ss1", 20000,
        900.0, {ENV_GOAL_MAP: "ROUTE101", ENV_FAULT_NO_CROP: "1", **STORY}, doc="as TOWN"),
    Arm("STUCK", "an unreachable goal: out of the house with the clock not set (Mom sends the player back up)", "explore",
        "clock_room.ss1", 12000, 600.0, {ENV_GOAL_MAP: "LITTLEROOT_TOWN", **STORY},
        doc="gates/make_clock_fixture.py (clock_room.build.json): VAR_LITTLEROOT_INTRO_STATE 5"),
    Arm("BUMP", "errands in the player's room across a tile the eyes call walkable: bumped once, then avoided", "goto",
        "house_2f_clockset.ss1", 6000, 600.0, {ENV_GOTO: BUMP_ERRANDS, **STORY}, doc="as HOUSE"),
    Arm("BUMPR", "REVERT of BUMP: bump learning off in a COPY: the same tile bumped again and again", "goto",
        "house_2f_clockset.ss1", 6000, 600.0, kind="harness", args=("--goto", BUMP_ERRANDS, "--personality", "Story"),
        mutations=(BUMPR_MUTATION,), doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)"),
    Arm("TRN", "a trainer battle (out of scope for step 3): the reason, no press on the battle's menu", "explore",
        "trainer_battle_r116.ss1", 6000, 600.0, {ENV_GOAL_MAP: "OLDALE_TOWN", **STORY},
        doc="gates/make_trainer_fixture.py: a trainer battle on Route 116 just begun"),
    Arm("XP", "a wild battle won (the experience not yet given), then errands over KNOWN tiles: the experience is the intent's "
        "only novelty, and it moves the intent's clock", "goto", "route101_xp.ss1", 8000, 600.0,
        {ENV_GOTO: XP_ERRANDS, ENV_WORLD: str(FIXTURES["route101_xp.world.jsonl"][0]), **STORY},
        doc="gates/make_step3_fixtures.py --only xp (route101_xp.build.json): the AI's own errands, then test-side presses "
            "to a second wild battle whose foe's HP just reached 0"),
    Arm("XPR", "REVERT of XP: experience is not novelty, in a COPY: no novelty line, the clock never moves", "goto",
        "route101_xp.ss1", 8000, 600.0, kind="harness",
        args=("--goto", XP_ERRANDS, "--personality", "Story", "--world-in", str(FIXTURES["route101_xp.world.jsonl"][0])),
        mutations=(XPR_MUTATION,), doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)"),
    # ---- build step 3.1 (the step-3 adversarial review)
    Arm("SCENE", "errands past Littleroot's twin (no Pokemon yet): the same scene pushes the player back each time; the target "
        "is given up after the second", "goto", "littleroot_twin.ss1", 6000, 600.0, {ENV_GOTO: SCENE_ERRANDS, **STORY},
        doc="gates/make_step3_fixtures.py --only twin (littleroot_twin.build.json): the AI's own walk out of the house"),
    Arm("SCENER", "REVERT of SCENE: the scene-repeat rules off (per target and per tile), in a COPY: the scene again and again "
        "until the novelty window", "goto", "littleroot_twin.ss1", 8000, 600.0, kind="harness",
        args=("--goto", SCENE_ERRANDS, "--personality", "Story"), mutations=SCENER_ALL,
        doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)", base="SCENE"),
    Arm("EXITS", "the ROM's warp table (test side) against the exits the eyes see by their LOOK", "-", "littleroot_twin.ss1",
        0, 600.0, kind="rom", doc="gates/exit_looks.py: every map of the ROM, read only"),
    # ---- the step-3.1 verifier's round
    Arm("SCENEX", "the EXPLORER (its own targets) from the twin's fixture toward Route 101, to its own end: the twin known by "
        "her words, at most 3 meetings in all, every tile she guards given up, the rest of the town explored", "explore",
        "littleroot_twin.ss1", 20000, 900.0, {ENV_GOAL_MAP: "ROUTE101", **STORY},
        doc="gates/make_step3_fixtures.py --only twin (littleroot_twin.build.json)"),
    Arm("SCENEXR", "REVERT of SCENEX: a scene not known by its words (per target and per tile only), in a COPY: the twin twice "
        "on EACH of her two tiles", "explore", "littleroot_twin.ss1", 20000, 900.0, kind="harness",
        args=("--goal-map", "ROUTE101", "--personality", "Story"), mutations=(SCENEWORDS_MUTATION,),
        doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)", base="SCENEX"),
    Arm("SCENENR", "REVERT of SCENEX: new words are not progress, in a COPY: May lifts nothing, the twin is never tried again, "
        "the run stops in May's house", "explore", "littleroot_twin.ss1", 20000, 900.0, kind="harness",
        args=("--goal-map", "ROUTE101", "--personality", "Story"), mutations=(NEWS_MUTATION,),
        doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)", base="SCENEX"),
    Arm("HOUSER", "REVERT of HOUSE: finding 2's two rules off (a stale target kept, no turn-back cost), in a COPY", "explore",
        "house_2f_clockset.ss1", 12000, 600.0, kind="harness",
        args=("--goal-map", "LITTLEROOT_TOWN", "--personality", "Story"), mutations=STALE_MUTATIONS,
        doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)", base="HOUSE"),
    Arm("TOWNR", "REVERT of TOWN: finding 2's two rules off, in a COPY", "explore", "pokedex_done.ss1", 20000, 900.0,
        kind="harness", args=("--goal-map", "ROUTE101", "--personality", "Story"), mutations=STALE_MUTATIONS,
        doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)", base="TOWN"),
    Arm("ROUTER", "REVERT of ROUTE: finding 2's two rules off, in a COPY", "explore", "route101_south.ss1", 24000, 900.0,
        kind="harness", args=("--goal-map", "OLDALE_TOWN", "--personality", "Story", "--world-in",
                              str(FIXTURES["route101_south.world.jsonl"][0])), mutations=STALE_MUTATIONS,
        doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)", base="ROUTE"),
    Arm("EDGER", "REVERT of TOWN's finding 1: a map's ends known from negative coordinates again, in a COPY: the live check "
        "'no road before a crossing' must FAIL on it", "explore", "pokedex_done.ss1", 20000, 900.0, kind="harness",
        args=("--goal-map", "ROUTE101", "--personality", "Story"), mutations=(EDGE_MUTATION,),
        doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)", base="TOWN"),
    Arm("TOWN9", "REPLICATION of TOWN at seed 9 (another trajectory, through the launcher)", "explore", "pokedex_done.ss1",
        20000, 900.0, {ENV_GOAL_MAP: "ROUTE101", **STORY}, doc="as TOWN", seed=REPLICATION_SEED, base="TOWN"),
    Arm("ROUTE9", "REPLICATION of ROUTE at seed 9 (another trajectory, through the launcher): a wild battle met and fled", "explore",
        "route101_south.ss1", 24000, 900.0,
        {ENV_GOAL_MAP: "OLDALE_TOWN", ENV_WORLD: str(FIXTURES["route101_south.world.jsonl"][0]), **STORY},
        doc="as ROUTE", seed=REPLICATION_SEED, base="ROUTE"),
    # ---- the step-3.1 verifier's second round
    Arm("WARPREAD", "the REAL eyes on every start, every memory read recorded, against every map's warp array (and three "
        "plants: an attribute, a getattr, a raw read: each caught)", "-", "littleroot_twin.ss1", 0, 1800.0, kind="warp",
        doc="gates/warp_reads.py: the eyes in a throwaway emulator, read only"),
    Arm("BUMPSR", "REVERT of BUMP's per-side rule: one bump walls the tile from every side (the step-3 rule), in a COPY: the "
        "one-way tile is walked round, not crossed", "goto", "house_2f_clockset.ss1", 6000, 600.0, kind="harness",
        args=("--goto", BUMP_ERRANDS, "--personality", "Story"), mutations=(BUMPSIDE_MUTATION,),
        doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)", base="BUMP"),
    Arm("TOWN9R", "REVERT of TOWN9: finding 2's two rules off, in a COPY, seed 9 (the A/B replicated at another seed)",
        "explore", "pokedex_done.ss1", 20000, 900.0, kind="harness", args=("--goal-map", "ROUTE101", "--personality", "Story"),
        mutations=STALE_MUTATIONS, doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)",
        seed=REPLICATION_SEED, base="TOWN9"),
    Arm("ROUTE9R", "REVERT of ROUTE9: finding 2's two rules off, in a COPY, seed 9 (the A/B replicated at another seed)",
        "explore", "route101_south.ss1", 24000, 900.0, kind="harness",
        args=("--goal-map", "OLDALE_TOWN", "--personality", "Story", "--world-in", str(FIXTURES["route101_south.world.jsonl"][0])),
        mutations=STALE_MUTATIONS, doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)",
        seed=REPLICATION_SEED, base="ROUTE9"),
    Arm("HOUSE9", "REPLICATION of HOUSE at seed 9 (another trajectory, through the launcher)", "explore", "house_2f_clockset.ss1",
        12000, 600.0, {ENV_GOAL_MAP: "LITTLEROOT_TOWN", **STORY}, doc="as HOUSE", seed=REPLICATION_SEED, base="HOUSE"),
    Arm("BUMP8", "REPLICATION of BUMP at seed 8 (another path noise, through the launcher; of seeds 1-10 only 3 and 8 walk "
        "down into the one-way tile, measured): bumped once from above, crossed from its open sides", "goto",
        "house_2f_clockset.ss1", 6000, 600.0, {ENV_GOTO: BUMP_ERRANDS, **STORY}, doc="as HOUSE", seed=BUMP_REPLICATION_SEED,
        base="BUMP"),
    Arm("BUMPSR8", "REVERT of BUMP8: one bump walls every side, in a COPY, seed 8 (the A/B replicated at another seed)", "goto",
        "house_2f_clockset.ss1", 6000, 600.0, kind="harness", args=("--goto", BUMP_ERRANDS, "--personality", "Story"),
        mutations=(BUMPSIDE_MUTATION,), doc="gates/hands_harness.py from a copy of the package (in-process, not a purity proof)",
        seed=BUMP_REPLICATION_SEED, base="BUMP8"),
    Arm("SCENEX9", "REPLICATION of SCENEX at seed 9 (another trajectory, through the launcher)", "explore", "littleroot_twin.ss1",
        20000, 900.0, {ENV_GOAL_MAP: "ROUTE101", **STORY}, doc="as SCENEX", seed=REPLICATION_SEED, base="SCENEX"),
    Arm("F2AB", "FINDING 2's live A/B over every pair of this session (HOUSE, TOWN, ROUTE at seed 3, TOWN9, ROUTE9 at seed 9, "
        "each against its revert): which discriminator the claim rests on", "-", "pokedex_done.ss1", 0, 60.0, kind="summary",
        doc="no run: the graded runs of this session"),
    Arm("CLOCKS", "THE GAME'S CLOCK: every launcher arm in-process with the cartridge's clock pinned at 8 instants over 12 days: "
        "which trajectories depend on WHEN a run is played", "-", "pokedex_done.ss1", 0, 2400.0, kind="clock",
        doc="gates/hands_harness.py --game-clock, every launcher arm's own start, seed and options (in-process)"),
]


# ---------------------------------------------------------------------- running
def run_arm(arm: Arm, build_root: Path) -> Run:
    run = Run(arm)
    profile_dir, _ = launcher.ensure_profile(build_root, PROFILE)
    if not (profile_dir / launcher.PROFILE_MARKER).is_file():
        raise SystemExit(f"profile {PROFILE} is not ai_player-owned; refusing to touch it")
    launcher.force_http_off(profile_dir)
    cheats = profile_dir / "game_cheats.yml"
    if cheats.exists():
        cheats.unlink()
    run.before, raw = truth_of(FIXTURES[arm.fixture][0])
    if run.before is None:
        run.notes.append(f"truth of the fixture failed: {raw[-1500:]}")
    run.run_dir = profile_dir / "ai_player_runs" / f"{time.strftime('%Y%m%d-%H%M%S')}-{arm.name}"
    run.command = [sys.executable, "-m", "ai_player", "run", "--profile", PROFILE, "--frames", str(arm.frames),
                   "--wall-seconds", f"{arm.wall:g}", "--build-root", str(build_root), "--run-dir", str(run.run_dir),
                   "--state", str(FIXTURES[arm.fixture][0])]
    env = clean_env({ENV_BRAIN: arm.brain, ENV_SEED: str(arm.run_seed), **arm.env})
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    run.started = time.time()
    began = time.monotonic()
    proc = subprocess.Popen(run.command, cwd=str(REPO), env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, creationflags=flags)
    try:
        raw_out, _ = proc.communicate(timeout=arm.wall + 240)
    except subprocess.TimeoutExpired:
        launcher.kill_tree(proc)
        raw_out, _ = proc.communicate()
        raw_out = (raw_out or b"") + b"\n[DRIVER] the run overran the driver's own wall clock; process tree killed\n"
    run.elapsed = time.monotonic() - began
    run.exit_code = proc.returncode if proc.returncode is not None else -9
    run.stdout = raw_out.decode("utf-8", errors="replace")
    run.verdict = launcher.read_verdict(run.run_dir)
    actions = run.run_dir / "actions.jsonl"
    if actions.is_file():
        run.records = [json.loads(line) for line in actions.read_text(encoding="utf-8").splitlines() if line.strip()]
    log = run.run_dir / "ai_player.log"
    if log.is_file():
        run.ai_log = log.read_text(encoding="utf-8", errors="replace")
    run.world = last_world(run.run_dir / "world.jsonl")
    state = profile_dir / launcher.STATE_FILE
    if state.is_file():
        run.state_mtime = state.stat().st_mtime
        run.after, raw = truth_of(state)
        if run.after is None:
            run.notes.append(f"truth of the state left behind failed: {raw[-1500:]}")
        elif arm.name not in NO_ANSWER:
            kind = ARRIVALS.get(arm.name, (None,))[0]
            warp = last_ai_warp(run) if kind == "warp" else None
            crossing = last_ai_connection(run) if kind == "connection" else None
            run.answer, run.answer_fault = game_answer(state, run.after, warp, crossing)
    return run


def last_ai_warp(run: Run) -> tuple[list[int], list[int]] | None:
    """The warp the AI used LAST, by its own memory (map key "g:n", the warp tile): what `game_answer.py --after-warp`
    is asked about (the grader also checks it is the pre-registered `STUCK_WARP`)."""
    used = [t for t in transitions(run) if t[3] == "warp" and t[4] == "ai" and t[5] is not None]
    if not used:
        return None
    group, number = (int(v) for v in str(used[-1][1]).split(":"))
    return [group, number], [int(v) for v in used[-1][5]]


def last_ai_connection(run: Run) -> tuple[list[int], list[int], str] | None:
    """(the step-3.1 verifier's second round) The map edge the AI walked off LAST, by its own memory (the map, the tile it
    left from, the direction): what `game_answer.py --after-connection` is asked about."""
    crossed = [t for t in transitions(run) if t[3] == "connection" and t[4] == "ai" and t[5] is not None]
    if not crossed:
        return None
    group, number = (int(v) for v in str(crossed[-1][1]).split(":"))
    return [group, number], [int(v) for v in crossed[-1][5]], str(crossed[-1][7])


def game_answer(state: Path, truth: dict, after_warp: tuple[list[int], list[int]] | None = None,
                after_connection: tuple[list[int], list[int], str] | None = None) -> tuple[dict, dict | None]:
    """`gates/game_answer.py` on the state a run left, for save block 1's claim (map, pos); then, as its FAULT-TEST
    (CLAUDE.md rule 6), the same probe claiming the first neighbouring tile it rules out, which must disagree.
    `after_warp` (map, tile): also ask where the ROM says that warp leaves the player (`--after-warp`); `after_connection`
    (map, tile, direction), the same for a map edge walked off (`--after-connection`)."""

    def ask(xy) -> dict:
        command = [sys.executable, str(GAME_ANSWER), str(state), *(str(v) for v in truth["map"]), *(str(v) for v in xy)]
        if after_warp is not None:
            command += ["--after-warp", *(str(v) for v in after_warp[0]), *(str(v) for v in after_warp[1])]
        elif after_connection is not None:
            command += ["--after-connection", *(str(v) for v in after_connection[0]), *(str(v) for v in after_connection[1]),
                        after_connection[2].capitalize()]
        data, raw = run_json(command, "ANSWER", clean_env({}), 300)
        return data if data is not None else {"error": raw[-1500:]}

    answer = ask(truth["pos"])
    wrong = (answer.get("ruled_out") or [None])[0]
    return answer, (ask(wrong) if wrong is not None else None)


def run_harness_arm(arm: Arm) -> Run:
    """`gates/hands_harness.py` once, from a COPY of the package with the arm's mutations (in-process: the skills' code)."""
    run = Run(arm)
    root = make_copy(arm.mutations)
    run.run_dir = Path(tempfile.mkdtemp(prefix=f"ai_step3_{arm.name}_"))
    run.command = [sys.executable, str(root / "ai_player" / "gates" / HARNESS.name), arm.brain, "--state",
                   str(FIXTURES[arm.fixture][0]), "--seed", str(arm.run_seed), "--frames", str(arm.frames), *arm.args,
                   "--run-dir", str(run.run_dir), "--game-clock", GAME_CLOCK]
    run.started = time.time()
    began = time.monotonic()
    try:
        run.harness, raw = run_json(run.command, "HANDS", clean_env({launcher.ENV_BUILD_ROOT: str(REPO / "sandbox-pokebot")}), arm.wall)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    if run.harness is None:
        run.notes.append(f"the harness printed no HANDS line: {raw[-2000:]}")
    actions = run.run_dir / "actions.jsonl"
    if actions.is_file():
        run.records = [json.loads(line) for line in actions.read_text(encoding="utf-8").splitlines() if line.strip()]
    run.world = last_world(run.run_dir / "world.jsonl")
    run.elapsed = time.monotonic() - began
    run.exit_code = 0 if run.harness is not None else 1
    return run


def run_rom_arm(arm: Arm) -> Run:
    """(build step 3.1) A test-side scan of the ROM in a throwaway emulator (`gates/exit_looks.py`): no AI runs. (The
    step-3.1 verifier's second round) arm WARPREAD: `gates/warp_reads.py`, the real eyes' every read against the warp
    arrays, and its three plants (each from a COPY of the package)."""
    run = Run(arm)
    script, prefix = (WARP_READS, "WARPREADS") if arm.kind == "warp" else (EXIT_LOOKS, "EXITS")
    run.command = [sys.executable, str(script)]
    run.started = time.time()
    began = time.monotonic()
    run.harness, raw = run_json(run.command, prefix, clean_env({}), arm.wall)
    if run.harness is None:
        run.notes.append(f"the scan printed no {prefix} line: {raw[-2000:]}")
    run.elapsed = time.monotonic() - began
    run.exit_code = 0 if run.harness is not None else 1
    return run


def harness_args(arm: Arm) -> list[str]:
    """A launcher arm's own start, seed and options as `hands_harness.py` arguments (arm CLOCKS)."""
    env = arm.env
    out = [arm.brain, "--state", str(FIXTURES[arm.fixture][0]), "--seed", str(arm.run_seed), "--frames", str(arm.frames)]
    for key, flag in ((ENV_GOAL_MAP, "--goal-map"), (ENV_ROAM_STEPS, "--roam-steps"), (ENV_GOTO, "--goto"),
                      (ENV_WORLD, "--world-in"), (ENV_PERSONALITY, "--personality")):
        if env.get(key):
            out += [flag, env[key]]
    if env.get(ENV_FAULT_NO_CROP):
        out.append("--no-crop")
    return out


def run_clock_arm(arm: Arm) -> Run:
    """(the step-3.1 verifier's second round) Arm CLOCKS: every launcher arm, in-process (`hands_harness.py`, this repo),
    with the cartridge's clock pinned at each of `CLOCK_INSTANTS`; its frames and presses at each."""
    from concurrent.futures import ThreadPoolExecutor

    run = Run(arm)
    arms = [a for a in ARMS if a.kind == "launcher"]
    jobs = [(a, when) for a in arms for when in CLOCK_INSTANTS]
    run.command = [sys.executable, str(HARNESS), "<each launcher arm's options>", "--game-clock", "<each instant>"]
    run.started = time.time()
    began = time.monotonic()

    def one(job: tuple[Arm, str]) -> dict:
        target, when = job
        folder = Path(tempfile.mkdtemp(prefix=f"ai_step3_clock_{target.name}_"))
        extra: dict = {}
        try:
            data, raw = run_json([sys.executable, str(HARNESS), *harness_args(target), "--run-dir", str(folder),
                                  "--game-clock", when], "HANDS", clean_env({}), 1200)
            actions = folder / "actions.jsonl"
            if data is not None and target.name in CLOCK_SENSITIVE and actions.is_file():
                # what the clock-sensitive arms' claims rest on, at this instant too
                records = [json.loads(line) for line in actions.read_text(encoding="utf-8").splitlines() if line.strip()]
                truth = data.get("truth") or {}
                if target.name.startswith("SCENEX"):
                    t = twin_scenes(records)
                    extra = {"twin_segments": t["segments"], "map": truth.get("map"),
                             "var": truth.get("VAR_LITTLEROOT_TOWN_STATE")}
                else:
                    metrics = next(((r.get("extra") or {}) for r in records if r.get("decision") == "roam"), {})
                    extra = {"steps": metrics.get("steps"), "spin_ratio": metrics.get("spin_ratio")}
        finally:
            shutil.rmtree(folder, ignore_errors=True)
        if data is None:
            return {"arm": target.name, "when": when, "error": raw[-400:]}
        return {"arm": target.name, "when": when, "frames": data.get("frames"), "presses": data.get("presses"),
                "reason": str(data.get("reason"))[:70], **extra}

    with ThreadPoolExecutor(max_workers=12) as pool:
        rows = list(pool.map(one, jobs))
    run.harness = {"rows": rows, "instants": list(CLOCK_INSTANTS), "pinned": GAME_CLOCK}
    run.elapsed = time.monotonic() - began
    run.exit_code = 0 if all("error" not in r for r in rows) else 1
    return run


def last_world(path: Path) -> dict | None:
    if not path.is_file():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(lines[-1]) if lines else None


# ---------------------------------------------------------------------- shared checks
def check_after_is_this_run(run: Run) -> None:
    """The state graded is the one THIS run wrote (as `live_step2.check_after_is_this_run`, for this driver's fixtures)."""
    after = run.after or {}
    before_md5 = FIXTURES[run.arm.fixture][1]
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    start_frame = (run.before or {}).get("frame") or 0
    frame = after.get("frame")
    written = run.state_mtime is not None and run.state_mtime >= run.started - 1.0
    near = isinstance(frame, int) and frames > 0 and abs(frame - (start_frame + frames)) <= FRAME_SLACK
    run.check(bool(after) and written and near and after.get("state_md5") != before_md5,
              f"the state graded is the one THIS run wrote: written "
              f"{'%.1fs after the run started' % (run.state_mtime - run.started) if run.state_mtime else 'NEVER'}; frame {frame} "
              f"== start {start_frame} + {frames} real frames (+-{FRAME_SLACK}); md5 {after.get('state_md5')} (fixture {before_md5})")


def selftest_after_check() -> list[str]:
    """FAULT-TEST of `check_after_is_this_run` on synthetic runs (CLAUDE.md rule 6): its own state passes; a stale one,
    a frame off by 3000, no file and the fixture's own bytes fail."""
    arm = ARMS[0]
    md5 = FIXTURES[arm.fixture][1]

    def verdict(mtime, frame, state_md5) -> bool:
        run = Run(arm, started=1000.0, state_mtime=mtime, verdict={"counters": {"real_frames": 3344}},
                  before={"frame": 15268}, after=None if frame is None else {"frame": frame, "state_md5": state_md5})
        check_after_is_this_run(run)
        return run.passed

    cases = [("its own state", verdict(1500.0, 18612, "abc"), True),
             ("a stale state (mtime before the start)", verdict(900.0, 18612, "abc"), False),
             ("a frame +3000", verdict(1500.0, 21612, "abc"), False),
             ("no state file", verdict(None, None, "abc"), False),
             ("the fixture's own bytes", verdict(1500.0, 18612, md5), False)]
    return [f"{name}: passed={got}, want {want}" for name, got, want in cases if got != want]


def memory_of(run: Run) -> WorldMemory | None:
    return WorldMemory.from_dict(run.world) if run.world else None


def check_crop(run: Run, expect_inside: bool = True) -> int:
    """THE PERCEPTION RULE on the AI's own memory: every known tile lay inside the window of the tile it was first seen
    from. Returns how many did not."""
    world = memory_of(run)
    if world is None:
        run.check(False, "the AI's memory (world.jsonl) was written")
        return -1
    tiles = [(memory.const or key, xy, fact.seen_from) for key, memory in world.maps.items() for xy, fact in memory.tiles.items()]
    outside = [(name, xy, frm) for name, xy, frm in tiles if not in_window(frm, xy)]
    if expect_inside:
        run.check(bool(tiles) and not outside,
                  f"THE CROP, on the AI's own memory: all {len(tiles)} known tiles of {len(world.maps)} maps lie inside the 15 x 11 "
                  f"window of the tile they were first seen from (outside: {outside[:3] or 'none'})")
    decisions = [r for r in run.records if r.get("decision") == "decide" and (r.get("extra") or {}).get("target") is not None]
    unseen = [(r["frame"], (r["extra"] or {}).get("target"), (r["extra"] or {}).get("seen_from")) for r in decisions
              if not ((r["extra"] or {}).get("known") and in_window(tuple(r["extra"]["seen_from"]), tuple(r["extra"]["target"])))]
    if expect_inside:
        run.check(bool(decisions) and not unseen,
                  f"every one of the {len(decisions)} targets the AI chose was a tile it had SEEN, inside the window it was seen "
                  f"from (not: {unseen[:3] or 'none'})")
    return len(outside)


def check_hands(run: Run, walking: bool = True) -> None:
    """Every press has a gate; every A is a wait, a menu confirm or a talk by its look; every walking hold is pressed on
    a look of the overworld with nothing waiting and no menu, and is CHUNK_FRAMES long (`walking`: the arm walks at
    all; TRN does not); no catch-all idle."""
    presses = run.presses
    no_gate = [p for p in presses if not p.get("reason")]
    run.check(bool(presses) and not no_gate, f"{len(presses)} presses in the action log, every one with its gate (without: {len(no_gate)})")
    kinds: dict[str, int] = {}
    wrong = []
    for press in (p for p in presses if p["action"].startswith("press A ")):
        kind, ok = classify_a(press)
        kinds[kind] = kinds.get(kind, 0) + 1
        if not ok:
            wrong.append((press["frame"], kind, press["reason"][:60], (press.get("digest") or "")[:90]))
    run.check(not wrong, f"EVERY A press is a WAIT, a MENU confirm (the battle's RUN included) or a TALK by its look: "
                         f"{dict(sorted(kinds.items())) or 'none pressed'}; any other: {wrong[:4] or 'none'}")
    walks = [p for p in presses if str(p.get("reason", "")).startswith(WALK_GATES)]
    bad_walk = [(p["frame"], p["reason"][:50], (p.get("digest") or "")[:100]) for p in walks
                if not str(p.get("digest", "")).split()[1:2] == ["overworld"] or "waits=A/B" in (p.get("digest") or "")
                or " ui=" in (p.get("digest") or "")]
    run.check((bool(walks) == walking) and not bad_walk,
              f"{len(walks)} walking holds (want {'some' if walking else 'none'}), each pressed on a look of the OVERWORLD with "
              f"nothing waiting and no menu (any other: {bad_walk[:3] or 'none'})")
    lengths = sorted({(p.get("extra") or {}).get("hold") for p in walks})
    others = [(p.get("extra") or {}).get("hold") for p in presses if p not in walks and p["action"].startswith("press ")]
    run.check(lengths == ([CHUNK_FRAMES] if walking else []) and all(h is not None and 1 <= h <= 7 for h in others),
              f"pace: every walking hold {CHUNK_FRAMES} frames (seen {lengths}), every other press 1-7 frames "
              f"(seen {sorted(set(others))})")
    idle = [r for r in run.records if r.get("decision") == "watch"]
    generic = [(r["frame"], r["reason"]) for r in idle if str(r.get("reason", "")).startswith(GENERIC_BUSY)]
    run.check(not generic, f"{len(idle)} stretches standing still, NONE under the catch-all {GENERIC_BUSY!r}: {generic[:3] or 'none'}; "
                           f"reasons {sorted({re.sub(r'[0-9]+', '#', str(r['reason']))[:50] for r in idle})[:10]}")
    walk_gates: dict[str, int] = {}
    for press in walks:
        key = press["reason"].split(":")[0].split(" (")[0]
        key = re.sub(r"[0-9]+", "#", key)
        walk_gates[key] = walk_gates.get(key, 0) + 1
    run.notes.append(f"walking holds by gate: {json.dumps(dict(sorted(walk_gates.items())), ensure_ascii=False)}")


def transitions(run: Run) -> list[list]:
    return (run.world or {}).get("transitions") or []


def names(run: Run) -> dict[str, str]:
    world = memory_of(run)
    return world.names() if world is not None else {}


def describe_transitions(run: Run) -> str:
    n = names(run)
    return "; ".join(f"{n.get(t[1], t[1])} -> {n.get(t[2], t[2])} {t[3]} by {t[4]} tile {t[5]} arrival {t[6]} {t[7]}"
                     for t in transitions(run)) or "none"


def world_lines(run: Run) -> list[str]:
    return [line for line in run.ai_log.splitlines() if line.startswith("[AI-WORLD]")]


def stats(truth: dict | None, key: str) -> int | None:
    return ((truth or {}).get("game_stats") or {}).get(key)


def map_name_of(record: dict) -> str | None:
    """The map key ("group:number") of a record's look: its digest says "REGION NAME(g,n) xy=..."."""
    match = re.search(r"\((\d+),(\d+)\) xy=", record.get("digest") or "")
    return None if match is None else f"{match.group(1)}:{match.group(2)}"


def walk_steps_on(run: Run, key: str) -> int:
    """How many steps (a "walk ..." gate: the first chunk of a step) the AI pressed on one map, from its action log."""
    return sum(1 for p in run.presses if str(p.get("reason", "")).startswith("walk ") and map_name_of(p) == key)


def describe_trial(trial: dict) -> str:
    p = trial["predicted"]
    want = (f"{p['steps']} step(s), then the map becomes {p['map']}" if p["ends"] == "map"
            else f"{p['steps']} step(s), then a stop at {p.get('at')} ({p.get('why')})")
    got = (f"{trial['game_steps']} step(s) (the game's counter), map {'changed to ' + str(trial['loaded_map']) if trial['map_changed'] else 'unchanged'}")
    return f"hold {trial['direction']}: the ROM predicts {want}; the game: {got} -> {'agrees' if trial['agree'] else 'DISAGREES'}"


def check_game_answer(run: Run) -> None:
    """THE GAME'S ANSWER to where the player stands (`gates/game_answer.py`; the step-3 verifier's weak proof 3: the
    truth's `pos` is the memory the eyes read too): holding a direction from the state the run left, the game's own
    step counter and the map it loads must do what the ROM's layout at save block 1's claimed tile predicts; the same
    probe claiming a neighbouring tile it rules out must DISAGREE (its fault-test)."""
    a, after = run.answer or {}, run.after or {}
    claim = f"{after.get('map')} {after.get('pos')}"
    if not a or "error" in a:
        run.check(False, f"THE GAME'S ANSWER for {claim}: the probe failed: {str(a.get('error'))[-300:]}")
        return
    trials = a.get("trials") or []
    fault = run.answer_fault or {}
    lock = a.get("locked") or {}
    if a.get("inconclusive") or (not a.get("agree") and lock.get("locked")):
        # (the step-3 verifier's second round: an INCONCLUSIVE answer used to pass on the loaded map header alone, so
        # STUCK's end tile had no behavioural confirmation. It no longer passes without one.) (The step-3.1 verifier's
        # second round) also a walking answer the game did not step at all, the player LOCKED by a scene (SCENEX's end:
        # Birch's rescue on Route 101): then THE ARRIVAL across the pre-registered crossing, a warp or a map edge.
        why = "; ".join(f"{d}: {p.get('why')}" for d, p in (a.get("plans") or {}).items())
        if trials:
            why = "the walking trials met a player who does not move: " + " | ".join(describe_trial(t) for t in trials)
        arrival = a.get("arrival") or {}
        held = "; ".join(f"{d}: {h['game_steps']} steps, moved {h['moved']}, map changed {h['map_changed']}"
                         for d, h in (lock.get("held") or {}).items())
        kind, want = ARRIVALS.get(run.arm.name, (None, None))
        if not arrival or kind is None or "error" in arrival:
            run.check(False, f"THE GAME'S ANSWER for {claim}: {'INCONCLUSIVE' if a.get('inconclusive') else 'LOCKED'} ({why}) "
                             f"and no arrival answer ({arrival.get('error') if arrival else 'none asked for'}; pre-registered: "
                             f"{kind}): the end tile has NO behavioural confirmation")
            return
        changes = transitions(run)
        last = changes[-1] if changes else None
        after_it = [(p["frame"], p["reason"][:50]) for p in run.presses if last is not None and p["frame"] >= last[0]]
        if kind == "warp":
            crossing = [arrival.get("warp", {}).get("map"), arrival.get("warp", {}).get("tile")]
            pre = list(want)
            step_ok = arrival.get("raw_landing_is_the_claim") is False
            step_text = (f"the exit step {arrival.get('exit_step')} leaves the player on {arrival.get('tile')} (build step 3.1, "
                         f"item 7: graded against save block 1's position after the transition; the RAW landing "
                         f"{arrival.get('landing')} is that position: {arrival.get('raw_landing_is_the_claim')}, want False: a "
                         f"door-family landing leaves the player one tile on)")
        else:
            c = arrival.get("connection") or {}
            crossing = [c.get("map"), c.get("tile"), str(c.get("direction", "")).lower()]
            pre = [want[0], want[1], want[2]]
            step_ok = arrival.get("exit_step") == [0, 0]
            step_text = f"across the ROM's {c.get('direction')} connection (offset {c.get('offset')}; a connection has no exit step)"
        run.check(bool(a.get("agree_by_arrival")) and crossing == pre and last is not None and not after_it
                  and fault.get("agree_by_arrival") is False and fault.get("agree") is not True and step_ok,
                  f"THE GAME'S ANSWER for save block 1's claim {claim} ({why}): (1) LOCKED: each direction held "
                  f"{lock.get('held_frames')} frames from the state left moves nothing and counts no step ({held}) -> locked "
                  f"{lock.get('locked')}: the player cannot have moved since; (2) THE ARRIVAL by the ROM: the {kind} the AI "
                  f"crossed last {crossing} (pre-registered {pre}) lands on {arrival.get('map')} {arrival.get('landing')} "
                  f"({arrival.get('landing_behaviour')}), and {step_text} -> agrees {arrival.get('agrees')}; the loaded map "
                  f"(gMapHeader) is the claimed map's: {a.get('loaded_header_is_claimed_map')}; (3) the AI pressed NOTHING from "
                  f"that arrival (f{last[0] if last else '?'}) on: {after_it or 'none'}; FAULT-TEST: the probe claiming "
                  f"{(a.get('ruled_out') or [None])[0]} instead -> by the arrival {fault.get('agree_by_arrival')}, by walking "
                  f"{fault.get('agree')} (want False, not True)")
        return
    standable = 8 - len(a.get("neighbours_that_are_walls") or [])
    wrong = (a.get("ruled_out") or [None])[0]
    run.check(bool(a.get("agree")) and fault.get("agree") is False,
              f"THE GAME'S ANSWER to save block 1's claim {claim}, by its behaviour from the state left (gates/game_answer.py): "
              f"{' | '.join(describe_trial(t) for t in trials)}; the map the game LOADED (gMapHeader) is the claimed map's ROM "
              f"header: {a.get('loaded_header_is_claimed_map')}; the trials rule out {len(a.get('ruled_out') or [])} of the "
              f"{standable} neighbouring tiles the player could stand on {a.get('ruled_out')}; FAULT-TEST: the probe claiming "
              f"{wrong} instead: {' | '.join(describe_trial(t) for t in fault.get('trials') or []) or fault} -> agree="
              f"{fault.get('agree')} (want False)")


# ---------------------------------------------------------------------- graders
def grade_common(run: Run, want_prefix: str, walking: bool = True) -> None:
    check_purity(run, None)
    run.check(run.outcome.startswith(want_prefix), f"the brain's outcome: {run.outcome[:200]!r} (want it to begin {want_prefix!r})")
    check_after_is_this_run(run)
    check_hands(run, walking)
    if run.arm.name not in NO_ANSWER:
        check_game_answer(run)
    run.notes.append("the AI's [AI-WORLD] lines:\n    " + "\n    ".join(line[:300] for line in world_lines(run)))
    run.notes.append(f"map changes (from the memory): {describe_transitions(run)}")


def reversal_bound(name: str, seed: int) -> int:
    """The reversals a walking arm (or the arm a replication replays) may show at `seed`: at seed 3 the pre-registered
    count of its trajectory (`REVERSALS_SEED3`), at any other seed the sweep's per-run bound."""
    return REVERSALS_SEED3.get(name, 0) if seed == 3 else REVERSALS_PER_RUN


def stale_arrivals(run: Run) -> tuple[int, list[dict]]:
    """(the step-3.1 verifier's round, finding 2) The frontier targets the AI WALKED ONTO and kept: its next decision was
    made standing on the target (the action log's `decide` records: `player`), with no "not worth going to any more"
    record for it between (a target dropped as stale on the move, the fix, is not one). For each, whether everything
    beside it had been seen by then, by the memory's OWN first-seen frames (`seen_frame` of its four neighbours in
    world.jsonl, the same memory the eyes filled, read after the run). Returns (frontier targets chosen, the arrivals)."""
    world = memory_of(run)
    decides = [r for r in run.records if r.get("decision") == "decide" and (r.get("extra") or {}).get("target") is not None]
    dropped = [((r.get("extra") or {}).get("map"), tuple((r.get("extra") or {}).get("stale") or ()), r.get("frame"))
               for r in run.records if r.get("decision") == "world" and "is not worth going to any more" in str(r.get("reason"))]
    chosen, out = 0, []
    for i, record in enumerate(decides):
        extra = record["extra"]
        if extra.get("kind") != "frontier":
            continue
        chosen += 1
        after = decides[i + 1] if i + 1 < len(decides) else None
        if after is None or after["extra"].get("map") != extra.get("map") or after["extra"].get("player") != extra.get("target"):
            continue
        tile = tuple(extra["target"])
        if any(key == extra.get("map") and xy == tile and record["frame"] <= frame <= after["frame"] for key, xy, frame in dropped):
            continue
        memory = world.maps.get(extra.get("map")) if world is not None else None
        beside = [(tile[0] + dx, tile[1] + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))]
        seen = memory is not None and all(xy in memory.tiles and memory.tiles[xy].seen_frame <= after["frame"] for xy in beside)
        out.append({"map": extra.get("map"), "target": list(tile), "chosen": record["frame"], "arrived": after["frame"],
                    "everything_beside_it_seen": seen})
    return chosen, out


def check_reversals(run: Run) -> None:
    """(build step 3.1, the step-3 review's finding 2) REVERSALS (A -> B -> A, or a U-turn's third step) on the player's
    path as the LOOKS showed it (`walk_path`, the action log's digests), at most the arm's pre-registered number; and
    every target dropped as stale on the way is named. (The step-3.1 verifier's round) the bound at seed 3 is that
    trajectory's own count (`reversal_bound`), which the revert arms break; and no frontier target was WALKED ONTO with
    everything beside it already seen (`stale_arrivals`: the stale target the review found, by the memory's own frames),
    with targets dropped as stale on the way (the rule acted: not vacuous)."""
    steps, found = path_reversals(run)
    stale = [r for r in run.records if r.get("decision") == "world" and "is not worth going to any more" in str(r.get("reason"))]
    limit = reversal_bound(run.arm.base or run.arm.name, run.arm.run_seed)
    run.check(steps > 0 and len(found) <= limit,
              f"REVERSALS (finding 2): {len(found)} on the {steps} steps the looks showed (want <= {limit}, pre-registered for "
              f"seed {run.arm.run_seed}): {[(r['map'], r['kind'], r['tiles']) for r in found] or 'none'}; targets dropped as "
              f"stale on the way: {len(stale)} {[str(r.get('reason'))[:70] for r in stale[:4]]}")
    chosen, arrived = stale_arrivals(run)
    walked = [a for a in arrived if a["everything_beside_it_seen"]]
    run.check(chosen > 0 and stale and not walked,
              f"NO STALE TARGET WALKED ONTO (finding 2): of the {chosen} frontier targets chosen, {len(arrived)} were walked onto "
              f"and kept, {len(walked)} of them with everything beside them already seen by the memory's own first-seen frames "
              f"(want 0: {walked[:3] or 'none'}); {len(stale)} targets dropped as stale on the way (want > 0: the rule acted)")
    run.measure("steps", steps)
    run.measure("reversals", len(found))
    run.measure("stale_walked", len(walked))
    run.measure("stale_dropped", len(stale))


def grade_HOUSE(run: Run) -> None:
    grade_common(run, "explore: done: explore to LITTLEROOT_TOWN")
    check_reversals(run)
    before, after = run.before or {}, run.after or {}
    run.check(before.get("map") == HOUSE_2F and before.get("VAR_LITTLEROOT_INTRO_STATE") == 6,
              f"NON-VACUITY (the fixture): map {before.get('map')} (the player's 2F {HOUSE_2F}), VAR_LITTLEROOT_INTRO_STATE "
              f"{before.get('VAR_LITTLEROOT_INTRO_STATE')} (6: the clock set, the TV scene still to come)")
    run.check(after.get("map") == LITTLEROOT and after.get("VAR_LITTLEROOT_INTRO_STATE") == 7,
              f"TRUTH after (save block 1): map {after.get('map')} == LITTLEROOT_TOWN {LITTLEROOT} at {after.get('pos')}; "
              f"VAR_LITTLEROOT_INTRO_STATE {after.get('VAR_LITTLEROOT_INTRO_STATE')} == 7 (the TV scene was played through)")
    moves = [t for t in transitions(run)]
    n = names(run)
    chain = [(n.get(t[1]), n.get(t[2]), t[3], t[4]) for t in moves]
    # (since the whim among equals, a seed may look round 1F, or go back up, before it leaves: the first and the last
    # map change are the claim, and every change between is the AI's own warp)
    run.check(len(chain) >= 2 and chain[0] == ("LITTLEROOT_TOWN_BRENDANS_HOUSE_2F", "LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", "warp", "ai")
              and chain[-1] == ("LITTLEROOT_TOWN_BRENDANS_HOUSE_1F", "LITTLEROOT_TOWN", "warp", "ai")
              and all(c[2:] == ("warp", "ai") for c in chain),
              f"the AI's own memory: down the stairs and out the door, each a WARP it used itself: {chain}")
    a = [p for p in run.presses if p["action"].startswith("press A ")]
    run.check(len(a) >= 3, f"the TV scene read through: {len(a)} A presses, each on a wait (above)")
    check_crop(run)
    s0, s1 = stats(before, "steps"), stats(after, "steps")
    run.notes.append(f"the game's own step counter: {s0} -> {s1}")


def grade_TOWN(run: Run) -> None:
    grade_common(run, "explore: done: explore to ROUTE101")
    before, after = run.before or {}, run.after or {}
    run.check(before.get("map") == LAB and after.get("map") == ROUTE101,
              f"TRUTH (save block 1): map {before.get('map')} (Birch's lab {LAB}) -> {after.get('map')} (ROUTE101 {ROUTE101}) at "
              f"{after.get('pos')}")
    b0, b1 = (before.get("flags") or {}).get("SYS_B_DASH"), (after.get("flags") or {}).get("SYS_B_DASH")
    run.check(b0 is False and b1 is True, f"TRUTH: SYS_B_DASH {b0} -> {b1}: Mom's Running Shoes scene was played through on the way")
    n = names(run)
    chain = [(n.get(t[1]), n.get(t[2]), t[3], t[4], t[7]) for t in transitions(run)]
    # (since the whim among equals a seed may look into a house on the way: the first and the last map change are the
    # claim; a change between is a warp into or out of a building, the AI's or a scene's)
    run.check(len(chain) >= 2 and chain[0][:4] == ("LITTLEROOT_TOWN_PROFESSOR_BIRCHS_LAB", "LITTLEROOT_TOWN", "warp", "ai")
              and chain[-1] == ("LITTLEROOT_TOWN", "ROUTE101", "connection", "ai", "up")
              and all(c[2] == "warp" for c in chain[1:-1]),
              f"the AI's own memory: out of the lab by a WARP, then off the north edge: a CONNECTION going up: {chain}")
    world = memory_of(run)
    connection = next((c for c in (world.connections if world is not None else []) if n.get(c.get("target")) == "ROUTE101"), {})
    run.check(bool(connection) and connection.get("offset") is not None and connection["arrival"][1] == 19,
              f"the connection learned with its offset: {connection}")
    check_crop(run)
    s0, s1 = stats(before, "steps"), stats(after, "steps")
    ai_steps = walk_steps_on(run, "0:9") + walk_steps_on(run, "1:4") + walk_steps_on(run, "0:16")
    run.check(isinstance(s0, int) and isinstance(s1, int) and s1 - s0 >= ai_steps > 0,
              f"the game's OWN step counter (gameStats[GAME_STAT_STEPS]): {s0} -> {s1} (+{(s1 or 0) - (s0 or 0)}) >= the AI's "
              f"walking steps {ai_steps} (a scene's movements count too)")
    run.notes.append(f"TOWN: {walk_steps_on(run, '0:9')} walking steps on LITTLEROOT_TOWN; decisions "
                     f"{sum(1 for r in run.records if r.get('decision') == 'decide')}")
    check_reversals(run)
    check_no_road_before_a_crossing(run)


_MAP_SIZES: dict[str, list[int]] = {}


def rom_map_sizes(keys: list[str]) -> dict[str, list[int]]:
    """TEST SIDE (the step-3.1 verifier's round): each map's (width, height) by the ROM's own layout (the framework's
    `get_map_data(...).map_size`, in a throwaway emulator), for maps "group:number"; cached for the driver's run."""
    wanted = sorted({key for key in keys if key and key not in _MAP_SIZES})
    if wanted:
        state = FIXTURES["pokedex_done.ss1"][0]
        code = ("import json,sys;from pathlib import Path;sys.path.insert(0,r'%s');from ai_player.gates.probe_eyes import boot;"
                "c=boot('ai-step0-fixture');c.emulator.load_save_state(Path(r'%s').read_bytes());c.emulator.run_single_frame();"
                "from modules.map import get_map_data;"
                "print('ROM '+json.dumps({k:list(get_map_data(tuple(int(v) for v in k.split(':')),(0,0)).map_size) for k in %r}))"
                % (REPO, state, wanted))
        data, raw = run_json([sys.executable, "-c", code], "ROM", clean_env({}), 300)
        _MAP_SIZES.update(data or {})
    return {key: _MAP_SIZES[key] for key in keys if key in _MAP_SIZES}


def past_real_edge(tile: tuple[int, int], size: list[int]) -> str | None:
    """Which edge of the map (by the ROM's size, test side) `tile` lies past, or None: inside."""
    x, y = tile
    width, height = size
    return "up" if y < 0 else "down" if y >= height else "left" if x < 0 else "right" if x >= width else None


def edge_crossings(run: Run) -> dict[tuple[str, str], int]:
    """(map key, side) -> the frame of the first crossing of that edge the AI SAW (its memory's connections, a loaded
    memory's included): a connection crossed going D leaves its source by side D and enters its target by the opposite."""
    opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
    out: dict[tuple[str, str], int] = {}
    for c in (run.world or {}).get("connections") or []:
        direction, frame = c.get("direction"), int(c.get("frame") or 0)
        if direction not in opposite:
            continue
        for key in ((c.get("source"), direction), (c.get("target"), opposite[direction])):
            out[key] = min(out.get(key, 10**12), frame)
    return out


def edge_targets(run: Run) -> tuple[list[dict], dict]:
    """Every target the AI chose PAST a map's real edge (the ROM's size, test side) BEFORE it had seen a crossing of that
    edge, with its kind and reason; and the crossings (`edge_crossings`)."""
    crossings = edge_crossings(run)
    decides = [r for r in run.records if r.get("decision") == "decide" and (r.get("extra") or {}).get("target") is not None]
    sizes = rom_map_sizes(sorted({(r["extra"] or {}).get("map") for r in decides if (r["extra"] or {}).get("map")}))
    out = []
    for r in decides:
        extra = r["extra"]
        size = sizes.get(extra.get("map"))
        side = past_real_edge(tuple(extra["target"]), size) if size else None
        if side is not None and r["frame"] < crossings.get((extra.get("map"), side), 10**12):
            out.append({"frame": r["frame"], "map": extra.get("map"), "kind": extra.get("kind"), "target": extra["target"],
                        "side": side, "reason": str(r.get("reason"))[:60]})
    return out, crossings


def road_claims(targets: list[dict]) -> list[dict]:
    """The targets among `targets` that claim to know a map ENDS there: a road, or a road that leads back or toward the
    goal ("the road ...": `brain/explore.py` roads)."""
    return [t for t in targets if t["kind"] == "road" or t["reason"].startswith("the road ")]


def check_no_road_before_a_crossing(run: Run) -> None:
    """(build step 3.1, the step-3 review's finding 1) No target was a ROAD past a map's edge before the AI had SEEN a
    crossing of THAT edge: the explorer no longer knows where a map ends from its coordinates. (The step-3.1 verifier's
    round: "the live check never fires", roads chosen: none.) It now also says the case finding 1 is about WAS met: at
    least one target was chosen past the map's real edge (the ROM's size, test side) before a crossing of that edge was
    seen, and every such target was chosen as what it LOOKS like (frontier, a door, grass), none as a road. Its fault is
    the revert arm EDGER (the old coordinates rule: the same targets become roads, and this check fails there)."""
    past, crossings = edge_targets(run)
    early = road_claims(past)
    run.check(bool(past) and not early,
              f"NO ROAD BEFORE A CROSSING (finding 1): {len(past)} targets chosen past a map's real edge (the ROM's size) before "
              f"a crossing of that edge was SEEN (want >= 1: the case finding 1 is about), by kind "
              f"{sorted({t['kind'] for t in past})} (want no road): {[(t['map'], t['kind'], t['target'], t['side']) for t in past[:4]]}; "
              f"roads among them: {early[:3] or 'none'}; first crossings seen by (map, edge): "
              f"{ {f'{k[0]} {k[1]}': v for k, v in sorted(crossings.items())} }")


def grade_ROUTE(run: Run) -> None:
    grade_common(run, "explore: done: explore to OLDALE_TOWN")
    before, after = run.before or {}, run.after or {}
    run.check(before.get("map") == ROUTE101 and after.get("map") == OLDALE,
              f"TRUTH (save block 1): map {before.get('map')} (ROUTE101) -> {after.get('map')} (OLDALE_TOWN {OLDALE}) at {after.get('pos')}")
    first = next((line for line in world_lines(run) if "memory from" in line), "")
    run.check("route101_south.world.jsonl" in first and ": 3 maps (" in first,
              f"the memory of the TOWN walk was LOADED (knowledge grows over a playthrough): {first[:200]}")
    n = names(run)
    chain = [(n.get(t[1]), n.get(t[2]), t[3], t[4], t[7]) for t in transitions(run)]
    run.check(chain and chain[-1] == ("ROUTE101", "OLDALE_TOWN", "connection", "ai", "up"),
              f"the last map change: Route 101's north edge, a CONNECTION going up: {chain}")
    south = [r for r in run.records if r.get("decision") == "decide" and (r.get("extra") or {}).get("kind") in ("road",)
             and (r.get("extra") or {}).get("target", [0, 0])[1] >= 20 and (r.get("extra") or {}).get("map") == "0:16"]
    run.check(not south, f"the road back south (to Littleroot, known from the loaded memory) was never chosen as a new road: {south[:2] or 'none'}")
    w0, w1 = stats(before, "wild_battles"), stats(after, "wild_battles")
    fled = sum(1 for line in world_lines(run) if line.startswith("[AI-WORLD] battle: fled"))
    met = sum(1 for line in world_lines(run) if line.startswith("[AI-WORLD] battle:"))
    run.check(isinstance(w0, int) and isinstance(w1, int) and w1 - w0 == met == fled,
              f"every wild battle met was FLED: the game's own wild-battle count {w0} -> {w1} (+{(w1 or 0) - (w0 or 0)}) == the "
              f"battles the AI met {met} == fled {fled}")
    p0, p1 = before.get("party"), after.get("party")
    run.check(bool(p0) and [m[0] for m in p0] == [m[0] for m in p1 or []] and all(m[1] > 0 for m in p1 or []),
              f"the party (get_party): {p0} -> {p1}: nobody fainted")
    check_crop(run)
    check_reversals(run)
    check_no_road_before_a_crossing(run)


def roam_record(run: Run) -> dict:
    return next(((r.get("extra") or {}) for r in run.records if r.get("decision") == "roam"), {})


def xy_of(record: dict) -> tuple[int, int] | None:
    """The player's tile in a record's look (its digest says "... xy=(x,y) ...")."""
    match = re.search(r"xy=\((-?\d+),(-?\d+)\)", record.get("digest") or "")
    return None if match is None else (int(match.group(1)), int(match.group(2)))


def roam_rederived(run: Run) -> dict:
    """The roaming metrics RE-DERIVED from the action log alone, not from the skill's own bookkeeping (the step-3
    verifier recomputed them from the looks' digests): the tile on the look before each training step's press (`roam
    ...`, the first chunk of a step), and the tile on the look of the metrics record after the last. A press after
    which the tile changed MOVED the player; one after which it did not is INTERRUPTED if a battle was met before the
    next press (the encounter is rolled at the end of the step before: it pre-empts this one), else it walked in place
    (a spin). Spins = those + the reversals (A -> B -> A) of the derived path. Also the walk to the grass before the
    first training step: the moves of its "walk ..." presses."""
    presses = [p for p in run.presses if str(p.get("reason", "")).startswith("roam ")]
    metrics_record = next((r for r in run.records if r.get("decision") == "roam"), {})
    seq = [xy_of(p) for p in presses] + [xy_of(metrics_record)]
    frames = [p["frame"] for p in presses] + [metrics_record.get("frame") or 10**12]
    battles = [r["frame"] for r in run.records if r.get("decision") == "world" and str(r.get("reason", "")).startswith("battle:")]
    path, interrupted, in_place = ([seq[0]] if seq and seq[0] is not None else []), 0, 0
    preempted: list[dict] = []
    for i in range(len(presses)):
        if seq[i + 1] != seq[i]:
            path.append(seq[i + 1])
        elif any(frames[i] <= f <= frames[i + 1] for f in battles):
            interrupted += 1
            preempted.append(preemption(run, presses[i]))
        else:
            in_place += 1
    reversals = sum(1 for k in range(2, len(path)) if path[k] == path[k - 2])
    first = presses[0]["frame"] if presses else 0
    walks = [p for p in run.presses if str(p.get("reason", "")).startswith("walk ") and p["frame"] < first]
    walk_seq = [xy_of(p) for p in walks] + ([seq[0]] if seq else [])
    walk_moves = sum(1 for a, b in zip(walk_seq, walk_seq[1:]) if a != b)
    return {"presses": len(presses), "steps": len(path) - 1, "path": path, "interrupted": interrupted, "in_place": in_place,
            "reversals": reversals, "spins": reversals + in_place, "walk_presses": len(walks), "walk_moves": walk_moves,
            "distinct": len(set(path)), "battles_logged": len(battles), "preempted": preempted}


def reversals(path: list) -> list[dict]:
    """(build step 3.1, the step-3 review's finding 2) Every REVERSAL within a short window in a walk: `path` is
    [(map, (x, y))] after every step, in order. A reversal is a step back onto the tile of two steps before ("back":
    A -> B -> A, the ROUTE arm's (17,9) -> (18,9) -> (17,9)) or the third step of a U-TURN, three steps that end beside
    the tile they began on ("u-turn": A -> B -> C -> D with D next to A, the TOWN arm's (11,7) -> (12,7) -> (12,6) ->
    (11,6): one step's worth of ground for three). Steps across a map change or a jump are not compared. Pure."""
    out = []
    for i in range(2, len(path)):
        if not path[i][0] == path[i - 1][0] == path[i - 2][0]:
            continue
        a, b, c = path[i - 2][1], path[i - 1][1], path[i][1]
        if c == a:
            out.append({"at": i, "kind": "back", "tiles": [list(a), list(b), list(c)]})
            continue
        if i >= 3 and path[i - 3][0] == path[i][0]:
            start = path[i - 3][1]
            if abs(c[0] - start[0]) + abs(c[1] - start[1]) == 1 and len({start, a, b, c}) == 4:
                out.append({"at": i, "kind": "u-turn", "tiles": [list(start), list(a), list(b), list(c)]})
    return out


WALK_GATE = re.compile(r"walk (\w+): \((-?\d+), (-?\d+)\) -> \((-?\d+), (-?\d+)\)")


def walk_path(run: Run) -> list[list]:
    """The AI's OWN steps, in order, as the LOOKS confirmed them: every walking press that begins a step (its gate "walk
    D: (x, y) -> (x2, y2)") whose destination a look showed the player on before the next such press (that press's own
    look included), as (map key, (x, y)). A step that does not begin where the last one ended (a scene or a warp moved
    the player between: the twin's push, Mom walking the player to the TV) starts a new stretch, so `reversals` never
    counts what a script did."""
    walks = [i for i, r in enumerate(run.records)
             if str(r.get("reason", "")).startswith("walk ") and str(r.get("action", "")).startswith("hold ")]
    stretches: list[list] = []
    current: list = []
    for n, i in enumerate(walks):
        record = run.records[i]
        match, key = WALK_GATE.match(str(record.get("reason"))), map_name_of(record)
        if match is None or key is None:
            continue
        frm = (int(match.group(2)), int(match.group(3)))
        to = (int(match.group(4)), int(match.group(5)))
        end = walks[n + 1] if n + 1 < len(walks) else len(run.records) - 1
        if not any(map_name_of(r) == key and xy_of(r) == to for r in run.records[i + 1:end + 1]):
            continue  # the step did not happen (a bump, a person, a battle first)
        if current and current[-1] != (key, frm):
            stretches.append(current)
            current = []
        if not current:
            current = [(key, frm)]
        current.append((key, to))
    stretches.append(current)
    return [stretch for stretch in stretches if stretch]


def path_reversals(run: Run) -> tuple[int, list[dict]]:
    """(steps along the looks' path, every reversal in it) over every stretch of `walk_path`."""
    steps, found = 0, []
    for stretch in walk_path(run):
        steps += max(0, len(stretch) - 1)
        found += [{**r, "map": stretch[r["at"]][0]} for r in reversals(stretch)]
    return steps, found


def facing_of(record: dict) -> str | None:
    match = re.search(r"facing=(\w+)", record.get("digest") or "")
    return None if match is None else match.group(1)


def preemption(run: Run, press: dict) -> dict:
    """(the step-3 verifier's second round: "the ROAM spin ratio does not count the presses a battle pre-empted as
    spins ... a choice of definition") What one training press that did not move the player looked like, from the
    action log alone: the first record after it whose look is IN A BATTLE, how many pad frames after the press that
    was (`pad_frame`: the pad's own count), whether any look between showed the player on another tile or FACING
    another way (a press the game took would at least have turned the player toward a direction it did not face),
    and the direction pressed against the one faced."""
    index = run.records.index(press)
    battle = next((r for r in run.records[index + 1:] if (r.get("digest") or "").split()[1:2] == ["battle"]), None)
    between = run.records[index + 1:run.records.index(battle)] if battle is not None else []
    pressed = str(press.get("action", "")).split()[1].lower() if str(press.get("action", "")).startswith("hold ") else None
    start = (press.get("extra") or {}).get("pad_frame")
    seen = (battle.get("extra") or {}).get("pad_frame") if battle is not None else None
    return {"frame": press["frame"], "tile": xy_of(press), "pressed": pressed, "facing": facing_of(press),
            "battle_frame": battle["frame"] if battle is not None else None,
            "battle_after_pad_frames": None if seen is None or start is None else seen - start,
            "moved_before_the_battle": any(xy_of(r) not in (None, xy_of(press)) for r in between + ([battle] if battle else [])),
            "turned_before_the_battle": any(facing_of(r) not in (None, facing_of(press)) for r in between + ([battle] if battle else []))}


def grade_ROAM(run: Run) -> None:
    grade_common(run, "roam: roamed:")
    before, after = run.before or {}, run.after or {}
    metrics = roam_record(run)
    steps, attempts, spins = metrics.get("steps"), metrics.get("attempts"), metrics.get("spins")
    ratio = spins / steps if steps else None
    derived = roam_rederived(run)
    run.check(steps == 150 and ratio is not None and ratio < 0.02,
              f"ROAMING: {steps} training steps (want 150), spin ratio {spins}/{steps} = {ratio} over the TRAINING STEPS (the "
              f"stricter denominator; want < 0.02: back and forth on the same 1-2 tiles, or walking in place); over every "
              f"press {spins}/{attempts} = {metrics.get('spin_ratio_of_attempts')}")
    run.check(attempts == derived["presses"] and metrics.get("interrupted") == derived["interrupted"],
              f"ATTEMPTS == every training step PRESSED (the verifier: 150 'tried' for 163 roam presses): the AI's attempts "
              f"{attempts} == the `roam ...` presses in the action log {derived['presses']}; of them interrupted by a battle "
              f"{metrics.get('interrupted')} == re-derived {derived['interrupted']} (a battle logged between the press and the next)")
    run.check(steps == derived["steps"] and spins == derived["spins"] and [list(xy) for xy in derived["path"]] == metrics.get("path"),
              f"RE-DERIVED from the looks' digests alone (not the skill's bookkeeping): {derived['steps']} steps that moved the "
              f"player, {derived['reversals']} reversals + {derived['in_place']} in place = {derived['spins']} spins, "
              f"{derived['distinct']} distinct tiles; the path from the digests == the AI's path: "
              f"{[list(xy) for xy in derived['path']] == metrics.get('path')}")
    # (the step-3 verifier's second round) the presses that did NOT move the player, by what the game did with them. The
    # design's spin (draft §4: "walking in place is never a training action"; §7 criterion 9: "spin ratio under 2% of
    # training steps"; HUMAN-PLAY-DESIGN pillar 3) is a press that walks in place or back and forth. A press is
    # PRE-EMPTED, not spun, only when the evidence says the game never acted on it: the battle (rolled at the END of
    # the step before, on the tile just stepped onto) is on screen within the press's own two chunks (2 x
    # CHUNK_FRAMES pad frames: the press was still being held when the battle took the screen), the player stood on
    # the same tile AND faced the same way until the battle (a press the game took turns the player at once, or moves
    # it 8 frames in: measured 2026-10-08), and each battle accounts for ONE press. Anything else is counted as a spin
    # (`in_place`, asserted 0 here).
    pre = derived["preempted"]
    late = [p for p in pre if p["battle_after_pad_frames"] is None or p["battle_after_pad_frames"] > 2 * CHUNK_FRAMES]
    acted = [p for p in pre if p["moved_before_the_battle"] or p["turned_before_the_battle"]]
    battles_matched = {p["battle_frame"] for p in pre}
    other_way = sum(1 for p in pre if p["pressed"] != p["facing"])
    delays = sorted({p["battle_after_pad_frames"] for p in pre})
    run.check(derived["in_place"] == 0 and not late and not acted and len(battles_matched) == len(pre) == derived["interrupted"]
              and len(pre) <= (metrics.get("encounters") or 0),
              f"every press that did not move the player was PRE-EMPTED by a battle, not spun: {len(pre)} such presses, the "
              f"battle on screen {delays} pad frames after each (want <= {2 * CHUNK_FRAMES}: within the press's own two chunks; "
              f"late: {late[:2] or 'none'}); the player on the same tile and FACING the same way until the battle in every one "
              f"(else: {acted[:2] or 'none'}), {other_way} of them pressed AWAY from the way it faced (a press the game took "
              f"would have turned it); {len(battles_matched)} distinct battles for {len(pre)} presses (one each), of the "
              f"{metrics.get('encounters')} met; presses that left the player standing with NO battle: {derived['in_place']}")
    # (build step 3.1, the step-3 review's finding 9) BOTH ratios, from the AI's report AND re-derived from the looks:
    # the back-and-forth spin ratio (the criterion above) and the strict non-moving-press ratio (reported), whose
    # difference is exactly the pre-empted presses the check above explains
    strict = metrics.get("strict_ratio")
    derived_strict = (derived["in_place"] + derived["interrupted"]) / derived["presses"] if derived["presses"] else None
    run.check(metrics.get("reversals") == derived["reversals"] and metrics.get("in_place") == derived["in_place"]
              and metrics.get("preempted") == derived["interrupted"] == len(pre)
              and metrics.get("non_moving") == derived["in_place"] + derived["interrupted"]
              and isinstance(strict, float) and derived_strict is not None and abs(strict - derived_strict) < 1e-6,
              f"BOTH RATIOS (finding 9), the AI's report == re-derived from the looks: BACK-AND-FORTH spin ratio "
              f"{metrics.get('spin_ratio')} = ({metrics.get('reversals')} reversals + {metrics.get('in_place')} in place) / "
              f"{steps} training steps (the criterion, < 2%); STRICT non-moving-press ratio {strict} = "
              f"({metrics.get('in_place')} in place + {metrics.get('preempted')} pre-empted by a battle) / {attempts} presses "
              f"(reported, NOT a criterion: each pre-empted press is the check above's, a battle rolled at the end of the step "
              f"before took the screen while it was held); re-derived: {derived['reversals']} + {derived['in_place']} and "
              f"{derived['in_place']} + {derived['interrupted']} over {derived['presses']} = {derived_strict}")
    run.check((metrics.get("distinct") or 0) >= 40, f"distinct tiles covered: {metrics.get('distinct')} (want >= 40); the "
                                                    f"most-visited tile {metrics.get('most_visited')} times")
    s0, s1 = stats(before, "steps"), stats(after, "steps")
    # the run stops 8 frames into its last step (when the eyes see the tile change) and the game counts a step at its
    # END: `gates/game_answer.py` lets the saved state run on with no input and reports the step(s) still in flight
    flight = (run.answer or {}).get("steps_in_flight")
    run.check(isinstance(s0, int) and isinstance(s1, int) and isinstance(flight, int)
              and s1 + flight - s0 == derived["walk_moves"] + (steps or 0),
              f"the game's OWN step counter: {s0} -> {s1} (+{(s1 or 0) - (s0 or 0)}), + {flight} step in flight when the state "
              f"was saved (counted by the game once it ends) == the walk to the grass {derived['walk_moves']} (of "
              f"{derived['walk_presses']} walk presses) + the {steps} training steps")
    w0, w1 = stats(before, "wild_battles"), stats(after, "wild_battles")
    run.check(isinstance(w0, int) and isinstance(w1, int) and w1 - w0 == metrics.get("encounters") == metrics.get("fled")
              and (metrics.get("encounters") or 0) >= 1,
              f"encounters: the game's OWN wild-battle count {w0} -> {w1} (+{(w1 or 0) - (w0 or 0)}) == the AI's encounters "
              f"{metrics.get('encounters')} == fled {metrics.get('fled')}, and >= 1")
    path = [tuple(xy) for xy in metrics.get("path") or []]
    run.check(after.get("map") == ROUTE101 and path and list(path[-1]) == after.get("pos"),
              f"TRUTH: still on ROUTE101 ({after.get('map')}), the end tile by save block 1 {after.get('pos')} == the AI's last path "
              f"tile {list(path[-1]) if path else None}")
    check_crop(run)


def grade_CROP(run: Run, town: Run | None) -> None:
    grade_common(run, "explore: done: explore to ROUTE101")
    before, after = run.before or {}, run.after or {}
    # (the step-3 verifier's second round: CROP's success rested on the navigator's own outcome string; the game's
    # answer confirmed save block 1's claim but nothing compared that claim with ROUTE101)
    run.check(before.get("map") == LAB and after.get("map") == ROUTE101,
              f"TRUTH (save block 1): map {before.get('map')} (Birch's lab {LAB}) -> {after.get('map')} (ROUTE101 {ROUTE101}) at "
              f"{after.get('pos')}: the faulted run did reach the goal")
    outside = check_crop(run, expect_inside=False)
    world = memory_of(run)
    total = sum(len(m.tiles) for m in world.maps.values()) if world else 0
    run.check(outside > 100, f"the FAULT's harm to the perception rule, in the memory: {outside} of {total} known tiles lie OUTSIDE the "
                             f"window of the tile they were first seen from (the real arms: 0)")
    decisions = [(r.get("extra") or {}) for r in run.records if r.get("decision") == "decide"]
    first_town = next((d for d in decisions if d.get("map") == "0:9"), {})
    # SEEN = inside the window of the tile it was first seen from (the perception rule); the record's `in_window` is
    # "inside the window NOW", which an honest target seen two steps ago need not be (the sweep: TOWN seeds 4 and 6)
    seen = bool(first_town.get("known") and first_town.get("seen_from")
                and in_window(tuple(first_town["seen_from"]), tuple(first_town["target"])))
    # (build step 3.1, finding 1: a tile past an edge is a road only after a crossing is SEEN, so the uncropped eyes no
    # longer beeline to a 'road': their first town target is whatever far place they saw, a door or the frontier at the
    # far end of the margin they showed; what separates them is that it was NOT SEEN, whatever its kind)
    run.check(bool(first_town) and not seen,
              f"the first target on LITTLEROOT_TOWN: a {first_town.get('kind')} at {first_town.get('target')} from "
              f"{first_town.get('player')}, first 'seen' from {first_town.get('seen_from')}: inside that window: {seen} (a place it "
              f"could not have seen; in the window now: {first_town.get('in_window')})")
    # NOT A CHECK (the step-3 verifier): the walk's LENGTH does not tell a cropped run from an uncropped one. An honest
    # TOWN seed can be as short (the seed sweep's Story seed 1: 26 steps, CROP's own total), so the two checks above
    # (tiles known from outside every window; a first target on the town it could not have seen) are the
    # discriminators, and `gates/rate_step3.py` measures them over 10 seeds of each (CROP-SEP in its evidence).
    steps = walk_steps_on(run, "0:9")
    if town is not None:
        real = walk_steps_on(town, "0:9")
        real_decisions = sum(1 for r in town.records if r.get("decision") == "decide")
        run.notes.append(f"for the record, NOT a discriminator: {steps} walking steps and {len(decisions)} decisions on the way "
                         f"(the real TOWN arm of this session, the same seed: {real} and {real_decisions})")
    else:
        run.notes.append(f"for the record, NOT a discriminator: {steps} walking steps on LITTLEROOT_TOWN, {len(decisions)} decisions")


def grade_STUCK(run: Run) -> None:
    grade_common(run, "explore: stuck: ping-pong:")
    before, after = run.before or {}, run.after or {}
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    run.check(0 < frames < run.arm.frames // 2, f"no hang: it gave up by itself after {frames} of {run.arm.frames} frames")
    n = names(run)
    ai = [t for t in transitions(run) if t[4] == "ai" and n.get(t[1]) == "LITTLEROOT_TOWN_BRENDANS_HOUSE_2F"]
    scene = [t for t in transitions(run) if t[4] == "scene"]
    run.check(len(ai) == 3 and len(scene) >= 2,
              f"the stairs used by the AI exactly 3 times ({[t[0] for t in ai]}), the scene's warps back recorded as the scene's "
              f"({len(scene)}): no door ping-pong past the rule")
    run.check(after.get("VAR_LITTLEROOT_INTRO_STATE") == 5 and after.get("FLAG_SET_WALL_CLOCK") is False
              and (after.get("map") or [None])[0] == 1,
              f"TRUTH: VAR_LITTLEROOT_INTRO_STATE {after.get('VAR_LITTLEROOT_INTRO_STATE')} (5), FLAG_SET_WALL_CLOCK "
              f"{after.get('FLAG_SET_WALL_CLOCK')} (False), map {after.get('map')} (still the house): nothing advanced")
    check_crop(run)


def rom_tile(state: Path, map_key: tuple[int, int], xy: tuple[int, int]) -> dict:
    """The SECOND PATH for BUMP: the ROM layout's facts at a tile, read by the framework's `MapLocation` (test side)."""
    code = ("import json,sys;from pathlib import Path;sys.path.insert(0,r'%s');from ai_player.gates.probe_eyes import boot;"
            "c=boot('ai-step0-fixture');c.emulator.load_save_state(Path(r'%s').read_bytes());c.emulator.run_single_frame();"
            "from modules.map import get_map_data;t=get_map_data(%r,%r);"
            "print('ROM '+json.dumps({'behaviour':t.tile_type,'collision':t.collision,'elevation':t.elevation}))"
            % (REPO, state, map_key, xy))
    data, raw = run_json([sys.executable, "-c", code], "ROM", clean_env({}), 300)
    return data or {"error": raw[-500:]}


def walk_steps_of(presses: list[dict]) -> list[tuple]:
    """(direction, from, to) of each "walk ..." gate (the first chunk of a step the AI pressed)."""
    out = []
    for p in presses:
        m = re.match(r"walk (\w+): \((-?\d+), (-?\d+)\) -> \((-?\d+), (-?\d+)\)", str(p.get("reason")))
        out.append((m.group(1), (int(m.group(2)), int(m.group(3))), (int(m.group(4)), int(m.group(5)))) if m else None)
    return out


def one_way_crossed(records: list[dict]) -> tuple[bool, str, list, list]:
    """(build step 3.1, finding 4) BUMP's errands 2, (0,4) -> (2,4), and 3, back to (0,4), from the action log's walking
    gates: crossed STRAIGHT THROUGH the one-way tile (1,4) from its open sides (2 steps each way), as the per-side rule
    allows; step 3's rule (one bump walls every side) walks round it. (The step-3.1 verifier's second round: the check
    also grades the revert arm BUMPSR, where it must FAIL.)"""
    presses = [r for r in records if str(r.get("action", "")).startswith(("press ", "hold "))]
    errand2 = [p for p in presses if str(p.get("reason", "")).startswith("walk ") and "toward the goto at (2, 4)" in p["reason"]]
    errand3 = [p for p in presses if str(p.get("reason", "")).startswith("walk ") and "toward the goto at (0, 4)" in p["reason"]
               and p["frame"] > (errand2[-1]["frame"] if errand2 else 10**12)]
    want2 = [("right", (0, 4), BUMP_TILE), ("right", BUMP_TILE, (2, 4))]
    want3 = [("left", (2, 4), BUMP_TILE), ("left", BUMP_TILE, (0, 4))]
    got2, got3 = walk_steps_of(errand2), walk_steps_of(errand3)
    ok = got2 == want2 and got3 == want3
    text = (f"THE ONE-WAY TILE CROSSED FROM ITS OPEN SIDES: errand 2, (0,4) -> (2,4): {got2} (want {want2}: straight through "
            f"{BUMP_TILE} going right); errand 3, back: {got3} (want {want3}) (step 3 walked round it in 4: a bump walled "
            f"every side)")
    return ok, text, got2, got3


def grade_BUMP(run: Run) -> None:
    grade_common(run, "goto: done:")
    after = run.after or {}
    world = memory_of(run)
    bumped = {key: sorted(memory.bumped) for key, memory in (world.maps.items() if world else [])}
    # (build step 3.1, the step-3 review's finding 4) a bump belongs to the SIDE it came from: (1, 4) refused the player
    # going DOWN, and that is all the AI learned of it
    run.check(bumped == {"1:1": [(BUMP_TILE, "down")]},
              f"exactly one way in learned blocked by bumping: {bumped} (want {{'1:1': [({BUMP_TILE}, 'down')]}})")
    bump_lines = [line for line in world_lines(run) if "BUMP:" in line]
    run.check(len(bump_lines) == 1 and f"{BUMP_TILE} is learned blocked moving down" in bump_lines[0],
              f"ONE bump: {bump_lines[0][:260] if bump_lines else 'none'}")
    learned_at = next((r["frame"] for r in run.records if r.get("decision") == "world" and "BUMP:" in str(r.get("reason"))), None)
    down = [(p["frame"], p["reason"][:60]) for p in run.presses if str(p.get("reason")).startswith(f"walk down: (1, 3) -> {BUMP_TILE}")]
    later = [t for t in down if learned_at is not None and t[0] > learned_at]
    run.check(len(down) == 1 and not later,
              f"pressed DOWN into {BUMP_TILE} once (the bump, f{down[0][0] if down else '?'}) and never again that way after it was "
              f"learned (f{learned_at}): later {later or 'none'}")
    decisions = [r for r in run.records if r.get("decision") == "decide"]
    ok, text, _, _ = one_way_crossed(run.records)
    run.check(ok, text)
    run.measure("bumps", sum(len(v) for v in bumped.values()))
    rom = rom_tile(FIXTURES[run.arm.fixture][0], (1, 1), BUMP_TILE)
    run.check(rom.get("collision") == 0 and "Impassable" in str(rom.get("behaviour")),
              f"WHY, by a second path (the ROM layout via the framework's MapLocation): {BUMP_TILE} has collision {rom.get('collision')} "
              f"(the eyes call it walkable) and behaviour {rom.get('behaviour')!r} (it blocks a step from the north)")
    run.check(after.get("pos") == [0, 4] and after.get("map") == HOUSE_2F,
              f"TRUTH (save block 1): the last errand's tile [0, 4] == {after.get('pos')} on {after.get('map')}")
    run.notes.append(f"decisions: {[(r['frame'], r['action']) for r in decisions]}")
    check_crop(run)


def grade_BUMPR(run: Run) -> None:
    data = run.harness or {}
    run.check(str(data.get("reason", "")).startswith("goto: stuck"), f"the run's outcome: {str(data.get('reason'))[:200]!r} (want goto: stuck ...)")
    bumps = [line for line in data.get("lines") or [] if "BUMP:" in line and f"{BUMP_TILE} is learned blocked" in line]
    run.check(len(bumps) >= 10, f"HARM: {len(bumps)} bumps into the same tile {BUMP_TILE} (want >= 10): the bump is not remembered")
    truth = data.get("truth") or {}
    run.check(truth.get("pos") != [0, 4], f"errand 1 was never done: the player ended at {truth.get('pos')}, not (0, 4)")
    run.check(isinstance(data.get("frames"), int) and data["frames"] < run.arm.frames,
              f"no hang: it gave up within its budget: {data.get('frames')} of {run.arm.frames} frames")


def grade_BUMPSR(run: Run, bump: Run | None) -> None:
    """(the step-3.1 verifier's second round: "FINDING 4 (bumps keyed by tile and direction) has no live revert arm ...
    BUMP's live check 'THE ONE-WAY TILE CROSSED FROM ITS OPEN SIDES' has never been run against the reverted rule")
    BUMP's start, errands and seed from a COPY where one bump walls the tile from EVERY side (`revert_step3.py` W34, the
    step-3 rule): BUMP's own check must FAIL on this run, with the same one bump learned."""
    data = run.harness or {}
    run.check(str(data.get("reason", "")).startswith("goto: done"), f"the run's outcome: {str(data.get('reason'))[:160]!r}")
    world = memory_of(run)
    bumped = {key: sorted(memory.bumped) for key, memory in (world.maps.items() if world else [])}
    run.check(bumped == {"1:1": [(BUMP_TILE, "down")]},
              f"the SAME one bump as BUMP's, learned the same way: {bumped} (want {{'1:1': [({BUMP_TILE}, 'down')]}}): the "
              f"difference is only what the AI made of it")
    ok, text, got2, got3 = one_way_crossed(run.records)
    run.check(not ok, f"HARM (finding 4's per-side rule reverted): BUMP's own check FAILS on this run: {text}")
    run.check(len(got2) == 4 and len(got3) == 4 and BUMP_TILE not in [step[2] for step in got2 + got3 if step],
              f"walked ROUND the one-way tile: errand 2 in {len(got2)} steps, errand 3 in {len(got3)}, never onto {BUMP_TILE} "
              f"(want 4 each: step 3's way, every side walled after one bump from above)")
    run.measure("bumps", sum(len(v) for v in bumped.values()))
    run.measure("errand_steps", [len(got2), len(got3)])
    if bump is not None:
        _, _, real2, real3 = one_way_crossed(bump.records)
        theirs = ((bump.verdict or {}).get("counters") or {}).get("real_frames")
        run.check(len(real2) == 2 and len(real3) == 2,
                  f"A/B on the same fixture, errands and seed: errands 2 and 3 in {len(real2)} + {len(real3)} steps with the rule "
                  f"({bump.arm.name}, straight through), {len(got2)} + {len(got3)} without; {theirs} frames with, "
                  f"{data.get('frames')} without")


def grade_WARPREAD(run: Run) -> None:
    """(the step-3.1 verifier's second round: "FINDING 5's guard only checks syntax ... a `getattr` read is not [caught]; a
    raw-memory read of gMapHeader's events would also get past it") The behavioural guard (`gates/warp_reads.py`): the
    REAL eyes' every read against every map's warp array, and three plants, each of which must be caught."""
    d = run.harness or {}
    real = d.get("real") or {}
    starts = real.get("starts") or []
    if not starts:
        run.check(False, f"the scan ran: {str(real)[:400]}")
        return
    run.check(real.get("warp_arrays", 0) > 400 and all(s["reads"] > 1000 and s["rom_reads"] > 0 for s in starts),
              f"THE RECORDER SAW THE EYES READ: {real.get('warp_arrays')} warp arrays in the ROM; reads per start "
              f"{[(s['start'], s['reads'], s['rom_reads']) for s in starts]} (all, then those in the cartridge)")
    with_warps = [s for s in starts if any(s["own_warp_arrays"].values())]
    run.check(len(with_warps) >= 4 and all(s["map_events_read"] for s in starts),
              f"NON-VACUITY: {len(with_warps)} of {len(starts)} starts stand on a map WITH warps "
              f"({[(s['start'], list(s['own_warp_arrays'].values())) for s in with_warps]}), and on every start the recorder saw "
              f"the eyes read that map's MapEvents struct, one pointer from its warp array (the signs: `bg_events`): "
              f"{[(s['start'], s['map_events_read']) for s in starts]}")
    hits = {s["start"]: s["warp_table_read_count"] for s in starts}
    run.check(not any(hits.values()),
              f"THE REAL EYES READ NO WARP TABLE, by any route: reads overlapping a warp array, per start: {hits} (want all 0)")
    static = d.get("static_real") or {}
    run.check(static and not any(static.values()),
              f"and the STATIC check on every host file names none: {static}")
    plants = d.get("plants") or {}
    caught_all = True
    lines = []
    for name in ("attribute", "getattr", "raw"):
        p = plants.get(name) or {}
        scan = (p.get("scan") or {}).get("starts") or []
        caught = {s["start"]: s["warp_table_read_count"] for s in scan}
        every = bool(scan) and all(caught.get(s["start"], 0) > 0 for s in with_warps)
        caught_all &= every
        run.measure(f"plant_{name}_caught", sum(1 for v in caught.values() if v))
        lines.append(f"{name} ({p.get('code', '')[:90]}): the scan caught it on {sum(1 for v in caught.values() if v)} of "
                     f"{len(scan)} starts (every start with warps: {every}); the static check: {p.get('static') or 'NOTHING'}")
    static_ok = bool((plants.get("attribute") or {}).get("static")) and bool((plants.get("getattr") or {}).get("static")) \
        and not (plants.get("raw") or {}).get("static")
    run.check(caught_all and static_ok,
              f"FAULT-TESTS, three plants in host/eyes.py `_map_facts` (each in a COPY): " + "; ".join(lines)
              + " (want: the scan catches all three; the static check the first two, and it cannot see the raw read: that is "
                "what the scan is for)")


def grade_F2AB(run: Run, done: dict) -> None:
    """(the step-3.1 verifier's second round: "FINDING 2's live check at seed 3 separates fixed from reverted by a single
    event per arm") Every live pair of this session for finding 2 together: the real arm against its revert. The claim
    rests on the STALE TARGETS WALKED ONTO (0 against several, on every pair); the reversals are a few events in all,
    reported; the frequency is the sweep's REVERT A/B."""
    pairs = [(a, r) for a, r in (("HOUSE", "HOUSER"), ("TOWN", "TOWNR"), ("ROUTE", "ROUTER"), ("TOWN9", "TOWN9R"),
                                 ("ROUTE9", "ROUTE9R")) if a in done and r in done]
    rows, totals = [], {"real": [0, 0, 0], "revert": [0, 0, 0]}
    every = bool(pairs)
    for a, r in pairs:
        cells = []
        for side, name in (("real", a), ("revert", r)):
            steps, found = path_reversals(done[name])
            _, arrived = stale_arrivals(done[name])
            walked = sum(1 for x in arrived if x["everything_beside_it_seen"])
            totals[side][0] += len(found)
            totals[side][1] += steps
            totals[side][2] += walked
            cells.append((len(found), steps, walked))
        every &= cells[0][2] == 0 and cells[1][2] > 0
        rows.append(f"{a} vs {r}: stale walked onto {cells[0][2]} vs {cells[1][2]}; reversals {cells[0][0]} in {cells[0][1]} "
                    f"steps vs {cells[1][0]} in {cells[1][1]}")
    real, rev = totals["real"], totals["revert"]
    run.check(len(pairs) == 5 and every,
              f"THE DISCRIMINATOR, on every pair ({len(pairs)} pairs, seeds 3 and 9): 0 stale targets walked onto with the rules, "
              f"> 0 without: {every}. " + " | ".join(rows))
    run.check(rev[2] > real[2] and rev[0] > real[0],
              f"IN ALL: stale targets walked onto {real[2]} with the rules, {rev[2]} without (the claim rests on this); "
              f"reversals {real[0]} in {real[1]} steps with, {rev[0]} in {rev[1]} without (a handful of events: reported; "
              f"the frequency is the sweep's REVERT A/B, `evidence/<date>-step3-RATE.txt`)")
    run.measure("stale_walked_real", real[2])
    run.measure("stale_walked_revert", rev[2])
    run.measure("reversals_real", real[0])
    run.measure("reversals_revert", rev[0])


def grade_CLOCKS(run: Run) -> None:
    """(the step-3.1 verifier's second round) WHICH launcher trajectories depend on the game's clock. Every launcher arm,
    in-process, the cartridge's clock pinned at `CLOCK_INSTANTS`: the arms whose frames and presses are the same at every
    instant may pre-register them for a launcher run (whenever it is played); the arms that change are exactly
    `CLOCK_SENSITIVE` (pre-registered: a new one would mean a launcher prediction that can miss by the hour); and at
    `GAME_CLOCK` every arm's trajectory is registered here (`PREDICTED`, the numbers an in-process run reproduces)."""
    rows = (run.harness or {}).get("rows") or []
    errors = [r for r in rows if "error" in r]
    run.check(bool(rows) and not errors, f"every launcher arm ran at every instant: {len(rows)} runs, failed {errors[:2] or 'none'}")
    by_arm: dict[str, list[dict]] = {}
    for row in rows:
        by_arm.setdefault(row["arm"], []).append(row)
    varies = sorted(name for name, cells in by_arm.items() if len({(c.get("frames"), c.get("presses")) for c in cells}) > 1)
    stable = sorted(name for name in by_arm if name not in varies)
    run.check(varies == sorted(CLOCK_SENSITIVE),
              f"THE CLOCK-SENSITIVE ARMS: {varies} (pre-registered {sorted(CLOCK_SENSITIVE)}); per arm, the trajectories over "
              f"{len(CLOCK_INSTANTS)} instants from {CLOCK_INSTANTS[0]} to {CLOCK_INSTANTS[-1]}: "
              + "; ".join(f"{name} {sorted({(c.get('frames'), c.get('presses')) for c in by_arm[name]})}" for name in varies))
    mismatch = [(name, PREDICTED.get(name, {}).get("frames"), by_arm[name][0].get("frames")) for name in stable
                if "frames" in PREDICTED.get(name, {}) and PREDICTED[name]["frames"] != by_arm[name][0].get("frames")]
    unregistered = [name for name in stable if "frames" not in PREDICTED.get(name, {})]
    registered_sensitive = [name for name in varies if "frames" in PREDICTED.get(name, {})]
    run.check(not mismatch and not unregistered and not registered_sensitive,
              f"a launcher arm's frames are pre-registered (`PREDICTED`) exactly when they hold at EVERY clock: the {len(stable)} "
              f"stable arms all registered, each at the frames it plays at every instant (mismatched: {mismatch or 'none'}; "
              f"unregistered: {unregistered or 'none'}); the clock-sensitive ones registered with none: "
              f"{registered_sensitive or 'none'} (their launcher checks are the graders' own, which hold at any clock)")
    # what the clock-sensitive arms' launcher claims rest on must hold at EVERY instant (their trajectories differ)
    twin_bad = [(c["arm"], c["when"], c.get("twin_segments"), c.get("map"), c.get("var")) for name in varies if name.startswith("SCENEX")
                for c in by_arm[name] if not (c.get("twin_segments") and 1 < c["twin_segments"][0] <= TWIN_SCENES_IN_ALL
                                              and all(n <= 1 for n in c["twin_segments"][1:]))]
    roam_bad = [(c["when"], c.get("steps"), c.get("spin_ratio")) for c in by_arm.get("ROAM", [])
                if not (c.get("steps") == 150 and isinstance(c.get("spin_ratio"), (int, float)) and c["spin_ratio"] < 0.02)]
    run.check(not twin_bad and not roam_bad and all("twin_segments" in c for name in varies if name.startswith("SCENEX")
                                                    for c in by_arm[name]),
              f"THE CLOCK-SENSITIVE ARMS' CLAIMS HOLD AT EVERY INSTANT: the twin's push-backs before news and between news "
              + "; ".join(f"{name} {[(c['when'][5:], c.get('twin_segments'), c.get('map'), c.get('var')) for c in by_arm[name]]}"
                          for name in varies if name.startswith("SCENEX"))
              + f" (want 2..{TWIN_SCENES_IN_ALL} before any news, <= 1 after each; not: {twin_bad or 'none'}); ROAM's 150 "
              f"steps and back-and-forth spin ratio < 2% {[(c['when'][5:], c.get('steps'), c.get('spin_ratio')) for c in by_arm.get('ROAM', [])]} "
              f"(not: {roam_bad or 'none'})")
    for name, cells in by_arm.items():
        pinned = next((c for c in cells if c["when"] == GAME_CLOCK), None)
        if pinned is not None:
            run.measure(f"{name}@pinned", [pinned.get("frames"), pinned.get("presses")])
    run.measure("clock_sensitive", varies)
    run.notes.append("per arm and instant (frames, presses): " + json.dumps(
        {name: {c["when"]: [c.get("frames"), c.get("presses")] for c in cells} for name, cells in by_arm.items()}))


def grade_TRN(run: Run) -> None:
    grade_common(run, "explore: stuck: a trainer battle: out of scope", walking=False)
    menu = [p for p in run.presses if "battle_action" in str(p.get("reason"))]
    run.check(not menu, f"NOTHING pressed on the battle's action menu: {[(p['frame'], p['reason'][:50]) for p in menu][:3] or 'none'}")
    after = run.after or {}
    run.check(stats(run.before, "trainer_battles") == stats(after, "trainer_battles"),
              f"the game's trainer-battle count unchanged ({stats(run.before, 'trainer_battles')} -> {stats(after, 'trainer_battles')}): "
              f"the battle was begun in the fixture, not by the AI")


def novelty_records(run: Run) -> list[dict]:
    """The navigator's novelty records (`[AI-WORLD] novelty at f...`: a novelty that is not a place, and the clock)."""
    return [r for r in run.records if r.get("decision") == "world" and str(r.get("reason", "")).startswith(NOVELTY_PREFIX)]


def intent_start(run: Run) -> int | None:
    """The frame of the intent's first look (its record "intent '...'": the novelty clock's starting value)."""
    record = next((r for r in run.records if r.get("decision") == "world" and str(r.get("reason", "")).startswith("intent ")), None)
    return None if record is None else record.get("frame")


def exp_of(truth: dict | None) -> dict[str, int]:
    """PID (hex) -> total experience, by the framework's own decoder (`hands_harness.py` truth: `party_exp`)."""
    return {row[0]: row[2] for row in (truth or {}).get("party_exp") or []}


def grade_XP(run: Run) -> None:
    """(the step-3 verifier's second round: "no live run has yet shown an intent's novelty clock reset by an XP gain")"""
    grade_common(run, "goto: stuck: nothing new")
    before, after = run.before or {}, run.after or {}
    e0, e1 = exp_of(before), exp_of(after)
    run.check(before.get("game_state") == "BATTLE" and len(e0) == 1,
              f"NON-VACUITY (the fixture, by the framework): a battle on screen ({before.get('game_state')}), the party "
              f"{before.get('party_exp')}: its experience not yet given")
    records = novelty_records(run)
    start = intent_start(run)
    record = records[0] if len(records) == 1 else {}
    extra = record.get("extra") or {}
    frame, clock = record.get("frame"), extra.get("clock")
    pid = next(iter(e1), None)
    want = f"experience gained (PID {pid}: {e0.get(pid)} -> {e1.get(pid)})"
    run.check(len(records) == 1 and extra.get("novelty") == [want],
              f"the AI told ONE novelty in the whole intent, and it is the experience, by IDENTITY: {[r.get('reason') for r in records]} "
              f"(want exactly [{want!r}]: the PID and both totals the framework's get_party() reads before and after)")
    ended = next((r["frame"] for r in run.records if r.get("decision") == "world" and str(r.get("reason", "")).startswith("battle:")), None)
    run.check(clock == [start, frame] and isinstance(ended, int) and ended <= frame and isinstance(start, int) and frame - start >= 300,
              f"the intent's CLOCK moved from its start f{start} to the experience gain f{frame} ({clock}), {None if not isinstance(frame, int) or not isinstance(start, int) else frame - start} "
              f"frames on, once the battle was over (f{ended}) and the AI looked at the party again")
    match = STUCK_NOTHING_NEW.search(run.outcome)
    end = after.get("frame")
    quiet, last = (int(match.group(1)), int(match.group(2))) if match else (None, None)
    run.check(match is not None and last == frame and "experience gained" in match.group(3) and quiet >= 3000
              and isinstance(end, int) and abs(end - (last + quiet)) <= FRAME_SLACK and isinstance(start, int) and end - start > quiet,
              f"BEHAVIOUR: the intent ended 'stuck: nothing new' {quiet} frames after the LAST novelty f{last} "
              f"({match.group(3) if match else '?'!r}), at f{end} (the state's frame, +-{FRAME_SLACK}): "
              f"{None if not isinstance(end, int) or not isinstance(start, int) else end - start} frames after the intent's start: "
              f"the experience gain bought it {None if not isinstance(frame, int) or not isinstance(start, int) else frame - start} frames")
    run.check(bool(e0) and bool(e1) and pid in e0 and e1[pid] > e0[pid],
              f"TRUTH (the framework's get_party, total_exp by PID): {e0} -> {e1}: the game gave the experience")
    w0, w1 = stats(before, "wild_battles"), stats(after, "wild_battles")
    met = [line for line in world_lines(run) if line.startswith("[AI-WORLD] battle:")]
    run.check(w0 == w1 and len(met) == 1 and "the battle ended" in met[0],
              f"the battle was the fixture's (the game's wild-battle count {w0} -> {w1}), ended by the AI reading it out: {met}")
    first = next((line for line in world_lines(run) if "memory from" in line), "")
    last_line = next((line for line in world_lines(run) if "memory at the end" in line), "")
    count = lambda line: (re.search(r"(\d+) tiles learned", line) or [None, None])[1]  # noqa: E731
    run.check("route101_xp.world.jsonl" in first and count(first) is not None and count(first) == count(last_line),
              f"NO PLACE was new (the memory of the AI's own errands was LOADED and knew every tile it saw): tiles learned "
              f"{count(first)} at the start, {count(last_line)} at the end")
    check_crop(run)


def grade_XPR(run: Run, xp: Run | None) -> None:
    data = run.harness or {}
    reason = str(data.get("reason", ""))
    match = STUCK_NOTHING_NEW.search(reason)
    lines = [line for line in data.get("lines") or [] if "] novelty at f" in line]
    truth = data.get("truth") or {}
    run.check(match is not None and match.group(3) == "none" and not lines,
              f"HARM: with experience not novelty the intent never saw anything new: {reason[:220]!r}; novelty lines: {lines or 'none'}")
    if match is not None:
        quiet, last = int(match.group(1)), int(match.group(2))
        run.check(abs(truth.get("frame", 0) - (last + quiet)) <= FRAME_SLACK,
                  f"stuck {quiet} frames after the intent's START f{last} (the clock never moved), at f{truth.get('frame')}")
    if xp is not None and match is not None:
        xp_end, xp_start = (xp.after or {}).get("frame"), intent_start(xp)
        here = truth.get("frame", 0) - int(match.group(2))
        there = (xp_end - xp_start) if isinstance(xp_end, int) and isinstance(xp_start, int) else None
        run.check(there is not None and here < there - 300,
                  f"A/B on the same fixture and seed: the intent lasted {here} frames here and {there} with the experience counted "
                  f"(XP): the gain alone moved the stuck verdict {None if there is None else there - here} frames later")
    run.check(exp_of(truth) and any(exp_of(truth)[k] > v for k, v in exp_of(data.get("start_truth")).items() if k in exp_of(truth)),
              f"the game DID give the experience here too (get_party): {exp_of(data.get('start_truth'))} -> {exp_of(truth)}: the "
              f"mutant ignored it")


def scene_lines(lines: list[str]) -> list[str]:
    return [line for line in lines if SCENE_LINE in line]


def grade_SCENE(run: Run) -> None:
    """(build step 3.1, the step-3 review's finding 3) A REPEATING SCENE: Littleroot's twin pushes a player with no
    Pokemon back from the road every time; the errand past her is given up after the second time, nothing new."""
    grade_common(run, f"goto: stuck: the goto at {SCENE_TARGET} cannot be reached (a scene stopped the way there 2 times")
    before, after = run.before or {}, run.after or {}
    run.check(before.get("map") == LITTLEROOT and before.get("VAR_LITTLEROOT_TOWN_STATE") == 0,
              f"NON-VACUITY (the fixture, by save block 1): map {before.get('map')} (LITTLEROOT_TOWN {LITTLEROOT}), "
              f"VAR_LITTLEROOT_TOWN_STATE {before.get('VAR_LITTLEROOT_TOWN_STATE')} (0: the rival not met, so the twin's coord "
              f"events at (10,1) and (11,1) run every time: LittlerootTown_EventScript_NeedPokemonTrigger*)")
    told = scene_lines(world_lines(run))
    given_up = [line for line in world_lines(run) if "given up" in line and "a scene stopped the way there" in line]
    run.check(len(told) == 2 and len(given_up) == 1,
              f"the scene met on the way to {SCENE_TARGET} exactly TWICE, then the target given up: {told}; {given_up}")
    frames = ((run.verdict or {}).get("counters") or {}).get("real_frames") or 0
    run.check(0 < frames < 3000, f"no wait for the novelty window: it gave up after {frames} frames (the window alone: 3000 "
                                 f"frames after the last novelty)")
    run.check(after.get("map") == LITTLEROOT and after.get("pos") == SCENE_PUSHED_TO
              and after.get("VAR_LITTLEROOT_TOWN_STATE") == 0,
              f"TRUTH (save block 1): on {after.get('map')} at {after.get('pos')} (pushed back to {SCENE_PUSHED_TO} by the "
              f"scene), VAR_LITTLEROOT_TOWN_STATE {after.get('VAR_LITTLEROOT_TOWN_STATE')} (0: nothing advanced)")
    a = [p for p in run.presses if p["action"].startswith("press A ")]
    run.check(len(a) >= 4, f"the scene's texts read through twice: {len(a)} A presses, each on a wait (the hands' check above)")
    check_crop(run)


def grade_SCENER(run: Run, scene: Run | None) -> None:
    data = run.harness or {}
    reason = str(data.get("reason", ""))
    told = scene_lines(data.get("lines") or [])
    run.check(reason.startswith("goto: stuck: nothing new") and len(told) >= 3,
              f"HARM: with the rule off the same scene stopped the way to {SCENE_TARGET} {len(told)} times (want >= 3: more than "
              f"the rule's 2; one round of the twin's scene takes ~1,100 frames, the window 3,000), and the intent ended only on "
              f"the novelty window: {reason[:220]!r}")
    run.check(isinstance(data.get("frames"), int) and data["frames"] >= 3000,
              f"it took {data.get('frames')} frames (want >= 3000: the novelty window)")
    if scene is not None:
        there = ((scene.verdict or {}).get("counters") or {}).get("real_frames")
        run.check(isinstance(there, int) and isinstance(data.get("frames"), int) and data["frames"] > there + 1000,
                  f"A/B on the same fixture and seed: {data.get('frames')} frames here, {there} with the rule (SCENE): the rule "
                  f"saved {None if not isinstance(there, int) else data['frames'] - there} frames of the same scene")
    truth = data.get("truth") or {}
    run.check(truth.get("VAR_LITTLEROOT_TOWN_STATE") == 0, f"nothing advanced: VAR_LITTLEROOT_TOWN_STATE {truth.get('VAR_LITTLEROOT_TOWN_STATE')}")


#: (the step-3.1 verifier's round) the scenes one tile may stop the explorer with before it stops stepping on that tile
#: (pre-registered, a literal: `brain/navigator.py` SCENE_REPEATS is the AI's own number, not the grade's)
TWIN_SCENES_PER_TILE = 2


def scenes_by_tile(records: list[dict]) -> dict:
    """(the step-3.1 verifier's round) Every scene that stopped the way to a target, by the tile it BEGAN on: the AI's own
    record (`began`), with a second reading from the action log, the player's tile on the look of the last walking press
    before it (the step the scene cut short), and the target it stopped (the explorer's own choice, or an errand)."""
    out: dict = {}
    for i, record in enumerate(records):
        if not (record.get("decision") == "world" and str(record.get("reason", "")).startswith("a scene stopped the way")):
            continue
        extra = record.get("extra") or {}
        press = next((p for p in reversed(records[:i]) if str(p.get("reason", "")).startswith(("walk ", "keep walking "))
                      and str(p.get("action", "")).startswith("hold ")), None)
        began = tuple(extra.get("began") or ()) or None
        out.setdefault(began, []).append({"frame": record.get("frame"), "target": tuple(extra.get("scene_for") or ()),
                                          "kind": extra.get("kind"), "after": extra.get("after"),
                                          "pressed_from": xy_of(press) if press is not None else None,
                                          "words": extra.get("words")})
    return out


def scene_walls_told(records: list[dict]) -> list[tuple[int, tuple[int, int], str]]:
    """The tiles the AI said it would not step on again (a scene sent the player back from them): (frame, tile, map)."""
    return [(r["frame"], tuple((r.get("extra") or {})["scene_wall"]), (r.get("extra") or {}).get("map")) for r in records
            if r.get("decision") == "world" and (r.get("extra") or {}).get("scene_wall")]


def twin_scenes(records: list[dict]) -> dict:
    """(the step-3.1 verifier's rounds) The twin's scenes in one run: by the tile each began on, in all, their words (the
    AI's own record of what she said), the targets they stopped, and the tiles the AI then gave up."""
    every = {tile: hits for tile, hits in scenes_by_tile(records).items() if tile in TWIN_TILES}
    # (the step-3.1 verifier's second round) her PUSH-BACKS only: at VAR_LITTLEROOT_TOWN_STATE 1 her scene on (11, 1) lets
    # the player pass ("Um, hi!": GoSaveBirchTrigger), which is no meeting that sends the player back
    twin = {tile: [h for h in hits if h.get("after") is not None and tuple(h["after"]) != tile] for tile, hits in every.items()}
    twin = {tile: hits for tile, hits in twin.items() if hits}
    pushes = sorted((h["frame"], tile) for tile, hits in twin.items() for h in hits)
    lifts = [r["frame"] for r in records if r.get("decision") == "world" and "lifted" in (r.get("extra") or {})]
    news = [(r["frame"], (r.get("extra") or {}).get("words")) for r in records if r.get("decision") == "world"
            and str(r.get("reason", "")).startswith("novelty at f") and (r.get("extra") or {}).get("words")]
    bounds = [0] + lifts + [10**12]
    segments = [sum(1 for f, _ in pushes if bounds[i] <= f < bounds[i + 1]) for i in range(len(bounds) - 1)]
    return {"by_tile": twin, "counts": {str(tile): len(hits) for tile, hits in sorted(twin.items())},
            "total": sum(len(h) for h in twin.values()), "worst": max((len(h) for h in twin.values()), default=0),
            "words": sorted({str(hit.get("words")) for hits in twin.values() for hit in hits}),
            "targets": sorted({hit["target"] for hits in twin.values() for hit in hits}),
            "walls": scene_walls_told(records), "lifts": lifts, "news": news, "segments": segments,
            "passed_her": [(h["frame"], str(tile), h.get("words")) for tile, hits in every.items() for h in hits
                           if h.get("after") is None or tuple(h["after"]) == tile]}


def grade_SCENEX(run: Run) -> None:
    """(the step-3.1 verifier's round: "the SCENE plan ... tests the scene rule on a scripted goto target, not on a target
    the explorer chose") The EXPLORER from the twin's fixture: its own targets behind the twin. (The step-3.1 verifier's
    second round: "the twin guards two tiles, so the explorer meets her 4 times in total"; "SCENEX's budget was chosen so
    the run ends outdoors ... what happens after the twin is not graded by the game's answer") The twin is now known by
    her WORDS: at most `TWIN_SCENES_IN_ALL` meetings in all, every tile she began on given up and never stepped on after;
    and the run goes to its OWN end (the novelty window, not a budget), with the rest of the town explored after her, and
    the game's answer graded wherever that end is (`grade_common`). MEASURED: the end is ROUTE101. After her, the explorer
    meets May in her house; her words are NEWS (`Novelty.heard`), so the twin's tiles are worth a try again; at
    VAR_LITTLEROOT_TOWN_STATE 1 the twin lets the player pass ("Um, hi!", GoSaveBirchTrigger, state 2), and Birch's
    rescue scene locks the player on Route 101's first tile: the game's answer there is LOCKED + THE ARRIVAL across the
    edge the AI walked off (`ARRIVALS`, `game_answer.py --after-connection`)."""
    grade_common(run, "explore: done: explore to ROUTE101")
    before, after = run.before or {}, run.after or {}
    run.check(before.get("map") == LITTLEROOT and before.get("VAR_LITTLEROOT_TOWN_STATE") == 0,
              f"NON-VACUITY (the fixture, by save block 1): map {before.get('map')} (LITTLEROOT_TOWN), VAR_LITTLEROOT_TOWN_STATE "
              f"{before.get('VAR_LITTLEROOT_TOWN_STATE')} (0: the twin's coord events at {list(TWIN_TILES)} run every time)")
    by_tile = scenes_by_tile(run.records)
    t = twin_scenes(run.records)
    twin = t["by_tile"]
    other = {tile: len(hits) for tile, hits in by_tile.items() if tile not in TWIN_TILES}
    second = all(hit["pressed_from"] == tile for tile, hits in twin.items() for hit in hits)
    first = t["segments"][0] if t["segments"] else 0
    run.check(1 < first <= TWIN_SCENES_IN_ALL and t["worst"] <= TWIN_SCENES_PER_TILE + len(t["lifts"]) and len(t["targets"]) >= 2
              and second,
              f"THE TWIN SENDS THE PLAYER BACK, by the tile each began on: {t['counts']}; before any news {first} times (want "
              f"2..{TWIN_SCENES_IN_ALL}: counted per tile alone it was 4, twice on each, the verifier's finding); the AI's own tile "
              f"== the tile of the look of the walking press it cut short, every time: {second}; the targets it stopped, the "
              f"EXPLORER's own choices: {t['targets']} (want >= 2 different); other scenes on the way: {other or 'none'}")
    same = [r for r in run.records if r.get("decision") == "world" and (r.get("extra") or {}).get("same_scene_tiles")]
    run.check(len(t["words"]) == 1 and t["words"][0] not in ("None", "") and bool(same),
              f"KNOWN BY HER WORDS: every push-back's words, as the AI's own record says them: {t['words']} (want one, the same "
              f"each time); the AI said it was the same scene from "
              f"{[(r['frame'], (r.get('extra') or {}).get('same_scene_tiles')) for r in same] or 'NOWHERE'}")
    walls, lifts = t["walls"], t["lifts"]
    met = sorted(twin)

    def lifted_after(frame: int) -> int:
        return min([f for f in lifts if f > frame] or [10**12])

    later = [(p["frame"], p["reason"][:50]) for frame, tile, key in walls for p in run.presses
             if frame < p["frame"] < lifted_after(frame) and str(p.get("reason", "")).startswith("walk ")
             and f"-> ({tile[0]}, {tile[1]})" in p["reason"] and map_name_of(p) == key]
    first_walls = sorted({tile for frame, tile, _ in walls if frame < (lifts[0] if lifts else 10**12)})
    run.check(bool(walls) and first_walls == met and not later,
              f"EVERY TILE SHE GUARDS GIVEN UP, NOT STEPPED ON AGAIN until news: the tiles the AI gave up before any news "
              f"{first_walls} == the tiles she began on {met}; walls {[(f, t2) for f, t2, _ in walls]}; a step onto one while it "
              f"was given up: {later or 'none'}")
    news = t["news"]
    run.check(bool(lifts) and bool(news) and bool(walls) and lifts[0] > walls[0][0] and all(n <= 1 for n in t["segments"][1:]),
              f"NEWS LIFTS HER, ONCE MORE IS ENOUGH: new words heard in scenes that left the player be "
              f"{[(f, w[:40]) for f, w in news]}; the tiles worth a try again at {lifts}; her push-backs between the news "
              f"{t['segments'][1:]} (want each <= 1: met once more with nothing new since, she is given up again at once)")
    run.check(after.get("VAR_LITTLEROOT_TOWN_STATE") == 2 and after.get("map") == ROUTE101 and bool(t["passed_her"]),
              f"WHAT HAPPENED AFTER THE TWIN, by save block 1: VAR_LITTLEROOT_TOWN_STATE {before.get('VAR_LITTLEROOT_TOWN_STATE')} "
              f"-> {after.get('VAR_LITTLEROOT_TOWN_STATE')} (want 2: May met in her house (1), then the twin let the player pass "
              f"(2): her scene that did NOT send the player back {t['passed_her'] or 'NONE'}), the player on {after.get('map')} "
              f"(ROUTE101 {ROUTE101}) at {after.get('pos')}; the run ended by ITSELF at its goal ({run.outcome[:60]!r}), not by a "
              f"budget; the game's answer on that tile above")
    run.measure("twin_pushes", t["total"])
    run.measure("twin_segments", t["segments"])
    check_crop(run)


def grade_SCENEXR(run: Run, real: Run | None) -> None:
    """(the step-3.1 verifier's second round) SCENEX from a COPY where a scene is not known by its words (counted per target
    and per tile only, the verifier's round's code): the twin, who guards two tiles, twice on EACH."""
    data = run.harness or {}
    t = twin_scenes(run.records)
    first = t["segments"][0] if t["segments"] else 0
    run.check(first > TWIN_SCENES_IN_ALL and t["counts"] and all(n >= TWIN_SCENES_PER_TILE for n in t["counts"].values()),
              f"HARM (the words rule reverted): the twin sent the player back {first} times before any news (want > "
              f"{TWIN_SCENES_IN_ALL}), by tile {t['counts']} in all: at least twice on each of her tiles, the per-tile rule alone "
              f"(the verifier's 'meets her 4 times in total'); her push-backs between news {t['segments']}; the outcome "
              f"{str(data.get('reason'))[:160]!r}")
    truth = data.get("truth") or {}
    if real is not None:
        mine = twin_scenes(real.records)
        mine_first = mine["segments"][0] if mine["segments"] else 0
        run.check(1 < mine_first <= TWIN_SCENES_IN_ALL < first and mine["total"] < t["total"],
                  f"A/B on the same fixture and seed: before any news {mine_first} push-backs with the rule (SCENEX, "
                  f"{mine['counts']} in all, {mine['total']}), {first} without ({t['counts']} in all, {t['total']}); the end: "
                  f"SCENEX on {(real.after or {}).get('map')} (VAR_LITTLEROOT_TOWN_STATE {(real.after or {}).get('VAR_LITTLEROOT_TOWN_STATE')}), "
                  f"this copy on {truth.get('map')} ({truth.get('VAR_LITTLEROOT_TOWN_STATE')})")
    run.check(truth.get("map") != ROUTE101,
              f"and it never got past her: the copy ended on {truth.get('map')} at {truth.get('pos')} (VAR_LITTLEROOT_TOWN_STATE "
              f"{truth.get('VAR_LITTLEROOT_TOWN_STATE')}), {str(data.get('reason'))[:80]!r}")
    run.measure("twin_pushes", t["total"])
    run.measure("twin_segments", t["segments"])


def grade_SCENENR(run: Run, real: Run | None) -> None:
    """(the step-3.1 verifier's second round) SCENEX from a COPY where NEW WORDS are not progress (`revert_step3.py` W53):
    May's "Who are you?" lifts nothing, so the explorer never tries the twin again and stops in May's house, "nothing
    new", with the road it could now take open (VAR_LITTLEROOT_TOWN_STATE 1): what the verifier's 'at 10,000 frames or
    more ... inside May's house' was."""
    data = run.harness or {}
    t = twin_scenes(run.records)
    truth = data.get("truth") or {}
    run.check(str(data.get("reason", "")).startswith("explore: stuck: nothing new") and not t["lifts"]
              and truth.get("map") != ROUTE101 and truth.get("VAR_LITTLEROOT_TOWN_STATE") == 1,
              f"HARM (new words not progress): no tile worth a try again ({t['lifts'] or 'none'}), the run stuck "
              f"{str(data.get('reason'))[:90]!r} on {truth.get('map')} at {truth.get('pos')}, VAR_LITTLEROOT_TOWN_STATE "
              f"{truth.get('VAR_LITTLEROOT_TOWN_STATE')} (want 1: May met, the twin would let the player pass now, and the AI "
              f"never tried her again)")
    if real is not None:
        run.check((real.after or {}).get("map") == ROUTE101 and truth.get("map") != ROUTE101,
                  f"A/B on the same fixture and seed: with new words as progress (SCENEX) the explorer reached "
                  f"{(real.after or {}).get('map')} (ROUTE101), without on {truth.get('map')}")
    run.measure("twin_pushes", t["total"])


def grade_REVR(run: Run, real: Run | None) -> None:
    """(the step-3.1 verifier's round: "the live reversal grades in HOUSE, TOWN and ROUTE do not tell the fixed code from
    the reverted code at seed 3") The arm's start and seed from a COPY with finding 2's two rules reverted: the live
    checks of the real arm must FAIL here, and the A/B against it shows the difference.
    (The step-3.1 verifier's second round: "FINDING 2's live check at seed 3 separates fixed from reverted by a single
    event per arm: 0 reversals against 1".) THE DISCRIMINATOR each pair's claim RESTS ON, said in its check (CLAUDE.md
    rule 7): the STALE TARGETS WALKED ONTO (0 with the rules, several without: the review's stale target itself). The
    reversal count is one or two events a run; at seed 3 the revert still breaks the real arm's pre-registered bound 0
    (a single event, labelled so), at seed 9 it need not (TOWN9R measured 1, as TOWN9). The FREQUENCY answer is the
    sweep's REVERT A/B (`rate_step3.py`), and this session's pairs together are arm F2AB."""
    data = run.harness or {}
    base = run.arm.base
    steps, found = path_reversals(run)
    limit = reversal_bound(base, run.arm.run_seed)
    chosen, arrived = stale_arrivals(run)
    walked = [a for a in arrived if a["everything_beside_it_seen"]]
    run.measure("steps", steps)
    run.measure("reversals", len(found))
    run.measure("stale_walked", len(walked))
    run.check(str(data.get("reason", "")).startswith("explore: "), f"the run's outcome: {str(data.get('reason'))[:160]!r}")
    run.check(len(walked) >= 1,
              f"HARM, THE DISCRIMINATOR this pair rests on: {len(walked)} of the {chosen} frontier targets were walked onto with "
              f"everything beside them already seen (the stale targets the review found): {[a['target'] for a in walked]}")
    if run.arm.run_seed == SEED:
        run.check(len(found) > limit,
                  f"and at seed {SEED}: {len(found)} reversals on the {steps} steps the looks showed, more than {base}'s "
                  f"pre-registered bound {limit}: the real arm's reversal check FAILS on the reverted code (ONE EVENT: not what "
                  f"the claim rests on) ({[(r['map'], r['kind'], r['tiles']) for r in found][:3]})")
    else:
        run.notes.append(f"reversals at seed {run.arm.run_seed}: {len(found)} on {steps} steps "
                         f"({[(r['map'], r['kind'], r['tiles']) for r in found][:3]}); the bound there is {limit}, not a claim")
    if real is not None:
        real_steps, real_found = path_reversals(real)
        _, real_arrived = stale_arrivals(real)
        real_walked = [a for a in real_arrived if a["everything_beside_it_seen"]]
        run.check(not real_walked and len(walked) > 0 and len(real_found) <= len(found),
                  f"A/B on the same start and seed: STALE TARGETS WALKED ONTO {len(real_walked)} with the rules ({base}), "
                  f"{len(walked)} without (the discriminator); reversals {len(real_found)} in {real_steps} steps with, "
                  f"{len(found)} in {steps} without (reported: not fewer without the rules)")


def grade_EDGER(run: Run, town: Run | None) -> None:
    """(the step-3.1 verifier's round: "the live check 'NO ROAD BEFORE A CROSSING' never fires") TOWN's start and seed
    from a COPY with finding 1 reverted (a map's top and left ends from negative coordinates): the same live check FAILS."""
    data = run.harness or {}
    probe = Run(run.arm, records=run.records, world=run.world)
    check_no_road_before_a_crossing(probe)
    ok, text = probe.checks[-1] if probe.checks else (True, "no check ran")
    past, _ = edge_targets(run)
    roads = road_claims(past)
    run.check(not ok and bool(roads),
              f"HARM (finding 1 reverted): the live check FAILS on this run: {len(roads)} targets chosen as ROADS past an edge no "
              f"crossing had shown ({[(t['map'], t['kind'], t['target'], t['side']) for t in roads[:3]]}); the check said: "
              f"{text[:260]}")
    if town is not None:
        mine, _ = edge_targets(town)
        run.check(not road_claims(mine) and bool(mine),
                  f"A/B on the same start and seed: TOWN chose {len(mine)} targets past an uncrossed edge, none a road; this copy "
                  f"chose {len(roads)} roads there")
    run.notes.append(f"the run's outcome: {str(data.get('reason'))[:200]!r}")


def grade_ROUTE9(run: Run) -> None:
    """(the step-3.1 verifier's round: "ROUTE seed 3 no longer meets a wild battle, so fleeing is proven live only by
    ROAM") ROUTE at seed 9, through the launcher: its every check, and a wild battle MET (and fled)."""
    grade_ROUTE(run)
    met = [line for line in world_lines(run) if line.startswith("[AI-WORLD] battle:")]
    run.check(len(met) >= 1 and all(line.startswith("[AI-WORLD] battle: fled") for line in met),
              f"NON-VACUITY of the flee check: {len(met)} wild battle(s) met on this trajectory, each fled: {met}")


def grade_EXITS(run: Run) -> None:
    """(build step 3.1, the step-3 review's finding 5) The eyes see exits by their LOOK; the ROM's warp table is read
    here only (`gates/exit_looks.py`), against them."""
    d = run.harness or {}
    if not d:
        run.check(False, "the ROM scan ran")
        return
    arm_maps = [w for w in d.get("v1") or [] if w["map"].startswith(ARM_MAP_PREFIXES)]
    unseen_arm = [w for w in arm_maps if not w["seen"]]
    run.check(not d.get("game_looks_not_in_the_eyes") and not d.get("step_warps_missed"),
              f"THE GAME'S OWN RULE: every look the game warps on (IsWarpMetatileBehavior, IsArrowWarpMetatileBehavior, "
              f"TryDoorWarp, a cracked floor; the Union Room's bridge look left out) is in the eyes' table (missing: "
              f"{d.get('game_looks_not_in_the_eyes') or 'none'}), and no warp tile of the ROM with such a look is unseen "
              f"({d.get('step_warps_missed') or 'none'})")
    run.check(len(arm_maps) > 20 and not unseen_arm,
              f"THE ARMS' MAPS (Littleroot, Route 101, Oldale, their buildings): all {len(arm_maps)} warp tiles LOOK like exits "
              f"(not: {unseen_arm or 'none'})")
    v1_unseen = d.get("v1_not_seen") or []
    run.notes.append(f"v1's other maps (Routes 102 and 103, Petalburg): {len(v1_unseen)} warp tiles look like plain ground, places "
                     f"a script puts the player (no step warps from such a look, by the game's rule: the first check): "
                     f"{sorted({(w['map'], w['look']) for w in v1_unseen})}")
    fault = d.get("fault_without_doormats") or {}
    fault_arm = [w for w in fault.get("not_seen") or [] if str(w[0]).startswith(ARM_MAP_PREFIXES)]
    run.check(len(fault_arm) > 0,
              f"FAULT-TEST of the arms' maps check: the same scan with the doormat look (SOUTH_ARROW_WARP) taken out of the eyes' "
              f"table leaves {len(fault_arm)} of their warp tiles unseen (want > 0; the real table: {len(unseen_arm)}): "
              f"{fault_arm[:4]}")
    run.notes.append(f"THE WHOLE ROM: {d.get('recognised')} of {d.get('warp_tiles')} warp tiles on {d.get('maps')} maps look like "
                     f"exits; the rest by look {d.get('unrecognised')} (e.g. {d.get('unrecognised_examples')}); exit-looking tiles "
                     f"with no warp (closed doors: tried once and remembered closed): {d.get('exits_looks_without_a_warp', d.get('exit_looks_without_a_warp'))}")


GRADERS = {"HOUSE": grade_HOUSE, "TOWN": grade_TOWN, "ROUTE": grade_ROUTE, "ROAM": grade_ROAM, "STUCK": grade_STUCK,
           "BUMP": grade_BUMP, "BUMPR": grade_BUMPR, "TRN": grade_TRN, "XP": grade_XP, "SCENE": grade_SCENE, "EXITS": grade_EXITS,
           "SCENEX": grade_SCENEX, "TOWN9": grade_TOWN, "ROUTE9": grade_ROUTE9,
           # the step-3.1 verifier's second round
           "WARPREAD": grade_WARPREAD, "HOUSE9": grade_HOUSE, "BUMP8": grade_BUMP, "SCENEX9": grade_SCENEX,
           "CLOCKS": grade_CLOCKS}
#: Graders that compare with another arm of the same session (the arm named): a fault arm or a revert and its real arm.
PAIRED = {"CROP": (grade_CROP, "TOWN"), "XPR": (grade_XPR, "XP"), "SCENER": (grade_SCENER, "SCENE"),
          "SCENEXR": (grade_SCENEXR, "SCENEX"), "HOUSER": (grade_REVR, "HOUSE"), "TOWNR": (grade_REVR, "TOWN"),
          "ROUTER": (grade_REVR, "ROUTE"), "EDGER": (grade_EDGER, "TOWN"),
          # the step-3.1 verifier's second round
          "BUMPSR": (grade_BUMPSR, "BUMP"), "BUMPSR8": (grade_BUMPSR, "BUMP8"), "TOWN9R": (grade_REVR, "TOWN9"),
          "ROUTE9R": (grade_REVR, "ROUTE9"), "SCENENR": (grade_SCENENR, "SCENEX")}
#: Graders of the whole session (every run graded before them): FINDING 2's A/B over its pairs.
SUMMARIES = {"F2AB": grade_F2AB}


# ---------------------------------------------------------------------- evidence
def md5_of(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def predictions_ref(source: Path = Path(__file__)) -> str:
    """(the step-3 verifier's second round: "I cannot check that the predictions were pre-registered before the graded
    run, because the tree is uncommitted") The PRE-REGISTERED predictions this run is graded against, pinned: sha256 of
    this file's module docstring, read from the file at the START of the run, before any arm. A reviewer recomputes it
    (`py -3.12 -c "import ast,hashlib;print(hashlib.sha256(ast.get_docstring(ast.parse(open(PATH,encoding='utf-8').read()),
    clean=False).encode()).hexdigest()[:16])"`): equal means the predictions in the file now are the ones this run read,
    unedited since. WHAT IT CANNOT SHOW: that they were written before a first look at a graded run; only a commit
    made before the run can (this round's worker may make no commit), or a re-run by someone else after reading them
    (the step-3 verifier did exactly that, and every arm's frames and presses equalled the predictions)."""
    import ast

    text = ast.get_docstring(ast.parse(source.read_text(encoding="utf-8")), clean=False) or ""
    numbers = json.dumps(predicted_numbers(source), sort_keys=True)
    # (the step-3.1 verifier's second round) the PREDICTED table is pre-registered too: it is in the digest (when the
    # file has one; the one-line recompute of earlier rounds is the docstring-only digest, still printed beside it)
    both = hashlib.sha256((text + "\n" + numbers).encode("utf-8")).hexdigest()[:16]
    return (f"sha256:{both} of live_step3.py's docstring ({len(text)} characters) + its PREDICTED table ({len(numbers)} "
            f"characters) [the docstring alone: sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}], read at the "
            f"start of this run")


def predicted_numbers(source: Path = Path(__file__)) -> dict:
    """The `PREDICTED` table as the FILE holds it (`ast.literal_eval` of its assignment), read at the start of the run like
    the docstring, so a run is graded against the numbers written before it began."""
    import ast

    for node in ast.parse(source.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "PREDICTED":
            return ast.literal_eval(node.value)
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PREDICTED" for t in node.targets):
            return ast.literal_eval(node.value)
    return {}


def measured_numbers(run: Run) -> dict:
    """What a run measured, for `PREDICTED`: its frames and presses (a launcher arm: the instrument's `real_frames` and
    `ai_presses` / 2, the pad's presses; an in-process arm: the harness's), and every grader measure."""
    out = dict(run.measures)
    counters = (run.verdict or {}).get("counters") or {}
    if run.arm.kind == "launcher" and counters:
        out["frames"] = counters.get("real_frames")
        out["presses"] = (counters.get("ai_presses") or 0) // 2
    elif run.arm.kind == "harness" and run.harness:
        out["frames"] = run.harness.get("frames")
        out["presses"] = run.harness.get("presses")
    return out


def check_predictions(run: Run, predicted: dict) -> None:
    """(the step-3.1 verifier's second round: "A PRE-REGISTERED PREDICTION DID NOT HOLD AND THIS IS NOT SAID ANYWHERE":
    ROUTER's docstring predicted 4 stale targets walked onto, the graded run measured 5, and its check asked only for >= 1)
    Every number this round pre-registers in `PREDICTED` is compared with what the run measured, and the arm FAILS a check
    of its own when one differs: a miss cannot pass unsaid. The summary counts them."""
    want = predicted.get(run.arm.name)
    if not want:
        return
    got = measured_numbers(run)
    for name, value in want.items():
        measured = got.get(name)
        if isinstance(measured, tuple):
            measured = list(measured)
        run.predictions.append((name, value, measured, measured == value))
    missed = [(n, p, m) for n, p, m, ok in run.predictions if not ok]
    run.check(not missed,
              f"PRE-REGISTERED NUMBERS (PREDICTED, written before this run): " + "; ".join(
                  f"{n} {p} {'==' if ok else '!='} {m}" for n, p, m, ok in run.predictions)
              + f" -> {'all held' if not missed else 'NOT HELD: ' + str(missed)}")


def write_evidence(run: Run, code_ref: str, tag: str, predictions: str = "") -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"{time.strftime('%Y-%m-%d')}-{tag}-{run.arm.name}.txt"
    fixture = FIXTURES[run.arm.fixture]
    env = " ".join(f"{k}={v}" for k, v in {ENV_BRAIN: run.arm.brain, ENV_SEED: str(run.arm.run_seed), **run.arm.env}.items())
    if run.arm.kind == "harness":
        env = f"none (a test-side script in its own throwaway emulator, from a COPY of the package; seed {run.arm.run_seed})"
    elif run.arm.kind == "rom":
        env = "none (a test-side scan of the ROM in its own throwaway emulator: no AI runs; the fixture is only where it boots)"
    elif run.arm.kind == "warp":
        env = ("none (a test-side script: the REAL eyes in a throwaway emulator on every start of gates/warp_reads.py STARTS, "
               "every memory read recorded; then the same from three planted COPIES of the package)")
    elif run.arm.kind == "summary":
        env = "none (no run: the graded runs of this session, read again)"
    elif run.arm.kind == "clock":
        env = (f"none (test-side runs of every launcher arm's options in their own throwaway emulators, the cartridge's clock "
               f"pinned at each of {list(CLOCK_INSTANTS)})")
    out = [
        f"AI PLAYER BUILD STEP 3 (THE WORLD MODEL AND THE NAVIGATOR) - LIVE PROOF - ARM {run.arm.name}: {run.arm.title}",
        f"date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"code: {code_ref}",
        f"predictions: {predictions or predictions_ref()}",
        f"fixture: {fixture[0].relative_to(REPO).as_posix()} md5={md5_of(fixture[0])}",
        f"fixture documentation: {run.arm.doc or '-'}",
        f"command: {' '.join(run.command)}",
        f"env: {env}",
        f"exit code: {run.exit_code}   elapsed: {run.elapsed:.1f}s   run dir: {run.run_dir}",
        f"VERDICT: {'PASS' if run.passed else 'FAIL'}",
        SELFTEST_LINE,
        "checks (pre-registered in ai_player/gates/live_step3.py's docstring; each quotes both values):",
        *[f"  [{'PASS' if ok else 'FAIL'}] {text}" for ok, text in run.checks],
        f"PRE-REGISTERED NUMBERS (live_step3.py PREDICTED, machine-checked): "
        + ("; ".join(f"{n} predicted {p}, measured {m} -> {'held' if ok else 'NOT HELD'}" for n, p, m, ok in run.predictions)
           if run.predictions else "none registered for this arm"),
        f"MEASURED (every number PREDICTED may register): {json.dumps(measured_numbers(run), sort_keys=True, ensure_ascii=False)}",
    ]
    if run.notes:
        out += ["", "---- notes ----", *run.notes]
    if run.verdict is not None:
        out += ["", "---- the instrument's verdict file (purity.json) ----", json.dumps(run.verdict, indent=2, sort_keys=True)]
    if run.before is not None:
        out += ["", "---- TRUTH of the fixture BEFORE the run (gates/hands_harness.py truth) ----", json.dumps(run.before, sort_keys=True, ensure_ascii=False)]
    if run.after is not None:
        out += ["", "---- TRUTH of the state the run LEFT (gates/hands_harness.py truth) ----", json.dumps(run.after, sort_keys=True, ensure_ascii=False)]
    if run.answer is not None:
        out += ["", "---- THE GAME'S ANSWER for save block 1's claim, by its behaviour from the state left (gates/game_answer.py) ----",
                json.dumps(run.answer, sort_keys=True, ensure_ascii=False)]
    if run.answer_fault is not None:
        out += ["", "---- its FAULT-TEST: the same probe claiming the first neighbouring tile it rules out (must disagree) ----",
                json.dumps(run.answer_fault, sort_keys=True, ensure_ascii=False)]
    if run.harness is not None and run.arm.kind == "rom":
        out += ["", "---- the scan (gates/exit_looks.py) ----", json.dumps(run.harness, ensure_ascii=False, sort_keys=True)]
    elif run.harness is not None and run.arm.kind == "clock":
        out += ["", "---- the runs (gates/hands_harness.py --game-clock): arm, instant, frames, presses, outcome ----",
                *[f"  {r.get('arm')} {r.get('when')}: {r.get('frames')} frames, {r.get('presses')} presses, {r.get('reason') or r.get('error')}"
                  for r in run.harness.get("rows") or []]]
    elif run.harness is not None and run.arm.kind == "warp":
        out += ["", "---- the scan (gates/warp_reads.py): the real package, then each plant ----",
                json.dumps(run.harness.get("real"), ensure_ascii=False, sort_keys=True),
                *[f"PLANT {name}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}"
                  for name, value in (run.harness.get("plants") or {}).items()],
                f"STATIC (every host file): {json.dumps(run.harness.get('static_real'), ensure_ascii=False)}"]
    elif run.harness is not None:
        harness = {k: run.harness.get(k) for k in ("brain", "seed", "reason", "frames", "presses", "seconds")}
        out += ["", "---- the run, in-process from a COPY of the package (gates/hands_harness.py) ----", json.dumps(harness, ensure_ascii=False),
                "the brain's lines:", *[f"  {line[:400]}" for line in run.harness.get("lines") or []],
                "TRUTH at the end:", json.dumps(run.harness.get("truth"), ensure_ascii=False, sort_keys=True)]
    if run.world is not None:
        world = WorldMemory.from_dict(run.world)
        n = world.names()
        out += ["", "---- the AI's memory at the end (world.jsonl, its last snapshot): maps, links, bumps ----"]
        for key, memory in world.maps.items():
            out.append(f"  {key} {memory.const}: {len(memory.tiles)} tiles known, {len(memory.visits)} stood on, bumped "
                       f"{sorted(memory.bumped)}, edges {memory.edges}, arrivals {memory.arrivals}")
        for name, link in sorted(world.warps.items()):
            out.append(f"  warp {name} ({n.get(name.split('|')[0])}) -> {n.get(link.get('to'))} {link}")
        for connection in world.connections:
            out.append(f"  connection {connection}")
    if run.records:
        out += ["", f"---- the action log: {len(run.records)} records (frame | decision | action | gate or reason | digest) ----"]
        for r in run.records:
            if r.get("decision") in ("start", "end"):
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {r.get('reason')} | {r.get('digest')}")
            else:
                extra = r.get("extra") or {}
                brief = {k: extra[k] for k in ("target", "kind", "player", "in_window", "seen_from", "map", "hold") if k in extra}
                out.append(f"f{r.get('frame')} | {r.get('decision')} | {r.get('action')} | {str(r.get('reason'))[:200]} | "
                           f"{(r.get('digest') or '')[:200]} {json.dumps(brief) if brief else ''}")
    if run.stdout:
        keep = [line for line in run.stdout.splitlines() if line.startswith(("[AI-", "[DRIVER]"))]
        out += ["", "---- evidence lines from stdout ([AI-*]) ----", *[line[:500] for line in keep]]
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def leftover_processes() -> list[str]:
    try:
        import psutil
    except ImportError:
        return []
    found = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except Exception:  # noqa: BLE001
            continue
        if (("pokebot.py" in cmd and PROFILE in cmd) or ("hands_harness.py" in cmd and "ai_step3_" in cmd) or "game_answer.py" in cmd
                or "exit_looks.py" in cmd or "warp_reads.py" in cmd):
            found.append(f"pid {proc.info['pid']}: {cmd[:160]}")
    return found


def main() -> int:
    global SEED, SELFTEST_LINE
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Live proof of AI-player build step 3 (the world model and the navigator).")
    parser.add_argument("--arms", default=",".join(a.name for a in ARMS))
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--evidence-tag", default=None)
    args = parser.parse_args()
    SEED = args.seed
    tag = args.evidence_tag or (EVIDENCE_TAG if SEED == 3 else f"{EVIDENCE_TAG}-seed{SEED}")
    broken = selftest_after_check()
    SELFTEST_LINE = (f"[SELFTEST] check_after_is_this_run on 5 synthetic runs (its own: pass; a stale mtime, a frame +3000, no file, "
                     f"the fixture's md5: fail): {'PASS' if not broken else 'FAIL ' + str(broken)}")
    print(SELFTEST_LINE)
    if broken:
        return 2
    wanted = [name.strip() for name in args.arms.split(",") if name.strip()]
    unknown = [name for name in wanted if name not in GRADERS and name not in PAIRED and name not in SUMMARIES]
    if unknown:
        print(f"unknown arms: {unknown}")
        return 2
    for name, (path, md5) in FIXTURES.items():
        actual = md5_of(path) if path.is_file() else "MISSING"
        if actual != md5:
            print(f"ABORT: fixture {name} has md5 {actual}, pinned {md5}")
            return 2
    build_root = launcher.resolve_build_root()
    code_ref = tree_provenance(REPO)
    predictions = predictions_ref()
    predicted = predicted_numbers()  # read from the FILE at the start of the run, as the docstring is
    print(f"predictions: {predictions}")
    results: list[Run] = []
    done: dict[str, Run] = {}
    for arm in [a for a in ARMS if a.name in wanted]:
        print(f"\n=== ARM {arm.name}: {arm.title} ===", flush=True)
        if arm.kind == "harness":
            run = run_harness_arm(arm)
        elif arm.kind in ("rom", "warp"):
            run = run_rom_arm(arm)
        elif arm.kind == "clock":
            run = run_clock_arm(arm)
        elif arm.kind == "summary":
            run = Run(arm, exit_code=0)
        else:
            run = run_arm(arm, build_root)
        if arm.name in SUMMARIES:
            SUMMARIES[arm.name](run, done)
        elif arm.name in PAIRED:
            grader, partner = PAIRED[arm.name]
            grader(run, done.get(partner))
        else:
            GRADERS[arm.name](run)
        check_predictions(run, predicted)
        done[arm.name] = run
        evidence = write_evidence(run, code_ref, tag, predictions)
        results.append(run)
        print(f"ARM {arm.name}: {'PASS' if run.passed else 'FAIL'}  (exit {run.exit_code}, {run.elapsed:.1f}s) -> {evidence.relative_to(REPO)}")
        for ok, text in run.checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {text[:400]}")
    leftovers = leftover_processes()
    print("\n=== SUMMARY ===")
    for run in results:
        print(f"  ARM {run.arm.name:<6} {'PASS' if run.passed else 'FAIL'}  {run.arm.title}")
    held = [p for run in results for p in run.predictions if p[3]]
    missed = [(run.arm.name, p[0], p[1], p[2]) for run in results for p in run.predictions if not p[3]]
    print(f"  PRE-REGISTERED NUMBERS (PREDICTED, machine-checked): {len(held)} of {len(held) + len(missed)} held; "
          f"NOT held: {missed or 'none'}")
    print(f"  leftover emulator processes: {leftovers or 'none'}")
    ok = all(run.passed for run in results) and not leftovers
    print(f"OVERALL: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
