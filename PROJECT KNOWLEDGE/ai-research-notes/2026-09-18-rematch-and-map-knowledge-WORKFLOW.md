# REMATCH LEDGER + MAP KNOWLEDGE — 11-AGENT WORKFLOW SYNTHESIS (2026-09-18)

> ⛔⛔ **AGENT OUTPUT IS A NOTE, NEVER TRUTH.** 5 research angles, each adversarially verified, then
> synthesised. 11 agents, 0 errors, ~38 min, 1.75M subagent tokens. Commissioned by the USER
> DIRECTIVE of 2026-09-18 (`06-DECISIONS-LOG.md`).
> ‼ **READ ITS §7 (REFUTED / WITHDRAWN) BEFORE QUOTING ANYTHING FROM IT.**

---

# ⭐ THE HEADLINES, AND WHAT THEY MEAN FOR US

**⭐⭐ BOTH OF THE USER'S RECOLLECTIONS ARE CONFIRMED** — one exactly, one with a precision correction:
* *“ordinary rematches after the 5th gym (Norman)”* → **CONFIRMED IN SUBSTANCE**: the gate is
  **FIVE BADGES**, not Norman by name, and it is spelled **two different ways** — the walking path
  counts ANY five (`HasAtLeastFiveBadges`), the phone path counts a **sequential prefix** that stops
  at the first missing badge (`GetNumOwnedBadges`). In vanilla order they coincide. ‼ **the bot's
  condition must be the CODE's, not the story's.**
* *“gym leaders after the Hall of Fame”* → **CONFIRMED EXACTLY**: gated on `FLAG_SYS_GAME_CLEAR`.

**⭐⭐ AND THE COST QUESTION IS ANSWERED THE GOOD WAY: FIGHTING REMATCHES NEEDS *ZERO* POKÉNAV WORK.**
The game ARMS; the player always STARTS. Accepting an armed rematch is *walk to the NPC, face, A,
advance the dialogue* — primitives we already have. The PokéNav can arm an ordinary trainer via an
outgoing call, but the WALKING path arms for free, and the armed state is readable straight from
SaveBlock1 rather than by opening the app. ⇒ **the “we would need PokéNav menu-driving” cost estimate
I gave earlier was wrong for the battle half.**

**⛔⛔ THE FINDING THAT MATTERS MOST TO §Ch24, AND IT IS A TRAP WE ALREADY HALF-KNEW:**
`ResetEliteFour` is called from `data/scripts/hall_of_fame.inc` **AND from `EventScript_WhiteOut`**
⇒ **a whiteout ANYWHERE IN HOENN clears `FLAG_DEFEATED_ELITE_4_*`.** ‼ Our handoff already carried a
narrowed version of this (*“those flags ARE the correct PER-ROOM VICTORY signal … cleared on BOTH the
loss AND the win path”*); this supplies the MECHANISM and widens it. ⇒ **never use those flags as
evidence the bot beat the league** — which is exactly why USER RULING 11's conjunct (1) is the Hall of
Fame / `SYS_GAME_CLEAR`, and why `#24-markerwinstate` chose `IS_CHAMPION`. Consistent; no change
needed, but the reason is now documented.

**⛔ A TRAP IN THE PROJECT'S OWN FAVOURITE SHAPE — “A CANDIDATE IS NOT AN ATTEMPT”:**
`ShouldTryRematchBattle` returns TRUE **forever** once the second ladder step has been beaten, so
talking to that trainer ALWAYS takes the rematch branch and the un-armed case falls silently through
to post-battle text. ⇒ **assert the BATTLE, or the cleared `trainerRematches[i]` — never the dialogue
branch.** This is `CLAUDE.md` §7 almost verbatim, arriving from the decomp.

⚠ **NOT VERIFIED BY ME:** everything below this line, including the SaveBlock1 offsets (`+0x9C8`,
`+0x9CA`), which the note itself marks as **INFERRED for our BPEE0 — never probed**. Verify before
any code reads them.

---

# REMATCH + MAP-KNOWLEDGE NOTE — synthesis of 5 researched + adversarially-verified angles
**2026-09-18 · READ-ONLY pass · THIS IS A NOTE, NEVER TRUTH.** Decomp refs are `pret/pokeemerald@5eff786` unless stated. Repo refs are absolute. Markers: **VERIFIED** = confirmed at a cited line by an adversarial pass that re-fetched the source; **RE-CONFIRMED IN-SESSION** = I re-ran the check myself just now; **INFERRED** = design/arithmetic, not observed; **NOT CHECKED** = nobody looked.

---

## 1. THE ANSWER TO THE USER'S POKÉNAV QUESTION

### Who initiates
**The GAME arms. The PLAYER always starts.** The PokéNav can *arm* a rematch (ordinary trainers only) but can never *start* one.

| Question | Answer | Evidence |
|---|---|---|
| Can the PokéNav start a battle? | **NO.** `BattleSetup_StartRematchBattle` appears in exactly 4 paths repo-wide (`include/battle_setup.h`, `src/battle_setup.c`, `data/scripts/trainer_battle.inc`, `data/specials.inc`); none of the 14 `src/pokenav_*.c` files references it. Its only A-button actions are CALL / CHECK / CANCEL. | VERIFIED `src/pokenav_match_call_list.c:149-166` |
| Does the trainer ring you? | **YES**, unprompted, for ordinary trainers only. | VERIFIED `src/match_call.c:1325` (`MatchCall_PrintIntro` → `SelectMatchCallMessage`) |
| Can you ring them? | **YES**, and that call CAN arm the rematch. Same decider both directions: `else if (ShouldTrainerRequestBattle(matchCallId)) { … UpdateRematchIfDefeated(matchCallId); }` | VERIFIED `src/match_call.c:1524-1528`; outgoing entry `src/pokenav_match_call_list.c:351-364`; arming `src/battle_setup.c:1631-1635` |
| Do gym leaders ring you? | **NEVER**, and calling one can never arm. Incoming selection is bounded to rows 0-63; outgoing takes the `isSpecialTrainer` branch into read-only canned text. | VERIFIED `src/match_call.c:1118-1144` (comment at `:1117`: *"Ignores … special trainers like Wally and the gym leaders"*); `src/pokenav_match_call_data.c:1022-1058` |
| Does a defeated trainer re-approach you in the overworld? | **NEVER.** `CheckTrainer` returns before approach distance is consulted once the trainer flag is set. | VERIFIED `src/trainer_see.c:271` |
| Registration cost | **Free side-effect of winning**, if you hold Match Call. No prompt. | VERIFIED `src/battle_setup.c:1754-1762` `RegisterTrainerInMatchCall` |
| Accepting an armed rematch | face → A → intro speech → one button press → battle. **No yes/no prompt, no menu.** | VERIFIED `data/scripts/trainer_battle.inc` `EventScript_TryDoRematchBattle` |

**⇒ Architecture consequence: fighting rematches needs ZERO PokéNav work.** It is `walk to NPC + face + A + advance dialogue` — primitives we already have.

### Gate (a) — ordinary trainers: "after the 5th gym (Norman)" — **CONFIRMED IN SUBSTANCE, with a precision correction**
The gate is **FIVE BADGES**, not Norman by name, and it is spelled **two different ways**:
- Walking path: `HasAtLeastFiveBadges()` — counts **any** five (`if (++count >= 5) return TRUE;`). VERIFIED `src/battle_setup.c:1776-1790`.
- Phone path: `GetNumOwnedBadges()` — a **sequential prefix** count that `break`s at the first missing badge; gate `if (GetNumOwnedBadges() < 5) return FALSE;`. VERIFIED `src/match_call.c:1868-1878`, gate at `:1890`.
- Badge 5 = Norman. VERIFIED `data/maps/PetalburgCity_Gym/scripts.inc` (`setflag FLAG_DEFEATED_PETALBURG_GYM` beside `setflag FLAG_BADGE05_GET`).

