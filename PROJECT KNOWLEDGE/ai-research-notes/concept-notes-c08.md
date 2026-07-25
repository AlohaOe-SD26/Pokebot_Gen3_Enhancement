## A. MECHANICS THE ROM ENFORCES

**1. Mystery Gift Core & Unlock**
*   **The Unlock:** Mystery Gift is dormant until the player enters the phrase "LINK TOGETHER WITH ALL" in the questionnaire at a Poké Mart counter (`data/scripts/questionnaire.inc`). This sets `FLAG_SYS_MYSTERY_GIFT_ENABLE`. **[VERIFIED]**
*   **The Storage:** The ROM allocates a specific block in memory for received data: `gSaveBlock1Ptr->mysteryGift` (struct `MysteryGiftSave`, `include/mystery_gift.h`). It holds exactly 1 Wonder Card and 1 Wonder News at a time. **[VERIFIED]**
*   **The Delivery:** Once a Wonder Card is received, the script checks card status. The player must speak to the Deliveryman upstairs in any Pokémon Center (`data/scripts/mystery_gift.inc`) to receive the attached item/Pokémon. **[VERIFIED]**
*   **Without Official Data:** **It is mathematically and logically impossible to obtain these items via pure gameplay.** The ROM contains only the *client-side receiving logic* (`src/mystery_gift_client.c`). It does not contain the Wonder Card payloads, generation logic, or ticket data. Without feeding an official distribution payload into the GBA link/wireless ports, or executing a direct memory write via emulator, the bot will never encounter these events. **[VERIFIED]**

**2. Hardware / Protocol Requirements**
*   **e-Reader:** In English/Western Emerald, e-Reader support for Mystery Gift was completely stripped. It only supports scanning Trainer Hill and Berry data (`src/ereader_helpers.c`). You cannot scan an Eon Ticket e-Reader card into English Emerald. **[VERIFIED]**
*   **Wireless Adapter:** English Emerald expects Wonder Cards via the GBA Wireless Adapter protocol (`src/link_rfu.c`). **[VERIFIED]**
*   **Record Mixing:** The Eon Ticket can be obtained via GBA Link Cable Record Mixing (`src/link.c`), provided the *other* connected game is a Ruby/Sapphire/Emerald cart that already holds a distributable Eon Ticket. **[VERIFIED]**

**3. The Event Tickets (Lilycove Harbor scripts)**
The SS Tidal (`data/maps/LilycoveCity_Harbor/scripts.inc`) checks specific bag items and flags to grant access to event islands. **None of these destinations are reachable any other way.** There are no map connections (`data/maps/*/connections.inc`) or physical warp tiles from the mainland. **[VERIFIED]**

| Ticket | Item ID | Required Flag | Destination | Unlockable | Reachable otherwise? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Eon Ticket** | `ITEM_EON_TICKET` | `FLAG_ENABLE_SHIP_SOUTHERN_ISLAND`<br>`FLAG_SYS_HAS_EON_TICKET` | Southern Island | Latias or Latios (opposite of roaming choice) + Soul Dew | No |
| **Aurora Ticket** | `ITEM_AURORA_TICKET`| `FLAG_ENABLE_SHIP_BIRTH_ISLAND` | Birth Island | Deoxys | No |
| **Mystic Ticket** | `ITEM_MYSTIC_TICKET`| `FLAG_ENABLE_SHIP_NAVEL_ROCK` | Navel Rock | Ho-Oh and Lugia | No |
| **Old Sea Map** | `ITEM_OLD_SEA_MAP` | `FLAG_ENABLE_SHIP_FARAWAY_ISLAND` | Faraway Island | Mew | No |

## B. WHAT THE BOT CAN OBSERVE

*   **Mystery Gift State:** `gSaveBlock1Ptr->mysteryGift.state` (values: `0` = Empty, `1` = Has Card, `2` = Card Used/Item Claimed). **[VERIFIED]**
*   **Key Items Pocket:** `gSaveBlock1Ptr->bagPocket_KeyItems` to check if the ticket has been successfully claimed from the Deliveryman. **[VERIFIED]**
*   **Obedience Bit (Fateful Encounter):** `GetMonData(&mon, MON_DATA_MODERN_FATEFUL_ENCOUNTER)`. **[VERIFIED]**

