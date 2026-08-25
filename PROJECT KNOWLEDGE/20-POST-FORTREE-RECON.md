# Post-Fortree story recon — decomp-verified (2026-07-26)

> Parallel decomp audits run while a live batch was going. Every claim is read out of
> `pret/pokeemerald` master with file:line evidence, NOT recalled. This file CORRECTS
> several claims in `12-STORYMODE-DESIGN.md`; where they disagree this is the later and
> better-evidenced one, but neither replaces a live probe at build time.

---

## 1. Ch14 — Route 121 / Mt. Pyre / Magma Emblem

### The existing spec was wrong in four places

| design-doc claim | reality |
|---|---|
| "Route 121 → south fork → Mt. Pyre exterior door" | **Mt. Pyre is off ROUTE 122, which is ALL WATER** (no `land_mons` entry at all). The only door is `Route122 (22,29) → MT_PYRE_1F`. **SURF IS MANDATORY** for the chapter. Without it the bot loops Route 121 hunting a door that does not exist. |
| "exterior map (24,21)" is the entrance | (24,21)/(25,21)/(26,21) are FOG coord-triggers. The real warp is **Exterior (10,42) ↔ 1F (3,6)/(4,6)**. |
| "ride the Archie/Maxie scene chain" | Wrong scene. Ch14's is `TeamAquaExits` at `VAR_MT_PYRE_STATE == 0`, triggers (22,7)/(23,7)/(24,7), sets STATE=1. **STATE=2 is set in `SootopolisCity/scripts.inc:1367` — Ch16, post-Kyogre.** A Ch14 bot must never wait on it. |
| "the old lady gives the Magma Emblem after" | She does not. It is handed out inline by the same cutscene (`MtPyre_Summit/scripts.inc:60`). |

### PERMANENT-WEDGE RISK — the most important finding here

**A full KEY ITEMS pocket silently strands the run.** `Std_ObtainItem`
(`data/scripts/obtain_item.inc:4`) sets `VAR_RESULT=FALSE` on failure, but the summit script
**never checks it** — it still runs `setflag FLAG_HIDE_JAGGED_PASS_MAGMA_GUARD` and
`setvar VAR_MT_PYRE_STATE, 1`. The `STATE==0` trigger is then dead and the Magma Emblem is
**unobtainable for the rest of that save**; the Jagged Pass door never opens.

The bot MUST assert a free Key Items slot before stepping on the y=7 trigger row.

‼ **CORRECTED 2026-07-26 (later recon, see `22-CAPABILITY-RECON.md` §C):** this hazard is
REAL but I originally over-generalised it. It applies to **`giveitem`/`Std_ObtainItem` gift
scenes ONLY** — those call `additem` with **no pre-check**. Overworld pickups are SAFE:
item balls (`finditem`/`Std_FindItem`) and hidden items both call `checkitemspace` FIRST, and
on a full bag they leave the ball in place with its flag unset, so the pickup is simply
RETRYABLE. There are **38 unchecked `giveitem` sites**, and they are concentrated in the
Key Items (cap 30) and TM/HM (cap 64) pockets — including **every single HM**.

### Confirmed
- `ITEM_MAGMA_EMBLEM` = 375, a KEY ITEM with no flag — gate on the BAG, as Jagged Pass does.
- Jagged Pass door triggers are **(13,15),(14,15),(21,15),(21,20),(22,20)** — standing at
  (16,18) does nothing. A Magma guard sits at (16,19) until the emblem hides him.
- Mt. Pyre interior 2F-6F is **entirely optional**; no interior floor reaches the exterior.
- **No ledges on Mt. Pyre Exterior** — the climb is fully reversible, so no stranding.
- All four summit grunts are **unavoidable**; Route 121 adds ~10 more incl. a DOUBLE
  (Kate+Joy, Slaking L32). Cut trees at (32,5),(65,4),(26,12) can block a straight path.
- Training bands: Route 121/123 land **L25-28**; Mt. Pyre 1F-3F L22-29, Exterior L25-29,
  Summit L24-30. Route 122 is water/fishing only.

---

## 2. Lilycove → Aqua Hideout → Route 124 — **was NOT specced at all**

`12-STORYMODE-DESIGN.md` row 17 is **factually wrong**: it describes a "room-key + Electrode
puzzle / USED_ROOM_n_KEY". Those keys belong to the **Abandoned Ship** and appear in **zero**
AquaHideout scripts. Fix that row.

### The mechanic is a pure WARP-PAD GRAPH
No keys, no switches, no vars. A pad teleports you and you land standing on a pad (it will
not re-fire until you step off). **Pad rooms are collision-islands** — movement between
regions is *only* via pads.

The bot must plan over the warp graph, never a distance heuristic. A greedy walker wedges
instantly; a naive replanner oscillates forever across a bidirectional pair.

- **Entry is NOT gated by the Magma Emblem or the Scanner.** Two grunts block the 1F stairs
  until the **Slateport Harbor sub-theft** sets their hide flags.
