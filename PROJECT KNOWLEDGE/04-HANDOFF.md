# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-08-16 — start at the single orientation block immediately below.
Every banner further down is HISTORY, newest first.

---
# ‼ YOU ARE HERE (2026-08-16, SESSION END) — **THE LIVE WORK IS THE PC / PARTY ROBUSTNESS ARC, AND IT IS AT A CLEAN BOUNDARY **AS OF THE COMMIT CARRYING THIS LINE** (a cold-start audit correctly flagged the earlier absolute wording: a banner cannot truthfully say "everything is pushed" while it is itself the uncommitted edit — so read this as *"true at this commit"*, and trust `git status` over any prose). ✅ Drift is 0 — the KI-81 whiteout guard was PROMOTED 2026-08-16, user-approved. BOTH `story_mode.py` changes are promoted too (the comment-only correction and the **KI-80 DECOUPLING**, a BEHAVIOUR change proven by a THREE-POINT A/B against `--build custom`), user-approved 2026-08-16.** ✅ **(P4) IS DRIVEN THROUGH STAGE 2** — the real heal COLLECTS the boxed counter and leads with it (ARM B), and ARM A leaves it boxed, reproducing the user's derail ORGANICALLY; matrix {ARM A, ARM B} x {sandbox, custom} = **4/4 ACCEPTANCE: PASS**. ✅ **BOTH PROMOTIONS ARE DONE (user-approved): `counter_hunt.py` (comment-only) and `pc_trip.py` (KI-79, a BEHAVIOUR change proven by a three-point A/B).** ⛔ **(P6) WAS INVESTIGATED AND REFUTED — its "obvious" fix is a REGRESSION; see KI-80, now GATED (suite #24).** ✅✅ **KI-80'S REPRO DRIVER IS BUILT, DRIVEN AND FAULT-TESTED — `--driver ki80ladder`, 3 arms, `ACCEPTANCE: PASS` in BOTH forks, and KI-80 is REPRODUCED (Winona's real Route 119 patch DELETES her counter ladder). ⛔ DO NOT REBUILD IT.** ✅✅ **KI-80 IS DECOUPLED — BUILT, DRIVEN AND REVIEWED (sandbox only).** `POKEBOT_KI80_DECOUPLED=1` went **FAIL → PASS**, arm 4 (the mirror-regression guard) **still PASSES**, the old coupled expectation now **FAILS** (proving behaviour changed), and `repro_boss_grass_gate.py` **SELF-RETIRED**. ✅ **AND PROMOTED TO BOTH FORKS 2026-08-16 (user-approved), by a THREE-POINT A/B against `--build custom`: `POKEBOT_KI80_DECOUPLED=1` FAIL → PASS, the coupled expectation PASS → FAIL, arm 4 PASS on both sides.** ✅✅ **THE WHOLE KI-80 ARC IS COMPLETE AND PROMOTED — reproduced, fixed, guarded, reviewed, and in BOTH forks. ⛔ DO NOT REOPEN IT.** ✅ **The UNRELATED KI-81 whiteout guard was also promoted 2026-08-16 — drift is 0 and nothing awaits a ruling.** ➡ **NEXT ACTION: `(P4c) #24-orphans` — ✅ (4) IS DONE (the harness no longer eats an A/B's first arm); FIVE remain.** ⛔ **Its COST ranking and its STARTABILITY ranking differ, and the item lists only cost.** Costliest is **(1)** — no caller acts on `withdraw_from_box`'s verdict — ✅ **the USER'S RULING EXISTS** — *"reattempt but after intelligently processing the data (text boxes it reads to determine why it failed)"* (`06-DECISIONS-LOG.md`) — ⛔ **BUT IT IS NOT READY TO BUILD: a recon found a BLOCKER (the PC message buffer `sStorage->messageText` is HEAP-allocated and its offset is NOT known here — it must be MEASURED, and until it is every failure classifies UNKNOWN, which must not retry, so the feature would ship INERT) plus FOUR PREREQUISITES.** Read `06-DECISIONS-LOG.md`'s design entry FIRST. ⇒ **the genuinely startable work with zero input is (2) KI-65, (3) KI-66, or `#24-abortswallow` triage.** ⛔ When it IS built: NOT a blind retry — bound it, diagnose from READ text, and an UNKNOWN reason must stop loudly rather than retry. ⇒ **Startable with zero input: (2) KI-65 and (3) KI-66.** ✅ **(2) NOW HAS FULL RECON (2026-08-16) — read KI-65's `RECON` block first; it corrected the item on THREE counts** (there are TWO unbound reads not one; the captured saves are a FIXTURE not a repro, and "moveset unchanged" is today's GREEN result so an A/B on it is VACUOUS; and fixing the flagged line alone leaves the ping-pong intact). The fault-injection point is identified and needs no production edit, and the fix is specified in three parts — but ⛔ **it is a REPRO-FIRST item of real size, not a one-liner**, and its own entry defers the fix until the repro exists. **(3) KI-66** is four unguarded full-party scans, one feeding an UNBOUNDED `while … press A`. *(Also tracked: `#24-logcollision-siblings`, `#24-zerokocounter`, (P5).)* §Ch20's chapter assembly stays **PARKED, NOT CANCELLED**. Read this, then `14-AGENT-PLAYBOOK.md`, then NEXT ACTIONS item 0.

> ⛔ **ORDER, EXPLICITLY (a Tier 2 cold-start audit could not tell which of these came first):
> (1) RUN THE RITUAL BELOW — it is cheap and it tells you whether the tree is sane; (2) READ
> `14-AGENT-PLAYBOOK.md`; (3) GO TO `NEXT ACTIONS` item 0.** The banner sentence above lists the
> READING order only; the ritual outranks it, because reading is wasted if the tree is broken.
>
> ‼ **FIRST, ALWAYS:** `cd tools/story-dev` **from the repo root** (the folder holding `sandbox-pokebot/`, `custom-pokebot/` and `40cakes repo/`), then
> `PYTHONUTF8=1 py -3.12 preflight.py` and `PYTHONUTF8=1 py -3.12 run_gates.py`
> — **both must exit 0; the suite is 24 gates** (it prints its own count — believe that, not this
> line, which has been wrong at 17, 18, 19, 20 and 21 on the way here). That ritual survived the 2026-08-14
> priority redirect and is NOT part of the superseded "older framing".

> **State: `main`, clean, 24/24 gates PASS, nothing parked, nothing running.** All work pushed.
> ✅ **The tree is clean AND the sandbox→custom drift figure is 0** — everything is promoted.
> *(⚠ Keep those two ideas separate anyway: they are independent, and this line existed to say so
> loudly while they disagreed. ‼ `audit_doc_consistency` matches the literal string and cannot
> tell a NEGATION from a claim — it red-flagged this very line once for saying the figure was NOT
> zero, so phrase any future caveat here carefully.)*
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
> each assert which fork they imported). ‼ **`promote.py --check` is the authority — expect
> `0 differing, 0 orphaned`; ANY file it lists is a reason to stop.**
> ⛔⛔ **DIGITS, NOT WORDS — when you change a drift count, grep the WORD forms too.** *(Confirmed
> again 2026-08-15: the gate flagged 3 of 7 stale claims; the 4 it missed were spelled "zero",
> sat in a table cell, or read "0 as of". Full history of this line's four staleness incidents:
> `28-HANDOFF-ARCHIVE.md`.)*
> **Every room of the Seafloor Cavern is DRIVEN and PASSING** — `ch20dive` → rooms 1, 2, 6, 3, 8, 9
> (Kyogre awakened, `VAR_ROUTE128_STATE == 2`). **What remains of §Ch20 is CHAPTER ASSEMBLY.**

## ✅ ROOM 9 — ARCHIE, KYOGRE, THE ATOLL ESCAPE (driven 2026-08-14) — DETAIL in `28-HANDOFF-ARCHIVE.md`

‼ **Keep only what later work leans on:** `--driver ch20room9` PASSED 2 of 3 — the cavern is driven
END TO END, graded on **`VAR_ROUTE128_STATE == 2`** (never the Kyogre flag, set BEFORE the forced
warp); the atoll escape is **south to `(38,23)`, then Surf onto `(38,24)`** (the landing tile has
ZERO surfable neighbours, so a naive Surf reads as a HUNG LEG). ⚠ **The Archie fight is the chain's
one stochastic element — 2W/1L**, and a LOST run prints nothing (whiteout → Manual → KI-71 abandons
the generator) ⇒ the chapter needs a **whiteout-retry policy** and **pre-boss readiness**.
‼ Two reusable rules: **release is gated on a VAR, never on "looks controllable"**; and press
**A only when a text printer is waiting, B otherwise** (A beside an NPC starts a conversation —
the museum-greeter rule, `08-MISTAKES.md`).
## ✅ ROOM 8 (driven 2026-08-14) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (same day, when the PC/PARTY queue replaced the Ch20 queue)

