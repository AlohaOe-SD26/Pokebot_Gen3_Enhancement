# §Ch23 — VICTORY ROAD B1F / B2F: THE FLOORS NOBODY HAD AUDITED

> ‼ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`). Produced 2026-09-03 by a decomp agent
> after the scope-cut retraction put both basement floors on the mandatory path.
> ⭐⭐ **IT HAS SINCE BEEN THROUGH TWO INDEPENDENT ADVERSARIAL PASSES AND MY OWN PROBE, AND THE
> HEADLINE SURVIVED WHILE FIVE SUB-CLAIMS DID NOT.** Everything below is the CORRECTED state; each
> correction says who overturned it. ⛔ **Nothing here is confirmed in the live emulator** — the
> three checks in §F are still owed before code depends on any of it.
> ✅ Byte lengths asserted on every binary by both passes independently: 1F **4140**, B1F **2852**,
> B2F **2852**, general attributes **1024**, cave attributes **828**.

---

## §0. ⛔⛔ THE HEADLINE — IT SURVIVED, BUT THE MECHANISM UNDER IT WAS WRONG

**Two first pushes seal Victory Road B1F for that visit.** An exhaustive Sokoban over the full state
space (player position + carried elevation × 8 boulders × 6 rock states) confirms it, and an
INDEPENDENT re-implementation forced every legal first push and reproduced exactly three:

```
FIRST = PUSH (4,7)  SOUTH -> (4,8)    ->  SEALED  (ladder unreachable)
FIRST = PUSH (4,7)  WEST  -> (3,7)    ->  solvable, total cost 3
FIRST = PUSH (9,10) SOUTH -> (9,11)   ->  SEALED  (ladder unreachable)
```

⛔⛔ **BUT THREE SUB-CLAIMS IN THE ORIGINAL AUDIT ARE REFUTED, AND ONE OF THEM WOULD HAVE PUT THE
WRONG RULE IN THE CODE:**

1. ⚠ **"Both are available on move one" — TWO PASSES SAID OPPOSITE THINGS AND BOTH WERE RIGHT.** The
   adversarial pass measured **7, 9 and 7 steps of walking** to reach them; the independent solver
   answered *"available at move 1? **YES**"*. They are answering different questions.
   ⇒ **THE PRECISE STATEMENT: each fatal push is available as your FIRST *PUSH* — no other action
   has to happen first to enable it — though you must walk ~7-9 tiles to stand there.** Say it this
   way; "on move one" reads as *first button press* and invites a wrong guard.
2. ⛔ **"The boulder can never be gotten behind" is FALSE for (4,7).** The search finds
   `PUSH (4,8) NORTH -> (4,7)` *is* reachable later, by going around through the y=10 corridor.
   ⭐ And the independent solver sharpens the condition: **(4,7)-south is fatal ONLY while the other
   boulder is still at (9,10).** Once that one is safely at (10,10), the same push is survivable —
   you route via the x=9 column instead.
3. ⛔ **"A 1-tile shaft with a wall at the bottom" is FALSE.** (4,8)/(4,9) are one-wide, but
   **(4,10) is a T-junction** (open to the east); same shape at (9,11)/(9,12) with **(9,13) a
   junction**. The walls at (4,11)/(9,14) sit below the *junction*, not below a one-wide shaft.

⭐⭐ **AND THE MOST USEFUL SAFETY FACT EITHER PASS PRODUCED: ONLY PUSHES CAN KILL.** Over the whole
state graph — **186,602 walk edges and 145 smash edges — ZERO cross from live to dead.** Every one of
the 3 fatal edges is a push. ⇒ **the guard belongs on `strength_push` and nowhere else**; the bot
cannot lose this floor by walking badly, by taking a ledge, or by smashing the wrong rock.

### ⭐⭐ THE REAL INVARIANT, AND IT IS THE THING TO ENCODE
**THE FATAL BOULDER IS `(9,10)`.** Pushing it SOUTH walks it down to **(9,13) — the junction tile —
where it blocks the only way east.** Pushing **(4,7) south seals only INDIRECTLY**: it removes the
west route into the y=10 corridor, which forces the sole remaining push on (9,10) to be SOUTH.
Both sealed branches converge on the **same 36 reachable tiles**.
⇒ ⛔ **A bot encoding "a boulder in a shaft means the floor is lost" would model the wrong thing.**
The rule to encode is about **(9,10) never going south**, and about preserving the west route that
keeps (9,10)'s other options open.

✅ **NOT A HARD SOFTLOCK, and this is a direct decomp read:** `ClearTempFieldEventData()`
(`src/event_data.c:39-48`) memsets `TEMP_FLAGS_START`…`FLAG_TEMP_1F` — covering all 14 object flags —
on every map load (`src/overworld.c:798`, `:848`). The (8,3) ladder stays inside the 36-tile sealed
pocket, so **leaving and re-entering is a full reset**, as in the §Ch22 ice puzzle.
⛔ The same function does `FlagClear(FLAG_SYS_USE_STRENGTH)` at `:45` ⇒ **Strength must be
re-activated on EVERY visit**, and the puzzle solved in a single visit.

### ⇒ THE DESIGN CONSTRAINT, UNCHANGED BY THE CORRECTIONS
**Ship a fixed push SEQUENCE, never a runtime solver, and make a SOUTH push on either boulder
unreachable in code.** A refusal costs nothing if the model is over-cautious; a wrong push costs the
visit. This is the §Ch22 ice-route pattern: a precomputed table verified live per step beats a
planner on a puzzle where one wrong move is unrecoverable.

## §1. ⭐ THE MINIMUM SOLUTION — 2 PUSHES + 1 SMASH, **CONFIRMED EXACTLY** (cost 3)

From B1F (8,3) to the B2F ladder at (30,25):

| # | action | stand on | note |
|---|---|---|---|
| 1 | **PUSH WEST** boulder (4,7) → **(3,7)** | (5,7) facing W | opens the x=4 column *and* preserves (9,10)'s east option |
| 2 | **PUSH EAST** boulder (9,10) → **(10,10)** | (8,10) facing E | ⛔ the one push that must never go SOUTH |
| 3 | **SMASH** rock **(18,12)** | — | on the row-12/13 corridor east |

✅ **An independent solver reproduced cost 3 with the identical actions and identical standing
tiles.** ⛔ **My own probe briefly called step 1 REDUNDANT — that was MY error, not the audit's;
see §E2.**

**The other 5 boulders and 5 rocks are OPTIONAL.** ‼ The (20,5)/(21,4) and (20,26)/(21,25) clusters
are deliberate boulder-rock **INTERLOCKS** — three boulders have no legal push until their paired
rock is smashed ⇒ **pushes are ORDER-DEPENDENT and a tile graph cannot express them.**

## §2. THE ROUTE — AND B1F HAS **THREE** LADDER-BEARING REGIONS, NOT TWO

⛔ **The original audit listed 6 warps; B1F has 7.** Corrected:

* **Region A** (301 tiles): ladders (8,3)→1F(9,14) · (42,25)→1F(42,38) · **(30,25)→B2F**
* **Region B** (107 tiles): ladders **(20,21)→1F(21,32)** · (17,16)→B2F · (5,26)→B2F
* ⭐ **Region C — MISSED ENTIRELY (35 tiles, x=40-44 / y=1-10, elevation 4):** warp
  `{x:42, y:2 → MAP_VICTORY_ROAD_B2F}`, reachable **only** from B2F(43,2). It holds **TM Psychic at
  (42,8)** — which is why that item is unreachable from B1F.
* *(301 + 107 + 35 = 443; the remaining 6 walkable tiles are the right-edge column (45,0)-(45,5).)*

✅ **"Crossing A→B requires B2F by Surf" is CONFIRMED by an impossibility proof:** from Region A
without Surf — **with every boulder, rock and NPC removed** — 301 tiles and zero Region-B ladders.

⇒ **The chain:** 1F(15,40) → 1F(9,14) → **B1F(8,3) → [2 pushes + 1 smash] → B1F(30,25)** →
**B2F(30,25) → [SURF] → B2F(19,12) or (5,26)** → **B1F(17,16) or (5,26) → B1F(20,21)** → 1F(21,32)
→ 1F(39,5) → the League.

| kit (all obstacles removed, so this is a reachability proof) | exit |
|---|---|
| no Surf | ❌ **impossible** |
| **Surf, no Waterfall climb** | ✅ 1821 states |
| Surf + Waterfall climb | ✅ 1821 states — **climbing adds literally zero** |

⛔ **WATERFALL IS NOT REQUIRED INSIDE THE CAVE.** `[MB_WATERFALL] = TILE_FLAG_UNUSED |
TILE_FLAG_SURFABLE` (`metatile_behavior.c:28`); `MetatileBehavior_IsWaterfall` is index 14 of
`sForcedMovementTestFuncs` → `sForcedMovementFuncs[15] = ForcedMovement_PushedSouthByCurrent`, so
descending is free. Climbing is gated by `FIELD_MOVE_WATERFALL, // FLAG_BADGE08_GET`
(`party_menu.c:127`). ⚠ **Waterfall IS still required to REACH Ever Grande** — that is a different
leg, and both statements are true.
⚠ Without the climb the B1F→B2F→B1F transit is ONE-WAY; we hold Waterfall (Wailmer), so all four
B2F ladders interconnect — but the route must assert the carrier is alive.

