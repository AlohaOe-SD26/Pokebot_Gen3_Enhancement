# 2026-09-30 — design v2 step 13 (KB-2, healing items in DOUBLE battles): recon angle `ourcode`, verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (a subagent's return, read-only recon; workflow `doubleitems13-recon`). Every load-bearing claim is verified by the author before the design relies on it.

# Step 13 (KB-2) code audit: where a flag-gated double-battle item path has to plug in

**Summary:** adding `decide_turn_in_double_battle` to `StoryItemBattleStrategy` would not be enough on its own. The code that carries out an item action has no idea which of our two Pokémon is choosing. It reads only the left Pokémon's action-menu cursor, so the right Pokémon cannot use an item at all. Worse, one item used by the left Pokémon breaks the right Pokémon's ordinary move in the same turn.

This is a NOTE. VERIFIED means I read the line. INFERRED means reasoning from lines I read. Nothing was modified or run. Line numbers are for worktree `C:/Remote Projects/pokebot-wt-ch24`. The decomp is `pret/pokeemerald` at master `fe1d8e51`, fetched with `gh api`. In the citations, `sm` = `sandbox-pokebot/plugins/custom_modes/story_mode.py` and `bas` = `sandbox-pokebot/modules/battle_action_selection.py`.

---

## (a) `StoryItemBattleStrategy`, its item logic and its parent chain

**The class chain (VERIFIED):**
- `StoryItemBattleStrategy` (`sm:739`) inherits `LevelUpTravelBattleStrategy` (`sm:403`).
- That inherits `LevelUpLeadBattleStrategy` (`battle_strategies/level_up.py:9`), which has no double-battle override anywhere in its 148 lines.
- That inherits `DefaultBattleStrategy` (`default.py:60`), which inherits `BattleStrategy` (`_interface.py:8`).

**Methods the class defines (VERIFIED):** only `__init__` (`sm:765`), `decide_turn` (`sm:796`) and `_maybe_use_item` (`sm:805`). There is no `decide_turn_in_double_battle`.

**How a double battle resolves today (VERIFIED):**
- The call goes to `LevelUpTravelBattleStrategy.decide_turn_in_double_battle` at `sm:563-614`. Your spec cites `:518`; the method has moved to `:563`, and the spec's claim about it is true.
- **Trainer battle:** it returns only `UseMove` or `UseMoveAgainstRightSideOpponent`, never an item, switch or run (`sm:575-614`).
- **Wild battle:** it calls `super()` at `sm:573-574`, which lands on `DefaultBattleStrategy` at `default.py:236-279`. That path can call `_handle_lead_cannot_battle` (`default.py:249`, `:279`).

**`decide_turn` (VERIFIED):** `sm:796-803` wraps `_maybe_use_item` in `try/except Exception: action = None`, so it fails open. Otherwise it returns `super().decide_turn`.

**`_maybe_use_item`, in order (VERIFIED):**
- `import os as _os` sits at the top, and that position matters (`sm:806-817`).
- Wild battles return early: `if BattleType.Trainer not in battle_state.type: return None` (`sm:823-824`).
- The step-6 gate follows: `if _os.environ.get("POKEBOT_R27_KEYITEMS") == "1" and not _r27_key_gate(self, battle_state): return None` (`sm:830-831`).
  - `_r27_key_gate` is at `sm:6361-6400`. It caches its verdict on the instance (`_r27_verdict`, `sm:794`, `:6371-6373`, `:6393-6394`).
  - It reads opponent B only when the battle has the `TwoOpponents` flag (`sm:6383-6388`).
  - The pure verdict is `trainer_identity.key_battle_verdict` (`modules/story/trainer_identity.py:70-84`). It already takes a list of sides; its docstring says *"the list form is for step 13"* (`:71-74`). The key classes are listed at `:63-67`.
