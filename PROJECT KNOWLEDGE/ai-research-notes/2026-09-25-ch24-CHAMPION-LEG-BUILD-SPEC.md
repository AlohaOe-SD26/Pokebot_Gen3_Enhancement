<!-- PROVENANCE BANNER — read this before the spec. -->
# ⚠ HOW THIS DOCUMENT WAS MADE, AND HOW MUCH TO TRUST IT

**Produced 2026-09-25 by a 13-agent workflow**: six independent recon angles, each then handed to a
**separate adversarial verifier** whose only brief was to check every citation at `file:line` and
mark it CONFIRMED / REFUTED / OVERSTATED / UNVERIFIABLE, then one synthesis pass.

⛔ **IT IS A NOTE, NOT TRUTH** — the same rule every Gemini and Claude agent output carries here.
Verify any load-bearing claim yourself before code depends on it.

‼ **THE VERIFICATION PASS EARNED ITS COST, AND THAT IS THE REASON TO KEEP §0.** It killed **twelve**
recon claims, several of which would have shaped the design wrongly — including one that INVERTED a
core assumption (the production watchdog is *trigger-happy on a winning run*, not *blind*). It also
found the recon carried **systematic citation drift of 4-80 lines**, which is exactly why every
`file:line` in the body was re-derived against the working tree at commit `d202e55c`.
⇒ **§0 "WHAT IS DEAD" is the most valuable section in this file.** Read it first; a reviewer will
check that none of those claims leaked back into the design.

⭐ **EVERYTHING TAGGED ⭐MEASURED COMES FROM ONE TRAJECTORY** — the 2026-09-17 `--driver ch24tailprobe`
run. Per `CLAUDE.md` session-discipline #8 that is a replay, not a replication. Read every ⭐ as
*"measured once"*.

✅ **ALREADY ACTIONED FROM THIS SPEC (2026-09-25), so the next reader does not redo it:**
* **P1 — the classifier case defect: FIXED AND GATED.** `story_mode.py` emits a CAPITAL
  *"End of built content."* while all three log classifiers matched the lowercase needle
  case-sensitively ⇒ the first ever completed run would have been filed as `HANG CONFIRMED`.
  Fixed by casefolding **both** sides (lowercasing only the haystack would have broken **ten**
  other needles), and locked behind new **gate #75** `repro_content_end_classifier.py`, which
  demonstrates the RED→GREEN transition and fault-tests itself.
* **P0 — the three documentation defects: CORRECTED.** M6 marked DONE with its evidence path (it
  was ordering a re-spend of a finished ~50,000-frame drive), "25 opposing Pokémon" → **26**, and
  the "~20,000 frames" header → the measured **13,107-14,575**.

⇒ **THE NEXT ACTION FROM THIS SPEC IS P2** — one instrumented re-run of `Ch24TailProbeMode` that
settles seven questions at once and supplies the second trajectory. See §6.

---

# §Ch24 CHAMPION LEG — BUILD SPEC

**Scope:** ROOM 5 (Wallace) + THE TAIL, as a separate leg with its own grade, per the settled ruling `03-PUNCH-LIST.md:923` (`#24-leg2spec`): *"BUILD ROOMS 1-4 AS THE UNIT, AND BUILD ROOM 5 PLUS ITS TAIL AS A SEPARATE LEG WITH ITS OWN GRADE."* Rooms 1-4 are `fight_one_room` and are **not touched by this spec**.

**Provenance of the citations below.** Every `file:line` in this document was re-derived by `grep`/`sed` in this pass against the working tree at commit `d202e55c`, because the recon that fed it carries a *systematic* citation drift of 4–80 lines in `story_harness.py`'s `Ch24TailProbeMode` region and in `pokemon_league.py`. Where I found the recon's number wrong I have printed the corrected one and said so.

**MEASURED vs INFERRED is separated explicitly throughout.** ⛔ Everything tagged ⭐MEASURED comes from **one trajectory** — the 2026-09-17 `--driver ch24tailprobe` run, `tools/story-dev/evidence/2026-09-17-ch24tailprobe-FULL-TAIL.stdout.txt`. Per CLAUDE.md session-discipline #8 that is a replay, not a replication. Read every ⭐ as "measured once".

---

## 0. WHAT IS DEAD — claims the recon refuted or overstated, which this spec does NOT build on

> ⛔⛔⛔ **REFUTED BY P2 (2026-09-25) — READ THIS BEFORE THE SECTION BELOW.**
> The spec's most emphatic and most-repeated design instruction was that the production
> watchdog is **“trigger-happy on a winning run”**, and that the leg must be engineered against a
> **spurious derail**. **IT WOULD NOT FIRE.** Measured on the instrumented tail drive, under
> production's OWN 5-tuple: max consecutive-identical streak **12,680** against its **18,000**
> threshold — **5,320 frames of margin**, with **0 signature exceptions**
> (`evidence/2026-09-25-ch24tail-P2.stdout.txt`; graded in `2026-09-25-ch24-P2-MEASURED.md`).
> ⇒ **D5 IS CLOSED AND ALL THREE OF ITS OPTIONS ARE DEAD.** Do NOT build watchdog mitigation —
> `context.message` mutation, a per-mode suspension, or a raised threshold — against a threat
> that does not exist.
> ‼ AND A NUANCE WORTH KEEPING: the spec declared the earlier 12,681-frame figure **dead** for
> having been measured under the HARNESS's 6-tuple. Re-measured under production's own tuple it
> is **12,680** — within ONE frame. **The reasoning for distrusting it was sound; the conclusion
> was wrong.** Keep the method, drop the verdict.


A reviewer will check that none of these leaked back in.

| Dead claim | What is actually true | Was it load-bearing? |
|---|---|---|
| "Position reads THROW for thousands of frames on the tail; `_cur` becomes None; the 18,000-frame watchdog is **blind** there." | ⭐MEASURED refutation: the evidence file contains **zero** `<err` strings, and `_tp_safe` (`story_harness.py:19579-19584`) would have emitted one on any exception. Line 536 reads `gs=UNKNOWN where=(16, 11)(7, 5)`; line 539 (post-reset, title screen) reads `gs=TITLE_SCREEN where=(0, 0)(-7, -7)` — **stale garbage, constant, not a throw**. | ⛔⛔ **THIS CELL IS ITSELF REFUTED BY P2 — see the banner at the top of §0.** It read: *“⛔ YES, and it inverts the design. The watchdog is **trigger-happy**, not blind.* The leg must engineer against a *spurious derail on a winning run*, not against a silent hang. |
| "Nobody has measured whether the bot's machinery survives the in-game `SoftReset(RESET_ALL)`." | ⭐MEASURED: frame count **increases** across the reset (`8544521 → 8544533`, evidence :535-537), so `main.py:119`'s `previous > current` never fires; `listeners=14` and the *same* generator object `0x…BCBF8F90` appear on both sides. | YES — frame-denominated budgets stay valid across the reboot; no re-anchoring, no listener rebuild. |
| "Zero production Python handles a soft reset / title screen / CONTINUE." | REFUTED: `modules/modes/util/soft_reset.py:13-45` *is* that state machine (`case GameState.TITLE_SCREEN` :27, `MAIN_MENU` :31, `OVERWORLD` :35), imported by eight production modes. | YES — its **wait loop** (:24-45) is the shape to reuse. ⛔ Its **line 21** `context.emulator.reset()` is an *emulator* reset that would zero the frame counter; never call the function. |
| "Winning sets raw flag 1615, which REFUTES the settled line 'Room 5 has no defeat flag'." | OVERSTATED. The ROM mechanism is confirmed at source (`src/battle_setup.c:1245-1250`, `:984-988`, `:1327-1349`; `flags.h:1343`; `opponents.h:339` ⇒ 0x500+335=1615) but **has never been read on our ROM**, and the punch-list sentence's *flag-GUARD* half is correct. | ⛔ NO — and see §3 S4: `on_battle_ended`'s `BattleOutcome` already gives the same WIN/LOSS answer, ⭐MEASURED (`R battle_outcome = '<BattleOutcome.Won: 1>'`). 1615 is demoted to an optional forensic reading behind a probe. |
| "The production 18,000-frame watchdog sees an unbroken 12,681-frame constant block, leaving 5,319 frames of margin." | OVERSTATED. The 12,681 was measured under the **harness's** 6-tuple; production's is a different 5-tuple (`story_mode.py:3733-3739` — it adds `get_map_data_for_current_position()` and `context.message`, drops the controller name and battle fields). It also compares *emulator* frames to a threshold the code itself calls **mode-driven** frames. | The *number* is dead. The *question* is alive → Probe P2b. |
| "Not pressing at THE END pushes the block to ~19,881 frames." | Inference on an inference — `tDelay` is never printed anywhere in the evidence, so the added cost is unbounded below. | Dead as a number. |
| "Step 5 of `beat_the_trainer_here` is UNREACHABLE in the Champion's room (zero controllable frames)." | Mechanism REFUTED by this project's own measurement: `player_avatar_is_controllable()` **reads True under `lockall`** (`story_harness.py:19491-19492`). Step 5 *runs*, during the cutscene. | The conclusion ("do not port it") survives and is **worse** than stated: `ensure_facing_direction("Up")` (`pokemon_league.py:2430`) would press directions at a locked avatar. |
| "Step 7's live-grid check would return True — worse than a failing check." | `_live_collision_grid` **raises** for any map the avatar is not standing on; step 7 is unreachable anyway because step 6 raises first. | Dead as stated; the step is still deleted, for the reason in §7. |
| "PP is unmeasured anywhere in the tree." | WITHDRAWN. PP is read and acted on: `early_game.py:1152` `lead_has_no_damaging_pp`, `:1200` `_team_is_out_of_pp`, `pokemon_league.py:1880` `heal_on_lead_pp=True`, and `#24-ppscope` (`03-PUNCH-LIST.md:632`) measured it over 264 battles. | The narrow true claim survives: **PP is not a term in `party_is_gauntlet_ready` and is not in §Ch24 gauntlet telemetry.** |
| "There is no production completion marker for §Ch24." | FALSE. Two exist: `chapters.py:288` `flag("SYS_GAME_CLEAR")` (the READOUT) and `victory_road.py:3308` `CH24_GAME_CLEAR_FLAG = "IS_CHAMPION"` (already used as a ch23 disjunct at `:3364`). | YES — reuse `CH24_GAME_CLEAR_FLAG`; do not reinvent it. The true gap is *no §Ch24 completion GATE dispatched from `_play`*. |
| "`ch24_chapter_done() = IS_CHAMPION` was settled-and-rejected at `06-DECISIONS-LOG.md:6118`." | That entry is about **§Ch23** and rejects `SYS_GAME_CLEAR` *in favour of* `IS_CHAMPION`. The §Ch24 rejection lives in the punch list (`:944`), not the decisions log. | No — but cite the right file. |
| "The only PP restoration reachable inside the League is a whiteout." | There is a **Nurse at League 1F (3,2)**, and `03-PUNCH-LIST.md:943` already says so. The claim is true only of the **sealed zone** (HALL5 onward). | No, and per rule 11 this is already-known, not a new finding. |
| "The room 5 tail is ~46,000 frames of A-presses." | ⭐MEASURED refutation: ~29,959–30,908 of those frames are the **battle**, during which the story generator is starved (~60 iterations, ~0.2%) and its press loop does not tick. Press-gated body ≈ **1,648 intro + 19,914 tail**. | YES — a press loop budgeted on 46,000 frames is budgeting frames it will never see. |
| "The champion leg must hand back to a restock-and-retry path on a loss." | That path **does not exist**: `#24-restockleg` (`03-PUNCH-LIST.md:92`) is UNBUILT and blocked on money, not design. | YES — the loss posture is *terminal for this run* (§8-D4). |

