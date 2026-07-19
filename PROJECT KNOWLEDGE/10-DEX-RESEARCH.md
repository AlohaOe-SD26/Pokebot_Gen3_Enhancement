# 10 — POKÉDEX & ITEM-DEX Research (Phase 1: Inventory / Gap Analysis / Schema / Plan)

**Status:** Phase 1 — READ-ONLY research & inventory. No GUI or program code written.
**Scope:** Prepare a living **Pokédex tab** and an **Item-Dex tab** for the pokebot-gen3 fork.
**Data source read:** `custom-pokebot/` (the sandbox), cross-referenced with
`40cakes repo/DOCUMENTATION/05-stats-config-data-tests.md`.
**Date:** 2026-07-19.

> **Headline verdict:** The bot already ships **~90% of the Pokédex data** and
> **most Item-Dex data** as baked-in JSON, plus a live stats.db for caught/shiny
> counts and a save-reader for in-game seen/owned flags. Building the tabs is
> mostly **assembly + a name-normalization map**, not deep research. The genuine
> gaps requiring external Gen-3 research are: **(1) Pokémon dex artwork** (only
> battle sprites ship), **(2) species flavor text + height/weight/category**,
> **(3) item overworld/hidden map locations**, and **(4) the pickup-ability item
> table**. Item images and Pokémon battle sprites are effectively complete.

---

## 1. Bot's shipped data inventory (`custom-pokebot/modules/data/`)

All files are JSON arrays (index in array is meaningful for moves/items). Extracted
from the ROM by `extract.py`. Counts below distinguish **total array entries** from
**real named entries** (the rest are `????????` / `?` placeholder/unused slots).

### `species.json` — **412 entries (386 real, natdex 1–386)**  *(1.08 MB)*
Per-species fields (verified present):

| Field | Type | Notes |
|---|---|---|
| `name` | str | e.g. `"Bulbasaur"`. Uses curly `’`, gender symbols `♀/♂` |
| `national_dex_number` | int | 1–386 |
| `hoenn_dex_number` | int | Hoenn regional number |
| `types` | list[str] | 1–2 types, e.g. `["Grass","Poison"]` |
| `abilities` | list[str] | 1–2 abilities (Gen-3 has no hidden ability) |
| `held_items_rse` | list[[name, prob]] | wild-held items, e.g. Pikachu `[["Oran Berry",0.5],["Light Ball",0.05]]` |
| `held_items_frlg` | list[[name, prob]] | FR/LG wild-held items |
| `base_stats` | dict | `hp, attack, defence, speed, special_attack, special_defence` |
| `gender_ratio` | int | raw Gen-3 value (0–254; 255=genderless) |
| `egg_cycles` | int | steps-to-hatch factor |
| `base_friendship` | int | |
| `catch_rate` | int | 3–255 |
| `safari_zone_flee_probability` | int | Safari flee rate |
| `level_up_type` | str | growth curve, e.g. `"Medium Slow"` |
| `egg_groups` | list[str] | |
| `base_experience_yield` | int | |
| `ev_yield` | dict | EV yield per stat |
| **`learnset`** | dict | **full — see below** |
| `localised_names` | dict | `D/E/F/I/J/S` names only (no dex text) |
| `evolutions` | list[dict] | `{method, method_param, target_species}` e.g. Pikachu `{method:"item", method_param:96(Thunderstone), target_species:26}` |
| `evolves_from` | int/null | reverse pointer |
| `family` | list[int] | full evolution family species indices |

**`learnset` is COMPLETE — all four move sources present:**
- `level_up`: dict `{move_id: level}` (e.g. Bulbasaur `{"33":1}` = Tackle @ Lv1)
- `tm_hm`: list[move_id]
- `tutor`: list[move_id]
- `egg`: list[move_id]

