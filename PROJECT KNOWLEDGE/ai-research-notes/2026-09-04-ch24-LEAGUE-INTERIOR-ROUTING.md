# §Ch24 — THE POKÉMON LEAGUE INTERIOR: routing, warp kinds, triggers, and the endgame

**Date:** 2026-09-04 · **Status:** ⚠ **AGENT NOTE — NOT TRUTH.** Decomp-cited throughout, and two
independent binary decodes agreed byte-for-byte, but **nothing here has been confirmed in our own
harness.** Per `00-READ-THIS-FIRST.md`, the authoritative doc wins on any contradiction until a claim
is verified live. Verify anything code will depend on.
‼ **AND THIS NOTE HAS ALREADY HAD ITS HEADLINE FINDING REFUTED ONCE** — §0c claimed an unrecoverable
softlock; reading the decomp directly disproved it. Read §0c's refutation before trusting any other
section, and treat the confidence of the original wording as a warning about the rest.

**Why this note exists:** §Ch24 is a **one-way gauntlet with no save-scumming and no nurse**. Getting
the routing wrong costs a full five-fight run, so it was mapped from the decomp before any code.

---

## ⛔⛔⛔ 0. THE THREE FINDINGS THAT CHANGE WHAT WE BUILD

### 0a. THE GAUNTLET IS STRICTLY ONE-WAY — the bot physically cannot retreat

Every **backward** warp in the chain sits on an `MB_NORMAL` tile. Verified in
`src/field_control_avatar.c`, all three warp paths reject `MB_NORMAL`:

| kind | line | requirement |
|---|---|---|
| step-on | `:155` → `TryStartWarpEventScript:702` | `IsWarpMetatileBehavior:751` |
| arrow | `:164` → `TryArrowWarp:688` | behavior read at the **player's own** tile |
| door | `:170` → `TryDoorWarp:833` | `DIR_NORTH` **and** `MetatileBehavior_IsWarpDoor` (`metatile_behavior.c:220`, `MB_ANIMATED_DOOR` only) |

⇒ **A warp event on an `MB_NORMAL` tile is DESTINATION-ONLY. It never fires.** This is the single
most important routing fact in the chapter.
⇒ **The moment the bot steps on lobby tile (9,1) it is committed to all five battles or a white-out.**

### 0b. ‼ THE ELITE FOUR MUST BE TALKED TO. THE CHAMPION MUST NOT.

**This is the biggest behavioural gotcha, and the two halves are opposites.**
- **Sidney / Phoebe / Glacia / Drake:** there are **no `coord_event`s** in any E4 room, and each
  trainer object is `trainer_type: TRAINER_TYPE_NONE`, `sight: 0`. The fight lives in the object's
  **interaction** script (`EverGrandeCity_SidneysRoom_EventScript_Sidney`, `scripts.inc:45-53` →
  `trainerbattle_no_intro TRAINER_SIDNEY`). ⇒ **the bot must walk up and press A.**
- **Wallace:** `EverGrandeCity_ChampionsRoom_OnFrame`, gated on `VAR_TEMP_1 == 0` (temp vars clear on
  every map load — `event_data.c:39-48`), auto-walks the player and enters
  `trainerbattle_no_intro TRAINER_WALLACE` (`scripts.inc:23-43`). ⇒ **no input starts it.**

⇒ A single "press A at the trainer" routine is wrong for Wallace, and a single "wait for the battle"
routine is wrong for the other four.

### 0c. ⛔ A MID-GAUNTLET WHITE-OUT WIPES ALL GAUNTLET PROGRESS AND HALF THE MONEY

**‼‼ THIS SECTION ORIGINALLY CLAIMED AN UNRECOVERABLE SOFTLOCK. THAT CLAIM IS REFUTED — I READ THE
DECOMP MYSELF. The refutation is kept in place of the claim, because the reasoning is the useful
part.**

**WHAT ACTUALLY HAPPENS** (`data/event_scripts.s`, read directly, not relayed):

