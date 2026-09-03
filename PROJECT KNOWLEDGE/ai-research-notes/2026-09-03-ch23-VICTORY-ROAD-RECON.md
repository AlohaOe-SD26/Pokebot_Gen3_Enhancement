# §Ch23 — VICTORY ROAD: RECON (build NOT started)

> ‼ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). A **✅** marks a claim I re-opened the
> source and confirmed MYSELF. Produced 2026-09-03 by three concurrent agents (decomp recon, an
> our-code capability audit, and a KI-47 diagnosis that ran alongside), then **§3b re-derived the
> load-bearing routing claim independently, in a committed tool with controls**, and §3c captured
> and verified the start fixture. ⛔ **Still true: no §Ch23 code exists and nothing has been
> DRIVEN.** Everything here is static analysis plus one fixture read.

---

## §0. ⛔⛔ THE HEADLINE — **RETRACTED 2026-09-03. STRENGTH AND ROCK SMASH *ARE* REQUIRED.**

> ⛔⛔ **THIS SECTION READ "THREE FEARED REQUIREMENTS ARE NOT REQUIREMENTS" AND TWO THIRDS OF IT
> WAS WRONG.** An adversarial review refuted it and my own corrected tool reproduces the
> refutation exactly. **Only the FLASH half survives.**
> * ⛔ **The exit is UNREACHABLE on Victory Road 1F alone** (477 tiles reached). The "71-step
>   1F-only route" was an artifact of running the pathfind with **elevation ignored** — with the
>   carried-elevation rule this repo already implements it is 71 steps over 646 tiles, and
>   UNREACHABLE with it. ‼ **Our own planner would have refused that route**, so the number could
>   never have driven.
> * ⛔ **The real route is 1F → B1F → B2F → B1F → 1F**, and on B1F a 2×2 boulder/rock interlock
>   opens only when BOTH moves are held: **23 tiles with neither, 66 with Strength alone, 23 with
>   Rock Smash alone, 298 and the B2F warp with both.** ⇒ **§Ch23 DOES need a boulder solver.**
> * ✅ **Flash is still optional** — but B1F and B2F are now on the CRITICAL path, so the bot walks
>   them dark. That is the opposite of what this heading implied.
> * ⭐ **The one thing that got BETTER: Wally is FREE.** His triggers sit ON the shortest path to
>   the mandatory B1F ladder (29 + 15 = 44 = the direct distance), so the detour costs **0 steps**,
>   not the ~31 claimed below.
> ⇒ Re-derived by me in `tools/story-dev/solve_victory_road.py`, whose self-test now carries **one
> control per model**: the v1 control proved 0 of 1,388 *collision* tiles leaked and said NOTHING
> about elevation, which is exactly where the bug was. The new elevation control fires on **169**
> open tiles. See `08-MISTAKES.md` 2026-09-03.

### (retracted) THE HEADLINE — THREE FEARED REQUIREMENTS ARE NOT REQUIREMENTS, AND OUR OWN CODE WAS WRONG

### ⛔ F1. `chapters.py`'s §Ch23 row named the WRONG ROUTES, and I have corrected it

It read *"Rt 128/132-134 → Ever Grande"*. ✅ **Verified by me against the decomp:**
`EverGrandeCity/map.json` has exactly one connection —
`{"map": "MAP_ROUTE128", "offset": 40, "direction": "left"}`. Routes 132/133/134 run **WEST to
Slateport** and carry the one-way Pacifidlog drift currents; they are not on this path at all.
⇒ the real chain is **Sootopolis → (dive) → Route 126 → 127 → 128 → Ever Grande**.
‼ That row feeds `progress.py`'s readout, so the error would have misled every log review *and*
sent a builder down the wrong ocean. Fixed in `modules/story/chapters.py` (drift 9 → 10).

### ⛔ F2. **RETRACTED IN PART** — Flash is not required; **Strength and Rock Smash ARE.**

The same row claimed *"(Strength/Rock Smash/Flash inside)"*. All three are **optional**:

* ✅ **Verified by me:** `VictoryRoad_1F/map.json` is `requires_flash: false` (B1F and B2F are
  `true`). And `requires_flash` compiles to `MapHeader.cave`, whose ONLY consumer is
  `SetDefaultFlashLevel` (`src/overworld.c:967-979`) — a vision **radius**. Entering unlit gives
  radius 24px, not darkness, and **nothing gates movement, collision, warps or scripts on it.**