## §3. TRAINERS — **5 SIGHT-TRIGGERED + WALLY**, NOT 6 SIGHT-TRIGGERED

⛔ The original "6 unavoidable battles" is **not reproducible as stated**. An independent count of
minimum distinct sight-triggered trainers on any entrance→exit path gives **5**: **Hope, Edgar (1F),
Halle, Samuel (B1F), Julie (B2F)** — computed with boulders removed, so it is a **LOWER BOUND**.
✅ **Wally is separately proven unavoidable:** blocking his only two trigger tiles 1F(2,23)/(3,23)
drops the exit from reachable to unreachable (433 vs 680 tiles).
⇒ **The honest figure is ≥5 sight battles + 1 scripted Wally.** The boulder-constrained minimum was
not computed by either pass.

Sight is a 1-wide line along the CURRENT facing, blocked by any collision or object en route
(`src/trainer_see.c:308-311`, `:384-389`); `sight = 0` can never initiate (`:377-378`).
⚠ **Halle (14,20) alternates between two facings at random** (`event_object_movement.c:3321-3331`:
`direction = directions[Random() & 1]`) — **both lines are live; you cannot time it.**
⚠ **Dianne (25,18) and Felix (25,21) face each other across an elevation-4 platform** and both see
both crossing rows (19 and 20) at once.
⚠ Returning via B1F(5,26) instead of (17,16) adds Michelle and Mitchell ⇒ **prefer (19,12)→(17,16).**

