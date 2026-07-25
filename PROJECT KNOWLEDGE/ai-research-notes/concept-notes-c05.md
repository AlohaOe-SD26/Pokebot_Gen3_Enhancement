## A. MECHANICS THE ROM ENFORCES

### 1. Healing Item Economy (Emerald)
In Generation 3, items are stored in a 30-slot general `Items` pocket. **VERIFIED**: There is no dedicated `Medicine` pocket in Emerald (introduced in Gen 4).

| Item | Effect | Cost | Primary Purchase Location |
| :--- | :--- | :--- | :--- |
| Potion | +20 HP | $300 | Any Mart |
| Super Potion | +50 HP | $700 | Rustboro (after badge 1), Mauville |
| Hyper Potion | +200 HP | $1200 | Fallarbor, Lilycove Dept. Store |
| Max Potion | 100% HP | $2500 | Lilycove Dept. Store (post-Mossdeep) |
| Full Restore | 100% HP + Status | $3000 | Lilycove Dept. Store (post-Elite 4) |
| Revive | +50% HP (Fainted) | $1500 | Fallarbor, Lilycove Dept. Store |
| Antidote | Clears Poison | $100 | Any Mart |
| Parlyz Heal | Clears Paralysis | $200 | Any Mart |
| Awakening | Clears Sleep | $250 | Any Mart |
| Burn / Ice Heal | Clears Burn / Freeze | $250 | Any Mart |
| Full Heal | Clears All Status | $600 | Mauville, Lavaridge |
| Fresh Water | +50 HP | $200 | Lilycove Vending Machines |
| Soda Pop | +60 HP | $300 | Lilycove Vending Machines |
| Lemonade | +80 HP | $350 | Lilycove Vending Machines |
| Moomoo Milk | +100 HP | $500 | Mt. Chimney (Single purchases only) |
| EnergyPowder | +50 HP (Bitter) | $500 | Herb Shop (Lavaridge) |
| Energy Root | +200 HP (Bitter) | $800 | Herb Shop (Lavaridge) |
| Heal Powder | All Status (Bitter) | $450 | Herb Shop (Lavaridge) |
| Revival Herb | 100% HP (Fainted, Bitter)| $2800 | Herb Shop (Lavaridge) |

**Mart Inventories**: **VERIFIED** (`data/maps/*/scripts.inc`). Unlike Gen 8+, Emerald Marts do **not** globally scale with badges. They have statically defined arrays (e.g., `MauvilleCity_Mart_Pokemart`). 
*Exception*: Petalburg City updates via `FLAG_PETALBURG_MART_EXPANDED_ITEMS` (set after 5th badge), and Lilycove expands via story flags.

### 2. Money Economy
*   **Trainer Payouts**: **VERIFIED** (`src/battle_message.c`). Formula: `Base Rate * Level of last Pokémon in opponent's party`. Base rates are defined per Trainer Class in `gTrainerMoney` (e.g., Rich Boy = $200, Hiker = $40). 
*   **Whiteout Loss Formula**: **VERIFIED** (`src/battle_main.c` `GetWhiteoutMoneyLoss`). 
    *   *R/S vs Emerald Difference*: Ruby/Sapphire blindly halved your money. Emerald backported the FireRed/LeafGreen formula.
    *   Formula: `Base Payout * Highest level in Player's party`.
    *   Base Payout scales by Badges: 0 badges = 8, 1 badge = 16, 2 = 24, 3 = 36, 4 = 48, 5 = 64, 6 = 80, 7 = 100, 8 = 120.
    *   Loss is capped at your current money (cannot go negative).
*   **Amulet Coin**: **VERIFIED** (`ITEM_AMULET_COIN`). If a Pokémon holding this enters battle, `gBattleStruct->moneyMultiplier` is set to 2.
*   **Pay Day**: **VERIFIED** (`MOVE_PAY_DAY`). Yields `$5 * User Level` per cast. Stackable. Subject to Amulet Coin doubling. Added to wallet at end of battle.

### 3. In-Battle Item Use Rules
*   **Priority**: **VERIFIED** (`src/battle_main.c`). The action selection phase resolves item usage (`ACTION_USE_ITEM`) *before* move execution (`ACTION_USE_MOVE`). You cannot be outsped when using a Potion.
*   **Turn Consumption**: Takes the entire turn for that Pokémon. In double battles, the other Pokémon still executes its selected action.

## B. WHAT THE BOT CAN OBSERVE