In vanilla order the two coincide, so the user's memory is right. **The bot's condition must be the code's, not the story's.**

### Gate (b) — gym leaders: "after the Hall of Fame" — **CONFIRMED EXACTLY**
`if (FlagGet(FLAG_SYS_GAME_CLEAR) && (Random() % 100) <= 30)` — VERIFIED `src/gym_leader_rematch.c:32-41`. Flag set in `GameClear()`, VERIFIED `src/post_battle_event_funcs.c:27-30`, immediately before `CB2_DoHallOfFameScreen`.

### The three classes are three different systems

| Class | Rows | Armed by | Rate | PokéNav? |
|---|---|---|---|---|
| Ordinary trainers | 0-63 | 255-step counter + per-map-load 31% roll **OR** a phone call | see below | arm yes / battle no |
| Wally (Victory Road) | 64 | walking path only (inclusive loop bound) | 31%/map load | **excluded** from both call directions |
| Gym leaders | 65-72 | **battle counter**, never steps, never phone | ~1 arming / 65 trainer battles | read-only text |
| Elite Four + Wallace | 73-77 | **HARD-EXCLUDED from the rematch system** | n/a | listed only |

- **Ordinary/walking (VERIFIED `src/battle_setup.c:1605-1629`, `:1792-1817`):** counter ticks only at ≥5 badges; on *every* map load each registered, unarmed, non-forbidden row whose map == the loaded map rolls `(Random() % 100) <= 30` = **31.0%**, with **no `break`** — several can arm in one entry. A total miss leaves the counter at 255 ⇒ **free re-roll on re-entry**. Entering a map where someone is already armed burns the counter to 0 — *but the other unarmed rows still roll on that same entry* (the loop does not break).
- **⭐ Gym leaders are rate-limited by a modulo the first pass missed:** `TryUpdateGymLeaderRematchFromWild` is `% 60`, `FromTrainer` is `% 20`. VERIFIED `src/battle_setup.c:956-966`. ⇒ **~1 arming per 65 trainer battles or ~194 wild battles**, not 31% per battle. Both counters are live simultaneously, and `GAME_STAT_TRAINER_BATTLES` is also an input to the phone hash — the two systems are coupled.
- **Hidden gym sub-gate:** before `FLAG_WATTSON_REMATCH_AVAILABLE` (the New Mauville errand), 7 leaders with `maxRematch=1` and **Wattson excluded entirely**; after, 8 leaders with `maxRematch=5` (effectively no cap). VERIFIED `src/gym_leader_rematch.c:21-30, 36-39, 59`; flag set at `data/maps/MauvilleCity/scripts.inc:15-18`.
- **Elite Four:** `if (rematchTableId >= REMATCH_ELITE_FOUR_ENTRIES) return TRUE;` VERIFIED `src/battle_setup.c:1576-1586`. All five ladder slots hold the same trainer id. They re-arm via `ResetEliteFour`, called from `data/scripts/hall_of_fame.inc:7` **and from `EventScript_WhiteOut`** (`data/event_scripts.s:585-588`). ⛔ **A whiteout anywhere in Hoenn clears `FLAG_DEFEATED_ELITE_4_*` — never use those flags as evidence the bot beat the league.**

### Consumption + ladder
One arming = one battle. **A WIN clears it; a LOSS preserves it** (the defeat branch goes to `CB2_WhiteOut` and returns before `HandleRematchVarsOnBattleEnd`). VERIFIED `src/battle_setup.c:1351-1368`, `:1733-1739`. `trainerRematches[i]` stores the **ladder step 1-5**, not a boolean; the top team repeats forever (`return trainerEntry->trainerIds[REMATCHES_COUNT - 1]; // already beaten at max stage`, VERIFIED `src/battle_setup.c:1691-1716`). **No level scaling ever.**

### Reading the state — no UI required
`SaveBlock1 +0x9C8 u16 trainerRematchStepCounter`, `+0x9CA u8 trainerRematches[100]` (78 used). VERIFIED `include/global.h:1015-1016`, `include/constants/global.h:61`. Accessor exists: `get_save_block(1, offset, size)` at `C:\Remote Projects\Pokebot_Gen3_Enhancement\sandbox-pokebot\modules\memory.py:119`. **The 0x9CA offset has NOT been probed on our BPEE0 — INFERRED for our ROM.** The only in-game indicator is a Poké Ball icon in the Match Call list, drawn from exactly this array (`src/pokenav_match_call_list.c:315-327`) — so reading RAM is strictly better than opening the app.

### ⛔ Three traps that will bite a naive implementation
1. **CANDIDATE IS NOT AN ATTEMPT.** `ShouldTryRematchBattle` returns TRUE *forever* once `trainerIds[1]` has been beaten (`WasSecondRematchWon`), so talking to that trainer **always** takes the rematch branch — the un-armed case falls silently through to post-battle text. VERIFIED `src/battle_setup.c:1839-1845`, `:1764-1774`. **Assert the battle, or the cleared `trainerRematches[i]` — never the dialogue branch.**
2. **Double battles.** All 8 gym rematches **plus 5 ordinary rows** (`LILA_AND_ROY_1`, `ANNA_AND_MEG_1`, `JOHN_AND_JAY_1`, `KIRA_AND_DAN_1`, `AMY_AND_LIV_1`) use `trainerbattle_rematch_double`. With <2 usable mons the interaction prints a refusal and burns nothing. The ledger needs an `is_double` column, not a gym footnote. VERIFIED (14 files carry the macro).
3. **Norman MOVES as a function of rematch state, in the hostile direction.** `goto_if_eq VAR_RESULT, TRUE, PetalburgCity_Gym_EventScript_DontMoveNormanToFront` — i.e. **exactly when he is armed he stays at the BACK**, behind the room maze. VERIFIED `data/maps/PetalburgCity_Gym/scripts.inc:41, 52-58`. Also: the rematch row's map field names the **CITY** (`MAP_PETALBURG_CITY`), not the gym interior — a naive "row → map → walk there" lands outside the building.

---

## 2. THE REMATCH LEDGER

**Status: COMPLETE, 78/78 rows, NOT a subset — for WHO / WHAT PARTY / HOW MUCH at the TOP tier.** Built by one agent and then **rebuilt from scratch by a second, independent parser** over `src/battle_setup.c` (gRematchTable), `src/data/trainers.h`, `src/data/trainer_parties.h`, `src/data/pokemon/species_info.h`, cross-checked against our own `sandbox-pokebot/modules/data/species.json`. **Every species, level, $ and exp reproduced EXACTLY — zero discrepancies, two oracles.** VERIFIED.

**⭐ The artifact already exists.** `…\scratchpad\ledger.json` — 78 rows, each `{tid, name, cls, dbl, party[[species,lvl]…], items, cash, exp, exp_ours, last, mult, idx, key, map, ids[5]}`, with `exp` (decomp) and `exp_ours` (our species.json) equal on every row. Generator: `…\scratchpad\parse.py`. **RE-CONFIRMED IN-SESSION** (loaded, 78 rows, row 0 = ROSE/AROMA_LADY/Route118/$1360/e3269). ⇒ **Promote it; do not re-derive it.** Both files are in session-temp and will be lost.

