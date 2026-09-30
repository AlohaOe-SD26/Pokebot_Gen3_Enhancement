# 2026-09-30 — design v2 step 12 (weaken-to-catch) recon: an adversarial refutation of the v2 step-12 spec

⚠ **A NOTE, NOT TRUTH.** A Claude recon agent's report (model output), verbatim. Every load-bearing claim is re-checked by the author at its FILE:LINE before the design relies on it; the design note records which.

**STEP 12 ADVERSARIAL REVIEW. This is a note, not a source of truth. Read-only: nothing in the worktree was changed.**

Worktree `C:/Remote Projects/pokebot-wt-ch24`, branch `wt/weaken12` = `cdb49f83`. Decomp line numbers are from pret/pokeemerald master, fetched with `gh api` on 2026-09-30.

Abbreviations:
- **v2** = `PROJECT KNOWLEDGE/ai-research-notes/2026-09-29-r23-27-DESIGN-v2.md`
- **D11** = `…/2026-09-30-dmgcalc11-DESIGN.md`
- **SM** = `sandbox-pokebot/plugins/custom_modes/story_mode.py`
- **BAS** = `sandbox-pokebot/modules/battle_action_selection.py`
- **BS** = `sandbox-pokebot/modules/battle_state.py`
- **U** = `sandbox-pokebot/modules/battle_strategies/_util.py`
- **bsc.c** = `src/battle_script_commands.c`
- **bs1.s** = `data/battle_scripts_1.s`
- **learnsets** = `src/data/pokemon/level_up_learnsets.h`

Tags: VERIFIED means I read the line. INFERRED means reasoning or standard mechanics that I did not read at a line.

## Blockers

**B1. The gate plan points at rows that do not exist.**
- **Spec:** v2:647 says "rows W1-W37 as in the weaken pass". The fault sets at v2:653-657 name W2, W3, W19, W20 and W23.
- **Evidence (VERIFIED):**
  - A grep of every `.md` file in the tree for W19, W23 or W37, outside v2 itself, finds nothing.
  - The only weaken-pass remnant is v1 §4b (`2026-09-28-r23-25-DESIGN.md:497-569`). It is "discussion only" and has no numbered rows.
- **Why it blocks:** the "assert set equality" fault sets cannot be registered in advance. A builder would have to number the rows and then choose the sets afterwards.
- **Fix:** file the W-row table (id, snapshot, expected verdict) in the step 12 predictions before any code, then write the fault sets against it.

**B2. The move that runs can differ from the move the module chose, which is a stage-1 KO path.**
- **Spec:** the only selection hazards covered are "PP, Disable, Taunt and Choice Band" (v2:647). The damage floor (v2:633-635) is checked only for the move the module picks.
- **Evidence (VERIFIED):**
  - **Encore.** When we are encored and pick Fight, the game runs the encored move without opening the menu (`src/battle_main.c:4192-4196`). Encore lasts 3-6 turns (bsc.c:8039).
  - **Our Encore reader is wrong.** `BS:729-734` `encored_move` reads disable-struct offset 0x04, which is `disabledMove`. `encoredMove` is at 0x06 (`include/battle.h:73-74`). The upstream mirror has the same bug. `encore_turns_remaining` (0x0E, BS:753) is correct.
  - **Torment.** The game refuses our last-used move (`src/battle_util.c:999`).
  - **Our handler substitutes blindly after a refusal.** The KI-93 re-pick replaces a refused slot with the first slot that has PP (`BAS:390-418`: `_ki93_alt = _slot` at :411, `index = _ki93_alt` at :418). The no-PP override does the same (`BAS:553-569`). Neither checks the weaken floor.
  - **Exposure:**
    - Spheal knows Encore from L7 (learnsets), and `emerald_rarity.json` lists it at best rate 50 across the Shoal Cave rooms.
    - Nuzleaf learns Torment at L25; it is on Route 114 at 1%, which makes it rare by rate.
    - Vulpix, Ralts and Kirlia learn Imprison.
