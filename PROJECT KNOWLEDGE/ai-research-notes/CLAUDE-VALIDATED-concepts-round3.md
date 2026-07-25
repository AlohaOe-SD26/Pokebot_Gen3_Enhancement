# ✅ CLAUDE-VALIDATED — concept notes ROUND 3 (2026-07-25)

**Scope:** `c08` (Mystery Gift / event distribution — priority 1), `c05` (healing items & money
economy — priority 2), the **remainder** of `c02` (ball multipliers + shake maths), and the `c06`
water items round 2 left open (Dive layers, currents).

**Ground truth used this pass.** Rather than fight the GitHub search rate limit, I made a **local
partial clone of the decomp** and grepped/read it directly:

```
git clone --depth 1 --filter=blob:none --no-checkout --single-branch \
    https://github.com/pret/pokeemerald ppe
cd ppe && git sparse-checkout set --no-cone '/src/**' '/data/**' '/include/**' '/*.txt'
git checkout master        # 44 MB, full src/ + data/ + include/
```

This is strictly better than `gh api` for absence claims (I can grep the *whole* tree, not a
sample) and it costs one clone instead of hundreds of API calls. **Recommend this as the default
grounding method from now on.** `ld_script.ld` was fetched separately via `gh api … -H "Accept:
vnd.github.raw"`.

Every ruling below cites a path + line that I opened in that tree. Where I did not open a source,
the ruling is `UNRESOLVED` and says so.

**Version caveat (same as rounds 1–2).** pret `master` has been refactored since retail
(`gSpeciesInfo`, `gTrainerMoneyTable`, `.battleUsage`, `POCKET_*` enums). Symbol *names* may not
match a 2004 disassembly; the *logic, constants and data values* are the retail ones. Where a name
matters for our code I flag it.

**Prefix convention reminder:** our own `modules/data/event_flags/emerald.txt` and
`event_vars/emerald.txt` store names **without** the `FLAG_`/`VAR_` prefix. Every flag/var name
used below was checked against those two files — **28 flags and 8 vars, all present, zero phantoms**
(§6).

---

# ‼ 0. THE ONE-PARAGRAPH ANSWER TO THE DECISIVE QUESTION

