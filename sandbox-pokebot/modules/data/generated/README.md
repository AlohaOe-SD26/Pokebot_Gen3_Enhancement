# Generated Dex Datasets (DEX DATA — Phase 2)

Static, denormalized datasets for the future **Pokédex** and **Item-Dex** tabs,
assembled from the bot's shipped ROM-extracted JSON. These are **build
artifacts** — do not hand-edit them; regenerate instead (see below).

- `pokedex_data.json` — one entry per real species (**386**, national-dex order)
- `itemdex_data.json` — one entry per real item (**309**)

## Regenerate

```
cd sandbox-pokebot
py -3.12 tools/build_dex_data.py
```

The build script reads `modules/data/{species,moves,items,abilities,types,
natures}.json` and the sprite folders under `modules/web/static/sprites/`,
resolves every move/ability/type/item cross-reference to a name, inverts wild
held-items into `held_by`, cross-references TM/HM → `learnable_by`, applies the
sprite name-normalization map, and writes the two JSON files here. It prints a
validation summary and exits non-zero if referential integrity or the required
species sprites (normal + shiny + cropped) ever fail. Rerun it whenever
`modules/data/*.json` or the sprite sets change.

## Static vs. runtime-merged

These files hold **only immutable, per-ROM data** (base stats, learnsets,
evolutions, descriptions, sprite paths, held-by, …). **Live per-profile counts
are intentionally NOT baked in** — the future tab merges them at runtime, keyed
by species national-dex / item index:

| Live overlay | Source |
|---|---|
| Pokédex `owned` / `seen` flags | save read — `modules/pokedex.py` `get_pokedex()` → `owned_species` / `seen_species` |
| Bot catches / total & shiny encounters (per species) | `modules/stats.py` `get_global_stats()` → `GlobalStats.encounter_summaries` (Unown keyed `20100 + letter`) |
| Item quantity currently held (bag + PC + party) | save read — `get_item_bag()` / `get_item_storage()` + party held items |
| Item pickup totals | `stats.db` `pickup_items.times_picked_up` (Pickup-ability items only) |

The tabs load these static JSONs once (instant, no per-request cross-referencing
of 386 × 354 relationships) and overlay the small volatile numbers live via the
existing `/pokedex`, `/items`, and global-stats HTTP endpoints.

## Schema

### `pokedex_data.json` (array, national-dex order)

```jsonc
{
  "national_dex_number": 25,
  "hoenn_dex_number": 156,
  "name": "Pikachu",
  "localised_names": { "D": "...", "E": "...", "F": "...", "I": "...", "J": "...", "S": "..." },
  "types": ["Electric"],
  "abilities": ["Static"],
  "base_stats": { "hp":35, "attack":55, "defence":30, "speed":90, "special_attack":50, "special_defence":40 },
  "bst": 300,                       // derived: sum of base_stats
  "ev_yield": { "hp":0, ... },
  "catch_rate": 190,
  "base_experience_yield": 82,
  "gender_ratio": 127,              // raw Gen-3 female-threshold byte (255 = genderless)
  "gender": { "genderless": false, "male_percent": 50.0, "female_percent": 50.0 },  // derived
  "egg_groups": ["Field", "Fairy"],
  "egg_cycles": 10,
  "base_friendship": 70,
  "growth_rate": "Medium Fast",     // from species.level_up_type
  "safari_zone_flee_probability": 0,
  "evolves_from": "Pichu",          // resolved name (null if base form)
  "evolutions": [
    { "method": "item", "target": "Raichu", "target_national_dex": 26, "item": "Thunderstone" }
    // level methods carry "parameter": <level/beauty/etc.>; item/trade_with_item carry "item"
  ],
  "family": ["Pichu", "Pikachu", "Raichu"],   // resolved names, full evolution family
  "held_items": [                              // wild-held items, both game sets
    { "item": "Oran Berry",  "probability": 0.5,  "game": "rse" },
    { "item": "Light Ball",  "probability": 0.05, "game": "rse" }
  ],
  "learnset": {
    "level_up": [ { "level": 1, "move": "Thunder Shock" }, ... ],  // sorted by level
    "tm_hm":    [ { "tm_hm": "TM24", "move": "Thunderbolt" }, ... ],
    "tutor":    ["Body Slam", ...],
    "egg":      ["Wish", ...]
  },
  "sprites": {
    "normal":          "pokemon/normal/Pikachu.png",
    "shiny":           "pokemon/shiny/Pikachu.png",
    "normal_cropped":  "pokemon/normal-cropped/Pikachu.png",
    "shiny_cropped":   "pokemon/shiny-cropped/Pikachu.png",
    "animated_normal": "pokemon-animated/normal/Pikachu.gif",
    "animated_shiny":  "pokemon-animated/shiny/Pikachu.gif"
  },   // paths are relative to modules/web/static/sprites/

  // ---- Phase-3 RESEARCH GAPS (null until sourced externally) ----
  "_phase3_gaps": ["dex_artwork","flavor_text","height_m","weight_kg","category"],
  "dex_artwork": null,
  "flavor_text": null,
  "height_m":    null,
  "weight_kg":   null,
  "category":    null
}
```

