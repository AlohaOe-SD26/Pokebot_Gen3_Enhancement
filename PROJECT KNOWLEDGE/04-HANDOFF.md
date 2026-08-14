# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-08-13 — start at the single orientation block immediately below.
Every banner further down is HISTORY, newest first.

---
# ‼ YOU ARE HERE — the **§Ch20 CAVERN-INTERIOR** session (2026-08-13, latest): Rooms 1 AND 2 are driven. Read this, then `14-AGENT-PLAYBOOK.md`.

> **State: `main`, clean, 17/17 gates PASS, nothing parked, nothing running.** Three commits
> this session, all pushed. **Rooms 1 and 2 of the Seafloor Cavern are DRIVEN and PASSING**;
> Rooms 3-9 are planning only.
> ‼ `stash@{0}` exists **on purpose** — see the STATE table; **never drop it.**

## 🚩 THE BOT IS INSIDE THE SEAFLOOR CAVERN AND THROUGH ROOM 1 — driven, first attempt

**`--driver ch20room1` → `ACCEPTANCE: PASS`.** Mossdeep → dive → `SEAFLOOR_CAVERN_ENTRANCE (10,17)`
→ `ROOM1 (5,18)` → Rock Smash + two Strength pushes → **`ROOM2 (10,7)`, controllable, real step
taken.** Two trainer battles fired on the way and were ridden out.

**‼ THE RESULT IS THE A/B, NOT THE ARRIVAL.** Same call, same target, live objects on both arms:

    A/B BEFORE  (5,18) -> (11,11)   PathFindingError      <- the corridor really IS sealed
    A/B AFTER   (5,11) -> (11,11)   OK len=6              <- and the smash+push really opens it

That converts `probe_ch20_interior.py`'s Room 1 NO-PATH from a **LOWER BOUND** (it was measured from
Mossdeep, with no cavern objects loaded) into a **measured fact**. A one-armed "it worked" could not
have ruled out "the corridor was open all along".

**‼ THE ROUTE HAD TO BE ARBITRATED BEFORE IT COULD BE DRIVEN — OUR OWN BUILD SPEC WAS WRONG.**
`ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md` claims an **exhaustive** search
proves Room 1's `(5,11)` boulder must be pushed **NORTH**. The decomp *and* our own ROM reader both
say `(5,10)` and `(5,12)` are `collision=0 elevation=3 'Cave'` ⇒ **either direction is legal, the
uniqueness claim is false, the search was not exhaustive.** Upstream's **SOUTH** push
(`puzzle_solver.py:373`) is what ships, and it was then confirmed live.
⇒ ‼ **THAT SPEC'S ROOM 2 AND ROOM 8 "EXHAUSTIVE" SEQUENCES ARE NOW UNAUDITED.** Arbitrate each
against the decomp **and** upstream's Emerald branch (`puzzle_solver.py:395-454`) before driving it.
**Standing rule from `06-DECISIONS-LOG.md`: copy upstream's ROUTE, never upstream's CONTROL FLOW** —
its second push is a bare `walk_one_tile`, unbounded by its own docstring and judging nothing; ours
go through `strength_push`, which is bounded and verifies the boulder **by `local_id`**.

**‼ NEW ISSUE — KI-77, and it was found by the ONE prediction that FAILED.** On arrival the live
object dump returned **2 of the map's 5** objects; the rock and both grunts were absent yet
demonstrably present. **`get_map_objects()` is a CAMERA-RANGE WINDOW, not a map inventory** — and
`map_path.py:811-818/844-853/861` builds the planner's whole object model from it. ⇒ **after a push,
walking out of range re-blocks the tile the boulder LEFT and frees the tile it now OCCUPIES.**
Benign in Room 1 (the route never revisits `(5,11)`), **armed in Room 8's nine pushes in 48 tiles.**
Code-verified, deliberately NOT fixed — the repro comes first.

**Artefacts:** `--driver ch20room1` (new), pre-registered predictions + full transcript in
`ai-research-notes/2026-08-13-ch20-room1-drive-predictions.md` (6 of 7 held).
**Refactor, proven neutral:** `Ch20DiveMode`'s fixture and legs 1-5 are now `_inject_dive_fixture()`
/ `_ingress()` so the new driver **reuses** the proven ingress instead of copying it — re-running
`--driver ch20dive` gave `legs=6/6 … ACCEPTANCE: PASS`, matching its documented prior result.

## 🚩 …AND THEN THROUGH ROOM 2, INTO THE ROOM 6 CURRENT MAZE (same session, later)

**`--driver ch20room2` → `ACCEPTANCE: PASS`, first drive, 10 of 10 pre-registered predictions.**
It re-solves Room 1 from scratch every run (the `FLAG_TEMP_*` objects respawn on every map load), so
**Room 1 is now n=3.** Route 2 was arbitrated first and, unlike Room 1's, came out **clean**:
decomp + our own ROM agree on all 8 objects and upstream `puzzle_solver.py:395-402` is correct step
for step. Smash `(8,7)` → **exactly three** north pushes of boulder `id 4` → `(6,1)` →
`SEAFLOOR_CAVERN_ROOM6 (11,21)`.