- **Concrete KO path:** we use Dragon Rage (40 damage). The target Encores it. The module's next pick is sleep, per the order at v2:604. The game runs Dragon Rage instead on a target at 40 HP or less, and it faints.
  - DEFER does not save it: the parent's status pick (`catch.py:57-60`) is also forced into the encored move. With weaken OFF this never happens, because our last move is never a damaging one.
- **Fix:**
  - Put Encore (0x06 plus the timer at 0x0E), our Torment (`BS:159`) and the target's ImprisonedOthers (`BS:180`) into the snapshot.
  - While any of them is active, the verdict is THROW-ONLY. The only exception: the encored move itself, and only if it passes the floor at the current HP.
  - Add a row and a fault for each.
  - Log the move that actually ran (`gChosenMoveByBattler[0]` at the selection exit, as dmgaudit does; D11:35-37 B3), per rule 7.

## Should-fix

**S1. Nothing gates the stage-1 / stage-2 boundary.**
- **Spec:** v2:633-639 and the row list at v2:647.
- **Evidence:**
  - No row asserts "WEAKEN=1 with WEAKEN_CALC unset: a plain hit is never a candidate, even when the calculator would admit it".
  - No fault covers it.
  - This boundary is the whole safety decision of this step: the calculator is measured but not cleared (dmgcalc11 GRADED:3-7; D11:240-249).
- **Fix:** a row pair on the same snapshot (CALC unset → not admitted; CALC set → admitted), plus a CALCLEAK fault that reddens exactly those rows.

**S2. The hazard floor protects one turn, but the hazards repeat.**
- **Spec:** v2:625-628, together with the order "damage, then sleep" (v2:604, v2:617).
- **Evidence (VERIFIED):**
  - Recoil applies on every use: 1/4 at bsc.c:2636-2639, 1/3 at :2843-2846, minimum 1. The damage it keys on is capped at the victim's HP (bsc.c:1921-1928).
  - Struggle's recoil ignores Rock Head: the Struggle branch jumps past the Rock Head check (bs1.s:3939-3940). So "Rock Head → 1" (v2:627) fails once a Rock Head target runs out of PP.
  - Ghost Curse can faint its own user (bs1.s:1525-1529, `datahpupdate BS_ATTACKER` then `tryfaintmon BS_ATTACKER`). It fails only if our current mon is already cursed (bsc.c:8470-8479). After our cursed mon faints, a fresh one comes in and can be cursed again.
  - The recoil floor is computed from our current HP (v2:627). A faint-switch brings in a mon with more HP.
  - Up to 3 sleep tries come after the damage turn, while the target is still awake and can still use its recoil move.
- **Fix:**
  - For targets that know recoil or Ghost Curse: either do no damage, or take the floor over the expected remaining turns using the party's maximum HP.
  - For those targets, sleep first. Exception: targets that know Sleep Talk, which can call recoil moves or Explosion (bsc.c:8209-8219 excludes only Sleep Talk, Assist, Mirror Move and Metronome).
  - Add rows for Rock Head plus Struggle, Curse after a faint-switch, and recoil over k turns.

**S3. The observation line cannot see the outcome it exists to check.**
- **Spec:** v2:644, "`[WEAKEN] obs … at the next decision`".
- **The four gaps:**
  1. **A knockout has no next decision.** The battle ends, so the obs line is never written. Step 11 found and fixed this exact problem (D11:38-43 B4; D11:147-151 pairing at battle end). Today the only KO signal is `[CATCH] end … end=other res=Won` (SM:6506-6519, :6541-6545), and the live proof never names it.
  2. **The HP difference is confounded.** Step 11 measured a heal that hid our hit (D11:206-209) and moved to Δ`gBideDmg[1]` for that reason.
  3. **"The next decision" can be the same turn.** After a refusal the handler is re-entered within one selection (BAS:24-31).
  4. **`prev=` records the candidate, not the executed move** (see B2).
- **Fix:**
  - Reuse dmgaudit's BEFORE/AFTER/end reads, and add a battle-end hook.
  - Pre-register "0 `[CATCH] end … res=Won` in any ON arm" as the primary safety readout.

