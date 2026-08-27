# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-08-26 — start at the single orientation block immediately below.
Every banner further down is HISTORY, newest first.

---
# ‼ YOU ARE HERE (2026-08-18, SESSION END) — **THE LIVE WORK IS THE PC / PARTY ROBUSTNESS ARC, AND IT IS AT A CLEAN BOUNDARY **AS OF THE COMMIT CARRYING THIS LINE** (a cold-start audit correctly flagged the earlier absolute wording: a banner cannot truthfully say "everything is pushed" while it is itself the uncommitted edit — so read this as *"true at this commit"*, and trust `git status` over any prose). ⚠ **DRIFT IS 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) AS OF 2026-08-23** (`early_game.py`, `#24-loopheadabort`, sandbox-only — ⛔ PROMOTION DONE 2026-08-24, the USER's call). *(It was 0 after ALL FIVE WERE PROMOTED 2026-08-17, USER-APPROVED)* (the `#24-orphans` (1) verdict change, the `#24-abortswallow` guards and the `#24-ki76correctness` COMMENT-ONLY map_path fix). ⛔ NOTHING awaits a promotion decision now** (all five, now IN BOTH FORKS: `pc_trip.py`, `higher_level_actions.py`, `early_game.py`, `counter_hunt.py`, `map_path.py` — ⛔ the STATE row is the authority for this list, and `promote.py --check` outranks both); everything BEFORE them was already promoted, the KI-66 `_on_field` fix included (2026-08-17, user-approved, THREE-POINT A/B against `--build custom`, not a byte-compare). BOTH `story_mode.py` changes are promoted too (the comment-only correction and the **KI-80 DECOUPLING**, a BEHAVIOUR change proven by a THREE-POINT A/B against `--build custom`), user-approved 2026-08-16.** ✅ **(P4) IS DRIVEN THROUGH STAGE 2** — the real heal COLLECTS the boxed counter and leads with it (ARM B), and ARM A leaves it boxed, reproducing the user's derail ORGANICALLY; matrix {ARM A, ARM B} x {sandbox, custom} = **5/5 ACCEPTANCE: PASS**. ✅ **BOTH PROMOTIONS ARE DONE (user-approved): `counter_hunt.py` (comment-only) and `pc_trip.py` (KI-79, a BEHAVIOUR change proven by a three-point A/B).** ⛔ **(P6) WAS INVESTIGATED AND REFUTED — its "obvious" fix is a REGRESSION; see KI-80, now GATED (suite #24).** ✅✅ **KI-80'S REPRO DRIVER IS BUILT, DRIVEN AND FAULT-TESTED — `--driver ki80ladder`, 3 arms, `ACCEPTANCE: PASS` in BOTH forks, and KI-80 is REPRODUCED (Winona's real Route 119 patch DELETES her counter ladder). ⛔ DO NOT REBUILD IT.** ✅✅ **KI-80 IS DECOUPLED — BUILT, DRIVEN AND REVIEWED (sandbox only).** `POKEBOT_KI80_DECOUPLED=1` went **FAIL → PASS**, arm 4 (the mirror-regression guard) **still PASSES**, the old coupled expectation now **FAILS** (proving behaviour changed), and `repro_boss_grass_gate.py` **SELF-RETIRED**. ✅ **AND PROMOTED TO BOTH FORKS 2026-08-16 (user-approved), by a THREE-POINT A/B against `--build custom`: `POKEBOT_KI80_DECOUPLED=1` FAIL → PASS, the coupled expectation PASS → FAIL, arm 4 PASS on both sides.** ✅✅ **THE WHOLE KI-80 ARC IS COMPLETE AND PROMOTED — reproduced, fixed, guarded, reviewed, and in BOTH forks. ⛔ DO NOT REOPEN IT.** ✅ **The UNRELATED KI-81 whiteout guard was also promoted 2026-08-16 — drift was 0 at that point and nothing awaited a ruling — the KI-66 `_on_field` fix was PROMOTED 2026-08-17, user-approved. ⚠ **TODAY (2026-08-24) drift is 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until the chapter is driven) — `modules/story/seafloor_cavern.py`, the §Ch20 chapter UNDER CONSTRUCTION, sandbox only. ⛔ NOT a promotion decision: it is incomplete (constants + predicates + preflight only, no legs yet) and must not be promoted until it is driven end to end.** ✅ The abort guards themselves are PROMOTED and their drift is 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven). — `early_game.py` (`#24-loopheadabort` + `#24-abortrecoveryresiduals` (b)/(c)) was PROMOTED 2026-08-24, user-approved. *(It was 0 when all five were PROMOTED 2026-08-17, user-approved, each with its own before/after discriminator and a live drive against custom.** ➡➡ **✅✅✅ THE FIVE-PASS DEEP SANITY CHECK IS COMPLETE (passes 1-5, 2026-08-22). ⛔ DO NOT RE-RUN ANY PASS.** ✅✅ **`#24-loopheadabort` IS DONE 2026-08-23 — ALL 17 nav retry loops patched, GATED as #30. ⛔ DO NOT REDO IT.** ⛔ **An earlier draft excluded 3 of them claiming they run "while the latch is SET" — an adversarial review REFUTED that and it is WITHDRAWN: `StoryMode.run` clears the latch BEFORE every recovery routine, in both branches (AST-verified). Gate #30 §1 now enforces THAT ORDERING**, because the hazard is real only if someone hoists the recovery calls above the clear. Proven by a two-armed drive of the real `_navigate_through_scripts`: ARM A `nav_attempts=25` + the FABRICATED cause, ARM B `nav_attempts=0` + `StoryAbort`. ✅✅ **`#24-p4residuals` IS 6 OF 7 DONE (2026-08-23) — (a) `--strict`, (b) fence-blanking, (c) `splitlines()`, (d) a DENYLIST, (e) `--build` on three gates, (g) proximity-scoped supersede; each fault-tested BOTH ways. ⛔ TWO of them REFUTED the item's own proposed fix by MEASUREMENT before any code changed.** Only **(f)** remains and is deferred deliberately (a real emulator drive inside a 573-line gate). ⚠ NO production code was touched, so drift is unchanged. ✅ **THE PROMOTION IS DONE (2026-08-24, user-approved) — drift is 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) and the forks are EQUAL; custom went 8 AST abort-swallowers → 0.** ✅✅✅ **§Ch20 IS A CHAPTER NOW (2026-08-24) — THE STORY FRONTIER MOVED.** `modules/story/seafloor_cavern.py` (971 lines) is wired as **Segment 19b (teach Dive) + Segment 20**, and the PRODUCTION entry point drove **5/5 ACCEPTANCE: PASS** — clean, plus ALL THREE recovery paths exercised by fault injection (`room8_recoveries=1`; `route128_resumes=1` with `room8_recoveries=0`, proving attempt 2 never re-dived into the permanently-disarmed trigger). ⛔ Dive is still INJECTED by the driver, so these are ASSEMBLY tests, not end-to-end story tests. ⛔⛔ **THE USER REDIRECTED PRIORITIES ON 2026-08-26 — THREE PRODUCTION DEFECTS FROM REAL TESTING (single instance, Mudkip) NOW OUTRANK §Ch21** *(status after the MINED validation batch, late 2026-08-26: `#26-mossdeeppuzzlespeed` ✅ FIXED ~2.9× A/B-proven; `#26-surfteachchain` D1/D2 gates ✅ LIVE-VALIDATED — 7 of 10 teach-failure runs FINISHED; `#26-manualderails` Fortree half ✅ the SECOND WIND is END-TO-END PROVEN (27 live firings; ⚠ post-wind same-count repeat burn = an OPEN USER QUESTION); `#26-fleefreeze` ✅ ARC CLOSED (live arm landed, zero CantEscape freezes); `#26-battleitemwedge` hang-fix shipped, its live arm = the NEXT batch; finish rate 8/31 = 25.8% vs baseline 12.0%; ⛔ Treecko 0/6 unchanged)*:** `#26-manualderails` (reverts to MANUAL around Fortree/Mossdeep, recoverable by re-selecting Story — so a guard/retry hands off, not a wedge), `#26-surfteachchain` (post-Norman HM03 A-spam re-talks the NPC and re-teaches, sometimes the WRONG HM; plus the DESIGN GAP that a non-Mudkip run may hold no Surf learner at all), and `#26-mossdeeppuzzlespeed` (solved correctly but far too slowly; keep the stuck detection). ➡ §Ch21 leg 2 is PARKED, NOT CANCELLED — its build spec survived adversarial verification and is saved at `ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md`. ✅✅ **§Ch21 LEG 1 IS BUILT AND DRIVEN (2026-08-24) — the bot dives from Route 128 into Sootopolis by itself.** `modules/story/sootopolis.py`, `--driver ch21dive`, `ACCEPTANCE: PASS`, fixture `saves/post_sootopolis_arrival.ss1` (PINNED). ⛔ **NOT wired into `_play()` — legs 2-5 do not exist.** ‼ Three drives: the first two FAILED usefully (the arrival cutscene was still running; then MY acceptance check demanded a walkable path to the Cave of Origin, which Emerald never provides — Steven WARPS you in). ⇒ **leg 2 is FIND STEVEN, not walk to the cave.** ➡➡ **THE RECON IS DONE (2026-08-24) — THE REST OF THE CHAPTER IS *NOT* BUILT.** Five agents, one angle each, every load-bearing claim re-verified here. ⛔ **READ THE §Ch21 ATLAS IN `12-STORYMODE-DESIGN.md` BEFORE WRITING ANY Ch21 CODE.** Three results a cold reader must not re-derive: (1) the **Mach Bike is NOT needed** and two rows of `12-STORYMODE-DESIGN` said it was — corrected; (2) the ascent **REQUIRES a deliberate fall through `4F (6,4)`/`(7,4)`** (⛔ NOT `(9,4)`, a decoy) and **no pathfinder here can propose it** — `map_path.py` does not model `"Cracked Floor"`; (3) **there is no air option** — `VISITED_PACIFIDLOG_TOWN` and `VISITED_SOOTOPOLIS_CITY` are both **False**, measured, so entry and exit are BOTH by water. ‼ Ch21 is *enterable*, but "enterable" was never the question — it is **~5 legs**, and its multichoice in `CaveOfOrigin_B1F` hangs FOREVER on any answer but index 2. ✅✅ **`#24-p2headergate` IS DONE 2026-08-23** — **TWO** checks shipped (symmetric P2 header/body rule; control-character guard) and a THIRD (ratchet-baseline claims) **deliberately DELETED after a six-angle review returned 7 blockers on it — 289 lines removed**. Suite unchanged at 30 = 28 ENFORCING + 2 ADVISORY. ✅✅ **`#24-brokenrepros` IS ALSO DONE 2026-08-23** — the item said FIVE, a full sweep found SIX, each with a different root cause; the sixth was invisible because a doc filed it as "needs a real mgba", and **that same script had been misfiled the same way once before**. Filed `#24-reprosweepratchet` for the structural cause: none of the 104 repros is in `run_gates.py`, and what the suite does not run, rots. ✅✅ **`#24-abortrecoveryresiduals` (b) IS DONE 2026-08-23** — the 5 abort-swallowers my loop-head fix created are guarded, swallowing functions 11 → 7, proven two-armed (latch clear → swallowed, unchanged; latch set → re-raised) and the ratchet turned 36 → 31 WITH the control arm it demands. ✅✅ **`#24-abortrecoveryresiduals` IS FULLY RESOLVED 2026-08-23 — (a), (b) AND (c).** The abort-swallow class is CLOSED in sandbox (AST finds ZERO; ratchet 36 → 31 → 23, control-armed at each step). **(a) was ASSESSED, not coded**: a second whiteout during recovery cannot realistically occur — the window is spent on maps with ROM land-encounter rate **0**, `on_whiteout()` cannot fire twice on Emerald, and it has never happened in **16,688 recorded recoveries**. ⛔ **ON PROMOTION, LOWER the probe's custom baseline 36 → 23 IN THE SAME COMMIT.** ⛔ **ON PROMOTION, lower `probe_abort_swallowing.py`'s custom baseline 36 → 31 in the SAME commit.** ⛔ **NOT `#24-ki76correctness`** — pass 5 proved its only fixture is VACUOUS for its only live defect (it stages in ROOM6, which has ZERO armed dismount chains), so a dismount A/B there would print "no difference" and read as a REFUTATION of a real 1,852-chain defect; it is BLOCKED until an anchor is captured on ROUTE132/133/134 or ROOM7 with Surf. *(Its one zero-input sub-task IS startable: the single `get_map_data` check of ROUTE134 `(60,31)`.)* **PASS 4 (INFRASTRUCTURE) IS DONE — ⛔ DO NOT RE-RUN IT.** It found **THREE STANDING GATES THAT COULD NOT FAIL** (`probe_slot_free_plan`, `probe_regi_capabilities`, `probe_dive_routing` — zero assertions, printing 4/23/6 alarm lines while the suite said PASS), a **gate runner with NO TIME BOUND**, **seven "observe-only" gates writing shared profile state** (2,820 files / 160 MB), and **8 BYPASSES + 1 FALSE POSITIVE in the `git add -A` hook CLAUDE.md calls "ENFORCED"**. All fixed and fault-tested; the suite is now **29 gates = 27 ENFORCING + 2 ADVISORY** (a new tier — see `06-DECISIONS-LOG.md`). ‼ Five items were FILED, not fixed: `#24-fixturecoverage`, `#24-gateselftests`, `#24-testrunsweep`, `#24-p4residuals`, `#24-flagnamedocscan`. ✅ **KI-82 IS CLOSED (2026-08-23) AND NOTHING AWAITS A RULING** — the tracked Emerald ROM had already been ruled KEEP on 2026-07-18 and the user re-affirmed it; ⛔ do not re-raise it (see `05-KNOWN-ISSUES.md` KI-82). ‼ The method that made passes 1-3 work: 8 agents per pass, one ANGLE each, and **every agent required to FAULT-INJECT or RE-DERIVE, never to reason** — that single instruction is what found a gate that could not fail and a control that could not fail. ⛔ VERIFY EVERY AGENT FINDING YOURSELF: 2 of ~40 were false positives. ➡ **THEN, the standing queue head is `#24-ki76correctness`** — ⛔ but read it first: its ends-on-a-warp defect is CONFIRMED LIVE, and its planner-side half is **VACUOUS ON THIS ROM, measured over 54,990 pathfinding calls** (`(14,8)` is a topological dead end, so a COST test is vacuous too). That half is BLOCKED ON REALITY, not effort. ⚠ The DISMOUNT defect is UNCONFIRMED and needs its OWN fixture — Room 7 has no driver.** ✅✅ **`#24-orphans` (5) AND (6) ARE BOTH DONE 2026-08-17 — ⛔ DO NOT REBUILD EITHER.** (5)'s premise was REFUTED before anything was built: `compare_runs.py` already existed AND already paired, but fed a real A/B (`ACCEPTANCE: FAIL` vs `PASS`) it clustered the arms as IDENTICAL on all four axes — so an `ACCEPTANCE` axis + `A/B DISCRIMINATION` section shipped instead of the requested wrapper, fault-tested four ways (test 4 caught a defect in the fix itself). ⚠ `tools/` is shared — no promotion twin. (6) closed the ORPHANING only: KI-76's correctness half now HAS an item; **its two defects remain OPEN**, and are MEASURED (production as the oracle: dismount **1,852** armed, ends-on-warp **9 and all in ROOM6, zero on the routes** — so KI-76's old header was half backwards). ⚠ **DRIFT IS 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) AS OF 2026-08-23** (`early_game.py`, `#24-loopheadabort`, sandbox-only — the promotion is DONE 2026-08-24). *(It reached zero when ALL FIVE FILES WERE PROMOTED 2026-08-17, USER-APPROVED)*, each with its own before/after discriminator (the verdict gate 1→0 on custom; the abort probe 44→36 on custom; map_path byte-equal and still AST-equal) plus a LIVE DRIVE against custom that printed `verdict landed=True code=landed` — the promoted branch RUNNING, not a file that copied. Restore point `restore/2026-08-17-pre-promotion-all5`. ✅ `#24-abortswallow` ROUND 3 is **DONE 2026-08-17**: refinement (1) shipped (37 → 36), refinement (2) **REFUTED** (it would blind the gate to five already-fixed sites, one of them an OBSERVED failure), and the probe is now **gate #27, a RATCHET at baseline 36**, fault-tested both ways. ⛔ DO NOT REBUILD ANY OF THAT.The previous next action, `(P4c) #24-orphans` (1), is HALF DONE 2026-08-17: its INSTRUMENTATION half is BUILT, GATED (#26) and A/B-PROVEN — `withdraw_from_box` returns `(landed, code, detail)`, its ONE caller BINDS it, ARM B `landed=True code=landed` vs ARM A `landed=False code=did_not_land`. ⛔ DO NOT REBUILD IT. Its REACTION half stays OPEN and still needs the USER plus an unmeasured heap offset.** ⚠ **DRIFT IS 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) AS OF 2026-08-24** — `early_game.py` was PROMOTED 2026-08-24 (user-approved), so nothing is owed. *(Those five files were PROMOTED 2026-08-17, user-approved.)* ✅ The previous next action, `#24-driftassertions`, is **DONE 2026-08-17: the drift-statement sweep IS a gate now** — `check_drift` detects CLAIM SHAPE, A/B-measured 4→9 sites caught with none lost, 17 fault tests (`--self-test` D9–D22, including two BYPASSES an adversarial review found in the first draft and which were reproduced before fixing). ⛔ DO NOT REBUILD IT; its separate REDUCTION half is filed as `#24-driftreduction`. ✅ The previous next action, `#24-faintchooser-fourthspace`, is ANSWERED 2026-08-17: the probe was built and driven, **no fourth index space is demonstrated**, the anomaly is INERT — ⛔ do not "fix" it. ✅ `#24-orphans`: (4) and (2) DONE; **(3) KI-66 is PARTLY DONE** — its `_on_field` half is FIXED, DRIVEN and PROMOTED 2026-08-17, its OWNER-filter half is still open and measured INERT on the one fixture we have. Remaining there: (1) and (3)-owner-half ONLY — ⛔ (5) and (6) are DONE 2026-08-17 and this clause listed them as remaining for one commit (a Tier 2 audit caught it). ✅✅✅ **(2) KI-65 IS FULLY CLOSED — REPRODUCED, FIXED, A/B-PROVEN, GATED (#25) AND **PROMOTED TO BOTH FORKS** ON 2026-08-16 (user-approved). ⛔ DO NOT REBUILD OR RE-PROMOTE IT.** Proven by a THREE-POINT A/B against `--build custom` (BEFORE `lie_msg=1` → FAIL; AFTER `lie_msg=0, honest_msg=1` → PASS; sandbox still PASS), with COMMITTED transcripts under `tools/story-dev/evidence/2026-08-16-ki65-PROMOTION-*`. ⛔ Its recon's prescribed fixture was REFUTED by measurement — do not retry `movelearn_hmwedge_*.ss1` on it. ⛔ **Its COST ranking and its STARTABILITY ranking differ, and the item lists only cost.** Costliest is **(1)** — no caller acts on `withdraw_from_box`'s verdict — ✅ **the USER'S RULING EXISTS** — *"reattempt but after intelligently processing the data (text boxes it reads to determine why it failed)"* (`06-DECISIONS-LOG.md`) — ⛔ **BUT IT IS NOT READY TO BUILD: a recon found a BLOCKER (the PC message buffer `sStorage->messageText` is HEAP-allocated and its offset is NOT known here — it must be MEASURED, and until it is every failure classifies UNKNOWN, which must not retry, so the feature would ship INERT) plus FOUR PREREQUISITES.** Read `06-DECISIONS-LOG.md`'s design entry FIRST. ⇒ **✅✅ **(3) KI-66 IS NOW *DRIVEN*, NOT PENDING (2026-08-17): `--driver ki66faint` is BUILT and WORKS — ⛔ DO NOT REBUILD IT. Its "sends out an ALLY's mon" HEADLINE IS REFUTED (the bot never ASKED FOR an ally slot); the REAL defect is `_on_field`'s INDEX SPACE, costing 1263 frames vs 59. ➡ ✅✅ **`_on_field`'s INDEX SPACE IS FIXED AND PROMOTED TO BOTH FORKS (2026-08-17, user-approved). ⛔ DO NOT REDO IT.** Direction MEASURED first by an observe-only probe, then applied; all gates PASSED when that landed (**25** at the time — ⛔ the CURRENT count is deliberately not repeated here; `run_gates.py` prints it and IS the authority. This sentence has now been stale at 25 AND at 26 — ⛔ `run_gates.py` prints its own count and IS the authority, never this sentence). ➡ **NEXT: the OWNER filter is still unfixed and proved INERT on this fixture — it needs its OWN discriminator, not this one. `:541-545` and `_util.py:522-587` are also untouched.** Formerly: "the genuinely startable work with zero input is now (3) KI-66"** — ✅✅ **(2) KI-65 IS DONE (2026-08-16): reproduced, fixed, A/B-proven, gated as #25. ⛔ DO NOT REBUILD IT.** ⛔ When (1) IS built: NOT a blind retry — bound it, diagnose from READ text, and an UNKNOWN reason must stop loudly rather than retry. **(3) KI-66** is four unguarded full-party scans, one feeding an UNBOUNDED `while … press A`. *(Also tracked: `#24-logcollision-siblings`, `#24-zerokocounter`, (P5).)* §Ch20's chapter assembly stays **PARKED, NOT CANCELLED**. Read this, then `14-AGENT-PLAYBOOK.md`, then NEXT ACTIONS item 0.