**‼ THE HEADLINE IS A CORRECTION TO OUR OWN SHIPPED SOURCE.**
`STRENGTH-FLAG after the ROOM1→ROOM2 warp: **False**`. `modules/story/early_game.py` said in two
places that `FLAG_SYS_USE_STRENGTH` is *"NEVER CLEARED … once per SAVE, not once per map"*. It is
cleared on **EVERY WARP** (`ClearTempFieldEventData` → `LoadMapFromWarp`). The old claim rested on
"a decomp-wide search for `clearflag`" — the **script macro**; the clear is the C function
`FlagClear`, so that search could never have found it. ✅ **The code was always safe** —
`strength_push` re-checks per call — so this was **load-bearing documentation on top of correct
code**, invisible to every gate, and lethal only to the next author who deletes the re-check as
redundant. Both comments corrected. ⇒ **drift is STILL EXACTLY 3** — `early_game.py` was already
one of the three, so this adds no new file. (Measured with the loop in HOW TO RUN / TEST.)

**The three-point A/B earned its keep:** `M1 NO-PATH → M2 NO-PATH → M3 OK` attributes the opening to
the **pushes**, not the smash. A two-point A/B would have accepted "the rock was the only obstacle",
which is false.

**Room 6's current model survives contact with the live room:** `calculate_path((11,21) → (4,1))` =
`OK len=13` measured from INSIDE — the same 13 waypoints `probe_ch20_currents.py` predicted from
outside. ⚠ **Still a PLAN, not a walk.** No current has ever been executed (KI-76).

**‼ KI-77 WAS CORRECTED THE SAME DAY IT WAS FILED, TWICE OVER.** The despawn window is now derived
(`x ∈ [px-9,px+10]`, `y ∈ [py-7,py+9]` — 20x17) and **predicts our live Room 1 dump 5/5 on the
boundary**. So (a) **"armed in Room 8" is REFUTED** — Room 8 is 11x14, *smaller than the window*;
the rooms at risk are the **large** ones. And (b) the game **physically resets a pushed boulder to
its template tile when it despawns**, so the planner is **fail-safe and never under-blocks** —
fixing it would have been fixing the wrong thing.

## ⚠ THE ONE THAT WILL STRAND THE RUN, AND IT IS UNTESTED — read before building §Ch20's exit

`ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md` holds four decomp blockers. Three
are still untested; **Blocker 2 is the dangerous one.** The chapter's forced exit lands on
`ROUTE128 (38,22)`, a shallow-water sandbar, and **releases the player facing NORTH** — and north is
a **41-tile CLOSED LAGOON** on a map with `"allow_escaping": false`. The bot also cannot Surf from
the landing tile at all (all four neighbours are `MB_SHALLOW_WATER`, which is not surfable).
⇒ **Step SOUTH to `(38,23)`, face south, Surf onto `(38,24)`.** The trap points the way the camera
does, and three chapters have already shipped stranded.

⇒ **NEXT: ROOM 3 — arbitrate it first.** It is *not* the walk the spec calls it: it has a
**7-boulder puzzle the spec omits entirely**, its two trainers are unavoidable on the push-free
line, and it is the one room where a boulder can be parked on the `(9,13)` retreat warp. See
"NEXT ACTIONS".

---

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

⇒ ✅ **THAT LIVE DRIVE HAPPENED — see the block at the top of this file.** Room 1 is driven and the
Area Atlas's Room 1 lower bound is now a measured fact. Rooms 2-9 are still planning only.


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

## ⏱ THE 60-SECOND VERSION (if you read nothing else)
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
  best runs. ⛔ **`custom-pokebot` is still INERT — promotion NOT asked for.**
* *(SUPERSEDED by the bullet above — kept for its detail; the "not wired" half is NO LONGER TRUE for sandbox, only for `custom-pokebot`.)* **KI-63 IS RESOLVED — THE BOT ACQUIRES DIVE BY PLAYING.** `--driver divelearner` (NEW) →
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
* **Nothing is parked. Nothing is running.** All 15 gates exit 0 after the change.
* **§Ch19 is DONE and the ladder runs 20 of 24 beats.** §Ch18 + §Ch19 are **PROMOTED** to
  `custom-pokebot/` and verified by driving `--build custom`, including the real ladder.
