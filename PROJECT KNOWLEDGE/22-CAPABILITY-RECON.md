# Capability recon — healing items and the PC (2026-07-26)

> Decomp + our-codebase verification, paired against the Gemini notes in
> `ai-research-notes/2026-07-26-sweep/`. Where they disagree, this file wins.
> Feeds `#24-provisions`, `#24-items`, `#24-partyvariety`, `#24-pc`.

---

## A. HEALING ITEMS

### A1. ‼ Heal amounts are NOT in `items.h`
`.holdEffectParam` there is only the HOLD effect. The authoritative amount is **byte [6] of
the item-effect array in `src/data/pokemon/item_effects.h`**, dispatched by
`src/pokemon.c:5066-5080`. Anyone reading `items.h` for heal amounts gets the wrong number.

| item | price | heals | ¥/HP |
|---|---|---|---|
| Potion | 300 | +20 | 15.0 |
| Super Potion | 700 | +50 | 14.0 |
| Hyper Potion | 1200 | +200 | **6.0** |
| Max Potion | 2500 | full | — |
| Full Restore | 3000 | full + status | — |
| **Fresh Water** | 200 | +50 | **4.0** |
| Lemonade | 350 | +80 | 4.375 |
| Soda Pop | 300 | +60 | 5.0 |
| Revive | 1500 | revive + **maxHP/2** | — |
| Max Revive | 4000 | revive + full | — |

`ITEM6_HEAL_HP_FULL = (u8)-1`, `HALF = (u8)-2`.

### A2. ‼ The cheap-drinks strategy is real but UNREACHABLE by our machinery
Fresh Water/Lemonade are the cheapest HP in the game — but the **only** seller is the
Lilycove Dept. Store **rooftop vending machine**, which is a `multichoice` script, **not a
`pokemart`**. `buy_in_shop` / `_mart_item_row` cannot drive it; it needs a new script driver.
**Moomoo Milk is not sold anywhere in Emerald** (Miltank held item only). Before Lilycove,
the cheapest mart HP is **Super Potion at 14 ¥/HP**.

### A3. ‼ Mart stock gates on STORY FLAGS, not badge count
**No mart in the game reads a `FLAG_BADGE*`.** Any design that keys shopping off badge count
is wrong. Notables: **Lavaridge is the first Revive seller**; Fortree adds Hyper Potion;
Sootopolis adds Max Potion; **Battle Frontier is the only Full Restore seller**.

### A4. Item use resolves BEFORE all moves
`B_ACTION_USE_ITEM` battlers are placed first in turn order and **explicitly excluded from
the speed sort** (`src/battle_main.c:4816-4834`). So the correct survival test is
**post-heal HP vs one incoming hit**, not pre-heal HP.

### A5. ‼ The buying machinery ALREADY EXISTS and is item-generic
`buy_in_shop(shopping_list)` (`modules/modes/util/higher_level_actions.py:340-434`) is
already generic over items, validates live stock, and **already gates on money** at :385-387.
Its own docstring example is literally `(get_item_by_name("Potion"), 20)`.

Our story fork instead hand-rolls `buy_poke_balls()` (`early_game.py:1925-2014`). The only
Poké-Ball-specific lines are one `_mart_item_row("Poké Ball")` call and the message strings —
the quantity maths (`(money - reserve) // price`) is already item-agnostic. **Minimal change:
parameterise it into `buy_item(name, count, price, mart)`.**

### A6. The in-battle seam is a single line
`DefaultBattleStrategy.decide_turn()` (`modules/battle_strategies/default.py:166-181`): line
:172 currently drops to `_handle_lead_cannot_battle` below `hp_threshold`. **A heal check
inserts immediately before that call.** The plumbing is already proven live:
`TurnAction.use_item_on(item, party_index)` → `battle_action_use_item`, used today by
`catch.py:62`.