**NOT present in species.json** (→ gaps, see §5): **height, weight, category/species
classification ("Seed Pokémon"), Pokédex flavor text.** Confirmed by field dump and
`grep` (0 hits for height/weight/category/flavor in species.json and extract.py).

### `moves.json` — **355 entries (354 real; index 0 = `"-"`)**  *(443 KB)*
Array index = move ID (verified: index 33 = Tackle, 15 = Cut). Fields:
`name, effect, base_power, type, accuracy, pp, secondary_accuracy, target, priority,
makes_contact, is_sound_move, affected_by_protect, affected_by_magic_coat,
affected_by_snatch, usable_with_mirror_move, affected_by_kings_rock,
tm_hm` (e.g. `"HM01"` / `"TM26"` / null), `localised_names`, `localised_descriptions`
(full move descriptions in 6 languages). → Powers the "learnable moves" section directly.

### `items.json` — **377 entries (309 real)**  *(414 KB)*
Fields: `index, name, price, type, battle_use, field_use, pocket` (`items / berries /
tms_and_hms / poke_balls / key_items`), `hold_effect, parameter, extra_parameter,
tm_hm_move_id` (links TM/HM item → move), `localised_names`,
**`localised_descriptions`** (full item descriptions, 6 languages). → item info +
description ready out of the box.

### `abilities.json` — **78 entries (77 real)**
Fields: `name, localised_names, localised_descriptions` (full ability text).

### `types.json` — **18 entries**
Fields: `name, effectiveness` (type-chart multipliers), `localised_names`.

### `natures.json` — **25 entries**
Fields: `name, localised_names`, 5 stat modifiers. (Not core to the two dexes, but available.)

### TM/HM / tutor / egg-move data
There is **no separate tm/hm/tutor/egg file** — this data lives **inside each species'
`learnset`** (per-species lists of move IDs), and the reverse (which item is which TM)
lives in `items.json.tm_hm_move_id` + `moves.json.tm_hm`. Everything needed to render
"learnable moves (level-up + TM/HM + tutor + egg)" is present and cross-linkable by move ID.

---

## 2. Caught / shiny counts source

Two independent, complementary sources exist:

### A. `stats.db` (per-profile SQLite) via `modules/stats.py` — lifetime bot counts
- **`get_global_stats() -> GlobalStats`** (stats.py:819). `GlobalStats.encounter_summaries`
  is `dict[species_id -> EncounterSummary]`.
- **`EncounterSummary`** (stats.py:317) fields relevant to the dex:
  `total_encounters`, `shiny_encounters`, **`catches`**, plus IV/SV records & phase stats.
- **Per-species keying:** normal species keyed by `species.index`. **Unown special index:**
  `20100 + unown_letter_index` (confirmed in `SpeciesRecord.species_id_for_database`,
  stats.py:96–100, and DOC 05 §encounter_summaries). `GlobalStats.species(pokemon)` resolves
  the right summary and returns a zeroed summary if the species was never encountered.
- Backing table **`encounter_summaries`** (one row/species): `total_encounters,
  shiny_encounters, catches, ...` (DOC 05:74). Already serialized to the web via
  `context.stats.get_global_stats().to_dict()` (http.py:519).