- **The target is hard-coded:** `mon = battle_state.own_side.left_battler` (`sm:832-834`).
- The biggest hit taken is tracked per `mon.party_index`, in one number for the whole battle (`sm:838-841`).
- **Status-cure verdict:** `sm:863-885`. It compares `mon.party_index` against the index saved when the cure was requested.
- **Heal verdict:** `sm:887-1037`.
  - It takes a fresh `get_battle_state()` (`sm:905-910`), but the Pokémon it judges is again `own_side.left_battler` (`sm:908`).
  - The branch order is: consumed (`sm:959`), then "judged Pokémon is not the one we asked for" (`sm:974`, which clears the request **silently**), then "not consumed" (`sm:976`, which triggers the retry or the item disable).
- **Choosing the item:**
  - Candidates are bag items with `battle_use is Healing` (`sm:1045-1049`), then RULING 18's reserve filter, which fails unlocked (`sm:1057-1062`), then `parameter > 0` for the HP policy (`sm:1063`).
  - The `POKEBOT_HEAL_AT_FRACTION` override is read at `sm:1079-1097`.
  - `choose_healing_item` (`modules/story/battle_items.py:59`) applies these rules:
    - heal only at or below 0.35 of max HP (`:43`, `:80`);
    - at most 4 uses per battle (`:49`, `:79`);
    - do not heal into a losing race (`:92-95`);
    - pick the cheapest item that covers the gap, otherwise the largest (`:98-110`).
  - If no heal is chosen, `choose_status_or_revive_item(..., allow_revive=False)` runs (`sm:1123-1132`). It cures only Sleep and Freeze.
  - `POKEBOT_E4_FAULT_NOCURE` is at `sm:1141-1142`.
- **Committing to the item (side effects):**
  - `_item_uses += 1` (`sm:1146`).
  - One single slot of "pending request" state: `_hp_when_item_requested = (mon.party_index, hp)`, `_item_qty_when_requested`, or `_status_when_item_requested` (`sm:1151-1164`).
  - The `[ITEM] using {item} on {species} {hp}/{max} (use n, worst hit w)` log line (`sm:1168-1172`).
  - `_index_space` is only a log label now (`sm:1185-1186`, `:1197-1213`).
- **Which index it sends:** `TurnAction.use_item_on(item, mon.party_index)` (`sm:1214`).
  - `party_index` is the low byte of `gBattlerPartyIndexes[battler]` (`battle_state.py:274`). That is the party-array index, not the battle order or the menu slot.
  - The menu slot is resolved later, by the executor (see (c)).
- **Where the strategy is built:** `StoryMode.on_battle_started` returns it for trainer battles at `sm:4357`. The harness drivers `mossdeepgym` and `mossdeepbadge` build it directly (`tools/story-dev/story_harness.py:3302-3309`, `:3402-3409`).

## (b) How the battle handler drives a double

**Where the decision is called (VERIFIED):**
- `bas:116` reads `battle_state = get_battle_state()` once, when the handler is entered.
- **Left Pokémon:** when controller 0's callback is in (`HandleInputChooseAction`, …), the handler sets `battler_index = 0` and calls `strategy.decide_turn_in_double_battle(battle_state, 0)` (`bas:198-205`).
- **Right Pokémon:** when controller 2's callback is `HandleInputChooseAction`, it sets `battler_index = 2` and calls `decide_turn_in_double_battle(battle_state, 1)` (`bas:207-212`).
- ⇒ **"battler_index" has TWO index spaces.** The strategy receives {0, 1}. The handler, the `[TURN]` line (`bas:453-457`) and KI-93's memory (`bas:33-43`) use battle-slot numbers {0, 2}. A probe must label which one it logs (rule 10).

**How often it is called (VERIFIED):** once per Pokémon, each time that Pokémon's action menu is up. The right Pokémon is only asked after the left one's choice is confirmed (decomp `battle_main.c:4140-4146`). The handler can be re-entered several times in one selection (`bas:27-30`), so a decision can repeat within a turn.

**The right Pokémon decides on stale data (VERIFIED from statement order):**
- The re-read `if previous_battler_index != battler_index: battle_state = get_battle_state()` at `bas:577-579` runs **after** each decision and before the action is carried out.
- So the right Pokémon's decision (`bas:212`) uses the object from the left Pokémon's re-read. That read happened **before** the left Pokémon's item flow ran.
- The game writes a heal into `gBattleMons[battler].hp` at menu time (decomp `pokemon.c:4788-4801` finds the battler, `:5091-5096` writes the HP), and removes the bag item at menu time (`party_menu.c:4428-4433`).
- ⇒ The right Pokémon cannot see a heal the left one just applied. Two items could be spent on one Pokémon (INFERRED consequence).

