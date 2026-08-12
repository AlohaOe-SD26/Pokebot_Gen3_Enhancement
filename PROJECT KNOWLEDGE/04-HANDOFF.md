# Handoff — Pokebot_Gen3_Enhancement
> Current-state file: edit in place, CONTINUOUSLY. A new agent with zero
> context must be able to resume from this file alone.

**Repository:** https://github.com/AlohaOe-SD26/Pokebot_Gen3_Enhancement.git
**Last updated:** 2026-08-11 — read "‼ YOU ARE HERE" immediately below.
Every banner further down is HISTORY, newest first.

---

# ‼ YOU ARE HERE — 2026-08-11. Read this, then `14-AGENT-PLAYBOOK.md`.

## WHAT THIS IS
`sandbox-pokebot/` is the working build of a Pokémon Emerald bot. Its **Story mode** plays the
game autonomously from Littleroot. `40cakes repo/` is a pristine upstream mirror (never edit);
`custom-pokebot/` is the promoted fork. **All work happens in `sandbox-pokebot/`.**

## STATE
| | |
|---|---|
| branch / HEAD | `main`, clean, pushed |
| box | **IDLE.** Batch `20260811-130454` finished 4:05 PM (VERDICT OK, 28 runs, 0 header violations). **Freeze LIFTED.** |
| story content | Littleroot → 6 badges → Mt. Pyre → Magma Hideout (Groudon awakened). Next unwritten beat: the **Slateport submarine** — ✅ **SPEC + PLAN + VERIFIED ANCHOR all ready; only the code is missing.** |
| ‼ is code frozen? | **No.** The batch finished; `sandbox-pokebot/` is editable again. |
| upstream | checked **2026-08-11**, `5dd898f8`, unchanged |
| **if stopped mid-task** | **NOTHING IS PARKED.** The session ended on a completed, verified item (`#24-teachmsgstall`), gate 12/12 green, docs current, tree clean. Start at "NEXT ACTIONS". |
| promotion | ✅ **ALL CURRENT WORK IS PROMOTED (two rounds, both user-approved, 2026-08-11).** `#24-teachmsgstall`; then KI-51 guard + KI-52 fallback + battle STATUS telemetry. Both verified **DRIVEN in `custom-pokebot`** on deterministic fixtures, frame-for-frame identical to sandbox. **Source drift: ZERO.** ‼ KI-52's fallback is structurally proven only — no live A/B (see `DIVERGENCE-LOG`). |

## ✅ WHAT JUST SHIPPED — `#24-teachmsgstall`, the project's top bug, CLOSED
**The replace-prompt detector had a ONE-FRAME window.** Measured with a new frame trace
(`TEACH_TRACE=1`, `magma_door.ss1`, HM02 → Swellow):
```
f3232735  tasks=['Task_ReplaceMoveYesNo']              <- the ONLY frame it is visible
f3232736  tasks=['Task_HandleReplaceMoveYesNoInput']   <- gone, and it never comes back
```
`pret/pokeemerald src/party_menu.c` explains it exactly — `Task_ReplaceMoveYesNo` displays the
menu and **sets its own function to `Task_HandleReplaceMoveYesNoInput` in the same frame**, i.e.
it retires on the frame it becomes answerable, which is the frame our condition first became true.

**Missing it lost the teach** because the loop kept mashing A every 12 frames, and
`Task_HandleStopLearningMoveYesNoInput` reads **A as YES = ABANDON THE TEACH**. ‼ The three
"different" failure points recorded across runs are **three phases of that one road**: summary
handoff → "did not learn FLY" → back in the bag, re-arming. ‼ And it read as deterministic *and*
intermittent at once because a `.ss1` replays identical frame timing (0/3 from one save) while
live runs land on a random phase (38/42) — that property is what made it unfalsifiable for four
rounds.

**Fix:** match both task spellings (`_PROMPT_TASKS`/`_STOP_TASKS`), add an `already-advanced`
exit (non-fatal), press **B** at the stop-learning prompt before the blind-A fallback. The ride
ladder had the identical exposure and is fixed the same way.

**A/B — same save, same item, same target, one env var apart:**
| arm | env | exit | result |
|---|---|---|---|
| OLD | `POKEBOT_TEACHWINDOW_A=1 TEACH_CANCEL_FORGET=1` | `ride:hard-cap stall_peak=61 frame=8999` | **`learned=False`** |
| NEW | `TEACH_CANCEL_FORGET=1` | `ride:learned stall_peak=250 frame=896` | **`learned=True`** |

The OLD arm's record is structurally identical to the 2026-08-10 production failure
(`not-learned-after-ride:hard-cap`, `stall_peak=61`, `frame=8999`).

