# 2026-09-30 — design v2 step 13 (KB-2, healing items in DOUBLE battles): recon angle `gemini`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `doubleitems13-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Step 13 (KB-2) Gemini fan-out, checked against the decomp

This is a note, not truth. Every claim below was checked against pret/pokeemerald `master`, fetched 2026-09-30. Its line numbers match our older cites; for example, `ItemUseCB_Medicine` is at `party_menu.c:4396`, the same line our code comments give. Nothing in the worktree was changed and no emulator was run.

Gemini was run with no `--model`, so it used the default `gemini-3.1-pro-preview`. The worktree has no `sandbox-pokebot/profiles/gemini.key`, so the first call exited with "No API key". I passed the main checkout's key file through `GEMINI_API_KEY` without printing it.

- Prompt: `C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\01ddd963-7a1a-4b49-8ecd-33397f5304e2\scratchpad\step13\prompt.md`
- Raw Gemini answer: `...\scratchpad\step13\gemini_doubleitems.md`
- Decomp copies used for checking: `...\scratchpad\step13\decomp\`

## Error rate

I split Gemini's answer into 44 separate claims:

| Verdict | Count |
|---|---|
| CONFIRMED | 19 |
| PARTIAL (right name, wrong value, file or mechanism) | 4 |
| WRONG | 21 |
| UNVERIFIABLE | 0 |

That is **48% fully wrong, 57% including partials**. The wrong claims cluster in exactly the part step 13 depends on: when an item takes effect, when it leaves the bag, and which index the party menu uses.

- **Names that do not exist:** 5 of about 45 (about 11%): `gItemMenuLocation`, `gBattleStruct->itemPartyIndex` (Gemini marked it UNSURE), `gActionsByPriority`, `SwapPokemon`, `playhealingsfx`.
- **Code-search check:** each returned 0 hits in `gh search/code repo:pret/pokeemerald`. A control search for `ChooseMonForInBattleItem` returned 3 hits, so the search works.
- **"useitemeffect":** offered as a battle-script command. The token exists only in `pokemon.c` and `pokemon.h`; the real item-script command is `useitemonopponent` (`battle_script_commands.c:6311`).
- **Denied a real symbol:** it said `gBattlePartyCurrentOrder` does not exist. It does (6 code hits), and it is the array KI-101 depends on.
- **Wrong path:** one map-script path (see #38).

## Claim by claim

**Q1: the item code path**
1. `PlayerHandleChooseAction` is in `battle_controller_player.c`. CONFIRMED, line 2575.
2. It "calls `HandleInputChooseAction`". PARTIAL: it installs `HandleChooseActionAfterDma3` (:2579), which then installs `HandleInputChooseAction` (:2571).
3. `gActiveBattler` is 0 to 3. CONFIRMED, :249.
4. `B_POSITION_PLAYER_LEFT` is 0 and `B_POSITION_PLAYER_RIGHT` is 2. CONFIRMED, `include/constants/battle.h:28,30`.
5. The BAG choice sends `B_ACTION_USE_ITEM` "(value 4)" through `BtlController_EmitTwoReturnValues`. PARTIAL: the call is at `battle_controller_player.c:255`, but the value is **1** (`include/battle.h:28`).
6. `CB2_BagMenuFromBattle` with `ITEMMENULOCATION_BATTLE`. CONFIRMED: `item_menu.c:565-568`, `include/item_menu.h:10`. The route is: the engine calls `BtlController_EmitChooseItem` (`battle_main.c:4236`), then `PlayerHandleChooseItem` (:2653), then `OpenBagAndChooseItem` (:1375-1383).
7. `ChooseMonForInBattleItem` (Gemini marked it UNSURE), `PARTY_MENU_TYPE_IN_BATTLE` and `PARTY_ACTION_USE_ITEM`. CONFIRMED:
   - `party_menu.c:5780-5785`;
   - installed by `ItemUseInBattle_ShowPartyMenu`, `item_use.c:1005`;
   - the constants are at `include/constants/party_menu.h:55` and `:71`.
8. A double battle uses `PARTY_LAYOUT_DOUBLE`. CONFIRMED by `GetPartyLayoutFromBattleType`, `party_menu.c:5765-5771`. Gemini missed that a multi battle uses `PARTY_LAYOUT_MULTI`.
9. "The menu slots mirror `gPlayerParty` 0-5." **WRONG**:
   - `ChooseMonForInBattleItem` calls `UpdatePartyToBattleOrder` (:5784).
   - That function physically reorders `gPlayerParty` into battle order (:6078-6087). `UpdatePartyToFieldOrder` undoes it when the menu closes (:1235-1236).
   - Double battle order: slot 0 is the left active mon, slot 1 the right active mon, then the rest in party order (`BufferBattlePartyOrderBySide`, :5941-5956).
   - Multi battle order is fixed at [0,3,1,2,4,5] (:5926-5937).
10. `ItemUseCB_Medicine` is in `item_use.c`. **WRONG file**: it is `party_menu.c:4396`. `item_use.c:1017` only assigns `gItemUseCB`.
11. The field path calls `ExecuteTableBasedItemEffect`. CONFIRMED: `party_menu.c:4388-4394` calls `pokemon.c:4723`.
12. "In battle (`gItemMenuLocation`) it skips the immediate heal." **WRONG** on both counts:
    - `gItemMenuLocation` does not exist; the real field is `gBagPosition.location` (`item_menu.c:1420`).
    - The heal is applied at **selection time** in battle too. The call passes `GetPartyIdFromBattleSlot(slot)` (`party_menu.c:4390-4391`). `PokemonUseItemEffects` then writes HP (`pokemon.c:5091`) and `gBattleMons[battler].hp` (:5096), and `RemoveBagItem` runs (`party_menu.c:4434`).
13. `gSpecialVar_ItemId` holds the item. CONFIRMED, `battle_controller_player.c:1390`.
14. The target is `gPartyMenu.slotId`. CONFIRMED (`party_menu.c:4399`), but it is a slot in the reordered battle-order party.
15. The target index is sent back through `gBattleStruct->itemPartyIndex`. **WRONG**: that field does not exist. **Only the item id travels to the engine**, through `BtlController_EmitOneReturnValue(itemId)` (`battle_controller_player.c:1390`, `battle_controllers.c:1391-1398`), and it lands in `gLastUsedItem` (`battle_main.c:4412`).
16. `gBattlerPartyIndexes` maps battler to party index. CONFIRMED, `pokemon.c:4796`.
17. "The item is not executed when selected." **WRONG** (see #12).
18. `HandleAction_UseItem` is in `battle_main.c`. PARTIAL: it is defined at `battle_util.c:312`; `battle_main.c:539` is only its table entry.
19. `BattleScript_PlayerUsesItem` via `gBattlescriptsForUsingItem`. CONFIRMED: `battle_util.c:330`, `data/battle_scripts_2.s:31-32`.
20. The heal happens at execution through a script command. **WRONG**: `BattleScript_PlayerUsesItem` is just `moveendcase MOVEEND_MIRROR_MOVE; end` (`battle_scripts_2.s:113-115`).

**Q2: both player battlers using items in one turn**
21. Both battlers may choose an item. CONFIRMED: there is no gate at `battle_controller_player.c:244-262` or `battle_main.c:4221-4237`.
22. "No code blocks BAG for battler 2." CONFIRMED as literally stated, but Gemini missed a related rule. Pressing B on the right battler's menu normally cancels back to the partner; it is **refused when the partner used a non-ball item** (`battle_controller_player.c:306-318`). The partner's action and item reach that check through `BtlController_EmitChooseAction` (`battle_main.c:4168`).
23. Items are not removed at selection. **WRONG**: they are removed at `party_menu.c:4434`. `HandleAction_UseItem` removes nothing for the player.
24. One Potion can be chosen for both battlers. **WRONG**: it is gone from the bag before battler 2's bag opens.
25. Items and switches have "+6 priority" in `gActionsByPriority`. PARTIAL: they do go first, but in battler-id order in `gActionsByTurnOrder` (`battle_main.c:4817-4845`). There is no priority number and no such array.
26. If the target switches out, the item hits the literal slot. **WRONG premise**: the heal has already happened.
27. If the target faints first, the item fails at execution. **WRONG**: a non-revive item on a 0-HP mon is refused at selection and not consumed (`pokemon.c:5056-5060`, `party_menu.c:4416-4421`).

**Q3: index spaces**
28. Menu slot equals save order. **WRONG** (see #9).
29. "`gBattlePartyCurrentOrder` does not exist in Gen 3." **WRONG**: it is used at `battle_controller_player.c:2661` and `battle_main.c:4092`.
30. Switches physically swap `gPlayerParty` via `SwapPokemon`. **WRONG**: `SwapPokemon` does not exist. In-battle switches update `gBattlerPartyIndexes` and `battlerPartyOrders` (`SwitchPartyOrder`, `battle_main.c:4085-4112`).
31. The callback uses the save index and writes it into the engine. **WRONG**: see #15 and `party_menu.c:4391` with `:6034-6044`.
32. The engine checks `gBattlerPartyIndexes` at execution. **WRONG timing**: that check happens at selection, `pokemon.c:4790-4801`.

**Q4: Tate & Liza and the Space Center**
33. Tate & Liza are TRAINER plus DOUBLE. CONFIRMED:
    - TRAINER comes from `battle_setup.c:1277`;
    - DOUBLE is ORed in at `battle_main.c:2072`;
    - `trainers.h:3263` has `.doubleBattle = TRUE`.
34. The double flag is set in `battle_setup.c`. **WRONG**: `battle_setup.c:848` reads `doubleBattle` only for the battle-transition minimum party count.
35. The player may use items against Tate & Liza. CONFIRMED: the block list is `battle_main.c:4221-4225`.
36. Space Center flags are MULTI, INGAME_PARTNER, TWO_OPPONENTS, DOUBLE and TRAINER. CONFIRMED, `battle_tower.c:2123`.
37. Started from `data/scripts/maps/MossdeepCity_SpaceCenter_2F.inc`. **WRONG path**: it is `data/maps/MossdeepCity_SpaceCenter_2F/scripts.inc:233-238`, which calls `special DoSpecialTrainerBattle` with `VAR_0x8004=SPECIAL_BATTLE_STEVEN`.
38. The player uses party slots 0-2. CONFIRMED: `ChooseHalfPartyForBattle` and `ReducePlayerPartyToSelectedMons` at `scripts.inc:228,234`.
39. Steven's team comes from `CreateNPCTrainerParty`. **WRONG**: it comes from `FillPartnerParty` and `sStevenMons` (`battle_tower.c:2124`, `:2959-2975`).
40. Steven's mons go into `gPlayerParty` 3-5. CONFIRMED, `battle_tower.c:2972-2975`.
41. The player may use items in the Space Center battle. CONFIRMED.
42. The bag is gated inside `HandleInputChooseAction` by LINK, EREADER and FRONTIER. **WRONG**: the gate is in `HandleTurnActionSelectionState` (`battle_main.c:4221-4225`), and the flags are LINK, FRONTIER_NO_PYRAMID, EREADER_TRAINER and RECORDED_LINK.

**Gemini's two "gotchas"**
43. Switch-swap hazard. **WRONG**: the heal applies at selection.
44. Duplicate-item illusion. **WRONG, and the opposite is true**: the bag count drops at selection.

## What Gemini raised that the spec (§Step 13, design doc lines 672-679) does not handle

**G1. The party menu layout differs in doubles and multis.**
- Double battles use `PARTY_LAYOUT_DOUBLE`; multi battles use `PARTY_LAYOUT_MULTI` with the fixed order [0,3,1,2,4,5], where slots 1, 4 and 5 belong to the partner (`party_menu.c:1190`).
- Moving Up/Down still steps through slots in index order and skips empty ones (`party_menu.c:1505-1513`, `:1588-1676`). Up from slot 0 goes to Cancel (7).
- The existing Up/Down walk in `scroll_to_party_menu_index` (`sandbox-pokebot/modules/menuing.py:189-227`) should therefore still reach the target (INFERRED). The probe should also log `gPartyMenu.layout`.

**G2. Both battlers can use an item in the same turn, but the strategy tracks only one request.**
- `_hp_when_item_requested` and `_item_qty_when_requested` hold one request each (`story_mode.py:1162-1175`).
- `_item_uses` (the cap on item uses per battle) and `_worst_hit` are shared across both active mons (`story_mode.py:766-771`).
- In a double, two foes can hit one mon between decisions, so `_worst_hit` can record the sum of two hits (INFERRED).
- Tate & Liza also carry 4 Hyper Potions (`trainers.h:3262`), which is the "heal war" case the item cap exists for.

**G3. The Space Center battle.**
- Steven's mons sit in `gPlayerParty[3..5]` for the whole battle, so our party readers see them as ours. One example is the living-member count passed to `choose_status_or_revive_item` (`story_mode.py:1124`).
- The player controls only battler 0. Battler 2 runs Steven's controller (`battle_controllers.c:141-146`); `PlayerPartnerHandleChooseAction` lets the AI choose (`battle_controller_player_partner.c:1502-1506`).
- So `decide_turn_in_double_battle(…, 0)` is the only call made there, and the battler-2 hazards below do not arise in that fight.

**G4. When the heal lands (Gemini got this backwards, but the question is decisive).** Because the heal applies at selection:
- the probe's ground truth can be read the moment the party menu closes, before the turn runs;
- any decision for battler 2 that follows a battler-0 heal must see the healed HP.

## Found while checking, in step 13's path, and not in the spec (INFERRED from code plus decomp; none of it measured)

**B1. The action-menu cursor is not battler-aware.**
- `scroll_to_battle_action` calls `_select_in_menu("gActionSelectionCursor", i)` without `use_third_byte` (`modules/battle_menuing.py:90-91`), so it always reads byte 0. `scroll_to_move` does pass it (:95-96).
- The game keeps one cursor per battler (`battle_main.c:225`, `battle_controller_player.c:249`) and resets it only when a mon switches in (`battle_main.c:3203`, `:3285`, `battle_controller_player.c:2190`).
- **Effect 1:** once battler 0 has chosen BAG, cursor[0] stays at 1. Battler 2's FIGHT (`battle_action_use_move` → `scroll_to_battle_action(0)`, `battle_action_selection.py:1197-1198`) then presses Left against cursor[2], which does not move. After 60 steps this is a KI-45 derail, and it repeats every turn until battler 0 switches.
- **Effect 2:** a battler-2 item request can press A on FIGHT, so a move gets committed instead of the item. The bag-count check (`story_mode.py:955-961`) then records "not consumed" twice, and items are switched off for the rest of the battle.

**B2. Battler 2 decides on stale HP.**
- Battler 2's decision (`battle_action_selection.py:211-212`) receives the state re-read at `:577-579`. That re-read happens after battler 0's decision but **before battler 0's item flow**.
- Since the heal lands at selection, battler 2 sees the pre-heal HP and could heal the same mon twice.
- Adding a fresh read inside the decide frame makes the `:578` read the **second** `get_battle_state()` in that frame. Under KI-108 (`battle_state.py:249-262` together with `state_cache.py:293-298`), that second read can carry a stale `_battler_party_order`.
- This already happens today: the KI-101 fresh read (`story_mode.py:907`) runs in the decide frame whenever a check is pending. The damage is limited because that state then feeds only the cosmetic `_pre_menu` value (`battle_action_selection.py:1126`) and RotateLead (`:611`). The real target re-map (`:1115`) runs in a later frame.

**B3. Only the left battler is ever considered.** Both `mon = …left_battler` (`story_mode.py:832`) and the KI-101 check (`:908`) use the left battler. A healed right-side mon is dropped without being checked by the branch at `:966`.

**B4. There are four index spaces in play:**
1. the strategy's side slot, 0 or 1 (`battle_action_selection.py:212` passes 1 for game battler 2);
2. the game battler, 0 or 2;
3. the party menu slot, in battle order;
4. the party index (`gBattlerPartyIndexes`).

The probe should log all four. In non-link doubles, battlers 0 and 2 get the same order at battle start (`battle_controllers.c:99-103`) and keep it through switches (`battle_main.c:4099-4105`). So `map_battle_party_index` should give the same answer whichever battler opened the bag (INFERRED).

**B5. Useful ground truths for the probe:**
- `gBattlerInMenuId`, the battler that opened the bag (`battle_controller_player.c:2659`);
- `gBattlePartyCurrentOrder` after the bag opens;
- `gPartyMenu.slotId` plus the PID and species at `gPlayerParty[slotId]` while the menu is open, which is the mon the item will actually touch (`party_menu.c:4399`);
- `gActionSelectionCursor[0..3]`;
- `gBattleResults.numHealingItemsUsed`, which goes up only when an active player mon is healed (`pokemon.c:5099-5100`).

**B6. Fixtures.**
- `at_mossdeep_leaders.ss1` is the "fast way to exercise the BATTLE" (`story_harness.py:3378`). It is re-captured on every ch18b PASS by default (`CH18B_CAPTURE="1"`, `story_harness.py:3363-3366`) and is not in `FIXTURES.md5`, so it is as volatile as `in_mossdeep_gym.ss1`.
- `post_space_center.ss1` is captured after the Space Center battle (`story_harness.py:3907-3910`) and is also not in the manifest, so the manifest has no pre-battle Space Center fixture.

**B7. The spec's own citations.**
- The "attacks only" cite `story_mode.py:518` has drifted. The double override is `story_mode.py:563-615`; line 518 is inside `choose_new_lead_after_faint`.
- The item block is exactly FRONTIER_NO_PYRAMID (`include/constants/battle.h:92`), so the Battle Pyramid does allow items.
- The spec's `battle_main.c:4222`, `:2072` and `battle_script_commands.c:5625-5626` cites are all CONFIRMED.

**B8. A stray B press on battler 2's action menu.**
- After battler 0 uses a medicine, the game refuses the cancel (see #22), which protects us.
- If battler 0 attacked instead, a stray B cancels battler 0's move (`battle_main.c:4282-4321`), and battler 0 is decided again (INFERRED).
