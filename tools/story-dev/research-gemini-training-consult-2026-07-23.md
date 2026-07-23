Excellent questions. Designing a bot to navigate a Pokémon game's story efficiently requires a deep understanding of the underlying mechanics. Here are precise answers for Pokémon Emerald.

### 1. XP Persistence on Loss

Yes, all Experience Points (XP), stat experience (EVs), and level-ups earned during a trainer battle are kept permanently, even if the player whites out.

If a Pokémon grows to a new level and then faints in the same battle, it will remain at that new level after the whiteout. The game state for each Pokémon (current HP, stats, level, XP) is updated immediately after each opponent is knocked out. A whiteout simply ends the battle sequence and teleports the player; it does not roll back any character data progression.

**Caveats:**

*   **Traded Pokémon Boost:** The 1.5x XP multiplier for traded Pokémon applies normally and is retained.
*   **Exp. Share:** The mechanics work as expected. If one Pokémon with an Exp. Share is in the party (even if it never fought or is already fainted), it will receive its 50% share of the XP from any KO. The remaining 50% is split among the battle participants. All this XP is retained on whiteout.
*   **Switching:** The "switched" battle style multiplier (where non-participating Pokémon get XP) is not a feature in Generation 3. XP is only awarded to Pokémon that participated in the KO (were on the field for at least one turn when that opponent was active) or that hold an Exp. Share.

### 2. Whiteout Money Loss Formula

In Pokémon Emerald (and Ruby/Sapphire), the money lost upon whiting out is **not** a percentage of your total cash, unlike in later generations. The formula is a function of your party's highest-level Pokémon and the number of badges you possess.

**Formula:** `Money Lost = (Level of Highest-Level Pokémon) × (Base Payout)`

The Base Payout value increases as you earn more badges. The values for Emerald are:

| Badges | Base Payout |
| :--- | :--- |
| 0 | $8 |
| 1 | $16 |
| 2 | $24 |
| 3 | $36 |
| 4 | $48 |
| 5 | $60 |
| 6 | $80 |
| 7 | $100 |
| 8 | $120 |

For your bot challenging Wattson, it has 2 badges (Stone, Knuckle). If its highest-level Pokémon is L28, the money lost per whiteout would be: `28 × $24 = $672`.

### 3. XP Math Sanity Check

The XP gain from the gym leader will be an order of magnitude higher. Let's do a rough comparison using the Generation 3 XP formula.

**XP Formula:** `XP = (a × b × L) / 7`
*(This is a simplified version, assuming one non-traded Pokémon participates)*
*   `a` = 1.5 for a trainer battle, 1.0 for a wild battle.
*   `b` = The base experience yield of the defeated Pokémon.
*   `L` = The level of the defeated Pokémon.

**Required Data:**
*   **Voltorb** Base XP: 105
*   **Magneton** Base XP: 161
*   **Oddish** Base XP: 78

**Calculations:**
1.  **Wattson's Pokémon (Trainer Battle, a=1.5):**
    *   KO'ing **L20 Voltorb**: `(1.5 × 105 × 20) / 7` ≈ **450 XP**
    *   KO'ing **L22 Magneton**: `(1.5 × 161 × 22) / 7` ≈ **758 XP**
    *   **Total for 2 KOs:** ~**1,208 XP**

2.  **Wild Pokémon (Wild Battle, a=1.0):**
    *   KO'ing **L13 Oddish**: `(1.0 × 78 × 13) / 7` ≈ **145 XP**

**Conclusion:**
In a single losing attempt where the bot KOs just two of Wattson's Pokémon, it earns roughly **1,208 XP**. This is approximately **8.3 times** the XP earned from defeating a single L13 wild Oddish. The "train on the leader" strategy is vastly superior for raw XP gain per Pokémon defeated.

### 4. Better Mid-Game XP Sources Near Mauville

The bot is overlooking the single best source of repeatable XP in Emerald: the **PokéNav's Match Call** feature.

Here is a ranked list of better XP sources at this stage (for a party L20-28):