```
EventScript_WhiteOut::
	call EverGrandeCity_HallOfFame_EventScript_ResetEliteFour
	goto EventScript_ResetMrBriney
	end

EverGrandeCity_HallOfFame_EventScript_ResetEliteFour::
	clearflag FLAG_DEFEATED_ELITE_4_SIDNEY
	clearflag FLAG_DEFEATED_ELITE_4_PHOEBE
	clearflag FLAG_DEFEATED_ELITE_4_GLACIA
	clearflag FLAG_DEFEATED_ELITE_4_DRAKE
	setvar VAR_ELITE_4_STATE, 0
	return
```

⇒ **A white-out CLEARS all four defeat flags and RESETS `VAR_ELITE_4_STATE` to 0.** Therefore on
re-entry `FLAG_DEFEATED_ELITE_4_SIDNEY` is **unset**, Sidney's `OnLoad` `call_if_set` does **not**
fire `_ResetAdvanceToNextRoom`, and the room is in its ordinary, enterable state. **There is no
box-in. There is no softlock.**

**THE REAL CONSEQUENCE, WHICH IS STILL SEVERE:**
- **A loss anywhere in the gauntlet sends the bot back to SIDNEY.** No partial credit — beating four
  and losing to Wallace forfeits all four.
- **`DoWhiteOut` also halves the money** (`overworld.c:358-366`, `SetMoney(money / 2)`).
- Respawn is **EVER_GRANDE_CITY (18,6)** (`heal_locations.json:117-122`) — the lobby door, which at
  least means the retry is a short walk, and the party comes back healed.
⇒ **DESIGN CONSEQUENCE: §Ch24 IS ALL-OR-NOTHING.** There is no resumable mid-gauntlet state to
checkpoint, so the chapter's completion predicate is `FLAG_SYS_GAME_CLEAR` and nothing finer. Items
consumed are consumed; a retry needs the bag restocked, at half the money.

**⭐⭐ HOW THIS WAS CAUGHT, BECAUSE THE METHOD IS THE TRANSFERABLE PART.** Two independent research
agents were asked different questions and **contradicted each other while citing the same lines**
(`event_scripts.s:628-634`): one concluded the flags *persist* (and built the softlock prediction on
it), the other that a white-out *clears* them. ⇒ I read the source. The persist reading was wrong: it
saw the `ResetEliteFour` label and the Champion's use of it, and missed that **`EventScript_WhiteOut`
`call`s the very same label** three lines earlier.
‼ Note also that **our own `04-HANDOFF.md` already recorded the correct behaviour** — *"a whiteout
ANYWHERE in Hoenn runs `ResetEliteFour`, wiping all four flags"* — so the existing documentation beat
the fresh research, exactly as the standing rule predicts.
⇒ **DISAGREEMENT IS THE CHEAPEST BUG-FINDER AVAILABLE.** Had both agents agreed on the softlock, it
would have been believed and coded around — and *agreement is not a confidence signal.* The lesson is
not "agents are unreliable"; it is **ask overlapping questions on purpose, then adjudicate the seam
against primary source.**

---

## 1. THE MAP CHAIN — ‼ HALL5 COMES FIRST, NOT HALL1

The hall numbering is **not** traversal order.

| # | `MAP_*` constant | notes |
|---|---|---|
| 1 | `MAP_EVER_GRANDE_CITY` | the bot is here, (18,6) |
| 2 | `MAP_EVER_GRANDE_CITY_POKEMON_LEAGUE_1F` | nurse + mart + **2 door guards** |
| 3 | `MAP_EVER_GRANDE_CITY_HALL5` | ⇐ **not Hall1** |
| 4 | `MAP_EVER_GRANDE_CITY_SIDNEYS_ROOM` | |
| 5 | `MAP_EVER_GRANDE_CITY_HALL1` | |
| 6 | `MAP_EVER_GRANDE_CITY_PHOEBES_ROOM` | |
| 7 | `MAP_EVER_GRANDE_CITY_HALL2` | |
| 8 | `MAP_EVER_GRANDE_CITY_GLACIAS_ROOM` | |
| 9 | `MAP_EVER_GRANDE_CITY_HALL3` | |
| 10 | `MAP_EVER_GRANDE_CITY_DRAKES_ROOM` | |
| 11 | `MAP_EVER_GRANDE_CITY_HALL4` | **11×34**, 31 tiles of walking |
| 12 | `MAP_EVER_GRANDE_CITY_CHAMPIONS_ROOM` | Wallace |
| 13 | `MAP_EVER_GRANDE_CITY_HALL_OF_FAME` | |

