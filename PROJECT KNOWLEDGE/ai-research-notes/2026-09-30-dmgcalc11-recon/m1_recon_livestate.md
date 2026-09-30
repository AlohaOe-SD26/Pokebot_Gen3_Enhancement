> ⚠ **A NOTE, NOT A SOURCE OF TRUTH.** Output of one agent of the design v2 step 11 recon (2026-09-30, a workflow of five fresh Claude agents; decomp read at pret/pokeemerald f90719c4). The design that uses it is `../2026-09-30-dmgcalc11-DESIGN.md`, whose author re-read every load-bearing claim it relies on (marked ✔ there). Line numbers are as of branch `wt/dmgcalc11` at `241929d7`. Scratch scripts it mentions were not committed.

# M1b recon: the live data `[DMGAUDIT]` needs each turn, and where our code can read it

*A research NOTE, not a source of truth. Angle: live-data readability for design v2 step 11 M1b.*

**Provenance**
- Our tree: worktree `C:/Remote Projects/pokebot-wt-ch24`, branch `wt/dmgcalc11`, HEAD `241929d7`. I only read it and changed nothing.
- Decomp: pret/pokeemerald pinned at **`f90719c46ce710427cfcae65419a3fa684b34a8a`** (master, 2026-09-29), fetched raw with `gh api`. Every decomp `FILE:LINE` below is at that commit.
- Symbol table: `sandbox-pokebot/modules/data/symbols/pokeemerald.sym` (73,195 lines). `patches/pokeemerald.sym` is empty. `patches/language/pokeemerald.yml` shifts battle symbols **only for Japanese (J)**, and only the old ones.
- Everything marked **UNVERIFIED** is inferred from code and was not observed live. I did not run the emulator.

---

## 0. The ten findings that matter for the design

1. **No reader exists today for the foe's chosen action, but the symbol is in our table.** `gChosenActionByBattler` is at `0x0202421c`, 4 bytes, one per battler (`pokeemerald.sym`). A grep of `sandbox-pokebot/` and `tools/` finds no Python reader for it, nor for `gChosenMoveByBattler`, `gWishFutureKnock`, `gBideDmg` or `gBattleResources`. Its lifecycle in the decomp:
   - It is set during selection (`battle_main.c:4179`, `:4369-4372`, `:4514`).
   - It is reset to `B_ACTION_NONE` in `BattleTurnPassed` (`battle_main.c:4001-4005`) and before the first turn (`:3897-3899`).
   - ⇒ **It is already cleared at the next `[TURN]`.** It can only be read between the end of selection and the end of that turn.

2. **The one race-free read point for "what did everyone choose" is the selection EXIT.** That is the first frame on which `gBattleMainFunc` is no longer `HandleTurnActionSelectionState`.
   - The decomp moves to `SetActionsAndBattlersTurnOrder` only when every battler has confirmed (`battle_main.c:4538-4541`).
   - In our code this is the frame on which `handle_battle_action_selection`'s `while` (`battle_action_selection.py:173`) falls through. Its caller continues in the same frame (`battle_handler.py:380`), so a read there adds no frames.
   - No HP has changed at that point: no action has run yet.
   - The foe's pick *probably* lands before our `[TURN]` decision too. The opponent controller answers synchronously (`battle_controller_opponent.c:1540-1544`, `:1551-1613`), and the foe is prompted in the same pass as us (`battle_main.c:4144-4170`). That timing is **UNVERIFIED**, and a read at the exit does not depend on it.

3. **After the turn, the turn-order arrays are SCRAMBLED, so they cannot be read back at the next `[TURN]`.**
   - `DoFieldEndTurnEffects`' `ENDTURN_ORDER` resets `gBattlerByTurnOrder` to the identity and re-sorts it by speed (`battle_util.c:1199-1212`).
   - `SwapTurnOrder` swaps `gActionsByTurnOrder` along with it (`battle_main.c:4587-4593`).
   - `Cmd_switchineffects` also overwrites a switched-in battler's action with `B_ACTION_CANCEL_PARTNER` (`battle_script_commands.c:5271-5273`).
   - ⇒ "Who moved first" and "what did the foe do" must be captured during the turn.