### A7. Proposed policy (pure, unit-testable, no emulator)
```
decide_heal(hp, max_hp, opp_max_damage_est, bag, is_trainer, turns_left) -> Item | None
```
1. Heal only if `hp/max_hp <= 0.45`.
2. **Never heal if it dies anyway:** skip if `hp + heal <= opp_max_damage_est` (see A4).
3. **Never overheal:** cheapest item with `heal >= (max_hp - hp) * 0.8`, else the largest.
4. Never heal when a KO is available this turn.
5. Wild, non-trainer, `frac <= 0.20` → prefer flee (existing behaviour).

Stock plan: pre-Gym1 10 Potion (¥3,000) → Gym1-3 10 Super (¥7,000) → Gym4+ 10 Super +
3 Revive (¥11,500, Lavaridge) → Gym6+ 10 Hyper + 5 Revive (¥19,500, Fortree).

---

## B. THE PC / BOXES

### B1. The UI driver is written and has NEVER RUN
All seven `PCAction` factories exist in `modules/modes/util/pc_interaction.py`. Repo-wide,
`interact_with_pc` has **exactly one caller**: `daycare.py:203`, using `release_pokemon_from_party`.
**`withdraw_pokemon_from_box` and `deposit_pokemon_to_box` have no caller anywhere.**

‼ **Those unexercised paths poll `_get_storage_state()` in UNBOUNDED `while` loops**
(:424-433, :466-493, :488-492) with no frame budget — this project's single most common hang
shape. **Budget them before first live use.**

### B2. Menu structure verified correct
Top-level PC order (`data/scripts/pc.inc:10-24`): `0 SOMEONE'S/LANETTE'S PC → 1 PLAYER'S PC →
2 HALL OF FAME (only if game clear) → LOG OFF`. Storage submenu: `WITHDRAW, DEPOSIT, MOVE
POKÉMON, MOVE ITEMS, SEE YA`. Our indices 0/1/2 are right, and our `menu_option_map`
(:381-392) matches the game's in-box menu IDs **exactly**.

### B3. Navigation gap is ~15 lines
The PC tile is **(10,1)** in `PokemonCenter_1F` (decoded: `MB_PC = 0x83`), so the bot stands at
**(10,2) facing Up** — which is what `interact_with_pc` requires. `heal_in_pokemon_center`
already walks into any Centre but hardcodes the nurse tile (7,4). A sibling helper for the PC
tile is the whole navigation gap.

### B4. Game rules that matter
| rule | consequence |
|---|---|
| **14 boxes × 30 = 420** | matches our hardcoded constants |
| Catch with a full party auto-sends to the PC, wrapping through all 14 boxes | the story catch path works today **by omission** — no code reads storage |
| ‼ **You cannot throw a ball at all when party + storage are full** | an all-boxes-full run **silently stops catching with no diagnostic**. Add a guard; the storage read already exists |
| Cannot deposit/move/release the last **alive non-egg** mon; mail-holders refused | our client-side guards at :445-451 mirror this correctly |
| ‼ **NO HM restriction in Emerald** — zero `IsHMMove` references in the storage system | **boxing your only Surf carrier is legal and will soft-lock the run.** This is why `21-TEAM-POLICY-DESIGN.md` §6 forbids randomising HM carriers |

### B5. ‼ A much cheaper alternative exists for one case
`VAR_PC_BOX_TO_SEND_MON` (`src/pokemon.c:4452`) is **settable** — the destination box for an
auto-sent catch can be steered **without ever opening the PC**. If all we want is "put new
catches somewhere sensible", that is near-free compared to a PC trip.

### B6. Cost of a PC trip
**~1,500-2,500 frames (25-40 s at 60 fps)** for a deposit+withdraw visit, because
`interact_with_pc` dispatches by section and so enters the storage system **twice**, paying a
full fade + load each time. **Not measured on hardware — these paths have never run.**
Merging the two entries would bring it to ~1.6× a single operation instead of 2×.