## §4. HAZARDS — the census, with two corrections and one that bites our own tooling

**B1F:** `MB_CAVE` 685 · `MB_NORMAL` 546 · `MB_IMPASSABLE_NORTH` 178 · `MB_JUMP_WEST` 10 · `MB_LADDER` 7
**B2F:** `MB_CAVE` 530 · `MB_NORMAL` 450 · **`MB_OCEAN_WATER` 238** · `MB_IMPASSABLE_NORTH` 181 ·
`MB_WATERFALL` 18 · `MB_JUMP_SOUTH` 5 · `MB_LADDER` 4
*(Both passes reproduce the `MB_IMPASSABLE_NORTH` counts **exactly** — one of four invariants that
independently confirm the coordinate space; see §E1.)*

⛔ **CORRECTION — THE LEDGE CLAIM WAS BACKWARDS.** B1F has **10** `MB_JUMP_WEST` tiles in **three**
groups — (11,4-6), (24,12-15), (39,25-27) — not the three tiles originally named. And the structural
conclusion fails a direct test: **banning EVERY ledge on B1F leaves Region A at 301 tiles with
(8,3) ↔ (30,25) still connected both ways.** ⇒ **no B1F ledge is load-bearing; they are all
shortcuts**, and the claim that entering the (30,25) chamber is a one-way jump is wrong.
⭐ Bonus the first pass missed: **(11,4-6) is a one-way ledge *INTO* the arrival chamber** from
(12,y) — an inbound path, which is *why* §0's "only two exits" still holds.