4. **`gBideDmg` (at `0x020241f8`, `s32[4]`, in the table) is a better primary observable than the HP difference.**
   - `Cmd_datahpupdate` adds the uncapped `gBattleMoveDamage` to it *before* capping HP at 0 (`battle_script_commands.c:1912` vs `:1920-1929`). It skips negative damage (heals, `:1896-1901`), Substitute hits (`:1865-1892`), and any update flagged `HITMARKER_IGNORE_BIDE`.
   - That flag is set for all battler end-turn effects (`battle_util.c:1464`), for Future Sight and Wish/Perish Song (`:1783`), and for sand and hail chip (`data/battle_scripts_1.s:3211`).
   - The only other write is a reset in `Cmd_setbide` (`battle_script_commands.c:7125`).
   - ⇒ **Its per-turn difference ignores AI items, drain, Leftovers, berries, Wish, Ingrain, poison, burn, Leech Seed, Nightmare, Curse ticks, Wrap, weather chip and Future Sight. It also keeps KO samples: it records the uncapped roll, where the HP difference is capped at the foe's remaining HP.**
   - Its live behaviour is **UNVERIFIED**. §5 gives a self-check.

5. **KI-108 cannot corrupt M1b's HP, PID or status reads, but it CAN corrupt the turn number.**
   - `BattleState.__eq__` compares `gBattleMons`, `gStatuses3`, `gDisableStructs`, weather, side timers, party indexes, count, type and absent flags (`battle_state.py:249-263`). The cache keeps the OLD object only when that comparison is equal (`state_cache.py:293-297`), so every compared byte of a stale object is current.
   - `current_turn` (`gBattleResults+0x13`, `battle_state.py:822`) is not compared, so it can be stale.
   - ⇒ Pair samples on a direct `read_symbol("gBattleResults", offset=0x13, size=1)`, never on `battle_state.current_turn` or the number on the `[TURN]` line.
   - M1b must also **not call `get_battle_state()`** (use a pure read; see §4). If it made itself the first caller in a frame, the KI-96 and KI-101 acting readers would become second callers, and the inertness control would be at risk.

6. **The `[TURN]` line is the wrong source for "the selected move".**
   - It is emitted (`battle_action_selection.py:534-538`) *before* the no-PP override rewrites `index` (`:552-569`).
   - A turn can produce several `[TURN]` lines: the move-menu B-back branch (`:211-245`) and the refusal bounces re-decide within the same turn.
   - Encore silently substitutes the move (`battle_main.c:4192-4197`).
   - ⇒ Log the move the game will execute: `gChosenMoveByBattler[0]` (at `0x02024274`, `u16[4]`), read at the selection exit (rule 7).

7. **`gBattleStruct` and `gBattleResources` are heap POINTERS. Our tree's only two `gBattleStruct` reads do not dereference them.**
   - `_util.py:93` reads `read_symbol("gBattleStruct", offset=0x4C)`, which actually reads `sLearningMoveTableID` at `0x020244e8`.
   - `battle_move_replacing.py:147` reads offset 16, which actually reads `gActionSelectionCursor` at `0x020244ac`.
   - The decomp declares the pointer at `include/battle.h:703`, allocates it at battle start (`battle_util2.c:25-35`) and frees it and sets it NULL at battle end (`:55-65`).
   - ⇒ Copying the house idiom would log garbage. Any `gBattleStruct` or `gBattleResources` field needs a dereference plus a non-NULL check.

8. **Several FAIL-direction (under-prediction) cases are missing from the spec's exclusion list.** They are cases where the foe acts *first* and changes our damage:
   - Swagger or Flatter on us;
   - the foe's own Superpower;
   - Dig, Fly or Dive, which make Earthquake, Gust, Twister or Surf double (`data/battle_scripts_1.s:237-240`);
   - Transform;
   - a hit that drops our HP to 1/3 or less, so Blaze, Torrent, Overgrow or Swarm activates (the calculator reads our HP from the snapshot, `_util.py:408-415`).

   Two unmodelled boosts also under-predict: our activated Flash Fire (`pokemon.c:3367`; `_util.py:518` "todo") and Cloud Nine or Air Lock (`_util.py:497` "todo"). These need `gChosenMoveByBattler[1]` and, for the Flash Fire case, `gBattleResources->flags`.

9. **The spec's "Rough Skin" exclusion must key on OUR ability, not the foe's.** Rough Skin damages the *attacker* (`datahpupdate BS_ATTACKER`, `data/battle_scripts_1.s:4184-4187`). The foe loses HP when it makes contact with *our* Rough Skin holder. By the same logic, our Liquid Ooze hurts a foe that drains us.