---

## What this changes

1. **`#24-provisions` is cheaper than it looked.** Buying is `buy_in_shop` (already generic,
   already money-gated); in-battle use is one insertion at `default.py:172` on plumbing that
   `catch.py` already proves. The work is the POLICY, not the mechanics.
2. **Do not key shopping off badge count** — mart stock gates on story flags.
3. **Read heal amounts from `item_effects.h`**, never `items.h`.
4. **Before any PC work: bound those `while` loops.** Unexercised unbounded polling is the
   exact shape that has hung this bot before.
5. **Add an all-boxes-full guard to the catch path** — today it fails silently.
6. **Consider `VAR_PC_BOX_TO_SEND_MON` first** — it may remove the need for a PC trip in the
   common case entirely.


---

## C. GROUND AND HIDDEN ITEMS

### C1. ‼ Overworld pickups are SAFE on a full bag — the strand vector is GIFTS
| path | pre-checks space? | on full bag |
|---|---|---|
| Item balls — `finditem` → `Std_FindItem` | **YES** (`checkitemspace`) | "the BAG is full", ball STAYS, flag unset, **retryable** |
| Hidden items — `EventScript_HiddenItemScript` | **YES** | same, `SetHiddenItemFlag` only runs on success |
| **Gifts — `giveitem` → `Std_ObtainItem`** | **NO** | `additem` fails, sets `VAR_RESULT=FALSE`, prints nothing useful — **silent loss** |

So pickup logic does NOT need a bag-space guard. **Gift scenes do.**

### C2. ‼ 38 unchecked `giveitem` sites — and they include EVERY HM
Sites that set a "received" flag immediately after, permanently locking the NPC out. Pocket
caps: Items 30, **Key Items 30**, Poké Balls 16, **TM/HM 64**, Berries 46.

