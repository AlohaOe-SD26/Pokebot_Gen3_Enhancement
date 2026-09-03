# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-09-03 — start at the single orientation block immediately below.
Every banner further down is HISTORY, newest first.

---
# ‼ YOU ARE HERE (2026-09-03) — **§Ch22 IS A CHAPTER. IT IS BUILT, WIRED AS SEGMENT 22, AND DRIVEN TO `ACCEPTANCE: PASS` — INCLUDING LOSING THE GYM FIGHT AND RECOVERING FROM IT. THE LADDER IS 23 OF 24. ⛔ DO NOT REBUILD ANY PART OF §Ch21 OR §Ch22. THE LIVE WORK IS §Ch23 — VICTORY ROAD** (`chapters.py:259-262`, graded on `DEFEATED_WALLY_VICTORY_ROAD`). *(This banner said "THE LIVE WORK IS NOW §Ch22 (GYM 8 — JUAN)" for a day after the fight was won — a Tier 1 re-check caught it while the queue head 300 lines below had already been corrected, which is the fix-landed-in-the-wrong-half shape verbatim.)* §Ch21: legs 1 + 2a + 2b + 3 + 4 + 5 **AND** the `_play()` WIRING are ALL BUILT AND DRIVEN (Segment 21, chapter drive `frames=95823`, PASS) — ⛔ nothing about §Ch21 remains to build; ✅ LEG 3's POCKET-EXIT PROBE IS DONE 2026-08-27 (§4.11's answer is the RESTING tile **(31,17)**, not the warp target (31,16)); ✅✅ THE SKY PILLAR ATLAS PASS IS DONE AND **VERIFIED BY ITS ADVERSARIAL CRITICS**: the story climb runs on the **CLEAN** layouts while our planner reads the **post-game** ones. ✅ **THE “no crack-free route” BLOCKER WAS REFUTED — it answered the wrong question; every leg HAS a crack-free story route and banning 4F's five real cracks is FREE.** ⛔ Still inverted on `SKY_PILLAR_TOP` and `ROUTE131` (that is KI-73's shape, not new). ✅✅✅ **LEG 3 IS BUILT AND DRIVEN 2026-09-01 — `--driver ch21approach`, `ACCEPTANCE: PASS`, all 14 readings, `missing=[]`, `frames=34122`, `encounters=9`, both fault arms run; fixture `post_skypillar_door.ss1` PINNED. ⛔ DO NOT REBUILD IT.** ⛔⛔ **AND ITS FIRST DRIVE FOUND A DEFECT CLASS THE WHOLE TREE WAS BLIND TO: `_map_layout_cache` (map.py:735-755) is keyed by MAP ALONE, so the LIVE and STATIC layout readers share one entry and whichever reads first wins FOR THE PROCESS — `calculate_path` silently inherits it.** The bot walked into a 9x3 block of solid rock in Sootopolis; A/B proven 37 wp-with-3-live-walls → 35 wp-with-none. New instrument: `probe_live_mapgrid.py` reads `gBackupMapLayout`, the grid the GAME walks on — the FIRST reader in this tree that can see `setmetatile`/`setmaplayoutindex` at all. ✅✅✅ **LEG 4 IS BUILT AND DRIVEN 2026-09-01 — `--driver ch21climb`, `ACCEPTANCE: PASS`, all 15 readings, `order_ok`, both DELIBERATE FALLS, RAYQUAZA awakened, all 7 floors pinned to CLEAN, SEVEN fault arms; fixtures `post_wallace_scene`/`post_skypillar_summit`/`post_rayquaza_gone` PINNED. ⛔ DO NOT REBUILD IT.** ⛔⛔ **AND ITS RECON KILLED TWO PLANS BEFORE A DRIVE: `_bounded_step` cannot express a fall (it asserts SAME-map; a fall CHANGES map) and `_live_wall_tiles` is crack-BLIND (collision only).** ✅✅✅ **LEG 5 (THE RETURN + HM07 WATERFALL) IS BUILT AND DRIVEN 2026-09-02 — `--driver ch21return`, `ACCEPTANCE: PASS`, all 13 readings, `missing=[]`, `order_ok`, `frames=20705`, `whiteouts=0`, `hm07_in_bag=1`, `wallace_state=1`, `gym_door_wp=2`; SIX fault arms; fixtures `post_legends_calmed.ss1` + `post_hm07.ss1` PINNED. ⛔ DO NOT REBUILD IT.** PART C ran FIRST (`--driver ch21leg5probe`, PASS, P0-P6) and settled BOTH gates: the ROUTE131 pin is load-bearing (proven by an arm with it REMOVED — un-pinned the swim does not mis-plan, it raises `PathFindingError` and the bot never moves), and the state-5 Sootopolis layout is SAFE (pin is a NO-OP; 0 of 3600 tiles open-to-planner/wall-live). ⛔⛔ **AND DRIVE 1 PASSED WHILE SEALING §Ch22** — `_ride_talk` returned mid-script so Wallace never stepped off the tile blocking the GYM warp, and the 'can continue' check had been aimed at the Poke Center; fixed, and the lesson is in `08-MISTAKES.md` 2026-09-02. ✅✅✅ **§Ch21 IS A CHAPTER AS OF 2026-09-02 — WIRED INTO `_play()` AND DRIVEN END TO END. ⛔ DO NOT REBUILD IT.** `--driver ch21chapter` from `post_ch20.ss1` → `ACCEPTANCE: PASS`, `premise_ok=True`, ROUTE128 (38,24) vars (1,0) → SOOTOPOLIS_CITY (31,34) vars (5,3), `hm07_in_bag=1`, `wallace_state=1`, gym door 2 wp, `encounters=26`, `whiteouts=0`, **`frames=95823` (MEASURED)**. ‼ IT ALSO MEASURED THE PARTY: `post_ch20` starts with one member ALREADY FAINTED and the chapter **MEASURED: `post_hm07.ss1` is SIX ALIVE at 629/694 (91%), lead 52/115 — NOTHING is fainted.** ⛔ *(A claim that it "ENDS chipped, one member fainted, lead 25/115" stood here on 2026-09-02 and was WRONG: that is the CHAPTER DRIVE's end party from a DIFFERENT run (`post_ch20.ss1` → legs 1-5), which was never captured to a fixture. An adversarial refuter caught it and my own re-measurement confirmed it — see `08-MISTAKES.md`.)* ‼ **BOTH states are real, and §Ch22 must handle the WORSE one:** a live §Ch21 handover arrives chipped HARDER than the pinned fixture suggests. — only two heals exist (legs 2a and 3) and there is NO Poke Center after leg 3, so **§Ch22 inherits a chipped party**. NEXT = **§Ch23, VICTORY ROAD** (`chapters.py:259-262`, graded on `DEFEATED_WALLY_VICTORY_ROAD`) — Surf/Waterfall/Dive to Ever Grande, clear Victory Road (Strength / Rock Smash / Flash inside), beat Wally. ⭐ **Badge 8 is what makes field WATERFALL usable** (`src/field_control_avatar.c` gates `EventScript_UseWaterfall` on `FLAG_BADGE08_GET`), so §Ch22 landing is exactly what unblocks it. ⛔ §Ch22 is DONE — chapter, wiring and all. See the last ➡➡➡ in NEXT ACTIONS. Three USER DECISIONS are ripe and listed there. ⛔ The PC/PARTY arc and the three `#26-*` production defects are DONE — a 2026-08-18 headline claimed the PC/PARTY arc was live until a cold-start audit caught it on 2026-08-27. THE TREE IS AT A CLEAN BOUNDARY **AS OF THE COMMIT CARRYING THIS LINE** (a cold-start audit correctly flagged the earlier absolute wording: a banner cannot truthfully say "everything is pushed" while it is itself the uncommitted edit — so read this as *"true at this commit"*, and trust `git status` over any prose). ⚠ **DRIFT IS 9 as of 2026-09-02 (⬆ from 8 on 2026-09-02: the NEW `modules/story/sootopolis_gym.py`, §Ch22's chapter module — a new sandbox-only chapter file, exactly as §Ch20 and §Ch21 each did. ⚠ PROMOTION IS THE USER'S CALL and is NOT implied here; run `promote.py --check`, which outranks this text). *(formerly 8 as of 2026-08-27 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) AS OF 2026-08-23** (`early_game.py`, `#24-loopheadabort`, sandbox-only — ⛔ PROMOTION DONE 2026-08-24, the USER's call). *(It was 0 after ALL FIVE WERE PROMOTED 2026-08-17, USER-APPROVED)* (the `#24-orphans` (1) verdict change, the `#24-abortswallow` guards and the `#24-ki76correctness` COMMENT-ONLY map_path fix). ⛔ NOTHING awaits a promotion decision now** (all five, now IN BOTH FORKS: `pc_trip.py`, `higher_level_actions.py`, `early_game.py`, `counter_hunt.py`, `map_path.py` — ⛔ the STATE row is the authority for this list, and `promote.py --check` outranks both); everything BEFORE them was already promoted, the KI-66 `_on_field` fix included (2026-08-17, user-approved, THREE-POINT A/B against `--build custom`, not a byte-compare). BOTH `story_mode.py` changes are promoted too (the comment-only correction and the **KI-80 DECOUPLING**, a BEHAVIOUR change proven by a THREE-POINT A/B against `--build custom`), user-approved 2026-08-16.** ✅ **(P4) IS DRIVEN THROUGH STAGE 2** — the real heal COLLECTS the boxed counter and leads with it (ARM B), and ARM A leaves it boxed, reproducing the user's derail ORGANICALLY; matrix {ARM A, ARM B} x {sandbox, custom} = **5/5 ACCEPTANCE: PASS**. ✅ **BOTH PROMOTIONS ARE DONE (user-approved): `counter_hunt.py` (comment-only) and `pc_trip.py` (KI-79, a BEHAVIOUR change proven by a three-point A/B).** ⛔ **(P6) WAS INVESTIGATED AND REFUTED — its "obvious" fix is a REGRESSION; see KI-80, now GATED (suite #24).** ✅✅ **KI-80'S REPRO DRIVER IS BUILT, DRIVEN AND FAULT-TESTED — `--driver ki80ladder`, 3 arms, `ACCEPTANCE: PASS` in BOTH forks, and KI-80 is REPRODUCED (Winona's real Route 119 patch DELETES her counter ladder). ⛔ DO NOT REBUILD IT.** ✅✅ **KI-80 IS DECOUPLED — BUILT, DRIVEN AND REVIEWED (sandbox only).** `POKEBOT_KI80_DECOUPLED=1` went **FAIL → PASS**, arm 4 (the mirror-regression guard) **still PASSES**, the old coupled expectation now **FAILS** (proving behaviour changed), and `repro_boss_grass_gate.py` **SELF-RETIRED**. ✅ **AND PROMOTED TO BOTH FORKS 2026-08-16 (user-approved), by a THREE-POINT A/B against `--build custom`: `POKEBOT_KI80_DECOUPLED=1` FAIL → PASS, the coupled expectation PASS → FAIL, arm 4 PASS on both sides.** ✅✅ **THE WHOLE KI-80 ARC IS COMPLETE AND PROMOTED — reproduced, fixed, guarded, reviewed, and in BOTH forks. ⛔ DO NOT REOPEN IT.** ✅ **The UNRELATED KI-81 whiteout guard was also promoted 2026-08-16 — drift was 0 at that point and nothing awaited a ruling — the KI-66 `_on_field` fix was PROMOTED 2026-08-17, user-approved. ⚠ **TODAY (2026-08-24) drift was 8 as of 2026-08-27 (it is 9 now) — see the STATE row (`map_data.py` joined for §Ch21 leg 2a); formerly 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until the chapter is driven) — `modules/story/seafloor_cavern.py`, the §Ch20 chapter UNDER CONSTRUCTION, sandbox only. ⛔ NOT a promotion decision: it is incomplete (constants + predicates + preflight only, no legs yet) and must not be promoted until it is driven end to end.** ✅ The abort guards themselves are PROMOTED and their drift was 8 as of 2026-08-27 (it is 9 now) — see the STATE row (`map_data.py` joined for §Ch21 leg 2a); formerly 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven). — `early_game.py` (`#24-loopheadabort` + `#24-abortrecoveryresiduals` (b)/(c)) was PROMOTED 2026-08-24, user-approved. *(It was 0 when all five were PROMOTED 2026-08-17, user-approved, each with its own before/after discriminator and a live drive against custom.** ➡➡ **✅✅✅ THE FIVE-PASS DEEP SANITY CHECK IS COMPLETE (passes 1-5, 2026-08-22). ⛔ DO NOT RE-RUN ANY PASS.** ✅✅ **`#24-loopheadabort` IS DONE 2026-08-23 — ALL 17 nav retry loops patched, GATED as #30. ⛔ DO NOT REDO IT.** ⛔ **An earlier draft excluded 3 of them claiming they run "while the latch is SET" — an adversarial review REFUTED that and it is WITHDRAWN: `StoryMode.run` clears the latch BEFORE every recovery routine, in both branches (AST-verified). Gate #30 §1 now enforces THAT ORDERING**, because the hazard is real only if someone hoists the recovery calls above the clear. Proven by a two-armed drive of the real `_navigate_through_scripts`: ARM A `nav_attempts=25` + the FABRICATED cause, ARM B `nav_attempts=0` + `StoryAbort`. ✅✅ **`#24-p4residuals` IS 6 OF 7 DONE (2026-08-23) — (a) `--strict`, (b) fence-blanking, (c) `splitlines()`, (d) a DENYLIST, (e) `--build` on three gates, (g) proximity-scoped supersede; each fault-tested BOTH ways. ⛔ TWO of them REFUTED the item's own proposed fix by MEASUREMENT before any code changed.** Only **(f)** remains and is deferred deliberately (a real emulator drive inside a 573-line gate). ⚠ NO production code was touched, so drift is unchanged. ✅ **THE PROMOTION IS DONE (2026-08-24, user-approved) — drift was 8 as of 2026-08-27 (it is 9 now) — see the STATE row (`map_data.py` joined for §Ch21 leg 2a); formerly 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) and the forks are EQUAL; custom went 8 AST abort-swallowers → 0.** ✅✅✅ **§Ch20 IS A CHAPTER NOW (2026-08-24) — THE STORY FRONTIER MOVED.** `modules/story/seafloor_cavern.py` (971 lines) is wired as **Segment 19b (teach Dive) + Segment 20**, and the PRODUCTION entry point drove **5/5 ACCEPTANCE: PASS** — clean, plus ALL THREE recovery paths exercised by fault injection (`room8_recoveries=1`; `route128_resumes=1` with `room8_recoveries=0`, proving attempt 2 never re-dived into the permanently-disarmed trigger). ⛔ Dive is still INJECTED by the driver, so these are ASSEMBLY tests, not end-to-end story tests. ⛔⛔ **THE USER REDIRECTED PRIORITIES ON 2026-08-26 — THREE PRODUCTION DEFECTS FROM REAL TESTING (single instance, Mudkip) OUTRANKED §Ch21 (resolved 2026-08-27 into three ripe user decisions; the arc then RESUMED)** *(status after the MINED validation batch, late 2026-08-26: `#26-mossdeeppuzzlespeed` ✅ FIXED ~2.9× A/B-proven; `#26-surfteachchain` D1/D2 gates ✅ LIVE-VALIDATED — 7 of 10 teach-failure runs FINISHED; `#26-manualderails` Fortree half ✅ the SECOND WIND is END-TO-END PROVEN (27 live firings; ⚠ post-wind same-count repeat burn = an OPEN USER QUESTION); `#26-fleefreeze` ✅ ARC CLOSED (live arm landed, zero CantEscape freezes); `#26-battleitemwedge` hang-fix shipped AND LIVE-VALIDATED 2026-08-27 (its KI-47 family 2 → 0); finish rate 12/32 = 37.5% (12.0 → 25.8 → 37.5); ⛔ Treecko FIRST FINISH, and its wall is now a named run-ender)*:** `#26-manualderails` (reverts to MANUAL around Fortree/Mossdeep, recoverable by re-selecting Story — so a guard/retry hands off, not a wedge), `#26-surfteachchain` (post-Norman HM03 A-spam re-talks the NPC and re-teaches, sometimes the WRONG HM; plus the DESIGN GAP that a non-Mudkip run may hold no Surf learner at all), and `#26-mossdeeppuzzlespeed` (solved correctly but far too slowly; keep the stuck detection). ➡ §Ch21 leg 2 was parked here and is ✅ BUILT AND DRIVEN 2026-08-27 (2a+2b) — its build spec survived adversarial verification and is saved at `ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md`. ✅✅ **§Ch21 LEGS 1 AND 2 (2a+2b) ARE BUILT AND DRIVEN — the bot dives in, heals, takes Steven's escort, descends the Cave of Origin and sends Wallace to Sky Pillar (state 3): `--driver ch21dive` / `ch21escort` / `ch21cave`, each `ACCEPTANCE: PASS` with a fault arm; fixtures `post_steven_escort.ss1` + `post_wallace.ss1` PINNED.** ⛔ *(SUPERSEDED — this clause said "STILL NOT wired into `_play()`" and that is FALSE as of 2026-09-02: the chapter IS wired, Segment 21, and driven end to end.)* ✅ Leg 5 SHIPPED 2026-09-02, ALL FIVE LEGS EXIST, **and so does the wiring**. *(This clause has now gone stale THREE TIMES in the same way: it read "leg 3 is SPEC'D AND GATED but NOT BUILT", then "legs 4-5 do not exist", then "leg 5 does not exist" — each time contradicting this same banner's own headline once the leg shipped, and each time caught only by an independent reader. **P2: a banner is a claim about EVERY clause inside it**, and a clause that has rotted twice will rot again — ⛔ when the next leg/wiring ships, THIS SENTENCE is the one to grep for first.)* ‼ Three drives: the first two FAILED usefully (the arrival cutscene was still running; then MY acceptance check demanded a walkable path to the Cave of Origin, which Emerald never provides — Steven WARPS you in). ⇒ **leg 2 is FIND STEVEN, not walk to the cave.** ➡➡ **THE RECON IS DONE (2026-08-24) — THE REST OF THE CHAPTER IS *NOT* BUILT.** Five agents, one angle each, every load-bearing claim re-verified here. ⛔ **READ THE §Ch21 ATLAS IN `12-STORYMODE-DESIGN.md` BEFORE WRITING ANY Ch21 CODE.** Three results a cold reader must not re-derive: (1) the **Mach Bike is NOT needed** and two rows of `12-STORYMODE-DESIGN` said it was — corrected; (2) the ascent **REQUIRES a deliberate fall through `4F (6,4)`/`(7,4)`** (⛔ NOT `(9,4)`, a decoy) and **no pathfinder here can propose it** — `map_path.py` does not model `"Cracked Floor"`; (3) **there is no air option** — `VISITED_PACIFIDLOG_TOWN` and `VISITED_SOOTOPOLIS_CITY` are both **False**, measured, so entry and exit are BOTH by water. ‼ Ch21 is *enterable*, but "enterable" was never the question — it is **~5 legs**, and its multichoice in `CaveOfOrigin_B1F` hangs FOREVER on any answer but index 2. ✅✅ **`#24-p2headergate` IS DONE 2026-08-23** — **TWO** checks shipped (symmetric P2 header/body rule; control-character guard) and a THIRD (ratchet-baseline claims) **deliberately DELETED after a six-angle review returned 7 blockers on it — 289 lines removed**. Suite unchanged at 30 = 28 ENFORCING + 2 ADVISORY. ✅✅ **`#24-brokenrepros` IS ALSO DONE 2026-08-23** — the item said FIVE, a full sweep found SIX, each with a different root cause; the sixth was invisible because a doc filed it as "needs a real mgba", and **that same script had been misfiled the same way once before**. Filed `#24-reprosweepratchet` for the structural cause: none of the 104 repros is in `run_gates.py`, and what the suite does not run, rots. ✅✅ **`#24-abortrecoveryresiduals` (b) IS DONE 2026-08-23** — the 5 abort-swallowers my loop-head fix created are guarded, swallowing functions 11 → 7, proven two-armed (latch clear → swallowed, unchanged; latch set → re-raised) and the ratchet turned 36 → 31 WITH the control arm it demands. ✅✅ **`#24-abortrecoveryresiduals` IS FULLY RESOLVED 2026-08-23 — (a), (b) AND (c).** The abort-swallow class is CLOSED in sandbox (AST finds ZERO; ratchet 36 → 31 → 23, control-armed at each step). **(a) was ASSESSED, not coded**: a second whiteout during recovery cannot realistically occur — the window is spent on maps with ROM land-encounter rate **0**, `on_whiteout()` cannot fire twice on Emerald, and it has never happened in **16,688 recorded recoveries**. ⛔ *(BOTH SUPERSEDED — a Tier 2 audit found these standing as LIVE imperatives over work this same file reports finished. The promotion happened 2026-08-24 and the baselines followed: both forks now read **23**, i.e. ZERO AST abort-swallowers — see the `probe_abort_swallowing.py --build custom` line in HOW TO RUN. Nothing is owed.)* ⛔ **NOT `#24-ki76correctness`** — pass 5 proved its only fixture is VACUOUS for its only live defect (it stages in ROOM6, which has ZERO armed dismount chains), so a dismount A/B there would print "no difference" and read as a REFUTATION of a real 1,852-chain defect; it is BLOCKED until an anchor is captured on ROUTE132/133/134 or ROOM7 with Surf. *(Its one zero-input sub-task IS startable: the single `get_map_data` check of ROUTE134 `(60,31)`.)* **PASS 4 (INFRASTRUCTURE) IS DONE — ⛔ DO NOT RE-RUN IT.** It found **THREE STANDING GATES THAT COULD NOT FAIL** (`probe_slot_free_plan`, `probe_regi_capabilities`, `probe_dive_routing` — zero assertions, printing 4/23/6 alarm lines while the suite said PASS), a **gate runner with NO TIME BOUND**, **seven "observe-only" gates writing shared profile state** (2,820 files / 160 MB), and **8 BYPASSES + 1 FALSE POSITIVE in the `git add -A` hook CLAUDE.md calls "ENFORCED"**. All fixed and fault-tested; the suite is now **29 gates = 27 ENFORCING + 2 ADVISORY** (a new tier — see `06-DECISIONS-LOG.md`). ‼ Five items were FILED, not fixed: `#24-fixturecoverage`, `#24-gateselftests`, `#24-testrunsweep`, `#24-p4residuals`, `#24-flagnamedocscan`. ✅ **KI-82 IS CLOSED (2026-08-23) AND NOTHING AWAITS A RULING** — the tracked Emerald ROM had already been ruled KEEP on 2026-07-18 and the user re-affirmed it; ⛔ do not re-raise it (see `05-KNOWN-ISSUES.md` KI-82). ‼ The method that made passes 1-3 work: 8 agents per pass, one ANGLE each, and **every agent required to FAULT-INJECT or RE-DERIVE, never to reason** — that single instruction is what found a gate that could not fail and a control that could not fail. ⛔ VERIFY EVERY AGENT FINDING YOURSELF: 2 of ~40 were false positives. ➡ **THEN, the standing queue head is `#24-ki76correctness`** — ⛔ but read it first: its ends-on-a-warp defect is CONFIRMED LIVE, and its planner-side half is **VACUOUS ON THIS ROM, measured over 54,990 pathfinding calls** (`(14,8)` is a topological dead end, so a COST test is vacuous too). That half is BLOCKED ON REALITY, not effort. ⚠ The DISMOUNT defect is UNCONFIRMED and needs its OWN fixture — Room 7 has no driver.** ✅✅ **`#24-orphans` (5) AND (6) ARE BOTH DONE 2026-08-17 — ⛔ DO NOT REBUILD EITHER.** (5)'s premise was REFUTED before anything was built: `compare_runs.py` already existed AND already paired, but fed a real A/B (`ACCEPTANCE: FAIL` vs `PASS`) it clustered the arms as IDENTICAL on all four axes — so an `ACCEPTANCE` axis + `A/B DISCRIMINATION` section shipped instead of the requested wrapper, fault-tested four ways (test 4 caught a defect in the fix itself). ⚠ `tools/` is shared — no promotion twin. (6) closed the ORPHANING only: KI-76's correctness half now HAS an item; **its two defects remain OPEN**, and are MEASURED (production as the oracle: dismount **1,852** armed, ends-on-warp **9 and all in ROOM6, zero on the routes** — so KI-76's old header was half backwards). ⚠ **DRIFT IS 8 as of 2026-08-27 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) AS OF 2026-08-23** (`early_game.py`, `#24-loopheadabort`, sandbox-only — the promotion is DONE 2026-08-24). *(It reached zero when ALL FIVE FILES WERE PROMOTED 2026-08-17, USER-APPROVED)*, each with its own before/after discriminator (the verdict gate 1→0 on custom; the abort probe 44→36 on custom; map_path byte-equal and still AST-equal) plus a LIVE DRIVE against custom that printed `verdict landed=True code=landed` — the promoted branch RUNNING, not a file that copied. Restore point `restore/2026-08-17-pre-promotion-all5`. ✅ `#24-abortswallow` ROUND 3 is **DONE 2026-08-17**: refinement (1) shipped (37 → 36), refinement (2) **REFUTED** (it would blind the gate to five already-fixed sites, one of them an OBSERVED failure), and the probe is now **gate #27, a RATCHET at baseline 36**, fault-tested both ways. ⛔ DO NOT REBUILD ANY OF THAT.The previous next action, `(P4c) #24-orphans` (1), is HALF DONE 2026-08-17: its INSTRUMENTATION half is BUILT, GATED (#26) and A/B-PROVEN — `withdraw_from_box` returns `(landed, code, detail)`, its ONE caller BINDS it, ARM B `landed=True code=landed` vs ARM A `landed=False code=did_not_land`. ⛔ DO NOT REBUILD IT. Its REACTION half stays OPEN and still needs the USER plus an unmeasured heap offset.** ⚠ **DRIFT IS 8 as of 2026-08-27 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) AS OF 2026-08-24** — `early_game.py` was PROMOTED 2026-08-24 (user-approved), so nothing is owed. *(Those five files were PROMOTED 2026-08-17, user-approved.)* ✅ The previous next action, `#24-driftassertions`, is **DONE 2026-08-17: the drift-statement sweep IS a gate now** — `check_drift` detects CLAIM SHAPE, A/B-measured 4→9 sites caught with none lost, 17 fault tests (`--self-test` D9–D22, including two BYPASSES an adversarial review found in the first draft and which were reproduced before fixing). ⛔ DO NOT REBUILD IT; its separate REDUCTION half is filed as `#24-driftreduction`. ✅ The previous next action, `#24-faintchooser-fourthspace`, is ANSWERED 2026-08-17: the probe was built and driven, **no fourth index space is demonstrated**, the anomaly is INERT — ⛔ do not "fix" it. ✅ `#24-orphans`: (4) and (2) DONE; **(3) KI-66 is PARTLY DONE** — its `_on_field` half is FIXED, DRIVEN and PROMOTED 2026-08-17, its OWNER-filter half is still open and measured INERT on the one fixture we have. Remaining there: (1) and (3)-owner-half ONLY — ⛔ (5) and (6) are DONE 2026-08-17 and this clause listed them as remaining for one commit (a Tier 2 audit caught it). ✅✅✅ **(2) KI-65 IS FULLY CLOSED — REPRODUCED, FIXED, A/B-PROVEN, GATED (#25) AND **PROMOTED TO BOTH FORKS** ON 2026-08-16 (user-approved). ⛔ DO NOT REBUILD OR RE-PROMOTE IT.** Proven by a THREE-POINT A/B against `--build custom` (BEFORE `lie_msg=1` → FAIL; AFTER `lie_msg=0, honest_msg=1` → PASS; sandbox still PASS), with COMMITTED transcripts under `tools/story-dev/evidence/2026-08-16-ki65-PROMOTION-*`. ⛔ Its recon's prescribed fixture was REFUTED by measurement — do not retry `movelearn_hmwedge_*.ss1` on it. ⛔ **Its COST ranking and its STARTABILITY ranking differ, and the item lists only cost.** Costliest is **(1)** — no caller acts on `withdraw_from_box`'s verdict — ✅ **the USER'S RULING EXISTS** — *"reattempt but after intelligently processing the data (text boxes it reads to determine why it failed)"* (`06-DECISIONS-LOG.md`) — ⛔ **BUT IT IS NOT READY TO BUILD: a recon found a BLOCKER (the PC message buffer `sStorage->messageText` is HEAP-allocated and its offset is NOT known here — it must be MEASURED, and until it is every failure classifies UNKNOWN, which must not retry, so the feature would ship INERT) plus FOUR PREREQUISITES.** Read `06-DECISIONS-LOG.md`'s design entry FIRST. ⇒ **✅✅ **(3) KI-66 IS NOW *DRIVEN*, NOT PENDING (2026-08-17): `--driver ki66faint` is BUILT and WORKS — ⛔ DO NOT REBUILD IT. Its "sends out an ALLY's mon" HEADLINE IS REFUTED (the bot never ASKED FOR an ally slot); the REAL defect is `_on_field`'s INDEX SPACE, costing 1263 frames vs 59. ➡ ✅✅ **`_on_field`'s INDEX SPACE IS FIXED AND PROMOTED TO BOTH FORKS (2026-08-17, user-approved). ⛔ DO NOT REDO IT.** Direction MEASURED first by an observe-only probe, then applied; all gates PASSED when that landed (**25** at the time — ⛔ the CURRENT count is deliberately not repeated here; `run_gates.py` prints it and IS the authority. This sentence has now been stale at 25 AND at 26 — ⛔ `run_gates.py` prints its own count and IS the authority, never this sentence). ➡ **NEXT: the OWNER filter is still unfixed and proved INERT on this fixture — it needs its OWN discriminator, not this one. `:541-545` and `_util.py:522-587` are also untouched.** Formerly: "the genuinely startable work with zero input is now (3) KI-66"** — ✅✅ **(2) KI-65 IS DONE (2026-08-16): reproduced, fixed, A/B-proven, gated as #25. ⛔ DO NOT REBUILD IT.** ⛔ When (1) IS built: NOT a blind retry — bound it, diagnose from READ text, and an UNKNOWN reason must stop loudly rather than retry. **(3) KI-66** is four unguarded full-party scans, one feeding an UNBOUNDED `while … press A`. *(Also tracked: `#24-logcollision-siblings`, `#24-zerokocounter`, (P5).)* ⛔ *(A clause here read "§Ch20's chapter assembly stays PARKED, NOT CANCELLED" until 2026-09-01. It is **FALSE and was already retired once**: §Ch20 SHIPPED AS A CHAPTER on 2026-08-24 — see this file's own `## ✅ §Ch20 — SHIPPED AS A CHAPTER` heading. The 2026-08-27 correction landed in three places and MISSED this one and the queue preamble; a Tier 2 cold-start audit found both. **P2: a banner is a claim about every clause inside it.**)* Read this, then `14-AGENT-PLAYBOOK.md`, then NEXT ACTIONS item 0.