10. **In wild battles the foe can never use an item or switch.** `AI_TrySwitchOrUseItem` runs only under `BATTLE_TYPE_TRAINER` (`battle_ai_switch_items.c:541`). A wild foe picks a random move (`battle_controller_opponent.c:1596-1610`); only roamer, Safari and first-battle foes can flee (`:1563`, `:1574-1575`). So in the wild stratum those two exclusions never fire, which is correct.

---

## 1. Datum-by-datum table

"Ours" names where our code already reads the datum. "Symbol" names the memory needed when nothing reads it today. Offsets are into the decomp struct; "in sym" means present in `pokeemerald.sym` with the address shown.

| Datum (spec) | Readable today? | Where (ours) / how | Decomp evidence |
|---|---|---|---|
| Selected UseMove (acted-on) | ⚠ Only the strategy's *candidate* is readable | `[TURN]`'s `_me.moves[index]` (`battle_action_selection.py:466-470`) is logged before the override at `:552-569`. **Use `gChosenMoveByBattler[0]`**: `0x02024274`, `u16[4]`, in sym, never read today. The slot is `gBattleStruct->chosenMovePositions[0]` (heap `+0x80`, hand-computed, UNVERIFIED). | Set at `battle_main.c:4399`; Encore at `:4192-4197`; reset at `:4004` |
| Predicted [min, max], crit_max | Yes, from inputs | `BattleStrategyUtil(state).calculate_move_damage_range(move, me, foe, is_critical_hit)` (`_util.py:165-242`). ⚠ Attacker, defender and util **must come from ONE snapshot**: `attacker in own_side` compares raw `gBattleMons` bytes (`battle_state.py:370-377`, `:479-483`). A mixed snapshot turns `attacker_is_player` False (`_util.py:301-308`), drops the badge boosts (`:336-343`) and under-predicts by about 10%, which would read as a false FAIL. | n/a |
| Foe PID | Yes | `BattlePokemon.personality_value`, `gBattleMons[1]+0x48` (`battle_state.py:673-675`). Get the foe via `battle_state.opponent.left_battler` (`:396-402`), which can be None. ⛔ Not `get_opponent()`: that returns `gEnemyParty[0]` (`pokemon.py:1536-1546`), the wrong mon after a trainer switch. | `include/pokemon.h:291` (`personality` at `0x48`) |
| Foe species | Yes | `.species`, `+0x00` (`battle_state.py:491-493`). Transform rewrites it, which a PID-and-species check will read as "changed". | `include/pokemon.h:262` |
| Foe HP / maxHP | Yes | `.current_hp` `+0x28`, `.total_hp` `+0x2C` (`battle_state.py:622-634`) | `include/pokemon.h:282`, `:285` |
| Foe HP "at the next [TURN]" | Yes | The handler's own entry read, `battle_state` at `battle_action_selection.py:115`. **Reuse that object; do not call `get_battle_state()` again.** | HP is final after `BattleTurnPassed` (`battle_main.c:3956-4027`) |
| Foe fainted | Yes | `gBattleResults+0x01` (`opponentFaintCounter`), already read at `story_mode.py:2500`. Also HP 0, a PID change at the after-read, or the battle ending. | `include/battle.h:237` |
| Weather | Yes | `BattleState.weather` from `gBattleWeather` (`battle_state.py:311-322`). The bit masks match the decomp. | `include/constants/battle.h:232-244` |
| Foe poisoned, burned or toxic | Yes | `.status_permanent`, `+0x4C` (`battle_state.py:704-706`; `StatusCondition.from_bitfield`, `pokemon.py:831-845`) | `include/constants/battle.h:117-121` |
| Foe knows recoil, crash, drain, heal or Substitute | Yes (the full moveset) | `.moves` from `+0x0C` (`battle_state.py:518-533`). ⚠ The list **skips empty slots** (`:524-525`), so its positions are not slot numbers; read PP by slot from raw `+0x24+slot`. Dispatch on `move.effect` (effects in `modules/data/moves.json`: RECOIL (includes Struggle), DOUBLE_EDGE, RECOIL_IF_MISS, ABSORB, DREAM_EATER, RESTORE_HP, SOFTBOILED, MORNING_SUN, SYNTHESIS, MOONLIGHT, REST, SUBSTITUTE, …), never on names. **Better:** `gChosenMoveByBattler[1]` gives the move the foe actually *chose this turn*, which excludes less. | Chosen move: `battle_main.c:4399` |
| Foe held item | Yes | `.held_item`, `+0x2E` (`battle_state.py:661-667`). A berry already eaten reads 0, so it cannot trigger a second time. | `include/pokemon.h:286` |
| Rough Skin | Yes, but **it is OUR ability** | `own_side.active_battler.ability` (`battle_state.py:565-570`, derived from species + `abilityNum`). ⚠ Trace, Skill Swap and Role Play change only the live byte `+0x20`: `ability_n` (`:572-574`) with `get_ability_by_index` (`pokemon.py:1495`). | `data/battle_scripts_1.s:4184-4187` |
| Foe switched | Yes (after the fact); the intent too | PID or species differs at the after-read. The intent is `gChosenActionByBattler[1] == 2` at the selection exit. | `battle_ai_switch_items.c:429`, `:543`; `B_ACTION_SWITCH` `include/battle.h:29` |
| Foe used a bag item | ❌ **Not read today** | `gChosenActionByBattler[1] == 1` (`B_ACTION_USE_ITEM`) at the selection exit: `0x0202421c`, in sym. Cross-check: `gBattleResources→battleHistory→trainerItems[]` loses the item at CHOICE time (`battle_ai_switch_items.c:938`). The pointer chain is `gBattleResources` (`0x020244a8`) `+0x18` → `BattleHistory`, with `trainerItems` at `+0x48` (`u16[4]`) and `itemsNo` at `+0x50`, hand-computed from `include/battle.h:190-203`, `:222-232`, UNVERIFIED. The chosen item is `gBattleStruct->chosenItem[(1/2)*2 = 0]` (heap `+0xC0`, a truncated `u8`; `battle_ai_switch_items.c:937`). | Heal rule at `battle_ai_switch_items.c:870` (the spec says `:866`) |
| Leech Seed, Nightmare, Curse, Wrap family on the foe | Yes | `.status_temporary` (`battle_state.py:708-710`, `:118-196`): LeechSeeded (`gStatuses3` bit 2), Nightmare (status2 bit 27), Cursed (bit 28), Wrapped (bits 13-15) | `battle_util.c:1505`, `:1557`, `:1577`, `:1588`; bits at `include/constants/battle.h:140`, `:151-152`, `:159` |
| Wish | ❌ Not read today | `gWishFutureKnock` (`0x020243d0`, size `0x2C`, in sym): `wishCounter[1]` at `+0x21`. When it equals 1 at the before-read, the Wish heals at the end of this turn. | Struct at `include/battle.h:164-174`; heal at `battle_util.c:1315-1326` |
| Ingrain | Yes | `TemporaryStatus.Rooted` (`gStatuses3` bit 10, `battle_state.py:175-176`) | `battle_util.c:1476-1477` |
| Foe confused | Yes | `TemporaryStatus.Confused` (status2 bits 0-2, `battle_state.py:120-121`). The self-hit is `datahpupdate BS_ATTACKER` with no IGNORE_BIDE (`data/battle_scripts_1.s:3801-3811`), so it contaminates `gBideDmg` as well. | `include/constants/battle.h:129` |
| Foe's chosen action this turn | ❌ Not read today | `gChosenActionByBattler[1]` at the selection exit. Values: 0 USE_MOVE, 1 USE_ITEM, 2 SWITCH, 3 RUN (a fleeing roamer or Safari foe rewrites it at `battle_main.c:4362-4370`), 0xFF NONE. | `include/battle.h:27-44` |
| **Not in the spec, but needed:** foe's chosen move | ❌ | `gChosenMoveByBattler[1]` at the selection exit. If the action is USE_MOVE but the move is 0 (MOVE_NONE), the foe is Struggling or locked in; exclude it. | `battle_main.c:4399`; the no-valid-moves path is at `:4181-4190` |
| **Not in the spec:** Future Sight or Doom Desire landing on the foe | ❌ | `gWishFutureKnock.futureSightCounter[1]` at `+0x01`; a value of 1 means it lands this turn. It contaminates the HP difference but not `gBideDmg` (the flag set at `battle_util.c:1783`). | `battle_util.c:1798-1813` |
| **Not in the spec:** foe Substitute already up | Yes | status2 bit 24 plus `substitute_hp` (`battle_state.py:744-746`; `gDisableStructs+0x0A`) | `battle_script_commands.c:1865-1892` |
| **Not in the spec:** foe semi-invulnerable or Minimized | Yes | `TemporaryStatus.InTheAir`, `Underground`, `Underwater`, `Minimized` (`battle_state.py:167-174`, `:189-190`) | `data/battle_scripts_1.s:237-240` (Surf ×2 against a diving foe) |
| **Not in the spec:** Mud Sport or Water Sport | Yes | `TemporaryStatus.Mudsport` or `Watersport` on any battler (`battle_state.py:185-188`). The calculator leaves them as a "todo" (`_util.py:402-406`). | `pokemon.c:3215-3218` |
| **Not in the spec:** our Flash Fire boost | ❌ | `gBattleResources` `+0x04` → `ResourceFlags.flags[0] & 1` (pointer; hand-computed, UNVERIFIED). Unmodelled (`_util.py:518`). | `pokemon.c:3367`; set at `battle_util.c:2700`; `include/battle.h:63-68` |
| **Not in the spec:** our move actually executed | Yes, indirectly | The PP of the chosen slot drops by 1, or by 2 against Pressure. Sleep, freeze, full paralysis, flinch and a confusion self-hit skip `ppreduce`, while a MISS still spends PP (`data/battle_scripts_1.s:242-247` vs `:273-275`). Raw byte `gBattleMons[0]+0x24+slot`. | As cited |
| **Not in the spec:** Reflect or Light Screen on the foe's side | Yes | `opponent.reflect_timer` and `lightscreen_timer` (`battle_state.py:437-443`). The game tests the `gSideStatuses` bits (`pokemon.c:3267`, `:3318`; symbol `gSideStatuses` `0x0202428e`, not read); the timer and the bit move together. | `include/battle.h:149-162` |
| **Not in the spec:** Spikes on the foe's side | Yes | `opponent.spikes_amount` (`battle_state.py:457-459`). Relevant to `gBideDmg`: a switch-in taking Spikes has no IGNORE_BIDE (`data/battle_scripts_1.s:3403-3404`). | as cited |
| Turn counter (for pairing) | Yes, but read it **directly** | `read_symbol("gBattleResults", offset=0x13, size=1)`. Not `battle_state.current_turn` (KI-108). It saturates at 0xFF and does not increment on the turn the battle ends (`battle_main.c:3988-3998`). | `include/battle.h:247` |
| **Proposed primary observable:** `gBideDmg[1]` | ❌ | `read_symbol("gBideDmg", offset=4, size=4)` as `s32`; `0x020241f8`, size 0x10, in sym | §5 |