**Actions a double may return (VERIFIED):**
- The `TurnAction` values are: `UseMove`, `UseMoveAgainstRightSideOpponent`, `UseMoveAgainstPartner`, `RotateLead`, `UseItem`, `RunAway`, `SwitchToManual` (`_interface.py:104-147`). `use_move_against_left_side_opponent` is just an alias for `use_move` (`:117-119`).
- The executor's `match` (`bas:581-1007`) does not check single versus double.

**Is `UseItem` supported in a double?** It is accepted (`bas:585-598`) but it does not work:
- `battle_action_use_item(battle_state, item, target_index)` (`bas:1016`) has **no battler parameter**. It calls `scroll_to_battle_action(1)` (`bas:1034`).
- `scroll_to_battle_action` (`battle_menuing.py:89-91`) calls `_select_in_menu("gActionSelectionCursor", idx)` without `use_third_byte`, so it always reads **byte 0**, the left Pokémon's cursor (`battle_menuing.py:57-64`).
- The move-cursor helper does take a side: `scroll_to_move(..., battler_index > 1)` (`bas:1218`). Only the action cursor lacks it.
- In the game, `gActionSelectionCursor` is `u8[MAX_BATTLERS_COUNT]` (`battle_main.c:225`), and input is read per battler (`battle_controller_player.c:249`).

**Consequences (INFERRED from the lines above):**
1. **Right Pokémon uses an item:** reading byte 0 while the button presses move the right Pokémon's cursor never converges. It either hits the 60-step KI-45 limit, or, if byte 0 already reads 1, it presses A on whatever the right Pokémon's cursor is on. That can commit an unintended move before the "bag-did-not-open" return (`bas:1043-1056`).
2. **Left Pokémon uses an item, right Pokémon then attacks in the same turn:**
   - The action cursor is not reset per turn. It resets only on switch-in (`battle_controller_player.c:2190`), at battle setup (`battle_main.c:3203`, `:3285`) and on a reset command. Within the files I read, that command is only ever sent as `RESET_MOVE_SELECTION` (`battle_script_commands.c:7802`). So byte 0 stays at 1 (Bag).
   - The right Pokémon's move path then calls `scroll_to_battle_action(0)` (`bas:1197-1198`), reads byte 0 = 1, presses Left, and never converges.
   - That hits KI-45: `battle_menuing.py:38-55` calls `request_mode_recovery`, which sets a pending fault. The handler then stops at `battle_handler.py:332-333`, and StoryMode derails because it opted in (`sm:2123`).
   - The harness modes did not opt in (`MossdeepBadgeMode(BotMode)` at `story_harness.py:3372`, no `handles_battle_faults`), so there it raises `BotModeError` and drops to Manual.
   - ⇒ **Even a left-only item path needs the action-cursor fix.**
3. **Pressing B:** B on the right Pokémon's action menu cancels back to the left Pokémon, **except** after the left one used a non-ball item, when B does nothing (`battle_controller_player.c:306-324`). The comment at `bas:363-365` ("B is inert in a single battle") does not cover doubles.

## (c) How the executor carries out `use_item`, and every index conversion

**The steps (VERIFIED):**
1. Scroll to the Bag action (`bas:1034`; the per-battler problem is in (b)).
2. Press A up to 3 times, each waiting up to 30 frames for `BAG_MENU` (`bas:1043-1056`).
3. `scroll_to_item_in_bag` (`menuing.py:64-141`), then A, 4 frames (Ruby/Sapphire/Emerald), A (`bas:1058-1065`).
4. Wait up to 120 frames for `PARTY_MENU` (`bas:1106-1111`).
5. `_menu_slot = get_battle_state().map_battle_party_index(target_index)`, the "fresh" re-map from KI-101 (`bas:1112-1121`).
6. A cosmetic "pre-menu" value from the handler's snapshot (`bas:1125-1128`), logged on the `[ITEM-FLOW] party-menu target=… -> menu slot …` line (`bas:1129-1132`).
7. `scroll_to_party_menu_index(_menu_slot)`, A, then press B until `BATTLEMAINCB2` (`bas:1133-1140`).

