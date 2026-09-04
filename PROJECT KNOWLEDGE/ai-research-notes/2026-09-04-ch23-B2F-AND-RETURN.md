# §Ch23 LEG 7-8 — VICTORY ROAD B2F AND THE RETURN LEG (2026-09-04)

> ⛔ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md`. The authoritative doc WINS on any
> contradiction until this is verified. **READ** = an agent read the decomp file; **MODELED** = an
> agent's own collision/movement simulator, *not* a decomp fact; **OURS** = measured in our harness.

**Provenance.** A 19-agent workflow (`ch23-b2f-return-recon`, 0 errors): five independent recon
angles, each of whose load-bearing non-READ findings was then handed to an **adversarial verifier**
told to refute it. ⚠ Agreement is not a confidence signal here — citations are.

---

## 0. ⛔⛔ THE HEADLINE: OUR WORKING ASSUMPTION WAS **PARTLY REFUTED**

We assumed B2F was *"surf across the lake and ride the waterfall down"*. The adversarial pass:

> **VERDICT: PARTLY REFUTED — and the surviving half is the dangerous half.**

- ✅ **SURVIVES:** the waterfall **descent is badge-free** and **Waterfall/HM07 is NOT required**.
  `field_player_avatar.c:160` maps `MetatileBehavior_IsWaterfall` to slot 14 of
  `sForcedMovementTestFuncs`, pairing with `ForcedMovement_PushedSouthByCurrent` at `:184` — **no
  flag check**. `PlayerStep` (`:344`) evaluates forced movement *before* keypad input, so holding
  North cannot override it.
- ⛔ **BROKEN:** it is not one lake crossing. It is a **~115–119 step traverse across THREE
  elevation layers with TWO separate Surf mounts**, and the arrival ladder sits in a **65-tile land
  pocket** whose only water access is `(33,17)` facing north.
- ⛔ **BROKEN:** B2F is **not ledge-free** — five `MB_JUMP_SOUTH` tiles at **(40,20)–(44,20)**.
  (Boulders and rocks genuinely are zero, as we believed.)
- ⚠ **BROKEN, but LESS badly than this note first said:** **SIX** line-of-sight trainers, of
  which **FOUR are reported unavoidable** (that count is MODELED and unverified). Dianne (25,18,
  facing DOWN) and Felix (25,21, facing UP) face each other across (25,19)/(25,20), so crossing
  between them triggers **TWO CONSECUTIVE SINGLE BATTLES**.
  ⛔⛔ **CORRECTION 2026-09-04 — THIS NOTE ORIGINALLY CALLED THAT A "forced 2-vs-4 DOUBLE
  BATTLE" AND IT IS FALSE.** A Tier 1 reviewer refuted it from primary source and I re-verified:
  `data/maps/VictoryRoad_B2F/scripts.inc` gives **`trainerbattle_single`** for all six trainers
  including Felix and Dianne, and `map.json` marks both **`TRAINER_TYPE_NORMAL`**, not
  `TRAINER_TYPE_DOUBLE` — the only type that links two NPCs into a simultaneous double battle.
  ⇒ two back-to-back single fights is still a real hazard for a 4-battler party, but it is **not**
  the capability question the original wording made it. ‼ **AND THE 19-AGENT WORKFLOW'S OWN
  ADVERSARIAL PASS REPORTED "0 errors" OVER THIS** — see §6.

⇒ **Leg 7 is materially harder than legs 5 and 6** — a ~115-step traverse, two Surf mounts, a
one-way descent and four reported-unavoidable trainer fights on a party whose bench is an L19 mule.
‼ Plan the trainer load *before* building the walk: four consecutive fights with no heal is the same
attrition shape that took leg 6 from 100% to 32%.
⛔ *(This paragraph called it "a capability question, not a routing one" because of the double-battle
claim above. With that refuted it is a ROUTING and ATTRITION question — the ordinary kind.)*

## 1. ⛔⛔⛔ THE B2F ROUTE BELOW **STRANDS THE BOT** — DO NOT BUILD IT. (kept as history; see §1b)

> **REFUTED 2026-09-04 by an adversarial verifier working from the decoded `map.bin` (size asserted
> 2852 = 46×31×2, decoder self-validated by finding exactly 4 `MB_LADDER` tiles at exactly the 4
> `map.json` warp coordinates).**
>
> ⛔ **THE FATAL STEP IS PHASE 2.** Mounting Surf at `(33,17)` northward onto `(33,16)` enters a
> **43-tile DEAD-END POND** (x24-35, y12-16) whose **seven** dismount tiles all return to the land
> pocket you came from. **It cannot reach the exit ladder from there.** A leg built on this route
> surfs into a cul-de-sac and strands.
>
> ⛔ Two further errors in the same phase: the arrival pocket is **354 tiles, not 65** (it spans
> y=1..26 and contains **3 of the 4 ladders** — (30,25), (43,2) and (5,26) are all walk-connected
> with **no Surf at all**), and it offers **20 legal Surf mounts, not one**. The "65" figure is not
> reproducible under any movement model; the correct one — treating **elevation 0 as
> `ELEVATION_TRANSITION`, a wildcard** (`event_object_movement.c:7709`) — gives 354.
>
> ⇒ ‼ **THE ROUTE WAS BUILT ON A MOVEMENT MODEL THAT MIS-HANDLED ELEVATION 0**, which is exactly the
> class of error the FIRST recon agent reported correcting in its own simulator mid-run (301 tiles
> vs 106). The same bug survived into a different agent's output and was never caught, because the
> workflow's verify stage **exempted `READ`-tagged claims** — see §6.

### ⭐ THE CORRECTING STRUCTURE: THE WATER IS **THREE DISCONNECTED BODIES**, NOT ONE

Waterfalls are one-way, and the only seams at row y=11 are the two waterfall columns (x7-9 and
x25-27); **every other tile on that row is collision 1.**

| body | tiles | extent | mounts from the arrival pocket | reaches the EXIT ladder? |
|---|---|---|---|---|
| NORTH | 141 | x4-27, y1-10 | (4,6)N (5,6)N (6,6)N/E (6,7)E (6,8)E (6,9)E **(6,10)E** | **only via a waterfall** |
| **WEST-MID** | 54 | x6-22, y12-17 | **(13,18)N (14,18)N (15,18)N** | ✅ **YES** |
| EAST-MID | 43 | x24-35, y12-16 | (33,12)W (33,13)W/S (34,13)S (35,13)S **(33,17)N** (34,17)N (35,17)N | ⛔ **NO — dead end** |

⇒ **ONE mount suffices**: enter WEST-MID directly at (13,18)/(14,18)/(15,18). The second mount and
the waterfall descent in §1 are **not required** — they are one valid way to reach WEST-MID, not the
only one.

## 1b. THE ORIGINAL (REFUTED) ROUTE — HISTORY ONLY, DO NOT BUILD

*(kept so the error is legible; every phase from 2 onward rests on the dead-end mount)*

## 1c. THE ORIGINAL ROUTE TABLE (MODELED — two agents, 115 vs 119 steps)

B2F has `connections: null`, so the whole traverse is **ONE per-map walk** containing 2 surf mounts,
2 dismounts and a forced descent. Ordered:

| # | phase | detail |
|---|---|---|
| 1 | walk, elev 3 | `(30,25)` → E,E `(32,25)` → N,N `(32,23)` → E `(33,23)` → N×6 → **`(33,17)`**. ⚠ `(33,22)` is in **Julie's** sight cone. |
| 2 | **MOUNT SURF** | stand `(33,17)`, face **NORTH**, press A → water `(33,16)`. **The only water access from the arrival pocket.** |
| 3 | surf | `(33,16)` → N → `(33,15)` → N → `(33,14)` |
| 4 | **DISMOUNT** | N onto `(33,13)` (elev 3) |
| 5 | walk, the long circuit (~60 steps) | `(33,12)` → E `(34,12)` → N×7 → `(34,5)` → E×4 `(38,5)` → S `(38,6)` → E `(39,6)` → … → `(41,8)` → S×11 → `(41,19)` |
| 6 | elev 3→4 | W onto **`(40,19)`** — an ELEVATION-0 TRANSITION tile. ⚠ **There are FIVE such 3↔4 seams, not two: (39,17), (6,18), (40,18), (6,19), (40,19)** — any route hardcoding two mis-models the graph (verified 2026-09-04). |
| 7 | walk, elev-4 trunk | `(40,19)` → W×32 along row 19 → `(8,19)`. ⛔ **`(25,19)` is in BOTH Dianne's and Felix's cones — TWO CONSECUTIVE SINGLE battles (not a double; see §0).** |
| 8 | elev 4→3 | `(8,19)` → N `(8,18)` → W `(7,18)` → W **`(6,18)`** (second elevation-0 gateway) → W×4 → `(1,18)` |
| 9 | walk | `(1,18)` → N×8 → `(1,10)` → E×5 → **`(6,10)`** |
| 10 | **MOUNT SURF (2nd)** | stand `(6,10)`, face **EAST** → water `(7,10)`. ‼ **POINT OF NO RETURN NEXT** |
| 11 | **FORCED DESCENT** | S onto `(7,11)` = `MB_WATERFALL`; the game seizes control and slides you S to `(7,14)` |
| 12 | surf | `(7,14)` → E along row 14 → `(17,12)`/`(19,14)` region |
| 13 | **DISMOUNT + ladder** | onto the apron (`(18,12)` or `(19,13)`), then **ONE explicit step** onto **`(19,12)`** `MB_LADDER` → B1F warp 1 = **`(17,16)`** |

✅ **RESOLVED 2026-09-04 — BOTH agents were right, and there is a third.** The ladder `(19,12)` sits
on a 6-tile island `{(18,12),(19,12),(20,12),(18,13),(19,13),(20,13)}`, all `MB_CAVE` elev 3.
**`(19,11)` is collision 1 — a wall — so a NORTH approach is impossible**; the other three neighbours
all work: **`(18,12)`→E, `(20,12)`→W, `(19,13)`→N**. Our own planner reaches (18,12) and (19,13) in
**63 wp each** (§4b). ⇒ the "at most one can be right" framing was itself wrong.

## 2. ⭐ THE VERIFIER'S CORRECTION — the waterfalls are BIDIRECTIONAL

An adversarial verifier confirmed the descent AND caught a modeling artifact worth more than the
claim it checked:

- Waterfall columns (READ, decoded from `map.bin` with the size asserted): **x=26 at y=9,10,11** and
  **x=8 at y=11,12,13**, all `coll=0 elev=1`, ocean water above and below.
- Pressing **North** from a base is a **NET-ZERO bounce** — you enter the tile and are pushed back.
- ⛔ **BUT ASCENT IS NOT IMPOSSIBLE — IT IS IMPOSSIBLE *BY D-PAD*.** `field_control_avatar.c:453-459`
  (`GetInteractedWaterScript`): facing a waterfall with `FLAG_BADGE08_GET` and `IsPlayerSurfingNorth()`
  returns `EventScript_UseWaterfall`; `field_effect.c:1873-1898` rides up one tile at a time with
  `preventStep = TRUE`, so the south push cannot fire mid-ride.
- ⇒ **Both columns are bidirectional in the real game. The recon BFS modeled only descent and emits
  no ascent successor at all**, so any "the upper region is unreachable" conclusion from it is a
  **modeling artifact of a missing HM, not B2F topology.** ‼ Do not let "NET-ZERO bounce" propagate
  into a doc as "unreachable" — **we hold HM07.**

⚠ Also un-modeled (READ): `fpa.c:416` gates forced movement on `!(flags & PLAYER_AVATAR_FLAG_CONTROLLABLE)`,
giving a **one-step grace window** after returning to the field (post-battle, post-menu, post-warp)
in which a player parked on a waterfall tile is *not* pushed. Our bot fights wild encounters on
water, so this window is reachable.

## 3. ✅ OUR OWN SURF/WATERFALL SUPPORT IS COMPLETE — WITH ONE REAL BUG

**Good news (audit of `sandbox-pokebot/`):** Surf is **fully automatic**. `calculate_path` treats
water as walkable-while-surfing via an elevation 3→1 transition gated on BADGE05 + a party Surf move,
emits `WaypointAction.Surf`, and `follow_waypoints` mounts by **pressing A at the water's edge**.
There is no separate "mount surf" helper and no caller passes `no_surfing=True`. Waterfall is modelled
end-to-end (climb UP gated on BADGE08 + the move, ride DOWN un-gated), with integration tests both
directions on Route 119.

✅ **THE BUG — FOUND HERE AND FIXED 2026-09-04 (`#24-waterfalltimeout`, sandbox only). The snippet below is the PRE-FIX text, kept because it is what made the defect legible:**
```python
frames_remaining_until_timeout += 195 + (get_player_location()[0][1] - waypoint.coordinates[1]) * 42
```
`get_player_location()` returns **`(map_enum, (x, y))`** (`player.py:291`). ⇒ `[0][1]` is the **MAP
NUMBER**, not the player's `y`. It must be `[1][1]`.
- Ever Grande is map num **8**; a climb to `y=59` gives `(8 − 59) × 42 = **−2142** frames` — a
  **negative** timeout allowance.
