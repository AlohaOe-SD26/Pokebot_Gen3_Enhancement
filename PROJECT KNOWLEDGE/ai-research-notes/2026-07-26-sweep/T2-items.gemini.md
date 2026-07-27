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

Here is a detailed breakdown of overworld item mechanics in Pokémon Emerald, specifically tailored for programming an automated story-playing bot.

### 1. Visible vs. Hidden Items: How the Player Obtains Them
*   **Visible Items:** These are represented on the overworld map by a standard Poké Ball sprite. To pick one up, the player cannot step *onto* the item's tile. The player must stand on one of the four adjacent tiles (North, South, East, West), face the item, and press the 'A' button. 
*   **Hidden Items:** These occupy a specific, invisible tile on the map. They are frequently hinted at by level design (a missing patch of grass, the center of a crater, a lone rock, or the end of a dead-end path). To pick them up, the rules are identical to visible items: the player must stand on an adjacent tile, face the coordinate of the hidden item, and press 'A'. 

### 2. The ITEMFINDER
*   **Where it is obtained:** It is given to the player by their Rival (May/Brendan) on Route 110 (the route connecting Slateport to Mauville) immediately after defeating them in battle.
*   **How it behaves:** It is a Key Item used from the Bag (or registered to Select). When used, the player character performs a short scanning animation.
*   **What it tells the player (Direction & Proximity):**
    *   **No Item:** If no hidden item is currently rendered on-screen, a text box says: *"Nope! There's no response."*
    *   **Proximity/Direction:** If an item is on-screen (roughly within a 7-8 tile radius), a sound plays, the text says: *"Huh? The ITEMFINDER's responding! There's an item buried around here!"* **Crucially, the player character will automatically turn to face the exact direction of the item.**
    *   **Underfoot:** If the player is standing directly on top of the hidden item tile, the text changes to: *"Oh! The ITEMFINDER's shaking wildly! There's an item buried underfoot!"* (To pick it up, the player must step off the tile, turn around, and press A).
*   *Bot Note:* Using the Itemfinder dynamically is computationally complex for a bot. It is almost always better to hardcode the X/Y coordinates of hidden items into the bot's memory rather than teaching it to use the Itemfinder.

### 3. Bag Full Behavior
*   **What happens:** When the bot presses 'A' to interact with an item, the game first displays: *"{Player} found one {ITEM}!"* Immediately after, the game checks the inventory. If the relevant pocket is full, a second text box appears: *"Too bad! The Bag's {Pocket Name} POCKET is full..."*
*   **Is it lost permanently?** **No.** If the bag is full, the item is dropped. A visible Poké Ball will remain on the overworld, and a hidden item's event flag will remain un-triggered. The player can return later with bag space to collect it.
*   **Bot Warning (Softlock Danger):** If your bot has a localized loop of "If see item -> go to item -> press A", a full bag will create an infinite loop. The bot will pick it up, fail, the item will stay there, and the bot will try to pick it up again. Your bot **must** parse the "Bag is full" text and temporarily blacklist that item's coordinates to break the loop.

### 4. Bag Pocket Structure in Emerald
Emerald's bag is divided into five pockets. Items stack up to 99 per slot.
*   **ITEMS Pocket:** 30 slots. (This is a major bottleneck. *Ruby/Sapphire only had 20, Emerald expanded it to 30*). This holds Potions, Repels, X-items, evolution stones, and hold items. 
*   **POKé BALLS Pocket:** 16 slots. Holds all capture devices.
*   **TMs & HMs Pocket:** 64 slots. *Virtually infinite* for a playthrough, as there are only 50 TMs and 8 HMs in Gen 3.
*   **BERRIES Pocket:** 43 slots. Holds exactly enough for one of every berry in the game.
*   **KEY ITEMS Pocket:** 30 slots. Ample space for all Key Items required for the story.
*   **PC Storage:** Because the 30-slot Items pocket fills up fast, your bot may need logic to visit a PC, boot up the item storage system, and deposit items (or just toss cheap items like Antidotes). The PC holds 50 slots.

### 5. Valuable Early-to-Mid Game Ground Items
Since money is finite and a bot might waste heals, picking up free items is highly recommended. 
*   **Visible Items worth a detour:**
    *   *Route 104 & Petalburg Woods:* Potion, Paralyze Heal, Great Ball, Ether.
    *   *Route 116 (Rustboro):* Repel, Potion, HP Up.
    *   *Route 110:* Revive, Dire Hit.
    *   *Route 113 (Ash Grass):* Max Ether, Super Repel.
*   **Hidden Items worth a detour (Hardcode these X/Y coords!):**
    *   *Route 104 (Beach):* Hidden Potion in the top left corner of the bottom beach.
    *   *Petalburg Woods:* Hidden Potion in the top right corner.
    *   *Route 116:* Hidden Super Potion in the crater near the Rusturf Tunnel entrance.
*   **Unbuyable Items:** Prioritize **Ethers, Max Ethers, Elixirs, and Rare Candies**. These cannot be bought at Poké Marts and are invaluable for a bot to restore PP before elite/boss fights or brute-force a level up.

### 6. STRATEGY: Sensible Policy for a Bot
The best policy for an automated bot is **Value-Weighted Hardcoding**. 

1.  **Do NOT use "Always Detour" (Dynamic Discovery):** If you give the bot vision to "see" a Poké Ball sprite and walk to it, it will eventually see items behind Cut trees, across water, or over one-way ledges. It will get stuck walking into a ledge or trying to pathfind to an unreachable node. 
2.  **Hardcode Waypoints:** Treat high-value items (Ethers, Revives, Rare Candies, TMs, and specific healing items) as optional story nodes. For example: *Node 45: Defeat Roxanne -> Node 46: Walk to X/Y on Route 116 to pick up Repel -> Node 47: Walk into Rusturf Tunnel.*
3.  **Ignore "Junk":** Ignore basic Potions after the 2nd Gym, and ignore stat-boosters (X-Attack, X-Defend) unless your bot is programmed to use them in battle. Picking up junk will fill the 30-slot Items pocket, preventing the bot from picking up a crucial TM or Revive later.
4.  **On-Path Incidental Grabs:** You can program a secondary rule: *If a Poké Ball sprite is literally adjacent to the bot's predetermined path, and the Items pocket is < 28/30, face it and press A.* But limit this to a 1-tile deviation to prevent pathfinding disasters. 
5.  **Hidden Items:** Exclusively hardcode these. Do not try to program Itemfinder logic. Just give the bot a list of 10-15 high-value hidden items and have it walk to those exact X/Y coordinates to press 'A' at the correct stage of the game.