### Formulas (every number below rests on these)
- **MONEY = 4 × level-of-the-LAST-mon-in-the-array × classMult × (2 if double) × (2 if Amulet Coin).** VERIFIED `src/battle_script_commands.c:5595, 5624-5629`; class table `src/battle_main.c:474-533` (LADY/RICH_BOY/CHAMPION 50, LEADER/ELITE_FOUR 25, BEAUTY/POKEFAN/GENTLEMAN 20, COOLTRAINER 12, TUBER 1, SWIMMER 2, default 5). **All figures below assume NO Amulet Coin.** Party size is irrelevant to payout.
- **EXP**: per fainted mon, pool = `floor(floor(baseExp × lvl / 7) × 1.5)` for a trainer battle. ⚠ The division by `viaSentIn` happens **before** the ×1.5 (`src/battle_script_commands.c:3314, 3324, 3378-3379`), so the published totals are **exact only for a ONE-participant battle and ~1-2% optimistic otherwise**.

### Money rank (top tier, one battle)
| # | Trainer | $ | # | Trainer | $ |
|---|---|---|---|---|---|
|1|Juan (D)|13,200|11|Winston|7,200|
|2|Tate&Liza (D)|13,000|12|Drake|5,500|
|3=|Norman (D)|12,000|13|Glacia|5,300|
|3=|Winona (D)|12,000|14|Phoebe|5,100|
|5|Wallace|11,600|15|Sidney|4,900|
|6=|Wattson (D)|11,000|16|John&Jay (D)|4,160|
|6=|Flannery (D)|11,000|17|Jessica|3,520|
|8=|Roxanne (D)|10,400|18|Wally VR|3,420|
|8=|Brawly (D)|10,400|19|Walter|3,280|
|10|Cindy|7,200|20|Thalia|3,200|

### EXP rank (top tier, total pool)
Juan 15,104 · Wallace 14,212 · Norman 14,074 · Tate&Liza 13,553 · Winona 12,797 · Flannery 12,285 · Roxanne 11,275 · Drake 10,932 · Wattson 10,632 · **Wally VR 10,073** · Brawly 9,832 · Glacia 9,060 · Phoebe 8,604 · Sidney 8,349 · **Gabrielle 7,273** · Lydia 6,252 · Isaac 5,840 · Elliot 5,798 · Nicolas 5,460 · Pablo 5,322.

### ⭐ Money-per-action outliers (the money answer)
**Cindy and Winston, both on `MAP_ROUTE104`: $7,200 EACH for ONE level-36 Linoone.** Next best per-mon is Miguel $3,040 (one Delcatty L38, Route 103), then Juan $2,200/mon. ⚠ Each carries 1× Full Restore — expect one AI heal. ⚠ They share Route 104 with Haley, so one 255-step cycle arms an **expected 0.93 of the three**, not both of the pair.

### Aggregates
| Block | $ | exp | mons | marker |
|---|---|---|---|---|
| E4 + Wallace, one lap | **32,400** | 51,157 | 26 | VERIFIED |
| All 8 leaders, top tier | **93,000** | 99,552 | 48 | VERIFIED |
| All 65 walk-pool rows (0-64), one sweep | **110,852** | **218,341** | 168 | **CORRECTED** — the source note's 107,432 / 208,268 omitted Wally's own row |
| Pre-New-Mauville, tier 1 only | Roxanne 7,400 · Brawly 7,400 · Flannery 8,000 · Norman 9,000 · Winona 9,000 · Tate&Liza 10,000 · Juan 10,200 · Wattson n/a | | | VERIFIED |

One E4 lap = **2.25** Cindy+Winston *pairs* (not 4.5).

### EV per 255-step cycle, by map (INFERRED arithmetic over VERIFIED inputs; `P(≥1)=1-0.69ⁿ`, `EV=0.31·Σ/P`)
**Money:** Route104 $6,899 · Route121 $4,048 · MeteorFalls_1F_2R $3,853 · VictoryRoad_1F $3,420 · AbandonedShip_Rooms_1F $3,200 · Route110 $3,183.
**EXP:** VictoryRoad_1F 10,073 · **MtPyre_3F 7,273** · Route117 6,276 · **Route106 5,798** · MeteorFalls 5,451 · Route126 5,322 · Route121 5,138.
*(Both lists corrected — the source swept only maps with n≥3 and missed the n=1 maps that outrank its entries.)*

### Held items (22 rows, VERIFIED exact)
3× Full Restore on every gym leader · 4× on Wallace · 2× on each E4 member and on Wally · 1× on Cindy, Winston, Brooke, Wilton, Catherine, Jackson · 1× Hyper Potion on Cristin.

### What the ledger does NOT contain
- **NPC overworld coordinates** — the blocker. 44 distinct maps across all 78 rows (35 of them in the walk pool). **Until this exists the ledger is unroutable.**
- Ladder tiers 1-4 (only the top tier is tabulated), IVs, movesets.
- ⚠ Three rows are **irregular**: `REMATCH_WALLY_VR` duplicates slot 4 (3 distinct rematch parties, not 4); `REMATCH_CINDY` skips `CINDY_2`; `REMATCH_AMY_AND_LIV` skips `_3`. A planner counting "5 tiers = 1 story + 4 rematches" over-counts Wally.
- The five E4/Wallace rows repeat one id five times — any ledger assuming 78×5 distinct `gTrainers` entries double-counts.

---

## 3. WHAT MAP KNOWLEDGE WE ALREADY HAVE

### Built and wired (all in `C:\Remote Projects\Pokebot_Gen3_Enhancement\sandbox-pokebot\`)

