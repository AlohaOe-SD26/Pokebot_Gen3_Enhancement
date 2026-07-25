# ✅ CLAUDE-VALIDATED — Concept round 1 (2026-07-25)

**Status: this file is grounded in EXTERNAL truth.** Every ruling below cites a decomp file that
was fetched and read in-session via `gh api repos/pret/pokeemerald/contents/<path>` (pret/pokeemerald
`master`, fetched 2026-07-25), or a project data file read directly. Line numbers are from those
fetched files.

Scope: the four highest-stakes claims named in `00-READ-THIS-FIRST.md` (`c12`, `c01`, `c09`, `c11`),
plus the requested spot-check of the catch formula and ball multipliers in `c02`. The other seven
concept notes were **not** examined and remain LEADS.

Sources personally read (all fetched this session):

| file | what it settled |
|---|---|
| `src/battle_script_commands.c` | `Cmd_getexp` (3255-3529), `Cmd_givecaughtmon` (10055-10083), `Cmd_handleballthrow` (9905-10053), `sBallCatchBonuses` (841-847) |
| `src/battle_controller_player.c` | `Task_GiveExpToMon` (1154-1189), `PlayerHandleExpUpdate` (2726-2742) |
| `src/overworld.c` | `DoWhiteOut` (358-366), `Overworld_ResetStateAfterWhiteOut` (399-414), `CB2_WhiteOut` (1550-1570) |
| `src/script_pokemon_util.c` | `HealPlayerParty` (30-56) |
| `src/battle_setup.c` | `CB2_EndWildBattle` (602-616), `CB2_EndScriptedWildBattle` (618-634), `IsPlayerDefeated` (994-1010) |
| `src/battle_main.c` | `ReturnFromBattleToOverworld` (5217-5248), `B_ACTION_SAFARI_BALL` guard (4268-4277) |
| `src/pokemon.c` | `GiveMonToPlayer` (4425-4445), `CopyMonToPC` (4447-4479), `IsPlayerPartyAndPokemonStorageFull` / `IsPokemonStorageFull` (4609-4630) |
| `src/item_use.c` | `ItemUseInBattle_PokeBall` (938-956) |
| `src/party_menu.c` | `IsMoveHm` (4694-4704), `ItemUseCB_TMHM` (4733-4767), `Task_LearnedMove` (4769-4787), `Task_PartyMenuReplaceMove` (4882-4895), Move Deleter specials (6341-6376), `IsLastMonThatKnowsSurf` (6407-6430) |
| `src/pokemon_summary_screen.c` | `CanReplaceMove` (2246-2254), `ShowCantForgetHMsWindow` (2256-2265) |
| `src/field_specials.c` | `ShouldShowBoxWasFullMessage` (3405-3416) |
| `src/roamer.c` | `ROAMER` macro (17), `SetRoamerInactive` (237-239), `sRoamerLocations` |
| `src/strings.c` | `gText_BoxFull` (249), `gText_HMMovesCantBeForgotten2` (516) |
| `src/data/pokemon/species_info.h` | catch rates / expYield for the 8 legendaries checked |
| `include/constants/flags.h` | every legendary `FLAG_DEFEATED_*` / `FLAG_CAUGHT_*` id |
| `include/constants/battle.h`, `include/constants/items.h`, `include/battle_controllers.h` | `B_OUTCOME_*`, ball item ids, `BALL_3_SHAKES_SUCCESS` |
| `data/maps/{SkyPillar_Top, TerraCave_End, MarineCave_End, DesertRuins, IslandCave, AncientTomb, SouthernIsland_Interior, FarawayIsland_Interior, BirthIsland_Exterior, NavelRock_Top, NavelRock_Bottom, LilycoveCity_MoveDeletersHouse}/scripts.inc` | per-legendary flag semantics; Move Deleter script |
| `sandbox-pokebot/modules/data/species.json`, `modules/data/event_flags/emerald.txt`, `modules/roamer.py` | cross-check against our own ROM-derived tables |

---

## 1. RULINGS

### 1a. `c12` — "Mid-battle EXP survives a whiteout"