**Symbol-table presence** (all at `pokeemerald.sym`, English): gBattleMons 02024084/0x160; gStatuses3 020242ac/0x10; gDisableStructs 020242bc/0x70; gBattleWeather 020243cc/2; gWishFutureKnock 020243d0/0x2c; gChosenActionByBattler 0202421c/4; gChosenMoveByBattler 02024274/8; gBideDmg 020241f8/0x10; gBideTarget 02024288/4; gBattleStruct 0202449c/4 (pointer); gBattleResources 020244a8/4 (pointer); gBattleResults 03005d10/0x44; gSideTimers 02024294/0x18; gSideStatuses 0202428e/4; gActionsByTurnOrder 0202407a/4; gBattlerByTurnOrder 0202407e/4; gCurrentTurnActionNumber 02024082/1; gProtectStructs 0202433c/0x40; gSpecialStatuses 0202437c/0x50; gBattleMoveDamage 020241f0/4; gHpDealt 020241f4/4; gCritMultiplier 02024211/1; gLastMoves 02024248/8; gLastLandedMoves 02024250/8; gLastHitBy 02024270/4; gHitMarker 02024280/4; gBattleScripting 02024474/0x28; gLastUsedItem 02024208/2. The table has **no** `gFieldStatuses`, `gIsCriticalHit` or `gBattleTurnCounter`: those are pokeemerald_expansion names, not vanilla.

