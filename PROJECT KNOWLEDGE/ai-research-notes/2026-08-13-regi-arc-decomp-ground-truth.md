# Regi arc — decomp ground truth (2026-08-13)

> ‼ **THIS IS A NOTE, NOT TRUTH.** Read `00-READ-THIS-FIRST.md` first. Produced by a Claude
> subagent reading `pret/pokeemerald` live via `gh api` (so it is TOOL-verified recall, not recall
> alone), then cross-checked in places by a second, independent adversarial agent. On any conflict
> the authoritative doc WINS until the claim is verified in our own harness.
>
> **Verification status:** the two `setmetatile` findings below were reached INDEPENDENTLY by two
> agents with matching citations, and the OUR-SIDE half (we never read `gBackupMapLayout` in
> `modules/map.py`) was verified directly by me. Everything else is UNVERIFIED IN OUR HARNESS.

## Why this note exists

Scoping the Regi arc (KI-69). It corrects several things the authoritative docs currently assert.

---

## ⛔ CORRECTIONS TO WHAT WE CURRENTLY BELIEVE

### 1. Regice is **NOT a timed wait** — it is a 36-tile perimeter lap
Emerald replaced R/S's ~2-minute wait. The R/S wait function is an **empty stub** —
`src/braille_puzzles.c:258-261`, `static void UNUSED DoBrailleWait(void) { }`, with the decomp's own
comment noting the commented-out task. The real rule (`braille_puzzles.c:281-343`):

1. Interact with the back-wall braille → sets `FLAG_TEMP_REGICE_PUZZLE_STARTED`.
2. **Every step** runs `ShouldDoBrailleRegicePuzzle()` (`field_control_avatar.c:536,565-569`).
   Stepping on a listed tile sets its bit in `VAR_REGICE_STEPS_1/2/3`; stepping on **any unlisted
   tile** sets `FLAG_TEMP_REGICE_PUZZLE_FAILED` and clears STARTED.
3. Completion needs `STEPS_1==0xFFFF && STEPS_2==0xFFFF && STEPS_3==0xF` (36 bits) **and** final
   position exactly `(8,21)`.
4. ‼ `IslandCave_OnTransition` calls `ClearSteps`, so **the lap must be done in ONE visit** —
   leaving the map resets it. **Order does not matter; the SET does. No running requirement in
   code** despite the braille text saying "RUN".

The 36 tiles (`braille_puzzles.c:17-56`, `sRegicePathCoords`):
```
(4,21)(5,21)(6,21)(7,21)(8,21)(9,21)(10,21)(11,21)(12,21)(12,22)(12,23)
(13,23)(13,24)(13,25)(13,26)(13,27)(12,27)(12,28)
(4,29)(5,29)(6,29)(7,29)(8,29)(9,29)(10,29)(11,29)(12,29)
(4,28)(4,27)(3,27)(3,26)(3,25)(3,24)(3,23)(4,23)(4,22)
```
⇒ **This is a bounded, exactly-specified walk** — closer to §Ch18's Mossdeep route than to a puzzle.

### 2. `FLAG_REGI_DOORS_OPENED` is never read INSIDE the tombs — it bricks the OUTDOOR doors
Read in exactly four places: `SealedChamber_InnerRoom`, and **`Route105`, `Route111`, `Route120`**
`OnLoad`, each `call_if_unset` a script doing
`setmetatile <x>,<y>, METATILE_General_RockWall_*, TRUE`:
Route105 `(9,19)/(9,20)` · Route111 `(29,86)/(29,87)` · Route120 `(7,54)/(7,55)`.

⇒ **The Sealed Chamber is what makes the tomb entrances physically exist**; the per-tomb puzzle
checks in `braille_puzzles.c` never test that flag. **This is a hard serial prefix.**
‼ **And the 4th argument `TRUE` sets the impassable bit in the LIVE grid only** — which our shared
map reader cannot see. **Filed as KI-74.**

### 3. `CheckRelicanthWailord` gates the SEALED CHAMBER ONLY
Three references repo-wide: `braille_puzzles.c`, `data/specials.inc:298`,
`SealedChamber_InnerRoom/scripts.inc:8`. No tomb script calls it. ⇒ **Once `FLAG_REGI_DOORS_OPENED`
is set, Wailord and Relicanth can be boxed.** Minimum viable party for that one step is **2 mons**,
`[Wailord, Relicanth]`. ‼ It uses `MON_DATA_SPECIES_OR_EGG`, so an **egg in the last slot fails**.