| Capability | Where | State |
|---|---|---|
| Tile pathing with **live** badge+party HM gating | `modules/map_path.py:787` (Surf/BADGE05), `:794` (Dive/BADGE07), `:802` (Waterfall/BADGE08), `:843` dynamic collision flags; `PathTile` `:57-84` carries `waterfall_to`, `muddy_slope_to`, `forced_movement_to`, `needs_acro_bike`, `blocked_exit_directions`, `elevation` | **Knows 3 of 8 HMs.** No Cut/RockSmash/Strength/Fly (grep: zero hits) |
| ⭐ Cross-map limit | `map_path.py:769-774` refuses when `source_tile.map.level != destination_tile.map.level` | **It refuses cross-REGION, not cross-map.** `level` = connected component of the N/E/S/W connection graph. 518 maps → **461 regions; largest = 49 maps (the mainland)**. One call CAN cross the whole mainland; it cannot cross a doorway. **CORRECTS the brief.** |
| World graph #1 | `modules/warp_graph.py` (447 lines), cache `cache/warp_graph_BPEE0.json` v2 — 518 maps, **1268 warp edges**, 61 connection entries | **No capability gating at all** |
| World graph #2 | `modules/story/region_reach.py` (524 lines) — BFS + gates, `reachable_maps`/`hops_to`/`is_map_reachable`/`why_unreachable` | **No disk cache**; rebuilt in-process from 518 `get_map_data()` calls |
| Cross-map navigation | `modules/modes/util/global_navigation.py:426 navigate_to_anywhere` — per-map legs, validates up to 6 candidate first-warps, re-plans after each warp | `_walk_is_possible` **returns True on unexpected error** (`:210-216`) — fails OPEN |
| ⚠ Walking across a map CONNECTION as an intermediate step | `global_navigation.py:48-98 _connection_step` | **DEFAULT OFF, `POKEBOT_CONNECTION_STEP=1`, MEASURED HARMFUL — "it then STRANDS the bot"**, with 2 named prerequisites |
| ⭐ Live-grid (`gBackupMapLayout`) reader | `modules/story/early_game.py:4144-4147 _live_passable()`; `modules/story/sootopolis.py:902` (collision) and `:971` (metatile id, each with a loaded-map guard); `modules/story/sootopolis_gym.py` — **already promoted to `custom-pokebot/`** | **EXISTS AND SHIPS. RE-CONFIRMED IN-SESSION.** Only `modules/map.py` has none |
| ⭐ Item-ball pickup primitive | `modules/story/early_game.py:8464 collect_item_ball(map, ball_tile, approach, facing, flag_name, item_name)` — 5 production call sites: `early_game.py:8579, 9226, 9230`, `pokemon_league.py:1100, 1140`. Approach-tile solver `pokemon_league.py:897 _ball_approach` | **EXISTS. RE-CONFIRMED IN-SESSION.** Already collects the Aqua Hideout Nugget + TM13. **Graded ON THE BAG, not on the flag** |
| Story gates | **13 entries, 4 tables. RE-CONFIRMED IN-SESSION by AST:** `KNOWN_GATES` **3** @ `region_reach.py:81`; `AREA_PREREQ` **6** @ `training_areas.py:270`; `AREA_ITEM_PREREQ` **1** @ `:312`; `NO_RETURN_GROUNDS` **3** @ `:333` | Everything not listed **fails OPEN** |
| Training grounds | **RE-CONFIRMED IN-SESSION:** `TRAINING_GRASS` **10 rows** @ `training_areas.py:64` + `PENDING_GRASS` **12** @ `:97` which are **behaviour-neutral** (`tile is None` ⇒ skipped) | Actionable coverage is **10 of 518 maps**, not 22 |
| Leader data | `modules/badge_case.py:126-143 BADGES` — 8 decomp-verified rows (leader, city, type, ace, `ace_level`, TM reward, HM granted), consumed live at `plugins/custom_modes/story_mode.py:2136-2137` | **NOT zero trainer data.** Extend this, don't start from nothing |
| Obstacle discovery | `modules/story/obstacle_clearing.py` — generic, ROM-derived. ROM counts in its own header: Strength 59 / RockSmash 44 / Cut 33 objects | **Only Rock Smash acts.** Cut = *"mechanism matches, never validated live — needs one probe"*; Strength = *"a boulder is PUSHED, not removed"* |
| Encounter index | `modules/encounter_index.py` + `cache/encounter_index_BPEE0.json` — species → [{map, method, rate%, min/max level}] | **The proven precedent** for any new dataset: versioned, ROM-keyed, corrupt-tolerant |
| Poké Centers | `modules/modes/util/map.py:7` (48 RSE map keys), `modules/map_data.py:1524 PokemonCenter` (15 RSE door tiles) | ~9% of maps; outside that set `find_closest_pokemon_center` raises |
| Fly | `modules/region_map.py:38-54 FlyDestinationRSE` — **17** members (incl. PacifidlogTown); `modules/modes/util/higher_level_actions.py:243 fly_to` | **ZERO `fly` references in `global_navigation.py`.** The planner is blind to the cheapest long-haul edge in the game |

### The honest gap list
1. ⭐ **CHAPTER → MAP: NOTHING.** 30 chapters exist (`modules/story/chapters.py`), each with **one** milestone flag and an `area: str` that is **prose**. Repo-wide grep for `MAPS_BY_CHAPTER|CHAPTER_MAPS|chapter_maps|maps_for_chapter` returns **nothing**. VERIFIED.
2. **The gate table is 3 edges over ~1400 (~2510 with Fly).** `git log` shows it was born with 2 entries on 2026-07-25, grew by **exactly one** on 2026-07-26, and has been **byte-frozen for 7.7 weeks**. VERIFIED.
3. **No persisted tile/collision dataset of any kind.** Every traversability read goes through a running emulator; the only caching is a process-global dict.
4. **No Fly / dive-emerge / hole-fall edges** in either graph (`warp_graph.py:341-342`: *"Dive/Emerge need HM08 — excluded on purpose"*).
5. **No item-location index.** Readers exist (`modules/map.py:660 kind`, `:700 hidden_item`, `:705 hidden_item_flag_id`); the only consumer anywhere is the debug GUI (`modules/gui/debug_tabs.py:1395-1397`).
6. **No trainer-party reader.** `grep gTrainers|gTrainerParties|TrainerParty|get_trainer` over `modules/` = **0 hits**. Rematch data: none.
7. **Route knowledge is imperative, not queryable.** 628 `MapRSE.*` references over 136 distinct maps in `modules/story/`; `early_game.py` is 9,336 lines. A future AI pilot cannot read it.
8. ⚠ **Both persisted caches are gitignored, and a TRACKED tool reads both** — `tools/story-dev/rare_species_dataset.py:61-62` opens `warp_graph_BPEE0.json` and `encounter_index_BPEE0.json` directly ⇒ **it cannot run from a clean clone.**

### Two correctness ceilings that bound everything
- ⛔ **KI-74 — `setmetatile` is invisible to ROM readers.** **873 call sites across 46 script files** (corrected; the 874th occurrence is the macro definition at `asm/macros/event.inc:1345`). Concentrations: `abnormal_weather.inc` 224, `Route110_TrickHousePuzzle3` 156, `NewMauville_Inside` 83, `elite_four.inc` 42, `SootopolisCity` 34, and ~13 further non-Frontier files the source list omitted. **It fails in BOTH directions**, and the dangerous one is ROM-says-open / live-says-sealed (measured at the E4 entry door 2026-09-16) — *nothing reports it as impossible; the bot just jams at a threshold.* Plus `setmaplayoutindex`: **18 sites over 14 maps** (corrected from 13).
- ⛔ **KI-24 — `calculate_path` reads the dual-elevation bridges on Routes 118/119/120 as WALLS**, and fails even a same-map walk inside Route 119 (y=5 → y=135). Those are among the best mid-game training maps.

---

## 4. A PER-CHAPTER REACHABILITY MODEL

### ⛔ The one design decision that determines whether it is useful or quietly wrong
**A per-map BOOLEAN is WRONG.** Proven in-tree: Victory Road B1F's passable-tile count is **23 / 66 / 23 / 298** for {neither, Strength only, Rock Smash only, both} — same map, four answers, and **only the fourth reaches the B2F warp**. VERIFIED, quoted verbatim at `sandbox-pokebot/modules/story/chapters.py:271-273`.

### The algorithm — a two-tier FIXED POINT (INFERRED design; inputs VERIFIED below)
```
TIER A — world graph, 518 map nodes. Edge kinds:
  e1 connections   134 cardinal (L40/R40/U27/D27), bidirectional, ungated by data
  e2 warps         1268 resolvable + 45 dynamic(127), DIRECTED, warp tile -> arrival tile
  e3 hole falls    6 (setholewarp), DIRECTED, arrival = SAME local (x,y), COMPUTED AT RUNTIME
  e4 dive/emerge   7 + 7, gated BADGE07 + party Dive
  e5 Fly           68 source maps x 16 destinations = 1088, gated BADGE06 + Fly + FLAG_VISITED_<sec>
TIER B — tile grid, flooded PER REGION (not per map: the 49-map mainland shares one
  coordinate frame), from an ENTRY-TILE SET, elevation carried as STATE.
  Output: reachable mask + which exits that fill actually TOUCHES.
COUPLING (why one pass is wrong):
  frontier = {(spawn_map, spawn_tile)}
  repeat: flood each unsettled (map, entry_set) -> exits_touched
          promote exits_touched to live Tier-A edges (each with its far-side arrival tile)
          BFS Tier A -> may deliver NEW entry tiles to already-filled maps -> re-fill those
  until no new (map, arrival-tile) pair appears.   [terminates: finite pair space]
```