- **Living-dex "caught?"** → `catches > 0` (bot-caught) — see caveat below.
- **"# shinies caught of this species"** → **caveat:** `shiny_encounters` counts shiny
  *encounters*, not specifically shiny *catches*. There is no per-species "shiny catches"
  counter. Options: use `shiny_encounters` as the displayed number (honest label: "shinies
  seen"), or derive shiny-catch count by querying the raw `encounters` table
  (`get_encounter_log()` / `query_encounters(where, params)`) filtering `is_shiny=1 AND
  outcome=Caught`. The `encounters` table stores the full Pokémon data structure per row
  (DOC 05:54–61), so this is queryable but **not** every encounter is inserted (only if
  `log_encounters` on, or shiny/filter match — DOC 05:63), so raw-row shiny catches are
  reliable (shinies are always "of interest") but total counts must come from the aggregate.

### B. Save read via `modules/pokedex.py` — in-game seen/owned flags
- **`get_pokedex() -> Pokedex`** reads the save blocks; exposes:
  - `Pokedex.seen_species -> list[Species]`
  - `Pokedex.owned_species -> list[Species]` (the true in-game "caught" flag)
  - `is_national_dex_enabled`
- `to_dict()` returns `{"seen":[...], "owned":[...]}`; already served at HTTP `/pokedex`
  (http.py:195) and streamed (http_stream.py:268).

**Recommendation:** the living-dex "caught?" mark should use the **in-game `owned_species`**
flag (authoritative "you have owned this species"), and show the **bot's `catches` count**
and **`shiny_encounters`** as secondary stats from stats.db. Merge both at runtime.

---

## 3. Image / asset audit (`modules/web/static/sprites/`)

Subfolders: `badges, items, other, pokeblocks, status, stream-overlay, tcg, types,
pokemon/, pokemon-animated/`.

### Pokémon
`pokemon/` contains: `normal/`, `normal-cropped/`, `shiny/`, `shiny-cropped/`,
`anti-shiny/`, plus `Egg.png`. `pokemon-animated/` has `normal/`, `shiny/`, `anti-shiny/`
gifs + `Egg.gif`.

- **413 files** each in `normal/`, `shiny/`, `normal-cropped/`.
- **Dimensions:** `normal/Bulbasaur.png` = **128×128** (upscaled front battle sprite);
  `normal-cropped/` = tight-cropped (62×72). Items 24×24.
- **These are ALL battle (front) sprites** — full, cropped, and animated variants of the
  same in-battle art. **There is NO separate "Pokédex / box / Sugimori artwork" image.**
- **Coverage:** all **386 real species** have normal + shiny + cropped sprites. The 30
  "missing" names are (a) `?`/`??????????` placeholder indices (expected/irrelevant), and
  (b) **naming-convention mismatches only**, not real gaps:
  - `Nidoran♀`→`Nidoran_f.png`, `Nidoran♂`→`Nidoran_m.png`
  - `Farfetch’d`→`Farfetch_d.png`
  - `Mr. Mime`→`Mr. Mime.png` (exists)
  - `Unown` (base) → per-letter files `Unown (A).png` … `Unown (Z).png` + `Unown (em).png`
    (!) + `Unown (qm).png` (?) — 28 forms, matching stats.db's Unown keying.
  → A small **name→filename normalization map** resolves all of these.

**VERDICT (Pokémon images):** Battle sprite = **YES** (complete, 3 sizes + animated).
Dex/box artwork = **NO — must be sourced externally** (Phase 3).

### Items
`items/` — **306 files**, 24×24 bag icons (`Potion.png`, `Oran Berry.png`).
- Gen-3 items have exactly **one** official image (the bag icon); there is no separate
  larger "inventory image." So one style is the correct and complete answer.
- **Coverage:** 309 real items vs 306 files. The 78 "missing" are almost all
  `????????` unused slots, plus a handful of naming mismatches (again resolvable):
  `Guard Spec.`→`Guard Spec.png`, `Thunderstone`→`Thunder Stone.png`,
  `Exp. Share`→`Exp Share.png`, `King’s Rock`→`Kings Rock.png`,
  `S.S. Ticket`→`SS Ticket.png`, `Oak’s Parcel`→`Oaks Parcel.png`,
  `Rm. 1 Key` etc. (FR/LG key items). Essentially every obtainable Emerald item has an icon.

**VERDICT (item images):** Sprite/inventory icon = **YES** (complete). Separate "inventory
image" beyond the bag icon = **N/A in Gen 3** (the bag icon IS it).

### Other useful asset folders (bonus, ready to use)
`types/` (18 type badges + `large/` + `swsh/` variants), `badges/` (gym badges),
`pokeblocks/` (5 flavor icons), `status/`, `other/` (Male/Female/Pokérus/Feeder/Birch),
`tcg/`, `stream-overlay/`.

---

## 4. Item map-location + used-by / drop data — the hard part

What the bot HAS vs what it does NOT have for "where to find items" and "what uses them":

### Already in the bot (assembly, no research needed)
- **"Held by wild Pokémon"** → invert `species.json` `held_items_rse` / `held_items_frlg`.
  Verified: Pikachu holds Oran Berry (50%) + Light Ball (5%); Butterfree→Silverpowder, etc.
  This gives a solid "wild Pokémon that hold this item (+ probability)" list per item.
- **"Which Pokémon can learn a TM/HM"** (for TM/HM items) → cross-reference
  `items.json.tm_hm_move_id` → move → every species whose `learnset.tm_hm` contains it.
- **Berries** → `items.json` berries pocket + descriptions; `berry_trees.py` reads **live**
  planted berry-tree state from the save (stage, yield) — but that's dynamic garden state,
  **not** a catalog of where each berry is first obtained.
- **Mart inventories** → `mart.py` `get_mart_buyable_items()` reads only the **currently
  open** mart from live memory. **No static per-town mart catalog** exists.
- **Pickup tracking** → `stats.db.pickup_items` (item_id, item_name, times_picked_up) logs
  items the bot's Pickup Pokémon actually grabbed — a **dynamic counter**, not the static
  "which species + which level band yields which item" **Pickup table**.

### NOT in the bot (→ requires external Gen-3 Emerald research)
- **Overworld item-ball locations** (the Poké Ball items lying on maps) — no data.
- **Hidden items** (Itemfinder spots) — no data.
- **Marts by town / their stock lists** — only live-read, no static catalog.
- **Gift items / one-time event items / TM locations** — no data.
- **NPC-given items** — no data.
- **The Pickup-ability item table** (level-banded drop rates) — not shipped; only what the
  bot happened to pick up is recorded.
- **"Drops"** — Gen-3 wild Pokémon do not "drop" items on faint (no drop mechanic); the
  correct analog is **wild-held items** (covered above). So "drop" = held-item probability.

**Gap size for item locations:** MEDIUM-LARGE. The location catalog (item balls + hidden
items + mart stock + gifts) for all ~300 items must be compiled from a trusted external
Gen-3 source (Bulbapedia / a decomp map dump) — this is the single biggest research task.

---

## 5. Gap analysis — SOURCE per requested field

Legend: **BOT** = shipped JSON · **STATS** = stats.db · **SAVE** = live save read ·
**RESEARCH** = not available, needs external Gen-3 sourcing.

### POKÉDEX tab
| Requested field | Source |
|---|---|
| Search all obtainable species | **BOT** (species.json, 386) |
| Caught? (living-dex mark) | **SAVE** (`owned_species`) + **STATS** (`catches>0`) |
| # shinies caught | **STATS** (`shiny_encounters`; true shiny-*catches* via raw `encounters` query) |
| Types | **BOT** |
| Abilities | **BOT** |
| Base stats | **BOT** |
| Dex numbers (national + Hoenn) | **BOT** |
| Category ("Seed Pokémon") | **RESEARCH** |
| Height / weight | **RESEARCH** |
| Flavor text | **RESEARCH** |
| Gender ratio / egg groups / egg cycles / catch rate / EV yield / base exp / friendship / growth rate / safari flee | **BOT** |
| Evolutions / evolves-from / family | **BOT** |
| Learnable moves: level-up | **BOT** (`learnset.level_up`) |
| Learnable moves: TM/HM | **BOT** (`learnset.tm_hm`) |
| Learnable moves: tutor | **BOT** (`learnset.tutor`) |
| Learnable moves: egg | **BOT** (`learnset.egg`) |
| Move details (power/acc/pp/type/effect/desc) | **BOT** (moves.json) |
| Battle sprite (normal + shiny) | **BOT** (assets, complete) |
| Pokédex/box artwork image | **RESEARCH** (only battle sprites ship) |

### ITEM-DEX tab
| Requested field | Source |
|---|---|
| Search all items | **BOT** (items.json, 309) |
| Total collected historically | **STATS partial** — only Pickup items are historically counted; **general item-acquisition history is NOT tracked** → RESEARCH/FEATURE (would need a new counter) |
| Currently held (bag + PC + party) | **SAVE** (`get_item_bag`/`get_item_storage`; party held items via pokemon data) |
| Item info / description | **BOT** (`localised_descriptions`) |
| Pocket / price / hold effect / TM link | **BOT** |
| Where to find on the map | **RESEARCH** (item balls, hidden items, marts, gifts) |
| Pokémon that hold/use it (wild-held) | **BOT** (invert `held_items_rse/frlg`) |
| Pokémon that can use a TM/HM item | **BOT** (cross-ref learnsets) |
| Pickup-ability item table | **RESEARCH** |
| Item sprite / inventory icon | **BOT** (assets, complete) |

**Big picture:** For the **Pokédex**, only 5 things need research (category, height,
weight, flavor text, dex artwork). For the **Item-Dex**, the research is item **map
locations**, the **pickup table**, and deciding how to handle **historical "total collected"**
(new bot feature vs omit). Everything else is assembly.

---

## 6. Proposed data model

Two static precomputed JSON datasets (built once from bot data + research), **merged with
live counts at runtime**. Rationale: species/move/item base data is immutable per ROM, so
precompute a clean, denormalized `pokedex_data.json` / `itemdex_data.json` (fast, no
per-request cross-referencing); overlay the volatile caught/shiny/held numbers live.

### `pokedex_data` (array, one object per species; national_dex order)
```jsonc
{
  "national_dex_number": 25,
  "hoenn_dex_number": 156,
  "name": "Pikachu",
  "types": ["Electric"],
  "abilities": ["Static"],
  "base_stats": {"hp":35,"attack":55,"defence":30,"speed":90,"special_attack":50,"special_defence":40},
  "bst": 300,
  "ev_yield": {...},
  "catch_rate": 190,
  "gender_ratio": 127,
  "egg_groups": ["Field","Fairy"],
  "egg_cycles": 10,
  "growth_rate": "Medium Fast",
  "base_experience_yield": 82,
  "base_friendship": 70,
  "safari_zone_flee_probability": 0,
  "evolutions": [{"method":"item","item":"Thunderstone","target":"Raichu"}],
  "evolves_from": null,
  "family": ["Pichu","Pikachu","Raichu"],
  "learnset": {
    "level_up": [{"level":1,"move":"Thunder Shock"}, ...],
    "tm_hm":  [{"id":"TM24","move":"Thunderbolt"}, ...],
    "tutor":  ["...move names..."],
    "egg":    ["...move names..."]
  },
  "sprites": {"normal":"pokemon/normal/Pikachu.png","shiny":"pokemon/shiny/Pikachu.png",
              "cropped":"pokemon/normal-cropped/Pikachu.png","animated":"pokemon-animated/normal/Pikachu.gif"},
  // ---- RESEARCH-sourced (Phase 3) ----
  "category": "Mouse Pokémon",
  "height_m": 0.4,
  "weight_kg": 6.0,
  "flavor_text": "…",
  "dex_artwork": "pokemon/artwork/Pikachu.png"   // to be sourced
}
```
**Live overlay** (fetched from `/pokedex` + global-stats endpoint, merged client-side by
species id / national dex):
```jsonc
{ "owned": true, "seen": true,
  "bot_catches": 3, "bot_total_encounters": 412, "shiny_encounters": 1 }
```

### `itemdex_data` (array, one object per item; by index)
```jsonc
{
  "index": 200,
  "name": "Leftovers",
  "pocket": "items",
  "price": 200,
  "description": "A hold item that gradually restores HP in battle.",
  "hold_effect": "leftovers",
  "tm_hm_move": null,                      // for TM/HM items → move name
  "sprite": "items/Leftovers.png",
  "held_by": [ {"species":"Snorlax","game":"rse","probability":0.05}, ... ],  // inverted from species.json
  "learnable_by": [ ... ],                 // TM/HM items only: species that can learn it
  // ---- RESEARCH-sourced (Phase 3) ----
  "locations": [ {"map":"Route 118","method":"item_ball"}, {"map":"...","method":"hidden"} ],
  "pickup_from": [ {"species":"Meowth","level_band":"1-10","rate":0.01} ]  // pickup table
}
```
**Live overlay** (from `/items` + stats.db):
```jsonc
{ "held_now": 3,        // bag+PC+party current quantity (SAVE)
  "pickup_total": 12 }  // stats.db pickup_items.times_picked_up (only pickup items)
```

**Precompute vs live:** Precompute the two static JSONs from bot data (Phase 2) so the tabs
load instantly and don't re-cross-reference 386×354 relationships per request. Read live
only the small volatile overlay (owned/seen, catches, shiny count, current held qty) via the
existing `/pokedex`, `/items`, and global-stats HTTP endpoints. A build script can regenerate
the static JSONs whenever `modules/data/*.json` changes.

---

## 7. Phased plan

- **Phase 1 (this doc) — DONE.** Inventory, image audit, source mapping, schema, gaps.
- **Phase 2 — Compile the static datasets from bot data (no external research).**
  Write a build script that reads `species/moves/items/abilities/types.json`, resolves all
  move-ID → name links, builds learnsets, inverts held_items → `held_by`, cross-refs TM/HM →
  `learnable_by`, applies the sprite **name-normalization map**, and emits
  `pokedex_data.json` + `itemdex_data.json` (BOT-sourced fields only; research fields left
  null). **Fact-check:** verify N random species (types/BST/evolutions/learnset counts) and
  N items against the source JSON and against Bulbapedia spot-checks.
- **Phase 3 — Source the missing pieces (external Gen-3 research, with citations).**
  (a) Pokémon **category, height, weight, flavor text** (386 species) — from Bulbapedia /
  pokeemerald decomp (`pokedex_text.h`, `pokedex_entries.h`). (b) **Dex artwork** images
  (Sugimori/box art, 386) — sourced & placed in a new `pokemon/artwork/` asset set.
  (c) **Item map locations** (item balls, hidden items, mart stock, gifts) + the **Pickup
  table** — from Bulbapedia / decomp map files. Each datum cited. This is the real "deep
  research" bucket and the largest effort.
- **Phase 4 — Sanity / fact-check pass.** Adversarially verify a sample of every
  research-sourced field against a second source; reconcile the name-normalization map
  against 100% of sprite files (no unresolved names); confirm stats.db keying incl. Unown.
- **Phase 5 — Build the tabs (GUI/program code — first non-read-only phase).** Pokédex tab
  (search/filter, living-dex grid, detail view w/ moves + both images) and Item-Dex tab
  (search, counters, locations, held-by), consuming the static JSON + live overlay endpoints.

**Effort estimate:** Phases 2 (assembly) is small; the research is concentrated in Phase 3,
dominated by item locations + dex artwork. Pokémon text fields (height/weight/category/flavor)
are cleanly available in the pokeemerald decomp, so that sub-task is low-risk.

---

## 8. Preliminary sanity check (verified against the actual files)

**Species (5) — all fields present & values correct:**
| # | Name | Types | Abilities | BST | Catch | lvlup / tm+hm / tutor / egg | Evolution |
|---|---|---|---|---|---|---|---|
| 6 | Charizard | Fire/Flying | Blaze | 534 | 45 | 11 / 28 / 20 / 0 | (final) |
| 25 | Pikachu | Electric | Static | 300 | 190 | 11 / 22 / 19 / 0 | item 96 (Thunderstone)→Raichu |
| 201 | Unown | Psychic | Levitate | 336 | 225 | 1 / 0 / 0 / 0 | (none) |
| 302 | Sableye | Dark/Ghost | Keen Eye | 380 | 45 | 13 / 29 / 21 / 3 | (none) |
| 384 | Rayquaza | Dragon/Flying | Air Lock | 680 | 3 | 11 / 36 / 15 / 0 | (none) |

All cross-checked against known Gen-3 values (Charizard BST 534 ✓, Rayquaza 680/catch 3 ✓,
Pikachu→Raichu via Thunderstone ✓). Learnset's four buckets populate as expected (Unown only
learns Hidden Power — 1 level-up move, no TM/tutor/egg ✓).

