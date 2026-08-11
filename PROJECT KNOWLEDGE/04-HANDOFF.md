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
| box | **IDLE.** No batch running. |
| story content | Littleroot → 6 badges → Mt. Pyre → Magma Hideout (Groudon awakened). Next unwritten beat: the **Slateport submarine**. |
| ‼ is code frozen? | **No.** The freeze rule applies only during an `x4_headless` BATCH. |
| upstream | checked **2026-08-11**, `5dd898f8`, unchanged |
| **if stopped mid-task** | **NOTHING IS PARKED.** The session ended on a completed, verified item (`#24-teachmsgstall`), gate 12/12 green, docs current, tree clean. Start at "NEXT ACTIONS". |
| promotion | ✅ `#24-teachmsgstall` promoted 2026-08-11 (user-approved), **verified DRIVEN in `custom-pokebot` as the same A/B**, frame-for-frame identical. ‼ **THE SANDBOX HAS DRIFTED AGAIN SINCE**, by exactly one change: the **KI-51 whiteout guard** in `do_magma_hideout` (`modules/story/early_game.py`). Not promoted — needs approval, and arguably should wait until its live firing is confirmed. |

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

## ⏭ NEXT ACTIONS, IN ORDER
1. ~~Ask about promotion~~ — ✅ **DONE 2026-08-11, user-approved and verified driven in
   `custom-pokebot` (OLD `learned=False` / NEW `learned=True`, identical to sandbox). Zero source
   drift.** ‼ **Nothing about teach reliability has been measured in a BATCH yet** — the live
   rate to beat is 38 of 42 in `20260810-082509`. The honest claim is "the mechanism is proven and
   its failure mode is closed", not a percentage. Do not quote an outcome number until a batch
   produces one.
2. **Build the SLATEPORT SUBMARINE beat — ✅ RECON IS DONE, the spec is
   `12-STORYMODE-DESIGN.md` §Ch16** (written 2026-08-11 from `SlateportCity_Harbor/scripts.inc`
   + `map.json`). Headlines so the next agent can judge the cost before opening it:
   * **There is NO BATTLE in this beat.** It is a coord-trigger cutscene — the cheapest
     remaining chapter by a wide margin.
   * **The precondition is already satisfied by Ch15 for free** — every trigger is gated on
     `VAR_SLATEPORT_HARBOR_STATE == 1`, which Maxie's defeat sets.
   * The trigger column is **`SLATEPORT_CITY_HARBOR x=8, y=11..14`**; trigger 3 (`y=14`)
     `applymovement`s the player into the scene, so aim there from the south doors.
   * **Completion test: `VAR_SLATEPORT_HARBOR_STATE == 2`.** Binary, no batch.
   * ‼ **THE TRAP:** that var is set roughly HALFWAY through the script — Stern's approach, a
     second msgbox, two setflags and `releaseall` all follow. Exiting on the var leaves the
     avatar `lockall`ed. **This is the exact failure that cost two runs on 2026-08-10.**
   * It opens `FLAG_HIDE_AQUA_HIDEOUT_1F_GRUNT_1/2_BLOCKING_ENTRANCE` — i.e. the **Lilycove Aqua
     Hideout**, which is the next (much larger) chapter.
   * ‼ `OnTransition` rewrites the harbor's population (patrons hidden, Stern moved to `(12,13)`).
     **Do not model this map from `map.json` alone** — same class as the Jagged Pass guard.
   **✅ STEP 1 IS PART-DONE (2026-08-11), and it exposed two bugs — read this before retrying:**
   * `--driver magmahideout` now **captures `saves/post_maxie.ss1` on success**
     (`MAGMA_HIDEOUT_CAPTURE=0` to suppress), gated on `groudon` so a failed run cannot write a
     wrong-era anchor. `probe_ch16_anchor.py` is the era gate for it (NAME / ERA / not-yet-run /
     PATH controls).
   * ‼ **THE ANCHOR WAS NOT PRODUCED — the chapter LOST to Maxie (KI-50).** The chapter is
     **not deterministic**: it reaches Maxie reliably but completes 1 of 2 driven runs. Just
     re-run `--driver magmahideout` from `magma_door.ss1` until `groudon=True`; the capture is
     automatic. **Then run `probe_ch16_anchor.py` before building anything on it.** ‼ Budget for
     it: **the chapter wins 1 in 3**, so expect ~3 runs of ~6-10 min each. Give each run a
     timeout well over 10 minutes — one of mine was cut off by a 10-minute cap mid-fight.
   * ‼ **KI-51, FIXED (structurally proven; live firing UNCONFIRMED)**: a losing run used to ride
     60,000 frames at an empty overworld and then blame "the Maxie challenge never resolved". It
     now fails after 300 off-map frames with the real state (map, tile, `party_alive`), so a retry
     loop is cheap. `repro_maxie_whiteout_guard.py` pins it (18 checks, fault-injected red).
     **If you re-run the chapter and it loses, grab the stdout** — a line reading
     `left MAGMA_HIDEOUT_4F during the Maxie challenge` is the missing live confirmation.
   Then §Ch16's steps 2-4. **✅ THE IMPLEMENTATION PLAN IS WRITTEN** —
   `12-STORYMODE-DESIGN.md` §Ch16 "IMPLEMENTATION PLAN" has the decomp-read route
   (`SLATEPORT_CITY (28,12)` -> harbor `(11,14)` -> walk west to trigger 3 at `(8,14)`), the
   function shape, the Segment 16 wiring copied from Segment 15's pattern, and the driver spec.
   Once the anchor exists this is mechanical.
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

# HISTORY — 2026-08-10 night

## WHAT THIS IS
`sandbox-pokebot/` is the working build of a Pokémon Emerald bot. Its **Story mode** plays the
game autonomously from Littleroot. `40cakes repo/` is a pristine upstream mirror (never edit);
`custom-pokebot/` is the promoted fork. **All work happens in `sandbox-pokebot/`.**

## STATE
| | |
|---|---|
| branch / HEAD | `main`, clean, pushed |
| box | **IDLE.** No batch running. |
| story content | Littleroot → 6 badges → Mt. Pyre → **MAGMA HIDEOUT (Groudon awakened)**. Next unwritten beat: the Slateport submarine. |
| ‼ is code frozen? | **No.** The freeze rule applies only during an `x4_headless` BATCH. |
| upstream | checked 2026-08-10, `5dd898f8`, unchanged |
| **if stopped mid-task** | **NOTHING IS PARKED.** The session ended on a completed, verified item: chapter done, full regression gate 10/10 green, all docs current, working tree clean, 0 unpushed. Start at "NEXT ACTIONS" below — there is no interrupted work to resume. |
| promotion | ✅ **DONE 2026-08-10 night, user-approved.** Ch15 + `#24-strength` promoted to `custom-pokebot/`, **verified DRIVEN there** (`--build custom` → `groudon=True`). **Source drift: ZERO.** |

## ✅ WHAT JUST SHIPPED — `#24-magmahideout` AND `#24-strength`, BOTH DONE
```
[magmahideout] RESULT groudon=True map=MAGMA_HIDEOUT_4F at=(15, 21)
  floors=['MAGMA_HIDEOUT_1F','MAGMA_HIDEOUT_2F_1R','MAGMA_HIDEOUT_3F_1R','MAGMA_HIDEOUT_4F']
  whiteouts=0
```
`FLAG_GROUDON_AWAKENED_MAGMA_HIDEOUT` is set — the flag the decomp's own Maxie script sets on
defeat, and the chapter's whole acceptance test. **Binary. No batch, no z-score.**
`do_magma_hideout_chapter()` is wired into `story_mode.py` as **Segment 15**.

**The chain, all driven:** Mt. Pyre summit → heal Lilycove → heal Mauville **+ teach Strength**
→ Route 111/112 (clearing the `#24-smashroute` rock) → cable car → Mt. Chimney → Jagged Pass →
coord trigger un-walls the entrance → **two Strength pushes** → 1F → 2F_1R → 3F_1R → 4F → Maxie.

```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 probe_magma_anchor.py     # era gate, 4 controls
PYTHONUTF8=1 py -3.12 probe_ch15_travel.py      # the route
PYTHONUTF8=1 py -3.12 probe_ch15_interior.py    # the interior
PYTHONUTF8=1 COLUMNS=400 py -3.12 story_harness.py post_mtpyre.ss1 --driver magmatravel  --frames 2500000 --profile mtN
PYTHONUTF8=1 COLUMNS=400 py -3.12 story_harness.py magma_door.ss1  --driver magmahideout --frames 2500000 --profile mhN
```
**New anchors:** `saves/magma_door.ss1` (at the OPEN hideout door, party knows Strength) and
`saves/magma_1f_fail.ss1` (a failure site kept for iterating). `magmatravel` re-captures the
first on every success.

## ‼‼ ALREADY PROVEN — DO NOT RE-RUN THESE. Review the evidence instead.
Everything below was measured on 2026-08-10 with a control. **Re-deriving any of it is wasted
tokens.** Each row says how to *review* it cheaply if you need to; only re-run if you have changed
the code it covers.

| claim | verdict | how to review (do not re-run unless you changed it) |
|---|---|---|
| The Magma Hideout chapter completes | ‼ **1 of 3 driven runs** (see KI-50). Run 1 `groudon=True`, 0 whiteouts; runs 2 and 3 (2026-08-11) both **LOST to Maxie** (7 and 4 whiteouts). **Reaches Maxie 3/3; WINS 1/3.** The navigation is proven, the fight is not. | `07-CHANGELOG` 2026-08-10 (night); re-run only via `--driver magmahideout` from `saves/magma_door.ss1` |
| The promotion works in `custom-pokebot`, driven | ✅ `groudon=True`, identical result | `custom-pokebot/DIVERGENCE-LOG.md`, last entry |
| Source drift sandbox ↔ custom | ✅ **ZERO** (`modules/`, `plugins/` diff clean) | `diff -rq --exclude=__pycache__ sandbox-pokebot/modules custom-pokebot/modules` |
| The travel leg reaches the door and opens it | ✅ `arrived=True opened=True JAGGED_PASS_STATE=2 party_alive=6/6`, 1 whiteout | `--driver magmatravel` from `saves/post_mtpyre.ss1` (~75k frames, several minutes) |
| Full regression gate | ✅ **10 of 10 PASS** | the ten `repro_*.py` listed under HOW TO RUN / TEST |
| `saves/post_mtpyre.ss1` is the right ERA | ✅ READY (guard flag True, `MT_PYRE_STATE`=1, Emblem held; era control vs `jagged_descent.ss1` passes) | `py -3.12 probe_magma_anchor.py` — seconds, offline |
| The Jagged Pass door is walled until a coord trigger fires | ✅ decomp-verified; `calculate_path` says "2 waypoints" to a sealed tile | `12-STORYMODE-DESIGN.md` §Ch15 |
| 1F is **Strength-gated** | ✅ 3 collision components (299/70/9); the 44-tile pocket's only exits are 3 edges into boulders | `03-PUNCH-LIST` `#24-magmahideout`; `probe_ch15_interior.py` |
| The 2-push plan opens the route | ✅ end state boulders `[(4,22),(5,23),(7,22)]`, 295 tiles, goal reachable | the `MAGMA_HIDEOUT_1F_PUSHES` docstring in `early_game.py` |
| The documented "shortest route" via `1F (20,22)` | ❌ **unwalkable** — that warp is on a 9-tile island | `12-STORYMODE-DESIGN.md` §Ch15 (corrected) |
| Maxie's reachable approach tile | ⚠ **varies** — static said `(17,21)`, live said `(15,21)` | code now tries all four neighbours at runtime; do not hard-code |
| Zigzagoon can learn Strength | ❌ **False** (`can_learn_tm_hm(HM04)`) — only Mightyena & Sceptile, both full | `03-PUNCH-LIST` `#24-strength` |
| `LAVARIDGE_TOWN` reachable from `ROUTE112` | ❌ live navigator refuses 3/3 (though `calculate_path` says 66 wp) | that staging heal is best-effort by design |
| `#24-teachmsgstall` still reproduces | ✅ **0 of 3** teaches from post-battle saves vs **38 of 42** in live batch `20260810-082509` | the two `--driver teachfull` commands below |
| …and is **not** a regression from this work | ✅ the session-start commit (`320f55a5`) fails identically | already A/B'd; do not repeat |
| …and is not item-, target- or replace-slot-specific | ✅ HM04→Mightyena and HM02→Swellow fail identically | `07-CHANGELOG` 2026-08-10 (evening, part 3) |
| Upstream moved | ❌ `5dd898f8`, unchanged; checked 2026-08-10 | `40cakes repo/UPDATE-LOG.md` |

### ‼ THREE DEAD ENDS — do not re-walk them
1. **Do not try to "fix" navigation to reach the hideout door.** The door was never a pathfinding
   problem; it is a metatile the coord trigger removes.
2. **Do not add Strength to `obstacle_clearing`.** Its success test ("the object is gone") cannot
   express a push. That is why `strength_push()` exists separately.
3. **Do not chase `#24-teachmsgstall` at the replace prompt.** The failure point *moves* across
   runs (`Task_BagMenu_HandleInput` / `Task_ClosePartyMenuAfterText` /
   `Task_ClosePartyMenuAndSetCB2`), so a single broken menu step cannot be the cause. Start
   upstream of it.

## ‼‼ THE FIVE THINGS THAT WILL SAVE THE NEXT AGENT REAL TIME
1. **A flag set by a script is NOT the end of that script.** `EventScript_ActivateStrength` sets
   `FLAG_SYS_USE_STRENGTH` and then keeps running (animation, message, `releaseall`). Exiting the
   wait the instant the flag flips leaves the avatar `lockall`ed, so every button press does
   nothing. **This cost two runs** while every diagnostic looked healthy. Ride the scene out and
   wait for control.
2. **A failure message must report STATE, not a HYPOTHESIS.** Mine said "check the destination is
   walkable"; the destination was walkable all three times. Dumping the world instead
   (flag, tracked object id, every object with coords + graphics) cracked it in one run.
3. **Every static claim about the Magma Hideout has been wrong at least once.** The door read as
   "2 waypoints" while walled shut by a `setmetatile`; the "shortest route" started on a nine-tile
   island; Maxie's approach tile was `(17,21)` statically and `(15,21)` live. **Ask the planner at
   the moment it matters** — Maxie's approach now tries all four neighbours at runtime.
4. **`walk_one_tile` leaves the direction and B HELD if you abandon it early.** Release in a
   `finally`, or every later retry runs with a jammed D-pad.
5. **Track a displaced object by `local_id`, not by "is anything on that tile".** Pushing a
   boulder moves the PLAYER onto its old tile, so the obvious test reads False on success. Third
   instance of this family in the project (see `08-MISTAKES`).

## ‼ `#24-teachmsgstall` — DODGED, NOT FIXED. STILL THE BEST BUG TO FIX NEXT.
1F is Strength-gated, so the chapter needs a teach — and the natural place (inside the dungeon)
is the worst one, because that bug wedges a teach taken right after a won battle. Measured:
**0 of 3** teaches from committed post-battle saves, against **38 of 42 in live batch
`20260810-082509`**. The chapter dodges it by teaching **at a heal stop**; in the winning run
Lilycove's teach failed (logged, skipped) and Mauville's succeeded
(*"Mightyena learned Strength (lost Taunt)"*).

✅ **A far cheaper repro than the 19,000-frame fixture on file:**
```
PYTHONUTF8=1 TEACH_ITEM=HM04 py -3.12 story_harness.py magma_door.ss1 --driver teachfull --frames 400000 --profile tf-hm04
PYTHONUTF8=1 TEACH_ITEM=HM02 py -3.12 story_harness.py magma_door.ss1 --driver teachfull --frames 400000 --profile tf-hm02
```
‼ **THREE NEW FACTS.** HM02/Fly → Swellow fails *identically* to HM04/Strength → Mightyena, so
the wedge is **not item-**, **not target-** and **not replace-slot-specific**. ‼‼ **And the
failure POINT MOVES** — `Task_BagMenu_HandleInput` / `Task_ClosePartyMenuAfterText` /
`Task_ClosePartyMenuAndSetCB2` across three runs. **One broken menu step cannot do that**, which
is evidence against the standing framing ("the replace prompt never appears" — one step too
late). Also confirmed **not a regression**: the session-start commit fails identically.

## ⏭ NEXT ACTIONS, IN ORDER
1. **`#24-teachmsgstall`** — now the best-value bug in the project: a cheap deterministic repro,
   three fresh discriminating facts, and it is the only thing standing between the story bot and
   reliable HM teaching. Start upstream of the replace prompt.
2. **Build the SLATEPORT SUBMARINE beat** — Maxie's defeat opens it (`VAR_SLATEPORT_CITY_STATE`
   and `VAR_SLATEPORT_HARBOR_STATE` → 1, Stern / Gabby-and-Ty hide flags cleared). Recon it the
   way §Ch15 was: decomp first, then a driven probe, graded on a flag.
3. ~~Ask about PROMOTION~~ — ✅ **DONE 2026-08-10 night, user-approved and verified driven in
   `custom-pokebot`. Zero source drift.** The next promotion decision is whatever ships next.
4. **Do NOT grade any of this on the finish rate.** Four batches read 25.0 → 33.3 → 16.1 → 28.6%
   at n≈30 and resolved nothing. Content is binary and instantly verifiable, which is exactly
   why this session spent there.

## ‼ CARRIED FORWARD — still true
* **Ch14 hands over a WRECKED party**: `post_mtpyre.ss1` is 3 of 6 fainted, survivors at 21/117
  and 18/109, one Hyper Potion, **no Revives**, nearest Pokémon Centre 276+ waypoints away. The
  travel leg heals at Lilycove and Mauville because of it, and it still costs **one whiteout**.
  ‼ Direction matters: north over Route 121/122 is ground Ch14 already cleared (trainers beaten);
  ROUTE123/118 westward are FRESH trainers.
* **`LAVARIDGE_TOWN` is not reachable from `ROUTE112` by the live navigator** (3/3) though
  `calculate_path` scores it 66 waypoints. That staging heal is best-effort.
* **A harness driver must mirror the OVERRIDES of the mode it stands in for**, not just call its
  functions — `on_whiteout()` defaults to False (drop to Manual) while StoryMode overrides it to
  True. Two runs stopped at the identical frame before I noticed.

---

# HISTORY — 2026-08-09 (second session of the day)

## WHAT THIS IS
`sandbox-pokebot/` is the working build of a Pokémon Emerald bot. Its **Story mode** plays the
game autonomously from Littleroot. `40cakes repo/` is a pristine upstream mirror (never edit);
`custom-pokebot/` is the promoted fork. **All work happens in `sandbox-pokebot/`.**

## STATE
| | |
|---|---|
| branch / HEAD | `main`, clean, **0 unpushed** |
| box | **IDLE — nothing running.** Last batch `20260810-082509` finished ~11:25 AM 2026-08-10 (VERDICT OK, 28 runs). |
| story content | Littleroot → 6 badges → **Mt. Pyre → Magma Emblem**. Magma Hideout UNLOCKED but UNBUILT. |
| promotion | ✅ **FIVE promotions, all user-approved — `custom-pokebot` and `sandbox-pokebot` are at ZERO source drift** (the fence, `#24-progressiongate`, `#24-bosstelemetry` parts 1+2, and `#24-battleitems`). ‼ `#24-battleitems` shipped with **no resolved outcome metric** — see its DIVERGENCE-LOG entry before quoting it. |
| ‼ is code frozen? | **No — nothing is running.** The rule applies only during a batch: never edit `sandbox-pokebot/` mid-batch, because restarted lanes re-import from disk. `tools/story-dev/` and docs are always safe. |

## ‼ THE ONE NUMBER THAT MATTERS, AND HOW TO GRADE ANYTHING HERE
**Grade the counter chain on CONVERSION — hunts started vs `counter hunt CAUGHT` — never on the
finish rate and never on candidate counts.** Measuring population instead of conversion cost a
whole round (`08-MISTAKES` 2026-08-08).

‼ **And split reported vs REAL catches**: a "catch" of a species that was never hunted is a
pre-existing party mon, not a catch.
```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 -c "
import re,glob,collections
h=collections.Counter(); c=collections.Counter()
for f in glob.glob('x4-runs/<STAMP>/L0*/stdout.txt'):
    t=open(f,encoding='utf-8',errors='replace').read()
    for m in re.finditer(r'to catch ([A-Za-z]+)', t): h[m.group(1)]+=1
    for m in re.finditer(r'counter hunt CAUGHT ([A-Za-z]+)', t): c[m.group(1)]+=1
real={k:v for k,v in c.items() if k in h}
print('hunts',sum(h.values()),'reported',sum(c.values()),'REAL',sum(real.values()))
print('hunts',dict(h)); print('real',real); print('FALSE',{k:v for k,v in c.items() if k not in h})"
```
‼ Every finish-rate claim needs its **z** computed first. Seven batches now; the only resolvable
result to date is conversion 15% → 50% (z = +2.73).

## ‼ THE BATCH — `x4-runs/20260809-081643`, code `16283010`, 8 lanes / 180 min
**PURPOSE: confirm the `party_counter_slot` fence**, which reverses the `#24-slugmaspin`
regression (batch `20260808-174145`: 20 hunts, 13 *reported* catches, **3 real**; Machop
**6/8 → 0/7**). **Acceptance: REAL conversion back to ≥50%, `CAUGHT Machop` ~6/8, reported≈real.**

### ✅ RESULT — **the fence WORKS. The regression is reversed. Verdict OK, 0 header violations.**

| batch | code | REAL conversion | `CAUGHT Machop` | FALSE catches | finish rate |
|---|---|---|---|---|---|
| `20260808-095721` | `e84b814f` | 5/33 = 15.2% | 5/5 | 0 | — |
| `20260808-131334` (best before) | `def4b649` | 9/20 = **45.0%** | 6/8 | 1 | 28.6% (8/28) |
| `20260808-174145` (the regression) | `85fc8416` | 3/20 = 15.0% | **0/7** | **10** | 19.4% (7/36) |
| **`20260809-081643` (the fence)** | `16283010` | 9/23 = **39.1%** | **6/7** | **0** | 17.2% (5/29) |

**The two sharp results, both exactly what the fence was for:**
* **`CAUGHT Machop` 0/7 → 6/7 — z = +3.24, RESOLVABLE.** This is the regression itself, reversed.
* **FALSE catches 10 → 0.** Reported (9) now equals REAL (9). The fence's literal job was to stop
  counting pre-existing party mons as hunt catches, and it does, completely.
* Overall REAL conversion **15.0% → 39.1%, z = +1.76 — directional only, NOT resolvable.**
  Against the pre-regression 45.0% it is statistically indistinguishable, i.e. **restored**.

‼ **The written acceptance bar was "REAL conversion ≥50%", and it was not met — but that bar was
itself wrong.** The celebrated "15% → 50% (z = +2.73)" was computed on **REPORTED** catches. Recomputed
on REAL catches the pair is **15.2% → 45.0%, z = +2.39** — still resolvable, so the conclusion
stands, but the target to beat was always ~45%, not 50%. 39.1% sits inside that noise.

‼ **Finish rate is 17.2% (5/29), the lowest recorded — do NOT read it as a regression.** 29 binary
outcomes cannot resolve a change of this size (the whole reason conversion is the instrument), and
the counter chain is a small part of a run. Worth watching, not acting on. `global_watchdog` was
26 (vs 18 and 0 in the two prior batches) — unexplained, and the one number here that deserves a
look before the next batch.

‼ **PROMOTION IS READY BUT NOT DONE.** The 3 drifted files now have their confirmation, but
`CLAUDE.md`'s standing directive is that sandbox → `custom-pokebot/` promotion happens **ONLY after
explicit user approval**. A generic "proceed autonomously" is not that approval, and `custom-pokebot/`
is the production fork. **Awaiting a yes; everything else for it is prepared.**

## WHAT SHIPPED THIS SESSION (all pushed, each with evidence)
| item | state |
|---|---|
| **anchor manufacturing** | **DONE.** `probe_anchor_inventory.py` (reads all 60 saves; reports the map as a `MapRSE` **enum**, with a positive control) + `--driver anchorcapture` + `--driver anchorstory`. Produced `saves/mauville_prewattson.ss1`. |
| **`#24-r116sweep`** | **ANSWERED: DO NOT ADD ROUTE116.** See below — it also **closes standing concern #5**. |
| **`#24-teachmsgstall`** | ‼ **REPRODUCED locally and deterministically, and ROOT-CAUSED in code. Fix specified but NOT written** (a batch was mid-flight). |
| **KI-48 / KI-49** | two travel bugs, found and logged while doing the above. |
| docs | playbook §2b (anchors), architecture driver list, three `08-MISTAKES` entries. |

## ‼ `#24-r116sweep` — ANSWERED, AND WATTSON'S ANSWER IS "NO COUNTER"
Driven sweep from a **verified** anchor (MAUVILLE_CITY (19,15), **badge03=False**, party L16-20):
`arrived=False left=False verdict=DO NOT ADD`.

‼ **Read the failure precisely.** The JOURNEY SUCCEEDED — the bot reached ROUTE116 in ~32,000
frames and stood at **(65,11)**. The *intra-map* leg failed. `(11,7)` is
`RUSTBORO_TRAINING_GRASS`, a tile for the **pre-Roxanne** era entered from the WEST; the hunt
arrives from the EAST. `probe_r116_east_grass.py` (2 positive controls, both PASS): from the east
arrival **0 of 138** grass tiles are reachable (17/151 walkable, a pocket at x 64-78); from the
west, **136 of 138** are.

⇒ **Wattson has NO legal huntable counter.** Nincada @ ROUTE116 is unreachable from where the
hunt fires, and his other candidate sits behind him (`#24-progressiongate`). **The counter chain
stopping honestly for Wattson is CORRECT behaviour, not a gap to fix.** Beat him with levels/lead.
‼ **Do NOT relax the narrowing to manufacture a candidate** — permissiveness measured 28 wasted
treks and 15% conversion; the narrowing took it to 50%.

## ‼‼ `#24-teachmsgstall` — REPRODUCED IN ~19,000 FRAMES, ROOT CAUSE IN HAND
```
cd tools/story-dev
PYTHONUTF8=1 TEACH_ITEM=HM03 TEACH_INJECT=marshtomp TEACH_AFTER_TRAINER=1 \
  py -3.12 story_harness.py journey_r116_wedge.ss1 --driver teachfull --frames 600000 --profile tf-trainer1
```
All three `TEACH EXIT` records match the batch's byte for byte (`post-select-900-exhausted`
frame=900; `ride:hard-cap stall_peak=82` frame=8999; `not-learned-after-ride:hard-cap`; tasks
`['ListMenuDummyTask','Task_ContinueTaskAfterMessagePrints']`). **2 of 2 runs, stalling at the
identical frame f19130.**

**Condition: teach right after a WON battle** (its EXP/money message chain) — *not* trainers, and
*not* the catch/nickname prompt. Fled, caught-to-box and caught-to-party all teach fine.

**CAUSE: STILL OPEN — and three candidate causes were REFUTED today, each in minutes.** Do not
re-walk them:
1. *"`normalize_to_overworld` settles while a message is printing"* (it omits
   `Task_ContinueTaskAfterMessagePrints` from `_MENU_TASK_MARKERS`, `early_game.py:452`). Fits the
   crash signature perfectly. **REFUTED:** at the hand-off instant `message_task_active=False` —
   that task only appears AFTER the bag opens, so the gate would have been inert. A repro
   asserting it was written, committed RED, then deleted.
2. *"the parked battle script is the discriminator"* (`instr=BattleScript_PayDayMoneyAndPickUpItems`
   on the failing run vs `BattleScript_SuccessBallThrowEnd` on the passing one — at first look the
   ONLY differing field). **REFUTED:** six ordinary controllable saves nowhere near a teach report
   the identical pair, 6 of 6. `instr` is **residue of the last battle script**, not live state.
3. *"the teach's own parameters differ"*. **REFUTED:** both runs are `move=Surf slot=2
   replace_slot=1` on the same target with the same four moves.

‼ **WHERE THE DIFFERENCE ACTUALLY SHOWS — start here.** Downstream of the bag, in `TEACH EXIT`:
failing `post_select=exhausted` (the 900-frame window expires and the replace prompt NEVER
appears) with `stall_peak=82`, ending `ride:hard-cap` at 8,999; passing `post_select=replace-prompt`,
`stall_peak=171`, `ride:learned` at **463**. `stall_peak=82` against a 900 threshold means the
failing run is **CYCLING, not frozen**.
**NEXT STEP: diff the two runs frame-by-frame from the moment the bag opens** — logs are on disk
(`profiles/tf-premise/` fails, `profiles/tf-premise-pass/` passes), and they differ in exactly one
input: how the previous battle ended.

## NEW KNOWN ISSUES (both measured today)
* **KI-48** — direct navigation cannot walk ROUTE110 → MAUVILLE_CITY: 3/3 identical deterministic
  failures at (16,89); it enumerates only Mauville's **six building doors**, never the map
  connection. Story mode makes the same trip every run. A door-warp race is RULED OUT by a
  retry-after-settle A/B — do not re-test it.
* **KI-49** — journey planning is MAP-granular, so it can arrive at an entrance from which the
  destination TILE is unreachable, and nothing tries another entrance. This is what the r116
  sweep actually hit.

‼ Cross-map fixture travel failed **four** times today (Slateport→Mauville, ROUTE116 intra-map,
Fortree→ROUTE119, Mt. Pyre→ROUTE119). **Prefer an anchor already standing on the map you need.**

## ‼‼ THE STRATEGIC RESULT OF THIS SESSION — read before choosing what to do next
The counter chain's MECHANISM now works end to end: 23 hunts, **9 real catches (39.1%)**, 12
training attempts with **1** failure, false catches **0**. And it does not help:
**19 of 24 non-finishing runs (79%) still end on the chain's own "N losses with no
super-effective answer to X" stop**, and the finish rate has not moved in a week.

