# 2026-09-27 — USER RULING 22 (Shedinja): decomp check and bot readiness — a NOTE

> ⛔ **A NOTE, NOT A SOURCE OF TRUTH.** One read-only Claude agent (recon), then a second one told to REFUTE each
> key claim against the decomp / logs / code (verification). Line numbers refer to the branch `wt/r20fly` or the
> running sandbox as each section says. Verify a load-bearing claim yourself before code depends on it.

## Recon

USER RULING 22 (Shedinja): decomp check and bot readiness (a NOTE, not truth)

Decomp files were fetched from pret/pokeemerald master. Bot code was read at C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot (branch wt/r20fly). I edited nothing and ran nothing.

## A. Decomp (MEASURED: code read, not run live)

1. **Only one thing gates Shedinja: a free party slot.** `CreateShedinja` in `src/evolution_scene.c:548-583` checks two things:
   - `gEvolutionTable[preEvo][0].method == EVO_LEVEL_NINJASK`
   - `gPlayerPartyCount < PARTY_SIZE` (:551)
   There is **no Poké Ball check and no item is consumed** anywhere in :548-583. The ball requirement is a Gen 4+ rule.
   - Code search found `CreateShedinja` only in this file, and its only call is at :814. The trade scene's end state (:1219) does not call it.
2. **Eggs take up the slot.** `CalculatePlayerPartyCount` (`src/pokemon.c:4481-4492`) counts every slot whose species is not NONE.
3. **Nincada evolves at level 20.** `src/data/pokemon/evolution.h:141-142`: `{EVO_LEVEL_NINJASK, 20, NINJASK}, {EVO_LEVEL_SHEDINJA, 20, SHEDINJA}`. The check is `param <= level` (`pokemon.c:5576-5578`), so it fires at 20 or above. An Everstone blocks it (`pokemon.c:5521-5522`).
4. **PID is shared.** Shedinja is built with `CopyMon` (:556), and `CopyMon` is a plain `memcpy` (`pokemon.c:4420-4423`). Personality and OT ID are never rewritten, so **Shedinja keeps Ninjask's PID.**
   - Overwritten: species (:557), nickname set to "SHEDINJA" (:558), held item, markings, ribbons, status and mail cleared (:559-570), stats recalculated (:572). Max HP is forced to 1 (`pokemon.c:2845-2847`).
   - It goes into slot `gPlayerParty[gPlayerPartyCount]` (:554), which is the end of the party.
   - Pokédex #292 is marked seen and caught (:575-576).
5. **Shedinja copies the evolved Ninjask, not the Nincada.** The species is set to Ninjask at :764 (state `SET_MON_EVOLVED`). `CreateShedinja` runs later, at `EVOSTATE_END` (:813-814), after the move-learn states. So Shedinja gets Ninjask's moves after the three level-20 prompts (Double Team, Fury Cutter, Screech; `level_up_learnsets.h:3935-3937`).
6. **Evolution can be triggered from two places, both cancellable:**
   - **After a battle:** only if `gLeveledUpInBattle != 0` and `gBattleOutcome == B_OUTCOME_WON` (`battle_main.c:5160-5167`). `TryEvolvePokemon` then calls `EvolutionScene(..., TRUE, i)` (:5180-5206). A battle that ends in a catch, flight or whiteout does not evolve anything.
   - **Rare Candy:** `party_menu.c:5095-5105` calls `BeginEvolutionScene(..., TRUE, slot)`, which runs through the same `EVOSTATE_END`, so Shedinja is created here too.
7. **Pressing B cancels Shedinja.** Cancel only happens when all of these hold (:638-645):
   - `gMain.heldKeys == B_BUTTON` exactly
   - the task is in state `EVOSTATE_WAIT_CYCLE_MON_SPRITE` (enum index 8, :588-604)
   - the graphics task is active
   - the can-stop bit is set
   Cancelling sets `tEvoWasStopped = TRUE` (:847), and :813 skips `CreateShedinja` when that flag is set. So a cancelled evolution produces no Shedinja.