**The conversion (VERIFIED):** party index → battle slot through the nibble-packed `gBattlePartyCurrentOrder` (`battle_state.py:332-354`, read at `:816`). This matches the decomp's packing (`party_menu.c:5911-5913`) and `GetPartyIdFromBattleSlot` (`:6027-6038`).

**The menu cursor (VERIFIED):** `scroll_to_party_menu_index` (`menuing.py:144-226`) reads `gPartyMenu[9]` (`menuing.py:229-236`) and presses only Up and Down.
- `gPartyMenu[9]` is `slotId` (`include/party_menu.h:9-21`; byte 8 holds `menuType:4` and `layout:2`).

**Does it assume the singles party-menu layout? No, as far as Up/Down go (VERIFIED from the decomp):**
- In a battle the layout is SINGLE, DOUBLE or MULTI (`party_menu.c:5765-5772`, used by `ChooseMonForInBattleItem` at `:5781-5786`).
- In the double layout, Up and Down step one at a time over non-empty slots (`party_menu.c:1588-1640`, `:1686-1696`; `MENU_DIR_DOWN = 1`, `UP = -1` at `:159-160`).
- The menu opens with the cursor at slot 0 (`party_menu.c:524-525`).

**The in-menu order in a normal (non-multi) double:** slot 0 = left active Pokémon, slot 1 = right active Pokémon, then the rest in ascending order.
- The order builder (`party_menu.c:5918-5976`) and the per-battler setup at battle start (`battle_controllers.c:97-103`) are VERIFIED.
- `SwitchPartyOrder` keeps the left and right Pokémon's orders equal in doubles (`battle_main.c:4097-4105`), which is VERIFIED. That the "slot 0 = left, slot 1 = right" invariant then holds for the whole battle is INFERRED.
- ⇒ This gives a **ground truth that does not depend on our mapping code**, for the rule-10 probe.

**The order array's source:**
- Opening the bag refills `gBattlePartyCurrentOrder` from `gBattleStruct->battlerPartyOrders[gActiveBattler]` (`battle_main.c:4236`, `battle_controller_player.c:2653-2663`). The same code sets `gBattlerInMenuId`, the number of the battler that opened the bag (`:2659`).
- `SwitchPartyOrder` copies **any** battler's order into that array, **enemies included** (`battle_main.c:4092-4093`, consistent with `battle_handler.py:494-495`). So the pre-menu value can be the opponent's order.

**The KI-108 stale-read hazard (VERIFIED):**
- `get_battle_state()` returns the cached object when it was already read in the same frame (`battle_state.py:808-811`).
- The cache setter keeps the **old** object when `__eq__` says equal (`state_cache.py:293-298`).
- `__eq__` compares neither `_battler_party_order` nor `_current_turn` (`battle_state.py:249-263`). It **does** compare `gBattleMons` and the battler party indexes, so HP and `party_index` from a cached object are always correct. **Only the order and the turn number can be stale.**

**Where KI-108 bites in step 13:**
- `bas:578` on the first loop pass is the **second** call in the frame of `bas:116`, with no `yield` between them. It can return an older object with a stale order and turn. That object goes into the left Pokémon's executor (it only affects the cosmetic value at `bas:1126`), and into the right Pokémon's decision and its `[TURN]` turn number (INFERRED).
- `sm:907` (`_ki101_state()`) is also a second call in that frame. It is safe because it reads only HP and `party_index`.
- `bas:1115` (the item re-map) is correct only while it is the **first** call of its frame. `bas:806` (the swap re-map) is in the same position.
  - ⇒ **An observe-only probe must NOT call `get_battle_state()` during the item flow.** It must read raw with `read_symbol` (the rule `dmgaudit.py:12-13` states; `sm:6584` follows it too).
  - The GUI debug tab calls `get_battle_state()` on every update (`modules/gui/debug_tabs.py:427`). In a run with the GUI open, that call could become first in each frame (INFERRED).

