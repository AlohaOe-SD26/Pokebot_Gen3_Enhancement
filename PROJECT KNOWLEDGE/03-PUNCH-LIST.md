# Punch List — Pokebot_Gen3_Enhancement
> Current-state file: edit in place. The agreed work queue. ⛔ **THIS FILE IS AT ITS LINE BUDGET — run `lint_docs.py` for the live number. The next edit that GROWS it turns Tier 0 RED; retire a completed item first (SUMMARISE + POINT at `07-CHANGELOG.md`, never delete).**
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

### 1. ⚠ MIXED — ⛔ NOT AN ACTIVE LIST. Re-titled 2026-08-22 (PASS 5): **12 of its 16 rows are CLOSED**
> ⛔ **A HEADING IS A CLAIM ABOUT EVERY ROW BENEATH IT.** This table said "the only things being
> worked on now" while most rows carried ✅ DONE, and it named NEITHER live item. A cold reader
> using it as the index would have worked from a 12-day-old picture.
> ➡ **`#24-loopheadabort` IS DONE (2026-08-23, gate #30).** ⚠ **THE LIVE THING IS A PROMOTION
> DECISION — the USER's call** (drift: see the STATE row / `promote.py --check`). Then `#24-p4residuals`.
> ‼ *This row has now gone stale TWICE the same way — it names whatever was live when it was
> last edited. ⛔ `04-HANDOFF.md`'s NEXT ACTIONS queue is the thing to act from, not this table.*
> ⛔ **NOT `#24-ki76correctness`** — its only fixture is VACUOUS for its only live defect; and
> `#24-sanitycheck` is COMPLETE. *(This line named both of those as live until 2026-08-23 — it
> was written during pass 5 and went stale the moment pass 5 finished.)* — and
> `04-HANDOFF.md`'s NEXT ACTIONS queue, not this table, is what a session should act from.
> ‼ Rows below are kept for their evidence; read each row's OWN marker.
| item | state |
|---|---|
| `#24-battleitems` | ✅ **DONE & PROMOTED 2026-08-10.** Built, unit-proven (27 checks), live, self-correcting; validation batch `20260810-082509` passed (flips 20 → 2, both-failed 10 → 0). ‼ Outcome unproven — grade any follow-up on BATTLE-level metrics. |
| `#24-teachmsgstall` | ‼‼ **REOPENED 2026-08-11 by batch `20260811-130454`. The fix has NO production effect**: success 38/47 (80.9%) vs 38/42 (90.5%) pre-fix, **z = −1.28 NOT resolvable**; `post_select=exhausted` 8/85 vs 3/80, **z = +1.46 NOT resolvable**; and the new `already-advanced` exit fired **ZERO** times in 85 teaches. The one-frame window was real and decomp-confirmed, but it was **not the dominant production cause** — there is another path to `exhausted`. The fix stays (it closes a real hole and costs nothing). Original entry: **ROOT-CAUSED, FIXED, A/B-PROVEN.** The replace-prompt detector had a **ONE-FRAME window**: `Task_ReplaceMoveYesNo` swaps itself out for `Task_HandleReplaceMoveYesNoInput` on the frame it becomes answerable (decomp `src/party_menu.c`; measured f3232735 → f3232736). Missing it left a blind A-mash that reaches `Task_HandleStopLearningMoveYesNoInput`, where **A = give up**. Fixed by watching both spellings, an `already-advanced` exit, and B at the stop prompt. **A/B (same save, one env var): OLD `learned=False` / NEW `learned=True`.** ✅ **PROMOTED 2026-08-11 (user-approved), verified DRIVEN in `custom-pokebot` as the same A/B, frame-for-frame identical. Source drift: ZERO.** |
| `#24-grounditems` | 🟡 **PARTLY DONE 2026-08-12.** The shared helper **`collect_item_ball(map, ball_tile, approach, facing, flag, item_name)` is BUILT** and has two callers (the Magma Hideout Escape Rope, refactored onto it, and the Aqua Hideout Master Ball + Nugget) — the duplication this item existed to prevent never happened. `repro_hideout_exit.py` now checks the escape-rope path DELEGATES to it, so a future edit cannot quietly fork a second copy. ‼ Lessons baked in: grade on a **bag delta** (a FULL pocket makes `finditem` set no flag AND give no item, so a flag test hangs forever); an item ball is an OBJECT you stand beside, and not every neighbour is reachable; **the ball VANISHES when taken, freeing its tile** (that is how the Master Ball is reached at all). **WHAT REMAINS:** per-area sweep LISTS so chapters collect the balls they walk past. Known uncollected in already-built content: Aqua Hideout **Max Elixir** `B1F (29,12)` (all four approaches reachable from node `(27,12)`) and **Nest Ball** `B2F (3,13)`; Magma Hideout **Rare Candy** `1F (3,20)`. |
| `#24-npcgifts` | ‼ **NEW 2026-08-12 (user directive).** **Collect GIFT ITEMS from NPCs** — items a person hands you, which the bot currently walks straight past. Decomp-anchored starters: **EXP SHARE** — `RustboroCity_DevonCorp_3F_EventScript_MrStone`, gated on `FLAG_DELIVERED_STEVEN_LETTER`, sets `FLAG_RECEIVED_EXP_SHARE` (272); **QUICK CLAW** — `RustboroCity_PokemonSchool_EventScript_Teacher`, sets `FLAG_RECEIVED_QUICK_CLAW` (275). Both flag names verified present in `modules/data/event_flags/emerald.txt`. Shape: navigate to the NPC, face, A-ride the dialogue, grade on **the bag** (both scripts branch to `Common_EventScript_ShowBagIsFull`, which gives nothing and sets no flag). ‼ These are ORDINARY-PLAY value, not story-critical: an Exp Share collected in Rustboro compounds over every later chapter, which is exactly the organic-play goal. **Enumerate the full gift list from the decomp before building** — `giveitem` in `data/maps/*/scripts.inc` — rather than adding them one at a time. |
| `#24-masterball` | ✅ **DONE 2026-08-12 — the MASTER BALL is collected, driven PASS.** `master_balls=1 nuggets=1 escaped=True whiteouts=0`, and the driver's acceptance now REQUIRES it (read from the BAG, since a full pocket makes `finditem` set no flag and give no item). ‼ It cannot be taken directly: both of its free neighbours are unreachable, so the route takes the **Nugget** at `(15,10)` first and steps onto the tile the vanished ball frees. No Electrode is ever faced. ‼ The return leg had to be re-derived after a driven failure — the first one walked across a warp panel; `can_walk` in `probe_aqua_hideout_graph.py` is now panel-aware. |
| `#24-impassabledirs` | ✅ **DONE 2026-08-13 — FIXED, BOTH HALVES, A/B PROVEN, AND GATED.** `modules/map_path.py`: the entry vector now starts all-True and CLEARS `[opposite(D)]`, and a NEW `PathTile.blocked_exit_directions` carries the decomp's *exit* rule, checked on the SOURCE tile in the A* expansion loop (`is_tile_accessible` is handed the NEIGHBOUR and structurally cannot express it). **THE A/B, on `VICTORY_ROAD_1F`:** before → `repro_impassable_dirs.py` exits **1** with **29/29** live tiles reading `[--S-]` against a correct `[NE-W]`, and `calculate_path` returns **NO-PATH from every single direction** — all 29 walkable tiles were **completely invisible to the planner**; after → exits **0**, 0/29 mismatches, and the legal approaches return `OK len=1`. **COLLATERAL CONTROL:** the `MOSSDEEP_CITY` block of `probe_ki59_routing_ab.py` (a map with zero such tiles) is **byte-identical across both arms** — the two arms were produced with real production code via `git stash`, not by re-implementation. **NEGATIVE CONTROL:** `SEAFLOOR_CAVERN_ROOM1` reports **0 live tiles and 0 mismatches in both arms**, confirming from production objects that the branch is inert there. **New gate `repro_impassable_dirs.py` is in `run_gates.py` (suite reached 17 with it — 18 since `audit_doc_consistency.py`, 2026-08-14 — all PASS, 124.3s).** ‼ **`probe_shoal_tide.py` corrected IN LOCKSTEP** (it replicated the inversion, so it agreed with production while both were wrong) — and its headline numbers **re-derived on the fixed model are UNCHANGED: LOW 278 / HIGH 0, all controls PASS**, so the user-delegated **"Shoal Cave is NOT adopted"** ruling stands and now rests on a correct model. ✅ **PROMOTED 2026-08-14, user-approved — sandbox↔custom drift is back to ZERO** (it had reached 5: `map_path.py`, `early_game.py`, `story_mode.py`, plus `counter_hunt.py` and `pokemon_party.py` on 2026-08-14). Verified by DRIVING, not diffing: `--driver ch20dive --build custom` → `ACCEPTANCE: PASS`, `repro_box_counter_move_test.py --build custom` exit 0, drift was re-measured 0 both directions *(history: at that promotion)*. Restore point `restore/2026-08-14-pre-promotion-5files`. History and the measurement that reprioritised this item follow. ‼ **MEASURED 2026-08-13 — the INVERSION IS REAL but the TARGET MAP IN THE OLD TEXT WAS WRONG.** `tools/story-dev/probe_impassable_dirs.py` (NEW) swept **all 518 maps**. **The bug is REAL:** `map_path.py:128-132` starts `accessible_from_direction` all-False and **sets** `[opposite]` True, where ground truth is start all-True and **clear** `[opposite]`. For `Impassable North` the shipped model is `[--S-]` — the *exact complement* of correct `[NE-W]` — so it refuses the three legal entries **and permits the one illegal one**. ⛔ **BUT: `map_path.py:118` is `if tile.collision != 0:` and the `Impassable` handler is its `elif`, so a collision≠0 tile NEVER REACHES IT.** Measured: **2,658 such tiles game-wide, 2,257 DORMANT (collision≠0), only 401 (15.1%) LIVE.** ‼‼ **ZERO of the Seafloor Cavern's 115 are live** (all `collision=1`) — so the old instruction "A/B on `SEAFLOOR_CAVERN_ROOM1` before the cavern chapter exists" **would have measured nothing**, and this is **NOT a §Ch20 prerequisite**. **Where it IS live:** SHOAL_CAVE inner 77 + entrance 12 + high-tide 9; **DESERT_RUINS 48 / ISLAND_CAVE 48 / ANCIENT_TOMB 48 (the REGI arc — the user's ask, 144 tiles)**; LILYCOVE contest hall 40 + lobby 8; ARTISAN_CAVE_B1F 34; VICTORY_ROAD 1F/B2F/B1F 58; MIRAGE_TOWER_4F 5; GRANITE_CAVE_B2F 4; a tail of 1-3. Live strings: `North` 347, `East` 27, `West` 24, `North and South` 3. ✅ **THE FIX IS SPECIFIED AND DE-RISKED** (decomp-verified `gOppositeDirectionBlockedMetatileFuncs` / `gDirectionBlockedMetatileFuncs`, `event_object_movement.c:893-905, 4715-4722`): `MB_IMPASSABLE_<D>` means **"the tile's `<D>` EDGE is a wall"**, blocking entry *and* exit across it. ⇒ (a) `accessible_from_direction = [True]*4` then clear `[opposite(D)]`; (b) **a NEW exit-blocking concept is required** — `PathTile` cannot express "may not LEAVE in direction D" at all, and without it the fix still lets the planner walk north off a wall (22 of Island Cave's 48 live tiles have open floor to their north). ✅ **Hazards pre-checked, all clear:** the four `_is_optional_blocker` salt tiles are plain `Cave`, not Impassable (so the fix cannot defeat the salt gates); `Secret Base Breakable Door` (0xBE, a directional impassable the code misses) and `Secret Base Impassable` (0xB9, a false friend that must stay OUT) both occur **0 times** in this ROM. ‼ **`tools/story-dev/probe_shoal_tide.py:364-367` REPLICATES the inversion** and must change in lockstep — see the note under `#24-shoalcave`/KI-54. **Per-string split (live/total), which BOUNDS the fix:** `North` **347**/2601 · `East` **27**/27 (all live) · `West` **24**/24 (all live) · `North and South` **3**/3 (all live) · `South` **0**/3 (all dormant). **Five of the ten producible strings never occur in this ROM at all.** ⚠ **THESE ARE STATIC ROM LAYOUTS, NOT RUNTIME TRUTH.** Three of the four biggest live maps rewrite themselves: `setmetatile` appears in `DesertRuins`, `IslandCave`, `AncientTomb` (those ARE the braille walls opening), `ShoalCave_LowTideInnerRoom` and `LilycoveCity_ContestLobby`; `setmaplayoutindex` in both Shoal Cave low-tide rooms. So 77/48/48/48 describe the **compiled** layout, not what is on screen. ‼ **The Seafloor conclusion is UNAFFECTED — no `SEAFLOOR_CAVERN_ROOM*` script uses either command** (checked across the full result set). **REMAINS: the fix itself + an A/B.** ⇒ **RUN IT ON `VICTORY_ROAD_1F` (29 live tiles)** — it is the cleanest target because it does NOT rewrite itself, unlike Island Cave / Shoal Cave. **With a NEGATIVE control on a Seafloor room proving the branch is inert there**, and the A/B must assert **both** directions (entry AND exit), never on the Seafloor Cavern alone. |
| `#24-pathsourcecheck` | ‼ **NEW 2026-08-12 (KI-60), code-verified.** `calculate_path` never runs its SOURCE tile through `is_tile_accessible` — it seeds the queue unconditionally. So a path requested *out of solid rock* returns OK (this produced the wrong "different components" story in KI-57's first write-up), and an invalid source reports a bare "could not find a path" instead of naming itself. Low-risk fix = raise a distinct error on an inaccessible source, but it is shared code and needs its own A/B. |
| `#24-mossdeepgym` | ✅ **DONE 2026-08-12 — §Ch18 runs END TO END and is WIRED into the ladder (Segment 18).** `--driver mossdeepbadge` gives `badge=True map=MOSSDEEP_CITY_GYM at=(23,8) controllable=True whiteouts=0`; `BADGE07_GET` set after 754 frames; anchor `saves/post_mossdeep_gym.ss1`. The ladder reached **19/24** with this item (current: **20 of 24 beats**, since §Ch19). ‼ An adversarial review then found a defect the PASS could not have caught (the whiteout path checked the map only at entry, and raised `RuntimeError` where the chapter catches `BotModeError`, so the recovery could never fire) — fixed and proven by `repro_gym_whiteout_guard.py`, which INJECTS the fault. History below. ✅ Leg 1 driven PASS (`--driver mossdeeptravel`, `whiteouts=0`, anchor `in_mossdeep_gym.ss1`). ✅ **KI-58 resolved:** the gym is a **ROTATING-TILE STATUE PUZZLE** — nine floor switches call `moverotatingtileobjects`, shifting every object on a matching coloured arrow one tile. ✅ **NEW 2026-08-12: `modules/story/mossdeep_gym_puzzle.py` simulates it, and `probe_gym_simulate.py` PASSES** — 11/11 loaded objects predicted on a live press, identity-keyed on `local_id`, plus a period-4 identity control on all five colours. Encoding derived from the ROM dump: band = `(mt-0x250)//8` (`0 Yellow 1 Blue 2 Green 3 Purple 4 Red`), code = `(mt-0x250)%8` (`0 Right 1 Down 2 Left 3 Up`), **codes 4/5 = that colour's switch**. ‼ Movement is a **rigid simultaneous rotation with NO occupancy check**; **nine TRAINERS rotate too**; statues are `graphics_id == 224`. ‼ **"5 counters mod 4" is unsafe** — use the full object-position tuple. ‼ `(23,7)/(24,7)` are collision-1 — target `(23,8)/(24,8)` facing NORTH, press A; they need **≥2 usable Pokémon**. ‼ `(21,6)` ejects to `(7,30)` and is **not flag-gated**. ‼ **Leaving the gym RESETS the puzzle**; internal warps preserve it. ‼ **Solving the puzzle AIMS THE TRAINERS AT YOU** — pressing yellow at `(3,30)` puts Maura adjacent and facing you; gym battles are a consequence of the mechanic, not a derail. ✅ **SOLVER + EXECUTOR BUILT AND DRIVEN 2026-08-12:** `--driver mossdeepgym` gives `at_leaders=True map=MOSSDEEP_CITY_GYM at=(23,8) controllable=True whiteouts=0`, the 117-step route walked in a single plan with zero re-plans; anchor `saves/at_mossdeep_leaders.ss1`. The BFS route matches both agent-derived routes switch-for-switch. ✅ **The Tate & Liza DOUBLE battle is built and driven** (`fight_the_leaders`): the ≥2-usable-Pokémon gate is checked up front rather than discovered, and the chapter allows three attempts because a whiteout leaves the gym and leaving RESETS the puzzle. ‼ Still UNEXERCISED: the executor’s own interruption branch (the trainer battles that fired were handled by the standard listeners) and the real whiteout path (both driven runs had `whiteouts=0`; the guard is proven by fault injection, not by a live loss). ✅ **AND the chapter now LEAVES the gym** (it was stranding the run on an eleven-tile island; the acceptance test now requires being outside). **NEXT: §Ch19, the Mossdeep Space Center** — groundwork + measured hazards in `modules/story/space_center.py` and `tools/story-dev/probe_ch19_hazards.py`; ‼ §Ch21 is BLOCKED by KI-63 (no Dive learner, party full) — beating the leaders already sets `VAR_MOSSDEEP_SPACE_CENTER_STATE=1` and unhides Team Magma + Steven. |
| `#24-spacecenter` | ✅ **DONE 2026-08-12 — §Ch19 runs END TO END and is WIRED into the ladder (Segment 19).** One chapter covers BOTH the Space Center defence and the Dive hand-over, because `chapters.py` grades chapter 19 on `RECEIVED_HM_DIVE`. Driven from `post_mossdeep_gym.ss1`: `dive=True hm08=True MOSSDEEP_SPACE_CENTER_STATE=3 map=MOSSDEEP_CITY at=(19,11) controllable=True whiteouts=0`, **CAN-CONTINUE OK(15wp)**. The ladder now runs **20 of 24 beats**. Anchors captured: `at_steven_2f.ss1`, `post_space_center.ss1`, `post_dive.ss1`. Drivers: `--driver spacecenter1` (legs 1-3), `spacecenter2` (the menu + multi battle), `spacecenter` (whole chapter; run it from `post_space_center.ss1` too — that PROVES the resume guards by skipping to leg 6). ‼ **THE CITY IS CUT IN TWO** until the forced cutscene runs: the gym victory SPAWNS five Team Magma NPCs onto the only land bridge (x=44, y=23-26) and our planner blocks loaded-object tiles, so leg 1 is TWO legs — trigger line, assert `VAR_MOSSDEEP_CITY_STATE == 2`, then the door. I first mis-blamed KI-59 for this; see `08-MISTAKES.md`. ‼ **THE STAIR GRUNT MUST BE TALKED TO** (`sight_radius = 0`, stands ON the only tile the stairs are reachable from) — navigating there can never succeed. ‼ **THE PARTY-SELECT MENU IS NOW SOLVED AND VERIFIED LIVE:** cursor slots 0-5 are mons, **6 = CONFIRM**, each pick is `A` (submenu) then `A` (ENTER) and **the cursor does not advance**; A on an already-picked mon DESELECTS it, so blind A-mash toggles for ever. Every pick is verified against `gSelectedOrderFromParty` — measured `[1,5,3,0]` against `INTENDED-PICKS [0,4,2]`, an exact match (Sceptile L48 / Mightyena L44 / Swellow L40). **Always bring 3**: the loss condition sums HP over the player's picks ONLY, so bringing fewer is strictly worse. ‼ **Losing is a RETRY, not an error** — the script calls `SetCB2WhiteOut` itself, halves the money and warps to the last heal location, but leaves the var at 2; leg 1's heal matters twice over because the anchor's respawn was measured to be **LILYCOVE**, across the sea. ‼ **§Ch19 nearly ended INSIDE Steven's house** — caught by the acceptance's `calculate_path` off the end tile, KI-56's rule for the third time. |
| `#24-remainingarc` | 🔜 ✅✅ **2026-09-07 — `KI-95`, `KI-93` AND THE L60 GRIND ALL SHIPPED OVERNIGHT; THE LIVE BLOCKER IS NOW `KI-96`. ⛔ **SUPERSEDED 2026-09-07 (evening): `KI-96` IS SOLVED AND DRIVEN — the live blocker is now `#24-regimeb-noescalation`.**** The party is at **L60** (`post_grind_L60.ss1`, PINNED — 623 battles, 0 whiteouts, `--driver ch24grind`), the Torment livelock is FIXED and the bot **beats Sidney** (⚠ on its last Pokémon, 5 of 6 fainted), and the faint chooser now ranks on expected damage (gate #39). ⛔⛔ **BUT LEVELLING ALONE DOES NOT UNBLOCK §Ch24:** §Ch23's chain now wedges in the in-battle PARTY MENU (`KI-96`, an unbounded `while PARTY_MENU: press A`, A/B'd as PRE-EXISTING and present in BOTH forks) before the League door. ⇒ **✅✅ **SUPERSEDED 2026-09-07 (evening) — `KI-96` IS SOLVED AND DRIVEN; ⛔ IT IS NOT THE NEXT JOB.** Read it for the ANSWER, not for work; the live queue is the `➡➡➡` marker in `04-HANDOFF.md`. *(was: read `KI-96` in `05-KNOWN-ISSUES.md` — it is the next job.** ⛔ All of it is SANDBOX-ONLY; for the live drift run `promote.py --check` (the authority; never restated here) — the arc-2 four were PROMOTED 2026-09-07 (user-authorised, verified by driving); the KI-96 probe fix, #24-truckleak, #24-pcpingpong and #24-hm07teach are sandbox-only — ⛔ **the batch that blocked promotion FINISHED 2026-09-08 (`x4-runs/20260907-203713`), so nothing is waiting on it; PROMOTING IS THE USER'S CALL**. *(This cell's own rule says its FIRST WORDS are what a skimmer acts on, and it advanced four times on 2026-09-06/07; a Tier 2 cold-start audit caught it still routing readers to the CLOSED `#24-ch23chain`.)* Older text follows. 🔜 **§Ch23 (VICTORY ROAD) IS A CHAPTER AS OF 2026-09-05 — ALL ELEVEN LEGS **AND** THE ORCHESTRATOR + SEGMENT 23 WIRING ARE SHIPPED AND DRIVEN. ⛔ DO NOT REBUILD ANY OF IT. ‼ **§Ch24 (THE ELITE FOUR) IS THE ONLY CHAPTER WITH NO DISPATCH AT ALL**, and §Ch23's CHAIN **PASSES** (`ACCEPTANCE: PASS`, `done=True`, `battles=16`, `whiteouts=0`, 2026-09-05) — *(this read "RE-DRIVEN 2026-09-05 AND IT FAILS FOR A KNOWN REASON: the party LOSES the leg-9 Katelynn+Quincy DOUBLE battle on VICTORY_ROAD_1F and whites out" — **SUPERSEDED THE SAME DAY: the chain now PASSES**, `done=True`, `whiteouts=0`)* (`ACCEPTANCE: FAIL`, `battles=16`, `whiteouts=1`, `outcome=BattleOutcome.Lost` at f67819). ✅ KI-90's fix HELD — same fight, same start frame (f56544) as the previous drive, but no raise and no hang: the bot could act, and lost. ⇒ ⛔ **RETRACTED 2026-09-05 — this read "the wall moved from a BOT DEFECT to a GAME PROBLEM (levelling/strategy)" AND IT IS REFUTED BY THE DRIVE LOG.** It is still a BOT defect: the bot entered the fight with **two mons already at 0 HP** after eight battles with no heal, and **no heal ever runs on this floor**. The opposition is **L43** against our L52/L48/L47/L47. ⇒ the wall moved from ONE bot defect (a hang) to ANOTHER (unwired healing). See `06-DECISIONS-LOG.md` / `08-MISTAKES.md` 2026-09-05. ⭐ MEASURED, not counted from memory: the last `_guard(...)` in `story_mode.py` is `"Victory Road (Ch23)"` and there is no Ch24 guard — `grep -oE '_guard\("[^"]+"' plugins/custom_modes/story_mode.py | tail -1`. *(An earlier draft of this clause said "THE LADDER IS 24 OF 24 BUILT". ⛔ I could not derive that denominator from the code — the older cells say "23 of 24" while ALSO listing TWO chapters as remaining, which cannot both be true. A number you cannot re-measure does not belong in a current-state file; the grep above can be re-run.)* ⛔ Its live item is `#24-ch23chain`; read THAT, not this cell.** *(superseded: this opened "IS UNDERWAY … LEG 1 IS SHIPPED" and pointed at `#24-ch23victoryroad`, whose own header then commanded rebuilding the orchestrator. This cell's own note demands its FIRST WORDS change when the item advances — this is the third time that was needed.)* ‼ The route legs and the Victory Road boulder puzzle remain; the ladder is **23 of 24** and only §Ch23 and §Ch24 (Elite Four) are left. ⛔⛔ **AND THE ONE THING A SKIMMER MUST NOT MISS: TWO BOULDER PUSHES SEAL VICTORY ROAD B1F FOR THAT VISIT — never push (4,7) or (9,10) SOUTH.** ✅✅✅ **§Ch22 IS A CHAPTER AS OF 2026-09-03 — GYM 8, JUAN, THE RAIN BADGE, WIRED AS SEGMENT 22 AND DRIVEN TO `ACCEPTANCE: PASS`. THE LADDER IS 23 of 24, AND ONLY VICTORY ROAD (§Ch23) AND THE ELITE FOUR (§Ch24) REMAIN.** ⛔ Read `#24-ch22chapter` for its detail, not this cell. ‼ *(This cell's FIRST WORDS are what a skimmer acts on — it opened with "§Ch20 IS A CHAPTER" through two whole chapters of work, and with "§Ch21 IS A CHAPTER" through one more. ⇒ when this item advances, change the FIRST WORDS.)* ✅✅✅ **§Ch21 IS A CHAPTER AS OF 2026-09-02 — ALL FIVE LEGS **AND** THE `_play()` WIRING ARE SHIPPED AND DRIVEN. ⛔ DO NOT REBUILD ANY OF IT.** `--driver ch21chapter` from `post_ch20.ss1` → `ACCEPTANCE: PASS`, `frames=95823` (MEASURED), `encounters=26`, `whiteouts=0`, ending SOOTOPOLIS_CITY (31,34) with the GYM WARP (31,32) reachable in 2 wp and HM07 in the bag. ‼ **IT ALSO MEASURED THE PARTY HANDOVER: §Ch21 has two heals and NONE after leg 3, so **MEASURED: `post_hm07.ss1` is SIX ALIVE at 629/694 (91%), lead 52/115 — NOTHING is fainted.** ⛔ *(A claim that it "ENDS chipped, one member fainted, lead 25/115" stood here on 2026-09-02 and was WRONG: that is the CHAPTER DRIVE's end party from a DIFFERENT run (`post_ch20.ss1` → legs 1-5), which was never captured to a fixture. An adversarial refuter caught it and my own re-measurement confirmed it — see `08-MISTAKES.md`.)* ‼ **BOTH states are real, and §Ch22 must handle the WORSE one:** a live §Ch21 handover arrives chipped HARDER than the pinned fixture suggests. ⇒ **§Ch22 inherits a chipped party and its first act is almost certainly the Poke Center (43,32), 22 wp away and MEASURED reachable.** ⇒ **§Ch23 — VICTORY ROAD IS NOW WIRED** (`chapters.py:280-286`, graded on `DEFEATED_WALLY_VICTORY_ROAD` for the READOUT — the DISPATCH gates on `ch23_chapter_done()`, which is that flag **AND** a position, because the flag fires at leg 5 of 11). *(superseded: cited `chapters.py:259-262`, which is Segment 21's neighbourhood — verified against the code 2026-09-05.)* ⛔ *(This read "NEXT IS §Ch22 — GYM 8, JUAN" until §Ch22 shipped on 2026-09-03; §Ch22's own items are `#24-ch22juan` and `#24-ch22chapter`, both CLOSED.)* Detail: `07-CHANGELOG.md` 2026-09-03. *(⛔ THIS CELL OPENED WITH "§Ch20 IS A CHAPTER AS OF 2026-08-24" THROUGH TWO WHOLE CHAPTERS OF WORK — a Tier 2 cold-start audit caught it, calling it "the exact P5 shape the rule was written for": the live status was buried ~3,000 words into a single cell. ⇒ when this item advances, THE FIRST WORDS OF THIS CELL are what to change.)* ✅✅✅ **§Ch20 IS A CHAPTER AS OF 2026-08-24 — ASSEMBLED, WIRED AND DRIVEN. ⛔ DO NOT REBUILD IT.** `modules/story/seafloor_cavern.py` (971 lines, nine legs + orchestrator) is wired as **Segment 19b (organic Dive) + Segment 20**, graded on `_done_var("ROUTE128_STATE", 2)` — never the pre-warp Kyogre flag. `--driver ch20chapter` drives the PRODUCTION entry point (not a copy) and returned **5/5 ACCEPTANCE: PASS**: clean (`done=True var2=2 surfing=True at=(38,24) ocean_path=True`), plus ALL THREE recovery paths exercised by fault injection — `room8_recoveries=1` for an in-room jam, and `route128_resumes=1` **with `room8_recoveries=0`** proving attempt 2 never re-dived into the permanently-disarmed trigger. ‼ Acceptance includes *and the bot can continue*: a real `calculate_path` to the open-ocean probe, not the 41-tile lagoon. ⚠ **NOT proven:** organic Dive in the same run (the driver injects it, so these are ASSEMBLY tests) and a LOST Archie fight (stochastic, 2W/1L measured; all five runs won). ‼ An adversarial review found **4 blockers, all in the orchestration glue** — the dropped per-push `try/except` (a jam skipped the fault-proven recovery), a once-only resume check, an unguarded `PathFindingError`, and a missing loop-head abort; fixing them exposed 3 undefined names on exactly those branches. ➡ **§Ch21 IS UNDERWAY, NOT UN-STARTED** (updated 2026-09-01): legs 1 + 2a + 2b + 3 + 4 **and 5** are BUILT AND DRIVEN (leg 5 shipped 2026-09-02) — **ALL FIVE LEGS EXIST, AND SO DOES THE `_play()` WIRING**: §Ch21 became a CHAPTER on 2026-09-02 (Segment 21, driven end to end — see later in this cell). *(This clause read "what remains is the `_play()` WIRING, which does NOT exist yet" for a few hours between the leg-5 commit and the wiring commit; a Tier 1 reviewer caught it contradicting the SAME CELL's own later text.)* ✅✅✅ **LEG 3 (THE APPROACH) SHIPPED 2026-09-01 — ⛔ DO NOT REBUILD IT.** `--driver ch21approach` from `post_wallace.ss1` → `ACCEPTANCE: PASS`, **all 14 readings, `missing=[]`**, `frames=34122` (MEASURED, replacing the spec's ~55,000 estimate), `encounters=9`, `whiteouts=0`, `pocket_attempts=1`, `method_ok=True`, `premise_ok=True`; fixture **`post_skypillar_door.ss1` PINNED** (⚠ party at 91% HP — no Poke Center after Sootopolis). THREE fault arms ran (the third added after an ADVERSARIAL REVIEW found a BLOCKER — the pocket recovery's OWN walk-back was not guarded against the exception it recovers from, so a second stall escaped the retry budget as a raw exception; it now raises a NAMED "stranded" error, proven by `POKEBOT_CH21_FAULT_POCKETWALKBACK=1`): `POCKETSTALL` → `pocket_attempts=2` and still PASS (**the pocket recovery was the leg's one designed-but-UNPROVEN component and is now a RESULT** — a second arrival DOES re-open the pocket, and the retry loop terminates); `BLINDWALL` → fails LOUDLY naming the step index, bounded, **no hang**. ‼ Three things were measured for the FIRST time: the ROUTE131 layout divergence read **live in-drive** (`planner=0x08417FE4 live=0x0845C1B0 agree=False`, and 0 of the 18 tiles the leg walks are live walls); a **blind step executed onto a tile our own planner calls a WALL** ((40,19) — no such step had ever been taken in this project); and the resting-tile rule's **first arrow-warp case**, which CONFIRMS it ((6,16), matching prediction) — while the SAME leg produced its first REFUTATION, `UNDERWATER_ROUTE126`'s rest being **(45,66)**, not the warp target (45,65) that BOTH build-spec critics hard-asserted. ⛔⛔ **AND THE FIRST DRIVE FOUND A DEFECT CLASS THE WHOLE TREE WAS BLIND TO:** `_map_layout_cache` (map.py:735-755) is keyed by **MAP ALONE**, so the LIVE and STATIC layout readers share one entry and whichever reads first wins FOR THE PROCESS — `calculate_path` silently inherits it. The bot walked into a 9x3 block of solid rock in Sootopolis; A/B proven (37 wp with 3 live walls → 35 wp with none, `evidence/2026-09-01-ch21-leg3-LAYOUTPIN-ab.txt`). New instrument **`tools/story-dev/probe_live_mapgrid.py`** reads `gBackupMapLayout` — the grid the GAME walks on — and is the FIRST reader in this tree that can observe `setmetatile`/`setmaplayoutindex` at all (KI-74 had been unobservable in principle). ✅✅✅ **LEG 4 (THE SKY PILLAR CLIMB + DESCENT) SHIPPED 2026-09-01 — ⛔ DO NOT REBUILD.** `--driver ch21climb` from `post_skypillar_door.ss1` → `ACCEPTANCE: PASS`, all 15 readings, `order_ok`, `frames=10079`, both DELIBERATE FALLS, RAYQUAZA awakened (5/1/1), all 7 floors pinned to CLEAN, SEVEN fault arms all FAIL for their own reason (evidence `2026-09-01-ch21climb-CLEAN.txt` + `-FAULTARMS.txt`). Fixtures PINNED: `post_wallace_scene`, `post_skypillar_summit`, `post_rayquaza_gone`. ‼ Its recon KILLED TWO PLANS before a drive: `_bounded_step` cannot express a fall (asserts SAME-map), and `_live_wall_tiles` is crack-BLIND. ✅✅✅ **LEG 5 (THE RETURN + HM07 WATERFALL) SHIPPED 2026-09-02 — ⛔ DO NOT REBUILD.** PART C ran FIRST as the queue demanded (`--driver ch21leg5probe`, `ACCEPTANCE: PASS`, P0-P6, `frames=16297`, predictions filed before the drive in `ai-research-notes/2026-09-02-ch21-leg5-PARTC-PREDICTIONS.md` and graded in `…-RESULTS.md`), then PART D (`--driver ch21return`, `ACCEPTANCE: PASS`, **all 13 readings, `missing=[]`, `order_ok`**, `frames=20705`, `whiteouts=0`, `hm07_in_bag=1`, `wallace_state=1`, `gym_door_wp=2`). Fixtures PINNED: `post_legends_calmed.ss1` (mid-leg, so the NPC half iterates in ~4,600 frames instead of re-swimming) and `post_hm07.ss1` (the chapter's end state). ‼ **GATE 1 SETTLED BY AN ARM WITH THE PIN REMOVED:** un-pinned, ROUTE131 -> ROUTE126 raises `PathFindingError` and the bot never moves — the pin is not an optimisation, it is the only reason a plan exists. ‼ **GATE 2 SETTLED:** the state-5 Sootopolis layout is SAFE — the pin is a NO-OP and 0 of 3600 tiles are open-to-planner/wall-live (the 10 diffs are all locked DOOR warps). ⛔⛔ **AND DRIVE 1 PASSED WHILE SEALING §Ch22:** `_ride_talk` returned mid-script, so Wallace never stepped off the (31,33) tile that blocks the (31,32) GYM warp, and the 'can continue' check had been aimed at the Poke Center, which is reachable either way. FIXED (ride now requires `not script.is_active`; new `R-GYMDOOR` reading) — see `08-MISTAKES.md` 2026-09-02 for that and for the held-button msgbox hang the fix then exposed. ⇒ **NEXT IS THE CHAPTER WIRING** — ✅✅✅ **§Ch21 IS A CHAPTER AS OF 2026-09-02 — WIRED INTO `_play()` (Segment 21) AND DRIVEN END TO END: `--driver ch21chapter`, `ACCEPTANCE: PASS`, `frames=95823` (MEASURED), `encounters=26`, `whiteouts=0`, ending SOOTOPOLIS_CITY (31,34) with the GYM WARP reachable in 2 wp. ⛔ DO NOT REBUILD IT.** The chapter ladder moves 20 → 21 of 24. ‼ It also measured what nothing had: the party STARTS chipped (one fainted at 80%) and **MEASURED: `post_hm07.ss1` is SIX ALIVE at 629/694 (91%), lead 52/115 — NOTHING is fainted.** ⛔ *(A claim that it "ENDS chipped, one member fainted, lead 25/115" stood here on 2026-09-02 and was WRONG: that is the CHAPTER DRIVE's end party from a DIFFERENT run (`post_ch20.ss1` → legs 1-5), which was never captured to a fixture. An adversarial refuter caught it and my own re-measurement confirmed it — see `08-MISTAKES.md`.)* ‼ **BOTH states are real, and §Ch22 must handle the WORSE one:** a live §Ch21 handover arrives chipped HARDER than the pinned fixture suggests., because §Ch21 has two heals and none after leg 3 ⇒ **§Ch22 inherits a chipped party**. ⇒ NEXT IS §Ch22 (Gym 8, Juan). ⛔ **A CLAUSE HERE CLAIMED `chapters.py` "does not yet consume `RECEIVED_HM_WATERFALL`" — THAT WAS FALSE and is corrected 2026-09-02:** `chapters.py:250` already grades §Ch21 on that flag and `progress.py:40` maps it, so the wiring needs NO `chapters.py` edit. ‼ What it DOES need: a gate on leg 1, which has no resume guard of its own (`sootopolis.py:194` swims to ROUTE126 unconditionally, impossible from zero-connection Sootopolis), and `sootopolis_reached()` (`:99`) is DEAD CODE so no shipped predicate exists for it. ⇒ the live status is in THIS item's headline above and in `04-HANDOFF.md`'s queue. Older text follows. 🔄 **THE SEAFLOOR CAVERN IS DRIVEN END TO END (2026-08-14, latest) — KYOGRE AWAKENED, THE ATOLL ESCAPE EXECUTED; what remains of §Ch20 is the CHAPTER ASSEMBLY.** `--driver ch20room9` (NEW) → `ACCEPTANCE: PASS` ×2 (runs 1 & 3): Rooms 1→8 re-proven, the `(17,42)` trigger (gate `VAR_SEAFLOOR_CAVERN_STATE == 0` verified live), the Archie SINGLE battle, the Kyogre chain ridden with three bounded milestones, release gated on **`VAR_ROUTE128_STATE == 2`** (‼ the first `releaseall` is a decomp-proven trap — Room 9's script tail releases on Route 128 BEFORE the Steven scene re-locks), landing `(38,22)` with all mid-warp invariants exact, **facing on release MEASURED `'Up'` ×2** (previously decomp-only), and the measured escape `(38,23)` → Surf `(38,24)` → `OCEAN-PATH OK len=5` to the dive tile. **10/10 pre-registered predictions held** (`ai-research-notes/2026-08-14-ch20-room9-drive-predictions.md`). ⚠ **Run 2 LOST the Archie fight — 2W/1L measured, the chain's ONE stochastic element** — the party arrives chipped (no heal in the cavern; run 3 telemetry: one mon fainted, lead 96/135, usable=5), and a lost run prints NO RESULT (whiteout → Manual → generator dropped; the `PRE-ARCHIE PARTY` line is the attribution record). Ruled in `06-DECISIONS-LOG.md`: a loss is a VALID BRANCH — the chapter carries a bounded whiteout-retry (each retry = full re-dive, ~25 min) + pre-boss readiness. ‼ Pre-run adversarial review caught the museum-greeter bug being re-written into the new ride loop (A mashed across the release seam) — fixed BEFORE run 1 with the gated `A`-if-`is_waiting_for_input()`-else-`B` press (`08-MISTAKES.md`). Counts: **R1 n=13, R2 n=10, R6 n=9, R3 n=8, R8 n=5, R9 full-chain n=2.** ⇒ **NEXT: ASSEMBLE §Ch20 AS A CHAPTER** (Segment 20; organic Dive via KI-63's wiring; Repel policy — Blocker 3; badge/move pre-flight — Blocker 4; whiteout-retry; grade the segment on `VAR_ROUTE128_STATE == 2` + escape + can-continue, NOT on the pre-warp Kyogre flag). ⛔ Still NOT a chapter; ladder remains 20 of 24. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 8 — THE BOT STANDS IN ROOM 9 (2026-08-14). `--driver ch20room8` (NEW) → `ACCEPTANCE: PASS` twice: once CLEAN (first attempt — 9/9 pushes, `attempts=1`) and once FAULT-INJECTED (`POKEBOT_CH20_FAULT=room8`: the jam-recovery handler was EXERCISED, not just written — exit to Room 3 via the `(5,12)` arrow warp, re-enter, all twelve boulders respawn, retry clean; `recovered=True attempts=2`).** OUR adjudicated 9-push sequence (⛔ step 9 faces **LEFT**) executed exactly as tabled; an independent offline refutation pass (our ROM reader + the pret decomp agreeing on all 12 boulder templates, simulation checker itself fault-tested) returned **SURVIVES** before the drive. Exit path `(5,4)→(5,2)` `OK len=2`, **no boulder on `(5,3)`**, `ROOM9 (5,4)` arrival, real step taken. **9/9 pre-registered predictions held** (`ai-research-notes/2026-08-14-ch20-room8-drive-predictions.md`) — including KI-77's window predicting **exactly 8 of 12** boulders visible at arrival. The Room-3 walk was extracted VERBATIM into `_cross_room3` so ch20room8 inherits it; neutrality proven by re-running `--driver ch20room3` → PASS. Re-proof counts now: **R1 n=10, R2 n=7, R6 n=6, R3 n=5, R8 n=2.** ‼ Adversarial review of the diff found one real defect BEFORE it ran: the recovery hardcoded `"Down"` instead of deriving the hold direction from the live tile (the `_cross_room6` rule) — fixed, and the fault run then showed the arrow warp fires during the navigate itself, which the hardcode would have handled blindly. ⇒ **NEXT: ROOM 9** — the 62-step walk to the trigger `(17,42)` (⛔ NOT `(16,42)`, which is plain floor), Archie, Kyogre, grade on `VAR_ROUTE128_STATE == 2` (never the Kyogre flag), and the atoll exit: step SOUTH to `(38,23)`, face Down, Surf onto `(38,24)`. ⛔ Still NOT a chapter — no module in `modules/story/`, drivers inject Dive; the ladder remains 20 of 24. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 3 — THE BOT STANDS IN ROOM 8 (2026-08-13). `--driver ch20room3` → `ACCEPTANCE: PASS`, reproduced twice.** The WALK route: 18 steps, **zero pushes**, ending `SEAFLOOR_CAVERN_ROOM8 (5,12)` with a real step. It re-proves every room beneath it → **Room 1 n=7, Room 2 n=4, Room 6 n=3**. ✅ **THE DOUBLE-BATTLE CLAIM IS CONFIRMED LIVE:** one trainer battle in Room 3, `is_double=True`, at exactly `(6,5)`, with `usable=6` asserted BEFORE the walk so the result is attributable. ⛔ **My own discriminator printed a false "REFUTED"** — it counted trainer battles run-wide and swept in the Room 1 grunt; **the instrument was wrong, not the claim**, and it was caught because `saw_double` was reported rather than graded and the raw log printed the map next to the judgement. ✅ Two wild encounters fired, one **between two Strength pushes** — closing a gap the Room 2 note flagged as untested. ✅ An adversarial review of increment 3 found a real BLOCKER (a design decision that lived only in a commit message, never in `06-DECISIONS-LOG.md`) — closed. ⇒ **NEXT: BUILD `--driver ch20room8`** (‼ it does **not exist yet** — it is the thing to write, not a command to run), **using OUR 9-push sequence** — ⛔ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit); a jam is recoverable by exiting to Room 3 and re-entering. **Then Room 9** (62-step walk to the trigger `(17,42)`, Archie, and the atoll exit). Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH THE ROOM 6 CURRENT MAZE AND THE BOT STANDS IN ROOM 3 (2026-08-13, latest). `--driver ch20room6` → `ACCEPTANCE: PASS`, first drive, 8/8 pre-registered predictions.** ‼ **THE FIRST EXECUTED CURRENT CROSSING IN THIS PROJECT** — Rooms 6/7 were planner-level only until now, and *a plan is not a walk*. ⇒ **"Rooms 6/7 need no solver" now rests on a WALK.** ⚠ The **endpoint** is proven, not the intermediate slide behaviour. ✅ **And Room 3's arbitration was confirmed LIVE in the same run:** `calculate_path((4,15)→(8,1))` = `OK len=18` **containing `(6,5)`** ⇒ **Room 3 is crossable PUSH-FREE, so its 7-boulder puzzle is OPTIONAL**, and the walk **must** take the trainer battle (decomp: a single **DOUBLE** battle, still unobserved live). ⛔ **An earlier agent pass called our build spec "REFUTED" on Room 3 and was ITSELF WRONG** — I propagated it into the docs before a deeper pass corrected it; *an agent's REFUTED needs the same two independent authorities as a CONFIRMED*. ‼ **The drivers also DERAILED instead of failing** on the one branch three green runs never took (`AttributeError` on `self.moved`) — found by adversarial review, reproduced via the new permanent hook **`POKEBOT_CH20_FAULT=room1`**, fixed, A/B proven. **Room 1 is now n=5, Room 2 n=2.** ⇒ **NEXT: `--driver ch20room3`** (the WALK: `navigate_to(ROOM3,(8,1))`, 18 steps, zero pushes, precondition ≥2 usable Pokémon, graded on both trainer flags SET), **then Room 8** with OUR 9-push sequence — ⛔ step 9 faces **LEFT, never UP**. Older text follows. 🔄 **§Ch20 IS DRIVEN THROUGH ROOM 2 (2026-08-13). `--driver ch20room2` → `ACCEPTANCE: PASS`, first drive, 10/10 pre-registered predictions.** It re-solves Room 1 from scratch every run (`FLAG_TEMP_*` objects respawn on map load), so **Room 1 is now n=3**. Route: smash `(8,7)` → **exactly three** north pushes of boulder `id 4` → `(6,1)` → `SEAFLOOR_CAVERN_ROOM6 (11,21)`, then a real `calculate_path` to the room's exit `(4,1)` = `OK len=13` **measured from inside** — matching what `probe_ch20_currents.py` predicted from outside. ‼ **THE HEADLINE IS A CORRECTION TO OUR OWN SHIPPED SOURCE:** `FLAG_SYS_USE_STRENGTH` read **False** right after the ROOM1→ROOM2 warp, so `early_game.py`'s *"NEVER CLEARED … once per SAVE"* was wrong — it is cleared on EVERY warp (`ClearTempFieldEventData` → `LoadMapFromWarp`). The old claim rested on a search for the SCRIPT MACRO `clearflag`; the clear is the C function `FlagClear`. The CODE was always safe (`strength_push` re-checks per call) — this was load-bearing documentation on top of correct code. Both comments fixed; **for the live drift run `promote.py --check` (the authority; never restated here)** — as of that entry the drifting files were (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) — the guard was PROMOTED 2026-08-16** (`early_game.py` was already one of them). ‼ **KI-77 CORRECTED TWICE the day it was filed:** the despawn window is derived (20x17, predicts our live dump 5/5) so **"armed in Room 8" is REFUTED** (Room 8 is 11x14, smaller than the window — the LARGE rooms are the risk), and the game **physically resets a pushed boulder to its template tile on despawn**, so the planner is fail-safe and never under-blocks. ⚠ **THE UNTESTED DANGER IS THE EXIT:** the chapter lands on `ROUTE128 (38,22)` **facing north**, and north is a **41-tile closed lagoon** with `allow_escaping: false` ⇒ **step SOUTH to `(38,23)` and Surf**. ⇒ **NEXT: ROOM 3 — arbitrate first; it is NOT the walk the spec calls it (7-boulder puzzle omitted, trainers unavoidable on the push-free line, and a boulder can block the `(9,13)` retreat warp).** Room 8 is already adjudicated — use OUR 9-push sequence, and ‼ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit). Older text follows. 🔄 **§Ch20 INCREMENT 1 IS DRIVEN AND PASSING (2026-08-13): the bot is INSIDE the cavern and through ROOM 1.** `--driver ch20room1` → `ACCEPTANCE: PASS` first drive — ingress `legs 5/5`, `ROOM1 (5,18)`, Rock Smash + **two `strength_push`es verified by `local_id`** (boulder 1 → `(5,12)`, boulder 2 → `(13,11)`), ending `ROOM2 (10,7)` controllable with a real step taken. ‼ **The A/B is the result, not the arrival:** `calculate_path(→ (11,11))` went `PathFindingError` → `OK len=6` with live objects on both arms, which turns `probe_ch20_interior.py`'s Room 1 NO-PATH from a **lower bound** into a **measured fact**. 6 of 7 pre-registered predictions held (`ai-research-notes/2026-08-13-ch20-room1-drive-predictions.md`). ⛔ **AND THE ROUTE HAD TO BE ARBITRATED FIRST — our own build spec was WRONG about Room 1.** It claimed an *exhaustive* search proves the `(5,11)` boulder must be pushed **north**; the decomp and our own ROM both say `(5,10)` and `(5,12)` are `collision=0 elevation=3 'Cave'`, so **either** direction is legal and the uniqueness claim is false. Upstream's **south** push ships and was confirmed live. ⇒ ‼ **The spec's Room 2 and Room 8 "exhaustive" sequences are UNAUDITED — arbitrate each against the decomp AND `puzzle_solver.py:395-454` before driving it.** ‼ **NEW: KI-77** — `get_map_objects()` is a **camera-range window**, so a pushed boulder's vacated tile is re-blocked once it scrolls off screen; benign in Room 1, **armed in Room 8's nine pushes**. ⇒ **NEXT: arbitrate Room 2, then drive `--driver ch20room2` the same way (measure → A/B → solve → can-continue).** Older text follows. 🔄 **§Ch20 IS FULLY SCOPED AND UNBLOCKED, NOT YET BUILT (2026-08-13).** ✅ Its blockers are gone: **KI-63 resolved** (the bot acquires Dive by playing), the **dive leg is driven 6/6**, and **KI-59 never gated it** (retracted — 0 of the cavern's 115 tiles reach the buggy branch). **Artefacts to build from:** the 11-leg spec `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`, the Area Atlas `probe_ch20_interior.py`, and `probe_ch20_currents.py`. **Shape:** Rooms 1/2/3/5/8 are **STRENGTH-BOULDER** puzzles, Rooms 6/7 are **current mazes** (‼ routable by our planner — 4/4 predictions, no solver needed), Rooms 4/9 split by terrain. ‼ **ROCK SMASH IS MANDATORY** — Strength alone is physically stuck in Room 1. ‼ **Trigger tile is `ROOM9 (17,42)`, NOT `(16,42)`.** ‼ **Grade on `VAR_ROUTE128_STATE == 2`, not the Kyogre flag** — the flag is set before a forced warp into a SECOND cutscene that lands on a **sandbar the bot must Surf off**. ‼ **Losing to Archie resets the whole dungeon**; **puzzle state resets on every map re-entry**. ⇒ **NEXT: DRIVE IT, leg by leg** — the interior was measured from OUTSIDE, so its per-room routing is a LOWER BOUND. Older text follows. 🔄 **§Ch18 + §Ch19 DONE; §Ch20/§Ch21 remain.** The path to the end of the Aqua/Magma story, decomp-gated: ✅ **§Ch18** Mossdeep Gym → `BADGE07`; ✅ **§Ch19** Mossdeep Space Center **and** Steven's **HM08 Dive** → `FLAG_RECEIVED_HM_DIVE` (both in Segment 19 — they are one chapter in `chapters.py`), which also unhides the Seafloor Cavern entrance guard; ⛔ **§Ch21** Seafloor Cavern (Kyogre) — **BLOCKED BY KI-63**: HM08 is in the bag but **no party member can learn Dive and the party is full**, so `#24-pc` is a PREREQUISITE, not a later nicety. ‼ My handoff had said the Seafloor Cavern was next — it was three beats away, and Dive was the real gate. Checking beat the assumption. ⛔ **RETRACTED 2026-08-13 — "KI-59 is armed in the Seafloor Cavern" is FALSE and was never a §Ch20/§Ch21 prerequisite.** The 115 `Impassable *` tiles are real, but **every one has `collision=1`**, and `map_path.py:128` is the `elif` of `if tile.collision != 0:` — so **none of them reach the buggy branch**. Measured over all 518 maps by `probe_impassable_dirs.py`; re-measured in a fresh process in reverse order as a cache-poisoning control (KI-73), both agree. The prescribed A/B on `SEAFLOOR_CAVERN_ROOM1` would have shown a zero delta and invited the wrong conclusion. KI-59 is still REAL — it is live on 401 other tiles, chiefly the **Regi tombs** — but it does **not** gate the cavern. See `#24-impassabledirs`. Superseded text: KI-59 is armed in the Seafloor Cavern (115 `Impassable *` tiles across Rooms 1-9) — fix it with an A/B on `SEAFLOOR_CAVERN_ROOM1` BEFORE the cavern chapter exists. | ⛔⛔ **[SUPERSEDED 2026-09-01 — LEG 3 SHIPPED. THE CELL BELOW IS 2026-08-28 HISTORY AND ITS "LEG 3 ITSELF IS NOT BUILT" IS FALSE.** It survived BOTH Tier 2 audit rounds because the leg-3 commit rewrote the FIRST cell of this row and left the THIRD — the P5 shape exactly: a fact in three places, two updated. See this row's opening cell for the live status.]** ✅✅ **§Ch21 LEGS 1 + 2a + 2b ARE BUILT AND DRIVEN; LEG 3 IS FULLY SPEC'D AND GATED (2026-08-28)** — `modules/story/sootopolis.py` + `--driver ch21dive`/`ch21escort`/`ch21cave`, all `ACCEPTANCE: PASS`; fixtures `post_sootopolis_arrival.ss1`, `post_steven_escort.ss1`, `post_wallace.ss1` PINNED. Leg 3 step 0 MEASURED (§4.11's answer is the RESTING tile **(31,17)**, not (31,16)); the Sky Pillar atlas pass and the **ROUTE131 pre-build gate** are DONE (`probe_ch21_route131_live.py`, offline, fault-tested — SET B = layout #318, 116 tiles open-in-A/WALL-in-B). ⛔ *(superseded — see the marker opening this cell)* **LEG 3 ITSELF IS NOT BUILT**; leg 5 (the return, HM07) did not exist WHEN THIS CELL WAS WRITTEN — ⛔ it SHIPPED 2026-09-02, and so did the `_play()` WIRING (Segment 21) — see this row's opening cell. *(the trailing "STILL NOT wired into `_play()`" that stood here is SUPERSEDED.)* ➡ **§Ch21 RECON IS DONE 2026-08-24 (the chapter is NOT built): the routing is closed on paper, the Mach Bike question is SETTLED (not needed), and the §Ch21 ATLAS in `12-STORYMODE-DESIGN.md` carries the measured staircase + the FOUR hang/strand hazards. ⛔ READ THE ATLAS BEFORE WRITING ANY Ch21 CODE — the ascent REQUIRES a deliberate fall through `4F (6,4)`/`(7,4)`, which no pathfinder here can propose.**
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

### 5. ✅ DUPLICATE / OVERLAPPING IDS — CONSOLIDATED 2026-08-10 (user-approved) — 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-08, R3 budget).
- [x] ⛔ CLOSED bookkeeping — which duplicate IDs were merged, and why. Not a live item.

### 6. CLOSED BY THIS TRIAGE (evidence in each entry)
* `#24-leadcounter` — shipped; `is_hunted_counter` is in `team_policy.lead_rank_key`.
* `#24-counters` phase 2 — shipped and batch-validated repeatedly (z = +3.24 on Machop).
* the "READY TO APPLY THE MOMENT BATCH `20260802-160603` LANDS" heading — that batch landed
  2026-08-02.

### Marker states (documented 2026-07-27 — the file uses THREE, not two)
| marker | meaning |
|---|---|
| `- [ ]` | open — not started, or started and not landed |
| `- [~]` | **partial** — built but not fully verified/promoted, or v1 done with follow-ups |
| `- [x]` | done |

⛔ **NO COUNTS ARE QUOTED HERE ON PURPOSE — `lint_docs.py` prints them and IS the authority.**
This table carried `80 / 17 / 37` from 2026-07-27 until a 2026-08-17 audit recounted the boxes and
measured **98 / 22 / 95** — stale by +18 / +5 / +58, and it had survived every doc pass since.
‼ A hand-typed tally in a file whose items change daily is stale the moment it is written; this is
the same rule the handoff's LINE BUDGETS block already applies to its own limits. **Count the
boxes** (`grep -c '^- \[x\]'`), never re-type a tally.

‼ `- [~]` is load-bearing and was previously undocumented: several `[~]` items read as
"DONE" in their text (e.g. `#24-move`, `#24-resume`) while still carrying open follow-ups.
Do not treat `[~]` as either finished or unstarted without reading the entry.

**Status audit 2026-07-27** (`#doc-audit-1`, partial — see `#doc-audit-2`): 98 distinct
`#`-ids carry a checkbox; exactly **one** id had a genuinely conflicting status
(`#24-pokenav-faithful`, now cross-linked — it is a legitimate RECURRENCE, not a
bookkeeping error). No item marked `[x]` was found whose code is missing. A full
open-vs-built sweep of all 80 open items has **not** been done.

## Now (active focus)

### 📦 SESSION END 2026-08-05 — **ARCHIVED 2026-09-04 to `28-HANDOFF-ARCHIVE.md` (387 lines, VERBATIM, nothing deleted).**

- [x] **Moved because this file sat at its 3,600-line cap for three commits and R3's own wording names the cause: "an archive is forming inside a current-state file". This block declared itself HISTORICAL in its own heading.** ‼ Its opening line records that the heading read "THE CURRENT TOP OF THE LIST" for a month over a stale suite figure — the exact failure mode that keeping spent content in a current-state file causes. Slugs it contains, preserved and findable in the archive: `#24-cavethread`, `#24-ch21climb-whiteoutarm`, `#24-driftassertions`, `#24-driftreduction`, `#24-gymwhiteoutgatehang`, `#24-handoffbudget`, `#24-hmteachloop`, `#24-ki59archiveheader`, `#24-livegridreader`, `#24-logcollision-siblings`, `#24-organicteam`, `#24-orphans`, `#24-partycap`, `#24-pcoverflow`, `#24-pcoverflow-proof`, `#24-probecountgate`, `#24-roster`, `#24-skypillarprobewrites`, `#24-stdoututf8gate`, `#24-zerokocounter`, `#26-gatestartupcontention`.

### ✅ `#24-abortrecoveryresiduals` — ALL THREE RESOLVED 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted).
- [x] ⛔ DO NOT REDO. Full detail in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ✅ `#24-brokenrepros` — DONE 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ✅ `#24-p2headergate` — DONE 2026-08-23 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ‼ `#24-pluginwhiteoutnoyield` — an UPSTREAM bug: the plugin whiteout hook has NEVER run (filed 2026-08-23)

- [ ] **VERIFIED, not reported second-hand.** `modules/modes/_listeners.py:567` calls
      `plugin_whiteout()` **bare** — no `yield from`. `plugin_whiteout` IS a generator function
      (`modules/plugins.py`, `-> Generator`, contains `yield from`), so the generator object is
      created and immediately discarded and **no plugin's `on_whiteout()` hook has ever executed**.
      ⛔ **UPSTREAM, NOT OURS:** identical at `40cakes repo/pokebot-gen3/modules/modes/_listeners.py:536`,
      so it must NOT be fixed in the mirror. Fixing it in our forks is a DIVERGENCE and needs a
      DIVERGENCE-LOG entry.
      ⚠ **Currently a NO-OP for us** — no plugin in our tree implements `on_whiteout`; StoryMode's
      handling goes through `bot_mode.on_whiteout()` at `:566`, which does run. So this is latent,
      not live. ‼ It becomes live the moment anyone writes a plugin whiteout hook and quietly gets
      nothing. Scoped: exactly 1 bare call out of 10 generator functions in `plugins.py` — an
      isolated slip, not a pattern.

### ‼ `#24-harnesswhiteoutdrop` — 36 harness runs dropped to Manual on a whiteout (filed 2026-08-23)

- [ ] **Found while assessing `#24-abortrecoveryresiduals` (a).** 36 genuine
      `[MODE] Story -> Manual (message='Player whited out...')` transitions, ALL in story-dev harness
      profiles (`repro-*`, `nc-*`, `nat-*`, `mt1/2`, `ki66single`, `hpstart`, `item-old`, `jp-post`)
      and **never in the batch runs**. Diagnosis: `on_whiteout()` reached something that was not a
      `StoryMode`, i.e. a harness pushing `run()` without setting `context.bot_mode_instance`, so the
      custom handling never engaged and the listener fell through to `set_manual_mode()`.
      ⇒ **This is a TEST-FIDELITY defect, not a bot defect:** any harness driver that whites out
      silently stops behaving like the real mode from that point on, so whatever it was measuring
      afterwards is suspect. ➡ **RECON 2026-08-26 (static sweep, spot-verified): the filed
      mechanism is REFUTED AS STATED** — all 67 driver branches (+ an else fallback,
      `story_harness.py:10551`) DO set `context.bot_mode_instance`, and the frame loop passes that
      instance to listeners (`:10620`). Two candidate mechanisms survive: (a) the mode those old
      profiles ran was a NON-Story mode whose inherited `BotMode.on_whiteout()` returns False
      (`_interface.py:191` — verified) → Manual by design; (b) assignment runs ONLY on
      stack-empty frames (`:10286`), so a stale instance can persist. ✅ **THE LOG MINING RAN the
      same day** — corrected analysis in `ai-research-notes/2026-08-26-whiteoutdrop-log-tally.md`:
      **26/36 ran named NON-story drivers (expected drops, not defects); the other 10 are
      UNRESOLVABLE from the logs because the run header never records `--driver`.** ⇒ NEXT: add
      `driver:` to the harness run header (2 lines + one proving boot); the mixin-adoption
      question for recon drivers is the USER's call.

### ‼‼ `#26-manualderails` — PRODUCTION derails to MANUAL around Fortree and Mossdeep (USER REPORT 2026-08-26)

**USER-OBSERVED, single live instance, Mudkip starter:** the bot *"works really well but has some
derails where it reverts to MANUAL"*, clustered **around Fortree and Mossdeep** — and ‼ **when the
user flips it back to Story mode it continues normally.** That recoverability is the diagnostic gold:
whatever gives up is a GUARD or RETRY-EXHAUSTION handing off via `set_manual_mode()`, not a wedge —
the underlying navigation still works on re-entry.
**Plan (the user's own suggestion):** an `--lanes 8` batch, then read the debug logs for the derail
signatures — WHICH `_guard()`/abort path fired, on which map, at what point. ⛔ Batches answer
FREQUENCY; once a signature is in hand, the fix is proven by a targeted driver, not more batches.

➡ **FORTREE HALF DIAGNOSED 2026-08-26 (31 finished bundles mined; MECHANISM read from code):**
* Dominant signature: the **Winona hopeless-gate** — `story_mode.py:1919` raises *"N losses with no
  super-effective answer … Grinding levels will not fix this"*. **530 lines corpus-wide, ALL 31
  bundles incl. the newest; 111 runs burned their budget on it.**
* ⛔ **ITS PREMISE IS MEASURABLY WRONG SOMETIMES:** `20260811-130454/L01` lost twice to Winona then —
  same team shape, NO super-effective answer, lead SWELLOW — **won the Feather Badge on retry.**
* **WHY THE USER'S FLIP WORKS, precisely:** losses live in `self._loss_ko_history` (PER MODE
  INSTANCE, `story_mode.py:1153`) and the counter ladder gets ONE attempt per boss per run — once it
  fails, **every later derail in the same instance deterministically re-raises with zero new
  information**, burning the 5-derail budget → `main.py:151` → `set_manual_mode()`. Flipping back
  builds a FRESH instance: losses reset, ladder re-armed, the bot re-fights — and often wins.
  **The budget was exhausted, not the situation.**
* ⛔ **THE HONEST-STOP RULING STANDS** (`06-DECISIONS-LOG.md` 2026-07-30 — do NOT delete the raise).
  ✅ **THE SECOND WIND IS SHIPPED 2026-08-26, BY THE BOOK:** the `--driver secondwind` arm was
  built FIRST and measured on unmodified code (`era=TODAY`: RAISE x5 + re-arm RAISE, matching the
  hand-computed discriminator exactly), THEN the fix landed (`era=AFTER`: SECOND_WIND +
  PLAIN_ESCALATION x4, ZERO raises, and ⛔ the re-arm control still RAISES — the 2026-07-30
  honest-stop ruling is COMPLIED WITH, not reopened). Once per boss per run; both natural resets
  (manual flip, per-run reset) re-arm it; the per-run-state gate enforces the reset.
  Evidence: `evidence/2026-08-26-secondwind-AB.txt`. ⚠ The arm proves the DECISION layer (it
  drives `_prepare_for_fight` directly, the ki80ladder pattern); the end-to-end pass through the
  real derail loop is measured by the next post-fix batch, discriminator: no five-fold
  hopeless-gate repeats before Manual. ‼ The arm's predicted casualty (ki80ladder)
  was confirmed then fixed — and that run exposed a PRE-EXISTING stale-era rot in ki80ladder
  (proven at pristine HEAD), fixed the same hour.
* Secondary: KI-36 battle wedges at the gym (last seen 20260810); cutscene-wedge family (absent from
  the newest 7 bundles — already fixed).
➡ **MOSSDEEP HALF — FIRST DATA EVER, mined MID-BATCH 2026-08-26 (⚠ interim; final counts when the
  batch lands):**
  * ✅ **THE GYM ITSELF IS CLEAN: 5 of 5 lanes that reached it passed badge 7, ZERO derails inside.**
    The user's "around Mossdeep" is the era, not the gym.
  * ⛔ **NEW SIGNATURE 1 — the unfleeable-battle freeze (3 lanes):** became `#26-fleefreeze`,
    ✅ FIXED + LIVE-VALIDATED (zero freezes in both post-fix batches) — see its entry.
  * ⛔ **NEW SIGNATURE 2 — the degraded-party spiral (L08):** party fell to ONE viable mon; the
    Tate & Liza DOUBLE-battle preflight correctly REFUSED ("need 2 Pokemon able to fight; the party
    has 1") — and then recovery could not path out (`(23,8) -> (6,35) @ MOSSDEEP_CITY_GYM` refused;
    a MAUVILLE heal target refused too), burning 5 derails. The refusal was right; the RECOVERY
    (heal-then-return, or exit the gym at all) is what is missing.
  * *(interim Winona/type-loss tallies superseded by the final numbers below.)*
➡ **BATCH COMPLETE 2026-08-26 — FINAL NUMBERS (baseline: `ad37949b` pre-fix production code):**
  * **50 boundary-marked runs: 6 finished / 44 derailed** (measured from the run-boundary lines
    myself — ‼ the mining agent reported "0 finishes" and was WRONG; the harness's lane table and
    my own grep agree on 6. Verify-the-agent, again). Treecko lanes: **0 finished of 9** — the
    user's starter concern is now a measured fact.
  * ⛔ **§Ch20 RAN IN A BATCH FOR THE FIRST TIME — and the TEACH BUG killed it.** L01 debug-log
    081321: reached the Seafloor Cavern, SOLVED ROOM 8, exited to ROUTE128 — then died to
    *"Teach flow finished but Linoone does not know Surf"*. On PRE-fix code: this is the exact path
    `#26-surfteachchain`'s D1/D2 gates fix, now measured as a run-killer (~9% of endings, 5 runs).
  * **The freeze signature is settled:** both frozen contexts are **MAGMA_HIDEOUT (24,86)/(24,91)
    during the "to Fortree" stage** (the interim "To Lilycove" label was wrong), one frozen INSIDE
    `EventScript_DoNoIntroTrainerBattle` — a NO-INTRO TRAINER battle, which can never be fled.
  * **Treecko's Surf-chain corner measured:** L03 085044: *"Cannot hunt a Surf learner: no Poké
    Balls and no money to buy any"* — the resource-depleted end of the hunt, filed with D3-D6.
  * Winona: **15 run-ending derails this batch** (treecko/torchic lanes), no loss-then-win observed
    IN THIS BATCH (the premise-refutation win is from 20260811/L01). Agent-mined ranking (⚠ its
    finish count was wrong, so treat ranks as indicative): boss type-loss 21, watchdog 9, nav 6,
    Surf-teach 5, handler wedge 4.
➡➡ **POST-FIX VALIDATION BATCH MINED 2026-08-26 (`20260826-130441`, code `dce95b4a`, 300 min,
  VERDICT OK, headers 39/39 clean). The four PRE-REGISTERED discriminators, graded:**
  * **(1) FINISH RATE: PASS — 8/31 completed (25.8%) vs baseline 6/50 (12.0%).** Same wall-clock,
    fewer + LONGER runs (runs die deeper). Mudkip lanes 5/10 finished (L02 **4/4**); ⛔ Treecko
    **0/6** — the design-gap half is untouched, as expected (D3-D6 + `#24-roster`).
  * **(2) SURF-TEACH: PASS, instrument-honest.** At DOUBLE the exposure (10 involved runs vs 5),
    **7/10 finished through the failure** (baseline 4/5 by the SAME stdout instrument);
    surf-as-last-derail 2 vs 1. ⚠ The old "~9% of endings" figure came from the mining agent whose
    totals this entry already flags as wrong — by symmetric instruments the teach failure is now
    overwhelmingly non-fatal at higher exposure. D1b (failure-phase exit fault arm) is STILL unproven.
  * **(3) FLEE-FREEZE LIVE ARM: PASS, decisive** — `[KI-52] … escape impossible (a partial-trapping
    move …) -> FIGHTING ON` fired repeatedly on the exact Torkoal signature; **ZERO
    `BattleScript_PrintCantEscapeFromBattle` freezes corpus-wide** (baseline: 3 lanes frozen); zero
    KI-47 nets on that signature. The 3 KI-47 nets present are ALL the `#26-battleitemwedge` /
    action-selection family — which is NOT in this batch's code and rides the NEXT one, as filed.
  * **(4) HOPELESS REPEATS: ⛔ FAIL AS PRE-REGISTERED — WORKING AS DESIGNED.** 27 live SECOND-WIND
    firings end-to-end (the proof the arm could not give); 17 resolved with NO repeat cluster. But
    10 runs still burned **five same-count raises + boundary echo AFTER their one wind was spent**
    (counts frozen: 12/12/12…, 25×5, etc. — deterministic, zero new information). That residue IS
    the ruled once-per-boss design. ➡ **OPEN QUESTION FOR THE USER (do not build unilaterally):
    once the wind is spent and a raise repeats with an UNCHANGED loss count, should the run go
    straight to Manual instead of burning ~4 more derail cycles?** (Saves dead time on genuinely
    hopeless runs; the honest stop itself stays.)
➡➡ **SECOND POST-FIX BATCH MINED 2026-08-27 (`20260826-185918`, code `86eaf8f3`; the manifest's
  `-dirty` was DOCS-ONLY, verified; 300 min, VERDICT OK):**
  * **Finish rate 12/32 = 37.5%** (12.0% → 25.8% → 37.5% in one day); Mudkip lanes 8/10.
    **11 of 12 Surf-teach-involved runs FINISHED.** D4 shape unchanged (20 winds, 7 burns).
  * ‼ **FIRST TREECKO FINISH EVER** (L07 run 2 — the real Ch20-done line; ⚠ frame count zeroed
    by a mid-run emulator reset).
  * ‼ **THE TREECKO WALL, NAMED by a clean run-ender:** *"No party mon can learn Surf and the
    party is full — needs PC box management (`#24-pc`) or a manual swap"* (L07 run 3, stage 14)
    — the `#24-roster` WITHDRAW half measured as a run-ender in production's own words.
  * **`#26-battleitemwedge` live arm: VALIDATED** — its KI-47 family **2 → 0** over 572 item
    flows, 577 `bag-not-open-yet` re-presses recovering eaten As. The 2 remaining nets are the
    `handle_fainted_pokemon`/FaintedMonTry family (KI-66 residual area) — the NEXT wedge target.
    CantEscape freezes still ZERO.

### ‼ `#26-surfteachchain` — D1/D2 GATES SHIPPED 2026-08-26 (ordinary case A/B-clean); D3-D6 residuals remain

**SHIPPED:** the ride loop's blind `_f % 3 → A` and the post-select loop's blind A are GATED (A only
in a menu / text / waiting-for-input; else B) + a FAILURE-PHASE EXIT (30 stable overworld frames
without the move learned → break; the honest raise fires ~8,000 frames sooner and never touches the
NPC). The museum-greeter shape verbatim, armed only in the Surf seam (indoors next to Wally's dad,
Norman battle tail resident) — which is why Rock Smash with IDENTICAL code stayed clean (outdoors,
quiet map). Ordinary-case arm: `--driver teachfull` replace-path → `learned=True, ride_exit=learned,
ride_frames=479`. ⚠ HONEST LIMIT: the failure-phase exit is NOT yet exercised (needs a teach-failure
fault hook). **Also shipped:** the hunt fallback flip `grounds[-1]` → `grounds[0]` (measured
incident: the SURF hunt sent to Surf-gated ROUTE119).
✅ **LIVE VALIDATION 2026-08-26 (batch `20260826-130441`):** at double the exposure, 7 of 10
teach-failure runs FINISHED anyway — the gates convert the run-killer into a recovered stumble.
Full discriminator-2 grading (and the ~9%-figure correction): `#26-manualderails`' batch section.
⛔ Treecko lanes 0/6 — the design-gap half is measurably still the cost.
**HALF 2 ANSWERED BY AUDIT:** the guarantee EXISTS — Segment 12c wires
`ensure_hm_learner_making_room(HM03)` post-Norman; a slot is freed BEFORE the catch (never lands in
the PC); sole-carrier protection holds; catch cap 4 keeps runway. Per-starter: Mudkip line
self-learns; Treecko/Torchic hunt Zigzagoon/Lotad on R102, Petalburg's doorstep.
**RESIDUALS:** D1b fault arm (above); D3 `_select_forget_slot` blind relative scroll assumes cursor
slot 0 on RE-entry — ‼ DECOMP RECON DONE 2026-08-26 (`ai-research-notes/2026-08-26-d3-forgetmenu-
cursor-decomp.md`, NOTE not truth): cursor RESETS on re-entry (screen freed + AllocZeroed), but
re-entry inserts an EXTRA "replace move?" YES/NO before the selector — the D3 hazard is FLOW
desync, not cursor drift; needs a live probe before code changes; D4 the A-cadence can race
`Task_HandleChooseMonInput`; D5 per-frame press cadences; D6 cheap hardening — step OUTSIDE Wally's
house before teaching (mirrors Rock Smash's clean seam); the KI-63 making-room deposit path has ZERO
recorded live firings; Wingull HM03 decomp cross-check. *(original filing:)*

📦 *(original A-spam observation: fixed by the D1/D2 gates above; full quotes in
`07-CHANGELOG.md` 2026-08-26 + git history of this entry.)*
⛔ **HALF 2, THE DESIGN GAP:** the user's test bot was MUDKIP, which learns Surf itself. **A
Treecko/Torchic run may hold NO Surf-capable pokémon at this point.** Required: an organic
surf-learner path — capture a suitable pokémon, and if the party is full, ensure it ends up IN the
party (PC trip), before the story needs Surf. ‼ The Dive equivalent already exists and is DONE
(`ensure_hm_learner_making_room`; its driver is likewise complete — cited here as the PROVEN PATTERN
to copy, ⛔ not as work to run) — establish whether Surf has an equivalent, and if not, build one
shaped like the Dive one. Anchors: `norman_done.ss1`, `prenorman_fodder_grind.ss1`.

### ✅ `#26-mossdeeppuzzlespeed` — FIXED 2026-08-26, A/B-PROVEN ~2.9x: ~62k → ~21k frames (~17.2 → ~5.8 min)

Bounded PRE-TURN (`TURN_TIMEOUT_FRAMES=32`) removed the 58% sink; all five safety checks kept and
silent on both arms. Evidence `evidence/2026-08-26-mossdeep-speed-AB.txt`; narrative + original
filing in `07-CHANGELOG.md` 2026-08-26. ⛔ Fixes B/C deliberately NOT taken.

### ✅ `#26-fleefreeze` — FIXED 2026-08-26, GATED as #32 — and the LIVE arm LANDED: confirmed in batch `20260826-130441`

`_escape` delegates to the inherited KI-52 `_handle_flee` on the escape-impossible branch instead
of blindly returning `run_away()`. Gate #32 `repro_flee_trap_delegate.py` proves it 3 ways (⚠ its
ARM A sentinel was strengthened 2026-08-27 — it had been value-equal to `run_away()`). LIVE ARM
LANDED in BOTH post-fix batches: zero CantEscape freezes corpus-wide (baseline 3 of 8 lanes).
**ARC CLOSED.** 📦 Diagnosis + evidence: `07-CHANGELOG.md` 2026-08-26/27 + git history.

### ✅ `#26-battleitemwedge` — HANG closed 2026-08-26 AND LIVE-VALIDATED 2026-08-27 (batch `20260826-185918`: its KI-47 family 2 → 0 over 572 item flows)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ‼ `#26-gatestartupcontention` — one gate times out IN-SUITE with an EMPTY log, passes solo (filed 2026-08-26)

`repro_gym_whiteout_guard.py` hangs IN-SUITE and passes solo. ⛔ **THE FIRST FILING OF THIS ITEM GOT
THREE DETAILS WRONG, AND A TIER 1 REVIEW CORRECTED ALL THREE WITH A LIVE OBSERVATION** (it caught the
gate mid-hang in a running suite): (1) the freeze is just AFTER phase [1]'s header prints, not
before it; (2) `run_gates.py` is strictly SEQUENTIAL — "~30 parallel gates" was wrong, so
gate-parallelism is not the mechanism; (3) it reproduces on a QUIET machine, so batch load is
refuted too. What stands: in-suite hang (≥3 occurrences: two 900s timeouts + one live-observed),
solo PASS the same hour, audio-host errors (`PaErrorCode -9999, no driver installed`) present at the
freeze point. ⛔ **A 900→2400 bound raise was tried and REVERTED — more time cannot fix a hang.**
➡➡ **DIAGNOSED 2026-08-26 — THE HANG SITE IS CAPTURED; THE PLANNED BISECT IS MOOT.** Stack dump
(`evidence/2026-08-26-gatecontention-stackdump.txt`): **`sounddevice.write` ← `libmgba.py:621
run_single_frame`** — the FPS limiter is a blocking audio write with NO BOUND; a wedged PortAudio
host blocks it forever. Reproduced **SOLO, twice, deterministically, 0 bytes out** (buffered
stdout — "after the header" and "empty log" are the SAME hang); host-state-dependent, batch lanes
immune (`audio=False speed=0` enforced). ⚠ The "sibling passes solo" control was WEAK
(`probe_chapter_order` never drives frames). **FIX CANDIDATES (one drive each): (a) run the gate
stream-free/unthrottled at EMULATOR level like the lanes; (b) bound the write in `libmgba.py`
(production internals — careful).** Narrative: `07-CHANGELOG.md` 2026-08-26.

### ✅ `#24-driftheadlineshape` — DONE 2026-08-26: `check_drift` PASS 3 reads the drift-row HEADLINE (filed 2026-08-24)

- [x] **SHIPPED 2026-08-26 — ⛔ do not rebuild.** `check_drift` PASS 3: the FIRST `N as of <date>`
      in any drift-labelled table row is compared to `real_drift()`; history deeper in the cell is
      exempt **BY POSITION** (the cell's own documented "today's number is at the TOP" convention —
      a declared exemption, not vocabulary). Fault-tested BOTH ways (D28a-e: fires on a wrong
      headline incl. word-form; quiet on right-headline-wrong-history — the inverted incident —
      non-drift rows, and fenced quotes) **plus a live INCIDENT REPLAY**: the real cell's `7`
      flipped to `2` turned the gate red at `04-HANDOFF.md:209` naming both figures, file restored
      byte-identical. Narrative: `07-CHANGELOG.md` 2026-08-26.

### ✅ `#24-ch22juan` — §Ch22, GYM 8 (JUAN): **DONE AND CLOSED 2026-09-03.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (R3 line budget; nothing deleted). ⛔ Nothing here is outstanding — the badge is won, the chapter is assembled and wired as Segment 22, and `#24-ch22chapter` carries the live detail. ⚠ **Drift: run `promote.py --check` (the authority; never restated here)** — `modules/story/victory_road.py` (⚠ **NO LONGER COMMENT-ONLY as of 2026-09-08** — it now also carries the `team_is_ready` EMPTY-BATTLER GUARD, a real behaviour change: an empty battler set used to return `(True, [])` and certify a broken run READY. Gate #48 `probe_empty_battler_guard.py` locks it, fault-tested) and `modules/story/counter_hunt.py` (the `KI-84` workaround, ⚠ **UNDRIVEN** — its A/B is `--driver ki84counter`). SANDBOX-ONLY; ⛔ do NOT promote `counter_hunt.py` before that A/B. *(was 1 as of 2026-09-08 — `modules/story/victory_road.py`, and it is COMMENT-ONLY** (9 insertions, 0 deletions: the note recording that the stepping fix was DRIVEN AND REFUTED, so it is not rebuilt). ⛔ Not a behaviour difference; promoting it is optional and cosmetic. *(was 0 as of 2026-09-08 — ALL FIVE PROMOTED (`KI-96`, `#24-truckleak`, `#24-pcpingpong`, `#24-hm07teach`, `#24-hm07funnel` + the whiteout budget), **PROMOTED 2026-09-08, user-authorised, verified by driving `--build custom` (`ACCEPTANCE: PASS`, `done=True`, `battles=12`, `whiteouts=0`); rollback tag `pre-promote-2026-09-08`**. *(was: drift 5, sandbox-only — ⛔ **the batch that blocked promotion FINISHED 2026-09-08 (`x4-runs/20260907-203713`), so nothing is waiting on it; PROMOTING IS THE USER'S CALL**. *(was: `battle_action_selection.py` for `KI-96`, `mossdeep_gym.py` for `#24-mossdeepstrand`, `counter_plan.py` for `#24-countermsg`, plus `story_mode.py`, the `KI-95` fix, sandbox-only and awaiting the user's promotion call); it was 0 — PROMOTED 2026-09-06.** *(pre-promotion count now lives in `DIVERGENCE-LOG.md`; the file detail is kept:)* (`modules/story/pokemon_league.py` joined 2026-09-04 — the §Ch24 out-of-battle party heal; `modules/story/overworld_items.py` joined 2026-09-04 — the NEW pure out-of-battle healing policy for `#24-e4healing`, gate #36; `modules/modes/util/walking.py` joined on 2026-09-04 — the `#24-waterfalltimeout` fix; 2026-09-03: `chapters.py` for a §Ch23 correctness fix, plus the new sandbox-only chapter modules `sootopolis_gym.py` and `victory_road.py`) — ✅✅ **PROMOTED 2026-09-06 with USER APPROVAL, which took drift to 0** *(it went to 2 on 2026-09-06 — `story_mode.py` for `KI-95` and `battle_action_selection.py` for `KI-93` — and back to **0 on 2026-09-07** when both were PROMOTED and driven-verified)*, driven-verified against `--build custom`; see `custom-pokebot/DIVERGENCE-LOG.md`. *(this read "PROMOTION IS THE USER'S CALL and is not implied", true until that date.)* ‼ The one rule worth carrying out of it: *a pre-step check that REFUSES is worth more than a post-hoc assertion that explains* — the guards caught five faults here, including a `+1`-per-step counter that is really `+2` on a threshold crossing, and a fall direction reversed because y increases SOUTHWARD.

### ✅ `#24-ch23wally` — **CLOSED 2026-09-04: WALLY IS BEATEN.** ✅ Option (b) (the faint-replacement ranking) is **DONE 2026-09-06** — `KI-95`, gate #39, sandbox-only and unpromoted. It had been OBSERVED firing inside the winning run — see the open bullet. (filed, ruled, trained and closed 2026-09-04)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ✅ `#24-waterfalltimeout` — **FIXED 2026-09-04 (sandbox).** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted).
- [x] ⛔ DO NOT REDO. `[0][1]` → `[1][1]`, direction MEASURED before the edit; detail in the archive and `07-CHANGELOG.md` for 2026-09-04.

### ✅ `#24-ch23healdescent` — **CLOSED 2026-09-04: leg 6 now heals before descending, and an A/B proves it (un-healed 32% / 3 fainted vs healed 87% / 0).** (filed and closed 2026-09-04)  📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ DO NOT REDO. Full detail is in the archive under its 2026-09-07 banner and in `07-CHANGELOG.md`.

### ✅ `#24-ch23attrition` — **CLOSED 2026-09-04.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 line budget; nothing deleted, nothing edited).
- [x] ⛔ **DO NOT RE-RUN THE §Ch23 ATTRITION WORK.** The party is back to 807/807 with zero fainted; the fix and its A/B are in the archive under the 2026-09-07 banner and in `07-CHANGELOG.md` for 2026-09-04.

### 🔜 `#24-ch23leg3arms` — **§Ch23 leg 3's OWED FAULT ARMS + the B1F/B2F §F live checks.** (opened 2026-09-05)

⛔ **OPENED BECAUSE A HEADER TRIED TO CLOSE OVER THEM.** These two residuals were stated plainly
inside `#24-ch23victoryroad`'s body and had no slug of their own, so when that header was promoted to
✅ they briefly became invisible — the `#24-orphans` / `#24-codeorphans` shape, which this file has
already paid for twice. A Tier 1 reviewer caught it; the fix is a slug, not a caveat.

**OWED (quoted from `#24-ch23victoryroad`'s own body, unchanged):**
* *"LEG 3's OWED ARMS (still open): `STALERESPAWN`, a real `BADSTEP` (the current one is **hollow** —
  its branch never runs), and a `_play()` run to demonstrate the layout pin (a **NO-OP** in a fresh
  process)."* ✅ `NOHEAL` is already fault-proven by A/B — do not redo that one.
* *"Adjudicated OFFLINE only — the three live checks in the B1F/B2F note §F are still owed."*

‼ **A HOLLOW FAULT ARM IS WORSE THAN A MISSING ONE** — it reports PASS while proving nothing, which
is this project's most expensive documented failure shape. `BADSTEP`'s branch never runs, so its
green result is not evidence. ⇒ when this is worked, FAULT-TEST THE ARM ITSELF: prove it FAILS when
the thing it guards is broken, before trusting any run that includes it.

⚠ Priority: BELOW `#24-ch23chain`. The chain hang blocks the chapter; these harden a leg that already
drives green. ⛔ But do not silently drop them — that is why this slug exists.

---

### ✅ `#24-ch23chain` — **CLOSED 2026-09-05: §Ch23 COMPLETES END TO END.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-07, R3 line budget; nothing deleted, nothing edited).
- [x] ⛔ **DO NOT REBUILD ANY PART OF §Ch23.** `ACCEPTANCE: PASS`, `done=True`. The full item — every leg, fixture, A/B and gotcha — is in the archive under its 2026-09-07 banner, and the shipping detail is in `07-CHANGELOG.md` for 2026-09-04/05.

### ✅ `#24-icebeamtrip` — **CLOSED 2026-09-05: TM13 ICE BEAM IS IN THE BAG.** ⛔ DO NOT REDO THE TRIP. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget).
### ✅ `#24-icebeamteach` — **CLOSED 2026-09-05: WAILORD KNOWS ICE BEAM.** ⛔ DO NOT REOPEN. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-05, to keep 03 under its R3 line budget).
### ✅ `#24-flyunlock` — **CLOSED 2026-09-05: FLY IS TAUGHT AND FLOWN; the Ever Grande plateau is solved.** ⛔ DO NOT REDO. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget).
### ✅ `#24-e4moveset` — **CLOSED 2026-09-05: the four FREE move changes are applied and driven.** ⛔ DO NOT REDO THEM. 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-10, R3 budget).
‼ **ITS LIVE RESIDUAL IS HERE, NOT IN THE ARCHIVE — the block was the only place tracking it:** the free
pickup **Dragon Claw (TM02) for Sceptile** is STILL UN-FETCHED (availability confirmed by
`probe_ch24_readiness.py`), and **Wallace is still a loss**. ⛔ A CLOSED ITEM CAN BE THE SOLE OWNER OF
AN OPEN FACT — sweep for residuals before retiring one.

---

### 🔜 `#24-e4healing` — **§Ch24 HEALING: the bot CAN now revive, cure status and top up out of battle (step 1 DONE 2026-09-04). Steps 2-4 — calling it between rooms, the in-battle question, and the 0.35 threshold — REMAIN.** (opened 2026-09-04)

⛔⛔⛔ **AND IT IS WORSE THAN A RE-BUY — VERIFIED IN CODE 2026-09-06.** The §Ch23 dispatch is:
`story_mode.py:3791` `if not ch23_chapter_done():` → `:3792` runs the chapter, `:3793` else-skips —
and `:3795` `_guard("Victory Road (Ch23)", ch23_chapter_done)` sits **OUTSIDE the if/else**.
`_guard` (`story_mode.py:2917-2878`) **RAISES `BotModeError`** when its check fails. ⇒ the moment
§Ch24 spends the basket, the next pass through `_play()` does all three of these:
(1) re-enters the WHOLE Victory Road chapter, because `:3791` is now True;
(2) reaches leg 11 and tries to re-buy a **₽54,300** basket holding **₽1,741** — leg 11 refuses
loudly, exactly as designed; and
(3) `_guard` raises anyway, because the predicate is still False.
⇒ ⭐ **BOTH HALVES MUST BE RELAXED IN THE SAME COMMIT — a fix aimed only at the `if` leaves the
unconditional `_guard` and turns a wasteful re-buy into a HARD FAILURE.** ‼ Research suggests
short-circuiting on `SYS_GAME_CLEAR` (claimed whiteout-proof, unlike the `DEFEATED_ELITE_4_*` flags
which `ResetEliteFour` clears) — ⚠ **that is AGENT-REPORTED and NOT yet measured here; verify it
before relying on it.**

⛔⛔ **READ THIS BEFORE BUILDING ANY §Ch24 STEP — A HARD DEPENDENCY §Ch23 NOW PLACES ON YOU.** `ch23_chapter_done()` requires the **Elite Four basket in the bag** (it was position-only until 2026-09-05, and a WHITEOUT respawn at Ever Grande satisfied it — the predicate called a WIPED party "chapter complete"; see `06-DECISIONS-LOG.md` 2026-09-05). ⇒ **THE MOMENT §Ch24 SPENDS THE BASKET, `ch23_chapter_done()` FLIPS FALSE and the dispatch will RE-ENTER §Ch23** and re-buy it. ‼ **§Ch24 MUST THEREFORE SET ITS OWN PROGRESS MARKER** (a flag/var its own predicate reads) so Segment 23 is not re-entered mid-gauntlet. ⭐ This line exists here, and not only in the decisions log, because this project has repeatedly lost facts that lived in exactly one place a builder does not open.

**STATUS: OPEN — step 1 of 4 is DONE (the party-heal is built and driven); steps 2-4 remain.**

**MEASURED BY ME against our own code, 2026-09-04 — not an agent's claim.** (A research agent
reported the in-battle cap was "1+ per battle"; the real constant is
`MAX_ITEM_USES_PER_BATTLE = 4` at `modules/story/battle_items.py:46`. The agent's number was wrong,
which is exactly why this was re-read rather than believed.)

**WHAT THE IN-BATTLE POLICY ACTUALLY DOES** (`battle_items.py`, a pure module):
- heals only below **`HEAL_AT_FRACTION = 0.35`** (line 40) — above 35% HP it attacks instead;
- picks the **cheapest SUFFICIENT** item, else the largest (rules 2, lines 94-104);
- **refuses to heal into a losing race** — if the best heal we hold is smaller than the biggest hit
  taken this battle, it attacks instead (rule 3, lines 89-92);
- is **bounded at 4 uses per battle** (line 46), and `on_battle_started` returns a FRESH strategy
  instance per fight, so the bound RESETS each fight ⇒ **up to 20 in-battle heals across the
  gauntlet**, against 33 usable HP items. The bound is not the problem.

⛔ **THE PROBLEM IS THE FILTER AT `battle_items.py:85`** — `if qty > 0 and param > 0`. Checked
against `modules/data/items.json`:

| item | bought | `battle_use` | `parameter` | in-battle usable? |
|---|---|---|---|---|
| Hyper Potion | 30 | healing | 200 | ✅ |
| Full Restore | 3 | healing | 255 | ✅ |
| **Full Heal** | **8** | healing | **0** | ⛔ **NO** |
| **Revive** | **3** | healing | **0** | ⛔ **NO** |
| Antidote | 4 | healing | 0 | ⛔ NO |

⇒ **11 purchased items — ₽9,300 of the ₽54,300 — are invisible to the in-battle policy.** The module
says so on purpose (docstring lines 16-18: *"`Full Heal` is `parameter == 0` — a STATUS cure, not an
HP item, and is excluded here on purpose"*). It is a deliberate, documented scope boundary, **not a
bug** — but it is a boundary the Elite Four sits directly on top of.

⛔⛔ **AND THE SECOND HALF IS WORSE: THERE IS NO OUT-OF-BATTLE PARTY-HEAL AT ALL.**
`modules/modes/util/items.py:43` `use_item_from_bag()` opens the bag, scrolls, presses A and waits
for the start menu — the shape for a **no-target** item like a Repel. A Potion or Revive then asks
*"Use on which POKéMON?"*, and **nothing in the tree answers that prompt.** ‼ Corrected while
writing this: `menuing.py:680/723/728` DO contain the strings "Revive"/"Max Revive", but they are
entries in `get_items_available_for_pickup()` — a list of what the Pickup ability can yield. **That
is not revive logic**, and reading it as such would have been a false reassurance.

⇒ **WHAT THIS MEANS FOR THE GAUNTLET, CONCRETELY:**
1. **HP carries over between all five fights** with no way to top up between rooms.
2. **A fainted Pokémon stays fainted for the entire gauntlet** — attrition is strictly one-way. The
   3 Revives cannot be used by any code path we currently have.
3. **Status is completely unhandled.** Gen-3 freeze does not thaw on its own; Glacia's ice moves and
   a sleep/paralysis from any of the five would simply persist. The 8 Full Heals cannot be used.

⛔⛔ **AND A THIRD THING, READ OFF THE FIXTURE FILE ITSELF (`probe_anchor_inventory.py
post_league_shop.ss1`) RATHER THAN RECALLED — THE PARTY IS NOT WHAT I HAD BEEN WRITING.**
I had been describing it as "L47 across the board". It is actually:

| slot | mon | level | verdict for the gauntlet |
|---|---|---|---|
| 1 | Sceptile | **L53** | real fighter |
| 2 | **Zigzagoon** | **L19** | ⛔ **DEAD WEIGHT** — HM mule |
| 3 | Swellow | **L48** | real fighter |
| 4 | Wailord | **L47** | real fighter |
| 5 | Mightyena | **L48** | real fighter (has Crunch) |
| 6 | **Castform** | **L36** | ⛔ **DEAD WEIGHT** |

⇒ ‼ **THIS IS A FOUR-POKÉMON PARTY, NOT A SIX**, against five trainers fielding ~25 Pokémon at
L46-58. Two slots are carrying an HM mule and a L36 passenger. **That reframes the level-gap question
entirely:** the cheapest intervention may not be grinding the four — it may be *replacing the two
dead slots*, which costs no grinding at all.
⚠ **AND IT ARMS A KNOWN BUG:** `#24-ch23wally` records that the faint-replacement ranking can feed
**Zigzagoon L19** into a fight. In Victory Road that cost a leg; in the Elite Four, where a fainted
mon cannot be revived (see above), sending the L19 in is **a wasted Pokémon we cannot get back.**
⇒ this is now a §Ch24 blocker too, not just a §Ch23 annoyance.

**THE WORK (in order):**
- [x] ✅✅ **1. DONE 2026-09-04 — `heal_party_from_bag()` IS BUILT AND DRIVEN.** ⛔ DO NOT REBUILD IT.
      `modules/story/pokemon_league.py` (the driver) + `modules/story/overworld_items.py` (a PURE
      policy, gate **#36** `repro_overworld_items.py`, fault-tested against **five** broken policies).
      `--driver ch24heal` `ACCEPTANCE: PASS`: from *two fainted, one FROZEN, two badly hurt* → seven
      actions → **147/147 · 48/48 · 139/139 · 226/226 · 144/144 · 103/103**, `heal_ready=True`,
      `whiteouts=0`. `POKEBOT_CH24_FAULT_NOHEAL=1` correctly FAILS.
      ⭐ **THE DISCRIMINATOR IS THE REVIVE ORDER**, and it is asserted live: with Mightyena L48 in
      slot 4 and Zigzagoon L19 in slot 1 both fainted, a slot-order policy revives the HM mule first.
      The run logs `REVIVE ORDER = [(4,'Revive'),(1,'Revive')]` — battle value, not slot order.
      ⭐ And a CONTROL: Castform is deliberately left untouched by the staging, and the run asserts it
      is still untouched afterwards — a heal there would mean the "never a no-op" rule is broken.
      ⛔⛔ **TWO BUGS ONLY THE LIVE DRIVE CAUGHT, BOTH "a field read as if it described itself":**
      (1) `parameter` is a **UNION TYPE** — filtering on `parameter > 0` picked **Repel** (parameter
      100 = *steps*) as a healer; (2) `field_use` is an **ENUM**, so `== "healing"` is always False
      and the allowlist came back EMPTY — **silently**, because the revive/status passes do not use
      it. ⇒ the gate now carries Repel/X Attack/Nugget/Escape Rope as TRAPS (its item universe was
      cleaner than the real bag), and an empty allowlist now RAISES.
- [ ] **2. Call it between rooms**, in the corridor after each Elite Four win, before the next door.
- [ ] **3. Decide whether the in-battle policy should get status/revive awareness**, or whether
      between-room healing is enough. ⭐ Prefer step 2 first — it is the cheaper, more testable half,
      and it may make step 3 unnecessary.
- [ ] **4. Re-check `HEAL_AT_FRACTION = 0.35` for the gauntlet specifically.** 35% against an E4 mon
      may already be inside one-shot range; this is a NUMBER TO MEASURE, not to argue about.

‼ **DO NOT "FIX" THIS BY EDITING `battle_items.py`'s filter.** That module is pure and exhaustively
tested by `repro_battle_items.py`; widening `param > 0` would silently make `effective_heal()` return
0 for a Revive and the policy would pick it as the "cheapest sufficient" heal for everything. The
right place is a NEW out-of-battle path.

---

### 🔶 `#24-ch23victoryroad` — **MIXED. READ EACH BULLET'S OWN MARKER; THIS HEADING DOES NOT CLOSE THE ITEM.**

✅ **DONE, ⛔ DO NOT REBUILD:** §Ch23 Victory Road is TRAVERSED and EXITED, party whole and bag stocked — ELEVEN LEGS BUILT AND DRIVEN, **and the chapter orchestrator + Segment 23 wiring SHIPPED 2026-09-05** (`ch23_chapter_done()` + `do_victory_road_chapter()`, dispatch at `story_mode.py:3779-3795`, `--driver ch23chapter`).
🔜 **STILL OPEN, and tracked so it cannot go invisible:**
* the chapter's CHAIN hangs on `KI-90` ⇒ **`#24-ch23chain`**;
* **`#24-ch23leg3arms`** — leg 3's owed fault arms and the B1F/B2F §F live checks, both stated in this item's own body below (`"LEG 3's OWED ARMS (still open)"`, `"the three live checks … are still owed"`).

⛔⛔ **WHY THIS HEADING IS 🔶 AND NOT ✅ OR 🔜 — BOTH WERE WRONG, IN OPPOSITE DIRECTIONS.** 📦 *(SUPERSEDED WORDING, quoted as history — the phrases below are what this heading FORMERLY said; neither is a live claim.)* It formerly read *"ONLY THE CHAPTER ORCHESTRATOR + SEGMENT 23 WIRING REMAIN"* (an UNDERclaim commanding the rebuild of shipped work, caught by Tier 1), and was then promoted to *"✅ … DO NOT REBUILD ANY OF IT"* (an OVERclaim over a body that still says "still open", caught by Tier 1 the very next round). ⇒ ⭐ **the project's own pair-P2 rule is the answer: a heading is a claim about every bullet beneath it, and when their statuses differ the heading must say MIXED.** ⚠ The party ends at 35% with three fainted — `#24-ch23attrition` — ✅ **CLOSED 2026-09-04** (the party is back to 807/807 with zero fainted; the fix was a 36-step walk to the League's Poké Center, not the ~5 hours of training I had priced). *(This clause read "now ACTIONABLE because the bot can finally leave" until a Tier 1 reviewer quoted it against that item's own CLOSED header — P2: a heading is a claim about everything it points at.)* (filed 2026-09-03, updated 2026-09-04)

> ⛔⛔ **THAT HEADER DROPPED THE UN-DRIVEN EXIT FOR ONE COMMIT — THE FOURTH TIME THIS ITEM'S HEADLINE HAS BEEN CAUGHT CLAIMING MORE THAN ITS OWN BULLETS.** The bullet one line below it listed the arrow warp; the header said "ONLY the wiring remains". `04-HANDOFF.md` had it right in BOTH halves, so this was the punch list alone regressing. ⇒ **when a header enumerates what remains, diff it against the bullet directly beneath it before committing** — and note that gate #35 cannot catch this shape, because no CLOSED slug is being mis-described.

> ⛔⛔ **P5 CAUGHT THIS ITEM FOR THE THIRD TIME (2026-09-04).** Twice before, a CHILD item was closed while this PARENT kept commanding the finished work; this time its header still read *"Leg 6 ships WITHOUT a heal step"* and its bullet still said *"Add the heal before building leg 7"* AFTER `#24-ch23healdescent` closed. ⇒ **closing a child is not updating the parent, and this item is where that keeps failing.** A research note calls this item *"the authoritative live status"*, so a cold agent reading it would rebuild shipped work and start leg 7 from the superseded 32%/3-fainted fixture. **Whoever closes the next §Ch23 child item: grep this slug and re-read this block FIRST.**

> ⛔ **HEADER/BODY PAIR NOTE (2026-09-04).** This header read "LEGS 1-4 SHIP AND PASS; LEGS 5-8 REMAIN" for one commit *after* its own body bullet had been corrected to "legs 6-8" — a Tier 1 reviewer caught it. **P2: a header is a claim about every bullet beneath it**, and updating the body alone is the more dangerous state, because the body looks current.

- [x] **DONE 2026-09-05: the chapter orchestrator + Segment 23 wiring SHIPPED.** `ch23_chapter_done()` + `do_victory_road_chapter()` in `victory_road.py`; dispatch at `story_mode.py:3779-3795`; `--driver ch23chapter`. ⛔ What remains is NOT this — it is the CHAIN, tracked as `#24-ch23chain` — ✅✅✅ `KI-90` is FIXED **and the chain now PASSES** (`ACCEPTANCE: PASS`, `done=True`, `whiteouts=0`, 2026-09-05) — `#24-ch23chain` is CLOSED. *(This read "the chain was re-driven 2026-09-05 and FAILS because the party loses the leg-9 double" — true when written, fixed the same day by the (33,16) bypass plus the leg-11 sell top-up.)*
      ✅✅✅ **LEG 11 SHIPPED 2026-09-04 — THE ELITE FOUR'S HEALING IS STOCKED** (`ch23shop`, PASS,
      fixture `post_league_shop.ss1`): **Hyper Potion 30 · Full Restore 3 · Full Heal 8 · Revive 3**,
      ₽56,041 → ₽1,741. ⛔ **BUT ONLY 33 OF THE 44 ARE USABLE** — see `#24-e4healing` above; the
      bot cannot use Full Heal or Revive at all, so **it is NOT ready to attempt §Ch24.**
      ✅✅✅ **LEG 10 SHIPPED 2026-09-04 — THE PARTY IS WHOLE** (`ch23heal`, PASS, `battles=0`,
      `whiteouts=0`, fixture `post_league_heal.ss1` at EVER_GRANDE_CITY (18,6), **807/807**).
      ✅✅✅ **LEG 9 SHIPPED 2026-09-04 — THE BOT IS OUT OF VICTORY ROAD** (`ch23exit`, PASS,
      `battles=2`, `whiteouts=0`, fixture `post_vr_exit.ss1` at EVER_GRANDE_CITY (18,28)).
      ⛔ **URGENT: 4% HP, FIVE FAINTED** — the League door is 37 wp away and it is the ONLY heal.
      ✅✅✅ **LEG 8 SHIPPED 2026-09-04** (`ch23return`, PASS, `battles=2`, `whiteouts=0`, fixture
      `post_return.ss1` at VICTORY_ROAD_1F (21,32)). ⛔ **It broke a TRAP:** from B1F (17,16) every
      other exit was unreachable, so the bot could not leave Victory Road until it shipped.
      ✅✅ **LEG 7 SHIPPED 2026-09-04** (`ch23cross2`, PASS, `battles=3`, `whiteouts=0`, fixture
      `post_b2f.ss1` at VICTORY_ROAD_B1F (17,16)); its `LADDERAIM` fault arm is proven to FAIL.
      ⭐ The crossing is ONE `navigate_to` — the planner mounts Surf and rides the descent itself.
      ✅ **LEG 6 SHIPPED 2026-09-04** (`ch23descend`, PASS, `battles=4`, `whiteouts=0`, fixture
      `post_b1f.ss1` at VICTORY_ROAD_B2F (30,25)); both its fault arms proven to FAIL.
      ✅✅ **AND THE HEAL SHIPPED TOO (2026-09-04) — `#24-ch23healdescent` is CLOSED.** The A/B:
      un-healed → **32% HP, THREE fainted**; healed → **87%, ZERO**. ⭐ **LEG 7 STARTS FROM
      `post_b1f_healed.ss1`** (`b2eeb15c…`), ⛔ **NOT `post_b1f.ss1`**, which is kept only as that
      A/B's un-healed arm.*
      ⭐⭐ **STUB MARKER — READ BEFORE ANY BOULDER CODE:** `ai-research-notes/2026-09-04-ch23-VICTORY-ROAD-TRAVERSAL.md` (3 independent agents) + `...-ch24-POKEMON-LEAGUE.md`. ⛔ NOTES, not truth — the reachability is MODELED and 3 live checks are OWED. Headlines: (1) **the route is `1F→B1F→B2F→B1F→1F`** — 1F's entrance and exit are in DIFFERENT walk-regions, so "walk across 1F" is impossible; (2) **TWO boulders are mandatory, (4,7) WEST and (9,10) EAST** — a "delete it and re-path" model finds only (9,10) and misses (4,7); (3) ⛔ **pushing either SOUTH kills the route irreversibly** — exactly what a greedy push-toward-goal router does; (4) **every warp RESETS the puzzle** (`FLAG_TEMP_*` cleared, boulders revert — also the recovery from a trap push) and **`FLAG_SYS_USE_STRENGTH` clears on every map load**; (5) minimal HMs = **{Surf, Strength, Rock Smash}** — **Waterfall and Flash NOT required**; (6) ✅ `strength_push` exists (`early_game.py:8011`, Magma-Hideout-proven) ⇒ **the machinery exists; only the route is missing.**
      ⛔ *(This item's header read "PRODUCTION CODE IS ZERO" and its first line "`victory_road.py`
      DOES NOT EXIST" for a day AFTER legs 2-4 shipped from that very file — the heading-vs-body rot
      this tree keeps paying for. Rewritten 2026-09-04.)*

      ✅ **SHIPPED AND DRIVEN — ⛔ DO NOT REBUILD ANY OF IT:**
      * **Leg 1** — `--driver ch23teach`: Waterfall onto Wailmer (lost Rollout, **kept Dive + Surf**).
      * **Legs 2-3** — `victory_road.depart_sootopolis` + `--driver ch23depart` → PASS first drive;
        heal, arm the respawn, dive the crater, emerge on ROUTE126.
      * **Leg 4** — `victory_road.cross_to_ever_grande` + `--driver ch23cross` → PASS first drive;
        Rt126→127→128→Ever Grande, the two forced trainer fights, the waterfall climb, the Ever
        Grande heal, ending on the Victory Road **apron**.

      **FIXTURE CHAIN (all PINNED, each captured only on a FULL PASS):**
      `post_badge8` → `post_waterfall` → `post_depart_sootopolis` (ROUTE126 (45,66), 100%) →
      **`post_ever_grande.ss1`** (`18203e99…`, EVER_GRANDE (18,42), 100%) →
      **`post_training.ss1`** (`2f517f1f…`, VICTORY_ROAD_1F (15,39), 95%) →
      **`post_wally.ss1`** (`76000aa5…`, VICTORY_ROAD_1F (9,15), 67%) →
      **`post_b1f.ss1`** (`d362df89…`, B2F (30,25), 32%, 3 fainted — ⛔ the UN-HEALED A/B arm,
      NOT a start point) → **`post_b1f_healed.ss1`** (`b2eeb15c…`, B2F (30,25), **87%, ZERO
      fainted**) ← **⭐ START LEG 7 HERE.**
      ⛔ **NEITHER EARLIER FIXTURE IS THE START POINT.** `post_ever_grande.ss1` is PRE-TRAINING and
      its party LOSES to Wally (MEASURED, twice); `post_training.ss1` is trained but PRE-WALLY.
      ✅ **WALLY IS BEATEN (2026-09-04)** — `--driver ch23road`, `wally_flag=True`,
      **`whiteouts=0`**, `battles=6` — and `post_wally.ss1` sits on **(9,15) = the B1F ladder
      apron**, i.e. leg 6 starts exactly there. `#24-ch23wally` is **CLOSED**.
      ⛔⛔ **HEAL FIRST — 67% HP with Sceptile AND Zigzagoon FAINTED** (`probe_anchor_inventory`
      marks it "CANNOT SURVIVE A JOURNEY"). Sceptile is now **L52**, not the L51 training left.
      ‼ The grind only worked after **KI-84**; gym prep is still exposed to the same bug.
      ⚠ *(Both claims here were false for one commit — Tier 1 caught it. **P5 twice in the same
      item: closing the CHILD item is not updating the PARENT.**)*

      📄 **ALL ANALYSIS LIVES IN ONE PLACE:** `ai-research-notes/2026-09-03-ch23-CHAPTER-BUILD-SPEC.md`
      — §1 the opening state and the field-move/HP correction, §2 the FOUR harness edits + the `os`
      trap, §2b the measured hop table, §3 the four grading rules, §4b legs 2-3's contract (4
      blockers), **§4c legs 4's contract (3 blockers, 2 settled by a seconds-long waypoint dump)**.
      Companions: `…-VICTORY-ROAD-RECON.md`, `…-VICTORY-ROAD-B1F-B2F.md`, `…-VICTORY-ROAD-1F.md`,
      `…-WATER-ROUTE.md`.

      ⛔⛔ **THE THREE THINGS LEG 5+ MUST NOT MISS:**
      1. **NEVER PUSH B1F's (4,7) OR (9,10) SOUTH** — either seals the floor for that visit. Minimum
         solution: PUSH WEST (4,7)→(3,7) from (5,7); PUSH EAST (9,10)→(10,10) from (8,10); SMASH
         (18,12). ⭐ **Only pushes can kill** (0 of 186,602 walk and 145 smash edges cross live→dead)
         ⇒ the guard is a refusal at the `strength_push` call site, **fail-LOUD**, in the §Ch23
         module — NOT in `strength_push` (§Ch20 shares it). Ruled in `06-DECISIONS-LOG.md`.
         ⚠ **Adjudicated OFFLINE only — the three live checks in the B1F/B2F note §F are still owed.**
      2. **NEVER AIM A PATH AT A TILE AN OBJECT STANDS ON** — a refusal there means "something is
         standing there", not "you cannot get there". And **never aim at a DOOR warp**: aiming leg 4
         at (18,41) would have ended it *inside* Victory Road (MEASURED).
      3. **1F IS THREE REGIONS CUT BY ELEVATION** — from (15,40) you can reach ONLY the B1F ladder;
         from (21,32) ONLY the exit. That is what forces the basement detour, and production's own
         planner confirms it. 1F needs **no field moves** and **cannot be bricked**.

      ⛔⛔ **LEG 3's OWED ARMS (still open):** `STALERESPAWN`, a real `BADSTEP` (the current one is
      **hollow** — its branch never runs), and a `_play()` run to demonstrate the layout pin (a
      **NO-OP** in a fresh process). ✅ `NOHEAL` IS fault-proven by A/B.
      ⚠ **KI-83** bounds every heal/dive call at our call site; **KI-72/73/53/60** are armed on this
      route; **KI-47** can wedge any battle; **`#26-surfteachchain` D3** is OPEN and armed here.

### 🔧 `#24-linebudgetchars` — **THE LINE-COUNT DOC BUDGET REWARDS CRAMMING, AND IT HAS NOW PRODUCED THE ROT IT EXISTS TO PREVENT.** (filed 2026-09-03)

- [ ] **`lint_docs.py` R3 counts LINES and nothing else** (`lint_docs.py:156`, `if lines > budget`).
      There is no character or word check, so the cheapest way to stay under budget is to append to
      an existing line rather than add one. That is exactly what happened: `04-HANDOFF.md`'s §Ch23
      queue head reached **~14,000 characters on ONE line**, and by the time it was read it carried
      **four statements that later text on the SAME line falsified** — *"§Ch23 has none"* (a
      fixture), *"STILL OWED: dump the bag's HMs"*, *"genuinely UNMEASURED"* (Flash), and
      *"B1F/B2F STILL HAVE NO TRAINER OR BOULDER AUDIT"*.
      ‼ **This is the second time in two days the same rot hit the same queue item, and a warning
      about it was already ON the line** — the §Ch22 retirement note, which says in so many words
      that a chronological append-log inside a current-state file rots from the middle.
      ⇒ **The lesson is not "be careful". A gate that measures the wrong quantity does not merely
      fail to help — it actively teaches the workaround that defeats it.** The budget was meant to
      force retirement; it produced an unreadable line instead.
      **Proposed fix (cheap, and it must be FAULT-TESTED before it is trusted):** add an R-rule
      capping any single line in a current-state file at ~2,000 characters, and prove it (a) fires
      on the pre-retirement queue head, and (b) does NOT fire on legitimately long table rows —
      ⚠ `03-PUNCH-LIST.md`'s `#24-remainingarc` row is a single cell of many thousands of
      characters, so a naive rule turns Tier 0 red immediately and the next agent bypasses it.
      ⇒ **scope it to non-table lines first, or grandfather the known offenders explicitly.**
      ⚠ Do NOT raise the line budgets as the fix — that removes the pressure to retire without
      addressing why retirement was avoided.

### ✅✅ `#24-ch22chapter` — §Ch22 IS A CHAPTER: **DONE AND CLOSED 2026-09-03.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (R3 line budget; nothing deleted). ⛔ Nothing outstanding: built, wired as **Segment 22**, driven to `ACCEPTANCE: PASS` (`frames=64563`, `ice_steps=64`, `b1f_steps=19`, `battles_on_B1F=0` with `b1f_entered=True`, `CONTINUE=23`, `RECOVERIES 1`), both fault arms exercised — **and it passed by LOSING the gym fight and recovering.** The chapter ladder is **23 of 24**. ⚠ The two facts §Ch23 inherits: the Juan fight is **stochastic (5 wins, 1 loss over six distinct RNG draws)** so a story run may spend ~35k extra frames there; and ⛔ **KI-47 can freeze the shared battle path inside it** — `#24-ki47rotatelead`, deliberately NOT fixed. ⇒ the live successor is `#24-ch23victoryroad`.

### ‼‼ `#24-ki47rotatelead` — the RotateLead switch can wedge EVERY battle in the game (2026-09-03)

- [ ] ⭐⭐ **MECHANISM PROVEN, REPRO DETERMINISTIC, FIX DELIBERATELY NOT ATTEMPTED YET.**
      `battle_action_selection.py:269-291` drove the in-battle party menu onto **the mon already on
      the field**; the game refused (`gStringVar4 = "SCEPTILE is already in battle!"`, which ends in
      `PAUSE_UNTIL_PRESS` and returns to the chooser) and the branch's last statement is an
      **unbounded** `while get_game_state() == PARTY_MENU: press A; yield` — no counter, no break,
      no raise. ‼ The KI-46 bound cannot fire: `unrecognised` only increments in the
      "no branch matched" paths, so it is frozen at 0 once a branch matched. Only
      `handle_battle._watch`'s 3,000-frame net caught it. Full evidence in **KI-47**.
      ⛔ Repro: `POKEBOT_CH22JUAN_JITTER=181 … --driver ch22chapter` (~22,000 frames).
- [ ] ⛔ **THE NEXT STEP IS AN OBSERVE-ONLY PROBE, NOT A FIX.** Why the cursor sat on slot 0 is
      UNEXPLAINED — three index spaces are conflated here (battle-party id vs menu slot vs live
      `gPlayerParty` index, all MEASURED divergent in the stall state), and a reconstruction of
      `select_rotation_target` predicts slot 4, not 0. **This is the `handle_fainted_pokemon` shape
      a FOURTH time** (KI-18/34/66 + `#24-faintchooser-fourthspace`), and the standing rule is that
      an index conversion has its DIRECTION MEASURED before it is applied. Log `index`,
      `in_battle_index`, `gBattlePartyCurrentOrder`, `gBattlerPartyIndexes` and the live cursor
      immediately BEFORE the A-spam and again after `scroll_to_party_menu_index` — the party order
      is observed to change 35 frames after the decision, so a stale conversion is a live candidate.
- [ ] ⚠ **AND THE STALL SIGNATURE IS BLIND TO MENU CHURN.** `_progress_sig`
      (`battle_handler.py:257-269`) is script instruction + main callback + learn-move state + total
      exp — none of which a party-menu ping-pong changes. ⇒ "KI-47 fired" means *this signature
      stopped moving*, NOT *the game stopped moving*. Worth widening once the above is settled.
- [ ] ⛔ **ANY FIX TOUCHES EVERY BATTLE IN THE GAME**, so it needs an A/B on the ORDINARY case, not
      just on this repro (SESSION DISCIPLINE #9).

### ‼ `#24-pressbuttoncause` — a prevention rule's stated MECHANISM contradicts the code (2026-09-03)

- [ ] ⚠ `08-MISTAKES.md` (2026-09-02, §Ch21 leg 5) says `press_button` on every frame **HOLDS** the
      button, denying `waitbuttonpress` its `JOY_NEW` edge. ✅ But `modules/libmgba.py:476` is
      `self._pressed_inputs |= (self._prev_pressed_inputs & mask) ^ mask` with `_pressed_inputs`
      cleared every frame — **so it AUTO-RELEASES: every-frame calls give a clean edge every two
      frames.** The `frames % 4` fix worked; its recorded CAUSE cannot be right as written.
- [ ] **THE DISCRIMINATOR:** one arm with the duty cycle removed and the `not ...is_active`
      predicate KEPT, on the §Ch21 leg-5 fixture — the two landed together, so neither was isolated.
      ⛔ Until it runs, the fix stands and the cause is marked UNVERIFIED, **not deleted**: a wrong
      recorded cause that is flagged is far safer than a silent one, and a rule pointed at the wrong
      mechanism is what makes the next person apply the wrong remedy.

### ‼ `#24-retiredclaimgate` — a RETRACTED claim survives a literal grep, four times in one round (filed 2026-09-03)

- [ ] **THE MEASUREMENT THAT MOTIVATES IT.** Retracting one claim ("the party cannot win Juan" →
      it won; *believed* 4/4 at the time, later measured 5W/1L) took **four sweeps**: my literal grep (12 hits fixed), then Tier 1 pass 1
      (3 more), then a Tier 1 pass aimed at *where the fixes landed* (4 more — including
      `04-HANDOFF.md`'s own YOU-ARE-HERE banner, the first thing a cold agent reads), then my own
      sweep again (1 more). **Every survivor was a PARAPHRASE**: *"THE LIVE WORK IS NOW §Ch22 (GYM 8
      — JUAN)"* contains none of the search terms and says the same wrong thing.
      ⇒ full narrative + three prevention rules: `08-MISTAKES.md` 2026-09-03.
- [ ] **THE GATE, to be written** (proposed name: an `audit_retired_claims` script alongside the
      other doc gates in `tools/story-dev/` — ⛔ it does NOT exist yet, so this is a SPEC, not a
      citation). A small registry of
      `(retired phrase or regex, retired-on date, the marker that legitimises a quotation)` — and
      the gate fails if a retired phrase appears anywhere in `PROJECT KNOWLEDGE/` or
      `sandbox-pokebot/modules/story/` **outside** an adjacent supersede marker.
      ⛔ **FAULT-TEST IT BOTH WAYS** (the standing rule): prove it FAILS on a re-introduced phrase,
      and prove it does NOT fire on the retraction's own quotation of that phrase — this gate's
      whole failure mode is flagging the sentence that says *"this used to read X"*.
      ‼ Seed the registry from the retractions already in `08-MISTAKES.md`; each one is a phrase
      that has already cost a sweep.
- [ ] ⚠ **SCOPE HONESTLY.** This catches re-introduction and literal survivors. It CANNOT catch a
      paraphrase nobody registered — which is the majority of what the reviewers found. ⇒ it is a
      RATCHET, not a replacement for the independent sweep; say so in its own docstring so the next
      reader does not retire Tier 1 on the strength of a green gate.

### ‼ `#24-crackedfloorpathfinder` — the planner cannot see a hole in the floor (filed 2026-08-24; §Ch21 half RETIRED 2026-09-02, POST-GAME half still OPEN)

- [ ] **WHAT SURVIVES, AND IT IS ONLY THE POST-GAME HALF.** `map_path.py` does not model
      `"Cracked Floor"` at all — decoded in `map.py:391`, then never consulted
      (`grep -n "Cracked" map_path.py` = ZERO hits). The real blocker is the **Rayquaza CAPTURE**
      (post-game), which needs 10 cracked tiles crossed on Sky Pillar 2F at `PLAYER_SPEED_FASTEST`
      = **Mach Bike at `bikeFrameCounter == 2` ONLY**; the Acro Bike returns `PLAYER_SPEED_FASTER`
      and **always falls**. Also gates **Mirage Tower** and **Granite Cave B1F**. The bot is
      BIKELESS (`RECEIVED_BIKE=False`, measured).
      ‼ Whoever fixes it must decide whether a cracked tile is *a hazard to avoid* or *a traversal
      edge with a destination* — for the Sky Pillar it is BOTH, tile by tile. A hazard-avoiding
      planner would report the summit UNREACHABLE, which reads as "our pathfinder is broken", and
      this project has burned days on exactly that shape.

⛔⛔ **THE ENTIRE §Ch21 HALF OF THIS ITEM IS RETIRED — IT IS RESOLVED, AND IT WAS DANGEROUS.**
Its headline claim ("no crack-free route exists on 2F/4F") was **REFUTED 2026-09-01**: it measured
the DEFAULT/post-game crack set, while the story runs on the `*_Clean` layouts where 33 of 38 (2F)
and 29 of 34 (4F) are SOLID GROUND. Every leg had a crack-free story route, and banning 4F's five
real cracks cost nothing (29 wp either way, measured). `SKY_PILLAR_TOP` was validated the same day.
**And all of it has since SHIPPED: legs 3, 4 and 5 are built and driven, and §Ch21 IS A CHAPTER as
of 2026-09-02** (`--driver ch21chapter`, PASS, `frames=95823`) — including the deliberate falls the
planner cannot propose, and the ROUTE131 live-pin the swim turned out to be impossible without.
Full narrative: `07-CHANGELOG.md` 2026-09-01 and 2026-09-02.
‼ **WHY IT IS RETIRED RATHER THAN LEFT TO ACCRETE:** a Tier 2 cold-start audit found this item
**commanding the opposite of the live first action**, under four layers of inline SUPERSEDED /
REFUTED markers stacked on one another — a reader who stopped at any one of them got a different
answer. ⇒ *when an item's claim is refuted AND its work has shipped, COMPRESS it to what survives;
stacking another correction on top is how it became unreadable.*
### ✅ `#24-ch21anchor` — DONE 2026-08-24 (RETIRED to a summary; full detail in `07-CHANGELOG.md`)

⛔ **`saves/post_ch20.ss1` EXISTS — DO NOT RE-CAPTURE IT.** Captured by `--driver ch20chapter`
with `CH20_CAPTURE=`, which writes ONLY on `ACCEPTANCE: PASS`, so the file's existence IS the
acceptance record. Probe-verified `OVERWORLD ROUTE128 (38,24)`, badges 1-7, `ROUTE128_STATE=2`,
`SOOTOPOLIS_CITY_STATE=1` — §Ch21's entry condition, measured live.
⚠ It carries **1 FAINTED party member at 80% HP** — faithful, but a §Ch21 leg started from it
can whiteout; heal first and do NOT read an early whiteout as a Ch21 bug.
‼ The lesson that outlived the item: **verify an anchor with `probe_anchor_inventory.py`, never
from the driver's log** — the probe caught the fainted member the driver's log did not report.

### ‼ `#24-divegroundroute120` — a MEASURABLY better Dive-learner ground nobody had evaluated (filed 2026-08-24)

- [ ] **Route 120 Marill beats Route 117 Marill on every axis, and the 2026-08-13 plan never
      enumerated it** — it framed the choice as Route 117 vs Shoal Cave only.
      | | Route 117 (wired today) | **Route 120 (proposed)** |
      |---|---|---|
      | slot rate | Marill 10% | **Marill 15%** |
      | levels | L13 | **L25-27** |
      | trip from Mossdeep | **1,055** waypoints | **379** out / 395 back |
      ⇒ 2.8× shorter, ~13 levels more useful, outdoors (no tide, no KI-73, no cave-warp threading).
      ✅ **AND IT IS INERT FOR TRAINING — MEASURED:** adding it to `TRAINING_GRASS` **with**
      `AREA_PREREQ[ROUTE120] = "surf"` changes **0 of 66** levels L5-70. ⛔ That prereq entry is
      LOAD-BEARING, not cosmetic: WITHOUT it, 47 of 66 levels change.
      ⚠ **NEEDS ONE LIVE SWEEP BEFORE ADOPTION** — this project demotes statically-derived grounds
      (the Route 114 lesson), and all 436 of Route 120's encounter tiles are **Long Grass** while
      every ground swept to date is plain **Tall Grass**. ⛔ Whether `spin()` behaves on Long Grass
      is NOT DETERMINED; the sweep must assert it.
      ‼ Prefer a SEPARATE HM-ground table over appending to `TRAINING_GRASS` — `_hm_hunting_grounds`
      has exactly one production caller, so the blast radius is provably nil, and
      `06-DECISIONS-LOG.md` already names that shape. ⛔ Do NOT reuse `HUNTING_GROUNDS`; that dict
      feeds the counter planner and would widen a second consumer.
      ⛔ **DO NOT RE-PROPOSE SHOAL CAVE.** Ruled out 2026-08-13 (user-delegated): at HIGH TIDE its
      reachable on-foot encounter tiles are **0**, so the hunt silently burns its whole budget.
- [ ] ⛔⛔ **2026-09-10 — THIS ITEM IS *NOT* A FIX FOR THE §Ch23 REFUSAL, AND THAT WAS TESTED BEFORE
      IT WAS PROPOSED.** `Marill` is the named offender in 11 of 23 refusal events and is the Dive
      carrier acquired at ROUTE117 **L13**, so re-prioritising this from "quality" to "capability"
      looked obvious. **[MEASURED — `tools/story-dev/probe_dive_carrier_level.py`]** it is not:
      L13 → **406,972** frames · L25 → **352,518** · L27 → **336,755**, against a **250,000** ceiling.
      ⇒ **every reachable acquisition level REFUSES**, so this stays a QUALITY upgrade and the
      2026-08-13 ruling is **VINDICATED**, not undermined.
      ⭐ The validation also found the carrier is **inert in the exp-bearing batch** (521/521 at
      `L13:exp1757`) — ⚠ but see `#24-lowlevelmules`: corpus-wide it DOES level (1,492 readings
      above L13), so "never gains" was a one-batch scope error of mine plus observation censoring.
      **Full record: `07-CHANGELOG.md`, "A better Dive ground would NOT clear the gate".**

### ‼ `#24-hmgroundwatertiles` — two HM hunting grounds are WATER tiles priced off the LAND table (filed 2026-08-24)

- [ ] **A silent 40,000-frame stall, tried FIRST.** `ROUTE118 (29,15)` and `ROUTE119 (21,109)` are
      **Ocean Water, elevation 1**, where only the SURF table fires — but `_hm_hunting_grounds`
      reads `enc.land_encounters` only, so it promises Linoone/Zigzagoon while the tile can only
      produce Tentacool/Wingull/Pelipper. They are the LAST two entries and `ensure_hm_learner`
      tries `reversed(grounds)`, so they are the **first** thing a post-Norman **HM03 Surf** hunt
      attempts — spinning its full budget meeting nothing that can learn Surf, then reading as bad
      luck. Same shape as the failure the Shoal ruling refused.
      ⚠ **STATIC ROM READING, NOT A DRIVEN OBSERVATION.** Confirm cheaply first: spin on
      `ROUTE118 (29,15)` and log the species actually encountered.
      ‼ Related: `ROUTE115/118/119`'s recorded training BANDS are land bands on water tiles, so
      `best_training_area` mis-describes those grounds too.

### ‼ `#24-gatescopeharness` — the undefined-name gate is blind to `tools/story-dev/` (filed 2026-08-24)

- [ ] ⛔ **RE-SCOPED 2026-08-24 — THE ORIGINAL FILING RESTED ON A FALSE PREMISE.** It claimed
      `repro_undefined_names.py` was "structurally blind" to `story_harness.py`. It is NOT: that file
      has been in `EXTRA_FILES` since 2026-08-12, added for the very same missing-`os` bug. The two
      `NameError`s that killed a 25-minute drive were caught by nothing because **the gate was not
      RUN before the drive**, not because it could not see the file.
      ⇒ **What IS genuinely uncovered: the REST of `tools/story-dev/*.py`** — ~100 probe/repro
      scripts outside `EXTRA_FILES`. Widening to them is still worth doing.
      ⚠ **NOT a blind switch-on**: those scripts have never been linted, so the baseline is unknown —
      give it its own RATCHET the way `probe_abort_swallowing` has one, rather than demanding zero.
      ‼ And the cheaper half needs no code at all: **run the gate suite BEFORE a long drive**, not
      only before a commit.

### 🔧 `#24-advisorydocstring` — **`advise_on_diff.py` FIRES ON HAZARDS DESCRIBED IN DOCSTRINGS, SO DOCUMENTING A TRAP ACCUSES YOU OF HAVING IT.** (filed 2026-09-03, MEASURED)

- [ ] **R-LOOP false-fired on `victory_road.py` for a `while True:` THAT DOES NOT EXIST** — the only
      occurrence is `:149`, inside the **module docstring**, describing KI-83. AST-verified: the file
      has **six `For` loops and ZERO `While` loops.** **Cause:** the tool strips `#` comments, but a
      **docstring is a string expression, not a comment**, so documented hazard names reach the
      matcher as code.
      ⛔⛔ **THE PERVERSE INCENTIVE IS THE POINT: the more carefully you DOCUMENT a hazard, the more
      the tool accuses you of COMMITTING it** — and this project asks every module to explain its
      traps in its docstring, so the two rules fight. ‼ *A gate with false positives teaches the
      reader to bypass it* — advisory-only makes that cheaper, not harmless.
      **Fix, FAULT-TESTED BOTH WAYS:** blank every `ast.Expr` string before matching. ⭐ The two arms
      are the point: (a) a real `while True:` still FIRES; (b) the same text in a docstring is
      SILENT. Without (a) the "fix" could just disable the rule.
      ⚠ Likely affects the other text-matching rules too — check them in the same pass.
      ✅ The rest of that advisory run was correct: R-EXCEPT prompted a real check, and
      `probe_abort_swallowing.py` reports **23 sites, exactly at baseline** — zero new debt.

### ✅ `#24-difftriggeredrules` — **DONE 2026-08-26, CLOSED.** 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (R3 budget; nothing deleted). ⛔ DO NOT REBUILD. `tools/story-dev/advise_on_diff.py` — 9 diff-keyed rule families, ADVISORY and never blocking (exit 0 either way), delivered by `.claude/hooks/advise-on-commit.ps1` as `additionalContext` only; ⛔ deliberately NO `permissionDecision`, because an "allow" would auto-approve the commit past the user's own prompt. Proof: a 32-check `--self-test` (every rule both ways) plus a mutation test. ⭐ **IT IS LIVE AND EARNING ITS KEEP:** on 2026-09-03 its **R-SCANBOUND** rule caught a coordinate scan in a new probe bounded by the WRONG shaft's floor — the output had been right only by luck. ‼ Adding a rule = one table entry + its two self-test arms (T25 enforces the pairing).

### ‼ `#24-sanitycheck2` — the deep sanity check is 2 passes of 5 (filed 2026-08-27)

- [ ] **PASSES 1-2 RAN (20 fault-injecting agents) and paid for themselves** — 5 gate defects fixed,
      13 stale-prose contradictions corrected (`07-CHANGELOG.md` 2026-08-27). ⛔ **PASSES 3-5 DID
      NOT RUN** (account limit twice; the user ruled the 40-agent fan-out too expensive — do NOT
      re-run it that way). **What is therefore UNAUDITED since 2026-08-22:** (3) story-code
      re-verification (loop bounds + `_check_abort` placement since `dce95b4a`, A-press gating,
      PID-identity, era-keyed Expect rot); (4) infrastructure (runner controls, fixture-coverage
      delta, evidence orphans, shared-state growth, the contention gate's live status); (5)
      cold-start startability. ⇒ **DO IT CHEAPLY — greppable/AST checks INLINE, or 2-3 agents per
      pass; ⛔ never a 40-agent fan-out.** Angle list: the workflow script `deep-sanity-5x8-*.js`.
### ‼ `#24-reprosweepratchet` — WHAT THE STANDING SUITE DOES NOT RUN, ROTS (filed 2026-08-23)

- [ ] **⛔ MEASURED, not theorised: the SAME script was written off as "environmental" TWICE.**
      `#24-brokenrepros` fixed six `repro_*.py` scripts. **None of the 104 repros is in
      `run_gates.py`** — the suite covers 28 enforcing gates, and the rest are run only when somebody
      remembers to. Consequences already paid, twice on one script:
      * 2026-07-30 — `repro_double_faint`'s stub lost `level` when the KI-18 tiebreaker landed; its
        own comment records it was *"recorded as environmental, needs a real mgba, for days. It needs
        no emulator at all."*
      * 2026-08-23 — the SAME script, the SAME misfiling, a different missing stub attribute
        (`is_double_battle_with_partner`). It was not in the item's own table of five, and only a
        full 150s sweep of all 104 surfaced it.
      ⇒ **A doc line saying "environmental" is a CLAIM, and it is self-sealing: it tells the next
      reader not to run the thing that would refute it.**
      ‼ **DESIGN (do NOT just bolt 104 scripts onto `run_gates.py` — the suite is 158s and must stay
      fast enough to run every commit):** a `repro_sweep_ratchet.py` that runs every `repro_*.py`
      with the 150s cap and asserts the set of failing scripts is a SUBSET of a documented allowlist,
      each entry carrying a REASON. Ratchet semantics, like every other gate here: the set may shrink
      freely, may never grow. ⛔ Run it as an ADVISORY/slow tier or on a schedule, NOT in the hot
      suite; and ⛔ `repro_x4_lanes` must stay excluded — it spawns real lane processes.
      ⚠ **Fault-test both directions:** break a passing repro (must fire); add a listed one (must
      stay silent); and prove the allowlist cannot silently absorb a NEW failure.

### ‼ `#24-codeorphans` — SIX SLUGS THAT CODE CITES AND THIS FILE NEVER DEFINED (filed 2026-08-22, PASS 5)

- [ ] **⛔ THE `#24-orphans` SHAPE AGAIN, and this time the dangling pointers are IN THE CODE.**
      Measured: each slug below has **0 mentions in this file** and is referenced from a script or
      a KI. `repro_fortree_gate_solver.py:1` literally opens *"ACCEPTANCE CHECK for punch-list
      #24-fortreegates"* — a gate declaring itself the acceptance check for an item that does not
      exist. ⇒ **These are STUBS to make the pointers resolve, not a claim about their status;**
      each needs triage against the code before anyone works it (this file's own history has THREE
      items marked "ready to build" that had already shipped).
      | slug | cited from | what the citation says it is |
      |---|---|---|
      | `#24-fortreegates` | `repro_fortree_gate_solver.py:1` | Fortree Gym rotating-gate solver; the script is its acceptance check |
      | `#24-harness-finish` | `story_harness.py:10181`, `compare_runs.py:158` | distinguish a run that FINISHED from one that HUNG — a live grading question |
      | `#24-boxmessage` | `story_harness.py:1653` | capability test: does a FULL-PARTY catch complete and exit cleanly |
      | `#24-endlessruns-gui` | `endless_runs.py:9` | lands in the currently UNPROMOTED GUI bundle |
      | `#24-bosstelemetry` | `probe_boss_healing.py:16,118` + 3 KI cites | per-turn opponent logging; `probe_boss_healing` reads what it writes |
      | `#24-areaitemgate` | `05-KNOWN-ISSUES.md:1302` | touches the heal/item path alongside `#24-pc` |
      ⚠ **SEPARATE, related defect:** five more slugs exist ONLY as rows of the (now re-titled)
      MIXED index at the top of this file and have no `- [ ]` item anywhere — `#24-pathsourcecheck`,
      `#24-npcgifts`, `#24-grounditems`, `#24-remainingarc`, `#24-shoalcave`. ‼ **`#24-pathsourcecheck`
      was RE-DERIVED AS REAL AND OPEN:** `map_path.py:968` still passes only the
      NEIGHBOUR tile to the accessibility predicate and never the SOURCE tile (the predicate is
      `is_tile_accessible`, `map_path.py:829`), and KI-60 is still open in `05-KNOWN-ISSUES.md`.

- [ ] `#24-fixturecoverage` — **NEW 2026-08-22 (deep sanity check PASS 4). ‼ REFERENCED FROM CODE
      (`verify_fixtures.py`) — this item may not be deleted without editing that file.**
      **`verify_fixtures.py` walks the MANIFEST, never the DIRECTORY**, so a save with no
      `saves/FIXTURES.md5` row is not merely unprotected, it is INVISIBLE. **MEASURED: 11 rows
      against 77 `.ss1` on disk ⇒ 66 fixtures neither PINNED nor declared VOLATILE.** Among them
      **`at_steven_2f.ss1`** (the KI-66 driver's anchor) and **`ch13_fortree_door.ss1`** (KI-80's
      condition table) — both cited in the docs as things evidence rests on.
      ✅ The gate now PRINTS the gap at every run (advisory, 2026-08-22). ⛔ It deliberately does NOT
      fail: 66 red files would block every commit, and a gate that cries wolf is worse than none.
      **THE WORK:** decide PINNED vs VOLATILE per file and add rows. ⚠ **Pin nothing you have not
      first measured as stable** — pinning a save a driver rewrites turns the suite permanently red,
      and `verify_fixtures.py`'s own docstring records that "copy the file now" is NOT pinning.
      ⚠ 1 of the 77 (`midstuck.ss1`) is deliberately gitignored — a demoted shared scratch path, not
      a hole. Do not "fix" it.

- [ ] `#24-gateselftests` — **NEW 2026-08-22 (PASS 4). Make PASS 4's fault-injections PERMANENT.**
      **MEASURED, and worse than the lead said: 21 of 28 suite gates had NO `--self-test`** (⚠ re-derive: the suite is **29** now and 7 carry one, so **22** lack it — `selftest_git_add_hook.py` is the 29th and is the precedent to copy) (the
      earlier note said "9 of 11 sampled"). ‼ **"No self-test" is NOT "cannot fail"** — pass 4's
      agents demonstrated by injection that most of the 21 DO fail correctly (all four static
      scanners, all four behavioural repros, lint R1-R6, preflight's four sections,
      `verify_fixtures`, `audit_flag_names`, `repro_party_accounting`, `repro_impassable_dirs`).
      ⛔ **But those demonstrations lived in ephemeral scratch and are now GONE.** That is the whole
      item: a gate proven to fail once, with no standing proof, decays to a gate nobody can trust.
      ⇒ Port the injections into `--self-test` blocks, cheapest first. Precedent to copy exactly:
      `selftest_git_add_hook.py` (2026-08-22) and `repro_whiteout_abort.py --self-test`.

- [ ] `#24-testrunsweep` — **NEW 2026-08-22 (PASS 4). 98 more `LibmgbaEmulator(...)` sites still
      lack `is_test_run=True`.** Without it the emulator registers an atexit that OVERWRITES shared
      `profiles/<name>/current_state.ss1` and drops a `states/` snapshot — so an "observe-only"
      probe mutates state the next run reads. **MEASURED: `profiles/repro-ml/states/` had reached
      2,820 files / 160 MB.** ‼ **RE-DERIVE BOTH, do not trust these digits** (a Tier 1 reviewer
      correctly flagged them as bare numbers): sites =
      `grep -rn "LibmgbaEmulator(" tools/story-dev/*.py | wc -l` minus `... | grep -c is_test_run`
      (⛔ the `grep -c ... | grep -v` form I first wrote here is BROKEN — it emits per-file counts, so
      the filter matches nothing; caught by a PASS 5 agent running it verbatim); accumulation =
      `ls sandbox-pokebot/profiles/repro-ml/states/ | wc -l` and `du -sh` on the same path. Both
      GROW with every run on every machine, so they are readings, not properties. ✅ Pass 2 fixed 2 (the KI-76 probes); **PASS 4 fixed the 7 that are in
      the STANDING SUITE** and PROVED it (states count and `current_state.ss1` mtime byte-identical
      across four probe runs). ⛔ **The remaining 98 were deliberately NOT swept**: `is_test_run`
      also suppresses LOADING `current_state.ss1` (`libmgba.py:144`), so it is a BEHAVIOUR change,
      and a blind mass-edit of 98 files could silently change what a probe boots from.
      ⚠ `story_harness.py:122` is the real driver and probably SHOULD keep profile state — decide it
      explicitly rather than sweeping it. ⇒ Do them in batches, running each after.

- [~] `#24-p4residuals` — **SIX OF SEVEN DONE 2026-08-23; only (f) remains.**
      ✅ **(a) `--strict`, (b) fence-blanking, (c) `splitlines()`, (d) the DENYLIST, (e) `--build`
      on three gates, (g) proximity-scoped supersede — all shipped, each fault-tested BOTH ways.**
      ⛔⛔ **TWO OF THEM PROVE THE ITEM'S OWN PROPOSED FIX WAS WRONG, and both were refuted by
      MEASUREMENT before any code changed:** (d)'s relevance-keyword allowlist would have newly
      failed **43 genuine handlers** (all 60 comment justifications are real; this codebase justifies
      in DOMAIN PROSE, not keywords) and broken the ratchet on all four roots; (g)'s span-port
      inverts the corpus's direction (the drift check needs the marker BEFORE the claim; gate-count
      retractions here come AFTER the figure) — 1 false positive over 143 commits. See
      `06-DECISIONS-LOG.md` and `07-CHANGELOG.md`, both 2026-08-23.
      ⚠ **NO PRODUCTION CODE WAS TOUCHED — drift is unchanged at 1.**
      *(This header said "Six" while listing seven, then "SEVEN" — both caught by audits the same day.)*
      ✅ **(a) DONE 2026-08-23 — `--strict` added, proven on all four arms (drift 1 → check 0 /
      strict 1; forced drift 0 → both 0).** Original: `promote.py --check` — the drift "authority" — **ALWAYS exits 0**
      (`promote.py:117-120` returns 0 before any refusal), so it cannot be chained or gated.
      VERIFIED FROM SOURCE, not from a passing run. ⇒ add `--strict`; ⛔ do NOT make plain `--check`
      exit 1 on drift — drift is a normal state, not an error.
      ✅ **(b) DONE 2026-08-23 — fences are blanked before R1/R2 scan, LINE COUNT PRESERVED so R3
      and `--show` are unaffected; fault-tested 5 ways.** Original: lint R1/R2 fire on `# HISTORY` and banner text INSIDE fenced code blocks (latent
      today). ⇒ strip ``` fences before scanning.
      ✅ **(c) DONE 2026-08-23 — `len(text.splitlines())`; all five files drop by exactly 1, none
      changes pass/fail, boundary still discriminates (900 quiet / 901 RED).** Original: lint R3 counts `text.count("
")+1`, one MORE than `wc -l` for any file ending in a trailing newline.
      ⛔ **NO EXAMPLE FIGURE IS QUOTED HERE — the first draft cited two line counts and both were
      stale within a day.** Re-derive: `wc -l <file>` beside `lint_docs.py`'s budget table.
      Harmless DIRECTION (it over-counts, so the effective limit is one stricter) but the budget
      is off by one. ⇒ `len(text.splitlines())`.
      ✅ **(d) DONE 2026-08-23 — a DENYLIST, not the proposed allowlist (see the header). Gate still
      reports exactly 148, per-root 133/4/3/8 unchanged; new `--self-test`, 10 reject + 8 keep
      cases, fault-tested three ways.** Original: `repro_no_silent_except.py:107` justifies a silent handler on comment LENGTH
      (`>= 12` chars), not relevance — any filler comment launders it.
      ✅ **(e) DONE 2026-08-23 — `--build sandbox|custom` on all three, PROVEN not a no-op (153
      offender paths under the selected fork, 0 under the other); two now REFUSE loudly instead
      of tracebacking on a missing fork.** Original: `repro_undefined_names.py`, `repro_no_silent_except.py`, `repro_roster_reorder.py`
      hardcode `sandbox-pokebot` with no `--build` (only `repro_pid_identity_key.py` has one) ⇒ a
      defect landing in the PROMOTED fork is invisible to all three.
      ⛔ **(f) IS THE ONLY ONE LEFT — and it is deferred DELIBERATELY.** That gate is 573 lines,
      boots a ROM and orchestrates its arms as SUBPROCESSES, so ARM C is a real emulator drive
      with its own verification, not a quick addition. ‼ A gate change that cannot be proven in
      the same sitting should not ship in that sitting. Evidence intact below.
      **(f)** `repro_ki65_unbound_party_index.py` tests only the UNBOUND read; the documented KI-65
      residual (a legitimately-bound `party_index = -1`, i.e. the LAST party member) is untested and
      REPRODUCES THE LIE when injected (`lie_msg=1`, Loudred consulted instead of Marshtomp).
      ⇒ add ARM C.
      ✅ **(g) DONE 2026-08-23 — unit scope KEPT, direction-agnostic PROXIMITY of 120 chars added.
      Measured over 143 historical commits: 4 TRUE-STALE, 0 FALSE POSITIVES, 0 findings lost, 0 on
      the live tree; the reinjected `28 gates` defect is now CAUGHT.** Original: `audit_doc_consistency`'s supersede exemption is NEIGHBOURHOOD-BOUND, not
      CLAIM-BOUND — the SAME bug shape already fixed in `check_promotion_prose` on 2026-08-17.**
      ⚠ **ITS EXAMPLE IS NOW UNREPRODUCIBLE — a starter must build a fresh one** (the stale line was
      fixed the same day). The GATE DEFECT is still real: `audit_doc_consistency.py:513` still scopes
      the exemption to the whole unit. As it was MEASURED: `04-HANDOFF.md:51` carried a stale GATE-COUNT claim (a suite size two behind
      reality) six lines above a correct one, and the gate stayed SILENT. ⛔ The stale sentence is
      DESCRIBED here, not reproduced — quoting it verbatim re-created a live-looking false claim
      that `audit_doc_consistency` then flagged, correctly, in this very file — because the claim falls inside a **3,975-character unit**
      that contains the words *"older framing"* somewhere, and one supersede marker exempts the
      WHOLE unit, live orientation instructions included. A **Tier 1 human-shaped reviewer** caught
      it; the gate structurally could not. ⇒ scope the exemption to the SENTENCE/clause, as
      `check_promotion_prose` now does. ⛔ **MEASURE THE BLAST RADIUS FIRST** — narrowing it will
      un-exempt every number in every large annotated block, and a flood of false positives is worse
      than the miss. *(A seventh phrasing was added to the claim regex the same day; it is correct
      and matches this line in isolation — it simply never gets consulted here.)*

- [ ] `#24-flagnamedocscan` — **NEW 2026-08-22 (PASS 4). ⛔ THE OBVIOUS FIX IS REFUTED BY
      MEASUREMENT — do not build it.** `audit_flag_names.py` scans only story `*.py`; docs are never
      checked, and CLAUDE.md names docs as exactly where hallucinated flag names land.
      **But gating doc flag names WOULD BE NOISE** — and ⚠ **TWO INDEPENDENT MEASUREMENTS OF THIS
      POPULATION DISAGREE** (293 unresolvable / 438 mentions / 49 files vs a later 281 / 500 / 59),
      because the population is REGEX-DEFINED and therefore definition-sensitive. ⛔ **Do not pick a
      side — re-derive with your own scan and state your regex.** Both agree on the SHAPE, which is
      what decides the ruling: the overwhelming majority of hits are in `ai-research-notes/` — explicitly "RECALL ONLY, never
      authoritative", where unverified names are the POINT — and of the **15 in 7 authoritative
      docs**, most are prose PLACEHOLDERS (`FLAG_NAME`, `FLAG_BADGE`, `VAR_TEMP`,
      `FLAG_MOSSDEEP_GYM_SWITCH_X`). A gate firing on those trains the reader to bypass it.
      ‼ **ALSO MEASURED AND NON-OBVIOUS:** the ground truth (`modules/data/event_flags/emerald.txt`)
      stores **BARE** names (`BADGE07_GET`), while docs use the **decomp** prefix
      (`FLAG_BADGE07_GET`) — a naive comparison reports 100% failure. *(My first probe did exactly
      that and I nearly filed 652 phantom findings; the CHECK was wrong, not the docs.)*
      ⇒ **THE REAL WORK IS SMALL:** adjudicate the ~8 non-placeholder names against the decomp via
      `gh api repos/pret/pokeemerald/contents/...` — `FLAG_RECEIVED_HM03`,
      `FLAG_DEFEATED_RIVAL_ROUTE119`, `FLAG_RECEIVED_ITEMFINDER`,
      `FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1`, `FLAG_RECEIVED_MAGMA_EMBLEM`, `FLAG_DEFEATED_CHAMPION`,
      `FLAG_RECEIVED_TM27`, `FLAG_GET_CAUGHT`. Fix any that are wrong; gate nothing.

- [ ] `#24-driftreduction` — **NEW 2026-08-17, split out of `#24-driftassertions` (which shipped the
      GATE half). Assert the drift number in ONE place; every other site points at the command.**
      Keep the STATE table row (it is where a cold start looks) and the HOW TO RUN `Expect:` line
      (it is a grading claim); everywhere else should say *"run `promote.py --check`"* with no digit.
      ✅ **THE MEASUREMENT THAT SIZES THIS JOB ALREADY EXISTS:** the corpus carries **67** windows
      mentioning a drift figure across the 7 current-state docs, classified as ~16 claims about now,
      ~24 historical measurements, ~29 prose-about-the-problem. **Only the claims-about-now are in
      scope** — ⛔ do NOT strip the historical ones, they are the evidence trail, and the gate is
      built to leave them alone.
      ⚠ **DO THIS AT A QUIET MOMENT, NOT MID-ARC:** it touches the same lines every in-flight change
      touches, and a merge conflict here is a stale drift figure by another route.
      ‼ **AND IT IS NOW MUCH LESS URGENT THAN WHEN IT WAS FILED** — the gate half closed the failure
      mode this was meant to prevent (a stale figure surviving a hand sweep). Treat it as tidying,
      and re-run `audit_doc_consistency.py --self-test` after, because deleting figures changes the
      very corpus the false-positive controls were tuned against.

- [x] `#24-abortswallow` — **KI-81. ✅ CLOSED AND GATED. ⛔ DO NOT REOPEN, AND DO NOT "FIX" A LISTED
      SITE.** `StoryAbort` is a `BotModeError` is an `Exception`, so every broad `except` in the
      story path can catch a whiteout. KI-67 fixed only the two chapters it had OBSERVED failing;
      this item swept the CLASS. Three rounds of fixes shipped and were PROMOTED TO BOTH FORKS
      (user-approved), each proven by a MEASURED before/after rather than a byte-compare.
      ✅ **`probe_abort_swallowing.py` IS GATE #27, A RATCHET — MEASURED 2026-09-02: 23 sites in
      BOTH forks, exactly at baseline, PASS.** ⛔ **A "CANDIDATE" IS NOT A DEFECT** — the probe says
      so itself, and ~64% were MEASURED (2026-08-17) not to be this defect. ⇒ **the number must
      never GROW; do NOT drive it to zero, and do NOT fix a site because it is listed.**
      *(This item's headline read "⛔ 36 CANDIDATES REMAIN" until 2026-09-02. It was STALE — the
      baseline is 23 — and it looked like it contradicted `04-HANDOFF.md`'s "AST finds ZERO". It
      does not: those count DIFFERENT THINGS (zero unguarded defects vs 23 candidate sites). The
      contradiction was settled by RUNNING THE PROBE before this item was compressed, because
      silently resolving a contradiction you do not understand is how detail gets lost.)*
      ‼ **THE ONE ENGINEERING RULE WORTH CARRYING FORWARD lives in the CODE, not here** —
      `higher_level_actions.py:842`: a handler that catches `Exception` must re-raise **only
      BotModeError-family** objects, because `PathFindingError` is a `RuntimeError` and a re-raised
      one would escape `StoryMode.run`'s `except BotModeError` (`story_mode.py:2536`) and leave the
      global abort latch STUCK TRUE for every later mode.
      ⚠ **KNOWN STALE CITATION, DELIBERATELY NOT FIXED:** that code comment still says
      `story_mode.py:2505`, which is a bare `pass`; the handler is at **:2536** (verified
      2026-09-02). ⛔ Fixing it in sandbox alone takes DRIFT 8 → 9 and creates a promotion
      decision for the USER over a comment typo — a bad trade, and `audit_doc_consistency.py`
      caught the drift the moment I tried it. ⇒ **bundle this one-word fix into the NEXT
      approved promotion round of `higher_level_actions.py`**; the correct line number is
      recorded HERE in the meantime, so nothing is lost by waiting.
      ⇒ **Full narrative: `07-CHANGELOG.md` 2026-08-16 (×3), 2026-08-17 (×2), 2026-08-23.**
      *(RETIRED to this summary 2026-09-02 — 101 lines → 21 — to free the line budget. Nothing was
      deleted: the arc is in the changelog and the rule is in the code comment.)*
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

- [x] HISTORY — `#24-rarepredicate` (original spec, 2026-08-06) — **the duplicate-catch exemption (`#24-roster` ruling 3). SOLVED — the  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

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

- [x] HISTORY — `#24-movepoolcounters` (original measurement) — **USER DIRECTIVE 2026-08-07.**  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

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

- [x] HISTORY — `#24-counterdesertgate` (original diagnosis) — ✅ FIXED 2026-08-07, the same day it was found. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing).
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

- [x] `#24-huntreachproof` (part 1 detail) — **narrowing: `hunt_ground_tile(require_driven=...)`,
      strict by default.** ✅ DONE. Retired to a summary 2026-09-03; detail in `07-CHANGELOG.md`.

- [x] `#24-huntreachproof` (original finding) — ✅ CLOSED. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05.** The ORIGINAL 2026-08-08 framing — *"only ONE counter rung has ever worked"* — kept for its reasoning; the shipped answer is the `- [x]` entry above.
- [x] `#24-r116sweep` — ✅ **ANSWERED 2026-08-09, CLOSED: DO NOT ADD ROUTE116 to `HUNTING_GROUNDS`. Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-17** (the R3 relief valve: this file hit its 3,600-line limit). ⛔ Nothing here is outstanding; read the archive for the reachability method behind the ruling.

- [x] `#24-battleitems` — ✅ **DONE, PROMOTED 2026-08-10 (user-approved), zero source drift.**  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

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

- [x] `#24-progressiongate` (original finding) — ‼‼ **USER-IDENTIFIED 2026-08-08, VERIFIED. The counter planner has  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

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
- [x] HISTORY — `#24-teachmsgstall` (original characterisation) — ✅ superseded; the live status is the `- [x]` entry above (shipped 2026-08-11, reopened the same day). **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05**, including its task signature, its "post_select DOES NOT MATTER" analysis and its NEXT STEP plan.
- [x] HISTORY — `#24-winonaground` (wrong-cause history) — ✅ CLOSED. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing). It records a diagnosis that was WRONG and how it was corrected.
- [x] HISTORY — `#24-winonaground` — **the original text was WRONG and is superseded.** Retired to
      a summary 2026-09-03; the wrong claim, its refutation and the measurement that settled it are
      in `07-CHANGELOG.md` and `08-MISTAKES.md`. ⛔ Kept as a slug so citations resolve.

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

- [x] HISTORY — `#24-teachpathrace` (original report) — ✅ CLOSED (fixed 2026-08-07, same day). **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05**, including its root-cause and FIX SHAPE paragraphs.
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

- [x] HISTORY — `#24-whiteoutloop` (part 2, "the hard plateau") — ✅ CLOSED; BOTH PARTS SHIPPED 2026-08-07. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing).
- [x] HISTORY — `#24-whiteoutloop` (diagnosis) — ✅ CLOSED; both parts shipped 2026-08-07. **Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-09-05** (no loss, no orphan — both invariants asserted before writing).
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

- [x] `#24-r121gate` — ✅ **CLOSED 2026-08-10: IT WAS ALREADY BUILT** — the THIRD stale "ready to build" header found that week, caught only because the spec was verified before coding. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted). ‼ **Its TWO REUSABLE RULES WERE PROMOTED to `14-AGENT-PLAYBOOK.md` §4 (items 2 and 6) on 2026-08-24** — *accessors take the BARE var name* and *`calculate_path` spans only DIRECTLY CONNECTED maps* — because a chapter author never looks inside a CLOSED punch-list item, and both had been costing real time.
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

