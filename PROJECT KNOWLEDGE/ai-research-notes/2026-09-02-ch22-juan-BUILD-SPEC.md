# §Ch22 — GYM 8, JUAN (SOOTOPOLIS): RECON + BUILD SPEC (recon done, build NOT started)

> ‼ **THIS IS A NOTE, NOT TRUTH** (`00-READ-THIS-FIRST.md`) — with the same exception as the §Ch21
> wiring note: a **✅** marks a claim I re-opened the source and confirmed MYSELF. Everything else is
> a note. Produced 2026-09-02 by a 6-agent workflow (4 recon angles → adversarial refuter →
> synthesis), run `wf_f5458755-890`. The refuter decoded `map.bin` and `metatile_attributes.bin`
> itself rather than trusting the recon, and **overturned seven claims — including one of MINE.**

---

## §0. WHAT THE REFUTER KILLED (read before trusting any earlier §Ch22 statement)

| # | Claim | Reality |
|---|---|---|
| W1 | **MINE, in `04-HANDOFF.md` + a commit message: "the party arrives with one member FAINTED, lead 25/115."** | ✅ **FALSE for the fixture.** `post_hm07.ss1` is **six alive at 629/694 (91%), lead 52/115**. The fainted-Zigzagoon/25-115 party is the **chapter drive's END state** from a *different* run (`post_ch20.ss1` → legs 1-5), which was never captured to a fixture. I wrote one fixture's story onto another. See `08-MISTAKES.md`. ⚠ **BOTH states are real and §Ch22 must handle the WORSE one** — a live §Ch21 handover is chipped harder than the pinned fixture suggests. |
| W2 | "KI-73 / `_live_collision_grid` is the central risk and the oracle here." | ✅ **THE OPPOSITE — IT IS A FALSE NEGATIVE BY CONSTRUCTION.** See §2; this is the single most dangerous item in the note. |
| W3 | "Whiscash's Earthquake is neutral on everything except Castform." | **Inverted.** Ground→Flying is NO EFFECT, so **Swellow is IMMUNE** — it is the free switch-in the fight actually offers. Castform is pure Normal and takes it neutrally. |
| W4 | "a fall from section C costs up to 8 gym-trainer battles." | **10**, not 8. |
| W5 | "X Attack ×2 → Leaf Blade ~68/turn is the one lever." | **Leaf Blade is SPECIAL in Gen 3** (`IS_TYPE_SPECIAL(moveType) = moveType > TYPE_MYSTERY(9)`, Grass = 12). X Attack is INERT on it; its only real targets here are Swellow's Aerial Ace and Mightyena's Take Down. |
| W6 | Poké Center warp at (43,32). | **(43,31)** (`map_data.py:1544`); (43,32) is the apron tile in front. ⚠ Both are correct in context — a "can continue" path check must target the APRON, because pathing to a door warp ends you INSIDE. |
| W7 | the 40-frame stair-unlock window could shove the bot onto `MB_SLIDE_SOUTH`. | **Resolves SAFE**: an ON_FRAME match makes `DoCB1_Overworld` call `LockPlayerFieldControls()` and skip `PlayerStep()`, so the avatar is frozen for the `delay 40`. It only means a held D-pad is swallowed — which `_bounded_step` already tolerates. |

---

## §1. ⛔ SUPERSEDED — **THE FIGHT IS WINNABLE: THE PARTY WON IT FIRST TRY, AND 4 TIMES OUT OF 4.**