> ⛔ **ORDER, EXPLICITLY (a Tier 2 cold-start audit could not tell which of these came first):
> (1) RUN THE RITUAL BELOW — it is cheap and it tells you whether the tree is sane; (2) READ
> `14-AGENT-PLAYBOOK.md`; (3) GO TO `NEXT ACTIONS` item 0 and find the **`➡➡➡`** marker.
> ✅ **EXACTLY ONE LINE IN THIS FILE *BEGINS* WITH THE `➡➡➡` MARKER, AND IT IS THE LIVE NEXT ACTION.** ⚠ A bare `grep` finds many more — they are prose mentions.
> ⛔ **A MARKER IS A LINE THAT *BEGINS* `>    ➡➡➡`.** Several lines MENTION the arrows in prose
> (including this one), so a bare `grep -c` returns ELEVEN (NOT a figure to trust either — re-count it) and the old "use the LAST one" tie-break
> now lands on prose. Use `grep -n "^>    ➡➡➡"` — that returns exactly one line, and it is the
> instruction. *(A Tier 2 round-3 audit caught this: the fix for the marker defect broke the
> very invariant it was documenting.)*
> This instruction used to have to warn *"there are two; the first is a ✅-DONE block"* — that was a
> hedge around a doc defect, so the ✅-DONE block was moved to `28-HANDOFF-ARCHIVE.md` instead.
> ⛔ **If you ever find more than one `➡➡➡` here again, that is a DEFECT to fix, not a rule to
> follow:** ⛔ *(and do NOT use the old 'the live instruction is the LAST one' tie-break — the LAST occurrence is now PROSE; use the line-anchored grep above)*, and a ✅-DONE block must not wear the marker that
> means "do this next". **The live instruction is the `➡➡➡` line**, not the first thing under the
> heading. The banner sentence above lists the
> READING order only; the ritual outranks it, because reading is wasted if the tree is broken.
>
> ⚠⚠ **LINE BUDGETS — ⛔ NO COUNT IS QUOTED HERE ON PURPOSE.** `lint_docs.py` prints both and IS
> the authority; the LIMITS are fixed at **900** for this file and **3,600** for
> `03-PUNCH-LIST.md`, and rule R3 turns RED — **blocking the Tier 0 commit** — the moment either
> is passed. ‼ **This row used to quote the counts and went stale THREE times in one day**, the
> last time by ONE line, from an edit made twelve lines below it — a self-referential number
> cannot survive its own file being edited. ✅ **38 lines were recovered on 2026-08-17 (net)** by
> merging ten already-archived `##` stubs into one (`#24-handoffbudget`); nothing was deleted.
> ⛔⛔ **ARCHIVE FIRST, WRITE SECOND — AN INSTRUCTION, NOT A CAUTION.** A cold-start audit named
> this the likeliest way the next session does damage: **a nearly-full file vs a multi-agent finding
> generator.** *(That was written when `#24-sanitycheck` passes 4-5 were still ahead; both have since
> run, and between them they DID fill both files — 243 lines had to be archived at wrap-up to make
> room. The warning was right.)* R3 goes RED at 901 and blocks the Tier 0
> commit mid-wrap-up. ⛔ Do NOT trim live content, and do NOT append to banner line 10 (already
> ~6,000 chars — this file's worst readability defect). ➡ Move one CLOSED block behind a stub
> BEFORE the first agent returns. ‼ Room is NOT interchangeable — ⛔ NO FIGURE IS QUOTED HERE:
> **RUN `lint_docs.py` — its budget table is the authority.** ‼ These three counts were quoted here and were ALL wrong within a day (`03` said ~97 free with 6 left). `06`/`07`/`08` have NO budget, so findings belong THERE, not here.
> ‼ *This warning itself cost 11 lines on its first draft — even the caution consumes the
> budget it warns about, which is exactly why the move goes FIRST.* ‼ If you approach either limit,
> the relief valve is lint's own `I1` line (⛔ RUN IT — the count is deliberately not quoted here, and was wrong twice when it was; completed `[x]` items still sitting in a current-state
> file) — archive CLOSED items behind a stub BEFORE adding text, never trim live content to fit.
>
> ‼ **STEP 0 — SYNC BEFORE ANYTHING ELSE** (`CLAUDE.md` requires it; a cold-start audit found this
> ritual jumped straight to `preflight.py` and never fetched):
> ```
> git status --short && git fetch && git status -sb
> git fetch upstream-pokebot && git rev-parse --short upstream-pokebot/main   # daily, CALENDAR-day
> ```
> ⛔ **BEHIND → pull first. AHEAD or DIVERGED → STOP and report to the user** — it means a previous
> session ended without finishing its wrap-up, and reconciling unpushed work is the USER's call.
> Compare the upstream hash against `40cakes repo/UPDATE-LOG.md`; the STATE row's `upstream` date
> goes stale on a CALENDAR DAY, not on an event.
>
> ‼ **THEN, ALWAYS:** `cd tools/story-dev` **from the repo root** (the folder holding `sandbox-pokebot/`, `custom-pokebot/` and `40cakes repo/`), then
> `PYTHONUTF8=1 py -3.12 preflight.py` and `PYTHONUTF8=1 py -3.12 run_gates.py`
> — **both must exit 0; the suite is 33 gates (31 ENFORCING + 2 ADVISORY; #33 = `audit_handoff_invariants.py`, 2026-09-01 — the STRUCTURAL half of the doc layer)** ⚠ *(ONE EXPECTED EXCEPTION: if a session deliberately
> holds a commit for a Tier 2 audit, `preflight.py` exits 1 on "git is AHEAD of the remote". That is
> the ritual working, not a broken tree — report it and push, per `CLAUDE.md`.)* (it prints its own count — believe that, not this
> line, which has been wrong at 17, 18, 19, 20, 21 and 25 on the way here). ‼ **The 25 was found by a Tier 1 reviewer, FOUR LINES above a correct `26/26`** — the gate could not see this phrasing until the same commit taught it to. That ritual survived the 2026-08-14
> priority redirect and is NOT part of the superseded "older framing".

> ⛔⛔ **ONE ENFORCING GATE IS KNOWN RED: `repro_gym_whiteout_guard.py` HANGS** (killed at the
> suite's 900s bound; re-run standalone it produced nothing for ~36 minutes). It is FILED as
> `#24-gymwhiteoutgatehang` and it is **NOT a regression from §Ch21 leg 3** — it imports neither
> `sootopolis` nor `story_harness`. ⇒ **expect `run_gates.py` to cost ~15 minutes and come back
> RED on that one gate. Do not go hunting a regression.**
> ⛔ **AND EXPECT A SECOND RED IF THIS TREE IS AHEAD OF THE REMOTE:** `preflight.py` is
> `GATES[0]` and it HARD-FAILS on `ahead` (`preflight.py:95-98`). ⇒ while commits are unpushed
> the suite reads **30 of 32**, not 31, and the second red is not a regression either — it is
> preflight telling you to push. ‼ *(An earlier version of this line promised "31 of 32" flatly.
> That number is an INFERENCE from re-running ONE gate alone, not from a full suite run —
> `run_gates.py` never prints such a string; on failure it prints a FAILED list.)*
> *(This line once claimed the whole suite was green while the punch list recorded two reds the
> same day — it quoted an all-pass fraction that was never true; a Tier 2
> re-audit called it the single most likely way a next session wastes its time.)*
> **State: `main`, suite is 33 gates (**31 ENFORCING + 2 ADVISORY** — ⛔ `run_gates.py` prints its own count and IS the authority, never this line), drift **9** (see the STATE drift row; run `promote.py --check`, which outranks this line; ⛔ NOT a promotion decision until it is driven further. `early_game.py`'s promotion was DONE 2026-08-24), nothing parked MID-TASK, nothing running.** ✅ **THREE DECISIONS AWAIT A USER RULING — the drift promotion, the post-wind repeat burn and mixin adoption, all listed in the queue.** *(KI-82 — the tracked Emerald ROM — was CLOSED 2026-08-23: it had ALREADY been ruled on 2026-07-18 (`06-DECISIONS-LOG.md`, "keep it as is"), and the user re-affirmed it. ⛔ Do not re-raise it; the only condition that reopens it is the repo being made PUBLIC.)*
> ⚠ **DISK: 87% used, 247 GB free (RE-MEASURED 2026-08-18 at wrap-up).** ⛔ This row briefly read
> *"100% — 2.6 GB free"*, which was a TRANSIENT reading taken while audit agents were copying whole
> forks to scratch; one of them hit `No space left on device` mid-run, which is real and is why the
> caution below stands. ‼ **I wrote that spike into a CURRENT-STATE file as a standing fact and it
> was false within the hour** — the exact staleness shape this session fixed a dozen times, in the
> file that warns about it. ⇒ **a resource reading is a MEASUREMENT, not a property: re-take it at
> wrap-up or do not record it.** ⛔ Still true regardless: do NOT copy a whole fork to scratch —
> prefer synthetic fixtures — because a full disk truncates logs, and a truncated log reads here as
> a short run.
> ✅✅✅ **THE DEEP SANITY CHECK (user-requested, 5 passes x 8 agents) IS COMPLETE — 5 of 5**, each pass committed
> separately: PASS 1 TRUTH (`045bdd1c`), PASS 2 CODE HEALTH (`e74d6e50`), PASS 3 ADVERSARIAL
> (`899f4ce7`). ‼ **What it found is why passes 4-5 are worth running:** a GATE THAT COULD NOT FAIL
> (`repro_whiteout_abort.py` matched a COMMENT, now AST + 6 fault tests), a POSITIVE CONTROL THAT
> COULD NOT FAIL (asserted coordinates, not the booleans it published — 1852 -> 978 under injection
> while still printing PASS), two 'observe-only' probes that were WRITING, a tool that never
> compiled, and a false 'the forks have diverged' claim in `01-VISION-AND-DESIGN.md`.
> ⛔ **2 of ~40 agent findings were FALSE POSITIVES — verify every one before acting.** All work pushed
> **as of the commit carrying this line** — trust `git status`. ⚠ *"Nothing parked mid-task"* means no
> half-edited work and no `/checkpoint` debt. ‼ *(CORRECTED 2026-08-27: this cited §Ch20 chapter
> assembly as the thing "parked, finished and waiting" — it SHIPPED 2026-08-24, so that example is
> retired. Name whatever IS parked here; do not write the unqualified absolute.)*
> ⚠ **EXPECTED DIRT — READ BEFORE BELIEVING `preflight.py`'s WARN:** every `story_harness.py` drive
> APPENDS to the TRACKED `tools/story-dev/party_accounting_ledger.jsonl` ((P3b)'s observer ledger),
> so after ANY driver run `git status` shows it modified and preflight prints `WARN 1 uncommitted
> file(s)`. **Expected, not a broken tree.** ⛔ Do NOT `git checkout --` it — COMMIT it with the work
> that produced it. ✅ **2026-08-16: `preflight.py` now LISTS the dirty files and annotates this one
> in place** — *"EXPECTED after any driver run; COMMIT it, never `git checkout --` it"* — so the tool
> answers the question at the point of confusion. This line is now the BACKUP, not the only way.
> ⚠ *(Superseded 2026-08-27: this led with a drift figure of 1.)* ‼ **DRIFT IS 8 as of 2026-08-27 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) AS OF 2026-08-23** — `modules/story/early_game.py`, the `#24-loopheadabort` loop-head abort checks (sandbox only). ⛔ **A PROMOTION DECISION IS NOW OWED and it is the USER's call.** ⛔ Never read a drift figure from prose: run `promote.py --check`. *(Superseded: "the drift figure is 0, and NO PROMOTION DECISION IS OWED")* — — `pc_trip.py`, `higher_level_actions.py`, `early_game.py`, `counter_hunt.py`, `map_path.py` (the `#24-orphans` (1) verdict change, the `#24-abortswallow` abort guards, and `#24-ki76correctness`s COMMENT-ONLY cap correction) — ✅ ALL FIVE WERE PROMOTED 2026-08-17, user-approved; ⛔ this clause read "all sandbox-only" for one commit AFTER the promotion, which is the exact contradiction a Tier 2 audit stops for. ⛔ Everything BEFORE it is promoted (the KI-66 `_on_field` fix 2026-08-17, KI-65 2026-08-16), each proven by a THREE-POINT A/B, never a byte-compare. *(⚠ DESCRIBED, NOT REPRINTED — this file's own convention, because the gate matches literal strings and cannot tell a quotation from a claim: this line asserted a ZERO figure, and 'everything is promoted', for a day after both stopped being true. A Tier 2 audit caught it; the gate now also matches the phrasing with a NOUN between 'drift' and 'is'.)*
> *(⚠ Keep those two ideas separate anyway: they are independent, and this line existed to say so
> loudly while they disagreed.)*
> ✅✅ **CORRECTED 2026-08-17 BY MEASUREMENT — the note that used to sit here was FALSE OF THE CODE.**
> It said `audit_doc_consistency` "cannot tell a NEGATION from a claim — it red-flagged this very
> line once for saying the figure was NOT zero, so phrase any future caveat here carefully."
> ⛔ **The gate never fired on any negation.** All six verbatim historical phrasings were run
> through the SHIPPED gate with the ground truth stubbed to **both** 0 and 1, and then through
> **every** `check_*` function in the file: **silent in all cases**. A negation was a FALSE
> NEGATIVE in both directions, and that advice was steering authors *into* the blind spot rather
> than away from a noisy gate. ✅ **NOW FIXED:** negations are PARSED and evaluated as claims
> (`drift ≠ N`), polarity inverted — ruling in `06-DECISIONS-LOG.md`, fault-tested both ways
> (`--self-test` D13/D13b). ‼ Write the caveat you mean; the gate reads it correctly now.
> ✅ **The 2026-08-15/16 promotions (KI-79 `pc_trip.py`, the comment-only `counter_hunt.py` and
> `story_mode.py` corrections) are DONE and user-approved** — narrative in `07-CHANGELOG.md`,
> restore points in the STATE table. ‼ **Keep the two METHOD rules they bought:** a comment-only
> promotion is proved behaviour-neutral by **AST equality**, never by "the diff looks like
> comments"; and a behaviour change is proved by a **THREE-POINT A/B against `--build custom`**,
> because "byte-identical" only proves a file was COPIED, never that its new branch RUNS.
> each assert which fork they imported). ‼ **`promote.py --check` IS the authority — ⛔ and this line no longer quotes a digit, per
> `#24-driftreduction`: read the STATE table's drift row for today's figure and the sanctioned file
> list. A file it lists that the STATE row does NOT name is unexplained drift and a reason to stop.**
> ⛔⛔ **DIGITS, NOT WORDS — when you change a drift count, grep the WORD forms too.** *(Confirmed
> again 2026-08-15: the gate flagged 3 of 7 stale claims; the 4 it missed were spelled "zero",
> sat in a table cell, or read "0 as of". Full history of this line's four staleness incidents:
> `28-HANDOFF-ARCHIVE.md`.)*
> **Every room of the Seafloor Cavern is DRIVEN and PASSING** — `ch20dive` → rooms 1, 2, 6, 3, 8, 9
> (Kyogre awakened, `VAR_ROUTE128_STATE == 2`). ⛔ *(This line read "What remains of §Ch20 is
> CHAPTER ASSEMBLY" until 2026-09-01 — FALSE, and two lines above the heading that says so:
> §Ch20 SHIPPED AS A CHAPTER on 2026-08-24. Nothing of §Ch20 remains.)*