- **TM/HM pocket:** HM_CUT (Rustboro Cutter's House), HM_FLASH (Granite Cave 1F),
  HM_STRENGTH (Rusturf Tunnel), HM_ROCK_SMASH (Mauville House1), HM_SURF (Wally's House),
  HM_FLY (Route 119), HM_DIVE / HM_WATERFALL (Steven's House / Sootopolis).
- **Key Items:** Letter, Devon Goods, Wailmer Pail, all three Rods, **Itemfinder**,
  Basement Key, Coin Case, Go-Goggles, Meteorite, Soot Sack, Powder Jar, Devon Scope,
  SS Ticket, Pokéblock Case, both Bikes, both Fossils, **Magma Emblem**.
- The general **Items pocket has NO unchecked story grant on the path** — the risk is
  concentrated in Key Items and TM/HM.

**Rule for the bot:** keep headroom in Key Items and TM/HM before any scripted gift scene.
Ordinary Potions filling the Items pocket cannot strand a run.

### C3. ‼ The Itemfinder is NOT required to COLLECT a hidden item
`field_control_avatar.c:346-353` checks only `FlagGet(flagId)` — there is no bag check on the
collect path. **Standing adjacent, facing the tile, pressing A works with no Itemfinder.**
The Itemfinder only *detects*. ⇒ the bot can harvest hidden items straight from a coordinate
table, and does not need the Route 110 rival gift first.

Hidden items are `bg_events` of type `hidden_item` (`asm/macros/map.inc:111`), not a script
macro — so they are extractable per map as data.

### C4. Healing / revive items on the current story path
| map | (x,y) | item |
|---|---|---|
| Route102 | 11,15 | Potion |
| Route104 | 5,8 | Potion |
| PetalburgWoods | 4,26 / 4,8 | Paralyze Heal / Ether |
| Route116 | 34,7 / 19,6 | Potion / Ether |
| RusturfTunnel | 30,2 | Max Ether |
| Route109 | 25,6 | Potion |
| Route110 | 6,38 | Elixir |
| **Route117** | **9,1** | **REVIVE** |
| **PetalburgCity** | **19,2** | **MAX REVIVE** |
| Route118 | 69,7 | Hyper Potion |
| Route119 | 33,117 / 3,56 | Hyper Potion ×2 |

Hidden healing on-path: Route104 7,6 Super Potion · 14,55 Potion; Route116 22,9 Super Potion;
**Route109 16,23 REVIVE**; **Route110 35,39 REVIVE** · 37,67 Full Heal; Lavaridge 4,5 Ice Heal;
Route119 26,120 Full Heal.

Also notable: Granite Cave B2F **29,4 Rare Candy**, Route110 26,47 Rare Candy,
Petalburg 11,29 Rare Candy (hidden) — free levels on maps the bot already walks.

**Zero items at all** (verified both lists empty): Route101, Route107, Dewford, Slateport,
Fortree, Weather Institute, Steven's Room.

### C5. What this means for `#24-items`
Do the **visible item balls on the existing path** first: navigate + press A, no bag guard
needed, fully retryable, and it directly feeds `#24-provisions` with free Potions and two
Revives before Gym 5. Hidden items are a second, equally cheap pass — a coordinate table and
the same press, with no Itemfinder prerequisite.


---

## D. SHOPS, HEAL POINTS AND MONEY (decomp-verified)

### D1. Every Poké Center is the SAME layout
`LAYOUT_POKEMON_CENTER_1F` everywhere: **nurse (7,3) → stand (7,4)**;
**PC (10,1) → stand (10,2) facing North**; exit (6-7,8). So one PC-navigation helper works
in every town — no per-town table needed.

### D2. Settlement table (PC door / heal respawn / mart door)
| town | PC door | respawn | mart | notable stock |
|---|---|---|---|---|
| Oldale | (6,16) | (6,17) | (14,6) | +Poké Ball after `FLAG_ADVENTURE_STARTED` |
| Petalburg | (20,16) | (20,17) | (25,12) | +Great Ball, **Super Potion** when expanded |
| Rustboro | (16,38) | (16,39) | (16,45) | Potion, **Super Potion**, balls |
| **Dewford** | (2,10) | (2,11) | — | ‼ **NO MART** |
| Slateport | (19,19) | (19,20) | (13,26) | Super Potion, Great Ball |
| Mauville | (22,5) | (22,6) | (23,14) | Super Potion (no Potion), X-items |
| Verdanturf | (16,3) | (16,4) | (12,3) | Nest Ball, all status heals |
| Fallarbor | (14,7) | (14,8) | (15,15) | Super Potion, Super Repel |
| **Lavaridge** | (9,6)/(9,2) | (9,7) | (15,5) | ‼ **FIRST REVIVE SELLER**; Herb Shop (12,15) |
| **Fortree** | (5,6) | (5,7) | (4,14) | ‼ **FIRST HYPER POTION**, Ultra Ball, Revive |
| Lilycove | (24,14) | (24,15) | Dept (27,6) | see D3 |
| Mossdeep | (28,16) | (28,17) | (37,18) | Hyper Potion, Full Heal, Revive |
| **Sootopolis** | (43,31) | (43,32) | (17,29) | ‼ **MAX POTION**. Mart and PC are on OPPOSITE crater rims — budget the walk |
| Pacifidlog | (8,15) | (8,16) | — | no mart |
| Ever Grande | (27,48) | (27,49) | in League | see D4 |

‼ **Dewford has no mart at all** — the bot must buy before sailing from Rustboro. Directly
relevant to the current Dewford arc work.

### D3. Lilycove Dept Store — 2F-Right is the best HP counter before Mossdeep
2F-Right (10,6): Potion → Super → Hyper → **Max Potion**, **Revive**, all three Repels.
2F-Left (7,6): balls + every status heal. 3F vitamins / X-items. 4F TMs. Elevator (2,1) on
every floor.

### D4. The League has all three, and Victory Road is LESS exposed than its reputation
`EVER_GRANDE_CITY_POKEMON_LEAGUE_1F`: **nurse (3,2)**, **mart clerk (16,2)**, **PC (6,1)**.
The mart sells **FULL RESTORE** — the only pre-Battle-Frontier source. Entry (18,5) → arrive
(9-10,11); E4 door (9-10,1); the guards check only `FLAG_BADGE06_GET`.

### D5. ‼ EXPOSURE — the danger zone is post-Badge-7, NOT Victory Road
| rank | stretch | maps | why it hurts |
|---|---|---|---|
| **1** | **Mossdeep → R127 → R128 → Seafloor Cavern → Sootopolis** | **12** | ‼ Longest in the game. Surf encounters both ways, Aqua grunts, Archie + Kyogre at the end, and **no mart either**. |
| 2 | Lilycove → R121/122 → Mt. Pyre (8 maps) → back | 8 | 5,051 tiles with no exit shortcut |
| 3 | Fallarbor → Meteor Falls → Mt. Chimney → Jagged Pass → Lavaridge | 5+ | Maxie fight; Jagged Pass is one-way down |
| 5 | Ever Grande → Victory Road → League | 3 | **Bounded at BOTH ends** — League 1F has nurse + mart |

**Hard rule for the bot: never enter `MAP_ROUTE127` southbound without a full Revive /
Hyper Potion loadout bought at Mossdeep.**

### D6. Money — the formula and where it comes from
`payout = 4 × (level of the opponent's LAST party mon) × moneyMultiplier × classValue`,
doubled again for a double battle. `moneyMultiplier` is 1 unless an **Amulet Coin** holder has
been **sent out** (it applies on switch-in).

Class values: Champion/Lady/Rich Boy 50 · **Leader / Elite Four 25** · Aqua+Magma Leader 20 ·
Rival 15 · Cooltrainer 12 · Fisherman/Triathlete/Hiker/Admin 10 · Black Belt/Sailor/Bird
Keeper 8 · Battle Girl/Psychic 6 · School Kid/grunts **and the default** 5 · Youngster/Lass 4 ·
Twins 3 · Swimmer 2 · Tuber 1.

‼ **There are NO scripted cash gifts in Hoenn** — no `addmoney` anywhere in `data/`. Income is
trainers, **selling at `price / 2`**, and Pay Day (`level × 5` per use). The Lilycove lottery
pays items only. So trainer battles are effectively the ENTIRE economy, which is a second
independent argument for `#24-gymtrainers`.
Bonus: **buying is halved while the Slateport PokéNews is active** (`price >> IsPokeNewsActive`).

### D7. Restock waypoints per gym
| gym | mart | buy |
|---|---|---|
| 1 Roxanne | Rustboro (16,45) | Potion ×10, balls, Escape Rope (Granite Cave next) |
| 2 Brawly | ‼ **Rustboro BEFORE sailing** — Dewford has none | Super Potion ×10, status heals |
| 3 Wattson | Slateport (13,26) → Mauville (23,14) | Super Potion ×15, X Defend |
| 4 Flannery | Fallarbor → Lavaridge (15,5) + Herb (12,15) | **Burn Heal ×5**, **Revive ×3** |
| 5 Norman | Petalburg (25,12) expanded / Verdanturf | Super Potion, X Special |
| 6 Winona | Fortree (4,14) | **Hyper Potion ×10, Revive ×5** — first Hyper source |
| 7 Tate&Liza | Lilycove Dept 2F-Right → Mossdeep (37,18) | Max Potion + Revive before Mt. Pyre |
| 8 Juan | Mossdeep **before Seafloor Cavern**; Sootopolis after | Hyper/Max ×20, Revive ×8 |
| E4 | **League 1F (16,2)** | Full Restore ×10+, Revive ×10 — last stop |
