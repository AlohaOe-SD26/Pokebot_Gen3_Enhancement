# 2026-09-30 — design v2 step 13: the DESIGN REVIEW (three lenses + refuters), verbatim

⚠ **A NOTE, NOT TRUTH.** Model output (subagent returns). Each finding, its refuter verdict where one ran (nits were not refuted), and what each lens checked and found true. The design folds every confirmed finding (its REVIEW section).

# LENS safety

## safety:S13-P1 [blocker] design §2 D7/V1 (DESIGN.md:23-27, :110-117) vs sandbox-pokebot/modules/battle_action_selection.py:1207-1215 (the no-move-menu Struggle loop)
CLAIM: With the flag ON, battler 0's Struggle loop can press A on battler 2's action menu, and the design leaves that path open. Once battler 2 has used an item, its action cursor (byte 2) stays on BAG. The next time battler 0 has no usable move, the loop opens battler 2's bag and drives it blind. The result is either a heal no policy asked for, on battler 0's Pokémon, or a menu loop that only the KI-47 net stops (a derail, or Manual in a harness mode that did not opt in). C1 does not reach this loop, so this is a new hang and derail path.
EVIDENCE: The Struggle loop at bas:1207-1215 presses A while `get_main_battle_callback()` is in HandleTurnActionSelectionState and `get_battle_controller_callback(battler_index=0)` is not a move-menu callback. It checks only battler 0's controller.

The game shows battler 2's action menu while gBattleMainFunc stays HandleTurnActionSelectionState: once battler 0 reaches STATE_WAIT_ACTION_CONFIRMED, battler 2 gets its ChooseAction (battle_main.c:4143-4172). A battler with no usable move goes through BattleScript_NoMovesLeft (battle_util.c:1125-1140; battle_main.c:4186-4193), so battler 0's move menu never opens. The loop therefore keeps pressing A into battler 2's menu.

A on cursor 1 means B_ACTION_USE_ITEM (battle_controller_player.c:249-256). Byte 2 is written only by a switch-in, battle start, HandleAction_Switch and a reset message (battle_controller_player.c:2190, :3106-3110; battle_main.c:3203, :3285; battle_util.c:299), so after battler 2's item it stays 1 until our next FIGHT scroll. gBattleMainFunc does not change while the bag is open (it is read by get_main_battle_callback, battle_state.py:835-836), so the A presses go on: the bag item → USE → the party menu, which opens on slot 0 (party_menu.c:524-525). In battle order, slot 0 is battler 0's active Pokémon (party_menu.c:5970-5983). That Pokémon is healed if damaged. At full HP the game says 'won't have any effect' and returns to the bag (party_menu.c:4413-4425, :4476-4477), and the A presses repeat until the KI-47 net fires at 3000 frames (battle_handler.py:174, :298-316).

The strategy does reach this loop: when every move is at 0 PP it returns use_move(0) (story_mode.py:612-617). The design's C1 changes only the scroll before this loop.
FIX: Behind DOUBLEITEMS (so D-OFF still equals base), add an exit condition to the loop at bas:1208-1211. In a double, when battler_index==0 and `get_battle_controller_callback(2)` reaches HandleInputChooseAction, return without pressing, and let the handler make battler 2's decision. Add a fake-emulator gate row: controller(2) enters HandleInputChooseAction mid-loop, and no A may be pressed after that frame. Add a mutant that removes the exit. Name this path in V1/D7 and in §6's residuals.
VERDICT: refuted=False corrected=should-fix
REASONING: The mechanism checks out against both the decomp and our code, and the design does not handle it. I could not refute it. I am downgrading it from blocker because it is very hard to reach, and when it does fire the damage is limited.

WHY IT IS REAL:
(1) The loop at sandbox-pokebot/modules/battle_action_selection.py:1208-1215 presses A while gBattleMainFunc is HandleTurnActionSelectionState. It checks the controller of battler_index (0) only. get_main_battle_callback reads gBattleMainFunc (battle_state.py:835-836), not gMain.callback1/2, so the loop keeps pressing A while the bag and the party menu are open.
(2) A battler whose moves are all unusable goes through AreAllMovesUnusable → STATE_SELECTION_SCRIPT → STATE_WAIT_ACTION_CONFIRMED_STANDBY (battle_main.c:4184-4191; battle_util.c:1125-1139). An Encored battler skips its move menu the same way (:4192-4197). Once battler 0 reaches STATE_WAIT_ACTION_CONFIRMED, battler 2 gets EmitChooseAction (:4145-4148, :4168). So the loop presses A into battler 2's action menu. This already happens in the base code: with byte 2 = 0, it blindly commits battler 2's FIGHT → move → target.
(3) A reads gActionSelectionCursor[gActiveBattler], and 1 means USE_ITEM (battle_controller_player.c:249-256). Byte 2 is reset only by a switch-in (:2190), SwitchIn/FaintClearSetData (battle_main.c:3203, :3285), HandleAction_Switch (battle_util.c:299), battle start (battle_controllers.c:52), or a reset message. The only reset message ever emitted is RESET_MOVE_SELECTION (battle_script_commands.c:7802). So after battler 2 uses an item, byte 2 stays 1 until C1's next scroll for battler 2.
(4) In the bag, the blind A presses reach ChooseMonForInBattleItem. The party menu opens on slot 0 (party_menu.c:524-525), and in a non-multi double slot 0 is the left active Pokémon, which is battler 0's (:5970-5983). If that Pokémon is damaged, the item is consumed on it. If it is at full HP, the game says "won't have any effect", the exit callback is nulled and the menu returns to CB2_ReturnToBagMenu (:4419-4425, :4476-4477, :5783). The A presses then repeat. _watch's progress signature (script instruction, main callback, learn state, EXP) stays frozen, so the KI-47 net fires after 3000 frames (battle_handler.py:174, :300-318, wrapped at :383).
(5) The design covers none of this. There is no mention of Struggle, NoMovesLeft or Encore anywhere in DESIGN.md or the recon notes. C1/D7 (DESIGN.md:110-117) changes only scroll_to_battle_action, and this loop never calls it. D4's guard lives in battle_action_use_item, which this path never enters. §8 lists no such residual. The adversary recon (d13_recon_adversary.md:42) flagged a sibling path, battler 2's own FIGHT request reading byte 0, which C1 does fix. It did not flag this one.

WHY IT IS NOT A BLOCKER:
(a) The trigger is narrow. Battler 0 must have no move menu on its next decision, and byte 2 must still be 1: the path is open from battler 2's item until its next FIGHT pick (in practice the very next turn), and a switch-in or faint resets it earlier. That needs all four moves unusable (all at 0 PP, Taunt with an all-status moveset, Torment, Imprison, or Choice Band locked on a 0-PP move) or Encore.
(b) Tate & Liza's party is Claydol, Xatu, Lunatone and Solrock (src_data_trainer_parties.h:3550-3573). None of them has Encore, Taunt, Torment, Disable or Imprison. At that fight, which is every step-13 arm and step 14's only item-eligible double with KEYITEMS=1, the path needs battler 0's whole moveset drained to 0 PP. In practice no arm or batch run will reach it. Among the leader rematches, only Flannery 4-5 and Juan 2-5 have Taunt, and no rematch party has Encore.
(c) The damage is limited. A successful blind use heals the player's own active Pokémon and costs battler 2 its turn and one item. It happens in the same battle whose key gate already let battler 2 use an item, so it cannot breach RULING 27. The full-HP loop is stopped by KI-47 at 3000 frames. In StoryMode that is a recoverable fault (handles_battle_faults at story_mode.py:2123). Only the harness modes that did not opt in drop to Manual.
(d) No arm is made unable to fail. If the path does fire in D-ON, D-ON's clause "No item ever reaches another PID" (DESIGN.md:197) would catch it.

So this is a real defect created by the flag, with a limited effect. That is should-fix, not blocker. The proposed fix is sound: behind the flag, in a double, when battler_index==0, exit the loop as soon as get_battle_controller_callback(2) is HandleInputChooseAction, so the handler's branch at bas:207-212 makes battler 2's decision. It also needs a fake-emulator gate row and a mutant, and the path named in V1/D7/§8. Doing it without the flag would also change the base code's existing blind drive of battler 2, which goes beyond C1.
REFUTER EVIDENCE: - The loop, read at sandbox-pokebot/modules/battle_action_selection.py:1208-1215:
  `while get_main_battle_callback() in ("HandleTurnActionSelectionState","sub_8012324") and get_battle_controller_callback(battler_index) not in ("HandleInputChooseMove","HandleAction_ChooseMove"): press A`
- sandbox-pokebot/modules/battle_state.py:835-836: `get_main_battle_callback` returns `get_callback_for_pointer_symbol("gBattleMainFunc")`.
- Decomp battle_main.c:4145-4148: battler 2 gets its ChooseAction when its partner's state is STATE_WAIT_ACTION_CONFIRMED.
- battle_main.c:4184-4191: AreAllMovesUnusable → STATE_SELECTION_SCRIPT, then stateIdAfterSelScript = STATE_WAIT_ACTION_CONFIRMED_STANDBY.
- battle_main.c:4192-4197: an encored battler skips the move menu the same way.
- battle_util.c:1125-1139: sets gSelectionBattleScripts = BattleScript_NoMovesLeft.
- battle_controller_player.c:249-256: `switch (gActionSelectionCursor[gActiveBattler])`, where case 1 is B_ACTION_USE_ITEM.
- Every cursor write in the decomp, from grep:
  - battle_controller_player.c:2190 (switch-in anim) and :3106/:3110 (reset handler);
  - battle_main.c:3203 and :3285;
  - battle_util.c:299 (HandleAction_Switch);
  - battle_controllers.c:52 (battle start);
  - battle_script_commands.c:7802 is the only emit, and it sends RESET_MOVE_SELECTION.
- battle_main.c:4406-4410: an item of 0 (bag cancelled) sends the battler back to STATE_BEFORE_ACTION_CHOSEN.
- party_menu.c:524-525: `if (!keepCursorPos) gPartyMenu.slotId = 0`.
- party_menu.c:5780-5785: ChooseMonForInBattleItem, with exit callback CB2_ReturnToBagMenu.
- party_menu.c:5970-5983: in a double, partyIndexes[0] = gBattlerPartyIndexes[leftBattler].
- party_menu.c:4413-4425: an item that cannot be used gives gText_WontHaveEffect.
- party_menu.c:4476-4477: exitCallback is set to NULL, so the menu returns to the bag.
- sandbox-pokebot/modules/battle_handler.py:
  - :174: _SUBHANDLER_STALL_FRAMES = 3000;
  - :260-270: progress signature = (script instr, gBattleMainFunc, learn state, EXP);
  - :300-318: the KI-47 park or BotModeError;
  - :383: handle_battle_action_selection is wrapped by _watch.
- sandbox-pokebot/modules/libmgba.py:476: press_button releases a button held on the previous frame, so repeated A presses do register.
- plugins/custom_modes/story_mode.py:611-614: returns `_default_target(0)` at all 0 PP, which leads to battle_action_use_move.
- plugins/custom_modes/story_mode.py:2123: `handles_battle_faults = True` (StoryMode only).
- DESIGN.md:110-117 (D7) scopes C1 to scroll_to_battle_action callers only. A grep of the design and all six recon notes for Struggle/NoMovesLeft/Encore/1208 finds nothing. d13_recon_adversary.md:42 raises only the byte-0 variant for battler 2's own FIGHT request, which C1 fixes.
- src_data_trainer_parties.h:3550-3573: Tate & Liza's moves (Earthquake, Ancient Power, Psychic, Light Screen / Psychic, Sunny Day, Confuse Ray, Calm Mind / Light Screen, Psychic, Hypnosis, Calm Mind / Sunny Day, Solar Beam, Psychic, Flamethrower) include no Encore, Taunt, Torment, Disable or Imprison.
- A grep of the rematch leader parties for those moves finds Taunt only in Flannery 4-5 and Juan 2-5, and Encore in none.

## safety:S13-P2 [should-fix] design D4 (DESIGN.md:92-93) vs story_mode.py:863-885 and :1151-1164; modules/story/battle_items.py:225-226
CLAIM: D4 says 'the existing retry-once / disable bounds the rest' after a guard refusal. That is false for status cures whose parameter is 0 (Awakening, Full Heal, Ice Heal and the like). A cure request is judged only by the status branch, which never counts a failure. So a mismatch that persists makes the requester re-request the cure on every re-decision within the same selection. Only `_item_uses` reaching 4 stops it. That spends four full bag round-trips and the whole battle's item budget, so no HP heal is possible later in that battle.
EVIDENCE: A request with parameter==0 sets only `_status_when_item_requested` (sm:1151-1164, the else branch). No HP value or bag count is banked. At the next decision the status block clears it and logs '‼ no change … NOT counted against the no-op detector' (sm:863-885). `_hp_when_item_requested` is None, so the retry/disable code at sm:976-987 never runs. `choose_status_or_revive_item` stops only at `uses_so_far >= max_uses` (battle_items.py:225-226; MAX_ITEM_USES_PER_BATTLE = 4 at :49).

The refused battler re-decides immediately: the unwind returns to its own action menu (battle_main.c:4406-4409), and the handler loops back to the same battler (bas:198-212). A sleep cure is reachable at the target fight: Lunatone carries Hypnosis (d13_recon_decomp.md §B5). WRONGSLOT on a cure decision (D-SLOT) would produce exactly this.
FIX: Pick one and gate it:
(a) The executor records a per-battle `guard_refused` outcome (for example, a per-PID flag in the ledger), and the strategy counts it through `_index_space_flipped` / `_items_ineffective` whatever the item kind.
(b) Step 13 allows only parameter>0 items in doubles (no status cures) until (a) exists.
Either way, correct D4's bound claim. Add a gate row: a cure request, a guard refusal twice, then no third request.
VERDICT: refuted=True corrected=nit
REASONING: The mechanism the finding describes is accurate, but the harm is overstated, so it does not reach should-fix.

What holds:
- A parameter==0 cure request banks only `_status_when_item_requested` (story_mode.py:1160-1164).
- At the next decision the status block clears that request and logs "no change … NOT counted" (story_mode.py:863-885). It never touches `_index_space_flipped` or `_items_ineffective`.
- The not-consumed retry/disable branch (story_mode.py:976-987) runs only inside `if self._hp_when_item_requested is not None`, which a cure request never sets.
- `choose_status_or_revive_item` stops only at `uses_so_far >= max_uses` (battle_items.py:225-226; the cap is 4 at :49).
- A cancelled item re-opens the same battler's choice. With a zero item id the game sets `gBattleCommunication[gActiveBattler] = STATE_BEFORE_ACTION_CHOSEN` (battle_main.c, the B_ACTION_USE_ITEM case at ~4405-4409, checked in the decomp copy).
- A cure is reachable at Tate & Liza. Lunatone carries MOVE_HYPNOSIS (src_data_trainer_parties.h:3566), and the policy cures Sleep with Awakening, Full Heal or Lava Cookie (battle_items.py:156, :253-258).
- So D4's sentence "the existing retry-once / disable bounds the rest" is false for parameter==0 cures. There the bound is the 4-use cap. The design has no cure-refusal gate row (§7).

What is overstated:
1. The claimed harm, "the whole battle's item budget, so no HP heal is possible later in that battle", is the same end state as the bound D4 does claim. Take the HP path under a persistent refusal. Refusal 1 sets `_index_space_flipped`, and refusal 2 sets `_items_ineffective = True` (story_mode.py:981-986). Then `if self._items_ineffective: return None` (:1038-1039) ends ALL items for the battle. Under D3 that flag is per battle, shared by both battlers, exactly like `_item_uses`. So "retry-once / disable" and "cap at 4" both leave no items for the rest of the battle.
   - The difference is two extra bag round-trips, and they cost frames, not turns. Each refusal backs out to STATE_BEFORE_ACTION_CHOSEN and the same battler re-chooses within the same selection.
   - A transient refusal also costs the same budget either way. Both paths increment `_item_uses` per request (story_mode.py:1146).
2. It is bounded, so there is no hang, lost battle or derail. It is also not new: singles already treat a failed cure as uncounted by deliberate design (the "a cure that fails is a menu problem" comment at :875-876). The doubles path inherits shipped behaviour and does not introduce it.
3. Fix (a) would not restore the HP heals the finding says are lost. Counting refusals ends in `_items_ineffective`, which is the same "no items" state two round-trips earlier.
4. The D-SLOT arm cannot be made unable to fail by this. Its row (DESIGN.md:199) predicts refusal, no A press, bag unchanged and partner HP unchanged, and all of these hold with 2 or 4 refusals. If Step 0's pre-registered prediction copies D4's "retry once then disable" and the discriminator turns out to be a cure, the arm shows 4 refusals. That is a visible prediction miss, not a silent pass.

Residual, worth a nit:
- Correct D4's wording to say that a parameter>0 heal is bounded by retry-once/disable and a parameter==0 cure by the 4-use cap. The end state is the same.
- Optionally add a gate row pinning the cure-refusal count, so the Step-0 D-SLOT prediction is written against the real bound.
REFUTER EVIDENCE: Our code (worktree C:/Remote Projects/pokebot-wt-ch24/sandbox-pokebot):
- plugins/custom_modes/story_mode.py:863-885: the status verdict clears the request and logs "no change … NOT counted against the no-op detector". It sets neither `_index_space_flipped` nor `_items_ineffective`.
- story_mode.py:887 and :976-988: the not-consumed retry/disable runs only when `_hp_when_item_requested` is set. Refusal 1 sets `_index_space_flipped=True`; refusal 2 sets `_items_ineffective=True`.
- story_mode.py:1038-1039: `if self._items_ineffective: return None`. This is the claimed bound's end state, and it also means no HP heals for the rest of the battle.
- story_mode.py:1146: `self._item_uses += 1` on every request, heal or cure.
- story_mode.py:1151-1164: parameter>0 banks HP and the bag count; the else branch banks only the status.
- modules/story/battle_items.py:49: MAX_ITEM_USES_PER_BATTLE = 4. :79 and :225-226 apply the same cap to both policies.
- battle_items.py:130 and :156-157: cures fire only for Sleep and Freeze, with Awakening / Ice Heal, then Full Heal, Lava Cookie, Full Restore (:253-258). Full Restore has parameter 255, so it takes the COUNTED path.
- modules/battle_action_selection.py:1128-1140: the B-unwind returns to BATTLEMAINCB2 without a turn being spent.

Design:
- DESIGN.md:92-93: the claim under review.
- DESIGN.md:83-84: `_item_uses` and `_items_ineffective` are both PER BATTLE, so the two end states are identical.
- DESIGN.md:199: the D-SLOT row names no refusal count.

Decomp (scratchpad copy):
- battle_main.c, B_ACTION_USE_ITEM (~4405-4409): an item id of 0 gives `gBattleCommunication[gActiveBattler] = STATE_BEFORE_ACTION_CHOSEN`, so the same battler re-chooses and no turn is spent.
- src_data_trainer_parties.h:3562-3566: Tate & Liza's Lunatone carries MOVE_HYPNOSIS, so a sleep cure is reachable.

