# 11 — Living-Dex / Hunt Improvements: Deep Design (Punch-list #41–#45)

**Status:** DESIGN ONLY — read-only analysis + this doc. No code, no GUI, no
profile writes were made. Everything below is grounded in the real fork at
`sandbox-pokebot/` with `file:line` citations; anything not directly readable
from code today is explicitly flagged **NEEDS-RESEARCH** or **FUTURE**.
**Date:** 2026-07-19. **ROM of record:** Emerald `BPEE0`.

> **One-line headline:** #43 (opportunistic catching) and #44 (party-ball
> rework) are **buildable now** and cheap; #42 splits into an **easy capability
> gate (buildable now)** and a **hard reachability graph (v2)**; #41
> (obtainability model) is **buildable now for the evolution half**, but its
> static/gift/trade/legendary/roamer half and the "Emerald-unobtainable"
> honesty flag are a **bounded research-list compile**; #45 is a **FUTURE**
> coordination note only.

---

## 0. Ground truth: the data & the code as they actually are

### 0.1 Two species datasets — different indexing (critical)
There are **two** species data files, keyed differently. Getting this wrong
silently corrupts every evolution/family lookup.

| File | Entries | Order / key | Evolution shape | family / evolves_from |
|---|---|---|---|---|
| `modules/data/species.json` | 412 (386 real) | **internal species id** = array position | `{method, method_param:int, target_species:int}` where `target_species` is an **internal id** | **internal ids** |
| `modules/data/generated/pokedex_data.json` | 386 | **national-dex** order | `{method, target:NAME, target_national_dex:int, item:NAME \| parameter:int}` | **names** (`evolves_from`) / list of **names** (`family`) |

- The **live code works in internal ids.** `Species.index` is the internal id;
  `Species.national_dex_number` is the dex number (`modules/pokemon.py:1487`
  `get_species_by_index`, `:1496` `get_species_by_national_dex`).
- `encounter_index` is keyed by **internal id** (`enc.species.index`,
  `encounter_index.py:94`). The cached file `cache/encounter_index_BPEE0.json`
  keys are internal ids.
- `living_dex.owned_indices()` collects **internal ids** (`species.index`,
  `living_dex.py:31`). `Pokedex.owned_species` returns `Species` objects
  (`pokedex.py:44-53`), reading the save's National-Dex-ordered owned bitfield
  (`get_species_by_national_dex(index+1)`), so the *bit* is dex-ordered but the
  returned object's `.index` is internal — consistent with everything else.
- **Phase-2 finding (confirmed, `10-DEX-RESEARCH.md:464`):** in `species.json`
  the `family` / `evolves_from` / `target_species` fields are **internal ids,
  not national-dex numbers**. They coincide for Gen 1/2 but diverge for Hoenn
  (Ralts internal 392 vs national-dex 280). Any evolution logic that treats
  them as dex numbers is wrong for Hoenn.

**Design rule for #41:** do all obtainability logic in **internal ids**, using
`species.json` evolutions (`target_species` is *already* a usable
`get_species_by_index` argument — zero conversion). Use
`generated/pokedex_data.json` only for the human-readable method/item/target
names in UI, converting `target_national_dex` via `get_species_by_national_dex`.
Never mix the two id spaces.

### 0.2 Evolution method vocabulary (exhaustive, both files agree — counts)
Enumerated across all 386 species (identical set in both files):

| method | count | automatable? | note |
|---|---|---|---|
| `level` | 135 | **YES** | level up to `parameter` |
| `item` | 21 | **PARTIAL** | evolution stone; needs the stone in bag + a "use item on party mon" action (not yet a helper) |
| `level_with_friendship` | 7 | slow-YES | raise friendship then level |
| `trade_with_item` | 8 | **NO** | trade holding item (Politoed/Slowking/Steelix/Scizor/Kingdra/Porygon2/Huntail/Gorebyss) |
| `trade` | 4 | **NO** | plain trade (Alakazam/Machamp/Golem/Gengar) |
| `level_with_friendship_during_day` | 1 | RTC-YES | Espeon |
| `level_with_friendship_during_night` | 1 | RTC-YES | Umbreon |
| `level_with_attack_lower_than_defence` | 1 | IV-dependent | Tyrogue→Hitmonchan |
| `level_with_attack_greater_than_defence` | 1 | IV-dependent | Tyrogue→Hitmonlee |
| `level_with_attack_equal_to_defence` | 1 | IV-dependent | Tyrogue→Hitmontop |
| `level_silcoon` | 1 | personality-split | Wurmple→Silcoon |
| `level_cascoon` | 1 | personality-split | Wurmple→Cascoon |
| `level_with_empty_slot_in_party` | 1 | special | Nincada→Shedinja (needs empty slot + a Ball) |
| `level_with_beauty` | 1 | **hard** | Feebas→Milotic (max beauty via blue Pokéblocks) |