`..._POKEMON_LEAGUE_2F` exists but is the **Union Room / Cable Club** — not part of the gauntlet.
Halls 1/2/3/5 share `LAYOUT_EVER_GRANDE_CITY_SHORT_HALL` (11×13); all four E4 rooms are
collision-identical 13×14.

⚠ `include/constants/map_groups.h` **does not exist in the repo** — it is generated at build time.
The source of truth is `data/maps/map_groups.json:281-297`.

---

## 2. WARPS AND THEIR KINDS

| map | warp | coord | elev | → dest | KIND |
|---|---|---|---|---|---|
| EVER_GRANDE_CITY | 0 | (18,5) | 0 | LEAGUE_1F w0 | **(c) ANIMATED DOOR** `MB_ANIMATED_DOOR` (0x69), collision 1 — stand (18,6), face N, **hold** Up |
| LEAGUE_1F | 0,1 | (9,11),(10,11) | 3 | EVER_GRANDE | **(b) SOUTH ARROW** `MB_SOUTH_ARROW_WARP` (0x65) — stand ON it, hold Down |
| LEAGUE_1F | 2,3 | (9,1),(10,1) | 3 | HALL5 w0 | **(a) STEP-ON** `MB_NON_ANIMATED_DOOR` (0x60) |
| LEAGUE_1F | 4 | (1,7) | 4 | LEAGUE_2F | `MB_UP_ESCALATOR` (step-on) — ⛔ not our route |
| HALL5 | 1 | (5,2) | 0 | SIDNEYS_ROOM | **(a) STEP-ON**, open as authored |
| HALL5 | 0,2,3 | (5,12),(4,12),(6,12) | 3 | LEAGUE_1F | ⛔ **NONE** — `MB_NORMAL`, destination-only |
| E4 ROOM | 1 | (6,2) | 0 | next hall | **(a) STEP-ON** — *only after victory* |
| E4 ROOM | 0 | (6,13) | 3 | prev hall | ⛔ **NONE** — `MB_NORMAL` |
| HALL1/2/3 | 1 | (5,2) | 0 | next room | **(a) STEP-ON** |
| HALL4 | 1 | (5,2) | 0 | CHAMPIONS_ROOM | **(a) STEP-ON** |
| CHAMPIONS_ROOM | 1 | (6,2) | 0 | HALL_OF_FAME | opens on victory but **unused** — the script force-warps |

Elevation never blocks: every forward warp is `elevation: 0` = `ELEVATION_TRANSITION`.

---

## 3. THE DOOR-SEALING MECHANIC

**`setmetatile` and nothing else** — no object, no moving script.
`data/scripts/elite_four.inc:19-29`:

```
PokemonLeague_EliteFour_EventScript_WalkInCloseDoor::
	applywaitmovement LOCALID_PLAYER, Common_Movement_WalkUp6
	playse SE_TRUCK_DOOR
	setmetatile 5, 12, METATILE_EliteFour_EntryDoor_ClosedTop, TRUE
	... (5,6,7 × 12,13 — all six) ...
```

The 4th arg is `impassable` (`asm/macros/event.inc:1345`); `ScrCmd_setmetatile`
(`scrcmd.c:2044-2047`) ORs `MAPGRID_IMPASSABLE` (0x0C00). ⇒ (6,13) `0x3234` → `0x3E0E`.

