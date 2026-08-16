# Punch List — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue.
> Item format: `- [ ] #N — description` (N never gets reused; check items
> off with `[x]` and move them to Done with the completion date).
> Full future-idea catalog: `09-FEATURE-BRAINSTORM.md`.
>
> ⛔ **A SANDBOX↔CUSTOM DRIFT FIGURE QUOTED INSIDE AN ITEM IS A DATED CLAIM ABOUT THAT ITEM'S
> FILES, NEVER THE REPO'S CURRENT NUMBER.** Several items quote one, each true on its own
> promotion date. **The only authority is `promote.py --check`**, and `04-HANDOFF.md`'s STATE row
> names the currently expected set. Added 2026-08-14 after a `#24-roster` line claimed the KI-63
> wiring was "NOT promoted" for hours after it was — the same failure in the other direction.
> ‼ Note the phrasing here is deliberate: `audit_doc_consistency.py` matches the literal figure
> and **cannot tell a quotation from a claim**, so naming it even as a warning turns this line red.

## ‼ TRIAGE INDEX (2026-08-10) — read this before scanning 100+ entries

**The problem this solves:** the list carried **117 open/partial entries**, and a scan could not
distinguish "being worked on today" from a roadmap line written three weeks ago. Two entries were
found stale-open for **8 days** while their code had shipped, and one contradicts the handoff.
Nothing below was deleted — items are closed only with evidence, and conflicts are flagged for the
user rather than resolved unilaterally.

