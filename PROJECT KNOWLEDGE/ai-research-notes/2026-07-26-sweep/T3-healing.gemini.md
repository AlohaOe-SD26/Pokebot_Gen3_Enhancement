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

Here is a comprehensive guide to healing items, mechanics, and bot strategies specifically tailored for **Pokémon Emerald (Generation 3)**.

---

### 1. Full List of Healing Items in Emerald

*Note: In Gen 3, Sitrus Berries heal a flat 30 HP, NOT 25% of max HP like in Gen 4+. This is a crucial distinction for bot programming.*

**HP-Healing Items**
*   **Potion:** 20 HP (Buyable)
*   **Super Potion:** 50 HP (Buyable)
*   **Hyper Potion:** 200 HP (Buyable)
*   **Max Potion:** 100% HP (Buyable)
*   **Full Restore:** 100% HP + All Status (Buyable)
*   **Fresh Water:** 50 HP (Buyable - Vending Machine)
*   **Soda Pop:** 60 HP (Buyable - Vending Machine)
*   **Lemonade:** 80 HP (Buyable - Vending Machine)
*   **Moomoo Milk:** 100 HP (Buyable - Limited, Route 112)
*   **EnergyPowder:** 50 HP (Buyable - Herb Shop) *Lowers Friendship*
*   **Energy Root:** 200 HP (Buyable - Herb Shop) *Lowers Friendship*
*   **Oran Berry:** 10 HP (Found/Grown)
*   **Sitrus Berry:** 30 HP (Found/Grown)
*   **Berry Juice:** 20 HP (Found - Extremely rare)

**Status Healers**
*   **Antidote:** Poison (Buyable)
*   **Paralyze Heal:** Paralysis (Buyable)
*   **Awakening:** Sleep (Buyable)
*   **Burn Heal:** Burn (Buyable)
*   **Ice Heal:** Freeze (Buyable)
*   **Full Heal:** All Status (Buyable)
*   **Lava Cookie:** All Status (Buyable - Mt. Chimney/Lilycove)
*   **Heal Powder:** All Status (Buyable - Herb Shop) *Lowers Friendship*
*   **Status Berries (Pecha, Cheri, Chesto, Rawst, Aspear, Lum):** (Found/Grown)

**Revives**
*   **Revive:** Restores to 50% HP (Buyable)
*   **Max Revive:** Restores to 100% HP (Found Only)
*   **Revival Herb:** Restores to 100% HP (Buyable - Herb Shop) *Lowers Friendship*
*   **Sacred Ash:** Restores entire fainted party to 100% HP (Found Only - Navel Rock/Event)

---

### 2. Story Availability and Costs

In Gen 3, Poké Mart inventories are largely tied to specific cities rather than your badge count (though some items unlock post-game).

*   **Early Game (Gym 1-2):**
    *   *Potions (300₽)*, *Antidotes (100₽)*, *Paralyze Heals (200₽)*: Oldale, Petalburg.
    *   *Super Potions (700₽)*: Rustboro City, Slateport City.
*   **Mid Game (Gym 3-6):**
    *   *Herb Shop (Lavaridge Town):* EnergyPowder (500₽), Energy Root (800₽), Heal Powder (450₽), Revival Herb (2800₽). *(Highly accessible mid-game power, but dangerous for friendship).*
    *   *Lava Cookies (200₽):* Mt. Chimney summit. (Cheaper than Full Heals, identical effect).
    *   *Hyper Potions (1200₽)* & *Revives (1500₽)*: Fallarbor Town, Fortree City.
*   **Late Game (Gym 7-8 & Elite Four):**
    *   *Lilycove Department Store:* The ultimate hub. Sells Hyper Potions, Max Potions (2500₽), Revives, and Full Heals (600₽).
    *   *Vending Machines (Lilycove Roof):* Fresh Water (200₽), Soda Pop (300₽), Lemonade (350₽).
    *   *Pokémon League Mart:* Unlocks **Full Restores (3000₽)**.

---

### 3. In-Battle Mechanics & Tactical Rules

Using an item takes up the turn, but has a priority of **+6**, meaning it will almost always occur before any Pokémon attacks.

**Tactical Rules for a Bot:**
1.  **The "Out-Damage" Rule:** If `Enemy_Expected_Damage > Item_Heal_Amount`, using an item is mathematically a losing play. The bot will burn its turn and its item, and end up with less HP than it started with. *Action: Switch or Attack.*
2.  **The "Kill vs. Be Killed" Rule:** If `Current_HP < Enemy_Expected_Damage` (you will die this turn) **AND** you outspeed the enemy **AND** you can KO the enemy this turn: *Action: ATTACK.* Do not heal. Win the fight.
3.  **The "Setup" Rule:** Healing gives the opponent a free turn. If the opponent uses stat-boosting moves (Dragon Dance, Calm Mind) while the bot heals repeatedly, the bot will get swept.

