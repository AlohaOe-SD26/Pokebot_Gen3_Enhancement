# 2026-09-29 — design v2 step 0: the three claims VERIFIED before any doc states them

> A NOTE. Three independent Claude agents (read-only) plus the orchestrator's own re-checks, as recorded below. It
> backs the step-0 doc edits: the `#24-rarepredicate` correction, KI-109 to KI-111, and the Sudowoodo data note.

## 1. `rare_species_dataset.py`: SUPPORTED, but it is TWO defects, not one

- **Defect 1, the edge parse (`tools/story-dev/rare_species_dataset.py:79`).**
  - The script has `s, d = tuple(edge[0]), tuple(edge[1])`.
  - `warp_graph.py:58-59` stores an edge as `[from_map, from_coords, to_map, to_coords]`, so `edge[1]` is a TILE
    coordinate, not a map.
- **Defect 2, the seeds (`:83-84`).**
  - The comment "Underwater maps are not group 0" is FALSE: `map_data.py:844-850` puts `UNDERWATER_ROUTE*` at
    (0,50)-(0,56).
  - The recorded spec seeds "every NON-underwater group-0 map".
- **Runs** (agent, scratch copies; the orchestrator re-ran C itself: identical):

| Run | Histogram | depth ≥ 3 | RARE | Bagon |
|---|---|---|---|---|
| A, unchanged | d0=62 d1=36 d2=22 d3=11 d99=1 | 12 | 23 | d2 |
| B, `edge[2]` only | d0=62 d1=21 d2=39 d3=7 d4+=3 d99=0 | 10 | 23 | d3 |
| **C, both fixes** | **d0=59 d1=21 d2=39 d3=7 d4+=3 d99=3** | **13** | **26** | **d3** |
| D, underwater only | d0=59 d1=4 d2=54 d3=9 d4+=2 d99=4 | 15 | 26 | d2 |

- C matches every number the 2026-08-06 record gives (archive ~6149). Run A matches the 2026-08-07 "computed" row that
  produced the "does not reproduce" verdict, digit for digit.
- **Also retired by the fix:** 03's "making warps bidirectional moved d99 from 34 to 1". That sensitivity exists only
  under the parse bug: with `edge[2]`, one-way and two-way warps give identical per-species depths.
- **Not reproduced (tangential):** the record's "adding the water-only axis takes the set from 26 to 61". It measures
  46 to 52.
- **Record error:** the caches are NOT committed (`sandbox-pokebot/.gitignore:40` ignores `cache/`). They are generated
  from the ROM, and every copy checked is identical.

## 2. Damage calculator (`sandbox-pokebot/modules/battle_strategies/_util.py`): both REAL, plus a third

- **KI-109 (live effect).** `:218` checks `move.name == "Sonic Boom"` and `:227` checks `"Psy Wave"`, but `moves.json`
  spells them `"Sonicboom"` (:1718) and `"Psywave"` (:5218). So both are scored as 1-power moves by every move picker.
  - Measured: an L18 Voltorb picks Tackle (7) over Sonicboom (really 20).
  - ‼ The fixed-damage returns (`:215-228`) come AFTER the type multiply and ignore immunity: Seismic Toss vs Ghost and
    Night Shade vs Normal already score 20. A fix must match on `move.effect` AND return 0 on a 0 type product.
- **KI-110 (dormant).** `:342` boosts OUR Sp. Def on `BADGE08_GET`; the decomp (`pokemon.c:3167`) does it on
  `FLAG_BADGE07_GET`. The Mind Badge boosts both Sp. Atk and Sp. Def, in pokeruby and pokefirered too.
  - No caller computes damage aimed at us, so the line never runs today.
  - The code also lacks `ShouldGetStatBadgeBoost`'s exceptions: no badge boost in the Battle Frontier, link or e-Reader
    battles.
- **KI-111 (NEW, live effect).** `:508` checks `move.name == "Solar Beam"`; the data name is `"Solarbeam"` (:2663). So
  the weather halving never applies. The same misspelling in `profiles/battle.yml:31`, the template, the schema default
  and `pokemon_league.py:2469` means **Solarbeam is not actually banned**, although it is listed as a banned two-turn
  move.
- All three are UPSTREAM bugs: the same code is in the mirror, `custom-pokebot` and 40Cakes `main`.

## 3. `emerald_obtainability.json`: the Sudowoodo note is wrong; two other entries too

- **Sudowoodo (185).** The note says "Route 111 — blocks the path … not in the bot's static_soft_resets seed (a gap to
  add)". That is Gold/Silver/Crystal lore.
  - Emerald: `BattleFrontier_OutsideEast/scripts.inc:113-141` (`setwildbattle SPECIES_SUDOWOODO, 40`), reached with the
    Wailmer Pail. It is post-game (the ferry needs `FLAG_SYS_GAME_CLEAR`) and ONE-SHOT (`FLAG_DEFEATED_SUDOWOODO`).
    It is in 0 wild tables.
  - The bot already has `modes/sudowoodo.py`. Only `note` is wrong; no code acts on it.
- **Meowth (52) is obtainable; the file says "unobtainable".** `meta._ingame_trades` has give and receive swapped.
  - `src/data/trade.h` `[INGAME_TRADE_MEOWTH]` `.species = SPECIES_MEOWTH`, OT "ISIS".
  - `BattleFrontier_Lounge6`: "Would you like to trade me a {STR_VAR_1}…", "A SKITTY is so much cuter".
  - So Isis GIVES Meowth for a Skitty (orchestrator re-checked). This changes reachability: Meowth, and Persian by
    evolution.
  - It breaks the pin at `tests/test_obtainability.py:122`, and `11-LIVINGDEX-DESIGN.md:692-697` repeats the reversal.
- **Chikorita, Cyndaquil and Totodile** carry "No … gift … gives this species". But Birch gives one
  (`LittlerootTown_ProfessorBirchsLab/scripts.inc:329/370/411`), gated on a complete Hoenn dex (`pokedex.c:4387-4397`).
  - `emerald_reachable: false` stays correct under the file's definition; only the kind and note are wrong.