⚠ **CORRECTION — DO NOT GENERALIZE "VICTORY ROAD HAS NO MAP SCRIPTS."** True for the basements only:
`VictoryRoad_B1F/scripts.inc` and `_B2F` are both `MapScripts:: / .byte 0` with `coord_events: []`.
⛔ **`VictoryRoad_1F` DOES have an `ON_TRANSITION` script and 2 Wally `coord_events`.**

✅ **VERIFIED NEGATIVE on both basements:** no cracked-floor holes, no slides, no ice, no currents,
no muddy slopes, no warp pads, no arrow warps.

✅ **`MB_IMPASSABLE_NORTH` IS A REAL MECHANIC BUT IS *VACUOUS ON B1F* — MEASURED, NOT ASSUMED.** The
north EDGE is blocked in both directions (`event_object_movement.c:893-905`, `:4715-4722`) while the
tile reads collision-0, so a pure-collision pathfinder normally walks straight through. ⛔ **Here it
does not matter:** all 13 *passable* such tiles — (19..22,8), (29..32,8), (41,14), (42,14),
(32..34,15) — have a collision-1 wall directly north, so **0 passable→passable crossings are blocked
by the rule alone**, and its fault arm changes nothing (min 3, 70,442 states, 891 dead).
⇒ ‼ **Do not carry "B1F has 178 impassable-north tiles" as a hazard** — 178 is the raw behaviour
count, and only 13 sit on passable tiles, none of which gate anything. *(I initially blamed this rule
for my own false finding in §E2. That was wrong; see §E2 for the real cause.)*
⚠ It remains live elsewhere in the ROM (KI-59), and production models it
(`accessible_from_direction` / `blocked_exit_directions`) while our offline scripts do not.

⚠ **WILD ENCOUNTERS ON EVERY WALKABLE TILE** — B1F land 10 + rock-smash 20; B2F land 10 + water 4.
**`RockSmashWildEncounter` can start a battle from the smash itself**
(`data/scripts/field_move_scripts.inc:90`) ⇒ **a mid-puzzle battle is NORMAL, not a fault.**

## §5. ITEMS (all optional; none on the mandatory path)

B1F: **TM Psychic (42,8)** — ⛔ inside **Region C**, reachable only from B2F(43,2) · Full Restore
(32,3) · no hidden items. B2F: Full Heal (13,8) — Surf only · hidden Elixir (28,5) — Surf only ·
hidden Max Repel (37,1).
*(Nitpick from the adversarial pass: the 14 objects use 14 of the 15 flags in the range —
**`FLAG_TEMP_18` is unused**.)*

## §E1. ✅ THE COORDINATE-SPACE TRAP — CHECKED FIRST, AND IT IS NOT THE FAULT LINE

The likeliest way this audit could have been worthless while reading perfectly was an **object/layout
coordinate offset**. It was attacked directly and **four independent invariants agree in raw layout
space**: all 7 B1F warps land exactly on the 7 `MB_LADDER` tiles; both named boulders sit on
`MB_CAVE`/collision-0/elevation-3 tiles; the `MB_IMPASSABLE_NORTH` counts reproduce exactly; and the
arrival chamber independently computes to 23 tiles. ✅ **My own probe reproduced the boulder/rock
positions, both shaft walls, both push destinations and the 23-tile chamber from the same bytes.**

⚠ **THE REMAINING VARIANT OF THAT RISK, AND WHY I BELIEVE IT IS ALREADY RETIRED.** The running game
stores `gObjectEvents[].currentCoords` with `MAP_OFFSET` (7) applied; if our bot surfaced live coords
un-normalised, every tile here would be off by **+7 in both axes** while every static check still
passed. ✅ **Evidence in hand that it does not:** earlier today `--driver ch23route` fed
`calculate_path` these same decomp coordinates and got **29 wp** to Wally (3,23), **44 wp** to the
B1F ladder (9,14), and **15 wp** between them — matching my offline model on all three, and
29 + 15 = 44. **Three independent agreements are not obtainable under a uniform +7 shift.**
⇒ treated as retired, but §F check 1 confirms it for free anyway by reading the arrival tile.