So **12 trade lines are the only truly non-automatable evolutions** (4 `trade`
+ 8 `trade_with_item`). Everything `level*` is automatable given the base mon
and enough grinding; `item` is automatable once a "use evolution stone" action
exists (a small future helper); Feebas is the one genuinely painful case.

### 0.3 Obtainability census (computed now from the real index + data)
Classifying all 386 with the **Emerald `BPEE0` encounter-index cache** +
`generated/pokedex_data.json` (`natdex→internal` via `species.json` position):

- **132 species** have ≥1 wild encounter in Emerald's index.
  Location rows by method: Grass 309, Good Rod 151, Surfing 145, Old Rod 105,
  Super Rod 87, Rock Smash 8.
- **149 species** are **evolve-only** (no wild location **and** have
  `evolves_from`) → obtained by evolving a pre-evolution.
- **105 species** are **base-and-not-wild** (no wild location, no
  `evolves_from`) → the "special obtain" bucket: starters, fossils, gifts,
  statics, legendaries, roamers, **and Kanto/Johto species that are simply not
  wild in Emerald at all.**

`132 + 149 + 105 = 386`. ✔

> **CRITICAL HONESTY FINDING.** The 105 bucket **conflates two very different
> things** and the encounter index alone **cannot** tell them apart:
> 1. Species obtainable in Emerald by a *non-wild* mechanism the index doesn't
>    model — static object encounters (e.g. **Sudowoodo** on Route 111,
>    Kyogre/Groudon/Rayquaza/Regis), gift NPCs (Castform, Beldum, one starter,
>    fossils), and the **roamer** (Latias/Latios).
> 2. Species **genuinely unobtainable in Emerald without trading** from
>    FR/LG / Colosseum / XD (most Kanto/Johto lines: Caterpie, Pidgey, Growlithe,
>    Eevee, the Kanto birds, Chikorita/Cyndaquil/Totodile, Unown, the Johto
>    legendary beasts, Mew/Celebi/Jirachi, …).
>
> The current `living_dex.py` treats **all 254** non-wild species (149 evo-only
> + 105 base-non-wild) identically as "skipped: no wild location"
> (`living_dex.py:9-11, 76-77`). That is honest about *this mode's* limits but
> useless as a living-dex plan. Fixing this is the whole point of #41, and the
> static/gift/trade/roamer/unobtainable split is the research work — see §1.

### 0.4 The codebase already contains partial static/gift lists (reuse these)
Two reset modes hard-code Emerald static & gift encounters we can seed #41 from
(they are tuned for shiny-resetting, **not** dex-completeness, so they are
*incomplete* — but a verified starting point):

- **Statics** (`modules/modes/static_soft_resets.py:52-60`): Lugia, Rayquaza,
  Deoxys, Regirock, Regice, Registeel. (RS branch `:61-77` also lists
  Groudon/Kyogre, Latios/Latias, Kecleon — Kecleon/Groudon/Kyogre apply to
  Emerald too but live under the non-emerald branch.)
- **Gifts** (`modules/modes/static_gift_resets.py:49-56`): Castform (×3 tiles),
  Hoenn Fossils, Beldum, Wynaut.
- **Roamer** read-out exists: `modules/roamer.py:148` `get_roamer()` →
  `Roamer.species` (`roamer.py:37`) gives the live roaming species (Latias or
  Latios) and its map (`roamer.py:33`).

These prove the *data can be expressed as `(species, map, coords, method)`
tuples* and give us ~12 verified entries; the research task is completing them.

### 0.5 Save-readable state inventory (what a gate can actually read *now*)
| Capability signal | How to read it | Cite |
|---|---|---|
| Owned/seen species | `get_pokedex().owned_species / .seen_species` | `pokedex.py:44,32` |
| Badges (1–8) | `get_event_flag("BADGE0N_GET")` | flags in `data/event_flags/emerald.txt` (BADGE01_GET=2151 … BADGE08_GET=2158); reader `memory.py:336` |
| Any story event flag/var | `get_event_flag(name)` / `get_event_var(name)` | `memory.py:336,393`; names in `data/event_flags/emerald.txt` |
| Owned HMs (bag) | `get_item_bag().tms_hms` contains HM01–HM08 (item idx 339–346) | `items.py:368,533` |
| Owned rods | `get_item_bag()` has Old/Good/Super Rod (idx 262–264) | `items.py`; `fishing.py:34-45` |
| Party knows a field move | `get_party().first_pokemon_with_move("Surf")` | `pokemon_party.py:79`; pattern used by `fly_to` `higher_level_actions.py:67` |
| Player location | `get_player_location()` | `player.py:291` |
| Roamer present + where | `get_roamer()` | `roamer.py:148` |