- [x] `#24-magmahideout` — ✅ **DONE, CLOSED. Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-17** (`#24-handoffbudget`'s relief valve: this file hit its 3,600-line R3 limit). ⛔ Nothing here is outstanding; read the archive only if you need the history.

- [x] `#24-strength` — ✅ **DONE, CLOSED. Full entry ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md` on 2026-08-17** (`#24-handoffbudget`'s relief valve: this file hit its 3,600-line R3 limit). ⛔ Nothing here is outstanding; read the archive only if you need the history.

### ‼ THREE FLAGS THAT MUST STAY `0` (each hides a MEASURED regression)
`POKEBOT_LEAD_DEMOTE_WONDER_GUARD` (~20 pts) · `POKEBOT_AREA_ITEM_GATE` (~7 pts) ·
`POKEBOT_PC_ROTATION` (~19 pts of the last rung). All three REMOVED something and were
justified by counting failures without counting successes. Do not re-enable without a batch.


### ~~READY TO APPLY THE MOMENT BATCH `20260802-160603` LANDS~~ — ✅ APPLIED; header stale  — 📦 **ARCHIVED 2026-08-22 (PASS 5, R3 budget) → `28-HANDOFF-ARCHIVE.md`. CLOSED; moved verbatim, nothing deleted.**

### ‼ BATCH 5 LANDED — the blocker moved a THIRD time, to the LEAD  — 📦 **ARCHIVED 2026-08-22 (PASS 5, R3 budget) → `28-HANDOFF-ARCHIVE.md`. CLOSED; moved verbatim, nothing deleted.**

### ‼ APPLIED 2026-08-01 AFTER BATCH `20260801-075805` LANDED

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

- [x] `#24-navready-budget` (**KI-43**) — ✅ **DONE 2026-07-31** — fixed via a dedicated nav-ready budget. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [ ] `#24-wdcanary-dedupe` — `summarize_lane` counts `global watchdog` in stdout AND the
      debug log, so every reported figure is ~2× (`9 → 143` is really `5 → 72`). Dedupe the
      source, then `--resummarise` **all four** batches so they are read by one instrument.
      ‼ Specific to this canary — `GAVE UP` is debug-only, `BADGE:`/`losses` stdout-only.

### ‼ BATCH REVIEW 2026-07-26 (bundle `20260726-231412`) — two catastrophic bugs found & FIXED  — 📦 **ARCHIVED 2026-08-22 (PASS 5, R3 budget) → `28-HANDOFF-ARCHIVE.md`. CLOSED; moved verbatim, nothing deleted.**

### ‼ BATCH REVIEW 2026-07-27 (bundle `20260727-063751`) — PRE-FIX DATA + a new failsafe hole
That batch launched before the fixes above existed, from a working copy that had not been
pulled, so it re-confirms them rather than testing them. It did expose one NEW bug:

- [x] `#24-x4-framebudget` — ✅ **DONE** — the per-run frame cap could not stop a runaway run; now it can. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [ ] `#24-weatherinstitute-hang` — the specific hang P3 hit: `do_weather_institute` →
      `_ride_out_all_scenes` (`early_game.py:454`), then `state=3 controllable=False` for
      27M frames. The frame budget now BOUNDS it (the run derails and the batch continues),
      but the underlying scene wait is still wrong. Needs the first post-fix batch to see
      whether it recurs and how often before spending time on it.
- [ ] ⭐ `#24-grindconverge` — **RE-SCOPED 2026-09-09 AFTER AN ADVERSARIAL PASS KILLED THE OBVIOUS
  READING.** P1/P2 ground for 13-20M frames without reaching a level floor.
  ⛔⛔ **DO NOT BUILD IT AS "REPLACE THE FRAME CEILING WITH A CONVERGENCE TEST" — THAT IS KILLED.**
  At §Ch23 the test is **VACUOUS**: `estimate_frames_to_level` returns `None` only when
  `wild_level is None or wild_level <= 0`, and §Ch23 hardcodes `WILD_MAX = 40`, so the estimate is
  ALWAYS finite and positive. A predicate *"will this grind reach the target?"* returns TRUE for
  every one of the 16 refusals. ⇒ it does not RAISE the ceiling, it **DELETES** it and substitutes a
  tautology — strictly worse than *"raise the ceiling"*, which is already measured wrong.
  ‼ **AND THIS ITEM'S OWN TEXT IS A COST TEST:** *"a training target that the local grass cannot
  deliver **in reasonable time**"*. *In reasonable time* IS cost. The item cannot be cited as
  authority for replacing cost with convergence.
  ⭐⭐ **ITS REAL SHAPE IS ALREADY DESCRIBED IN CODE AND IS NARROW AND BUILDABLE** —
  `victory_road.py:474-476`: a spin parked on an `MB_NORMAL` tile **generates ZERO battles while
  looking perfectly healthy**. ⇒ the failure is *no encounters*, not *slow encounters*. The DETECTOR
  already exists (`_story_spin`'s xp watchdog, `_STORY_SPIN_NO_PROGRESS_FRAMES = 2400`,
  `early_game.py:168/217`); **its defect is DISPOSITION, not detection** — it bails into the
  500-round retry loop instead of abandoning the target. ⇒ **build the disposition, and make it
  SUPPLEMENT the ceiling, never replace it.**
- [ ] ⛔⛔ **STRUCTURAL FACT THAT CHANGES EVERY "BUDGET HEADROOM" ARGUMENT — VERIFIED 2026-09-09.**
  `MAX_FRAMES_PER_RUN = 5_000_000` sits at `story_mode.py:4329`, **inside `StoryEndlessResetMode`
  (`:4283`) — the BATCH HARNESS.** Production `StoryMode` (`:1123`) has **no total-frame budget at
  all**; `train_team` has only a 500-*round* guard. ⇒ **in a real run the per-call
  `MAX_TRAINING_FRAMES` ceiling is the ONLY pre-emptive bound in existence**, and removing or
  loosening it re-opens the `KI-28` shape with nothing behind it.
- [ ] ⛔ **AND THE HEADROOM ITSELF IS NOT THERE.** Measured at the 16 Ch23 refusals from debug-log
  `f`-stamps: median run had burned **85.8%** of the harness budget (median spare **710,600**, range
  78,800-1,932,800). The FULL bill — every battler under L47, not just the worst — exceeds the
  run's own remaining budget in **10 of 16** runs on the solo model and **14 of 16** with the
  2-way split, before the seven §Ch23 legs after training (declared caps ≥720,000).
  ⭐ **RE-RUNNABLE:** `py -3.12 tools/story-dev/probe_ch23_headroom.py` prints the 16-row table.
  ‼ These numbers were first published from an agent's report with no command behind them and a
  reviewer refused them; re-measured, two reproduced and **three did not** (median battlers 3.5
  → **3.0**, 9/16 → 10/16, 13/16 → 14/16). ⚠ Erratic/Fluctuating growth curves are approximated
  as Medium Fast in that tool, so species on those curves may be mis-costed.
- [ ] ⛔⛔ **"ONE UNDER-LEVELLED MULE" IS FALSE — IT IS 2-5 BATTLERS, MEDIAN 3.5.** Excluding
  `BENCH_SPECIES`, the count of battlers under L47 at the refusal is **2 to 5 (median 3.0)** (e.g. one run:
  `Swampert:L57 / Mightyena:L33 / Ninjask:L23 / Dustox:L29 / Machoke:L30 / Shedinja:L29` — **five**).
  The error message prints only `max(estimates)`, **which is why this tree believes it is one mon**.
  ⇒ every plan scoped to "the mule" is scoped to roughly a third of the real debt.
- [x] ⛔⛔ **WIRING THE PICKER IS KILLED 2026-09-09 — AND THE PREMISE OF THE 2026-07-21 DIRECTIVE IS
  NOT GENERALLY TRUE.** Six-agent adversarial pass. ⇒ **do NOT wire `best_training_grass` into
  training as a maintenance pass.** Three independent reasons:
  1. ✅⛔ **MEASURED 2026-09-09 — THE PROPORTION HOLDS, THE INFERENCE IS REFUTED.** *(Was
     `[AGENT, UNVERIFIED]`: "of 1,496 mons that ever reached 15+ behind, 88.8% were ALREADY more
     than 6 behind the FIRST time they were observed (median 11)", concluding **"THE MONS ARE BORN
     DEAD WEIGHT, so there is no early small-gap window to maintain."*)*
     **[MEASURED BY ME — `tools/story-dev/probe_laggard_origin.py`, batch `20260909-160339`,
     24 logs / 17,302 heartbeats / 78,113 id elements / 0 dropped]**
     ```
       population (ever >= 15 behind) : 63          first-seen gap > 6 : 53/63 = 84.1%  [claimed 88.8%]
       median first-seen gap          : 10          [claimed 11]
     ```
     ⇒ ✅ **THE PROPORTION IS ESSENTIALLY RIGHT** — most laggards DO arrive already past the
     threshold. A 5-angle adversarial pass put 88.8% inside the measurement's own 95% CI
     (74.3%-92.0%), and a **sampling-independent** arrival-anchored angle agreed (median 8 behind,
     ~80% > 6 at the instant of entry), which also proves heartbeat lag hides nothing here
     (median delta 0; identical for ~94% of paired mons).
     ⛔⛔ **BUT THE CONCLUSION DRAWN FROM IT IS FALSE, AND THAT IS THE HALF THAT ROUTED THE
     DECISION:**
     ```
       A arrived already INSIDE the <=6 window : 10        C never inside it at all : 38
       B arrived outside, LATER got inside it  : 15        => HAD a window (A+B) : 25/63 = 39.7%
           of which the LAGGARD LEVELLED UP    : 11  <= actionable
           of which the PARTY MAX FELL         :  4  (a deposit/swap — the bot did not earn it)
       median time inside the window : 163 heartbeats = 163 MINUTES (~2.7 HOURS emulated)
     ```
     ⇒ **"no early small-gap window to maintain" is refuted for 40% of the population**, and the
     window is not a sliver: the median mon spends **~2.7 HOURS of emulated time inside it**.
     ⛔ **BUT USE 33.3%, NOT 39.7%, WHEN PRICING A FIX.** A gap closes from either end, and only one
     end is actionable: 4 of the 15 recoveries happened because the party MAX FELL (the leader was
     deposited or swapped out — level never drops on a faint), not because the laggard improved.
     ⇒ **TRAINING-REACHABLE = A + B/level-rose = 21/63 = 33.3%.** *(Found by an adversarial review
     that was asked to attack exactly this claim; the tool now prints both numbers so the
     distinction cannot be lost again.)*
     ⇒ the problem is not only that they arrive behind — **a long window existed and was not used**,
     which is a different defect with a different fix, reachable at TRAINING time.
     ⛔⛔ **CORRECTED — THE 33.3% USED A WINDOW ONE LEVEL WIDER THAN THE CODE'S (found 2026-09-09,
     hours after publishing it).** My tool called a mon "inside the window" at `gap <= 6`, but the
     predicate is `level >= target - 6` with `target = team_max + 1` in boss-fodder mode ⇒ the real
     condition is **`gap <= 5`**. Re-measured on the same population:
     ```
       threshold                A inside   B rose   B topfell   TRAINING-REACHABLE
       gap <= 6  (my tool)            10       11           4      21/63 = 33.3%   <- overstated
       gap <= 5  (the CODE)            1       12           7      13/63 = 20.6%   <- USE THIS
     ```
     ‼ `A inside` collapses **10 -> 1**: nine of the ten mons that "arrived inside the window"
     arrived at **exactly gap 6**, the single value the predicate excludes.
     ⚠ **AND 20.6% IS ITSELF AN UPPER BOUND.** Outside boss-fodder mode `target` is the BOSS BAND,
     not `team_max + 1`, so "gap from team max" is not the code's coordinate there at all — this
     window only maps onto the predicate in the fodder branch.
     ⭐⭐ **THE FINDING THIS EXPOSED, AND IT IS BIGGER THAN THE CORRECTION.** First-seen gap over all
     184 mons in the batch:
     ```
       gap 0: 48   gaps 1-5: 12 TOTAL   gap 6: 23   gap 7: 36   gap 8: 26   gaps 9-15: 16   16+: 23
     ```
     **46% of arrivals land in gaps 6-8 while gaps 1-5 are nearly empty, and the window is gap <= 5.**
     ⇒ mons arrive SYSTEMATICALLY JUST OUTSIDE the training window.
     ⛔⛔ **AND THAT LEAD IS DEAD — KILLED 2026-09-09. DO NOT RE-PROPOSE WIDENING
     `TRAIN_CATCHUP_GAP`.** Four reasons, in one line each; **the full record with all raw output is
     in `07-CHANGELOG.md`, "I killed my own most promising lead, with evidence"**:
     1. **The histogram was contaminated** — 95 of 184 "arrivals" are not catches (starters, the
        Wally tutorial, **27 of Steven's allies merged by the §Ch19 multi-battle**, gifts, PC
        withdrawals, Shedinja spawns). All 48 gap-0 arrivals were non-catches. Genuine catches
        (n=89): `0-5: 2 | 6-8: 69 | 9-15: 2 | 16+: 16`.
     2. **The mechanism is refuted** — [MEASURED BY ME] 79/89 = **89%** of caught mons gain exp
        (median **+20 levels**); 59/89 = **66%** reach gap <= 5. They are not stuck outside it.
     3. **The fix does nothing** — `tools/story-dev/probe_catchup_threshold_sweep.py`: G=6 → G=∞
        admits **+2 mons** overall and **+1** of the 69 gap-6-8 catches; 65 of those 69 are already
        admitted at the shipped value. Flat from 5 to ∞ ⇒ the threshold binds nothing.
     4. **The gap is geography** — ⚠ [AGENT-MEASURED, NOT RE-DERIVED BY ME] all 90 catches fall
        inside the wild-band prediction (90/90, residual +0.20 ± 0.54); the bot already catches at
        its floor (only 40 of 8,401 catch-capable minutes offered a lower-gap catch).
     ⭐ **AND THE SAME REASONING WAS APPLIED TO A NEIGHBOURING CONSTANT ON 2026-07-24** —
     `06-DECISIONS-LOG.md:267-269`, rejecting an alternative:
     > *"3. Raise/lower the level window. Any level-denominated threshold is wrong for the same
     > reason the current one is: it cannot see the XP rate. Tuning it just moves which map it is
     > wrong on."*
     ⚠ **THAT ENTRY IS ABOUT `mon.level + 3`** (the evo-lookahead sufficiency gate, `story_mode.py:1563`,
     commit `e8d133be`), **NOT about `TRAIN_CATCHUP_GAP`** (`:1136`, commit `395c392d`, three days
     earlier). ⇒ it is an **ANALOGY whose reasoning transfers**, *not* a prior ruling on this
     constant. *(Recorded this way after a Tier 1 reviewer caught the overreach — the kill above
     rests on the measurements, not on borrowed authority.)*
     ⭐⭐ **AND THE FLAT SWEEP POINTS AT THE REAL CONSTRAINT.** If admission is unchanged from G=5
     to G=∞, then *what decides who trains is not the gap threshold*. A Tier 1 reviewer proposed
     bench membership — `_battler_slots()` (`modules/story/early_game.py:1894`) admits only a
     non-egg mon **holding a damaging move**. ⛔ **THAT IS UNTESTED AND CURRENTLY UNTESTABLE:
     `ids=` records no moves.** Reading the predicate suggests it is permissive, but that is a READ,
     not a measurement — and this project has a logged habit of those diverging.
     ⭐⭐⭐ **2026-09-10 — THE REFUSAL'S DRIVERS ARE NOW NAMED, AND THE OBVIOUS FIX IS DEAD.**
     **[MEASURED BY ME, reproduced by 10 agents]** the §Ch23 refusal message
     (`<Species>#<PID> alone needs <N> frames`) is dominated by ONE species:
     ```
       occurrences (all of x4-runs, stdout.txt): 414 = 198 Marill · 72 Slugma · 36 Mightyena ·
                                                  36 Nincada · 18 each Shedinja/Ninjask/Poochyena/Kadabra
       ⚠ BUT THE DECISION UNIT IS **23 DISTINCT REFUSAL EVENTS**, not 414 lines: each event renders
         18x in stdout and 15x in debug-logs (both counts correct, same events).
       Marill is named in **11 of 23 events = 47.8%** — the proportion HOLDS at event level.
     ```
     ⭐ **AND THE BENCH MECHANISM DEMONSTRABLY WORKS — THE LIST IS MERELY INCOMPLETE:**
     **[MEASURED BY ME, batch `20260909-160339`, n=13 Castform / 34 Zigzagoon]** `Castform` has a **92.3%** laggard rate and **0** refusals *because it is benched*; `Zigzagoon`
     20.6% and 0 refusals, benched. `Marill` (100% laggard, peak **L14 across 15 runs**, never once
     above L15 in 33 runs corpus-wide; `Azumarill` NEVER OBSERVED) and `Slugma` are the same shape
     and are NOT on the list.
     ⛔⛔ **BUT DO NOT ADD THEM — THE CANDIDATE IS DEAD.** Two reasons; **full record in
     `07-CHANGELOG.md`, "The §Ch23 refusal is diagnosed (HM carriers), and the obvious fix is dead"**:
     1. **Benching is "do not train", NOT "do not field"** (`07-CHANGELOG.md` F6, verified by me in
        code): the faint-replacement chooser (`story_mode.py:273-274`) filters on
        `None / is_egg / current_hp <= 0 / _excluded`, and `_excluded` (`:262-270`) is
        ally-and-already-battling only; `BENCH_SPECIES` has exactly two consumers, both in
        `victory_road.py`. ⇒ it deletes the only gate refusing to enter the E4 with a L13 Marill
        **and still fields it there**. ‼ A no-op on the estimate is not a no-op on the run.
     2. **The refusal is an ARGMAX** (`worst = max(estimates)` vs 250,000), so removing the named mon
        promotes the next: **6-10 of 23 events clear** *(four agents re-priced every event independently; conservative count 6)*, and the top residual is **Mightyena, the
        CRUNCH carrier that can never be benched**.
     ⭐ **THE DIAGNOSIS THAT SURVIVES, AND IT IS WORTH KEEPING:** the bot acquires **HM carriers it
     can neither train to the bar nor safely field** — Marill is caught purely as a Dive/Waterfall/
     Surf carrier and sits at **L13 in 100% of 521 sightings in the one exp-bearing batch** ⚠ **(corpus-wide it DOES level: 1,492 readings above L13 across 33 logs — see the correction below)**. The refusal is the MESSENGER, not the
     defect. ⇒ any real fix is UPSTREAM of both benching and training, and must answer *"what should
     happen to a mon that is carried for a field move and can never reach the battle bar?"*
     ⛔⛔ **THE SOLUTION SPACE, NARROWED BY MEASUREMENT — THREE DIRECTIONS ARE DEAD:**
     | direction | why it is dead | evidence |
     |---|---|---|
     | widen `TRAIN_CATCHUP_GAP` | admits **+2 mons** from G=6 to G=∞ | `probe_catchup_threshold_sweep.py` |
     | add the mule to `BENCH_SPECIES` | benching is *do not train*, **not do not field** — deletes the only gate and still fields it | `story_mode.py:273-274`; `07-CHANGELOG.md` F6 |
     | acquire the carrier at a better ground | **L27 still refuses** (336,755 vs a 250,000 ceiling) | `probe_dive_carrier_level.py` |
     ⭐ **WHAT THE MEASUREMENTS AGREE ON:** the carrier is **INERT IN THAT BATCH** — 521/521 sightings at
     `L13:exp1757` ⚠ **(NOT corpus-wide: 1,492 readings above L13 across 33 logs, and "never" was also CENSORING — 25 of 28 non-gainers were observed for less time than the slowest gainer needed)** — and the gate counts it as a battler. ⇒ any surviving fix
     must change **whether it is in the party at the gate**, or **whether the gate counts it**, not
     how much it is trained.
     ⛔⛔ **AND A PC DEPOSIT IS THE FOURTH DEAD DIRECTION — found by `precheck_prior_art.py` in two
     minutes, before any design.** `06-DECISIONS-LOG.md:1313-1316`: *"**Deposit to make room** — the
     real fix… Rejected FOR NOW because it is the shape of `POKEBOT_PC_ROTATION`, **which is disabled
     for costing ~19 points by depositing team members**."* ⇒ it was TRIED and it LOST 19 points.
     ‼ And the machinery carries **four documented live defects** (`06-DECISIONS-LOG.md:2694-2716`):
     `withdraw_from_box` counts `alive` EXCLUDING EGGS (its own sibling fixed exactly that bug);
     `interact_with_pc` has **unbounded `while … press A` loops** (`:424-433` plus four more), and per
     the decomp `Task_WithdrawMon` on a full party never reaches the state they wait for; the capacity
     guard tests `get_party_size()` when the game uses `CalculatePlayerPartyCount()`; and its blanket
     `except Exception` has no `StoryAbort` guard, so **a whiteout during a PC visit is being
     LAUNDERED today**. ⇒ depositing the carrier is not a quick win, it is four prerequisites deep.
     ⛔⛔ **AND THE FIFTH DIRECTION IS DEAD TOO — "bench a mon that has never gained exp since
     capture". KILLED 2026-09-10 BEFORE ANY CODE, BY A PROOF.** **Four CATCH-OBSERVATIONS across THREE distinct `Abra`** (one PID recurs in two separate reset-runs of the same lane — deterministic RNG, not two mons) were caught
     byte-identical at `L7:exp236` (the exact MediumSlow curve minimum); **three trained on to
     Kadabra L17-L20 and one never gained a point** — *verified by me*:
     ```
       A5FC8AAC  L7:exp236 -> Kadabra L20      BCE77DD9  L7:exp236 -> L7:exp236  (inert)
       A5FC8AAC  L7:exp236 -> Kadabra L17      51A86B58  L7:exp236 -> Kadabra L17
     ```
     ⇒ **at capture every mon satisfies the predicate**, and minutes-to-first-exp-gain across 89
     genuine catches is **continuous, not bimodal** (1,1,1,1,2,2,2,3…44,47,128,256,397,420,459 — no
     gap). Misclassification never falls below **65%** at any threshold. **No predicate reading
     current state can separate a tool from a future battler.**
     ⛔ **AND IT WOULD MAKE THINGS WORSE.** The predicate is MONOTONE (false→true only) and
     `team_is_ready` re-runs `battler_identities()` AFTER the grind (`victory_road.py:2055`): a mule
     excluded at the estimate that later gains one point **re-enters at L13 and raises after the
     budget is spent** — moving the refusal from before the cost to after it.
     ⛔⛔ **AND MY OWN LOAD-BEARING CLAIM WAS WRONG AT CORPUS SCOPE — CORRECTED HERE.** I published
     *"all 521 Marill sightings read `L13:exp1757`; the carrier NEVER gains a point"*. That is true
     of **one batch** and false of the corpus: across all **33** Marill-carrying logs the levels are
     `L13: 5,951 | L14: 926 | L15: 566` ⇒ **1,492 readings above L13**, and 5 of 33 runs show it
     levelling. ‼ It is also **CENSORING**: the slowest observed gainer needed 157 minutes, and
     **25 of 28 non-gainers were observed for less time than that**. ⇒ "inert" was an artifact of the
     observation window as much as a property of the mon.
     ⭐⭐ **AND THE PROCESS LESSON — THE MANDATORY FIXTURE TEST WAS VACUOUS.** Every member of the
     known-good fixture sits far above its capture level, so this predicate benches NOBODY there and
     "passes" while discriminating nothing. **Passing the test that killed the 2026-09-08 design was
     NOT evidence for this one.** A mandatory check that a candidate satisfies trivially proves
     nothing — the check must be one the candidate could FAIL.
     ⇒ **FIVE DIRECTIONS ARE NOW DEAD AND THERE IS NO SURVIVING CANDIDATE.** That is the honest
     state. The next attempt should start from the ROUTING question (is the carrier needed at
     §Ch23 at all?) rather than from another predicate over party state.
     ⛔ Run `tools/story-dev/precheck_prior_art.py` first: it has now killed four directions.
     ⛔ **DO NOT BUILD A FOURTH DESIGN WITHOUT RUNNING `tools/story-dev/precheck_prior_art.py` FIRST**
     — three have died here in two days, and two of the three were killed by arguments already in
     this repo.
     ⚠ **SIDE FINDING, load-bearing if anything here is ever promoted:**
     `custom-pokebot/modules/story/victory_road.py:1806` has **NO empty-battler guard**; it exists
     only in sandbox (`:1817-1827`). `06-DECISIONS-LOG.md` shipped that guard as a hard prerequisite
     for touching this predicate ⇒ promote the guard WITH any change, or the prerequisite is
     silently unmet.
     ⭐⭐ **THE QUESTION THAT REOPENS, AND IT IS THE REAL ONE:** if caught mons DO train and DO reach
     the window, **why is `#24-lowlevelmules` still ~a third of run-ends?** The cause is NOT "they
     cannot get into training". That is now ruled out with evidence, and the next investigation
     should start from what happens AFTER they are admitted.
     ⚠ **DENOMINATOR: 1,496 IS NOT REPRODUCIBLE.** An adversarial sweep of 17 unit definitions x 39
     batches found no population of 1,496 anywhere, and none within +-5% of it at +-3pp of 88.8%.
     ⭐ The likeliest explanation is benign and was found by the same pass: keying `party=` by
     **species + re-entry generation** (the natural pre-PID method) yields **81.9% / median 11 on
     story runs alone — the claimed median exactly**. ⇒ treat 1,496 as an artifact of a pre-`ids=`
     instrument, not as evidence of bad faith; and note the direction — species keying
     **UNDERSTATES** born-behind (72.9% vs 84.1%), so the instrument cannot explain a too-HIGH
     number.
     ⛔⛔ **AND THE MECHANISM SENTENCE WAS WRONG — VERIFIED IN THE CODE, NOT REPORTED.** This bullet
     used to say *"`TRAIN_CATCHUP_GAP = 6` excludes them from `to_train`"* keyed on the TEAM MAX.
     `story_mode.py:2135-2137` actually reads:
     ```python
     catchup  = target - self.TRAIN_CATCHUP_GAP        # target - 6, NOT team_max - 6
     to_train = {i for i in battlers if party[i].level >= catchup}
     to_train.add(strongest)                            # <- the strongest is ALWAYS included
     ```
     with `need = [i for i in to_train if party[i].level < target]` at `:2142`. ⇒ the window is
     **`target - 6 <= level < target`**, and `target` is **`team_max + 1`** in boss-fodder mode
     (`:2095`) but the **BOSS BAND** otherwise. So the exclusion is REAL and the framing was
     imprecise: in the team-keyed branch it is ">5 behind team max", near enough that the original
     conclusion survives — but a reader planning against "6 behind the team max" is planning
     against the wrong quantity in the branch that does not use it.
     ‼ `to_train.add(strongest)` and the `losses >= 2` top-up mean the set is **not purely
     gap-based** — another reason a plan keyed on a single gap number can miss.
  2. ⛔ **[AGENT, UNVERIFIED] THE ECONOMICS ARE SOMETIMES NEGATIVE.** `xp/battle = 50.2 * wild_level
     / 7` depends ONLY on the DEFEATED wild's level, so a level-matched (lower) band pays LESS per
     battle and can only win via the full-vs-half share — capped at 2.0x. Reported example: a L12 mon
     soloing its matched ROUTE117 earns **71.7 xp/battle** against **78.9** swap-training on
     ROUTE111 — **0.91x, i.e. WORSE**. ⇒ *"a matched area beats swap-training"* is not a general
     truth under this codebase's own XP model.
  3. ⛔ **[AGENT, UNVERIFIED] IT DOES NOT EVEN DELIVER "FULL XP".** The picker's winnability boundary
     (`mon_level >= lo - 1`) OVERLAPS the swap trigger (`level + 2 <= foe.level`): at L18 its own
     pick still swap-trains on **75%** of the band.
  ⭐ **WHAT THE ROUND DID ESTABLISH, AND IT IS NOT NOTHING:** early maintenance would be far cheaper
  than late payoff (**[AGENT, UNVERIFIED]** ~1.2% of a lane budget at Stone vs ~33% at Feather), so the distinction
  from the killed §Ch23 relocation is REAL — the idea fails on its own mechanism, not by being that
  fix again.
- [x] ✅ **SETTLED 2026-09-09 BY A CHECKED-IN TOOL — AND THREE EARLIER ANSWERS WERE ALL WRONG.**
  The question *"does a training relocation ever deliver battles?"* was answered three times before
  this: an agent said **114/114, 1:1, ZERO battles delivered**; I "refuted" it with **128 not 114**
  (contaminated — 14 of my 128 were `FIERY_PATH` COUNTER-HUNT lines that merely name ROUTE111 as the
  bot's CURRENT position); a reviewer corrected my contamination and concluded the 1:1 **holds**.
  ⭐ **All three were aggregate reasoning.** `tools/story-dev/probe_training_relocation.py` anchors on
  the FULL message shape, excludes the counter-hunt look-alike explicitly, and pairs each decision
  with its own outcome **inside its own run**:
  ```
  453 relocation decisions   (613 training drops, 162 counter-hunt look-alikes EXCLUDED)
    252  (55.6%)  battles delivered
    130  (28.7%)  DROPPED as unreachable
     71  (15.7%)  no signal in window
  ```
  ⇒ **"zero battles delivered" is FALSE — relocation succeeds most of the time.**
  ⭐⭐ **BUT THE REAL FINDING SURVIVES AND IS WORTH AN ITEM: ~29% of training relocations end in an
  unreachable drop.** That is the honest number, it is reproducible in one command, and it is a real
  defect — just not the catastrophe three earlier answers described.
  ‼ **THE LESSON: TWO TOTALS MATCHING IS NOT PAIRING.** 453-vs-613 looks like nothing in aggregate;
  only per-run pairing exposed the 28.7%. Aggregate agreement is coincidence until each event is
  matched to its own outcome.
- [x] ✅ **FIXED 2026-09-09 — TWO FALSE STATEMENTS IN THE FUNCTION THAT DECIDES RELOCATION.**
  **[MEASURED BY ME]** `training_areas.py:432` is
  `FODDER_RULE = _os.environ.get("POKEBOT_FODDER_RULE", "xp_rate")` — the default is **xp_rate** —
  while `_local_grass_is_fodder`'s docstring claimed *"behaviour under the default rule is
  byte-for-byte the legacy expression"* and its branch comment read `# "legacy" (default)`. **Both
  false, and not equivalent:** `xp_rate` returns NOT-fodder whenever `best_available_max` is falsy,
  so a caller that has not looked for an alternative gets NO relocation, where `legacy` would compare
  levels. ⇒ anyone reasoning about when this bot relocates got it backwards — **including my own
  agent brief, which three reviewers had to correct.** Comment-only fix; it adds one file to the sandbox drift (run `promote.py --check` — the authority, never restated here).
- [ ] ⚠ **`best_training_grass(mon_level)` — the per-mon, trainee-keyed picker requested 2026-07-21 —
  HAS NO **PRODUCTION** CALL SITE** (`training_areas.py:102`) — ⚠ it DOES have one TEST caller, `tools/story-dev/repro_no_return_grounds.py` (import :49, call :75), which exercises its no-return-ground refusal. *(This bullet read "ZERO CALL SITES" until 2026-09-09; my grep had been scoped to `sandbox-pokebot/` and `PROJECT KNOWLEDGE/`, so `tools/` was invisible to it. ⇒ a MEASURED claim must carry its SCOPE.)*. And
  `grep -c VICTORY_ROAD modules/story/training_areas.py` = **0**, so the picker cannot even compare
  against the ground §Ch23 uses. That is a `#24-trainmap+` gap, not a new concept.
- [ ] ⚠ **NEW, PREVIOUSLY UNFILED:** the post-hoc frame REPORT at `story_mode.py:4535`
  (`raw_frames = get_frame_count() - start_frame`) does **not** re-base across the reset performed
  inside `super().run()` at `:4506`, so **printed per-run frame totals are wrong**. The live
  enforcement path DOES re-base (`:4386-4388`), so the budget itself is correct — it is the REPORT
  that lies. ⇒ derive frames from debug-log `f`-stamps, never from the printed summary.
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

### 🔜 `#24-dexhunt` — catch EVERY new species, and hunt for unseen ones — **RE-AFFIRMED AND WIDENED BY A NEW USER DIRECTIVE 2026-09-04; NOW UNBLOCKED** (user proposal 2026-07-29, ruled 2026-07-31)

⛔⛔ **THIS IS THE ITEM THAT SERVES THE 2026-09-04 CATCHING DIRECTIVE. DO NOT OPEN A SECOND ONE.**
*(I opened `#24-dexcatch` on 2026-09-05 with a fresh guard list before an adversarial reviewer found
this entry and the 2026-07-31 ruling. That ruling PINS the predicate — "the codebase already has the
right predicate: `counter_hunt.resource_blocker()`. **Reuse it rather than writing a second one that
can drift**" — so my guard list WAS the forbidden second predicate. `#24-dexcatch` is retired before
it ever shipped. See `08-MISTAKES.md` 2026-09-05.)*

**THE NEW DIRECTIVE (2026-09-04, verbatim):** *"I am fine with the bot catching and training
pokemon, it should be doing this as well as collecting pokemon (new, rare, considered rare) to fill
out the pokedex"*. ⇒ it does not overturn the 2026-07-31 ruling; it **widens** it — Pokédex
completion becomes a first-class goal, and **rarity becomes a selection criterion** rather than an
accident of what the bot happened to meet.

**✅ WHAT IS NOW MEASURED AND UNBLOCKED (2026-09-05):**
* **Dex: seen 116 / owned 11** — **105 species seen but never caught**, incl. Pikachu, Gyarados,
  Skarmory, Kingdra, Tentacruel, Crobat, Azumarill, Magneton, Xatu.
* **23 Poké Balls** held ⇒ `resource_blocker()`'s only remaining gate (`_ball_count() <= 1`) is clear.
* **A full party no longer refuses a catch** — ruled `#24-pcoverflow` 2026-08-05; it lands in the box
  and `pc_trip.withdraw_from_box` retrieves it. The PC is empty (all 14 boxes).
* **`#24-flyunlock` is CLOSED**, so the bot can finally REACH wild encounters at all.

**⛔ THE FIVE CONSTRAINTS AN ADVERSARIAL REVIEW FOUND — build against these, they are measured:**
1. **`_should_catch` already implements the right dex test** (`story_mode.py:1423`, comparing
   `owned_species` by national dex number). It is gated off by conditions written for the NARROWER
   pre-Gym-1 team-building purpose: `if get_event_flag("BADGE01_GET"): return False` and a
   party-full check. ⇒ **relax those two; do not rewrite the predicate.**
2. ⛔ **THE SPIN'S WATCHDOG IS EXP-BASED AND A CATCH EARNS ZERO EXP.** `_story_spin` stops after
   `_STORY_SPIN_NO_PROGRESS_FRAMES = 2400` of unchanged party EXP (`early_game.py:168,183-219`). A
   catch-and-skip phase moves that number by nothing ⇒ the watchdog fires every ~40 s and the caller
   re-navigates: **an invisible retry loop, not a hang you would see.** `counter_hunt.hunt` survives
   only because it FIGHTS nearly every encounter.
3. ⛔ **THE FRAME BUDGET IS BLIND HERE — KI-36.** `_run_with_frame_budget` cannot check itself while
   a battle handler sits above the mode, and a catch phase is ~100% battle handler. KI-36 measured
   25,632,106 frames against a 5,000,000 cap reporting `frame-cap=0`.
4. ⛔ **NEVER RETURN `BattleAction.Catch`.** It routes through `_listeners.py:277` to the STOCK
   `CatchStrategy`, whose `decide_turn` returns `switch_to_manual()` the moment no ball can be
   thrown (`catch.py:45-48`) — and ball exhaustion is this feature's DESIGNED terminus. Return a
   STRATEGY OBJECT (`StoryCatchStrategy`), which `_listeners.py:124` routes through `fight()`.
5. ⛔ **"PARTY UNCHANGED BY PID" IS A VACUOUS GRADE HERE** — with a 6/6 party every catch goes to the
   box by construction, so the PID SET cannot change and the check passes whether or not the feature
   ran. Keep it as a SAFETY INVARIANT; grade on **`owned_species` COUNT STRICTLY INCREASED** and name
   the new dex numbers. ⚠ And do NOT grade party ORDER: `choose_new_lead_after_battle` legitimately
   rotates the lead after a faint, which catch battles cause often.

- [x] ✅ **THE "88.8% ARE BORN BEHIND" FIGURE — WHICH IS THIS ITEM'S PRIORITY ARGUMENT — IS
  `[AGENT, UNVERIFIED]` AND WAS *UNVERIFIABLE* UNTIL 2026-09-09.** **[MEASURED BY ME — scope:
  `x4-runs` 298 `stdout.txt` + its `debug-logs/*.log`, `sandbox-pokebot/profiles` 500 `*.log`,
  `tools/story-dev` 500 `*.log`]** party telemetry recorded `Species:L<level>` and nothing stable:
  `Species#PID` appeared in **96** stdout lines, **all §Ch23 refusal messages AT THE TIME OF MEASUREMENT** ⚠ **RE-MEASURED 2026-09-10: the corpus has since grown to 140 such lines across 14 files and 2 are "counter training finished" lines, so the "all" NO LONGER HOLDS. The finding it supported — that no CONTINUOUS PID-bearing telemetry existed — is unaffected.**, plus ~15 lines from
  one-off probe drivers. ⇒ **a Pokémon could not be followed across a run.**
  ✅ **FIXED — `modules/debug_logger.py` now emits `ids=[Species#PID:L<lv>:exp<n>, …]` per
  heartbeat.** Full record under **`#24-lowlevelmules`** (that item owns the measurement); it is
  noted here only because the same field is what will finally test THIS item's priority argument.
  ✅ **BAN LIFTED 2026-09-09 — IT HAS BEEN MEASURED.** Cite it as: *"~84% of mons that reach 15+
  behind were already >6 behind when first seen (measured, n=63)"*. ⛔ **DO NOT cite the conclusion
  that used to accompany it** — *"born dead weight, no early window to maintain"* is **REFUTED**:
  **39.7% had a <=6 window** — median **163 minutes (~2.7 HOURS)** of emulated time — of which **33.3% of the population was TRAINING-REACHABLE** ⚠ **(SUPERSEDED — use 20.6%; the code's real window is `gap <= 5`, see bullet 1)** (the rest recovered only because the party max fell). See bullet 1 and `tools/story-dev/probe_laggard_origin.py`.

- [x] ⭐⭐ **DESIGNED 2026-09-09 (6-agent adversarial pass) — VERDICT: BUILD A NARROWER VERSION,
  AND ONE PREREQUISITE MUST SHIP FIRST.** The shape that survived: post-badge catching allowed
  **only at a FULL party** (so the game stores it via `CopyMonToPC` and it cannot consume the
  HM/counter runway `#24-partycap` measured as load-bearing) **and only when no hunt is armed**.
  ✅ **STRUCTURAL CLAIMS I VERIFIED MYSELF** (static reads — these are what the build rests on):
    * `ensure_hm_learner` is **SELF-FENCED**: `early_game.py:4505-4506` raises at `party_count >= 6`
      *before* its spin ⇒ **a party==6 dex gate can never fire during an HM hunt.**
    * `counter_hunt.catch_confirmed` is **SPECIES-BLIND on the box path**: `counter_hunt.py:363-365`
      returns True for **any** new box PID ⇒ an unrelated dex catch at party 6 would END the spin,
      the species-aware verdict would then find nothing, and the ladder fails. ⛔ **This is the real
      landmine and it is why the "no armed hunt" half of the fence is not optional.**
  ⛔⛔ **THE SPEC AS DRAFTED WOULD NOT HAVE WORKED — AND WOULD HAVE FAILED SILENTLY.** It calls
  `counter_hunt.hunt_active()`. **That function does not exist** (0 mentions); the real name is
  **`is_armed()`** — the cited line `:73` is correct, the NAME is invented. Because `_should_catch`
  wraps its body in `except Exception: return False`, the `AttributeError` would have been
  **swallowed**: the feature would never fire, and the A/B would have read "no difference" ⇒ **a
  REFUTATION of a feature that was never running.** ‼ Five other symbols checked out (`is_armed`,
  `HM_CATCH_TARGET_DEX` `early_game.py:4330`, `number_of_balls_except_master_ball` `items.py:447`,
  `_should_catch`'s single call site, `StoryCatchStrategy`). **One invented in six.**
  ✅ **PREREQUISITE NOW SHIPPED — dex telemetry** (`modules/debug_logger.py`): `owned=<n>` on every
  heartbeat plus `[DEX] owned N -> M: +#<dex>…` when the set grows. Before this there was **zero**
  dex telemetry — the only story-path read of `owned_species` was `_should_catch`'s own gate ⇒
  every arm of the A/B graded on nothing.
  ⛔ **THE FIRST VERSION OF THAT PREREQUISITE WAS BROKEN AND TIER 1 CAUGHT IT**: `_last_owned`'s
  `global` landed in `enable()` instead of `on_frame()` (my regex anchored on `_stall_frames`, which
  is in BOTH), so every heartbeat raised `UnboundLocalError` inside `main.py`'s `except: pass` ⇒
  **all telemetry silently dead, including `party_ids`.** Fixed in both functions (`enable()` also
  gained the missing per-run `_last_owned = None` reset, or run 2 of a batch would diff against run
  1's dex), and now GATED by `tools/story-dev/repro_heartbeat_emits.py`, which drives the **real
  `on_frame()`** and is fault-tested (arm B: 0 heartbeat lines).
  ⇒ **NEXT: write the fence using `is_armed()`, and grade on `owned` strictly increasing.**
  ⚠ Also required by the build (not yet done): `story_mode.py:2500` prints *"for the team!"* — at
  party 6 the mon goes to a BOX. It does **not** lie today (the gate requires party < 4); it would
  begin lying the moment the fence lands, so it changes **in the same commit**.

**STATUS: OPEN — the fence is specified and its prerequisite is shipped; `hunt_active()` must be
written as `is_armed()`.**

---

### `#24-dexhunt` (original 2026-07-29 proposal) — 📦 **ARCHIVED VERBATIM to `28-HANDOFF-ARCHIVE.md`** (2026-09-08, R3 budget; nothing deleted, nothing edited).
- [x] ⛔ NOT A LIVE ITEM — it is the ORIGINAL proposal, kept for its rationale, which now
  lives in the archive under its 2026-09-08 banner. **The LIVE `#24-dexhunt` is the re-affirmed and widened section ABOVE this one** — act from that, not from this pointer.

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

### ‼‼ `#24-orphans` — SIX REAL RESIDUALS THAT WERE WRITTEN DOWN BUT NEVER TRACKED — **MIXED STATUS (2026-08-17, LATEST): 4 DONE `[x]` ((2) KI-65, (4) log collision, (5) compare_runs A/B axis, (6) the KI-76 shelving), 2 PARTLY DONE `[~]` ((1) — instrumentation SHIPPED, REACTION half open; (3) KI-66 — `_on_field` half FIXED+PROMOTED, OWNER-filter half open), and ⛔ NOTHING plain OPEN `[ ]`** (filed 2026-08-15; last updated 2026-08-17)
> ⛔ **(6) CLOSED THE ORPHANING, NOT THE DEFECTS** — KI-76's two defects are OPEN and live in
> `#24-ki76correctness`. ‼ This heading said *"1 OPEN `[ ]` ((6) …)"* for one commit after (6)'s own
> box became `[x]`; a Tier 2 cold-start audit counted the boxes and caught it. **Count the boxes,
> do not re-type the tally.**
> ⛔ **THE CHECKBOX AND THE HEADER MUST SAY THE SAME THING — corrected 2026-08-17 by a Tier 1
> reviewer.** This header called (1) *OPEN* while its box was `[~]` and its body opened
> *"✅ INSTRUMENTATION HALF DONE"*, and called (3) *PARTLY DONE* while its box was `[ ]`. Both are
> now `[~]`, which is what a half-done item is. ‼ It is the P2 header-vs-body pair in miniature:
> the marker is what gets skimmed, so a marker that disagrees with the prose IS the bug.

> ⛔ **THE HEADING IS A CLAIM ABOUT EVERY BULLET BENEATH IT (P2).** These six do NOT share a status —
> read each bullet's own marker. Three are closed; three are live.

> ⛔ **WHY THIS ITEM EXISTS.** An audit asked a question nobody had asked: *for every "still open /
> still owed / not built" sentence written this session, would a future session ever FIND it?* Six
> would not. ‼ **Four of the six share one shape — a live residual recorded inside a document half
> that is marked DONE or ARCHIVED** (a CLOSED KI's body, an "older framing" queue block, an
> archived handoff section, a research note). That is the P2 header-vs-body failure applied to
> TRACKING rather than to STATUS, and prose alone did not catch it — the question did.

- [~] **(1) `withdraw_from_box`'s VERDICT — ✅ INSTRUMENTATION HALF DONE 2026-08-17 (returned,
      BOUND, reported, gated, two-armed A/B). ⛔ REMAINING: the REACTION POLICY — still blocked on
      an UNMEASURED heap offset, and it needs the USER.**
      ⛔ **STATUS IN ONE LINE: production can now READ the verdict; it still does not ACT on it.**
      That split is deliberate and is the whole shape of this item.
      ✅✅ **WHAT SHIPPED (⚠ was sandbox-only; ✅ PROMOTED 2026-08-17, user-approved — drift was 0 then; ⚠ it is 1 as of 2026-08-23, see the STATE row):**
      all five exits of `withdraw_from_box` return `(landed, code, detail)` — the shape the recorded
      design asked for — its ONE caller (`modules/modes/util/higher_level_actions.py:420`) BINDS the
      result, and a new PURE function `withdraw_verdict_report` turns it into a reported line.
      ‼ **The codes distinguish ATTEMPTED-AND-FAILED from NEVER-ATTEMPTED** (`landed`, `not_in_box`,
      `party_full_no_deposit`, `did_not_land`, `error`). ⛔ Collapsing the no-attempt cases into a
      failure would manufacture one out of the commonest case — the same shape as the count-based
      lie KI-79 removed. ⛔ An UNRECOGNISED code and a MISSING verdict both read as FAILED.
      ✅ **PROVEN TWO WAYS, both MEASURED:**
      (a) **LIVE TWO-ARMED A/B**, `--driver boxcounter2` on `fortree_gym_wedge.ss1`:
          ARM B unfaulted → `verdict landed=True code=landed`, `ACCEPTANCE: PASS`, 0 fault lines;
          ARM A `POKEBOT_PCWITHDRAW_FAULT=1` → `verdict landed=False code=did_not_land` (×2), fault
          provably armed (2 `SKIPPING the PC interaction` lines), `ACCEPTANCE: FAIL` — which is the
          REGISTRY'S DOCUMENTED EXPECTATION for the faulted arm, not a regression.
          Transcripts: `evidence/2026-08-17-withdrawverdict-ARM{A,B}-*.stdout.txt`.
      (b) **THE GATE FIRES ON THE REAL BEFORE-CODE, not a synthetic one:**
          `repro_withdraw_verdict.py --build custom` (the unpromoted tree) FAILS on exactly the bare
          returns and the discarded result; the same gate passes on sandbox. Gate #26, 7 self-tests.
      ⛔ **DO NOT REBUILD ANY OF THAT.**
      🔜 **WHAT REMAINS — the REACTION half, and every constraint below still applies to it.**
      ⛔ **Do not open THAT half expecting to write mode code.** Its next action is a live probe for
      one heap offset. ‼ Header and body disagreeing on that was itself a P2 finding (2026-08-16).
      ✅ **DESIGN RULED 2026-08-16 — THE USER RULED** (`06-DECISIONS-LOG.md`): *"reattempt but after
      intelligently processing the data (text boxes it reads to determine why it failed)"*.
      ‼ **That is TWO requirements and the second is load-bearing:** reattempt, but **NOT blindly** —
      the retry must be informed by a DIAGNOSIS read from the on-screen TEXT. ⛔ A retry that repeats
      the same failing action without knowing why is the PING-PONG this project has been burned by
      twice (`#24-movelearn-recovery`; KI-65's recon). ⛔ **Bound it**, ⛔ **an UNKNOWN reason must
      NOT retry** (stop loudly instead), and ⛔ **the reason must be READ, not inferred from internal
      state** — inferring it is the same class of error as the original bug, which announced an
      identity derived from a COUNT. Taxonomy, bound and retryability follow from MEASUREMENT.
      ✅✅ **RECON DONE 2026-08-16 — READ `06-DECISIONS-LOG.md`'s DESIGN ENTRY BEFORE CODING.**
      It found a BLOCKER and FOUR PREREQUISITES, each of which a naive retry would AMPLIFY:
      ⛔ **BLOCKER — the text the ruling depends on is not where any existing reader looks.** PC
      messages go to `sStorage->messageText` (heap-allocated); every text reader in this repo reads
      `gStringVar4` or `gDisplayedStringBattle`. **The struct offset is unknown here and MUST BE
      MEASURED** (the technique is established — `pc_interaction.py:135-182` reads that same struct
      at `+0xC74`/`+0x6FA`/`+0x20A0` — but ⛔ do NOT guess the number). Until then every failure is
      `UNKNOWN`, and UNKNOWN must not retry ⇒ **the feature would ship INERT.** Measure first.
      ✅ The refusal STRINGS are already verified against our own symbol table's byte sizes
      (`gText_YourPartysFull` 0x13, `gText_BoxIsFull2` 0x11, `gText_ThatsYourLastPkmn` 0x1a …) ⇒
      compare **ROM bytes vs the live buffer** like `menu_parsers.py:357`; ⛔ never hardcode English.
      **PREREQUISITES (each is its own defect, and each is now tracked here rather than orphaned):**
      **P1 ⛔ `withdraw_from_box` (`pc_trip.py:481-482` (the gate is `:489`)) counts `alive` EXCLUDING EGGS — a live latent bug.** Its
      own sibling `deposit_one_dead_weight._occupied` (`pc_trip.py:248-263`) documents that exact
      exclusion as *"a REAL bug (found by adversarial review 2026-08-13)"* and was fixed; this
      function never got the fix. On **5 mons + 1 egg** the make-room block is SKIPPED and
      `pc_interaction.py:418` then raises. ‼ **A retry over this ping-pongs forever.**
      **P2 ⛔ `interact_with_pc` has UNBOUNDED `while … press A` loops** (`pc_interaction.py:424-433`
      plus `:466-492`, `:332-344`, `:363-376`). Per decomp, `Task_WithdrawMon` on a full party sets
      `state = 1` and **never reaches the state 4 that loop waits for**. Wrapping a retry around an
      unbounded wait MULTIPLIES a hang. *(Loop behaviour under repeated A is decomp INFERENCE, not
      observed — but "no bound + a state that may never arrive" is enough to bound it first.)*
      **P3 ⛔ the capacity guard uses the WRONG QUANTITY** — `pc_interaction.py:418` tests
      `get_party_size()` (**B**) while the game uses **A**; `pokemon_party.py:184-193` says capacity
      questions must use A. With a **HOLE** (A=6,B=5 — already OBSERVED 30x in `boxcounter2`) the
      bot proceeds and the GAME refuses. ‼ This is the case proving the ruling's second clause: the
      diagnosis must change the **ACTION** (deposit), not repeat it.
      **P4 ✅ FIXED AND PROMOTED 2026-08-16 (KI-81) — was: the blanket `except` had no `StoryAbort`
      guard, so a WHITEOUT during a PC visit was laundered.** `reraise_if_aborting(error)` is now the
      FIRST statement of all 8 handlers in `pc_trip.py` / `mossdeep_gym.py` / `higher_level_actions.py`
      in **both** forks; probe reads **53 → 45** on custom. ⚠ **This removes a hazard, it does not
      supply the retry** — a retry loop still must not re-enter a dead run, so keep the guard the
      first statement of any new handler this item adds. Precedents (TRY lines, re-derived from source
      2026-08-16 — ⛔ re-derive, never re-type; six of eight hand-copied citations in the KI-81 entry
      were wrong): `space_center.py:955` (handlers `:962`/`:971`), `mossdeep_gym.py:540` (handlers
      `:543`/`:554`).
      ‼ **P1 and P4 are worth fixing on their own merits even if the retry never ships.**
      KI-79 made the *message* honest (identity-verified, loud on failure) but production still
      cannot REACT:
      the function returns nothing and never raises, so a failed withdraw is now *reported* and
      still silently tolerated. ⛔ It was filed in the body of a KI whose header read only
      "CLOSED" — any session scanning for open issues skips it. (KI-79's header now carries the
      caveat.) The next Slugma-class derail is still invisible to callers.
- [x] **(2) ✅✅ DONE 2026-08-16 — KI-65 REPRODUCED, FIXED, A/B-PROVEN AND GATED (#25).**
      ⛔ DO NOT REOPEN. Retired to a summary 2026-09-03 (line budget) — the reproduction, the A/B
      and the gate are all in `07-CHANGELOG.md` 2026-08-16 and `31-KNOWN-ISSUES-ARCHIVE.md` KI-65.

- [~] **(3) KI-66 — PARTLY DONE: `_on_field`'s index space is FIXED AND PROMOTED; what REMAINS is
      the OWNER filter (measured INERT on our one fixture) plus `:541-545` and `_util.py:522-587`.**
      The multi-battle hazard is BROADER than the faint chooser: four more
      full-party scans are unguarded, one feeding an UNBOUNDED `while … press A`. OPEN,
      code-verified, never live-run, and untracked until now.
      ✅✅ **DRIVEN 2026-08-17 — `--driver ki66faint` IS BUILT AND WORKS. ⛔ DO NOT REBUILD IT.** It subclasses `SpaceCenter2Mode`, stages one of our own picks at 1 HP (two bytes, `data[86:88]`) so it faints in real combat, and carries a PROVEN guard against overwriting the unpinned fixture `post_space_center.ss1`. ⛔⛔ **AND THE HEADLINE IS REFUTED: the bot NEVER ATTEMPTED an ally slot.** Ally slots sat in `alive_slots` on both faints, but the chooser ASKED FOR slots 2 then 3 — both ours — because `choose_new_lead_after_faint` already filters allies. ‼ **A CANDIDATE IS NOT AN ATTEMPT**, so an A/B fixing only the owner filter shows NO DIFFERENCE here and could make it WORSE (it empties `alive_slots` and trips a FALSE 'no eligible replacement'). ‼‼ **THE REAL DEFECT IS `_on_field`'S INDEX SPACE** — field-order `gBattlerPartyIndexes` compared against a party `UpdatePartyToBattleOrder` has already permuted; it excluded Swellow while Swellow was on the BENCH (proven by its send-out at `f21009`), costing **1263 frames vs 59** on a clean faint. ⇒ **✅✅ **`_on_field`'s INDEX SPACE IS FIXED AND PROMOTED TO BOTH FORKS (2026-08-17, user-approved). ⛔ DO NOT REDO IT.** Direction MEASURED first by an observe-only probe, then applied; all gates PASSED when that landed (**25** at the time — ⛔ the CURRENT count is deliberately not repeated here; `run_gates.py` prints it and IS the authority. This sentence has now been stale at 25 AND at 26 — `run_gates.py` IS the authority) (measured). ➡ **NEXT: the OWNER filter is still unfixed and proved INERT on this fixture — it needs its OWN discriminator, not this one. `:541-545` and `_util.py:522-587` are also untouched.** Read KI-66's DRIVEN block first.
      ✅✅ *(superseded: "BUILD-READY" — the driver now EXISTS.)* Earlier: both blockers CLOSED by recon (a cold-start agent first found them
      by TRYING to begin it, then a follow-up recon closed them).
      ✅✅ **BUILD-READY AS OF 2026-08-16 — the two blockers are CLOSED by recon; read KI-66's `RECON 2026-08-16` block FIRST.** The FIXTURE existed all along and was merely undocumented: **`--driver spacecenter2`, anchor `saves/at_steven_2f.ss1`**, drives the real six-mon multi battle. The FAINT needs no new capability and no `gBattleMons` writer: **pre-stage one selected mon at 1 HP before the battle** (1, not 0 — a 0-HP mon is never SELECTED) and it faints in real combat. ⛔⛔ **REFUTED 2026-08-17 BY THE LIVE RUN — this block used to claim the ally case "needs all three of ours down = the LOSS condition". BOTH HALVES ARE FALSE:** only TWO of ours were down (Swellow was alive on the BENCH, sent out at `f21009`), and in a multi battle the side is `gPlayerParty[0..5]` — ours AND Steven's — so that is not the loss condition at all. The run WON, `whiteouts=0`. See KI-66's DRIVEN block. ✅ **Grade instead on the ATTEMPTED SLOT INDICES + refusal count on a SINGLE faint**, which `:630-636` reaches while two of ours are still alive. ⚠ ARM B's behaviour when only ally mons remain is a USER POLICY call.
      *(Superseded: "RECON IS STARTABLE; THE BUILD IS NOT".)* Same correction item (1) already carries. What it confirmed by
      reading: all four sites are live (`battle_handler.py:541-545`, `:588-598`, `:630-636`,
      `_util.py:522-587`), and the choke point `ally_party_indices()` EXISTS
      (`battle_strategies/default.py:12`), called from `default.py:189` / `level_up.py:53` /
      `story_mode.py:171` — and from **none** of the four. What BLOCKS the build:
      **(i) no anchor save is named anywhere that reaches a partner double battle, and
      (ii) no fault hook forces the PLAYER FAINT that is the sole trigger for all four sites.**
      ‼ **Without both, the obvious before/after A/B IS VACUOUS** — the entry's own words are
      *"none has ever run live (every §Ch19 drive had zero faints)"*, so both arms are
      byte-identical and read as *"the fix is unnecessary"*. ⇒ **first deliverable is a FIXTURE +
      a faint hook, not a patch.** *(Undocumented candidates a future session may evaluate — found
      by listing directories, NOT cited by any doc, so verify before trusting:
      `saves/at_steven_2f.ss1`, `saves/post_space_center.ss1`, drivers `spacecenter1/2`,
      `faintrepro`.)*
      ⛔ **AND ONE POLICY QUESTION FOR THE USER, not for an agent:** when only ALLY mons are
      alive, ARM B's correct behaviour is *"ride out the loss"* — but that contradicts
      `ally_party_indices`'s own documented fail-closed rationale (`default.py:31-34`, which
      fails closed to an empty set precisely to avoid pushing the caller into the full-party
      fallback). Deliberately losing a battle is a behaviour choice.
      ‼ **The `IndexError`-on-turn-1 sub-claim is REFUTED (2026-08-12), not pending.** Do not
      re-check it; `05-KNOWN-ISSUES.md` cites the driven run (`ch19d.log` f23255, six-entry party,
      multi battle WON).
- [x] **(4) ✅ DONE 2026-08-16 — `story_harness.py` no longer overwrites its log.** — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] (5) ✅ DONE 2026-08-17 — and the item's own premise was REFUTED — 📦 **ARCHIVED 2026-08-26 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] **(6) ✅ DONE 2026-08-17 — SHELVED (it now has its own item, `#24-ki76correctness`) AND
      MEASURED. ⛔ The DEFECTS remain open; what closed is the ORPHANING, which is what this bullet
      was about.** *(Was: "KI-76's CORRECTNESS half is OPEN and MIS-SHELVED. Its only queue mention
      sits inside a block the handoff brackets as 'older framing … ⛔ also NOT next'.")*
      ‼ **Verified before acting:** KI-76 had **no punch-list entry of any kind** — its sole
      appearance in this file was this bullet saying it was mis-shelved, and its sole handoff
      appearance was buried at `04-HANDOFF.md:610` inside a §Ch20-era block. It is now a first-class
      item with the measurement attached; the numbers live THERE, not here, so they cannot drift
      into a second copy.

‼ **PREVENTION, and it is a question rather than a rule:** at wrap-up, for every *"still open /
owed / not built / residual"* sentence written that session, ask **"where would a future session
FIND this?"** If the only answer is an append-only log, a CLOSED KI's body, or a research note, it
is ORPHANED — put it here. ⇒ `08-MISTAKES.md`, 2026-08-15.

### ✅✅ `#24-sanitycheck` — the 5-PASS DEEP AUDIT — **COMPLETE (5/5)**, ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`

- [x] **All five passes done and committed. ⛔ DO NOT RE-RUN ANY OF THEM.**
      ‼ **THE METHOD, which is the reusable part:** 8 agents per pass, ONE ANGLE EACH, sent in
      ONE message so they run concurrently, and **every agent required to FAULT-INJECT or
      RE-DERIVE, never to reason** — that single instruction is what found a gate that could
      not fail and a control that could not fail. ⛔ **VERIFY EVERY FINDING YOURSELF** (across
      the five passes, agent claims failed my check three times, and one arrived already
      STALE). Output contract: `SEVERITY | what | what you RAN | result | smallest fix`,
      ~16 lines, anything unexecuted labelled CANNOT-REPRODUCE. Full record in the archive.

### ‼ `#24-ki76correctness` — KI-76's CORRECTNESS half: the slide model's ENDPOINT is wrong (filed 2026-08-17 from `#24-orphans` (6), which existed because this had NO item of its own)

- [ ] **TWO OPEN DEFECTS IN `map_path.py`, and they have OPPOSITE arming profiles — ⛔ do not treat
      them as one issue, which is exactly what KI-76's own header did until this measurement.**
      **(A) THE DISMOUNT DEFECT** — `map_path.py:340-344` ends a slide on the LAST WATER TILE; the
      game moves the player ONTO the walkable land tile ahead and DISMOUNTS
      (`COLLISION_STOP_SURFING`). ⇒ wrong tile AND wrong movement mode; every planned step after it
      is wrong.
      **(B) THE ENDS-ON-A-WARP DEFECT** — `map_path.py:972` charges the 1,000,000 warp penalty
      against the NEIGHBOUR, and `:1013` only afterwards substitutes the slide DESTINATION. So a
      slide that ends on a warp is never penalised and never marked `is_warp`. ‼ And A* is *biased
      toward* long slides (~9x cheaper than walking under `avoid_encounters`), i.e. toward exactly
      the moves that spring it.
      ⛔⛔ **STOP — THE ONLY FIXTURE THIS ITEM HAS CANNOT TEST ITS ONLY LIVE DEFECT (found 2026-08-22,
      PASS 5). READ THIS BEFORE PLANNING AN A/B.** The pinned save is `post_dive_ki76.ss1` and
      `--driver ki76warp` stages in **SEAFLOOR_CAVERN_ROOM6** — and this item's OWN table below says
      ROOM6 has **ZERO** armed DISMOUNT chains. ⇒ a dismount A/B on that fixture runs **both arms
      over 0 armed chains**, prints *"no difference"*, and would read as a **REFUTATION of a
      1,852-chain defect that is real.** ‼ This is precisely the `team_max 39` vacuous-arm trap the
      standing directives were written about, sitting on the queue head, and no consistency check
      can see it — the item is perfectly self-consistent and perfectly unusable.
      ➡ **BEFORE ANY DISMOUNT WORK: capture an anchor standing on ROUTE132/133/134 or
      SEAFLOOR_CAVERN_ROOM7 with Surf** (those are where the 1,852 live), pin it, and name it here.
      ✅ **ONE THING IS STARTABLE TODAY WITH ZERO INPUT:** the single `get_map_data` check of the
      Sealed Chamber DIVE entry at ROUTE134 `(60,31)` — it decides whether this item is urgent or
      merely real, and needs no fixture at all.
      ✅✅ **MEASURED 2026-08-17 — `tools/story-dev/probe_slide_endpoints.py`, evidence
      `evidence/2026-08-17-ki76-slide-endpoints-MEASURED.stdout.txt`. ⛔ DO NOT RE-DERIVE THESE.**
      ‼ **PRODUCTION IS THE ORACLE**: every count is classified on `PathTile.forced_movement_to` —
      the endpoint `map_path.py:260-350` ITSELF computes — not on a replica. (A replica was written
      first, was kicked back by an adversarial review for being blind past a map boundary, and now
      survives only to supply the break REASON and as a cross-check: it agreed with production on
      **3,763 of 4,384** chains, and all 621 disagreements are the cross-map case.)
      | | armed chains | where |
      |---|---|---|
      | **(A) dismount** | **1,852** *(lower bound, understated by ≤24)* | ROUTE133 765, ROUTE132 542, ROUTE134 501, ROOM7 44, **ROOM6 0** |
      | **(B) ends-on-warp** | **9** | **ROOM6 only — ZERO on ROUTE132/133/134** |
      ✅ **The dismount PREMISE holds with no exceptions:** all 1,852 tiles the game would dismount
      onto are elevation 3 (`ELEVATION_DEFAULT`) — checked, not assumed, because that premise is
      what the whole defect rests on.
      ✅ **AND THE SAFETY HALF'S CAP IS NOW PROVEN, not assumed:** production followed every
      cross-map chain on ONE shared 512-step budget and the cap **never fired**; nothing cycles; the
      longest chain in the ROM is **77** steps ⇒ margin **6.6x**. ⛔ `map_path.py`'s comment claimed
      "32 tiles / ~16x / ROUTE132-134 unmeasured" — all three were stale and are corrected in the
      code (comment-only, AST-proven, net-zero on line count so no `map_path.py:NNN` citation moved).
      ✅ **PROMOTED 2026-08-17, USER-APPROVED** (`modules/map_path.py`, comment-only) in the five-file
      round — bytes now identical, AST still equal, and the three refuted claims are gone from custom.
      Restore point `restore/2026-08-17-pre-promotion-all5`. *(Superseded: this cell carried a drift figure; the STATE row and `promote.py --check` are the authority.)* **(`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven).**
      ⛔ **PRIORITY, and it is NOT what the docs said.** ‼ But §Ch23/Ever Grande is a **Fly
      destination** — VERIFIED IN OUR OWN FORK, `sandbox-pokebot/modules/region_map.py:54` — so the
      currents are BYPASSABLE there, and the handoff's "the route to … Ever Grande" OVERSTATES it.
      ⚠ **The Regi arc looks like the real forcing function, but that half is NOT verified and must
      not be treated as measured:** the Sealed Chamber's DIVE entry at ROUTE134 `(60,31)` comes from
      `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md:67`, whose own header says
      *"Everything else is UNVERIFIED IN OUR HARNESS"*. ⇒ **Before this item's 501 ROUTE134 chains
      are called unavoidable, confirm that entry with `get_map_data`** — one call, and it decides
      whether this item is urgent or merely real. ⛔ Do not repeat the coordinate as fact until then.
      ✅✅ **STEP 1 IS DONE 2026-08-17 — THE ENDS-ON-A-WARP DEFECT IS CONFIRMED LIVE.
      ⛔ DO NOT REBUILD `--driver ki76warp`.** It staged on `(8,12)`, pressed EAST onto `(9,12)`, and
      recorded the whole slide: **exactly the nine steps production predicted, ending exactly on its predicted `(14,8)`** (⚠ the COUNT and ENDPOINT were predicted; the intermediate tiles are what the recorded tile TYPES imply, and they match), then
      `SEAFLOOR_CAVERN_ENTRANCE` — warp-arrival tile `(10,1)` at f+142, then the game's own auto-step to `(10,2)`, which is the FINAL settled tile the driver graded on — a different MAP — with **`surfing` True throughout the
      slide and False on arrival**. ⇒ a planner resting on `(14,8)` in ROOM6 is wrong on map, tile
      AND movement mode. `ACCEPTANCE: PASS`, anchor hash unchanged.
      ‼ **The acceptance grades the INSTRUMENT, not the answer** (staged AND stepped AND anchor
      intact AND landed on one of the two predicted arms) — a driver that only passes when it likes
      the result is not an experiment.
      ⚠ **Two honest limits, both recorded:** the run does NOT confirm the DISMOUNT defect in its own
      right (that one is about a slide ending beside walkable LAND; this dismount came from a WARP
      transition), and n is small — a second run is a DETERMINISM check, never a replication.
      📁 `evidence/2026-08-17-ki76warp-RUN3-CONFIRMED.stdout.txt`.
      ⛔⛔ **AND THE PLANNER-SIDE ASSERTION IS *VACUOUS* — MEASURED 2026-08-17, NOT ARGUED.**
      The obvious next step ("assert `calculate_path` PENALISES or MARKS a slide destination that is
      a warp") **cannot fail on the only map where the defect is armed.** Two observe-only queries,
      re-run by hand after a Tier 2 agent reported them (⛔ an agent's word is not enough on a
      load-bearing point): asking for a path TO `(14,8)` returns ONE waypoint,
      `coords=(10,1) is_warp=True` — the planner already resolves it THROUGH the warp and MARKS it
      (`map_path.py:869` sets `is_warp` on the final node); and the real Room 6 crossing emits 13
      waypoints, **none of them `(14,8)`**, because A* cannot expand past that tile — continuing
      needs SEAFLOOR_CAVERN_ENTRANCE, which is not on ROOM6's connected set.
      ⇒ **Both arms identical. Shipping that assertion would have printed "no difference", which
      reads as a REFUTATION of a defect that is LIVE-CONFIRMED** — the worst available outcome.
      📁 `evidence/2026-08-17-ki76-plannerside-VACUOUS.stdout.txt`.
      ‼ **A subtler finding, worth more than the assertion would have been:** on that map the
      planner is **ACCIDENTALLY SAFE — safe by INABILITY, not by design.** It avoids the warp only
      because it cannot route past it, and that protection evaporates on any map where the far side
      IS in the connected set.
      ✅✅ **VACUITY RE-CONFIRMED EXHAUSTIVELY 2026-08-17 (pass 3), and it now covers the COST
      half too.** An adversarial agent swept **all 235 legal ROOM6 tiles x 235 destinations =
      54,990 `calculate_path` calls**: `(14,8)` appears as a non-final waypoint in **0** of them.
      The structural cause is topology, not tuning — `(14,8)`'s north/east/west neighbours are
      collision walls and its south neighbour is the current that feeds it, so it is a DEAD END
      A* can only reach as an explicitly requested destination. ⛔ **Therefore a COST-based test
      is vacuous for the SAME structural reason**: there is no competing route to compare costs
      against on this ROM. ⇒ **the planner-side half is vacuous IN ITS ENTIRETY here**, not just
      its `is_warp` piece.
      ‼ It also re-scanned every map with currents through the production oracle and reproduced
      **9 D2-armed chains ROM-wide, all `(14,8)` in ROOM6, 0 elsewhere**, and found **0** D2
      endpoints anywhere in the ROM with an escape route — so the dead-end is universal for this
      data, not a ROOM6 quirk.
      ➡ **WHAT IS ACTUALLY LEFT, restated after that sweep:** nothing on this ROM discriminates.
      A real test needs a map where a slide destination is a warp AND the far side is on the
      connected set — and **no such map exists here**. ⇒ this half is BLOCKED ON REALITY, not on
      effort; treat it as such rather than hunting for a cleverer assertion. Formerly:** the COST at `map_path.py:972` is charged against the NEIGHBOUR and never against
      the substituted destination, so the planner may still PREFER a route it should avoid. That is
      a route-CHOICE comparison (does the emitted route change when the penalty is applied to the
      destination?), **not** an `is_warp` check. ⛔ Do not start it by re-deriving the vacuous one.
      ⛔ **NOT READY TO PATCH, and the reason is KI-76's own:** both fixes are changes to SHARED
      pathfinding every mode depends on (the KI-59 shape), each needs its own A/B, and KI-76
      requires **LIVE confirmation before code depends on either**. This measurement is static; it
      does NOT discharge that.
      ⛔⛔ **SUPERSEDED 2026-08-17 — THE BUILD SPEC BELOW IS HISTORY. THE DRIVER EXISTS AND HAS RUN.**
      Everything from here to the NAMING HAZARD note was the recipe for `--driver ki76warp`; it is
      kept because its measurements (the staging tile, the nine entry tiles, the unreachability of
      `(14,9)`) are still the reference. ⛔ **It is NOT a work instruction any more** — a Tier 2
      cold-start audit found this `➡ NEXT ACTION` marker commanding a driver the same item declares
      built, seventeen lines above.
      ⚠ **NAMING HAZARD:** the two defects are numbered inconsistently across three files —
      `probe_ch20_currents.py:174` calls the WARP one "KI-76 / D1", `probe_current_edges.py:1` calls
      the `None`-unpack "KI-76 / D5", and KI-76 itself calls the warp one "Defect 2". ⛔ Say
      "dismount" and "ends-on-warp"; do not mint a fourth numbering.

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
- [ ] **(1) `train_team` never picks an area.** `early_game.py:1998` —
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

- [x] **`#24-reprorot` — DONE 2026-07-30.** The 4 "environmental / needs mgba" repro failures were real bugs. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted). ‼ **This exact misfiling recurred on 2026-08-23** (`#24-brokenrepros`) — see `#24-reprosweepratchet` for the structural cause.
- [x] **`#24-menuorder` — DONE 2026-07-30.** Story block + ×4 controls hoisted to the TOP of the menu. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
- [x] **`#24-x4headless` — DONE 2026-07-31.** Headless ENDLESS-RESET batch runner. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
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

- [x] **`#24-smashroute` — DONE 2026-07-31.** The bot clears a field-move obstacle that seals a route. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
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
- [x] **`#24-counters` phase 2 — ✅ BUILT 2026-07-30, and LIVE-VALIDATED many times since;  — 📦 **ARCHIVED 2026-08-23 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).

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
      Biggest find: `02-ARCHITECTURE.md`'s folder map omitted **`sandbox-pokebot/`, where all work
      happens**, while its own prose cited sandbox-only modules — the doc contradicted itself.
      Retired to a summary 2026-09-03; fixes/method/calibration: `06-DECISIONS-LOG.md` 2026-07-27.
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
      `_lead_best_matchup` (`early_game.py:1677`) picks `min(incoming_multiplier, -level)` —
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
      ⛔⛔ **THIS BODY HAS NOW GONE STALE TWICE — it said "20 of 24" and "Seafloor Cavern driven
      through Room 3" on 2026-09-03, when §Ch20 AND §Ch21 had both shipped as wired chapters.**
      ⇒ **DO NOT RESTATE THE LADDER HERE.** The ladder count and the live head belong in
      `04-HANDOFF.md` (the 60-SECOND VERSION and NEXT ACTIONS); this entry now POINTS there,
      because a second copy of a moving number is how it goes stale a third time.
      Current order: `#24-ch22chapter` → the `04-HANDOFF.md` NEXT ACTIONS queue.
      Sub-items live in `## Story bot (#24) — open backlog` below.
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
      `_should_catch` (`story_mode.py:1423-1442`) requires `not BADGE01_GET` AND
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
- [x] ~~`#24-team`~~ — ‼ **SUPERSEDED by `#24-organicteam`, which is ✅ APPROVED — GATE LIFTED** (user 2026-08-06, re-confirmed 2026-08-14). ⛔ Read `#24-organicteam`, not this. — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
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
- [x] **✅ `#24-ch8b-museum` — DONE 2026-07-22; the marker was 31 DAYS STALE** (found by a PASS 5 audit). — 📦 **ARCHIVED 2026-08-24 → `28-HANDOFF-ARCHIVE.md`** (CLOSED; moved verbatim for the R3 budget, nothing deleted).
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
      `_story_spin` (`early_game.py:171`) for the whiteout-abort and no-progress watchdog.
      The user wants it to WANDER the grass with human-like movement, mixing in occasional
      spins, so training looks organic instead of robotic.
      !! THIS IS THE SAFE PLACE TO PUT RANDOM MOVEMENT, and the risk profile is INVERTED
      versus travel meandering (#24-meander):
        * On a TRAVEL leg, extra steps mean more wild encounters, which means more battles,
          more damage and more whiteouts. Our dominant failure is travel attrition, so
          meandering there is actively dangerous.
        * While TRAINING, extra steps mean more encounters - which is the entire POINT.
          Wandering costs nothing we did not already want.
      SEAM ALREADY PROVEN: `run_in_circle` (`modules/modes/util/walking.py:726`) shows
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

## Done — ⚠ MIXED, and that is a defect being tracked, not a convention
> ⛔ **THREE STILL-OPEN `[ ]` ITEMS ARE FILED UNDER THIS HEADING** and are therefore invisible to
> anyone scanning for work: **`#24-partyindex-minus-one`**, **`#24-errorpath-frequency`**,
> **`#24-stalestatusclaims`** (that last one is named in `04-HANDOFF.md` as a startable
> alternative, so the handoff points INTO a section marked Done). Found by a PASS 5 audit
> 2026-08-22. ⇒ Move the three blocks above this heading; until then, this warning is the pointer.
> ⛔ **THE 8 OLDEST CLOSED ITEMS OF THIS SECTION MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-17)**
> on the R3 3,600-line budget. All were `[x]` and long closed; nothing was deleted. The relief
> valve is deliberate — `lint_docs` has been reporting ~105 completed items sitting in a
> CURRENT-STATE file, and this is the first draw on it.

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

### `#24-faintchooser-fourthspace` — ✅ CLOSED 2026-08-17, ARCHIVED 2026-08-22 → `28-HANDOFF-ARCHIVE.md`

- [x] **ANSWERED: no fourth index space is demonstrated; the anomaly is INERT. ⛔ DO NOT "FIX" IT.**
      ‼ **The rule that survives:** `handle_fainted_pokemon` has had THREE index-space bugs
      (KI-18, KI-34, KI-66) — ⛔ when a fix is a coordinate/index conversion, MEASURE ITS
      DIRECTION with an observe-only probe FIRST; never reason it out from the docstring,
      which has now produced three bugs. Full 70-line record in `28-HANDOFF-ARCHIVE.md`.

### `#24-partyindex-minus-one` — a BOUND-BUT-WRONG `party_index` of `-1` slips past KI-65's guards (filed 2026-08-17)

- [ ] **Found by an orphan audit, not by a bug report.** KI-65's fix guards
      `battle_move_replacing.py:285` and `:425` with `if party_index is None:`, which covers
      **unbound**. It does NOT cover *bound but wrong*: `get_party_menu_cursor_pos` does not raise on
      a bad cursor — it calls `set_manual_mode()` and returns **`slot_id = -1`**
      (`battle_move_replacing.py:138` assigns it straight through), and `get_party()[-1]` is the
      **LAST party member**. That is a WRONG MON, not an exception, so both guards pass it.
      ‼ **Why it was nearly orphaned:** it was written only inside KI-65's body — under a header that
      reads **CLOSED** — which is exactly the shape `#24-orphans` exists to stop. Now tracked here.
      ⚠ **NOT observed live and unquantified.** ⛔ Do not "fix" it blind: first measure whether
      `slot_id = -1` ever reaches that line (an observe-only probe, per the rule that settled KI-66),
      because `set_manual_mode()` has already fired by then and the run may be derailing anyway.

### `#24-errorpath-frequency` — the fixes are proven CORRECT but their real-world FREQUENCY is unmeasured (filed 2026-08-17)

- [ ] **Both 2026-08-17 fixes are error-path fixes whose rate in real play is unknown**, and this was
      stated honestly in the changelog and then tracked nowhere:
      * **KI-65** reproduces what happens WHEN `_read_offered_move` fails — never how OFTEN it does.
      * **KI-66** was driven on one fixture; the pathological faint cost 1263 frames vs 59, but how
        often a real run hits it is unmeasured.
      ‼ **This is the one question a BATCH is actually the right instrument for** — §0c: battle-level
      metrics get ~800 samples per 3-hour batch and CAN resolve, whereas finish rate cannot.
      ⛔ **Pre-register the questions BEFORE running**, or the result gets rationalised afterwards:
      (a) how many times does KI-65's "cannot verify" message fire? (b) how many faints occur inside
      a partner double battle, and what is the menu-open→send-out frame cost distribution?
      (c) any NEW derail class that did not exist before these two fixes?
      ⚠ Blocks nothing today. It is worth doing once several changes have accumulated, so the three
      hours buy more than one answer.

### `#24-stalestatusclaims` — an ADVERSARIAL AUDIT FOUND 14 TRACKING CLAIMS THAT ARE FALSE OF THE CODE (2 fixed on sight, 12 filed) (filed 2026-08-17)

**2026-09-08 — ONE SUB-CLASS OF THIS ITEM IS NOW GATED, NOT CLOSED. ⛔ THE ITEM REMAINS OPEN.**
The *drift-figure* sub-class is done and enforced: `probe_drift_restatement.py` (gate #46) forbids a
live restatement outside the STATE row. Fourteen instances were found and remediated — an audit
listed 3, a Tier 1 reviewer found a 4th, a grep a 5th, the gate six more, and a SECOND reviewer pass
a 14th that the gate itself had been blind to (line-global quote parity on a 30,045-character line).
⭐ The transferable finding for the REST of this item: **when one instance on a line is found and
another on the same line is not, suspect the INSTRUMENT, not the list.**
⛔ The other 12 filed claims are untouched by that work and still need auditing.

- [ ] ⛔ **These are DOC defects, not code defects — the code is fine. Each was verified against the
      repo by an agent that ran greps and tools rather than reading prose.** ‼ **Two were fixed on
      sight because they would MISDIRECT the next session** (see below); the rest are filed here so
      they are not re-discovered one painful item at a time.
      ✅ **FIXED 2026-08-17, on sight:**
      * an `➡ NEXT: decouple _counter_ladder from grass_is_fodder` arrow commanding work that had
        **shipped to BOTH forks** on 2026-08-16 (`story_mode.py:1901` is `if boss_teaches:`);
      * this file's own `#24-driftassertions` deliverable claimed the gate "walks past `zero`" and
        made WORD FORMS the job — **`_WORD_NUMBERS` already includes `zero`** and `_NUM` interpolates
        it into all seven drift patterns (`re.I`). Only CLAIM-SHAPE detection was open —
        ✅ **and THAT SHIPPED 2026-08-17; `#24-driftassertions` is CLOSED. ⛔ Nothing here is
        outstanding work.** *(This clause read "Only CLAIM-SHAPE detection is open" until the item
        closed; a Tier 1 reviewer caught it still commissioning finished work from ~3,000 lines
        away — the very defect the bullet above it describes, committed by the pass that describes
        it.)*
      🔜 **STILL TO SWEEP (each has both halves quoted in the audit; re-verify before editing):**
      1. `#24-leadpolicy` tracked TWICE with conflicting states (`[x] A+C BUILT` vs an `[ ]` bullet)
         and **no supersede marker**, unlike this file's other duplicate IDs. Code: `early_game.py:1755`.
      2. **KI-25** still says *"needs a user ruling"*; the ruling shipped.
      3. **KI-43** header says *"FIX NOT YET APPLIED"*; `_TRANSIENT_WAIT_FRAMES = 600` is live in BOTH forks.
      4. **KI-26** says *"exactly SIX sites"* → there are **eight**; its "biggest lever" already exists.
      5. `#24-counters` *"Phase 2 NOT STARTED / the executor itself"* → `counter_hunt.py` IS the
         executor (`def hunt` `:426`, wired `story_mode.py:1702`), and `:2267` already says BUILT.
      6. `#24-items` *"walks past every item ball"* → `collect_item_ball()` is live (`early_game.py:8059`).
      7. `#24-postwinona-save` body says *"No save exists past Winona"* → `saves/post_winona.ss1` exists.
      8. `#24-slugmaspin` *"production runs this regression WITHOUT its fix"* → forks are identical.
      9. `CREDIBLE_ANSWER_POWER` written as `(60)` in the present tense → it is **75** in both forks
         (and this file says 75 elsewhere).
      10. Marker/count drift: the marker table says `80/17/37` → measured **96/21/105**; *"all 8
          handlers"* → **9**; *"24 checks"* → **21**; *"KNOWN_GATES holds ONE entry"* → **3**.
      11. `05-KNOWN-ISSUES.md`'s own header says *"23 distinct IDs … KI-15 appears twice"* → **64**
          distinct IDs, and `KI-15` appears exactly once — inside that sentence.
      12. `cache/warp_graph_BPEE0.json` is called *"committed"* but is **git-ignored and untracked**,
          while `rare_species_dataset.py:61` reads it ⇒ that dataset cannot be rebuilt from a clean
          clone. ‼ This one is arguably a REAL defect, not just a doc defect — triage it first.
      ⛔⛔ **THE GATES CANNOT SEE ANY OF THIS.** `lint_docs` and `audit_doc_consistency` exit 0 over all
      ‼ **And `probe_stale_citations.py` EXISTS but is NOT REGISTERED in `run_gates.py`** — a gate
      that might catch this class is sitting unused. **Registering it (after fault-testing) is
      probably the cheapest first move on this item.**
      ⚠ The audit also relayed ~9 further suspected items it did NOT personally re-verify. Treat
      those as UNCONFIRMED and re-check before acting.

### `#24-mossdeepstrand` — winning BADGE07 LOCKS THE BOT INSIDE the Mossdeep gym (filed 2026-09-07, ✅ FIXED IN THE SANDBOX same day — ⚠ UNDRIVEN, NOT PROMOTED)
- [x] ✅ **FIXED 2026-09-07 (sandbox, UNDRIVEN).** Two halves, each a no-op off the gym map:
  Segment 18's `else` now calls `leave_the_gym()` before printing (`story_mode.py:3774`), and
  the chapter's own badge early-return leaves first (`mossdeep_gym.py:549`). ⛔ The IDENTICAL
  early-return in `fight_the_leaders()` (`:382`) was deliberately LEFT ALONE — that one is a
  SUB-STEP and is correct: leaving is the chapter's job, and the fight is retried 3x.
  ⚠ Acceptance still owed: a drive from a save standing on (23,8) with BADGE07 set.
- [x] `(23,8)` is an 11-tile collision island whose only exit is a **coord_event** at `(21,6)` no warp
  solver can offer (`mossdeep_gym.py:460-461`). Its sole stepper, `leave_the_gym()`, is called only at
  `:596` — **after** the badge early-return (`:548-549`, `:556-557`) — and Segment 18 skips the
  chapter once BADGE07 is set (`story_mode.py:3772`). ⇒ **double bypass: with BADGE07 set and the
  avatar on (23,8), nothing in the tree can move it.** The chapter's own `:590-593` comment warns of
  exactly this; a later early-return re-opened it. `KI-97` moves this derail from Segment 13a to 19,
  not away. ✅ **That is exactly what was done** (bullet above): `leave_the_gym()` is resume-safe
  (`:471-474`), so calling it at Segment 18 and before the chapter's early-return costs nothing
  anywhere else. Detail: `ai-research-notes/2026-09-07-batch-blockers-RECON.md`.

### `#24-ballrestock-ordering` — the counter hunt's ball restock is DEAD CODE from its only caller (filed 2026-09-07)
- [ ] ✅ `hunt()` holds the contingency (`counter_hunt.py:471-475`) but the ladder calls
  `resource_blocker()` first (`story_mode.py:1778-1782`) and returns; that blocker is now **only** a
  ball gate (`counter_hunt.py:405-407`) and `:1809` is `hunt()`'s sole production caller ⇒ **those
  five lines can never run.** Lane L03 lost a run to *"no spare Poké Balls"*, then bought 30 one run
  later. ⚠ **NOT a one-liner:** `provision_poke_balls` defaults to `RUSTBORO_MART`
  (`early_game.py:2299`), the tree's only mart constant, so from Fortree a restock is a cross-Hoenn
  trek spending the boss's one ruled hunt attempt shopping ⇒ minimum = ordering fix **+** nearest-mart
  lookup. ⛔ `06-DECISIONS-LOG.md:958/998/3423` checked — whitelist, one-hunt-per-run and second wind
  are SETTLED; **this ordering is covered by none.** Detail: `ai-research-notes/2026-09-07-batch-blockers-RECON.md`.

### `#24-punchlist-archive` — 03 is AT its 3600-line budget; the next item needs an archive pass first (filed 2026-09-07)
- [ ] ⛔ Move CLOSED items VERBATIM to an append-only archive; never splice. A 2026-09-07
  anchor-to-anchor compression swallowed a root-cause block and no gate noticed.

### `#24-tateliza-attrition` — the DEEPEST runs die losing to Tate & Liza, and NO guard catches it (filed 2026-09-07)
- [ ] ✅ MEASURED on the live batch: both `too many whiteout recoveries in a row` runs — the two
  deepest of the batch at **3,877,438** and **4,198,775 frames** — died in the Mossdeep Gym
  (`MOSSDEEP_CITY_GYM = (14, 0)`, `map_data.py:1005`) against **Tate & Liza**. Lane L04 reached
  **`defeat #24 here`**, L05 `defeat #11`. Each loss whites out, and each recovery **re-solves the
  117-step statue puzzle** (`Story: Ch18 plan #1 from (6, 35) — 117 steps`) before losing again.
- [ ] ⛔ **THE GUARD THAT SHOULD HAVE STOPPED IT NEVER FIRED, AND THAT IS THE REAL FINDING.** The
  non-convergence guard stops a boss it judges HOPELESS — but it grades on TYPE coverage, and against
  Psychic the party genuinely has Dark/Ghost/Bug answers, so `_boss_plan_is_hopeless` returns False
  and the bot simply keeps losing. ⇒ **it catches "wrong types" and is blind to "right types, too
  weak".** The 3 runs that died with a clean *"no super-effective answer"* diagnosis are the case it
  DOES handle; this is the case it does not, and it is the one that burns the most frames.
- [ ] ⚠ **TWO HYPOTHESES, NOT YET DISCRIMINATED — do not pick one without measuring.**
  (a) TEAM: the party is simply under-levelled/under-powered for a double boss.
  (b) BATTLE LOGIC: Tate & Liza is the story's one DOUBLE battle, and `KI-96`'s freshness invariant
  is **incomplete in doubles** — battle slot 0 encodes only the LEFT battler (decomp-verified
  2026-09-07), so a rotation aimed from a partly-stale order is unvalidated exactly here.
  ⭐ **The discriminator is cheap and already built:** run the `[KI96-REREAD]` drive against this
  fight and count rotations that hit the 240-press bound or log `DIFFER`. If rotations are clean, it
  is (a) and the answer is levels; if they wedge, (b) is contributing. ⛔ Do NOT grind levels first —
  that is the expensive arm, and it would mask (b) rather than rule it out.
- [ ] ⚠ Also worth pricing: a whiteout here costs the 117-step puzzle re-solve, so attrition at this
  boss is far more expensive per attempt than at any other. Detail: `ai-research-notes/2026-09-07-batch-blockers-RECON.md`.

### ✅ `#24-countermsg` — the counter guard's CORRECT diagnosis read as WRONG (filed + fixed 2026-09-07, sandbox, display-only)
- [x] ⭐ **This cost a false defect report, which is the justification.** From a live batch log I read
  *"Winona: Need one of: Rock, Ice, Dragon. Nearest reachable counters: Slugma (Fire)..."* and
  reported the recommender as violating its own constraint. **It was not.**
  `counter_plan.py:156,185-205` admits a species by TYPES **or** by a level-up move of a needed type
  (`#24-movepoolcounters`, user directive) — Slugma learns **Rock Throw at L15** and Fiery Path
  Slugma is L15. ⇒ the list was right and the LINE was unreadable. ‼ **A message that makes correct
  behaviour look broken costs what a bug costs: someone investigates it.**
- [x] The explanation was already computed and discarded: `counter_plan.py:331-335` builds
  `answer_via` (`"type"` vs `"move:Rock Throw@L15"`) under a comment demanding the log say which rule
  fired — with ZERO production consumers. Now rendered, verified by direct call:
  `Slugma (Fire) via move:Rock Throw@L15 on Fiery Path (tile (18, 19), L15-15, 10% rate) — reachable`
- [x] The printed top-5 is now deduped **BY SPECIES** (5 of up to 12). Live, four of Winona's five
  rows were the same Geodude across four Magma Hideout floors. ⛔ The ladder's `huntable_candidates()`
  dedupes by `(map, tile)` and does NOT collapse those — the floors are distinct maps. A reader wants
  SPECIES; the executor wants DESTINATION. Different questions, different keys, deliberately not
  shared. ⛔ **DISPLAY ONLY** — `_counter_catch_message` builds a `BotModeError` string
  (`story_mode.py:2053`) and feeds nothing the ladder chooses.

### `#24-counterprobe-rotted` — an offline counter-planner probe fails its OWN positive control (filed 2026-09-07)
- [ ] `probe_counter_candidates_offline.py` exits 1 with *"POSITIVE CONTROL — Norman finds Machop @
  FIERY_PATH: FAIL - the harness is broken... Ignore every other number this script printed."*
  ✅ RULED OUT as caused by `#24-countermsg`: the probe never calls `summarise_candidates`, and that
  diff is confined to that one function (hunks at `:474` and `:487`). ⛔ It is **not registered in
  `run_gates.py`** — nothing runs it, exactly the rot `#24-reprosweepratchet` names. Either repair its
  ROM stand-ins and register it, or delete it; **an ungated probe that lies is worse than none.**

### `#24-countermsg-repro` — the display fix has no committed regression guard (filed 2026-09-07)
- [ ] `#24-countermsg` was verified by calling `summarise_candidates` directly, and a Tier 1 reviewer
  independently reproduced the output byte-for-byte — but **nothing was committed that re-runs it**,
  so a future edit can silently drop `answer_via` again or break the by-species dedupe and no gate
  would notice. ‼ A DISPLAY regression is invisible by definition: the program keeps working and only
  the reader is misled, which is precisely how this defect survived since `#24-movepoolcounters`.
  **Build:** a small `repro_countermsg_display.py` asserting (a) a `move:` answer renders its
  `via move:<Name>@L<n>` clause, (b) a `type` answer renders `(type match)`, (c) a missing
  `answer_via` renders neither and does not raise, (d) the displayed list keeps at most one row per
  species. Fault-test each arm, then register as a gate and bump the suite count.

### `#24-harness-faultgap` — no harness driver can exercise `request_mode_recovery` (filed 2026-09-07)
- [ ] ✅ VERIFIED: `handles_battle_faults` appears **ZERO times** in `tools/story-dev/story_harness.py`,
  so `request_mode_recovery` (`modules/battle_fault.py`) returns False for every driver and the caller
  raises — dropping to Manual **by design**. ⇒ every fix that routes through that channel (`KI-47`'s
  watchdog, the `KI-34` faint-chooser give-up, `KI-96`'s new bound) is **UNPROVEN BY DRIVING**, and a
  Manual drop in a harness log proves nothing about recovery — it is easily misread as proving it
  BROKEN. ⭐ `--driver storyresume` (added 2026-09-07) inherits `handles_battle_faults = True` from
  `StoryMode` and is the first driver that CAN test it. **Next:** drive a fault through it and show
  the mode consumes it (`take_pending_fault`) and derails recoverably instead of stopping.

### `#24-mossdeep-strandfixture` — the strand fix's RESCUE half has no fixture (filed 2026-09-07)
- [ ] `#24-mossdeepstrand`'s SAFE half is driven (Segment 18's `else` ran and `leave_the_gym()`
  no-oped off the gym map). Its RESCUE half needs a save standing on **MOSSDEEP_CITY_GYM (23,8) with
  BADGE07 SET**, and `at_mossdeep_leaders.ss1` was captured BEFORE the fight, so the badge is unset.
  **Build:** win the fight from `at_mossdeep_leaders.ss1` and capture immediately after the badge
  flag sets, before leaving the platform — that is precisely the state production reaches and the one
  no fixture covers. ⚠ The batch shows this fight is lost often (`#24-tateliza-attrition`), so the
  capture may need several attempts.

### `#24-rotatelead-precondition` — the RotateLead arm presses blind; the move path does not (filed 2026-09-07)
- [ ] ✅ VERIFIED contrast. `battle_action_use_move` presses **only** while
  `get_battle_controller_callback(battler)` is an input-accepting callback and stops the instant it
  is not (`battle_action_selection.py:976, 987-1000`) — so a refusal ENDS the loop. The
  `TurnAction.RotateLead` arm computes its aim pre-menu, scrolls blind, presses A blind, then mashes
  on `while get_game_state() == GameState.PARTY_MENU` — **which is true both while the menu waits for
  input AND while it prints a refusal at you.** `scroll_to_battle_action` likewise only compares
  `gActionSelectionCursor`; it never checks the action menu is live.
  ⇒ the loop cannot tell "not yet accepted" from "actively refused", which is why `KI-96` could spin.
  **Fix shape (independent of KI-96's cause):** gate the presses on the controller callback the way
  the move path does, and treat `gPartyMenuUseExitCallback` — set TRUE only on success
  (`party_menu.c:5852`) and read by `WaitForMonSelection` — as the accept signal, rather than "did
  the menu close". ⚠ MEASURE FIRST: `[KI96-WHY]` will say whether the refusal is per-slot or a
  trapped-mode refusal that no aim can satisfy.

### 🔶 `#24-truckleak` — MIXED: the FIX is in (sandbox), its ACCEPTANCE is not — a HELD BUTTON leaked across the reset boundary (filed + fixed 2026-09-07)
- [x] ✅ **ROOT-CAUSED AND FIXED.** `_held_inputs` is Python-side wrapper state (`libmgba.py:157`);
  `reset()` (`:198-199`) never clears it and it is re-OR'd every frame (`:581`). A run killed
  mid-walk by the frame budget leaked `Up`, which then beat the truck loop's `Right` forever.
  **Separation is total:** 867 dumps `held_buttons=[]` → truck exit in ~67 frames; 719 dumps
  `['B','Up']` → 858 failures, ZERO escapes. Cost: lane L03 lost **146 runs**.
  **Fix:** `reset_held_buttons()` before `context.emulator.reset()` in `StoryDebugResetMode.run`,
  printing the released mask. ⛔ Do NOT clear holds per-frame — navigation depends on them; the
  inverse failure is the batch filling with `Could not reach …` derails.
- [ ] ⚠ **`#24-truckleak-accept` — THE RESIDUAL, TRACKED ON ITS OWN SLUG.** The fix above is
  UNDRIVEN, and its acceptance MUST be **fault-armed**: a normal run holds nothing, so an
  unarmed run proves nothing at all. Hold `Up`+`B` deliberately at a run boundary, then require
  BOTH the `DEBUG-RESET: released leaked held inputs (0x00c0)` line (proving the arm was real
  AND the fix acted) and a truck exit (`INSIDE OF TRUCK(25,40) -> LITTLEROOT TOWN`) within 300
  frames. ⛔ Do not close `#24-truckleak` until this runs.

### ✅ `#24-lane-respawn-build` — a respawned lane loads the ON-DISK build (filed + fixed 2026-09-07)
- [x] ✅ **FIXED AND GATED — after shipping DEAD once.** `Lane.build_commits` records
  `git_commit()` at EVERY spawn, and `lane_summary()` (extracted for exactly this reason)
  carries it into the report. ⛔ The FIRST version recorded it on the Lane and never copied
  it into the summary dict — a mixed batch would have printed `(not recorded)` — and SEVEN
  green checks missed it because each called the reporting function on a HAND-TYPED dict.
  The gate now drives the REAL path (a real `Lane` through the real assembly), separates
  UNVERIFIED (a git hiccup) from MIXED, and is **fault-tested against the actual defect**:
  deleting the wiring line turns 11 checks red and exits 1; restoring it returns ALL PASS.
  ⭐ Detection does NOT replace the rule — it makes it auditable.
- [x] ⚠ `x4_headless.py` respawns a dead lane, and the new process imports whatever is on disk **at
  that moment**. ⇒ promoting mid-batch can put **two builds inside one batch**, not merely stale the
  MANIFEST — a finish rate whose build is ambiguous is not a measurement. This is the concrete
  mechanism behind the "never promote while a batch runs" rule. **Options:** snapshot the build per
  batch, or record each lane's load-time commit in the MANIFEST so a mixed batch is at least
  DETECTABLE. ⛔ Prefer detectable over forbidden — a rule nobody can verify is prose.

### 🔶 `#24-pcpingpong` — MIXED: the FIX is in (sandbox), its DRIVE is not — the heal deposited a mon then withdrew the SAME mon (filed + fixed 2026-09-07)
- [x] ✅ **FIXED + GATED + FAULT-TESTED.** `withdraw_precedence()` (pure, testable) defers the
  counter-withdraw when the visit was entered to FREE a seat. MEASURED 135/135 failures had a
  withdraw, 9/9 successes did not, and the withdrawn mon was **the same mon just deposited 135/135**.
  ⛔ Adds NO deposit — it removes an UNDO — so it stays inside the 2026-08-05/08-06 rulings
  (`POKEBOT_PC_ROTATION` still 0; catch policy and party cap untouched).
  Gate: `repro_heal_piggyback_reporting.py` (25 checks, all four branches incl. **the ordinary heal
  that must not move**); removing the fix turns it red.
- [ ] ⚠ **`#24-pcpingpong-accept` — THE DRIVE IS OWED.** 144 samples of perfect separation is a
  natural CONTRAST, not an executed A/B. Run both arms on a fixture that reaches HM03 with a full,
  Surf-incapable party carrying a spent counter. POSITIVE CONTROLS (all must APPEAR or the run never
  reached the code): `freeing ONE slot`, `depositing ONE mon to free a slot: <name>`, and
  `catching <sp> — it can learn the HM we need!`. PASS = `freed a slot (6 -> 5)` + the `DEFERRED`
  line, and NO `withdrawing <same name>` between them — **that identity is the discriminator**.
  FAULT ARM (`POKEBOT_PCPINGPONG_FAULT=1`) must reproduce the ping-pong.

### `#24-counterpids-never-retired` — a hunted counter is re-collected FOREVER (filed 2026-09-07)
- [ ] ✅ VERIFIED: `_hunted_counter_pids` has exactly two mutations — `story_mode.py:1327` (init) and
  `:1876` (`.add`). No `.clear`/`.discard`/`.remove` anywhere in either tree. ⇒ once a counter is
  registered it is withdrawn at EVERY subsequent heal, long after its boss is dead (L03 prints
  `BADGE: Balance Badge (Norman…)` on the line before the ping-pong). `#24-pcpingpong` stops it
  refilling a seat that was just emptied, but does NOT answer *when does an element leave this set?*
  ⚠ Likely retirement point: the boss it was hunted for is beaten. ⛔ MEASURE FIRST — a counter kept
  deliberately for a LATER boss would be lost by a naive retirement.

### ✅ `#24-hm07teach` — **CLOSED 2026-09-08, DRIVEN AT SCALE.** ⛔ DO NOT REDO.
- [x] Production never taught Waterfall, so §Ch23's preflight killed every 8-badge run in project
  history (six across 37 batches, all six there). `ensure_waterfall_learner()` + Segment 22b fixed
  it. **MEASURED: the §Ch23 Waterfall preflight went 11 of 53 → 0 of 49** (batch `20260907-203713`
  vs `20260907-113851`, equal wall time). Runs now die 16x deeper, in the TRAINING leg — see
  `#24-ch23training`. Full detail: `07-CHANGELOG.md` 2026-09-07 and 2026-09-08.

### ✅ `#24-hm07funnel` — **CLOSED 2026-09-08, DRIVEN AT SCALE.** ⛔ DO NOT REDO.
- [x] Every HM funnelled onto one mon because Waterfall's and Dive's species pools are strict
  SUBSETS of Surf's (74 and 76 of 101, ZERO Surf-incapable) — forced by the learnset DATA, not by
  ranking. `pick_land_hm_slot()` (PURE) + `land_hm_learner_slot()` prefer a non-carrier at the two
  LAND-HM sites only; `hm_learner_slot` untouched so Surf and Dive keep the water mon.
  **MEASURED: Surf + Dive party-full went 7 of 53 → 0 of 49**, with 18 runs reaching Victory Road,
  so both teach points were passed — elimination, not avoidance. Detail: `07-CHANGELOG.md`.

### `#24-ch23preflight-gap` — the §Ch23 preflight omits Strength and Rock Smash (filed 2026-09-07)
- [ ] `assert_ch23_preflight` checks only `("Surf", "Dive", "Waterfall")`, but `chapters.py:265-274`
  records that Victory Road B1F needs **Strength AND Rock Smash**: a 2x2 boulder/rock interlock that
  opens only with BOTH (23 tiles reachable with neither, 66 with Strength alone, 23 with Rock Smash
  alone, 298 + the B2F warp with both). ⇒ a party missing either reaches the chapter and fails
  mid-cave instead of at a named preflight. ⚠ Deliberately NOT bundled with `#24-hm07funnel`: adding
  requirements makes the preflight STRICTER and could turn currently-passing driven fixtures red.
  Check the §Ch23 fixtures first, then add both to `field_move_carriers()` and the preflight.

### 🔶 `#24-whiteoutloop` — MIXED: the COUNTER is fixed and gated; the bot still cannot WIN the fights (filed + half-fixed 2026-09-07)
- [x] ✅ **THE COUNTER — ROOT-CAUSED, FIXED, GATED (sandbox).** `recoveries` had **no reset
  site anywhere** while its message said *"in a row"*: a LIFETIME loss quota. All 14 killed
  runs reached exactly #41 after whiteouts spread over a **median of 13 different towns**,
  while winning **86-96%** of their battles (one won 866 of 907 with an L51 lead). ⇒ a fuse
  on run LENGTH — kill rate 0% under 1.5M frames, 62% above 3.5M, and `MAX_FRAMES_PER_RUN`
  (5,000,000) was never reached by ANY of the 61 runs. ⛔⛔ **FALSE AS OF 2026-09-09 — MEASURED 6 FIRINGS.** `grep -rho "per-run frame budget exhausted" x4-runs/*/L0*/stdout.txt | wc -l` = **6** (overshoot ≤10,149 frames, 0.2%). ‼ AND THE BIGGER POINT: `MAX_FRAMES_PER_RUN` lives at `story_mode.py:4329`, inside **`StoryEndlessResetMode` — the BATCH HARNESS**. Production `StoryMode` has **no total-frame budget at all**, so in a real run the per-call `MAX_TRAINING_FRAMES` ceiling is the ONLY pre-emptive bound in existence. ⛔ Do not argue from run-budget headroom: at the 16 Ch23 refusals the median run had already burned 86% of it (median spare **707,123** frames against a mean training bill of **1,083,258** solo / **2,164,009** with the 2-way split). FIX: `whiteout_budget()` (PURE) keys
  it to CONSECUTIVE whiteouts at ONE location. GATE #44 `probe_whiteout_budget.py` replays
  the 14 real sequences: **0 of 14 still killed**, a stuck run and a blind run both STILL
  stopped at #41, and three fault arms fire. ⛔ DO NOT rewrite it to use `_progress_sig()` —
  that contains `total_exp`, which grows on the walk back, so it would reset every time and
  DELETE the guard (FAULT ARM 3 fails exactly that).
- [ ] ⛔ **THE OTHER HALF IS OPEN — see `#24-regimeb-noescalation`.** The counter fix stops
  runs being killed for playing long; it does NOT make the bot win. ⚠ EXPECT the failure to
  MOVE, not vanish: runs that used to die at #41 will now run on to some later blocker.
- [x] ⭐ ORIGINAL QUESTIONS, ANSWERED (kept as history): `Story: too many whiteout recoveries in a row —
  stopping so I don't loop forever. Check the team/route.` — 14 of 53 ended runs in the full 8-hour
  batch `20260907-113851` (26%), up from 2 of 17 before, because runs now survive long enough to
  reach it. **Never investigated.**
- [ ] ⭐ FIRST QUESTIONS (do not guess): WHERE do the whiteouts happen — one boss, or scattered? Is
  the cap itself reasonable, or does it fire on a run that would have recovered? Is this the same
  "right types, too weak" shape as `#24-tateliza-attrition`, which the counter-guard cannot see
  because it grades on TYPE coverage only? ⚠ Two of the deepest runs in the PREVIOUS batch died at
  Tate & Liza with 24 and 11 losses, so start by checking whether these 14 share a location.

### `#24-regimeb-noescalation` — the back half of the game has NO loss-adaptation at all (filed 2026-09-07)
- [ ] ⛔ **VERIFIED IN OUR OWN TREE, not taken from an agent.** There are **8** `*_fight` configs and
  **8** `_prepare_for_fight` call sites; the last is `winona_fight` (badge 6, `story_mode.py:3729`).
  Every chapter after it is dispatched as a bare `if not _done(...): yield from chapter()`. All six
  late chapter modules — `mossdeep_gym`, `sootopolis_gym`, `victory_road`, `pokemon_league`,
  `seafloor_cavern`, `space_center` — contain **ZERO** uses of `_prepare_for_fight`, `_defeat_counts`
  or `_boss_plan_is_hopeless`.
- [ ] ⇒ **From badge 7 on, N whiteouts is N IDENTICAL losses.** No level escalation, no plateau
  detector, no counter-hunt, no second wind, no honest stop — the machinery that badges 1-6 get.
  Survival mode cannot help: it is gated on `encounter is not None`, i.e. WILD battles only, and a
  gym leader is a trainer battle by construction.
- [ ] ⚠ **DO NOT SCOPE FROM THE TERMINAL-LOCATION STATISTIC** — it is a sample of size one per run
  (`08-MISTAKES.md` 2026-09-07). Plot the whole distribution of loss sites first.
- [x] ⛔⛔ **THE 'CHEAPEST FIRST SLICE' BELOW IS REFUTED 2026-09-08 — DO NOT BUILD IT.** Arming the
  Mossdeep respawn would make retries CHEAPER; it cannot make them SUCCEED, and cheapness is not what
  kills these runs. **(1) The runs die on a COUNT, not on time** — `whiteout_budget(cap=40)` — and
  this file already records that `MAX_FRAMES_PER_RUN` (5,000,000) **was never reached by ANY of the
  61 runs** ⛔⛔ **FALSE AS OF 2026-09-09 — MEASURED 6 FIRINGS.** `grep -rho "per-run frame budget exhausted" x4-runs/*/L0*/stdout.txt | wc -l` = **6** (overshoot ≤10,149 frames, 0.2%). ‼ AND THE BIGGER POINT: `MAX_FRAMES_PER_RUN` lives at `story_mode.py:4329`, inside **`StoryEndlessResetMode` — the BATCH HARNESS**. Production `StoryMode` has **no total-frame budget at all**, so in a real run the per-call `MAX_TRAINING_FRAMES` ceiling is the ONLY pre-emptive bound in existence. ⛔ Do not argue from run-budget headroom: at the 16 Ch23 refusals the median run had already burned 86% of it (median spare **707,123** frames against a mean training bill of **1,083,258** solo / **2,164,009** with the 2-way split).. Saved frames buy nothing. **(2) From badge 7 on, attempt N+1 is BYTE-IDENTICAL to
  attempt N** (this very item's own finding), so a cheaper loop is the same loop.
  ⛔⛔ **(3) IT IS ACTIVELY HARMFUL:** `whiteout_budget`'s `key` **is** `get_last_heal_location()`,
  and the budget RESETS to 1 when the key changes ⇒ re-arming Lilycove→Mossdeep grants **one free
  reset, i.e. up to 40 EXTRA Tate & Liza losses** before the honest stop. The fix would make runs die
  SLOWER, not better.
  ⭐ **Also: the mechanic in the slice below is wrong.** `setrespawn` lives in the Poké Center's
  `MAP_SCRIPT_ON_TRANSITION` (`data/maps/MossdeepCity_PokemonCenter_1F/scripts.inc`), so **walking in
  arms it — healing is irrelevant**; `data/scripts/pkmn_center_nurse.inc` contains no `setrespawn`.
  And `heal_in_pokemon_center` would be the wrong tool anyway: it runs the chapter's hardest journey
  on the WEAKER navigator (`navigate_to_anywhere`, `avoid_scripted_events=True`, no retry) where
  `_navigate_riding_out` retries 10x with obstacle clearing.
  ⭐⭐ **AND THE MEASUREMENT BELOW IS A PROXY, NOT A READING** — its largest bucket (ROUTE 124, 58%)
  is IMPOSSIBLE: `src/data/heal_locations.json` contains **zero routes**. ⇒ **read the real value:**
  `get_last_heal_location()` (`modules/save_data.py:14`, SaveBlock1 +0x1C), already wrapped as
  `respawn_reading()` / `respawn_is_armed()` (`victory_road.py:666`, `:680`) and used at 8 sites in
  §Ch23. ‼ The item below carried the hedge *"the exact split is proxy-dependent"*; my proposal
  deleted it. **The hedge was the honest part.**
- [x] ✅ **THE MONEY CONTRADICTION THIS ITEM RECORDED AS OPEN IS NOW SETTLED, FROM THE DECOMP.**
  `src/overworld.c:358` — `DoWhiteOut()` does `SetMoney(&money, GetMoney(&money) / 2)`. `MoneyLoss`
  has **zero** hits in `pret/pokeemerald`; the `sWhiteOutMoneyLossMultipliers` table is FireRed's
  (`pokefirered/src/overworld.c:227`). ⇒ **`victory_road.py:446` was RIGHT; `story_mode.py`'s
  boss-training comment was WRONG** and has been corrected in sandbox. ⚠ The CONSEQUENCE is filed
  separately as `#24-bosstrainingeconomics` — the fact is settled, the decision is not.
- [ ] ⭐ CHEAPEST FIRST SLICE, and it is not the escalation: **90% of Mossdeep Gym whiteouts respawn
  in LILYCOVE** (148 vs 16) because the Mossdeep Poké Center is never registered before the gym —
  the only two `heal_in_pokemon_center(PokemonCenter.MossdeepCity)` calls are in `seafloor_cavern.py`
  and `space_center.py`, both chapters that run AFTER it. Cost: a median ~8 min per retry.
  ✅ **VERIFIED MYSELF 2026-09-07** (was agent-reported): `heal_in_pokemon_center(PokemonCenter.MossdeepCity)` has EXACTLY TWO call sites — `seafloor_cavern.py:884` and
  `space_center.py:185` — and both chapters run AFTER the gym. And of **139** whiteouts that
  STARTED on a Mossdeep map, only **13** respawn at Mossdeep: ~91% land elsewhere (my split
  is ROUTE 124 81 / LILYCOVE 45, because ROUTE 124 is the Lilycove→Mossdeep surf corridor and
  a 'first map after recovery' proxy catches transit; the agent read 148/16. ⇒ **the exact
  split is proxy-dependent, the ~90% direction is not.**)
- [ ] ⚠ ALSO REPORTED, UNVERIFIED: `story_mode.py:1995` justifies boss-training mode with *"whiteout
  money loss is level x badge-payout — cheap"*, which is the FRLG model; our own
  `victory_road.py:446` records that Emerald's `DoWhiteOut` does `SetMoney(money / 2)`.
  ✅ **THE INTERNAL CONTRADICTION IS VERIFIED 2026-09-07** — both lines exist as quoted, and
  they cannot both be right. ⛔ **WHAT IS *NOT* VERIFIED IS WHICH ONE THE GAME AGREES WITH**:
  that needs the decomp, not our own two comments. Settle it there BEFORE re-deriving the
  economics of deliberately farming whiteouts (`story_mode.py:1996` engages boss-training
  ~98% of the time on that premise, and each attempt spends a unit of the whiteout budget).


### `#24-bosstrainingeconomics` — boss-training re-loses on purpose, and EVERY loss halves all money (filed 2026-09-08)
- [ ] ⛔ **THE PREMISE WAS FALSE AND IS NOW CORRECTED IN CODE.** `story_mode.py`'s boss-training
  comment justified deliberately re-attempting a boss as a training vehicle with *"whiteout money
  loss is level x badge-payout — cheap"*. That is **FireRed's** model. Emerald halves ALL money on
  every whiteout (`src/overworld.c:358`, decomp-read 2026-09-08). The comment is fixed; the STRATEGY
  is untouched.
- [ ] ⭐ **MEASURED EXPOSURE:** the *"boss-training mode — local wilds …"* line fires **1,477 times**
  across `20260907-203713` + `20260907-113851` (16 lane files, total occurrences). Each engagement is
  a deliberate loss, i.e. a halving.
- [ ] ⛔⛔ **DO NOT ACT ON THIS YET — THE COST IS UNMEASURED AND THE INSTRUMENT DOES NOT EXIST.**
  Money is not written to any log, and the natural proxy is unusable: `provision_poke_balls`'s
  *"too low on money to restock"* goes to `context.message` (a UI field), **not** `console.print`, so
  it never reaches `stdout.txt`. A zero count there means NOT LOGGED, not NEVER HAPPENED.
  ⇒ **FIRST DELIVERABLE IS AN INSTRUMENT, NOT A FIX**: log money at run start, at each whiteout, and
  at each mart visit. Only then is "boss-training is too expensive" a claim rather than an inference.
- [ ] ⚠ **THE ONE HARD DATA POINT SO FAR:** 5 runs derailed on *"Cannot hunt a Surf learner: no Poké
  Balls and no money to buy any."* Real, but 5 — nowhere near enough to indict a strategy that fires
  1,477 times. ⛔ Do not scope this from that number.
- [ ] ⭐ **AND THE COUNTER-ARGUMENT, so it is not re-derived:** boss-training exists because a lost
  attempt that KOs two of the boss's mons pays ~1,200 XP against ~145 XP for a local wild, and Gen 3
  **does** keep mid-battle XP through a whiteout (that half of the comment is true). The strategy may
  well still be correct at half-money. **Price it; do not assume either way.**

### `#24-ch23training` — TOP BLOCKER, ROOT-CAUSED 2026-09-08 (16 of 49, 32.7%) — ⛔ the guard is the MESSENGER
- [x] ✅ **ROOT CAUSE VERIFIED.** `victory_road.py:1937` refuses when ANY single under-target battler
  costs more than `MAX_TRAINING_FRAMES = 250_000` to reach `TRAIN_TARGET = 47` on `WILD_MAX = 40`.
  ⚠ **"alone" does NOT mean the mon is alone in the party** (all 16 failures have 2+ members) — it
  means *that one mon by itself*. Inverted levels: **Marill ≈L13, Slugma L17, Mightyena ≈L20,
  Shedinja ≈L23**, against a leg calibrated on a curated party with an **L40 floor**.
- [x] ⭐ **THE BOT CREATES THEM AND THEN PINS THEM.** `ensure_hm_learner` CATCHES a wild mon at wild
  level to carry an HM; HMs cannot be forgotten in Gen 3; `team_policy.py:147-149` exempts a **sole
  HM carrier** from deposit BEFORE any level test. `battler_identities` (`victory_road.py:1770`)
  then admits it — `BENCH_SPECIES` is only `("Zigzagoon","Linoone","Castform")`, 3 hardcoded names
  against 6 observed species. ‼ Already measured in `team_policy.py:8-16`: *"35% of badge moments
  carried at least one mon 15+ levels below the team max"*. My recount: **86.9%/78.9% of runs.**
- [x] ⛔⛔ **SIX NOW — "ROUTE THE MULE TO A LEVEL-MATCHED AREA" IS KILLED ON ARITHMETIC (2026-09-09).**
  Adversarial pass, five angles. **No ground in Emerald can clear the ceiling from L13.** The per-call
  budget is `250,000 / FRAMES_PER_WILD_BATTLE(1433)` = **174 battles**; L13→L47 needs 81,301 exp, i.e.
  **467 xp/battle, i.e. a wild level of ≥65**. The highest wild level the project's own encounter cache holds is **50**
  (⚠ *this said 44 — an undercount; corrected 2026-09-09 by a reviewer*). **Either way it is far short of 65**, so the conclusion is untouched.
  ‼ **AND A SEPARATE DEFECT SURFACED WHILE CHECKING IT — FILED, NOT FIXED:** those high entries carry **FRLG-only map names** (*"Artisan Cave"*, *"Desert Underpass"*) inside a **BPEE0 Emerald** cache, which points at a map-name lookup mismatch for high bank/map indices (`modules/pokemon.py`'s shared gen3 name list). ⇒ any analysis that trusts `map_name` from `cache/encounter_index_BPEE0.json` may be reading a wrong label. Not this item's bug; do not fix it here. Relocating moves the number the WRONG way — VR1F 406,972 → ROUTE121 580,365 →
  ROUTE117 **1,160,730**, all against an unchanged 250,000.
  ‼ **AND THE PREMISE WAS WRONG:** `best_training_area(13)` returns **ROUTE117 (L13-14)**, never a
  L25-28 area — `if team_level < lo - 1: continue` rejects every higher band. The picker is
  level-matched by construction, so it can only ever pick something POORER than Victory Road.
- [x] ⛔⛔ **THE ESTIMATOR IGNORES THE EXP SPLIT — ‼ ALREADY FILED 2026-09-08 (see the "UNDERSTATES TRAINEE COST ~2x" bullet above); WHAT IS NEW IS THE CONSEQUENCE NOBODY APPLIED.** That bullet ends *"any future costing of a catch-time top-up must double the estimate"* — and this item's own FIX DIRECTION below never did. ⇒ do not re-file this fact; the value here is the arithmetic it implies:
  `training_areas.estimate_frames_to_level` computes `xp_per_battle = CAL * wild_level / 7` with **no
  division by participants** (verified in source), i.e. it models a SOLO fight — while its own caller
  `train_team` sets `set_swap_train(True)` (`early_game.py:2026`), putting TWO mons in the battle and
  halving the share. ⇒ **every training cost estimate is up to 2x optimistic about the path that
  calls it.**
  ⭐⭐ **CONSEQUENCE FOR THIS ITEM: THE "BAR IS L35" MAY BE WRONG.** Recomputed with a model that
  reproduces all five published figures EXACTLY (L13=406,972 / L20=384,044 / L26=345,353 /
  L30=308,095 / L35=243,610), then halved for two participants:
  ```
  arrival   SOLO (modelled)   2-WAY SPLIT      ceiling 250,000
    L35           243,610         487,220      REFUSE
    L40           160,496         319,559      REFUSE
    L42           118,939         237,878      PASS
  ```
  ⇒ L35 is the SOLO bar; the real bar looks like **L42**, and this item's planned *"catch at L26 AND
  train the remainder to ~L39"* would **still refuse**.
  ⚠ **NOT PROVEN, AND THE LIMIT IS HONEST:** the split is 2 only when swap-training actually fires; it
  does not fire when no capable finisher exists, and then the solo model is right. The true cost lies
  BETWEEN the two columns.
- [ ] ⛔ **THE DECIDING MEASUREMENT IS NOT AVAILABLE FROM EXISTING LOGS — IT NEEDS INSTRUMENTATION.**
  I looked: **0** logs in `sandbox-pokebot/profiles` + `tools/story-dev/x4-runs` contain BOTH
  `-> RotateLead` telemetry AND an exp readout. Production rotation logs carry `party=None` and no exp
  field at all. ⇒ **NEXT DELIVERABLE IS ONE LOG LINE, NOT AN ANALYSIS**: record the trainee's
  `total_exp` BY PID before and after each wild battle in a run where swap-training fires, and divide.
  That single number decides whether this item targets **L35 or L42** — i.e. whether its next build
  works or repeats this failure one level up.
- [ ] ⚠ **CARRY-FORWARD HAZARD FOR WHOEVER TOUCHES §Ch23's TRAINING:** `WILD_MAX = 40`
  (`victory_road.py`) and `grass=TRAIN_SPOT_1F` are **independent hardcodes**. A relocation that edits
  one and not the other prices the grind at L40 while grinding at L14 — that is `KI-28`'s 19.9M-frame
  livelock with its only guard blinded. Also `_MAX_TRAINING_TRAVEL_LEGS` (4) is never referenced by
  `victory_road.py` or `early_game.py`, so a relocation bypasses the travel cap silently.
- [ ] ⛔ **FIVE FIXES ARE MEASURED WRONG — DO NOT PROPOSE ANY OF THEM:** benching low mons,
  stepping the target, raising the ceiling, training elsewhere, relaxing the estimator. Each was
  killed by evidence, not opinion; the reasons are in `07-CHANGELOG.md` 2026-09-07/08.
- [x] ⛔⛔ **SECOND, INDEPENDENT REASON STEPPING COULD NEVER WORK (review, not drive):**
  `team_is_ready(target)`'s LEVEL loop uses `target` but its **CRUNCH loop does not** — it tests
  `mon.level < CRUNCH_LEVEL`(=47) unconditionally, and it is the terminal gate. ⇒ any sub-target < 47
  RAISES whenever a sub-47 Mightyena lacks Crunch, which the fixture has ⇒ **it would have broken the
  CONTROL.** ⭐ **STANDING TRAP: `team_is_ready` IS NOT SAFELY CALLABLE WITH A SUB-TARGET.**
- [x] ⛔⛔ **THE BENCH FIX IS REFUTED — DO NOT RE-PROPOSE IT.** An adversarial review returned
  UNSAFE: on the chapter's OWN fixture (`Sceptile L51 / Swellow L42 / Wailmer L40 / Mightyena L44`)
  a `party_max - 8` line benches **Wailmer and Swellow — two of the four mons the shipped run
  trained to L47** — and Wailmer is the sole carrier of Dive AND Waterfall (`victory_road.py:760`).
  It also turns a LOUD refusal SILENT (a benched Poochyena never evolves, so the Crunch guard keyed
  on `species.name == "Mightyena"` never fires ⇒ Phoebe's all-Ghost team with no Dark move, and
  there is no Dark TM in Emerald), and an empty battler set returns `(True, [])` ⇒ a broken run ✅✅ **CLOSED 2026-09-08 — FIXED AND GATED BEFORE THE PREDICATE IS TOUCHED.** `team_is_ready` now refuses loudly on an empty battler set (`victory_road.py`, +24/−1), locked by **gate #48 `probe_empty_battler_guard.py`** (4 arms; fault-tested — disable the guard and it exits 1, restore byte-identical and it exits 0). ⛔ This does NOT advance the item: the ROLE predicate is still unbuilt. It removes the trap that would have made a bad predicate look like a SUCCESS. Rationale + raw evidence: `06-DECISIONS-LOG.md` 2026-09-08.
  grades PASS. `team_policy.py:42-59` had ALREADY measured this predicate over 363 parties: *"59%
  would be left with FEWER THAN 3 mons"* — which is why that module CAPS it and my proposal did not.
  Full detail: `07-CHANGELOG.md` 2026-09-08.
- [x] ⛔⛔ **STEPPING IS ALSO REFUTED — BUILT, DRIVEN, REVERTED 2026-09-08.** MEASURED: **69 battles,
  Marill lead at 0/43 HP, STILL L13.** A L13 mon cannot survive VICTORY_ROAD_1F's L36-40 wilds and a
  fainted mon earns nothing ⇒ it can never level there **at any step size**.
- [x] ⭐⭐ **⇒ THE GUARD IS CORRECT, FOR A REASON ITS MESSAGE DOES NOT STATE.** It says "too
  expensive"; the truth is "not survivable here", and the two coincide BY CONSTRUCTION — a mon over
  the 250k ceiling is ~20+ levels under the wild band. **The ceiling is a PROXY for survivability.** ⛔⛔ **WITHDRAWN 2026-09-09 — THIS RESTED ON A FABRICATED MEASUREMENT.** The mule was NOT one-shot: measured, it started **66 of 72** battles at full 43/43 and fought 2.3 turns each. It gained nothing because the DRIVER never installed swap-training (`Ch23TrainMode` returns `StoryItemBattleStrategy`; 232 turn decisions, 0 RotateLead), not because it could not survive. ⇒ **the ceiling is a COST test, not a survivability proxy.** See `07-CHANGELOG.md` 2026-09-09.
- [ ] ⇒ **BOTH LEG-LOCAL FIXES ARE DEAD; THE DEFECT IS UPSTREAM — see `#24-lowlevelmules`.** The bot
  catches HM mules and counters at wild level and never trains them; by Victory Road no local remedy
  exists.
- [ ] ⭐ **AND THE PREMISE IS SMALLER THAN IT LOOKS:** at the measured **1032 frames/sec**, Marill's
  406,972 frames is **~6.6 minutes**; all six mules ≈ **44 minutes**. The refusal is rejecting a
  sub-hour grind — a per-call-ceiling artefact, not an economics fact.
- [x] ✅ **THE DISCRIMINATOR EXISTS — ⛔ DO NOT REBUILD IT.** `--inject-hmmule` adds an L13 Marill
  to an otherwise-ready party; with `POKEBOT_CH23_ESTIMATE_ONLY=1 --driver ch23train` the arms differ
  in seconds (CONTROL worst 217,816 passes · ARM A worst 406,972 refuses, shared mons identical).
  406,972 is the EXACT production figure. Evidence: `acceptance-2026-09-07/EVIDENCE.md`.
- [x] ⭐ **ACCEPTANCE CRITERIA (kept — they are what KILLED the step fix):** ARM A must PASS · the
  CONTROL must be UNCHANGED · a genuinely impossible case must STILL refuse. Stepping failed the
  first two; ⚠ `ESTIMATE_ONLY` returns BEFORE the raise, so it cannot grade a real run.
- [ ] ⛔⛔ **THE TRAP IN THE CODE YOU WILL MIRROR.** `Ch24Grind`'s step loop
  (`story_harness.py:15236-15246`) is the reference implementation — `sub = min(target, low + STEP)`,
  `MAX_STEPS/MAX_RETRIES = 24/2`, and a **"refuse to spin"** break when a step moves nobody. **Copy
  those.** ⛔ **DO NOT copy its `except Exception as error:`** — that is legitimate in a HARNESS
  driver (a refusal IS the reading) but in the CHAPTER RUNNER it would swallow `StoryAbort` and
  re-open the abort-swallow debt that gate #27 ratchets at baseline 23. Production must
  `reraise_if_aborting(error)` first, or not catch at all.
- [ ] ⚠ **AND THE CALL SITE IS THE CHANGE, NOT THE FUNCTION.** `train_for_victory_road` ALREADY takes
  `target=` (`victory_road.py:1872`), so stepping is a CALLER concern. The site is the chapter runner
  at `victory_road.py:3290`. ⛔ Nothing about `battler_identities`, `team_is_ready` or
  `MAX_TRAINING_FRAMES` needs to change — and Decision 3 explicitly rejected touching the constant.
- [ ] ⚠ **NOT BUILT DELIBERATELY — THERE IS NO DISCRIMINATOR YET.** No fixture reproduces a low-level
  mule party, `--inject-*` is preset-only, and `battler_identities` feeds BOTH `team_is_ready` and
  the estimator (a shared path). ⇒ ⭐ **STEP 1 IS THE FIXTURE, NOT THE FIX:** capture a save whose
  party holds a sole-HM-carrier 15+ levels below the max (or add a harness inject for one), and show
  the two arms DIFFER on it before changing `battler_identities`.

### `#24-marillskew` — ⚠ my own `#24-hm07funnel` fix appears to cost 2.7x more Marill (filed 2026-09-08)
- [ ] **MEASURED over distinct RUNS (not log-line mentions):** Marill 4 of 61 (6.6%) → **10 of 57
  (17.5%)**; every other species flat. Marill is the refused mon in **9 of 16** `#24-ch23training`
  failures. ⭐ The innocent explanation is REFUTED: at the SAME depth band (party max L50+, 18 runs
  each) it is still **3 → 8**. ⚠ n=18/cell — SUGGESTIVE, not proven (p ~ 0.1).
- [ ] ⛔ The DIRECT mechanism is also refuted: `pick_land_hm_slot` excludes Waterfall-capable species
  and Marill learns Waterfall, so it can never SELECT one. ⇒ the path is INDIRECT. Leading
  hypothesis, UNVERIFIED: spreading land HMs across more mons creates more **sole-HM-carrier
  exemptions**, and each such mon becomes permanently undepositable.
- [ ] ⇒ **NET: the funnel fix STAYS** (preflight 11→0, Surf/Dive 7→0). This is a cost to track, not a
  reason to revert. Settle it by correlating `teaching Rock Smash/Strength to <X>` against the
  refused PID in `x4-runs/20260907-203713/L0*/debug-logs/`.

### `#24-cutscenestall` — NEW in the post-fix batch: 4 of 49 runs (8.2%) (filed 2026-09-08)
- [ ] `Cutscene did not end after N frames (controllable=False, script_active=True).` **Zero
  occurrences in the BEFORE batch**, so this is genuinely new rather than a share-of-a-different-mix
  artefact. ⚠ Also new: `per-run frame budget exhausted` (2 of 49). ⛔ Both are UNINVESTIGATED —
  check whether either traces to this session's changes before assuming they are pre-existing.
### `#24-tier2audit-residue` — 10 doc defects a cold-start audit found and I did NOT fix (filed 2026-09-08)
- [ ] ⭐ **THE SYSTEMIC CAUSE, worth more than the list:** *a status change gets written where the
  WRITER is looking and not where the READER will look.* Four instances were fixed 2026-09-08 (the
  `➡➡➡` headline, `KI-81`'s header, "live frontier is `KI-96`", `KI-97`'s header). These remain:
- [ ] **(a) THREE "ARCHIVED VERBATIM … nothing deleted" claims where ~399 lines NEVER MOVED** — `05`
  `KI-76` (~165), `KI-66` (~163), `KI-50` (~80). The archive holds copies (`28`), so this is
  DUPLICATION, not archival, and the stated R3 budget relief never happened. ⭐ This is exactly
  `archive_doc_block.py`'s **INVARIANT D** class, in history predating it. Either move them or
  retract the claim.
- [ ] **(b) `05:430-431` a KI-26 header wrapped across two `##` lines** ⇒ a PHANTOM section that
  structurally owns KI-26's body; any tool walking `##` boundaries mis-attributes it.
- [ ] **(c) `05:28-29` the file's own navigation grep is wrong for the 3rd time** — it prescribes
  `^## KI-[0-9]+` (66) and misses 10 backticked headings (`^## \`KI-`); true total ~75.
- [ ] **(d) promotion-paste residue in `KI-93` / `KI-95` / `KI-79`** — headers say PROMOTED while
  bodies still say "unpromoted / still open"; `KI-95` has a runaway parenthetical whose last rendered
  words are the opposite of its Status line. **(e)** `KI-47:890` + `KI-8:136-137` still commission a
  probe `KI-96` ANSWERED; `05:2738-2740` is a 4th live copy of the KI-96 census instruction.
  **(f)** `05:16/:22` claims everything from KI-6 on is our own code — refuted by KI-83/88/89
  ("upstream helper"). **(g)** `05:1509` MIXED heading has an unmarked bullet (`KI-60`).
  **(h)** `KI-35` header carries no status in a file whose preamble says "open problems only".
  **(i)** `KI-73`'s sub-heading asserts what the line beneath it corrects. **(j)** the preamble says
  fixed issues are removed, but the 2026-07-29 ruling retains sandbox-only fixes — ≥16 promoted
  entries are retained; the file asserts both.

### `#24-lowlevelmules` — the REAL defect behind `#24-ch23training`: caught mons are never trained (filed 2026-09-08)

- [x] ⭐⭐⭐ **ROOT CAUSE FOUND AND VERIFIED IN CODE 2026-09-08 — IT IS AN ABSORBING STATE, AND THIS
  ITEM'S TITLE UNDERSTATES IT.** `story_mode.py:2135-2137 (SANDBOX; the same logic sits at ~:2119 in custom-pokebot — a fork mixup, corrected 2026-09-10)` (`TRAIN_CATCHUP_GAP = 6`, `:1136`):
  `to_train = {i for i in battlers if party[i].level >= target - 6}`, with `target` drawn from the
  fight's own band (`:1945`). ⇒ a battler more than 6 below the band is excluded from training, so it
  gains nothing, so it is further below the NEXT band, so it is excluded again — **permanently, with
  nothing in the tree pulling it back**. `team_policy.py:11-14` had already recorded the symptom
  (*Makuhita L8 → L9 across FIVE badges*) without naming the mechanism.
  ⇒ **the HM mule is not special — it is the most FREQUENT victim of a general trap.**
- [x] ⭐⭐⭐ **AND THE BIGGER STRUCTURAL FINDING: THERE IS NO TEAM TRAINING AFTER WINONA.** Verified by
  exhaustive grep: **8** `"band"` configs and **8** `_prepare_for_fight` call sites, the last being
  `winona_fight` (`story_mode.py:3753`, `:3758`). **No band, no prep, and no `train_team` call exists
  for Tate & Liza, Juan, the E4, or §Ch16-§Ch22.** The only `train_team` callers in the tree are
  `counter_hunt.py:782` (the hunted counter only), `victory_road.py:2004` (§Ch23 itself),
  `story_mode.py:1988` (single-mon top-up), `:2240` (band prep) and `:3145` (§Ch6 rival).
  ⇒ **the party crosses ~9 chapters from Winona's L29-33 band to §Ch23's L47 requirement with NO
  training mechanism at all** — the max climbs organically to L49-59 while any laggard receives
  nothing. §Ch23 is simply the first place that requires the WHOLE team.
- [x] ⭐ **MEASURED — what §Ch23 sees** (18 runs of `20260907-203713` that reached it, using the code's
  own bench predicate): lowest battler **median L13 (L12-23)** against party max **L49-59**;
  **0 of 18** clear L35 on every battler. Lowest-battler species: **Marill 9**, Slugma 2, Abra 2,
  Shedinja 1, Ninjask 1, Mightyena 1, Kadabra 1, Poochyena 1. ⇒ Marill is exactly HALF; the rest are
  **late catches, not HM mules**, so an HM-scoped fix can address at most half the population.
- [x] ⛔⛔ **REFUTED — "acquire a Marill on Route 104 at §Ch3 so it is never a mule".** Killed by
  adversarial review on six counts, each verified in code. The two that are fatal on their own:
  (a) `pick_land_hm_slot` (`early_game.py:4416-4417`) **skips any species that can learn Waterfall**
  — Marill does, so it is **structurally ineligible for Strength/Rock Smash forever**; and
  (b) Route 104 is in **`PENDING_GRASS` with spin tile `None`** (`training_areas.py:57-58`), never
  swept, and `_hm_hunting_grounds` skips `tile is None`. Also: no ball supply at §Ch3
  (`provision_poke_balls` → `RUSTBORO_MART`, §Ch4); until it holds an HM it has **no deposit
  exemption** (`team_policy.py:147-149`) and is sorted FIRST for boxing; and on Mudkip runs the
  starter wins Surf (`hm_learner_slot` ranks by LEVEL) so the slot is a passenger.
- [x] ⛔⛔ **REFUTED — "the earlier catch-time refutation used the wrong bar".** The reasoning was that
  a fresh catch need not reach L35, only `target - 6` of the NEXT fight, after which `to_train`
  carries it. **The next fight is WINONA AND THERE IS NOTHING AFTER IT** (finding above), so the
  ceiling this mechanism can deliver is `randint(29,33)` = **L33**. Reproducing the project's own
  measured sweep from `estimate_frames_to_level` (5 of 5 exact matches at L13/L26/L30/L35) and filling
  the gap: **L33 needs 272,270 frames against the 250,000 ceiling — it STILL REFUSES, by 22,270.**
  ‼ My "rides to ~L47" was a misreading: **L47 is `TRAIN_TARGET`** (`victory_road.py:492`), the level
  §Ch23 trains *to*, not one the band curve delivers.
- [x] ⛔⛔ **THE B1F 'LEAD' IS ALSO REFUTED — I RECORDED IT AS LIVE WITHOUT CHECKING THE HISTORY FIRST.** `07-CHANGELOG.md` (2026-09-08, earlier the same day) already killed it under *"move the training somewhere better"*: **B1F is richer (959.2 vs 768.0) but its ladder is 44 wp PAST WALLY'S TRIGGER — the better ground is gated behind the fight the training is for**, and readiness must pass BEFORE Wally. ⇒ **seven refuted fixes; no cheap lead remains.**
  `victory_road.py:1942-1943`'s refusal message already says: *"train on B1F AFTER Wally (950.8
  EXP/battle vs 1F's 775.6)"* — a **1.226x** economy. At B1F rates L33 costs ~222k, which **passes**.
  ⛔ It is NOT free: it depends on (1) KI-84 being fixed for the gym-prep path, (2) the carrier being
  a Fast-curve species (Marill yes; a **Lotad** carrier is Medium-Slow and raises the bar L35 → L38),
  and (3) drawing L33 rather than the L31 expectation. ⚠ Check first whether this is the already-
  refuted *"training elsewhere"* before proposing it.
- [x] ⛔ **KI-84 FIRES ON THE GYM-PREP PATH, and this corrects an attribution.** At Winona the
  established battlers are all >= target, so `need` (`story_mode.py:2126`) collapses to the single
  mule slot, i != 0 — literally the documented-broken `train_team(slots={i})` case
  (`victory_road.py:1970-1982`). ⇒ the *Makuhita L8 → L9* evidence is the **KI-84 +1-level
  signature**, not purely the catchup gap. ⭐ The multi-slot case DOES converge while slot 0 is also
  below target (the swap keeps the member set closed) — that is the early game, not Winona.
- [x] ⛔ **THE ESTIMATOR UNDERSTATES TRAINEE COST ~2x.** `estimate_frames_to_level`
  (`training_areas.py:571-580`) models FULL XP, but `train_team` enables swap-train
  (`early_game.py:2009`) which this project's own comment calls *"half-XP swap-training"*
  (`story_mode.py:2106-2107`). Any future costing of a catch-time top-up must double the estimate.
  ‼ And `story_mode.py:2240` (band prep) has **no estimate gate at all**.
- [ ] ⛔ **UPSTREAM, AND ALREADY MEASURED — `team_policy.py:8-16`:** *"35% of badge moments carried a
  mon 15+ levels below the team max… the answer was in the party the whole time and never became
  usable."* My recount over two batches: **86.9% / 78.9% of runs** ever carried such a mon.
- [ ] ⭐ **WHY FATAL ONLY AT §Ch23:** `ensure_hm_learner` CATCHES a wild mon for an HM;
  `team_policy.py:147-149` then EXEMPTS a sole carrier from deposit (correctly — boxing the only Surf
  carrier soft-locks). Created, pinned, never trained; §Ch23 is where its level is first REQUIRED.
- [x] ⭐⭐ **THE BAR IS MEASURED: L35.** Sweep (`POKEBOT_MULE_LEVEL` 13/20/26/30/35, ESTIMATE_ONLY,
  seconds per arm): Marill needs 406,972 / 384,044 / 345,353 / 308,095 / **243,610** frames — the
  §Ch23 refusal clears only at **L35**. (Pre-registered prediction "L34-L35" HELD.)
- [x] ⛔⛔ **NEITHER LEVER ALONE REACHES IT.** Catch-time training buys ~+15 (L13→L28). The whole-game
  GRASS ceiling for a water-HM carrier is Shoal Cave L26-32 / Route 120 L25-27 — **both under L34**;
  Route 120 maps to the L26 arm at 345,353, **still refuses**. ⇒ `#24-divegroundroute120` alone does
  NOT clear §Ch23 (it is still a real win: 236 battles vs 588, 379 wp vs 1,055).
- [ ] ⇒ ⛔⛔ **FIX DIRECTION — ITS ARITHMETIC IS STALE AND IT FAILS ONCE CORRECTED (2026-09-09).**
  It reads *"L26 catch + 250k budget at wild-28 → ~L39, clearing L35"* — computed at FULL xp,
  ignoring the *"must double the estimate"* instruction in this item's OWN bullet above.
  ‼ Redone with the split applied (model reproduces all five published figures exactly): the
  first arrival level clearing the 250,000 ceiling is **L42, not L35**, and 250k at wild-28
  from L26 buys far less than the ~L39 claimed. ⇒ **CATCH-HIGHER + TRAIN-THE-REMAINDER, AS
  SPEC'D, WOULD STILL REFUSE.**   ✅✅ **DECOMP-VERIFIED AND MEASURED 2026-09-09 — THE PAYOUT IS DIVIDED AMONG PARTICIPANTS.**
  ⭐ **THE MECHANISM, from the decomp (settles it independently of any log):** `Cmd_getexp`,
  `pret/pokeemerald` `src/battle_script_commands.c:3292-3324` —
  ```c
  for (viaSentIn = 0, i = 0; i < PARTY_SIZE; i++)   ...   viaSentIn++;   // mon that were SENT IN
  calculatedExp = gSpeciesInfo[...].expYield * gBattleMons[gBattlerFainted].level / 7;
  *exp = SAFE_DIV(calculatedExp, viaSentIn);            // no EXP Share
  *exp = SAFE_DIV(calculatedExp / 2, viaSentIn);        // with EXP Share  ⇒ a SECOND regime
  ```
    ‼ **`viaSentIn` counts "was sent in AND IS STILL ALIVE", not "why".** Verified by reading the loop:
  ```c
  if (GetMonData(&gPlayerParty[i], MON_DATA_SPECIES) == SPECIES_NONE
      || GetMonData(&gPlayerParty[i], MON_DATA_HP) == 0)   continue;   // ⇐ a FAINTED participant
  if (gBitTable[i] & sentIn)  viaSentIn++;                             //    does NOT dilute
  ```
  ⇒ two consequences: (1) the divisor is **mechanism-independent** — a deliberate swap-training
  rotation and an emergency survival rotation increment the same counter, which is what licenses a
  general-population measurement standing in for swap-training; (2) **a participant that FAINTED is
  excluded**, so a trainee that goes down does not cost the survivor half its payout.
  *(This passage read "counts 'was sent in', NOT 'why'" until a verification pass caught the missing
  ALIVE condition — correct about the part that mattered, incomplete about the mechanic.)*
  ⭐ **MEASURED, and it agrees to three decimal places** (batch `20260909-160339`, 8 lanes, 3h,
  `--build sandbox`; `tools/story-dev/probe_exp_participant_divisor.py`, matched on (foe species,
  foe level) so the divisor is not confounded with which foes get fought):
  ```
    min n2   groups   median ratio      pooled sanity check (confounded by foe mix):
         1       88          0.829        1 participant  median 205 exp  (n=3,290)
         5       27          0.592        2 participants median 123 exp  (n=  401)
        10       11          0.504        ratio 0.60
        20        2          0.501      ⇐ decomp predicts exactly 0.500
  ```
  ⇒ **`estimate_frames_to_level` HAS NO PARTICIPANT DIVISOR, so every estimate where a second mon
  participates is up to 2x OPTIMISTIC — and this item's corrected arithmetic (L42, not L35) STANDS.**
  ⚠ **SCOPE, STATED:** the 401 two-participant observations are **mostly NOT deliberate
  swap-training** — this batch holds only **14** turn-0 full-HP rotation windows (11 of which showed
  two mon gaining). The decomp is what licenses generalising from one to the other; the log evidence
  alone would not.
  ⚠ **HETEROGENEITY IS REAL:** `Poochyena L6` (0.83, n2=13) and `Nincada L6` (0.81, n2=13) sit far
  from 0.5 — the `calculatedExp / 2 / viaExpShare` branch above is a plausible second regime and is
  **not** separated by this tool.
  ⚠ Previously (superseded by the measurement above): the split is 2 only when swap-training FIRES,
  so the true cost is between the solo and 2-way columns — which is exactly why the measurement
  below (log `total_exp` by PID either side of a battle) was the next deliverable.
  ✅✅ **THAT BLOCKER IS CLEARED 2026-09-09 — THE TELEMETRY NOW EXISTS.**
  **[MEASURED BY ME — scope: `x4-runs` 298 `stdout.txt` + its `debug-logs/*.log`,
  `sandbox-pokebot/profiles` 500 `*.log`, `tools/story-dev` 500 `*.log`]** there was **no continuous
  PID-bearing party telemetry anywhere**: `Species#PID` occurred in **96** stdout lines, **AT THE TIME OF MEASUREMENT all of
  them §Ch23 refusal messages**, plus ~15 from one-off probes. Party snapshots carried
  `Species:L<level>` and nothing stable ⇒ **a mon could not be followed across readings**, which is
  why this measurement was blocked and why the *"88.8% born behind"* figure on `#24-dexhunt` is
  still unverifiable.
  ✅ **`modules/debug_logger.py` now emits `ids=[Species#PID:L<lv>:exp<n>, …]` in the heartbeat.**
  ⛔ It is a **SEPARATE field**: `_party_key` is untouched because it drives `_detect_events` (size
  change ⇒ CATCH, slot change ⇒ LEVEL-UP/EVOLUTION), and folding identity into it would change which
  frames count as party events — a behaviour change wearing telemetry clothes. Nothing reads the new
  field. Per-mon safety: `None` slots skipped, an unreadable PID degrades to `#????????`, each mon
  wrapped in its own `except`, and the whole call wrapped again by the file's `_safe()`.
  ‼ **NOT GATE-CERTIFIED, and say so honestly:** `repro_no_silent_except.py` and
  `repro_undefined_names.py` **do not scan `modules/debug_logger.py`**, so their green exits are NOT
  evidence for that handler; the safety case is the code, read directly.
  ⇒ **NEXT: one ORDINARY batch answers it — `PYTHONUTF8=1 py -3.12 x4_headless.py --build sandbox`.**
  ⛔ **`--build sandbox` IS MANDATORY** (`x4_headless.py` defaults to `custom`, and BOTH fields are sandbox-only — `custom-pokebot/modules/debug_logger.py` has `party_ids` 0x, `_owned_dex` 0x, measured 2026-09-09) ⇒ a default batch emits NOTHING and reads as a refutation.
  Pair `total_exp` by PID either side of a wild battle
  where swap-training fires, and the L35-vs-L42 question is settled. No new driver, no fixture.
- [ ] ⚠ **SURF IS STILL UNSOLVED BY BOTH.** Best pre-Surf ground is Route 117 **L13** (every
  higher-band Surf-learner ground is gated behind Surf itself), and L13+250k → ~L28 < L35. ⇒ the only
  candidate is acquiring a carrier at **§Ch3 (Route 104 Marill L4-5, at team level)** so it is never
  a mule. ✅ **VERIFIED 2026-09-08** from our own ROM-derived cache `sandbox-pokebot/cache/encounter_index_BPEE0.json`: **Route 104 Grass, Marill, 20% of encounters, L4-5.** ⛔⛔ BUT THE §Ch3 ACQUISITION IS **REFUTED** — see the block below; the encounter data was never the weak link.
  ⭐ [VERIFIED] Marill learns ALL FIVE HMs (Dive/Rock Smash/Strength/Surf/Waterfall); Zigzagoon only
  Cut/Rock Smash/Surf. Full detail: `ai-research-notes/2026-09-08-hm-mule-catch-sites-MEASURED.md`.