Moved for the R3 budget. ‼ **Keep only what later work leans on:** `--driver ch20room8` PASSED
twice (clean 9/9, plus a FAULT run that EXERCISED the jam-recovery handler — `recovered=True`),
and ⛔ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit). Two adversarial
passes preceded the drive and BOTH changed something: an offline refutation of the 9-push table
(verdict SURVIVES) supplied the template data that turned KI-77's window into the exact
prediction *"8 of 12 boulders visible at arrival"*, which the live run matched exactly; and a diff
review caught the recovery handler HARDCODING an arrow-warp direction instead of deriving it from
the live tile. ⇒ *the happy path cannot exercise an error path — fault-inject it on purpose.*
## 🛡 THE DOC CONSISTENCY LAYER (2026-08-14) — the DIRECTIVE now lives in `CLAUDE.md`; read it before editing any doc

**Gate suite: `run_gates.py` PRINTS the count and is authoritative — this prose is not.**
`audit_doc_consistency.py` forbids the docs contradicting themselves or the code; `CLAUDE.md`
carries pairs **P1-P4** (banner↔queue, KI header↔body, STATE↔changelog, README↔files), **Tier 1**
(an independent agent per completed item's doc diff) and **Tier 2** (a cold-start agent at session
end). ⚠ **The gate is a FLOOR, not a sweep** — on 2026-08-15 it saw only 3 of 7 stale drift claims.
Origin detail: `28-HANDOFF-ARCHIVE.md`.

## ✅ ROOMS 1, 2, 6 AND 3 (driven 2026-08-13) — BANNERS in `28-HANDOFF-ARCHIVE.md`

All DRIVEN AND PASSING; ⛔ do not rebuild. ‼ **Four reusable rules:** *assert the OUTCOME, not the position
you expected* (Room 6); *the instrument was wrong, not the claim* (Room 3 — a discriminator counted
battles RUN-WIDE and printed a false REFUTED over data that CONFIRMED it); *copy upstream's ROUTE,
never its CONTROL FLOW* (Rooms 1/2 — pushes go through the bounded `strength_push`); and
**`FLAG_SYS_USE_STRENGTH` is cleared on EVERY WARP** — the code was safe, the COMMENTS were wrong.
⚠ Room 6's arrow-warp derived-direction branch is still UNEXECUTED; KI-77's despawn window (20x17)
has since predicted a live dump exactly.
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
## ⛔ NAMING CORRECTION — "§Ch21" IN OLDER TEXT MEANS **CHAPTER 20**. Read before acting.

