# §Ch21 LEG 2 BUILD SPEC — recon workflow output (2026-08-26)

> ‼ PROVENANCE: produced by a 9-agent workflow (4 recon angles, each ATTACKED by an adversarial
> verifier, then synthesised under the rule that only SURVIVING claims may appear as facts).
> Per the standing rule this is a NOTE, not truth — but its evidence standard is stated per row
> and its live-probe gaps are marked ❓ rather than filled in.
> ⛔ PARKED 2026-08-26: the USER redirected priorities to three PRODUCTION defects observed in real
> testing (see `03-PUNCH-LIST.md` `#26-*` items). Build leg 2 from THIS spec when the arc resumes.

# §Ch21 LEG 2 — BUILD SPEC

**Scope:** SOOTOPOLIS_CITY (state 2, post-arrival) → Steven's escort → Cave of Origin → Wallace → `VAR_SOOTOPOLIS_CITY_STATE = 3`.
**Fixture:** `saves/post_sootopolis_arrival.ss1` — SOOTOPOLIS_CITY (29,53), surfing, controllable, state 2, badges 1-7.

**Evidence standard used here.** A coordinate or behaviour appears as a fact only if it was decomp-quoted AND survived its adversarial verifier, or if I re-read it in this repo myself (marked `[I READ THIS]`). Reachability numbers from the four recon angles are **three independent re-implementations of the bot's tile model, not the bot's own `calculate_path`** — they agree to the tile, which is corroboration, not measurement (this project's own rule: agreement is not a confidence signal). Every such number is marked `❓ NEEDS A LIVE PROBE` where the build depends on it.

**Answer to Q5 up front, because it structures the steps: leg 2 is TWO legs.** Seam at the escort warp. Full argument in §5.

---

## 0. CODE CHANGES REQUIRED BEFORE ANY OF THIS RUNS

### 0.1 The heal is impossible today — one-line gap

`[I READ THIS]` `sandbox-pokebot/modules/modes/util/higher_level_actions.py:317`:

```python
def heal_in_pokemon_center(pokemon_center_door_location: PokemonCenter) -> Generator:
```

It dereferences `.value[0]`/`.value[1]` and does an identity test `if pokemon_center_door_location is PokemonCenter.PalletTown:` — it demands an **enum member**, not a map+coord.

`[I READ THIS]` `sandbox-pokebot/modules/map_data.py:1524-1554` — I read the whole enum. RSE block runs `OldaleTown` (1525) to `PacifidlogTown = (MapRSE.PACIFIDLOG_TOWN, (8, 15))` (1538); FRLG from 1540. `sed -n '1524,1555p' modules/map_data.py | grep -c 'Sootopolis'` → **`0`**. Scope of that null: the entire enum body plus its `__repr__`.

**Add, after `PacifidlogTown`:**

```python
    SootopolisCity = (MapRSE.SOOTOPOLIS_CITY, (43, 31))
```

(43,31) is decomp-verified as the PC door — `data/maps/SootopolisCity/map.json` warp_events: `{'x': 43, 'y': 31, 'elevation': 0, 'dest_map': 'MAP_SOOTOPOLIS_CITY_POKEMON_CENTER_1F', 'dest_warp_id': '0'}` — **and** it is the one tile on this leg that has a **live** `calculate_path` measurement: `tools/story-dev/story_harness.py:8710` `p_ = calculate_path((MapRSE.SOOTOPOLIS_CITY, at), (MapRSE.SOOTOPOLIS_CITY, (43, 31)))`, which the brief reports as OK, 38 waypoints. A verifier also checked the convention against every other RSE member (Mossdeep (28,16), Pacifidlog (8,15), Lilycove (24,14) are each exactly the city-side PC warp tile), so the value is convention-exact, not a guess.

### 0.2 Interior tiles are safe (verified, not assumed)

`heal_in_pokemon_center` hard-codes `(7,4)` (nurse), `(7,7)`/`(7,8)` (exit). A verifier ran the diff the original report admitted it had not: `SootopolisCity_PokemonCenter_1F/map.json` and `MossdeepCity_PokemonCenter_1F/map.json` both carry `"layout": "LAYOUT_POKEMON_CENTER_1F"`, nurse at `(7,2)`, warps `[(7,8), (6,8), (1,6)]` — **identical on every hard-coded tile**, and neither map has an object_event on (7,4)/(7,7)/(7,8). `MapRSE.SOOTOPOLIS_CITY_POKEMON_CENTER_1F = (15, 2)` already exists.

### 0.3 Not a blocker, fix alongside

`modules/modes/util/map.py` has no `SOOTOPOLIS_CITY` row in `_closest_pokemon_centers` (`grep -c SOOTOPOLIS` → 0 over all 119 lines `[I READ THIS]`). A verifier established `find_closest_pokemon_center` has **zero callers under `modules/story/` or `plugins/custom_modes/`** — it is reachable only from `ev_train` and `pokecenter_loop`. Latent inconsistency, not a leg-2 blocker. Do not spend leg-2 effort on it.

### 0.4 Doc corrections owed in the same commit

Two places in the tree state a cause that this dossier has now **determined**, and they state it wrongly:

- `tools/story-dev/story_harness.py` (~:8694-8712) `[I READ THIS]`, verbatim: *"THE EXPERT BODY-BLOCK REMAINS THE LEADING EXPLANATION"* and *"why the planner refuses is undetermined (likely an elevation-transition rule on the dismount)"* and *"the door's land island is 52 tiles and TOUCHES WATER in both the LegendsBattle and Normal layouts"*.
- `PROJECT KNOWLEDGE/12-STORYMODE-DESIGN.md:3657-3659`, verbatim (quoted by two agents): *"why the planner refuses is UNDETERMINED (likely an elevation-transition rule)."*

Both are refuted by §3.4 below. Two independent BFS re-implementations measured the Expert alone cutting **at most three** tiles of a **seven**-tile refusal, and both measured the door's land component at **~350 tiles**, not 52. Correcting these is a P2/P4 obligation, not optional tidying — a future agent skims them and acts.

---

## 1. LEG 2, STEP BY STEP

Notation: `MAP (x,y)` — coordinate provenance is stated per row. Direction names are the **bot's** (`ensure_facing_direction`), which map to the game's `VAR_FACING` as: `"Left"` = DIR_WEST, `"Up"` = DIR_NORTH.

### LEG 2a — Steven's escort

---

**Step 0 — PREFLIGHT. No movement. Refuse loudly here rather than deep in a cutscene.**

Model it on the existing `sootopolis.assert_ch21_preflight()` (`modules/story/sootopolis.py:87` `[I READ THIS]`).

| Check | Why |
|---|---|
| map is `MapRSE.SOOTOPOLIS_CITY`, avatar controllable | baseline |
| `get_event_var("SOOTOPOLIS_CITY_STATE") == 2` | the arrival cutscene is finished; state 1 means it is still running |
| `get_event_flag("STEVEN_GUIDES_TO_CAVE_OF_ORIGIN") is False` | **the escort can only ever fire once** — see §3.1 |
| `get_event_flag("HIDE_SOOTOPOLIS_CITY_STEVEN") is False` | he is spawned |
| snapshot party as `[(pid, species, current_hp, total_hp)]` | assert IDENTITY, never slot or count |

`[I READ THIS]` — the names resolve and the numbers match the decomp exactly. `sandbox-pokebot/modules/data/event_flags/emerald.txt`:
```
255:307 STEVEN_GUIDES_TO_CAVE_OF_ORIGIN
259:311 WALLACE_GOES_TO_SKY_PILLAR
670:820 HIDE_CAVE_OF_ORIGIN_B1F_WALLACE
823:973 HIDE_SOOTOPOLIS_CITY_STEVEN
```
307/311/820/973 = 0x133/0x137/0x334/0x3CD, matching `include/constants/flags.h:333` `#define FLAG_STEVEN_GUIDES_TO_CAVE_OF_ORIGIN 0x133`, `:337 0x137`, `:871 0x334`, `:1024 0x3CD`. `modules/data/event_vars/emerald.txt:95` → `94 SOOTOPOLIS_CITY_STATE`.

⛔ **Run `python tools/story-dev/audit_flag_names.py` before committing.** `[I READ THIS]` `modules/memory.py:336-338`:
```python
def get_event_flag(flag_name: str) -> bool:
    if flag_name not in _event_flags:
        return False
```
A misspelled flag name reads **False forever**, which for `STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` means "the escort has not run" permanently — a silent infinite-retry generator, not an error. (`get_event_var` returns `-1` for an unknown name, which fails loud instead.)

---

**Step 1 — HEAL.**

- Coordinate: `SOOTOPOLIS_CITY (43, 31)` — **SURVIVED**, and live-measured reachable (38 waypoints) from the arrival tile.
- Action: `yield from heal_in_pokemon_center(PokemonCenter.SootopolisCity)` (after §0.1).
- **Assertion:** re-read the party and assert `current_hp == total_hp` **for every PID in the pre-heal snapshot**. Not a count, not a slot index. Corroborate with the existing `mossdeep_gym._usable_pokemon()` (`modules/story/mossdeep_gym.py:325-333`) ≥ 2, following the `seafloor_cavern.py:893-898` precedent that raises below 2.
- Why heal first, and why heal at all — this is not politeness:
  - the brief's fixture state says a party member is **fainted**, and `modules/story/sootopolis.py:141` `[I READ THIS]` already records *"the party arrives here with a fainted member"*;
  - both cave maps the bot must cross carry land encounters at `encounter_rate: 4` — Entrance Zubat L28-35 + Golbat L33-36; 1F Zubat L30-34 + Sableye L30-34 + Golbat L33-36 (`src/data/wild_encounters.json`, band corrected by an adversarial verifier; B1F has **no** encounter table at all);
  - `heal_in_pokemon_center` **returns without asserting anything about HP** — `[I READ THIS]` its tail at `higher_level_actions.py:464-472` terminates on `while stable < 20 and waited < 300:` / `if player_avatar_is_controllable():`, i.e. on controllability alone. The acceptance is yours to write;
  - project context: crossing a cave with a fainted member exercises `handle_fainted_pokemon`, which already has three fixed index-space bugs (KI-18/34/66) and a fourth filed (`#24-faintchooser-fourthspace`). Do not walk into that avoidably.
- ❓ **NEEDS A LIVE PROBE — the tile the bot is standing on when `heal_in_pokemon_center` returns.** Nobody has driven the Sootopolis PC. Do not hard-code a post-heal position; read it and path from it.
- ❓ **NEEDS A LIVE PROBE** — the three PC-piggyback blocks inside `heal_in_pokemon_center` (`higher_level_actions.py:352-441`: rotation deposit, KI-63 slot-freeing, counter withdraw). Nobody has traced them in Sootopolis.

---

**Step 2 — APPROACH STEVEN AND TALK.**

- Steven: `SOOTOPOLIS_CITY (20, 36)`, elevation 3, `MOVEMENT_TYPE_FACE_DOWN`, `movement_range_x/y = 1` (he does not wander), script `SootopolisCity_EventScript_Steven`, flag `FLAG_HIDE_SOOTOPOLIS_CITY_STEVEN`. **SURVIVED** — verbatim from `data/maps/SootopolisCity/map.json` object_events entry 7 of 18; re-enumerated and confirmed by an adversarial verifier as the only Steven-related object on the map. He is **not** repositioned at state 2: the reposition is gated on the escort's own flag (`data/maps/SootopolisCity/scripts.inc:100` `goto_if_set FLAG_STEVEN_GUIDES_TO_CAVE_OF_ORIGIN, SootopolisCity_EventScript_SetEnterCaveOfOriginObjPos`).
- Approach list — **coordinates SURVIVED, bot-reachability ❓**:

```python
STEVEN_TILE = (20, 36)
STEVEN_APPROACHES = [((21, 36), "Left"), ((20, 37), "Up")]   # Left=DIR_WEST, Up=DIR_NORTH
```

Both are `coll=0 elev=3 MB_NORMAL` plain land (decoded independently by three agents). They are the **only two directions the escort script handles** — `data/maps/SootopolisCity/scripts.inc:903-904`, the complete dispatch, the only two lines between `closemessage` and the next `msgbox`:

```
	call_if_eq VAR_FACING, DIR_WEST, SootopolisCity_EventScript_StartWalkToCaveOfOriginWest
	call_if_eq VAR_FACING, DIR_NORTH, SootopolisCity_EventScript_StartWalkToCaveOfOriginNorth
```

There is no DIR_EAST arm, no DIR_SOUTH arm, no default, and the following `applymovement LOCALID_PLAYER, SootopolisCity_Movement_PlayerWalkToCaveOfOrigin` assumes a start-walk already ran. The two arms converge — West opens `walk_left, walk_up ×3, walk_right…`, North opens `walk_up ×4, walk_right…` — verified independently by two agents.

⚠ **The verifiers demoted this from "load-bearing new constraint" to "recorded fact", and they are right**: facing is forced by the act of talking (`src/field_control_avatar.c:143` `playerDirection = GetPlayerFacingDirection();` → `:170` `GetInFrontOfPlayerPosition(&position);` → `:282` `gSpecialVar_Facing = direction;`), and the two unhandled tiles (19,36)/(20,35) measure NOPATH from anywhere reachable at state 2. **You cannot construct the failure.** Keep the explicit facing anyway — it costs one call and removes a dependency on approach topology (a verifier noted (21,37) is at the same distance as (22,36), so arrival facing is *not* guaranteed by topology).

- **Action — use the `space_center._talk_to_the_stair_grunt` pattern, NOT bare `talk_to_npc`.** `[I READ THIS]` `modules/story/space_center.py:240-241`:

```python
STAIR_GRUNT_TILE = (13, 2)
STAIR_GRUNT_APPROACHES = [((12, 2), "Right"), ((13, 3), "Up"), ((14, 2), "Left")]
```
and its body at `:302-322`: `for approach, facing in …` → `_navigate_riding_out(FLOOR_1F, approach, tries=6)` → `wait_until_truly_controllable()` → re-verify the NPC is still there → `ensure_facing_direction(facing)` → `press_button("A")`.

  ‼ **Correction to the dossier that I verified myself, and the builder must not act on the uncorrected version.** The `ourcode` angle claims `talk_to_npc` has "no way to constrain facing". That is imprecise. `[I READ THIS]` `modules/modes/util/higher_level_actions.py:841-842`:
```python
            yield from navigate_to(*nearest_tile, final_facing_direction=Direction.from_string(nearest_tile_facing))
            yield from ensure_facing_direction(nearest_tile_facing)
```
  It **does** force a facing, derived from whichever adjacent tile it picked. And its candidate map at `:814-819` gives `"Up" → (npc_x, npc_y+1)` = (20,37) and `"Left" → (npc_x+1, npc_y)` = (21,36) — i.e. **both of its reachable candidates land on a handled escort branch.** So `talk_to_npc` is not itself a facing hazard here. Its two real problems are: (a) it takes an **integer** `local_object_id` we have only **inferred** (see §4.5); (b) it picks by path length with no caller control (`:831-834`), so a reachability change silently changes the tile and the facing, and nothing is auditable in a log. Prefer the explicit list — it removes the local_id dependency entirely.

- **Assertion before pressing A:** `_npc_is_on(MapRSE.SOOTOPOLIS_CITY, (20, 36))` is True. `[I READ THIS]` `modules/story/space_center.py:247-265` — it uses `get_map_objects()` (live, mutated positions), and its own docstring says why that matters: *"`MapLocation.objects` reads the ROM header and always returns ORIGINAL positions. Mixing those two up is where most of this project's wrong conclusions about rooms have come from."* This assertion is also the **sharpest single discriminator** in the whole dossier (see §4.2) — log its result either way.
- **Assertion after pressing A:** a script engaged within a bounded window, and it is the escort, not the post-escort dialogue. The two are distinguishable: the escort's first line is `msgbox SootopolisCity_Text_InvolvedWithCrisisComeWithMe`; the already-escorted branch is `SootopolisCity_EventScript_StevenHelpWallace` (`scripts.inc:885-888`), which is `msgbox` / `releaseall` / `end` — three frames and control returns with nothing changed. If the flag is still clear and control returned, the A-press missed; retry the next approach.

---

**Step 3 — RIDE THE ESCORT OUT.**

The cutscene, `data/maps/SootopolisCity/scripts.inc:900-923` (**SURVIVED verbatim, all four angles**): three `msgbox … MSGBOX_DEFAULT`, four `applymovement` pairs, a `delay 120`, an `applymovement LOCALID_SOOTOPOLIS_EXPERT, SootopolisCity_Movement_ExpertMoveAside`, then:

```
	setflag FLAG_STEVEN_GUIDES_TO_CAVE_OF_ORIGIN
	applymovement LOCALID_PLAYER, SootopolisCity_Movement_PlayerEnterCaveOfOrigin
	waitmovement 0
	warp MAP_CAVE_OF_ORIGIN_ENTRANCE, 9, 20
	waitstate
	end
```

A verifier closed the one hole nobody had: `asm/macros/event.inc` — `warp`'s macro body reads `.ifb \c @ Only two arguments provided, treat them as a coord pair and use dummy warpId`, so this is **(x=9, y=20)**, not (warpId=9, x=20). Round-trip: `CaveOfOrigin_Entrance/map.json` warp 0 = `{'x': 9, 'y': 20, 'elevation': 3, 'dest_map': 'MAP_SOOTOPOLIS_CITY', 'dest_warp_id': '3'}` and Sootopolis warp 3 = `{'x': 31, 'y': 16, … 'dest_map': 'MAP_CAVE_OF_ORIGIN_ENTRANCE', 'dest_warp_id': '0'}` — self-consistent. **The player lands standing on Entrance (9,20).**

- **Write a new bounded rider `_ride_steven_escort(budget_frames=…)`** modelled on `sootopolis._ride_arrival_scene` (`modules/story/sootopolis.py:109-148` `[I READ THIS]`) with **its guards inverted**:
  - `_check_abort()` as the **first statement of the loop body, outside any try** (the loop-head abort rule, already honoured at `sootopolis.py:135`);
  - button gated exactly as `sootopolis.py:142`: `context.emulator.press_button("A" if is_waiting_for_input() else "B")`. Safe here — the escort contains no menu, so B cannot cancel anything;
  - ⛔ the existing rider **raises** if the run leaves Sootopolis. In leg 2a that is the **success** condition. Invert it: success = `get_event_flag("STEVEN_GUIDES_TO_CAVE_OF_ORIGIN")` **AND** map is `MapRSE.CAVE_OF_ORIGIN_ENTRANCE` **AND** controllable. Failure-to-arrive = raise with flag + map + coords + state in the message.
  - The flag is set **before** the warp (`:918` vs `:921`), so the flag alone is true mid-cutscene. Require all three.
- ❓ **NEEDS A LIVE MEASUREMENT — the frame budget.** Nobody has timed this cutscene. Start with `_ride_arrival_scene`'s 30000 (which raises), and **record the measured frame count from the first drive** so the budget can be set from data rather than superstition.
- ⛔ **Do NOT use `_ride_out_all_scenes` here or anywhere on this leg.** `[I READ THIS]` `modules/story/early_game.py:437-450`:
```python
def _ride_out_all_scenes(*, quiet_frames: int = 600, max_frames: int = 12000) -> Generator:
    …
    while quiet < quiet_frames:
        if total > max_frames:
            break
```
That `break` is **silent** — the caller then proceeds believing the scene rode out. Its two siblings fail loudly (`_wait_until_cutscene_over` raises at 8000 frames, `early_game.py:685-694`; `_ride_arrival_scene` raises at 30000). The silent one is the dangerous one.

---

**Step 4 — LEG 2a ACCEPTANCE.** See §2.

---

### LEG 2b — the Cave of Origin

**Step 5 — LANDING CHECK.**

- `CAVE_OF_ORIGIN_ENTRANCE (9, 20)` — **SURVIVED** (decomp warp semantics, above). `MapRSE.CAVE_OF_ORIGIN_ENTRANCE = (24, 37)` `[I READ THIS]`.
- Assert map + coords + controllable.
- ⛔ (9,20) **is** the warp tile back to Sootopolis (31,16). You are standing on it. Any southward step re-triggers it.
- The Entrance's only map script is one `ON_RESUME` — the entire 8-line file, quoted in full and confirmed verbatim by two agents:
```
CaveOfOrigin_Entrance_MapScripts::
	map_script MAP_SCRIPT_ON_RESUME, CaveOfOrigin_Entrance_OnResume
	.byte 0

CaveOfOrigin_Entrance_OnResume:
	setescapewarp MAP_SOOTOPOLIS_CITY, 31, 17
	end
```
No forced movement, no cutscene, no one-way warp on entering any of the three cave maps. (`CaveOfOrigin_1F/scripts.inc` is 7 lines, one `ON_TRANSITION` whose callee is dead Ruby/Sapphire code — `data/scripts/cave_of_origin.inc:1` is literally `@ All unused / leftover scripts from RS`. `CaveOfOrigin_B1F_MapScripts::` / `.byte 0` — an empty table. All three have `"coord_events": []`.)

**Step 6 — ENTRANCE → 1F.**

- `navigate_to(MapRSE.CAVE_OF_ORIGIN_ENTRANCE, (9, 5))` — **coordinate SURVIVED**, route is a straight 5-wide shaft up x=9 from y=20 to y=5. Two independent BFS runs both returned **15 steps**. (The `adversarial` angle's "76" was refuted: 76 is the corridor's tile count, not a step count.)
- `navigate_to` carries through a terminal warp on its own — `[I READ THIS]` `walking.py:443-447`: `if waypoints[-1].is_warp:` / `destination_map = waypoints[-1].map` / `destination_coordinates = waypoints[-1].coordinates`.
- Wrap in `_navigate_riding_out` (`early_game.py:236`) — encounters are live here.
- **Assertion:** map becomes `MapRSE.CAVE_OF_ORIGIN_1F` (= `(24, 38)`) at **(11,17)**. (Entrance warp 1 → 1F `dest_warp_id "0"` → 1F warp 0 is at (11,17); resolution by `src/overworld.c:603-610` `SetPlayerCoordsFromWarp`, which places the player on the **destination** warp's own coords.)

**Step 7 — 1F → B1F.**

- `navigate_to(MapRSE.CAVE_OF_ORIGIN_1F, (14, 5))` — **coordinate SURVIVED**; route measured at **23 steps**, path list reproduced identically by two agents.
- **Assertion:** map becomes `MapRSE.CAVE_OF_ORIGIN_B1F` at **(9,3)**.
- ⛔ **`MapRSE.CAVE_OF_ORIGIN_B1F = (24, 42)`, NOT (24,39)** `[I READ THIS]` — `CAVE_OF_ORIGIN_UNUSED_RUBY_SAPPHIRE_MAP1/2/3` occupy (24,39)/(24,40)/(24,41) in between. Use the enum member, never a guessed tuple.

**Step 8 — B1F → WALLACE.**

- Wallace: `CAVE_OF_ORIGIN_B1F (9, 13)`, `MOVEMENT_TYPE_FACE_UP`, script `CaveOfOrigin_B1F_EventScript_Wallace`, flag `FLAG_HIDE_CAVE_OF_ORIGIN_B1F_WALLACE`. **SURVIVED** (the only object_event on the map). Talk-triggered only: B1F has an empty map-script table and `"coord_events": []` — both instruments could have seen a trigger and neither did.
- Approach list — **all SURVIVED**, step counts reproduced identically by two agents from the (9,3) arrival:

```python
WALLACE_TILE = (9, 13)
WALLACE_APPROACHES = [((9, 14), "Up"), ((8, 13), "Right"), ((10, 13), "Left")]   # 21 / 19 / 19 steps
```

- ⛔ **(9,12) — the tile directly north of Wallace — is impassable.** Both agents measured NO PATH; the correct cause is a **collision wall** (`metatile 816 coll 1 elev 0`), not elevation. The elevation-2 centre island is real but starts at (9,11)/(8,12)/(10,12). Never put (9,12) in the approach list.
- **B1F has no wild encounters at all** — `MAP_CAVE_OF_ORIGIN_B1F` is absent from `src/data/wild_encounters.json` (scope: a whole-file grep for `CAVE_OF_ORIGIN` returns exactly five map entries — Entrance, 1F, and three `_UNUSED_RUBY_SAPPHIRE_MAP*`).
- **Before pressing A:** `_npc_is_on(MapRSE.CAVE_OF_ORIGIN_B1F, (9, 13))`. If it is **False** and `SOOTOPOLIS_CITY_STATE == 3`, the leg is **already done** — return, do not wait for him (see §3.6: he never respawns).
- `ensure_facing_direction(facing)`, then `press_button("A")`.
- His script opens `lock` / `faceplayer` / `msgbox CaveOfOrigin_B1F_Text_WallaceStory, MSGBOX_DEFAULT`, then the menu.

**Step 9 — ANSWER THE MULTICHOICE. Index 2 = "SKY PILLAR".**

⛔ **Write a bespoke bounded handler. Do NOT call `wait_for_multiple_choice_question(2)`.** Reasons in §3.2.

The facts it must be built on, all **SURVIVED**:

- `data/maps/CaveOfOrigin_B1F/scripts.inc:25-31`:
```
	multichoice 0, 0, MULTI_WHERES_RAYQUAZA, FALSE
	switch VAR_RESULT
	case 0, CaveOfOrigin_B1F_EventScript_AtCaveOfOrigin
	case 1, CaveOfOrigin_B1F_EventScript_AtMtPyre
	case 2, CaveOfOrigin_B1F_EventScript_AtSkyPillar
	case 3, CaveOfOrigin_B1F_EventScript_DontRemember
	goto CaveOfOrigin_B1F_EventScript_DontRemember
```
- Index order — `src/data/script_menu.h:737-743` `{gText_CaveOfOrigin}, {gText_MtPyre}, {gText_SkyPillar}, {gText_DontRemember}` with `src/strings.c:857-860` giving the literal strings. **Index 2 == "SKY PILLAR".**
- **Cursor starts at 0** — plain `multichoice` passes a literal `0` as defaultChoice (`src/script_menu.c:40-50` `DrawMultichoiceMenu(left, top, multichoiceId, ignoreBPress, 0);`), which seeds the cursor at `:109 InitMenuInUpperLeftCornerNormal(windowId, count, cursorPos);`. Index 0 is a **wrong** answer.
- **Wrapping is ON** — `src/script_menu.c:191-194` `if (count > 3)` / `gTasks[taskId].tDoWrap = TRUE;` and count is 4. So Down×2 and Up×2 both reach index 2.
- **The prompt re-arms with a FRESH `multichoice`**, so the cursor **resets to 0** on every loop. Any stray A re-selects index 0 forever.
- **Menu identity:** `include/constants/script_menu.h:121` `#define MULTI_WHERES_RAYQUAZA 110`. Our code already reads that namespace — `[I READ THIS]` `modules/modes/util/tasks_scripts.py:69-70`: *"The choices given can be identified by the 'multichoice ID', which is the 7th value in the multi choice task's data."* and `:78 multi_choice_ids = (17, 20, 94)` (= `MULTI_YESNOINFO`/`_2`/`MULTI_YESNO`).

Handler shape (the in-tree precedent is the Briney sail driver, `modules/story/early_game.py:3528-3547` `[I READ THIS]` — a bounded `while` with `presses > 900 → raise`, a `task_is_active("Task_HandleMultichoiceInput")` branch, a cursor move, then A until the task drops; **that one does not check `data_value(7)` and yours must**):

```
attempts = 0; frames = 0
loop (frames budget → raise):
    _check_abort()                                  # first statement, outside any try
    if get_event_var("SOOTOPOLIS_CITY_STATE") == 3: return          # success
    if task_is_active("Task_HandleMultichoiceInput"):
        assert get_task("Task_HandleMultichoiceInput").data_value(7) == 110   # MULTI_WHERES_RAYQUAZA
        attempts += 1
        if attempts > 3: raise BotModeError(... wrong-answer loop ...)
        wait_for_n_frames(4); press "Down"; wait 2; press "Down"; wait 2
        while task_is_active("Task_HandleMultichoiceInput"): press "A"; yield; wait 2
        continue
    press "A"                                        # advance msgbox only
```

⛔ **The word `"B"` must not appear anywhere in this block** — see §3.2.
⛔ **The loop counter is what distinguishes success from the trap.** The helper's natural exit (task drops) is satisfied by a *wrong* answer too. The only honest exit is `SOOTOPOLIS_CITY_STATE == 3`.

The payoff, `data/maps/CaveOfOrigin_B1F/scripts.inc:49-60` (**SURVIVED verbatim**):
```
CaveOfOrigin_B1F_EventScript_AtSkyPillar::
	msgbox CaveOfOrigin_B1F_Text_WellHeadToSkyPillar, MSGBOX_DEFAULT
	closemessage
	playse SE_EXIT
	fadescreenspeed FADE_TO_BLACK, 4
	setflag FLAG_WALLACE_GOES_TO_SKY_PILLAR
	setvar VAR_SOOTOPOLIS_CITY_STATE, 3
	removeobject LOCALID_CAVE_OF_ORIGIN_WALLACE
	clearflag FLAG_HIDE_SKY_PILLAR_WALLACE
	fadescreen FADE_FROM_BLACK
	release
	end
```
Note: **`release`, no warp.** The bot is left standing on B1F.

**Step 10 — LEG 2b ACCEPTANCE.** See §2.

**Step 11 — BOUNDARY. Do NOT build this into leg 2b.** The climb back out (B1F (9,3) → 1F (11,17)... wait, B1F warp is at (9,3) → 1F (14,5); 1F (11,17) → Entrance (9,5); Entrance (9,20) → Sootopolis (31,16)) and, past it, the pocket exit. All intra-cave return routes are measured (B1F (9,14)→(9,3) = 21 steps with Wallace's tile still treated as blocked; 1F return 23; Entrance return 15). **The Sootopolis half is not.** See §3.4 and §5.

---

## 2. THE GRADING PREDICATE

**Leg 2a (the escort) is done when:**

```python
get_event_flag("STEVEN_GUIDES_TO_CAVE_OF_ORIGIN") is True
and _on_map(MapRSE.CAVE_OF_ORIGIN_ENTRANCE)
and player_avatar_is_controllable()
```

Why this and not something else:
- The flag is the **game's own record that the escort happened**, and a whole-repo grep of the extracted decomp tarball (a strictly stronger instrument than GitHub code search, which a verifier caught under-reporting on this very symbol) returns **exactly four references**: the reposition guard `scripts.inc:100`, the escort gate `:876`, the single `setflag` at `:918`, and the `#define`. **There is exactly one writer, and it is the escort itself.**
- ⛔ **Map presence alone is not the predicate.** `setflag` is at `:918` and the `warp` at `:921` — the flag is true for a stretch while the cutscene is still running. And this project already paid for the general form of that lesson: `modules/story/sootopolis.py:118` `[I READ THIS]` — *"⇒ 'we are on the map' is NOT 'we have arrived'. Grade on the VAR, never on the map."* Require all three conjuncts.

**Leg 2b (the cave) is done when:**

```python
get_event_var("SOOTOPOLIS_CITY_STATE") == 3
and get_event_flag("WALLACE_GOES_TO_SKY_PILLAR") is True
```

Why:
- The **VAR is primary**, per the project rule.
- The flag is the corroborating second observable, and it is the one with a **whole-repo-verified single writer**: a tarball-wide grep returns exactly two script references — `setflag FLAG_WALLACE_GOES_TO_SKY_PILLAR` (once, in `AtSkyPillar`) and `call_if_set FLAG_WALLACE_GOES_TO_SKY_PILLAR, SkyPillar_Outside_EventScript_OpenDoor` (once). Both halves are written by the same seven-line block, so disagreement between them is itself a signal that something is wrong with the reading.
- ⛔ **NEVER grade on Wallace's absence.** `_npc_is_on(...(9,13))` returns False in three different worlds: success, "he was never loaded", and "the map is not current". And after success he is gone **permanently** — §3.6.
- ⛔ **NEVER grade leg 2 on `sootopolis.ch21_done()`.** `[I READ THIS]` `modules/story/sootopolis.py:80-84`: *"The WHOLE chapter's grading flag — ⛔ not leg 1's."* → `RECEIVED_HM_WATERFALL`, per `modules/story/chapters.py:249-254` `[I READ THIS]`. That is **three legs past** leg 2 (Sky Pillar climb, Rayquaza, the quelling). Leg 2 has no registry-level grade of its own; `SOOTOPOLIS_CITY_STATE == 3` is the only leg-scoped end-state marker that exists.

---

## 3. HAZARDS

### 3.1 The escort fires exactly ONCE, ever — a retry is a deadlock

`data/maps/SootopolisCity/scripts.inc:876` (**SURVIVED**), sitting **above** all four state branches:
```
	call_if_unset FLAG_STEVEN_GUIDES_TO_CAVE_OF_ORIGIN, SootopolisCity_EventScript_StevenLeadPlayerCaveOfOrigin
```
The callee ends in `end` (`:923`), so control never returns to the branches below. Once the flag is set, talking to Steven runs `SootopolisCity_EventScript_StevenHelpWallace` — `msgbox` / `releaseall` / `end`. **A leg-2a retry loop that re-approaches and re-talks after the flag is set will press A forever against three frames of dialogue.** Hence the Step-0 precondition and the flag-based grade.

### 3.2 The Wallace multichoice: unbounded helper + B cancels into a no-escape loop

`[I READ THIS]` `modules/modes/util/tasks_scripts.py:110-125`, verbatim and complete:
```python
def wait_for_multiple_choice_question(choice_index: int) -> Generator:
    task_name = "Task_MultichoiceMenu_HandleInput" if context.rom.is_frlg else "Task_HandleMultichoiceInput"
    while not task_is_active(task_name):
        …
        yield

    if choice_index > 0:
        yield from wait_for_n_frames(4)
        for _ in range(choice_index):
            context.emulator.press_button("Down")
            yield from wait_for_n_frames(2)

    yield from wait_until_task_is_not_active(task_name, "A")
```
Three defects, all confirmed:
1. **Both loops are unbounded by construction.** The terminator `wait_until_task_is_not_active` (`:33-36`) is `while task_is_active(function_name):` with no counter.
2. **It never checks which menu it is answering.** Its sibling `wait_for_yes_no_question` does — `[I READ THIS]` `:85-89`: `if task.data_value(7) in multi_choice_ids:`. This one does not.
3. **It verifies no outcome.** It returns the instant the task drops — which a *wrong* answer also does, because each wrong branch is `message`/`waitmessage`/`goto` with **no `closemessage` and no `waitbuttonpress`**: the prompt re-arms on its own.

It is also the only `def` in that 161-line file with neither `@debug.track` nor a docstring (nine siblings carry the decorator).

**The B-press hazard:** `multichoice … FALSE` means `ignoreBPress = FALSE`, so B cancels → `gSpecialVar_Result = MULTI_B_PRESSED` = 127 (`include/constants/script_menu.h:8`), which matches no `case 0..3` and falls through the bare `goto CaveOfOrigin_B1F_EventScript_DontRemember` → back to the same prompt.

⛔ **No B-pressing rider may run over this menu.** But note the correction the verifier forced, and use the corrected version: the "guaranteed infinite hang" framing was **REFUTED** — all three riders are bounded (`_ride_out_all_scenes` 12000 with a **silent** `break`, `_wait_until_cutscene_over` 8000 with a raise, `_ride_arrival_scene` 30000 with a raise). The true hazard is **a bounded stall that ends in a wrong outcome, silently in one of the three.** That is worse than a hang for a story bot, because the caller proceeds.

Also relevant `[I READ THIS]` — `_wait_until_cutscene_over` routes A-requests through `_dialogue_button` (`early_game.py:575-590`), whose first line is `if button != "A": return button`. **A "B" request passes straight through ungated.** So the gating that protects other menus does not protect this one.

### 3.3 A misspelled flag name reads False forever

`[I READ THIS]` `modules/memory.py:336-338` — quoted in §Step 0. Run `tools/story-dev/audit_flag_names.py`. This is not hypothetical bookkeeping: `STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` misspelled means "the escort never ran", which is exactly the input a retry loop keys on.

### 3.4 The return trip out of the Cave of Origin is a pathfinding trap

**The mechanism (code-quoted, SURVIVED, and I re-read it):** `[I READ THIS]` `modules/map_path.py:843-853`:
```python
        if tile.dynamic_collision_flag is not None and not get_event_flag_by_number(tile.dynamic_collision_flag):
            if (
                tile.dynamic_object_id is None
                or (tile.map.map_group_and_number, tile.dynamic_object_id) not in active_objects
            ):
                return False
        if (
            tile.dynamic_collision_flag is None
            and tile.dynamic_object_id
            and (tile.map.map_group_and_number, tile.dynamic_object_id) not in active_objects
        ):
            return False
```
and `active_objects` is camera-limited — `:806-811` `for object in get_map_objects():`. **The test is LOADEDNESS, never occupancy.** A flag-visible object that is not currently loaded makes its ROM-template tile impassable.

**And the bot reads ROM templates, never the save-block copy** `setobjectxyperm` writes: `modules/map.py:818-823` (`events_list_pointer = unpack_uint32(self._map_header[0x04:0x08])`) feeding `:990-997`, versus the decomp's `src/event_object_movement.c:1666 struct ObjectEventTemplate *template = &gSaveBlock1Ptr->objectEventTemplates[i];`.

**Consequence, measured by three independent BFS re-implementations that agree to the tile:** Steven's template tile (20,36) plus Boy2's (19,37) form a **two-tile diagonal cut** sealing a ~343-tile north-west pocket. Block both → the whole column (31,16)..(31,22) refuses while (43,31) still reaches. Block **either one alone** → the column fully reopens. The Expert at (31,18) is a *separate* one-tile choke that can cut **at most three** tiles of that column — verified by direct fault injection: `Expert(31,18) → 31,16=X 31,17=X 31,18=X 31,19=R 31,20=R 31,21=R 31,22=R`.

**Why it matters for leg 3, not leg 2:** after the escort, the game moves Steven to (32,18) and the Expert to (30,18), so the gateway is **physically open** — but the bot still blocks (20,36) whenever Steven is not loaded. And `navigate_to` re-plans: `[I READ THIS]` `walking.py:424-438` (`except PathFindingError as e: raise BotModeError(str(e))`) inside a `waypoint_generator()` whose `while not player_is_at(...)` re-enters, plus the outer `while True:` at `:459-463` that restarts a **fresh** generator on `TimedOutTryingToReachWaypointError`. A re-plan taken more than ~9 tiles from Steven refuses.

⚠ **State the claim honestly.** The verifier refuted "leg 2 ends by stranding the bot" as a **prediction, not a measurement** — the *first* plan out of the pocket is made while Steven is loaded at (32,18), so it routes fine, and the walk completes if nothing forces a re-plan. What is measured is: *a re-plan from inside the pocket refuses*. Do not write the stronger sentence into the code comments.

⛔ **And do not "fix" this by closing the underlying defect as working-as-intended.** The rule produces the correct answer at state 2 only by coincidence (Steven really is standing on his template tile). The same rule produces a **false** block on an empty tile after the escort.

### 3.5 `setmetatile` is invisible to the planner too

Collision comes from ROM layout blockdata (`modules/map.py:772-774` `map_data_pointer = unpack_uint32(self._map_layout[12:16])`), while `setmetatile` writes the RAM map grid. During the crisis, `SootopolisCity_EventScript_LockHouseDoors::` closes nine house doors and `SootopolisCity_EventScript_LockGymDoor::` closes the Gym door — **and the bot models all of them as OPEN.** The Poké Center (43,31) and the Mart (17,29) are in **neither** list, which is why the heal is safe. ⛔ Do not route leg 2 to any house door or the Gym.

### 3.6 Wallace does not respawn on B1F

The `removeobject LOCALID_CAVE_OF_ORIGIN_WALLACE` in the success branch **sets his hide flag permanently**: `src/scrcmd.c:1048-1054 ScrCmd_removeobject` → `RemoveObjectEventByLocalIdAndMap` → `src/event_object_movement.c:1389-1397` `FlagSet(GetObjectEventFlagIdByObjectEventId(objectEventId));`, and 0x334 is far outside the temp range (`TEMP_FLAGS_END FLAG_TEMP_1F`). This **refutes** the `cave` angle's claim 4 and the `adversarial` angle's open item, both of which concluded he respawns from a script-text search that could never have seen a C-side `FlagSet`.

Consequences: a retry that re-enters B1F expecting to find him **waits forever**; and his absence is not evidence of anything. Grade on the VAR.

⚠ This refutation was not itself re-attacked. It does not change the build (the grading rule is the same either way), but if a drive ever shows Wallace back on (9,13) with state 3, the C-path reading is what to re-examine.

### 3.7 (31,18) is not modelled as an obstacle — latent, benign at state 2

The Expert's template carries `"flag": "0"`, so `if map_object.flag_id != 0:` skips the flag record; Wallace's template sits on the **same tile** later in the list and overwrites `tile.dynamic_object_id` (assigned unconditionally on the next line, `map_path.py:438-440` `[I READ THIS]`), while his own hide flag is SET at state 2 — so **neither guard fires and (31,18) reads walkable while a body is standing on it**. Pre-escort you cannot reach it anyway; post-escort the Expert has moved to (30,18), so the model happens to be right. ⚠ **Forward warning for leg 4:** at state 4 Wallace is placed on (31,18) with his hide flag *cleared*, which flips this tile into the opposite regime.

### 3.8 The layout cache — real defect, does not touch leg 2

`modules/map_path.py:488 _maps: dict[...] = {}` / `:502-503 if game_key in _maps: return _maps[game_key]`, with no invalidation anywhere in the file. The game swaps Sootopolis to `LAYOUT_SOOTOPOLIS_CITY_LEGENDS_BATTLE` at states 1-4; the planner reads the **static ROM layout**. Measured diff of the two binaries by two agents independently: **645 blocks differ, of which 28 differ in collision or elevation — all inside x=27..35, y=43..45 (the Groudon/Kyogre arena) plus (49,48).** No leg-2 route touches any of them, and the two-tile cut reproduces identically on **both** layouts. Note it, do not act on it.

---

## 4. OPEN QUESTIONS — with the probe that settles each

All probes are read-only additions to `tools/story-dev/story_harness.py`'s existing `Ch21Dive` runner (which already does exactly this shape at `:8710`/`:8715`), on `saves/post_sootopolis_arrival.ss1`.

**4.1 — Is `FLAG_STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` actually unset on the fixture?** *(all four angles list this as their top unknown; every "Steven is at (20,36)" claim is derived from control flow, never read)*
```python
log(f"[ch21leg2] guides={get_event_flag('STEVEN_GUIDES_TO_CAVE_OF_ORIGIN')} "
    f"hide_steven={get_event_flag('HIDE_SOOTOPOLIS_CITY_STEVEN')} "
    f"state={get_event_var('SOOTOPOLIS_CITY_STATE')}")
```
Expected: `guides=False hide_steven=False state=2`. If `guides=True`, Steven is at (32,18) and leg 2a is already spent — the whole spec changes.

**4.2 — THE DISCRIMINATOR. Is the (31,16)..(31,22) refusal really the Steven/Boy2 body-block?** Run in this exact order:
```python
log([(o.local_id, tuple(o.current_coords)) for o in get_map_objects()])      # from (29,53): expect []
for t in [(20,36), (21,36), (20,37), (19,36), (20,35), (31,22), (31,16), (43,31)]:
    try:    log(f"{t} OK {len(calculate_path((MapRSE.SOOTOPOLIS_CITY, at), (MapRSE.SOOTOPOLIS_CITY, t)))} wp")
    except Exception as e: log(f"{t} {type(e).__name__}")
# then walk to (21,36) and repeat BOTH prints
```
Predicted, from the arrival tile: `(21,36)` OK, `(20,37)` OK, `(43,31)` OK; `(20,36)`, `(19,36)`, `(20,35)`, `(31,22)`, `(31,16)` all refuse. **Then, from (21,36):** `get_map_objects()` now lists Steven at (20,36) and Boy2 at (19,37), **and `calculate_path` to (31,22) now SUCCEEDS.** That flip is the sharpest single discriminator between the body-block explanation and every rival, and it is unrun.
⛔ This also settles §0.4: if the flip happens, the harness comment and `12-STORYMODE-DESIGN.md:3657-3659` must be corrected in the same commit.

**4.3 — Are (21,36)/(20,37) reachable by the bot's own planner?** Covered by 4.2. **This is the first thing leg 2 should measure, before writing any escort code.** Three re-implementations say yes at 25 tile-steps; none of them is `calculate_path`. Note the known divergence: the `steven` agent's model calls the Poké Center door unreachable (`coll=1 elev=0`) while the bot really does path there in 38 waypoints, because of the destination-warp exception at `map_path.py:841` (`elif not tile.accessible_from_direction[from_direction] and not (tile == destination_tile and tile.warps_to):`). **Treat their step counts as topology evidence, never as expected waypoint numbers.**

**4.4 — What facing does the bot actually arrive with at (21,36)?**
```python
yield from navigate_to(MapRSE.SOOTOPOLIS_CITY, (21, 36))
log(f"facing={get_player_avatar().facing_direction} at={tuple(get_player_avatar().local_coordinates)} "
    f"surfing={...}")
```
Two tiles tie at distance 24-25, so arrival facing is not guaranteed by topology. This also answers the unverified sub-question *"does the surf-exit leave a controllable WALKING player on (22,36)?"* — nobody checked.

**4.5 — Steven's numeric `local_id`.** Only needed if you use `talk_to_npc`; the recommended pattern removes the need. It is **INFERRED, not read**: the decomp defines only the symbol `LOCALID_SOOTOPOLIS_STEVEN` (a code search returns exactly one file, `map.json`), and porymap's 1-based list order puts him 7th — which a verifier order-checked but which is still an inference. ⛔ **Do not hard-code 7.** If you need it: from (21,36), `log([(o.local_id, tuple(o.current_coords)) for o in get_map_objects()])` and match on (20,36).

**4.6 — The party's real state.** The brief says *"ONE PARTY MEMBER IS FAINTED at 54% HP"*, which is internally inconsistent (fainted = 0 HP). Do not build on either reading:
```python
log([(m.personality_value, m.species.name, m.current_hp, m.total_hp) for m in get_party()])
```
Assert by PID afterwards, never by slot index or party count.

**4.7 — Where does `heal_in_pokemon_center` leave the bot, and can it path to Steven from there?**
```python
yield from heal_in_pokemon_center(PokemonCenter.SootopolisCity)
here = get_player_location(); log(f"post-heal {here}")
log(calculate_path(here, (MapRSE.SOOTOPOLIS_CITY, (21, 36))))
```
Also confirms the interior tiles (7,4)/(7,7)/(7,8) drive correctly on a map nobody has ever driven, and whether the three PC-piggyback blocks misbehave here.

**4.8 — The escort's frame cost.** Count frames from the A-press to `guides=True AND map==CAVE_OF_ORIGIN_ENTRANCE`. Set the budget from that number, not from a guess. Log the landing coords to confirm (9,20).

**4.9 — Does `Task_HandleMultichoiceInput` actually drop between a wrong answer and the re-arm?** The claim that `wait_until_task_is_not_active` cannot distinguish success from the loop is **reasoned from script text, not traced**. Settle it by fault injection in a throwaway run: deliberately answer index 0 once, and log per-frame `task_is_active("Task_HandleMultichoiceInput")`, `get_task(...).data_value(7)`, and `get_event_var("SOOTOPOLIS_CITY_STATE")`. Expected: the task drops, the message prints, the task returns with `data_value(7) == 110`, and the state never leaves 2. *(Whatever the trace shows, the helper still reads none of `VAR_RESULT`, the state, or the flag — so the bespoke handler is required regardless.)*

**4.10 — Encounter pressure across the cave.** `encounter_rate: 4` is quoted verbatim by two agents, but **nobody read the code that turns it into a per-step probability.** Count actual encounters over the 15 + 23 + 21 = 59-step descent on the first drive. Claim "low rate but real", never a number.

**4.11 — The Sootopolis tile the bot lands on when walking back out.** Decomp-established as **(31,16)** (`CaveOfOrigin_Entrance` warp 0 → `dest_warp_id "3"` → Sootopolis warp 3 at (31,16), resolved by `src/overworld.c:603-610`). ⚠ The `cave` angle misquoted that field as `"0"` and manufactured a false doubt from it; the misquote was refuted and the value is solid. But it has **never been observed live**. It is leg 3's first fact — probe it there.

---

## 5. IS LEG 2 ONE LEG OR TWO?

**TWO. The seam is the escort's `warp MAP_CAVE_OF_ORIGIN_ENTRANCE, 9, 20`.**

- **2a — Steven's escort:** SOOTOPOLIS_CITY → CAVE_OF_ORIGIN_ENTRANCE (9,20). Graded on `FLAG_STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` + map + controllable.
- **2b — the Cave of Origin:** Entrance → 1F → B1F → Wallace → `VAR_SOOTOPOLIS_CITY_STATE == 3`.

Four independent reasons, each from surviving evidence:

1. **It is irreversible and un-repeatable.** `setflag FLAG_STEVEN_GUIDES_TO_CAVE_OF_ORIGIN` sits three lines before the warp, and it is the escort's **only** gate (one writer repo-wide). A single leg that retries from the top after the flag is set deadlocks against three frames of `StevenHelpWallace` dialogue. A leg boundary is exactly where a retry must not cross.
2. **It permanently changes the map.** After the flag, `SootopolisCity_OnTransition` at states 2 and 3 runs `SetEnterCaveOfOriginObjPos` — Expert to (30,18), Steven to (32,18). The city the bot re-enters is not the city it left.
3. **The failure modes are disjoint.** 2a's risks are pathfinding and a facing-sensitive cutscene; 2b's are wild encounters and a no-escape menu. Nothing 2b does can recover a 2a failure, and vice versa.
4. **Testability.** 2b is untestable in isolation without its own fixture. The seam is where that save must be taken: `saves/post_steven_escort.ss1` at CAVE_OF_ORIGIN_ENTRANCE (9,20), flag set, state 2. This matches the chapter file's own enumeration — `modules/story/sootopolis.py:3-5` `[I READ THIS]` lists *"legs 2-5 (Steven's escort, the Cave of Origin, the Sky Pillar climb, HM07 from BOTH Maxie AND Archie)"*, i.e. the escort and the cave were always meant to be separate legs. It also matches §Ch20's stated method, quoted at `sootopolis.py:9-11`: *"incremental drivers that INHERIT: each leg is driven standalone, and the chapter is the ASSEMBLY of proven ingredients."*

**There is a THIRD boundary, and it belongs to leg 3, not to 2b.** The walk back out of the 343-tile pocket (§3.4) is the single largest un-measured risk in this whole area. Keep it out of 2b: **2b ends on B1F with state 3** (or, at most, back at Entrance (9,20), which is the last position reachable without touching the pocket). Leg 3 opens by probing the exit, not by assuming it.

---

## LOW CONFIDENCE — what I could not verify

- **I ran no emulator and no live probe.** Every `❓` above is genuinely open. In particular I did **not** confirm that `calculate_path` reaches (21,36) or (20,37) — the load-bearing precondition of Step 2 — and I did not read the save's flags, vars, party, or item bag.
- **Every reachability number in this spec is a re-implementation, not `calculate_path`.** Three agents wrote three BFS models over the decomp layout binaries and agree to the tile, including a 25-step route reproduced verbatim. Per this project's own measured rule, **agreement is not a confidence signal** — and one of the three demonstrably diverges from the bot on door tiles.
- **§3.6 (Wallace never respawns) rests on one agent's decomp-C reading that was not itself re-attacked.** It does not change the grading rule, which is why I let it stand as a hazard rather than a build dependency.
- **The escort's intermediate coordinates are not claimed by anyone.** One agent's tile-by-tile walk was refuted as a miscount and re-derived by a verifier as touching no colliding tile, both arms converging on (16,8) → (29,21) → (31,18) → (31,16). I have **not** re-derived it and I assert none of those tiles — only the endpoints.
- **I did not verify the bicycle case** (Sootopolis has `"allow_cycling": true`) or whether the escort choreography differs for a cycling avatar. The bot arrives surfing and dismounts to walk, so it should not arise.
- **The "52-tile island / touches water" figure in `story_harness.py` is contradicted by the dossier's ~350-tile land-component measurement, but nobody in the dossier reproduced the 52 itself.** Treat the correction as "the harness comment names an undetermined cause that is now determined", and re-derive the island figure before overwriting it — a broken instrument does not invalidate its past readings.