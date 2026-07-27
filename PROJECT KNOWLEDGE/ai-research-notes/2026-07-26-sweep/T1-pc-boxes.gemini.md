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

Here is the concrete, specific information regarding the Pokemon Storage System in Pokemon Emerald for an automated bot.

### 1. Box vs. Party: Routing and Full Party Behavior
*   **Wild Catches:** When a wild Pokemon is caught, if the party has 5 or fewer members, it is added directly to the party. If the party has 6 members, it is automatically sent to the PC Box. 
*   **When the Party is Full:** The game automatically routes caught Pokemon to the currently active Box. If the active Box is full, the game automatically increments and deposits it into the next available Box with free space. The game will display a text box stating: `"[Pokemon] was sent to Box [Name] on the PC."` 
*   **Gift Pokemon / Eggs (UNCERTAIN):** I am heavily confident but flagging as *UNCERTAIN* for safety: Unlike wild catches, gift Pokemon (like Castform, Steven's Beldum, or the Wynaut Egg) generally *do not* go to the PC automatically in Gen 3. The NPC will usually say "Your party is full!" and the bot will be blocked from receiving the gift until it deposits a Pokemon to make a free slot.

### 2. PC UI Flow in Emerald (Menu Path)
To program the exact inputs from standing directly in front of the PC in a Pokemon Center, facing up:

**Initial PC Boot:**
1. Press `A` to interact.
2. Text: "[Player] booted up the PC."
3. Menu pop-up. Select **SOMEONE'S PC** (Note: this dynamically renames to **LANETTE'S PC** after speaking to Lanette on Route 114. Your bot must check for both strings or just select the top option).
4. Text: "The POKéMON Storage System was opened."

**Path A: Using DEPOSIT / WITHDRAW (Traditional)**
*   **To Deposit:**
    1. Select **DEPOSIT POKéMON**.
    2. The Party menu appears. Move D-Pad to highlight the party member.
    3. Press `A`. A sub-menu appears.
    4. Select **STORE**. The Pokemon disappears into the current Box.
    5. Press `B` to exit back to the Storage System menu.
*   **To Withdraw:**
    1. Select **WITHDRAW POKéMON**.
    2. The Box grid appears. Move D-Pad to highlight a boxed Pokemon.
    3. Press `A`. A sub-menu appears.
    4. Select **WITHDRAW**. The Pokemon disappears into the Party.
    5. Press `B` to exit back to the Storage System menu.

**Path B: Using MOVE POKéMON (Recommended for Bots)**
*Emerald has a drag-and-drop UI which is often faster/less prone to sub-menu looping.*
1. Select **MOVE POKéMON**. 
2. A hand cursor appears in the Box grid. 
3. Move the cursor to the bottom right corner of the screen to the **PARTY** icon and press `A`. The screen slides to the Party view.
4. Highlight a party member, press `A`, select **MOVE**. 
5. The screen slides back to the Box. Move to an empty grid slot, press `A` to drop it.
6. (To withdraw, do the reverse: grab from the Box grid, move to the PARTY icon, and drop into an empty party slot).
7. Press `B` to back out to the main menu.

### 3. Box Capacity and Full Storage
*   **Capacity per Box:** 30 Pokemon
*   **Number of Boxes:** 14 Boxes
*   **Total Capacity:** 420 Pokemon
*   **When ALL 420 slots are full:** The game completely prevents you from catching Pokemon. If the bot attempts to throw any Poke Ball in battle, the item is not consumed, the throw animation does not play, and a message appears. *(UNCERTAIN on exact string: I believe it is "The BOX is full! You can't catch any more!" or "There is no more room for POKéMON!")*. Your bot must recognize this fail-state or it will get stuck in an infinite loop trying to throw balls.

### 4. In-Game Restrictions
*   **Last Conscious Pokemon:** **Restricted.** You *cannot* deposit your last alive (non-fainted) Pokemon. The game will block it with the message: `"That's your last POKéMON for battle!"` (You *can* deposit fainted Pokemon freely, as long as one alive Pokemon remains).
*   **Holding an Item:** **Allowed.** You can deposit Pokemon holding items. The item stays equipped to them inside the PC.
*   **Knowing an HM Move:** **Allowed.** You can freely deposit Pokemon knowing HM moves. (Emerald has an anti-softlock mechanism for *releasing* HM Pokemon, but not for *depositing* them). 

### 5. Strategy for an Automated Bot
*   **When is it worth swapping?** Almost never, unless the bot needs a specific HM (like Dive or Waterfall) to progress the story and no current party member can learn it. 
*   **The "PC Heal" (Benefit):** Depositing a Pokemon into the PC and withdrawing it immediately fully restores its HP, PP, and cures status conditions. This is a common speedrun strat. A bot could technically use the PC to heal without talking to Nurse Joy, though Nurse Joy's `A`-mashing text is usually easier to program.
*   **The Leveling Cost:** Emerald **does not** have a modern, universal EXP Share. Boxed Pokemon gain 0 EXP. If your bot swaps a level 15 Pokemon out of the box into the party during the late-game, that Pokemon will be instantly obliterated in battle. 
*   **Optimal Bot Strategy:** Catch a core team of 3-4 Pokemon, keep them in the party permanently so they become massively over-leveled, and only use the PC to fetch temporary HM slaves if absolutely necessary.

### 6. Ordering / Party Position Rules
*   **Lead Pokemon (Slot 1):** The Pokemon in Slot 1 is always sent out first in single battles. In double battles (which are quite frequent in Emerald, especially if you cross lines of sight of two trainers simultaneously), **Slot 1 and Slot 2** are sent out together. 
*   **Taking the First Hit:** Because Slot 1 is sent out first, they will always take the first hit. If Slot 1 is fainted before the battle starts, the game automatically sends out the next conscious Pokemon in numerical order (Slot 2, then 3, etc.).
*   **Out-of-Battle Abilities:** The lead Pokemon (even if fainted) applies Gen 3 field effects. For example, if Slot 1 has *Intimidate*, it reduces the wild encounter rate of low-level Pokemon. If it has *Synchronize*, wild Pokemon have a 50% chance to share its nature.
*   **EXP Share (Held Item):** In Emerald, EXP Share is a *held item*, not a global toggle. The total base EXP of a defeated enemy is split 50/50. 50% goes to the Pokemon holding the EXP Share, and 50% is divided evenly among all Pokemon who actually participated in the battle. If a bot swaps Pokemon mid-battle, the battle EXP is fractured, resulting in slower leveling overall.