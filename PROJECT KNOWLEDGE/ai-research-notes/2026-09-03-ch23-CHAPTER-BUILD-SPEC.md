# §Ch23 (VICTORY ROAD) — CHAPTER BUILD SPEC

> ⛔⛔ **SUPERSEDED IN PART, 2026-09-05 — ITEM 8 OF THIS SPEC IS BUILT.** The "chapter
> orchestrator + Segment 23 wiring" this note lists as `⛔ not built` **SHIPPED**: `ch23_chapter_done()`
> + `do_victory_road_chapter()` in `modules/story/victory_road.py`, dispatch at `story_mode.py:3779-3795`,
> `--driver ch23chapter`. ⛔ DO NOT BUILD IT AGAIN. The live work is `#24-ch23chain` — the chapter's
> CHAIN is blocked by `KI-90`. The rest of this spec is kept for its reasoning.


> Written 2026-09-03, before any §Ch23 production code exists. ⛔ **`sandbox-pokebot/modules/story/
> victory_road.py` DOES NOT EXIST.** Everything §Ch23 has today is HARNESS DRIVERS.
> Companion notes: `2026-09-03-ch23-VICTORY-ROAD-RECON.md` (the approach),
> `2026-09-03-ch23-VICTORY-ROAD-B1F-B2F.md` (the basements + the boulder seal),
> `2026-09-03-ch23-VICTORY-ROAD-1F.md` (1F — three regions cut by ELEVATION),
> **`2026-09-03-ch23-WATER-ROUTE.md`** (Sootopolis → Ever Grande, tile by tile), and
> `2026-09-03-ch23-WATERFALL-TEACH-PREDICTIONS.md` (leg 1, graded).
> The authoritative live status is `#24-ch23victoryroad` and `04-HANDOFF.md`'s queue head.

---

## §0. ⛔⛔ THE FIRST THING TO GET RIGHT: "LEG 1 IS DONE" MEANS A DRIVER, NOT PRODUCTION

`Ch23TeachMode` is a **harness driver** that calls production's `teach_hm_move`. So the PRIMITIVE is
proven — Waterfall really can be taught to Wailmer, Rollout really is the move that goes, Dive and
Surf really do survive. **But nothing in the shipped bot orchestrates it.**

‼ **This is the exact shape an adversarial review caught in §Ch22**, where four movement legs lived
only in drivers while the docs read as though the chapter could perform them.
⇒ **§Ch23's real deliverable is a PRODUCTION MODULE plus Segment 23 wiring**, not more drivers.
⇒ When writing status anywhere, say *"the driver drove it"* or *"the chapter does it"* — never the
ambiguous *"leg N is done"*.

## §1. THE OPENING STATE — AND A DANGER I GOT WRONG, CORRECTED HERE

**Measured on `post_waterfall.ss1`** (`--driver partypids`, which had to be taught to report HP by
identity before anything in this tree could answer the question):

```
slot=3  Wailmer   L40  pid=FA51ECF3  hp=0/160 (0%)  ⛔ FAINTED
slot=2  Swellow   L42  hp=5/118 (4%)
the other four at 100%          party total 428/701 (61%)
```

Wailmer is the **sole carrier of Dive** (the only exit from the Sootopolis crater) **and of
Waterfall** (the only way up to Victory Road), and also carries Surf.

### ⛔⛔ THE CORRECTION IS MORE USEFUL THAN THE FINDING: FIELD MOVES IGNORE HP ENTIRELY
I first wrote that the heal was a **hard precondition** because the bot "cannot leave the crater on a
dead Dive carrier". **That is FALSE**, and a decomp pass refuted it:

* **No HP check exists anywhere in the field-move chain** — not in `SetPartyMonFieldSelectionActions`
  (`party_menu.c:2607-2637`, which reads only `MON_DATA_MOVE1..4`), not in `CursorCb_FieldMove`
  (`:3702-3780`, whose complete gate list is null-func / link-room / badge flag), not in
  `SetUpFieldMove_Surf` (`:3858`), `_Dive` (`:3916`) or `_Waterfall` (`:3896`).
* The **prompt** path is the same: every one of `EventScript_UseSurf` / `_UseDive` / `_UseWaterfall`
  picks its mon with `checkpartymove` → `ScrCmd_checkpartymove` (`scrcmd.c:1713-1732`), which skips
  **only** `SPECIES_NONE` and eggs.
* All 15 `MON_DATA_HP` reads in `party_menu.c` were enumerated; every one is cosmetic or belongs to
  another context. ‼ The `gText_PkmnHasNoEnergy` refusal people misremember is `:5813` — **in-battle
  switching only.**