**S4. The live controls are weaker than what step 11 and KI-112 now require.**
- **Spec:** v2:660, "an OFF control on seed 1 … byte-identical in every `[TURN]`/`[CATCH]` line".
- **Evidence (VERIFIED):**
  - KI-112 (05:3150, :3163): "One control run is not a control"; graded A/Bs run the control at least twice.
  - 05:3185: per-turn tables come from two runs separated in time.
  - Step 11's rule (D11:227-231) compares every frame-stamped line that does not contain the flag's name, and requires zero such lines with the flag off.
  - The spec names no log category for `[WEAKEN]`/`[WEAKEN-OBS]`. `[TURN]` is logged in category BATTLE (BAS:538-541), which is why step 11 gave its lines their own category (v2:584).
- **Fix:** run OFF twice, separated in time. Compare every non-WEAKEN line. Put the new lines in their own `WEAKEN` category, and require zero lines containing "WEAKEN" with the flag off.

**S5. L0 can show only that observe is inert, and even that is at risk.**
- **Spec:** v2:660, "The readout replaces the paper predictions". That contradicts v2:159, which says predictions come before any drive.
- **What L0 cannot fail on today:**
  - It has no correctness check. Add:
    - (a) exactly one OBS line per in-scope decision, reconciled against the `[TURN]` lines inside team or dex `[CATCH] start` battles;
    - (b) no OBS lines in shiny, HM, counter or trainer battles;
    - (c) each OBS line's snapshot, replayed through the pure module, gives the same `would=`.
- **Its predictions rest on unread facts:**
  - `FIXTURES.md5:92` gives species and levels only, not movesets.
  - The lead can rotate (`default.py:211-217`), so "Skitty `would=damage Mud-Slap`" assumes Mudkip is leading.
  - The spec does not say whether L0 sets WEAKEN_CALC, and "under CALC only" depends on it.
  - Which species are already owned is not read, so the Taillow and Abra rows may never become catch battles.
- **The window is not sized:**
  - Team catches stop once the party reaches the target of 6 (SM:2344-2349), and the fixture starts at 4, so a seed gives about 2 successful team catches before gym 1.
  - The window rule at v2:862 ("never size a window without the encounter rate") is not applied.
- **The acting path never runs live:**
  - Add an execution arm, following step 11's M1b-EXEC (D11:265).
  - To make stage 1 non-vacuous, add a harness lever such as `--set-lead-move`, with a read-back like `--set-balls` (`story_harness.py:32`, :29029-29031).
  - INFERRED: Seismic Toss on the L13 Mudkip deals a fixed 13 against the Normal-type targets there, and Fighting is not immune to them.

**S6. The "does not show" caveat is false for stage 1.**
- **Spec:** v2:666, "the mid-game … no damage move is admissible".
- **Evidence (VERIFIED):** exact damage does not depend on the target's level:
  - Sonicboom does 20 (bs1.s:1727) and Dragon Rage 40 (bs1.s:826).
  - Night Shade and Seismic Toss do our level (bs1.s:1202).
  - Super Fang halves the target's current HP (bsc.c:7577-7581).
- **Consequence:** Super Fang is admissible from any HP of 2 or more, as long as the target is above 50%. So a stage-1 "no difference" in the mid-game is evidence, not a non-result.
- **Fix:** scope the caveat to stage 2.

**S7. Legendary battles are missing from DEFER.**
- **Spec:** the DEFER list at v2:605-610. But §5 (v2:847-851) says the design DEFERs when it is unclear whether a defeated legendary comes back.
- **Evidence:**
  - RULING 25 makes legendaries uncapped (06:8049).
  - The battle-type flags exist to test: Legendary, Regi, KyogreGroudon, Groudon, Kyogre and Rayquaza (BS:55-56, :71-73). Pyramid and Pike are at :63-64.
- **Fix:** add them to DEFER, with rows.

**S8. Abilities are read from the species, not the battle.**
- **Evidence (VERIFIED):**
  - `BattlePokemon.ability` returns the species ability chosen by a bit (BS:566-570). The live ability byte is `ability_n` at 0x20 (BS:573-575).
  - The game checks the live ability: sleep immunity at bsc.c:6836-6837, sand at :7614, Limber at bs1.s:1011.
  - Step 11 added a classifier reason for exactly this, `ability-not-species` (D11:359-361).