## safety:S13-P3 [should-fix] design D5/C5/C6/§7 (DESIGN.md:99-100, :146-147, :153-155, :209-210)
CLAIM: `observe` is specified as 'NO state change' ('the instance __dict__ equal before and after'), and D-OBS must equal D-OFF on every line without DBLITEM. The OBS line still reports `would=` and `worst=` per requester. Those need what `_maybe_use_item` builds and mutates, and C6 provides no pure extraction of them. Implemented the obvious way, observe mutates battle state and prints `[ITEM]`/`[KEYBATTLE]` lines. Implemented the state-free way, `worst` is always 0. That switches off the policy's rule 3, so OBS's first `would≠-` can come before the turn where D-ON actually acts.
EVIDENCE: `_maybe_use_item` does several things observe must not:
- it calls `_r27_key_gate`, which caches `_r27_verdict` and logs `[KEYBATTLE]` (sm:830, :6389-6399);
- it updates `_hp_seen` and `_worst_hit` (sm:838-841);
- when it picks an item, it runs `_item_uses += 1` and sets the pending request (sm:1146-1164);
- it logs `[ITEM] using` (sm:1166-1172).
A pending request set in observe would then be judged 'not consumed', which flips and later disables items. That would corrupt the rest of the OBS readout.

Rule 3 in `choose_healing_item` refuses to heal when the best item heals less than worst_hit (battle_items.py:92-95), and worst_hit=0 turns that check off. C6 lists mode/in_scope/invariant_order/menu_position/decode_bpo/guard_ok/ledger_key and no function that builds the policy inputs (medicine list, RULING 18 reserve filter sm:1057-1062, HEAL_AT_FRACTION sm:1079-1097).
FIX: Add a pure `policy_inputs(bag_items, reserve_filter, env)` to C6, and have both `_maybe_use_item` and observe call it. Observe then evaluates the pure policy with its own per-PID HP tracker. Declare that tracker as observe-only state and exclude it from the `__dict__` gate row, or keep it off the instance. State that observe never calls `_maybe_use_item` or `_r27_key_gate`, and give the `why=` field a key-class value computed from `key_battle_verdict` without caching or logging.
VERDICT: refuted=False corrected=should-fix
REASONING: The finding survives. I checked every citation and they all hold. The design never says how `observe` works out `would=` or `worst=` without changing state.

1. **The design leaves it out.**
   - D5 (DESIGN.md:100) requires observe to make "NO state change".
   - The §7 gate (:209-210) requires "no state change" for observe; the unset row says what that means: "the instance `__dict__` equal before and after".
   - The C5 line (:146-147) still has to report `would=`, `why=`, `worst=` and `uses=`.
   - D-OBS (:196) must equal D-OFF on every line without DBLITEM, and "Its first would≠- row = S0-5's discriminator".
   - S0-5 (:185) defines that discriminator as the first decision where `_maybe_use_item(side)` would choose an item. That decision includes rule 3 and each requester's worst hit.
   - C6 (:153-155) lists only mode, in_scope, invariant_order, menu_position, decode_bpo, guard_ok and ledger_key. Nothing builds the policy inputs, and nothing in the design says observe must avoid `_maybe_use_item`. A grep of the design for pure/choose_healing/_maybe_use_item/worst/__dict__ finds only the lines cited above.

2. **The recon warned about exactly this, and the design dropped it.**
   - `d13_recon_ourcode.md:200` (W3): "'What the singles policy would choose' cannot be computed without side effects … An observe-only probe needs that part pulled out as a pure function."
   - `d13_recon_adversary.md:113-118` (F10, SHOULD-FIX): "the observe-only probe must not call `_maybe_use_item`". Its fix is to call only the pure choosers, on copies.
   - The design lists these recon notes as inputs (:16-18) but did not carry the fix into C6 or D5.

3. **Both obvious ways to build it fail.**
   - **Calling `_maybe_use_item`.** It writes `_hp_seen` and `_worst_hit` (sm:838-841), increments `_item_uses` and sets a pending request (sm:1146-1164), and logs `[ITEM] using` (sm:1165-1174). On the next decision the unconsumed request takes the not-consumed branch: it flips once, then disables items (sm:976-987). The partner's decision can also clear it silently (sm:974). Either way the rest of the observe readout is corrupted, and the extra `[ITEM]` lines break D-OBS = D-OFF.
   - **Staying state-free.** It has no previous HP to compare against, so `worst` is 0. `battle_items.py:73-74` and `:94` say a worst hit of 0 disables rule 3. Observe can then report an item on a turn where D-ON, with its per-requester ledger (D3), refuses. That breaks the D-OBS criterion "first would≠- = S0-5".

4. **Why should-fix and not blocker.** The flag-unset path is untouched, no item goes to a wrong Pokémon, and the arms are not made unable to fail. A state-mutating observe would turn D-OBS red through the extra `[ITEM]` lines. A zero-worst observe would at worst produce a spurious D-OBS mismatch. The mismatch only happens when the bag's best heal is smaller than a hit the requester has already taken (Potion/Super Potion). A Hyper Potion, Max Potion or Full Restore makes rule 3 unreachable at these HP totals. The effect is a real, bounded defect: rework or a misread rule-10 arm.

5. **Two small overstatements, neither affecting the verdict.**
   - `[KEYBATTLE]` and the `_r27_verdict` cache fire only when `POKEBOT_R27_KEYITEMS=1` (sm:830, :6371-6399). The D-OBS arm lists only `observe`.
   - "mutates battle state" really means the strategy instance's state, not game state.

The proposed fix is sound, and it matches F10:
- extract a pure policy-input builder (medicine list, the RULING 18 filter, the heal fraction) that both paths call;
- give observe its own per-PID HP tracker for `worst`, and declare it in or exclude it from the `__dict__` gate row;
- state that observe never calls `_maybe_use_item` or `_r27_key_gate`.
REFUTER EVIDENCE: DESIGN (C:/Remote Projects/pokebot-wt-ch24/PROJECT KNOWLEDGE/ai-research-notes/2026-09-30-doubleitems13-DESIGN.md):
- :100 `observe`: "super() plus one [DBLITEM-OBS] line per decision (§3), with NO state change."
- :146-147 the OBS line carries "would=<item|-> why=<reason> worst=<n> uses=<n>".
- :153-155 C6 contains only mode/in_scope/invariant_order/menu_position/decode_bpo/guard_ok/ledger_key; there is no policy-input builder.
- :185 S0-5 computes "the FIRST decision where `_maybe_use_item(side)` would choose an item".
- :196 D-OBS must be "= D-OFF on every line without DBLITEM … Its first would≠- row = S0-5's discriminator".
- :209-210 the gate requires no state change ("the instance `__dict__` equal before and after", on the unset row).

OUR CODE (sandbox-pokebot/plugins/custom_modes/story_mode.py):
- :830 the KEYITEMS gate calls `_r27_key_gate`.
- :838-841 `_hp_seen` and `_worst_hit` are written.
- :974 a pending request is cleared silently when a different party index is judged.
- :976-987 not consumed: flip once, then `_items_ineffective = True`.
- :1057-1062 the RULING 18 reserve filter, inline.
- :1079-1097 the HEAL_AT_FRACTION knob, inline.
- :1146 `self._item_uses += 1`.
- :1152-1164 the pending request fields are set.
- :1168-1172 the `[ITEM] using … worst hit` log line.
- :6371-6399 `_r27_key_gate` caches `strategy._r27_verdict` and logs `[KEYBATTLE]`.

OUR CODE (sandbox-pokebot/modules/story/battle_items.py):
- :73-74 docstring: "0 disables that rule".
- :92-95 `if worst_hit_taken and best_possible < worst_hit_taken: return None`.

RECON (same folder, 2026-09-30-doubleitems13-recon/), which flagged this before the design:
- d13_recon_ourcode.md:200 (W3): "cannot be computed without side effects … needs that part pulled out as a pure function".
- d13_recon_adversary.md:113-118 (F10, SHOULD-FIX): "the observe-only probe must not call `_maybe_use_item` … Call only the pure `choose_healing_item` and `choose_status_or_revive_item` on copies."

## safety:S13-P4 [should-fix] design §6 D-SLOT / D-NOG rows (DESIGN.md:199-200); C5 (:145-150)
CLAIM: D-SLOT's 'no A press' is inferred from bag and HP staying unchanged, and nothing in C5 records the A press itself. If the partner is at full HP, or fainted, when the arm acts, an A press on it consumes nothing. Then a guard that logs `ok=0 guard refused` and still presses A (the natural 'log, then fall through' bug) passes D-SLOT. D-NOG instead fails even when the guard is truly load-bearing. The arm's result depends on a precondition that is not pre-registered.
EVIDENCE: An HP item on a full-HP target restores nothing (pokemon.c:5082-5083). On a 0-HP target the item is skipped (pokemon.c:5058-5061). Both lead to cannotUse → 'won't have any effect', and RemoveBagItem is never reached (party_menu.c:4413-4425 vs :4428-4434). The C5 lines are `[DBLITEM] use`, `menu … ok=`, `guard refused`; none of them marks the A press at bas:1134. S0-5 computes only the requester's discriminator, not the partner's HP (DESIGN.md:184-187).
FIX: Pre-register in S0-5 that the partner is alive and below max HP at the acting frame (both levers). If it is not, the arm is VOID. Add a C5 line emitted by the code that presses A (for example `[DBLITEM] pressed-A slot=`), so 'no A press' is observed directly (rule 7). Add a mutant that logs the refusal and then presses A, and it must turn D-SLOT's gate row red.
VERDICT: refuted=False corrected=should-fix
REASONING: The core of the finding holds. The partner's state at the acting frame decides what D-NOG and half of D-SLOT can show, and the design does not pre-register it. S0-5 (DESIGN.md:184-187) names the acting discriminator's frame, side, item, target PID, M_truth and P, which are all the requester's. Nothing names the partner's HP or status. The decomp confirms the mechanism. An HP item on a full-HP mon restores nothing (pokemon.c:5082-5083), and on a 0-HP non-Revive target the effect is skipped (pokemon.c:5058-5061). Either way cannotUse leads to "won't have any effect", and RemoveBagItem (party_menu.c:4428-4434) is never reached (the cannotUse branch is party_menu.c:4419-4425). The problem is wider than HP. The singles policy also hands out status cures (story_mode.py:854, :1148, :1161), so a Full Heal or Awakening aimed at a partner with no status is also a no-op. So the precondition should be "the S0-5 item has an effect on the partner at that frame", not only "the partner is below max HP".

Consequences:
- D-NOG (:200), "the wrong PID's HP rises and the bag drops", fails spuriously whenever that precondition is unmet. It is a pre-registered arm whose outcome hangs on an unregistered fact.
- D-SLOT's "bag count unchanged" and "partner's HP unchanged" (:199) are vacuous under the same condition. The design applies its own vacuity rule to the observe arm (D8, :126-127) but not to these two arms.

Two parts of the finding are OVERSTATED or already handled:
1. "Nothing records the A press itself" is true of C5 only. The existing, unconditional `_stage("target-chosen")` at sandbox-pokebot/modules/battle_action_selection.py:1136 runs in the next frame after the A press at :1134. It already appears in harness evidence logs (tools/story-dev/evidence/2026-09-28-r20T-CONTROL.txt:218 `[ITEM-FLOW] target-chosen state='CB2_UPDATEPARTYMENU'`). The guard sits between the scroll (:1133) and the A (:1134) per D4 (DESIGN.md:90-92). So a "log refusal, then fall through" bug would print `target-chosen` after `guard refused`, and the press is directly observable today. The fix is to name "no `[ITEM-FLOW] target-chosen` between `guard refused` and `returned-to-battle`" as D-SLOT's observable. A new C5 line is not needed.
2. The proposed mutant is already covered by the gate. §7 has the production row "the guard refuses a PID mismatch (fake emulator: no A press)" (DESIGN.md:216), which observes the press directly. It also has "a mutant per rule, each reddening exactly its own rows" (:219).

What survives is the unregistered partner precondition for D-NOG, plus D-SLOT's vacuous bag/HP clauses and its unnamed A-press observable. The effect is bounded:
- A spurious D-NOG failure is loud, not silent.
- D-SLOT's refusal still has to show `ok=0` and `guard refused`.
- The gate row covers the press at unit level.

Should-fix, not a blocker.
REFUTER EVIDENCE: DESIGN.md:184-187 (S0-5 computes only the requester's discriminator: "its frame, side, item, target PID, M_truth and P"). DESIGN.md:199-200 (D-SLOT: "no A press, bag count unchanged, the partner's HP unchanged"; D-NOG: "the wrong PID's HP rises and the bag drops"), with no partner-state precondition and no named observable for the A press. Decomp (scratchpad/decomp/party_menu.c): ItemUseCB_Medicine sets canHeal=FALSE when hp==MAX_HP; the cannotUse branch shows gText_WontHaveEffect; RemoveBagItem(item,1) sits only in the else branch. pokemon.c: `if (GetMonData(mon, MON_DATA_HP, NULL) == 0) { itemEffectParam++; break; }` (the 0-HP skip) and `if (GetMonData(mon, MON_DATA_MAX_HP, NULL) != GetMonData(mon, MON_DATA_HP, NULL))` (the full-HP no-op). The policy uses status cures, which never raise HP (story_mode.py:854, :1148, :1161, plugins/custom_modes/story_mode.py). Partial refutations: battle_action_selection.py:1133-1136 is `scroll_to_party_menu_index(_menu_slot)`, then `press_button("A")`, then `yield`, then `_stage("target-chosen")`. That is an existing unconditional A-press marker, present in evidence logs (tools/story-dev/evidence/2026-09-28-r20T-CONTROL.txt:218). DESIGN.md:216 has the gate row "the guard refuses a PID mismatch (fake emulator: no A press)", and :219 has "a mutant per rule". The adversary recon already anchors grading on "party HP read before and after 'target-chosen'" (d13_recon_adversary.md:57).

## safety:S13-P5 [should-fix] design S0-6 / arm X (DESIGN.md:188-189, :201)
CLAIM: Arm X can pass without testing anything. If post_mtpyre's 90,000 frames meet no double in which battler 2 selects a move, C1's changed read never runs, and base and build are identical by construction. S0-6 only says to 'record' the doubles met, and X's pass rule ('all four runs identical') has no premise.
EVIDENCE: C1 changes behaviour only when `battle_action_use_move`, `battle_action_use_item` or RotateLead run with battler_index 2 (DESIGN.md:111-112; bas:1198, :1034, :773). Singles take byte 0 in both builds (battle_menuing.py:61-64). CLAUDE.md session discipline rule 4 requires a check to assert something the run does not already satisfy.
FIX: Make X's premise explicit and pre-registered: at least one double (`[TRAINER] … double=1`) with at least one battler-2 FIGHT decision in all four runs, or the arm is VOID and needs a different fixture or more frames. Count those decisions in the X report.
VERDICT: refuted=True corrected=nit
REASONING: The literal point is correct: X's row (DESIGN.md:201) and S0-6 (:188-189) name no VOID condition. But the finding overstates what that costs, for two reasons.

(1) The premise is not left to chance. The fixture was picked because committed evidence shows exactly this setup (post_mtpyre.ss1 80602159, storyresume, seed 1, 90,000 frames) meeting three two-trainer doubles in the first ~24k frames after the first logged battle. In every one of them both of our actives are alive, so battler 2 decides every turn. S0-6 re-measures on the base code and records "the two-trainer doubles it meets". §5 is "reads that must come BEFORE the predictions" (:172), and §6 files the arms' values from Step 0 "BEFORE any code" (:191). So a zero count would surface before any prediction is filed.

(2) Even if X did come out vacuous, C1's changed read would not go untested. Arm D-OFF (:195) requires the build with the flag unset to equal "the base-code Step-0 run" (S0-5, :184, base code with both levers). That run is on the Tate & Liza fixture, a scripted `trainerbattle_double` in which, with the lever fainting slot 0, slots 1 and 2 are both out. So battler 2 goes through `decide_turn_in_double_battle(state, 1)` → `battle_action_use_move` → the C1 read on every such turn, compared against base code with the same flags. That is the ordinary attack-only behaviour on a double, which is what rule 9 asks for. So "C1 inert" does not rest on X alone.

What survives is a documentation nit, and it is cheap to apply: X's pass rule and the headline (:11, "proven inert … arm X") should state the premise, e.g. at least one `double=True` [TRAINER] with a battler-2 action decision in every X run, else VOID, and should cite D-OFF as the second, fixture-independent measurement. Nothing wrong is used, nothing hangs, and no arm is left unable to fail on C1, so the blocker and should-fix criteria are not met.
REFUTER EVIDENCE: - DESIGN.md:188-189: "S0-6 ... post_mtpyre.ss1 (PINNED 80602159694b), storyresume, seed 1, 90,000 frames, base code, twice apart (KI-112). Record the hash and the two-trainer doubles it meets."
- DESIGN.md:172: "STEP 0 (reads that must come BEFORE the predictions)".
- DESIGN.md:191: "the exact frames and values come from Step 0 and are filed as predictions BEFORE any code".
- DESIGN.md:195: D-OFF, "Equal to the base-code Step-0 run: the build with the flag unset changes nothing".
- DESIGN.md:184: S0-5, "Base-code runs, seed 1, both levers" on the Tate & Liza fixture.
- DESIGN.md:163-165: the HP=0 lever sends slots 1 and 2, "Then BOTH battlers discriminate".
- tools/story-dev/evidence/2026-09-29-r27keyitems-M0-liveA.txt:1: "post_mtpyre.ss1 (80602159), storyresume, 90000 frames, seed 1".
  - :11 f3148510 "double=True two=True": HP Mightyena 0, Sceptile 21/117, Swellow 18/109 (:10), so both actives are alive.
  - :16 f3156846 double=True; :21 f3168023 double=True (Swellow 11, Zigzagoon 32 alive, :20).
  - The first logged battle is f3144418 (:4) and the last is f3231535, so the doubles fall early in the window.
- d13_recon_fixture.md:9 and :61-73: post_mtpyre is chosen as "the cheapest non-vacuous double", with "three Route 123 two-trainer doubles".
- Tate & Liza is `trainerbattle_double` (d13_recon_fixture.md:37, MossdeepCity_Gym/scripts.inc:52).
- sandbox-pokebot/modules/battle_action_selection.py:206-212: battler 2 → `decide_turn_in_double_battle(battle_state, 1)` with battler_index=2.
- battle_action_selection.py:1197-1198: `battle_action_use_move` calls `scroll_to_battle_action(0)`, i.e. the C1 read, on every FIGHT.
- sandbox-pokebot/modules/battle_menuing.py:61-64 (byte 0 vs byte 2) and :89-91 (no side passed today).

## safety:S13-P6 [nit] design D4 + D9 (DESIGN.md:88-95, :128-129)
CLAIM: The guard's behaviour when its own read raises is not specified. D9 puts 'executor telemetry never raises' and 'the guard's refusal … backs out' together. If the guard's reads sit inside a swallow-and-continue telemetry wrapper, an exception falls through to the A press, silently, which is the NOGUARD state. Backing out costs no turn and is already bounded by the retry and disable, so the guard should fail closed.
EVIDENCE: The existing executor style swallows the exception and keeps going: `_stage` swallows (bas:1022-1031), and a failed KI-101 remap keeps the caller's value (bas:1116-1121). `read_symbol` itself does no bounds check (memory.py:66-69), so a slotId of 6 or 7 reads bytes past gPlayerParty and gives a mismatched PID. That case refuses correctly; only an exception path is undefined.
FIX: State in D4: if any guard read raises, refuse (no A), log `[DBLITEM] ‼ guard unreadable`, and unwind. Add a gate row in which a fake `read_symbol` raises and no A is pressed.

## safety:S13-P7 [nit] design G2 / D8 (DESIGN.md:57-58, :123-125)
CLAIM: '[left, right, the rest ascending]' is called the decomp INVARIANT, but only positions 0 and 1 are invariant. After any faint-switch, SwitchPartyOrder swaps positions, so the tail stops being ascending. `agree` compares only the target's position (0 or 1), so it is safe. The 6-digit `truth` column will differ from `bpo` after a switch, and a reader or later gate that compares the full orders will report a false mismatch.
EVIDENCE: SwitchPartyOrder calls SwitchPartyMonSlots on the two positions and copies the result to both player battlers (battle_main.c:4086-4105; party_menu.c:6040-6053). Example: [1,2,0,3,4,5], party 1 faints and party 4 replaces it → [4,2,0,3,1,5], while 'rest ascending' gives [4,2,0,1,3,5].
FIX: Reword G2 and D8: only 'the left active is at 0 and the right active at 1' holds for the whole battle. Label `truth` as valid for the tail only until the first switch, or log only the target's position.

### checked and found true
- V1-V5 hold at the cited lines: battle_menuing.py:30-96 (the action cursor reads byte 0 unless use_third_byte), bas:198-212 (strategy index {0,1}, handler index {0,2}), bas:577-579 (the re-read comes after the decision), story_mode.py:796-803 and :832/:908 (the two left_battler reads), bas:1016/:1034/:1106-1121/:1133-1140.
- G1 holds: ItemUseCB_Medicine applies the heal and calls RemoveBagItem at selection time (party_menu.c:4396-4434; pokemon.c:5082-5096). G2 holds for positions 0 and 1: ChooseMonForInBattleItem → UpdatePartyToBattleOrder (party_menu.c:5781-5786, :6078-6087), non-multi order (:5970-5983), cursor opens on slot 0 (:524-525). G3 holds: B on battler 2's menu is refused after a non-ball item and cancels the partner after a move or switch (battle_controller_player.c:306-324; battle_main.c:4282-4318).
- With the flag unset, the build equals today apart from C1. C2 returns super() before any read. C4's new battler_index is 0 in singles. C5 lines appear only with the flag set. C7 adds env reads only.
- C1 is frame-identical on the ordinary double today. Byte 2 is written only by resets, and our code never moves it: battler 2's scroll reads byte 0, which is 0, so it presses nothing, and scroll_to_move runs only once the move menu is open. With byte 2 = 0, `_select_in_menu` takes the same yield and break as today. The run and Safari paths and the multi (only battler 0 is ours) keep byte 0.
- The D4 guard's B-unwind cannot wedge and cannot cancel the wrong battler. The path runs: PARTY_MENU B → HandleChooseMonCancel default branch → DisplayCancelChooseMonYesNo returns FALSE for PARTY_MENU_TYPE_IN_BATTLE (party_menu.c:1378-1418) → Task_ClosePartyMenuAndSetCB2 restores field order (:1235-1236) → CB2_ReturnToBagMenu → bag B sets ITEM_NONE (item_menu.c:1250-1258) → battle → item 0 → STATE_BEFORE_ACTION_CHOSEN for the same battler (battle_main.c:4406-4409). BATTLEMAINCB2 is reached. The loop at bas:1137 stops before that battler's action menu takes input. press_button alternates press and release (libmgba.py:471-476), so B keeps producing edges.
- D4's pre-bag read of gPlayerParty[target_index] is in field order: every in-battle party menu restores it on close (party_menu.c:1235-1236), including after battler 0's successful item in the same turn.
- A failed request is always judged within the same selection. After a refusal, 'won't have any effect', or a bag that did not open, the requester's own action menu comes straight back and the handler re-decides it before the other battler acts. So the bag-count verdict is shared across battlers only when a request succeeded, and with the guard, 'consumed' still means 'the requester took the item'.
- The D3 ledger does not leak across battles: a new StoryItemBattleStrategy is created for every battle (story_mode.py:4357; story_harness.py:3302-3308, :3402-3408). In Gen 3 a PID cannot change sides without a switch, and the bot never switches by choice in trainer doubles. A faint replacement gets a fresh ledger, and the old PID's pending request is simply never judged, which is harmless.
- D3's shared bounds (_item_uses, _index_space_flipped, _items_ineffective) are conservative: a failure on one battler can only disable items for both, never enable more uses.
- KI-108: every new read in the design is raw. The only get_battle_state() on the new path is the existing KI-101 judge (sm:907), whose HP and party_index are covered by __eq__ (battle_state.py:249-263). The executor's remap at bas:1115 still happens in a later frame than the decision, so it stays the first call in its frame.
- _r27_key_gate in doubles caches one verdict for each battle and strategy instance, shared correctly by both battlers. It reads opponent B only for TwoOpponents (sm:6361-6400), so Tate & Liza (a single trainer ID) reads A as LEADER.
- D1 scope excludes Multi and InGamePartner (battle_state.py:47, :62). That keeps out the Space Center, where the party-menu slots 1, 4 and 5 are Steven's Pokémon (party_menu.c:5942-5955) and the bot controls only battler 0.
- D2 (self-only) is the safe choice. Together with D4, an item lands either on the requester's own PID or on nothing. It also makes V3's stale snapshot harmless for HP, because battler 0's action cannot change battler 2's HP or status.
- D6 (orthogonal flags) is safe as designed: default OFF, and step 14 runs both flags ON, so RULING 27 still holds in the batch. The only cost is exposure: DOUBLEITEMS=1 on its own acts in every trainer double, as singles do today.
- Bag holes left by the partner's last unit do not misdirect the item scroll: ItemBag._get_pocket skips empty slots (items.py:341-351), and scroll_to_item_in_bag computes its index after the bag has opened (menuing.py:63-76).

# LENS mechanics

## mechanics:M1 [should-fix] DESIGN §6 arms D-SLOT and D-NOG; §5 S0-5 (no partner-HP precondition)
CLAIM: D-NOG predicts that the partner takes the item: its HP rises and the bag count drops. The game only does that when the partner is below max HP, or holds a status the item cures. With the partner at full HP, the NOGUARD arm consumes nothing. D-SLOT's physical criteria ('bag count unchanged, the partner's HP unchanged') then read the same with or without the guard. S0-5 computes the requester's discriminator only and sets no condition on the partner.
EVIDENCE: party_menu.c:4410-4425: ItemUseCB_Medicine takes cannotUse from ExecuteTableBasedItemEffect_. On TRUE it shows gText_WontHaveEffect and never reaches RemoveBagItem (:4434). pokemon.c:5082-5114: the HP branch runs only `if (MAX_HP != HP)`, so retVal stays TRUE (no effect) on a full-HP mon. The failure path goes back to the bag, not the battle: exitCallback is NULL, so gPartyMenu.exitCallback = CB2_ReturnToBagMenu (party_menu.c:4477, :1238-1241, :5783). In that case D-NOG misses its prediction for a reason unrelated to the guard, which reads as a false refutation of 'the guard is load-bearing'.
FIX: Add to S0-5, as a pre-registered prediction: at the act frame the partner's HP is below max (or, for a Full Restore, the partner holds a curable status). Record the partner's PID, HP and max. If the fixture does not give that, stage it in every WRONGSLOT arm and its control, e.g. `--set-party-hp <partner slot>=<max-1>`. Grade D-NOG on 'the wrong PID took the item' (HP rose OR status bit cleared), measured as in M4.
VERDICT: refuted=False corrected=should-fix
REASONING: I could not refute M1. The design never makes the partner's HP (or status) a precondition. The decomp confirms that a partner at full HP consumes nothing, so D-NOG's prediction depends on a state the design never checks or sets up.

