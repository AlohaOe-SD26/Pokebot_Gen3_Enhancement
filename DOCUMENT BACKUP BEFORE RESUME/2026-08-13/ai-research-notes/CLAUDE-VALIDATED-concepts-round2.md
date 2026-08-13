# ✅ CLAUDE-VALIDATED — concept notes ROUND 2 (2026-07-25)

**Scope:** `concept-notes-c03`, `c04`, `c06`, `c07`, `c10` — the five never-examined angles, worked
in the priority order given (c10 → c03 → c07 → c04 → c06). **`c05` and `c08` were NOT examined at
all** — see §5 METHOD.

**Ground truth used:** every ruling below cites a file I fetched and read in this session via
`gh api repos/pret/pokeemerald/contents/<path> -H "Accept: application/vnd.github.raw"`, or a file
in this repo that I opened. `pret/pokeemerald` master is a *matching* decomp (it builds a
byte-identical retail ROM; non-matching changes sit behind `#ifdef BUGFIX` / `B_*` gates, and I saw
that pattern in the very files I read), so behaviour claims from it are safe. **Names have drifted**
in some places — where the Gemini note named the wrong file, I say so, because a wrong path is how
the next agent wastes an hour.

Round 1 (`CLAUDE-VALIDATED-concepts-round1.md`) settled c01/c09/c11/c12 and spot-checked c02. I did
not redo any of it; where round 1 already ruled, I defer and say so.

---

# ‼ 1. SHIPPED-CODE IMPLICATIONS — READ FIRST

## 1.1 The Fortree re-entry reset assumption is **CORRECT**. No code change required.

`sandbox-pokebot/modules/story/early_game.py :: do_fortree_gym()` (and the identical
`custom-pokebot/modules/story/early_game.py`) recovers from an unsolvable state by walking to the
entrance warp, leaving, and re-entering. **Both halves of that assumption are now decomp-verified.**

**(a) Gate orientations reset on every warp into the gym — CONFIRMED, two independent mechanisms.**

Gate state is not stored anywhere persistent. `src/rotating_gate.c:642-658`:

```c
static void RotatingGate_ResetAllGateOrientations(void)
{
    u8 *ptr = (u8 *)GetVarPointer(VAR_TEMP_0);
    for (i = 0; i < sRotatingGate_PuzzleCount; i++)
        ptr[i] = sRotatingGate_PuzzleConfig[i].orientation;
}
static s32 RotatingGate_GetGateOrientation(u8 gateId)
{ return ((u8 *)GetVarPointer(VAR_TEMP_0))[gateId]; }
```

* The 8 Fortree gates (`sRotatingGate_FortreePuzzleConfig`, `rotating_gate.c:191-202`) are a byte
  array overlaid on `VAR_TEMP_0..VAR_TEMP_3` — exactly what our `fortree_gates.read_orientations()`
  reads. The decomp even carries a comment at `rotating_gate.c:222-227`: *"using vars that persist
  when exiting the map could softlock the puzzle"* — the reset is deliberate design.
* Mechanism 1: `LoadMapFromWarp()` (`src/overworld.c:848`) calls `ClearTempFieldEventData()`, which
  is `memset` over all 16 temp vars and all 32 temp flags (`src/event_data.c:39-48`).
* Mechanism 2: `data/maps/FortreeCity_Gym/scripts.inc` —
  `map_script MAP_SCRIPT_ON_TRANSITION, FortreeCity_Gym_OnTransition` →
  `special RotatingGate_InitPuzzle` → restores the *config defaults* (not zeros).
  `RunOnTransitionMapScript()` is called by `LoadMapFromWarp` after the temp clear.

**(b) Defeated-trainer / NPC positions reset on re-entry — CONFIRMED. The user was right.**

The chain, all read this session:

1. `LoadMapFromWarp()` → `LoadObjEventTemplatesFromHeader()` (`src/overworld.c:468-478`):
   `CpuFill32(0, gSaveBlock1Ptr->objectEventTemplates, …)` then `CpuCopy32` **from the ROM map
   header**. Any runtime template edit (`setobjectxyperm` → `SetObjEventTemplateCoords`) is wiped.
2. `LoadMapInStepsLocal()` case 3 → `InitObjectEventsLocal()` (`src/overworld.c:2163-2178`) →
   `ResetObjectEvents()` → `ClearAllObjectEvents()` (wipes live `gObjectEvents`), then
   `TrySpawnObjectEvents(0, 0)`.
3. `TrySpawnObjectEvents()` (`src/event_object_movement.c`) spawns each object at
   `template->x + MAP_OFFSET, template->y + MAP_OFFSET` read out of
   `gSaveBlock1Ptr->objectEventTemplates[i]` — i.e. its **original vanilla tile**.

So after a leave-and-re-enter the room is in the exact vanilla initial state: default gate
orientations **and** every trainer back on its starting tile. The recovery path is sound, and the
`_FORTREE_MAX_RESET_CYCLES = 2` bound is reasonable.

**Docs action (not code):** the two comments in `do_fortree_gym` that say
`‼ USER MECHANIC (2026-07-24): leaving and re-entering the gym resets NPC POSITIONS as well as the
gate orientations` can be upgraded from "user mechanic" to decomp-cited fact — cite
`overworld.c:468-478` + `overworld.c:2163-2178` + `event_object_movement.c :: TrySpawnObjectEvents`.

## 1.2 ‼ NEW RISK in the same function: `get_map_objects()` is **not** a room inventory

`do_fortree_gym` builds `blocked_tiles` from `get_map_objects()` every round. `TrySpawnObjectEvents`
(`src/event_object_movement.c`) only spawns templates inside a window around the camera:

```c
s16 left = gSaveBlock1Ptr->pos.x - 2;  s16 right  = gSaveBlock1Ptr->pos.x + MAP_OFFSET_W + 2;
s16 top  = gSaveBlock1Ptr->pos.y;      s16 bottom = gSaveBlock1Ptr->pos.y + MAP_OFFSET_H + 2;
… if (top <= npcY && bottom >= npcY && left <= npcX && right >= npcX && !FlagGet(template->flagId))
```

An object further up the room **is not in `gObjectEvents` at all** until the camera gets near it.
Consequences for our code:

* Right after entering at (15,24), `blocked_tiles` is *systematically incomplete*. The per-tile
  re-read loop already self-corrects, so this is not a live bug — but **never treat a short/empty
  `get_map_objects()` as evidence a room is clear**, in this function or any future one. (Same trap
  applies to any "is the corridor free?" pre-check elsewhere in the story bot.)
* Corollary worth encoding: if `solve()` returns `None` *immediately after a reset, standing on the
  entrance tile, with default orientations*, that is a **solver/model bug**, not a game state — the
  vanilla initial configuration is solvable by construction. That case is deterministically
  reproducible and deserves a distinct error message rather than burning the second reset cycle.

## 1.3 Repel handling in shipped code is **correct** — verified, no change

I checked because c07's observability claim was wrong (see §2, c07-8). Our
`modules/pokemon_party.py :: get_current_repel_level()` reads `get_event_var("REPEL_STEP_COUNT")`
and uses `get_party().first_non_fainted`, and `non_fainted_pokemon` filters
`not pokemon.is_egg and pokemon.current_hp > 0`. That matches `IsWildLevelAllowedByRepel`
(`src/wild_encounter.c:874-896`) exactly, including the egg exclusion and the
"first party member with HP, not literally slot 0" subtlety. `modules/map.py ::
_calculate_repel_rate_and_species_map` also treats a wild level *equal* to the repel level as
allowed, which matches `if (wildLevel < ourLevel) return FALSE;`. Nothing to fix.