* **The next content beat (§Ch21, Seafloor Cavern) is BLOCKED, and the reason changed twice** —
  read **KI-68** before touching it. It is *not* the party slot, and Dive is *not* impossible:
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
  ⚠ **This raises sandbox↔custom drift to 3. Promotion is the USER's call and has not been asked.**
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
| ‼ is code frozen? | **No.** Nothing is running. |
| party ORDER | ✅ **PROVEN 2026-08-13.** `--driver roster` from `saves/post_dive.ss1` → `phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True ACCEPTANCE: PASS`. Raw transcripts (both A/B arms) in `ai-research-notes/2026-08-13-roster-drive-predictions.md`. ‼ The **deposit/withdraw** half of `#24-roster` is still open. |
| upstream | checked **2026-08-13**, still `5dd898f8` — no change. ‼ This row goes stale on a CALENDAR DAY, not on an event: if today's date is later than the one shown, **the daily check is DUE** (`git fetch upstream-pokebot`, compare against `40cakes repo/UPDATE-LOG.md`). Do not read it as satisfied. |
| restore point | **`restore/2026-08-13-pre-ki63-promotion`** (annotated, pushed) — taken immediately BEFORE promoting KI-63's fix. Older: `restore/2026-08-13-pre-roster-promotion`, `restore/2026-08-12-pre-ch1819-promotion`. |
| sandbox ↔ custom drift | ⚠ **EXACTLY 3 as of 2026-08-13 (latest).** ‼ **`modules/map_path.py` is the NEW third** — KI-59's fix (entry inversion + the new `blocked_exit_directions` exit half), A/B proven on `VICTORY_ROAD_1F` with a byte-identical `MOSSDEEP_CITY` collateral control, gated by `repro_impassable_dirs.py`. **NOT promoted — the USER's call, not asked for.** ⛔ Until it is, `custom-pokebot`'s planner still cannot see the 401 live `Impassable *` tiles (Regi tombs 144, Shoal Cave 98, Victory Road 58). The other two, unchanged, described next: **EXACTLY 2, both deliberate and sandbox-only (2026-08-13, earlier):** `modules/story/early_game.py` (the new `ensure_hm_learner_making_room`) and `plugins/custom_modes/story_mode.py` (both HM call sites wired to it). **This is KI-63's PRODUCTION WIRING, driven to a PASS but NOT promoted — promotion has not been asked for.** ⛔ Until it is, `custom-pokebot`'s copy of the KI-63 fix is **INERT**: it reads `_needs_party_slot` and nothing there sets it. Earlier today drift was ZERO twice (`restore/2026-08-13-pre-roster-promotion`, `restore/2026-08-13-pre-ki63-promotion`). ‼ **MEASURE, don't trust this row** — the loop is below in "HOW TO RUN / TEST". |
| **if stopped mid-task** | **NOTHING IS PARKED.** Everything is committed and pushed. Start at "NEXT ACTIONS". |
| ‼ **`git stash` — KEPT ON PURPOSE (USER RULING 2026-08-13)** | **`stash@{0}` EXISTS, IS NOT YOURS, AND IS KEPT AS A RECORD. ⛔ DO NOT DROP IT.** `WIP on main: e0f723e4` (2026-07-24) — a 14-line Fortree Gym "only ride out a scene that exists" guard. Its substance is ALREADY in today's `early_game.py` (reimplemented during the rotating-gate rewrite), so it is functionally superseded — **and the user ruled that a superseded stash is still a RECORD and dropping it is a destructive act that buys nothing** (`06-DECISIONS-LOG.md`). ⛔ **Standing rule: never `git stash drop` / `clear` / `pop` in this repo.** `pop` is separately banned because it mutates a GLOBAL stack — that is how this stash was disturbed in the first place (`08-MISTAKES.md`). To read it: `git stash show -p "stash@{0}"`, and apply by hand if ever needed. ‼ A stash is invisible to `git status` and to the kit's sync check, which is how it sat unnoticed for three weeks — so `git stash list` belongs in the session-start ritual, to SEE it, not to clear it. |

## ✅ WHAT SHIPPED IN THE LATEST SESSION (§Ch19 + promotion + roster)
1. **§Ch19 built and driven end-to-end** — Space Center multi battle **and** HM08 Dive, wired as
   Segment 19. Ladder **19 → 20 of 24**. Acceptance includes "and the bot can continue".