- B2F is map num 45 against `y≈11`, giving `+1428` — a wildly over-generous one.
⇒ **The same line is both far too short and far too long depending on the map.** It is latent today
only because our legs **hand-drive** waterfall climbs rather than letting the planner emit a
`Waterfall` waypoint (§Ch23 leg 4 does exactly this, with the `NOCLIMB` fault arm). ‼ **Leg 7's
descent may be the first time we ride a planner-emitted waterfall waypoint — fix this first.**

## 4. THE RETURN LEG (B1F → 1F → the exit) — MODELED, one confirmed trap

From B2F `(19,12)` you land on **B1F `(17,16)`**, with **all `FLAG_TEMP_*` and
`FLAG_SYS_USE_STRENGTH` CLEAR** (the warp reset — which we have already confirmed live).

✅ **The 2×2 plug is exactly as we believed:** rocks at **(20,25)** + **(21,26)**, boulders at
**(21,25)** + **(20,26)**.

⛔⛔ **THERE IS EXACTLY ONE TRAP, AND IT IS AVOIDABLE BY CONSTRUCTION:** boulder `local_id 6` at
**(21,25)** has a **single legal push (EAST)** and **it bricks the route**. ⭐ **Pushing boulder
`local_id 5` at (20,26) NORTH instead makes that trap physically impossible.** ⇒ order the solve so
the trap is never reachable, rather than guarding against choosing it.