### 4. Reachability — less is needed than KI-69 implies
| tomb | entrance | what is actually needed to REACH it |
|---|---|---|
| ISLAND_CAVE (Regice) | Route 105 `(9,20)` | **SURF** — the whole route is water |
| ANCIENT_TOMB (Registeel) | Route 120 `(7,55)` | **nothing** — foot-reachable from the Route 121 connection; `map.json "requires_flash": false`. ‼ Flash is the PUZZLE move, not a lighting requirement |
| DESERT_RUINS (Regirock) | Route 111 `(29,87)` | **GO-GOGGLES** (an item, not an HM) — scripted sandstorm gate, `Route111/scripts.inc:189-204` |
| SEALED_CHAMBER | Route 134 dive at `(59-62,30-32)`, centre `(60,31)` | **SURF + DIVE** (Mind Badge) |

### 5. Badge gates on the puzzle moves
Rock Smash needs `BADGE03` (Dynamo); Flash needs `BADGE02` (Knuckle); **Dig needs NO badge**
(`FIELD_MOVE_DIG` is index 9 and the check is `fieldMove <= FIELD_MOVE_WATERFALL`, index 7 —
`party_menu.c:118-134, 3728-3733`). We hold all badges through 7, so none of these gate us.

### 6. Acquisition — Wailmer EVOLVES, so no 1% Wailord hunt is needed
* **RELICANTH: `UNDERWATER_ROUTE124` and `UNDERWATER_ROUTE126` ONLY**, surfing while underwater,
  slots 3+4 = **5% of encounters**, levels 30-35. ⇒ Dive is upstream of the whole arc.
* **WAILMER: Route 105 Super Rod is 100% Wailmer** across all five super-rod slots (levels 25-45).
  ⚠ Route 105 is also the Island Cave route — one trip serves both.
* **`[SPECIES_WAILMER] = {{EVO_LEVEL, 40, SPECIES_WAILORD}}`** (`evolution.h:147`). A wild Wailord
  is only Route 129 water slot 4 at **1%** — ignore it; fish a Wailmer and level it.
* ⚠ **KI-69 names the Route 118 Fisherman as the Super Rod source. A second agent says that is the
  GOOD ROD, and the Super Rod is `MossdeepCity_House3/scripts.inc:11`.** Not verified by me —
  **check before writing a fetch chapter.**

### 7. The battle — the "unrecoverable" rule, verbatim
`DesertRuins/scripts.inc:68-74` (identical in all three): only `B_OUTCOME_RAN` and
`B_OUTCOME_PLAYER_TELEPORTED` route to `Common_EventScript_LegendaryFlewAway` (no flag set,
respawns). **Everything else falls through to `setflag FLAG_DEFEATED_REGI*` — including `LOST`,
`DREW`, `MON_FLED`, `CAUGHT`, `FORFEITED`.** Level 40, `BATTLE_TYPE_LEGENDARY | BATTLE_TYPE_REGI`
(the REGI flag only changes BGM). ⇒ **A Regi battle must never reach a whiteout, and the only safe
non-catch exits are RUN and TELEPORT.** UNVERIFIED: whether a Poké Doll yields `B_OUTCOME_RAN`.

---

## MINIMUM CAPABILITY LIST (each traced to the step that needs it)

| # | capability | needed for |
|---|---|---|
| 1 | HM03 Surf (+BADGE05) | Route 134 dive spot; Island Cave; underwater 124/126 |
| 2 | HM08 Dive (+BADGE07) | dive `(60,31)`; ‼ **surface at exactly `(12,44)`**; Relicanth |
| 3 | a mon knowing **DIG** (TM28) | Sealed Chamber outer room, stand `(9/10/11, 3)` |
| 4 | **WAILORD in slot 0** | inner-room back wall |
| 5 | **RELICANTH in the LAST slot** | same |
| 5a | Super Rod → Wailmer (Route 105, 100%) | to get a Wailord at all |
| 5b | level Wailmer to 40 | evolution |
| 6 | HM06 Rock Smash (+BADGE03) | Desert Ruins `(6,23)/(5,23)/(7,23)` |
| 7 | HM05 Flash (+BADGE02) | Ancient Tomb `(8,25)` |
| 8 | GO-GOGGLES | enter the Route 111 desert |
| 9 | a 36-tile single-visit lap ending `(8,21)` | Island Cave |
| 10 | Poké Balls + a **RUN-or-TELEPORT-only** exit policy | all three L40 Regis |

**Not required:** Strength, Fly, Cut, Waterfall, Devon Scope, or Flash for lighting anything.

## ‼ WHAT TO VERIFY IN OUR HARNESS BEFORE BUILDING
1. The Route 105/111/120 `setmetatile` doors — stand there with the flag unset and confirm our
   planner routes into a wall (that is KI-74's live proof, and it is cheap).
2. The Super Rod source (Route 118 vs Mossdeep House 3) — two agents disagree.
3. The `(12,44)` single-tile dive-surface point — KI-72 says never let the planner pick it.
4. Whether the Regice lap's 36 tiles are all walkable in OUR model (this is exactly the sort of
   exact-tile walk `follow_path` does with **no collision checking**).