‼‼ **A RESULT I PUBLISHED EARLIER TODAY IS RETRACTED — read this before quoting anything about
counters.** I ran the long-specified experiment (`--driver normancounter`, a Fighting counter
injected at L18/22/26/40/55 plus a no-counter control), got **six losses**, and concluded that
beating a boss "cannot be a type-coverage or level problem". **That conclusion was wrong: all six
arms measured a mon that COULD NOT ATTACK.**
`#24-bosstelemetry` (shipped hours later) showed it on its first run:
```
[TURN  8] Machop L55 83/150 -> UseMove:Karate Chop(pp22)  vs Slaking L31 143/143
[TURN  9] Machop L55 83/150 -> UseMove:Karate Chop(pp22)  vs Slaking L31 143/143
[TURN 12] Machop L55 32/150 -> UseMove:Karate Chop(pp22)  vs Slaking L31 143/143
```
PP frozen at 22, Slaking untouched — while a natural party member in the SAME battle behaved
normally (`Mightyena -> Bite(pp24)`, Slaking 143 → 125 → 108). Cause:
`debug_create_pokemon(moves=[LearnedMove.create(...)])` builds move slots the engine selects but
never executes. With `NORMAN_MACHOP_NATURAL=1` (omit `moves=`) the same L55 Machop fights properly
— **Cross Chop, PP 5 → 4 → 3 → 2**, opponents knocked down.
‼ **What survives:** the natural-moves arm still LOST, so "a counter alone does not automatically
win" stands — but as an observation with visible causes, not as a sweeping claim.
‼ **The prevention rule is in `08-MISTAKES` and is worth the 30 seconds:** an injected fixture mon
must be proven to **ACT**, not merely to exist. Full HP, in the party, sent out — three checks, all
passing, none of which asked whether its moves worked.

## ‼ WHAT `#24-bosstelemetry` IS, AND THE TWO LEADS IT ALREADY FOUND
`modules/battle_action_selection.py` now logs **one line per turn decision** — actor + HP, the
action (move NAME and remaining PP), and the opponent with HP. It is the instrument this project
did not have: six arms could be run without learning why a fight was lost. Leads, both stated as
leads:
1. **Norman HEALS and the bot has no answer.** Slaking was ground to **27/143** and came back to
   **136/143** on turn 31; the team re-ground it with Bite/Scratch and lost. A boss out-healing
   chip damage is a different problem from type coverage.
2. **A "selected but not executed" pattern also appears on NATURAL mons mid-battle** (Cross Chop
   stuck at pp2 for three turns, Ninjask's Scratch at pp30). Could be misses (Cross Chop is 80%)
   plus a display artifact, or something real. **Undiagnosed — and now instrumented.**

## ‼‼ WHY BOSS FIGHTS ARE LOST — one hypothesis REFUTED, one CONFIRMED AND QUANTIFIED
Boss losses end **~88% of all non-finishing runs** (21 of 24 in batch `20260809-155844`), so this
is the project's dominant failure mode. Two candidate causes came out of the `normancounter` work;
batch `20260809-155844` settled both, and they went opposite ways.

**❌ REFUTED — "the bot arrives at bosses with a fainted party."** The anchor really did enter
Norman with its ace at `0/120`, and it looked like the biggest lever here. Measured directly over
**16,749 battles** with the new `[BATTLE] started hp=…` field (control: 35.5% of battles entered
at FULL health):
| | rate |
|---|---|
| entered with **>=1 mon fainted** | **6.4%** |
| entered with the **ace** fainted | **2.9%** |
| mean party HP at battle start | **90.6%** |
**One anchor was not representative.** ‼ This also retires an earlier inference-based reading that
said **99.4%** — it was deliberately never promoted to a finding because ~99% looked like a
misreading, and the direct measurement proved it was. `probe_fainted_ace.py` now reads the field.

**✅ CONFIRMED — bosses HEAL, and the bot has no answer.** `probe_boss_healing.py` reads opponent
HP out of the turn records:
* **`Slaking` healed 27 times, median +81 HP, max +119** (`24 -> 143`, `13 -> 123`, `8 -> 117`, …)
  — Norman restoring his ace from near-death to near-full while the party does **6-8 chip damage a
  turn**.
* **17.0% of boss-length battles show a LARGE (>=50 HP) heal** — i.e. trainer item usage. ‼ An earlier figure of 61.8% was INFLATED: it counted any HP increase, including an unexplained small class (+1/+2/+3) that is now quarantined in the probe. See `07-CHANGELOG` 2026-08-10.
‼ Honest edge: of 1,261 heal events, **140 are >=50 HP** (Slaking dominates, unmistakable item
usage) but **386 are <=5 HP** and mid-size ones cluster on wild species — those are **unexplained**
and no claim rests on them. The Slaking result stands alone.

⇒ **THE COUNTER CHAIN IS ANSWERING THE WRONG QUESTION.** It correctly diagnoses type coverage,
hunts, catches (34.8% conversion) and trains — and a super-effective attacker does not beat an
opponent that restores 81 HP at a time. The plausible answers are burst damage, the bot **using
its own items**, or not entering a fight it cannot close. ‼ **That is a design decision, and it is
the user's** — do not pick one unilaterally.

## ‼ `#24-battleitems` — THE USER'S DIRECTIVE: WORKING IN LIVE RUNS
**Directive: "use items intelligently and strategically."** Built because the bot was the only
side of a boss fight not using items (`Slaking` healed 27 times, median +81 HP).

**Batch `20260809-214515` (code `5a2f0182`, VERDICT OK, 27 runs) — it fires for real: 86
`[ITEM] using` events**, up from 0 by construction.
| metric | before | after | z |
|---|---|---|---|
| finish rate | 25.0% (8/32) | **33.3% (9/27)** | 0.70 |
| boss-length battle win rate | 51.1% (425/831) | **53.3% (426/799)** | 0.88 |
| counter-chain stops per run | 65.6% | **55.6%** | — |
‼ **Everything moved the right way and NOTHING is resolvable** (both z well under 1.96). Do NOT
quote a finish-rate improvement for this feature — that is the exact mistake this project has
made repeatedly at n≈30.

‼ **A REPORTED FAILURE RATE OF ~1/3 WAS INFLATED — CORRECTED 2026-08-10.** The "no HP rise"
guard compares `own_side.left_battler`'s HP at the NEXT decision against the value recorded for
the mon that requested the item — and after a faint that is a DIFFERENT POKÉMON. **9 of the 10
"both index spaces failed" cases in `20260810-035733` are immediately followed by a
`[FAINT-CHOOSER]`**: the target died, and the guard blamed the item. The true failure rate is much
lower and is not yet known. ‼ The INDEX-SPACE RULE is unaffected — it was derived from the 29
LANDINGS (HP demonstrably rising on the same mon), not from failure counts.
**Queued fix:** key the recorded HP by `party_index`, and treat "subject changed" or
`current_hp == 0` as NO VERDICT rather than as a failure (`08-MISTAKES` 2026-08-10).
Historically: 85 targeted uses completed the entire menu flow while some battles saw no HP rise. The two
index spaces disagree constantly in the logs — `(party 0, battle-order 1)` x19, `(1, 0)` x12.
Yesterday's fix (pass the party index) took the fixture from 1-of-5 landing to 3-of-3, **but
`battle_handler`'s after-faint chooser does the OPPOSITE and is correct there** (that conversion
is what fixed KI-34). ⇒ **the item-target menu and the after-faint menu are not ordered the same
way.**
✅ **ADDRESSED 2026-08-10 — the code now settles it empirically instead of by argument.** When a
use demonstrably does nothing, the strategy **flips the index space, retries once, and logs which
one landed** (`[ITEM] ✔ landed using the party-order index (HP now 120/120)`). Bounded to one flip
per battle, so a wrong first guess costs a turn rather than a loop; if both fail, items are
disabled for that battle as before. The index choice also moved OUT of `battle_action_use_item`
and INTO the strategy — the only layer that can observe the outcome.
✅ **ANSWERED by batch `20260810-035733`: the ordering is CONDITIONAL.** 68 requests →
`landed {party: 19, battle: 10}`, 20 flips to battle-order of which **10 LANDED (50%)**, 10 where
both failed. So neither convention is universally right, and the flip is doing real work — 10 of
29 landings exist only because of it. **KEEP the self-correction.**
**REMAINING: find the CONDITION.** Leading candidate — whether any party member has FAINTED, since
`map_battle_party_index` exists precisely because the game reorders the battle party on a faint.
Testable from these same logs: correlate each `✔ landed using the …-order` line against the
`[BATTLE] started hp=` field of its battle. `probe_item_index_space.py` is the starting point.
✅ **PROMOTED 2026-08-10 (user-approved); zero source drift.** ‼ It shipped with **no resolved
outcome metric** — promoted because the mechanism is proven and its failure modes bounded, NOT
because outcomes moved. See its `custom-pokebot/DIVERGENCE-LOG.md` entry before quoting it.

## ✅ THE NEXT CHAPTER IS UNBLOCKED — `#24-magmahideout` is READY TO BUILD
Built content ends at `do_mt_pyre_summit()`; there is no Magma Hideout code. That chapter was
deferred three weeks ago as *"the door is unreachable; one-way ledges"*. **That reason was wrong.**

The door at `JAGGED_PASS (16,18)` has a **Team Magma guard standing on `(16,19)`** — the column's
only entry — hidden by flag **847 `HIDE_JAGGED_PASS_MAGMA_GUARD`** (decomp `JaggedPass/map.json`).

| save | guard hidden | `(16,20)→door` |
|---|---|---|
| `jagged_descent.ss1` (badges 1-3) | False | FAIL |
| **`post_mtpyre.ss1` (badges 1-6)** | **True** | **OK, 2 waypoints** |

⇒ In the correct era the door is **2 waypoints** from a tile the bot already reaches. No scripted
movement, no navigation fix — the planner was right, it was modelling the guard.
**BUILD ANCHOR: `saves/post_mtpyre.ss1`.** ‼ Never develop this from a pre-Emblem save: doing so
cost seven probes and two wrong conclusions in one session (`08-MISTAKES` 2026-08-10). **Verify an
anchor against the STORY CLOCK, not just the map.**

## ⏭ NEXT ACTIONS, IN ORDER
1. **BUILD `#24-magmahideout` — the next unwritten chapter, now fully specified in
   `12-STORYMODE-DESIGN.md` §Ch15** (decomp-verified entry, warp graph, route, completion flag).
   ‼ **Start with INCREMENT 1: the TRAVEL LEG to Jagged Pass** — it is the only part with a
   measured failure against it (an `anchorcapture` probe from `post_mtpyre.ss1` whited out at
   f24808; that driver has no prep/heal, unlike the production path, so build it through the
   normal heal/prep machinery). Then 2: enter. Then 3: win 4F.
   ‼ **Develop from `saves/post_mtpyre.ss1` ONLY** — pre-Emblem saves have the Magma guard on the
   door's entry tile and will waste your time exactly as they wasted mine.
   **Grade it BINARY**: does `GROUDON_AWAKENED_MAGMA_HIDEOUT` end up set? No batch needed.
2. **Do NOT grade mechanism work on the finish rate.** Four batches read 25.0 → 33.3 → 16.1 →
   28.6% at n≈30; nothing resolved, ~12 hours spent. Battle-level metrics have ~800 samples per
   batch — use `probe_boss_healing.py`, `probe_item_index_space.py`, `analyse_conversion.py`.
3. **`#24-battleitems`** — ✅ promoted 2026-08-10; zero drift. ‼ Its OUTCOME is still unproven, so
   the open question is whether boss item usage actually converts fights — measure that with
   BATTLE-level metrics (boss win rate), never the finish rate.
4. **KI-48 / KI-49** — the travel bugs. KI-49 (map-granular journeys arriving at a dead-end
   entrance) is the one most likely to bite the Ch15 travel leg.
5. `#24-teachmsgstall` — reproduced deterministically, 3 causes refuted, LOW priority (zero
   run-ending events).

## ‼ THE HABIT THAT PAID OFF TODAY, AND THE ONE THAT COST
**Verify before building.** THREE punch-list items marked "ready to build" / "awaiting validation"
had already shipped (`#24-leadcounter`, `#24-counters` phase 2, `#24-r121gate`), and a three-week
deferral (`#24-magmahideout`) was wrong. All four were caught by checking the code or the decomp
before writing anything. **Treat the punch list as a hypothesis about what exists.**
**And check the STORY CLOCK on every anchor.** Seven probes ran from badges-1-3 saves to answer a
post-Mt-Pyre question, producing two confident wrong conclusions before the decomp settled it.
Name the flag that gates the content and assert it on the anchor first.


## ‼ STANDING CONCERNS (carried forward, still true)
1. **The finish rate has not moved in a week** (39.1 / 36.0 / 41.7 / 25.8 / 28.6 / 19.4%, no pair
   resolvable). Real mechanism wins are proven; **no outcome win is.** Worth deciding whether the
   counter chain is still the right place to spend, versus story content.
2. **Read the DATA, not a proxy** — eight wrong statements in nine days from this one habit.
   Today's two: `map_name` (a display *label*) read as map identity, and a detector whose callback
   could never observe the thing it tested. **The fix that works is a POSITIVE CONTROL on the
   column a decision actually reads**, plus printing how many times a check ran beside its answer.
3. **A fixture must assert it created its condition.** Three guards added today paid for
   themselves within an hour, and one of them (`trainers=0`) is the only reason the reproduction
   above was not misattributed to trainer battles.

## HOW TO RUN / TEST
```
cd tools/story-dev
# capability tests (binary, minutes) — THE PREFERRED WAY TO GRADE A CHANGE
PYTHONUTF8=1 WITHDRAW_CENTER=LilycoveCity py -3.12 story_harness.py boxwithdraw.ss1 \
  --driver boxwithdraw --frames 400000 --profile w1
PYTHONUTF8=1 SWEEP_GROUND=ROUTE116:11,7 SWEEP_RETURN=MAUVILLE_CITY:19,15 \
  py -3.12 story_harness.py mauville_prewattson.ss1 --driver groundsweep --frames 900000
# anchors: look one up, or MAKE one
PYTHONUTF8=1 py -3.12 probe_anchor_inventory.py [--filter <name>]
PYTHONUTF8=1 CAPTURE_TARGET=MAUVILLE_CITY CAPTURE_NAME=foo.ss1 CAPTURE_FORBID_FLAG=BADGE03_GET \
  py -3.12 story_harness.py slateport.ss1 --driver anchorstory --frames 900000
# offline probes (no emulation loop) — each carries a POSITIVE CONTROL
PYTHONUTF8=1 py -3.12 probe_counter_candidates_offline.py
PYTHONUTF8=1 py -3.12 probe_r116_east_grass.py
# a batch (3h, 8 lanes) — for DISCOVERING failure modes, and for conversion
PYTHONUTF8=1 py -3.12 x4_headless.py --lanes 8 --minutes 180
```
**Regression gate (ALL GREEN — re-run 2026-08-10):** `repro_battle_items` (27 checks, the item
policy), plus the counter/boss suite — `repro_counter_hunt`,
`repro_counter_huntable`, `repro_movepool_counter_candidates`, `repro_hunt_driven_grounds`,
`repro_counter_move_answer`, `repro_boss_plateau`, `repro_boss_cfg_coverage`, `repro_area_item_gate`.

## GOTCHAS (unchanged, still true)
* **Never use the Grep TOOL on `tools/story-dev/x4-runs/`** — gitignored, ripgrep silently
  reports 0. Use Bash `grep`, and print the size of what you searched as a control.
* **NAME THE SURFACE** — `*/stdout.txt` and `*/debug-logs/*.log` carry different facts; debug logs
  are copied into the run dir only when the batch ends.
* **A harness "HANG CONFIRMED" after a probe finishes is the PROBE idling, not the bot.**
* **`.sav` and `.ss1` are not the same kind of save.** A `.ss1` is a full machine snapshot and
  **does** preserve battle callbacks / mid-script state (measured, 6 of 6). "X is runtime state so
  a save can't hold it" is a claim about `.sav` only — believing it of `.ss1` cost three wedged
  probe runs.
* **Report identity as the ENUM, never the display label** — `MAUVILLE_CITY_GYM`'s `map_name` is
  literally `"MAUVILLE CITY"`.
* Never bulk-import `modules/data/*`; never route to a WARP TILE; `story_harness.py` has a UTF-8 BOM.
* `get_event_var()` returns **−1** for an unknown name — use `_done_var()` / `_done()`.

---

# ‼ BATCH 4 LANDED (2026-08-01 00:00 PDT)

`x4-runs/20260731-201554`, commit **`92d220d5`**, 8 lanes / **180.1 min**, `VERDICT OK`,
38 headers checked, **0 emulation violations, 0 lane restarts**. It completed its full bound
and self-terminated; nothing was interrupted.

## ‼ THE RESULT: the training fix FIRES, then 7/7 training runs FAIL. The funnel is FLAT.

**30 runs ended, 18 finished = 60.0%** (batch3: 20/35 = 57.1%). Badge funnel, which is the
instrument that matters:

| rung | batch3 `3875843c` | batch4 `92d220d5` | z |
|---|---|---|---|
| Stone→Knuckle | 42/43 (98%) | 35/37 (95%) | −0.72 |
| Knuckle→Dynamo | 32/42 (76%) | 31/35 (89%) | 1.40 |
| Dynamo→Heat | 31/32 (97%) | 29/31 (94%) | −0.62 |
| **Heat→Balance (beating Norman)** | 24/31 (77%) | 24/29 (83%) | **0.52** |
| Balance→Feather | 20/24 (83%) | 18/24 (75%) | −0.71 |
| Stone→Feather (whole funnel) | 20/43 (47%) | 18/37 (49%) | 0.19 |

**Not one rung is significant.** Do not read the 57.1% → 60.0% finish rate as an improvement;
it cannot resolve a change this size, which is exactly why the funnel is the instrument.

## WHY — and the blocker has MOVED AGAIN, to `KI-44`

| | batch3 | batch4 |
|---|---|---|
| `counter hunt CAUGHT` | 5 | 9 |
| `training … rejected` (old all-or-nothing gate) | 4 | **0** |
| affordable target chosen | 0 | **7** |
| `training the counter —` (training STARTS) | 0 | **7** |
| **`counter training failed`** | 0 | **7** |

`affordable_training_target` is working — it picks e.g. `Machop L15 -> L21 (team is L35, est
222115 frames)` and the refusal is gone. Training then fails **7 of 7**: six with
`Could not reach (9, 2) on MapRSE.ROUTE102 … not walkable from ROUTE103`, one to a whiteout.
**Zero counters were ever trained**, so the Machop still meets Norman at L15-16 vs L28-31 —
batch3's exact situation, hence the flat funnel.

‼ **KI-44 is EXPOSED, not caused, by the training fix.** Before it, the gate refused before
any travel was attempted, so this failure could not appear in a log. **Do not revert the
training fix.** Full detail + how to probe it in `05-KNOWN-ISSUES.md` **KI-44**.

Also new: `no money to buy any` **0 → 14** occurrences (3 ended runs) — ball starvation,
consistent with KI-43 (catches rose 5 → 9 while each restock bought 10 balls, not 30).
Clean canary: KI-38's `GAVE UP` **10 → 0**.

## ‼ KI-43 — FIXED AND PROVEN (this session)

`_navigate_when_ready` waited on a budget of 18,000 frames — **the same number as the global
watchdog's stall threshold** — while pressing nothing and changing nothing, so the derail won
by one frame every time and its `break` was dead code. It now uses its own
`_TRANSIENT_WAIT_FRAMES = 600`.

* **Structural proof:** `repro_watchdog_budget_collision.py` (no emulator) parses whichever
  constant the wrapper actually uses. Green at 600; fault-inject `60*60*5` → 3 checks red;
  restore → green.
* **Live A/B**, `gym1_done.ss1 --driver martbuy BUYN=30`, 40,000 frames:
  **OLD arm 0 purchases** (no `[buy] AFTER` line at all), **NEW arm 3 purchases + 3 Premier
  Balls**, money 8628 → 2628. The old arm parks at `(3,3)` with
  `RustboroCity_Mart_EventScript_PokemartBasic` active — the shop script keeps the avatar
  non-controllable and the wrapper waits on it silently.

`_MAX_NON_OVERWORLD_FRAMES` was deliberately left at 18,000: the outer loop waits on game
STATE, which flips during a cutscene and keeps resetting the watchdog signature, so it does
not produce the frozen signature the wrapper did.

## ‼ KI-44 — FIXED 2026-08-01 (and it was NOT a routing bug)

`train_counter` used `cfg["grass"]` — the **boss's** patch — so a Machop caught in FIERY_PATH
was sent to Norman's `PETALBURG_TRAINING_GRASS = (ROUTE102, (9,2))`. Two faults, and the log
only showed the first: it **cannot get there** (7/7 failures, stranded on ROUTE103), and
**ROUTE102's land wilds are L3-4** so it was never worth going. ‼ The obvious repair is also
wrong — FIERY_PATH / ROUTE112 / JAGGED_PASS are all `NO_RETURN_GROUNDS` (the heal leg fails),
so there was **no legal training ground at all**. Structural hole, not a wrong constant.

Fixed by `counter_hunt.counter_training_ground()` deferring to `best_training_area` — the
picker that already refuses no-return grounds, guards winnability and honours reachability.
Live-probed from `lavaridge.ss1`: relocates to **ROUTE117 (31,16) L13-14, heal Verdanturf**
("RELOCATED, fix fired"). Full detail in `05-KNOWN-ISSUES.md` KI-44.

## ‼ NEXT, IN THIS ORDER
1. **RUN A BATCH — the KI-44 fix has NO outcome proof.** `x4_headless.py --lanes 8
   --minutes 180`. Read `Heat→Balance` against batch4's **24/29 (83%)** and count
   **`counter training failed`**, which was **7 of 7**. ‼ Batch4's own lesson: the mechanism
   firing is not the funnel moving — instrument both.
2. **Two gaps in the KI-44 proof, stated so they are not mistaken for done:** the probe stood
   on LAVARIDGE_TOWN, one map short of FIERY_PATH (18,19) where the catch happens; and no run
   has yet trained a counter end-to-end.
3. **`#24-wdcanary-dedupe`** — `summarize_lane` counts `global watchdog` in stdout AND the
   debug log, so every reported figure is ~2×. Dedupe, then `--resummarise` **all four**
   batches so one instrument reads them all.
4. The KI-44 fix is **sandbox-only** — it lands after the BATCH-4 promotion, so sandbox and
   custom have diverged again by exactly this change. Promote it with the next round.

# ‼ START HERE — 2026-07-31 PM (most recent; supersedes every section below)

## READ THIS, THEN `14-AGENT-PLAYBOOK.md`. You need nothing from any chat transcript.

**Repro suite: 72 pass, 0 fail** — measured 2026-08-02 with KI-43 + KI-44 + #24-relocfloor + #24-leadpolicy + #24-pc + #24-areaitemgate in the tree, all 72
`repro_*.py` at 90 s each. ‼ `repro_x4_lanes` did NOT need skipping this time (it spawns real
lane processes and had been recorded as a by-design skip); it ran and passed on an idle box.
`repro_watchdog_budget_collision.py` (KI-43) is the newest and is GREEN as of the fix.

## WHERE WE ARE — the blocker chain, ordered by MEASURED evidence
1. ~~**KI-38** after-faint chooser~~ **FIXED 2026-07-31 AM** (`1099e9d9`). It was the reason
   runs stopped finishing. Hangs at `BattleScript_FaintedMonTryChoose` went **11/12 → 1/8**.
2. **THE RUN-KILLER IS `#24-counters`** — the counter chain correctly diagnoses
   "Norman: 6 losses, no super-effective answer to Normal, need Fighting" and **ends the run**.
   4 of 6 remaining hangs are this; it is the ~72%-of-derails item.
3. ~~**It cannot act because of KI-39** (no cross-map route planning)~~ — ‼ **THIS WAS THE
   WRONG DIAGNOSIS AND IT IS NOW CORRECTED.** See `05-KNOWN-ISSUES.md` "KI-39 — CORRECTED".
4. ~~**It cannot act because of `#24-smashroute` / KI-41**~~ — **FIXED 2026-07-31 PM.** A
   **ROCK SMASH rock** at ROUTE111 **(18,101)** sealed the Mauville→Route 112 corridor, and
   Fiery Path's only two doors are on Route 112. The bot now clears it: live A/B, OLD arm
   `arrived=False map=MAUVILLE_CITY`, **NEW arm `arrived=True map=FIERY_PATH`, 45,305 frames.**

⇒ ‼ **THE PATH TO THE COUNTER IS NOW OPEN, AND THE NEXT STEP IS TO MEASURE IT.** Both
navigational blockers are gone; whether the counter chain actually hunts, catches and trains
is **unmeasured**. Do not record it as working until a batch says so — that mistake has been
made twice here (`d7d493d8` "live-validated" on the wrong metric; KI-39's four-failures-one-
cause). Run `x4_headless --lanes 8` and read the `end_reasons` in `summary.json`.

## ‼ WHAT I GOT WRONG YESTERDAY, AND HOW IT WAS CAUGHT (read this — it is the main lesson)
KI-39 and this handoff both asserted *"the bot has NO cross-map overworld route planning"*
because *"`calculate_path` only spans directly-connected maps"*, and called a generic BFS
journey planner **"the highest-value item in the project"**. Measured live, that is false:
* `map_path.py` gives every edge-connected map a global offset and a shared `level` — Mauville
  and Routes 110/111/112/116/117 are **all level 459** — and its own docstring says it
  "supports paths across several maps".
* Reachability is **PARTIAL, not zero**: ROUTE110 **17/125** sampled tiles, ROUTE111 **11/173**,
  ROUTE117 **22/41**, VERDANTURF **14/23**. A planner that could not cross maps scores 0.

The four blocked trips had **four different causes**; only one was route planning. The original
probe ran four `calculate_path` calls, got four failures, and fitted ONE explanation to them.
**Prevention rule (now in 08-MISTAKES): a probe that returns FAIL for every case has found a
common SYMPTOM, not a common cause — make one measurement that could DISCRIMINATE before
writing a cause into this file.**

## WHAT SHIPPED 2026-07-31 PM (all pushed, all with repro + green sweep)
| item | state |
|---|---|
| `#24-x4headless` — headless ENDLESS-RESET batch runner (`tools/story-dev/x4_headless.py`) | done; `repro_x4_headless.py` |
| fix: `--endless-target` was parsed then discarded by every frontend but the tile lane | done; fault-injected AST A/B |
| `#24-journey` / KI-39 — warp planning at **MAP** granularity | done; live A/B, bot reaches Route 116 from Mauville |
| `#24-smashroute` / KI-41 — clear a field-move obstacle that seals a journey | done; live A/B, bot reaches FIERY_PATH from Mauville |
| `#24-journey` part 2 — **staged progress** (`_staged_progress_warp`) | the Mauville-only proofs were not general |
| `#24-journey` part 3 — never call `navigate_to` during a battle transition | `_navigate_when_ready`; 24 retries were burning on a transient |
| fix: TWO bugs in my own batch summariser | see below — the first batch summary was wrong |
| KI-39 corrected, KI-41 logged then fixed, **KI-42** logged + mitigated | docs |
| **USER RULING** `#24-dexhunt` = "always catch new, when it is cheap" | `06-DECISIONS-LOG` 2026-07-31 |

## ‼‼ THE RESULT — MEASURED AND SIGNIFICANT (read this first)
Three 8-lane / 180-min batches, same box, same runner:

| | baseline `289d1710` | batch3 `3875843c` | |
|---|---|---|---|
| finish rate | 23.7% (9/38) | **57.1% (20/35)** | z = 2.92 ✅ |
| whole-funnel completion (Stone→Feather) | 20% | **47%** | z = 2.71 ✅ |
| Balance→Feather (finishing after Norman) | 45% | **83%** | z = 2.67 ✅ |
| Heat→Balance (beating Norman) | 56% | 77% | z = 1.88 — directional only |
| Norman counter-chain derails | 15 | **3** | z = −3.06 ✅ |
| counter-chain share of non-finishes | 25/29 (86%) | 8/15 (53%) | |

‼ **USE THE BADGE FUNNEL, NOT THE FINISH RATE.** Finish rate is ~38 binary outcomes and can
only resolve ~+30-point changes; badge records are ~200 per batch and show WHERE runs are
lost. The early rungs were FLAT (98%/97% in both arms) with the whole change concentrated
where the counter chain and long-distance travel operate — that is what makes this credible
rather than a lucky sample, and a finish rate could not have shown it. Segment
`badge-log.json` by window (sort by `earned_at`; new batch wherever `run_index` stops
increasing).

‼ **Two caveats, recorded so they are not lost:**
* ~~`global watchdog` rose **9 → 143**. Runs travel much further now and long journeys trip
  the 18k-frame no-progress watchdog, which then recovers.~~ ‼ **INVESTIGATED 2026-07-31 PM
  AND THAT EXPLANATION IS WRONG — it is a hard regression. See KI-43.** Real figures are
  **5 → 72** (the summariser double-counts this canary). It is not travel: **35 of 72 fire
  inside `RUSTBORO_CITY_MART`** right after `bought Poké Balls`, and 31 in `LAVARIDGE_TOWN`
  right after the Heat Badge — both stationary wedges at a step boundary. Root cause:
  `_navigate_when_ready`'s escape hatch is budgeted at **exactly** the watchdog's 18,000
  frames, so the derail always wins the race and the `break` is dead code. Measured cost
  beyond the frames: the mart restock completes **0 of 36** times (baseline 33/33), so the
  bot buys 10 balls instead of 30 and loses 2 free Premier Balls per trip.
  Repro (no emulator, RED on purpose): `tools/story-dev/repro_watchdog_budget_collision.py`.
  ‼ **The fix is NOT applied** — batch `20260731-201554` was mid-flight and restarted lanes
  re-import from disk. Apply it after that batch lands, then prove with a live A/B.
* Batch3 predates `affordable_training_target` (`1c4b183d`), so all four `CAUGHT Machop`
  events still hit the all-or-nothing training refusal. **The gain above was achieved with the
  counter still entering underlevelled**, and the training fix is in NO measurement yet.

## ‼ MEASURED: THE BASELINE, AND WHAT THE FIXES DID
**Baseline** (`x4-runs/20260731-105549`, commit `289d1710`, 8 lanes, 180 min, 46 runs started):
* **38 runs ended, 9 finished = 23.7%**
* **25 of 29 non-finishes (86%) are the counter chain** naming an answer it cannot reach —
  Norman/Fighting **15**, Winona/Rock-Ice-Dragon **5**, Wattson/Ground **5**. Everything else
  is 4 events, one each. This CONFIRMS the handoff's old "~72% of derails" and sharpens it.
* KI-38 `GAVE UP` 20 with `NO ELIGIBLE REPLACEMENT` 1.

**Post-fix batch** (`x4-runs/20260731-140514`, commit `1b9e690f`) — the counter hunt **FIRES**
for the first time (`counter hunt — going to FIERY_PATH (18, 19) to catch Machop`, 4× in the
first 8 runs; baseline had it 0×) and then **fails to travel**. That is what produced the
staged-progress work below; the batch predates it.