1.  **PokéNav Match Call Rematches:** This is, by far, the best option. After defeating a trainer, they may be registered in the PokéNav. They have a chance to request a rematch after the player takes 255 steps. The bot can walk/bike back and forth on a route to trigger these calls. Rematched trainers have higher-level Pokémon than their initial teams, their levels scale with story progression, and they award the 1.5x trainer XP multiplier plus prize money. Trainers on Route 117 (Triathletes) and Route 110 (PokéFans, Triathletes) are prime early targets. This is the most "faithful player" method for grinding.
2.  **Unfought Optional Trainers:** Before any grinding, the bot should exhaust all one-time trainer battles. This includes the remaining trainers on Route 110 (Seaside Cycling Road), Route 117, and especially Route 111 north of Mauville. This provides a massive, one-time XP and money boost.
3.  **Trick House:** North of Slateport on Route 110. The first few challenges are available and contain trainers with appropriate level Pokémon. This is another excellent one-time XP source.
4.  **Winstrate Family:** They are a good one-time burst of XP from fighting the four family members in a row. However, the final rematchable member (Vicky) has a very low-level team at this stage (L18 Pokémon) and is not useful for grinding a L28 team. She is mainly for EV training later.

### 5. Pitfalls of the "Train on the Leader" Strategy

While efficient for XP, this strategy has significant mechanical drawbacks the bot must account for.

*   **Money Drain:** As calculated, each loss costs hundreds of PokéDollars. Compounding this over 10-20 attempts can deplete the bot's funds, making it unable to afford crucial items like Potions, Antidotes, or Repels later on. The strategy gains XP at the direct expense of money.
*   **PP Depletion:** This is the most critical logistical constraint. The bot will use its most powerful moves to secure KOs. These moves have limited PP. After 3-5 losing attempts, the bot's key Pokémon may run out of PP for their strongest attacks, making subsequent attempts futile until it visits a Pokémon Center. This loop (fight, lose, heal, repeat) is viable, but the bot must track PP and not waste attempts when key moves are depleted.
*   **Leader's AI and Status Moves:** Wattson's team is designed to be disruptive. Voltorb may use Screech, and Magneton has Supersonic and Thunder Wave. Manectric also has Thunder Wave. The bot could easily get paralyzed or confused on turn one, fail to secure any KOs, and waste the entire attempt (costing money and PP for zero gain). The bot should be able to handle this, perhaps by leading with a Pokémon holding a **Cheri Berry**.
*   **No Anti-Repeat Mechanic:** There is **no limit** to how many times you can challenge a Gym Leader after a loss in Pokémon Emerald. You can immediately re-enter the gym and challenge them again. This part of the strategy is mechanically sound. The only "penalty" is the whiteout sequence and associated money loss.

### 6. Highest-Value Bot Improvement

For an in-game story bot, the highest-value improvement is overwhelmingly **(a) ordering the party before the fight so resistant/super-effective mons come out first.**

**Justification:**

*   **Simplicity vs. Impact:** This is the simplest change to implement with the most dramatic impact on performance. It requires a single, pre-battle calculation based on the known gym leader's team type. Starting with a favorable matchup (e.g., Marshtomp or Grovyle vs. Wattson's team) grants immediate initiative, reduces incoming damage, and maximizes the chance of securing the first one or two KOs. It directly solves the problem of a weak lead like Swellow fainting immediately.
*   **AI Complexity:** Live switch decisions (b) represent a massive leap in AI complexity. It requires predicting the opponent's move, evaluating every possible switch, and calculating risk vs. reward. While powerful, it is overkill for a story playthrough where a level and type advantage is usually sufficient.
*   **Brute Force Avoidance:** Simply raising the level target further (c) is the very problem the bot is trying to solve. It is the least efficient solution.
*   **Alternative (d):** A strong "something else" would be **strategic item usage** (e.g., using an X-item on the lead, or programming the bot to use a Super Potion when HP is low). This is also very high-value. However, correct party order is more fundamental—it prevents the bot from needing to use those Potions in the first place.

Therefore, implementing a pre-battle party order check is the most logical and efficient first step to improve the bot's battle intelligence.