⇒ **A fainted Wailmer Surfs, Dives and Waterfalls exactly as at full HP.**
⇒ ⛔⛔ **ASSERT WAILMER *PRESENT*, NEVER *ALIVE*.** Present by `(PID, species)` is right — a deposited
or released Wailmer genuinely strands the run. **A liveness gate is dead code against the real
engine, and worse: it would make the bot refuse a move the game permits.**
✅ **Our own code is already clear of the one real version of this risk:** `hm_learner_slot`
(`early_game.py:4316`) skips only `None` and eggs, with **no HP filter** — read in full, not grepped.
⚠ One behavioural difference worth knowing: the party menu uses the slot you highlight, while the
**prompt auto-selects the LOWEST-NUMBERED slot** that knows the move. If the bot picks a slot and the
prompt names another, that mismatch is ours to handle.

### ⛔ AND I OVERSTATED `allow_escaping: false`
It gates **Escape Rope and Dig ONLY** (`global.fieldmap.h:186`; exactly two readers —
`item_use.c:911` and `fldeff_dig.c:17`). It does **not** block Fly, Teleport, or fleeing a wild
battle. **Fly is permitted on Sootopolis, Routes 126/127/128 and Ever Grande**
(`MAP_TYPE_CITY` / `MAP_TYPE_OCEAN_ROUTE`), blocked only while `MAP_TYPE_UNDERWATER`.
⚠ No party member knows Fly, so it is a capability we could acquire, not one we hold.

### ⭐⭐ THE TWO RISKS THAT REPLACE IT — BOTH BIGGER THAN THE ONE THEY REPLACE
1. ⛔ **`lastHealLocation` MUST BE ARMED BEFORE DEPARTING.** A whiteout warps to
   `gSaveBlock1Ptr->lastHealLocation`, set by `setrespawn` in the Poké Center's **`ON_TRANSITION`** —
   i.e. by merely **walking in**; healing is not required. If the bot never entered the Sootopolis
   Center, a whiteout dumps it at whatever far earlier Center is still saved. **That is the genuinely
   expensive failure on this leg.** ⇒ **READ the value; never assume it.** *(⚠ `sWhiteOutHealCenters`
   does not exist in Emerald — that is an FRLG construct. Emerald has exactly one saved heal warp.)*
2. ⚠ **FIELD POISON TICKS WHILE SURFING AND CAN WIPE THE PARTY** — the only non-battle party-killer
   (`field_poison.c:119-140`: `if (hp == 0 || --hp == 0) numFainted++`), exempt only on
   forced-movement tiles. ⇒ **cure poison before departing.**

### ✅ WHITEOUT IS A COST, NOT A STRAND
`DoWhiteOut` (`overworld.c:358-366`) runs `HealPlayerParty()` — **full HP, full PP, status cleared**
(`script_pokemon_util.c:30-60`) — halves money, and warps. The avatar state is **re-derived from the
destination tile** (`GetAdjustedInitialTransitionFlags`, `overworld.c:911-927`), so on-foot-on-water
is structurally impossible. ⇒ the heal before departing is still worth doing, for the smaller reason
that a whiteout costs **half the money** and restarts the leg.

## §2. THE BUILD MECHANICS — VERIFIED AGAINST THE HARNESS, AND IT IS **FOUR** EDITS, NOT THREE

Line numbers verified 2026-09-03 against a 14,817-line `story_harness.py` (an earlier reading of
14,803 was a transcription error and could not be reproduced; git's HEAD blob, `wc` and `grep -c`
all agree on 14,817). ⚠ **Re-derive them before editing — they move constantly.**

1. **`story_harness.py:37`** — add `"ch23chapter"` to `choices=[...]`. *(argparse ignores order; the
   list is not chapter-ordered.)*
2. **after `:14320`** — the dispatch branch:
   ```python
   elif args.driver == "ch23chapter":
       context.bot_mode_instance = Ch23ChapterMode()
   ```
   The chain lives inside the main frame loop under
   `if context.bot_mode == "Manual": … elif len(context.controller_stack) == 0:` and terminates in an
   `else:` that instantiates the real production mode by name.
   ⭐ *(`"story"` is in `choices` with NO `elif` — it falls through to that terminal `else` on purpose
   and runs production `StoryMode`. A second shape defines the class inline inside the `elif` body
   (`traintest`, `gymtest`, `anchorstory`) — **not** what §Ch2x uses; ignore it.)*
3. **after `:12546`** (end of `Ch23TeachMode`, before `class Ch22StairsMode` at `:12549`) —
   `class Ch23ChapterMode(BotMode)`, modelled on `Ch22ChapterMode` (`:11959-12229`).
4. **a `saves/FIXTURES.md5` row** for any fixture the chapter captures. ⛔ **Not** a README table row:
   `tools/story-dev/README.md`'s saves table stops at §Ch11d and is not the registry.

**Required members:** `@staticmethod name() -> str`; `run(self)` — a GENERATOR pushed onto
`context.controller_stack`, ending with `context.set_manual_mode()`.
⚠ **`BotMode.on_whiteout` defaults to `False`, which DROPS the bot** — a chapter driver must override
it. `on_battle_started` / `on_battle_ended` are optional; wrap `super().on_battle_ended(outcome)` in
`try/except TypeError`.