**Positive controls (the fix must not cost the healthy path):** replace path with no env →
`ride:learned frame=458 stall_peak=167`, **byte-identical to the pre-fix run**; free-slot path
(`TEACH_SLOT=1 TEACH_ITEM=HM06`, Zigzagoon L3) → `learned=True replaced=[]`.
‼ One arm is a **negative** result worth keeping: `TEACH_MISS_WINDOW=1` alone with the pre-fix
loop still LEARNS (`ride:learned`, 323f) — the ride ladder recovers it. Missing the window is
**necessary but not sufficient**; where the blind A-mash then lands decides survival. That is
exactly why the recorded failure point moved between runs.

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 repro_teach_prompt_window.py                    # 26 checks, seconds, offline
PYTHONUTF8=1 TEACH_TRACE=1 TEACH_ITEM=HM02 py -3.12 story_harness.py magma_door.ss1 \
  --driver teachfull --frames 400000 --profile tftrace                # the trace that found it
```

## ✅ AND WHY THE MAGMA HIDEOUT CHAPTER LOSES — ANSWERED 2026-08-11, no longer a mystery
**Crobat confuses the two strongest attackers into killing themselves, then Maxie heals Camerupt
out of the kill.** Both measured from the chapter's own telemetry:
```
[TURN 4] Sceptile L44 110/122 [Confused] -> UseMove:Slam(pp19)  vs Crobat L38 90/119   # 122->110->30->4
[TURN 14] Skitty L17 45/45 -> UseMove:Tackle(pp35)  vs Camerupt L39  22/110
[TURN 15] Skitty L17 45/45 -> UseMove:Tackle(pp34)  vs Camerupt L39  67/110            # +45 heal
```
‼ **Neither is a BUG.** The action pipeline is fine — confusion self-hits simply do not consume
PP, which is why "frozen PP" looked like a broken move. The bot has **no answer to confusion**
(no switch-out, no Persim Berry) and **no answer to a healing boss**. Both are DESIGN decisions and
they are the user's — see `03-PUNCH-LIST` §2.
‼ This also **refutes `#24-bosstelemetry` LEAD 2 for this instance**. The 2026-08-09 sightings were
logged without status and are NOT retro-explained — but the field now exists to re-check them.

## ‼‼ THREE THINGS THAT WILL SAVE THE NEXT AGENT REAL TIME
1. **A Gen 3 `Task_XxxYesNo` hands off to `Task_HandleXxxYesNoInput` on the frame the menu
   becomes answerable.** Never key a detector on the DISPLAY task alone — watch the input
   handler too, or you have a one-frame lottery. This one cost four rounds.
2. **Never blind-mash A at a live yes/no.** Somewhere in Gen 3 there is a prompt where A means
   "give up", and a 900-frame mash will find it. Mash only to advance TEXT.
3. **A fault injection that models a TIMING miss must fire ONCE.** My first version re-fired on
   every retry, which made the FIXED arm loop for ever and look worse than the broken one. If the
   fix's mechanism is retry, an always-on fault is unsatisfiable by construction.

## ‼ THE OLD `#24-teachmsgstall` REPRO IS DEAD — do not chase it
`saves/magma_door.ss1` is **re-captured by `--driver magmatravel` on every success**, and a
chapter run at 22:05 on 2026-08-10 overwrote the save the 21:27/21:34 failures were measured on.
Both documented arms (HM04, HM02) now **PASS** on it with identical parameters. Nothing was wrong
with the finding; the fixture underneath it moved. **A save any driver re-captures is a cache, not
a fixture.**

## ‼‼ KI-56 — THE BOT IS STRANDED IN THE MAGMA HIDEOUT. READ THIS BEFORE ANY STORY WORK.
Driving §Ch16 exposed it: **Ch15 completes its binary flag test and leaves the run permanently
stuck four floors deep.** Measured from `profiles/ch16a/current_state.ss1`:
* component containing the bot at `MAGMA_HIDEOUT_1F (25,34)`: **248 tiles, NO reachable exit warp**
* the INBOUND route `(10,34) → (25,34)` now **also fails** — the way it walked in is gone
* the push-from tiles are **unreachable**, so it cannot even re-push
* boulders measured at `(5,22) (7,22) (6,23)` = the **ORIGINAL** positions ⇒ **Strength boulders
  RESET on map reload**, exactly like Rock-Smash rocks

‼ **The acceptance test never asked whether the bot could LEAVE** — `GROUDON_AWAKENED` is set the
moment Maxie falls. New playbook rule added: *a chapter's test must include "and the bot can
continue"*.

**Fix options recorded in KI-56, none chosen.** The leading one is **Escape Rope support**, which
the bot does not have at all (0 hits across `modules/story/` and `modules/modes/util/`).

## ⏭ NEXT ACTIONS, IN ORDER
1. ~~Ask about promotion~~ — ✅ **DONE 2026-08-11, user-approved and verified driven in
   `custom-pokebot` (OLD `learned=False` / NEW `learned=True`, identical to sandbox). Zero source
   drift.** ‼ **Nothing about teach reliability has been measured in a BATCH yet** — the live
   rate to beat is 38 of 42 in `20260810-082509`. The honest claim is "the mechanism is proven and
   its failure mode is closed", not a percentage. Do not quote an outcome number until a batch
   produces one.