- Completion = beating **Matt** (Mightyena L34, Golbat L34) → `FLAG_TEAM_AQUA_ESCAPED_IN_SUBMARINE`.
- **Matt is a TWO-STEP beat**: the coord trigger at (28,16)/(28,17) only sets `VAR_TEMP_1`;
  the battle needs a separate interaction at (23,19).
- **Route 124 is physically locked until Matt falls** — `LilycoveCity_OnLoad` paints Wailmer
  metatiles over (76-78, 12-17). Do not cache Lilycove collision across that fight.
- Optional side loop yields a **MASTER BALL** (B1F 15,9) + Nugget, guarded by two wild
  **Electrode L30**.
- **Lilycove Dept Store 2F is the provisioning point**: Balls, status heals, Potion →
  **MAX POTION**, **Revive**, Repels. 3F vitamins/X-items, 4F TMs.

---

## 3. Gyms 7 and 8 — were only "SPEC SEEDS"

`badge_case.py`'s decomp-verified leader table cross-checks clean — no discrepancy.

### Mossdeep Gym — two independent mechanics
1. **Teleport pads** — six bidirectional pairs. A **trap at (21,6)** warps you back to the
   entrance; never step there.
2. **Colour-switch rotating statues** — eight floor triggers, each advancing one colour by
   one step. Every arrow group is a **2×2 counter-clockwise cycle, period 4**. Deterministic
   solve = BFS over `(player tile, per-colour phase 0-3)`, ≤4⁵ = 1024 configurations.
   **Some trainers sit on arrow tiles and move with the statues.**

**Statue state is SAVE-PERSISTENT** (`MoveRotatingTileObjects` writes
`gSaveBlock1Ptr->objectEventTemplates`), so a re-entered gym is NOT the map.json layout. The
bot must read live object positions and never assume the initial configuration.

### Sootopolis Gym — the ice floor is a HAMILTONIAN PATH
Thin ice cracks on the first step and drops you through on the second. Tile counts per
section are **7 / 19 / 38 = 64**, exactly matching the stair thresholds (8 / 28 / 67) ⇒
**every tile must be stepped exactly once**. The three paths can be precomputed and replayed.

**Progress persists in `VAR_TEMP_1..A` across falls, but `VAR_ICE_STEP_COUNT` resets to 1 on
every map transition** — so falling and re-entering can leave a section **unsolvable**.
Recovery is to exit to Sootopolis City and re-enter to clear the temp vars (VERIFY LIVE).
Falling also drops you into B1F with **eight more gym trainers**.

### Gating chain to the endgame (verified, in order)
1. Aqua sub escapes → Surf east to Mossdeep (**Surf = Badge 5**)
2. Mossdeep Gym → **Badge 7**
3. Space Center: Steven **multi battle** — reduces the party to **3** and opens a
   party-select menu; the bot needs a handler
4. Steven's House → **HM08 Dive** (**Dive = Badge 7**)
5. Route 128 dive → Seafloor Cavern (**Strength**) → Kyogre
6. **Sootopolis is entered BY DIVE** (`UNDERWATER_ROUTE126` → `UNDERWATER_SOOTOPOLIS_CITY`)
7. Cave of Origin / Rayquaza → Wallace gives **HM07 Waterfall** — obtained BEFORE the gym
   but unusable in the field until **Badge 8**. Do not route on it early.
8. **Juan** (Kingdra L46 @ Chesto, Rest/Double Team — the hardest single mon before the E4)

### Tate & Liza — a failure mode the bot WILL hit
One trainer entry, `doubleBattle = TRUE`. With fewer than **2 usable Pokémon** the script
prints `NeedTwoMons` and **no battle starts**. A bot that cannot detect "message shown,
battle never began" will **loop on the leader forever**. It must heal or withdraw a second
mon and retry.

---

## What this changes about priorities

- **`#24-provisions` is now doubly justified**: the 1:1 loss→whiteout measurement, plus the
  discovery that the Dept Store sells Max Potions and Revives at exactly this stage.
- **`#24-items` gains a hard safety requirement** — verify the item actually entered the bag,
  because the game itself does not.
- **Every remaining gym and hideout is a graph-search puzzle** (warp pads, rotating statues,
  Hamiltonian ice). None is solvable by a distance heuristic. That is one shared capability
  worth building once rather than three times — and it is the same machinery the
  "meandering pathing" work must not break.

---

## 4. SECOND-PASS FINDINGS (2026-07-26, later agents) — corrections and gaps

### 4.1 ‼ CORRECTION to §3's Sootopolis ice claim
I wrote that a fall could leave a section **unsolvable**. It cannot.
`ClearTempFieldEventData()` wipes temp **vars** as well as flags and runs on *every* warp, and
`OnTransition` hard-sets `VAR_ICE_STEP_COUNT = 1`. So a fall wipes **everything**, including
the already-opened stairs. All 64 tiles must be done in **one unbroken visit** — failure is
expensive, never a wedge.