* ✅ **STILL TRUE:** all **8** Strength boulders and **6** Rock Smash rocks are on **B1F**; 1F and
  B2F have ZERO of each — counted from 1F's `object_events`, not inferred from a path.
  ⛔ **But "they are all on B1F" is NOT "they are optional"** — that was the inferential leap, and
  it is where this section went wrong. The route MUST cross B1F, so their floor is irrelevant.
* ⛔ **RETRACTED: "the route stays entirely on 1F ... 71 steps".** The exit is **UNREACHABLE** on 1F
  alone. 71 was produced with the elevation rule switched off. ✅ Corrected tool + a control per
  model: `tools/story-dev/solve_victory_road.py --self-test`.
* ⭐ **CORRECTED THE OTHER WAY: Wally's detour costs 0 steps**, not 29 — his trigger is on the
  shortest path to the B1F ladder the route must take (29 + 15 = 44 = direct).

⇒ ⛔ **RETRACTED: "§Ch23 does not need a boulder solver". IT DOES.** Only the HM05/Flash half
survives. ‼ This was billed as *"the single biggest scope reduction available on this
chapter"* — which is exactly why it was the claim most worth attacking, and it did not
survive the attack. **The bigger the scope cut, the harder it must be refuted before use.**

### ⛔ F3. BUT WALLY IS **OFF** THE SHORTEST PATH, AND HE IS THE GRADING FLAG