> ⛔ **ORDER, EXPLICITLY (a Tier 2 cold-start audit could not tell which of these came first):
> (1) RUN THE RITUAL BELOW — it is cheap and it tells you whether the tree is sane; (2) READ
> `14-AGENT-PLAYBOOK.md`; (3) GO TO `NEXT ACTIONS` item 0 — ‼ **and READ DOWN TO THE `➡➡➡` MARKER.**
> Item 0 opens with ~148 lines of ✅-DONE history (§Ch20 rooms, P1/P2, KI-80, the 2026-08-14 user
> redirect); **the live instruction is the `➡➡➡` line**, not the first thing under the heading.** The banner sentence above lists the
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
> — **both must exit 0; the suite is 32 gates (30 ENFORCING + 2 ADVISORY; #32 = the fleefreeze delegation, 2026-08-26)** ⚠ *(ONE EXPECTED EXCEPTION: if a session deliberately
> holds a commit for a Tier 2 audit, `preflight.py` exits 1 on "git is AHEAD of the remote". That is
> the ritual working, not a broken tree — report it and push, per `CLAUDE.md`.)* (it prints its own count — believe that, not this
> line, which has been wrong at 17, 18, 19, 20, 21 and 25 on the way here). ‼ **The 25 was found by a Tier 1 reviewer, FOUR LINES above a correct `26/26`** — the gate could not see this phrasing until the same commit taught it to. That ritual survived the 2026-08-14
> priority redirect and is NOT part of the superseded "older framing".