| claim | verdict | the actual truth | source |
|---|---|---|---|
| **Mid-battle EXP survives a whiteout** | **CONFIRMED** | EXP is written into `gPlayerParty` the moment the opponent faints, and nothing on the whiteout path rolls it back. `DoWhiteOut()` does exactly four things: run `EventScript_WhiteOut`, halve money, `HealPlayerParty()`, reset avatar/field flags, warp to the last heal location. There is **no save reload and no party rollback**. | `src/overworld.c:358-366` — `RunScriptImmediately(EventScript_WhiteOut); SetMoney(&money, GetMoney(&money)/2); HealPlayerParty(); Overworld_ResetStateAfterWhiteOut(); SetWarpDestinationToLastHealLocation(); WarpIntoMap();` |
| EXP actually reaches the *party* struct (not just `gBattleMons`) | **CONFIRMED** | `Cmd_getexp` case 3 emits `BtlController_EmitExpUpdate`; the player controller's `Task_GiveExpToMon` calls `SetMonData(mon, MON_DATA_EXP, …)` on `gPlayerParty[monId]`, level-by-level. | `src/battle_script_commands.c:3427-3445`; `src/battle_controller_player.c:1165-1189` (`SetMonData(mon, MON_DATA_EXP, &nextLvlExp)`) and `:1243-1263` |
| `HealPlayerParty` does not touch EXP/level | **CONFIRMED** | It writes only `MON_DATA_HP` (to max), `MON_DATA_PP1..4` and clears status. | `src/script_pokemon_util.c:30-56` |
| Losing routes to the whiteout callback (not back into the script) | **CONFIRMED** | `IsPlayerDefeated()` returns TRUE for `B_OUTCOME_LOST` and `B_OUTCOME_DREW`; both wild and scripted-wild battle-end callbacks then `SetMainCallback2(CB2_WhiteOut)`. | `src/battle_setup.c:994-1010`, `:602-616`, `:618-634` |
| Money is halved on whiteout | **CONFIRMED** | `SetMoney(&gSaveBlock1Ptr->money, GetMoney(&gSaveBlock1Ptr->money) / 2)` | `src/overworld.c:361` |
| **"Trainer multiplier: `Total = (Base * 15) / 10`, applied to the total"** | **REFUTED** | The ×1.5 trainer bonus is applied **per recipient, AFTER the participant split**, as its own truncating `*150/100`. Real order: `base = expYield * level / 7` → split by `viaSentIn` → then per mon: `+= gExpShareExp` → `×150/100` Lucky Egg → `×150/100` trainer → `×150/100` traded. Four independent truncations, not one. | `src/battle_script_commands.c:3310` (`gSpeciesInfo[...].expYield * level / 7`), `:3314`/`:3324` (split), `:3374-3390` |
| **A Pokémon that is fainted when the opponent faints gets ZERO exp** (note does not say this) | **NEW / CONFIRMED** | Both the message/EV step and the exp-award step are gated on `MON_DATA_HP != 0`. A mon that KO'd the enemy and died in the same turn (recoil, Destiny Bond, simultaneous faint) banks **nothing**. The `viaSentIn` divisor also skips fainted mons. | `src/battle_script_commands.c:3367` (`if (GetMonData(…, MON_DATA_HP))`), `:3431`, `:3294` |
| EXP-Share / participant split arithmetic | **CONFIRMED** | `viaExpShare` and `viaSentIn` are counted only over party members with `species != NONE` **and `HP != 0`**; `SAFE_DIV`; minimum yield clamped to 1. Halving when any Exp Share is held is exactly as described. | `src/battle_script_commands.c:3292-3328` |
| Symbol name `gBaseStats` | **REFUTED (stale)** | Current decomp uses **`gSpeciesInfo`**; `expYield`/`catchRate`/`growthRate` live there. Any symbol-based reader must use `gSpeciesInfo`. | `src/battle_script_commands.c:3310`, `:9935`; `src/battle_controller_player.c:1166` |
| Growth-rate tables / rematch mechanics (Match Call vs VS Seeker) | **UNRESOLVED** | Not checked. `src/data/pokemon/experience_tables.h` and `src/match_call.c` exist in the tree but were not read. | — |

### 1b. `c01` — "Can a caught Pokémon be LOST when party + all boxes are full?"

| claim | verdict | the actual truth | source |
|---|---|---|---|
| **A caught Pokémon can be lost when everything is full** | **REFUTED — it cannot happen in vanilla** | Both throw paths are guarded *before* the ball leaves your hand. Bag path: `if (IsPlayerPartyAndPokemonStorageFull() == FALSE) { RemoveBagItem(…) … } else { DisplayItemMessage(…, gText_BoxFull, CloseItemMessage); }` — **the ball is not consumed, no turn is used, and the bag stays open.** Safari path is guarded identically and runs `BattleScript_PrintFullBox`. | `src/item_use.c:938-956`; `src/battle_main.c:4268-4277` |
| The guard's actual condition | **CONFIRMED** | `IsPlayerPartyAndPokemonStorageFull()` = all 6 party slots non-empty **AND** `IsPokemonStorageFull()` = every one of `TOTAL_BOXES_COUNT × IN_BOX_COUNT` (14×30 = 420) box slots non-empty. | `src/pokemon.c:4609-4630` |
| Auto-deposit wraps to the next box | **CONFIRMED** | `CopyMonToPC` walks `boxPos 0..IN_BOX_COUNT` in `StorageGetCurrentBox()`, then `boxNo++` (wrapping 13→0) until it returns to the starting box; only then `return MON_CANT_GIVE`. | `src/pokemon.c:4447-4479` |
| **But: the catch code has NO handling for `MON_CANT_GIVE`** | **NEW / CONFIRMED** | `Cmd_givecaughtmon` tests only `!= MON_GIVEN_TO_PARTY` and then unconditionally prints a "sent to <box>" message. If storage were ever full at that point the Pokémon would be **silently discarded while the game claimed it was deposited.** The only thing preventing it is the two pre-throw guards above. | `src/battle_script_commands.c:10055-10083` |
| Exact "box full" text | **REFUTED (wording)** | `gText_BoxFull` is literally `"The BOX is full."` — not "The BOX is full! You can't catch any more!". A bot matching on text must use the real string. | `src/strings.c:249` |
| The *other* box message is cosmetic and one-shot | **NEW / CONFIRMED** | `ShouldShowBoxWasFullMessage()` fires at most once (latched by `FLAG_SHOWN_BOX_WAS_FULL_MESSAGE`) and only means "the box you had selected filled up, so I used a different one". **It is not a failure.** A run-to-failure bot that treats any box message as "catch failed" will mis-handle this. | `src/field_specials.c:3405-3416`; `src/pokemon.c:4466-4468` |
| Release/egg restrictions (`CanReleaseMon`, Bad Egg contagion, "HM slave releasing is unblocked") | **UNRESOLVED** | `src/pokemon_storage_system.c` was fetched but the release-path functions were not read. The Bad-Egg-corrupts-adjacent-slots claim is an unsourced folk claim; do not build on it. | — |