**Mew, Deoxys, Lugia, Ho-Oh and the Southern-Island Latias/Latios are UNREACHABLE on a normal
cartridge. Jirachi does not exist in Emerald at all. Do not build a hunt for any of them.**
All four destinations are closed map clusters with **zero map connections and zero warps from
anywhere except the Lilycove Harbor ferry script**, and that script's four branches are each gated
on `checkitem ITEM_<TICKET>` **plus** `FLAG_ENABLE_SHIP_<DEST>`. In the entire ROM those items and
flags are set by exactly **three unreachable RAM scripts** (`data/scripts/gift_*.inc`) and **one
dead special** (`ShouldDistributeEonTicket`, which the decomp itself annotates *"Always returns
FALSE"*). The single non-injection route that exists at all is the **Eon Ticket via Record Mixing
from a Ruby/Sapphire cart that already holds a distributable ticket** — and even the *sender* side
of that chain is unreachable from an Emerald cart, because the Mystery **Event** system that arms it
is disabled in this ROM (§2, §3).

---

# 1. RULINGS

Verdict key: `CONFIRMED` / `REFUTED` / `UNRESOLVED`. "NEW" marks a finding absent from the Gemini
note and behaviour-changing.

## 1a. `c08` — Mystery Gift, event distribution, the tickets (priority 1)

| # | claim | ruling | the actual truth | source I read |
|---|---|---|---|---|
| c08-1 | Mystery Gift is unlocked by entering "LINK TOGETHER WITH ALL" in the Poké Mart questionnaire, setting `FLAG_SYS_MYSTERY_GIFT_ENABLE` | **CONFIRMED, plus a prerequisite the note omits** | The phrase is exactly `{EC_WORD_LINK, EC_WORD_TOGETHER, EC_WORD_WITH, EC_WORD_ALL}`. ‼ **It only works if `FLAG_SYS_POKEDEX_GET` is already set** — `goto_if_unset FLAG_SYS_POKEDEX_GET, Questionnaire_EventScript_ThankYou` silently no-ops otherwise. Also re-entering it once the flag is set is a no-op. | `src/easy_chat.c:693-698` (`sMysteryGiftPhrase`), `:2988-2991` (`DidPlayerInputMysteryGiftPhrase`), `data/scripts/questionnaire.inc:30-41` |
| c08-2 | The Wonder Card lives in `gSaveBlock1Ptr->mysteryGift`, one card + one news at a time | **CONFIRMED (location), REFUTED (the readable field)** | `struct MysteryGiftSave mysteryGift` is at **SaveBlock1 `0x322C`** and holds exactly one `WonderNews` + one `WonderCard` + metadata + `questionnaireWords` + `trainerIds[2][5]`. ‼ **There is no `state` field.** The note's `mysteryGift.state ∈ {0,1,2}` does not exist. Validity is decided by **CRC**: `ValidateSavedWonderCard()` checks `cardCrc != CALC_CRC(card)`, then `ValidateWonderCard()`, then `ValidateSavedRamScript()`. Any bot reader must recompute a CRC, not read a byte. | `include/global.h:925-940, 1066`; `src/mystery_gift.c :: ValidateSavedWonderCard` |
| c08-3 | The attached gift is claimed from the Deliveryman upstairs in a Pokémon Center | **CONFIRMED** | `CableClub_EventScript_MysteryGiftMan` → `trywondercardscript`, which runs `GetSavedRamScriptIfValid()`. The man is shown/hidden by `CableClub_OnTransition` → `CableClub_EventScript_HideOrShowMysteryGiftMan`, i.e. **his presence is itself an observable**: `FLAG_HIDE_POKEMON_CENTER_2F_MYSTERY_GIFT_MAN` is cleared only if `ShouldDistributeEonTicket()` **or** `ValidateSavedWonderCard()` is true. | `data/scripts/cable_club.inc:1-30`; `src/scrcmd.c:2228-2231`; `src/script.c:441-463` |
| c08-4 | "It is impossible to obtain these items via pure gameplay; the ROM has only client-side receiving logic and no payloads" | **CONFIRMED in conclusion, REFUTED in the reasoning — and this matters** | The conclusion is right, but the ROM **does** contain the payload scripts. `data/mystery_gift.s` is linked into the ROM (`ld_script.ld:704 → data/mystery_gift.o(.rodata)`) and `.include`s eight distribution RAM scripts: `gift_stamp_card`, `gift_pichu` (Surfing Pichu egg), `gift_trainer`, `gift_battle_card`, **`gift_aurora_ticket`**, **`gift_mystic_ticket`**, `gift_altering_cave`, **`gift_old_sea_map`**. What is missing is not the script but the **Wonder Card + `ramScript` that dispatches to it**. ‼ **`MysteryGiftScript_AuroraTicket` / `_MysticTicket` / `_OldSeaMap` have ZERO references anywhere in `src/`, `data/` or `include/`** (grepped the whole tree) — they are dead ROM data. Emerald also ships a **server** (`gMysteryGiftServerScript_SendWonderCard`, `src/mystery_gift_scripts.c`), so an Emerald that *has* a card can share it to another Emerald — which still requires one genuine card to exist first. | `data/mystery_gift.s`; `decomp/ld_script.ld:704`; whole-tree grep for `MysteryGiftScript_` |
| c08-5 | e-Reader support for Mystery Gift was stripped from Western Emerald; only Trainer Hill / berry data remains | **CONFIRMED** | `src/ereader_helpers.c` contains **only** Trainer Hill transfer (`ValidateTrainerHillData`, `TryWriteTrainerHill`, `ReadTrainerHillAndValidate`, `EReader_Send/Recv`). No card, no gift, no item path. | `src/ereader_helpers.c:376-560` |
| c08-6 | The Eon Ticket can be obtained via Record Mixing from an RS/Emerald cart that holds a distributable one | **CONFIRMED — and this is the ONLY non-injection route in the game** | `ReceiveGiftItem()`: if the partner's `giftItem` is a **key item** you do not already hold in bag *or* PC, `AddBagItem` it and — `if (*item == ITEM_EON_TICKET) FlagSet(FLAG_ENABLE_SHIP_SOUTHERN_ISLAND)`. It is called for **both** the RS record (`sReceivedRecords->ruby.giftItem`) and the Emerald record (`…->emerald.giftItem`). The sender side is `GetRecordMixingGift()`, which pops one from `gSaveBlock1Ptr->recordMixingGift` (a CRC-checked `{unk0, quantity, itemId}` triple with a **finite quantity that decrements per mix**). ‼ **Only a Mystery *Event* script can arm that triple** (`SetRecordMixingGift`, called solely from `MEScrCmd_setrecordmixinggift`, opcode `0x0b`) — see c08-7. | `src/record_mixing.c:969-987`, `:198, 217, 246, 266, 279`; `src/mystery_event_script.c:135-166, 307` |
| c08-7 | *(not in the note)* | **NEW / CONFIRMED — the Mystery EVENT system is fully unreachable in this Emerald** | Three independent locks, any one of which is fatal: (1) `Task_MainMenuCheckSaveFile` only ever does `tMenuType = HAS_SAVED_GAME; if (IsMysteryGiftEnabled()) tMenuType++;` — it can never reach `HAS_MYSTERY_EVENTS`, and `IsMysteryGiftEnabled()` reads *only* `FLAG_SYS_MYSTERY_GIFT_ENABLE`. The decomp's own header comment: *"the check to enable Mystery Events would normally happen here, but this version of Emerald has them disabled"* and *"Code to start a Mystery Event is present here, but is unreachable in this version."* (2) The questionnaire's Mystery-Event branch is dead: `SetSpecialEasyChatResult` can only ever set `gSpecialVar_0x8004` to **0 or 2**, so `goto_if_eq VAR_0x8004, 1` (→ `setflag FLAG_SYS_MYSTERY_EVENT_ENABLE`) is never taken. (3) `CheckCompatibility()` additionally requires `version & (1 << 9)`. ⇒ **No Emerald cart can ever become an Eon-Ticket distributor.** | `src/main_menu.c:60-62, 96-98, 636-672`; `src/event_data.c:107-110`; `src/easy_chat.c:2965-2977`; `src/mystery_event_script.c:22-50` |
| c08-8 | `VAR_DISTRIBUTE_EON_TICKET` / the in-Center Eon Ticket giver | **NEW / CONFIRMED — dead code, and the decomp says so in two places** | `CableClub_EventScript_DistributeEonTicket` really does `giveitem ITEM_EON_TICKET` + `setflag FLAG_ENABLE_SHIP_SOUTHERN_ISLAND`, but it is guarded by `specialvar ShouldDistributeEonTicket`, whose body is `if (!VarGet(VAR_DISTRIBUTE_EON_TICKET)) return FALSE;` and is labelled **`// Always returns FALSE`**. `VAR_DISTRIBUTE_EON_TICKET` is *written* only by that same script (to 0) — nothing in the ROM ever sets it non-zero. The vars header states it outright: *"This var is read and written, but is always zero. The only way to obtain the Eon Ticket in Emerald is via Record Mixing."* | `data/scripts/cable_club.inc:32-42`; `src/field_specials.c:3629-3636`; `include/constants/vars.h:83` |
| c08-9 | Ticket → flag → destination table (Eon/Southern, Aurora/Birth, Mystic/Navel, Old Sea Map/Faraway); "none reachable any other way" | **CONFIRMED — every cell, plus the gate the note omits** | Harbor script verbatim. ‼ **The whole ferry attendant is additionally gated on `FLAG_SYS_GAME_CLEAR`** (`goto_if_unset FLAG_SYS_GAME_CLEAR, …_FerryUnavailable`) — the event islands are post-Champion **even with a ticket**. Reachability: all four clusters have `connections: null` and only *internal* warps; a whole-tree grep for `MAP_SOUTHERN_ISLAND|MAP_BIRTH_ISLAND|MAP_NAVEL_ROCK|MAP_FARAWAY_ISLAND` outside their own directories yields **only** the six `warp` lines in `LilycoveCity_Harbor/scripts.inc`. No Fly destination, no `setdivewarp`, no `setwarp`. | `data/maps/LilycoveCity_Harbor/scripts.inc:9-13, 54-75, 99-137, 199-274`; `data/maps/{SouthernIsland_*,BirthIsland_*,NavelRock_*,FarawayIsland_*}/map.json` |
| c08-10 | Southern Island gives "the opposite of the roaming choice" + Soul Dew | **CONFIRMED, with the exact level and item** | `call_if_eq VAR_ROAMER_POKEMON, 0, …SetUpLatios` / `call_if_ne …SetUpLatias`, and the battle setter is `seteventmon SPECIES_LATIOS, 50, ITEM_SOUL_DEW` (resp. `LATIAS`). So `VAR_ROAMER_POKEMON == 0` ⇒ roamer is **Latias**, island is **Latios** — consistent with story-round1's "0 = Latias". **Level 50, holding Soul Dew.** | `data/maps/SouthernIsland_Interior/scripts.inc:16-20, 74-76, 104-110` |
| c08-11 | *(levels, not in the note)* | **NEW / CONFIRMED** | Ho-Oh **L70**, Lugia **L70** (`NavelRock_Top/scripts.inc:58`, `NavelRock_Bottom/scripts.inc:54`), Deoxys **L30** (`BirthIsland_Exterior/scripts.inc`), Mew **L30** (`FarawayIsland_Interior/scripts.inc:130`). All via `seteventmon`. | those four files |
| c08-12 | **"Injected Mew/Deoxys never obey; `CalculatePlayerMonObedience` in `src/pokemon.c` checks the fateful bit"** | **CONFIRMED in substance, REFUTED in every name — and the real rule is HARSHER than the note says** | There is **no `CalculatePlayerMonObedience`** anywhere in the tree. The real code is `IsMonDisobedient()` in **`src/battle_util.c:3923`**, using helper **`IsBattlerModernFatefulEncounter()` at `:3913`**, which returns FALSE only for a player-side **Mew or Deoxys** whose `MON_DATA_MODERN_FATEFUL_ENCOUNTER` bit is clear. ‼ **When it returns FALSE the entire obedience block is skipped, so `obedienceLevel` stays 0** — and the two escape hatches (`if (!IsOtherTrainer(...)) return OBEDIENT` and `if (FlagGet(FLAG_BADGE08_GET)) return OBEDIENT`) are *inside* that skipped block. Consequence: an illegal Mew/Deoxys **disobeys forever, at any level, with all eight badges, even when you are its original trainer**. It is also **untradeable** (`trade.c:1577-1582` returns `PARTNER_MON_INVALID`). | `src/battle_util.c:3913-3960`; `src/trade.c:1576-1582` |
| c08-13 | *(who sets the bit — not in the note)* | **NEW / CONFIRMED** | Two writers only: `CreateEventMon()` (`src/pokemon.c:2633-2640`), reached via `CreateEnemyEventMon()` ← the **`seteventmon`** script command; and the **`setmodernfatefulencounter`** script command (`src/scrcmd.c:2211-2218`, used by `gift_pichu.inc`). The decomp notes *"there is no similar command to clear it."* ⇒ **Every legitimately-scripted island legendary (Mew, Deoxys, Lugia, Ho-Oh, Lati@s) is fateful and obedient.** Only a *hand-injected* one is crippled. | `src/pokemon.c:2633-2640, 2773-2788`; `src/scrcmd.c:2210-2226` |
| c08-14 | "Overwriting a Wonder Card permanently loses the unclaimed one" | **CONFIRMED (mechanism), with the exact prompt** | The server script `sServerScript_TossPrompt` fires on `HAS_DIFF_CARD` and asks the client (`CLI_ASK_TOSS`); **FALSE (tossed old) → send new; TRUE (kept old) → cancel new.** So it is not silent — there is a yes/no the bot must answer, and answering "keep" cancels the *incoming* card. `HAS_SAME_CARD` → `sServerScript_HasCard`, no prompt. | `src/mystery_gift_scripts.c` (`sServerScript_TossPrompt`, `_HasCard`, `gMysteryGiftServerScript_SendWonderCard`) |
| c08-15 | "Unsaved receptions are lost; distribution hardware may lock your Trainer ID out" (tagged RECALL) | **UNRESOLVED — and correctly so** | The save-block field `trainerIds[2][5]` exists (`MysteryGiftSave`, 5 ids for battles + 5 for trades) but that is the *card's own* stamp/battle bookkeeping, not a distributor-side lockout. Distributor behaviour is outside the ROM and unverifiable here. Moot anyway given c08-4/c08-7. | `include/global.h:925-940` |
| c08-16 | "Old Sea Map was never released outside Japan" | **UNRESOLVED (historical, not a ROM fact) — but the ROM half is CONFIRMED** | The English item, English text and the full English `MysteryGiftScript_OldSeaMap` are all present in the ROM (`gift_old_sea_map.inc`, English strings). Whether a distribution ever happened in the West is a real-world claim I cannot ground from the decomp. Irrelevant to the ruling: unreachable either way. | `data/scripts/gift_old_sea_map.inc` |
| c08-17 | **Jirachi** | **NEW / CONFIRMED IMPOSSIBLE — nothing to hunt** | Grepped `SPECIES_JIRACHI` across all of `src/` and `data/`. **Zero scripts, zero encounter tables, zero gift paths.** Every hit is passive data: species/name/icon/cry/bard tables, `tmhm_learnsets`, `easy_chat_group_pokemon`, `frontier_util.c:682`'s **banned-species list**, and two "have you caught it" Pokédex reads (`birch_pc.c:68,75`; `match_call.c:2036`). There is no Jirachi event in Emerald at all — it came from the Colosseum Bonus Disc / Channel, i.e. an external GameCube transfer. | whole-tree grep |
| c08-18 | *(the ticket scripts' own idempotency — not in the note)* | **NEW / CONFIRMED** | Each `gift_*.inc` refuses to re-give: Aurora checks `FLAG_RECEIVED_AURORA_TICKET` **or `FLAG_BATTLED_DEOXYS`**; Mystic checks `FLAG_RECEIVED_MYSTIC_TICKET` **or `FLAG_CAUGHT_LUGIA` or `FLAG_CAUGHT_HO_OH`**; Old Sea Map checks `FLAG_RECEIVED_OLD_SEA_MAP` **or `FLAG_CAUGHT_MEW`**. All three fail gracefully on a full **KEY ITEMS** pocket (`checkitemspace` → "bag full" message, no flag set, retryable). | `data/scripts/gift_{aurora_ticket,mystic_ticket,old_sea_map}.inc` |

## 1b. `c05` — healing items, Mart stocks, money economy (priority 2)

| # | claim | ruling | the actual truth | source I read |
|---|---|---|---|---|
| c05-1 | "No dedicated Medicine pocket in Emerald; items live in a 30-slot general Items pocket" | **CONFIRMED** | `BAG_ITEMS_COUNT 30`. Every medicine has `.pocket = POCKET_ITEMS`. Five pockets: **Items 30 / Key Items 30 / Poké Balls 16 / TMHM 64 / Berries 46**; per-slot stack `MAX_BAG_ITEM_CAPACITY 99`, PC `999`. ‼ **Berries have their own 46-slot pocket** — the note's "berries compete with medicine for the 30 slots" is wrong, and this also settles round 1's open "ball-pocket slot/stack limits": **16 slots × 99**. | `include/constants/global.h:51-55`; `include/constants/items.h:451-452`; `src/data/items.h` |
| c05-2 | Healing-item **effects** table | **CONFIRMED for every row, ONE REFUTED** | See §4 for the full verified table. Potion 20, Super 50, Hyper 200, Max/Full Restore full, Revive **half**, Max Revive full, Fresh Water 50, Soda Pop 60, Lemonade 80, Moomoo Milk 100, EnergyPowder 50, Energy Root 200, Heal Powder all-status, Revival Herb full. **REFUTED:** the note says Energy Root/Revival Herb friendship is a vague "negative"; the real bands are **Energy Root −10/−10/−15** and **Revival Herb −15/−15/−20** (worst in the game), EnergyPowder/Heal Powder −5/−5/−10. | `src/data/pokemon/item_effects.h:1-110, 387-405` |
| c05-3 | Healing-item **prices** | **CONFIRMED — every single price in the note is correct** | Potion 300, Super 700, Hyper 1200, Max 2500, Full Restore 3000, Revive 1500, Antidote 100, Parlyz Heal 200, Awakening 250, Burn/Ice Heal 250, Full Heal 600, Fresh Water 200, Soda Pop 300, Lemonade 350, Moomoo Milk 500, EnergyPowder 500, Energy Root 800, Heal Powder 450, Revival Herb 2800. (Also verified: Max Revive 4000, Repel 350 / Super 500 / Max 700, Escape Rope 550.) | `src/data/items.h` (`.price` per entry) |
| c05-4 | **"Primary purchase location"** column | ‼ **REFUTED — six of the rows are wrong, and this is the load-bearing column** | Ground truth in §4b. Specifically: **Potion is NOT sold at "any Mart"** — Mauville, Verdanturf, Lavaridge, Fallarbor, Fortree, Mossdeep and Sootopolis all skip it and start at Super Potion; after Rustboro the *only* Potion sources are Petalburg, Oldale, Rustboro, Slateport and Lilycove 2F. **Hyper Potion is NOT in Fallarbor** (Fallarbor's best heal is Super Potion) — it is Fortree/Mossdeep/Sootopolis/Lilycove-2F/League/Frontier. **Revive is NOT in Fallarbor** — Lavaridge/Fortree/Mossdeep/Sootopolis/Lilycove-2F/League/Frontier. **Full Heal is NOT in Mauville or Lavaridge** — Mossdeep/Sootopolis/Lilycove-2F/League/Frontier. **Max Potion's first source is Sootopolis Mart**, not Lilycove. **Full Restore is sold in exactly three shops, all post-game:** `EverGrandeCity_PokemonLeague_1F`, `BattleFrontier_Mart`, and `TrainerHill_Entrance`'s expanded list (gated `FLAG_SYS_GAME_CLEAR`). **Max Revive is sold nowhere at all** (its only occurrence in `data/maps/` is one hidden item on Route 121). **Moomoo Milk is not purchasable anywhere in the game** — a whole-tree grep finds it only in `items.h`, the icon table, `item_effects.h`, and as **Miltank's wild held item** (`species_info.h:7256`). The "Mt. Chimney specialty" is a **Lava Cookie** (a free gift, `giveitem ITEM_LAVA_COOKIE`), not a milk shop. | all 12 `data/maps/*_Mart/scripts.inc` + `LilycoveCity_DepartmentStore_2F`, `EverGrandeCity_PokemonLeague_1F`, `BattleFrontier_Mart`, `SlateportCity`, `MtChimney`; whole-tree grep for `MOOMOO` |
| c05-5 | "Emerald Marts do not scale with badges; they are static arrays. *Exception*: Petalburg via `FLAG_PETALBURG_MART_EXPANDED_ITEMS` (set after 5th badge), and Lilycove via story flags" | **CONFIRMED in principle, REFUTED in the details — and there are FOUR upgrading shops, not one** | Static arrays: yes. But every upgrade is gated on a **story flag, never on a badge count**: **Oldale** `FLAG_ADVENTURE_STARTED` (set in Birch's Lab, adds only Poké Ball); **Petalburg** `FLAG_PETALBURG_MART_EXPANDED_ITEMS`, set by `Common_EventScript_ReadyPetalburgGymForBattle`, which is `call_if_eq VAR_PETALBURG_GYM_STATE, 6` from the **ON_TRANSITION of the Rustboro / Dewford / Mauville / Lavaridge Gyms** — i.e. it fires when you next walk into one of those four gyms after Norman becomes challengeable, **not on badge 5**; **Rustboro** `FLAG_MET_DEVON_EMPLOYEE` (set on **Route 116**, `Route116/scripts.inc:55`) adds Timer + Repeat Ball; **Trainer Hill Entrance** `FLAG_SYS_GAME_CLEAR` swaps a Super-Potion-tier list for Hyper/Max Potion + Full Restore + Full Heal + Revive. Lilycove Dept. Store has **no** conditional stock at all — its five floors are unconditional. | `data/maps/{OldaleTown,PetalburgCity,RustboroCity}_Mart/scripts.inc`; `data/maps/TrainerHill_Entrance/scripts.inc:240-285`; `data/event_scripts.s:676-679`; `data/maps/Route116/scripts.inc:55`; `data/maps/LittlerootTown_ProfessorBirchsLab/scripts.inc:519` |
| c05-6 | Trainer payout = `gTrainerMoney[class] × level of last mon`; Rich Boy 200, Hiker 40 | **CONFIRMED numerically, REFUTED as a description of the table** | Real symbol is **`gTrainerMoneyTable`** in **`src/battle_main.c:474`** (no `gTrainerMoney` exists), and the values are **per-4**: Rich Boy **50**, Hiker **10**, Lady 50, Champion 50, Elite Four 25, Leader 25, Tuber 1, Swimmer 2. The formula is `moneyReward = 4 × lastMonLevel × moneyMultiplier × tableValue`, and **`BATTLE_TYPE_DOUBLE` inserts an extra ×2** (`BATTLE_TYPE_TWO_OPPONENTS` does not — it instead calls `GetTrainerMoneyToGive` twice and sums). Unlisted classes fall through to the `{0xFF, 5}` sentinel ⇒ ¥20/level. So the note's "Rich Boy = $200/level" is right *as an outcome* (4×50) but anyone who greps for `gTrainerMoney` expecting 200 in the table will not find it. | `src/battle_script_commands.c:5618-5646` (`GetTrainerMoneyToGive`, `Cmd_getmoneyreward`); `src/battle_main.c:474-531` |
| c05-7 | Amulet Coin sets `moneyMultiplier = 2` | **CONFIRMED** | `case HOLD_EFFECT_DOUBLE_PRIZE: gBattleStruct->moneyMultiplier = 2;` (`battle_util.c:3308-3310`), default 1 (`battle_main.c:3118`), and it multiplies **both** the trainer payout and Pay Day (`battle_script_commands.c:7454`). Only `ITEM_AMULET_COIN` carries the hold effect. | `src/battle_util.c:3308-3310`; `src/data/items.h:2315` |
| c05-8 | Pay Day yields `5 × user level`, stackable, Amulet-Coin-doubled, paid at end of battle | **UNRESOLVED (partly)** | I confirmed the payout path — `bonusMoney = gPaydayMoney * gBattleStruct->moneyMultiplier` added at battle end (`battle_script_commands.c:7454`) — but I did **not** open the `Cmd_` that accumulates `gPaydayMoney`, so the `5 × level` coefficient is unverified by me. | `src/battle_script_commands.c:7450-7460` only |
| c05-9 | **Whiteout money loss** — the note's `Base Payout × highest party level`, badge-scaled 8/16/…/120, via `GetWhiteoutMoneyLoss` | ‼ **REFUTED (re-confirming round 1/2 from a fresh read)** | `DoWhiteOut()` is six lines: `RunScriptImmediately(EventScript_WhiteOut); SetMoney(&money, GetMoney(&money) / 2); HealPlayerParty(); Overworld_ResetStateAfterWhiteOut(); SetWarpDestinationToLastHealLocation(); WarpIntoMap();`. **Plain `money / 2`.** No `GetWhiteoutMoneyLoss`, no `GetWhiteoutMoneyPenalty`, no badge table, no level term anywhere in the tree. The FR/LG formula was **not** backported. | `src/overworld.c:358-366` |
| c05-10 | *(the real cost of a whiteout — not in any note)* | ‼ **NEW / CONFIRMED — the most behaviour-changing finding of this pass** | `DoWhiteOut` first runs `EventScript_WhiteOut`, and that script is **not** a no-op: it `call`s `EverGrandeCity_HallOfFame_EventScript_ResetEliteFour`, which **`clearflag`s all four `FLAG_DEFEATED_ELITE_4_{SIDNEY,PHOEBE,GLACIA,DRAKE}` and `setvar VAR_ELITE_4_STATE, 0`**, then falls through to `EventScript_ResetMrBriney` (which relocates Briney by `VAR_BRINEY_LOCATION`). ⇒ **Every whiteout wipes Elite Four progress.** Boss-training-by-whiteout is therefore *only* safe outside the E4 gauntlet; a whiteout on E4 member 3 costs the first two fights as well as half the money. | `src/overworld.c:360`; `data/event_scripts.s:585-593, 628-634` |
| c05-11 | *(field-poison whiteout — not in the note)* | **NEW / CONFIRMED** | A poison-faint whiteout goes through the **same** path: `EventScript_FieldWhiteOut` → `special SetCB2WhiteOut` → `CB2_WhiteOut` → `DoWhiteOut`. Same `money / 2`, same E4 reset. One special case: `call_if_set FLAG_WHITEOUT_TO_LAVARIDGE, EventScript_SetRespawnLavaridgePkmnCenter` (`setrespawn HEAL_LOCATION_LAVARIDGE_TOWN`) — the Mt. Pyre/Magma-era override. Also `AdjustFriendship(..., FRIENDSHIP_EVENT_FAINT_FIELD_PSN)` per poisoned faint. | `data/scripts/field_poison.inc`; `src/overworld.c:1550-1570`; `src/post_battle_event_funcs.c:88-91`; `src/field_poison.c:42-51` |
| c05-12 | In-battle items resolve **before** moves — "you cannot be outsped when using a Potion" | **CONFIRMED, with two additions** | `SetActionsAndBattlersTurnOrder`: `B_ACTION_RUN` is ordered **first of all** (and in a `BATTLE_TYPE_LINK` battle *any* battler's run pre-empts); then a pass that front-loads every `B_ACTION_USE_ITEM` **or `B_ACTION_SWITCH`**; then everything else, which is what gets speed-sorted. ‼ So **switching has the same pre-move priority as an item** — that is the cheap counter-play primitive, not just Potions. In `BATTLE_TYPE_SAFARI` the ordering pass is skipped entirely. | `src/battle_main.c:4756-4835` |
| c05-13 | Trap: "the in-battle healing infinite loop — items go first, so the bot can heal 20 and take 25 forever" | **CONFIRMED as a real risk** | Mechanically sound given c05-12 (items are pre-move but do not prevent the incoming hit). The note's fix (`Heal_Amount > Expected_Enemy_Damage`) is the right shape. No ROM guard exists. | derived from `src/battle_main.c:4817-4834` |
| c05-14 | Trap: "Lavaridge herb items call `ApplyFriendshipModulator` in `ItemUse_Medicine` (`src/item_use.c`)" | **REFUTED (names), CONFIRMED (effect)** | **Neither `ApplyFriendshipModulator` nor `ItemUse_Medicine` exists anywhere in the tree.** Friendship-on-heal is applied inline by the `ITEM5_FRIENDSHIP_{LOW,MID,HIGH}` cases of the big item-effect switch in `src/pokemon.c` (`:4730-4740` macro, `:5274`, `:5414`); the separate event-driven API is **`AdjustFriendship(mon, FRIENDSHIP_EVENT_*)`** at `src/pokemon.c:5914`. Anyone who went looking for the note's two symbols would have found nothing. | `src/pokemon.c:4725-4745, 5270-5280, 5410-5420, 5914` |
| c05-15 | B-section: "Map Healing — bot must **infer** whether the current map has a PokéCenter; typically requires a nav-graph flag" | ‼ **REFUTED — the ROM has an explicit table, and this is exactly what c05 needed** | `src/data/heal_locations.json` → `sHealLocations[]` (`src/heal_location.c:11-38`, `GetHealLocationIndexByMap`) is a **22-entry map+coordinate table**, reproduced in §4c. Respawn is set by the script command **`setrespawn`, in the PokéCenter 1F `ON_TRANSITION`** — i.e. **merely walking into the Center building sets your respawn point; you do not have to talk to the nurse.** Only 23 `setrespawn` sites exist in the whole game (13 Centers + League 1F + Frontier + the truck/Hall-of-Fame bedroom pair + two `SSTidalCorridor` + the Lavaridge poison override). ‼ Note `HEAL_LOCATION_SOUTHERN_ISLAND_EXTERIOR` exists in the table but **has no `setrespawn` caller** — it is unreachable/dead. | `src/data/heal_locations.json`; `src/heal_location.c:11-38`; `data/maps/MauvilleCity_PokemonCenter_1F/scripts.inc:1-9`; whole-tree grep for `setrespawn` |
| c05-16 | *(free out-of-Center heals — not in the note, and the subject of this project's first documented AI error)* | ‼ **NEW / CONFIRMED — the complete list is exactly five NPCs** | `Common_EventScript_OutOfCenterPartyHeal` (`data/event_scripts.s:723-729`) is a **full party heal** (`special HealPlayerParty`) and has exactly **five** call sites: **`Route111_OldLadysRestStop`**, `Route119_WeatherInstitute_1F`, `RustboroCity_DevonCorp_3F`, `SSTidalRooms`, and Mom in `data/scripts/players_house.inc:357`. **The Route 111 Old Lady's Rest Stop is real, ungated, and repeatable** (its script even loops back to "still tired? rest again?"), and it sets `FLAG_LANDMARK_OLD_LADY_REST_SHOP` on map entry — confirming at decomp level the user's memory that the first-round Gemini note "refuted" (`00-READ-THIS-FIRST` §Proof). | `data/event_scripts.s:723-729`; `data/maps/Route111_OldLadysRestStop/scripts.inc:1-30`; whole-tree grep |
| c05-17 | Trap: "the finite economy softlock — trainer money is strictly finite until late-game Match Call farming" | **UNRESOLVED** | The premise (trainers are one-shot) is true, but I did not open `src/match_call.c`, so the rematch-income half is still the round-1 open question. The break-even model itself is a design choice, not a ROM fact. | — |

## 1c. `c02` — the remaining ball maths (priority 3)

Round 1 read `Cmd_handleballthrow` in full and its rulings **all reproduce exactly** on my
independent read of `src/battle_script_commands.c:9905-10053` + `sBallCatchBonuses` at `:841-847`.
I am not re-litigating them; §4a is the completed table. What follows is only what round 1 left
open or did not look at. (Note: **`src/pokeball.c` does not exist** — the ball logic the task
pointed me at lives in `battle_script_commands.c`; `src/pokeball.c` is FRLG/other-project naming.)

| # | claim | ruling | the actual truth | source I read |
|---|---|---|---|---|
| c02-A | Where does `catchRate` come from? | **CONFIRMED / NEW detail** | `catchRate = gSpeciesInfo[gBattleMons[target].species].catchRate` — a **`u8`**, read from the *battle* mon (so a form-changed/transformed target uses its current species). Safari substitutes `gBattleStruct->safariCatchFactor * 1275 / 100`. | `:9932-9935` |
| c02-B | Safari catch factor range | **CONFIRMED** | Initialised `= gSpeciesInfo[enemy species].catchRate * 100 / 1275` (`battle_main.c:3115`); "Go Near" adds `sGoNearCounterToCatchFactor[…]` and **clamps at 20** (`battle_util.c:596-598`) ⇒ reconstructed catchRate ≤ `20*1275/100 = 255`. The displayed factor is the same value shown on the Safari HUD (`battle_interface.c:1352`). | `src/battle_main.c:3115`; `src/battle_util.c:596-598` |
| c02-C | Shake-check maths and RNG cost | **CONFIRMED, with the exact bound** | `odds = Sqrt(Sqrt(16711680 / odds)); odds = 1048560 / odds; for (shakes = 0; shakes < BALL_3_SHAKES_SUCCESS && Random() < odds; shakes++);` `BALL_3_SHAKES_SUCCESS == 4` (enum `BALL_NO_SHAKES=0, BALL_1_SHAKE, BALL_2_SHAKES, BALL_3_SHAKES_FAIL, BALL_3_SHAKES_SUCCESS=4, BALL_TRAINER_BLOCK=5`). ‼ **`Sqrt` is the GBA BIOS syscall `u16 Sqrt(u32)` (`include/gba/syscall.h:20`) — an integer, truncating sqrt, not a float.** Model it as `isqrt`. `Random()` is 16-bit, so at the ceiling `a = 254` you get `b = 65535` ⇒ per-shake pass probability `65535/65536`, i.e. `1 - 2^-16`, never exactly 1. The loop **short-circuits** ⇒ 1 to 4 `Random()` calls per throw. | `:10025-10028`; `include/battle_controllers.h:134-141`; `include/gba/syscall.h:20` |
| c02-D | Trainer battles / the Wally tutorial | **NEW / CONFIRMED** | `BATTLE_TYPE_TRAINER` short-circuits to `BALL_TRAINER_BLOCK` + `BattleScript_TrainerBallBlock` **before any maths and without consuming RNG**; `BATTLE_TYPE_WALLY_TUTORIAL` forces `BALL_3_SHAKES_SUCCESS`. Both bypass the formula entirely — unlike Master Ball, which does not. | `:9915-9926` |
| c02-E | Master Ball bookkeeping | **NEW / CONFIRMED (extra quirk)** | Besides the `sBallCatchBonuses[-1]` underflow round 1 found, Master Ball also **skips the per-ball attempt counter**: `if (gLastUsedItem == ITEM_MASTER_BALL) gBattleResults.usedMasterBall = TRUE; else gBattleResults.catchAttempts[gLastUsedItem - ITEM_ULTRA_BALL]++` — the same `-ITEM_ULTRA_BALL` index, so `catchAttempts` is indexed 0..10 for Ultra..Premier. Safari Ball skips both. | `:9996-10007` |
| c02-F | *(not in any note)* | ‼ **NEW — Timer Ball has a u8 overflow that can produce `odds == 0`** | `u8 ballMultiplier` (declared `:9907`) is assigned `gBattleResults.battleTurnCounter + 10`. `battleTurnCounter` is a **`u8` that saturates at 0xFF** (`battle_main.c:3995-3997`), so at turn **246** the int result 256 truncates to **0** and the `if (ballMultiplier > 40)` clamp never fires. Turn 246 ⇒ multiplier 0 ⇒ `odds = 0` ⇒ `16711680 / odds` is a **divide by zero**; turns 247–255 give multipliers 0.1×–0.9× instead of the capped 4.0×. Practical rule for a bot: **never throw a Timer Ball after turn ~240** — and more generally, a >240-turn stall battle is a state to avoid outright. *(The truncation and the clamp bypass are certain from the code; what the ARM division routine actually does with /0 I did not verify, so I do not claim "it crashes" — only that the input is 0.)* | `:9907, 9971-9975, 10025`; `src/battle_main.c:3995-3997` |
| c02-G | Ball-pocket slot/stack limits (round 1's explicit open item) | **RESOLVED — CONFIRMED** | `BAG_POKEBALLS_COUNT 16` distinct slots, `MAX_BAG_ITEM_CAPACITY 99` per slot ⇒ **16 × 99 = 1584 balls max in the bag**, PC cap 999 per slot. There are exactly 12 ball species, so slot exhaustion is impossible; only the 99 stack cap binds. | `include/constants/global.h:53`; `include/constants/items.h:451-452` |
| c02-H | Ball item IDs are contiguous 1..12 | **CONFIRMED (and load-bearing)** | `MASTER 1, ULTRA 2, GREAT 3, POKE 4, SAFARI 5, NET 6, DIVE 7, NEST 8, REPEAT 9, TIMER 10, LUXURY 11, PREMIER 12`, with a decomp warning that *"several places expect the ball IDs to be first and contiguous (e.g. `gBattlescriptsForBallThrow` and `MON_DATA_POKEBALL`)"*. This is why `gLastUsedItem > ITEM_SAFARI_BALL` works as the "modern ball" test and why Master Ball underflows the bonus table. | `include/constants/items.h:5-22` |

## 1d. `c06` — what round 2 left open on Dive layers and currents (priority 4)

| # | claim | ruling | the actual truth | source I read |
|---|---|---|---|---|
| c06-9′ | "Dive routes are 124, 126, 127, 128" — round 2 marked this **UNRESOLVED** and advised settling it "from map connections (`CONNECTION_DIVE`) rather than from encounter tables" | ‼ **REFUTED — the note undercounts, and round 2's suggested method is itself incomplete** | Enumerating `connections[].direction == "dive"` over all 400+ `map.json` gives **seven** surface routes, not four: **Route 105, 124, 125, 126, 127, 128, 129** (each paired with `Underwater_RouteNNN` via a matching `emerge`). ‼ **But connections are only half the mechanism.** `SetDiveWarp()` falls back to a script-set fixed warp when no connection exists: `if (connection != NULL) SetWarpDestination(...); else { RunOnDiveWarpMapScript(); if (IsDummyWarp(&sFixedDiveWarp)) return FALSE; SetWarpDestinationToDiveWarp(); }`. The `setdivewarp` script command (`SetFixedDiveWarp`) supplies that warp, and there are **16 `setdivewarp` sites**, giving nine dive/emerge pairs that have **no map connection at all** — including **Route 134 → `Underwater_Route134`** (`Route134_OnResume: setdivewarp MAP_UNDERWATER_ROUTE134, 8, 6`), the entrance to the **Sealed Chamber**. A navigator built only from `CONNECTION_DIVE` would conclude the Sealed Chamber is unreachable. Full census in §4d. | all `data/maps/*/map.json`; `src/overworld.c:695-702, 756-782`; whole-tree grep for `setdivewarp`; `data/maps/Route134/scripts.inc:1-7` |
| c06-9″ | *(underwater topology — not in either note)* | **NEW / CONFIRMED** | The underwater layer is **not** a mirror of the surface. Only `Underwater_Route{124,126,127,128}` are joined to each other (124↕126, 126↔127, 127↕128); `Underwater_Route{105,125,129,134}` are **isolated single maps** reachable only by diving on their own surface route. `Underwater_Route{105,125,127,129}` each hold **two warps to `MAP_UNDERWATER_MARINE_CAVE`** (the roaming Kyogre cave, whose own exit warp is `MAP_DYNAMIC`); `Underwater_Route126` → `Underwater_SootopolisCity`; `Underwater_Route128` → `Underwater_SeafloorCavern`; `Underwater_Route134` → `Underwater_SealedChamber`. ⇒ **you cannot swim underwater from one dive spot to an arbitrary other**; treat each underwater island as its own component. | the 14 `Underwater_*` / `AbandonedShip_Underwater*` `map.json` files |
| c06-4′ | Currents (round 2: "existence and input-lock yes, directions unverified") | **UNRESOLVED — deliberately not re-opened** | Story-round1 already settled the naming (`MB_EASTWARD_CURRENT` &c., **not** `MB_CURRENT_*`) and that **no whirlpools exist in Emerald**. I did not open `GetForcedMovementByMetatileBehavior` in `src/field_player_avatar.c` this pass, so the per-route direction map remains open. Cheapest settle: read that one function plus a metatile dump of Routes 130–134. | — (see `CLAUDE-VALIDATED-story-round1.md`) |

---

# 2. ‼ IMPOSSIBLE WITHOUT EVENT DATA — the do-not-attempt list

**Rule: do not write a hunt, a route, a flag check, or a punch-list item for anything in this
table. There is no gameplay sequence that reaches it.**

| target | where it lives | what a normal cart can do | why it is closed |
|---|---|---|---|
| **Mew** (Faraway Island, L30) | `MAP_FARAWAY_ISLAND_ENTRANCE/_INTERIOR` | **nothing** | needs `ITEM_OLD_SEA_MAP` + `FLAG_ENABLE_SHIP_FARAWAY_ISLAND`; both set only by `MysteryGiftScript_OldSeaMap`, which has **zero callers** in the ROM |
| **Deoxys** (Birth Island, L30) | `MAP_BIRTH_ISLAND_HARBOR/_EXTERIOR` | **nothing** | needs `ITEM_AURORA_TICKET` + `FLAG_ENABLE_SHIP_BIRTH_ISLAND`; ditto `MysteryGiftScript_AuroraTicket` |
| **Lugia + Ho-Oh** (Navel Rock, L70 each) | `MAP_NAVEL_ROCK_*` (harbour, 11 down + 4 up floors) | **nothing** | needs `ITEM_MYSTIC_TICKET` + `FLAG_ENABLE_SHIP_NAVEL_ROCK`; ditto `MysteryGiftScript_MysticTicket` |
| **Southern-Island Latias *or* Latios** (L50, holding **Soul Dew**) — the twin *opposite* to `VAR_ROAMER_POKEMON` | `MAP_SOUTHERN_ISLAND_EXTERIOR/_INTERIOR` | **only via Record Mixing with a Ruby/Sapphire cart that already holds a distributable Eon Ticket** — a second physical game, a link cable, and a save that was itself event-fed | `ITEM_EON_TICKET` has one live setter, `ReceiveGiftItem()`; the in-Center giver is behind `ShouldDistributeEonTicket()`, annotated *"Always returns FALSE"* |
| **Soul Dew** | Southern-Island Lati's held item | as above | its only occurrence in `data/` is the two `seteventmon … ITEM_SOUL_DEW` lines |
| **Jirachi** | — | **nothing** | **no script, no encounter table, no gift, no item** anywhere in the ROM; external GameCube transfer only |
| Surfing Pichu (egg, `MOVE_SURF`), Altering Cave wild sets 1–8, the Stamp Card / Battle Card / event Trainer | `data/scripts/gift_*.inc`, in ROM at fixed rodata addresses | **nothing** | same dead-RAM-script class; `VAR_ALTERING_CAVE_WILD_SET` is only ever advanced by `MysteryGiftScript_AlteringCave`, so **Altering Cave is permanently on wild set 0** |
| Becoming an Eon-Ticket **distributor** yourself | `MEScrCmd_setrecordmixinggift` | **nothing** | Mystery **Event** is triple-locked: `HAS_MYSTERY_EVENTS` unreachable in `main_menu.c`, the questionnaire's event branch is dead code, and `CheckCompatibility` gates on `1 << 9` |

**Corollary — three things it IS safe to build:**
1. **The story bot never needs to model any of this.** The four `FLAG_ENABLE_SHIP_*` flags read
   False forever; a `goto_if_set` on them is dead weight, and `CreateLilycoveSSTidalMultichoice`
   will offer only **Slateport** (+ **Battle Frontier** once `FLAG_MET_SCOTT_ON_SS_TIDAL`) + **Exit**
   (`src/script_menu.c:400-500`). So the Lilycove ferry multichoice on a real save has a **fixed,
   short option list** — index 0 = Slateport, and Exit is always last. Good news for a chooser.
2. **A KO'd Mew/Deoxys/Lugia/Ho-Oh is not a loss we can suffer**, so those species can be dropped
   from any "permanently losable legendary" safety table (`c09`) — it shortens the list we must get
   right.
3. **If we ever *do* inject** (explicitly against the project's faithful-gameplay directive, and
   noted here only so the trap is on record): injecting a Mew or Deoxys **without** its
   `MODERN_FATEFUL_ENCOUNTER` bit produces a mon that disobeys **forever, at any level, with 8
   badges, even as its original trainer** (c08-12) and **cannot be traded**. Injecting the ticket +
   flag *is* enough for the ferry, provided `FLAG_SYS_GAME_CLEAR` is set — and the island scripts
   themselves use `seteventmon`, so a legitimately-caught island legendary is fine.

---

# 3. HOW THE MYSTERY-GIFT MACHINERY ACTUALLY FITS TOGETHER

For anyone who has to reason about it again, the whole chain in one place:

```
questionnaire "LINK TOGETHER WITH ALL"  (needs FLAG_SYS_POKEDEX_GET)
      └─> FLAG_SYS_MYSTERY_GIFT_ENABLE            [easy_chat.c:693 / questionnaire.inc:30]
              └─> main menu grows a MYSTERY GIFT row (IsMysteryGiftEnabled)   [main_menu.c:645]
                      └─> wireless link, client script CLI_SAVE_CARD + CLI_SAVE_RAM_SCRIPT
                              └─> SaveBlock1: mysteryGift.card (0x322C) + ramScript (0x3728)
                                      └─> PokeCenter 2F man visible          [cable_club.inc:5-10]
                                              └─> `trywondercardscript`
                                                      └─> GetSavedRamScriptIfValid()  [script.c:441]
                                                            requires: ValidateSavedWonderCard()
                                                                      magic == RAM_SCRIPT_MAGIC
                                                                      mapGroup/mapNum == MAP_UNDEFINED
                                                                      localId == NO_OBJECT
                                                                      checksum matches
                                                      └─> runs the RAM script -> giveitem + setflag
```

* The **`struct RamScript`** is `{u32 checksum; u8 magic; u8 mapGroup; u8 mapNum; u8 localId;
  u8 script[995];}` — so a Wonder Card's payload is capped at **995 bytes** of ordinary script
  bytecode, which is why the in-ROM `gift_*.inc` scripts use the `v`-prefixed relocatable opcodes
  (`setvaddress`, `vgoto_if_set`, `vmessage`, `returnram`).
* **Mystery Gift ≠ Mystery Event.** Gift is the wireless Wonder Card system and it *works*.
  Event is the older link/e-Reader bytecode system with its own 17-opcode table
  (`data/mystery_event_script_cmd_table.s`) — `initramscript`, `setenigmaberry`, `giveribbon`,
  `givenationaldex`, `setrecordmixinggift`, `givepokemon`, `addtrainer`, `enableresetrtc` — and it
  is **disabled in this ROM**. Everything the community associates with "Emerald event
  distribution" that *isn't* a Wonder Card ran through that dead table.
* `ReceiveGiftItem` gate worth remembering if we ever emulate a link: the gift is **refused** if the
  key item is already in the **bag or the PC**, or if `AddBagItem` fails — and `multiplayerId != 0`,
  so the *host* (id 0) never receives.

---

# 4. NUMBERS TABLES — the verified, computable versions

## 4a. Ball multipliers — COMPLETE (all 12 balls)

The full odds calculation, in the ROM's exact evaluation order
(`src/battle_script_commands.c:9987-9994`):

```
catchRate  = gSpeciesInfo[target.species].catchRate            # u8; Safari: safariCatchFactor*1275/100
a          = (catchRate * ballMult10 / 10)                     # <-- INTEGER TRUNCATION HAPPENS HERE
             * (3*maxHP - 2*hp)
             / (3*maxHP)
if sleep or freeze:                      a *= 2                # exact
if poison or burn or paralysis or toxic: a = a * 15 / 10       # INDEPENDENT if, so it STACKS -> x3.0
if a > 254:  caught outright
else:
    b = 1048560 / isqrt(isqrt(16711680 / a))                   # isqrt = GBA BIOS Sqrt(u32)->u16
    shakes = 0; while shakes < 4 and Random16() < b: shakes += 1
    if ITEM_MASTER_BALL: shakes = 4                            # forced AFTER the loop; RNG spent
    caught iff shakes == 4
```

`ballMult10` is the ROM's ×10-scaled integer (`u8`, so mind c02-F):

| ball | id | `ballMult10` | effective ×  | condition | source line |
|---|---|---|---|---|---|
| Master | 1 | *(n/a — `sBallCatchBonuses[-1]`, OOB)* | guaranteed catch, **but the formula and the shake loop still run and consume 1–4 `Random()` calls** | always | `:9984, 10030-10031` |
| Ultra | 2 | 20 | **2.0×** | always | `:841-847` |
| Great | 3 | 15 | **1.5×** | always | `:841-847` |
| Poké | 4 | 10 | **1.0×** | always | `:841-847` |
| Safari | 5 | 15 | **1.5×** | Safari Zone only; also substitutes `catchRate` | `:841-847, 9932-9933` |
| Net | 6 | 30 / 10 | **3.0×** / 1.0× | target is **Water OR Bug** type | `:9941-9946` |
| Dive | 7 | 35 / 10 | **3.5×** / 1.0× | `GetCurrentMapType() == MAP_TYPE_UNDERWATER` — **underwater ONLY**; surfing and fishing get 1.0× | `:9947-9952` |
| Nest | 8 | `max(40−L, 10)` if L<40 else 10 | **`max(40−L,10)/10`** → 3.9× @L1, 3.0× @L10, 2.0× @L20, 1.1× @L29, **1.0× for all L≥30** | target level | `:9953-9964` |
| Repeat | 9 | 30 / 10 | **3.0×** / 1.0× | species already `FLAG_GET_CAUGHT` in the **National** dex numbering | `:9965-9970` |
| Timer | 10 | `min(turns+10, 40)` **(u8!)** | **`(turns+10)/10`**, rational not floored → 1.0× @turn 0, 1.5× @turn 5, 2.0× @turn 10, cap **4.0× at turn 30**. ‼ **0.0× at turn 246** (u8 wrap, → `odds = 0`); 0.1–0.9× turns 247–255 | `gBattleResults.battleTurnCounter` | `:9907, 9971-9975` |
| Luxury | 11 | 10 | **1.0×** | always | `:9976-9979` |
| Premier | 12 | 10 | **1.0×** | always | `:9976-9979` |

**Status multipliers** (`:9991-9994`) — two **independent** `if`s:

| target status | multiplier |
|---|---|
| Sleep **or** Freeze | **×2.0** (exact `odds *= 2`) |
| Poison / Burn / Paralysis / Toxic | **×1.5** (`odds * 15 / 10`, truncating) |
| Sleep **and** any of Poison/Burn/Par/Toxic | **×3.0** — they **stack** |
| none | ×1.0 |

**Things that are NOT in the formula:** Critical Capture (does not exist in Gen 3 — I read the
function end-to-end), any Repeat-Ball level term, any Dive-Ball surfing/fishing bonus, any
Master-Ball early-out before the RNG.

**Policy notes a throw planner must respect:** compute `a` with the `(catchRate × ballMult10 / 10)`
truncation *first*; a trainer battle and the Wally tutorial never reach the maths at all (c02-D);
`b` saturates at 65535 so the per-shake success probability is capped at `1 − 2⁻¹⁶`; and each throw
costs **1–4** RNG advances (short-circuiting), not always 4.

## 4b. Healing items — effect, price, and where you can actually buy it

`price` from `src/data/items.h`; effect from `src/data/pokemon/item_effects.h`; stock from the 12
mart scripts + Lilycove Dept. 2F + League 1F + Frontier Mart, all read this pass.
Cost-per-HP is `price / HP` for a full-value heal.

| item | effect | price | ¥/HP | where it is sold (verified) |
|---|---|---|---|---|
| **Potion** | +20 HP | 300 | 15.0 | Oldale, Petalburg, Rustboro, Slateport, **Lilycove 2F** — *and nowhere else* |
| **Super Potion** | +50 HP | 700 | 14.0 | Petalburg (expanded), Rustboro, Slateport, Mauville, Verdanturf, Lavaridge, Fallarbor, Fortree, Lilycove 2F |
| **Hyper Potion** | +200 HP | 1200 | **6.0** | **Fortree**, Mossdeep, Sootopolis, Lilycove 2F, League 1F, Frontier, Trainer Hill* |
| **Max Potion** | full HP | 2500 | — | **Sootopolis**, Lilycove 2F, League 1F, Frontier, Trainer Hill* |
| **Full Restore** | full HP + all status | 3000 | — | **only** League 1F, Frontier Mart, Trainer Hill* — all post-game |
| **Revive** | revive at **½ max HP** | 1500 | — | **Lavaridge**, Fortree, Mossdeep, Sootopolis, Lilycove 2F, League 1F, Frontier, Trainer Hill* |
| **Max Revive** | revive at full HP | 4000 | — | **not sold anywhere** (one hidden item, Route 121) |
| Antidote | cure poison | 100 | — | Oldale, Petalburg, Rustboro, Slateport, Mauville, Verdanturf, Lavaridge, Fallarbor, Fortree, Lilycove 2F |
| Parlyz Heal | cure paralysis | 200 | — | same as Antidote |
| Awakening | cure sleep | 250 | — | Oldale, Petalburg, Mauville, Verdanturf, Lavaridge, Fallarbor, Fortree, Lilycove 2F |
| Burn Heal | cure burn | 250 | — | Verdanturf, Lavaridge, Lilycove 2F |
| Ice Heal | cure freeze | 250 | — | Verdanturf, Lilycove 2F |
| **Full Heal** | all status | 600 | — | **Mossdeep**, Sootopolis, Lilycove 2F, League 1F, Frontier, Trainer Hill* |
| Fresh Water | +50 HP | 200 | **4.0** | **Lilycove Dept. Store Rooftop vending machine only** (`checkmoney 200`) |
| Soda Pop | +60 HP | 300 | 5.0 | rooftop vending machine (`checkmoney 300`); ×6 free from the Route 109 Seashore House |
| Lemonade | +80 HP | 350 | **4.4** | rooftop vending machine (`checkmoney 350`) |
| Moomoo Milk | +100 HP | 500 | 5.0 | ‼ **NOT PURCHASABLE ANYWHERE.** Miltank's wild held item only |
| EnergyPowder | +50 HP, friendship −5/−5/−10 | 500 | 10.0 | Lavaridge Herb Shop |
| Energy Root | +200 HP, friendship **−10/−10/−15** | 800 | **4.0** | Lavaridge Herb Shop |
| Heal Powder | all status, friendship −5/−5/−10 | 450 | — | Lavaridge Herb Shop |
| Revival Herb | revive full HP, friendship **−15/−15/−20** | 2800 | — | Lavaridge Herb Shop |
| *(non-heal, for the buying policy)* | Repel 350 / Super Repel 500 / Max Repel 700 / Escape Rope 550 | | | |

`*` **Trainer Hill** = `TrainerHill_Entrance`'s *expanded* list, gated on `FLAG_SYS_GAME_CLEAR`;
before game-clear that shop's best heal is Super Potion. Its basic and expanded lists are the only
place `X ACCURACY` + `GUARD SPEC` + the full X-item set sit next to the top-tier heals.

Friendship bands are `[low ≤99, mid 100-199, high ≥200]` — as with `FAINT_LARGE`, **the biggest
penalty lands on the mon you have raised most**.

**Break-even, straight off the table.** The cheapest HP in the game is **Energy Root (¥4.0/HP)**
tied with **Fresh Water (¥4.0/HP)** and **Lemonade (¥4.4/HP)** — but the three cheap drinks are
sold at exactly **one** vending machine (post-Lilycove), and Energy Root costs friendship. In the
mid-game the real floor is **Hyper Potion at ¥6.0/HP from Fortree onward**; before Fortree it is
**Super Potion at ¥14.0/HP**. Potion is the *worst* value in the game at ¥15.0/HP and is also the
one that disappears from the mart list after Slateport. ⇒ the "carry potions" arm of the trade-off
is ~2.3× more expensive before Fortree than after it; a break-even model that uses one flat
¥/HP will be wrong by that factor.

## 4c. Free healing — the complete set

**Respawn points** (`sHealLocations`, `src/data/heal_locations.json`; set by `setrespawn` in each
PokéCenter 1F's **ON_TRANSITION**, so entering the building is enough):

| id | map | x, y |
|---|---|---|
| `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F` / `MAYS_HOUSE_2F` | those maps | 4, 2 |
| `LITTLEROOT_TOWN_BRENDANS_HOUSE` / `MAYS_HOUSE` | `MAP_LITTLEROOT_TOWN` | 5, 9 / 14, 9 |
| `OLDALE_TOWN` | `MAP_OLDALE_TOWN` | 6, 17 |
| `PETALBURG_CITY` | `MAP_PETALBURG_CITY` | 20, 17 |
| `RUSTBORO_CITY` | `MAP_RUSTBORO_CITY` | 16, 39 |
| `DEWFORD_TOWN` | `MAP_DEWFORD_TOWN` | 2, 11 |
| `SLATEPORT_CITY` | `MAP_SLATEPORT_CITY` | 19, 20 |
| `MAUVILLE_CITY` | `MAP_MAUVILLE_CITY` | 22, 6 |
| `VERDANTURF_TOWN` | `MAP_VERDANTURF_TOWN` | 16, 4 |
| `LAVARIDGE_TOWN` | `MAP_LAVARIDGE_TOWN` | 9, 7 |
| `FALLARBOR_TOWN` | `MAP_FALLARBOR_TOWN` | 14, 8 |
| `FORTREE_CITY` | `MAP_FORTREE_CITY` | 5, 7 |
| `LILYCOVE_CITY` | `MAP_LILYCOVE_CITY` | 24, 15 |
| `MOSSDEEP_CITY` | `MAP_MOSSDEEP_CITY` | 28, 17 |
| `SOOTOPOLIS_CITY` | `MAP_SOOTOPOLIS_CITY` | 43, 32 |
| `PACIFIDLOG_TOWN` | `MAP_PACIFIDLOG_TOWN` | 8, 16 |
| `EVER_GRANDE_CITY` | `MAP_EVER_GRANDE_CITY` | 27, 49 |
| `EVER_GRANDE_CITY_POKEMON_LEAGUE` | `MAP_EVER_GRANDE_CITY` | 18, 6 |
| `BATTLE_FRONTIER_OUTSIDE_EAST` | that map | 3, 52 |
| `SOUTHERN_ISLAND_EXTERIOR` | that map | 15, 20 | ‼ **dead — no `setrespawn` caller** |

**Free full heals outside a PokéCenter** — every call site of
`Common_EventScript_OutOfCenterPartyHeal` (`special HealPlayerParty`, `data/event_scripts.s:723`):

| where | notes |
|---|---|
| **`Route111_OldLadysRestStop`** | ungated, **repeatable in a loop** ("still tired? rest again?"); sets `FLAG_LANDMARK_OLD_LADY_REST_SHOP` on entry. This is the NPC the first Gemini round declared nonexistent. |
| `Route119_WeatherInstitute_1F` | after the Aqua raid |
| `RustboroCity_DevonCorp_3F` | Mr. Stone's floor |
| `SSTidalRooms` | on the ferry |
| Mom, `players_house.inc:357` | Littleroot |
| *(plus)* PokéCenter nurses (`data/scripts/pkmn_center_nurse.inc`) and Secret Bases (`data/scripts/secret_base.inc`) | |

**Cost of the alternative (whiteout):** `money / 2` **+ all four Elite-Four flags cleared +
`VAR_ELITE_4_STATE = 0`** + warp to last heal location + Briney relocated. Party is fully healed.
Mid-battle EXP survives (round 1). Field-poison whiteout is identical.

## 4d. Dive / emerge sites — the complete census

**By map connection** (7 pairs — `connections[].direction == "dive"/"emerge"`):
Route **105, 124, 125, 126, 127, 128, 129** ↔ `Underwater_Route105/124/125/126/127/128/129`.

**By `setdivewarp` script command** (9 further pairs, invisible to a connection-only scan):

| from | to | script |
|---|---|---|
| `Route134` | `Underwater_Route134` @ (8,6) | `Route134_OnResume` |
| `Underwater_Route134` | `Route134` @ (60,31) | `Underwater_Route134_OnResume` |
| `SealedChamber_OuterRoom` | `Underwater_SealedChamber` @ (12,44) | ON_RESUME |
| `Underwater_SealedChamber` | `Route134` @ (60,31) **and** `SealedChamber_OuterRoom` @ (10,19) | two sites |
| `SootopolisCity` | `Underwater_SootopolisCity` @ (9,6) | `SootopolisCity/scripts.inc:162` |
| `Underwater_SootopolisCity` | `SootopolisCity` @ (29,53) | ON_RESUME |
| `SeafloorCavern_Entrance` | `Underwater_SeafloorCavern` @ (6,5) | ON_RESUME |
| `Underwater_SeafloorCavern` | `SeafloorCavern_Entrance` @ (10,17) | `…:36` |
| `MarineCave_Entrance` | `Underwater_MarineCave` @ (9,6) | ON_RESUME |
| `Underwater_MarineCave` | `MarineCave_Entrance` @ (10,17) | `…:11` |
| `AbandonedShip_Corridors_B1F` / `_HiddenFloorCorridors` | `AbandonedShip_Underwater1` @ (5,4) | two sites |
| `AbandonedShip_Rooms_B1F` | `AbandonedShip_Underwater2` @ (17,4) | ON_RESUME |
| `AbandonedShip_Underwater1` → `_HiddenFloorCorridors` @ (0,10); `_Underwater2` → `_Rooms_B1F` @ (13,7) | | |

**Underwater connectivity** (why "swim underwater to X" usually fails): only
`Underwater_Route124 ↕ 126 ↔ 127 ↕ 128` are joined. `Underwater_Route105 / 125 / 129 / 134` are
isolated. Marine-Cave entrances are the **two warps each** on `Underwater_Route105/125/127/129`.

---

# 5. SHIPPED-CODE IMPLICATIONS

Nothing in this round contradicts code we have shipped. Four things to keep in mind before the
next commit:

1. **Do not add `FLAG_ENABLE_SHIP_*` handling, ticket checks, or event-island navigation anywhere.**
   They are unreachable (§2). If any doc or punch-list entry implies a Mew / Deoxys / Lugia / Ho-Oh
   / Jirachi / Soul Dew objective, delete it rather than leave it as "someday".
2. **Any Timer Ball throw policy must clamp on turn count**, not just on the 4.0× cap — the u8 wrap
   at turn 246 sends the multiplier to **0** and the odds to `0` (c02-F). More generally, cap stall
   battles well below 240 turns.
3. **Whiteout is no longer a cheap tool inside the Elite Four.** If a boss-training or E4 module
   treats "lose and retry" as costing only half our money, that model is wrong: it also clears
   `DEFEATED_ELITE_4_{SIDNEY,PHOEBE,GLACIA,DRAKE}` and `VAR_ELITE_4_STATE` (c05-10). Any E4
   sequencer that resumes from those flags must re-check them **after** a loss, and the
   "whiteout is the safe abort for a scripted static" rule from round 1 needs the caveat
   *"— except during the E4 gauntlet."*
4. **A "does this map have a PokéCenter?" helper should read the heal-location table**, not infer
   from map type or a hand-kept list (§4c), and it must know that **entering the Center building —
   not talking to the nurse — is what moves the respawn point.** If `modules/map_data.py` keeps its
   own healing-point list, cross-check it against the 22 rows in §4c plus the five free-heal NPCs;
   the Route 111 Old Lady's Rest Stop entry that already exists there is **correct** and now has a
   decomp citation.

*(Not audited: I did not read `sandbox-pokebot` source this pass beyond the two flag/var name
tables, so I make no claim about specific functions there.)*

---

# 6. NAME AUDIT

All checked against `sandbox-pokebot/modules/data/event_flags/emerald.txt` (1164 entries) and
`event_vars/emerald.txt` (256), which store names **without** the `FLAG_`/`VAR_` prefix.
**28 flags + 8 vars checked, 0 phantoms.**

Flags (index in our table): `ENABLE_SHIP_SOUTHERN_ISLAND` 2227, `ENABLE_SHIP_BIRTH_ISLAND` 2261,
`ENABLE_SHIP_FARAWAY_ISLAND` 2262, `ENABLE_SHIP_NAVEL_ROCK` 2272, `SYS_MYSTERY_GIFT_ENABLE` 2267,
`SYS_MYSTERY_EVENT_ENABLE` 2220, `RECEIVED_AURORA_TICKET` 314, `RECEIVED_MYSTIC_TICKET` 315,
`RECEIVED_OLD_SEA_MAP` 316, `SHOWN_EON_TICKET` 430, `SHOWN_AURORA_TICKET` 431,
`SHOWN_MYSTIC_TICKET` 475, `SHOWN_OLD_SEA_MAP` 432, `CAUGHT_MEW` 458, `CAUGHT_LUGIA` 145,
`CAUGHT_HO_OH` 146, `BATTLED_DEOXYS` 429, `DEFEATED_DEOXYS` 428, `DEFEATED_MEW` 455,
`CAUGHT_LATIAS_OR_LATIOS` 457, `PETALBURG_MART_EXPANDED_ITEMS` 296, `MET_DEVON_EMPLOYEE` 287,
`ADVENTURE_STARTED` 116, `LANDMARK_OLD_LADY_REST_SHOP` 2209, `WHITEOUT_TO_LAVARIDGE` 108,
`SYS_GAME_CLEAR` 2148, `DEFEATED_ELITE_4_SIDNEY` 1275, `MET_SCOTT_ON_SS_TIDAL` 464.

Vars: `DISTRIBUTE_EON_TICKET` 63, `ROAMER_POKEMON` 213, `ELITE_4_STATE` 156,
`PETALBURG_GYM_STATE` 133, `ALTERING_CAVE_WILD_SET` 62, `FARAWAY_ISLAND_STEP_COUNTER` 58,
`DEOXYS_ROCK_LEVEL` 53, `SS_TIDAL_STATE` 180.

‼ **Reminder from story-round1 that applies to the new names here:** passing the audit proves a name
is *readable*, not that it is *monotonic*. `VAR_DISTRIBUTE_EON_TICKET` is the extreme case — it
exists, it audits clean, and it is **always 0**. And `EventScript_WhiteOut` `clearflag`s four
`DEFEATED_ELITE_4_*` flags on every whiteout (c05-10), so those four are **non-monotonic** and
belong in that census.

---

# 7. METHOD — grounded vs not, and what blocked me

**Grounded** (read in the local decomp clone this session):
`src/battle_script_commands.c` (`Cmd_handleballthrow` in full, `GetTrainerMoneyToGive`,
`Cmd_getmoneyreward`, `sBallCatchBonuses`), `src/battle_main.c` (`gTrainerMoneyTable`,
`SetActionsAndBattlersTurnOrder`, safari factor init, `battleTurnCounter`),
`src/battle_util.c` (`IsMonDisobedient`, `IsBattlerModernFatefulEncounter`, Amulet Coin, Go-Near),
`src/overworld.c` (`DoWhiteOut`, `CB2_WhiteOut`, `SetDiveWarp`/`SetFixedDiveWarp`),
`src/main_menu.c`, `src/event_data.c`, `src/easy_chat.c`, `src/mystery_gift.c`,
`src/mystery_gift_scripts.c`, `src/mystery_event_script.c`, `src/record_mixing.c`,
`src/script.c`, `src/scrcmd.c`, `src/script_menu.c`, `src/field_specials.c`, `src/pokemon.c`
(`CreateEventMon`, `CreateEnemyEventMon`, friendship/item-effect paths), `src/trade.c`,
`src/heal_location.c`, `src/ereader_helpers.c`, `src/field_poison.c`, `src/util.c` (absence),
`include/global.h`, `include/constants/{global,items,vars,flags}.h`,
`include/battle_controllers.h`, `include/gba/syscall.h`,
`src/data/items.h`, `src/data/pokemon/item_effects.h`, `src/data/heal_locations.json`,
`data/mystery_gift.s`, `data/mystery_event_script_cmd_table.s`, `data/event_scripts.s`,
`data/script_cmd_table.inc`, `data/scripts/{questionnaire,cable_club,field_poison,
gift_aurora_ticket,gift_mystic_ticket,gift_old_sea_map,gift_pichu,gift_altering_cave,
pkmn_center_nurse}.inc`, all 12 `*_Mart/scripts.inc` + `LilycoveCity_DepartmentStore_2F`,
`EverGrandeCity_PokemonLeague_1F`, `BattleFrontier_Mart`, `SlateportCity`,
`data/maps/{LilycoveCity_Harbor,SouthernIsland_Interior,BirthIsland_Exterior,NavelRock_Top,
NavelRock_Bottom,FarawayIsland_Interior,Route111_OldLadysRestStop,Route134,
MauvilleCity_PokemonCenter_1F}/scripts.inc`, every `data/maps/*/map.json` (connections + warps, via
a script), and `ld_script.ld` (fetched via `gh api`).
Repo-side: `sandbox-pokebot/modules/data/event_flags/emerald.txt`, `event_vars/emerald.txt`.

**Absence findings** — the shape `00-READ-THIS-FIRST` flags as most dangerous. Each of these was
established by grepping the **entire** cloned tree (`src/` + `data/` + `include/`), not a sample,
and I name the search so it can be repeated: **zero** references to `MysteryGiftScript_*` outside
their own `.inc`; **zero** occurrences of `CalculatePlayerMonObedience`, `ApplyFriendshipModulator`,
`ItemUse_Medicine`, `GetWhiteoutMoneyLoss`, `GetWhiteoutMoneyPenalty`, `gTrainerMoney`,
`src/pokeball.c`; `SPECIES_JIRACHI` in **no** script or encounter table; `MOOMOO` in **no**
`pokemart` list; **no** warp or connection to any event island outside `LilycoveCity_Harbor`;
`Sqrt` defined **only** as the BIOS syscall.

**What blocked me / left UNRESOLVED, and the cheapest way to close each:**

| open item | why it is open | what settles it |
|---|---|---|
| Pay Day's `5 × level` coefficient (c05-8) | did not open the accumulating `Cmd_` | grep `gPaydayMoney` in `src/battle_script_commands.c` and read the setter |
| Match Call rematch income (c05-17, still open from round 1) | out of scope for the priorities I was given | `src/match_call.c` + the Gabby/Ty scripts |
| Current **directions** per route (c06-4′) | round 2 left it; I chose depth on c08 instead | `GetForcedMovementByMetatileBehavior` in `src/field_player_avatar.c` + a metatile dump of Routes 130–134 |
| What the ARM divide does with `16711680 / 0` (c02-F) | needs an emulator experiment, and five story runs are using the machine | a scratch libmgba run, or just obey the "no Timer Ball past turn 240" rule and never find out |
| Distributor-side Trainer-ID lockout (c08-15) | outside the ROM; unverifiable from any source available to me | nothing in this repo can settle it; moot given §2 |
| Lilycove Dept. 1F / 3F / 4F / 5F stock | not needed for healing/money; 3F is vitamins, 4F is TMs | those `scripts.inc` files if a shopping planner ever needs TMs |

**Two process notes worth carrying forward.**
(a) **Clone, don't search.** The partial clone in the header cost one command and made every
absence claim in this file checkable against the whole tree; the `gh api search/code` route hit a
403 after eight queries. (b) **Round 2's own advice was wrong once**, in the same way Gemini's is:
"settle the dive routes from `CONNECTION_DIVE` rather than encounter tables" would have missed nine
dive sites including the Sealed Chamber, because `setdivewarp` is a second, script-level mechanism
(c06-9′). A validated file is a better *lead* than an unvalidated one, but a *method* suggested in
one is still just a suggestion — check that the mechanism you are enumerating is the only one.