### ⛔⛔ THE `os` TRAP — IT HAS ALREADY COST A 25-MINUTE DRIVE, AND IT IS UNGATED
`story_harness.py` imports **`os as _os`**. A bare module-level `os` in a new driver is a `NameError`
**on frame 1**. Use a function-local `import os` (as `Ch22ChapterMode` does) or `import os as _os`
(as `Ch23TeachMode` does).
‼ **`repro_undefined_names.py` scans `modules/story/`, NOT `tools/story-dev/`**, so nothing catches
this. ⇒ **SMOKE-TEST EVERY NEW DRIVER WITH A TINY `--frames` BEFORE COMMITTING TO A LONG RUN.**

### Conventions
* **Logging:** a module-level `log(msg)` to logfile + stdout, every line prefixed `f"[{TAG}] ..."`.
  Emission order `PRE` → `RESULT` → named reading blocks → `CAPTURE SKIPPED`/`REFUSED` →
  **`ACCEPTANCE:` last, always**. There is **no `READING:` prefix**.
* ⭐ **A refusal IS a reading** — `except Exception as err:  # a refusal IS the reading`, logging the
  exception TYPE. Never swallow.
* **Fault knobs:** `POKEBOT_CH23_FAULT_<ARM>=1` (the §Ch21/§Ch22 suffixed-boolean style). ⛔ The bare
  multi-valued `POKEBOT_CH20_FAULT=<name>` form is §Ch20-only. `POKEBOT_CH23_*` is a free namespace.
* **Capture:** `CH23_CAPTURE=<name>.ss1`, gated on FULL PASS, refusing overwrite without
  `CAPTURE_FORCE=1`. ⛔ Do **not** copy the older default-ON boolean idiom
  (`os.environ.get("CH18_CAPTURE", "1") != "0"`) used by CH16-CH19 — it is superseded.
* ⭐ `modules/debug_logger.py`'s `_BEHAVIOUR_ENV_VARS` is the canonical registry of production knobs
  — read it before naming a new one. And `POKEBOT_HMTEACH_POSTLEARN_A` (`early_game.py:5045`) is an
  existing A/B arm on the HM-teach post-learn path, directly relevant to the Waterfall teach.

## §2b. ✅ THE LEGS ARE MEASURED — PRODUCTION ROUTES THEM, HOP BY HOP (`ch23route` R9)

Asked of production BEFORE writing the code that walks them. Every hop below is WITHIN one map,
which is the only shape `calculate_path` can answer, so each is a real reading.

| hop | production |
|---|---|
| SOOTOPOLIS (31,33) → Poké Center door (43,32) | ✅ 23 wp |
| SOOTOPOLIS (31,33) → dive tile (29,53) | ✅ 22 wp |
| **SOOTOPOLIS Poké Center (43,32) → dive tile (29,53)** | ✅ **37 wp** — leg 2 → leg 3 joins up |
| `UNDERWATER_SOOTOPOLIS_CITY` (9,6) → walk-on warp (9,8) | ✅ 3 wp |
| `UNDERWATER_ROUTE126` (45,65) → safe emerge tile (45,66) | ✅ 1 wp |
| `ROUTE126` (45,66) → east edge (79,45) | ✅ 55 wp |
| `ROUTE127` (0,45) → south edge (30,79) | ✅ 64 wp |
| `ROUTE128` (30,0) → midpoint (70,25) | ✅ 79 wp |
| `ROUTE128` (101,29) → Ever Grande seam (119,29) | ✅ 20 wp |

⭐ **KI-72 ("the planner cannot see non-surfacing tiles") did NOT bite on either underwater hop** —
that was the flagged risk on leg 3 and it is measured clear.

### ⛔⛔ AND ONE REFUSAL TAUGHT A BUILD RULE — **NEVER AIM A PATH AT AN OBJECT'S TILE**
`ROUTE128 (70,25) → (101,29)` **REFUSES**, and so does `→ (101,22)`. But `→ (101,26)` returns **32
wp** and `→ (100,29)` returns **34 wp**. **(101,29) is Carlee's tile and (101,22) is Harrison's.**
⇒ the channel is **OPEN**; production was refusing because the **destination** was occupied.
⇒ **Leg 4 must target a free channel tile — use (101,26) — never a trainer's own tile.**
‼ **A refusal to an occupied tile says "something is standing there", not "you cannot get there".**

‼ **This also falsified a comment in `Ch23RouteMode` itself**, which asserted that production does
NOT block on objects on a non-active map. It does. ✅ The correction *strengthens* the B1F reading:
R6's answers are the **"boulders still present"** case, so R6a/R6b/R6c refusing genuinely corroborates
that the B1F arrival chamber is SEALED until the pushes happen. B2F (no boulders) and the 1F queries
are unaffected. ⇒ `08-MISTAKES.md` 2026-09-03: *a claim about your INSTRUMENT needs the same evidence
bar as a claim about the SUBJECT.*