1. **The game mechanic holds.** `ItemUseCB_Medicine` does call `RemoveBagItem` only on its `cannotUse == FALSE` branch. The pure-HP effect clears `retVal` only when MAX_HP != HP. So a Potion, Super Potion or Hyper Potion given to a full-HP partner shows "won't have any effect" and consumes nothing.
2. **The failure path goes back to the bag, as claimed.** In battle, the item callback receives `Task_ClosePartyMenuAfterText`. With `gPartyMenuUseExitCallback` FALSE, the internal exit callback is set to NULL. Close then falls through to `gPartyMenu.exitCallback`, which is `CB2_ReturnToBagMenu`.
3. **Our policy can pick an item the partner cannot use.** It picks an HP item first and a status cure only second. The requester qualifies through its own low HP or status. Neither says anything about the partner.
4. **The design does not already handle it.** I searched the design, the six recon notes and the v2 spec for any partner-HP or full-HP precondition and found none.
   - S0-5 derives only the requester's discriminator: frame, side, item, target PID, M_truth and P.
   - D-NOG (design:200) asserts "the wrong PID's HP rises and the bag drops" unconditionally.
   - D4 (design:94-95) takes over the adversary note's premise that the living partner "consumes the item silently". The note states it without the at-max-HP caveat (d13_recon_adversary.md:55).
   - The fixture recon says HP at the Tate & Liza fixture is still unread (d13_recon_fixture.md:10, :113). So a partner at full HP is a live possibility, not a far-fetched one.
5. **Effect.** With the partner at full HP, D-NOG's physical outcome equals D-SLOT's: bag unchanged, partner HP unchanged. D-NOG then misses its prediction for a reason unrelated to the guard. That reads as a false refutation of "the guard is load-bearing". This is the CLAUDE.md Tier 2(4) case: a discriminator that is not computed on the named fixture.

**Why not a blocker.**
- D-SLOT can still fail on its own. Its `ok=0` / `guard refused` columns come from the guard itself, so only its physical columns turn vacuous.
- D-NOG would fail visibly rather than pass vacuously, so no arm becomes unable to fail.
- Production and flag-unset behaviour are unaffected.
- The fix is cheap and uses a lever the design already has: stage the partner below max HP with `--set-party-hp` in the WRONGSLOT arms and the control, and add a pre-registered S0-5 row recording the partner's PID, HP and max.
REFUTER EVIDENCE: **Decomp** (session copies under `scratchpad/decomp/`):
- `party_menu.c:4396-4434`: `ItemUseCB_Medicine`. `cannotUse = ExecuteTableBasedItemEffect_(...)`. On `cannotUse != FALSE` it shows `gText_WontHaveEffect` and sets `gPartyMenuUseExitCallback = FALSE`. `RemoveBagItem(item, 1)` runs only in the `else` branch.
- `pokemon.c:5082-5114`: "Only restore HP if not at max health". `if (GetMonData(mon, MON_DATA_MAX_HP) != GetMonData(mon, MON_DATA_HP))` is the only place in the HP case that sets `retVal = FALSE`.
- `party_menu.c:1316`: the in-battle use calls `gItemUseCB(taskId, Task_ClosePartyMenuAfterText)`.
- `party_menu.c:4474-4480`: `exitCallback = NULL` when `gPartyMenuUseExitCallback == FALSE`.
- `party_menu.c:1238-1241`: a NULL exit callback falls through to `gPartyMenu.exitCallback`.
- `party_menu.c:5783`: `ChooseMonForInBattleItem` sets that to `CB2_ReturnToBagMenu`.

**Our code:**
- `sandbox-pokebot/plugins/custom_modes/story_mode.py:1040-1130`: the HP policy (`choose_healing_item` on `mon.current_hp` / `total_hp` of the requester), then the status fallback. Nothing looks at the partner.

**Design** (`2026-09-30-doubleitems13-DESIGN.md`):
- `:184-187` S0-5 computes only the requester's frame, side, item, target PID, M_truth and P.
- `:199` D-SLOT: "bag count unchanged, the partner's HP unchanged".
- `:200` D-NOG: "The PARTNER takes the item: the wrong PID's HP rises and the bag drops. ⇒ the guard is load-bearing."
- `:94-95` D4 rests on "the LIVING partner, which consumes the item silently".
- `:163-166` the `--set-party-hp SLOT=HP` lever already exists and can stage the partner below max.

**Recon:**
- `d13_recon_adversary.md:55`, `:158`: "the wrong slot is often the living partner, so the item is consumed", with no full-HP caveat.
- `d13_recon_fixture.md:10`, `:113`: the fixture's HP and bag are unread/unverified.
- A grep of the design, recon and v2 spec for full HP, max HP, WontHaveEffect or a partner-HP precondition returns nothing beyond these lines.