---

## 1. VERDICT

**The champion leg is buildable now as a harness-driven production function, and it is blocked on exactly one instrumented drive before it can be graded.** Every structural question — where it starts, what it presses, what bounds it, what it must refuse, what it must never reuse — is settled by source reads and by the one measured trajectory, and the shape that survives is not a fight at all but a **bounded observe-and-press tail driver** with a single irreversible act. What is *not* settled is whether its acceptance predicate needs five conjuncts or one (the `OVERWORLD`-during-the-tail question), and whether the production watchdog derails a *winning* run — ✅ **ANSWERED BY P2: IT DOES NOT** (12,680 vs 18,000, 0 exceptions), so this clause is settled, not open — and both are reads, not experiments, so one instrumented re-run of the existing probe settles them together and simultaneously supplies the second trajectory the project's own rules require. ⛔ Wiring into `_play` is **out of scope for this leg** and must not be attempted in the same commit: it carries five independent co-landing requirements (§8-D1) including a live classifier defect that would file the first ever win as a hang.

---

## 2. THE HARD CONSTRAINTS — the checklist a reviewer checks the design against

**HC1 — The leg issues ZERO navigation and ZERO direction input inside the Champion's room.**
The room's `OnFrame` (`data/maps/EverGrandeCity_ChampionsRoom/scripts.inc:19-21`, gated on `VAR_TEMP_1, 0`) runs `EventScript_EnterRoom`, whose FIRST opcode is `lockall` (`:24`) and which then walks the player itself (`Common_Movement_WalkUp4` + two `walk_up`, `:25-27`, `:33-36`) from (6,12) to (6,6), facing north via `OnWarp`'s `turnobject … DIR_NORTH` (`:15-17`). ⭐MEASURED: evidence `:22,23,24,26` — f60 (6,12) → f120 (6,8) → f180 (6,7) → f240 (6,6), with the probe issuing **only** `A`. *(Recon inaccuracy corrected: `script` reads **False** at f60 and only goes True from f120.)*

**HC2 — The only bot act between HALL4 (5,3) and the Hall of Fame is 8 frames of `Up` plus an A-cadence.**
Follows from HC1. The 8 frames (not 1) are required because a single-frame press does not complete a tile step — the ML-9 lesson recorded at `early_game.py:429-431`. Precedent: `story_harness.py:19439-19449`.

**HC3 — `player_avatar_is_controllable()` is NOT a gate anywhere in this leg.**
It reads **True under `lockall`** (`story_harness.py:19491-19492`, written after that exact mistake cost the probe its first run: `evidence/2026-09-17-ch24tailprobe-v1-STOPPED-EARLY.stdout.txt:169` `R end_where = ((16, 4), (6, 6))`). Every settle keys on the script context, the CB2 symbol, the map id, or a mode callback. *(Honest scope: "it is True for the entire room" is an INFERENCE — the only datum is one post-battle frame; `player.py:263-284` additionally requires `heldMovementActive` and forbids `frozen`/`ForcedMove`.)*

**HC4 — `wait_until_truly_controllable()` may be called but its return proves nothing.**
`early_game.py:1257-1280`: it presses nothing and **returns silently on timeout** with no success signal — `03-PUNCH-LIST.md:90` (`#24-e4postbattlestall`) records that as "leg 1's first blocker" across 262 call sites. ⇒ call it once at the very end, then **re-assert** the settle conjuncts after it returns.

**HC5 — The grade is never built on the four `DEFEATED_ELITE_4_*` flags or `VAR_ELITE_4_STATE`.**
`data/event_scripts.s:628-634` `ResetEliteFour` clears all four and zeroes the var; `data/scripts/hall_of_fame.inc:7` calls it **on the winning path**. ⭐MEASURED: evidence `:296` `e4state=4 champ=False` → `:297` `e4state=0 champ=True`, one 60-frame sample apart, still `sym='CB2_OVERWORLD'`. ⇒ those terms read **FALSE ON SUCCESS**.

**HC6 — No flag NAME may be passed for Wallace, to any helper.**
`memory.py:336-338` `if flag_name not in _event_flags: return False` — silently. The table has no trainer-flag names in the 1280–2143 range. `beat_the_trainer_here` (`pokemon_league.py:2355-2568`) reads the flag raw at `:2487` and `:2528` and has **no** `_event_flags` membership guard; that guard lives only in its callers (`:2618` in `fight_one_room`, `:2110` in `prepare_and_open_the_league`). ⇒ a reused helper reports "this is what a LOSS looks like" (`:2532-2534`) on a perfect win.

**HC7 — Every reader in the post-battle half is raise-safe.**
`_here_tile()` (`sootopolis.py:852-866`, shimmed via `victory_road.py` to `pokemon_league.py:79`) **raises** on an unreadable position, and `beat_the_trainer_here` calls it unwrapped at `:2403`, `:2423`, `:2429`, `:2530`. The `_tp_*` family (`story_harness.py:19547-19690`: `_tp_script_inactive` :19547, `_tp_left_champions_room` :19559, `_tp_frame` :19572, `_tp_safe` :19579, `_tp_symbol` :19587, `_tp_gamestate_name` :19596, `_tp_controllable` :19606, `_tp_flag` :19615, `_tp_flash_flag` :19624, `_tp_snapshot` :19640) is the pattern and must be promoted, not reinvented.

**HC8 — `''` is a first-class symbol value, not an error.**
⭐MEASURED: evidence `:535-537`, `CB2_CREDITS -> '' at frame 8544521` then `'' -> CB2_INITCOPYRIGHTSCREENAFTERBOOTUP at frame 8544533 (+12)`. Twelve frames wide — a per-frame loop sees it; a 60-frame sampler may not.

**HC9 — The button is `A`, every frame, never held, never a direction, never SELECT.**
`story_harness.py:19321-19323`: A is the only button satisfying all three gate families — `JOY_NEW(A|B)` text prompts, the Hall-of-Fame screen's `JOY_NEW(A_BUTTON)`-**only** exit, and the title screen's `JOY_NEW(A|START)`. The wrapper XOR-alternates ⇒ an edge every 2 frames. The room unit's dismisser presses **B** (`pokemon_league.py:2668-2675`, rationale at `:2649-2651`), which cannot exit the Hall-of-Fame screen. Directions are forbidden after the one `Up` (title-menu cursor, T16); SELECT is forbidden always (`CLEAR_SAVE_BUTTON_COMBO`, T19) — both at `story_harness.py:19328-19336`.

**HC10 — The leg stops pressing the instant the avatar is genuinely usable after the reboot.**
`story_harness.py:19505-19507`: "A-mash is only safe under `lockall`; here it would interact with the room." This boundary is the leg's most dangerous single line.

