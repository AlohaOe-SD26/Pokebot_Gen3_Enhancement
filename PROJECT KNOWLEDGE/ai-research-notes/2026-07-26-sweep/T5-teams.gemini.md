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

Designing an automated bot to complete Pokémon Emerald requires a deep understanding of Generation 3’s mechanical quirks. Unlike modern Pokémon games, Gen 3 requires strict resource management, lacks the modern universal EXP Share, and features a level curve that will severely punish a bot for spreading its experience too thin.

Here is a comprehensive breakdown of how to program a bot to build, maintain, and evaluate teams in Pokémon Emerald.

---

### 1. The Balanced Hoenn Team (Coverage, Roles, & Size)
**The "Train 6" Trap:** In Emerald, realistically, a human player **only trains 3 to 4 core combat Pokémon.** Training a full team of 6 splits the limited available EXP too thinly, leaving the whole team under-leveled.
*   **Core Combatants (3-4):** These receive 100% of the combat EXP.
*   **HM Mules (2):** These are never used in combat. Emerald requires heavy HM use: *Surf, Dive, Waterfall, Fly, Strength, Rock Smash, Cut, Flash*.
    *   *Mule 1 (Water):* Tentacool, Marill, or Wailmer (Surf, Dive, Waterfall, Strength).
    *   *Mule 2 (Land/Air):* Tropius or Skarmory (Fly, Cut, Rock Smash, Flash).

**Required Type Coverage for Emerald:**
*   **Water:** Mandatory for HMs, but also objectively the best type in Gen 3.
*   **Electric or Grass:** 70% of Hoenn is water, and the Champion (Wallace) uses an all-Water team. Electric is generally better (Manectric, Magneton).
*   **Fighting or Ground:** Needed to break through Norman (Normal), Wattson (Electric/Steel), and Sidney (Dark). 
*   *Note on the Physical/Special Split:* Gen 3 links physical/special damage to *Types*, not individual moves. All Water, Grass, Fire, Electric, Ice, Psychic, Dark, and Dragon moves are Special. All others are Physical. The bot *must* factor this in (e.g., giving a high-Attack Pokémon like Gyarados Water moves is a waste).

### 2. The Level Curve & Target Levels
Emerald has a notorious mid-to-late game EXP drought. Here is the curve the bot should aim for to avoid being steamrolled:

*   **Gym 1 (Roxanne - Rock):** Lv 14-15
*   **Gym 2 (Brawly - Fighting):** Lv 16-18
*   **Gym 3 (Wattson - Electric):** Lv 22-24
*   **Gym 4 (Flannery - Fire):** Lv 27-29
*   **Gym 5 (Norman - Normal):** Lv 29-31
*   **Gym 6 (Winona - Flying):** Lv 32-34
*   **Gym 7 (Tate & Liza - Psychic):** Lv 41-42 *(Note: This double battle is infamous. The level jump here is severe. The bot will likely need to grind wild Pokémon or use Match Call trainers before this fight).*
*   **Gym 8 (Juan - Water):** Lv 44-46
*   **Elite Four & Champion Wallace:** Core team must be **Lv 50-55**. Wallace’s ace (Milotic) is Lv 58.

### 3. EXP Mechanics & Catching Up
Gen 3 uses a "Flat EXP" formula. A level 5 Pokémon and a Level 50 Pokémon defeating the same Level 20 opponent will receive the exact same amount of EXP. (Modern games use scaled EXP).

*   **How EXP is shared:** If multiple Pokémon participate in a battle, the total EXP is divided equally among them. Trainer battles yield 1.5x more EXP than wild battles.
*   **The EXP Share:** Obtained from Mr. Stone at Devon Corp after delivering a letter to Steven in Dewford.
    *   *Function:* 50% of the total EXP goes to the participants. 50% goes to the EXP Share holder. 
    *   *Quirk:* If the EXP Share holder *also* participates in the battle, it gets 100% of the EXP (assuming it was the only participant).
*   **Cheapest catch-up method for a Bot:** "Switch Training" or "Bait and Switch." Put the under-leveled Pokémon in Slot 1. When battle starts, immediately switch to a high-level sweeper. The weak Pokémon gets 50% of the EXP safely. If it holds the EXP share *and* switch-trains, it gets 75% of the EXP.

### 4. Replacing vs. Training (Dead Weight)
Because EXP is a finite resource without tedious grinding, **replacing is often mathematically superior to catching up.** 