> **State: `main`, 32/32 gates green (**29 ENFORCING + 2 ADVISORY** — ‼ this read '28 + 2' against a 31 total, which does not even add up), drift **2** (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its wiring, sandbox only; ⛔ NOT a promotion decision until it is driven further. `early_game.py`'s promotion was DONE 2026-08-24), nothing parked MID-TASK, nothing running.** ✅ **NOTHING ELSE — BEYOND THE PROMOTION DECISION NAMED ABOVE — AWAITS A USER RULING.** *(KI-82 — the tracked Emerald ROM — was CLOSED 2026-08-23: it had ALREADY been ruled on 2026-07-18 (`06-DECISIONS-LOG.md`, "keep it as is"), and the user re-affirmed it. ⛔ Do not re-raise it; the only condition that reopens it is the repo being made PUBLIC.)*
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
> half-edited work and no `/checkpoint` debt; it does **NOT** mean nothing is parked — **§Ch20 chapter
> assembly IS parked**, deliberately, finished and waiting (NEXT ACTIONS item 0).
> ⚠ **EXPECTED DIRT — READ BEFORE BELIEVING `preflight.py`'s WARN:** every `story_harness.py` drive
> APPENDS to the TRACKED `tools/story-dev/party_accounting_ledger.jsonl` ((P3b)'s observer ledger),
> so after ANY driver run `git status` shows it modified and preflight prints `WARN 1 uncommitted
> file(s)`. **Expected, not a broken tree.** ⛔ Do NOT `git checkout --` it — COMMIT it with the work
> that produced it. ✅ **2026-08-16: `preflight.py` now LISTS the dirty files and annotates this one
> in place** — *"EXPECTED after any driver run; COMMIT it, never `git checkout --` it"* — so the tool
> answers the question at the point of confusion. This line is now the BACKUP, not the only way.
> ⚠ **THE DRIFT FIGURE IS 1 AND PROMOTION DONE 2026-08-24 (2026-08-23).** ‼ **DRIFT IS 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) AS OF 2026-08-23** — `modules/story/early_game.py`, the `#24-loopheadabort` loop-head abort checks (sandbox only). ⛔ **A PROMOTION DECISION IS NOW OWED and it is the USER's call.** ⛔ Never read a drift figure from prose: run `promote.py --check`. *(Superseded: "the drift figure is 0, and NO PROMOTION DECISION IS OWED")* — — `pc_trip.py`, `higher_level_actions.py`, `early_game.py`, `counter_hunt.py`, `map_path.py` (the `#24-orphans` (1) verdict change, the `#24-abortswallow` abort guards, and `#24-ki76correctness`s COMMENT-ONLY cap correction) — ✅ ALL FIVE WERE PROMOTED 2026-08-17, user-approved; ⛔ this clause read "all sandbox-only" for one commit AFTER the promotion, which is the exact contradiction a Tier 2 audit stops for. ⛔ Everything BEFORE it is promoted (the KI-66 `_on_field` fix 2026-08-17, KI-65 2026-08-16), each proven by a THREE-POINT A/B, never a byte-compare. *(⚠ DESCRIBED, NOT REPRINTED — this file's own convention, because the gate matches literal strings and cannot tell a quotation from a claim: this line asserted a ZERO figure, and 'everything is promoted', for a day after both stopped being true. A Tier 2 audit caught it; the gate now also matches the phrasing with a NOUN between 'drift' and 'is'.)*
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
> ✅ **BOTH the KI-79 fix (`pc_trip.py`) and the comment-only `counter_hunt.py` correction were
> PROMOTED 2026-08-15, user-approved.** ✅ **And `plugins/custom_modes/story_mode.py` (COMMENT-ONLY —
> the false "Thunderbolt vs Winona" example; Electric is NEUTRAL into Dragon/Flying) was PROMOTED
> 2026-08-16, user-approved.** ‼ That one was proved behaviour-neutral by **AST equality** before
> copying (not "the diff looks like comments"), and that check was fault-tested.
> ‼ The behaviour change was proven by a **THREE-POINT A/B**, because "1/1 byte-identical" only
> proves a file was COPIED, never that its new branch is what RUNS: with
> `POKEBOT_PCWITHDRAW_FAULT=1` against `--build custom`, the IDENTICAL command went **PASS (hook
> absent, inert) BEFORE → FAIL (`‼ THE WITHDRAW DID NOT LAND`) AFTER**, and an unfaulted AFTER
> run still PASSed. Restore point `restore/2026-08-15-pre-promotion-ki79-pctrip`. ✅ The earlier comment-only `counter_hunt.py` correction WAS promoted 2026-08-15,
> user-approved, and — because a copy is not evidence — VERIFIED BY DRIVING:
> `--driver boxcounter2 --build custom` ARM A **and** ARM B both `ACCEPTANCE: PASS`, plus four
> `--build custom` gates. Restore point `restore/2026-08-15-pre-promotion-counterhunt-comment`.
> Everything else was PROMOTED 2026-08-15, user-approved and VERIFIED BY DRIVING
> (`--driver ch20dive --build custom` → `ACCEPTANCE: PASS`, plus four `--build custom` gates that
> each assert which fork they imported). ‼ **`promote.py --check` IS the authority — ⛔ and this line no longer quotes a digit, per
> `#24-driftreduction`: read the STATE table's drift row for today's figure and the sanctioned file
> list. A file it lists that the STATE row does NOT name is unexplained drift and a reason to stop.**
> ⛔⛔ **DIGITS, NOT WORDS — when you change a drift count, grep the WORD forms too.** *(Confirmed
> again 2026-08-15: the gate flagged 3 of 7 stale claims; the 4 it missed were spelled "zero",
> sat in a table cell, or read "0 as of". Full history of this line's four staleness incidents:
> `28-HANDOFF-ARCHIVE.md`.)*
> **Every room of the Seafloor Cavern is DRIVEN and PASSING** — `ch20dive` → rooms 1, 2, 6, 3, 8, 9
> (Kyogre awakened, `VAR_ROUTE128_STATE == 2`). **What remains of §Ch20 is CHAPTER ASSEMBLY.**

## ✅ §Ch20 — ALL NINE ROOMS DRIVEN AND PASSING (2026-08-13/14) — DETAIL in `28-HANDOFF-ARCHIVE.md`

⛔ **DO NOT REBUILD ANY OF THEM.** ‼ **Keep only the rules later work leans on:** graded on
**`VAR_ROUTE128_STATE == 2`**, never the Kyogre flag (set BEFORE a forced warp); the atoll escape is
**south to `(38,23)` then Surf onto `(38,24)`** (the landing tile has ZERO surfable neighbours, so a
naive Surf reads as a HUNG LEG); the **Archie fight is the chain's one stochastic element (2W/1L)**
and a LOST run prints nothing, so the chapter needs a whiteout-retry policy; *assert the OUTCOME,
not the position you expected*; *the instrument was wrong, not the claim*; *copy upstream's ROUTE,
never its CONTROL FLOW*; **`FLAG_SYS_USE_STRENGTH` is cleared on EVERY WARP**; and press **A only
when a text printer is waiting, B otherwise** (A beside an NPC starts a conversation).
## PATHFINDER + §Ch20 SCOPING BACKGROUND — in `28-HANDOFF-ARCHIVE.md`

‼ **Keep only what later work leans on:** (1) **KI-59** (the pathfinder's inverted `Impassable *`
handling) is **FIXED, PROVEN and GATED** (`repro_impassable_dirs.py`) — its headline was wrong in
FOUR documents: it is **NOT** armed in the Seafloor Cavern (all 115 tiles are `collision=1`);
game-wide **401 of 2,658** such tiles are live, chiefly the Regi tombs (144), Shoal Cave (98) and
Victory Road (58). (2) §Ch20's spec corrected our own docs: **ROCK SMASH is mandatory**, the trigger
tile is **`(17,42)` not `(16,42)`**, and the chapter grades on **`VAR_ROUTE128_STATE == 2`**, never
the Kyogre flag (set BEFORE a forced warp). (3) **KI-74/75/76** were filed there; KI-76's safety
half is fixed and fault-tested, its **correctness half is OPEN**.
⇒ ✅ **ALL NINE ROOMS ARE DRIVEN — the cavern is END TO END (2026-08-14). ⛔ DO NOT REBUILD ANY.**
## ⛔ NAMING: "§Ch21" IN OLDER TEXT MEANS **CHAPTER 20** (Seafloor Cavern / Kyogre, `chapters.py:233`)
The genuine Chapter 21 is Sootopolis / Rayquaza and is untouched. ✅ Rename DONE 2026-08-13
(`--driver ch20dive`, `probe_ch20_topology.py`). ‼ The old `ch21*` names SURVIVE ON PURPOSE in the
append-only `06`/`07`/`08` — entries dated on or before 2026-08-13 mean the Chapter 20 artefacts.

## ⏱ THE 60-SECOND VERSION (if you read nothing else) — rewritten 2026-08-15

* **The live arc is PC / PARTY ROBUSTNESS**, redirected here by the user on 2026-08-14 after a real
  run caught a Slugma for Winona, healed, derailed to Manual, and re-fought her WITHOUT the counter.
* ✅ **(P4) IS NOW DRIVEN THROUGH STAGE 2.** `--driver boxcounter2` (a SUBCLASS of `boxcounter`, so
  Stage 1 re-proves every run): the real Poké-Center heal **collects the boxed counter and leads
  with it** (ARM B), and ARM A — the shipped fault hook — **leaves it boxed**, reproducing the
  user's derail *organically*, from production logic rather than from the test.
  **{ARM A, ARM B} × {sandbox, custom} = 4/4 `ACCEPTANCE: PASS`.**
* ‼ **Three things the build corrected that four documents had agreed on:** `needed` for Winona is
  **{Rock, Ice, Dragon}, NOT {…Electric}** (her ace Altaria is Dragon/Flying and Electric is
  0.5×2.0 = **neutral**); the Stage 2 anchor is **`fortree_gym_wedge.ss1`, NOT
  `ch13_fortree_door.ss1`** (ROUTE120 is a KI-24 bridge map — the run cannot even reach the PC);
  and the `sole` control only ever passed because `post_dive.ss1`'s boxes are empty.
  ⇒ **Agreement between documents is not evidence — they may all be copies of one another.**
* ✅ **Both halves of (P4b) are DONE.** `counter_hunt.py` (comment-only) was promoted,
  user-approved and verified by driving. **KI-79 is FIXED and FAULT-PROVEN** — `withdraw_from_box`
  now verifies BY IDENTITY instead of announcing one from `len(get_party())`, and the new
  `POKEBOT_PCWITHDRAW_FAULT` hook makes the sabotaged case print `‼ THE WITHDRAW DID NOT LAND`
  where the old code printed green success. ✅ **AND IT IS PROMOTED** (user-approved) — proven by
  a three-point A/B that the new branch actually RUNS in custom, not merely that the file copied.
  **Both forks carry both fixes.** *(✅ And the KI-80 decoupling too, promoted 2026-08-16 — as was the KI-65 fix later the same day, which took drift to 0 AT THAT MOMENT. ⚠ **AND IT WAS 0 as of 2026-08-17; it is 1 as of 2026-08-23 (`early_game.py`, sandbox-only) — run `promote.py --check`** — the KI-66 `_on_field` fix was promoted that day, and the LATER `#24-orphans` (1) verdict change WAS sandbox-only and OWED a decision — ✅ it was PROMOTED 2026-08-17, user-approved, so NOTHING is owed now. *(This clause briefly read "NOT ZERO … a ruling is owed", which was true for about an hour and then was not; it is the reason rule 8 below exists. MEASURE with `promote.py --check`.)*)*
* **What (P4) still does NOT prove:** anything UPSTREAM of registration. The Slugma is INJECTED and
  its PID published by the driver, so the real `hunt()` → `story_mode.py:1750` wiring is untested.
* **§Ch20 (Seafloor Cavern) is DRIVEN END TO END** — all nine rooms, `ACCEPTANCE: PASS`. Its
  CHAPTER ASSEMBLY is **PARKED, NOT CANCELLED**. ⛔ Do not rebuild any room.