**HC11 — Nothing is bounded by a press count or a stop count.**
`R presses = 19056` over 49,873 frames — duty-cycle ticks, not prompts. The stop count is dex-state dependent (`data/scripts/prof_birch.inc:70` `goto_if_eq VAR_0x800A, 0, Common_EventScript_NopReturn`) and the tree disputes it three ways: `~10` (recon), `~11` (`DESIGN-REFUTATION`/O1), `~13-15` (`03-PUNCH-LIST.md:940`, O9). One of them (`prof_birch.inc:53-58` `ShowRatingMessage`) is a **raw `waitbuttonpress`** the shipped KI-93 dismisser is structurally blind to. ⇒ frames, with a no-progress escape.

**HC12 — The trainer's own defeat speech is NOT a stop on this path.**
`EventScript_DoNoIntroTrainerBattle` ends in `gotopostbattlescript` (`data/scripts/trainer_battle.inc:48`), returning to `ChampionsRoom/scripts.inc:42`; it never reaches `gotobeatenscript`. No trainer-defeat script appears anywhere in the evidence. Stated so nobody re-derives it while sizing the chain.

**HC13 — The leg must refuse before the (5,2) step, because there is no second look.**
`EverGrandeCity_Hall4/map.json` warp[1] `{x:5,y:2 → CHAMPIONS_ROOM, dest_warp_id:0}`; `allow_escaping: false` on both maps; no defeated-flag guard anywhere (`trainerbattle_no_intro` → `EventScript_DoNoIntroTrainerBattle`, the one variant with no `GetTrainerFlag` check — `trainer_battle.inc:44-48` vs `:9-17`). ⇒ **every entry is another full Wallace battle.** Precedent for concentrating all checks above the line: `pokemon_league.py:2879`.

**HC14 — After the step, "we are still on HALL4" is NOT evidence of failure.**
⭐MEASURED: evidence `:9-13` — `after the step: at=((16, 8), (5, 2))`, then `f0 … where=(16, 8)(5, 2) script=False`, then the map change begins **32 frames later** and `CB2_OVERWORLD` on `(16,4)(6,12)` arrives at +43 (`:19-20`).

**HC15 — The end MAP is gender-dependent; the end TILE is not.**
`src/data/heal_locations.json`: both `…BRENDANS_HOUSE_2F` and `…MAYS_HOUSE_2F` are `x:4, y:2`. `map_data.py:854 = (1,1)`, `:856 = (1,3)`. ⇒ assert tile `(4,2)` unconditionally; accept either map. *(Note the two mechanisms differ: `setrespawn` sets the whiteout respawn, `SetContinueGameWarpToHealLocation` (`post_battle_event_funcs.c:38-41`) sets the CONTINUE warp. The leg depends on the second.)*

**HC16 — "Not on map X" is a weak test against garbage and may only be a backstop.**
⭐MEASURED: the post-reset garbage read is `where=(0, 0)(-7, -7)`, and `map_data.py:794 PETALBURG_CITY = (0, 0)` resolves to a real map. So `_tp_left_champions_room()` returns True throughout the reboot window.

**HC17 — A 9-frame MIXED read exists: right map, stale tile.**
⭐MEASURED: evidence `:564` `CB2_CONTINUESAVEDGAME -> CB2_LOADMAP at 8544938 / gs=CHANGE_MAP where=(1, 1)(7, 5)`; correct tile only at `:570` (`8544947`). ⇒ never assert "we are home" on map identity alone; read map and tile on the same frame.

**HC18 — `len(get_party()) > 0` is the only positive proof EWRAM reloaded.**
⭐MEASURED and change-detected (not sampled): `:534` `f49485: PARTY CHANGE […] -> []` and `:544` `f49692: [] -> […]` = 207 frames empty. ⛔ And the consequence the recon got backwards: `get_party()` returns `[]`, so an **unguarded `party[0]` raises IndexError**; only guarded readers return zeros (`story_mode.py:2038-2055` is guarded — that is why it returns `(0,0,0)`).

**HC19 — The leg holds control through a battle it does not fight.**
The `BattleListener` sits above the story generator; ⭐MEASURED ~60 generator iterations across 30,908 battle frames (~0.2%). ⇒ (a) anything to be observed during the fight must be latched in a **mode callback** (`on_battle_started` / `on_battle_ended` — `story_harness.py:19380`, `:19388`, "⭐⭐ THE ONLY GUARANTEED LATCH CHANNEL"); (b) `handles_battle_faults = True` is required (`battle_fault.py:41` gates the escape on it) and `take_pending_fault()` must be called on every frame the leg holds control. ✅ Production `StoryMode` already has all four hooks — `handles_battle_faults` `story_mode.py:1738`, `on_battle_ended` `:1984`, `on_whiteout` `:2011`, `on_battle_started` `:3318`, `take_pending_fault()` `:3650`. What is **missing** is a §Ch24-scoped latch: `on_battle_ended` (`:1984`) handles only the `Lost` branch and stores neither the outcome nor the frame.

**HC20 — The last heal opportunity is HALL4 (5,3), and the heal must never raise there.**
`heal_party_from_bag` (`pokemon_league.py:250`) has no map or position precondition. `Ch24Hall4Mode` heals in **Drake's room** (`story_harness.py:19165-19192`) under "there is no heal after this one" (`:19166-19168`) — outcome-true but literally imprecise; (5,3) is 31 tiles later. Nothing can damage the party in between: `EverGrandeCity_Hall4/map.json` has `"object_events": []`, `"coord_events": []`, no wild table (`story_harness.py:19062-19063`), and a graded-ready party cannot be poisoned (`overworld_items.py:247` requires `m.status is None`). ⛔ The heal **raises** on a no-op item use (`pokemon_league.py:317-325`); both existing callers wrap it (`:2716-2719` under "⛔⛔ THIS NEVER RAISES. The zone is sealed behind us" `:2692-2694`; `story_harness.py:19176-19181`). Copy the wrap, not the call.

**HC21 — `heal_ready` must be a top-level grade conjunct, and it is NOT the same thing as the R-HEALED reading.**
⭐ Verified this pass: on an **empty plan** `heal_party_from_bag` sets `heal_ready` at `pokemon_league.py:297` and **returns at :298 — before `readings.add("R-HEALED")` at :336**. So on a fully-healed party the reading is never taken while `heal_ready` is True. The precedent for the conjunct: `:2707-2719` records a run that read `heal_ready=False, missing=[], failure=None` and **still PASSED** until the conjunct was added.

**HC22 — The leg must not raise anywhere in the 426-frame post-reset window.**
`story_mode.py:4033` `at_title = get_game_state() is GameState.TITLE_SCREEN or not game_has_started()`; `:4055` `if at_title:` → `:4059` `yield from run_intro(...)`; re-entry via `:3840 continue`. `game_has_started()` reads symbols zeroed by `RESET_ALL`. ⇒ a raise in that window starts a **NEW GAME over a freshly-autosaved cleared save**. *(Honest: this is trap **T17**, already named at `ai-research-notes/2026-09-17-ch24-legB-BUILD-SPEC.md:160` and hard-aborted in the probe at `story_harness.py:19468-19471`. What is NEW is the `_play`-re-entry path.)*

**HC23 — The END-OF-CONTENT classifiers are ALREADY BROKEN BY CASE, today.**
⭐MEASURED by grep this pass: `story_mode.py:5335` prints **`End of built content.`** (capital E); `compare_runs.py:102`, `endless_runs.py:60` and `story_harness.py:25042` all match the lowercase needle `end of built content` with a case-sensitive `in` (`compare_runs.py:143-145`; **no `.lower()` exists in either tool**). ⇒ the wedge suppressor is inert and `endless_runs.py` can never classify `content-end`. Advice of the form "keep the substring" preserves the bug.

**HC24 — The gauntlet is 26 opposing Pokémon, not 25, and the longest fight is last.**
`src/data/trainer_parties.h:4414-4457` `sParty_Wallace[]` has **six** (Wailord 57, Tentacruel 55, Ludicolo 56, Whiscash 56, Gyarados 56, **Milotic 58 holding a Sitrus Berry**, with Recover/Toxic); the other four parties are five each. `03-PUNCH-LIST.md:929` (O3) says 25.

---

## 3. THE LEG'S SHAPE

### 3.0 Function boundary — TWO production generators, no self-skip

⛔ The recon proposed one generator with a DRAKE'S-ROOM premise whose first four steps "self-skip when already on HALL4 (5,3)". **Reject it:** a self-skip is a branch whose skipped half cannot fail, i.e. a vacuity hazard in the premise itself — the exact shape `pokemon_league.py:2549-2551` already warns about for reloaded fixtures.

Build instead:

* **`cross_to_the_champions_door(report)`** — promotion of `Ch24Hall4Mode`'s non-test parts. Premise: `_on_map(DRAKES_ROOM)` ∧ `DEFEATED_ELITE_4_DRAKE` ∧ `not IS_CHAMPION`. Body: dismiss → `_pass_through_door((6,2), DRAKE)` → `navigate_to(HALL4, (5,3))` → assert-both-halves. Grade: on HALL4 ∧ tile (5,3). **It does not heal** (see 3.1 S1). Composes with `fight_one_room`'s documented end state (`pokemon_league.py:2574-2578`).
* **`fight_the_champion(report)`** — this spec. Premise: HALL4 (5,3). Drivable alone from `post_hall4_door.ss1`.