### Inputs
| Input | Source | Marker |
|---|---|---|
| Collision rule | `GetCollisionAtCoords`, `src/event_object_movement.c:4658-4672` — **SEVEN** branches, not six. The one commonly missed is `else if (objectEvent->trackedByCamera && !CanCameraMoveInDirection(direction)) return COLLISION_IMPASSABLE;` — **player-specific**, so a flood fill must not drop it. | VERIFIED |
| Elevation | `include/global.fieldmap.h:14-21` (TRANSITION 0, SURF 1, DEFAULT 3, MULTI_LEVEL 15); `IsElevationMismatchAt` `:7707-7723`. **Our `map_path.py:855-859` already matches condition-for-condition — reuse, do not rewrite.** Whether ours models the `trackedByCamera` term: **NOT CHECKED** | VERIFIED |
| Badge→HM | `src/party_menu.c:120-127` + `:3725` `FlagGet(FLAG_BADGE01_GET + fieldMove)` ⇒ Cut 01, Flash 02, RockSmash 03, Strength 04, Surf 05, Fly 06, Dive 07, Waterfall 08. ⚠ **NECESSARY, not SUFFICIENT** — Fly also needs `Overworld_MapTypeAllowsTeleportAndFly`, Surf also needs `IsPlayerFacingSurfableFishableWater` | VERIFIED |
| Flash | **NOT a movement gate.** Exactly 7 maps set `requires_flash`; it feeds `SetDefaultFlashLevel` — a vision *radius* | VERIFIED |
| Per-chapter capability vector | **MUST BE MEASURED, not synthesised.** `chapters.py` carries one flag per chapter; reachability depends on 481 distinct hide flags + several state vars. The project already owns **167 save fixtures** in `tools/story-dev/saves/`, and **all 22 named boundary fixtures exist** (gym1_done … post_wallace). Precedent: `probe_chapter_order.py` **corrected** a chapter order the design doc called "confirmed" | VERIFIED |

