# TM/HM teach chain — every prompt, every exit, every task symbol (2026-09-05)

> ⚠ **THIS IS A RESEARCH NOTE, NOT TRUTH.** See `00-READ-THIS-FIRST.md`. It was produced by a Claude
> subagent reading `pret/pokeemerald@master` with `gh api`. Where it CONTRADICTS an authoritative
> doc, the authoritative doc wins until the claim is verified in our own harness.
>
> ⭐ **THE HALF THAT WAS VERIFIED LIVE, AND HOW.** This note's exit-path table (§3) predicted the
> message `"{STR_VAR_1} already knows {STR_VAR_2}."` for the "already knows the move" exit. Our
> `--driver ch24teachice` message trace read, on the same day, from the real ROM:
> `[TEACH-SAID] 0: 'DIVER already knows DIVE.'` ⇒ **exit path E, confirmed independently.**
>
> ⛔ **AND THE HALF THAT WAS WRONG, WHICH IS WHY THE RULE EXISTS.** The agent's own ranking put that
> answer FOURTH and named a bag-side B-press as "most likely (#1)". Its ENUMERATION was gold; its
> RANKING was wrong. ⇒ ⭐ **Use an agent to enumerate WHAT TO LOOK FOR, never to decide what happened
> — the identical rule the 2026-07-25 measurement produced for Gemini.**

## 1. The chain, USE → move-forget screen

```
item_menu.c:  Task_ItemContext_MultipleRows        (TM/HM context grid; cursor starts at ACTION_USE)
              ItemMenu_UseOutOfBattle -> GetItemFieldFunc(item)
item_use.c:   ItemUseOutOfBattle_TMHM              "Booted up a TM." / "Booted up an HM."
              BootUpSoundTMHM
              Task_ShowTMHMContainedMessage        ⚠ accepts A **or B**
              UseTMHMYesNo                         "Teach {MOVE} to a POKéMON?"  YES/NO
              UseTMHM -> SetUpItemUseCallback      gItemUseCB = ItemUseCB_TMHM
party_menu.c: CB2_ShowPartyMenuForItemUse          PARTY_MSG_TEACH_WHICH_MON, keepCursorPos = TRUE
              Task_HandleChooseMonInput -> HandleChooseMonSelection -> gItemUseCB(...)
              ItemUseCB_TMHM
                 -> Task_LearnedMove               (free slot; THIS is where the TM is consumed)
                 -> Task_ReplaceMoveYesNo -> Task_HandleReplaceMoveYesNoInput
                       YES -> Task_ShowSummaryScreenToForgetMove
pss.c:                      Task_HandleReplaceMoveInput / Task_HandleInputCantForgetHMsMoves
```

## 2. ⛔ THREE HAZARDS FOR A BOT THAT PRESSES BUTTONS ON A TIMER

1. **`B` IS DESTRUCTIVE AT EVERY YES/NO IN THIS CHAIN.** `Task_CallYesOrNoCallback` and
   `Task_HandleReplaceMoveYesNoInput` both fold `MENU_B_PRESSED` into the **NO** branch. And
   `Task_ShowTMHMContainedMessage` accepts `A_BUTTON | B_BUTTON`, so a bot that advances text with B
   sails through "Booted up a TM." and then answers **NO** to the teach.
   ⇒ **Never use B to advance text inside a teach.** Ours presses only A.
2. ‼ **"Stop trying to teach {MOVE}?" DEFAULTS TO YES, AND YES MEANS ABORT.**
   (`Task_HandleStopLearningMoveYesNoInput` case 0 → `gText_MoveNotLearned` → close.) An A-mash that
   reaches this prompt **cancels the teach it is trying to complete**. ⭐ This is the one prompt in
   Gen 3 where the safe default is inverted, and it is exactly the shape of `KI-88`.
   ⇒ A-mashing is only safe while the screen you want has NOT yet appeared. Ours gates on that.
3. **`keepCursorPos = TRUE`** — the party cursor starts wherever the LAST party menu left it, not at
   slot 0 (`InitPartyMenu` resets it only when the slot is invalid). "Press Down N times" is unsound;
   A on `PARTY_SIZE + 1` is CANCEL and exits to the bag silently.
   ⇒ Ours is closed-loop on the cursor and requires a STABLE read, so this cannot bite it.

## 3. Every exit that returns to the bag WITHOUT teaching and WITHOUT consuming the TM

The TM is removed in exactly one place — `party_menu.c:Task_LearnedMove` (`RemoveBagItem(item, 1)`,
and only for `item < ITEM_HM01`). Anything that does not reach it leaves the TM in the bag.

| | trigger | message |
|---|---|---|
| A | party is empty | `gText_NoPokemon` |
| B | **NO or B at "Teach {MOVE} to a POKéMON?"** | **none — silent** |
| C | **B in the party menu, or A on CANCEL** | **none — silent** |
| D | species can't learn it | `gText_PkmnCantLearnMove` — *"…are not compatible."* |
| E | **already knows the move** | `gText_PkmnAlreadyKnows` — ⭐ **OBSERVED LIVE: "DIVER already knows DIVE."** |
| F | declined the replace prompt, then YES to "Stop trying to teach" | `gText_MoveNotLearned` |
| G | backed out of the move-forget summary screen | `gText_MoveNotLearned` |

⭐ **B and C are SILENT.** That is why "it bounced to the bag" is not a diagnosis on its own, and why
the message buffer had to be read: only D/E/F/G say anything at all.

**Ruled OUT, both of which had been on our candidate list:**
* **EGG** — `IsSelectedMonNotEgg` beeps and the party menu **stays open**; it does not exit.
* **FAINTED** — *there is no HP check anywhere in this chain.* A fainted Pokémon can be taught a TM.

## 4. Task symbols worth waiting on (instead of mashing)

| screen | task |
|---|---|
| item context grid | `Task_ItemContext_MultipleRows` |
| a bag message still printing | `Task_ContinueTaskAfterMessagePrints` |
| "Booted up a TM." | `Task_ShowTMHMContainedMessage` |
| **"Teach {MOVE} to a POKéMON?" box** | `Task_CallYesOrNoCallback` |
| party menu, choosing a mon | `Task_HandleChooseMonInput` |
| **"Should a move be deleted…?" box** | `Task_HandleReplaceMoveYesNoInput` |
| **"Stop trying to teach…?" box** | `Task_HandleStopLearningMoveYesNoInput` |
| move-forget summary screen | `Task_HandleReplaceMoveInput` |
| "HM moves can't be forgotten now." | `Task_HandleInputCantForgetHMsMoves` |

## 5. ⚠ What this note does NOT establish

* It was read from `master`, not a vanilla-era tag. Every symbol above is vanilla-era and we have
  live-confirmed exit **E** and the two `Task_Handle*Forget*` names, but the rest is UNVERIFIED here.
* The agent could not separate exits **B** and **C** — they produce a byte-identical end state. Only
  a live log of whether `Task_HandleChooseMonInput` ever became active tells them apart. Ours logs it.
* `\p` page-break press accounting was inferred from `strings.c`, not read out of `src/text.c`.

📌 **Related:** `05-KNOWN-ISSUES.md` KI-89 (upstream `scroll_to_item_in_bag` selects the wrong item),
`KI-88` (upstream `teach_hm_or_tm` A-mash), `03-PUNCH-LIST.md` `#24-icebeamteach`.