Every step below names what it reuses. Blanket rule: **reuse `_take` (:64), `_where` (:73), `_on_map` (:85), `_budgeted` (:97), `heal_party_from_bag` (:250), `party_is_gauntlet_ready` (`overworld_items.py:240`)**. `_here_tile` (:79) is reusable **only above the door**.

---

### S1 — PREMISE + THE LAST HEAL, at HALL4 (5,3)

**Does:** reads the premise, records everything that will never be readable again, heals, and refuses if anything is wrong. Everything that matters happens here.

**Premise conjuncts (all four, ANDed):**
| # | Conjunct | Evidence it is non-vacuous |
|---|---|---|
| P-a | `_on_map(EVER_GRANDE_CITY_HALL4)` ∧ `_here_tile() == (5,3)` | `Ch24Hall4Mode` stops here deliberately (`story_harness.py:19040-19042`); the (5,2) control ends `is_warp=True` already inside the Champion's room (`:19000-19001`) |
| P-b | `get_event_flag("IS_CHAMPION") is False` | Monotone, cleared nowhere (`victory_road.py:3303-3307`); ⭐MEASURED True at the end |
| P-c | `int(get_event_var("ELITE_4_STATE")) == 4` | ⭐MEASURED 4 on every pre-HoF sample and **0** from evidence `:297` |
| P-d | `get_event_flag("DEFEATED_ELITE_4_DRAKE") is True` | Cleared on the winning path by `ResetEliteFour` |

⭐ **Why this set and not flag 1615.** F11 of the recon could not resolve the tension "the re-entry guard and the premise conjunct are the same never-cleared bit, so the guard makes the leg un-rerunnable." It dissolves: the re-entry guard is **P-b (`IS_CHAMPION`)**, which is monotone, name-readable and already a production constant. 1615 is never needed for it.

**Readings taken here:** `C-PREMISE`; plus, recorded and never asserted — per-member HP fraction and status, per-move PP (see §6 P2e), bag contents, `get_event_var("LAST_TALKED")` (§6 P2d), `battles == 0`.

**Heal:** `heal_party_from_bag(heal_report)` wrapped in a bare `except` that RECORDS (HC20). `C-HEALED` is taken unconditionally; **`heal_ready is True` is a separate grade conjunct** (HC21).

**Bounds:** `_budgeted(..., 200_000)` for the heal, matching `pokemon_league.py:2712-2713`. A *frame* bound, because the bag menu's cost is input-cadence-dependent and unmeasured here.

**Refuses when:** any premise conjunct is False (naming which), or `heal_ready is not True`. ⇒ **refusal happens above the irreversible line, where refusal is free.**

**Reuses:** `_on_map`, `_here_tile`, `heal_party_from_bag`, `party_is_gauntlet_ready`, `_take`, `_budgeted`.
**New:** the four-conjunct premise block; the PP/HP/LAST_TALKED telemetry dump.

---

### S2 — THE CROSSING: eight frames of `Up`

**Does:** `take_pending_fault(); context.emulator.press_button("Up"); yield` × 8 (shape: `story_harness.py:19439-19449`). Then observe until the map reads `CHAMPIONS_ROOM`.

**Bounds:** **600 frames** to observe the map change. Frame-denominated because the transition is a `CB2_LOADMAP` sequence with no input, and ⭐MEASURED cost is **43 frames** (evidence `:10` → `:19-20`), of which the first 32 still read HALL4 (5,2) (HC14). 600 ≈ 14×.

**Reading:** `C-CROSSED` when `_where()` map == `(16,4)`. ⛔ Not "we left HALL4" (HC14), and not "we stepped on the warp".

**Refuses when:** 600 frames elapse with the map still HALL4 ⇒ the press did not take. (This is the only refusal after S1 that is recoverable — nothing has happened yet.)

**Reuses:** nothing but `_where`. ⛔ **`navigate_to`, `_pass_through_door`, `_goto_warp` and `_navigate_riding_out` are all forbidden here** — they make the warp a *destination*, which is trap T10 and is exactly what `Ch24Hall4Mode`'s tripwire (`story_harness.py:19090-19093`) exists to prevent one tile earlier.

---

### S3 — THE APPROACH AND THE INTRO: press A, observe, do not act

**Does:** press `A` every frame. The game walks the avatar (6,12)→(6,6) and prints `Text_IntroSpeech` as `MSGBOX_DEFAULT` (`ChampionsRoom/scripts.inc:40`), which halts on `waitbuttonpress`. The leg's only job is to supply edges.

**Bounds:** **6,000 frames** from `C-CROSSED` to `on_battle_started`. ⭐MEASURED cost 1,648 frames (evidence `:19` → `:86`, `8495117 → 8496765`). ~3.6×, sized generously because the prompt count is dex-independent here but unmeasured as a count and must not be bounded as one (HC11).

**Reading:** `C-ENGAGED`, taken **from the `on_battle_started` mode callback**, never from our press. `pokemon_league.py:2376` states the rule: *"A room leg must NEVER assume its own press caused the battle"* — and here it demonstrably did not: the fight is started by `trainerbattle_no_intro TRAINER_WALLACE` inside the map script.

**Refuses when:** the bound expires with no `on_battle_started`. ⛔ Also aborts immediately on `on_whiteout` (impossible here, but the channel is always live).

**Reuses:** the mode-callback latch pattern. **New:** the §Ch24 latch fields on the production `StoryMode` (`battle_started_frame`, `battle_ended_frame`, `battle_outcome`, `battles`) — `story_mode.py:1984`'s `on_battle_ended` currently stores none of them.

⛔ **Deleted, not ported:** locate-the-trainer (`pokemon_league.py:2404-2419`), stand-beside (`:2421-2428`), face (`:2430`), and the three-signal engage discriminator (`:2461-2506`). The room has **three** `object_events` — Wallace (6,5), RIVAL (6,12) and BIRCH (6,12) — so the "exactly ONE object_event" safety comment at `:2407-2413` has its own escape clause fire. *(Precision the recon got wrong in the other direction: the two extras are `addobject`ed only at `scripts.inc:56` and `:95`, deep in the POST-battle chain, and `new_game.inc:227-228` hides them at load — so at engage time there is exactly one visible object. The step is deleted because it is **inapplicable**, not because it would mis-pick.)* And the room is **13×13** (`layouts.json`, vs 13×14 for the E4 rooms), so any ported geometry reading at y=13 is out of bounds and **passes by construction** — `_live_wall_tiles` defaults a missing key to wall (`sootopolis.py:994-997`) and `MapLocation._metatile_attributes` returns collision 3 off-map (`map.py:766-777`).

---

### S4 — THE FIGHT: hold control, press, observe nothing

**Does:** keep pressing `A` and calling `take_pending_fault()` every frame it gets one. It gets ~0.2% of them.

**Bounds:** **150,000 frames** from `on_battle_started` to `on_battle_ended`. ⭐MEASURED 30,908 (CB2 window `8496774 → 8527682`) / 29,959 (BattleListener latch). ~5×, because a fight's length is the most variable quantity in the leg and a too-tight bound would kill a winning run. ⛔ Budget on the **CB2 window (30,908)**, not the latch (29,959) — the latch is 883 frames early.

**Readings:** `C-WON` when `on_battle_ended` latches `BattleOutcome.Won`. ⭐MEASURED: `R battle_outcome = '<BattleOutcome.Won: 1>'`. ⭐ **This is the leg's immediate, causal, already-measured WIN/LOSS discriminator** — it needs no flag, no name, no probe, and it is available on the frame the battle ends. *(Optional, behind §6 P2c: `get_event_flag_by_number(1615)` read in the same callback, recorded only.)*

**Refuses when:** `on_whiteout` fires (`story_harness.py:19370-19378`: *"THIS IS A RESULT, NOT AN ERROR … the fixture is spent"*) ⇒ **terminal for this run**, recorded as a LOSS with its own outcome string, never retried, never handed to a restock path that does not exist (§8-D4). Or the 150,000-frame bound expires.

**Reuses:** `handles_battle_faults` + `take_pending_fault()` (already in production, `story_mode.py:1738`, `:3650`), `on_whiteout` (`:2011`).
**New:** nothing structural.

---

### S5 — THE POST-BATTLE CHAIN AND THE WARP

**Does:** keeps pressing `A`. The game runs ~9–10 button-gated stops interleaved with `applywaitmovement`/`delay`/`waitfieldeffect` blocks no button advances, spawns the rival and Birch, runs `ProfBirch_EventScript_RatePokedex` (containing a raw `waitbuttonpress`, `prof_birch.inc:53-58`, and a dex-state branch at `:70`), opens the door metatiles (`ChampionsRoom/scripts.inc:47-48`), and ends with `warp MAP_EVER_GRANDE_CITY_HALL_OF_FAME, 7, 16` (`:123`).

**Bounds:** **10,000 frames** from `on_battle_ended` to the map reading `HALL_OF_FAME`. ⭐MEASURED 2,681 + 9 = 2,690 (evidence `8527682 → 8530372`). ~3.7×. ⛔ Frames and not presses, and ⛔ **not gated on `get_text_printer(0).state == WaitForButton`** — that gate is blind to `waitbuttonpress` (`03-PUNCH-LIST.md:940`, O9) and the count moves with dex state.