* 📚 The 2026-08-13-era 60-second version (roster / `puzzle_solver.py` / the first driven dive, all
  still true) moved to `28-HANDOFF-ARCHIVE.md` — it was two arcs stale in the FIRST thing a cold
  reader saw. ‼ Two of its rules still bite: **never let the planner choose a surfacing tile**
  (KI-72), and **`puzzle_solver.py` is a recipe book to COPY FROM, never to drive.**

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
| story content | ✅ **§Ch19 COMPLETE 2026-08-12 — the MOSSDEEP SPACE CENTER is defended and HM08 DIVE is in the bag. 20 of 24 beats.** Littleroot → 6 badges → Mt. Pyre → Magma Hideout (and out) → Slateport submarine theft → the Lilycove AQUA HIDEOUT (with the MASTER BALL) → the MIND BADGE → **the Space Center multi battle + Dive**. (was 19 of 24 before Ch19.) |
| ‼ **§Ch20 SEAFLOOR CAVERN** | ✅ **DRIVEN END TO END (2026-08-14) — Kyogre awakened, atoll escape executed.** Seven drivers, all `ACCEPTANCE: PASS`: `ch20dive` (6/6) → `ch20room1` → `ch20room2` → `ch20room6` → `ch20room3` → `ch20room8` (PASS ×2 incl. a FAULT run proving jam recovery) → **`ch20room9` (NEW, PASS ×2 — runs 1 & 3; ⚠ run 2 LOST the Archie fight, a MEASURED 2W/1L on the chain's one stochastic element)**. Each run re-solves every room beneath it (`FLAG_TEMP_*` respawn on map load) — counts now **R1 n=13, R2 n=10, R6 n=9, R3 n=8, R8 n=5, R9 scene n=3 (full chain n=2)**. The cutscene chain is deterministic (identical milestone frame counts across passing runs); release gated on `VAR_ROUTE128_STATE == 2`; facing on release MEASURED `'Up'` ×2. ✅ **IT IS A CHAPTER AS OF 2026-08-24** (`modules/story/seafloor_cavern.py`, wired as Segment 20, 5/5 drives PASS — commit `2680433f`). ⛔ *This row said "NOT a chapter" for one commit after it became one; a Tier 1 review caught it.* ‼ The ladder is **21 of 24** now, not the 20 quoted below. Superseded text: No module in `modules/story/`, nothing wired into `story_mode.py`, drivers **inject Dive with a debug write**. Ladder still **20 of 24**. **Remaining: CHAPTER ASSEMBLY** (organic Dive via KI-63 wiring, Repel policy, badge/move pre-flight, whiteout-retry for Archie, the atoll escape leg). |
| ‼ is code frozen? | **No.** Nothing is running. |
| party ORDER | ✅ **PROVEN 2026-08-13.** `--driver roster` from `saves/post_dive.ss1` → `phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True ACCEPTANCE: PASS`. Raw transcripts (both A/B arms) in `ai-research-notes/2026-08-13-roster-drive-predictions.md`. ‼ The **deposit/withdraw** half of `#24-roster` is still open. |
| upstream | checked **2026-08-23**, still `5dd898f8` — no change (re-fetched this session; `40cakes repo/UPDATE-LOG.md` already recorded the same date, and THAT file is the authority — this row only mirrors it). ‼ This row goes stale on a CALENDAR DAY, not on an event: if today's date is later than the one shown, **the daily check is DUE** (`git fetch upstream-pokebot`, compare against `40cakes repo/UPDATE-LOG.md`). Do not read it as satisfied. |
| restore point | **NEWEST: `restore/2026-08-17-pre-promotion-all5`** — taken immediately before the user-approved FIVE-FILE promotion (2026-08-17); roll back HERE to undo all five. Its BEFORE evidence is one commit EARLIER, in `0b1d8480`. Previous: **`restore/2026-08-17-pre-promotion-ki66-onfield`** (the KI-66 `_on_field` promotion). Previous: `restore/2026-08-16-pre-promotion-ki65`, then `restore/2026-08-16-pre-promotion-ki81-abort-guard` (the KI-81 whiteout guard — roll back HERE to undo it; its BEFORE evidence is one commit EARLIER, in `6de47264`). Then `restore/2026-08-16-pre-promotion-ki80-decoupling` (the KI-80 BEHAVIOUR promotion — roll back HERE to undo it; its BEFORE evidence is one commit EARLIER, in `1c11927e`). Then `…-credible-answer-comment` (2026-08-16), then `…-ki79-pctrip` (2026-08-15). ⛔ *This row has now been caught stale TWICE — once naming the wrong tag by TIME, once by failing to add two newer ones. Both times a rollback taken from it would have gone to the WRONG point.* ⛔ *This row named `…-counterhunt-comment` as newest until a 2026-08-15 cold-start audit checked the tag DATES: `ki79-pctrip` is 18:00, `counterhunt-comment` is 16:30. A rollback taken from the row as written would have reverted to the WRONG point.* ‼ **`git for-each-ref --sort=creatordate refs/tags/restore/` is the authority, not this row.** Also today, oldest-first: `…-stage0-p4`, `…-boxwrite-docstring`, `restore/2026-08-15-pre-promotion-counterhunt-comment` (annotated, pushed, and verified on origin by `promote.py` BEFORE it copied) — taken immediately before the user-approved comment-only `counter_hunt.py` promotion, and therefore the rollback point for it. ⛔ *The promotion HAS been taken; the older row below still called it "the promotion decision below" as if pending.* Older: **`restore/2026-08-13-session-end-ch20room3`** (annotated, pushed) — taken at the END of the §Ch20 cavern session, immediately before Room 8, which is the riskiest room in the dungeon (a boulder pushed onto `(5,3)` **permanently seals the exit**). ‼ It is also the natural rollback point if the **promotion decision** below is taken. Older: **`restore/2026-08-13-pre-ki63-promotion`** (annotated, pushed) — taken immediately BEFORE promoting KI-63's fix. Older: `restore/2026-08-13-pre-roster-promotion`, `restore/2026-08-12-pre-ch1819-promotion`. |
| sandbox ↔ custom drift | ⚠ **7 as of 2026-08-26, MEASURED by `promote.py --check`** — `modules/battle_action_selection.py` (the `#26-battleitemwedge` bounded bag-open) **+** `modules/battle_strategies/level_up.py` (the `#26-fleefreeze` delegate) **+** `modules/story/mossdeep_gym.py` + `modules/story/early_game.py` (the `#26-*` production fixes, A/B-proven, sandbox only — ⛔ NOT a promotion decision until the user rules) **plus** `modules/story/seafloor_cavern.py`, **`modules/story/sootopolis.py` (NEW 2026-08-24 — §Ch21 leg 1)** and `plugins/custom_modes/story_mode.py`, sandbox only. ‼ The count went 2 → 3 the moment leg 1 landed, and `check_drift` caught SEVEN stale "drift is 7" claims across two files — the gate doing exactly what it was built for. ⛔ NOT a promotion decision yet: §Ch20 is driven but §Ch21 is unbuilt, so the arc is mid-flight.** *(This cell led with "0 … Nothing is owed" for one commit after §Ch20 landed as a chapter — a Tier 1 review caught it, and the cell's own rule is the fix: **run `promote.py --check`, never trust this number**.)* ✅ **Previously 0 as of 2026-08-24** — the whiteout/abort guards were PROMOTED (user-approved) and the forks were EQUAL.** `early_game.py` carried `#24-loopheadabort` + `#24-abortrecoveryresiduals` (b) and (c); custom went 8 AST swallowers → 0, probe 36 → 23. Rollback tag `pre-promote-2026-08-24-abortguards`.** Run `promote.py --check`; it is the authority, never this cell. *(Previously: everything promoted 2026-08-17, USER-APPROVED: `pc_trip.py`, `higher_level_actions.py`, `early_game.py`, `counter_hunt.py`, `map_path.py`: the `#24-orphans` (1) verdict change and the `#24-abortswallow` abort guards. ✅ **THEY WERE SANDBOX-ONLY AND ARE NOW PROMOTED (2026-08-17, user-approved) — NOTHING AWAITS A DECISION.** Everything before it IS promoted, the KI-66 `_on_field` fix included (2026-08-17, user-approved; THREE-POINT A/B; restore point `restore/2026-08-17-pre-promotion-ki66-onfield`) and the KI-65 fix before it (2026-08-16, `restore/2026-08-16-pre-promotion-ki65`). *(Superseded the same day: this cell read "0 — EVERYTHING IS PROMOTED" after the KI-81 guard landed, which was true until the KI-65 fix. ‼ `audit_doc_consistency` did NOT catch it. ⛔ **The reason recorded here was WRONG and is corrected 2026-08-17:** it is NOT digits-vs-words (word forms ARE handled). It walked past `0 as of` because that is a CLAIM and the rule is scoped to an EXPECTATION. *(Hand-grepping word forms is still good advice for a human sweep — just not the gate's defect.)*)* Everything ELSE is promoted, the KI-81 WHITEOUT GUARD included (user-approved). Restore point `restore/2026-08-16-pre-promotion-ki81-abort-guard`. ‼ **Proven by a MEASURED before/after, not a byte-compare:** `probe_abort_swallowing.py --build custom` fell **53 → 45**, custom's guarded-handler counts moved **0→3 / 0→4 / 1→2**, the PathFindingError split survived the copy, and the guard mechanism was re-verified importing from CUSTOM. **History below.** ✅ Previously 0 as of 2026-08-16 — EVERYTHING WAS PROMOTED, including the KI-80 DECOUPLING (a BEHAVIOUR change), user-approved.** Restore point `restore/2026-08-16-pre-promotion-ki80-decoupling`. ‼ **Proven by a THREE-POINT A/B against `--build custom`, NOT a byte-compare** — identical commands: `POKEBOT_KI80_DECOUPLED=1` went **FAIL → PASS**, the coupled expectation went **PASS → FAIL** (the mirror), and **arm 4 stayed PASS on both sides** — that invariance is what shows KI-23's mirror regression did NOT land. ⛔ The BEFORE half is unrepeatable once the copy happens, so it was run and committed FIRST, in `1c11927e`. **History below.** ✅ The earlier **COMMENT-ONLY** correction was promoted 2026-08-16 (user-approved), restore point `restore/2026-08-16-pre-promotion-credible-answer-comment`: the `CREDIBLE_ANSWER_POWER` docstring justified the threshold with *"Thunderbolt vs Winona"*, which is FALSE — Electric is `0.5x` Dragon `x 2.0x` Flying = **NEUTRAL** into Altaria. It is the FIFTH copy of an error whose other four were corrected the same day. ✅ **PROMOTED 2026-08-16, user-approved**, as the earlier comment-only `counter_hunt.py` fix was. ‼ **Proved behaviour-neutral by AST EQUALITY before copying** — `ast.dump(parse(sandbox)) == ast.dump(parse(custom))`, 323,580 chars each — and ⛔ that check was FAULT-TESTED (flipping `CREDIBLE_ANSWER_POWER` 75→76 makes it return False), because a check that cannot fail proves nothing. ⚠ **There is no three-point A/B here and there cannot be**: a comment has no branch to flip, so AST identity + `1/1 byte-identical` is the proof, and the `--build custom` drives only show the file still loads. ⛔ The edit was made **net-zero on line count** so it did not shift the `story_mode.py:NNNN` citations that fill the append-only logs (verified after: `grass_is_fodder` still `:1899`, `winona_fight` still `:3532`). ‼ **That promotion left the tree fully promoted AT THAT TIME** (⚠ historical; the figure is DESCRIBED not reprinted, because the gate cannot tell history from a claim — today's number is at the TOP of this cell); ANY unexplained file is worth stopping for.** **The rest of this cell is HISTORY, kept for its promotion evidence.** ✅ **0 as of 2026-08-15 (the promotion round) — BOTH promotions were DONE, USER-APPROVED, and VERIFIED BY DRIVING.** (1) `modules/story/pc_trip.py` — the KI-79 fix, a **BEHAVIOUR** change, restore point `restore/2026-08-15-pre-promotion-ki79-pctrip`. ‼ **Proven by a THREE-POINT A/B, because 1/1 byte-identical only proves a file was COPIED, never that its new branch is what RUNS:** with `POKEBOT_PCWITHDRAW_FAULT=1` against `--build custom`, the IDENTICAL command went **PASS (hook absent, inert) BEFORE → FAIL (`‼ THE WITHDRAW DID NOT LAND`) AFTER**, and an unfaulted AFTER run still PASSed. Transcripts committed under `tools/story-dev/evidence/`. (2) `modules/story/counter_hunt.py` — the comment-only Electric correction, restore point `restore/2026-08-15-pre-promotion-counterhunt-comment`. Both are also green on four `--build custom` gates that each ASSERT which fork they imported, and on `boxcounter2 --build custom` ARM A. ‼ **MEASURE, don't trust this row** — `promote.py --check` is the authority. *(That round expected 0 AT THAT TIME; today's figure is at the TOP of this cell.)* ⛔ Digits, not words. **The rest of this cell is the PREVIOUS state, kept for its promotion evidence — read "0"/"ZERO" below as *"zero at that moment"*, not as today's figure.** ✅ **0 as of 2026-08-15 (earlier) — every drifted file was PROMOTED, user-approved, and VERIFIED BY DRIVING.** Promoted: `modules/party_accounting.py` (new), `modules/pokemon_party.py`, `modules/modes/util/higher_level_actions.py`, `modules/debug_utilities.py`, `modules/story/counter_hunt.py`. **Evidence:** tool-side drift 0 both directions + 5/5 byte-identical; **`--driver ch20dive --build custom` → `legs=6/6 … ACCEPTANCE: PASS`**, matching sandbox; and FOUR `--build custom` gates (`repro_party_accounting` 33, `repro_heal_piggyback_reporting` 20, `repro_box_counter_move_test`, `repro_pid_identity_key`) each ASSERTING which fork it imported. Restore point **`restore/2026-08-15-pre-promotion-stage0-p4`** (annotated, pushed, verified on origin by the tool before it copied). ⛔ **Digits, not words** — this cell read a spelled-out "THREE" for a day, invisible to `audit_doc_consistency`'s drift check, and it survived two doc passes. ⛔ **What promotion does NOT mean:** party accounting is still STAGE 0 (it observes and decides nothing), `debug_write_box_slot` is PROVEN LIVE (`--driver boxwrite` → PASS, 2026-08-15), and (P4) is driven through **STAGE 2** (`--driver boxcounter2`, 4/4 across both forks, 2026-08-15) — ⛔ *this sentence read "STAGE 2 … is NOT built" until Stage 2 landed the same day; the drift figures around it are historical, this clause is CURRENT.* ‼ **Anything else appearing in `promote.py --check` is unexplained drift and is worth stopping for.** ⛔ The rest of this cell is the PREVIOUS state and is kept for its promotion evidence — read "ZERO" below as *"zero at that moment"*, not as today's figure: ✅ **ZERO as of 2026-08-14 (earlier) — KI-78 STAGE 1 WAS PROMOTED, user-approved, and it is the first promotion executed by `tools/story-dev/promote.py` rather than by hand.** The tool refuses on a dirty tree, a missing or UNPUSHED restore point, a diverged remote, or a no-op, and it re-measures drift in BOTH directions plus byte-equality per file — it also refuses to claim the driven verification it cannot perform. Restore point **`restore/2026-08-14-pre-promotion-ki78`**. **Evidence:** drift 0 both directions, 3/3 byte-identical; **`repro_pid_identity_key.py --build custom` exit 0** and **`repro_box_counter_move_test.py --build custom` exit 0** (both ASSERT which fork they imported before testing); plus a live drive against custom. ⛔ **KI-78 is still not fully closed** — its residual cases (R2 debug-fabricated pairs, R3 corrupt box slots, R5 Frontier rentals, R6 evolved-since-capture) stay open. ‼ **MEASURE, don't trust this row** — `promote.py --check` (in HOW TO RUN / TEST) reports it BOTH ways in seconds — ⛔ **this historical sentence expected 0 because that was true on 2026-08-14; it is 0 again TODAY after the counter_hunt.py promotion — but do not act on a historical sentence, run the command.** 📚 Every earlier drift state — including the 2026-08-13/14 rounds where `map_path.py`, `early_game.py`, `story_mode.py`, `counter_hunt.py` and `pokemon_party.py` were awaiting promotion — moved to `28-HANDOFF-ARCHIVE.md` on 2026-08-14, because stacking four supersessions in one cell made a promoted file read as still pending. |
| **if stopped mid-task** | ⚠ **drift is 7, and TWO of the five are THIS SESSION'S OWN `#26-*` production fixes (`modules/story/mossdeep_gym.py` + `modules/story/early_game.py`, A/B-proven, sandbox only — ⛔ a PROMOTION DECISION IS OUTSTANDING and is the USER's call), plus `seafloor_cavern.py`, `sootopolis.py` and `story_mode.py` (the §Ch20/21 arc, mid-flight). ⛔ This cell said only "`seafloor_cavern.py` + `story_mode.py` UNDER CONSTRUCTION" after a mechanical digit bump — a Tier 1 review caught it as exactly the `#24-driftheadlineshape` shape, in the one cell the resume ritual reads. The `sandbox ↔ custom drift` row above is the authority (promoted 2026-08-24, user-approved) and NO UNCOMMITTED WORK IS PARKED.** ‼ *(2026-08-23: this cell's HEADLINE said "NO PROMOTION DECISION IS OWED: drift is 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven)" while its own tail, ~1,100 chars later, already said 1 differing — the tail was patched and the headline was not. A Tier 1 reviewer caught it, and the cell's own parenthetical records the SAME failure happening before. ⛔ THE HEADLINE CARRIES THE CAVEAT.)* Historical, 2026-08-17: no promotion decision was owed then, drift was 0 — all five were promoted (`pc_trip.py`, `higher_level_actions.py`, `early_game.py`, `counter_hunt.py`, `map_path.py` — the `#24-orphans` (1) verdict change and the `#24-abortswallow` guards) and promoting is the USER's call.** *(This cell opened with "NO PROMOTION DECISION IS OWED" while saying "2 differing … awaiting promotion" fourteen clauses later — a Tier 2 audit caught the contradiction.)* Formerly: — the LATEST promotion is the KI-66 `_on_field` fix (2026-08-17, user-approved, three-point A/B + a single-battle regression control); the KI-65 fix went 2026-08-16. *(Superseded, kept for its evidence: before those, the LATEST promotion was the **KI-81 whiteout guard** (2026-08-16, user-approved, proven by a MEASURED before/after: the probe fell 53→45 on custom); the KI-80 decoupling was promoted earlier the same day. `promote.py --check` expects `1 differing, 0 orphaned`. ✅ **And KI-80's "needs a driven repro first" precondition is now MET** — `--driver ki80ladder` is built, driven in both forks and committed, so the decoupling is UNBLOCKED. ⚠ *That is a statement about SHIPPED WORK, not a claim that the user owes nothing anywhere:* the **boss/status battle-policy change remains the USER's call and must not be built unilaterally** (see the §Ch18/§Ch19 decisions block below), and **KI-80's decoupling** — whose driven-repro precondition is now SATISFIED (see above) — is a production BEHAVIOUR change and lands in sandbox only. Neither blocks a next session from starting. *(A Tier 2 cold-start read the old absolute phrasing as contradicting that policy line — correctly.)* Everything is committed and pushed **as of the commit carrying this line** — ‼ trust `git status`, not this sentence, which is itself an uncommitted edit whenever you are reading it mid-session; BOTH 2026-08-15 promotions (`counter_hunt.py`, `pc_trip.py`) are DONE and user-approved, and so are BOTH 2026-08-16 `story_mode.py` promotions (the comment-only correction and the KI-80 decoupling), so `promote.py --check` reported no differences then; ⚠ as of 2026-08-23 it reports **7 differing** (`early_game.py`, sandbox-only, promotion decision OWED) (everything is promoted as of the FIVE-FILE PROMOTION (2026-08-17, user-approved)) — ANY file it lists is unexplained drift and is worth stopping for. *(§Ch20's chapter assembly is deliberately PARKED as a work item, which is a different thing again.)* Start at "NEXT ACTIONS". |
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

Moved for the R3 budget; the arc is item 4 in NEXT ACTIONS and is not started. ‼ **Keep these four, every one of which fails SILENTLY if got wrong:** (1) **Emerald REVERSED the party order — WAILORD first (slot 0), RELICANTH last** (`braille_puzzles.c:92-104`); the R/S order everyone remembers is wrong and the wrong order gives no message and no error. (2) ⛔ **The Regi battle is UNRECOVERABLE** — level 40, catch rate 3, and the fall-through case **including `B_OUTCOME_LOST`** sets `FLAG_DEFEATED_*`, so **a KO *or* a whiteout deletes the encounter permanently**; the only safe non-catch exit is fleeing. (3) **REGICE IS NOT A TIMED WAIT** — Emerald wants a **36-tile perimeter lap in ONE visit** ending exactly on `(8,21)`, reset by any map transition and by one wrong tile. (4) Measured capability gaps: **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or Flash — and **Relicanth is underwater-only, so Dive is upstream of the whole arc.** Ground truth: `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md`.

## ⏭ NEXT ACTIONS, IN ORDER

> **The ordered work queue** (the cold-start orientation is the ‼ YOU ARE HERE block at the top of
> this file, not here). Everything is committed and pushed **as of the commit carrying this line** —
> trust `git status` over this sentence. **No work is parked MID-TASK** (nothing half-edited, no
> `/checkpoint` debt). ⚠ That is NOT the same as "nothing is parked": **§Ch20 chapter assembly IS
> parked** — deliberately, by the user on 2026-08-14, finished and waiting, not abandoned (item 0).
>
> 0. ‼ **THE LIVE QUEUE (updated 2026-08-14) — DO THESE FIRST; items 2-4 below are older framing (item 1 is the ritual and is NOT older framing; item 5 was archived 2026-08-17).**
>    ‼ NEW STANDING RULE FOR EVERY ITEM BELOW: doc edits run Tier 0 (`lint_docs` +
>    `audit_doc_consistency`, both exit 0) before their commit, and a completed item gets a
>    Tier 1 independent review of its doc diff — see `CLAUDE.md`'s DOC CONSISTENCY LAYER.
>    ✅ **✅ (a) (b) (a2) (a3) (a4) ARE ALL DONE, AND (c) IS OBSOLETE — eve…** 📦 ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3
>    budget; CLOSED, nothing deleted).
>    ⛔⛔ **THE USER REDIRECTED PRIORITIES ON 2026-08-14, AFTER Room 9 landed. §Ch20 CHAPTER
>    ASSEMBLY IS NO LONGER QUEUE ITEM 0 — IT IS PARKED, READY, AND WAITING.** The live queue is
>    the **PC / PARTY ROBUSTNESS ARC** below. This was triggered by a live user test: a Winona
>    counter-hunt caught Slugma, healed, **derailed to Manual**, and on continue re-fought Winona
>    without the counter. The user's words: *"I want to ensure that the bot can robustly,
>    intelligently and strategically use the pokemon pc"*, and *"we should shift focus onto this
>    first so future issues can be handled better."*
>
>    **THE LIVE QUEUE, IN ORDER:**
>    ✅ **(P1) the Slugma derail and (P2) KI-78 Stage 1 are BOTH DONE, A/B-PROVEN, GATED (#19,
>    #20) AND PROMOTED. ⛔ DO NOT REBUILD EITHER.** Detail ARCHIVED VERBATIM to
>    `28-HANDOFF-ARCHIVE.md` (2026-08-18, R3 budget). ‼ **The one caveat that must not be
>    lost: KI-78 is NOT fully closed** — debug-fabricated identical pairs, corrupt box slots,
>    Frontier rentals and the evolved-since-capture path all stay OPEN. See its entry.
>    ✅ **(P3) party-accounting STAGE 0 is BUILT, GATED (#22) and DRIVEN, and (P3b) IS ANSWERED —
>    a DIVERGENCE WAS OBSERVED (2026-08-15). ⛔ DO NOT RE-RUN EITHER.** Detail ARCHIVED VERBATIM
>    to `28-HANDOFF-ARCHIVE.md` (2026-08-18, R3 budget). ‼ **Two rules survive and still bite:**
>    STALE is SAMPLED 1-in-300, so ⛔ read the SCAN COUNT, never the bare zero; and
>    ⛔ index/menu-cursor call sites STAY on quantity B — if A > B an index from A is out of
>    range. Stage 1 (re-pointing the ~35 capacity-shaped call sites) is UNBLOCKED.
>    🔜 **(P4) The END-TO-END repro of the user's actual scenario — STILL OWED.** Nincada evolves
>    into a full party → counter hunt → heal. **The honest gap: P1 is proven by a fabricated
>    fixture, not by reality.** ✅ **Its OBSERVABILITY half shipped 2026-08-14** (gate #23): the
>    heal's three PC piggybacks swallowed everything, so *worked* / *nothing to do* / *threw* were
>    one silence — the user's run took the middle branch, said nothing. They report now.
>    ⛔ **That is NOT P4.** ‼ **DESIGNED IN FULL — read
>    `ai-research-notes/2026-08-15-p4-boxcounter-repro-design.md` BEFORE BUILDING**; it refuted
>    four of my own premises. ✅ **Steps 1-3 DONE:** `debug_write_box_slot()` (‼ **PROVEN LIVE**,
>    `--driver boxwrite` → PASS; the P4 driver must still open with its own read-back control),
>    the `POKEBOT_BOXCOUNTER_TYPEONLY_A` fault hook, and the gate exercising the REAL hook.
>    ✅✅ **(P4) STAGES 1 AND 2 ARE DRIVEN AND CLOSED — `--driver boxcounter` (both arms) and
>    `--driver boxcounter2` (matrix {ARM A, ARM B} × {sandbox, custom} = 4/4 `ACCEPTANCE: PASS`).
>    ⛔ DO NOT REBUILD EITHER. 📦 **The full evidence — the four controls, the `hunted_pids=None`
>    control that made the mechanism decisive, and ARM A reproducing the user's derail from
>    PRODUCTION rather than simulation — is ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md`
>    (moved 2026-08-24 on the R3 900-line budget; nothing deleted).**
>    ‼ The PID is published ONLY from `box_counter_pid`'s return; `boxwithdraw` HAND-SETS it,
>    which is exactly why that driver never caught this bug.
>    ⛔⛔ **ANCHOR IS `saves/fortree_gym_wedge.ss1` — the "use `ch13_fortree_door.ss1`" correction
>    is REVERSED BY A DRIVE.** `ch13_fortree_door` is on ROUTE120 and the run died on its first
>    leg: `Cannot reach FORTREE_CITY: it is not walkable from ROUTE120`. That is **KI-24**,
>    documented in our own `region_reach.py:7-11` — Routes 118/119/120 are dual-elevation-bridge
>    maps `calculate_path` reads as WALLS. Every Winona-era anchor we own is on ROUTE119/120
>    EXCEPT the wedge. The feared gym-exit leg cost nothing.
>    ⚠ **What the swap gives up:** the wedge has NO Shedinja/Ninjask twins, so Stage 2 no longer
>    runs over a live KI-78 collision; `ch13_fortree_door.ss1` (which DOES hold a real pair
>    sharing `pid=42207D6F`) stays the anchor for any test whose SUBJECT is that collision.
>    ⛔ **`needed` IS `{Rock, Ice, Dragon}` — NOT `{...Electric}`.** Corrected by the driver's new
>    `needed_ok` control on its FIRST run: production derives `needed` from the ACE alone, the ace
>    is Altaria (Dragon/Flying), and Electric is 0.5× into Dragon × 2.0× into Flying = **1.0,
>    NEUTRAL**. Four copies (`counter_hunt.py:250`, the design note, THIS file, the driver) were
>    corrected — ⛔ **and a FIFTH was found 2026-08-15**, prose on `CREDIBLE_ANSWER_POWER`
>    (`story_mode.py:1087`) that named no type list, so the grep for the type set walked past it.
>    ‼ **STILL NOT PROVEN BY STAGE 2 — the honest gap:** everything UPSTREAM of registration. The
>    Slugma is INJECTED and the PID is published by the driver, so the real `hunt()` →
>    `story_mode.py:1750` wiring remains untested end-to-end. ⚠ And `hunt()` snapshots its OWN
>    `before_box_pids` AFTER travel, so an injected fixture is excluded a second time — that leg
>    needs a REAL CATCH, not an injection.
>    ✅✅ **(P4b) IS CLOSED — BOTH of its things are DONE (2026-08-15, user-approved).**
>    ✅✅ **KI-80's REPRO DRIVER IS BUILT, DRIVEN AND FAULT-TESTED (2026-08-15). ⛔ DO NOT REBUILD.**
>    `story_harness.py --driver ki80ladder`, anchor `saves/batch2_run04_wedge.ss1`. **THREE arms on
>    one fixture — same party, same 8 seeded losses, same boss; only the cfg's `grass` key differs:**
>    `NOGRASS` → ladder · `GRASS_FODDER` (Route 102, `wild_max` 4) → ladder ·
>    ⛔ `GRASS_STRONG` (Route 119, `wild_max` 27 — **the patch her own cfg comment names**,
>    `story_mode.py:3532`; ⛔ she has NO `grass` key today, and that is the only reason her ladder works) → **plain escalation,
>    ladder SKIPPED**. `ACCEPTANCE: PASS` on `--build sandbox` AND `--build custom`.
>    ‼ **The driver EXITS 0 even on FAIL — grade the `ACCEPTANCE:` line, never the exit code.**
>    Fault-tested twice: against `ch13_fortree_door.ss1` it FAILS with *"THE A/B WOULD BE VACUOUS"*
>    and all three arms return `LADDER` — a live demonstration that the fixture this file once
>    prescribed would have read as a REFUTATION of a true finding; and `POKEBOT_KI80_DECOUPLED=1`
>    FAILS today, which is what makes it usable as the AFTER run.
>
>    ✅ **✅✅ DONE 2026-08-16 — THE COUNTER-LADDER IS DECOUPLED FROM …** 📦 `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3).
>    ✅✅ **AND IT IS PROMOTED TO BOTH FORKS (2026-08-16, user-approved)** by a THREE-POINT A/B
>    against `--build custom`: `POKEBOT_KI80_DECOUPLED=1` **FAIL → PASS**, the coupled expectation
>    **PASS → FAIL**, and **arm 4 PASS on BOTH sides** — that invariance is what shows the mirror
>    regression did not travel with the fix. ⛔ **THE KI-80 ARC IS CLOSED; DO NOT REOPEN.**
>
>    ✅ **✅✅ PREVIOUS QUEUE ITEM 0 IS ANSWERED (2026-08-17): `#24-fa…** 📦 `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3).
>    ⚠ Limits recorded in the item: refusal count APPROXIMATE, n=1 diverging faint.
>
>    ✅✅ **`#24-driftassertions` IS DONE (2026-08-17) — the drift sweep IS A GATE** (`check_drift`;
>    reduction half `#24-driftreduction` open). ‼ Earned its keep again 2026-08-24: `sootopolis.py`
>    moved the count and it found SEVEN stale claims — a Tier 1 review then found an EIGHTH, in this
>    file's STATE-table HEADLINE, a shape `check_drift` missed (`#24-driftheadlineshape` —
>    ✅ CLOSED 2026-08-26: PASS 3 reads the row's FIRST `N as of <date>`, D28a-e + a live
>    incident replay prove it both ways).
>    📦 Detail ARCHIVED in `28-HANDOFF-ARCHIVE.md` (2026-08-24, R3 budget).
>    ✅✅ **`(P4c) #24-orphans` (1) IS HALF DONE (2026-08-17): its INSTRUMENTATION half is BUILT,
>    GATED (#26) and A/B-PROVEN (`withdraw_from_box` returns `(landed, code, detail)`; ARM B
>    `landed=True` vs ARM A `landed=False`). ⛔ DO NOT REBUILD IT. Its REACTION half stays OPEN
>    and still needs the USER plus an unmeasured heap offset. 📦 Detail ARCHIVED VERBATIM in
>    `28-HANDOFF-ARCHIVE.md` (2026-08-24, R3 headroom).
>    ✅✅ **`#24-abortswallow` (2026-08-17): 8 MORE SITES FIXED** — part of the arc that ended in
>    gate #27 (ratchet, baseline 36). ⛔ DO NOT REDO IT. 📦 Detail ARCHIVED VERBATIM in
>    `28-HANDOFF-ARCHIVE.md` (2026-08-26, R3 budget).
>    ✅✅ **`#24-abortswallow` ROUND 3 IS DONE (2026-08-17)** — refinement (1) shipped (37→36),
>    refinement (2) REFUTED (it would blind the gate to five already-fixed sites, one an OBSERVED
>    failure). ⛔ DO NOT REBUILD IT. 📦 Detail ARCHIVED VERBATIM in `28-HANDOFF-ARCHIVE.md`.
>    ✅✅ **AND THE PROBE IS NOW GATE #27 — A RATCHET, baseline 36, fault-tested both ways** (inject one
>    unguarded site → 37 → exit 1). That closed this item's gating question without a zero-threshold.
>
>    ➡➡➡ **QUEUE ITEM 0 — ✅✅✅ ALL FIVE PASSES ARE DONE AND COMMITTED (2026-08-22).
>    ⛔ DO NOT RE-RUN ANY OF THEM. ✅✅ `#24-loopheadabort` IS ALSO DONE (2026-08-23) — **all 17**
>    nav retry loops patched, gate #30. ⛔ An earlier draft excluded 3 on a FALSE premise ("the
>    latch is still set"); an adversarial review refuted it and the exclusion is WITHDRAWN. #30 §1
>    now gates the real invariant: the latch is cleared BEFORE every recovery routine.
>    ✅✅ `#24-p4residuals` is **6 of 7 DONE** (2026-08-23); only **(f)** remains, deferred because
>    ARM C is a real emulator drive. ⛔ Two of its sub-items REFUTED the fix the item itself
>    proposed — see `06-DECISIONS-LOG.md`.
>    ✅✅ `#24-abortrecoveryresiduals` **(b) is DONE** (2026-08-23) — my own abort-swallowing debt
>    cleared, 11 → 7, control-armed. **(a)** still needs a driven double-whiteout; **(c)** (7
>    PRE-EXISTING swallowers, newly filed) wants its own control arm.
>    ➡➡➡ **NEXT ACTION, 2026-08-26 (USER REDIRECT): THE THREE `#26-*` PRODUCTION DEFECTS.**
>    Work order: (1) launch `x4_headless.py --lanes 8` and let it accumulate derail/HM-teach
>    evidence in the background; (2) meanwhile review the POST-NORMAN HM03 TEACH code and the
>    SURF-LEARNER acquisition gap (`#26-surfteachchain` — anchors `norman_done.ss1` /
>    `prenorman_fodder_grind.ss1`); (3) profile the Mossdeep puzzle from `in_mossdeep_gym.ss1`
>    BEFORE changing it (`#26-mossdeeppuzzlespeed`); (4) ✅ DONE — the batch LANDED and was MINED
>    (final numbers in `#26-manualderails`: 50 runs, 6 finished, Treecko 0/9), and ➡ **THE FORTREE
>    HALF IS FIXED: the Winona SECOND WIND shipped 2026-08-26** — two-era arm (`--driver
>    secondwind`) built FIRST on unmodified code, then the fix; the honest-stop ruling complied
>    with (the re-arm control RAISES in both eras). ⚠ Decision-layer proof; the end-to-end pass =
>    the next post-fix batch (discriminator: no five-fold hopeless-gate repeats before Manual).
>    ‼ ki80ladder's TEN-DAY Expect-rot found and fixed the same hour (its era flag has zero
>    production hits since the 2026-08-16 promotion).
>    ✅ `#26-fleefreeze` SHIPPED 2026-08-26 (the one-line delegate; gate #32 proves it 3 ways,
>    old behaviour refuted by construction; live-trap arm rides the batch below). ⛔ DO NOT REDO.
>    ✅✅ **BATCH `20260826-130441` IS MINED — ⛔ DO NOT RE-MINE.** D1 25.8% vs 12.0% PASS; D2
>    PASS (7/10 teach-failure runs finished); D3 PASS decisive (zero CantEscape); D4
>    FAIL-as-registered/works-as-designed (numbers + the OPEN USER QUESTION: `#26-manualderails`).
>    ✅✅ **BATCH `20260826-185918` IS ALSO MINED (2026-08-27, just after midnight) — ⛔ DO NOT
>    RE-MINE. Finish rate 12/32 = 37.5%** (12.0 → 25.8 → 37.5 in one day); **wedge fix VALIDATED**
>    (its KI-47 family 2 → 0 over 572 item flows); **FIRST TREECKO FINISH EVER**; and the Treecko
>    wall is now a NAMED clean run-ender (*"No party mon can learn Surf and the party is full —
>    needs PC box management (#24-pc)"*) — full numbers in `#26-manualderails`'s batch section.
>    ➡➡➡ **NEXT: THREE USER DECISIONS ARE NOW RIPE, then build.** (1) ⛔ **the drift-7 promotion**
>    — the `#26-*` fixes are now validated by TWO independent batches (this is the USER's call, and
>    the evidence is as strong as it gets without promoting); (2) the POST-WIND repeat burn
>    (`#26-manualderails` D4 open question); (3) recon-driver mixin adoption
>    (`#24-harnesswhiteoutdrop`). **BUILD CANDIDATES, in measured-cost order:** (a) the
>    `#24-roster` WITHDRAW half — the named Treecko run-ender IS its spec; (b) the
>    `handle_fainted_pokemon`/FaintedMonTry KI-47 family (2 nets, both batches — KI-66 residual
>    area); (c) `#26-surfteachchain` D3-D6 (D3 recon note ready); (d) `#26-gatestartupcontention`
>    fix candidates (diagnosis complete); (e) the harness run-header `driver:` line (2 lines).
>    *(D3's recon note: `ai-research-notes/2026-08-26-d3-forgetmenu-cursor-decomp.md`; the
>    contention diagnosis + suite-31/32 story: `#26-gatestartupcontention` + changelog.)*
>    §Ch21 leg 2 stays PARKED with its spec at `ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md`.
>    ⛔ Batches answer FREQUENCY, drivers answer CORRECTNESS — fixes get proven by targeted
>    drivers, never by another batch.
>    *(parked, was:)* BUILD §Ch21 LEG 2 — HEAL, THEN FIND STEVEN — spec at
>    `ai-research-notes/2026-08-26-ch21-leg2-BUILD-SPEC.md`.
>    ✅ LEG 1 IS DONE AND DRIVEN (`--driver ch21dive`, `ACCEPTANCE: PASS`). ⛔ DO NOT REBUILD IT.
>    Start from **`saves/post_sootopolis_arrival.ss1`** (PINNED): `SOOTOPOLIS_CITY (29,53)`,
>    `SOOTOPOLIS_CITY_STATE=2`, SURFING, controllable. ⚠ **1 party member is FAINTED at 54% HP**,
>    so leg 2 opens with a HEAL — the Poke Center at `(43,31)` is 38 waypoints away and that path
>    is exactly what leg 1's acceptance proves.
>    ⛔ **LEG 2 IS *FIND STEVEN*, NOT *WALK TO THE CAVE OF ORIGIN*.** The decomp settles it:
>    `SootopolisCity_EventScript_StevenLeadPlayerCaveOfOrigin` ends `warp
>    MAP_CAVE_OF_ORIGIN_ENTRANCE, 9, 20` — the game WARPS you in; nobody walks to that door.
>    ✅✅ **STEVEN IS AT `(20,36)` AND IS REACHABLE — 27 waypoints, MEASURED** by
>    `probe_ch21_npcs.py` (fault-tested). He is `OBJ_EVENT_GFX_STEVEN` (134) in the ROM's
>    object-event templates; approach him from `(20,37)`.
>    ⛔ **AN EARLIER VERSION OF THIS LINE SAID `(20,36)` IS "UNVERIFIED AND ITSELF UNREACHABLE".
>    BOTH HALVES WERE WRONG, AND IT WOULD HAVE SENT YOU DOWN A DEAD END.** Cause: I ran
>    `calculate_path` to each NPC's OWN tile, which ALWAYS fails because the tile is occupied, and
>    read the universal "refuses" as geography. ⇒ **A BOT STANDS BESIDE AN NPC, NEVER ON ONE — ask
>    reachability of the NEIGHBOURS.** Re-measured adjacently: **15 of 18 Sootopolis NPCs are
>    approachable**, Maxie `(29,33)` and Archie `(31,33)` among them (leg 5 needs BOTH).
>    ⛔ The "ZERO NPCs loaded" half was invalid too: `get_map_objects()` is CAMERA-RANGE-limited and
>    returns only the player from `(29,53)`. The ROM TEMPLATES are range-free and show **EXPERT_M(21)
>    AND WALLACE(133) BOTH STATIONED ON `(31,18)`** — the body-block our ATLAS names is REAL.
>    ⚠ Still true and still measured: the whole column `(31,16)..(31,22)` refuses, so the block is
>    not the only reason — the ledge is unreachable from the water as well.
>    *(superseded)* BUILD §Ch21 LEG 1 — ROUTE128 → SOOTOPOLIS (the dive-in).
>    ✅ The fixture now EXISTS: **`saves/post_ch20.ss1`** (`#24-ch21anchor` DONE — ⛔ do not
>    re-capture it). Probe-verified `OVERWORLD ROUTE128 (38,24)`, `ROUTE128_STATE=2`,
>    `SOOTOPOLIS_CITY_STATE=1` — i.e. **Ch21's entry condition, measured live.**
>    ⚠ It has **1 FAINTED party member at 80% HP** — heal first, or treat the heal as leg 0; do NOT
>    read an early whiteout as a Ch21 bug.
>    ⛔ **READ THE §Ch21 ATLAS in `12-STORYMODE-DESIGN.md` FIRST.** Leg 1 is: surf 128→127→126
>    (one region, ONE `navigate_to`), pick a dive tile near `(45,66)` and **assert its tile_type
>    before `dive()`** (KI-72 — never let the planner choose where you surface), `navigate_to`
>    `UNDERWATER_ROUTE126 (45,65)`, land `UNDERWATER_SOOTOPOLIS_CITY (9,8)`, **step OFF (9,8)/(10,8)
>    (both warp straight back)**, then `surface_from_dive()`. ✅ That map has ZERO
>    `Underwater Blocked Above`/`Seaweed No Surfacing` tiles — the KI-72 trap does not apply there.
>    ➡ *(previous)* the promotion is DONE 2026-08-24 — the USER's call (drift 0 — promoted 2026-08-24). ⛔ **When it lands, lower `probe_abort_swallowing.py`'s custom baseline 36 → 31 in the
>    SAME commit**, or the ratchet re-permits 5 sites of debt in the fork that ships.
>    ✅✅ `#24-brokenrepros` **is DONE** (2026-08-23) — six repros fixed, not the five filed; ⛔ do
>    NOT re-do it. **NEW from it: `#24-reprosweepratchet`** (the repros are not in the standing suite,
>    so they rot; the same script was written off as "environmental" TWICE).
>    ✅✅ `#24-p2headergate` **is DONE** (2026-08-23) — 2 checks added inside existing gates, 1
>    deliberately deleted (7 blockers, guarding a doc nicety). ⛔ do NOT re-do it, and ⛔ **do not
>    resurrect the deleted check** — the long note at its former site in `audit_doc_consistency.py`
>    explains why, and it cost six review rounds to learn.
>    ⚠ **`03-PUNCH-LIST.md` IS AT ITS 3600 CAP (measured at commit time — run `wc -l`, never trust
>    this line). ‼ THE NEXT EDIT THAT GROWS IT MUST FIRST RETIRE A COMPLETED ITEM (candidates:
>    older ✅ `#24-*` blocks; the mined `#26` entries are retirable — the batch section keeps
>    their numbers).** ‼ *(This figure is re-derived at commit time — an earlier one drifted by 4 lines because
>    it was measured BEFORE the last edits. Measure a line count LAST.)* It hit 3597 (3 left) on
>    2026-08-23 and was brought back by RETIRING the just-completed `#24-brokenrepros` entry from
>    ~56 lines to a 16-line summary. ⛔ **When it tightens again, retire another COMPLETED item the
>    same way: SUMMARISE + POINT at `07-CHANGELOG.md`, never delete** — code and docs cite these
>    slugs and `audit_doc_citations.py` will go red. `03` is a CURRENT-STATE file, so summarising
>    finished work is maintenance, not loss: the narrative lives in the append-only history.
>    ✅✅ **`#24-difftriggeredrules` IS DONE 2026-08-26 — ⛔ DO NOT REBUILD IT.** `advise_on_diff.py`
>    (9 diff-keyed rule families, ADVISORY — exit 0 with or without findings) + a fail-open
>    PreToolUse hook (`advise-on-commit.ps1`) that injects the advisory at `git commit` time
>    WITHOUT touching the permission flow (⛔ deliberately NO `permissionDecision` — an "allow"
>    would auto-approve past the user's prompt; see `06-DECISIONS-LOG.md`). 32-check self-test,
>    mutation-proven (evidence/2026-08-26-advise-on-diff-mutation-test.txt); an adversarial
>    review KICKED BACK the first version (two-line-gate false positive; renames/binary diffs
>    invisible to path rules) and both are fixed and self-tested.
>    ➡ Other candidates: `#24-reprosweepratchet`, or
>    ✅✅✅ **§Ch20 SHIPPED AS A CHAPTER 2026-08-24 — 5/5 drives PASS, both recovery paths exercised.
>    ⛔ DO NOT REBUILD IT.** The module, the Segment 19b/20 wiring and `--driver ch20chapter` all
>    exist and are driven. ⚠ What is NOT proven: organic Dive acquisition in the same run (the driver
>    injects it), and a LOST Archie fight (stochastic, measured 2W/1L; all five runs won).
>    ➡ *(SUPERSEDED 2026-08-24 — the live instruction is the ➡➡➡ line above; §Ch21 RECON IS DONE and the ATLAS in `12-STORYMODE-DESIGN.md` now governs.)* **§Ch21 — SOOTOPOLIS / RAYQUAZA.** It is enterable immediately: Room 9 sets
>    `VAR_SOOTOPOLIS_CITY_STATE = 1` in the SAME block that sets `ROUTE128_STATE`, and Sootopolis's
>    own ON_FRAME fires on it. ⛔ Read `#24-divegroundroute120`, `#24-hmgroundwatertiles` and
>    `#24-gatescopeharness` first — all three were measured today and none is started.
>    ⛔ **`#24-abortrecoveryresiduals` IS DONE — DO NOT RE-OPEN ANY OF (a)/(b)/(c).** (a) was closed
>    by ASSESSMENT (reachability VERY LOW, evidence in `07-CHANGELOG.md`); deliberately no code change
>    to the whiteout-recovery path.
>    ➡ **BEST NEXT ITEMS, in order:**
>    1. ✅ **`#24-difftriggeredrules` — DONE 2026-08-26** (see the ✅✅ block above; ⛔ do not
>       rebuild). The next-best list below moves up one.
>    2. **`#24-harnesswhiteoutdrop`** — 36 harness runs silently stopped behaving like the real mode
>       after a whiteout. Any result measured after that point is suspect, so this taints EVIDENCE.
>    3. **`#24-reprosweepratchet`** — what the standing suite does not run, rots.
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
>    `#24-plainenglishstale` (the human-facing status file is two days behind).
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
>    **(PARKED, NOT CANCELLED) ASSEMBLE §Ch20 AS A CHAPTER** — a module in `modules/story/`,
>    wired as Segment 20 in `story_mode.py`, built from the driven ingredients (`_ingress`, the
>    room solves, the walk route, the var-gated scene ride, the atoll escape). Requirements,
>    all measured: **organic Dive acquisition** (drivers inject it; KI-63's
>    `ensure_hm_learner_making_room` is wired in sandbox), **whiteout-retry policy for Archie**
>    (one retry = full re-dive of Rooms 1-8, ~25 min; Mossdeep Gym's N-attempts precedent),
>    **pre-boss readiness** (potions/party order — run 3 entered with a fainted mon and
>    Sceptile at 96/135), **Blocker 3** (Repel policy — Rooms 6/7 have `water_mons`; Rock Smash
>    prompts YES/NO every smash), **Blocker 4** (pre-flight badge/move assertion incl.
>    Dive/BADGE07), and grade the SEGMENT on **`VAR_ROUTE128_STATE == 2` + the escape +
>    can-continue** (the ladder chapter in `chapters.py:233` grades on
>    `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`, which is set PRE-warp — too weak for the segment).
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
>    2026-08-15; it has said 17, 18, 19, 20, 21, 22, 23 and 28 on its way to **32** — `run_gates.py` is authoritative, never this prose), and the drift check below.
>    ⚠ **EXPECT 7 differing (`seafloor_cavern.py`, the §Ch20 chapter under construction — NOT a promotion decision), 0 orphaned as of 2026-08-24 — the abort guards were PROMOTED (user-approved). Formerly 0 differing after the FIVE-FILE PROMOTION (2026-08-17, user-approved)**, the KI-66 `_on_field` fix included, the KI-81 whiteout guard
>    included (2026-08-16, user-approved). **ANY file listed is unexplained drift.**
>    *(This line read "EXPECT 0 — everything was PROMOTED 2026-08-15" until 2026-08-15, when Stage 2
>    corrected a wrong type-set comment in that file. A Tier 1 audit caught that the drift figure had
>    been updated in the STATE row and the banner but NOT here, fifteen lines away — so a cold agent
>    running `promote.py --check`, getting one file back, would have read an EXPECTED result as an
>    alarm. ALL drift statements in this file move together or not at all — ⛔ do NOT trust a COUNT here (this line said 'three' while another said 'five'; the true figure reached THIRTEEN across five files). GREP, case-insensitively, and require zero.)*
>    ⛔ Do not restate the figure here; it has been wrong at 2, 3 and 3 again. `promote.py --check`
>    is the authority. (Earlier EXPECT-2 / EXPECT-3 trails moved to `28-HANDOFF-ARCHIVE.md`.)
>
> 1b. ✅ **DONE — the KI-63 wiring was PROMOTED on 2026-08-14 and is in BOTH forks. There is no
>    decision left here** (‼ not a claim about today's drift figure — see item 1). Its superseded
>    "first decision for the user" text, and the measured worth behind it (20 terminal run-kills in
>    1,129 runs, #1 of 14 derail causes by frames), moved to `28-HANDOFF-ARCHIVE.md` 2026-08-14.
>
> 2. ✅ **DONE 2026-08-13 — `reorder_party()` IS DRIVEN.** `--driver roster` passes: six swaps, all
>    verified by PID, including the never-driven `RotatePokemon(i, j != 0)`. Both unknowns this
>    item asked about are SETTLED; the trace detail moved to `28-HANDOFF-ARCHIVE.md` 2026-08-14 on
>    the line budget. ⚠ **Keep one thing from it:** `gPartyMenu.slot_id` is NOT reset between menu
>    sessions and `navigate_to_mon:520-524` reads it — it happened to be re-read live in time, so
>    that is LUCK, not safety. Re-check it first if a roster drive ever mis-swaps.
>    ‼ **What is NOT done:** the **deposit/withdraw** half of `#24-roster`. Ordering answers "in
>    what order", not "which Pokémon". And **promotion of `roster.py` + `menuing.py` to
>    `custom-pokebot/` — ✅ **DONE, promoted 2026-08-13/14; both files are in BOTH forks.**
>    ‼ That is a statement about THESE TWO FILES, not about the repo's drift figure today —
>    PARTY ACCOUNTING STAGE 0 has since moved it. See the STATE line at the top of this file.**
>
> 2c. **‼ READ `ai-research-notes/2026-08-13-puzzle-solver-already-ships-ch21-and-the-regi-arc.md`
>    BEFORE ITEMS 3 AND 4 BELOW.** Both were written believing §Ch21 and the Regi arc had to be
>    built as chapters. **Most of that content already exists in upstream code we already have.**
>    Items 3 and 4 are still correct about the DIVE LEG — which is the real gap — but wrong about
>    the scale of what remains. **KI-72** also lands here: never let the planner choose a surfacing
>    tile.
>
> 3. ✅ **DONE — DO NOT RE-DO.** KI-68's dive leg is driven (`--driver ch20dive` →
>    `ACCEPTANCE: PASS legs=6/6`) and all nine cavern rooms with it. ‼ **Keep the RULE, not the
>    task:** `WaypointAction.Dive`/`Emerge` are assigned NOWHERE and `warp_graph.py:342` excludes
>    dives from `calculate_path` **on purpose** — so *"not routable" never meant "not possible"*;
>    the answer is a CHAPTER that drives the transition, never a planner rewrite.
>    ‼ **LIVE, not stale:** if a hunting ground is ever added, **NOT to `TRAINING_GRASS`** —
>    measured, a Shoal Cave row becomes the highest band and flips `best_training_area` for every
>    team ~L30 up. ⇒ see **KI-80**, the same table's second sharp edge.
>
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
⛔ `probe_skypillar_clean_layout.py` is NOT in `run_gates.py`: it fetches the decomp's layout binaries
over the network (cached under `.layout-cache/`, gitignored), and a standing gate must not need the net.
‼ It exists because a Tier 1 review REFUSED the §Ch21 atlas's central finding while it rested only on an
uncommitted scratch script — the numbers were right and un-re-runnable, which this project treats as
not proven.

### Capture the §Ch21 start fixture (⛔ already done — `saves/post_ch20.ss1` exists; do NOT redo)
```
CH20_CAPTURE=post_ch20.ss1 PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1     --driver ch20chapter --frames 6000000        # ~25 min; writes ONLY on ACCEPTANCE: PASS
PYTHONUTF8=1 py -3.12 probe_anchor_inventory.py --filter post_ch20   # verify the FILE, not the log
```


‼ **RESTORED 2026-08-13.** This file referenced a "HOW TO RUN / TEST" section in four places while
the section itself lived only in `28-HANDOFF-ARCHIVE.md` — so a cold-start agent following the
handoff's own instruction found nothing. The archive copy is longer and still useful for the §Ch18/
§Ch19 drivers; this is the minimum a new session needs.

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 preflight.py        # ‼ RUN THIS FIRST. git + fixtures + docs + freeze
PYTHONUTF8=1 py -3.12 run_gates.py        # THE STANDING SUITE — all 32, exits non-zero on any
                                          #   failure (~130s). ‼ The list lives in CODE, not prose — `run_gates.py` is the only
#   authority on how many gates there are. Every prose count in this file has been
#   wrong at some point.
PYTHONUTF8=1 py -3.12 run_gates.py --quick   # the 24 needing no ROM (was 10, 14, 15, 16, 17, 18, 20, 21; MEASURE)
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
# ⛔ THE THREE Expect: BLOCKS BELOW WERE ATTACHED TO THE WRONG COMMANDS until 2026-08-13 — the
#   fault-injection note even carried ch20room2's PASS line as its "Expect". Each Expect now sits
#   DIRECTLY under its own command; a cold agent grades a run against the line beneath it.
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
#   ‼ `saw_double` is REPORTED, NOT GRADED — it measures a decomp claim, and grading on it
#     would turn "we learned the claim was wrong" into "the run failed".
#   ‼ `battles` counts trainer battles IN ROOM 3 only. Counting them run-wide once printed a
#     false REFUTED over data that CONFIRMED the claim (the Room 1 grunt is fought every run).
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
#   ‼ Read this BEFORE writing the exit leg. The landing tile has ZERO surfable neighbours, so a
#     naive "Surf from where you land" reads as a HUNG LEG, not as a failure.

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
PYTHONUTF8=1 py -3.12 lint_docs.py                  # line budgets, banners, flag registry
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
#   Expect as of 2026-08-24 (LATEST): 7 differing (`seafloor_cavern.py`, the §Ch20 chapter under construction — NOT a promotion decision) (the abort guards were PROMOTED; formerly 1, sandbox
#   only, PROMOTION DECISION OWED), 0 orphaned. ⛔ The tool is the authority, never this comment. — everything ELSE promoted incl. the KI-66 `_on_field` fix, the KI-65 fix, the KI-81
#   whiteout guard included. ANY file listed is unexplained drift.
#   ‼ THE FIGURE ABOVE HAS BEEN 0 -> 1 -> 0 -> 1 -> 0 IN TWO DAYS, once per promotion, so DO NOT
#     pattern-match it — RUN the command. ⛔ Earlier retractions here quoted the OLD figure
#     VERBATIM, which made the retraction byte-identical to the claim it followed and unreadable;
#     superseded figures are now DESCRIBED, never reprinted. (`audit_doc_consistency` also cannot
#     tell a quotation from a claim, so reprinting one turns this line red.)
#   ‼ DIGITS, NOT WORDS, AND CASE-INSENSITIVELY: a spelled-out "THREE" went stale here for a day,
#     and a capital "drift is 7 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until the chapter is driven)" survived a lowercase sweep on 2026-08-16.
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

‼ **VERIFY THE SANDBOX↔CUSTOM DRIFT ROW RATHER THAN TRUSTING IT** — `promote.py --check` is in the block above and measures it BOTH ways in seconds. ✅ **Expected as of 2026-08-24 (LATEST): 7 differing (formerly 1, `early_game.py`, sandbox-only), 0 orphaned — PROMOTION DONE 2026-08-24. Formerly 0 differing, EVERYTHING PROMOTED** (the five-file promotion, user-approved) — everything ELSE is promoted (⚠ the five sandbox-only files are NOT): the KI-66 `_on_field` fix (2026-08-17), the KI-65 fix (2026-08-16), and the KI-81 whiteout guard before them. ⛔ ANY file listed is unexplained. *(This line was the SURVIVOR an adversarial review caught on 2026-08-16 — a 13-site hand sweep missed it AND `audit_doc_consistency` passed over it, which is the false negative `#24-driftassertions` exists to remove.)* *(This line said "0 differing, 0 orphaned" until a Tier 2 cold-start audit found it, along with the sibling line in the command block above, still claiming 0 after three other places in this file had been corrected to 1. ALL drift statements in this file move together or not at all — ⛔ a COUNT here has been wrong twice ('three' vs 'five'; the real sweep found THIRTEEN across five files). GREP, case-insensitively, print the MATCH not the line, and require zero.)* Superseded: *"the PowerShell loop is in `28-HANDOFF-ARCHIVE.md`'s copy of this section"*, together with an older expected-count naming `modules/map_path.py`, `modules/story/early_game.py` and `plugins/custom_modes/story_mode.py` — all PROMOTED now and not part of the current drift set. ‼ **The old FIGURE is deliberately not reprinted**: `audit_doc_consistency` cannot tell a quotation from a claim, so quoting a stale count turns this line red (it did). ‼ `tools/story-dev/` is sandbox-only and is **not** part of that comparison, so the `ch20*` drivers, `probe_route128_landing.py` and `repro_party_accounting.py` do not change the count.

---

# 📚 EARLIER HANDOFF SNAPSHOTS → `28-HANDOFF-ARCHIVE.md`

Every superseded "you are here" section now lives in **`28-HANDOFF-ARCHIVE.md`** (append-only).
This file is CURRENT STATE only — if something here is no longer true, fix it here rather than
adding another banner below it.
