# 2026-09-30 — design v2 step 12 (weaken-to-catch) recon: an audit of our code (where W-b plugs in)

⚠ **A NOTE, NOT TRUTH.** A Claude recon agent's report (model output), verbatim. Every load-bearing claim is re-checked by the author at its FILE:LINE before the design relies on it; the design note records which.

# Step 12 (W, weaken-to-catch): where the W-b adapter plugs in, and where the spec is wrong about our code

This is a note, not truth. Read-only audit of worktree `pokebot-wt-ch24` at HEAD `cdb49f83`. The two files already modified in the tree (`party_accounting_ledger.jsonl`, `magma_1f_fail.ss1`) were not touched.

**Paths used below:**
- SM = `sandbox-pokebot/plugins/custom_modes/story_mode.py`
- CS = `sandbox-pokebot/modules/battle_strategies/catch.py`
- BS = `sandbox-pokebot/modules/battle_state.py`
- U = `sandbox-pokebot/modules/battle_strategies/_util.py`
- BAS = `sandbox-pokebot/modules/battle_action_selection.py`
- Decomp files were fetched with `gh api` into the scratchpad.

**Bottom line:** no weaken code exists yet. The adapter's intended spot in `StoryCatchStrategy.decide_turn` is correct. The spec is wrong or incomplete on five points that will break gates or safety (section 3, items 1–8).

## 1. Current FILE:LINE for every site the spec names (all VERIFIED)

| Spec's line (as of 57b46186) | Now | What is there |
|---|---|---|
| — | SM:85-93 | `StoryCatchStrategy.decide_turn`. The out-of-balls flee is SM:86-92 (inside `try/except: pass`) and marks `_r20_mark("end","out_of_balls")` at :89. `return super().decide_turn(...)` is SM:93, **outside any try**. W-b goes between :92 and :93. |
| — | CS:41-62 | Parent `CatchStrategy.decide_turn`. It throws a ball, or uses a status move when the target is Healthy and the one-throw chance is below 0.5 (CS:50-60). |
| — | CS:64-65 | `decide_turn_in_double_battle` just calls `self.decide_turn`, so the adapter **is** reached in a double. It must check `BattleType.Double` itself. |
| — | CS:38-39 | `should_flee_after_faint` returns False. |
| — | SM:112-235 | `StoryDexCatchStrategy`: reserve and faint bail in `decide_turn` SM:197-217 (then `super()` at :217); faint bail in `should_flee_after_faint` SM:149-171; trapped-and-empty fight-out SM:219-235; its `__init__` SM:123-140. The bails run before W-b by construction. |
| :243 | **SM:275** | `StoryShinyCatchStrategy.decide_turn` (SM:251-275) calls `CatchStrategy.decide_turn(self, ...)` directly, so it never reaches a W-b placed in the `StoryCatchStrategy.decide_turn` body. W-b must not be put in a `CatchStrategy` hook (for example an override of `_get_best_status_changing_move`), because shiny would inherit that. |
| shiny :3875 | **SM:4093** | `_r20_catch_start(self,"shiny",…)` at :4092 |
| hm :3910 | **SM:4128** | start at :4127 |
| counter :4020 | **SM:4238** | start at :4237 |
| dex/team :4121 | **SM:4015**, now inside **`StoryMode._dex_catch_commit` (SM:3952-4018)**, not `on_battle_started` | `return StoryDexCatchStrategy() if _post_badge else StoryCatchStrategy()`. The start call is at :4014 with kind "dex" or "team". `_post_badge` (SM:4002-4010) falls back to False, i.e. "team", if the badge flag can't be read. The commit is called twice: SM:4257 (OVERSURVIVAL on) and SM:4309 (off). |
| reset_per_run_state :2151 | **SM:2249** | R25 flags at SM:2370-2375 (`_r25_cap`, `_r25_rare`, `_r25_last_verdict = None`). R24 flags at SM:2357-2369. |