## B. The bot as it stands (MEASURED: code read)

- **Evolution handler.** `handle_evolution_scene` (`modules/battle_evolution_scene.py:16-61`):
  - It presses `"B" if should_stop else "A"` (:60).
  - `should_stop` starts as True (:19). It asks the strategy once `task_state >= 4` (:52-58).
  - So B is pressed for states 0-3 even when the evolution will be allowed. INFERRED harmless: cancel needs state 8, and states 4-7 take many frames.
- **Story training battles always allow evolution.** `LevelUpTravelBattleStrategy.should_allow_evolution` returns True (`plugins/custom_modes/story_mode.py:678-687`). `StoryItemBattleStrategy` (:690) and `SwapTrainBattleStrategy` (:1158) inherit it.
- **Catch, shiny and flee battles would cancel.** `StoryCatchStrategy`, `StoryDexCatchStrategy`, `StoryShinyCatchStrategy` and `StoryFleeStrategy` inherit `DefaultBattleStrategy.should_allow_evolution` (`modules/battle_strategies/default.py:161-168`). That returns `... and not stop_evolution`, and `profiles/battle.yml:19` sets `stop_evolution: true`. **So those strategies would press B and cancel.**
  - INFERRED: this only matters if such a battle ends WON with a level-up. The catch strategy never uses damaging moves (story_mode.py:71-74), so the realistic route is a poison tick killing the wild Pokémon. Rare, but it would silently lose the Shedinja.
- **Battle-handler routing.** When the evolution task is active, battle_handler.py:368-371 and :384-385 send control to `handle_evolution_scene`. The default B-spam at :403-405 is only reached when the task is inactive.
- **PID-twin handling already exists.** It is keyed on `(PID, species)`: `pokemon_party.py:99-107`, `pc_trip.py:726-727`, `victory_road.py:597-606`, `pokemon.py:875-899`.
- **Minor doc error.** `modules/debug_logger.py:665` says Shedinja is "a COPY of Nincada". It is a copy of the just-evolved Ninjask (point A5). The PID claim there is still right.
- **The duplicate Nincada is blocked today.** The gate is `decide_dex_catch` at `story_mode.py:1881-1882` (`species_dex in owned_dex → "already owned"`). `owned_dex` comes from the Pokédex owned flags (:2425), so Nincada #290 stays owned for the rest of the run. The Shedinja exception must go before :1881.
- **Right counter for the reservation.** `party_accounting.game_party_count()` (`modules/party_accounting.py:152-162`) reads `gPlayerPartyCount`, the exact value `CreateShedinja` tests. It counts eggs, and so does the game.

## C. Where the "keep a slot free" rule has to live (INFERRED)

This is a **capacity reservation**, not a catch rule. Every path that can add a party member must honour one shared predicate. Sites I found:

- **Catch sites:**
  - the full-party branch of `decide_dex_catch` (:1902-1949)
  - the HM catch branch, `< 6` (:3775)
  - the counter branch (:3804, which deliberately has no party gate; at 5 of 6 it would fill the slot)
  - the checks at :3875 and :3961
- **Withdraw path:** `pc_trip.party_has_room_for_withdraw` / `withdraw_from_box` (`pc_trip.py:556`, `:584`). The RULING 20 heal withdraw of owed counters goes through here.
- **Gift Pokémon and eggs:** not grepped. INFERRED to be another way the slot can be filled.

The rule only has to hold at one moment: the end of the WON battle in which the Nincada reaches 20 or above. A catch and an evolution cannot happen in the same battle (point A6).

## D. What the bot must do, in order