⚠ **Japanese ROMs:** the newly needed symbols (gChosen\*, gBideDmg, gWishFutureKnock, gBattleResources, gBattleStruct) have no J patch in `patches/language/pokeemerald.yml` (it patches gBattleMons, gStatuses3, gDisableStructs and others at `:505-521`). M1b should refuse to run on J.

---

## 2. Values that are NOT readable at the next `[TURN]` (and why)

| Tempting symbol | Why it is useless after the turn |
|---|---|
| `gProtectStructs[1].physicalDmg` / `.specialDmg` (the exact damage our move dealt) | Written at `battle_script_commands.c:1941`, `:1957`; the whole struct is zeroed by `TurnValuesCleanUp(FALSE)` in `BattleTurnPassed` (`battle_main.c:3974`, `:4871-4873`) |
| `gSpecialStatuses[1]` | Cleared at every `HandleAction_ActionFinished` (`battle_util.c:663`) |
| `gBattleMoveDamage` | Zeroed in `BattleTurnPassed` (`battle_main.c:3982`) and overwritten by end-turn effects |
| `gHpDealt` | Never reset; it holds the turn's LAST `datahpupdate` (end-turn effect or the foe's hit), `battle_script_commands.c:1923`, `:1927` |
| `gCritMultiplier` (the crit flag) | Set by `critcalc` (`battle_script_commands.c:1283-1285`), then overwritten to 1 by the trainer AI's damage scoring during the next selection (`battle_ai_script_commands.c:1192`, `:1477`, …; `battle_ai_switch_items.c:752`) and at `:3625`. **Whether our hit was a crit is not readable at the after-read.** Either tag readings in (max, crit_max] as "crit or under-prediction, ambiguous", or add a per-frame text sniff (UNVERIFIED) |
| `gLastLandedMoves[1]` | Zeroed when the attacker's action finishes (`battle_util.c:675`), so it depends on move order |
| `gActionsByTurnOrder` / `gBattlerByTurnOrder` | Scrambled at end of turn (finding 3) |
| `gChosenActionByBattler` / `gChosenMoveByBattler` | Reset in `BattleTurnPassed` (`battle_main.c:4001-4005`) |

