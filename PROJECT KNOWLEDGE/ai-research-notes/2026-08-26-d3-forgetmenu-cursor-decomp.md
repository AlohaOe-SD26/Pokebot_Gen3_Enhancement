# NOTE — `#26-surfteachchain` D3: move-forget selector cursor on RE-entry (decomp recon)

> ⚠ **RESEARCH NOTE, NOT TRUTH** (see `00-READ-THIS-FIRST.md`). Produced 2026-08-26 by ONE
> Claude subagent reading pret/pokeemerald **master** via `gh api` (raw text, not base64).
> Verification gates before any code depends on this: the flow claims (3) want a LIVE probe
> of the re-entry path (fault-inject a B on the selector, watch the task chain); the
> dangling-pointer claim (4b) is explicitly UNVERIFIED. Line numbers are from the 2026-08-26
> fetch of master, which carries modernizations — they will drift.

## The question

`early_game.py:_select_forget_slot` scrolls BLINDLY: assumes the forget-menu cursor starts
at move slot 0 and presses Down `replace_slot` times. Probed TRUE on first entry. D3 asked:
does that assumption survive RE-entry (B on selector → "Stop trying to teach?" → NO → back)?

## Findings (each with the decomp site it rests on)

1. **Task chain (overworld teach):** `src/party_menu.c` `Task_ReplaceMoveYesNo` (L4815) →
   `Task_HandleReplaceMoveYesNoInput` (L4824) → `Task_ShowSummaryScreenToForgetMove` (L4841)
   → `CB2_ShowSummaryScreenToForgetMove` (L4850) →
   `ShowSelectMovePokemonSummaryScreen(..., CB2_ReturnToPartyMenuWhileLearningMove, ...)`
   (L4852). Cursor lives in `sMonSummaryScreen->firstMoveIndex`
   (`src/pokemon_summary_screen.c`, dpad handler `Task_HandleReplaceMoveInput` L2192).

2. **First-entry init:** `ShowPokemonSummaryScreen` L1102 —
   `sMonSummaryScreen = AllocZeroed(sizeof(*sMonSummaryScreen));` — the zeroed alloc IS the
   cursor init on the SELECT_MOVE path (the explicit `firstMoveIndex = 0` at L1887 belongs
   to the NORMAL-mode moves page, not this path).

3. **Re-entry after Stop-prompt → NO: the screen is DESTROYED and REBUILT, never kept
   live.** B on the selector sets `sMoveSlotToReplace = MAX_MON_MOVES` and
   `BeginCloseSummaryScreen`; `CloseSummaryScreen` → `FreeSummaryScreen()` (L1502) frees
   the struct holding the cursor. `Task_ReturnToPartyMenuWhileLearningMove` (L4860) sees
   `MAX_MON_MOVES` → `StopLearningMovePrompt` → NO branch (L4936-4944) →
   `gTasks[taskId].func = Task_ReplaceMoveYesNo` — i.e. ‼ **NO loops back to the
   "replace move?" YES/NO prompt FIRST**; only another YES re-opens the selector, through
   `AllocZeroed` again → cursor 0.

4. **Battle variant:** (a) same screen, same cursor state —
   `Cmd_yesnoboxlearnmove` case 2 (`src/battle_script_commands.c` L5447) calls the same
   `ShowSelectMovePokemonSummaryScreen`. Our `_get_move_selection_cursor`
   (`sandbox-pokebot/modules/battle_move_replacing.py:564`, offset +0x40C6) reads
   `firstMoveIndex` — the agent recomputed the struct layout and the offset is RIGHT for
   both variants **while the screen is open**. (b) ⚠ UNVERIFIED: `Free(sMonSummaryScreen)`
   does not NULL the pointer, so a read taken while the party-menu prompts are on screen
   (exactly the re-entry window) dereferences FREED memory — a plausible cause for the
   recorded "returns garbage here" observation. (`gMoveSelectionCursor` is the unrelated
   choose-a-move-to-USE cursor.)

## Verdict (the agent's, adopted as the working hypothesis — not yet verified live)

**Cursor RESETS to slot 0 on re-entry** (conjunction of the Free at L1502-1506 and the
re-entry re-running AllocZeroed at L1102; no code path writes a saved cursor back).
⇒ the blind relative scroll is NOT wrong about the cursor — **the real D3 hazard is the
FLOW: re-entry inserts an extra "replace move?" YES/NO before the selector**, so a bot
expecting the selector immediately after answering NO misfires even with a correct scroll.
⚠ Caveat carried from the agent: read from pret master, not a retail-tagged revision;
control flow matches the classic decomp but was not diffed against it.