## (d) Upstream (the pristine `40cakes repo/pokebot-gen3` mirror)

**Healing in doubles:** upstream never heals in a double (VERIFIED).
- Its `DefaultBattleStrategy.decide_turn_in_double_battle` only attacks (`40cakes repo/pokebot-gen3/modules/battle_strategies/default.py:165-203`).
- Two strategies can return an item in a double, neither of them a heal:
  - `CatchStrategy.decide_turn_in_double_battle` just returns `decide_turn`, which throws a ball: `TurnAction.use_item(ball)` with no target (`battle_strategies/catch.py:62-65`).
  - An escape via `get_best_escape_method` can return a Poké Doll or Fluffy Tail (`battle_strategies/_util.py:108-112`).

**Upstream has the same executor defect (VERIFIED):**
- `battle_action_use_item` is battler-agnostic (`40cakes repo/pokebot-gen3/modules/battle_action_selection.py:162-178`).
- It maps before the menu opens (`:173`), which is the KI-101 bug our fork has since fixed.
- Its `scroll_to_battle_action` reads byte 0 only (`40cakes repo/pokebot-gen3/modules/battle_menuing.py:46-48`).

⇒ There is **no tested double-battle item path anywhere**, upstream or ours.

## (e) Telemetry a probe can reuse, and how flags are read

**Log lines (VERIFIED):**
- **`[ITEM]` family** (`sm`): `using` (`:1168-1172`, no battler and no PID), `✔ CONSUMED` (`:966-971`), `‼ not consumed` (`:987`), `status cure` (`:872-877`), `✔ landed` (`:1029-1033`), `‼ no effect` (`:1016-1019`), `KI-101 fresh-read failed` (`:917-921`).
- **`[ITEM-FLOW] {stage}`** (`bas:1022-1031`), including the target → menu slot line (`bas:1129-1132`).
- **`[TURN n] {me} -> {action} vs {foe}`** (`bas:537-541`). "me" is chosen by battle slot {0, 2} (`bas:453-457`). The **foe is always `opponent.left_battler`** (`bas:458`), even when the move targets the right opponent, so it mislabels doubles. For an item, the action prints only "UseItem".
- **`[KEYBATTLE] opp= class= key= allow= reason=`** (`sm:6397-6399`), printed only with the flag ON.
- **`[TRAINER] start … double= two= heal_stock=`** (`trainer_identity.py:222-262`). It is called only from `StoryMode.on_battle_started` (`sm:4083`), so the harness Tate & Liza drivers print **no** `[TRAINER]` line.
- **`[BATTLE] started hp=[…]`** (`modules/debug_logger.py:533`) and **`[PARTY] slotN a -> b`** (`debug_logger.py:540-544`). The `[PARTY]` lines show the party being reordered while the menu is open.
- **`[DMGAUDIT]` is singles-only** (`modules/dmgaudit.py`): it reads 2 battlers of `gBattleMons` (`:60`, size `0xB0`), battler 0's chosen action only (`:102`), and left versus left (`:113`). It cannot be reused for doubles as written.
- The KI-93 and KI-96 census lines are unrelated to items.

**Raw memory the probe can read without `get_battle_state()`** (addresses from `sandbox-pokebot/modules/data/symbols/pokeemerald.sym`):

| Symbol | Address / size | What it gives |
|---|---|---|
| `gActionSelectionCursor` | `0x020244ac`, u8[4] (`:185`) | each battler's action cursor |
| `gBattlerInMenuId` | `0x020244b8` (`:188`) | which battler opened the bag |
| `gPartyMenu` | `0x0203cec8`, `0x14` bytes (`:673`) | `[8] >> 4 & 3` = layout, `[9]` = cursor slot |
| `gBattlePartyCurrentOrder` | `0x0203cf00`, 3 bytes (`:685`) | the in-menu order |