## ‼ TWO BUGS WERE IN MY MEASURING INSTRUMENT — CHECK YOURS
The first summary of the baseline claimed **69% finish rate** and showed the counter chain
**zero** times. Both wrong; the raw logs were fine.
1. `COLUMNS=400` was set to stop rich wrapping the outcome lines and **was not enough** (a
   counter derail message is ~1,000 chars). The `(N frames) ===` tail landed on the next line.
   **And `repro_x4_headless.py` asserted that a wrapped line IS unparseable** — the workaround
   pinned as intended behaviour, so the suite defended the bug. Parser is wrap-tolerant now.
2. Batch totals used `Counter({k: v for lane in lanes ...})` — an inner **dict comprehension**,
   so a reason in several lanes kept only the LAST lane's count. It reported 9 end reasons for
   29 non-finishing runs; every number looked plausible and only the arithmetic exposed it.

`x4_headless.py --resummarise <dir>` re-reads stored logs. **The logs are the data; the summary
is only a reading of them.** Never re-run hours of emulation to fix a regex — it also produces
a different sample and destroys the comparison.

## ‼ I CAN RUN BATCHES ON THIS BOX — THIS CHANGES HOW TO WORK
mgba is **vendored** at `sandbox-pokebot/mgba/`. Measured throughput **~1,211 fps per lane**;
a full 3.5M-frame run is ~45 min. Box is a Ryzen 9 5950X, 16C/32T, 128 GB — 8 lanes is
comfortable (4 lanes ≈ 4 cores); don't max it out.

**USE THIS ONE — `tools/story-dev/x4_headless.py` (built 2026-07-31):** N parallel lanes of
**the user's own mode**, `Story (ENDLESS RESET)`, headless.
```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 x4_headless.py --lanes 8 --minutes 180
PYTHONUTF8=1 py -3.12 x4_headless.py --lanes 4 --runs 5      # 5 runs per lane, mirrors the GUI
```
* `--lanes 4` = the dashboard's `torchic/mudkip/treecko/random`; `--lanes 8` = **2 per starter
  + 2 random**, doubling per-starter sample size (needed for starter-specific bugs like
  `#24-starter-gym3`: Treecko stalls at Wattson in 11 of 14 runs, Mudkip never does).
* Refuses to run unbounded — give `--minutes` and/or `--runs` (runs PER LANE).
* Output `x4-runs/<stamp>/`: `MANIFEST.txt`, `summary.json` (finish rate, **grouped
  end-reasons**, KI-38/KI-40 canaries, battle-outcome tally, losses by map), per-lane
  `stdout.txt` + this window's debug logs. Root `INDEX.md` + `LATEST.txt` record each batch's
  **COMMIT HASH** — never compare a batch to code it did not run.
* ‼ It **asserts** `emulation: speed=0 video=True` from every run's RUN HEADER, all batch long,
  and aborts loudly on a violation. A lane at 1x is ~20x slower and looks exactly like a hang.
  Do NOT add speed/video forcing to the runner — see `06-DECISIONS-LOG` 2026-07-31 for why
  verification beats duplication here.

`tools/story-dev/livetest.py` still exists and drives **plain `Story`**, where a `BotModeError`
drops to Manual and the run ENDS. ‼ **Its finish rates are HARSHER than the user's and are not
directly comparable** — that is exactly the gap `x4_headless.py` closes. Prefer `x4_headless`
for anything that will be compared against a user bundle.

## HOW TO READ A HANG (learned the hard way, twice, 2026-07-30/31)
* ‼ **A state trace shows where the bot IS, never why it got there.** `ctrl=<none>` +
  `bot_mode=Manual` means only "no controller is driving the game" — the mode already exited.
  **The `*** BotModeError -> Manual:` line in stdout names the cause.** Reading
  `BattleScript_LocalBattleLostEnd` as "a whiteout bug" was wrong; it was the counter chain's
  honest stop, and the whiteout screen was just what was left on screen.
* ‼ **Probe with the SAME call the production path uses.** `calculate_path` cannot cross warps
  and says so in its own error text; using it to test reachability nearly retired a working
  feature (08-MISTAKES 2026-07-30).
* ‼ **State the METRIC beside any "validated" claim.** `d7d493d8` was recorded as
  live-validated on *"no unrecovered errors"* and was simultaneously finishing **0%** of runs.
  A failure metric can be driven to zero by better recovery while the bot makes no progress.

## WHAT SHIPPED 2026-07-30/31 (all pushed, all with repros)
| item | state |
|---|---|
| `#24-counters` step 1 — hunting-ground gate (`hunt_ground_tile`/`huntable`/`best_huntable`) | done; blocks the executor from walking into Victory Road |
| `#24-counters` step 2 — executor (`counter_hunt.py`, `_counter_ladder`, catch-on-sight) | done; **inert until KI-39** |
| `#24-counters` step 2b — destination fallback (max 3, cheap failures cascade) | done |
| `#24-reprorot` — 4 "environmental" repros were 4 different rots | done; suite green |
| `#24-menuorder` — Story block + ×4 controls at TOP of the Bot-mode popup | done (user request) |
| KI-38 mitigation A — `FAINT_CHOOSER_GIVEUP_LIMIT` 3→20, clamped 200, env-tunable | done; insufficient alone |
| **KI-38 real fix — chooser LEARNS refusals** | **done, live-confirmed** |

## ‼ NEXT, IN THIS ORDER
1. ~~**Headless ENDLESS-RESET runner**~~ **DONE** — `tools/story-dev/x4_headless.py` (see the
   batch section above). Video question ANSWERED: `-hl` removes the GUI **window**, not the
   **renderer**; `PokebotHeadless.run()` sets `context.video = not no_video`, and
   `_apply_debug_emulation_config()` forces `video=True` anyway. Confirmed live —
   `emulation: speed=0 video=True` on every lane header of every run of an 8-lane batch.
2. ~~**`#24-journey`**~~ **DONE** — warp planning at MAP granularity. ‼ Do NOT retry gateway
   waypoints (refuted 2026-07-30) and do NOT build the full leg-list planner KI-39 sketched
   (rejected with reasons in `06-DECISIONS-LOG` 2026-07-31).
3. ~~**`#24-smashroute` (KI-41)**~~ **DONE** — the bot clears the ROUTE111 (18,101) rock and
   reaches Fiery Path. ‼ Only **Rock Smash** is actionable; **Strength is excluded on purpose**
   (a boulder is pushed, not removed, so the success test cannot see it) and Cut is
   known-but-unvalidated — both recorded in `obstacle_clearing.KNOWN_BUT_UNSUPPORTED`.
4. ✅ **`#24-counters` MEASURED — and the blocker has MOVED to training.** Batch
   `x4-runs/20260731-170603` (commit `3875843c`) shows the chain working end to end through
   the CATCH, three times:
   ```
   Story: counter hunt CAUGHT Machop (slot 5).
   Story: training Machop to L35 rejected — estimated 1693806 frames exceeds the
          budget (250000). It joins the fight at L16.
   ```
   Diagnose → travel to Fiery Path → **catch the Machop** → field it at **L16 vs Norman's
   L28-31**. **Balance Badges that batch: 0.**

   **Shipped:** `affordable_training_target()` — the gate was ALL-OR-NOTHING and a fresh catch
   is ~15 levels below the team BY CONSTRUCTION, so it resolved to "don't train" every time
   (the cost of catching with the benefit of neither option the user priced). It now buys the
   highest level the budget covers. `repro_counter_training_budget.py`, 14 checks, no emulator.

   ‼ **AND THAT IS NOT SUFFICIENT — the next step is a DECISION, not a fix.** Measured
   ~**89k frames per level**:
   | budget | levels bought | result |
   |---|---|---|
   | 250,000 (current `MAX_PREP_TRAINING_FRAMES`) | 2 | L18 vs L28-31 |
   | ~890,000 | 10 | L26 — a real answer |

   Three options, priced in `07-CHANGELOG.md` 2026-07-31: raise a counter-specific budget;
   rank counter candidates by LEVEL GAP (more principled, raises no budget); or accept the
   underlevelled counter and lean on 2× STAB.
   ‼ **MEASURE THE THIRD ONE FIRST** — it is binary and costs minutes, and if an L18 counter
   beats Norman the other two are unnecessary:
   ```
   cd tools/story-dev
   NORMAN_MACHOP_LEVEL=18 PYTHONUTF8=1 py -3.12 story_harness.py \
       prenorman_fodder_grind.ss1 --driver normancounter --frames 800000 --profile repro-live3
   ```
   Sweep the level (18 / 22 / 26) to find where it starts winning — THAT number is what the
   budget or the candidate ranking has to deliver.

5. ✅ **`#24-journey` IS COMPLETE.** From `norman_done.ss1` (PETALBURG_CITY — the position the
   Norman ladder actually fires from), through the production call path:
   `RESULT arm=new arrived=True map=FIERY_PATH`.

   The arc, all measured from Petalburg:
   | step | how far |
   |---|---|
   | start of day | ends the run; no travel attempted |
   | map-granular warp planning + staged progress | ROUTE116 |
   | no `navigate_to` during battle transitions | ROUTE116 (47,9) |
   | prefer doors leading somewhere NEW (`pick_leg`) | ROUTE116 → FIERY_PATH |
   | obstacle search re-runs PER MAP | **PETALBURG → FIERY_PATH, arrives** |

   ‼ **Four of the five bugs were introduced by me the same day.** The one worth internalising:
   an `obstacle_search_exhausted` latch justified with *"riding out a scene cannot create new
   rocks, so one empty answer is final for this trip"* — true for scenes, **false for
   journeys**. It searched once in Petalburg (correctly empty), latched, then walked seven maps
   and stopped standing on the map whose rock seals the corridor, with the feature off.
   **An optimisation whose justification contains the word "cannot" deserves a second look.**

   Reproduce (anchor save `journey_r116_wedge.ss1` is the SHORT version, ~5 min;
   `norman_done.ss1` is the full journey, ~30 min):
   ```
   cd tools/story-dev
   SMASH_ARM=new SMASH_TARGET=FIERY_PATH:18,19 PYTHONUTF8=1 py -3.12 story_harness.py \
       journey_r116_wedge.ss1 --driver smashroute --frames 700000 --profile repro-live4
   ```
5. `#24-dexhunt` / `#24-pc` / team-PC-reserve — the "travel to a known place on request"
   capability they were gated on now exists, but they are still gated on the **ruling below**.

## USER RULINGS — DO NOT RE-ASK
`#24-counters` → price both, then catch-and-train Fighting; `#24-leadpolicy` → **A+C**;
`#24-route110cap` → **A**; KI-24b → **A**; `#doc-policy-05` → **A**; repo size → leave it;
debug modes → unthrottled + video ON; `xp_rate` is the default fodder rule.
`#24-dexhunt` → **RULED 2026-07-31: "always catch new, WHEN IT IS CHEAP."** Catch every unseen
species EXCEPT when it would block progress. ‼ This **supersedes `21-TEAM-POLICY-DESIGN.md`
§1**'s scored random roll — update that section, don't leave two docs disagreeing. "Cheap" is
defined, not left to judgement: reuse `counter_hunt.resource_blocker()` (spare balls with the
last one reserved; party space, since a full party means the catch goes to a box the bot
cannot manage until `#24-pc`; and never mid boss-prep). A skip must LOG ITS REASON — a silent
"no" is indistinguishable from "the feature isn't running", which has cost this project time
three times now (KI-24, KI-42, KI-39). Full rationale + the two rejected options in
`06-DECISIONS-LOG.md` 2026-07-31.
**NOTHING IS STILL OWED.** Every open ruling has been answered.

# ‼ START HERE — 2026-07-30 (most recent; supersedes the sections below)

## READ THIS FIRST, THEN `14-AGENT-PLAYBOOK.md`. You need nothing from any chat transcript.

## WHERE WE ARE
The Story bot **reliably reaches Winona / Gym 6 = end of built content, and has beaten her.**
A long fix campaign on the batch harness and on double battles is **complete and confirmed
live**. The last two logs (`20260730-095944`, `20260730-105452`, build `d7d493d8`) show **no
unrecovered errors**. The agreed next step is to **build story content past Winona**, starting
with the counter chain.

‼ **"No unrecovered errors" is not "clean".** The recovery machinery is doing real work — about
six derail events in one 3.15M-frame run, all six recovered. The underlying causes are
survivable, not gone. Do not read a quiet run as proof they are fixed.

**GUI, 2026-07-30 (user request):** the Play tab's `Bot mode ▾` popup now opens with
**Manual → STORY block (the 4 Story modes + Endless Debug-Reset + Endless Loop ×4 + Park ×4)
→ OTHER MODES**. Park and Stop used to be the last two entries, under the greyed-out modes.
Ordering lives in the pure `dashboard_gui.build_mode_menu_plan()`, asserted by
`repro_mode_menu_order.py`. ‼ Entries keep a FIXED position — non-selectable Story modes are
greyed IN PLACE, and `Park ×4` is always shown (greyed when idle), because hiding it changed
the block height and shifted everything below it.

**Since then (2026-07-30, this session):** `#24-counters` phase 2 **step 1 is done** — the
hunting-ground gate that any travel-and-catch executor must sit behind (details in "NEXT"
below). Two load-bearing beliefs in this file were also found to be FALSE and corrected:
**this box has mgba** (vendored at `sandbox-pokebot/mgba/`), and **counter candidates are not
all `tile: None`**. No bot behaviour has changed yet — nothing travels or catches.

## WHAT WAS FIXED IN THIS CAMPAIGN (all live-confirmed unless noted)
| fix | evidence |
|---|---|
| per-run state reset | `couldn't beat the Rustboro rival` **31 → 0** |
| honest outcomes (`stopped:` vs `finished`) | dead runs no longer report success |
| `run_index` stride 1 | was all-odd stride 2 |
| in-run frame budget + raise to 5M (KI-35) | a WINNING run used 3,058,007 frames = 87% of the old 3.5M cap |
| KI-32 in-battle stall blindness | stall dumps now fire in battle — **this is what caught KI-34** |
| **KI-34** after-faint chooser index-space bug | `GAVE UP` **3,975 → 3**; `[orders DIVERGE]` confirms the diagnosis |
| **KI-37** listener starving the mode | worst stall **1,182,000 → 111,000** frames; hand-overs now claimed |
| self-describing debug logs (RUN HEADER) | build/ROM/emulation/active-rule in every log |
| debug modes force unthrottled + video ON | video is load-bearing: the faithful PokéNav path needs the renderer |

## ‼ THE FIVE RULES THAT MATTER WHEN YOU TOUCH THIS CODE
1. **Never `raise` from battle code.** It is a SIBLING of the mode on a FLAT controller stack, so
   a `BotModeError` reaches `main_loop` and forces Manual. Use
   `modules/battle_fault.py` → `request_mode_recovery()`.
2. **Every listener that can sit above the mode must honour `battle_fault_pending()` and be
   bounded.** Forgetting this caused KI-37 — a deadlock worse than the wedge it followed.
   `BattleListener` and `TrainerApproachListener` now do; **others are UNAUDITED**.
3. **Bound the OUTCOME, not the frames.** A bounded loop re-entered by its dispatcher is still
   infinite (KI-34 burned 23.9M frames that way).
4. **Prove two integers share a coordinate system before comparing them.** Party-menu indices
   and `get_party()` indices DIVERGE; `map_battle_party_index()` converts. This caused KI-34.
5. **Never write a game fact from memory** — decomp or live probe only.

## STILL OPEN (see `05-KNOWN-ISSUES.md`, 39 entries)
- **KI-38** — 3 residual after-faint give-ups. `presses={'Down': 3, 'A': 273}`,
  `cursors_seen=[0,2,3,7]` in a 4-mon party; cursor 7 is probably the CANCEL entry. The data
  cannot separate "wrong target" from "right target, refused". **`#24-menutext` (the user's
  text-detection fallback) is the thing that resolves it — string MUST come from the decomp.**
- **KI-36** — only NETTED. The per-run frame budget is a GENERATOR wrapper and cannot fire while
  a battle handler is on top of the flat stack. Currently netted by `debug_logger`'s stall
  detector at 60,000 frames, **which only works while debug logging is ON**. A
  stack-independent budget in `main_loop` is the complete fix.
- **New, unexplained:** a wild **Slugma** encounter wedged 111,000 frames (log `20260730-095944`).
- KI-25 (defensive-only lead), KI-26 (Route 110 rival: no prep/cap), KI-27 (Weather Institute
  hang), KI-28 (training livelocks), KI-29 (P4 canary), KI-31 (fodder gate), KI-33.

## ‼‼ STOP — READ THIS BEFORE ANY FEATURE WORK (2026-07-30, evening)

**RUNS STOPPED FINISHING: 48% → 0%.** Root-caused to **KI-38** (see `05-KNOWN-ISSUES` KI-40):
the after-faint chooser cannot select a living replacement, gives up, and **abandons an ACTIVE
battle** with the party menu open. The mode gets a fault its recovery cannot act on, recovery
re-enters the same step, and the run wedges. Measured `NO ELIGIBLE REPLACEMENT` = **0** with
`GAVE UP` at **~22/h** — a valid target always existed.

| build | limit | watchdog/h | runs finished |
|---|---|---|---|
| `21b587f1` | none | 0.4 | **48%** |
| `d7d493d8` | 3 | ~20 | 0 of 2 |
| `ffb062ce` | 3 | ~29 | 0 of 30 |

* **MITIGATION A SHIPPED:** `FAINT_CHOOSER_GIVEUP_LIMIT` 3 → 20 (clamped 200, env-tunable).
* **THE REAL FIX IS `#24-menutext`** — now the #1 punch-list item.
* ‼ **The 2026-07-30 counter-chain and menu commits are CLEARED** by controlled A/B — the
  regression predates them, in the KI-34/35/36/37 work.
* ‼ **`#24-counters` and `#24-journey` are BOTH ON HOLD.** Neither matters while runs die at
  Gym 2. Do not resume them until the finish rate is back.
* ‼ **`d7d493d8` was recorded here as "live-validated" and was NOT** — that verdict was
  measured on *"no unrecovered errors"*, never on finish rate. **State the METRIC beside every
  validated claim, and make one of them an OUTCOME metric** (08-MISTAKES 2026-07-30).

## ‼ NEXT, IN THIS ORDER (agreed with the user 2026-07-30)
1. **`#24-counters` phase 2 — the biggest lever by far.** ~**72% of all derails** are the counter
   chain correctly NAMING the answer it needs and then ENDING THE RUN. **User ruling: price
   both options, then catch-and-train a Fighting type for Norman** (not potions).

   ✅ **STEP 1 DONE 2026-07-30 — the hunting-ground gate.** `training_areas.HUNTING_GROUNDS`
   + `hunt_ground_tile()`; candidates now carry `huntable`; **`counter_plan.best_huntable()`
   is the ONLY selector an executor may call.** `repro_counter_huntable.py` — ALL PASS.
   It had to land first: the cost model prices "train it up to the team's level" at ~0 for a
   wild ALREADY ABOVE the team, so it **ranks endgame maps as cheapest** — rank 1 for Norman
   is **Hariyama @ VICTORY_ROAD_B1F L38-42**. Building the executor on `cands[0]` would have
   walked a mid-game team into the E4 approach, and reachability would NOT have stopped it
   (live from the Winona save, `_counter_area_allowed` calls Magma Hideout / Shoal Cave /
   Safari Zone reachable, 10/10). Closes punch-list blockers (1), (3), (4).

   ‼ **The old blocker (1) claim — "every candidate has `tile: None`" — was FALSE.** All
   three measured derail classes now resolve to a swept, walkable destination:
   | Norman → Fighting | **Machop @ FIERY_PATH (18,19)** ← matches the user's ruling |
   | Wattson → Ground | **Sandshrew @ ROUTE111 (25,55)** |
   | Winona → Rock/Elec/Ice | **Electrike @ ROUTE118 (29,15)** |

   ✅ **STEP 2 DONE 2026-07-30 — the executor.** New `modules/story/counter_hunt.py`
   (arm → hunt → train), `StoryMode._counter_ladder`, and a catch-on-sight branch in
   `on_battle_started` cloned from the `HM_CATCH_TARGET_DEX` one.
   `repro_counter_hunt.py` — **15 checks, ALL PASS.**
   ‼ **THE BOUND: one hunt per boss per run, held in `self._counter_hunts`** (cleared by
   `reset_per_run_state`). A retry or frame budget CANNOT bound this — the chain fires from
   inside `_prepare_for_fight`, which the run loop re-enters after every lost attempt, so
   any per-call budget becomes per-attempt. **That is the KI-34 shape that burned 23.9M
   frames.** The attempt is recorded BEFORE the hunt runs, so a hunt that derails mid-flight
   still consumes its one chance.
   ‼ **Rung 3 (train) is load-bearing, not garnish.** With a Fighting type in the party
   `_boss_plan_is_hopeless` stops firing, so shipping the catch WITHOUT the training would
   have been a regression: the honest stop goes quiet and the bot re-attempts Norman with an
   untrained L15 Machop until the 5M-frame budget kills it.
   ‼ **The terminal raise at `story_mode.py` is untouched** — every failure path
   (no huntable candidate / party full / no spare ball / planner throws / hunt finds nothing
   / already hunted this run) still stops honestly.

   ✅ **STEP 2b — DESTINATION FALLBACK (2026-07-30).** `probe_counter_reachability.py`
   drives the REAL navigation from verified anchors and measured this:
   | rung | destination | driven navigation |
   |---|---|---|
   | **Norman → Fighting** | Machop @ FIERY_PATH (18,19) | ✅ **ARRIVED, 2,922 frames** |
   | Wattson → Ground | Sandshrew @ ROUTE111 (25,55) | ❌ failed, 255 frames |
   | Winona → Rock/Elec/Ice | Electrike @ ROUTE118 (29,15) | ❌ failed, 255 frames |
   So two of three bosses were burning their one hunt on an unreachable place. The ladder
   now walks `counter_plan.huntable_candidates()` in rank order, up to
   `COUNTER_HUNT_MAX_DESTINATIONS = 3`.
   ‼ **Cheap failures cascade, expensive ones do not.** A navigation failure (~255 frames,
   one place) tries the next destination and is recorded in `_training_unreachable`; an
   *arrived-but-caught-nothing* (a full 120,000-frame spin) does NOT cascade; a resource
   wall (full party / no spare ball) stops the ladder outright.
   ‼ **`calculate_path` CANNOT answer a reachability question about a destination behind a
   WARP** — it plans only across directly-connected maps and says so in its error text.
   Probe with `_navigate_riding_out`, which is what the executor actually calls
   (08-MISTAKES 2026-07-30).

   ‼‼ **READ KI-39 BEFORE JUDGING THIS FEATURE (found 2026-07-30, after the build).** The
   bot has **no cross-map overworld route planning**: the whole Hoenn overworld is region
   **0**, so `navigate_to_anywhere` always takes its same-region branch and hands the trip to
   `calculate_path`, which only spans DIRECTLY CONNECTED maps. Measured from Mauville:
   ROUTE117 (adjacent) OK; ROUTE110 (joined via a gate building = warp) FAIL; ROUTE116 FAIL;
   ROUTE111-north FAIL. Long journeys work today only because the chapters hand-code them.
   **Consequence: the counter hunt can only reach a destination a leg or two away.** Fiery
   Path arrives in 2,922 frames from **Lavaridge**, but Norman is fought at **Petalburg** —
   so even the rung measured "live" is probably inert at the moment it actually fires.
   **Expect the chain to stop honestly far more often than it hunts. That is KI-39, not the
   executor failing.** Tracked as `#24-journey`, now the biggest structural blocker: it also
   gates `#24-dexhunt`, `#24-pc`, `#24-catchcap` and the whole team/PC-reserve plan.
   ‼ Do NOT attempt gateway waypoints — tried and refuted (`probe_counter_gateway.py`).

   ⏭ **WHAT IS OWED NOW: A LIVE RUN.** Nothing proves the bot can actually walk to Fiery
   Path from Petalburg, catch a Machop and beat Norman with it. On the next batch, grep for
   `counter hunt` and `already hunted a counter`, and check in this order:
   1. Does a hopeless verdict now produce a HUNT rather than an immediate stop?
   2. Does the hunt reach FIERY_PATH (18,19), and does the catch-on-sight branch fire?
   3. Does `train_counter` accept or decline the frame estimate (it logs both)?
   4. ‼ **The regression to fear:** a boss that used to stop honestly now LOOPS. The
      per-run bound is what prevents it and `repro_counter_hunt` case 2 is its proof, but
      only a live run exercises the real re-entry path.
   ‼ **SET EXPECTATIONS BEFORE READING THE LOGS.** Norman's rung is proven live; **Wattson
   and Winona's FIRST choices are proven unreachable**, so those fall back to a second
   destination that may itself be declined by the frame-cost gate (Wattson's Route 116
   Nincada is L6-7 for an ~L20 team: est. 355,384 frames vs a 250,000 budget). **A Wattson
   derail in the next batch is NOT evidence the executor failed** — read the log line, which
   names which rung was tried and why it stopped. Expect the Norman case to be the one that
   demonstrates the full arm → hunt → catch → train chain.
2. **Then the next chapters: Mt. Pyre → Magma hideout** (`12-STORYMODE-DESIGN.md`).
   MAP FIRST (static recon → Area Atlas → build → validate) — playbook §4.
3. **Then the team/catch work** (`#24-dexhunt`, `#24-maintain`, `#24-catchcap`), which share
   machinery: `encounter_index`, `hunt_mode`, `training_areas`, and the **built-but-UNWIRED**
   `modules/story/team_policy.py`.
4. **Then overnight x4 sweeps** and review, per `14-AGENT-PLAYBOOK.md` §2c.

## USER RULINGS ALREADY GIVEN — DO NOT RE-ASK (`06-DECISIONS-LOG.md` 2026-07-29/30)
`#24-counters` → price both, then catch-and-train Fighting; `#24-leadpolicy` → **A+C**;
`#24-route110cap` → **A** (prep, **NO** cap); KI-24b → **A**; `#doc-policy-05` → **A**;
repo size → **leave it**; debug modes → unthrottled + video ON; `xp_rate` is the **default**
fodder rule (`POKEBOT_FODDER_RULE=legacy` reverts).
**One ruling still owed:** `#24-dexhunt` asks for ALWAYS-catch-new, while
`21-TEAM-POLICY-DESIGN.md` §1 specifies a SCORED RANDOM roll so runs differ. They cannot both
be the rule.

## ENVIRONMENT — this box
- Tests: `py -3.12 tools/story-dev/repro_<name>.py` (plain `python` is 3.9 and will fail).
- ‼ **Full sweep is GREEN: 59 pass, 0 fail, 1 skip** (60 scripts; `repro_x4_lanes`
  SPAWNS REAL LANE PROCESSES — skip it). Measured 2026-07-30 after `#24-counters` step 2.
  **The old "5 environmental" expectation is retired — treat ANY failure as real.**
  Expect the sweep to take ~20-25 min now: four repros that used to bail out early
  actually run their emulators.
- **What "environmental" was hiding** (`#24-reprorot`, DONE — full detail in `07-CHANGELOG`
  and two `08-MISTAKES` entries): four different rots, no production bug in any of them,
  and **none ever needed an emulator it did not have** — all four launched mGBA 0.10.2 fine.
  Two of `repro_sufficiency`'s four faults produced **no crash at all**, because the code
  under test sits inside `except Exception: pass` — a missing stub attribute became a
  silently WRONG VERDICT. A test that quietly stops testing looks exactly like one that passes.
  ‼ **When you write a repro that stands in for `StoryMode`, copy `_StoryModeStub`** (in
  `repro_boss_training.py` / `repro_sufficiency.py`): it HARVESTS every UPPERCASE constant
  instead of hand-listing them, BINDS real methods rather than re-stubbing their verdicts,
  and raises a self-explaining error when the code grows a new dependency.
- ‼‼ **THIS BOX *DOES* HAVE mgba — the old "no mgba here" claim was FALSE** (corrected
  2026-07-30, `08-MISTAKES.md`). It is **vendored in the repo** at `sandbox-pokebot/mgba/`,
  so a bare `import mgba` from the repo root fails while every repro — which puts
  `sandbox-pokebot` on `sys.path` first — succeeds. Verified: `repro_counter_wiring.py`
  loaded a real save state, ran frames and read live party/flag data here.
  **Live validation belongs HERE, not deferred to the user's machine.** Re-check any
  "environmental" repro and any "must be validated live elsewhere" note written before
  this date.
- ‼ **Run repros with `PYTHONIOENCODING=utf-8` when capturing output.** They print `‼`
  and em-dashes; through a PIPE Python falls back to cp1252 and dies with
  `UnicodeEncodeError`, which a test harness will report as a FAILING REPRO. Cost an
  entire bogus red sweep on 2026-07-30.
- ‼ **The user runs the bot from a DIFFERENT MACHINE** and pulls with `install_sandbox.py`
  (which does `git fetch` + `git pull --ff-only`). Commits here do not reach it until they pull.
- **Revert point:** tag `backup/pre-trainmap-2026-07-29` (on origin). Recipes in §0-BACKUP.

# START HERE — 2026-07-27 (HISTORY — superseded by the 2026-07-30 section above)

## 0. ✅ THE FIXES ARE DEPLOYED AND VALIDATED LIVE (2026-07-29, five bundles)

The running machine pulled. Five bundles reviewed (`20260727-164830`, `20260728-172826`,
`20260728-221523`, `20260728-222654`, `20260729-062040`). **All four harness fixes are
confirmed working in production:**

| fix | evidence across the five bundles |
|---|---|
| per-run state reset | **`couldn't beat the Rustboro rival` : 31 → 0.** P2 hit it 31 times in 32 runs on 07-27; **zero** in every bundle after. Runs 4+ now play. |
| frame budget enforced in-run | max single-run frames now **1.9M–3.1M, all under the 3.5M cap**. The 27M/30M-frame hangs are gone. The budget fired once (P3, 07-28) and the batch continued. |
| `run_index` stride | **stride 1 in all four lanes** in the newest bundle (was all-odd stride 2). |
| honest outcomes | derails are now itemised and attributable (36 in the last bundle) instead of hiding behind `finished`. |

**Throughput, newest bundle (56 runs across 4 lanes):** P1 5×Feather, P2 5×Feather,
P4 4×Feather, P3 2×Feather. Reaching end-of-built-content went from a once-per-batch event
to **16 times in one batch**.