**Reading:** `C-INHOF` when the map reads `(16,11)`. ⭐ Verified this pass: the first Hall-of-Fame frame reads `where=(16,11)(7,5)` — **the scripted warp's literal coordinates**, which the warp *event* at (6,2) could not have produced. That is the proof that the bot never walked through the door.

**Refuses when:** the bound expires. ⛔ **Does NOT assert "the exit door is open"** — vacuous (HC-§7).

---

### S6 — THE HALL OF FAME, THE SAVE, THE CREDITS, THE REBOOT

**Does:** keeps pressing `A` through: the HoF map cutscene → `SetGameClearFlags` (`hall_of_fame.inc:1-7`: `SetChampionSaveWarp`, `setflag FLAG_IS_CHAMPION`, `call ResetEliteFour`) → `special GameClear` (which sets `FLAG_SYS_GAME_CLEAR` at `post_battle_event_funcs.c:30` and swaps the main callback at `:84`) → the forced save → the HoF screen (`Task_Hof_ExitOnKeyPressed` blocks on `JOY_NEW(A_BUTTON)` **forever**) → `THE END`'s 7,200-frame `tDelay` (cut by any new key, `credits.c:665`, `:674`) → `SoftReset(RESET_ALL)` (`credits.c:694-698`) → title → main menu → CONTINUE.