### 1c. `c09` — "Which legendaries can be PERMANENTLY lost, and which flag records it?"

**Verdict: CONFIRMED that all listed statics are permanently lost on KO — with two material corrections
that would each have produced a broken safety check.**

Every scripted static uses the same shape (Rayquaza shown; the others are identical modulo names):

```
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, ..._DefeatedRayquaza     @ you KO'd it
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, ..._RanFromRayquaza      @ safe: no flag
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, ..._RanFrom @ safe: no flag
	setflag FLAG_DEFEATED_RAYQUAZA                                  @ FALLTHROUGH — incl. CAUGHT
```
and the respawn gate is `OnTransition: call_if_unset FLAG_DEFEATED_X → clearflag FLAG_HIDE_X`.
— `data/maps/SkyPillar_Top/scripts.inc` (`_EventScript_Rayquaza`, `_EventScript_TryShowRayquaza`)

| species | Lv (from script) | catchRate | KO permanently loses it? | flag on KO | flag on CATCH | source |
|---|---|---|---|---|---|---|
| Rayquaza | 70 | 3 | **YES** | `FLAG_DEFEATED_RAYQUAZA` | **same flag** | `SkyPillar_Top/scripts.inc`; `species_info.h:11489-11498` |
| Groudon | 70 | 5 | **YES** | `FLAG_DEFEATED_GROUDON` | **same flag** | `TerraCave_End/scripts.inc:17,42-52`; `species_info.h:11459-11468` |
| Kyogre | 70 | 5 | **YES** | `FLAG_DEFEATED_KYOGRE` | **same flag** | `MarineCave_End/scripts.inc:18,42-52`; `species_info.h:11429-11438` |
| Regirock | 40 | 3 | **YES** | `FLAG_DEFEATED_REGIROCK` | **same flag** | `DesertRuins/scripts.inc:32,~64-77`; `species_info.h:11339-11348` |
| Regice | 40 | 3 | **YES** | `FLAG_DEFEATED_REGICE` | **same flag** | `IslandCave/scripts.inc:33,102-110` |
| Registeel | 40 | 3 | **YES** | `FLAG_DEFEATED_REGISTEEL` | **same flag** | `AncientTomb/scripts.inc:19,69-77` |
| Lati@s — Southern Island (Eon Ticket) | 50 (+ Soul Dew) | 3 | **YES** | `FLAG_DEFEATED_LATIAS_OR_LATIOS` | `FLAG_CAUGHT_LATIAS_OR_LATIOS` | `SouthernIsland_Interior/scripts.inc` (`_EventScript_Lati`, `_LatiDefeated`) |
| Mew — Faraway Island | 30 | 45 | **YES** | `FLAG_DEFEATED_MEW` | `FLAG_CAUGHT_MEW` | `FarawayIsland_Interior/scripts.inc:38-43,135-144`; `species_info.h:4539-4548` |
| Deoxys — Birth Island | 30 | 3 | **YES** | `FLAG_DEFEATED_DEOXYS` | `FLAG_BATTLED_DEOXYS` | `BirthIsland_Exterior/scripts.inc:16-26,88-96` |
| Ho-Oh — Navel Rock | 70 | 3 | **YES** | `FLAG_DEFEATED_HO_OH` | `FLAG_CAUGHT_HO_OH` | `NavelRock_Top/scripts.inc:4-19,59-67`; `species_info.h:7509-7518` |
| Lugia — Navel Rock | 70 | 3 | **YES** | `FLAG_DEFEATED_LUGIA` | `FLAG_CAUGHT_LUGIA` | `NavelRock_Bottom/scripts.inc:7-16,59-67` |
| **Lati@s — ROAMER** | 40 | 3 | **YES — and by more outcomes than the note says (below)** | **NO FLAG AT ALL** | — | `src/battle_main.c:5231-5245`; `src/roamer.c:237-239` |