## §3. ⭐ THE FOUR GRADING RULES TO COPY — EACH ONE EARNED BY A SHIPPED DEFECT

From `Ch22ChapterMode`. These are not style; each exists because a driver PASSED while broken.

1. **ANTI-VACUITY PREMISE (`not start_done`).** A chapter driver that starts already-done grades a
   **zero-frame no-op as PASS**. §Ch21's chapter driver shipped with exactly that hole.
2. **A REAL `calculate_path` OFF THE END TILE, LENGTH NON-ZERO.** The missing conjunct that let
   §Ch15, §Ch18 and §Ch19 each PASS **while stranded**. ⛔ Non-zero matters because *a whiteout
   respawns the bot standing ON the Poké Center apron* — a length-0 path lets the very failure being
   checked for satisfy the check.
3. **A PRESENCE CONJUNCT BEFORE EVERY ABSENCE CONJUNCT** — `b1f_entered` before `battles_b1f == 0`.
   *"Zero battles means nothing unless B1F was entered — drive 1 printed 0 having never gone there."*
   This is house rule 7 (**a candidate is not an attempt**) in grade form.
4. **GRADE THE BOUND, NOT THE COUNT; THE INVARIANT, NOT THE SINGLE-ATTEMPT FIGURE.**
   `recoveries <= 2` rather than `whiteouts == 0` (production tolerates 40, and the Juan fight is
   measured stochastic); `ice_total % 64 == 0` summed across attempts rather than `steps == 64`.

## §4. THE LEG PLAN (skeleton — fill from the recon notes as they land)

| leg | what | status |
|---|---|---|
| 1 | teach Waterfall to Wailmer | ✅ **driver** only (`ch23teach`), production module absent |
| 2 | **heal (HARD precondition)** + preflight assert Wailmer ALIVE by (PID, species) | ⛔ not built |
| 3 | leave the crater: dive at (29,53) → `UNDERWATER_SOOTOPOLIS_CITY (9,6)` → walk-on warp (9,8) → `UNDERWATER_ROUTE126 (45,65)` → **step south to (45,66)** → emerge | ⛔ not built — ✅ **recon DONE** |
| 4 | Rt126 east → Rt127 south → Rt128 basin A → ⛔ **fight Carlee + Harrison at x=101** → exit (119, y 27-32) | ⛔ not built — ✅ **recon DONE** |
| 5 | Ever Grande: surf to **(18,68)**, face NORTH, press A → lands **(18,59)** → (18,56) → step north to land **(18,55)** → 16 steps to **(18,41)** | ⛔ not built — ✅ **recon DONE** |
| 6 | Victory Road 1F: (15,40) → **Hope (MANDATORY)** → Wally (2,23) or (3,23) → the B1F ladder (9,14) | ⛔ not built — ✅ **1F recon DONE** |
| 7 | **B1F: 2 pushes + 1 smash** → B2F → back to B1F → 1F(21,32) → **Edgar (MANDATORY)** → exit (39,5) | ⛔ not built |
| 8 | chapter orchestrator + Segment 23 wiring + fixture capture | ⛔ not built |

⛔ **Leg 7 carries the seal hazard.** Only pushes can kill (0 of 186,602 walk and 145 smash edges
cross live→dead), so the guard is a refusal inside the `strength_push` call site — ruled in
`06-DECISIONS-LOG.md` 2026-09-03. **Never push (4,7) or (9,10) SOUTH.**
### ⛔⛔ WHAT THE WATER-ROUTE AUDIT **CORRECTED** — three facts I had recorded wrong
1. **THE WATERFALL IS ON EVER GRANDE'S OWN MAP, NOT ROUTE 128.** `MB_WATERFALL`: Rt126 **0**,
   Rt127 **0**, Rt128 **0**, **EverGrandeCity 96** (x=15-26, y=60-67).
2. **THE ROUTE HAS *TWO* UNDERWATER TRANSITIONS.** The dive lands on a separate 20×10 map,
   `UNDERWATER_SOOTOPOLIS_CITY`, which reaches Route 126 by a **walk-on warp**, not by diving.
3. **DIVE IS GATED ON BADGE 7**, not Badge 8 (Waterfall is Badge 8). Harmless — we hold all eight.

⛔⛔ **AND THE x=101 PINCH IS SETTLED: THE BATTLES ARE UNAVOIDABLE.** Carlee (101,29) and Harrison
(101,22), sight 4, patrol ranges that **between them occupy the entire 8-tile channel** (y=22-29,
the only way through basin A). All 48 configurations × 8 rows enumerated: **no guaranteed-safe row**;
best odds ~44% at y=22 or y=29. No alternate column, and the **underwater bypass fails** (max x=81).
⇒ **the bot must FIGHT them, not route around them.** First pass only — their flags then stay set.
⭐ **Land trainers cannot see a surfing player** (elevation mismatch is checked before the
object-event case), so the three elevation-3 trainers on Route 128 are harmless.