Suggested order (MODELED): walk `(17,16)`→`(19,25)` · **Rock Smash `(20,25)`** facing E · walk to
`(20,27)` · **Strength-push boulder 5 NORTH** · **Rock Smash `(21,26)`** facing E · walk to the apron
**`(21,21)`** · **one explicit step WEST** onto the ladder `(20,21)` → 1F `(21,32)`.

Then on 1F: `(21,32)` → 61 steps → apron **`(38,5)`** → **one explicit step EAST** onto **`(39,5)`**
→ ⛔ **HOLD DPAD_DOWN** until the map changes (`MB_SOUTH_ARROW_WARP` — ✅ CONFIRMED verbatim from
`field_control_avatar.c`, and we have now driven the *other* arrow warp at (15,40) live).

⚠ **Two corrections to our priors:** B1F is **SEVEN** meaningful walk-islands, not three; and the
Victory Road **top exit lands on an isolated Ever Grande region** (consistent with the earlier
League-approach note's plateau finding).

## 4b. ✅✅✅ LIVE VERIFICATION — `--driver ch23b2fprobe`, OBSERVE ONLY, 2026-09-04

Run from `post_b1f_healed.ss1` (already on B2F (30,25)), `ACCEPTANCE: PASS`, all 6 readings,
**`battles=0`, `whiteouts=0`, not a step taken.** Everything below is **OURS** — our own
`calculate_path` and our own `get_map_data`, not a model.

### ⭐ EVERY TILE-LEVEL CLAIM IN THIS NOTE IS CONFIRMED

| tile | claimed | MEASURED |
|---|---|---|
| `(30,25)` arrival | ladder | **Ladder**, coll 0, elev 3 ✅ |
| `(33,17)` mount 1 stand | land | **Cave**, elev 3 ✅ |
| `(33,16)` | ocean water | **Ocean Water**, elev 1 ✅ |
| `(33,13)` dismount | land elev 3 | **Cave**, elev 3 ✅ |
| `(40,19)` | ELEVATION-0 transition | **Cave, elev 0** ✅ |
| `(6,18)` | second elev-0 gateway | **Impassable North, elev 0** ✅ |
| `(6,10)` mount 2 stand | land | **Cave**, elev 3 ✅ |
| `(7,10)` / `(7,11)` / `(7,14)` | water / waterfall / water | **Ocean Water / Waterfall / Ocean Water**, all elev 1 ✅ |
| `(40,20)`, `(42,20)`, `(44,20)` | `MB_JUMP_SOUTH` ledges | **Jump South**, coll 1, elev 0 ✅ |

⇒ **the agents' READS were accurate.** It is the *routing synthesis* built on top of them that needs
care — which is the same split the double-battle error showed (real files, wrong conclusion).

### ⛔⛔ BUT THE ROUTE ITSELF IS MUCH SIMPLER THAN THIS NOTE'S §1 SAYS

| target | our planner |
|---|---|
| `(33,16)` — first water | **12 wp**, actions `{Surf: 1}` |
| `(33,13)` — across, dismounted | 15 wp, `{Surf: 1}` |
| `(6,10)` — second mount stand | 54 wp, `{Surf: 1, Waterfall: 1}` |
| `(25,19)` — the trainer corridor | 61 wp, `{Surf: 1}` |
| **`(18,12)` exit apron** | **63 wp**, `{Surf: 1, Waterfall: 1}` |
| **`(19,13)` exit apron** | **63 wp**, `{Surf: 1, Waterfall: 1}` |

⭐⭐ **OUR PLANNER ROUTES THE WHOLE TRAVERSE BY ITSELF, MOUNTING SURF AND RIDING THE WATERFALL** —
one `navigate_to` reaches the exit apron. §1's 13-phase hand-built route was a MODELED reconstruction
of what the planner does anyway. ⇒ **leg 7 does NOT need to hand-drive the crossing** the way leg 4
had to hand-drive its waterfall CLIMB (the planner genuinely will not plan a climb; it plans a
descent fine).

⭐ **THE TWO AGENTS' DISAGREEMENT IS RESOLVED — AND BOTH WERE RIGHT.** (18,12) and (19,13) are each
reachable in **63 wp**. Either works as the exit apron; pick one and pin it.

⛔⛔ **THE WARP-OVERRIDE TRAP, CONFIRMED LIVE FOR THE FOURTH TIME IN THIS CHAPTER.** Aiming at the
ladder itself: `calculate_path (30,25) → (19,12)` returns **64 wp whose LAST waypoint is
`map=(24,44) coords=(17,16) is_warp=True`** — i.e. it silently ends on **B1F**, doing leg 8's job,
and an honest end-position grade would FAIL a perfect run. ⇒ **aim at the apron; step onto the ladder
explicitly.**

⚠ **WHAT THIS DOES *NOT* SETTLE.** Waypoints are not steps — 63 wp is consistent with §1's ~115
tiles. And a reachable path says nothing about **trainer sight-lines**, which fire regardless: the
corridor tile `(25,19)` is 61 wp in and on a live path. The attrition question stands.

## 4c. ⭐⭐⭐ THE TRAINER LOAD IS A CHOICE, NOT A MAP PROPERTY — AND WE ALREADY HOLD THE LEVER

**VERIFIED 2026-09-04** by an adversarial pass that decoded `map.bin` itself (2852 bytes asserted)
and replayed the decomp's own LOS algorithm over all 1426 tiles, by two independent constructions
that agreed exactly.

| capability | FORCED trainer fights |
|---|---|
| **Surf + Waterfall** | ⭐ **ONE — Julie only** |
| Surf only | **FOUR** — Caroline, Julie, Dianne, Felix |
| no Surf | the exit is **unreachable** (238 tiles of B2F are `MB_OCEAN_WATER`; the exit ladder sits on a 3×2 island) |

✅✅ **AND THE ONE-FIGHT PREDICTION IS NOW CONFIRMED IN A LIVE DRIVE (2026-09-04).** Leg 7's
instrumented run logged `battle_log = ['wild Lairon', 'TRAINER', 'wild Golbat']` — **two wild
encounters and EXACTLY ONE trainer.** ‼ Run 1 had logged only `battles=3` with no names, which could
not confirm or refute anything; the fix was an INSTRUMENT, not a rewording.

⇒ ⛔ **"FOUR UNAVOIDABLE" IS REFUTED AS A MAP FACT.** It is a property of *a pathfinder that cannot
climb waterfalls* — and the exact membership match makes that the near-certain cause of the original
figure. **Never hardcode it.**

✅✅ **AND WE ALREADY HAVE THE LEVER — MEASURED, NOT ASSUMED (`--driver ch23b2fprobe`, 2026-09-04):**
`knows_waterfall = True`. **Wailord#FA51ECF3 carries `['Dive', 'Surf', 'Water Spout', 'Waterfall']`**
(§Ch23 leg 1 taught it), Sceptile carries `Rock Smash` + `Strength`, and Zigzagoon carries Surf too.
⇒ **leg 7 faces ONE forced fight, not four.**

**Julie — the one unavoidable fight.** Her row-22 corridor is exactly x33–34 (walled at x32, occupied
at x35), forced in *every* scenario and for *every* exit warp:
**Sandslash 42 · Ninetales 42 · Tropius 42**, IV 100, full AI, one Full Restore.
⇒ Against Sceptile L53 / Swellow L47 / Wailord L47 / Mightyena L47 this is favourable: **Wailord's
Surf is 2× on Sandslash and Ninetales; Swellow's Flying is 2× on Tropius.** The Full Restore costs
turns, not HP.

⚠ **THE HAZARD THE FIRST RECON SENSED BUT MIS-EXPLAINED (third correction to the same claim; see
§0).** Dianne (25,18) and Felix (25,21) share **both** sight tiles (25,19) and (25,20), and
`CheckForTrainersWantingBattle` accumulates `gNoOfApproachingTrainers == 2` — one step there fires
**BOTH, back to back, with no field access between them.** Real and specific, but **two single
battles, not a double** — and on the Waterfall route it never fires at all.

⚠ **Three corrections to the trainer data itself:** **Owen's sight range is 4, not 2**; **no trainer
on this map uses an alternating `FACE_*` variant** (all six are fixed-direction); and there is a
**7th object event — an item ball (Full Heal) at (13,8)** — not a trainer, but it **occludes LOS**.

**Sight tiles (computed twice, agreeing):** Vito (15,7)(15,8) · Owen (43,10)–(43,13) ·
Caroline (2,18)(2,19) · Julie (33,22)(34,22) · Dianne (25,19)(25,20) · Felix (25,20)(25,19).

**If a Surf-only route is ever forced** (it should not be), the added fights are Caroline
(Skarmory 43 / Sableye 43, IV 100) and Dianne + Felix — both of whom are **IV 0 with `aiFlags = 0`**
(random move choice) and two moves each. ‼ **Felix's Medicham has only Psychic, which does nothing at
all to Mightyena** (Dark is immune, and hits back 2×). The two genuine problems there are **Lanturn's
Thunderbolt, 2× on BOTH Wailord and Swellow** (lead Sceptile — Electric resisted, Grass 2× back), and
**Skarmory, which nothing in our party hits super-effectively** (best answered by Wailord's special
Surf into its weak 65 Sp.Def rather than anything physical into Def 140).

## 4d. ✅✅ THE RETURN LEG IS VERIFIED LIVE TOO — `--driver ch23retprobe`, OBSERVE ONLY, 2026-09-04

Run from `post_b2f.ss1`, which sits exactly where leg 8 begins (B1F **(17,16)**, the B2F landing).
`ACCEPTANCE: PASS`, all 5 readings, **`battles=0`, `whiteouts=0`, nothing moved or pushed.**
‼ That fixture is 38% HP with three fainted — fine here *precisely because* this probe fights nothing.

| §4's claim (MODELED) | measured against OUR planner |
|---|---|
| trap boulder **`local_id 6` at (21,25)** | ✅ present, exactly there |
| rock **`local_id 11` at (20,25)** | ✅ present |
| the 1F ladder **(20,21)** is blocked by the plug | ✅ **UNREACHABLE** |
| smash standpoint **(19,25)** reachable, ~15 steps | ✅ **REACHABLE, 15 wp** — the step count matches |
| push standpoint **(20,27)** reachable | ✅ **REACHABLE, 18 wp** |
| apron **(21,21)** lies behind the plug | ✅ **UNREACHABLE** |
| **(20,21)** is a ladder | ✅ `Ladder`, coll 0, elev 3 |

⭐ **The plug tiles are all `Cave`, collision 0, elevation 3** — (20,25), (21,26), (21,25), (20,26).
⇒ the tiles are walkable; it is the **OBJECTS** on them that block, which is why `strength_push` and
`_smash_rock` (both keyed on `local_id`) are the right instruments and a tile-collision check is not.

⭐ **`(22,25)` — the tile east of the trap boulder — is ALREADY UNREACHABLE**, and `(20,12)` is on a
different island. ⇒ consistent with §4's "B1F is SEVEN walk-islands, not three".

⭐⭐ **AND THE WARP-RESET IS CONFIRMED A THIRD TIME, FROM A NEW DIRECTION.** Leg 6's boulder
`local_id 4` is back at **(9,10)** and its rock `local_id 10` back at **(18,12)** — restored even
though we returned via **B2F**, not by re-entering B1F from 1F. ⇒ the reset is a property of the WARP,
not of any particular door. ⛔ Leg 8 must therefore re-solve the plug on every entry, exactly as leg 6
re-solves its own.

⚠ **HONEST LIMIT:** `local_id 5` (the boulder the recon says to push NORTH at (20,26)) is **NOT in
the visible list** — (20,26) is ~10 tiles from (17,16), at the edge of the camera window. **That is
NOT evidence it is absent**; `get_map_objects()` is a window, not a census. Confirm it from an
adjacent standpoint before the push.

✅✅ **SUPERSEDED 2026-09-04 — LEG 8 SHIPPED AND ALL OF THIS WAS DRIVEN.** `--driver ch23return`, `ACCEPTANCE: PASS`, `battles=2`, `whiteouts=0`; the plug solve is legible in the run's own report (rock 11 smashed → boulder 5 **(20,26)→(20,25)** → rock 12 smashed → ladder open, **trap boulder 6 never moving**), and the `TRAPPUSH` arm PROVED the trap by pushing 6 to (22,25) and sealing the route. ⇒ **read `03-PUNCH-LIST.md` `#24-ch23victoryroad` and the handoff queue for live status, not this paragraph.** Kept as the pre-build record:

⛔ *(WAS) STILL OWED FOR LEG 8 — the arms that involve actually MOVING something:* the smash at (20,25),
the **NORTH** push of boulder 5 at (20,26) *(the recon's whole point: pushing boulder 6 at (21,25)
EAST is its ONLY legal push and it BRICKS the route, so ordering the solve to push 5 first makes the
trap physically unreachable)*, the second smash at (21,26), and then (20,21) becoming REACHABLE.
‼ **An A/B with only its negative arm run is not an A/B** — that is the same debt leg 6 cleared.

## 5. ⛔ WHAT MUST BE MEASURED BEFORE LEG 7 IS BUILT

Legs 5 and 6 both shipped clean because every load-bearing value was driven first. Leg 7 has **no
live recon at all** yet. In priority order:
1. ✅ **DONE 2026-09-04 — `#24-waterfalltimeout` is FIXED** (`[0][1]` → `[1][1]`, direction measured first; sandbox only). ⭐ This note's prediction was right: `ch23b2fprobe` measured `{Surf: 1, Waterfall: 1}` on the route to the exit. ⚠ Still unexercised on a live traversal.
2. **The trainer load, not a double battle.** `(25,19)`/`(25,20)` sit in both Dianne's and Felix's
   cones, giving **two consecutive SINGLE battles** (§0 — the "double battle" reading was refuted).
   Confirm the party survives four unavoidable fights with no heal between them.
3. ✅ **DONE (§4b).** `calculate_path` emits `Surf` on the way to `(33,16)` and `Surf`+`Waterfall`
   on the way to `(6,10)` and the exit apron. ⛔ Still owed: that the bot ACTUALLY MOUNTS when driven
   — a plan containing a Surf waypoint is not a mount performed.
4. ⚠ **PARTLY DONE (§4b).** `(7,11)` is confirmed `Waterfall`, elev 1, with Ocean Water above and
   below, and our planner emits a `Waterfall` action. ⛔ Still owed: DRIVING it and watching the
   slide end at `(7,14)`.
5. ✅ **DONE (§4b) — and both agents were right.** (18,12) and (19,13) are each 63 wp. Pick one.
6. ✅ **DONE (§4b).** `(40,19)` is Cave elev **0** and `(6,18)` is Impassable North elev **0** —
   both confirmed as elevation-0 transition tiles, and our planner routes across them.

## 6. ‼‼ A PROCESS GAP THIS NOTE EXPOSED — READ BEFORE TRUSTING THE NEXT RECON ROUND

The workflow that produced this note ran **19 agents with an adversarial verifier on each recon
angle** and reported **0 errors**. It still shipped a **false, decomp-checkable, one-grep-away
claim** (the "double battle"), which then propagated **unhedged into `04-HANDOFF.md`** — a
current-state file — before a Tier 1 reviewer caught it.

⛔ **THE CAUSE IS IN THE WORKFLOW'S OWN DESIGN, NOT IN THE AGENTS.** The verify stage was written as:

```js
const risky = res.findings.filter(f => f.load_bearing && f.tag !== 'READ')
```

⇒ **claims the agent tagged `READ` were EXEMPTED from verification**, on the theory that a citation
is self-proving. **But the tag is SELF-REPORTED.** An agent that synthesises a conclusion and labels
it `READ` buys itself an exemption from the only check that would have caught it. ⇒ *the verification
layer was strongest exactly where it was least needed, and absent where a mistake was most likely.*

**Rules for the next recon round:**
1. ⛔ **NEVER EXEMPT A CLAIM FROM VERIFICATION ON THE STRENGTH OF ITS OWN SELF-REPORTED TAG.** Verify
   by *consequence* — anything a builder would ACT on — not by how the author graded themselves.
2. ⛔ **A SYNTHESIS IS NOT A READ.** "Both trainers face each other, therefore double battle" is an
   INFERENCE wearing a citation's clothes. The cited files were real; the conclusion drawn from them
   was not in them.
3. ‼ **"N agents, 0 errors" IS A THROUGHPUT NUMBER, NOT A CONFIDENCE ONE.** It says every agent
   returned, not that anything is true. This project already knows agreement is not a confidence
   signal; *"0 errors"* is a weaker signal still.