## 0-BACKUP. ‼ REVERT POINT — `backup/pre-trainmap-2026-07-29`

An annotated git tag marking the last known-good state before the `#24-trainmap+`
training-area work. **Pushed to origin**, so it survives this machine.

State at that tag: all four x4 harness fixes validated live; `team_policy.py` built (pure,
unwired); repro suite 48 pass / 0 fail / 5 environmental; docs 00/01/02/03/05/14/21 audited.

```bash
git diff backup/pre-trainmap-2026-07-29                 # what changed since
git revert <sha>                                        # undo one commit  (PREFERRED)
git checkout backup/pre-trainmap-2026-07-29 -- <path>   # restore ONE file
git worktree add ../revert-check backup/pre-trainmap-2026-07-29   # inspect the whole tree
git revert --no-commit backup/pre-trainmap-2026-07-29..HEAD && git commit   # full rollback
```

‼ **Never `git reset --hard` a pushed branch, and never force-push** — the batch machine
pulls from this remote, and the project rule forbids rewriting published history. Every
recipe above is additive.

## 0a. Deployment — RESOLVED, but keep the check

**The repo you are editing is not the repo that runs.** This checkout is
`C:\Remote Projects\Pokebot_Gen3_Enhancement`. The bot runs from

    C:\Users\Ripto\OneDrive\Documents\Pokebot Gen 3 SECOND RUNNING PROFILE\
        Pokebot_Gen3_Enhancement_old\sandbox-pokebot\

(seen in every lane's stdout header and debug-log path). The 2026-07-26/27 fixes are
committed and pushed HERE, and the `20260727-063751` batch — launched from THERE — still ran
the old code: runs 4+ `finished (0 frames)`, `run_index` stride still 2.

‼ **That path does not exist on this machine** (checked 2026-07-27) — the bot runs on the
user's OTHER, more powerful computer. So this is not a local sync you can perform: the fixes
must be pulled on THAT machine before the next batch.

**Before any further batch is meaningful, the running machine must pull `main`** (currently
`9074bb09`). Until then every bundle will re-report the same already-fixed bugs and no fix
can be validated. **Say this to the user explicitly and early — do not bury it in an
analysis.** Two consecutive bundles have now been reviewed against code that was never
running, which is the single largest waste in this project so far.

**Check it cheaply on the next bundle** — reliable tells, in order of usefulness:
  * `grep -c "couldn't beat the Rustboro rival"` → **non-zero = the per-run-state fix is
    ABSENT.** The single best discriminator (31 hits pre-fix, 0 after).
  * `run_index` all-odd with a perfect stride of 2 → the badge-log fix is absent. *(A stride
    >1 on its own is NOT proof — a run that earns no badges leaves a legitimate gap. Look for
    the alternating parity.)*
  * any single run exceeding ~3.5M frames → the frame-budget fix is absent.
  * `per-run frame budget exhausted` / `stopped: handed to Manual` present → fix definitely
    PRESENT. *(Absence proves nothing — it only means no run tripped that path.)*

  ‼ **`finished (0 frames)` is NOT a pre-fix tell.** It was listed as one here until
  2026-07-29 and it is wrong: it comes from the negative-frame CLAMP, which was never
  removed. `start_frame` is captured before the run, the hard reset restarts the counter
  mid-run, so `now - start_frame` goes negative for essentially every run after the first and
  is clamped to 0. It is expected post-fix and it briefly muddied the 5-bundle review.

## 0b. THE LOG BUNDLES REVIEWED SO FAR

The user delivered `P1 - P4 x4 LOGs 20260726-231412.zip` and it has been fully analysed.
**Verdict: the batch was producing almost no usable data while reporting most runs as
successes.** Two catastrophic bugs, both now FIXED in sandbox with A/B repros:

1. **Per-run state was never reset between runs.** The endless loop reuses ONE mode object,
   so `StoryMode.__init__` ran once per BATCH — under a comment claiming the opposite.
   `_rival_attempts` (cap 3) tripped on run 4 in every lane, so **runs 4+ quit at the
   Rustboro rival without fighting it**: 16/20 P1, 6/9 P2, 5/8 P3. P1 run 8's debug log has
   ZERO lost battles yet reports "couldn't beat the rival in 3 tries". `_defeat_counts`
   leaked too, so boss give-up thresholds fired on borrowed losses.
   → `StoryMode.reset_per_run_state()`, called per run. `repro_endless_per_run_state.py`.
2. **Failed runs were labelled "finished".** `outcome` defaulted to success and only a raised
   `BotModeError` changed it; a derail that calls `set_manual_mode()` returns normally. Any
   summary of that batch reads ~80% success against a true ~20%.
   → `try/except/else` reporting `stopped:`. Same repro.
3. Also fixed: **`run_index` still advanced by 2 per run** (1,3,5…37 over 19 runs). The old
   adjacency dedupe could never fire; replaced with ownership
   (`reset_for_new_run(..., authoritative=True)`). `repro_badgelog_run_index.py`.

**Confirmed healthy — do not re-investigate:** badge recording is clean in all four lanes
(correct gym order, no duplicates, no gaps), and losses:whiteouts held at exactly **1:1**.

**Two items were deliberately NOT fixed — they need the USER'S RULING** (see punch list):
- `#24-leadpolicy` — `_lead_best_matchup` is purely defensive (`min(incoming, -level)`); it
  benches the only mon that can win. P2 led **Whismur L15** into the Route 110 rival **13
  times** with **Marshtomp L24** in slot 2. ‼ This is NOT the old `train_team` lead-restore
  bug — that fix is intact and its repro still passes; the matchup call runs afterwards and
  overrides it. A matching signature is a hypothesis, not a diagnosis.
- `#24-route110cap` — that rival gets no prep and no attempt cap. But a naive cap would have
  KILLED the P2 run that recovered after those 13 losses. Needs data, not a guess.

### The SECOND bundle, `20260727-063751` (reviewed 2026-07-27) — pre-fix data + one new bug

Ran the OLD code (see §0a). Re-confirmed all three bugs above. NEW finding, now fixed:

4. **`MAX_FRAMES_PER_RUN` could not stop a runaway run** — it was checked only AFTER
   `super().run()` returned, so a run that never returns never reached it. Three of four
   lanes spent the night inside ONE run: **P3 hung 27M frames / ~6.5 h** at the Weather
   Institute (`controllable=False`, frozen position, and ZERO STUCK dumps — the global
   watchdog was itself what wedged); P1 19.9M and P2 13.4M frames in grind loops that are
   genuinely BUSY, so no progress detector can see them. ~16 of 29 lane-hours lost.
   → `_run_with_frame_budget()` enforces the budget every 2048 yields from inside the run.
   `repro_endless_frame_budget.py`.

Still-open items it raised (`#24-weatherinstitute-hang`, `#24-grindconverge`, `#24-canary11`)
are in the punch list; all three want the first post-fix batch before more effort.

**‼ NEXT ACTION: sync the running copy (§0a), THEN run a fresh x4 batch.**

### Documentation correctness audit — 2026-07-27 (docs 00/01/02/05/14 corrected)

Done while the user ran batches. Read-only agents verified claims against code and reported
`file:line`; only the main thread edited, and every load-bearing claim was re-checked (two
agent claims were wrong and discarded — see `08-MISTAKES.md`). Highlights:

- **`02-ARCHITECTURE.md`'s folder map omitted `sandbox-pokebot/`** — the copy where all work
  happens — plus `tools/`, `PROJECT KIT/`, `REMOTE START/`, `cloud-backups/`. Its prose
  meanwhile cited sandbox-only modules, so the doc contradicted itself on one page. Rewritten,
  with a "Which copy am I in?" table. It also had **no testing section at all**; the repro
  suite and `py -3.12` are now documented there.
- **`01-VISION-AND-DESIGN.md`** gave the active copy no intent section, and its Story-Mode /
  Endless-×4 headings named bare paths a reader would resolve to `custom-pokebot/`, **where
  the ×4 files do not exist**. Fixed, plus real sections for the five custom modes, the
  `tools/story-dev/` harness, the installers and the custom interface (the "Future" placeholder
  was stale — all built).
- **`05-KNOWN-ISSUES.md`** re-audited entry-by-entry; six entries prescribe already-shipped
  work (worst: **KI-18** says *"Do NOT patch on the hypothesis. Reproduce first"* for a shipped
  fix). Added **KI-25…KI-29** — defensive-only lead selection, uncapped Route 110 rival,
  Weather Institute hang, training livelocks, P4 canary anomaly.
- **`14-AGENT-PLAYBOOK.md`** gained §2c: a repeatable **x4 log-bundle review method** — use it
  on tonight's bundle instead of reinventing one.

**Resumed 2026-07-29 after a weekly usage limit interrupted the session.** State now:
- `#doc-audit-2` **PARTIAL** — consistency half done by hand: 134 items / 98 ids; the
  undocumented third marker `- [~]` (17 items) is now defined at the top of `03`; the single
  status conflict (`#24-pokenav-faithful`) proved to be a legitimate recurrence and is
  cross-linked. The expensive half — checking all 80 open items against code for
  "already built" — is NOT done.
- `#doc-audit-4` **SPOT-CHECKED** — the anti-poison system passes on the one documented Gemini
  error (claim tagged `(INFERENCE)` and rebutted with our own `map_data.py` evidence). A
  systematic sweep of all 84 note files is NOT done; highest-risk class is Gemini's
  *architecture advice*, not its names.
- `#doc-audit-3` **NOT STARTED** — `12-STORYMODE-DESIGN.md` (2,886 lines) has never been
  audited. Every conclusion about where runs *really* die is
now suspect, because runs 4+ never happened and derail reasons were poisoned by leaked
defeat counts. The previously-ranked feature list (`#24-provisions` etc., §4 below) is
DEFERRED until a clean batch exists — building on this data would be measuring noise.

## 0b. ‼ RUNNING THE TESTS ON THIS MACHINE — use `py -3.12`, not `python`

The repro suite did not run here at all: `confz`/`ruamel.yaml`/`rich`/`numpy` were missing and
the default `python` is **3.9** (unsupported; the project wants 3.11–3.13). Deps are now
installed into **Python 3.12**. Run repros as:

```
py -3.12 tools/story-dev/repro_<name>.py        # from the repo root
```

Current suite state: **45 pass, 0 fail, 6 environmental** (need a real mgba, or pre-existing
harness issues: `repro_boss_training`, `repro_double_faint`, `repro_navigate_failfast`,
`repro_smashrock_battle_wedge`, `repro_sufficiency`; plus `repro_x4_lanes`, which SPAWNS REAL
LANE PROCESSES — skip it unless you mean it). The old claim of "13 emulator-free repros"
undercounts by a lot.

## 1. HOW TO REVIEW THE NEXT LOG BUNDLE

The user is running an ENDLESS LOOP x4 batch overnight and will hand you a zip named
`P1 - P4 x4 LOGs <date> <time>.zip`. **Review it before anything else.** Procedure that works
(used twice; reuse it rather than inventing one):

```
# 1. extract somewhere scratch, read the manifest first
python -c "import zipfile;zipfile.ZipFile(r'<zip>').extractall('.')"
cat MANIFEST.txt          # lanes, starters, per-lane badge tallies

# 2. per-lane metrics — !! BATTLE OUTCOMES ARE ONLY IN THE DEBUG LOG, NEVER STDOUT.
#    A summarizer pointed at *-stdout-*.txt reports battles=0 and is lying to you.
#    stdout has: whiteouts ("recovered from the whiteout"), "lost a battle at map (g, n)",
#                "derail #N", "starting run", "-> derailed:"/"finished"
#    debug log has: "BattleOutcome.<X>", [MAP], [PARTY], [BATTLE], STUCK dumps

# 3. badge-log.json is CUMULATIVE and never archived — split records by `earned_at`
#    against the batch start time, or you will read old pre-fix data as new.
#    Group by `run_index` (NOT run_started_frame, which is unreliable).
```

**‼ FIVE TRAPS, ALL HIT FOR REAL ON 2026-07-26. Do not re-learn these:**
- **A bundle can span SEVERAL app launches.** `20260726-231412` held three (18:55, 20:30,
  21:08). The 18:55 stdout was ALREADY-REVIEWED pre-fix data left behind because only debug
  logs get archived, not stdout. **Segment by launch before concluding anything**, or you
  will attribute old failures to new code.
- **`MapRSE` and `MapFRLG` share (group, number) keys.** Parsing `map_data.py` without
  scoping to the `MapRSE` class silently yields KANTO names — `(8,1)` reads as
  `LAVENDER_TOWN_POKEMON_CENTER_2F` when it is `PETALBURG_CITY_GYM`. If a Hoenn run appears
  to be in Celadon, that is this bug.
- **"finished" did NOT mean finished** before this session's fix. In older bundles, treat
  every `finished` as unknown and confirm from the run's last `[STEP]` in the debug log.
- **Run outcome ≠ run progress.** The fastest way to see where a run really ended is the last
  non-`Encounter` `[STEP]` line per debug log. Sixteen P1 runs all ended on the identical
  step, which is what exposed the bug — a per-run outcome tally showed nothing.
- **Look for RUN-INDEX-shaped patterns, not just lane-shaped ones.** The failure was "every
  lane dies from run 4 onward", invisible in any per-lane aggregate.

**What to look for, in priority order:**
1. **Do runs 4+ still play?** The 2026-07-26 bug killed every run after the third in all
   three lanes that got that far. Count runs per lane and check the LAST STORY STEP of each;
   if late runs cluster on one step, per-run state is leaking again.
2. **Are outcomes honest?** Cross-check every `finished` against the run's real ending. A run
   reported `finished (0 frames)` did not finish.
3. **Badge records sane?** Correct gym order, no duplicates, no badge before its predecessors,
   and `run_index` advancing by ONE per run (it advanced by two until 2026-07-26).
4. **The 1:1 canary.** losses:whiteouts was EXACTLY 1:1 in every lane across two batches,
   because no potion layer exists. Above 1.0 means whiteouts with no battle logged (poison
   steps are the usual cause).
5. **Repeated losses at one fixed tile** — still worth checking, but read the lead-selection
   logic before calling it a regression. In `20260726-231412` the signature matched the old
   `train_team` bug exactly and was a DIFFERENT cause (`_lead_best_matchup`, see §0).

## 2. WHAT WAS BUILT AND IS LIVE (sandbox only; custom-pokebot untouched)

- **ENDLESS LOOP x4** — `Emulator > Endless Loop x4...` in the bot-mode popup. Four lanes,
  one process/profile/starter each (P1 torchic, P2 mudkip, P3 treecko, P4 random), 2x2 tiles
  in the video area, party strip follows the focused tile.
- **Park x4 & Collect Logs** — parks every lane, bundles all four lanes' logs into one
  VERIFIED zip under `profiles/x4 LOGS/`, archives originals to `debug-logs/Old/` only after
  the zip proves out.
- **Badge case** — Bag button under the 6th party ball; 2x4 badges, silhouette until earned,
  hover/click for leader detail + the team that won.
- **RNG decorrelation** — a random 0-120 frame pause on the naming screen. Without it, cold
  starts were BIT-IDENTICAL (Emerald is not RTC-seeded), so lanes were not independent
  samples at all.
- **Fixes**: the training lead-restore livelock; badge false positives (3 filters);
  `run_index` double-count; negative run frames; a stray directory in `profiles/` crashing
  startup; crash logs now written to `crash-<ts>.log`.

**Verification bar:** the `tools/story-dev/repro_*.py` suite — **52 scripts, of which 47
pass emulator-free** (0 fail, 5 environmental) as of 2026-07-27. Run the WHOLE sweep after
any change with `py -3.12` and a ~90s per-script timeout; see `02-ARCHITECTURE.md` §"Testing"
and `14-AGENT-PLAYBOOK.md` §2b.
*(An earlier version of this line said "13 emulator-free repro scripts … ~20 older need a
real mgba". Both figures were wrong — re-counted 2026-07-27. Running only 13 and calling the
suite green skips the two repros guarding the 07-26/27 endless-loop fixes.)*

## 3. THE PLANNING DOCS WRITTEN THIS SESSION (read before building)

| doc | what it decides |
|---|---|
| `19-TEAM-BUILDING-DISCUSSION.md` | the user's three team requests + the two-axis personality design |
| `20-POST-FORTREE-RECON.md` | Mt. Pyre, Aqua Hideout, gyms 7-8, + second-pass corrections |
| `21-TEAM-POLICY-DESIGN.md` | BUILD-READY: catch policy, dead-weight predicate, rotation, counter ladder, never-randomise list, offline test plan |
| `22-CAPABILITY-RECON.md` | healing items, the PC, ground/hidden items, shops, money |
| `23-MEANDER-PATHING-DESIGN.md` | the pathing verdict + algorithm |
| `ai-research-notes/2026-07-26-*/` | Gemini notes — RECALL ONLY, stub-marked, decomp wins |

## 4. NEXT ITEMS, RANKED (all specced, none built)

> ‼ **THIS RANKING IS DEFERRED as of 2026-07-26.** It was derived from batch data in which
> runs 4+ never happened and derail reasons were poisoned by leaked defeat counts (see §0).
> Item 5 in particular ("45 of the derails were the counter chain") is not trustworthy —
> some of those derails fired on borrowed losses from earlier runs.
> **Re-rank after a clean x4 batch on the fixed code.** The two ruling-needed items,
> `#24-leadpolicy` and `#24-route110cap`, come first if the user rules on them.

1. **`#24-provisions`** — healing items. Highest value: losses:whiteouts is 1:1, so EVERY
   loss becomes a full whiteout. `buy_in_shop()` is already item-generic and money-gated;
   the in-battle seam is one insertion at `battle_strategies/default.py:172`. Mostly policy.
2. **`#24-grasswander`** — organic movement while training. Nearly free; the seam is proven
   (`run_in_circle`, `walking.py:706`, takes an arbitrary waypoint generator).
3. **`#24-items`** — ground/hidden pickup. Pickups are SAFE and retryable; only `giveitem`
   gift scenes can strand a run. Itemfinder NOT needed to collect hidden items.
4. **`#24-partyvariety`** — the bot catches FOUR mons and stops at Badge 1. Two conditions in
   `_should_catch`. That is the whole "runs look the same" complaint.
5. **`#24-counters` phase 2** — the counter chain diagnoses and then ENDS THE RUN. 45 of the
   derails in the last batch were this.
6. **`#24-gymtrainers`** — Dewford's six gym trainers are skipped entirely (their sight cones
   are off the path to Brawly). Trainer battles are the ENTIRE economy: there are no scripted
   cash gifts in Hoenn.
7. **Travel meandering** — deliberately LAST. See `23-...`: it is net-negative today.

## 5. ‼ THINGS THAT WILL BITE YOU

- **`git add -A` is unsafe after running research agents.** One extracted the pokeemerald
  decomp into the repo root and I committed 11,567 files / 61 MB before catching it. Removed
  and gitignored, but NOT history-rewritten (project rule: never force-push). The repo is
  permanently ~61 MB heavier; cleaning it needs `filter-repo` + a force-push and is the
  USER'S call. **Check `git status` before staging.**
- **This dev box has no `mgba`** — nothing involving a live emulator has ever run here. The
  more powerful machine may differ; check before claiming anything is live-verified.
- **Gemini research needs `GEMINI_API_KEY`.** The user supplied one in chat this session; it
  is NOT in the repo and should be treated as compromised/rotated.
- **Never write game facts from memory.** Two were wrong this session: the 8th gym leader is
  JUAN in Emerald (Wallace is Champion — that is Ruby/Sapphire), and Emerald is NOT RTC-seeded
  (Ruby is). Both differ *between* Gen-3 games, which is exactly where recall fails.

---

### ⭐ YOU ARE HERE — 2026-07-27 — THREE BATCHES REVIEWED, FOUR HARNESS BUGS FIXED, NONE YET VALIDATED LIVE

**State right now.** `#24-x4` Phase 1 is built and has been run live by the user; three
bundles have now been reviewed (`20260726-201838`, `20260726-231412`, `20260727-063751`).
‼ **None of them ran the fixed code** — see §0a, the running copy is a different directory
and has not been synced. Four harness bugs are fixed and repro-proven here; ZERO are
validated live. The second review (`20260726-231412`) found that the instrument
itself was broken in two ways that made its output actively misleading — per-run state leaked
across runs so **runs 4+ never really played**, and failed runs were labelled `finished`.
Both are FIXED in sandbox with A/B repros (see §0 at the top of this file; suite is 45/0/6
under `py -3.12`). `custom-pokebot` and the upstream mirror are untouched.

**What is owed.** A fresh x4 batch on the fixed code. Until that exists, every claim about
*where* runs die — including the ranked feature list in §4 — is built on data where three
quarters of the runs were phantoms. Two design questions (`#24-leadpolicy`,
`#24-route110cap`) are written up with evidence and are waiting on the user's ruling; they
were deliberately not fixed on a guess, because in both cases the obvious fix is measurably
wrong at least some of the time.

**Older context for the feature itself follows.**

### ENDLESS LOOP ×4, PHASE 1 (built 2026-07-26)

**What it is.** `#24-x4`: a new `Emulator ▸ Endless Loop ×4…` command in the dashboard's
bot-mode popup launches FOUR independent `Story (ENDLESS RESET)` bots — one process,
profile and starter each — tiled 2×2 inside the video area, looping for ever and
restarting independently, unthrottled and muted with debug logging on. It is a TEST
INSTRUMENT: more reviewable failure data per hour, with guaranteed starter coverage.

| lane | starter | profile | logs |
|------|---------|---------|------|
| P1 | torchic | `endless-P1-torchic` | `profiles/endless-P1-torchic/debug-logs/P1-*` |
| P2 | mudkip  | `endless-P2-mudkip`  | `…/P2-*` |
| P3 | treecko | `endless-P3-treecko` | `…/P3-*` |
| P4 | random  | `endless-P4-random`  | `…/P4-*` |

Each lane writes BOTH a debug log (`P#-Story_(ENDLESS_RESET)-debug-<ts>.log`) and its
stdout (`P#-stdout-<ts>.txt`) into its own profile's `debug-logs/`. Those are the files
to collect and hand over.

**New (sandbox only — custom-pokebot and the mirror untouched):** `modules/tile_bridge.py`
(shared-memory frame channel), `modules/tile_mosaic.py` (pure-PIL 2×2 renderer),
`modules/gui/tile_child.py` (the lane frontend), `modules/endless_x4.py` (lane table +
process management). **Touched:** `pokebot.py`, `modules/gui/dashboard_gui.py`,
`modules/debug_logger.py` (`name_prefix`), `plugins/custom_modes/story_mode.py`
(`ENDLESS_RESET_COMPLETED`).

**‼ WHAT IS AND IS NOT VERIFIED.** This dev box has **no `mgba` installed** (no
`.last-requirements-check` anywhere — the bot has never been run here), so **no lane has
ever actually emulated a frame.** Everything NOT requiring an emulator is tested and
green (4 test scripts: cross-process bridge, mosaic rendering, `_on_frame` publish path
against a fake emulator, dashboard wiring on a real Tk canvas). The seam between
`PokebotTileChild.run()` and a live `LibmgbaEmulator` is the untested part.

**LIVE CONFIRMS THE USER MUST RUN (on a machine with the bot installed):**
1. Launch the sandbox dashboard, `Emulator ▸ Endless Loop ×4…`, accept. Expect four
   lane profiles to be created and four tiles to appear within a few seconds.
2. Confirm each tile shows its own game, and that the label reads the right starter once
   each lane gets past Birch's bag (this is the whole point — check P1 really is Torchic).
3. Click each quadrant; confirm the blue focus border follows the click **and the left
   party strip switches to that lane's team** (phase 2a). Hover a slot for the tooltip.
3b. Confirm each tile's label shows a growing `log <size>` and never `‼ NO LOG`.
3c. Once a lane beats Roxanne, confirm `profiles/endless-P1-torchic/badge-log.json` exists
   and contains a Stone Badge record with the team that won.
3d. `Emulator ▸ Park ×4 & Collect Logs…`: confirm all four tiles go to the title screen,
   the zip appears under `profiles/x4 LOGS/`, it opens and contains P1–P4 folders plus
   `MANIFEST.txt`, each profile's `debug-logs/Old/` now holds the originals, and
   `badge-log.json` is STILL in each profile (bundled but not moved).
4. Toggle handheld mode with a batch running; confirm the 2×2 still fills the video rect.
5. Close the window; confirm **no orphaned `python`/`pokebot` processes remain** (this is
   the hazard `_close_window()` guards — it ends in `os._exit(0)`, so nothing else runs).
6. Let it run a while, then hand over the `P1..P4` logs.

**UPDATE 2026-07-26 (same day, second round):**
- **Phase 2a DONE — the party strip follows the focused lane.** Click a tile and the left
  strip, party tab and hover tooltip all switch to that lane's team.
  `modules/remote_party.py` rebuilds stand-ins from the lane's status blob; the party
  renderer itself is untouched. `STATUS_BYTES` was raised 1 KiB → 8 KiB because a real
  six-mon team measures 2,385 bytes and the old cap would have silently dropped it.
- **`modules/badge_log.py` added** (#24-badges, the capture half of the trainer-card
  request): records the party at the instant each `BADGE0N_GET` flag flips, into
  `<profile>/badge-log.json`. Re-arms on emulator reset, so every run of an x4 batch is
  captured, and the first poll of a run adopts existing badges without inventing records.
  The badge-case OVERLAY is tabled (see punch list #24-badges); the recorder shipped first
  because it can only capture badges earned after it is switched on.
- **Logs were never actually missing** — the user found them; a lane logs into its OWN
  profile (`profiles/endless-P#-<starter>/debug-logs/`), not the profile the dashboard was
  opened with. Made discoverable rather than "fixed": the batch now prints each lane's log
  folder to the event log, and every tile shows its log size (or `‼ NO LOG` in red).
  One genuine latent fix went in alongside: lane stdout was block-buffered because it is a
  file, so `P#-stdout-*.txt` could sit empty for minutes — lanes now run `PYTHONUNBUFFERED=1`.

**‼ UPDATE 2026-07-26 (fourth round) — COLD STARTS WERE NOT INDEPENDENT SAMPLES.**
Verified in the pokeemerald decomp (`83df84e4`): `gRngValue` is 0 at every hard reset and
Emerald is **not** RTC-seeded (`SeedRngWithRtc` is inside `#ifdef BUGFIX`;
`include/config.h:48` leaves it undefined — Ruby DOES seed from the RTC, Emerald inherited
FireRed's `main.c`). The only per-frame advance is `Random()` in `VBlankIntr`
(`src/main.c:365-366`); the only single-player reseed is `SeedRng(REG_TM1CNT_L)`
(`src/main.c:208-214`), from a timer started when the naming screen opens
(`src/naming_screen.c:412`) and read when the name is confirmed (`:701`).
⇒ Two instances fed the same frame-aligned script produce a **bit-identical game**.
- **Fixed:** `modules/story/intro.py` now idles a random **0–120 frames between typing the
  name and confirming it** — the only externally controllable input to the seed. Random per
  RUN, not a fixed per-lane offset, because the hard reset between endless runs would
  otherwise make every run of a lane replay the same early game.
  `POKEBOT_RNG_DECORRELATION_FRAMES=0` restores deterministic cold starts for bug repro.
  No existing `repro_*.py` is affected (they load save states, not the intro).
- **How to read PAST batches:** lanes only diverged once something consumed a different
  number of frames — a different starter at Birch's bag, or the bot's own Python-side
  randomness (`story_mode.py:1330`, `:2015`). The intro, rival scene and Birch rescue ran
  identically across lanes, and same-starter lanes stayed in lockstep much longer.
  Early-game counts from old batches are repeated observations of ONE run, not N samples.
- Full reasoning: 06-DECISIONS-LOG and 08-MISTAKES, both 2026-07-26.

**UPDATE 2026-07-26 (third round) — `Emulator ▸ Park ×4 & Collect Logs…`** (shown only
while a batch runs). Parks all four lanes, bundles every lane's logs into
`profiles/x4 LOGS/P1 - P4 x4 LOGs <date> <time>.zip` with a `MANIFEST.txt`, verifies the
zip, and only then archives the originals into each profile's `debug-logs/Old/`. This is
the "collect a batch and send it over" path — one attachment instead of four folders.
- Order is **park → copy → VERIFY → archive**, and nothing is moved until the finished zip
  has been reopened and proved complete. Verification failure ⇒ nothing archived.
- Parking needed a parent→child command channel: `tile_bridge` slots are now
  `[header][status][command][frame]`, with `command` written ONLY by the parent (`MAGIC`
  bumped to ...33). This is also the channel phase 2b's control toggle will use.
- `badge-log.json` is bundled but NEVER archived — it is cumulative history.
- `park_all()` blocks the window briefly (typically ~100 ms, bounded 15 s); the dashboard
  has no Tk mainloop, so pumping Tk inside that wait would re-enter the frame callback.
- The batch does NOT resume after collecting; stop it from the same menu.

**KNOWN GAPS (by design, phase 2b — agreed with the user, NOT built):**
- Watch-only. The control toggle (click a tile, then drive it) is not built; the channel
  is cheap when it is (`libmgba.press_button`/`hold_button`/`release_button` take plain
  strings), but nothing routes input to a lane today.
- The TOOL COLUMN (KPIs, stats, cheats) still reflects this process's idle profile — only
  the PARTY follows the focus. Extending it means shipping more per-lane state.
- While a batch runs, this process's own emulator is parked in **Manual at 1×** purely to
  pump the Tk queue. Its previous mode and speed are restored on stop. `context.video` is
  deliberately never touched (user directive 2026-07-26).

**Also fixed on the way (both would have bitten in real use):** closing the window would
have orphaned four emulator processes; and four lanes starting at once on a machine with
no `.last-requirements-check` would have run four concurrent `pip` installs into one
environment (lanes now skip the requirements check and the launch-time cloud sync).


### ⭐⭐⭐ 2026-07-24 — KI-15 FIXED (3 proven fixes) + OVERNIGHT CHAPTER LOOP RUNNING
**KI-15 is fixed** (see 05-KNOWN-ISSUES KI-15 + changelog for the full story): (1)
`navigate_to` no-progress bail (`NavigationStuckError`), (2) the cutscene rider's
450-frame B→single-A escalation for the stale post-battle battle-text wedge, (3) the
StoryMode run-loop 240-frame persistence nudge. Each proven on a captured state
(`saves/ki15_gotaway_wedge.ss1`, `saves/ki15_nurse_wedge.ss1`); museum-greeter
regression probe green; faithful goods_recovered runs self-recover where they used to
hang terminally. ‼ TWO intermediate designs FAILED and taught lessons (08-MISTAKES
2026-07-24): the wedge is reader-indistinguishable from a dialogue tail (discriminate
by RESPONSE TO INPUT + persistence, never by readers), and any auto-unstick press must
be sustained-signature + single-press + cooldown, or it A-mashes NPC dialogues.
New probe tools: probe_stuck_state.py / probe_press_variants.py / probe_ride_fixed.py.

**OVERNIGHT DIRECTIVE (user, 2026-07-24, verbatim intent):** work through ALL remaining
chapters until the story bot is complete; harden + fill in the chapter skeleton; fix
errors along the way, but after a bunch of failed fix retries MOVE ON to the next
chapter; use Gemini assistants (gemini_relay.py) for research gaps.

**OVERNIGHT PROGRESS (as of ~02:30):**
- **Ch12 BUILT + WIRED + committed (`f5aba6d8`)** — Segments 12a/b/c: direct
  Lavaridge→Petalburg route (Fiery-Path note was WRONG — see changelog), Rusturf
  Wanda-wall smashes, Petalburg gym SIGN-script doors (never walk into them!),
  Norman challenge, fully-automatic Surf handoff, teach Surf. Mechanically validated
  live to Norman's room (run9: 500k frames, 0 hang / 0 Manual; one whiteout →
  recovery + boss-training kicked in correctly). The Norman WIN is level-bound on
  the thin flannery_done team — a 2M-frame run is grinding it out in the background
  (ch12_run10_long.log). When it lands, capture `norman_done.ss1`/`surf_taught`
  checkpoint + validate 12c, then update END_MARKERS batches.
- **Fresh batch (3M frames, 5 lanes): 3/5 reached HEAT BADGE organically, 0 Manual**
  (KI-15 fix class held); 2 lanes → the NEW **KI-17** (after-faint reshow DMA race —
  the original "Shedinja chooser" bug, real all along; 2 states captured, Gemini
  decomp analysis archived, sweep hardened; validate on the next batch).
- **Ch13a-e SKELETON built + wired + committed (`4b626c91`)** — Surf arc: travel to
  Fortree (Surf crossing planner-native), Weather Institute (Shelly), Route 119
  rival → HM02 Fly, Devon Scope (Steven (13,15)/Kecleon (12,16) on R120; city
  Kecleon (25,8)), Fortree Gym (turnstile push-solve) → Winona. Flags audited
  (phantoms dodged: use HIDE_ROUTE_119_RIVAL / RECEIVED_HM_FLY). ⚠ ALL of Ch13 is
  first-run-validate — expect a Ch12-style iteration burst when a post-Surf save
  exists.
- **§Ch14 SPEC drafted** (Route 121 → Mt. Pyre exterior → Magma Emblem [KEY ITEM,
  no flag — gate on the BAG] → Jagged Pass hideout door → Maxie; flags audited).
- **Norman balance:** the flannery_done team (no Fighting answer) didn't break
  Slaking in 2M frames (6 attempts, boss-training cycled correctly, 0 hangs) —
  fresh teams carry Combusken; the win is expected organically in the big batch.
- **★ NORMAN BEATEN ORGANICALLY (batch 20260724-070630 lane 1, Blaziken team)** —
  Ch12 validated end-to-end; **`saves/norman_done.ss1`** captured+verified (BADGE05 +
  RECEIVED_HM_SURF, controllable). The lane's one failure (the 12c Surf-teach hunt
  picking warp-locked Route 117 grounds) is FIXED (reachable-grounds picker + Route
  102 (9,2) promoted into TRAINING_GRASS). Batch: 1× Norman+Surf, 2× healthy
  budget-INCOMPLETE, 2× pre-jolt-fix wedges (fixes landed mid-batch, 54f9537e).
