# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-08-14 — start at the single orientation block immediately below.
Every banner further down is HISTORY, newest first.

---
# ‼ YOU ARE HERE (2026-08-14, latest) — **THE LIVE WORK IS THE PC / PARTY ROBUSTNESS ARC. (P3) PARTY-ACCOUNTING STAGE 0 IS BUILT, GATED (#22) AND DRIVEN; NEXT IS (P3b) — ACCUMULATE `[PARTY-ACCT]` SUMMARIES FROM LONG RUNS BEFORE STAGE 1.** §Ch20 is driven END TO END and its chapter assembly is **PARKED, NOT CANCELLED**. Read this, then `14-AGENT-PLAYBOOK.md`, then NEXT ACTIONS item 0.

> ‼ **FIRST, ALWAYS:** `cd tools/story-dev` **from the repo root** (the folder holding `sandbox-pokebot/`, `custom-pokebot/` and `40cakes repo/`), then
> `PYTHONUTF8=1 py -3.12 preflight.py` and `PYTHONUTF8=1 py -3.12 run_gates.py`
> — **both must exit 0; the suite is 22 gates** (it prints its own count — believe that, not this
> line, which has been wrong at 17, 18, 19, 20 and 21 on the way here). That ritual survived the 2026-08-14
> priority redirect and is NOT part of the superseded "older framing".

> **State: `main`, clean, 22/22 gates PASS, nothing parked, nothing running.** All work pushed.
> ⚠ **Sandbox→custom drift is 2, both EXPLAINED:** `modules/party_accounting.py` (new) and
> `modules/pokemon_party.py` (its three log-only hooks) — PARTY ACCOUNTING STAGE 0, 2026-08-14.
> **Promotion is the USER's call, not asked for**; waiting is deliberate (Stage 0 is a MEASUREMENT
> barely taken). `promote.py --check` is the authority — anything ELSE listed is a reason to stop.
> **Every room of the Seafloor Cavern is DRIVEN and PASSING** — `ch20dive` → rooms 1, 2, 6, 3,
> 8, and now **9** (Archie fought, Kyogre awakened, `VAR_ROUTE128_STATE == 2`, the measured
> atoll escape executed). **What remains of §Ch20 is the CHAPTER ASSEMBLY**, not exploration.

## ✅ ROOM 9 — ARCHIE, KYOGRE, THE ATOLL ESCAPE (driven 2026-08-14) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md`

Moved for the R3 budget once the live queue became the PC/PARTY arc. ‼ **Keep only what later
work leans on:** `--driver ch20room9` PASSED twice of three runs — the cavern is driven END TO END,
Kyogre awakened, graded on **`VAR_ROUTE128_STATE == 2`** (never the Kyogre flag, which is set
BEFORE the forced warp), and the atoll escape executed (**south to `(38,23)`, Surf onto
`(38,24)`** — the landing tile has ZERO surfable neighbours, so a naive Surf reads as a HUNG LEG).
⚠ **The Archie fight is the chain's one stochastic element — 2W/1L measured**, and a LOST run prints
**no RESULT and cannot** (the whiteout drops to Manual and the generator is abandoned), which is why
the driver logs a `PRE-ARCHIE PARTY` HP line as the loss's attribution record. ⇒ the chapter must
carry a **whiteout-retry policy** and **pre-boss readiness**. ✅ The previously decomp-only claim
that the cutscene releases the player facing north is now **MEASURED (`'Up'`, twice)**.
‼ Two design rules from this room, both reusable: **release is gated on a VAR, never on "looks
controllable"** (the first `releaseall` fires while a second cutscene is still queued), and the
scene-riding loop presses **A only when a text printer is waiting, B otherwise** — A beside an NPC
STARTS a conversation (`08-MISTAKES.md`, the museum-greeter rule).
## ✅ ROOM 8 (driven 2026-08-14) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (same day, when the PC/PARTY queue replaced the Ch20 queue)

Moved for the R3 budget. ‼ **Keep only what later work leans on:** `--driver ch20room8` PASSED
twice (clean 9/9, plus a FAULT run that EXERCISED the jam-recovery handler — `recovered=True`),
and ⛔ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit). Two adversarial
passes preceded the drive and BOTH changed something: an offline refutation of the 9-push table
(verdict SURVIVES) supplied the template data that turned KI-77's window into the exact
prediction *"8 of 12 boulders visible at arrival"*, which the live run matched exactly; and a diff
review caught the recovery handler HARDCODING an arrow-warp direction instead of deriving it from
the live tile. ⇒ *the happy path cannot exercise an error path — fault-inject it on purpose.*
## 🛡 NEW SINCE THEN (2026-08-14): THE DOC CONSISTENCY LAYER — read `CLAUDE.md`'s new directive before editing any doc

**The suite is 22 gates today** (this line said 18 when `audit_doc_consistency.py` was new, then 21; `repro_box_counter_move_test.py`, `repro_pid_identity_key.py`, `audit_encoding.py` and `repro_party_accounting.py` all joined on 2026-08-14 — ‼ **`run_gates.py` is authoritative and PRINTS the count, this prose is not**). **`audit_doc_consistency.py` is NEW** — it mechanically forbids the docs
contradicting themselves or the code (gate/drift/ladder counts, queue-vs-headline driver
contradictions, cited-artifact existence; `--self-test` proves it fires). **`CLAUDE.md` now carries
the DOC CONSISTENCY LAYER directive**: pairs P1-P4 that must move together in the same commit
(banner↔queue, KI header↔body, STATE↔changelog, README↔files), Tier 1 = one independent agent per
completed item's doc diff, Tier 2 = a cold-start agent at session end — both wired into `/wrapup`
and `/checkpoint`. ‼ **Born from measurement, not caution:** two audits found ~26 instances of
stale-text-beside-correct-text, including a TRIAGE INDEX blessing a five-chapters-stale entry, an
archive move done BACKWARDS (the refuted text stayed, the correction left — KI-39), `Expect:`
lines attached to the wrong commands in THIS file, and an R6 flag gate that could not see FIVE of
the sixteen flags it existed to police (all registered now, 16/16).

## ✅ ROOM 6 (the first executed current crossing, 2026-08-13) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-14)