- **Gating var:** `VAR_ELITE_4_STATE` (`vars.h:176`, 0x409C, **saved**). Sidney 0→1, Phoebe 1→2,
  Glacia 2→3, Drake 3→4, each via `MAP_SCRIPT_ON_FRAME_TABLE`. `ON_LOAD` re-applies the seal on
  every map load.
- **The forward door opens AUTOMATICALLY on victory** — no walking into it.
  `..._SetAdvanceToNextRoomMetatiles` (`elite_four.inc:1-17`) runs inside `_Defeated`, setting (6,1)
  and (6,2) passable and calling `special DrawWholeMapView`. The tile becomes `0x345`, behavior
  `0x60` `MB_NON_ANIMATED_DOOR` ⇒ step-on.

---

## 4. TRIGGERS, GEOMETRY, AND THE GUARDS

**Room geometry (identical in all four):** arrive (6,13) → `Common_Movement_WalkUp6`
(`movement.inc:71-78`) auto-walks the player to **(6,7)**; the member stands at **(6,5)**.
⇒ **walk north 1 to (6,6), face north, press A.**

⭐ **AFTER VICTORY THE MEMBER STAYS AT (6,5) AND BLOCKS THE STRAIGHT LINE TO THE DOOR.** Route
around, e.g. `(6,6)→(5,6)→(5,5)→(5,4)→(5,3)→(6,3)→(6,2)`. Rows y=4..8 are walkable x=2..10; y=3 is
walkable full width.

**Trainer constants** (`include/constants/opponents.h`): `TRAINER_SIDNEY` 261, `TRAINER_PHOEBE` 262,
`TRAINER_GLACIA` 263, `TRAINER_DRAKE` 264, `TRAINER_WALLACE` 335.

**⛔ THE DOOR GUARDS ARE A REQUIRED STEP.** `..._PokemonLeague_1F_OnTransition` (`scripts.inc:9`)
calls `GuardsBlockDoor` while `FLAG_ENTERED_ELITE_FOUR` (0x107) is unset, `setobjectxyperm`-ing two
guards onto **(9,2)/(10,2)** — directly under the warp tiles. ⇒ **stand (9,3), face north, press A**;
they step aside to (8,2)/(11,2) and the flag is set **permanently** (`:59-70`). Only
`FLAG_BADGE06_GET` is actually checked (`:57`).
‼ This RECONCILES with `04-HANDOFF`'s standing warning *"never press A at the guards"* — that warning
was correct **for §Ch23**, where opening the gauntlet early was a hazard. For §Ch24 it is the
**required** action. ⇒ the rule is not "never"; it is **"not until §Ch24 deliberately does it."**

---

## 5. AFTER WALLACE — ‼ THE GAME SOFT-RESETS THE CONSOLE

`Task_CreditsSoftReset` calls **`SoftReset(RESET_ALL)`** (`credits.c:694-698`). **Control does not
return to the overworld.**

- **Party IS fully healed** — `HealPlayerParty()` is line 1 of `GameClear()`
  (`post_battle_event_funcs.c:21`).
- **`FLAG_SYS_GAME_CLEAR` is the real "beaten" flag** (`flags.h:1354`, set at
  `post_battle_event_funcs.c:30`). ⛔ **`FLAG_IS_CHAMPION` (`flags.h:1387`) gates only link/trade
  compatibility — it is NOT the game-clear marker.** Grade §Ch24 on `FLAG_SYS_GAME_CLEAR`.
- **Automatic save, no prompt** — `TrySavingData(SAVE_HALL_OF_FAME)` (`hall_of_fame.c:521-541`).
  Order: heal → flags → save.
- **Final position: `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F` (4,2)** (or `MAYS_`), facing south — via
  `SetContinueGameWarpToHealLocation` consumed by `CB2_ContinueSavedGame` (`overworld.c:1739-1746`),
  i.e. only **after a reboot + CONTINUE**.