- **Ch13a-c VALIDATED (11 iterations from norman_done, commit e043cbaf):** teach
  Surf → Surf-cross Route 118 → Weather Institute (Shelly) → **HM02 Fly** → reaches
  Fortree/Route 120. Six general engine fixes fell out (all in the playbook table):
  phantom-escape in `_ride_out_all_scenes`, choice-aware scene rides, `_hold_walk_route`
  (bridges the planner can't cross), coord-trigger targeting, `_clear_stale_battle_message`,
  Fortree-side travel `order` ranking.
- **Ch13d Devon Scope WORKS end-to-end** (real path, run 13, commit 2bdd526e): the
  Route 120 north-bridge strand is solved (`_leave_route120_north_bridge`: Steven's
  scene isolates the avatar at (13,16) — held Up→(13,15), Left→(5,15) escapes; called
  from 3 resume paths). The run crossed Route 120, flushed the city Kecleon, healed,
  and reached the Fortree gym door. Checkpoint `saves/devon_scope_got.ss1`.
- **✅ Ch13e "tree-bridge blocker" was NEVER REAL — note REFUTED and retired (2026-07-24.)**
  The old claim here said the gym door (22,11) is reachable only from (21,11)/(22,12) and
  blamed planner-blind elevation walkways (the Route-119/120 class). Probed live
  (`tools/story-dev/probe_route120_to_fortree.py` §6/7): (22,11) is a correctly-typed
  `Door Warp` → FORTREE_CITY_GYM, landing (15,24), matching the code's own docstring. Its
  ONLY blocker is the transient story flag **969 HIDE_FORTREE_CITY_KECLEON** — the Kecleon
  sits in the single chokepoint tile (25,8) between the walkway and the door cluster. With
  flag 969 forced True (reader-level fault injection), (22,11) plans from (25,7) in 9
  waypoints, from the plaza (5,6) in 38, and from ROUTE120 (5,15) in 115 — i.e. reachable
  from essentially anywhere, no held-walk route needed. `get_devon_scope` already flushes
  that exact Kecleon before `do_fortree_gym` runs, so the real playthrough sets the flag
  first. Control: (22,12) is fully walkable both before and after injection, proving the
  pre-flush FAIL came from the one gated chokepoint and not a second broken tile.
  ‼ The stale note was written from observing the PRE-FLUSH blocked state and mistaking a
  story-sequenced flag for a map/planner limitation. **Residual debt:** this is a strong
  fault-injection proof, not a live post-flush save — capture a checkpoint keyed on flag
  969 and re-run §6/7 without injection to close it (punch-list `#24-fortreelive`).
  NEXT: 13e Winona (turnstile gym, built, untested) → BADGE06. Then Ch14 (§Ch14 spec
  ready). Milestones:
  `norman_done.ss1` (clean, BADGE05+Surf), `devon_scope_got.ss1` (Scope, on Route 120).
- **KNOWN OPEN:** KI-17 (after-faint reshow DMA freeze — sweep hardened per Gemini's
  decomp analysis, validate next batch); the fresh 5M batch was 0/5-frontier but all
  failures were the freeze family / pre-jolt-fix wedges (fixes landed), not new breakage.

> **NEW AGENT: read `14-AGENT-PLAYBOOK.md` right after this file.** It is the
> accumulated craft (harness, debugging method, story-mapping, faithfulness rules, bug
> patterns) — use it to build faster and prove every fix.

### ⭐⭐⭐⭐⭐ 2026-07-23 — **CH11d COMPLETE: HEAT BADGE WON** (frontier = Ch12)
The Lavaridge trapdoor maze is SOLVED and Segment 11d is WIRED. `do_lavaridge_gym` no
longer guesses: it scans both floors for holes (1F behaviour 104), geysers (B1F
behaviour 41) and **jump-south ledges (behaviour 59)**, builds the chamber graph and
BFSes it from wherever the player actually is. The ledges were the whole bug — under
plain collision the floors look like sealed chambers with no exits, which is why five
prior runs oscillated on inert tiles. Canonical chain = 4 falls: (8,9), (0,10), (2,3),
(10,6). **Validated (ch11d_run11): 0 derails, Flannery beaten, BADGE04_GET, clean
content-end; the run whited out mid-way, self-recovered and re-solved the maze move for
move — an unplanned determinism proof.** Checkpoint `saves/flannery_done.ss1`.
Also fixed: a failed leg used to B-ride a nonexistent cutscene (18k-frame wedge, run 10)
— recovery is now script-aware and stall-budgeted. Details: changelog + 08-MISTAKES
(two entries) + 06-DECISIONS + design §Ch11d (full mechanics table).
⚠ Segment 11d does NOT pre-grind: a two-way sweep proved NO training grass is reachable
from Lavaridge (Jagged Pass one-way; Route 112 lower has no return). L29-31 wins but is
marginal → #24-trainmap.

**✅ FIXED (user's real-HW log 2026-07-23, `Story_DEBUG__RESET...062055.log`) — both
reported bugs, reproduced in-harness then proven:**
1. **Slateport museum greeter loop.** Root cause: "A" is not "advance text" — beside an
   NPC it STARTS a conversation, so A-riding a plain message re-opened it forever (the
   fee was already paid; the text was "Please enjoy yourself."). New `_dialogue_button()`
   presses A only while a Yes/No/multichoice is on screen, B otherwise; ride-outs also no
   longer mash during a dialogue's non-controllable tail. Closes the whole class.
2. **Dewford detour to the dock.** Briney is STATIC at (12,9), but the code used the
   wandering-NPC helper whose known-spot path is a GREEDY stepper — it dead-ended on the
   y=10 wall band and wandered into the south-east pocket. Now walks straight to (11,9)
   with the pathfinder and talks; the helper also tries the pathfinder before greedy
   stepping. Dock leg is now a direct 10-tile walk.
Proof: `museumprobe2.py` (repro → clean pass) + a 250k-frame `brawly_done.ss1` run
through Dewford gym → sail → Slateport → museum delivered → Route 110 rival → Mauville
prep, still in Story mode at the budget end, 1 self-recovered derail.
New tool: `tools/story-dev/mapfacts.py` (warps + objects + passability grid for any map).
⚠ Sandbox only — not promoted to custom (standing rule: promote on the user's explicit OK).

**ALSO LANDED 2026-07-23 (user directives, built during their fresh-start test run):**
- **"Show Coords" toggle** — Play tab → CONTROLS → "Debug" row. Live tile + area name +
  map group/number + facing, for reporting pathing coordinates during development.
  Off by default, display-only, fully guarded. ⚠ **Compile-verified but NOT clicked live**
  (the user's test was running) — confirm on screen.
- **`sandbox-pokebot/profiles/GEMINI-FULLGAME-RESEARCH.md`** — a Deep Research commission
  for a whole-game bot-grade walkthrough, to be re-run periodically so mapping detail lands
  ahead of the build frontier. Grade the result with the procedure in that file (including
  a known-answer control from an already-built chapter) and record it in its run log.

**2026-07-23 (day, cont.) — user's fresh-start test graded + HM-learner fix + Gemini full-game:**
- User's fresh run reached Mauville/Rock Smash cleanly; their report exposed the Ch10b
  design flaw: the HM mule was picked by LEVEL, not compatibility (party menu loops on
  NOT ABLE when the top mon can't learn it — e.g. any Swellow-led party). FIXED +
  A/B-PROVEN: `hm_learner_slot` (compatible pick) + `ensure_hm_learner` (derives hunting
  grounds from ROM encounter tables × learnsets, provisions balls, catches a learner via
  the new HM_CATCH_TARGET_DEX on-sight catch branch) + `teach_hm_move` truthful
  compat guard. Proof: repro_hm_learner.py + `--driver hmtest` (fault-injected party →
  hunted Rt 117 → caught Poochyena → taught Rock Smash, PASS). Watch out for the
  function-local-import shadowing lesson in 08-MISTAKES.
- **Gemini full-game Deep Research response GRADED B+** (run log + detail in
  profiles/GEMINI-FULLGAME-RESEARCH.md): step order/rosters/puzzle-rules HIGH (Sky
  Pillar first-visit-solid-floors trap, Fortree turnstile persistence, Aqua warp graph,
  Seafloor Sokoban reset, Sootopolis Hamiltonian ice); identifiers MEDIUM — several
  phantom flags, audit_flag_names.py is mandatory before wiring any of them. Leads
  folded into design §Ch12+ (⚠ unverified-external). PROMPT 2 (early-game check =
  the known-answer control) not yet relayed.
- New punch-list futures from the user: #24-provisions (potions/strategic healing),
  #24-tms, #24-pokeprofiles (per-species battle profiles via batched overnight research
  + Gemini cross-referencing), #24-economy. All noted for later — not next work.

**PENDING (2026-07-23):** (1) the user's fresh-start test run — log incoming, grade it
when it arrives; (2) the full-game PROMPT 2 early-game pass is still unrelayed.
**DONE 2026-07-23 (afternoon):** the #24-pokeprofiles Batch-1 response is GRADED (B:
TM-compat 98%, levels 42% — never trust research levels; grading + raw archive in
profiles/GEMINI-POKEPROFILES-*.md, machine check = tools/story-dev/grade_pokeprofiles.py)
and the **Gemini API relay is BUILT + verified** (tools/story-dev/gemini_relay.py; key
GITIGNORED at sandbox-pokebot/profiles/gemini.key — never commit it; usage + day-one
rules in 15-ESCALATION-RESEARCH.md).

**BUILT 2026-07-23 (evening, user approved "proceed"):** the whole boss-training
discussion landed, each piece proven (changelog has the details + proofs):
KI-14 fixed (menu-free close + menu-aware cutscene rider; teach-to-Route-113 clean,
museum repro still clean) - matchup-aware after-faint chooser (A/B: no more
Thunderbolt-food replacements) - BOSS-TRAINING MODE (KO telemetry from
gBattleResults; light top-up + boss re-attempts when grass is fodder; 0-KO fallback;
grass-less bosses skip the grind). Punch list: +#24-trainersweep (one-time trainer
sweep before grinding; Match Call rematches later - NOT built yet).
NEXT VALIDATION: a fresh batch (or the user's next real-HW run) through Wattson to
watch boss-training fire organically; then Ch12.

**BUILT 2026-07-23 (night, user approved + defensive backup):** the SWEEPER-SUFFICIENCY
GATE (see changelog for full detail + proofs). Revert point if anything goes wrong:
tag `backup-pre-sufficiency-2026-07-23` (pushed) —
`git checkout backup-pre-sufficiency-2026-07-23 -- sandbox-pokebot/plugins/custom_modes/story_mode.py`.
Gate: sufficient sweeper (ace-pair score + stat-fit + defensive veto) → skip team prep;
near-miss / imminent-evolution (Torchic→Combusken) → targeted top-up of ONE mon;
no sweeper → band prep unchanged; losses ≥2 → reactive layer owns it. Proven by
repro_sufficiency.py (6 scenarios) + a live rustboro.ss1 run (targeted top-up →
ROXANNE BEATEN → into Ch5). gemini_relay default is now gemini-3.1-pro-preview.
DEFERRED (my call, user offered now-or-later): the "company-style" multi-agent Gemini
orchestration refinement — better done overnight/later; noted on the punch list.

**FIXED 2026-07-23 (late night, user's paired logs):** the Route 111 first-rock hang
(the batch-8 morning-queue wedge, now closed): `_smash_rock` is idempotent and judged
by the rock OBJECT disappearing (Rock Smash spawns wild battles — the script context
can read active forever afterward), plus a phantom-script escape in the cutscene rider
(10s of playable+quiet+script-active = parked context, scene over). Proofs:
repro_phantom_script.py A/B + live rocksmash_taught run through both rocks to Route
113. Log identification for the user: 56c1baf9 (12:24) = mid-Wattson training;
478c2506 (13:41) = the fresh run with the hang. Punch list: +#24-hm-multi.

**BUILT 2026-07-23 (late night, user directive): milestone-state sharing.** The repo's
checkpoint library is now a GUI feature: "Load Milestone State" (dashboard GAME MENU
card + both Emulator menus) lists the story-ordered, chapter-tagged checkpoints from
tools/story-dev/saves and loads them like save states (registry:
modules/story_milestones.py — curated table + auto-labeled fallback; safety copy about
the NICK test playthrough + use-a-test-profile + pair with resume-anywhere Story modes,
never DEBUG-RESET). saves/user-reports/ added for the user's bug-capture states.
⚠ Compile/import-verified, NOT yet clicked live (user's test was running) — confirm
the popup renders next GUI session.

**FIXED 2026-07-23 (user's DEBUG run from a personal save):** the Mt. Chimney cable
car wedge + a structural stranding, both proven end-to-end (changelog for detail):
(1) boarding approached the wrong tile (attendant is (6,6), approach (6,7) — was (6,8));
now `ride_cable_car_to_summit()` with a retry; (2) a whiteout on a Jagged Pass trainer
respawns below the one-way descent and the cable-car segment was Magma-gated →
permanent stranding + a guard that falsely passed. Now `do_jagged_descent` re-rides the
cable car when stranded below, and the 11c guard checks arrival-in-Lavaridge. One run
meteorfalls_done → cable car → Maxie → whiteout → cable-car RE-RIDE → Lavaridge →
Flannery → HEAT BADGE, 0 derails. Also validated this session: the rock-smash fix
(taught to Mightyena, no hang) and the sufficiency gate, both from the user's earlier logs.

**BUILT 2026-07-23 (user's milestone-testing feedback):** three fixes, all proven
(changelog for detail); revert point tag `backup-pre-resume-robustness-2026-07-23`.
(1) Rock Smash field use 6x faster (was gating the YES-answer A on "script inactive",
but the prompt IS a script) — ~20s for both Route 111 rocks now.
(2) RESUME-FROM-ANYWHERE: `normalize_to_overworld()` at `_play` start B-presses any
entry state (menu/dialogue/battle/cutscene) to a clean controllable overworld before
segments navigate; proven to heal the actual menu-saved milestone (BAG_MENU -> OVERWORLD
in 204 frames) + a 5-state fault-injected A/B.
(3) `rocksmash_taught.ss1` milestone regenerated in a clean overworld (was saved in the
bag menu); other Ch10 checkpoints audited clean. `regen_rocksmash_taught.py` is the
template for re-capturing any checkpoint safely.
NOTE for the future: the user asked to keep extending resume robustness "for all
situations" — the normalizer covers the common ones; deepen as new edge states appear.

**KI-16 FIXED + VALIDATED 2026-07-23:** the wattson_done deterministic wedge was
`_smash_rock` returning before `EventScript_SmashRock`'s WaitForMovementFinish completed —
the next navigation cancelled the crumble movement and stranded the script. Fix: wait for
the field script to clear before returning. The wattson_done batch that was 5/5 hangs is
now **5/5 HEAT BADGE, 0 hangs/derails/whiteouts.** wattson_done is a good milestone again.
**KI-15 RE-DIAGNOSED 2026-07-23 (still open, ~1/5):** ‼ it is NOT an after-faint party-menu
hang — that was a MISDIAGNOSIS never supported by any log (`grep -r "SHEDINJA fainted"` = 0
hits; the after-faint sweep is proven ROBUST). The REAL bug (3 confirmed 20k hangs) is a
**post-battle STORY-RESUME hang**: an inline battle interrupts story navigation/a scripted
scene and the flow can't resume (stale `cb=ReturnFromBattleToOverworld` +
`BattleScript_PayDayMoneyAndPickUpItems`). Two forms: `_wait_until_cutscene_over` loops
(RUSTBORO), and `navigate_to` bounces `(5,6)↔(5,7)` (ROUTE 104). Env-gated `KI15_TRACE`
instrumentation is in `_wait_until_cutscene_over`; faithful `--driver story` runs ride the
scene cleanly (hang needs the rare battle-interrupt race). Full diagnosis + next steps in
05-KNOWN-ISSUES KI-15. Do NOT patch the battle handler for this.

**VALIDATION SWEEP DONE 2026-07-23 (user-requested 5 fresh + 5 milestone):**
Pass 1 (5 fresh→HEAT BADGE): 4/5 clean (3 frontier + 1 budget-INCOMPLETE), 1 real hang
(after-faint chooser, KI-15). Pass 2 (5 from rocksmash_taught): **5/5 HEAT BADGE, 0
hangs/derails/whiteouts** — the recent frontier work is validated solid. Two intermittent
bugs logged with repros: KI-15 (after-faint chooser + 1-HP Shedinja) and KI-16
(wattson_done deterministic navigator wedge — use rocksmash_taught for milestone tests,
not wattson_done). Neither guess-patched (critical code, need validated repros first).

**IN PROGRESS — Ch12 BUILD STARTED 2026-07-23 (route leg, WIP/unwired):**
`travel_lavaridge_to_petalburg` exists in early_game.py but is **NOT wired into _play**
(frontier = Flannery/HEAT BADGE, untouched). Progress: the Route 112 ledge crossing works
(Lavaridge→Route111(13,90) reaches the desert edge). **BLOCKER FOUND + documented:** Route
111's middle is the Go-Goggles DESERT — it blocks N↔S, so the Lavaridge→Mauville leg must
go via the FIERY PATH (reverse Ch10 `travel_to_fallarbor`: Route112 → Fiery Path → Route112
→ Route111-south past the smashed rocks → Mauville). RESUME HERE: finish that leg by
mirroring travel_to_fallarbor's Fiery-Path+rock legs, then validate the Mauville→Petalburg
tiles (currently guesses), then build do_petalburg_gym + the Surf handoff (tasks #5/#6),
then wire Segment 12 + livetest END_MARKERS. Backup tag `backup-pre-ch12-2026-07-23`.
Recon tools: route_probe_ch12.py, route_chain_ch12.py, petalburg_gym_probe.py.

**(reference) Ch12 DEEP-MAP + build plan** — §Ch12 build spec in 12-STORYMODE-DESIGN
(now corrected for the Fiery-Path routing). 
**NEXT: BUILD Ch12 — DEEP-MAPPED 2026-07-23, ready.** Spec in 12-STORYMODE-DESIGN §Ch12
(archived research tools/story-dev/research-gemini-ch12-2026-07-23.md). Key findings,
verified this session: **Go-Goggles/Route 111 desert are OPTIONAL — SKIP them** (Route 111
connections probed: the desert is never on the Lavaridge→Mauville→Petalburg path). Route =
long overland backtrack (Lavaridge → Rt112 ledges → Rt111 S → Mauville → Rt117 → Verdanturf
→ Rusturf Tunnel → Rt116 → Rustboro → Rt104 → Petalburg Woods → Petalburg). Gym = the tall
9×112 PETALBURG_CITY_GYM, VAR_PETALBURG_GYM_STATE-gated doors (runtime-modified, Mauville
class → LIVE-SOLVE), Norman at top (4,2), 8 trainer tiers. Beat Norman (Spinda27/Vigoroth27/
Linoone29/Slaking31 ⚠, TRUANT ace) → BADGE05 + TM42 → **step DOWN** → Wally's dad → warp to
Wally's house → HM03 Surf (RECEIVED_HM_SURF) → teach it. Build as progress-gated legs +
a do_petalburg_gym live-solver; validate connections + the door path + Norman team at build.
Start from `flannery_done.ss1`. Update livetest END_MARKERS when the frontier moves.

### (superseded) OVERNIGHT LOOP INSTRUCTIONS — kept for the resume ritual
The user commissioned an unattended overnight loop: (1) 5-run fresh batches until ALL
FIVE reach the Dynamo Badge content-end clean (no Manual/hang/crash; self-recovered
derails OK) — fix what fails, rerun; (2) then deep-map the next chunk (Ch10 first),
sanity-check (audit_flag_names + two-way pathability sweeps + decomp validation),
build it, test along the way; (3) any question needing Gemini goes to
`sandbox-pokebot/profiles/GEMINI-PROMPTS.md` (append-only, never blocks — build with
the decomp-verified best answer + a marked assumption); (4) repeat chapter by chapter,
building the skeleton as deep into the game as possible. Batches ~25-40 min each;
mapping/doc work interleaves during runs (no code edits mid-batch). If this session
ends mid-loop, resume the loop from this note + the newest livetest-runs batch.
Current: batch 20260722-204645 running (5 lanes, fresh→badge, with the cave-heal +
mapped-index fixes 55e27eab). Watch item: Rustboro rival staging non-engagement (1/5
in the prior batch).

### ⭐⭐⭐⭐⭐ Session 2026-07-22 (Fable 5, afternoon→evening) — **CHAPTER 9 COMPLETE: DYNAMO BADGE WON**
**Story frontier = Ch10.** Run 14 played stern_done.ss1 → rival → Wally → prep-training
(Route 117 (31,16), band 20-24, two evolutions: Swellow + Mightyena) → live-grid maze
solve → **Wattson BEATEN** → `wattson_done.ss1` (verified: BADGE03_GET +
DEFEATED_MAUVILLE_GYM + DEFEATED_WALLY_MAUVILLE) → clean content-end. KI-13 closed by:
the 0-power move-learn guard (Mud-slap preserved), Segment 9c prep, the two-way-swept
training tile, and `_ride_out_all_scenes` (aftermath chains). Interrupt hardening from
the user's real-HW log: `ensure_facing_direction` rides out field scripts (85k-frame
wedge fixed, regression-proven) + a GLOBAL StoryMode no-progress watchdog (18k frames of
stasis → self-derail into recovery). **NEXT: Ch10 (Rock Smash from Mauville SE house →
Route 111/112 → Fiery Path → Fallarbor)** — run /validate-docs + audit_flag_names.py
first; note the Route 110/117 pathability prevention rule (two-way sweep FROM THE REAL
ENTRY TILE) before picking any grind tile.
**Five proven fixes this session** (each with repro + proof; changelog has details):
1. Phantom post-evolution script suppressed wild encounters → training spin starved
   (batch run05) → `_story_spin` B-rides leftover scenes on its no-progress bail.
2. After-faint party menu deadlock (blind A-spam lockstep; slots 0+1 both fainted) →
   STATE-AWARE sweep in `handle_fainted_pokemon` + dispatch recognizes
   `BattleScript_FaintedMonTryChoose`. Proven live on the wedge state (~128 frames).
3. Ch9a guard keyed on a PHANTOM flag ("DEFEATED_RIVAL_ROUTE_110" doesn't exist!) →
   decomp-true `route110_rival_beaten()` (VAR_ROUTE110_STATE ≥ 1, tear-resistant);
   `_done()` now raises on unknown names; NEW `tools/story-dev/audit_flag_names.py`.
4. **THE BIG ONE:** Mauville's barriers exist only in the LIVE grid (gBackupMapLayout);
   `get_map_data`/`calculate_path` read the ROM's STATIC layout — blind to setmetatile.
   `do_mauville_gym` now reads the live grid, learns both barrier configs, BFS-plans
   across toggles, walks legs judged by ARRIVAL. (Applies to every runtime-modified map
   ahead: Trick House, ice floors, Sky Pillar.)
5. Harness: NO-PROGRESS milestones dump the generator call stack; player position is in
   the progress signature (an exploring solver is not a hang).
**Assets:** `saves/mauville_wedge.ss1` (mid-maze repro), ch9_run*.log series,
livetest batch REPORT.md (runs 01-04 clean/budget-bound; run05 = fix #1's repro).
**Batch verdict (20260722-134735):** 4× zero-error budget-bound INCOMPLETE + 1 organic
stall (fixed). Report in `tools/story-dev/livetest-runs/20260722-134735/REPORT.md`.

### ⭐⭐ Session 2026-07-22 (late night) — KI-12 battle-chain fixed + Gemini PoC GRADED + Ch9 validated
- **KI-12 (user's gym party-menu hang + "double battle bug") FIXED as a 3-bug chain** via a
  purpose-built repro (`--inject-faintbench`): bounded after-faint party menu; chooser-None
  fallback (any living mon beats crashing); the double-battle `reason` TypeError fixed +
  story strategy now ATTACK-THROUGHS trainer doubles. Key insight: Emerald fires TRUE
  double battles when two trainers sight you at once (why these clustered at gyms). Proof:
  the repro plays the double to a natural whiteout → story recovery. Details: changelog +
  08-MISTAKES (one-repro-three-bugs lesson).
- **Gemini external-research PoC: GRADE = HIGH.** Its Ch9 research was precise + cited,
  matched every decomp spot-check (Route 110 rival triggers, Wally flags/Scott sequence),
  and CORRECTED our own doc (Gabby&Ty's first battle is Route 111, not Slateport).
  VERDICT: promote to the REGULAR pre-build validation step (/validate-docs source 3 via
  the primer); deep mid-build escalation stays rare. Gemini-via-API documented in
  15-ESCALATION-RESEARCH as the future automation path (needs the user's key, gitignored).
- **§Ch9 written into the design doc** (validated sequencing, ✓-tagged by source):
  Route 110 rival choke-point (⚠ probe VAR_ROUTE110_STATE in stern_done first) → Mauville
  Wally-gates-the-gym → switch-puzzle gym → Wattson (Voltorb20/Electrike20/Magneton22/
  Manectric24) → BADGE03. **NEXT: build Ch9 from §Ch9** (probe the ⚠ items first).

### ⭐ CH8b DONE — Devon Goods → Capt. Stern (KI-11 resolved) — 2026-07-22
`deliver_devon_goods_to_stern` BUILT + WIRED + VALIDATED: full run slateport.ss1 → Stern's
Shipyard → **talk to Dock** (the missing story step — sets FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA,
clearing the grunt-sealed museum; user-supplied + decomp-confirmed) → museum → ¥50 fee → 2F
→ Stern (13,6) → two grunt battles WON → Archie → `DELIVERED_DEVON_GOODS` (+ scene heals) →
clean content-end. Checkpoint `stern_done.ss1` (verified: DELIVERED + Aqua-cleared). KI-11 was
a DOC/sequencing gap → the new **/validate-docs** process exists to catch this class going
forward. **Frontier now = Ch9 (Route 110 → Mauville → Wattson); run /validate-docs on §Ch9
before building.** Also open from the batch sweep: #24-evo-trainstall (evolve-mid-training
hang, repro `saves/evostall.ss1`) + #24-freshbatch-rustboro. Minor: an 8000-frame cutscene-
wait derail recovers during the museum approach (non-fatal; tighten later).

### ⭐⭐⭐⭐ Session 2026-07-22 (Fable 5, night) — SHINY ALWAYS-CATCH ✅ + dock-stall fix ✅ + DEBUG modes ✅ (SANDBOX, pushed)
- **SHINY = ALWAYS CATCH implemented + proven** (the user's directive, done first): shiny
  branch now FIRST in `on_battle_started` → `StoryShinyCatchStrategy` (catches with any
  usable ball — owned species/full party/any stage; out-of-balls mid-battle → fights
  through; zero balls / tutorial → fight-through). Proofs: `repro_shiny_noballs.py` A/B
  (parent flees / shiny fights on the same input) + `--driver shinytest` fault-injection
  (forced-shiny wild: 3 balls thrown → CAUGHT, with team-catch gating forced off).
- **Real-HW dock stall FIXED** (user's log: derail-loop at Dewford (11,9) on the open
  post-sail Letter-reminder msgbox): both sail legs + the derail recovery now B-ride any
  active script before waiting for control.
- **New Run-tab modes**: "Story (DEBUG)" (debug logger on, resume-anywhere) and "Story
  (DEBUG - RESET)" (debug logger + hard reset + forced NEW GAME; ⚠ the save-present menu
  branch still wants one real-profile validation — the harness profile has no in-game save).
- **FULL-ARC REGRESSION GREEN:** one story run post_rival.ss1 → sail → Letter → Brawly →
  sail → Slateport PC, ~75k frames, 0 derails/whiteouts — proves the dock fix end-to-end
  and that the shiny reorder didn't disturb normal battle routing.
- Punch list: +#24-interrupt (interruption intelligence), +#24-movelock (Disable/Encore/
  Taunt-aware move choice) — user's slate-for-later items.
- **REAL-HW TRIPLE-LOG REVIEW (user's 2nd-PC session):** DEBUG-RESET's forced-NEW-GAME-
  over-existing-save branch VALIDATED on a real profile (fresh run then played clean
  through Roxanne→PokéNav; abrupt log end = the user's SYSTEM crash mid Match-Call
  tutorial, no bot stall dumps). A second run validated the ENTIRE Ch5c→8a arc on real
  HW (rival→Briney ambush→sail→letter→Brawly→Slateport, 0 derails). Finding fixed:
  watchdog's `_SELF_RECOVERING_MODES` exact-name check missed the DEBUG variants
  (spurious restart after the intentional content-end Manual + save-state reloads
  silently re-armed) → `_is_self_recovering` prefix matcher, A/B-proven.
- **NEW: "Conduct Live Tests" capability** (`/livetest`, `tools/story-dev/livetest.py`):
  N-run batch sweeps (fresh→frontier or scoped from any checkpoint) in isolated
  parallel lane profiles + auto summaries → a LIVE TEST REPORT (frequency + context
  signature + universal-bug vs nuanced-situation triage) reviewed WITH the user before
  fixes. ‼ Keep `END_MARKERS` in livetest.py in sync with the story's content-end
  message whenever the frontier moves. Never run lanes while the user live-tests.

### ⭐⭐⭐ Session 2026-07-22 (Fable 5, latest) — CHAPTER 8a DONE: the bot reaches SLATEPORT (SANDBOX, pushed)
- **`sail_to_slateport()` BUILT + VALIDATED (0 derails)**: `brawly_done.ss1` → gym exit →
  Dewford heal → dock Briney (Up×1→A on his Cancel-defaulted multichoice — the stock helper
  would wrap onto Petalburg) → sail → Route 109 → Slateport → PC heal → clean stop.
  Checkpoint **`tools/story-dev/saves/slateport.ss1`** (Slateport (19,20), healed,
  `DELIVERED_DEVON_GOODS=False` = the Ch8b anchor). Two new engine rules learned + logged
  (playbook §7): object events are CAMERA-LOADED (use `approach_hint` on town-sized maps),
  and `multichoicedefault` menus need explicit cursor moves.
- **NEXT: Ch8b — Devon Goods → Capt. Stern.** Read the SlateportCity + OceanicMuseum decomp
  first (beat chain: Stern hunt → museum entry (fee?) → 2 Aqua grunt fights → Archie scene →
  `DELIVERED_DEVON_GOODS`). ‼ Gabby&Ty DOUBLE battle at (28,14)/(29,13) right next to Stern's
  pre-museum spot — the live testbed for the double-battle fix + the open framework rotation
  stall. Then Route 110 N → Mauville → Gym 3 (Wattson). Start from `slateport.ss1`.

### ⭐⭐ Session 2026-07-22 (Fable 5, later) — CHAPTER 7 DONE: Steven's Letter + KNUCKLE BADGE (SANDBOX, pushed)
- **`deliver_stevens_letter()` + `do_dewford_gym()` BUILT + VALIDATED**: full `--driver story`
  run `dewford.ss1` → Dewford PC heal → Route 106 → Granite Cave **five-warp ladder chain**
  (every floor is split; route dips through B2F — full pathfinder-verified graph in design
  §Ch7) → Steven (7,8), Letter delivered (TM47) → reverse chain (1F one-way-ledge shortcut)
  → PC heal → dark gym → **Brawly beaten, BADGE02** — **0 derails / 0 whiteouts** (ch7_run7).
  Checkpoint **`tools/story-dev/saves/brawly_done.ss1`** (Dewford Gym (4,4), flags verified).
- **NEW primitive `_walk_warp_chain`** (furthest-along pathable step — first-match loops on
  one-way ledges) + `_enter_warp_by_navigation` (warp-entry with map-change detection +
  last-error reporting). Segment-6 sail gate now a pre-sail map WHITELIST. Checkpoint capture
  rides out leftover dialogue first (dewford.ss1 v1 loaded non-controllable; repaired).
- Brawly prep is FLOOR-ONLY (band 14-16): **no training grass exists around Dewford pre-Surf**
  (Route 106/107/Dewford = surf-only tables; Granite Cave wilds L6-10) — `training_areas.py`
  updated; loss-escalation falls back to the (slow) cave spot. KI-10 logged (post-sail
  mainland respawn edge; mitigated by the early Dewford heal).
- **NEXT: Ch8** — Briney at the Dewford dock (12,9) → sail to Slateport (read the DewfordTown
  decomp for gating: likely needs the Letter delivered — we have it), Route 109 → Slateport
  (Stern/Museum; ‼ Gabby&Ty DOUBLE battle — also the live testbed for the open framework
  rotation stall) → Route 110 → Mauville → Gym 3 (Wattson). Start from `brawly_done.ss1`.

### ⭐ Session 2026-07-22 (Fable 5) — CHAPTER 6 DONE: the bot sails to Dewford (SANDBOX, pushed)
- **`sail_to_dewford()` BUILT + VALIDATED end-to-end** (post_rival.ss1 → Dewford dock (12,3)):
  Rustboro → Route104 north → back through Petalburg Woods (river-split, doorprobe-verified
  warp table in design §Ch6) → south beach → Briney's cottage (17,50) → first-sail **YES/NO**
  (decomp correction: the multichoice is only for later sails) → sail → DEWFORD_TOWN.
  Proven BOTH via `--driver saildewford` AND the real `StoryMode._play` (Segment 6 wired,
  guard map==DEWFORD, clean content-end stop). Checkpoint **`tools/story-dev/saves/dewford.ss1`**.
- **NEW primitive `_talk_to_wandering_npc`** — Briney PATROLS his cottage (as does Peeko);
  4 approaches failed provably before the winner: observe a patrol lap → park BESIDE his
  route → face-tap+A as he transits. Full saga + prevention rules in 08-MISTAKES (2026-07-22)
  + playbook §7 (incl. the `calculate_path`-blocks-walkers gotcha and the three-body
  route-tile deadlock). `STORY_TALK_DEBUG=1` traces the helper.
- Daily upstream check done (main still `5dd898f8`).
- **NEXT: Ch7** — Dewford → Route 106 → Granite Cave 1F→B1F→Steven's Room (7,8): deliver the
  Letter (A-through, no choices; sets `DELIVERED_STEVEN_LETTER`, gives TM47) → back → Gym 2
  **Brawly** (dark gym; type-aware lead — Taillow/Flying resists Fighting; level-floor;
  attempt-cap) → `BADGE02_GET`. Start from `dewford.ss1`; §Ch6–8 has the map facts
  (⚠ validate the cave floor-warp chain + Dewford door warps live).

### ⭐ Session 2026-07-21 (late) — battle-robustness + provisioning fixes (SANDBOX, pushed)
All from real-hardware debug logs; each reproduced + fixed + committed:
- **Faithful PokéNav Match-Call tutorial** now works (bot calls Mr. Stone; renderer-gated,
  state-write fallback). Confirmed on real HW.
- **Rustboro rival** wired (§5c): type-aware lead (Taillow beats grass Grovyle) + whole-team
  **level floor ≥10** + safe heal + attempt-cap. **Failed-rival stuck-at-(16,53) bug FIXED**
  (re-engage keyed off the live battle, not the persistent MET flag). A full fresh run BEAT
  the rival → `post_rival.ss1` captured (Rustboro (16,53), STATE=8).
- **Double-battle after-faint hang FIXED** (`level_up.py` chooser dropped the on-field-partner
  exclusion → returned the partner's slot). A/B proven.
- **Gym/trainer fight-through FIXED** (Roxanne hung switching Torchic into a weak bench):
  trainer/gym/E4 battles now attack-through, never rotate/flee into a stall. A/B proven.
- **Premier Ball batching**: buy Poké Balls in tens → 1 free Premier Ball each (validated +2).
- **OPEN (framework):** the mid-battle **rotation-execution** stall
  (`battle_action_selection.py`) still exists for any rotating strategy — needs a live repro to
  pin `map_battle_party_index` / the party-menu submenu. Story bot sidesteps it in trainers.
  (The sail leg that was queued here is DONE — see the 2026-07-22 session block above.)

## What this project is
Documents and enhances 40Cakes/pokebot-gen3 (Python shiny-hunting bot for
Gen-3 Pokémon via libmgba). Layout (details in CLAUDE.md "Project rules"):
- `40cakes repo/pokebot-gen3/` — PRISTINE upstream mirror (git subtree,
  remote `upstream-pokebot`, commit `5dd898f8`). Daily upstream check;
  record in `40cakes repo/UPDATE-LOG.md` (last check 2026-07-19, unchanged).
- `40cakes repo/DOCUMENTATION/` — verified dev docs of the ORIGINAL program.
- `custom-pokebot/` — OUR PRODUCTION fork; divergences in `DIVERGENCE-LOG.md`.
- `sandbox-pokebot/` — experimental copy; new work is built + verified here,
  then PROMOTED into custom on the user's explicit OK.
- `install.py` (repo root) = custom installer; `install_sandbox.py` = sandbox.
- `Pokemon_Emerald_AI_Notes.md` — transfer notes for the sibling AI project.

## HISTORICAL — what was WHERE as of 2026-07-21 (‼ NOT current state)

> **‼ Read `## ‼ YOU ARE HERE — 2026-07-25 (late), the COUNTER system` below for the
> CURRENT state.** Everything in this section is a snapshot from **2026-07-21** and is
> now roughly eight chapters stale — it ends at "Frontier: PokéNav + tutorial done",
> whereas the bot now reaches **Badge 6 (Winona), the end of built content**. It is kept
> because the per-feature promotion history and the Rustboro-era atlas notes are still
> useful; do not read any sentence in it as describing today.

### ⭐ PROMOTED to custom (production) 2026-07-21 — commit `a9553ee4`
This session's Story-mode work is now in `custom-pokebot`: matured defeat/whiteout
recovery (no Manual / no save reloads; resumable Segment 1), the Oldale heal-loop fix,
StoryCatchStrategy (flee-not-Manual when out of balls), SwapTrainBattleStrategy
(swap-training + finish-don't-flee), whiteout-aware `_story_spin`, `training_areas.py`
groundwork, and the opt-in Debug Logging toggle (`modules/debug_logger.py`). 10 code
files copied sandbox→custom (verified clean superset); DIVERGENCE-LOG updated for the
upstream-file edits (heal exit, main.py debug hook, GUI toggle). Sandbox now matches
custom on these files (test harness / profiles / SANDBOX-NOTES stay sandbox-only).
**Real-hardware validated through:** fresh save → Oldale → rival → Pokédex → Petalburg
→ Wally → Woods → Rustboro → pre-gym catching + swap-training.
**SOLIDIFY-RUSTBORO pass DONE (2026-07-21, promoted `395c392d`/`f04e2c01`):**
(1) Resume edge fixed — Segment 3 recognizes the whole Rustboro area (Route 116 mid-
training resume no longer backtracks). (2) `_lead_strongest_battler()` leads the gym with
our best mon. (3) Training-grind fixed — `_prepare_for_fight` readies only the primary +
near-band battlers (`train_team(slots=)`), leaving fresh low catches to level organically
(#24-team). **Full flow VALIDATED end-to-end in-harness: route116 save → minimal prep →
BEAT ROXANNE (Stone Badge, Mudkip→Marshtomp) → Devon Goods (Rusturf) → clean content-end
stop, 0 whiteouts.**
**NEXT-CHUNK PASS started (2026-07-21, SANDBOX checkpoint, NOT promoted):**
Rustboro mapped statically (Devon Corp floors + Mr. Stone 3F (15,5), rival NPC city (16,50),
PC/Mart/Gym entrances) → §Ch5b Atlas + Hardening Checklist in 12-STORYMODE-DESIGN.
`return_devon_goods_and_get_pokenav()` BUILT + VALIDATED (gets the PokéNav).
**✅ PokéNav Match-Call tutorial SOLVED (2026-07-21, SANDBOX, NOT promoted).** Root-caused
(WebFetch pokeemerald + harness obs): after the PokéNav the game auto-walks you into the
city; the map ON_FRAME (`VAR_RUSTBORO_CITY_STATE==6`) fires the Scientist tutorial → intro
msgboxes → start-menu multichoice (case 3 = POKéNAV) → PokéNav app in
`POKENAV_MODE_FORCE_CALL_READY` (must place a Match Call). **The app does NOT advance in
our headless harness** (proven: 150 A-presses/1500f = 0 progress). Fix (user chose FAITHFUL):
`handle_pokenav_match_call_tutorial()` **actually plays the tutorial** — opens the PokéNav,
Down,Down→MATCH CALL→A→list→A→CALL→A (calls **Mr. Stone**)→advance→B out→
`RUSTBORO_CITY_STATE=7`. This works because the PokéNav app only advances with the **renderer
ON** (`context.video=True`, which the real bot has); harness needs `--video`. **Proven
end-to-end via `_play` (video on): app opens, call placed, clean stop, NO fallback used.**
FALLBACK: headless/stall → `skip_pokenav_match_call_tutorial()` (state-write to vanilla's
exact end-state) — never hangs. **Wired into `_play` §5b → clean stop.**
**REAL-HW RUN (2026-07-21 debug log) confirmed: faithful PokéNav tutorial WORKS (called Mr.
Stone). Losing the rival stranded the bot at (16,52) → Manual — FIXED + validated** (the Down-step
loop keyed off the persistent MET flag; now keys off actual engagement → retries re-engage).
Added (user directive): whole-team **LEVEL FLOOR ≥10** (escalating) + **safe PC heal** right
before the rival, and raised the training heal margin so the swap-train finisher heals earlier.
**✅ FULL FRESH RUN BEAT THE RIVAL + post_rival.ss1 CAPTURED (2026-07-21).** A from-scratch
headless run (new game → … → Rustboro rival) with the fixes won the rival with a NATURAL team
(led Taillow L17 = Flying, resists Grass + hits Grovyle 2×; team Dustox L16 / Marshtomp L18 /
Taillow L17 / Poochyena L16, all ≥10). **No faint-hang recurred** (heal-margin mitigation +
a real team). **`post_rival.ss1`** (scratchpad, regenerate via the fresh run if needed) is
validated: `DEFEATED_RIVAL_RUSTBORO=True`, `RUSTBORO_CITY_STATE=8`, controllable at **Rustboro
(16,53)** — i.e. the rival cutscene leaves you at (16,53) in Rustboro; walk SOUTH from there off
the map edge onto Route 104. The choose-after-faint framework hang is now a rare latent edge
(mitigated, didn't trigger) — still worth a proper fix but not blocking. **NEXT: build the sail
leg from post_rival.ss1 — walk south (16,53)→Route 104→Mr. Briney's house→talk Briney→Dewford
(§Ch6 atlas).**
**Rustboro rival: WIRED (§5c) with type-aware lead + attempt-cap (user-chosen).** Trigger =
coord row y=53 x12-19 (gated VAR==7). §5c: `_prepare_for_fight(band 16-19)` →
`_lead_best_matchup(["Grass"])` (avoids the 4×-weak Marshtomp; validated vs the type chart —
picks a 1× mon) → `fight_rustboro_rival` (stage (16,52), Down across y=53). `RIVAL_MAX_ATTEMPTS=3`
bounds the whiteout→retrain retry (thin team stops cleanly, no loop). Verified: wiring runs
error-free (enters training). ⚠️ **NOT yet validated: an actual rival WIN** — the `devon_done`
test save has a pathological team (Marshtomp + L7-8 filler) that loses regardless of lead. **To
prove the win we need a NATURAL post-gym team save** (ask user for one, or build via a fuller
harness playthrough). **Frontier: PokéNav + tutorial done, rival wired-but-win-unvalidated.** NEXT-AREA MAPPED
(design §Ch6 atlas: Route 104 S → Mr. Briney (sail) → Dewford → Granite Cave (Steven's Letter)
→ Gym 2 Brawly — all warps/NPCs/coords). **Sail-leg build is GATED (see §Ch6 SAIL-LEG RECON
NOTE):** (a) need a real post-rival save (rival cutscene deposit position unknown; a synthetic
rival-flag state stalls at Rustboro (16,53) — the Rustboro-south↔Route104-north corridor needs
recon), and (b) the Briney sail mechanic is understood (talk (5,3) → multichoice → Dewford=idx0).
**NEXT: confirm rival win on real hardware → capture a real post-rival save → build the sail leg
from §Ch6.** Open: #24-team organic-team leveling; #24-trainmap area-training groundwork.
### In custom-pokebot (PROMOTED, production) — big promotion `f0b275f3` (2026-07-19)
Native dashboard GUI (default; `--classic-gui` = stock), handheld mode,
backup/restore + cloud + cloud-save-sync (off by default), macros, Patrol
v3 (multi-map/global-nav), gamepad in-game input, shiny alerts, update
notice, game cheats, tabbed GUI, full-dex sprite picker. Stock auto-updater
footgun fixed (ML-4). Installer V2 done. Requirements install-only-missing.
User confirmed the native GUI + installer hands-on ("worked!").

### In sandbox-pokebot ONLY (BUILT + self/fact-verified, NOT yet promoted)
All 2026-07-19, awaiting user review/promotion:
- #33 GUI fixes (left party always visible; Pokéball-open/Hide both modes)
- #22 Watchdog/auto-recovery · #9 Hunt Planner v1+v2 (encounter index +
  travel-and-hunt) · #23 Living-Dex Orchestrator · #11 Analytics (stats
  browser/trend/luck meter)
- #30 handheld menu→Play-tab + Left Party Section + hover · #31 money cheat
  + Lock · #32 gamepad GUI-nav (adversarially verified clean)
- Adjustments #36–#40: bigger party balls (140px), themed hover tooltip,
  gamepad-nav gated to drawer, auto-decline move learning (`new_move:
  cancel`), catch-ball allowlist (protects Master Ball)
- Living-Dex deepening: #43 opportunistic catching · #44 party ball moved
  to hover (strip now clean) · #41-evo obtainability(evolution) + #42-easy
  capability gating · #41-research Emerald obtainability lists.
  **Census (sums to 386): wild 132/evolution 149/gift 7/static 8/roamer 1/
  event 6/breeding 3/special 1/unobtainable 79 → 217/386 obtainable in
  Emerald without trading.** `modules/data/emerald_obtainability.json`.

### Live-verified on the USER'S REAL SAVE (`Nick - Emerald`, placed in both
bots' gitignored profiles/): real shiny party renders (Celebi/Sceptile
Lv100…), money cheat read real 7,908, analytics read real 57,436
encounters/10 shinies ("lucky"), capability gate read real Old/Good/Super
Rod. Save left md5-identical after every test.

### Dex data (#34/#35 tabs not built yet)
`modules/data/generated/pokedex_data.json` = 386 species COMPLETE except
`dex_artwork` (stats/learnsets/evolutions/sprites/category/height/weight/
flavor all done, Phases 1/2/3a). `itemdex_data.json` = core (309 items);
gaps = map_locations/mart/pickup/historical.

## ‼ YOU ARE HERE — 2026-07-25 (late), the COUNTER system

**Everything committed and pushed. Tree clean.** The session that produced this was very long;
prefer these files over any transcript.

### The headline: Badge 6 from a COLD START
A fresh title-screen run reached the **end of built content** (f2.48M, 38 maps, **0 derails**).
The Fortree rotating-gate puzzle is solved live (`modules/story/fortree_gates.py`, a port of the
decomp's `src/rotating_gate.c`, validated **4/4** against the emulator). Next unbuilt chapters:
**Mt. Pyre, the Magma hideout.**

### The problem now being solved — `#24-counters` (KI-23)
The user's overnight logs: **198 Winona attempts, 41 losses, 41 whiteouts, never won**, with a
party FAR ABOVE her levels (Sceptile L42 vs her L29-33). It lost on TYPES, not levels — Sceptile
is resisted by Flying, Ninjask is itself part Flying, nothing was Electric/Rock/Ice.
**Boss-as-training-vehicle cannot converge without a type answer, and levelling does not help.**

Four pieces, each independently PROVEN, being connected in this order:
| piece | file | state |
|---|---|---|
| detect non-convergence | `story_mode._boss_plan_is_hopeless` | done; Winona now goes through `_prepare_for_fight` (she never did before — the guard could not fire on the one boss that motivated it) |
| identify needed types | same | done; computed from the real type chart, not a table |
| find catch candidates | `modules/story/counter_plan.py` | done; over the whole-game encounter index |
| region reachability | `modules/story/region_reach.py` | done; **KI-24 fixed for BOTH consumers** as of 2026-07-25 — counter selection AND the training gate |
| wire them together | — | IN PROGRESS at session end |
| execute (travel/catch/train) | — | NOT STARTED |

### Four traps a future session must not re-walk
1. **`calculate_path` is unsound at REGION scale** (KI-24). It reads the Route 118/119/120
   dual-elevation bridges as walls, so it reported Route 118 — the real Winona answer — as
   unreachable, and it fails even on a same-map Route 119 walk. **Both consumers now use
   `region_reach`** — `_counter_area_allowed` and, as of 2026-07-25, `_training_area_allowed`.
   Never reach for `calculate_path` to answer "can I get to that map"; it is correct only for the
   final tile-level leg once already ON the map. Measured effect of the training-gate switch: the
   Winona candidate list went from `[False × 10]` to `[True × 5, False × 5]`.
   **The whole story-bot repro suite is GREEN (5/5):** `repro_fodder_grass`, `repro_counter_plan`,
   `repro_counter_wiring`, `repro_region_reach`, `repro_boss_plateau`.
2. **Hop count is a FILTER, not a RANK** (KI-24b). Measured from ROUTE120: Fortree 1, Route119 2,
   **Lilycove 2**, Route118 3, Mossdeep 4, Pacifidlog 10 — Lilycove is *closer* than the answer,
   because one connection can span a whole sea route. Use `max_hops=4` as a sanity bound and let
   `counter_plan`'s own criteria rank.
3. **Event flags are not all monotonic** (KI-21) and **whiteout wipes the Elite Four flags**
   (KI-22). `_done()`-style resume gating assumes flags stick; for Ch16 that is false.
4. **‼ Expect a fix in a well-tested area to turn something RED for the WRONG reason.** Much of
   this suite was written to CHARACTERISE defects, so some assertions require a FAILURE to occur
   ("at least one unreachable", "raises", "returns empty") and invert the moment that failure is
   repaired. **Two were found this way on 2026-07-25 alone**, and neither would ever have been
   noticed while green. When a fix reddens a test, the first question is not "what did I break"
   but "was this assertion depending on the thing I just fixed?" — see the 08-MISTAKES pattern
   entry (2026-07-25).

### Research: five `CLAUDE-VALIDATED-*` files, ~175 claims grounded in the real decomp
Indexed in `ai-research-notes/00-READ-THIS-FIRST.md`. **Gemini notes are LEADS ONLY** — a Claude
subagent with tool access is the final word (`CLAUDE.md`). Best grounding method found: a local
sparse clone of pokeemerald (~44 MB) — it makes ABSENCE claims checkable, which per-file API
fetches cannot do.

### Top open items
1. **`#24-counters` phase 2** — now the #1 item. The bot DIAGNOSES a hopeless boss plan and names a
   concrete reachable counter, then stops. Travelling to it, catching it and training it is unbuilt.
   `#24-whiteout` collapsed into this (below), so they are one problem from two ends.
2. **`#24-npcheal`** — re-pair Route 111 training to `ROUTE111_OLD_LADYS_REST_STOP` (decomp-cited
   full ungated repeatable heal, 96 steps vs 213 to Fallarbor). Needs a heal-at-NPC helper.
3. `#24-counters` phase 2 (the chain NAMES a counter; acting on it isn't built).
4. `#24-edgecost`, `#24-regionreach` gate table, KI-18 live confirmation.

### 🏁 SESSION END 2026-07-26 — state, and the ONE thing waiting on the user

**Everything is committed and pushed. Tree clean, branch `main`, in sync with origin. Suite 10/10
green.** Upstream unchanged (`5dd898f8`, daily check done 2026-07-26).

**⏳ WAITING ON THE USER — a ~2 minute smoke check, not a test run.** The ENDLESS-RESET *video*
fix can only be validated on their setup: the headless livetest harness never enables the renderer
and never runs ENDLESS RESET, so no batch I run can see it. Start ENDLESS RESET with video ON, let
run 1 finish and run 2 begin, then stop, and check:
* does the renderer STAY on into run 2? (before the fix it was forced off)
* does the log say **`"calling Mr. Stone"`** rather than `"state-write to vanilla end-state"`?
If both hold, `#24-pokenav-faithful` is cured and the next long run exercises the faithful path.
‼ **The user's checkout is a DIFFERENT working copy** (`OneDrive\Desktop\pokebot gen3 v3\...`) —
they must `git pull` there or none of today's fixes are in their runs.

**Per the batching directive (06-DECISIONS 2026-07-26): do NOT ask for a full validation run yet.**
Accumulate the next chunk of fixes first. What is already landed and awaiting that run: the
out-of-PP livelock fix, the ENDLESS-RESET video fix, survival mode, the Route 111 memory, the
plateau guard recalibration, cost-based counter ranking, and the Victory Road gate.

**NEXT WORK, in order:**
1. **`#24-counters` phase 2 executor, built as CATCH-AND-LEAVE** (see the reframe below and §CC2).
   Do not reuse `train_team` at the hunting ground — Fiery Path's heal leg cannot complete.
2. `#24-whiteout` residual attrition — batch `20260726-094520` run02 showed 23.8% flee / 82 losses /
   40 whiteouts / no frontier. The new `flee_rate` metric is how to watch it.
3. `#24-pokenav-faithful` — likely already cured by the video fix; confirm from the smoke check
   before spending anything on it.

### 🧭 2026-07-26 — phase 2 REFRAMED: catch-and-leave, not train-in-place
**Read `12-STORYMODE-DESIGN.md` §CC2 and its three updates before touching `#24-counters`.**

**Cave support is BUILT and proven; the Fiery Path tile is deliberately NOT promoted.**
`_exit_training_cave_if_inside` / `_goto_training_area` are now ROM-verified tables
(`_CAVE_EXITS`, `_CAVE_ENTRANCES`), and `story_harness.py --driver fierycave` proves legs 1-2:
Lavaridge → Fiery Path (18,19) **PASS**, exit the cave **PASS**. Leg 3 (heal at Lavaridge) FAILS —
`calculate_path` is ASYMMETRIC on the identical pair (Lavaridge→door OK at 60 waypoints,
door→Lavaridge FAILS). Route 112's ledges make the return one-way.

**‼ THE REFRAME.** A counter HUNT does not need a heal loop at the hunting ground: it needs to
travel, catch, and LEAVE, then train the catch somewhere that does have a working heal trip. That
sidesteps the failing leg entirely and is a better fit for phase 2 than reusing `train_team` in
place. Build the executor that way, not around the training loop.

**Guard rails now in code so this cannot be re-derived:** `training_areas.NO_RETURN_GROUNDS`
(JAGGED_PASS / ROUTE112 / FIERY_PATH, each with measured evidence + date). BOTH training pickers
refuse those maps BEFORE any reachability check — they ARE reachable, which is what made them
dangerous. `repro_no_return_grounds.py` pins it. ‼ This existed as PROSE since 2026-07-23 and was
re-derived by a 30-minute probe cycle anyway — see 08-MISTAKES 2026-07-26. **Grep the decision code
(`training_areas.py`, `KNOWN_GATES`, `_CAVE_EXITS`) for a map name before probing it.**

**Suite is now 10 files.** `repro_no_return_grounds`, `repro_cave_exit_table`,
`repro_out_of_pp_livelock` joined the seven.

### 🚨 2026-07-26 — OUT-OF-PP LIVELOCK from the user's real hardware, + a harness blind spot
**User reported "a shiny pre-Pokédex crashed the game — maybe disable shiny logic until the
Pokédex".** ‼ The shiny was a RED HERRING and that fix would have changed nothing: the shiny path
worked correctly ("no catch possible here, fighting through"), WON the battle, and the run
continued **1.86 million frames**. The "reset" was ENDLESS RESET starting run 2 on budget expiry.

**The real bug — a livelock that can strand ANY cold start.** Outcome tally for that run:
**3,011 `RanAway` · 5 `Won` · 1 `Lost`**, `Treecko L6 21/21` (FULL HP) parked on the Route 103
training tile at "training the starter to Lv 8", ~2.9M frames, not one level gained.
HP and PP do not deplete together: a starter that WINS without being hit keeps full HP while its
only attacking move drains; once PP is gone the stock strategy finds no usable move and takes
`lead_cannot_battle_action` (default **flee**); fleeing takes no damage, so HP stays at 100% and
`train_team`'s **HP-only** heal gate can NEVER fire. Fixed: `_team_is_out_of_pp()`, and the
training loop now stops spinning AND heals on *low HP **or** out of PP* (a Poké Center heal
restores PP too, so it reuses the existing heal). A/B on the exact logged state:
`old_gate=False → new_gate=True`. `repro_out_of_pp_livelock.py`, 6 cases.

**‼ AND MY OWN BATCHES WERE BLIND TO IT.** Running the same tally over batch `20260726-052205`
returned ZERO outcomes for all five runs — `story_harness.py` never logged an outcome, only
`battle_is_active -> False`. Five cold starts could not have reported this class, and I had already
reviewed that batch as validated. Now: the harness logs `outcome=BattleOutcome.X`, and `livetest.py`
reports `battles=N flee=NN%` with a **‼LIVELOCK?** marker at ≥80% flee over ≥50 battles (validated
against the user's real log: flee_rate 0.998).
**Second measurement blind spot in two days** (the whiteout metric read 0 for every batch ever).
Treat any metric never cross-checked against a raw count as broken until proven.
⏳ A 5-lane validation batch for the PP fix is RUNNING at the time of writing — read its
`flee_rate` first; it is now the cheapest health signal a batch produces.

### 🎯 2026-07-26 — phase-2 groundwork: ranking, gate, and the ECONOMICS that decide it
Batch `20260726-052205` validated the day's guards and found two defects in them (both fixed —
see below). Then three phase-2 blockers were worked, and one produced a finding that should shape
whether phase 2 gets built at all.

**‼ VERDICT: BUILD PHASE 2 — the economics now support it.** (An earlier note today said the
opposite; it was true of the candidate list as it stood and the constraint causing it has been
removed. Superseded — do not act on it.) The blocker was the hop FILTER, not reachability: from
the real pre-Norman anchor every Fighting-counter map is 5-7 hops while `_counter_area_allowed`
used `max_hops=4`, so it admitted only the nearest map and excluded the cheap ones — the
encounter-rate mistake in different clothing. With `COUNTER_MAX_HOPS = 8` the live list is now
**Machop/JAGGED_PASS 75,949 · Machop/FIERY_PATH 168,616 · Makuhita/GRANITE_CAVE 315,260**, and
Victory Road is correctly gated out. Against the measured 399,000-508,000 frames of LOSING to
Norman, the top candidate is **5-6x better than doing nothing** (it was 9%).
‼ Caveat: `region_reach` does not model ledge directionality and Jagged Pass has known one-way
ledges, so rank 1 may be a wrong YES — run `probe_counter_tiles.py --nav` before trusting it.
`_training_unreachable` bounds that to one wasted walk, and rank 2 (FIERY_PATH) is on the Ch10
route and traversable both ways. Full numbers: `12-STORYMODE-DESIGN.md` §CC2 + both updates.

* **Blocker #2 CLOSED — candidates rank by COST, not encounter rate.** `rate * 1_000 - level_gap`
  outweighed level fit ~1000×, so a L6-10 Makuhita (50%) beat a L20-22 Machop (25%) for a L31 team
  — measured, the preferred pick was **4.2× more expensive** (315,260 vs 75,949 frames). `tier` is
  now separate from `score`; within a tier candidates sort by `est_frames` (frames to FIND + frames
  to TRAIN to the team's level). Unpriceable sorts LAST (unknown ≠ cheap); with no team level it
  degrades to the old ordering, so existing callers are unaffected.
* **Blocker #3 CLOSED — Victory Road is gated on Waterfall.** Cost ranking made this urgent:
  Hariyama is L38-42, already above the team, so its training cost is ~0 and it ranks **#1** the
  moment anything calls the map reachable. Only `max_hops=4` had been keeping it out — luck, not a
  gate. Probed: the ONLY boundary edge into the whole cluster is
  `EVER_GRANDE_CITY (0,8) <-> VICTORY_ROAD_1F (24,43)`. One entry closes every floor.
* **‼ BLOCKER #1 SWEPT (2026-07-26) — a tile is FOUND but deliberately NOT promoted.**
  `probe_counter_tiles.py --nav` from `lavaridge.ss1`: **FIERY_PATH (18,19) OUT = OK** (the tile is
  real); JAGGED_PASS **FAIL** — it reached (14,40) then could not path WITHIN the map, confirming
  the one-way-ledge caveat, i.e. cost-rank-1 was a wrong YES; GRANITE_CAVE **FAIL** — routes via
  ROUTE106, a sea route, so it needs Surf from Lavaridge.
  The Fiery Path RETURN leg failed *inside the cave* — the known warp-level limitation that
  dropped two real-HW runs to Manual (2026-07-22). `_exit_training_cave_if_inside()` handles it and
  is **hardcoded to GRANITE_CAVE_1F**. **NEXT STEP, precisely:** generalise it to a
  `{cave map: exit warp tile}` table covering FIERY_PATH, prove the exit with a repro from a tile
  deep inside, THEN promote `(MapRSE.FIERY_PATH, (18, 19), (15, 16))` into `TRAINING_GRASS`. That
  one promotion unblocks phase 2's executor.
  Hop counts are strongly ANCHOR-dependent (Route 102: Fiery 7 / Granite 5; Lavaridge: Fiery 2 /
  Granite 10-11) — the counter list is position-sensitive by design.
* **Blocker #1 background — the maps are CAVES.** The counter maps are CAVES — encounters come
  from the cave FLOOR, so ANY walkable non-warp tile is a valid spin tile and no `MB_TALL_GRASS`
  sweep applies (which is why `jaggedgrass_probe.py` finds nothing there). Counted, with the most
  central: FIERY_PATH 269 `(18,19)` · JAGGED_PASS 367 `(16,22)` · GRANITE_CAVE_1F 201 `(22,7)` ·
  GRANITE_CAVE_B1F 291 `(16,12)`. **Next concrete step:** run
  `tools/story-dev/probe_counter_tiles.py --nav` (two-way navigation from the anchor), then
  promote whichever passes into `TRAINING_GRASS` — that is the last thing standing between the
  diagnosis and a working executor.
* Still open: #4, story interiors (`GRANITE_CAVE_STEVENS_ROOM`) are proposed as hunting grounds.

### ✅ 2026-07-26 — SURVIVAL MODE closes the travel-attrition half of `#24-whiteout`
The batch's largest loss cluster is fixed: **25 whiteouts on ROUTE110 in one run** (31 of 66
batch-wide). It was NOT training attrition — with no `train_team` session running,
`on_battle_started` falls through to `LevelUpTravelBattleStrategy`, which fights every wild to
level the lead and "flees only at low HP, which the training loop covers by healing". On a TRAVEL
leg there is no training loop, so nothing heals and HP only falls until the party wipes.
Now: after **3** defeats on a map, wild battles there are FLED (`SURVIVAL_WHITEOUT_THRESHOLD`).
Wild only (trainers are un-fleeable; the boss/gym path is untouched), never during `train_team`,
per-map. `repro_survival_mode.py` (7 cases) asserts each limit and flees on the real run01 state.
‼ **Read the 08-MISTAKES entry before editing `on_battle_started`:** the first version silently
did nothing because several branches of that method import `console` locally, which makes the name
function-local for the WHOLE method — so a module-level `console.print` is an `UnboundLocalError`
that a surrounding `except Exception: pass` reports as "condition False". The warning was
commented 16 lines above where I wrote it, and I still hit it.
**Suite is now 7/7** (`repro_survival_mode` and `repro_training_unreachable` joined the five).

### 🧪 2026-07-25 — LIVE BATCH `20260725-194810`: the day's fixes hold; 2 new issues fixed
5 fresh cold-start lanes, 3M frames, commit `26613bcb`. **1/5 reached the frontier (baseline 0/5)**,
**0/5 move-learn deaths (baseline 2/5)**, 66 losses (baseline 128). Batch dir has `REVIEWED.md`.
* **All three of the day's fixes confirmed live.** The `CantForgetHM` branch fired **44 times** —
  the wedge situation kept arising and kept being handled, which is stronger than "it didn't occur".
  The plateau guard fired on Norman at **exactly 6 losses** (was 27). The counter chain ran
  end-to-end for the first time and named `Makuhita (Fighting), Granite Cave 1F, L6-10, 50%`.
  The battle-fault channel never triggered — still repro-only evidence.
* **Fixed: a wrong YES from `region_reach` cost the RUN, not a walk** (killed 2/5). ROUTE111's
  training tile is FALLARBOR-SIDE ONLY but the map is reachable from Mauville, so the gate passed
  and the walk died at the desert — then every derail re-picked the SAME tile. New
  `UnreachableDestinationError` + a `(standing map, target map, tile)` memory. ‼ Read the
  08-MISTAKES entry: "recoverable" describes the LOOP, not the failure.
* **Fixed: `livetest.py`'s whiteout metric always read 0** — it counted a debug-log-only string.
  ‼ **Ignore the `whiteouts` field in every archived batch summary.** Now also emits `losses` and
  `losses_by_map`, automating the census that redirected `#24-whiteout`.
* **Found, NOT fixed — training-loop attrition has no give-up guard.** run01 lost **25 times on
  Route 110** swap-training a lopsided team, KOs flat at 1. Same plateau shape as Norman; the guard
  covers configured BOSSES only. Now the largest single loss cluster (31 of 66). See `#24-whiteout`.

### 📊 2026-07-25 (later) — `#24-whiteout` MEASURED: it is gyms, not attrition
Do not redesign healing/travel for this. Census of all 5 night5 runs (~128 losses; **losses and
whiteouts are 1:1** — there is no potion/revive layer, so losing always means whiting out):
**~83% of losses are GYM LEADERS** — Norman 38, Wattson 24, Winona 20, Flannery 18, Route110 10,
Dewford+Rustboro 6. The cost is the **boss-as-training-vehicle** strategy, and it is a PLATEAU, not
slow progress: run3 made **27 Norman attempts over 508,000 frames** (~19k each) for **+2-4 levels**,
with **KOs flat at 1-2 of 4 across all 27** and a **L15 Shroomish** carried untrained throughout.
* **Fixed:** `_boss_plan_is_hopeless` was **power-blind** — it accepted **Rock Smash (20 power)** as
  a super-effective "answer" to Norman (Fighting is 2.0x vs Normal, and that HM is one the bot is
  REQUIRED to carry), so the guard could never fire on the boss that needed it most. Now needs
  `base_power x effectiveness x STAB >= CREDIBLE_ANSWER_POWER` (60). A/B on the real logged party:
  `(False, []) -> (True, ['Fighting'])`. Its `except Exception` also used to return the SAME value
  as success — a silent self-disable — and now warns.
* ‼ Reading the night5 logs: they launched at **07:36**, and the entire counter chain landed
  **after** (09:47 → 13:27). Anything those logs show about non-convergence pre-dates the guard.
* **Still open** (now `#24-counters` phase 2): the bot stops with a named counter instead of going
  and getting it. Also unbuilt: a provisions/healing layer so a loss isn't automatically a whiteout,
  and benching dead weight (a L15 in a L30+ team is a free loss).
* Tests: `repro_boss_plateau.py` CASE 5 = the REAL run3 party + its real KO trace; CASE 6 guards
  against over-correcting the threshold (STAB Double Kick, the organic Norman win, must still count).

### ✅ 2026-07-25 (later) — `#24-movelearn-recovery` CLOSED (was the #1 open item)
The move-learn wedge that killed 2 of 5 night5 cold-start runs (~f1.55M each) is fixed and
A/B-proven from the real captures. **Read the changelog entry before touching move-learn code** —
the filed diagnosis was only the last of FOUR links, and three of them are still worth knowing:
* The game says **`Task_HandleInputCantForgetHMsMoves`** ("HM moves can't be forgotten") and until
  now nothing in the codebase referenced that symbol — `get_learn_move_state()` reported it as the
  Yes/No prompt, because the script pointer stays parked at `BattleScript_AskToLearnMove+0x11`.
* The actual hang was an **unbounded "screen is still opening, just wait" branch**: zero inputs for
  6,000 straight frames. Found by instrumenting BUTTON PRESSES, not states — the before-arm read
  `{'B': 4050, 'A': 1350}` with **no `Down` at all**, which is exactly 3×1800 escape-valve presses
  and proved the main handler pressed nothing.
* The cursor in `sMonSummaryScreen` is **not trustworthy until the move-select input task is
  active**; a stale read is how an HM got confirmed while the decision was DECLINE.
* New: **`modules/battle_fault.py`** — battle handling is a SIBLING generator on
  `context.controller_stack`, not nested in the mode, so a `BotModeError` from battle code can
  never reach `StoryMode.run()`'s `except`. Faults now travel by an **opt-in channel**
  (`handles_battle_faults`) and cost one derail. Stock modes are provably unchanged.
Assets: `saves/movelearn_hmwedge_{quickattack,slash}.ss1` (real wedge states, rescued from the run
profiles before the next batch could overwrite them), `repro_movelearn_hm_wedge.py`,
`repro_movelearn_fault_recovery.py` (stock / optin / story arms). Suite 5/5 green.
⚠ `repro_hm_replace_valve_forced.py`'s default budget was raised 25,000 → 35,000: bounding the wait
costs more emulator frames per iteration, so the third strike moved to f27,583 and the repro
*looked* like a regression when nothing had changed.

## Earlier — 2026-07-25, overnight autonomous research stretch

**State: everything committed and pushed. Working tree clean apart from gitignored run output.**
The user is running `Story (ENDLESS RESET)` overnight on their own machine and will bring the logs
in the morning. I was told to proceed autonomously on RESEARCH/DOCUMENTATION until then.

### Headline results from 2026-07-24/25 (all pushed)
* **BADGE 6 WON.** Fortree's rotating-gate puzzle is solved live — the decomp rule
  (`src/rotating_gate.c`) was ported into `modules/story/fortree_gates.py`, validated **4/4**
  against the live emulator at the tile a real run died on, and a full run reached Winona's
  challenge tile and beat her in 182k frames with **0 derails**. Story bot now reaches the
  **end of built content** (next unbuilt: Mt. Pyre, Magma hideout).
* **First run ever to survive its whole 3,000,000-frame budget** without hanging.
* ~19 fixes shipped, ~15 A/B-proven. Story-bot bundle PROMOTED to `custom-pokebot`
  (`6202a257`), verified there behaviourally, not just by import.
* `Story (ENDLESS RESET)` bot mode + a CLI batch runner (`tools/story-dev/endless_runs.py`).

### Research state — the important nuance
`PROJECT KNOWLEDGE/ai-research-notes/` holds ~57 Gemini notes. **Read
`ai-research-notes/00-READ-THIS-FIRST.md` before using ANY of it.** Findings that matter:
* Notes are LEADS. A Gemini pass may never be the final word on a fact code depends on.
* Only `CLAUDE-VALIDATED-*.md` files are grounded in the real decomp. **FIVE exist**
  (~175 claims total): `items-round1` (9 claims), `concepts-round1`
  (**51 claims: 30 confirmed, 15 refuted, 6 unresolved**), `concepts-round2`,
  `concepts-round3`, `story-round1`.
* ‼ **SUPERSEDED grounding method.** Round 1 used per-file API fetches
  (`gh api repos/pret/pokeemerald/contents/<path>`). **Use a local sparse clone of
  pokeemerald (~44 MB) instead** — it is the default now because it makes ABSENCE
  claims checkable (you can grep the whole tree for "this symbol does not exist"),
  which a per-file fetch fundamentally cannot do. The `gh api` route still works for
  a single known path, but do not start a validation round with it.
* **Stacking same-model passes does NOT converge on truth.** The adversarial critique invented a
  correction to a claim that was already right; the adjudicator then claimed ~100% confidence
  while describing recall as decomp verification.
* ‼ **~35 notes are tainted**: I overrode the relay's correct default with a two-generation-old
  model (see 08-MISTAKES 2026-07-25). Now impossible — `gemini_relay.py` refuses anything below
  Pro 3.1 in code. Story angles have been re-run as `story-notes-s*-v2.md`.

### The four highest-value validated facts (safe to build on)
1. **Mid-battle EXP survives a whiteout** → boss-training mode is VALID. But EXP goes only to mons
   ALIVE when the opponent faints, and the trainer ×1.5 is per-recipient after the split.
2. **A catch cannot be lost** with full party + full boxes (guarded before the ball is consumed).
   Real risk is an infinite bag→"BOX is full"→bag loop.
3. **The roamer sets NO flag** and is destroyed by every ODD battle outcome (incl. a mutual KO and
   teleport). `FLAG_DEFEATED_*` on statics means "encounter resolved", not "destroyed".
   **Whiteout is the safe abort for every scripted static.**
4. **`IsMonValidForMoveDeleter` does not exist** — the game guards only SURF
   (`IsLastMonThatKnowsSurf`). Fly/Dive/Waterfall/Strength/Rock Smash/Cut/Flash are UNGUARDED, so
   the bot must own HM coverage or it can strand a run permanently.

### Next steps, in priority order
1. **Cross-reference the user's overnight ENDLESS-RESET logs** against
   `tools/story-dev/batch3/*.log`. Where runs die tells us which research topic actually blocks
   progress — that beats more research.
2. `#24-movelearn-recovery` — the move-learn `BotModeError` is raised inside the battle handler,
   OUTSIDE StoryMode's derail-recovery scope, so a stall kills a run instead of costing one
   battle. **This killed 2 of 3 cold-start runs.** Gated on `#24-harness-savepath` (concurrent
   runs all overwrite one shared save path, so it still has no clean repro).
3. `#24-npcheal` — re-pair Route 111's training band to `ROUTE111_OLD_LADYS_REST_STOP` (PROVEN
   full ungated repeatable heal, 96 steps vs 213 to Fallarbor). Needs a heal-at-NPC helper;
   the existing path assumes a Poké Center layout.
4. KI-18 remains open/downgraded: both fixes are proven, but no live `.ss1` confirms the real
   cursor lands on the partner's slot.
5. `#24-whiteout` — attrition is the largest silent cost (58/85 whiteouts in single runs).

## MOST RECENT — 2026-07-24 (story bot: 3-starter validation batch)

**What just happened.** Ran three starter-locked fresh runs to hunt starter-specific
bugs (`profiles/starter-{treecko,torchic,mudkip}`, each `story.yml` pinning `starter:`).
All three are FINISHED. Headline: **no starter-specific logic bug exists** — every failure
was on shared navigation/attrition code, so the chapter code is starter-agnostic.

| starter | frames | maps | stopped at | party head |
|---|---|---|---|---|
| treecko | 2,195,761 | 38 | `get_devon_scope` → `_ride_out_scripted_scene` (Route 120, Ch13d) | Sceptile L39 + **Castform L25** |
| torchic | 1,650,182 | 27 | `ensure_facing_direction` @ Route 111 (18,99) | Combusken L29 |
| mudkip  | 2,113,515 | 34 | "too many whiteout recoveries" guard → Manual | Marshtomp L38 |

Treecko is the DEEPEST organic run to date — the Castform proves it cleared the Weather
Institute (Ch13b) and got as far as the Devon Scope errand. Logs live in
`tools/story-dev/starter-runs/{treecko,torchic,mudkip}.log`.

**Fixed this session:** `ensure_facing_direction` unbounded press loop (branch-local guards
could not fire — see 08-MISTAKES 2026-07-24). Now bounded at 1800 frames → `BotModeError`,
which StoryMode can recover from instead of hanging.

**Open from this batch (not yet fixed):**
- **Whiteout attrition is the top cost.** treecko 58, mudkip 85, torchic 11 whiteouts.
  Clusters: mudkip Petalburg ×24 / Slateport ×18; treecko Mauville ×16 / Slateport ×14 —
  i.e. the Norman and Wattson gyms plus the Slateport corridor. The "boss re-attempt IS the
  training" strategy is functioning but expensive; mudkip's run ended because it tripped the
  consecutive-whiteout bound. Needs a prep/attrition rethink, punch-list #24-whiteout.
- treecko's Route 120 `_ride_out_scripted_scene` wedge (Ch13d) — new, uncaptured.

**Docs:** `17-PORTABLE-ORCHESTRATION-GUIDE.md` added — the project-agnostic version of the
multi-agent structure, written to be lifted into any other Claude Code repo (16 stays the
Pokébot-specific one).

## Most recent work (2026-07-20)
- **PLANNING & RESILIENCE METHODOLOGY (doc 13) + out-of-balls safety floor (sandbox).**
  User directive: pause new story/feature code, plan the situations up front
  (provision-or-fall-back, never break, no cheats), retrofit existing scripts with
  preconditions/fallbacks, resume story ONLY when the user says so. Delivered:
  **`13-PLANNING-AND-RESILIENCE.md`** — goal-oriented task model (preconditions →
  provision/fallback → execute → verify → recover), Resource Ledger spec, an
  enumerated Contingency Catalog, the **Mart Atlas** (Oldale (2,4)/Petalburg (8,6)/
  Rustboro (11,7); badge-gated basic/expanded stock; Poké Ball 200), the Emerald
  money reality (no Vs Seeker → sell/Pickup/economy), a retrofit plan, and the future
  decision-brain seam. Referenced from 00-README. **First retrofit done: catching is
  now resource-aware** — `_should_catch` returns False when poke_balls ≤ 1 so it
  never attempts a catch it can't complete (fallback = skip). **BUY-AT-MART
  PROVISIONING now COMPLETE + verified**: `buy_poke_balls`/`provision_poke_balls`
  (early_game.py) drive the Emerald shop (talk from Rustboro-mart (3,3) facing Left;
  Poké Ball index 0; `wait_until_task_is_not_active(task,"A")` for list confirms;
  advance the "How many?"/"OK?" messages). Wired into catch_starter_team: out of
  balls → buy min(30, affordable) keeping a ¥500 reserve → resume; broke → skip.
  Verified end-to-end (balls forced to 2 → caught → bought 30 → resumed → team of 4).
  Commits: doc 13, `_should_catch` safety floor, `1a3df6ad` buy provisioning.
  **Retrofit largely complete** (catching/healing/training/nav/defeat/derail all
  have preconditions+fallbacks). Buy made SHOP-AGNOSTIC (`_mart_item_row` reads stock
  live → works at any mart). **DO NOT resume story chapters until the user says so.**
- **⭐ LATEST (2026-07-21) — "stuck at Oldale PC" investigation (sandbox).** User
  reported the bot getting stuck at the first Poké Center in Oldale "after respawn."
  Two DISTINCT bugs found:
  - **Bug 1 FIXED + verified — Segment 1 intro re-run.** `_play` Segment 1 was
    monolithic (gated only by RECEIVED_POKEDEX), so ANY pre-Pokédex recovery/resume
    (whiteout, derail, loaded save) re-ran the scripted intro FROM THE TRUCK →
    `go_upstairs` navigated to the house from Route 103/Oldale → impossible → derail
    loop, frozen in place. Reproduced from a pre-Pokédex Route 103 save. Fix: split
    Segment 1 — scripted intro (truck→lab) runs only while `_has_starter()` is False;
    train→rival→Pokédex is resumable + gated by DEFEATED_RIVAL_ROUTE103. Verified it
    now resumes at training. Also hardened the derail budget: `_progress_sig` is now a
    monotonic PARTY fingerprint (flags flicker during battle transitions and faked
    progress → infinite loops); recovery `wait_until_truly_controllable` (waits for a
    STABLE controllable overworld, presses nothing).
  - **Bug 2 OPEN — post-battle transition freeze (likely the ACTUAL "Oldale PC
    stuck").** During training, after a battle (flee / level-up / move-learn e.g.
    Mudkip Water Gun @L10) the return-to-overworld transition leaves the overworld
    non-controllable while the bot acts (navigate / walk to the Oldale nurse) → can
    hard-freeze (nurse heal dialogue never starts). Confirmed REAL (harness runs the
    identical `main_loop`), timing/starter-sensitive (default starter = "random";
    Treecko's overnight run got through, Mudkip reliably hits it). Offline repro is
    hampered by save-state reload artifacts. **USER DECISION: validate on the real PC
    first** (force Mudkip via `<profile>/story.yml` `starter: mudkip`, fresh game) and
    report back before a deeper fix. See 08-MISTAKES 2026-07-21 (3 entries).
  Committed to sandbox; battle_handler mis-fire change reverted (keyed on
  gDisplayedStringBattle which goes STALE after battle).
- **⭐ DEBUG LOGGER (2026-07-21, sandbox) — Bug 2 CONFIRMED on real PC.** Built an
  opt-in "Debug Logging (diagnostic file)" toggle in the Run (bot-mode) menu of BOTH
  GUIs (native `dashboard_gui.py` + classic `emulator_controls.py`), default OFF.
  `modules/debug_logger.py` writes an extensive structured log to
  `<profile>/debug-logs/<mode>-debug-<ts>.log` (gitignored): EVENT stream
  (story steps / battles+outcomes / map / party level-ups / mode changes / Story
  DERAIL+WHITEOUT) + auto STUCK DUMPS carrying the running GENERATOR CALL STACK
  (function+line, via gi_yieldfrom walk — pinpoints where the bot is waiting) plus
  held buttons / tasks / scripts / battle text; battles excluded from stall
  detection. Hooked once in `main_loop` (guarded); StoryMode logs derail/recovery
  events. Validated on the freeze scenario (self-healing ~1078-frame stalls →
  DERAIL #1..#5 → Manual).
- **⭐⭐ Bug 2 FIXED (2026-07-21) via the user's real-bot debug log.** The generator
  call stack pinpointed it (a TREECKO run — NOT Mudkip-specific): heal → derail →
  RE-heal loop. `heal_in_pokemon_center` returned while the overworld was transiently
  non-controllable, so `fight_route103_rival`'s next navigate choked → derail →
  recovery re-ran `_play` → re-healed → endless heal/leave-PC/re-enter-PC → Manual.
  FIX: heal waits for a STABLE controllable overworld after the exit warp
  (`higher_level_actions.py`, 34bfc47a). Downstream blocker also fixed:
  `StoryCatchStrategy` flees instead of Manual when out of balls (opportunistic
  pre-gym catching could burn the 5 starter balls on bad RNG; 3b069d47). VALIDATED
  in-harness end-to-end (route103 pre-Pokédex → **Rustboro → Route 116 catching**,
  team Mudkip L13 + Poochyena L4, **0 derails / 0 Manual**).
- **⭐ SWAP-TRAINING (2026-07-21) — fixes the training loop the user then saw.** With a
  very under-levelled catch (Lv2 Poochyena) the pre-gym `train_team` ground it against
  too-high Route 116 wilds → fight/faint/heal/repeat churn. NEW `SwapTrainBattleStrategy`
  switches a trainee that's ≥2 levels below the wild to the strongest team-mate turn 1
  (shares XP, no fainting/heal-churn); gated by `_SWAP_TRAIN` around `train_team`, which
  heals off the team's lowest HP. Validated (route116team save): Poochyena L4→L7,
  **0 heals / 0 faints**, flee rate 25%. Commit ef812c0e. User chose "BOTH": also landed
  area-training groundwork `modules/story/training_areas.py` (#24-trainmap, commit
  d405674d) — level-spectrum of early grass + `best_training_grass()`, to later route a
  low mon to a full-XP area (swap-train stays the fallback). **NEXT: user re-tests on
  the real PC — should now reach Rustboro/Roxanne with smoother training.**
  Documented strategy (planning doc §4/§4b): map shops/PCs AS REACHED, not all now;
  new punch-list #24-shops (incl. Lilycove multi-floor, E4 PC shop+mart) and #24-pc
  (PC/box team management). Remaining planning items future/noted (money-making
  engine, PP-aware heal, HM-gated routing, decision brain).
- **STORY TEAM-BUILDING: pre-fight training + retrain + pre-gym catching (sandbox,
  user directives #1/#2).** (a) `train_team(target, scope)` grinds wilds on Route 116
  (11,7) — scope 'whole' rotates the lowest battler to lead, 'lead' trains the lead.
  (b) `_prepare_for_fight(cfg)` before Gym 1: proactive target in the band (Roxanne
  13-17, random) + reactive escalation if lost here ≥2× (the +levels strategy AND
  team scope both randomized for organic feel). (c) `catch_starter_team(4)` +
  `on_battle_started` catch branch: catch NEW species (no dups, by dex #) until the
  party fills to 4. Verified: rustboro.ss1 → train Mudkip→Marshtomp L20 → beat Roxanne
  → Chapter 5a; and caught Abra/Whismur/Taillow (party 1→4). Committed b2fd5875
  (train/retrain) + c6433bf6 (catching). Tuning notes: Route 116 trainers over-train
  a bit; a full caught team is a slow grind (the 'lead' scope keeps some runs fast).
  **NEXT: Chapter 5b (return goods → Devon Corp 3F president → PokéNav → Rustboro rival).**
- **STORY DEFEAT/WHITEOUT RECOVERY built + verified (sandbox, user directive #1).**
  No more save-state reloads on defeat. (1) Watchdog neutered for Story
  (`_SELF_RECOVERING_MODES={"Story"}`, watchdog.py) — never reloads/rewinds. (2)
  StoryMode: `on_whiteout()`→abort+True (never Manual); `run()` wraps `_play` in a
  restart loop that steps out of the Poké Center (respawn lands ON warp (7,8) → walk
  above + step down), waits for a stable started+overworld state (post-warp flickers
  "not started", which had misfired the intro), and resumes; `on_battle_ended(Lost)`
  counts losses per location. Verified from rustboro.ss1 + injected Lv3 Poochyena:
  lost to Roxanne 7×, recovered every time, stayed in Story, no reloads. Committed
  `301fdea9`. **NEXT (in progress): retrain-on-2nd-loss (Route 116 grass, randomized
  scope/target per user), pre-fight level thresholds (~L17 for Roxanne), pre-gym
  catching (new species only), then Chapter 5b.** Repro harness gained `--inject-weak`.
- **STORY CHAPTER 5a BUILT + VERIFIED (sandbox only): recover the Devon Goods.**
  `recover_devon_goods()` (early_game.py) wired as StoryMode Segment 5a (gated by
  RECOVERED_DEVON_GOODS). After Gym 1: walk Rustboro → theft (DEVON_GOODS_STOLEN) →
  chase east onto Route 116 → across to the Rusturf Tunnel west door (47,8) →
  approach the grunt at (13,5) from the west and engage WITH A → grunt battle →
  goods recovered + Peeko freed. Verified via the real StoryMode.run() from
  gym1_done.ss1: RECOVERED_DEVON_GOODS=True at ~f31858, clean finish (Mudkip→Marshtomp
  evolved mid-chase, handled cleanly). Checkpoint `goods_recovered.ss1`. Key geometry
  fixes (mapdump): Devon Corp warps (11,15)/(12,15); Route 116 far tiles have no path
  (ledges — target the west edge, let the global navigator cross); the tunnel grunt
  BLOCKS the corridor (don't pathfind past it — engage with A, not B). **NOT promoted
  to custom** (sandbox-only, like legs 3-4 + Gym 1). **NEXT: Chapter 5b —
  `return_goods_get_pokenav()` (back to Devon Corp, president on 3F → PokéNav) + the
  Rustboro rival (211).** Full plan + verified coords in design §Ch5.
- **★ Lv16 MOVE-LEARN HANG — ROOT CAUSE FOUND & FIX VALIDATED (both builds, ML-13).**
  Overnight autonomous debugging session (user-authorised). REPRODUCED the exact hang
  with a faithful main.py-loop headless harness (`scratchpad/repro_movelearn.py`):
  inject a Treecko at `exp_for_L16-1`, walk into the Route 103 rival (single-Pokémon
  trainer, encounters avoided) so it crosses Lv16 on the KO that ENDS the battle.
  ROOT CAUSE: the Emerald BATTLE "Delete a move to make room for X?" Yes/No has NO
  backing task, so `get_learn_move_state()` could only detect it by a fragile
  script-offset (`+0x11`); when that never matched, the state stayed `Unknown` and the
  fallback pressed A only when `is_waiting_for_input()` (the FIELD printer, unreliable
  in battle) → it pressed NOTHING → froze on the Yes/No. FIX: rewrote
  `handle_move_replacement_dialogue` to be fully TEXT/TASK-driven (§DA) — Yes/No
  detected from on-screen text, move-select from the reliable input task, all other
  text advanced with A directly (no is_waiting_for_input gate); hardened
  `handle_evolution_scene`'s hand-off likewise. PROVEN by fault-injection A/B (force
  the state Unknown + is_waiting_for_input False = the user's env): OLD stalls ~10,600
  frames & fails to learn the move; FIXED resolves in 394 frames, learns Pursuit,
  evolves to Grovyle, sensible moveset — on BOTH builds. The earlier ML-12 dispatch
  reorder was a RED HERRING (A/B byte-identical) but is kept as harmless defence.
  Backup before the session: git tag `backup-pre-overnight-2026-07-20` (pushed) +
  local copy `C:/Remote Projects/_pokebot_backup_2026-07-20_overnight/`.
  Committed: `7af57428` (fix, both builds) + `71732daf` (design §DA doc).
  **END-TO-END from-scratch proof:** ran a FRESH Treecko game via the real Story
  mode (no injection); Treecko trained naturally to Lv16 in a real story battle and
  hit the EXACT fragile condition (`ml=Unknown, tasks=[]`, "trying to learn PURSUIT")
  — the fix RESOLVED it cleanly (learned Pursuit, mode=Story continued). This is the
  user's precise scenario working on a fresh save. (Separately, that run then
  WHITED OUT: a lone Lv16 Treecko can lose to Roxanne — the KNOWN #24-team weakness,
  NOT the move-learn bug; `do_rustboro_gym` assumes a stronger team. Flagged for
  #24-team/#24-defeat.) Recommend the user still do one real 32× confirmation.
- **MOVE-LEARN HANG — dispatch-order fix + live stall diagnostic (BOTH builds).**
  User: the Lv16 move-learn STILL froze on the "Delete a move?" prompt despite
  every prior fix passing my offline harness (the unexplained harness-vs-real
  gap). Found a concrete cause in `handle_battle`'s dispatch chain (ML-12): the
  action-selection check (`get_main_battle_callback() ==
  "HandleTurnActionSelectionState"`) ran BEFORE the move-learn check, so if that
  callback lingered while the post-battle move-learn prompt was up, the frame was
  swallowed by action-selection and the prompt was NEVER handled → the exact hang.
  FIX: move-learn + evolution-animating now dispatch FIRST, before action
  selection. Also added `_dump_battle_stall_diagnostic()`: when the in-battle
  no-progress watchdog fires (~100s), it now logs the EXACT on-screen battle/field
  text + script instruction + callback + move-learn state + active menu tasks to
  the console AND `<profile>/battle_stall.log` — so if it still hangs, the user's
  log pins the precise frame (closes the harness-vs-real gap with real data, §DA).
  The move-learn text-detection is already universal (matches generic phrases
  like "make room for", reads the offered move dynamically). Both builds compile.
  NOT yet user-verified on the real 32× run — **ask the user to re-test; if it
  still freezes, send `battle_stall.log`.** Design §DA; ML-12.
- **AUTONOMOUS RUN (2026-07-20): a fresh game now auto-plays through GYM 1
  (Stone Badge).** User granted full autonomy to build story chunks until a wall.
  Done this run: (a) documented the Story bot's PURPOSE — it's the deterministic
  REFERENCE/scaffold for the SEPARATE Pokémon Emerald AI project (design §P,
  01-VISION); (b) built the reusable recon tool `sandbox-pokebot/tools/mapdump.py`
  + a RECON PLAYBOOK (design §R); (c) PROMOTED Petalburg→Woods (legs 1-2) to
  custom (`8686a8d8`); (d) built + verified (all deterministic, ×2, via the
  listener harness with per-frame state refresh):
  **leg 3** `cross_petalburg_woods()` (Woods maze + Aqua/Devon scene → Route 104
  north), **leg 4** `travel_route104_north_to_rustboro()` (→ Rustboro), and
  **GYM 1** `do_rustboro_gym()` (heal → gym → beat Roxanne → BADGE01_GET). All
  wired into StoryMode. Checkpoints: route104_north / rustboro / gym1_done .ss1.
  **NOT yet promoted** (legs 3-4 + Gym 1 await user test→promote).
  NEXT: Chapter 4 (deliver Devon Goods → Rusturf Tunnel → Dewford / Gym 2).
- **FIX (2026-07-20, user-reported): Petalburg Woods STALL** — the real bot got
  "stuck" in the Woods (all my tests passed). Root cause ML-9: door entry
  hand-stepped onto the warp tile (flaky → BotModeError → main.py Manual mode =
  "stuck"), AND my harness masked it by reading player/map every frame. FIX: warp
  via `navigate_to(map, door_tile)` (`_pass_through_door`, like
  heal_in_pokemon_center). Re-verified with a MAIN.PY-FAITHFUL harness
  (scratch `faithful.py`): wally_done → Woods → Rustboro → Gym 1 → BADGE01_GET
  True, no error. Fixed in BOTH builds (sandbox + custom — leg 2 was promoted).
  **Test harness rule CORRECTED (design §16 / ML-9): match main.py — do NOT read
  player/map every frame (it hides timing bugs); catch BotModeError→manual.**
- **CHAPTER 5 (Devon errand) FULLY RECONNOITERED, not built** — mapped live from
  gym1_done: theft scene (StolenGoodsScene @ ~23,20 → DEVON_GOODS_STOLEN) needs a
  FLAG-ANCHORED ride-out (mid-scene controllable windows thrash the generic one);
  Devon employee (EmployeeAskToGetGoods @ 30,9); chase Rustboro E → Route 116 →
  Rusturf Tunnel WEST door Route116 (47,8)→tunnel(4,10) [navigate_to_anywhere
  picks the wrong (Verdanturf) warp — use _pass_through_door leg-by-leg]; grunt
  battle → RECOVERED_DEVON_GOODS + Peeko; return → Devon Corp (11,0) →
  RECEIVED_POKENAV. Rival battle (DEFEATED_RIVAL_RUSTBORO) trigger still to find.
  Full plan design §Ch5; checkpoint post_theft.ss1. NEXT: build recover_devon_goods()
  + return_goods_get_pokenav() using the flag-anchored ride-out + _pass_through_door.
- **RESUME-FROM-ANYWHERE v1 + Wally-detection fix (sandbox)** — user-reported a
  resumed save (in Petalburg Woods) mis-detected as "still needs Wally".
  StoryMode.run() rebuilt as a SEGMENTED flag-gated resume (fresh game runs all;
  resumed/hand-played save skips finished segments; Woods segment enters by
  current map). Fixed chapters.py Ch2 flag → HIDE_PETALBURG_CITY_WALLYS_MOM (the
  never-set THANKED_FOR_PLAYING_WITH_WALLY was the bug). Verified across
  checkpoints. Design §RS; refinements (per-step, fly/teleport, title-Continue,
  evolution) = punch-list #24-resume/#24-evo. Sandbox-only (needs legs 3-4+gym
  promoted first).
- **MOVE-LEARNING re-checked** — user reported "still has issues (Pursuit/Treecko)".
  The decision logic is verified correct (Mudkip + Treecko/Pursuit, never throws,
  declines status moves) and on the real path (_listeners→handle_battle→
  handle_move_replacement_dialogue); most likely their test predated the
  move-learning commit. NOTE evolution is OFF (stop_evolution default True) →
  #24-evo. Ask user to re-test with latest.
- **Smart MOVE-LEARNING implemented (both builds)** — user-reported the "learn a
  new move / delete an old one?" prompt. Added `LevelUpTravelBattleStrategy.
  which_move_should_be_replaced()`: never trades a damaging move for a status move
  (a Pokémon can't end up with only non-combat moves), preserves type coverage,
  skips no-gain moves; overrides the stock `new_move: cancel` decline-all.
  Unit-verified with real game objects (both status-slot and all-damaging kits).
  Remaining refinement (status-move utility ranking) folded into #24-team.
- **NEW punch-list items** (both user-requested, future): **#24-team** organic
  team-building / helper acquisition (design §TB), and **#24-ui** a Story-bot
  pre-run settings popup (name / starter / nickname). #24-ui is explicitly
  "after the bot is finished + tested 100%".
- OPEN: Torchic-vs-Roxanne needs the #24-team helper model (do_rustboro_gym
  assumes a favourable starter; verified with Mudkip).
- **Story travel Petalburg → Petalburg Woods BUILT + verified (sandbox, not
  promoted).** `travel_to_petalburg_woods()` (early_game.py) + new
  `LevelUpTravelBattleStrategy` (story_mode.py), wired into StoryMode. Chain:
  heal at Petalburg PC → cross WEST onto Route 104 riding out the one-time
  `PetalburgCity_EventScript_Scott` cutscene at (4,12) → fight the Route 104
  trainer (no-flee strategy) → enter the Woods south door (10-11,38) via
  discrete up-steps. Deterministic via the listener harness (fresh gym save →
  Woods, 6251 frames, ×2). KEY FIXES: single-mon party can't flee/rotate a
  trainer → crash (ML-8, fixed with heal + no-flee strategy); Scott script runs
  while state stays OVERWORLD (advance on `script.is_active`); navigate walks
  OVER door warps without triggering (step up into it discretely). Full map
  facts in design §16. Checkpoint `woods_entered.ss1` (in Woods at (17,38)).
  **NEXT: leg 3 — cross the Woods past the mandatory Aqua-grunt/researcher scene
  → north warp → Route 104 north → Rustboro (leg 4) → HM01 Cut → Gym 1.**
- **Dashboard GUI bug fixed (BOTH builds, committed `27189794`):** clicking
  "Hide" threw `_tkinter.TclError: wrong # args … raise tagOrId` from
  `_pokeball_button.lift()`. `_pokeball_button` is a **Canvas**, and Tkinter's
  Canvas aliases BOTH `.lift()` AND `.tkraise()` to `tag_raise` (raise a canvas
  ITEM, needs a tag). Fix = `tkinter.Misc.tkraise(self._pokeball_button)` (base
  widget-stacking raise). Non-fatal but noisy; fixed in sandbox+custom. The
  other `.lift()` calls in the file are on Toplevel/Frame (safe). See ML-6.
- **Petalburg→Rustboro travel — DIAGNOSED, NOT yet built.** Read the ROM
  connection graph: **Route 104 is one map ID split by the Petalburg Woods
  warp barrier**, so `navigate_to_anywhere` structurally CANNOT do
  Petalburg→Rustboro (it routes the connection graph, then fails the local path
  across the split Route 104). Must build LEG-BY-LEG through the Woods warps.
  Full verified geometry + 5-leg plan in design §16; root cause in ML-7. This
  is the immediate next build.
- **Story mode now runs a fresh game → through Professor Birch's lab** (sandbox,
  awaiting user test → promote). Full chain (verified with real battle
  listeners, ~17.5k frames): title → intro → house → clock → rival → Birch
  rescue on Route 101 → **random starter** → **first battle won** → **finish
  lab conversation** → hands to manual in the lab. `early_game.py` functions +
  StoryMode wiring. Config: `starter` (random/specific) live; `starter_nickname`
  GATED OFF (types but doesn't persist — TODO, user-deprioritised).
- **Sandbox audio off at startup** (sandbox `pokebot.py` forces `no_audio`;
  reliable regardless of launch; GUI-toggleable). Custom unaffected.
- **CHAPTER 1 COMPLETE through the rival battle (sandbox, awaiting user test →
  promote).** A fresh game now plays: intro → house → clock → rival intro →
  Birch rescue → starter → first battle → lab → **north to Route 103 (training
  en route) → grind to a random Lv 8-10 (healing at Oldale's Poké Center) →
  heal to full → beat the rival.** `travel_to_route103` + `train_lead_to_level`
  + `fight_route103_rival` in early_game.py, wired into StoryMode.
  on_battle_started returns `LevelUpLeadBattleStrategy` (fight-to-win).
  Key fixes: default strategy fled wilds (no XP); `find_closest_pokemon_center`
  is broken (hard-target `PokemonCenter.OldaleTown`); heal-to-full before the
  un-fleeable rival trainer battle. VERIFIED piecewise (fresh→lab 18.9k frames;
  route103→rival-beaten 31.1k frames). Earlier Chapter-1 parts (→lab) already
  in custom; the travel/train/rival is NOT yet promoted.
- **Pokédex sequence DONE + wired + committed** (`return_to_lab_and_get_pokedex`
  + `_navigate_through_scripts` helper): after the rival, back to Birch's lab
  (riding out the Oldale rival intercept), receive the Pokédex + Poké Balls.
  Verified (SYS_POKEDEX_GET True). StoryMode now ends cleanly at the Pokédex.
  NOT yet promoted (test then promote).
- **Pokédex sequence PROMOTED to custom** (user-tested "runs perfectly to the
  PokeDex").
- **Petalburg travel DONE + wired (sandbox)**: `travel_to_petalburg` reaches
  Petalburg — `_navigate_leg` to Oldale (past the Route 101 loop) then
  `navigate_to_anywhere(PETALBURG)`. Verified with listeners (22.1k frames).
  StoryMode now ends "reached Petalburg." NOT yet promoted (test then promote).
- **Petalburg travel PROMOTED to custom** (user-tested).
- **Chapter 2 DONE + wired (sandbox): Petalburg Gym (Dad/Norman) + Wally
  catching tutorial.** `do_petalburg_gym_and_wally_tutorial()`: enter gym → fire
  the Norman scene at (4,108) → ride out the fully-auto tutorial (Route 102
  Ralts catch + back). Completion = back in the gym + controllable after
  visiting Route 102 (NOT a flag). Verified via the listener harness. NOT yet
  promoted (test then promote).
- **CRITICAL TESTING LESSON:** test story steps ONLY via the listener-driven
  harness (build FrameInfo + call get_bot_listeners each frame, like main.py) —
  a bare `next(gen)+run_single_frame()` loop reads STALE state (no state-cache
  update) and gives WRONG results for scripted scenes. This cost hours.
- **DETECTOR BUG (low priority):** `chapters.py` Ch2 flag
  `THANKED_FOR_PLAYING_WITH_WALLY` is NOT set by the Wally tutorial — find the
  real flag (badge-anchored detection makes this low-impact).
- **Chapter 2 PROMOTED to custom** (user-tested "it worked").
- **NEXT SESSION — build Route 104 → Woods → Rustboro travel (leg-based).**
  Full verified geometry + 5-leg plan is in **design §16**; root cause of why
  `navigate_to_anywhere` fails is **ML-7**. Verified connection graph:
  Petalburg(30×30) West→Route104(offset-50); Route104(40×80) North→Rustboro,
  East→Petalburg, South→Route105; Petalburg Woods(24,11 / 48×44) has NO map
  connections (WARP-entered only); Rustboro(0,3 / 40×60) South→Route104.
  **Route 104 is warp-split by the Woods** — so travel MUST go leg-by-leg:
  (1) Petalburg west-edge exit → Route104 south [find the exact west-exit y at
  x=0; a script/wall triggers near (4,13)], (2) → Woods south warp, (3) cross
  Woods riding out the mandatory Aqua-grunt/researcher scene → north warp,
  (4) Route104 north → Rustboro south connection, (5) into Rustboro. Keep the
  battle listener attached through grass. Warps: `MapWarp` has
  `.local_coordinates` + `.destination_warp_id` (NOT `.destination_map`).
  GYM 1: Roxanne = Geodude Lv12/12 + Nosepass Lv15; starter is only Lv8-10 →
  TRAIN first; Torchic (Fire) weak vs Rock. Also need HM01 Cut. Checkpoints:
  petalburg.ss1, wally_done.ss1 (post-tutorial, in the gym at (8,1)/(4,108)).
- Iteration save-states in scratchpad: truck/house1f/house2f/clockset/
  outside_town/rival_*/birch_rescue/birch_free/first_battle/birch_lab/lab_done.

- **Story chunk B COMPLETE (sandbox, awaiting user test → promote):** a new game
  now auto-plays intro → into house → set clock → downstairs (rides Mom + the
  Petalburg-Gym TV scene) → outside → rival's house (auto mom greeting → upstairs
  → touch Poké Ball → meet the rival) → back outside. `early_game.py`
  (`walk_off_truck_and_into_house`, `go_upstairs_and_set_clock`,
  `descend_and_leave_players_house`, `visit_rivals_house`) wired into StoryMode.
  Full fresh-run verified (~11,800 frames → Littleroot (14,9), NICK/male). Map
  facts in design §14/§14.1/§14.2. Iteration uses scratchpad save-states
  (truck/house1f/house2f/clockset/outside_town/rival_* .ss1). **NEXT CHUNK:
  Route 101 → help Birch → choose starter → first battle.** Then a config pass
  (starter choice + nickname; character name already lives in `<profile>/
  story.yml`). Clock+earlier parts already promoted to custom; THIS chunk (the
  downstairs+rival additions) is sandbox-only pending the user's test.

- **PROMOTED Story Mode (chunks 1-2) to custom** after the user tested the
  intro live ("worked perfectly"). custom now has modules/story/, the StoryMode
  plugin, the title-screen selection fix (BotMode.is_selectable_from_title_
  screen + both pickers), and story tests. Verified in custom (compile, 12/12
  tests, intro smoke test → NICK/male in truck). DIVERGENCE-LOG (j) + docs
  updated. Sandbox == custom for all story files. **Next work (chunk B) starts
  in SANDBOX again** per the sandbox→promote workflow.
- **Story-mode chunk 2 BUILT: Chapter 0 New Game intro AUTOMATED.**
  `modules/story/intro.py` (`run_intro`) + `config.py` (story.yml name/gender)
  + `plugins/custom_modes/story_mode.py` (`StoryMode` bot). Drives title → New
  Game → Birch speech → gender → name → **controllable INSIDE the truck**.
  Verified on fresh throwaway profiles (boy/NICK, girl/MAY, config/ASH),
  deterministic ~4600 frames, real save untouched. Live facts → design §13.
  **NEXT CHUNK:** step off truck → room + set clock → Route 101 rescue →
  choose starter → first battle (design §6.3 step 4 / user's "chunk B").
  Intro TODO: the "existing save → Continue from title" path (intro currently
  assumes a save-less boot).
- **Story-mode chunk 1 (sandbox):** `modules/story/` read-only progress
  detector + 30-chapter registry + `tests/test_story_progress.py` (12/12).
  Badge-anchored (design §12 + ML-5). On the real save → **ch5, 1 badge**,
  flags the stray Magma Emblem anomaly.
- Story build is sandbox-only, NOT promoted. How to run: set bot mode to
  "Story" (fresh profile → intro; loaded save → detects chapter). Test harness
  pattern: `create_profile` + `LibmgbaEmulator` + drive the generator with
  `run_single_frame()` (see this session's scratch harnesses).
- Story-mode design Pass 4 → CONVERGED (see 12-STORYMODE-DESIGN §10).
- Fixed KI-8 (party strip 140→84px, no longer overlaps video) and KI-9
  (controller stuck in menu: `toggle_handheld` leaked `_gui_nav_active`; now
  cleared + gamepad uses a DERIVED gate `gamepad_gui_nav_engaged()`; added a
  "Controller GUI Control" master toggle — View menu + F10). Both PROMOTED to
  custom, live-verified on the real save (md5 identical). See 07-CHANGELOG.

## AWAITING THE USER (nothing blocked on me)
1. **PROMOTE** the sandbox batch → custom (with a promotion-time independent
   adversarial sweep; also fold in the OPEN VERIFICATION DEBT below).
2. **Ball size** — keep 140px (~2.7×) or make the left strip scrollable for a
   true 5×? (Note: #44 moved the ball to the hover, so the strip is clean now
   anyway — may be moot; confirm.)
3. **4 dex-tab decisions** (build #34/#35): (a) Pokémon dex artwork — source
   Sugimori art or reuse battle sprites? (b) item historical totals — track
   going forward/current-only/omit? (c) item map-location scope? (proceeding
   default: flavor/dims already done from ROM.)
4. **#41 honesty policy** — proceeding "show BOTH denominators" (386 National
   + 217 Emerald-obtainable) unless told to exclude. Two flagged
   uncertainties for the user: Latias-vs-Latios roamer/static (flips with the
   in-game TV answer), and Surskit (Emerald-alone unobtainable but
   record-mix swarm with a 2nd cart) — filed unobtainable; confirm.

## Next steps (in order)

**`#24` (the story auto-player) is the ONLY active work.** Everything else below is
parked and should not be started without the user asking for it.

0. **`#24-x4` live confirms** — the six checks listed under "YOU ARE HERE" above. Phase 1
   is built and unit-green but has never driven a real emulator; do these before relying
   on the batch for data, and before starting phase 2 (party-follows-focus + control
   toggle).
1. DAILY upstream check at session start (CLAUDE.md ritual; last 2026-07-19).
2. **`#24-movelearn-recovery`** — the move-learn `BotModeError` is raised inside the
   battle handler, OUTSIDE StoryMode's derail-recovery scope, so a stall kills the
   run. **Killed 2 of 5 cold-start runs** — the highest-value open item. Reproducible:
   per-run stall snapshots land in `tools/story-dev/saves/stalls/`.
3. **`#24-whiteout`** — whiteout attrition is the dominant cost of the current
   strategy (the run that SUCCEEDED still took 80 whiteouts).
4. **`#24-counters` phase 2** — the chain now NAMES a reachable counter (Electrike,
   Route 118); travelling to it, catching it and training it is not built (KI-23).
5. **`#24-regionreach` gate table** — `region_reach.KNOWN_GATES` has one hand-verified
   entry, and the training-gate switch is blocked on a repro mock leak (KI-24b).
6. `#24-npcheal`, `#24-edgecost`, `#24-trainmap` `PENDING_GRASS` tiles; KI-18 live
   confirmation.
7. Next unbuilt chapters: **Mt. Pyre**, then the **Magma hideout**.

**Parked (not active):** on user "promote", merge sandbox→custom + independent
adversarial sweep + live-launch check; `#41` living-dex obtainability wiring +
auto-evolve helper; dex tabs `#34`/`#35` (blocked on the 4 decisions above);
`#27` battery-aware, `#28` mobile remote, `#42-hard` HM-gated map reachability, `#45`.

## OPEN VERIFICATION DEBT
The big promotion's #8/#12/#18/#20 + the 2026-07-19 GUI polish went to custom
with builder self-verification; a partial independent sweep on custom fixed
4 bugs (`75e02cab`). The post-#f0b275f3 sandbox batch (above) is self/fact/
live-verified but wants an independent adversarial pass at promotion time.

## How to run / test

### The bot itself
```powershell
cd sandbox-pokebot         # ★ ACTIVE copy — build/test here (custom-pokebot = promoted only)
python pokebot.py                      # dashboard GUI (default)
python pokebot.py "Nick - Emerald"     # the user's real save (progressed)
python pokebot.py <profile> --classic-gui
python ..\install.py                   # setup/update/heal (custom)
python ..\install_sandbox.py           # same for sandbox
```
Story modes in the dropdown: `Story`, `Story (DEBUG)`, `Story (DEBUG - RESET)` (hard
reset → forced NEW GAME), `Story (ENDLESS RESET)` (chained reset runs in-process; set
the count from the GUI's "Endless Debug-Reset Runs…" item, 0 = forever).

### The story-bot test harness — `tools/story-dev/` (read its `README.md` first)
**Always `py -3.12` (the repo `python` is 3.9 and fails on match statements) and
`PYTHONUTF8=1`.** Full method: `PROJECT KNOWLEDGE/14-AGENT-PLAYBOOK.md`.

```powershell
# story_harness.py — the FAITHFUL main-loop harness (== the real bot's loop).
#   <state> = a .ss1 basename in tools/story-dev/saves/, a full path, or `fresh`.
$env:PYTHONUTF8=1
py -3.12 tools/story-dev/story_harness.py fresh --driver story --frames 2500000
py -3.12 tools/story-dev/story_harness.py norman_done.ss1 --driver story --build sandbox
py -3.12 tools/story-dev/story_harness.py fresh --driver storydebugreset --video
#   --video is REQUIRED to drive app UIs (PokéNav etc.) — they stall headless.

# endless_runs.py — the CLI batch runner (fresh profile per run, wall-clock +
#   log-growth stall failsafes; the GUI mode is the in-process equivalent).
py -3.12 tools/story-dev/endless_runs.py                 # 10 runs, treecko
py -3.12 tools/story-dev/endless_runs.py --count 0       # infinite (Ctrl-C)
py -3.12 tools/story-dev/endless_runs.py --count 25 --starter mudkip
py -3.12 tools/story-dev/endless_runs.py --starters all  # rotate all three

# compare_runs.py — cluster failures by signature ACROSS runs. This is the single
#   most productive debugging move in the project; a cluster of >=2 across different
#   machines/starters is the strongest evidence we act on. Reads both the harness
#   format and the in-game debug-logger format.
py -3.12 tools/story-dev/compare_runs.py tools/story-dev/night5/*.log
py -3.12 tools/story-dev/compare_runs.py --label mine tools/story-dev/night5/*.log `
                                         --label user ~/Downloads/Story_DEBUG*.log

# repro_*.py — the regression suite; run the relevant ones after any story change.
#
# repro_x4_*.py — ENDLESS LOOP x4 (#24-x4). Run all five after touching tile_bridge /
#   tile_mosaic / tile_child / endless_x4 / the dashboard's x4 methods. They need NO
#   emulator (mgba is stubbed into sys.modules where an import demands it), so they run
#   on any dev box:
#     repro_x4_bridge.py      cross-process shared-memory round trip, 4 slots, no crosstalk
#     repro_x4_mosaic.py      2x2 renderer at 4 sizes x every lane state -> x4-preview/*.png
#     repro_x4_tile_child.py  the publish path: rate gate, format conversion, must-not-raise
#     repro_x4_dashboard.py   dashboard wiring on a real Tk canvas: paint, no leak, clicks
#     repro_x4_lanes.py       lane profiles + story.yml starters + spawn/restart/teardown
#   ‼ repro_x4_lanes.py CANNOT exercise anything past `load_plugins()` on a box without
#   mgba, and says so per lane when it runs. It is not evidence that a lane emulates.
py -3.12 tools/story-dev/repro_fodder_grass.py     # prep/training decision table
py -3.12 tools/story-dev/repro_counter_plan.py     # counter-candidate ranking
py -3.12 tools/story-dev/repro_counter_wiring.py   # counter chain, all 3 outcomes
py -3.12 tools/story-dev/repro_region_reach.py     # region reachability oracle
py -3.12 tools/story-dev/repro_boss_plateau.py     # boss non-convergence detection
```

## Gotchas / unpushed work
- Tree clean, all pushed. NEVER edit `40cakes repo/pokebot-gen3/` (mirror).
- `profiles/` (incl. the user's real save) + `roms/` are gitignored — never
  commit them. The Emerald ROM IS tracked by user ruling (private repo).
- New `plugins/*.py` need `.gitignore` negations + `git ls-files` check (ML-2).
- Never `git commit` without a pathspec in automation (ML-3).
- Stock auto-updater is disabled for our root-`.git` layout (ML-4 fix).
- **Known issues: `05-KNOWN-ISSUES.md` holds 23 DISTINCT entries, not 6.** ‼ The IDs are
  NOT contiguous — **KI-12 and KI-13 do not exist in that file**, and KI-1 and KI-15 each
  appear under two headings (25 headings, 23 IDs; re-counted 2026-07-27).
  The ones that are LIVE and can cost a run:
  - **KI-17** — after-faint party-menu RESHOW freeze (HIGH; hit 2 of 5 fresh lanes).
  - **KI-18** — DOUBLE-battle replacement swap loops forever (HIGH; user-reported).
  - **KI-23** — Winona/boss-as-training-vehicle cannot converge without a TYPE
    answer; the counter chain diagnoses it but does not yet act (`#24-counters`
    phase 2).
  - **KI-24 / KI-24b** — `calculate_path` is unsound at region scale. **Partially
    fixed:** `region_reach` is wired into counter-candidate selection only;
    `_training_area_allowed` still uses `calculate_path`, so the false negatives
    are still live for training-area selection.
  Older low-severity ones still open: KI-1 (stale upstream `pokebot.spec`), KI-4/5
  (cloud-sync minor), KI-8 (mid-battle rotation party-menu stall). KI-6/7/11/14/15/16
  are fixed; KI-9/10 mitigated; KI-19 fixed-pending-wiring; KI-20/21/22 are
  decomp-verified fact dumps to read before building, not defects.
- **Mistakes: `08-MISTAKES.md` holds ~70 entries, not 7.** ML-1..ML-7 are the
  earliest (ML-6 = Canvas `.lift`/`.tkraise` both map to `tag_raise`; ML-7 = the
  global navigator can't cross a warp-split map like Route 104 through the Woods) —
  everything after them is story-bot era and is where the current traps live. Read
  the tail of the file, not just the head.

### Note added 2026-07-26 — badge case should be LIVE (#24-badges-live)
The Bag/badge-case overlay already follows the FOCUSED x4 lane, but only at the moment it
is opened: `open_badge_case()` snapshots the entries into `_badge_case_entries_cache`. So
clicking another tile while it is open does not switch it, and it does not update as badges
are earned mid-run. The user wants it to behave like the party strip, which IS live.
The snapshot exists for a reason — entries come from a disk read of `badge-log.json` and
`_show_badge_detail` fires on every hover — so the fix is to refresh on focus-change and on
the sidebar cadence, never per hover. Lanes already publish their badge set in the status
blob, which answers "has anything changed?" without touching the disk. See punch list.
