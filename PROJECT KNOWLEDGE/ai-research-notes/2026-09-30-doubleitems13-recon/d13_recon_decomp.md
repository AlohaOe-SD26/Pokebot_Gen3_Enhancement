# 2026-09-30 — design v2 step 13 (KB-2, healing items in DOUBLE battles): recon angle `decomp`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `doubleitems13-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Step 13 (KB-2) research note: how healing items work in Emerald double and multi battles, checked against the decomp

This is a note, not a source of truth. I read the decomp at pret/pokeemerald `master` `fe1d8e51` (2026-09-30) with `gh api`, and our code in `C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot` as it stood on 2026-09-30.

- **VERIFIED** means I read the cited line.
- **INFERRED** means I reasoned from lines I read but did not run anything.

The files are cached at `C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\01ddd963-7a1a-4b49-8ecd-33397f5304e2\scratchpad\decomp\` and its `s13\` subfolder. I did not touch the worktree and did not run the emulator.

**Headline:** a player's healing item takes effect the moment it is chosen in the party menu, not when the turn runs. That fact decides most of the design questions below.

## A. The spec's claims, one by one

| # | Claim in the spec | Verdict | Evidence |
|---|---|---|---|
| A1 | Items are blocked only in link, Frontier, e-Reader and recorded-link battles (`battle_main.c:4222`) | **NUANCED** | `battle_main.c:4221-4225` tests `LINK \| FRONTIER_NO_PYRAMID \| EREADER_TRAINER \| RECORDED_LINK`. `FRONTIER_NO_PYRAMID` leaves the Pyramid out (`include/constants/battle.h:96-97`), so the Battle Pyramid allows items. `DOUBLE`, `MULTI`, `INGAME_PARTNER` and `TWO_OPPONENTS` are not in the block. A blocked choice goes through `BattleScript_ActionSelectionItemsCantBeUsed` and back to the action menu (`battle_main.c:4226-4233`). |
| A2 | `StoryItemBattleStrategy` has no double-battle override, so it only attacks (`story_mode.py:518`, 06:4427) | **VERIFIED in substance; the line number is stale** | The only `decide_turn_in_double_battle` in `story_mode.py` is at `:563`, on `LevelUpTravelBattleStrategy`. The class at `:739-1214` overrides only `decide_turn` (`:796`). It is worse than the spec says: in a double, battler 0 is also sent to the double method (`battle_action_selection.py:202-203`), so neither battler ever reaches `_maybe_use_item`. |
| A3 | All 32 leader rematch IDs are doubles | **VERIFIED from the source** | `src/data/trainers.h`: every `_2` to `_5` for Roxanne, Brawly, Wattson, Flannery, Norman, Winona, Tate & Liza and Juan has `.doubleBattle = TRUE` (Roxanne_2 at `:9251` through Juan_5 at `:9623`). All eight gym scripts start the rematch with `trainerbattle_rematch_double` (for example `data/maps/MossdeepCity_Gym/scripts.inc:108`). `battle_setup.c:1137-1140` swaps in the rematch ID. Every rematch entry carries 3 Full Restores. |
| A4 | `CreateNPCTrainerParty` ORs the double flag into the battle type (`battle_main.c:2072`) | **VERIFIED** | `gBattleTypeFlags \|= gTrainers[trainerNum].doubleBattle;` |
| A5 | Tate & Liza 1 is the only first-fight leader who fights a double | **VERIFIED** | `trainers.h:3263` is `TRUE`; the other seven `_1` entries are `FALSE` (`:3191`, `:3203`, `:3215`, `:3227`, `:3239`, `:3251`, `:3275`). |
| A6 | Doubles pay ×2 (`battle_script_commands.c:5625-5626`) | **VERIFIED; the lines are off by one** | At `fe1d8e51`, `:5626-5627` is the ×2 branch. `:5624-5625` is the two-opponent branch, which comes first and is not doubled; both trainers are paid instead (`:5637-5639`). Tate & Liza 1 pays 4 × 42 × 2 × 25 = ₽8,400 (LEADER money value 25 at `battle_main.c:501`; last mon L42), doubled again with the Amulet Coin (`battle_util.c:3296`). |
| A7 | Maxie and Tabitha at the Space Center are a story-boss multi where items are usable | **VERIFIED, with limits** | The flags are `TRAINER\|DOUBLE\|TWO_OPPONENTS\|MULTI\|INGAME_PARTNER` (`battle_tower.c:2122-2124`), so the player may use items. See §B4 for the limits. |
| A8 | `in_mossdeep_gym.ss1` is VOLATILE (`FIXTURES.md5:37`) | **VERIFIED** | The game also refuses to start a double unless the party has 2 or more usable mons (`data/scripts/trainer_battle.inc:28-29`, and `:69-70` for rematches; `pokemon.c:4507-4525`). A pinned Tate & Liza save must therefore have at least 2 non-fainted, non-egg mons. |
| A9 | The "index probe" is needed (plan step 1) | **VERIFIED** | There are two party index spaces plus the battler-id space; see §B2. Vanilla Emerald has no `itemPartyIndex` field (0 matches in `include/battle.h`, `battle_main.c` and `party_menu.c`). The target never reaches the battle engine; only the item ID is returned (`battle_controller_player.c:1390`). |

## B. The mechanics, from the decomp

### B1. How each player battler chooses an action in a double
- **Who is asked when.** Battler 0 (player left) is asked first. Battler 2 (player right) is asked only after battler 0's choice is confirmed, unless the partner is absent or the battle is a MULTI (`battle_main.c:4145-4148`). A battler that is locked into a multi-turn move or must recharge is not asked at all (`:4160-4165`). An absent battler gets "nothing" automatically (`:4150-4156`).
- **The action menu.** Each battler has its own cursor, `gActionSelectionCursor[gActiveBattler]` (`battle_main.c:225`). "Bag" is cursor position 1 and sends `B_ACTION_USE_ITEM` (`battle_controller_player.c:254-256`). The cursor is reset only when a battle starts (`battle_controllers.c:52`).
- **Opening the bag.** The engine sends `EmitChooseItem(gBattleStruct->battlerPartyOrders[gActiveBattler])` (`battle_main.c:4236`). On receipt, `PlayerHandleChooseItem` sets `gBattlerInMenuId = gActiveBattler` and copies that order into `gBattlePartyCurrentOrder` (`battle_controller_player.c:2653-2663`).
- **B on battler 2's menu.** Battler 2's prompt always carries battler 0's choice and item (`battle_main.c:4168`). In a non-multi double, pressing B there (`battle_controller_player.c:306-324`) behaves by what battler 0 chose:
  - a Poké Ball: the ball goes back into the bag and battler 0 chooses again;
  - any other item: the B press does nothing (`return` at `:319`), so a heal cannot be undone;
  - a move or switch: battler 0's choice is cancelled (`B_ACTION_CANCEL_PARTNER`, handled at `battle_main.c:4292-4330`) and battler 0 chooses again.
- **Can both battlers use an item in the same turn?** Yes. Nothing checks the partner's choice.
- **If both want the last Potion.** It cannot be double-spent. The item is removed from the bag when battler 0 uses it (`party_menu.c:4434`). At zero quantity the slot's item is cleared (`item.c:399-400`), and the bag is compacted the next time it opens (`item_menu.c:726`, `:1102-1113`). Battler 2 never sees it.
- **Cancelling out of the bag.** Leaving the bag returns item 0 (`item_menu.c:1257`), and the battler simply chooses again with no turn lost (`battle_main.c:4406-4410`).

### B2. The party menu inside a battle: layout, cursor and the two index spaces
- **Which layout.** A single uses `PARTY_LAYOUT_SINGLE`. A double uses `DOUBLE`, or `MULTI` when `IsMultiBattle()` is true (`party_menu.c:5765-5772`). `IsMultiBattle()` means MULTI and DOUBLE and TRAINER and in battle (`:1206-1212`). The item menu is opened by `ChooseMonForInBattleItem` (`:5781-5786`).
- **Where the cursor starts.** `keepCursorPos` is false, so the cursor starts on menu slot 0 (`party_menu.c:524-525`). In a double, slot 0 is the left battler's mon, even when battler 2 is the one choosing. To heal itself, battler 2 must move to slot 1.
- **Cursor movement in the double and multi layouts.** Up and Down step through slots in order, skipping empty ones (`:1588-1695`; `MENU_DIR_DOWN` = 1 and `MENU_DIR_UP` = -1 at `:159-160`). Up from slot 0, or Down from the last slot, lands on Cancel (slot 7). `gPartyMenu.slotId` is byte 9 of `gPartyMenu` (`include/party_menu.h:9-21`), which is what our `get_current_party_menu_index` reads (`menuing.py`).

**The two index spaces:**
- **P, the party index.** This is the index into `gPlayerParty` in its normal order, i.e. `gBattlerPartyIndexes[battler]`. Our `mon.party_index` is this value (`battle_state.py:274`).
- **M, the menu slot.** This is the position on screen in the party menu, i.e. `gPartyMenu.slotId`.

**The conversion:**
- M to P: `GetPartyIdFromBattleSlot(M)` returns nibble M of `gBattlePartyCurrentOrder` (`party_menu.c:6027-6038`).
- P to M: `GetPartyIdFromBattlePartyId(P)` returns the position whose nibble equals P (`party_menu.c:6058-6076`).
- Our `map_battle_party_index` (`battle_state.py:332-354`) goes P to M, the same direction as the decomp (VERIFIED by reading both).

**How the order is built:**
- In a non-multi double, the order is [left active, right active, then the rest ascending] (`party_menu.c:5971-5987`), set up for every battler at battle start (`battle_controllers.c:100-103`).
- After a switch, `SwitchPartyOrder` writes the same order to both player battlers (`battle_main.c:4099-4105`). So battlers 0 and 2 see the same M order, and the two active mons stay at slots 0 and 1 (INFERRED from the swap at `:4095-4097`).
- In the multi, the order is fixed as P0, P3, P1, P2, P4, P5 (`party_menu.c:5950-5955`, via `battle_controllers.c:151`). Slots 1, 4 and 5 are Steven's mons (`:5806`).

**While the menu is open, `gPlayerParty` itself is rearranged into menu order:**
- `UpdatePartyToBattleOrder` rearranges it (`party_menu.c:5785` calls `:6078-6087`), and `UpdatePartyToFieldOrder` puts it back when the menu closes (`:1235-1236`).
- Inside the menu, `gPlayerParty[k]` is therefore the mon on menu slot k.

**How the target is resolved:**
- `ItemUseCB_Medicine` calls `ExecuteTableBasedItemEffect(&gPlayerParty[slotId], item, GetPartyIdFromBattleSlot(slotId), 0)` (`party_menu.c:4388-4394`, `:4416`).
- `PokemonUseItemEffects` then looks for the battler by P: starting on the choosing battler's side, it checks battlers 0 and 2 for `gBattlerPartyIndexes[i] == P` (`pokemon.c:4789-4802`). `gBattlerInMenuId` decides only the side, not the target. Either battler can heal either mon.

### B3. When the heal happens, and what happens with odd targets
- **The heal applies at selection.** HP is written to the party and, for an on-field target, to `gBattleMons[b].hp` immediately (`pokemon.c:5083-5096`). The bag count drops at the same moment (`party_menu.c:4434`).
- **At execution, the player's item does nothing more.** `HandleAction_UseItem` (`battle_util.c:312-331`) runs `BattleScript_PlayerUsesItem`, which is only `moveendcase MOVEEND_MIRROR_MOVE; end` (`data/battle_scripts_2.s:113-115`).
- **Turn order.** Items and switches are queued first, in battler-ID order (0, 1, 2, 3), and are left out of the speed sort (`battle_main.c:4817-4825`, `:4841-4847`). The player's heal has in fact already landed before battler 2 is even asked. Opponent AI heals run as their own action, first in the turn (`BattleScript_OpponentUsesHealItem`, `data/battle_scripts_2.s:117-125`).
- **Target is the partner's active mon.** `battler` becomes 2, its `gBattleMons` HP is updated and its health box refreshed (`pokemon.c:5094-5106`).
- **Target is a benched mon.** `battler` stays `MAX_BATTLERS_COUNT`, so only the party copy changes (`:5091`).
- **Target is fainted and the item is not a Revive.** The effect is skipped (`pokemon.c:5056-5062`) and the game shows "won't have any effect" (`party_menu.c:4419-4425`). Nothing is consumed and the game returns to the bag, not the battle (`:4476-4477`, exit callback `CB2_ReturnToBagMenu` at `:5783`). Backing out of the bag then leads to a re-choice.
- **Revive on a benched fainted mon.** It clears the absent flag of the choosing battler's partner position instead (`pokemon.c:5050`). This is a quirk, and Revive is off in our bot.
- **A game counter that confirms an on-field heal.** `gBattleResults+0x03` (`numHealingItemsUsed`, `include/battle.h:239`) goes up only when a non-Revive HP item lands on an active player battler (`pokemon.c:5097-5100`).

### B4. Which battles allow items, and which battler the player controls
- **Ordinary doubles and gym-leader rematches:** the player controls battlers 0 and 2 (`battle_controllers.c:220-230`), and both may use items.
- **The Space Center multi (Steven with you, against Maxie and Tabitha):**
  - Battler 2 is `SetControllerToPlayerPartner` (`battle_controllers.c:137-138`), which runs AI immediately (`battle_controller_player_partner.c:1502-1506`). Our handler's battler-2 branch will never fire; the bot plays battler 0 only.
  - Steven never uses items (`battle_ai_switch_items.c:815-816`).
  - The opponents get no items at all in partner battles (`battle_ai_script_commands.c:291-296`).
  - Steven's mons sit at P3 to P5 in `gPlayerParty` with a different trainer ID (`battle_tower.c:2969-2991`). Nothing I found stops the player's Potion targeting them (`party_menu.c:1309-1317` checks only for eggs; INFERRED, not run).
- **Two opponents:** the flag changes only the pay (A6), not whether items are allowed.

### B5. Tate & Liza (`trainers.h:3256-3266`; party at `trainer_parties.h:3546-3575`)
- **Entry:** class LEADER, 4 Hyper Potions, `doubleBattle` TRUE, AI flags CHECK_BAD_MOVE, TRY_TO_FAINT and CHECK_VIABILITY.
- **Party:**
  - Claydol L41 (Earthquake / Ancient Power / Psychic / Light Screen);
  - Xatu L41 (Psychic / Sunny Day / Confuse Ray / Calm Mind);
  - Lunatone L42, holding a Sitrus Berry (Light Screen / Psychic / Hypnosis / Calm Mind);
  - Solrock L42, holding a Sitrus Berry (Sunny Day / Solar Beam / Psychic / Flamethrower).
- **Their healing:** both of their battlers share one pool of trainer A's items (`battle_ai_script_commands.c:299-306`). A Hyper Potion is used only below 25% HP or when more than 200 HP is missing (`battle_ai_switch_items.c:864-868`); at their levels that effectively means below 25%. This is noise for any comparison, so measure only our side.
- **Relevance to the A/B (INFERRED):** Hypnosis puts a mon to sleep, which is in our cure set, so a status-cure decision is reachable. Earthquake hits both of our mons, so a turn where both want an item is reachable.

## C. What a builder needs to know
1. The heal happens when the target is chosen, not when the turn runs. HP and the bag count are both final before the party menu closes, and before battler 2 is asked. The consumption check (did the bag count drop?) can be judged right after the menu closes.
2. Battler 0 always chooses first. A heal by battler 0 cannot be cancelled from battler 2's menu.
3. Neither the game nor anything else reserves items between the two battlers. When the item runs out, it is gone from the bag.
4. The cursor starts on slot 0 (the left battler's mon) whichever battler is choosing. In the double layout, Up and Down move through slots in order.
5. The only conversion needed is party index P to menu slot M, using `gBattlePartyCurrentOrder` read after the bag opens. In a non-multi double it is the same for both battlers.
6. Rule 10 ground truth, all independent of our own variables:
   - `gBattlerInMenuId` (`battle_main.c:228`) tells you which game battler is choosing;
   - `gPartyMenu[9]` gives the menu slot, and `gPlayerParty[slot]` read while the menu is open gives the exact mon the A press will hit;
   - after the menu closes, the HP change of the intended mon, found by PID in normal order, confirms the heal;
   - the bag count change confirms consumption;
   - `gBattleResults[3]` confirms an HP item landed on an active battler.
7. The multi is outside a doubles probe: the bot controls battler 0 only, and Steven's three mons appear in the party.
8. A double needs 2 or more usable mons, or the leader refuses the fight.

## D. Where our code runs into these mechanics (reads VERIFIED; consequences INFERRED)
- **D1. The battle-action cursor bug is the most likely thing to wedge once doubles use items.**
  - `scroll_to_battle_action` → `_select_in_menu("gActionSelectionCursor", …)` always reads byte 0, which is battler 0's cursor (`battle_menuing.py:57-64`, `:90-91`). Battler 2's menu moves `gActionSelectionCursor[2]` (`battle_controller_player.c:250`, `:268-303`). `scroll_to_move` gets this right with its third-byte argument; the action cursor does not.
  - Once battler 0 has picked Bag, `cursor[0]` stays at 1. If battler 2 then wants to Fight (`battle_action_selection.py:1197-1198`), it presses Left on a cursor that never changes. It gives up after 60 steps (`battle_menuing.py:27`) and the mode goes into recovery.
  - If battler 2 wants the Bag instead, nothing is pressed, and A lands on battler 2's own cursor (probably Fight). The retry presses at `battle_action_selection.py:1044-1047` could then commit a move.
  - This is invisible today only because both cursors always stay at 0 in doubles.
- **D2. Two meanings of "battler index."**
  - The strategy is handed 0 or 1 (`battle_action_selection.py:203`, `:212`).
  - The handler and the game use 0 or 2 (`:199`, `:211`; `gBattlerInMenuId`).
  - The probe must say which one it logs.
- **D3. The item logic assumes the left battler.** `_maybe_use_item` takes `own_side.left_battler` for the decision (`story_mode.py:832`) and for the fresh-read verdict (`:908`). With two battlers asking for items, the pending checks at `:1152` and `:1161` must be tied to the mon's identity (PID), not its slot.
- **D4. Battler 2 decides on out-of-date HP.** The handler re-reads the battle state only when the battler changes, and only after deciding (`battle_action_selection.py:577-579`, while the decision is at `:212`). Battler 2 therefore sees HP from before battler 0's heal, although the game has already applied it (`pokemon.c:5091`, `:5096`). It could spend a second item on a mon that is already healed.
- **D5. Where KI-108 bites.** `BattleState.__eq__` ignores the party order (`battle_state.py:249-261`). The cache keeps the old object when the new one compares equal (`state_cache.py:293-298`). Only the first `get_battle_state()` caller in a frame gets the fresh object (`battle_state.py:808-827`). If a new probe calls `get_battle_state()` in the same frame, before the remap after the bag opens (`battle_action_selection.py:1115`) or before the verdict read (`story_mode.py:907`), that remap or verdict can get a stale party order. The probe should read the raw symbols with `read_symbol` instead.
- **D6. Our party reader sees menu order while the menu is open.** While `PARTY_MENU` is showing, `get_party()` returns the mons in menu order (B2), not normal order. The `[PARTY]` permutation logged at `battle_action_selection.py:1087-1092` is this effect. Take PIDs inside the menu deliberately as the menu-slot ground truth, and nowhere else.
- **D7. Holes in the bag (UNVERIFIED).** The strategy reads the bag before the bag opens, so it may see an empty slot left by battler 0's last item. I did not check how our bag reader handles an empty slot in the middle of a pocket.
- **Possible fixture.** A pinned double exists, `ki90_double_absent_seed.ss1` (`FIXTURES.md5:66`). It is not a key-class fight and has not been confirmed to reproduce, so it could at most be an ordinary-double control.

## E. Not verified
- That `ReducePlayerPartyToSelectedMons` puts the chosen 3 at P0 to P2.
- That the bag's in-battle list order matches our bag reader after compaction.
- Anything at runtime: every consequence in §D is reasoned from code, not observed.