| State | Memory Location / Struct | Readability |
| :--- | :--- | :--- |
| Current Money | `gSaveBlock1Ptr->money` | Direct Read (u32, cap 999,999) |
| Inventory | `gSaveBlock1Ptr->bagPocket_Items` | Direct Read (Array of `ItemSlot` structs) |
| Active Status | `gPlayerParty[i].status` | Direct Read (Bitmask: SLP, PSN, BRN, FRZ, PRZ) |
| HP Deficit | `maxHP - hp` in `gPlayerParty` | Direct Read (u16) |
| Map Healing | Map Header `mapType` | **UNSURE**: Bot must infer if current map has a PokeCenter. Typically requires a nav-graph flag. |

## C. OPTION SPACE: THE BREAK-EVEN ANALYSIS

To decide between Walking to a Free Heal vs Using/Buying a Potion, the bot calculates Expected Cost.
`Cost_Walk = (Steps_To_Center / Steps_Per_Encounter) * Avg_Escape_Damage + Whiteout_Risk_Cost`
`Cost_Potion = HP_Deficit * Cost_Per_HP (e.g., $15/HP for standard Potion)`

### Strategy 1: Center-Bound Pacifist (Free Heals Only)
*   **Mechanic**: Bot memorizes PC locations. Whenever `Party_HP < Safety_Threshold`, it walks back.
*   **Cost**: Time, and minor HP drain from fleeing wild encounters on the way back.
*   **Failure Mode**: "Event Horizon" Softlock. If the expected damage taken walking back exceeds current party HP, the bot enters a guaranteed whiteout.
*   **Detection**: Graph search distance * wild encounter rate * average damage taken from failing to flee > total remaining HP.

### Strategy 2: Consumable Thresholding (Just-in-Time Healing)
*   **Mechanic**: Bot buys Potions to maintain a fixed inventory (e.g., 10 Potions), using them out-of-battle when `maxHP - hp >= Potion_Value`.
*   **Cost**: Hard drain on the finite money pool. Trainer battles are generally non-repeatable until post-game or arbitrary Match Calls.
*   **Failure Mode**: Bankruptcy. The bot drains its finite cash on Potions, runs out, hits the Event Horizon, and repeatedly whiteouts.
*   **Detection**: `gSaveBlock1Ptr->money` drops below the cost of 1 Potion AND `bagPocket_Items` lacks healing items. 

### Strategy 3: The "Pay Day / Berry" Loop
*   **Mechanic**: Bot acquires a Meowth/Skitty (Pay Day) or farms Oran Berries to generate infinite healing resources.
*   **Cost**: Extremely high time cost, requires complex navigation to berry patches or grinding low-level wild mons with Pay Day.
*   **Failure Mode**: Getting locked into farming routines instead of progressing the story.
*   **Detection**: Track `Story_Flags_Set / Time`. If derivative is 0 for X hours, abort loop.

## D. TRAPS

### 1. The Finite Economy Softlock
Trainer money is strictly finite until late-game Match Call farming. If the bot plays poorly (taking unnecessary damage) and masks it by spamming purchased Potions, it will permanently exhaust the save file's available cash pool. 
*   **Result**: Unable to buy Repels or mandatory story items (like Harbor Mail, though usually cheap, $0 means $0).

### 2. The In-Battle Healing Infinite Loop
Because items go first, the bot uses a Potion to heal 20 HP. The enemy attacks and deals 25 damage. Net HP change is -5. 
*   **Result**: The bot loops Potion usage until inventory is empty, wasting cash and still losing the battle. 
*   **Fix**: Bot logic must require `Heal_Amount > Expected_Enemy_Damage` to justify in-battle item use.

### 3. Friendship Evolution Sabotage (The Bitter Trap)
Lavaridge Herb Shop items (Energy Root, Revival Herb) are hyper-efficient on a Cost-per-HP basis ($800 for 200HP vs $1200 for 200HP Hyper Potion).
*   **The Trap**: **VERIFIED** (`ItemUse_Medicine` in `src/item_use.c`). These items trigger `ApplyFriendshipModulator` with negative values. 
*   **Result**: If the bot buys these for efficiency and uses them on Zubat, Marill, or Togepi, their Friendship will plummet to 0, permanently delaying their evolutions, leaving the bot with under-statted Pokémon for the late game.

### 4. 30-Slot Inventory Overflow
Emerald's main `Items` pocket has exactly 30 slots. Medicine, held items, evolution stones, and repels all compete for this space. 
*   **The Trap**: If the bot picks up every random item (X Attack, Antidotes, assorted loot), the pocket fills. 
*   **Result**: The bot fails to purchase Potions when required ("Your bag is full"), or fails to receive critical held items from NPCs (like EXP Share or Amulet Coin). 
*   **Fix**: The bot must have a subroutine to actively `TOSS` or `SELL` useless items (like X Items or Mail) to maintain free slots.