### 1. ACTIVE — the only things being worked on now
| item | state |
|---|---|
| `#24-battleitems` | ✅ **DONE & PROMOTED 2026-08-10.** Built, unit-proven (27 checks), live, self-correcting; validation batch `20260810-082509` passed (flips 20 → 2, both-failed 10 → 0). ‼ Outcome unproven — grade any follow-up on BATTLE-level metrics. |
| `#24-teachmsgstall` | ‼‼ **REOPENED 2026-08-11 by batch `20260811-130454`. The fix has NO production effect**: success 38/47 (80.9%) vs 38/42 (90.5%) pre-fix, **z = −1.28 NOT resolvable**; `post_select=exhausted` 8/85 vs 3/80, **z = +1.46 NOT resolvable**; and the new `already-advanced` exit fired **ZERO** times in 85 teaches. The one-frame window was real and decomp-confirmed, but it was **not the dominant production cause** — there is another path to `exhausted`. The fix stays (it closes a real hole and costs nothing). Original entry: **ROOT-CAUSED, FIXED, A/B-PROVEN.** The replace-prompt detector had a **ONE-FRAME window**: `Task_ReplaceMoveYesNo` swaps itself out for `Task_HandleReplaceMoveYesNoInput` on the frame it becomes answerable (decomp `src/party_menu.c`; measured f3232735 → f3232736). Missing it left a blind A-mash that reaches `Task_HandleStopLearningMoveYesNoInput`, where **A = give up**. Fixed by watching both spellings, an `already-advanced` exit, and B at the stop prompt. **A/B (same save, one env var): OLD `learned=False` / NEW `learned=True`.** ✅ **PROMOTED 2026-08-11 (user-approved), verified DRIVEN in `custom-pokebot` as the same A/B, frame-for-frame identical. Source drift: ZERO.** |
| `#24-grounditems` | 🟡 **PARTLY DONE 2026-08-12.** The shared helper **`collect_item_ball(map, ball_tile, approach, facing, flag, item_name)` is BUILT** and has two callers (the Magma Hideout Escape Rope, refactored onto it, and the Aqua Hideout Master Ball + Nugget) — the duplication this item existed to prevent never happened. `repro_hideout_exit.py` now checks the escape-rope path DELEGATES to it, so a future edit cannot quietly fork a second copy. ‼ Lessons baked in: grade on a **bag delta** (a FULL pocket makes `finditem` set no flag AND give no item, so a flag test hangs forever); an item ball is an OBJECT you stand beside, and not every neighbour is reachable; **the ball VANISHES when taken, freeing its tile** (that is how the Master Ball is reached at all). **WHAT REMAINS:** per-area sweep LISTS so chapters collect the balls they walk past. Known uncollected in already-built content: Aqua Hideout **Max Elixir** `B1F (29,12)` (all four approaches reachable from node `(27,12)`) and **Nest Ball** `B2F (3,13)`; Magma Hideout **Rare Candy** `1F (3,20)`. |
| `#24-npcgifts` | ‼ **NEW 2026-08-12 (user directive).** **Collect GIFT ITEMS from NPCs** — items a person hands you, which the bot currently walks straight past. Decomp-anchored starters: **EXP SHARE** — `RustboroCity_DevonCorp_3F_EventScript_MrStone`, gated on `FLAG_DELIVERED_STEVEN_LETTER`, sets `FLAG_RECEIVED_EXP_SHARE` (272); **QUICK CLAW** — `RustboroCity_PokemonSchool_EventScript_Teacher`, sets `FLAG_RECEIVED_QUICK_CLAW` (275). Both flag names verified present in `modules/data/event_flags/emerald.txt`. Shape: navigate to the NPC, face, A-ride the dialogue, grade on **the bag** (both scripts branch to `Common_EventScript_ShowBagIsFull`, which gives nothing and sets no flag). ‼ These are ORDINARY-PLAY value, not story-critical: an Exp Share collected in Rustboro compounds over every later chapter, which is exactly the organic-play goal. **Enumerate the full gift list from the decomp before building** — `giveitem` in `data/maps/*/scripts.inc` — rather than adding them one at a time. |
| `#24-masterball` | ✅ **DONE 2026-08-12 — the MASTER BALL is collected, driven PASS.** `master_balls=1 nuggets=1 escaped=True whiteouts=0`, and the driver's acceptance now REQUIRES it (read from the BAG, since a full pocket makes `finditem` set no flag and give no item). ‼ It cannot be taken directly: both of its free neighbours are unreachable, so the route takes the **Nugget** at `(15,10)` first and steps onto the tile the vanished ball frees. No Electrode is ever faced. ‼ The return leg had to be re-derived after a driven failure — the first one walked across a warp panel; `can_walk` in `probe_aqua_hideout_graph.py` is now panel-aware. |
| `#24-impassabledirs` | ✅ **DONE 2026-08-13 — FIXED, BOTH HALVES, A/B PROVEN, AND GATED.** `modules/map_path.py`: the entry vector now starts all-True and CLEARS `[opposite(D)]`, and a NEW `PathTile.blocked_exit_directions` carries the decomp's *exit* rule, checked on the SOURCE tile in the A* expansion loop (`is_tile_accessible` is handed the NEIGHBOUR and structurally cannot express it). **THE A/B, on `VICTORY_ROAD_1F`:** before → `repro_impassable_dirs.py` exits **1** with **29/29** live tiles reading `[--S-]` against a correct `[NE-W]`, and `calculate_path` returns **NO-PATH from every single direction** — all 29 walkable tiles were **completely invisible to the planner**; after → exits **0**, 0/29 mismatches, and the legal approaches return `OK len=1`. **COLLATERAL CONTROL:** the `MOSSDEEP_CITY` block of `probe_ki59_routing_ab.py` (a map with zero such tiles) is **byte-identical across both arms** — the two arms were produced with real production code via `git stash`, not by re-implementation. **NEGATIVE CONTROL:** `SEAFLOOR_CAVERN_ROOM1` reports **0 live tiles and 0 mismatches in both arms**, confirming from production objects that the branch is inert there. **New gate `repro_impassable_dirs.py` is in `run_gates.py` (suite reached 17 with it — 18 since `audit_doc_consistency.py`, 2026-08-14 — all PASS, 124.3s).** ‼ **`probe_shoal_tide.py` corrected IN LOCKSTEP** (it replicated the inversion, so it agreed with production while both were wrong) — and its headline numbers **re-derived on the fixed model are UNCHANGED: LOW 278 / HIGH 0, all controls PASS**, so the user-delegated **"Shoal Cave is NOT adopted"** ruling stands and now rests on a correct model. ✅ **PROMOTED 2026-08-14, user-approved — sandbox↔custom drift is back to ZERO** (it had reached 5: `map_path.py`, `early_game.py`, `story_mode.py`, plus `counter_hunt.py` and `pokemon_party.py` on 2026-08-14). Verified by DRIVING, not diffing: `--driver ch20dive --build custom` → `ACCEPTANCE: PASS`, `repro_box_counter_move_test.py --build custom` exit 0, drift re-measured 0 both directions. Restore point `restore/2026-08-14-pre-promotion-5files`. History and the measurement that reprioritised this item follow. ‼ **MEASURED 2026-08-13 — the INVERSION IS REAL but the TARGET MAP IN THE OLD TEXT WAS WRONG.** `tools/story-dev/probe_impassable_dirs.py` (NEW) swept **all 518 maps**. **The bug is REAL:** `map_path.py:128-132` starts `accessible_from_direction` all-False and **sets** `[opposite]` True, where ground truth is start all-True and **clear** `[opposite]`. For `Impassable North` the shipped model is `[--S-]` — the *exact complement* of correct `[NE-W]` — so it refuses the three legal entries **and permits the one illegal one**. ⛔ **BUT: `map_path.py:118` is `if tile.collision != 0:` and the `Impassable` handler is its `elif`, so a collision≠0 tile NEVER REACHES IT.** Measured: **2,658 such tiles game-wide, 2,257 DORMANT (collision≠0), only 401 (15.1%) LIVE.** ‼‼ **ZERO of the Seafloor Cavern's 115 are live** (all `collision=1`) — so the old instruction "A/B on `SEAFLOOR_CAVERN_ROOM1` before the cavern chapter exists" **would have measured nothing**, and this is **NOT a §Ch20 prerequisite**. **Where it IS live:** SHOAL_CAVE inner 77 + entrance 12 + high-tide 9; **DESERT_RUINS 48 / ISLAND_CAVE 48 / ANCIENT_TOMB 48 (the REGI arc — the user's ask, 144 tiles)**; LILYCOVE contest hall 40 + lobby 8; ARTISAN_CAVE_B1F 34; VICTORY_ROAD 1F/B2F/B1F 58; MIRAGE_TOWER_4F 5; GRANITE_CAVE_B2F 4; a tail of 1-3. Live strings: `North` 347, `East` 27, `West` 24, `North and South` 3. ✅ **THE FIX IS SPECIFIED AND DE-RISKED** (decomp-verified `gOppositeDirectionBlockedMetatileFuncs` / `gDirectionBlockedMetatileFuncs`, `event_object_movement.c:893-905, 4715-4722`): `MB_IMPASSABLE_<D>` means **"the tile's `<D>` EDGE is a wall"**, blocking entry *and* exit across it. ⇒ (a) `accessible_from_direction = [True]*4` then clear `[opposite(D)]`; (b) **a NEW exit-blocking concept is required** — `PathTile` cannot express "may not LEAVE in direction D" at all, and without it the fix still lets the planner walk north off a wall (22 of Island Cave's 48 live tiles have open floor to their north). ✅ **Hazards pre-checked, all clear:** the four `_is_optional_blocker` salt tiles are plain `Cave`, not Impassable (so the fix cannot defeat the salt gates); `Secret Base Breakable Door` (0xBE, a directional impassable the code misses) and `Secret Base Impassable` (0xB9, a false friend that must stay OUT) both occur **0 times** in this ROM. ‼ **`tools/story-dev/probe_shoal_tide.py:364-367` REPLICATES the inversion** and must change in lockstep — see the note under `#24-shoalcave`/KI-54. **Per-string split (live/total), which BOUNDS the fix:** `North` **347**/2601 · `East` **27**/27 (all live) · `West` **24**/24 (all live) · `North and South` **3**/3 (all live) · `South` **0**/3 (all dormant). **Five of the ten producible strings never occur in this ROM at all.** ⚠ **THESE ARE STATIC ROM LAYOUTS, NOT RUNTIME TRUTH.** Three of the four biggest live maps rewrite themselves: `setmetatile` appears in `DesertRuins`, `IslandCave`, `AncientTomb` (those ARE the braille walls opening), `ShoalCave_LowTideInnerRoom` and `LilycoveCity_ContestLobby`; `setmaplayoutindex` in both Shoal Cave low-tide rooms. So 77/48/48/48 describe the **compiled** layout, not what is on screen. ‼ **The Seafloor conclusion is UNAFFECTED — no `SEAFLOOR_CAVERN_ROOM*` script uses either command** (checked across the full result set). **REMAINS: the fix itself + an A/B.** ⇒ **RUN IT ON `VICTORY_ROAD_1F` (29 live tiles)** — it is the cleanest target because it does NOT rewrite itself, unlike Island Cave / Shoal Cave. **With a NEGATIVE control on a Seafloor room proving the branch is inert there**, and the A/B must assert **both** directions (entry AND exit), never on the Seafloor Cavern alone. |
| `#24-pathsourcecheck` | ‼ **NEW 2026-08-12 (KI-60), code-verified.** `calculate_path` never runs its SOURCE tile through `is_tile_accessible` — it seeds the queue unconditionally. So a path requested *out of solid rock* returns OK (this produced the wrong "different components" story in KI-57's first write-up), and an invalid source reports a bare "could not find a path" instead of naming itself. Low-risk fix = raise a distinct error on an inaccessible source, but it is shared code and needs its own A/B. |
| `#24-mossdeepgym` | ✅ **DONE 2026-08-12 — §Ch18 runs END TO END and is WIRED into the ladder (Segment 18).** `--driver mossdeepbadge` gives `badge=True map=MOSSDEEP_CITY_GYM at=(23,8) controllable=True whiteouts=0`; `BADGE07_GET` set after 754 frames; anchor `saves/post_mossdeep_gym.ss1`. The ladder reached **19/24** with this item (current: **20 of 24 beats**, since §Ch19). ‼ An adversarial review then found a defect the PASS could not have caught (the whiteout path checked the map only at entry, and raised `RuntimeError` where the chapter catches `BotModeError`, so the recovery could never fire) — fixed and proven by `repro_gym_whiteout_guard.py`, which INJECTS the fault. History below. ✅ Leg 1 driven PASS (`--driver mossdeeptravel`, `whiteouts=0`, anchor `in_mossdeep_gym.ss1`). ✅ **KI-58 resolved:** the gym is a **ROTATING-TILE STATUE PUZZLE** — nine floor switches call `moverotatingtileobjects`, shifting every object on a matching coloured arrow one tile. ✅ **NEW 2026-08-12: `modules/story/mossdeep_gym_puzzle.py` simulates it, and `probe_gym_simulate.py` PASSES** — 11/11 loaded objects predicted on a live press, identity-keyed on `local_id`, plus a period-4 identity control on all five colours. Encoding derived from the ROM dump: band = `(mt-0x250)//8` (`0 Yellow 1 Blue 2 Green 3 Purple 4 Red`), code = `(mt-0x250)%8` (`0 Right 1 Down 2 Left 3 Up`), **codes 4/5 = that colour's switch**. ‼ Movement is a **rigid simultaneous rotation with NO occupancy check**; **nine TRAINERS rotate too**; statues are `graphics_id == 224`. ‼ **"5 counters mod 4" is unsafe** — use the full object-position tuple. ‼ `(23,7)/(24,7)` are collision-1 — target `(23,8)/(24,8)` facing NORTH, press A; they need **≥2 usable Pokémon**. ‼ `(21,6)` ejects to `(7,30)` and is **not flag-gated**. ‼ **Leaving the gym RESETS the puzzle**; internal warps preserve it. ‼ **Solving the puzzle AIMS THE TRAINERS AT YOU** — pressing yellow at `(3,30)` puts Maura adjacent and facing you; gym battles are a consequence of the mechanic, not a derail. ✅ **SOLVER + EXECUTOR BUILT AND DRIVEN 2026-08-12:** `--driver mossdeepgym` gives `at_leaders=True map=MOSSDEEP_CITY_GYM at=(23,8) controllable=True whiteouts=0`, the 117-step route walked in a single plan with zero re-plans; anchor `saves/at_mossdeep_leaders.ss1`. The BFS route matches both agent-derived routes switch-for-switch. ✅ **The Tate & Liza DOUBLE battle is built and driven** (`fight_the_leaders`): the ≥2-usable-Pokémon gate is checked up front rather than discovered, and the chapter allows three attempts because a whiteout leaves the gym and leaving RESETS the puzzle. ‼ Still UNEXERCISED: the executor’s own interruption branch (the trainer battles that fired were handled by the standard listeners) and the real whiteout path (both driven runs had `whiteouts=0`; the guard is proven by fault injection, not by a live loss). ✅ **AND the chapter now LEAVES the gym** (it was stranding the run on an eleven-tile island; the acceptance test now requires being outside). **NEXT: §Ch19, the Mossdeep Space Center** — groundwork + measured hazards in `modules/story/space_center.py` and `tools/story-dev/probe_ch19_hazards.py`; ‼ §Ch21 is BLOCKED by KI-63 (no Dive learner, party full) — beating the leaders already sets `VAR_MOSSDEEP_SPACE_CENTER_STATE=1` and unhides Team Magma + Steven. |
| `#24-spacecenter` | ✅ **DONE 2026-08-12 — §Ch19 runs END TO END and is WIRED into the ladder (Segment 19).** One chapter covers BOTH the Space Center defence and the Dive hand-over, because `chapters.py` grades chapter 19 on `RECEIVED_HM_DIVE`. Driven from `post_mossdeep_gym.ss1`: `dive=True hm08=True MOSSDEEP_SPACE_CENTER_STATE=3 map=MOSSDEEP_CITY at=(19,11) controllable=True whiteouts=0`, **CAN-CONTINUE OK(15wp)**. The ladder now runs **20 of 24 beats**. Anchors captured: `at_steven_2f.ss1`, `post_space_center.ss1`, `post_dive.ss1`. Drivers: `--driver spacecenter1` (legs 1-3), `spacecenter2` (the menu + multi battle), `spacecenter` (whole chapter; run it from `post_space_center.ss1` too — that PROVES the resume guards by skipping to leg 6). ‼ **THE CITY IS CUT IN TWO** until the forced cutscene runs: the gym victory SPAWNS five Team Magma NPCs onto the only land bridge (x=44, y=23-26) and our planner blocks loaded-object tiles, so leg 1 is TWO legs — trigger line, assert `VAR_MOSSDEEP_CITY_STATE == 2`, then the door. I first mis-blamed KI-59 for this; see `08-MISTAKES.md`. ‼ **THE STAIR GRUNT MUST BE TALKED TO** (`sight_radius = 0`, stands ON the only tile the stairs are reachable from) — navigating there can never succeed. ‼ **THE PARTY-SELECT MENU IS NOW SOLVED AND VERIFIED LIVE:** cursor slots 0-5 are mons, **6 = CONFIRM**, each pick is `A` (submenu) then `A` (ENTER) and **the cursor does not advance**; A on an already-picked mon DESELECTS it, so blind A-mash toggles for ever. Every pick is verified against `gSelectedOrderFromParty` — measured `[1,5,3,0]` against `INTENDED-PICKS [0,4,2]`, an exact match (Sceptile L48 / Mightyena L44 / Swellow L40). **Always bring 3**: the loss condition sums HP over the player's picks ONLY, so bringing fewer is strictly worse. ‼ **Losing is a RETRY, not an error** — the script calls `SetCB2WhiteOut` itself, halves the money and warps to the last heal location, but leaves the var at 2; leg 1's heal matters twice over because the anchor's respawn was measured to be **LILYCOVE**, across the sea. ‼ **§Ch19 nearly ended INSIDE Steven's house** — caught by the acceptance's `calculate_path` off the end tile, KI-56's rule for the third time. |
| `#24-remainingarc` | 🔄 **THE SEAFLOOR CAVERN IS DRIVEN END TO END (2026-08-14, latest) — KYOGRE AWAKENED, THE ATOLL ESCAPE EXECUTED; what remains of §Ch20 is the CHAPTER ASSEMBLY.** `--driver ch20room9` (NEW) → `ACCEPTANCE: PASS` ×2 (runs 1 & 3): Rooms 1→8 re-proven, the `(17,42)` trigger (gate `VAR_SEAFLOOR_CAVERN_STATE == 0` verified live), the Archie SINGLE battle, the Kyogre chain ridden with three bounded milestones, release gated on **`VAR_ROUTE128_STATE == 2`** (‼ the first `releaseall` is a decomp-proven trap — Room 9's script tail releases on Route 128 BEFORE the Steven scene re-locks), landing `(38,22)` with all mid-warp invariants exact, **facing on release MEASURED `'Up'` ×2** (previously decomp-only), and the measured escape `(38,23)` → Surf `(38,24)` → `OCEAN-PATH OK len=5` to the dive tile. **10/10 pre-registered predictions held** (`ai-research-notes/2026-08-14-ch20-room9-drive-predictions.md`). ⚠ **Run 2 LOST the Archie fight — 2W/1L measured, the chain's ONE stochastic element** — the party arrives chipped (no heal in the cavern; run 3 telemetry: one mon fainted, lead 96/135, usable=5), and a lost run prints NO RESULT (whiteout → Manual → generator dropped; the `PRE-ARCHIE PARTY` line is the attribution record). Ruled in `06-DECISIONS-LOG.md`: a loss is a VALID BRANCH — the chapter carries a bounded whiteout-retry (each retry = full re-dive, ~25 min) + pre-boss readiness. ‼ Pre-run adversarial review caught the museum-greeter bug being re-written into the new ride loop (A mashed across the release seam) — fixed BEFORE run 1 with the gated `A`-if-`is_waiting_for_input()`-else-`B` press (`08-MISTAKES.md`). Counts: **R1 n=13, R2 n=10, R6 n=9, R3 n=8, R8 n=5, R9 full-chain n=2.** ⇒ **NEXT: ASSEMBLE §Ch20 AS A CHAPTER** (Segment 20; organic Dive via KI-63's wiring; Repel policy — Blocker 3; badge/move pre-flight — Blocker 4; whiteout-retry; grade the segment on `VAR_ROUTE128_STATE == 2` + escape + can-continue, NOT on the pre-warp Kyogre flag). ⛔ Still NOT a chapter; ladder remains 20 of 24. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 8 — THE BOT STANDS IN ROOM 9 (2026-08-14). `--driver ch20room8` (NEW) → `ACCEPTANCE: PASS` twice: once CLEAN (first attempt — 9/9 pushes, `attempts=1`) and once FAULT-INJECTED (`POKEBOT_CH20_FAULT=room8`: the jam-recovery handler was EXERCISED, not just written — exit to Room 3 via the `(5,12)` arrow warp, re-enter, all twelve boulders respawn, retry clean; `recovered=True attempts=2`).** OUR adjudicated 9-push sequence (⛔ step 9 faces **LEFT**) executed exactly as tabled; an independent offline refutation pass (our ROM reader + the pret decomp agreeing on all 12 boulder templates, simulation checker itself fault-tested) returned **SURVIVES** before the drive. Exit path `(5,4)→(5,2)` `OK len=2`, **no boulder on `(5,3)`**, `ROOM9 (5,4)` arrival, real step taken. **9/9 pre-registered predictions held** (`ai-research-notes/2026-08-14-ch20-room8-drive-predictions.md`) — including KI-77's window predicting **exactly 8 of 12** boulders visible at arrival. The Room-3 walk was extracted VERBATIM into `_cross_room3` so ch20room8 inherits it; neutrality proven by re-running `--driver ch20room3` → PASS. Re-proof counts now: **R1 n=10, R2 n=7, R6 n=6, R3 n=5, R8 n=2.** ‼ Adversarial review of the diff found one real defect BEFORE it ran: the recovery hardcoded `"Down"` instead of deriving the hold direction from the live tile (the `_cross_room6` rule) — fixed, and the fault run then showed the arrow warp fires during the navigate itself, which the hardcode would have handled blindly. ⇒ **NEXT: ROOM 9** — the 62-step walk to the trigger `(17,42)` (⛔ NOT `(16,42)`, which is plain floor), Archie, Kyogre, grade on `VAR_ROUTE128_STATE == 2` (never the Kyogre flag), and the atoll exit: step SOUTH to `(38,23)`, face Down, Surf onto `(38,24)`. ⛔ Still NOT a chapter — no module in `modules/story/`, drivers inject Dive; the ladder remains 20 of 24. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 3 — THE BOT STANDS IN ROOM 8 (2026-08-13). `--driver ch20room3` → `ACCEPTANCE: PASS`, reproduced twice.** The WALK route: 18 steps, **zero pushes**, ending `SEAFLOOR_CAVERN_ROOM8 (5,12)` with a real step. It re-proves every room beneath it → **Room 1 n=7, Room 2 n=4, Room 6 n=3**. ✅ **THE DOUBLE-BATTLE CLAIM IS CONFIRMED LIVE:** one trainer battle in Room 3, `is_double=True`, at exactly `(6,5)`, with `usable=6` asserted BEFORE the walk so the result is attributable. ⛔ **My own discriminator printed a false "REFUTED"** — it counted trainer battles run-wide and swept in the Room 1 grunt; **the instrument was wrong, not the claim**, and it was caught because `saw_double` was reported rather than graded and the raw log printed the map next to the judgement. ✅ Two wild encounters fired, one **between two Strength pushes** — closing a gap the Room 2 note flagged as untested. ✅ An adversarial review of increment 3 found a real BLOCKER (a design decision that lived only in a commit message, never in `06-DECISIONS-LOG.md`) — closed. ⇒ **NEXT: BUILD `--driver ch20room8`** (‼ it does **not exist yet** — it is the thing to write, not a command to run), **using OUR 9-push sequence** — ⛔ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit); a jam is recoverable by exiting to Room 3 and re-entering. **Then Room 9** (62-step walk to the trigger `(17,42)`, Archie, and the atoll exit). Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH THE ROOM 6 CURRENT MAZE AND THE BOT STANDS IN ROOM 3 (2026-08-13, latest). `--driver ch20room6` → `ACCEPTANCE: PASS`, first drive, 8/8 pre-registered predictions.** ‼ **THE FIRST EXECUTED CURRENT CROSSING IN THIS PROJECT** — Rooms 6/7 were planner-level only until now, and *a plan is not a walk*. ⇒ **"Rooms 6/7 need no solver" now rests on a WALK.** ⚠ The **endpoint** is proven, not the intermediate slide behaviour. ✅ **And Room 3's arbitration was confirmed LIVE in the same run:** `calculate_path((4,15)→(8,1))` = `OK len=18` **containing `(6,5)`** ⇒ **Room 3 is crossable PUSH-FREE, so its 7-boulder puzzle is OPTIONAL**, and the walk **must** take the trainer battle (decomp: a single **DOUBLE** battle, still unobserved live). ⛔ **An earlier agent pass called our build spec "REFUTED" on Room 3 and was ITSELF WRONG** — I propagated it into the docs before a deeper pass corrected it; *an agent's REFUTED needs the same two independent authorities as a CONFIRMED*. ‼ **The drivers also DERAILED instead of failing** on the one branch three green runs never took (`AttributeError` on `self.moved`) — found by adversarial review, reproduced via the new permanent hook **`POKEBOT_CH20_FAULT=room1`**, fixed, A/B proven. **Room 1 is now n=5, Room 2 n=2.** ⇒ **NEXT: `--driver ch20room3`** (the WALK: `navigate_to(ROOM3,(8,1))`, 18 steps, zero pushes, precondition ≥2 usable Pokémon, graded on both trainer flags SET), **then Room 8** with OUR 9-push sequence — ⛔ step 9 faces **LEFT, never UP**. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 2 (2026-08-13). `--driver ch20room2` → `ACCEPTANCE: PASS`, first drive, 10/10 pre-registered predictions.** It re-solves Room 1 from scratch every run (`FLAG_TEMP_*` objects respawn on map load), so **Room 1 is now n=3**. Route: smash `(8,7)` → **exactly three** north pushes of boulder `id 4` → `(6,1)` → `SEAFLOOR_CAVERN_ROOM6 (11,21)`, then a real `calculate_path` to the room's exit `(4,1)` = `OK len=13` **measured from inside** — matching what `probe_ch20_currents.py` predicted from outside. ‼ **THE HEADLINE IS A CORRECTION TO OUR OWN SHIPPED SOURCE:** `FLAG_SYS_USE_STRENGTH` read **False** right after the ROOM1→ROOM2 warp, so `early_game.py`'s *"NEVER CLEARED … once per SAVE"* was wrong — it is cleared on EVERY warp (`ClearTempFieldEventData` → `LoadMapFromWarp`). The old claim rested on a search for the SCRIPT MACRO `clearflag`; the clear is the C function `FlagClear`. The CODE was always safe (`strength_push` re-checks per call) — this was load-bearing documentation on top of correct code. Both comments fixed; **drift is still exactly 3** (`early_game.py` was already one of them). ‼ **KI-77 CORRECTED TWICE the day it was filed:** the despawn window is derived (20x17, predicts our live dump 5/5) so **"armed in Room 8" is REFUTED** (Room 8 is 11x14, smaller than the window — the LARGE rooms are the risk), and the game **physically resets a pushed boulder to its template tile on despawn**, so the planner is fail-safe and never under-blocks. ⚠ **THE UNTESTED DANGER IS THE EXIT:** the chapter lands on `ROUTE128 (38,22)` **facing north**, and north is a **41-tile closed lagoon** with `allow_escaping: false` ⇒ **step SOUTH to `(38,23)` and Surf**. ⇒ **NEXT: ROOM 3 — arbitrate first; it is NOT the walk the spec calls it (7-boulder puzzle omitted, trainers unavoidable on the push-free line, and a boulder can block the `(9,13)` retreat warp).** Room 8 is already adjudicated — use OUR 9-push sequence, and ‼ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit). Older text follows. 🔄 **§Ch20 INCREMENT 1 IS DRIVEN AND PASSING (2026-08-13): the bot is INSIDE the cavern and through ROOM 1.** `--driver ch20room1` → `ACCEPTANCE: PASS` first drive — ingress `legs 5/5`, `ROOM1 (5,18)`, Rock Smash + **two `strength_push`es verified by `local_id`** (boulder 1 → `(5,12)`, boulder 2 → `(13,11)`), ending `ROOM2 (10,7)` controllable with a real step taken. ‼ **The A/B is the result, not the arrival:** `calculate_path(→ (11,11))` went `PathFindingError` → `OK len=6` with live objects on both arms, which turns `probe_ch20_interior.py`'s Room 1 NO-PATH from a **lower bound** into a **measured fact**. 6 of 7 pre-registered predictions held (`ai-research-notes/2026-08-13-ch20-room1-drive-predictions.md`). ⛔ **AND THE ROUTE HAD TO BE ARBITRATED FIRST — our own build spec was WRONG about Room 1.** It claimed an *exhaustive* search proves the `(5,11)` boulder must be pushed **north**; the decomp and our own ROM both say `(5,10)` and `(5,12)` are `collision=0 elevation=3 'Cave'`, so **either** direction is legal and the uniqueness claim is false. Upstream's **south** push ships and was confirmed live. ⇒ ‼ **The spec's Room 2 and Room 8 "exhaustive" sequences are UNAUDITED — arbitrate each against the decomp AND `puzzle_solver.py:395-454` before driving it.** ‼ **NEW: KI-77** — `get_map_objects()` is a **camera-range window**, so a pushed boulder's vacated tile is re-blocked once it scrolls off screen; benign in Room 1, **armed in Room 8's nine pushes**. ⇒ **NEXT: arbitrate Room 2, then drive `--driver ch20room2` the same way (measure → A/B → solve → can-continue).** Older text follows. 🔄 **§Ch20 IS FULLY SCOPED AND UNBLOCKED, NOT YET BUILT (2026-08-13).** ✅ Its blockers are gone: **KI-63 resolved** (the bot acquires Dive by playing), the **dive leg is driven 6/6**, and **KI-59 never gated it** (retracted — 0 of the cavern's 115 tiles reach the buggy branch). **Artefacts to build from:** the 11-leg spec `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`, the Area Atlas `probe_ch20_interior.py`, and `probe_ch20_currents.py`. **Shape:** Rooms 1/2/3/5/8 are **STRENGTH-BOULDER** puzzles, Rooms 6/7 are **current mazes** (‼ routable by our planner — 4/4 predictions, no solver needed), Rooms 4/9 split by terrain. ‼ **ROCK SMASH IS MANDATORY** — Strength alone is physically stuck in Room 1. ‼ **Trigger tile is `ROOM9 (17,42)`, NOT `(16,42)`.** ‼ **Grade on `VAR_ROUTE128_STATE == 2`, not the Kyogre flag** — the flag is set before a forced warp into a SECOND cutscene that lands on a **sandbar the bot must Surf off**. ‼ **Losing to Archie resets the whole dungeon**; **puzzle state resets on every map re-entry**. ⇒ **NEXT: DRIVE IT, leg by leg** — the interior was measured from OUTSIDE, so its per-room routing is a LOWER BOUND. Older text follows. 🔄 **§Ch18 + §Ch19 DONE; §Ch20/§Ch21 remain.** The path to the end of the Aqua/Magma story, decomp-gated: ✅ **§Ch18** Mossdeep Gym → `BADGE07`; ✅ **§Ch19** Mossdeep Space Center **and** Steven's **HM08 Dive** → `FLAG_RECEIVED_HM_DIVE` (both in Segment 19 — they are one chapter in `chapters.py`), which also unhides the Seafloor Cavern entrance guard; ⛔ **§Ch21** Seafloor Cavern (Kyogre) — **BLOCKED BY KI-63**: HM08 is in the bag but **no party member can learn Dive and the party is full**, so `#24-pc` is a PREREQUISITE, not a later nicety. ‼ My handoff had said the Seafloor Cavern was next — it was three beats away, and Dive was the real gate. Checking beat the assumption. ⛔ **RETRACTED 2026-08-13 — "KI-59 is armed in the Seafloor Cavern" is FALSE and was never a §Ch20/§Ch21 prerequisite.** The 115 `Impassable *` tiles are real, but **every one has `collision=1`**, and `map_path.py:128` is the `elif` of `if tile.collision != 0:` — so **none of them reach the buggy branch**. Measured over all 518 maps by `probe_impassable_dirs.py`; re-measured in a fresh process in reverse order as a cache-poisoning control (KI-73), both agree. The prescribed A/B on `SEAFLOOR_CAVERN_ROOM1` would have shown a zero delta and invited the wrong conclusion. KI-59 is still REAL — it is live on 401 other tiles, chiefly the **Regi tombs** — but it does **not** gate the cavern. See `#24-impassabledirs`. Superseded text: KI-59 is armed in the Seafloor Cavern (115 `Impassable *` tiles across Rooms 1-9) — fix it with an A/B on `SEAFLOOR_CAVERN_ROOM1` BEFORE the cavern chapter exists. |
| `#24-aquahideout` | ✅ **DONE 2026-08-11 — §Ch17 BUILT and driven PASS.** `escaped=True controllable=True map=AQUA_HIDEOUT_B2F at=(24,19) whiteouts=0`, all **8 maze hops** in order. B1F is a warp-panel maze (‼ 21 of its 25 warps return to B1F) so the route was BFS-solved from the ROM warp table by `probe_aqua_hideout_graph.py` and every hop is graded on **(map AND tile)** — Ch15's "did the map change?" is useless when most hops are B1F→B1F. Wired as Segment 17; anchor `saves/post_aqua.ss1` captured on PASS. **Out of scope:** the Master Ball at `B1F (15,9)` behind two Electrode. |
| `#24-slateportsub` | ✅ **DONE 2026-08-11 — §Ch16 runs end to end, driven PASS (x3, frame-identical).** `harbor_state=2 controllable=True map=SLATEPORT_CITY_HARBOR at=(8,13)`. **Legs 2-4 had never been exercised before.** The blocker (KI-57) was resolved by reading the game rather than routing around it: ‼ the harbor door is set in a solid wall whose ONLY neighbour is Capt. Stern's tile, and `SlateportCity_EventScript_CaptStern` — **talking to him** — ends in `warp MAP_SLATEPORT_CITY_HARBOR, 11, 14`. The script carries the player in. Anchor `saves/post_harbor.ss1` now captured on every PASS. |
| **KI-56 — stranded in the Magma Hideout** | ✅ **RESOLVED 2026-08-11 — BUILT AND DRIVEN.** Cause confirmed against the WHOLE eight-map warp graph (18 of 20 nodes reachable from the stranded tile; the only two misses are the exit warp and Jagged Pass), so there is no walk-out and options 2 and 3 are dead. Fixed with the **Escape Rope the dungeon itself provides** at `3F_3R (9,19)` — no detour, no shopping. `--driver magmaexit` VERDICT **PASS**: `out=True map=JAGGED_PASS at=(16,19) controllable=True`, the exact tile predicted from `escapeWarp` beforehand. Guarded by `repro_hideout_exit.py` (fault-injected both ways). |
| **KI-57 — Capt. Stern blocks Ch16's harbor approach** | ✅ **RESOLVED 2026-08-11.** He was never an obstacle — **he is the door.** `SlateportCity_EventScript_CaptStern` ends with `removeobject` + `setvar VAR_SLATEPORT_CITY_STATE, 2` + `warp MAP_SLATEPORT_CITY_HARBOR, 11, 14`, landing on the same tile the door warp uses. Ch16 legs 1+2 now walk to `(27,13)`, face Right and ride the scene; the door path survives as the resume branch. ‼ Two instrument lessons recorded: `calculate_path` does NOT validate its source tile (a 'path' out of solid rock reports OK), and a story NPC in a doorway is usually the trigger. |
| `#24-r110mauville` / KI-48 / KI-49 | travel bugs, measured, unstarted. `could not reach` was 72 events in one batch. |
| `#24-magmahideout` + `#24-strength` | ✅ **DONE 2026-08-10 night** — `GROUDON_AWAKENED_MAGMA_HIDEOUT` set, wired as Segment 15. Listed here only so the next reader sees they closed; details in the entries below. |

### 2. BLOCKED ON A USER DECISION — no work should start on these
| item | the decision |
|---|---|
| ~~PROMOTE Ch15 + `#24-strength`~~ | ✅ **DONE 2026-08-10 night — user-approved.** Promoted and **verified DRIVEN in `custom-pokebot`** (`--build custom` → `groudon=True`, 0 whiteouts). **Source drift: ZERO**, so the sandbox re-base is a no-op. See `custom-pokebot/DIVERGENCE-LOG.md`. |
| ~~`#24-magmahideout` status conflict~~ | ✅ **RESOLVED 2026-08-10.** The conflict was "this list says DEFERRED, the handoff calls it the next lever". The handoff was right, the deferral's *reason* was wrong three separate times (see the entry below), and the chapter is now **DONE**. |
| the boss-healing response | items / burst damage / stop promising an answer — see `04-HANDOFF.md`. ‼ **2026-08-11 sharpened it**: the Magma Hideout loss is **Crobat CONFUSING the two best attackers into killing themselves** + Maxie healing Camerupt 22→67. So the menu of answers now includes **status response** (switch out / Persim Berry), not just burst damage and items. |
| **KI-52 — `lead_cannot_battle_action`** | ‼ **NEW 2026-08-11.** A WILD battle ends the run when the lead drops below `hp_threshold`, **with five healthy party members unused** (measured, Magma Hideout 4F). `rotate` is obviously right there — but **`flee` is CORRECT for shiny hunting**, so a global flip trades a story derail for a hunting regression. Needs a scope decision: mode-scoped override, a story battle strategy, or leave it. |
| `#doc-policy-05` | should `05-KNOWN-ISSUES` drop an entry at sandbox-fix or at promotion? |
| `#24-organicteam` | ✅ **APPROVED — GATE LIFTED (user 2026-08-06, re-confirmed 2026-08-14).** ⛔ This cell read *"deferred by the user on purpose 2026-08-05. Do not start early"* until 2026-08-14 and was stale by eight days; it is the line the session-start catch-up summary quotes, so it misdirected every cold start. Build order: the three PC defects first, then this. |

### 3. THE MEASUREMENT PROBLEM — affects every outcome item above
Finish rate has been unresolvable in **every** batch: 25.0 → 33.3 → 16.1% at n≈30 runs each. To
resolve a 10-point change needs ~300 runs ≈ **30 hours of batching per question**. Battle-level
metrics have ~800 samples per batch instead. **Grade mechanism work on battle-level metrics**
(boss win rate, item landings, heal events); treat finish rate as a lagging indicator only.

### 4. DORMANT BACKLOG — real ideas, nobody is working on them
GUI/dashboard (`#30`, `#31`, `#32`, `#33`, `#36b`, `#25`, `#26`, `#28`), dex/analytics tooling
(`#9`, `#11`, `#22`, `#23`, `#34`, `#35`, `#41`, `#42`, `#45`), and story sub-features not yet
scheduled (`#24-ui`, `#24-shops`, `#24-autosave`, `#24-defeat`, `#24-personality`, `#24-favourite`,
`#24-badges*`, `#24-gymtrainers`, `#24-partyvariety`). ‼ Several are marked "BUILT IN SANDBOX
2026-07-19" and were never verified or closed.

### 5. ✅ DUPLICATE / OVERLAPPING IDS — CONSOLIDATED 2026-08-10 (user-approved)
Each group now has ONE canonical entry; the duplicates were converted into **pointers** with all
their original text kept underneath, because IDs are never reused here and the reasoning trail is
worth more than the tidiness.
| group | canonical (still open) | why it wins |
|---|---|---|
| the `#24` umbrella (was 3 entries) | **"STORY AUTO-PLAYER"** | the umbrella header; ⛔ its "cold start reaches Badge 6" body went FIVE CHAPTERS stale and was corrected 2026-08-13 — **the live head is `#24-remainingarc` at the TOP of this file**, not this entry |
| PC / box team management | **`#24-roster`** | the user APPROVED it 2026-08-06 and lifted its gate, which outranks the older `#24-pc` design entry |
| organic team building | **`#24-organicteam`** | ⛔ **CORRECTED 2026-08-14** — this cell used to read *"it carries the user's 2026-08-05 DEFERRAL, i.e. the live instruction"*, which was **already false when written on 2026-08-10**: the user reversed that deferral on 2026-08-06 (`06-DECISIONS-LOG.md` RULING 1) and re-confirmed the lift on 2026-08-14. The entry is canonical because it is the concept's home, NOT because it carries a deferral. **The gate is LIFTED.** |
‼ **`#24-pc` (Surf resource walls) REMAINS OPEN and was not touched** — it is a derail class, a
different thing from the PC/box *feature* that shares its id.
Counts after consolidation: **86 open / 21 partial / 102 done (measured 2026-08-15; ‼ `lint_docs.py`'s I1/I2 lines are the authority — this prose goes stale every session)** (was 91/22/93).

HISTORY — originally flagged as: duplicate / overlapping ids, not merged
* **`#24` appears three times** as the umbrella (L≈1828 "STORY AUTO-PLAYER", L≈2040 "STORY-MODE
  BOT", L≈2292 "Story auto-player"). Two are roadmap-era restatements of the third.
* **`#24-pc` appears twice** (the resource-wall entry and the PC/box team-management entry) and
  **overlaps `#24-roster`**, which is the approved PC-roster feature.
* **`#24-organicteam` and `#24-team`** are the same concept under two IDs.
⇒ Recommend consolidating each group under its newest ID with the older ones pointing at it.
**Not done unilaterally — it rewrites history in a current-state file.**

### 6. CLOSED BY THIS TRIAGE (evidence in each entry)
* `#24-leadcounter` — shipped; `is_hunted_counter` is in `team_policy.lead_rank_key`.
* `#24-counters` phase 2 — shipped and batch-validated repeatedly (z = +3.24 on Machop).
* the "READY TO APPLY THE MOMENT BATCH `20260802-160603` LANDS" heading — that batch landed
  2026-08-02.

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

- [x] `#24-hmslots` — **RULED 2026-08-05: RESERVE SLOTS. No code change; this ratifies current
      behaviour.** The party fills to 4 with early wilds and grows organically to a measured mean
      **5.85 by Feather** as HM learners and counters board. Logged as a ruling so nobody reads it
      as unfinished and re-raises the cap — that mistake cost 36 points once already.
      Rejected: cap 5 (unmeasured, cosmetic, costs a batch), deposit-to-make-room (the real fix,
      but it is `POKEBOT_PC_ROTATION`'s shape — disabled for costing ~19 points).
      Full rationale: `06-DECISIONS-LOG.md` 2026-08-05.

- [ ] `#24-organicteam` — ✅ **THE GATE IS LIFTED. APPROVED TO BUILD (user, 2026-08-14:
      *"Yes lift the gate as I believe it will help with other progress with this bot!"*), which
      RE-CONFIRMS RULING 1 of 2026-08-06.**
      ⛔ **THIS ENTRY SAID "DEFERRED — do not start early" UNTIL 2026-08-14, AND IT WAS WRONG BY
      FOUR DAYS.** The 2026-08-05 deferral quoted below was reversed by the user on 2026-08-06
      (`06-DECISIONS-LOG.md` RULING 1, *"reversed knowingly"*); the 2026-08-10 triage then
      re-recorded the deferral as *"the live instruction"* without referencing that reversal, so
      a deferral and its reversal both read as live. **Measured cost: it misled an agent twice in
      one conversation on 2026-08-14.** Superseded text, kept for the trail:
      *"DEFERRED BY USER 2026-08-05, on purpose. Do not start early."*
      > "we want to revisit this in the future to make the bot play more organically like a
      > regular player would (once we finish mapping the story out and can dedicate more time)"

      The user's REVERSAL reason (2026-08-06, quoted in the decisions log): *"it will help the
      story in the long run (less chance for failure, less errors with incompatible pokemon for
      bosses/gym leaders or missing HMs to travel…) We need this."*
      The real design question is not a seat count — it is the bot CHOOSING a team on purpose
      (type coverage, HM duties, keeping a favourite) instead of taking whatever slot is free.
      **Needs PC deposit/withdraw to be trustworthy first** — and as of 2026-08-14 that is
      measurably NOT trustworthy: three cited defects (the PC-menu Manual trapdoor, the egg-blind
      `withdraw_from_box` fullness test, and the type-only `box_counter_pid`) are being fixed
      first. It subsumes `#24-pcoverflow-proof` and the retired `POKEBOT_PC_ROTATION`.
      ‼ The OLD gate (*"story mapping must be finished first"*) is retired: the story IS mapped
      through §Ch20, and the user has ruled the feature helps the remaining progress rather than
      competing with it.

- [x] `#24-pcoverflow-proof` — **CLOSED 2026-08-07. Both halves are now live-proven, each by its
      own capability test.** Catch half: `--driver boxcatch` (see `#24-pcoverflow` below).
      Withdraw half: `--driver boxwithdraw` (see `#24-pcwithdraw-proof` below).
      The original blocker stands as a lesson: batch `20260805-122057` logged `withdrawing` **0**
      times because the Surf guard derailed runs before any full-party catch reached the overflow
      path. Bundling the feature with the cap measured the BUNDLE, not the part — and a targeted
      probe answered in **~45,000 frames** what four 3-hour batches could not.

- [x] `#24-pcoverflow` — **BUILT 2026-08-05** (user ruling: build the real thing, not a raised
      constant). `resource_blocker` no longer refuses a full party (ball gate untouched);
      `pc_trip.box_views/find_in_box/withdraw_from_box` read the PC, find a mon **by PID**, and
      collect it at the next heal. Frees exactly ONE slot, never deposits its own target.
      `repro_pc_overflow.py`. **NOT live-proven.**

- [x] `#24-cavethread` — **‼ CLOSED 2026-08-05: IT WAS NEVER A BLOCKER. Multi-hop cave
      threading ALREADY WORKS, in both directions, with no chain table.**
      Measured (`--driver cavethread`, `reached_dest` = maps actually visited):
      **IN** `DEWFORD_TOWN → ROUTE106 → GRANITE_CAVE_1F → B1F → B2F` (3 warps);
      **OUT** `GRANITE_CAVE_B1F → GRANITE_CAVE_1F → ROUTE106 → DEWFORD_TOWN`.
      MT_PYRE_SUMMIT is the same 3-warp shape ⇒ **`#24-mtpyre` is UNBLOCKED**, and Granite Cave
      B1F/B2F can be unparked as training grounds.
      ‼ **THE ONE REAL GOTCHA: never pass a WARP TILE (door/ladder/stairs) as a navigation
      destination** — walking onto it FIRES it, so the trip ends one map PAST the target and
      the navigator reports success. Both probe runs hit this and both first read as failures.
      Only the stale `_CAVE_EXITS` comment was changed; the tables are kept (redundant, cheap,
      harmless). Full detail: `07-CHANGELOG.md` + `08-MISTAKES.md` 2026-08-05.

      <details><summary>superseded framing (kept for the reasoning trail)</summary>

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
      </details>

- [x] `#24-mtpyre` — **BUILT AND LIVE-PROVEN 2026-08-06.** `open_route121_aqua_gate()` +
      `do_mt_pyre_summit()`, Segment 14. From `post_winona.ss1` in 76,368 frames: Magma Emblem
      obtained, `HIDE_JAGGED_PASS_MAGMA_GUARD` True (Magma Hideout open). End save:
      `saves/post_mtpyre.ss1`. 8 repros green. ‼ NOT batched — see `#24-mtpyre-batch`.

- [x] `#24-mtpyre-batch` — **DONE 2026-08-06. Segment 14 holds in production.**
      `20260806-055947` (`498eedd9`, VERDICT OK): MT. PYRE 274 / ROUTE 121 171 / ROUTE 122 89 in
      the debug logs; **9 finishes vs 10 runs reaching Feather (~90% conversion)**; 0
      BotModeError from either guard. Finish rate 52.0% → 37.5% is the new completion
      requirement, not damage — **no funnel rung moved significantly** (Balance→Feather z=1.49,
      whole funnel z=0.88). Whiteout uptick measured NOT attributable to Mt. Pyre.

- [x] `#24-mtpyre-log` — **DONE 2026-08-06.** Segment 14's five milestones now `console.print`
      (`_ch14_say`), so a mid-way failure leaves a trail in batch stdout. Frame count identical.

- [x] `#24-pcoverflow` — **CATCH HALF PROVEN AND ENABLED 2026-08-07.** Two independent breaks
      were found and fixed: (1) `pc_trip.box_views()` called `boxes`, a `@cached_property`
      returning a list → `TypeError` every call; (2) both catch branches required `party < 6`.
      Capability test (`--driver boxcatch`, `post_mtpyre.ss1`): `caught=True box 0→1
      exited_clean=True exit_frames=120`, then `second_catch=True box_now=2`.
      `POKEBOT_BOX_OVERFLOW_CATCH` defaults **1**.
      ‼ The box-transfer message does NOT need dismissing — the existing battle handler already
      rides it out. I "confirmed" that wedge twice and both were my probe idling (`08-MISTAKES`).

- [x] `#24-pcwithdraw-proof` — **PROVEN 2026-08-07. The withdraw half executes end to end.**
      New harness driver `--driver boxwithdraw` + fixture save `saves/boxwithdraw.ss1` (the end
      state of the proven box-catch run: party 6, box 2). Three consecutive runs, identical:
      ```
      Story: PC — depositing Skitty L17 to make room for Poochyena.
      Story: PC — withdrawing Poochyena from the box.
      Story: PC — Poochyena is in the party; party is now 6.
      [boxwithdraw] RESULT withdrew=True target=Poochyena party_before=6 party_after=6
                    box_before=2 box_after=2 deposited=True map=(0, 5)
      [boxwithdraw] AFTER usable=True second_heal_ok=True still_has_target=True party=6 box=2
      ```
      ‼ **It drives the PRODUCTION call site**, not `withdraw_from_box` directly: the probe sets
      `self._hunted_counter_pids` and calls `heal_in_pokemon_center`, which is the attribute and
      the piggyback the story bot actually uses (`higher_level_actions.py:218-232`). Calling the
      function directly would have proven the function works and NOT that the piggyback fires —
      and the piggyback is the half that was dead.
      ‼ **The no-op assertion matters as much as the positive one.** A second heal at the same
      Centre produced **exactly one** `withdrawing` line in total: with the PID now in the party
      `find_in_box` returns None and the piggyback returns without touching the PC. A
      duplicate-withdraw loop is the regression shape a fires-every-heal piggyback invites.
      ‼ Graded with a capability test, NOT a batch — four batches on 2026-08-06 produced zero
      statistically resolvable finish-rate differences; this took ~45,000 frames.

- [ ] `#24-roster` — **APPROVED 2026-08-06, gate LIFTED. The PC-roster feature.**
      Catch overflow into the box + withdraw on demand, so the bot can field type counters and HM
      carriers it could not otherwise hold. **Rulings + rationale: `06-DECISIONS-LOG.md` 2026-08-06.**
      Measured targets: `no super-effective answer` = **8 of 15 non-finishes**;
      `nobody can learn Surf — hunting…` = **~42/batch in 16 of 17 batches**.
      ‼ Round one changes NO catch policy, NO party cap, and adds NO deposit path
      (`POKEBOT_PC_ROTATION` stays pinned at 0 — it cost ~1 team member/run and a 5.4% VOID batch).
      ‼ **KEY INSIGHT: the roster is the missing PRECONDITION for `#24-partycap`, not a competitor.**
      At cap 4 the bot hunts a Surf carrier successfully (42×/batch, costly); at cap 6 the identical
      need became a hard derail (127×) and the batch collapsed 52.0% → 15.8%. A roster decouples
      "party is full" from "cannot obtain a carrier" — the exact mechanism that made the cap fatal.
      Prerequisites, in order: `#24-hmteachloop` → `#24-pcoverflow-proof` → re-baseline → slice.
      ✅ **PARTY ORDER IS DONE AND PROVEN (2026-08-13).** `modules/story/roster.py`'s
      `reorder_party()` is driven end-to-end by **`--driver roster`**: six swaps, all verified by
      PID, including `RotatePokemon(i, j != 0)` — a path nothing in this project had ever driven.
      The drive found and fixed a real defect (it returned `True` with the avatar unable to walk;
      A/B proven). This is the piece the **Regi arc** needs (KI-69: Wailord first, Relicanth last).
      ✅ **PROMOTED to `custom-pokebot/` 2026-08-13 (user-approved)** — verified by driving
      `--driver roster --build custom` to a **frame-identical PASS**, with `find_spec` confirming
      the custom tree was the one imported. Post-copy drift ZERO. Restore point
      `restore/2026-08-13-pre-roster-promotion`.
      ‼ **The DEPOSIT/WITHDRAW half of `#24-roster` is still the open work** — ordering answers
      *"in what order"*, not *"which Pokémon"*. `withdraw_from_box` remains proven only by
      `--driver boxwithdraw`. Two issues filed and deliberately NOT fixed: **KI-70**, **KI-71**.
      ‼ `reorder_party()` still has **ZERO production callers** — it is capability, not yet content.
      ✅ **THE DEPOSIT HALF SHIPPED 2026-08-13** — `pc_trip.deposit_one_dead_weight()` frees exactly
      one slot (postcondition-verified, sole-HM-carrier exempt), wired into production via
      `early_game.ensure_hm_learner_making_room` at both `story_mode.py` HM call sites, and gated by
      `repro_hm_slot_wiring.py` (22/22, fault-injected). Driven: `--driver divelearner`
      `ACCEPTANCE: PASS`, deposit asserted **by PID**.
      **Measured worth:** 20 terminal run-kills in 1,129 runs (**0.91%** excl. a reverted party-cap
      bundle) and **#1 of 14 derail causes by frames per event (1,717k ≈ 46 min)**, every one five
      badges deep — rare, but it kills the deepest runs.
      ✅ **PROMOTED 2026-08-14 — `custom-pokebot` is no longer inert.** ⛔ Corrected 2026-08-14:
      this line read *"NOT promoted — `custom-pokebot` is still inert (reads the flag, nothing
      sets it)"* for hours AFTER the promotion landed, contradicting `04-HANDOFF.md` item 1b and
      the changelog. Caught by MEASURING (`promote.py --check` lists only the two PARTY ACCOUNTING
      STAGE 0 files), not by reading. ‼ *A promotion updates the handoff AND every punch-list item
      that claims the file is unpromoted — that is a P-pair, and it was missed.*
      ‼ **STILL OPEN in this item:** withdraw-on-demand, catch-overflow policy, and any use of
      `reorder_party` by real content (the Regi arc is what will need it).

      ## PARTY ACCOUNTING — STAGE 0 SHIPPED 2026-08-14 (the ROOT beneath the P1/P2 fixes)
      ✅ **`modules/party_accounting.py` + gate `repro_party_accounting.py` (#22).** Splits the
      three quantities RULING D named: **A** `gPlayerPartyCount` (CAPACITY authority), **B**
      `len(get_party())` (ITERATION/INDEX authority, can be LESS than A), **C** the belief ledger
      — **not built, deliberately**. Divergence classes: HOLE / OVERFLOW / INVALID observed
      EXACTLY from `get_party()`'s own branches; STALE ⛔ **SAMPLED 1-in-300, never exhaustive.**
      ✅ **It wires NO call site, and the gate ASSERTS that** rather than trusting it — alongside
      a byte-identical observer-on/off A/B, silence on a healthy party, and a raising observer
      that must break the LOG and never the read. Three source injections each made it fail.
      ✅ **DRIVEN:** `--driver ch20dive` → `ACCEPTANCE: PASS` unchanged, and the run reported
      **25,523 recomputes / 86 scans / NO DIVERGENCE** — which also empirically confirms the
      once-per-frame bound (25,523 recomputes over 25,523 frames).
      🔜 **NEXT IS MORE MEASUREMENT, NOT STAGE 1.** ⛔ Do not re-point the ~35 capacity-shaped
      call sites at A until `collect_party_accounting.py` exits 0. ✅ PROMOTED 2026-08-15 (user-approved,
      verified by driving `--build custom` to an ACCEPTANCE: PASS); drift is back to nil.
      ‼ **(P3b) 2026-08-15 — the collector I shipped COULD NOT REACH ITS OWN CRITERION.** It
      demanded ≥5 drives and read them from `harness*.log`, which `story_harness.py:70` opens
      `"w"` — **every drive truncates the previous**. Fixed with a durable append-only
      `party_accounting_ledger.jsonl`; proven by ACCUMULATING, not by inspection. And its first
      fixed run **double-counted one drive as two** (`ch20dive` vs `Ch20Dive`), so fingerprints are
      normalised and log-scanning is OFF by default. ⇒ *for a tool that decides "is there enough
      evidence yet", over-counting is the dangerous direction.*
      ✅✅ **(P3b) ANSWERED 2026-08-15 — CRITERION (a) MET, the collector exits 0.
      7 clean drives / 7 distinct drivers / 280,707 recomputes / 940 scans / NO DIVERGENCE.**
      `ch20dive` 25,523 · `room1` 28,364 · `room9` 69,645 · `room2` 31,275 · `room8` 47,585 ·
      `room3` 46,118 · `room6` 32,197. ‼ `ch20room9` LOST its Archie fight (documented 2W/1L) and
      its row was written anyway — the measurement is independent of the driver's verdict.
      ⛔⛔ **READ THE POPULATION, NOT JUST THE ZERO.** All seven drives are §Ch20 DUNGEON content
      with a STATIC party — no catching, no evolving, no PC traffic. The scenarios most likely to
      make A differ from B (catch into a full party; a Shedinja spawning unbidden) were never
      exercised. The criterion was pre-registered and is honestly met, so P3b CLOSES — but the
      finding is *"the dungeon path is clean"*, **not** *"A cannot differ from B"*, and it is NOT
      licence to re-point the ~35 capacity call sites. ⇒ **(P4) is the better next step than
      Stage 1**: its fixture is exactly the party-mutating case this population lacks.

      ## (P4) THE END-TO-END REPRO — ✅ STAGE 1 **AND STAGE 2** DRIVEN, 4/4 ACROSS BOTH FORKS
      ✅✅ **STAGE 2 IS DRIVEN 2026-08-15 (`--driver boxcounter2`) — matrix {ARM A, ARM B} ×
      {sandbox, custom} = 4/4 `ACCEPTANCE: PASS`. ⛔ DO NOT REBUILD IT.** A SUBCLASS of
      `BoxCounterMode`, so every Stage 2 run re-proves Stage 1 first. ARM B: the real
      `heal_in_pokemon_center(FortreeCity)` collected the boxed Slugma — `moved=True` (in party
      AND gone from the box), `knows_rock_throw=True`, `lead_is_counter=True` with a
      `hunted_pids=None` CONTROL proving the mechanism was decisive (`control=Mightyena L38` →
      `real=Slugma L15`), and a second heal that NO-OPed for the ATTRIBUTED reason. ARM A: the
      derail reproduced organically — `_hunted_counter_pids` published EMPTY, counter left boxed,
      **no deposit at all**. ‼ The PID is published ONLY from `box_counter_pid`'s return value.
      ⛔⛔ **THE ANCHOR IS `fortree_gym_wedge.ss1` — the "use `ch13_fortree_door.ss1`" correction
      further down this entry is REVERSED BY A DRIVE.** `ch13_fortree_door` is on ROUTE120 and the
      run died on its first leg (`Cannot reach FORTREE_CITY: it is not walkable from ROUTE120`) —
      **KI-24**, documented in our own `region_reach.py:7-11`. ⚠ The wedge has NO Shedinja/Ninjask
      twins, so `ch13_fortree_door.ss1` stays the anchor for tests whose SUBJECT is that collision.
      ⛔ **`needed` IS `{Rock, Ice, Dragon}` — NOT `{…Electric}`** (the ace is Altaria,
      Dragon/Flying; Electric is 0.5×2.0 = 1.0, NEUTRAL). Caught by the new `needed_ok` control on
      its first run; the four-type set was in four documents that were copies of one another.
      🔜 **WHAT (P4) STILL DOES NOT COVER:** everything UPSTREAM of registration — a real `hunt()`
      catch feeding `story_mode.py:1750`. The Slugma is INJECTED and the PID published by the
      driver. Also still unbuilt: the natural-vs-injected byte-equivalence control.
      🆕 **RESIDUAL `#24-zerokocounter` (filed 2026-08-16, from the KI-80 decoupling):
      SHOULD `boss_teaches` ALSO COME OFF THE COUNTER-LADDER'S GATE?** The KI-80 fix removed
      `grass_is_fodder` from `story_mode.py:1901` and KEPT `boss_teaches`. KI-80's own wording
      ("gated on *is this fight hopeless*, which `_boss_plan_is_hopeless` already answers alone")
      can be read as removing BOTH conjuncts. ‼ **The argument for removing it is strong:** a party
      that KOs **nothing** and has no type answer is the MOST hopeless case, yet it currently gets
      the `:1932` "the boss can't teach us" message and plain grass escalation rather than a counter
      hunt. ⛔ **It was NOT shipped because NO TEST CAN SEE IT:** all four `ki80ladder` arms seed
      `kos = 1`, so `boss_teaches` is True in every arm we have. Shipping it would be changing
      behaviour we cannot observe — the thing this project keeps being burned by.
      ⇒ **To pick this up: add a FIFTH arm that seeds a flat `kos = 0` history** on
      `batch2_run04_wedge.ss1` with the NOGRASS cfg. ✅ **DISCRIMINATOR COMPUTED 2026-08-16 — the
      arms DO differ:** `recent_kos = [0,0]` ⇒ `boss_teaches` False ⇒ **today** `:1901` is skipped,
      `:1932` fires, `boss_mode` stays False, `OUTCOME = PLAIN_ESCALATION`; **after** removing the
      gate, `_boss_plan_is_hopeless` runs and every one of its own gates still passes on a flat zero
      seed (`losses 8 >= 6`; `len 8 >= 6`; `max(last 3)=0 > max(prev 3)=0` is False so it does NOT
      bail; `hard_plateau` needs 12) ⇒ `hopeless=True` ⇒ `OUTCOME = LADDER`. Non-vacuous.
      ⛔⛔ **BUT A FIFTH ARM IS NOT ENOUGH, AND THIS ENTRY UNDERSTATED THE HAZARD UNTIL 2026-08-16.**
      It described the `:1932` problem as a lost MESSAGE. It is worse, twice over:
      (a) removing `boss_teaches` makes `:1901` unconditional, so the `elif` at `:1932` is
      **structurally DEAD in every case**, not just the hopeless one — an `elif` on an always-true
      `if` never runs; and (b) the NOT-hopeless path below becomes reachable by a zero-KO party for
      the first time, so a boss with a **fodder patch AND a credible answer** whose party KOs
      nothing would hit `if grass_is_fodder: boss_mode = True`, print *"re-attempting the boss is
      the real training (KO'd [0, 0] of theirs)"* — absurd on its face — and **SUPPRESS `:1937`'s
      grass escalation.** ‼ **That is KI-23's mirror regression in a new guise, and arm 5 CANNOT SEE
      IT** (a NO_ANSWER save returns at `:1923` and never reaches `:1925`). ⇒ **an ARM 6 is required
      too: HAS_ANSWER save + `kos = 0` + a FODDER patch.** Same lesson as arms 1-3 vs arm 4.
      ⚠ **And measure first:** nobody has checked how often a flat zero-KO loss series actually
      occurs in production. `analyse_defeat_loops.py` measured *"53 sequences with >=3 defeats — flat
      in 37"* but never broke out zero-KO series. ⛔ Do not change behaviour of unknown frequency.
      *(Hazard (a)/(b) and the discriminator were derived by a Tier 2 cold-start agent, 2026-08-16.)*
      🆕 **RESIDUAL (filed 2026-08-15, found by a Tier 2 cold-start): `04-HANDOFF.md`'s
      `NEXT ACTIONS` numbering RESTARTS.** It runs 1, 2, 2c, 3, 3b, 4, 5 and then begins again at
      2b, 3, 4, 5, so a cross-reference to "NEXT ACTIONS item 3" resolves to TWO different items.
      Not misleading about STATE — item 0 is unambiguous and is what a cold start acts on — but any
      citation to items 1-5 is unresolvable. ⇒ when the "older framing" block is next touched,
      archive it wholesale rather than renumbering in place.
      ✅✅ **KI-80'S REPRO IS BUILT, DRIVEN AND FAULT-TESTED (2026-08-15) — `--driver ki80ladder`.**
      THREE arms on `saves/batch2_run04_wedge.ss1` (`team_max` 28, 8 seeded losses): `NOGRASS` →
      ladder · `GRASS_FODDER` (Route 102, `wild_max` 4) → ladder · ⛔ `GRASS_STRONG` (Route 119 —
      **the patch her own cfg comment names**, `story_mode.py:3531`; ⛔ she has NO `grass` key today, `wild_max` 27) → **plain escalation, ladder SKIPPED.** Only the
      `grass` key differs. `ACCEPTANCE: PASS` in BOTH forks. Fault-tested twice: the fixture KI-80
      itself once prescribed (`ch13_fortree_door`) FAILS with *"THE A/B WOULD BE VACUOUS"* and all
      three arms return `LADDER`; and `POKEBOT_KI80_DECOUPLED=1` FAILS today, which is what makes
      the same driver the AFTER run. ‼ **Exits 0 even on FAIL — grade the `ACCEPTANCE:` line.**
      ➡ **NEXT: decouple `_counter_ladder` from `grass_is_fodder` (`story_mode.py:1899-1901`)**,
      then flip `POKEBOT_KI80_DECOUPLED=1` FAIL → PASS.
      ⛔⛔ **BUT NOT THE NAIVE EDIT, AND `POKEBOT_KI80_DECOUPLED` ALONE WILL BLESS IT.** MEASURED
      2026-08-16: with `grass_is_fodder` simply deleted from the `:1901` gate, the three-arm run
      goes **`ACCEPTANCE: PASS`** — all three arms reach the ladder — while KI-23's **mirror
      regression has silently landed**. ⇒ **ALSO RUN ARM 4, BEFORE AND AFTER:**
      `POKEBOT_KI80_ARM4=1 … story_harness.py fortree_gym_wedge.ss1 --driver ki80ladder`.
      It PASSes today and, against that same naive edit, printed
      `ARM4 OUTCOME=BOSS_TRAINING_MODE` and `ACCEPTANCE: FAIL` — *"a boss with a STRONG patch AND a
      credible answer entered BOSS-TRAINING MODE, so `:1937`'s plain grass escalation is
      SUPPRESSED."* Keep `boss_mode = True` (`:1925`) behind `grass_is_fodder`.
      Transcripts: `evidence/2026-08-16-ki80ladder-FAULT-naive-edit-*`. The BEFORE run is committed FIRST because
      it is unrepeatable afterwards. `repro_boss_grass_gate.py` SELF-RETIRES on the fix — designed.
      ✅ **BOTH PROMOTIONS ARE DONE (user-approved 2026-08-15).** *(✅ The comment-only `story_mode.py` fix was PROMOTED 2026-08-16, user-approved. ✅ And the KI-80 DECOUPLING in the same file — a BEHAVIOUR change — was PROMOTED 2026-08-16 too, by a THREE-POINT A/B against `--build custom`. Drift is 0.)* The KI-79 fix `pc_trip.py` (a BEHAVIOUR change) was proven by a THREE-POINT A/B showing the new branch actually RUNS in custom, not merely that the file copied. And `counter_hunt.py`
      (comment-only, the Electric correction) promoted with restore point
      `restore/2026-08-15-pre-promotion-counterhunt-comment`: 1/1 byte-identical, and VERIFIED BY
      DRIVING — `--driver boxcounter2 --build custom` ARM A and ARM B both `ACCEPTANCE: PASS`,
      plus four `--build custom` gates. See `custom-pokebot/DIVERGENCE-LOG.md`.

      *(Everything below is the Stage-1-era text. It is kept for its build detail; where it
      predicts Stage 2 or names the anchor, the block above supersedes it.)*
      ## (P4) THE END-TO-END REPRO — ✅ STAGE 1 DRIVEN (both arms), ⛔ STAGE 2 NOT BUILT
      ‼ **Read `ai-research-notes/2026-08-15-p4-boxcounter-repro-design.md` before building.** It
      refuted FOUR of the premises it was briefed with, two fatally: the heal's withdraw is no
      longer gated `if _pids:`, and ⛔ **`post_dive.ss1` is POST-WINONA**, so the counter rung can
      never fire from it (use `saves/ch13_fortree_door.ss1` — the wedge sits INSIDE the gym).
      ✅ **BUILT:** `debug_write_box_slot()` (`debug_utilities.py`) — the missing half of the
      fixture, mirroring the storage reader; refuses on R/S, on an occupied slot, on a short
      record. `POKEBOT_BOXCOUNTER_TYPEONLY_A` — a permanent fault hook restoring the pre-fix
      TYPE-ONLY behaviour, read INSIDE the function. And `repro_box_counter_move_test.py` now
      exercises the **REAL** hook (4 checks, 2 of them controls) — every arm in that gate was
      previously a re-implementation, so the hook could have rotted unnoticed.
      ✅ **STAGE 1 IS DRIVEN 2026-08-15 (`--driver boxcounter`), BOTH ARMS PASS** — the first time
      `box_counter_pid` ran against REAL `gPokemonStorage` memory rather than `FakeStorage`.
      ARM B → the Slugma's PID (found by its MOVE); ARM A (`POKEBOT_BOXCOUNTER_TYPEONLY_A=1`) →
      `None`, the user's bug reproduced on demand. Four controls: `disjoint`, `fixture_ok`,
      `sole`, `not_excluded`. ⛔ Stage 1 CANNOT DERAIL, which is why the decisive claim lives
      there — under KI-71 a derailed arm prints nothing at all.
      ✅ **ANCHOR CORRECTED BY MEASUREMENT for Stage 2: `saves/ch13_fortree_door.ss1`**, not
      `fortree_gym_wedge.ss1` (that one sits INSIDE the gym). It holds a **REAL Shedinja+Ninjask
      sharing `pid=42207D6F`** — the first LIVE KI-78 twin pair here. ⚠ Its box holds a Castform.
      🔜 **SMALL OPEN ITEM (not blocking):** two docstrings still say the Shedinja twin is "the
      LATER slot" without the *at creation* caveat — `repro_pid_identity_key.py` (tools, free to
      edit) and `pokemon_party.get_index_for_pokemon` (PROMOTED, so editing it costs a promotion
      cycle). The live save has them REVERSED because `reorder_party()` runs. The fix does not
      depend on order, so this is wording, not behaviour.
      🔜 **STAGE 2 REMAINS:** the heal → withdraw → boss-fought-WITH-the-counter half,
      a one-time natural-vs-injected byte-equivalence control, and the
      {ARM A,B}×{sandbox,custom} matrix. ⛔ **The likeliest way it ships broken:** inject the
      Slugma BEFORE `counter_hunt.py:477`'s `before_box_pids` snapshot and `exclude_pids` filters
      it out — `None` in BOTH arms, so ARM A "reproduces" the bug for entirely the wrong reason.

      ## THE HEAL'S PC PIGGYBACKS NOW REPORT — the OTHER half of the Slugma/Winona derail (2026-08-14)
      ✅ **Gate #23 `repro_heal_piggyback_reporting.py` (20 checks, no emulator; ‼ it PRINTS its own count — believe that, not this).** The three PC
      actions riding on `heal_in_pokemon_center` (rotation deposit, KI-63 slot-freeing deposit,
      hunted-counter withdraw) each wrapped everything in `except Exception: pass`, collapsing
      *worked* / *nothing to do* / *threw* into one silence. **The user's run took the middle
      branch and said nothing** — that silence is most of why the bug cost a day. All three now
      report; the decision is a pure, testable `counter_withdraw_outcome()`; the empty-case message
      names `_hunted_counter_pids` AND the Slugma shape. ⛔ The empty case must NOT read as an
      error — it is the common case, and that is a gate check, because a diagnostic that cries
      wolf on every heal is worse than the silence it replaced.
      ‼ **Why no gate caught it:** `repro_no_silent_except` did not scan `modules/modes/util/`, and
      **its rule-3 escape hatch had already approved all three handlers** — a justification comment
      documents intent, it does not make a failure observable. Scope extended (baseline 140 → 149)
      and the ratchet is now **per scan root** (133/4/3/9, all measured), so the widened budget
      cannot fund new debt in the roots it already covered. Both halves fault-tested.
      ⛔ **THIS IS NOT (P4).** P4 — the END-TO-END live repro — is **still owed**. Recon is done and
      its three constraints are recorded in `04-HANDOFF.md`'s queue item P4 (no save holds a
      Nincada; KI-71 means a derailed arm prints NO RESULT; do not depend on a stochastic catch).

- [ ] `#24-logcollision-siblings` — **NEW 2026-08-16, found while fixing `#24-orphans` (4).** Four
      more repro scripts carry the SAME evidence-destroying pattern `story_harness.py` just shed —
      a fixed default log name opened `"w"`, so re-running the same arm silently eats the previous
      transcript: `repro_hm_move_replace_loop.py:82`, `repro_hm_replace_valve_forced.py:54`,
      `repro_movelearn_fault_recovery.py:73`, `repro_movelearn_hm_wedge.py:65`. ⚠ **Milder than the
      harness's was** — each varies by `build`/`mode`/`state`, so it only collides when the SAME
      arm is repeated (still exactly the before/after case). ⇒ apply the same one-line fix
      (`_<timestamp>_<pid>`, print the path first). **Filed rather than done** so the change can be
      run-verified per script instead of swept in unverified — the harness fix was proven by an
      actual A/B, and these deserve the same.


- [ ] `#24-zerokocounter` — **NEW 2026-08-16, from the KI-80 decoupling. Should `boss_teaches` ALSO
      come off the counter-ladder's gate?** `story_mode.py:1901` is now `if boss_teaches:`. KI-80's
      wording ("gated on *is this fight hopeless*, which `_boss_plan_is_hopeless` answers alone")
      can be read as removing BOTH conjuncts. ‼ **The case FOR is strong:** a party that KOs
      **nothing** and has no type answer is the MOST hopeless case, yet today it gets the `:1932`
      "the boss can't teach us" message and plain grass escalation instead of a counter hunt.
      ⛔ **NOT SHIPPED BECAUSE NO TEST CAN SEE IT** — all four `ki80ladder` arms seed `kos = 1`.
      ✅ **DISCRIMINATOR COMPUTED** (arm 5: flat `kos = 0` on `batch2_run04_wedge.ss1`, NOGRASS):
      today → `PLAIN_ESCALATION`; after → `LADDER`. Non-vacuous.
      ⛔⛔ **BUT ARM 5 IS NOT ENOUGH — TWO HAZARDS, derived by a Tier 2 audit:** (a) removing
      `boss_teaches` makes `:1901` unconditional, so the `elif` at `:1932` is **structurally DEAD in
      every case**; (b) the not-hopeless path becomes reachable by a zero-KO party, so a boss with a
      **fodder patch AND a credible answer** would set `boss_mode = True`, print *"re-attempting the
      boss is the real training (KO'd [0, 0] of theirs)"* and **SUPPRESS `:1937`'s grass
      escalation** — KI-23's mirror regression again. **⇒ an ARM 6 is required too** (HAS_ANSWER +
      `kos = 0` + fodder patch). Same lesson as arms 1-3 vs arm 4.
      ⚠ **AND MEASURE FIRST:** nobody has checked how often a flat zero-KO loss series occurs in
      production. `analyse_defeat_loops.py` measured *"53 sequences with >=3 defeats — flat in 37"*
      but never broke out zero-KO series. ⛔ Do not change behaviour of unknown frequency.
      ‼ **PROMOTED TO A TOP-LEVEL ITEM 2026-08-16** because a Tier 2 audit pointed out the irony: it
      was filed as a nested bullet inside `#24-roster`'s body — reachable only from inside another
      item — which is precisely the defect `#24-orphans` exists to stop. `#24-orphans` says SIX;
      this was the seventh. *(The full derivation stays in that nested bullet; this is the tracked
      entry point.)*


- [ ] `#24-rarepredicate` — ‼ **NOT READY TO BUILD. 2026-08-07: the dataset does not reproduce,
      and as computed it FAILS the user's own named example.**
      `tools/story-dev/rare_species_dataset.py` (new) is the **first script in this repo that
      computes this dataset** — the figures below were prose only, with nothing to regenerate or
      audit them, and `#24-roster` is approved to build ON them.
      | | recorded 2026-08-06 | computed 2026-08-07 |
      |---|---|---|
      | histogram | `d0=59 d1=21 d2=39 d3=7 d4+=3 d99=3` | `d0=62 d1=36 d2=22 d3=11 d99=1` |
      | depth>=3 | 13 species | 12 |
      | RARE (either rule) | 26 of 132 | 23 of 132 |
      | **Skitty** | rare via rate (2%) | ✅ **rate 2%, depth 0 — reproduces exactly** |
      | **Bagon** | pseudo-rare via warp depth, **d3** | ❌ **depth 2 — NOT selected** |
      ‼ **The `>=3` threshold exists FOR BAGON**, and under this derivation Bagon is d2, so the
      rule as written does not select the example that motivated it.
      ‼ **DO NOT tune the BFS until Bagon comes out at 3** — that is fitting the method to the
      desired answer. The punch list already predicted this exact fragility ("Meteor Falls' d2
      rooms are ALSO Surf-gated in reality, so `>=3` earns some of its precision by luck of
      Bagon's room being one warp deeper"); that luck does not hold here.
      **WHAT UNBLOCKS IT:** pin ONE definition of warp depth deliberately — the seed set, whether
      the connection closure is transitive, and warp directionality (making warps bidirectional
      moved d99 from 34 to 1, so that choice alone dominates the answer) — write the reasoning
      down, and make that script authoritative. Then re-decide the threshold with Bagon's real
      depth known. Skitty's rate rule is unaffected and is already reproduced.
      ✅ ‼ **USER INPUT 2026-08-14 — THIS MAY RETIRE WARP DEPTH ENTIRELY, WHICH WOULD UNBLOCK
      THE ITEM.** Asked what makes Bagon pseudo-rare, the user did NOT describe warp distance —
      they described **HM GATING plus LOCATION SCARCITY**, verbatim:
      > "For the Bagon instance, it is locked behind a Surf AND Waterfall requirement, and it is
      > only available in that one location which to me would be considered 'pseudo-rare' simply
      > based on the gating and limited location, encounter rate may not be low enough to
      > constitute a legit 'rare' tag but those other factors contribute to it being somewhat
      > rare/hard to find."

      > "For Feebas, that one should be considered rare due to the limited (potentially random)
      > tiles it is available on (also gated by fishing rod and surf requirement) as well as low
      > spawn rate"

      ⇒ **The candidate replacement rule is `HM/field-move gate count` + `distinct location
      count`, not BFS warp depth.** Bagon = 2 field-move gates (Surf, Waterfall) × 1 location ⇒
      pseudo-rare; that is a DIRECT read of the user's reasoning rather than a proxy that has to
      be tuned until it agrees. ‼ **This is exactly what "pin ONE definition deliberately" asked
      for — and warp depth was never the user's mental model, it was ours.**
      ⚠ **Feebas needs a special case regardless of the rule chosen:** it is one of the known
      false negatives that are **absent from `encounter_index` altogether** (with Beldum, gift
      and static species), so no rate-based or location-count rule can see it; and its real
      mechanic (a handful of seed-chosen tiles on ROUTE119) is not expressible in the encounter
      tables at all. Treat it as an explicit entry, not as something the predicate derives.
      ⚠ Field-move gates are partly modelled already (`training_areas.AREA_PREREQ` uses
      `"surf"`/`"rocksmash"`; `region_reach.KNOWN_GATES`) but **Waterfall and rod requirements
      are not**, and `KNOWN_GATES` is admittedly incomplete — pricing that gap is step 1.

- [x] HISTORY — `#24-rarepredicate` (original spec, 2026-08-06) — **the duplicate-catch exemption (`#24-roster` ruling 3). SOLVED — the
      "pseudo-rare" axis is WARP DEPTH, and it needs no new recon.**
      Three OR'd rules: shiny (already works) / rare gender variant / rare species.
      **Rare species = `best_slot_rate <= 4%` OR `warp_depth >= 3`** — 26 of 132 wild species (19%).

      **WARP DEPTH** = 0-1 BFS over the committed `cache/warp_graph_BPEE0.json`: seed every
      non-underwater group-0 map at 0, connection edges cost 0, **warp edges cost 1**, take the MIN
      over all of a species' locations. Histogram (independently reproduced 2026-08-06):
      `d0=59 d1=21 d2=39 d3=7 d4+=3 d99=3` (d99 = no path = **Dive**-gated, deliberate — Dive edges
      are excluded at `warp_graph.py:20`). **`depth>=3` = 13 species, ZERO false positives on
      inspection.** Bagon = **d3** (METEOR_FALLS_B1F_2R, Surf+Waterfall); Skitty = d0 (rate rule
      catches it at 2%).
      **Threshold rationale: there is a CLIFF between 4% and 5%** — the 5% Safari slots add 18
      species at once. 4% is the natural stop.

      ‼ **REJECTED: the encounter-METHOD proxy** (a species available only via `surf_encounters` is
      "Surf-gated"). Measured: 27/132 water-only species are the most UBIQUITOUS in Hoenn
      (Magikarp 53 maps, Tentacool 38, Wailmer 33). Surf-gating is TEMPORAL, not rarity — and Bagon
      is Grass-only anyway. Adding this axis takes the set from 26 to 61.
      ‼ **REJECTED: `nmaps == 1`** — 62/132 (47%), half the dex.

      ✅ **The field-move recon is NOT a prerequisite** — decisive. Warp depth is pure graph
      topology off a cache the bot already loads (`get_warp_graph()`), and the predicate fires at
      ENCOUNTER time, when the bot has by construction already cleared the gate. "Where is
      Waterfall first required" is a routing question this filter never asks. (That recon is still
      a real gap for `counter_plan` routing — just not for this.)

      ‼ **KNOWN FALSE NEGATIVES, accepted:** **Feebas is not in the encounter index at all**
      (`encounter_index.py:75-115` reads `gWildMonHeaders`; the 6-tile mechanic is not in that
      table), so the most iconic pseudo-rare species can never fire this rule. Same for Beldum and
      other gift/static/version-exclusives. Pure-sea endgame species (Luvdisc, Corsola, Staryu) are
      structurally d0 and miss. ‼ And the cutoff is fragile at the boundary: Meteor Falls' d2 rooms
      are ALSO Surf-gated in reality, so `>=3` earns some of its precision by luck of Bagon's room
      being one warp deeper. Treat warp depth as a good INFERENCE, not proof of a required HM.
      Traps found: `custom_catch_filters` runs **≥2× per encounter**, so the "do I own this species"
      lookup must be cached, never a 420-slot box scan; and `is_repeat_encounter` is PID dedup, NOT
      species dedup — do not reuse or name anything near it.

- [x] `#24-hmteachloop` — **ROOT-CAUSED AND FIXED 2026-08-07. The user's description was literally
      accurate, and the bug was OUR BUTTONS re-arming the teach.**
      After the move is learned, both replace branches switch themselves off (`and not _knows()`),
      so the ride fell through to a blind `A`-every-third-frame — and a Gen 3 bag teach ends on
      **"Do you want to teach <MOVE> to another POKéMON?"**, where **A means YES**. It reopened the
      party menu and re-entered the cycle until the 9,000-frame cap expired. Fix: once `_knows()`
      is true the only button is **B**.
      **A/B** (`--driver teachfull`, `POKEBOT_HMTEACH_POSTLEARN_A` toggles the arms):
      | arm | ride_exit | ride_frames | learned |
      |---|---|---|---|
      | OLD | `hard-cap` | **8,999** | True |
      | NEW | `learned` | **479** | True |
      Same outcome (`replaced=['Taunt']`), clean overworld exit instead of a dangling YES/NO.
      `repro_hmteach_postlearn.py` — 17 checks, green; fault-inject the branch to A → 3 red.
      ‼ **WHY FOUR BUDGET ROUNDS FAILED (7/8/9/4), and it is an instrument lesson:**
      1. Only the SUCCESS path emitted telemetry, so no batch could say WHICH exit fired — every
         hypothesis was unfalsifiable. Five exits are instrumented now (`TEACH EXIT`).
      2. **"Every successful teach exits in 35-86 frames" was measuring the wrong loop.**
         `TEACH OK … in {_f} frames` read `_f` AFTER the menus-closed loop rebound it (Python
         leaks `for` variables). The ride's real cost was **8,999**. That bogus figure is what
         justified "the budget governs only failures" and all four tunings.
      3. The stall detector could never fire: the ping-pong keeps state changing
         (`stall_peak=171` vs a 900 threshold). It was never frozen, it was busy.
      ‼ `--driver hmtest` could not reproduce this — it teaches a freshly caught mon with a FREE
      move slot, so there is no replace dialogue (12/12 clean). The failures are all on a mon with
      **four** moves; `--driver teachfull` forces exactly that.

- [x] HISTORY — `#24-hmteachloop` (original report) — **USER-REPORTED 2026-08-06. Real bug, wastes frames and looks buggy.**
      > "the hm learning feature works but it still loops trying to teach/get out of the teaching
      > cycle after it teaches an hm"

      i.e. the teach SUCCEEDS, then the bot keeps re-entering the teach/exit cycle instead of
      moving on. Suspects to check first: `early_game.teach_hm_move()` and `ensure_hm_learner()`
      (`early_game.py` ~4280-4440) — specifically whether the post-teach success test actually
      observes the learned move, or whether the caller re-enters because its own guard still
      reads False. ‼ This is the "guard every did-it-work?" shape, and a bounded loop re-entered
      by its dispatcher is still infinite (KI-34).
      **USER SEQUENCING: fix this AFTER the roster feature lands and BEFORE resuming story
      chapters.** Cheap to reproduce — `ensure_hm_learner` is wired for exactly two moves
      (Rock Smash `story_mode.py:2793`, Surf `:2967`).

- [x] `#24-movepoolcounters` — **SHIPPED 2026-08-07. It is the fix for `#24-winonaground`.**
      Winona: **0 huntable candidates -> 1** (Slugma @ FIERY_PATH via `move:Rock Throw@L15`).
      Norman control unchanged (Machop @ FIERY_PATH via type); Wattson 1 -> 2.
      TWO changes, both required: (a) movepool-aware candidates behind three gates — damaging
      (`base_power > 0`), obtainable (level-up only, known at capture), credible (`bp x 2.0 x
      STAB >= 75`); (b) **huntability added to `tier`** — without it the huntable candidate
      ranked **42 of 43** behind unhuntable MAGMA_HIDEOUT Geodudes and `max_results=5` truncated
      it away, leaving the feature inert. `repro_movepool_counter_candidates.py` +
      `probe_counter_candidates_offline.py` (with a positive control).
      ‼ Original measurement note kept below — its "+2, will not fix Winona" conclusion was
      WRONG, because I had not yet found the Grass-only filter that excludes her one type match.

- [x] HISTORY — `#24-movepoolcounters` (original measurement) — **USER DIRECTIVE 2026-08-07.**
      > "some pokemon can learn moves of types that can be a counter so its not just the pokemon
      > type, it can be the moves they learn… know the difference between damaging moves,
      > passive/defensive/stat boosting/debuff moves and area/effect moves as well as status
      > moves with no damage"

      `counter_plan.py:155-157` today keeps a candidate only if
      `{t.name for t in species.types} & needed` — pure species typing.
      **Measured with `tools/story-dev/probe_movepool_counters.py` over all 11 huntable grounds:**
      | gating | Winona | Norman | Wattson |
      |---|---|---|---|
      | by species TYPE (today) | 1 | 1 | 1 |
      | + any learnable move of a needed type | +82 | +47 | — |
      | **+ DAMAGING, LEVEL-UP only, power×2.0×STAB ≥ 75** | **+2** | **+0** | **+0** |
      ‼ **The naive version is WORSE THAN TODAY.** Almost the entire raw gain is `TM13 Ice Beam` /
      `TM14 Blizzard` (Gen 3 TMs are single-use and we almost certainly do not own them) and
      `HM06 Rock Smash` at **20 power** — the exact case `CREDIBLE_ANSWER_POWER = 75` was
      calibrated to reject ("a 20-power HM is 2.0x against Normal and still loses to Slaking 27
      times running"). Unfiltered, every Zigzagoon becomes a Norman counter.
      **THREE GATES ARE MANDATORY, in this order:**
      1. **DAMAGING ONLY** — `move.base_power > 0`. Everything at 0 is status / stat-change /
         field effect and cannot answer a type weakness: Toxic, Growl, Sunny Day.
         ‼ **Smog is NOT in that group** — our data has it at **20 bp Poison, `effect=POISON_HIT`**.
         Classify on `base_power`, never on the name or on the presence of a secondary effect.
      2. **OBTAINABLE** — level-up moves within reach of the catch band, or a TM/HM **we own**.
         Never "could learn if we had TM13".
      3. **CREDIBLE POWER** — reuse the existing `power × effectiveness × STAB >= 75`.
      **The whole actionable gain is 2 Winona candidates:** Baltoy learns **Rock Tomb** (L15,
      50bp) on ROUTE111; Slugma learns **Rock Throw** (L15, 50bp) on FIERY_PATH.
      ⇒ Worth building — it is the correct model and it widens a chain that is now **75% of all
      non-finishes** — but it will NOT by itself fix Winona, and it must not be sold as the fix.
      Do `#24-winonaground`'s real diagnosis first.

- [x] `#24-counterdesertgate` — **FIXED 2026-08-07, same day it was found.**
      `counter_plan` now checks `AREA_ITEM_PREREQ` per candidate location and skips the area
      unless the item is in the bag; fails CLOSED, and sits before the reachability branch.
      **A/B on the item, both arms, control in both:**
      | arm | Winona's best_huntable |
      |---|---|
      | bag HOLDS Go-Goggles | Baltoy @ ROUTE111 `via=move:Rock Tomb@L15` (admitted) |
      | bag EMPTY | **Slugma @ FIERY_PATH** `via=move:Rock Throw@L15` (ROUTE111 refused) |
      | control | Norman → Machop @ FIERY_PATH, unchanged in both |
      ‼ Both arms run on purpose — the gate fails closed, so a one-armed offline test would show
      the right answer for the wrong reason. `probe_counter_item_gate.py`.
      ‼ **Deliberately NOT done by flipping `POKEBOT_AREA_ITEM_GATE`** (one character, and it
      would have re-litigated the measured 2026-08-04 ruling). That ruling was about TRAINING,
      where a bad pick costs one trek; a counter hunt gets ONE attempt per boss per run, so a bad
      pick costs the boss. `repro_movepool_counter_candidates.py` §5 asserts the flag stays off.
      **NO OUTCOME PROOF YET** — needs a batch: `CAUGHT Slugma` > 0 with `CAUGHT Machop` unchanged.

- [x] HISTORY — `#24-counterdesertgate` (original diagnosis) — **NEW 2026-08-07, ROOT-CAUSED.**
      Batch `20260807-200030`: **7 Baltoy hunts to ROUTE111 (25,55), 0 caught.**
      `AREA_ITEM_PREREQ = {ROUTE111: "Go-Goggles"}` gates the desert, and
      **`counter_plan.py` references `AREA_ITEM_PREREQ` ZERO times** — it consults only
      `AREA_PREREQ`. The planner offers the desert tile (which sits NORTH of the goggles gate),
      the bot walks cross-Hoenn, cannot enter, and spins wherever it stopped.
      ‼ **PRE-EXISTING.** The gate exists in `_counter_area_allowed` behind
      `POKEBOT_AREA_ITEM_GATE` and is **OFF BY DEFAULT since 2026-08-04** ("THIS GATE COST MORE
      THAN IT SAVED", measured). `#24-movepoolcounters` only made it load-bearing — before it,
      ROUTE111 never won Winona's ranking.
      ‼ **DO NOT just flip `POKEBOT_AREA_ITEM_GATE` on.** That was measured and rejected for
      TRAINING, where a bad pick costs one trek. A COUNTER HUNT gets **one attempt per boss per
      run**, so a bad pick costs the boss. **Fix `find_counter_candidates` to honour
      `AREA_ITEM_PREREQ` for its own destination choice only** — that demotes Baltoy@ROUTE111
      below Slugma@FIERY_PATH, a ground already proven by Norman's 6-of-7 catch rate.
      **Acceptance:** `counter hunt — … FIERY_PATH … Slugma` appears and `CAUGHT Slugma` > 0,
      with `CAUGHT Machop` (control) unchanged.

- [x] `#24-huntreachproof` — **PART 1 SHIPPED AND BATCH-CONFIRMED 2026-08-08.**
      **CONVERSION 15% → 50% (5/33 → 10/20), z = +2.73 — RESOLVABLE ✅.** Hunts fell 33 → 20 and
      catches DOUBLED. `could not reach` 72 → 53; `global watchdog` 9 → 0.
      ‼‼ **PART 2 AS PLANNED IS CANCELLED — the batch REFUTED my (anchor → ground) hypothesis.**
      `Numel @ FIERY_PATH` went 5 hunts/0 caught → **7 hunts/3 caught**, so FIERY_PATH *is*
      reachable from Mauville. The old 0/5 was **destination ORDERING**: the ladder spent the
      boss's single hunt on ROUTE111/ROUTE116 first and the bound was consumed before the good
      ground was tried. The per-anchor sweep campaign would have fixed a problem that does not
      exist. **Do not run it.**

- [x] `#24-slugmaspin` — ‼ **BATCH-CONFIRMED 2026-08-09** (`x4-runs/20260809-081643`, code
      `16283010`, VERDICT OK): the fence reverses the regression on the species that carried it —
      **`CAUGHT Machop` 0/7 → 6/7, z = +3.24 (RESOLVABLE)** — and **FALSE catches 10 → 0**, so
      reported (9) now equals REAL (9). Overall REAL conversion 15.0% → 39.1% (z = +1.76,
      directional), statistically indistinguishable from the 45.0% before the regression.
      ‼ The written bar of "≥50%" was itself mis-derived — that figure counted REPORTED catches;
      on REAL catches the historical pair is 15.2% → 45.0% (z = +2.39). See `08-MISTAKES` 2026-08-09.
      ‼ **Promotion to `custom-pokebot/` is READY and NOT DONE — it needs an explicit user YES**
      (`CLAUDE.md` standing directive). Until then production runs this regression WITHOUT its fix.

      HISTORY — **FIXED 2026-08-08, same day it was found. It was the SUCCESS TEST, not
      the spin.** `party_counter_slot()` checked the caught mon's OWN TYPE, so a Slugma (Fire)
      caught for Winona (Rock/Ice/Dragon) was never recognised: `_stop()` never fired, the spin
      ran to budget, the hunt reported nothing caught. **34 Slugma encounters, 0 registered.**
      `#24-movepoolcounters` taught the PLANNER about movepools and left this behind.
      **Fix:** also accept a mon that knows a DAMAGING move of a needed type. Lenient by design
      (no credible-power floor — a fresh L15 Slugma knows Rock Throw and that IS success; the
      strict question belongs to `_boss_plan_is_hopeless`).
      `repro_counter_move_answer.py` — 4 cases, incl. Sandstorm (Rock, **0 power**) correctly
      REJECTED, pinning the damaging-only rule. Suite 6/6.
      ‼ **NO OUTCOME PROOF YET.** Acceptance next batch: `counter hunt CAUGHT Slugma` > 0, and
      overall CONVERSION at or above this batch's 50%.

- [x] `#24-slugmaspin` (original finding) — **Winona's rung FIRES but does not convert.**
      `Slugma @ FIERY_PATH`: **5 hunts, 0 caught** — on the same ground that converts 6/8 for
      Machop and 3/7 for Numel in the same batch, so **it is not travel**. This is the movepool
      work reaching production for the first time; the catch is the last missing step.
      Likeliest causes, in order: the **10% encounter rate** (vs Machop 15% / Numel 30%) against
      the spin budget; or the catch-on-sight branch not targeting the species.
      **NEXT PROBE: instrument the Slugma spin — arrivals, encounters seen, species matched —
      BEFORE changing anything.** Winona is 6 of 20 non-finishes.

- [x] `#24-huntreachproof` (part 1 detail) — **narrowing.** `hunt_ground_tile(require_driven=...)`, strict by default: a counter hunt may only
      target `HUNTING_GROUNDS` (driven reach-and-leave evidence), never the `TRAINING_GRASS`
      fallback. A/B: Norman control unchanged; Wattson 5 huntable/3 grounds → 1; Winona 2/2 → 1;
      all now FIERY_PATH. `POKEBOT_HUNT_ANYGROUND=1` reproduces the old arm.
      `repro_hunt_driven_grounds.py`; suite 8/8 green.
      ‼ **A REDUCTION, NOT A CURE:** `Numel @ FIERY_PATH` was **5 hunts, 0 caught** on the SAME
      ground Machop converts 5/5 from — reachability is a property of the **(boss anchor →
      ground) PAIR**. Part 2 is per-pair driven sweeps from real boss anchors.
      ‼ **Acceptance for the next batch is CONVERSION** (hunts started vs `counter hunt CAUGHT`):
      33 → 5 (15%) now, 18 → 7 (39%) before. NOT the finish rate, NOT the candidate count.

      **PART 2 PLAN — every input verified present 2026-08-08, so this is ready to execute:**
      Drive `_navigate_riding_out(ground, tile)` from each BOSS ANCHOR to each candidate ground,
      **both directions**, and add only the pairs that pass. That is the bar `HUNTING_GROUNDS`
      already sets and the one FIERY_PATH already meets.
      * probe: `tools/story-dev/probe_counter_reachability.py` (exists — drives the REAL
        navigation, not `calculate_path`, which cannot cross warps and has caused this exact
        mistake before).
      * anchors (from the six `_prepare_for_fight` cfgs) and the saves that sit on them:
        PETALBURG → `norman_done.ss1`; MAUVILLE → `mauville_wedge.ss1` / `wattson_done.ss1`;
        FORTREE → `fortree_gym_wedge.ss1` / `ch13_fortree_door.ss1`;
        LAVARIDGE → `lavaridge.ss1`; DEWFORD → `dewford.ss1`; RUSTBORO → `rustboro.ss1`.
      * grounds to test per anchor: FIERY_PATH, ROUTE111, ROUTE116, ROUTE117, ROUTE118.
      ‼ **The single most informative pair is MAUVILLE → FIERY_PATH.** Numel went 5 hunts / 0
      caught from there while Machop goes 5/5 from Petalburg to the SAME ground — so that one
      run decides whether the (anchor, ground) model is right.
      ‼ Do NOT run these while a batch is using the box: 8 lanes already occupy ~8 cores, and a
      contended probe is exactly how this project has produced false timing results before.

- [x] `#24-huntreachproof` (original finding) — ‼‼ **TOP ITEM 2026-08-08. Only ONE counter rung has ever worked, and
      `#24-movepoolcounters` widened the set with destinations the bot CANNOT TRAVEL TO.**
      Batch `20260808-095721`, conversion by target:
      | species | hunts | caught |
      |---|---|---|
      | **Machop @ FIERY_PATH** | 5 | **5 (100%)** |
      | Wingull / Nincada / Numel / Oddish / Baltoy / Taillow | 28 | **0** |
      `could not reach` **72**, `Could not find a path` **45**, `hunt found nothing` **0** —
      **travel failures, not catch failures.** Hunts 18 → 33 while catches fell 7 → 5.
      **ROOT CAUSE:** `huntable = reachable AND hunt_tile is not None`, and **`reachable` is a
      PREDICTION** (`_counter_area_allowed`'s hop budget + region oracle) that is wrong for 28 of
      33. `hunt_ground_tile`'s whitelist is evidence-backed for STANDING AND SPINNING, but its
      `TRAINING_GRASS` entries were two-way swept **for training, from training anchors** — not
      for a hunt firing from a boss anchor. `HUNTING_GROUNDS` — the table that encodes *driven,
      reach-and-leave* evidence — still has **one** entry, FIERY_PATH, and that is the only rung
      that converts. Not a coincidence.
      ‼ **Plausibly WORSE than before:** Winona used to stop immediately; now she burns a
      cross-Hoenn trek and then stops, and the hunt is bounded to ONE attempt per boss per run —
      so a failed destination costs the boss, not a trek. `no super-effective answer` rose from
      10 of 14 (71%) to **19 of 23 (83%)** of non-finishes. (Finish 41.7% → 25.8% is z = −1.24,
      NOT resolvable — the concern rests on the conversion counters, not on the rate.)
      **FIX:** require DRIVEN evidence from the anchor the hunt fires from — the bar
      `HUNTING_GROUNDS` already sets and FIERY_PATH already meets. Either sweep candidate grounds
      from real boss anchors and add them, or have the ladder demote a destination that has
      already failed to travel. ‼ Do NOT simply widen `HUNTING_GROUNDS` on a guess — its whole
      value is that every entry is measured.

- [x] `#24-progressiongate` — **SHIPPED 2026-08-08.** `AREA_PREREQ[FIERY_PATH] = "rocksmash"`,
      resolved by `_party_can_rock_smash()` (move AND `BADGE03_GET`, fails closed).
      **DECOMP-VERIFIED**: `src/party_menu.c:122` — `FIELD_MOVE_ROCK_SMASH, // FLAG_BADGE03_GET`.
      A/B: pre-Wattson **0 huntable** (was the circular Numel @ FIERY_PATH); post-Wattson 1.
      Norman control preserved. Suite 8/8.

- [x] `#24-r116sweep` — ‼ **ANSWERED 2026-08-09: DO NOT ADD ROUTE116 to `HUNTING_GROUNDS`.**
      Driven sweep from the newly captured, verified anchor `saves/mauville_prewattson.ss1`
      (MAUVILLE_CITY (19,15), **badge03=False**, party L16-L20):
      ```
      [sweep] RESULT ground=ROUTE116 arrived=False left=False badge03=False verdict=DO NOT ADD
      ```
      ‼ **READ THE FAILURE PRECISELY — it is not "Route 116 is unreachable".** The journey
      SUCCEEDED: the bot reached ROUTE116 in ~32,000 frames and stood at **(65, 11)**. The
      *intra-map* leg then failed — `Could not find a path from (65/11 @ ROUTE116) to
      (11/7 @ ROUTE116)`. `(11, 7)` is `RUSTBORO_TRAINING_GRASS`, a tile chosen for the
      **pre-Roxanne** era when the route is entered from the WEST; the counter hunt arrives
      from the EAST. `probe_r116_east_grass.py` (2 positive controls, both PASS) measured the
      split: from the east arrival **0 of 138** grass tiles are reachable (17 of 151 walkable,
      a pocket at x 64-78); from the west **136 of 138** are. Logged as **KI-49**.
      **CONSEQUENCE FOR WATTSON — this closes handoff concern #5.** His only legal pre-badge
      counter (Nincada @ ROUTE116) is **not huntable from where the hunt fires**. Combined with
      `#24-progressiongate` (his other option is behind him), **Wattson has no legal huntable
      counter**, and the chain stopping honestly is the CORRECT behaviour, not a gap to fix.
      Beat him with levels/lead. ‼ Do NOT relax the narrowing to manufacture a candidate —
      permissiveness measured 28 wasted treks and 15% conversion; the narrowing took conversion
      to 50% (z = +2.73).
      ‼ **The one thing that could revisit this is KI-49, not the sweep**: if journey planning
      learns to pick an entrance from which the tile is reachable, ROUTE116 becomes worth
      re-sweeping. Until then the verdict stands on driven evidence.

      HISTORY — **TOOL BUILT 2026-08-09, and the two anchors first tried were both invalid;
      the probe itself is what proved it.**
      New `--driver groundsweep` (`SWEEP_GROUND=MAP:x,y SWEEP_RETURN=MAP:x,y`) drives
      `_navigate_riding_out` there and back and prints
      `arrived=… left=… badge03=… verdict=ADD/DO NOT ADD`.
      ‼ It reports `badge03` and the party ON PURPOSE, because that is what exposed both bad
      anchors:
      | save | what it actually is | verdict |
      |---|---|---|
      | `mauville_wedge.ss1` | badge03=False but starts INSIDE the gym at (10,0); leg 1 failed stuck at (4,13) | wrong position — prep runs from the CITY |
      | `wally_done.ss1` | **lone Mudkip L14**, no Devon goods, no PokéNav, no Rustboro rival — the PETALBURG tutorial Wally, not the Mauville one | wrong ERA entirely |
      ‼ **`probe_counter_reachability.py`'s own docstring already warned about this** — *"Anchors
      are verified on load, never trusted by name — several saves in this directory have proven
      misnamed"* — and I ran two before reading it. **Verify the anchor's era and position BEFORE
      spending a run.**
      ✅ **ANCHOR OBTAINED 2026-08-09 — the blocker is gone.** `probe_anchor_inventory.py` read
      all 60 saves and answered the question properly for the first time: **none of them** stood
      in MAUVILLE_CITY with badge03 unheld, so the anchor did not exist and no third guess would
      have found it. It was then MADE with the new `--driver anchorstory` (the real story bot
      plays until it stands on the wanted map, then snapshots; `CAPTURE_FORBID_FLAG=BADGE03_GET`
      guarantees the era) and verified by the inventory probe as a separate instrument:
      **`saves/mauville_prewattson.ss1` — MAUVILLE_CITY (19, 15), badges [1, 2], party L16-L20,
      controllable**, captured in 13,666 frames.
      Run the sweep with:
      `SWEEP_GROUND=ROUTE116:11,7 SWEEP_RETURN=MAUVILLE_CITY:19,15 --driver groundsweep`
      (return tile 19,15 — the anchor's own tile, which the bot provably stood on; 22,6 is
      unverified and Mauville's walkability is exactly what KI-48 shows is not safe to assume).
      ‼ Do not read the `wally_done` run as evidence: `arrived=True` there says Route 116 is
      reachable from PETALBURG in the early game, which is not the question.

- [x] `#24-battleitems` — ✅ **DONE, PROMOTED 2026-08-10 (user-approved), zero source drift.**
      Policy unit-proven (`repro_battle_items.py`, 27 checks, no emulator); a real
      `battle_action_use_item` index-space bug found and fixed underneath it (5 requests → 1
      potion consumed, became 3 → 3); index space proven CONDITIONAL and handled by a
      self-correcting flip; validation batch `20260810-082509` passed its acceptance test
      (flips **20 → 2**, both-spaces-failed **10 → 0**).
      ‼ **OUTCOME UNPROVEN and that is on the record** — finish rate across the four item-era
      batches reads 25.0 → 33.3 → 16.1 → 28.6% at n≈30, nothing resolvable. It was promoted
      because the mechanism is proven and bounded, not because outcomes moved. **Any follow-up
      must be graded on BATTLE-level metrics** (`probe_item_index_space.py`,
      `probe_boss_healing.py`), never the finish rate.
      HISTORY — **USER DIRECTIVE 2026-08-09: "use items intelligently and
      strategically." BUILT, ROOT-CAUSED, FIXED — but its OUTCOME EFFECT IS UNMEASURED.**
      Motivated by measurement: `Slaking` healed **27 times, median +81 HP** in batch
      `20260809-155844` while the bot never used an item; 61.8% of boss-length battles show an
      opponent heal; boss losses end ~88% of non-finishing runs.
      * `modules/story/battle_items.py` — PURE policy (heal amounts from `items.json`, never
        memory). Four rules: only below 35% HP; **cheapest sufficient** item; **never heal into a
        losing race**; **bounded per battle** (the opponent heals too — unbounded is an infinite
        battle, the KI-34 shape). `repro_battle_items.py`: **27 checks, ALL PASS**, no emulator.
      * `StoryItemBattleStrategy` — TRAINER battles only, fails open, so wilds/training/catching
        are bit-identical to before.
      * ‼ **Found and fixed a real bug in `battle_action_use_item`**: it fed a BATTLE-order index
        into a PARTY-MENU scroll, so item use silently did nothing whenever the active mon was not
        at index 0 (5 requests → 1 consumed). After the fix: **3 requests → 3 consumed, Blaziken
        `23/120` → `120/120`**. Ball throwing passes no target and never enters that branch.
      * A **no-op guard** remains: if a request does not raise HP by the next decision, items are
        disabled for that battle (bounds the cost to one turn if execution ever breaks again).
      **NEXT: a batch.** Acceptance should be **boss-battle win rate**, not the finish rate. ‼ Do
      NOT quote the fixture's `badge=True` as proof — it reproduced even when items did nothing.

- [ ] `#24-r110mauville` — **NEW 2026-08-09, MEASURED (KI-48).** `_navigate_riding_out` cannot
      walk ROUTE110 → MAUVILLE_CITY: **3/3 identical deterministic failures** at (16, 89), with
      the planner enumerating only Mauville's **six building doors** and never the map
      connection. Story mode makes the same trip every run, so it is a gap in the direct
      navigation entry point, not a map fact. Repro is ~1,400 frames (see KI-48).
      ‼ A door-warp transition race is **RULED OUT** by a retry-after-settle A/B — do not
      re-test it. ‼ Do NOT assume it explains the batch's 72 `could not reach` events without a
      measurement that could discriminate.

- [x] `#24-r116sweep` (original framing) — **NEW 2026-08-08.** His only LEGAL pre-badge answer is **Nincada @ ROUTE116** (verified
      Bug/**Ground**; ROUTE116 carries no prereq), and `#24-huntreachproof` part 1 removed it
      because ROUTE116 is in `TRAINING_GRASS`, not `HUNTING_GROUNDS`.
      ‼ **Do NOT relax the narrowing to get it back** — permissiveness measured 28 wasted treks
      and 15% conversion; the narrowing took conversion to 50% (z = +2.73). **EARN the entry:**
      sweep ROUTE116 from Wattson's real anchor (**MAUVILLE**) with
      `probe_counter_reachability.py`, both directions, and add it to `HUNTING_GROUNDS` only if
      it passes.
      ‼ Do not assume it will: Nincada @ ROUTE116 was **5 hunts, 0 caught** in batch
      `20260808-095721`. The sweep exists to answer that, not to confirm a hope.

- [x] `#24-progressiongate` (original finding) — ‼‼ **USER-IDENTIFIED 2026-08-08, VERIFIED. The counter planner has
      NO progression model, and for Wattson it proposes a counter that is behind Wattson.**
      > "I think Slugma is not available before Wattson… keep this sort of logic in mind (pokemon
      > availability). In this instance Slugma is gated behind Rocksmash which you can only use
      > after beating Wattson"

      **Verified with the real `find_counter_candidates`** against a pre-Wattson team (L22):
      ```
      WATTSON needs Ground -> only huntable candidate: Numel @ FIERY_PATH (30%)
      ```
      **That is CIRCULAR.** Fiery Path's only two doors are on ROUTE112; the Mauville→Route 112
      corridor is sealed by a Rock Smash rock at ROUTE111 (18,101) (measured, `#24-smashroute`);
      and Rock Smash **field use requires BADGE03** — Wattson's own badge (`get_rock_smash_hm`
      docstring). So every Fiery Path species — Numel, Slugma, Machop, Torkoal, Koffing — is
      unobtainable until Wattson is already beaten.
      **`FIERY_PATH` has NO entry in `AREA_PREREQ` or `AREA_ITEM_PREREQ`** — confirmed, both
      return `None` — so the planner treats it as freely reachable at any story stage.
      ‼ **`#24-huntreachproof` part 1 made this the ONLY option for Wattson.** Before the
      narrowing he was also offered ROUTE111/ROUTE116 (unreachable in practice, but not
      circular). Now the single surviving candidate is one he gates himself. That is a real
      consequence of my change and it was invisible to every metric I was watching, because
      conversion counts catches and this rung can never even start.
      **FIX:** teach the gate about FIELD MOVES / BADGES. `AREA_PREREQ` already carries a
      vocabulary (`"surf"`, `"region"`) and `_counter_area_allowed` already resolves `"surf"`
      against the party — add `"rocksmash"` (badge-checked) and populate FIERY_PATH, plus any
      other ground behind a field move.
      ‼ **Every entry is a GAME FACT — verify each from the decomp or a live probe, never from
      recall.** The three facts above are already measured and cited; anything added beyond them
      needs the same treatment.
      ‼ **The general rule the user is asking for, beyond this instance:** a counter/hunt target
      is only valid if its LOCATION is reachable AT THAT POINT IN THE STORY. Availability is a
      function of story progress, not just of the encounter table.

- [x] `#24-teachmsgstall` — ✅ **FIX SHIPPED 2026-08-11 AND KEPT; ⚠ REOPENED THE SAME DAY** because
      batch `20260811-130454` showed it had **no measurable production effect** (success 38/47 vs
      38/42 pre-fix, **z = -1.28 NOT resolvable**; the new `already-advanced` exit fired **ZERO**
      times in 85 teaches). The one-frame `Task_ReplaceMoveYesNo` window was real and
      decomp-confirmed, and the fix closes it and costs nothing — but **it was not the dominant
      production cause, and another path to `exhausted` remains unfound.** Promoted 2026-08-11,
      user-approved, verified DRIVEN in `custom-pokebot` as the same A/B, frame-for-frame identical.
      📚 **The full 344-line investigation — the decomp trace, the A/B, the batch statistics and the
      reopening analysis — is ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md` (moved 2026-08-16 on the
      3600-line budget). Nothing was deleted.** ‼ The live summary of its status is the table row
      for `#24-teachmsgstall` near the top of this file; this entry is its history.
- [x] HISTORY — `#24-teachmsgstall` (original characterisation) — **NEW 2026-08-07, THIRD teach bug.**
      All **9** teach failures in batch `20260807-160545` share one signature:
      ```
      tasks=['ListMenuDummyTask', 'Task_ContinueTaskAfterMessagePrints']   9 of 9, identical
      move=Surf                                                            9 of 9
      post_select=exhausted (7)   |   post_select=replace-prompt (2)
      ```
      A message never completes with the bag list still up, so the teach rides out the full
      9,000-frame cap and Surf is never learned.
      ‼ **`post_select` DOES NOT MATTER** — the two that reached the replace prompt died in the
      same place. That rules out path selection as the cause, and rules out `#24-teachpathrace`
      (my 2026-08-07 fix) as the culprit: it changed the shape (`instant-learn` → `exhausted`)
      because it stopped the flow mislabelling the path, which **revealed** this stall rather
      than creating it.
      ‼ 4 → 9 failures is **z = +1.05, NOT resolvable** — do not call it a regression. Teach
      SUCCESSES rose 33 → 38 over the same window.
      **NEXT STEP:** reproduce with `--driver teachfull TEACH_ITEM=HM03` on a save whose party
      matches the failing shape (a 4-move Marshtomp-line mon that already knows Rock Smash), then
      instrument what `Task_ContinueTaskAfterMessagePrints` is waiting on. Every failure is Surf
      and every mon already carries an HM — worth checking whether the HM-slot exclusion in
      `replace_slot` picking leaves no legal choice and the game silently refuses.

- [x] `#24-winonaground` — **SOLVED 2026-08-07 by `#24-movepoolcounters`. The real cause was
      neither the whitelist nor reachability: across all 11 huntable grounds Winona's needed
      types appear ONCE (Geodude @ ROUTE111) and it is a **Rock Smash** encounter, which the
      `method == "Grass"` filter drops — leaving zero candidates.** She now has Slugma @
      FIERY_PATH via Rock Throw. ‼ My first two stated causes were both wrong; the history is
      kept below because the wrong turns are the lesson.

- [x] HISTORY — `#24-winonaground` (wrong-cause history) — ‼‼ **MY STATED CAUSE WAS WRONG.**
      I wrote that the huntable whitelist was `{FIERY_PATH, ROUTE116, ROUTE117, ROUTE102}` and
      contained no Rock/Electric/Ice ground. **False.** I grepped for named `*_TRAINING_GRASS =`
      CONSTANTS instead of reading the `TRAINING_GRASS` TABLE, which has **10 entries**:
      ROUTE101/102/103/111/115/116/117/**118**/119/121, plus FIERY_PATH from `HUNTING_GROUNDS`
      = **11 huntable grounds**.
      * **ROUTE118 (29,15) — Electrike, the named Winona answer — is ALREADY whitelisted.**
      * **ROUTE111 hosts Geodude (Ground/Rock, rate 100%, Lmax 20)** — a by-TYPE Rock answer to
        Winona that is already huntable.
      So there IS a candidate and there IS a swept ground. **Do NOT sweep ROUTE118; it is done.**
      The failure message is `no huntable counter candidate (**nothing reachable** with a proven
      spin tile)` — the rejection is downstream of the whitelist, in reachability or in
      `best_huntable`'s cost/level gates. Prior evidence points the same way: 2026-07-30 measured
      `Electrike @ ROUTE118 (29,15) — navigation FAILED, 255 frames`.
      **NEXT PROBE:** call `counter_plan.huntable_candidates()` for Winona's needed types from a
      REAL pre-Winona anchor and log the rejection reason PER CANDIDATE. Do not guess which gate
      it is — four gates can produce this one message.
      ‼ **The lesson (3rd time this session): I read a proxy for the data instead of the data.**
      Same class as grepping a gitignored tree and as reading the profile dirs with a date glob.

- [x] HISTORY — `#24-winonaground` (superseded wrong text) — ~~Winona's counter can NEVER be hunted: the huntable
      whitelist contains no ground that hosts a Rock/Electric/Ice wild.~~
      Measured in batch `20260807-102552` — the counter chain's remaining failure class, and with
      whiteouts now addressed it is the **top one** (`no super-effective answer` = 5 of 14
      non-finishes: Winona 2, Norman 2, Wattson 1):
      | marker | count | reading |
      |---|---|---|
      | `counter hunt — going to FIERY_PATH (18,19) to catch Machop` | 7 | Norman's rung |
      | `counter hunt CAUGHT Machop` | 6 | **86% catch rate — this rung WORKS** |
      | `counter training failed` | **0** | training is fixed (was 7 of 7 failing in batch 4) |
      | `already hunted a counter for Winona … (blocked: no huntable counter candidate)` | 8 | ‼ |
      | `no huntable counter candidate (nothing reachable with a proven spin tile)` | 10 | ‼ |
      **ROOT CAUSE — an unfilled evidence table, not a bug.** `hunt_ground_tile()` is a
      deliberate WHITELIST that fails closed, and its whole universe is:
      `HUNTING_GROUNDS` = **{FIERY_PATH}** plus `TRAINING_GRASS` = {ROUTE116, ROUTE117, ROUTE102}.
      Norman's Machop lives on FIERY_PATH and Wattson's Nincada on ROUTE116, so those rungs work.
      **Nothing in those four maps hosts a Rock/Electric/Ice wild**, so Winona's rung resolves to
      "no candidate" every single time, then burns its one-hunt-per-boss bound saying so.
      ‼ The whitelist is CORRECT and must not be widened by guessing — its docstring explains why
      (the cost model ranks endgame maps as cheapest, so the raw planner offers Victory Road and
      Mirage Tower). **The fix is to SWEEP one ground and add it with evidence**, exactly as
      FIERY_PATH was added: ROUTE118 (Electrike, the previously-named Winona answer) is the
      obvious candidate.
      **What the sweep must prove** (the table's own bar): reach the tile FROM THE REAL ANCHOR the
      hunt fires from, and get back OUT — both directions, live, via `_navigate_riding_out`, not
      `calculate_path` (which cannot cross warps and has caused this exact mistake before).
      A catch-and-leave hunt never walks the onward heal leg, so that leg may fail (FIERY_PATH's
      does) without disqualifying the ground.

- [ ] `#24-ballstarve` — **NEW 2026-08-07.** `Cannot hunt a Surf learner: no Poké Balls and no
      money to buy any` — 4 occurrences + 1 whole run derailed, batch `20260807-102552`. Consistent
      with KI-43's note that catches rose while each restock still buys 10 balls. Pairs with the
      end reason `No party mon can learn Surf and the party is full — needs PC box management`,
      which the now-proven `#24-pcoverflow` withdraw path should be able to serve.
      ⚠ **MEASURED 2026-08-13 — the premise DOES NOT HOLD at `post_dive.ss1`, which does NOT
      close this item.** `probe_dive_learner_plan.py` reads **19 balls** (Poké 16 / Premier 1 /
      Great 1 / Master 1) and **$54,334** there — `affordable_poke_balls()` = 269, and the Mossdeep
      mart door is 27 waypoints away. So a hunt at the CURRENT era is not ball-starved.
      ‼ **This is a late-game anchor and the item was filed from a mid-game BATCH** (4 occurrences,
      Surf-era, party still small and poor). Ball starvation is plausibly a real EARLY/MID-game
      condition that simply does not reproduce this late. ⇒ **Do not close on this evidence** —
      it needs a measurement at the era the batch actually failed in. Recorded so the next reader
      does not re-derive "we have no balls" from a stale headline.

- [x] `#24-teachpathrace` — **FIXED 2026-08-07, same day it was found. Caught by the
      `#24-hmteachloop` telemetry in its FIRST batch — a SECOND, independent teach bug.**
      Batch `20260807-102552`: **33 of 37 teaches succeeded; all 4 failures were this**, on Surf,
      each burning the full 9,000-frame cap without learning the move.
      **FIX:** the instant-learn exit now requires POSITIVE evidence — a genuinely free move slot
      (`_free_slots` / `_may_instant_learn`) or `_knows()` — instead of the mere presence of
      `Task_HandleChooseMonInput`.
      **Live proof, both branches** (`--driver teachfull`; `TEACH_SLOT` picks the target):
      | target | moves before | post_select | ride_frames | result |
      |---|---|---|---|---|
      | Mightyena (4 moves) | Tackle/Taunt/Take Down/Bite | `replace-prompt` | 479 | learned, replaced Taunt |
      | Zigzagoon (3 moves) | Tackle/Growl/Surf | `instant-learn` | 252 | learned, replaced nothing |
      ‼ The second row is not optional: the fix GATES the instant-learn exit, so proving the
      replace path still works is only half a proof — a gate one notch too tight would strand
      every free-slot teach in the 900-frame loop, and the replace test cannot see that.
      `repro_hmteach_postlearn.py` §5 pins it (17 → 22 checks).

- [x] HISTORY — `#24-teachpathrace` (original report) — **found 2026-08-07 by the `#24-hmteachloop` telemetry.**
      2 failures in 24 teaches (~8%) in `20260807-102552`, both on **Surf**, both fatal
      (`not-learned-after-ride:hard-cap`, the full 9,000 frames, Surf never learned):
      ```
      TEACH EXIT reason=ride:hard-cap stall_peak=82 post_select=instant-learn move=Surf
        slot=4 replace_slot=1 frame=8999 tasks=['ListMenuDummyTask',
        'Task_BagMenu_HandleInput', 'Task_ScrollIndicatorArrowPair']
        moves=['Take Down', 'Mud Shot', 'Rock Smash', 'Muddy Water']
      ```
      ‼ **`post_select=instant-learn` on a mon with FOUR moves is a contradiction, and that is
      the smoking gun.** The post-select loop (`early_game.py`, `for _f in range(900)`) breaks on
      `"Task_PartyMenuReplaceMove" in t or "Task_HandleChooseMonInput" in t` and calls it the
      instant-learn path — but `Task_HandleChooseMonInput` is STILL UP for a while after the mon
      is chosen, so it wins the race before `Task_ReplaceMoveYesNo` appears. The guarded
      `if "Task_ReplaceMoveYesNo" in _tasks():` block is then skipped entirely, the replace
      prompt is never answered, and the flow rides out the cap stuck in the BAG
      (`Task_BagMenu_HandleInput`). `stall_peak=82` confirms it was churning, not frozen.
      **FIX SHAPE:** the instant-learn break must require positive evidence of a FREE SLOT (or of
      the move actually being known), not the mere presence of the party-menu task — a task that
      is present on BOTH paths cannot discriminate between them.
      ‼ **Pre-existing, not introduced:** that loop is untouched by the 2026-08-07 fix. It was
      invisible before because nothing logged which exit fired, and it was being absorbed into
      the "7/8/9/4 teach failures" that four budget rounds chased.

- [x] `#24-whiteoutloop` — **BOTH PARTS SHIPPED 2026-08-07.**
      **Part 1 (cfgs):** `flannery_fight` + `rival110_fight` added — the two fights that had NO
      boss cfg at all and were **48% of all defeats**. Team data decomp-verified
      (`sParty_Flannery1`: Numel 24 / Slugma 24 / Camerupt 26 / **Torkoal 29**;
      `sParty_MayRoute110*`: the ace is always the L20 evolved starter that counters yours).
      ‼ Neither carries a `grass` key, on purpose — `_prepare_for_fight` explicitly supports a
      grass-less cfg, and Lavaridge genuinely has none (two-way sweep, `jaggedgrass_probe.py`).
      Inventing a training tile is how KI-44 happened.
      ‼ Also corrected the Route 110 ace derivation to name TYPE PAIRS (Marshtomp =
      Ground/Water, Combusken = Fighting/Fire) — effectiveness against a dual-type is the
      PRODUCT, so the old primary-type-only version understated every matchup.
      **NEW `repro_boss_cfg_coverage.py`** asserts every measured defeat map has a cfg carrying
      ace data — fault-injected RED. ‼ It also caught two of my OWN wrong assumptions: Brawly's
      ace really is L19 against a (14,16) band (the band is a training target, not a range
      containing the ace), and the Rustboro rival's missing `ace_types` is fine because it
      recorded **0 defeats in four batches**.

- [x] HISTORY — `#24-whiteoutloop` (part 2) — **the hard plateau.**
      Confirmed as the **#1 end reason** of batch `20260807-102552`: *"too many whiteout
      recoveries in a row"* = **4 of 14 non-finishes (29%)**.
      **SHIPPED — the hard plateau.** `_boss_plan_is_hopeless` demanded BOTH a KO plateau AND
      "no credible super-effective answer", so an UNDERLEVELLED party holding a good move on
      paper never gave up (measured worst case: PETALBURG_CITY_GYM, **32 consecutive losses**,
      KOs stuck at 2-3 throughout). The type-chart answer test is a **prediction**; a long flat
      KO series is a **measurement**. Past `HARD_PLATEAU_LOSS_THRESHOLD = 12` the measurement now
      wins and the existing counter/training escalation runs instead of another identical attempt.
      ‼ **Keyed on FLAT KOs across two six-attempt windows, never on attempt count** — that is
      what honours KI-26's record of a run that lost **13 times** at ROUTE110 and then reached
      Fortree. `repro_boss_plateau.py` cases 8-10 pin all three behaviours (fires on flat;
      **does NOT fire on a climbing run**; leaves the original no-answer path untouched); 1-7
      still pass unchanged.
      **STILL TO DO (part 1):** real `_prepare_for_fight` cfgs for **Flannery / Gym 4** and the
      **Route 110 rival**. They have none, so none of this machinery runs there at all — and
      they are **48% of all defeats** (1,079 / 2,236 over four batches) and top-4 in 4 of 4.
      ‼ Needs verified game facts (training grass tile, heal centre, ace types/level) — probe or
      decomp, never recall. The Route 110 rival's ace depends on the player's starter.

- [x] HISTORY — `#24-whiteoutloop` (diagnosis) — **DIAGNOSED 2026-08-07 from stored logs. It is KI-26, generalised:
      uncapped boss re-attempts. Fix is specified and NOT yet implemented.**
      ‼ Measured NOT to be Mt. Pyre's: a run with 0 `MT. PYRE` mentions logged 3 whiteouts while
      heavy-Mt.-Pyre runs logged none. **The "show WHERE" ask is now answered** — every whiteout is
      preceded by `lost a battle at map (G,N) (defeat #K here; KO'd J of theirs first)`, so the
      map, the attempt ordinal and the progress signal were in the logs all along.
      * **48% of all defeats (1,079 / 2,236 across four batches) are at maps with NO
        `_prepare_for_fight` cfg** — ROUTE110 and LAVARIDGE_GYM (Flannery) are top-4 in 4 of 4.
      * **Re-attempting usually does not work:** of 53 sequences with ≥3 defeats at one map,
        the KO trend is **FLAT in 37, improving in 15, worse in 1**. Worst: 17 straight losses at
        Lavaridge with a constant `kos=[3]*17`; 32 straight at Petalburg.
      * `_boss_plan_is_hopeless` already has the right plateau test but demands **plateau AND no
        super-effective answer**, so an underlevelled party that HAS one never gives up.
      **FIX (2 parts, both deferred until the batch lands — never edit `sandbox-pokebot/` mid-batch):**
      1. Real `_prepare_for_fight` cfgs for Flannery and the Route 110 rival.
      2. A cfg-independent cap keyed on **flat KOs, not attempt count** — which is precisely what
         lets it honour KI-26's warning that a run losing 13 times still went on to reach Fortree.
      Full measurement + method in `05-KNOWN-ISSUES.md` KI-26.

- [x] ~~`#24-mtpyre-batch`~~ (superseded) — **NEXT ACTION. Batch Segment 14 before trusting any finish rate.**
      Every run that beats Winona now continues into Mt. Pyre, so run length and finish rate
      both change by construction. Read against the **52.0%** baseline (`20260805-075638`).
      Watch: does the Route 121 gate fire reliably from a real run's approach (the live proof
      started from a save already ON Route 121's north band)? Do the four summit-corridor Aqua
      grunts' sight-lines derail the ascent?

- [x] ~~`#24-mtpyre`~~ (superseded) — **‼ NOW UNBLOCKED (2026-08-05) AND THE TOP ITEM. First chapter past
      Winona.** 3 hops, one branch; the 2F-6F tower is a skippable side dungeon.
      `#24-cavethread` was its only blocker and is closed — the navigator already threads a
      3-warp cave in both directions, which is exactly MT_PYRE_SUMMIT's shape.
      ‼ **Pick plain walkable destination tiles — never a ladder/door/stairs warp tile** (see
      `08-MISTAKES.md` 2026-08-05; it costs one map of overshoot AND reports success).
      ‼ **FULLY SPECIFIED 2026-08-05 — `12-STORYMODE-DESIGN.md` §Ch14a** (ROM + pret decomp).
      The chapter is ONE COORD TRIGGER: step on `(23,7)` at `VAR_MT_PYRE_STATE == 0` and the
      scene gives the Magma Emblem and sets `FLAG_HIDE_JAGGED_PASS_MAGMA_GUARD` by itself.
      Completion test `get_event_var("MT_PYRE_STATE") >= 1` (name verified to exist).
      Measure `_navigate_riding_out(MT_PYRE_SUMMIT, (23,7))` FIRST — it may be the whole thing.
      ⏭ **BLOCKED ONLY ON: no post-Winona save exists.** See `#24-postwinona-save`.

- [x] `#24-r121topology` — **ANSWERED 2026-08-05: it is a STORY GATE, not topology.** See
      `#24-r121gate`. Superseded text below kept for the reasoning trail.

- [x] `#24-r121gate` — ✅ **CLOSED 2026-08-10: it is ALREADY BUILT. The "ready to build" header
      was the THIRD stale item found this week** (after `#24-leadcounter` and `#24-counters`
      phase 2), and it was caught only because the spec was verified before coding.
      In code: `ROUTE121_AQUA_GATE_TRIGGER = (25, 5)` (`early_game.py:6534`), the guard
      `get_event_var("ROUTE121_STATE") >= 1` (:6572), and `do_mt_pyre_summit()` (:6615),
      which the story run calls at `story_mode.py:3504`.
      ‼ The spec itself was re-verified against the decomp and is CORRECT: coord events at
      **(25,5) (25,6) (25,7) (25,8)** gated on `VAR_ROUTE121_STATE == 0`, grunts at
      (30,7)/(30,8)/(31,7), flag **914** `HIDE_ROUTE_121_TEAM_AQUA_GRUNTS`, and
      `Route121_EventScript_AquaGruntsMoveOut` ends with `setvar VAR_ROUTE121_STATE, 1`.
      ‼ Note the accessor names carry NO `FLAG_`/`VAR_` prefix — `get_event_var` returns −1
      for an unknown name, so `VAR_ROUTE121_STATE` would fail silently.
      HISTORY — **Fully specified, ready to build.**
      Three Team Aqua grunts at (30,7)/(31,7)/(30,8) seal Route 121's only corridor south
      (`FLAG_HIDE_ROUTE_121_TEAM_AQUA_GRUNTS` = 914, measured **False** = visible). Coord trigger
      **(25,5)-(25,8)** at `VAR_ROUTE121_STATE == 0` runs `Route121_EventScript_AquaGruntsMoveOut`,
      which removes them and sets the var to 1. Guard on `VAR_ROUTE121_STATE >= 1`.
      Spec: `12-STORYMODE-DESIGN.md` §Ch14-PRE. ‼ Use explicit adjacent-map legs, not one generic
      journey call — `calculate_path` spans only DIRECTLY CONNECTED maps.

- [x] ~~`#24-r121topology`~~ (superseded) — **DO THIS BEFORE ANY MORE NAVIGATION WORK ON MT. PYRE.**
      From ROUTE121 (21,5) — where the ROUTE120 connection lands — `calculate_path` reaches
      neither Route 121's own south edge nor ANY Route 122 tile, **with surf allowed**
      (`BADGE05_GET=True`, `party_has_surf=True`, both measured). So the blocker is topological,
      not a missing capability and not a tile-choice heuristic.
      **(1)** Dump ROUTE121 at FULL WIDTH — every dump so far covers only x=0-46 of **80**.
      **(2)** Reachability-sweep from (21,5) (`calculate_path` per sampled tile, the KI-39
      method). **(3)** Then decide if the Mt. Pyre route goes via LILYCOVE instead.
      ‼ Two `_connection_step` heuristics have already failed inside the untested assumption
      that Route 121 is traversable from the entry point. Measure first.

- [ ] `#24-connstep` — **WRITTEN, BOTH VARIANTS FAIL, GATED OFF (`POKEBOT_CONNECTION_STEP=0`).**
      It crosses the ROUTE120→ROUTE121 border the old code could not, then strands the bot in
      Route 121's north band (its own south edge is unreachable from the tile chosen). Cause:
      the candidate lattice scans `y` from the TOP, biasing north when the target is south.
      **Fix before enabling:** (1) aim the choice with `map_path`'s global `offset`/`level`;
      (2) remember rejected targets (`used_warps` pattern). **Then batch it.**

- [ ] `#24-connstep-batch` — **RUN A BATCH BEFORE ENABLING `#24-connstep`.**
      The connection step (shipped 2026-08-05, live A/B: old dies on ROUTE120, new reaches
      ROUTE121) has **no outcome measurement**. `navigate_to_anywhere` is used by every chapter,
      so a regression here is broad. Read the finish rate against the **52.0%** baseline
      (`20260805-075638`) and watch for journeys that now wander instead of failing fast.
      ‼ Known weakness to watch: the step target is a coarse-lattice tile, not aimed at the
      onward route, so it can land somewhere with less onward reachability than ideal.

- [x] `#24-postwinona-save` — **THE PRACTICAL BLOCKER FOR ALL Ch14 WORK. Do this first.**
      No save exists past Winona, so nothing in Mt. Pyre can be validated. A 2026-08-05 attempt
      drove Story from `fortree_gym_wedge.ss1` and ground through 10 Winona attempts (KO'ing
      3-4 of her 5 each) without converging — that save's team has no super-effective answer to
      Flying. Options: drive a fresh run to completion and keep the end state; or build the save
      from a run that already beat her (52% of batch runs do). Once it exists, commit it to
      `tools/story-dev/saves/` as `post_winona.ss1` — every Ch14 probe will want it.

- [x] `#24-magmahideout` — ✅ **DONE 2026-08-10. `GROUDON_AWAKENED_MAGMA_HIDEOUT` is SET, and
      `do_magma_hideout_chapter()` is wired into `story_mode.py` as Segment 15.**
      ```
      [magmahideout] RESULT groudon=True map=MAGMA_HIDEOUT_4F at=(15, 21)
        floors=['MAGMA_HIDEOUT_1F','MAGMA_HIDEOUT_2F_1R','MAGMA_HIDEOUT_3F_1R','MAGMA_HIDEOUT_4F']
        whiteouts=0
      ```
      Binary acceptance, no batch. Full chain driven: Mt. Pyre → Lilycove heal → Mauville heal
      **+ teach Strength** → R111/112 (Rock Smash rock cleared) → cable car → Mt. Chimney →
      Jagged Pass → coord trigger → two Strength pushes → 1F→2F_1R→3F_1R→4F → Maxie.
      ‼ **Maxie is approached ADAPTIVELY** — all four neighbours are tried at runtime, because the
      static read said `(17,21)` and the live arrival said `(15,21)`. The winning run used
      `(15,21)`. Every static claim about this dungeon has been wrong at least once.
      HISTORY — **IN PROGRESS 2026-08-10 (evening). Increments 1-3 WRITTEN;
      increment 1 driven-tested and iterating. Entry model CORRECTED twice today.**

      ‼‼ **THE ENTRY IS A STEP TRIGGER, NOT A WALK.** The door `JAGGED_PASS (16,18)` is covered
      by `METATILE_Lavaridge_RockWall` at runtime (`JaggedPass_OnLoad` →
      `..._ConcealHideoutEntrance`) while `VAR_JAGGED_PASS_STATE <= 1`. A coord_event on one of
      **(21,15) (22,20) (21,20) (14,15) (13,15)** runs `JaggedPass_EventScript_OpenMagmaHideout`,
      which opens the metatiles and sets the var to **2**. The var reaches 1 by itself
      (`JaggedPass_OnResume` checks for the Magma Emblem). **Use `(13,15)`** — 8-10 waypoints
      from the descent's arrival tiles vs 15-23 for the (21,*)/(22,*) trio.
      ‼ `calculate_path` said "(16,20) → (16,18), 2 waypoints" for that sealed tile, because it
      reads the ROM LAYOUT and cannot see a `setmetatile`. **A static PASS is not evidence on a
      map whose scripts rewrite metatiles** (`08-MISTAKES` 2026-08-10). This is the third wrong
      answer about this one door; the other two were "one-way ledges" and "a real south-facing
      ledge", both the same wall.

      **BUILT (in `modules/story/early_game.py`, all compile-clean):**
      `travel_to_magma_hideout_door()` · `open_magma_hideout_entrance()` ·
      `enter_magma_hideout()` · `do_magma_hideout()` · `do_magma_hideout_chapter()`.
      Driver `--driver magmatravel`; probes `probe_magma_anchor.py` (era gate, 4 controls),
      `probe_ch15_travel.py` (route), `probe_ch15_interior.py` (interior).
      ‼ **NOT yet wired into `story_mode.py`** — waiting on a green increment-1 run.

      **MEASURED THIS SESSION:**
      * anchor `post_mtpyre.ss1` VERIFIED READY (guard flag True, `MT_PYRE_STATE`=1, Emblem in
        bag; era control passes against `jagged_descent.ss1`).
      * ‼ **Ch14 hands over a WRECKED party** — 3 of 6 fainted, survivors at 21/117 and 18/109,
        lead's best move at 0 PP, **one Hyper Potion and no Revives**, and the nearest Pokémon
        Center is 276+ waypoints away (Mauville 276 / Fortree 432 / Lilycove 883). It dies ~61
        waypoints in, on ROUTE123. **The whiteout is the game's own recovery and StoryMode
        already handles it** (`on_whiteout` → True); the travel leg now heals at Lilycove and
        Mauville en route and survives.
      * the overland haul WORKS: run 3 reached **ROUTE112 (28,28)**, the cable-car station
        approach, after one whiteout.
      * ‼ **Lavaridge is NOT reachable from ROUTE112 by the live navigator** ("it is not
        walkable from ROUTE112", 3/3) although `calculate_path` scores it 66 waypoints. The
        staging heal there is now best-effort.

      ‼‼ **INCREMENT 3 IS BLOCKED ON `#24-strength` — MEASURED, NOT SUSPECTED.** The driven run
      entered 1F cleanly and stopped dead: `groudon=False map=MAGMA_HIDEOUT_1F at=(10,34)
      floors=['MAGMA_HIDEOUT_1F'] whiteouts=0`. A plain COLLISION flood (no elevation, no
      pathfinder — an independent instrument) shows 1F has **three components**: #0 **299 tiles**
      with the entrance (10,34) and `(25,34)→2F_1R`; #1 **70** with `(31,3)→2F_2R`; #2 **NINE**
      with `(20,22)→2F_3R`. `calculate_path` reaches **44** of #0's 299, and the boundary is
      **exactly three edges, all into Strength boulders** — `(7,23)→(7,22)`, `(7,23)→(6,23)`,
      `(8,22)→(7,22)`. The boulders ARE the gate.
      ‼ **The §Ch15 "shortest route" was WRONG and is corrected**: `(20,22)` is on that nine-tile
      island, i.e. an EXIT from 2F_3R, never an entrance. Real route (all legs verified connected
      to their arrival tiles — 2F_1R 383, 3F_1R 154, 4F 293):
      `1F (25,34) → 2F_1R → (17,33) → 3F_1R → (7,21) → 4F`, then stand `(17,21)` facing Left and
      TALK to Maxie at `(16,21)`. **Everything past 1F is already proven connected.**

- [x] `#24-strength` — ✅ **DONE 2026-08-10.** `ensure_strength_learner()` +
      `strength_push()` + `open_magma_hideout_1f()` in `modules/story/early_game.py`, proven by
      the chapter completing. Kept OUT of `obstacle_clearing` on purpose: that framework's success
      test is "the object is GONE", and a boulder is PUSHED — so the test here is **the boulder
      MOVED**, tracked by `local_id` (the player ends up standing on its old tile).
      ‼ Three bugs found only by driving it, all logged in `08-MISTAKES`: a one-frame press is not
      a walk; `walk_one_tile` leaves the D-pad HELD if abandoned early; and **a flag set by a
      script is not the end of that script** (the avatar was still `lockall`ed — that one cost two
      runs). The teach is done at a HEAL STOP to dodge `#24-teachmsgstall`.
      HISTORY — **NEW 2026-08-10. The blocker on `#24-magmahideout` increment 3, and the
      first hard dependency the story bot has had on an unsupported field move.**
      `obstacle_clearing.KNOWN_BUT_UNSUPPORTED` excludes `EventScript_StrengthBoulder` on purpose:
      *"a boulder is PUSHED, not removed; the success test cannot see it"* — i.e. the existing
      obstacle framework's success test ("is the obstacle gone?") cannot express this move. Two
      pieces are needed and they are independent:
      1. **A party member that knows Strength.** ✅ **CHEAPER THAN EXPECTED — measured
         2026-08-10 on both `post_mtpyre.ss1` and `magma_door.ss1`:**
         * **`HM04` is ALREADY IN THE BAG** (alongside HM02/HM03/HM06) — no Rusturf Tunnel trip.
         * **Badges 1-6 are held**, and field Strength is gated on the **Heat Badge (BADGE04)**,
           which is one of them.
         * ‼ **CORRECTION (measured minutes later, and it reverses the easy part).** I first
           wrote that `Zigzagoon L3` would carry it — it has a free fourth slot and is already
           the Surf slave. **`can_learn_tm_hm(HM04)` is FALSE for Zigzagoon.** Only **two** party
           members can learn Strength at all, and **both have four moves**:
           | slot | mon | moves | can learn HM04 |
           |---|---|---|---|
           | 0 | Mightyena L43 | Tackle / Taunt / Take Down / Bite | **True** |
           | 4 | Sceptile L43 | Rock Smash / Pursuit / Leaf Blade / Slam | **True** |
           | 1,2,3,5 | Zigzagoon, Swellow, Skitty, Castform | — | False |
           ⇒ the teach **costs a move slot on a fighter**. `hm_learner_slot()` picks the
           highest-level compatible mon and breaks the L43 tie toward slot 0, i.e. **Mightyena**;
           `teach_hm_move(replace_slot=None)` then takes the most expendable slot, which is
           **Taunt** (base power 0) — a status move, so the damaging-move count does not drop.
           That is the good outcome and it should be asserted, not assumed.
           ‼ Sceptile is the WORSE carrier: its only 0-power-ish slot is protected (Rock Smash is
           an HM) so the picker would eat a damaging move.
         ⇒ still one `teach_hm_move()` call with existing machinery, but **verify the mon that
         ends up knowing Strength and which move it lost**. ‼ Do the teach at a heal stop, the way
         `#24-pc` piggybacks — not as a detour.
      2. **A success test that works for a PUSH.** The obstacle is not removed, it MOVES, so the
         test must be "did the boulder's tile change / is the target tile now walkable", not
         "did the object disappear". ‼ Do NOT reuse the Rock Smash path unmodified — its test is
         exactly the one that cannot see this.
      ‼ Bound any push loop: a boulder that will not move (pushed against a wall) must fail
      loudly rather than retry, and Rock-Smash rocks respawning on map reload already turned one
      retry loop into 23.9M wasted frames (KI-34).

      HISTORY — ✅ **NOT BLOCKED. READY TO BUILD (2026-08-10). The three-week-old
      deferral was right by accident and wrong in its reason.**
      The door at JAGGED_PASS (16,18) is guarded by a **Team Magma NPC standing on (16,19)**,
      the column's only entry — `OBJ_EVENT_GFX_MAGMA_MEMBER_M`, hidden by flag **847**
      `HIDE_JAGGED_PASS_MAGMA_GUARD` (decomp `JaggedPass/map.json`). Measured:
      | save | guard hidden | `(16,20)→door` |
      |---|---|---|
      | `jagged_descent.ss1` (badges 1-3) | False | FAIL |
      | `post_mtpyre.ss1` (badges 1-6) | **True** | **OK, 2 waypoints** |
      ⇒ **No ledge problem, no KI-24 blind spot, no scripted movement needed** — the planner
      was correctly modelling the guard. In the right era the door is 2 waypoints from a
      tile the bot already reaches, and the chapter runs after Mt. Pyre so the flag is set
      by the time it matters.
      **BUILD ANCHOR: `saves/post_mtpyre.ss1`.** ‼ Do NOT develop this from a pre-Emblem
      save — that error cost seven probes and two wrong conclusions (`08-MISTAKES` 2026-08-10).
      HISTORY — status conflict flagged by triage: THIS entry says **DEFERRED** (the JAGGED_PASS (16,18) door is unreachable from
      the ROUTE112 side), while `04-HANDOFF.md` lists it as the **next story content and the
      largest untouched lever**. Both are current-state files and they disagree, which is
      exactly the case `CLAUDE.md` says to raise rather than resolve unilaterally.
      ‼ **THE TECHNICAL OBJECTION IS NOW CORROBORATED, AND IT IS THE ONLY THING BETWEEN THE BOT
      AND NEW CONTENT** — measured 2026-08-10 (static, with a PASSING control):
      | from | to `MAGMA_HIDEOUT_1F` door (16,18) |
      |---|---|
      | MT_CHIMNEY entry (13,5) | **FAIL** |
      | MT_CHIMNEY entry (14,5) | **FAIL** |
      | door → ROUTE112 exit (14,40) | **FAIL** |
      | CONTROL: entry (13,5) → ROUTE112 exit (14,40) | **OK, 39 waypoints** |
      Warps confirmed from the decomp: JaggedPass exits are (14,40)/(15,40)→ROUTE112,
      (13,5)/(14,5)→MT_CHIMNEY, and **(16,18)→MAGMA_HIDEOUT_1F**. The door tile IS walkable;
      it simply sits in a pocket the descent cannot enter. So `do_jagged_descent()` already
      walking this map does NOT get us the door.
      ‼ **BUT A STATIC FAIL IS 'UNPROVEN', NOT 'IMPOSSIBLE'** — `calculate_path` reads
      dual-elevation terrain and ledges as walls and has called a reachable place
      unreachable before (KI-24). **The deciding test is a DRIVEN one**, and the anchor
      tooling to run it did not exist when this was deferred on 2026-07-26:
      capture a MT_CHIMNEY/JAGGED_PASS anchor with `--driver anchorstory`, then drive
      `--driver groundsweep SWEEP_GROUND=JAGGED_PASS:16,18`. ~20 minutes, and it converts a
      three-week-old deferral into a measured yes/no. **DO THAT BEFORE WRITING THE CHAPTER.**
      ✅ **RE-TESTED PROPERLY 2026-08-10 (two DRIVEN attempts + a purpose-captured anchor):
      the blocker is REAL, and the chapter is BUILDABLE with scripted movement.**
      From the bot's OWN in-descent position `JAGGED_PASS (14,9)` the door and both its
      neighbours are unreachable while the control (continue to the ROUTE112 exit) succeeds
      in 34 waypoints. A walkable flood fill shows the door is in the SAME 238-tile region as
      every warp, so it is **ledge-isolated, not walled off** — `(15,18)`/`(17,18)` are solid
      and the nearest reachable tile is `(14,18)`, two away.
      ⇒ **Do not try to fix generic navigation for this. Write the approach as EXPLICIT
      SCRIPTED MOVEMENT**, which is already this item's own instruction and the project's
      pattern for ledge terrain. Anchors to develop against now exist:
      `saves/jagged_descent.ss1` (JAGGED_PASS (14,9)) and `saves/mt_chimney_top.ss1`.
      HISTORY — **DEFERRED.** Door at JAGGED_PASS (16,18) is unreachable from the
      ROUTE112 side (one-way ledges; a 2026-07-26 probe already failed to path there). Only
      approach is ROUTE112 → cable car → MT_CHIMNEY → descend ⇒ ~8 warps + a scripted ride.

### ‼ THREE FLAGS THAT MUST STAY `0` (each hides a MEASURED regression)
`POKEBOT_LEAD_DEMOTE_WONDER_GUARD` (~20 pts) · `POKEBOT_AREA_ITEM_GATE` (~7 pts) ·
`POKEBOT_PC_ROTATION` (~19 pts of the last rung). All three REMOVED something and were
justified by counting failures without counting successes. Do not re-enable without a batch.



### ~~READY TO APPLY THE MOMENT BATCH `20260802-160603` LANDS~~ — ✅ APPLIED; header stale
> Closed by triage 2026-08-10. That batch landed on 2026-08-02 and the item below shipped;
> the heading sat here for eight days implying pending work that did not exist.

- [x] `#24-leadcounter` — ✅ **CLOSED 2026-08-10 by triage: it SHIPPED and this entry was stale.**
      Verified in code: `team_policy.lead_rank_key(..., is_hunted_counter: bool = False)`
      (`team_policy.py:263`) and `early_game.py:1712/1735` compute and pass it. It also has a
      recorded post-ship bug (`08-MISTAKES` 2026-08-03 — it was silently dead for two batches),
      which is further proof it was applied. HISTORY — **USER RULING 2026-08-02: super-effectiveness outranks raw level
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

### ‼‼ `#24-orphans` — SIX REAL RESIDUALS THAT WERE WRITTEN DOWN BUT NEVER TRACKED (filed 2026-08-15)

> ⛔ **WHY THIS ITEM EXISTS.** An audit asked a question nobody had asked: *for every "still open /
> still owed / not built" sentence written this session, would a future session ever FIND it?* Six
> would not. ‼ **Four of the six share one shape — a live residual recorded inside a document half
> that is marked DONE or ARCHIVED** (a CLOSED KI's body, an "older framing" queue block, an
> archived handoff section, a research note). That is the P2 header-vs-body failure applied to
> TRACKING rather than to STATUS, and prose alone did not catch it — the question did.

- [ ] **(1) ‼ HIGHEST COST — `withdraw_from_box` has NO CALLER THAT CHECKS ITS VERDICT.** KI-79 made
      the *message* honest (identity-verified, loud on failure) but production still cannot REACT:
      the function returns nothing and never raises, so a failed withdraw is now *reported* and
      still silently tolerated. ⛔ It was filed in the body of a KI whose header read only
      "CLOSED" — any session scanning for open issues skips it. (KI-79's header now carries the
      caveat.) The next Slugma-class derail is still invisible to callers.
- [ ] **(2) KI-65 — `battle_move_replacing.py`: `party_index` unbound reads raise into SILENT
      excepts.** OPEN and code-verified since 2026-08-12. ‼ Standing candidate cause for the
      REOPENED `#24-teachmsgstall`, so orphaning it broke a live investigation's only lead.
      ✅ **RECON DONE 2026-08-16 — read KI-65's "RECON" block BEFORE writing a line.** It corrected
      this item on three counts: **there are TWO unbound reads, not one** (`:397`, the HM veto, is
      the more damaging and hides behind `except: pass`); **the captured `movelearn_hmwedge_*.ss1`
      saves are a FIXTURE, not a repro** (`last_confirmed_slot is None` on a fresh generator, so the
      crash line is skipped — and "moveset unchanged" is today's GREEN result, so an A/B on it is
      VACUOUS); and **fixing the flagged line alone leaves the ping-pong intact**, because
      `:380-381` re-arms the doomed pick every cycle while `last_offered_move_name` is never set.
      ✅ Fault-injection point identified, no production edit needed (rebind `bmr.get_battle_state`
      so `map_battle_party_index` raises — the most plausible REAL raiser). Fix specified in three
      parts. ⛔ **STILL DEFERRED BY THIS ENTRY'S OWN RULE: repro FIRST.** Changing the teach flow
      without one is how `#24-teachmsgstall` earned its "the fix had no production effect" verdict.
      ⚠ `custom-pokebot`'s copy is byte-identical — whatever lands has a promotion twin.
- [ ] **(3) KI-66 — the multi-battle hazard is BROADER than the faint chooser:** four more
      full-party scans are unguarded, one feeding an UNBOUNDED `while … press A`. OPEN,
      code-verified, never live-run, and untracked until now.
- [x] **(4) ✅ DONE 2026-08-16 — `story_harness.py` no longer overwrites its log.** The default is
      now `harness_<build>_<driver>_<timestamp>_<pid>.log`, which **cannot collide**, and the run
      PRINTS its path as its first line (`[setup] LOG -> …`) so the "read the flushed log while it
      hangs" workflow still works. `--log` still pins a path exactly.
      ✅ **REGRESSION-TESTED, not just changed:** both arms of a real A/B run back to back now leave
      TWO transcripts with different content (`EXPECTATION = COUPLED` / `= DECOUPLED`); forcing both
      arms onto one path with `--log` reproduces the OLD destruction (arm 1's transcript gone),
      which is the fault test. ‼ The old fix had shipped as a PROSE HABIT ("give each arm a distinct
      `--log`") that a fresh session had no reason to know — this is the same rule as a GATE.
      ⚠ Docs that named `harness_sandbox.log` as the file to read are updated (`04-HANDOFF`,
      `14-AGENT-PLAYBOOK`, `05-KNOWN-ISSUES`); the append-only logs keep their historical wording.
- [ ] **(5) `compare_runs.py` pairing for the (P4) matrix — never built.** Blocks nothing today; it
      lives only in `ai-research-notes/2026-08-15-p4-boxcounter-repro-design.md`, and a research
      note is explicitly "a NOTE, never a source of truth" — nobody mines those for backlog.
- [ ] **(6) KI-76's CORRECTNESS half is OPEN and MIS-SHELVED.** Its only queue mention sits inside a
      block the handoff brackets as *"older framing … ⛔ also NOT next"*. ⚠ It is ARMED on Routes
      132/133/134 — the approach to the Regi arc and §Ch23 — so it will resurface as a "new" bug at
      the worst possible moment.

‼ **PREVENTION, and it is a question rather than a rule:** at wrap-up, for every *"still open /
owed / not built / residual"* sentence written that session, ask **"where would a future session
FIND this?"** If the only answer is an append-only log, a CLOSED KI's body, or a research note, it
is ORPHANED — put it here. ⇒ `08-MISTAKES.md`, 2026-08-15.

### ‼‼ THE BIG ONE — `#24-trainmap+` : area-aware training, party>4, PC rotation

> ⛔⛔ **BEFORE YOU TOUCH ANY BOSS `cfg["grass"]` OR `TRAINING_GRASS`, READ KI-80 (2026-08-15).**
> The handoff's (P6) framing of this — *"Norman's patch is L3-5 against a band of L27-31, and
> Winona has no patch at all"* — is **WRONG ON BOTH EXAMPLES**, and acting on it regresses the
> bot. ✅ **UPDATED 2026-08-16 — THE COUPLING IS GONE FROM BOTH FORKS (promoted).** `grass_is_fodder`
> (`story_mode.py:1899`) USED TO CO-GATE KI-23's `_boss_plan_is_hopeless`/`_counter_ladder`
> (with `boss_teaches`, inside `losses >= 2`), so giving Winona a `grass` key SKIPPED her counter
> machinery silently for any team at L30-35. **KI-80 decoupled it:** `:1901` is now
> `if boss_teaches:` and `boss_mode` sits behind its own `if grass_is_fodder:`.
> ⚠ **The warning below still stands for the OTHER two reasons**, which the decoupling does NOT
> address. ✅ The decoupling was PROMOTED 2026-08-16, so BOTH forks now have it. Norman's L3-5 patch is the DELIBERATE fodder trigger for the only relocation
> this bot has ever performed (70-83% measured). And a new `TRAINING_GRASS` row re-ranks ONE
> GLOBAL table for every caller, including the counter picker for every other boss.
> ✅ **ENFORCED, not requested:** `repro_boss_grass_gate.py` (suite #24) fails the build if an
> at-risk fight gains a `grass` key while the coupling stands. It is AST-based (a comment cannot
> trip it) and SELF-RETIRING (it stops enforcing once the ladder is decoupled).
> ✅✅ **DONE — KI-80's decoupling is BUILT, DRIVEN, REVIEWED AND PROMOTED TO BOTH FORKS
> (2026-08-16). ⛔ DO NOT REBUILD IT.** *(This line commanded it as live work after it shipped.)*
> It did NOT ship on reading alone: the KI-23 repro was driven before AND after. ⛔ **READ KI-80's CONDITION TABLE FIRST.** This line used to say
> *"at `losses >= 2` with `kos >= 1` and no type answer"* — that is **REFUTED and would build a
> VACUOUS test**: below `losses >= 6` the ladder cannot fire at all, at 12+ `hard_plateau`
> passes it for the WRONG reason, and the fixture must ALSO satisfy `team_max <= wild_max + 8`
> or `grass_is_fodder` never flips and BOTH arms take the same branch.

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

- [x] ~~**‼ `#24-smashroute` — clear a ROCK SMASH obstacle that seals a journey (new,
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

- [x] ~~**‼ `#24-journey` — CROSS-MAP OVERWORLD ROUTE PLANNING (new, 2026-07-30; see KI-39).
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
- [x] **`#24-counters` phase 2 — ✅ BUILT 2026-07-30, and LIVE-VALIDATED many times since;
      the "awaiting validation" header was 8 days stale (closed by triage 2026-08-10).**
      Evidence: `best_huntable` (`counter_plan.py:435`) and `hunt` (`counter_hunt.py:327`) are
      live; batch `20260808-131334` measured conversion 15% → 45% (z = +2.39 on REAL catches),
      and `20260809-081643` restored `CAUGHT Machop` 0/7 → 6/7 (z = +3.24) with FALSE catches
      10 → 0. ‼ Its open FOLLOW-UPS live in newer items, not here — see `#24-battleitems`
      and the boss-healing work; the chain's DIAGNOSIS is sound and its premise is what is
      now in question. HISTORY —
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

- [ ] **#24 — STORY AUTO-PLAYER.** The only active work.
      ⛔ **CORRECTED 2026-08-13 — the body below was FIVE CHAPTERS STALE and the TRIAGE INDEX
      blessed it as "the only entry carrying CURRENT state". Current truth:** the ladder runs
      **20 of 24 beats** (7 badges, Mt. Pyre, Magma Hideout and out, Slateport submarine, Aqua
      Hideout + Master Ball, Mind Badge, Space Center + HM08 Dive), and the **Seafloor Cavern is
      driven through Room 3 in the harness** (`#24-remainingarc`, the live head of this list).
      The current order is `#24-remainingarc` → the queue in `04-HANDOFF.md` NEXT ACTIONS.
      Superseded text (true on 2026-08-10): A cold start reaches
      **Badge 6 (Winona) = end of built content** (38 maps, ~2.48M frames, 0 derails).
      Sub-items live in `## Story bot (#24) — open backlog` below; the then-current order was
      `#24-whiteout`, `#24-counters` phase 2, `#24-regionreach` gate table (KI-24b).
      Next unbuilt chapters: **Mt. Pyre**, then the **Magma hideout**.
- [ ] #V — Post-promotion verification sweep (PARKED behind #24): independent adversarial pass
      on the promoted features that only had builder self-verification (not
      an independent pass) — #8 global pathfinding, #12 shiny alerts, #18
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
      ⛔ **UNBLOCKED 2026-08-13 — the blocker below was CLOSED 2026-08-05** (`#24-cavethread`: multi-hop cave threading ALREADY WORKS, both directions, no chain table — see its [x] entry). This item is now limited by priority, not by a dependency. Superseded text: ‼ **BLOCKED ON ONE THING:** `_CAVE_EXITS` / `_CAVE_ENTRANCES` are SINGLE-HOP tables,
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

## Next (user-set order 2026-07-19: #30 → #31 → #32, THEN the first wave below)
> #30/#31/#32 are BUILT + ADVERSARIALLY VERIFIED in sandbox (clean pass:
> money cheat byte-safe 56/56, GUI nav 28/28, no code bugs). AWAITING USER
> OK to promote to custom. In-game confirms still pending (filled-slot
> composites, hover with real stats, money effect, controller feel on Ally).
- [ ] #30 — Handheld & GUI refinements (user-specified 2026-07-19):
      (a) Persistent "Handheld Mode" button — move it out of the Play/
      Controls tab into an always-visible header (in the drawer: right of
      the "TOOLS" text; desktop: a header row above the tabs) so it shows on
      every tab.
      (b) Handheld menu relocation — in handheld mode the Tk top menu
      (Emulator/Profile/View/Help) must NOT appear at all (even with the
      drawer open; reverses the earlier "menu shows with drawer" behavior
      for handheld). Surface those commands as buttons/sections inside the
      PLAY tab instead. Desktop keeps the normal menu bar.
      (c) Left Party Section — a vertical party strip to the LEFT of the
      emulator video, in BOTH desktop and handheld: 6 slots, 1 mon/row.
      Empty slot = Poké Ball sprite; filled slot = the mon's sprite
      composited over its caught-ball sprite (ball BEHIND, from
      `pokemon.poke_ball`; ball art at sprites/items/<Ball>.png).
      (d) Hover stats — hovering (mouse) over a Left Party slot shows ALL
      that mon's stats (level/IVs/nature/ability/moves/…) in a tooltip;
      SAME hover-stats on the Party tab rows; must also be reachable via the
      gamepad-GUI navigation (#32).
- [ ] #31 — Adjustable money cheat: in the CHEATS card, a money entry
      pre-filled with the character's CURRENT money (read live), editable to
      any value, + a "Lock" toggle that freezes money at the typed value
      (on = keep re-applying that exact value; off = stop). Refines the
      existing Max/Infinite money.
- [ ] #32 — ★ Gamepad-driven GUI navigation (roadmap F2, PRIORITIZED by
      user to come right after #30/#31): drive the dashboard with the ROG/
      Xbox controller (D-pad/stick move focus across tabs/cards/buttons/
      party, A activates, incl. triggering the party hover-stats). Distinct
      from the existing in-GAME gamepad input (Manual mode).

## Adjustments (user-requested 2026-07-19)
- [x] #36 — Left Party balls enlarged 52→104px (ball visible behind mon)
      (ce66eb78).
- [x] #37 — Party hover tooltip restyled Pokémon-themed (type badges, IV
      grid, moves, sprite) (ce66eb78).
- [x] #38 — Gamepad GUI-nav gated to drawer-open only (no more gameplay
      interruption) (ce66eb78).
- [x] #39 — Auto-DECLINE new move learning (default `new_move: cancel`;
      seam for future move-intelligence at
      DefaultBattleStrategy.which_move_should_be_replaced) (25fac025).
      User's placed battle.yml also set to cancel.
- [x] #40 — Catch-ball allowlist (d5573234): "CATCH BALLS" card (checkbox+
      icon per ball) filters catch.py::_get_best_poke_ball; catch_balls.yml
      global+per-profile; default protects Master Ball. Live-verified on the
      real save. (Live catch in a real battle still pending.)
- [~] #36b — Party balls enlarged further to 140px (~2.7×); reads clearly
      behind smaller mons, big sprites (Celebi/Sceptile) still partly cover.
      Capped by column height — could go scrollable for a true 5× if the
      user wants. (d5573234)
- [x] #S — User's real save placed: "Nick - Emerald" (progressed) +
      "-restored" + global configs into custom/sandbox profiles/
      (gitignored). LIVE TEST on real party running.

## User rulings + new round (2026-07-19)
- [x] RULINGS: Latias+Latios BOTH obtainable (218/386); Surskit unobtainable
      (c2707bad).
- [x] #46 — Hover tooltip ball ~3× (fixed thumbnail no-op bug) (c2707bad).
- [x] #47 — Opportunistic catch: any SHINY (even owned) caught (c2707bad).
- [x] PROMOTE-2 — whole batch promoted to custom w/ extensive intent docs
      (DIVERGENCE-LOG a–i + DOCUMENTATION/05-hunting-and-livingdex.md);
      live-verified on the real save; 29b9aae5.
- [x] ~~`#24` (roadmap restatement)~~ — ‼ **SUPERSEDED by the canonical `#24`
      entry (“STORY AUTO-PLAYER”). Consolidated 2026-08-10.**
      HISTORY, kept for the design detail — #24 — STORY-MODE BOT (design-first, multi-pass/triple-check): play
      from a fresh save (user-set name; Oak intro/gender/name; Littleroot
      start) OR continue existing; goal = beat Elite 4 + complete the game
      (eventually pokedex); CHUNKED into chapters; must build+maintain a
      team; enumerate EVERY key event/interaction/item/requirement to
      progress + how to obtain progression items. Design → 12-STORYMODE-
      DESIGN.md, several verification passes before building.
      - PROGRESS (2026-07-20): a fresh game auto-plays through **GYM 1 (Stone
        Badge)** — intro→starter→first battle→Pokédex→train→rival→Petalburg→
        Dad/Wally→Route104→Petalburg Woods (Aqua scene)→Rustboro→Roxanne.
        Legs 1-2 promoted to custom; legs 3-4 + Gym 1 in sandbox (awaiting
        test→promote). Fixed the Woods-door stall (ML-9) in BOTH builds. NEXT:
        Chapter 4 (deliver Devon Goods → Rusturf Tunnel → Dewford / Gym 2).
        Low-pri OPEN: chapters.py Ch2 completion-flag bug.
      - PROGRESS (2026-07-24 overnight): fresh runs auto-play through GYM 4
        (Heat Badge) organically (3/5 lanes, batch 20260724-004252). Ch12
        BUILT + WIRED (Segment 12a/b/c: Lavaridge-Petalburg direct route,
        Wanda-wall smashes, sign-script gym doors, Norman, auto Surf handoff,
        teach Surf) - live-iterating from flannery_done (travel proven, gym
        chain walking). KI-15 FIXED (3 proven fixes); KI-17 opened (after-
        faint reshow freeze, 2 states captured, Gemini-diagnosed DMA race,
        sweep hardened per the analysis - validation pending).
- [~] #24-move — SMART MOVE-LEARNING (user 2026-07-20): DONE — Story strategy
      `which_move_should_be_replaced` override keeps every Pokémon combat-capable
      (never trades a damaging move for a status move), preserves type coverage,
      and skips no-gain moves; overrides the stock `new_move: cancel` decline.
      In both builds, unit-verified. REMAINING (folds into #24-team): status-move
      UTILITY ranking (value Sleep Powder/heal over Growl) rather than treating
      all status moves as equal.
- [~] #24-resume — RESUME-FROM-ANYWHERE (user 2026-07-20): v1 DONE — segmented
      flag-gated run() resumes from a fresh game / resumed save / hand-played
      state, skipping finished segments (fixed the "thinks I need Wally"
      mis-detection via the HIDE_PETALBURG_CITY_WALLYS_MOM flag). REMAINING:
      finer per-STEP resume with each step self-locating from any tile; FAST
      travel (Fly/Teleport/Escape Rope when available, gated by HMs/badges/items
      per #42); title-screen-with-save auto-Continue; reliable completion flags
      for chapters past Gym 1. Design §RS.
- [ ] #24-autosave — AUTO CHAPTER SAVE-STATE (sandbox testing aid; user
      2026-07-20). After each scripted chapter/segment completes in StoryMode
      (SANDBOX ONLY), auto-save a save state named by chapter into `states/` so
      chapters can be tested/resumed fast. TOGGLE in the Play tab, DEFAULT ON,
      safely toggleable on/off even while the bot runs (the story generator reads
      the flag at SEGMENT BOUNDARIES, so flipping it never interrupts). Implement
      by hooking the segment boundaries already in `StoryMode.run()` (§RS).
      **APPLY ONLY AFTER the user green-lights the current story build** (it
      touches run()); until then this is a note. Save quickly at a boundary
      (get_save_state + write) — negligible one-frame pause.
- [x] #24-loadpage — LOAD-STATE POPUP PAGINATION (user 2026-07-20): DONE both
      builds. `load_state_window.py` now shows 5 states/page and lazily renders
      only the current page's thumbnails (Prev/Next + arrow/PageUp-Down + page
      label; nav auto-hidden for one page). Fixes the slow-open with a full
      `states/` folder (was decoding up to 128 PNGs at once).
- [ ] #24-defeat — DEFEAT RESPONSE (user 2026-07-20; design §DR). What the bot
      does when it LOSES a battle, as a settings-popup choice:
      (A) "Reload save state" = today's watchdog behaviour, made a toggle; verify
      the resume-after-reload rough edges (the segmented resume §RS already fixes
      most — the old run() stranded the bot on any restart; also ensure watchdog
      snapshots are CLEAN OVERWORLD states, never mid-battle/scene).
      (B) "Play through & retry" = ride out the whiteout → respawn (Poké Center /
      early houses) → recalc position + story segment (§RS) → MATCHUP ASSESS (avg
      enemy vs own level, team size, type/move coverage) → train/adjust team
      (#24-team) if outmatched → escalate on repeated loss → retry. Mode B = §RS +
      matchup gate + #24-team, one engine. Sub-parts: a small matchup scorer;
      whiteout ride-out; failure/attempt tracking per objective.
- [~] #24-evo — EVOLUTION policy (user 2026-07-20): CURRENT (sandbox+custom) =
      ALLOW ALL evolutions (`should_allow_evolution → True`, overriding the stock
      `stop_evolution`) — fixes the Lv16 evolve+move-learn hang and strengthens
      the team. POPUP options to add (#24-ui): **allow all (default on) / random
      evolution / no evolution**. Robustness the bot must have (verify): RECOGNIZE
      when an evolution happens, navigate the evolution CUTSCENE, and handle the
      accept/deny of a new move + deleting an old one to replace it (uses the
      stock evolve→learn path + `which_move_should_be_replaced`). "Random" mode =
      per-Pokémon coin-flip whether to evolve (organic team variety, ties #24-team).
- [x] ~~`#24-team`~~ — ‼ **SUPERSEDED by `#24-organicteam`**, which is ✅ **APPROVED — GATE
      LIFTED** (user 2026-08-06, re-confirmed 2026-08-14). ⛔ This pointer said the target
      "carries the user's 2026-08-05 DEFERRAL — the live instruction" until 2026-08-14; that was
      stale (the deferral was reversed on 2026-08-06). Consolidated 2026-08-10.
      HISTORY — #24-team — ORGANIC TEAM-BUILDING / helper acquisition (user 2026-07-20;
      design in 12-STORYMODE-DESIGN §TB). Bot builds a team to beat gyms/trainers
      but decides to catch "helpers" ORGANICALLY: a rising "recruit urge" that
      grows with failed/struggled battles (increasing re-rolls/odds), weighted by
      real team gaps (type matchup vs the fight, team type-diversity, move
      coverage), pulling candidates from the obtainability+reachability data
      (#41/#42). Random/human-like, not a min-maxer. Needed for Torchic-vs-Roxanne
      and later type-hard gyms; implement when a gym requires it.
- [ ] #24-shops — MAP SHOPS AS REACHED (user 2026-07-21; planning doc §4). Each mart
      has its own layout AND stock/order; the buy code is already shop-agnostic
      (universal task-driven flow + `_mart_item_row` reads stock live). So map each
      shop's ENTRY facts (mart map, clerk-approach tile, facing) when first reached,
      verify live, add an Atlas row. SPECIAL: **Lilycove Department Store** is
      MULTI-FLOOR (per-floor shop + stock, elevator nav); the **Elite Four Poké
      Center** has a shop + mart; Slateport stalls / TM sellers use non-standard
      menus. Do NOT map all shops up front (unreachable → can't verify).
- [x] ~~`#24-pc` (design entry)~~ — ‼ **SUPERSEDED by `#24-roster`**, which the
      user APPROVED 2026-08-06 with its gate lifted. Consolidated 2026-08-10.
      ‼ The OTHER `#24-pc` entry (Surf resource walls) is a DIFFERENT thing — a derail
      class — and REMAINS OPEN.
      HISTORY — #24-pc — PC / BOX TEAM MANAGEMENT (user 2026-07-21; planning doc §4b). Advanced
      team development via the Pokémon Storage PC: store / move / withdraw Pokémon
      (and items). Map PC access points (every Poké Center + player's-house PC) and
      the PC UI (Deposit/Withdraw/Move, box navigation, party↔box swaps, item
      storage). Enables swapping in a better-matched mon per gym and parking
      over-levelled/redundant catches. Build when a fight needs it; ties #24-team /
      §7 matchup awareness. Poké Centers are otherwise near-identical (generic code
      handles them) — only map PC/layout exceptions (e.g. the E4 Poké Center).
- [x] #24-resume — SEGMENT 1 RESUME BUG FIXED (2026-07-21). Pre-Pokédex
      recovery/resume re-ran the scripted intro from the truck → derail loop
      ("stuck after respawn"). Split Segment 1: scripted intro gated on
      `_has_starter()`; train→rival→Pokédex resumable + flag-gated. Derail budget
      hardened (monotonic party `_progress_sig`; patient recovery). Verified in
      harness. Sandbox (early_game.py, story_mode.py). See CHANGELOG/MISTAKES 07-21.
- [x] #24-freeze — OLDALE PC FREEZE **FIXED** (user 2026-07-21). Root cause (from the
      user's real-bot debug log's generator call stack): heal returned while the
      overworld was transiently non-controllable → heal→go-to-rival navigate choked →
      derail → re-heal → endless heal/leave/re-enter loop → Manual. FIX:
      heal_in_pokemon_center waits for a STABLE controllable overworld after the exit
      warp. Downstream: StoryCatchStrategy flees instead of Manual when out of balls.
      Validated route103→Rustboro→Route116 catching, 0 derails/Manual. Old note below
      kept for history.
      ~~POST-BATTLE TRANSITION FREEZE (the likely real "stuck at Oldale PC").~~ After a training battle (flee/level-up/move-learn, e.g.
      Mudkip Water Gun @L10) the return-to-overworld transition leaves the overworld
      non-controllable while the bot acts (navigate / walk to the Oldale nurse) → can
      hard-freeze (nurse heal dialogue never starts). REAL (harness == real
      main_loop), timing/starter-sensitive (default starter "random"; Treecko passed,
      Mudkip hits it). Offline repro hampered by save-state reload artifacts. NEXT:
      user validates on real PC (force `starter: mudkip`, fresh game) and reports;
      then decide a deeper "settle before acting" fix (heal_in_pokemon_center nurse
      interaction + story navigations) vs a training-flow workaround.
- [x] #24-debuglog — DEBUG LOGGING TOGGLE (user 2026-07-21). Opt-in "Debug Logging"
      in the Run (bot-mode) menu (both GUIs), default off → `modules/debug_logger.py`
      writes an extensive structured log to `<profile>/debug-logs/` (event stream +
      stuck dumps with the generator call stack). For diagnosing Bug #2 (#24-freeze)
      from a shared real-bot log. Built + validated in sandbox. See CHANGELOG 07-21.
- [x] #24-swaptrain — SWAP-TRAINING **DONE** (user 2026-07-21). Fixes the
      under-levelled-mon training loop: `SwapTrainBattleStrategy` switches a trainee
      that's ≥2 levels below the wild foe to the strongest team-mate turn 1 (shares
      XP, no fainting/heal-churn). Gated around `train_team`. Validated Poochyena
      L4→L7, 0 heals/faints. Commit ef812c0e.
- [~] #24-trainmap — AREA-APPROPRIATE TRAINING (user 2026-07-21, Option 1).
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
- [ ] #24-ui — STORY-BOT PRE-RUN SETTINGS POPUP (user 2026-07-20). A popup/menu
      shown BEFORE the Story bot runs to set: player name; starter nickname mode
      (none / defined / random); starter choice (specific / random); + other
      settings TBD. Front-end for the existing `<profile>/story.yml`
      (character_name/gender/starter/starter_nickname already read by
      modules/story/config.py). WORK ON THIS ONLY AFTER the bot is finished and
      tested 100% (user directive). Popup also hosts the #24-autosave toggle
      (auto chapter save-state, default on) and the #24-defeat "Defeat response"
      section (Reload-save-state vs Play-through-and-retry + sub-toggles).

## Living-Dex deepening (user-requested 2026-07-19; DESIGN-FIRST, no cutting corners)
- [ ] #41 — Obtainability model: classify every species — wild / evolution
      (method+from) / in-game trade / gift / static / roamer / event — so the
      Living Dex knows trade-evolutions and evolve-only / trade-only mons
      (must obtain pre-evo + evolve, or manual trade), not just "no wild →
      skip". (design: 11-LIVINGDEX-DESIGN.md)
- [ ] #42 — Reachability/requirement gating: hunt + living-dex must skip a
      target when the area/encounter needs a capability the player lacks
      (Surf/Cut/Rock Smash/Dive/Waterfall HMs, the right fishing rod, badges
      for HM use, story-flag area access). Read owned HMs/rods/badges/flags
      from the save.
- [x] #43 — Living Dex OPPORTUNISTIC catching: catch ANY wanted-uncaught
      species en route (target only drives travel); live-dex-driven
      advancement; 22/22 units (a8840769).
- [x] #44 — Party ball rework: strip now clean mon sprites (no ball
      backdrop); caught ball moved to the hover tooltip as an icon+name row.
      Live-verified on the real save (9c2b1f94).
- [x] #41-evo/#42-easy — obtainability (evolution) + capability gating
      built (ceb7343e; 30/30 units; live save read Old/Good/Super Rod;
      panel shows 128 wild/147 evolve/102 special-trade). obtainability.py
      + capabilities.py.
- [x] #41-research — compiled + fact-checked Emerald obtainability lists
      (gift 7/static 8/roamer 1/event 6/breeding 3/special 1/unobtainable 79;
      in-game trades rescue nothing). Census sums to 386; "show both"
      denominators exposed (217/386 obtainable without trading). 16/16 units.
      modules/data/emerald_obtainability.json + obtainability.py. Fact-check
      report + citations: 11-LIVINGDEX-DESIGN.md (Phase #41-research). REMAINING
      for full #41: wire living_dex_mode target selection to plan_for's gate +
      route gift/static/roamer to reset modes; auto-evolve helper.
- [ ] #42-hard — HM-gated cross-map reachability in the nav graph (v2).
- [ ] #45 — (FUTURE, with story-mode bot #24) enumerate story instances the
      bot can automate, and let hunt/living-dex progress the story to unlock
      areas/capabilities needed for dex completion.

## Now-ish (user-added 2026-07-19, ahead of first wave)
- [ ] #33 — GUI fixes (in sandbox): Left Party Section ALWAYS visible in
      both modes regardless of drawer state; unified open/close — Pokéball
      opens the side tool menu + a Close/Hide collapses it in BOTH handheld
      AND desktop (desktop can hide tools to see more emulator).
- [ ] #34 — Living POKÉDEX tab: search all Emerald species; caught mark +
      shinies-caught count (from stats.db) + full dex info (types/abilities/
      base stats/dex#/category/flavor) + learnable moves (level-up/TM/HM/
      tutor/egg) — offline Bulbapedia. Needs battle sprite + dex artwork.
      RESEARCH-FIRST (see 10-DEX-RESEARCH.md): inventory bot data → gap-fill
      → fact-check → THEN build.
- [ ] #35 — ITEM-DEX tab: search all items; total-collected-historically +
      currently-held counters + item info + map locations + used/held/
      dropped-by Pokémon. Needs item sprite + inventory image. Same
      research-first flow as #34 (10-DEX-RESEARCH.md).

## First wave (after #30-#32 + #33-#35 — agreed direction 2026-07-19)
- [ ] #22 — ★ Watchdog / auto-recovery: BUILT IN SANDBOX 2026-07-19
      (c7d25305; encounter-stall + drop-to-Manual + frame-freeze detection,
      bounded recovery ladder [re-assert → savestate-reload w/ safety backup
      → give up to Manual], overworld-gated, alerts, GUI status line; 17/17
      self-tests + recovery-path safety confirmed). Remaining: live-hunt
      softlock recovery needs a progressed save; independent adversarial
      pass to bundle with the batch verification before promotion.
- [ ] #9 — Hunt planner: v1 + v2 BUILT IN SANDBOX 2026-07-19 (6141d96f,
      4df17747). Encounter index from ROM (132 species/805 locations,
      19/19 fact-check); Hunt tab shows ranked locations + mode; v2 adds an
      encounter-tile finder + "Hunt (Custom)" mode = one-click travel (via
      global nav) + hunt. KI-6 tab overcrowding FIXED (two-row tab bar).
      REMAINING: live navigate+hunt on a progressed save; Rock Smash has no
      auto-tile finder (degrades to manual). Independent adversarial pass at
      promotion time.
- [ ] #23 — Living-Dex orchestrator: v1 BUILT IN SANDBOX 2026-07-19
      (34c5f461; living_dex.py target derivation + "Living Dex (Custom)"
      mode: travel→hunt→catch-first-uncaught→advance; catch-intent verified;
      16/16 units + real-ROM fact-check 132 targets). REMAINING: live
      autonomous run needs a progressed save; screenshot harness needs a fix
      after #33 layout change; independent adversarial pass at promotion.
- [ ] #25 — Pokémon detail + PC box viewer: click a party/box mon → full
      stats (IVs/nature/ability/moves); browse PC boxes with sprites. (M)
- [ ] #11 — Analytics suite: v1 BUILT IN SANDBOX 2026-07-19 (8094bb05;
      analytics.py + ANALYTICS card in Stats tab: encounter-rate sparkline,
      luck meter [actual vs binomial 1/8192, Ïƒ/z/verdict], sortable+
      filterable stats browser w/ sprites; 26/26 units). REMAINING:
      meaningful values need a populated stats.db (real hunt); independent
      pass at promotion.
- [ ] #27 — Battery-aware mode (ROG Ally): throttle speed/fps on low
      battery, pause on critical, resume on charge. (S-M)
- [ ] #28 — Polished mobile remote: phone-optimized web dashboard view to
      monitor 24/7 hunts (builds on the existing HTTP API). (M)

## Later / icebox (catalog in 09-FEATURE-BRAINSTORM.md; user re-orders/culls)
- [x] ~~`#24` (roadmap restatement)~~ — ‼ **SUPERSEDED by the canonical `#24`
      entry (“STORY AUTO-PLAYER”, the one carrying current state). Consolidated 2026-08-10.**
      HISTORY, kept for the reasoning trail — #24 — Story auto-player (trainer/gym battler) — most ambitious, most
      transformative: progress the game to bootstrap a save to any hunt. (L)
- [ ] #26 — Theme system (selectable color themes; palette is centralized). (S-M)
- [ ] #29 — Box manager / auto-release by IV/nature/shiny filter (prevents
      full-box stalls in long hunts). (M)
- [ ] #13 — Macro composer v2: chain macros + repeat counts + conditions. (M-L)
- [ ] #14 — Profile manager UI (create/duplicate/rename/delete). (S-M)
- [ ] #15 — Config editor GUI (catch_block/battle/cheats + CCF builder). (M)
- [ ] #16 — PKHeX quick-export (.pk3 of any party/box mon). (S)
- [ ] #17 — Multi-instance manager (several profiles, aggregating board). (L)
- [ ] #19 — Stream overlay theme refresh (OBS overlay → dashboard style). (S-M)
- [ ] #6 — Idea backlog: everything else in 09-FEATURE-BRAINSTORM.md
      (egg-hatch optimizer, catch profiles, Nuzlocke, goals panel, log
      viewer, setup wizard, keybinding editor, shiny gallery, hunt-summary
      cards, cross-session history, stream chat, webhooks, crash-safe
      savestate ring, health monitor, scheduled hunts, gamepad-driven GUI,
      RNG manip, cheat presets, plugin loader UI).

## Promoted to custom 2026-07-19 (built; awaiting user in-game confirmation)
- [~] #3 — Custom automations + Patrol (v3 multi-map/global-nav). Awaiting
      user's in-game play-test.
- [~] #7 — Sandbox enhancement round (backup/restore + cloud, macros,
      multi-map Patrol, GUI pack) — built, adversarially verified (16-bug
      round), promoted.
- [~] #8 — Warp-aware global pathfinding — promoted; user cross-warp walk pending.
- [~] #10 — Gamepad + handheld menu-hide — promoted; user real-pad test pending.
- [~] #12 — Shiny alerts — promoted; user sees a live shiny fire it pending.
- [~] #18 — Auto-update notice — promoted; observe on a stale checkout pending.
- [~] #20 — Cloud save-sync v2 (off by default) — promoted; desktop↔Ally run pending.
- [~] #21 — Game cheat menu (+ tabbed GUI, full-dex sprite picker, XP bars,
      topmost dialogs) — promoted; user in-game effect test pending.

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
- [ ] #24-sanity — SELF-CORRECTION / SANITY-CHECK (user 2026-07-20; design §SC).
      Story mode must never get permanently derailed: re-validate at every segment
      boundary (did the completion flag actually set? else retry/skip-ahead),
      handle out-of-place execution (self-locate), handle non-monotonic progress
      (reload/blackout moving backward), detect mid-run derailment (expected vs
      actual segment) and re-sync, bounded retries + escalation (ties §DR/#24-team),
      stall watch as last resort (Watchdog #22). Unifies §RS + §DR + #24-team into
      one state-machine engine. Also bounds the Treecko-Lv16 "stuck but not stopped"
      loop class.
- [ ] #24-interrupt — INTERRUPTION INTELLIGENCE (user 2026-07-22): the bot should
      KNOW when its current task was interrupted and by WHAT (training spin →
      trainer sight-line battle; navigation → PokéNav call ring; heal walk →
      scripted scene; etc.) and resume the task accordingly instead of relying on
      the generic derail/retry loop. Today large parts are handled implicitly
      (battle listeners resume travel; _ride_out_scripted_scene; the derail
      recovery re-runs _play) — this item is the DELIBERATE design pass: a small
      "current intent" state (what am I doing + resume point) + an interruption
      classifier, so recovery is targeted rather than re-derived. Design first
      (fits the decision-brain seam in doc 13 §future).
- [ ] #24-movelock — BATTLE ENGINE: move-blocking/locking effects (user
      2026-07-22): Disable (last move unusable), Encore (locked INTO a move for
      N turns), and kin (Taunt — status moves blocked; Torment — can't repeat;
      Imprison; Choice-item lock later). The turn chooser (get_strongest_move_
      against / move_is_usable) currently ignores these volatile statuses, so a
      blocked move can be selected → wasted turns (the game refuses the input).
      Fix: read the battler's volatile status/disable struct and filter the
      usable-move set; if EVERYTHING is blocked, Struggle happens naturally.
      Validate vs a Roxanne/Brawly-era Disable user (e.g. wild Whismur has none —
      find a story trainer with Disable/Encore, or fault-inject the volatile
      struct in the harness).
- [ ] #24-ch8b-museum — Oceanic Museum entry gating (KI-11): resolve how the
      Aqua crowd clears so Stern is reachable; then Devon Goods → Stern
      (deliver_devon_goods_to_stern is built). BLOCKS Ch8b/Ch9.
- [ ] #24-freshbatch-rustboro — batch run03 (fresh game) 2026-07-22 played
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
- [x] #1 — Vendor upstream 40Cakes/pokebot-gen3 (subtree @ 5dd898f8) (2026-07-17).
- [x] #2 — Deep documentation pass + Pokemon_Emerald_AI_Notes.md (2026-07-17).
- [x] #4 — install.py V2 (setup/update/heal + ROM handling) — "worked!" (2026-07-18).
- [x] #5 — Native dashboard GUI + handheld mode — "worked!" (2026-07-18).
- [~] #24-textread — DIALOGUE AWARENESS: read on-screen text to drive interactions
      (user 2026-07-20; design §DA). FEASIBILITY CONFIRMED (decode_string of
      gDisplayedStringBattle / gStringVar4 reads exact text). STARTED: move-learn
      now uses text-driven detection (both builds) — UNIVERSAL (matches generic
      phrases + reads the offered move dynamically, not hardcoded to any move).
      â˜… ROOT CAUSE of the Lv16 hang FOUND & FIXED (ML-13): the Emerald battle Yes/No
      has no task and was detected only by a fragile script-offset; when it stayed
      `Unknown` the old code pressed nothing (is_waiting_for_input gate) → froze.
      `handle_move_replacement_dialogue` rewritten fully text/task-driven;
      `handle_evolution_scene` hand-off hardened. PROVEN by fault-injection A/B on
      both builds (old stalls ~10.6k frames & fails to learn; fix resolves in 394 &
      learns Pursuit + evolves). Faithful repro harness: scratchpad/repro_movelearn.py.
      Still want the user's real-32× confirmation. FULL SYSTEM (next big build):
      Reader (normalized current text + menu/cursor) -> Classifier (text -> interaction
      type) -> Responder (type + story progress + config -> answer; multi-valid
      decisions like fossil/starter = random). Gather conversation dumps {exact text,
      speaker, valid answers, how to answer} from runtime logging + pokeemerald script
      data; build a response table. Subsumes fragile scripted-scene ride-outs; robust
      + deterministic vs flaky task-state. Backstops: no-progress watchdog + advance-
      plain-text-with-A so nothing hard-freezes.

- [x] #24-evo-trainstall (FIXED 2026-07-22: interrupt-safe _rotate_lead_safely + _yield_bounded; proven on evostall.ss1; same fix covers the user's 110k-frame Joey stall) — `train_team`/`_story_spin` can hang right AFTER a
      trainee EVOLVES mid-training (batch run02 2026-07-22: Grovyle evolved +
      learned Fury Cutter on Route 116, then the spin never resumed → 20k-frame
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

- [x] `#24-ch20rename` — ✅ **DONE 2026-08-13.** Renamed and VERIFIED BY RE-RUNNING BOTH, not by a
      diff: `--driver ch21dive` → **`ch20dive`** (class `Ch21DiveMode` → **`Ch20DiveMode`**, all 33
      log tags), `probe_ch21_topology.py` → **`probe_ch20_topology.py`**, and
      `ai-research-notes/2026-08-13-ch21-dive-leg-predictions.md` → **`...-ch20-...`**. Also the
      three `§Ch21` prose occurrences inside `story_harness.py`, each checked individually to be
      about the cavern. **Proof:** `probe_ch20_topology.py` exit 0; `--driver ch20dive` →
      `[ch20dive] ACCEPTANCE: PASS legs=6/6 at_entrance=True got_out=True can_continue=True`.
      Current-state docs `03`/`04`/`05` updated (0 residual old names). ‼ **`06`/`07`/`08` were
      deliberately NOT touched** — append-only history is not rewritten, so 7 references to the old
      names remain there on purpose; **both renamed files carry a provenance header** saying those
      entries mean the new artefacts. 17/17 gates PASS, `lint_docs` PASS. Original item follows.
- [x] `#24-ch20rename` (original text) — **NEW 2026-08-13, SMALL AND SAFE, do it at the START of a session not the end.**
      The Seafloor Cavern beat is **Chapter 20** (`chapters.py:233`), but 2026-08-13's work called it
      "§Ch21" throughout and the misnomer is baked into artefact names:
      `--driver ch20dive` (and its `Ch21DiveMode` class), `tools/story-dev/probe_ch20_topology.py`,
      and `ai-research-notes/2026-08-13-ch20-dive-leg-predictions.md`.
      ‼ Nothing is broken — they are correct code with wrong names. The risk is a future agent
      building "Chapter 21" (which is really **Sootopolis / Rayquaza**) against cavern tooling.
      **Do:** rename driver + class + probe + note, update `04-HANDOFF.md`'s naming-correction
      block and every reference, then run `run_gates.py`. **Do NOT** rewrite git history or the
      append-only logs — correct forward and leave the old names in the changelog where they are.