- **KO path (INFERRED):** our Kirlia or Gardevoir with Trace copies the target's Rough Skin, Flame Body, Effect Spore or Poison Point. Carvanha is at best rate 100 on Routes 118/119; Slugma, Shroomish and Roselia are the others. The "our contact ability" hazard (v2:628) is then missed.
- **Fix:** map `ability_n` through `abilities.json`, and add Trace rows.

**S9. Stage 2 is built now (OFF) but leaves out step 11's known divergences.**
- **W is undefined.** D11:247 says so; v2:637 still uses it.
- **Guts plus burn.**
  - Ours: ×1.5 for Guts (U:397) and a burn halving that ignores Guts (U:444-446).
  - Game: the halving is skipped with Guts (pokemon.c:3211, :3263).
  - Result: we under-predict by about 2×, for example a burned Swellow.
- **Our Flash Fire is not modelled** ("todo", U:518), a 1.5× under-prediction.
- **Marvel Scale checks the wrong battler's status.** Ours looks at the attacker (U:399); the game looks at the defender (pokemon.c:3213).
- **Charge plus D1** can be 8 HP low; the bound absorbs that only at c ≥ 41 (D11:247-249).
- **Fix:**
  - Exclude every persistent divergence from the snapshot (the list at D11:165-166).
  - Define W.
  - Name the weaken margin `WEAKEN_MARGIN`. It must be separate from `ACCEPT_MARGIN` (D11:242-243). v2:732 still calls it plain "MARGIN".

**S10. Some fault sets cannot be exact, and some rows cannot fail.**
- **The name-dispatch fault cannot redden W20.** It lists {W19, W20} (v2:655), but only Sonicboom's name differs between the calculator and the data (`moves.json:1718` "Sonicboom" vs U:218 "Sonic Boom"). The other four names match:
  - Seismic Toss and Night Shade: U:224 vs `moves.json:2418` and :3538.
  - Dragon Rage: U:215 vs :2873.
  - Super Fang: U:221 vs :5673.

  So the LEVEL_DAMAGE row stays green under name dispatch.
- **The no-hazard fault's set is not a set.** "The hazard rows, W40 included" (v2:654) lists nothing.
- **Rows with no fault behind them:** W38, A1, non-contiguous slots, and "observe returns the parent's action".
- **Step 11's precedent:** a coverage row fails if any row is in no mutant set (D11:326), and the first adversarial pass found 96 of 107 mutants that the gate missed (D11:344).
- **Fix:** enumerate every set, add the coverage row, and run an adversarial mutant pass.