Note **`player.py` has NO badge accessor** — badges are event flags, read via
`get_event_flag`. The established precedent is `fly_to`
(`higher_level_actions.py:52-69`): it gates on `get_event_flag("BADGE03_GET")`
**and** `first_pokemon_with_move("Fly")`. #42's capability check should mirror
this exactly.

---

## #41 — OBTAINABILITY MODEL

### Current state
- `living_dex.derive_targets()` builds the run as **only** "all wild-catchable
  species not owned" (`living_dex.py:82-84`, via `_all_wild_species_indices`
  `:41-54`). Custom lists drop any species with `not
  locations_for_species(...)` into `skipped` with reason `"no wild location"`
  (`:76-77`).
- Consequence: **254 of 386 species are unreachable** by the mode — every
  evolution, every gift/static/legendary/roamer, and every trade mon. The mode's
  docstring is explicit that this is by design today (`living_dex.py:9-11`).

### Proposed mechanism (grounded)
Introduce a pure-data **obtainability classifier** — a new module
(`modules/obtainability.py`, say) that, given an internal species id, returns an
`ObtainPlan`:

```
ObtainPlan = {
  species_id: int,
  method: "wild" | "evolve" | "gift" | "static" | "roamer" | "ingame_trade"
          | "trade_only" | "event_only" | "unobtainable_in_emerald",
  # for wild: pull from encounter_index.locations_for_species(id)
  # for evolve: { from_species_id, evo_method, evo_param/item, then: ObtainPlan(from_species_id) }  (recursive)
  # for gift/static/roamer/ingame_trade: { map, coords, note, capability_reqs }
  automatable: bool,
  needs_user: bool,            # e.g. "raise to Lv N then trade manually"
  emerald_reachable: bool,     # false => honestly mark red in the dex
  reason: str,
}
```

**Derivation rules:**
1. **wild** — `encounter_index.locations_for_species(id)` non-empty → plan =
   hunt as today. (132 species; fully derivable now.)
2. **evolve** — species has `evolves_from` (use `species.json` internal-id
   `evolves_from`). Plan = *recursively* obtain the pre-evolution until a
   `wild`/`gift`/`static` base is reached, then apply the evolution `method`:
   - `level*` → automatable (raise to `method_param`, or trigger condition).
   - `item` → automatable **once** a "use evolution stone" helper exists
     (needs stone in bag); until then `needs_user`.
   - `trade` / `trade_with_item` → **not automatable**; plan degrades to
     "obtain + raise the pre-evo, then require a manual trade" (`needs_user`,
     `automatable=false`). 12 lines.
   - `level_with_beauty` (Feebas→Milotic) → `needs_user` (Pokéblock beauty).
   - Wurmple split / Tyrogue IV splits / Nincada→Shedinja → automatable but the
     *which-result* is PV/IV/slot-dependent; note it, don't over-promise.
   (149 evolve-only species; the *chain* is fully derivable now from the data.)
3. **static / gift / roamer / ingame_trade** — **compiled static lists** (see
   Research Gaps). Seed from `static_soft_resets.py` / `static_gift_resets.py` /
   `roamer.py`; complete by research.
4. **trade_only / event_only / unobtainable_in_emerald** — compiled honesty
   list; `emerald_reachable=false`. The dex marks these clearly (e.g. a grey/red
   "not obtainable in Emerald without trading" badge). This is the "true living
   Emerald dex has species you cannot catch" callout the task demands.