- ⚠ `SetChampionSaveWarp` **sets no warp** despite its name (`save_location.c:136-139`).

---

## 6. PROMPTS AND CUTSCENES

**Inside the gauntlet there is exactly ONE yes/no, and it is the nurse.** No `MSGBOX_YESNO` and no
`multichoice` anywhere in `EverGrandeCity_*`, `elite_four.inc`, or `hall_of_fame.inc`. The guard, all
five battles and the Hall of Fame are plain `MSGBOX_DEFAULT` ⇒ **A-mashing is correct there.**

**After the gauntlet, three things break a naive A-loop:**
1. **A hard blocking A-press** ends the Hall of Fame — `Task_Hof_ExitOnKeyPressed` waits indefinitely
   for `A_BUTTON` only (`hall_of_fame.c:730-737`).
2. **Credits are unskippable and, on a FIRST clear, cannot even be sped up** — the B-button 2×
   speedup (`credits.c:349-357`) is gated on `gHasHallOfFameRecords`, **FALSE** on first entry.
   ~2.5–4 min. ⛔ **MEASURE IT, do not hardcode.**
3. ⛔ **THE LATIAS/LATIOS MULTICHOICE.** The Hall of Fame arms the S.S. Ticket event
   (`hall_of_fame.inc:21,57-61`), and the player's-house **1F** has an OnFrame keyed on it
   (`LittlerootTown_BrendansHouse_1F/scripts.inc:49-55`). The first step onto 1F fires a cutscene
   ending in `multichoice ... MULTI_TV_LATI, TRUE` — **`ignoreBPress = TRUE`, so it MUST be
   answered** (`players_house.inc:446-450`). **A-mashing picks index 0 = RED = LATIAS, permanently**
   (`roamer.c:84-90`). The bedroom (2F) itself is safe.

---

## 7. UNVERIFIED / COULD NOT DETERMINE

1. ✅ ~~The mid-gauntlet white-out softlock~~ — **REFUTED from primary source, see §0c.** It was
   this note's headline finding and it was wrong. What replaced it (a white-out costs the WHOLE
   gauntlet plus half the money) is confirmed in the decomp but still not driven live.
2. **The Hall of Fame floor decodes to `MB_ICE` (0x20)** on every tile including (7,11). Both decodes
   agree, unexplained. Not load-bearing (the room is fully scripted and the Champion's script
   force-warps with `warp MAP_..._HALL_OF_FAME, 7, 16`).
3. **Credits duration in frames** — estimated, not simulated.
4. ⚠ **Whether our harness survives `SoftReset(RESET_ALL)`** (BIOS SWI 0x00). The decomp cannot
   answer this; **it is the biggest integration risk in the endgame path.**

---

## 8. ‼ A TOOLING TRAP THAT NEARLY POISONED THIS REPORT

**`gh api <binary> --jq '.content' | base64 -d` CORRUPTS BINARY in this environment** — bytes ≥0x80
come back UTF-8-expanded. `SidneysRoom/map.bin` decoded to 376 bytes instead of 364; `Hall4` to an
**odd** 1085 instead of 748. ⛔ **The corrupted grids look plausible but are wrong.**

⇒ **Use `urllib` against `raw.githubusercontent.com`, and ASSERT `len(raw) == width * height * 2`
before decoding.** ⭐ The assertion is the whole defence: a length check is cheap, total, and turns a
silent wrong-answer into a loud failure. *(Added to the playbook.)*

---

## 9. CONFIRMED AGAINST OUR EXISTING RECORD — nothing contradicted

Independently re-checked: `src/data/wild_encounters.json` has exactly **one** matching entry,
`MAP_EVER_GRANDE_CITY` (water + fishing only) ⇒ **no interior League map has any encounter table.** ✓
The items-legal (`battle_main.c:4221-4239`) and balls-blocked (`battle_script_commands.c:9915`)
claims were **not** re-derived by this pass — nothing conflicting was found, which is weaker than
confirmation and is recorded as such.