- While the party menu is open, the PID at `gPlayerParty[slotId]` is the **identity** ground truth, because the party is reordered in the menu (`party_menu.c:6078-6087`).
- `gBattleStruct` is a **pointer** (`pokeemerald.sym:181`, size 4; `battle_main.c:221`). Reading `battlerPartyOrders` needs the pointer followed and then an offset. I estimate the offset at `0x60` from the struct layout in `include/battle.h:354-381`; that is INFERRED and must be checked live (at battle start it should decode as left, right, then the rest).

**How flags are read (VERIFIED):**
- `reset_per_run_state` (`sm:2265`) reads the R20, R24 and R25 flags into attributes (`sm:2363-2400`).
- `POKEBOT_R27_KEYITEMS` is read on every call (`sm:830`). That is the stated A-N6 exception (design v2 `:159`): the harness builds the strategy directly.
  - Its fault arms are `POKEBOT_R27_FAULT_RAISE` and `POKEBOT_R27_FAULT_ALLORDINARY` (`sm:6381-6385`).
  - It is also read by the kit's D2 rule (`modules/story/stock_topoff.py:308-313`).
- `POKEBOT_R26_KITTOPOFF` is parsed before any `yield` in `higher_level_actions.py:531-535`, and read in `stock_topoff.py:189` and `league_reserve.py:333`.
- ⇒ A `POKEBOT_R27_DOUBLEITEMS` flag **cannot** be read in `reset_per_run_state`:
  - the Tate & Liza drivers never create a StoryMode (`story_harness.py:3302-3309`, `:3402-3409`);
  - the executor module has no mode object at all, like the `dmgaudit` precedent (`dmgaudit.py:10-11`).
  - It has to be read on each call or per instance.
- New log fields may appear only with the flag ON (design v2 `:162`).

---

## Where the spec's assumptions about our code are wrong or incomplete

- **W1. Fixing the strategy is not enough.** The spec's statement at `:673` is true (the line is now `sm:563`). But the executor cannot run an item for the right Pokémon, and a left-Pokémon item derails the right Pokémon's same-turn move ((b), consequences 1 and 2).
- **W2. "Observe-only … beside ground truth" is partly contradictory.** The true in-menu order exists only after the bag is opened, which is an action (`battle_controller_player.c:2653-2663`). Ways around it:
  - read the source, `battlerPartyOrders[battler]`, through the dereferenced pointer (offset INFERRED);
  - use the decomp invariant (slot 0 = left, slot 1 = right in a non-multi double);
  - run a "look and back out" arm: open the bag, read, press B, which leads to `STATE_BEFORE_ACTION_CHOSEN` (`battle_main.c:4406-4409`). No item and no turn are spent, but extra frames make the run diverge (INFERRED).
- **W3. "What the singles policy would choose" cannot be computed without side effects.** `_maybe_use_item` hard-codes the left Pokémon (`sm:832`) and changes state: `_item_uses`, `_hp_seen`, `_worst_hit`, the pending-request slots, the index flip and `_r27_verdict`. The input-building code (`sm:1045-1105`) is inline. An observe-only probe needs that part pulled out as a pure function.
- **W4. "battler_index" is ambiguous:** {0, 1} for the strategy versus {0, 2} for the handler (b).
- **W5. Fixture.** `at_mossdeep_leaders.ss1` already exists. It is committed, stands at the leaders with the puzzle solved, is **not** in `FIXTURES.md5`, and `--driver mossdeepgym` overwrites it on every PASS (`CH18B_CAPTURE` defaults on, `story_harness.py:3363-3366`). Treat it as VOLATILE and **copy** it before measuring. `post_mossdeep_gym.ss1` is also unlisted and overwritten by `mossdeepbadge` (`:3472-3475`). The `mossdeepbadge` docstring claims the leads are Sceptile L47 + Zigzagoon L15 (`:3386-3390`). If so, the right Pokémon may faint before it can be healed. That is unverified, so compute the discriminator before relying on it.
- **W6. The Space Center fight is a MULTI battle, not a plain double.** Its flags are TRAINER, DOUBLE, TWO_OPPONENTS, MULTI and INGAME_PARTNER (`battle_tower.c:2123`). That means the MULTI menu layout, fixed per-side orders (`party_menu.c:5937-5950`), Steven's Pokémon in our party array, and only battler 0 being ours (INFERRED). It needs its own probe arm.
- **W7. The flag's relation to `KEYITEMS` is undecided.** With `KEYITEMS` off, the singles path uses items in **every** trainer battle (`sm:823-831`). So `DOUBLEITEMS` on its own would heal in ordinary two-trainer doubles. The kit already follows a "requires `KEYITEMS`" rule (`stock_topoff.py:308-313`); this flag needs the same decision.
- **W8. Shared per-battle state.** The 4-uses limit and `_worst_hit` are per battle, and the trackers are keyed by `party_index` in single slots (`sm:767-791`), not by PID as rule 3 requires. When the right Pokémon asks and the judged Pokémon (always the left one, `sm:908`) differs, a failed request is cleared silently at `sm:974` before the "not consumed" branch at `sm:976`. The retry-or-disable safety net never runs for it.

