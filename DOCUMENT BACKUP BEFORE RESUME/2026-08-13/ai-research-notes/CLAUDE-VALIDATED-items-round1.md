# CLAUDE-VALIDATED — Item Locations Round 1

**Status: the only file in this directory whose claims were checked against an external
ground truth** (the real `pret/pokeemerald` decomp, fetched live via `gh api`, and read
line-by-line — not recalled). Produced per the process correction in
`00-READ-THIS-FIRST.md`: Gemini fans out → Gemini critiques → **this Claude pass is the
final word**.

Every ruling below cites a file I actually fetched and read this session. Where I could not
fetch and read a source, the claim is marked UNRESOLVED rather than guessed at.

**Important meta-finding: the Gemini critique pass (`VERIFY1-*.md`) is not reliable either.**
Two of the nine claims below (HM07 Waterfall's true location, and the Route 134 "no hidden
items" claim) show the critique itself was wrong even while correctly identifying that the
*original* note was wrong. Treat `VERIFY1-*` and `ADJUDICATED-*` as leads on what to check,
never as the answer — this file demonstrates why.

---

## 1. RULINGS

| # | Claim | Verdict | The actual truth | Exact source read |
|---|---|---|---|---|
| 1 | `ITEM_REVIVE` hidden in `MAP_MOSSDEEP_CITY_STEVENS_HOUSE`, flag `FLAG_HIDDEN_ITEM_STEVENS_HOUSE_REVIVE` | **REFUTED** | No hidden item exists in Steven's House at all. The only item-granting script in the map is `MossdeepCity_StevensHouse_EventScript_StevenGivesDive`, which Steven gives you directly (`giveitem ITEM_HM_DIVE`) once `VAR_STEVENS_HOUSE_STATE` reaches the right stage. There is also an unused leftover script `MossdeepCity_StevensHouse_EventScript_DiveItemBall` (commented `@ Unused, leftover from RS`) that calls `finditem ITEM_HM_DIVE` — this is dead code from Ruby/Sapphire, never wired to any map object, and is almost certainly what the original note's author confused for a "hidden item." The flag `FLAG_HIDDEN_ITEM_STEVENS_HOUSE_REVIVE` does not appear anywhere in the file. | `data/maps/MossdeepCity_StevensHouse/scripts.inc` (full file fetched via `gh api repos/pret/pokeemerald/contents/data/maps/MossdeepCity_StevensHouse/scripts.inc`) |
| 2 | HM07 (Waterfall) is an item ball in `MAP_CAVE_OF_ORIGIN_B1F` *(note)* — critique said instead it's an item ball in the final room of Marine Cave (`MarineCave_End`) | **REFUTED both versions** | HM07 Waterfall is **not an item ball anywhere**. It is a story gift from **Wallace in Sootopolis City**, given via `SootopolisCity_EventScript_GiveWaterfall` (`giveitem ITEM_HM_WATERFALL`), gated behind `goto_if_set FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE`. Confirmed absence at both wrong locations: `data/maps/CaveOfOrigin_B1F/map.json` has zero `ITEM_`/`hidden_item` references at all; `data/maps/MarineCave_End/scripts.inc` contains only the Kyogre legendary-battle script, no item grant. | `data/maps/SootopolisCity/scripts.inc` line ~1275-1287 (`SootopolisCity_EventScript_Wallace` → `SootopolisCity_EventScript_GiveWaterfall`); `data/maps/CaveOfOrigin_B1F/map.json` (fetched, grepped for `ITEM_`/`hidden_item`, zero matches); `data/maps/MarineCave_End/scripts.inc` (fetched in full) |
| 3 | Mach/Acro Bike prerequisite is "defeat Wattson" (`FLAG_DEFEATED_MAUVILLE_GYM`) | **REFUTED** | There is no prerequisite. Rydel's script (`MauvilleCity_BikeShop_EventScript_Rydel`) checks only `FLAG_RECEIVED_BIKE` and `FLAG_DECLINED_BIKE` — whether you already have/declined a bike. No gym-badge or gym-defeat flag is checked anywhere in the file. The bike is available the first time you talk to Rydel in Mauville. | `data/maps/MauvilleCity_BikeShop/scripts.inc` (full file fetched and read) |
| 4 | A Meowth swarm appears on Route 116 after the Elite Four | **REFUTED on species, but the underlying mechanic is real** | Meowth does not appear anywhere in Emerald's wild encounter tables (`src/data/wild_encounters.json` — searched full file, zero hits) and is not in the mass-outbreak species table either. **However, Emerald genuinely has a "mass outbreak" (swarm) system**, gated by `FLAG_SYS_GAME_CLEAR` (i.e. post-Elite-Four, matching the note's timing claim), implemented in `TryStartRandomMassOutbreak()` in `src/tv.c`. Its species pool (`sPokeOutbreakSpeciesList[]`) has exactly 5 fixed entries: Seedot/Route102, Nuzleaf/Route114, Seedot/Route117, Seedot/Route120, and **Skitty (level 8) on Route116**. So there IS a Route-116 post-E4 swarm — the species is **Skitty**, not Meowth. | `src/tv.c` lines ~192-224 (`sPokeOutbreakSpeciesList[]` table) and ~1646-1684 (`TryStartRandomMassOutbreak`, `FlagGet(FLAG_SYS_GAME_CLEAR)` gate); `src/data/wild_encounters.json` (fetched, grepped for "meowth", no matches) |
| 5 | Relicanth holds `ITEM_DEEP_SEA_SCALE` as a wild held item *(note)* — critique said instead `ITEM_DEEP_SEA_TOOTH` | **REFUTED both versions** | Relicanth's `species_info.h` entry has `.itemCommon = ITEM_NONE, .itemRare = ITEM_GREEN_SHARD`. It holds neither Deep Sea item. Deep Sea Tooth and Deep Sea Scale are **not wild held items at all** in this decomp — both are obtained as a one-time trade choice from Captain Stern in Slateport Harbor, in exchange for the Scanner (`SlateportCity_Harbor_EventScript_DeepSeaTooth` / `_DeepSeaScale`, player picks one). Note also: Clamperl's rare item is `ITEM_BLUE_SHARD` (not Big Pearl as the critique's "missing" section claimed). | `src/data/pokemon/species_info.h` line 10739 (`SPECIES_RELICANTH`) and line 10499 (`SPECIES_CLAMPERL`); `data/maps/SlateportCity_Harbor/scripts.inc` lines 335-358 |
| 6 | Mirage Tower fossils are item balls that give the fossil directly *(note)* — critique said instead interacting starts a wild Lileep/Anorith battle at `MAP_MIRAGE_TOWER_2F` | **CONFIRMED (note's core claim), critique's specific citation wrong** | The fossils are on **`MirageTower_4F`**, not 2F, and are given via a plain Yes/No `giveitem` (`MirageTower_4F_EventScript_RootFossil` / `_ClawFossil`) — no wild battle occurs. Taking either fossil sets flags that hide *both* fossils (`FLAG_HIDE_MIRAGE_TOWER_ROOT_FOSSIL` and `FLAG_HIDE_MIRAGE_TOWER_CLAW_FOSSIL` are both set by either script) and removes the chosen object — confirming they are mutually exclusive, one-time, permanent choices. | `data/maps/MirageTower_4F/scripts.inc` (full file fetched); confirmed empty of fossil scripts on `MirageTower_1F/2F/3F/scripts.inc` |
| 7 | A man in Pacifidlog Town trades `ITEM_TM27` (Return) for a Green Shard | **REFUTED** | No shard trade exists anywhere in Pacifidlog Town (checked all 5 houses' scripts). The real mechanic: **`PacifidlogTown_House2`**, the Pokémon Fan Club Chairman's Younger Brother, gives a **free** TM based on your lead Pokémon's friendship score (`GetLeadMonFriendshipScore`) — `ITEM_TM_RETURN` if friendship ≥ 150-199 band, `ITEM_TM_FRUSTRATION` otherwise (with a middling "put in more effort" band with no gift). No item is removed from the player. It is also **not one-time** — `FLAG_RECEIVED_FANCLUB_TM_THIS_WEEK` plus `SetPacifidlogTMReceivedDay`/`GetDaysUntilPacifidlogTMAvailable` show it resets on a weekly real-time cycle, so it's a renewable gift, not a single acquisition. (Note: I also checked `PacifidlogTown_House4` and `_House5` directly, since the critique cited `_House5` as the TM giver — that house is actually the Mirage Island watcher's house and has no TM script at all. The critique's own citation was wrong even though its core "no shard trade" claim was right.) | `data/maps/PacifidlogTown_House2/scripts.inc` (full file fetched); `data/maps/PacifidlogTown_House4/scripts.inc` and `_House5/scripts.inc` (fetched, confirmed no TM/shard content) |
| 8 | Unpicked/neglected berry trees "eventually disappear and are replaced by a new, identical tree of the same type that was originally there" (tree death/regrowth) | **REFUTED, with an added nuance neither the note nor the critique captured** | Confirmed false as stated: in `BerryTreeTimeUpdate()`, if a tree is left too long (`minutes >= GetStageDurationByBerryType(tree->berry) * 71`), the entire tree struct is reset to `gBlankBerryTree` — it does **not** respawn the original default berry; the spot goes back to having no tree. **Additional mechanic not mentioned by either pass**: a *maintained* tree (picked and rewatered in time) regrows the same berry automatically — `BerryTreeGrow()` cycles it from `BERRY_STAGE_BERRIES` back to `BERRY_STAGE_SPROUTED` and increments `tree->regrowthCount`; only after **10** such regrowth cycles does the tree finally reset to blank permanently. So a default wild berry tree is good for up to 10 harvests if kept alive, but is genuinely and permanently lost — not "replaced" — if neglected past ripeness or after the 10th cycle. | `src/berry.c`, function `BerryTreeGrow()` (~line 1048-1073) and `BerryTreeTimeUpdate()` (~line 1078-1112) |
| 9a | "No hidden items on Route 116" | **REFUTED** | Route 116 has **two** hidden items: `ITEM_SUPER_POTION` at (22, 9), flag `FLAG_HIDDEN_ITEM_ROUTE_116_SUPER_POTION`, and `ITEM_BLACK_GLASSES` at (70, 13), flag `FLAG_HIDDEN_ITEM_ROUTE_116_BLACK_GLASSES` (the critique found the Super Potion but missed the Black Glasses, and had the wrong coordinates for the Super Potion — (37,10) vs. the actual (22,9)). | `data/maps/Route116/map.json`, `bg_events` array, two `"type": "hidden_item"` entries (fetched and read directly, not scripts.inc — this decomp version stores hidden items in map.json, not a `hiddenitem` macro in scripts.inc) |
| 9b | "No hidden items on Route 117" | **REFUTED** | Route 117 has one hidden item: `ITEM_REPEL` at (3, 18), flag `FLAG_HIDDEN_ITEM_ROUTE_117_REPEL` (critique had the right item but wrong coordinates — (29,13) vs. actual (3,18)). | `data/maps/Route117/map.json`, `bg_events` array |
| 9c | "No hidden items on Route 134" | **CONFIRMED — the original note was RIGHT and the critique was WRONG** | Both `data/maps/Route134/map.json` and `data/maps/Underwater_Route134/map.json` have a literal empty `"bg_events": []` array — no hidden items exist on Route 134 or its underwater section at all, in either direction. The critique's claimed `ITEM_HEART_SCALE` (21,31) and `ITEM_STAR_PIECE` (48,13) at a map path `Route134_Underwater/scripts.inc` do not exist; that map path isn't even the correct directory name (the real one is `Underwater_Route134`), and its `bg_events` list is empty. This is exactly the "categorical absence claim wrongly overturned" failure mode the task brief warned about — the critique pass fabricated a correction to something that was already true. | `data/maps/Route134/map.json` (`bg_events: []`) and `data/maps/Underwater_Route134/map.json` (`bg_events: []`), both fetched and read in full |

---

## 2. CORRECTED FACTS (usable values)

- **HM07 Waterfall**: obtained from **Wallace** in **Sootopolis City** (NPC gift, not an item
  ball), after `FLAG_SOOTOPOLIS_ARCHIE_MAXIE_LEAVE` is set (post Team Aqua/Magma Sootopolis
  confrontation). Not in Cave of Origin, not in Marine Cave.
- **HM08 Dive**: given directly by **Steven** in his Mossdeep house (`MossdeepCity_StevensHouse`)
  once `VAR_STEVENS_HOUSE_STATE` advances — an NPC gift, not a hidden item, and there is no
  hidden item of any kind in that house.
- **Mach/Acro Bike**: no prerequisite. Available on first talking to **Rydel** in the Mauville
  City Bike Shop; player picks Mach or Acro, and can swap freely afterward.
- **Wild-held Deep Sea items**: neither is a wild held item. Both **Deep Sea Tooth** and **Deep
  Sea Scale** come from a one-time trade with **Captain Stern** in **Slateport Harbor**, in
  exchange for the **Scanner** (player picks exactly one).
- **Relicanth's actual wild held item**: `ITEM_GREEN_SHARD` (rare slot only; no common item).
- **Clamperl's actual wild held item**: `ITEM_BLUE_SHARD` (rare slot only; no common item, and
  no Big Pearl).
- **Mirage Tower fossils**: on **`MirageTower_4F`** (not 2F). Simple `giveitem` on Yes/No
  prompt — no wild battle. Taking either fossil permanently removes the other and collapses the
  tower (mutually exclusive, one-time).
- **Route 116 post-Elite-Four mass outbreak**: species is **Skitty** (level 8), not Meowth.
  Meowth is not obtainable in the wild anywhere in Emerald (trade-only from FR/LG).
- **Pacifidlog friendship TM**: **`PacifidlogTown_House2`**, the Fan Club Chairman's younger
  brother. Free (no shard or any item cost) — gives `ITEM_TM_RETURN` at high lead-Pokémon
  friendship or `ITEM_TM_FRUSTRATION` at low friendship, with a "no gift" middle band. Resets
  weekly (renewable, not a one-time pickup).
- **Berry tree loss**: an unpicked, over-ripe tree resets to no-tree (blank), it does not
  respawn. A maintained tree survives up to **10** harvest cycles before it resets to blank
  regardless of care.
- **Route 116 hidden items**: `ITEM_SUPER_POTION` (22,9) and `ITEM_BLACK_GLASSES` (70,13).
- **Route 117 hidden item**: `ITEM_REPEL` (3,18).
- **Route 134 hidden items**: none — surface and underwater `bg_events` are both empty.
- **Underwater Route 124 hidden items** (spot-checked while verifying the Route 134 shard
  claim): 7 total — `ITEM_CARBOS` (42,51), `ITEM_GREEN_SHARD` (14,40, only **one** shard color,
  not four as one critique claimed), `ITEM_PEARL` (66,34), `ITEM_BIG_PEARL` (64,54),
  `ITEM_HEART_SCALE` ×2 (70,64) and (45,36), `ITEM_CALCIUM` (42,5).

---

## 3. STILL UNRESOLVED

Nothing in the priority list handed to me remains unresolved — all nine target claims were
grounded against a fetched decomp file. Two adjacent things surfaced during this work that
would need their own pass if they matter later:

- **HM06 Rock Smash "Wally's uncle" claim** (flagged by one critique as an RS-vs-Emerald
  difference) — I did not fetch `data/text/maps/mauville_city.inc` to confirm the "Rock Smash
  Guy is not Wally's uncle" claim myself. It wasn't on the priority list, so I left it
  unverified rather than pad the report; **evidence needed**: read that file's NPC text and the
  giver script for `ITEM_HM_ROCK_SMASH`.
- **Exact visual behavior of a "dead" berry tree tile** (whether it renders as bare dirt or
  tilled soil) — the code confirms the save-state fields reset to blank, but I did not trace
  the tile-drawing code that turns `BERRY_STAGE_NO_BERRY` into a specific overworld graphic;
  **evidence needed**: `src/event_object_movement.c` or the berry tree graphics table, if a
  bot ever needs to recognize "empty planted plot" vs. "never-planted tile" visually.

---

## 4. METHOD

- **`gh api repos/pret/pokeemerald/contents/<path>` was reachable and used for every ruling
  above** — no rate-limit or auth failures encountered this session. All fetches were
  `--jq '.content' | base64 -d`, written to the scratchpad directory, then read/grepped
  directly. I did not use WebFetch as a fallback; it was not needed.
- I also used `gh api -X GET "search/code?q=...&repo:pret/pokeemerald"` a handful of times to
  locate which map/file actually contains a given `ITEM_`/function name when I didn't know the
  path up front (e.g. finding `SootopolisCity` as the real HM07 source, finding
  `PacifidlogTown_House2` for the friendship TM). Code search has some indexing gaps for very
  short queries but was reliable for `ITEM_*`, function-name, and multi-word queries.
- **This decomp's data layout differs from what earlier critiques assumed**: current
  `pret/pokeemerald` master stores hidden items as `"type": "hidden_item"` entries inside each
  map's `bg_events` array in `map.json`, not as a `hiddenitem` macro line in `scripts.inc`, and
  base stats live in `src/data/pokemon/species_info.h`, not `src/data/pokemon/base_stats.h`.
  Several critique citations pointed at file paths/macros that don't exist in the current repo
  state — I did not treat a stale path as proof of anything and re-derived the real path in
  each case before ruling.
- `sandbox-pokebot/modules/data/event_flags/emerald.txt` was checked but turned out to be a
  raw *numeric flag ID → short internal name* table (e.g. `1 TEMP_1`), not a list of the
  decomp's full `FLAG_*` constant names, so it could not be used to cross-check the `FLAG_*`
  names found in the decomp scripts. `tools/story-dev/audit_flag_names.py` only audits flag
  names actually referenced by `early_game.py` / `story_mode.py` against that same numeric
  table, so it also wasn't applicable to auditing decomp constant names in isolation — decomp
  file reads were the correct and sufficient tool for this task, per the brief's own emphasis
  on `gh api` as the primary ground truth.
- **Claims grounded: 9 of 9** priority claims from the task brief, each against at least one
  directly-fetched decomp file (several against two, to also check the critique's counter-claim
  rather than just the original note). **Zero UNRESOLVED** on the priority list; two low-priority
  adjacent questions noted above for a future pass if needed.
- Net correction count against the *critique* pass itself (not just the original notes): **2**
  outright wrong critique claims (HM07's "Marine Cave" location; Route 134 "has hidden items"),
  plus **several wrong coordinates** in otherwise-correct critique citations (Route 116/117 hidden
  item coords, the Route 124 four-shards claim, the Pacifidlog House5 citation). This is the
  concrete evidence for why this pipeline needs a tool-using validator as the final word, not a
  third same-model opinion.
