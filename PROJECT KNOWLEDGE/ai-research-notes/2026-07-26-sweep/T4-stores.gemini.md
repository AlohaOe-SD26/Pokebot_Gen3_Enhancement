> # ‼ GEMINI RESEARCH NOTE — NOT A SOURCE OF TRUTH
> Produced 2026-07-26 by `tools/story-dev/gemini_relay.py`. **Recall, not verification.**
> A paired Claude agent is verifying the same topic against the pokeemerald decomp and our
> own codebase; where they disagree, **the decomp/code wins** and this file is wrong.
>
> Per `00-READ-THIS-FIRST.md`, before any claim here is built on:
> * item/flag/species NAMES -> check `modules/data` or the decomp
> * coordinates -> live probe
> * prices/amounts -> `src/data/items.h`
> * mart stock -> `data/maps/<X>_Mart/scripts.inc`
>
> ‼ **GRADE ITS NAMES, NOT ITS ARCHITECTURE.** Measured 2026-07-25: Gemini's symbol/name
> recall is strong; its "your bot should DO x" advice is where it hallucinates. Use this to
> learn WHAT TO LOOK FOR, never to decide what the bot does.

Here is a comprehensive guide to shops, economy, and purchasing routing in **Pokémon Emerald**, specifically tailored for programming an automated story-playing bot.

### 1. Poké Marts & The "Badge Expansion" Misconception
**FLAG - CRITICAL MECHANIC:** Unlike Generation 4 and onwards, **Poké Mart inventories in Gen 3 DO NOT universally expand based on gym badges.** 
In Emerald, shop inventories are geographically fixed. Oldale Town will *never* sell Ultra Balls, even if you have 8 badges. The only "expansions" that occur are event-driven:
*   **Oldale Town:** Sells only Potions/Status heals until May gives you the Pokédex. Then, Poké Balls are added.
*   **Rustboro City:** Adds Repeat Balls and Timer Balls after you deliver the Devon Goods and talk to the Devon Researcher on Route 116. 

To get better items, the bot *must* shop at later-game towns. Here is the fixed stock of key Marts:
*   **Oldale & Petalburg:** Potion, Antidote, Paralyze Heal, Awakening, Repel (Petalburg), Poké Ball.
*   **Rustboro & Dewford:** Super Potion (Rustboro only), Potion, Repel, Escape Rope, Poké Ball. 
*   **Slateport & Mauville:** Super Potion, Great Ball, Repel, standard status heals.
*   **Fallarbor & Lavaridge:** Super Potion, Great Ball, **Super Repel**, Revive (Lavaridge).
*   **Fortree:** **Hyper Potion**, Ultra Ball, Super Repel, Revive.
*   **Mossdeep:** Hyper Potion, Ultra Ball, Net/Dive Balls, **Max Repel**, **Full Heal**.
*   **Sootopolis:** **Max Potion**, Hyper Potion, Ultra Ball, Max Repel, Full Heal, Revive.

### 2. Lilycove Department Store
This is the ultimate mid/late-game shopping hub. 
*   **1F:** Service Counter / Lottery (Ignore for bot).
*   **2F (Basic Items):** 
    *   *Left Cashier:* Poké/Great/Ultra Balls, Escape Rope, Full/Antidote/Paralyze/Burn/Ice Heals, Awakening.
    *   *Right Cashier:* Potion, Super/Hyper/Max Potions, Revive, Repel, Super/Max Repels.
*   **3F (Stat Boosters):** 
    *   *Left Cashier:* X-Items (X Attack, X Defend, etc.), Dire Hit, Guard Spec.
    *   *Right Cashier:* Vitamins (HP Up, Protein, Iron, Carbos, Calcium, Zinc) - 9,800₽ each.
*   **4F (TMs & Bases):** 
    *   *Left Cashier:* TM38 Fire Blast (5,500₽), TM25 Thunder (5,500₽), TM14 Blizzard (5,500₽), TM15 Hyper Beam (7,500₽).
    *   *Right Cashier:* Secret Base Decorations (Ignore).
*   **5F (Furniture):** Dolls, Mats, Cushions (Ignore).
*   **Rooftop:** Vending Machines (Fresh Water, Soda Pop, Lemonade).

**What is worth buying for a bot run?**
*   **2F Right Cashier:** This is your primary stop. The bot should stock up heavily on **Hyper Potions, Revives, and Max Repels** here. 
*   **3F Right Cashier (Vitamins):** **CRITICAL BOT STRATEGY:** Bots tend to white-out (die) and lose half their money. If the bot is holding a lot of cash, program it to dump its money into Vitamins for your carry Pokémon (e.g., Protein for Swampert). This converts liquid cash into permanent stat buffs that cannot be lost on death.
*   **4F TMs:** Only if your bot is programmed with logic to teach Fire Blast/Thunder/Blizzard to a specific Pokémon. Otherwise, ignore.

### 3. Ever Grande City (Pokémon League)
Yes, the Pokémon League building has both a healing center and a shop. It is located in the lobby just before the Elite Four doors.
*   **Inventory:** Ultra Ball, Hyper Potion, Max Potion, **Full Restore** (3,000₽), Full Heal, Revive, Max Repel.
*   *Note:* This is the **only shop in the game** that sells Full Restores. 