2. ✅✅ **BUILD §Ch16 — IT IS FULLY UNBLOCKED. Everything except the code exists.**
   * **ANCHOR: `saves/post_maxie.ss1`** — md5 **`19399688e730`**, 59,053 bytes. ‼ **Check that md5
     before using it**; three separate fixture mix-ups happened on 2026-08-11 alone.
   * **VERIFIED** by `probe_ch16_anchor.py`, every control green:
     gate `SLATEPORT_HARBOR_STATE=1`; ERA control (1 vs `magma_door.ss1`'s 0 — they differ);
     beat-not-yet-run (Aqua blocking flags unset); corroboration (`groudon=True`,
     `SLATEPORT_CITY_STATE=1`); path control, and door `(11,14)` → trigger3 `(8,14)` = 3 waypoints.
   * **SPEC + IMPLEMENTATION PLAN:** `12-STORYMODE-DESIGN.md` §Ch16 — route, function shape,
     Segment 16 wiring copied from Segment 15's pattern, driver spec.
   * **NO BATTLE in the beat.** Completion is binary: `SLATEPORT_HARBOR_STATE == 2`.
   * ‼ **THE TRAP:** the var is set roughly HALFWAY through the script — Stern's approach, a second
     msgbox, two setflags and `releaseall` all follow. **Wait for CONTROL, not the var**, and put
     BOTH halves in the driver's acceptance test.
   * ‼ **NO `VAR_` PREFIX** on event-var names — the reader's table is keyed `SLATEPORT_HARBOR_STATE`
     and `get_event_var` returns **-1** for an unknown name *without raising*. That silently cost a
     capture on 2026-08-11.
   * ‼‼ **THE ONE MEASURED RISK IS THE LAST MILE — `KI-53`.** Static recon
     (`probe_ch16_travel.py`, all controls green) says the leg is plannable *until* Slateport:
     ```
     MAUVILLE(22,6)   -> ROUTE110(14,97) : OK, 203 wp
     ROUTE110(14,97)  -> SLATEPORT(28,13): FAIL      <- the last mile
     SLATEPORT(28,13) -> ROUTE110(14,97) : OK,  30 wp  (the exact reverse plans!)
     SLATEPORT -> harbor door(28,12): OK 1 wp;  harbor(11,14) -> trigger3(8,14): OK 3 wp
     ```
     ⇒ **Do NOT write the travel leg as one `navigate_to(SLATEPORT_CITY, …)`** — build it as
     EXPLICIT SHORT LEGS in the §Ch15 pattern with **ROUTE110 → SLATEPORT_CITY as its own leg**, so a
     failure names itself. ‼ A static FAIL is NOT a verdict: `_navigate_riding_out` does strictly
     more than the planner, and that is exactly how Ch15's Mauville → Route 112 leg succeeded while
     planning statically as FAIL.

3b. **RUN `verify_fixtures.py` FIRST, and after any long driven run.** New 2026-08-11. Three
   results were lost in one day to "same filename, different bytes"; `saves/FIXTURES.md5` +
   `verify_fixtures.py` make that check mechanical (exit 1 on drift of a PINNED save). ‼ The
   §Ch16 anchor is PINNED at md5 `19399688e730` — if it drifts, a driver overwrote it; recover it,
   do not bless it with `--update`.
3. **KI-48 / KI-49** — the travel bugs; `could not reach` was 72 events in one batch.
4. **Do NOT grade any of this on the finish rate.** Four batches read 25.0 → 33.3 → 16.1 → 28.6%
   at n≈30 and resolved nothing.

## HOW TO RUN / TEST — the gate is now **12 of 12** (re-run 2026-08-11)
`repro_battle_items`, `repro_counter_hunt`, `repro_counter_huntable`,
`repro_movepool_counter_candidates`, `repro_hunt_driven_grounds`, `repro_counter_move_answer`,
`repro_boss_plateau`, `repro_boss_cfg_coverage`, `repro_area_item_gate`, `repro_hmteach_postlearn`,
`repro_teach_under_dialogue`, **`repro_teach_prompt_window`** (new).
‼ `repro_counter_hunt` and `repro_area_item_gate` print `RESULT: ALL PASS` / `all checks pass.` —
grepping only for "ALL PASS" reports them as false failures.
---

# 📚 EARLIER HANDOFF SNAPSHOTS → `28-HANDOFF-ARCHIVE.md`

Every superseded "you are here" section now lives in **`28-HANDOFF-ARCHIVE.md`** (append-only).
This file is CURRENT STATE only — if something here is no longer true, fix it here rather than
adding another banner below it.
