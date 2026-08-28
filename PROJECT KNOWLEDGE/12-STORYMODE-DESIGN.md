# Story-Mode Bot — Deep Design (Pass 1 + Pass 2 + Pass 3 + Pass 4 verified)

> ### ⚠ STUB MARKER — unverified AI-research notes exist for the unbuilt chapters
> `PROJECT KNOWLEDGE/ai-research-notes/` holds notes written by **AI research agents**
> (Gemini) covering Mt. Pyre → Champion, the Magma/Aqua hideouts, gyms 7-8, Victory Road,
> HM gating, missable one-time events, overworld obstacle mechanics, and a story flag/var
> reference — plus the healing-point and legendary dossier in `18-*`.
>
> They are **POSSIBLE, NOT A SOURCE OF TRUTH** (user directive, 2026-07-24). Read
> `ai-research-notes/00-READ-THIS-FIRST.md` before using any of it. Nothing there may become
> code, or overwrite THIS document, until verified against the ROM/decomp. **Where a note
> contradicts this file, this file wins** until the note is proven. One note in the first
> batch was already confidently wrong on its central question (it denied the existence of
> `ROUTE111_OLD_LADYS_REST_STOP`, which is in our own `map_data.py`).

## ⭐ STORY PROGRESS LEDGER (what's built vs next — read this first) — 2026-07-21
Code: `sandbox-pokebot/modules/story/early_game.py` (segment functions) wired into
`plugins/custom_modes/story_mode.py` `StoryMode._play` (flag-gated, idempotent resume).
Status key: ✅ built + validated · 🚧 scaffold/partial · 📋 mapped, not built · ⬜ not mapped.

| Ch | Beat | Code (fn) | Completion signal | Status |
|----|------|-----------|-------------------|--------|
| 1 | Intro → starter → Route 103 rival → Pokédex | `help_birch_and_choose_starter`, `fight_route103_rival`, `return_to_lab_and_get_pokedex` | `RECEIVED_POKEDEX_FROM_BIRCH` | ✅ |
| 2 | Petalburg → Wally catch tutorial | `do_petalburg_gym_and_wally_tutorial` | Wally flags | ✅ |
| 3 | Route 104 → Petalburg Woods → Rustboro | `travel_to_petalburg`, `travel_to_petalburg_woods`, `cross_petalburg_woods`, `travel_route104_north_to_rustboro` | in Rustboro | ✅ |
| 4 | **Gym 1 — Roxanne** | `catch_starter_team` + `_prepare_for_fight` + `do_rustboro_gym` | `BADGE01_GET` | ✅ |
| 5a | Devon Goods (theft → Rusturf → recover) | `recover_devon_goods` | `RECOVERED_DEVON_GOODS` | ✅ |
| 5b | Return goods → **PokéNav + Match-Call tutorial** | `return_devon_goods_and_get_pokenav`, `handle_pokenav_match_call_tutorial` (faithful; state-write fallback) | `RECEIVED_POKENAV`, `RUSTBORO_CITY_STATE=7` | ✅ (real-HW confirmed) |
| 5c | **Rustboro rival** (type-lead + level-floor + heal + attempt-cap) | `_play §5c` + `_lead_best_matchup`, `train_team`, `fight_rustboro_rival` | `DEFEATED_RIVAL_RUSTBORO` | ✅ (fresh run won) |
| 6 | Sail to Dewford (via Petalburg Woods → beach → Briney) | `sail_to_dewford` + `_talk_to_wandering_npc` | on `DEWFORD_TOWN` | ✅ (2026-07-22; driver `saildewford` + real `_play`) |
| 7 | Granite Cave (Steven's Letter, TM47) + **Gym 2 — Brawly** | `deliver_stevens_letter` (+`_walk_warp_chain`), `do_dewford_gym` | `DELIVERED_STEVEN_LETTER`, `BADGE02_GET` | ✅ (2026-07-22; zero-derail run dewford→badge) |
| 8a | Sail to Slateport (dock Briney → Route 109 gauntlet → PC) | `sail_to_slateport` | on `SLATEPORT_CITY`, healed | ✅ (2026-07-22; zero-derail run brawly_done→Slateport) |
| 8b | Slateport: Devon Goods → Capt. Stern (Shipyard/Dock → Museum → 2 grunt battles) | `deliver_devon_goods_to_stern` | `DELIVERED_DEVON_GOODS` | ✅ (2026-07-22; KI-11 resolved via Dock; full run validated) |
| 9a | Route 110 north + rival battle | `travel_route110_and_fight_rival` | `route110_rival_beaten()` = **VAR_ROUTE110_STATE ≥ 1** (vanilla sets NO named flag — "DEFEATED_RIVAL_ROUTE_110" was a phantom name) | ✅ (2026-07-22; run 6+) |
| 9b | Mauville: Wally unblocks the gym door | `fight_wally_mauville` | `DEFEATED_WALLY_MAUVILLE` (real flag 190, decomp-confirmed) | ✅ (2026-07-22; run 6+) |
| 9c | Mauville Gym: prep (Route 117 train, band 20-24) → switch maze → Wattson | `do_mauville_gym` (LIVE-grid two-config BFS solver) + Segment 9c prep | `BADGE03_GET` | ✅ (2026-07-22 run 14: trained (2 evolutions), maze solved, **Wattson BEATEN — Dynamo Badge**; checkpoint `wattson_done.ss1` verified) |
| 10a | HM06 Rock Smash (Mauville SE house) | `get_rock_smash_hm` (+live-grid gym exit, `_exit_small_interior`) | `RECEIVED_HM_ROCK_SMASH` | ✅ (2026-07-22 overnight; `rocksmash_got.ss1`) |
| 10b | Teach Rock Smash to the mule (starter) | `teach_hm_move` (probed overworld bag→party→summary chain) | party knows Rock Smash | ✅ (2026-07-22 overnight; `rocksmash_taught.ss1`) |
| 10c | Route 111 rocks → Fiery Path → Route 113 → Fallarbor | `travel_to_fallarbor` + `_smash_rock` | in Fallarbor, healed | ✅ (2026-07-22 overnight; `fallarbor.ss1`) |
| 11a | Meteor Falls Magma cutscene (unblocks the Cable Car) | `do_meteor_falls_scene` | `HIDE_ROUTE_112_TEAM_MAGMA` | ✅ (2026-07-22 overnight; `meteorfalls_done.ss1`) |
| 11b | Cable Car → Mt. Chimney Magma chain (Maxie) + meteorite | `do_mt_chimney` | `DEFEATED_EVIL_TEAM_MT_CHIMNEY` | ✅ (2026-07-22 overnight) |
| 11c | Jagged Pass descent → Lavaridge | `do_jagged_descent` | in Lavaridge, healed | ✅ (2026-07-22 overnight; `lavaridge.ss1`) |
| 11d | Lavaridge trapdoor gym → **Flannery, HEAT BADGE** | `do_lavaridge_gym` | `BADGE04_GET` | ✅ (2026-07-23; `flannery_done.ss1`) |
| 12 | Lavaridge → Petalburg (Norman, **Gym 5**) → HM03 Surf (Go-Goggles/desert SKIPPED) | — | `BADGE05_GET` + `RECEIVED_HM_SURF` | 🗺️ DEEP-MAPPED 2026-07-23 (§Ch12 build spec) — ready to build |
| 13+ | Surf arc: Rt 118 → Weather Institute → Fly (Rt 119 rival) → Fortree (Gym 6) → … | — | — | ⬜ (§Ch12+ leads) |

**You are at the Ch10 boundary (2026-07-22).** `wattson_done.ss1` = Mauville Gym (5,3),
BADGE03_GET + DEFEATED_MAUVILLE_GYM + DEFEATED_WALLY_MAUVILLE verified. Next: Ch10 —
HM06 Rock Smash (Mauville SE house) → Route 111/112 → Fiery Path (§Ch10–13 roadmap;
run /validate-docs + audit_flag_names.py before building).
CRITICAL Ch9c lesson: the gym barriers exist ONLY in the LIVE grid (gBackupMapLayout);
get_map_data/calculate_path read the ROM's static layout and are blind to setmetatile —
the solver reads the live grid and judges every leg by arrival. Applies to EVERY
runtime-modified map ahead (Trick House, ice puzzles, Sky Pillar cracks...).

### §Ch9 — Route 110 → Mauville → Gym 3 Wattson (validated sequencing, 2026-07-22)
Source: Gemini external-research PoC (the /escalate-sequence primer flow) + my decomp
spot-checks. Legend: `✓ decomp-verified` (I confirmed it), `✓ external` (Gemini, cited,
plausible — VERIFY AT BUILD), `⚠ probe live`.
1. **Route 110 northbound ON FOOT** (no bike → the ground dirt path; Cycling Road needs the
   Mach Bike). Trick House: fully optional, doesn't interrupt. `✓ external`
2. **Rival battle — MANDATORY choke-point**: coord triggers `Route110_EventScript_
   RivalTrigger1/2/3` span the dirt path `✓ decomp (triggers exist; VAR_ROUTE110_STATE=1
   set on exit)`; gate = `VAR_ROUTE110_STATE==0` `✓ external` — **⚠ probe VAR_ROUTE110_STATE
   in stern_done.ss1 before building**. Rival team ~L18-20, starter-dependent (vs our
   Mudkip start: Wingull 18 / Shroomish 18 / Grovyle 20) `✓ external
   (src/data/trainer_parties.h)`. Win sets VAR_ROUTE110_STATE=1 + Itemfinder
   (`FLAG_RECEIVED_ITEMFINDER`) `✓ external`. Mirror the Rustboro-rival prep pattern
   (type-aware lead vs Grovyle = Taillow/Dustox-class; heal; attempt-cap).
3. **Gabby & Ty CORRECTION (our old doc was wrong):** the Slateport pair at (28,14) is a
   TEXT interview only (`SlateportCity_EventScript_GabbyAndTy`); their FIRST DOUBLE battle
   is on ROUTE 111, not here. `✓ external` (trainer doubles now attack-through anyway).
4. **Mauville: Wally gates the gym door** — he + his uncle stand at the gym entrance; TALK
   to Wally → mandatory battle (`TRAINER_WALLY_MAUVILLE`, Ralts ~L16 `✓ external`); win →
   `FLAG_DEFEATED_WALLY_MAUVILLE` + Scott scene (`VAR_SCOTT_STATE`++ ,
   `FLAG_ENABLE_FIRST_WALLY_POKENAV_CALL`, `VAR_WALLY_CALL_STEP_COUNTER=0`)
   `✓ decomp-verified (script names, flags, Scott)`. ⚠ probe the door/NPC tiles live.
5. **Mauville Gym**: floor-switch coord_events toggle the electric barriers (walk over
   them; trainer battles do NOT open barriers) `✓ external` — ⚠ probe the switch tiles +
   barrier layout live (grid probe like the museum). **Wattson (Emerald)**: Voltorb 20 /
   Electrike 20 / Magneton 22 / Manectric 24, holds 2 Super Potions `✓ external
   (TRAINER_WATTSON_1)` — VERIFY at build. Ground moves ideal (Marshtomp's Mud Shot —
   Magneton is Electric/Steel: Ground 4×… but Magneton levitates? NO — Magnet Pull/Sturdy
   ability, Ground hits). Prep: level-floor ~20-22, lead Marshtomp (Ground immunity to
   Electric); attempt-cap.
6. **Completion**: `FLAG_BADGE03_GET` (+ `FLAG_DEFEATED_MAUVILLE_GYM`, TM34) `✓ external`;
   BADGE03 enables Rock Smash field use (needed later for Route 111+). `✓ external`

### §Ch12 — Lavaridge (post-HEAT BADGE) → Petalburg (Norman, Gym 5) → HM03 Surf — BUILD SPEC (deep-mapped 2026-07-23)
> Tags: ✓ = ROM-probed / flag-table-verified this session; ⚠ = external-research lead
> (Gemini 3.1 Pro, archived tools/story-dev/research-gemini-ch12-2026-07-23.md), decomp-
> verify at build time. Recon tools: `petalburg_gym_probe.py`, `mapfacts.py`.

**Frontier entry state:** in Lavaridge Town (9,7), `BADGE04_GET` set, 4 badges. Norman's
gym only opens with 4 badges — now satisfied.

- **Go-Goggles are OPTIONAL — SKIP them for the Norman critical path (✓ structurally
  verified).** They gate only the Route 111 DESERT (Mirage Tower / fossils / Winstrates),
  which is not on the route to Petalburg. Proof: `ROUTE111.connections` = South→Mauville,
  West→Route112/113 (probed); the desert is an internal mid-section the Mauville-side path
  never enters. `RECEIVED_GO_GOGGLES` (221) is never required to reach or beat Norman.
  (⚠ lead: the Go-Goggles come from the RIVAL just outside the Lavaridge gym after
  Flannery — not the hot-springs woman. Irrelevant unless we later want the desert/fossils
  → #24-optional.)

- **‼ RE-CORRECTION (static recon 2026-07-24, ch12_static_recon*.py — supersedes the
  2026-07-23 Fiery-Path note): the DIRECT route works; the Fiery Path is USELESS here.**
  The Fiery tunnel's doors connect LOWER Route 112 (11,36) to the ROUTE-113-SIDE section
  (22,10) — it goes north, not toward Mauville. The direct course Lavaridge → Route 112
  (ledges, y47–51, one-way SOUTH = our direction) → Route 111 west junction (y67–99 —
  the SAME corridor Ch10 walked northbound at ground truth) never touches the desert
  (which seals y≈61–88 further north; probed: (13,90)→(18,68..88) NO PATH but
  (13,90)↔(18,99) fine). ‼ The twin rocks RESPAWN on map reload — southbound must
  re-smash (18,101) from (18,100) facing Down (one rock opens column 18; `_smash_rock`
  is idempotent). Then Route 111 south (y102–139) → Mauville — all statically pathable.
  ALSO probed: the Rusturf Tunnel mid-wall is TWO Rock Smash rocks (24,4)/(24,5) with
  PERMANENT flags 931/932 (the Wanda quest — smash once, open forever; Wanda (25,4) and
  her boyfriend (23,5) flank it; the Ch5a grunt/Peeko objects at x14 are already hidden).
  `travel_lavaridge_to_petalburg` is BUILT + WIRED (Segment 12a) with these legs.
- **Overland route Lavaridge → Petalburg (⚠ route lead, ✓ Route 111 connections):** no Fly
  / no Surf yet, so it is a long backtrack. Lavaridge → **Route 112** (‼ one-way ledges —
  descend SOUTH only, never pathfind up Jagged Pass) → **Fiery Path → Route 111 SOUTH**
  (see the correction above) → **Mauville**
  → **Route 117** (⚠ tightly-packed trainers can force DOUBLE battles — our doubles
  attack-through handles it) → **Verdanturf** → **Rusturf Tunnel** (the Rock-Smash boulders
  are ALREADY cleared if Ch10 smashed them; else Rock Smash here — we have HM06) → **Route
  116** → **Rustboro** → **Route 104** → **Petalburg Woods** (N→S, no Cut needed) → **Route
  104 south** → **Petalburg City** → gym. Build as PROGRESS-gated riding-navigation legs
  (the corridor maps are shared with earlier trips — gate on arrival, not on map identity,
  the Ch11 lesson). ‼ Validate each connection live at build time (a two-way sweep is not
  needed — it's a forward march — but confirm the Rusturf boulder state and the Verdanturf
  entry).

- **Petalburg Gym interior (✓ probed: `PETALBURG_CITY_GYM` map (8,1), 9×112):** ENTER at
  the bottom (warps (4,111)/(5,111) ↔ Petalburg City (15,8)); gym guide at (3,109);
  **Norman at the TOP (4,2)**. Eight trainer tiers, each trainer at column x=4:
  Mary (4,94) · Randall (4,81) · George (4,68) · Alexia (4,55) · Parker (4,42) ·
  Berke (4,29) · Jody (4,16) · Norman (4,2). Each room has LEFT doors (x=1-2) and RIGHT
  doors (x=6-7) that are INTERNAL warps to other tiers; the doors are gated by
  `VAR_PETALBURG_GYM_STATE` (133 ✓) and only open after that room's trainer is beaten —
  a RUNTIME-MODIFIED layout, exactly the Mauville-gym class.
  **BUILD MECHANICS (decomp-verified 2026-07-24 — CORRECTS the earlier "find the walkable
  door tile" idea):** the doors are **never walkable** — each is a collision-blocked SIGN
  script (`PetalburgCity_Gym_EventScript_<X>RoomDoor`): FACE it from below, press A,
  answer YES to its "go through?" msgbox, and the script `warpdoor`s you to the landing.
  The entrance pair needs only `VAR_PETALBURG_GYM_STATE ≥ 6` (4 badges — our arrival
  state, probed =6); later doors answer "locked" until their gating trainer is beaten:
  Confusion←RANDALL, LeftDefense←RANDALL, RightDefense/Recovery←MARY,
  LeftStrength←PARKER, RightStrength←ALEXIA, LeftOHKO←ALEXIA, RightOHKO←GEORGE,
  **LeftGymLeaders←JODY**, RightGymLeaders←BERKE. Built chain (do_petalburg_gym /
  PETALBURG_GYM_CHAIN): Speed door (1,105)→(7,85) → beat Randall (4,81) → Confusion door
  (1,79)→(7,46) → beat Parker (4,42) → LeftStrength door (7,40)→(1,20) → beat Jody (4,16)
  → LeftGymLeaders door (7,14)→(1,7) → Norman. Gym trainers ~L26-27.
  ⚠ Walking INTO a closed door wedges the avatar (heldMovementActive stuck, input-starved
  — ch12 runs 4-8) — never navigate onto a door tile; always the face-and-A ritual.

- **Norman battle (⚠ team lead — decomp/trainer-data verify at build):** Spinda L27 /
  Vigoroth L27 / Linoone L29 / **Slaking L31** (ace). Cannot be fled. ‼ **Slaking has
  TRUANT** (loafs every other turn) but hits like a truck — our attack-through lead should
  bring a strong physical answer; a Fighting-type (Combusken/Blaziken, Machop line, Breloom
  if present) is the textbook counter (Normal is neutral, but the bot needs raw damage +
  to survive Slaking's big turns). Consider a Fighting or bulky lead + the matchup-aware
  after-faint chooser we already have. Beating Norman sets `DEFEATED_PETALBURG_GYM` (1268
  ✓) + `BADGE05_GET` (2155 ✓), gives **TM42 Facade**, and advances `VAR_PETALBURG_GYM_STATE`
  → 6.

- **HM03 Surf handoff (⚠ sequence lead, ✓ Wally's-dad object):** after Norman, **step DOWN**
  in Norman's room — a `VAR_PETALBURG_GYM_STATE==6` coord trigger fires and **Wally's Dad**
  (gym object id=11 at (1,7), flag `HIDE_PETALBURG_GYM_WALLYS_DAD` 824 ✓) walks in, talks,
  and warps the player to `PETALBURG_CITY_WALLYS_HOUSE`; an auto-script there hands over
  **HM03 Surf** and sets `RECEIVED_HM_SURF` (122 ✓). ‼ Do NOT Escape-Rope/Teleport out of
  the gym after the battle — that skips the coord trigger and soft-locks Surf. Just walk
  down. Completion signal for the segment: `RECEIVED_HM_SURF`.
  THEN teach Surf to a capable mon (the existing `ensure_hm_learner`/`teach_hm_move` path;
  Marshtomp/Swampert is the natural carrier) — Surf unlocks the whole Ch13+ water arc
  (Route 118 east, the Weather Institute, Fly from the Route 119 rival).

- **Gotchas summary (build-time watch list):** Route 112 one-way ledges (south only);
  Route 117 forced doubles; Rusturf boulder state (idempotent Rock Smash); Slaking Truant;
  the post-Norman step-down trigger; runtime-gated gym doors (read the LIVE grid like
  Mauville). Completion of Ch12 = `BADGE05_GET` + `RECEIVED_HM_SURF` + Surf taught.

### §Ch13 — the Surf arc: Mauville → Route 118/119 → Weather Institute → rival (Fly) → Fortree — BUILD SPEC (recon 2026-07-24 overnight)
> Status: flags audited ✓ + map structure probed ✓; Surf-crossing pathability needs a
> post-Surf save to verify (the pathfinder's `can_surf()` gates on live BADGE05 + a
> Surf mon — it plans water legs natively once those hold; `WaypointAction.Surf` is
> handled in follow_waypoints). Build from the `norman_done`/surf-taught checkpoint
> when the Ch12 long run lands it.

- **Flags (audited 2026-07-24 — two phantoms dodged):** `HIDE_ROUTE_119_TEAM_AQUA` ✓
  (Institute cleared), `HIDE_ROUTE_119_RIVAL` ✓ (rival done — use THIS, not the phantom
  "DEFEATED_RIVAL_ROUTE_119"), `RECEIVED_HM_FLY` ✓ (not "RECEIVED_HM02"),
  `RECEIVED_CASTFORM` ✓, `RECEIVED_DEVON_SCOPE` ✓, `DEFEATED_FORTREE_GYM` ✓,
  `BADGE06_GET` ✓; vars `ROUTE119_STATE` ✓ `FORTREE_CITY_STATE` ✓.
- **13a travel:** Mauville → Route 118 (east; Gabby&Ty rematch objects at (33-34,8) are
  flag-gated — the listener fights if engaged) → SURF the river channel (planner-native
  once Surf is taught; ⚠ validate the crossing live and watch the east-bank Steven
  scene — ride it) → north into **Route 119** (40x140, tall grass, rain) → up the west
  side to the **Weather Institute door at R119 (6,32)** (interior = map group 32;
  Aqua grunts inside; **Shelly** — Carvanha/Mightyena L28; completion =
  `HIDE_ROUTE_119_TEAM_AQUA`; Castform offered after — `RECEIVED_CASTFORM`, ‼ needs a
  free party slot, SKIP politely if party full [B through]) → the bridge Aqua grunts
  (13,33-34) despawn with the same flag → **rival at ~(17,33)** (object flag 923; fights
  L29/29/31, then gives **HM02 Fly** — completion `RECEIVED_HM_FLY` +
  `HIDE_ROUTE_119_RIVAL`) → north to **Fortree** (city 40x20; PC at (5,6) enum tile).
- **13b gym access:** the Fortree GYM is Kecleon-blocked — Route 120 east: Steven scene
  (bridge, invisible Kecleon, gives **Devon Scope** `RECEIVED_DEVON_SCOPE`) → back to
  Fortree → gym → **Winona** (Swellow/Pelipper/Skarmory/Altaria L29-33, Altaria ace —
  Electric/Ice lead) → `BADGE06_GET`. ‼ Fly field use unlocks at BADGE06 (KI-7: the
  stock fly_to gates on the WRONG badge for Emerald — fix before using Fly in nav).
- **Build shape:** Segment 13a legs mirror Ch12a (progress-gated riding navigation +
  interior scripts); 13b = a short travel + scene ride + gym in the Dewford pattern.
  END_MARKERS addition when wired: "FEATHER BADGE earned" (or the content-end message).
- **13d Devon Scope (⚠ tiles recon-pending — probe ROUTE120 objects/coord events before
  wiring):** Fortree → Route 120 east: STEVEN waits at the north bridge beside an
  invisible Kecleon; talking to him starts the scene → a forced Kecleon battle (L30,
  can flee/faint safely) → he hands over the **Devon Scope** (`RECEIVED_DEVON_SCOPE` ✓)
  and leaves. Then back west into Fortree: the gym-path Kecleon (on the tree-bridge
  before the gym) is flushed by A-ing it with the Scope (one more L30 Kecleon battle).
  Completion: `RECEIVED_DEVON_SCOPE` + the gym door reachable (probe the blocking
  object's flag at recon).
- **13e Fortree Gym — Winona (SOLVED ON PAPER 2026-07-24, see below):** ROTATING GATES.
  ‼ The old "graded-HIGH lead" here claimed turnstile STATE PERSISTS across exits and that
  they are runtime metatiles of the Mauville/Petalburg live-grid class. **Both halves are
  WRONG** — corrected from the decomp (`src/rotating_gate.c`,
  `data/maps/FortreeCity_Gym/scripts.inc`):
  - State does NOT persist. `MAP_SCRIPT_ON_TRANSITION` fires
    `RotatingGate_InitPuzzle → RotatingGate_ResetAllGateOrientations` on EVERY warp in, so
    orientations reset to the same fixed start every entry. (Good news: a plan computed from
    the entrance is valid on every attempt, and re-entering is a legitimate reset.)
  - They are NOT a live-grid metatile puzzle. Static collision never changes; a gate is
    `(x, y, shape, orientation)` and the game only consults gate logic for a step onto a tile
    whose STATIC collision is already open. So "push the blocking turnstile" is incoherent —
    a blocked tile is ordinary scenery and never reaches gate code at all. That is exactly
    why the greedy `push` heuristic failed 100% of the time.
  - Orientation IS readable live: the puzzle overlays gate bytes on `VAR_TEMP_0..VAR_TEMP_3`,
    so `orientation_i = (get_event_var(f"TEMP_{i//2}") >> (8 * (i % 2))) & 0xFF` for gates 0-7.
  - 8 gates: (6,7)T2@90, (9,15)T2@180, (3,19)T2@90, (2,6)T1@90, (9,12)T1@0, (6,23)T1@0,
    (12,22)T1@0, (6,3)L4@180. A faithful port of the decomp rule + BFS over the real extracted
    collision grid finds a legal 97-move solution entrance (15,24) → challenge tile (15,3);
    see `tools/story-dev/fortree/fortree_gate_solver.py` (runs, reproduces it).
  Trainers en route; **Winona**: Swellow L29 / Pelipper L30 / Skarmory L31 /
  **Altaria L33** (ace; Earthquake+DragonBreath — Electric is 2× into three of four
  but 0× into... note Altaria is Dragon/Flying: ICE is the 4× answer; Electric handles
  Swellow/Pelipper/Skarmory). Completion `BADGE06_GET` → **Fly becomes field-usable**
  (fix KI-7's wrong-badge gate in fly_to before using Fly in navigation).

### §Ch14 — Route 121 → Mt. Pyre → Magma Emblem → Magma Hideout (Maxie) — SPEC DRAFT (recon 2026-07-24 overnight; ⚠ build-time verify)
- **Flags audited:** `HIDE_MT_PYRE_SUMMIT_MAXIE` 856 ✓ / `_ARCHIE` 916 ✓ /
  `_TEAM_AQUA` 917 ✓; `VAR MT_PYRE_STATE` 185 ✓; `HIDE_JAGGED_PASS_MAGMA_GUARD` 847 ✓;
  `VAR JAGGED_PASS_STATE` 200 ✓; `HIDE_MAGMA_HIDEOUT_GRUNTS` ✓;
  `GROUDON_AWAKENED_MAGMA_HIDEOUT` 111 ✓; `TEAM_AQUA_ESCAPED_IN_SUBMARINE` 112 ✓ (Ch15).
  ‼ PHANTOMS dodged: "RECEIVED_MAGMA_EMBLEM" and "MET_ARCHIE_MT_PYRE" do NOT exist —
  the **Magma Emblem is a KEY ITEM** (gate on the BAG:
  `get_item_bag().quantity_of(get_item_by_name("Magma Emblem")) > 0`).
- **Route:** Fortree → Route 120 south (already recon'd) → **Route 121** west→east
  (80x20; the Safari Zone gate warp (37,5) is a DISTRACTION — skip) → south fork →
  **Mt. Pyre exterior door** — exterior map (24,21) 38x51: enter via MT_PYRE 1F (3,6)
  door → the EXTERIOR climb path (the interior tower is OPTIONAL — exterior only, per
  the graded lead) → exterior→summit doors at (19-20,10) → **summit**: ride the
  Archie/Maxie scene chain (MT_PYRE_STATE / the HIDE flags flip; the old lady gives the
  **Magma Emblem** after) — completion = the EMBLEM IN THE BAG.
- **Hideout:** back to Jagged Pass (Fly to Lavaridge once KI-7's badge gate is fixed —
  BADGE06 makes Fly legal — else the overland Ch12-reverse route) → the hideout door
  opens at ~(16,17-18) with the Emblem (`JAGGED_PASS_STATE`; ‼ the LEDGE below the door
  drops you back toward Lavaridge — approach from ABOVE, the one-way class) → **Magma
  Hideout** (multi-floor; grunts + Tabitha en route — listener fights) → **Maxie**
  (Mightyena 37 / Crobat 38 / Camerupt 39) → Groudon awakens/leaves
  (`GROUDON_AWAKENED_MAGMA_HIDEOUT`) — completion for the segment.
- **Build order note:** requires a BADGE06 save to iterate; spec only until the batch
  lands one. Then: 14a Route121→Pyre summit→Emblem; 14b hideout→Maxie. PREP: Maxie band
  ~L35-38 — the boss-training loop owns escalation; Lilycove mart provisions en route
  (#24-provisions).

### §Ch15/16 — Lilycove → Aqua Hideout → Mossdeep → Seafloor → Sootopolis → Sky Pillar → Juan — FLAG AUDIT + SPEC SEEDS (2026-07-24 overnight; ⚠ full recon at build)
- **Flags audited ✓:** `HIDE_LILYCOVE_CITY_RIVAL`, `TEAM_AQUA_ESCAPED_IN_SUBMARINE`
  (Aqua-hideout completion), `BADGE07_GET`/`DEFEATED_MOSSDEEP_GYM` (Tate&Liza),
  `RECEIVED_HM_DIVE`, `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`, vars `SHOULD_END_ABNORMAL_WEATHER`
  57 / `SOOTOPOLIS_CITY_STATE` 94 / `SKY_PILLAR_STATE` 202 / `SKY_PILLAR_RAYQUAZA_CRY_DONE`
  215, `RECEIVED_HM_WATERFALL`, `BADGE08_GET` (Juan), `DEFEATED_ELITE_4_DRAKE`,
  `SYS_GAME_CLEAR`. ‼ PHANTOM: "LEGENDARY_BATTLE_COMPLETED" does not exist.
- **Ch15 seeds:** Lilycove rival (HIDE flag above) → **Aqua Hideout** — warp-pad GRAPH:
  parse the hideout maps' warp tables and BFS them (the Granite-Cave chain-walker
  class; NO distance heuristics — graded-HIGH lead) — Matt → sub escapes
  (`TEAM_AQUA_ESCAPED_IN_SUBMARINE`) → Surf east → **Mossdeep** — Tate&Liza DOUBLE
  (Claydol/Xatu/Lunatone/Solrock L41-42; the doubles attack-through handles form;
  puzzle = colored switches rotating statue walls — live-grid class) → BADGE07 →
  Space Center Magma double w/ Steven (⚠ verify the ≥3-conscious-mons claim at build)
  → **HM08 Dive** from Steven's house.
- **Ch16 seeds:** Route 128 dive spot → **Seafloor Cavern** (Strength SOKOBAN — a wrong
  push is UNFIXABLE in-room: exit/re-enter to reset, the graded-HIGH lead; current
  tiles force-slide) → Archie → Kyogre escapes (`KYOGRE_ESCAPED_SEAFLOOR_CAVERN` +
  the weather var) → **Sootopolis** (Wallace) → **Sky Pillar FIRST VISIT = SOLID
  FLOORS** (`SKY_PILLAR_STATE`; NO bike puzzle in the story visit — never build one)
  → Rayquaza (`SKY_PILLAR_RAYQUAZA_CRY_DONE`) → back → **HM07 Waterfall** (Wallace) →
  **Juan** (ice floors = HAMILTONIAN PATH per grid — every tile exactly once, a fall =
  B1F + reset; Kingdra L46) → BADGE08. Then Victory Road (needs Surf/Waterfall/
  Strength/Rock Smash in the party — the HM-slave planning of #24-hm-multi matters
  HERE) → Wally (Gardevoir L45) → E4 → Wallace → `SYS_GAME_CLEAR`.

### §Ch12+ EXTERNAL-RESEARCH LEADS — Norman → Champion (Gemini Deep Research 2026-07-23, ⚠ UNVERIFIED)
> Source: the full-game commission (profiles/GEMINI-FULLGAME-RESEARCH.md — grading in its
> run log: HIGH for step order/rosters/puzzle rules, MEDIUM for identifiers; several flag
> names are phantom/wrong-dialect, so run `audit_flag_names.py` on EVERY name before
> wiring, and decomp-verify each chapter with /validate-docs at build time).

**Chapter chain:** Go-Goggles → Rt 111 desert → **Norman** (rooms gate on trainer
defeats — script-drawn doors, live-grid class like Mauville; VAR `PETALBURG_GYM_STATE` ✓
exists) → HM03 Surf from Wally's Dad → Surf Rt 118 (Steven beach trigger) → Rt 119 →
**Weather Institute** (Shelly: Carvanha/Mightyena L28; sets `HIDE_ROUTE_119_TEAM_AQUA` ✓
→ unblocks the bridge — hidden-prereq class) → Castform (‼ needs party space) → Rt 119
rival (L29/29/31, gives Fly; ‼ completion flag name is PHANTOM — likely VAR-gated like
Rt 110) → **Fortree** → Rt 120 Steven + Kecleon L30 → Devon Scope ✓ → **Winona**
(Altaria L33 ace) → Rt 121 → **Mt. Pyre** (‼ interior tower is OPTIONAL — exterior path
only) → Magma Emblem (‼ flag name unverified) → Jagged Pass hideout door (~(16,17-18);
‼ ledge below = softlock back to Lavaridge — one-way class) → **Magma Hideout** →
Maxie (Mightyena 37/Crobat 38/Camerupt 39; `HIDE_MAGMA_HIDEOUT_GRUNTS` ✓ exists) →
**Lilycove** rival → **Aqua Hideout** (warp-pad GRAPH — parse map.json warps, no
distance heuristics; Master Ball room en route) → Matt → sub departs
(`TEAM_AQUA_ESCAPED_IN_SUBMARINE` 112 is OUR likely completion flag) → **Mossdeep**
(Tate&Liza DOUBLE, Claydol/Xatu/Lunatone/Solrock 41-42; puzzle = colored switches
rotate statue walls) → Space Center double w/ Steven (‼ claim: needs ≥3 conscious mons
— verify) → HM08 Dive → Rt 128 dive → **Seafloor Cavern** (Strength SOKOBAN — wrong
push = exit/re-enter resets; current tiles force-slide) → Archie (Sharpedo L43) →
Kyogre escapes (`VAR SHOULD_END_ABNORMAL_WEATHER` ✓ exists) → **Sootopolis** → Wallace
→ ‼‼ **SKY PILLAR FIRST VISIT NEEDS NO MACH BIKE — ⛔ BUT IT DOES *NOT* HAVE SOLID FLOORS**
(`SKY_PILLAR_STATE` ✓ exists. ⛔ **THIS LINE READ "HAS SOLID FLOORS … cracked floors are post-game
only" UNTIL 2026-08-24 AND WAS FALSE** — it was the THIRD copy of that claim in this file and it
survived two sweeps because it is worded differently from the other two. **`4F_Clean` has FIVE
cracked tiles and the ascent MUST fall through one** — see the §Ch21 ATLAS below and
`probe_skypillar_clean_layout.py`. The "no bike solver" half is CORRECT and stands.) → Rayquaza → HM07 Waterfall → **Juan** (ice floors =
HAMILTONIAN PATH per grid: every tile exactly once, fall = B1F + reset; Kingdra L46) →
Victory Road (needs Surf/Waterfall/Strength/Rock Smash in party) → Wally VR (Gardevoir
L45) → **E4**: Sidney/Phoebe/Glacia/Drake → Wallace (Milotic L58) → `SYS_GAME_CLEAR` ✓.

### §Ch10–13 ROADMAP — Mauville → Fallarbor → Mt. Chimney → Lavaridge (Gym 4) → Petalburg (Gym 5) → Surf
Research-mapped 2026-07-22 (decomp WebFetches + static ROM recon; Gemini pass pending —
see the outstanding question). Legend: `✓ decomp` / `✓ probe` / `✓ external` / `⚠ open`.

### §Ch11 — Fallarbor → Meteor Falls → Mt. Chimney → Jagged Pass → Lavaridge (Gym 4) — BUILD SPEC (decomp sweep 2026-07-22 overnight)
- **11a Meteor Falls scene**: Fallarbor → Route 114 WEST (Fallarbor connects at R114's
  east edge; fishermen/hikers en route) → Meteor Falls door at **R114 (8,63)** → walk in
  → the Magma-steals-meteorite CUTSCENE fires (NO battle in Emerald; Archie cameo) →
  sets `FLAG_HIDE_ROUTE_112_TEAM_MAGMA` (unblocks the Cable Car!) + VAR_METEOR_FALLS_
  STATE=1. Completion: that flag. Then exit and travel back east → south to Route 112.
- **11b Mt. Chimney**: R112 Cable Car station warps at **(28-29,27)** → ride up (station
  interior scene) → the Magma chain: Grunt1 → Grunt2 → Tabitha → **Maxie**
  (`trainerbattle_no_intro`; PREP: band-train ~L24-27 + heal — Maxie: Mightyena 24 /
  Zubat 24 / Camerupt 25). Completion: `FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY`. Then TAKE
  THE METEORITE from the machine (FLAG_RECEIVED_METEORITE — needed for TM27 later,
  authentic pickup).
- **11c Jagged Pass DOWN**: Mt. Chimney south exit warps → Jagged Pass top (13-14,5) →
  descend (ONE-WAY ledges southbound — our direction; trainers Eric (10,8), Diana
  (9,21), Autumn (14,25), Julio (18,25), Ethan (16,35)) → bottom warps (14-15,40) →
  R112 lower (6-7,46) → WEST connection → **LAVARIDGE TOWN**. Heal at its PC.
- **11d Lavaridge Gym (trapdoor maze) — ✅ SOLVED + BUILT + VALIDATED (2026-07-23).**
  The maze is derived from the ROM's own map data at run time, not explored or
  hardcoded. Three metatile behaviours are the whole puzzle:
  | behaviour | floor | meaning |
  |---|---|---|
  | 104 (`MB_LAVARIDGE_GYM_1F_WARP`) | 1F | **HOLE** — fall to B1F at the SAME coordinate |
  | 41 (`MB_LAVARIDGE_GYM_B1F_WARP`) | B1F | **GEYSER** — launch to 1F at the SAME coordinate |
  | 59 (`MB_JUMP_SOUTH`) | both | **LEDGE** — collision=1 but hoppable DOWNWARD (2 tiles) |
  Every warp pair in this gym is same-coordinate (dumped + live-confirmed), so a warp
  event whose tile is neither 104 nor 41 is INERT — a landing pad only, which is why
  landings never re-trigger. ‼ **The ledges are the crux**: each floor looks like
  sealed chambers under plain collision, and several chambers then appear to have no
  exit at all — but every one of them is escapable southward over a ledge band. Model
  hops and there are no dead ends; ignore them and the solver oscillates between two
  inert tiles (that was the ch11d_run9 wedge).
  So: state = the 1F chamber you stand in; an edge = "fall through a reachable hole H,
  walk the B1F chamber to a reachable geyser G, surface at 1F G". A backward BFS from
  Flannery's chamber gives the next move from wherever we ACTUALLY are, so a battle
  knock-off or surprise landing just re-plans. **Canonical chain from the entrance is
  4 falls: (8,9)→(0,17 | 5,14), (0,10)→(0,6), (2,3)→(7,2), (10,6)→(12,12)** — the last
  geyser surfaces on Flannery's platform (1F chamber (11-15, 9-12)).
  Two planning hazards, both handled: paths must never cross ANOTHER hole/geyser (it
  fires en route and throws the plan away), and four B1F geysers — (4,18) Jace, (3,6)
  Keegan, (13,17) Jeff, (4,16) Eli — are the buried trainers' own tiles, so NPC-held
  tiles are excluded from both planning and walking. Movement uses held input
  (`_hold_walk_to`); the stock navigator idles in this gym post-warp, the same latent
  upstream quirk as the post-badge Mauville exit.
  **Flannery**: Numel 24 / Slugma 24 / Camerupt 26 / Torkoal 29 — WATER lead (all four
  are 2× to Water). Completion: `BADGE04_GET`. Wired as Segment 11d (lead + heal, NO
  pre-grind — see the training-tile note below). Checkpoint `flannery_done.ss1`.
  THEN: the Go-Goggles scene (⚠ verify trigger position) unlocks the desert; Ch12 =
  Petalburg (Norman).
- **⚠ NO training grass is reachable from Lavaridge** (two-way sweep,
  `tools/story-dev/jaggedgrass_probe.py`, 2026-07-23): Jagged Pass cannot be re-entered
  from the town (one-way ledges — outbound nav fails outright) and Route 112's lower
  grass has an outbound path but NO return path. Segment 11d therefore preps with a
  Water lead + heal only. A L29-31 team wins but is marginal (validation run 11 lost
  once, self-recovered, then won). Fix when it bites: find a swept Lavaridge-area tile
  (#24-trainmap) — never a blind grind target.
- ⚠ open (append to GEMINI-PROMPTS.md if build hits walls): Cable Car station interior
  scripts (auto-scene or talk-to-attendant?); B1F warp-pair destination coords (fetch
  LavaridgeTown_Gym_B1F/map.json at build time); Go-Goggles exact trigger.

**Ch10 — Mauville → Fallarbor (via Fiery Path).**
- Prereq: HM06 Rock Smash — `✓ decomp` (2026-07-22): **MauvilleCity_House1 = map (10,2),
  door at Mauville CITY (32,14)** (the SE house east of the Mart (23,14)→(10,7)); the
  "Rock Smash Guy" gives `ITEM_HM_ROCK_SMASH` gated only on `RECEIVED_HM_ROCK_SMASH`
  not yet set (also sets HIDE_ROUTE_111_ROCK_SMASH_TIP_GUY). Static NPC → simple
  enter + face-talk (no wandering machinery needed).
- TEACH FLOW (build item — no helper exists yet): StartMenuNavigator("BAG") →
  `scroll_to_item_in_bag(HM06)` (menuing.py primitive, bag already open) → A → USE →
  party → pick the mule → confirm → overworld move-learn UI if 4 moves. Mule policy:
  **Marshtomp** (learns Rock Smash; replace Tackle — keeps Mud-slap + Water Gun; Rock
  Smash 20bp Fighting adds coverage). Field use after BADGE03 (have it): walk INTO a
  breakable rock → YES/NO prompt → YES breaks it (no menu needed).
- ROUTE SPEC `✓ decomp` (2026-07-22, full map.json sweep — build against THIS):
  Mauville north edge → **Route 111 south** (Victor the first Winstrate at (13,114)
  ON-path — sight-line battle; his house door (13,113); breakable rocks at **(18,101) +
  (19,100)**, object events cleared by the walk-into→YES prompt) → north to the R112
  east connection (R111 connects LEFT→Route112 offset 20) → **Route 112 south** (Hiker
  Brice (24,34), Trent (15,40) near the path; AVOID the Cable Car station warps at
  (28-29,27)) → **Fiery Path door at R112 (11,36)** → tunnel (NO trainers; the six
  Strength boulders only gate optional item alcoves, the main passage is clear) → exit
  warp (26,4) → **R112 north at (22,10)** (Bryant (31,7)/Shayla (31,11) east of path)
  → north connection → **Route 113** (offset -60; ash route: Jaylen (62,8), Madeline
  (51,11), **TWINS Tori&Tia (45-46,6) = DOUBLE battle on-path**, buried ninjas (29,6)/
  (71,2) pop-ups, Sophie (7,6)/Coby (7,13) near the west end) → LEFT connection →
  **FALLARBOR TOWN** (PC heal = chapter end; checkpoint `fallarbor.ss1`).
  Sanity checks still owed before build: two-way pathability sweeps from the REAL
  entry tiles for every leg + audit_flag_names + live task-name probe for the
  overworld HM-teach UI.
- Route 111 (40×140! `✓ probe`): from Mauville go NORTH; **Rock Smash rocks at
  (18,101)/(19,100) gate the path** (`✓ probe`; tip-man at (19,101)). Winstrate house at
  (13,113)→interior (`✓ probe`; the family battle gauntlet is optional? `⚠ open`). Desert
  (sandstorm, needs Go-Goggles) is EAST — not needed yet.
- Route 111 –(W)→ **Route 112**: the NE Magma grunt pair blocks the CABLE CAR area
  pre-Meteor-Falls (`✓ decomp: FLAG_HIDE_ROUTE_112_TEAM_MAGMA cleared later`); first
  visit goes DOWN through **FIERY PATH** (a through-tunnel: R112 (22,10)↔inside (26,4);
  inside (26,36)↔R112 lower (11,36) `✓ probe`) → Route 112 west –(conn)→ **Route 113**
  (ash route, 100×20 `✓ probe`) → west → **FALLARBOR TOWN** (`✓ probe` warps: PC (1,6)?,
  Cozmo's house (8,7), Move Tutor…; `⚠ open`: exact PC door).
**Ch11 — Meteor Falls scene → Mt. Chimney (Magma) → Jagged Pass.**
- Fallarbor –(W)→ **Route 114** → Meteor Falls door (8,63) → **METEOR_FALLS_1F_1R**:
  the Magma-steals-the-Meteorite CUTSCENE (NO battles `✓ decomp`); sets
  `VAR_METEOR_FALLS_STATE=1`, `FLAG_MET_ARCHIE_METEOR_FALLS`, and **clears the Route 112
  Magma blockade → the CABLE CAR opens** (`✓ decomp` via FLAG_HIDE_ROUTE_112_TEAM_MAGMA).
  Prof. Cozmo inside at (13,23) `✓ probe`. `⚠ open`: the scene's trigger tile.
- Back to Route 112 → **Cable Car station (28-29,27) `✓ probe`** → attendant (6,6) → ride
  (scripted) → Mt. Chimney summit. **Fights (`✓ decomp`): TRAINER_GRUNT_MT_CHIMNEY_2 +
  TRAINER_TABITHA_MT_CHIMNEY (Tabitha at (12,11)), then TRAINER_MAXIE_MT_CHIMNEY (Maxie
  (13,6)) — un-fleeable, use the boss prep pattern.** Win →
  `FLAG_DEFEATED_EVIL_TEAM_MT_CHIMNEY` + Magma/Aqua despawn; optionally take the
  METEORITE from the machine (`giveitem ITEM_METEORITE` — later tradeable for TM27;
  policy: TAKE it, it's free). `⚠ open`: Maxie/Tabitha teams (Gemini asked).
- Descend **JAGGED PASS** (top (13-14,5) ↔ Chimney (20-21,41); bottom (14-15,40) ↔ R112
  lower (6-7,46) `✓ probe`) — a LEDGE-JUMP descent (`⚠ open`: exact ledge path; the
  Magma Hideout door (16,18) is a LATER chapter) → Route 112 lower → **LAVARIDGE**.
**Ch12 — Gym 4: Flannery (Torch Badge) + Go-Goggles.**
- Lavaridge (`✓ probe`): gym door (5,15) → GYM_1F; **Flannery 1F (13,9)**; the gym is a
  1F↔B1F TRAPDOOR MAZE (26 warp-pairs! `✓ probe`) — `⚠ open`: the minimal trapdoor route
  to Flannery (Gemini asked; else grid-probe + trial). Flannery (Emerald): Numel/Slugma/
  Camerupt/Torkoal ~L24-29 `⚠ verify`. Marshtomp (Water) is the natural sweeper. Win →
  BADGE04 + TM50 Overheat; outside, the RIVAL gives the **GO-GOGGLES** (`⚠ open`: exact
  trigger/coords). Herb shop optional.
**Ch13 — Gym 5: Norman (Balance Badge) → HM03 Surf.**
- Travel Lavaridge → Petalburg (`⚠ open`: best route — likely back over Jagged Pass is
  ONE-WAY (ledges); the sane route is Cable Car → R112 → R111 → Mauville → R110 → ... or
  Lavaridge –(E conn)→ Route 112? Gemini asked; NOTE we have no Fly/Surf yet).
- **Petalburg Gym (`✓ decomp`): Norman requires 4 BADGES; themed rooms** — the
  Speed→Confusion→Strength door chain reaches Norman (`VAR_PETALBURG_GYM_STATE` drives
  doors; ≥6 unlocks all). Win → `FLAG_BADGE05_GET`(!! the BALANCE badge is BADGE05 in
  data even though it's the 5th badge... `⚠ verify numbering`), TM42 Facade,
  `VAR_PETALBURG_GYM_STATE=7`, `VAR_PETALBURG_CITY_STATE=4` → **Wally's dad walks you to
  Wally's house → HM03 SURF** (`✓ decomp` for the gym side; `⚠ open`: the house scene's
  exact flow/flags). Norman (Emerald): Spinda/Vigoroth/Linoone/Slaking ~L27-31
  `⚠ verify`. SURF then opens Routes 118+ (Ch14+: Weather Institute → Fortree/Winona).


> **Pass 4 (2026-07-20)** re-derived every fact independently from ROM + two/three
> external walkthroughs and diffed against the doc. It **confirmed all five Pass-3
> corrections** (no regressions) and found **two NEW content-detail errors** (the
> Petalburg-Woods Devon-Goods flag misattribution and the Cut "Route 104 vs
> Rustboro" contradiction), now fixed and tagged **[P4]**. It also resolved two
> former verify-live items (Magma Emblem = key item, not a flag; `MT_PYRE_STATE`
> var). Full table + convergence verdict in the new **§10**. The strategic
> backbone has **converged**; residual unknowns are live-only where-to-stand/timing.

> **Pass 3 (2026-07-20)** independently triple-checked every factual claim
> against BOTH (A) the bot's own ROM ground truth (`event_flags/emerald.txt`,
> `event_vars/emerald.txt`, `symbols/pokeemerald.sym`, `menuing.py`,
> `map_path.py`, `higher_level_actions.py`) AND (B) an external Emerald
> walkthrough (Bulbapedia / Thonky / pokemondb / psypokes / GameFAQs). It caught
> a **Pass-2 regression** (Rock Smash location) plus a **chapter-order error**
> and a **flag misplacement**. Inline Pass-3 fixes are tagged **[P3]**; see the
> new **§9 "Pass 3 accuracy audit"** for the full claim-by-claim table.

> Design-only document. NO code was written or changed producing this. **Pass 2
> (2026-07-19)** adversarially re-audited the Pass-1 skeleton against the bot's
> own ground-truth data (`modules/data/event_flags/emerald.txt`,
> `event_vars/emerald.txt`, `modules/data/symbols/pokeemerald.sym`,
> `modules/menuing.py`, `modules/map_path.py`) and caught several errors and
> missed mandatory beats — see **§8 "Pass 2 verification"** at the end for the
> full change list. Inline Pass-2 corrections are tagged **[P2]**. This remains
> a design doc for punch-list **#24** (Story-Mode Bot), grounded in the **real**
> capabilities of the working fork at `sandbox-pokebot/`, cited as `file:line`.
> Emerald-only for v1 (profile `Nick - Emerald`, game code `BPE`).
>
> **[P2] Headline corrections:** (1) **Gym 8 leader is JUAN, not Wallace** —
> Wallace is the *Champion*. (2) **Fly's field-use gate is the Feather Badge
> (BADGE06), code-confirmed** — the doc's earlier uncertainty is resolved, and a
> real fork bug was found in `fly_to`. (3) Three **mandatory late-game beats were
> missing** from the skeleton: **Mt. Pyre**, the **Slateport Harbor submarine
> theft**, and the **Magma Hideout / Groudon awakening**. (4) **Mr. Briney &
> the Peeko rescue** (the gate to the Dewford/Slateport boat) needed to be made
> explicit. (5) HM04 **Strength comes from Rusturf Tunnel, not Mt. Chimney**.
> (6) **Brawly's gym IS a puzzle** (dark room). All resolved below.
>
> **Reading note on citations:** all `modules/...:NNN` paths are relative to
> `C:\Remote Projects\Pokebot_Gen3_Enhancement\sandbox-pokebot\`. Line numbers
> were read on 2026-07-19; treat them as anchors, not guarantees across future
> upstream pulls.

---

## §P. PURPOSE & PROJECT CONTEXT (read this first — it shapes HOW we build)

**What this Story bot is.** A *scripted, deterministic* bot that plays Pokémon
Emerald from a fresh save all the way to the end of the story by itself. It is
driven by observed game state (maps, coordinates, script names, flags) and hard
sequences — NOT by learning. Its job is to be a **reliable, repeatable reference
playthrough**.

**Why it exists (the bigger goal).** It is the **scaffold/reference for a
SEPARATE Pokémon-playing AI program** (a different project — the "Emerald AI"
sibling). That AI is meant to *learn to play the game organically, like a human*.
This Story bot and its documentation exist to **accelerate that AI's training**:
the bot provides a known-good trajectory (what to do, where, in what order) and
this documentation captures the game's mechanics, map facts, and decision points.
The AI will **not call this bot at runtime** — it learns from the *reference and
the notes*, then plays on its own. Getting a bot that can complete the story end-
to-end by itself is step 1; layering in more human-like behaviour comes later
(to be detailed separately).

**What this means for HOW we work (documentation is a first-class deliverable):**
- Write down not just *what* the code does but **WHY**, the **game facts** behind
  it (map ids, coords, script names, flags, level thresholds, type matchups), and
  **HOW we discovered them** (the recon that found the fact). Those notes are
  what the AI project consumes — they are as important as the code.
- Every chunk's function carries a docstring in the INTENT / STORY CONDITION /
  HOW IT WORKS / GOAL-END-STATE format (see `modules/story/early_game.py`) so the
  trajectory reads as a documented sequence of game states.
- Prefer *discovering ground truth* (dump the map, read the script name, read the
  flag) over guessing — see **§R. RECON PLAYBOOK**. Recorded facts compound; a
  guess that happens to work teaches the AI project nothing.
- Log the hard-won lessons in `08-MISTAKES.md` (they double as "gotchas the AI
  will also hit").

---

## §R. RECON PLAYBOOK (the standard way to build a chunk — do this FIRST)

Cross-region travel and scripted scenes bit us repeatedly (ML-7/ML-8) whenever we
GUESSED coordinates. The reliable, fast way is to **dump ground truth first, then
write code against it.** This playbook is now the default build loop.

### 1. Static map recon — `tools/mapdump.py` (the "map dump")
One command prints a map's dimensions, connections, warps (with destinations),
NPCs (if a state is loaded), and an ASCII collision/tile grid:
```
py -3.12 tools/mapdump.py <MAP_NAME> --profile story-b-test [--state PATH.ss1]
# e.g. py -3.12 tools/mapdump.py PETALBURG_WOODS --state /tmp/woods_entered.ss1 --profile story-b-test
```
Read from it: the **only** walkable openings (a fenced edge with one gap → the
exit), which warp leads where (find a door's destination map/`warp_id`), whether
an intermediate map is **warp-split** (a route that only continues THROUGH a
building/cave → connection-routing will fail, go leg-by-leg — ML-7), and whether
a "silent blocker" is a wanderer or stationary NPC.

### 2. Dynamic recon — name the script that stalls you
When the player stops at a tile for no visible reason, it is almost always a
coordinate-trigger script (Scott gate, a trainer sight-line, a cutscene). Walk
into it and read the active script's name:
```python
from modules.tasks import get_global_script_context
sc = get_global_script_context()
if sc and sc.is_active:
    print(sc.stack)   # e.g. ['PetalburgCity_EventScript_Scott'] or ['EventScript_TrainerApproach']
```
`EventScript_TrainerApproach` ⇒ a TRAINER (must FIGHT, not ride out — use the
no-flee travel strategy + pre-heal, ML-8). A `*_EventScript_*` cutscene ⇒ ride it
out. NB some overworld scripts run while `game_state` stays OVERWORLD, so gate the
ride-out on `script.is_active`, not on a state change (ML-8 companion note).

### 3. Test EVERYTHING via the listener-driven harness (never a bare next()+frame)
Scripted scenes read STALE state under a bare `next(gen)+run_single_frame()` loop
and give WRONG results (this cost hours — ML-5). Drive each step exactly like the
real main loop: build a `FrameInfo` and call the `get_bot_listeners()` each frame,
with a mode whose `on_battle_started` returns the strategy. Skeleton:
```python
context.controller_stack = [mode.run()]
context.bot_listeners = get_bot_listeners(context.rom)
prev = None
while frames < CAP:
    sc = get_global_script_context(); ss = sc.stack if sc and sc.is_active else []
    fi = FrameInfo(frame_count=..., game_state=get_game_state(), active_tasks=[...],
                   script_stack=ss, controller_stack=[c.__qualname__ for c in context.controller_stack],
                   previous_frame=prev)
    for L in context.bot_listeners.copy(): L.handle_frame(context.bot_mode_instance, fi)
    try: next(context.controller_stack[-1])
    except StopIteration: context.controller_stack.pop() ...
    context.emulator.run_single_frame(); prev = fi
```
(Full working copies live in the scratchpad harnesses; reuse one.)

### 4. Reusable patterns learned (apply these, don't re-derive)
- **Leg-by-leg travel** past a warp-split map: navigate each leg with
  `navigate_to_anywhere(..., avoid_scripted_events=False)` so trainer approaches
  become battles the listener wins, and the no-flee strategy prevents the flee-crash.
- **Door warps:** navigate STOPS ON a door tile without triggering it; step UP into
  the door with DISCRETE steps (press, let the ~16-frame step finish), and if you
  ended on the door, drop one tile south first. See `travel_to_petalburg_woods`.
- **Checkpoints:** save a `.ss1` at each leg boundary (scratchpad) so the next leg
  iterates in seconds, not minutes. WRITE the save AFTER the harness loop ends
  (writing mid-emulation raises PermissionError).
- **Pre-heal** before any trainer route while the party is tiny (ML-8).

---

## §TB. ORGANIC TEAM-BUILDING & HELPER MODEL (design — future, punch-list #24-team)

**Goal (user, 2026-07-20):** the bot should build a team to beat gyms/trainers,
but the decision to go catch a "helper" must look **organic, not mechanical** —
a human adapting, not an optimizer. It ties directly to the AI-reference purpose
(§P): a trajectory that *adapts under pressure* is far richer training data than
one that always pre-counters. NOT needed for Gym 1 with Mudkip/Treecko; it becomes
necessary for **Torchic vs Roxanne** and for later type-hard gyms.

**Model — a rising "recruit urge", not a rule:**
- Maintain a **pressure score** that RISES on struggle and decays on success:
  a battle lost / near-wipe / lead fainting / a gym attempt failed all add
  weight (more weight = bigger setback). Winning comfortably lets it decay.
- Each time the bot is about to tackle a hard fight (or between fights), it
  **re-rolls**: `P(go catch a helper) = f(pressure, current team gaps)`. Low at
  first (it tries with what it has — organic), rising with repeated failure so a
  stuck run self-rescues. Randomness means it won't always grab the obvious
  counter, and sometimes tries again first — human-like.
- The re-roll is **weighted by real team gaps**, so when it DOES recruit, the
  choice is *logical*: prefer a species that (a) covers the upcoming/again-lost
  type matchup, (b) adds **type diversity** to the team (avoid stacking one
  type), (c) brings **move-type coverage** the team lacks. Pull candidates from
  the **obtainability + reachability data we already built** (#41/#42,
  `emerald_obtainability.json`) filtered to what's catchable on routes reached so
  far (e.g. pre-Roxanne: a **Lotad** on Route 102/103/104, a **Marill** Water,
  or a Ground move) — never a mon we can't yet reach.
- Then it **goes and catches it organically** (travel to the route, encounter,
  weaken, throw balls) and optionally trains it, before re-attempting the fight.

**Why this shape:** increasing odds on failure guarantees eventual progress
(no hard stuck), while the low starting odds + randomness + gap-weighting keep it
from looking like a min-maxer. Tunable knobs: base P, pressure gain/decay,
gap-weight mix. Details (exact scoring, candidate tables per chapter, catch
routine) to be settled when implemented. Reuses: the no-flee travel strategy,
`navigate_to_anywhere`, the recon tools, and the obtainability model.

---

## §Ch5. CHAPTER 5 RECON — Devon Goods errand (fully mapped 2026-07-20, NOT built)

Post-Gym-1. Verified live from `gym1_done.ss1`. Checkpoint `post_theft.ss1` saved
(controllable in Rustboro, DEVON_GOODS_STOLEN set). Map ids: RUSTBORO_CITY=(0,3),
ROUTE116=(0,31), RUSTURF_TUNNEL=(24,4), RUSTBORO_CITY_DEVON_CORP_1F=(11,0).

**Order of operations (all live-verified):**
1. **Theft scene** — walking into EASTERN Rustboro (~(23,20)) trips
   `RustboroCity_EventScript_StolenGoodsScene` (grunt bolts with the goods).
   Sets **DEVON_GOODS_STOLEN**. ⚠️ This cutscene has mid-scene CONTROLLABLE
   windows that fool the generic ride-out — ride it out **flag-anchored** (press
   B/A until DEVON_GOODS_STOLEN is set), NOT until "controllable + no script"
   (that thrashes `_navigate_through_scripts` → "too many interruptions").
2. **Devon employee** at the east exit (~(30,9)):
   `RustboroCity_EventScript_EmployeeAskToGetGoods` — ride out (dialogue).
3. **Chase to the tunnel:** Rustboro EAST → Route 116 (Route116 West→Rustboro).
   Tunnel WEST door = Route116 **(47,8)** → RUSTURF_TUNNEL (4,10). NOTE
   `navigate_to_anywhere(RUSTURF_TUNNEL)` picks the WRONG warp (the Verdanturf/east
   side) — go leg-by-leg: navigate onto Route 116 then `_pass_through_door((47,8),
   ROUTE116)`. Rusturf warps: (4,10)→Route116-W, (18,20)→Route116-E,
   (29,16)→Verdanturf (blocked by Rock-Smash rocks until later).
4. **Grunt battle** in the tunnel (west side) → recover goods + free **Peeko**
   (Mr. Briney's Wingull); Mr. Briney appears. Sets **RECOVERED_DEVON_GOODS** (143).
5. **Return** to Rustboro → **Devon Corp 1F** (warp (11,0)/(12,15) in Rustboro) →
   talk to the president → **PokéNav** + **Steven's Letter**. Sets
   **RECEIVED_POKENAV** (188), RETURNED_DEVON_GOODS (144).
6. **Rustboro rival battle** (DEFEATED_RIVAL_RUSTBORO 211) — NOT yet located live
   (likely near the Pokémon School on the way back); find its trigger when building.

**Build plan:** one `recover_devon_goods()` (steps 1-4, flag-anchored theft
ride-out + `_pass_through_door` tunnel entry + no-flee grunt battle → checkpoint
`goods_recovered.ss1`) then `return_goods_get_pokenav()` (step 5, + step 6 rival).
Completion flag for the whole chapter: **RECEIVED_POKENAV**. Reuse: no-flee travel
strategy, `_pass_through_door`, `_navigate_through_scripts`, the mapdump tool.

### BUILD PROGRESS 2026-07-21 — `recover_devon_goods()` BUILT + VERIFIED (Chapter 5a)
Chapter 5a is **DONE** (sandbox only, like the unpromoted Gym 1 work). `recover_devon_goods()`
in `early_game.py`, wired as **StoryMode Segment 5a** (gated by RECOVERED_DEVON_GOODS).
Verified via the REAL `StoryMode.run()` from `gym1_done.ss1`: `RECOVERED_DEVON_GOODS=True`
at ~f31858, clean finish to Manual, no errors (Mudkip evolved to Marshtomp mid-chase,
handled cleanly). Checkpoint `goods_recovered.ss1`. The verified sequence + geometry:
- **Gym exit warp:** (5,19)/(6,19) → RUSTBORO_CITY. `navigate_to_anywhere(RUSTBORO_CITY, …)`
  routes out through it.
- **Theft:** walking WEST through the city (target ~(18,20)) fires the theft; anchor
  on **DEVON_GOODS_STOLEN** (rode it out via `navigate…except → _ride_out`). Confirmed
  set. (Post-theft the player stands at (23,20); NPCs id2(19,13)/id6(26,23)/id13(19,27)
  — none block the east exit.)
- **Devon Corp warps** are **(11,15)/(12,15)** (recon's "(11,0)" was WRONG).
- **Chase to Route 116:** `navigate_to_anywhere(ROUTE116, (5,9))` gets ONTO Route 116
  (the far target (40,8) had NO PATH — Route 116 has ledges/blocked tiles; the WEST
  edge (5,9) works). Then `navigate_to_anywhere(ROUTE116, (47,9))` crosses to the
  door approach (the global navigator handles the ledges; plain `navigate_to` to
  (46,9) FAILED). Route 116 has wild encounters even with avoid — the starter levels
  and evolves en route (Mudkip→Marshtomp seen; the move-learn/evo fix handled it clean).
- **Tunnel door:** the warp is **Route116 (47,8)**, entered from **(47,9)** below it
  (`_pass_through_door((47,8), ROUTE116)`). Confirmed lands in RUSTURF_TUNNEL (24,4)
  at entrance (4,10).
- **Rusturf Tunnel layout:** entrance warp (4,10); walkable = the (3-7) vertical
  corridor up to the wide rows 4-5. **Grunt NPC id6 at (13,5)** (gfx117, faces WEST),
  **Mr. Briney id7 at (13,4)** (gfx211). Path: (4,10)→up the corridor→row5→EAST toward
  the grunt. Reached (11,5), 2 W of the grunt. Targets EAST of the grunt (e.g. (20,5))
  have NO PATH — the grunt BLOCKS the corridor (use that as the "we're here" signal,
  don't pathfind past them).
- **Grunt engage (SOLVED):** approach to (12,5) adjacent-west, then engage WITH A
  (not B — B skipped the challenge). The grunt says "…So you want to battle me?",
  the listener fights it, then "NICK put away the DEVON GOODS…" + Mr. Briney frees
  Peeko → RECOVERED_DEVON_GOODS. `_wait_until_cutscene_over("A")` rides out the tail.

**NEXT (Chapter 5b, still to build):** `return_goods_get_pokenav()` — from the tunnel,
back out the west door (4,10)→Route116→Rustboro→**Devon Corp** (enter (11,15)/(12,15)).
The president who gives the **PokéNav + Steven's Letter** is on **Devon Corp 3F** (go up
1F→2F→3F) — needs interior recon (floors/warps/president NPC). Completion:
**RECEIVED_POKENAV** (188); also RETURNED_DEVON_GOODS (144). Then the **Rustboro rival**
(DEFEATED_RIVAL_RUSTBORO 211) — trigger not yet located (likely near the Pokémon School
(27,34) on the way back). Recon tool: `tools/story-dev/story_harness.py --driver ch5recon`
(dev tooling, not committed).

### BUILD PROGRESS 2026-07-21 — Chapter 5b: PokéNav return + forced tutorial SOLVED + rival wired (sandbox)
`return_devon_goods_and_get_pokenav()` (Devon Corp 3F, Mr. Stone (15,5), A-spam to
RECEIVED_POKENAV) was already built + validated. This pass solved the two remaining
blockers and wired the full segment.

**The forced PokéNav/Match-Call tutorial — SOLVED via a targeted state-write.**
After the PokéNav, the game auto-walks you out of Devon Corp into Rustboro City (~(11,16)).
The map's **ON_FRAME table** (`map_script_2 VAR_RUSTBORO_CITY_STATE, 6,
RustboroCity_EventScript_ScientistAddMatchCall`) then fires a Scientist NPC (approaches
at ~(11,17)) who runs the Match-Call tutorial: 2 intro msgboxes → a **start-menu
multichoice** (`special ScriptMenu_CreateStartMenuForPokenavTutorial`) whose `switch
VAR_RESULT` only falls through on **case 3 = POKéNAV** (all else nags via
`PleaseSelectPokenav` and re-opens) → `special OpenPokenavForTutorial` opens the PokéNav
app in **`POKENAV_MODE_FORCE_CALL_READY`** (you must actually place a Match Call to
Mr. Stone) → closing msgbox → Scientist leaves → **sets `VAR_RUSTBORO_CITY_STATE = 7`**.
- The multichoice part is satisfiable with `wait_for_multiple_choice_question(3)` (picks
  POKéNAV). The PokéNav **app** then opens — and its looped tasks (`Task_Pokenav`/
  `Task_RunLoopedTask`) **only advance when the BG/OBJ renderer is ON**. Headless
  (video off) it never progresses (~150 A-presses/1500f = 0 progress). With the renderer
  ON it drives normally.
- **SOLUTION (user directive: be faithful, keep state-write as fallback) —
  `handle_pokenav_match_call_tutorial()`:** FAITHFULLY plays the tutorial when the renderer
  is on. Harness-verified full sequence (screenshots confirm each screen): navigate south a
  step → Scientist fires → `wait_for_multiple_choice_question(3)` (POKéNAV) → PokéNav main
  menu (cursor on **HOENN MAP**) → **Down,Down → MATCH CALL → A** (call list, cursor on
  **MR. STONE**) → **A** (CALL/CANCEL submenu, cursor on **CALL**) → **A** (place the call)
  → advance Mr. Stone's call with **A** → **B** out of the PokéNav → the script resumes and
  sets `VAR_RUSTBORO_CITY_STATE=7`. Proven end-to-end via `_play` (video on): app opens,
  call placed, clean stop, no fallback. **FALLBACK:** if the renderer is off (headless) or
  the nav stalls, it calls `skip_pokenav_match_call_tutorial()` — a state-write to vanilla's
  EXACT end-state (`RUSTBORO_CITY_STATE=7` + `ROUTE104_STATE=1` + flags `HAS_MATCH_CALL` /
  `ADDED_MATCH_CALL_TO_POKENAV` / `HIDE_RUSTBORO_CITY_SCIENTIST`) — so the tutorial always
  clears and never hangs. See DECISIONS-LOG 2026-07-21 (revised).
- **KEY LESSON:** the PokéNav (and likely other full-screen apps) need `context.video=True`
  to drive; the harness added a `--video` flag for exactly this.

**The Rustboro rival — trigger LOCATED + wired.** `RustboroCity_EventScript_RivalTrigger0..7`
is a **row of coord-triggers at y=53, x 12–19**, gated on **`VAR_RUSTBORO_CITY_STATE == 7`**
— i.e. the tutorial-skip both clears the tutorial AND arms the rival. `fight_rustboro_rival()`
now: lead strongest → navigate to staging **(16,52)** (just N of the row; navigating
straight onto a trigger tile can be refused as a scripted-event tile) → **step Down across
y=53** → battle → win (`DEFEATED_RIVAL_RUSTBORO`). Harness-proven: staging→Down→(16,53)→
`MET_RIVAL_RUSTBORO=True`→battle starts.
- **DIFFICULTY — type matchup (handled: type-aware lead + attempt-cap, user-chosen).** A
  Mudkip start makes the rival LEAD a grass **Grovyle**; our Marshtomp (Water/Ground) is
  **4× weak to Grass** (confirmed via the type chart), so "lead strongest" is the WRONG
  lead. `_lead_best_matchup(["Grass"])` picks the battler with the lowest incoming-Grass
  multiplier (tie-break by level) — on our test team it correctly leads a 1× mon
  (Poochyena) instead of the 4× Marshtomp. `fight_rustboro_rival` no longer sets the lead
  itself (the caller does). **Attempt-cap:** `StoryMode.RIVAL_MAX_ATTEMPTS = 3` bounds the
  train→fight→whiteout retry so a thin team stops cleanly to manual instead of looping.
- **WIRED into `_play` §5b/§5c:** `return_devon_goods_and_get_pokenav` →
  `handle_pokenav_match_call_tutorial` (FAITHFUL; state-write fallback) → §5c:
  `_prepare_for_fight(band 16-19)` → `_lead_best_matchup(["Grass"])` → `fight_rustboro_rival`
  (stage (16,52), Down across y=53) → guard `DEFEATED_RIVAL_RUSTBORO` → clean stop.
  **Validated:** faithful tutorial end-to-end; type-aware lead selection correct; §5c wiring
  runs error-free (training toward the rival) and is bounded. **NOT yet validated: an actual
  rival WIN** — the frontier test save (`devon_done`) has a pathological team (Marshtomp +
  L7-8 filler) that loses regardless of lead; a natural post-gym team is needed to prove the
  win. On a thin team the attempt-cap stops cleanly (no regression).
- Harness drivers (dev tooling, not committed): `--driver pokenavtut|pokenavclear|pokenavskip|pokenavfaith`
  (+ `--video` to enable the renderer for the PokéNav app).
- **NEXT build:** Route 104 south → Mr. Briney's cottage → sail to Dewford → Granite Cave
  (Steven's Letter) → Gym 2 (Brawly, dark-cave puzzle) → Knuckle Badge.

### §Ch6 ATLAS — Route 104 S → Mr. Briney → Dewford → Granite Cave → Gym 2 (static ROM recon, 2026-07-21)
Recon via `tools/story-dev/maprecon.py` (static `get_map_data`, no navigation). Coordinates are
map-local. **NOT yet built or live-verified** — this is the build map for the next session.

- **ROUTE 104 (0,19) — size 40×80.** Connections: **North→Rustboro**, **South→Route 105**,
  East→Petalburg. Key objects: `Route104_EventScript_Rival` at **(17,50)** — an ALTERNATE
  rival-encounter site: the object is positioned ONLY while `FLAG_MET_RIVAL_RUSTBORO` is
  unset (a player who skipped the Rustboro meeting gets caught at the cottage instead;
  decomp-verified `Route104_EventScript_TrySetRivalPos`). After our Rustboro rival win the
  NPC is hidden and the cottage door is clear (validated 2026-07-22). Pretty Petal flower
  shop entrance = warp (5,18). Cut tree at (35,22) gates the NE; items scattered (Potion
  (5,8), PP Up (39,15), X Accuracy (37,22), Poké Ball (29,53)).
  **FULL WARP TABLE (doorprobe-verified 2026-07-22):** #0 (17,50)→Briney's house (5,8);
  #1 (5,18)→flower shop; #2/#3 **(10,30)/(11,30)→WOODS (14,5)/(15,5)** (north doors);
  #4/#5 **(10,38)/(11,38)→WOODS (16,38)/(17,38)** (south doors); #6/#7 (32,42)/(33,42)→
  WOODS (36,38)/(37,38) (east pair).
- **MR. BRINEY'S HOUSE (17,0) — 12×9.** `…Briney` NPC = **local_id 1** (spawn (5,3)),
  Peeko = local_id 2 (spawn (6,3)). ‼ **BOTH PATROL a walk-sequence ring around the central
  table** (route tiles x∈{6..9}, y∈{3..6}; Peeko laps AHEAD of Briney, same direction) —
  Briney is almost never at (5,3); talk via `_talk_to_wandering_npc` (observe → park beside
  route → A on transit; see playbook). Exits (5,8)/(6,8) → Route 104 (17,50).
  **Talk to Briney → he sails you to Dewford.**
- **DEWFORD TOWN (0,11) — 20×20.** Connections: North→Route 106, East→Route 107. Warps:
  PC/houses/hall at (3,3),(2,10),(8,17),(17,14),(8,8). `DewfordTown_EventScript_Briney` at
  **(12,9)** = the boat dock (Briney ferries Dewford↔Route104/Slateport). OldRodFisherman
  (12,14). **Gym entrance:** Dewford Gym warp is Dewford **warp#2** (from the gym side,
  (5,27)/(6,27)).
- **DEWFORD GYM (3,3) — 18×28 (DARK gym).** `Brawly` at **(4,3)** (top). Trainers: Takao
  (2,18), Jocelyn (15,3), Laura (12,25), Cristian (7,8), Lilith (16,9), Brenden (14,12);
  GymGuide (5,24). Entry warp (5,27)/(6,27) at the bottom. The room is dark (Flash helps but
  isn't required); path bottom→top to Brawly. **Beat Brawly → Knuckle Badge (BADGE02).**
- **GRANITE CAVE (Route 106, west of Dewford):** `GRANITE_CAVE_1F (24,7)` entrance warp
  (37,12)→Route 106; internal warps to B1F. `…B1F (24,8)` warp (12,3)→Steven's Room. Steven
  is in **GRANITE_CAVE_STEVENS_ROOM (24,10)** at **(7,8)** — **deliver Steven's Letter here.**
  (Granite Cave also holds items: Escape Rope 1F (17,7), Poké Ball B1F (15,21), Repel/Rare
  Candy B2F; B2F has Rock-Smash rocks — later.)

**SAIL LEG — BUILT + VALIDATED end-to-end (2026-07-22).** `sail_to_dewford()` runs
post_rival.ss1 → Dewford (harness `--driver saildewford`; checkpoint **`dewford.ss1`**).
The route (every leg keyed off the LIVE map, resume-safe): Rustboro (16,53) → Down across
the connection → ROUTE104 (16,0) north strip → navigate (11,29) → north door (11,30) →
Woods (15,5) → cross southbound → inside door (17,38) → Route104 (11,38) south beach →
door (17,50) → cottage → `_talk_to_wandering_npc(Briney id=1)` → **first sail = YES/NO**
(A-through; cursor defaults YES) → warped to the boat (Route104 (13,51)) → sail cutscene
(B-through) → DEWFORD_TOWN, arrive at the dock (12,3).
‼ **CORRECTION to the earlier recon:** the `MULTI_BRINEY_OFF_DEWFORD` multichoice belongs to
LATER sails; the FIRST sail is a plain YES/NO ("You have a LETTER bound for DEWFORD… We'll
set sail" — decomp-verified `Route104_MrBrineysHouse` scripts; sets `VAR_BOARD_BRINEY_BOAT_
STATE=1`, hides house-Briney/Peeko, `RUSTBORO_CITY_STATE=8`, `ROUTE104_STATE=2`). The code
handles BOTH (A-through answers the yesno YES; a multichoice task is answered with index 0).

**Original build plan (superseded by the build above):** (1) Route 104 SOUTH to
Mr. Briney's house entrance → enter → talk to Briney → sail (anchor: arrive DEWFORD_TOWN).
(2) Dewford: deliver **Steven's Letter** — Route 106 W → Granite Cave 1F→B1F→Steven's Room
(7,8), talk to Steven (anchor a letter/received flag). (3) Dewford **Gym 2 (Brawly)** — heal,
lead-strongest (Brawly = Fighting; lead a Flying/Psychic if we have one, else strongest),
navigate the dark gym bottom→top to Brawly (4,3), win → **BADGE02**. **Hardening:** map each
warp live before trusting it (house-entrance warps resolved oddly in static recon); verify the
Briney sail trigger + the Granite Cave floor-warp chain; heal before Brawly; expect Brawly's
Makuhita/Machop to hit hard — train to band before the gym like Roxanne.

### §Ch6–8 DEEP BUILD PLAN — Rustboro → Dewford → Granite Cave → Brawly → Slateport (2026-07-21)
> Prepared for Fable 5. **Coordinates below are from static ROM recon (accurate — real map
> data).** Anything about the exact stand-here/press-this SEQUENCE is tagged **`⚠ VALIDATE
> LIVE`** — run it in the harness and correct this doc as you go. Scripted-beat logic marked
> **`✓ script-verified`** was read from the pokeemerald decomp (authoritative). Start from a
> post-rival save (`post_rival.ss1`: Rustboro (16,53), `RUSTBORO_CITY_STATE=8`,
> `DEFEATED_RIVAL_RUSTBORO=True`; regenerate via the fresh-run recipe in playbook §2).

**Full recon dump**: regenerate with `tools/story-dev/maprecon2.py` (regenerate with a
`maprecon.py`-style `get_map_data` sweep). Key connections (map graph):
Rustboro –(S)→ **Route 104** –(S)→ Route 105 –…; Route 104 also –(N)→ Rustboro, –(E)→ Petalburg.
**Dewford Town** –(N off -60)→ Route 106 –(N)→ Route 105; Dewford –(E)→ Route 107 –(E)→ Route
108 –(E off -40)→ **Route 109** –(N)→ **Slateport City** –(N)→ Route 110 (→ Mauville, Gym 3).
Granite Cave entrance is on **Route 106 (48,16)**.

**Chapter 6 — sail to Dewford. ✅ BUILT + VALIDATED end-to-end (2026-07-22),** wired into
`_play` as Segment 6 (gated on ¬DELIVERED_STEVEN_LETTER ∧ ¬BADGE02; guard: map==DEWFORD).
`sail_to_dewford()` in early_game.py; harness driver `saildewford`; checkpoint `dewford.ss1`.
1. From Rustboro (16,53), **walk Down** → crosses the south connection onto **ROUTE104 (16,0)**
   (north strip). ✅ (leg-by-leg; the global navigator won't one-shot it).
2. **‼ Route 104 is river-split.** The ONLY north↔south path is back through Petalburg Woods.
3. North strip → **Woods north door (11,30)** (stage (11,29)) → inside (15,5) → cross the Woods
   southbound → **inside south door (17,38)** (stage (17,37)) → Route104 **(11,38)** south
   beach → **Briney's door (17,50)** → cottage interior (5,8). ✅ all doorprobe-verified + run.
4. Talk to **Briney (local_id 1 — he PATROLS; use `_talk_to_wandering_npc`)**: FIRST sail is a
   **YES/NO** (A-through = YES); later sails use the `MULTI_BRINEY_OFF_DEWFORD` multichoice
   (Dewford = index 0) — both handled. ✅ decomp-verified + run.
5. Confirming warps to the boat (Route104 (13,51)); ride out the sail (B) → `DEWFORD_TOWN`,
   dock (12,3). ✅

**Chapter 7 — Granite Cave (Steven's Letter) + Gym 2 (Brawly).**
- **Dewford Town map:** PC entrance = warp **#1**; Gym entrance = warp **#2**; Hall = #0-ish;
  Briney (boat for Slateport later) stands at **(12,9)**. `⚠ VALIDATE LIVE` which door is which.
- **Steven's Letter** `✓ script-verified` + **ladder chain pathfinder-verified 2026-07-22**:
  Dewford –(N)→ **Route 106** → Granite Cave entrance **(48,16)** → `GRANITE_CAVE_1F` (land
  (37,12)). **‼ EVERY cave floor is split into disconnected walk-sections**; the route to
  Steven is the FIVE-WARP CHAIN (matches vanilla, dips through B2F):
  **1F (17,11) ↓ B1F (4,21) → (28,21) ↓ B2F (28,21) → (29,13) ↑ B1F (29,13) → (25,13) ↑
  1F (35,3) → Steven's door 1F (5,10) → room (7,3)**. Section membership on a floor is
  ambiguous by coordinates — the code resolves it by LIVE pathability (`_walk_warp_chain`).
  **`GRANITE_CAVE_STEVENS_ROOM`, Steven at (7,8)** (static). Talk from (7,7) facing Down
  (A-through, no choices): hand over `ITEM_LETTER` → **`setflag FLAG_DELIVERED_STEVEN_LETTER`**
  → receive **TM47 Steel Wing** → Steven registers in the PokéNav → he departs + despawns.
  Return = the exact reverse chain. Completion flag: `DELIVERED_STEVEN_LETTER`. (Cave is
  dark; Flash irrelevant to the bot.) 1F Hiker trainer at (36,9) near the entrance; Route
  106 beach trainers Elliot (51,14) / Ned (65,14). **‼ NO TRAINING GRASS around Dewford
  pre-Surf** — Route 106/107/Dewford have ONLY surf encounter tables; Granite Cave 1F land
  wilds are L6-10 (probed 2026-07-22).
- **Gym 2 — Brawly** (Fighting): `DEWFORD_TOWN_GYM` (18×28, DARK). Brawly at **(4,3)** (top);
  entrance warp (5,27)/(6,27) at the bottom; trainers scattered (Takao (2,18), Jocelyn (15,3),
  Laura (12,25), Cristian (7,8), Lilith (16,9), Brenden (14,12)). Path bottom→top. Mirror the
  Roxanne prep: **heal → level-floor → TYPE-AWARE lead** (Brawly's Makuhita/Machop are Fighting —
  lead a **Flying or Psychic** mon, e.g. Taillow/Abra, which resist/counter Fighting; NOT a
  Normal mon which is weak to it) **→ attempt-cap → fight**. Win → **BADGE02 (Knuckle Badge)**.
  `⚠ VALIDATE LIVE` the dark-gym path + the completion flag (BADGE02_GET).

**Chapter 8 — sail to Slateport + Slateport.** (Recon done; build after Ch7.)
- After Brawly, **Mr. Briney at Dewford (12,9)** offers **Slateport** (`⚠ VALIDATE LIVE` the exact
  gating — likely after BADGE02 and/or the Letter; read the DewfordTown decomp when you build it).
  Sail → **Route 109** (Briney appears at (109 21,24)) → North → **Slateport City**.
- **Slateport City** (40×60): PC door (30,26?→ actually PC=(19,19)); Mart; **Oceanic Museum**
  doors **(30,26)/(31,26)**; **Stern's Shipyard** door **(26,38)**; the Harbor **(28,12)/(40,7)**.
  NO gym here — the next gym is **Wattson (Gym 3, Mauville)** via Route 110 north.
- **‼ Ch8b SEQUENCING (walkthrough + decomp-verified 2026-07-22, KI-11 — the doc was WRONG
  before):** the Oceanic Museum is **grunt-SEALED** on arrival. 11 outside Team Aqua grunts
  share hide-flag `FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` (882, unset by default); two of them
  (obj id 5/18) sit on **(31,27)/(30,27)**, the ONLY tiles below the museum doors, so the
  entrance is impassable. **You must FIRST go to Stern's Shipyard (city door (26,38)) and talk
  to DOCK (interior (5,5); approach from (4,5) facing Right — he's walled below).** Dock's
  script `✓ decomp`: `setflag FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA` + `FLAG_DOCK_REJECTED_DEVON_
  GOODS` → the grunts go inside, the entrance CLEARS. THEN enter the museum: fee attendant
  (7,7)/(12,7) ¥50 YES/NO (broke+undelivered → free entry); the Rusturf "familiar grunt" (9,4)
  gives **TM46 Thief**; stairs 1F (6,1) → 2F. **Capt. Stern is on 2F at (13,6)** (NOT the
  (28,13) the old doc said — that was the harbor Stern). Talk → two BACK-TO-BACK un-fleeable
  grunt battles (TRAINER_GRUNT_MUSEUM_1/2) → Archie speech → **`FLAG_DELIVERED_DEVON_GOODS`** +
  the script HEALS the party + removes the Route 110 Aqua blockade (unblocks Ch9). Built:
  `deliver_devon_goods_to_stern` (Shipyard→Dock→museum→Stern).
- **‼ DOUBLE BATTLE:** **Gabby & Ty** (Interviewers) stand at Slateport **(28,14)/(29,13)** and are
  a DOUBLE battle. This is the first likely double-battle in the run — the after-faint double-battle
  fix (exclude the on-field partner) applies here. Validate a real Gabby & Ty double battle to
  confirm the fix end-to-end (and to smoke-test the OPEN framework rotation-execution stall).

**Reusable pattern for every gym/boss (from Roxanne + the rival):** heal at the PC → whole-team
**level-floor ≥N** (escalating on losses) → **type-aware lead** (never lead a mon weak to the
boss's ace) → **safe heal** → fight with an **attempt-cap** (retrain+retry a bounded number, then
stop cleanly). Trainer/gym/E4 battles **attack through, never rotate/flee** (see §Battle rules /
playbook §6).

---

## §DA. DIALOGUE AWARENESS — read the text to drive interactions (user 2026-07-20)

**Is it possible? YES — verified.** The bot can decode the exact on-screen text:
- `decode_string(read_symbol("gDisplayedStringBattle"))` → the current BATTLE text
  (e.g. `"Delete a move to make room for WATER GUN?"`, `"CASTFORM is trying to
  learn WATER GUN."`).
- `decode_string(read_symbol("gStringVar4", size=0x3E8))` → field/NPC dialogue.
- Menu/choice state via the yes/no + multichoice tasks (see
  `wait_for_yes_no_question` / `wait_for_multiple_choice_question`).

**Why this is the right architecture:** the internal task/script state for these
prompts FLICKERS, and driving off it caused the move-learn hang that resisted
many state-based fixes (ML-11). Reading what the game ACTUALLY SAYS is
deterministic — the text is stable and unambiguous. It also generalises: the same
reader handles ANY conversation (move-learn, evolution, nickname, NPC yes/no,
fossil/starter multi-choice) so the bot can progress the story flexibly.

**Architecture (build incrementally):**
1. **Reader** — one helper that returns the normalized current text (battle vs
   field) + whether a yes/no or multi-choice menu is up (task-based) + the cursor.
2. **Classifier** — match the text against a table of known prompts → an
   interaction TYPE (move-learn / nickname / yes-no / multi-choice / plain-advance).
3. **Responder** — given the type + STORY PROGRESS (chapter/flags) + config,
   produce the answer. Decisions with MULTIPLE valid answers (fossil, starter,
   which-house) are RANDOM/config (like the random-starter pick we already do).
4. **Backstops** — a no-progress watchdog + "advance plain text with A" so nothing
   can ever hard-freeze even on an unrecognised prompt.

**Data to gather (the user's "conversation dumps"):** per interaction, capture
{exact text, speaker, is it a menu, valid answer(s), how to answer}. Source it
from the on-screen text at runtime (log every distinct `gDisplayedStringBattle` /
`gStringVar4` we hit) AND the pokeemerald script/text data the bot already bundles.
Build a response table keyed by text pattern → general answering algorithm.

**Status:** move-learn now uses text-driven detection (dispatch + advance) as the
first piece (2026-07-20). Full system = punch-list #24-textread; it also subsumes
the fragile parts of scripted-scene ride-outs. Recommended next big build once the
core chapters are stable.

**★ ROOT CAUSE of the Lv16 move-learn hang — confirmed & fixed (ML-13, 2026-07-20).**
The mechanism, found by faithfully reproducing the freeze:
- The Emerald *battle* "Delete a move to make room for X?" Yes/No has **NO backing
  task** — `tasks=[]` throughout. `get_learn_move_state()` can only recognise it by a
  **fragile script-offset** (`gBattleScriptCurrInstr == BattleScript_AskToLearnMove +
  0x11`). When that offset is never observed the state stays **`Unknown`**.
- The old `Unknown` branch pressed A **only when `is_waiting_for_input()`** — which
  reads the FIELD text-printer (`sTextPrinters[0]`), lags ~140 frames in battle and
  can be **permanently False**. Fragile-state + unreliable-gate ⇒ presses NOTHING ⇒
  frozen on the Yes/No (exactly the user's report).
- **Fix:** `handle_move_replacement_dialogue` is now fully **text/task-driven** — the
  Yes/No is detected from the on-screen TEXT (`"make room for"` / `"Delete a move"`)
  as well as the state; the move-select is driven by the reliable
  `Task_HandleReplaceMoveInput`; every other text box is advanced with A **directly**
  (never gated on `is_waiting_for_input`). `handle_evolution_scene`'s move-learn
  hand-off was hardened the same way (breaks on state OR text OR the move-select task).
- **How it was proven — FAULT-INJECTION A/B** (`scratchpad/repro_movelearn.py
  --break-state`): force `get_learn_move_state` to never report AskWhetherToLearn (→
  Unknown) and `is_waiting_for_input` → False (the user's failing env). OLD code stalls
  **~10,600 frames** and fails to learn the move; the FIX resolves in **394 frames**,
  learns Pursuit, evolves to Grovyle (moveset: Fury Cutter, Pursuit, Absorb, Quick
  Attack). Verified on BOTH builds. Lesson: the Emerald battle Yes/No prompts are NOT
  task-backed — read the text; never gate a battle press on `is_waiting_for_input`.

---

## §SC. SELF-CORRECTION / SANITY-CHECK — "Story mode needs to be smarter" (user 2026-07-20)

**Goal:** the bot must NEVER get permanently derailed. If it somehow skips a beat,
ends up somewhere unexpected, or jumps BACKWARD (a watchdog reload, a blackout
respawn, or a hand-played detour), it should recognise its ACTUAL state and get
back on track from wherever it really is — not blindly follow the script.

**Principles (the backbone that makes Story mode "smart"):**
1. **Truth = the live game state, never the script's assumptions.** Every step
   answers "am I done? / where am I? / what's next?" from FLAGS + MAP + PARTY
   (like §RS), never from "I already called this function."
2. **Re-validate at EVERY segment boundary.** After running a segment, CHECK its
   completion flag actually set — if not, the segment silently failed/derailed →
   retry it (bounded) or, if a LATER flag is set, skip ahead. Before a segment,
   re-detect in case the world moved under us.
3. **Handle out-of-place execution.** If a step's start location isn't where the
   player is (blackout dropped us at a Poké Center; a warp went wrong), the step
   SELF-LOCATES (navigate-from-anywhere, §RS-fast-travel) instead of assuming.
4. **Non-monotonic progress is normal.** A reload/blackout moves progress
   BACKWARD; detection must handle progress going down, not only up.
5. **Bounded retries + escalation, never an infinite loop.** Each objective tracks
   attempts; repeated failure escalates (train / adjust team — §DR + #24-team)
   rather than spinning. A hard "no progress for N frames" stall watch (the
   Watchdog #22) is the last-resort safety net; ideally the boundary checks catch
   it first.
6. **Detect derailment mid-run, not only at start.** Periodically (or at
   boundaries) compare EXPECTED segment vs the segment the live state implies; on
   mismatch, re-run full detection and re-enter the correct segment.

**IMPLEMENTED v1 (2026-07-20):** `StoryMode.run()` now calls `_guard(label,
done_check)` AFTER each segment — if the segment didn't reach its completion
signal (flag/map), it raises a diagnostic BotModeError (→ Manual) naming where it
actually is, instead of blindly proceeding and compounding the derail; re-running
Story then resumes correctly from the real state. Verified no false-fire on the
happy paths (gym1_done all-skip; woods/petalburg resumes). This also catches a
gym/battle LOSS (blackout → not in the expected state → guard fires → recover on
re-run). REMAINING (below): bounded auto-retry, self-locate, mid-segment stall
watch for the battle-handler hang class.

**Implementation sketch (future, #24-sanity):** wrap the segmented `run()` (§RS)
so each segment is: (a) precondition — skip if its completion flag is already set;
(b) locate — navigate to the start if not there; (c) execute; (d) postcondition —
confirm the completion flag set, else retry/escalate. Add a boundary "expected vs
actual" re-detect. This unifies with §RS (resume), §DR (defeat response) and
#24-team into ONE state-machine engine. It also fixes the Treecko-Lv16-style
"stuck but not stopped" class by giving the loop a stall/attempt bound.

---

## §DR. DEFEAT RESPONSE — what the bot does when it LOSES a battle (design, user 2026-07-20)

**Today:** a lead faint the strategy can't recover from (trainer battle → can't
flee/rotate → faint → the game blacks you out; or the strategy dropping to Manual)
is caught by the **Watchdog** (`modules/watchdog.py`, #22): attempt 1 RE-ASSERTS
the mode (clears the controller stack, re-runs `StoryMode.run()`); attempt 2+
RELOADS the last healthy in-memory save state and re-runs the mode. **The segmented
resume run() (§RS) already fixes most of the "it picks up from a weird earlier
state" problem** — the OLD run() just detected-and-went-manual on any restart, so
a fault stranded the bot; the NEW one re-detects the chapter and continues.

**Goal (make it a chosen behaviour, exposed in the settings popup #24-ui):**

### Mode A — "Reload save state" (current watchdog behaviour, made a toggle)
On defeat, reload the last healthy save state + restart the mode (which now
resumes via §RS). Toggleable. FIX/verify the rough edges the user saw:
- The watchdog's snapshot must be a CLEAN OVERWORLD state (never mid-battle /
  mid-cutscene) — reloading a mid-scene snapshot is what makes resume confused.
- Confirm that after a fault the restarted StoryMode resumes the RIGHT segment
  (should now work via §RS — verify live).

### Mode B — "Play through & retry" (new, ORGANIC / human-like)
Don't reload — let the blackout happen and play it forward:
1. **Ride out the whiteout prompts** → the game respawns you at your last heal
   point (usually the last-visited **Poké Center**; sometimes a HOUSE in early
   story beats — e.g. Mom heals at the Littleroot house pre-first-Center).
2. **Recalculate position:** read the current map/coords after respawn and use the
   §RS segment detection to know WHERE you are and WHAT the next/failed objective
   is (the segment whose completion flag is unset = the thing you just lost).
3. **Failure-aware retry with a MATCHUP ASSESSMENT** — before re-attempting a
   battle-heavy objective (gym / rival / strong trainer), score whether the team
   can win, from:
   - **avg enemy team level vs own** team (and lead) level,
   - **team size** (# usable non-fainted Pokémon),
   - **type matchup**: our Pokémon types + our damaging-move types vs the
     opponent's known types (super-effective coverage we have / weaknesses we
     expose). Reuse the type data already in the dex.
   If the score says OUTMATCHED → **train** (grind levels on a nearby route,
   healing at the Center) and/or **adjust the team** (catch a helper of a needed
   type — this IS #24-team) BEFORE reattempting.
4. **Escalate on repeated failure:** track a per-objective loss count; each loss
   raises the effort (more training, more likely to recruit a helper) — the SAME
   rising-urge model as #24-team. Guarantees progress, no infinite retry loop.
5. Navigate back to the objective (via §RS; fast-travel when #24-resume lands) and
   retry.

**Convergence:** Mode B = §RS resume + a matchup gate + #24-team escalation, all
triggered by a blackout. The three features share one engine; build them together.

**Settings-popup toggles (#24-ui → "Defeat response" section):** choose
Reload-save-state vs Play-through-and-retry; (Mode B) auto-train-before-retry
on/off, auto-catch-helper on/off. Default TBD with the user.

**Punch-list:** #24-defeat (this whole system). Depends on §RS (done), the matchup
scorer (new, small), and #24-team (helper recruiting).

---

## §RS. RESUME MODEL — pick up from wherever the save is (user 2026-07-20)

**Goal:** run the bot from ANY point — a fresh game, a resumed save, or a game
you hand-played partway — and it figures out what's already done, what the next
task is, and continues. Never re-do finished steps (the "it thinks I still need
Wally" bug), and eventually navigate to the next task from anywhere (walk / fly /
teleport / escape rope).

**Implemented (v1):** `StoryMode.run()` is now SEGMENTED. The story is linear, so
each segment runs only if its completion signal isn't set:
- Chapter 0 intro — title screen only (mid-intro isn't a resumable point; it must
  run from the truck). A title screen WITH a save should Continue first (TODO).
- Seg 1 truck→Pokédex — gated by `RECEIVED_POKEDEX_FROM_BIRCH`.
- Seg 2 Petalburg+Wally — gated by `HIDE_PETALBURG_CITY_WALLYS_MOM` (the intended
  `THANKED_FOR_PLAYING_WITH_WALLY` is never set — found by flag-diffing pre/post
  Wally saves; chapters.py Ch2 milestone updated to match, fixing detection).
- Seg 3 Woods→Rustboro — done if in Rustboro or `BADGE01_GET`; picks its
  SUB-ENTRY by current map (resume inside the Woods → start at
  `cross_petalburg_woods`, don't backtrack to Petalburg).
- Seg 4 Gym 1 — gated by `BADGE01_GET`.
Verified: gym1_done → skips all → manual; woods_entered → skips intro+Wally,
resumes the Woods crossing; petalburg → skips intro, does Wally. Segments
self-locate via `navigate_to_anywhere`.

**TODO (refinements → punch-list #24-resume):**
- Finer per-STEP resume + each step self-locating from ANY tile (currently
  segment-level; a resume in an odd spot may relocate sub-optimally).
- FAST travel: use Fly / Teleport / Escape Rope / dig when available instead of
  always walking (needs the HM/badge/item gating from #42).
- Title-screen-with-save → auto-select Continue (today the title path assumes a
  save-less New Game).
- Reliable per-chapter completion flags for chapters beyond Gym 1.

---

## §AA. AREA ATLAS — hand-craft each area's recovery/routing facts (user 2026-07-21)

**The rule (do this BEFORE scripting any area's logic):** blanket, universal
assumptions ("every Poké Center exits the same", "a flag is set so I must be in
town X") are the root of the derail bugs. Each area is unique and must be
hand-crafted. Before building an area's story logic, MAP and record here:
- **Respawn point** — which Poké Center the player wakes at after a whiteout in this
  area (the last one healed at). Recovery routes FROM here back to the objective.
- **Nearby grass** — a reachable grass tile for training/catching (with encounters).
- **Inter-map routing** — how to get from this area to adjacent areas / the next
  objective, leg-by-leg (warp-split maps like Route 104-via-Woods can't be one-shot
  routed — ML-7).
- **Key event/fight locations** — where each major fight/event triggers (map +
  approach tile), so localization can route back to "the current objective".

**How the bot uses it (already partly wired):** the segmented resume re-navigates
from wherever the player actually is (so a Petalburg respawn while the objective is
Roxanne re-runs the Woods travel back to Rustboro — it does NOT assume location from
flags). Recovery steps out of the respawn Poké Center first (robust warp exit),
waits for a stable state, then re-runs the resume. A non-whiteout derail
re-localizes (logs stage+map via `detect_live`) and retries a bounded number of
times before Manual (§SC). PC exits and training/catching navigation now ride out
scenes and fire warps from a fresh step (robust, not blanket-fragile).

**ATLAS — region covered so far (Littleroot → Rustboro → Rusturf):**
| Area / stage | Respawn PC | Nearby grass (encounters) | Key locations | Notes |
|---|---|---|---|---|
| Littleroot / Route 101-103 (intro→starter→rival→Pokédex) | Oldale Town PC | Route 103 grass (5,7) | Route 103 rival approach (10,4); Birch lab | pre-Pokédex = no balls (no catching) |
| Petalburg / Route 102-104 south / Woods | Petalburg City PC (then Rustboro once healed there) | Route 104 south, Petalburg Woods | Petalburg Gym (Norman/Wally); Woods researcher scene | Route 104 is WARP-SPLIT by the Woods — go leg-by-leg (ML-7) |
| Rustboro / Route 116 / Rusturf | **Rustboro City PC** (16,38→city) | **Route 116 (11,7)** — 101 grass tiles, straight east of Rustboro | **Roxanne** gym (map (11,3), approach (5,4)); Devon Corp warps (11,15)/(12,15); Rusturf grunt (tunnel (13,5)) | training/catching spot for Gym 1; PC 1F exit warp (6,8)/(7,8) |

Standard Emerald Poké Center 1F: exit warp (6,8)/(7,8); after a whiteout the player
respawns ON the warp — walk to (7,7) and step DOWN to fire it (do NOT navigate onto
the warp tile, it can stop there without firing — ML-9).

**LONG-DISTANCE INTELLIGENCE (future):** the user's example — respawn at Petalburg
while fighting Roxanne must route Petalburg→Woods→Rustboro→gym. The segmented resume
handles this today by re-travelling; formalize per-area routes here as areas grow so
the router never has to guess.

---

## 0. TL;DR for a future agent

The bot is a **shiny-hunting automation** whose primitives happen to be exactly
what a story-player needs: it already **auto-wins wild AND trainer battles to
completion**, **pathfinds across connected maps** (auto-surfs/waterfalls),
**advances scripted dialogue by reading the game's own task/script scheduler
(not pixels)**, **types on the naming keyboard**, **teaches HMs/TMs**, **uses
every field move**, **shops, heals, talks to NPCs, manages the PC**, and can
**read every story flag/var/badge/item** to know where in the plot a save is.

The story bot is therefore **mostly a composition + sequencing layer**, plus a
handful of genuinely-new pieces:

1. **Intro automation** — Birch speech, **gender select**, **player-name entry**
   (none exist; keyboard typer exists but is wired only to nicknames).
2. **A chapter/objective orchestrator** — every existing mode is a self-contained
   map-specific routine; there is no cross-map "advance the plot" driver.
3. **Per-obstacle field-move routing on the critical path** — the *execution*
   of Cut/Strength/etc. exists, but nothing routes the avatar to the specific
   story-critical tree/boulder and detects it. `puzzle_solver.py` only covers
   end-game puzzle maps.
4. **Cross-region warp navigation is built but unwired** (`navigate_to_anywhere`)
   and cannot open locked/HM/story-gated doors — it fails at runtime instead.
5. **Better boss-battle AI** — move selection is competent but naive (pure
   max-damage; no status/setup/switching). Serviceable for most trainers;
   risky for gyms/Elite Four without a stronger `decide_turn`.

---

## 1. Goal + Approach

### 1.1 Goal
From a **fresh save** (or a **continued** one), drive Pokémon Emerald all the way
to **beating the Elite Four + Champion Wallace** (endgame flag `SYS_GAME_CLEAR`
/ `IS_CHAMPION`). Full living-dex completion is explicitly a *later* concern
(punch-list #45); v1 stops at Hall of Fame.

### 1.2 Fresh-or-continue + user-set identity
- **Fresh:** start a New Game, drive Birch's intro, set **gender** (user choice)
  and **player name** (user string), through to stepping out in Littleroot.
- **Continue:** load an existing save and **detect the current chapter** from
  event flags/badges, then jump into the correct chapter mid-stream.
- **Character name/gender** are stored as story-mode config, applied only on the
  fresh-start path. They are readable back afterward via `Player.name`
  (`modules/player.py:187`) and `Player.gender` (`modules/player.py:191`).

### 1.3 The Chapter model (discrete, resumable milestones)
Progress is modeled as an **ordered list of Chapters**, each a small state
machine with:

- **`is_complete()`** — a predicate over event flags/vars/badges/items/party/map
  that returns true when the chapter's outcome already exists in the save. This
  is what makes the bot **resumable**: on start, walk the chapter list and skip
  every already-complete chapter; begin at the first incomplete one.
- **`preconditions()`** — asserts that must hold to *run* the chapter (right
  badge, HM taught, key item in bag, party can battle). Reuses `modules/modes/
  _asserts.py` helpers.
- **`run()`** — a generator that performs the chapter (navigate, battle, talk,
  teach HM, heal, shop), exactly like an existing `BotMode.run()`.
- **`on_battle_started()` / listeners** — inherited from the `BotMode` contract
  so involuntary events (battles, whiteouts, eggs, repel) are handled by the
  existing reflex listeners (`modules/modes/_listeners.py`).

**Progress detection** is read-only and cheap — no separate save file is
strictly required because *the game's own flags are the source of truth*:
- `get_event_flag(name)` — `modules/memory.py:336` (returns False for unknown).
- `get_event_var(name)` — `modules/memory.py:393` (returns -1 for unknown).
- Badges are **not** a Player field — they are the eight flags
  `BADGE01_GET`…`BADGE08_GET` (`modules/data/event_flags/emerald.txt`, numbers
  2151–2158); badge count = number of those flags true.
- Endgame: `SYS_GAME_CLEAR` (flag 2148), `IS_CHAMPION` (2175).

**Progress persistence:** the bot's own bookkeeping (which sub-step inside a
chapter it was on, retry counts, chosen starter) is small and can live in a
JSON in the profile dir (mirrors how `hunt_target.json` / `soft_reset_frames.json`
already sit in `profiles/<name>/`). But the **authoritative** resume signal is
always re-derived from game flags on launch — the JSON is only a within-chapter
optimization, never trusted over the ROM state (matches the CLAUDE.md
"trust-but-verify" doctrine).

### 1.4 Why this fits the existing architecture
The upstream/dev docs already bless this shape: *"An AI agent playing Emerald can
be implemented as just another `BotMode`: `run()` becomes the policy loop
(observe → decide → `yield from` an action helper), and the existing listeners
already handle the involuntary events"* (`40cakes repo/DOCUMENTATION/
03-bot-modes-and-battle.md:686-691`). Story-mode is that agent, but with a
scripted (not learned) policy: a hand-authored chapter list.

---

## 2. FULL CHAPTER SKELETON (new-game → Champion)

**Legend:** *Gate* = the hard requirement to leave the chapter. *Key flag* =
the Emerald event flag that proves completion (names from
`modules/data/event_flags/emerald.txt`). HM **badge gates** that are
**confirmed in code** are marked ✅ (from `modules/map_path.py` /
`modules/menuing.py` / `modules/modes/rock_smash.py`).

### Overview table — 8 gyms, HM tie-ins, endgame

| # | Chapter | City / Area | Boss / Key battle | Badge | HM unlocked (field-use gate) | Key completion flag |
|---|---------|-------------|-------------------|-------|------------------------------|---------------------|
| 0 | Intro & Identity | Truck → Littleroot | (none) | — | — | `ADVENTURE_STARTED` (116) |
| 1 | Starter & first steps | Route 101 / Oldale / Rt 102-103 | Birch rescue; Rival (Rt 103) | — | — | `RESCUED_BIRCH` (82), `DEFEATED_RIVAL_ROUTE103` (130), var `STARTER_MON` (35), `RECEIVED_POKEDEX_FROM_BIRCH` (2276) |
| 2 | Petalburg & Wally | Petalburg City | Catch tutorial w/ Wally | — | — | (meet Dad/Wally scripts) |
| 3 | Woods (researcher rescue) & Cut | Rt 104 / Petalburg Woods / Rustboro | **[P4 FIX]** Aqua Grunt in Petalburg Woods is a **RESEARCHER-RESCUE, NOT a goods theft** — grunt flees, researcher gives a Great Ball (Bulbapedia Part 2) | — | **Cut** (HM01) obtained in **Rustboro City** (Cutter's House, W of the PC) **[P4]** | **[P4 FIX]** `RECEIVED_HM_CUT` (137). **`DEVON_GOODS_STOLEN` (142) / `RECOVERED_DEVON_GOODS` (143) do NOT belong here** — the theft (Rustboro) & recovery (Rusturf) happen AFTER Gym 1, in row 5 |
| 4 | **Gym 1 — Roxanne** | Rustboro City | Roxanne (Rock) | **Stone** | **Cut usable** ✅ (`menuing.py:812`) | `DEFEATED_RUSTBORO_GYM` (1264), `BADGE01_GET` (2151) |
| 5 | Devon errand, **Peeko rescue** & Rival | Rustboro / Rt 116 / **Rusturf Tunnel** | Aqua grunt (Rusturf); Rival (Rustboro) | — | — | **[P3 FIX]** `RETURNED_DEVON_GOODS` (144 — returned to Devon Corp Rustboro; the Rusturf grunt also drops the goods & frees Peeko, `RECOVERED_DEVON_GOODS` 143), `RECEIVED_POKENAV` (188), `DEFEATED_RIVAL_RUSTBORO` (211). **149 does NOT belong here** — that's the Slateport delivery (row 8) |
| **5b** | **[P2 MADE EXPLICIT] Mr. Briney & Peeko** — MANDATORY gate to the boat | Rt 116 → Rusturf Tunnel → Briney's cottage (Rt 104) | rescue Peeko from Aqua grunt | — | — | `MR_BRINEY_SAILING_INTRO` (147); Peeko/Briney hide-flags 738-744, 879-881 — *verify exact gate ordering live* |
| 6 | To Dewford + Steven letter (**Briney's boat**) | Rt 104/105 (Mr. Briney sails) / Granite Cave | (cave; Steven) | — | **Flash** (HM05) in Granite Cave | `DELIVERED_STEVEN_LETTER` (189), `RECEIVED_HM_FLASH` (109) |
| 7 | **Gym 2 — Brawly** | Dewford Town | Brawly (Fighting) | **Knuckle** | **Flash usable** | `DEFEATED_DEWFORD_GYM` (1265), `BADGE02_GET` (2152) |
| 8 | Slateport & Oceanic Museum | Rt 109 / Slateport | **[P2]** Aqua grunts (Museum) + Archie; deliver Devon parts to Capt. Stern | — | — | **[P3 FIX]** `DELIVERED_DEVON_GOODS` (**149** — delivered to Capt. Stern **here**, moved from row 5; dock-rejected first, `DOCK_REJECTED_DEVON_GOODS` 148); `OCEANIC_MUSEUM_MET_REPORTER` (105); Museum Aqua-grunt hide-flag 883. EARLY Slateport visit; the sub theft is the LATE beat 16c |
| 9 | Mauville & Bike | Rt 110 / Mauville | Rival (Rt 110) | — | **[P3 FIX] Rock Smash (HM06) from a man in the SOUTHEAST HOUSE of MAUVILLE CITY** (east of the Poké Mart) — **the Pass-2 "Route 111" was a REGRESSION and is WRONG** (pokemondb/Thonky/PokéCoders, §2.3); **Bike** from Rydel's, Mauville | `RECEIVED_BIKE` (90), `RECEIVED_HM_ROCK_SMASH` (107) |
| 10 | **Gym 3 — Wattson** | Mauville City | Wattson (Electric) | **Dynamo** | **Rock Smash usable** ✅ (`rock_smash.py:143` = `BADGE03_GET`) | `DEFEATED_MAUVILLE_GYM` (1266), `BADGE03_GET` (2153), `GOT_BASEMENT_KEY_FROM_WATTSON` (208) |
| 11 | Rt 111/112, Mt. Chimney (Magma) | Rt 111 desert / Fiery Path / Rt 112 / Mt. Chimney | Team Magma; Maxie | — | **Go-Goggles** (Lavaridge, for Rt 111 desert); **Meteorite** event. **[P2] HM04 Strength is from RUSTURF TUNNEL, not here** (available earlier once the tunnel is opened) | `DEFEATED_EVIL_TEAM_MT_CHIMNEY` (139), `RECEIVED_METEORITE` (115), `RECEIVED_GO_GOGGLES` (221); `RECEIVED_HM_STRENGTH` (106) — obtained at Rusturf |
| 12 | **Gym 4 — Flannery** | Lavaridge Town | Flannery (Fire) | **Heat** | **Strength usable** (`SYS_USE_STRENGTH`) | `DEFEATED_LAVARIDGE_GYM` (1267), `BADGE04_GET` (2154) |
| 13 | **Gym 5 — Norman (Dad)** | Petalburg City | Norman (Normal) — **needs 4 badges to challenge** (var `PETALBURG_GYM_STATE`, event_vars 133; door greeter blocks until then) | **Balance** | **Surf** (HM03) from a house in Petalburg **after** the gym | `DEFEATED_PETALBURG_GYM` (1268), `BADGE05_GET` (2155), `RECEIVED_HM_SURF` (122) |
| 14 | Rt 118/119, Weather Institute, Rival | Rt 118 (Surf) / 119 / Weather Inst. | **Aqua** at Weather Inst. (Emerald = Aqua, get Castform); Rival (Rt 119) | — | **[P3] Fly (HM02) is GIVEN BY THE RIVAL** (May/Brendan) after the Rt 119 battle — **not** a generic NPC (pokemondb/GameFAQs) | `RECEIVED_HM_FLY` (110) |
| **14b** | **[P3 REORDER — PREREQUISITE TO GYM 6]** Devon Scope & Fortree Kecleon | Fortree City / **Route 120** (east of Fortree) | **Steven** gives **Devon Scope** (after a Lv30 Kecleon battle on Rt 120); then reveal & battle the **invisible Kecleon blocking the Fortree Gym door** | — | **Devon Scope** (reveals Kecleon) | `RECEIVED_DEVON_SCOPE` (285), `KECLEON_FLED_FORTREE` (295) — **the Fortree Gym CANNOT be entered until this is done** (Bulbapedia/Thonky/PokéBase) |
| 15 | **Gym 6 — Winona** | Fortree City | Winona (Flying) — **rotating-gate gym puzzle** (§2.4) — **[P3] gym entry is GATED behind row 14b (Devon Scope + Kecleon reveal)** | **Feather** | **Fly usable** ✅ **[P2] Feather/BADGE06** (`menuing.py:826`; NOT `fly_to`'s BADGE03 — that's a fork bug, §2.1) | `DEFEATED_FORTREE_GYM` (1269), `BADGE06_GET` (2156) |
| 16 | Rt 120/121 → Lilycove (post-Winona travel) | Rt 120 / 121 / Lilycove | route trainers; Team Magma/Aqua sighting in Lilycove | — | (Devon Scope/Kecleon already done in row 14b) | reach Lilycove (Mt. Pyre & Aqua-Hideout arc begins next) |
| **16b** | **[P2 ADDED] Mt. Pyre** (was MISSING) | Rt 122/123 (Surf) / Mt. Pyre | Team Magma/Aqua at summit; orb theft; **summit caretaker gives the Magma Emblem** | — | Surf to reach | `HIDE_MT_PYRE_SUMMIT_MAXIE` (856). **[P4]** Progress tracked by **var `MT_PYRE_STATE` (185)**; the summit yields the **Magma Emblem key item** (gates row 16d). Exact completion value still *verify live* |
| **16c** | **[P2 ADDED] Slateport Harbor submarine theft** (was MISSING) | Slateport Harbor | Team Aqua grunts + Archie steal sub | — | — | `EVIL_TEAM_ESCAPED_STERN_SPOKE` (271); NPC-hide flags 845-848, 860 |
| **16d** | **[P2 ADDED] Magma Hideout — Groudon** (was MISSING) | Jagged Pass / Route 112 → Magma Hideout | Team Magma; Maxie; **Groudon awakened** | — | **[P3] Entry gated by the MAGMA EMBLEM** obtained at Mt. Pyre summit (row 16b); Rock Smash/Strength used inside | `GROUDON_AWAKENED_MAGMA_HIDEOUT` (111); `HIDE_MAGMA_HIDEOUT_4F_GROUDON` (853). **[P4 RESOLVED] The Magma Emblem is a KEY ITEM, not a flag** — `items.json` "Magma Emblem" (index `MAGMAEMBLEM`); the Jagged Pass entrance auto-appears when it is in the bag (Bulbapedia). Gate via `get_item_bag()`, not a flag. Mt. Pyre progress is tracked by **var `MT_PYRE_STATE` (185)** |
| 17 | Team Aqua — Hideout & Submarine | Lilycove / Aqua Hideout | Team Aqua; room-key + Electrode puzzle | — | — | `TEAM_AQUA_ESCAPED_IN_SUBMARINE` (112), `USED_ROOM_1/2/4/6_KEY` (240-243), `DEFEATED_ELECTRODE_1/2_AQUA_HIDEOUT` (452/453) |
| 18 | **Gym 7 — Tate & Liza** | Mossdeep City | Tate & Liza (Psychic, **DOUBLE**) | **Mind** | **Dive usable** ✅ (`map_path.py:690` = `BADGE07_GET`) | `DEFEATED_MOSSDEEP_GYM` (1270), `BADGE07_GET` (2157) |
| 19 | Mossdeep + Space Center | Rt 124/125 (Surf) / Mossdeep | Magma at Space Center; Steven tag (**DOUBLE**) | — | **Dive** (HM08) given in **Steven's house, Mossdeep** (`ITEM_MOSSDEEP_STEVENS_HOUSE_HM08` 1133) | `DEFEATED_MAGMA_SPACE_CENTER` (117), `RECEIVED_HM_DIVE` (123), `INTERACTED_WITH_STEVEN_SPACE_CENTER` (205) |  ‼ **ORDER CORRECTED 2026-08-12** — this beat REQUIRES Badge 7; its NPCs are hidden until then.
| 20 | Seafloor Cavern (Kyogre) | Rt 128 (Dive) / Seafloor Cavern | Team Aqua; Archie; Kyogre wakes | — | **Dive** required to enter (`can_dive` gate) | `KYOGRE_ESCAPED_SEAFLOOR_CAVERN` (129) |
| 21 | Sootopolis crisis & Rayquaza | Sootopolis (**Dive under Rt 126** to enter) / Cave of Origin / Sky Pillar | (Rayquaza quells legendaries) | — | Dive to enter Sootopolis (⛔ **no Fly** — `VISITED_SOOTOPOLIS_CITY` is False, measured). ⛔ **NO MACH BIKE NEEDED — but the ascent DELIBERATELY FALLS through ONE cracked tile.** `_CLEAN` is per-floor, not global: `2F_Clean` has 0 cracked tiles, **`4F_Clean` has 5**, and `4F (3,1)` is a SEALED POCKET reachable ONLY by falling through `4F (6,4)`/`(7,4)` (⛔ NOT `(9,4)` — a decoy). ➡ **READ §Ch21 ATLAS in this file before building; a route that avoids all cracked tiles CANNOT reach the summit.** | `LEGENDARIES_IN_SOOTOPOLIS` (83), `STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` (307), `DEFEATED_RAYQUAZA` (448), `RECEIVED_RED_OR_BLUE_ORB` (212), `WALLACE_GOES_TO_SKY_PILLAR` (311) |
| 22 | **Gym 8 — JUAN** **[P2 FIX: not Wallace]** | Sootopolis City | **Juan** (Water) — `SootopolisCity_Gym_1F_EventScript_Juan` | **Rain** | **Waterfall** (HM07) given by **Wallace in Sootopolis** (around crisis resolution; *verify exact trigger live*) | `DEFEATED_SOOTOPOLIS_GYM` (1271), `BADGE08_GET` (2158), `RECEIVED_HM_WATERFALL` (312) |
| 23 | Victory Road | Rt 128/132-134 (Surf/Dive/Waterfall) → Ever Grande | Rival Wally (Victory Road) | — | Surf+Waterfall+Dive to reach; **Strength**+Rock Smash+Flash inside | `DEFEATED_WALLY_VICTORY_ROAD` (126) |
| 24 | **Elite Four + Champion** | Ever Grande / Pokémon League | Sidney→Phoebe→Glacia→Drake→Wallace | — | — | `DEFEATED_ELITE_4_SIDNEY/PHOEBE/GLACIA/DRAKE` (1275-1278), `IS_CHAMPION` (2175), `SYS_GAME_CLEAR` (2148) |

### 2.1 HM → badge field-use gate table (the "stuck bot" prevention list)

The bot must not attempt a field HM before its badge exists; `use_field_move`
and the pathfinder already enforce this and will raise `BotModeError` if the
badge is missing (which the orchestrator must catch and re-sequence, never
crash on).

**[P2] ALL EIGHT badge gates are now code-confirmed** in `modules/menuing.py`
`use_field_move()`, the Emerald branch, lines **810-833** (one authoritative
`case` per HM). This is ground truth and settles every earlier "verify" note:

| HM | Move | Badge required to USE in field | Code-confirmed gate |
|----|------|-------------------------------|---------------------|
| HM01 | Cut | **Stone** (Gym 1, BADGE01) | ✅ `menuing.py:811` |
| HM05 | Flash | **Knuckle** (Gym 2, BADGE02) | ✅ `menuing.py:814` |
| HM06 | Rock Smash | **Dynamo** (Gym 3, BADGE03) | ✅ `menuing.py:817` + `rock_smash.py:143` |
| HM04 | Strength | **Heat** (Gym 4, BADGE04) | ✅ `menuing.py:820` |
| HM03 | Surf | **Balance** (Gym 5, BADGE05) | ✅ `menuing.py:823` + `map_path.py:687` (`can_surf`) |
| HM02 | Fly | **Feather** (Gym 6, BADGE06) | ✅ `menuing.py:826` **[P2 RESOLVED]** |
| HM08 | Dive | **Mind** (Gym 7, BADGE07) | ✅ `menuing.py:829` + `map_path.py:693` (`can_dive`) |
| HM07 | Waterfall | **Rain** (Gym 8, BADGE08) | ✅ `menuing.py:832` + `map_path.py:701` (`can_waterfall`) |

> ⚠️ **[P2] FORK BUG found — do NOT rely on `fly_to()` for the Fly gate.**
> `higher_level_actions.py:52,55` (`fly_to`) checks **`BADGE03_GET` for BOTH the
> RSE and FRLG branches**. That is correct only for FRLG (Fly = Thunder Badge 3);
> for **Emerald it is wrong** — Emerald Fly needs **BADGE06** (per the
> authoritative `use_field_move` at `menuing.py:826`). The story bot must gate
> Fly on `BADGE06_GET` itself (or fix `fly_to`), not trust `fly_to`'s check.
> Logged as a candidate upstream/fork fix; noted in §8.

### 2.2 HM criticality (hard gate vs shortcut)

Not every HM is mandatory to *finish the game*; missing a hard-gate HM =
permanently stuck. Priority for the bot to obtain + teach:

- **Surf (HARD)** — required for essentially all post-Gym-5 travel (Rt 118/119,
  Mossdeep, Sootopolis, Victory Road approach).
- **Dive (HARD)** — required to enter Seafloor Cavern and to reach Sootopolis
  underwater (Rt 126/128).
- **Waterfall (HARD)** — required to climb to Ever Grande City / Victory Road.
- **Strength (HARD)** — mandatory boulder pushes in Victory Road (and caves).
- **Rock Smash (semi)** — clears mandatory rocks in some caves/routes.
- **Cut (semi)** — a few mandatory trees; many are optional shortcuts.
- **Flash (optional-ish)** — makes Granite Cave / Victory Road navigable; the
  pathfinder can sometimes route dark caves without it, but obtaining it is cheap.
- **Fly (optional but huge)** — pure convenience/time-saver; not a gate.

### 2.3 [P2] HM & key-item HANDOFF table (WHO gives it / WHERE)

Every progression item, its giver/location, and the flag that proves receipt.
**Flag numbers verified** in `modules/data/event_flags/emerald.txt`. Locations
marked **(code-anchored)** are confirmed by a symbol/flag; **(established)** are
well-documented Emerald facts I could not fully pin to an in-repo symbol, so the
exact NPC/tile is marked *verify live*.

| Item | Giver / Location | Receipt flag | Confidence |
|------|------------------|--------------|-----------|
| **HM01 Cut** | Cutter's House, **Rustboro City** (man) | `RECEIVED_HM_CUT` (137) | established (solid) |
| **HM05 Flash** | Hiker in **Granite Cave** (Dewford) | `RECEIVED_HM_FLASH` (109) | established |
| **HM06 Rock Smash** | **[P3 FIX]** Man in the **SOUTHEAST house of Mauville City** (east of the Poké Mart) — **Pass 2 wrongly moved this to "Route 111"; it IS Mauville** (pokemondb/Thonky/PokéCoders). Given once you have 2 badges; field-use still needs Dynamo (BADGE03) | `RECEIVED_HM_ROCK_SMASH` (107) | **confirmed (external)** |
| **HM04 Strength** | **Rusturf Tunnel** (the man after the tunnel is opened) — **[P2 FIX: doc said "near Mt. Chimney" — WRONG]** | `RECEIVED_HM_STRENGTH` (106); `RUSTURF_TUNNEL_OPENED` (199) | established, corrected |
| **HM03 Surf** | House in **Petalburg City**, **after beating Norman** (Wally's father / the man) | `RECEIVED_HM_SURF` (122) | established, *verify exact house/NPC live* |
| **HM02 Fly** | **[P3 FIX] Given by the RIVAL** (May/Brendan) after the **Route 119** rival battle (north Rt 119, en route to Fortree) — not a generic NPC | `RECEIVED_HM_FLY` (110) | **confirmed (external)** |
| **HM08 Dive** | **Steven's house, Mossdeep** (after Space Center) | `RECEIVED_HM_DIVE` (123); item `ITEM_MOSSDEEP_STEVENS_HOUSE_HM08` (1133) | **code-anchored** |
| **HM07 Waterfall** | **Wallace, Sootopolis** (around the legendary-crisis resolution) | `RECEIVED_HM_WATERFALL` (312) | established, *verify exact trigger live* |
| **Devon Goods** (steal→recover→return→deliver) | **[P3 clarified]** stolen by Aqua grunt → grunt caught in **Rusturf Tunnel** (also frees Peeko) → **RETURNED** to Devon Corp Rustboro (**144**) → later **DELIVERED to Capt. Stern, Slateport** (dock-rejected **148** → **149**) | 142→143→144→148→149 chain | **code-anchored** |
| **Letter (for Steven)** | Devon president, Rustboro → deliver in Granite Cave | `DELIVERED_STEVEN_LETTER` (189) | **code-anchored** |
| **PokéNav** | Devon president, Rustboro | `RECEIVED_POKENAV` (188) | **code-anchored** |
| **Devon Scope** | **Steven, Route 120** (→ reveal Kecleon) | `RECEIVED_DEVON_SCOPE` (285) | **code-anchored** |
| **Go-Goggles** | **Lavaridge Town** (Cozmo's wife), after Mt. Chimney — needed for Rt 111 desert sandstorm | `RECEIVED_GO_GOGGLES` (221) | established, *verify NPC live* |
| **Wailmer Pail** | **Route 104** flower shop (Pretty Petal) — berries only | `RECEIVED_WAILMER_PAIL` (94) | established — **OPTIONAL** |
| **Mach/Acro Bike** | **Rydel's Cycles, Mauville** (pick one; swappable) — ⛔ ~~Mach Bike required for Sky Pillar~~ **FALSE — REFUTED 2026-08-24 against the decomp, all six floors.** The STORY ascent runs at `VAR_SKY_PILLAR_STATE` 0→1, both `< 2`, so every floor is `_CLEAN`. The bot has never owned a bike and does not need one. ⛔ **DO NOT BUILD A BIKE SOLVER FOR THE STORY** | `RECEIVED_BIKE` (90) | **code-anchored** |
| **Meteorite** | Prof. Cozmo (Meteor Falls / post-Chimney) | `RECEIVED_METEORITE` (115) | established — **OPTIONAL** |
| **Basement Key** | **Wattson**, after Gym 3 (opens New Mauville) | `GOT_BASEMENT_KEY_FROM_WATTSON` (208) | **code-anchored** — New Mauville is **OPTIONAL** |
| **Room Keys 1/2/4/6** | Aqua Hideout interior (puzzle items) | `USED_ROOM_*_KEY` (240-243) | **code-anchored** |
| **Scanner** | Abandoned Ship (Rt 108) → exchange w/ Capt. Stern | `EXCHANGED_SCANNER` (294) | established — **OPTIONAL** |
| **Rods** (Old/Good/Super) | Dewford / Route 118 / Mossdeep fishermen | 257 / 227 / 152 | established — **OPTIONAL** |
| **Coin Case** | Mauville (Game Corner area) | `RECEIVED_COIN_CASE` (258) | established — **OPTIONAL** |
| **Red/Blue Orb** | Cave of Origin / Sootopolis crisis | `RECEIVED_RED_OR_BLUE_ORB` (212) | **code-anchored** |
| **Eon Ticket** | Mystery-Gift event → Southern Island (Lati@s) | `SHOWN_EON_TICKET` (430) | **OPTIONAL / event-only** |

### 2.4 [P2] GYM-INTERIOR PUZZLE enumeration (each grounded in a real script)

Pass 1 left these "un-enumerated." Each gym's puzzle mechanic is now confirmed by
an actual symbol in `pokeemerald.sym`, so the routing/authoring cost is scoped:

| Gym | Leader | Puzzle | Grounding symbol | Authoring need |
|-----|--------|--------|------------------|----------------|
| 1 Rustboro | Roxanne | **None** — straight trainer corridor | (no puzzle script) | waypoints only |
| 2 Dewford | Brawly | **[P2 FIX: NOT "none"]** **Dark room** — beat trainers to brighten the room progressively | `DewfordTown_Gym_EventScript_BrightenRoom` (+ per-trainer `…BrightenRoom`) | order-sensitive route: must beat trainers to reveal path |
| 3 Mauville | Wattson | **Switches → raise/lower electric barriers/doors** | `MauvilleGymPressSwitch`, `MauvilleGymSetDefaultBarriers` | authored switch-press sequence |
| 4 Lavaridge | Flannery | **Warp trapdoors** (hot-sand holes) between 1F/B1F | `DoLavaridgeGym1FWarp`, `DoLavaridgeGymB1FWarp`, `StartLavaridgeGymB1FWarp` | authored warp-tile path map |
| 5 Petalburg | Norman | **Room-choice doors** — pick a challenge room per door; correct rooms open the path | `PetalburgGymSlideOpenRoomDoors`, `PetalburgGymUnlockRoomDoors` | authored door/room routing |
| 6 Fortree | Winona | **Rotating-gate puzzle** (push gates to align a path) | `RotatingGate_*` (`GetCurrentMapRotatingGatePuzzleType`, `RotatingGate_RotateInDirection`) | authored gate-push solution |
| 7 Mossdeep | Tate & Liza | **Warp-tile teleport maze** + **DOUBLE battle** | `MetatileBehavior_IsMossdeepGymWarp`, `DoMossdeepGymWarp` | authored warp path + double-battle AI |
| 8 Sootopolis | **Juan** | **Cracked-ice floor** — step pattern; ice cracks/breaks per step | `SetSootopolisGymCrackedIceMetatiles`, `SootopolisGymIcePerStepCallback` | authored no-repeat step path |

`puzzle_solver.py` covers **none** of these gym interiors — all eight need
per-map authored navigation (six are genuine puzzles; gyms 1 has none and 2 is a
"beat-trainers-to-progress" variant).

---

## 3. DEEP DETAIL — First buildable chunk: Intro → Gym 1 (Rustboro)

This is the proof-of-approach and the first thing to build. It exercises every
hard new piece (intro, naming, gender, first HM teach, first gym) at small scale.

### Chapter 0 — Intro & Identity  (NEW WORK is concentrated here)
Goal: New Game → controllable in Littleroot with the user's name+gender set.

**[P2] The intro task/script symbols DO exist in `pokeemerald.sym` — the intro
automation can key off them directly (not pixels). Real names below.**

1. **Boot to title / New Game.** From a fresh ROM, mash through copyright/title.
   `soft_reset(mash_random_keys=True)` exists (`modules/modes/util/soft_reset.py`)
   but **no New-Game menu driver** — build. **[P2] Main-menu tasks to key off:**
   `Task_MainMenuCheckSaveFile`, `Task_DisplayMainMenu`, `Task_HandleMainMenuInput`,
   `Task_HandleMainMenuAPressed` (menu-item order: NEW GAME / CONTINUE / OPTIONS,
   CONTINUE only present if a save exists — drives the fresh-vs-continue branch).
2. **Birch intro speech + the entire boy/girl/name flow is ONE task chain**
   (`Task_NewGameBirchSpeech_*`). **[P2] Ordered symbols:** `…_Init` →
   `…_ThisIsAPokemon` → `…_MainSpeech` → `…_AndYouAre` → `…_BoyOrGirl` →
   `…_WaitToShowGenderMenu` → `…_ChooseGender` → `…_WhatsYourName` →
   `…_StartNamingScreen` → (`CB2_NewGameBirchSpeech_ReturnFromNamingScreen`) →
   `…_SoItsPlayerName` → `…_CreateNameYesNo` → `…_ProcessNameYesNoMenu` →
   `…_AreYouReady` → `…_ShrinkPlayer` → `…_Cleanup`. `sBirchSpeechMainTaskId`
   (0x03000dd0) holds the active sub-task id. Advance with the existing
   `wait_until_task_is_active` / `wait_for_task_to_start_and_finish`
   (`tasks_scripts.py`).
3. **Gender select.** Cursor at `Task_NewGameBirchSpeech_ChooseGender`; the chosen
   value lives in the var **`sIntroCharacterGender`** (0x0203bcc8). **No gender
   helper exists** — build: at `…_ChooseGender`, move cursor to the user's choice,
   confirm A, then read `sIntroCharacterGender` back to verify. (Reuse the
   cursor-scroll idiom `menuing.get_scroll_direction`, `menuing.py:27`.)
4. **Name entry.** At `Task_NewGameBirchSpeech_StartNamingScreen` the naming
   keyboard (`sNamingScreen`, 0x02039f94) opens. **The typer exists**:
   `type_in_naming_screen(name, max_length)` (`keyboard.py:146`) /
   `handle_naming_screen` (`keyboard.py:226`) — wired today only to Pokémon
   nicknames. Reuse it for the player name. Then confirm the "So it's <name>?"
   yes/no at `…_CreateNameYesNo` / `…_ProcessNameYesNoMenu`. *Low-risk reuse.*
5. **Clock set.** After the truck (`WarpToTruck`), set the bedroom wall clock.
   **[P2] Symbols:** the clock script is `ScrCmd_initclock` → `StartWallClock`
   (returns via `ReturnFromStartWallClock`); state in `sClockInfo` (0x0203bcfe).
   Build: `navigate_to` the clock, press A to open `StartWallClock`, set hour/
   minute (D-pad), confirm. `modules/clock.py` only *reads* time — the intro
   *setter* is new but the script boundary (`StartWallClock`/`ReturnFrom…`) gives
   a clean wait target.
6. **Downstairs, meet Mom, TV, exit house.** Scripted movement + dialogue;
   navigate to the door, advance scripts.
7. **Meet Rival (May/Brendan) next door** (Prof. Birch's kid) — scripted.
   Completion signal: `ADVENTURE_STARTED` (flag 116) becomes true.

`is_complete()` for Ch0: `get_event_flag("ADVENTURE_STARTED")`.

### Chapter 1 — Starter & first steps
1. **Route 101 — rescue Birch.** Walk north from Littleroot onto Route 101; a
   scripted event triggers where Birch is chased by a wild Poochyena and drops his
   bag. `navigate_to(MapRSE.ROUTE101, <bag coords>)` with
   `avoid_scripted_events=False` / `expecting_script=True` so the pathfinder
   *does not route around* the trigger tile (default `avoid_scripted_events=True`
   would dodge it — `walking.py:314`, `map_path.py:924-927`).
2. **Choose starter from Birch's bag.** This is the *exact* mechanic
   `starters.py` already automates (RSE Hoenn path): it opens the bag via
   `wait_until_task_is_active("Task_HandleStarterChooseInput"/"Task_StarterChoose2",
   "A")` and presses Left/Right to pick (`modules/modes/starters.py:80-144`).
   Story mode reuses this selection logic (but keeps the mon instead of soft-
   resetting). Starter choice = story-mode config; readable back via var
   `STARTER_MON` (event_vars 35). **Team-building note:** default recommend
   **Mudkip** (Water/Ground line resists the first two gyms' problem types and
   trivializes several; see §4).
3. **Win the tutorial battle** (Poochyena) — auto-handled: BattleListener coerces
   tutorial battles to `CustomAction` but the fight itself runs; the strongest-
   move brain wins trivially.
4. **Oldale Town.** Walk north; scripted Birch/rival intro to catching; get the
   **Pokédex** (`RECEIVED_POKEDEX_FROM_BIRCH`, 2276) and **Poké Balls** from Birch
   in Littleroot lab (the "deliver to Mom's" loop). Navigate lab, advance scripts.
5. **Route 103 — beat the Rival.** Navigate onto Route 103, trigger the rival
   battle (auto-won by `handle_battle`; trainer battles are *always fought*,
   `_listeners.py`). Completion: `DEFEATED_RIVAL_ROUTE103` (130).
6. Return to Birch's lab → receive Pokédex/Running Shoes/Balls if not already;
   Mom gives Running Shoes.

`is_complete()` Ch1: `get_event_flag("DEFEATED_RIVAL_ROUTE103")` AND party size ≥ 1.

### Chapter 2 — Petalburg City (Dad + Wally)
1. Navigate Route 102 → Petalburg City (auto-battle any trainers en route,
   catch nothing required). Route 102 has trainers + tall grass (encounter
   avoidance on for travel: `avoid_encounters=True` default).
2. Enter **Petalburg Gym**, talk to **Norman (Dad)** — scripted; he won't battle
   yet. Then the **Wally catching tutorial**: Wally borrows a Zigzagoon and
   catches a Ralts; the player watches/advances a scripted sequence
   (`talk_to_npc` + script waits). No battle input needed.
3. Optional but recommended: heal at Petalburg PC
   (`heal_in_pokemon_center(PokemonCenter.PetalburgCity)`,
   `higher_level_actions.py:172`; PC door coords from `PokemonCenter` enum,
   `map_data.py:1524`).

### Chapter 3 — Route 104 / Petalburg Woods / Devon Goods + Cut
1. Route 104 (south) → **Petalburg Woods**. Auto-battle trainers/bug-catchers.
2. **[P4 FIX] Team Aqua Grunt event = a RESEARCHER RESCUE, not the Devon-Goods
   theft:** a Devon researcher is accosted; a scripted battle vs an Aqua Grunt
   triggers; on win the **grunt flees** and the researcher hands you a **Great
   Ball**. **The `DEVON_GOODS_STOLEN` (142) / `RECOVERED_DEVON_GOODS` (143) flags
   are NOT set here** — the actual theft (a grunt bolts from the Devon Corp
   building in Rustboro) and recovery (Rusturf Tunnel, which also frees Peeko)
   both happen AFTER Gym 1, in Chapter 5 (Bulbapedia Emerald Part 2).
3. Exit Woods north → Route 104 (north) → **Rustboro City**.
4. **[P4 FIX] Cutter's House is in RUSTBORO CITY** (west of the Pokémon Center,
   not on Route 104 — corrects the earlier "Route 104" claim; matches §2.3):
   talk to the man to receive **HM01 Cut** (`RECEIVED_HM_CUT`, 137). Cut's item
   can be obtained now; **field use still waits on the Stone Badge** (Gym 1).
5. **Teach Cut** to a party member with `teach_hm_or_tm(get_item_by_name("HM01"),
   party_index, move_index_to_replace)` (`modules/modes/util/items.py:160`). The
   helper validates `can_learn_tm_hm` and refuses to overwrite existing HM slots.
   Choose a bulky non-lead HM-mule or the starter (see §4 move policy).

`is_complete()` Ch3: `get_event_flag("RECEIVED_HM_CUT")` AND a party mon
`has_pokemon_with_move("Cut")` (`pokemon_party.py:76`).

### Chapter 4 — Gym 1: Roxanne (Rock) → Stone Badge
1. Navigate to **Rustboro Gym** (`MapRSE.RUSTBORO_CITY_GYM = (11,3)`,
   `map_data.py:952`). The Rustboro gym has **no puzzle** — just a straight
   corridor of trainers, then Roxanne. Route: `navigate_to` to each trainer's
   line-of-sight tile (they auto-initiate: `TrainerApproachListener`,
   `_listeners.py:288`), or walk straight to Roxanne and let approaches fire.
2. **Beat the gym trainers + Roxanne** — all auto-won by `handle_battle`. Roxanne
   uses Geodude/Geodude/Nosepass (~Lv 12-15). **Level target: ~14-16.** With
   Mudkip (Water Gun/Mud-Slug) this is trivial; with Treecko fine; with Torchic
   bring a caught Water/Grass mon (see §4).
3. Receive **Stone Badge** (`BADGE01_GET`, 2151) + TM39 Rock Tomb. Stone Badge
   also **enables Cut in the field**.
4. Heal at Rustboro PC before moving on.

`is_complete()` Ch4: `get_event_flag("BADGE01_GET")`.

### Detailed primitive-call map for Chapter 4 (illustrative)
```
preconditions: assert_party_has_damaging_move(...); party lead can battle
run():
  yield from navigate_to_anywhere(MapRSE.RUSTBORO_CITY, <gym door coords>)   # cross-region
  yield from navigate_to(MapRSE.RUSTBORO_CITY_GYM, <inside spawn>)           # warp through door
  for trainer_line_tile in gym_trainer_route:            # authored waypoints
      yield from navigate_to(gym_map, trainer_line_tile, avoid_encounters=False)
      # TrainerApproachListener + BattleListener auto-run the fight to completion
      yield from wait_for_no_script_to_run("B")
  yield from navigate_to(gym_map, <tile in front of Roxanne>)
  yield from talk_to_npc(roxanne_object_id)              # start boss battle
  # handle_battle auto-plays; on win, badge script runs
  yield from wait_until_event_flag_is_true("BADGE01_GET", "B")
  yield from heal_in_pokemon_center(PokemonCenter.RustboroCity)
```
Every symbol above exists today except the **authored `gym_trainer_route`
waypoint list** and the **`roxanne_object_id`** — i.e. the per-map data, not the
engine. That is the recurring shape of ALL story chapters: **engine ready,
per-map data authored.**

---

## 4. TEAM BUILDING & MAINTENANCE

### 4.1 Starter choice
Configurable; **default recommendation: Mudkip** (→ Marshtomp → Swampert).
Rationale: Water/Ground typing walls Roxanne (Rock), Wattson (Electric — Ground
immunity is huge), and gives Surf/Dive/Waterfall STAB later. Treecko and Torchic
are supported but flag more gym-matchup work. Starter is picked with the
existing `starters.py` selection logic (§3, Ch1).

### 4.2 What to catch and when
The bot is already a **catching machine** (`CatchStrategy`, `catch.py:23`;
opportunistic-catch scaffolding from living-dex #43). Story team plan:
- **Route 102 / 104:** catch a cheap utility mon early (e.g. a Taillow for a
  flyer, a Zigzagoon as a Pickup/HM-mule and future Fly/Cut carrier). Wurmple/
  Poochyena optional.
- **HM-mule strategy:** dedicate 1-2 low-value party members (Zigzagoon/Linoone,
  Tentacool later) to carry Cut/Rock Smash/Strength/Flash/Dive so the *combat*
  slots keep strong offensive movesets. `teach_hm_or_tm` protects HM slots from
  being overwritten (`items.py:160`).
- Keep 3-4 real battlers leveled; the rest are mules/box.

### 4.3 Leveling & healing per gym (level targets)
Suggested "party lead level ≥" gates before each gym (conservative, since the
battle AI is naive — see §5):

| Gym | Boss | Target level | Notes |
|-----|------|-------------|-------|
| 1 Roxanne | Rock | 14-16 | Water/Grass/Fighting coverage |
| 2 Brawly | Fighting | 16-19 | Flying/Psychic; avoid Normal leads |
| 3 Wattson | Electric | 20-24 | Ground immunity ideal |
| 4 Flannery | Fire | 26-29 | Water/Rock/Ground |
| 5 Norman | Normal | 30-33 | Fighting; watch Slaking Truant |
| 6 Winona | Flying | 33-36 | Electric/Rock/Ice |
| 7 Tate&Liza | Psychic (double) | 38-42 | **Double battle** — see §5 risk |
| 8 Juan | Water | 42-46 | Grass/Electric (**[P2] leader is Juan, not Wallace**) |
| E4+Champ | mixed | 50-58 | broad coverage; heal items |

**Grinding** reuses the proven loop brains: `PokecenterLoopController`
(`pokecenter_loop.py:23`) or `LevelBalancingBattleStrategy`
(`level_balancing.py:17`, keeps the low-level mon as lead but shares EXP) to
bring under-leveled members up between chapters. Route-trainer XP en route is
often enough; a dedicated grind sub-step triggers only when a level gate is unmet.

**Healing decision:** no global `needs_healing` flag exists — derive it. After
each battle, if `party.first_non_fainted is None` (`pokemon_party.py:68`) or the
lead's `current_hp_percentage` (`pokemon.py:1230`) < threshold, route to the
nearest center via `find_closest_pokemon_center` (`modes/util/map.py:86`) +
`heal_in_pokemon_center`. Between-chapter policy: **always heal + save at each
new town's PC** (cheap insurance; `save_the_game`, `higher_level_actions.py:244`).

### 4.4 Move-learning policy — reconciling with #39
- **#39 flipped the leveling-bot default** `battle.new_move` from `stop` → `cancel`
  so hunts don't get interrupted (changelog 2026-07-19; config default at
  `modules/config/schemas_v1.py:29`; decision point
  `DefaultBattleStrategy.which_move_should_be_replaced`,
  `modules/battle_strategies/default.py:25-103`).
- **Story mode wants GOOD movesets**, so it must NOT run with `cancel`. The
  cleanest fix uses the **already-existing `learn_best` branch**
  (`default.py:44-103`): it computes an "effective power" (base × attacking-stat ×
  STAB) per move, protects HM moves, and replaces the weakest / a redundant-type
  move for coverage. The docstring explicitly calls this the "future-intelligence
  seam" (`default.py:26-35`).
- **Recommendation:** the Story `BotMode` runs with `battle.new_move = "learn_best"`
  and `battle.stop_evolution = false`, either by setting these in the story
  profile's `battle.yml` or (cleaner) by supplying a **`StoryBattleStrategy`**
  subclass of `DefaultBattleStrategy` from `on_battle_started()` that (a) forces
  `learn_best` semantics regardless of config, (b) allows evolution, and (c) —
  as a later upgrade — overrides `decide_turn` for boss fights (§5).
- **Evolution:** default B-cancels every evolution (`battle_evolution_scene.py:17`;
  `should_allow_evolution` returns `... and not stop_evolution`, and
  `stop_evolution` defaults True, `schemas_v1.py:30`). Story mode must set
  `stop_evolution=false` so the starter and team evolve on schedule.

### 4.5 TMs / items / PC-box management
- **HMs/TMs** are taught with `teach_hm_or_tm` (`items.py:160`). Gym-reward TMs
  (Rock Tomb from Roxanne, etc.) can be taught to appropriate mons.
- **Bag/item queries:** `get_item_bag().quantity_of(get_item_by_name("HM01"))`
  (`items.py:427,529`); key items live in the `key_items` pocket.
- **PC/box management:** `interact_with_pc([PCAction...])`
  (`pc_interaction.py:730`) deposits/withdraws party↔box; read boxes via
  `get_pokemon_storage()` (`pokemon_storage.py:140`). Used to park HM-mules or
  swap in a type-matchup mon before a gym. `assert_boxes_or_party_can_fit_pokemon`
  (`_asserts.py:170`) guards against a full PC.

---

## 5. FEASIBILITY MAP vs current capabilities

Honest COVERED / PARTIAL / NEW per needed ability.

| Ability | Status | Evidence (file:line) |
|---|---|---|
| **Navigate within connected maps** (auto surf/waterfall/bike) | **COVERED** | `navigate_to` `walking.py:314`; waypoint actions `map_path.py:589`, exec `walking.py:209-291`; re-plans on timeout `walking.py:377-405` |
| **Navigate across regions through warps** | **PARTIAL** | `navigate_to_anywhere` `global_navigation.py:51` + `warp_graph.py:113` exist BUT not exported/wired, and **cannot open locked/HM/story-gated doors** (fails at runtime `global_navigation.py:127-132`) |
| **Auto-win wild battles** | **COVERED** | `handle_battle` `battle_handler.py:36`; `DefaultBattleStrategy` `default.py:12` |
| **Auto-win TRAINER/gym battles** | **COVERED** | trainer battles "always fought", flee blocked (`_listeners.py`; `_util.py:55` escape=0 for Trainer; `battle_action_selection.py:110`) |
| **Move-selection QUALITY for bosses** | **PARTIAL/NAIVE** | `get_strongest_move_against` `_util.py:244` is type/STAB/damage-model aware but pure max-damage: no accuracy, status, setup, PP, or switch logic; reactive switching only |
| **Send-out next / faint handling** | **COVERED** (naive pick) | `handle_fainted_pokemon` `battle_handler.py:154`; new lead = highest-HP `default.py:128` |
| **Double battles (Tate&Liza, some plot)** | **PARTIAL** | `decide_turn_in_double_battle` exists (`_interface.py`) and default fills it, but tuned less than singles — verify vs gym 7 |
| **Advance scripted dialogue / cutscenes** | **COVERED** | task/script waiters `tasks_scripts.py:11-158`; `is_waiting_for_input` `tasks.py:199` — event-driven off RAM, not OCR |
| **Yes/No + multiple-choice prompts** | **COVERED** | `wait_for_yes_no_question` `tasks_scripts.py:52`, `wait_for_multiple_choice_question` `:110` |
| **Player NAME entry (intro)** | **PARTIAL** | typer exists `keyboard.py:146,226` but wired only to nicknames — reuse for player name = small new glue |
| **GENDER selection (intro)** | **NEW** | no gender code anywhere in repo (confirmed) |
| **New-Game / title-menu driver + Birch speech + clock set** | **NEW** | no New-Game menu handler, no Birch-speech handler, no intro-clock setter |
| **Choose starter from Birch's bag** | **COVERED** | `starters.py:80-144` (RSE Hoenn selection) |
| **Talk to NPC / interact** | **COVERED** | `talk_to_npc` `higher_level_actions.py:718` |
| **Field-move EXECUTION (Cut/Strength/Flash/Rock Smash/Surf/Dig/Fly)** | **COVERED** | `use_field_move` `menuing.py:804` (badge-checked); wrappers `use_strength`/`use_rock_smash` `puzzle_solver.py:52,61`; Surf/Waterfall/Dive auto via pathfinder |
| **Field-move ROUTING to a specific story tree/boulder + detection** | **NEW (partial)** | only end-game puzzle maps are authored (`puzzle_solver.py:107`); critical-path Cut trees / Strength boulders / Rock Smash rocks on routes are **not** authored |
| **Teach HM/TM to party** | **COVERED** | `teach_hm_or_tm` `items.py:160` (validates learnability, protects HMs) |
| **Item pickup (overworld balls / hidden items)** | **NEW** | no composable `pick_up_item` helper; done ad hoc in some modes only |
| **Shopping (buy/sell)** | **COVERED** | `buy_in_shop` `higher_level_actions.py:301`, `sell_in_shop` `:399` (expects mart menu open) |
| **Healing at Pokémon Center** | **COVERED** | `heal_in_pokemon_center` `:172`; center lookup `map.py:86` |
| **When-to-heal orchestration across overworld story** | **NEW** | heal is only wired into grind loops today; a story-level heal policy must be added |
| **Catch team members** | **COVERED** | `CatchStrategy` `catch.py:23`; opportunistic-catch scaffolding (#43) |
| **Evolution management** | **COVERED (config)** | `battle_evolution_scene.py:17`; set `stop_evolution=false` |
| **Gym puzzles** | **PARTIAL** | `puzzle_solver.py` covers end-game puzzles, **not** gym interiors (e.g. Mauville switches, Petalburg rooms, Fortree gym, Mossdeep) — each needs authoring |
| **Read badges/flags/vars/items/party/map for progress** | **COVERED** | `get_event_flag` `memory.py:336`; flag table `data/event_flags/emerald.txt`; `MapRSE` `map_data.py:792`; `_asserts.py` |
| **The chapter orchestrator itself** | **NEW** | no cross-map plot driver exists; every mode is self-contained |

**Big new pieces, ranked:** (1) chapter orchestrator + per-map data authoring
(the bulk of the work — dozens of authored routes/NPC-ids/waypoints); (2) intro
automation (New Game + gender + name + clock); (3) critical-path field-move
routing (Cut trees, Strength/Rock Smash obstacles, gym-interior puzzles);
(4) wiring + hardening `navigate_to_anywhere` and teaching it to *satisfy* gates
(or letting the orchestrator sequence gate-satisfaction); (5) stronger boss AI.

---

## 6. RISKS / UNKNOWNS / OPEN QUESTIONS + Build order

### 6.1 Top risks
1. **Naive battle AI loses winnable boss fights.** Max-damage-only selection with
   no status/setup/switch handling can lose to Norman's Slaking, Tate&Liza's
   double battle, or the Elite Four. Mitigation: (a) level buffers (§4.3), (b) a
   `StoryBattleStrategy.decide_turn` upgrade for flagged boss encounters, (c) heal-
   item usage in-battle (the engine supports `UseItem` turns).
2. **`navigate_to_anywhere` can't pass gated warps** — it *fails at runtime* when a
   door is locked/HM/story-gated (`global_navigation.py:127-132`). The orchestrator
   must own gate-sequencing (do the plot event that unlocks the door *before*
   trying to path through it), and catch/retry on `BotModeError` rather than crash.
   It's also **not exported** from `modes/util/__init__.py` and **unused** today —
   needs wiring + real-world testing.
3. **Massive per-map data authoring surface** — every gym interior, every
   critical-path tree/boulder, every plot NPC id and trigger tile must be
   authored and verified per map. This is the true cost, and it's brittle (NPC
   object ids, coords). Mitigation: build incrementally, one chapter at a time,
   each independently testable from a save parked at its start.
4. **Version/symbol fragility** — modes lean on Emerald-specific task/script symbol
   names; three-way `is_rs/is_emerald/is_frlg` branches abound
   (`DOCUMENTATION/03:680-682`). v1 is Emerald-only to contain this.
5. **Scripted-event avoidance vs triggering** — the pathfinder defaults to
   *avoiding* scripted tiles (`avoid_scripted_events=True`); story mode frequently
   needs the opposite (`expecting_script=True` / `avoid_scripted_events=False`).
   Getting this wrong = the bot walks *around* the event it needs to trigger.
6. **Softlocks / unexpected dialogue** — Match Call, Pokénav, wild double battles,
   rival surprise battles. Many are covered by listeners (`PokenavListener` etc.),
   but story mode must be robust to "an unexpected script is running" (watchdog
   #E1 synergy).

### 6.2 Open questions (for the user / later passes)
- Should the bot **grind for items/money** (buy Potions/Revives, Great Balls) or
  run lean? Affects shopping sub-steps.
- **Catch quotas:** does the user want a specific team, or "whatever works"?
- **Fly usage:** obtain + use Fly for fast travel (big time saver, needs Feather
  Badge) or walk everything?
- **Post-game scope:** stop at Champion (v1) vs continue to Rayquaza-caught /
  National Dex / Battle Frontier. #45 defers this.
- **In-battle item use policy** for bosses (buy & use X-items / Full Restores?).

### 6.3 Recommended CHUNKED build order (each independently testable)
1. **Read-only progress detector + chapter registry** — ✅ **DONE 2026-07-20**
   (`modules/story/`: `chapters.py` registry of 30 chapters + `progress.py`
   `detect_progress()`; unit battery `tests/test_story_progress.py`, 12/12).
   Live-tested on the real `Nick - Emerald` save (read-only; `.sav` md5
   unchanged). **See §12 for the detection-model finding — this chunk did its
   job and reshaped the model.**
2. **Chapter 4 (Gym 1) in isolation** — start from a save parked in Rustboro;
   author the gym route + Roxanne id; prove "navigate → auto-win gym → badge
   detected → heal." This exercises the core loop with the least new work.
3. **Intro (Chapter 0)** — ✅ **DONE 2026-07-20** (built ahead of step 2, per
   user request to start with the intro). `modules/story/intro.py`
   (`run_intro(name, gender)`) drives title → New Game → Birch's speech →
   gender → name → **lands controllable INSIDE the moving truck**.
   `plugins/custom_modes/story_mode.py` = the `StoryMode` bot (fresh boot →
   intro; existing save → detect & report). Name/gender from
   `<profile>/story.yml` (`modules/story/config.py`). Verified on fresh
   throwaway profiles: boy/NICK, girl/MAY, config/ASH — all land in the truck
   with correct name+gender, deterministic (~4600 frames). **Key live facts
   learned (§13).** Still TODO for the intro: the "existing save" Continue path
   from the title screen (currently the intro path assumes a save-less boot).
4. **Chapters 2-3** — fill Petalburg/Woods/Cut, including the **first HM teach**
   (`teach_hm_or_tm`) and first field-move routing (Cut). Proves the HM pipeline.
5. **Wire + harden `navigate_to_anywhere`** — export it, add gate-aware retry,
   test cross-region routing on the real world graph.
6. **Chapters 5-10** — Dewford/Slateport/Mauville; introduces Flash, Rock Smash,
   Bike, first mid-game gym puzzles.
7. **Chapters 11-16** — Chimney/Magma, Strength, Lavaridge, Norman (Surf), Fortree
   (Fly), Devon Scope/Kecleon. The HM-gate-heavy stretch.
8. **Chapters 17-22** — Aqua arc, Dive, Mossdeep double gym, Seafloor, Sootopolis/
   Rayquaza, Wallace (Waterfall).
9. **Chapters 23-24** — Victory Road (Strength puzzles) + Elite Four + Champion.
   Boss-AI upgrade lands here if not earlier.

**Where the progressed save helps:** every chapter after 0 can be tested by
starting from a save (or savestate) parked at its beginning — the `Nick - Emerald`
profile and its many savestates (`profiles/Nick - Emerald/states/`) let a
developer jump straight to a mid-game chapter without replaying the intro. Build
a small library of "parked at chapter N" savestates as a test fixture.

---

## 7. SELF-SANITY-CHECK (re-read against known Emerald progression)

Things I am **confident** about (code-confirmed or well-established):
- The 8 gym order, cities, types, and badge flags (`DEFEATED_*_GYM` 1264-1271,
  `BADGE0N_GET` 2151-2158) — flag names verified in
  `modules/data/event_flags/emerald.txt`.
- Endgame flags `IS_CHAMPION` (2175) + `SYS_GAME_CLEAR` (2148), Elite Four flags
  (1275-1278) — verified.
- HM field-use badge gates for **Surf (Badge5), Dive (Badge7), Waterfall (Badge8),
  Rock Smash (Badge3), Cut (Stone)** — CONFIRMED IN CODE (`map_path.py:684,690,698`;
  `rock_smash.py:143`; `menuing.py:812`).
- All HM-received flags exist (`RECEIVED_HM_CUT/FLASH/FLY/STRENGTH/SURF/DIVE/
  WATERFALL/ROCK_SMASH`) — verified in the flag table.
- Key-item flags exist: `RECEIVED_WAILMER_PAIL` (94), `RECEIVED_GO_GOGGLES` (221),
  `RECEIVED_DEVON_SCOPE` (285), `RECEIVED_POKENAV` (188), `RECEIVED_BIKE` (90),
  `RECEIVED_METEORITE` (115), `RECEIVED_SS_TICKET` (291), rods (152/227/257),
  `GOT_BASEMENT_KEY_FROM_WATTSON` (208), room keys (240-243), Devon Goods chain
  (142/143/144/148/149 — 144 = Rustboro return, 149 = Slateport/Stern delivery
  **[P3]**) — verified.
- Team arc flags: `MET_ARCHIE_METEOR_FALLS` (207), `DEFEATED_EVIL_TEAM_MT_CHIMNEY`
  (139), `TEAM_AQUA_ESCAPED_IN_SUBMARINE` (112), `GROUDON_AWAKENED_MAGMA_HIDEOUT`
  (111), `KYOGRE_ESCAPED_SEAFLOOR_CAVERN` (129), `DEFEATED_MAGMA_SPACE_CENTER`
  (117), `LEGENDARIES_IN_SOOTOPOLIS` (83), `STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` (307),
  `DEFEATED_RAYQUAZA` (448), `DEFEATED_WALLY_VICTORY_ROAD` (126) — verified.

**[P2] RESOLVED in Pass 2** (was "unsure" in Pass 1 — now settled against
in-repo ground truth):
1. **All 8 HM field-use badge gates** — RESOLVED, code-confirmed (`menuing.py:
   810-833`); see §2.1. Fly = Feather (BADGE06). A `fly_to` **fork bug** was found
   (checks BADGE03 for Emerald — wrong).
2. **HM/key-item handoff locations** — filled in §2.3 with receipt flags. HM04
   **Strength corrected to Rusturf Tunnel** (was wrongly "near Mt. Chimney"). HM08
   Dive code-anchored to Steven's house (`ITEM_MOSSDEEP_STEVENS_HOUSE_HM08` 1133).
   Softer NPC/tile facts are tagged *verify live* in the §2.3 table.
3. **Norman prerequisite** — 4 badges; var `PETALBURG_GYM_STATE` (event_vars 133)
   confirmed present (semantics: gates the challenge until 4 badges). Row 13.
4. **Gym-interior puzzles** — all 8 ENUMERATED and grounded in real scripts, §2.4.
   Correction: **Brawly (Gym 2) IS a puzzle** (dark room), not "none". **Gym 8 =
   Juan**, cracked-ice floor.
5. **Missed mandatory beats** — added: **Mt. Pyre (16b)**, **Slateport Harbor sub
   theft (16c)**, **Magma Hideout / Groudon (16d)**, and made **Mr. Briney + Peeko
   rescue (5b)** explicit as the boat gate.
6. **Intro symbols** — RESOLVED: the full `Task_NewGameBirchSpeech_*` chain +
   `Task_*MainMenu*`, `sIntroCharacterGender`, `sNamingScreen`, `StartWallClock`/
   `ScrCmd_initclock`/`sClockInfo`, `WarpToTruck` all exist in `pokeemerald.sym`
   (§3 Ch0). Only the *exact cursor positions/timing* need live observation.
7. **`navigate_to_anywhere`** — re-read (`global_navigation.py:51-139`): it
   **raises `BotModeError` on any gated/locked warp** (lines 127-132) and
   **cannot route through Dive or dynamic warps** (lines 108-111). Confirmed
   unwired/ungated. See "still needs work" below.

Things that **genuinely still need LIVE discovery / testing** (cannot be settled
from in-repo data alone):
1. **Exact NPC object-ids and trigger tiles** for every *verify live* item in
   §2.3 (Surf house in Petalburg, Fly NPC on Rt 119, Rock Smash house on Rt 111,
   Go-Goggles giver in Lavaridge, Waterfall trigger in Sootopolis). Flags prove
   *receipt*; the *where-to-stand* must be read off a live/parked save.
2. **[P3 RESOLVED] The late-game chapter ORDERING** (Mt. Pyre → Slateport sub
   theft → Magma Hideout/Groudon → Aqua Hideout → Mossdeep → Tate&Liza) is now
   **CONFIRMED against an external Emerald walkthrough** (psypokes / Neoseeker /
   Bulbapedia) — §2 rows 16b→16c→16d→17→18→19 match the canonical order exactly.
   The Mt. Pyre summit yields the **Magma Emblem** that gates the Magma Hideout.
   No live check is needed for the ordering itself.
3. **Mandatory-vs-shortcut field-move obstacles** — which specific Cut tree /
   Strength boulder / Rock Smash rock / Surf/Dive/Waterfall spot is on the *only*
   path vs a shortcut. Late-game water HM sequence (Surf→Dive→Waterfall to reach
   Sootopolis/Seafloor/Ever Grande) is asserted from `can_surf/dive/waterfall`
   gating but the exact required tiles on Rt 126/128/132-134 must be confirmed live.
4. **`navigate_to_anywhere` real-world leg coverage** — export it, add gate-aware
   retry, and test **leg-by-leg**; it definitely cannot open story-gated doors or
   route Dive segments, so the orchestrator must own gate-sequencing.
5. **Double-battle AI quality** (Tate&Liza Gym 7, Steven Space-Center tag) —
   `decide_turn_in_double_battle` exists but is untuned; test on a parked save.
6. **Intro cursor/timing** — the symbols are known (§3 Ch0); the exact cursor
   deltas and frame waits for gender/name/clock must be observed on a live New Game.

**Net:** engine feasibility remains high and well-cited. Pass 2 removed the
"soft-fact" risk from HM gates, item sources, gym puzzles, intro symbols, and the
late-game beat list (all now grounded). Residual risk is concentrated in (a) the
large per-map authoring surface (NPC ids / trigger tiles / puzzle solutions), (b)
the exact late-game ordering, (c) critical-path obstacle identification, and (d)
wiring/hardening `navigate_to_anywhere`. None are blockers.

---

## 8. PASS 2 VERIFICATION — what changed / was caught

Adversarial re-audit on **2026-07-19** against the bot's own ground truth
(`event_flags/emerald.txt`, `event_vars/emerald.txt`, `symbols/pokeemerald.sym`,
`menuing.py`, `map_path.py`, `global_navigation.py`).

### 8.1 ERRORS corrected
- **Gym 8 leader = JUAN, not Wallace.** Wallace is the **Champion** (Ch24). Both
  the overview table (Ch22) and the §4.3 level table wrongly named Wallace as the
  gym leader. Confirmed by `SootopolisCity_Gym_1F_EventScript_Juan` and
  `ENABLE_JUAN_MATCH_CALL` (473) in the flag/sym data. **Fixed.**
- **HM04 Strength source was WRONG** — the doc said "NPC near Mt. Chimney"; it is
  the **Rusturf Tunnel** man (`RUSTURF_TUNNEL_OPENED` 199 context). **Fixed (§2.3).**
- **Brawly's gym (Gym 2) was implied to have no puzzle** — it is a **dark-room
  puzzle** (`DewfordTown_Gym_EventScript_BrightenRoom`). **Fixed (§2.4).**
- **Fly badge gate uncertainty** — RESOLVED to **Feather (BADGE06)**
  (`menuing.py:826`), and a **fork bug** was found: `fly_to`
  (`higher_level_actions.py:52,55`) checks BADGE03 for Emerald too (only right for
  FRLG). **Documented (§2.1).**

### 8.2 MISSED mandatory beats added
- **Mr. Briney & the Peeko rescue (Rusturf Tunnel)** — the gate that unlocks
  Briney's boat to Dewford/Slateport. Was only glancingly mentioned; now an
  explicit mandatory beat (row **5b**, `MR_BRINEY_SAILING_INTRO` 147).
- **Mt. Pyre** (row **16b**) — the orb-theft / Magma-vs-Aqua summit beat, entirely
  absent from the Pass-1 skeleton.
- **Slateport Harbor submarine theft** (row **16c**) — `EVIL_TEAM_ESCAPED_STERN_
  SPOKE` (271); distinct from the *early* Oceanic-Museum visit; was absent.
- **Magma Hideout / Groudon awakening** (row **16d**) —
  `GROUDON_AWAKENED_MAGMA_HIDEOUT` (111); listed in Pass-1's "confident flags" but
  **never given a chapter**. Now a mandatory beat.

### 8.3 RESOLVED specifics now baked in
- **All 8 HM→badge field gates** code-confirmed, single source `menuing.py:810-833`
  (§2.1).
- **HM & key-item handoff table** with receipt flags + confidence (§2.3).
- **Gym-puzzle enumeration**, each grounded in a real `pokeemerald.sym` symbol
  (§2.4).
- **Intro automation symbols** — the whole `Task_NewGameBirchSpeech_*` chain +
  main-menu tasks + gender var + naming screen + wall-clock scripts identified in
  the .sym (§3 Ch0); only cursor/timing needs live observation.
- **Norman gate** — 4 badges via `PETALBURG_GYM_STATE` (var 133) (row 13).
- **`navigate_to_anywhere`** re-confirmed to raise on gated warps and to exclude
  Dive/dynamic warps (§7 item 7).

### 8.4 Per-chapter confidence (post-Pass-2)
| Chapters | Confidence | Why |
|----------|-----------|-----|
| 0 Intro | **High** on *what* to do (symbols known); **Medium** on cursor/timing (live) |
| 1-4 (Starter → Gym 1) | **High** — flags + puzzles (none) confirmed; primary build target |
| 5-6 (Devon/Peeko/Briney/Dewford/Flash) | **High** on beats/flags; **Medium** on Briney gate ordering (verify live) |
| 7-10 (Brawly→Slateport→Mauville→Wattson) | **High** on gyms/flags; gym puzzles enumerated |
| 11-13 (Chimney/Magma→Flannery→Norman) | **High** — Strength source & Norman gate corrected/confirmed |
| 14-16 (Rt118/Weather/Winona/Kecleon) | **High** on flags; **Medium** on Fly NPC + Weather Inst. ordering |
| 16b-16d (Mt. Pyre / Slateport sub / Magma Hideout) | **Medium** — beats+flags confirmed, exact **ordering verify live** |
| 17-19 (Aqua Hideout→Mossdeep→Tate&Liza) | **High** on flags; **Medium** on double-battle AI + hideout ordering |
| 20-22 (Seafloor→Sootopolis/Rayquaza→Juan) | **High** — Juan fixed; HM water-sequence gates confirmed; **Medium** on Waterfall trigger |
| 23-24 (Victory Road → E4 → Champion Wallace) | **High** on flags; **Medium** on boss-AI survivability + VR obstacle tiles |

---

## 9. PASS 3 ACCURACY AUDIT (2026-07-20)

Independent, skeptical triple-check. Every factual claim was cross-referenced
against **(A)** the bot's own ROM ground truth (in-repo) **and (B)** an external
Emerald walkthrough. "CONFIRMED" = both sources agree. "CORRECTED" = an error
was fixed (what→what + source). "VERIFY-LIVE" = neither source can settle it;
needs an in-game/parked-save read.

### 9.1 Claim-by-claim verdicts

| Claim area | Verdict | Detail / source |
|---|---|---|
| **8 gym leaders, types, badges, order** (Roxanne/Rock/Stone → Brawly/Fighting/Knuckle → Wattson/Electric/Dynamo → Flannery/Fire/Heat → Norman/Normal/Balance → Winona/Flying/Feather → Tate&Liza/Psychic/Mind → Juan/Water/Rain) | **CONFIRMED** | pokemondb gym list + `DEFEATED_*_GYM` 1264-1271 & `BADGE0N_GET` 2151-2158 in `event_flags/emerald.txt` |
| **Gym 8 = JUAN; Wallace = Champion** (Pass-2 fix) | **CONFIRMED** | `SootopolisCity_Gym_1F_EventScript_Juan` + `EverGrandeCity_ChampionsRoom_EventScript_Wallace` in `pokeemerald.sym`; external gym list |
| **Badge→HM field-use gates** (Stone=Cut, Knuckle=Flash, Dynamo=RockSmash, Heat=Strength, Balance=Surf, Feather=Fly, Mind=Dive, Rain=Waterfall) | **CONFIRMED** | `menuing.py:810-833` (each `case`) + external gym list agree exactly; `map_path.py:687/693/701` (surf/dive/waterfall) + `rock_smash.py:143` |
| **Fly field gate = Feather/BADGE06** (Pass-2 fix) | **CONFIRMED** | `menuing.py:826` |
| **`fly_to()` fork bug** (checks BADGE03 for Emerald) | **CONFIRMED (bug real)** | `higher_level_actions.py:52,55` — both RSE & FRLG branches read `BADGE03_GET`; wrong for Emerald |
| **HM04 Strength from Rusturf Tunnel** (Pass-2 fix) | **CONFIRMED** | pokemondb ("Wanda's boyfriend after breaking rocks") + `RUSTURF_TUNNEL_OPENED` 199 |
| **Brawly Gym = dark-room puzzle** (Pass-2 fix) | **CONFIRMED** | `DewfordTown_Gym_EventScript_*BrightenRoom` symbols present |
| **All 8 gym puzzle mechanics** (§2.4) | **CONFIRMED** | every grounding symbol verified in `pokeemerald.sym` (BrightenRoom / MauvilleGymPressSwitch / DoLavaridgeGym1FWarp / PetalburgGymSlideOpenRoomDoors / RotatingGate_RotateInDirection / DoMossdeepGymWarp / SetSootopolisGymCrackedIceMetatiles) |
| **HM06 Rock Smash location** | **CORRECTED** | Pass 2 said "Route 111" → **Mauville City, SE house** (pokemondb / Thonky / PokéCoders). Pass-2 REGRESSION reverted. |
| **Fortree Gym order vs Devon Scope/Kecleon** | **CORRECTED** | Doc had Winona (Ch15) **before** Devon Scope/Kecleon (Ch16). Reality: the invisible **Kecleon blocks the Fortree Gym door**; **Devon Scope (Steven, Rt 120) is required to enter** → new row **14b** precedes Winona (Bulbapedia/Thonky/PokéBase). |
| **DELIVERED_DEVON_GOODS (149) chapter** | **CORRECTED** | Was on Ch5 (Rustboro). Reality: 149 = delivery to **Capt. Stern in Slateport** (Ch8); Rustboro return = **RETURNED_DEVON_GOODS (144)** (walkthrough + flag names 144/148/149) |
| **HM02 Fly giver** | **CORRECTED (refined)** | "generic NPC near Weather Institute" → **the RIVAL** (May/Brendan) after the Rt 119 battle (pokemondb/GameFAQs) |
| **Magma Hideout entry gate** | **CORRECTED (refined)** | Primary gate is the **Magma Emblem** from Mt. Pyre summit, not "Rock Smash/Strength inside" (psypokes/Neoseeker) |
| **Late-game order** (Mt.Pyre→Slateport sub→Magma Hideout/Groudon→Aqua Hideout→Mossdeep→Tate&Liza) | **CONFIRMED** | psypokes/Neoseeker/Bulbapedia match §2 rows 16b→16c→16d→17→18→19; upgraded from Pass-2 "verify live" |
| **Weather Institute = Team AQUA (Emerald), gives Castform** | **CONFIRMED** | external walkthrough (Emerald = Aqua; R = Magma) |
| **Norman is Gym 5, needs 4 badges** | **CONFIRMED** | external gym list (#5) + `PETALBURG_GYM_STATE` var 133 |
| HM01 Cut = Rustboro Cutter's house | **CONFIRMED** | pokemondb + `RECEIVED_HM_CUT` 137 |
| HM05 Flash = Granite Cave hiker | **CONFIRMED** | pokemondb + `RECEIVED_HM_FLASH` 109 |
| HM03 Surf = Petalburg, Wally's father, after Norman | **CONFIRMED** | pokemondb + `RECEIVED_HM_SURF` 122 |
| HM07 Waterfall = Wallace, Sootopolis, after crisis | **CONFIRMED** | pokemondb (Emerald) + `RECEIVED_HM_WATERFALL` 312 |
| HM08 Dive = Steven's house, Mossdeep | **CONFIRMED** | pokemondb + `ITEM_MOSSDEEP_STEVENS_HOUSE_HM08` 1133 |
| Devon Goods questline (Rusturf grunt frees Peeko, unlocks Briney's boat) | **CONFIRMED** | Thonky/StrategyWiki + `MR_BRINEY_SAILING_INTRO` 147, `HIDE_RUSTURF_TUNNEL_BRINEY` 879 |
| Slateport Oceanic Museum (Aqua grunts + Archie, deliver to Stern) | **CONFIRMED** | Bulbapedia + museum hide-flags 883-887 |
| All key-item / team-arc / endgame **flag numbers** cited (badges, gyms, HMs, orbs, room keys, Electrodes, E4 1275-1278, IS_CHAMPION 2175, SYS_GAME_CLEAR 2148, STARTER_MON var 35, PETALBURG_GYM_STATE var 133, etc.) | **CONFIRMED** | every number re-grepped in `event_flags/emerald.txt` / `event_vars/emerald.txt` — all exact |
| Intro/Birch-speech/clock/naming symbols (§3 Ch0) | **CONFIRMED (exist)** | previously grepped in Pass 2; symbol names valid; cursor/timing still **VERIFY-LIVE** |
| Exact NPC object-ids / trigger tiles for every *verify live* item | **VERIFY-LIVE** | flags prove receipt; where-to-stand needs a parked save (unchanged from Pass 2) |
| `RECEIVED_MAGMA_EMBLEM` flag | **VERIFY-LIVE** | no such flag in the repo table; Emblem gate is well-established externally but the exact flag/var must be read in-game |

### 9.2 Errors found & fixed in Pass 3 (summary)
1. **Rock Smash location** — Pass-2 regression "Route 111" → **Mauville City (SE house)**. (Overview row 9, §2.3.)
2. **Fortree Gym ordering** — Devon Scope + Kecleon reveal is a **prerequisite to Gym 6**; inserted row **14b** before Winona and flagged the gate. (Overview rows 14b/15/16.)
3. **DELIVERED_DEVON_GOODS (149)** — moved from Ch5 to Ch8 (Slateport/Stern); Ch5 now correctly uses **RETURNED_DEVON_GOODS (144)**. (Overview rows 5/8, §2.3.)
4. **HM02 Fly giver** — refined to **the Rival** after the Rt 119 battle. (Overview row 14, §2.3.)
5. **Magma Hideout gate** — refined to the **Magma Emblem** from Mt. Pyre. (Overview row 16d.)

### 9.3 Source-disagreements between (A) ROM and (B) walkthrough
**None of substance.** Every ROM flag/symbol and every external walkthrough fact
agreed once the doc's own three errors above were corrected. The only "gap" is
the Magma Emblem, which the external source documents but which has **no matching
flag** in the in-repo table (so it is marked VERIFY-LIVE, not a disagreement).

### 9.4 Final per-chapter accuracy verdict (post-Pass-3)
| Chapters | Verdict |
|---|---|
| 0 Intro / 1 Starter | **Accurate**; symbols exist; cursor/timing verify-live |
| 2-4 (Petalburg → Woods/Cut → Gym 1 Roxanne) | **Accurate** — no errors found |
| 5 (Devon/Peeko/Rusturf/Rival) | **Fixed** — flag 144 vs 149 corrected; beats accurate |
| 6-8 (Dewford/Flash/Gym 2 → Slateport) | **Fixed** — Slateport now carries flag 149; otherwise accurate |
| 9-10 (Mauville/Bike → Gym 3 Wattson) | **Fixed** — Rock Smash location corrected to Mauville |
| 11-13 (Chimney/Magma → Gym 4 Flannery → Gym 5 Norman) | **Accurate** — Strength source & Norman 4-badge gate hold up |
| 14 (Rt118/Weather/Fly) | **Fixed** — Fly giver = Rival |
| 14b-15 (Devon Scope/Kecleon → Gym 6 Winona) | **Fixed (reordered)** — Devon Scope now precedes Winona |
| 16-16d (Lilycove → Mt.Pyre → Slateport sub → Magma Hideout) | **Accurate + confirmed** — late-game order matches external walkthrough; Magma Emblem gate added |
| 17-19 (Aqua Hideout → Gym 7 Tate&Liza → Mossdeep/Space Center) | ‼ **CORRECTED 2026-08-12 — the previous "order confirmed" was WRONG.** The Space Center was listed BEFORE Gym 7. It cannot be: the Space Center's Team Magma and Steven are HIDDEN until Tate & Liza are beaten (`MossdeepCity_Gym/scripts.inc:73-76` clears the three `HIDE_..._SPACE_CENTER_*` flags). **MEASURED** (`probe_chapter_order.py`): on `post_aqua.ss1` (6 badges) all three HIDE flags are TRUE and `MOSSDEEP_SPACE_CENTER_STATE=0`; on `post_mossdeep_gym.ss1` (7 badges) all three are FALSE and the var is 1. Fixed in `modules/story/chapters.py`. |
| 20-22 (Seafloor/Kyogre → Sootopolis/Rayquaza → Gym 8 Juan) | **Accurate** — Juan-after-crisis order correct; Waterfall from Wallace |
| 23-24 (Victory Road → E4 Sidney/Phoebe/Glacia/Drake → Champion Wallace) | **Accurate** — roster & flags correct |

### 9.5 Overall confidence statement
After three independent passes and a two-source cross-check, the story-mode
design's **factual backbone is now high-confidence**: all 8 gyms
(leader/type/badge/order/puzzle), all 8 HM field-use gates, all HM givers, the
key-item receipt flags, the villain-arc beats, and — newly — the **late-game
chapter ordering** are confirmed by both the ROM ground truth and an external
walkthrough. Pass 3 corrected **3 substantive errors** (one of them a Pass-2
regression) plus **2 refinements**. Residual uncertainty is **not** about the
plot/facts anymore — it is confined to (a) exact NPC object-ids & trigger tiles
(VERIFY-LIVE on a parked save), (b) the Magma Emblem's exact flag/var, and (c)
engineering risks unrelated to accuracy (per-map authoring surface, boss AI,
`navigate_to_anywhere` gating). The doc is safe to build against.

**Sources (external, Pass 3):** [pokemondb gym list](https://pokemondb.net/emerald/gymleaders-elitefour) · [pokemondb HM chart](https://pokemondb.net/ruby-sapphire/hms) · [Bulbapedia Emerald walkthrough](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Emerald) · [Thonky RSE walkthrough](https://www.thonky.com/pokemon-ruby-sapphire-emerald/) · [psypokes Emerald walkthrough](https://www.psypokes.com/emerald/walkthrough.php) · [GameFAQs Emerald](https://gamefaqs.gamespot.com/gba/921905-pokemon-emerald-version) · [PokéCoders Rock Smash](https://www.pokemoncoders.com/how-to-get-rock-smash-in-pokemon-emerald/)

---

## 10. PASS 4 — INDEPENDENT RE-DERIVATION (2026-07-20)

**Method:** facts were re-derived **from scratch** — (A) directly from the bot's
in-repo ROM ground truth (`event_flags/emerald.txt`, `event_vars/emerald.txt`,
`menuing.py:810-833`, `modes/rock_smash.py:143`, `map_path.py:684-704`,
`modes/util/higher_level_actions.py:50-61`, `items.json`) and (B) two-to-three
independent external walkthroughs (Bulbapedia, Thonky, pokemondb, PokéBase,
StrategyWiki) — **without** reading the doc's own conclusions first, then diffed
against the doc. Goal: catch NEW errors AND re-check that Pass 3's own five
corrections were not themselves wrong.

### 10.1 Re-audit of Pass 3's five corrections (each independently re-derived)

| Pass-3 correction | Pass-4 verdict | Independent basis |
|---|---|---|
| HM06 Rock Smash = **Mauville City** SE house (reversing Pass-2's "Route 111") | **STILL CORRECT** | PokéCoders + Thonky Mauville page + Bulbapedia: house right/SE of the Poké Mart, needs Stone+Knuckle badges |
| **Fortree Gym gated by Devon Scope + Kecleon reveal** (row 14b before Winona) | **STILL CORRECT** | PokéBase + Thonky Fortree + StrategyWiki Rt 120: Steven gives Devon Scope after a Lv30 Kecleon battle on Rt 120; invisible Kecleon blocks the gym door until revealed |
| **`DELIVERED_DEVON_GOODS` (149) = Slateport/Capt. Stern** (not Rustboro); Rustboro = `RETURNED_DEVON_GOODS` (144) | **STILL CORRECT** | Flag table 142→143→144→148→149 chain matches Bulbapedia Part 4 / Neoseeker: Rustboro president = return (144); Stern at Slateport Oceanic Museum = deliver (149), Dock-rejected first (148) |
| **HM02 Fly given by the RIVAL** after the Rt 119 battle | **STILL CORRECT** | Bulbapedia Part 10 + StrategyWiki Rt 119: rival (Brendan/May) battle on the north Rt 119 bridge past the Weather Institute yields HM02 Fly |
| **Magma Hideout gated by the Magma Emblem** from Mt. Pyre summit | **STILL CORRECT (upgraded)** | Bulbapedia Magma Hideout + Mt. Pyre pages: summit caretaker gives the Emblem; the Jagged Pass entrance auto-appears only with it in the bag. **Upgraded**: the Emblem is a **KEY ITEM** (`items.json`), not a flag — see 10.3 |

**All five Pass-3 corrections independently reconfirmed. Pass 3 introduced no
new errors.**

### 10.2 Independently-derived facts → diff against the doc

| Independently-derived fact | Source | Verdict vs doc |
|---|---|---|
| 8 gyms: Roxanne/Rock/Stone → Brawly/Fighting/Knuckle → Wattson/Electric/Dynamo → Flannery/Fire/Heat → Norman/Normal/Balance → Winona/Flying/Feather → Tate&Liza/Psychic/Mind → Juan/Water/Rain | pokemondb + `DEFEATED_*_GYM` 1264-1271, `BADGE0N_GET` 2151-2158 | **AGREES** |
| HM field-use badge gates: Cut=B1, Flash=B2, RockSmash=B3, Strength=B4, Surf=B5, Fly=B6, Dive=B7, Waterfall=B8 | `menuing.py:811-833` (re-read every `case`) | **AGREES** |
| `can_surf`=BADGE05, `can_dive`=BADGE07, `can_waterfall`=BADGE08 | `map_path.py:687/693/701` | **AGREES** |
| Rock Smash field gate re-checked | `modes/rock_smash.py:143` = `BADGE03_GET` | **AGREES** |
| `fly_to()` fork bug: **both** RSE and FRLG branches read `BADGE03_GET` (wrong for Emerald, should be BADGE06) | `modes/util/higher_level_actions.py:52 & 55` (path is `modes/util/`, not repo root — doc's citation omits the subdir) | **AGREES** (bug real; minor citation-path nit noted) |
| Devon Goods chain 142 STOLEN / 143 RECOVERED / 144 RETURNED / 148 DOCK_REJECTED / 149 DELIVERED | `event_flags/emerald.txt:91-98` | **AGREES** |
| HM receipt flags: Cut 137, Flash 109, RockSmash 107, Strength 106, Surf 122, Fly 110, Dive 123, Waterfall 312 | `event_flags/emerald.txt` | **AGREES** |
| Key items: Bike 90, Meteorite 115, PokéNav 188, Steven Letter 189, Basement Key 208, Go-Goggles 221, Devon Scope 285, Kecleon-fled 295 | `event_flags/emerald.txt` | **AGREES** |
| Vars: STARTER_MON 35, PETALBURG_GYM_STATE 133, MT_PYRE_STATE 185 | `event_vars/emerald.txt` | **AGREES** |
| Endgame: E4 1275-1278, SYS_GAME_CLEAR 2148, IS_CHAMPION 2175 | `event_flags/emerald.txt` | **AGREES** |
| **Petalburg Woods grunt = researcher-rescue, NOT a Devon-Goods theft** (grunt flees, Great Ball reward); theft/recovery happen post-Gym-1 | Bulbapedia Part 2 | **DOC WRONG → FIXED [P4]** (overview row 3 + Ch3 step 2) |
| **HM01 Cut is in RUSTBORO CITY** (Cutter's House, W of the PC), not Route 104 | Thonky Rustboro + pokemondb | **DOC WRONG → FIXED [P4]** (Ch3 step 3 contradicted §2.3, which was right) |
| **Magma Emblem is a KEY ITEM** (`items.json` "Magma Emblem"), not a flag; no `RECEIVED_MAGMA_EMBLEM` flag exists | `items.json` + `event_flags/emerald.txt` (no match) | **NEW-RESOLUTION [P4]** (was VERIFY-LIVE; mechanism now known — gate on bag item) |
| Mt. Pyre progress var `MT_PYRE_STATE` (185) exists | `event_vars/emerald.txt:186` | **NEW-RESOLUTION [P4]** (var identified; exact completion value still live) |
| Exact NPC object-ids / trigger tiles (Surf house, Fly rival tile, Rock Smash house, Go-Goggles giver, Waterfall trigger, gym-interior waypoints) | — | **STILL-VERIFY-LIVE** (unchanged; flags prove receipt, not where-to-stand) |
| Intro cursor deltas / frame-timing (gender/name/clock) | — | **STILL-VERIFY-LIVE** (symbols known; timing needs a live New Game) |

### 10.3 NEW errors found & fixed in Pass 4

1. **Petalburg Woods Devon-Goods flag misattribution.** Overview row 3 and Ch3
   step 2 attributed `DEVON_GOODS_STOLEN` (142) / `RECOVERED_DEVON_GOODS` (143)
   to the Petalburg Woods grunt. **Reality:** the Woods grunt is a *researcher
   rescue* — the grunt flees and the researcher gives a **Great Ball**; the
   Devon Goods theft (a grunt bolts from Devon Corp in Rustboro **after Gym 1**)
   and the Rusturf-Tunnel recovery (which also frees Peeko) both belong to
   **Chapter 5**. Fixed in both places, tagged **[P4 FIX]**. *(Source: Bulbapedia
   Emerald Part 2.)*
2. **HM01 Cut location — internal contradiction.** Ch3 step 3 said Cut comes
   from a "**Route 104** (north) → Cutter's House"; §2.3 said "**Rustboro City**".
   §2.3 was right — the Cutter's House is **in Rustboro City, west of the Poké
   Center**. Fixed Ch3 to Rustboro, tagged **[P4 FIX]**. *(Source: Thonky
   Rustboro + pokemondb.)*

Both are **content-detail** errors (mislabeled event / wrong town for one HM
giver); **neither changes the chapter spine** (Cut still before Gym 1; Devon
theft/recovery still after Gym 1) nor any of the 8-gym / 8-HM / late-game facts.

### 10.4 verify-live items newly resolved

- **Magma Emblem gate** — moved VERIFY-LIVE → **RESOLVED**: it is a **key item**
  (`items.json` "Magma Emblem"), so the bot gates the Magma Hideout on
  *item-in-bag* (`get_item_bag()`), not on a nonexistent flag. Rows 16b/16d updated.
- **Mt. Pyre progress** — the var **`MT_PYRE_STATE` (185)** exists and tracks the
  arc (exact completion value still to be read on a parked save). Row 16b updated.

### 10.5 Remaining genuine live-only unknowns (unchanged, small)

Exact NPC object-ids & trigger tiles for the "verify live" givers (Surf house in
Petalburg, Fly rival tile on Rt 119, Rock Smash house in Mauville, Go-Goggles
giver in Lavaridge, Waterfall trigger in Sootopolis) and all per-map gym-interior
waypoints/puzzle solutions; the Magma Emblem/Mt-Pyre exact completion value;
intro cursor deltas & frame-timing. These are **where-to-stand / timing** facts,
not plot facts — they need a parked save, exactly as Pass 3 concluded.

### 10.6 Source disagreements

**None.** Every external walkthrough agreed with every other and with the ROM
ground truth on all audited points. The only prior "gap" — the Magma Emblem
having no flag — is now explained (it is a key item, not a flag), so it is no
longer even a gap.

### 10.7 Convergence statement

Pass 4 **did find NEW errors** — **two content-detail mistakes** that survived
Passes 1-3 (the Petalburg-Woods Devon-Goods flag misattribution and the Cut
"Route 104 vs Rustboro" contradiction), now fixed. It **also confirmed** that
**all five Pass-3 corrections were correct** (Pass 3 introduced no regressions),
resolved **two former verify-live items** (Magma Emblem = key item; `MT_PYRE_STATE`
var), and re-verified the entire factual backbone (8 gyms, 8 HM gates, HM/key-item
givers & flags, villain-arc beats, late-game order) against ROM + two external
sources with **zero disagreements**.

**Verdict:** the doc's **strategic backbone has fully converged and is
high-confidence**; the two Pass-4 fixes were localized detail corrections, not
structural. After four passes the only residual uncertainty is live-only
where-to-stand/timing data, which cannot be settled from repo + walkthroughs and
is correctly flagged as such. **Confidence: HIGH — safe to build against.**

**Sources (external, Pass 4):**
[Bulbapedia Emerald Part 2](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Emerald/Part_2) ·
[Bulbapedia Part 4](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Emerald/Part_4) ·
[Bulbapedia Part 10](https://bulbapedia.bulbagarden.net/wiki/Walkthrough:Pok%C3%A9mon_Emerald/Part_10) ·
[Bulbapedia Magma Hideout](https://bulbapedia.bulbagarden.net/wiki/Magma_Hideout_(Jagged_Pass)) ·
[Thonky Rustboro City](https://www.thonky.com/pokemon-ruby-sapphire-emerald/rustboro-city) ·
[Thonky Mauville City](https://www.thonky.com/pokemon-ruby-sapphire-emerald/mauville-city) ·
[Thonky Fortree City](https://www.thonky.com/pokemon-ruby-sapphire-emerald/fortree-city) ·
[PokéBase Kecleon/Fortree](https://pokemondb.net/pokebase/406508/how-do-i-get-past-the-invisible-kecleon-blocking-fortree-gym) ·
[StrategyWiki Route 120](https://strategywiki.org/wiki/Pok%C3%A9mon_Ruby_and_Sapphire/Route_120) ·
[PokéCoders Rock Smash](https://www.pokemoncoders.com/how-to-get-rock-smash-in-pokemon-emerald/)

---

## §12 — Detection-model finding (from building chunk 1, 2026-07-20)

Building the read-only detector and running it against the real `Nick -
Emerald` save produced a model-shaping result — exactly what a read-only
chunk-1 is for.

**The save is a hand-built test save, not a natural playthrough:** party is
shiny Celebi Lv100 + Sceptile Lv100 alongside a Lv9 shiny Bulbasaur, Lv6
Lotad, etc.; `BADGE01_GET` (Stone) is set but the Wally-tutorial and Cut-HM
flags are NOT, and a stray **Magma Emblem** key item is in the bag. Its event
flags are therefore **non-linear** — no single naive scan places it correctly.

**Two detection strategies were tried and REJECTED:**
1. *First-incomplete scan* (current = first chapter whose flag is unmet) —
   placed the save at **ch2 (Wally)** because an early flag was unset, ignoring
   the Stone Badge that proves it's past ch2. Wrong.
2. *Furthest-proof* (current = after the highest-order met milestone) — the
   stray Magma Emblem threw it to **ch16c (chapter 21/30)**. Wrong the other
   way; a single stray item dominated.

**Adopted model — the badge spine.** The 8 gym badges are earned strictly in
order and can't be skipped in normal play, so they are the reliable anchor.
Detection: take the **highest badge set** → its **bracket** (the chapters
played while holding exactly that many badges) → the first chapter in the
bracket whose finer milestone is unmet. Finer flags/items only refine *within*
the bracket and can never move placement outside it. Anything met ahead of the
badge count is reported as an **anomaly** (the test-save signature), not used
for placement. Result on the real save: **ch5 (Devon errand), 1 badge**, with
the Magma Emblem flagged as an anomaly. Correct and honest.

**Two registry data corrections this surfaced:**
- `HIDE_MT_PYRE_SUMMIT_MAXIE` is an **unreliable** completion proxy (read True
  on a save nowhere near Mt. Pyre). ch16b now uses the **Magma Emblem key item
  in bag** (the [P4] authoritative signal), matching how the bot will gate the
  Magma Hideout.
- `badges_before` per chapter is **derived** from which chapter earns each
  badge (the `badge` field), not hand-entered — one source of truth.

**Implication for later chunks:** the bot must not trust any single non-badge
flag as ground truth for "where am I"; badge level is the coarse gate and fine
flags refine. This is the same discipline the HM→badge gate table (§2.1)
already encodes.

---

## §13 — Intro (Chapter 0) live facts learned (2026-07-20)

Built by driving the intro headlessly against fresh throwaway profiles and
watching `GameState` + named tasks. Facts that will matter for later chunks:

- **Drive by tasks, not flags.** The intro sets almost no event flags. The
  named tasks are the ground truth: `Task_NewGameBirchSpeech_BoyOrGirl` (just
  before the gender menu), `Task_NewGameBirchSpeech_ChooseGender` (the menu),
  naming via `GameState.NAMING_SCREEN`.
- **Birch's speech reports as `GameState.MAIN_MENU`**, not OVERWORLD — so
  "advance the speech" means "mash A while state is not OVERWORLD."
- **Gender is position-based, NOT `sIntroCharacterGender`.** Reading that byte
  live gave the wrong result; the reliable method is: menu opens on BOY (top),
  press Down once for a girl, then A. (Confirmed: boy→male, girl→female.)
- **Naming:** `GameState.NAMING_SCREEN` flips a few frames BEFORE the keyboard
  struct pointer is populated — wait for `get_naming_screen_data() is not None`
  before calling `type_in_naming_screen()` (which raises on a null struct).
  Player names cap at **7** characters.
- **Name confirm ("is this okay?") is consumed by mashing A** (default = YES);
  a separate `wait_for_yes_no_question` HUNG (the confirm had already passed).
  Lesson: for a linear cutscene, mash A to a state target, don't wait on a
  specific transient task.
- **First controllable moment = `INSIDE OF TRUCK`** (map name), before the
  truck auto-drives to Littleroot. This is the clean, detectable end of
  Chapter 0. `ADVENTURE_STARTED` (116) is still FALSE here — it sets later
  (chunk B territory: stepping off / entering Littleroot).
- The whole intro is deterministic (~4593 frames boy / ~4627 girl) with no RNG
  dependence, so it replays reliably.

---

## §14 — Early-game (post-intro) live facts (2026-07-20, chunk B in progress)

Building forward from the truck. Iteration uses save states parked at each
sub-step (scratchpad `truck_base.ss1`, `house1f_base.ss1`) so we don't replay
the whole intro every test. `modules/story/early_game.py`.

- **Step-off sequence** (`walk_off_truck_and_into_house()`, DONE + tested):
  from INSIDE OF TRUCK, walk **east** (player starts local (2,2); exit warps are
  the x=4 column) → LITTLEROOT TOWN → `LittlerootTown_EventScript_StepOffTruck
  Male` → `...GoInsideWithMom` (Mom escorts you) → **warp into the house** →
  `PlayersHouse_1F_EventScript_MomFacePlayerMovingInMale` + her "set the clock"
  speech → control returns **inside PlayersHouse_1F at local (8,7)**.
- **`map_name` is STALE across warps** (still reads "LITTLEROOT TOWN" inside the
  house). Use the map **group/number** instead: PlayersHouse_1F = **(1, 0)**;
  Littleroot Town = (0, 9).
- **Cutscene end-detection:** require `player_avatar_is_controllable()` AND
  `not get_global_script_context().is_active` for ~15 consecutive frames. A
  single-frame check stops too early — there's a window where Mom's script is
  "active" but the avatar isn't locked yet (would stop at (3,10), wrong).
- **House 1F (1,0) warps:** stairs to 2F = **(8,2)**; the front door = (8,8)/
  (9,8). Player lands at (8,7). So B2 = walk to (8,2) → 2F → clock.
- `ADVENTURE_STARTED` (116) is still FALSE through all of this — it sets later.
- **NEXT (B2):** up the stairs (8,2) → 2F → interact with the wall clock → set
  the time. Then downstairs → Route 101 → Birch's bag → starter → first battle.

### §14.1 — Clock + downstairs findings (2026-07-20, chunk B continued)
- **Upstairs + clock** (`go_upstairs_and_set_clock()`, DONE + tested): 1F
  stairs (8,2) → 2F. Wall clock bg_event at **(5,1)** = `..._EventScript_
  WallClock` (stand (5,2) facing North). Flow: interact → mash A to
  `Task_SetClock_HandleInput` → let it fade (~40f) → **A accepts the shown
  time** → `Task_SetClock_HandleConfirmInput` (**cursor DEFAULTS TO NO**) → so
  **Up then A picks Yes** → done. Ends controllable on 2F (5,2). "Accept the
  default time" = never touch the D-pad on HandleInput, just Up+A on confirm.
- **After the clock, MOM COMES UPSTAIRS** (`PlayersHouse_2F_EventScript_
  MomComesUpstairsMale`), triggered when the player moves — talk plays in the
  bedroom, not downstairs.
- **BLOCKER for next turn — the 1F "movers" scene:** on the ground floor the
  Vigoroth movers (`PlayersHouse_1F_EventScript_Vigoroth1/2`) + a script are
  active while moving in; `navigate_to` toward the front door
  ((8,8)/(9,8) warps) **consistently times out at waypoint (8,4)** even with
  `avoid_scripted_events=False` and retries — so (8,4) is a persistent block,
  not a transient one. The downstairs→exit step must handle this (likely wait
  the movers/Mom scene out until the floor clears, or find the real walkable
  route). Player's-house 1F objects: Mom (2,6), Vigoroth (1,3)/(4,5).
- **NEXT (this chunk):** downstairs → clear the 1F Mom/movers scene → out the
  front door → rival's house → rival's mom → 2F Poké Ball → rival talk →
  outside. (Save-state checkpoints: truck/house1f/house2f/clockset in scratch.)

### §14.2 — Downstairs + rival's house (2026-07-20, chunk B milestone DONE)
The whole "moved-in → met the rival → back outside" sequence now runs. Facts:
- **The 1F "block" was the Petalburg-Gym TV scene, not the movers.** Coming
  down to 1F auto-fires `PlayersHouse_1F_EventScript_PetalburgGymReport*`,
  which *walks the player to the TV at (4,5)* and plays Mom's dialogue. RULE:
  when a script auto-moves the player, RIDE IT OUT (`_ride_out_scripted_scene`)
  — never `navigate_to` during it, or the moving avatar fights the pathfinder
  (that was the phantom "(8,4) block"). Wait for the script to ENGAGE first,
  then for control to return.
- **Player's-house front door:** navigate to the tile ABOVE the door (8,7),
  then step South through the warp (`_walk_through_warp`). A warp tile can't be
  a `navigate_to` destination for your own house, but CAN be walked onto to
  ENTER another building (see rival house below). Exit → Littleroot (0,9) ~(5,9).
- **Littleroot warps:** (5,8)→player house (1,0); **(14,8)→rival house (1,2)**;
  (7,16)→Birch's Lab (1,4).
- **Rival's (May's) house:** enter by `navigate_to((0,9),(14,8))` (walks onto
  the door → warps in). **Mom's greeting is AUTOMATIC on entry**
  (`MaysHouse_1F_EventScript_YoureNewNeighbor`) — no need to walk to her. 1F
  stairs up = (2,2). 2F: the **Poké Ball is the object at (5,4)**
  (`MaysHouse_2F_EventScript_RivalsPokeBall`); stand (5,5) facing North + A →
  `MeetMay`/`MeetMayNorth` (rival rushes in, introduces themselves). 2F
  stairs-down = (1,1). Exit: navigate to (2,7) then step South through the door.
- Both houses have ambient Vigoroth "movers" that can transiently block
  pathing; sticking to the left-side routes (x≈2) avoids them here.
- **CHUNK B COMPLETE.** NEXT CHUNK: Route 101 → Birch's bag → **choose a
  starter** → **first battle** (vs the wild Poochyena). Then the config pass
  (starter choice + nickname; name already in story.yml).

---

## §15 — Chapter 1: Route 101 → starter → first battle → Birch's lab (2026-07-20)

Verified order of operations (confirmed IN-GAME before coding) and built. A
fresh game now auto-plays all the way from the title screen to standing in
Professor Birch's lab with a starter, first battle won. `early_game.py`.

**Order of operations (verified):**
1. From outside the rival's house, walk **north**. At Littleroot (11,1) the
   `GoSaveBirch` coord-trigger fires (brief "you hear a scream" dialogue); the
   game then crosses to **Route 101 (0,16)**.
2. `Route101_EventScript_StartBirchRescue` fires and **AUTO-WALKS** the player
   up the route (to ~(11,15)) while Birch yells, then returns control.
3. Walk to **Birch's bag at (7,14)** (stand (8,14) facing West) and open it →
   `Task_HandleStarterChooseInput`.
4. Choose starter: Left=Treecko, none=Torchic, Right=Mudkip; mash A to confirm
   "Do you choose this?" → the **first battle** (starter vs the wild Pokémon).
5. Win the battle (bot's normal BattleListener; `StoryMode.on_battle_started`
   returns Fight). Birch thanks you and **warps you to his lab (1,4)**.

**Functions (each has a full INTENT / STORY CONDITION / GOAL / HOW-IT-WORKS
docstring in early_game.py):**
- `_go_north_to_birch_rescue()` — INTENT: reach Route 101 in the bag-ready
  state. GOTCHA: there is a false "free control" window at (11,19) right after
  crossing the border, BEFORE StartBirchRescue fires — do NOT stop there (you
  get boxed in). We wait until the `StartBirchRescue` script is actually on the
  stack, then ride the auto-walk out. Ends controllable at ~(11,15).
- `_choose_starter(species)` — INTENT: pick the configured starter. The bag
  cursor starts on the middle ball (Torchic); Left/Right pick the sides;
  mashing A confirms into the battle.
- `help_birch_and_choose_starter(starter)` — orchestrates 1–5. The battle is
  fought by the framework while this generator is paused; on resume it advances
  Birch's thanks with **B** (B also answers "No" to any incidental Yes/No such
  as a nickname prompt, matching the default of keeping the species name) until
  arriving in the lab. GOAL/END STATE: starter in party, wild Pokémon beaten,
  standing controllable in Birch's lab (1,4). Config: `starter` = random |
  treecko | torchic | mudkip (from `<profile>/story.yml`).

**Config added** (`modules/story/config.py`, `story.yml`): `starter` (default
random) and `starter_nickname` (default none | random | literal). Starter
selection is live; **nickname application is TODO** — verify whether/where the
game offers a starter-nickname prompt (this early sequence did not appear to),
otherwise it needs the Name Rater later. `on_battle_started` → Fight added to
StoryMode so story battles are always fought.

**Verified:** full fresh run with real battle listeners → 15,425 frames →
NICK/male, random Torchic Lv5, in Birch's lab (1,4). Random selection also
produced Mudkip and Treecko across runs. Checkpoint `birch_lab.ss1` saved.

**NEXT (remaining in the user's chunk):** finish Birch's lab conversation →
head north to **Oldale Town (0,10)** → **train the starter to a random Lv 8-10**
→ Route 103 → **rival battle**. Order still to verify in-game for the lab
dialogue (watch for a possible nickname/Pokédex prompt) and the rival trigger.

### §15.1 — Birch's lab conversation (2026-07-20)
`finish_birch_lab(nickname_mode)` — INTENT: close the give-starter scene so the
player can leave. STORY: starts in the lab (1,4) with the starter, running
`GiveStarterEvent`. HOW: Birch asks "give a nickname?" (a Std_MsgboxYesNo that
**B does NOT dismiss** — needs the Yes/No handler). Then advance the rest by
waiting for the `GiveStarterEvent` script to leave the stack while mashing **A**
(B doesn't advance these boxes; and the wait stops the instant the script ends,
BEFORE another A could re-open Birch's repeatable talk — A while facing him
re-triggers `EventScript_Birch` in a loop, the bug that first stalled this).
- **NICKNAME feature GATED OFF for now:** the Yes→naming path reaches the
  keyboard and types, but the typed name does NOT persist (post-naming confirm
  subtlety unsolved), and the user deprioritised nicknames. So we always answer
  No (keep species name). Config (`starter_nickname`) + `_resolve_nickname()` +
  a nickname pool remain for the future fix. **TODO: nickname persistence.**
- Verified from the `birch_lab` checkpoint: "none" → Torchic Lv5, controllable
  in the lab (6,5). Checkpoint `lab_done.ss1` saved.

### §15.2 — Shiny contingency for story battles (2026-07-20)
`StoryMode.on_battle_started()` always returns `BattleAction.Fight`. If the wild
in a story battle (notably the scripted first Birch battle) is shiny — very rare
— we log it and fight through WITHOUT catching or stopping. WHY this is safe:
the default "shiny → stop the bot" (and any auto-catch) lives in
`modules/encounter.handle_encounter()`, which `_listeners.py` only calls when
`on_battle_started` returns None (line 114-115). Returning Fight bypasses it; the
first battle is also an `EncounterType.Tutorial`, which the framework forces to
`CustomAction` (also never calls handle_encounter). Unit-tested: shiny/normal/
None encounters all return Fight and never raise.

### §15.3 — Oldale/Route 103: travel, training, rival battle (2026-07-20) — CHAPTER 1 COMPLETE
`travel_to_route103()` + `train_lead_to_level()` + `fight_route103_rival()`.
A fresh game now plays through the FIRST RIVAL BATTLE.
- **travel_to_route103**: map-by-map chain (lab → Littleroot via warp →
  Route 101 → Oldale → Route 103) with `avoid_encounters=False`, so wild
  encounters en route are fought (starting training). Uses `navigate_to` for
  the direct connections (works WITH listeners fighting the encounters; the
  one-shot `navigate_to_anywhere(OLDALE)` from the lab LOOPS, so the chain is
  used). Ends on a Route 103 grass tile (5,7).
- **train_lead_to_level(target)**: `spin()` on the grass triggers wilds fought
  by `LevelUpLeadBattleStrategy` (strongest move; flees only at low HP). Stop
  spinning at target level OR when HP <= hp_threshold+8; on low HP, heal at
  **Oldale's Poké Center** and loop back (`navigate_to_anywhere` for the
  cross-map return). KEY FIXES: (1) `BattleAction.Fight`/DefaultBattleStrategy
  FLED wilds (no XP) — switched to `LevelUpLeadBattleStrategy`; (2)
  `find_closest_pokemon_center()` is BROKEN (fails even from Oldale) — hard-
  target `PokemonCenter.OldaleTown` instead. StoryMode.on_battle_started now
  returns `LevelUpLeadBattleStrategy()`.
- **fight_route103_rival**: HEAL TO FULL first (the rival at (10,3) is a TRAINER
  battle — cannot be fled; a low-HP LevelUpLead would try to flee and the
  framework RAISES). Then navigate to (10,4), face North, A to talk → battle.
  At full HP with a Lv 8-10 starter the (Lv5) rival loses decisively.
- **Random target Lv 8-10** (`random.randint(8,10)`) per user spec.
- **VERIFIED (piecewise, headless): fresh→lab (18.9k frames); route103→train
  Lv8→heal→beat rival (31.1k frames, done, no crash).** Full single-run
  exceeds the headless timeout but is the sum of validated pieces.

### §16 — Chapter 2 start: return to lab, get the Pokédex (2026-07-20)
`return_to_lab_and_get_pokedex()`: after the rival, head back to Birch's lab.
On the way, the rival intercepts you in **Oldale** (`OldaleTown_EventScript_
RivalFinish`, "go see my dad") — new helper `_navigate_through_scripts()` rides
out any scene that interrupts navigation and retries until the destination is
reached. In the lab, advance with A until `RECEIVED_POKEDEX_FROM_BIRCH` is set
(Pokédex + Poké Balls given), then ride out. Verified from the post-rival
checkpoint: dex + `SYS_POKEDEX_GET` True, controllable in the lab (4.1k frames).
Checkpoint `pokedex_done.ss1`. NEXT: leave lab -> Route 102 -> Petalburg (meet
Dad/Norman + Wally catching tutorial = Chapter 2 proper).

### §16.1 — Petalburg journey (DONE + wired, 2026-07-20)
`travel_to_petalburg()` + `_navigate_leg()` (navigate_to per leg with ride-out
retry, since `navigate_to_anywhere` LOOPS on Route 101). Handles Mom's
Running-Shoes gift in Littleroot. STATUS: reaches Oldale reliably; the
**Oldale -> Route 102 leg fails** ("Stuck trying to reach (0,17)") — the target
coord (14,8)/approach is wrong OR navigate_to won't cross that connection.
NEXT SESSION: find the correct Oldale west-exit / Route 102 coords (ROUTE102 =
(0,17), PETALBURG_CITY = (0,0)); then Chapter 2 proper — enter the Petalburg Gym
to meet Dad/Norman, then the **Wally catching tutorial** (a big scripted
sequence to explore). StoryMode currently ends at the Pokédex (§16); wire the
Petalburg travel only once it reaches Petalburg cleanly. Checkpoints:
pokedex_done.ss1, rival_beaten.ss1.

### §16.1 UPDATE — travel_to_petalburg FIXED & wired
The Oldale->Route102 leg failed because per-leg `navigate_to` needs the exact
crossing coords AND the travel REQUIRES the battle listener (Route 101/102 grass
triggers wilds that must be fought or navigation stalls). WORKING approach:
`_navigate_leg` to Oldale (past the Route 101 loop), then
`navigate_to_anywhere(PETALBURG_CITY, (20,18))` from Oldale (the global nav
routes Oldale->Route102->Petalburg fine once past Route 101). Verified with
listeners: pokedex_done -> Petalburg (0,0), 22.1k frames. Wired into StoryMode
(now ends "reached Petalburg"). Checkpoint `petalburg.ss1`.

### §17 — Chapter 2 (Petalburg Gym: Dad/Norman + Wally) — findings for next build
- Petalburg **Gym door = (15,8)** -> map PETALBURG_CITY_GYM (8,1). Wally's house
  door (7,5)->(8,0); PC (20,16)->(8,4).
- The gym is TALL (Norman at (4,2), entrance ~ (4,110)). Walking up to **(4,108)**
  fires the scene: `PetalburgCity_Gym_EventScript_Norman` -> `WallyArriveNorth`
  -> `NormanAddressPlayerNorth` (Norman notices you, Wally arrives, Norman asks
  you to help Wally catch a Pokémon).
- The trigger is finicky: it fired when walking UP from the entrance with A
  presses, but NOT when navigate_to_anywhere dropped the player at (4,108) — so
  the build should ENTER the gym, then step Up tile-by-tile from the entrance
  until the Norman script engages, then ride it out.
- TODO next session: build enter-gym -> Norman/Wally scene -> the Wally catching
  tutorial (Wally catches a Ralts on Route 102 — determine if it auto-plays or
  needs navigation) -> back to the gym -> free. Then Route 104 -> Petalburg Woods
  -> Rustboro (Gym 1). Checkpoint `petalburg.ss1` to iterate from.

### §17.1 — Wally tutorial (DONE + wired)
`do_petalburg_gym_and_wally_tutorial()` (early_game.py, unwired). KNOWN GOOD:
the tutorial is ENTIRELY AUTO-SCRIPTED — enter the gym, the Norman coord-scene at
(4,108) fires (`Norman`→`WallyArrive`→`NormanAddressPlayer`→`ExitGymWithWally`→
`BeginWallyTutorial`→`WallyTutorial` auto-walks you+Wally to Route 102 for the
Ralts catch and back). So the build is: reach (4,108), then RIDE OUT until
`THANKED_FOR_PLAYING_WITH_WALLY` (135) is set.
BLOCKER: getting the Norman scene to TRIGGER reliably from the built function.
In the raw observation (`$TEMP/wally_obs.py`: navigate_to_anywhere(GYM,(4,110))
-> step Up ~40 frames to (4,108) -> ride out mashing "B if i%3 else A") it FIRED
(Norman active on the first ride-out frame) and auto-walked to (25,17)+. But the
built function (reach (4,108) via a `while != (4,108)` loop, then A/B) does NOT
fire it — 40k frames stuck at (4,108). Suspect a timing/step-completion nuance
(the coord-event vs. the exact frame the Up-mash stops / the A/B starts).
NEXT SESSION: re-run wally_obs to confirm it still fires; diff the exact
frame-level input sequence; possibly step to (4,109) then a single Up onto
(4,108) then release + ride out. Also verify petalburg.ss1 is a clean
"just arrived" state. Checkpoint: petalburg.ss1.

### §17.1 UPDATE — Wally tutorial DONE + wired (2026-07-20)
`do_petalburg_gym_and_wally_tutorial()`: enter the gym, step Up to (4,108) to
fire the Norman scene, then ride out the fully-auto tutorial (auto-walks to
Route 102 for the Ralts catch and back). COMPLETION DETECTION: NOT a flag —
`THANKED_FOR_PLAYING_WITH_WALLY` is NOT set by this tutorial (it's a later
event). Instead: advance dialogue with A/B while a script runs (and to fire the
initial scene), and STOP once back in the gym (8,1) AND controllable AFTER having
visited Route 102 (0,17) — pressing nothing when free at the end so A doesn't
re-trigger Norman's repeatable dialogue in a loop. Verified via the real
listener drive (petalburg.ss1 -> done, back in gym, ~8.4k frames).
- KEY LESSON: a simple `next(gen)+run_single_frame()` test harness gives WRONG
  results for scripted scenes (stale state cache) — story steps MUST be tested
  via the listener-driven harness (FrameInfo + get_bot_listeners), like the real
  main loop. This wasted a lot of debugging; use the listener harness always.
- DETECTOR FIX TODO: `chapters.py` uses `THANKED_FOR_PLAYING_WITH_WALLY` (135)
  as Ch2's completion flag — it's WRONG (not set by the tutorial). Find the real
  flag (none of MET_WALLY_IN_PETALBURG / WALLY_SPEECH / ENABLE_FIRST_WALLY_
  POKENAV_CALL were set either). Low priority (badge-anchored detection).
- Checkpoint `wally_done.ss1`. NEXT: Route 104 -> Petalburg Woods -> Rustboro
  (HM01 Cut, then Gym 1 Roxanne).

## §16 — Petalburg → Rustboro corridor: VERIFIED map geometry + travel plan (2026-07-20)
Read directly from the ROM (get_map_data connections/dims) — no more guessing.

**Connection graph (group/number, dims = width×height):**
- PETALBURG_CITY (0,0) 30×30: **West → Route 104** (offset -50), East → Route 102.
- ROUTE 104 (0,19) 40×80: **North → Rustboro City**, East → Petalburg (offset 50),
  South → Route 105.
- PETALBURG_WOODS (24,11) 48×44: **NO map connections** — entered only by WARPS
  (doorways) off Route 104.
- RUSTBORO_CITY (0,3) 40×60: **South → Route 104**, North → Route 115, East → Route 116.

**WHY `navigate_to_anywhere` CANNOT do Petalburg→Rustboro (root cause):**
Route 104 is one map ID but is PHYSICALLY SPLIT by the Petalburg Woods building.
The south half (the Petalburg/beach entrance, ~y50-79) and the north half (the
Rustboro connection, ~y0) are joined ONLY by walking THROUGH the Woods via warps.
The global navigator routes over the connection GRAPH (Petalburg→Route104→Rustboro
all look edge-connected) but then fails the LOCAL path across Route 104 — it errors
`Could not find a path from (…@PETALBURG) to (…@ROUTE104)` or picks an unreachable
Route104 waypoint like (10,30). A warp barrier is invisible to connection routing.
=> The trip MUST be built in LEGS with explicit warp traversal. See ML-7.

**West-exit blocker (observed):** navigating from Petalburg toward Route 104 paths
the player to the west edge (reached ~(4,13)) but then triggers a scripted event /
hits a wall right at the exit. The exact west-edge exit tile (which y crosses to
Route 104) and any NPC/script there still need pinning down. Manual walk west along
y=11 dead-ended at (4,11). Petalburg's West connection has offset -50, so its full
west edge (x=0, y=0..29) maps to Route 104's east edge at y≈50..79 (the beach).

**Leg-1 probe result (2026-07-20):** from the gym-exit tile Petalburg (15,9),
`navigate_to_anywhere(PETALBURG,(x,y))` FAILS "Could not find a path" for EVERY
west-edge tile x=0/1/2 at y=15..28 — the pathfinder won't route to the west edge
from there. Yet manually pressing Left from (15,11) walks to (4,11) before hitting
a wall, and navigating toward a far target paths the player to ~(4,13) then fires a
scripted event. So: the walkable west limit is ~x=4, the true Route-104 exit tile
is NOT any of x=0-2 at those y's, and a script triggers near (4,13). NEXT SESSION
should DUMP the Petalburg collision/passability grid (or watch it live) to find the
actual open exit tile + identify the (4,13) script — do NOT blind-guess coords (ML-7).

**STATUS (2026-07-20): Legs 1-3 IMPLEMENTED + verified.**
- **Legs 1-2** `travel_to_petalburg_woods()`: heal(Petalburg PC) → cross west to
  Route 104 (Scott ride-out) → fight the Route 104 trainer (no-flee
  `LevelUpTravelBattleStrategy`, ML-8) → enter the Woods south door (10-11,38)
  via discrete up-steps. Deterministic (6251 frames, x2). Checkpoint
  `woods_entered.ss1` (Woods (17,38)).
- **Leg 3** `cross_petalburg_woods()`: cross the Woods maze — ~3 Bug-Catcher
  trainers fought inline + the MANDATORY Devon-researcher/Aqua-grunt cutscene
  (`PetalburgWoods_EventScript_DevonResearcherRight` → grunt battle
  `EventScript_DoNoIntroTrainerBattle` → Great Ball) ridden out — then exit the
  NORTH warp (Woods 14-15,5) onto Route 104 north. Deterministic (16123 frames,
  x2). Checkpoint `route104_north.ss1` (Route 104 north (11,29)).
- Woods warps (from mapdump): south doors (16-17,38)&(36-37,38)→Route104; north
  exit (14-15,5)→Route104.
- **Leg 4** `travel_route104_north_to_rustboro()`: single navigate (Route 104
  north connects DIRECTLY to Rustboro, no warp split), no-flee strategy for route
  trainers. Deterministic (3166 frames, x2). Checkpoint `rustboro.ss1`.
- **GYM 1** `do_rustboro_gym()`: heal at Rustboro PC → enter gym → navigate up to
  (5,4) fighting the two gym Youngsters inline → step to (5,3) and face-up+A to
  challenge ROXANNE (object id=1 at gym (5,2)) → ride out battle+dialogue until
  BADGE01_GET. Deterministic (21505 frames, x2; Mudkip Lv13→Lv16, won at 21 HP).
  Checkpoint `gym1_done.ss1`. **A FRESH GAME NOW PLAYS THROUGH TO THE STONE BADGE.**
  All of legs 1-4 + Gym 1 are StoryMode-wired.
- **STARTER CAVEAT (Gym 1):** verified with **Mudkip** (Water Gun = 4x on Roxanne's
  Rock/Ground Geodudes, 2x on Nosepass — ideal). **Treecko** (Grass) resists Rock
  and is fine. **TORCHIC** (Fire) is WEAK to Rock with no super-effective move here
  — a Torchic run likely needs extra grinding and/or a caught helper (e.g. a
  Route-104 Lotad / a Ground move). `do_rustboro_gym` currently assumes a
  favourable/leveled starter; the Torchic path is an OPEN TODO (see punch list).

**HARNESS FIDELITY — CORRECTED (ML-9 supersedes the earlier note here):** test
with a harness that MATCHES `main.py`. Per frame, read ONLY
`get_game_state()` / `get_global_script_context()` / `get_tasks()` to build the
FrameInfo — do NOT read `get_player_avatar()` / `get_map_data_for_current_position()`
every frame, and CATCH `BotModeError` the way main.py does (→ set_manual_mode).
Reading extra state each frame subtly shifts battle/warp timing and HIDES
timing-sensitive bugs (it hid the Woods-door stall — the bot went to Manual mode
= "stuck" in the real run while every over-refreshed test passed). Scratchpad
`faithful.py` is the reference harness. (This reverses the earlier, wrong advice.)
Also: never hand-step onto a warp tile — `navigate_to(map, door_tile)` it.

**LEG PLAN (build + verify each via the LISTENER harness):**
1. Petalburg → Route 104 (south/beach): find the west-edge exit tile (probe y at
   x=0), cross west. Grass on Route 104 ⇒ keep the battle listener attached.
2. Route 104 south → Petalburg Woods: navigate to the Woods SOUTH-entrance warp,
   step onto it. (Enumerate Route 104 warps — `MapWarp` has `.local_coordinates`
   and `.destination_warp_id`, NOT `.destination_map`; match the warp whose dest
   is the Woods.)
3. Cross Petalburg Woods: ride out the MANDATORY Team-Aqua-grunt / Devon-researcher
   scripted scene (design §3 [P4]: grunt battles then flees, researcher gives a
   Great Ball), exit the NORTH warp back to Route 104 (north half).
4. Route 104 north → Rustboro: navigate north to Rustboro's South connection, cross.
5. Enter Rustboro City.
Checkpoints to reuse: wally_done.ss1 (in the gym at (8,1)/(4,108)). Save a
route104_south.ss1 / woods_done.ss1 / rustboro.ss1 as each leg lands.

**GYM 1 (Roxanne) reminder:** Geodude Lv12/12 + Nosepass Lv15 — starter is only
Lv 8-10 out of Chapter 1, so TRAIN before the gym; Torchic (Fire) is weak vs Rock.
Also need HM01 Cut (from the Rustboro/Route 104 cuttable tree area) before some paths.

## §Ch5b-6 — Post-Rustboro chunk (Devon Corp → PokéNav → rival → Dewford → Gym 2)
Planned/mapped 2026-07-21 (map data read statically from ROM via `get_map_data`, verified
tiles below). Built INCREMENTALLY, each sub-step hardened + harness-validated before the
next — see the Hardening Checklist. Frontier state to build from: Rusturf Tunnel,
`BADGE01_GET` + `RECOVERED_DEVON_GOODS` set, PokéNav/rival flags False.

### Rustboro Area Atlas (reconned, tiles are city-map local coords unless noted)
- **Devon Corp entrance** (city): warp (11,15)/(12,15) → DEVON_CORP_1F.
- **Devon Corp 1F** (11,0): stairs-up warp (14,1) → 2F; **StairGuard NPC (15,5)** (blocks
  until you have Devon business); greeter (5,3); city-exit warps (5,8)/(6,8).
- **Devon Corp 2F** (11,1): stairs-down (14,1)→1F, **stairs-up (2,1) → 3F**; scientists.
- **Devon Corp 3F** (11,2): stairs-down (2,1)→2F; **Mr. Stone NPC (15,5)** = returns the
  goods + gives the PokéNav + Steven's Letter (script `…3F_EventScript_MrStone`).
- **Rustboro rival**: static NPC (16,50) `RustboroCity_EventScript_Rival` (south end, on
  the way to the Route 104 south exit) = DEFEATED_RIVAL_RUSTBORO battle (after PokéNav).
- **Poké Center** entrance (16,38) → (11,5); **Mart** entrance (27,34) → (11,4);
  **Gym** entrance (27,19) → (11,3) [RUSTBORO_CITY_GYM].

### Sequence (flags to drive resume-safe segment gating)
1. Return Devon Goods → PokéNav+Letter (Mr. Stone, Devon Corp 3F). Flag: RECEIVED_POKENAV
   (RETURNED_DEVON_GOODS also flips). Guard may need talking-to; validate.
2. Rustboro rival battle (head south to (16,50)). Flag: DEFEATED_RIVAL_ROUTE104? →
   verify actual flag (DEFEATED_RIVAL_RUSTBORO candidate).
3. Route 104 SOUTH → Mr. Briney's cottage (south tip) → sail to Dewford. [recon Route 104
   south + Briney tiles when built]
4. Dewford Town: PC/Mart map; deliver Steven's Letter (Steven is in GRANITE CAVE B1F —
   recon); pick up HM Flash from a hiker (optional). Gym 2 = Brawly (Fighting).
5. **Gym 2 puzzle** (Dewford Gym): dark gym — you can see only around you; the correct
   path lights up as you beat trainers, OR use Flash. [recon the gym layout + trainer
   path when built] → beat Brawly → Knuckle Badge (BADGE02_GET). Marshtomp is neutral vs
   Fighting; Marshtomp's Water/Ground is fine; watch Machop/Makuhita.

### Hardening Checklist (apply to EVERY new segment — lessons from Rustboro)
- [ ] Segment gated by its completion FLAG **and** an area/map check for resume safety
      (like Segment 3's whole-Rustboro-area check — don't backtrack).
- [ ] All grinding via `_story_spin` (whiteout-aware); any long wait calls `_check_abort`.
- [ ] After warps/heals, `wait_until_truly_controllable` before the next navigate.
- [ ] `_lead_strongest_battler()` before any gym/major fight; training via
      `_prepare_for_fight` (readies battlers, not every catch).
- [ ] Cross-map travel via `_navigate_riding_out` / `_navigate_through_scripts` (rides
      out scripted scenes + retries) — never a bare navigate through a scene.
- [ ] Verify actual completion flags with the harness (flag diff before/after) — don't
      trust the "intended" flag name (ML-9: THANKED_FOR_PLAYING_WITH_WALLY was never set).
- [ ] Map each new area's PC/Mart/warps/NPCs statically first (get_map_data), add to this
      Atlas; verify the gym puzzle path before coding the gym.

## §CC2 — COUNTER-CATCH PHASE 2 spec: acting on the diagnosis (#24-counters, 2026-07-26)

Phase 1 (shipped) DIAGNOSES a hopeless boss plan and NAMES a reachable counter, then stops.
Phase 2 is the execution: travel → catch → train → re-attempt. This section is the build spec.

### Measured starting point (not assumed)
Probed with the real `norman_done.ss1` (party avg **L31.4**), `find_counter_candidates(["Fighting"])`
with a permissive `allow`, ranked exactly as shipped:

| # | species | map | level band | rate | gap vs team | tile |
|---|---|---|---|---|---|---|
| 1 | Makuhita | GRANITE_CAVE_1F | 6-10 | 50% | **-25** | `None` |
| 2 | Makuhita | GRANITE_CAVE_STEVENS_ROOM | 6-10 | 50% | -25 | `None` |
| 3 | Hariyama | VICTORY_ROAD_B1F | 38-42 | 35% | +7 | `None` |
| 4 | Hariyama | VICTORY_ROAD_1F | 38-40 | 25% | +6 | `None` |
| 5 | Machop | JAGGED_PASS | 20-22 | 25% | **-11** | `None` |
| 6 | Machop | FIERY_PATH | 15-16 | 15% | -16 | `None` |

Scores (`…49976` / `…34991` / `…24989`) show **encounter rate dominates and level fit is only a
decimal tiebreak**. This is what put a L6-10 Makuhita in front of a L20-22 Machop for a L31 team.

### ‼ Four blockers, in priority order — phase 2 CANNOT act until these are fixed
1. **No tiles. `tile: None` on every candidate.** The planner returns a `TRAINING_GRASS`-verified
   spin tile or nothing, and none of Granite Cave / Jagged Pass / Fiery Path has one. **Phase 2
   has nothing to path to.** This is the single blocking item, and it is field work, not code:
   two-way-sweep a spin tile per counter map FROM A REAL STORY ANCHOR (the Route 111/114 lesson —
   same-map connectivity does NOT imply the story can reach it), then promote out of
   `PENDING_GRASS`. `GRANITE_CAVE_1F (35,11)` already sits in `PENDING_GRASS` and is the cheapest
   first promotion.
2. **Rank must put level fit first.** A counter 25 levels below the team is not a counter, it is a
   second grind — the whole point of the diagnosis was that grinding does not converge. Proposed
   key: filter to `band_hi >= team_avg - LEVEL_FIT_TOLERANCE` first, THEN rank by encounter rate
   within that set; fall back to the current ordering only if the filter empties. On the measured
   data this swaps Makuhita(L6-10) → Machop(L20-22), ~14 fewer levels of grind.
3. **False reachability: VICTORY_ROAD ranks as `reachable: True`.** It is behind the Elite Four
   gate and unreachable during the story. This is the documented `KNOWN_GATES` gap
   (`#24-regionreach` (a)) showing up in the counter path. Add the E4/Badge gates before phase 2
   trusts `reachable`. Until then the `_training_unreachable` memory (2026-07-25) bounds the cost
   to one wasted trek rather than the run.
4. **Story-interior maps are proposed.** `GRANITE_CAVE_STEVENS_ROOM` is a scripted room, not a
   hunting ground. Exclude interiors/story rooms from the candidate index.

### Execution design (once the blockers are cleared)
Model it on the existing `ensure_hm_learner` flow, which already solves the same shape
(derive a hunting ground → provision balls → travel → catch a specific species → return):
* **Preconditions** — a free party slot (or a box), ≥N Poké Balls (reuse `provision_poke_balls`),
  and the target map reachable by `region_reach` AND not in `_training_unreachable`.
* **Travel** — leg-by-leg via the existing navigator; treat `UnreachableDestinationError` as
  "drop this candidate, try the next", exactly as the training picker now does.
* **Catch** — reuse the `HM_CATCH_TARGET_DEX` on-sight branch (a dex-number allowlist already
  wired into `on_battle_started`); set it to the counter's dex number for the hunt.
* **Train** — `train_team(slots=[new mon])` to the boss's band, at the counter map's own grass so
  the trip is not wasted; heal via `_training_area_heal_map`.
* **Re-attempt** — clear that boss's `_defeat_counts` / `_loss_ko_history` entry so the plateau
  detector re-evaluates from scratch rather than firing again immediately on stale history.
* **Bound it** — ONE counter hunt per boss per run. If the boss is still hopeless afterwards,
  stop with the diagnosis (today's behaviour). Never loop hunt→lose→hunt.

### Open question for the user (do not decide unilaterally)
For **Winona** (the KI-23 case) catching an Electric/Rock/Ice counter is clearly right. For
**Norman** it is less obvious: Normal has no weakness except Fighting, and a vanilla player beats
him with levels and items rather than a type answer. The bot has no items strategy
(`#24-provisions`), so "catch a Fighting type" may be the right move *for this bot* — but "buy
Super Potions and out-level him" may be cheaper than catching a L20 Machop and training it 10
levels. **Worth pricing both before building**, using the frame-cost model added 2026-07-24
(`e8d133be`, "price prep grinds in frames before committing to them").

### §CC2 UPDATE 2026-07-26 — blocker #2 CLOSED by measurement; the open question is answered

**Blocker #2 (ranking) is fixed.** Candidates are now ordered by ESTIMATED COST within a
reachability/coverage tier, not by encounter rate. Cost = frames to FIND one
(`(100/rate) × FRAMES_PER_WILD_BATTLE`, the measured 1433) + frames to TRAIN it from the top of
its band to the team's level (`estimate_frames_to_level`, the real Gen 3 growth curve). Rate is
still present — demoted to the small term it should always have been. Unpriceable candidates sort
LAST within their tier (unknown cost is not cheap), and with no team level to read the ordering
degrades to the previous rate-then-gap behaviour. Pinned by `repro_counter_plan.py` case 5.

Measured effect (real save, L31 party): **Machop/Jagged Pass 75,949 frames vs
Makuhita/Granite Cave 315,260** — the old ranking preferred the one that is **4.2× more
expensive**, purely because it is easier to bump into.

**The open question ("is catching a counter even right for Norman?") — ANSWERED, and the answer
is uncomfortable.** Priced against the measured cost of the current behaviour:

| option | frames |
|---|---|
| Machop L21 → L28 (Jagged Pass) | **98,877** |
| Machop L15 → L28 (Fiery Path) | 190,589 |
| Makuhita L8 → L28 (Granite Cave) | 363,982 |
| *doing nothing: run05 lost to Norman 21×* | *~399,000* |
| *doing nothing: run3 lost 27×* | *508,000* |

Catching a counter is clearly worth it **for the right candidate** — and clearly marginal for the
wrong one. ‼ The catch: in the live batch the ONLY Fighting counter `_counter_area_allowed`
accepted was **Makuhita / Granite Cave (364k)** — Jagged Pass and Victory Road were both filtered
UNREACHABLE. So for Norman as it stands, phase 2 would buy roughly a **9% improvement over losing**.
**Phase 2's value is gated by reachability, not by ranking.** Before building the executor, widen
what is legitimately reachable (hop budget / `KNOWN_GATES` / a verified Fiery Path tile — Fiery
Path is on the Ch10 route and IS traversable both ways, unlike Jagged Pass's one-way ledges).

**‼ Blocker #3 got MORE dangerous, not less.** Cost ranking makes end-game encounters look almost
free — Hariyama on VICTORY_ROAD is L38-42, already above the team, so its training cost is ~0 and
it ranks **#1** the moment anything marks it reachable. It was only kept out of the live answer by
the `max_hops=4` bound, which is a coincidence of distance, not an Elite Four gate. Add the real
gate to `KNOWN_GATES` before phase 2 acts on a candidate list.

### §CC2 UPDATE 2026-07-26 (later) — ‼ THE ECONOMICS VERDICT IS REVERSED: phase 2 is now clearly worth building

The earlier update concluded *"phase 2's value is gated by REACHABILITY, not ranking"* and that a
counter hunt would buy only **~9%** over doing nothing. **That conclusion is now obsolete** — it
was true of the candidate list as it stood, and the constraint producing it has been removed.

**What was actually wrong: the hop FILTER, not reachability itself.** Probed from the real
pre-Norman anchor (`saves/prenorman_fodder_grind.ss1`, Route 102, party avg L27), every
Fighting-counter map is 5-7 hops away — FIERY_PATH 7, JAGGED_PASS 7, GRANITE_CAVE_1F 5 — while
`_counter_area_allowed` used `max_hops=4`. So the filter admitted only the NEAREST map and
excluded the cheap ones. **That is the encounter-rate mistake in different clothing: a proximity
proxy overriding measured cost.** Raising it to `COUNTER_MAX_HOPS = 8` (measured: 8 admits
Fiery Path/Jagged Pass and Mt Pyre, still excludes Safari Zone at 10-11 and Pacifidlog at 10).

**The live list for Norman now, with the real predicate:**

| # | candidate | reachable | est. frames |
|---|---|---|---|
| 1 | Machop / JAGGED_PASS L20-22 | yes | **75,949** |
| 2 | Machop / FIERY_PATH L15-16 | yes | 168,616 |
| 3 | Makuhita / GRANITE_CAVE_B1F | yes | 295,198 |
| 4 | Makuhita / GRANITE_CAVE_1F | yes | 315,260 |
| 6 | Hariyama / VICTORY_ROAD | **no** (Waterfall gate) | — |

Against the measured cost of the current behaviour (399,000-508,000 frames of losing to Norman),
the top candidate is **5-6x better than doing nothing**, not 9%. **Build phase 2.**

**Blocker #1 (tiles) is also smaller than it looked.** FIERY_PATH / JAGGED_PASS / GRANITE_CAVE are
CAVES — their encounters come from the cave FLOOR, so any walkable non-warp tile is a valid spin
tile and no `MB_TALL_GRASS` sweep is needed (which is why `jaggedgrass_probe.py` finds nothing on
them). Walkable non-warp tiles counted, with the most central listed:
FIERY_PATH 269 (e.g. `(18,19)`), JAGGED_PASS 367 (`(16,22)`), GRANITE_CAVE_1F 201 (`(22,7)`),
GRANITE_CAVE_B1F 291 (`(16,12)`). Tool: `tools/story-dev/probe_counter_tiles.py` (stage 3 `--nav`
runs the two-way navigation before promoting any of them into `TRAINING_GRASS`).

**‼ Caveat on the #1 pick.** `region_reach` models connections + warps, NOT ledge directionality,
and Jagged Pass is known to have one-way ledges (it could not be re-entered from Lavaridge,
2026-07-23). So `JAGGED_PASS` at rank 1 may be a wrong YES. Two things make that acceptable now
rather than fatal: `_training_unreachable` bounds a wrong YES to ONE wasted walk, and rank 2
(FIERY_PATH, 168,616 — still 2.4-3x better than doing nothing) is on the Ch10 route and known
traversable both ways. Run the `--nav` stage before trusting rank 1.

#### §CC2 blocker #4 — `map_type` is NOT a usable filter for "is this a hunting ground" (dead end, 2026-07-26)
Tried and rejected: excluding story interiors like `GRANITE_CAVE_STEVENS_ROOM` by map header type.
Measured — **Steven's Room and Granite Cave 1F are BOTH `'Underground'`**, so the field cannot
separate them:

| map | `map_type` |
|---|---|
| GRANITE_CAVE_1F / _B1F / **STEVENS_ROOM** | `Underground` |
| FIERY_PATH, VICTORY_ROAD_1F | `Underground` |
| JAGGED_PASS, SAFARI_ZONE_NORTH, ROUTE110 | `Route` |
| PETALBURG_CITY | `City` |

Note it also lumps SAFARI_ZONE in with ordinary routes, so it would not have caught that either.
Remaining idea (unmeasured): a floor on walkable non-warp tile count — a real hunting ground needs
room to spin, and Steven's Room is tiny. ‼ If that is pursued, bracket the threshold with data on
BOTH sides first (the `CREDIBLE_ANSWER_POWER` lesson, 08-MISTAKES 2026-07-26).
**Priority is now LOW:** cost ranking demoted Steven's Room to rank 5 behind two genuinely good
candidates, so it is only reachable if everything above it fails.

#### §CC2 blocker #1 — TWO-WAY SWEEP RESULTS (2026-07-26): a tile is found, but do NOT promote it yet
`tools/story-dev/probe_counter_tiles.py --nav`, anchored at `lavaridge.ss1` (Lavaridge Town, clean
overworld, pre-Norman, avg L26 — the moment the counter plan fires):

| map | OUT (anchor → tile) | BACK | reading |
|---|---|---|---|
| **FIERY_PATH (18,19)** | **OK** | FAIL — ended inside FIERY_PATH (22,22) | **the tile is real**; the return leg is the cave problem below |
| JAGGED_PASS (16,22) | FAIL — *reached* (14,40) then "could not find a path" WITHIN the map | — | ‼ the one-way-ledge caveat CONFIRMED: rank 1 was a wrong YES |
| GRANITE_CAVE_1F / _B1F | FAIL — routed via `ROUTE106`, a sea route | — | correctly unreachable from Lavaridge without Surf |

**Hop counts are strongly ANCHOR-dependent** — from Route 102: FIERY_PATH 7, JAGGED_PASS 7,
GRANITE_CAVE_1F 5; from Lavaridge: FIERY_PATH 2, JAGGED_PASS 2, GRANITE_CAVE 10-11. At the
Lavaridge anchor the cheap counters are 2 hops and Granite Cave is excluded by
`COUNTER_MAX_HOPS = 8` — the same ordering the cost model wants, reached independently.

**‼ WHY THE TILE IS NOT PROMOTED YET.** The BACK leg failed *inside the cave*, which is the known
warp-level limitation: "the global navigator can NOT cross warp levels, so a heal that targets a
town PC from inside a cave plan-fails ('not on connected maps') — two real-HW runs dropped to
Manual on exactly that (2026-07-22)". `_exit_training_cave_if_inside()` exists for precisely this
and is **hardcoded to `GRANITE_CAVE_1F`**. Promoting FIERY_PATH (18,19) into `TRAINING_GRASS`
before generalising that helper would re-ship that stranding on a new map.

**NEXT STEP, precisely:** generalise `_exit_training_cave_if_inside` into a table of
`{cave map: exit warp tile}` covering FIERY_PATH (2 warps) alongside Granite Cave, prove the exit
with a repro from a tile deep inside, THEN promote `(MapRSE.FIERY_PATH, (18, 19), (15, 16))` into
`TRAINING_GRASS`. That single promotion unblocks phase 2's executor, since Fiery Path is rank 2 by
cost (168,616 frames, still 2.4-3× better than losing to Norman) and is the only candidate whose
OUT leg actually passes.

#### §CC2 blocker #1 — cave support BUILT and proven; the Fiery Path tile is still NOT promoted (2026-07-26)

**Done: the cave machinery is generalised and ROM-verified.** `_exit_training_cave_if_inside` and
`_goto_training_area` knew only Granite Cave, so a second in-cave ground could neither be entered
nor left — the stranding that dropped two real-HW runs to Manual (2026-07-22) would simply have
shipped again on a new map. Both are now table-driven:
* `_CAVE_EXITS = {GRANITE_CAVE_1F: (37,12), FIERY_PATH: (26,36)}`
* `_CAVE_ENTRANCES = {GRANITE_CAVE_1F: (ROUTE106,(48,16)), FIERY_PATH: (ROUTE112,(11,36))}`
* `_training_area_heal_map` gains `FIERY_PATH -> LavaridgeTown`.
`repro_cave_exit_table.py` checks every tile is a REAL warp going where the table claims, AND that
each cave's entrance and exit are the SAME physical doorway (via `destination_warp_id`) — Fiery
Path has TWO Route 112 mouths, so entering by one and leaving by the other would surface the bot on
the wrong side of the mountain. ‼ That test exists because I first typed the Route 112 door as
`(2,30)` from memory; the ROM says `(11,36)`. Coordinates are never to be guessed.

**Proven live** (`story_harness.py lavaridge.ss1 --driver fierycave`, the FAITHFUL loop with
battle listeners): leg 1 Lavaridge → Fiery Path (18,19) **PASS**; leg 2 exit the cave **PASS**
(`map=(0,27) left_cave=True`).

**‼ BLOCKED AT LEG 3, AND THIS IS WHY THE TILE MUST NOT BE PROMOTED.** The heal trip fails:
`Could not find a path from (11/37 @ ROUTE112) to (9/6 @ LAVARIDGE_TOWN)`. Characterised — the
pathfinder is **ASYMMETRIC on the identical pair**:

| leg | result |
|---|---|
| Lavaridge (9,6) → R112 door (11,36) | **OK, 60 waypoints** |
| R112 door (11,36) → Lavaridge (9,6) | **FAIL** |
| R112 exit (11,37) → R112 door (11,36) | OK (adjacent) |

Route 112's ledges make the return effectively one-way for `calculate_path`. A training ground
whose heal trip cannot complete is precisely the stranding class this work exists to prevent, so
`FIERY_PATH (18,19)` stays OUT of `TRAINING_GRASS`.

**Next step — and it reframes the problem.** A counter HUNT does not need a training loop at the
hunting ground: it needs to travel, catch, and leave (train the catch anywhere convenient). That
sidesteps the heal trip entirely, and is a better fit for `#24-counters` phase 2 than reusing
`train_team` in place. Before that, decide the exit pairing deliberately: the NORTH mouth
(`FIERY_PATH (26,4)` ↔ `ROUTE112 (22,10)`) surfaces on the Route 111 side toward Fallarbor, which
may path where the Lavaridge side does not — measure both directions before choosing.

---

## §Ch14 — Mt. Pyre → Magma Hideout — RECON (ROM-verified 2026-08-05, `probe_ch14_recon.py`)

The first chapter past Winona (Gym 6 = end of built content). Every number below is read from
the ROM's own map headers, not recalled — `probe_ch14_recon.py` re-derives all of it in seconds.

### ~~THE HEADLINE: BOTH AREAS ARE 3-4 WARPS DEEP, AND THE NAVIGATOR IS SINGLE-HOP~~
### ‼‼ CORRECTED 2026-08-05 — THAT HEADLINE WAS FALSE. §Ch14 IS **NOT** BLOCKED.

**The navigator is not single-hop, and has not been since `#24-journey` (2026-07-31).** Measured
live 2026-08-05 with `--driver cavethread`, asserting on maps VISITED, **no chain table involved
in either direction**:

```
IN   DEWFORD_TOWN -> ROUTE106 -> GRANITE_CAVE_1F -> B1F -> B2F     (3 warps deep)
OUT  GRANITE_CAVE_B1F -> GRANITE_CAVE_1F -> ROUTE106 -> DEWFORD_TOWN
```

`MT_PYRE_SUMMIT` is the SAME 3-warp shape, so the capability the chapter was waiting on already
exists. `_CAVE_EXITS`/`_CAVE_ENTRANCES` are single-hop, but they are a redundant *pre-step*, not
the mechanism — `_navigate_riding_out` wraps the multi-hop `navigate_to_anywhere`.

**How this doc came to say the opposite:** it inherited the justifying comment on `_CAVE_EXITS`,
written 2026-07-26, which `#24-journey` invalidated five days later. Nobody re-read the comment
after the fix. (`08-MISTAKES.md` 2026-08-05: *a comment that justifies a workaround by naming a
limitation is a claim with an expiry date*.)

‼ **THE ONE REAL CONSTRAINT TO CARRY INTO THE BUILD — never route to a WARP TILE.** Walking onto
a door/ladder/stairs FIRES it, so navigation finishes one map PAST the target **and reports
success**. This bit both cavethread probe runs. It matters here immediately: **MT_PYRE_1F's
doorways are PAIRED two-tile warps** ((17,18)+(18,18) and (3,6)+(4,6)), so all four of those are
warp tiles. Approach tiles must be plain walkable ones ADJACENT to the doorway, not the doorway.

### Mt. Pyre — 8 maps, TWO branches from 1F
```
ROUTE122 <--(17,18)/(18,18)-- MT_PYRE_1F --(3,6)/(4,6)--> MT_PYRE_EXTERIOR --(19,10)/(20,10)--> MT_PYRE_SUMMIT
                                   |
                                   +--(11,1)/(20,9)--> 2F -> 3F -> 4F -> 5F -> 6F   [interior tower, DEAD END at 6F]
```
* **The story path is the EXTERIOR branch**, not the tower: `ROUTE122 → 1F → EXTERIOR → SUMMIT`.
* **SUMMIT is 3 warps from the nearest outdoor route.** Exit chain: SUMMIT → EXTERIOR → 1F →
  ROUTE122.
* The interior tower (2F-6F) is a **side dungeon** — 6F's only warps go back to 5F. It is not
  on the critical path; do not route through it.
* Sizes: 1F 22×19, 2F-6F 13×13, EXTERIOR 38×51, SUMMIT (probe it when needed).
* ‼ 1F has **paired warps** — (17,18)+(18,18) both → ROUTE122, and (3,6)+(4,6) both →
  EXTERIOR. Two-tile doorways; either tile fires. Do not assume a single exit tile.

### Magma Hideout — 8 maps, ONE outdoor exit, THREE routes to the goal
```
JAGGED_PASS <--(10,34)-- MAGMA_HIDEOUT_1F --(25,34)--> 2F_1R --(17,33)--> 3F_1R --(7,21)--> 4F
                              |                            |                  |
                              |                            +--(21,9)--> 3F_2R [DEAD END]
                              +--(31,3)--> 2F_2R (loops back to 1F and 2F_1R)
                              +--(20,22)--> 2F_3R --(16,13)--> 3F_3R --(16,21)--> 4F
```
* **`JAGGED_PASS (10,34)` is the ONLY outdoor exit** — every other warp is interior-to-interior.
* **4F (the objective) is 4 warps deep**, via either `2F_1R→3F_1R` or `2F_3R→3F_3R`.
* `3F_2R` is a dead-end side room off `3F_1R` (single warp back).
* ‼ **JAGGED_PASS is in `NO_RETURN_GROUNDS`** ("one-way ledges from Mt. Chimney; not
  re-enterable from Lavaridge", two-way sweep 2026-07-23). So the hideout's only door sits on
  a map the bot is already recorded as unable to re-enter from one side. **Probe the approach
  before designing the route** — this is the single riskiest fact in the chapter.

### BUILD ORDER (do not reorder)
1. **Chain-aware cave threading** — the blocking capability. Also unparks Granite Cave B1F/B2F.
2. **Mt. Pyre** — simpler (3 hops, one branch to follow, the tower is skippable).
3. **Magma Hideout** — 4 hops, and gated behind the JAGGED_PASS approach question.

### STILL UNVERIFIED — do NOT build on these until probed
* SUMMIT's internal layout and the orb/Magma scene trigger tiles.
* The flags/vars that gate each scene (`audit_flag_names.py` + decomp; a phantom flag name has
  burned this project twice — see `ai-research-notes/00-READ-THIS-FIRST.md`).
* Whether JAGGED_PASS is reachable at all from the post-Winona position.
* Encounter tables / level bands for both areas (for the training and counter pickers).

### §Ch14 — THE MAGMA HIDEOUT APPROACH IS SETTLED (ROM + existing measurement, 2026-08-05)

> ‼‼ **CORRECTED 2026-08-10 — THE LEDGE EXPLANATION BELOW IS WRONG.** The door is not blocked by
> one-way ledges. A **Team Magma guard stands on (16,19)**, the door column's only entry
> (`OBJ_EVENT_GFX_MAGMA_MEMBER_M`, flag **847 `HIDE_JAGGED_PASS_MAGMA_GUARD`**, decomp
> `JaggedPass/map.json`). With the guard gone the door is **2 waypoints** from `(16,20)`, a tile
> the bot already reaches. Measured: `jagged_descent.ss1` (badges 1-3, guard present) → FAIL;
> `post_mtpyre.ss1` (guard hidden) → **OK, 2 waypoints**. The 2026-07-26 probe that "could not
> path to (16,22)" was run pre-Emblem and was blocked by the guard, not the terrain.
> **The verdict "approach from above" still holds** (the pass IS ledge-descended), but the door
> itself was never the obstacle. Full build spec: **§Ch15** below.


**The hideout cannot be entered from the Route 112 side.** Probed warps:

```
JAGGED_PASS (30x46)
  (14,40)/(15,40) -> ROUTE112      <- BOTTOM of the pass
  (13,5)/(14,5)   -> MT_CHIMNEY    <- TOP of the pass
  (16,18)         -> MAGMA_HIDEOUT_1F
```

The hideout door sits at **y=18**, between the two ends. Jagged Pass descends by **one-way
ledges**, so from the ROUTE112 entrance at y=40 the door is *above* the player and unreachable.

‼ **This is not inference alone — it was already measured.** `NO_RETURN_GROUNDS`' own entry
records a 2026-07-26 probe that *"reached JAGGED_PASS (14,40) and then could not path WITHIN
the map to (16,22)"* — four tiles from the hideout door. The ROM topology explains a failure
the project had already observed and filed under a different heading.

**⇒ THE ONLY APPROACH IS FROM ABOVE:**
```
ROUTE112 (28,27)/(29,27) -> ROUTE112_CABLE_CAR_STATION -> [CABLE CAR] ->
MT_CHIMNEY_CABLE_CAR_STATION -> MT_CHIMNEY (20,41)/(21,41) -> JAGGED_PASS ->
descend to (16,18) -> MAGMA_HIDEOUT_1F -> ... -> 4F
```

**That makes the Magma Hideout objective ~8 warps deep AND behind a cable-car ride**, which is
a scripted scene, not a warp. Revised difficulty: this is the hardest area the story bot has
ever been asked to traverse — deeper than Granite Cave B2F (parked) and Mt. Pyre (3 hops).

### ‼ BUILD ORDER — REVISED AGAIN 2026-08-05 (step 1 is DONE, and was never needed)
1. ~~**Chain-aware cave threading**~~ — **CLOSED. The capability already existed** (see the
   corrected headline above). Granite Cave B1F/B2F unpark as a side effect.
2. **Mt. Pyre — NOW THE TOP ITEM.** 3 hops, one branch, no scripted transport.
3. **Magma Hideout — STILL DEFERRED.** Unchanged: it needs cable-car handling *plus* descending
   a one-way pass, ~8 warps deep. Do not attempt until Mt. Pyre ships.

‼ Do NOT "fix" `NO_RETURN_GROUNDS`' JAGGED_PASS entry by deleting it. It is correct: the pass
genuinely cannot be climbed. What was missing is that the map has a SECOND entrance from the
top, which makes the hideout reachable by a different route rather than making the entry wrong.

## §Ch14a — MT. PYRE: COMPLETE BUILD SPEC (ROM + decomp verified 2026-08-05)

Every fact below is read from the ROM (`mapfacts.py`) or the pret decomp
(`gh api repos/pret/pokeemerald/contents/data/maps/MtPyre_Summit/…`). Nothing is recalled.
**This supersedes the "STILL UNVERIFIED" list in the §Ch14 recon for the summit.**

### ‼ THE HEADLINE: THE WHOLE CHAPTER IS ONE COORD TRIGGER. NO NPC INTERACTION AT ALL.

`MtPyre_Summit_EventScript_TeamAquaExits` does everything the moment the player steps on a
trigger tile — Archie leaves, the Old Lady walks over unprompted, and the Emblem is handed over:
```
removeobject ARCHIE + GRUNT_1..4
setflag FLAG_HIDE_MT_PYRE_SUMMIT_ARCHIE      (916)
setflag FLAG_HIDE_MT_PYRE_SUMMIT_TEAM_AQUA   (917)
setvar  VAR_MT_PYRE_STATE, 1                 (185)
msgbox  …BothOrbsTakenMagmaLeftThis
giveitem ITEM_MAGMA_EMBLEM
setflag FLAG_RECEIVED_RED_OR_BLUE_ORB
setflag FLAG_HIDE_JAGGED_PASS_MAGMA_GUARD    ← THIS is what opens the Magma Hideout
```
So the bot never talks to the caretakers. **Walk to the tile, ride out the scene, done.**

### THE TRIGGER TILES (`MtPyre_Summit/map.json` coord_events)
| tile | var gate | script |
|---|---|---|
| **(22,7) (23,7) (24,7)** | `VAR_MT_PYRE_STATE == 0` | `…TeamAquaTrigger0/1/2` ← **THE ONE WE WANT** |
| (22,9) (23,9) (24,9) | `VAR_MT_PYRE_STATE == 2` | `…ArchieMaxieTrigger0/1/2` — a LATER visit, not ours |

‼ Both trigger rows sit in the same corridor. The y=9 row is **inert at state 0**, so walking
up the corridor cannot fire the wrong one — but do NOT use state-2 tiles as a waypoint.

### THE ROUTE — 3 warps, all ROM-verified, and a straight corridor at the end
```
ROUTE122 (22,29) --> MT_PYRE_1F (17,18)
MT_PYRE_1F (3,6)|(4,6) --> MT_PYRE_EXTERIOR (10,42)
MT_PYRE_EXTERIOR (19,10)|(20,10) --> MT_PYRE_SUMMIT (23,31)
MT_PYRE_SUMMIT: walk (23,31) --> (23,7)      [clean vertical corridor at x=23, y=31..7]
```
Return: SUMMIT (22,31)|(23,31)|(24,31) → EXTERIOR (19,10) → 1F (3,6) → ROUTE122 (22,29).

‼ **PAIRED / TRIPLED DOORWAYS — every one of those is a WARP TILE.** 1F↔R122 is (17,18)+(18,18);
1F↔EXTERIOR is (3,6)+(4,6); EXTERIOR↔SUMMIT is (19,10)+(20,10); SUMMIT↔EXTERIOR is
(22,31)+(23,31)+(24,31). **Never pass one as a navigation destination** — walking onto a warp
FIRES it, so the trip ends one map past the target and reports success (`08-MISTAKES.md`
2026-08-05). The target `(23,7)` is a plain walkable tile, which is exactly why it is the target.

### ‼ THE LIKELY IMPLEMENTATION IS ONE CALL — VALIDATE THIS FIRST BEFORE WRITING A CHAPTER
Multi-hop warp threading was proven working 2026-08-05 (Dewford ⇄ Granite Cave B2F, 3 warps).
MT_PYRE_SUMMIT is the same depth, and the destination is a plain tile, so the entire traversal
may reduce to:
```python
yield from _navigate_riding_out(MapRSE.MT_PYRE_SUMMIT, (23, 7))
```
**Measure that before building any warp chain by hand.** If it works, the chapter is: travel →
that call → ride out the scene → guard on completion.

### THE GRAPH ALREADY KNOWS THE WHOLE JOURNEY FROM WHERE THE STORY ENDS
Offline BFS over the ROM warp-graph cache (`probe_cavethread_static.py` style), 2026-08-05:
```
FORTREE_CITY  -> ROUTE120 -> ROUTE121 -> ROUTE122 -> MT_PYRE_1F -> MT_PYRE_EXTERIOR -> MT_PYRE_SUMMIT
LILYCOVE_CITY -> ROUTE121 -> ROUTE122 -> MT_PYRE_1F -> MT_PYRE_EXTERIOR -> MT_PYRE_SUMMIT
```
Fortree is exactly where the built content stops, so the journey is **6 hops from the current
end state**. ‼ Route KNOWN is not route WALKABLE — `ROUTE121 -> ROUTE122` is a water crossing
and these are connection edges, which can be phantoms (the Verdanturf case). **SURF is the
gate.** Treat this as evidence the single-call approach is worth measuring FIRST, not as proof.

### COMPLETION TEST — use the VAR, not the HIDE flag
`VAR_MT_PYRE_STATE (185) == 1`, and/or `ITEM_MAGMA_EMBLEM` in the bag.
‼ **Do NOT use `FLAG_HIDE_MT_PYRE_SUMMIT_MAXIE` (856) as the completion proxy** — this doc
already records it reading True on a save nowhere near Mt. Pyre (§10.3), and the decomp confirms
why: 856 hides an object that is only *positioned* at `MT_PYRE_STATE == 2`, a different visit.

### SUMMIT MAP (50x37) — objects, from the ROM
| obj | tile | script | hide flag |
|---|---|---|---|
| 1 | (22,5) | `MtPyre_Summit_EventScript_OldMan` | — |
| 3 | (23,5) | `MtPyre_Summit_EventScript_OldLady` | — |
| 2 | (23,6) | (none) | **916** Archie |
| 8 | (23,6) | (none) | **856** Maxie |
| 4,6,5,7 | (21,15) (21,11) (25,18) (25,11) | Grunt1-4 | **917** Team Aqua |

The four grunts stand IN the corridor between the entrance and the trigger. They are
`removeobject`d by the scene, but they are present on the way UP — **expect trainer sight-lines
and treat this as a fight-through leg**, not a clean walk.

### FREEBIES ON THE MAP (bg_events) — not required, listed so they are not "discovered" later
`ITEM_RARE_CANDY` hidden at **(37,7)**; `ITEM_ZINC` hidden at **(9,25)**.

### STILL OPEN (must be probed live — needs a post-Winona save)
* **Reaching ROUTE122 at all.** It is across water — **SURF is required**, which is the same gate
  that `#24-partycap` broke. Route 121 → 122 pathing is unmeasured.
* Whether the 4 grunts' sight-lines derail the ascent.
* The scene's ride-out length (it has `fadescreen`, `msgbox`, `giveitem` and an NPC walk).

## §Ch14-PRE — ROUTE 121: THE TEAM AQUA GATE (decomp + live verified 2026-08-05)

**‼ THIS IS THE FIRST STEP OF THE MT. PYRE CHAPTER, AND WITHOUT IT NOTHING ELSE IS REACHABLE.**

Route 121 (80x20) has a north band and a south band joined by ONE corridor at **x=30-31**.
Three Team Aqua grunts stand in its mouth:

| object | tile | graphics | script | flag |
|---|---|---|---|---|
| grunt 1 | (30,7) | `OBJ_EVENT_GFX_AQUA_MEMBER_M` | `0x0` | `FLAG_HIDE_ROUTE_121_TEAM_AQUA_GRUNTS` |
| grunt 2 | (31,7) | same | `0x0` | same |
| grunt 3 | (30,8) | same | `0x0` | same |

Flag **914** (`event_flags/emerald.txt:764`). Measured LIVE on a post-Winona save:
**`HIDE_ROUTE_121_TEAM_AQUA_GRUNTS = False`** — they are present and blocking. With them there,
`calculate_path` cannot reach Route 121's south edge, the x=30-31 corridor, or **any** ROUTE122
tile, **even with surf allowed** (`BADGE05_GET=True`, `party_has_surf=True`).

### THE TRIGGER — walk onto it, that is all
`data/maps/Route121/map.json`:
```
(25,5) (25,6) (25,7) (25,8)   var: VAR_ROUTE121_STATE == 0
                              -> Route121_EventScript_AquaGruntsMoveOut
```
The script walks the three grunts away, `removeobject`s them, and sets
**`VAR_ROUTE121_STATE = 1`**. No battle, no conversation.

**Completion test:** `get_event_var("VAR_ROUTE121_STATE") >= 1` — ‼ verify the exact name
resolves (`get_event_var` returns **-1** for an unknown name, which would make a guard never
fire). `HIDE_ROUTE_121_TEAM_AQUA_GRUNTS` is an acceptable secondary check.

### CHAPTER LEG SEQUENCE (use explicit legs, NOT one generic journey call)
1. **`ROUTE121 (25,5)`** — fires the gate. Guard `VAR_ROUTE121_STATE >= 1`.
2. **`ROUTE122 (22,30)`** — the plain tile directly BELOW the Mt. Pyre door at (22,29).
   ‼ Never target (22,29) itself: walking onto a warp fires it, so a warp tile is only ever an
   implicit destination, never an explicit one.
3. **`MT_PYRE_1F` → `MT_PYRE_EXTERIOR` → `MT_PYRE_SUMMIT (23,7)`** — see §Ch14a.

‼ **WHY EXPLICIT LEGS.** `calculate_path` spans only DIRECTLY CONNECTED maps. A single
`navigate_to_anywhere(MT_PYRE_SUMMIT, …)` from Fortree fails because it commits to a leg two
connections away; a chain of adjacent-map legs is exactly what the pathfinder handles natively.
Measured from the stall position ROUTE121 (21,5): `(25,5)` is **OK, 6 waypoints**.


## §Ch15 — MAGMA HIDEOUT: COMPLETE BUILD SPEC (decomp-verified 2026-08-10)

**This is the next unwritten chapter.** Built content ends at `do_mt_pyre_summit()`; there is no
hideout code. Everything below is verified against the pret/pokeemerald decomp and against live
ROM data, not recalled.

### ENTRY — solved, and it was never a terrain problem

> ‼‼ **CORRECTED 2026-08-10 (second pass) — THE ENTRY MODEL BELOW WAS INCOMPLETE, AND THE
> MISSING PIECE IS THE WHOLE MECHANISM.** The guard is real but it is not what seals the door.
> **`JaggedPass_OnLoad` walls the door shut with a metatile**, and a **STEP TRIGGER** opens it.
> Full decomp listing in the next block. Read that before writing or trusting anything here.

* Door: **`JAGGED_PASS (16,18)` → `MAGMA_HIDEOUT_1F`** (warp id 4, **unconditional** in `map.json`).
* Its only entry is **`(16,19)`**, occupied by a **Team Magma guard** until flag **847
  `HIDE_JAGGED_PASS_MAGMA_GUARD`** is set. That flag is set by the Mt. Pyre / Magma Emblem
  sequence, i.e. by the time this chapter runs it is already true.
* With the guard gone: `(16,20) → (16,18)` is **2 waypoints** *according to `calculate_path`* —
  ‼ and that number is **an artifact**, see the metatile block below. `(16,20)` itself is
  genuinely planner-reachable, and the descent reaches it: from every arrival tile below the top
  warps, 13–17 waypoints, control passing (`probe_ch15_travel.py`, 2026-08-10).
* ‼ **Develop only from a post-Emblem anchor.** `saves/post_mtpyre.ss1` has the flag set;
  `jagged_descent.ss1` and `post_winona.ss1` do NOT. Using a pre-Emblem save cost seven probes and
  two wrong conclusions (`08-MISTAKES` 2026-08-10).

### ‼‼ THE DOOR IS WALLED SHUT UNTIL A STEP TRIGGER OPENS IT (decomp, 2026-08-10)

`data/maps/JaggedPass/scripts.inc`:

```
JaggedPass_OnResume:
    call_if_eq VAR_JAGGED_PASS_STATE, 0, JaggedPass_EventScript_CheckHasMagmaEmblem
JaggedPass_EventScript_CheckHasMagmaEmblem::
    checkitem ITEM_MAGMA_EMBLEM
    goto_if_eq VAR_RESULT, TRUE, JaggedPass_EventScript_SetReadyToOpenHideout
JaggedPass_EventScript_SetReadyToOpenHideout::
    setvar VAR_JAGGED_PASS_STATE, 1          ← AUTOMATIC, on every map load, if the Emblem is held

JaggedPass_EventScript_ConcealHideoutEntrance::   ← called from JaggedPass_OnLoad while state <= 1
    setmetatile 16, 17, METATILE_Lavaridge_RockWall, TRUE
    setmetatile 16, 18, METATILE_Lavaridge_RockWall, TRUE

JaggedPass_EventScript_OpenMagmaHideout::         ← coord_event, gated VAR_JAGGED_PASS_STATE == 1
    special ShakeCamera … msgbox …BoulderShakingInResponseToEmblem … special ShakeCamera
    playse SE_EFFECTIVE
    setmetatile 16, 17, METATILE_Lavaridge_CaveEntrance_Top, TRUE
    setmetatile 16, 18, METATILE_Lavaridge_CaveEntrance_Bottom, FALSE
    special DrawWholeMapView
    setvar VAR_JAGGED_PASS_STATE, 2               ← THE CHAPTER'S REAL ENTRY GATE
```

**The five trigger tiles** (`JaggedPass/map.json` coord_events, all `VAR_JAGGED_PASS_STATE == 1`,
all → `JaggedPass_EventScript_OpenMagmaHideout`): `(21,15) (22,20) (21,20) (14,15) (13,15)`.

‼ **Use `(13,15)`.** Measured from the four plausible descent arrival tiles: `(13,15)`/`(14,15)`
are **8–10 waypoints**, the `(21,*)`/`(22,*)` trio **15–23**. The bot descends at x=13–14.

⇒ **THE SEQUENCE IS: hold the Emblem → enter the pass (state auto-set to 1) → step on a trigger
tile → ride out the scene → state 2, door open → walk onto (16,18).**

### ‼ WHY EVERY EARLIER READING OF THIS MAP WAS WRONG — and the rule that follows

Three separate conclusions were written into this project about this door. All three were the
metatile wall, misread:

| reading | what it actually was |
|---|---|
| "one-way ledges make the door unreachable" (2026-07-26) | the wall (and the guard) |
| "ledge-isolated, needs SCRIPTED MOVEMENT" (2026-08-10 AM, driven from `(14,9)`) | the wall |
| "`(16,20)` → Up ×12 does not move: a real south-facing LEDGE" (`--driver magmadoor`) | the wall |

‼ **AND THE STATIC PROBE CANNOT SEE IT.** `calculate_path` reads the ROM's **layout**, where
`(16,18)` is already a cave entrance — so it cheerfully answers "2 waypoints" for a tile the
running game has walled off. **A static PASS is not evidence when a script rewrites the
metatiles.** This is the KI-24 failure mode inverted: KI-24 was a static FAIL on reachable
terrain; this is a static **PASS** on unreachable terrain, and it is the more dangerous of the
two because it looks like confirmation.

**Prevention rule:** when the decomp shows a map's `OnLoad`/`OnResume` calling `setmetatile`,
reachability on that map must be graded by the VAR the script sets, never by `calculate_path`.

### THE WARP GRAPH (all eight maps, from each map.json)
```
JAGGED_PASS (16,18) ──> 1F (10,34)
1F (25,34) ──> 2F_1R        1F (31,3) ──> 2F_2R        1F (20,22) ──> 2F_3R
2F_1R (8,2) ──> 1F          2F_1R (11,23) ──> 2F_2R    2F_1R (17,33) ──> 3F_1R
2F_2R (36,4) ──> 1F         2F_2R (10,22) ──> 2F_1R
2F_3R (16,1) ──> 1F         2F_3R (16,13) ──> 3F_3R
3F_1R (23,3) ──> 2F_1R      3F_1R (21,9) ──> 3F_2R     3F_1R (7,21) ──> 4F
3F_2R (12,15) ──> 3F_1R
3F_3R (16,1) ──> 2F_3R      3F_3R (16,21) ──> 4F
4F (46,7) ──> 3F_1R         4F (20,21) ──> 3F_3R
```
~~**SHORTEST ROUTE TO 4F — three warps:** `1F (20,22)` → `2F_3R` → `(16,13)` → `3F_3R` →
`(16,21)` → **4F**. (The 2F_1R/3F_1R branch is longer and passes `3F_2R`, a dead end.)~~

> ‼‼ **CORRECTED 2026-08-10 — THAT ROUTE CANNOT BE WALKED FROM THE ENTRANCE.** A plain COLLISION
> flood of 1F (no elevation, no pathfinder) finds **three separate components**:
>
> | component | size | warps it holds |
> |---|---|---|
> | #0 | **299** | the entrance `(10,34)` **and** `(25,34)` → 2F_1R |
> | #1 | 70 | `(31,3)` → 2F_2R |
> | #2 | ‼ **9** | `(20,22)` → 2F_3R |
>
> `(20,22)` sits on a **nine-tile island**: it is an **EXIT from 2F_3R, never an entrance to it**.
> Counting warp hops on the graph made it look shortest; the graph does not know what is walkable.

**THE REAL ROUTE TO 4F — the `2F_1R` branch, every leg verified in one connected component with
its arrival tile (2F_1R **383** tiles, 3F_1R **154**, 4F **293**):**
```
1F (25,34)    -> 2F_1R   [arrive (8,2)]
2F_1R (17,33) -> 3F_1R   [arrive (23,3)]
3F_1R (7,21)  -> 4F      [arrive (46,7)]
4F: stand (17,21), face Left, TALK to Maxie (16,21)
```
‼ `3F_2R` is still a dead end and is still not entered — the branch was dismissed for the wrong
reason, not for a wrong conclusion about `3F_2R`.

### ⛔ 1F IS STRENGTH-GATED — the chapter's real blocker (measured 2026-08-10)
`calculate_path` reaches **44** of component #0's 299 tiles, and the boundary between the 44 and
the rest is **exactly three edges, every one into a Strength boulder**:
`(7,23)→(7,22)`, `(7,23)→(6,23)`, `(8,22)→(7,22)`.

⇒ The boulders at `(5,22)/(7,22)/(6,23)` **are the gate out of the entrance pocket**, not scenery
beside it. `obstacle_clearing.KNOWN_BUT_UNSUPPORTED` excludes `EventScript_StrengthBoulder` by
design ("a boulder is PUSHED, not removed; the success test cannot see it"), and no party member
on `post_mtpyre.ss1` knows Strength. **Tracked as `#24-strength`.**
‼ An earlier pass asserted these boulders were "west of the arrival and off the direct path".
That was inferred from their coordinates and it was wrong. **Adjacency is a measurement.**

### THE OBJECTIVE — a clean binary completion test
`MagmaHideout_4F_EventScript_Maxie` runs `trainerbattle_no_intro TRAINER_MAXIE_MAGMA_HIDEOUT`,
and on defeat sets:
* **`FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT`** ← ‼ the chapter's DONE condition, and
  `modules/story/chapters.py:200` already references this flag
* `FLAG_HIDE_MAGMA_HIDEOUT_GRUNTS`, `VAR_SLATEPORT_CITY_STATE = 1`,
  `VAR_SLATEPORT_HARBOR_STATE = 1` (these open the following beat), plus
  `FLAG_HIDE_SLATEPORT_CITY_CAPTAIN_STERN` / `..._GABBY_AND_TY` cleared.

⇒ **Grade this chapter binary**: from a cold start (or from `post_mtpyre.ss1`), does
`GROUDON_AWAKENED_MAGMA_HIDEOUT` end up set? No statistics needed — which is the whole argument
for spending here rather than on finish-rate tuning.

### OPPOSITION on the way
4F holds `TRAINER_MAXIE_MAGMA_HIDEOUT`, `TRAINER_TABITHA_MAGMA_HIDEOUT` and
`TRAINER_GRUNT_MAGMA_HIDEOUT_11/12/13`; the lower floors hold the other numbered grunts. All are
ordinary trainer battles — the boss-prep machinery already applies.

### ‼ THE ONE MEASURED RISK — the travel leg, not the hideout
An `--driver anchorcapture` probe from `post_mtpyre.ss1` to `JAGGED_PASS (16,20)` **whited out at
f24808** and never arrived. That probe drives RAW navigation with no prep or healing, unlike the
production story path — so it is a probe limitation, not proof the trip is impossible. **But it
does mean the chapter must reach Jagged Pass through the normal heal/prep path, and that leg
should be built and proven BEFORE the interior.** Treat "get to the door in one piece" as
increment 1, entering as increment 2, and the 4F fight as increment 3.

---

# §Ch16 — SLATEPORT HARBOR: the submarine theft (SPEC, 2026-08-11, decomp-verified, UNBUILT)

**Status: fully specified, nothing written.** This is the next unwritten beat, and it is the
CHEAPEST one in the remaining ladder: **there is no battle in it at all.** Sources read directly:
`data/maps/SlateportCity_Harbor/scripts.inc` and `.../map.json` (`pret/pokeemerald`).

## PRECONDITION — already satisfied by Ch15, for free
`VAR_SLATEPORT_HARBOR_STATE == 1`, which `MagmaHideout_4F_EventScript_Maxie` sets on defeat
(alongside `VAR_SLATEPORT_CITY_STATE = 1` and the Stern / Gabby-and-Ty hide flags). ‼ So the
entry condition needs **no new work** — assert it on the anchor rather than building toward it.
Every one of the four coord triggers is gated on exactly `VAR_SLATEPORT_HARBOR_STATE == 1`.

## THE MAP — `SLATEPORT_CITY_HARBOR`
| | |
|---|---|
| doors back to `SLATEPORT_CITY` | `(11,14)` / `(12,14)` → city warp 8; `(19,15)` / `(20,15)` → city warp 9 |
| escape warp | `MAP_SLATEPORT_CITY, (28,13)` (`setescapewarp` in `OnTransition`) |
| **the trigger column** | **`x=8`, `y=11,12,13,14`, elevation 3** — four triggers, `AquaEscapeTrigger0..3` |
| Archie | `(8,10)` — directly ABOVE the top trigger `(8,11)` |
| Aqua grunt | `(7,10)` |
| submarine shadow | `(7,9)` |
| Capt. Stern | `(6,13)`, but `ReadyAquaEscapeScene` **moves him to `(12,13)`** on transition |

‼ `OnTransition` also sets `FLAG_HIDE_SLATEPORT_CITY_HARBOR_PATRONS`, so the Beauty / Sailor /
Fat Man vanish for this scene. **Do not model the harbor's population from `map.json` alone** —
the transition script rewrites it. (Same class as the Jagged Pass guard, which cost a three-week
deferral: `map.json` describes the map, the `OnTransition` script describes the *era*.)

## THE SCENE — a cutscene, not a fight
`AquaEscapeTrigger0..3` → `lockall` → Archie's "you again / our hideout is in Lilycove" →
the grunt and Archie board → the submarine leaves → **`setvar VAR_SLATEPORT_HARBOR_STATE, 2`**,
`setflag FLAG_MET_TEAM_AQUA_HARBOR`, `setflag FLAG_HIDE_LILYCOVE_MOTEL_SCOTT` → Stern walks over
→ "why steal my submarine" → `setflag FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1/2_BLOCKING_ENTRANCE` →
`copyobjectxytoperm` → **`releaseall`**.

‼ Trigger 3 (`y=14`) is the one to aim for from the south doors — it `applymovement`s the player
UP into the scene itself, so the walk-in is scripted for you. Triggers 0-2 assume you are already
level with Archie.

## ‼‼ THE ONE TRAP, AND THIS PROJECT HAS ALREADY PAID FOR IT ONCE
**`VAR_SLATEPORT_HARBOR_STATE` is set to 2 roughly HALFWAY through the script**, with Stern's
approach, a second `msgbox`, two more `setflag`s and the `releaseall` still to run. Exiting the
wait the instant the var flips leaves the avatar `lockall`ed and every later button press does
nothing — **this is the exact failure that cost two runs on 2026-08-10**
(`EventScript_ActivateStrength`; see `08-MISTAKES` and `04-HANDOFF` "a flag set by a script is NOT
the end of that script"). **Grade on the var, but wait for CONTROL.**

## COMPLETION TEST — binary, no batch
**`VAR_SLATEPORT_HARBOR_STATE == 2`.** Secondary confirmations: `FLAG_MET_TEAM_AQUA_HARBOR` set,
and the avatar controllable again on `SLATEPORT_CITY_HARBOR`.

## WHAT IT OPENS
`FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1/2_BLOCKING_ENTRANCE` — the two grunts barring the **Lilycove
Aqua Hideout** entrance are removed. That is ladder row 17 (`TEAM_AQUA_ESCAPED_IN_SUBMARINE`,
room keys, the Electrode puzzle) and it is a much larger chapter. **This beat is the key to it.**

## SUGGESTED BUILD ORDER
1. **Anchor first.** Manufacture or find a save with `VAR_SLATEPORT_HARBOR_STATE == 1` — i.e.
   post-Maxie. `probe_anchor_inventory.py` first; if none exists, `--driver anchorstory` with
   `CAPTURE_TARGET=SLATEPORT_CITY`. ‼ **Assert the var on the anchor before spending a probe on
   it** — seven probes ran from the wrong era on 2026-08-10.
2. **Travel leg**: reach `SLATEPORT_CITY` and the harbor door. ‼ KI-48 (ROUTE110 → MAUVILLE
   direct navigation, 3/3 failures) and KI-49 (map-granular journeys) are the standing risks on
   any cross-map leg; prefer an anchor already standing in Slateport.
3. **The scene**: walk onto `(8,14)` (trigger 3) and ride to `releaseall`.
4. Grade `VAR_SLATEPORT_HARBOR_STATE == 2`. No statistics.

## §Ch16 IMPLEMENTATION PLAN (2026-08-11) — written so the build is mechanical once the anchor exists

Every coordinate below is decomp-read, not inferred. The city-side door and the trigger tile are
the only two the code needs.

### The route, end to end
```
SLATEPORT_CITY (28,12)            <- warp id 8, the harbor door  (escape warp returns to (28,13))
  -> SLATEPORT_CITY_HARBOR (11,14)   <- harbor warp id 0, where you land
  -> walk WEST along row 14 to (8,14)  <- AquaEscapeTrigger3, three tiles
```
‼ Aim for **trigger 3** specifically. It is the only one of the four that `applymovement`s the
player UP into the scene itself, so the walk-in is scripted rather than something the bot has to
get right. The other three assume you are already level with Archie.

### The function — `do_slateport_harbor_theft()` in `modules/story/early_game.py`
Shape it on `do_mt_pyre_summit()` (the closest analogue: a coord trigger, no conversation, no
battle), NOT on `do_magma_hideout()` (which is a dungeon crawl plus a boss).

```
if VAR_SLATEPORT_HARBOR_STATE >= 2: return            # already done, idempotent
travel to SLATEPORT_CITY through the normal heal/prep path
navigate to (28,12) and warp in
navigate SLATEPORT_CITY_HARBOR (11,14) -> (8,14)
ride the scene: press nothing but A/B advance, and WAIT FOR CONTROL  (see the trap below)
```

### ‼‼ THE TRAP — the completion var fires MID-SCRIPT
`setvar VAR_SLATEPORT_HARBOR_STATE, 2` runs **before** Stern walks over, before the second
`msgbox`, before two `setflag`s and before `releaseall`. **Exiting the wait the instant the var
flips leaves the avatar `lockall`ed and every later button press does nothing.** This is exactly
the `EventScript_ActivateStrength` failure that cost two runs on 2026-08-10.

⇒ The wait condition is **`VAR_SLATEPORT_HARBOR_STATE == 2` AND the avatar is controllable**, in
that order, with `wait_until_truly_controllable()` after it. Same shape the Strength fix ended up
with.

⇒ And apply KI-51's lesson while writing it: **the loop must also notice leaving
`SLATEPORT_CITY_HARBOR`.** There is no battle here so a whiteout is not the risk, but the rule
generalises — a loop whose exit is a story var must watch for the ways the game can move the
player out from under it.

### Wiring — Segment 16 in `plugins/custom_modes/story_mode.py`
Follow Segment 15's pattern exactly (it sits directly above the "END OF BUILT CONTENT" banner):
```python
# --- Segment 16: the SLATEPORT HARBOR submarine theft (§Ch16). A coord trigger, no
#     battle. Maxie's defeat set VAR_SLATEPORT_HARBOR_STATE to 1, which is what arms
#     the four triggers; the scene sets it to 2. ---
from modules.story.early_game import do_slateport_harbor_theft

if not _done_var("SLATEPORT_HARBOR_STATE", 2):
    yield from do_slateport_harbor_theft()
else:
    console.print("[dim]Story: Slateport Harbor theft already done — skipping.[/]")
_guard("Slateport Harbor theft (Ch16)", lambda: _done_var("SLATEPORT_HARBOR_STATE", 2))
```
‼ `_done_var` **raises on a phantom var name** rather than returning False — that is deliberate
(`get_event_var` returns −1 for an unknown name, which compares False against every threshold for
ever). Use it; do not hand-roll the comparison.

### The driver — `--driver slateporttheft`
Mirror `MagmaHideoutMode`: run the production function, log
`RESULT harbor_state=<n> map=<enum> at=<tile> controllable=<bool> whiteouts=<n>`, and **capture
nothing** (this chapter's output is a var, not an anchor the next beat needs). Acceptance is
`harbor_state == 2 AND controllable == True` — the second half is the trap above, so it belongs in
the acceptance test, not just in the code.

### What "done" unlocks
`FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1/2_BLOCKING_ENTRANCE` — the Lilycove Aqua Hideout (ladder row
17). That is a much larger chapter: room keys, an Electrode puzzle, `TEAM_AQUA_ESCAPED_IN_SUBMARINE`.

---

## §Ch21 ATLAS — Sootopolis / Cave of Origin / Sky Pillar / Rayquaza (built 2026-08-24)

**PROVENANCE, PER ROW.** ✅ **HARD** = read out of ROM map headers by `probe_ch21_topology.py`
(evidence: `tools/story-dev/evidence/2026-08-24-ch21-topology-probe.stdout.txt`, every assertion
PASS, fault-tested both ways). 📝 **NOTE** = decomp-cited research, authoritative-doc rules apply —
it is a NOTE until verified here. ❓ **OPEN** = nobody knows; needs a live drive.
⛔ **No coordinate below was recalled.** The ones we could not read are marked ❓, not filled in.

### The spine: `SOOTOPOLIS_CITY_STATE` has SEVEN states (0-6), not five

📝 (`ai-research-notes/CLAUDE-VALIDATED-story-round1.md` §3f — every setter located and read.)
⛔ **Our API takes the BARE name `SOOTOPOLIS_CITY_STATE`; `VAR_SOOTOPOLIS_CITY_STATE` is the decomp
spelling and returns −1 here.** (Playbook §4.2 — this is the default mistake, not an exotic one.)

| state | meaning | set by | what it means for the bot |
|---|---|---|---|
| 1 | Kyogre awakened | `SeafloorCavern_Room9` — **the SAME block that sets `ROUTE128_STATE`** | ✅ §Ch20 leaves us here |
| 2 | the Groudon-vs-Kyogre scene has played | `SootopolisCity/scripts.inc:243` (arrive via Poké Center) **or** `:342` (arrive via Dive) | two camera variants; ours is the DIVE one — budget for a locked scene |
| 3 | Wallace met in the Cave of Origin, go to Sky Pillar | `CaveOfOrigin_B1F` | ⛔ gated behind the multichoice hang, below |
| 4 | Wallace has opened the Sky Pillar door | `SkyPillar_Outside/scripts.inc:82` | the door is a metatile swap, not a warp |
| 5 | **Rayquaza awakened** | `SkyPillar_Top/scripts.inc:126` | ‼ the ONLY window in which Maxie and Archie are talkable |
| 6 | crisis over | `SootopolisCity_Gym_1F/scripts.inc:102` — i.e. **beating Juan** | that is §Ch22, not this chapter |

⛔ **THERE IS NO VALUE OF THIS VAR THAT MEANS "THE FIGHT IS OVER".** The city keeps the legendaries layout at state 5 while `SKY_PILLAR_STATE <= 1`; **the fight-is-over predicate is `SKY_PILLAR_STATE >= 2`**, set in Sootopolis AFTER the Rayquaza arrival scene — not when you wake Rayquaza. Grading Ch21 on the city var alone would call the crisis resolved while it is still raging.

### ⛔ THE FOUR THINGS THAT WILL HANG OR STRAND THE BOT

*(It said THREE until the Cave-of-Origin body-block was found on 2026-08-24 — a heading is a claim about every bullet beneath it, so the count moves with the list.)*

1. ⛔⛔ **`CaveOfOrigin_B1F`'s multichoice is an UNBOUNDED DERAIL — only index 2 ("Sky Pillar")
   advances.** Indices 0/1/3, the switch default **and a B-press** all `goto` back to the same
   prompt: **no counter, no timeout, no escape** (`05-KNOWN-ISSUES.md:256`). A blind A-press hangs
   forever. Use `wait_for_multiple_choice_question(2)`. ‼ Three of the four mandatory critical-path
   multichoice menus default to the WRONG option — the swept table of all 49 sites is §3i.
2. ⛔ **The Rayquaza awakening is a COORD TILE, not the sprite.** 📝 `SKY_PILLAR_TOP (14,9)`, gated
   `VAR_SKY_PILLAR_RAYQUAZA_CRY_DONE == 0`. A bot that climbs to the top and presses A at Rayquaza
   waits forever — **the identical shape as the Route 128 trigger that already bit §Ch20.**
   ⚠ (14,9) is UNVERIFIED here and DISAGREES with the two Rayquaza coordinates our code holds
   (`static_soft_resets.py:55` `(14,6)`, `static_run_away.py:163` `(16,14)`/`(14,7)`) — but **both of
   those are the POST-GAME catchable Rayquaza, a different event.** Verify live before building.
3. ⛔⛔ **THE CAVE OF ORIGIN ENTRANCE IS BODY-BLOCKED BY AN NPC, NOT BY A SCRIPT — AND (31,18) IS
   THE SOLE PASSAGE.** `LOCALID_SOOTOPOLIS_EXPERT` stands there with `"flag": 0` (never hidden), and
   the approach is a one-tile corridor. The scripts shuffle who occupies it by city state: blocked at
   0/1; **blocked at 2/3 UNTIL Steven's escort sets `FLAG_STEVEN_GUIDES_TO_CAVE_OF_ORIGIN`**; blocked
   again at 4 (Wallace), 5 and 6 (the Expert). ⇒ **A bot that plans "walk into the Cave of Origin"
   without first talking to Steven paths into a body and stalls.** Steven does not merely unblock it —
   `SootopolisCity_EventScript_StevenLeadPlayerCaveOfOrigin` ends `warp MAP_CAVE_OF_ORIGIN_ENTRANCE,
   9, 20`, i.e. **he WARPS you in.** *(The corridor geometry is agent inference from blockdata —
   verify with a live `calculate_path` before building.)*
4. ⛔ **HM07 Waterfall needs BOTH Maxie AND Archie talked to at state 5** — that sets
   `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE`, which also unlocks the Gym door and every house door.
   **Miss one NPC and the run is dead.** `RECEIVED_HM_WATERFALL` is this chapter's grading flag.

### ✅ HARD ROUTE — every warp below was read from ROM map headers, not from a note

*(Provenance, since the two halves have DIFFERENT sources: the **warps** come from `probe_ch21_topology.py` reading ROM map headers; the **surf leg** `128→127→126` comes from our own ROM-extracted `cache/warp_graph_BPEE0.json` — Routes 126–131 and Pacifidlog are ALL region 0, so `calculate_path` spans the leg in ONE `navigate_to`, while `SOOTOPOLIS_CITY` is region 1 with ZERO edges. Both re-derived here 2026-08-24; see the ADDENDUM in `evidence/2026-08-24-skypillar-clean-reachability.txt`.)*

```
  ROUTE128 (38,24)  --surf-->  ROUTE127  -->  ROUTE126        [one region: ONE navigate_to]
  ROUTE126 <a dive tile>  --dive-->  UNDERWATER_ROUTE126 (same x,y)
      HARD: ROUTE126 and UNDERWATER_ROUTE126 are BOTH (80,80) -> the same-(x,y) landing HOLDS
      HARD: 1,349 dive-capable tiles on ROUTE126; nearest the warp column: (45,66) dist=1
  UNDERWATER_ROUTE126 (45,65)  --warp-->  UNDERWATER_SOOTOPOLIS_CITY (9,8)   [its ONLY warp]
  STOP: (9,8) AND (10,8) WARP STRAIGHT BACK to Route 126 -- STEP OFF BEFORE SURFACING
  UNDERWATER_SOOTOPOLIS_CITY  --surface-->  SOOTOPOLIS_CITY
      HARD: map is (20,10); 33 tiles have collision==0
      HARD: ZERO tiles are "Underwater Blocked Above" or "Seaweed No Surfacing"
            => THE KI-72 SURFACING TRAP DOES NOT APPLY ON THIS MAP (measured, not assumed)
  SOOTOPOLIS_CITY (60,60)   (31,16) --warp--> CAVE_OF_ORIGIN_ENTRANCE (9,20)
  CAVE_OF_ORIGIN_ENTRANCE (9,5)  --> CAVE_OF_ORIGIN_1F (11,17)
  CAVE_OF_ORIGIN_1F       (14,5) --> CAVE_OF_ORIGIN_B1F (9,3)      [dead end: Wallace]
  ROUTE131 (36,6) --> SKY_PILLAR_ENTRANCE (6,16)
  SKY_PILLAR_ENTRANCE (14,4) --> SKY_PILLAR_OUTSIDE (17,13)
  SKY_PILLAR_OUTSIDE  (14,5) --> SKY_PILLAR_1F (6,13)
  SKY_PILLAR_1F (10,1) --> 2F ; 2F (3,1) --> 3F ; 3F (11,1) --> 4F ; 4F (3,1) --> 5F
  SKY_PILLAR_5F (10,1) --> SKY_PILLAR_TOP (16,14)
```

### ⛔ SOOTOPOLIS IS A TRUE ISLAND — and that decides the Sky Pillar leg

✅ `SOOTOPOLIS_CITY` is **the only map in its region** and has **ZERO map connections**. The city's
only non-Dive warps are its own buildings and the Cave of Origin.
⇒ **YOU CANNOT SURF FROM SOOTOPOLIS TO ROUTE 131.** Two options, and this is a real design choice:

* ⛔ **(a) FLY to Pacifidlog — RULED OUT 2026-08-24, MEASURED.** `VISITED_PACIFIDLOG_TOWN` is
  **False** on `post_dive.ss1`, and §Ch20 never goes near Pacifidlog, so it is still False when Ch21
  starts. `fly_to()` requires the destination's VISITED flag, so **this option silently is not one.**
  *(Badges 1-7 are set and 8 is not, as expected; `BADGE06_GET` was never the binding constraint.)*
  ‼ `VISITED_SOOTOPOLIS_CITY` is **False** too — so **Fly cannot shortcut INTO Sootopolis either.**
  ⇒ **BOTH the entry and the exit are by water. There is no air option anywhere in this chapter.**
* ✅ **(b) SWIM BACK OUT — THE ONLY OPTION, not a preference.** — dive out of Sootopolis (`Sootopolis Deep Water` is in `dive()`'s allowed
  list), warp to `UNDERWATER_ROUTE126`, surface, then surf 126→127→128→129→130→131. Long, no Fly needed.
  ⛔ There is **no `UNDERWATER_ROUTE130` or `UNDERWATER_ROUTE131`** — no diving shortcut near the pillar.

### ⛔⛔ THE SKY PILLAR CLIMB REQUIRES A DELIBERATE FALL — MEASURED, AND IT CORRECTS THIS FILE

⛔ **AN EARLIER DRAFT OF THIS ATLAS SAID UPSTREAM'S ROUTE "STALLS ON 4F BECAUSE THE FALL NEVER
HAPPENS ON THE CLEAN LAYOUT". THAT WAS WRONG, AND IT WAS WRONG IN THE DANGEROUS DIRECTION** — it
told a future author to throw away the one route that works. ‼ **`LAYOUT_SKY_PILLAR_4F_CLEAN` RETAINS
FIVE CRACKED TILES** at `(0,3) (1,3) (6,4) (7,4) (9,4)` — the "clean" layouts are clean on **2F**,
not everywhere. `2F_Clean` has 0; `4F_Clean` has 5.

✅ **MEASURED HERE 2026-08-24** by decoding the shipped `data/layouts/SkyPillar_*_Clean/map.bin`
collision bits (10-bit metatile / 2-bit collision / 4-bit elevation) and running BFS. Two independent
agents reached the same structure; these numbers are OUR OWN, not either agent's:

| leg (CLEAN layout) | result |
|---|---|
| `1F` (6,13)/(7,13) → (10,1) up | ✅ 17 / 16 steps |
| `2F` (10,1) → (3,1) up | ✅ 10 steps, **0 cracked tiles on 2F_Clean** |
| `3F` (3,1) → (7,1) | ⛔ **NO PATH** |
| `4F` (11,1) → (3,1) | ⛔ **NO PATH** (even allowing cracked tiles) |
| `4F` (7,1) → (3,1) | ✅ 7 steps, crossing 0 cracked tiles |
| `5F` (3,1) → (10,1) | ✅ 34 steps |
| `Top` (16,14) → the (14,9) trigger | ✅ 14 steps |

⇒ **`4F (3,1)` (the 5F stairs) and `3F (7,1)` are SEALED 11-TILE POCKETS.** Their only entrance is a
**fall through the cracked `4F (6,4)` or `(7,4)`** — `warphole` preserves (x,y), so you land on
`3F (6,4)`, which our BFS confirms is inside the pocket holding `3F (7,1)`:
`[(5,2) (6,2) (6,3) (6,4) (7,1) (7,2) (7,3) (7,4) (8,2) (8,3) (9,2)]`.

**THE STORY ROUTE, THEREFORE:**
```
  1F (10,1) -> 2F ; 2F (3,1) -> 3F ; 3F (11,1) -> 4F (11,1)
  cross 4F to (5,4)          [reachable from (11,1) without touching a crack -- MEASURED]
  step EAST onto (6,4)       [CRACKED -> you FALL, on purpose]
  !! NOT (9,4) -- IT IS A DECOY. All three of 4F's reachable cracked tiles drop you onto the
  !! SAME (x,y) on 3F, but only (6,4)/(7,4) land INSIDE the sealed pocket. (9,4) lands in 3F's
  !! MAIN region, which cannot reach 3F (7,1) -- so the whole climb is wasted and the bot loops.
  !! MEASURED: 3F (6,4) in pocket=True, (7,4) in pocket=True, (9,4) in pocket=False.
  land 3F (6,4) -> walk to 3F (7,1) -> 4F (7,1) -> west along row 2 -> 4F (3,1) -> 5F -> Top
```
⇒ **UPSTREAM'S ROUTE SHAPE IS CORRECT AND WORTH COPYING** (`puzzle_solver.py:144-168`, whose comment
literally reads `# after falling down to floor 3`). ⛔ **What is wrong with it for the story is ONLY
its `assert_registered_item("Mach Bike", ...)` and its `mount_bike()`** — those hard-fail on frame
one for a bikeless bot. Take the waypoints, drop the bike.
⛔ **AND THE PATHFINDER CANNOT EXPRESS THIS LEG.** `map_path.py` does not model `"Cracked Floor"` at
all, so it will never propose the fall — the fall must be an EXPLICIT chapter step, exactly like
`dive()`. A `calculate_path` to `4F (3,1)` will simply raise.

*(The same file's Seafloor Cavern branch ends in `set_manual_mode()`; see the corrected note
`2026-08-13-puzzle-solver-already-ships-ch21-and-the-regi-arc.md`.)*

### ✅ THE MACH BIKE IS NOT NEEDED FOR THE STORY — but NOT for the reason first written

The story ascent runs at `SKY_PILLAR_STATE` 0 then 1, **both `< 2`**, so every floor swaps to its
`_CLEAN` layout — decomp-verified on all six floors. The bot has never owned a bicycle
(`RECEIVED_BIKE` appears **only** in two data tables; no code reads it) and does not need one.
⛔ **DO NOT BUILD A BIKE SOLVER FOR THE STORY.** *(Two rows in this very file said the opposite
until 2026-08-24 — see the correction in `20-POST-FORTREE-RECON.md` §4.2.)*

⛔ **BUT DO NOT ENCODE IT AS "THE FLOORS DO NOT COLLAPSE ON THE FIRST VISIT."** They do:
`STEP_CB_CRACKED_FLOOR` and `setholewarp` are registered from `MAP_SCRIPT_ON_RESUME` on 2F and 4F
with **no state guard at all** — the mechanic is ALWAYS armed. What changes is only the LAYOUT. The
story visit works because `2F_Clean` has zero cracked tiles and because 4F's surviving five are ones
you either avoid or *want* to fall through (above).

⛔ **THE ACRO BIKE NEVER WORKS, EVEN POST-GAME.** `GetPlayerSpeed()` returns `PLAYER_SPEED_FASTER`
for Acro and only `sMachBikeSpeeds[2] == PLAYER_SPEED_FASTEST` clears the check —
`FASTER != FASTEST`. Walking and Dash are `NORMAL`/`FAST`; all fall.
⛔ **STOPPING ON A CRACKED TILE IS FATAL EVEN AT TOP SPEED** — the tile is rewritten to a HOLE three
frames later and the hole check runs every frame regardless of movement. A bot that pauses
mid-crossing to think drops a floor.

⚠ **The residue that IS real:** `map_path.py` does not model `"Cracked Floor"` (the behaviour is
decoded in `map.py:391` and never consulted), so it plans straight across one. For the STORY that is
survivable — the one crossing is the intended fall — but it gates the POST-GAME Rayquaza capture
(2F needs 10 cracked tiles crossed at top speed), Mirage Tower and Granite Cave B1F.

### ⛔ THREE OF THIS CHAPTER'S MAPS ARE LAYOUT-SWAPPED AT RUNTIME — a class, not a quirk

Measured 2026-08-24. **A static tile read of any of these describes a map the bot never sees:**
* **`SKY_PILLAR_1F..TOP`** → `LAYOUT_SKY_PILLAR_*_CLEAN` while `SKY_PILLAR_STATE < 2`.
* **`ROUTE131`** → `LAYOUT_ROUTE131_SKY_PILLAR`, **unconditionally**, in `OnTransition`. The tower
  door at `(36,6)` is **elevation 1 in the DEFAULT layout and elevation 3 in the swapped one** — a
  statically-derived atlas shows **open water where the door is**.
* **`SOOTOPOLIS_CITY`** → a crisis layout selected by `SOOTOPOLIS_CITY_STATE` (legendaries vs normal).

⇒ **WARPS are map-header data and are safe to read statically. TILES ARE NOT.** That is exactly why
`probe_ch21_topology.py` asserts only on warps, sizes and the two UNDERWATER maps (which do not swap).
⇒ ‼ **AND THE FIX IS NOT ALWAYS "GO LIVE".** The decomp ships every swapped layout as
`data/layouts/<NAME>/map.bin`; decoding those bytes answers the question exactly, and that is how the
whole Sky Pillar staircase was settled without an emulator. ⛔ A 25-minute drive was queued to answer
what **392 bytes** answered — ask whether the source data can be read directly BEFORE filing a
question as "needs a live run".

### ✅✅ LEG 1 IS BUILT AND DRIVEN — `modules/story/sootopolis.py`, `--driver ch21dive` (2026-08-24)

`ACCEPTANCE: PASS` on drive 3. ⛔ **The chapter is still NOT wired into `_play()`.** ‼ *(SUPERSEDED 2026-08-27 — this line read "legs 2-5 do not exist", which stopped being true on 2026-08-26/27: **legs 2a and 2b ARE built and driven** (`--driver ch21escort`, `--driver ch21cave`, both `ACCEPTANCE: PASS`) and **leg 3's pocket-exit probe is MEASURED** — see the LEG 3 STEP 0 section below. Legs 4-5 (Sky Pillar, HM07) genuinely do not exist. A Tier 1 review caught this: the handoff names THIS FILE as the authority for leg status, so a stale sentence here mis-states the arc for every cold reader.)*
```
RESULT reached=True at=SOOTOPOLIS_CITY(29,53) arrived=True center_path=True cave_path=False state=2
```
**TWO ATLAS CLAIMS WERE CORRECTED BY THE DRIVES, both in the "I reasoned it out" direction:**
* ⛔ **"Emerge preserves (x,y), so we come up at `(9,7)`."** True of the emerge and IRRELEVANT: the
  ARRIVAL CUTSCENE then warps the player. The bot rests at **`(29,53)`**. ‼ The predicted constant was
  DELETED rather than updated — the game chooses that tile, so it is MEASURED. (Hard-coding a guessed
  coordinate is how `ROOM8_PUSHES` got fabricated.)
* ⛔ **"the Cave of Origin door `(31,16)` is where leg 2 goes."** `calculate_path` **REFUSES to route there from the arrival point** — the
  whole column `(31,16)..(31,22)`. ✅✅ **THE CAUSE IS MEASURED NOW (2026-08-27, `--driver
  ch21leg2probe`), no longer "undetermined" and NOT the Expert alone:** it is the
  **Steven `(20,36)` + Boy2 `(19,37)` two-tile body-block cut** through `map_path.py`'s
  loadedness-not-occupancy rule (`:843-853` — a flag-visible object that is NOT camera-loaded
  makes its ROM-template tile impassable). Proven by the flip: from `(29,53)` all five tiles
  refuse; **standing at `(21,36)` with both NPCs camera-loaded, the SAME queries path —
  `(31,16)` 98 wp, `(31,22)` 94 wp.** *(An earlier "ZERO NPCs loaded so not the body-block"
  inference was invalid — camera window; and the "elevation-transition rule" guess is refuted.
  The 52-tile-island figure is UNVERIFIED either way — the leg-2 build spec measured ~350 and
  says re-derive before trusting either number.)*
  It matches the decomp: Steven's escort ends `warp MAP_CAVE_OF_ORIGIN_ENTRANCE, 9, 20` — **the game
  WARPS you in.** ⇒ leg 2 is *find and talk to Steven*, never *walk to the cave*.

‼ **AND "ON THE MAP" IS NOT "ARRIVED".** `SootopolisCity_OnFrame` fires the arrival scene with NO
coordinate condition the instant the map loads, and sets the var to 2 only at its END. Drive 1 reported
`reached=True … state=1` mid-scene — **an acceptance of "are we in Sootopolis?" would have PASSED it.**
⇒ **GRADE ON THE VAR, NEVER ON THE MAP.**

### ✅✅ LEG 3 STEP 0 — THE POCKET EXIT IS MEASURED, STATICALLY **AND** LIVE (2026-08-27)

`probe_ch21_pocket_exit.py` (static, seconds, 4 controls) + `--driver ch21pocket` (live,
`ACCEPTANCE: PASS`, 4,166 frames). Evidence: `evidence/2026-08-27-ch21-pocket-exit-probe.stdout.txt`,
`evidence/2026-08-27-ch21-pocket-LIVE-drive.stdout.txt` (both arms). Fixture: `saves/post_wallace.ss1`
(PINNED, `CAVE_OF_ORIGIN_B1F (9,14)`, state 3, party **687/687 = 100%**).

⛔⛔ **A WARP TABLE GIVES THE WARP *EVENT* TILE — NOT WHERE THE AVATAR COMES TO REST.** This is the
single fact the drive bought, and neither the ROM warp table nor the decomp JSON could have supplied it:

| warp | table target | **avatar RESTS at (MEASURED LIVE)** |
|---|---|---|
| `B1F (9,3)` → 1F | (14,5) | **(14,5)** — same tile |
| `1F (11,17)` → Entrance | (9,5) | **(9,6)** — one south |
| `Entrance (9,20)` → City | (31,16) | **(31,17)** — one south |

⇒ **§4.11 IS ANSWERED, AND ITS ANSWER IS (31,17), NOT (31,16).** (31,16) is correct as the warp
event tile — both our ROM reader and the decomp agree on it, and *both are answering a different
question*. ⛔ **Leg 3 must key on the measured RESTING tile.** Hard-coding (31,16) as the post-warp
position is wrong by one tile, silently.

✅ **THE POCKET IS REAL, AND ITS CAUSE IS PROVEN BY FAULT INJECTION** (not by a re-implementation —
production's own `calculate_path` is the oracle). From the landing tile with **nothing loaded**,
`(43,31)`, `(29,53)` and `(21,36)` **all refuse**, symmetric in both directions. Marking Steven
(local_id 7) loaded at his state-3 tile **(32,18)** re-opens all three. The rig's positive control
reproduces the **98 wp** that `--driver ch21leg2probe` measured live, so the counterfactual is trusted.
* **Pocket size: 347 tiles** by production's planner (three independent BFS re-implementations had
  predicted ~343 — first confirmation from the oracle, and it retires the stale "52-tile island").
* It is **ONE connected component**: from the deepest point (20,35) the same 347 tiles are reachable.
  ⇒ an interrupted walk leaves the bot **stranded but alive**, never hard-crashed.

‼‼ **THE RE-PLAN DANGER ZONE IS 89 OF 121 CITY WAYPOINTS — 74% OF THE ESCAPE.** Walking the route
tile by tile and asking the pessimistic question at each: a plan re-computed while Steven is unloaded
**refuses on the first 89 waypoints**, and the first safe waypoint is index 89 — **(20,36) itself**,
his vacated template tile. ⛔ The build spec's "a re-plan more than ~9 tiles from Steven refuses" is
**far too optimistic**; the exposure runs almost the whole way.

✅ **THE WALK OUT SUCCEEDS, AND THE BOT CAN CONTINUE.** Live from (31,17): **121 wp** to the Poke
Center FRONT tile `(43,32)`, 1,624 frames, `whiteouts=0`. ⛔ The target is deliberately (43,32) and
not the door (43,31): a path TO a door FOLLOWS the warp, so a first version ended *inside the
building* — which silently skipped the "and the bot can continue" check while ACCEPTANCE still said
PASS, the exact §Ch15/18/19 false-pass shape. From (43,32) the planner reaches **(29,53), the dive
tile leg 3 needs, in 37 wp** — that is the continuation proof. Steven **(32,18)** and the Expert
**(30,18)** were sighted live for the first time, exactly where §5 predicted.

✅✅ **AND THE POCKET RE-SEALS BEHIND THE BOT — measured, not inferred.** The same matrix taken again
from the END tile (43,32), where Steven is now out of camera range, refuses `(31,22)`, `(20,36)` AND
`(19,37)` while still reaching `(29,53)` and `(21,36)`. ⇒ the bot walked out through a gap that
closed behind it. ⛔ **Leg 3 gets ONE attempt at this crossing per visit**; there is no going back
for a forgotten errand inside the pocket without re-loading Steven.

✅ **THE LIVE 'NOTHING LOADED' ARM, TAKEN FOR FREE ON B1F.** Standing in the cave, `get_map_objects()`
is exactly `[(255,(9,14))]` — the player alone — and from there `(31,17)→(43,32)` and `(31,17)→(29,53)`
both raise `PathFindingError`. The seal is therefore measured LIVE, not only in the static rig.
‼ This matters because the near-arm alone is *guaranteed* to say "the pocket is open" and so proves
nothing on its own; an adversarial review named exactly that gap.

✅ Static and live AGREE tile-for-tile from (31,17): `(43,32)` 121, `(29,53)` 118, `(21,36)` 91,
`(20,36)` 90, `(19,37)` REFUSED — identical in the static rig and the drive.

⚠ **BOTH WALK ARMS MEASURED IDENTICAL — SO THE A/B IS *NOT* DISCRIMINATING, AND MUST NOT BE QUOTED
AS ONE.** `follow_waypoints` (plan once, never re-plan) and a naive `navigate_to` both finished in
**exactly 1,781 frames**: `navigate_to` wraps the same waypoint walk, so with nothing forcing a
re-plan they are the same code path. The prediction was filed in the driver docstring *before* the
run and held. ⇒ **The danger is a TAIL risk. A green run is not evidence the naive design is safe.**
⛔ And neither primitive RECOVERS: `follow_waypoints` raises on a waypoint timeout, `navigate_to`
re-plans and then refuses. **Leg 3 should plan once at the resting tile and, on a timeout, walk back
toward (32,18) to re-load Steven before re-planning** — that recovery is a RECOMMENDATION, unbuilt
and unproven, not a measured result.

✅ **§4.10 ENCOUNTER PRESSURE, ANSWERED:** **2 encounters** over the whole 61-waypoint return, **both
on `CAVE_OF_ORIGIN_1F`**. ⛔ **B1F has NO wild-encounter header at all — zero encounters are possible
there**; Entrance and 1F carry land tables (rate 4; Zubat/Golbat/Sableye). ‼ Do NOT read our
per-tile `has_encounters` flag as "this map has encounters" — it is a metatile-behaviour capability
(MB_CAVE) and reads true across ~1,300 tiles of B1F, where encounters cannot fire. Counted via the
`on_battle_started` **hook** (`_listeners.py:108` calls it unconditionally), never by polling — a
driver generator gets no frames during a battle, so a poll could never have answered positive.

✅ **Intra-cave return, by production rather than by re-implementation:** B1F `(9,14)→(9,3)` **21 wp**,
1F `(14,5)→(11,17)` **24 wp**, Entrance `(9,5)→(9,20)` **16 wp** — **61 wp + 3 warps**. The spec's
21/23/15 were *step* counts; a step count is not a waypoint count, so these agree.

⚠ **A PRIOR, RECORDED SO A PASS IS NOT OVER-READ:** this walk had already been done live once, by
accident — the escort-v1 bug rode past its bail and ended at `SOOTOPOLIS_CITY (20,37)`, the far side
of the choke, at state 2 (where `SetEnterCaveOfOriginObjPos` places Steven identically). Its route was
never logged, so it corroborates rather than proves.

### ✅ THE FIXTURES EXIST — `saves/post_ch20.ss1` and `saves/post_sootopolis_arrival.ss1` (2026-08-24)

`--driver ch20chapter` with `CH20_CAPTURE=post_ch20.ss1` snapshots at `ACCEPTANCE: PASS`. ⛔ It writes
**only** on `passed`, which already means arrived + controllable + surfing on the launch tile + a real
`calculate_path` proving open ocean — so **the file's existence IS the acceptance record.**
Verified with `probe_anchor_inventory.py` (never the driver's log — playbook §2b):

```
  post_ch20.ss1   badges=1234567   OVERWORLD   ROUTE128 (38,24)
  ROUTE128_STATE=2   SOOTOPOLIS_CITY_STATE=1   SKY_PILLAR_STATE=0   RAYQUAZA_CRY_DONE=0
```
✅ **`SOOTOPOLIS_CITY_STATE == 1` MEASURED — this is Ch21's entry condition, live.** Room 9 really does
set it in the same block as `ROUTE128_STATE`; that was a decomp claim until this anchor.
⚠ **CAVEAT THE PROBE CAUGHT AND THE DRIVER DID NOT:** *"HP 548/687 (80%), 1 FAINTED — CANNOT SURVIVE A
JOURNEY."* That is the bot's HONEST post-cavern state, so it is a faithful fixture, **but a Ch21 leg
started from it can whiteout early.** ⛔ Do not read such a whiteout as a Ch21 bug — heal first, or
treat the heal as leg 0.

### ⚠ MIXED — what was CLOSED on 2026-08-24, and what is STILL OPEN

*(A heading is a claim about every bullet beneath it. This one said "STILL OPEN" while two of its
bullets had been CLOSED the same day — each bullet now carries its own marker.)*

* ❓ **Which ROUTE126 tile to dive on.** 1,349 qualify; `(45,66)` is adjacent to the warp column and
  is the obvious candidate, but ⛔ **KI-72 says never let the planner choose** — assert the tile type
  before `dive()`.
* ❓ **Where you EMERGE in Sootopolis.** Emerge keeps (x,y), but underwater is (20,10) and the city is
  (60,60), so only the city's top-left 20x10 is reachable by surfacing. Which tile is water — and
  whether the arrival scene fires from it — is unmeasured.
* ✅ **CLOSED 2026-08-24 — the CLEAN-layout interior.** `probe_ch21_topology.py` still cannot answer
  it (`get_map_data` returns the header's DEFAULT layout), but the DECOMP's own
  `data/layouts/SkyPillar_*_Clean/map.bin` IS the story layout, so decoding those collision bits
  answers it exactly. ⇒ **WHEN AN INSTRUMENT CANNOT SEE A MAP, CHECK WHETHER THE SOURCE DATA CAN BE
  READ DIRECTLY BEFORE CALLING THE QUESTION "NEEDS A LIVE RUN".** Results in the staircase table above.
* ❓ **The exact fall-launch approach on 4F.** We know `(5,4)` is reachable from `(11,1)` and is
  adjacent to the cracked `(6,4)`; the step ordering and the ~80-frame fall script are unmeasured live.
* ⚠ **`1F`'s exit to the Outside is a `MB_SOUTH_ARROW_WARP`** — `TryArrowWarp` requires the direction
  to be **HELD**, so a single tap will NOT warp. Relevant on the way back down.
* ✅ **CLOSED 2026-08-24: `VISITED_PACIFIDLOG_TOWN` is False** (and so is `VISITED_SOOTOPOLIS_CITY`).
  The Fly-vs-swim choice is settled — **it is SWIM**, and it was settled by a 20-second flag read
  rather than the live drive this line originally demanded.
* ❓ Whether the Route 126 to Sootopolis warp is itself event-gated.