**S11. Adapter-level rows sit in a "pure" gate, where they cannot fail.**
- **Spec:** "reserve bail first", "0 balls → flee" and "observe returns the parent's action" (v2:647).
- **Evidence:** these can only fail if the real classes run: `StoryDexCatchStrategy.decide_turn` (SM:197-217) and `StoryCatchStrategy.decide_turn` (SM:85-93). This is the step 8 lesson (A-S1 and K11, v2:14, :871).
- **Also missing:**
  - An AST row that the adapter adds no `get_battle_state()` call (KI-108, 05:3066; step 11's NH-gbs-count row).
  - A defined failure path: the adapter's own `try`, falling back to DEFER with a `[WEAKEN] ERR` line (flag on only).

**S12. Stage 1 has no immunity, progress or E-gain check.**
- **Evidence:**
  - VERIFIED: every exact-damage move runs `typecalc` first (bs1.s:1200, :1725, :824, :814).
  - INFERRED (standard mechanics; v1 C21 says the same): Night Shade does nothing to Normal types, and Seismic Toss, Sonicboom and Super Fang do nothing to Ghosts. Four of Route 116's six targets are Normal type.
  - The spec's progress ≥ 10% and E-gain rules apply to stage 2 only (v2:638). Stage 1 (v2:634-635) needs only the floor and HP above 50%.
- **Fix:** apply immunity, progress and E-gain to stage 1. All three are calculator-free for exact damage.

## Nits

- **N1. A semi-invulnerable target should be THROW-ONLY, not DEFER.**
  - v2:610 DEFERs, which hands the turn to the parent's unguarded status chooser (`catch.py:57-60`, :186-210).
  - A ball does work against it: VERIFIED at bsc.c:9905-10050 and `battle_scripts_2.s:50-53`.
- **N2. The sleep skips are incomplete.**
  - Uproar blocks sleep (bsc.c:6832, `UproarWakeUpCheck`), and Whismur learns Uproar at L5 and appears on Route 116.
  - Shed Skin is also missing.
  - Soundproof must key on `is_sound_move`, not on names: the data says "Grasswhistle", not "GrassWhistle".
- **N3. Healing moves and items are not modelled.** Rest, Recover, Oran Berry and Leftovers were listed in v1 (r23-25:544). The turn counters bound the cost, but add rows.
- **N4. The v1 question "stop weakening when our active mon is low" (r23-25:567) was dropped without a word.** Record 06:8041 (faints during a catch are accepted) as the reason, or add a row.
- **N5. THROW-ONLY for Explosion (v2:612) gives up sleep,** and a sleeping target cannot explode unless it knows Sleep Talk. This is an optimization, not a safety issue.
- **N6. Observe's later verdicts are counterfactual.** After a hypothetical damage or status turn, HP and status never change, so later `would=` values leave the path ON would take. Step 14's frequency data (v2:686) should count only the first non-throw verdict per battle.
- **N7. Two floor rules are unstated.**
  - How floors combine: the maximum within one turn, the sum across turns.
  - "Total PP ≤ 4 (Struggle)" (v2:628) does not say whose PP.
- **N8. There are three catch-chance implementations.** The new `catch_p`, `dex_catch_expected_throws` (SM:1768-1789), and `U:271-294`, which lacks the certain-catch branch for odds above 254 (bsc.c:10009). Add a row that checks they agree.
- **N9. The "a catch never damages" statements are incomplete and some line numbers are stale.**
  - Missed statements: `tools/story-dev/probe_dexcatch_bail.py:4` and `probe_dex_open_fence.py:8`.
  - Stale citations and their current lines:

    | Cited | Now |
    |---|---|
    | :3875 (shiny) | SM:4093 |
    | :3910 (HM) | SM:4128 |
    | :4020 (counter) | SM:4238 |
    | :4121 (dex/team) | SM:4015 |
    | :1725 | SM:1773 |
    | :1975 | SM:2073 |
- **N10. Hail has no rows** (v2:648-650 cover sand only).
  - INFERRED, from my own species list: every level-up learner of Sandstorm or Hail in Hoenn is immune to it. Sand: Sandshrew L53, Baltoy L31, Nosepass L31, Trapinch L49, and Cacnea L45 through Sand Veil. Hail: Spheal L31 and Snorunt L37 (Ice types); Castform L20 is a gift, not a wild.
  - So W40 guards against a case that does not occur live.
- **N11. The fence's full-HP expected-throws refusal still blocks ordinary hard catches before weaken can act** (SM:2088, `DEX_CATCH_MAX_EXPECTED_THROWS=10` at SM:1700). Record this as the intended scope.

## Checked and holds

- **Balls:** no Substitute or semi-invulnerable test (bsc.c:9905-10050). Catch formula at bsc.c:9987-10028.
- **Sand immunity:** includes Sand Veil and Dig/Dive, read from the live battler (bsc.c:7608-7616). Hail spares Ice types and Dig/Dive (bsc.c:7628-7630).
- **Ghost Curse:** costs max HP / 2 (bsc.c:8477), and the Ghost check uses the user's live type (bs1.s:1483).
- **Exact-damage moves:** they set their damage after `typecalc` (Super Fang takes half HP, minimum 1, at bsc.c:7577-7581), and none of them rolls a crit (bs1.s:809-828, :1195-1204, :1720-1729).
- **Thunder Wave vs Ground and Glare vs Ghost:** blocked by `typecalc` (bs1.s:1013-1014).
- **Called moves:** no Nature Power result damages its user (bsc.c:759-771), so Metronome is the only one that can.
- **Shiny catches:** they bypass the adapter (SM:251-275).