✅✅ **MEASURED 2026-09-03: THE PARTY *WON*, FIRST TRY** (`--driver ch22juan`, `BADGE08_GET`=True, `city_state=6`, `BattleOutcome.Won`, 5/6 survivors, `frames=32891`). ⛔ **THE "NOT WINNABLE" CLAIM WAS A DAMAGE CALCULATION, NOT A MEASUREMENT, AND IT WAS WRONG.** ✅✅ **AND IT IS NOW SAMPLED: 4 WINS OUT OF 4** — control plus three independent RNG draws (`POKEBOT_CH22JUAN_JITTER` 181/1013/47; frames 32891/25508/21386/24565, all `BattleOutcome.Won`, all 5/6 survivors). ⛔ *(This sentence read "ONE WIN IS NOT A RELIABILITY MEASUREMENT … treat a boss fight as stochastic until sampled" — a caveat that was discharged in the same round that wrote it, in the very file `04-HANDOFF.md` sends readers to. A Tier 1 re-check caught it. ⇒ **when an item raises a caveat AND discharges it, grep for the caveat's own wording before committing.**)* ⚠ Still true and still worth carrying: §Ch20's Archie fight is 2W/1L, so a re-run's LOSS is a RESULT, not a defect.

> ⛔ **THIS SECTION'S HEADLINE READ "THE FIGHT IS NOT WINNABLE BY THE MEASURED
> PARTY" AND IT WAS WRONG.** Every TYPING fact below is correct and verified — Kingdra really is
> Water/Dragon, Grass/Electric/Ice really are all neutral, Juan really does restore it three
> times — but the CONCLUSION drawn from them was a 1v1 damage calculation, and the live battle
> is not a 1v1. ⇒ **correct premises do not license a conclusion that only a measurement can
> settle.** Kept in full below because the typing analysis is still the right input to any
> future re-balancing.

### The original (correct) typing analysis, and its (wrong) conclusion

Juan (`src/data/trainers.h:3268-3278`, `trainer_parties.h:3577-3613`): Luvdisc 41, Whiscash 41,
Sealeo 43, Crawdaunt 43, **Kingdra 46 @ Chesto Berry** (Water Pulse / Double Team / Ice Beam /
**Rest**), all IVs 30, plus **2× Hyper Potion** in the trainer's `.items`.

⛔ **KINGDRA IS WATER/DRAGON, AND THAT NEUTRALISES THE ENTIRE PARTY:**
Grass 2.0 × 0.5 = **1.0**; Electric = **1.0**; Ice 0.5 × 2.0 = **1.0**. Only **Dragon** is 2×, and
**no party member has a Dragon move.** TM02 Dragon Claw is not in the bag and its only reachable
placement is Meteor Falls B1F — out of scope for this chapter.
⇒ *The "counters: Grass/Electric" line in `12-STORYMODE-DESIGN.md` is right about Juan's TEAM and
wrong about his ACE.*

* Kingdra derived: **HP 138**, Def/SpD/SpA 106, Spe 97.
* Sceptile L50 Leaf Blade ≈ **44–52** mid-roll ⇒ **3HKO**. Kingdra's Ice Beam into Sceptile ⇒ **2HKO**.
* Juan restores Kingdra **three times** (Rest+Chesto, then 2 Hyper Potions) ⇒ ~12 Sceptile turns
  needed; Sceptile survives 2–3. **Sceptile loses the 1v1 outright.**
* **Double Team** stacks against Leaf Blade's 100% accuracy. The only accuracy-proof damage in the
  party is **Swellow's Aerial Ace** (`EFFECT_ALWAYS_HIT`, accuracy 0) at ~29/turn — and Ice Beam is
  2× on Flying.
* Bag: **1 Potion, 0 Revives, 0 Berries.** Party mean level ≈ 38.3 against 41/41/43/43/46.

**⇒ §Ch22 IS A READINESS PROBLEM BEFORE IT IS A GYM PROBLEM.** The cheapest honest fix, using only
what the bot already owns: heal → **take the ten B1F trainers deliberately for XP** (they sit on a
map the chapter must traverse anyway) → buy healing at the Mart → grind if still short.
⛔ **The required level is UNKNOWN and must be MEASURED by a live Juan drive, never calculated.**

## §2. ⛔⛔ THE INSTRUMENT THAT WORKED ALL THROUGH §Ch21 IS BLIND HERE — AND FAILS *SILENTLY*

✅ **Verified myself, all three links:**
1. `sootopolis.py:934` — `grid[(x,y)] = (block & 0x0C00) >> 10`. Our live grid keeps **collision bits only.**
2. `src/scrcmd.c:2044-2047` — `ScrCmd_setmetatile` ORs `MAPGRID_IMPASSABLE` **only** when arg 4 is TRUE.
3. `SootopolisCity_Gym_1F/scripts.inc` — **every** gym `setmetatile` passes **`FALSE`**.

⇒ The gym's runtime tile changes never touch collision, so `_live_collision_grid` returns an
**all-zero grid** and **`probe_live_mapgrid.py` will report 0 differences and PASS** while the model
is catastrophically wrong. ⛔ **A PASS from those two instruments in this gym is a FALSE NEGATIVE BY
CONSTRUCTION — do not use them to certify anything here.**

**The correct readers:** a new `_live_metatile_grid()` returning `block & 0x03FF` (a two-line variant
of the existing helper, reusing its already-calibrated `offset = 7`), and/or
`get_event_var("ICE_STEP_COUNT")` — which exists today (`event_vars/emerald.txt` → `34 ICE_STEP_COUNT`)
and must increment by exactly 1 per step.

## §3. THE ICE PUZZLE — exact cover, and our planner cannot route it *structurally*

64 thin-ice tiles in three sections (**7 / 19 / 38**) against `setvar VAR_ICE_STEP_COUNT, 1` +
one `addvar` per unlock, thresholds **8 / 28 / 67**. The arithmetic closes exactly ⇒ **every tile
exactly once, zero revisits**, and each section has exactly one entry, so the cover is forced.

Three independent reasons `calculate_path` fails: `map_path.py:137` gates the `"Slide "` branch on
`collision != 0` but the locked stairs are collision **0**; `:351` matches `tile_type == "Ice"`
exactly so `"Thin Ice"`/`"Cracked Ice"` fall through; and it is **exact cover, not shortest path**.
The naive planner happily returns a straight walk up column x=8 into `MB_SLIDE_SOUTH`.

⇒ **Ship a PRECOMPUTED ROUTE TABLE, live-verified per step — not a runtime solver.** The puzzle input
is constant (`ClearTempFieldEventData()` wipes the visited bitmask on every map change and
`OnTransition` resets the counter, so every entry gets virgin ice). Ship the DFS as a *build-time*
generator plus a unit test that re-derives the table from `map.bin`.

## §4. ⛔ THE EXIT REQUIRES A DELIBERATE FALL — B1F IS NOT A FAILURE PATH, IT IS THE ONLY WAY OUT

With the ice walked (and therefore cracked), Juan's platform is a **20-tile island**: BFS from (8,3)
with thin ice removed reaches neither the exit warp (8,25), nor the 1F ladder (11,22), nor any ramp.
The exit is: step onto a cracked tile → `warphole` → **B1F at the same (x,y)** → traverse south →
ladder (11,22) → 1F → (8,25) → city. Every fall point (8,6)…(8,19) BFS-reaches the ladder.
‼ This is the §Ch21-leg-4 shape again — *a deliberate fall no pathfinder can propose.*
✅ And **`"allow_escaping": false` on BOTH floors** — Escape Rope / Dig / Teleport are refused.

## §5. THE FIVE LEGS (drive each separately, then assemble — the §Ch20/§Ch21 pattern)

| Leg | Does | Acceptance |
|---|---|---|
| **L1 HEAL & PREP** | (31,34) → Poké Center (43,31) → heal → shop → gym door (31,32) | every party PID present **and** `hp == total` (PID-keyed, never counts); HMs still on their carriers; path to (31,32) OK |
| ~~**L2 XP RUN**~~ ⛔ **WITHDRAWN 2026-09-03** | *(was: deliberate B1F descent, clear the 10 trainers, exit (11,22), re-heal)* | ⛔ **THIS LEG MUST NOT BE BUILT.** The Juan victory script `settrainerflag`s all ten B1F trainers itself, so post-badge the descent is battle-free — and the party wins Juan 4/4 without any XP. Both premises for this leg are gone: see `2026-09-03-ch22-CHAPTER-ASSEMBLY-SPEC.md` §0 F1. |
| **L3 ICE WALK** | the 64-step route to (8,3) | `_at(GYM_1F,(8,3))` **and** `ICE_STEP_COUNT == 67` — assert both: the var is the action, the position is the plan |
| **L4 JUAN** | fight, take TM03 | `BADGE08_GET` **and** `SOOTOPOLIS_CITY_STATE == 6` and controllable. ⛔ Pre-check bag space — `giveitem` branches to `BagIsFull` INSIDE the badge script |
| **L5 EXIT** | the mandatory fall → B1F → ladder → city | on `SOOTOPOLIS_CITY`, badge held, **and** a live path to (43,31) |

## §6. WHAT MUST BE MEASURED BEFORE ANYTHING IS BUILT

1. **The ice floor, live** — a read-only probe using the METATILE reader (§2), not the collision one.
   Confirm 64 thin-ice tiles, the three sections, and that `ICE_STEP_COUNT` behaves as modelled.
2. **The Mart's stock and the player's money** — both UNVERIFIED; they decide whether "buy healing"
   is a real option.
3. **How under-levelled the party actually is** — a live Juan drive is the discriminator, not a
   damage calculation. Expect to LOSE the first one; that is the measurement.
4. **`train_team`'s `grass=` parameter has only ever been used on LAND tiles.** Sootopolis has no
   grass, so a Surf-encounter tile is UNVERIFIED for that helper.