| claim | verdict | the actual truth | source |
|---|---|---|---|
| **Roamer KO sets `FLAG_DEFEATED_LATIAS_OR_LATIOS`** | **REFUTED — dangerous** | The roamer path sets **no flag whatsoever**. It clears `gSaveBlock1Ptr->roamer.active`. `FLAG_DEFEATED_LATIAS_OR_LATIOS` is written **only** by the Southern Island script. A bot gating on that flag to detect "roamer lost" reads False forever. | `src/roamer.c:17` (`#define ROAMER (&gSaveBlock1Ptr->roamer)`), `:237-239` (`SetRoamerInactive` → `ROAMER->active = FALSE`); `SouthernIsland_Interior/scripts.inc` is the only `setflag FLAG_DEFEATED_LATIAS_OR_LATIOS` found |
| Which outcomes destroy the roamer | **REFUTED (note lists only KO)** | Vanilla condition is `if ((gBattleOutcome & B_OUTCOME_WON) \|\| gBattleOutcome == B_OUTCOME_CAUGHT) SetRoamerInactive();`. Since `B_OUTCOME_WON == 1`, the bitwise AND is true for **every odd outcome**: WON(1), **DREW(3)**, **PLAYER_TELEPORTED(5)**, CAUGHT(7), FORFEITED(9). The decomp flags this as a bug in a comment ("When Roar is used by a roamer, gBattleOutcome is B_OUTCOME_PLAYER_TELEPORTED (5), which deactivates the roamer"). **Safe** outcomes: LOST(2, whiteout), RAN(4), MON_FLED(6, its turn-1 flee). | `src/battle_main.c:5231-5245`; `include/constants/battle.h:100-109` |
| **Whiteout is safe for scripted statics** | **CONFIRMED** | On `B_OUTCOME_LOST` the battle-end callback becomes `CB2_WhiteOut`, replacing `gMain.savedCallback` — so the map script **never resumes** and no `setflag` executes. The legendary is preserved. (A **DREW** is also a "player defeated" whiteout for statics, so also safe there — but a DREW against the *roamer* still destroys it, per the row above.) | `src/battle_setup.c:618-634` + `:994-1010`; `src/overworld.c:1550-1570` |
| **`FLAG_DEFEATED_X` means "encounter resolved", not "killed"**, for Rayquaza/Groudon/Kyogre/the 3 Regis | **REFUTED (note implies KO-only)** | Catching is the script's *fallthrough*, which also runs `setflag FLAG_DEFEATED_X`. The flag cannot distinguish caught from KO'd for those six. Ho-Oh/Lugia/Mew/Deoxys/Southern-Lati DO have separate caught flags. | the six map scripts cited above |
| Rayquaza base catch rate = 3 | **CONFIRMED** (note was right; a plausible-sounding "45" is wrong) | `.catchRate = 3` | `src/data/pokemon/species_info.h:11498`; cross-checked `sandbox-pokebot/modules/data/species.json` → `Rayquaza catch_rate=3` |
| Groudon/Kyogre catch rate = 5 (note's own footnote) | **CONFIRMED** | `.catchRate = 5` both | `species_info.h:11438`, `:11468` |
| Fleeing / Teleporting out of a static is recoverable | **CONFIRMED** | `RAN` and `PLAYER_TELEPORTED` both route to `Common_EventScript_LegendaryFlewAway`, which sets no flag; `OnTransition` re-shows the object on re-entry. Mew additionally treats `B_OUTCOME_MON_TELEPORTED` as recoverable (Mew can Teleport out). | `SkyPillar_Top/scripts.inc`; `FarawayIsland_Interior/scripts.inc:135-138` |
| Flag **ids** cross-validate against our own ROM tables | **CONFIRMED** | `FLAG_DEFEATED_RAYQUAZA 0x1C0`=448, `REGIROCK 0x1BB`=443, `LATIAS_OR_LATIOS 0x1C8`=456, `HO_OH 0x1DC`=476, `DEOXYS 0x1AC`=428 — all match our table exactly. | `include/constants/flags.h:466,481-486,494-495,516-517` vs `sandbox-pokebot/modules/data/event_flags/emerald.txt` |
| ‼ **Naming gotcha for our code** | **NEW** | Our flag table stores names **without** the `FLAG_` prefix (`DEFEATED_RAYQUAZA`, not `FLAG_DEFEATED_RAYQUAZA`). `get_event_flag("FLAG_DEFEATED_RAYQUAZA")` is a phantom name → silently False forever (the Ch9a failure mode). | `sandbox-pokebot/modules/data/event_flags/emerald.txt`; `tools/story-dev/audit_flag_names.py` builds its valid set from `parts[1]` of that file |
| "Elite Four rematches do not respawn defeated legendaries" | **CONFIRMED (narrow)** | Respawn is gated *solely* on `FLAG_DEFEATED_X` being unset, and nothing in any of the 11 legendary map scripts read clears it. This is an absence result limited to those files — but it is the only place a respawn could live, since the gate is in their own `OnTransition`. | the 11 `scripts.inc` files listed above |
| Roamer IV glitch "fixed in Emerald"; roamer moves on map transition; Kyogre knows Double-Edge; Rayquaza knows Outrage; Mew's hide-and-seek pathing | **UNRESOLVED** | Not checked. Roamer generation and level-up learnsets were not read. The two "self-KO move" traps are the load-bearing ones for a False-Swipe strategy — verify against `src/data/pokemon/level_up_learnsets.h` before automating either fight. | — |

### 1d. `c11` — "Single-use TMs, and the HM-forgetting restriction"

| claim | verdict | the actual truth | source |
|---|---|---|---|
| **TM01–TM50 are single-use; HM01–HM08 are not consumed** | **CONFIRMED** | `Task_LearnedMove`: `if (item < ITEM_HM01) RemoveBagItem(item, 1);`. One `sTMHMMoves` table backs both, HMs indexing past TM50 (`ItemIdToBattleMoveId`). | `src/party_menu.c:4769-4780`, `:4688-4692` |
| Is the TM consumed when it *replaces* a move? | **CONFIRMED — yes** | `Task_PartyMenuReplaceMove` sets the new slot then calls `Task_LearnedMove(taskId)`, which runs the same `RemoveBagItem`. `gPartyMenu.data[1]` is set to 0 by `ItemUseCB_TMHM`, so the guard passes. | `src/party_menu.c:4882-4895`, `:4746`, `:4775-4780` |
| Is the TM consumed if the bot **cancels** the "which move to forget" prompt? | **NEW / CONFIRMED — NO, it is safe** | Declining routes to `StopLearningMovePrompt` → `Task_StopLearningMoveYesNo`; `Task_LearnedMove` is never reached, so `RemoveBagItem` never runs. **Backing out of a TM is free.** | `src/party_menu.c:4824-4839`, `:4897-4913` |
| "HMs cannot be overwritten by level-up moves or TMs" | **CONFIRMED — mechanism identified** | `CanReplaceMove()` returns FALSE iff the highlighted move `IsMoveHm()` **and** `newMove != MOVE_NONE`; failure shows `gText_HMMovesCantBeForgotten2` = `"HM moves can't be\nforgotten now."`. The `newMove != MOVE_NONE` term is exactly why the Move Deleter (which enters with `newMove == MOVE_NONE`) *can* delete HMs. | `src/pokemon_summary_screen.c:2246-2254`, `:2256-2265`, `:3735-3739`; `src/strings.c:516`; `src/party_menu.c:4694-4704` |
| **"The Move Deleter checks if deleting Surf/Dive will strand the player; `IsMonValidForMoveDeleter` returns FALSE… If the bot brute-forces this it loops in the UI"** | **REFUTED as stated; a weaker real guard exists** | There is **no `IsMonValidForMoveDeleter`** anywhere. The real guard is a script-level `special IsLastMonThatKnowsSurf` before `special MoveDeleterForgetMove`, and it covers **`MOVE_SURF` ONLY** — checking the rest of the party *and* the PC boxes (`AnyStorageMonWithMove`), with **no location/island condition at all**. `MoveDeleterForgetMove()` itself is unconditional. ⇒ **Dive, Waterfall, Fly, Strength, Rock Smash, Cut and Flash are entirely unprotected.** | `data/maps/LilycoveCity_MoveDeletersHouse/scripts.inc:37-39,63-64`; `src/party_menu.c:6407-6430`, `:6368-6376` |
| Move Deleter is in Lilycove City; refuses a mon with 1 move; refuses eggs | **CONFIRMED** | Script path is `data/maps/LilycoveCity_MoveDeletersHouse/`; it calls `special GetNumMovesSelectedMonHas` → `goto_if_eq VAR_RESULT, 1, …_MonOnlyKnowsOneMove` and `special IsSelectedMonEgg`. | same file, lines 17-22; `src/party_menu.c:6348-6357` |
| TM-compatibility helper is `CanSpeciesLearnTMHM()` in `pokemon_summary_screen.c` | **REFUTED (wrong name/file)** | The real entry points are `CanMonLearnTMHM(mon, item - ITEM_TM01)` and `CanMonLearnTMTutor(mon, item, 0)`, both in `src/party_menu.c`. | `src/party_menu.c:2042`, `:4748` |
| Move Relearner cost/behaviour, tutor flags, Heart-Scale scarcity, Hidden Power BP=0, Gen-3 physical/special split by type | **UNRESOLVED** | Not checked. (The type-based split boundary at `TYPE_MYSTERY` (9) — physical 0-8, special 10-17 — is consistent with `include/constants/pokemon.h` but that file was not read this session.) | — |

### 1e. `c02` spot-check — catch formula and ball multipliers

The whole calculation lives in one function, which I read in full:
`src/battle_script_commands.c:9905-10053` (`Cmd_handleballthrow`), table at `:841-847`.

```c
odds = (catchRate * ballMultiplier / 10)
     * (gBattleMons[t].maxHP * 3 - gBattleMons[t].hp * 2)
     / (3 * gBattleMons[t].maxHP);
if (status1 & (STATUS1_SLEEP | STATUS1_FREEZE))                        odds *= 2;
if (status1 & (STATUS1_POISON|STATUS1_BURN|STATUS1_PARALYSIS|STATUS1_TOXIC_POISON)) odds = (odds * 15) / 10;
if (odds > 254) /* caught outright */
else { odds = Sqrt(Sqrt(16711680 / odds)); odds = 1048560 / odds;
       for (shakes = 0; shakes < BALL_3_SHAKES_SUCCESS && Random() < odds; shakes++); }
```

| claim | verdict | the actual truth | source |
|---|---|---|---|
| Formula shape / truncation order | **REFUTED (ordering)** | Real order is `(catchRate × ballMult / 10)` **first** — that division truncates before the HP term — then `× (3·maxHP − 2·hp)` then `/ (3·maxHP)`. The note applies the HP fraction first and folds status into a single `/10`. Numerically different at the margins; a throw policy computed from the note will mispredict. | `:9987-9989` |
| Status multipliers are 2.0 / 1.5 / 1.0 | **CONFIRMED, but** | Sleep/Freeze is an exact `odds *= 2`; PSN/BRN/PAR/TOXIC is `(odds*15)/10`. **They are independent `if`s, not `else if`** — asleep **and** poisoned stacks to ×3.0. The note misses this. | `:9991-9994` |
| `a ≥ 255` ⇒ instant catch | **CONFIRMED** | `if (odds > 254)` | `:10009` |
| Shake maths `b = 1048560 / Sqrt(Sqrt(16711680/a))` | **CONFIRMED** | verbatim | `:10025-10026` |
| "RNG called 4 times, each must be < b" | **CONFIRMED, with a caveat** | `BALL_3_SHAKES_SUCCESS == 4` (enum `BALL_NO_SHAKES=0 … BALL_3_SHAKES_SUCCESS=4`). The loop **short-circuits**, so it is *up to* 4 `Random()` calls — 1 on an immediate fail. Matters for any RNG-frame accounting. | `:10028`; `include/battle_controllers.h:135-140` |
| **Master Ball "bypasses the formula"** | **REFUTED** | The odds are computed and the shake loop **runs and consumes RNG**; `shakes` is only *then* forced to success (the decomp even comments "why calculate the shakes before that check?"). Guaranteed catch: yes. Formula skipped: no. | `:9987-10031` |
| Master Ball's table lookup | **NEW / CONFIRMED (quirk)** | `ITEM_MASTER_BALL (1) - ITEM_ULTRA_BALL (2) = -1` ⇒ `sBallCatchBonuses[-1]`, an out-of-bounds read. Harmless in vanilla only because `shakes` is overwritten. **Never model Master Ball via the bonus table.** | `:9982-9984`; `include/constants/items.h:7-18` |
| Poke 1.0 / Great 1.5 / Ultra 2.0 / Safari 1.5 | **CONFIRMED** | `sBallCatchBonuses = { [ULTRA]=20, [GREAT]=15, [POKE]=10, [SAFARI]=15 }` | `:841-847` |
| Net 3.0× on Water **or** Bug | **CONFIRMED** | `IS_BATTLER_OF_TYPE(target, TYPE_WATER) \|\| …TYPE_BUG` → 30, else 10 | `:9941-9946` |
| **Dive Ball 3.5× "if surfing, fishing, or underwater"** | **REFUTED** | `if (GetCurrentMapType() == MAP_TYPE_UNDERWATER) ballMultiplier = 35; else 10;` — **underwater ONLY.** Surfing and fishing get 1.0×. | `:9947-9952` |
| **Nest Ball `floor((41 − Level)/10)`** | **REFUTED** | `if (level < 40) { mult = 40 - level; if (mult <= 9) mult = 10; } else mult = 10;` ⇒ multiplier = `max(40 − L, 10) / 10`: 3.9× at L1, 2.0× at L20, 1.0× at L≥30. | `:9953-9964` |
| Repeat 3.0× if dex-caught | **CONFIRMED** | `GetSetPokedexFlag(SpeciesToNationalPokedexNum(species), FLAG_GET_CAUGHT)` → 30 else 10 | `:9965-9970` |
| Timer Ball, max 4.0× at 30 turns | **CONFIRMED (value), REFUTED (formula shape)** | `mult = gBattleResults.battleTurnCounter + 10`, capped at 40 ⇒ multiplier `(turns+10)/10` as a rational — 1.5× at turn 5, not the note's floored 1×. Cap reached at turn 30. | `:9971-9975` |
| Luxury / Premier = 1.0× | **CONFIRMED** | `case ITEM_LUXURY_BALL: case ITEM_PREMIER_BALL: ballMultiplier = 10;` | `:9976-9979` |
| Critical Capture does not exist in Gen 3 | **CONFIRMED** | No such branch anywhere in `Cmd_handleballthrow`. | `:9905-10053` (read in full) |
| "Safari Zone: the standard `a` formula does not apply" | **REFUTED** | The **same** formula applies; only `catchRate` is substituted: `catchRate = gBattleStruct->safariCatchFactor * 1275 / 100`, with ballMultiplier 15 from the Safari table entry. | `:9932-9933`, `:841-847` |
| **`c02` trap: "if the currently selected PC box is full (30/30) the game prohibits throwing any ball; it does not auto-switch boxes"** | **REFUTED twice** | It **does** auto-wrap through all 14 boxes, and the prohibition requires **all 420 slots** full. See §1b. | `src/pokemon.c:4447-4479`, `:4620-4629` |
| Ball-pocket slot/stack limits (16 slots × 99) | **UNRESOLVED** | Not checked. | — |

---

## 2. DESIGN CONSEQUENCES

### Boss-training mode is VALID — keep it, but fix one assumption
`_prepare_for_fight`'s premise holds: XP banked from KOs is kept after a whiteout; the cost is
half your money and a warp to the last heal point. **However**, EXP is awarded only to party members
that are **alive at the instant the opponent faints** (`battle_script_commands.c:3367`, `:3431`).
So:
* Sequence the trainee so it **survives** each KO it earns. A mon that trades a KO for its own life
  (recoil, Destiny Bond, simultaneous faint) banks nothing from that kill.
* The whiteout must be the *last* event, not a mid-strategy tool: **model the money cost** (`money /= 2`
  per whiteout, `overworld.c:361`) and prefer walking back to a Centre when PP runs low.
* Recompute expected XP with the **real** multiplier order (split first, then per-mon ×1.5s). Any
  XP-per-frame table built from `c12`'s formula is wrong at the margins.
* Use the symbol **`gSpeciesInfo`**, not `gBaseStats`.

### Ball throws: you do NOT need a pre-throw box-space check — you need a **menu-loop guard**
The ROM already refuses the throw and keeps the ball (`item_use.c:938-956`). The bot's real risk is
the opposite of what `c01` feared: an infinite "select ball → 'The BOX is full.' → back to bag" loop
that never advances the battle.
* Detect on the **item count**: if a throw was issued and the ball quantity did not decrement, treat
  it as a hard "storage full" and exit the battle (run/flee), do not retry.
* Match on the exact string `"The BOX is full."` if matching text at all.
* Do **not** treat the "box was full, so I used <box>" message as a failure — it is cosmetic, one-shot,
  and latched by `FLAG_SHOWN_BOX_WAS_FULL_MESSAGE` (`field_specials.c:3405-3416`).
* Keep a soft capacity policy anyway (clear boxes well before 420) so the bot never *reaches* the
  wedge state — and never write to `gPokemonStoragePtr` to make room, because
  `Cmd_givecaughtmon` has no `MON_CANT_GIVE` branch (`battle_script_commands.c:10057`): any hack that
  desynchronises the fullness check from reality silently destroys a caught Pokémon.

### Legendary hunting: two safety checks in the notes are broken as written
1. **Never gate roamer safety on a flag.** Use `modules/roamer.get_roamer() is not None` — it reads
   byte `0x13` (`active`) of the roamer struct, which is exactly what `SetRoamerInactive()` clears
   (`roamer.py:148-166`; `roamer.c:237-239`). `FLAG_DEFEATED_LATIAS_OR_LATIOS` will read False forever
   for a roamer.
2. **The roamer is destroyed by more than a KO.** Any battle outcome with an odd value ends it:
   WON, **DREW (mutual KO)**, **PLAYER_TELEPORTED**, CAUGHT, FORFEITED. Concretely: the bot must
   **never use Teleport (or anything that produces `PLAYER_TELEPORTED`) to leave a roamer battle**, and
   must never let a mutual KO happen. The safe exits are the ordinary **Run** (`B_OUTCOME_RAN`), a
   whiteout (`B_OUTCOME_LOST`), or letting it flee (`B_OUTCOME_MON_FLED`).
3. **`FLAG_DEFEATED_<RAYQUAZA|GROUDON|KYOGRE|REGIROCK|REGICE|REGISTEEL>` is set on a successful
   CATCH too.** Never read it as "I destroyed this one". To decide "is this species still obtainable",
   check the flag **and** whether the species exists in party/PC/Pokédex-caught. Ho-Oh, Lugia, Mew,
   Deoxys and Southern-Island Lati@s do have distinct caught flags and are safe to reason about directly.
4. **Whiteout is the safe abort for every scripted static** — losing means the script never resumes and
   no flag is written. So the recovery policy for a static-legendary attempt should be
   "lose the fight" long before it is "risk a KO". (Exception: a DREW against the roamer still kills it.)
5. Our flag helpers take names **without** the `FLAG_` prefix (`"DEFEATED_RAYQUAZA"`). Extend
   `tools/story-dev/audit_flag_names.py`'s file list to any new module that reads these.

### Move management
* **Cancelling a TM is free** (`party_menu.c:4824-4839`). So the safe protocol is: open the TM, read
  the "needs to replace a move" prompt, evaluate, and back out if no slot is worth losing — no risk of
  burning the TM. Only `Task_LearnedMove` consumes it, and only after a move actually changes.
* **The Move Deleter protects Surf and nothing else.** `IsLastMonThatKnowsSurf` (`party_menu.c:6407-6430`)
  covers `MOVE_SURF` only, party **and** boxes, with no island condition. Deleting the last **Dive**
  (Sootopolis / underwater), **Waterfall**, **Fly**, **Strength**, **Rock Smash** or **Cut** is
  unguarded and can hard-strand the run. ⇒ The bot must own this invariant itself: maintain an
  HM-coverage set over party+PC and refuse any deletion/release that would empty it. Do **not** rely
  on the game refusing, and delete the note's claimed `IsMonValidForMoveDeleter` from any design doc.
* HMs cannot be chosen as the move to forget when learning a new one (`CanReplaceMove`,
  `pokemon_summary_screen.c:2246-2254`) — so a mon with 4 HMs is combat-dead until Lilycove. Cap HMs
  per mon at design time.

### Throw policy must be recomputed
Three of the numbers a throw policy would use are wrong in `c02`:
* **Dive Ball is 1.0× unless the map type is UNDERWATER** — worthless while surfing or fishing.
  Any "Dive Ball for water encounters" heuristic is a pure waste of a better ball.
* **Nest Ball is `max(40−L,10)/10`**, not `floor((41−L)/10)`; **Timer Ball is `(turns+10)/10`**, a
  rational, not a floored integer. Both are *better* than the note at low turn counts / mid levels.
* **Master Ball consumes RNG** and its table index underflows — special-case it entirely.
* Sleep **stacks** with poison/burn (×3.0). Worth knowing even though the project rightly refuses to
  poison a catch target (it can die to end-of-turn damage at 1 HP).
* Compute `a` in the ROM's exact order, with the `(catchRate × ballMult / 10)` truncation first.

---

## 3. STILL UNRESOLVED — and what would settle each

| open question | why it matters | the evidence that settles it |
|---|---|---|
| Do Kyogre/Rayquaza actually know Double-Edge / Outrage at Lv 70? | These two traps decide whether a False-Swipe hunt is safe at all. If false, `c09`'s "never attempt unsupervised" is over-cautious; if true, it is load-bearing. | Read `src/data/pokemon/level_up_learnsets.h` for `SPECIES_KYOGRE`/`SPECIES_RAYQUAZA` up to L70, or dump `gEnemyParty[0]` moves from a live probe on a real save at the encounter. |
| `CanReleaseMon` semantics; can a Bad Egg corrupt adjacent box slots? | `c01` calls Bad-Egg contagion FATAL; it is the kind of unsourced folk claim that has already burned this project once. | Read the release path in `src/pokemon_storage_system.c`; the contagion claim needs either decomp evidence or an emulator experiment (do not attempt on a real save). |
| Growth-rate curves and `gExperienceTables` values | Needed for accurate "levels remaining" planning. | `src/data/pokemon/experience_tables.h` (in the tree, unread). |
| Match Call rematch trigger probabilities; Gabby & Ty's "always ready on relocation" | `c12` Strategy 2 rests entirely on this. | `src/match_call.c` + the Gabby/Ty scripts. |
| Move Relearner cost/eligibility; tutor flag names; Heart Scale sources | Resource planning only; no irreversible risk identified. | `data/maps/FallarborTown_House2/scripts.inc`, `src/data/pokemon/tutor_learnsets.h`, `audit_flag_names.py` for each `TUTOR_*`. |
| Hidden Power BP-0 handling; Gen-3 physical/special split constants | Scoring accuracy only. | `src/data/battle_moves.h`, `include/constants/pokemon.h`. |
| Ball-pocket slot/stack limits | Buying policy only. | `include/constants/items.h` / `src/item.c` pocket capacities. |
| Roamer IV generation; Emerald "roamer IV glitch fixed" | Shiny/IV hunting only. | `CreateInitialRoamerMon` in `src/roamer.c:84-100` (fetched but not read in detail) + `CreateRoamerMonInstance`. |
| Concept notes `c03`–`c08`, `c10` | Entirely unexamined this pass. | Still LEADS. Nothing in them should reach code unvalidated. |

---

## 4. METHOD

**What worked.** `gh api repos/pret/pokeemerald/contents/<path> --jq '.content' | base64 -d` worked on
every call, for both `src/*.c` and `data/maps/*/scripts.inc`. For files past the base64 content limit
(`src/data/pokemon/species_info.h`, ~11.7 k lines) `gh api … -H "Accept: application/vnd.github.raw"`
worked. `gh api -X GET "search/code?q=<symbol>+repo:pret/pokeemerald"` was the right tool for locating
a definition when it was not in the file that called it (`ShouldShowBoxWasFullMessage` → `field_specials.c`,
`HealPlayerParty` → `script_pokemon_util.c`, `IsLastMonThatKnowsSurf` → `party_menu.c`). No WebFetch
fallback was needed.

**Cross-checks against our own data** (a second, independent ground truth) agreed with the decomp on
every point tested: legendary catch rates in `modules/data/species.json` matched `species_info.h`
exactly, and five legendary flag **ids** in `modules/data/event_flags/emerald.txt` matched
`include/constants/flags.h` exactly. `audit_flag_names.py` takes no CLI arguments (it scans a fixed
file list) — it reported `all names valid` for the current story modules; the flag-name check here was
done by reading its source table directly.

**Coverage.** 5 notes examined, **51 individual claims ruled**: 30 CONFIRMED, 15 REFUTED, 6 grouped
UNRESOLVED buckets (listed in §3). **Every CONFIRMED and REFUTED ruling cites a file I fetched and
read this session** — no ruling rests on recall. Nine findings are marked **NEW**: facts the notes did
not contain that change how the bot must behave (fainted mons bank zero EXP; `Cmd_givecaughtmon` has no
`MON_CANT_GIVE` branch; the box-was-full message is cosmetic; the roamer dies on DREW/PLAYER_TELEPORTED;
`FLAG_DEFEATED_*` doubles as "caught" for six species; cancelling a TM is free; the Move Deleter guards
Surf only; Master Ball consumes RNG and underflows its table; sleep stacks with poison).

**What I deliberately did not do.** I did not run a live emulator probe — every claim in scope was
decidable from source, and the decomp is the stronger authority for control-flow questions like
"does the script resume after a whiteout". The claims that *would* need a probe (or at minimum the
learnset tables) are exactly the ones parked in §3.

**Note on the notes.** `c09`'s and `c11`'s narrative conclusions were largely right while their
*mechanisms* were wrong — and the mechanism is what code depends on. `c09` named the correct flags and
the correct verdict ("KO = permanent loss") but attributed the roamer to a flag that never gets set and
missed three additional roamer-killing outcomes. `c11` correctly warned about stranding but invented the
function that supposedly prevents it, and the real guard covers one move out of eight. This is the same
failure shape recorded earlier in `00-READ-THIS-FIRST.md`: confident, well-formatted, structurally
plausible, and wrong exactly where it costs something.