### 4.2 ‼ Sky Pillar needs NO Mach Bike in the story — ⛔ but it is NOT free of cracked floors
⛔ **THIS HEADING READ "has NO cracked floors" UNTIL 2026-08-24 AND WAS FALSE.** `_Clean` is a
PER-FLOOR fact: `2F_Clean` has **0** cracked tiles, **`4F_Clean` has 5** — measured by decoding the
shipped `data/layouts/SkyPillar_4F_Clean/map.bin`. Worse, the ascent **REQUIRES stepping on one**:
`4F (3,1)` (the 5F stairs) and `3F (7,1)` are SEALED POCKETS, and from the `4F (11,1)` arrival the
5F stairs are unreachable **even if every cracked tile is treated as passable**. The only way in is
a deliberate fall through `4F (6,4)`/`(7,4)` — ⛔ and **NOT `(9,4)`, which lands in 3F's MAIN region
and wastes the climb.** See the §Ch21 ATLAS in `12-STORYMODE-DESIGN.md`; evidence in
`tools/story-dev/evidence/2026-08-24-skypillar-clean-reachability.txt`.
Every floor swaps to a `_Clean` layout below `VAR_SKY_PILLAR_STATE 2`
(`SkyPillar_2F/scripts.inc:6-16`). The Mach Bike is needed only for the POST-GAME Rayquaza capture.
Two places in our own docs/code said otherwise and were fixed. ⛔ **BUT THE CLAIM "are now fixed" WAS NOT TRUE OF THE
WHOLE TREE: on 2026-08-24 an independent audit found TWO MORE ROWS still asserting the Mach Bike —
`12-STORYMODE-DESIGN.md`'s Ch21 roadmap row AND its key-items row, i.e. THE TWO TABLES AN AGENT BUILDING
Ch21 OPENS FIRST.** Both are corrected now. ⇒ **A FIX-COUNT IS A CLAIM ABOUT THE WHOLE TREE; the honest
form is the `grep` you actually ran.** (Cost had it stood: an agent reads the table, concludes the chapter
is blocked, and builds a bike solver nobody needs.)

### 4.3 ‼ Ch21's completion milestone could never fire (FIXED)
`chapters.py` used `flag("DEFEATED_RAYQUAZA")`, set only inside `TryShowRayquaza`, gated on
`VAR_SKY_PILLAR_STATE >= 2` — the post-game catchable Rayquaza. The story Rayquaza is roused
in a cutscene and flies off; it is never battled. Changed to `RECEIVED_HM_WATERFALL`.
Scope: `chapters.py` feeds `progress.py` **reporting** only, so this was a reporting defect,
not a dispatch deadlock — but a wrong "current chapter" misleads every log review.

### 4.4 Seafloor Cavern boulders RESET on re-entry
`LoadObjEventTemplatesFromHeader()` re-copies from the map header on every warp-in, and
nothing ever writes boulder coords back. So a sokoban solver is needed, but a **perfect** one
is not — exit and re-enter is a sound recovery. Room 8 is the hard one (12 boulders).
Rooms 6 and 7 are **water-current mazes**, which is a different problem again.

### 4.5 Magma Hideout is MANDATORY, not optional
`MagmaHideout_4F/scripts.inc:61-63` is the ONLY setter of `VAR_SLATEPORT_HARBOR_STATE, 1`,
which arms the Slateport sub-theft, which unblocks the Aqua Hideout stairs. Skip it and the
whole rest of the game is unreachable. Jagged Pass has **zero map connections** — warp-only.

### 4.6 Space Center multi battle — corrects §3
It is **1-3 Pokémon, not exactly 3** (`GetMinBattleEntries()` = 1). ‼ And
`GetBattleEntryEligibility` rejects eggs and over-cap mons but **does NOT check HP** — a
fainted mon is selectable, which is an instant whiteout. The bot must filter on HP itself.
Cancelling the menu loops the prompt forever. On a **loss the party is restored** before the
whiteout, so a retry is safe.

### 4.7 Kyogre and Rayquaza are NOT battles in the story
No `setwildbattle` in `SeafloorCavern_Room9/scripts.inc`; Kyogre flees. Rayquaza is roused in
a cutscene. Neither is catchable during the story.

### 4.8 ‼ Dive is invisible to our reachability layer
`region_reach.py` excludes Dive/Emerge edges, `KNOWN_GATES` has no Dive entry, and
`capabilities.py` models only Surf + Rock Smash. Since `SootopolisCity` has **zero map
connections** and no inbound warp, **Sootopolis, its gym and the Cave of Origin are
unreachable nodes in the graph** — the same false-negative class the Victory Road entry was
added to fix. Dive spots are also NOT warp events: they are `MB_DEEP_WATER` metatiles, so the
bot must find them by **scanning tile behaviours**, not the warp table.

### 4.9 ‼ The biggest documentation gap: teaching HMs
The design doc has an acquisition row for all 8 HMs and **no section anywhere** on teaching
one to a party member, or on HM-slave party planning. Every HM above is unusable without it.

### 4.10 Sootopolis is the only true island
Zero map connections; entry by `setdivewarp` only. Exit needs Dive or Fly. A bot that boxes
its Dive carrier there is stranded — which is why HM carriers are on the never-randomise list.
