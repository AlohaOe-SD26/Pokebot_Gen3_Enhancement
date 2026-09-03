# §Ch23 — VICTORY ROAD: RECON (build NOT started)

> ‼ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). A **✅** marks a claim I re-opened the
> source and confirmed MYSELF. Produced 2026-09-03 by three concurrent agents (decomp recon, an
> our-code capability audit, and a KI-47 diagnosis that ran alongside). ⛔ Nothing here has been
> driven; the whole chapter is unbuilt.

---

## §0. THE HEADLINE — THREE FEARED REQUIREMENTS ARE **NOT REQUIREMENTS**, AND OUR OWN CODE WAS WRONG

### ⛔ F1. `chapters.py`'s §Ch23 row named the WRONG ROUTES, and I have corrected it

It read *"Rt 128/132-134 → Ever Grande"*. ✅ **Verified by me against the decomp:**
`EverGrandeCity/map.json` has exactly one connection —
`{"map": "MAP_ROUTE128", "offset": 40, "direction": "left"}`. Routes 132/133/134 run **WEST to
Slateport** and carry the one-way Pacifidlog drift currents; they are not on this path at all.
⇒ the real chain is **Sootopolis → (dive) → Route 126 → 127 → 128 → Ever Grande**.
‼ That row feeds `progress.py`'s readout, so the error would have misled every log review *and*
sent a builder down the wrong ocean. Fixed in `modules/story/chapters.py` (drift 9 → 10).

### ⛔⛔ F2. FLASH IS NOT REQUIRED. Neither is STRENGTH. Neither is ROCK SMASH.

The same row claimed *"(Strength/Rock Smash/Flash inside)"*. All three are **optional**:

* ✅ **Verified by me:** `VictoryRoad_1F/map.json` is `requires_flash: false` (B1F and B2F are
  `true`). And `requires_flash` compiles to `MapHeader.cave`, whose ONLY consumer is
  `SetDefaultFlashLevel` (`src/overworld.c:967-979`) — a vision **radius**. Entering unlit gives
  radius 24px, not darkness, and **nothing gates movement, collision, warps or scripts on it.**
* **All 8 Strength boulders and 6 Rock Smash rocks are on B1F.** 1F and B2F have none.
* A **72-step entrance → exit route stays entirely on 1F**, with every boulder and rock left in
  place, all 7 NPCs blocking, and both Wally trigger tiles avoided (agent's 3-floor pathfind, same
  answer with elevation modelled and ignored — so not a modelling artifact). ⚠ AGENT-DERIVED, not
  re-verified by me; **verify before building on the step count.**

⇒ **§Ch23 does not need an HM05 side-quest, and it does not need a boulder solver.** That is the
single biggest scope reduction available on this chapter, and it came from reading the game.

### ⛔ F3. BUT WALLY IS **OFF** THE SHORTEST PATH, AND HE IS THE GRADING FLAG

`FLAG_DEFEATED_WALLY_VICTORY_ROAD` (`0x7E`) is set **only** by
`VictoryRoad_1F_EventScript_WallyEntranceBattle`'s explicit `setflag` — a single writer, so it is a
clean completion signal. But the battle fires from **coord events at (2,23) and (3,23)**, gated on
`VAR_VICTORY_ROAD_1F_STATE == 0`, in a north-west alcove ~31 steps from the entrance that the
72-step exit route never touches. ⇒ **the chapter must deliberately detour to a dead end.**
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
⇒ **the first §Ch23 leg is "teach Waterfall to Wailmer", and its risk is the FORGET menu.**
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
6. Victory Road 1F has 5 sight-trainers; since the exit route stays on 1F, only those are candidates.

---

## §4. WHAT MUST HAPPEN BEFORE ANY §Ch23 CODE

1. ⛔ **CAPTURE THE START FIXTURE.** Every chapter so far pinned one; §Ch23 has none.
   `CH22_CAPTURE=post_badge8.ss1 … --driver ch22chapter` (gated on the full PASS, refuses to
   overwrite).
2. ⛔ **MEASURE THE BAG.** No probe in this tree dumps HMs, so *"do we hold HM05 Flash?"* is
   genuinely UNMEASURED. Per F2 it should not matter — which is exactly why it is cheap to check
   and worth checking once rather than assuming twice.
3. ⚠ **Re-verify the 72-step 1F route myself.** It is the load-bearing agent claim in this note and
   it is the one I have NOT re-derived.
4. ⚠ **A live probe of the Route 128 x=101 pinch.**

## §5. A TOOLING FACT WORTH KEEPING

⛔ **`gh api … --jq '.content' | base64 -d` SILENTLY CORRUPTS BINARY on this machine** — it
UTF-8 re-encodes bytes ≥ 0x80, so a 7,200-byte `map.bin` decodes to 9,433 bytes. It is fine for
TEXT (`scripts.inc`, `.h`, `.json`) and this project has used it correctly for those all along.
⇒ **for `map.bin` / `metatile_attributes.bin`, fetch from `raw.githubusercontent.com` and
ASSERT THE BYTE LENGTH.** A silent corruption in tile data would produce a confident, wrong map.