`FLAG_DEFEATED_WALLY_VICTORY_ROAD` (`0x7E`) is set **only** by
`VictoryRoad_1F_EventScript_WallyEntranceBattle`'s explicit `setflag` — a single writer, so it is a
clean completion signal. But the battle fires from **coord events at (2,23) and (3,23)**, gated on
`VAR_VICTORY_ROAD_1F_STATE == 0`, in a north-west alcove **29 steps** from the entrance.
⭐ **AND IT IS FREE:** (3,23) → the mandatory B1F ladder (9,14) is 15 more, and the direct distance
to that ladder is 44 — so **the detour costs 0 steps**. ⛔ *(This said the chapter "must deliberately
detour to a dead end"; both halves were wrong — it is not a dead end and it is not a detour.)*
⇒ **the chapter walks through Wally's trigger on its way to the ladder it has to take anyway.**
⚠ Do not confuse him with the **exit** Wally at (31,9) (`TRAINER_WALLY_VR_2`), who is hidden until
the Hall of Fame and does NOT set the flag.

**His party** (`TRAINER_WALLY_VR_1`, no held items, explicit moves, **2× Full Restore**,
`AI_SCRIPT_CHECK_BAD_MOVE | TRY_TO_FAINT | CHECK_VIABILITY`):
Altaria 44 · Delcatty 43 · Roselia 44 · Magneton 41 · **Gardevoir 45 (IV 250)**.

---

## §1. THE ROUTE, LEG BY LEG

| # | from | mechanism | to |
|---|---|---|---|
| 1 | Sootopolis (31,33) | walk S, Surf | the crater lake |
| 2 | dive pool x24-32, y53-55 | **DIVE** (needs Badge 7 — held) | `Underwater_SootopolisCity (9,6)` |
| 3 | (9,8)/(10,8) `MB_WATER_SOUTH_ARROW_WARP` | swim S | `Underwater_Route126 (45,65)` |
| 4 | (45,65) `MB_WATER_DOOR` | **surface** | `Route126 (45,65)` |
| 5-7 | Route 126 → 127 → 128 | map connections | `EverGrandeCity x=0, y66-72` |
| 8 | Ever Grande x15-26, y60-67 | **WATERFALL, climbing UP** | the north half |

⛔ **The Sootopolis crater has NO connections and NO land exit** — the way out is a *scripted dive
warp* (`SootopolisCity/scripts.inc`: `setdivewarp MAP_UNDERWATER_SOOTOPOLIS_CITY, 9, 6`), paired in
the reverse direction. A `connections`-based planner will not see it.

**The waterfall is the only one on the route (96 tiles; Routes 126/127/128 have zero).** It needs
`FLAG_BADGE08_GET` **and** `IsPlayerSurfingNorth()` (`src/field_control_avatar.c:448-459`) — so
**direction is load-bearing**. One use carries all 8 rows.
⭐ **AND IT IS TWO-WAY:** the tiles are collision 0 / elevation 1, and surfing south onto one
triggers `ForcedMovement_PushedSouthByCurrent`. **No leg of this route strands the bot** — no
currents anywhere on 126/127/128/Ever Grande, and the dive is paired.

---

## §2. WHAT *WE* CANNOT DO YET — the real work

⭐ **§Ch23 IS AN ORCHESTRATION BUILD, NOT A NEW-PRIMITIVE BUILD.** ✅ Both verified by me:
`map_path.py:829-832` already routes through waterfall tiles (`can_waterfall()` gates the northward
climb; descending south is free), and `strength_push` (`early_game.py:7884`) is built and
idempotent. The blocker is elsewhere:

### ⛔ NOBODY IN THE PARTY KNOWS WATERFALL, AND ONLY ONE MON *CAN* LEARN IT

✅ **Verified by me from `src/data/pokemon/tmhm_learnsets.h`:**

| mon | lvl | WATERFALL | FLASH |
|---|---|---|---|
| Sceptile | 51 | no | **yes** |
| Zigzagoon | 19 | no | no |
| Swellow | 42 | no | no |
| **Wailmer** | 40 | **YES** | no |
| Mightyena | 44 | no | no |
| Castform | 36 | no | **yes** |

⇒ **Wailmer is the only candidate — and its moveset is FULL** (Dive / Surf / Water Gun / Rollout),
of which **Dive and Surf are HMs and cannot be forgotten in Gen 3**. ⇒ **teaching Waterfall REQUIRES
the forget-a-move flow, and the only two legal victims are Water Gun and Rollout.**
‼ ✅ And `hm_learner_slot` (`early_game.py:4316`) picks by *"already knows it"* then highest level —
it **never inspects free move slots**. It will pick Wailmer (correctly, as the only compatible mon)
and hand the teach flow a full moveset.
⇒ **the first §Ch23 leg is "teach Waterfall to Wailmer", and its risk was the FORGET menu.**
✅✅ **DRIVEN 2026-09-03 AND IT WORKS** (`--driver ch23teach` from `post_badge8.ss1`,
`ACCEPTANCE: PASS`, `frames=1896`): production picked slot 3 by itself, **Rollout** was the move
lost, Waterfall was gained, and ⭐ **Dive and Surf both SURVIVED** — the safety property that
matters, since Wailmer is the sole Dive carrier and Dive is the only way out of the crater.
Predictions were filed before the run in `2026-09-03-ch23-WATERFALL-TEACH-PREDICTIONS.md`; all
seven held. ⚠ **But `#26-surfteachchain` D3 did NOT fire rather than being fixed** — its hazard is
re-entry, and this run never re-entered. D3 stays open.
*(Flash, if ever wanted, can only go on Sceptile or Castform — Castform is the natural carrier since
all four of its moves are forgettable. But per F2 it is never needed.)*

### ⚠ FOUR PATHFINDING KIs ARE ARMED ON THIS ROUTE
**KI-72** (the planner cannot see `Underwater Blocked Above` / `Seaweed No Surfacing`, and this
chapter dives — pick the surfacing tile EXPLICITLY and assert its `tile_type` positively, the
`seafloor_cavern.py:318-322` pattern), **KI-73** (layout swaps), **KI-53**, **KI-60**.
‼ A static `calculate_path` FAIL is **not** automatically a verdict — `navigate_to_anywhere` routes
the warp graph and re-plans per leg (`early_game.py:8563`).

---

## §3. HAZARDS, RANKED

1. ⚠ **Route 128, column x=101** — Carlee (101,29) and Harrison (101,22), both sight **4**, both
   `WALK_UP_AND_DOWN` with range 3. The column is passable only at y=22..29 and their bands cover
   it; a gap exists only on phases where one faces away. ⚠ AGENT-INFERRED (facing is dynamic) —
   **this is the one place on the water route that needs a live probe.**
2. ⛔ **`allow_escaping: false`** on Sootopolis, Routes 126/127/128, every underwater map, and Ever
   Grande City — but **`true`** on all three Victory Road floors. ⇒ the ocean legs are the
   no-escape stretch, not the cave.
3. ⭐ **The Ever Grande Poké Center (27,48) is reachable BEFORE Victory Road** — same walkable region
   as the waterfall pool and the cave entrance, entered by walking NORTH onto the door at (27,49).
   ⇒ the healing gap is only *Sootopolis → waterfall → Ever Grande*, and the cave can be entered
   from a full heal.
4. ⚠ `Route128/scripts.inc` has a live `ON_FRAME` Kyogre scene gated on `VAR_ROUTE128_STATE == 1`.
   Post-Rayquaza it should already be 2 — ⛔ **read it live rather than assuming.**
5. ✅ **Trainer sight is a 1-tile LINE and `sight=0` can never initiate** (`src/trainer_see.c`), which
   retires Route 127's three fishermen and Route 128's Wayne as talk-only.
6. ⛔ **SUPERSEDED — this said "since the exit route stays on 1F, only those are candidates".** Victory Road 1F does have 5 sight-trainers, but **B1F and B2F are now on the mandatory path and NEITHER HAS BEEN AUDITED** for trainers or hazards. ‼ That audit is owed before the build — this bullet would otherwise have scoped it away.

---

## §3b. ⛔⛔ RE-DERIVED BY ME, WITH CONTROLS — **AND I GOT IT WRONG. THE SCOPE CUT DOES NOT HOLD.**

> ⛔⛔ **THIS SECTION HEADING READ "THE SCOPE CUT HOLDS" AND THE SECTION CLAIMED INDEPENDENT
> CONFIRMATION. BOTH WERE WRONG.** My tool's v1 compared elevations TILE-TO-TILE and treated any
> elevation-15 tile as a free pass, so it crossed 1F's multi-level bridge and welded two regions
> together. The correct rule — which this repo already ships at `map_path.py:859` and `:1039` — is a
> **carried** elevation that a 15-tile PRESERVES. Corrected: **the exit is UNREACHABLE on 1F alone**
> and **Strength and Rock Smash are BOTH required**. See §0 and `08-MISTAKES.md` 2026-09-03.
> ‼ **The controls below are real and they passed — about COLLISION.** The bug was in ELEVATION,
> which nothing here tested. ⇒ **a control tests the failure mode it was written for and no other.**
> The tool now carries one control per model; the new elevation control fires on **169** open tiles.
>
> **The two numbers in this section that SURVIVE:** the boulder/rock CENSUS (8 + 6, all on B1F; 1F
> and B2F have none) — counted from object lists, not from a path — and the byte-length assertions.
> ⛔ But "they are all on B1F" was never the same as "they are optional", and that inferential leap
> is precisely what went wrong.

### (retracted) RE-DERIVED BY ME, WITH CONTROLS — THE SCOPE CUT HOLDS

⛔ The 72-step claim was the load-bearing agent number and §4.3 said I had NOT re-derived it. I have
now, in a committed, re-runnable tool: **`tools/story-dev/solve_victory_road.py`** (offline, decodes
the decomp layouts itself). *Right numbers in an un-re-runnable script are NOT PROVEN — the same
rule that produced `probe_skypillar_clean_layout.py`.*

**Byte lengths ASSERTED before a single tile was decoded** (this is the guard against the silent
binary corruption in §5): 1F **4140** = 46×45×2 ✅ · B1F **2852** = 46×31×2 ✅ · B2F **2852** ✅.

| question | agent said | **I measured** | verdict |
|---|---|---|---|
| Strength boulders on **1F** | 0 (all on B1F) | **0** | ✅ CONFIRMED — 1F's `object_events` are 5 trainers, 2 Wallys, 2 item balls and nothing else |
| Rock Smash rocks on **1F** | 0 | **0** | ✅ CONFIRMED |
| where they all are | B1F | **B1F: 8 boulders + 6 rocks. B2F: 0 of each** | ✅ CONFIRMED, with coordinates |
| entrance (15,40) → exit (39,5), objects blocking | 72 steps | ~~71 steps~~ ⛔ **BOTH WRONG — the exit is UNREACHABLE on 1F** | ⛔ **REFUTED.** 71/72 are what you get with elevation OFF |
| Wally's trigger from the entrance | "~31 steps" | **(3,23) = 29, (2,23) = 30** | ✅ counts stand — ⭐ **and the DETOUR COST is 0**: 29 + 15 to the mandatory ladder = 44 = the direct distance |

‼ **I am reporting 71 and 29, not rounding to the agent's 72 and 31.** Two independent derivations
agreeing on the STRUCTURE while differing by a step is the corroboration worth having — and this
project has a logged case where agreeing on a count while disagreeing on the path was *stronger*
evidence than agreeing on both. The step counts are not load-bearing; **"zero obstacles on the exit
route" is**, and that is confirmed from the object list rather than inferred from a path.

⇒ ⛔ **RETRACTED — see the box at the top of this section.** Only *no HM05 side-quest* survives; **§Ch23 DOES need a boulder solver.** The line below it ("confirmed independently") was the most confident sentence in this note and the most wrong.

**THE CONTROLS, because a search that reaches everything proves nothing** (`--self-test`, all PASS):
* ✅ **negative:** 0 of **1,388** collision tiles are reachable — the wall-walking failure mode this
  project logged on 2026-09-03 is absent.
* ✅ **fault:** with collision ignored, a previously-unreachable wall becomes reachable ⇒ the refusal
  comes from the COLLISION MODEL, not from a broken search.
* ✅ **negative:** an off-grid start RAISES rather than quietly returning nothing.
* ✅ **positive:** the entrance reaches itself in 0 steps and the exit in 71.

⚠ **WHAT THIS DOES NOT SAY, stated so nobody reads it as more:** it is a TILE-GRAPH answer. It says
the route EXISTS; it does not say `calculate_path` will find it, and it models **no trainer sight
lines**. Both remain live questions for a live probe.

## §3c. ✅ THE START FIXTURE IS CAPTURED — AND IT ARRIVES HURT

`saves/post_badge8.ss1`, md5 **`723d94cc899f3ad2c75fbf49f9192984`**, 397,312 bytes. Written by
`CH22_CAPTURE=post_badge8.ss1 … --driver ch22chapter` **only on the full PASS**, so the file's
existence is the acceptance record.
✅ Verified from the FILE (not the driver's log) with `probe_anchor_inventory.py`, whose own
positive control passed first (`oldale` 0 badges vs `post_winona` 6):
```
post_badge8.ss1   badges=12345678   OVERWORLD   SOOTOPOLIS_CITY (31, 33)
party: Sceptile L51, Zigzagoon L19, Swellow L42, Wailmer L40, Mightyena L44, Castform L36
HP 428/701 (61%), 1 FAINTED  ‼ CANNOT SURVIVE A JOURNEY — heal before using this as a start point
```
⛔⛔ **THAT WARNING IS THE FINDING, NOT A DEFECT IN THE FIXTURE.** §Ch22 genuinely hands over a
party at **61% with one member fainted** — contrast `post_hm07.ss1`, which starts §Ch22 at 91% with
none down. ⇒ **§Ch23's FIRST act must be a heal**, and the Sootopolis Poké Center is 23 waypoints
away and measured reachable. ‼ And §Ch23's own preflight must assert the party AFTER that heal, by
PID, exactly as §Ch22's does — a chapter that begins a no-escape ocean crossing on a fainted party
has no way back.

## §3d. ⭐⭐ PRODUCTION'S OWN PLANNER ADJUDICATES — AND IT SIDES WITH THE CORRECTION

`--driver ch23route` (READ-ONLY; it moves nothing and presses nothing, so it costs a few frames and
cannot derail the fixture) asks `calculate_path` — **the planner the bot will actually use** — the
same questions my offline tool answered. This is the recorded prevention rule executed: *when a tool
answers a question production also answers, DIFF THEM.* Evidence:
`evidence/2026-09-03-ch23route-PLANNER-READINGS.txt`.

| question | my v1 (wrong) | my v2 (corrected) | **PRODUCTION** |
|---|---|---|---|
| 1F (15,40) → exit (39,5) | 71 steps | **UNREACHABLE** | ⭐ **`PathFindingError` — "Could not find a path"** |
| 1F (15,40) → Wally (3,23) | 29 | 29 | **29 waypoints** |
| 1F (15,40) → B1F ladder (9,14) | — | 44 | **44 waypoints** |
| Wally (3,23) → ladder (9,14) | — | 15 | **15 waypoints** |

⇒ **THREE-WAY AGREEMENT on the corrected answer** (my fixed tool, the adversarial reviewer, and the
shipped planner), and **production REFUTES the original**. 29 + 15 = 44 = the direct distance, so
**Wally's detour costs 0 steps — now confirmed by the authority, not just by my own model.**

## §3e. ⭐ THE BAG'S HMs, DUMPED FOR THE FIRST TIME IN THIS PROJECT

`04-HANDOFF.md` said *"no probe in this tree dumps them, so 'do we hold HM05 Flash?' is genuinely
UNMEASURED."* It is measured now, by item identity:

| HM01 Cut | HM02 Fly | HM03 Surf | HM04 Strength | HM05 Flash | HM06 Rock Smash | HM07 Waterfall | HM08 Dive |
|---|---|---|---|---|---|---|---|
| **0** | **1** | 1 | 1 | **0** | 1 | 1 | 1 |

* ⛔ **HM05 FLASH IS NOT HELD.** Harmless — Flash is optional (§0 F2) — but it is now a measurement
  rather than an assumption, and it would have been a real blocker had the retraction gone the
  other way.
* ⭐ **HM02 FLY *IS* HELD** — worth knowing, because the adversarial review found that Victory
  Road's exit terrace cannot be walked back down to the Poké Center or Route 128. Fly is allowed on
  `MAP_TYPE_CITY`, so Ever Grande is escapable that way. ⚠ **No party member knows Fly**, so this is
  a capability the bot *could* acquire, not one it has.
* HM01 Cut is not held either; §Ch23 does not need it.

**And the carriers, read from the party by move identity** (post-teach):
Surf → Zigzagoon + Wailmer · Dive → **Wailmer only** · **Waterfall → Wailmer only** ·
Strength → Sceptile · Rock Smash → Sceptile · Flash → nobody.
⇒ ✅ **§Ch23 already carries every field move the route needs** — including the Strength and Rock
Smash the retraction made mandatory, both on Sceptile. ⛔ But Wailmer now carries **three** of them
(Dive, Surf, Waterfall) and is the sole carrier of two; it is the single point of failure for the
whole chapter.

## §3f. TWO MORE READINGS THAT CHANGE HOW THE ROUTE MUST BE BUILT

* ✅ **`ROUTE128_STATE = 2`** — the `ON_FRAME` Kyogre scene fires only at 1, so it is SPENT and will
  not ambush the swim. The recon said to read this rather than assume it; it is read.
* ⛔ **`calculate_path` IS CONNECTION-GRAPH ONLY.** Both cross-map legs refuse with *"Source … and
  destination … are not on connected maps (note that warps don't count.)"* ⇒ **the §Ch23 route must
  be driven with `navigate_to_anywhere`, which routes the WARP graph and re-plans per leg**, and
  `calculate_path` is only good for within-map questions. ‼ This is KI-53's shape and is NOT a
  verdict about reachability — it is the wrong instrument for that question.
* ✅ **Ever Grande (18,41) → the Poké Center apron (27,49) = 23 waypoints**, confirming the heal is
  reachable from the Victory Road entrance side before the cave.

## §4. WHAT MUST HAPPEN BEFORE ANY §Ch23 CODE

1. ✅ **DONE — the start fixture is captured and verified.** `saves/post_badge8.ss1`
   (md5 `723d94cc899f3ad2c75fbf49f9192984`). See §3c — ⚠ it arrives at 61% HP with one member
   FAINTED, so §Ch23 opens with a heal.
2. ✅ **DONE — the bag is dumped (§3e).** HM05 Flash is **NOT** held (harmless: Flash is
   optional), HM02 Fly **is**, and every field move the route needs is already carried.
3. ⛔⛔ **SUPERSEDED — AND IT IS THE MOST IMPORTANT LINE IN THIS LIST.** This read *"DONE —
   re-derived with controls: 71 steps, and ZERO obstacles on 1F. The scope cut is confirmed."*
   **RETRACTED** (§0, §3b): the exit is **UNREACHABLE on 1F alone**, the route is
   1F → B1F → B2F → B1F → 1F, and **§Ch23 DOES need a boulder solver.** ✅ The re-derivation with
   the corrected carried-elevation model IS done — `solve_victory_road.py --self-test`, now with
   one control per model.
4. ⚠ **A live probe of the Route 128 x=101 pinch.**

## §5. A TOOLING FACT WORTH KEEPING

⛔ **`gh api … --jq '.content' | base64 -d` SILENTLY CORRUPTS BINARY on this machine** — it
UTF-8 re-encodes bytes ≥ 0x80, so a 7,200-byte `map.bin` decodes to 9,433 bytes. It is fine for
TEXT (`scripts.inc`, `.h`, `.json`) and this project has used it correctly for those all along.
⇒ **for `map.bin` / `metatile_attributes.bin`, fetch from `raw.githubusercontent.com` and
ASSERT THE BYTE LENGTH.** A silent corruption in tile data would produce a confident, wrong map.