⚠ **Two more corrections worth carrying:** `VAR_ROUTE128_STATE` must be tested **`!= 1`, not `>= 2`**
(`MapHeaderCheckScriptTable` is exact equality — only 1 fires); and ⛔ **do not emerge on the arrival
tile** `UNDERWATER_ROUTE126 (45,65)` — it is `MB_WATER_DOOR`, emergible only because a `#ifdef BUGFIX`
is off ("the dive glitch"). **Step one south to (45,66) first.**
⚠ Route127 CAN seize control if `VAR_SHOULD_END_ABNORMAL_WEATHER == 1`, and its ON_LOAD rewrites
water metatiles when `VAR_ABNORMAL_WEATHER_LOCATION` is 13/14 — a walkability change invisible to a
static reader (KI-74's shape).

### ⚠⚠ AND ONE UNMEASURED QUESTION THAT DECIDES THE CHAPTER'S RISK PROFILE
**Is the Ever Grande Poké Center (27,48) reachable from the waterfall-top landing (18,55)?**
Production paths (18,41)→(27,49) in 23 wp, but the water-route audit says (27,48) sits in an upper
city gated behind Victory Road. **These may not conflict** — "from below" probably means below the
*waterfall*. ⛔ **Do not assume either way.** If the answer is NO, there is **no heal anywhere between
Sootopolis and the Pokémon League**. ⭐ **One `calculate_path` query settles it: add (18,55) → (27,48)
to `--driver ch23route`.**

### ⭐ WHAT THE 1F AUDIT ADDS TO THE PLAN (full detail in its own note)
* ✅ **1F needs NO field moves** — zero boulders, zero breakable rocks, `requires_flash: false`.
  Strength/Rock Smash/Flash are basement-only, and **1F cannot be bricked** the way B1F can.
* ⭐⭐ **1F is THREE regions cut by ELEVATION, not walls.** From (15,40) you can reach ONLY (9,14);
  from (21,32) ONLY (39,5); (42,38) is a dead end. A and B *share* 16 elevation-15 bridge tiles but
  arrive carrying **3** vs **4**, so the same tile lets one through and refuses the other.
  ⇒ **this is what forces the basement detour**, and it rests entirely on "elevation-15 PRESERVES
  the carried elevation".
* ⭐ **Wally fires unconditionally on the first visit and never again** (`VAR_VICTORY_ROAD_1F_STATE`
  = 0x40C3, a persistent var appearing in only three files; nothing else in the game touches it).
  The `ON_TRANSITION` is a **no-op at state 0** and can only reposition Wally.
  ⛔ **CORRECTION: "he becomes a permanent blocker" was too strong** — he parks at (2,24) *or*
  (3,24), never both, and seals nothing (44 vs 46 steps).
* ⛔ **TWO MANDATORY 1F SIGHT BATTLES, one per leg: Hope (6,15) on the way IN, Edgar (33,22) on the
  way OUT.** Both proven by removing their cones and finding the destination unreachable. The other
  three (Albert, Katelynn, Quincy) are avoidable at **+0 steps**.
* ⚠ **Encounters do NOT fire on every 1F tile** — only `MB_CAVE` carries the flag, so **632 of 682
  walkable tiles (92.7%)**; 50 are safe. *(The basements differ — there it is every walkable tile.)*

### ⚠⚠ AND ONE OPEN DISAGREEMENT THAT MUST BE SETTLED ON THE FIRST 1F VISIT
Our `calculate_path` says **(21,32)→(39,5) = 64**; the audit's BFS says **61** — while agreeing
EXACTLY on (15,40)→(9,14) = 44, →Wally = 29, Wally→ladder = 15, and on (15,40)→(39,5) being
unreachable. ‼ **Leg 2 is the only leg crossing the elevation-15 bridge at y=17-18**, and
elevation-15 is precisely the rule that moves the reachable set by hundreds of tiles.
⭐ **The cheapest discriminator is ONE STEP:** walk to **1F (29,28)** from the entrance side, print
the carried elevation (**predict 3**), step **EAST to (30,28)** (**predict FAIL**); then from the
(21,32) side, same tile, **predict elevation 4 and the step SUCCEEDS**. ⛔ **If it succeeds from the
entrance side, the three-region model is wrong and the basement detour is not forced** — which would
change the chapter's shape entirely. **Do this on the first 1F visit; it costs one step.**

⛔ **Nothing about the basements is confirmed live yet** — the three checks in the B1F/B2F note's §F
are owed, and they cannot run until legs 2-6 can put the bot on that floor.

## §4b. ⭐⭐ THE REVIEWED DESIGN FOR LEGS 2-3 — AND THE FOUR BLOCKERS FOUND *BEFORE ANY CODE EXISTED*

Three independent designs (safety-first / minimal-reuse / structural-fidelity) were synthesised and
then adversarially attacked. **The attack found 4 BLOCKERS, 5 SERIOUS and 3 MINOR defects in a design
that had already been judged the best of three.** Verdict: *implement with the listed fixes* — all
local. ‼ **Every one of these would have cost at least one 25-minute drive, and blocker 3 costs hours.**

### ⛔⛔ THE FACT THAT SHAPES EVERYTHING: NO NAVIGATION PRIMITIVE HERE CAN DIVE OR EMERGE
`WaypointAction.Dive` / `.Emerge` are **declared** at `map_path.py:692-693` and **assigned nowhere**;
`follow_waypoints` handles only `Surf` and `Waterfall` (`walking.py:221,226,284,294`). Structurally
corroborated: `cache/warp_graph_BPEE0.json` gives `SOOTOPOLIS_CITY` **13 warp edges and ZERO
connections**, none to `UNDERWATER_SOOTOPOLIS_CITY` — the scripted `setdivewarp` is in neither
structure. ⇒ **leg 3 must hand-sequence the crossing; `navigate_to_anywhere(ROUTE126, …)` from inside
the crater is structurally impossible.**
⛔⛔ **DO NOT GENERALISE THAT TO THE REST OF THE CHAPTER — MEASURED 2026-09-04, AND LEG 4 IS THE
OPPOSITE.** The crater refuses because Sootopolis has **zero map connections**; that says nothing
about maps which ARE connected. `ch23route` R10 asked, and every cross-map query on the ocean route
**SUCCEEDED**: ROUTE126→ROUTE127 **56 wp**, ROUTE127→ROUTE128 **65 wp**, ROUTE128 (101,26)→
EVER_GRANDE (18,68) **53 wp**, and ⭐⭐ **the WHOLE of leg 4 — ROUTE126 (45,66) → EVER_GRANDE
(18,68) — in ONE call: 273 wp.**
⇒ **leg 4 is a navigate-and-fight leg, not a hand-sequenced one.**
‼ **The rule to carry is NOT "the planner cannot cross maps". It is "the planner crosses
CONNECTIONS, never WARPS"** — which is exactly what its own refusal message says (*"warps don't
count"*). The crater is warp-only; the ocean route is connection-joined. **One sentence, two opposite
consequences, and the difference is a property of the MAP, not of the planner.**
⭐ **BUT §Ch21 LEG 3 ALREADY DOES THIS EXACT CROSSING AND IS DRIVEN AND PASSING** (`sootopolis.py:1613`,
`:1636`). ⇒ **import its constants, do not re-derive them; do NOT refactor it in this commit** (that
would charge §Ch23 for a §Ch21 regression). Extract to a shared helper only after §Ch23 has its own
`ACCEPTANCE: PASS`, in one commit that re-drives **both** `ch21approach` and `ch23depart`.
⚠ **CORRECTION to the water-route note:** §Ch21's three drive logs
(`ch21approach_clean4/clean5/capture.log:134`) all print the warp resting tile as **(45,66)**, not
(45,65) — so `navigate_to(UWS,(9,8))` *does* fire the arrow warp and the avatar *already rests on the
safe emerge tile*. **READ and BRANCH; do not unconditionally step south.**

### THE FOUR BLOCKERS (each with the failure sequence, so they are not re-introduced)
1. ⛔ **A PER-ATTEMPT "archive and reset" MAKES THE HAPPY PATH UNGRADEABLE.** Taking `R-PRE` before
   the retry loop and then archiving `readings`/`trace` on attempt 1 means a **perfect single-attempt
   run FAILS** (the reading is in `previous_attempts`, not in `readings`). ⇒ **grade the UNION across
   `previous_attempts`** exactly as §Ch22 sums `ice_total` (`story_harness.py:12170-12181`, which
   records that grading the last attempt's figure *"would FAIL a healthy run"*), and make the trace
   check a **subsequence**, never `==`. ‼ §Ch22's archive is deliberately narrow (`if "steps" in
   report:`, only accumulating counters) — do not generalise it to readings.
2. ⛔ **ASSERTION ORDER MISDIAGNOSES THE EXACT FAULT THE LEG EXISTS FOR.** "HP must rise" placed
   BEFORE the respawn check means: a real respawn fault → retry → the party is already full → the HP
   assertion raises *"HP total did not rise"* and the respawn check is never reached. The chapter dies
   with the wrong diagnosis and its own re-arm retry is destroyed. ⇒ **respawn check FIRST**, and gate
   the HP rise on `hp_before < max`, not on an attempt number.
3. ⛔⛔ **THE LAYOUT PIN LIVES IN LEG 2 BUT PROTECTS LEG 3'S WALK — AND A WHITEOUT SKIPS LEG 2.**
   `_pin_planner_to_live_layout` mutates a **process-global** cache keyed by (rom, map) with no unpin,
   and §Ch21 leaves `SOOTOPOLIS_CITY` pinned to the LEGENDS_BATTLE layout. Sequence: whiteout on
   Route 128 → respawn at (43,32) → `departure_ready()` is True (whiteout heals fully) → **leg 2 is
   skipped → the pin never runs** → leg 3 walks `(43,32)→(29,53)` on the stale layout, which §Ch21
   measured as *"37 waypoints, walks into live rock"* vs 35 correct. Bounded only by the ~41-cycle
   whiteout budget ⇒ **hours**. ⇒ **pin inside leg 3, where the walk it protects happens.**
4. ⛔ **THE NEVER-HANG AUDIT CLEARED THE WRONG LOOPS.** It checked `heal_in_pokemon_center`'s *exit*
   loops and declared it safe; the **nurse interaction three lines earlier** is unbounded and
   abort-blind. ⇒ **KI-83** (filed): `tasks_scripts.py` is **8 unbounded, abort-blind loops, 0 frame
   caps, 0 `_check_abort`** — upstream code, byte-identical to the mirror, so **bound it at the CALL
   SITE** with `_budgeted(...)`, never by patching upstream.

### THE SERIOUS ONES WORTH CARRYING INTO THE CODE
* **Every resume path `KeyError`s the acceptance** — the leg-2 block is the only writer of the graded
  keys and it is skipped whenever `departure_ready()` is True. ⇒ initialise every graded key to a
  sentinel and read with `.get`.
* **`pc_entered` is a READ, not an action witness** — `respawn_reading()` returns a tuple whenever the
  save-block read succeeds, *whatever value it holds*, so it is True on every non-erroring run. ⇒ latch
  a real witness (a map-change observation), per house rule *a candidate is not an attempt*.
* **5 of 12 fault arms are hollow or predict the wrong outcome** — one faults a branch that provably
  never executes; one pushes a guard in the direction it cannot fire; one is a self-declared no-op;
  one patches a read at only one of its two call sites so the run departs anyway. ⇒ *an arm that
  cannot fail is a sentence that says PASS.* Keep NOHEAL, LOSEDIVE, STATUS, SKIPLEG2, STRANDED, BADEMERGE.
* **A resume from INSIDE the Poké Center is an un-owned strand** two tiles from the exit — the phase
  selector matches no known map and raises. ⇒ treat `(CITY, PC_1F, PC_2F)` as the island side.
* **`navigate_to(UWS,(9,8))` silently no-ops if the dive already lands ON (9,8)** (`walking.py:431,439`),
  and §Ch21 leg-5 PART C measured an arrival of exactly (9,8). ⇒ step off and re-navigate, or assert a
  non-empty path first.
* **A stated bound of "1 re-entry" is 1 PER ATTEMPT** ⇒ 3 per chapter call, 9 under the driver's
  wrapper. *A bounded loop re-entered by its dispatcher is still infinite* (KI-34 burned 23.9M frames).

### ⚠ AND ONE THING NOT TO HARD-CODE
The tile type at `UNDERWATER_ROUTE126 (45,66)` is **UNMEASURED**; two designs predicted different
values. §Ch21 emerged there three times with **no tile guard at all**. ⇒ **REPORT the type, raise only
on a named-bad set** (`Water Door`, `Underwater Blocked Above`, `Seaweed No Surfacing`); an allowlist
can only lose. Tighten after drive 1 prints the real string.

## §4c. ⭐⭐ LEG 4's CONTRACT — 3 BLOCKERS + 5 SERIOUS, FOUND BEFORE THE CODE, TWO SETTLED BY QUERY

An adversarial review of the leg-4 PLAN returned **3 BLOCKERS and 5 SERIOUS** defects. ⭐ **Two of
the blockers were then settled definitively by a 3-query waypoint DUMP (`ch23route` R11) that cost
seconds — each would otherwise have cost a 30-minute drive.**

### ⛔ BLOCKER 1 — `follow_waypoints`' WATERFALL TIMEOUT READS THE MAP NUMBER, NOT THE PLAYER'S y
`walking.py:226-227` indexes `get_player_location()` as `[0][1]`, which is the **map number**
(`MapRSE.__getitem__` returns `value[item]`), so for `EVER_GRANDE_CITY (0,8)` it computes
`195 + (8-59)*42 = -1947` — a **negative budget** that trips on frame 1, re-paths, times out
identically, and dies in 8 no-progress rounds as `NavigationStuckError`. Upstream-origin, never
exercised.
✅ **MEASURED SAFE FOR OUR PATH (R11a):** the 273-wp crossing plan's only actions are **four
`WaypointAction.Surf`** and its last waypoint is `EVER_GRANDE (18,68) is_warp=False` — **no
`Waterfall` waypoint at all.** ⇒ aiming at the BASE never enters that branch.
⇒ **The climb stays HAND-ROLLED**, and that is now a measured necessity rather than a style choice:
`ensure_facing_direction("Up")` + `_budgeted(wait_for_task_to_start_and_finish("Task_UseWaterfall",
"A"), …)`. ⛔ **Never ask `navigate_to` for the TOP.**

### ⛔ BLOCKER 2 — A TRAINER'S SIGHT LINE ABORTS A RAW `navigate_to`, AND THIS CROSSING HITS TWO
`walking.py:479-485` raises `BotModeError` when a waypoint times out while a script is active — and
the countdown keeps ticking through the trainer intro msgbox because the game state stays
`OVERWORLD` (`:253-254`). **Carlee and Harrison are unavoidable** (no safe row exists in the x=101
channel), so a raw `navigate_to` is *guaranteed* to abort, retry the whole 273-wp crossing, and
exhaust its attempts ~30 minutes in.
⇒ **Use `_navigate_riding_out`**, whose docstring names this exact case. ⛔ **NEVER
`expecting_script=True`** to dodge it — that path `return`s, silently ending the crossing mid-ocean
**and reporting success.**

### ⛔ BLOCKER 3 — AIMING AT (18,41) ENDS LEG 4 *INSIDE* VICTORY ROAD — MEASURED
(18,41) is the Victory Road DOOR **warp**, and `navigate_to` overrides its own destination when the
final waypoint is a warp (`walking.py:446-448`). **R11b measured it:** the 16-wp plan's last waypoint
is `map=VICTORY_ROAD_1F coords=(15,40) is_warp=True`.
⇒ leg 4 would silently do **leg 5's** job, and an honest `_at(EVER_GRANDE,(18,41))` grade would FAIL
a perfect run. ✅ **R11c: aiming at the APRON (18,42) returns 15 wp ending `EVER_GRANDE (18,42)
is_warp=False`.** ⇒ **park on the apron; leg 5 takes the warp.** *(Same door-vs-apron split as
`PC_DOOR`/`PC_APRON` in leg 2.)*

### THE FIVE SERIOUS ONES, EACH BUILT INTO THE LEG
* **The Ever Grande heal is LOAD-BEARING, not housekeeping.** Until the bot walks into that Poké
  Center, `lastHealLocation` is still **Sootopolis**, so any whiteout inside Victory Road lands
  **below the falls, inside the crater**, forcing a full re-run of legs 3 AND 4. ⇒ heal, then assert
  `respawn_is_armed(EVER_GRANDE)`.
* **A mid-leg whiteout respawns where this leg cannot plan at all** — Sootopolis has zero
  connections, so every attempt raises `PathFindingError` and reports *"could not reach (18,68)"*,
  the wrong diagnosis. ⇒ phase 0 detects an island-side/underwater position and re-runs leg 3, which
  is idempotent and self-skips.
* **The recovery machinery is weakest exactly at the channel.** `_navigate_riding_out`'s fail-fast
  assumes "nothing can differ between attempts" — false against a *walking NPC*, collapsing its
  effective tries ~10 → 2 — and `navigate_to`'s no-progress window holds **six** positions against
  an **eight**-tile channel, so it can keep resetting while making no progress. ⇒ **stage at
  ROUTE128 (101,26) first**, so a failure names which half failed.
* **The grade needs a PRESENCE witness that cannot be collected as written.** `yield from
  navigate_to(...)` gives the leg no frames, so it can never observe the crossing. ⇒ a `_sampling()`
  wrapper records the map every frame (and is also where the missing `_check_abort()` lives, since
  `navigate_to` never calls it). **ROUTE127 ∈ maps_seen AND ROUTE128 ∈ maps_seen** is the witness.
* ⚠ **`avoid_encounters=True` adds +1000 per WATER tile** — on an all-water crossing it avoids
  nothing and only inflates the search. ⇒ `avoid_encounters=False` for the ocean.

### ⚠ AND ONE FINDING I VERIFIED AND *NARROWED* RATHER THAN RELAYING
The review said the **L19 Zigzagoon** is a live faint-replacement candidate, because
`story_mode.py:210` keys on `(incoming, -outgoing, -hp_fraction, -level)` — ranking HP **fraction
above level** — while `:185` filters only `current_hp > 0`, dropping the parent's
`pokemon_can_battle`. ✅ **Both halves verified by reading.**
⛔ **But its worked example omits Sceptile.** Computed for this party against Water STAB: Sceptile is
`incoming 0.5 / outgoing 2.0` (Grass resists Water; Leaf Blade is super-effective) and **is picked
first**; Wailmer second. The four-way tie that promotes the fresh L19 mule requires **BOTH Sceptile
AND Wailmer** to be out — reachable after a 273-tile crossing, but narrower than stated.
⇒ **The defect is real and the fix is cheap insurance, so it ships** (`_lead_strongest_battler`
before the channel — it exists at `early_game.py:1646`, and no travel leg had ever called it), **but
it is recorded at its true severity.** ‼ *An agent's worked example is an argument, not a
measurement — recompute it before adopting its urgency.*

## §5. WHAT DOES NOT EXIST YET (checked, not assumed)
* `sandbox-pokebot/modules/story/victory_road.py` — **NOT FOUND**
* Any fixture for Ever Grande, Victory Road, Routes 126/127/128, the League or the Elite Four —
  **NONE**; §Ch23 creates the first on that arc.
* ⚠ `wally_done.ss1` is the **Petalburg catching tutorial**, NOT Victory Road Wally. Do not reuse it.