1. **Detect a missed Shedinja:** Pokédex #292 is not owned, but #291 (Ninjask) is. The dex flag is reliable because `CreateShedinja` always sets it (A1).
2. **Add a narrow exception before `story_mode.py:1881`:** allow a wild Nincada catch only when #292 is not owned and no Nincada is already in the party or PC. The catch must land in the **party**, so there must be a free slot when it is caught (a full-party catch goes to the PC).
3. **Arm the reservation** while that Nincada is below level 20 and #292 is not owned: `game_party_count() <= 5` after every party-adding action. Deposit first if needed, counting eggs.
4. **Make sure Nincada holds no Everstone** (pokemon.c:5521).
5. **Train it only in battles whose strategy allows evolution** (the LevelUpTravel family). Alternatively, override `should_allow_evolution` to True for species Nincada in the catch and flee strategies as well.
6. **Let the three level-20 move prompts run** through the existing move-replacement handler. Shedinja inherits whatever Ninjask ends up with.
7. **Check the result by identity, never by slot or count:**
   - a party member exists with species Shedinja and the Ninjask's PID, at index `gPlayerPartyCount - 1`
   - Pokédex #292 is owned
8. **Then release the reservation.** Remove the exception once #292 is owned, so it cannot fire twice.

**Open question:** whether a Shedinja gets boxed afterwards is the user's call. Boxing needs the `(PID, species)` identity, because the twins share a PID.

## Adversarial verification

Adversarial check of 12 Shedinja claims (this is a NOTE, not truth). I pulled pret/pokeemerald with `gh api` into the scratchpad and read the repo code under `C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot`. With `cmp`, battle_evolution_scene.py, debug_logger.py, party_accounting.py and default.py are identical to the running sandbox. story_mode.py and battle.yml differ, but the cited lines match in both except one offset noted in claim 10. I wrote nothing to either tree.

Result: 12 of 12 CONFIRMED on their citations, none REFUTED. Five need tightening before code relies on them:

- **Claim 10 is the one that matters.** The already-owned gate (story_mode.py:1881-1882) covers only the decide_dex_catch route. The HM-learner branch (story_mode.py:3761-3785) and the counter-catch branch (:3860-3894) return StoryCatchStrategy with no owned check. So 'a duplicate Nincada is blocked today' is not universal. Whether Nincada can actually become an HM or counter target is INFERRED, not measured.
- **Claim 3 wording:** Shedinja goes to `gPlayerParty[gPlayerPartyCount]` (evolution_scene.c:554/:556), the first slot after the counted party. That is not always slot 6, and it overwrites whatever sits at that index.
- **Claim 4 parenthetical:** the L20 moves (Double Team, Fury Cutter, Screech) are learned only if the evolution happens at exactly L20 (pokemon.c:3028/3036). A natural L20 Nincada already has four moves, so each goes through the replace prompt. Shedinja keeps whatever moveset the learning step left.
- **Claim 5:** the B-cancel check has a fourth condition the claim leaves out: the evolution graphics task must be active (evolution_scene.c:640).
- **Claim 1:** there is a third precondition outside the function: the evolution must not have been cancelled (caller check at :813).

Also measured: the bot's B presses in states 0-3 are harmless, because the game only accepts a cancel in EVOSTATE_WAIT_CYCLE_MON_SPRITE (state 8, evolution_scene.c:595).

Key paths:
- C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot/modules/battle_evolution_scene.py
- C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot/plugins/custom_modes/story_mode.py
- C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot/modules/debug_logger.py
- C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot/modules/party_accounting.py

Decomp copies are in the scratchpad `decomp/` folder.

- **[CONFIRMED]** 1. CreateShedinja's only gates are Nincada's evo method and a free party slot (gPlayerPartyCount < PARTY_SIZE); no Poke Ball is checked or consumed  
  How: MEASURED from the decomp (gh api raw). evolution_scene.c:548 opens CreateShedinja; :551 is `if (gEvolutionTable[preEvoSpecies][0].method == EVO_LEVEL_NINJASK && gPlayerPartyCount < PARTY_SIZE)`; the body (548-583) has no bag or item read and no RemoveBagItem. Caveat: the caller at :813 also requires !tEvoWasStopped, so there is a third precondition outside the function.