**Docstrings and comments claiming a catch never damages or never fights back:**
- ~:72-77 is now **SM:72-83**, the `StoryCatchStrategy` class docstring: ":72 A CATCH BATTLE NEVER FIGHTS BACK", ":73-74 never a damaging move", ":75-76 the wild attacks for free".
- `dex_catch_bail_reason` ~:96-110 is now **SM:96-109**. The phrase is split across lines: "a catch battle never" at :100 and "fights back" at :101, so a single-line grep for "never fights back" misses it. There is also "(the wild attacks for free)" at :103.
- ~:1725 is now **SM:1773**, in `dex_catch_expected_throws` (:1768-1784): "the catch strategy never damages". Its conclusion (the estimate is an upper bound) still holds, because damage only raises catch odds. Only the stated reason needs to change.
- ~:1975 is now **SM:2073-2078**, inside `decide_dex_catch`'s health gate.
- **The spec misses two more:** `tools/story-dev/probe_dexcatch_bail.py:4` and `tools/story-dev/probe_dex_open_fence.py:8`.
- The spec's ":1734-1735 / :1964-1969" now point at unrelated text: SM:1733-1735 is an `_expected_throws_for` comment and SM:1962-1971 is `decide_dex_catch`'s egg-count docstring.

**R25 helpers and constants:**
- `r25_rarity_verdict` SM:1864-1876; `r25_catch_inputs` SM:1879-1885; `_r25_log_suffix` SM:1888-1900.
- `R25_MAX_ATTEMPTS = 3` SM:1694; `DEX_CATCH_BALL_RESERVE = 10` SM:1681.
- The rare verdict is set in `_should_catch` at SM:2615 and :2637-2640.
- **INFERRED from the branch order in `on_battle_started` (SM:4073 → :4106 → :4135 → :4256):** the hm and counter branches return before `_should_catch` runs. For those kinds, `mode._r25_last_verdict` still holds the previous battle's verdict and must not be read.

**[CATCH] telemetry:**
- `start` SM:6446-6469 (the rare suffix is added only for dex/team, :6465); `end` SM:6493-6548; mark helpers SM:6472-6490; `trainee` lines :6280 and :6294; `loss-filed` :2482.
- In `[CATCH] end`, the outcome `Won` falls through to `end=other` (SM:6507-6522). So a weaken KO would read `end=other res=Won`. The same reading already happens with the flag OFF, in a trapped fight-out (`bail=trapped`) and a shiny fight-through (SM:251-268).

**Step 11 (dmgaudit) hooks:**
- BAS:15 (import), BAS:117-118 `on_selection_entry`, BAS:1009-1012 `on_selection_exit` (only on the loop fall-through; early returns skip it).
- `battle_handler.py:324-325` `on_battle_start`; `:417-418` `on_battle_end`.
- `dmgaudit.py` already reads raw `gChosenActionByBattler` and `gChosenMoveByBattler` (:56, :72-73, :103-106) and `gSideStatuses` (:57). Its contract is no `get_battle_state()` because of KI-108 (:13-14). KI-108 itself is `05-KNOWN-ISSUES.md:3066`, and `BattleState.__eq__` at BS:249-261 does omit the party order and the turn.

**`[TURN]` line:** it is emitted with category BATTLE at **BAS:537-541** (the spec says :535-537).

**`weaken_catch.py`:** does not exist. There is no `probe_weaken_catch.py`, no `POKEBOT_R25_WEAKEN*` anywhere, and no registry rows. VERIFIED by `find` and `grep`.

## 2. How moves and state are exposed (VERIFIED against the decomp)

**How a move slot is chosen:**
- `TurnAction.use_move(i)` does no validation (`_interface.py:113-115`).
- The index goes `battle_action_use_move` (BAS:1190-1272) → `scroll_to_move` → `_select_in_menu("gMoveSelectionCursor", i)` (`battle_menuing.py:95-96`). So `i` is the game's move-menu slot.
- Nothing checks PP, Disable, Taunt or Choice Band before the game sees the pick. When the game refuses a pick, two paths change the index:
  - **KI-93 re-pick** (BAS:391-418): picks the first slot with PP that was not refused. It fires on the refusal scripts at BAS:48-55: Tormented, Disabled, Taunted, Imprisoned, ChoiceItem, NoPP.
  - **NoPP override** (BAS:555-572): picks the first slot with PP.
  - The `[TURN]` line logs the index after the KI-93 re-pick but before the NoPP override.

**Our mon's moves:**
- `BattlePokemon.moves` (BS:518-533) **skips empty slots** (the `continue` at :525), so the list is compacted. PP is read from the real slot (`0x24+index`, :528). This matches `06-DECISIONS-LOG.md:4600-4604`.
- Party `Pokemon.moves` keeps the empty slots as None (`pokemon.py:1104-1105`).
- The parent's status chooser (CS:186-210) uses the compacted indices. It checks Taunt (CS:188), PP, and the target's Insomnia, Vital Spirit and Limber (the ability read described below). It does **not** check `banned_moves`, Disable, the target's Substitute, Safeguard, Soundproof or type immunity.