## ✅ §Ch20 — SHIPPED AS A CHAPTER 2026-08-24 — ⛔ DO NOT REBUILD — DETAIL in `28-HANDOFF-ARCHIVE.md`

‼ **The rules later work still leans on, kept here on purpose:** grade on
**`VAR_ROUTE128_STATE == 2`**, never the Kyogre flag (set BEFORE a forced warp);
**`FLAG_SYS_USE_STRENGTH` is cleared on EVERY WARP**; press **A only when a text printer is
waiting, B otherwise**; **copy upstream's ROUTE, never its CONTROL FLOW**; **KI-59** is FIXED,
PROVEN and GATED (`repro_impassable_dirs.py`) — ⚠ KI-76's correctness half is still OPEN.

## ⛔ NAMING: "§Ch21" IN TEXT DATED ON OR BEFORE 2026-08-13 MEANS **CHAPTER 20** (Seafloor Cavern)
✅ Rename DONE 2026-08-13; the old `ch21*` names survive ON PURPOSE in the append-only `06`/`07`/`08`.

## ⏱ THE 60-SECOND VERSION (if you read nothing else) — rewritten 2026-08-27

*(‼ rewritten 2026-08-27 because the previous version was TWO ARCS STALE — it opened on an arc that had finished days earlier. This is the FIRST thing a cold reader sees, so it rots the most expensively; it gets rewritten on EVERY chapter move.)*

* **§Ch21 IS FINISHED — Sootopolis / Cave of Origin / Sky Pillar / Rayquaza / HM07.** All five legs
  **AND** the `_play()` wiring shipped 2026-09-02: Segment 21 dispatches
  `sootopolis.do_sootopolis_chapter()`, and `--driver ch21chapter` drove legs 1→5 end to end from
  `post_ch20.ss1` → `ACCEPTANCE: PASS`, **`frames=95823` (MEASURED)**, `encounters=26`,
  `whiteouts=0`, ending SOOTOPOLIS_CITY (31,34) with the GYM WARP reachable in 2 wp. The
  chapter ladder is **23 of 24** — ⛔ DERIVED so it can be re-checked: §Ch18+§Ch19 reached **20**,
  §Ch20 **21**, §Ch21 **22**, §Ch22 **23**. Only §Ch23 (Victory Road) and §Ch24 remain. *(A draft said 21, putting §Ch20 and §Ch21 on the same rung; a Tier 2 cold-start audit caught it.)*
* ➡ **THE NEXT ACTION IS §Ch23 — VICTORY ROAD** (`chapters.py:259-262`, graded on
  `DEFEATED_WALLY_VICTORY_ROAD`): Surf/Waterfall/Dive to Ever Grande, then clear Victory Road
  (Strength / Rock Smash / Flash inside) and beat Wally. ⭐ **Badge 8 is precisely what unblocks
  it** — `src/field_control_avatar.c` gates field `EventScript_UseWaterfall` on `FLAG_BADGE08_GET`.
  ⛔ Do NOT rebuild a §Ch21/§Ch22 leg, re-run the leg-5 PART C probe, or re-wire either chapter.
* ✅✅✅ **§Ch22 IS A CHAPTER (2026-09-03) — BUILT, WIRED AS SEGMENT 22, AND DRIVEN TO
  `ACCEPTANCE: PASS`.** `--driver ch22chapter` from `post_hm07.ss1`: `badge8=True`, ending
  `SOOTOPOLIS_CITY (31,33)`, `city_state=6`, `ice_steps=64`, `b1f_steps=19`, `CONTINUE=23`,
  `frames=64563`. Both fault arms exercised. ⛔ DO NOT REBUILD ANY OF IT.
  ⭐⭐ **AND IT PASSED BY *LOSING THE GYM FIGHT AND RECOVERING*** — `outcomes=['BattleOutcome.
  Lost','BattleOutcome.Won']`, `RECOVERIES 1`: it cleared the abort latch, walked out of the Poké
  Center, re-entered, walked **virgin ice** and won the second time. ⚠ **The fight is stochastic:
  5 WINS AND 1 LOSS over six distinct RNG draws.** "The party CAN win Juan" is measured; "wins
  reliably" is measured FALSE. ⇒ a story run may spend an extra ~35k frames there, by design.
  ⭐ **`battles_on_B1F=0` WITH `b1f_entered=True`** confirms the decomp read that the Juan victory
  script `settrainerflag`s all ten B1F trainers ⇒ the post-badge descent is free, there is no XP
  run, and `ch22exit`'s 3 battles / 629→332 HP were measured at `badge8=False`, a premise the
  chapter never enters. ‼ Drive 1 printed the SAME `0` having never entered B1F — identical
  number, and only one of them means anything.
  ⛔⛔ **AND ONE ARM DIED TO KI-47, WHICH IS NOT §Ch22's:** `handle_battle_action_selection` froze
  3,001 frames inside the Juan fight and dropped to Manual with **no `ACCEPTANCE` line at all**
  (it happens in the battle listener, outside the story generator). ⭐ KI-47 now has a
  deterministic ~22,000-frame repro command — see KI-47. *(This bullet has gone stale FIVE times;
  it is the FIRST thing a cold reader is told to read, so update it whenever §Ch22/§Ch23 moves.)*
* ⛔⛔ **A CONTINUATION CHECK IS ONLY AS GOOD AS THE CONTINUATION IT NAMES** — leg 5 drive 1
  printed `ACCEPTANCE: PASS` holding HM07 while the (31,32) SOOTOPOLIS GYM warp, §Ch22's own
  entrance, was UNREACHABLE: Wallace had never stepped off the tile in front of it and the
  check pointed at the Poké Center, reachable either way. ⇒ aim every can-continue check at what the NEXT item actually walks to. (`08-MISTAKES.md` 2026-09-02.)
* ⛔⛔ **THE RULE LEG 3 PAID FOR: "the planner returned a path" is NOT "the bot can walk it".**
  `_map_layout_cache` (map.py:735-755) is keyed by MAP ALONE, so the live and static layout
  readers share one entry, whoever reads FIRST wins for the process, and `calculate_path`
  inherits it — leg 3's first drive walked into a 9x3 block of solid rock. ⇒ **check routes
  against `sootopolis._live_wall_tiles()` / `probe_live_mapgrid.py`, which read `gBackupMapLayout`, the grid the GAME walks on.** ‼ §Ch22 is the same class in a NEW form: there, `_live_collision_grid` is blind to `setmetatile` and fails SILENTLY.
* ✅ **Everything before §Ch21 is DONE** — the PC/PARTY arc, §Ch20 as a chapter (2026-08-24), and the three `#26-*` production defects. ⛔ Do not rebuild any of them.
* ⛔ **Three USER DECISIONS are ripe and are not mine to make:** the drift promotion, the post-wind repeat burn (`#26-manualderails` D4), mixin adoption (`#24-harnesswhiteoutdrop`).
* ‼ **The rules that keep biting, in one line each:** agreement between documents is NOT
  evidence (they may be copies); **never let the planner choose a surfacing tile** (KI-72);
  **`puzzle_solver.py` is a recipe book to COPY FROM, never to drive**; and a chapter's grade
  must include a real `calculate_path` off the END tile — §Ch15/18/19 each PASSED stranded.

## WHAT THIS IS
`sandbox-pokebot/` is the working build of a Pokémon Emerald bot. Its **Story mode** plays the game
autonomously from Littleroot. `40cakes repo/` is a pristine upstream mirror (never edit);
`custom-pokebot/` is the promoted fork. **All work happens in `sandbox-pokebot/`.**

‼ **CLAUDE SUBAGENTS ARE STANDING-APPROVED** for research and assistance (user directive
2026-08-12, in `CLAUDE.md`). Use them freely — fan out on different ANGLES in ONE message, include
one explicitly ADVERSARIAL, tell them what is already ruled out, and keep working while they run.
**Their output is a NOTE, never truth**: verify the load-bearing claim in our own harness. That is
how KI-58 was cracked after four of my own models failed.

‼ **READ `01-VISION-AND-DESIGN.md`'s NORTH STAR FIRST if you have not.** The user restated the goal
on 2026-08-11: (1) a bot that plays Emerald **organically and faithfully, as a human would**, and
(2) **a documented substrate for a future self-training AI agent**. Goal 2 is why the documentation
burden here is so heavy, and why negative results are treated as the most valuable asset.