- **[CONFIRMED]** 2. Nincada evolves at level 20 (param <= level, so 20+); an Everstone blocks it  
  How: MEASURED. evolution.h:141-142 is {EVO_LEVEL_NINJASK,20,NINJASK},{EVO_LEVEL_SHEDINJA,20,SHEDINJA}. pokemon.c:5576-5578 is `param <= level`. pokemon.c:5521-5523 returns SPECIES_NONE for HOLD_EFFECT_PREVENT_EVOLVE unless the mode is EVO_MODE_ITEM_CHECK. EVO_LEVEL_SHEDINJA has no case in pokemon.c (grep found none), so only the Ninjask entry triggers.
- **[CONFIRMED]** 3. Shedinja is a memcpy of the just-evolved Ninjask, keeping Ninjask's PID and OT; nickname, held item, markings, ribbons, status and mail are reset; it goes to the end slot  
  How: MEASURED. pokemon.c:4420-4423 shows CopyMon is memcpy. evolution_scene.c:556 does the copy. :557 sets the species, :558 the nickname (species name), :559 the held item, :560 markings, :563-566 ribbons, :568 status, :570 mail (:561 also clears ENCRYPT_SEPARATOR). Nothing resets personality or OT. WORDING FIX: the target is gPlayerParty[gPlayerPartyCount] (:554/:556), the first slot after the counted party. That is not necessarily slot 6, and it overwrites whatever sits at that index.
- **[CONFIRMED]** 4. CreateShedinja runs at EVOSTATE_END after the species is set (:764) and after the move-learn states, so Shedinja inherits Ninjask's post-learn moves (Double Team/Fury Cutter/Screech at L20)  
  How: MEASURED. The enum at :601-603 orders SET_MON_EVOLVED, TRY_LEARN_MOVE, END. :764 sets the species to Ninjask. TRY_LEARN_MOVE (:772-802) moves to END only when there is nothing left to learn. :814 calls CreateShedinja(mon). learnsets.h:3935-3937 lists L20 DOUBLE_TEAM, FURY_CUTTER, SCREECH. CAVEAT (INFERRED): the parenthetical is conditional. MonTryLearningNewMove only matches level == current level (pokemon.c:3028/3036), so a Nincada that evolves at L21+ learns none of them. A natural L20 Nincada already has 4 moves (learnsets.h:3915-3918), so each of the three goes through the replace prompt, and Shedinja's moves are whatever the replace/decline answers left.
- **[CONFIRMED]** 5. B-cancel only fires with heldKeys == B_BUTTON in EVOSTATE_WAIT_CYCLE_MON_SPRITE with the can-stop bit set; a cancelled evolution skips CreateShedinja  
  How: MEASURED. The check at :638-641 has four conditions, not three. The claim omits `gTasks[sEvoGraphicsTaskId].isActive` (:640). :643 goes to EVOSTATE_CANCEL, :847 sets tEvoWasStopped = TRUE, :813 then skips CreateShedinja, and :776 also skips move-learning. :160/:168 alias tBits to tCanStop at bit 0. Both battle_main.c:5201 and party_menu.c:5104 pass canStop = TRUE.
- **[CONFIRMED]** 6. Post-battle evolution happens only when the outcome is WON and something leveled; a Rare Candy evolution goes through the same scene and creates Shedinja  
  How: MEASURED. battle_main.c:5160 returns to the overworld if gLeveledUpInBattle == 0 or gBattleOutcome != B_OUTCOME_WON. :5180-5206 calls EvolutionScene(...,TRUE,i). The Rare Candy chain is ItemUseCB_RareCandy (party_menu.c:4955), then Task_TryLearnNewMoves (:5060/:5082), then PartyMenuTryEvolution (:5095-5104), then BeginEvolutionScene, then EvolutionScene (evolution_scene.c:193), which runs the same Task_EvolutionScene that ends at :814. The Pg1-to-TryLearnNewMoves hop between these was INFERRED, not opened.