Moved for the R3 budget. ‼ **Keep only:** the crossing carried straight through into Room 3 and
a strict positional assert would have FAILED a perfect crossing — *assert the outcome, not the
position you expected* (now in `06-DECISIONS-LOG.md`). ⚠ Still true: the **endpoint** is proven,
not the per-slide behaviour (KI-76's correctness half). ⛔ **CORRECTED 2026-08-14:** this said the
arrow-warp branch "first executed later, in ch20room8's recovery" — **it did not.** Both there and
here the warp fired DURING the navigate (the walker holds the direction), so the derived-direction
branch was SKIPPED in both. **It remains UNEXECUTED.** Room 6 is now **n=9**.

## ✅ ROOM 3 (driven 2026-08-13) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-14)

Moved for the R3 budget. ‼ **Keep only the two reusable lessons:** the WALK route through Room 3
is 18 steps and **zero pushes** (its 7-boulder puzzle is OPTIONAL — it only dodges the trainers),
and the decomp's **single DOUBLE battle** claim (Shelly + Grunt5 collected into one fight) was
**CONFIRMED LIVE** at exactly `(6,5)` with `usable=6` asserted BEFORE the walk, so the result is
attributable. ⛔ **And my own discriminator printed a false "REFUTED"** — it counted trainer
battles RUN-WIDE, sweeping in the Room 1 grunt that is fought every run. **The instrument was
wrong, not the claim**, and it was caught only because `saw_double` was REPORTED rather than
GRADED and the raw log printed the MAP beside each judgement.

## ✅ ROOMS 1 AND 2 (driven 2026-08-13) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-14)

Both blocks moved verbatim for the R3 budget when the Room 8 banner landed. ‼ **Keep only what
later work still leans on:** (1) Room 1's A/B (`PathFindingError → OK len=6`, live objects both
arms) is what converted the Area Atlas's NO-PATH from a lower bound into a fact — and its route
had to be ARBITRATED first because our build spec's "exhaustive NORTH push" claim was **false**
(either direction is legal; upstream's SOUTH ships). *Copy upstream's ROUTE, never its CONTROL
FLOW* — our pushes go through `strength_push` (bounded, verifies by `local_id`). (2) Room 2's
headline was a correction to our own shipped source: **`FLAG_SYS_USE_STRENGTH` is cleared on
EVERY WARP** (`ClearTempFieldEventData` → `LoadMapFromWarp`); the code was always safe, the
comments were wrong. (3) **KI-77** was filed from Room 1's short object dump (2 of 5) and
corrected same-day: the despawn window is derived (20x17), the game resets a despawned boulder
to its template, the planner never under-blocks — and the window has since predicted the Room 8
arrival dump exactly (8 of 12, 2026-08-14).

## ✅ THE ATOLL EXIT (Blocker 2) — MEASURED 9/9, then DRIVEN — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md`

‼ **Keep the rule, it is the whole point:** the §Ch20 exit lands on `ROUTE128 (38,22)`, a sandbar
whose on-foot component is 71 tiles and **whose landing tile has ZERO surfable neighbours** — so a
naive "Surf from where you land" does nothing in any direction and reads as a **HUNG LEG, not a
failure**. ⇒ **step SOUTH to `(38,23)`, face Down, Surf onto `(38,24)`.** ✅ Driven 2026-08-14
(`--driver ch20room9`). ⛔ The hazard is NOT a compass direction — the atoll wraps, and 33 launch
points north DO reach open water; the trap is the **28 launches into a 41-tile CLOSED LAGOON** on
the WESTERN shore. Full measurement: `ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md`
and `tools/story-dev/probe_route128_landing.py`.
## 🧭 WHAT THE PREVIOUS SESSION DID (PATHFINDER + §Ch20 SCOPING) — still the best background


**1. KI-59 (the pathfinder's inverted `Impassable *` handling) — MEASURED, FIXED, PROVEN, GATED.**
* ⛔ **Its headline was wrong in four documents** and is retracted: *"armed in the Seafloor Cavern,
  A/B on `SEAFLOOR_CAVERN_ROOM1`"*. The handler is the `elif` of `if tile.collision != 0`, **all 115
  cavern tiles have `collision=1`, so ZERO reach it** — that A/B would have measured a zero delta and
  invited "KI-59 isn't real". Game-wide: **2,658 such tiles, 2,257 dormant, 401 (15.1%) live**,
  chiefly the **Regi tombs (144)**, **Shoal Cave (98)**, **Victory Road (58)**.
* ✅ **Fixed both halves** — the entry vector, **plus a new `PathTile.blocked_exit_directions`** for
  the decomp's exit rule, which the data model previously could not express at all.
  **A/B on `VICTORY_ROAD_1F`: `calculate_path` went from NO-PATH from EVERY direction onto all 29
  live tiles (they were invisible to the planner) to `OK len=1` on the legal ones.** Mossdeep
  collateral control byte-identical; gate **`repro_impassable_dirs.py`** is now #17.

**2. §Ch20 (Seafloor Cavern / Kyogre) — SCOPED END TO END, NOT YET BUILT.**
* `#24-ch20rename` **DONE** (`--driver ch20dive`, `probe_ch20_topology.py`), verified by re-running.
* **Area Atlas** (`probe_ch20_interior.py`): warp graph benign, all rooms reachable; **Rooms 1/2/3/5/8
  are STRENGTH-BOULDER puzzles**, Rooms 6/7 are open-water **current mazes**, Rooms 4/9 split by terrain.
* **11-leg build spec** with assertable conditions:
  `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`. ‼ It corrected **our own docs**:
  **ROCK SMASH is mandatory** (Strength alone is physically stuck in Room 1), the trigger tile is
  **`(17,42)` not `(16,42)`**, and the chapter must be graded on **`VAR_ROUTE128_STATE == 2`**, not
  the Kyogre flag — which is set *before* a forced warp into a SECOND cutscene, landing on a
  **sandbar** the bot must Surf off.
* ✅ **The current mazes are routable by our planner** (4/4 pre-registered predictions, slide model
  proven in use), so Rooms 6/7 need **no solver**.

**3. NEW ISSUES FILED: KI-74, KI-75, KI-76** (see `05-KNOWN-ISSUES.md`). KI-76's **safety half is
fixed** (bounded slide loop + `None` guards, fault-tested); its **correctness half is OPEN**.

⇒ ✅ **ALL NINE ROOMS ARE DRIVEN — the cavern is END TO END (2026-08-14).** Seven drivers,
all `ACCEPTANCE: PASS`. ⛔ **DO NOT REBUILD ANY OF THEM.**
⛔ **The line below is STALE and is kept only for its trail — it says Rooms 8 and 9 are still
planning-only, which was true for a few hours on 2026-08-13 and is not true now:**
*(stale)* ⛔ **UPDATED:** Rooms **2, 6 and 3 are now driven too** — only Rooms 8 and 9 remain planning-only.


## ⛔ NAMING CORRECTION — "§Ch21" IN THIS FILE MEANS **CHAPTER 20**. Read this before acting.

The Seafloor Cavern / Kyogre beat is **Chapter 20**, not 21:
`modules/story/chapters.py:233` — `Chapter("20", 25, "Seafloor Cavern — Kyogre", …)`, and
`:249` — `Chapter("21", 26, "Sootopolis crisis & Rayquaza", …)`. `12-STORYMODE-DESIGN.md` agrees.

✅ **THE RENAME IS DONE (2026-08-13, `#24-ch20rename`).** The artefacts are now
**`--driver ch20dive`** (class `Ch20DiveMode`), **`tools/story-dev/probe_ch20_topology.py`** and
**`ai-research-notes/2026-08-13-ch20-dive-leg-predictions.md`**. Verified after renaming by
re-running both: probe exit 0, driver `ACCEPTANCE: PASS legs=6/6`.

‼ **THE OLD NAMES SURVIVE ON PURPOSE IN `06`/`07`/`08`.** Those are append-only history and are not
rewritten, so entries dated on or before 2026-08-13 still say `--driver ch21dive` /
`probe_ch21_topology.py` / `...-ch21-dive-leg-predictions.md`. **They mean the Chapter 20
artefacts above.** Both renamed files carry a provenance header saying so.

‼ **THE UNDERLYING RULE STILL APPLIES:** the Seafloor Cavern is **Chapter 20**
(`chapters.py:233`); the genuine **Chapter 21 is Sootopolis / Rayquaza** and has not been touched.
Anywhere older text says "§Ch21" and means the cavern, read **Chapter 20**.

## â± THE 60-SECOND VERSION (if you read nothing else)
* **`reorder_party()` IS NOW DRIVEN AND PROVEN.** `--driver roster` (NEW) ran **six swaps, all
  verified by PID**, including **`RotatePokemon(i, j != 0)` — a path nothing in this project had
  ever driven.** The party-ORDER capability the Regi arc needs is real, not just planned.
* **The drive found a real defect and it is FIXED, A/B proven:** `reorder_party()` returned `True`
  with the avatar **unable to walk**. ‼ Every cheap check said it was fine — not Manual, state
  already `OVERWORLD`, start menu already closed. Only asking it to MOVE revealed it.
* **‼ 0 of 6 pre-registered predictions fired, and neither prediction pass found the real bug.**
  Both hunted the KI-38 hang family because that is where the docs point. See
  `ai-research-notes/2026-08-13-roster-drive-predictions.md` — it holds the full raw transcripts.
* **Two issues filed, both deliberately NOT fixed: KI-70** (`_rotate_lead_safely` has the same
  shape, on the hottest path in the bot — **measured, margin held, but n = 1**) and **KI-71**
  (roster.py's "dropped to MANUAL" guard is **unreachable**; `main.py:145-147` abandons the
  generator first).
* **`puzzle_solver.py` IS A RECIPE BOOK, NOT A SHORTCUT — COPY FROM IT, DO NOT DRIVE IT.**
  It is byte-identical to the upstream mirror and holds the Seafloor Cavern + Sealed Chamber +
  Regi routes. ‼ **I first wrote this up as "it already ships §Ch21 and the Regi arc" and that was
  OVERSTATED** — an adversarial pass refuted it and I verified the refutation myself:
  the Seafloor branch ends `navigate_to(ROOM9, (16,42))` → `set_manual_mode()` — ‼ **and (16,42) is
  PLAIN FLOOR that fires NOTHING; the real coord trigger is `(17,42)`, one tile EAST**
  (`Room9/map.json:124-134`, decomp-verified 2026-08-13). So upstream stops one tile short of the
  event as well as handing off. (it parks the bot on
  **Archie's own cutscene tile** and hands control to a human — no battle, no progression, no exit),
  and the Regi branches **open the door only**, ending at the tomb's EXIT warp, never at the statue.
  **What survives is still valuable**: the `dive() → navigate → surface_from_dive()` template (which
  `--driver ch20dive` copied to a 6/6 PASS), free hand-derived room coordinates, and independent
  corroboration of **KI-69**'s Emerald party order (`("Wailord", 0)` / `("Relicanth", size-1)`).
  Read `ai-research-notes/2026-08-13-puzzle-solver-already-ships-ch21-and-the-regi-arc.md` —
  **the correction is at the top.** ⛔ Never point it at a Regi tomb: its battle handling is
  `handle_encounter(encounter, enable_auto_battle=True)` (`puzzle_solver.py:99` — ‼ the kwarg is
  **`enable_auto_battle`**, corrected 2026-08-13; this line used to say `auto_battle=True`, which
  greps to nothing) and KO'ing a Regi destroys the encounter. ✅ **Re-audited 2026-08-13: the hazard
  is REAL but currently UNREACHABLE** — every Regi branch calls `set_manual_mode()` before the statue
  is engaged, and `main.py:145-146` discards the generator on the next frame. ‼ One residual: the
  shared tail presses `A` once *before* its first `yield`, so a single stray A can be emitted after
  Manual is set; on the Emerald paths the avatar is still in the OUTER room so it cannot reach a
  statue, but the R/S paths end at `(8,11)` INSIDE and that tile was not checked.
* **✅ THE FIRST DRIVEN DIVE IN THIS PROJECT — KI-68 step 1 IS DONE.** `--driver ch20dive` (NEW)
  → `ACCEPTANCE: PASS legs=6/6 at_entrance=True got_out=True can_continue=True`. Mossdeep →
  `SEAFLOOR_CAVERN_ENTRANCE (10,17)` **and back out to the open ocean**.
  ‼ **THE STATIC WARP DATA IS MISLEADING AT BOTH ENDS OF THIS CAVERN** — the way in *and* the way
  out are RUNTIME `setdivewarp`s that no warp-graph or path scan can see. **Drive it; do not read
  it.** The way out is three hops, not the one the table implies.
  ‼ **This does NOT make §Ch21 unblocked** — the run INJECTED Dive with a debug write. Acquiring a
  real Dive learner (KI-63) is still open.
* **KI-72 filed (NEW, code-verified):** `calculate_path` has never heard of
  `"Underwater Blocked Above"` / `"Seaweed No Surfacing"` — the two tile types you cannot surface
  from — so it will route a dive to a dead end. ⇒ **NEVER let the planner choose where you
  surface**; pick the tile explicitly, as upstream already does.
* **✅✅✅ KI-63 IS RESOLVED *AND NOW WIRED INTO PRODUCTION* (sandbox).** `story_mode.py`'s two HM
  call sites (Rock Smash, Surf) call the new `ensure_hm_learner_making_room`, which frees ONE slot
  and retries once — **only** on the specific "party is full" failure. New gate
  **`repro_hm_slot_wiring.py` (22/22, fault-injected)** keeps the chain connected, because the
  previous failure was *a chain of correct parts with one link missing* and nothing caught it.
  **📊 MEASURED WORTH (1,129 runs):** 20 terminal run-kills (**0.91%** excl. a reverted party-cap
  bundle), **#1 of 14 derail causes by frames per event (1,717k avg ≈ 46 min)** — 7.2% of all
  derailed lane time from 3.4% of derails, **every one five badges deep**. Rare, but it kills the
  best runs. ✅ **PROMOTED 2026-08-14 — `custom-pokebot` is NO LONGER inert.** Superseded: *that it was still inert and promotion had not been asked for*.
* *(SUPERSEDED by the bullet above — kept for its detail. ⛔ **This marker used to say the "not wired" half was still true for `custom-pokebot`; that is FALSE since the 2026-08-14 promotion — it is wired in BOTH forks and drift is ZERO.**)* **KI-63 IS RESOLVED — THE BOT ACQUIRES DIVE BY PLAYING.** `--driver divelearner` (NEW) →
  `ACCEPTANCE: PASS` **on the first drive**: freed a slot (Skitty L17 deposited), hunted and caught
  a **Marill L13** (balls 19→17), taught **Dive over Defense Curl** (the 0-power move), and
  **Zigzagoon kept Surf**. `knows_dive=True can_dive=True surf_intact=True can_continue=True`.
  **NEW production code:** `pc_trip.deposit_one_dead_weight()` + an opt-in `_needs_party_slot`
  piggyback in `heal_in_pokemon_center`.
  ‼‼ **BUT THE CAPABILITY IS PROVEN, NOT WIRED.** `_needs_party_slot` has **no setter anywhere in
  `modules/` or `plugins/`** — only the driver sets it. In a real `StoryMode` run the piggyback
  **never fires** and `ensure_hm_learner(HM08)` still raises *"the party is full"*. **Wiring
  `story_mode.py` to catch that and set the flag is the remaining work** — do not read this as
  "§Ch21 is unblocked in production". §Ch21 also still has to be BUILT, and the learner is an L13
  HM slave 36 levels below the team.
* (superseded) **THE NEXT BUILD WAS SPECIFIED AND MEASURED: KI-63.** Read
  `ai-research-notes/2026-08-13-ki63-dive-learner-acquisition-plan.md` — it has the build order,
  the pre-registered failure modes, and **two corrections to this handoff's own older text**:
  the deposit path KI-54 named (`withdraw_from_box`'s deposit block (~`modules/story/pc_trip.py:437-461`)) **cannot free a slot pre-catch**
  (it returns immediately when nothing is boxed), and `deposit_dead_weight_if_worth_it` is a
  **silent no-op** behind `POKEBOT_PC_ROTATION`. **A new narrow ungated one-deposit function is
  needed**, and **deposit-first is the wrong order.**
  ✅ Already verified safe: teaching Dive **cannot** overwrite Surf (HM slots are filtered at two
  layers), and `find_dead_weight` **exempts** the sole Surf carrier.
  ✅ **RULED 2026-08-13 (user delegated it to me): SHOAL CAVE IS NOT ADOPTED. Route 117 stays.**
  Full rationale + the three conditions that would unlock it: `06-DECISIONS-LOG.md`.
  ‼‼ **THE DECISIVE NUMBER, measured live and reproduced by me — reachable spin tiles:
  LOW 278, HIGH 0.** At high tide every candidate becomes `Shallow Water` with
  `has_encounters=False`, and **the failure mode is a SILENT STALL**: the tile is still standable,
  so `ensure_hm_learner` burns its entire 40,000-frame budget meeting nothing. KI-54's 65 encounter
  tiles at high tide are **REAL** — reproduced exactly — but form an **ISLAND** unreachable from
  the entrance warp. What was never checked was reachability, not the count.
  ⚠ **MY FIRST RATIONALE WAS PARTLY WRONG and is corrected in place** (`06-DECISIONS-LOG.md`,
  `08-MISTAKES.md`): I claimed the tooling could not see the room at all. It can —
  `get_map_data_for_current_position()` reads the **live** header. **KI-73's real defect is CACHE
  POISONING**: both paths share one `_map_layout_cache` keyed on `(group, number)`, so the first
  writer wins for the session. Still real, still unfixed, narrower than I said.
  ✅ The tide gate itself is **cheap and decomp-confirmed**: LOW = hours **03-08 and 15-20**,
  sampled **once on entry and frozen for the visit**; `get_clock_time().hours` predicts it and
  `get_event_flag("SYS_SHOAL_TIDE")` (set = HIGH) asserts it.
  ⇒ **Unlock is now short:** fix/fence **KI-73** → **live two-way sweep** one of the 278 low-tide
  tiles → ship behind the clock+flag gate in a **SEPARATE HM-ground table** (so `best_training_area`,
  which reads the same `TRAINING_GRASS` list, is untouched).
* **`#24-ballstarve`'s premise does not hold at `post_dive.ss1`** — 19 balls, $54,334 measured.
  ‼ **Not closed**: the item was filed from a mid-game Surf-era batch and may still be real there.
* **Nothing is parked. Nothing is running.** All gates exit 0 after the change. *(That said "15";
  the suite is **22** today — `run_gates.py` PRINTS the count and is authoritative, this prose is not, and this line alone has claimed 15, 17, 21 and 22.)*
* **§Ch19 is DONE and the ladder runs 20 of 24 beats.** §Ch18 + §Ch19 are **PROMOTED** to
  `custom-pokebot/` and verified by driving `--build custom`, including the real ladder.
* ⛔ **RETRACTED 2026-08-13 — three errors in one line.** It is **Chapter 20**, not 21 (see the
  naming correction above); it is **NOT BLOCKED** (Rooms 1/2/6/3 are driven and passing); and
  **KI-68 is RESOLVED and lives in `31-KNOWN-ISSUES-ARCHIVE.md`, not in `05-KNOWN-ISSUES.md`** —
  its route is driven. Superseded text: *"The next content beat (§Ch21, Seafloor Cavern) is
  BLOCKED, and the reason changed twice — read KI-68 before touching it."* It is *not* the party slot, and Dive is *not* impossible:
  the planner cannot AUTO-route a dive, so **a chapter must drive `dive()` explicitly.**
* **The REGI arc is the user's ask** — read **KI-69**. ‼ **Emerald reversed the party order:
  WAILORD first, RELICANTH last**, and the wrong order fails **silently**. ‼ **The Regi battle is
  UNRECOVERABLE** — a KO *or* a whiteout deletes the encounter permanently.
* **✅✅ KI-59 IS FIXED, BOTH HALVES, A/B PROVEN (2026-08-13, latest).** `map_path.py`'s entry vector
  now starts all-True and CLEARS `[opposite(D)]`, and a **NEW `PathTile.blocked_exit_directions`**
  carries the decomp's *exit* rule, checked on the SOURCE tile in the A* loop — `is_tile_accessible`
  is handed the NEIGHBOUR and structurally could never express it. **THE A/B on `VICTORY_ROAD_1F`:
  before, `calculate_path` returned NO-PATH from EVERY direction onto all 29 live tiles — they were
  completely invisible to the planner; after, the legal approaches return `OK len=1`.** The gate
  `repro_impassable_dirs.py` goes **exit 1 → exit 0** (29/29 mismatches → 0/29) and is now **gate
  #17**. **Collateral control:** the `MOSSDEEP_CITY` arm of `probe_ki59_routing_ab.py` is
  **byte-identical** across both arms (real production code both times, via `git stash`).
  ‼ **`probe_shoal_tide.py` was corrected in lockstep** — it had COPIED the bug, so it agreed with
  production while both were wrong — and **its numbers re-derived on the fixed model are UNCHANGED
  (LOW 278 / HIGH 0)**, so the **"Shoal Cave is NOT adopted"** ruling stands on a correct model.
  ✅ **PROMOTED 2026-08-14 — this file is in BOTH forks.** ‼ It took drift to nil AT THAT MOMENT;
  do not read it as a statement about drift TODAY, which PARTY ACCOUNTING STAGE 0 has since moved
  (see the STATE line at the top — `promote.py --check` is the only authority on the current
  figure, and no prose here should restate it).
* **‼ THE MEASUREMENT THAT PRECEDED IT: KI-59's HEADLINE WAS WRONG AND IS RETRACTED IN FOUR
  DOCS.** The inversion in `map_path.py:128-132` is **real and decomp-confirmed** — for
  `Impassable North` the shipped `[--S-]` is the *exact complement* of correct `[NE-W]`, so it
  refuses all three legal entries **and permits the one illegal one**. ⛔ **But it was NEVER a
  Seafloor Cavern blocker.** The handler is the `elif` of `if tile.collision != 0:`, and **all 115
  cavern tiles have `collision=1` ⇒ zero reach it**; the A/B four documents prescribed
  (`SEAFLOOR_CAVERN_ROOM1`) would have measured a **zero delta**. Swept over **all 518 maps**:
  **2,658 tiles, 2,257 dormant, 401 live (15.1%)**, concentrated on the **REGI TOMBS (144)**,
  **SHOAL CAVE (98)** and **VICTORY ROAD (58)**. ⇒ **KI-59 gates the REGI ARC, not the cavern.**
  New artifact `tools/story-dev/probe_impassable_dirs.py`; a fresh-process reverse-order control
  rules out KI-73 cache poisoning, and an **adversarial reviewer re-derived every number by parsing
  the `.gba` off disk with ZERO shared code** — byte-for-byte agreement. **The fix is specified and
  its hazards are pre-checked, but NOT YET WRITTEN** — see `#24-impassabledirs`. ⇒ **Run the A/B on
  `VICTORY_ROAD_1F` (29 live tiles) with a Seafloor room as the negative control**, and assert BOTH
  directions: ⚠ the counts are **static ROM layouts**, and the Regi tombs / Shoal Cave / Lilycove
  lobby all rewrite their own tiles at runtime (`setmetatile`/`setmaplayoutindex`) — **no Seafloor
  Cavern script does**, so that conclusion is unaffected. ‼ Knock-on: `probe_shoal_tide.py:364-367`
  replicates the inversion, and that probe produced the number behind the **"Shoal Cave is NOT
  adopted"** ruling.
* **Run `preflight.py` first.** Then the gate list in "HOW TO RUN / TEST".

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
| upstream | checked **2026-08-13**, still `5dd898f8` — no change. ‼ This row goes stale on a CALENDAR DAY, not on an event: if today's date is later than the one shown, **the daily check is DUE** (`git fetch upstream-pokebot`, compare against `40cakes repo/UPDATE-LOG.md`). Do not read it as satisfied. |
| restore point | **`restore/2026-08-13-session-end-ch20room3`** (annotated, pushed) — taken at the END of the §Ch20 cavern session, immediately before Room 8, which is the riskiest room in the dungeon (a boulder pushed onto `(5,3)` **permanently seals the exit**). ‼ It is also the natural rollback point if the **promotion decision** below is taken. Older: **`restore/2026-08-13-pre-ki63-promotion`** (annotated, pushed) — taken immediately BEFORE promoting KI-63's fix. Older: `restore/2026-08-13-pre-roster-promotion`, `restore/2026-08-12-pre-ch1819-promotion`. |
| sandbox ↔ custom drift | ⚠ **TWO as of 2026-08-14 (latest), both EXPLAINED and deliberately unpromoted: `modules/party_accounting.py` (new) and `modules/pokemon_party.py` (its three log-only hooks) — PARTY ACCOUNTING STAGE 0.** Promotion is the USER's call and has not been asked for; waiting is deliberate, because Stage 0 is a measurement that has so far been taken on exactly one run. ‼ **Anything else appearing in `promote.py --check` is unexplained drift and is worth stopping for.** ⛔ The rest of this cell is the PREVIOUS state and is kept for its promotion evidence — read "ZERO" below as *"zero at that moment"*, not as today's figure: ✅ **ZERO as of 2026-08-14 (earlier) — KI-78 STAGE 1 WAS PROMOTED, user-approved, and it is the first promotion executed by `tools/story-dev/promote.py` rather than by hand.** The tool refuses on a dirty tree, a missing or UNPUSHED restore point, a diverged remote, or a no-op, and it re-measures drift in BOTH directions plus byte-equality per file — it also refuses to claim the driven verification it cannot perform. Restore point **`restore/2026-08-14-pre-promotion-ki78`**. **Evidence:** drift 0 both directions, 3/3 byte-identical; **`repro_pid_identity_key.py --build custom` exit 0** and **`repro_box_counter_move_test.py --build custom` exit 0** (both ASSERT which fork they imported before testing); plus a live drive against custom. ⛔ **KI-78 is still not fully closed** — its residual cases (R2 debug-fabricated pairs, R3 corrupt box slots, R5 Frontier rentals, R6 evolved-since-capture) stay open. ‼ **MEASURE, don't trust this row** — `promote.py --check` (in HOW TO RUN / TEST) reports it BOTH ways in seconds; expect **the two PARTY ACCOUNTING STAGE 0 files named at the top of this cell, and 0 orphaned** (that superseded an earlier "0 differing, 0 orphaned"). 📚 Every earlier drift state — including the 2026-08-13/14 rounds where `map_path.py`, `early_game.py`, `story_mode.py`, `counter_hunt.py` and `pokemon_party.py` were awaiting promotion — moved to `28-HANDOFF-ARCHIVE.md` on 2026-08-14, because stacking four supersessions in one cell made a promoted file read as still pending. |
| **if stopped mid-task** | **NOTHING IS PARKED.** Everything is committed and pushed. Start at "NEXT ACTIONS". |
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

## â­ NEXT ACTIONS, IN ORDER

> **The ordered work queue** (the cold-start orientation is the ‼ YOU ARE HERE block at the top of
> this file, not here). Everything is committed and pushed; nothing is parked.
>
> 0. ‼ **THE LIVE QUEUE (updated 2026-08-14) — DO THESE FIRST; items 1-5 below are older framing.**
>    ‼ NEW STANDING RULE FOR EVERY ITEM BELOW: doc edits run Tier 0 (`lint_docs` +
>    `audit_doc_consistency`, both exit 0) before their commit, and a completed item gets a
>    Tier 1 independent review of its doc diff — see `CLAUDE.md`'s DOC CONSISTENCY LAYER.
>    ✅ **(a) and (b) ARE DONE** — Room 2 arbitrated (clean) and driven to a PASS.
>    ✅ **(c) IS OBSOLETE** — the KI-77 repro is no longer the gate on Room 8: the despawn window
>    was derived (20x17) and Room 8 (11x14) is **smaller than it**, so KI-77 cannot fire there. See
>    KI-77's corrected entry. A repro is still worth having for the LARGE rooms, but it blocks
>    nothing.
>
>    ✅ **(a2) ROOM 3 IS DONE — DRIVEN AND PASSING (`--driver ch20room3`, PASS ×2), AND THE
>    DOUBLE-BATTLE CLAIM IS CONFIRMED LIVE.** Do NOT rebuild it; see the banner at the top of this
>    file. The original item is kept below only for its route detail, which is still accurate.
>    ✅ **(a3) ROOM 8 IS DONE (2026-08-14) — `--driver ch20room8` DRIVEN AND PASSING ×2**, clean
>    first-attempt 9/9 plus a fault-injected run proving the jam-recovery handler
>    (`recovered=True attempts=2`). Do NOT rebuild it; see the 2026-08-14 banner at the top.
>    ✅ **(a4) ROOM 9 IS DONE (2026-08-14) — `--driver ch20room9` DRIVEN, `ACCEPTANCE: PASS` ×2
>    (runs 1 & 3), the cavern is END-TO-END.** Do NOT rebuild it; see the NEWEST banner at the
>    top. ⚠ Run 2 LOST the Archie fight (2W/1L measured; the party arrives chipped, no heal in
>    the cavern) — that is CHAPTER-DESIGN input, not a driver defect. The facing-north claim is
>    now MEASURED (`'Up'` ×2).
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
>    ✅ **(P3) THE PARTY-ACCOUNTING SPLIT, STAGE 0 — BUILT, GATED (#22), AND DRIVEN (2026-08-14).**
>    `modules/party_accounting.py` adds the readers (**A** `gPlayerPartyCount`, per-slot occupancy)
>    and a divergence log: **HOLE** (empty slot below A — what makes B < A), **OVERFLOW** (A > 6)
>    and **INVALID**, all observed EXACTLY from `get_party()`'s own branches, plus **STALE**
>    (occupied slot at or past A), ⛔ **SAMPLED 1-in-300, not exhaustive** — read the sample count
>    printed beside it, never the bare zero.
>    ✅ **It wires NO call site, and that is ASSERTED by the gate, not merely intended**, along
>    with a byte-identical observer-on/off A/B on four fixtures, silence on a healthy party, and a
>    fault-injected observer that must break the LOG and never the read. Three source-level
>    injections were run and the gate failed each (4, 2 and 15 checks).
>    ‼ Index/menu-cursor call sites MUST STILL stay on B — if A > B an index derived from A is out
>    of range for the list the bot holds, most likely MID-BATTLE.
>    🔜 **(P3b) THE MEASUREMENT IS THE POINT, AND IT IS NOT FINISHED.** The one `--driver ch20dive`
>    run so far reported **25,523 recomputes / 86 scans / NO DIVERGENCE** — not a population.
>    ⛔ **Do NOT start Stage 1 (re-pointing the ~35 capacity-shaped call sites at A) until several
>    LONG runs have reported their `[PARTY-ACCT]` summaries**, printed by `story_harness.py` at the
>    end of every drive. A "no divergence" line from one run answers nothing, and it says so.
>    🔜 **(P4) The END-TO-END repro of the user's actual scenario** — Nincada evolves into a full
>    party → counter hunt → heal. **The honest gap: P1 is proven by a fabricated fixture, not by
>    reality.**
>    🔜 **(P5) The CATCH POLICY round** — the user CALLED it (`06-DECISIONS-LOG` 2026-08-14,
>    rulings A-D): a **LIVING DEX**, per-run, breadth with depth as the payoff. Gate lifted on
>    `#24-organicteam`. ⛔ The RARE leg is blocked on `#24-rarepredicate`, whose fix is now
>    specified (HM-gating + location count, NOT warp depth — the user's Bagon/Feebas reasoning).
>    Trade evolutions are a SANCTIONED non-faithful deviation with four conditions attached.
>    🔜 **(P6) TRAINING-AREA MAPS per gym AND per boss** — measured hole: Norman's configured patch
>    is **L3-5** against a boss band of **L27-31**, and **Winona has no patch configured at all**,
>    so the whole relocation machinery is skipped for her.
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
>    ✅ **(d) DONE 2026-08-14 — the user approved it and everything was PROMOTED; drift is ZERO.**
>    ⛔ **Stale text follows, kept only for the trail:**
>    *(stale)* **STILL THE USER'S CALL, NOT MINE:** promoting the drifted files to
>    `custom-pokebot/`. Nothing here changes that.
> 1. **Run `preflight.py`**, then the **22**-gate suite in "HOW TO RUN / TEST" (all exit 0
>    2026-08-14; it has said 17, 18, 19, 20 and 21 on its way to **22** — `run_gates.py` is authoritative, never this prose), and the drift check below.
>    ✅ **EXPECT EXACTLY 2, AND BOTH ARE NAMED:** `modules/party_accounting.py` and
>    `modules/pokemon_party.py` — PARTY ACCOUNTING STAGE 0, deliberately unpromoted (the user has
>    not been asked, and Stage 0 is a measurement that has barely been taken). ‼ Anything ELSE in
>    that list is unexplained drift and is worth stopping for. Superseded text follows, which would send a cold session to investigate a non-problem:
>    ⛔ *(superseded)* **CORRECTED — EXPECT EXACTLY 3**, not 2: `modules/map_path.py`
>    joined the list with KI-59's fix. The stale "2" below would have made a deliberate, gated,
>    A/B-proven change read as *unexplained drift*. Superseded text: **EXPECT EXACTLY 2:**
>    `modules/story/early_game.py` and `plugins/custom_modes/story_mode.py` — KI-63's **production
>    wiring**, driven to a PASS but **NOT promoted**. (Do NOT expect `roster.py`/`menuing.py`:
>    those were PROMOTED on 2026-08-13 and drift on them is now zero.)
>
> 1b. ✅ **DONE — the KI-63 wiring was PROMOTED on 2026-08-14 and is in BOTH forks. There is no
>    decision left here** (‼ not a claim about today's drift figure — see item 1). Its superseded
>    "first decision for the user" text, and the measured worth behind it (20 terminal run-kills in
>    1,129 runs, #1 of 14 derail causes by frames), moved to `28-HANDOFF-ARCHIVE.md` 2026-08-14.
>
> 2. ✅ **DONE 2026-08-13 — `reorder_party()` IS DRIVEN.** `--driver roster` exists and passes.
>    Six swaps, all verified by PID, including the never-driven `RotatePokemon(i, j != 0)`.
>    **Both unknowns this item asked about are now SETTLED by the trace:**
>    * *the exit-menu timing gap* — **REAL, and it was a bug.** The party menu's last act is
>      re-showing the Start menu (`Task_ShowStartMenu` still live at f660 of a 662-frame call), so
>      `reorder_party` used to return `True` while the avatar could not walk. **Fixed** with a
>      `swapped`-gated `_settle()`; A/B proven (`moved=False`→`True`, FAIL→PASS, and phase 3 costs
>      0 frames in BOTH arms — the control arm proving the gate does not over-fire).
>    * *the stale-cursor read* — **the mechanism is real but did NOT fire.** `gPartyMenu.slot_id`
>      is **not reset between menu sessions**: the tracer read a stale `slot_id=2` on the overworld
>      before the menu had opened, and `navigate_to_mon:520-524` computes its scroll direction from
>      exactly that global. It happened to be re-read live in time. **This is luck, not safety** —
>      re-check it first if a future roster drive ever mis-swaps.
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
> 3. **‼‼ READ KI-68 BEFORE TOUCHING §Ch21 — AND DO NOT READ "NOT ROUTABLE" AS "NOT POSSIBLE".**
>    The party slot is **not** the blocker. `WaypointAction.Dive`/`Emerge` are declared and assigned
>    **nowhere**, and `warp_graph.py:342` says the exclusion is **on purpose** — a dive is not a warp
>    event, so `calculate_path` was never going to emit one. **But `dive()` already exists and
>    works.** ⇒ **The fix is a CHAPTER that drives the transition**, exactly like §Ch18's coord-event
>    exit and Steven's bottom-row door — *not* a planner rewrite.
>    ⛔ *(STALE — this was DONE: `--driver ch20dive` → `ACCEPTANCE: PASS legs=6/6`, and all nine
>    cavern rooms have since been driven. Do not re-do it.)* It used to command *"DO THIS FIRST:
>    inject Dive via `debug_utilities.py:611` and drive Route 128 → Seafloor Cavern"* — DONE, and
>    **the ⛔ ends HERE**, at the end of this sentence.
>    ‼ **LIVE, not stale:** if a hunting ground is ever added, **NOT to `TRAINING_GRASS`** — measured,
>    a Shoal Cave row becomes the highest band and flips `best_training_area` for every team ~L30 up.
>
> 3b. ⛔⛔ **THE ORDER CHANGED 2026-08-13 — READ `06-DECISIONS-LOG.md`'s entry before item 4.**
>    The Regi arc is **NOT** next, and *"KI-59 blocked it, I fixed it, so build it"* was **REFUTED
>    three ways**: the tombs walk their laps with `follow_path` (**"no collision checking"**), their
>    144 tiles describe a room `setmetatile` rewrites at runtime, and upstream ships a working Regi
>    solver **against the un-fixed inversion**. ‼ That was the SAME error logged that morning —
>    counting tiles without checking what REACHES them — made twice in one day.
>    **DO, IN THIS ORDER:**
>    **(i) `#24-ch20rename`** — small, safe, start-of-session. `--driver ch20dive`,
>    `probe_ch20_topology.py` and two note filenames are misnomers pinned to **Chapter 20**.
>    **(i) IS DONE 2026-08-13** — renamed and verified by RE-RUNNING both (`probe_ch20_topology.py`
>    exit 0; `--driver ch20dive` → `ACCEPTANCE: PASS legs=6/6`).
>    **(ii) §Ch20 — THE AREA ATLAS IS BUILT (2026-08-13). ‼ IT IS A STRENGTH-BOULDER DUNGEON, not a
>    route.** `probe_ch20_interior.py` (NEW) measured all ten cavern maps: **the warp graph is
>    benign — every room is reachable from the entrance by warps alone** — and the difficulty is
>    inside the rooms. Components over walkable tiles, then with object tiles removed:
>    ROOM1 2→5 · **ROOM2 1→6** · ROOM3 1→5 · **ROOM4 5→5 (split by TERRAIN, not objects)** ·
>    ROOM5 1→5 · **ROOM6 1→1 and ROOM7 1→1 (open water, elev 1, ZERO objects — these need SURF,
>    not Strength)** · **ROOM8 3→7 (12 objects in 48 tiles)** · ROOM9 2→2 (terrain; Archie/Kyogre).
>    ⛔ *(STALE — and this ⛔ covers everything to the END OF THIS BULLET: the interior WAS
>    re-measured from inside, all nine rooms are driven, do NOT re-drive.)* It used to command
>    *"drive INTO the cavern and re-measure with LIVE objects"* — that is DONE. ‼ **The LESSON
>    survives:** the atlas was read from Mossdeep, and `is_tile_accessible` blocks every tile whose
>    object is not in `active_objects`, so a remote read's routing is a **LOWER BOUND** and its
>    NO-PATHs are an artifact, not map facts. (§Ch19 hit this trap too; probe output section 3b.)
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
> 4. **The REGI arc (user-requested) — read KI-69 ‼ AND ITS NEW STUB MARKER.**
>    ⛔ **REGICE IS NOT A TIMED WAIT** — R/S's wait function is an empty stub; Emerald wants a
>    **36-tile perimeter lap in ONE visit** ending exactly on `(8,21)`, reset by any map transition
>    and by one wrong tile. Full ground truth:
>    `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md`. ‼ **WAILORD first, RELICANTH last** (Emerald
>    reversed it; the wrong order fails silently). ‼ **The Regi battle is UNRECOVERABLE** — a KO *or*
>    a whiteout deletes the encounter; only fleeing is safe. Phase A is measured: we have Go-Goggles,
>    HM08, Surf and Rock Smash; we have **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or
>    Flash. **Relicanth is underwater-only, so Dive (item 3) is upstream of the whole arc.**
>
> 5. Older framing below, kept for its measurements — its CONCLUSION is superseded by items 3-4:

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
PYTHONUTF8=1 py -3.12 run_gates.py        # THE STANDING SUITE — all 22, exits non-zero on any
                                          #   failure (~130s). ‼ The list lives in CODE, not prose — `run_gates.py` is the only
#   authority on how many gates there are. Every prose count in this file has been
#   wrong at some point.
PYTHONUTF8=1 py -3.12 run_gates.py --quick   # the 15 needing no ROM (was 10, then 14; MEASURE)
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

# --- PARTY ACCOUNTING STAGE 0 — the readers, the divergence log, and its gate ---
PYTHONUTF8=1 py -3.12 repro_party_accounting.py     # PARTY ACCOUNTING STAGE 0 (gate #22)
#   Expect: `ALL 33 CHECKS PASS`, exit 0. No emulator, ~1s. ‼ It PRINTS its own check count —
#     believe that line, not this one. Takes `--build custom` and
#     ASSERTS which fork it imported. It drives the REAL get_party() over FABRICATED gPlayerParty
#     memory, so it tests the shipped reader, not a copy. ‼ The CONTROLS are the point: a healthy
#     party must record NOTHING, and get_party() must be byte-identical with the observer stubbed.
#   ‼ THE MEASUREMENT IT EXISTS FOR IS NOT IN THE GATE — it is the `[PARTY-ACCT] STAGE 0 SUMMARY`
#     that every `story_harness.py` drive now prints at the end. Collect those from LONG runs.

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
#   Expect as of 2026-08-14 (later): exactly TWO differing — modules/party_accounting.py and
#     modules/pokemon_party.py, PARTY ACCOUNTING STAGE 0, unpromoted on purpose — and 0 orphaned.
#     (Superseded: "0 differing, 0 orphaned. Everything has been PROMOTED.")
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
`tools/story-dev/harness_sandbox.log`.

‼ **VERIFY THE SANDBOX↔CUSTOM DRIFT ROW RATHER THAN TRUSTING IT** — `promote.py --check` is in the block above and measures it BOTH ways in seconds. ✅ **Expected as of 2026-08-14 (later): exactly two, `modules/party_accounting.py` and `modules/pokemon_party.py` — PARTY ACCOUNTING STAGE 0, unpromoted on purpose.** Superseded: *"the PowerShell loop is in `28-HANDOFF-ARCHIVE.md`'s copy of this section. Expected as of 2026-08-13: exactly 3"* (`modules/map_path.py`, `modules/story/early_game.py`, `plugins/custom_modes/story_mode.py`) — those three are all PROMOTED now and are not part of the current drift set. ‼ `tools/story-dev/` is sandbox-only and is **not** part of that comparison, so the `ch20*` drivers, `probe_route128_landing.py` and `repro_party_accounting.py` do not change the count.

---

# 📚 EARLIER HANDOFF SNAPSHOTS → `28-HANDOFF-ARCHIVE.md`

Every superseded "you are here" section now lives in **`28-HANDOFF-ARCHIVE.md`** (append-only).
This file is CURRENT STATE only — if something here is no longer true, fix it here rather than
adding another banner below it.