## mechanics:M2 [should-fix] DESIGN §1 G2 ('[left active, right active, then the rest ascending]'), D8 (M_truth / `truth=<6 digits>`), C6 `invariant_order`, §7 pure rows
CLAIM: REFUTED as a whole-battle invariant. After any switch, faint replacement, Baton Pass or forced switch, the tail of the order carries switch history and is no longer ascending. Only positions 0 and 1 hold P(left) and P(right) for the whole battle. The design builds a 6-digit 'truth' order and gates `invariant_order` over every (left, right) pair as ground truth. Compared as a whole order, it disagrees with the real battlerPartyOrders after the first switch and would wrongly void `bpo`. A later partner or bench heal (D2's deferred item) that reuses it would misroute. Self-only M_truth, which is always 0 or 1, is unaffected.
EVIDENCE: battle_main.c:4086-4105: SwitchPartyOrder copies battlerPartyOrders[battler], swaps the POSITIONS of the outgoing mon (gBattlerPartyIndexes[battler], :4095) and the incoming mon (monToSwitchIntoId, :4096) with SwitchPartyMonSlots (:4097, party_menu.c:6052-6056), then writes the result to both player battlers (:4099-4105). It runs before getswitchedmondata updates gBattlerPartyIndexes: battle_scripts_1.s:3110-3111 (voluntary switch), :2844-2845 then :2886 (faint replacement), battle_script_commands.c:5177-5178, :5207 and :7364 (forced switch). Example: order [0,1,2,3,4,5], left P0 replaced by P3, gives [3,1,2,0,4,5]; the design's invariant gives [3,1,0,2,4,5]. The ascending tail exists only at battle start: battle_controllers.c:97-103 calls BufferBattlePartyCurrentOrderBySide, which builds it at party_menu.c:5972-5987 and loops over all 6 indexes, so empty slots sit at the end.
FIX: Restate G2: positions 0 and 1 hold the two active party indexes for the whole non-multi double (verified above); positions 2-5 carry history. Make `invariant_order` return only those two positions, or rename it `active_slots`. Log the whole order only as `bpo`, never as 'truth'. Define `agree` on the target's position only, and gate only positions 0 and 1. If the full order is ever needed, add a pure `apply_switch(order, out_p, in_p)` row that mirrors SwitchPartyOrder.
VERDICT: refuted=True corrected=nit
REASONING: The finding's mechanism is correct, but none of the consequences it lists follow from the design as written.

**What holds.** SwitchPartyOrder swaps the positions of the outgoing and incoming mons in the order array. So after a switch, positions 2-5 of battlerPartyOrders carry switch history, and G2's unqualified "[left, right, then the rest ascending]" is only true at battle start. Example: left P0 replaced by P3 gives [3,1,2,0,4,5], not [3,1,0,2,4,5].

**What fails.**

(1) "Compared as a whole order ... would wrongly void bpo":
- The design compares whole orders in one place only. S0-4 decodes them "at the first decision of the double". SwitchPartyOrder cannot have run before that first action selection. The starting order comes from BufferBattlePartyCurrentOrderBySide, which is built after SetBattlePartyIds, so it matches the invariant (including the `--set-party-hp 0=0` lever start, [1,2,0,...]).
- Everywhere else D8 compares POSITIONS: M_bpo against M_truth, the target's position in each order. D2 makes the target the battler's own active mon, so that position is always 0 or 1. The finding itself concedes this case is unaffected.
- So D-OBS's "agree=1 on every row" is not falsified by the tail, and bpo is not wrongly voided.

(2) "Gates invariant_order ... as ground truth": the §7 row checks that the pure function matches its own definition for every (left, right) pair. It asserts nothing about game memory.

(3) "A later partner or bench heal would misroute":
- This is a hypothetical about work §8 defers.
- A partner heal also targets position 0 or 1, so it would route correctly.
- The executor never uses invariant_order. It remaps through the refilled gBattlePartyCurrentOrder read at PARTY_MENU. D4's PID guard refuses any mismatch before A is pressed, so a mismatch is refused, not misrouted.

**Residual.** Two wording fixes. G2 (DESIGN:56-58) should say "at battle start; SwitchPartyOrder later permutes positions 2-5". The OBS column `truth=<6 digits>` is misnamed after a switch. Neither changes any behaviour or any arm: a nit.

**Aside, which cuts against the finding's own proposed fix.** The claim that positions 0 and 1 hold the two actives for the whole battle is not strictly true in vanilla. The ROM is built without BUGFIX, so in Cmd_forcerandomswitch the SwitchPartyOrder call runs even when TryDoForceSwitchOut FAILS:
- By then the validMons loop has left i = lastMonId = 6, so monToSwitchIntoId = 6.
- GetPartyIdFromBattlePartyId(6) finds no 6 in the order and returns 0.
- So a failed Roar or Whirlwind against the player's RIGHT battler swaps order positions 0 and 1 for both player battlers, while gBattlerPartyIndexes is unchanged.

In that case bpo is right and the invariant is wrong even at positions 0 and 1, so D-OBS could legitimately log agree=0 in some doubles. D4's PID guard still protects the target. Tate & Liza's team has no Roar or Whirlwind, so none of the arms is affected. If anything is filed, it should be "agree=0 is possible after a failed forced switch against the right battler", not the finding as filed.
REFUTER EVIDENCE: **Decomp** (pret/pokeemerald, fetched fresh):
- battle_main.c:4086-4105, SwitchPartyOrder:
  - :4093 loads battlerPartyOrders[battler]
  - :4095-4096 find the positions of the outgoing and incoming mons
  - :4097 SwitchPartyMonSlots
  - :4099-4105 in a double, writes the result to both the battler and its partner
- party_menu.c:6051-6056 SwitchPartyMonSlots swaps two positions; party_menu.c:6058+ GetPartyIdFromBattlePartyId returns 0 when the value is absent. So the tail does carry history (the finding's premise).
- The order is built at battle start: battle_controllers.c:97-103 (SetBattlePartyIds, then BufferBattlePartyCurrentOrderBySide), producing party_menu.c:5970-5983 [L, R, then i<6 ascending].
- The bag opens on that order: battle_main.c:4236 EmitChooseItem(battlerPartyOrders[...]); battle_controller_player.c:2661-2662 copies it into gBattlePartyCurrentOrder.
- Failed forced switch (the aside):
  - battle_script_commands.c:7303 lastMonId = PARTY_SIZE (no BUGFIX)
  - :7324-7332 the validMons loop leaves i = 6
  - :7340 if (TryDoForceSwitchOut()), with the #ifndef BUGFIX brace at :7358-7360 closing the if early
  - :7361 monToSwitchIntoId = i; :7363-7364 if (!IsMultiBattle()) SwitchPartyOrder(gBattlerTarget), which runs even on failure
  - :7164-7176 TryDoForceSwitchOut returns FALSE on the level roll
- src/data/trainer_parties.h:3546-3575, sParty_TateAndLiza1: Claydol, Xatu, Lunatone, Solrock. None knows Roar or Whirlwind.

**Design:**
- DESIGN:122-127 (D8): M_bpo and M_truth are the target's POSITIONS; disc compares M_truth with P.
- DESIGN:71-76 (D2): self-only, so the target sits at position 0 or 1.
- DESIGN:180-183 (S0-4): the whole-order decode happens only "at the first decision of the double".
- DESIGN:206: the pure row tests the function's definition only.
- DESIGN:88-95 (D4): the PID guard refuses any mismatch before A is pressed.
- DESIGN:223 (§8): partner and bench heals are deferred.
- DESIGN:56-58 (G2): the unqualified wording, the one residual (nit).

**Our code:** sandbox-pokebot/modules/battle_action_selection.py:1111-1116. The executor's KI-101 remap uses a fresh get_battle_state().map_battle_party_index(), which re-reads gBattlePartyCurrentOrder (battle_state.py:816) at PARTY_MENU. That is the real menu order; invariant_order is never used for routing.

## mechanics:M3 [should-fix] DESIGN D8 / C5 raw reads (`truth=` from gBattlerPartyIndexes, `bpo=` via *gBattleStruct) and §5 S0-4 self-check
CLAIM: The raw reads do not state their strides or which battler space they use, and S0-4's self-check cannot fail on the unstaged fixture for exactly the likely mistake. (a) gBattlerPartyIndexes is u16[4], so battler b sits at byte 2b. Indexing it by byte [b] reads battler 1, the OPPONENT. (b) The OBS line is emitted from the strategy, which receives strategy index {0,1}, but battlerPartyOrders is indexed by game battler {0,2}. Offset +0x60+3*1 = +0x63 is the opponent's order. (c) At battle start, with the player's actives at P0/P1, the player's and the opponent's arrays are both 01 23 45. So an S0-4 check run on the unstaged fixture passes an off-by-one-battler read. Only the `--set-party-hp 0=0` lever (player 12 03 45 against opponent 01 23 45) separates them.
EVIDENCE: battle_main.c:158: `u16 gBattlerPartyIndexes[MAX_BATTLERS_COUNT]`; sym `0202406e g 00000008` (sandbox-pokebot/modules/data/symbols/pokeemerald.sym:118). Our own reader uses `_battler_party_indexes[index * 2]` (battle_state.py:274). battle.h:354-381 puts battlerPartyOrders at +0x60, 3 bytes per battler. battle_controllers.c:100-103 fills all 4 battlers' orders at start. BufferBattlePartyOrderBySide builds the opponent side from the opponent's own indexes (party_menu.c:5936-5945, :5972-5987); Tate & Liza start at [0,1] (battle_controllers.c:597-628). The strategy index against the handler's battler: battle_action_selection.py:198-212.
FIX: Write the reads into the design: truth left = u16 at gBattlerPartyIndexes+0, right = u16 at +4. bpo = read_bytes(u32(*gBattleStruct) + 0x60 + 3*g, 3) with g = 2*side, and log g. Run S0-4 under `--set-party-hp 0=0` and require bpo(0) = bpo(2) = 12 03 45 AND bpo(1) = 01 23 45, so a wrong-battler read fails.
VERDICT: refuted=False corrected=should-fix
REASONING: The core of the finding holds. S0-4's live self-check, as the design words it, cannot catch a `bpo` read of the wrong battler. Two parts of the finding go too far.

1. **What is right.**
   - The offset is +0x60. Walking `struct BattleStruct` in battle.h:354-381 gives:
     - `assistPossibleMoves` u16[24] at 0x18-0x47;
     - `expValue` aligned to 0x50;
     - `selectionScriptFinished` at 0x54, `battlerPartyIndexes` at 0x58, `monToSwitchIntoId` at 0x5C;
     - `battlerPartyOrders[4][3]` at 0x60, and `runTries` at 0x6C.
   - At battle start, battle_controllers.c:97-102 fills all four battlers' orders.
   - `BufferBattlePartyOrderBySide` builds each side from its own side's `gBattlerPartyIndexes` (party_menu.c:5931-5940, :5972-5987). So on an unstaged Tate & Liza start all four arrays are 01 23 45.
   - S0-4 (DESIGN:180-183) names no run or lever. It checks "at the first decision", so it would most likely run on the S0-3 unstaged driver run. On that run, a strategy-index read (side 1 → battler 1, +0x63) passes. So does an offset error of +3. S0-4 is the step meant to certify the instrument before the predictions, so this is the vacuity pattern CLAUDE.md rules 4 and 10 forbid.
   - The finding's lever math is correct. With slot 0 at HP 0, SetBattlePartyIds (battle_controllers.c:597-640, `gBattlerPartyIndexes[i - 2] != j` at :628) seats party 1 and 2. That makes player bpo 12 03 45 against the opponent's 01 23 45.

2. **Overstated, part 1: the byte stride.** `gBattlerPartyIndexes` is u16[4] (battle_main.c:158; pokeemerald.sym:118, size 8), and our reader already uses `[index*2]` (battle_state.py:274). But a byte-stride or side-space `truth` read does NOT pass the unstaged check.
   - Byte 1 and byte 2 both read 0 at start: the high byte of battler 0's entry, and the opponent-left's low byte.
   - So `truth` gets right = 0, not 1, and the invariant no longer matches 01 23 45. S0-4 fails.
   - The real flaw there is different. The design's stated fallback ("bpo column is void, observe falls back to the invariant alone") would then blame `bpo` and keep the broken `truth`.

3. **Overstated, part 2: "does not state which battler space".** The design does state it:
   - V2 (DESIGN:28-30) names both index spaces;
   - D8 (:120) says `battlerPartyOrders[battler]`;
   - S0-4 (:181) says "battler 0 and battler 2";
   - C5 (:146) already logs `battler=`. The proposed "log g" is therefore already in the design.

4. **Why it is not a blocker.** No arm is made unable to fail. D-OBS must reproduce S0-5's discriminator, and S0-5 uses both levers (DESIGN:184, :196). So D-OBS runs the lever config, where a side-1 read of battler 1 gives `agree=0` on the discriminating rows, and D-OBS's "agree=1 on every row" fails. The cost is bounded:
   - the instrument's pre-registration check is vacuous;
   - a later `agree=0` is ambiguous between a measurement bug and the executor-remap defect that D8 exists to detect, so it invites a misdiagnosis.

   OBSERVE changes no state, so no battle and no item can be affected.

**Recommended fix (a narrowed version of the one proposed):**
- Run S0-4 under `--set-party-hp 0=0`.
- Require bpo(0) = bpo(2) = 12 03 45 AND bpo(1) = bpo(3) = 01 23 45.
- Require `truth` left/right = (1, 2) from u16 reads at +0 and +4.
- State that a `truth` mismatch voids `truth`, not `bpo`.
REFUTER EVIDENCE: - **Decomp, `gBattlerPartyIndexes`:** battle_main.c:158 `EWRAM_DATA u16 gBattlerPartyIndexes[MAX_BATTLERS_COUNT]`; sandbox-pokebot/modules/data/symbols/pokeemerald.sym:118 `0202406e g 00000008 gBattlerPartyIndexes`. Our reader is battle_state.py:274 `self._battler_party_indexes[index * 2]`.
- **Decomp, `struct BattleStruct` (battle.h:354-381):** `battlerPartyIndexes[4]` @0x58, `monToSwitchIntoId[4]` @0x5C, `battlerPartyOrders[4][3]` @0x60, `runTries` @0x6C. `gBattleStruct` is a pointer (sym:181, size 4).
- **Decomp, battle-start order build:** battle_controllers.c:97 `SetBattlePartyIds();` and :102 `BufferBattlePartyCurrentOrderBySide(i, 0);` for every battler. party_menu.c:5938 selects the opponent's own positions for an opponent battler. :5975 `partyIndexes[1] = gBattlerPartyIndexes[rightBattler];` and :5987 pack the nibbles. So both sides are 01 23 45 when each side's actives are at 0/1.
- **Decomp, the lever:** battle_controllers.c:628 `&& gBattlerPartyIndexes[i - 2] != j`. With slot 0 at HP 0, the actives are party 1 and 2, so the player's order is 12 03 45.
- **Our dispatch:** battle_action_selection.py:198-212 calls `decide_turn_in_double_battle(battle_state, 0)` for battler 0 and `(battle_state, 1)` with `battler_index = 2`.
- **DESIGN, battler space already stated:** :28-30 (V2 names both spaces), :120 (`battlerPartyOrders[battler]`), :181 ("battler 0 and battler 2"), :146 (C5 already logs `battler=`).
- **DESIGN, S0-4 names no run or lever:** :180-183.
- **DESIGN, D-OBS runs the lever config:** S0-5 uses "both levers" (:184), and D-OBS must reproduce S0-5's discriminator and show `agree=1` on every row (:196). So it would catch a wrong-battler read late, as `agree=0`.
- **DESIGN, fallback blames `bpo`:** :182 ("If they do not, D8's bpo column is void"), so a `truth`-read bug would be misattributed.

## mechanics:M4 [should-fix] DESIGN §6 D-ON ('that PID's HP rises'), D-NOG ('the wrong PID's HP rises'), D-SLOT ('the partner's HP unchanged'); C5 telemetry list
CLAIM: The heal is applied when the target is chosen, and the turn's damage lands after it. None of the C5 lines reads HP after the menu closes. The only later HP reading is the requester's next decision, which is a post-turn value. The project already measured that value as a transient with a 4-HP margin (KI-101 blocker 1). At Tate & Liza, Earthquake hits both of our Pokémon, so 'HP rises', read post-turn, can fail on a heal that landed, or pass for the wrong reason.
EVIDENCE: pokemon.c:5082-5096: SetMonData(HP) and `gBattleMons[battler].hp = dataUnsigned` run at menu time. The party returns to field order BEFORE the callback switches back: party_menu.c:1233-1241 (UpdatePartyToFieldOrder, then SetMainCallback2). A successful use exits straight to battle through CB2_SetUpExitToBattleScreen (party_menu.c:1312-1313). The turn runs only after every battler has confirmed (battle_main.c:4524-4528). story_mode.py:936-958 documents the post-turn read as a transient ('use 2: 2/147 -> 6/147 … verdict survived by FOUR HP'). The item's status cures also write at selection (pokemon.c:5306-5316).
FIX: In C5, add a raw read at the executor's first BATTLEMAINCB2 frame (the `returned-to-battle` stage, before any move runs): the HP and status1 of every player PID, in field order. Grade D-ON, D-NOG and D-SLOT on the change between that read and the pre-bag read, never on the next decision. HP items grade on HP; Awakening and Ice Heal grade on the status bit. Optional independent counter: gBattleResults+0x03 (numHealingItemsUsed) rises only when a non-Revive HP item lands on an ACTIVE player battler (pokemon.c:5097-5099).
VERDICT: refuted=False corrected=should-fix
REASONING: The finding survives as filed: the design never says where the HP reading used in its arms comes from.

- **The game applies the item when the target is chosen.** The HP (and any status cure) is written to both the party data and gBattleMons while the party menu is still open. Items then go first in the turn, and the moves that turn deal their damage afterwards.
- **The design's C5 telemetry has no HP read after the menu closes.** The OBS line reads HP at the decision, which is observe mode only. The `use` line reads HP before the bag opens. The `menu` line logs only the slot and PIDs.
- **No existing instrument covers the gap either.**
  - `[PARTY]` lines are keyed on species and level only, not HP.
  - The handler re-reads the battle state only when the battler changes, and that re-read happens before the item runs. So battler 2's `[TURN]` line in the same round shows stale HP (the design's own V3). In D-NOG that is exactly the partner whose HP the arm grades.
  - The next HP reading is the requester's next decision, a post-turn value. The code's own `[ITEM] CONSUMED` line labels that value "NOT the heal's result" and cites the measured transient (the 2/147 -> 6/147 read after a Full Restore).
- **The recon the design cites had already given the right instrument.** d13_recon_decomp.md §C.6 says to read the intended Pokémon's HP by PID after the menu closes, and to use gBattleResults[3]. Neither made it into C5.
- **What goes wrong if the arms are graded on the next-decision value:**
  - D-SLOT's "partner's HP unchanged" fails whenever the partner is hit that turn. Tate & Liza's Claydol has Earthquake, which hits both of our Pokémon, and the rest of their team also attacks.
  - D-ON's "HP rises" fails when that turn's damage exceeds the heal, or when the healed Pokémon faints.
  - D-NOG's "wrong PID's HP rises" can pass for the wrong reason if the partner's HP rises some other way that turn.
- **D-ON can pick a cure instead of an HP item.** S0-5 takes the first decision where the policy picks any item. The decomp recon itself says Hypnosis makes a status-cure decision reachable at Tate & Liza. If that first pick is an Awakening, D-ON's "HP rises" criterion does not apply at all.

**Why should-fix and not blocker:**
- The HP clauses are one condition among several in each arm, so no arm becomes unable to fail.
- The load-bearing identity evidence is still graded correctly. That is `ok=1` plus `menu_pid`/`intended_pid` on the menu line, plus the bag-count drop, which the design's D4 already names as the proof.
- Production behaviour is unaffected: the verdict judges whether the bag count dropped, and HP is only reported.
- The effect is therefore limited to arms that can fail or pass on the wrong evidence. The fix is to grade the HP clauses (and a status bit for cures) on a raw read at the executor's `returned-to-battle` stage, before any move runs, as proposed.
REFUTER EVIDENCE: Heal applied when the target is chosen:
- decomp/pokemon.c:5083-5096: SetMonData(mon, MON_DATA_HP) and then `gBattleMons[battler].hp = dataUnsigned`.
- :5097-5099: numHealingItemsUsed++ only when battler != MAX_BATTLERS_COUNT and the item is not a Revive.
- HealStatusConditions at :5306-5316 clears gBattleMons[battler].status1 at the same point.
- party_menu.c:4396-4434: ItemUseCB_Medicine runs the effect, then RemoveBagItem.

Menu exit straight to battle:
- party_menu.c:1233-1241: UpdatePartyToFieldOrder, then SetMainCallback2.
- :1312-1313: CB2_SetUpExitToBattleScreen for an in-battle item use.

Items go first in the turn: battle_main.c:4817-4825 queues B_ACTION_USE_ITEM before the moves.

No HP read in C5 after the menu closes:
- DESIGN.md:146-150 lists the C5 lines: the OBS line reads hp at the decision, the use line hp=cur/max when acting, and the menu line only slot, menu_pid, intended_pid and ok.
- DESIGN.md:197, :199 and :200 grade on "that PID's HP rises", "the partner's HP unchanged" and "the wrong PID's HP rises", with no instrument named.

No other HP read in our code:
- sandbox-pokebot/modules/debug_logger.py:620-622: `_party_key` is species:level only, no HP.
- battle_action_selection.py:116-119 and :577-579: the state is re-read only when the battler changes, before the action executes, so battler 2's [TURN] line (:530-533) shows pre-item HP (V3).
- The executor's `returned-to-battle` stage (:1133-1140) reads no HP.
- plugins/custom_modes/story_mode.py:936-958: KI-101 blocker 1 measures the post-turn read as a transient ("use 2: 2/147 -> 6/147 … verdict survived by FOUR HP").
- story_mode.py:976-981: the CONSUMED line says "HP reads … (a post-turn value, NOT the heal's result)".

The recon already proposed the right read:
- d13_recon_decomp.md:101 and :109: "after the menu closes, the HP change of the intended mon, found by PID in normal order, confirms the heal"; gBattleResults[3] (include_battle.h:239).
- d13_recon_decomp.md:93 and :98: Claydol has Earthquake, which hits both of our Pokémon; Hypnosis makes a cure decision reachable, so D-ON's first act may not be an HP item.

## mechanics:M5 [should-fix] DESIGN D4 (identity guard) and the D-ON claim 'No item ever reaches another PID'
CLAIM: D4 takes the 'intended' PID from gPlayerParty[target_index], and target_index comes from the strategy. The guard therefore checks only the party-index-to-menu-slot conversion. It does not check D2's binding from the acting battler to its own party index. A side mix-up in C2/C3 would pass the guard and consume the item on the partner, and no fault arm covers it. Examples: the strategy space {0,1} confused with the handler space {0,2}, or a `left_battler` read left in place for side 1.
EVIDENCE: Two battler spaces: battle_action_selection.py:198-212 (strategy index 0/1, handler battler_index 0/2). The game resolves the heal target only from the menu slot's party index, never from who is choosing: pokemon.c:4789-4802 walks i = 0, 2 for `gBattlerPartyIndexes[i] == partyIndex`, and gBattlerInMenuId only picks the side. So the game also lets either battler heal either Pokémon. gBattleMons[b].personality is at +0x48, stride 0x58 (include/pokemon.h:260-292; our battle_state.py:674-675). Transform does not overwrite it.
FIX: In the executor (flag 1, doubles), also require target_index == u16 gBattlerPartyIndexes[battler_index], or gBattleMons[battler_index].personality == intended_pid, before pressing A. Log it as `self=<0|1>`. Add a fault, e.g. POKEBOT_R27_FAULT_DBL_SIDESWAP (the strategy passes the partner's party index), whose arm the guard must refuse with the bag unchanged.
VERDICT: refuted=True corrected=nit
REASONING: The finding's mechanism is right, but it goes too far in saying nothing covers the case. The design already covers it at the point where the side binding is made.

What holds up:
(1) D4 takes the intended PID from gPlayerParty[target_index], and the strategy supplies target_index. So the guard only checks the step from party index to menu slot. It does not check that target_index belongs to the acting battler.
(2) The game does not stop a cross-heal. pokemon.c:4789-4802 in the decomp scratch copy resolves the target battler by walking gBattlerPartyIndexes[i]==partyIndex over i=0,2. gBattlerInMenuId only picks the side. So a side mix-up would really put the item on the partner.

Where it overreaches:
(a) The side binding is new code in C2/C3, and design §7 pins it with a production row: "`1`: side 0 heals the left Pokémon, side 1 the right; never the partner". §7 also requires "a mutant per rule, each reddening exactly its own rows". Both of the finding's examples would turn that row red if it runs on a fake with left≠right. One example is `side==2` used in place of `side==1`. The other is a `left_battler` read left unchanged at :832.
(b) The D-ON arm would also catch a swap live. It is graded against S0-5's pre-registered side, item and target PID. S0-5 computes these offline from `[TURN]` lines. Those lines take the deciding battler's mon from the handler's own 0→left / 2→right mapping (battle_action_selection.py:453-457), not from C2/C3. A swapped build would decide on the wrong mon's HP and target the wrong PID, so the arm fails its prediction.
(c) Everything else in the chain is existing, verified code. The handler passes strategy index 1 for battler 2 (:198-212). right_battler is gBattleMons slot 2 (battle_state.py:405-415). party_index is gBattlerPartyIndexes[2] (battle_state.py:274). No runtime state can separate these during one selection phase, so a mix-up needs a coding bug, and (a) is the check against coding bugs.

D4's own conclusion is scoped correctly. It says "bag dropped ⇒ the INTENDED Pokémon took it" and does not claim the target is the acting battler's own Pokémon.

What is left is cheap hardening, not a design defect. A runtime check (target_index == gBattlerPartyIndexes[battler], or gBattleMons[battler].personality == intended_pid) plus a `self=` log field would let D-ON's "no item ever reaches another PID" be checked by identity on acts after the first predicted one. Today, later acts can only be cross-checked by species through `[TURN]`. That is a nit. A dedicated live SIDESWAP fault arm adds little, because the §7 mutant row already fault-tests exactly this binding.
REFUTER EVIDENCE: DESIGN 2026-09-30-doubleitems13-DESIGN.md:211 "`1`: side 0 heals the left Pokémon, side 1 the right; never the partner;" and :219 "every C7 fault, plus a mutant per rule, each reddening exactly its own rows"; :138 C2 passes `side=battler_index` (strategy space, V2 :28-30); :140-141 C3 "The two `left_battler` reads select by `side`"; :185-186 S0-5 pre-registers "frame, side, item, target PID" computed offline from [TURN]; :197 D-ON "the named side uses the named item on its OWN Pokémon ... that PID's HP rises"; :94 D4's claim is "the intended Pokémon took the item" (scoped to intent). Code: sandbox-pokebot/modules/battle_action_selection.py:198-212 (battler 0 -> strategy 0, battler 2 -> strategy 1); :453-457 [TURN]'s `_me` = left_battler if battler_index==0 else right_battler (independent of C2/C3); :591 current executor call `battle_action_use_item(battle_state, index, target_index)` (no battler); modules/battle_state.py:274 party_index = gBattlerPartyIndexes[index*2]; :396-415 left=gBattleMons[0], right=gBattleMons[2]; plugins/custom_modes/story_mode.py:832 `mon = battle_state.own_side.left_battler`, :1214 `return TurnAction.use_item_on(item, mon.party_index)`. Decomp: pokemon.c:4789-4802 (the scratchpad decomp copy) `gActiveBattler = gBattlerInMenuId; i = (GetBattlerSide(...) != B_SIDE_PLAYER); while (i < gBattlersCount) { if (gBattlerPartyIndexes[i] == partyIndex) ... i += 2; }` confirms the game resolves the target by party index, so a strategy-side swap would be accepted silently. That part of the finding is correct, but the §7 row and mutants already cover it.

## mechanics:M6 [nit] DESIGN §6 D-CUR ('The exact failure (KI-45 or a not-consumed verdict) is predicted from which side acts first')
CLAIM: The first act's failure mode can be determined now: it is KI-45 whichever side acts first. The not-consumed branch needs byte 0 to already equal the target, which requires an earlier item use by battler 0 in the same battle. Also, under MossdeepBadgeMode, KI-45 becomes a BotModeError and the run drops to Manual, so the arm needs a frame bound.
EVIDENCE: battle_controllers.c:52 sets every byte to 0 at battle start. Left and Right only toggle bit 0 when it is set or clear (battle_controller_player.c:266-284), and they change gActionSelectionCursor[gActiveBattler], never byte 0. Battler 0 uses the item first: byte 0 = 1; battler 2's FIGHT presses Left, which leaves byte 0 unchanged; 60 steps, then KI-45 (battle_menuing.py:27, :38-55). Battler 0 attacks first: byte 0 = 0; battler 2's BAG presses Right, which moves byte 2 only; KI-45 again.
FIX: Pre-register 'KI-45 at the first act, either order'. Give D-CUR a frame bound and a stated terminal line, or run it only in a mode that declares handles_battle_faults.

## mechanics:M7 [nit] recon d13_recon_adversary.md:144-145 (S0-4 input): 'Self-check: +0x58 must equal gBattlerPartyIndexes'
CLAIM: That self-check is invalid, and Step 0 must not adopt it. gBattleStruct->battlerPartyIndexes (+0x58) is not a mirror of gBattlerPartyIndexes. It is written only when a switch or party screen is chosen, and it is zero from AllocZeroed until then. With the lever (P1, P2) it would void bpo on the first decision.
EVIDENCE: The only writes are battle_main.c:4241 (B_ACTION_SWITCH chosen) and battle_script_commands.c:4857, :5116, :7168, :7178. It is allocated zeroed at battle_util2.c:25.
FIX: Record in S0-4 that +0x58 is not a self-check. Keep the design's own check (M3's version).

## mechanics:M8 [nit] DESIGN §1 G2 ('the multi's is fixed (:5942-5955)')
CLAIM: This is REFUTED for the in-game-partner multi, the Space Center: the player's order is rewritten after a player switch. Step 13 is out of scope for it (D1), but the later multi item would inherit this wrong model from the design.
EVIDENCE: battle_util2.c:108-121: SwitchPartyOrderInGameMulti swaps positions inside battlerPartyOrders[0]. It is called from battle_script_commands.c:5201-5204 and at the end of selection, battle_main.c:4538-4543.
FIX: Reword to 'fixed at battle start ([0,3,1,2,4,5]); swapped by SwitchPartyOrderInGameMulti after player switches'.

## mechanics:M9 [nit] DESIGN D3 ('`_worst_hit` becomes the requester's own largest drop … That is the right input')
CLAIM: On a turn where the requester healed, `_worst_hit` misses that turn's damage. The heal lands at selection, after `_hp_seen` recorded the pre-heal HP, so the next decision measures (pre-heal HP) minus (healed HP minus damage), which is usually negative and ignored. The singles path has the same flaw; the claim 'right input' overstates it.
EVIDENCE: pokemon.c:5096 (heal at selection); story_mode.py:838-841 (`previous > mon.current_hp` only, `_hp_seen` set at the requesting decision).
FIX: Soften the claim, or re-baseline `_hp_seen[pid]` from the M4 post-menu read after an item lands.

## mechanics:M10 [nit] DESIGN D4 / C6 `guard_ok(intended, menu)`
CLAIM: The guard reads the PID at gPlayerParty[slotId] without first checking the range of slotId. Cancel is slot 7, and index 6 or 7 reads past gPlayerParty into gEnemyParty. The guard fails safe only because the PIDs happen to differ.
EVIDENCE: PARTY_SIZE+1 is Cancel (party_menu.c:1590-1631). gPlayerParty is 0x258 bytes at 0x020244ec, and gEnemyParty follows at 0x02024744 (pokeemerald.sym:202-203).
FIX: `guard_ok` returns False unless 0 <= slotId < gPlayerPartyCount; add a pure row for slot 7.

## mechanics:M11 [nit] DESIGN §8 KI-115 ('`_util.py:93` reads … as the run-attempt count')
CLAIM: Following the pointer will not fix `_util.py:93` on its own: +0x4C is not runTries in Emerald's BattleStruct. (The move-learn read's +0x10 is expGetterMonId, which is correct once the pointer is followed.)
EVIDENCE: From battle.h:354-381, computed below: +0x4C = switchInAbilitiesCounter and runTries = +0x6C. expGetterMonId = +0x10 matches battle_move_replacing.py:147's intent.
FIX: Put both the pointer follow and the 0x4C→0x6C offset into #27-battlestructptr's scope.