- **[CONFIRMED]** 7. Party count counts eggs, so an egg occupies the slot Shedinja needs  
  How: MEASURED. pokemon.c:4481-4492 counts while MON_DATA_SPECIES != SPECIES_NONE. pokemon.c:3830-3831 shows MON_DATA_SPECIES returns substruct0->species (or SPECIES_EGG for a bad egg), never NONE for an egg. No SPECIES_EGG exclusion exists. INFERRED: an egg's species field is its real species, which is nonzero.
- **[CONFIRMED]** 8. Bot presses B when should_stop, and should_stop is True by default until task_state >= 4  
  How: MEASURED. worktree sandbox-pokebot/modules/battle_evolution_scene.py (identical to the running sandbox, checked with cmp): :19 `should_stop = True`, :52-58 queries only when task_state >= 4, :60 presses B when should_stop. Nuance: B in states 0-3 cannot cancel, because the game checks state == WAIT_CYCLE_MON_SPRITE (enum index 8, evolution_scene.c:595). An explicit allow_evolution argument (:54/:57, used by modules/modes/util/items.py:351) bypasses the strategy.
- **[CONFIRMED]** 9. Story training strategies always allow evolution; catch/flee/shiny strategies inherit the default, which cancels under profiles/battle.yml stop_evolution: true  
  How: MEASURED. story_mode.py:678-687 returns True inside LevelUpTravelBattleStrategy (class at :354); StoryItemBattleStrategy (:690) inherits it. StoryFleeStrategy(RunAwayStrategy) (:31), StoryCatchStrategy(CatchStrategy) (:58) and Dex/Shiny (:111/:202) define no override: repo-wide grep finds overrides only in default.py, lose_on_purpose.py and _interface.py. RunAway and Catch subclass DefaultBattleStrategy (run_away.py:10, catch.py:23). default.py:161-168 ANDs with `not stop_evolution`. battle.yml:19 is `stop_evolution: true` in both trees, and no per-profile battle.yml exists. INFERRED: a catch or flee battle reaches the evo scene only on a WON outcome (battle_main.c:5160).
- **[CONFIRMED]** 10. A duplicate Nincada is blocked today by the already-owned gate in decide_dex_catch, fed by Pokedex owned flags  
  How: TRUE ONLY FOR THE DEX-CATCH ROUTE. MEASURED: story_mode.py:1881-1882 is `if species_dex in owned_dex: return False` in both trees. :2425 (worktree; :2419 in the running sandbox) builds owned_dex from get_pokedex().owned_species, and pokedex.py:44-53 reads the owned bitfield at 0x10. HOWEVER the HM-learner branch (story_mode.py:3761-3785, target set early_game.py:5024) and the counter-catch branch (:3860-3894) return StoryCatchStrategy with no owned_dex check. The shiny branch (:3751) is also separate. So 'blocked today' is not universal: a Nincada named as an HM or counter target would bypass the gate. Whether that can happen was INFERRED and not measured.
- **[CONFIRMED]** 11. debug_logger.py docstring says Shedinja is a copy of Nincada; it is actually a copy of the evolved Ninjask (PID claim still correct)  
  How: MEASURED. debug_logger.py:665 reads 'Gen 3 creates **Shedinja as a COPY of Nincada**'. The copy source is `mon` at :814, whose species was set to Ninjask at :764, and CopyMon memcpy's the whole struct (pokemon.c:4420-4423), so the PID is shared. The docstring is imprecise about species and correct about the PID.
- **[CONFIRMED]** 12. game_party_count() reads gPlayerPartyCount, the exact value CreateShedinja tests  
  How: MEASURED. party_accounting.py:152-162 returns read_symbol('gPlayerPartyCount', size=1)[0]. pokemon.c:76 declares `EWRAM_DATA u8 gPlayerPartyCount`, so size=1 is correct. evolution_scene.c:551 tests the same symbol without recalculating it first; CalculatePlayerPartyCount runs only afterwards, at :573. Caveat (INFERRED): the value can be stale relative to the physical slots, and the game uses it as-is.