The Seafloor Cavern / Kyogre beat is **Chapter 20** (`modules/story/chapters.py:233`); the genuine
**Chapter 21 is Sootopolis / Rayquaza** and has not been touched. ✅ **Rename DONE** (2026-08-13,
`#24-ch20rename`): `--driver ch20dive` (`Ch20DiveMode`), `probe_ch20_topology.py`, and
`2026-08-13-ch20-dive-leg-predictions.md`.
‼ **The old `ch21*` names SURVIVE ON PURPOSE in `06`/`07`/`08`** — those are append-only history
and are never rewritten, so entries dated on or before 2026-08-13 still say `ch21dive`. They mean
the Chapter 20 artefacts; both renamed files carry a provenance header saying so.

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
  **Both forks carry both fixes.** *(✅ And the KI-80 decoupling too, promoted 2026-08-16 — drift 0.)*
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
| branch / HEAD | `main`, **clean, 0 unpushed** |
| box | **IDLE.** Nothing running. Last batch `20260811-130454` (VERDICT OK, 28 runs). |
| story content | ✅ **§Ch19 COMPLETE 2026-08-12 — the MOSSDEEP SPACE CENTER is defended and HM08 DIVE is in the bag. 20 of 24 beats.** Littleroot → 6 badges → Mt. Pyre → Magma Hideout (and out) → Slateport submarine theft → the Lilycove AQUA HIDEOUT (with the MASTER BALL) → the MIND BADGE → **the Space Center multi battle + Dive**. (was 19 of 24 before Ch19.) |
| ‼ **§Ch20 SEAFLOOR CAVERN** | ✅ **DRIVEN END TO END (2026-08-14) — Kyogre awakened, atoll escape executed.** Seven drivers, all `ACCEPTANCE: PASS`: `ch20dive` (6/6) → `ch20room1` → `ch20room2` → `ch20room6` → `ch20room3` → `ch20room8` (PASS ×2 incl. a FAULT run proving jam recovery) → **`ch20room9` (NEW, PASS ×2 — runs 1 & 3; ⚠ run 2 LOST the Archie fight, a MEASURED 2W/1L on the chain's one stochastic element)**. Each run re-solves every room beneath it (`FLAG_TEMP_*` respawn on map load) — counts now **R1 n=13, R2 n=10, R6 n=9, R3 n=8, R8 n=5, R9 scene n=3 (full chain n=2)**. The cutscene chain is deterministic (identical milestone frame counts across passing runs); release gated on `VAR_ROUTE128_STATE == 2`; facing on release MEASURED `'Up'` ×2. ⛔ **NOT a chapter.** No module in `modules/story/`, nothing wired into `story_mode.py`, drivers **inject Dive with a debug write**. Ladder still **20 of 24**. **Remaining: CHAPTER ASSEMBLY** (organic Dive via KI-63 wiring, Repel policy, badge/move pre-flight, whiteout-retry for Archie, the atoll escape leg). |
| ‼ is code frozen? | **No.** Nothing is running. |
| party ORDER | ✅ **PROVEN 2026-08-13.** `--driver roster` from `saves/post_dive.ss1` → `phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True ACCEPTANCE: PASS`. Raw transcripts (both A/B arms) in `ai-research-notes/2026-08-13-roster-drive-predictions.md`. ‼ The **deposit/withdraw** half of `#24-roster` is still open. |
| upstream | checked **2026-08-16**, still `5dd898f8` — no change (re-fetched this session; `40cakes repo/UPDATE-LOG.md` already recorded the same date, and THAT file is the authority — this row only mirrors it). ‼ This row goes stale on a CALENDAR DAY, not on an event: if today's date is later than the one shown, **the daily check is DUE** (`git fetch upstream-pokebot`, compare against `40cakes repo/UPDATE-LOG.md`). Do not read it as satisfied. |
| restore point | **NEWEST: `restore/2026-08-16-pre-promotion-ki81-abort-guard`** (the KI-81 whiteout guard — roll back HERE to undo it; its BEFORE evidence is one commit EARLIER, in `6de47264`). Then `restore/2026-08-16-pre-promotion-ki80-decoupling` (the KI-80 BEHAVIOUR promotion — roll back HERE to undo it; its BEFORE evidence is one commit EARLIER, in `1c11927e`). Then `…-credible-answer-comment` (2026-08-16), then `…-ki79-pctrip` (2026-08-15). ⛔ *This row has now been caught stale TWICE — once naming the wrong tag by TIME, once by failing to add two newer ones. Both times a rollback taken from it would have gone to the WRONG point.* ⛔ *This row named `…-counterhunt-comment` as newest until a 2026-08-15 cold-start audit checked the tag DATES: `ki79-pctrip` is 18:00, `counterhunt-comment` is 16:30. A rollback taken from the row as written would have reverted to the WRONG point.* ‼ **`git for-each-ref --sort=creatordate refs/tags/restore/` is the authority, not this row.** Also today, oldest-first: `…-stage0-p4`, `…-boxwrite-docstring`, `restore/2026-08-15-pre-promotion-counterhunt-comment` (annotated, pushed, and verified on origin by `promote.py` BEFORE it copied) — taken immediately before the user-approved comment-only `counter_hunt.py` promotion, and therefore the rollback point for it. ⛔ *The promotion HAS been taken; the older row below still called it "the promotion decision below" as if pending.* Older: **`restore/2026-08-13-session-end-ch20room3`** (annotated, pushed) — taken at the END of the §Ch20 cavern session, immediately before Room 8, which is the riskiest room in the dungeon (a boulder pushed onto `(5,3)` **permanently seals the exit**). ‼ It is also the natural rollback point if the **promotion decision** below is taken. Older: **`restore/2026-08-13-pre-ki63-promotion`** (annotated, pushed) — taken immediately BEFORE promoting KI-63's fix. Older: `restore/2026-08-13-pre-roster-promotion`, `restore/2026-08-12-pre-ch1819-promotion`. |
| sandbox ↔ custom drift | ✅ **0 as of 2026-08-16 (LATEST) — EVERYTHING IS PROMOTED, the KI-81 WHITEOUT GUARD included (user-approved).** Restore point `restore/2026-08-16-pre-promotion-ki81-abort-guard`. ‼ **Proven by a MEASURED before/after, not a byte-compare:** `probe_abort_swallowing.py --build custom` fell **53 → 45**, custom's guarded-handler counts moved **0→3 / 0→4 / 1→2**, the PathFindingError split survived the copy, and the guard mechanism was re-verified importing from CUSTOM. **History below.** ✅ Previously 0 as of 2026-08-16 — EVERYTHING WAS PROMOTED, including the KI-80 DECOUPLING (a BEHAVIOUR change), user-approved.** Restore point `restore/2026-08-16-pre-promotion-ki80-decoupling`. ‼ **Proven by a THREE-POINT A/B against `--build custom`, NOT a byte-compare** — identical commands: `POKEBOT_KI80_DECOUPLED=1` went **FAIL → PASS**, the coupled expectation went **PASS → FAIL** (the mirror), and **arm 4 stayed PASS on both sides** — that invariance is what shows KI-23's mirror regression did NOT land. ⛔ The BEFORE half is unrepeatable once the copy happens, so it was run and committed FIRST, in `1c11927e`. **History below.** ✅ The earlier **COMMENT-ONLY** correction was promoted 2026-08-16 (user-approved), restore point `restore/2026-08-16-pre-promotion-credible-answer-comment`: the `CREDIBLE_ANSWER_POWER` docstring justified the threshold with *"Thunderbolt vs Winona"*, which is FALSE — Electric is `0.5x` Dragon `x 2.0x` Flying = **NEUTRAL** into Altaria. It is the FIFTH copy of an error whose other four were corrected the same day. ✅ **PROMOTED 2026-08-16, user-approved**, as the earlier comment-only `counter_hunt.py` fix was. ‼ **Proved behaviour-neutral by AST EQUALITY before copying** — `ast.dump(parse(sandbox)) == ast.dump(parse(custom))`, 323,580 chars each — and ⛔ that check was FAULT-TESTED (flipping `CREDIBLE_ANSWER_POWER` 75→76 makes it return False), because a check that cannot fail proves nothing. ⚠ **There is no three-point A/B here and there cannot be**: a comment has no branch to flip, so AST identity + `1/1 byte-identical` is the proof, and the `--build custom` drives only show the file still loads. ⛔ The edit was made **net-zero on line count** so it did not shift the `story_mode.py:NNNN` citations that fill the append-only logs (verified after: `grass_is_fodder` still `:1899`, `winona_fight` still `:3532`). ‼ **That promotion left the tree fully promoted AT THAT TIME** (⚠ historical; the figure is DESCRIBED not reprinted, because the gate cannot tell history from a claim — today's number is at the TOP of this cell); ANY unexplained file is worth stopping for.** **The rest of this cell is HISTORY, kept for its promotion evidence.** ✅ **0 as of 2026-08-15 (the promotion round) — BOTH promotions were DONE, USER-APPROVED, and VERIFIED BY DRIVING.** (1) `modules/story/pc_trip.py` — the KI-79 fix, a **BEHAVIOUR** change, restore point `restore/2026-08-15-pre-promotion-ki79-pctrip`. ‼ **Proven by a THREE-POINT A/B, because 1/1 byte-identical only proves a file was COPIED, never that its new branch is what RUNS:** with `POKEBOT_PCWITHDRAW_FAULT=1` against `--build custom`, the IDENTICAL command went **PASS (hook absent, inert) BEFORE → FAIL (`‼ THE WITHDRAW DID NOT LAND`) AFTER**, and an unfaulted AFTER run still PASSed. Transcripts committed under `tools/story-dev/evidence/`. (2) `modules/story/counter_hunt.py` — the comment-only Electric correction, restore point `restore/2026-08-15-pre-promotion-counterhunt-comment`. Both are also green on four `--build custom` gates that each ASSERT which fork they imported, and on `boxcounter2 --build custom` ARM A. ‼ **MEASURE, don't trust this row** — `promote.py --check` is the authority. *(That round expected 0 AT THAT TIME; today's figure is at the TOP of this cell.)* ⛔ Digits, not words. **The rest of this cell is the PREVIOUS state, kept for its promotion evidence — read "0"/"ZERO" below as *"zero at that moment"*, not as today's figure.** ✅ **0 as of 2026-08-15 (earlier) — every drifted file was PROMOTED, user-approved, and VERIFIED BY DRIVING.** Promoted: `modules/party_accounting.py` (new), `modules/pokemon_party.py`, `modules/modes/util/higher_level_actions.py`, `modules/debug_utilities.py`, `modules/story/counter_hunt.py`. **Evidence:** tool-side drift 0 both directions + 5/5 byte-identical; **`--driver ch20dive --build custom` → `legs=6/6 … ACCEPTANCE: PASS`**, matching sandbox; and FOUR `--build custom` gates (`repro_party_accounting` 33, `repro_heal_piggyback_reporting` 20, `repro_box_counter_move_test`, `repro_pid_identity_key`) each ASSERTING which fork it imported. Restore point **`restore/2026-08-15-pre-promotion-stage0-p4`** (annotated, pushed, verified on origin by the tool before it copied). ⛔ **Digits, not words** — this cell read a spelled-out "THREE" for a day, invisible to `audit_doc_consistency`'s drift check, and it survived two doc passes. ⛔ **What promotion does NOT mean:** party accounting is still STAGE 0 (it observes and decides nothing), `debug_write_box_slot` is PROVEN LIVE (`--driver boxwrite` → PASS, 2026-08-15), and (P4) is driven through **STAGE 2** (`--driver boxcounter2`, 4/4 across both forks, 2026-08-15) — ⛔ *this sentence read "STAGE 2 … is NOT built" until Stage 2 landed the same day; the drift figures around it are historical, this clause is CURRENT.* ‼ **Anything else appearing in `promote.py --check` is unexplained drift and is worth stopping for.** ⛔ The rest of this cell is the PREVIOUS state and is kept for its promotion evidence — read "ZERO" below as *"zero at that moment"*, not as today's figure: ✅ **ZERO as of 2026-08-14 (earlier) — KI-78 STAGE 1 WAS PROMOTED, user-approved, and it is the first promotion executed by `tools/story-dev/promote.py` rather than by hand.** The tool refuses on a dirty tree, a missing or UNPUSHED restore point, a diverged remote, or a no-op, and it re-measures drift in BOTH directions plus byte-equality per file — it also refuses to claim the driven verification it cannot perform. Restore point **`restore/2026-08-14-pre-promotion-ki78`**. **Evidence:** drift 0 both directions, 3/3 byte-identical; **`repro_pid_identity_key.py --build custom` exit 0** and **`repro_box_counter_move_test.py --build custom` exit 0** (both ASSERT which fork they imported before testing); plus a live drive against custom. ⛔ **KI-78 is still not fully closed** — its residual cases (R2 debug-fabricated pairs, R3 corrupt box slots, R5 Frontier rentals, R6 evolved-since-capture) stay open. ‼ **MEASURE, don't trust this row** — `promote.py --check` (in HOW TO RUN / TEST) reports it BOTH ways in seconds — ⛔ **this historical sentence expected 0 because that was true on 2026-08-14; it is 0 again TODAY after the counter_hunt.py promotion — but do not act on a historical sentence, run the command.** 📚 Every earlier drift state — including the 2026-08-13/14 rounds where `map_path.py`, `early_game.py`, `story_mode.py`, `counter_hunt.py` and `pokemon_party.py` were awaiting promotion — moved to `28-HANDOFF-ARCHIVE.md` on 2026-08-14, because stacking four supersessions in one cell made a promoted file read as still pending. |
| **if stopped mid-task** | **NO UNCOMMITTED WORK IS PARKED, AND NO PROMOTION DECISION IS OWED** — the LATEST promotion is the **KI-81 whiteout guard** (2026-08-16, user-approved, proven by a MEASURED before/after: the probe fell 53→45 on custom); the KI-80 decoupling was promoted earlier the same day. `promote.py --check` expects `0 differing, 0 orphaned`. ✅ **And KI-80's "needs a driven repro first" precondition is now MET** — `--driver ki80ladder` is built, driven in both forks and committed, so the decoupling is UNBLOCKED. ⚠ *That is a statement about SHIPPED WORK, not a claim that the user owes nothing anywhere:* the **boss/status battle-policy change remains the USER's call and must not be built unilaterally** (see the §Ch18/§Ch19 decisions block below), and **KI-80's decoupling** — whose driven-repro precondition is now SATISFIED (see above) — is a production BEHAVIOUR change and lands in sandbox only. Neither blocks a next session from starting. *(A Tier 2 cold-start read the old absolute phrasing as contradicting that policy line — correctly.)* Everything is committed and pushed; BOTH 2026-08-15 promotions (`counter_hunt.py`, `pc_trip.py`) are DONE and user-approved, and so are BOTH 2026-08-16 `story_mode.py` promotions (the comment-only correction and the KI-80 decoupling), so `promote.py --check` should report **0 differing, 0 orphaned** — ANY file it lists is unexplained drift and is worth stopping for. *(§Ch20's chapter assembly is deliberately PARKED as a work item, which is a different thing again.)* Start at "NEXT ACTIONS". |
| ‼ **`git stash` — KEPT ON PURPOSE (USER RULING 2026-08-13)** | **`stash@{0}` EXISTS, IS NOT YOURS, AND IS KEPT AS A RECORD. ⛔ DO NOT DROP IT.** `WIP on main: e0f723e4` (2026-07-24) — a 14-line Fortree Gym "only ride out a scene that exists" guard. Its substance is ALREADY in today's `early_game.py` (reimplemented during the rotating-gate rewrite), so it is functionally superseded — **and the user ruled that a superseded stash is still a RECORD and dropping it is a destructive act that buys nothing** (`06-DECISIONS-LOG.md`). ⛔ **Standing rule: never `git stash drop` / `clear` / `pop` in this repo.** `pop` is separately banned because it mutates a GLOBAL stack — that is how this stash was disturbed in the first place (`08-MISTAKES.md`). To read it: `git stash show -p "stash@{0}"`, and apply by hand if ever needed. ‼ A stash is invisible to `git status` and to the kit's sync check, which is how it sat unnoticed for three weeks — so `git stash list` belongs in the session-start ritual, to SEE it, not to clear it. |

## ✅ WHAT SHIPPED IN THE §Ch19 + PROMOTION + ROSTER SESSION (2026-08-12) — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

History, moved for the R3 budget. ‼ **Keep only what a future session still needs:** §Ch18 and §Ch19 shipped and were **PROMOTED** to `custom-pokebot/` (verified by DRIVING `--build custom`, never by a diff) taking the ladder to **20 of 24**; **KI-64** was fixed after being **wrong twice** (dead code on the story path, then a positional cut in the wrong index space — now keyed on **original trainer ID**); **KI-67** closed both halves, including this project's **first driven whiteout recovery**, where the proof was the **frame delta** (+7,789 / +7,087), not the count; and two gates were found **blind** — the flag audit was checking 2 files, and `pyflakes` had never been run. `modules/story/roster.py` (party reorder) also landed here.

## ✅ §Ch18 (Mossdeep Gym + the statue puzzle) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Shipped, wired as Segment 18, promoted. ‼ **Keep only the lesson:** the gym is a **rotating-tile
statue puzzle**, and four of our own instruments agreed it had no route because all four modelled it
as *walk + warp* and it has a **third movement primitive**. ⇒ *When N of your own instruments agree
on something impossible, they share a missing primitive.* It also **shipped stranded on an
eleven-tile island** while passing `badge + controllable`.
## ‼ THE TWO THINGS THAT MATTER MOST FROM THE §Ch18 SESSION — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Moved for the R3 budget. ‼ **Keep both, they are the most reused lessons in this project:** (1) **When N of your own instruments agree on something impossible, they share a missing primitive** — four instruments agreed the Mossdeep Gym had no route to its own leaders; all four modelled it as *walk + warp*, and the gym has a **third movement primitive**. Even the model-free brute-force walker was wrong, because it *changed the map while exploring it*. (2) **EVERY DEFECT THAT MATTERED WAS FOUND BY AN ADVERSARIAL AGENT, NOT BY A TEST** — three times in one session, each over green runs, because *the happy path cannot exercise an error path* and an acceptance test written by the author of the code inherits its blind spot. ⇒ **Spend agents on REFUTING finished work, not only on researching new work**, and **write the predicted failure down BEFORE the run.**

## ‼‼ THE BATCH RESULT (status tax + `#24-teachmsgstall`) — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)  — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Moved for the R3 budget. ‼ **Keep only its prevention rule, which is the most re-learned lesson in this project:** *a chapter's acceptance test must include **"and the bot can continue"*** — a REAL `calculate_path` off the end tile, not a "controllable" flag. §Ch15 ended four floors underground, §Ch18 on an eleven-tile island, and §Ch19 in a living room, and **all three passed their own tests**. Every §Ch20 driver carries that assertion.

## 🛡 THE HARDENING ROUND (advisory rules → code that refuses) — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

The tool-by-tool table moved out for the R3 budget. ‼ **Keep this:** it was driven by the finding that **≥12 of 164 logged mistakes are self-admitted REPEATS**, several committed while the author knew the rule — and **three of those tools found real problems on their first run** (six competing START-HERE banners, an 11th undocumented flag which turned out to be the roster blocker, and 140 silent handlers). **Run `preflight.py` before touching anything**, and see `29-DISABLED-FEATURES-REGISTRY.md` before proposing any feature behind a `POKEBOT_*` flag.

## ‼ WHAT THE USER DECIDED IN THE §Ch18/§Ch19 SESSION — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Moved for the R3 budget. ‼ **Keep this:** the **boss/status battle-policy change is still the USER's call and must not be built unilaterally** — the status tax now has a resolved rate behind it, but a status response touches every mode. And the "roster hygiene before bosses" unlock was **RETRACTED**: it was said to be one `POKEBOT_BOX_OVERFLOW_CATCH` flag and one text box away, and **both halves are false** — that flag has defaulted **ON** since 2026-08-07 and the text-box blocker was refuted the same day. Four docs repeated it because they were written from a **stale code comment** instead of the default twenty lines below it.

## ✅ KI-56 (Magma Hideout strand) — resolved 2026-08-11, detail ARCHIVED

Full block moved to `28-HANDOFF-ARCHIVE.md`; the issue itself is in
`31-KNOWN-ISSUES-ARCHIVE.md`. ‼ Keep only this: its prevention rule — **a chapter's test must
include "and the bot can continue"** — was violated AGAIN by §Ch18 on 2026-08-12, which passed
`badge + controllable` while parked on an eleven-tile island. It is the most re-learned lesson
in this project. Read it before writing any chapter's acceptance test.

## ✅✅ §Ch19 IS DONE (Space Center + HM08 Dive) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Shipped, wired as Segment 19, promoted to `custom-pokebot/`, ladder 19 → 20 of 24. Moved out of this
current-state file for the R3 budget when the §Ch20 Room 1/Room 2 drives landed. ‼ **Keep only the
four gotchas** — they are still true if you ever touch that chapter: (1) Mossdeep is **cut in two**
until the forced cutscene runs, so leg 1 is two legs; (2) the stair grunt **must be talked to**
(`sight_radius = 0`, standing on the only reachable tile); (3) the party-selection menu is **driven,
not mashed** — A on an already-picked mon DESELECTS it, and every pick is verified against
`gSelectedOrderFromParty`; (4) **losing is a RETRY, not an error** — the script calls
`SetCB2WhiteOut` itself and leaves the var at 2. ‼ And it **nearly shipped stranded, in a living
room**, with every completion signal true — which is why every chapter's acceptance must ask for a
real `calculate_path` off the end tile.
## 🛠 TWO GATES WERE BLIND, AND FIXING THEM FOUND A REAL BUG — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Moved for the R3 budget. ‼ **Keep this:** `audit_flag_names.py` was checking **TWO files** and could only see names written as literals AT the call site, while the house idiom is a module constant — so it was **blindest exactly at the completion markers**. Now 19 files / 144 names and it **exits 1** on a phantom. And **`pyflakes` was installed and had never been run**; the new `repro_undefined_names.py` gate found a `NameError` on the Magma Hideout's *success* path, plus KI-65. ⇒ *A gate that has never failed may simply not be looking.*

## ‼‼ THE ADVERSARIAL REVIEW THAT FOUND MY OWN §Ch19 FIX WAS WRONG TWICE — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Moved for the R3 budget. ‼ **Keep the two prevention rules, both re-learned since:** (1) **print the MRO before "fixing" a strategy method** — the first fix guarded the base class and was DEAD CODE on the story path; (2) **never identify a Pokémon by party INDEX across a battle-menu boundary** — opening the battle party menu runs `UpdatePartyToBattleOrder`, which PHYSICALLY PERMUTES `gPlayerParty`, so the `index >= 3` cut offered the ALLY's Pokémon and hid one of ours. Key on **original trainer ID**. ‼ And the meta-lesson: **my fault-injected A/B passed it anyway**, because all three arms modelled the un-permuted order — *a control arm does not save you if every arm measures the wrong thing.*

## ‼ THE §Ch19-ERA ISSUES (KI-64 … KI-67) — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Moved for the R3 budget; all four are in `05-KNOWN-ISSUES.md` or its archive with full detail. ‼ **Keep only what is still live:** **KI-65 (OPEN)** — `battle_move_replacing.py:280` binds `party_index` on a path that a silent `except` can skip, so a later `CantForgetHM` raises `UnboundLocalError` into a SECOND silent `except` that declines: **two invisible failures that compound**. **KI-66 (OPEN, unverified)** — the multi-battle hazard is broader than the faint chooser: four more full-party scans on the same paths, and a claimed `IndexError` in `decide_turn_in_double_battle` from `gPlayerPartyCount` still being 3, which would fire on **turn 1** rather than on a faint — check that FIRST. ‼ The right fix is ONE choke point (`ally_party_indices()` now exists), not a guard per call site. KI-64 and KI-67 are CLOSED.

## 🆕 THE REGI ARC (user-requested) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13). See **KI-69**.

Moved for the R3 budget; the arc is item 4 in NEXT ACTIONS and is not started. ‼ **Keep these four, every one of which fails SILENTLY if got wrong:** (1) **Emerald REVERSED the party order — WAILORD first (slot 0), RELICANTH last** (`braille_puzzles.c:92-104`); the R/S order everyone remembers is wrong and the wrong order gives no message and no error. (2) ⛔ **The Regi battle is UNRECOVERABLE** — level 40, catch rate 3, and the fall-through case **including `B_OUTCOME_LOST`** sets `FLAG_DEFEATED_*`, so **a KO *or* a whiteout deletes the encounter permanently**; the only safe non-catch exit is fleeing. (3) **REGICE IS NOT A TIMED WAIT** — Emerald wants a **36-tile perimeter lap in ONE visit** ending exactly on `(8,21)`, reset by any map transition and by one wrong tile. (4) Measured capability gaps: **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or Flash — and **Relicanth is underwater-only, so Dive is upstream of the whole arc.** Ground truth: `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md`.

## ⏭ NEXT ACTIONS, IN ORDER

> **The ordered work queue** (the cold-start orientation is the ‼ YOU ARE HERE block at the top of
> this file, not here). Everything is committed and pushed; nothing is parked.
>
> 0. ‼ **THE LIVE QUEUE (updated 2026-08-14) — DO THESE FIRST; items 1-5 below are older framing.**
>    ‼ NEW STANDING RULE FOR EVERY ITEM BELOW: doc edits run Tier 0 (`lint_docs` +
>    `audit_doc_consistency`, both exit 0) before their commit, and a completed item gets a
>    Tier 1 independent review of its doc diff — see `CLAUDE.md`'s DOC CONSISTENCY LAYER.
>    ✅ **(a) (b) (a2) (a3) (a4) ARE ALL DONE, AND (c) IS OBSOLETE — every §Ch20 room is DRIVEN
>    AND PASSING. ⛔ DO NOT REBUILD ANY OF THEM.** `ch20room2/3/8/9` all reached
>    `ACCEPTANCE: PASS` (Room 3 ×2 with the DOUBLE-battle claim confirmed live; Room 8 ×2 incl. a
>    fault run proving jam recovery, `recovered=True attempts=2`; Room 9 ×2, the cavern END TO
>    END). (c) died because KI-77's despawn window is **20x17** and Room 8 is **11x14**, smaller
>    than it, so KI-77 cannot fire there — a repro is still worth having for the LARGE rooms but
>    blocks nothing. ⚠ Room 9 run 2 LOST the Archie fight (**2W/1L measured** — the party arrives
>    chipped and there is no heal in the cavern): that is CHAPTER-DESIGN input, not a driver
>    defect, and it is why the chapter needs a whiteout-retry policy.
>    ⛔⛔ **THE USER REDIRECTED PRIORITIES ON 2026-08-14, AFTER Room 9 landed. §Ch20 CHAPTER
>    ASSEMBLY IS NO LONGER QUEUE ITEM 0 — IT IS PARKED, READY, AND WAITING.** The live queue is
>    the **PC / PARTY ROBUSTNESS ARC** below. This was triggered by a live user test: a Winona
>    counter-hunt caught Slugma, healed, **derailed to Manual**, and on continue re-fought Winona
>    without the counter. The user's words: *"I want to ensure that the bot can robustly,
>    intelligently and strategically use the pokemon pc"*, and *"we should shift focus onto this
>    first so future issues can be handled better."*
>
>    **THE LIVE QUEUE, IN ORDER:**
>    ✅ **(P1) The Slugma derail — FIXED, A/B PROVEN, GATED, PROMOTED.** `box_counter_pid` was
>    TYPE-ONLY while its party twin had accepted MOVE answers since 2026-08-08 — a fix applied to
>    one half of a documented pair. Gate `repro_box_counter_move_test.py` (#19) carries a PARITY
>    check so they cannot drift again. Also fixed: `catch_confirmed()` replaced a party-COUNT
>    delta (which a Shedinja spawn could fake) with an IDENTITY verdict.
>    ✅ **(P2) KI-78 Stage 1 — FIXED, A/B PROVEN, GATED (#20), AND PROMOTED (2026-08-14).**
>    Identity is now `(personality, species)`; a Shedinja shares its Ninjask's PID and the old
>    first-match lookup would **RELEASE the wrong Pokémon (permanent)**. ✅ **drift is ZERO —
>    the fix is in BOTH forks**, verified by `--driver ch20dive --build custom` →
>    `ACCEPTANCE: PASS` and by both `--build custom` gates. Superseded: *"drift is 3 —
>    custom-pokebot has the WARNING but not the FIX."*
>    ⛔ **KI-78 is NOT fully closed** — residual cases stay open (debug-fabricated identical
>    pairs, corrupt box slots, Frontier rentals, and the evolved-since-capture path, which is
>    handled but **unexercised by any live caller**). See its entry.
>    ✅ **(P3) STAGE 0 — BUILT, GATED (#22), DRIVEN.** `modules/party_accounting.py` adds the
>    readers (**A** `gPlayerPartyCount`, per-slot occupancy) and a divergence log: **HOLE** (empty
>    slot below A — what makes B < A), **OVERFLOW**, **INVALID**, all EXACT from `get_party()`'s own
>    branches, plus **STALE**, ⛔ SAMPLED 1-in-300 (read the scan count, never the bare zero).
>    ✅ It wires NO call site and the gate ASSERTS that, with a byte-identical observer-on/off A/B
>    and a fault-injected observer that must break the LOG and never the read.
>    ✅✅✅ **(P3b) IS ANSWERED BY CRITERION (b) — A DIVERGENCE WAS OBSERVED (2026-08-15). ⛔ THIS
>    SUPERSEDES THIS FILE'S EARLIER "CRITERION (a) MET … NO DIVERGENCE" — THAT CLAIM IS RETRACTED.**
>    `collect_party_accounting.py` now reports **`✅ CRITERION (b) MET — A DIVERGENCE WAS OBSERVED`**:
>    **`HOLE x30` in `boxcounter2`, in BOTH forks** — *slot 5 of `gPlayerPartyCount=6`: counted by
>    the game but (near-)all zero*. Totals are now **967,970 recomputes · 39 drives · 12 drivers**
>    (the earlier ">400k / 11 drivers" and "7 drives / 280,707" figures are both superseded and
>    disagreed with each other).
>    ‼ **THIS IS THE GOOD OUTCOME, AND IT IS EXACTLY WHAT (P3b) PREDICTED.** Its own caveat said the
>    population lacked any PARTY-MUTATING drive, so the cases most likely to make A differ from B
>    were never exercised. `--driver boxcounter2` (Stage 2) became the first such drive — a real PC
>    deposit AND withdraw on a FULL party of 6 — and **the divergence appeared immediately, in both
>    forks.** The make-room deposit is the moment A and B disagree.
>    ⛔ **THE DATA SAT IN THE COMMITTED LEDGER FOR THREE COMMITS WHILE TWO WRAP-UP PASSES RE-ASSERTED
>    "NO DIVERGENCE"** — nobody ran the command this file itself calls the authority. ⇒ *a figure
>    quoted from memory is not a measurement; RUN `collect_party_accounting.py`.*
>    ✅✅ **PARTY-ACCOUNTING STAGE 1 IS THEREFORE UNBLOCKED** (re-pointing the ~35 capacity-shaped
>    call sites at A). It was gated on "the criterion above is met"; criterion (b) IS met, and the
>    collector says what to do next: **reproduce the `HOLE` case, then design Stage 1 around it.**
>    ⛔ Index/menu-cursor call sites STILL stay on B — if A > B an index from A is out of range for
>    the list the bot holds, most likely MID-BATTLE.
>    ‼ **"Stage 1" is OVERLOADED in this file:** *KI-78* Stage 1 is the identity fix and is **DONE
>    and PROMOTED**; *party-accounting* Stage 1 is this one and is now **UNBLOCKED, not forbidden**.
>    Never read one for the other.
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
>    ✅✅ **STAGE 1 IS DRIVEN (`--driver boxcounter`), BOTH ARMS PASS — the first time
>    `box_counter_pid` ran against REAL `gPokemonStorage` memory rather than `FakeStorage`.**
>    ARM B → the Slugma's PID (found by its MOVE); ARM A
>    (`POKEBOT_BOXCOUNTER_TYPEONLY_A=1`) → `None`, **the user's bug reproduced on demand**.
>    Four controls: `disjoint` (pure FIRE, so the type branch is provably inert), `fixture_ok`
>    (read back through the PRODUCTION reader — mandatory, since a bad fixture is
>    indistinguishable from ARM A's expected miss), `sole`, and `not_excluded`.
>    ✅✅ **STAGE 2 IS DRIVEN (2026-08-15) — `--driver boxcounter2`, matrix {ARM A, ARM B} ×
>    {sandbox, custom} = 4/4 `ACCEPTANCE: PASS`. ⛔ DO NOT REBUILD IT.**
>    It SUBCLASSES `BoxCounterMode`, so every Stage 2 run re-proves Stage 1 first.
>    **ARM B:** the real `heal_in_pokemon_center(FortreeCity)` collected the boxed Slugma —
>    `moved=True` (in party AND gone from box), `knows_rock_throw=True`, `lead_is_counter=True`
>    with a `hunted_pids=None` CONTROL proving the mechanism was decisive
>    (`control=Mightyena L38` → `real=Slugma L15`), and a second heal that NO-OPed *for the
>    attributed reason* (`find_in_box=None` AND still in party). Production made room itself
>    (`depositing Skitty L17`). **ARM A:** `box_counter_pid` → `None` → `_hunted_counter_pids`
>    published EMPTY → the withdraw piggyback did nothing → `still_boxed=True not_in_party=True`
>    and **no deposit at all** — the user's derail, produced by production, not simulated.
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
>    (`story_mode.py:1083`) that named no type list, so the grep for the type set walked past it.
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
>    `story_mode.py:3531`; ⛔ she has NO `grass` key today, and that is the only reason her ladder works) → **plain escalation,
>    ladder SKIPPED**. `ACCEPTANCE: PASS` on `--build sandbox` AND `--build custom`.
>    ‼ **The driver EXITS 0 even on FAIL — grade the `ACCEPTANCE:` line, never the exit code.**
>    Fault-tested twice: against `ch13_fortree_door.ss1` it FAILS with *"THE A/B WOULD BE VACUOUS"*
>    and all three arms return `LADDER` — a live demonstration that the fixture this file once
>    prescribed would have read as a REFUTATION of a true finding; and `POKEBOT_KI80_DECOUPLED=1`
>    FAILS today, which is what makes it usable as the AFTER run.
>
>    ✅✅ **DONE 2026-08-16 — THE COUNTER-LADDER IS DECOUPLED FROM `grass_is_fodder`. ⛔ DO NOT
>    REBUILD IT.** `:1901` is now `if boss_teaches:` and `boss_mode = True` sits behind its own
>    `if grass_is_fodder:` — the one-line version would have shipped KI-23's mirror regression, and
>    arm 4 measured it doing exactly that. Blast radius (arithmetic measured, behaviour inferred):
>    **Brawly** gains the machinery across his band, **Roxanne** at `team_max` 13-16, **Wattson** at
>    20-22; Norman unchanged; the Rustboro rival unaffected (no `ace_types`).
>    ✅✅ **AND IT IS PROMOTED TO BOTH FORKS (2026-08-16, user-approved)** by a THREE-POINT A/B
>    against `--build custom`: `POKEBOT_KI80_DECOUPLED=1` **FAIL → PASS**, the coupled expectation
>    **PASS → FAIL**, and **arm 4 PASS on BOTH sides** — that invariance is what shows the mirror
>    regression did not travel with the fix. ⛔ **THE KI-80 ARC IS CLOSED; DO NOT REOPEN.**
>
>    ➡➡ **THE HEAD OF THE QUEUE IS `(P4c) #24-orphans` — ✅ (4) DONE 2026-08-16, FIVE REMAIN.**
>    ‼ **Cost order and STARTABILITY order differ, and the item lists only cost.** (1) is costliest
>    (no caller acts on `withdraw_from_box`'s verdict) but SPLITS: the INSTRUMENTATION half is fully
>    specified — return a verdict, bind it at its ONE caller (`higher_level_actions.py:344`), report
>    it, assert it two-armed with `POKEBOT_PCWITHDRAW_FAULT` — while the REACTION POLICY needs the USER.
>    ‼ The discriminator is real: today BOTH arms return `None` to the caller (that is the bug);
>    after the change they return True/False. ⇒ **fully startable with zero input: (2) KI-65 and
>    (3) KI-66**, both OPEN and code-verified. *(Tracked alternatives: `#24-zerokocounter`, which needs TWO new arms
>    plus a frequency measurement before anything ships; or (P5), the catch-policy round.)*
>    *(The detailed HOW-TO for this decoupling — the mirror-regression mechanism, the arm-4
>    fixture arithmetic, and the measured proof that the 3-arm suite alone would have blessed
>    the naive edit — is ARCHIVED in `28-HANDOFF-ARCHIVE.md`. The work is DONE; the reasoning
>    survives in `06-DECISIONS-LOG.md` and KI-80.)*
>    ✅ **(i) `counter_hunt.py` and (ii) KI-79 `pc_trip.py` are BOTH CLOSED AND PROMOTED** —
>    evidence moved to `28-HANDOFF-ARCHIVE.md` (2026-08-15, line budget). ‼ **Keep only the rule:**
>    *a byte-compare is NOT proof for a BEHAVIOUR promotion — a three-point A/B is* (PASS before →
>    FAIL after faulted → PASS after unfaulted), and run 1 is unrepeatable once the copy happens,
>    so it runs and commits FIRST. Hook `POKEBOT_PCWITHDRAW_FAULT`; detail in KI-79 + `07`/`06`.
>
>    🆕 **(P4c) `#24-orphans` — SIX REAL RESIDUALS THAT WERE WRITTEN DOWN BUT NEVER TRACKED**
>    (filed 2026-08-15, full list in `03-PUNCH-LIST.md`). ‼ **Four of the six were recorded inside
>    a document half marked DONE or ARCHIVED** — a CLOSED KI's body, an "older framing" block, a
>    research note — which is the P2 header-vs-body failure applied to TRACKING. Highest cost:
>    **no caller acts on `withdraw_from_box`'s verdict** (KI-79 made the message honest; production
>    still cannot REACT), plus **KI-65** and **KI-66**, both OPEN and code-verified and absent from
>    every queue. ⛔ Cheap to pick up, and each is a real defect rather than a nicety.
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
> 1. **Run `preflight.py`**, then the **24**-gate suite in "HOW TO RUN / TEST" (all exit 0
>    2026-08-15; it has said 17, 18, 19, 20, 21, 22 and 23 on its way to **24** — `run_gates.py` is authoritative, never this prose), and the drift check below.
>    ✅ **EXPECT 0 differing, 0 orphaned — everything is promoted**, the KI-81 whiteout guard
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
>    ✅ **(i) `#24-ch20rename` and (ii) the §Ch20 AREA ATLAS ARE BOTH DONE, and all nine rooms are
>    DRIVEN — do NOT re-measure or re-drive.** ‼ **Keep the two lessons:** §Ch20 is a
>    **STRENGTH-BOULDER dungeon, not a route** (Rooms 6/7 are open water needing SURF, not
>    Strength); and an atlas read REMOTELY is a **LOWER BOUND** — `is_tile_accessible` blocks every
>    tile whose object is not in `active_objects`, so a remote read's NO-PATHs are an ARTIFACT, not
>    a map fact (§Ch19 hit this too).
>    **(ii-continued) THE BUILD SPEC IS WRITTEN:**
>    `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md` — an 11-leg list, each with an
>    assertable condition, from a decomp recon that ran an exhaustive Sokoban search over
>    (player × boulder) states. ✅ It independently agrees with our own `probe_ch20_interior.py`.
>    **Its three corrections to what we believed:**
>    1. ‼ **ROCK SMASH IS MANDATORY, not just Strength** — a Strength-only party is *physically
>       stuck in Room 1* (`(5,10)` is a breakable rock and the only way into the row-11 corridor).
>       We have both on Sceptile; the chapter must ASSERT it in pre-flight.
>    2. ⛔ **The trigger tile is `ROOM9 (17,42)`, not `(16,42)`** — corrected in this file and in
>       `story_mode.py`. `(16,42)` is plain floor; upstream's solver stops one tile short of it.
>    3. ⛔ **Grade the chapter on `VAR_ROUTE128_STATE == 2`, NOT on the Kyogre flag.** The flag is set
>       BEFORE a forced `warp MAP_ROUTE128, 38, 22` that immediately starts a SECOND `lockall`
>       cutscene — so a flag-graded chapter reports success while the bot is inside two nested
>       scenes. ‼ And `(38,22)` is a shallow-water **SANDBAR**: the bot lands on an island and must
>       **Surf** off it. Three chapters have shipped stranded; this one strands you by design.
>    ✅ **THE BIGGEST UNKNOWN IS NOW ANSWERED AT THE PLANNING LEVEL (2026-08-13):**
>    `probe_ch20_currents.py` (NEW) put **4 pre-registered predictions** to our REAL planner on the
>    two current mazes and got **4/4, including the DISCRIMINATING one**: `ROOM6 (11,21)->(4,1)`
>    routes, and **`ROOM6 (4,1)->(11,21)` correctly FAILS** — our planner reproduces the currents'
>    ONE-WAY asymmetry independently of the decomp note. ⚠ **BUT AN AUDIT CORRECTED HOW MUCH THAT
>    PROVES (KI-76):** our one-way result comes from an **INVENTED entry mask** (we forbid entering a
>    current head-on against its flow) — the decomp imposes **no entry restriction on currents at
>    all**. The mask is benign and reachability-equivalent here, so the CONCLUSION holds, but
>    "independently reproduced the game's asymmetry" **overstated it**. ‼ **And the slide model is PROVEN in use, not assumed**: P1 emits 13
>    waypoints for a 27-tile Manhattan trip and P4 emits 12 for 24 — impossible with 1-tile steps.
>    ‼ **Measurable from outside the cavern ONLY because Rooms 6/7 have ZERO objects** (so the
>    `active_objects` artifact that invalidated the boulder rooms cannot apply here).
>    ⇒ **Rooms 6/7 can be driven with `navigate_to`; they do NOT need a §Ch18-style solver.**
>    ✅ **KI-76's SAFETY HALF IS FIXED (2026-08-13):** the slide loop now has a **512-step cap that
>    fails LOUD** (fault-tested at cap=3; A/B output byte-identical) and all four
>    `_get_connection_for_direction()` `None` unpacks are guarded. **Measured first:** only **FIVE
>    maps in the whole ROM have currents** — `ROUTE133` 1552, `ROUTE132` 1345, `ROUTE134` 1262,
>    `ROOM7` 117, `ROOM6` 108 — **0 armed tiles**, and **no currently-driven map has any current at
>    all** (`probe_current_edges.py`). ‼ **Routes 132/133/134 carry ~10x the cavern's currents and
>    are UNMEASURED for cycles** — and they are the route to the **Sealed Chamber (Regi arc)** and
>    **Ever Grande (§Ch23)**, so that is where these defects are really armed.
>    ‼ **KI-76's CORRECTNESS HALF IS STILL OPEN:** a slide that ENDS ON A WARP is never penalised
>    (`map_path.py:915`'s warp cost is applied one branch BEFORE `:957` substitutes the slide
>    destination), and A* is **actively biased toward long slides** (~9x cheaper than walking under
>    `avoid_encounters`). `ROOM6 (14,8)` is a water-level door and **9 of its 108 chains end on it**.
>    ✅ Measured: the four routes we actually plan spring **0** traps — `probe_ch20_currents.py`
>    section 3b asserts it — but that is not a general guarantee. **Re-run that assertion for any
>    NEW route through Room 6.**
>    ✅ **SUPERSEDED 2026-08-13 — the executor HAS now crossed a current** (`--driver ch20room6`,
>    `crossed=True`). Only the tile-by-tile slide model remains unverified.
>    ℹ Upstream `puzzle_solver.py:405` DOES `navigate_to(ROOM6, (4,1))` and its wiki marks the
>    Seafloor Cavern ✅ for Emerald — the strongest available signal that the executor can do it,
>    and still a third-party claim, not evidence.
>    Also: **puzzle state RESETS on every map re-entry** (`FLAG_TEMP_*`), so never cache "solved";
>    `FLAG_SYS_USE_STRENGTH` by contrast persists. **Losing to Archie resets the whole dungeon.** It IS the ladder
>    (`chapters.py:233`, graded `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`; `story_mode.py:3654` = END OF BUILT
>    CONTENT — ✅ **that line was ALREADY FIXED** — it now reads "KI-63 IS RESOLVED"; the string "BLOCKED BY
   KI-63" does not occur in that file. This instruction is retired, 2026-08-13). Uniquely
>    de-risked: the dive leg is **driven 6/6**, KI-63 is wired in sandbox, and `puzzle_solver.py`
>    hands you room coordinates free. Blast radius is **additive** — one module, one segment, no
>    shared code. Two cheap traps: apply **KI-72** (hand-pick the surfacing tile, assert its
>    `tile_type` — never let the planner choose), and ⛔ **THE TRIGGER TILE IS `ROOM9 (17,42)`, NOT
>    `(16,42)`** — corrected 2026-08-13, `(16,42)` is plain floor and fires nothing. It is
>    Archie's cutscene tile — the standing rule is *"and the bot can continue"*.
>    **(iii) `#24-r110mauville` / KI-48** — the highest-frequency OBSERVED defect (72 events in one
>    batch, 3/3 deterministic). Budget a MEASUREMENT; its root cause is still a hypothesis.
>    **(iv) THEN the Regi arc.** ‼ Its real cost, measured: **10 missing gates and ~7 subsystems that
>    do not exist** (fishing as a story capability — `fish()` has zero story callers and rod choice
>    is a **human GUI prompt**; underwater encounters — `EncounterType` has no Underwater member; TM
>    acquisition + `use_tm`; Flash acquisition; a no-KO/no-whiteout legendary policy; a **bounded**
>    exact-tile executor; and **no chapter entry at all**), behind a hard 9-step serial prefix.
>
> 4. ⛔ **NOT NEXT — OLDER FRAMING; a Tier 2 audit flagged that a skimmer could start the Regi arc
>    from here. The live queue is item 0 and its head is **(P4c) `#24-orphans`**. Background only.**
>    **The REGI arc (user-requested) — read KI-69 ‼ AND ITS NEW STUB MARKER.**
>    ⛔ **REGICE IS NOT A TIMED WAIT** — R/S's wait function is an empty stub; Emerald wants a
>    **36-tile perimeter lap in ONE visit** ending exactly on `(8,21)`, reset by any map transition
>    and by one wrong tile. Full ground truth:
>    `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md`. ‼ **WAILORD first, RELICANTH last** (Emerald
>    reversed it; the wrong order fails silently). ‼ **The Regi battle is UNRECOVERABLE** — a KO *or*
>    a whiteout deletes the encounter; only fleeing is safe. Phase A is measured: we have Go-Goggles,
>    HM08, Surf and Rock Smash; we have **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or
>    Flash. **Relicanth is underwater-only, so Dive (item 3) is upstream of the whole arc.**
>
> 5. Older framing (measurements only; CONCLUSION superseded by items 3-4) — ⛔ also NOT next:

> 2b. **‼ THE NEXT BUILD IS NO LONGER BLOCKED THE WAY THE DOCS SAID.** §Ch20/§Ch21 need **Dive
>    USED**, and KI-63 is real (no party member learns it, party 6/6). But the thing four documents
>    called the gate — `POKEBOT_BOX_OVERFLOW_CATCH` being off and "one unhandled text box" away —
>    **is false and has been since 2026-08-07.** It defaults to ON; the text box needs no handling.
>    **Verify it yourself at `story_mode.py:2241-2243` before believing either version.**
>    **THE PLAN (measured against `modules/data`, detail in KI-54's new section):**
>    * **Spheal**, ~50% of the `SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM` LAND table at L26-32, catch rate
>      255, learns **Surf AND Dive**. Mossdeep → Route 125 → the entrance room is **one warp**.
>      ⚠ TIDE is the one risk: the high-tide maps have **no encounter header at all**, and which RTC
>      hours give low tide is **UNVERIFIED**. Tide-free fallback: **Marill on Route 120** (15%, L25-27).
>    * ⛔ **RETRACTED 2026-08-13 — THE DEPOSIT PATH NAMED BELOW CANNOT DO THIS JOB.** Superseded by
>      `ai-research-notes/2026-08-13-ki63-dive-learner-acquisition-plan.md`. Verified directly:
>      `withdraw_from_box` opens with `target = find_in_box(pids); if target is None: return`
>      (`modules/story/pc_trip.py:420-421`), so with nothing yet boxed **it returns having done nothing** — its
>      deposit block is only reachable as a side effect of withdrawing an already-boxed PID. And
>      `deposit_dead_weight_if_worth_it` **is** a standalone one-deposit primitive but is a **silent
>      no-op** behind `POKEBOT_PC_ROTATION` (`pc_trip.py:83`). ⇒ **A new narrow, ungated,
>      one-deposit function must be written.** ‼ Also: **deposit-first is the wrong ORDER** —
>      `ensure_hm_learner` checks for an existing learner *before* the party-full check, so try it
>      first and deposit only on that specific failure. (Still true from the old text: the victim is
>      **Skitty L17**, and Zigzagoon L15 is EXEMPT as sole Surf carrier — re-measured 2026-08-13.)
>      Superseded text: Freeing one slot reuses `withdraw_from_box`'s deposit block (~`modules/story/pc_trip.py:437-461`), which is live-proven and deposits exactly ONE mon.
>    * ⛔ **Do NOT fetch the Super Rod first** — Sharpedo/Wailmer are real, but it needs three missing
>      subsystems (no rod chapter, no fishing capability at all, and `_hm_hunting_grounds` reads
>      land encounters only) against one `TRAINING_GRASS` row.
>    * ✅ **THE TIDE IS NOT A BLOCKER (measured 2026-08-12).** The high-tide "maps" have no encounter
>      header and no warps — they only own a LAYOUT that gets borrowed onto map (24,46), and the
>      encounter table keys off map number, not layout. **The Spheal 50% table is live at BOTH
>      tides** (65 walkable encounter tiles at high, 332 at low). No tide handling needed.
>      **Surf is the only gate** and we have it: `MOSSDEEP_CITY → ROUTE125` routes in 119 waypoints,
>      Zigzagoon L15 knows Surf, and Route 125 → the entrance room is one warp.
>    * ‼ **BUT THE REAL GATE IS STILL THE FULL PARTY** — `ensure_hm_learner` raises when the party is
>      ≥6 **before** it ever looks for a hunting ground. Free the slot first; the ground is
>      necessary, not sufficient.
>    * ⚠ Two hazards recorded in KI-54 before anyone codes in that room: `MapLocation` always
>      resolves the **low-tide** layout for (24,46), so in-room planning at high tide plans against
>      the wrong map; and (20,30) counts as a south-arrow warp, so never spin on or below it.
> 3. ✅ **DONE 2026-08-13 — KI-59 IS FIXED (both halves) AND GATED as `repro_impassable_dirs.py`.**
>    A/B on `VICTORY_ROAD_1F`: exit 1 → exit 0, 29/29 mismatches → 0/29, and `calculate_path` went
>    from NO-PATH-from-every-direction to `OK len=1` on the legal approaches. `MOSSDEEP_CITY`
>    collateral control byte-identical. ✅ **PROMOTED 2026-08-14 — nothing is left on this item, and drift is ZERO.**
>    ⛔ **The next sentence is STALE** (it asked for a promotion that has since happened; its drift figure is
>    not restated because the doc gate scans for one and cannot tell a quotation from a claim):
>    *(stale)* The only thing left on this item is PROMOTION, which is the USER's call. The retraction that reprioritised it follows.
>    ⛔ **RETRACTED 2026-08-13, MEASURED — "Fix KI-59 before the cavern exists" was WRONG.** The 115
>    `Impassable *` tiles in the cavern are real, but **every one has `collision=1`** and
>    `map_path.py:128` is the **`elif` of `if tile.collision != 0:` (`:118`)** — so **none of them
>    reach the buggy branch**, and the prescribed A/B on `SEAFLOOR_CAVERN_ROOM1` would have measured
>    a **zero delta**. KI-59 does **not** gate §Ch20/§Ch21. It is REAL and live on **401 of 2,658**
>    such tiles game-wide (15.1%), chiefly the **REGI TOMBS (144)**, **SHOAL CAVE (98)** and
>    **VICTORY ROAD (58)** ⇒ it is a prerequisite of the **REGI ARC (item 4)**, not of the cavern.
>    Measured by `probe_impassable_dirs.py` (NEW), with a fresh-process reverse-order control against
>    KI-73 cache poisoning. Fix specified + hazards pre-checked in `#24-impassabledirs`.
>    Superseded text: Fix KI-59 before the cavern exists — it is armed there (115 `Impassable *` tiles across Rooms 1-9). A/B on `SEAFLOOR_CAVERN_ROOM1`.
> 4. ✅ **THE PROMOTION ALREADY HAPPENED** (2026-08-12, user-approved, driven on `--build custom`).
>    Do NOT ask for it again. The line below is superseded; only the battle-policy half is still
>    the user's call. Superseded text: Two things remain the USER's call: **promoting §Ch18 + §Ch19 to `custom-pokebot/`**, and the
>    **boss/status battle-policy** decision further down.
> 5. Before building anything, skim `08-MISTAKES.md`'s last entries — five were written today and
>    three of them are about tests or gates that were green while something was broken.

1. **✅ §Ch18 IS DONE (2026-08-12) — the Mind Badge is won and Segment 18 is wired into the ladder.**
   The ladder reached **19/24** with this item (current: **20 of 24 beats**, since §Ch19). Three drivers, all PASS:
   * `--driver mossdeeptravel` → Surf Lilycove → Mossdeep, enter the gym. Anchor
     `saves/in_mossdeep_gym.ss1`.
   * `--driver mossdeepgym` → solve the statue puzzle. `at_leaders=True at=(23,8) whiteouts=0`,
     117 steps in a single plan. Anchor `saves/at_mossdeep_leaders.ss1`.
   * `--driver mossdeepbadge` → the whole chapter. `badge=True at=(23,8) controllable=True
     whiteouts=0`, `BADGE07_GET` after 754 frames. Anchor **`saves/post_mossdeep_gym.ss1`**.

   ‼ **TWO PATHS REMAIN UNEXERCISED, and neither should be described as tested.** (a) The
   executor's own `_ride_out_interruption` branch logged **zero** times — the trainer battles that
   fired were handled by the standard `TrainerApproachListener` / `BattleListener`. (b) The **real
   whiteout path**: both runs had `whiteouts=0`, so the recovery is proven only by fault injection
   (`repro_gym_whiteout_guard.py`), never by a live loss.

   ‼ **WHAT ADVERSARIAL REVIEW CAUGHT THAT THE PASSING RUN COULD NOT.** `walk_to_the_leaders`
   checked the gym map only at entry and then reasoned in gym-local coordinates forever — a
   whiteout would have had it planning gym routes from Pokémon Center coordinates — and it raised
   `RuntimeError` where the chapter catches `BotModeError`, so the re-enter-and-re-solve recovery
   **could never have fired**. Both fixed. *A green happy-path run says nothing about error paths.*

   ‼ **AND §Ch18 WAS STRANDING THE RUN** — found later the same day, by the adversarial pass for
   §Ch19, *after* §Ch18 had been driven twice, committed and reported complete. It ended on
   `(23,8)`, part of an **eleven-tile island**; `calculate_path((23,8) → (7,35))` raises, and the
   only exit is the `(21,6)` **coord event** (invisible to any warp-graph solver). Fixed with
   `leave_the_gym()` — driven, now ends in `MOSSDEEP_CITY (38,10)` — and **the acceptance test now
   requires being out of the gym**, so the stranded version would fail. *This is KI-56's rule
   violated a second time in the session in which I re-read it.*

## 📌 §Ch19 pre-build planning notes — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

§Ch19 shipped, was promoted and runs in the ladder, so its PRE-build research is history. It was
moved verbatim to the archive on 2026-08-13 to keep this current-state file inside its 900-line R3
budget — nothing was deleted. ‼ The measured hazards in it are still true and still useful if you
ever touch the Space Center: the city is cut in two until the forced cutscene runs, the 2F prompt
must be answered with **A**, completion is `VAR_MOSSDEEP_SPACE_CENTER_STATE == 3` (NOT the defeat
flag, which the Rayquaza PokeNav call clears again), and Steven must be talked to TWICE.

---

# HOW TO RUN / TEST

‼ **RESTORED 2026-08-13.** This file referenced a "HOW TO RUN / TEST" section in four places while
the section itself lived only in `28-HANDOFF-ARCHIVE.md` — so a cold-start agent following the
handoff's own instruction found nothing. The archive copy is longer and still useful for the §Ch18/
§Ch19 drivers; this is the minimum a new session needs.

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 preflight.py        # ‼ RUN THIS FIRST. git + fixtures + docs + freeze
PYTHONUTF8=1 py -3.12 run_gates.py        # THE STANDING SUITE — all 24, exits non-zero on any
                                          #   failure (~130s). ‼ The list lives in CODE, not prose — `run_gates.py` is the only
#   authority on how many gates there are. Every prose count in this file has been
#   wrong at some point.
PYTHONUTF8=1 py -3.12 run_gates.py --quick   # the 17 needing no ROM (was 10, 14, 15, 16; MEASURE)
PYTHONUTF8=1 py -3.12 run_gates.py --list    # what is in the suite
PYTHONUTF8=1 py -3.12 probe_chapter_order.py --build custom   # ‼ also check the OTHER fork

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
#   Expect as of 2026-08-16 (LATEST): 0 differing, 0 orphaned — everything is promoted, the KI-81
#   whiteout guard included. ANY file listed is unexplained drift.
#   ‼ THE FIGURE ABOVE HAS BEEN 0 -> 1 -> 0 -> 1 -> 0 IN TWO DAYS, once per promotion, so DO NOT
#     pattern-match it — RUN the command. ⛔ Earlier retractions here quoted the OLD figure
#     VERBATIM, which made the retraction byte-identical to the claim it followed and unreadable;
#     superseded figures are now DESCRIBED, never reprinted. (`audit_doc_consistency` also cannot
#     tell a quotation from a claim, so reprinting one turns this line red.)
#   ‼ DIGITS, NOT WORDS, AND CASE-INSENSITIVELY: a spelled-out "THREE" went stale here for a day,
#     and a capital "Drift is 1" survived a lowercase sweep on 2026-08-16.
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

‼ **VERIFY THE SANDBOX↔CUSTOM DRIFT ROW RATHER THAN TRUSTING IT** — `promote.py --check` is in the block above and measures it BOTH ways in seconds. ✅ **Expected as of 2026-08-16 (LATEST): 0 differing, 0 orphaned** — everything is promoted, the KI-81 whiteout guard included. ⛔ ANY file listed is unexplained. *(This line was the SURVIVOR an adversarial review caught on 2026-08-16 — a 13-site hand sweep missed it AND `audit_doc_consistency` passed over it, which is the false negative `#24-driftassertions` exists to remove.)* *(This line said "0 differing, 0 orphaned" until a Tier 2 cold-start audit found it, along with the sibling line in the command block above, still claiming 0 after three other places in this file had been corrected to 1. ALL drift statements in this file move together or not at all — ⛔ a COUNT here has been wrong twice ('three' vs 'five'; the real sweep found THIRTEEN across five files). GREP, case-insensitively, print the MATCH not the line, and require zero.)* Superseded: *"the PowerShell loop is in `28-HANDOFF-ARCHIVE.md`'s copy of this section"*, together with an older expected-count naming `modules/map_path.py`, `modules/story/early_game.py` and `plugins/custom_modes/story_mode.py` — all PROMOTED now and not part of the current drift set. ‼ **The old FIGURE is deliberately not reprinted**: `audit_doc_consistency` cannot tell a quotation from a claim, so quoting a stale count turns this line red (it did). ‼ `tools/story-dev/` is sandbox-only and is **not** part of that comparison, so the `ch20*` drivers, `probe_route128_landing.py` and `repro_party_accounting.py` do not change the count.

---

# 📚 EARLIER HANDOFF SNAPSHOTS → `28-HANDOFF-ARCHIVE.md`

Every superseded "you are here" section now lives in **`28-HANDOFF-ARCHIVE.md`** (append-only).
This file is CURRENT STATE only — if something here is no longer true, fix it here rather than
adding another banner below it.