---

## 3. Where in the turn loop to read, so that one pair brackets exactly one of our moves

**BEFORE, at the selection exit.** This is the fall-through of `while … get_main_battle_callback() in ("HandleTurnActionSelectionState","sub_8012324")` (`battle_action_selection.py:173`), just before `handle_battle_action_selection` returns, in the same frame.
- **Guard:** the direct turn counter still equals the turn value of the decision's snapshot, and the foe's HP equals that snapshot's HP. A mismatch means "late read", so exclude the sample.
- **Filter:** `gChosenActionByBattler[0] == 0` (USE_MOVE) and `gChosenMoveByBattler[0] != 0`. A zero move means a locked-in or recharge turn, where no choice is emitted (`battle_main.c:4159-4165`).
- **Read:** the turn counter; both chosen actions and moves; a pure snapshot of `gBattleMons`, `gStatuses3`, `gDisableStructs`, weather and side timers; `gBideDmg[1]`; `gWishFutureKnock`; `opponentFaintCounter`; and for trainer battles `trainerItems`. Compute min, max and crit_max for `gChosenMoveByBattler[0]` from that one snapshot.

**AFTER, at the next selection entry.** This is `battle_state = get_battle_state()` at `battle_action_selection.py:115`: reuse that object, and read the turn counter directly. Accept the pair only if the counter is T+1.
- If the battle ended during turn T, read at `battle_handler.py:414`, the loop exit. `gBideDmg` is a static EWRAM global and survives. Do not dereference `gBattleStruct` or `gBattleResources` there, because they are NULL after `FreeBattleResources` (`battle_util2.c:55-65`). Whether `gBattleMons` survives until then is UNVERIFIED.

**Why these two points bracket exactly one move of ours:** between them, exactly one `RunTurnActionsFunctions` pass runs, and in singles our battler has one action slot. Remaining edge cases, each of which the filters above exclude:
- a charge turn of a two-turn move (no damage);
- a multi-hit move (the difference is the sum of the hits);
- a move called by Metronome, Sleep Talk, Assist or Mirror Move (exclude by the effect of `gChosenMoveByBattler[0]`);
- our mon did not act: PP unchanged, or our PID changed because it fainted first or was Roared out;
- a double battle, where two of our moves fall in one pair. Keep M1b to singles.