**Items (5) — all fields present & values correct:**
| Item | idx | pocket | price | hold_effect | tm_move | desc (E) |
|---|---|---|---|---|---|---|
| Master Ball | 1 | poke_balls | 0 | – | – | "The best BALL that catches a POKéMON without fail." |
| Leftovers | 200 | items | 200 | leftovers | – | "…gradually restores HP in battle." |
| TM26 | 314 | tms_and_hms | 3000 | – | 89 (Earthquake) | "Causes a quake…no effect on flying foes." |
| Rare Candy | 68 | items | 4800 | – | – | "Raises the level of a POKéMON by one." |
| Lava Cookie | 38 | items | 200 | – | – | "…heals all status problems." |

Descriptions, pockets, hold effects, and TM→move linkage all verified present and correct.

**Sprite spot-checks:** `pokemon/normal/Bulbasaur.png` (128×128), `.../normal-cropped/` (62×72),
`pokemon/shiny/Charizard.png`, `items/Potion.png` & `items/Oran Berry.png` (24×24) all exist.
Naming edge-cases (`Nidoran_f/_m`, `Farfetch_d`, `Unown (A)…`, `Thunder Stone`, `Kings Rock`)
confirmed present under normalized filenames.

---

## Summary for the parent

- **Already in hand (assembly, not research):** full per-species data incl. **complete
  learnsets (level-up + TM/HM + tutor + egg)**, evolutions/family, base stats, catch rate,
  EV/egg/gender/growth data; full **move** and **item** databases with **descriptions**;
  wild-**held-items** (→ "held by") and TM→move→learnable-by cross-refs; **caught/shiny**
  counts from `stats.db` (`encounter_summaries`, Unown keyed 20100+letter) and **in-game
  seen/owned** from the save (`pokedex.py`); current **held quantities** from bag/PC/party.
  All served today via existing `/pokedex`, `/items`, and global-stats HTTP endpoints.
- **Genuine gaps needing research:** (1) Pokémon **dex/box artwork** (only battle sprites
  ship), (2) species **flavor text + height + weight + category** (cleanly in pokeemerald
  decomp), (3) item **overworld/hidden map locations + mart stock + gifts** (biggest task),
  (4) **Pickup-ability item table**, and (5) a decision on **historical "total items
  collected"** (bot only counts Pickup items today — would need a new counter or be omitted).
- **Image verdict:** Pokémon battle sprites = **YES/complete** (normal+shiny+cropped+animated,
  386/386 after a name-normalization map); Pokémon dex artwork = **NO** (source in Phase 3);
  item icons = **YES/complete** (Gen-3 items have only the one bag icon).
- **Recommended next phase:** **Phase 2** — write the build script to assemble
  `pokedex_data.json` + `itemdex_data.json` from bot JSON (all BOT-sourced fields), with a
  fact-check pass; this proves out ~90% of the datasets before committing to the Phase-3
  external research (which is bounded and dominated by item locations + dex artwork).