## STATE
| | |
|---|---|
| branch / HEAD | `main` — **⛔ TRUST `git status`, NOT THIS CELL.** It was clean and fully pushed at the commit carrying this line; a cell cannot truthfully assert its own push. |
| box | **IDLE.** Nothing running. Last batch `20260826-185918` (VERDICT OK, 12/32 finished — MINED 2026-08-27, see NEXT ACTIONS; its predecessor `20260826-130441` also mined). |
| story content | ✅ **§Ch19 COMPLETE 2026-08-12 — the MOSSDEEP SPACE CENTER is defended and HM08 DIVE is in the bag.** ⛔ **THE LADDER IS 23 of 24 AS OF 2026-09-03** (§Ch19 → 20, §Ch20 → 21, §Ch21 → 22, **§Ch22 → 23**); only VICTORY ROAD and the ELITE FOUR remain. This cell said "20 of 24" until a Tier 2 audit found three different values in this one file, and "22 of 24" until §Ch22 shipped — ‼ it is the cell that goes stale on EVERY chapter. Littleroot → 6 badges → Mt. Pyre → Magma Hideout (and out) → Slateport submarine theft → the Lilycove AQUA HIDEOUT (with the MASTER BALL) → the MIND BADGE → **the Space Center multi battle + Dive**. (was 19 of 24 before Ch19.) |
| ‼ **§Ch20 SEAFLOOR CAVERN** | ✅ **DRIVEN END TO END (2026-08-14) — Kyogre awakened, atoll escape executed.** Seven drivers, all `ACCEPTANCE: PASS`: `ch20dive` (6/6) → `ch20room1` → `ch20room2` → `ch20room6` → `ch20room3` → `ch20room8` (PASS ×2 incl. a FAULT run proving jam recovery) → **`ch20room9` (NEW, PASS ×2 — runs 1 & 3; ⚠ run 2 LOST the Archie fight, a MEASURED 2W/1L on the chain's one stochastic element)**. Each run re-solves every room beneath it (`FLAG_TEMP_*` respawn on map load) — counts now **R1 n=13, R2 n=10, R6 n=9, R3 n=8, R8 n=5, R9 scene n=3 (full chain n=2)**. The cutscene chain is deterministic (identical milestone frame counts across passing runs); release gated on `VAR_ROUTE128_STATE == 2`; facing on release MEASURED `'Up'` ×2. ✅ **IT IS A CHAPTER AS OF 2026-08-24** (`modules/story/seafloor_cavern.py`, wired as Segment 20, 5/5 drives PASS — commit `2680433f`). ⛔ *This row said "NOT a chapter" for one commit after it became one; a Tier 1 review caught it.* ‼ The ladder is **21 of 24** now, not the 20 quoted below. Superseded text: No module in `modules/story/`, nothing wired into `story_mode.py`, drivers **inject Dive with a debug write**. Ladder still **20 of 24**. **Remaining: CHAPTER ASSEMBLY** (organic Dive via KI-63 wiring, Repel policy, badge/move pre-flight, whiteout-retry for Archie, the atoll escape leg). |
| ‼ **§Ch21 SOOTOPOLIS / SKY PILLAR** | ✅ **LEGS 1, 2a, 2b AND 3 ARE BUILT AND DRIVEN.** `modules/story/sootopolis.py`; drivers `ch21dive` / `ch21escort` / `ch21cave` / `ch21approach`, all `ACCEPTANCE: PASS`. **Leg 3 (THE APPROACH) shipped 2026-09-01**: 14/14 readings, `frames=34122` (MEASURED), `encounters=9`, `whiteouts=0`, `method_ok=True`, `premise_ok=True`, plus THREE fault arms (`POCKETSTALL` → `pocket_attempts=2`, still PASS; `BLINDWALL` → fails loudly, bounded, no hang; `POCKETWALKBACK` → the recovery's own walk-back stalling now raises a NAMED "stranded" error — a BLOCKER an adversarial review found after the first three drives passed). Fixtures PINNED: `post_ch20` → `post_sootopolis_arrival` → `post_steven_escort` → `post_wallace` → **`post_skypillar_door`** (⚠ the last one is at **91% HP** — there is NO Poke Center after Sootopolis, so leg 4 inherits a chipped party). ✅✅ **LEG 4 (THE SKY PILLAR CLIMB + DESCENT) SHIPPED 2026-09-01** — `--driver ch21climb`, `ACCEPTANCE: PASS`, all 15 readings, `order_ok=True`, `frames=10079`, both DELIBERATE FALLS (`4F(6,4)` ascent, `4F(1,3)` descent), RAYQUAZA awakened (vars 5/1/1), all 7 floors pinned to their CLEAN layouts, plus SEVEN fault arms all FAIL for their own reason. Fixtures PINNED: `post_wallace_scene` (OUTSIDE 14,7, state 4) → `post_skypillar_summit` (TOP 14,9, state 5/1) → `post_rayquaza_gone` (ENTRANCE 14,3, state 5/1 — leg 5's start). ✅✅✅ **§Ch21 IS A CHAPTER AS OF 2026-09-02 — ALL FIVE LEGS **AND** THE `_play()` WIRING ARE SHIPPED AND DRIVEN.** Segment 21 dispatches `sootopolis.do_sootopolis_chapter()`, graded on `ch21_chapter_done()` (the flag **AND** `SOOTOPOLIS_WALLACE_STATE != 0` — stricter than `chapters.py:250` on purpose, see `06-DECISIONS-LOG.md`). `--driver ch21chapter` → PASS, `frames=95823`, `encounters=26`, `whiteouts=0`. ✅ **LEG 5 (THE RETURN + HM07 WATERFALL) SHIPPED 2026-09-02.** `--driver ch21return` from `post_rayquaza_gone.ss1` → `ACCEPTANCE: PASS`, **all 13 readings, `missing=[]`, `order_ok=True`**, `frames=20705` (MEASURED), `encounters=7`, `whiteouts=0`, `hm07_in_bag=1`, `wallace_state=1`, `gym_door_wp=2`, plus SIX fault arms each failing for its own reason. PART C ran FIRST (`--driver ch21leg5probe`, PASS, P0-P6, `frames=16297`) with predictions filed before the drive. Fixtures PINNED: `post_legends_calmed` (the mid-leg arrival anchor — the NPC half re-runs in ~4,600 frames instead of re-swimming) → **`post_hm07`** (SOOTOPOLIS_CITY (31,34), `RECEIVED_HM_WATERFALL` SET, HM07 x1 by item id, the gym warp reachable in 2 wp). ‼ HM07 = Wallace after BOTH leaders (gate `FLAG 0x9E`), and the SECOND leader talk `warpsilent`s the player to (31,34). ⛔⛔ **DRIVE 1 PASSED WHILE SEALING §Ch22** — the ride returned mid-script, Wallace never stepped off the tile blocking the (31,32) GYM warp, and the "can continue" check pointed at the Poke Center. FIXED (`not script.is_active` in the ride + a new `R-GYMDOOR` reading); `08-MISTAKES.md` 2026-09-02. ‼ The crack oracle is `get_map_data(...).tile_type` on a pinned floor (both 'Cracked Floor' AND 'Fall Warp') — `_live_wall_tiles` alone is crack-BLIND. |
| ‼ **§Ch22 GYM 8 — JUAN** | ✅✅✅ **A CHAPTER AS OF 2026-09-03 — BUILT, WIRED AS SEGMENT 22, DRIVEN TO `ACCEPTANCE: PASS`. THE LADDER IS 23 OF 24. ⛔ DO NOT REBUILD.** `modules/story/sootopolis_gym.py`; drivers `ch22probe` / `ch22ice` / `ch22stairs` / `ch22exit` / `ch22juan` / `ch22chapter`. The chapter drive: `badge8=True`, ending `SOOTOPOLIS_CITY (31,33)`, `city_state=6`, `ice_steps=64`, `b1f_steps=19`, `battles_on_B1F=0` **with `b1f_entered=True`**, `CONTINUE=23`, `frames=64563`, plus BOTH fault arms (`NODESCEND` strands on the island with the badge → FAIL; `STRANDED` stops on GYM_1F → FAIL — together they prove `ch22_chapter_done()` is the badge **AND a position**). ⭐ **IT PASSED BY LOSING THE GYM FIGHT AND RECOVERING** (`RECOVERIES 1`): the fight is stochastic — **5 wins, 1 loss over six distinct RNG draws** — so "CAN win" is measured and "wins reliably" is measured FALSE. ⛔ One jittered arm died to **KI-47** (a shared battle-path freeze, 3,001 frames, drop to Manual with NO `ACCEPTANCE` line) — that is not §Ch22's defect, and KI-47 now carries a deterministic repro. Fixture `post_hm07.ss1`; predictions were filed BEFORE the orchestrator existed and are graded in `ai-research-notes/2026-09-03-ch22-CHAPTER-RESULTS.md`. |
| ‼ is code frozen? | **No.** Nothing is running. |
| party ORDER | ✅ **PROVEN 2026-08-13.** `--driver roster` from `saves/post_dive.ss1` → `phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True ACCEPTANCE: PASS`. Raw transcripts (both A/B arms) in `ai-research-notes/2026-08-13-roster-drive-predictions.md`. ‼ The **deposit/withdraw** half of `#24-roster` is still open. |
| upstream | checked **2026-09-02**, still `5dd898f8` — no change (re-fetched this session; `40cakes repo/UPDATE-LOG.md` already recorded the same date, and THAT file is the authority — this row only mirrors it). ‼ This row goes stale on a CALENDAR DAY, not on an event: if today's date is later than the one shown, **the daily check is DUE** (`git fetch upstream-pokebot`, compare against `40cakes repo/UPDATE-LOG.md`). Do not read it as satisfied. |
| restore point | **NEWEST: `restore/2026-08-17-pre-promotion-all5`** — taken immediately before the user-approved FIVE-FILE promotion (2026-08-17); roll back HERE to undo all five. Its BEFORE evidence is one commit EARLIER, in `0b1d8480`. Previous: **`restore/2026-08-17-pre-promotion-ki66-onfield`** (the KI-66 `_on_field` promotion). Previous: `restore/2026-08-16-pre-promotion-ki65`, then `restore/2026-08-16-pre-promotion-ki81-abort-guard` (the KI-81 whiteout guard — roll back HERE to undo it; its BEFORE evidence is one commit EARLIER, in `6de47264`). Then `restore/2026-08-16-pre-promotion-ki80-decoupling` (the KI-80 BEHAVIOUR promotion — roll back HERE to undo it; its BEFORE evidence is one commit EARLIER, in `1c11927e`). Then `…-credible-answer-comment` (2026-08-16), then `…-ki79-pctrip` (2026-08-15). ⛔ *This row has now been caught stale TWICE — once naming the wrong tag by TIME, once by failing to add two newer ones. Both times a rollback taken from it would have gone to the WRONG point.* ⛔ *This row named `…-counterhunt-comment` as newest until a 2026-08-15 cold-start audit checked the tag DATES: `ki79-pctrip` is 18:00, `counterhunt-comment` is 16:30. A rollback taken from the row as written would have reverted to the WRONG point.* ‼ **`git for-each-ref --sort=creatordate refs/tags/restore/` is the authority, not this row.** Also today, oldest-first: `…-stage0-p4`, `…-boxwrite-docstring`, `restore/2026-08-15-pre-promotion-counterhunt-comment` (annotated, pushed, and verified on origin by `promote.py` BEFORE it copied) — taken immediately before the user-approved comment-only `counter_hunt.py` promotion, and therefore the rollback point for it. ⛔ *The promotion HAS been taken; the older row below still called it "the promotion decision below" as if pending.* Older: **`restore/2026-08-13-session-end-ch20room3`** (annotated, pushed) — taken at the END of the §Ch20 cavern session, immediately before Room 8, which is the riskiest room in the dungeon (a boulder pushed onto `(5,3)` **permanently seals the exit**). ‼ It is also the natural rollback point if the **promotion decision** below is taken. Older: **`restore/2026-08-13-pre-ki63-promotion`** (annotated, pushed) — taken immediately BEFORE promoting KI-63's fix. Older: `restore/2026-08-13-pre-roster-promotion`, `restore/2026-08-12-pre-ch1819-promotion`. |
| sandbox ↔ custom drift | ⚠ **9 as of 2026-09-02** (⬆ from 8: the NEW `modules/story/sootopolis_gym.py`, §Ch22's chapter module — a new sandbox-only chapter file, exactly as §Ch20 and §Ch21 each did. ⚠ PROMOTION IS THE USER'S CALL and is NOT implied by this row), RE-MEASURED by `promote.py --check`** (‼ the NUMBER is unchanged and that is not staleness: §Ch21 legs 3 and 4 landed in `sootopolis.py`, which was already on the list. That file now carries **all five legs AND the chapter orchestrator**, and as of 2026-09-02 it IS wired into `_play()` (Segment 21) and driven end to end. ⛔ *(This sentence used to read "leg 5 missing, not wired into `_play()` — so it is not a promotion candidate"; BOTH premises are now FALSE.)* ⚠ **Whether it is a promotion candidate is a USER RULING, not something this file may infer** — the standing rule is that nothing is promoted without the user's call, whatever is ruled for the other seven.) Formerly — `modules/battle_action_selection.py` (the `#26-battleitemwedge` bounded bag-open) **+** `modules/battle_strategies/level_up.py` (the `#26-fleefreeze` delegate) **+** `modules/story/mossdeep_gym.py` + `modules/story/early_game.py` (the `#26-*` production fixes, DOUBLE-BATCH-validated, sandbox only — ⛔ NOT a promotion decision until the user rules) **plus** `modules/story/seafloor_cavern.py`, `modules/story/sootopolis.py` (§Ch21 legs 1 + 2a + 2b), **`modules/map_data.py` (NEW 2026-08-27 — the `PokemonCenter.SootopolisCity` member, §Ch21 leg 2a)** and `plugins/custom_modes/story_mode.py`, sandbox only. ‼ The count went 2 → 3 the moment leg 1 landed, and `check_drift` caught SEVEN stale claims of the superseded figure across two files — the gate doing exactly what it was built for. ⛔ NOT a promotion decision yet: §Ch20 is driven but §Ch21 is unbuilt, so the arc is mid-flight.** *(This cell led with "0 … Nothing is owed" for one commit after §Ch20 landed as a chapter — a Tier 1 review caught it, and the cell's own rule is the fix: **run `promote.py --check`, never trust this number**.)* ✅ **Previously 0 as of 2026-08-24** — the whiteout/abort guards were PROMOTED (user-approved) and the forks were EQUAL.** `early_game.py` carried `#24-loopheadabort` + `#24-abortrecoveryresiduals` (b) and (c); custom went 8 AST swallowers → 0, probe 36 → 23. Rollback tag `pre-promote-2026-08-24-abortguards`.** Run `promote.py --check`; it is the authority, never this cell. *(Previously: everything promoted 2026-08-17, USER-APPROVED: `pc_trip.py`, `higher_level_actions.py`, `early_game.py`, `counter_hunt.py`, `map_path.py`: the `#24-orphans` (1) verdict change and the `#24-abortswallow` abort guards. ✅ **THEY WERE SANDBOX-ONLY AND ARE NOW PROMOTED (2026-08-17, user-approved) — NOTHING AWAITS A DECISION.** Everything before it IS promoted, the KI-66 `_on_field` fix included (2026-08-17, user-approved; THREE-POINT A/B; restore point `restore/2026-08-17-pre-promotion-ki66-onfield`) and the KI-65 fix before it (2026-08-16, `restore/2026-08-16-pre-promotion-ki65`). *(Superseded the same day: this cell read "0 — EVERYTHING IS PROMOTED" after the KI-81 guard landed, which was true until the KI-65 fix. ‼ `audit_doc_consistency` did NOT catch it. ⛔ **The reason recorded here was WRONG and is corrected 2026-08-17:** it is NOT digits-vs-words (word forms ARE handled). It walked past `0 as of` because that is a CLAIM and the rule is scoped to an EXPECTATION. *(Hand-grepping word forms is still good advice for a human sweep — just not the gate's defect.)*)* Everything ELSE is promoted, the KI-81 WHITEOUT GUARD included (user-approved). Restore point `restore/2026-08-16-pre-promotion-ki81-abort-guard`. ‼ **Proven by a MEASURED before/after, not a byte-compare:** `probe_abort_swallowing.py --build custom` fell **53 → 45**, custom's guarded-handler counts moved **0→3 / 0→4 / 1→2**, the PathFindingError split survived the copy, and the guard mechanism was re-verified importing from CUSTOM. **History below.** ✅ Previously 0 as of 2026-08-16 — EVERYTHING WAS PROMOTED, including the KI-80 DECOUPLING (a BEHAVIOUR change), user-approved.** Restore point `restore/2026-08-16-pre-promotion-ki80-decoupling`. ‼ **Proven by a THREE-POINT A/B against `--build custom`, NOT a byte-compare** — identical commands: `POKEBOT_KI80_DECOUPLED=1` went **FAIL → PASS**, the coupled expectation went **PASS → FAIL** (the mirror), and **arm 4 stayed PASS on both sides** — that invariance is what shows KI-23's mirror regression did NOT land. ⛔ The BEFORE half is unrepeatable once the copy happens, so it was run and committed FIRST, in `1c11927e`. **History below.** ✅ The earlier **COMMENT-ONLY** correction was promoted 2026-08-16 (user-approved), restore point `restore/2026-08-16-pre-promotion-credible-answer-comment`: the `CREDIBLE_ANSWER_POWER` docstring justified the threshold with *"Thunderbolt vs Winona"*, which is FALSE — Electric is `0.5x` Dragon `x 2.0x` Flying = **NEUTRAL** into Altaria. It is the FIFTH copy of an error whose other four were corrected the same day. ✅ **PROMOTED 2026-08-16, user-approved**, as the earlier comment-only `counter_hunt.py` fix was. ‼ **Proved behaviour-neutral by AST EQUALITY before copying** — `ast.dump(parse(sandbox)) == ast.dump(parse(custom))`, 323,580 chars each — and ⛔ that check was FAULT-TESTED (flipping `CREDIBLE_ANSWER_POWER` 75→76 makes it return False), because a check that cannot fail proves nothing. ⚠ **There is no three-point A/B here and there cannot be**: a comment has no branch to flip, so AST identity + `1/1 byte-identical` is the proof, and the `--build custom` drives only show the file still loads. ⛔ The edit was made **net-zero on line count** so it did not shift the `story_mode.py:NNNN` citations that fill the append-only logs (verified after: `grass_is_fodder` still `:1899`, `winona_fight` still `:3532`). ‼ **That promotion left the tree fully promoted AT THAT TIME** (⚠ historical; the figure is DESCRIBED not reprinted, because the gate cannot tell history from a claim — today's number is at the TOP of this cell); ANY unexplained file is worth stopping for.** **The rest of this cell is HISTORY, kept for its promotion evidence.** ✅ **0 as of 2026-08-15 (the promotion round) — BOTH promotions were DONE, USER-APPROVED, and VERIFIED BY DRIVING.** (1) `modules/story/pc_trip.py` — the KI-79 fix, a **BEHAVIOUR** change, restore point `restore/2026-08-15-pre-promotion-ki79-pctrip`. ‼ **Proven by a THREE-POINT A/B, because 1/1 byte-identical only proves a file was COPIED, never that its new branch is what RUNS:** with `POKEBOT_PCWITHDRAW_FAULT=1` against `--build custom`, the IDENTICAL command went **PASS (hook absent, inert) BEFORE → FAIL (`‼ THE WITHDRAW DID NOT LAND`) AFTER**, and an unfaulted AFTER run still PASSed. Transcripts committed under `tools/story-dev/evidence/`. (2) `modules/story/counter_hunt.py` — the comment-only Electric correction, restore point `restore/2026-08-15-pre-promotion-counterhunt-comment`. Both are also green on four `--build custom` gates that each ASSERT which fork they imported, and on `boxcounter2 --build custom` ARM A. ‼ **MEASURE, don't trust this row** — `promote.py --check` is the authority. *(That round expected 0 AT THAT TIME; today's figure is at the TOP of this cell.)* ⛔ Digits, not words. **The rest of this cell is the PREVIOUS state, kept for its promotion evidence — read "0"/"ZERO" below as *"zero at that moment"*, not as today's figure.** ✅ **0 as of 2026-08-15 (earlier) — every drifted file was PROMOTED, user-approved, and VERIFIED BY DRIVING.** Promoted: `modules/party_accounting.py` (new), `modules/pokemon_party.py`, `modules/modes/util/higher_level_actions.py`, `modules/debug_utilities.py`, `modules/story/counter_hunt.py`. **Evidence:** tool-side drift 0 both directions + 5/5 byte-identical; **`--driver ch20dive --build custom` → `legs=6/6 … ACCEPTANCE: PASS`**, matching sandbox; and FOUR `--build custom` gates (`repro_party_accounting` 33, `repro_heal_piggyback_reporting` 20, `repro_box_counter_move_test`, `repro_pid_identity_key`) each ASSERTING which fork it imported. Restore point **`restore/2026-08-15-pre-promotion-stage0-p4`** (annotated, pushed, verified on origin by the tool before it copied). ⛔ **Digits, not words** — this cell read a spelled-out "THREE" for a day, invisible to `audit_doc_consistency`'s drift check, and it survived two doc passes. ⛔ **What promotion does NOT mean:** party accounting is still STAGE 0 (it observes and decides nothing), `debug_write_box_slot` is PROVEN LIVE (`--driver boxwrite` → PASS, 2026-08-15), and (P4) is driven through **STAGE 2** (`--driver boxcounter2`, 4/4 across both forks, 2026-08-15) — ⛔ *this sentence read "STAGE 2 … is NOT built" until Stage 2 landed the same day; the drift figures around it are historical, this clause is CURRENT.* ‼ **Anything else appearing in `promote.py --check` is unexplained drift and is worth stopping for.** ⛔ The rest of this cell is the PREVIOUS state and is kept for its promotion evidence — read "ZERO" below as *"zero at that moment"*, not as today's figure: ✅ **ZERO as of 2026-08-14 (earlier) — KI-78 STAGE 1 WAS PROMOTED, user-approved, and it is the first promotion executed by `tools/story-dev/promote.py` rather than by hand.** The tool refuses on a dirty tree, a missing or UNPUSHED restore point, a diverged remote, or a no-op, and it re-measures drift in BOTH directions plus byte-equality per file — it also refuses to claim the driven verification it cannot perform. Restore point **`restore/2026-08-14-pre-promotion-ki78`**. **Evidence:** drift 0 both directions, 3/3 byte-identical; **`repro_pid_identity_key.py --build custom` exit 0** and **`repro_box_counter_move_test.py --build custom` exit 0** (both ASSERT which fork they imported before testing); plus a live drive against custom. ⛔ **KI-78 is still not fully closed** — its residual cases (R2 debug-fabricated pairs, R3 corrupt box slots, R5 Frontier rentals, R6 evolved-since-capture) stay open. ‼ **MEASURE, don't trust this row** — `promote.py --check` (in HOW TO RUN / TEST) reports it BOTH ways in seconds — ⛔ **this historical sentence expected 0 because that was true on 2026-08-14; it is 0 again TODAY after the counter_hunt.py promotion — but do not act on a historical sentence, run the command.** 📚 Every earlier drift state — including the 2026-08-13/14 rounds where `map_path.py`, `early_game.py`, `story_mode.py`, `counter_hunt.py` and `pokemon_party.py` were awaiting promotion — moved to `28-HANDOFF-ARCHIVE.md` on 2026-08-14, because stacking four supersessions in one cell made a promoted file read as still pending. |
| **if stopped mid-task** | ✅ **NOTHING IS PARKED MID-TASK (session end 2026-09-02)** — §Ch21 is FINISHED: all five legs AND the `_play()` wiring are built, driven, fault-armed, their fixtures captured and verified, and the docs updated. *(This cell said "session end 2026-09-01 — §Ch21 leg 4 is finished" through TWO further shipments — leg 5 and the wiring — until a Tier 2 cold-start audit caught it. It is the row a resuming session reads FIRST, so it goes stale most expensively.)* No half-edited work, no `/checkpoint` debt. ⛔ **Trust `git status`, not this cell** — a cell cannot truthfully assert its own push. ⚠ What IS outstanding is not mid-task work but the SAME **USER DECISION** as before: drift is **9**, MEASURED by `promote.py --check` on 2026-09-02 — `battle_action_selection.py`, `battle_strategies/level_up.py`, `map_data.py`, `story/early_game.py`, `story/mossdeep_gym.py`, `story/seafloor_cavern.py`, `story/sootopolis.py`, `plugins/custom_modes/story_mode.py`. ‼ **The number did NOT change this session:** leg 3 landed in `sootopolis.py`, which was already on the list. ⛔ *(SUPERSEDED 2026-09-02 — this said `sootopolis.py` is "an UNDER-CONSTRUCTION chapter (leg 5 missing, not wired into `_play()`)"; it is now COMPLETE and WIRED.)* ⚠ Promotion remains a **USER RULING** regardless of how the other seven are ruled. |
| ‼ **`git stash` — KEPT ON PURPOSE (USER RULING 2026-08-13)** | **`stash@{0}` EXISTS, IS NOT YOURS, AND IS KEPT AS A RECORD. ⛔ DO NOT DROP IT.** `WIP on main: e0f723e4` (2026-07-24) — a 14-line Fortree Gym "only ride out a scene that exists" guard. Its substance is ALREADY in today's `early_game.py` (reimplemented during the rotating-gate rewrite), so it is functionally superseded — **and the user ruled that a superseded stash is still a RECORD and dropping it is a destructive act that buys nothing** (`06-DECISIONS-LOG.md`). ⛔ **Standing rule: never `git stash drop` / `clear` / `pop` in this repo.** `pop` is separately banned because it mutates a GLOBAL stack — that is how this stash was disturbed in the first place (`08-MISTAKES.md`). To read it: `git stash show -p "stash@{0}"`, and apply by hand if ever needed. ‼ A stash is invisible to `git status` and to the kit's sync check, which is how it sat unnoticed for three weeks — so `git stash list` belongs in the session-start ritual, to SEE it, not to clear it. |

## 📚 ARCHIVED SESSIONS (§Ch18, §Ch19, promotion/roster, KI-56, hardening) — DETAIL in `28-HANDOFF-ARCHIVE.md`
⛔ **TEN `##` STUBS MERGED HERE 2026-08-17 (`#24-handoffbudget`) — nothing deleted.** The detail has lived in the archive since 2026-08-13; every DISTINCT lesson the stubs kept is below. What went was ten headings and the fact that the two rules below were each written out three and two times, in separate sections.
1. ⛔⛔ **A CHAPTER'S ACCEPTANCE TEST MUST INCLUDE "AND THE BOT CAN CONTINUE"** — a REAL `calculate_path` off the end tile, never a "controllable" flag. **§Ch15 ended four floors underground, §Ch18 on an eleven-tile island, §Ch19 in a living room, and ALL THREE PASSED THEIR OWN TESTS.** KI-56's prevention rule, violated again by §Ch18 the next day. Every §Ch20 driver carries it. Read it before writing any chapter's acceptance test.
2. ⛔⛔ **WHEN N OF YOUR OWN INSTRUMENTS AGREE ON SOMETHING IMPOSSIBLE, THEY SHARE A MISSING PRIMITIVE.** Four agreed the Mossdeep Gym had no route to its own leaders; all four modelled it as *walk + warp* and it has a **third movement primitive** (a rotating-tile statue puzzle). Even the model-free brute-force walker was wrong — it *changed the map while exploring it*.
3. ‼ **EVERY DEFECT THAT MATTERED WAS FOUND BY AN ADVERSARIAL AGENT, NOT BY A TEST** — three times in one session, each over green runs, because *the happy path cannot exercise an error path* and an acceptance test written by the code's author inherits its blind spot. ⇒ **spend agents on REFUTING finished work**, and **write the predicted failure down BEFORE the run.**
* ‼ **CITATIONS AN INDEPENDENT CHECK FOUND MISSING FROM THE MERGE ABOVE, RESTORED 2026-08-17** (it was asked to assume something was lost, and six things were): §Ch18 is wired as **Segment 18** and §Ch19 as **Segment 19**, taking the ladder **19 → 20 of 24**; the flag combination that falsely passed while the bot was stranded was **`badge + controllable`** — that pair IS the false-pass mechanism, which is why rule 1 above demands a real path instead; the batch-result item's tag is **`#24-teachmsgstall`**; **the status tax now has a resolved rate behind it** (the policy is still the USER's call); **KI-56 was resolved 2026-08-11** — one day before §Ch18 violated its rule — and the ISSUE itself lives in **`31-KNOWN-ISSUES-ARCHIVE.md`**, not in `28-HANDOFF-ARCHIVE.md`.
* **§Ch18 + §Ch19 shipped and were PROMOTED** (verified by DRIVING `--build custom`, never a diff), ladder to **20 of 24**; `modules/story/roster.py` (party reorder) landed with them. **KI-64** was fixed after being **wrong twice** (dead code on the story path, then a positional cut in the wrong index space — now keyed on **original trainer ID**); **KI-67** closed both halves, including this project's **first driven whiteout recovery**, proven by the **frame delta** (+7,789 / +7,087), never a count.
* **§Ch19's four gotchas, still true if you touch it:** (1) Mossdeep is **cut in two** until the forced cutscene runs, so leg 1 is two legs; (2) the stair grunt **must be talked to** (`sight_radius = 0`, on the only reachable tile); (3) the party-selection menu is **driven, not mashed** — A on an already-picked mon DESELECTS it, every pick verified against `gSelectedOrderFromParty`; (4) **losing is a RETRY, not an error** — the script calls `SetCB2WhiteOut` itself and leaves the var at 2.
* ⛔ **THE BOSS/STATUS BATTLE-POLICY CHANGE IS STILL THE USER'S CALL** and must not be built unilaterally — a status response touches every mode. And "roster hygiene before bosses" was **RETRACTED**: it was said to be one `POKEBOT_BOX_OVERFLOW_CATCH` flag and one text box away and **both halves are false** — that flag has defaulted **ON** since 2026-08-07, the text-box blocker was refuted the same day, and four docs repeated it from a **stale code comment** instead of the default twenty lines below it.
* 🛡 **The hardening round** (advisory rules → code that refuses) came from **≥12 of 164 logged mistakes being self-admitted REPEATS**, several committed while the author knew the rule — and **three of those tools found real problems on their first run** (six competing START-HERE banners, an 11th undocumented flag that turned out to be the roster blocker, 140 silent handlers). **Run `preflight.py` before touching anything**; read `29-DISABLED-FEATURES-REGISTRY.md` before proposing any `POKEBOT_*` flag.
* 🛠 **TWO GATES WERE BLIND, AND FIXING THEM FOUND A REAL BUG.** `audit_flag_names.py` checked **two files** and saw only names written as literals AT the call site, while the house idiom is a module constant — **blindest exactly at the completion markers**; now 19 files / 144 names, **exits 1** on a phantom. And **`pyflakes` was installed and had never been run**: the new `repro_undefined_names.py` found a `NameError` on the Magma Hideout's *success* path, plus KI-65. ⇒ *a gate that has never failed may simply not be looking.*
* ‼‼ **THE ADVERSARIAL REVIEW THAT FOUND MY §Ch19 FIX WRONG TWICE:** (1) **print the MRO before "fixing" a strategy method** — the first fix guarded the base class and was DEAD CODE on the story path; (2) **never identify a Pokémon by party INDEX across a battle-menu boundary** — opening it runs `UpdatePartyToBattleOrder`, which PHYSICALLY PERMUTES `gPlayerParty`, so the `index >= 3` cut offered the ALLY's mon and hid one of ours; key on **original trainer ID**. ‼ Meta-lesson: **my fault-injected A/B passed it anyway** — all three arms modelled the un-permuted order, and *a control arm does not save you if every arm measures the wrong thing.*

## ‼‼ §Ch19-ERA ISSUES — **MIXED: KI-64/65/67 CLOSED; `KI-66` IS *PARTLY FIXED* (its `_on_field` half is FIXED AND PROMOTED; its OWNER filter is OPEN)**
*(the CLOSED detail moved to `28-HANDOFF-ARCHIVE.md` 2026-08-13; ⛔ the heading used to read just
"MOVED to the archive", which buried the next work item's ONLY description inside a section a
reader skips — a cold-start audit caught it 2026-08-16, and it is the exact `#24-orphans` shape.)*

Moved for the R3 budget; all four are in `05-KNOWN-ISSUES.md` or its archive with full detail. ‼ **Keep only what is still live:** ✅✅ **KI-65 is NO LONGER LIVE — REPRODUCED, FIXED, A/B-PROVEN AND GATED (#25) ON 2026-08-16; ⛔ DO NOT REBUILD OR REOPEN IT** (and PROMOTED to both forks 2026-08-16, user-approved). *(It was: `battle_move_replacing.py:280` binds `party_index` on a path a silent `except` can skip, so a later `CantForgetHM` raised `UnboundLocalError` into a SECOND silent `except` that declined — two invisible failures compounding. Both reads now carry explicit `is None` guards.)* **KI-66 — OPEN and CODE-VERIFIED** (⛔ an older half of this line said "unverified"; the four sites were read and confirmed live): the multi-battle hazard is broader than the faint chooser — four more full-party scans on the same paths (`battle_handler.py:541-545`, `:588-598`, `:630-636`, `_util.py:522-587`). ⛔⛔ **THE `IndexError`-ON-TURN-1 SUB-CLAIM IS *REFUTED*, NOT PENDING — DO NOT "CHECK THAT FIRST".** `05-KNOWN-ISSUES.md` refuted it on 2026-08-12 from our own driven run (`ch19d.log` f23255: a SIX-entry party with the multi battle WON — `FillPartnerParty` does update the count). *(This line ordered "check that FIRST" for four days after its own KI file refuted it; a cold-start audit priced that at an hour of re-refuting.)* ‼ The right fix is ONE choke point (`ally_party_indices()`, which EXISTS at `battle_strategies/default.py:12` and is called from `default.py:189` / `level_up.py:53` / `story_mode.py:171` — and from NONE of the four sites). ✅✅ **BUILD IS NO LONGER BLOCKED — SUPERSEDED 2026-08-17.** *(It read: "no anchor save reaches a partner double battle with a player faint, and no fault hook forces one".)* **BOTH EXIST NOW:** `--driver ki66faint` on `saves/at_steven_2f.ss1`, with the faint produced by staging one of our picks at 1 HP before the battle. Driven three times. ⛔ The headline is REFUTED and the `_on_field` index-space defect it exposed is **FIXED AND PROMOTED TO BOTH FORKS (2026-08-17)** — ⛔ do NOT redo it. What stays LIVE is the OWNER filter (measured INERT on our one fixture), `:541-545` and `_util.py:522-587`. See KI-66's DRIVEN block. KI-64 and KI-67 are CLOSED.

## 🆕 THE REGI ARC (user-requested) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13). See **KI-69**.

Moved for the R3 budget; the arc is **NOT STARTED**. ⛔ *(This read "the arc is item 4 in NEXT ACTIONS"; that pointer is DANGLING — this file's own queue preamble says the surviving items are only `0`, `1` and `3b`, and that **item 4 never existed**. Caught by the 2026-09-02 Tier 2 cold-start audit.)* ‼ **Keep these four, every one of which fails SILENTLY if got wrong:** (1) **Emerald REVERSED the party order — WAILORD first (slot 0), RELICANTH last** (`braille_puzzles.c:92-104`); the R/S order everyone remembers is wrong and the wrong order gives no message and no error. (2) ⛔ **The Regi battle is UNRECOVERABLE** — level 40, catch rate 3, and the fall-through case **including `B_OUTCOME_LOST`** sets `FLAG_DEFEATED_*`, so **a KO *or* a whiteout deletes the encounter permanently**; the only safe non-catch exit is fleeing. (3) **REGICE IS NOT A TIMED WAIT** — Emerald wants a **36-tile perimeter lap in ONE visit** ending exactly on `(8,21)`, reset by any map transition and by one wrong tile. (4) Measured capability gaps: **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or Flash — and **Relicanth is underwater-only, so Dive is upstream of the whole arc.** Ground truth: `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md`.

## ⏭ NEXT ACTIONS, IN ORDER

> **The ordered work queue** (the cold-start orientation is the ‼ YOU ARE HERE block at the top of
> this file, not here). Everything is committed and pushed **as of the commit carrying this line** —
> trust `git status` over this sentence. **No work is parked MID-TASK** (nothing half-edited, no
> `/checkpoint` debt). ⛔ *(This used to add: "that is NOT the same as nothing is parked — §Ch20 chapter assembly IS
> parked ... (item 0)". **RETIRED 2026-09-01: §Ch20 SHIPPED AS A CHAPTER 2026-08-24**, so that
> pointer sent a cold reader to item 0 to finish work that had already shipped. ⇒ nothing is parked MID-TASK **and** no chapter is parked awaiting assembly; what IS outstanding is the drift promotion, which is a USER DECISION, not parked work.)*
>
> 0. ‼ **THE LIVE QUEUE (updated 2026-08-14) — DO THESE FIRST; ⛔ items 2-4 NO LONGER EXIST (archived 2026-09-01) (item 1 is the ritual and is NOT older framing; item 5 was archived 2026-08-17).**
>    ‼ NEW STANDING RULE FOR EVERY ITEM BELOW: doc edits run Tier 0 (`lint_docs` +
>    `audit_doc_consistency`, both exit 0) before their commit, and a completed item gets a
>    Tier 1 independent review of its doc diff — see `CLAUDE.md`'s DOC CONSISTENCY LAYER.
>    ✅ **✅ (a) (b) (a2) (a3) (a4) ARE ALL DONE, AND (c) IS OBSOLETE — eve…** 📦 ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3
>    budget; CLOSED, nothing deleted).
>    ⛔⛔ **THE USER REDIRECTED PRIORITIES ON 2026-08-14, AFTER Room 9 landed. §Ch20 CHAPTER
>    ✅✅✅ **QUEUE ITEM 0'S AUGUST WORK IS ALL DONE — ⛔ DO NOT RE-RUN ANY OF IT.** Detail moved
>    to `28-HANDOFF-ARCHIVE.md` 2026-09-01 (line budget). Still open there: `#24-abortrecoveryresiduals` (a) and (c).
>    ✅✅✅ **§Ch21 IS FINISHED — ALL FIVE LEGS *AND* THE `_play()` WIRING. ⛔ DO NOT REBUILD ANY
>    PART OF IT, and do NOT re-run the leg-5 PART C probe.** Drivers `ch21dive` / `ch21escort` /
>    `ch21cave` / `ch21approach` / `ch21climb` / `ch21return` / `ch21chapter`, every one
>    `ACCEPTANCE: PASS`, with 3 + 7 + 6 fault arms, and the fixture chain `post_ch20` →
>    `post_sootopolis_arrival` → `post_steven_escort` → `post_wallace` → `post_skypillar_door`
>    (md5 `f6f8ab116b1bc18644286f51c2f202c6`) → `post_wallace_scene` → `post_skypillar_summit` →
>    `post_rayquaza_gone` (`35cb5e6502fd613fb7460e27aa79fd68`) → **`post_hm07`** all PINNED.
>    ⛔ **RETIRED FROM THIS QUEUE 2026-09-03 (56 lines → this block) — SUMMARISED AND POINTED AT,
>    NEVER DELETED**, because §Ch21 is done and its detail was crowding out the LIVE item while
>    this file sat at its 900-line cap. The full narrative is in `07-CHANGELOG.md` 2026-09-01/02,
>    `12-STORYMODE-DESIGN.md` §Ch21, and `ai-research-notes/2026-09-02-ch21-leg5-{RECON,PARTC-
>    PREDICTIONS,PARTC-RESULTS}.md` + `2026-09-02-ch21-chapter-wiring-BUILD-SPEC.md`. Also spent and
>    archived there: leg 3's four pre-build results (the pocket exit's resting tile **(31,17)**, the
>    Sky Pillar `*_CLEAN` layout ruling gated on `VAR_SKY_PILLAR_STATE < 2`, the ROUTE131 SET-B gate
>    = layout **#318**, and leg 5's PART C validation of both load-bearing gates).
>    ‼ **THE THREE RULES §Ch21 PAID FOR IN LIVE DRIVES, WHICH §Ch22 MUST NOT RELEARN:**
>    (1) **a continuation check is only as good as the continuation it NAMES** — leg-5 drive 1
>    printed PASS holding HM07 while §Ch22's own gym warp (31,32) was SEALED, because the check
>    pointed at the Poké Center, which is reachable either way; (2) grade on POSITION **plus** a
>    live `calculate_path`, NEVER on vars alone — a whiteout respawns in Sootopolis where the vars
>    still read (5,1,1); (3) a resume/phase selector must match POSITION **and** state together.
>    ‼ And one MEASURED fact §Ch22 inherits directly: at `SOOTOPOLIS_CITY_STATE=5` /
>    `SKY_PILLAR_STATE=3` the Sootopolis layout pin is a **NO-OP**, and the only 10 live-vs-static
>    differing tiles are the **GYM plus nine HOUSE door warps**, locked by `SootopolisCity_OnLoad`
>    until `FLAG 0x9E` — a STORY state, not a layout bug. ⇒ §Ch22's own front door is one of them.
>    ✅ **DEEP SANITY CHECK 2026-08-27 — PASSES 1-2 OF 5 ONLY** (a 20-agent fan-out was ruled too
>    costly). 5 gate defects + 13 stale-prose contradictions fixed, fault-proven. ⛔ **PASSES 3-5
>    ARE UNRUN, filed as `#24-sanitycheck2` — do them CHEAPLY, NEVER as a 40-agent fan-out.**
>    ✅ **`03-PUNCH-LIST.md` HAS HEADROOM AGAIN (2026-09-02): `#24-abortswallow` was RETIRED 101 → 21 lines.** Its "36 CANDIDATES REMAIN" headline was STALE and only LOOKED like it contradicted "AST finds ZERO" — settled by RUNNING `probe_abort_swallowing.py` first (23 in BOTH forks, at baseline, PASS; a CANDIDATE is not a defect). Nothing was deleted: six changelog entries carry the narrative and the load-bearing rule is a code comment. ⛔⛔ **BUT `04-HANDOFF.md` IS STILL AT ITS CAP, SO THE NEXT EDIT THAT GROWS *THIS* FILE TURNS TIER 0 RED** (`lint_docs.py` fails at `lines > budget`). ⇒ **the next session's FIRST act is a retirement in BOTH files**, done the documented way (SUMMARISE + POINT at `07-CHANGELOG.md`, never delete). ⛔ **RUN `lint_docs.py` FOR THE LIVE NUMBERS — none are quoted here on purpose.** *(A first draft of this very line hardcoded two counts, inside a clause telling the reader to measure rather than repeat; a Tier 1 reviewer pointed out it was reproducing the anti-pattern it warns about. This file's own §LINE BUDGETS section already had the right convention.)* *(This line read "CLEARED … 3575 of 3600 (25 lines of headroom)" for about an hour; filing `#24-ch22juan` consumed it. ⇒ measure the number, never repeat it.)* *(This read "IS AT 3600 OF ITS 3600-LINE BUDGET (ZERO HEADROOM)" — a hard precondition raised by the Tier 2 audit. It was cleared once by COMPRESSING `#24-crackedfloorpathfinder`, whose §Ch21 half was refuted AND has since shipped, down to its surviving POST-GAME blocker; nothing was deleted.)* ‼ **NEXT RETIREMENT CANDIDATE, AND A QUESTION THAT MUST BE ANSWERED FIRST:** `#24-abortswallow` is 101 lines and its arc reads CLOSED (8 sites fixed and promoted to both forks, the probe gated as a ratchet) — **but its own headline still says "⛔ 36 CANDIDATES REMAIN (ALL `early_game.py`)" while THIS FILE says the class is closed with "AST finds ZERO" and the ratchet at 23.** ⛔ Those may be measuring different things (candidates vs defects) or may be a genuine contradiction. **Settle it with `probe_abort_swallowing.py` BEFORE compressing the item** — I deliberately did NOT compress it, because silently resolving a contradiction you do not understand is how detail gets lost. ⚠ **25 lines is still TIGHT** — enough for one §Ch22 item, not for a chapter's worth of findings, so the next growth still needs a retirement first.** `lint_docs.py` fails at `lines > budget`, so **the first edit that GROWS that file turns Tier 0 RED and blocks the commit** — and adding a §Ch22 item grows it. ⇒ **RETIRE A COMPLETED ITEM FIRST, the documented way: SUMMARISE + POINT at `07-CHANGELOG.md`, NEVER delete** (code and gates cite these slugs). `04-HANDOFF.md` (~15 spare lines) and `05-KNOWN-ISSUES.md` (~16) are tight too. *(Raised here by the 2026-09-02 Tier 2 cold-start audit, which called it a blocker that must be cleared before the first recon agent returns — otherwise a cold session meets it as a red gate mid-commit.)*
>    ➡➡➡ **NEXT ACTION: §Ch23 — VICTORY ROAD** (`chapters.py:259-262`, graded on `DEFEATED_WALLY_VICTORY_ROAD`). ⛔⛔ **§Ch22 IS FINISHED: chapter, Segment 22 wiring, `ACCEPTANCE: PASS` (`frames=64563`, `b1f_steps=19`, `battles_on_B1F=0` with `b1f_entered=True`, `CONTINUE=23`, `RECOVERIES 1`), and BOTH fault arms exercised. DO NOT REBUILD ANY OF IT.** ‼ Two things §Ch23 inherits: (1) **the Juan fight is stochastic — 5 wins and 1 LOSS over six distinct RNG draws — and the chapter recovers by design**, so a story run may spend an extra ~35k frames there; (2) ⛔ **KI-47 can freeze the shared battle path inside that fight** (`handle_battle_action_selection`, 3,001 frames, drop to Manual with NO `ACCEPTANCE` line) — it now has a deterministic repro command in KI-47, and it is NOT §Ch22's to fix. Detail: `07-CHANGELOG.md` 2026-09-03 (Juan, then chapter), `ai-research-notes/2026-09-03-ch22-CHAPTER-{PREDICTIONS,RESULTS}.md` (the predictions were filed BEFORE the orchestrator existed, commit `f372a780`, and are graded item by item — ⛔ the one rated HIGH missed and the one rated RISKIEST held), plus `12-STORYMODE-DESIGN.md` §Ch22 and `#24-ch22juan` / `#24-ch22chapter`, both CLOSED. ⛔⛔ **THE ENTIRE §Ch22 BUILD LOG THAT USED TO FOLLOW HERE IS RETIRED (2026-09-03) — SUMMARISED AND POINTED AT, NEVER DELETED.** It had grown to ~10,000 characters of chronological append on ONE line, and by the time the chapter shipped it still carried, as live text: *"SO THE NEXT ACTION IS NOW §Ch22 CHAPTER ASSEMBLY"*, *"a descent helper is still owed"*, *"NO DRIVER HAS EVER RUN `walk_the_ice → fight_juan → fall_to_b1f` COMPOSED"*, *"SAMPLED — 4 WINS OUT OF 4"* and *"the chapter must be heal → stock → ice → Juan → fall/B1F/out"* — **five statements the same day's work had already falsified.** ⇒ ‼ **A CHRONOLOGICAL APPEND-LOG INSIDE A CURRENT-STATE FILE ROTS FROM THE MIDDLE**, because each new clause is true when written and nothing ever revisits the ones above it. Retire a chapter's log the moment the chapter ships. ‼ **The three §Ch22 facts worth carrying forward are already stated ABOVE this sentence** (the fight is stochastic and the chapter recovers; KI-47 can freeze it and is not §Ch22's; the ladder is 23 of 24) — everything else is in the changelog and the notes.