**Frame safety (the inertness contract `[A-S10]`):** both points are existing frames. M1b must add no `yield`, press no button, and not call `get_battle_state()` (see §4). The code idiom is one generator yield per emulator frame (e.g. `_KI93_DISMISS_PERIOD`, `battle_action_selection.py:139-142`); that is inferred, UNVERIFIED as a formal contract.

**Optional mid-turn read.** Two facts exist only during the turn: who moved first, and the crit. `handle_battle`'s default branch (`battle_handler.py:410-412`) already runs every frame while the turn executes. An observe-only per-frame read placed there could latch `gBattlerByTurnOrder` once `gBattleMainFunc == RunTurnActionsFunctions`. This is UNVERIFIED; with the exclusions, a conservative design can skip it.

---

## 4. KI-108: can it corrupt M1b's reads?

**The mechanism** (`05-KNOWN-ISSUES.md:3066-3091`, re-read in the tree):
- `get_battle_state()` returns the cached object when `age_in_frames == 0` (`battle_state.py:809-810`). Otherwise it builds a new object and returns it (`:812-827`).
- The setter keeps the OLD object when `old == new` (`state_cache.py:293-297`).
- `__eq__` omits `_battler_party_order` and `_current_turn` (`battle_state.py:249-263`).

**What that means for M1b:**
- **HP, PID, species, status1/2/3, moves, PP, held item, ability bits, stat stages, types, weather, side timers:** they are all bytes of compared fields, so a stale object is byte-identical on them to the frame's first read. **These cannot be corrupted.**
- **`current_turn`: it can be corrupted.** It goes stale when the handler's read at `:115` is not the first in its frame and no compared byte changed across the turn. That is rare, because any executed move spends PP in `gBattleMons`, but it is possible (for example, both sides fully paralysed). The debug GUI's Battle tab (`gui/debug_tabs.py:427`) is a known earlier caller. ⇒ Pair on a direct read of `gBattleResults+0x13`.
- **Party order:** M1b does not need it.
- **New direct `read_symbol` reads** (gChosen\*, gBideDmg, …) bypass the cache entirely (`memory.py:43-70`), so KI-108 cannot touch them.
- **The real risk is M1b itself.** Per KI-108, the KI-96 swap re-map (~`:803`), the KI-101 item target (~`:1107`) and `battle_move_replacing.py` ~`:149` are correct only because each is the first caller in its frame. An extra `get_battle_state()` from M1b in such a frame would demote them to second caller. That changes behaviour, and the DMGAUDIT-on/off `[BATTLE]` identity would fail, or worse. ⇒ **M1b's exit read should be a PURE read**: build a `BattleState(...)` from `read_symbol` exactly like `battle_state.py:812-824`, without assigning `state_cache.battle_state`. This is KI-108's own fix candidate 2. At the after-read, reuse the handler's `:115` object.

---

## 5. `gBideDmg[1]` as the primary observable (decomp mechanism; live UNVERIFIED)

**Mechanism** (`battle_script_commands.c:1844-1929`):
- `if !(MOVE_RESULT_NO_EFFECT)` → if the target has a Substitute: damage to the sub, **no Bide**. Otherwise, if damage < 0: heal, **no Bide**. Otherwise, unless IGNORE_BIDE is set, `gBideDmg[target] += gBattleMoveDamage` (`:1912`), **before** HP is capped (`:1920-1929`).
- `gBattleMoveDamage` at that point already includes the random factor and the Focus Band, Endure and False Swipe clamp (`Cmd_adjustnormaldamage`, `:1658-1696`). Those clamps can only lower it, which is the safe direction.
- The only writes are `:1912` and `:7125` (`Cmd_setbide`); I grepped battle_main.c, battle_util.c, battle_util2.c, battle_script_commands.c, battle_ai_script_commands.c, battle_controllers.c, recorded_battle.c and battle_tv.c. So it is never reset at battle start or on a switch-in: **use differences only.**

**Contributions that DO land in `gBideDmg[1]`** (no IGNORE_BIDE in these scripts, `data/battle_scripts_1.s` lines as shown):
- our damaging hits;
- the foe's recoil (`:3941-3944`), crash (`:853-869`), confusion self-hit (`:3801-3811`), Substitute cost (`:1085-1099`), Belly Drum (`:1776-1785`), Ghost Curse cost (`:1511-1526`) and Pain Split (`:1239-1252`);
- our Rough Skin (`:4184-4187`);
- Spikes on a switch-in (`:3403-3404`);
- Liquid Ooze on our side against a foe's drain (UNVERIFIED script path).
⇒ Exclude by the foe's chosen move effect, foe confusion at the before-read, our ability, and Spikes combined with a PID change.