### ⭐ THE BIGGEST SINGLE FINDING, and it reshapes the model
**EVERY cut tree, smashable rock and strength boulder in Emerald uses a `FLAG_TEMP_*` hide flag and RESPAWNS on every map entry.** Census over all 518 `data/maps/*/map.json`, **independently reproduced exactly**: CUT 33/33 temp · SMASH 44/**42** temp · STRENGTH 59/59 temp. The only two persistent are `MAP_RUSTURF_TUNNEL` (24,5) and (24,4). `ClearTempFieldEventData()` memsets the temp block **and** `FlagClear(FLAG_SYS_USE_STRENGTH)`, and is called from **both** map-load paths. VERIFIED `src/event_data.c:39-48`, `src/overworld.c:798` (camera transition) and `:848` (warp).

⇒ **HM obstacles are a per-TRAVERSAL capability requirement, NOT a chapter unlock.** "Chapter 15 cleared the Route 116 trees" is FALSE. Budget the interaction on every pass, and re-activate Strength on every map entry. *Good news:* no per-chapter obstacle state to track, and boulder puzzles are deterministic from the template every visit.

### Traps — corrected inventory
| Trap | True size | Static-readable? |
|---|---|---|
| `setmetatile` | **873 sites / 46 files**; `abnormal_weather.inc` stamps a **cave entrance onto Routes 113/114/115/116/118** (`:22 setmetatile 59, 12, METATILE_General_CaveEntrance_Top, TRUE`) | **NO** |
| `setmaplayoutindex` | **18 sites / 14 maps** (SkyPillar 1F-Top, ShoalCave ×4, Route111/130/131, Sootopolis ×2, Birch's Lab ×2) | **NO** |
| Hole falls | **6** `setholewarp` sites, **all bare `setholewarp MAP_x` with no coordinates** — the landing is the falling player's own (x,y) at runtime. Chain: `setholewarp` → `SetFixedHoleWarp` (`src/overworld.c:705-708`) → `sFixedHoleWarp` → `SetWarpDestinationToFixedHoleWarp` (`:710-716`), reached when `warphole` runs with `MAP_UNDEFINED` | rule only, not the 6 tiles |
| Invisible intra-map teleports | **2**, not 5: `MB_MOSSDEEP_GYM_WARP`, `MB_LAVARIDGE_GYM_B1F_WARP`. (`MB_SHOAL_CAVE_ENTRANCE` is an **arrow warp** resolving through the normal table; `MB_MT_PYRE_HOLE`/`MB_CRACKED_FLOOR_HOLE` are the hole triggers already counted; `MB_BATTLE_PYRAMID_WARP` is out of scope) | **NO** |
| Rotating gates | **2 C arrays**: Fortree **8** gates (`src/rotating_gate.c:191-201`), Trick House **11** (`:204-217`). `ROTATING_GATE_PUZZLE_MAX 12` is a sprite-slot ceiling | **NO** |
| Cracked floors | degrade with steps (`src/field_tasks.c:801-835`, delay 3, 2 pending) ⇒ Sky Pillar reachability is a function of the PATH TAKEN | **NO** |
| Fly sources | the **4 map types** accepted by `Overworld_MapTypeAllowsTeleportAndFly` (`src/overworld.c:1366-1375`): ROUTE 41 + TOWN 7 + CITY 9 + OCEAN_ROUTE 11 = **68 maps**. ⛔ **NOT "any outdoor map"** — 105 UNDERGROUND and 14 UNDERWATER maps cannot Fly. A bot believing it can Fly out of Victory Road or Seafloor Cavern **strands itself** | yes |
| Fly destinations | 16 mapsecs, gated `FLAG_VISITED_*` (set by *visiting*) ⇒ **history-dependent, not chapter-dependent**. `src/data/heal_locations.json` has **22** entries; LITTLEROOT and EVER_GRANDE are **one-to-many** ⇒ mapsec→landing tile is not 1:1 | yes |
| Dynamic warps | 45 with destination 127 — already excluded by both our graphs | n/a |
| Object templates | 2776 objects, 1140 flagged over 481 flags; NPCs wander. `calculate_path` compensates live via `get_map_objects()`; **an offline artifact cannot** | partial |

### Artifact shape (INFERRED; sizes from VERIFIED counts: 441 layouts, 324,579 tiles, median layout 216 tiles)
| File | Kind | Size | Why |
|---|---|---|---|
| `cache/world_static_<ROMID>.bin` | generated, gitignored | ~650 KB raw (2 B/tile), far less gzipped | re-derivable in seconds; would only rot in git |
| `cache/world_graph_<ROMID>.json` | generated, gitignored | ~2,510 edges | same |
| ⭐ `PROJECT KNOWLEDGE/data/chapter_reach.json` | **committed** | ~50-150 KB | 30 rows: the capability vector it was computed under, the 518-bit reachable-map mask (65 B) + hop distance, and **for every REFUSED edge, the gate that refused it**. This is what a future AI pilot actually reads |
| ⭐ `PROJECT KNOWLEDGE/data/world_overlays.json` | **committed, hand-curated, live-verified** | <100 KB | the traps no static reader can see, each row carrying `decomp:<file>:<line>` or `probe:<name>@<fixture>` provenance |
| `PROJECT KNOWLEDGE/data/gate_table.json` | **committed** | small | successor to `KNOWN_GATES`'s 3 rows; the artifact that most needs human review |
| per-chapter tile bitmask | optional, regenerate | 40.6 KB/chapter | ~90% identical between adjacent chapters |

**Acceptance (non-negotiable):** per fixture, computed set **vs** live `region_reach.reachable_maps()` on that same save — every disagreement is a bug in one of the two. **PLUS a mandatory VACUITY ARM: recompute with Surf removed and assert the set SHRINKS.** A fill that returns the same answer with and without a capability is measuring nothing.

---

## 5. ITEMS WORTH A DETOUR

**Corpus (independently reproduced):** 162 real visible item balls + 112 hidden items = **274 items over 97 maps**, sell total **$467,850** (sell = `GetItemPrice/2`, `src/item_menu.c:2170`). VERIFIED.

### The shortlist, by payoff-per-effort
| # | Item | Where / gate | Value | Marker |
|---|---|---|---|---|
| **1** | ⭐ **AMULET COIN** | **Mom, Littleroot**, gated `FLAG_BADGE05_GET` — *the same Norman gate as rematches*. Needs **TWO separate talks** (`TryRegisterMom` ends `setflag FLAG_ENABLE_MOM_MATCH_CALL / release / end` — it does **not** fall through), and is blocked while `VAR_LITTLEROOT_HOUSES_STATE_MAY`/`_BRENDAN == 4` | **+100% of every trainer payout, forever.** On a L50 LEADER rematch that is **+$5,000** — *equal to* the single richest item ball in the game (a Nugget), on the first rematch, and repeating. ⛔ `moneyMultiplier = 2` is set **on SWITCH-IN of the holder** (`src/battle_util.c:3291-3297`) ⇒ must be on a mon that enters battle | VERIFIED |
| **2** | **EXP SHARE** | Mr. Stone, **Devon Corp 3F**, gated `FLAG_DELIVERED_STEVEN_LETTER` — *our bot already passes that gate and never goes back* (`early_game.py:3389` reads it) | Biggest single lever on "level-appropriate" training | VERIFIED |
| **3** | **MACHO BRACE** | Victoria, Route 111 Winstrate house — **UNGATED** (zero `trainerbattle` in the whole 101-line script; all 4 objects `TRAINER_TYPE_NONE`) | free EV rate | VERIFIED |
| **4** | **RARE CANDY ×16** (8 balls + 8 hidden) | Granite Cave B2F, Route110/114/119/127/132, Shoal Cave, Magma Hideout; hidden on Petalburg, Route108/111/120(×2)/123, Mt Pyre Summit, Safari NE | 16 free levels — **and the consumer already exists**: `apply_rare_candy` at `modules/modes/util/items.py:284` | VERIFIED |
| **5** | **NUGGET ×10** | balls @ Route112(14,43) Route119(19,5) Route120(20,55) AquaHideout_B1F(15,10) MagmaHideout_3F_1R(9,16) SafariNE(8,17); hidden @ Fallarbor(2,15) Route113(73,3) Route121(58,3) TrickHouseEnd(4,5) | **$50,000**. One (Aqua Hideout) is *already collected by our code* | VERIFIED |
| **6** | **10 TMs at $1,500 sell** | Earthquake, Ice Beam, Shadow Ball, Toxic, Solar Beam, Dragon Claw, Iron Tail, Focus Punch, Hail, Skill Swap | 15 TMs total (14 balls + 1 hidden) = $20,000 | VERIFIED |
| **7** | **Richest single maps** | Route 119 **$24,600** (9 balls + 4 hidden — *and it is on the critical path to Fortree*) · Artisan Cave B1F $24,500 (post-game vitamin vault) · Route 121 $22,750 · Route 123 $22,200 · Underwater Route 124 $14,450 (7 hidden, 0 balls) | 4 underwater maps hold 21 hidden items / $41,200 / zero balls | VERIFIED |
| **8** | **LEFTOVERS** | exactly ONE overworld instance in the game, **HIDDEN** @ SS Tidal Lower Deck (0,2) | | VERIFIED |
| **—** | ⛔ **LUCKY EGG** | present in `items.h`, hold effect exists, **but its only source is wild Chansey's rare held item and Chansey has ZERO wild encounters in Emerald** | **Do not put it in the ledger** | VERIFIED |

### Composition (recomputed independently — matters for the sell-vs-consume ruling)
| Class | items | sell $ |
|---|---|---|
| Vitamins + PP Up/Max | 45 | **220,500** |
| Sell-junk (Nugget, Pearls, Stardust, Star Piece, Mushrooms, Heart Scale, Shoal, Shards) | 54 | **104,050** |
| TMs | 15 | 20,000 |
| Everything else | 160 | 123,300 |

**⇒ ~47% of the headline is vitamins, which the user's "level-appropriate training" ruling arguably wants CONSUMED.** The ledger should surface the choice, not pre-decide it.

### Mechanics the harvester must respect
- **Hidden items need NO Itemfinder and are NOT underfoot.** Both kinds use the identical motion: stand on an adjacent walkable tile, **face the item tile**, press A. Interaction resolves against the tile *in front* (`src/field_control_avatar.c:170-172`); the hidden-item branch is a bare `FlagGet` with no bag/item check (`:348-353`). ⇒ **one routine harvests all 274.** VERIFIED.
- ⛔ **60 of the 222 `OBJ_EVENT_GFX_ITEM_BALL` objects are NOT items** (48 Battle Pyramid placeholders, 5 Voltorb/Electrode, 3 Birch starters, 2 rival bedroom, 1 Steven's Beldum, 1 Contest Hall script `0x0`). **A ball is an item only if a `finditem` stub in `data/scripts/item_ball_scripts.inc` backs it.** VERIFIED.
- ⚠ **LATENT BUG, ours AND upstream AND `custom-pokebot/`:** `hidden_item_flag_id` returns the **raw 16-bit index**, and `to_dict` feeds it to `get_event_flag_name`, whose table is keyed by **absolute** flags starting at 500. **RE-CONFIRMED IN-SESSION** at `sandbox-pokebot/modules/map.py:705` and `:728` (index 0 returns an **empty string**). Fix = `+ FLAG_HIDDEN_ITEMS_START (0x1F4)` for Emerald. **FRLG/RS base NOT CHECKED — do not apply blind.**
- ⛔ **Grade a pickup ON THE BAG, never on the flag.** `finditem` branches to `Common_EventScript_ShowBagIsFull`, which gives **no item AND sets no flag** — a flag-based success test hangs for its whole bound. This is already the documented contract of `collect_item_ball` (`early_game.py:8470-8479`).

---

## 6. SCOPE — BLUNTLY

**Framing the user should hold onto: the bot cannot yet beat the Elite Four.** Nearly everything in sections 1-2 is post-Hall-of-Fame or post-Norman economy. The map work in sections 3-4 is foundation for the v2 AI pilot — real value, but it is *weeks*, and it does not move the current bot one chapter forward.

### TIER A — do now. Cheap, on paths the bot already walks, zero new infrastructure.
| Item | Size | Why first |
|---|---|---|
| **A1 Amulet Coin errand** (2 talks in Littleroot, post-Norman) | ~half a day | Highest $/effort in this entire note. Doubles every trainer payout from then on |
| **A2 EXP Share errand** (revisit Devon 3F) | ~half a day | Biggest lever on level-appropriate training; the gate is already passed |
| **A3 Macho Brace** (Route 111 Winstrate house, ungated) | small | free |
| **A4 The `+500` hidden-item flag fix** (one line × 3 trees) | minutes | Do it **before** anything reads that field, or a harvester will re-walk taken items forever |
| **A5 Promote `ledger.json` + `parse.py`** into a committed generated dataset next to `modules/data` | ~1 hour | The 78-row ledger is DONE and dual-oracle-verified; it lives in session-temp and will be lost |

### TIER B — do once the E4 is beatable / once money is the bottleneck
- **B1 The E4 gauntlet loop.** **$32,400 + 51,157 exp per lap, RNG-free, no PokéNav, no rematch system, no new map data.** Almost certainly the bot's highest-throughput income. ⚠ Wall-clock per lap at x1 with human-looking input is **UNKNOWN** — the money/hour comparison against Route 104 cannot be made without it.
- **B2 Rematch state read** — one `get_save_block(1, 0x9CA, 100)` + a row enum mirroring `rematches.h`. ~half a day including the live probe.
- **B3 "Fight ONE armed rematch"** for one hand-verified trainer. **Pick Cindy or Winston** (Route 104, $7,200 for a single L36 Linoone — money-densest AND level-appropriate mid-game). Proves the loop end-to-end. It is 95% navigation, not mechanics.

### TIER C — foundation. Weeks. Do NOT start before the E4.
- **C1 Generalise the live-grid reader** out of `early_game._live_passable` / `sootopolis` into a map-agnostic module API with a loaded-map guard. ⚠ **This is NOT a greenfield day** — a battle-tested reader already ships in three modules and is already promoted.
- **C2 Measured per-chapter capability vectors** from the 22 boundary fixtures, headless, zero frames advanced. ~half a day, and **useful on its own** even if nothing else is built.
- **C3 THE GATE TABLE — irreducible, and the real cost.** 3 rows today over ~1400 edges (~2510 with Fly), frozen for 7.7 weeks. Days-to-weeks of judgement-heavy audit; a wrong row sends the bot across Hoenn. **Fan this out across agents; it is exactly the shape that worked for KI-58.**
- **C4 The Tier-A⟷Tier-B fixed point** + acceptance vs live `region_reach` + the vacuity arm. 3-5 days against code that mostly exists.
- **C5 The overlay** — 14 layout-swap maps, ~46 `setmetatile` files, 6 holes, 2 teleport behaviours, 2 gate arrays. **Probe-per-map; cannot be automated, because a ROM read can never observe a RAM write.**
- **C6 The 65-row approach-tile corpus** (map → row → approach tile → facing), built ONCE as DATA, never as 65 routines. It is the same corpus the item harvester needs. **Build it once; share it.**

### ⛔ NOT WORTH DOING
- **Driving the PokéNav to arm rematches.** Renderer-gated (video off ⇒ ~150 A-presses = zero progress, measured), requires scrolling a ~70-row list to a specific index, renderer on, at x1, **once per arming**. The walking and battle-count paths cost zero UI.
- **Calling gym leaders.** Can never arm; the only signal is a bit readable from RAM for free.
- **Treating rows 73-77 as rematch content.** They are a 5-room gauntlet re-run, a different module.
- **Farming gym leaders for money before the New Mauville errand** (7 rematches total, ever) — and even after, budget ~65 trainer battles per arming.
- **Building the deterministic phone hash into architecture.** It is a real mechanism, but per this project's own measured rule: *grade names highly, architecture advice not at all.* Use it to know **what to look for**, never to decide what the bot does.
- **Letting the item harvester grow its own reachability model.**
- **A third world graph.** Consolidate `warp_graph` + `region_reach`, or extend one. They are byte-identical sandbox↔custom, so this is a production decision.
- **DEFER ENTIRELY:** Battle Frontier, Trick House (8 puzzle maps, 156 `setmetatile` in Puzzle3 alone), Safari Zone, Secret Bases, abnormal-weather TerraCave/MarineCave, the 45 dynamic warps. **Excluding them removes most of the trap surface and none of the story.**

---

## 7. REFUTED / WITHDRAWN

Every claim the adversarial passes killed. **Do not copy these forward.**

| # | Claim killed | Corrected value |
|---|---|---|
| R1 | Gym-leader rematch rolls fire "at the START of essentially every wild or trainer battle" | **The functions are modulo-gated**: `% 60` wild, `% 20` trainer (`src/battle_setup.c:956-966`). Real rate ≈ **1 arming per 65 trainer battles / 194 wild battles** — off by 20-60× |
| R2 | "Gym leaders advance in LOCKSTEP — you cannot grind one ahead of the others; this kills 'farm Juan'" | **Lockstep binds only over currently-UNARMED leaders** (both loops guarded by `if (!trainerRematches[data[i]])`). Arm all 8, beat only Juan, and Juan climbs alone. **"Farm Juan" is NOT dead.** The real limit is R1 |
| R3 | "All 65 ordinary+Wally rows: $107,432 / 208,268 exp" | **$110,852 / 218,341 / 168 mons.** The stated figures are rows 0-63 — **Wally omitted from a total labelled "ordinary+Wally"** |
| R4 | Incoming Match Call chance is "1-in-3 (2-in-3 with Lightning Rod)" | `Random() % 10 < callChance * 3` ⇒ **30.0% / 60.0%** (`src/match_call.c:1055-1065`). The 1/3 figure was read off the decomp's English *comment*, not its code. The conjunction also omits the final gate at `:1108-1110` |
| R5 | "Registration is recoverable — every map script has a TryRegister re-talk path" | **FALSE as a universal.** `grep -c TryRegister`: Route104=12, Route116=8, PetalburgWoods=4, but **Route117=0, MtPyre_3F=0, Route124=0**. Also the mechanism is wrong: `SetMatchCallRegisteredFlag` is **not** gated on `FLAG_HAS_MATCH_CALL`. The correct scope is the pre-Rustboro set only |
| R6 | "EXP totals are independent of how many participants split them" | **False by integer truncation** — division by `viaSentIn` happens *before* the ×1.5. Published figures are exact for 1 participant, **~1-2% optimistic** otherwise |
| R7 | "The Hall of Fame re-arms the E4" (as the sole mechanism) | **A WHITEOUT also does** (`data/event_scripts.s:585-588`). ⇒ never treat `FLAG_DEFEATED_ELITE_4_*` as evidence the bot beat the league |
| R8 | "One E4 lap ≈ 4.5 Cindy+Winston pairs" | **2.25 pairs** ($32,400 / $14,400) |
| R9 | "Gym-leader rematches are cheap to add — 8 rows, 8 city maps, already on story routes" | Leaders are in **gym interiors**; the row's map field names the **CITY**. And **Norman's permanent position is a function of rematch state** — armed ⇒ he stays at the BACK (`PetalburgCity_Gym/scripts.inc:52-58`). A static map→approach-tile table is wrong for at least one leader |
| R10 | "Only gym-leader rematches are double battles" | **Plus 5 ordinary rows**: Lila&Roy, Anna&Meg, John&Jay, Kira&Dan, Amy&Liv. The ledger needs an `is_double` column |
| R11 | "Wally is gated on `FLAG_DEFEATED_WALLY_VICTORY_ROAD`" | That flag is set by the **ENTRANCE** battle (pre-HoF). The **binding** condition is `FLAG_REGISTERED_WALLY`, set only by the post-HoF **exit** battle vs `TRAINER_WALLY_VR_2` |
| R12 | "OUR FORK HAS ZERO HARVEST LOGIC / a ~40-line `collect_overworld_item(map,x,y,flag)` is the build" | ⛔ **`collect_item_ball` ships at `early_game.py:8464` with 5 production call sites** (RE-CONFIRMED IN-SESSION) and already collects a Nugget and a TM. The proposed design (`press A; confirm flag flipped`, signature without approach+facing) is **exactly the bug its docstring says it was written to avoid** |
| R13 | "No `gBackupMapLayout` reader in `modules/` — STEP 0 is lifting it out of a probe, a mandatory day one" | ⛔ **Four readers ship in `modules/story/`**, already promoted to `custom-pokebot/` (RE-CONFIRMED IN-SESSION). Only `modules/map.py` lacks one. The task is *generalise*, not *build* |
| R14 | "ZERO trainer data anywhere in the fork / rematch ledger = 0%" | **`badge_case.py:126-143`** is an 8-row decomp-verified leader table with `ace_level` and TM reward, consumed live. What is truly absent is narrower: `_2`..`_5` parties, money, XP, and every non-leader trainer |
| R15 | "~22 `TRAINING_GRASS` rows" | **10 actionable** + 12 behaviour-neutral `PENDING_GRASS` (RE-CONFIRMED IN-SESSION). Coverage is 1.9% of maps, not 4.2% |
| R16 | "`KNOWN_GATES` has grown by 2 entries in ~8 weeks" | **It grew by exactly ONE, on 2026-07-26, and has been frozen 7.7 weeks.** The "~2 per 8 weeks" rate came from quoting a punch-list line the punch list itself flags as stale |
| R17 | "`ScrCmd_setholewarp` at `src/scrcmd.c:785-794` calls `SetWarpDestination` then `DoFallWarp`" | **Wrong function.** `setholewarp` is at `:864-873` and calls `SetFixedHoleWarp`. The quoted body belongs to `ScrCmd_warphole`. Conclusion survives via a 3-hop chain the note never traced |
| R18 | "`GetCollisionAtCoords` at `:4663-4677`, SIX checks" | `:4658-4672`, **SEVEN** — the missing one is `trackedByCamera && !CanCameraMoveInDirection`, a **player-only** rule, in the very finding that says "build byte-identical to this" |
| R19 | "`setmetatile`: 874 sites / 47 files" · "`setmaplayoutindex`: 13 maps" · "5 teleport behaviours" · "Fortree = 12 gates" | **873 / 46** (the extra was the macro definition) · **14 maps** (its own list enumerated 14) · **2 behaviours** · **Fortree 8, plus an unmentioned Trick House array of 11** |
| R20 | "Fly: any OUTDOOR map → 16 destinations; graph ≈ 1430 edges" | **68 source maps** of type ROUTE/TOWN/CITY/OCEAN_ROUTE. **105 UNDERGROUND + 14 UNDERWATER maps cannot Fly.** Fly alone is **1088 edges**; the graph is **~2510** |
| R21 | "16 RSE Fly destinations, Littleroot..EverGrande" | **17** — the `..` range silently truncated **PacifidlogTown**, the one that matters most for the water routes |
| R22 | "`warp_graph_BPEE0.json` is committed" / "the only persisted map artifact" | **Both caches are gitignored**, and a **tracked** tool (`tools/story-dev/rare_species_dataset.py:61-62`) reads both ⇒ it cannot run from a clean clone |
| R23 | "`calculate_path` refuses cross-MAP requests" (the inherited brief) | It refuses **cross-REGION**. 461 regions; the largest is **49 maps** and one call crosses the whole mainland |
| R24 | "The Amulet Coin earns MORE THAN the richest overworld item on its first rematch" | Its **marginal** contribution on the cited L50 LEADER example is **$5,000 — exactly equal** to a Nugget. It exceeds one only above L50, which was never established |
| R25 | "~$180k is unambiguously sellable junk+Nuggets; ~$230k is vitamins" | **No partition yields either.** Junk+Nuggets = **$104,050** (54 items); vitamins+PP = **$220,500** (45 items). The $230k figure only reaches that size by folding in 4 Star Pieces |
| R26 | "a ladder of 5 STATIC parties per row" (inherited brief) | 5 **SLOTS**, not 5 distinct parties. Wally duplicates slot 4; the five E4/Wallace rows repeat ONE id five times; Cindy and Amy&Liv each skip a tier |
| R27 | "162 balls parsed from all **519** `map.json`" | **518** |
| R28 | Minor citation drift, ~25 instances, ±1-2 lines each, no fabrication found in any angle | Re-open before pasting any line number forward |

---

## 8. STILL UNKNOWN — and the cheapest experiment for each

| # | Unknown | Cheapest experiment |
|---|---|---|
| U1 | **`SaveBlock1 +0x9CA trainerRematches[100]` on our BPEE0.** Decomp-corroborated, never probed | One observe-only read of 100 bytes: expect **all-zero before 5 badges**, non-zero after a known arming. Half an hour |
| U2 | **The deterministic phone-arming hash** `((dayCount ^ dewfordRand) + (dewfordRand ^ trainerBattles)) ^ otId` | Compute the predicted trainer from RAM, call from a **different mapsec**, assert `trainerRematches[that row]` goes 0→non-zero **while a CONTROL row stays 0**. Do this before believing any plan built on it |
| U3 | **Wall-clock of one E4 lap at x1 with human-looking input** | Time one lap. Without it the "E4 gauntlet vs Route 104" money/hour comparison **cannot be made** — and it is the decision that ranks Tier B |
| U4 | **Can our pathfinder reach each rematch NPC?** ~30 maps; Mt Pyre 3F/6F, Abandoned Ship, Meteor Falls 1F_2R and Jagged Pass are the suspicious ones | Per map: `calculate_path` from a **real captured position** to the approach tile, **plus a control tile that DOES path**. Batch it over the 22 fixtures |
| U5 | **Where each rematchable NPC actually stands** (44 maps × `object_events`) — the blocker for turning the ledger into a route | One offline sweep of `data/maps/<Map>/map.json` `object_events` joined on the script labels already cited. ⚠ Must carry a **state-dependent** approach tile (Norman at minimum) |
| U6 | **Are the 112 hidden-item tiles reachable?** Interaction is face-and-A on the tile *in front*, so a harvester that paths **onto** the tile can never trigger it | Per coordinate: path to each of the 4 neighbours; assert ≥1 standable + a control. On cave/indoor maps check against the **live** `gBackupMapLayout`, not ROM (KI-74) |
| U7 | **Is `FLAG_HIDDEN_ITEMS_START` also `0x1F4` on FRLG and RS?** Only Emerald verified | Read the constant per ROM before applying the `+500` fix anywhere but Emerald |
| U8 | **Does `map_path` model the `trackedByCamera && !CanCameraMoveInDirection` collision term?** | Read `map_path.py`'s collision path once. 10 minutes; it is a player-only impassability rule the flood fill must not drop |
| U9 | **Which item-bearing maps are gated by which HM?** Only `requires_flash` (7 maps, 4 with items) was derived | Falls out of C3/C4 for free. Do **not** derive it separately |
| U10 | **Does our story bot ever talk to Mom after receiving the PokéNav?** If not, the Amulet Coin is unreachable even post-Norman without an explicit errand | `grep -ri "amulet\|players_house\|MOM_MATCH_CALL" modules/story/` — already known to return **nothing**, so: assume an errand is required |
| U11 | **Is the PokéNews buy-price halving worth modelling?** `sShopData->totalCost = (GetItemPrice(itemId) >> IsPokeNewsActive(POKENEWS_SLATEPORT))` — a verified 50% off | Trace what activates PokéNews and how long it lasts. Low priority; a shopping-timing optimisation only |
| U12 | **Do gym-leader rematch NPCs stand in their gyms at all times post-HoF, or only while armed?** Only the script branch was verified, not NPC presence/visibility flags | Read an armed leader's live object position **before** assuming any destination tile |
| U13 | **USER RULING NEEDED, not research:** sell the vitamins ($220,500) or consume them for EVs? | Swings the item headline by ~47%. The stated priorities point both ways (money high priority; training must be level-appropriate) |
| U14 | **USER RULING NEEDED:** does `chapter_reach.json` model the *optimal-play* Fly-visited set, the *fixture's actual* set, or both? Fly is history-dependent, so two saves at the same chapter differ | — |
| U15 | **The 92 non-reciprocal warps** were found with a crude index test whose own first hit (`AquaHideout_B2F→B1F`) is a multi-tile-door artifact | A dedicated pass separating real one-way edges (SeafloorCavern Room4/Room6→Entrance) from door artifacts |

---

**⛔ FINAL REMINDER.** This is a NOTE. Nothing here is truth until it reproduces in our own harness. The three highest-value items in it — the Amulet Coin errand, the E4 gauntlet loop, and the 78-row ledger — are also the three that need the least new infrastructure. The chapter-map is the most valuable *foundation* and the most expensive *build*, and its cost is concentrated in one place: **the gate table.**