## §E2. ⛔⛔ MY OWN PROBE PRODUCED A FALSE REFUTATION, AND THE REASON IS NEW

`tools/story-dev/probe_vr_b1f_claims.py` independently **confirmed all the geometry** (§E1). Then it
reported two refutations, **both of which are WRONG**:

| my finding | adjudication |
|---|---|
| "PUSH WEST (4,7) is REDUNDANT" | ⛔ **REFUTED** — the independent solver returns cost 3 with that push required |
| "pushing (4,7) SOUTH does not seal" | ⛔ **REFUTED** — forcing it as the first push yields SEALED |

⛔⛔ **AND MY FIRST DIAGNOSIS OF MY OWN ERROR WAS ALSO WRONG — CORRECTED HERE.** I blamed the missing
directional-edge-blocker rule. **The independent solver proves that rule is VACUOUS on this map:**
all 13 passable `MB_IMPASSABLE_NORTH` tiles — (19..22,8), (29..32,8), (41,14), (42,14), (32..34,15) —
have a **collision-1 wall directly north**, so the number of passable→passable crossings blocked
*only* by the directional rule is **0**. Its own fault arm confirms it: breaking that rule changes
nothing (min 3, 70,442 states, 891 dead, unchanged). ⇒ **a pure-collision model is not wrong here,
and my plausible-sounding explanation was a second guess dressed as a cause.**

**THE ACTUAL, SINGLE CAUSE OF BOTH FALSE FINDINGS: I TESTED BOARD STATES THE GAME CAN NEVER REACH.**
* The seal test asked *"with this boulder parked here **and every other obstacle cleared**, is the
  ladder reachable?"* — but you cannot clear the other obstacles **from** the sealed state. That was
  the whole point of it being sealed.
* The necessity test dropped push 1 and kept push 2 — but **you cannot perform push 2 without push
  1**: the only way to (8,10), where you must stand to push (9,10) east, is
  `(4,7)→(4,10)→(8,10)`, and push 1 is what opens (4,7).

⇒ ⛔⛔ **PREVENTION RULE — AND IT GENERALISES BEYOND SOKOBAN: APPLYING A SUBSET OF ACTIONS DOES NOT
PRODUCE A REACHABLE STATE. Before a counterfactual board refutes anything, prove the board is
REACHABLE, in order.** A "necessity" test that removes step *k* and keeps step *k+1* silently assumes
the steps are independent — and this note's own §1 says the pushes are **ORDER-DEPENDENT**. I had
written that sentence and then tested as though it were false.
⇒ The right instrument is the Sokoban's **forced-first-action enumeration over reachable states**; a
reachability query over a hand-built board is not, and cannot be made into one by being generous.

## §E3. ⭐⭐ AN INDEPENDENT RE-DERIVATION FROM SCRATCH — AND ITS FAULT TABLE IS THE REASON TO BELIEVE IT

A second solver was built **from primary data with no sight of the first**, in a fresh directory, and
told that a second *opinion* was worthless — only a second *instrument* counted. Its numbers:

| quantity | audit | independent re-derivation |
|---|---|---|
| minimum actions | 3 (2 pushes + 1 smash) | **3 — and the minimal sequence is UNIQUE (exactly 1)** |
| the actions & standing tiles | (5,7)W, (8,10)E, smash (18,12) | **identical** |
| reachable states | 70,442 | **70,442** |
| dead states | 891 | **891** |
| fatal actions | 2 | **2** (3 live→dead edges: (9,10)-south is fatal from 2 live configs) |

‼ **Agreement is not a confidence signal** (measured; see `CLAUDE.md`). What makes this one worth
believing is the **fault-injection table**, which is the discipline this project keeps re-learning:

| rule broken | effect | verdict |
|---|---|---|
| collision decode | min 3 → **0** | ✅ live |
| elevation ENTRY | 70,442 → **192,032** states | ✅ live |
| ⭐ **elevation CARRY (15 preserves)** | **goal becomes UNREACHABLE** (10,623 states, all dead) | ✅ **the single most load-bearing rule** |
| object/boulder blocking | min → 0 | ✅ live |
| ledges → plain walls / omnidirectional | 69,713 states / min → 1 | ✅ live |
| push-destination object check | → 92,650 states | ✅ live |
| player start elevation | 70,442 → 70,443 | ✅ live (barely) |
| directional edge blockers | **no change** | ⛔ vacuous here — *proved*, see §4 |
| push semantics (player steps in) | **no change** | ⛔ provably equivalent: 0/1088 push edges leave a vacated tile the player cannot immediately enter |
| rock-smash elevation gate | **no change** | ⛔ never fires: all 6 rocks and every standable neighbour are elevation 3 |
| static-NPC elevation source | **no change** | ⛔ template elevation == map elevation for all 7 statics |

⭐ **Note what it did with the four rules it could NOT break: it chased each to a PROOF OF WHY rather
than claiming them verified.** That is the correct handling of a control that cannot discriminate,
and it is the exact behaviour `solve_victory_road.py` was repaired to adopt earlier today.

⭐ **The elevation-15 carry is the rule the whole answer rests on** — break it and the player strands
on the `MULTI_LEVEL` bridge at (37,15)/(38,15)/(37,16) and can never step back down to elevation 3 at
(37,17). ✅ This is the same rule our own `map_path.py:859`/`:1039` implements, so production and this
model agree on the mechanic that matters most.

⛔ **IT ALSO CORRECTED A PREMISE I SUPPLIED.** I told it a Strength push moves the player into the
boulder's old tile. `PushBoulder_Move` (`src/field_player_avatar.c`) actually gives the player
`GetWalkInPlaceNormalMovementAction` and the boulder `GetWalkSlowMovementAction` — **the player walks
in place and does NOT enter the tile; you press the direction again to follow.** Provably equivalent
for reachability here, but the premise was wrong and would matter for step-counting a driver.

### ⚠ THE ROUTING HAZARD NEITHER EARLIER PASS FOUND: SAMUEL STANDS ON THE ANSWER
All five B1F trainers are `TRAINER_TYPE_NORMAL` and **move when they spot you**. **Samuel's sight
line (36,12)(35,12)(34,12) lies directly on the minimal path.** Sweeping all 1,200 combinations of
the five trainers over their sight corridors: **900 give min = 3, 300 give min = 6, none
unreachable.** All 300 are the cases where Samuel ends on **(34,12)** — argued impossible because a
trainer halts *adjacent* to the player and you enter his sight from the west, so he stops at (35,12).
⇒ ✅ **the 3-action answer is robust — but only just, and it rests on one unread mechanic.**

### ⛔ WHAT THE RE-DERIVATION EXPLICITLY COULD NOT SETTLE
1. The player's **carried elevation immediately after warp-in** (derived as 3 from `InitPlayerAvatar`
   + `ObjectEventUpdateElevation`, never observed live). Its fault arm moves the state count by 1.
2. **Samuel's exact post-battle resting tile** — the "stops adjacent" argument was reasoned, not read
   from `TrainerApproach`. **This is the one place the answer is sensitive to an unread mechanic.**
3. Whether `previousCoords` in `ObjectEventUpdateElevation` is the pre-step tile at the moment
   collision is evaluated (frame ordering of `OnBeginStep`/`OnFinishStep` not traced).
4. Ledge landing tiles are never validated by the game; all 10 landings were asserted collision-0.

## §F. ⛔ THE THREE LIVE CHECKS THIS NOTE IS NOT VALID WITHOUT

Nothing above has touched live RAM. **Do these before any §Ch23 boulder code:**
1. Warp into B1F from 1F and **read the arrival coordinates and the tile behaviour under the player**
   from the bot's own API. The decomp says **(8,3)/`MB_LADDER`**. If it reports (15,10), apply −7/−7
   to every coordinate in this document. *(One reading; validates the coordinate space and the
   behaviour readout at once.)*
2. Stand at **B1F(5,7)**, push **west**; confirm the boulder lands on **(3,7)** and the x=4 column opens.
3. Push **(9,10) south** once and confirm **(30,25) becomes unreachable** — reproduce the seal
   deliberately, so the hazard is measured rather than believed; then leave and re-enter to confirm
   the reset. ⭐ Assert the sealed pocket is **36 tiles**, which both solvers agree on.