⛔ **The credits cannot be fast-forwarded on a first clear, by construction**: `credits.c:349-357` gates the B-hold speed-up on `gHasHallOfFameRecords`, which `post_battle_event_funcs.c:23-30` sets FALSE exactly when this is the first clear. ⭐MEASURED: the probe A-mashed throughout and CREDITS still cost 10,353 frames. *(Note this CONFIRMS `03-PUNCH-LIST.md:944`'s decomp read rather than discovering it — the punch list got it right first.)*

**Bounds:** **40,000 frames** from `C-INHOF` to the reset marker. ⭐MEASURED 1,468+30+2,292+6+10,353+12 = 14,161. ~2.8×. ⛔ This budget must NOT be tightened toward the measured value: `gHasHallOfFameRecords` makes a SECOND clear materially shorter and a first clear is the only path this leg takes, so there is no slack to reclaim, only risk.

**Readings:**
* `C-CLEARED` when `IS_CHAMPION ∧ SYS_GAME_CLEAR` both read True.
* `C-REBOOTED` when `len(get_party()) == 0` is seen at least once. ⭐ Non-vacuous by construction: 207 frames wide, change-detected in the evidence, and unreachable at any earlier point in the leg. The `''` symbol (12 frames) is recorded as corroboration, not required (HC8).
* ⛔ **NOT graded:** the three-term acceptance window the recon found (`IS_CHAMPION=True ∧ SYS_GAME_CLEAR=False ∧ map=(16,11) ∧ CB2_OVERWORLD`, evidence `:296-301`). It is real but only ~60–180 frames wide and bracketed by a 60-frame sampler; a leg that grades on it takes the reading *sometimes*, which is a nondeterministic grade — worse than no grade. Record it if the per-frame loop happens to see it.

**Refuses when:** the bound expires, **or** `gs == "NAMING_SCREEN"` / `sym == "CB2_NAMINGSCREEN"` ⇒ **hard abort, stop pressing immediately** (`story_harness.py:19468-19471`: the reboot went into NEW GAME; pressing on would overwrite a save).

**Reuses:** the state-gated `TITLE_SCREEN`/`MAIN_MENU` shape of `soft_reset.py:24-45`. ⛔ **Never the function** (`:21` is `emulator.reset()`).

---

### S7 — THE SETTLE, THE ONLY PLACE THE LEG MAY RETURN FROM

**Does:** stops pressing the instant all five conjuncts hold, then calls `wait_until_truly_controllable()` **and re-asserts them**.

**The five-conjunct stop — copied EXACTLY from `story_harness.py:19502-19504`** (the recon's `:19255-19274` is `Ch24Hall4Mode`'s capture block; the real lines are these):

```
gs == "OVERWORLD"
  and _tp_controllable() is True
  and self.battle_ended_frame is not None
  and _script_idle is True          # not get_global_script_context().is_active
  and _left_champ is True           # map != CHAMPIONS_ROOM
```

Plus, for this leg, two more forced by the endgame measurement:
```
  and len(get_party()) > 0          # the only positive proof EWRAM reloaded (HC18)
  and map != EVER_GRANDE_CITY_HALL_OF_FAME   # the 206-frame post-reload false-pass window
```

⭐ Why `_script_idle` is the term doing the work: the global script context reads **ACTIVE for 12,651 frames** across the HoF screen and the entire credits roll, because `releaseall` sits *after* `special GameClear`, which swaps the main callback before the script runner can reach it (`EverGrandeCity_HallOfFame/scripts.inc:51-56`; `post_battle_event_funcs.c:84`). It therefore covers the exact `lockall` window controllability does not. ⛔ Conversely, any helper that *waits* for script idle would block for those 12,651 frames.

**Bounds:** 3,000 frames after `C-REBOOTED` to reach the settle. ⭐MEASURED 426 (`8544521 → 8544947`).

**Readings:** `C-HOME` (the seven conjuncts, plus tile `(4,2)` and map ∈ {`(1,1)`,`(1,3)`}, HC15/HC17) and `C-USABLE` (the same conjuncts re-read after `wait_until_truly_controllable()` returns, HC4).

⭐ Note `player.py:279-282` debounces `Task_ExitDoor` and `sub_8080B9C` — and **not** `Task_ExitNonDoor`, which is precisely the task present on the first post-CONTINUE `CB2_OVERWORLD` frame (evidence `:570`). That is why the first True is untrustworthy and why `C-USABLE` must be a second, later reading.

**Refuses when:** the bound expires, or `C-USABLE`'s re-assertion fails.

⛔ **Returns immediately after `C-USABLE`. It does not navigate, does not go downstairs, does not press another button.** `hall_of_fame.inc:20-22, :43-47` arms the S.S. Ticket / Dad scene one floor below (`clearflag FLAG_HIDE_PLAYERS_HOUSE_DAD`, `VAR_LITTLEROOT_HOUSES_STATE_* = 3`) — and the bedroom itself is quiet *because* `:22` sets the rival-bedroom hide flag (⭐MEASURED: evidence `:571` `scripts=[]`). Quiet upstairs, armed downstairs, by mechanism.

---

### 3.8 The full frame ledger the budgets are derived from

> ⚠⚠ **CORRECTED 2026-09-25 — THE CAPTION SAID “⭐MEASURED, once, sums exactly” AND THAT NOW
> OVERSTATES IT.** A second trajectory (P2) reproduced **every non-battle stage FRAME-FOR-FRAME**
> — 43, 1648, 9, 9, 2681, 1468, 30, 2292, 6, 10353, 12, 414 — which is a strong determinism
> result for the tail's scripted portion. **But THE FIGHT ITSELF VARIED: 30,908 → 34,795 frames,
> a 12.6 % swing from the SAME fixture and party**, purely from battle RNG.
> ⇒ the S4 bound of 150,000 still has ~4.3× margin and is fine; what is NOT fixed is the TOTAL.
> **Read the non-battle rows as deterministic and the fight row as a sample of one distribution.**


| Stage | Frames | Bound in this spec |
|---|---:|---:|
| step (5,2) → `CB2_OVERWORLD` in room | 43 | 600 |
| scripted approach + intro speech | 1,648 | 6,000 |
| `CB2_INITBATTLE` | 9 | — |
| the fight (`CB2_HANDLESTARTBATTLE`) | 30,908 | 150,000 |
| post-battle chain | 2,681 | 10,000 |
| scripted warp | 9 | — |
| HoF map cutscene | 1,468 | ⎱ |
| `CB2_DOHALLOFFAMESCREEN` | 30 | ⎰ |
| HoF screen | 2,292 | ⎱ 40,000 |
| `STARTCREDITSSEQUENCE` | 6 | ⎰ |
| credits | 10,353 | ⎰ |
| `''` (the reset) | 12 | ⎰ |
| boot → CONTINUE → `CB2_OVERWORLD` | 414 | 3,000 |
| **TOTAL** | **49,873** | **~210,000** |

Driver budget: `--frames ≥ 260_000` (the probe's `BUDGET` at `story_harness.py:19363`), and never the 30,000 an earlier spec estimated — `03-PUNCH-LIST.md:875` already says *"budget a leg-B driver at `--frames ≥ 120000`"*.

---

## 4. THE GRADE

```python
CHAMPION_READINGS = (
    "C-PREMISE",   # HALL4 (5,3), IS_CHAMPION False, ELITE_4_STATE == 4, DRAKE flag set
    "C-HEALED",    # the last bag heal ran (taken UNCONDITIONALLY; see heal_ready below)
    "C-CROSSED",   # the map became CHAMPIONS_ROOM after the one Up
    "C-ENGAGED",   # on_battle_started fired — NOT our press
    "C-WON",       # on_battle_ended latched BattleOutcome.Won
    "C-INHOF",     # the map became HALL_OF_FAME (via the scripted warp, at (7,16))
    "C-CLEARED",   # IS_CHAMPION and SYS_GAME_CLEAR both True
    "C-REBOOTED",  # an empty party was observed — EWRAM was wiped and reloaded
    "C-HOME",      # the seven-conjunct settle, tile (4,2), map in {(1,1),(1,3)}
    "C-USABLE",    # all of C-HOME re-asserted AFTER wait_until_truly_controllable()
)
```
⛔ Exported under the same contract as `ROOM_READINGS` (`pokemon_league.py:2324`): *"THE DRIVER IMPORTS THIS — never a private copy."*

**PASS ⟺ all ten readings taken AND `heal_ready is True` AND `whiteouts == 0` AND `battles == 1`.**

### Why each is non-vacuous

| Reading | Could it be satisfied without the leg working? | No, because |
|---|---|---|
| `C-PREMISE` | on a reloaded fixture? | It is a *refusal*, not an achievement — and §5-A5 shows it flips on the leg's own output |
| `C-HEALED` | always taken | ⇒ **it is not the conjunct.** `heal_ready` is, and §5-A4 arms it |
| `C-CROSSED` | by reloading a fixture already in the room | No such fixture exists, and `C-PREMISE` pins us on HALL4 one step earlier in the same run |
| `C-ENGAGED` | by our press | It comes from `on_battle_started`, and the fight is started by the map script — we could not have caused it |
| `C-WON` | by a battle merely *ending* | `BattleOutcome` distinguishes Won from Lost; `on_whiteout` is an independent second channel |
| `C-INHOF` | by walking through a door | The door is never walked; the arrival tile `(7,16)` is the scripted `warp`'s literal argument |
| `C-CLEARED` | by a stale flag | Both flags read **False** at `C-PREMISE` in the same run (⭐MEASURED `R start_champion = False`) |
| `C-REBOOTED` | at any earlier point | The party is non-empty at every other moment of the leg |
| `C-HOME` | in the 206-frame post-reload window | `gs != OVERWORLD` there, the party is briefly `[]`, and the map reads `(16,11)` — three of the seven conjuncts fail |
| `C-USABLE` | by the first controllable frame | ⭐ That exact failure is on disk: `evidence/…v1-STOPPED-EARLY.stdout.txt:169` `R end_where = ((16, 4), (6, 6))` |

### ⛔ How the leg refuses when pointed at its own output state

Run `fight_the_champion()` from the end-state fixture it mints (`CH24_CHAMP_CAPTURE=post_champion_bedroom`). **All four premise conjuncts fail, and three of the four are ⭐MEASURED to flip:**

| Conjunct | At the premise | At the leg's own output | Source |
|---|---|---|---|
| on HALL4 (5,3) | True | False — `(1,1)` or `(1,3)`, tile `(4,2)` | ⭐ `R end_where = ((1, 1), (4, 2))` |
| `IS_CHAMPION is False` | True | **False** | ⭐ `R start_champion = False` → `R end_champion = True` |
| `ELITE_4_STATE == 4` | True | **False** (0) | ⭐ evidence `:296` → `:297` |
| `DEFEATED_ELITE_4_DRAKE` | True | **False** (cleared by `ResetEliteFour`) | `event_scripts.s:628-634` |

The leg refuses in under 10 frames, naming which conjuncts failed. This is the guard that makes re-entry impossible — and re-entry is not a cosmetic concern: `trainerbattle_no_intro` has **no flag guard** (`trainer_battle.inc:44-48`) and `VAR_TEMP_1` re-arms on every map load (`event_data.c:39-48`, called at `overworld.c:798`/`:848`), so a second entry is another full championship battle against a party with no nurse, no PP restore and a spent bag.

---

## 5. THE FAULT ARMS

Env var: **`POKEBOT_CH24CHAMP_FAULT`**, read in **PRODUCTION** via a `_ch24champ_fault()` helper shaped on `pokemon_league.py:2336-2348` ("⛔ READ IN **PRODUCTION**, NOT IN THE DRIVER — that is what makes an arm driver-proof"), registered in `29-DISABLED-FEATURES-REGISTRY.md` (enforced by `lint_docs.py` R6). All arms fail by printing a verdict, never by dying.

| Arm | What it breaks | The reading that must FAIL, and why it is its OWN reason | Cost |
|---|---|---|---|
| **A1 `nostep`** | suppresses the 8 `Up` frames | `C-CROSSED` missing. Proves the map-change reading is a *measurement of an act*, not an artefact of the fixture. Nothing else in the leg can fail this way. | ~600 frames |
| **A2 `nopressintro`** | presses nothing between `C-CROSSED` and `on_battle_started` | `C-ENGAGED` missing — the `MSGBOX_DEFAULT` intro parks. Proves the cadence is load-bearing for the **`waitbuttonpress` text family**. | ~6,000 frames |
| **A3 `nopressafterwin`** | presses normally until `on_battle_ended`, then stops | `C-INHOF` missing. Proves the cadence is load-bearing **after** the fight — which is exactly where `beat_the_trainer_here` stops (`pokemon_league.py:2522-2528` contains no `press_button`). Different failure, different gate family, different code path from A2. | one full fight (~40,000) |
| **A3b `nopresshofscreen`** *(desirable, not mandatory)* | presses until `C-INHOF`, then stops | Hangs on `Task_Hof_ExitOnKeyPressed`, which blocks on `JOY_NEW(A_BUTTON)` **only**. ⭐ This is the one gate `B` cannot satisfy, so it is the only arm that proves the *button choice* rather than the *cadence*. It costs a fight but hangs ~8,000 frames into the tail rather than ~44,000. | one fight |
| **A4 `healnoop`** | calls the REAL heal with `max_actions=0` | `C-HEALED` **taken**, `missing` **empty**, and only `heal_ready` able to fail. Proves `heal_ready` is a grade conjunct and not decoration. Shape and rationale: `29-DISABLED-FEATURES-REGISTRY.md:271-286`. | ~5,000 frames |
| **A5 OUTPUT-STATE** *(no env var)* | points the leg at `post_champion_bedroom.ss1` | `C-PREMISE` missing, four conjuncts named. Proves the leg cannot re-enter a second championship battle. | <10 frames |
| **A6 `nosettle`** | returns on the first `OVERWORLD ∧ controllable` | `C-HOME`/`C-USABLE` false — `end_where` reads `CHAMPIONS_ROOM (6,6)`. ⭐ **Already run, unintentionally:** `evidence/2026-09-17-ch24tailprobe-v1-STOPPED-EARLY.stdout.txt:169`. Re-running is optional; cite the artefact. | free |
| **A7 `raiseafterreset`** | raises a `BotModeError` on the first post-reset `TITLE_SCREEN` frame | The recovery must NOT reach `run_intro` (`story_mode.py:4059`). ⛔ **DESTRUCTIVE IF THE FIX IS ABSENT** — run only on a throwaway profile, and only *after* the `at_title`-with-a-save branch lands. | one full tail |

### ⛔⛔ A4 IS VACUOUS ON `post_hall4_door.ss1` — COMPUTED, NOT ASSERTED

`Ch24Hall4Mode` heals **before** it mints that fixture, and the shipped run recorded `H-HEAL actions=3 ready=True` (`evidence/2026-09-17-ch24hall4-TREATMENT.stdout.txt:29`) at `story_harness.py:19177`, with the capture at `:19246`. ⇒ at (5,3) the plan is empty and `heal_ready` is True **with or without the arm** — the two arms are byte-identical, and the run would read "no difference", which is what a REFUTATION looks like. This is precisely the failure CLAUDE.md's Tier-2 rule (4) was added for.

**The fix is cheap and already tooled.** Mint `post_hall4_door_unhealed.ss1`:
```
POKEBOT_CH24_FAULT_NOROOMHEAL=1 CH24_HALL4_CAPTURE=post_hall4_door_unhealed \
  py -3.12 story_harness.py post_drake_L75.ss1 --driver ch24hall4 --frames 200000
```
Non-vacuity is already established for that path: `story_harness.py:19026-19027` — *"the start fixture carries a FAINTED Mightyena, so the plan is non-empty"* — and the isolated arm's own evidence shows the grade failing on exactly this conjunct (`2026-09-17-ch24hall4-FAULT-NOROOMHEAL-ISOLATED.stdout.txt:47-48`: `heal_ready=None … missing=['H-HEAL']`). Cost ~4,829 frames (TREATMENT `:28` f4000 → `:59` f4829). ⇒ **See §6 P3/P4: P2's premise dump may show the existing fixture is already below the bar, in which case this drive is unnecessary. Read before spending.**

### Guards that CANNOT be fault-armed, and why they are still worth having

* **The loss / `on_whiteout` posture.** Forcing a loss means throwing the hardest fight in the game (~30,000 frames) and lands in a state — money halved, all four E4 flags cleared, respawn at `EVER_GRANDE_CITY (18,6)` — that **has never been observed**, with no restock leg to hand back to. Leave it unarmed and say so. It is worth having because `on_whiteout` is the **only** channel that distinguishes "lost" from "wedged"; without it, a loss is indistinguishable from a hang and would be filed as a bug in the leg.
* **The `NAMING_SCREEN` hard abort.** Arming it requires a blank-flash profile — which is the very state the abort protects. It is three lines, and the harm it prevents (overwriting a save) is unrecoverable and non-idempotent, so the asymmetry justifies an unarmed guard. Precedent: it is already unarmed in the probe (`story_harness.py:19468-19471`).
* **The 150,000-frame fight bound.** It cannot be armed without a pathological fight, and a bound that never fires on any observed run is untestable by construction. Keep it as a liveness floor, not as a graded conjunct.

---

## 6. ⛔ PROBES THAT MUST RUN FIRST

**This list is short, and the reason is that the expensive measurement was already bought on 2026-09-17.** Two of the four items are offline chores; one is a single instrumented re-run that settles six questions at once; one is conditional.

### P0 — DOCUMENTATION RECONCILIATION (offline, minutes, no emulator)
Three defects that will actively misdirect the person who writes this code:
1. `ai-research-notes/2026-09-24-ch24-GAUNTLET-BUILD-SPEC.md:85` calls the post-(5,2) tail *"UNMEASURED — measure before building (M6)"* and `:105` commands *"extend `Ch24TailProbeMode` (`story_harness.py:19276`) through `(5,2)`"*. It was measured a week earlier with committed evidence, and the class is at **`:19301`** (`:19276` is a comment inside `Ch24Hall4Mode`). ⇒ a cold start reading the newest spec is ordered to redo a finished ~50,000-frame measurement (the P5 shape). Mark M6 DONE with the evidence path, or name the residual — the note already names it (`TAIL-MEASURED.md:83-89`: one trajectory, no win rate, a chain of fixtures).
2. `03-PUNCH-LIST.md:929` (O3): *"25 opposing Pokémon on one PP bar"* → **26** (`trainer_parties.h:4414-4457`). The 4% error sits entirely in the fight that has no heal after it, against a Milotic with Recover and a Sitrus Berry.
3. `03-PUNCH-LIST.md:944`'s HEADER says the flag fires *"~20,000 FRAMES"* before the game is usable; the measurement gives **13,107 as a lower bound** (`8531840 → 8544947`; `IS_CHAMPION` was set earlier still, somewhere in `8530372–8531840`, so the true range is 13,107–14,575), and `victory_road.py:3307` already says ~13,000. The header is the half that gets skimmed (pair P2).

**Why the design cannot proceed:** #1 sends the builder to re-spend the drive this spec depends on.

### P1 — THE CLASSIFIER CASE DEFECT (offline, already measured, code fix)
See HC23. Settles whether the banner's literal marker can be relied on at all — and it currently cannot. **Why it must precede the leg:** if the leg ever reaches `_play`, the first ever win is logged as `HANG CONFIRMED` and filed as a failure in every batch report. Fix the case (or lowercase all three matchers) and fault-test both directions.

### P2 — THE ONE INSTRUMENTED DRIVE (~50,000 frames, `post_hall4_door.ss1`, observe-only additions to `Ch24TailProbeMode`)
⛔ It re-measures nothing; it is the same drive with more instruments — and it supplies the **second trajectory** session-discipline #8 requires before any frame budget in §3 is trusted.

* **P2a — `SAMPLE_EVERY = 1`** (`story_harness.py:19364`) across `8531840 → 8544947`: does `get_game_state()` **ever** read `OVERWORLD` in that 13,107-frame window? *Settles:* whether `C-HOME` is a seven-conjunct predicate or a one-conjunct one. The existing log samples at 1/60 plus transitions, so "never OVERWORLD during the tail" is currently an **interpolation**. Until it is answered, the party-non-empty and not-on-HALL_OF_FAME terms are **load-bearing, not redundancy**.
* **P2b — the production watchdog, with production's own instrument.** Compute `story_mode.py:3733-3739`'s exact 5-tuple every frame; log `_stall_frames` and the per-frame exception count. *Settles:* whether a winning run derails at 18,000 frames. ✅ **RUN 2026-09-25 — ANSWER: NO.** Max streak **12,680**, 0 signature exceptions, 5,320 frames of margin. ⛔ The 12,681-frame figure was taken under the harness's 6-tuple and compares emulator frames to a **mode-driven**-frame threshold (`story_mode.py:3636-3638` says so: *"battles don't count — a listener holds control then"*). Note the asymmetry a designer must account for: `_progress_sig()` (`:2038-2055`) has its **own** try/except returning `None`, and `None == None` compares equal — so that component can fail silently and keep the stall streak alive, while a throw in `get_map_data_for_current_position()` resets it.
* **P2c — flag 1615, with controls.** Read `get_event_flag_by_number(1615)` at the premise (expect False) and inside `on_battle_ended` (expect True), plus a never-fought trainer's number as a negative control. ⛔ **Do not use the proposed 1275-vs-`DEFEATED_ELITE_4_SIDNEY` positive control — it is arithmetically circular:** `memory.py:346-356` computes `0x1270 + n//8, bit n%8`, and the named table is built from the identical formula and the identical constant, so the two paths agree *by construction*. The discriminating control is False-then-True **in the same run**. *Settles:* whether 1615 is a real reading at all. It is **not** load-bearing (see §3 S4), so a null result costs nothing.
* **P2d — `get_event_var("LAST_TALKED")` at the premise**, one line, observe-only. `trainerbattle_no_intro` does not call `SetMapVarsToTrainer` (`battle_setup.c:1110-1112`, contrast `:1113-1116`), so `EventScript_DoNoIntroTrainerBattle`'s opening `applywaitmovement VAR_LAST_TALKED, Movement_RevealTrainer` runs against a **stale local id**. It is harmless on the canonical route by coincidence (Drake and Wallace are both local id 1) — and a stale id fed to `applywaitmovement`+`waitmovement` under an un-releasable `lockall` is a candidate permanent hang, not a cosmetic defect. *Settles:* whether the fixture the leg is graded from carries the coincidence.
* **P2e — per-move PP of every party member at (5,3).** Telemetry only. *Settles:* nothing — it makes the **first Wallace loss diagnosable** as PP exhaustion rather than mis-attributed to levels, on a path with 26 opponents and no PP restore past the lobby (`items.py:92-96` `PpRecovery` is a distinct enum value from `Healing`, and `pokemon_league.py:279` filters on `ItemFieldUse.Healing`). ⛔ Do **not** add PP as a blocking conjunct without a measurement: a gate that cannot remedy is just a halt, and (5,3) is a strand.
* **P2f — the premise HP dump**, which also decides whether P3 is needed (below).
* **P2g — a per-frame count of controllable frames inside `CHAMPIONS_ROOM` after `on_battle_ended`.** *Settles:* whether any reading can be taken there at all, or whether the room is strictly a latch-only region.

### P3 — MINT `post_hall4_door_unhealed.ss1` (~5,000 frames) — **CONDITIONAL**
Run only if P2f shows `post_hall4_door.ss1`'s party is at or above `TOP_UP_BELOW` (`overworld_items.py`) on every member. *Settles:* the only fixture on which fault arm **A4** is non-vacuous. Without it the `heal_ready` conjunct ships unarmed, which the registry (`29-DISABLED:277-286`) explicitly says "tests nothing".

### P4 — run the arms
A1, A2, A4, A5, A6 before the treatment is believed. A3/A3b and A7 on their own schedule (each costs a fight or a throwaway profile).

**Honest note on what none of these settle:** the **win rate**. Wallace was beaten **once**, from a fully-healed party carrying one Revive, with a party of `Mightyena L77 / Zigzagoon L19 / Sceptile L75 / Swellow L75 / Wailord L75 / Castform L36` — four effective members. Nothing in this spec measures how often that party wins, and `on_whiteout` is the other exit.

---

## 7. WHAT THIS LEG MUST NOT DO

1. ⛔ **Must not be written as a fifth call to `fight_one_room` / `beat_the_trainer_here`.** Settled at `03-PUNCH-LIST.md:923`. Nothing in the code enforces it today — `IS_CHAMPION` **is** in the flag table (`emerald.txt:1061`), so `fight_one_room(..., victory_flag="IS_CHAMPION")` passes every premise check at `:2618` and `:2625-2641` and then walks into the un-fleeable fight via `_pass_through_door(HALL_FAR_DOOR, HALL4)` at `:2744-2745`. ⇒ **ship a two-line refusal naming `EVER_GRANDE_CITY_HALL4`/`EVER_GRANDE_CITY_CHAMPIONS_ROOM` at the top of `fight_one_room`, as gate #75**, fault-tested to fire on that pair and stay silent on the three legal ones and on mere mentions in comments. Template: the shipped class-constant tripwire at `story_harness.py:19090-19093`.
2. ⛔ **Must not pass any flag NAME for Wallace** to any helper (HC6).
3. ⛔ **Must not navigate, face, or press a direction inside the Champion's room** (HC1/HC2). `_goto_warp` (`:949`) and `_navigate_riding_out` (`:91`) are not merely irrelevant — they are the two functions that would silently warp the bot into the fight.
4. ⛔ **Must not use `player_avatar_is_controllable()` as a gate, nor trust `wait_until_truly_controllable()`'s return** (HC3/HC4).
5. ⛔ **Must not read any y=13 tile** — 13×13 room, out of bounds, **passes by construction** (§3 S3). This is a vacuity hazard, not a crash.
6. ⛔ **Must not grade on `DEFEATED_ELITE_4_*` or `VAR_ELITE_4_STATE`** — false on success (HC5).
7. ⛔ **Must not grade on "the exit door is open."** The door *is* opened passable (`setmetatile 6,1/6,2 … FALSE`; `scrcmd.c:2035-2047` confirms the 4th arg is `isImpassable`), but `lockall` is never released before the `warp` and the run leaves via `ScrCmd_warp`, not the warp event. Replace with "we are standing on HALL_OF_FAME."
8. ⛔ **Must not use `VAR_TEMP_1` as any kind of discriminator.** It is set to 1 **before** the battle (`scripts.inc:28` precedes `:29`) and zeroed on every map load. It means "a cutscene has begun" — and it means that on **two** maps in the tail: `EverGrandeCity_HallOfFame/scripts.inc` gates its own `OnFrame` on the same var.
9. ⛔ **Must not bound on a press count or a stop count** (HC11).
10. ⛔ **Must not press B during the tail, must not hold any button, must not press a direction after the one `Up`, must not press SELECT** (HC9).
11. ⛔ **Must not keep pressing once the bedroom is reached** (HC10).
12. ⛔ **Must not call `soft_reset()`** (HC-§0). The game performs its own reset; a second one would zero the frame counter and re-arm `story_mode.py:5800`'s negative clamp.
13. ⛔ **Must not hardcode the end map.** Assert tile `(4,2)`, accept map ∈ {`(1,1)`,`(1,3)`} (HC15).
14. ⛔ **Must not assert "we left HALL4" immediately after the step** (HC14).
15. ⛔ **Must not navigate out of the bedroom, or treat leaving it as part of completion** (§3 S7).
16. ⛔ **Must not let any exception escape in the 426-frame post-reset window** (HC22).
17. ⛔ **Must not take unwrapped position reads after the crossing** (HC7).
18. ⛔ **Must not capture a new fixture from the now-cleared profile and compare its tail length to 49,873.** `current_save.sav` holds a cleared game; a post-clear fixture takes the `gHasHallOfFameRecords=TRUE` fast path, and the shorter number would read as an improvement rather than a different code path (`TAIL-MEASURED.md:90-92`). ⭐ Re-running from `post_hall4_door.ss1` is safe — its RAM carries `SYS_GAME_CLEAR=False`, so the slow first-clear path is preserved.
19. ⛔ **Must not set `_reached_end_of_content` on any path that is not a completed §Ch24.** `story_mode.py:5344` sets it unconditionally, and `:5793` is the only reader — it suppresses the "stopped: handed to Manual mid-run" label. Anything reaching that line is scored `finished`.
20. ⛔ **Must not "fix" `exit_building_after_whiteout`.** `04-HANDOFF.md:439` blames it for firing inside the sealed gauntlet; it is a guarded no-op there (`early_game.py:385` returns unless the map name contains `POKEMON_CENTER`; `_CAVE_EXITS` holds only Granite Cave and Fiery Path) — and it is **correct** in the only state that can reach it, since a loss white-outs the bot clean out of the sealed maps into a Poké Center. Correct the handoff clause rather than patching an inert function; the real recovery hazard is `story_mode.py:3840 continue`.

---

## 8. OPEN DECISIONS FOR THE HUMAN

These are policy choices, not engineering ones. Options are stated neutrally; where the evidence is silent I have not invented a recommendation.

**D1 — Does the champion leg ship harness-only, or wired into `_play`?**
Harness-only is what every prior §Ch24 leg did (`pokemon_league.py:2805-2809` says so explicitly for `enter_the_league`), and four of the five gauntlet entry points are still unwired (`grep` over `story_mode.py` returns only `train_for_league`, `:5271`/`:5274`). Wiring requires **five things in one commit**: (i) `ch24_chapter_done()`; (ii) a `_guard(...)` between the dispatch and `:5332`; (iii) `:5344` made conditional; (iv) a retargeted banner; (v) the classifier fix from P1. *Options:* (a) harness-only now, wiring as its own item — smaller blast radius, and the leg is provable today; (b) both together — one commit, five coupled changes, and the first ever win at stake.

**D2 — Where does `ch24_chapter_done()` live?** ⛔⛔ **AND A CONSTRAINT THIS SPEC HAD NO LANGUAGE FOR, MEASURED 2026-09-25:** on **all five** §Ch24 fixtures, `SYS_GAME_CLEAR` and `IS_CHAMPION` read **RAM=False but FLASH=True** (two controls agree on both sides, so the readers discriminate). ⇒ **a predicate reading FLASH alone would report a cleared game on a save that has not beaten the Champion** — including one standing OUTSIDE the League with the door shut. And per P2a the tail reads `OVERWORLD` for **5,634 frames**, so it cannot be a single `OVERWORLD` conjunct either. ⇒ whichever module it lives in, it must say WHICH side it reads and why (`probe_ram_vs_flash_clear.py`). 
Beside `CH24_GAME_CLEAR_FLAG` / `CH24_SEALED_MAPS` in `victory_road.py:3289-3308` (where the §Ch24 constants already are), or in `pokemon_league.py` (where the legs are). Splitting them risks the "same fact in two functions" drift the module warns about at `:67-70`. *No evidence favours either;* ownership is `#24-gameclearflag` (`03-PUNCH-LIST.md:944`).

**D3 — Does the retargeted banner keep the literal marker, or do all three classifiers move to a new one?**
Given HC23, "keep the substring" is not an option as written — the substring does not currently appear. *Options:* (a) fix the case in `story_mode.py:5335` and keep `end of built content` as the contract; (b) define a new, explicit marker and update `compare_runs.py:102`, `endless_runs.py:60` and `story_harness.py:25042` together. Both are defensible; shipping one without the other is not.

**D4 — What is the loss posture?**
A Wallace loss calls the same `ResetEliteFour` as a win, so post-loss and post-win state are **identical** on all four E4 flags and on `VAR_ELITE_4_STATE`; money is halved (`overworld.c:358-366` `DoWhiteOut`), and the ruled remedy `#24-restockleg` (`03-PUNCH-LIST.md:92`, USER RULING 12) is **UNBUILT and blocked on money** (₽54,300 basket vs a measured ₽1,741, halved again per loss). *Options:* (a) terminal for the run — record the loss and hand to Manual with an explicit outcome string; (b) block the champion leg on `#24-restockleg`; (c) something in between (e.g. retry from a pinned fixture in the harness only, never in production).

**D5 — ✅ CLOSED 2026-09-25, NO DECISION REQUIRED. P2b MEASURED THAT IT DOES NOT FIRE** (12,680 vs 18,000). All three options below are DEAD; building any of them would be unrequested architecture against a non-existent threat. *(Superseded question:* **What does the leg do if P2b says the production watchdog fires on a winning run?**
*Options:* (a) mutate `context.message` on a cadence — cheapest, it is one of the five signature components, but that field is read by two other mechanisms (`story_harness.py:25042`'s hang suppressor and the END-OF-CONTENT classifiers) and the interaction is untested; (b) an explicit per-mode watchdog suspension for the tail — clean, new code in `story_mode.py`; (c) raise the threshold. ⛔ This is architecture, and the project's own measured rule says to grade recon's architecture advice "not at all" — so it waits for P2b.

**D6 — Is `beat_the_trainer_here`'s missing `_event_flags` guard fixed now or filed separately?**
It is a latent defect in an already-passing shared helper (the guard was left in the callers during the 2026-09-25 extraction; two copies exist, `:2110` and `:2618`). Moving it down gives all callers the guard — but it touches proven code on a path this leg does not use.

**D7 — Is the `_tp_*` reader family promoted to `modules/story/`, or duplicated in the leg?**
Duplicating is the drift shape `pokemon_league.py:67-70` calls out by name; promoting moves ~140 lines of test-only code into production in the same commit as a new leg.

**D8 — Does the second trajectory (P2) have to be a REAL-mode run?**
USER RULING 11 (`06-DECISIONS-LOG.md:6428-6444`) defines §Ch24 DONE as four conjuncts: the flag, **from the real story mode** (not a `--driver`), **with no fixture scaffolding** (not a pinned `.ss1`), **at ×1**. P2 is a driver run from a pinned fixture at speed, so it can satisfy conjunct (1) and no other. *Options:* (a) accept P2 as an engineering measurement and keep the ruling's conjuncts for the product claim; (b) require the second trajectory itself to be a real-mode run — which cannot happen until D1 resolves.

**D9 — Is PP a recorded telemetry field now, or a future blocking conjunct?**
`party_is_gauntlet_ready` cannot see it (`overworld_items.py:240-249`; `Target` at `:69-86` has no pp field), and adding a term would change the meaning of every existing `heal_ready` reading in the evidence corpus. *Options:* (a) record only (this spec's P2e); (b) record and gate, once a measurement exists.

**D10 — Post-clear positioning: in scope or follow-on?**
The bot ends **indoors** at `LITTLEROOT_TOWN_BRENDANS_HOUSE_2F (4,2)` where Fly is refused, and `_ch24_step_out_if_fly_illegal` (`pokemon_league.py:1690`) knows only Victory Road (`:1714-1719`). The staircase leads into an armed Dad / S.S. Ticket scene that nothing downstream expects.

**D11 — `#24-levelgap` (`03-PUNCH-LIST.md:677`, OPEN, awaiting a user choice on party composition).**
`story_mode.py:5287-5292` records that `train_for_league` has no floor `_guard` after it, so "the gauntlet's first act must be a readiness guard" — and that guard's threshold cannot be specified until D11 resolves. It is upstream of the champion leg, not part of it, but it blocks the wiring in D1.