**BattleState fields:** all offsets below match `struct BattlePokemon`, `DisableStruct` (`include/battle.h:70-102`) and `SideTimer` (`:149-162`). `gSideTimers` is 0x18 bytes in `pokeemerald.sym:163`, i.e. 12 per side, so the `[0:12]` / `[12:24]` slices at BS:301 and BS:305 are right.

| Field | Where | Notes |
|---|---|---|
| hp | BS:622-624 | offset 0x28 |
| max HP | BS:632-634 | 0x2C |
| level | BS:653-655 | 0x2A |
| held item | BS:661-667 | 0x2E |
| status1 | BS:704-706 via `pokemon.py:821-845` | Collapses to a single enum: no sleep-turn count, no toxic counter. |
| status2 / status3 | BS:708-710 → `TemporaryStatus.from_bitfield` BS:117-196 | Every bit matches `include/constants/battle.h:129-178`: Substitute bit 24; Confused 0-2; Wrapped 13-15; Nightmare 27; Cursed 28; Torment 31; **LeechSeeded is status3 bit 2**; InTheAir 6, Underground 7, Underwater 18 (semi-invulnerable); Minimized 8. |
| substitute HP | BS:744-746 | 0x0A |
| Disable | BS:716-722 and BS:748-750 | disabled move at 0x04, timer at 0x0B |
| Taunt | BS:772-774 | 0x13 |
| **Encore** | BS:728-734 | **BUG:** reads 0x04 (disabledMove). The decomp puts `encoredMove` at 0x06 (`include/battle.h:73-74`). `can_use_move` (BS:547-559) inherits the error. |
| Safeguard | `opponent.safeguard_timer` BS:449-451 | Timer only. The `SIDE_STATUS_SAFEGUARD` bit (`constants/battle.h:214`, in `gSideStatuses`) is not in BattleState. |
| Spikes | BS:457-459 | |
| weather | BS:311-322 | Matches `constants/battle.h:232-244`. Ignores Cloud Nine and Air Lock (U:497 has a todo; the game macro is `WEATHER_HAS_EFFECT` at `include/battle_util.h:47`). |
| battle type | BS:279-297, flags at BS:42-74 | Double, Trainer, Safari, Roamer bit 10. |
| turn number | BS:822 | `gBattleResults+0x13` |
| ability | BS:566-570 | Taken from the species plus the ability bit. The live, Trace-able byte is `ability_n` (BS:572-574), which can be mapped with `get_ability_by_index` (`pokemon.py:1495`). |
| side ability check | BS:468-469 | `has_ability` uses the species-based ability. |

**Other game facts checked:**
- **Encore overrides our choice:** when our battler is encored, picking Fight uses the encored move with no move menu (`src/battle_main.c:4191-4196`).
- **Choice Band:** the game substitutes the locked move (`src/battle_util.c:1051-1053`). BattleState does not expose the locked move, so a Choice Band on `held_item` (`ItemHoldEffect.ChoiceBand`, `items.py:139`) is the only available check.
- **Catch formula:** `Cmd_handleballthrow` is at `battle_script_commands.c:9905`; the formula is :9987-10028, which confirms the spec's lines.
  - Our exact integer version already exists for full HP only: SM:1768-1784, with the ball bonuses at SM:1703.
  - The parent's `calculate_catch_success_chance` (U:271-294) uses floats and is not clamped: it can return more than 1 when odds exceed 254.
- **Exact-damage moves still go through the type check:** Level Damage (`data/battle_scripts_1.s:1200`), Sonicboom (:1725), Dragon Rage (:824) and Super Fang (:814) all run `typecalc`, so Ghost is immune to Sonicboom, Super Fang and Seismic Toss. `calculate_move_damage_range` returns the fixed damage even against an immune type: U:212-213 zeroes it, then U:215-228 returns the fixed value regardless.
- **Move data names:** `moves.json` spells them "Sonicboom", "Selfdestruct" (effect EXPLOSION, the same as Explosion), "Grasswhistle", "Mud-slap", "Double-edge". Struggle's effect is RECOIL.
- **Banned moves:** `profiles/battle.yml:21-46` (False Swipe at :34). U:255 and U:594 honour the list; CS:186-210 does not.

## 3. Where the spec is WRONG or incomplete about our code