>    **Parallel build list:** `#24-roster` WITHDRAW half (the named Treecko run-ender), the
>    FaintedMonTry KI-47 family, `#26-surfteachchain` D3-D6, `#26-gatestartupcontention` fix,
>    the harness run-header `driver:` line.
>    *(D3 recon note: `ai-research-notes/2026-08-26-d3-forgetmenu-cursor-decomp.md`; contention
>    diagnosis: `#26-gatestartupcontention`.)*
>    ⛔ Batches answer FREQUENCY, drivers answer CORRECTNESS — fixes get proven by targeted
>    drivers, never by another batch.
>    ➡ *(previous)* the promotion is DONE 2026-08-24 — the USER's call (drift 0 — promoted 2026-08-24). ⛔ **When it lands, lower `probe_abort_swallowing.py`'s custom baseline 36 → 31 in the
>    SAME commit**, or the ratchet re-permits 5 sites of debt in the fork that ships.
>    ✅✅ `#24-brokenrepros` and `#24-p2headergate` are both **DONE (2026-08-23) — ⛔ do NOT
>    re-do either.** brokenrepros fixed SIX repros, not the five filed, and spawned
>    **`#24-reprosweepratchet`** (the repros are not in the standing suite, so they rot — the
>    same script was written off as "environmental" TWICE). p2headergate added 2 checks inside
>    existing gates and deliberately DELETED a third; ⛔ **do not resurrect the deleted check**
>    — the long note at its former site in `audit_doc_consistency.py` says why, and it cost six
>    review rounds to learn.
>    ⚠ **`03-PUNCH-LIST.md` RUNS CLOSE TO ITS 3600-LINE CAP** — it was AT the cap earlier on
>    2026-09-01. ⛔ **NO FIGURE IS QUOTED HERE ON PURPOSE.** A previous version wrote "3,582"
>    and the very commit that wrote it added 7 more lines to that file, so the figure was stale
>    before it was pushed — the exact failure the next sentence warns about, committed inside
>    the warning itself. `wc -l` is the only authority. ‼ Re-derive with `wc -l` LAST, never trust a
>    written figure (one drifted by 4 lines because it was measured before the final edits).
>    **THE NEXT EDIT THAT GROWS IT MUST FIRST RETIRE A COMPLETED ITEM** — candidates: older ✅
>    `#24-*` blocks, and the mined `#26` entries (the batch section keeps their numbers).
>    ⛔ **Retire by SUMMARISING + POINTING at `07-CHANGELOG.md`, never by deleting**: code and
>    docs cite these slugs and `audit_doc_citations.py` goes red if one vanishes. `03` is a
>    CURRENT-STATE file, so summarising finished work is maintenance, not loss.
>    ✅✅ **`#24-difftriggeredrules` IS DONE 2026-08-26 — ⛔ DO NOT REBUILD IT.**
>    `advise_on_diff.py` (9 diff-keyed rule families, ADVISORY — exit 0 either way) + the
>    fail-open `advise-on-commit.ps1` PreToolUse hook. ⛔ It deliberately emits NO
>    `permissionDecision` — an "allow" would auto-approve past the user's prompt
>    (`06-DECISIONS-LOG.md`). 32-check self-test, mutation-proven; an adversarial review kicked
>    back v1 and both defects are fixed. Detail: `07-CHANGELOG.md` 2026-08-26.
>    ✅✅✅ **§Ch20 SHIPPED AS A CHAPTER 2026-08-24 — ⛔ DO NOT REBUILD.** Detail archived
>    2026-09-01; narrative in `07-CHANGELOG.md`.
>    ➡ **BEST NEXT ITEMS, in order:**
>    1. **`#24-harnesswhiteoutdrop`** — 10 of 36 whiteout drops unresolved (26 were expected non-story-driver drops; the run header lacks `driver:`)
>       after a whiteout. Any result measured after that point is suspect, so this taints EVIDENCE.
>    2. **`#24-reprosweepratchet`** — what the standing suite does not run, rots.
>    ⚠ `#24-pluginwhiteoutnoyield` is UPSTREAM and currently a no-op for us — low priority, but do
>    NOT fix it in the pristine mirror.** ⛔ **NOT
>    `#24-ki76correctness`: its only fixture is VACUOUS for its only live defect** (ROOM6 has zero
>    armed dismount chains) and a run there would REFUTE a true finding. Read that item's STOP block
>    before planning anything on it. *(Formerly: pass 4/5.)* (2026-08-22: three gates that
>    could not fail, an unbounded runner, seven state-writing probes, and the `git add` hook's 8
>    bypasses — all fixed; see `07-CHANGELOG.md`). ✅ **PASS 5 IS DONE TOO (2026-08-23) and its scope — which
>    did not exist when filed — is now RECORDED in `#24-sanitycheck`, so the audit is reproducible.**
>    ⛔ **The standing lesson: VERIFY EVERY AGENT FINDING YOURSELF.** Across all five passes, agent
>    claims failed my check three times, and one finding was already STALE ON ARRIVAL (it reported a
>    gate red that had been fixed while it ran).** ‼ Method, and it is the whole reason they
>    worked: 8 agents per pass, ONE ANGLE EACH, every one required to **FAULT-INJECT or RE-DERIVE,
>    never to reason**. ⛔ Verify every finding yourself — 2 of ~40 were false positives.
>    ➡ **THEN the standing item is `#24-ki76correctness`** — ⛔ its planner-side half is VACUOUS ON
>    THIS ROM (measured, 54,990 calls; `(14,8)` is a dead end, so a COST test is vacuous too), so
>    it is BLOCKED ON REALITY. The DISMOUNT defect is unconfirmed and needs its own fixture.
>    ⚠ The DISMOUNT defect is still UNCONFIRMED and needs its OWN fixture (Room 7 has no driver).** ✅✅ **`#24-orphans` IS NOW FULLY DISPOSED OF — (5) and (6) both closed 2026-08-17;
>    ⛔ DO NOT REBUILD EITHER.** (5): its premise was REFUTED — `compare_runs.py` already existed and
>    already paired, but was MEASURED BLIND to `ACCEPTANCE:`, so an `A/B DISCRIMINATION` axis shipped
>    instead of the requested wrapper. (6): the ORPHANING is what closed — KI-76's correctness half
>    had no item anywhere and now has one; **its DEFECTS remain OPEN**, measured and specified in
>    `#24-ki76correctness`. Of the six, (1) and (3) stay PARTLY DONE `[~]` (both blocked as before:
>    (1) on an unmeasured heap offset AND the USER; (3) on needing its own discriminator).
>    ‼ **READ `#24-ki76correctness` FIRST — this handoff deliberately does not restate its numbers**,
>    because restating a spec is how the last three items acquired a second, drifting copy.
>    ⛔ **REMOVED 2026-08-18 — this said the item's next step was "startable with zero input"
>    using `--driver ch20room6` + `saves/post_dive.ss1`. BOTH HALVES ARE WRONG NOW:** that arm
>    is the ROOM6 / ends-on-warp one, which is MEASURED VACUOUS, and `post_dive.ss1` is
>    VOLATILE (the pinned copy is `post_dive_ki76.ss1`). A cold-start audit caught it pointing
>    a next session at the vacuous arm.
>    ⚠ **ALTERNATIVES, all filed and all startable with zero input:** `#24-probecountgate` (teach the
>    doc gate to grade probe counts — the third un-gated number class to go stale in one session),
>    ~~`#24-loopheadabort`~~ (✅ DONE 2026-08-23 — ALL 17 loops patched, gate #30; an earlier 3-loop exclusion was refuted and withdrawn),
>    `#24-ki59archiveheader` (three files disagree about whether KI-59 is open; `05` is right), and
>    ~~`#24-plainenglishstale`~~ (✅ BROUGHT CURRENT 2026-09-03 — it was three weeks and two chapters behind, not two days; ‼ it has no punch-list item, only this citation).
>
>    ➡➡ **THEN: `(P4c) #24-orphans` — MIXED: ✅ (2) KI-65, (4) log-collision, (5) the
>    `compare_runs.py` A/B axis and (6) the KI-76 shelving are DONE; `[~]` (1) and (3) PARTLY DONE
>    ((1) instrumentation shipped, REACTION half open; (3) KI-66 `_on_field` FIXED+PROMOTED,
>    OWNER-filter half open); **NOTHING in this item is plain OPEN any more.**
>    ⛔ **(6) closed the ORPHANING, not the DEFECTS** — KI-76's two defects live on in
>    `#24-ki76correctness` and are the queue head above.**
>    ‼ **Cost order and STARTABILITY order differ, and the item lists only cost.** (1) is costliest
>    (no caller acts on `withdraw_from_box`'s verdict) but SPLITS: the INSTRUMENTATION half is fully
>    specified — return a verdict, bind it at its ONE caller (`modules/modes/util/higher_level_actions.py:420`), report
>    it, assert it two-armed with `POKEBOT_PCWITHDRAW_FAULT` — while the REACTION POLICY needs the USER.
>    ‼ The discriminator is real: today BOTH arms return `None` to the caller (that is the bug);
>    after the change they return True/False. ⇒ ✅✅ **(2) KI-65 IS DONE — REPRODUCED, FIXED, A/B-PROVEN AND GATED (#25) ON 2026-08-16. ⛔ DO NOT REBUILD OR REOPEN IT** (and PROMOTED to both forks 2026-08-16, user-approved). ⇒ **(3) KI-66 — ✅✅ **DRIVEN 2026-08-17 — `--driver ki66faint` IS BUILT AND WORKS. ⛔ DO NOT REBUILD IT.** It subclasses `SpaceCenter2Mode`, stages one of our own picks at 1 HP (two bytes, `data[86:88]`) so it faints in real combat, and carries a PROVEN guard against overwriting the unpinned fixture `post_space_center.ss1`. ⛔⛔ **AND THE HEADLINE IS REFUTED: the bot NEVER ATTEMPTED an ally slot.** Ally slots sat in `alive_slots` on both faints, but the chooser ASKED FOR slots 2 then 3 — both ours — because `choose_new_lead_after_faint` already filters allies. ‼ **A CANDIDATE IS NOT AN ATTEMPT**, so an A/B fixing only the owner filter shows NO DIFFERENCE here and could make it WORSE (it empties `alive_slots` and trips a FALSE 'no eligible replacement'). ‼‼ **THE REAL DEFECT IS `_on_field`'S INDEX SPACE** — field-order `gBattlerPartyIndexes` compared against a party `UpdatePartyToBattleOrder` has already permuted; it excluded Swellow while Swellow was on the BENCH (proven by its send-out at `f21009`), costing **1263 frames vs 59** on a clean faint. ⇒ **✅✅ **`_on_field`'s INDEX SPACE IS FIXED AND PROMOTED TO BOTH FORKS (2026-08-17, user-approved). ⛔ DO NOT REDO IT.** Direction MEASURED first by an observe-only probe, then applied; all gates PASSED when that landed (**25** at the time — ⛔ the CURRENT count is deliberately not repeated here; `run_gates.py` prints it and IS the authority. This sentence has now been stale at 25 AND at 26 — ⛔ `run_gates.py` prints its own count and IS the authority, never this sentence). ➡ **NEXT: the OWNER filter is still unfixed and proved INERT on this fixture — it needs its OWN discriminator, not this one. `:541-545` and `_util.py:522-587` are also untouched.** Read KI-66's DRIVEN block first. *(superseded: "BUILD-READY" — it is now BUILT AND DRIVEN.)* Earlier recon, PARTLY SUPERSEDED — read the refutation above before acting on any of it:** ✅✅ **BUILD-READY AS OF 2026-08-16 — the two blockers are CLOSED by recon; read KI-66's `RECON 2026-08-16` block FIRST.** The FIXTURE existed all along and was merely undocumented: **`--driver spacecenter2`, anchor `saves/at_steven_2f.ss1`**, drives the real six-mon multi battle. The FAINT needs no new capability and no `gBattleMons` writer: **pre-stage one selected mon at 1 HP before the battle** (1, not 0 — a 0-HP mon is never SELECTED) and it faints in real combat. ⛔⛔ **REFUTED 2026-08-17 BY THE LIVE RUN — this block used to claim the ally case "needs all three of ours down = the LOSS condition". BOTH HALVES ARE FALSE:** only TWO of ours were down (Swellow was alive on the BENCH, sent out at `f21009`), and in a multi battle the side is `gPlayerParty[0..5]` — ours AND Steven's — so that is not the loss condition at all. The run WON, `whiteouts=0`. See KI-66's DRIVEN block. ✅ **Grade instead on the ATTEMPTED SLOT INDICES + refusal count on a SINGLE faint**, which `:630-636` reaches while two of ours are still alive. ⚠ ARM B's behaviour when only ally mons remain is a USER POLICY call. ✅✅ **THAT DRIVER EXISTS: `--driver ki66faint` was BUILT, DRIVEN and PROMOTED-ADJACENT on 2026-08-17 — ⛔ DO NOT REBUILD IT.** *(This clause used to read "Its first deliverable is a `ki66faint` driver … Nothing has been driven live yet", which was true when written and became the last thing a skimmer read on a line whose own headline says DRIVEN. A cold-start audit flagged it.)* What remains of KI-66 is the OWNER filter (measured INERT on our one fixture, so it needs its OWN discriminator), plus `:541-545` and `_util.py:522-587`. *(Tracked alternatives: `#24-zerokocounter`, which needs TWO new arms
>    plus a frequency measurement before anything ships; or (P5), the catch-policy round.)*
>    *(The detailed HOW-TO for this decoupling — the mirror-regression mechanism, the arm-4
>    fixture arithmetic, and the measured proof that the 3-arm suite alone would have blessed
>    the naive edit — is ARCHIVED in `28-HANDOFF-ARCHIVE.md`. The work is DONE; the reasoning
>    survives in `06-DECISIONS-LOG.md` and KI-80.)*
>    ✅ **✅ (i) `counter_hunt.py` and (ii) KI-79 `pc_trip.py` are BOTH…** 📦 ARCHIVED VERBATIM `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3).
>    ✅ 4 DONE ((2) KI-65, fixed+gated 2026-08-16; (4) the log collision; (5) the `compare_runs.py` A/B axis, 2026-08-17 — its premise REFUTED first; (6) the KI-76 shelving, 2026-08-17), 2 PARTLY DONE `[~]` ((1) instrumentation shipped / REACTION half open; (3) KI-66 `_on_field` FIXED+PROMOTED / OWNER-filter half open), and ⛔ NOTHING plain OPEN. (6) closed the ORPHANING; KI-76 defects live in `#24-ki76correctness`.**
>    ⛔ "SIX" is the FILING count, not the open count. (Full list in `03-PUNCH-LIST.md`.) ‼ **Four of the six were recorded inside
>    a document half marked DONE or ARCHIVED** — a CLOSED KI's body, an "older framing" block, a
>    research note — which is the P2 header-vs-body failure applied to TRACKING. Highest cost:
>    **no caller acts on `withdraw_from_box`'s verdict** (KI-79 made the message honest; production
>    still cannot REACT), plus **KI-66**, OPEN and code-verified and absent from
>    every queue. *(✅✅ **KI-65 was the other one and is now DONE** — fixed and gated 2026-08-16; ⛔ do not re-open it.)* ⛔ **Each is a real defect — but "cheap to pick up" was WRONG for KI-66 and is corrected:** its own entry defers it as *"a battle-layer refactor touching every mode"*. (1) needs a heap-offset MEASUREMENT; (3) is DRIVEN as of 2026-08-17 and its `_on_field` half is FIXED **and PROMOTED to both forks** — ⛔ do NOT redo it. Its remaining residual is the OWNER filter (measured INERT on the one fixture we have, so it needs its OWN discriminator), plus `:541-545` and `_util.py:522-587`.
>    🔜 **(P5) The CATCH POLICY round** — the user CALLED it (`06-DECISIONS-LOG` 2026-08-14,
>    rulings A-D): a **LIVING DEX**, per-run, breadth with depth as the payoff. Gate lifted on
>    `#24-organicteam`. ⛔ The RARE leg is blocked on `#24-rarepredicate`, whose fix is now
>    specified (HM-gating + location count, NOT warp depth — the user's Bagon/Feebas reasoning).
>    Trade evolutions are a SANCTIONED non-faithful deviation with four conditions attached.
>    ⛔ **(P6) TRAINING-AREA MAPS — CLOSED. Its investigation became KI-80, which is now FIXED AND
>    PROMOTED TO BOTH FORKS. ⛔ DO NOT REOPEN OR REBUILD IT.** Full history in
>    `28-HANDOFF-ARCHIVE.md`. ‼ **THREE RULES SURVIVE AND ARE STILL LIVE:** (1) ⛔ **do NOT add a row
>    to `TRAINING_GRASS`** — `best_training_area` ranks ONE GLOBAL table, so a new row near L29-33
>    changes the pick for every other caller including `counter_hunt.py:647`'s candidate picker for
>    EVERY boss (the measured Shoal Cave incident, `08-MISTAKES.md`); (2) **Norman's L3-5 patch
>    against a L27-31 band is DELIBERATE** — it is the FODDER TRIGGER for the only training
>    relocation this bot has ever performed (70-83% measured); "correcting" it would disable that;
>    (3) giving a boss a patch is now SAFE for the counter machinery (that was KI-80) but still
>    interacts with (1) and (2).
>    ✅✅ **NOTHING IS LEFT HERE — KI-80's decoupling is BUILT, DRIVEN, REVIEWED AND PROMOTED TO
>    BOTH FORKS (2026-08-16). ⛔ DO NOT REBUILD IT.** *(This block commanded it as live work for
>    hours after it shipped, 58 lines below a banner marking it DONE — a cold-start audit caught it
>    and called it the most expensive defect in the file, because NEXT ACTIONS is what an agent
>    EXECUTES from.)* The residual is `#24-zerokocounter`, tracked in `03-PUNCH-LIST.md`.
>    ⛔ **DO NOT BUILD THE REPRO FROM THIS HISTORICAL BLOCK.** Its conditions and its fixture were
>    both superseded on 2026-08-15. **The authoritative version is the queue head above** (and
>    KI-80's 9-condition table). In one line: `losses` must be **6-11**, and the fixture must pass
>    **BOTH** condition 7 (NO_ANSWER) **and** condition 9 (`team_max <= wild_max + 8`) — which
>    `ch13_fortree_door.ss1` does NOT, despite passing 7.
>
>    ⛔⛔ **RETIRED 2026-09-01 — DO NOT DO THIS. §Ch20 SHIPPED AS A CHAPTER ON 2026-08-24**
>    (`modules/story/seafloor_cavern.py`, wired as Segment 20, 5/5 drives PASS). This was a full
>    EXECUTABLE build spec sitting inside the LIVE queue item — the worst of the four stale
>    §Ch20 clauses, and the previous audit's fix retired the other two and missed this one.
>    The superseded spec read: **(PARKED, NOT CANCELLED) ASSEMBLE §Ch20 AS A CHAPTER** — a module in `modules/story/`,
>    The superseded spec body (~11 lines) is archived verbatim in `28-HANDOFF-ARCHIVE.md`.
>
>    *(the superseded ROOM 3 / ROOM 8 build blocks MOVED to `28-HANDOFF-ARCHIVE.md` 2026-08-14 on
>    the line budget. **Both rooms are DRIVEN AND PASSING — do not rebuild them.** Their reusable
>    lessons are already in the banners at the top of THIS file: the 18-step push-free walk route
>    with its confirmed DOUBLE battle at `(6,5)`, and ⛔ **step 9 faces LEFT, never UP** — north
>    from `(5,4)` permanently seals the `(5,2)` exit. The INSTRUCTION moved; corrections stayed.)*
>
>    **(c2) ✅ BLOCKER 2 — THE EXIT IS NOW DRIVEN** (`--driver ch20room9`, 2026-08-14: south to `(38,23)`, Surf onto `(38,24)`, then a real path to the dive tile). Superseded: *"THE EXIT STRANDS THE RUN, AND IT IS UNTESTED."* See the banner at the top:
>    step **SOUTH to `(38,23)`** and Surf, never north. Build the exit leg with that assertion in it.
>
>    ✅ **(d) DONE 2026-08-14 — the user approved that round and it was PROMOTED.** ‼ Promotion of
>    anything drifted TODAY remains the USER's call and has not been asked for.
> 1. **Run `preflight.py`**, then the gate suite in "HOW TO RUN / TEST" — **`run_gates.py` prints its own count and IS the authority; it reached 27 on 2026-08-17** (all exit 0
>    2026-08-15; it has said 17, 18, 19, 20, 21, 22, 23 and 28 on its way to **33** — `run_gates.py` is authoritative, never this prose), and the drift check below.
>    ⚠ **EXPECT 9 differing, 0 orphaned as of 2026-08-27 (the six `#26-*`/§Ch20/§Ch21 files in the drift row above + `map_data.py` + `story_mode.py` — NOT a promotion decision until the user rules) — the abort guards were PROMOTED (user-approved). Formerly 0 differing after the FIVE-FILE PROMOTION (2026-08-17, user-approved)**, the KI-66 `_on_field` fix included, the KI-81 whiteout guard
>    included (2026-08-16, user-approved). **ANY file listed is unexplained drift.**
>    *(This line read "EXPECT 0 — everything was PROMOTED 2026-08-15" until 2026-08-15, when Stage 2
>    corrected a wrong type-set comment in that file. A Tier 1 audit caught that the drift figure had
>    been updated in the STATE row and the banner but NOT here, fifteen lines away — so a cold agent
>    running `promote.py --check`, getting one file back, would have read an EXPECTED result as an
>    alarm. ALL drift statements in this file move together or not at all — ⛔ do NOT trust a COUNT here (this line said 'three' while another said 'five'; the true figure reached THIRTEEN across five files). GREP, case-insensitively, and require zero.)*
>    ⛔ Do not restate the figure here; it has been wrong at 2, 3 and 3 again. `promote.py --check`
>    is the authority. (Earlier EXPECT-2 / EXPECT-3 trails moved to `28-HANDOFF-ARCHIVE.md`.)
>
> ‼ *(Queue items **1b, 2, 2c and 3** were archived to `28-HANDOFF-ARCHIVE.md` on 2026-09-01
>    for the line budget — 1b/2/3 as ✅-DONE, and **2c as a live REFERENCE pointer** (it carried
>    KI-72's rule, *never let the planner choose a surfacing tile*), so 2c is NOT 'done'.
>    ⛔ **THE SURVIVING QUEUE ITEMS ARE ONLY `0`, `1` AND `3b`.** Any pointer in this file to
>    items **2, 2c, 3 or 4** is DANGLING — 4 never existed, the rest are archived. The Regi
>    arc those pointers mean is tracked in `05-KNOWN-ISSUES.md` KI-69.)*
> 3b. ⛔⛔ **THE ORDER CHANGED 2026-08-13 — READ `06-DECISIONS-LOG.md` before item 4.** The Regi
>    arc is **NOT** next: *"KI-59 blocked it, I fixed it, so build it"* was **REFUTED three ways**
>    (the tombs walk with `follow_path`, **"no collision checking"**; their 144 tiles describe a
>    room `setmetatile` rewrites at runtime; and upstream ships a working Regi solver against the
>    UN-fixed inversion). ‼ That was the SAME error logged that morning — counting tiles without
>    checking what REACHES them — made twice in one day.
>    ✅ **✅ (i) `#24-ch20rename` and (ii) the §Ch20 AREA ATLAS ARE BOTH DO…** 📦 ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3
>    budget; CLOSED, nothing deleted).
>    ‼ **The rules later work leans on are kept ABOVE and are unaffected:** ROCK SMASH is
>    MANDATORY, the trigger tile is **`(17,42)`** not `(16,42)`, and §Ch20 grades on
>    **`VAR_ROUTE128_STATE == 2`**, never the Kyogre flag. Full 11-leg spec:
>    `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`. ⛔ Everything retracted
>    there is DONE or RETRACTED — nothing in the archived block is a live instruction.
## 📌 §Ch19 pre-build planning notes → `28-HANDOFF-ARCHIVE.md`; its four gotchas live ONCE, in the "§Ch19 IS DONE" section above.

---

# HOW TO RUN / TEST

### §Ch21 recon instruments (both NEW 2026-08-24, both fault-tested)
```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 probe_ch21_topology.py            # warps/sizes/dive+surface tiles from ROM headers
POKEBOT_CH21PROBE_FAULT=warpcoord   ... same ...        # its self-test: MUST print 2 FAIL and exit 1

PYTHONUTF8=1 py -3.12 probe_skypillar_clean_layout.py   # the CLEAN-layout staircase + the deliberate fall
POKEBOT_SKYPILLAR_FAULT=nofall      ... same ...        # its self-test: MUST print 1 FAIL and exit 1
```
⛔ `probe_skypillar_clean_layout.py` is NOT in `run_gates.py` — it fetches decomp layout binaries over
the network and a standing gate must not need the net. ‼ It exists because a Tier 1 review REFUSED the
atlas's central finding while it rested on an uncommitted script: right numbers, un-re-runnable = NOT PROVEN.

### §Ch21 + §Ch22 STORY LEGS — the runnable drivers
*(‼ added 2026-08-27 because a Tier 1 review found every leg existed only as PROSE, so a cold agent
could not START the shipped work from this file.)*
```
cd tools/story-dev
# legs 1 / 2a / 2b — each from its own PINNED fixture. ‼ Also covered end-to-end by `ch21chapter`
# below; these stay for isolating ONE leg, not for regression sweeps.
PYTHONUTF8=1 py -3.12 story_harness.py post_ch20.ss1              --driver ch21dive
PYTHONUTF8=1 py -3.12 story_harness.py post_sootopolis_arrival.ss1 --driver ch21escort
PYTHONUTF8=1 py -3.12 story_harness.py post_steven_escort.ss1     --driver ch21cave
# leg 3 step 0 — POCKET-EXIT probe, LIVE half (post_wallace.ss1) ~4,200 fr. ⚠ The `navigate` arm
# is the naive one and is MEASURED IDENTICAL to `follow`.
PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1           --driver ch21pocket --frames 60000
POKEBOT_CH21_POCKET_ARM=navigate  ... same ...

# leg 4 — THE SKY PILLAR climb + descent            (fixture: post_skypillar_door.ss1) ~10,100 frames
PYTHONUTF8=1 py -3.12 story_harness.py post_skypillar_door.ss1    --driver ch21climb --frames 60000

# leg 5 PART C — read-mostly VALIDATION probe (post_rayquaza_gone.ss1) ~16,300 fr. SETTLED
#   2026-09-02; the reference for proving KI-73 on a layout-swapped map.
PYTHONUTF8=1 py -3.12 story_harness.py post_rayquaza_gone.ss1     --driver ch21leg5probe --frames 150000
CH21_PROBE_NOPIN131=1 ... same ...   # CONTROL: un-pinned, the swim RAISES and never moves

# leg 5 — THE RETURN + HM07 WATERFALL (post_rayquaza_gone.ss1) ~20,700 fr. Expect PASS, missing=[],
#   order_ok, at=SOOTOPOLIS_CITY(31,34), hm_flag, hm07_in_bag=1, wallace_state=1, gym_door_wp=2,
#   whiteouts=0, encounters=7
PYTHONUTF8=1 py -3.12 story_harness.py post_rayquaza_gone.ss1     --driver ch21return --frames 60000
PYTHONUTF8=1 py -3.12 story_harness.py post_legends_calmed.ss1    --driver ch21return --frames 30000
#   ^ NPC half only, ~4,600 fr (FAILs by PREMISE — correct for a resumed run). Six fault arms, each
#   FAIL for its own reason except NPCMISS which must still PASS: POKEBOT_CH21_FAULT_{NOPIN131,
#   SETTLESKIP,SCENESTOP,NPCMISS,DROPREADING,CONTROLOPEN}=1

# §Ch21 AS A CHAPTER — the PRODUCTION entry point, legs 1->5   (fixture: post_ch20.ss1)
#   MEASURED 2026-09-02: frames=95823, encounters=26, whiteouts=0, ACCEPTANCE: PASS.
#   Expect: ROUTE128(38,24) vars (1,0) -> SOOTOPOLIS_CITY(31,34) vars (5,3), hm07_in_bag=1,
#           wallace_state=1, gym_door(31,32)=2 wp, poke_center(43,32)=22 wp, premise_ok=True.
PYTHONUTF8=1 py -3.12 story_harness.py post_ch20.ss1              --driver ch21chapter --frames 250000
#   the VACUITY arm (must FAIL — it proves the grade is not satisfied by a no-op):
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch21chapter --frames 400

# §Ch22 PART A — the read-mostly gym probe (post_hm07.ss1) ~3,958 fr. PASSED 2026-09-02; kept
#   startable as the reference A/B for proving an instrument BLIND. Expect PASS, P0-P5, 64 thin ice
#   in sections 7/19/38, six locked stairs, metatile_diff=1 after one ice step and collision_diff=0
#   (the blindness proof), ICE_STEP_COUNT 1->2, re-entry resets to 1, money=67466, whiteouts=0.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22probe --frames 60000
#   its fault arm (must FAIL — proves the grade requires the MEASUREMENT, not just the code path):
POKEBOT_CH22_FAULT_NOSTEP=1 ... same ...

# §Ch22 THE ICE PUZZLE — the 64-step route table, walked   (fixture: post_hm07.ss1) ~2,232 frames
#   ⛔ DRIVEN 2026-09-02, and now also covered by the CHAPTER below. Production `walk_the_ice()`;
#   the table is re-derived from the DECOMP by `solve_gym_ice.py` and re-checked LIVE every step.
#   Expect: PASS, steps=64, sections (1,7,(8,17),9) (2,19,(8,12),29) (3,38,(8,6),68), frames=2232,
#           `end_tile=(8,6)` BUT `at=(8,3)` — DIFFERENT FIELDS, both right: production ENDS on
#           (8,6) and the 3-step climb to (8,3) is `climb_to_juan()`, which the CHAPTER owns.
#   ‼ End counts are 9/29/68, NOT 8/28/67 (each unlock's `addvar` lands in the crossing step's
#     beat). The guard tolerates +1 AND +2 — asserting +1 exactly was a real bug.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22ice   --frames 60000

# §Ch22 THE STAIR COLUMN — READ-ONLY, ~2,232 fr. ⛔ RUN BEFORE TOUCHING THE DESCENT. Walks the ice,
#   then dumps live column x=8 before AND after — an A/B in one run. Expect (8,4) and (8,5) both
#   0x20f -> 0x207 (LOCKED -> OPEN), (8,6) -> 0x20e cracked, (8,2)=0x22b (JUAN'S OWN TILE, plain
#   floor), VERDICT: WALK, PASS. ‼ PASS means THE READING HAPPENED — read the VERDICT line.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22stairs --frames 60000

# §Ch22 THE EXIT — the ice, then the DELIBERATE FALL to B1F and out, ~19,989 frames (MEASURED)
#   ⛔ DRIVEN 2026-09-03, the first entry into B1F ever. ‼ It re-walks the ice; the CHAPTER does not.
#   Expect PASS: ice_steps=64, fall to B1F (8,6) in ~140 fr, b1f_steps=19, battles=3 at (8,8)
#   (8,17) (8,19), end SOOTOPOLIS_CITY (31,33), continue=23 wp, whiteouts=0, frames=19989,
#   PARTY 629/694 -> 332/694 with ZERO faints.
#   ⛔⛔ 3 BATTLES IS *THIS DRIVER'S* PASS SHAPE — it runs at `badge8=False`. THE ASSEMBLED CHAPTER
#     SEES **ZERO** (the victory script settrainerflags all ten; MEASURED live, b1f_entered=True).
#     ⇒ this leg's battle count and its HP cost are NOT transferable; the FALL and the ROUTE are.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22exit  --frames 120000

# §Ch22 JUAN — GYM 8, ~32,891 fr (MEASURED; the first gym-LEADER fight ever timed here). DRIVEN
#   2026-09-03 AND WON. Expect PASS, badge8=True won=True at=GYM_1F(8, 3), city_state=6, battles=1,
#   outcomes=['BattleOutcome.Won'], whiteouts=0, SURVIVORS 5/6, frames=32891.
#   ⛔ RE-RUNNING THIS UNJITTERED IS A REPLAY, NOT A SAMPLE — 3 identical runs proved determinism
#     for a fixed (save, driver, code) triple. To take a NEW draw, perturb the RNG:
POKEBOT_CH22JUAN_JITTER=181 PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1 --driver ch22juan --frames 120000
#     Expect a DIFFERENT frame count (25508 at N=181) and two DIFFERENT RNG values across the
#     idle — equal means the jitter moved nothing. ⇒ a LOSS is a RESULT: 6 draws, 5 WINS, 1 LOSS.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22juan  --frames 120000

# §Ch22 AS A CHAPTER — the PRODUCTION entry point (Segment 22). (fixture: post_hm07.ss1) ~64,563 fr
#   ✅ DRIVEN TO PASS 2026-09-03, INCLUDING A LOST GYM FIGHT IT RECOVERED FROM. ⛔ DO NOT REBUILD.
#   Expect PASS: badge8=True, at=SOOTOPOLIS_CITY(31,33), city_state=6, ice_steps=64 (ice_ok=True),
#   b1f_steps=19, battles_on_B1F=0 WITH b1f_entered=True, CONTINUE=23, RECOVERIES 1,
#   outcomes=['BattleOutcome.Lost','BattleOutcome.Won'].
#   ⭐ `battles_on_B1F=0` IS THE DISCRIMINATOR AND IS MEANINGLESS WITHOUT `b1f_entered=True` —
#     drive 1 printed the same 0 having never set foot on B1F.
#   ⚠ A LOSS IS A RESULT (stochastic, 5W/1L over six draws) and the chapter RECOVERS. ⛔ A
#     transcript with NO `ACCEPTANCE` line + `BotModeError -> Manual` is **KI-47** (which has a
#     deterministic repro command there), not a hang and not a §Ch22 defect.
PYTHONUTF8=1 py -3.12 story_harness.py post_hm07.ss1              --driver ch22chapter --frames 300000
#   two fault arms, each FAILing for a DIFFERENT half of the completion predicate:
#   POKEBOT_CH22_FAULT_{NODESCEND -> stranded on the ISLAND | STRANDED -> still on GYM_1F}=1

# leg 3 — THE APPROACH, the PRODUCTION entry point. ~34,000 frames (MEASURED). Expect PASS,
#   reached=True at=SKY_PILLAR_ENTRANCE(6,16) pocket_attempts=1 rest=(6,16) encounters=9
#   whiteouts=0 frames=34122 rest_matches_prediction=True; METHOD planner_calls_on_route131=2
#   blind_steps_taken=1 tail_tiles_confirmed=16/16 method_ok premise_ok; CONTROL control_refused
PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 120000

# leg 4 — THE SKY PILLAR CLIMB + DESCENT. ~10,000 frames (MEASURED). Both one-shots, both falls.
#   Expect: reached=True at=SKY_PILLAR_ENTRANCE(14,3) phase=full order_ok=True falls=[ascent,descent]
#           floors_pinned=7 VARS end=(5,1,1)  METHOD premise_ok=True method_ok=True  ACCEPTANCE: PASS
PYTHONUTF8=1 py -3.12 story_harness.py post_skypillar_door.ss1 --driver ch21climb --frames 60000
# ‼ THE SEVEN FAULT ARMS ARE NOT OPTIONAL — each fails for its OWN reason (five from the mid-leg
#   fixtures; BADBLOCKDATA from the FULL fixture, premise valid, so it fails purely on its own guard).
POKEBOT_CH21_FAULT_SUMMITSTOP=1  story_harness.py post_wallace_scene.ss1 --driver ch21climb   # FAIL, missing every descent reading
POKEBOT_CH21_FAULT_NOFALL=1      story_harness.py post_wallace_scene.ss1 --driver ch21climb   # FAIL, 'map never changed', bounded, no hang
POKEBOT_CH21_FAULT_POCKETEXIT=1  story_harness.py post_skypillar_summit.ss1 --driver ch21climb # FAIL, 'LIVELOCK, not a refusal'
POKEBOT_CH21_FAULT_DROPREADING=1 story_harness.py post_skypillar_summit.ss1 --driver ch21climb # FAIL, R-FALL2 missing though the fall happened
POKEBOT_CH21_FAULT_CONTROLOPEN=1 story_harness.py post_skypillar_summit.ss1 --driver ch21climb # FAIL, control_refused=False + order_ok=False
POKEBOT_CH21_FAULT_BADBLOCKDATA=1 story_harness.py post_skypillar_door.ss1 --driver ch21climb # FAIL, blockdata mismatch NAMES SKY_PILLAR_1F, bounded (2244 frames), no hang
PYTHONUTF8=1 py -3.12 story_harness.py post_rayquaza_gone.ss1 --driver ch21climb  # the VACUITY arm: 'already DONE; nothing to resume'
# the Sky Pillar CLEAN layouts for all six floors, from our ROM (no network). Offline, seconds.
PYTHONUTF8=1 py -3.12 probe_skypillar_rom_layouts.py
POKEBOT_SPROM_FAULT=stride|noagree   ... same ...   # self-tests (both RED); anycand PASSES on purpose
# ‼ THE THREE FAULT ARMS ARE NOT OPTIONAL — the happy path cannot reach any of them. (This line
#   said TWO while THREE commands followed, until a Tier 2 audit caught it; a reader trusting the
#   count would skip POCKETWALKBACK, the arm an adversarial review added because it caught a REAL
#   blocker.) POCKETSTALL must still PASS with pocket_attempts=2 — the recovery working, LIVE.
POKEBOT_CH21_FAULT_POCKETSTALL=1 PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 40000
#   BLINDWALL must FAIL loudly naming the step index, bounded, and must NOT hang.
POKEBOT_CH21_FAULT_BLINDWALL=1   PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 60000
#   POCKETWALKBACK stalls the RECOVERY'S OWN walk back; it only fires while a recovery is running,
#   so it MUST be set WITH POCKETSTALL. Expect a NAMED BotModeError ("...the walk BACK to (31,17)
#   then stalled too... the stranded case") + FAIL — a RAW TimedOut... is the defect it catches.
POKEBOT_CH21_FAULT_POCKETSTALL=1 POKEBOT_CH21_FAULT_POCKETWALKBACK=1 PYTHONUTF8=1 py -3.12 story_harness.py post_wallace.ss1 --driver ch21approach --frames 30000
# ⛔⛔ NONE OF THE §Ch21 PROBES IN THIS BLOCK IS READ-ONLY, WHATEVER ITS 'Offline' LABEL SAYS —
#   ABOVE this line as well as below (a Tier 2 audit found it anchored below five of its subjects,
#   one under 'RUN THIS FIRST'). All SEVEN boot LibmgbaEmulator on the SHARED `repro-ml` profile
#   and write a save state + update current_state.ss1 EVERY RUN: probe_ch21_{skypillar,
#   route131_tail,route131_live,leg3_constants,pocket_exit}, probe_live_mapgrid,
#   ab_ch21_leg3_layoutpin. Gitignored, but it mutates shared state. `#24-skypillarprobewrites`.
# ⛔ keep BOTH sky-pillar
# probes: this one reads the layout WE plan on, `probe_skypillar_clean_layout.py` reads CLEAN.
# leg 3 — the TAIL adjudication + the CONSTANTS re-check. Seconds. ⛔ NOT read-only — see above.
PYTHONUTF8=1 py -3.12 probe_ch21_route131_tail.py
POKEBOT_R131TAIL_FAULT=stride|swapsets|bendtail  ... same ...    # self-tests; all three must fire
PYTHONUTF8=1 py -3.12 probe_ch21_leg3_constants.py
# ⛔ THE INSTRUMENT FOR "the planner and the game disagree about a tile" — use it on ANY map that
#   runs setmaplayoutindex or setmetatile. It reads gBackupMapLayout (RAM), which is the ONLY
#   reader in this tree that can see either. Pass any save state.
PYTHONUTF8=1 py -3.12 probe_live_mapgrid.py saves/post_skypillar_door.ss1
# leg 3's layout-pin A/B, against drive 1's own stall state (reproduces the failure, then fixes it):
PYTHONUTF8=1 py -3.12 ab_ch21_leg3_layoutpin.py

# leg 3 step 0 — the STATIC half. Seconds. ⛔ NOT read-only (see above). RUN THIS FIRST.
PYTHONUTF8=1 py -3.12 probe_ch21_pocket_exit.py
POKEBOT_POCKET_FAULT=rig PYTHONUTF8=1 py -3.12 probe_ch21_pocket_exit.py   # self-test: C3 RED, exit 1

# leg 3/4 — the SKY PILLAR, asked of PRODUCTION. Seconds, no network.
PYTHONUTF8=1 py -3.12 probe_ch21_skypillar.py
POKEBOT_SKYPILLAR_PROBE_FAULT=rig PYTHONUTF8=1 py -3.12 probe_ch21_skypillar.py  # self-test: C2 RED

# leg 3 PRE-BUILD GATE — ROUTE131 SET A vs SET B, from OUR ROM. Offline, seconds. ⛔ RUN BEFORE BUILDING.
PYTHONUTF8=1 py -3.12 probe_ch21_route131_live.py
POKEBOT_R131_FAULT=stride PYTHONUTF8=1 py -3.12 probe_ch21_route131_live.py   # self-test: C2 RED, exit 1
```
⛔ **Quote `ch21pocket`'s `RESULT` line, never its `ACCEPTANCE` line**: ACCEPTANCE grades *"did every
reading happen"*; whether the walk worked is the separate `walked_out=` field. ⚠ Any driver dirties
`party_accounting_ledger.jsonl` — expected, not damage (playbook §2b).

### Capture the §Ch21 start fixture — ⛔ ALREADY DONE, do NOT redo
`saves/post_ch20.ss1` exists (`--driver ch20chapter` + `CH20_CAPTURE=`, written only on
`ACCEPTANCE: PASS`, so the file's existence IS the acceptance record). Verify a fixture with
`probe_anchor_inventory.py --filter <name>` — the FILE, never the driver's log (playbook §2b).

‼ **RESTORED 2026-08-13.** This file referenced a "HOW TO RUN / TEST" section in four places while
the section itself lived only in `28-HANDOFF-ARCHIVE.md` — so a cold-start agent following the
handoff's own instruction found nothing. The archive copy is longer and still useful for the §Ch18/
§Ch19 drivers; this is the minimum a new session needs.

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 preflight.py        # ‼ RUN THIS FIRST. git + fixtures + docs + freeze
PYTHONUTF8=1 py -3.12 run_gates.py        # THE STANDING SUITE — all 33, exits non-zero on any
                                          #   failure (~130s). ‼ The list lives in CODE, not prose — `run_gates.py` is the only
#   authority on how many gates there are. Every prose count in this file has been
#   wrong at some point.
PYTHONUTF8=1 py -3.12 run_gates.py --quick   # the 25 needing no ROM (was 10, 14, 15, 16, 17, 18, 20, 21; MEASURE)
PYTHONUTF8=1 py -3.12 run_gates.py --list    # what is in the suite
PYTHONUTF8=1 py -3.12 probe_chapter_order.py --build custom   # ‼ also check the OTHER fork
PYTHONUTF8=1 py -3.12 probe_stale_citations.py   # ‼ RUN THIS BEFORE TRUSTING ANY `file.py:NNN`
                                          #   IN THE DOCS. 22 were stale on 2026-08-16; it took
                                          #   them to 0. NOT a gate (years of citations would
                                          #   make it red on arrival). Rule: RE-DERIVE, NEVER
                                          #   RE-TYPE — and the durable claim is the SHAPE,
                                          #   not the line, because lines drift on every edit.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive_ki76.ss1 --driver ki76warp --frames 2500000
#   KI-76's live confirmation. ⛔ DO NOT RE-RUN to "check" it — CONFIRMED and committed.
#   KI76_RELEASE_EARLY=1 is the control arm (releases the button on first movement).
PYTHONUTF8=1 py -3.12 probe_abort_swallowing.py --build custom  # KI-81 ratchet: baselines are EQUAL AGAIN -> {sandbox: 23, custom: 23}. sandbox went 36 -> 31 -> 23 as (b) then (c) landed, and custom followed 36 -> 23 when the file was PROMOTED 2026-08-24 (user-approved). Both forks now read ZERO AST abort-swallowers.

# --- §Ch20, the live drives (SEVEN of them; each ~4-25 min). All PASS as of 2026-08-14,
#     EXCEPT ch20room9, which is 2W/1L — the Archie fight is stochastic, see its note. ---
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20dive  --frames 900000
#   Expect: legs=6/6 at_entrance=True got_out=True can_continue=True ACCEPTANCE: PASS
#   ‼ `got_out` is the one that matters — an underwater cavern is the best place to strand a run.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room1 --frames 1500000
#   Expect: in_room1=True ab_before=False ab_after=True smashed=True pushed1=True pushed2=True
#           in_room2=True can_continue=True   ACCEPTANCE: PASS
#   ‼ `ab_before=False` is an ASSERTED part of the verdict: if the corridor was already reachable
#     the run proved nothing about the puzzle. A one-armed pass here would be meaningless.
# ⛔ THE THREE Expect: BLOCKS BELOW WERE ATTACHED TO THE WRONG COMMANDS until 2026-08-13 (the
#   fault note even carried ch20room2's PASS line). Each now sits DIRECTLY under its own command.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room2 --frames 2000000
#   Expect: room1_ok=True m1=False m2=False m3=True pushes=3/3 in_room6=True can_continue=True
#   ‼ It RE-SOLVES ROOM 1 from scratch first (FLAG_TEMP_* objects respawn on every map load), so
#     a ch20room2 PASS is also a Room 1 PASS. `m2=False` is the arm that matters: it attributes
#     the opening to the PUSHES rather than to the Rock Smash.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room6 --frames 2500000
#   Expect: room2_ok=True crossed=True in_room3=True room3_walk=True can_continue=True
#   ‼ `crossed` is THE FIRST EXECUTED CURRENT CROSSING here. `room3_walk` re-confirms LIVE that
#     Room 3 is crossable PUSH-FREE and that the line enters the trainer sight tile (6,5).
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room3 --frames 3000000
#   Expect: crossed=True usable=6 battles=1 saw_double=True in_room8=True can_continue=True
#   ‼ `saw_double` is REPORTED, NOT GRADED — grading a decomp claim would turn "we learned the
#     claim was wrong" into "the run failed". ‼ `battles` counts ROOM 3 only: counting run-wide
#     once printed a false REFUTED over data that CONFIRMED it (the Room 1 grunt fights every run).
# ‼ FAULT INJECTION: POKEBOT_CH20_FAULT=room1 forces the Room 1 solve to fail, so the drivers'
#   FAILURE branch can be exercised on demand.
#   Expect: RESULT … in_room2=False can_continue=False and a clean `ACCEPTANCE: FAIL` — ‼ a run
#   in fault mode that prints ACCEPTANCE: PASS, or no ACCEPTANCE at all, is the DEFECT.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room8 --frames 4000000
#   Expect: room3_ok=True pushes=9/9 attempts=1 recovered=False exit_path=True in_room9=True
#           can_continue=True   ACCEPTANCE: PASS
#   ‼ Step 9 faces LEFT. A boulder pushed north from (5,4) lands on (5,3) and PERMANENTLY
#     seals the only route to the (5,2) exit.
#   FAULT: POKEBOT_CH20_FAULT=room8 abandons attempt 1 before push 5 to EXERCISE the
#     jam-recovery handler. Expect: attempts=2 recovered=True and still ACCEPTANCE: PASS.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room9 --frames 6000000
#   Expect: rooms_ok=True triggered=True battles_r9=1 kyogre_flag=True var2=True landed=True
#           escaped=True ocean_path=True can_continue=True   ACCEPTANCE: PASS
#   ‼ 2W/1L: the ARCHIE fight is the chain's one stochastic element. A LOST run prints NO
#     RESULT AND CANNOT — the whiteout drops to Manual and the generator is abandoned. The
#     `PRE-ARCHIE PARTY` HP line is the loss's attribution record; grade a silent transcript
#     by its presence.
PYTHONUTF8=1 py -3.12 probe_route128_landing.py     # §Ch20's EXIT: 9/9, the atoll is real
#   ‼ The landing tile has ZERO surfable neighbours, so a naive "Surf from where you land" reads
#     as a HUNG LEG, not a failure. (§Ch20's exit leg is built; this stays as the trap it names.)

# --- (P4) STAGE 1 — the Slugma/Winona bug, live, BOTH ARMS. Needs a ROM; ~3 min each. ---
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver boxcounter --frames 200000
#   ARM B (this command, hook unset): expect `-> <pid>` and ACCEPTANCE: PASS.
POKEBOT_BOXCOUNTER_TYPEONLY_A=1 PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver boxcounter --frames 200000
#   ARM A (pre-fix): expect `-> None` and ACCEPTANCE: PASS — its expectation IS None.
#   ‼ BOTH ARMS PASS when the code is correct; `pid_match` means "matched THIS ARM's expectation".
#   ‼ Grade by `grep "boxcounter]"` — a driver that throws at f0 still produces a clean [done] line.

# --- (P4) STAGE 2 — the REAL heal collects the counter. ~4 min each. ⛔ ANCHOR IS THE GYM WEDGE:
#     `ch13_fortree_door.ss1` is on ROUTE120, which `calculate_path` reads as a WALL (KI-24), and
#     the run dies on its first leg with "Cannot reach FORTREE_CITY". This is measured, not feared.
PYTHONUTF8=1 py -3.12 story_harness.py fortree_gym_wedge.ss1 --driver boxcounter2 --frames 400000
#   ARM B: expect moved=True knows_rock_throw=True lead_is_counter=True noop_attributed=True,
#          ACCEPTANCE: PASS. Production prints `depositing Skitty L17` to make room — that deposit
#          is REPORTED, never graded.
POKEBOT_BOXCOUNTER_TYPEONLY_A=1 PYTHONUTF8=1 py -3.12 story_harness.py fortree_gym_wedge.ss1 --driver boxcounter2 --frames 400000
#   ARM A (the user's derail, reproduced): expect _hunted_counter_pids=[] and
#          still_boxed=True not_in_party=True, ACCEPTANCE: PASS — and NO deposit at all.
#   Add `--build custom` to either for the other fork (all four cells pass as of 2026-08-15).
#   ‼ Stage 2 SUBCLASSES Stage 1, so each run re-proves Stage 1 first — read the STAGE-1 GATE line.
#   ⛔ The gym leg is OFF by default and REPORTED-NOT-GRADED: POKEBOT_BOXCOUNTER2_GYM=1 enables it.

# --- KI-66 — the faint chooser inside the Steven MULTI battle (2026-08-17) ---
#   Stages ONE of our own picks at 1 HP so it FAINTS in real combat, then reads production's own
#   [FAINT-CHOOSER] telemetry. Expect `[ch19b] ACCEPTANCE: PASS`.
#   ‼ `[ki66] ACCEPTANCE` is INSTRUMENT HEALTH ONLY — the bug verdict is the `KI66-` lines.
#   ⛔ It NEVER captures an anchor (it injects) and re-hashes post_space_center.ss1 to prove it.
PYTHONUTF8=1 py -3.12 story_harness.py at_steven_2f.ss1 --driver ki66faint --frames 600000 --profile ki66
#   Promoted fork:  ...--driver ki66faint --build custom --profile ki66custom
#   SINGLE-BATTLE control (this faint path runs in EVERY battle, not only multi):
PYTHONUTF8=1 py -3.12 story_harness.py route116team.ss1 --driver faintrepro --inject-shedinja-faint --frames 120000 --profile ki66single
#   ‼ That one WHITES OUT by construction (all-1HP party) and exits non-zero — grade it by DIFFING
#   the two builds' stall/watchdog frames, never by its exit code.

# --- KI-80 — the counter-ladder gate, THREE arms in ONE run. ~40s. ⛔ ANCHOR MUST BE THIS SAVE:
#     it is NO_ANSWER (condition 7) AND team_max 28 <= wild_max 27 + 8 (condition 9). Both named
#     alternatives FAIL one of those: `fortree_gym_wedge` has a credible answer (Castform scores
#     160 >= 75), and `ch13_fortree_door` has team_max 39, which makes the A/B VACUOUS.
PYTHONUTF8=1 py -3.12 story_harness.py batch2_run04_wedge.ss1 --driver ki80ladder --frames 2000
#   ⛔ EXPECT `ACCEPTANCE: FAIL` — AND THAT IS THE HEALTHY ANSWER SINCE THE FIX SHIPPED.
#     This command grades the OLD, COUPLED expectation, so GRASS_STRONG now correctly reads
#     `-> LADDER expected PLAIN_ESCALATION`. Its FAIL is what PROVES the decoupling changed
#     behaviour. ‼ It said "Expect ... ACCEPTANCE: PASS" until 2026-08-16 and was inverted by the
#     fix — a cold-start audit caught it grading a healthy tree as broken.
#   ‼ THE DRIVER EXITS 0 EVEN ON FAIL — it is a harness driver, not a gate. GRADE THE
#     `ACCEPTANCE:` LINE, never `$?`. Grep with `grep "ki80ladder]"`.
POKEBOT_KI80_ARM4=1 PYTHONUTF8=1 py -3.12 story_harness.py fortree_gym_wedge.ss1 --driver ki80ladder --frames 2000
#   ⛔ ARM 4 — THE MIRROR-REGRESSION GUARD. Run BEFORE and AFTER the decoupling; must PASS both
#     times (OUTCOME=PLAIN_ESCALATION). Needs THIS save (HAS_ANSWER); the driver FAILS by name
#     on the wrong one, because arms 1-3's save cannot reach the `:1925` line it watches.
POKEBOT_KI80_DECOUPLED=1 PYTHONUTF8=1 py -3.12 story_harness.py batch2_run04_wedge.ss1 --driver ki80ladder --frames 2000
#   ✅ THE AFTER RUN, AND IT NOW PASSES — the ladder IS decoupled (2026-08-16). All three arms
#     reach LADDER. ‼ It said "Expect FAIL TODAY" until the fix shipped; seeing PASS is correct and
#     is NOT a sign the discriminator stopped discriminating. The proof that it still discriminates
#     is the command ABOVE, which correctly FAILS against the old expectation.
#   Fault-test kept for reference — the VACUOUS fixture this file once prescribed:
#     PYTHONUTF8=1 py -3.12 story_harness.py ch13_fortree_door.ss1 --driver ki80ladder --frames 2000
#     -> `ACCEPTANCE: FAIL … THE A/B WOULD BE VACUOUS`, and ALL THREE arms come back LADDER.
#   Transcripts: tools/story-dev/evidence/2026-08-15-ki80ladder-*.stdout.txt

PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver boxwrite --frames 200000
PYTHONUTF8=1 py -3.12 probe_box_contents.py ch13_fortree_door.ss1
#   READ-ONLY dump of EVERY box + party slot: species, level, PID, types, full moves, and per mon
#   `type_match`/`move_match` against NEEDED. Takes any save name (defaults to ch13_fortree_door).
#   ‼ This is what turned "the anchor's box might matter" into a measurement: it found the boxed
#   Castform whose Powder Snow (Ice) qualifies it as a counter, sitting AHEAD of any injected mon.
PYTHONUTF8=1 py -3.12 story_harness.py ch13_fortree_door.ss1 --driver partypids --frames 200000
#   READ-ONLY identity dump (party + box: species, level, PID) — flags shared PIDs. On this save
#   it prints the REAL KI-78 twin pair: Shedinja L30 and Ninjask L29 both pid=42207D6F.
#   Proves `debug_write_box_slot` writes a box slot the PRODUCTION reader can read. ACCEPTANCE: PASS.

# --- PARTY ACCOUNTING STAGE 0 — the readers, the divergence log, and its gate ---
PYTHONUTF8=1 py -3.12 repro_party_accounting.py     # PARTY ACCOUNTING STAGE 0 (gate #22)
#   Expect: `ALL 33 CHECKS PASS`, exit 0. No emulator, ~1s. ‼ It PRINTS its own check count —
#     believe that line, not this one. Takes `--build custom` and
#     ASSERTS which fork it imported. It drives the REAL get_party() over FABRICATED gPlayerParty
#     memory, so it tests the shipped reader, not a copy. ‼ The CONTROLS are the point: a healthy
#     party must record NOTHING, and get_party() must be byte-identical with the observer stubbed.
#   ‼ THE MEASUREMENT IT EXISTS FOR IS NOT IN THE GATE — it is the `[PARTY-ACCT] STAGE 0 SUMMARY`
#     that every `story_harness.py` drive now prints at the end. Collect those from LONG runs:
PYTHONUTF8=1 py -3.12 collect_party_accounting.py   # (P3b) aggregate every drive's summary
#   Exits 1 until the criterion is met (>=5 drives / >=3 drivers / >=250k recomputes, OR the first
#   divergence), so P3b cannot be eyeballed. ✅ AS OF 2026-08-15 IT EXITS 0: 7 drives, 7 drivers,
#   ⛔ SUPERSEDED 2026-08-15: it now reports ✅ CRITERION (b) MET — A DIVERGENCE WAS OBSERVED.
#   967,970 recomputes · 39 drives · 12 drivers, with HOLE x30 in `boxcounter2` in BOTH forks
#   (slot 5 of gPlayerPartyCount=6, counted by the game but near-all zero). The old line said
#   "7 drives, 280,707, NO DIVERGENCE … all DUNGEON content with a STATIC party" — true of that
#   population, false now that a party-MUTATING driver exists. ‼ RUN IT; do not quote it.
#   ‼ It MEASURES ONLY — it cannot drive the emulator, and it says so rather than implying a log
#     read is a reading. It also fails LOUD when no log matches ("I could not look" != "clean").

# --- THE DOC GATES — MANDATORY before ANY commit touching PROJECT KNOWLEDGE (Tier 0) ---
PYTHONUTF8=1 py -3.12 lint_docs.py
# ⛔ THE STRUCTURAL half of the doc layer (NEW 2026-09-01, gate #33). Tier 0 was GREEN over all
#   four defects that four cold-start audits found in one day, because each was STRUCTURAL:
#   a queue marker pointing at the wrong leg, the HOW TO RUN section deleted wholesale, a
#   claimed fault-arm count disagreeing with the arms listed. Offline, seconds.
PYTHONUTF8=1 py -3.12 audit_handoff_invariants.py
PYTHONUTF8=1 py -3.12 audit_handoff_invariants.py --self-test   # 7 cases; ⛔ MUST stay green                  # line budgets, banners, flag registry
PYTHONUTF8=1 py -3.12 audit_doc_consistency.py      # docs vs code vs each other
PYTHONUTF8=1 py -3.12 audit_encoding.py             # mojibake + BOM; --repair fixes in place
#   All three must exit 0. Each also takes --self-test, which FAULT-TESTS the gate itself.
#   ‼ audit_encoding exists because PowerShell `Get-Content`+`Set-Content` corrupted 343
#     lines of THIS FILE on 2026-08-14 while every other gate passed. NEVER read-modify-write
#     a doc with PowerShell; use the editor or Python with encoding='utf-8'. Appending with
#     `Add-Content -Encoding utf8` is safe (it never reads the existing bytes).

# --- THE SANDBOX <-> CUSTOM DRIFT CHECK (was only in the ARCHIVE; it belongs here) ---
PYTHONUTF8=1 py -3.12 promote.py --check            # measures drift BOTH ways, changes nothing
#   ‼ THE `PYTHONUTF8=1` PREFIX IS LOAD-BEARING, NOT DECORATION. Without it this crashes with
#   `UnicodeEncodeError: '→'` before printing the figure — it prints a `sandbox → custom`
#   arrow. A 2026-08-15 cold-start audit hit exactly that by copying the bare command out of the
#   PROSE mentions elsewhere in this file, which omit the prefix. ⇒ copy the line above, not
#   the prose. (The failure is loud, so it misleads nobody — it just wastes a minute.)
#   Expect as of 2026-09-02 (LATEST): 9 differing (the drift-row list + `map_data.py`, §Ch21 leg 2a — NOT a promotion decision) (the abort guards were PROMOTED; formerly 1, sandbox
#   only, PROMOTION DECISION OWED), 0 orphaned. ⛔ The tool is the authority, never this comment. — everything ELSE promoted incl. the KI-66 `_on_field` fix, the KI-65 fix, the KI-81
#   whiteout guard included. ANY file listed is unexplained drift.
#   ‼ THE FIGURE ABOVE HAS SWUNG ONCE PER PROMOTION, so DO NOT pattern-match it — RUN the command.
#     ⛔ Superseded figures are DESCRIBED here, never reprinted: an earlier retraction quoted the
#     old number verbatim and became byte-identical to the claim it retracted (and
#     `audit_doc_consistency` cannot tell a quotation from a claim, so it turned the line red).
#   ‼ DIGITS, NOT WORDS, AND CASE-INSENSITIVELY: a spelled-out "THREE" went stale here for a day,
#     and a capital "drift was 8 as of 2026-08-27 (it is 9 now) — see the STATE row (`map_data.py` joined for §Ch21 leg 2a); formerly 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until the chapter is driven)" survived a lowercase sweep on 2026-08-16.
#   To PROMOTE (the USER's call, never assume it): create + PUSH an annotated restore tag,
#   then `promote.py --restore-point <tag> --go`. It REFUSES on a dirty tree, a missing or
#   UNPUSHED tag, a diverged remote, or a no-op — and it cannot drive, so a copy is NOT
#   evidence: verify with a real driver `--build custom` afterwards.
PYTHONUTF8=1 py -3.12 repro_pid_identity_key.py --build custom       # gates that can SEE
PYTHONUTF8=1 py -3.12 repro_box_counter_move_test.py --build custom  #   the other fork
#   Expect BOTH: `(importing from custom-pokebot — verified)` then `ALL CHECKS PASS`,
#   exit 0. The import line is the point — it proves the gate tested the fork you meant.
#   Both ASSERT which fork they imported before testing. A gate that only ever imports
#   sandbox cannot tell you whether a promoted fix actually landed.
```

‼ **A driver keeps running after it prints ACCEPTANCE** — it drops to Manual and the harness only
exits on its own 20,000-idle-frame detector, logging **"HANG CONFIRMED"** on a run that SUCCEEDED.
**Read the `ACCEPTANCE:` line, not the last line.** Full transcripts land in
the harness log — ⛔ **whose path the run PRINTS as its first line** (`[setup] LOG -> …`),
because names are unique per run since 2026-08-16; `ls -t tools/story-dev/harness_*.log | head -1`
finds the newest afterwards.

‼ **VERIFY THE SANDBOX↔CUSTOM DRIFT ROW RATHER THAN TRUSTING IT** — `promote.py --check` is in the block above and measures it BOTH ways in seconds. ✅ **Expected as of 2026-09-02 (LATEST): 9 differing (the drift-row list + `map_data.py` + the NEW `sootopolis_gym.py`), 0 orphaned — PROMOTION DONE 2026-08-24. Formerly 0 differing, EVERYTHING PROMOTED** (the five-file promotion, user-approved) — everything ELSE is promoted (⚠ the five sandbox-only files are NOT): the KI-66 `_on_field` fix (2026-08-17), the KI-65 fix (2026-08-16), and the KI-81 whiteout guard before them. ⛔ ANY file listed is unexplained. *(This line was the SURVIVOR an adversarial review caught on 2026-08-16 — a 13-site hand sweep missed it AND `audit_doc_consistency` passed over it, which is the false negative `#24-driftassertions` exists to remove.)* *(This line said "0 differing, 0 orphaned" until a Tier 2 cold-start audit found it, along with the sibling line in the command block above, still claiming 0 after three other places in this file had been corrected to 1. ALL drift statements in this file move together or not at all — ⛔ a COUNT here has been wrong twice ('three' vs 'five'; the real sweep found THIRTEEN across five files). GREP, case-insensitively, print the MATCH not the line, and require zero.)* Superseded: *"the PowerShell loop is in `28-HANDOFF-ARCHIVE.md`'s copy of this section"*, together with an older expected-count naming `modules/map_path.py`, `modules/story/early_game.py` and `plugins/custom_modes/story_mode.py` — all PROMOTED now and not part of the current drift set. ‼ **The old FIGURE is deliberately not reprinted**: `audit_doc_consistency` cannot tell a quotation from a claim, so quoting a stale count turns this line red (it did). ‼ `tools/story-dev/` is sandbox-only and is **not** part of that comparison, so the `ch20*` drivers, `probe_route128_landing.py` and `repro_party_accounting.py` do not change the count.

---

# 📚 EARLIER HANDOFF SNAPSHOTS → `28-HANDOFF-ARCHIVE.md`

Every superseded "you are here" section now lives in **`28-HANDOFF-ARCHIVE.md`** (append-only).
This file is CURRENT STATE only — if something here is no longer true, fix it here rather than
adding another banner below it.
