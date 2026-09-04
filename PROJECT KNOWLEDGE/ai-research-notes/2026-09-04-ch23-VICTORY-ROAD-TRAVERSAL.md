# §Ch23 — VICTORY ROAD TRAVERSAL RECON (2026-09-04)

> ⛔ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md` before acting on anything here. On
> any contradiction with an authoritative doc, **the authoritative doc WINS** until the note is
> verified. Claims below are tagged **READ** (an agent read the decomp file), **MODELED** (derived by
> an agent's own collision simulator — *not* a decomp fact), or **OURS** (measured in our harness).

**Provenance.** Three independent Claude agents, given deliberately different angles: (1) decomp
recon of the B1F boulders, (2) an **adversarial** brief told to REFUTE "the B1F Strength puzzle is
mandatory", (3) a routing/warp-graph pass. They did not see each other's work.

⚠ **THEY AGREE — AND AGREEMENT IS NOT A CONFIDENCE SIGNAL** (this project has MEASURED that: where
two model generations agreed they were still wrong ~35% of the time). Agreement is why the *object
positions* below are worth trusting — those are READs of `map.json`, and this project grades model
**names** highly. It is **not** a reason to trust the MODELED reachability. See §7.

---

## 1. ⭐⭐ THE HEADLINE: THE ROUTE IS `1F → B1F → B2F → B1F → 1F`

**1F's entrance and its exit are in DIFFERENT walk-regions.** (MODELED, agents 2+3 independently)
1F splits into `{entrance (15,40), ladder (9,14)}`, `{ladder (21,32), exit (39,5)}`, and a dead-end
alcove `{(42,38)}`. ⇒ **there is no 1F path from entrance to exit.** You must descend and resurface.

⇒ Any plan of the shape "walk across 1F to the League exit" is impossible. This is the single most
important routing fact in the chapter.

## 2. THE WARP GRAPH (READ — `data/maps/VictoryRoad_*/map.json`)

`dest_warp_id` is a 0-based index into the destination map's `warp_events`.

| map | id | (x,y) | → dest | lands at |
|---|---|---|---|---|
| **1F** (46×45) | 0 | **(15,40)** | EVER_GRANDE_CITY | (18,41) |
| | 1 | **(39,5)** | EVER_GRANDE_CITY | (18,27) — **THE LEAGUE EXIT** |
| | 2 | (21,32) | B1F | (20,21) |
| | 3 | (42,38) | B1F | (42,25) |
| | 4 | **(9,14)** | B1F | **(8,3)** |
| **B1F** (46×31) | 0 | (30,25) | B2F | (30,25) |
| | 1 | (17,16) | B2F | (19,12) |
| | 2 | (42,25) | 1F | (42,38) |
| | 3 | (42,2) | B2F | (43,2) |
| | 4 | (8,3) | 1F | (9,14) |
| | 5 | (20,21) | 1F | (21,32) |
| | 6 | (5,26) | B2F | (5,26) |
| **B2F** (46×31) | 0/1/2/3 | (30,25)/(43,2)/(19,12)/(5,26) | B1F | reciprocal |

✅ **CONFIRMS OURS:** our measured `1F (9,14)` ladder and `(9,15)` apron are right, and the ladder
lands at **B1F (8,3)** — a value we did not have. *(Agent 3 adds that `(8,14)` also works as an
apron.)* Our measured `calculate_path(1F (15,40) → 1F (9,14)) = 44 wp` **matches agent 3's
independently-solved 44-step route** — the strongest corroboration in this note.

**NO ONE-WAY DROPS.** All 11 internal warps are `MB_LADDER` in 7 reciprocal pairs; zero `MB_JUMP_*`
ledges or floor holes anywhere in Victory Road. (MODELED census, agent 3.) The only one-way-ness is
B2F's waterfalls.

## 3. ⛔⛔ THE HM SET: `{Surf, Strength, Rock Smash}` — **NOT Waterfall, NOT Flash**

Agent 2 ran all 16 subsets of {Surf, Waterfall, Strength, Rock Smash} over the real collision data:
**the unique minimal sufficient set is `{Surf, Strength, Rock Smash}`.** Drop any one ⇒ the exit is
unreachable.

- **Strength** — `EventScript_StrengthBoulder` gates on `FLAG_BADGE04_GET` + `checkpartymove
  MOVE_STRENGTH`. (READ)
- **Rock Smash** — `EventScript_RockSmash` gates on `FLAG_BADGE03_GET` + `MOVE_ROCK_SMASH`. (READ)
- **Surf** — B2F holds a **256-tile water body**; B1F has **zero** water metatiles. (READ/MODELED)
- ⛔ **WATERFALL IS *NOT* REQUIRED, and the mechanism was proven rather than asserted.** The route
  rides the B2F waterfall **downward**, and `sForcedMovementTestFuncs[14] = MetatileBehavior_Is
  Waterfall` → `ForcedMovement_PushedSouthByCurrent` pushes you south **with no badge and no HM
  check**. The HM gate applies only going UP (`GetInteractedWaterScript` requires `FLAG_BADGE08_GET
  && IsPlayerSurfingNorth()`). (READ) ‼ Agent 2 flagged this as **the single point where a
  misreading flips the answer** — if descent were gated, the set would include Waterfall.
- ⛔ **FLASH IS *NOT* A GATE — the widely-held belief is refuted.** `B1F`/`B2F` have
  `"requires_flash": true` but `1F` does **not**. That field only feeds `SetDefaultFlashLevel` →
  `flashLevel` → the darkness-window *rendering*. Without Flash you get radius 24, not black.
  **It gates no collision, no warp, no script.** (READ) ⇒ a bot can traverse Victory Road blind.

## 4. ⭐⭐ THE B1F PUZZLE — TWO BOULDERS, AND A DELETION-MODEL ROUTER MISSES ONE

**All 8 boulders and all 6 rocks in Victory Road are on B1F.** 1F and B2F have zero of either. (READ)

**REQUIRED FOR TRAVERSAL from (8,3) to the B2F ladder (30,25)** — agents 1 and 2 agree, by two
different simulators:
- **Boulder `FLAG_TEMP_11` @ (4,7)** — push **WEST** (stand at (5,7))
- **Boulder `FLAG_TEMP_12` @ (9,10)** — push **EAST** (stand at (8,10))
- **Rock `FLAG_TEMP_1B` @ (18,12)** — Rock Smash; the unique 1-rock solution

⛔⛔ **THE TRAP A NAIVE PATHFINDER FALLS INTO.** A "could I path if the boulder were *deleted*" model
says only **(9,10)** is a cut, and **that is wrong**. (9,10) can only be pushed EAST, which requires
standing at (8,10) — reachable *only* through the west corridor that boulder **(4,7)** blocks. ⇒
**both are mandatory, and a deletion-model router misses (4,7) entirely.**

⛔⛔ **TWO PUSHES KILL THE ROUTE IRREVERSIBLY — and they are exactly what a greedy "push toward the
goal" router does:**

| push | result |
|---|---|
| (4,7) **SOUTH** | (30,25) **unreachable** |
| (9,10) **SOUTH** | (30,25) **unreachable** |
| (4,7) WEST | ✅ safe |
| (9,10) EAST | ✅ safe |

Recovery from a trap push = **leave B1F and re-enter** (see §5.1). Not fatal, but the router must
never choose a direction by "which way is the goal".

**NOT on the required path** (items only): (20,5)/(21,4)/(19,5)/(20,4) gate the *other* 1F ladder;
(35,6)/(34,4)/(34,3) gate the Full Restore at (32,3); the (20,25)/(21,25)/(20,26)/(21,26) cluster is
on the **return** leg. TM29 Psychic (42,8) is on an island unreachable from (8,3) at any cost.

## 5. ‼ FOUR MECHANICS THAT WILL BITE THE BOT (all READ — these are the buildable facts)

1. ⭐⭐ **EVERY WARP RESETS THE ENTIRE PUZZLE.** `LoadMapFromWarp` → `LoadObjEventTemplatesFrom
   Header()` re-copies templates from ROM, and `ClearTempFieldEventData()` wipes `FLAG_TEMP_*`. ⇒
   **boulders revert to their map.json coordinates and smashed rocks respawn on EVERY entry to
   B1F.** The route must be re-solved each visit — and this is also the recovery path from a trap
   push. ⛔ Never cache "the puzzle is solved" across a warp.
2. ⭐⭐ **`FLAG_SYS_USE_STRENGTH` IS CLEARED ON EVERY MAP LOAD** (`event_data.c:45`). ⇒ **Strength
   must be re-activated after each ladder transition.** Do not cache "Strength is on".
3. ⛔ **THE PLAYER DOES NOT ADVANCE WHEN PUSHING.** `PushBoulder_Move` gives the player
   `GetWalkInPlaceNormalMovementAction` and the boulder `GetWalkSlowMovementAction`. ⇒ one input =
   the boulder moves one tile, **the player stays put**; advancing takes a second input. Any
   input-count model is off by one per push.
4. ⚠ **SMASHING (18,12) CAN START A WILD BATTLE** — `EventScript_SmashRock` runs `special
   RockSmashWildEncounter` and B1F has a `rock_smash_mons` table (Geodude/Graveler 30–40). Guard it.

## 6. TRAINERS WITH LINE OF SIGHT ON THE ROUTE (READ positions, MODELED intersection)

**Five forced battles, in order: Hope (1F), Samuel (B1F), Julie (B2F), Halle (B1F), Edgar (1F).**
LOS is a straight line in the facing direction, distance 1..range, blocked by collision
(`trainer_see.c:327-400`); `FACE_X_AND_Y` movement types **alternate** — treat both directions live.

| map | trainer | (x,y) | faces | range | fires at |
|---|---|---|---|---|---|
| 1F | **Hope** | (6,15) | LEFT | 4 | (3,15) |
| 1F | **Edgar** | (33,22) | DOWN | 3 | (33,23) |
| B1F | **Samuel** | (37,12) | LEFT | 3 | (34,12) |
| B1F | **Halle** | (14,20) | UP+RIGHT | 3 | (16,20),(15,20) |
| B2F | **Julie** | (35,22) | LEFT | 2 | (33,22) |

⇒ the navigator must treat these as EXPECTED, not as a derail.

## 6b. ✅✅ LIVE VERIFICATION — RUN 2026-09-04, `--driver ch23b1fprobe` (OBSERVE ONLY)

⭐⭐ **THE LOAD-BEARING CLAIMS ARE NO LONGER MODELED. They were measured against OUR planner and the
GAME'S OWN live object list**, from `post_wally.ss1`, one step onto the ladder. `battles=0`,
`whiteouts=0`, all six readings taken.

| claim (3 agents, MODELED) | live measurement | verdict |
|---|---|---|
| 1F (9,14) ladder lands at B1F **(8,3)** | `arrived_on = ((24,44), (8,3))` | ✅ |
| boulders at **(4,7)** and **(9,10)**, rock at **(18,12)** | live objects: `local_id 3 @ (4,7)`, `local_id 4 @ (9,10)`, `local_id 10 @ (18,12)` | ✅ exact — ⚠ but see the window caveat below |
| (30,25) is UNREACHABLE with the boulders in place | `PathFindingError (8,3) -> (30,25)` | ✅ |
| (5,7) — the tile you stand on to push (4,7) WEST — is reachable | **9 waypoints** | ✅ |
| ⭐ **(8,10) is gated BEHIND boulder (4,7)** | `PathFindingError (8,3) -> (8,10)` | ✅✅ |

⛔⛔ **AND A CAVEAT ON THAT OBJECT ROW THAT I ALMOST SHIPPED AS A COMPLETENESS CLAIM.**
`get_map_objects()` is a **CAMERA-RANGE WINDOW**, not a map census: an object further than roughly a
screen away is **absent from the list whether or not it exists**. The agents say B1F carries **8
boulders and 6 rocks**; this probe, standing at (8,3), saw **three**. ⇒ **THE THREE IT SAW ARE
CONFIRMED PRESENT AT THE NAMED TILES WITH THE NAMED `local_id`s — AND THE ABSENCE OF THE OTHER
ELEVEN IS NOT EVIDENCE OF ANYTHING.** ‼ *(This project has paid for that read three times: the §Ch21
"ZERO NPCs loaded" misread, the (31,18) Expert claim, and leg 2b's Wallace check from (9,3).)*
⇒ what is established is exactly the critical-path subset; enumerating the full 14 would need reads
from several standpoints, and nothing here needs that. ‼ Note also `MapLocation.objects` is the ROM
**template** (ORIGINAL positions) — never mix it with the live list.

### ✅✅ AND THE PREREQUISITE THAT COULD HAVE BLOCKED EVERYTHING IS ALREADY SATISFIED

`EventScript_StrengthBoulder` gates on `FLAG_BADGE04_GET` **and** `checkpartymove MOVE_STRENGTH`, so
a party that cannot use Strength makes every route conclusion here unreachable in practice. Measured
the same run:

| prerequisite | live reading |
|---|---|
| party knows **Strength** | ✅ `True` |
| party knows **Rock Smash** | ✅ `True` |
| party knows **Surf** | ✅ `True` |
| HM04 in the bag | ✅ present (`HM02, HM03, HM04, HM06, HM07, HM08`) |

⇒ **THE WHOLE MINIMAL HM SET `{Surf, Strength, Rock Smash}` IS ALREADY ON THE PARTY. Leg 6 needs NO
teaching step** — `ensure_strength_learner()` exists but is not required here.

‼ **AND IT CORRECTS AN EARLIER READING OF OUR OWN.** A §Ch23 note recorded `FULL BAG: {'Nugget': 1,
'X Attack': 2, 'Potion': 1, 'Escape Rope': 1}` — that was **one pocket**, not the bag. The TM/HM
pocket holds **15** entries. ⇒ had leg 6 checked "is HM04 in the bag" against that reading it would
have found a **false blocker** and gone looking for a Strength teach that was never needed.
⛔ **A POCKET IS NOT A BAG** — name the pocket you read.
*(⚠ The probe's `badges` reading returns `None`: that accessor is wrong, not the save. Badge count
comes from `probe_anchor_inventory`, which reports **badges=12345678** for every §Ch23 fixture.)*

⇒ **THE ORDERING CONSTRAINT IS REAL AND OUR PLANNER SEES IT.** (8,10) is the only tile from which
(9,10) can be pushed EAST, and it is unreachable until (4,7) moves. This is precisely the claim the
adversarial agent said a *"delete the boulder and re-path"* model would MISS — and our own
`calculate_path`, which does model boulders as dynamic obstacles via `active_objects`, independently
agrees. ⇒ **`strength_push` has real `local_id`s to track: 3, 4 and 10.**

‼ **THE PROBE'S OWN FIRST RUN WAS WRONG, AND IT MATTERS HOW.** It reported three confident
`PathFindingError`s that were **vacuous** — `_walk_through_warp`'s second argument is the map you are
**LEAVING**, not the destination, so passing the destination made its `while` condition false
immediately: it pressed nothing, raised nothing, and returned "successfully" while the bot stood
still on 1F. The path queries then asked about 1F tiles *labelled* B1F. ⛔ **A no-op that cannot
raise is the same shape as a fault arm that cannot fire.** The probe now refuses to take any path
reading unless it is actually on B1F — **a MISSING reading is honest; a VACUOUS one is a lie with a
number on it** — and the `on_b1f` grade is what caught it.

## 7. ⛔ WHAT MUST BE VALIDATED LIVE BEFORE ANY BOULDER CODE SHIPS

Everything in §1, §4 and the routes is **MODELED** — a reimplementation of pokeemerald's collision
rules, not the engine. ‼ Agent 1 reports its simulator **found and corrected one of its own bugs
mid-run** (it propagated elevation with `me or e`, silently swallowing elevation-0 transition tiles
and cutting reachability 301 → 106 tiles). That is exactly the class of error that could still be
hiding.

**The three cheap decisive live checks** (also `2026-09-03-...-B1F-B2F.md` §F's owed checks):
1. ⚠ **HALF DONE.** (5,7) is confirmed REACHABLE (9 wp) and (8,10) confirmed UNREACHABLE — see §6b.
   ⛔ **STILL OWED: the PUSH itself** — push (4,7) WEST and confirm the corridor to (8,10) opens.
2. ⛔ **STILL OWED.** Deliberately push **(9,10) SOUTH** once and confirm (30,25) becomes
   unreachable — **this arm is what makes the "trap push" claim real rather than asserted.** Without
   it we have a warning we have never seen fire. ⭐ Safe to run: **every warp resets the puzzle**
   (§5.1), so leaving and re-entering B1F recovers it.
3. ⚠ **HALF DONE.** The "fails with the boulders in place" half is MEASURED (§6b). ⛔ **STILL OWED:
   that it SUCCEEDS after the two pushes** — that half is the one that proves the plan works, and
   an A/B with only its negative arm run is not an A/B.

✅ **ALREADY VERIFIED IN OUR CODE (2026-09-04):** `strength_push(map, approach_tile, face_dir)` exists
at `early_game.py:7884`, tracks the boulder by **`local_id`**, requires **both** halves of success
(left its tile AND arrived at the destination), bounds its attempts, and is exercised on the Magma
Hideout puzzle (`MAGMA_HIDEOUT_1F_PUSHES`). `map_path.py:808-854` already models pushed boulders as
dynamic obstacles via `active_objects`. ⇒ **the machinery exists; what is missing is the route.**

## 8. ⚠⚠ A TOOLING TRAP — TWO AGENTS HIT IT INDEPENDENTLY

**`gh api <repo>/contents/<path> --jq .content | base64 -d` SILENTLY CORRUPTS BINARY FILES ON
WINDOWS.** It round-trips through a UTF-16→UTF-8 conversion: B1F's 2852-byte `map.bin` decoded to
3942 bytes, 1F's 4140-byte file to 5756. **No error is raised.** Both agents initially analysed
garbage.

⇒ **Fetch binaries from `raw.githubusercontent.com` instead, and VERIFY `len == width * height * 2`
before trusting a single byte of a layout.** That length check is what caught it both times.

## 9. ⚠ TWO CORRECTIONS TO ASSUMPTIONS WE HELD

1. ⛔ **(15,40) and (39,5) are `MB_SOUTH_ARROW_WARP`, not step-on warps.** `TryArrowWarp` fires only
   when the player **stands on the tile, faces South, and holds Down**. ⇒ pathing to the tile is only
   half the action. ‼ **Corollary hazard:** arriving at (15,40) from Ever Grande leaves you *standing
   on the exit tile* — a stray Down press warps you straight back out. (READ, agent 3.)
   ⚠ **This one CONFLICTS with how our leg 5 currently enters** (`_walk_through_warp` north onto
   (18,41)). That entry works — it is the EG-side door, a different warp. But the 1F **exit** at
   (39,5) will need the hold-Down treatment. **VERIFY BEFORE BUILDING LEG 8.**
2. ✅ **Wally's trigger is UNAVOIDABLE, which confirms our design.** With both (2,23) and (3,23)
   blocked, (9,14) is unreachable from (15,40) — column x=3 is the only corridor north. ⇒ **do not
   build a route that dodges him; plan to fight.** Both triggers are `coord_events` at elevation 4
   gated on `VAR_VICTORY_ROAD_1F_STATE == 0`, so **re-entry behaviour differs once that var moves.**

## 10. B1F-vs-1F EXP — OUR NUMBERS CORROBORATED, NOT VERIFIED

Our measured **B1F 950.8 vs 1F 775.6 EXP/battle** is not directly checkable from decomp data, but the
encounter tables move the right way: 1F land avg level **37.67** with a Zubat/Whismur low tail; B1F
**40.00** and Lairon-heavy (far higher base EXP). Ratio 1.226 is plausible for that shift. B2F is avg
**42.00**. ⇒ nothing contradicts our numbers. (READ tables, agent 1.)

⛔ **AND IT REMAINS TRUE THAT B1F IS GATED BEHIND WALLY** — which is why the 2026-09-04 training leg
grinds on 1F at 775.6 despite B1F being better ground.