### 4. Other Notable Vendors
*   **Lavaridge Herb Shop (CRITICAL FOR BOTS):** Sells Energypowder (500₽ - heals 50HP), Energy Root (800₽ - heals 200HP), Heal Powder (450₽ - cures status), and **Revival Herb** (2,800₽ - acts as a Max Revive). *Note: Herbs lower Pokémon friendship. For a bot, this doesn't matter unless you are using Return. Revival Herbs are insanely cost-effective.*
*   **Slateport Market:**
    *   *Energy Guru:* Sells Vitamins (same as Lilycove 3F). 
    *   *TM Vendor:* TM10 Hidden Power (3,000₽), TM43 Secret Power (3,000₽).
*   **Mauville Game Corner:** Sells TM13 Ice Beam, TM24 Thunderbolt, TM35 Flamethrower. *UNCERTAIN/WARNING for bots: These cost 4,000 Coins (80,000₽). Your bot will likely not have the logic to grind coins, and converting cash to coins is very expensive. Skip these unless you have a dedicated Game Corner bot script.*

### 5. Money & Income
**Main Income Sources:** Trainer battles. You *must* program the bot to talk to Mom after beating Gym 5 (Norman) to receive the **Amulet Coin**. Program the bot to equip this to its lead Pokémon immediately. It doubles prize money. 
Selling Nuggets, Stardust, and Pearls found on the ground also provides boosts.

**Expected Wealth by Gym (Assuming linear path, fighting mandatory/obvious trainers, NO white-outs, Amulet Coin after Gym 5):**
*   **Gym 1 (Roxanne):** ~3,000₽
*   **Gym 2 (Brawly):** ~10,000₽
*   **Gym 3 (Wattson):** ~25,000₽
*   **Gym 4 (Flannery):** ~40,000₽
*   **Gym 5 (Norman):** ~55,000₽ *(Get Amulet Coin!)*
*   **Gym 6 (Winona):** ~110,000₽
*   **Gym 7 (Tate & Liza):** ~180,000₽
*   **Gym 8 (Juan):** ~240,000₽
*   **Elite Four:** ~320,000₽+
*   *FLAG:* Bots are prone to poor decision-making and wiping out. A bot's actual wealth will likely be **half** of this unless you script aggressive pre-boss shopping to drain funds before dying.

### 6. STRATEGY: Automated Restocking & Shopping List
Program your bot to visit specific coordinates (shop counters) before specific story milestones. 

**Stage 1: Pre-Rustboro (Gym 1)**
*   **Location:** Petalburg or Rustboro Mart.
*   **Buy:** 10 Potions. 
*   **Logic:** Keep the starter alive.

**Stage 2: Pre-Mauville (Gym 3)**
*   **Location:** Slateport City Mart.
*   **Buy:** 10-15 Super Potions, 3-5 Paralyze Heals, 10 Repels.
*   **Logic:** Super Potions unlock here. Paralyze Heals are crucial for Wattson (Gym 3). Repels are needed for the upcoming routes.

**Stage 3: Pre-Flannery & Norman (Gyms 4 & 5)**
*   **Location:** Lavaridge Town **Herb Shop** (Not the standard Mart).
*   **Buy:** 10 Revival Herbs, 20 Energy Roots.
*   **Logic:** Energy Roots heal 200HP for 800₽ (Hyper Potions heal 200HP for 1200₽). Revival Herbs act as Max Revives. This is the most economically efficient healing in the game. Dump extra cash into Super Repels at the Lavaridge Mart.

**Stage 4: Pre-Winona (Gym 6) & Team Aqua/Magma Hideouts**
*   **Location:** Fortree City Mart.
*   **Buy:** 20 Hyper Potions, 10 Full Heals.
*   **Logic:** Herbs are great, but the bot won't return to Lavaridge naturally. Fortree introduces standard Hyper Potions.

**Stage 5: Pre-Tate & Liza (Gym 7)**
*   **Location:** Lilycove Department Store (Floor 2).
*   **Buy:** 30 Hyper Potions, 15 Revives, 20 Max Repels.
*   **Cash Dump:** Go to Floor 3. If the bot has more than 20,000₽ remaining, buy Vitamins (Protein/Carbos) and use them on the carry Pokémon immediately. 
*   **Logic:** Tate & Liza are a notorious run-killer. The bot WILL white-out here. Drain the bot's wallet into items so it loses exactly 0₽ when it dies.

**Stage 6: Pre-Elite Four**
*   **Location:** Ever Grande City Pokémon League.
*   **Buy:** Dump **100% of all remaining money**. Buy 30 Full Restores, 30 Revives. Use any leftover change on Full Heals.
*   **Logic:** The bot has no use for money after the credits roll. Maximize survivability.

**A note on Repels for bots:** 
Mathematically, *Super Repels* (200 steps / 500₽ = 2.5₽ per step) are more cost-effective than *Max Repels* (250 steps / 700₽ = 2.8₽ per step). However, Max Repels require the bot to re-apply the item less often, which is slightly easier to program and execute without interruption. Use Super Repels in the mid-game, and switch to Max Repels in Lilycove.