2. **§Ch18 + §Ch19 PROMOTED** to `custom-pokebot/`, verified by driving `--build custom` three ways.
3. **KI-64 fixed** (the multi-battle faint replacer would have sent out STEVEN's Pokémon) — ‼ and my
   first fix was **wrong twice**: dead code on the story path, and a positional cut that inverted
   itself once the party menu permutes `gPlayerParty`. Now keyed on **original trainer ID**.
4. **KI-67 CLOSED, both halves** — the whiteout abort no longer burns a chapter's retry budget or
   launders itself into a fabricated diagnosis, and the harness finally mirrors production.
   **First driven whiteout recovery in this project** (frame deltas +7,789 / +7,087).
5. **Two blind gates fixed:** the flag audit was checking **2 files** and could not see names behind
   a module constant (i.e. blindest at the completion markers); and **pyflakes had never been run** —
   it found a `NameError` on the Magma Hideout's *success* path.
6. **New: `modules/story/roster.py`** (party reorder) + the `PartyMenuExit` freeze fix.
7. **Regi arc researched and Phase A measured** (KI-69) at the user's request.

### 📌 THE OLDER SESSION'S SUMMARY (§Ch16-§Ch18) FOLLOWS BELOW — it is HISTORY, not current state.
The story ladder went **16 → 19 of 24 beats**.

‼ **§Ch18 (items 5, 6 and the block below) is COMMITTED AND PUSHED BUT *NOT* PROMOTED to
`custom-pokebot/`.** Items 1-4 below were promoted on 2026-08-12 with the user's approval, verified
by driving `--build custom` to a frame-identical PASS. **§Ch18 has had no such approval and no such
verification — the sandbox↔custom drift row above is stale the moment you read it.** Promotion is
the user's call, and it needs its own driven check in `custom-pokebot`, not a diff.

1. **KI-56 FIXED — §Ch15 now LEAVES the Magma Hideout.** It used to pass its own binary test on
   runs that ended permanently stranded. No walk-out exists (18 of 20 warp-graph nodes reachable,
   the exit not among them); fixed with the **Escape Rope the dungeon itself provides**. Driven
   PASS, landing on the exact tile predicted from `escapeWarp` beforehand.
2. **KI-57 FIXED — §Ch16 (Slateport) COMPLETE.** ‼ Beating Maxie *parks Capt. Stern on the only
   tile touching the harbor door*: Ch15's own success spawns Ch16's blocker. The answer was not a
   route but a conversation — talking to him `warp`s the player inside. Driven PASS x3.
3. **§Ch17 (Lilycove Aqua Hideout) BUILT + the MASTER BALL.** An 18-hop warp-panel maze solved from
   the ROM warp table. ‼ The Master Ball can't be taken directly — both free neighbours are
   unreachable — so the route takes the **Nugget** first and steps onto the tile it vacates. Driven
   PASS with `master_balls=1`.
4. **The Ch16 haul whiteout FIXED** (`whiteouts` 1 → 0, and faster). The anchor hands the chapter a
   party at **8.8% HP, 5 of 6 fainted**, and the chapter was passing only *because a whiteout
   heals*. Heal stops are now nearest-first.
5. **§Ch18 leg 1** — `--driver mossdeeptravel` Surfs Lilycove → Mossdeep and enters the gym
   (PASS, `whiteouts=0`), capturing `saves/in_mossdeep_gym.ss1`.
6. **KI-58 RESOLVED — the Mossdeep Gym is a ROTATING-TILE STATUE PUZZLE**, not a maze (see below).
7. **KI-59 + KI-60 filed** — two latent bugs in the SHARED pathfinder, code-verified, deliberately
   **not** fixed. `#24-impassabledirs`, `#24-pathsourcecheck`.
8. **`#24-grounditems` groundwork** — `collect_item_ball()` is now shared by three callers;
   `#24-npcgifts` and `#24-masterball` added on your direction.
9. **New tools:** `probe_warp_maze.py` (generalised, self-checks against a DRIVEN route),
   `probe_gym_bruteforce.py` (model-free walker), `probe_gym_components.py`, `probe_escape_warp.py`,
   `probe_hideout_warp_graph.py`, `probe_slateport_harbor_map.py`, `repro_hideout_exit.py`.
   `probe_anchor_inventory.py` now prints **party HP** — it immediately flagged three anchors as
   "cannot survive a journey".

## ✅ §Ch18 (Mossdeep Gym + the statue puzzle) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

Shipped, wired as Segment 18, promoted. ‼ **Keep only the lesson:** the gym is a **rotating-tile
statue puzzle**, and four of our own instruments agreed it had no route because all four modelled it
as *walk + warp* and it has a **third movement primitive**. ⇒ *When N of your own instruments agree
on something impossible, they share a missing primitive.* It also **shipped stranded on an
eleven-tile island** while passing `badge + controllable`.
## ‼ THE TWO THINGS THAT MATTER MOST FROM THIS SESSION

**1. When N of your own instruments agree on something impossible, they share a missing primitive.**
Four instruments agreed the Mossdeep Gym had no route to its own leaders. All four modelled it as
*walk + warp*; the gym has a **third movement primitive** — floor switches that relocate 21 statues
and nine trainers. Even the model-free brute-force walker was wrong, because it *changed the map
while exploring it*. Five parallel Claude agents found it; the explicitly ADVERSARIAL one cracked it.

**2. ‼ EVERY DEFECT THAT MATTERED THIS SESSION WAS FOUND BY AN ADVERSARIAL AGENT, NOT BY A TEST.**
Three times: the statue model (caught by a validation gate I only built because the rule says to),
the whiteout path, and §Ch18 stranding the run. In each case my own runs were **green** — the
happy path cannot exercise an error path, and an acceptance test written by the same person who
wrote the code inherits the same blind spot. ⇒ *Spend the agents on REFUTING finished work, not
only on researching new work.* And: **write the predicted failure down BEFORE the run** — the
§Ch19 hazard checks did this and 3/3 held, which is how two traps got designed out instead of
debugged.

## ‼‼ THE BATCH RESULT — one thing resolved, one thing NOT
**RESOLVED — the status tax is real:** incapacitated turns lost **960/2,945 = 32.6%** vs a clean
control of **1,259/33,017 = 3.8%**. **8.5×, z = +62.2**, over 47,789 turns from 36 independent lane
logs. ‼ My earlier n=2 figure of 64.3% was **~2× too high** — one dungeon fight is not a rate.

**NOT RESOLVED — `#24-teachmsgstall` has no production effect and is REOPENED:**
teach success **38/47 (80.9%)** vs **38/42 (90.5%)** pre-fix, **z = −1.28**; `post_select=exhausted`
**8/85** vs **3/80**, **z = +1.46**; and the new `already-advanced` exit fired **ZERO** times in 85
teaches. The one-frame window was real but was **not the dominant production cause**. The fix stays
(it closes a real hole and costs nothing); **there is another path to `exhausted`.**

**NO EVIDENCE EITHER WAY:** KI-51 and KI-52 never fired in the batch (0 events). Still unmeasured.

## 🛡 THE HARDENING ROUND — advisory rules → code that refuses
Driven by the finding that **≥12 of 164 logged mistakes are self-admitted REPEATS**, several
committed while the author knew the rule. **Run `preflight.py` before touching anything.**
| tool | what it does |
|---|---|
| `preflight.py` | one gate: git sync + fixtures + docs + live-batch detection. **Exits 1.** |
| `lint_docs.py` | CLAUDE.md's doc rules enforced (R1-R6). Cut `04-HANDOFF` from 3,240 → 167 lines |
| `verify_fixtures.py` (+`--assert name=md5`) | PINNED saves byte-identical; put the assert **in** the measurement command |
| `repro_no_silent_except.py` | RATCHET at **140/203** silent handlers — may never rise |
| `29-DISABLED-FEATURES-REGISTRY.md` + lint R6 | every `POKEBOT_*` flag with its MEASUREMENT. **Check before proposing a feature** |
| `30-METRICS.md` | which instrument answers which question, at what n |
| `27-INJECTION-SURFACE.md` | how the bot observes/acts + the 8 timing traps (for goal #2) |
| `25-BACKUPS-AND-RESTORE.md` | restore points: naming, what a tag does/doesn't capture, recipes |
| `26-REVIEW-AND-HARDENING-PLAN-…md` | the full review: taxonomy, doc health, future path |

‼ **Three of these found real problems on their first run**: six competing START-HERE banners, an
**11th undocumented flag** (which turned out to be the roster blocker), and 140 silent handlers.

## ‼ WHAT THE USER DECIDED THIS SESSION
* **Promotions approved twice** (teach fix; then KI-51 + KI-52 + status telemetry).
* **"Roster hygiene before bosses"** approved as the boss-response direction — then found
  **BLOCKED** (KI-54): the box is empty, and the deposit path was already measured harmful.
  ⛔ **RETRACTED 2026-08-12:** the line below said the unlock was `POKEBOT_BOX_OVERFLOW_CATCH`,
  "one unhandled text box away". **Both halves are false.** That flag has defaulted to **ON** since
  2026-08-07 (`story_mode.py:2241-2243`, verified in the live code), and the text-box blocker was
  refuted the same day (`exit_frames=120`, zero forced presses). Four docs repeated it because they
  were written from a **stale code comment** instead of the default twenty lines below it. See
  KI-54's retraction block.
* **The boss-response design is still the user's call.** The status tax now has a resolved rate
  behind it, but a status response is a battle-policy change touching every mode — **do not build
  it unilaterally.**

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
## 🛠 TWO GATES WERE BLIND, AND FIXING THEM FOUND A REAL BUG
* **`audit_flag_names.py` was checking TWO files** — written before the chapters moved into
  `modules/story/*.py` — and, worse, could only see names written as literals AT the call site, while
  the house idiom is a module constant. So it was blindest exactly at the **completion markers**.
  Now globs 19 files, resolves `CONST = "LITERAL"`, prints per-file counts, and **exits 1** on a
  phantom (it used to print findings and exit 0). Coverage 2 files/117 names → 19/144. A/B proven by
  fault injection.
* **`pyflakes` was installed and had never been run.** New gate `repro_undefined_names.py`
  (ZERO tolerance over `modules/story` + `plugins/custom_modes`). It found my own missing import
  *after* a five-minute drive had already paid to reach it — **and KI-65**, below.

## ‼‼ THE ADVERSARIAL REVIEW OF THE FINISHED CHAPTER FOUND MY OWN FIX WAS WRONG TWICE
Run AFTER §Ch19 was committed and reported proven — which is exactly why it is worth doing.
* **KI-64's fix was DEAD CODE on the story path.** The MRO is `StoryItemBattleStrategy` →
  `LevelUpTravelBattleStrategy` → **`LevelUpLeadBattleStrategy`** → `DefaultBattleStrategy`, and
  `level_up.py:41` has its own `choose_new_lead_after_faint`. I had guarded the base class.
* **‼ And the `index >= 3` cut was in the WRONG INDEX SPACE.** Opening the battle party menu runs
  `UpdatePartyToBattleOrder`, which PHYSICALLY PERMUTES `gPlayerParty` — visible in my own passing
  log (`ch19d.log` f37745): index 1 becomes the ALLY's Metang and OUR Swellow moves to index 3. The
  cut **offered the ally and hid one of ours**, precisely when a replacement is needed.
* **My fault-injected A/B passed it anyway**, because the fixture modelled only the un-permuted
  order and asserted the base class directly. A control arm does not save you if all three arms
  measure the wrong thing.
* **Now fixed properly**: `ally_party_indices()` keyed on **ORIGINAL TRAINER ID** (identity travels
  with the Pokémon; position does not), wired at all three call sites. Repro is **5/5** with the
  permuted-array and story-class arms added; §Ch19 re-driven to a PASS afterwards.
⇒ **Two new prevention rules in `08-MISTAKES.md`:** print the MRO before "fixing" a strategy method,
and never identify a Pokémon by party index across a battle-menu boundary.

## ‼ FOUR NEW ISSUES FILED
* **KI-64 (FIXED)** — the multi-battle faint replacer would have sent out **STEVEN's** Pokémon.
  `FillPartnerParty` writes his Metang/Skarmory/Aggron into `gPlayerParty[3..5]`; both choosers
  excluded only the on-field mons and rank by condition, so three fresh L42-44 mons win outright.
  ‼ The guard needed already existed with **zero callers**: `is_double_battle_with_partner`.
* **KI-65 (OPEN, unfixed — ‼ and I CORRECTED MY OWN OVERSTATEMENT of it)** —
  `battle_move_replacing.py:280` uses `party_index`, which is assigned lower down. I first wrote
  that the HM-refusal re-pick "may never have executed"; **that was too strong.** Tracing the flow:
  the name is bound in the `AskWhetherToLearn` branch, which normally runs first, so on an ordinary
  teach the re-pick works. The real bug is narrower — line 371 is inside a `try:` whose `except`
  silently defaults, and on THAT path the name is never bound, so a later `CantForgetHM` raises
  `UnboundLocalError` into a SECOND silent `except` that declines. **Two invisible failures that
  compound.** Still worth fixing, still needs its own repro first.
* **KI-66 (OPEN)** — the multi-battle hazard is BROADER than the faint chooser: **four more**
  full-party scans on the same paths (two in `battle_handler.py`, `alive_slots`, and the rotation
  targets feeding an **unbounded** `while PARTY_MENU: press A`). The right fix is ONE choke point —
  `ally_party_indices()` now exists — not a guard per call site. ⚠ Also unverified and worth checking
  FIRST, because it would fire on turn 1 rather than on a faint: a claimed `IndexError` in
  `decide_turn_in_double_battle` from `gPlayerPartyCount` still being 3.
* **✅ KI-67 (CLOSED 2026-08-12)** — both halves. The chapter retry loops no longer swallow the
  abort (`StoryAbort` + the latch-keyed `reraise_if_aborting`, because a type-only guard cannot see
  an abort an inner loop already replaced with a fresh error), AND the harness now mirrors
  production via `StoryWhiteoutRecoveryMixin`. **First driven whiteout recovery in this project:**
  `--driver spacecenter2 --inject-weak` gave `whiteouts=3 recoveries=3`, ending controllable at
  `MOSSDEEP_CITY (28,17)`. ‼ **The proof is the FRAME DELTA, not the count** — +7,789 and +7,087
  between whiteouts, i.e. each attempt really walked back to Steven and fought again. Broken code
  would have burned three attempts in a handful of frames after ONE whiteout.
  ‼ Five defects in the mixin were caught by an adversarial review **before** it was driven
  (`PathFindingError` is a `RuntimeError` and escaped the recovery; MRO silent-revert; a `tag`
  dereference on the listener's stack; a class-counter budget; a `None`-is-success exit), plus a
  real blocker: an injected run could have silently overwritten a committed anchor.

## 🆕 THE REGI ARC — researched and measured 2026-08-12 (user-requested). See **KI-69**.

**‼ THE PARTY ORDER EVERYONE REMEMBERS IS THE RUBY/SAPPHIRE ONE.** Emerald reversed it:
**WAILORD first (slot 0), RELICANTH last** (`braille_puzzles.c:92-104`, comment and all). The wrong
order **fails silently** — no message, no error. Emerald also swapped **Regirock to ROCK SMASH**
(was Strength) and **Registeel to FLASH** (was Fly). Pinned in `repro_roster_reorder.py`.

**⛔ THE REGI BATTLE IS UNRECOVERABLE — read this before writing any battle policy.** Level 40,
catch rate 3. `B_OUTCOME_WON` removes it forever, and the fall-through case **including
`B_OUTCOME_LOST`** sets `FLAG_DEFEATED_*`. ⇒ **KO'ing it OR whiting out deletes the encounter
permanently.** The only safe non-catch exit is fleeing.

**✅ NEW CAPABILITY: `modules/story/roster.py`** — `plan_reorder` / `plan_last_slot` (PURE, proven
exhaustively: 720 permutations replayed, `repro_roster_reorder.py` 15/15) and `reorder_party()`
which drives `RotatePokemon` inside the `_rotate_lead_safely` harness.
⛔ **STALE TEXT CORRECTED 2026-08-13 — the line below said "the DRIVER is UNPROVEN" and that has been
FALSE since earlier the same day.** `--driver roster` ran **six swaps, all verified by PID**,
including `RotatePokemon(i, j != 0)`, giving `phases=4/4 saw_j_nonzero=True idempotent=True
restored=True can_continue=True ACCEPTANCE: PASS`. It contradicted this file's own 60-second summary
and `03-PUNCH-LIST.md`, in the exact section a Regi-scoping reader opens first.
‼ **What IS still true:** `reorder_party()` has **ZERO production callers** — it is a proven
capability, not yet content — and **KI-71** (the Manual-drop guard is unreachable) is still open.
Superseded text: ‼ **The DRIVER is UNPROVEN** — `RotatePokemon(i, j)` with `j != 0` has never been driven here, and it sits on the unfixed side of KI-38 (four unbounded loops + a `set_manual_mode()` trapdoor). **Drive it before anything depends on party order.**

**MEASURED capability status** (`probe_regi_capabilities.py`): ✅ Go-Goggles, HM08 in bag, Surf
(Zigzagoon), Rock Smash (Sceptile). ⛔ **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or
Flash. So the arc needs an acquisition phase first — Super Rod (Route 118), TM28 (Route 114), and
teaching Dive/Dig/Flash. ‼ **Relicanth is underwater-only, so Dive is upstream of everything.**

## ⏭ NEXT ACTIONS, IN ORDER

> **The ordered work queue** (the cold-start orientation is the ‼ YOU ARE HERE block at the top of
> this file, not here). Everything is committed and pushed; nothing is parked.
>
> 0. ‼ **THE LIVE QUEUE, 2026-08-13 (latest) — DO THESE FIRST; items 1-5 below are older framing.**
>    ✅ **(a) and (b) ARE DONE** — Room 2 arbitrated (clean) and driven to a PASS.
>    ✅ **(c) IS OBSOLETE** — the KI-77 repro is no longer the gate on Room 8: the despawn window
>    was derived (20x17) and Room 8 (11x14) is **smaller than it**, so KI-77 cannot fire there. See
>    KI-77's corrected entry. A repro is still worth having for the LARGE rooms, but it blocks
>    nothing.
>
>    **(a2) ROOM 3 IS NEXT, AND ARBITRATE IT FIRST.** ‼ It is **not** the walk the build spec calls
>    it. Decomp passes found: a **7-boulder puzzle the spec omits entirely**; the push-free
>    `(4,15) → (8,1)` line is 18 steps but **unavoidably** crosses `{(6,5),(7,5),(8,5)}`, the union
>    of both trainer sight cones (a zero-sight route exists but needs Strength — upstream takes it,
>    `puzzle_solver.py:427-436`); and it is **the one room where a boulder can be pushed onto a warp
>    tile that matters** — `(9,13)`, the Room 7 retreat. That search hit a 4M-state cap, so its
>    "no other hazard" is a lower bound, not a proof. **Then drive `--driver ch20room3` exactly like
>    room1/room2:** dump live objects on arrival, multi-point A/B across the solve, push only through
>    `strength_push`, verify by `local_id`, end with "and the bot can continue".
>
>    **(b2) ROOM 8 IS ALREADY ADJUDICATED — build from OUR sequence, not upstream's.** Both work;
>    ours is **9 pushes vs upstream's 10** and never touches boulder #3. Full table in
>    `ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md`. ⛔ **Step 9 must face LEFT,
>    never UP** — a boulder pushed north from `(5,4)` lands on `(5,3)` and **permanently seals the
>    only route to the `(5,2)` exit warp**. ✅ A jam IS recoverable: exit to Room 3 via `(5,12)` and
>    re-enter; all twelve boulders respawn. Wire that as the room's failure handler.
>
>    **(c2) ⚠ BLOCKER 2 — THE EXIT STRANDS THE RUN, AND IT IS UNTESTED.** See the banner at the top:
>    step **SOUTH to `(38,23)`** and Surf, never north. Build the exit leg with that assertion in it.
>
>    **(d) STILL THE USER'S CALL, NOT MINE:** promoting the **three** drifted files to
>    `custom-pokebot/`. Nothing here changes that.
> 1. **Run `preflight.py`**, then the **16**-gate suite in "HOW TO RUN / TEST" (all exit 0 as of
>    2026-08-13), and the sandbox↔custom drift loop. ‼ **EXPECT EXACTLY 2:**
>    `modules/story/early_game.py` and `plugins/custom_modes/story_mode.py` — KI-63's **production
>    wiring**, driven to a PASS but **NOT promoted**. (Do NOT expect `roster.py`/`menuing.py`:
>    those were PROMOTED on 2026-08-13 and drift on them is now zero.)
>
> 1b. ⛔ **THE FIRST DECISION FOR THE USER: promote the KI-63 WIRING?** Until it is promoted,
>    `custom-pokebot`'s copy of the KI-63 fix is **INERT** — it reads `_needs_party_slot` and
>    nothing in that tree sets it, so a real run there still dies on a full party.
>    **Measured worth: 20 terminal run-kills in 1,129 runs (0.91% excl. a reverted party-cap
>    bundle), #1 of 14 derail causes by frames per event (1,717k ≈ 46 min), every one five badges
>    deep.** Restore-point-first, then verify by DRIVING `--build custom`, never by a diff.
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
>    `custom-pokebot/` has NOT been asked for — that is the USER's call.**
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
>    **DO THIS FIRST, near-zero risk and required either way:** inject Dive via
>    `debug_utilities.py:611` and drive Route 128 → Seafloor Cavern to see what the legs really need.
>    ‼ If a hunting ground is ever added, **NOT to `TRAINING_GRASS`** — measured, a Shoal Cave row
>    becomes the highest band and flips `best_training_area` for every team from ~L30 up.
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
>    ⛔ **THE NEXT STEP IS A MEASUREMENT, NOT CODE: drive INTO the cavern and re-measure the
>    interior with LIVE objects.** The atlas was read from Mossdeep, and `is_tile_accessible` blocks
>    every tile whose object is not in `active_objects` — so its per-room routing is a **LOWER
>    BOUND**, and section 4's NO-PATHs are an artifact, not map facts. (‼ §Ch19 caught this exact
>    trap once already; the probe now documents it in its own output as section 3b.)
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
>    ⚠ **Still unproven LIVE** — a plan is not a walk, and the EXECUTOR has never crossed a current.
>    ℹ Upstream `puzzle_solver.py:405` DOES `navigate_to(ROOM6, (4,1))` and its wiki marks the
>    Seafloor Cavern ✅ for Emerald — the strongest available signal that the executor can do it,
>    and still a third-party claim, not evidence.
>    That is now the first thing to drive, not the first thing to design around.
>    Also: **puzzle state RESETS on every map re-entry** (`FLAG_TEMP_*`), so never cache "solved";
>    `FLAG_SYS_USE_STRENGTH` by contrast persists. **Losing to Archie resets the whole dungeon.** It IS the ladder
>    (`chapters.py:233`, graded `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`; `story_mode.py:3654` = END OF BUILT
>    CONTENT — ‼ that line still says "BLOCKED BY KI-63", which is **stale**, fix it). Uniquely
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
>    collateral control byte-identical. **The only thing left on this item is PROMOTION, which is
>    the USER's call** (drift is now 3). The retraction that reprioritised it follows.
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
   The ladder now runs **19 of 24 beats**. Three drivers, all PASS:
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
PYTHONUTF8=1 py -3.12 run_gates.py        # THE STANDING SUITE — all 17, exits non-zero on any
                                          #   failure (~125s). The list lives in CODE, not prose.
PYTHONUTF8=1 py -3.12 run_gates.py --quick   # the 10 needing no ROM (~3s)
PYTHONUTF8=1 py -3.12 run_gates.py --list    # what is in the suite
PYTHONUTF8=1 py -3.12 probe_chapter_order.py --build custom   # ‼ also check the OTHER fork

# --- §Ch20, the live drives (each ~4-6 min; both PASS as of 2026-08-13) ---
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20dive  --frames 900000
#   Expect: legs=6/6 at_entrance=True got_out=True can_continue=True ACCEPTANCE: PASS
#   ‼ `got_out` is the one that matters — an underwater cavern is the best place to strand a run.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20room1 --frames 1500000
#   Expect: in_room1=True ab_before=False ab_after=True smashed=True pushed1=True pushed2=True
#           in_room2=True can_continue=True   ACCEPTANCE: PASS
#   ‼ `ab_before=False` is an ASSERTED part of the verdict: if the corridor was already reachable
#     the run proved nothing about the puzzle. A one-armed pass here would be meaningless.
```

‼ **A driver keeps running after it prints ACCEPTANCE** — it drops to Manual and the harness only
exits on its own 20,000-idle-frame detector, logging **"HANG CONFIRMED"** on a run that SUCCEEDED.
**Read the `ACCEPTANCE:` line, not the last line.** Full transcripts land in
`tools/story-dev/harness_sandbox.log`.

‼ **VERIFY THE SANDBOX↔CUSTOM DRIFT ROW RATHER THAN TRUSTING IT** — the PowerShell loop is in
`28-HANDOFF-ARCHIVE.md`'s copy of this section. Expected as of 2026-08-13: **exactly 3**
(`modules/map_path.py`, `modules/story/early_game.py`, `plugins/custom_modes/story_mode.py`).
Anything else is unexplained drift. ‼ `tools/story-dev/` is sandbox-only and is **not** part of
that comparison, so `--driver ch20room1` does not change the count.

---

# 📚 EARLIER HANDOFF SNAPSHOTS → `28-HANDOFF-ARCHIVE.md`

Every superseded "you are here" section now lives in **`28-HANDOFF-ARCHIVE.md`** (append-only).
This file is CURRENT STATE only — if something here is no longer true, fix it here rather than
adding another banner below it.
