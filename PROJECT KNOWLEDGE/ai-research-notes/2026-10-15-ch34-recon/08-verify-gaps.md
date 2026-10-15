# 08 — ADVERSARIAL verification of the code-gap claims (00 §6 and §9, and 03)

**Status: a NOTE, not truth.** Written 2026-10-15 by a read-only Claude verifier subagent whose job was to FIND ERRORS in
`00-RECON-NOTE.md` §6 (the gaps) and §9 (the draft pre-registration) and in `03-our-code-gaps.md`. Nothing was run in the
emulator. Code was read on the 2026-10-15 working copy (step 5.1 uncommitted; a regression was running, nothing under
`ai_player/` was touched). Decomp files were fetched from pret/pokeemerald master with `gh api` into the session scratchpad.

Tags: **VERIFIED-code** (read in our tree, `file:line`), **VERIFIED-decomp** (read in pret, file:line or JSON key),
**MODEL** (taken from 05's static map model, not re-derived here), **UNVERIFIED** (inference or estimate).

⛔ **Person-fair (USER RULINGS 35-37).** Every coordinate, flag, route and sight line below is for the DEVELOPERS (proof
design, fixtures, fault arms). None of it may reach the AI as a hint. Where a fix needs knowledge, the source named is
something on screen or in the game's own words.

---

## 0. Verdicts in one table

| Claim (00 §6 / 03 §0) | Verdict | One-line reason |
|---|---|---|
| Gap 1: Route 104 halves; woods treated as an interior | **REAL, and UNDER-STATED** | It also fires BEFORE the scene, on any decision made inside the woods (§1.1). The proposed fix 1 does not cover the first crossing (§1.2) |
| Gap 2: ROXANNE can end the run | **PARTLY REAL; MIS-STATED; the worst mechanism is MISSED** | Losses are per RUN, not chapters 1-4. Training does continue after a loss while the party is short. But two failed training goals make the AI challenge her untrained (§2) |
| Gap 3: the first live evolution | **REAL as a TEST gap; the proposed fix is ALREADY the code** | The hands press only A. The residual risk is the stall detector and the evolution yes/no, never played live (§3) |
| Gap 4: "done" while a box is still up | **NOT REAL for chapter 4** | The badge comes inside a `talk` goal, which plays to a free screen before the loop checks the target (§4) |
| Gap 5: default YES into a party menu | **REAL, and there is a SECOND trap; the likelihood is understated** | WALDA's DAD's YES opens a naming keyboard. The balance rule forces chats (§5) |
| Gap 6: double battles | REAL (untested); rank fine | A two-trainer double records only trainer A's id (§6) |
| Gap 7: frame budgets | REAL as an amplifier | — |
| Gap 9: carry the world memory | REAL; INCOMPLETE | Personality, starter and seed must be pinned too, and the goal manager's memory is not carried (§7) |
| Gap 10: `DEEP_SOUTH_WARP` | Downgrade correct; the residual "sideways step re-enters the woods" is **NOT REAL** for planned walks | Warp tiles are never walkable in a plan (§8) |
| Gap 11: MARC missing | REAL data error, no run effect | ROXANNE is `named`; MARC feeds nothing |
| Gap 13: diagonal ledges | Consistent with the code | Not re-adjudicated |
| 03 gap 9 "(talk to ROXANNE) interrupted by JOSH counts as failed" | **Mostly NOT REAL** | A trainer battle met on the approach is played and the walk goes on (§9) |

Missed gaps that would stop a chapter 3-4 run are in §10, ranked. §11 checks the draft pre-registration against a no-op and
a beeline.

---

## 1. Gap 1: REAL, and worse than both notes say

### 1.1 It fires BEFORE the scene, not only after it (MISSED by 00 and 03)

- The ch3_woods milestone's first step is `go RUSTBORO_CITY` (`ai_player/knowledge/milestones.json:1090-1095`), and a `go`
  step counts as done only when the player stands on its map or a later step's map (`brain/goals.py:947-950`). Its second
  step, `follow`, has no map. So **the whole woods traversal is one `go RUSTBORO_CITY` goal.** VERIFIED-code.
- Any decision made INSIDE the woods runs `_travel` → `lead_toward("RUSTBORO_CITY")` (`goals.py:1608-1615`). The woods do
  not match `OUTDOOR` (`goals.py:432`), so the "look on from here" return is skipped (`:473-475`), and it returns the
  nearest visited outdoor map with `promise > 0` (`:476-485`): ROUTE104, one link away. VERIFIED-code.
- `promise` counts frontier tiles, unused exits and unknown roads (`world/memory.py:517-526`). Route 104 south almost
  surely has some (the SE pocket door, the cottage and the flower shop doors, the sea's edge). UNVERIFIED per seed, but
  it would have to be 0 on EVERY visited outdoor map for `lead_toward` to return None.
- In the woods the way back south is a `route` target worth `ROUTE_VALUE` 10 x `VALUE_TILES` 10 = 100 points
  (`brain/explore.py:155`, `:288-289`). The north exit, even if seen, is a `door` worth 0.8 x 10 = 8
  (`:150`, `:290-291`). VERIFIED-code: it walks out SOUTH.
- **What ends a woods walk early and forces a decision inside the woods** (each VERIFIED-code):
  1. **An item ball coming into view** ends any `go` walk (`goals.py:1340-1341`). The PARALYZE HEAL ball is at (4,26)
     (`data/maps/PetalburgWoods/map.json` object_events[11], lines 164-173, VERIFIED-decomp), beside the west grass column
     that the northbound spine climbs (MODEL, 05 §3c). This is the likeliest trigger.
  2. **LYLE.** Once a trainer's battle is seen on the woods map, `seen_levels` gets its level (`goals.py:711-716`), and
     ch3_woods's unnamed fight takes it (`:1059-1061`). Then `fight_next` is true and `train_min_steps` is not met
     (`:863`), so the AI TRAINS in the woods' grass (`_grass_map` stays, `:1633-1634`). The next decision after the
     session is inside the woods.
  3. A catch draw on the woods' grass (`:879-895`), a chat, or a heal.
  4. The `go` budget running out (`GO_FRAMES` 9,000, extended only for battles, `:200`, `:252-253`).
  5. **The scene itself**: the milestone changes, `moved_on` ends the walk (`:1336-1337`), and the next decision is made
     at about (26,23). This one is CERTAIN; it is 03's case.
- **Any whiteout after the woods were entered** sends the player to the last POKéMON CENTER ENTERED: the respawn is set by
  each centre's on-transition script (`data/maps/RustboroCity_PokemonCenter_1F/scripts.inc:6-7`
  `setrespawn HEAL_LOCATION_RUSTBORO_CITY`, VERIFIED-decomp). In chapter 3 that is Petalburg's or Oldale's, south of the
  woods, so the player must re-enter by the SW door, which is refused (next bullets). A loss to the grunt, to LYLE or to a
  wild Pokémon in the woods is therefore a stall.

**Expected result (trajectory UNVERIFIED, mechanism VERIFIED-code):** chapter 3 essentially cannot pass on the current
code. After the scene, it is certain that the next decision is made inside the woods.

### 1.2 Re-entry: stronger than 03 says, and fix 1 misses the first crossing

- 03 §2.1 says the woods are re-entered "only through the explorer's fallback (`goals.py:523-524`), when nothing else is
  left on Route 104 south". **Effectively never.** The fallback runs only when the filtered list is EMPTY. Every road
  tile is a candidate (`explore.py:300-310`), and a road `back` to PETALBURG_CITY (OUTDOOR) passes `keeps_going`
  (`goals.py:498-499`: no `exit`, so True). `not_back_to_seen_all` keeps the backs when nothing else is left
  (`explore.py:366-372`). So the list is never empty while a road exists. VERIFIED-code.
- `route_to` is breadth-first by map (`explore.py:174-203`) and ROUTE104 is one node. Once RUSTBORO is known, the "route"
  from Route 104 south is the north connection, which cannot be walked to from the south half (MODEL). The woods door stays
  `back` and stays refused. VERIFIED-code (the reachability is MODEL).
- **00's fix 1 ("a passage once its memory shows exits to two outdoor places") does NOT fire at the moment that
  matters.** On the first northbound crossing, the woods have exactly ONE known outdoor link: the SW door the AI came in
  by. The north exit is unseen or unused, so the rule cannot yet tell the woods from a house. ⇒ The fix must classify the
  woods as route-like FROM THE FIRST ENTRY, using something a person sees:
  - **the map-name popup.** `OUTDOOR`'s own docstring says it means "a map a person sees the NAME of when they walk onto
    it" (`goals.py:430-431`), and the woods show one: `"show_map_name": true`, `"map_type": "MAP_TYPE_ROUTE"`
    (`data/maps/PetalburgWoods/map.json:9`, `:13`, VERIFIED-decomp). The regex contradicts its own stated rule. The
    signal must be read as the POPUP SEEN on screen, never from the map header (that would be a ROM read, not a sight);
  - or tall grass and wild battles seen on the map. A building has neither.
- ⚠ **Side effect to guard (VERIFIED-code):** widening the regex alone would make the woods a TOWN in the heal logic.
  `town = here_const if OUTDOOR.match(...) and not here_const.startswith("ROUTE")` (`goals.py:780-781`) would then send a
  hurt AI on a 3,000-frame look round the woods for "its" POKéMON CENTER (`:782-794`, `CENTER_LOOK_FRAMES`). The fix must
  separate route-like from town.
- **Fix 2 (region-aware graph) and fix 3 (ties broken by walking distance) stand.** They are needed for every return
  north (heal, whiteout) and for `_grass_map` (§10 M2).

---

## 2. Gap 2: partly real, mis-stated, and the worst mechanism is missed

- **"A loss does not cause more training": MIS-STATED.** The train branch has no `ready` gate (`goals.py:859-869`). After
  a loss, while the strongest Pokémon is under the target and `sessions < TRAIN_SESSIONS`, it trains again. What is REAL:
  a loss raises neither the target nor the session cap, so a party AT its target re-challenges with no extra training.
- **"MAX_LOSSES counts across chapters 1-4" (00 §0.8, §6): MIS-STATED for the chained design.** Chapters are separate
  runs (README `:388-389`; `gates/rate_step5.py:350-358` `run_one(start=...)`). The loss count reads `Navigator.battle_log`
  (`mode.py:559-570`), which is created empty with each run's navigator (`brain/navigator.py:710`). So the cap is 3 per
  CHAPTER RUN. Inside a chapter-4 run, whiteouts while training and ROXANNE losses do still share it. VERIFIED-code.
- **The MISSED mechanism (VERIFIED-code): two failed `train` goals mark the fight READY, and the AI goes to ROXANNE
  untrained.**
  - A failed goal twice in a row puts its key aside (`FAIL_LIMIT` 2, `goals.py:1251-1255`).
  - With `train` put aside, `_allowed("train")` is False, so the code falls to
    `prep["ready"] = True; why_ready = "training put aside for a while"` (`:870-873`).
  - With no catch (`fight_next`, `:879-880`), the next goals are a heal and the story's go/talk to ROXANNE.
  - What makes two train failures likely in chapter 4 is in §10 M2.
- **Ranking.** HIGH stays right in OUTCOME, but for the §10 M2 + §2 chain, not for "3 losses across chapters".
- **Fix 3 of 00 §6 gap 2 is the right one.** "Count a session only if it won a battle or walked its steps" would stop the
  M2 burn. Add: a train goal that failed for want of reachable grass must not set `ready` ("put aside" must not mean
  "ready to fight").

## 3. Gap 3: a real test gap; the proposed fix is already the code

- "Advance evolution text with A only, never hold B" is **already** the behaviour. `skills/battle.py:9` says so, and
  `advance` presses only A, on the eyes' waits (`hands/dialogue.py:174-233`). No B is pressed in a battle's text stretch.
  VERIFIED-code. The `HOLD_B_EVOLVE` fault arm is still useful: it is a fault on an EXISTING property.
- **The residual risks that remain (UNVERIFIED, measure them on an L16 fixture):**
  1. **The stall detector during the animation.** While a scene is named, `advance` returns `stuck:` after 900 frames
     with an unchanged screen (`STALL_FRAMES_SCENE`, `hands/dialogue.py:62-63`, `:125-128`, `:227-231`). EVOLUTION is a
     named scene (`eyes/screens.py:392`). Whether the animation changes `seen_now` within 900 frames is unknown.
  2. The EVOLUTION-state learn-a-move yes/no (`host/eyes.py:527-528`, `:605-611`) and the summary-screen forget list have
     never been played live (`README.md:2027-2028`).
- **"Certain to occur in every chapter-4 run" is too strong.**
  - Catcher and Trainer targets are 17 and 18, so they cross L16 in a TRAINING battle, not in the gym.
  - Under §2's mechanism, a run may reach ROXANNE at L12-14 and never evolve.

## 4. Gap 4: not real for the chapter-4 end

- The badge is set by ROXANNE's post-battle script, which runs inside the `talk` goal. `talk_to` → `play_out` loops
  `nav.handle` until `nav_free` (`skills/story.py:148-159`, `:185-186`; `navigator.py:1001-1019`). Only then does the
  goal return, and only then does the play loop read the marks and end on `index > target` (`mode.py:437-438`). So the
  TM39 text has been read before the run ends. VERIFIED-code.
- `VAR_SCOTT_STATE` is not a milestone mark (no hit in `milestones.json`), so its "set before the dialogue" order cannot
  end anything.
- **Residual (low):** a `talk` that returns "talked; then stuck: …" with a screen still up. The next pass would end
  "done" with that screen up.
- ⇒ 9c PASS #2 ("the screen is free at the end") passes BY CONSTRUCTION on the current code (§11).

## 5. Gap 5: real; a second trap; more likely than stated

- **Trader: VERIFIED-decomp.**
  - `msgbox …, MSGBOX_YESNO` → `special ChoosePartyMon` → `PARTY_NOTHING_CHOSEN` declines
    (`data/maps/RustboroCity_House1/scripts.inc:12-16`).
  - The field party menu reads as `kind="party"` (`eyes/screens.py:520-526`). `_story_menu` knows only
    `choose_starter`, `clock`, `mart_buy` and `mart_menu` (`mode.py:575-583`), so the result is
    `stuck: an unexpected party on screen` (`navigator.py:1014-1017`).
  - The loop then replays it until `STORY_PATIENCE` (`mode.py:451-461`). VERIFIED-code.
- **MISSED second trap: WALDA's DAD**, RUSTBORO Flat1 2F.
  - "Do you know a funny phrase?" is `MSGBOX_YESNO`, and YES leads to `special DoWaldaNamingScreen`
    (`data/maps/RustboroCity_Flat1_2F/scripts.inc:20-24`, `:11-12`, VERIFIED-decomp).
  - The naming keyboard reads as `kind="naming"` (`eyes/screens.py:498-505`), which `_story_menu` does not handle. The
    result is the same stall. UNVERIFIED that the framework's game state is NAMING_SCREEN for Walda's screen.
- **Harmless:** the flower shop's YES only explains berries (`Route104_PrettyPetalFlowerShop/scripts.inc:23-25`). Mr.
  Briney's sail questions are behind `FLAG_HIDE_BRINEYS_HOUSE_MR_BRINEY`, which is set in `new_game.inc:132`
  (VERIFIED-decomp). The school blackboard's `multichoicegrid` (`RustboroCity_PokemonSchool/scripts.inc:13`) is a bg
  event; the AI chats only NPC objects (`goals.py:1108-1110`).
- **The likelihood is UNDERSTATED.** 03 quotes the chat draw (Trainer 0.3, Story 0.18, Catcher 0.12). But when the
  BALANCE is owed, every person within 4 tiles is chatted whatever the draw says (`goals.py:1132-1133`). The balance is
  owed when curiosity falls under `curious_min` (`:669-671`). In chapter 4, training (an errand, but not curiosity)
  dominates, and the catch errand is off (`:879-880`). So forced chats are likely there. VERIFIED-code; the real share is
  UNVERIFIED.
- **Fix:** add NO rules for "trade" and "phrase", keyed on the words on screen. Also let the play brain leave any
  unknown field menu with B. On the party menu, B gives `PARTY_NOTHING_CHOSEN`. On the naming screen, B with an empty
  name is UNVERIFIED as a clean exit.

## 6. Gap 6: doubles (ranking stands), one instrument gap

- The gym overlap is VERIFIED-decomp (sight 3 each, `RustboroCity_Gym/map.json` object_events):
  - TOMMY at (3,9) faces LEFT, so (2,9), (1,9) and (0,9) are in his sight;
  - MARC at (1,6) faces DOWN, so (1,7), (1,8) and (1,9) are in his.

  Line of sight through the tiles is MODEL. ROXANNE is `TRAINER_TYPE_NONE`, sight 0: she is met only by talking to her.
- **Instrument gap (VERIFIED-code):** the observation carries ONE `opponent_trainer_id` (gTrainerBattleOpponent_A;
  `eyes/observation.py:289`). P3's "TOMMY + MARC" therefore cannot be read from the AI's record. Read the battle type
  flags and both trainer flags (0x641, 0x73B) right after the battle.

## 7. Gap 9: carry more than the world memory

- **The goal manager's memory is NOT carried.**
  - A new `GoalManager` is made per run (`mode.py:368-369`); only `landmarks` come from the world memory (`:370`).
  - So these reset at each chained run: `seen_levels`, `fight_prep` (the session count), `talked`, `chat_drawn`,
    `tried_items`, `catch_maps` and `home_heals`.
  - Consequences: chats are re-drawn, an unreachable ball is retried, and the session budget restarts.
- **Pin the personality, starter and seed.**
  - README's chained example (`:389`) omits `AI_PLAYER_PERSONALITY`.
  - Without it, `pick_personality` draws from the seed (`personality.py:83-89`), so the chained run can be a DIFFERENT
    player.
  - The sweep does pin all three (`rate_step5.py:350-358`). §9's "Common rules" should say so.

## 8. Gap 10: the residual ping-pong is not real for planned walks

- A warp or door tile is never `walkable` (`world/memory.py:209-212`), and the planner refuses non-walkable tiles
  (`navigator.py:319-320`). Standing on (10,30) after leaving the woods, no plan steps sideways onto (11,30); the first
  step goes up. Roam steps also choose only walkable tiles. VERIFIED-code.

## 9. 03 §4 row "a talk to ROXANNE interrupted by JOSH counts as failed": mostly not real

- `approach` walks with `nav.go_to` (`skills/story.py:130-131`). Inside `nav.run`, a trainer battle is played by
  `handle`, which returns None on a win (`navigator.py:984-987`), and the walk goes on. The talk counts as interrupted
  only if the walk ENDED in a battle or a scene. VERIFIED-code. (Low either way.)

---

## 10. MISSED gaps, ranked by how likely each is to stop a chapter 3-4 run

| # | Gap | Evidence | Likelihood |
|---|---|---|---|
| M1 | **Gap 1 also fires before the scene and after any whiteout** (§1.1) | `milestones.json:1090-1095`; `goals.py:1340-1341`, `:711-716`, `:863`; `RustboroCity_PokemonCenter_1F/scripts.inc:6-7` | **Very high**: chapter 3 cannot pass on the current code. P5 alone does not cover it |
| M2 | **Chapter-4 training can fail on Route 104 north, and two failures make the AI fight ROXANNE untrained.** (a) `_grass_map` stays on any map whose memory holds grass (`goals.py:1633-1634`), else ties to ROUTE104 by name (`:1639-1640`). (b) Route 104's memory is ONE map; the north half's only grass is the NW pocket, off the walking line (MODEL, 05 §2b). (c) `roam_train` paths only to SEEN, reachable grass (`skills/roam_train.py:209-211`) and returns "no seen grass can be reached". (d) That session is still COUNTED (`goals.py:1474-1477`) and the goal FAILS (`:1481`). (e) Two failures put `train` aside, which sets `ready` (§2, `:870-873`). Then the heal before the fight routes to Petalburg (03's `_nearest_place` tie), and a loss respawns at the last centre ENTERED | code VERIFIED; whether the AI saw the NW pocket is UNVERIFIED (seed-dependent) | **High** |
| M3 | **Whiteout respawn = last centre ENTERED.** If Rustboro's centre was never entered, every chapter-4 loss lands south of the woods, which is gap 1 again | `RustboroCity_PokemonCenter_1F/scripts.inc:6-7` | Medium-high (amplifies M2 and gap 2) |
| M4 | **WALDA's DAD naming keyboard** (§5) | `RustboroCity_Flat1_2F/scripts.inc:11-24` | Medium (needs the 2F and a chat; the balance forces chats) |
| M5 | **Evolution animation versus the 900-frame stall detector** (§3) | `hands/dialogue.py:62-63`, `:227-231` | Unknown: measure on an L16 fixture |
| M6 | **Fix-1 side effect: the woods as a "town"** (§1.2) | `goals.py:780-794` | Certain IF the regex is simply widened |
| M7 | **One goal key across three milestones.** `go:RUSTBORO_CITY` is the key of ch3_route104, ch3_woods and ch3_rustboro (`goals.py:997-998`), so failures and cooldowns from ch3_woods carry into ch3_rustboro (`:1240-1255`) | VERIFIED-code | Low (costs a breather) |
| M8 | **Drift moves the target mid-chapter.** `training_target` uses the ACTIVE personality's margin (`goals.py:1064-1067`). With a draw every 400 steps at 25 % for 250-700 steps (`personality.py:164-169`), a long chapter 4 drifts 1-3 times (UNVERIFIED estimate). A Trainer drifting into the Story is judged "trained" at 16, not 18. `prep["judged_by"]` records who judged (`goals.py:876`). The heal threshold (0.45-0.6) and the explorer's taste also change | VERIFIED-code | Not a stopper; it is a grading trap (§11) |
| M9 | **Chained-run attrition.** A chapter-4 graded run starts from a chapter-3 end, which starts from chapters 1-2. With gap 1 unfixed, close to zero chapter-4 starts exist | `rate_step5.py:389-401` (CH1→CH2 chain only today) | Certain for the proof's sample size |

**Checked and not a new stopper:**
- Ledges: cardinal ledges are planned one-way (`navigator.py:311-318`); diagonal ones are walls.
- Blocking NPCs: only the Devon stair guard, which costs time.
- Patience: `STORY_PATIENCE` 120,000 since real progress, with `HEAL_RESETS_MAX` 3 per milestone. All of chapter 4 is ONE
  milestone, so after three heals only won training battles, levels, new maps, catches and items reset it
  (`mode.py:102`, `:108`, `:512-556`). That is correct behaviour for M2's stall.
- Cooldowns: `FAIL_LIMIT` 2, `COOLDOWN_DECISIONS` 12, `STORY_ASIDE_FRAMES` 6,000 and `DANGER_RETRIES` 3 are all bounded.
- The play loop's end conditions: target passed (`mode.py:437-438`), patience (`:451-454`), `MAX_LOSSES` per run
  (`:412-414`), 50 still passes (`:405-407`), 100,000 passes (`:509`), the intro again (`:442`), and the launcher's frame
  and wall budgets. A chapter-3 run (target ch3_rustboro, index 17) ends on the arrival that sets
  `FLAG_VISITED_RUSTBORO_CITY`.

---

## 11. The draft pre-registration (00 §9): would a no-op or a beeline pass?

**Headline: a BEELINE passes both chapter proofs outright.**
- Every human-likeness item is REPORTED with no floor: gifts, items, catches, training levels and hints heard (9b, 9c).
- There is no beeline arm (`errands_off`, `goals.py:580-581`) and no NOTRAIN arm (`train_off`) for chapter 3 or 4.
- The step-5.1 precedent graded these against controls: "OFF THE BEELINE", "CURIOSITY … the beeline 0.0", NOTRAIN
  (`README.md:1026`).
- §9's own common rule says "every metric must FAIL its control arm", but no metric is defined that could.
- ⇒ As drafted, the proofs show REACHABILITY only. Add CH3_OFF/CH4_OFF and CH4_NOTRAIN arms, each with a separation bound
  set from development seeds, or retitle the claim.

**Check by check:**

| Item | Problem | Fix |
|---|---|---|
| 9b.1 SCOTT == 1 | The premise does not require `VAR_SCOTT_PETALBURG_ENCOUNTER == 0` at the start. The trigger is on var 0 alone at (4,10..13) (`PetalburgCity/map.json` coord_events, VERIFIED-decomp), so a chapter-2 look round Petalburg's west edge may have fired it already. The check is then VACUOUS | Add it to the premise conjunct |
| 9b.2 "two independent witnesses" | **Not independent.** One script run sets both: `removeobject LOCALID_PETALBURG_WOODS_GRUNT` (`PetalburgWoods/scripts.inc:70`) sets that object's template flag `FLAG_HIDE_PETALBURG_WOODS_AQUA_GRUNT` (`map.json:55`; `src/event_object_movement.c:1389-1397` FlagSet), and `:92` sets the var. They agree by construction | Call it one witness. The independent one is the trainer flag 0x50A (9b.3) |
| 9b.3 / 9c.3 "the AI's battle log shows trainer id …" | `Navigator.battle_log` holds (frame, kind, outcome) only (`navigator.py:710`, `:974`). The id is only in the observations (`observation.py:289`, digest `:419-420`) | Join by frame, or log the id. As written the check cannot be implemented |
| 9b.5 / 9c.2 "screen free at the end" | A no-op passes it (nothing on screen). On the current code 9c.2 passes by construction (§4) | Keep it as a guard, never as evidence. Gap 4 needs its own fault arm (end the run inside the talk) |
| P1 woods choke | (a) "Is the scene forced?" is a CORRECTNESS question about the game: an instrument for a driver, not the AI's walk (CLAUDE.md rule 9). (b) A run that never reaches the N exit satisfies "var 1 before the N exit" vacuously. (c) On the current code, gap 1 (M1) can turn the AI back before either event | Use a driver that tries the best path with (26,23)/(27,23) walled, plus a reach floor |
| P5 gap-1 A/B | **Fixture vacuity.** With an empty or bot-save world memory, no visited outdoor map has promise, so `lead_toward` returns None (`goals.py:476-485`). Arm A then walks NORTH too, and a true gap reads as refuted | The fixture's `world.jsonl` must hold ROUTE104 visited with promise > 0 and the SW-door link. COMPUTE `lead_toward` on it before the run. Add a PRE-scene fixture (M1) |
| WOODS_INTERIOR reach "the scene var reached 1 in ≥ 0.6" | Under the reverted code, M1 sends many runs back south BEFORE the scene, so the reach floor fails and the arm is ungradable by design | Start the fault arm from P5's in-woods fixture, or set the reach to "entered the woods" |
| ROXANNE_LOSS ("an L15 Torchic loses") | With the Story target 16 (`goals.py:1067`), the CURRENT code already trains after that loss: L15 is short (`:863-869`). The arm passes unfixed and discriminates nothing | Use a fixture whose strongest is AT or ABOVE the active target, or whose sessions are spent, and compute both arms first. "A third loss must not end a gym it could win" is not measurable as written |
| TRADE_YES | Its reach depends on a chat draw | Force the talk in a driver. The arms differ: the current code stalls until patience; the fixed code is free within N |
| HOLD_B_EVOLVE reach "crossed L16, floor 0.6" | Under M2 a run may never reach L16 | Measure the reach on development seeds |
| "against the personality's target" (9c REPORTED) | Base or active? (M8) | Use `prep["judged_by"]` (`goals.py:876`), the lesson the sweep already paid for (`rate_step5.py:418-422`) |
| P3 two-trainer double | It needs both ids (§6) | Read 0x641 and 0x73B and the battle type flags |
| Chained start (9b, 9c) | Attrition (M9). Pinning (§7) | Pre-register the minimum N, and a fixed-fixture fallback labelled "one trajectory, replayed" |

---

*Sources read (read-only). Ours: `ai_player/brain/goals.py`, `brain/explore.py`, `brain/navigator.py` (excerpts),
`mode.py:80-600`, `skills/story.py`, `skills/battle.py:1-330`, `skills/roam_train.py` (excerpts), `hands/dialogue.py:120-270`,
`world/memory.py` (excerpts), `eyes/screens.py` (excerpts), `personality.py:83-235`, `knowledge/milestones.json`,
`README.md` (excerpts), `gates/rate_step5.py` (excerpts). pret/pokeemerald master (2026-10-15):
`data/maps/{PetalburgWoods,Route104,RustboroCity_Gym,PetalburgCity,Route104_MrBrineysHouse}/map.json`, the
`scripts.inc` of PetalburgCity, PetalburgWoods, Route104(+ flower shop, Briney), Route116, RustboroCity and its interiors,
`data/scripts/new_game.inc`, `src/event_object_movement.c`. Scratch copies are in this session's scratchpad (`v08/`), not
committed.*
