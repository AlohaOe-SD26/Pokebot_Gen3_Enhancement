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

## 1. THE B2F ROUTE (MODELED — two agents converged on the same shape, 115 vs 119 steps)

B2F has `connections: null`, so the whole traverse is **ONE per-map walk** containing 2 surf mounts,
2 dismounts and a forced descent. Ordered:

| # | phase | detail |
|---|---|---|
| 1 | walk, elev 3 | `(30,25)` → E,E `(32,25)` → N,N `(32,23)` → E `(33,23)` → N×6 → **`(33,17)`**. ⚠ `(33,22)` is in **Julie's** sight cone. |
| 2 | **MOUNT SURF** | stand `(33,17)`, face **NORTH**, press A → water `(33,16)`. **The only water access from the arrival pocket.** |
| 3 | surf | `(33,16)` → N → `(33,15)` → N → `(33,14)` |
| 4 | **DISMOUNT** | N onto `(33,13)` (elev 3) |
| 5 | walk, the long circuit (~60 steps) | `(33,12)` → E `(34,12)` → N×7 → `(34,5)` → E×4 `(38,5)` → S `(38,6)` → E `(39,6)` → … → `(41,8)` → S×11 → `(41,19)` |
| 6 | elev 3→4 | W onto **`(40,19)`** — an **ELEVATION-0 TRANSITION** tile |
| 7 | walk, elev-4 trunk | `(40,19)` → W×32 along row 19 → `(8,19)`. ⛔ **`(25,19)` is in BOTH Dianne's and Felix's cones — TWO CONSECUTIVE SINGLE battles (not a double; see §0).** |
| 8 | elev 4→3 | `(8,19)` → N `(8,18)` → W `(7,18)` → W **`(6,18)`** (second elevation-0 gateway) → W×4 → `(1,18)` |
| 9 | walk | `(1,18)` → N×8 → `(1,10)` → E×5 → **`(6,10)`** |
| 10 | **MOUNT SURF (2nd)** | stand `(6,10)`, face **EAST** → water `(7,10)`. ‼ **POINT OF NO RETURN NEXT** |
| 11 | **FORCED DESCENT** | S onto `(7,11)` = `MB_WATERFALL`; the game seizes control and slides you S to `(7,14)` |
| 12 | surf | `(7,14)` → E along row 14 → `(17,12)`/`(19,14)` region |
| 13 | **DISMOUNT + ladder** | onto the apron (`(18,12)` or `(19,13)`), then **ONE explicit step** onto **`(19,12)`** `MB_LADDER` → B1F warp 1 = **`(17,16)`** |

⚠ The two agents differ on the final approach (`(18,12)` E-step vs `(19,13)` N-step). **Both are
MODELED. Measure it.**

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

⛔⛔ **THE BUG — `walking.py:227`, VERIFIED IN OUR OWN CODE 2026-09-04, filed as `#24-waterfalltimeout`:**
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

## 5. ⛔ WHAT MUST BE MEASURED BEFORE LEG 7 IS BUILT

Legs 5 and 6 both shipped clean because every load-bearing value was driven first. Leg 7 has **no
live recon at all** yet. In priority order:
1. ⛔ **Fix `#24-waterfalltimeout`** — it is in the path leg 7 will take.
2. **The trainer load, not a double battle.** `(25,19)`/`(25,20)` sit in both Dianne's and Felix's
   cones, giving **two consecutive SINGLE battles** (§0 — the "double battle" reading was refuted).
   Confirm the party survives four unavoidable fights with no heal between them.
3. **The two Surf mounts** — that `calculate_path` really emits `WaypointAction.Surf` at `(33,17)`
   and `(6,10)`, and that the bot mounts.
4. **The forced descent** — one observe-only run confirming `(7,11)` slides to `(7,14)`.
5. **The final approach to `(19,12)`** — the two agents disagree ((18,12) E-step vs (19,13) N-step).
6. The elevation-0 transition tiles **(40,19)** and **(6,18)** — our planner's elevation handling
   across them.