**Contributions that do NOT land in it:** AI potions and Full Restores, drain heals, Rest and Recover, berries, Leftovers, Shell Bell (all negative damage); poison, burn, toxic, Leech Seed, Nightmare, Curse ticks and Wrap (`battle_util.c:1464`); sand and hail (`data/battle_scripts_1.s:3211`); Future Sight and Doom Desire (`battle_util.c:1783`); Wish (a heal).

**Effect on the design:** the spec's exclusions for items, drain, heal, Wish, Ingrain, end-of-turn effects and weather chip become **reporting strata, not discards**. The held-item exclusion shrinks to items that change our damage but are not modelled, such as Focus Band (a clamp, safe direction). The calculator already models Soul Dew, Deep Sea Scale and Metal Powder (`_util.py:368-375`). **KO samples become valid** (the uncapped roll), and they are probably the majority for a strong team. This matters directly for step 12's `damage_upper_bound`.

**Instrument self-check (rule 7; also the fault arm):** on turns with no KO, no heal and no end-of-turn change, `hp_before − hp_after` must equal `bide_after − bide_before`. Log the disagreement count per run. **Fault:** reading `gBideDmg[0]` (offset 0 instead of 4) must break that equality on clean turns. That proves the reader is pointed at the right battler.

---

## 6. The spec's decomp citations, re-checked at f90719c4

| Spec says | Actual |
|---|---|
| `battle_ai_switch_items.c:429` `ShouldSwitch` | ✓ definition at `:429` |
| `:541` | This is the `BATTLE_TYPE_TRAINER` gate; `ShouldSwitch()` is called at `:543` |
| `:528` `AI_TrySwitchOrUseItem` | ✓ |
| `:866` heal rule | **`:870`**; `:866` is `if (paramOffset == 0)` |
| `battle_util.c:1315` Wish, `:1476` Ingrain, `:1505` Leech Seed, `:1557` Nightmare, `:1577` Curse, `:1588` Wrap | ✓ all six |
| `[TURN]` is emitted with `category="BATTLE"` (`battle_action_selection.py:535-537`) | ✓ (the call spans `:534-538`) |

---

## 7. Side findings in our code (outside M1b's scope; they are traps for its author)

- `battle_state.py:728-734`: `encored_move` reads `disable_struct[0x04:0x06]`, which is `disabledMove`. The decomp puts `encoredMove` at `+0x06` (`include/battle.h:73-74`). `can_use_move` (`:547-559`) uses it. M1b avoids it by reading `gChosenMoveByBattler[0]`.
- `_util.py:93`: the escape-attempts read neither dereferences `gBattleStruct` nor uses the right offset. By a hand count, `runTries` is at `+0x6C` (anchored on the decomp's own `field_93` name, `include/battle.h:402`; `expGetterMonId` at `+0x10` matches `battle_move_replacing.py:147`'s intended offset). UNVERIFIED live.
- `battle_state.py:590-620`: `modified_stats()` indexes Python **sets** (`{10, 40}[0]`), so any call raises TypeError. The calculator uses `_calculate_modified_stat` instead, so it looks unused. UNVERIFIED that nothing calls it.

---

## 8. UNVERIFIED, and the observe-only probe that would settle it

1. `gBideDmg[1]`'s difference equals the HP difference on clean turns, and holds the uncapped roll on a KO. **Probe:** one wild battle and one trainer battle with a hit that does not KO and one that does. Print both differences beside `hp_before`.
2. `gChosenActionByBattler[1]` and `gChosenMoveByBattler[1]` are final at the selection exit, and (for information) already set at our decision frame.
3. `gBattleMons[1]` and `gBideDmg` are still intact at `battle_handler.py:414` after a battle ends.
4. The hand-computed heap offsets: `BattleStruct.chosenMovePositions` +0x80, `chosenItem` +0xC0; `BattleResources.flags` +0x04, `battleHistory` +0x18; `BattleHistory.trainerItems` +0x48.
5. The selection-exit read happens a few frames before the first action runs, so no HP has changed yet.

Everything else above was read in the decomp or our tree at the cited lines.