## C. OPTION SPACE

### Option 1: Direct Memory Injection (The Pragmatic Approach)
Because you have full `libmgba` memory access, bypass the missing physical link protocol entirely. Write the Key Item to the bag, set the ship flags, and set `FLAG_SYS_MYSTERY_GIFT_ENABLE`.
*   **Mechanical Cost:** Low CPU cost, immediate. Bypasses the "pure controller inputs" philosophy of a typical bot.
*   **Failure Mode:** If injected before obtaining the SS Tidal (post-game), the bot might attempt to use the harbor script before it is initialized, causing script logic traps.
*   **Detection:** Check `FLAG_SYS_GAME_CLEAR` (Elite 4 beaten) and `FLAG_SYS_HAS_EON_TICKET`. If both are true, the harbor script will succeed.

### Option 2: Record Mixing Emulation (For Eon Ticket Only)
Run a second `libmgba` instance loaded with a save file of Ruby/Sapphire that possesses a distributable Eon Ticket. Connect them via emulator link cable API and navigate to the Record Corner.
*   **Mechanical Cost:** Extremely high. Requires multi-instance synchronization, link cable state machine handling, and complex UI navigation on both instances.
*   **Failure Mode:** Serial interrupt desyncs; one bot enters a UI state the other does not expect, resulting in an infinite wait at "PLEASE WAIT".
*   **Detection:** Read `gMain.state` and the link status variables (`gReceivedRemoteLinkPlayers`). If link times out or state halts for >30 seconds, abort.

### Option 3: Vanilla Ignorance
Do not attempt to obtain any of these tickets. Treat the game as a standard retail cart.
*   **Mechanical Cost:** Zero.
*   **Failure Mode:** None. The bot completes the story and catches Rayquaza/Kyogre/Groudon normally.
*   **Detection:** N/A.

## D. TRAPS

*   **The Mew/Deoxys Obedience Softlock:** If you attempt to cheat the bot to Birth/Faraway Island by injecting warp coordinates *without* executing the actual Wonder Card / Script flags, Mew and Deoxys will **never obey the player in battle**. Emerald's battle engine (`CalculatePlayerMonObedience` in `src/pokemon.c`) strictly checks the `MON_DATA_MODERN_FATEFUL_ENCOUNTER` bit for Mew and Deoxys. This bit is only set if the official script logic generates the encounter. If caught in the wild unscripted, the bot will waste infinite turns as the Pokémon disobeys. **[VERIFIED]**
*   **Old Sea Map Regional Lock:** The Old Sea Map was *never* officially released outside of Japan. While the item and translation exist in the English Emerald ROM, injecting the Wonder Card data for it into a US ROM requires custom/hacked payload generation. If your bot relies on historical event preservation data, the Old Sea Map data does not exist for English carts. **[VERIFIED]**
*   **Overwriting Wonder Cards:** `gSaveBlock1Ptr->mysteryGift` can only hold one card. If the bot triggers a link reception for an Aurora Ticket while an unclaimed Mystic Ticket is pending at the Deliveryman, the Mystic Ticket is permanently overwritten and lost. **[VERIFIED]**
*   **Unsaved Receptions:** The Mystery Gift reception happens on the main menu, *before* the save file is loaded. The data is kept in RAM. If the bot receives a gift, starts the game, and reboots or crashes *before saving*, the Wonder Card is lost, but the distribution hardware may tag the bot's Trainer ID as "already received", permanently locking the bot out of receiving it again. **[RECALL]**
*   **Roamer vs Eon Ticket Conflict:** The Eon ticket dictates you catch the Lati twin you *didn't* pick on the TV post-game. If the bot triggers the TV script but fails to select a color due to an interruption, Southern Island will not spawn the correct twin because the opposite variable (`VAR_ROAMER_POKEMON`) was never initialized. **[VERIFIED]**