# §Ch24 LEG B — BUILD SPEC (Wallace → Hall of Fame → credits → reboot → controllable)

⛔⛔ **THIS IS A NOTE, NOT TRUTH** (`ai-research-notes/00-READ-THIS-FIRST.md`). It is the synthesis of a
**10-agent recon** (5 angles, each with an adversarial refuter): 133 claims, 41 refutations
(1 FATAL, 25 SERIOUS). Decomp citations pinned to pret/pokeemerald `5eff78649e7170a877b961ef0b3da13b81a16038`.
⛔ **Nothing here has been driven.** Every frame count is arithmetic (±30%) unless tagged **[M]**.
⭐ The companion file `2026-09-17-ch24-legB-VERIFIED-FACTS.md` holds the subset I re-checked BY HAND.

**Start fixture:** `post_hall4_door.ss1` (`1f15cc400218`) — `HALL4 (5,3)`, fully healed, 1 Revive.

---

## 1. THE SEQUENCE (⚠ = player is NOT on a map)

| # | what happens | frames | input | "done" signal |
|---|---|---|---|---|
| S0 | last controllable frame — ALL bag/heal/party work must already be done | — | — | `_on_map(HALL4)` ∧ `coords == (5,3)` |
| S1 | **IRREVERSIBLE** — one step north onto `(5,2)` → warp to `CHAMPIONS_ROOM (6,12)` | ~40–80 | **1× `Up`**, a deliberate single step | map becomes `(16,4)` |
| S2 | `ClearTempFieldEventData` zeroed `VAR_TEMP_1` ⇒ `OnFrame` matches on the **first controllable frame** (`field_control_avatar.c:150`, above `tookStep` at `:155`); first opcode `lockall` | 1 | none | ⛔ do NOT assert arrival at (6,12) |
| S3 | scripted approach `WalkUp4` + `delay 40` + `walk_up`×2 → player rests **(6,6)**, Wallace (6,5) | ~140–200 | ⛔ **none — issue NO movement, the player is locked** | coords `(6,6)`, script active |
| S4 | `msgbox Text_IntroSpeech` | press-bound | **14 A/B edges** (ceiling 20) | a battle starts |
| S5 | ⚠ the Wallace fight — 6 mons, IV 255, **4× Full Restore** | unbounded | BattleListener owns the stack; **the driver is starved** | `on_battle_ended(outcome)` on the mode instance — the only guaranteed latch |
| S6 | return-to-field; `_in_battle` clears on `len(get_map_objects())>0 ∧ standing_still` — **UNMEASURED for Wallace** | few hundred | none | generator resumes |
| S7 | post-battle cutscene (rival → Birch → dex rating → Wallace), ends `warp HALL_OF_FAME, 7, 16` (a **coordinate** warp) | long | **41–42 A/B edges** male / 39–40 female (ceiling 60) | map becomes `(16,11)` |
| S8 | ⭐ **HALL OF FAME *MAP* — AN ORDINARY OVERWORLD MAP.** Another `VAR_TEMP_1` `lockall` cutscene; 11 steps, 2 msgbox, field effect, then `SetGameClearFlags` → `setflag FLAG_IS_CHAMPION` → `ResetEliteFour` (clears all four E4 flags, zeroes `VAR_ELITE_4_STATE`) → `setrespawn` → fade | ≤700 | **7 A/B edges** (not 2). `_wait_until_cutscene_over` DOES work here | ⭐⭐ **BEST ACCEPTANCE WINDOW** — still `CB2_OVERWORLD`, everything readable |
| S9 | ⚠ `special GameClear` — `HealPlayerParty()` → `gHasHallOfFameRecords=FALSE` → `FlagSet(SYS_GAME_CLEAR)` → … → `SetMainCallback2(CB2_DoHallOfFameScreen)` **54 lines later** | 1 | none | symbol `CB2_DOHALLOFFAMESCREEN` |
| S10 | ⚠ **HoF SCREEN.** ~35 frames in: `TrySavingData(SAVE_HALL_OF_FAME)` → **FULL SAVE-SLOT WRITE**. Then parade/confetti/fade | ~1,850–2,050 | ⛔ **`JOY_NEW(A_BUTTON)` — A ONLY, an EDGE.** Not B, not START | symbol `CB2_STARTCREDITSSEQUENCE` |
| S11 | ⚠ **CREDITS — 57 pages** (MEASURED two ways; ⛔ **our punch list's "58" is WRONG**). Unskippable: B-hold gated on `gHasHallOfFameRecords`, FALSE on a first clear | ~8,940 | none possible | THE END chain |
| S12 | ⚠ THE END + copyright, then `tDelay = 7200` — **ended early by ANY key edge** | ~960 skipped / ~8,160 not | any edge (saves ~7,200) | reboot |
| S13 | ⚠ **REBOOT.** `RESET_ALL` wipes EWRAM+IWRAM; only ROM + flash survive. copyright → intro → title (Phase3 needs a **fresh** `JOY_NEW(A|START)`) → main menu (**cursor at CONTINUE**, because its EWRAM check byte was zeroed) → A → load | ~480–600 | **A edges only. ⛔ NO D-PAD** | symbol `CB2_OVERWORLD` |
| S14 | controllable in `LITTLEROOT…BRENDANS_HOUSE_2F (4,2)` (male) / `MAYS_HOUSE_2F` (female) — ⛔ derive from the saved `continueGameWarp`, never hardcode | 25 after CB2_OVERWORLD **[M]** | none | `player_avatar_is_controllable()` |

**Total ≈ 12,950 frames** (~3m37s) faithful with THE END skipped; ~20,150 without. **Budget `--frames ≥ 30000`.**

---

## 2. THE OBSERVE-ONLY PROBE — RUN THIS BEFORE ANY DRIVER

`--driver ch24tailprobe`, from `post_hall4_door.ss1`. **It is right about NOTHING in advance:** asserts
nothing, grades nothing, hardcodes no coordinate, no frame budget, no press count; every read wrapped
so a failure prints `<err …>` instead of raising.

**Only two side-effecting acts:** (1) one `Up` step onto `(5,2)`; (2) thereafter
`press_button("A")` every frame — the wrapper XOR-alternates, giving a `JOY_NEW` edge every 2 frames.
**A is the only button satisfying all three gate families** (`JOY_NEW(A|B)` text, HoF's A-only exit,
title Phase3's `A|START`). ⛔ **It stops pressing the instant `player_avatar_is_controllable()` is True
after the reboot** — A-mash is safe only under `lockall`; in the bedroom it would interact with furniture.

**⛔ MUST NOT:** navigate · `_pass_through_door` · `soft_reset()` · `_wait_until_cutscene_over` or any
ride helper · hold any button · press **SELECT** · press any **direction** after S1 · assert or grade.

**Prints** on every `get_game_state_symbol()` change and every 60 frames: frame · raw symbol ·
`GameState.name` · task symbols · `script_context.is_active` · `is_waiting_for_input()` ·
`player_avatar_is_controllable()` · map+coords · **controller-stack depth + top qualname** ·
`len(context.bot_listeners)` · A-presses issued · RAM `SYS_GAME_CLEAR`/`IS_CHAMPION`/4× `DEFEATED_ELITE_4_*`/
`VAR_ELITE_4_STATE` · and **flash** `get_save_data()` + its `SYS_GAME_CLEAR`. Plus a `TRANSITION` line
with the **frame delta since the previous transition** — *that delta table is the whole point.*

**Stops** on controllable ∧ OVERWORLD after reboot → summary → `context.set_manual_mode()`.
**Hard-aborts** on `GameState.NAMING_SCREEN` (the reboot went into NEW GAME).

**The questions it answers:** Q1 per-stage frame costs (*nothing in this tree has ever measured any of
them*) · Q2 does HoF+credits exceed the 20,000-frame detector · Q3 does `_in_battle` clear after Wallace
· Q4 the exact CB2 symbol order (`get_game_state()` is UNKNOWN for all of them) · Q5 does an
A-edge-every-2-frames cadence consume prompts 1:1 · Q6 does the in-game `SoftReset` move
`get_frame_count()` backwards **[M: it does NOT — 8490218→8491058; `emulator.reset()` → 0 does]** ·
⭐ Q7 **does flash written BY THE GAME survive the reboot** — *the single unmeasured load-bearing fact* ·
Q8 where the avatar actually rests at each stage · Q9 do the Rival/Birch objects un-hide onto (6,12).

---

## 3. THE REFUTATIONS THAT CHANGE THE BUILD

**FATAL — F1: there is NO navigation inside the Champion's Room.** The `OnFrame` script `lockall`s and
walks the player itself (6,12)→(6,6). A driver pathing to (6,6) issues movement into a locked player.
⇒ **issue NO movement after the door step.**

**Input gates (the press formula was wrong three times over):**
* **S1** — `\p` *and* `\l` both halt in `TextPrinterWaitWithDownArrow`, which returns only on
  `JOY_NEW(A|B)`. ⇒ pre-battle **14 not 11**; post-battle **41–42 not 37**; HoF map **7 not 4**.
  A bound of 11 stops three prompts short and reports "the battle never started" on a working room.
* **S3** — "presses nothing during the Hall of Fame" conflated the HoF **MAP** with the HoF **SCREEN**.
  The stall is specifically at `Task_Hof_ExitOnKeyPressed`.

**Acceptance/grading:**
* **S4** — ⛔ **"party fully healed" is NON-DISCRIMINATING**: `DoWhiteOut()` calls the same
  `HealPlayerParty()`, so a LOSS — room 5's only failure mode — reads identically.
* **S5** — the HoF **map** is the *better* acceptance window: `(16,11)` is reachable only through
  `CHAMPIONS_ROOM` warp 1 behind Wallace, so standing there **is** evidence the fight was won.
  A Champion's-room reading proves only that `fight()` returned.
* **T13/T14** — grading on `DEFEATED_ELITE_4_*` reads **FALSE on success**; RAM `SYS_GAME_CLEAR` alone
  is a **vacuous PASS**. ⭐ **The FLASH read is a legitimate precondition gate for a reset; the RAM read
  is vacuous as an acceptance grade.** Two roles — do not collapse them.

**Hang/wedge:**
* **S10/S12** — the BattleListener wedge is **real by default but fixable in two lines**: the escape is
  opt-in via `handles_battle_faults`, which appears **zero** times in the harness. The driver must set
  `handles_battle_faults = True` **and** call `take_pending_fault()` every frame it holds control.
* **S6** — the reset-early design's load-bearing step is **UNMEASURED**: the arms only prove a sav copied
  in *before* the run survives, never that flash written *by the game* survives `_core.reset()`.
* **S8** — HoF visual progress is **NOT** evidence of a save (a task-destroy freeze, and a
  `gFlashMemoryPresent != TRUE` path plays the whole parade having written nothing).

---

## 4. THE CONTRADICTIONS — recorded, not smoothed over

* **C1 — HoF: map or screen?** ⭐ **Two stages.** Decisive; it relocates both where the driver stalls
  and where it should grade.
* **C2 — 11 or 14 presses?** 14. ⇒ **do not hardcode either**; drive on script-context liveness with
  20/60 only as ceilings.
* **C3 — reset early or sit through the credits?** **Adopt the design, discard the recipe.** For the
  FIRST drive, faithful wins: only it produces the numbers; `06-DECISIONS-LOG.md` RULING 3 is the user's
  own *"yes drive through the post game save"*; and `gGameContinueCallback` is armed to
  `CB2_DoHallOfFameScreenDontSaveData` *before* the save, so an immediate CONTINUE may re-enter the HoF.
* **C4 — is the harness's reset recovery broken here?** Split: the measurement is real, the consequence
  was never demonstrated. **Do not preemptively patch the harness** — let the probe decide.
* **C6 — "fully healed" as acceptance?** Refuter wins decisively.
* **C8 — 57 or 58 credits pages?** **57. Our punch list is wrong** and must be corrected.
* **C10 — flash vs RAM `SYS_GAME_CLEAR`:** different roles, both legitimate; see §3.

---

## 5. STILL UNKNOWN — only a live run settles these

1. Every frame cost from the door step to the reboot (**none of it has ever been run here**).
2. Whether HoF+credits exceed the 20,000-frame no-progress budget.
3. Whether `_in_battle` clears after Wallace at all.
4. ⭐ Whether flash written **by the game** survives `_core.reset()`.
5. Whether the harness's non-recovery on the in-game SoftReset has any consequence.
6. Whether an A-edge-every-2-frames cadence consumes prompts 1:1.
7. Where the avatar actually rests at each stage.
8. Whether an immediate CONTINUE re-enters the Hall of Fame screen.

---

## 6. TRAPS — builder's checklist

⛔ **T27 FIRST: re-grep every line number.** The recon's harness citations have ALREADY drifted
(hang detector `:22377`/`:22393`, reset guard `:21488`, stack pop `:22246`). Never copy one forward.

- [ ] **T1** the 20,000-frame no-progress detector — its signature is **constant** across HoF+credits.
      Defeat it by making `ctrl` change. ⛔ Do NOT stuff `"end of built content"` into `context.message`.
- [ ] **T2** reset rebuilds `bot_listeners` but never clears `controller_stack` — **and the guard never
      fires for an in-game SoftReset at all** (frame_count keeps increasing).
- [ ] **T3/T4** `fight()` starves the driver; the escape is opt-in — set `handles_battle_faults = True`
      and call `take_pending_fault()` every frame.
- [ ] **T5** a driver whose `run()` RETURNS is re-instantiated next frame. End with `set_manual_mode()`.
- [ ] **T6** a winning run reports `HANG CONFIRMED` today.
- [ ] **T7** `_wait_until_cutscene_over` presses nothing on a CB2 screen and then RAISES. It DOES work
      on the HoF map.
- [ ] **T8** `_dialogue_button('A')` returns `'B'` **[M]**, while the HoF gate is A-only. ⛔ Do not loosen
      it (it guards the Slateport greeter) — build a separate bounded CB2-aware A-presser.
- [ ] **T9** a HOLD never satisfies `JOY_NEW`.
- [ ] **T10** `_pass_through_door` and `calculate_path(→(5,2))` both land you INSIDE the room.
- [ ] **T11** never assert arrival at a warp's target tile (R-WARPREST).
- [ ] **T12** two objects un-hide onto **(6,12)** post-battle (flags 920/921) — the arrival tile.
- [ ] **T16** `soft_reset()` is unusable as-is (opens with `emulator.reset()`; unbounded `while True`;
      no `NAMING_SCREEN` arm; random pool includes **"Up"**).
- [ ] **T17** a blank sav sends the reboot into NEW GAME **silently** **[M A/B]**. Gate on
      `get_save_data()` before AND after; hard-abort on `NAMING_SCREEN`.
- [ ] **T19** never hold SELECT / B+SELECT at the title (`CLEAR_SAVE_BUTTON_COMBO`).
- [ ] **T20** a leaked held button survives `emulator.reset()` (`#24-truckleak`, 146 runs lost).
- [ ] **T21** `get_game_state()` is **UNKNOWN** for the entire post-`GameClear` tail — branch on
      `get_game_state_symbol()`, ALL-UPPERCASE.
- [ ] **T22** do not hold B to fast-forward the credits.
- [ ] **T23** ⛔ never re-enter the Champion's Room to re-check or re-grade — every entry refights a
      full-strength Wallace with a damaged party.
- [ ] **T24** no abort path exists: `allow_escaping: false` in all three maps.
- [ ] **T25** ⛔ do not flip `allow_revive=True` (KI-100 wants a PID-grounded probe first).
      ‼ **AND KI-100 DOES NOT SAY THE GAME FORBIDS IN-BATTLE REVIVES** — it says *our call site* sets
      `allow_revive=False` deliberately. Several of our docs stated this wrongly; corrected 2026-09-17.
- [ ] **T26** a second CONTINUE resumes wherever the game last saved (the HoF map).