### checked and found true
- G1 VERIFIED. ItemUseCB_Medicine heals gPlayerParty[gPartyMenu.slotId] and calls RemoveBagItem(item,1) only on the success branch (party_menu.c:4396-4434). PokemonUseItemEffects writes party HP and gBattleMons[battler].hp at menu time (pokemon.c:5082-5096); status cures write the party and gBattleMons[battler].status1 (pokemon.c:5306-5316, plus STATUS2_NIGHTMARE at :4930-4935 and confusion at :4945-4949). A non-Revive item on a 0-HP mon is refused (pokemon.c:5056-5062) with 'won't have any effect'. Failure returns to the BAG (exitCallback NULL, then CB2_ReturnToBagMenu, party_menu.c:4477, :1238-1241, :5783). Success returns to battle (CB2_SetUpExitToBattleScreen, party_menu.c:1312-1313).
- Target resolution: PokemonUseItemEffects matches gBattlerPartyIndexes[i] == P for i = 0, 2 on the chooser's side (pokemon.c:4789-4802). gBattlerInMenuId picks only the side, so either battler can heal either mon, and the game never enforces self-only.
- G2, in-battle party layout: IsDoubleBattle and not IsMultiBattle gives PARTY_LAYOUT_DOUBLE (party_menu.c:5765-5772). ChooseMonForInBattleItem calls UpdatePartyToBattleOrder synchronously (party_menu.c:5781-5786). The field order is restored before the callback switches (party_menu.c:1233-1236, :6089-6098). So gPlayerParty[slotId] is the menu-slot mon while the menu is open, and normal order during action selection. slotId is byte 9 of gPartyMenu (include/party_menu.h:9-21); layout is bits 4-5 of byte 8 (PARTY_LAYOUT_DOUBLE = 1). The cursor opens on slot 0 (party_menu.c:524-525).
- Positions 0 and 1 of a non-multi double's order always hold P(left) and P(right). They are built after SetBattlePartyIds (battle_controllers.c:97-103). SwitchPartyOrder swaps the outgoing and incoming positions before getswitchedmondata (battle_main.c:4086-4105; battle_scripts_1.s:3110-3111, :2844-2845). battlerPartyOrders[0] == [2] for the whole battle, because SwitchPartyOrder's DOUBLE branch writes both (battle_main.c:4099-4105), including forced switches (battle_script_commands.c:7364).
- The lever --set-party-hp 0=0 sends P1 left and P2 right (SetBattlePartyIds skips HP==0 and the partner's index, battle_controllers.c:585-630). The order is 12 03 45, so both battlers discriminate. The leader still needs 2 or more alive mons (trainerbattle_double at MossdeepCity_Gym/scripts.inc:52; GetMonsStateToDoubles, pokemon.c:4507-4525).
- G3 VERIFIED. B on battler 2's action menu returns without cancelling when battler 0 chose a non-ball item. After a move or switch it emits B_ACTION_CANCEL_PARTNER (battle_controller_player.c:304-321). The B path needs position PLAYER_RIGHT, so B on battler 0's menu is inert.
- gActionSelectionCursor is u8[4], indexed by game battler id (battle_main.c:225). A reads [gActiveBattler] (battle_controller_player.c:249). Each menu reopens at its own byte (battle_controller_player.c:2586), so the right battler starts on FIGHT at battle start. Reset points: battle start (battle_controllers.c:52), SwitchInClearSetData (battle_main.c:3203), FaintClearSetData (battle_main.c:3285), HandleAction_Switch (battle_util.c:299), PlayerHandleSwitchInAnim (battle_controller_player.c:2190), and the RESET_ACTION_* handlers (battle_controller_player.c:3104-3110). The only emit sent is RESET_MOVE_SELECTION (battle_script_commands.c:7802). There is no per-turn reset, and HandleAction_UseItem (battle_util.c:312-331) does not reset it, so an item user's byte stays 1. C1 is inert today by construction: both bytes stay 0 in doubles.
- The right battler's item path is identical. EmitChooseItem(battlerPartyOrders[2]) (battle_main.c:4236; payload copied at battle_controllers.c:1231-1238). PlayerHandleChooseItem sets gBattlerInMenuId=2 and copies the order into gBattlePartyCurrentOrder (battle_controller_player.c:2653-2663). Battler 2 uses SetControllerToPlayer in a non-link double (battle_controllers.c:217-229). The only difference: the party cursor still opens on slot 0 (the LEFT mon), so self-heal takes one Down.
- A refused or cancelled item (item 0) sends the SAME battler back to STATE_BEFORE_ACTION_CHOSEN (battle_main.c:4406-4410). Battler 2 is prompted only after battler 0 is confirmed (battle_main.c:4145-4148). So a guard refusal re-prompts the refusing battler, and its verdict is judged before the partner can consume the same item type. That supports D4's 'bag dropped implies intended mon took it' under the per-Pokémon ledger.
- struct BattleStruct layout (include/battle.h:354-381, ARM alignment): 0x00 turnEffectsTracker, 0x01 turnEffectsBattlerId, 0x02 unused_0, 0x03 turnCountersTracker, 0x04-0x0B wrappedMove[8], 0x0C-0x0F moveTarget[4], 0x10 expGetterMonId, 0x11 unused_1, 0x12 wildVictorySong, 0x13 dynamicMoveType, 0x14-0x17 wrappedBy[4], 0x18-0x47 assistPossibleMoves u16[24], 0x48 focusPunchBattlerId, 0x49 battlerPreventingSwitchout, 0x4A moneyMultiplier, 0x4B savedTurnActionNumber, 0x4C switchInAbilitiesCounter, 0x4D faintedActionsState, 0x4E faintedActionsBattlerId, 0x4F pad, 0x50 expValue u16, 0x52 scriptPartyIdx, 0x53 sentInPokes, 0x54-0x57 selectionScriptFinished[4], 0x58-0x5B battlerPartyIndexes[4], 0x5C-0x5F monToSwitchIntoId[4], **0x60-0x6B battlerPartyOrders[4][3]** (battler 0 at +0x60, battler 2 at +0x66), 0x6C runTries. gBattleStruct is a heap pointer: AllocZeroed at battle_util2.c:25 via AllocateBattleResources (battle_main.c:591), freed only at battle end (battle_util2.c:57). It is valid during action selection and while the bag or party menu is open.
- PARTY_LAYOUT_DOUBLE cursor: Up/Down step through non-empty slots in order (UpdatePartySelectionDoubleLayout / GetNewSlotDoubleLayout, party_menu.c:1588-1695). chooseHalf is FALSE in battle (party_menu.c:511-514), so Down from the last mon and Up from slot 0 both go to Cancel = 7. Empty indexes always sit at the tail of the order, because only real mons are swapped, so there are no gaps. scroll_to_party_menu_index (sandbox-pokebot/modules/menuing.py:144-226) reaches slot 0 or 1 in at most one Down and does not misroute any self or partner target in the DOUBLE layout.
- Tate & Liza AI: action, move and target are chosen during selection. Battler 1 is prompted in the same pass as battler 0, and battler 3 right after battler 1 confirms (battle_main.c:4143-4172, :4458-4478; battle_controller_opponent.c:1540-1567). This is before our party-menu heal lands, and if_can_faint uses gBattleMons[target].hp at that moment (battle_ai_script_commands.c:1743-1770). So a healed mon still takes the attack aimed at it, and no retarget happens. Their Hyper Potions come from one pool and fire only at hp < maxHP/4 or missing > 200 (battle_ai_switch_items.c:835-870). Only our side needs measuring.
- D1 bit values match the decomp: Double 1<<0, Trainer 1<<3, Multi 1<<6, TwoOpponents 1<<15, InGamePartner 1<<22 (include/constants/battle.h:59-81 vs battle_state.py:43-65). Two-opponent doubles give the player both battlers.
- V-list gBattleStruct misreads VERIFIED: gBattleStruct is a 4-byte pointer (pokeemerald.sym:181, 0x0202449c), and read_symbol adds the offset to the symbol address without following the pointer (memory.py:66-70). 0x0202449c+0x10 = 0x020244ac = gActionSelectionCursor (sym:185), read by battle_move_replacing.py:147. 0x0202449c+0x4C = 0x020244e8 = sLearningMoveTableID (sym:199), read by _util.py:93.

# LENS proof

## proof:F1 [blocker] DESIGN §6 rows D-SLOT and D-NOG; §5 S0-5 (no precondition on the partner)
CLAIM: D-SLOT's physical checks cannot fail, and D-NOG can produce a false refutation, whenever the partner is at full HP (or fainted) at the acting decision. In that case the game refuses the item itself, so arms that are meant to prove the guard load-bearing show nothing. The design never requires the partner to be hurt at S0-5's frame, and the Tate & Liza fixture makes a full-HP partner likely.
EVIDENCE: Decomp: HP is restored only 'if not at max health' (pokemon.c:5082-5114; retVal becomes FALSE only inside that branch). ItemUseCB_Medicine then shows gText_WontHaveEffect and skips RemoveBagItem (party_menu.c:4412-4426, RemoveBagItem only at :4434). A 0-HP target is also refused (pokemon.c:5056-5062). So with a full-HP partner, D-SLOT's 'bag count unchanged, the partner's HP unchanged' holds whether or not the guard fires; only the guard's own `ok=0` line differs, which is the instrument under test (rule 7). D-NOG's 'the wrong PID's HP rises and the bag drops' then fails, which reads as 'the guard is not load-bearing'.
Fixture: FIXTURES.md5:96 (worktree, uncommitted) records d13_tateliza.ss1 with all six at full HP. With `--set-party-hp 0=0` the actives are Zigzagoon L15 (P1) and Swellow L40 (P2) (battle_controllers.c:585-630). Claydol's Earthquake hits Zigzagoon, and Swellow is Flying and immune (trainer_parties.h:3552). The L15 mon is likely KO'd on turn 1 and replaced at end of turn by a full-HP bench mon. So the likely first requester is Swellow (side 1), with a fresh full-HP partner. The time to the first act is INFERRED, not measured.
FIX: Add pre-registered preconditions to D-SLOT and D-NOG, computed in S0-5 from the OFF [TURN] lines. At the acting decision the partner must be present, alive and below max HP; for a status item it must also hold a curable status. If those fail at the first act, pick the first frame where they hold, or use the post_mtpyre arm proposed in F4, where the partner (Swellow 18/109) is hurt at the very first decision.
VERDICT: refuted=False corrected=blocker
REASONING: I could not refute F1. The game mechanism is right, the design says nothing about the partner's state, and the fixture makes the bad case plausible.

1. **Mechanism, verified in the decomp.** HP is restored only when current HP differs from max HP, and `retVal = FALSE` (the item applied) is set only inside that branch. A non-Revive item on a 0-HP Pokémon breaks out before that branch. `ItemUseCB_Medicine` then shows WontHaveEffect and never reaches `RemoveBagItem`. So with a partner at full HP (or fainted), the partner's HP and the bag count stay the same whether the guard fires or not. The same holds for a status cure on a partner that has no status.

2. **The design does not handle it.**
   - S0-5 pre-registers only the requester's frame, side, item, target PID, M_truth and P. It sets no condition on the partner.
   - The D-SLOT and D-NOG rows set none either.
   - D4's premise ("a wrong slot is often the LIVING partner, which consumes the item silently") carries the same unstated assumption. It comes from the adversary recon's F3/D1, which also treats "living" as enough. The game needs the partner to be below max HP, or to hold a status the item cures.
   - Nothing else in the design or in the six recon notes addresses a partner at full HP.

3. **The bad case is plausible on d13_tateliza.**
   - FIXTURES.md5:96 records all six Pokémon at full HP.
   - With `--set-party-hp 0=0`, SetBattlePartyIds sends Zigzagoon L15 and Swellow L40.
   - Claydol L41 has Earthquake. Swellow is Flying and immune to it; Zigzagoon at L15 is likely KO'd on turn 1 and replaced by a full-HP bench Pokémon.
   - My rough estimate (not measured): one Psychic from Xatu L41 takes a large share of Swellow's HP. So Swellow (side 1) could cross 0.35 at the turn-2 decision, while its partner is the fresh replacement.
   - Rule 3 (`battle_items.py`) turns down the fixture's Potion (heals 20) once the worst hit is large. So the first act is either a bigger HP item added with `--set-bag-item`, or the Full Heal on a sleeping requester (Lunatone has Hypnosis). For a Full Heal, the partner would also need a status.

4. **Effect.** With a partner at full HP:
   - D-SLOT's physical checks (bag count unchanged, partner's HP unchanged) cannot fail.
   - D-NOG's prediction (the wrong PID's HP rises and the bag drops) fails.
   - So the D-SLOT/D-NOG pair would show no difference between the arms. That is the vacuous A/B that reads as a refutation of a true finding, which CLAUDE.md's Tier 2 (4) names explicitly.

5. **What limits the finding.**
   - It depends on the run's trajectory; the turn of the first act is inferred, not measured.
   - D-SLOT still has checks that can fail (`ok=0`, `guard refused`), and §7's fake-emulator gate row already tests "no A press on a PID mismatch" offline.
   - So what is lost is the live proof that the guard is load-bearing, not production behaviour.

6. **Severity.** It still meets the task's blocker test: as written, an arm is unable to fail on its physical checks, and nothing pre-registered stops that. The fix is cheap, and the design's own lever already supports it:
   - add the proposed partner preconditions to S0-5, computed from the same `[TURN]` lines; or
   - use `--set-party-hp` to hurt the partner in both arms; or
   - use the post_mtpyre double, where the fixture recon reports Sceptile at 21/117 and Swellow at 18/109.