**How the living dex USES it:** `next_target_index` (`living_dex.py:137`) and
`derive_targets` (`:57`) consult the classifier. For an **evolve** target, the
mode's actual *hunt target* becomes the recursive **wild/gift/static base**;
after catching/obtaining the base it either (a) evolves automatically if the
method is a supported `level*`/`item`, or (b) marks the target `needs_user` and
advances. `gift`/`static`/`roamer` targets route via `navigate_to_anywhere`
(subject to #42 gating) to the fixed tile, then run a static/gift capture
sub-flow (the reset modes already know these tiles). `trade_only` /
`event_only` / `unobtainable` targets are **surfaced, not silently skipped** —
counted in the dex denominator with an honest "cannot be done in Emerald
alone" status.

### Derivable-now vs research vs future
- **DERIVABLE NOW:** the wild set (132), the full evolution graph + method/param
  for all 149 evolve-only species (from `species.json`), and the automatable/
  not-automatable verdict per evolution method. The recursion to a base is pure
  data.
- **NEEDS-RESEARCH (static lists to compile):** the gift / static / in-game-
  trade / roamer / event-only / Emerald-unobtainable enumerations (see §Research
  Gaps for exact contents + counts). The encounter index **cannot** produce
  these.
- **FUTURE:** a "use evolution stone on party mon" action, a friendship-grind
  loop, an RTC day/night wait for Eevee, and any auto-trade (blocked — needs a
  second game/link; not automatable at all).

### Edge cases
- **Wurmple** yields Silcoon **or** Cascoon by personality value — obtaining
  *both* Beautifly and Dustox needs two Wurmple with opposite PV parity; the
  plan must catch/breed until both branches are covered, not assume one Wurmple
  completes four dex slots.
- **Tyrogue → Hitmonlee/chan/top** splits on Atk vs Def IVs — completing all
  three needs three Tyrogue with the right IV relationships (or manual stat
  manipulation). Flag `needs_user` unless an IV-aware breeder is built.
- **Nincada → Ninjask + Shedinja**: evolving at Lv20 yields Ninjask *and* spawns
  Shedinja **only if** there's an empty party slot **and** a spare Poké Ball
  (`level_with_empty_slot_in_party`). Plan must ensure both.
- **Gender/branch legendaries:** Latias vs Latios is fixed per save (starter-
  choice TV question); the *other* is Eon-Ticket-event-only → `event_only`.
- **Kyogre & Groudon are BOTH catchable in Emerald** (unlike R/S) — the classifier
  must not inherit R/S's single-slot assumption.
- **De-dup vs national-dex:** Unown/Deoxys forms share one dex slot; owned-flag
  is per national-dex bit (`pokedex.py:48-52`) so "owned" is form-agnostic — good.

### Build plan (ordered)
1. Write `obtainability.py` with the wild + full evolution-chain classifier
   (pure data; unit-testable offline). Emit an `ObtainPlan` for all 386.
2. Add the compiled static-list JSON (gift/static/roamer/ingame_trade/
   event_only/unobtainable) — research deliverable — and fold it into the
   classifier.
3. Wire `living_dex.derive_targets` to use classifier categories instead of the
   binary wild/skip; keep wild behavior identical for the 132.
4. Add supported auto-evolution (`level*`) after catching a base; mark the rest
   `needs_user`.
5. (Later) evolution-stone / friendship / RTC helpers.

---

## #42 — REACHABILITY / REQUIREMENT GATING

### Current state
- Before hunting, the mode picks `locations[0]` (best rate) and calls
  `find_encounter_tile` + `navigate_to_anywhere` with **no capability or
  reachability check** (`living_dex_mode.py:82-108`, `hunt_mode.py:57-64`).
- `find_encounter_tile` returns `None` for Rock Smash and can't verify Surf
  access (`encounter_index.py:216-276`): Grass = walkable encounter tile,
  Surfing = a surfable tile (but doesn't check you *can* surf), rods = land tile
  adjacent to water, **Rock Smash / anything else → None** (`:262-276`). When it
  returns `None` the mode skips with "no reachable tile" (`living_dex_mode.py:93`).
- `navigate_to_anywhere` routes **only through the warp graph** and **explicitly
  does not model HM gates**: its docstring says routes requiring Dive, dynamic
  warps, or surf transitions raise a friendly `BotModeError` rather than guess
  (`global_navigation.py:11-13`); it plans legs over warps only
  (`:106-123`). So a target behind a Cut tree / Surf water / Strength boulder /
  Waterfall is *attempted and fails* rather than *pre-judged*.
- Fishing uses whatever rod is **registered** — `fish()` just presses Select
  (`higher_level_actions.py:145-146`); the stock Fishing mode asks the user to
  pick/register a rod (`fishing.py:34-47`). The hunt/living-dex modes call
  `fish(loop=True)` and **assume the correct rod is registered** — they do not
  check that the right rod for *this* species is owned.

### Proposed mechanism (grounded) — split EASY vs HARD

**EASY win (buildable now): per-target capability gate.** Before committing to a
target's chosen location, evaluate `can_attempt(location)`:

- **Method capability:**
  - `Surfing` → require `get_party().first_pokemon_with_move("Surf")` **and**
    the Surf badge (Emerald Balance Badge, `BADGE05_GET`). Mirror `fly_to`'s
    dual check (`higher_level_actions.py:52-69`).
  - `Old/Good/Super Rod` → require the **matching rod** in the bag
    (`get_item_bag().quantity_of(get_item_by_name("Good Rod")) > 0`). Different
    species need different rods — the location's `method` names exactly which
    rod, so this is a precise check.
  - `Rock Smash` → require the Rock Smash move on a party mon (+ Dynamo Badge
    prerequisite for the field move). Today `find_encounter_tile` returns `None`
    for Rock Smash anyway, so this is also where Rock Smash hunting would be
    enabled.
  - `Grass` → no capability needed.
- **If capability is missing:** don't hard-skip permanently — **defer** the
  target with a clear surfaced reason ("needs Surf + Balance Badge",
  "needs Good Rod"), and try the next *reachable* target. When a species has
  multiple locations (`locations_for_species` returns all, best-first
  `encounter_index.py:181-187`), prefer a location whose method the player *can*
  do now (e.g. a Grass slot over a Surf slot) before deferring.
- **Surface the reason:** reuse the existing `context.message` + `_alert`
  channel (`living_dex_mode.py:98-99,151-165`) and the `skipped` list, but with
  a `deferred` status distinct from permanent `skip`, so a later session
  (post-badge) retries it.

**HARD part (v2): true map reachability.** Deciding whether the *tile itself* is
reachable when the path crosses HM-gated terrain (Cut tree, Surf water, Strength
boulder, Waterfall, Dive) requires modeling those gates in the nav graph.
Today's warp graph has **no** notion of them (`global_navigation.py:11-13`). The
tile behaviors needed *are* readable per-tile — `map.py` exposes
`is_surfable` (`:880`), `has_encounters` (`:873`), `collision` (`:865`),
`tile_type` (`:861`), and metatile-behavior constants incl. `CUT_TREE` (0x69),
`ROCK_SMASH_BREAK` (0x68), `Waterfall`, `Dive` (`map.py:1297-1298, 91, 492`) —
but nothing *consumes* them for pathfinding across maps. Full accounting would
require: (a) annotating warp-graph edges / intra-map tiles with the field-move
capability they require, (b) a path planner that only traverses a gated edge if
the corresponding capability is satisfied, and (c) executing the field move
mid-route (surf on/off, cut, smash). That is a substantial navigation project —
**v2**, described here but not designed in detail.

### Derivable-now vs research vs future
- **DERIVABLE NOW:** rod ownership, HM ownership, badge flags, party-move
  presence, roamer presence — all read directly from save (§0.5). The
  capability gate and "defer with reason" flow are pure glue over existing
  readers.
- **NEEDS-RESEARCH (small):** the exact badge prerequisite per field move in
  Emerald (Surf=Balance/Badge5, Rock Smash=Dynamo/Badge3? Strength=Badge?,
  Waterfall=Badge8, Dive=Badge7). These are fixed Emerald facts to confirm
  against a source before hard-coding the flag names.
- **FUTURE (v2):** HM-gated cross-map reachability graph; mid-route field-move
  execution; area/story-flag gating (some areas open only after a story event —
  readable as event flags, but *which* flag gates *which* map is a research map).

### Edge cases
- A species whose *only* location is Surf/Rock-Smash and the player lacks the
  capability → defer, don't skip forever.
- Rod mismatch: species is Super-Rod-only but player has only Old Rod → defer
  (needs Super Rod), even though "a rod" is registered.
- Registered-item clobber: auto-registering a rod for the player overwrites
  their registered Select item — the gate should *check* rod ownership but let
  the existing `fishing`-style register flow (or a confirmation) handle
  registration, to avoid surprising the user.
- Capability can change mid-run (player earns a badge / catches a Surfer between
  targets) — re-evaluate deferred targets at the top of the target loop, not
  once.

---

## #43 — LIVING-DEX OPPORTUNISTIC CATCHING

### Current state
- The catch-intent fires **only for the current single target**:
  `on_battle_started` returns `BattleAction.Catch` **iff** `opponent.species.index
  == self._current_target_index and not is_owned(that)` (`living_dex_mode.py:44-57`).
  Any *other* uncaught species encountered en route falls through to the default
  pipeline (shiny/CCF only) and is **not** caught (`:56-57`).
- Advancement: `run()` sets `_current_target_index = sid`, travels, then spins/
  fishes until `is_owned(sid)` (`living_dex_mode.py:75-118`), records `done`, and
  moves to `next_target_index` (`:120-123, 137-144`). Progress counts owned-or-
  done (`living_dex.py:129-134`).

### Proposed mechanism (grounded)
Keep a target to **drive travel/movement**, but broaden the catch-intent to
**any uncaught species** (the true goal is dex completion):

- **`on_battle_started` change** (`living_dex_mode.py:44-57`): catch if the
  opponent is a species we don't yet own **and** we still want it —
  ```
  opp = encounter.pokemon.species.index
  if not living_dex.is_owned(opp) and living_dex.is_wanted(opp):
      return BattleAction.Catch
  ```
  where `is_wanted` is "in this run's target/plan set and not already `done`."
  Do **not** restrict to `_current_target_index`. Preserve the current
  fall-through so shinies-of-owned-species and custom catch filters still apply
  (the default pipeline still runs when we return `None`).
- **Advancement when a NON-target uncaught species is caught:** in
  `on_battle_ended` (currently a no-op, `living_dex_mode.py:167-168`) mark the
  caught species `done` (it becomes `is_owned` on the next save read anyway —
  `is_owned` reads the live Pokédex, `living_dex.py:37-38`, so this is mostly
  bookkeeping for progress display). **Keep hunting the same driving target** —
  do not abandon travel just because a bonus mon was caught. Only re-evaluate the
  driving target via `next_target_index` when the *driving* target itself becomes
  owned (which the existing `_caught_target` stop-condition already detects,
  `living_dex_mode.py:112-118`).
- **Stop condition subtlety:** today `spin(stop_condition=_caught_target)` stops
  only when the *driving* target is owned (`living_dex_mode.py:112-118`). That is
  actually **fine** for opportunistic catching — bonus catches happen inside the
  spin loop via `on_battle_started`, and the loop keeps going until the driving
  target is done. No change needed to the stop condition; just the catch-intent
  and progress bookkeeping.

### Edge cases (grounded in current guards)
- **Box/party space:** already guarded before each target
  (`_can_fit_pokemon`, `living_dex_mode.py:96-99, 132-139`) and Hunt mode asserts
  after each battle (`hunt_mode.py:36-39`). With opportunistic catching, space
  fills *faster* — add the same fit-check reaction inside the catch path (if full
  when a catchable appears, pause cleanly like the existing "boxes full" stop,
  `living_dex_mode.py:96-100`), so a catch is never lost.
- **Uncatchable encounter (fled/fainted/KO'd):** the species stays un-owned; do
  **not** mark it `done`. `is_owned` is the source of truth (`living_dex.py:37`),
  so a failed catch simply leaves it wanted — it'll be caught on a later
  encounter. Guard against marking `done` on `BattleOutcome != Caught`.
- **Double-catching:** the `not is_owned(opp)` check prevents re-catching a
  species already owned (`is_owned` re-reads the live dex each call). A species
  caught earlier in the same session reads as owned on the next frame, so no
  duplicate intent.
- **Non-target that is *evolve-only*'s base (per #41):** catching a wild base mon
  opportunistically also advances its evolution plan — free progress; the
  classifier should notice the base is now owned.

### Verdict
**Buildable now.** ~15 lines: broaden `on_battle_started`, add `is_wanted` to
`living_dex.py`, and do outcome-gated `done` bookkeeping in `on_battle_ended`.
No new subsystems. This is the highest value-to-effort item.

---

## #44 — PARTY-BALL REWORK (dashboard)

### Current state
- The **Left Party strip** renders each filled slot as a composite: the caught
  ball as a large backdrop with the mon sprite (0.55×) bottom-anchored in front
  (`dashboard_gui.py:1113-1129`, built in `_build_party_icon` `:1086-1130`;
  empty slot = a faded Poké Ball `:1114-1115`). This is the "sizing/legibility"
  problem — the mon is shrunk to fit inside the ball, and small balls (e.g.
  themed balls) fight the sprite for space.
- The **hover tooltip** already shows the ball as **text only**:
  `info_line(f"Held: {held}     Ball: {mon.poke_ball.name}")`
  (`dashboard_gui.py:1475`; also the web overlay line at `:1539`). Tooltip is
  built in `_build_tooltip_body` (`:1408+`), shown by `_show_party_tooltip`
  (`:1343`), sprite via `_tooltip_sprite` (`:1384`).

### Proposed mechanism (exact changes)
1. **Strip: remove the ball composite → clean, sensibly-sized mon sprite.**
   In `_build_party_icon` (`dashboard_gui.py:1086-1130`):
   - Delete the ball-backdrop branch for filled slots (`:1119-1121`).
   - Paste the mon sprite **centered and larger** — replace `mon_box = int(size
     * 0.55)` (`:1113`) with something like `int(size * 0.9)` and center-anchor
     (drop the `anchor="bottom"` used to sit it on the ball, `:1127`).
   - Keep the empty-slot Poké Ball (`:1114-1115`) — that's a fine "empty"
     affordance — and keep the egg branch (`:1116-1117`).
   - The cache key (`:1075`) currently embeds `ball`; once the strip no longer
     draws the ball, **drop `ball` from the strip key** so slots with the same
     mon share a cached icon regardless of ball. (Keep species + shiny.)
2. **Tooltip: add a proper ball ROW (icon + name).** In `_build_tooltip_body`,
   near the existing `Held:`/`Ball:` line (`:1474-1475`):
   - Split the combined line so the ball gets its own row with a **small ball
     icon** + ball name, matching the themed rows. Load the ball image from
     `get_sprites_path()/"items"/f"{ball_name}.png"` (the same asset the strip
     used, `:1091,1120`), thumbnail to ~16–18px, and place it left of a
     `"Caught in: {ball name}"` label using the existing `info_line` styling
     (`:1468-1470`) or a small `Frame` with an image `Label` + text `Label`.
   - Cache the tiny ball icon like `_tooltip_sprite` caches its sprite
     (`:1384-1406`) to avoid reloading per hover.
   - Keep `Held item` on its own line.

### Edge cases
- Ball asset missing → fall back to `Poké Ball.png` (the strip already does this,
  `dashboard_gui.py:1120`); in the tooltip, if even that fails, show the name
  text only (no broken image).
- Egg / empty slots have no ball → tooltip already early-returns for eggs
  (`:1419-1421`) and empty slots (`_show_party_tooltip` guards `is_empty`
  `:1351-1352`); no ball row for those.
- Shiny sprites unaffected — shiny is a separate key/flag (`:1075,1386`); only
  the ball dimension is removed from the strip key.

### Verdict
**Buildable now**, GUI-local, ~2 methods touched (`_build_party_icon` simplify,
`_build_tooltip_body` add a row) + a small ball-icon cache helper. No data or
save changes. (Actual coding is out of scope for this design pass.)

---

## #45 — STORY-MODE INTEGRATION (FUTURE note only)

When the story-mode bot (#24) exists, hunt/living-dex should be able to ask it to
**advance the story** to unlock dex capability (badges → HMs → new areas →
more of the map's encounters and gated legendaries).

**Coordination points (interface #24 should expose; do NOT design the story bot
here):**
- `story.available_instances() -> list[StoryGoal]` — the discrete, automatable
  milestones the story bot can drive to (e.g. "beat Gym N / obtain HMxx /
  unlock Route/area", "make Kyogre/Groudon available", "obtain Surf").
- `story.can_reach(goal) -> bool` and `story.progress_to(goal) -> Generator` —
  so a dex/hunt mode can *invoke* progression as a sub-goal.
- **Consumers:** #42's capability gate maps a deferred target's missing
  capability → the `StoryGoal` that grants it ("target needs Surf" →
  `progress_to(OBTAIN_SURF)`), then retries the target. #41's static/gift plans
  map "requires event/area X unlocked" → a `StoryGoal`.
- **Shared vocabulary:** capabilities should be named identically across #42 and
  #45 (Surf, Cut, RockSmash, Strength, Waterfall, Dive, Badge1..8, area-flags)
  so the gate's "reason" strings are directly resolvable to story goals.

This is a **FUTURE** note: no interface is built now; capturing the seam so #42's
"deferred with reason" data is shaped to be consumable by #24 later.

---

## RESEARCH GAPS — exact static lists to compile (with rough counts)

All of the following are **NOT derivable** from the ROM encounter index and must
be compiled as verified static data (cite each datum against a trusted Gen-3
Emerald source: pokeemerald decomp map scripts / Bulbapedia). Rough counts are
estimates to size the work, not asserted facts.

1. **Emerald gift Pokémon (~8–12).** Starter (Treecko/Torchic/Mudkip — one
   chosen, other two trade-only), the two Hoenn fossils (Lileep, Anorith →
   revived from Root/Claw Fossil), Castform (Weather Institute), Beldum
   (Steven's house), Wynaut (Lavaridge egg), plus any I'm missing (verify).
   *Seed:* `static_gift_resets.py:49-56`.
2. **Emerald static/interactable encounters (~10).** Kyogre, Groudon, Rayquaza,
   Regirock, Regice, Registeel, **Sudowoodo (Route 111)**, Kecleon (Route 119 +
   others), Voltorb/Electrode (if any), Zigzagoon-in-cutscene etc. — verify the
   full set. *Seed:* `static_soft_resets.py:52-77` (statics), but note that list
   is **incomplete** for dex purposes (no Sudowoodo, Kyogre/Groudon under the
   non-Emerald branch).
3. **Roamer (1 per save).** Latias **or** Latios based on starter/TV choice;
   the other is Eon-Ticket-event-only. *Live read exists:* `roamer.py:148`.
4. **Emerald in-game NPC trades (small fixed set, ~4–5).** The handful of
   over-the-counter trades (e.g. the Trade-for-a-species NPCs) — enumerate
   species offered/received + location. **NEEDS-RESEARCH** (no code today).
   These are `needs_user` (require the offered species in party) but *partially*
   automatable: raise the offered mon, then a manual trade completes it.
5. **Event-only legendaries (~6).** Mew, Celebi, Jirachi, Deoxys, Lugia, Ho-Oh —
   obtainable in Emerald **only** via official event distributions / tickets
   (Deoxys/Lugia/Ho-Oh have in-game Mystery-Gift-ticket routes; Mew/Celebi/
   Jirachi are pure event). Mark `event_only`, `emerald_reachable` = conditional.
6. **Emerald-unobtainable-without-trade species (~60–80).** The big honesty list:
   most Kanto/Johto lines with no Emerald wild/static/gift entry (from the 105
   base-non-wild bucket, minus the gifts/statics/legendaries/roamer above, PLUS
   the evolve-only species whose entire family's base is itself unobtainable).
   Examples visible in the census: Caterpie, Weedle, Pidgey, Rattata, Spearow,
   Ekans, Nidoran♀/♂, Growlithe, Poliwag, Bellsprout, Ponyta, Slowpoke, Gastly,
   Onix, Eevee, Chikorita/Cyndaquil/Totodile lines, Unown, the Johto beasts
   (Raikou/Entei/Suicune), Larvitar line, etc. **Each must be verified** — some
   in this bucket are actually obtainable via a static/gift I haven't confirmed
   (e.g. Sudowoodo IS a static), so the list is a *research subtraction*, not the
   raw 105. Mark `unobtainable_in_emerald`, `emerald_reachable=false`.

**Plus one VERIFY item (not a compile):** confirm the encounter-index cache
actually captured **all** Emerald wild tables including the **Safari Zone
National-Dex extension** and any special sub-maps. The census counted **132**
wild species; if the extension areas were not walked by
`get_wild_encounters_for_map` (`encounter_index.py:75-115`), that number is
low and some "unobtainable" species are actually wild. Rebuild the index with a
fully-explored ROM / confirm map coverage before trusting the 132/254 split.

**Also confirm (small):** per-field-move badge prerequisites in Emerald (§#42).

---

## RECOMMENDED BUILD ORDER

1. **#43 opportunistic catching** — buildable now, ~15 lines, highest ROI, no
   dependencies. Ship first.
2. **#44 party-ball rework** — buildable now, GUI-local, independent. Ship in
   parallel with #43.
3. **#42 EASY capability gate** — buildable now (rods/HMs/badges/party-move
   readers all exist). Gate + "defer with reason." Do **after** #43 so the
   opportunistic catcher benefits from smarter target selection. *Confirm the
   per-move badge flags first (small research).*
4. **#41 obtainability classifier — evolution + wild half** — buildable now from
   `species.json`; ship the pure-data classifier and wire evolve-only species
   into the living dex (auto-evolve for `level*`, `needs_user` for trades).
5. **#41 static/gift/roamer/trade/event/unobtainable half** — **blocked on the
   research-list compile** (§Research Gaps 1–6) + the Safari-extension VERIFY.
   Do the compile, then fold into the classifier and surface honest
   "not-in-Emerald" marks.
6. **#42 HARD reachability (v2)** — HM-gated cross-map nav graph +
   mid-route field moves. Large; schedule after 1–5 prove out.
7. **#45 story-mode seam** — FUTURE, gated on #24. Only shape #42's deferred-
   reason data now so it's consumable later.

### Things needing a USER decision
- **Honesty policy:** should Emerald-unobtainable / trade-only / event-only
  species count in the living-dex **denominator** (a true 386 goal, with red
  marks) or be excluded (a "catchable-in-Emerald" goal, ~300-ish)? This changes
  what "100%" means. **Recommend:** show both — full 386 with honest status
  badges, and a separate "obtainable in Emerald" completion %.
- **Manual-trade handling:** for the 12 trade evolutions + in-game trades, does
  the bot **raise-then-pause-for-manual-trade**, or just mark `needs_user` and
  skip? (Auto-trade is genuinely **not automatable** — needs a second game/link.)
- **Rod auto-registration:** may the gate auto-register the correct rod
  (overwriting the player's Select item), or must it ask?
- **Evolution-stone spending:** may the bot consume the player's stones to
  auto-evolve `item`-method species?

### Genuinely NOT automatable (call-outs)
- **Trade & trade-with-item evolutions** (12 lines) and **in-game/link trades**
  — require a second cartridge/link; the bot can raise the mon but a human/second
  system must complete the trade.
- **Event-only legendaries** (Mew/Celebi/Jirachi, and ticket-gated Deoxys/Lugia/
  Ho-Oh) — depend on distributions the bot cannot conjure.
- **Species with no Emerald obtain path at all** — honestly un-completable
  without importing from another game.