## Smallest set of changes a flag-gated double item path needs

- **S1. `StoryItemBattleStrategy.decide_turn_in_double_battle`:**
  - flag OFF → `super()`, unchanged byte for byte;
  - flag ON → the same `try/except` fail-open wrapper as `sm:797-803`;
  - pick the deciding Pokémon as `sm:576-578` does.
- **S2. Make the target a parameter of `_maybe_use_item`** (the deciding Pokémon, or a chosen partner). Re-judge the **same** Pokémon by PID at `sm:908`. Keep singles unchanged under gates #59/#60 and `repro_key_battle_items.py` (its A1 AST pin, and the fakes that supply only `left_battler` at `:159`). The step-6 gate is reused automatically (`sm:830`).
- **S3. Per-turn and identity bookkeeping:** at most one item per side per turn, or per-PID trackers. Either way, never judge a request in the partner's same-turn decision without knowing which Pokémon asked.
- **S4. Let the right Pokémon see the left one's heal.** Either skip the item when the partner already asked this turn, or take a fresh HP read. A fresh HP read is safe under KI-108 because HP is compared by `__eq__`. It must not come before an order-reading call in the same frame (`bas:806`, `bas:1115`).
- **S5. Executor:**
  - add an `is_right_side_pokemon` parameter to `scroll_to_battle_action` (`battle_menuing.py:89-91`; `_select_in_menu` already supports it);
  - pass the battler into `battle_action_use_item` (`bas:1016`, `:1034`);
  - **also** fix `battle_action_use_move`'s `scroll_to_battle_action(0)` (`bas:1198`). This is a shared path for every double battle, so gate it behind the flag or A/B-test it on ordinary doubles (rule 9).
- **S6. Keep the post-menu re-map as it is** (`bas:1106-1121`). Add, flag-ON only, the raw identity readback: `gBattlerInMenuId`, the layout, `slotId`, and the PID at `gPlayerParty[slotId]`.
- **S7. Read the flag per call or per instance** (the A-N6 exception) in both the strategy and the executor. Add a row to `29-DISABLED-FEATURES-REGISTRY.md` and a fault arm.
- **S8. Add `[ITEM]` fields, flag-ON only:** battler with both index spaces labelled, the target's (PID, species), the menu slot, and the PID found in the menu.

## Incidental finding (off-angle, VERIFIED as far as it goes)

`read_symbol("gBattleStruct", 16, 1)` reads the address `0x0202449c + 16 = 0x020244ac`, which is `gActionSelectionCursor[0]`, not `expGetterMonId`. `read_symbol` does not follow the pointer (`modules/memory.py:66-70`). Two call sites are affected:
- `sandbox-pokebot/modules/battle_move_replacing.py:147` (upstream `:104`). An item use leaves byte 0 at 1, so this code would read 1 as the party index when a move is learned. Consequence INFERRED.
- `sandbox-pokebot/modules/battle_strategies/_util.py:93` (`gBattleStruct` + `0x4C`), which is equally wrong for its run-attempts count.

It deserves its own verification and KI.

The decomp source files I read are saved in `C:\Users\Ripto\AppData\Local\Temp\claude\C--Remote-Projects-Pokebot-Gen3-Enhancement\01ddd963-7a1a-4b49-8ecd-33397f5304e2\scratchpad\decomp\`.