REFUTER EVIDENCE: **Decomp** (scratchpad `decomp/pokemon.c`, same text as pret/pokeemerald `src/pokemon.c`):
- `:5056-5062`: `else { if (GetMonData(mon, MON_DATA_HP, NULL) == 0) { itemEffectParam++; break; } }`. A non-Revive item on a 0-HP target breaks out before any heal.
- `:5081-5082`: `// Only restore HP if not at max health` / `if (GetMonData(mon, MON_DATA_MAX_HP, NULL) != GetMonData(mon, MON_DATA_HP, NULL))`.
- `retVal = FALSE` is set only inside that branch.

**Decomp** (scratchpad `decomp/party_menu.c`, same as `src/party_menu.c`), `ItemUseCB_Medicine`:
- `:4413`: `if (hp == GetMonData(mon, MON_DATA_MAX_HP)) canHeal = FALSE;`
- `:4419-4425`: if `cannotUse`, then `gPartyMenuUseExitCallback = FALSE` and `DisplayPartyMenuMessage(gText_WontHaveEffect, TRUE)`.
- `:4434`: `RemoveBagItem(item, 1)` appears only in the else (success) branch.

**Decomp**, `battle_controllers.c:584-630` (SetBattlePartyIds): each player battler takes the first party slot with HP != 0. With slot 0 set to 0 HP, the actives are slots 1 and 2.

**Decomp**, `trainer_parties.h:3546-3574` (sParty_TateAndLiza1):
- Claydol L41: Earthquake, Ancient Power, Psychic, Light Screen.
- Xatu L41: Psychic, Sunny Day, Confuse Ray, Calm Mind.
- Lunatone L42: Hypnosis, and others.

**Design** (`2026-09-30-doubleitems13-DESIGN.md`):
- `:184-187` (S0-5) pre-registers only "its frame, side, item, target PID, M_truth and P". There is no partner HP or status condition.
- `:199` (D-SLOT): "bag count unchanged, the partner's HP unchanged".
- `:200` (D-NOG): "the wrong PID's HP rises and the bag drops. ⇒ the guard is load-bearing".
- `:94-95` (D4): "a wrong slot is often the LIVING partner, which consumes the item silently". The HP/status condition is missing.

**Recon notes** (`2026-09-30-doubleitems13-recon/`):
- `d13_recon_adversary.md:55`, `:158`: the same "living partner is consumed" framing.
- `d13_recon_fixture.md:73`: post_mtpyre has Sceptile 21/117 and Swellow 18/109, both hurt at the first double.

**Fixture**, `tools/story-dev/saves/FIXTURES.md5:96` (worktree, uncommitted): d13_tateliza.ss1 has "Sceptile L47, Zigzagoon L15, Swellow L40, Skitty L17, Mightyena L43, Castform L36, all at full HP ... Potion x1, Full Heal x1".

**Our code:**
- `sandbox-pokebot/modules/story/battle_items.py`, choose_healing_item, rule 3: `if worst_hit_taken and best_possible < worst_hit_taken: return None`. The fixture's Potion (heals 20) is turned down once the worst hit exceeds 20.
- `sandbox-pokebot/plugins/custom_modes/story_mode.py`, the `choose_status_or_revive_item` branch: a Full Heal can be the first act. For WRONGSLOT to consume it, the partner would need a status.

## proof:F2 [should-fix] DESIGN §3 C5 (telemetry); §6 D-ON 'that PID's HP rises', D-SLOT 'the partner's HP unchanged', D-NOG 'the wrong PID's HP rises and the bag drops'
CLAIM: No specified line reads HP by PID, or the bag count, after the A press. Every HP criterion in D-ON, D-SLOT and D-NOG would therefore be graded from post-turn readings that the turn's damage confounds. D-SLOT's 'partner HP unchanged' is false across any turn in which the partner is hit.
EVIDENCE: C5's `[DBLITEM] use` and `[DBLITEM] menu` lines are logged before A. The executor's stages after A (`target-chosen`, `returned-to-battle`, battle_action_selection.py:1135-1140) log no HP. `[TURN]` prints the snapshot HP at the next decision (bas:519-541), and battler 2's snapshot is re-read before battler 0's action (bas:577-579). The existing verdict says of its own HP: 'a post-turn value, NOT the heal's result — see KI-101 blocker 1' (story_mode.py:967-969), and it only prints if the requester decides again. mossdeepbadge prints no `[TRAINER] … heal_stock=` line (story_harness.py:3401-3409 builds the strategy directly). The debug_logger `[PARTY]` events carry species and level only (debug_logger.py:536-544). A real counter exists: gBattleResults+0x03, numHealingItemsUsed (include/battle.h:239), which rises only when an HP item lands on an active player battler (pokemon.c:5099-5100).
FIX: Add a flag-only raw read at `returned-to-battle` (or at the first frame after A where gPlayerParty is back in field order), for example `[DBLITEM] after`. It should carry, by PID: both actives' HP from raw gPlayerParty, the requested item's bag count from the save block, and gBattleResults[3]. Grade D-ON, D-SLOT and D-NOG on that line, never on the next [TURN].
VERDICT: refuted=False corrected=should-fix
REASONING: The finding survives on its main claim, which is about HP by PID. One part is slightly overstated: the bag count.

**HP by PID.** Nothing the design specifies reads HP between the A press and the turn's damage.
- C5's two acting lines (`[DBLITEM] use`, `[DBLITEM] menu`) both come before A.
- After A, the executor logs only the state and the item name (`target-chosen`, `returned-to-battle`).
- The handler exits once both battlers have chosen and is re-entered next turn with a fresh `get_battle_state()`. So the requester's next `[TURN]` line is post-damage.
- In the same entry, battler 2's `[TURN]` line uses the stale entry snapshot, because the re-read happens only after that log line.
- The verdict's HP is labelled post-turn in our own code.
- The only existing flag-gated clean read is DMGAUDIT's BEFORE at selection exit. It is taken after the item applies and before any damage, but it dumps gBattleMons for battlers 0 and 1 only, so the player's right-hand Pokémon (battler 2) is missing. The design also never sets that flag in any arm. So the case is not already handled.
- Effect on each arm:
  - **D-SLOT:** "the partner's HP unchanged" will read as false whenever a foe hits the partner that turn, which is likely in a double.
  - **D-NOG:** "the wrong PID's HP rises" is confounded by the same damage.
  - **D-ON:** "that PID's HP rises" is confounded too.

**Bag count (overstated).** The design does name a post-A bag read. D4 relies on "the requester's next verdict", which reads `get_item_bag().quantity_of` at the requester's next decision. Damage cannot confound a bag count. But under D3's per-(PID, species) ledger, that verdict prints only if the same Pokémon decides again. If it faints that turn (plausible when healing at ≤35% against two foes), or the battle ends, the arm's "bag drops by 1" has no line to grade it.

**Why should-fix, not blocker.** The confound causes false failures and ambiguity; it does not make any arm unable to fail. The identity proof still has other gradeable criteria: `ok=`, `guard refused`, no A press, `menu_pid`, and the verdict when the requester lives. The fix is one flag-only line. The decomp recon had already listed this read as rule-10 ground truth ("after the menu closes, the HP change of the intended mon, found by PID in normal order ... gBattleResults[3]"), and the design dropped it from C5. The proposed fix (a raw post-A line by PID, with the bag count and gBattleResults+3) works: G1 makes HP and the bag count final before the menu closes. Reading by PID also avoids any party-order dependence.
REFUTER EVIDENCE: - **No post-A telemetry in the design:** DESIGN :145-150. Only `[DBLITEM-OBS]`, `use`, `menu` (at PARTY_MENU, before A) and `guard refused` are specified. The arms' HP criteria are at :197, :199 and :200.
- **Executor after A:** `sandbox-pokebot/modules/battle_action_selection.py:1133-1140`. It presses A, logs `_stage("target-chosen")`, presses B until BATTLEMAINCB2, then logs `_stage("returned-to-battle")`. `_stage` (:1022-1030) prints only the state and item name.
- **Handler timing:**
  - :116 `battle_state = get_battle_state()` on entry.
  - The loop runs while the main callback is HandleTurnActionSelectionState, so it exits once the turn executes.
  - The `[TURN]` log (:519-541) runs before the re-read at :577-579 (`if previous_battler_index != battler_index: battle_state = get_battle_state()`). So battler 2's `[TURN]` in the same entry prints the stale entry snapshot, and the next turn's `[TURN]` is post-damage.
- **The verdict's HP is post-turn:** `plugins/custom_modes/story_mode.py:969` reads "(a post-turn value, NOT the heal's result — see KI-101 blocker 1)".
- **The verdict's bag read is conditional:** :956 `_consumed = get_item_bag().quantity_of(_req_item) < _req_qty`, which D4 (DESIGN :92-93) relies on. Under D3's per-PID ledger (DESIGN :77-86) it runs only when the same Pokémon decides again.
- **DMGAUDIT does not cover it:** `modules/dmgaudit.py:154-166` logs a BEFORE after both choices, and :79 `"mons=" + ... for i in range(2)` dumps battlers 0 and 1 only. The design's arms never set it.
- **Harness strategy:** `tools/story-dev/story_harness.py:3401-3407` builds `StoryItemBattleStrategy()` directly.
- **Decomp:**
  - `src/pokemon.c:5085-5100`: SetMonData HP, then `gBattleMons[battler].hp = dataUnsigned`, and `numHealingItemsUsed++` only for an active player battler and a non-Revive item.
  - `include/battle.h:239`: `u8 numHealingItemsUsed; // 0x3`.
  - `src/party_menu.c:4416` and `:4434`: the effect applies, then `RemoveBagItem` runs, at selection (G1). A clean post-A read is therefore possible.
- **The recon already named this read:** `d13_recon_decomp.md:110-111` ("after the menu closes, the HP change of the intended mon, found by PID in normal order, confirms the heal; ... gBattleResults[3] confirms an HP item landed on an active battler").

## proof:F3 [should-fix] DESIGN §6 D-ON 'the partner's move that turn completes with no KI-45'; D-CUR '(KI-45 or a not-consumed verdict) … predicted from which side acts first'
CLAIM: D-ON's C1 check passes trivially when the acting side is battler 2, because battler 0 has already chosen that turn. It is also absent if battler 2 is not asked. For side 1 the C1-dependent events are different, and the design names none of them. D-CUR's hedge is imprecise: at the first act CURSOR0 gives KI-45 whichever side acts.
EVIDENCE: The right flank is prompted only after the left partner is confirmed or absent (battle_main.c:4143-4170). The handler decides battler 0 first (bas:198-205), then battler 2 (bas:207-212). So a side-1 item is always chosen after battler 0's FIGHT has already been scrolled with byte 0 = 0. For side 1, C1 is exercised by battler 2's own BAG scroll (byte 2 must go 0→1) and by its next-turn FIGHT: byte 2 stays 1 because the cursor resets only at battle start (battle_controllers.c:52), switch-in (battle_controller_player.c:2190) or a reset command (:3106-3110). If Swellow faints before its next decision, that second event never happens.
CURSOR0, side 0: byte 0 = 1, battler 2's cursor is at 0, and Left is a no-op at 0 (battle_controller_player.c:266-275). Side 1: byte 0 = 0, battler 2's cursor goes to 1, and Right is a no-op at 1 (:276-285). In both cases byte 0 never changes, so the 60-step bound raises KI-45 (battle_menuing.py:27, 38-55). The 'not consumed' alternative needs a previous battler-0 item and cannot be the first act.
FIX: Split D-ON's C1 criterion by side. Side 0: battler 2's same-turn FIGHT completes with no KI-45. Side 1: battler 2's BAG scroll converges, and its next-turn FIGHT with byte 2 = 1 completes, or the check is declared absent if it faints. Require that battler 2 is present and asked. Predict D-CUR exactly as KI-45 on the scroll named for the acting side.
VERDICT: refuted=False corrected=should-fix
REASONING: F3's main claim holds: D-ON's C1 criterion only tests anything when side 0 acts. Its D-CUR sub-claim goes too far, and its proposed D-CUR fix would predict one case wrongly. Severity stays should-fix, not blocker. D-ON can still fail on its item criteria, and a pure gate row (§7, `scroll_to_battle_action(1, True)` reads byte 2) covers the side-1 mechanism with a fake `read_symbol`. The gap is that the live D-ON/D-CUR pair has no pre-registered side-1 check.

1. **D-ON's criterion ("the partner's move that turn completes with no KI-45") is vacuous for side 1. Confirmed.**
   - Order: the game prompts the right flank only after the left partner is confirmed or absent (battle_main.c:4145-4148). The handler also decides battler 0 before battler 2 (battle_action_selection.py:198-212). So when battler 2 is the one using the item, the partner is battler 0, whose FIGHT scroll has already run.
   - That scroll reads byte 0 with or without C1, so the criterion cannot fail on a broken C1.
   - The item criteria do not rescue it. Under StoryMode, a KI-45 is DEFERRED, not raised: `handles_battle_faults = True` (story_mode.py:2123), and `request_mode_recovery` returns True (battle_fault.py:39-44). `_select_in_menu` then simply returns (battle_menuing.py:53-54), and `battle_action_use_item` goes on to press A (bas:1043-1050).
   - On side 1 with a broken C1, the first Right press has already moved byte 2 from 0 to 1, and further Right presses do nothing (battle_controller_player.c:276-285). So A opens the bag and the item lands: ok=1, the bag count drops and HP rises. The pending fault only stops the handler afterwards (battle_handler.py:330-333). D-ON as written therefore passes with a broken C1 on side 1.
   - Nothing else in the design asserts "no KI-45" on battler 2's own BAG scroll. KI-45 appears only on lines 197-198, and "= D-OFF" applies only up to S0-5's frame.
   - Side 1 is not a corner case. With `--set-party-hp 0=0` the actives are party 1 (Zigzagoon, L15) and party 2 (Swellow, L40) (fixture recon :104-106). The first act may well come from Swellow.
   - The next-turn point also holds. Byte 2 resets only at battle start (battle_controllers.c:52), at switch-in (battle_controller_player.c:2190), on a switch action (battle_util.c:299), or on a reset command (battle_controller_player.c:3106-3110). The only reset sent is RESET_MOVE_SELECTION (battle_script_commands.c:7802), which leaves the action cursor alone. So byte 2 stays at 1, and battler 2's next FIGHT is a real C1 event.

2. **The D-CUR sub-claim is partly refuted.** F3 says the not-consumed alternative "cannot be the first act". That is wrong when both battlers request an item on the first acting turn.
   - Battler 0's item moves byte 0 to 1. Battler 2's BAG scroll under CURSOR0 then reads byte 0 = 1, which equals the target, so it presses nothing (battle_menuing.py:67-74).
   - A is then pressed on byte 2 = 0, which is FIGHT (battle_controller_player.c:249-252). The bounded re-press loop commits a move and returns "bag-did-not-open" (bas:1043-1056). The result is a not-consumed verdict, not KI-45.
   - So the design's hedge "(KI-45 or a not-consumed verdict)" covers a real case. F3's fix, "KI-45 on the scroll named for the acting side", would predict it wrongly.
   - The design's wording is still loose. The failure depends on battler 2's action that turn, not only on "which side acts first". And for side 1, "the cursor for the other battler" names the wrong battler: there the wrongly read cursor belongs to the acting battler itself.
   - F3 is right about the single-actor cases:
     - Side 0 acts: Left at byte 2 = 0 is a no-op (:266-275), so battler 2's FIGHT scroll hits KI-45 after 60 steps (battle_menuing.py:27, 38-55).
     - Side 1 acts: Right at byte 2 = 1 is a no-op (:276-285), so battler 2's own BAG scroll hits KI-45.

Corrected fix:
- **D-ON:** split the criterion by side.
  - Side 0: battler 2's same-turn FIGHT scroll converges with no KI-45.
  - Side 1: battler 2's own BAG scroll converges with no KI-45, and its next-turn FIGHT (with byte 2 = 1) converges. If Swellow faints first, that second event is declared absent.
  - Require that battler 2 is present and actually prompted.
- **D-CUR:** predict from the acting turn's full action pair:
  - side 0 acts and battler 2 fights: KI-45 on battler 2's FIGHT scroll;
  - side 1 acts: KI-45 on battler 2's BAG scroll;
  - both battlers request items: not-consumed for battler 2.
REFUTER EVIDENCE: - **Decision order:** battle_main.c:4145-4148 prompts the right flank only when the left is confirmed or absent. The handler decides battler 0 first (sandbox-pokebot/modules/battle_action_selection.py:198-205), then battler 2 (:207-212).
- **The criterion as written:** DESIGN §6:197 "the partner's move that turn completes with no KI-45". The design mentions KI-45 only at lines 197-198. "= D-OFF" applies only up to S0-5's frame.
- **The deferred KI-45 path:**
  - battle_menuing.py:53-54 returns instead of raising when `request_mode_recovery` succeeds.
  - story_mode.py:2123 sets `handles_battle_faults = True`, and battle_fault.py:39-44 records the fault and returns True.
  - battle_action_use_item continues and presses A (battle_action_selection.py:1034, 1043-1050).
  - The handler stops only afterwards (battle_handler.py:330-333).
- **Cursor behaviour in the game:**
  - Right is a no-op at 1 (battle_controller_player.c:276-285); Left is a no-op at 0 (:266-275).
  - A acts on `gActionSelectionCursor[gActiveBattler]` (:249-262).
  - Resets happen only at battle_controllers.c:52, battle_controller_player.c:2190, battle_util.c:299 and :3106-3110. The only reset sent is RESET_MOVE_SELECTION (battle_script_commands.c:7802).
- **The both-act case that refutes F3's D-CUR claim:** the scroll exits at once when the byte it reads equals the target (battle_menuing.py:67-74). The bounded bag-open retry then commits FIGHT or a move and returns (battle_action_selection.py:1043-1056).
- **Mitigation already in the design:** the §7 gate row "`scroll_to_battle_action(1, True)` reads byte 2 (fake `read_symbol`)" covers the side-1 mechanism statically but not in the live arms.
- **Why side 1 is plausible:** the fixture recon (d13_recon_fixture.md:104-106) gives party slot 1 = Zigzagoon L15 and slot 2 = Swellow L40, which are the actives under `--set-party-hp 0=0`.