## 1.4 Two flatly-wrong beliefs that would break future code if adopted from the notes

* **Do not add a "level cap" to training logic for self-caught mons.** See c03-1/2/3: self-caught
  Pokémon *never* disobey, at any level, with zero badges. An over-levelled bench is safe. (Only
  in-game-TRADE mons are capped.)
* **Do not model running shoes as an encounter-rate multiplier.** No such code exists (c07-3). Any
  XP-per-frame or encounters-per-frame table that used ×1.6 for running is wrong — the only movement
  modifier is the bike, ×0.8.

---

# 2. RULINGS

Format: claim | ruling | the actual truth | the exact source I read.
`NEW` = absent from the Gemini note and behaviour-relevant.

## c10 — failure recovery: what PERSISTS vs RESETS (priority 1)

| # | claim | ruling | actual truth | source I read |
|---|---|---|---|---|
| c10-1 | "`gObjectEvents` structs are rebuilt from `events.inc` defaults upon map load; positional changes reset unless a map script moves them" | **CONFIRMED** | Exactly right. `LoadMapFromWarp` → `LoadObjEventTemplatesFromHeader()` re-copies templates from the ROM header over the saveblock copy; then `InitObjectEventsLocal()` → `ResetObjectEvents()` (`ClearAllObjectEvents`) + `TrySpawnObjectEvents(0,0)` respawns every object at its template tile. Same for a map **connection** crossing: `LoadMapFromCameraTransition` (`overworld.c:785-822`) calls both as well. | `src/overworld.c:468-478` (`LoadObjEventTemplatesFromHeader`), `:785-822`, `:826-872`, `:2163-2178`; `src/event_object_movement.c` (`ResetObjectEvents`, `TrySpawnObjectEvents`) |
| c10-2 | *(absent from note)* | **NEW** | **Returning from a BATTLE is not a map load.** `ReturnToFieldLocal()` → `InitObjectEventsReturnToField()` → `SpawnObjectEventsOnReturnToField()`, which iterates the **live** `gObjectEvents[i].active` and re-creates sprites for them. So a defeated trainer stays parked where the approach left it for as long as you remain on the map, and only snaps back on a warp/connection. This is precisely the failure our bounded escape was written for. | `src/overworld.c:1958-1985`, `:2180-2185`; `src/event_object_movement.c :: SpawnObjectEventsOnReturnToField` |
| c10-3 | *(absent from note)* | **NEW** | `TrySpawnObjectEvents` only spawns templates inside a camera window; distant objects are absent from `gObjectEvents`. See §1.2. | `src/event_object_movement.c :: TrySpawnObjectEvents` |
| c10-4 | "Gym puzzles reset completely on map reload, handled by `ON_TRANSITION` scripts resetting specific VARs" | **CONFIRMED** (for the rotating-gate puzzles; Sootopolis ice not checked) | True and the mechanism is doubly redundant — see §1.1(a). Fortree gates live in `VAR_TEMP_0..3`; Trick House puzzle 6 uses 11 gates over `VAR_TEMP_0..5`. The Sootopolis ice-floor claim specifically I did not open → treat as UNRESOLVED. | `src/rotating_gate.c:191-216, 642-701, 933-940`; `data/maps/FortreeCity_Gym/scripts.inc`; `src/event_data.c:39-48` |
| c10-5 | *(the crisp general answer, absent from note)* | **NEW — the load-bearing table** | **Exactly two storage regions reset on a map change, and nothing else does:** temp flags `0x000–0x01F` (32 flags) and temp vars `0x4000–0x400F` (16 vars), zeroed by `ClearTempFieldEventData()`; plus that function explicitly clears `FLAG_SYS_ENC_UP_ITEM`, `FLAG_SYS_ENC_DOWN_ITEM`, `FLAG_SYS_USE_STRENGTH`, `FLAG_SYS_CTRL_OBJ_DELETE`, `FLAG_NURSE_UNION_ROOM_REMINDER`. Everything else in the save block persists — including **trainer-defeated flags** (`TRAINER_FLAGS_START = 0x500`, far outside the temp range, so re-entering never re-arms a beaten trainer) and **`VAR_REPEL_STEP_COUNT = 0x4021`** (Repel survives map changes; White/Black Flute does **not**). | `src/event_data.c:5-48`; `include/constants/flags.h:11-44, 1343-1344`; `include/constants/vars.h:4-26, 51` |
| c10-6 | Whiteout money loss "based on highest level Pokémon and a badge-dependent multiplier … `src/money.c` (`GetWhiteoutMoneyPenalty`)" — marked **VERIFIED** | **REFUTED** | Emerald simply **halves** your money. `DoWhiteOut()` is five lines: run script, `SetMoney(money / 2)`, heal, reset field flags, warp. **`GetWhiteoutMoneyPenalty` does not exist** — `src/money.c` contains only `GetMoney/SetMoney/IsEnoughMoney/AddMoney/RemoveMoney` and UI helpers. The level-and-badge payout formula is a Gen 4+ mechanic. (Matches round 1's independent reading.) | `src/overworld.c:358-366`; full function list of `src/money.c` |
| c10-7 | Whiteout friendship: "fainted Pokémon lose 1; if the opponent was ≥30 levels higher, they lose 5 (for `friendship < 200`) or 10 (for `friendship < 100`)" | **REFUTED in the magnitudes** (trigger is right) | Trigger CONFIRMED: `if (opponentLevel - ownLevel > 29) FAINT_LARGE else FAINT_SMALL`. But the bands are **inverted**: `FAINT_SMALL = {-1,-1,-1}`; `FAINT_LARGE = {-5,-5,-10}` indexed by friendship band (0 = ≤99, 1 = 100–199, 2 = ≥200). So **−10 hits the *high*-friendship mons (≥200)** and −5 hits everything below 200. Also: this fires on **every faint in battle**, not only on a whiteout, and only skips inside Frontier/Pike/Pyramid. | `src/battle_util2.c:77-107` (`AdjustFriendshipOnBattleFaint`); `src/pokemon.c:2093-2103` (`sFriendshipEventModifiers`), `:5914-…` (`AdjustFriendship`, `ShouldSkipFriendshipChange`) |
| c10-8 | Respawn = `gSaveBlock1Ptr->lastHealLocation`, in `CB2_WhiteOut` | **CONFIRMED in substance, wrong function** | `CB2_WhiteOut` waits 120 frames then calls `DoWhiteOut()`, which does `SetWarpDestinationToLastHealLocation(); WarpIntoMap();`. Note for us: **no save reload, no party rollback** (round 1's boss-training ruling stands). Because it is a *warp*, the destination map gets the full temp-var/template reset of c10-5. | `src/overworld.c:1551-1570` (`CB2_WhiteOut`), `:358-366` |
| c10-9 | *(absent from note)* | **NEW** | `Overworld_ResetStateAfterWhiteOut()` also clears `FLAG_SYS_CYCLING_ROAD`, `FLAG_SYS_CRUISE_MODE`, `FLAG_SYS_SAFARI_MODE`, `FLAG_SYS_USE_STRENGTH`, `FLAG_SYS_USE_FLASH`, and if `VAR_SHOULD_END_ABNORMAL_WEATHER == 1` it ends the Groudon/Kyogre abnormal weather. The Fly/Teleport/Dig-Escape-Rope variants clear the same five flags (Teleport additionally runs `EventScript_ResetMrBriney`). | `src/overworld.c:368-412` |
| c10-10 | "Boss defeat flags: if a whiteout occurs the script terminates before `trainerbattle` can set the flag" | **UNRESOLVED** (consistent with round 1) | I did not open `src/battle_setup.c` this pass. Round 1 independently ruled that a whiteout is the safe abort for scripted statics because the script never resumes; the same reasoning applies here, but I am not sourcing it myself. | — |
| c10-11 | Stationary legendary: "fleeing does not set the flag but hides the sprite until the map is reloaded or E4 is beaten" | **UNRESOLVED** | Not opened this pass. Round 1 already corrected the *flag semantics* (`FLAG_DEFEATED_{RAYQUAZA,…}` is also set on a successful **catch** — it means "encounter resolved"). The sprite-hiding detail is unverified. | — |
| c10-12 | Roamer retains HP/status across encounters; "if they faint they are permanently flagged as dead" | **REFUTED in the flag part** (round 1) | Round 1: the roamer sets **no flag at all** — it clears `roamer.active` (`src/roamer.c:237-239`), and it dies on **every odd `gBattleOutcome`** (WON / DREW / PLAYER_TELEPORTED / CAUGHT / FORFEITED). Use `modules/roamer.get_roamer() is not None`. HP persistence itself I did not re-verify. | round 1; not re-read here |
| c10-13 | `gBattleStruct->typeEffectiveness`, `gBattleResults.battleTurnCounter` as observables | **UNRESOLVED** | Not verified. Note that `modules/battle_state.py` already gives us types + `stats`, so the effectiveness can be computed locally without touching an internal battle struct — prefer that. | — |
| c10-14 | Traps: TM exhaustion / friendship evolution lock / EXP-leech / PP-Struggle / one-shot legendary / roamer poison / bike softlocks | mostly **design, not fact** | The TM and legendary items were settled in round 1 (TMs single-use but *evaluating* one is free; legendary flags mean "resolved"). The EXP-leech trap is confirmed by round 1's finding that EXP goes only to mons alive at the instant the opponent faints. The roamer-poison-death specific claim is unverified. | round 1 |

## c03 — roster, obedience, cheap benching (priority 2)

| # | claim | ruling | actual truth | source I read |
|---|---|---|---|---|
| c03-1 | "Badge obedience caps **ONLY** apply to Pokémon with a mismatched OT ID / Secret ID" | **CONFIRMED** | `if (!IsOtherTrainer(gBattleMons[gBattlerAttacker].otId, gBattleMons[gBattlerAttacker].otName)) return DISOBEDIENCE_OBEDIENT;` — a self-caught mon returns obedient before the badge logic is ever reached. Note `IsOtherTrainer` compares **otId *and* otName**. | `src/battle_util.c:3923-3956` |
| c03-2 | "Any Pokémon the bot catches itself will obey 100% of the time, even at Lv100 with zero badges" | **CONFIRMED** | Follows directly from c03-1. **⇒ the "army"/over-levelled-bench strategy is safe and needs no cap.** | same |
| c03-3 | "`IsMonDisobedient` in `src/battle_main.c`" | **REFUTED (wrong file)** — behaviour fine | The function lives in **`src/battle_util.c:3923`**. It is *not* in `battle_main.c` (I grepped: zero hits). | `src/battle_util.c` |
| c03-4 | *(caps not listed in the note)* | **NEW** | The actual caps, for traded mons only: `FLAG_BADGE08_GET` → fully obedient (early return); else `obedienceLevel = 10`; `BADGE02` → 30; `BADGE04` → 50; `BADGE06` → 70. A traded mon at or below the cap always obeys; above it, two `Random()&255` gates decide ignore / random move / fall asleep / hit itself. Link and recorded-link battles are always obedient. So the only level-capped mons in a solo run are **in-game trades**. | `src/battle_util.c:3923-3956` |
| c03-5 | Party max 6 (`gPlayerPartyCount`); PC 14×30 = 420 | **CONFIRMED** (round 1) | Round 1 verified 420 slots and that boxes auto-wrap. | round 1 |
| c03-6 | Trap #1 "Shedinja Softlock": Shedinja is only created if the bag contains a standard `ITEM_POKE_BALL`; buying only Great Balls silently loses it | **REFUTED — hallucinated requirement** | `CreateShedinja()` has **one** precondition: `if (gEvolutionTable[preEvoSpecies][0].method == EVO_LEVEL_NINJASK && gPlayerPartyCount < PARTY_SIZE)`. There is **no ball check anywhere in the function**. Emerald needs only a free party slot. (The empty-ball requirement is a later-generation mechanic.) A bot rule "hold a spare Poké Ball for Shedinja" would be pure cargo cult. | `src/evolution_scene.c:548-583` |
| c03-7 | Trap #6 "HM Slave Erasure": the Daycare CAN overwrite HMs because it bypasses the HM lock — marked *RECALL* | **CONFIRMED — and it is worse than described. This is the single most dangerous confirmed trap in this round.** | `ApplyDaycareExperience()`: for each level gained, `while ((learnedMove = MonTryLearningNewMove(mon, firstMove)) != 0) { if (learnedMove == MON_HAS_MAX_MOVES) DeleteFirstMoveAndGiveMoveToMon(mon, gMoveToLearn); }` — **no HM check, no prompt, no confirmation.** Whatever sits in move **slot 1** is destroyed, silently, once per level-up-with-a-new-move. Deposit your only Surfer with Surf in slot 1 and you can lose Surf without a single dialogue box. **Bot rule: never daycare a mon that holds a required HM, full stop** — do not try to be clever about slot ordering. | `src/daycare.c:212-240` |
| c03-8 | Early-route species/slot table (Lotad 20% Route 102, Ralts 4%, Nincada 20% Route 116, Makuhita 50% Granite Cave 1F, …) | **UNRESOLVED — species/slot assignments not checked** | I verified the *slot probability* table exactly (see c07-6) and the *map-level* encounter rates (Route 102 land 20, Petalburg Woods 20, Granite Cave 1F 10, Route 119 land 15). Which species sits in which slot on which route I did not enumerate. Cheap to settle: `src/data/wild_encounters.json` (fetched, in scratch) or our own `modules/data/`. Note the note's rates are *slot* percentages, so e.g. "Makuhita 50%" implies it occupies slots 0+1+2 — plausible but unverified. | `src/data/wild_encounters.json` (rates only) |
| c03-9 | EXP `(BaseExpYield × EnemyLevel) / 7`; split evenly among participants; Exp. Share intercepts 50% before distribution | **partly REFUTED by round 1; Exp. Share UNRESOLVED** | Round 1: EXP goes only to mons **alive at the instant the opponent faints**, and the trainer **×1.5 applies per recipient after the split**, not to the total. Exp. Share's 50%-first behaviour I did not verify this pass. | round 1 |
| c03-10 | Traps #2 (B-button cancels evolution), #3 (move-overwrite blindness), #5 (Truant parity) | **UNRESOLVED** — plausible, not checked | Truant is observable: `modules/battle_state.py :: BattlePokemon.is_loafing_around` and `.truant_switch_in_hack` already exist, so the parity tracking the note asks for is unnecessary — read the flag. | `sandbox-pokebot/modules/battle_state.py:788-795` |
| c03-11 | Daycare "1 EXP per step", ¥100 + ¥100/level retrieval, movesets auto-overwritten | **CONFIRMED for the overwrite** (c03-7); costs UNRESOLVED | I read the move-overwrite path only. The step→EXP rate and the fee formula I did not open. | — |

## c07 — encounter mechanics, Repel quirk, encounters-per-frame (priority 3)

| # | claim | ruling | actual truth | source I read |
|---|---|---|---|---|
| c07-1 | `roll = Random() % 2880; if (roll < encounterRate * 16)` | **CONFIRMED**, with the exact order of operations | `WildEncounterCheck(rate, ignoreAbility)`: `rate *= 16` → bike ×80/100 → flute mod → Cleanse Tag mod → ability mod → **clamp to `MAX_ENCOUNTER_RATE` (2880)** → `EncounterOddsCheck`: `Random() % 2880 < rate`. The clamp matters: stacked multipliers saturate at 100%. | `src/wild_encounter.c:493-531` |
| c07-2 | Map rates "usually 21 for grass, 10 for caves, 4 for water" | **REFUTED (grass is 20)** | Grass is **20**, not 21. Verified samples: Route 101 land 20; Route 102 land 20 / water 4 / fishing 30; Petalburg Woods land 20; Granite Cave 1F land 10; Route 118 land 20 / water 4 / fishing 30; Route 124 water 4 / fishing 30; **Route 119 land 15** (so "usually" is doing real work — read the table, don't assume). Useful derived number: standard grass on foot = `20*16 = 320 / 2880 = 1/9 ≈ 11.1%` per step; on a bike `256/2880 ≈ 8.9%`. | `src/data/wild_encounters.json` |
| c07-3 | "Running shoes multiply the encounter threshold by 1.6 (`(rate*160)/100`)" — marked **VERIFIED** | **REFUTED — no such code exists** | `WildEncounterCheck` contains exactly one movement modifier: `if (TestPlayerAvatarFlags(PLAYER_AVATAR_FLAG_MACH_BIKE \| PLAYER_AVATAR_FLAG_ACRO_BIKE)) encounterRate = encounterRate * 80 / 100;`. There is no running-shoes branch anywhere in the function. **Any encounters-per-frame or XP-per-frame figure that applied ×1.6 for running is wrong.** | `src/wild_encounter.c:502-531` |
| c07-4 | Biking ×0.8 | **CONFIRMED** | `encounterRate * 80 / 100`, both bikes. | same |
| c07-5 | Acro-bike bunny hop in grass counts as a step and rolls an encounter | **UNRESOLVED** | I did not open `src/bike.c`. Note that the encounter check is driven from the step callback with `(curMetatileBehavior, prevMetatileBehavior)`, so a hop-in-place would hit the *same* metatile behaviour and therefore skip the 40% new-tile gate (c07-10) — but whether a hop fires the step callback at all is unverified. | — |
| c07-6 | Slot probability tables (land 20/20/10/10/10/10/5/5/4/4/1/1; water & rock smash 60/30/5/4/1; old rod 70/30; good rod 60/20/20; super rod 40/40/15/4/1) | **CONFIRMED — all six, exactly** | These are the `encounter_rates` arrays that generate the `ENCOUNTER_CHANCE_*` cumulative macros. Fishing is one 10-entry array partitioned into `old_rod [0,1]`, `good_rod [2,3,4]`, `super_rod [5..9]`; the selector rolls `Random() % 100` for every rod. | `src/data/wild_encounters.json` (`wild_encounter_groups[0].fields`); `src/data/wild_encounters.constants.json.txt`; `src/wild_encounter.c:182-250` |
| c07-7 | **The Repel quirk**: the slot is rolled *before* the Repel check and is **not** rerolled | **CONFIRMED — exactly as described** | `TryGenerateWildMon`: choose slot → `ChooseWildMonLevel` → `if (flags & WILD_CHECK_REPEL && !IsWildLevelAllowedByRepel(level)) return FALSE;`. One roll, no retry, the step is simply wasted. The note's consequence is right: Repel does **not** hunt for a rare high-level slot; it deletes the steps that rolled low ones. | `src/wild_encounter.c:422-455` |
| c07-8 | Repel observable at `gSaveBlock1Ptr->repelCounter`; compares "the lead Pokémon's level" | **REFUTED on both counts** | The counter is the event var **`VAR_REPEL_STEP_COUNT` (0x4021)**, ticked by `UpdateRepelCounter()`; there is no `repelCounter` field. And the comparison walks the party for the **first member with `MON_DATA_HP != 0` and not an egg** — with a fainted slot 0 the *second* mon's level is used. Suppression condition is `wildLevel < ourLevel`, so an encounter exactly at your level still happens. (Our shipped code already does this right — §1.3.) | `src/wild_encounter.c:850-896`; `include/constants/vars.h:51` |
| c07-9 | *(absent from note)* | **NEW — the encounters-per-frame headline** | **Sweet Scent bypasses everything.** `SweetScentWildEncounter()` calls `TryGenerateWildMon(..., 0)` — flags `0`, so **no `WILD_CHECK_REPEL` and no `WILD_CHECK_KEEN_EYE`** — and there is **no `WildEncounterCheck` rate roll at all**. On a valid land/water tile it is a guaranteed encounter on the spot, Repel active or not. That makes Sweet Scent the correct primitive for a grind loop, and it also means a Repel cannot be used to filter Sweet Scent encounters. | `src/wild_encounter.c:697-767` |
| c07-10 | *(absent from note)* | **NEW** | `AllowWildCheckOnNewMetatile()`: when `prevMetatileBehavior != curMetatileBehavior`, there is a **40% chance the encounter check is skipped entirely** (`Random() % 100 >= 60`). Stepping *into* grass from a path is therefore only 60% as likely to trigger as a step *within* grass. A grind loop that oscillates between two different tile types silently loses 40% of its rolls. | `src/wild_encounter.c:533-539`, and the call sites at `:597, :638` |
| c07-11 | "Illuminate / **Swarm** multiplies encounter rate ×2" | **half REFUTED** | Illuminate ×2 CONFIRMED. **Swarm has no overworld effect** — there is no `ABILITY_SWARM` branch. The other doubler is **`ABILITY_ARENA_TRAP`**. Full list in `WildEncounterCheck`: Stench ÷2 (but ×3/4 on the Battle Pyramid floor), Illuminate ×2, White Smoke ÷2, **Arena Trap ×2**, **Sand Veil ÷2 while `gSaveBlock1Ptr->weather == WEATHER_SANDSTORM`**. Nothing else. | `src/wild_encounter.c:509-527` |
| c07-12 | "Stench / White Smoke divide by 2" | **CONFIRMED** | With the Pyramid exception above. | same |
| c07-13 | "Intimidate / Keen Eye: 50% chance to suppress if wild level ≤ lead_level − 5" | **CONFIRMED — exactly** | `if (playerMonLevel > 5 && level <= playerMonLevel - 5 && !(Random() % 2)) return FALSE;`. Applies only where `WILD_CHECK_KEEN_EYE` is passed (standard land/water/rock-smash — **not** Sweet Scent, not fishing). | `src/wild_encounter.c:897-913` |
| c07-14 | "Static: 50% chance to force an Electric encounter; Magnet Pull: 50% Steel" | **CONFIRMED with two important caveats** | Both are **slot** influencers, not rate modifiers. `TryGetAbilityInfluencedWildMonIndex` requires: slot 0 not an egg, ability matches, `Random() % 2 == 0`; then `TryGetRandomWildMonIndexByType` **fails if the type is absent from the table OR if *every* slot is that type**. **Magnet Pull is checked on LAND only; Static on land and water.** Magnet Pull is evaluated before Static. | `src/wild_encounter.c:422-447, 915-953` |
| c07-15 | "Synchronize: 50% chance to force the lead's Nature" | **CONFIRMED** | `PickWildMonNature`: not an egg, ability == Synchronize, `Random() % 2 == 0` → returns `personality % NUM_NATURES` of slot 0. Safari-Zone Pokéblock nature steering takes priority (80%). | `src/wild_encounter.c:335-375` |
| c07-16 | "Hustle / Vital Spirit: 50% chance to force the highest level of the slot" — marked **RECALL** | **CONFIRMED, and upgraded: also `ABILITY_PRESSURE`** | `if (ability == ABILITY_HUSTLE \|\| ability == ABILITY_VITAL_SPIRIT \|\| ability == ABILITY_PRESSURE) { if (Random() % 2 == 0) return max; if (rand != 0) rand--; }` — note the *else* branch biases the roll upward by one as well. | `src/wild_encounter.c:268-302` |
| c07-17 | "These overworld abilities apply even if the lead Pokémon is fainted" | **CONFIRMED** | Every one of these checks reads `gPlayerParty[0]` and only excludes `MON_DATA_SANITY_IS_EGG`. **There is no HP check anywhere.** A fainted lead's ability still steers rate, slot, level and nature. (Contrast the *Repel* check, which does skip fainted mons — c07-8. Easy to conflate; don't.) | `src/wild_encounter.c:268-302, 335-375, 502-531, 897-953` |
| c07-18 | *(absent from note)* | **NEW — two free bot levers** | `ApplyFluteEncounterRateMod`: `FLAG_SYS_ENC_UP_ITEM` (White Flute) → ×1.5; `FLAG_SYS_ENC_DOWN_ITEM` (Black Flute) → ×0.5. `ApplyCleanseTagEncounterRateMod`: slot 0 holding `ITEM_CLEANSE_TAG` → ×2/3. ‼ **Both flute flags are explicitly cleared by `ClearTempFieldEventData()`, so a flute's effect ends the moment you change map** — a bot must re-use the flute per map, and must not assume a persistent buff. | `src/wild_encounter.c:955-967`; `src/event_data.c:39-48` |
| c07-19 | "Outbreaks: slots 0 and 1 are overwritten by the swarm species" | **REFUTED as described** | Outbreaks do not overwrite slots. `DoMassOutbreakEncounterTest()` runs **before** normal slot selection: if the map matches `outbreakLocationMapNum/Group` and `Random() % 100 < gSaveBlock1Ptr->outbreakPokemonProbability`, then `SetUpMassOutbreakEncounter` creates the outbreak species at `outbreakPokemonLevel` with `outbreakPokemonMoves[]` and the normal table is never consulted. It is a probability *pre-empt*, not a slot substitution. (Round 1 verified the Route 116 post-E4 outbreak is Skitty, 5 fixed entries.) | `src/wild_encounter.c:467-491, 613-620` |
| c07-20 | Feebas: 6 tiles on Route 119, seeded from `gSaveBlock1Ptr->dewfordTrends[0].rand`, in `IsFeebasMarkedTile` | **UNRESOLVED — function name is wrong; mechanism unverified** | The real functions are `CheckFeebas()`, `GetFeebasFishingSpotId()`, `FeebasSeedRng()`, `FeebasRandom()` — **there is no `IsFeebasMarkedTile`**. `NUM_FEEBAS_SPOTS` is indeed 6, and Route 119 is split into 3 sections with 131/167/149 valid spots. What seeds `sFeebasRngValue` I did not read. | `src/wild_encounter.c:27-35, 69-169` |
| c07-21 | *(absent from note)* | **NEW** | `AreLegendariesInSootopolisPreventingEncounters()`: while `FLAG_LEGENDARIES_IN_SOOTOPOLIS` is set, **all** water encounters in Sootopolis City are suppressed (both the step path and Sweet Scent). A grind loop parked there would spin forever. | `src/wild_encounter.c:541-550, 632-637, 747-750` |
| c07-22 | "Sticky Hold / Suction Cups increases the probability of a bite while fishing" | **CONFIRMED — see c06-5 for the exact numbers** | 85% vs the default 50%. | `src/field_player_avatar.c:1845-1878` |
| c07-23 | Option 3/4 "memory forcing" / writing the callback directly | **out of scope — and contrary to project directive** | Per `CLAUDE.md`, a state-write is a documented last-resort fallback that must reproduce vanilla's exact end-state. Forcing `StandardWildEncounter` is not that. Use Sweet Scent (c07-9), which is the natural-gameplay equivalent. | project directive |

## c04 — what is READABLE mid-battle (priority 4)

| # | claim | ruling | actual truth | source I read |
|---|---|---|---|---|
| c04-1 | Section B: opponent species / level / HP / status / statStages / ability / held item are "100% observable" | **CONFIRMED — and already implemented** | `sandbox-pokebot/modules/battle_state.py` already exposes, per battler: `species`, `level`, `current_hp`/`total_hp`/`current_hp_percentage`, `stats`, `ivs`, `types`, `ability`, `held_item`, `nature`, `moves` (as `LearnedMove`, i.e. with PP) plus `knows_move`/`can_use_move`, `status_permanent`, `status_temporary`, `stats_modifiers`/`modified_stats`, `friendship`, `hidden_power_type`/`_damage`, and the whole `DisableStruct`: `disabled_move`, `encored_move`, `disabled_turns_remaining`, `encore_turns_remaining`, `substitute_hp`, `protect_uses`, `stockpile_counter`, `perish_song_turns_remaining`, `taunt_turns_remaining`, `rollout_turns_remaining`, `fury_cutter_counter`, `charge_turns_remaining`, `recharge_turns_remaining`, `battler_preventing_escape`, `battler_with_sure_hit`, `is_loafing_around`, `truant_switch_in_hack`. Side state: `reflect/lightscreen/mist/safeguard/follow_me` timers, `spikes_amount`. **⇒ "plan a counter, detect failure, re-plan" is implementable today; nothing new needs reverse-engineering.** | `sandbox-pokebot/modules/battle_state.py:200-806` |
| c04-2 | *(the actual gap, absent from the note)* | **NEW** | `battle_state.py` models the **active battlers**, not the opponent's whole bench. The note's premise that `gEnemyParty[0..5]` is fully readable at battle start is separately plausible (our `modules/pokemon.py` has party readers) but I did **not** confirm a reader for the *opponent's* full party. If pre-battle scouting of a gym leader's back four is wanted, that reader is the piece to check/build first. | inspection of `battle_state.py` API surface |
| c04-3 | Quick Claw "20% chance to act first within the same priority bracket" | **mechanism CONFIRMED; the 20% UNRESOLVED** | `if (holdEffect == HOLD_EFFECT_QUICK_CLAW && gRandomTurnNumber < (0xFFFF * holdEffectParam) / 100) speed = UINT_MAX;`. Priority is compared *after* speed in `GetWhoStrikesFirst`, so the note's "within the same bracket" is right. ‼ **NEW:** the roll is `gRandomTurnNumber` — **one value for the whole turn, shared by both battlers** — so it is not two independent coin flips, and it is knowable before choosing an action. The literal 20% comes from the item's `holdEffectParam`, which I did not read. | `src/battle_main.c:4595-4690` |
| c04-4 | "Dynamo Badge boosts Speed by 10% (`(Speed*110)/100`)" | **CONFIRMED** | `FlagGet(FLAG_BADGE03_GET)` && `GetBattlerSide == B_SIDE_PLAYER` && not link/recorded-link/frontier → `speed = speed * 110 / 100`. Applied to each battler independently. | `src/battle_main.c:4639-4645, 4673-4679` |
| c04-5 | "Paralysis cuts Speed to 25%" | **CONFIRMED** | `speed /= 4`, applied **after** the badge boost. **NEW:** `HOLD_EFFECT_MACHO_BRACE` → `speed /= 2`, also before paralysis — the note omits it, and it matters if the bot ever equips a Macho Brace for EVs. | `src/battle_main.c:4647-4652, 4681-4686` |
| c04-6 | Trainer AI switching: "Emerald AI rarely switches voluntarily … evaluates switches if (1) Perish Song at 0, (2) locked into an unusable move, (3) the trainer has `AI_FLAG_CHECK_VIABILITY` and has 0 viable offensive options" | **REFUTED** | `src/battle_ai_switch_items.c` contains **zero occurrences of `AI_FLAG`** (I grepped the whole file). `ShouldSwitch()` is unconditional on AI flags. Its real structure: **hard blockers** — `STATUS2_WRAPPED \| STATUS2_ESCAPE_PREVENTION`, `STATUS3_ROOTED`, opposing Shadow Tag, opposing Arena Trap *(the decomp comments "Misses the flying type and Levitate check" — so the AI **over-refuses** to switch)*, Magnet Pull vs a Steel type, Battle Arena, or nothing available to switch to. Then, in order: `ShouldSwitchIfPerishSong()` → switch; `ShouldSwitchIfWonderGuard()` → switch; `FindMonThatAbsorbsOpponentsMove()` → switch; `ShouldSwitchIfNaturalCure()` → switch; `HasSuperEffectiveMoveAgainstOpponents()` → **stay**; `AreStatsRaised()` → **stay**; `FindMonWithFlagsAndSuperEffective(DOESNT_AFFECT_FOE, 2) \|\| (NOT_VERY_EFFECTIVE, 3)` → switch. **Design consequence:** the note's AI-baiting strategy is *less* reliable than claimed — the AI actively switches to an ability-absorber (Volt Absorb / Water Absorb / Flash Fire / Levitate class), which breaks a bait; but it will **never** switch away while it holds a super-effective move, which is exploitable in the other direction. "Locked into a move it can't execute" is not one of the triggers. | `src/battle_ai_switch_items.c :: ShouldSwitch` (read in full) |
| c04-7 | Type chart values 0/5/10/20 in `src/battle_main.c` (`gTypeEffectiveness`); Foresight/Levitate overrides; dual-type stacking | **UNRESOLVED** | Not opened. ‼ Caution: current pret master has migrated the chart to a `UQ_4_12` fixed-point table in its own data file, so the *literal 0/5/10/20 encoding* may be historical. The *semantics* (immune/resist/neutral/super, multiplicative for dual types) are not in doubt; the encoding and file path are. | — |
| c04-8 | Gen 3: Ghost types are **not** immune to trapping; Mean Look/Block/Spider Web; Baton Pass bypasses; Pursuit doubles to 80 BP and resolves before the switch; Smoke Ball is wild-only | **UNRESOLVED** | Not verified this pass. The *observable* half is settled though: `battle_state.py` exposes `battler_preventing_escape` and `status_temporary`, so the bot can detect that it is trapped **before** queueing a switch — which is what the note's "Trapped Menu Loop" trap actually needs. | `battle_state.py:709, 777` |
| c04-9 | Traps: trapped-menu loop, Pursuit suicide, Truant/Protect desync, Encore lock, PP Struggle, Roar desync | **sound in shape; all six are detectable with existing readers** | Encore → `encored_move`/`encore_turns_remaining`; Truant → `is_loafing_around`; PP → `moves[i].pp`; Roar → re-read `own_side.active_battler.species` every turn; trapping → `battler_preventing_escape`. No new reverse-engineering needed. | `battle_state.py` |

## c06 — water traversal, Dive layers, currents (priority 5)

| # | claim | ruling | actual truth | source I read |
|---|---|---|---|---|
| c06-1 | Surf requires `FLAG_BADGE05_GET` + a party mon with Surf | **CONFIRMED** | `if (FlagGet(FLAG_BADGE05_GET) == TRUE && PartyHasMonWithSurf() == TRUE && IsPlayerFacingSurfableFishableWater() == TRUE) return EventScript_UseSurf;` | `src/field_control_avatar.c:448-451` |
| c06-2 | Waterfall requires `FLAG_BADGE08_GET` + Waterfall | **CONFIRMED, with a nuance the note misses** | `if (MetatileBehavior_IsWaterfall(...)) { if (FlagGet(FLAG_BADGE08_GET) && IsPlayerSurfingNorth()) return EventScript_UseWaterfall; else return EventScript_CannotUseWaterfall; }`. ‼ **You must already be surfing and heading NORTH** — approaching a waterfall from any other direction yields the "cannot use" script, not the HM prompt. A navigator that tries to Waterfall while facing sideways will read as a hard block. | `src/field_control_avatar.c:453-460` |
| c06-3 | Dive requires `FLAG_BADGE07_GET` + Dive; surfacing checks the paired map | **CONFIRMED, plus the button mapping — NEW and directly actionable** | Dive **down** is on the **A button**: `if (input->pressedAButton && TrySetupDiveDownScript())` → `if (FlagGet(FLAG_BADGE07_GET) && TrySetDiveWarp() == 2) ScriptContext_SetupScript(EventScript_UseDive)`. **Emerging is on the B button** and additionally requires being on an underwater map: `if (input->pressedBButton && TrySetupDiveEmergeScript())` → `if (FlagGet(FLAG_BADGE07_GET) && gMapHeader.mapType == MAP_TYPE_UNDERWATER && TrySetDiveWarp() == 1)`. `TrySetDiveWarp` returns 1 for emerge, 2 for dive, 0 for neither, and resolves through `SetDiveWarpEmerge/Dive`, which consult the map's `CONNECTION_EMERGE`/`CONNECTION_DIVE` — so a dive only exists where the map pair declares the connection. | `src/field_control_avatar.c:153, 180, 463-481, 940-985`; `src/overworld.c:760-782` |
| c06-4 | Currents on Routes 132-134: `MB_CURRENT_*` tiles lock control and slide the player | **partly CONFIRMED — existence and input-lock yes, directions unverified** | Forced-movement tiles are real and do lock control: `MetatileBehavior_IsForcedMovementTile(GetPlayerCurMetatileBehavior(...))` gates input at `field_control_avatar.c:93`, and the tile-transition path is skipped while `PLAYER_AVATAR_FLAG_FORCED_MOVE` is set (`:547`). The specific `MB_CURRENT_R/L/U/D` constants and the function name `GetForcedMovementByMetatileBehavior` I did not open (it is in `src/field_player_avatar.c`, which I have in scratch but did not read for this). Encounters-during-current is unverified. | `src/field_control_avatar.c:93, 547` |
| c06-5 | Fishing: Suction Cups / Sticky Hold make a bite "far more likely" | **CONFIRMED, with exact numbers** | `Fishing_CheckForBite`: if slot 0 is not an egg and has Suction Cups or Sticky Hold, `if (Random() % 100 > 14) bite = TRUE;` → **85%**. Otherwise the default is `if (Random() & 1) → no bite` → **50%**. Also note `if (!DoesCurrentMapHaveFishingMons()) task->tStep = FISHING_NO_BITE;` — fishing on a map with no fishing table always fails, which is a cheap pre-flight check. | `src/field_player_avatar.c:1845-1878` |
| c06-6 | Trap 1: "the ROM prevents releasing the *last* Pokémon that knows an HM move like Surf … but Emerald's protection can be bypassed if the bot saves, resets, or uses specific day-care edge cases" | **CONFIRMED in outline, REFUTED in the details — and the real bypasses are different** | The guard is a **map-conditional table**, `sRestrictedReleaseMoves`: `{any map, MOVE_SURF}`, `{any map, MOVE_DIVE}`, `{League 1F, MOVE_STRENGTH}`, `{League 1F, MOVE_ROCK_SMASH}`, `{League 2F, MOVE_STRENGTH}`, `{League 2F, MOVE_ROCK_SMASH}`. So: **Surf and Dive are protected everywhere; Strength and Rock Smash only on the two Pokémon League floors; Fly, Waterfall, Cut and Flash are never protected.** The check scans the whole party *and* all 14 boxes for another owner of the move before refusing. Separately, `AtLeastThreeUsableMons()` blocks any release that would leave you with fewer than 3 mons total. ‼ The claimed save/reset bypass is unsupported. The **two real bypasses** are: (a) **DEPOSIT** — `GetRestrictedReleaseMoves` is called only from `InitCanReleaseMonVars`, i.e. the release path; nothing stops you depositing your only Surfer into a box (only `IsRemovingLastPartyMon` prevents emptying the party); and (b) the **DAYCARE**, which deletes move slot 1 with no check at all (c03-7). | `src/pokemon_storage_system.c:6488-6530` (`sRestrictedReleaseMoves`, `GetRestrictedReleaseMoves`), `:6522-6570` (`InitCanReleaseMonVars`), `:6572-6660` (`RunCanReleaseMon`), `AtLeastThreeUsableMons` |
| c06-7 | *(round-1 cross-check)* | **NEW — three different guards, do not conflate them** | Round 1 found `IsLastMonThatKnowsSurf` (`party_menu.c:6407-6430`) guards the **move-forget/Move-Deleter** path and is **SURF only**. This pass found the **PC-release** path uses a *different*, broader table (Surf + Dive + conditional Strength/Rock Smash). And the **daycare** path has **no guard whatsoever**. Three code paths, three different levels of protection. **The bot must own the HM-coverage invariant itself.** | `src/party_menu.c:6407-6430`; `src/pokemon_storage_system.c:6488-6502`; `src/daycare.c:212-240` |
| c06-8 | Repel wore-off: Emerald does not auto-prompt "use another?"; it shows text requiring an A press | **partly CONFIRMED** | `UpdateRepelCounter()` decrements `VAR_REPEL_STEP_COUNT` and, on reaching 0, `ScriptContext_SetupScript(EventScript_RepelWoreOff)` — so there **is** a script/text box the bot must clear, and it is *not* skipped in the Battle Pike / Pyramid / Union Room (those return early before the decrement). Whether the script contains a yes/no I did not read (`data/scripts/repel.inc` not opened) → that half UNRESOLVED. | `src/wild_encounter.c:850-872` |
| c06-9 | Map typology (hybrid vs pelagic routes; "dive routes are 124, 126, 127, 128") | **UNRESOLVED** | Not enumerated. Partial spot-check consistent: Route 124 has `water_mons` + `fishing_mons` and no `land_mons`; Routes 102/118/119 have all three. The dive-route list I did not verify — settle it from map connections (`CONNECTION_DIVE`) rather than from encounter tables. | `src/data/wild_encounters.json` (partial) |
| c06-10 | Fishing state machine names `FISHING_START` / `FISHING_NIBBLE` / `FISHING_BITE` / `sFishingState` / `sFishingBiteTimer` in `src/fishing.c` | **REFUTED (names and file)** | There is **no `src/fishing.c`** and no `sFishingState`/`sFishingBiteTimer`. It is a **task** in `src/field_player_avatar.c`: `Task_Fishing` over `sFishingStateFuncs[]`, with step constants `FISHING_START_ROUND 3`, `FISHING_GOT_BITE 6`, `FISHING_ON_HOOK 9`, `FISHING_NO_BITE 11`, `FISHING_GOT_AWAY 12`, `FISHING_SHOW_RESULT 13`, and state held in `gTasks[taskId].data[]` (`tStep`, `tFishingRod = data[15]`). Anyone who went looking for `src/fishing.c` on this note would have found nothing. (Our repo already has `modules/fishing.py`, which presumably does this correctly — not audited here.) | `src/field_player_avatar.c:123-142, 1702-1745` |

---

# 3. CONFIRMED-GOOD CORE — safe to build on

1. **Map re-entry is a full puzzle reset, and the reset surface is exactly two regions.** Temp flags
   `0x000–0x01F` + temp vars `0x4000–0x400F` are zeroed on every warp *and* every map-connection
   crossing; object-event templates are re-copied from ROM and every NPC respawns on its original
   tile. Everything else in the save block survives — trainer-defeated flags, Repel steps, badges,
   money. Returning from a **battle** resets nothing (live `gObjectEvents` is preserved).
2. **Self-caught Pokémon never disobey.** Obedience is gated on `IsOtherTrainer(otId, otName)`
   before any badge logic. Over-level a bench freely; only in-game trades are capped (10/30/50/70
   by badges 2/4/6/8).
3. **The Gen 3 Repel quirk is real, exactly as folklore describes it.** Slot and level are chosen
   first; a too-low level wastes the step with no reroll. Repel raises the *floor*, it does not hunt
   for rare slots. The floor is the level of the first non-fainted, non-egg party member, and a wild
   level *equal* to it still triggers.
4. **The encounter model, end to end:** `rate*16` → bike ×0.8 → flute ×1.5/×0.5 → Cleanse Tag ×2/3
   → ability (Illuminate/Arena Trap ×2; Stench/White Smoke/sandstorm-Sand-Veil ÷2) → clamp 2880 →
   `Random()%2880 <`. Grass = 20, cave = 10, water = 4, fishing = 30 (per map; Route 119 grass is
   15). Plus the 40% skip on a new metatile type. Slot tables exactly as in c07-6.
5. **Sweet Scent is a guaranteed encounter** on a valid tile — no rate roll, no Repel check, no Keen
   Eye check. This is the right primitive for a grind loop, and it is natural gameplay.
6. **Mid-battle opponent state is fully readable and already wrapped** by
   `sandbox-pokebot/modules/battle_state.py`. Counter-planning with failure detection is
   implementable with today's readers; the only gap is a reader for the opponent's *bench*.
7. **Turn order** = priority, then (badge ×1.1 on the player's side if `FLAG_BADGE03_GET`) ×
   stat-stage speed, ÷2 Macho Brace, ÷4 paralysis, Quick Claw sets `UINT_MAX` off a single
   per-turn roll shared by both battlers.
8. **HM field-move gates:** Surf `BADGE05`; Dive `BADGE07` (down = **A**, up = **B** and only on a
   `MAP_TYPE_UNDERWATER` map); Waterfall `BADGE08` **and already surfing northward**.
9. **Fishing:** 50% bite normally, 85% with Suction Cups / Sticky Hold on slot 0; always fails on a
   map with no fishing table. The state machine is `Task_Fishing` in `field_player_avatar.c`.
10. **HM-loss protection is uneven and the bot must own the invariant.** PC release protects
    Surf + Dive everywhere (Strength/Rock Smash only in the League); the move-forget path protects
    Surf only; **the daycare protects nothing**; deposit protects nothing.

---

# 4. DO NOT USE — wrong or hallucinated

| claim | file | why it is wrong |
|---|---|---|
| Whiteout money loss uses a level-and-badge formula via `GetWhiteoutMoneyPenalty` in `src/money.c` | c10 | The function **does not exist**. Emerald halves your money: `SetMoney(&…money, GetMoney(&…money) / 2)` in `DoWhiteOut()`. |
| Whiteout friendship: −10 for `friendship < 100`, −5 for `< 200` | c10 | Inverted. `FAINT_LARGE = {-5, -5, -10}` by band ≤99 / 100–199 / ≥200 — **−10 hits high-friendship mons**. |
| Running shoes multiply encounter rate by 1.6 | c07 | No such code. The only movement modifier in `WildEncounterCheck` is the bike, ×0.8. Kills any XP-per-frame table built on it. |
| `ABILITY_SWARM` doubles the encounter rate | c07 | No overworld effect. The second doubler is **Arena Trap**. |
| Repel state lives at `gSaveBlock1Ptr->repelCounter` and compares "the lead Pokémon" | c07 | It is `VAR_REPEL_STEP_COUNT` (0x4021), and it compares the **first non-fainted, non-egg** party member. |
| Feebas tiles are computed by `IsFeebasMarkedTile` | c07 | No such function. The real ones are `CheckFeebas` / `GetFeebasFishingSpotId` / `FeebasSeedRng` / `FeebasRandom`. |
| Outbreaks "overwrite slots 0 and 1" | c07 | Outbreaks pre-empt slot selection entirely via `DoMassOutbreakEncounterTest` + `outbreakPokemonProbability`; the table is never consulted. |
| `IsMonDisobedient` is in `src/battle_main.c` | c03 | It is in **`src/battle_util.c:3923`**. Zero hits in `battle_main.c`. |
| Shedinja needs a plain `ITEM_POKE_BALL` in the bag, or the spawn silently fails | c03 | Hallucinated. `CreateShedinja` requires only `gPlayerPartyCount < PARTY_SIZE`. Do not write a "keep a spare ball" rule. |
| Trainer AI only considers switching with `AI_FLAG_CHECK_VIABILITY`, or when locked into an unusable move | c04 | `battle_ai_switch_items.c` references **no AI flags at all**. Neither trigger exists; see c04-6 for the seven real checks. |
| The fishing state machine is `sFishingState` / `sFishingBiteTimer` in `src/fishing.c` | c06 | No such file or symbols. It is `Task_Fishing` + `sFishingStateFuncs[]` in `src/field_player_avatar.c`, state in `gTasks[].data[]`. |
| "Emerald's release protection can be bypassed if the bot saves, resets, or uses day-care edge cases" | c06 | The save/reset bypass is fabricated. The real holes are **deposit** (no restricted-move check) and the **daycare** (deletes move slot 1 unconditionally). |
| Grass encounter rate is 21 | c07 | It is 20. |
| Option "memory forcing" / writing `StandardWildEncounter`'s branch or the Sweet Scent callback | c07 | Contrary to the project's faithful-gameplay directive, and unnecessary — Sweet Scent already gives a guaranteed encounter. |

---

# 5. METHOD — what I grounded, and what blocked me

**Grounded** (fetched and read this session; copies in the session scratchpad):
`src/overworld.c`, `src/rotating_gate.c`, `src/wild_encounter.c`, `src/battle_util.c`,
`src/battle_main.c`, `src/battle_util2.c`, `src/battle_ai_switch_items.c`, `src/money.c`,
`src/event_data.c`, `src/event_object_movement.c`, `src/daycare.c`, `src/evolution_scene.c`,
`src/pokemon.c` (friendship only), `src/party_menu.c` (`IsLastMonThatKnowsSurf` only),
`src/pokemon_storage_system.c` (release paths only), `src/field_control_avatar.c`,
`src/field_player_avatar.c` (fishing only), `src/data/wild_encounters.json`,
`src/data/wild_encounters.constants.json.txt`, `data/maps/FortreeCity_Gym/scripts.inc`,
`include/constants/flags.h`, `include/constants/vars.h`, `include/wild_encounter.h`.
Repo-side: `sandbox-pokebot/modules/story/early_game.py :: do_fortree_gym`,
`modules/battle_state.py`, `modules/pokemon_party.py`, `modules/map.py` (Repel maths).

**Method notes.** I read whole functions, not grep hits, wherever a ruling turned on control flow —
`WildEncounterCheck`, `TryGenerateWildMon`, `IsMonDisobedient`, `ShouldSwitch`,
`ApplyDaycareExperience`, `CreateShedinja`, `LoadMapFromWarp`, `TrySpawnObjectEvents`. Several of
this round's REFUTEs are **absence** findings (no running-shoes branch; no `ABILITY_SWARM`; no ball
check in `CreateShedinja`; no `AI_FLAG` in the switch file) — the note's own §35 of
`00-READ-THIS-FIRST` flags absence as the most dangerous claim shape, so in each case I read the
complete function or grepped the complete file rather than sampling, and I say which.

**Version caveat.** pret master has been refactored since retail (`gSpeciesInfo`, `DISOBEDIENCE_*`
enums, `MOD()`, `#ifdef BUGFIX`, and a `UQ_4_12` type chart). It still matches the retail ROM by
default, so *behaviour* rulings hold; but **symbol names and file paths in these notes may not match
older revisions**, and c04-7 (the type-chart encoding) is exactly where that bites — which is why I
left it UNRESOLVED rather than ruling from master's data layout.

**Not examined at all — `c05` (healing items & money economy) and `c08` (Mystery Gift).** Depth was
chosen over breadth per the brief. `c08` in particular is likely low-risk (Mystery Gift without
event data is a dead end regardless), but `c05`'s heal-walk-vs-carry-potions break-even is real
design input and remains an open lead.

**Left UNRESOLVED with a reason** (each is cheap to settle, and the file to open is named in the
ruling row): Sootopolis ice-floor reset (c10-4); whiteout vs `trainerbattle` flag ordering (c10-10);
static-legendary sprite hiding (c10-11); roamer HP persistence (c10-12); `gBattleStruct` internals
(c10-13); per-route species/slot assignments (c03-8); Exp. Share split (c03-9); acro-hop as a step
(c07-5); Feebas seeding (c07-20); the opponent-bench reader (c04-2); Quick Claw's 20% parameter
(c04-3); the type chart / Foresight / Levitate / Pursuit / Smoke Ball (c04-7, c04-8); current tile
directions and encounters-during-current (c06-4); the Repel wore-off script's contents (c06-8); the
dive-route list (c06-9).

**Nothing blocked me** — `gh api` worked throughout; the only friction was that
`include/constants/wild_encounter.h` does not exist as a file (the `ENCOUNTER_CHANCE_*` macros are
**generated** from `src/data/wild_encounters.constants.json.txt` + the JSON's `fields` array), which
I resolved by reading the generator template and the JSON. No live emulator probe was run; every
ruling above is static ground truth, and the two rulings that most matter for shipped code (§1.1)
are additionally corroborated by the existing 4/4 live validation of `fortree_gates`.