**Signals a Pokémon is "Dead Weight" (Bot Triggers):**
*   **The 2HKO Threshold:** It consistently requires 3 or more turns to KO evenly-leveled wild Pokémon.
*   **The Speed/Squish Factor:** It is consistently outsped and takes >50% damage from evenly-leveled opponents.
*   **Bad Movepool Lock:** The bot has already used one-time TMs (like Thunderbolt, Earthquake, Ice Beam) on other Pokémon, leaving this team member with low-Base-Power moves (e.g., Tackle, Astonish) past Level 30.

**When to Replace:**
A bot should replace a failing team member when a wild Pokémon or static encounter can be caught at a *higher or equal level* than the dead weight, possessing better base stats.
*   *Examples:* Catching a Lv 40+ Lairon in Victory Road to replace a Lv 35 Mightyena. Catching a Lv 30-35 Castform/Kecleon mid-game. Catching the Lv 70 Rayquaza (if the bot is programmed to do the Sky Pillar puzzle—*UNCERTAIN if a bot can navigate the cracked floor puzzle easily*).

### 5. Rotating Through the PC
**What thoughtful human players do:** They do *not* rotate combat members. 
The EXP economy in Gen 3 strictly prohibits maintaining 8-10 battle-ready Pokémon. A human player uses the PC strictly to swap out HM mules (e.g., pulling out a Tropius to use Fly, then putting it back for a battle-member before a Gym), or to deposit an early-game Pokémon (like Poochyena) forever once a better mid-game Pokémon (like Electrike or Aron) is caught.

**Bot Directive:** Do not program the bot to actively rotate a large roster. Once a Pokémon goes into the PC to make room for a higher-level replacement, it should be considered "retired."

### 6. Strategy: A Policy for Bot Team Generation
To ensure the bot has **varied** runs but still builds teams **strong enough to win**, you must separate the team structure into "Fixed Rules" and "Randomized Variables."

#### WHAT MUST NEVER BE RANDOMIZED (Strict Rules):
1.  **The "Team of 4+2" Rule:** The bot must only ever designate a maximum of 4 Pokémon as "Combatants." 2 slots must be dedicated HM Mules.
2.  **Type Prerequisites:** The final team of 4 *must* contain at least one Water-type move user (for Surf in combat) and one Electric or Grass type (to beat Wallace). 
3.  **Physical/Special Awareness:** The bot must never assign Special attacks to Pokémon whose base Attack heavily outweighs their Special Attack, and vice-versa (e.g., Alakazam must only use Psychic, Fire, Ice, Electric, Grass, Water, Dark, or Dragon moves).
4.  **HM Mules:** The bot must specifically filter the PC for Pokémon that can learn the required HMs for the current route, prioritizing Pokémon with 3+ overlapping HMs (Tropius, Marill, Linoone).

#### WHAT SHOULD BE RANDOMIZED (For Variety):
1.  **The Starter:** Randomly pick Treecko, Torchic, or Mudkip. (This inherently changes the early-game routing and HM Mule needs).
2.  **Encounter Slots:** The bot should be allowed to randomly catch and keep 3 additional combat Pokémon from a pre-approved list of "Viable Gen 3 Pokémon." 
    *   *Pool A (Early Game Randoms):* Ralts, Taillow, Shroomish, Makuhita, Electrike, Magikarp (if bot can switch-train to Lv 20).
    *   *Pool B (Mid Game Randoms):* Aron, Numel, Swablu, Trapinch, Zangoose/Seviper.
    *   *Pool C (Late Game Randoms):* Spheal, Shuppet/Duskull, Vulpix, Heracross.
3.  **The "Mid-Game Pivot":** Force the bot to randomly select one of its early-game catches (excluding the starter) and permanently box it after Gym 5 (Norman), replacing it with a random encounter from Pool B or C. This guarantees team variety across different runs without sacrificing the heavily-invested Starter.

**Summary of the Bot's Routine:**
*   *Step 1:* Pick random starter. 
*   *Step 2:* Catch 3 random "approved" Pokémon by Gym 3. 
*   *Step 3:* Catch 2 HM Mules. 
*   *Step 4:* Feed all EXP to the 4 combatants (Starter + 3 Randoms). 
*   *Step 5:* At Gym 6, evaluate team. If any Pokémon is failing the "Dead Weight" checks, replace it with an on-level wild Pokémon (e.g., a Lv 35+ Water type via Super Rod, or a Victory Road Fighting type).
*   *Step 6:* Steamroll Elite Four using a concentrated, over-leveled core of 4 rather than a weak, spread-out team of 6.