---

### 4. Standard Human Player Inventory Heuristics

To ensure the bot doesn't run out of money or items, program its shopping logic to maintain these minimum inventory thresholds:

*   **Early Game (Pre-Wattson):** 10 Potions, 3 Antidotes, 3 Paralyze Heals.
*   **Mid Game (Flannery to Winona):** 15 Super Potions, 5 Revives, 3 Full Heals. *(Humans often buy 20 Lemonades here because they are highly cost-effective, though the text-box spam is annoying).*
*   **Late Game (Tate & Liza to Wallace):** 25 Hyper Potions, 10 Revives, 5 Full Heals.
*   **Elite Four Prep:** 40 Full Restores, 20 Max Potions (or Lemonades for between-battle healing), 25 Revives. *There is no healing between the 5 E4 battles; the bot must buy enough to survive 5 boss fights.*

---

### 5. Downsides and Traps a Bot Must Know

*   **The Revive Loop Trap:** A common bot failure state. The bot's Pokémon faints. It uses a Revive. The Pokémon is sent out at 50% HP. The enemy is faster and deals >50% HP damage, instantly killing it again. The bot uses another Revive. **Solution:** Never revive an outsped Pokémon if the expected incoming damage exceeds 50% of its Max HP.
*   **The Herb Shop Friendship Trap:** Revival Herbs and Energy Roots are cheap and powerful. However, they drastically lower a Pokémon's Friendship. If the bot is using a Pokémon that evolves via Friendship (e.g., Golbat into Crobat) or relies on the move **Return** (the best Normal-type move for bots, scaling with Friendship), Herb items will ruin the run.
*   **The Full Restore Overheal:** A poorly coded bot will use a 3000₽ Full Restore to cure a Poison status when the Pokémon is at 95% HP. This will bankrupt the bot. **Solution:** Separate Status healing from HP healing unless HP is also critically low.
*   **Vending Machine Bottleneck:** Buying Lemonades one by one takes a massive amount of time due to the animation. For an automated bot aiming for real-time speed, buying Hyper Potions in bulk at Lilycove is infinitely faster, even if less cost-efficient.

---

### 6. STRATEGY: Concrete, Testable Heal Policy for a Bot

Here is a proposed logic tree for the bot's battle engine. It separates regular encounters from boss fights to save money.

**Variables to track:**
*   `Fight_Class`: [Wild, Trainer, Boss/Gym/Rival]
*   `Enemy_Dmg`: The maximum damage the enemy has dealt in a single turn this fight (defaults to an estimated % based on level gap if unknown).
*   `Can_KO`: Boolean. True if the bot's best move will deal >= Enemy Current HP.
*   `Outspeeds`: Boolean. True if Bot Speed > Enemy Speed.

**The Policy (Evaluated every turn):**

**Phase 1: Do we skip healing?**
1. If `Fight_Class == Wild`: Do not use items. (Heal outside of battle). *Exception: Enemy is Shiny.*
2. If `Can_KO == True` AND `Outspeeds == True`: Do not heal. ATTACK.

**Phase 2: Are we in danger?**
3. Set `Danger_Threshold`:
   * If `Fight_Class == Boss`: `Danger_Threshold = 50%` of Max HP.
   * If `Fight_Class == Trainer`: `Danger_Threshold = 30%` of Max HP.
4. If `Current_HP < Enemy_Dmg`: (Lethal range)
   * If `Best_Available_Item_Heal <= Enemy_Dmg`: **SWITCH POKEMON**. (Healing is futile).
   * Else: **HEAL**.
5. If `Current_HP < Danger_Threshold`:
   * **HEAL**.

**Phase 3: Item Selection (If HEAL is triggered)**
6. Calculate `HP_Deficit = Max_HP - Current_HP`.
7. Iterate through inventory (from smallest healer to largest):
   * Select the cheapest item where `Heal_Amount >= HP_Deficit`.
   * *Fallback:* If no item perfectly covers it, use the item with the highest `Heal_Amount`.
8. *Status Override:* If `Status == Poison/Burn` AND `Fight_Class == Boss` AND `Current_HP > 50%`: Use Antidote/Burn Heal/Lava Cookie. (Ignore Poison in quick trainer fights). If `Status == Sleep/Freeze`, heal immediately regardless of fight class.

**Phase 4: Out-of-Battle Policy**
* After every battle, if any party member is `< 50% HP`, use the cheapest Potions (or Lemonades) to restore them to `> 80% HP`. *Never enter a trainer's line of sight below 80% HP.*