1. **"`weaken=` is passed at the three sites":** no constructor accepts it.
   - `StoryCatchStrategy` has no `__init__`, and `CatchStrategy.__init__(self)` takes no arguments (CS:25). `StoryDexCatchStrategy.__init__(self)` is at SM:123-124.
   - Gates build instances with `__new__`, skipping `__init__`: `probe_dexcatch_bail.py:100-105`, `probe_dex_catch_nofaintbail.py:120`, `repro_shiny_noballs.py:48`. So the value must be read with `getattr(self, …, None)`, as SM:154-155 already does.
   - The harness builds `StoryCatchStrategy()` with no arguments at `story_harness.py:2304` and `:2484`, so the default must be inert.
   - The shim `self` in `probe_dex_catch_oversurvival.py:162-163` has no mode attributes. The construction sites must use `getattr`, following the step-4 lesson at SM:4248-4252.
2. **Existing gates pin the construction text and will go red** (the spec doesn't list them):
   - `probe_dexcatch_bail.py:78` requires the exact string at SM:4015.
   - `:85` requires the count of `"StoryDexCatchStrategy()"` across both methods to be 1.
   - `:87` requires the count of `"return StoryCatchStrategy()"` in `on_battle_started` to be at least 2 (the hm and counter sites).
   - The fault arms at `:217-221` do string replacements on those same texts.
   - `probe_r20_telemetry.py:257-290` requires `_r20_catch_start` to be the statement immediately before each catch return (`body[i-1]`), so no line may be inserted between :4014/:4015, :4127/:4128 or :4237/:4238.
3. **The dex/team "site" is one expression that builds two classes for two kinds**, and it lives in `_dex_catch_commit`. So the spec's A1 check has to walk both `on_battle_started` and `_dex_catch_commit`, as the existing gates already do (`probe_r20_telemetry.py:272-275`, `probe_dexcatch_bail.py:80-86`).
4. **"Slots not contiguous → DEFER" can't be checked from `BattlePokemon.moves`,** because the list is compacted (BS:524-525). It needs the raw bytes `_data[0x0C:0x14]` (a private attribute) or the party mon's `moves` via `party_index`. **INFERRED:** the party copy can differ under Mimic or Transform.
5. **The DEFER list misses three cases** (VERIFIED code paths; the risk is INFERRED):
   - Encore: the game ignores our slot choice (battle_main.c:4191-4196), and our encore reader is wrong (BS:730).
   - Torment and Imprison: these trigger the KI-93 re-pick (BAS:391-418), which can run a damaging move the hazard floor never checked.
6. **`[WEAKEN] obs … at the next decision` is the wrong trigger:**
   - `decide_turn` can run more than once per turn: the selection handler is re-entered (BAS:423-424; `dmgaudit.py:25-26`).
   - No next decision happens after a KO, which is the one failure that matters. A KO shows only as `[CATCH] end … end=other res=Won` (SM:6507-6522).
   - The per-battle counters (3 damage turns, 2 no-progress turns, 3 status tries) must key on `battle_state.current_turn` (BS:822), not on how many times `decide_turn` is called.
   - Instrumenting the action (rule 7) means reading `gChosenMoveByBattler`, as dmgaudit does, not the candidate slot.
7. **Where the logs and reads go:**
   - `[WEAKEN]` and `[WEAKEN-OBS]` need their own `debug_logger` category. The logger prints `[category] message` (`debug_logger.py:332-338`); putting them in BATTLE or CATCH breaks the byte-identical OFF control by construction.
   - The adapter must reuse the `battle_state` it is passed and not call `get_battle_state()` (KI-108).
   - lint_docs R6 scans `tools/story-dev` (`lint_docs.py:283-285`), so every fault-arm string in the new probe needs a row in `29-DISABLED-FEATURES-REGISTRY.md`.
8. **Smaller points:**
   - The adapter must honour `context.config.battle.banned_moves`.
   - A DEFER does not mean "throw". It hands the turn to the parent, whose status chooser (CS:50-60) is unguarded.
   - **INFERRED:** in `observe` mode, `would=` is counterfactual only on the first turn; after that it describes a state the parent reached by throwing, not by weakening.
   - The L0 readout will print "Mud-slap", not "Mud-Slap".
   - **Not checked:** the spec's claims about the fixture's party (Stage 1 being vacuous on `r20_pregym1_party4_r116.ss1`); that needs a live read.