**Keying note:** in `species.json`, the `family`, `evolves_from`, and evolution
`target_species` fields are **array indices (Gen-3 internal species IDs), not
national-dex numbers** — the build script resolves them via the array index.
(They coincide for Gen 1/2 species but diverge for Hoenn, e.g. Ralts internal
392 ≠ national-dex 280.)

### `itemdex_data.json` (array, source order)

```jsonc
{
  "index": 200,                     // Gen-3 item id (item.index — NOT array position)
  "name": "Leftovers",
  "localised_names": { "D": "...", "E": "...", ... },
  "pocket": "items",                // items | berries | tms_and_hms | poke_balls | key_items
  "price": 200,
  "sell_price": 100,                // derived: price // 2 (Gen-3 convention)
  "hold_effect": "leftovers",
  "parameter": 0,
  "description": "A hold item that gradually restores HP in battle.",  // English convenience copy
  "localised_descriptions": { "D": "...", "E": "...", ... },
  "tm_hm_move_id": null,            // for TM/HM items → move id
  "tm_hm_move": null,               // for TM/HM items → resolved move name
  "sprite": "items/Leftovers.png",  // relative to sprites root; null if no icon ships
  "held_by": [                      // inverted from species held_items_rse/frlg
    { "species": "Snorlax", "game": "rse", "probability": 1 }
  ],
  "learnable_by": null,             // TM/HM items only: sorted list of species that can learn the move (else null)

  // ---- Phase-3 RESEARCH GAPS (null until sourced externally) ----
  "_phase3_gaps": ["map_locations","mart_stock","pickup_chance"],
  "map_locations": null,
  "mart_stock":    null,
  "pickup_chance": null
}
```

## Phase-3 gap fields (awaiting external Gen-3 research)

Left `null` by design — they are **not** in the bot's shipped data:

- **Pokédex:** `dex_artwork` (only battle sprites ship — Sugimori/box art must be
  sourced), `flavor_text`, `height_m`, `weight_kg`, `category` ("Mouse Pokémon").
  The four text fields are cleanly available in the pokeemerald decomp.
- **Item-Dex:** `map_locations` (item balls / hidden items / gifts), `mart_stock`
  (per-town mart catalogs), `pickup_chance` (the Pickup-ability level-band table).

---

## Validation report (last build)

Generated by `tools/build_dex_data.py` (`py -3.12`, cwd `sandbox-pokebot`).

### Counts
- `species.json` array entries: **412** → real species emitted: **386** ✓ (national-dex 1–386)
- `items.json` array entries: **377** → real items emitted: **309** ✓ (68 `????????` placeholder slots excluded)
- Reference tables loaded: 355 moves, 78 abilities, 18 types.

### Referential integrity — **PASS**
- Every learnset move id (level-up / tm_hm / tutor / egg) resolves to a real move name — **0 orphan ids**.
- Every species ability resolves to `abilities.json`; every type resolves to `types.json` — **0 unresolved**.
- Every evolution `target` and every `family` member resolves (via array index) — **0 unresolved**.
- Every `evolves_from` resolves — **0 unresolved**.
- Every wild-held item name resolves to a real item in `items.json` — **0 unresolved**.
- Every `held_by` species exists — **0 missing**.
- Every TM/HM item's `tm_hm_move_id` resolves to a real move — **0 unresolved**.

### Sprite existence — species **PASS**, items **1 known gap set**
- All **386** species: normal + shiny + normal-cropped + animated (normal & shiny)
  battle sprites exist on disk after name-normalization — **0 missing**.
  (Edge cases verified: `Nidoran♀/♂` → `Nidoran_f/_m`, `Farfetch’d` → `Farfetch_d.png`
  but animated `Farfetch'd.gif`; `Unown` → `Unown (P).png`; `Ho-Oh` → animated `Ho-oh.gif`.)
- Items: **305 / 309** icons resolve. **4 items have no shipped icon** — all obscure
  FR/LG Rocket-Hideout key items with no bag sprite in the repo:
  `Rm. 1 Key` (281), `Rm. 2 Key` (282), `Rm. 4 Key` (283), `Rm. 6 Key` (284).
  Their `sprite` is `null`. (14 items required the manual override map — e.g.
  `Thunderstone` → `Thunder Stone.png`, `King’s Rock` → `Kings Rock.png`,
  `MysticTicket` → `Mysticticket.png` — all resolved except the 4 above.)

### Spot-checks (assembled entries eyeballed vs source) — all correct
**Species:** Unown #201 (Psychic/Levitate, BST 336, catch 225, only Hidden Power,
genderless, sprite `Unown (P)`); Deoxys #386 (Psychic/Pressure, BST 600, catch 3);
Wurmple #265 (both Silcoon & Cascoon evolutions, family of 5); Vaporeon #134
(evolves_from Eevee, Water/Water Absorb, 87.5♂/12.5♀); Charmander #4 (→ Charmeleon
@ Lv16, family of 3, 8 egg moves); Rayquaza #384 (Dragon/Flying, Air Lock, BST 680).
**Items:** TM26 Earthquake (→ 128 learners), HM01 Cut (→ 113 learners), Oran Berry
(berry, restore_hp, held by 18 incl. Pikachu 50%), Master Ball (poke_balls, price 0),
Leftovers (held by Snorlax 100%), Rare Candy, Light Ball (held by Pikachu 5%),
Devon Scope (key item). All fields match the source JSON.