## proof:F4 [should-fix] DESIGN §6 X-BASE/X-BUILD (and D-OFF 'equal to the base-code Step-0 run'); §5 S0-6
CLAIM: The X arms are identical by construction. With the flag unset, a trainer double never selects anything but FIGHT, so bytes 0 and 2 are both 0 at every call and X can fail only on a crash. The same pinned fixture already holds a natural, non-trivial arm: a battler-0 heal on the first decision of the first Route 123 double, with a hurt partner and a non-identity order. The design runs it only with the flag unset.
EVIDENCE: The trainer double branch returns only UseMove variants (story_mode.py:563-614). Cursors reset at battle start and on switch-in (battle_controllers.c:52; battle_controller_player.c:2190). Battler 2's FIFGHT does reach `scroll_to_battle_action(0)` (bas:1197-1198), but with equal bytes.
evidence/2026-09-29-r27keyitems-M0-liveA.txt:8-9: the first double (f3148510, HEX_MANIAC+COLLECTOR) starts with party [Mightyena 0/124, Sceptile 21/117, Swellow 18/109, Skitty 0, Zigzagoon 16/16, Castform 0] and heal_stock=Hyper_Potion:1. So the actives are P1 and P2 with no lever (battle_controllers.c:585-630), and the order is [1,2,0,…] (party_menu.c:5969-5985). At battler 0's first decision worst=0 disables rule 3 (battle_items.py:92-95), and 21/117 = 0.18 ≤ 0.35, so the Hyper Potion is chosen (story_mode.py:1098-1105). The bag is then empty, so battler 2 (Swellow) FIGHTs with byte 0 = 1 and byte 2 = 0. The league reserve is not armed there (league_reserve.py:214). Both classes are non-key (trainer_identity.py:63-67).
FIX: Keep X, but word it as a no-crash regression check. Add X-ON on post_mtpyre (PINNED 80602159694b), storyresume, DOUBLEITEMS=1, KEYITEMS unset. It gives, all on a pinned fixture with no state write: a non-trivial C1 check (battler 2's FIGHT after a battler-0 item); D-CUR binding as KI-45; D-SLOT and D-NOG binding on a hurt partner (Swellow 18/109); and, with KEYITEMS=1 added, D6's composition control (no item in a non-key double). Re-measure on HEAD first (KI-112; M0 was on 7dcd69fd).
VERDICT: refuted=True corrected=nit
REASONING: The finding's facts about the cursor bytes are right, but the claims that make it a defect are overstated, and the coverage it asks for is mostly there already.

1. **The design already says X is equal by construction.** D7 (DESIGN:113-115) states: "today's code never reaches a state where byte 0 and byte 2 differ. Both cursors reset at battle start and both stay on FIGHT, so the fix is INERT today." It then presents X only as the rule-9 A/B on the ordinary case (DESIGN:11, :201). CLAUDE.md rule 9 prescribes exactly that test for a change on a shared path. X never claims to prove that C1 is correct.

2. **"X can fail only on a crash" is false, for two reasons.**
   - X checks the construction premise against a real run. Suppose some path the author missed moved byte 0 away from 0 in an ordinary double. The base code would then read the wrong byte for battler 2 and derail, the build would not, and X-BASE and X-BUILD would differ. V6's search of 4,520 logs is the same check run over the corpus, not something X repeats trivially.
   - X-BUILD also runs C2-C4 with the flag unset, not only C1. C3 changes `_maybe_use_item` itself: the `side` argument and the two `left_battler` reads (DESIGN:140-141). The same 90k-frame window includes a real singles heal: M0-liveA:47 "[ITEM] using Hyper Potion on Mightyena 30/127". So a mistake in how C3 picks the side in singles would make X fail without any crash.

3. **C1 already has two checks that can fail, on the pinned fixture.**
   - D-ON requires "the partner's move that turn completes with no KI-45" (DESIGN:197). Pressing the D-pad changes only the active battler's byte (battle_controller_player.c:268-303). Nothing resets byte 0 between battler 0 picking BAG and battler 2's choice: the resets are at battle start, switch-in and action reset (battle_controllers.c:52, battle_controller_player.c:2190, :3106-3110, battle_util.c:299). So when battler 2 picks FIGHT, byte 0 = 1 and byte 2 = 0. Code without C1 reads byte 0 there (battle_menuing.py:57-61, :89-91) and keeps pressing Left, which does nothing at FIGHT (bcp.c:268 needs cursor&1). That ends in KI-45.
   - If battler 2 is the one using the item instead, pre-C1 code cannot reach BAG: byte 0 stays 0 after Right is pressed.
   - D-CUR is the fault arm that removes C1 (DESIGN:198). The finding's "non-trivial C1 check" and "D-CUR binding as KI-45" are therefore already in the design.

4. **What survives is an improvement, not a defect.** The recon ranked `post_mtpyre.ss1` first for the observe probe and named it as a composition control (d13_recon_fixture.md:9, :64-73, :120). The design uses it only with the flag unset and does not say why it dropped the recon's pick for the flag-set arms. Checked against our code, the finding's natural case is plausible:
   - The bag is read live (story_mode.py:1047), so battler 2 sees it empty after battler 0's item.
   - The heal policy returns the Hyper Potion at 21/117 with worst hit 0 (battle_items.py:77-106).
   - No trainer battle comes before f3148510 (M0-liveA:4-9).

   The arm the finding proposes would add a run with no state write and a live check of D6 (which today is covered only by a gate row using fakes, DESIGN:214). Both are worthwhile but optional, and the proposed wording "no-crash regression check" is less accurate than the design's. This is a nit, not should-fix.
REFUTER EVIDENCE: Design text:
- DESIGN:113-115 (D7): "Both cursors reset at battle start and both stay on FIGHT, so the fix is INERT today. That inertness is not assumed; arm X measures it on the ordinary case (rule 9)."
- DESIGN:197, D-ON: "the partner's move that turn completes with no KI-45".
- DESIGN:198, D-CUR is the C1 fault arm.
- DESIGN:140-141, C3 modifies `_maybe_use_item` (the side select), and this code runs in X-BUILD with the flag unset.

Decomp:
- battle_controller_player.c:268-303: the D-pad changes only gActionSelectionCursor[gActiveBattler], and Left at FIGHT is a no-op because it needs cursor&1.
- The only resets are battle_controllers.c:52, battle_main.c:3203/3285, battle_controller_player.c:2190 and :3106-3110, and battle_util.c:299. None of them runs between battler 0's BAG and battler 2's choice.

Our code:
- battle_menuing.py:57-61 and :89-91: the read uses byte 0 unless use_third_byte, and scroll_to_battle_action passes no side.
- battle_action_selection.py:1197-1198: FIGHT goes through scroll_to_battle_action(0).
- story_mode.py:563-614: the trainer branch of the double returns only UseMove.
- story_mode.py:1047: the bag is read live.
- battle_items.py:77-106: the policy picks the item at 21/117 when worst=0.

Evidence file tools/story-dev/evidence/2026-09-29-r27keyitems-M0-liveA.txt:
- :4-9: only RanAway battles come before the first double at f3148510, and heal_stock is Hyper_Potion:1.
- :47: a singles Hyper Potion is used at f3196418, inside X's 90k-frame window.

Recon: d13_recon_fixture.md:9, :64-73 and :120 rank post_mtpyre first and name it as the composition control. The design does not adopt it for any arm with the flag set and records no reason why.

## proof:F5 [should-fix] DESIGN §2 D5 'observe … with NO state change'; §3 C5 OBS fields `would= … worst=`; §7 'observe → super() result, no state change'; §6 D-OBS 'first would≠- row = S0-5's discriminator'
CLAIM: Observe cannot compute `would` the way ON decides, because the decision depends on a worst-hit ledger that builds up across decisions, and observe is forbidden to keep state. With worst stuck at 0, observe ignores rule 3. Its first `would≠-` row can then come earlier than ON's first real act, so D-OBS fails for an instrument reason.
EVIDENCE: `_worst_hit` and `_hp_seen` are updated only inside `_maybe_use_item` (story_mode.py:838-841), and observe must not call it (the adversary's F10). Rule 3 refuses any heal whose best possible amount is below the worst hit taken (battle_items.py:92-95). The gate row pins 'no state change', and for the unset row 'the instance __dict__ equal before and after'. On d13_tateliza the only HP item is Potion x1, which heals 20 (FIXTURES.md5:96), so rule 3 vetoes it after any hit of 20 or more. That is exactly where OBS (worst=0) and ON (a real ledger) diverge.
FIX: Either let observe keep a PRIVATE per-PID HP ledger (in a separate object, excluded from the __dict__ row, and declared as the one permitted state), or drop the `first would≠- = S0-5` criterion. Also state that S0-5's offline computation uses D3's per-PID worst-hit definition.
VERDICT: refuted=False corrected=should-fix
REASONING: The finding holds, and nothing in the design deals with it.

1. **`worst` is carried from one decision to the next.** The biggest hit so far is updated only inside `_maybe_use_item`, before the policy runs (story_mode.py:838-841). The previous HP it compares against is kept in `_hp_seen`, which is state that persists.

2. **Observe is barred from keeping any state.** The design says so three times: §2 D5 "with NO state change", §7 "observe → super() result, no state change", and the adversary's F10 fix "call only the pure functions on copies". The ourcode recon's W3 had already warned that "what the singles policy would choose cannot be computed without side effects (`_hp_seen`, `_worst_hit`…)". The design never answers W3.
   - Under observe, `decide_turn` never runs in a double, so `self._worst_hit` stays at its `__init__` value of 0 (story_mode.py:770).
   - C5 still logs a `worst=<n>` column, but the design never says where the number comes from.

3. **Rule 3 is only a veto.** It returns None when `worst_hit_taken and best_possible < worst_hit_taken` (battle_items.py:92-95), and a worst of 0 switches it off. Rule 2's choice of item does not depend on worst. So observe's `would` fires at every decision where ON would act, and at extra ones too. Its first `would≠-` row therefore comes no later than ON's first act. It comes strictly earlier whenever rule 3 vetoes a decision below 35% HP first.

4. **On this fixture the veto is very likely.** The pinned `d13_tateliza.ss1` carries Potion x1, which heals 20, plus Full Heal x1 (FIXTURES.md5:96).
   - A battler only reaches 35% HP or less after losing at least 65% of its max HP. Against Tate & Liza's level 41-42 team (d13_recon_fixture.md), that almost always includes one turn's drop of more than 20.
   - At that decision ON's ledger vetoes the Potion, while observe reports `would=Potion`.
   - The design leaves the `--set-bag-item` item open (S0-2, S0-5 "both levers"). A Super Potion (50) still leaves the gap. Only a Hyper Potion (a flat 200) or better closes it, and nothing in the design requires one.

5. **D-OBS and D-ON share one pre-registered point.** D-OBS says "first `would≠-` row = S0-5's discriminator". D-ON says "= D-OFF up to S0-5's frame. There, the named side uses the named item". S0-5 is computed "offline, with the pure policy" without saying whether the ledger is included.
   - If S0-5 includes the ledger (faithful to `_maybe_use_item`), D-OBS fails for a reason in the instrument.
   - If S0-5 uses worst=0, D-ON fails instead: ON's real ledger vetoes the act at S0-5's frame.
   - Either way, one arm can fail for a reason in the instrument whenever rule 3 fires before ON's first act.

**Severity.** This is not a blocker. It does not put an item on the wrong Pokémon, change behaviour with the flag unset, or make an arm unable to fail. The effect is a false arm failure, contained to the grading. That can be misread as a real defect, which is the CLAUDE.md rule-4 trap. It stays should-fix.

**Fix.** The finding's fix is sound. Do both parts:
- Either let observe keep a private per-PID HP ledger and declare it as the one permitted state (excluded from the `__dict__` row), or restrict D-OBS's criterion to "would≠- first fires at or before S0-5".
- Say explicitly that S0-5 uses D3's per-PID worst-hit ledger.
- Alternatively, pin a bag item whose heal is at least the largest max HP, so rule 3 cannot fire.
REFUTER EVIDENCE: The policy reads the ledger; observe has none.
- story_mode.py:838-841 (worktree f7ae9878): `previous = self._hp_seen.get(mon.party_index)` / `if previous is not None and previous > mon.current_hp: self._worst_hit = max(self._worst_hit, previous - mon.current_hp)` / `self._hp_seen[mon.party_index] = mon.current_hp`. This runs only inside `_maybe_use_item`.
- story_mode.py:770: `self._worst_hit = 0` in `__init__`.
- story_mode.py:1098-1105: `choose_healing_item(..., worst_hit_taken=self._worst_hit, ...)`.
- battle_items.py:92-95: `best_possible = max(effective_heal(...))` / `if worst_hit_taken and best_possible < worst_hit_taken: return None`. This is a veto only.
- battle_items.py:73-74: "0 disables that rule".

The design forbids observe any state.
- DESIGN §2 D5:100: "`observe`: `super()` plus one `[DBLITEM-OBS]` line per decision (§3), with NO state change."
- DESIGN §7:210: "`observe` → `super()` result, no state change, exactly one OBS line".
- DESIGN §3 C5:146 logs `would=<item|-> ... worst=<n>` without saying where worst comes from.
- DESIGN D3:85-86: the ledger swap exists only for mode `1` (C2:138).

The recons flagged it and the design did not answer.
- d13_recon_ourcode.md:200 (W3): "'What the singles policy would choose' cannot be computed without side effects ... `_hp_seen`, `_worst_hit`".
- d13_recon_adversary.md F10: "Call only the pure `choose_healing_item` ... on copies".

The arms are coupled to one prediction.
- DESIGN §6:196 D-OBS: "Its first `would≠-` row = S0-5's discriminator."
- DESIGN §6:197 D-ON: "= D-OFF up to S0-5's frame. There, the named side uses the named item".
- DESIGN §5 S0-5:185-186: "compute offline, with the pure policy, the FIRST decision where `_maybe_use_item(side)` would choose an item". It does not say whether the worst-hit ledger is used.

The fixture's bag.
- tools/story-dev/saves/FIXTURES.md5:96, d13_tateliza.ss1: "Items pocket: Nugget x2, X Attack x2, Potion x1, Full Heal x1".
- Potion heals 20 (battle_items.py:14-15).
- Foes: Claydol 41, Xatu 41, Lunatone 42, Solrock 42 (d13_recon_fixture.md:43).
- DESIGN §4:167 and S0-2:176-177 leave the `--set-bag-item` item unspecified.

## proof:F6 [should-fix] DESIGN §4 levers ('--set-bag-item … keeps every other stack'; HEAL_AT_FRACTION as the only fallback); §5 S0-5; §2 D4 ('the existing retry-once / disable bounds the rest'); §6 D-ON/D-NOG predictions
CLAIM: Every arm's prediction assumes an HP item. On the pinned fixture an HP act is blocked by rule 3, which HEAL_AT_FRACTION cannot lift. A status act (Full Heal) is possible, and for a cure D-ON's 'HP rises' is false by construction. D4's bound also does not hold for cures.
EVIDENCE: FIXTURES.md5:96: Items pocket Nugget x2, X Attack x2, Potion x1, Full Heal x1. Rule 3 does not depend on the fraction (battle_items.py:80 vs :92-95). The status branch runs when the HP policy declines (story_mode.py:1126-1132) and Lunatone knows Hypnosis (trainer_parties.h:3566). The status verdict only logs and never sets `_index_space_flipped` or `_items_ineffective` (story_mode.py:863-885), unlike the HP path (:976-988). A guard refusal on a cure is therefore bounded only by MAX_ITEM_USES_PER_BATTLE = 4 (battle_items.py:49; `_item_uses += 1` per request at story_mode.py:1146), which also burns the battle's HP-heal budget. A Full Heal on a partner with no status is refused, the F1 shape again.
FIX: In S0-5, predict the item KIND, not only 'an item'. Set a large enough HP item with --set-bag-item (for example Hyper Potion, above the measured worst two-foe turn), and zero the Full Heal (the lever must allow two stacks or N=0). Otherwise pre-register kind-specific predictions: cure → status clears, and bound = 4 uses. Correct D4's bound statement for cures.
VERDICT: refuted=False corrected=should-fix
REASONING: The core of F6 holds up. On the fixture, every arm criterion and D4's bound statement assume an HP item. The design never mentions the status-cure branch. A grep of the design for "Full Heal|cure|sleep|Hypnosis|status" finds only the ledger field name at :78. Yet its own decomp recon says "a status-cure decision is reachable" on this fight.

Two parts of the finding are overstated, and they lower its force but do not refute it:

(1) "An HP act is blocked by rule 3, which HEAL_AT_FRACTION cannot lift" is too absolute. Rule 3 is indeed independent of the fraction. But rule 3 is skipped when worst_hit_taken is 0 (battle_items.py:94 `if worst_hit_taken and ...`). So the design's own `--set-party-hp SLOT=<low, non-zero>` would make the Potion fire at a Pokémon's first decision. A raised fraction can also fire after a first drop of 20 or less. In practice, though, a two-foe turn from L41-42 Psychic/EQ/Ancient Power users is well above the Potion's 20 HP. Also, S0-5 says "both levers", so `--set-bag-item` is already applied in Step 0, but the design never names the item. S0-5's only stated fallback when nothing fires is the fraction (:186-187). S0-2 (:176-177) reads as though `--set-bag-item` is needed only when there is no healing item, and the fixture has a Potion.

(2) The D4 bound error is real but mild. The cure verdict only logs, so a refused Full Heal is re-requested until `_item_uses` reaches 4. Each refusal unwinds back to the same battler's action menu in the same turn (the executor's B-loop, then the handler re-decides). So no turn is lost and nothing hangs. The HP path ends in the same place after 2 refusals, with `_items_ineffective`, so "burns the HP-heal budget" is not worse than today's behaviour.

S0-5 already names the item in the discriminator (:185-186: "its frame, side, item, target PID"), so part of the proposed fix already exists. Step 0 would therefore show a cure before predictions are filed.

What the design does NOT handle:
- The fixed "What it must show" criteria in D-ON ("that PID's HP rises") and D-NOG ("the wrong PID's HP rises and the bag drops") are false for a first act that is a cure.
- D-NOG with a Full Heal aimed at an unstatused partner can never pass, because the game refuses it without consuming it.
- The lever keeps the Full Heal in the bag (:167).

Why the severity stays should-fix, not blocker:
- Nothing reaches the wrong Pokémon.
- Nothing hangs.
- Nothing changes with the flag OFF.
- No arm becomes unable to fail: a cure first act makes D-ON and D-NOG fail loudly.

It is still a real defect with a bounded cost: a wasted Step-0 iteration, or a misleading failed fault arm. The fix is the proposed one: pin a large HP item (for example Hyper Potion) and zero the Full Heal, or pre-register criteria per item kind, and correct D4's bound text for cures (max 4 uses, same turn).
REFUTER EVIDENCE: Fixture bag, verified: tools/story-dev/saves/FIXTURES.md5:96, d13_tateliza.ss1, "Items pocket: Nugget x2, X Attack x2, Potion x1, Full Heal x1".

Rule 3 does not depend on the fraction: sandbox-pokebot/modules/story/battle_items.py:81 (fraction test) versus :92-95. But :94 `if worst_hit_taken and best_possible < worst_hit_taken` skips rule 3 when worst_hit is 0, which is why the finding's "cannot lift" is overstated. Potion = 20 HP (docstring :15).

Status branch:
- It runs only after the HP policy declines: sandbox-pokebot/plugins/custom_modes/story_mode.py:1106-1132.
- Sleep → Full Heal when no Awakening is held: battle_items.py:250-258.
- A parameter==0 item goes to `_status_when_item_requested`, and no bag count is banked: story_mode.py:1151-1164.

Lunatone knows Hypnosis: decomp trainer_parties.h:3566 (sParty_TateAndLiza1, Lunatone L42 {LIGHT_SCREEN, PSYCHIC, HYPNOSIS, CALM_MIND}).

The design's own recon flagged cures: d13_recon_decomp.md:98, "Hypnosis puts a mon to sleep, which is in our cure set, so a status-cure decision is reachable".

The cure verdict only logs and never sets `_index_space_flipped` or `_items_ineffective`: story_mode.py:863-885. The HP path, by contrast, flips and then disables at :976-988.

The bound for cures is the use cap: `_item_uses += 1` at story_mode.py:1146; `if uses_so_far >= max_uses: return None` at battle_items.py:224-225; MAX_ITEM_USES_PER_BATTLE = 4 at :49.

A refusal unwinds to the same battler in the same turn: battle_action_selection.py:1136-1139 (B until BATTLEMAINCB2), then the handler re-decides at :198-212.

A Full Heal on an unstatused mon is refused and not consumed: decomp party_menu.c:4416-4424. The cannotUse branch shows WontHaveEffect, and RemoveBagItem (:4433) runs only in the success branch. So D-NOG cannot pass on a cure.

Design text:
- D-ON and D-NOG criteria are HP-only (DESIGN :197, :200).
- D4's bound says "the existing retry-once / disable bounds the rest" (:92-93).
- The lever "sets one Items-pocket stack and keeps every other stack" (:167).
- S0-5 already names "item" in the discriminator, uses "both levers", and names HEAL_AT_FRACTION as the only fallback (:184-187).
- S0-2 makes `--set-bag-item` conditional on "no healing item" (:176-177).
- A grep of the design for Full Heal, cure, sleep, Hypnosis and status finds none outside the ledger field list at :78.

## proof:F7 [should-fix] DESIGN §2 D8 'OBSERVE IS THE RULE-10 MEASUREMENT'; §6 D-OBS 'agree=1 on every row'; §1 G2 / §7 pure row 'the invariant order for every (left, right) pair'
CLAIM: `agree` is forced to 1 whenever the S0-4 offset is right, so it re-checks S0-4 and nothing else. It never observes the conversion production acts on. In addition, the 'invariant' ([left, right, rest ascending]) is the order only at battle start: after any switch the bench is swapped, not re-sorted.
EVIDENCE: At battle start the order is built from gBattlerPartyIndexes (battle_controllers.c:97-103; party_menu.c:5969-5985). SwitchPartyOrder swaps two positions and writes the same array to BOTH player battlers (battle_main.c:4086-4106). So the active target always sits at position 0 or 1 in both arrays, and M_bpo equals M_truth by construction. Both are computed by new C6 code from raw bytes. The conversion production acts on is `get_battle_state().map_battle_party_index(target_index)` after the bag opens (bas:1106-1121), which observe never runs. Example: [1,2,0,3,4,5] with P1 replaced by P4 becomes [4,2,0,3,1,5], while the invariant gives [4,2,0,1,3,5].
FIX: Reword the headline. The rule-10 ground truth for the conversion production acts on is D-ON's menu line (menu_pid vs intended_pid), which the guard backs. D-OBS's `agree` is an offset self-check. Restrict `invariant_order` and M_truth to the two active positions (or rename the `truth=` column) so a later partner-heal, bench or Revive extension cannot reuse it for the bench.
VERDICT: refuted=False corrected=should-fix
REASONING: I could not refute the finding. Both halves hold against the decomp, our code and the design's own text.

(1) `agree` is an offset check, not a measurement of the conversion production uses. Under D2 (self-only) the target is always an active Pokémon. M_truth is its position in C6's `invariant_order`, so it is always 0 (left) or 1 (right).
- At battle start, battlerPartyOrders is built as [left, right, rest].
- Every later non-multi switch goes through SwitchPartyOrder. It swaps the outgoing Pokémon's position with the incoming one's, then writes the result to the battler AND its partner.
- So by induction the active Pokémon always sits at position 0 or 1 in both player arrays. M_bpo therefore equals M_truth whenever the offset and the nibble decode are right.
- If the offset is wrong, S0-4 already voids the bpo column. So the D-OBS clause "agree=1 on every row" cannot fail on its own.
- Both numbers come from new C6 code (`decode_bpo`/`menu_position` and `invariant_order`) over raw reads. Production's actual conversion, `get_battle_state().map_battle_party_index(target_index)` on the array refilled after the bag opens, never runs in `observe`.
- The only action-level ground truth is D-ON's `[DBLITEM] menu ... menu_pid= intended_pid= ok=` line, backed by the D4 guard and proven load-bearing by D-SLOT and D-NOG.
- So D8's headline "OBSERVE IS THE RULE-10 MEASUREMENT" claims more than it measures. CLAUDE.md rule 2 (the headline carries the caveat) and rule 7 (instrument the action, not its input) both apply.

(2) The invariant is only guaranteed at battle start. After a switch the bench is swapped, not re-sorted. The design states G2 ("[left active, right active, then the rest ascending]") in its AUTHOR-VERIFIED section without that caveat. The recon notes were more careful: d13_recon_decomp.md:59 says "set up ... at battle start", and d13_recon_ourcode.md:121 marks the whole-battle claim as INFERRED.
- The finding's example checks out. [1,2,0,3,4,5] with P1 replaced by P4 becomes [4,2,0,3,1,5], while the invariant gives [4,2,0,1,3,5].
- This is easy to reach in Tate & Liza, where faint replacements are common. The bot's faint chooser picks the replacement, so it is often not the lowest bench index (sending P3 from [0,1,2,3,4,5] gives [3,1,2,0,4,5]).
- The design never defines `agree` precisely. C5 prints `truth=<6 digits>` beside `bpo=<3 bytes>`, and S0-4's self-check compares the full array. So an implementer who applies the full-array comparison per row would see spurious mismatches, or void bpo, after the first such replacement.

Why this is should-fix, not a blocker:
- No item reaches the wrong Pokémon, because the D4 guard checks identity at the menu.
- D-OBS can still fail on its other criteria (the OFF-equality, the line count, disc=1, and the S0-5 discriminator).
- The design never uses the bench positions in this step.

The effect is bounded: a mislabelled instrument, one near-tautological clause, and a "verified" G2 that a later bench or Revive extension could build on wrongly. The proposed fix fits the problem:
- Reword D8 so D-ON's menu line is the rule-10 ground truth.
- Call `agree` an offset self-check.
- Limit `invariant_order`/M_truth (or the `truth=` column) to the two active positions, and add "at battle start" to G2.
REFUTER EVIDENCE: Decomp (pret/pokeemerald copies in the session scratchpad `decomp/`; src_party_menu.c is diff-identical to party_menu.c):
- battle_controllers.c:97-103: SetBattlePartyIds(), then for non-multi `BufferBattlePartyCurrentOrderBySide(i, 0)` for every battler. This is the only place the order is built fresh; grep finds no mid-battle re-buffer for non-link battles.
- party_menu.c:5969-5985 (BufferBattlePartyOrderBySide, double branch): partyIndexes[0]=left, [1]=right, then i ascending, skipping those two.
- battle_main.c:4086-4106 (SwitchPartyOrder): loads battlerPartyOrders[battler] into gBattlePartyCurrentOrder, then `SwitchPartyMonSlots(GetPartyIdFromBattlePartyId(gBattlerPartyIndexes[battler]), GetPartyIdFromBattlePartyId(monToSwitchIntoId[battler]))`, a two-position swap (party_menu.c:6051-6056). If BATTLE_TYPE_DOUBLE, it writes the result to both `battler` and `BATTLE_PARTNER(battler)` (:4101-4105).
- Callers: battle_script_commands.c:5178 and :5207 (switchhandleorder), and :7364 (forced switch). battle_main.c:4577-4583 and bsc:5193-5199 rewrite the order only for LINK+MULTI.
- battle_main.c:4236 and battle_controller_player.c:2653-2663: the bag-open refill copies battlerPartyOrders[gActiveBattler] into gBattlePartyCurrentOrder, which UpdatePartyToBattleOrder (party_menu.c:6078-6086) then applies to gPlayerParty.

Our code:
- sandbox-pokebot/modules/battle_action_selection.py:1106-1121: the executor's remap is `_fresh = get_battle_state().map_battle_party_index(target_index)` (:1115), run after the wait for PARTY_MENU (:1108).
- modules/battle_state.py:332-354: map_battle_party_index decodes gBattlePartyCurrentOrder (read at :816).

Design:
- DESIGN.md:56-58 (G2 claims "the rest ascending" with no battle-start caveat).
- :119-127 (D8: M_bpo and M_truth are both target positions, and the headline calls this "THE RULE-10 MEASUREMENT").
- :147 (C5 prints `truth=<6 digits>` and `bpo=<3 bytes>`; `agree` is not defined).
- :154 (both come from C6).
- :180-183 (S0-4 already checks the full decode against the invariant at the first decision, and voids bpo if it fails).
- :196 (D-OBS "agree=1 on every row").
- :149 and :197 (the D-ON menu line `menu_pid= intended_pid= ok=` is the real check at the moment of the action).

Recon:
- d13_recon_decomp.md:59-60 ("set up ... at battle start"; the actives staying at slots 0/1 is INFERRED).
- d13_recon_ourcode.md:121 (the whole-battle invariant is INFERRED).

Worked example: [1,2,0,3,4,5], P1 replaced by P4, gives [4,2,0,3,1,5], while invariant_order(4,2) gives [4,2,0,1,3,5]. The active positions agree and the bench differs.

## proof:F8 [should-fix] DESIGN §7 production rows and 'Faults and mutants … each reddening exactly its own rows'
CLAIM: As listed, the gate has no row that WRONGSLOT can turn red, and no row that separates a guard reading the cursor's actual slot (slotId) from one reading the intended slot (_menu_slot).
EVIDENCE: The only executor rows are 'the executor passes the battler' and 'the guard refuses a PID mismatch (fake emulator: no A press)'. A mismatch row still refuses under WRONGSLOT, and no positive row exists ('a PID match presses A on the requester's menu slot'). So WRONGSLOT turns zero rows red, and 'exactly its own rows' is unmet. `scroll_to_party_menu_index` can return early without reaching the target through KI-38's request_mode_recovery (menuing.py:197-207), after which the executor still presses A (bas:1133-1135). A mutant guard that compares gPlayerParty[_menu_slot] instead of gPlayerParty[slotId] passes every listed row.
FIX: Add two executor rows. (1) A positive control: matching PIDs → the cursor is driven to the requester's slot and A is pressed; WRONGSLOT turns this row red. (2) A fake whose party-menu scroll stops short: the guard must refuse, because it reads slotId (byte 9), not the intended slot.
VERDICT: refuted=False corrected=should-fix
REASONING: The finding survives. I read §7 of the design (lines 203-219). It has two executor-level production rows: "the executor passes the battler" (:215) and "the guard refuses a PID mismatch (fake emulator: no A press)" (:216).

**WRONGSLOT reddens nothing.** It drives the cursor to the partner's slot, so the mismatch row still refuses and stays green. "The executor passes the battler" does not involve the cursor target. The row "side 0 heals the left Pokémon, side 1 the right; never the partner" (:211) is listed with the strategy rows, beside the pending-verdict, Multi and KEYITEMS rows. Nothing in the design says it runs through the executor's cursor path, so WRONGSLOT (C7, :158) cannot touch it. The design's own claim at :219, "every C7 fault ... each reddening exactly its own rows", is therefore unmet for WRONGSLOT.

**No positive control.** No row asserts that matching PIDs lead to an A press. An executor wired to always refuse passes every listed production row. Only the one-off live D-ON arm would catch it, and a live arm is not the registered regression gate.

**The slotId vs _menu_slot mutant is real and reachable.**
- D4 (:90-91) correctly specifies reading gPartyMenu.slotId (byte 9) and gPlayerParty[slotId]. The decomp confirms this layout (include/party_menu.h, struct PartyMenu), and ItemUseCB_Medicine acts on gPlayerParty[gPartyMenu.slotId] (party_menu.c:4398).
- In our code, scroll_to_party_menu_index can return before reaching the target. When the KI-38 bound is hit and request_mode_recovery accepts, it returns (menuing.py:197-207; battle_fault.py:33-44). The executor then presses A anyway (battle_action_selection.py:1133-1135).
- In that case slotId differs from _menu_slot. A guard reading gPlayerParty[_menu_slot] would compare a PID that the KI-101 remap made equal to the intended one by construction. It would accept, and A would land on whatever Pokémon the cursor stopped on, possibly the living partner. That breaks D4's headline invariant (:94, "the bag count dropped implies the intended Pokémon took the item").
- The mutant is not hypothetical. The adversary recon proposes exactly that read as ground truth (d13_recon_adversary.md:152: "the PID at gPlayerParty[_menu_slot]").

**The live arms do not pin it.** D-SLOT and D-NOG (:199-200) probably do not tell the two reads apart either. If WRONGSLOT is implemented by changing _menu_slot, both guards read the partner and both refuse.

**Partial mitigation, and why it is only a should-fix.** §7 already commits to "an adversarial mutant pass" before registration (:203), which might surface these gaps at build time. The design as written still lists the rows and asserts they are complete. Step 12's history (its adversarial pass found that the gate missed 102 of 139 mutants) shows these gaps are real when left to build time. The effect is bounded: it weakens the gate, the design's specified behaviour is correct, and it makes no live arm unable to fail. So it is a should-fix, not a blocker.
REFUTER EVIDENCE: Design, C:/Remote Projects/pokebot-wt-ch24/PROJECT KNOWLEDGE/ai-research-notes/2026-09-30-doubleitems13-DESIGN.md:
- :215-216 are the only executor rows: "the executor passes the battler"; "the guard refuses a PID mismatch (fake emulator: no A press)".
- :211 "side 0 heals the left Pokémon, side 1 the right" is grouped with the strategy rows.
- :158 WRONGSLOT "drives the cursor to the PARTNER's menu slot".
- :219 "each reddening exactly its own rows".
- :90-91 the guard reads gPartyMenu.slotId (byte 9) and gPlayerParty[slotId].
- :94 "the bag count dropped implies the intended Pokémon took the item".

Our code, sandbox-pokebot/modules:
- menuing.py:197-207: after _MAX_CURSOR_PRESSES=40, `if request_mode_recovery(reason): return`. The scroll returns without reaching the target.
- battle_fault.py:33-44: request_mode_recovery returns True whenever the mode handles battle faults.
- battle_action_selection.py:1133-1135: `yield from scroll_to_party_menu_index(_menu_slot)` / `context.emulator.press_button("A")` / `yield`. A is pressed even after the early return.
- menuing.py:229-236: get_current_party_menu_index reads gPartyMenu[9].

Decomp (pret/pokeemerald):
- include/party_menu.h, struct PartyMenu: exitCallback (4 bytes), task (4 bytes), then menuType:4 and layout:2 in byte 8, so slotId is byte 9.
- src/party_menu.c:4398 `struct Pokemon *mon = &gPlayerParty[gPartyMenu.slotId];` The item acts on the actual cursor slot, not the intended one.

Recon: d13_recon_adversary.md:152 proposes "the PID at gPlayerParty[_menu_slot]" as ground truth, which is the exact mutant the finding describes.

## proof:F9 [nit] DESIGN §7 'The singles gates stay green unchanged'; §6 table Flags column
CLAIM: The gate list omits two existing gates that constrain what C2/C4/C5 may add. The arms table does not say which levers and which POKEBOT_R27_KEYITEMS value each arm runs with. That matters for observe: with KEYITEMS=1, observe either calls _r27_key_gate (which changes state and adds a [KEYBATTLE] line) or ignores it.
EVIDENCE: probe_dmgaudit.py:1831,1881 (NH-gbs-count) pin exactly 5 get_battle_state() calls in BAS: bas:116, 578, 806, 845, 1115. C4/C5 must add none, which is consistent with C5's rule, and this gate enforces it. repro_no_silent_except.py:293-299 sets per-root budgets (battle_action_selection.py 3, plugins/custom_modes 79): every new `except` needs a log or a `# noqa: BLE001` justification. _r27_key_gate caches `_r27_verdict` and logs KEYBATTLE (story_mode.py:6371, 6394, 6399). The gates I checked stay green under C1/C3/C4 as specified: A1 pins only statement order and a single `import os as _os` (repro_key_battle_items.py:243-260); repro_ki90's stub is `_empty_gen(*_a, **_k)` (repro_ki90_absent_left_slot.py:120-126); repro_ki45 calls `_select_in_menu` directly (repro_ki45_cursor_bound.py:77).
FIX: Name probe_dmgaudit NH-gbs-count and repro_no_silent_except in §7. In §6, add a column listing each arm's levers (`--set-party-hp 0=0`, `--set-bag-item …`) and its KEYITEMS value (unset in every D-arm unless observe's handling of the key gate is specified).

### checked and found true
- Lever (1): party HP is a u16 at struct Pokemon +0x56, after the 80-byte encrypted box, status (0x50), level and mail (include/pokemon.h:219-232; our current_hp is data[86:88] per the Ki66 docstring, story_harness.py:3930-3934). A 2-byte write is faithful and breaks no checksum.
- SetBattlePartyIds gives battler 0 the first party slot with HP > 0, and battler 2 the next such slot that is not battler 0's (battle_controllers.c:585-630). With P0 at 0 HP and P1, P2 alive, the game sends P1 and P2, and the battle-start order is [1,2,0,3,4,5] (party_menu.c:5969-5985 via InitBattleControllers, battle_controllers.c:97-103). FIXTURES.md5:96 (uncommitted) records all six at full HP, so the precondition holds on d13_tateliza.
- The two-usable-Pokémon checks pass with 5 alive: GetMonsStateToDoubles (pokemon.c:4507-4525; trainer_battle.inc:28-29; Tate & Liza use trainerbattle_double, MossdeepCity_Gym scripts.inc:52) and fight_the_leaders' own gate (mossdeep_gym.py:391-399).
- Nothing heals before the fight and undoes the lever: fight_the_leaders and do_mossdeep_gym_chapter contain no heal (mossdeep_gym.py:363-441, 519-616), and production skips _prepare_for_fight, _lead_best_matchup and the heal when already on the gym map (story_mode.py:5817-5845).
- --set-bag-item can be built like --set-balls: debug_write_item_bag with every other pocket kept, a read-back from the save block at 0x560, and an asserted equality (story_harness.py:28991-29035). The ki66 2-byte HP write is the precedent for --set-party-hp.
- Drivers from the fixture: mossdeepbadge fights Tate & Liza with StoryItemBattleStrategy() built directly (story_harness.py:3401-3409), and storyresume runs production StoryMode, which returns StoryItemBattleStrategy for trainer battles (story_mode.py:4357). mossdeepgym cannot fight them: it stops at the leader tiles, re-captures at_mossdeep_leaders.ss1 unless CH18B_CAPTURE=0, and goes Manual (story_harness.py:3352-3374). Neither fighting driver except storyresume opts into handles_battle_faults, so a KI-45 under mossdeepbadge raises BotModeError and drops to Manual.
- BattleStruct.battlerPartyOrders is at offset 0x60 (battler 2's array at 0x66) by the layout in include/battle.h:354-381, and expGetterMonId is at 0x10. This confirms that read_symbol('gBattleStruct', 16, 1) reads past the pointer.
- D-OBS's equality with OFF is not perturbed by logging: debug_logger.event and raw read_symbol reads consume no frames, and observe (per C5) calls no get_battle_state(). It is an inertness check that can fail only on a code difference.
- The in-battle item menu reorders gPlayerParty into menu order and opens with the cursor on slot 0 (party_menu.c:5781-5786, 524-525). So D4's 'read gPlayerParty[slotId] while the menu is open' is the correct identity readback.
- D-CUR binds deterministically as KI-45 at the first act, in either order, provided battler 2 is asked in that turn (battle_controller_player.c:266-285; battle_menuing.py:27, 38-55).
- The singles gates stay green under C1/C3/C4 as specified: the A1 AST pin (repro_key_battle_items.py:243-260), the ki90 stub (repro_ki90_absent_left_slot.py:120-126) and repro_ki45 (direct _select_in_menu) do not pin anything C1/C3/C4 change, and the FakeBattleState with only left_battler still works with side=0 as the default.

