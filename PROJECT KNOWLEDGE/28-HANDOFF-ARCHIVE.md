# 28 — HANDOFF ARCHIVE (superseded "you are here" snapshots)

> **APPEND-ONLY history. NOT a current-state file.** Nothing here describes the present.
> For the present, read `04-HANDOFF.md`.

‼ **WHY THIS FILE EXISTS.** `04-HANDOFF.md` had grown to **3,240 lines of which only the first
~162 were current** — 95% archive — and it carried **SIX** "START HERE"/"YOU ARE HERE" banners,
the oldest stale by nearly two weeks. A reader looking for "where are we" found six answers and no
way to tell which was live. That violates `CLAUDE.md`'s own rule for files 01-05 (*"edit them in
place so they always describe present reality. Remove stale content."*) and it taxed every session.

‼ **NOTHING WAS DELETED.** These snapshots contain hard-won detail — measurements, dead ends,
retractions — and this project treats negative results as its most valuable asset. The split was
verified byte-identical to the original tail before it was written.

⛔ **ORDER: OLDEST FIRST — APPEND-ONLY. New snapshots go at the BOTTOM.** *(This line claimed
"Newest first" until 2026-08-15, when a Tier 1 audit measured it against reality: every move ever
made here was APPENDED, so the 2026-08-10 block sits at the top and the newest is at the end. The
claim was corrected rather than the file reordered — `28` is append-only history, and CLAUDE.md
forbids rewriting or reordering it. ‼ To find the latest snapshot, read the END of this file.)*
Each block is verbatim, exactly as it stood in `04-HANDOFF.md`.

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
| The Magma Hideout chapter completes | ‼ **NOT a rate — save-dependent (KI-50).** Reaches Maxie **3/3**. But the CURRENT `magma_door.ss1` **loses to Maxie DETERMINISTICALLY**: three runs, byte-identical telemetry (md5 `07f99a10ac8b`). The one win was on the save as it stood before `magmatravel` overwrote it at 22:05 on 08-10. **Do not retry — re-mint the save.** | `07-CHANGELOG` 2026-08-10 (night); re-run only via `--driver magmahideout` from `saves/magma_door.ss1` |
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
| Why the Magma Hideout loses | ✅ **Crobat CONFUSES the top attackers (they kill themselves) + Maxie HEALS Camerupt 22→67.** Neither is a bug — both are missing bot RESPONSES | `05-KNOWN-ISSUES` KI-50; the turn log now prints `[Confused]` |
| `#24-bosstelemetry` LEAD 2 ("selected but not executed") | ❌ **REFUTED for the Magma Hideout instance** — it was confusion; self-hits do not consume PP. ‼ The 2026-08-09 sightings were logged WITHOUT status and are NOT retro-explained | re-check them with the new status field |
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

## Archived 2026-08-12 — the KI-56 (Magma Hideout strand) block from the handoff

Resolved and driven on 2026-08-11; the full issue write-up now lives in
`31-KNOWN-ISSUES-ARCHIVE.md`. Moved out of `04-HANDOFF.md` so that file stays CURRENT
state. ‼ Its prevention rule was violated again by §Ch18 on 2026-08-12 — see
`08-MISTAKES.md` and playbook §7.

## ✅ KI-56 — WAS: stranded in the Magma Hideout. **FIXED AND DRIVEN 2026-08-11.**
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

### ✅ CAUSE CONFIRMED, FIX BUILT, DRIVEN **PASS** (2026-08-11, later)
`probe_hideout_warp_graph.py` re-tested the strand against the **whole eight-map warp graph**
(KI-56's own evidence was a *same-map* path failure, and `calculate_path` "is not able to use
warps", so a routing gap would have looked identical). It is not a routing gap: from the stranded
tile the search reaches **18 of 20 nodes**, missing only the exit warp `1F (10,34)` and
`JAGGED_PASS`. **Option 2 (return-route) is formally DEAD**; option 3 was already dead.

**THE FIX — the dungeon supplies its own escape, so there is no detour:**
| | |
|---|---|
| Escape Rope item ball | `MAGMA_HIDEOUT_3F_3R (9,19)` — a room §Ch15 already walks through |
| flag | `ITEM_MAGMA_HIDEOUT_3F_3R_ECAPE_ROPE` (1059), **unset** ‼ the decomp misspells "ESCAPE"; the correct spelling reads `False` silently forever |
| approach | **`(9,20)` only**, face Up. The other three sides are unreachable |
| reachable from | both 3F_3R warp nodes — including from the STRANDED tile |
| rope lands at | **`JAGGED_PASS (16,19)`**, collision 0 (`probe_escape_warp.py`, 3 controls) |
| bag today | **0 Escape Ropes** on every save ‼ and Lavaridge Mart does not stock them |

**BUILT AND PROVEN.** `collect_hideout_escape_rope()` + `use_escape_rope_to_leave_hideout()` +
`leave_magma_hideout()`, and the chapter now ENDS with the exit — **outside** the
`_groudon_awakened()` guard, so a resumed run still finishes it. Driver `--driver magmaexit`:
```
[mhexit] RESULT out=True map=JAGGED_PASS at=(16, 19) controllable=True landed_on_jagged_pass=True
[mhexit] VERDICT PASS
```
‼ `(16,19)` is the exact tile predicted from `escapeWarp` before any code was written.
Guarded by `repro_hideout_exit.py` (24 checks, fault-injected both ways). Gate: **15 of 15 green**.

‼ **The one thing that did not work first time**, because it will bite the next dungeon too: the
first run **consumed the rope and went nowhere**. `StartEscapeRopeFieldEffect()` runs from
`DisplayItemMessageOnField`'s **callback**, which fires only when the message is DISMISSED — the
wait loop has to press **B**, not just yield. *A consumed item is not the end of the script that
consumed it.*

**Not yet proven:** driven from `post_maxie.ss1` (on 4F). The exit has **not** been driven from a
run that walked all the way back down to `1F (25,34)`; the warp graph says 3F_3R is reachable from
there, but that is static.


# ARCHIVED 2026-08-13 from 04-HANDOFF.md (R3 line budget) — §Ch19 PRE-BUILD planning notes
> ‼ §Ch19 SHIPPED, was promoted and runs in the ladder. This was already labelled HISTORY in the
> handoff; it is moved here verbatim so the current-state file stays inside its budget.

## 📌 HISTORY — §Ch19 planning notes, written BEFORE it was built. ‼ §Ch19 IS DONE AND WIRED.
> Everything from here to the next `##` heading is the pre-build research. It is kept because the
> measured hazards in it are still true and still useful, but its status line is **obsolete** —
> §Ch19 shipped, was promoted, and runs in the ladder. Do not read this as a to-do.

Start from **`saves/post_mossdeep_gym.ss1`** (re-captured: now standing in `MOSSDEEP_CITY (38,10)`,
7 badges, ‼ **66% HP with one Pokémon fainted** — heal FIRST).
`modules/story/space_center.py` holds the route and the first three legs and says plainly that it is
groundwork. `probe_space_center_recon.py` is the measured area atlas.

**Hazards were PREDICTED by an adversarial pass and then TESTED before building — 3/3 held**
(`probe_ch19_hazards.py`, keep it green):
* **The city is cut in two.** The five Team Magma NPCs the gym victory spawns occupy the ONLY land
  bridge (x=44, y=23-26). A single route gym → Space Center cannot exist. **Route to the cutscene
  trigger line first** — `(42,21) (41,22) (41,23) (41,24) (40,25) (40,26)` — ride the forced scene,
  **observe `VAR_MOSSDEEP_CITY_STATE == 2`**, then plan leg 2.
* **The 2F prompt must be answered with A.** It is a `MSGBOX_YESNO`; B answers NO, which warps you
  back to 1F **with the var unchanged** — an infinite re-entry livelock, healthy avatar, no error.
* **Completion is `VAR_MOSSDEEP_SPACE_CENTER_STATE == 3`.** ‼ NOT `FLAG_DEFEATED_MAGMA_SPACE_CENTER`,
  which the Rayquaza PokéNav call **clears again** ~250 steps later — a chapter graded on it would
  pass, then silently un-pass.
* **Steven must be talked to TWICE**, and leaving 2F resets that (his first talk is dialogue only —
  a bot waiting for a battle there will hang). The second talk opens a **party-selection menu**
  (`ChooseHalfPartyForBattle`, 1-3 mons) that **nothing in this codebase has ever driven**; blind
  A-mashing volunteers slots 0-2, i.e. Zigzagoon L15, into a fight with Maxie L42-44. **This is the
  one genuine unknown — instrument it on the first run rather than guessing.**
* **The multi battle puts Steven's Metang/Skarmory/Aggron into `gPlayerParty[3..5]`**, and our
  faint-replacer picks by party index — it can try to send out the ALLY's Pokémon. Losing calls
  `SetCB2WhiteOut` directly.

⛔ **§Ch21 (Seafloor Cavern) IS BLOCKED — KI-63.** **No party member can learn Dive and the party is
full** (measured: 0 learners, 6/6). Receiving HM08 is fine (a script gift needs no learner), so
§Ch19/§Ch20 are unaffected — but **`#24-pc` is a PREREQUISITE of §Ch21**, not a later nicety. The
natural single swap is a **Wailmer or Tentacool** (both learn Surf *and* Dive; Zigzagoon L15 is our
only Surf carrier).

⚠ **KI-59 is armed in the Seafloor Cavern** — 115 `Impassable *` tiles across Rooms 1-9, which
`map_path` over-blocks. That is the reproduce-map KI-59 asked for: fix it with an A/B on
`SEAFLOOR_CAVERN_ROOM1` **before** the cavern chapter exists.

   ✅ **`sandbox-pokebot/modules/story/mossdeep_gym_puzzle.py` simulates the puzzle offline**, and
   `probe_gym_simulate.py` **PASSES**: 11/11 loaded objects predicted on a live press, identity-keyed
   on `local_id`, plus a period-4 identity control on all five colours. Per-press object counts
   (Yellow 8, Blue 4, Green 3, Purple 10, Red 5) independently reproduce the decomp's pad occupancy
   table. **A route may now be planned on this model.**

   Encoding (derived from the ROM dump, not assumed): arrows are `0x250..0x27F`; band =
   `(mt-0x250)//8` → `0 Yellow 1 Blue 2 Green 3 Purple 4 Red`; code = `(mt-0x250)%8` →
   `0 Right 1 Down 2 Left 3 Up`; ‼ **codes 4/5 are that colour's SWITCH**. Movement is a **rigid
   simultaneous rotation with NO occupancy check**, so four presses of a colour is the identity.

   ‼ **THE THINGS THAT WILL BITE — all newly measured, all in KI-58:**
   * **Nine TRAINERS stand on arrow pads and rotate with the statues.** A statue-only model is wrong.
   * **Statues are `graphics_id == 224`** (21 of them), *not* `trainer_type == "None"`.
   * **"5 counters mod 4" is UNSAFE** — not every pad holds three objects. Use the object-position
     tuple (what the module does).
   * **Solving the puzzle AIMS THE TRAINERS AT YOU.** Pressing yellow at `(3,30)` slides Maura to
     `(4,30)`, adjacent and facing the player; the trainer intro fires before the bot can step off.
     **Expect gym battles as part of the mechanic**, and never write a wait loop that assumes no
     script will start.
   * **Three** switches are unavoidable transit tiles: `(23,24)`, `(23,21)`, `(8,10)`.
   * `(21,6)` ejects to `(7,30)` and is **not flag-gated**; treat as blocked. Leaving the gym RESETS
     the puzzle; internal warps preserve it (`SKIP_OBJECT_EVENT_LOAD`).
   * **No configuration is unsolvable** — 114,929 reachable states, 0 dead. The bot cannot strand
     itself here, which is a change from every dungeon so far.

   **HOW TO BUILD IT:** A\* over `(player tile, object-position tuple)` using
   `mossdeep_gym_puzzle.press` / `is_walkable`, with warps and forced switch tiles as edges. The
   116-step agent route in KI-58 is a **cross-check on the solver's answer, never the answer**. Then
   Tate & Liza at `(23,8)/(24,8)` facing NORTH: a **DOUBLE battle** needing **≥2 usable Pokémon**,
   and the party still carries Zigzagoon L11 / Skitty L17.

2. ✅ **DONE — the Slateport-haul whiteout is FIXED** (`whiteouts=0`, PASS, and 5,457 frames
   faster). Cause: the anchor hands Ch16 a party at **8.8% HP with 5 of 6 fainted**, and the
   chapter was passing only *because* a whiteout heals. Fix: `SLATEPORT_ROUTE_HEALS`,
   nearest-first (Lavaridge → Mauville → Slateport). ‼ **Three other anchors are in the same
   state** — `post_mtpyre` 11%/3 fainted, `post_winona` 29%/3 fainted — so any NEW chapter built
   on one inherits the same latent whiteout. `probe_anchor_inventory.py` now prints the HP line
   and says so. **Heal early in Ch17.**

3. **Optional hardening of the §Ch15 exit:** drive it from a run that walks back down to
   `1F (25,34)` rather than from 4F. The warp graph says 3F_3R is reachable from there, but only
   statically. `sandbox-pokebot/profiles/ch16a/current_state.ss1` is a free repro of that state.

3. **`#24-teachmsgstall` is REOPENED** — the fix has no production effect (z = −1.28) and
   `already-advanced` never fired. Start from `post_select=exhausted`, which still occurs 8/85.

4. **The boss-response decision is the USER's.** The status tax is now a resolved rate
   (32.6% vs 3.8%, z = +62.2), which is the evidence a status response needed — but it is a
   battle-policy change touching every mode using `DefaultBattleStrategy`. **Do not build it
   unilaterally.** ‼ And roster hygiene is blocked (KI-54) until
   `POKEBOT_BOX_OVERFLOW_CATCH` — ⛔ **RETRACTED 2026-08-12: it is already ON and already works.**

5. **Remaining hardening (designed, not built):** H5 (make `n=` structural in every analysis probe)
   and H7 (a bounded-loop helper so an unbounded loop is a visible smell). See
   `26-REVIEW-AND-HARDENING-PLAN-2026-08-11.md`.

6. **Do NOT grade anything on the finish rate.** Eight batches, zero resolvable pairs. Use
   `30-METRICS.md` to pick an instrument before measuring.

## HOW TO RUN / TEST
```
cd tools/story-dev
PYTHONUTF8=1 py -3.12 preflight.py          # ‼ RUN THIS FIRST. git + fixtures + docs + freeze
PYTHONUTF8=1 py -3.12 lint_docs.py          # doc rules (exit 1)
PYTHONUTF8=1 py -3.12 verify_fixtures.py    # PINNED saves byte-identical
PYTHONUTF8=1 py -3.12 probe_status_tax.py <batch-dir>   # the status tax, with its control
PYTHONUTF8=1 py -3.12 x4_headless.py --lanes 8 --minutes 180   # a batch (3h)

# --- §Ch18/§Ch19 (all exit 0 today; keep them green) ---
PYTHONUTF8=1 py -3.12 repro_gym_whiteout_guard.py   # 5/5, fault-injected  (~1 min)
PYTHONUTF8=1 py -3.12 probe_chapter_order.py        # KI-61 regression guard
PYTHONUTF8=1 py -3.12 probe_ch19_hazards.py         # 3/3; H1 is now a stranding guard
PYTHONUTF8=1 py -3.12 probe_space_center_recon.py   # §Ch19 area atlas (measured, not recalled)
PYTHONUTF8=1 py -3.12 probe_gym_solve.py            # re-derive the 117-step gym route

# ‼ THE STANDING SUITE — RUN IT WITH ONE COMMAND. The list lives in CODE now, not in this prose,
#   because this comment advertised 15 gates for a whole session after a 16th was added:
PYTHONUTF8=1 py -3.12 run_gates.py            # all 17, exits non-zero on any failure (~124s)
PYTHONUTF8=1 py -3.12 run_gates.py --quick    # the 10 needing no ROM (~3s)
PYTHONUTF8=1 py -3.12 run_gates.py --list     # what is in the suite
# (reference only — run_gates.py's GATES table is authoritative) the 17, all exit 0 2026-08-13:
#   preflight, lint_docs, verify_fixtures, audit_flag_names, repro_undefined_names,
#   repro_no_silent_except, repro_roster_reorder, repro_multi_battle_partner,
#   repro_whiteout_abort, repro_gym_whiteout_guard, repro_hm_slot_wiring, probe_chapter_order,
#   probe_dive_learner, probe_slot_free_plan, probe_regi_capabilities, probe_dive_routing,
#   repro_impassable_dirs
#   ‼ repro_impassable_dirs (NEW 2026-08-13) is KI-59's A/B gate. It reads the REAL production
#     PathTile objects and compares them to the DECOMP, because the probe that re-implemented the
#     model (probe_shoal_tide.py) had copied the bug and so could never have failed.
#   ‼ repro_hm_slot_wiring (NEW 2026-08-13) asserts KI-63's chain is still CONNECTED end to end.
#     It exists because the previous failure was a chain of individually-correct parts with ONE
#     LINK MISSING, and no test, gate or green driver caught it — only a diff review did.
PYTHONUTF8=1 py -3.12 probe_chapter_order.py --build custom   # ‼ also check the OTHER fork

# ‼ VERIFY THE SANDBOX<->CUSTOM DRIFT ROW RATHER THAN TRUSTING IT (PowerShell, from the repo root):
#   Get-ChildItem "sandbox-pokebot\modules","sandbox-pokebot\plugins" -Recurse -Filter *.py |
#     ForEach-Object { $rel=$_.FullName.Substring((Resolve-Path "sandbox-pokebot").Path.Length+1)
#                      $c="custom-pokebot\$rel"
#                      if (Test-Path -LiteralPath $c) { git diff --no-index --quiet -- $c $_.FullName
#                                                       if ($LASTEXITCODE -ne 0) { "differs: $rel" } }
#                      else { "MISSING in custom: $rel" } }
#   ‼ EXPECTED as of 2026-08-13: exactly 3 — `modules/map_path.py` (KI-59's fix, NEW),
#   `modules/story/early_game.py` and
#   `plugins/custom_modes/story_mode.py` (KI-63's PRODUCTION WIRING, driven but NOT promoted).
#   ‼ NOT `roster.py`/`menuing.py` — those were PROMOTED 2026-08-13 and now show ZERO drift.
#   Anything else is unexplained drift.

# --- §Ch19 gates + drivers (all exit 0 / PASS today; keep them green) ---
PYTHONUTF8=1 py -3.12 repro_roster_reorder.py       # party-reorder PLANNER, 16/16
# ‼ THE PARTY-ORDER DRIVE (added 2026-08-13). ~4 min. Expect ACCEPTANCE: PASS.
#   phases=4/4 saw_j_nonzero=True idempotent=True restored=True can_continue=True
#   ‼ `saw_j_nonzero` is the one that matters — False means the run re-proved the OLD shape only.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver roster --frames 400000
# ‼ THE FIRST DRIVEN DIVE (added 2026-08-13). ~3 min. Expect ACCEPTANCE: PASS, legs=6/6.
#   Mossdeep -> ROUTE128 (38,27) -> dive -> cavern -> surface (10,17) -> and back OUT.
#   ‼ `got_out` is the one that matters: an underwater cavern is the best place yet to strand a run.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver ch20dive --frames 900000
PYTHONUTF8=1 py -3.12 probe_ch20_topology.py         # the measured route (read-only, 2 controls)
# ‼ KI-63 END TO END (the session's headline result). ~6 min. Expect ACCEPTANCE: PASS with
#   deposited_pids / gained_pids each exactly one PID. Drives the PRODUCTION wrapper.
PYTHONUTF8=1 py -3.12 story_harness.py post_dive.ss1 --driver divelearner --frames 3000000
PYTHONUTF8=1 py -3.12 probe_regi_capabilities.py    # what the Regi arc still needs (KI-69 Phase A)
PYTHONUTF8=1 py -3.12 probe_dive_routing.py         # why a chapter must drive dive() (KI-68)
PYTHONUTF8=1 py -3.12 repro_undefined_names.py      # ZERO undefined names in the story surface
PYTHONUTF8=1 py -3.12 audit_flag_names.py           # 19 files / 144 names; exits 1 on a phantom
PYTHONUTF8=1 py -3.12 probe_ch19_route.py           # why Mossdeep is cut in two (models live NPCs)
PYTHONUTF8=1 py -3.12 story_harness.py post_mossdeep_gym.ss1 --driver spacecenter1 --frames 900000
PYTHONUTF8=1 py -3.12 story_harness.py at_steven_2f.ss1      --driver spacecenter2 --frames 600000
PYTHONUTF8=1 py -3.12 story_harness.py post_mossdeep_gym.ss1 --driver spacecenter  --frames 1500000
PYTHONUTF8=1 py -3.12 story_harness.py post_space_center.ss1 --driver spacecenter  --frames 400000  # resume-safety

# --- drivers (these run under the REAL main loop, so they can fight) ---
PYTHONUTF8=1 py -3.12 story_harness.py post_aqua.ss1          --driver mossdeeptravel --frames 500000
PYTHONUTF8=1 py -3.12 story_harness.py in_mossdeep_gym.ss1    --driver mossdeepgym    --frames 400000
PYTHONUTF8=1 py -3.12 story_harness.py at_mossdeep_leaders.ss1 --driver mossdeepbadge --frames 300000
```
‼ **Never read an exit code through a pipe** — `| head` reports ITS status, not the script's. Write
to a file and echo `$?` (this nearly recorded a PASS that had never run).
‼ **A driver can fight; a hand-driven probe cannot.** Battle handling lives in the main loop's
listeners, not inside a bot mode's generator (`modules/battle_fault.py:5`).
**‼ THE AUTHORITATIVE GATE LIST IS `run_gates.py`'s `GATES` TABLE — not this prose.** All 17 exit 0. Do not
reconstruct it from the prose below; there are 94 `repro_*.py` files and the older text says "the
ten standing repro_*" without naming them, which is not reproducible. Current pass counts, measured:
`repro_gym_whiteout_guard.py` **5/5**, `repro_roster_reorder.py` **16/16**,
`repro_whiteout_abort.py` **13/13**, `repro_multi_battle_partner.py` **5/5**.

**Older text (2026-08-12, counts now stale):** plus `repro_gym_whiteout_guard.py` (4/4, fault-injected — ‼ it is a BOUNDED prefix test, because a hand-driven generator has no battle listeners and cannot win a gym fight; see 08-MISTAKES). Previously 14 of 14 (2026-08-11): the ten standing `repro_*` plus
`repro_teach_under_dialogue`, `repro_teach_prompt_window`, `repro_maxie_whiteout_guard`,
`repro_lead_cannot_battle`, and the `repro_no_silent_except` ratchet.
‼ `repro_counter_hunt` and `repro_area_item_gate` print `RESULT: ALL PASS` / `all checks pass.` —
grepping only for "ALL PASS" reports them as false failures.

## GOTCHAS (still true)
* **Never use the Grep TOOL on `tools/story-dev/x4-runs/`** — gitignored, ripgrep returns a silent
  zero. Use Bash `grep` and print the bytes searched as a control.
* **Event-var/flag names carry NO `VAR_`/`FLAG_` prefix**, and unknown names return `-1`/`False`
  **silently**. Membership-test first.
* **Report map identity as the `MapRSE` ENUM, never `map_name`** — that is a display label.
* **`.ss1` replays IDENTICALLY.** One fight repeated five times is still n = 1.
* **A save any driver re-captures is a CACHE, not a fixture** (`FIXTURES.md5` marks these VOLATILE).


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim, nothing deleted)
## ✅ AND THEN, LATER ON 2026-08-12 — §Ch18 BUILT, DRIVEN, FIXED AND WIRED (ladder 18 → 19 of 24)
10. **The Mossdeep Gym puzzle is SIMULATABLE and the model is VALIDATED.**
    `modules/story/mossdeep_gym_puzzle.py` predicts every object's tile after a switch press;
    `probe_gym_simulate.py` made the GAME grade it — **11/11 loaded objects, identity-keyed on
    `local_id`** — and caught a completely wrong model on its first run. Method written up as
    playbook **§4b**.
11. **The route is SOLVED and DRIVEN.** BFS over `(player tile × every object position)` →
    **117 steps**, matching two independent agent routes switch-for-switch.
    `--driver mossdeepgym` → `at_leaders=True at=(23,8) whiteouts=0`, one plan, zero re-plans.
12. **§Ch18 COMPLETE.** `--driver mossdeepbadge` → `badge=True controllable=True whiteouts=0`,
    `BADGE07_GET` after 754 frames. **Segment 18 wired into the ladder.**
13. **‼ TWO REAL DEFECTS FOUND BY ADVERSARIAL AGENTS, NOT BY MY TESTS** — both invisible to a
    passing run: the whiteout path checked the map only at entry AND raised an error type the
    recovery could not catch (fixed, proven by fault injection, `repro_gym_whiteout_guard.py` 4/4);
    and **§Ch18 stranded the run on an eleven-tile island** while passing `badge + controllable`
    (fixed; **the acceptance now requires being out of the gym**).
14. **KI-61 FIXED** — the chapter registry had the Space Center BEFORE the gym, which made the
    progress detector skip two whole beats. A/B proven; the design doc's "order confirmed" was wrong.
15. **§Ch19 groundwork + measured hazards** (`space_center.py`, `probe_space_center_recon.py`,
    `probe_ch19_hazards.py`). **NOT built, NOT wired** — and it says so.
16. **KI-62, KI-63 filed.** KI-63 is a real blocker: **no party member can learn Dive and the party
    is full**, so `#24-pc` is a PREREQUISITE of §Ch21.

## ✅✅ §Ch19 IS DONE (2026-08-12, later session) — the Space Center AND Dive, ladder 19 → 20 of 24

**Driven end to end from `post_mossdeep_gym.ss1`, zero whiteouts:**
```
[ch19c] RESULT dive=True hm08=True MOSSDEEP_SPACE_CENTER_STATE=3
        map=MOSSDEEP_CITY at=(19, 11) controllable=True whiteouts=0
[ch19c] CAN-CONTINUE OK(15wp to the Pokemon Center)
[ch19c] ACCEPTANCE: PASS
```
`modules/story/space_center.py` is the chapter; **Segment 19 is wired into `story_mode.py`**, graded
on `RECEIVED_HM_DIVE` (‼ NOT on the Space Center var — `chapters.py` grades chapter 19 on the Dive
flag, and the two are set in DIFFERENT BUILDINGS; a segment stopping at the battle would pass its own
guard while `current_chapter()` returned 19 for ever, and on the re-run the 2F Steven has been
`removeobject`'d so there would be nobody left to talk to).

**New anchors:** `at_steven_2f.ss1`, `post_space_center.ss1`, `post_dive.ss1`.
**New drivers:** `spacecenter1` (legs 1-3), `spacecenter2` (the menu + multi battle), `spacecenter`
(whole chapter — ‼ run it from `post_space_center.ss1` as well; skipping to leg 6 is what PROVES the
resume guards).

### ‼ THE FOUR THINGS WORTH KNOWING BEFORE TOUCHING THIS CHAPTER
1. **Mossdeep is CUT IN TWO until the forced cutscene runs.** The gym victory SPAWNS five Team Magma
   NPCs onto the only land bridge (x=44, y=23-26) and our planner blocks loaded-object tiles, so no
   route to the Space Center door exists yet. Leg 1 is therefore TWO legs: trigger line → **assert
   `VAR_MOSSDEEP_CITY_STATE == 2`** → then the door. ‼ I first blamed KI-59 (our planner
   over-blocking) because my flood fill modelled collision only and could not see NPCs — the planner
   was right. `probe_ch19_route.py` now models live objects so it cannot tell that lie twice.
2. **The stair grunt must be TALKED to.** `sight_radius = 0`, and it stands ON (13,2), the only tile
   the stairs are reachable from — so navigating there can never succeed, and waiting cannot help.
3. **‼ THE PARTY-SELECTION MENU IS SOLVED AND VERIFIED LIVE** (this was the chapter's one genuine
   unknown). Cursor slots 0-5 are mons, **6 = CONFIRM, 7 = CANCEL**; each pick is `A` (submenu) then
   `A` (ENTER), and **the cursor does NOT advance between picks**. A on an already-picked mon
   DESELECTS it, so blind A-mash toggles one slot for ever with a healthy screen and no error. Every
   pick is verified against **`gSelectedOrderFromParty`** (stored as `slot + 1`): measured `[1,5,3,0]`
   against `INTENDED-PICKS [0,4,2]` — an exact match. **Always bring three**: `Cmd_checkteamslost`
   sums HP over the PLAYER's picks only, so bringing fewer is strictly worse, not "letting the ally
   carry it".
4. **Losing is a RETRY, not an error.** The script inspects the outcome itself and calls
   `SetCB2WhiteOut` on anything but a win — money halved, warp to the last heal location — but the
   var stays at 2 and no trainer flag is set. ‼ Leg 1's heal matters twice over: the anchor's
   respawn was measured to be **LILYCOVE**, across the sea with no Fly user.

### ‼ AND IT NEARLY SHIPPED STRANDED — FOR THE THIRD TIME
The first full run finished `dive=True hm08=True controllable=True` and **FAILED**, because it ended
inside `MOSSDEEP_CITY_STEVENS_HOUSE (3,7)`. The Dive gift is an ON_FRAME script that fires on the
doorstep, so the beat ends where it begins with every completion signal already true. **The
acceptance caught it only because it asks for a real `calculate_path` off the end tile** rather than
asking whether the avatar is "controllable" — which it was, indoors, the whole time. §Ch15 ended four
floors underground, §Ch18 on an eleven-tile island, §Ch19 in a living room. *Keep that assertion in
every chapter's acceptance.* (Second bug inside the fix: both navigate-based door helpers free the
tile by stepping SOUTH, and (3,7) is the bottom row — an exit door needs `_walk_through_warp("Down")`.)



---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## ‼‼ THE BATCH RESULT — one thing resolved, one thing NOT
**RESOLVED — the status tax is real:** incapacitated turns lost **960/2,945 = 32.6%** vs a clean
control of **1,259/33,017 = 3.8%**. **8.5×, z = +62.2**, over 47,789 turns from 36 independent lane
logs. ‼ My earlier n=2 figure of 64.3% was **~2× too high** — one dungeon fight is not a rate.

**NOT RESOLVED — `#24-teachmsgstall` has no production effect and is REOPENED:**
teach success **38/47 (80.9%)** vs **38/42 (90.5%)** pre-fix, **z = −1.28**; `post_select=exhausted`
**8/85** vs **3/80**, **z = +1.46**; and the new `already-advanced` exit fired **ZERO** times in 85
teaches. The one-frame window was real but was **not the dominant production cause**. The fix stays
(it closes a real hole and costs nothing); **there is another path to `exhausted`.**

**NO EVIDENCE EITHER WAY:** KI-51 and KI-52 never fired in the batch (0 events). Still unmeasured.


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## 🛡 THE HARDENING ROUND — advisory rules → code that refuses
Driven by the finding that **≥12 of 164 logged mistakes are self-admitted REPEATS**, several
committed while the author knew the rule. **Run `preflight.py` before touching anything.**
| tool | what it does |
|---|---|
| `preflight.py` | one gate: git sync + fixtures + docs + live-batch detection. **Exits 1.** |
| `lint_docs.py` | CLAUDE.md's doc rules enforced (R1-R6). Cut `04-HANDOFF` from 3,240 → 167 lines |
| `verify_fixtures.py` (+`--assert name=md5`) | PINNED saves byte-identical; put the assert **in** the measurement command |
| `repro_no_silent_except.py` | RATCHET at **140/203** silent handlers — may never rise |
| `29-DISABLED-FEATURES-REGISTRY.md` + lint R6 | every `POKEBOT_*` flag with its MEASUREMENT. **Check before proposing a feature** |
| `30-METRICS.md` | which instrument answers which question, at what n |
| `27-INJECTION-SURFACE.md` | how the bot observes/acts + the 8 timing traps (for goal #2) |
| `25-BACKUPS-AND-RESTORE.md` | restore points: naming, what a tag does/doesn't capture, recipes |
| `26-REVIEW-AND-HARDENING-PLAN-…md` | the full review: taxonomy, doc health, future path |

‼ **Three of these found real problems on their first run**: six competing START-HERE banners, an
**11th undocumented flag** (which turned out to be the roster blocker), and 140 silent handlers.


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## ‼‼ THE ADVERSARIAL REVIEW OF THE FINISHED CHAPTER FOUND MY OWN FIX WAS WRONG TWICE
Run AFTER §Ch19 was committed and reported proven — which is exactly why it is worth doing.
* **KI-64's fix was DEAD CODE on the story path.** The MRO is `StoryItemBattleStrategy` →
  `LevelUpTravelBattleStrategy` → **`LevelUpLeadBattleStrategy`** → `DefaultBattleStrategy`, and
  `level_up.py:41` has its own `choose_new_lead_after_faint`. I had guarded the base class.
* **‼ And the `index >= 3` cut was in the WRONG INDEX SPACE.** Opening the battle party menu runs
  `UpdatePartyToBattleOrder`, which PHYSICALLY PERMUTES `gPlayerParty` — visible in my own passing
  log (`ch19d.log` f37745): index 1 becomes the ALLY's Metang and OUR Swellow moves to index 3. The
  cut **offered the ally and hid one of ours**, precisely when a replacement is needed.
* **My fault-injected A/B passed it anyway**, because the fixture modelled only the un-permuted
  order and asserted the base class directly. A control arm does not save you if all three arms
  measure the wrong thing.
* **Now fixed properly**: `ally_party_indices()` keyed on **ORIGINAL TRAINER ID** (identity travels
  with the Pokémon; position does not), wired at all three call sites. Repro is **5/5** with the
  permuted-array and story-class arms added; §Ch19 re-driven to a PASS afterwards.
⇒ **Two new prevention rules in `08-MISTAKES.md`:** print the MRO before "fixing" a strategy method,
and never identify a Pokémon by party index across a battle-menu boundary.


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## 🛠 TWO GATES WERE BLIND, AND FIXING THEM FOUND A REAL BUG
* **`audit_flag_names.py` was checking TWO files** — written before the chapters moved into
  `modules/story/*.py` — and, worse, could only see names written as literals AT the call site, while
  the house idiom is a module constant. So it was blindest exactly at the **completion markers**.
  Now globs 19 files, resolves `CONST = "LITERAL"`, prints per-file counts, and **exits 1** on a
  phantom (it used to print findings and exit 0). Coverage 2 files/117 names → 19/144. A/B proven by
  fault injection.
* **`pyflakes` was installed and had never been run.** New gate `repro_undefined_names.py`
  (ZERO tolerance over `modules/story` + `plugins/custom_modes`). It found my own missing import
  *after* a five-minute drive had already paid to reach it — **and KI-65**, below.


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## ‼ THE TWO THINGS THAT MATTER MOST FROM THIS SESSION

**1. When N of your own instruments agree on something impossible, they share a missing primitive.**
Four instruments agreed the Mossdeep Gym had no route to its own leaders. All four modelled it as
*walk + warp*; the gym has a **third movement primitive** — floor switches that relocate 21 statues
and nine trainers. Even the model-free brute-force walker was wrong, because it *changed the map
while exploring it*. Five parallel Claude agents found it; the explicitly ADVERSARIAL one cracked it.

**2. ‼ EVERY DEFECT THAT MATTERED THIS SESSION WAS FOUND BY AN ADVERSARIAL AGENT, NOT BY A TEST.**
Three times: the statue model (caught by a validation gate I only built because the rule says to),
the whiteout path, and §Ch18 stranding the run. In each case my own runs were **green** — the
happy path cannot exercise an error path, and an acceptance test written by the same person who
wrote the code inherits the same blind spot. ⇒ *Spend the agents on REFUTING finished work, not
only on researching new work.* And: **write the predicted failure down BEFORE the run** — the
§Ch19 hazard checks did this and 3/3 held, which is how two traps got designed out instead of
debugged.


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## ‼ WHAT THE USER DECIDED THIS SESSION
* **Promotions approved twice** (teach fix; then KI-51 + KI-52 + status telemetry).
* **"Roster hygiene before bosses"** approved as the boss-response direction — then found
  **BLOCKED** (KI-54): the box is empty, and the deposit path was already measured harmful.
  ⛔ **RETRACTED 2026-08-12:** the line below said the unlock was `POKEBOT_BOX_OVERFLOW_CATCH`,
  "one unhandled text box away". **Both halves are false.** That flag has defaulted to **ON** since
  2026-08-07 (`story_mode.py:2241-2243`, verified in the live code), and the text-box blocker was
  refuted the same day (`exit_frames=120`, zero forced presses). Four docs repeated it because they
  were written from a **stale code comment** instead of the default twenty lines below it. See
  KI-54's retraction block.
* **The boss-response design is still the user's call.** The status tax now has a resolved rate
  behind it, but a status response is a battle-policy change touching every mode — **do not build
  it unilaterally.**


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## 🆕 THE REGI ARC — researched and measured 2026-08-12 (user-requested). See **KI-69**.

**‼ THE PARTY ORDER EVERYONE REMEMBERS IS THE RUBY/SAPPHIRE ONE.** Emerald reversed it:
**WAILORD first (slot 0), RELICANTH last** (`braille_puzzles.c:92-104`, comment and all). The wrong
order **fails silently** — no message, no error. Emerald also swapped **Regirock to ROCK SMASH**
(was Strength) and **Registeel to FLASH** (was Fly). Pinned in `repro_roster_reorder.py`.

**⛔ THE REGI BATTLE IS UNRECOVERABLE — read this before writing any battle policy.** Level 40,
catch rate 3. `B_OUTCOME_WON` removes it forever, and the fall-through case **including
`B_OUTCOME_LOST`** sets `FLAG_DEFEATED_*`. ⇒ **KO'ing it OR whiting out deletes the encounter
permanently.** The only safe non-catch exit is fleeing.

**✅ NEW CAPABILITY: `modules/story/roster.py`** — `plan_reorder` / `plan_last_slot` (PURE, proven
exhaustively: 720 permutations replayed, `repro_roster_reorder.py` 15/15) and `reorder_party()`
which drives `RotatePokemon` inside the `_rotate_lead_safely` harness.
⛔ **STALE TEXT CORRECTED 2026-08-13 — the line below said "the DRIVER is UNPROVEN" and that has been
FALSE since earlier the same day.** `--driver roster` ran **six swaps, all verified by PID**,
including `RotatePokemon(i, j != 0)`, giving `phases=4/4 saw_j_nonzero=True idempotent=True
restored=True can_continue=True ACCEPTANCE: PASS`. It contradicted this file's own 60-second summary
and `03-PUNCH-LIST.md`, in the exact section a Regi-scoping reader opens first.
‼ **What IS still true:** `reorder_party()` has **ZERO production callers** — it is a proven
capability, not yet content — and **KI-71** (the Manual-drop guard is unreachable) is still open.
Superseded text: ‼ **The DRIVER is UNPROVEN** — `RotatePokemon(i, j)` with `j != 0` has never been driven here, and it sits on the unfixed side of KI-38 (four unbounded loops + a `set_manual_mode()` trapdoor). **Drive it before anything depends on party order.**

**MEASURED capability status** (`probe_regi_capabilities.py`): ✅ Go-Goggles, HM08 in bag, Surf
(Zigzagoon), Rock Smash (Sceptile). ⛔ **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or
Flash. So the arc needs an acquisition phase first — Super Rod (Route 118), TM28 (Route 114), and
teaching Dive/Dig/Flash. ‼ **Relicanth is underwater-only, so Dive is upstream of everything.**


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## ‼ FOUR NEW ISSUES FILED
* **KI-64 (FIXED)** — the multi-battle faint replacer would have sent out **STEVEN's** Pokémon.
  `FillPartnerParty` writes his Metang/Skarmory/Aggron into `gPlayerParty[3..5]`; both choosers
  excluded only the on-field mons and rank by condition, so three fresh L42-44 mons win outright.
  ‼ The guard needed already existed with **zero callers**: `is_double_battle_with_partner`.
* **KI-65 (OPEN, unfixed — ‼ and I CORRECTED MY OWN OVERSTATEMENT of it)** —
  `battle_move_replacing.py:280` uses `party_index`, which is assigned lower down. I first wrote
  that the HM-refusal re-pick "may never have executed"; **that was too strong.** Tracing the flow:
  the name is bound in the `AskWhetherToLearn` branch, which normally runs first, so on an ordinary
  teach the re-pick works. The real bug is narrower — line 371 is inside a `try:` whose `except`
  silently defaults, and on THAT path the name is never bound, so a later `CantForgetHM` raises
  `UnboundLocalError` into a SECOND silent `except` that declines. **Two invisible failures that
  compound.** Still worth fixing, still needs its own repro first.
* **KI-66 (OPEN)** — the multi-battle hazard is BROADER than the faint chooser: **four more**
  full-party scans on the same paths (two in `battle_handler.py`, `alive_slots`, and the rotation
  targets feeding an **unbounded** `while PARTY_MENU: press A`). The right fix is ONE choke point —
  `ally_party_indices()` now exists — not a guard per call site. ⚠ Also unverified and worth checking
  FIRST, because it would fire on turn 1 rather than on a faint: a claimed `IndexError` in
  `decide_turn_in_double_battle` from `gPlayerPartyCount` still being 3.
* **✅ KI-67 (CLOSED 2026-08-12)** — both halves. The chapter retry loops no longer swallow the
  abort (`StoryAbort` + the latch-keyed `reraise_if_aborting`, because a type-only guard cannot see
  an abort an inner loop already replaced with a fresh error), AND the harness now mirrors
  production via `StoryWhiteoutRecoveryMixin`. **First driven whiteout recovery in this project:**
  `--driver spacecenter2 --inject-weak` gave `whiteouts=3 recoveries=3`, ending controllable at
  `MOSSDEEP_CITY (28,17)`. ‼ **The proof is the FRAME DELTA, not the count** — +7,789 and +7,087
  between whiteouts, i.e. each attempt really walked back to Steven and fought again. Broken code
  would have burned three attempts in a handful of frames after ONE whiteout.
  ‼ Five defects in the mixin were caught by an adversarial review **before** it was driven
  (`PathFindingError` is a `RuntimeError` and escaped the recovery; MRO silent-revert; a `tag`
  dereference on the listener's stack; a class-counter budget; a `None`-is-success exit), plus a
  real blocker: an injected run could have silently overwritten a committed anchor.


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## ‼‼ THE BATCH RESULT (status tax + `#24-teachmsgstall`) — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-13)

An older 36-lane measurement, moved out for the R3 budget. ‼ **Keep this:** the **status tax is REAL — 32.6% of turns incapacitated vs a 3.8% control, 8.5x, z = +62.2 over 47,789 turns** (an earlier n=2 figure of 64.3% was ~2x too high). **`#24-teachmsgstall` is REOPENED**: the fix closed a real hole but had **no measurable production effect** (z = −1.28; its new exit fired **ZERO** times in 85 teaches) ⇒ **another path to `exhausted` exists.** KI-51/KI-52 never fired — still unmeasured.


---

# ARCHIVED 2026-08-13 from `04-HANDOFF.md` (R3 budget; verbatim)

## ✅ WHAT SHIPPED IN THE **§Ch19 + PROMOTION + ROSTER** SESSION (2026-08-12) — HISTORY, not latest
> ‼ This heading used to say "THE LATEST SESSION". It is not the latest — the §Ch20 cavern work
> above it is. Renamed 2026-08-13 because a stale "latest" is exactly the kind of banner that sends
> a cold-start agent to the wrong place; this file has been cleaned of competing START-HERE banners
> once already.
1. **§Ch19 built and driven end-to-end** — Space Center multi battle **and** HM08 Dive, wired as
   Segment 19. Ladder **19 → 20 of 24**. Acceptance includes "and the bot can continue".
2. **§Ch18 + §Ch19 PROMOTED** to `custom-pokebot/`, verified by driving `--build custom` three ways.
3. **KI-64 fixed** (the multi-battle faint replacer would have sent out STEVEN's Pokémon) — ‼ and my
   first fix was **wrong twice**: dead code on the story path, and a positional cut that inverted
   itself once the party menu permutes `gPlayerParty`. Now keyed on **original trainer ID**.
4. **KI-67 CLOSED, both halves** — the whiteout abort no longer burns a chapter's retry budget or
   launders itself into a fabricated diagnosis, and the harness finally mirrors production.
   **First driven whiteout recovery in this project** (frame deltas +7,789 / +7,087).
5. **Two blind gates fixed:** the flag audit was checking **2 files** and could not see names behind
   a module constant (i.e. blindest at the completion markers); and **pyflakes had never been run** —
   it found a `NameError` on the Magma Hideout's *success* path.
6. **New: `modules/story/roster.py`** (party reorder) + the `PartyMenuExit` freeze fix.
7. **Regi arc researched and Phase A measured** (KI-69) at the user's request.

### 📌 THE OLDER SESSION'S SUMMARY (§Ch16-§Ch18) FOLLOWS BELOW — it is HISTORY, not current state.
The story ladder went **16 → 19 of 24 beats**.

‼ **§Ch18 (items 5, 6 and the block below) is COMMITTED AND PUSHED BUT *NOT* PROMOTED to
`custom-pokebot/`.** Items 1-4 below were promoted on 2026-08-12 with the user's approval, verified
by driving `--build custom` to a frame-identical PASS. **§Ch18 has had no such approval and no such
verification — the sandbox↔custom drift row above is stale the moment you read it.** Promotion is
the user's call, and it needs its own driven check in `custom-pokebot`, not a diff.

1. **KI-56 FIXED — §Ch15 now LEAVES the Magma Hideout.** It used to pass its own binary test on
   runs that ended permanently stranded. No walk-out exists (18 of 20 warp-graph nodes reachable,
   the exit not among them); fixed with the **Escape Rope the dungeon itself provides**. Driven
   PASS, landing on the exact tile predicted from `escapeWarp` beforehand.
2. **KI-57 FIXED — §Ch16 (Slateport) COMPLETE.** ‼ Beating Maxie *parks Capt. Stern on the only
   tile touching the harbor door*: Ch15's own success spawns Ch16's blocker. The answer was not a
   route but a conversation — talking to him `warp`s the player inside. Driven PASS x3.
3. **§Ch17 (Lilycove Aqua Hideout) BUILT + the MASTER BALL.** An 18-hop warp-panel maze solved from
   the ROM warp table. ‼ The Master Ball can't be taken directly — both free neighbours are
   unreachable — so the route takes the **Nugget** first and steps onto the tile it vacates. Driven
   PASS with `master_balls=1`.
4. **The Ch16 haul whiteout FIXED** (`whiteouts` 1 → 0, and faster). The anchor hands the chapter a
   party at **8.8% HP, 5 of 6 fainted**, and the chapter was passing only *because a whiteout
   heals*. Heal stops are now nearest-first.
5. **§Ch18 leg 1** — `--driver mossdeeptravel` Surfs Lilycove → Mossdeep and enters the gym
   (PASS, `whiteouts=0`), capturing `saves/in_mossdeep_gym.ss1`.
6. **KI-58 RESOLVED — the Mossdeep Gym is a ROTATING-TILE STATUE PUZZLE**, not a maze (see below).
7. **KI-59 + KI-60 filed** — two latent bugs in the SHARED pathfinder, code-verified, deliberately
   **not** fixed. `#24-impassabledirs`, `#24-pathsourcecheck`.
8. **`#24-grounditems` groundwork** — `collect_item_ball()` is now shared by three callers;
   `#24-npcgifts` and `#24-masterball` added on your direction.
9. **New tools:** `probe_warp_maze.py` (generalised, self-checks against a DRIVEN route),
   `probe_gym_bruteforce.py` (model-free walker), `probe_gym_components.py`, `probe_escape_warp.py`,
   `probe_hideout_warp_graph.py`, `probe_slateport_harbor_map.py`, `repro_hideout_exit.py`.
   `probe_anchor_inventory.py` now prints **party HP** — it immediately flagged three anchors as
   "cannot survive a journey".

---

# MOVED 2026-08-14 (from 04-HANDOFF.md, for the R3 budget when the Room 8 banner landed) — the two §Ch20 Room 1 / Room 2 blocks of 2026-08-13, verbatim:

## 🚩 THE BOT IS INSIDE THE SEAFLOOR CAVERN AND THROUGH ROOM 1 — driven, first attempt

**`--driver ch20room1` → `ACCEPTANCE: PASS`.** Mossdeep → dive → `SEAFLOOR_CAVERN_ENTRANCE (10,17)`
→ `ROOM1 (5,18)` → Rock Smash + two Strength pushes → **`ROOM2 (10,7)`, controllable, real step
taken.** Two trainer battles fired on the way and were ridden out.

**‼ THE RESULT IS THE A/B, NOT THE ARRIVAL.** Same call, same target, live objects on both arms:

    A/B BEFORE  (5,18) -> (11,11)   PathFindingError      <- the corridor really IS sealed
    A/B AFTER   (5,11) -> (11,11)   OK len=6              <- and the smash+push really opens it

That converts `probe_ch20_interior.py`''s Room 1 NO-PATH from a **LOWER BOUND** (it was measured from
Mossdeep, with no cavern objects loaded) into a **measured fact**. A one-armed "it worked" could not
have ruled out "the corridor was open all along".

**‼ THE ROUTE HAD TO BE ARBITRATED BEFORE IT COULD BE DRIVEN — OUR OWN BUILD SPEC WAS WRONG.**
`ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md` claims an **exhaustive** search
proves Room 1''s `(5,11)` boulder must be pushed **NORTH**. The decomp *and* our own ROM reader both
say `(5,10)` and `(5,12)` are `collision=0 elevation=3 ''Cave''` ⇒ **either direction is legal, the
uniqueness claim is false, the search was not exhaustive.** Upstream''s **SOUTH** push
(`puzzle_solver.py:373`) is what ships, and it was then confirmed live.
⇒ ‼ **THAT SPEC''S ROOM 2 AND ROOM 8 "EXHAUSTIVE" SEQUENCES ARE NOW UNAUDITED.** Arbitrate each
against the decomp **and** upstream''s Emerald branch (`puzzle_solver.py:395-454`) before driving it.
**Standing rule from `06-DECISIONS-LOG.md`: copy upstream''s ROUTE, never upstream''s CONTROL FLOW** —
its second push is a bare `walk_one_tile`, unbounded by its own docstring and judging nothing; ours
go through `strength_push`, which is bounded and verifies the boulder **by `local_id`**.

**‼ NEW ISSUE — KI-77, and it was found by the ONE prediction that FAILED.** On arrival the live
object dump returned **2 of the map''s 5** objects; the rock and both grunts were absent yet
demonstrably present. **`get_map_objects()` is a CAMERA-RANGE WINDOW, not a map inventory** — and
`map_path.py:811-818/844-853/861` builds the planner''s whole object model from it. ⇒ **after a push,
walking out of range re-blocks the tile the boulder LEFT and frees the tile it now OCCUPIES.**
Benign in Room 1 (the route never revisits `(5,11)`), **armed in Room 8''s nine pushes in 48 tiles.**
Code-verified, deliberately NOT fixed — the repro comes first.
*(Archive note: the "armed in Room 8" half was REFUTED the same day — see KI-77''s corrected entry —
and the window model went on to predict the Room 8 arrival dump exactly on 2026-08-14.)*

**Artefacts:** `--driver ch20room1` (new), pre-registered predictions + full transcript in
`ai-research-notes/2026-08-13-ch20-room1-drive-predictions.md` (6 of 7 held).
**Refactor, proven neutral:** `Ch20DiveMode`''s fixture and legs 1-5 are now `_inject_dive_fixture()`
/ `_ingress()` so the new driver **reuses** the proven ingress instead of copying it — re-running
`--driver ch20dive` gave `legs=6/6 … ACCEPTANCE: PASS`, matching its documented prior result.

## 🚩 …AND THEN THROUGH ROOM 2, INTO THE ROOM 6 CURRENT MAZE (same session, later)

**`--driver ch20room2` → `ACCEPTANCE: PASS`, first drive, 10 of 10 pre-registered predictions.**
It re-solves Room 1 from scratch every run (the `FLAG_TEMP_*` objects respawn on every map load), so
**Room 1 is now n=3.** Route 2 was arbitrated first and, unlike Room 1''s, came out **clean**:
decomp + our own ROM agree on all 8 objects and upstream `puzzle_solver.py:395-402` is correct step
for step. Smash `(8,7)` → **exactly three** north pushes of boulder `id 4` → `(6,1)` →
`SEAFLOOR_CAVERN_ROOM6 (11,21)`.

**‼ THE HEADLINE IS A CORRECTION TO OUR OWN SHIPPED SOURCE.**
`STRENGTH-FLAG after the ROOM1→ROOM2 warp: **False**`. `modules/story/early_game.py` said in two
places that `FLAG_SYS_USE_STRENGTH` is *"NEVER CLEARED … once per SAVE, not once per map"*. It is
cleared on **EVERY WARP** (`ClearTempFieldEventData` → `LoadMapFromWarp`). The old claim rested on
"a decomp-wide search for `clearflag`" — the **script macro**; the clear is the C function
`FlagClear`, so that search could never have found it. ✅ **The code was always safe** —
`strength_push` re-checks per call — so this was **load-bearing documentation on top of correct
code**, invisible to every gate, and lethal only to the next author who deletes the re-check as
redundant. Both comments corrected. ⇒ **drift is STILL EXACTLY 3** — `early_game.py` was already
one of the three, so this adds no new file. (Measured with the loop in HOW TO RUN / TEST.)

**The three-point A/B earned its keep:** `M1 NO-PATH → M2 NO-PATH → M3 OK` attributes the opening to
the **pushes**, not the smash. A two-point A/B would have accepted "the rock was the only obstacle",
which is false.

**Room 6''s current model survives contact with the live room:** `calculate_path((11,21) → (4,1))` =
`OK len=13` measured from INSIDE — the same 13 waypoints `probe_ch20_currents.py` predicted from
outside. ✅ **AND IT IS NOW A WALK:** `--driver ch20room6` executed the crossing on 2026-08-13.
What remains unproven is the *intermediate* slide behaviour, not the crossing (KI-76).

**‼ KI-77 WAS CORRECTED THE SAME DAY IT WAS FILED, TWICE OVER.** The despawn window is now derived
(`x ∈ [px-9,px+10]`, `y ∈ [py-7,py+9]` — 20x17) and **predicts our live Room 1 dump 5/5 on the
boundary**. So (a) **"armed in Room 8" is REFUTED** — Room 8 is 11x14, *smaller than the window*;
the rooms at risk are the **large** ones. And (b) the game **physically resets a pushed boulder to
its template tile when it despawns**, so the planner is **fail-safe and never under-blocks** —
fixing it would have been fixing the wrong thing.

---

# MOVED 2026-08-14 (from 04-HANDOFF.md, for the R3 budget when the Room 9 banner landed) — the §Ch20 Room 6 block of 2026-08-13, verbatim:

## 🚩 …AND ACROSS THE ROOM 6 CURRENT MAZE, INTO ROOM 3 (same session, latest)

**`--driver ch20room6` → `ACCEPTANCE: PASS`, first drive, 8/8 pre-registered predictions.**
**‼ THIS IS THE FIRST EXECUTED CURRENT CROSSING IN THIS PROJECT.** Everything about Rooms 6/7 was
**planner-level only** until now — and *a plan is not a walk*. It was driven as its own increment,
deliberately NOT bundled with Room 3, so a failure would have been attributable.

    ROOM6 entry=(11,21)   PLAN (11,21)->(4,1): OK len=13
    CROSSING at=(''SEAFLOOR_CAVERN_ROOM3'', (4,15)) crossed=True
    ROOM3-WALK (4,15)->(8,1): OK len=18 contains (6,5)
    RESULT room2_ok=True crossed=True in_room3=True room3_walk=True can_continue=True

⇒ **The punch list''s "Rooms 6/7 need no solver" now rests on a WALK, not a plan.**
⚠ **Precisely:** the **endpoint** is proven, not the intermediate slide behaviour. No per-slide
telemetry; the planner''s 13 waypoints were never compared step-by-step to the executor''s path.

**‼ A DESIGN DECISION 20 MINUTES OLD SAVED THE RUN.** The crossing did not stop on `ROOM6 (4,1)` —
it carried straight through into Room 3. A strict `where == (ROOM6,(4,1))` test would have printed
**FAIL over a crossing that worked perfectly**. *Assert the outcome, not the position you expected.*
⚠ The arrow-warp branch added alongside it **never executed and is UNTESTED**.
*(Archive note 2026-08-14: that branch''s pattern was later exercised via ch20room8''s recovery
design, and the tile-derived-direction rule it carried became load-bearing there.)*

**✅ AND ROOM 3''S ARBITRATION WAS CONFIRMED LIVE, IN THE SAME RUN, FOR FREE.**
`calculate_path((4,15) → (8,1))` = **`OK len=18`, containing `(6,5)`**. So **Room 3 is crossable
PUSH-FREE — its 7-boulder puzzle really is OPTIONAL** — and **the push-free line unavoidably enters
a trainer sight tile**, so the walk must take the battle. ‼ Decomp says that is a single **DOUBLE**
battle (Shelly + Grunt5); **that half is still unobserved live** and is the top prediction for the
Room 3 drive. *(Archive note: it WAS then observed live — repeatedly; the double is confirmed.)*


---

# MOVED 2026-08-14 (from 04-HANDOFF.md, for the R3 budget when the PC/PARTY ROBUSTNESS queue replaced the Ch20 queue) — the ROOM 8 banner, verbatim:

## 🚩 ROOM 8 (2026-08-14, earlier today): 9/9 PUSHES, AND THE JAM-RECOVERY HANDLER IS *EXERCISED*, NOT JUST WRITTEN

**`--driver ch20room8` (NEW) → `ACCEPTANCE: PASS` twice.** The CLEAN run: first attempt, all
9 pushes of OUR adjudicated sequence (⛔ step 9 faces **LEFT**), every boulder verified by
`local_id` on its destination, exit path `(5,4)→(5,2)` `OK len=2`, **no boulder on `(5,3)`**,
`ROOM9 (5,4)` arrival, real step taken. **9/9 pre-registered predictions held**
(`ai-research-notes/2026-08-14-ch20-room8-drive-predictions.md`).

**The FAULT run (`POKEBOT_CH20_FAULT=room8`) proved the failure handler:** attempt 1 abandoned
after push 4 on purpose → exit to Room 3 via the `(5,12)` arrow warp → re-enter → all twelve
boulders respawned → attempt 2 ran 9/9 clean → `RESULT … attempts=2 recovered=True` →
`ACCEPTANCE: PASS`. ‼ The happy path cannot exercise an error path — this is the same rule that
caught the Room 1 `AttributeError`, applied on purpose this time.

**Three independent checks preceded the drive, and two of them changed the code or the claim:**
1. An offline adversarial agent tried to REFUTE the 9-push table (our ROM + the pret decomp,
   agreeing on all 12 boulder templates; per-step simulation with a fault-tested checker) —
   verdict **SURVIVES**, and it supplied the template table that turned KI-77's window into the
   exact prediction "8 of 12 visible at arrival", which the live run then matched **exactly**.
2. An adversarial diff review found the recovery handler **hardcoded `"Down"`** at `(5,12)`
   instead of deriving the hold direction from the live tile (the `_cross_room6` rule, whose own
   comment says why). Fixed BEFORE driving — and the fault run then showed the arrow warp fires
   during the navigate itself (held direction), so the map-check-first structure absorbed a case
   the hardcode would have hit blindly.
3. The Room-3 walk was extracted VERBATIM into `_cross_room3` so ch20room8 INHERITS it (the
   `_ingress` rule: reuse, never copy) — **neutrality proven by re-running `--driver ch20room3` →
   `ACCEPTANCE: PASS`**, verdict line identical to its documented 2026-08-13 result.

**Re-proof counts after this session's three full runs: R1 n=10, R2 n=7, R6 n=6, R3 n=5,
R8 n=2** — and the Room 3 DOUBLE battle at `(6,5)` reported `is_double=True` in **all three**.

⇒ *(superseded LATER THE SAME DAY — `ch20room9` is BUILT, DRIVEN and PASSING ×2; the facing
claim is MEASURED; see the NEWEST banner at the top. The live queue is the CHAPTER ASSEMBLY.)*
Its route detail stays true: trigger `(17,42)` not `(16,42)`; grade on
**`VAR_ROUTE128_STATE == 2`**, never the pre-warp Kyogre flag; escape **south to `(38,23)`,
Surf onto `(38,24)`** (9/9, `probe_route128_landing.py`); losing to Archie whiteouts out of the
dungeon. ⛔ Still NOT a chapter — drivers inject Dive; the ladder remains 20 of 24.



---

# MOVED 2026-08-14 (from 04-HANDOFF.md, same R3-budget pass) — the ROOM 3 banner of 2026-08-13, verbatim:

## 🚩 …AND THROUGH ROOM 3. THE BOT NOW STANDS IN ROOM 8 (same session, latest)

**`--driver ch20room3` → `ACCEPTANCE: PASS`, reproduced twice.** The WALK route — 18 steps, **zero
pushes**, straight through the trainer sight line — ending `SEAFLOOR_CAVERN_ROOM8 (5,12)` with a
real step taken. It re-proves every room beneath it: **Room 1 n=7, Room 2 n=4, Room 6 n=3.**

**✅ THE DOUBLE-BATTLE CLAIM IS CONFIRMED LIVE.** One trainer battle in Room 3, `is_double=True`,
fired at exactly `(6,5)` — the tile the Room 6 run had already measured the push-free path to
contain. With `usable=6` the engine collected **both** trainers into one double battle, exactly as
`trainer_see.c:214-217` reads. ‼ The precondition was asserted **before** the walk and reported with
the result, so the confirmation is attributable rather than "we happened to qualify".

**⛔ AND MY OWN DISCRIMINATOR PRINTED A FALSE "REFUTED".** It counted trainer battles **run-wide**,
sweeping in the Room 1 grunt that is fought every run: two battles in the *run*, **one** in the
*room under test*. **The instrument was wrong, not the claim.** Fixed to filter on the battle's own
map. ✅ Contained by two earlier choices worth copying: `saw_double` was **reported, not graded**,
and the raw per-battle log printed **the map next to the judgement** — which made it visible in
seconds instead of going into the docs as a refutation.

**✅ A KNOWN GAP CLOSED FOR FREE:** two wild encounters fired, one **between two Strength pushes**
in Room 2. The Room 2 note flagged exactly that as untested; the idempotent `strength_push` held.

⇒ *(superseded 2026-08-14 — `--driver ch20room8` is BUILT, DRIVEN and PASSING ×2, with the jam
recovery fault-proven; see the 2026-08-14 banner above. The live queue is ROOM 9.)* **NEXT: BUILD
`--driver ch20room8`** — ‼ **it does not exist yet**; it is the thing to write, not a command to run. Already adjudicated, so **use OUR 9-push sequence** (upstream's is
10 and touches an extra boulder). ⛔ **Step 9 faces LEFT, never UP:** a boulder pushed north from
`(5,4)` lands on `(5,3)` and **permanently seals the only route to the `(5,2)` exit**. ✅ A jam IS
recoverable — exit to Room 3 via `(5,12)` and re-enter; all twelve boulders respawn. Wire that as
the room's failure handler rather than improvising. Full table:
`ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md`.
**Then Room 9** — the 62-step walk to the trigger `(17,42)`, Archie, and the exit that lands on the
atoll (see the banner below).
> ‼ `stash@{0}` exists **on purpose** — see the STATE table; **never drop it.**



---

# MOVED 2026-08-14 (from 04-HANDOFF.md, for the R3 budget once the PC/PARTY arc became the live queue) — the ROOM 9 banner, verbatim:

## 🚩 NEWEST (2026-08-14): ROOM 9 — ARCHIE, KYOGRE, AND THE ATOLL ESCAPE, DRIVEN. `ACCEPTANCE: PASS` ×2, AND THE ONE LOSS IS A MEASUREMENT, NOT A FLAKE

**`--driver ch20room9` (NEW) → `ACCEPTANCE: PASS` on runs 1 and 3; run 2 LOST the Archie
fight.** The chain: re-prove Rooms 1→8, walk `(5,4) → (17,42)` (the trigger; ⛔ `(16,42)` is
only the sparkle), ride the scene — **Archie SINGLE battle** → Kyogre awakens → forced
`warp (38,22)` → the Route 128 Steven scene — then the measured escape: south to `(38,23)`,
Surf onto `(38,24)`, real path to the dive tile. **10/10 pre-registered predictions held**
(`ai-research-notes/2026-08-14-ch20-room9-drive-predictions.md`).

**What the three runs measured:**
* **The cutscene chain is DETERMINISTIC**: milestone loop-frame counts IDENTICAL across both
  passing runs (battle ~1836, warp ~5844, var2 ~5392); every mid-warp invariant exact
  (`kyogre_flag=True scs=1 r128=1 pos=(38,22)` — all written BEFORE the warp). **The
  previously-unmeasured facing claim is now measured: `facing='Up'` on release, twice.**
* ⚠ **The Archie fight is the chain's ONE stochastic element: 2W / 1L.** The party reaches him
  CHIPPED (run 3 telemetry: Zigzagoon FAINTED, Sceptile 96/135, `usable=5`; no heal exists in
  the cavern). ⇒ the CHAPTER must carry a **whiteout-retry policy** (Mossdeep Gym's N-attempts
  precedent; one retry = a full ~25-min re-dive) and/or **pre-boss readiness** (potions/order).
* ‼ **A lost run prints NO RESULT and structurally cannot** — the WhiteoutListener sets Manual
  and the harness drops the mode generator (KI-71's shape). The driver's `PRE-ARCHIE PARTY`
  HP-snapshot line is the loss's attribution record; grade a silent transcript by its presence.
* **Design decisions that survived contact** (see `06-DECISIONS-LOG.md` 2026-08-14): release is
  gated on **`VAR_ROUTE128_STATE == 2`**, never on "looks controllable" — the decomp recon
  proved a control seam between Room 9's script tail and the Route 128 re-lock; and the ride
  loop presses **A only when `is_waiting_for_input()`, B otherwise** — the adversarial reviewer
  caught the museum-greeter bug being re-written into a brand-new loop BEFORE the first run
  (`08-MISTAKES.md` 2026-08-14).

⇒ ⛔ **THIS IS NO LONGER THE NEXT ACTION — READ "NEXT ACTIONS" ITEM 0.** The user redirected priorities on 2026-08-14 after a live PC bug; the live queue is the **PC / PARTY ROBUSTNESS ARC**, and §Ch20 chapter assembly is **PARKED, NOT CANCELLED** — its requirements below stay accurate and are what to pick up when it resumes.
*(parked)* **ASSEMBLE §Ch20 AS A CHAPTER** — a module in `modules/story/`, wired as Segment 20,
built from the driven ingredients: `_ingress`, the room solves, the walk route, the var-gated
scene ride, the atoll escape. **The drivers inject Dive; the chapter must acquire it organically** (KI-63's
`ensure_hm_learner_making_room` is wired in **BOTH forks** — promoted 2026-08-14; ✅ **drift is ZERO** — KI-78 Stage 1 was promoted later the same day too, see the STATE table. ‼ This line briefly carried a non-zero figure after that promotion had already happened; the number is not restated here because the doc gate scans for it and cannot tell a quotation from a claim). Carry Blockers 3
and 4 from `ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md` (Repel policy for
the `water_mons` rooms; the badge/move pre-flight incl. Dive/BADGE07), the whiteout-retry
policy above, and grade the segment on `VAR_ROUTE128_STATE == 2` + the escape + can-continue
(`chapters.py:233` grades the LADDER chapter on `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`, which is
set pre-warp — the segment's own acceptance must be the stricter var).
> ‼ `stash@{0}` exists **on purpose** — see the STATE table; **never drop it.**


---

# MOVED 2026-08-14 (from 04-HANDOFF.md, R3 budget) — the ATOLL / Blocker-2 section, verbatim:

## ✅ THE ONE THAT WOULD STRAND THE RUN — NOW MEASURED IN OUR OWN ROM (9/9). Read before building §Ch20's exit

`ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md` holds four decomp blockers.
**Blocker 2 is the dangerous one, and it is now CONFIRMED by `probe_route128_landing.py` (NEW)** —
re-measured through `modules.map.get_map_all_tiles`, the reader the chapter will use, **sharing no
code with the agent's `map.bin` decode**, and agreeing on every number (71 / 41 / 1766).

The chapter's forced exit lands on `ROUTE128 (38,22)`, a shallow-water sandbar whose on-foot
component is **71 tiles and never touches the map edge**. The water north of it is a **41-tile
CLOSED LAGOON**, a **different component** from the 1,766-tile open ocean, on a map with
`"allow_escaping": false`. ‼ **And the landing tile has ZERO surfable neighbours** — all four are
shallow — so "Surf from where you land" does nothing in any direction and will read as a **hung
leg**, not as a failure.

⇒ **THE RULE, MEASURED: step SOUTH to `(38,23)`, face Down, Surf onto `(38,24)`.** One step,
confirmed one of 46 real launches onto the open ocean.

⛔ **BUT THE ORIGINAL FRAMING WAS TOO CRUDE AND WOULD HAVE PRODUCED A WRONG GUARD.** "Surf north
and you strand" is false: the atoll **wraps around**, and **33 launch points north of the landing
DO reach the open ocean**. The hazard is not a compass direction — it is the **28 launches into the
closed lagoon, on the atoll's WESTERN shore (`x = 33-35`)**. ‼ My first version of the probe checked
"no launch point lies north", got REFUTED, and **the check was wrong, not the claim** — corrected in
place, and it is exactly the failure shape this project logs most often.
✅ **MEASURED 2026-08-14** — the cutscene releases the player facing **`'Up'`**, observed on two
separate `--driver ch20room9` runs. Superseded: *"still unmeasured … the facing wants a live check"*.

⇒ *(superseded — Room 3 is DRIVEN and PASSING; the live queue is ROOM 8)* **NEXT: ROOM 3** —
`ai-research-notes/2026-08-13-ch20-room3-arbitration.md`.
⛔ **AND IT INVERTED WHAT I WROTE HERE FIRST.** An earlier pass told me Room 3 *"is not the walk
the spec calls it"* and I put that in this file and in the punch list. **A deeper pass — decomp
PLUS our own ROM — refuted the refutation:** `(4,15) → (8,1)` is reachable **PUSH-FREE in 18
steps** (our real planner returns `OK, 18 waypoints`), so the **7-boulder puzzle is OPTIONAL** and
exists only to dodge the trainers. Our build spec's "a walk (+2 trainers)" was **operationally
right**. ‼ *An agent's "REFUTED" is a claim like any other* — Room 1's held up because two
independent authorities checked it; this one had not been, and it was wrong.

‼ **THE SPEC'S ONE REAL ERROR: it is a single DOUBLE BATTLE (Shelly AND Grunt5 at once), not two
singles** — `trainer_see.c:214-217` does not stop at the first trainer, and both sight lines cover
the same tiles. ✅ We already ride double battles out (`modules/story/mossdeep_gym.py:315-369`);
**reuse its `MINIMUM_USABLE_POKEMON` precondition**, because with <2 usable the engine fires two
sequential singles instead — a different shape.
✅ **RECOMMENDATION: take the WALK, not the puzzle.** The pushes are irreversible within a visit and
a mid-sequence derail can WEDGE the room; the walk has nothing to wedge, and we win the fight.
‼ **The A/B cannot be a single tile here** — nothing becomes reachable "because the room was
solved". Grade on the path CONTAINING `(6,5)`, on both trainer flags being set, and on
"and the bot can continue". Details in the note.

---


---

# MOVED 2026-08-14 (from 04-HANDOFF.md's STATE table) — the DRIFT ROW's stacked history, verbatim.

‼ Why it moved: four supersessions in ONE table cell meant a sentence deep inside it ("`map_path.py` is the NEW third … NOT promoted — the USER's call") read as live and contradicted the same cell's own promoted-file list. **Everything below is HISTORY. As of 2026-08-14 drift is ZERO and every file named here was promoted.**

**3 as of 2026-08-14 — KI-78 STAGE 1, awaiting the USER's promotion call.** `modules/pokemon.py` (the new shared `same_pokemon` predicate), `modules/pokemon_party.py` and `modules/pokemon_storage.py` now key identity on **(personality, species)** instead of the personality alone. ‼ **This is the fix for the destructive path**: a Shedinja shares its Ninjask's PID, so "release the Shedinja" destroyed the Ninjask. A/B proven by `repro_pid_identity_key.py` (the OLD rule returns the WRONG slot on a real fabricated twin pair; the new one is correct), which is **gate #20**. ⛔ Until promotion, `custom-pokebot` has the KI-78 *detection warning* but NOT the fix — the wrong-target release is still live there. **Earlier the same day drift was ZERO**, described next: ✅ **the five drifted files were PROMOTED, user-approved, and that promotion was VERIFIED BY DRIVING.** Promoted: `modules/story/counter_hunt.py` (the user-observed Slugma/Winona derail fix), `modules/pokemon_party.py` (KI-78 **Stage 0, detect-only**), `modules/map_path.py` (KI-59), `modules/story/early_game.py` + `plugins/custom_modes/story_mode.py` (KI-63's wiring). **Evidence:** drift re-measured by hash in BOTH directions = 0; `probe_chapter_order.py --build custom` exit 0; **`repro_box_counter_move_test.py --build custom` exit 0** (the gate was made build-aware during this promotion — it hard-coded `sandbox` and so could not see the promoted fork at all); and a live drive **`--driver ch20dive --build custom` → `legs=6/6 at_entrance=True got_out=True can_continue=True ACCEPTANCE: PASS`**, matching the sandbox result. Restore point **`restore/2026-08-14-pre-promotion-5files`** (annotated, pushed) taken BEFORE the copy. ⛔ **This does NOT mean §Ch20 is a chapter** (it is not, in either fork — ladder still 20 of 24) **nor that KI-78 is fixed** (both forks now merely DETECT the PID collision). Full detail: `custom-pokebot/DIVERGENCE-LOG.md`, 2026-08-14. ‼ **MEASURE, don't trust this row** — the loop is below in "HOW TO RUN / TEST". ‼ **`modules/map_path.py` is the NEW third** — KI-59's fix (entry inversion + the new `blocked_exit_directions` exit half), A/B proven on `VICTORY_ROAD_1F` with a byte-identical `MOSSDEEP_CITY` collateral control, gated by `repro_impassable_dirs.py`. **NOT promoted — the USER's call, not asked for.** ⛔ Until it is, `custom-pokebot`'s planner still cannot see the 401 live `Impassable *` tiles (Regi tombs 144, Shoal Cave 98, Victory Road 58). The other two, unchanged, described next: **EXACTLY 2, both deliberate and sandbox-only (2026-08-13, earlier):** `modules/story/early_game.py` (the new `ensure_hm_learner_making_room`) and `plugins/custom_modes/story_mode.py` (both HM call sites wired to it). **This is KI-63's PRODUCTION WIRING, driven to a PASS but NOT promoted — promotion has not been asked for.** ⛔ Until it is, `custom-pokebot`'s copy of the KI-63 fix is **INERT**: it reads `_needs_party_slot` and nothing there sets it. Earlier today drift was ZERO twice (`restore/2026-08-13-pre-roster-promotion`, `restore/2026-08-13-pre-ki63-promotion`). ‼ **MEASURE, don't trust this row** — the loop is below in "HOW TO RUN / TEST".


# MOVED 2026-08-14 (later, from 04-HANDOFF.md's NEXT ACTIONS) — the ROOM 3 and ROOM 8 build blocks, verbatim.

‼ Why they moved: 04-HANDOFF.md hit its 900-line budget when PARTY ACCOUNTING STAGE 0 landed, and
these two were the largest blocks the file itself already labelled *(superseded)*. **Both rooms are
DRIVEN AND PASSING** (`--driver ch20room3` PASS x2, `--driver ch20room8` PASS x2, 2026-08-14) and
every reusable lesson in them is ALREADY carried by the ROOM 3 / ROOM 8 banners at the top of the
handoff — the walk route and the confirmed DOUBLE battle, and "step 9 faces LEFT, never UP".
⛔ **The move direction was checked deliberately**: what left is the SUPERSEDED build instruction,
what stayed is the CORRECTION. That is the opposite of the KI-39 archive move, which shipped the
refuted text and archived the fix. Nothing below should be acted on — it is a trail.
⚠ And note one line inside the block above this one is now itself stale: it says "as of 2026-08-14
drift is ZERO". That was true when written; PARTY ACCOUNTING STAGE 0 has since moved it. This file
is append-only history — `promote.py --check` is the only authority on the current figure.

*(superseded, kept for the route detail)* **ROOM 3 IS NEXT AND IS ALREADY ARBITRATED** —
`ai-research-notes/2026-08-13-ch20-room3-arbitration.md`. ✅ **Build the WALK route:**
`navigate_to(SEAFLOOR_CAVERN_ROOM3, (8,1))` riding battles out — 18 steps, **zero pushes**.
The 7-boulder puzzle is **OPTIONAL** (it only dodges the trainers) and its pushes are
irreversible within a visit, so a derail can WEDGE the room. ‼ **Precondition: ≥2 usable
Pokémon** — it is ONE **DOUBLE** battle (Shelly + Grunt5), not two singles; reuse
`mossdeep_gym.py`'s `MINIMUM_USABLE_POKEMON` gate. ‼ **The A/B cannot be a single tile** —
nothing becomes reachable by solving the room. Grade on: the planned path CONTAINS `(6,5)`,
both trainer flags SET afterwards, and "and the bot can continue" out of `(8,1)`.
⛔ *(superseded)* "The double battle is decomp-derived and not yet observed live" — it **WAS**
observed, on 2026-08-13: one trainer battle in Room 3, `is_double=True`, at exactly `(6,5)`,
with `usable=6` asserted beforehand. See `ai-research-notes/2026-08-13-ch20-room3-drive-predictions.md`.

*(superseded — Room 8 is DRIVEN and PASSING x2, 2026-08-14; kept for the hazard detail)*
**(b2) ROOM 8 IS ALREADY ADJUDICATED — build from OUR sequence, not upstream's.** Both work;
ours is **9 pushes vs upstream's 10** and never touches boulder #3. Full table in
`ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md`. ⛔ **Step 9 must face LEFT,
never UP** — a boulder pushed north from `(5,4)` lands on `(5,3)` and **permanently seals the
only route to the `(5,2)` exit warp**. ✅ A jam IS recoverable: exit to Room 3 via `(5,12)` and
re-enter; all twelve boulders respawn. Wire that as the room's failure handler.


# MOVED 2026-08-14 (later, from 04-HANDOFF.md NEXT ACTIONS item 1b) — verbatim.

‼ Why it moved: line budget, and item 1b was already answered — the KI-63 wiring WAS promoted on
2026-08-14 and is in both forks. The text below self-labelled as "the first decision for the user"
and would send a cold session to ask for something already granted. **The measured-worth figures
are the part worth keeping**, which is why they were also summarised in the surviving 1b line
rather than only archived here.

*(superseded)* ⛔ **THE FIRST DECISION FOR THE USER: promote the KI-63 WIRING?** Until it is promoted,
`custom-pokebot`'s copy of the KI-63 fix is **INERT** — it reads `_needs_party_slot` and
nothing in that tree sets it, so a real run there still dies on a full party.
**Measured worth: 20 terminal run-kills in 1,129 runs (0.91% excl. a reverted party-cap
bundle), #1 of 14 derail causes by frames per event (1,717k ≈ 46 min), every one five badges
deep.** Restore-point-first, then verify by DRIVING `--build custom`, never by a diff.


# MOVED 2026-08-14 (later, from 04-HANDOFF.md NEXT ACTIONS item 2) — the reorder_party TRACE DETAIL, verbatim.

‼ Why it moved: line budget again, when the heal-piggyback observability work landed. Item 2 is
**DONE** (`--driver roster` passes, both files promoted to BOTH forks). What stays in the handoff is
the STATUS and the one thing still OPEN (the deposit/withdraw half of `#24-roster`). What moved is
the settled trace detail below — valuable, but it is evidence for a closed question.
⚠ **The stale-cursor note is the one worth re-reading if a future roster drive ever mis-swaps.**

> 2. ✅ **DONE 2026-08-13 — `reorder_party()` IS DRIVEN.** `--driver roster` exists and passes.
>    Six swaps, all verified by PID, including the never-driven `RotatePokemon(i, j != 0)`.
>    **Both unknowns this item asked about are now SETTLED by the trace:**
>    * *the exit-menu timing gap* — **REAL, and it was a bug.** The party menu's last act is
>      re-showing the Start menu (`Task_ShowStartMenu` still live at f660 of a 662-frame call), so
>      `reorder_party` used to return `True` while the avatar could not walk. **Fixed** with a
>      `swapped`-gated `_settle()`; A/B proven (`moved=False`→`True`, FAIL→PASS, and phase 3 costs
>      0 frames in BOTH arms — the control arm proving the gate does not over-fire).
>    * *the stale-cursor read* — **the mechanism is real but did NOT fire.** `gPartyMenu.slot_id`
>      is **not reset between menu sessions**: the tracer read a stale `slot_id=2` on the overworld
>      before the menu had opened, and `navigate_to_mon:520-524` computes its scroll direction from
>      exactly that global. It happened to be re-read live in time. **This is luck, not safety** —
>      re-check it first if a future roster drive ever mis-swaps.


# MOVED 2026-08-14 (later, from 04-HANDOFF.md) — the KI-63 / SHOAL CAVE block, verbatim.

‼ Why it moved: the line budget, when (P3b) was made executable. A Tier 2 cold-start audit had
flagged this block as a `(superseded)` tag with UNBOUNDED SCOPE spanning ~28 lines — including a
ruling that is still LIVE. Rather than leave an ambiguous tag in the current-state file, the whole
block moved here and the handoff keeps a short pointer to the parts that are still true.
⛔ **STILL LIVE inside it:** the *SHOAL CAVE IS NOT ADOPTED* ruling (LOW 278 / HIGH 0 reachable
spin tiles, re-derived on the corrected model) and **KI-73 = cache poisoning** in a shared
`_map_layout_cache`. ✅ SUPERSEDED: the *this is the NEXT build* framing — KI-63 shipped and was
promoted. Full rationale for the ruling: `06-DECISIONS-LOG.md`.

* *(superseded — ‼ **SCOPE: only the "this is the NEXT build" FRAMING is stale; KI-63 shipped and
  was promoted.** The ⛔ ends at the `#24-ballstarve` bullet below. **Everything inside is still
  factually LIVE** — in particular the ✅ **"SHOAL CAVE IS NOT ADOPTED"** ruling and its LOW 278 /
  HIGH 0 numbers, which were re-derived on the corrected model and still stand. A Tier 2 cold-start
  audit flagged this tag as unbounded across ~28 lines; it is bounded here rather than deleted,
  because the content is worth keeping and only the ordering claim expired.)*
  **THE NEXT BUILD WAS SPECIFIED AND MEASURED: KI-63.** Read
  `ai-research-notes/2026-08-13-ki63-dive-learner-acquisition-plan.md` — it has the build order,
  the pre-registered failure modes, and **two corrections to this handoff's own older text**:
  the deposit path KI-54 named (`withdraw_from_box`'s deposit block (~`modules/story/pc_trip.py:437-461`)) **cannot free a slot pre-catch**
  (it returns immediately when nothing is boxed), and `deposit_dead_weight_if_worth_it` is a
  **silent no-op** behind `POKEBOT_PC_ROTATION`. **A new narrow ungated one-deposit function is
  needed**, and **deposit-first is the wrong order.**
  ✅ Already verified safe: teaching Dive **cannot** overwrite Surf (HM slots are filtered at two
  layers), and `find_dead_weight` **exempts** the sole Surf carrier.
  ✅ **RULED 2026-08-13 (user delegated it to me): SHOAL CAVE IS NOT ADOPTED. Route 117 stays.**
  Full rationale + the three conditions that would unlock it: `06-DECISIONS-LOG.md`.
  ‼‼ **THE DECISIVE NUMBER, measured live and reproduced by me — reachable spin tiles:
  LOW 278, HIGH 0.** At high tide every candidate becomes `Shallow Water` with
  `has_encounters=False`, and **the failure mode is a SILENT STALL**: the tile is still standable,
  so `ensure_hm_learner` burns its entire 40,000-frame budget meeting nothing. KI-54's 65 encounter
  tiles at high tide are **REAL** — reproduced exactly — but form an **ISLAND** unreachable from
  the entrance warp. What was never checked was reachability, not the count.
  ⚠ **MY FIRST RATIONALE WAS PARTLY WRONG and is corrected in place** (`06-DECISIONS-LOG.md`,
  `08-MISTAKES.md`): I claimed the tooling could not see the room at all. It can —
  `get_map_data_for_current_position()` reads the **live** header. **KI-73's real defect is CACHE
  POISONING**: both paths share one `_map_layout_cache` keyed on `(group, number)`, so the first
  writer wins for the session. Still real, still unfixed, narrower than I said.
  ✅ The tide gate itself is **cheap and decomp-confirmed**: LOW = hours **03-08 and 15-20**,
  sampled **once on entry and frozen for the visit**; `get_clock_time().hours` predicts it and
  `get_event_flag("SYS_SHOAL_TIDE")` (set = HIGH) asserts it.
  ⇒ **Unlock is now short:** fix/fence **KI-73** → **live two-way sweep** one of the 278 low-tide
  tiles → ship behind the clock+flag gate in a **SEPARATE HM-ground table** (so `best_training_area`,
  which reads the same `TRAINING_GRASS` list, is untouched).

# MOVED 2026-08-15 (from 04-HANDOFF.md) — the ROOM 6 and ROOM 3 summary banners, verbatim.

‼ Why they moved: the line budget, when (P4) Stage 1 landed. These were already REDUCED summaries
of blocks archived on 2026-08-14 — a summary of a summary. Both rooms are DRIVEN AND PASSING and
the handoff keeps that status; what moved is the evidence detail.
⛔ **STILL LIVE, and kept in the handoff rather than only here:** Room 6's rule *assert the
OUTCOME, not the position you expected* (a strict positional assert would have FAILED a perfect
crossing — `06-DECISIONS-LOG.md`), and Room 3's *the instrument was wrong, not the claim* (a
discriminator counted trainer battles RUN-WIDE and printed a false REFUTED over data that
CONFIRMED the decomp's single-DOUBLE-battle claim). ⚠ Also still true: Room 6's arrow-warp
derived-direction branch remains UNEXECUTED.

## ✅ ROOM 6 (the first executed current crossing, 2026-08-13) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-14)

Moved for the R3 budget. ‼ **Keep only:** the crossing carried straight through into Room 3 and
a strict positional assert would have FAILED a perfect crossing — *assert the outcome, not the
position you expected* (now in `06-DECISIONS-LOG.md`). ⚠ Still true: the **endpoint** is proven,
not the per-slide behaviour (KI-76's correctness half). ⛔ **CORRECTED 2026-08-14:** this said the
arrow-warp branch "first executed later, in ch20room8's recovery" — **it did not.** Both there and
here the warp fired DURING the navigate (the walker holds the direction), so the derived-direction
branch was SKIPPED in both. **It remains UNEXECUTED.** Room 6 is now **n=9**.

## ✅ ROOM 3 (driven 2026-08-13) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-14)

Moved for the R3 budget. ‼ **Keep only the two reusable lessons:** the WALK route through Room 3
is 18 steps and **zero pushes** (its 7-boulder puzzle is OPTIONAL — it only dodges the trainers),
and the decomp's **single DOUBLE battle** claim (Shelly + Grunt5 collected into one fight) was
**CONFIRMED LIVE** at exactly `(6,5)` with `usable=6` asserted BEFORE the walk, so the result is
attributable. ⛔ **And my own discriminator printed a false "REFUTED"** — it counted trainer
battles RUN-WIDE, sweeping in the Room 1 grunt that is fought every run. **The instrument was
wrong, not the claim**, and it was caught only because `saw_double` was REPORTED rather than
GRADED and the raw log printed the MAP beside each judgement.


# MOVED 2026-08-15 (later, from 04-HANDOFF.md) — the ROOMS 1 AND 2 summary banner, verbatim.

‼ Why it moved: the line budget again, when (P4) Stage 1's runnable commands were added to
HOW TO RUN / TEST (a Tier 1 reviewer found the driver was not runnable from the handoff at all —
the more serious of its two findings). Rooms 1 and 2 are DRIVEN AND PASSING; the handoff keeps
that status and the rules below in condensed form.
⛔ **STILL LIVE:** *copy upstream's ROUTE, never its CONTROL FLOW* (our pushes go through
`strength_push`, bounded and verified by `local_id`); **`FLAG_SYS_USE_STRENGTH` is cleared on
EVERY WARP** (`ClearTempFieldEventData` → `LoadMapFromWarp`) — the code was always safe, the
COMMENTS were wrong; and KI-77's despawn window is derived (20x17) and has since predicted a
live arrival dump exactly.

## ✅ ROOMS 1 AND 2 (driven 2026-08-13) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-14)

Both blocks moved verbatim for the R3 budget when the Room 8 banner landed. ‼ **Keep only what
later work still leans on:** (1) Room 1's A/B (`PathFindingError → OK len=6`, live objects both
arms) is what converted the Area Atlas's NO-PATH from a lower bound into a fact — and its route
had to be ARBITRATED first because our build spec's "exhaustive NORTH push" claim was **false**
(either direction is legal; upstream's SOUTH ships). *Copy upstream's ROUTE, never its CONTROL
FLOW* — our pushes go through `strength_push` (bounded, verifies by `local_id`). (2) Room 2's
headline was a correction to our own shipped source: **`FLAG_SYS_USE_STRENGTH` is cleared on
EVERY WARP** (`ClearTempFieldEventData` → `LoadMapFromWarp`); the code was always safe, the
comments were wrong. (3) **KI-77** was filed from Room 1's short object dump (2 of 5) and
corrected same-day: the despawn window is derived (20x17), the game resets a despawned boulder
to its template, the planner never under-blocks — and the window has since predicted the Room 8
arrival dump exactly (8 of 12, 2026-08-14).


# MOVED 2026-08-15 (wrap-up) — the ATOLL EXIT banner, verbatim.

‼ Why: the handoff hit its 900-line cap while a session-end cross-doc sweep was correcting 19
defects, several of which needed MORE words, not fewer. The atoll exit is DRIVEN and its rule is
kept in the handoff in one line.
⛔ **STILL LIVE:** the §Ch20 exit lands on `ROUTE128 (38,22)`, whose landing tile has **ZERO
surfable neighbours** — a naive Surf does nothing in any direction and reads as a HUNG LEG, not a
failure. ⇒ step SOUTH to `(38,23)`, face Down, Surf onto `(38,24)`. The hazard is NOT a compass
direction: the trap is 28 launches into a 41-tile CLOSED LAGOON on the WESTERN shore.

## ✅ THE ATOLL EXIT (Blocker 2) — MEASURED 9/9, then DRIVEN — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md`

‼ **Keep the rule, it is the whole point:** the §Ch20 exit lands on `ROUTE128 (38,22)`, a sandbar
whose on-foot component is 71 tiles and **whose landing tile has ZERO surfable neighbours** — so a
naive "Surf from where you land" does nothing in any direction and reads as a **HUNG LEG, not a
failure**. ⇒ **step SOUTH to `(38,23)`, face Down, Surf onto `(38,24)`.** ✅ Driven 2026-08-14
(`--driver ch20room9`). ⛔ The hazard is NOT a compass direction — the atoll wraps, and 33 launch
points north DO reach open water; the trap is the **28 launches into a 41-tile CLOSED LAGOON** on
the WESTERN shore. Full measurement: `ai-research-notes/2026-08-13-ch20-decomp-blockers-and-room8.md`
and `tools/story-dev/probe_route128_landing.py`.
---

## 🧭 THE PATHFINDER + §Ch20 SCOPING BACKGROUND — MOVED here from `04-HANDOFF.md` (2026-08-15, on the R3 line budget when (P4) Stage 2 landed)

> Verbatim as it stood in the handoff. ‼ Its reusable content is summarised in a 6-line pointer
> that replaced it there; this is the full text.

## 🧭 WHAT THE PREVIOUS SESSION DID (PATHFINDER + §Ch20 SCOPING) — still the best background


**1. KI-59 (the pathfinder's inverted `Impassable *` handling) — MEASURED, FIXED, PROVEN, GATED.**
* ⛔ **Its headline was wrong in four documents** and is retracted: *"armed in the Seafloor Cavern,
  A/B on `SEAFLOOR_CAVERN_ROOM1`"*. The handler is the `elif` of `if tile.collision != 0`, **all 115
  cavern tiles have `collision=1`, so ZERO reach it** — that A/B would have measured a zero delta and
  invited "KI-59 isn't real". Game-wide: **2,658 such tiles, 2,257 dormant, 401 (15.1%) live**,
  chiefly the **Regi tombs (144)**, **Shoal Cave (98)**, **Victory Road (58)**.
* ✅ **Fixed both halves** — the entry vector, **plus a new `PathTile.blocked_exit_directions`** for
  the decomp's exit rule, which the data model previously could not express at all.
  **A/B on `VICTORY_ROAD_1F`: `calculate_path` went from NO-PATH from EVERY direction onto all 29
  live tiles (they were invisible to the planner) to `OK len=1` on the legal ones.** Mossdeep
  collateral control byte-identical; gate **`repro_impassable_dirs.py`** is now #17.

**2. §Ch20 (Seafloor Cavern / Kyogre) — SCOPED END TO END, NOT YET BUILT.**
* `#24-ch20rename` **DONE** (`--driver ch20dive`, `probe_ch20_topology.py`), verified by re-running.
* **Area Atlas** (`probe_ch20_interior.py`): warp graph benign, all rooms reachable; **Rooms 1/2/3/5/8
  are STRENGTH-BOULDER puzzles**, Rooms 6/7 are open-water **current mazes**, Rooms 4/9 split by terrain.
* **11-leg build spec** with assertable conditions:
  `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`. ‼ It corrected **our own docs**:
  **ROCK SMASH is mandatory** (Strength alone is physically stuck in Room 1), the trigger tile is
  **`(17,42)` not `(16,42)`**, and the chapter must be graded on **`VAR_ROUTE128_STATE == 2`**, not
  the Kyogre flag — which is set *before* a forced warp into a SECOND cutscene, landing on a
  **sandbar** the bot must Surf off.
* ✅ **The current mazes are routable by our planner** (4/4 pre-registered predictions, slide model
  proven in use), so Rooms 6/7 need **no solver**.

**3. NEW ISSUES FILED: KI-74, KI-75, KI-76** (see `05-KNOWN-ISSUES.md`). KI-76's **safety half is
fixed** (bounded slide loop + `None` guards, fault-tested); its **correctness half is OPEN**.

⇒ ✅ **ALL NINE ROOMS ARE DRIVEN — the cavern is END TO END (2026-08-14).** Seven drivers,
all `ACCEPTANCE: PASS`. ⛔ **DO NOT REBUILD ANY OF THEM.**
⛔ **The line below is STALE and is kept only for its trail — it says Rooms 8 and 9 are still
planning-only, which was true for a few hours on 2026-08-13 and is not true now:**
*(stale)* ⛔ **UPDATED:** Rooms **2, 6 and 3 are now driven too** — only Rooms 8 and 9 remain planning-only.


---

## ⏱ THE 2026-08-13-ERA "60-SECOND VERSION" — MOVED here from `04-HANDOFF.md` (2026-08-15)

> ‼ **Why it moved:** it was still titled *"THE 60-SECOND VERSION (if you read nothing else)"* at
> the TOP of the handoff while describing the roster/puzzle-solver/dive session of **2026-08-13** —
> so the summary a cold reader hit FIRST was two arcs stale. A current 60-second version replaced
> it in place. Nothing here is deleted; several of these items are still true and are cited from
> the replacement.

## ⏱ THE 60-SECOND VERSION (if you read nothing else)
* **`reorder_party()` IS NOW DRIVEN AND PROVEN.** `--driver roster` (NEW) ran **six swaps, all
  verified by PID**, including **`RotatePokemon(i, j != 0)` — a path nothing in this project had
  ever driven.** The party-ORDER capability the Regi arc needs is real, not just planned.
* **The drive found a real defect and it is FIXED, A/B proven:** `reorder_party()` returned `True`
  with the avatar **unable to walk**. ‼ Every cheap check said it was fine — not Manual, state
  already `OVERWORLD`, start menu already closed. Only asking it to MOVE revealed it.
* **‼ 0 of 6 pre-registered predictions fired, and neither prediction pass found the real bug.**
  Both hunted the KI-38 hang family because that is where the docs point. See
  `ai-research-notes/2026-08-13-roster-drive-predictions.md` — it holds the full raw transcripts.
* **Two issues filed, both deliberately NOT fixed: KI-70** (`_rotate_lead_safely` has the same
  shape, on the hottest path in the bot — **measured, margin held, but n = 1**) and **KI-71**
  (roster.py's "dropped to MANUAL" guard is **unreachable**; `main.py:145-147` abandons the
  generator first).
* **`puzzle_solver.py` IS A RECIPE BOOK, NOT A SHORTCUT — COPY FROM IT, DO NOT DRIVE IT.**
  It is byte-identical to the upstream mirror and holds the Seafloor Cavern + Sealed Chamber +
  Regi routes. ‼ **I first wrote this up as "it already ships §Ch21 and the Regi arc" and that was
  OVERSTATED** — an adversarial pass refuted it and I verified the refutation myself:
  the Seafloor branch ends `navigate_to(ROOM9, (16,42))` → `set_manual_mode()` — ‼ **and (16,42) is
  PLAIN FLOOR that fires NOTHING; the real coord trigger is `(17,42)`, one tile EAST**
  (`Room9/map.json:124-134`, decomp-verified 2026-08-13). So upstream stops one tile short of the
  event as well as handing off. (it parks the bot on
  **Archie's own cutscene tile** and hands control to a human — no battle, no progression, no exit),
  and the Regi branches **open the door only**, ending at the tomb's EXIT warp, never at the statue.
  **What survives is still valuable**: the `dive() → navigate → surface_from_dive()` template (which
  `--driver ch20dive` copied to a 6/6 PASS), free hand-derived room coordinates, and independent
  corroboration of **KI-69**'s Emerald party order (`("Wailord", 0)` / `("Relicanth", size-1)`).
  Read `ai-research-notes/2026-08-13-puzzle-solver-already-ships-ch21-and-the-regi-arc.md` —
  **the correction is at the top.** ⛔ Never point it at a Regi tomb: its battle handling is
  `handle_encounter(encounter, enable_auto_battle=True)` (`puzzle_solver.py:99` — ‼ the kwarg is
  **`enable_auto_battle`**, corrected 2026-08-13; this line used to say `auto_battle=True`, which
  greps to nothing) and KO'ing a Regi destroys the encounter. ✅ **Re-audited 2026-08-13: the hazard
  is REAL but currently UNREACHABLE** — every Regi branch calls `set_manual_mode()` before the statue
  is engaged, and `main.py:145-146` discards the generator on the next frame. ‼ One residual: the
  shared tail presses `A` once *before* its first `yield`, so a single stray A can be emitted after
  Manual is set; on the Emerald paths the avatar is still in the OUTER room so it cannot reach a
  statue, but the R/S paths end at `(8,11)` INSIDE and that tile was not checked.
* **✅ THE FIRST DRIVEN DIVE IN THIS PROJECT — KI-68 step 1 IS DONE.** `--driver ch20dive` (NEW)
  → `ACCEPTANCE: PASS legs=6/6 at_entrance=True got_out=True can_continue=True`. Mossdeep →
  `SEAFLOOR_CAVERN_ENTRANCE (10,17)` **and back out to the open ocean**.
  ‼ **THE STATIC WARP DATA IS MISLEADING AT BOTH ENDS OF THIS CAVERN** — the way in *and* the way
  out are RUNTIME `setdivewarp`s that no warp-graph or path scan can see. **Drive it; do not read
  it.** The way out is three hops, not the one the table implies.
  ‼ **This does NOT make §Ch21 unblocked** — the run INJECTED Dive with a debug write. Acquiring a
  real Dive learner (KI-63) is still open.
* **KI-72 filed (NEW, code-verified):** `calculate_path` has never heard of
  `"Underwater Blocked Above"` / `"Seaweed No Surfacing"` — the two tile types you cannot surface
  from — so it will route a dive to a dead end. ⇒ **NEVER let the planner choose where you
  surface**; pick the tile explicitly, as upstream already does.
* **✅✅✅ KI-63 IS RESOLVED *AND NOW WIRED INTO PRODUCTION* (sandbox).** `story_mode.py`'s two HM
  call sites (Rock Smash, Surf) call the new `ensure_hm_learner_making_room`, which frees ONE slot
  and retries once — **only** on the specific "party is full" failure. New gate
  **`repro_hm_slot_wiring.py` (22/22, fault-injected)** keeps the chain connected, because the
  previous failure was *a chain of correct parts with one link missing* and nothing caught it.
  **📊 MEASURED WORTH (1,129 runs):** 20 terminal run-kills (**0.91%** excl. a reverted party-cap
  bundle), **#1 of 14 derail causes by frames per event (1,717k avg ≈ 46 min)** — 7.2% of all
  derailed lane time from 3.4% of derails, **every one five badges deep**. Rare, but it kills the
  best runs. ✅ **PROMOTED 2026-08-14 — `custom-pokebot` is NO LONGER inert.** Superseded: *that it was still inert and promotion had not been asked for*.
* *(SUPERSEDED by the bullet above — kept for its detail. ⛔ **This marker used to say the "not wired" half was still true for `custom-pokebot`; that is FALSE since the 2026-08-14 promotion — it is wired in BOTH forks and drift is ZERO.**)* **KI-63 IS RESOLVED — THE BOT ACQUIRES DIVE BY PLAYING.** `--driver divelearner` (NEW) →
  `ACCEPTANCE: PASS` **on the first drive**: freed a slot (Skitty L17 deposited), hunted and caught
  a **Marill L13** (balls 19→17), taught **Dive over Defense Curl** (the 0-power move), and
  **Zigzagoon kept Surf**. `knows_dive=True can_dive=True surf_intact=True can_continue=True`.
  **NEW production code:** `pc_trip.deposit_one_dead_weight()` + an opt-in `_needs_party_slot`
  piggyback in `heal_in_pokemon_center`.
  ‼‼ **BUT THE CAPABILITY IS PROVEN, NOT WIRED.** `_needs_party_slot` has **no setter anywhere in
  `modules/` or `plugins/`** — only the driver sets it. In a real `StoryMode` run the piggyback
  **never fires** and `ensure_hm_learner(HM08)` still raises *"the party is full"*. **Wiring
  `story_mode.py` to catch that and set the flag is the remaining work** — do not read this as
  "§Ch21 is unblocked in production". §Ch21 also still has to be BUILT, and the learner is an L13
  HM slave 36 levels below the team.
* ✅ **KI-63 (the Dive-learner acquisition) SHIPPED AND WAS PROMOTED.** Its 33-line plan block
  moved to `28-HANDOFF-ARCHIVE.md` 2026-08-14 (line budget; a Tier 2 audit had flagged its
  `(superseded)` tag as unbounded). ⛔ **Two things in it are STILL LIVE:** (1) ✅ **SHOAL CAVE IS
  NOT ADOPTED, Route 117 stays** — reachable spin tiles **LOW 278 / HIGH 0**, and at high tide the
  failure is a **SILENT STALL**, not an error (rationale + the three unlock conditions:
  `06-DECISIONS-LOG.md`); (2) **KI-73 is CACHE POISONING** — both paths share one
  `_map_layout_cache` keyed on `(group, number)`, so the first writer wins for the session.
* **`#24-ballstarve`'s premise does not hold at `post_dive.ss1`** — 19 balls, $54,334 measured.
  ‼ **Not closed**: the item was filed from a mid-game Surf-era batch and may still be real there.
* **Nothing is parked. Nothing is running.** All gates exit 0 after the change. *(That said "15";
  the suite is **23** today — `run_gates.py` PRINTS the count and is authoritative, this prose is not, and this line alone has claimed 15, 17, 21 and 22.)*
* **§Ch19 is DONE and the ladder runs 20 of 24 beats.** §Ch18 + §Ch19 are **PROMOTED** to
  `custom-pokebot/` and verified by driving `--build custom`, including the real ladder.
* ⛔ **RETRACTED 2026-08-13 — three errors in one line.** It is **Chapter 20**, not 21 (see the
  naming correction above); it is **NOT BLOCKED** (Rooms 1/2/6/3 are driven and passing); and
  **KI-68 is RESOLVED and lives in `31-KNOWN-ISSUES-ARCHIVE.md`, not in `05-KNOWN-ISSUES.md`** —
  its route is driven. Superseded text: *"The next content beat (§Ch21, Seafloor Cavern) is
  BLOCKED, and the reason changed twice — read KI-68 before touching it."* It is *not* the party slot, and Dive is *not* impossible:
  the planner cannot AUTO-route a dive, so **a chapter must drive `dive()` explicitly.**
* **The REGI arc is the user's ask** — read **KI-69**. ‼ **Emerald reversed the party order:
  WAILORD first, RELICANTH last**, and the wrong order fails **silently**. ‼ **The Regi battle is
  UNRECOVERABLE** — a KO *or* a whiteout deletes the encounter permanently.
* **✅✅ KI-59 IS FIXED, BOTH HALVES, A/B PROVEN (2026-08-13, latest).** `map_path.py`'s entry vector
  now starts all-True and CLEARS `[opposite(D)]`, and a **NEW `PathTile.blocked_exit_directions`**
  carries the decomp's *exit* rule, checked on the SOURCE tile in the A* loop — `is_tile_accessible`
  is handed the NEIGHBOUR and structurally could never express it. **THE A/B on `VICTORY_ROAD_1F`:
  before, `calculate_path` returned NO-PATH from EVERY direction onto all 29 live tiles — they were
  completely invisible to the planner; after, the legal approaches return `OK len=1`.** The gate
  `repro_impassable_dirs.py` goes **exit 1 → exit 0** (29/29 mismatches → 0/29) and is now **gate
  #17**. **Collateral control:** the `MOSSDEEP_CITY` arm of `probe_ki59_routing_ab.py` is
  **byte-identical** across both arms (real production code both times, via `git stash`).
  ‼ **`probe_shoal_tide.py` was corrected in lockstep** — it had COPIED the bug, so it agreed with
  production while both were wrong — and **its numbers re-derived on the fixed model are UNCHANGED
  (LOW 278 / HIGH 0)**, so the **"Shoal Cave is NOT adopted"** ruling stands on a correct model.
  ✅ **PROMOTED 2026-08-14 — this file is in BOTH forks.** ‼ It took drift to nil AT THAT MOMENT;
  do not read it as a statement about drift TODAY, which PARTY ACCOUNTING STAGE 0 has since moved
  (see the STATE line at the top — `promote.py --check` is the only authority on the current
  figure, and no prose here should restate it).
* **‼ THE MEASUREMENT THAT PRECEDED IT: KI-59's HEADLINE WAS WRONG AND IS RETRACTED IN FOUR
  DOCS.** The inversion in `map_path.py:128-132` is **real and decomp-confirmed** — for
  `Impassable North` the shipped `[--S-]` is the *exact complement* of correct `[NE-W]`, so it
  refuses all three legal entries **and permits the one illegal one**. ⛔ **But it was NEVER a
  Seafloor Cavern blocker.** The handler is the `elif` of `if tile.collision != 0:`, and **all 115
  cavern tiles have `collision=1` ⇒ zero reach it**; the A/B four documents prescribed
  (`SEAFLOOR_CAVERN_ROOM1`) would have measured a **zero delta**. Swept over **all 518 maps**:
  **2,658 tiles, 2,257 dormant, 401 live (15.1%)**, concentrated on the **REGI TOMBS (144)**,
  **SHOAL CAVE (98)** and **VICTORY ROAD (58)**. ⇒ **KI-59 gates the REGI ARC, not the cavern.**
  New artifact `tools/story-dev/probe_impassable_dirs.py`; a fresh-process reverse-order control
  rules out KI-73 cache poisoning, and an **adversarial reviewer re-derived every number by parsing
  the `.gba` off disk with ZERO shared code** — byte-for-byte agreement. **The fix is specified and
  its hazards are pre-checked, but NOT YET WRITTEN** — see `#24-impassabledirs`. ⇒ **Run the A/B on
  `VICTORY_ROAD_1F` (29 live tiles) with a Seafloor room as the negative control**, and assert BOTH
  directions: ⚠ the counts are **static ROM layouts**, and the Regi tombs / Shoal Cave / Lilycove
  lobby all rewrite their own tiles at runtime (`setmetatile`/`setmaplayoutindex`) — **no Seafloor
  Cavern script does**, so that conclusion is unaffected. ‼ Knock-on: `probe_shoal_tide.py:364-367`
  replicates the inversion, and that probe produced the number behind the **"Shoal Cave is NOT
  adopted"** ruling.
* **Run `preflight.py` first.** Then the gate list in "HOW TO RUN / TEST".



## 2026-08-15 — archived from `04-HANDOFF.md`: the drift-count line's staleness history (moved on the 900-line budget)

The handoff's sandbox→custom drift statement went stale **four times in two days**, and the
commentary tracking that lived inline until the file hit its line budget. Preserved here in full:

> ⛔⛔ *(THIS ONE LINE HAS NOW GONE STALE THREE TIMES IN A SINGLE DAY, and every time for the same
> reason: it spelled the count as an ENGLISH WORD naming a specific file, so a sweep for the
> NUMERAL walked straight past it. **Digits, not words** — the rule that also caught a spelled-out
> "THREE" sitting here for a day. ‼ When you change a drift count, grep the word forms too, not
> just the numeral. ⚠ And note `audit_doc_consistency` cannot tell a QUOTATION from a claim: it
> red-flagged an earlier draft of this very parenthetical for merely reciting the stale wording,
> which is why the wording is described here rather than reproduced.)*

**Fourth incident, 2026-08-15 (the one that produced this archive move).** A deliberate
comment-only `story_mode.py` fix took drift 0 → 1. `audit_doc_consistency` flagged **3** stale
claims (`04-HANDOFF.md:29`, `:158`, `05-KNOWN-ISSUES.md:2702`) out of **7** that existed. The four
it could NOT see: `04-HANDOFF.md:10` (banner), `:24` (spelled **"zero"**), `:195` (phrased
*"0 as of 2026-08-15"* inside a table cell), and `03-PUNCH-LIST.md:380`. Plus five further
`0 differing, 0 orphaned` instructions the drift check does not model at all.
⇒ **The gate is a floor, not a sweep.** After changing a drift figure, grep manually for:
`drift is 0` · `drift is ZERO` · `drift.*zero` · `figure is zero` · `0 as of` · `0 differing`.


## 2026-08-15 — archived from `04-HANDOFF.md`: the (i)/(ii) closed-promotion evidence (moved on the 900-line budget when `--driver ki80ladder` landed)

Both items are CLOSED and PROMOTED. Preserved verbatim:

>    **(i) ✅ `counter_hunt.py` PROMOTED** (comment-only; the Electric correction), restore point
>    `restore/2026-08-15-pre-promotion-counterhunt-comment`, verified by driving `--build custom`.
>    **(ii) ✅✅ KI-79 FIXED, FAULT-PROVEN, AND PROMOTED** — `withdraw_from_box` no longer announces
>    an IDENTITY from `len(get_party())`; it verifies `(personality_value, species)` **and**
>    `contains_pokemon`, after a 2-frame yield, and prints a loud named failure instead of a green
>    lie. Permanent hook `POKEBOT_PCWITHDRAW_FAULT`. Restore point
>    `restore/2026-08-15-pre-promotion-ki79-pctrip`. ‼ **A byte-compare was NOT accepted as proof
>    for a BEHAVIOUR promotion** — a three-point A/B was: same command, **PASS before (hook
>    absent) → FAIL after (`‼ THE WITHDRAW DID NOT LAND`) → PASS after unfaulted**. Run 1 is
>    unrepeatable once the copy happens, so it was run and committed FIRST. Transcripts:
>    `tools/story-dev/evidence/2026-08-15-ki79-*`. Full detail: KI-79, `07-CHANGELOG.md`,
>    `custom-pokebot/DIVERGENCE-LOG.md`, and `06-DECISIONS-LOG.md` for the rulings.


## 2026-08-15 — archived from `04-HANDOFF.md`: the DOC CONSISTENCY LAYER origin section (moved on the 900-line budget)

The directive itself lives in `CLAUDE.md`; this was the handoff's narrative copy of it.

## 🛡 NEW SINCE THEN (2026-08-14): THE DOC CONSISTENCY LAYER — read `CLAUDE.md`'s new directive before editing any doc

**The suite is 24 gates today** (this line said 18 when `audit_doc_consistency.py` was new, then 21; `repro_box_counter_move_test.py`, `repro_pid_identity_key.py`, `audit_encoding.py` and `repro_party_accounting.py` all joined on 2026-08-14 — ‼ **`run_gates.py` is authoritative and PRINTS the count, this prose is not**). **`audit_doc_consistency.py` is NEW** — it mechanically forbids the docs
contradicting themselves or the code (gate/drift/ladder counts, queue-vs-headline driver
contradictions, cited-artifact existence; `--self-test` proves it fires). **`CLAUDE.md` now carries
the DOC CONSISTENCY LAYER directive**: pairs P1-P4 that must move together in the same commit
(banner↔queue, KI header↔body, STATE↔changelog, README↔files), Tier 1 = one independent agent per
completed item's doc diff, Tier 2 = a cold-start agent at session end — both wired into `/wrapup`
and `/checkpoint`. ‼ **Born from measurement, not caution:** two audits found ~26 instances of
stale-text-beside-correct-text, including a TRIAGE INDEX blessing a five-chapters-stale entry, an
archive move done BACKWARDS (the refuted text stayed, the correction left — KI-39), `Expect:`
lines attached to the wrong commands in THIS file, and an R6 flag gate that could not see FIVE of
the sixteen flags it existed to police (all registered now, 16/16).



## 2026-08-15 — archived from `04-HANDOFF.md`: the ROOM 9 summary in full (compressed in place on the 900-line budget)

## ✅ ROOM 9 — ARCHIE, KYOGRE, THE ATOLL ESCAPE (driven 2026-08-14) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md`

Moved for the R3 budget once the live queue became the PC/PARTY arc. ‼ **Keep only what later
work leans on:** `--driver ch20room9` PASSED twice of three runs — the cavern is driven END TO END,
Kyogre awakened, graded on **`VAR_ROUTE128_STATE == 2`** (never the Kyogre flag, which is set
BEFORE the forced warp), and the atoll escape executed (**south to `(38,23)`, Surf onto
`(38,24)`** — the landing tile has ZERO surfable neighbours, so a naive Surf reads as a HUNG LEG).
⚠ **The Archie fight is the chain's one stochastic element — 2W/1L measured**, and a LOST run prints
**no RESULT and cannot** (the whiteout drops to Manual and the generator is abandoned), which is why
the driver logs a `PRE-ARCHIE PARTY` HP line as the loss's attribution record. ⇒ the chapter must
carry a **whiteout-retry policy** and **pre-boss readiness**. ✅ The previously decomp-only claim
that the cutscene releases the player facing north is now **MEASURED (`'Up'`, twice)**.
‼ Two design rules from this room, both reusable: **release is gated on a VAR, never on "looks
controllable"** (the first `releaseall` fires while a second cutscene is still queued), and the
scene-riding loop presses **A only when a text printer is waiting, B otherwise** — A beside an NPC
STARTS a conversation (`08-MISTAKES.md`, the museum-greeter rule).


## 2026-08-16 — archived from `04-HANDOFF.md`: the ROOMS 6/3 and ROOMS 1/2 summaries, merged in place on the 900-line budget

## ✅ ROOMS 6 AND 3 (driven 2026-08-13) — BANNERS MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-15)

Both DRIVEN AND PASSING; ⛔ **do not rebuild them.** Moved on the line budget when (P4) Stage 1
landed. ‼ **Keep only the two reusable rules:** Room 6 — *assert the OUTCOME, not the position you
expected* (a strict positional assert would have FAILED a perfect crossing); Room 3 — *the
instrument was wrong, not the claim* (a discriminator counted battles RUN-WIDE and printed a false
REFUTED over data that CONFIRMED the single-DOUBLE-battle claim). ⚠ Room 6's arrow-warp
derived-direction branch is still UNEXECUTED.
## ✅ ROOMS 1 AND 2 (driven 2026-08-13) — BANNER MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-15)

Both DRIVEN AND PASSING; ⛔ do not rebuild. ‼ **Keep only:** *copy upstream's ROUTE, never its
CONTROL FLOW* (our pushes go through the bounded `strength_push`, verified by `local_id`), and
**`FLAG_SYS_USE_STRENGTH` is cleared on EVERY WARP** — the code was always safe, the COMMENTS
were wrong. KI-77's despawn window is derived (20x17) and has since predicted a live dump exactly.


## 2026-08-16 — archived from `04-HANDOFF.md`: the PATHFINDER + §Ch20 SCOPING BACKGROUND section in full

## PATHFINDER + §Ch20 SCOPING BACKGROUND — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-15)

Moved on the R3 line budget when (P4) Stage 2 landed. ‼ **Keep only these, which later work
leans on:** (1) **KI-59** (the pathfinder's inverted `Impassable *` handling) is **FIXED, PROVEN
and GATED** (`repro_impassable_dirs.py`) — and its headline was wrong in FOUR documents: it is
**NOT** armed in the Seafloor Cavern (all 115 cavern tiles are `collision=1`, so ZERO reach the
handler); game-wide **401 of 2,658 such tiles are live**, chiefly the Regi tombs (144), Shoal
Cave (98) and Victory Road (58). (2) §Ch20's spec corrected our own docs: **ROCK SMASH is
mandatory**, the trigger tile is **`(17,42)` not `(16,42)`**, and the chapter grades on
**`VAR_ROUTE128_STATE == 2`**, never the Kyogre flag (which is set BEFORE a forced warp).
(3) **KI-74/75/76** were filed there; KI-76's safety half is fixed and fault-tested, its
**correctness half is OPEN**.
⇒ ✅ **ALL NINE ROOMS ARE DRIVEN — the cavern is END TO END (2026-08-14). ⛔ DO NOT REBUILD ANY.**



## 2026-08-16 — archived from `04-HANDOFF.md`: the KI-80 decoupling HOW-TO, in full (the work is now DONE)

Kept verbatim because it contains the measured proof that the three-arm suite alone would have
blessed the naive edit, and the arm-4 fixture arithmetic that took three attempts to get right.

>    *(Superseded instruction, kept so nobody re-does it:)*
>    `story_mode.py:1899-1901` — split the two meanings so the ladder is gated on *"is this fight
>    hopeless"* (which `_boss_plan_is_hopeless` already answers alone), not on whether a patch
>    happens to be configured. ⛔ **Before touching it, run the BEFORE command below and confirm it
>    still PASSes**; then make the change; then run the SAME command with `POKEBOT_KI80_DECOUPLED=1`
>    and require it to go **FAIL → PASS**. ⛔ `repro_boss_grass_gate.py` (suite #24) is DESIGNED to
>    SELF-RETIRE when the coupling goes — it stops enforcing and says so. That is success, not a
>    regression. ⛔⛔ **AND READ KI-80's "TWO THINGS THE REPRO DRIVER CANNOT SEE" BULLET FIRST —
>    THE NAIVE EDIT CAUSES KI-23's MIRROR REGRESSION AND `ki80ladder` WOULD STILL GO GREEN.**
>    `grass_is_fodder` has a SECOND use site (`:1932`), and `:1925 boss_mode = True` sits on the
>    NOT-hopeless path where `:1937` reads it — so the naive edit silently disables grass
>    escalation for every boss that has a strong patch AND an answer. Arms 1-3 return at `:1924`
>    and never reach `:1925`. ✅ **ARM 4 IS ALREADY BUILT FOR EXACTLY THIS — RUN IT BEFORE AND
>    AFTER:** `POKEBOT_KI80_ARM4=1 … story_harness.py fortree_gym_wedge.ss1 --driver ki80ladder`
>    (PASS today; and ⛔ **MEASURED 2026-08-16, not predicted:** against the actual naive edit it
>    printed `ARM4 OUTCOME=BOSS_TRAINING_MODE` + `ACCEPTANCE: FAIL` **while the three-arm run under
>    `POKEBOT_KI80_DECOUPLED=1` went `ACCEPTANCE: PASS`** — i.e. the 3-arm test alone WOULD HAVE
>    BLESSED THE REGRESSION. ‼ Keep `boss_mode = True` (`:1925`) behind `grass_is_fodder`).
>    ⛔ Its grass map is **VICTORY_ROAD_1F**, not Route 119 — Route 119's `wild_max` 27 cannot flip
>    `grass_is_fodder` at that save's `team_max` 39, which made the first prescription VACUOUS.
>    ⚠ KI-23's own entry warns about the mirror regression.
>    ⛔ The existing `repro_boss_grass_gate.py` is the STRUCTURAL AST gate and is NOT this driver —
>    it forbids the edit; the driver proves the branch. Both are needed.


## 2026-08-16 — archived from `03-PUNCH-LIST.md`: the FULL `#24-teachmsgstall` entry (344 lines), verbatim

Moved on the 3600-line budget, which the file had reached. ⛔ NOTHING WAS DELETED — the item's
live status (shipped, kept, reopened for lack of measurable effect) stays in the punch list; this
is the investigation behind it: the decomp trace of the one-frame `Task_ReplaceMoveYesNo` window,
the A/B that proved the fix, and the batch statistics that reopened it.

- [x] `#24-teachmsgstall` — ⚠ **FIX SHIPPED 2026-08-11 AND KEPT — BUT REOPENED THE SAME DAY: the batch showed NO production effect** (success 80.9% vs 90.5% pre-fix; the new exit fired ZERO times in 85 teaches — another path to `exhausted` exists; see the REOPENED entry at the top of this file). The fix closes a real one-frame hole and costs nothing, so it stays. Headline was ✅ **DONE … GATE GREEN** — corrected 2026-08-13: the headline carries the caveat.

      **THE CAUSE — a ONE-FRAME detector window.** The post-select loop waited on
      `"Task_ReplaceMoveYesNo" in t and "Task_PrintAndWaitForText" not in t`. Frame trace
      (`TEACH_TRACE=1`, `magma_door.ss1`, HM02 → Swellow):
      ```
      f3232735  tasks=['Task_ReplaceMoveYesNo']              <- the ONLY frame it is visible
      f3232736  tasks=['Task_HandleReplaceMoveYesNoInput']   <- gone, and it never comes back
      ```
      `pret/pokeemerald src/party_menu.c` — the task **retires itself on the frame it becomes
      answerable**, which is the same frame the condition first became true:
      `Task_ReplaceMoveYesNo` → `PartyMenuDisplayYesNoMenu(); func = Task_HandleReplaceMoveYesNoInput;`

      **WHY MISSING IT LOST THE TEACH.** The loop kept mashing A every 12 frames, and
      `Task_HandleStopLearningMoveYesNoInput` reads **A as YES = ABANDON** (decomp case 0 →
      "did not learn X" → `Task_ClosePartyMenuAfterText`). ‼ **The three "different" failure
      points are three phases of that one road** — summary handoff
      (`Task_ClosePartyMenuAndSetCB2`), "did not learn FLY" (`Task_ClosePartyMenuAfterText` +
      `Task_PrintAndWaitForText`), back in the bag (`Task_BagMenu_HandleInput`). The standing
      note "one broken menu step cannot move like that" was right — it was never one step.

      ‼ **AND WHY IT WAS DETERMINISTIC *AND* INTERMITTENT** (the property that made it
      unfalsifiable for four rounds): a `.ss1` replays identical frame timing, so a save that
      misses the window misses it every replay (0/3); live runs land on a random phase (38/42).

      **THE FIX** (`modules/story/early_game.py`): match BOTH task spellings (`_PROMPT_TASKS`,
      `_STOP_TASKS`); add an `already-advanced` exit that picks the flow up past the prompt
      (non-fatal, `_wait_for(..., required=False)`); press **B** at the stop-learning prompt
      *before* the blind-A fallback. The ride ladder had the identical exposure and is fixed
      the same way.

      **THE PROOF — live A/B, same save, same item, same target, one env var apart:**
      | arm | env | exit | result |
      |---|---|---|---|
      | OLD | `POKEBOT_TEACHWINDOW_A=1 TEACH_CANCEL_FORGET=1` | `ride:hard-cap stall_peak=61 frame=8999` | **`learned=False`** |
      | NEW | `TEACH_CANCEL_FORGET=1` | `ride:learned stall_peak=250 frame=896` | **`learned=True`** |
      The OLD arm's record is structurally identical to the 2026-08-10 production failure.

      ‼ **THE OLD "CHEAP REPRO" IS DEAD — do not chase it.** `saves/magma_door.ss1` is
      re-captured by `--driver magmatravel` on every success, and a chapter run at 22:05 on
      2026-08-10 overwrote the save the 21:27/21:34 failures were measured on. Both documented
      arms now PASS on it. Use the injections instead.

      **New test:** `repro_teach_prompt_window.py` (26 checks, no emulator; fault-injected to
      3 red, restored green). Gate: **12 of 12 PASS**.

      ✅ **PROMOTED 2026-08-11, user-approved.** Verified DRIVEN in `custom-pokebot` as the
      same fault-injected A/B (OLD `ride:hard-cap f8999 learned=False` / NEW `ride:learned f896
      learned=True`) — **frame-for-frame identical to the sandbox arms**. Source drift: **ZERO**.
      `repro_teach_prompt_window.py` also passes with `REPRO_BUILD=custom`. See
      `custom-pokebot/DIVERGENCE-LOG.md` for what is still outstanding (no production batch has
      run with this fix in, so do NOT quote an outcome number for it yet).

      HISTORY — **PRIORITY RAISED 2026-08-10: THIS IS NOW THE PROJECT'S TOP
      BLOCKER.** It stops `#24-strength`, which stops `#24-magmahideout` increment 3, which is
      all of the new story content. Its old note ("LOW priority — zero run-ending events") was
      true when the only teaches were opportunistic; it is false now that a chapter REQUIRES one.

      ✅ **A MUCH CHEAPER REPRO THAN THE 19,000-FRAME FIXTURE — use this one:**
      ```
      cd tools/story-dev
      PYTHONUTF8=1 TEACH_ITEM=HM04 py -3.12 story_harness.py magma_door.ss1 --driver teachfull --frames 400000 --profile tf-hm04
      PYTHONUTF8=1 TEACH_ITEM=HM02 py -3.12 story_harness.py magma_door.ss1 --driver teachfull --frames 400000 --profile tf-hm02
      ```
      Both fail deterministically from a committed save, ~3,000 frames of setup.

      ‼ **THREE NEW FACTS from a discriminating test (2026-08-10).** HM02/Fly to Swellow fails
      *identically* to HM04/Strength to Mightyena — same three `TEACH EXIT` records. So the wedge
      is **not item-specific**, **not target-specific** (slot 0 vs slot 2) and **not
      replace-slot-specific** (1 vs 0).
      ‼‼ **And the point of failure MOVES**: HM04 exhausts its 900-frame post-select window still
      in `Task_BagMenu_HandleInput`; HM02 in `['Task_ClosePartyMenuAfterText',
      'Task_PrintAndWaitForText']`. **A single broken menu step cannot do that.** That is evidence
      against the standing framing ("the replace prompt never appears" — one step too late) and
      for something generic starving the flow upstream. Start there, not at the replace prompt.

      HISTORY — **REPRODUCED 2026-08-09, LOCALLY, IN ~19,000 FRAMES. Fix not yet
      written.** Nine fixtures in, the failure is now a command anyone can run:
      ```
      cd tools/story-dev
      PYTHONUTF8=1 TEACH_ITEM=HM03 TEACH_INJECT=marshtomp TEACH_AFTER_TRAINER=1 \
        py -3.12 story_harness.py journey_r116_wedge.ss1 --driver teachfull \
        --frames 600000 --profile tf-trainer1
      ```
      **It is the production failure, not a lookalike.** Side by side with the batch:
      | | batch `20260807-160545` | this fixture |
      |---|---|---|
      | exit 1 | `reason=post-select-900-exhausted move=Surf replace_slot=1 frame=900` | **identical** |
      | exit 2 | `reason=ride:hard-cap stall_peak=82 post_select=exhausted frame=8999` | **identical** |
      | exit 3 | `reason=not-learned-after-ride:hard-cap stall_peak=82 frame=8999` | **identical** |
      | tasks | `['ListMenuDummyTask', 'Task_ContinueTaskAfterMessagePrints']` | **identical** |
      Only `slot` differs (2 here vs 4 there) — the target's party position, which is incidental.
      Live symptom: `state=BAG_MENU` frozen ~9,000 frames at `teach_hm_move @ early_game.py:4732`,
      `instr=BattleScript_PayDayMoneyAndPickUpItems`, ending in
      `BotModeError: Teach flow finished but Marshtomp does not know Surf`.

      ‼ **THE CONDITION IS "TEACH RIGHT AFTER A **WON** BATTLE", AND IT IS NOT ABOUT TRAINERS.**
      The fixture is named `AFTER_TRAINER` because it was built to test the trainer-tail
      hypothesis — and it reproduced the bug with **`trainers=0`**. Its guard said so out loud
      (*"NO TRAINER ENGAGED — this run is NOT evidence"*), which is the only reason the
      reproduction was not misattributed to trainers. What the patrol actually produced was **9
      won WILD battles**, and the tail on screen was `'STALLME gained a boosted 109 EXP.
      Points!'` — the post-battle EXP/money message chain.
      That fits every prior fixture exactly:
      | fixture | battle outcome before the teach | tail | result |
      |---|---|---|---|
      | 6 | **fled** (`'Got away safely'`) | no EXP/money chain | ✅ taught |
      | 7 | caught -> box | `BattleScript_SuccessBallThrowEnd` | ✅ taught |
      | 8 | caught -> party | `'Give a nickname to the captured NINCADA?'` | ✅ taught |
      | 9 | **won** | `BattleScript_PayDayMoneyAndPickUpItems` + `Task_ContinueTaskAfterMessagePrints` | ❌ **STALLS** |
      ⇒ **ROOT CAUSE LOCATED IN CODE (read 2026-08-09; fix NOT written, see why below).**
      `teach_hm_move` hands off through `normalize_to_overworld()` (`early_game.py:4466`), which
      declares the field settled when it is OVERWORLD + controllable + no script + **no menu
      task** — and "menu task" is this list (`early_game.py:452`):
      ```python
      _MENU_TASK_MARKERS = ("Task_ShowStartMenu", "ListMenuDummyTask", "Task_HandleChooseMonInput")
      ```
      **`Task_ContinueTaskAfterMessagePrints` is not in it.** So a post-battle message chain
      that is still printing does not block the hand-off; the teach then opens the BAG on top of
      it, `ListMenuDummyTask` joins the still-running message task — which is *exactly* the
      recorded signature `['ListMenuDummyTask', 'Task_ContinueTaskAfterMessagePrints']` — the bag
      list never advances, `post_select` exhausts at 900, the ride hard-caps at 8,999.
      **PROPOSED FIX (2026-08-09, morning):** treat "a message is still printing" as not-settled
      in `normalize_to_overworld`, so the existing B-cadence rides the chain out before anything
      opens the bag.
      ‼‼ **AND THAT FIX WAS REFUTED THE SAME DAY, BEFORE IT WAS WRITTEN.** A `HANDOFF-STATE` line
      was added to `--driver teachfull` to print the exact state at the instant the teach takes
      over, and run on a FAILING and a PASSING fixture:
      | field | FAILING (won battle) | PASSING (catch) |
      |---|---|---|
      | `controllable` | True | True |
      | `cb` | `ReturnFromBattleToOverworld` | `ReturnFromBattleToOverworld` |
      | tasks | `['Task_MuddySlope','Task_RunPerStepCallback','Task_RunTimeBasedEvents','Task_WeatherMain']` | **identical** |
      | `message_task_active` | **False** | **False** |
      | `instr` | **`BattleScript_PayDayMoneyAndPickUpItems`** | `BattleScript_SuccessBallThrowEnd` |
      **`Task_ContinueTaskAfterMessagePrints` is NOT running at hand-off** — it only appears
      AFTER the bag opens. Gating `normalize_to_overworld` on it would have been **INERT.** A
      `repro_teach_message_gate.py` asserting that gate was written, committed RED, and then
      **deleted**, because a committed test for a refuted design misleads the next agent more
      than no test at all.
      ⇒ At first reading, the only field that differed was `instr` — so the next candidate gate was
      "wait for the parked battle script". ‼ **THAT IS REFUTED TOO, measured the same hour:** load
      six perfectly ordinary controllable overworld saves nowhere near a teach
      (`post_winona`, `norman_done`, `lavaridge`, `mauville_prewattson`, `rocksmash_taught`,
      `slateport`), run 120 frames, and **6 of 6** report
      `cb=ReturnFromBattleToOverworld instr=BattleScript_PayDayMoneyAndPickUpItems`. `instr` is
      **residue of the last battle script**, not "currently executing". Gating on it would block
      every teach forever.
      ⇒ **SO THE HAND-OFF STATE DOES NOT DISTINGUISH THE TWO RUNS AT ALL.** Nor do the teach's own
      parameters: failing and passing runs share `move=Surf slot=2 replace_slot=1` and the same
      target with the same four moves.

      ‼ **WHERE THE DIFFERENCE ACTUALLY SHOWS UP — start here next time.** It is downstream of the
      bag, in the `TEACH EXIT` records themselves:
      | | FAILING (`tf-premise`) | PASSING (`tf-premise-pass`) |
      |---|---|---|
      | `post_select` | **`exhausted`** — the 900-frame window expires without the replace prompt ever appearing | **`replace-prompt`** |
      | `stall_peak` | **82** | 171 |
      | outcome | `ride:hard-cap` at 8,999 | `ride:learned` at **463** |
      `stall_peak=82` against a 900 threshold means the failing run is **CYCLING, not frozen** —
      something is changing every ~82 frames while the flow never reaches the replace prompt.
      **NEXT STEP: diff the two runs frame-by-frame from the moment the bag opens.** Both logs are
      on disk (`profiles/tf-premise*/debug-logs/`), the fixtures are ~19,000 frames, and the two
      differ in exactly one input — how the previous battle ended.
      ‼ **Two things flagged when the (now refuted) fix was proposed, kept because risk (2)
      still applies to ANY fix here:**
      (1) whether `Task_ContinueTaskAfterMessagePrints` is ever *permanently* resident — if so
      `normalize_to_overworld` would burn its 3,600-frame bound on every call (bounded, so a
      delay rather than a hang, but a real cost); (2) that the settle still fires promptly on the
      paths that work today — fixtures 6/7/8 are the controls and all three must stay green.
      ✅ **RISK (1) MEASURED 2026-08-09 — moot for the refuted fix, kept as data.** Across **386** captured states
      (every `saves/*.ss1` plus every `saves/stalls/*.ss1`, each run 30 frames after load) the
      task is resident in **5**, and in **0 of them** is the game a settled controllable
      overworld. All five are teach-stall captures — `hmteach-new-f17130`, `repro-teach2-f2706`,
      `repro-teachab1-f2706`, `tf-trainer1-f19130`, `tf-trainer2-f19130` — i.e. it shows up in
      exactly this bug and nowhere else in the corpus.
      ‼ Caveat, so this is not over-read: those are captured SNAPSHOTS (anchors and stall
      captures), not a uniform sample of gameplay frames, so this bounds residency in the states
      we keep, not in all play. Risk (2) is untouched by it and still needs the three controls.
      ‼ Incidentally: `tf-trainer2` stalled at the **same frame (f19130)** as `tf-trainer1` — the
      reproduction is not merely repeatable, it is frame-identical.
      ‼ **Not verified, and NOT written today on purpose:** a batch was mid-flight and restarted
      lanes re-import `sandbox-pokebot/` from disk, so touching production mid-batch would have
      corrupted the measurement. Prove it with a fault-inject A/B against the fixture above,
      which now costs ~19,000 frames.
      ‼ A stall state was auto-saved at the wedge: **`saves/stalls/tf-trainer1-f19130.ss1`** —
      the first HM-bearing one, and (per the `.ss1` finding below) it should reload wedged.

      HISTORY — **2026-08-09: FOUR hypotheses eliminated, and ONE RECORDED RESULT WAS WRONG.**

      ‼‼ **CORRECTION — attempt 6 was NOT "a broken probe with no evidence".** It was recorded
      as *"the spin produced no encounter (`battle_seen=False`), fix the spin"*. Its own log
      (`tools/story-dev/harness_afterbattle.log`) says otherwise: **197
      `CONTROLLER -> BattleListener.fight` transitions**, Marshtomp's EXP climbing 21760 ->
      24240. Encounters were never missing. **The DETECTOR was blind:** the stop-condition
      polled `battle_is_active()` from inside `_story_spin`, and the mode's generator is not
      pumped while `BattleListener` owns the controller stack — so the callback only ran on
      ~2,466 of ~44,000 frames, every one of them a frame with no battle active. It could not
      have returned True. **FIXED:** count in `on_battle_started` (the framework calls it on the
      mode instance while the generator is suspended). A/B on the identical fixture:
      **old `battle_seen=False` after 2,466 pumps -> new `battles=1` after 7 pumps.**
      And attempt 6's real result, read correctly, is a **negative for the hypothesis**: it
      taught SUCCESSFULLY (`learned=True`) with a battle tail resident
      (`cb=ReturnFromBattleToOverworld`, `bt='Got away safely'`).

      | # | hypothesis / fixture | result |
      |---|---|---|
      | 6 | teach with a **wild BATTLE tail** resident | ❌ **RULED OUT** — succeeds, twice (attempt 6 re-read, plus the fixed-detector rerun) |
      | 7 | teach with a **CATCH tail** resident (`TEACH_AFTER_CATCH=1`, new) | ❌ **RULED OUT for the box-transfer tail** — `instr=BattleScript_SuccessBallThrowEnd`, `cb=ReturnFromBattleToOverworld`, `bt='TAILLOW was transferred to SOMEONE'S PC'`, `Task_HandleReplaceMoveYesNoInput` — teach SUCCEEDS |

      ‼‼ **FIXTURE 8 — THE EXACT PRODUCTION SHAPE — ALSO SUCCEEDS. The leading hypothesis is
      DEAD.** Fixture 7's catch went to the BOX (party was already 6), so it only tested the
      PC-transfer tail. Fixture 8 fixed that (arm catching only AFTER the walk — a wild caught
      in transit was filling the party) and produced a **PARTY catch, 5 -> 6**, teaching 8 pumps
      later with the production dialogue verbatim on screen:
      ```
      f9242 st=PARTY_MENU  instr=BattleScript_SuccessBallThrowEnd cb=ReturnFromBattleToOverworld
            ml=AskWhetherToLearn tasks=['Task_HandleReplaceMoveYesNoInput']
            bt='Give a nickname to the captured NINCADA?'
      f9435 st=POKEMON_SUMMARY_SCREEN ... tasks=['Task_HandleReplaceMoveInput']
            bt='Give a nickname to the captured NINCADA?'
      ```
      `learned=True`, Mud Shot replaced by Surf. **So "the teach runs while the post-catch
      nickname prompt is still resident" — the hypothesis this item has rested on since
      2026-08-08 — does NOT reproduce the stall.** Five hypotheses are now eliminated.

      ‼‼ **THE PRODUCTION CONTEXT, READ FROM THE BATCH'S OWN DEBUG LOGS 2026-08-09 — and it is
      a tail NO fixture has used.** (`x4-runs/20260807-160545`, 33 logs / 309,276 lines searched;
      positive control: `TEACH EXIT` x63 and `TEACH OK` x38 are visible in that sweep.) A
      failing teach dumps this:
      ```
      message='Story: teaching Surf to Swampert...'   controllable=False
      battle: active=False  callback=ReturnFromBattleToOverworld
              instr=BattleScript_PayDayMoneyAndPickUpItems
      battle_text='H2 got $3100 for winning!'   learn_state=LearnMoveState.DialogueNotActive
      tasks=['Task_ContinueTaskAfterMessagePrints', 'ListMenuDummyTask']
      TEACH EXIT reason=post-select-900-exhausted ... frame=900   (then ride:hard-cap at 8999)
      ```
      **`'... got $3100 for winning!'` is a TRAINER prize-money message.** Every fixture so far
      (6, 7, 8) used **WILD** battles, whose tails complete — fixture 6's read `'Got away
      safely'`, fixture 8's `'Give a nickname to the captured NINCADA?'`, and both taught fine.
      ‼ That single difference plausibly explains all five dead hypotheses at once: the variable
      was never the party, the item, the moveset or the catch — it is **which battle tail**.
      ‼ **Independent corroboration from today's UNRELATED runs:** `--driver anchorcapture` and
      `--driver groundsweep` both logged the same stuck signature after trainer fights —
      `STUCK-OW cb=ReturnFromBattleToOverworld instr=BattleScript_PayDayMoneyAndPickUpItems
      bt='NICK got $468 for winning!'` — with no teach anywhere in sight. So this tail appears to
      linger **generally**, not only under the teach. That makes it a candidate cause for
      unrelated travel failures too (see KI-48).
      **NEXT FIXTURE (spec):** teach immediately after a **TRAINER** battle. ‼ Attempts 3-5 had
      the right instinct here and failed on execution — they tried to win a GYM first and wedged
      three times; **any trainer battle is enough, do not return to the gym route.**
      ‼‼ **AN ASSUMPTION THIS ITEM WAS BUILT ON IS FALSE — MEASURED 2026-08-09.** The item
      records that *"a tail is RUNTIME state and cannot be loaded from a save"*, and that is why
      attempts 3-5 went down the fight-Norman-first road that wedged in the gym three times.
      True of a `.sav`; **FALSE of a `.ss1`, which is a full machine snapshot.** All **six**
      stall states in `saves/stalls/` reload — after 66 frames of running — with the tail intact:
      ```
      anchorcap-f1004.ss1  cb=ReturnFromBattleToOverworld  instr=BattleScript_PayDayMoneyAndPickUpItems
      anchorcap-f2421.ss1  cb=ReturnFromBattleToOverworld  instr=BattleScript_PayDayMoneyAndPickUpItems
      ... 6 of 6 identical
      ```
      ⇒ **The fixture does not have to fight anything.** Recipe: run any driver from a
      **badge-5+** save (so the bag holds HM03) through a TRAINER fight; the harness auto-saves
      `saves/stalls/<profile>-f<frame>.ss1` at the stall; then run `--driver teachfull` FROM that
      state. The tail is already resident on load, so the teach starts in the exact production
      condition in seconds. ‼ The six states available today are early-game (badges 1-2, **no HMs
      in the bag**), so they cannot drive a Surf teach — one HM-bearing stall state is all this
      item still needs.

      ‼ **The task sets independently say the stall is EARLIER than anyone has been probing.** Compare the failing batch signature with what every successful fixture shows:
      | | tasks on screen |
      |---|---|
      | batch failures (9 of 9, `20260807-160545`) | `['ListMenuDummyTask', 'Task_ContinueTaskAfterMessagePrints']` |
      | every successful fixture, incl. 8 | `['Task_HandleReplaceMoveYesNoInput']` -> `['Task_HandleReplaceMoveInput']` |
      `ListMenuDummyTask` is a **LIST MENU** — the BAG — plus an unfinished message. The
      successful runs are stuck-free at the *replace prompt*, which is **after** item selection.
      ⇒ **The failure is very likely in the BAG/item-selection step, before the party menu is
      ever reached**, not in the replace dialogue the last three fixtures have been recreating.
      ‼ This is an inference from task NAMES and is not yet verified — treat it as the next
      thing to measure, not as a finding.

      ‼ **A fixture guard earned its keep immediately.** Run 1 of `TEACH_AFTER_CATCH` spun
      through **125 battles and caught nothing** because `boxwithdraw.ss1`'s bag holds **zero
      Poké Balls** (measured). The `caught=False` guard reported *"this run is NOT evidence"*
      instead of producing a fourth confident non-result. Ball supply is now checked up front.

      ‼ **Cross-map fixture travel failed FOUR times today** (Slateport->Mauville, ROUTE116
      intra-map, Fortree->ROUTE119, Mt. Pyre->ROUTE119). Prefer a save that is ALREADY on a map
      with grass — `journey_r116_wedge.ss1` + `TEACH_GRASS=ROUTE116:11,7` works and is what
      produced fixture 7. See KI-48/KI-49.

      HISTORY — **2026-08-08: TWO HYPOTHESES ELIMINATED by direct repro.**
      New fixture: `--driver teachfull TEACH_INJECT=marshtomp [TEACH_INJECT_SLOT=n]` writes the
      batch's exact failing party shape into a live save.
      | hypothesis | result |
      |---|---|
      | the MOVESET (`Take Down/Mud Shot/Rock Smash/Muddy Water`, an HM in the set) | ❌ **RULED OUT** — teach SUCCEEDS, 457 frames, replaced Mud Shot |
      | a FULL party with the target at **slot 4** (most batch records read `slot=4`) | ❌ **RULED OUT** — succeeds, 463 frames |
      | HM03/Surf specifically | ❌ ruled out by both runs above |
      ‼ **So it is not the party and not the item — it is the CALLER CONTEXT.** In production the
      teach runs immediately after `ensure_hm_learner`, which the function's own header warns
      *"returns the instant the catch registers while 'Give a nickname to the captured X?' is
      still on screen"*. `normalize_to_overworld()` is supposed to absorb that. The stuck task
      set — `['ListMenuDummyTask', 'Task_ContinueTaskAfterMessagePrints']` — is a LIST MENU plus
      an unfinished message, which fits a lingering post-catch dialogue far better than anything
      about the moveset.
      ‼‼ **THE CALLER CONTEXT IS IDENTIFIED: THE NORMAN BATTLE TAIL.** Segment 12c runs
      `do_petalburg_gym()` and then IMMEDIATELY `ensure_hm_learner(HM03)` → `teach_hm_move`
      (`story_mode.py:3137-3163`). `teach_hm_move`'s own comment already recorded this and I
      under-weighted it: *"all 7 start with the NORMAN BATTLE TAIL still resident
      (`callback=ReturnFromBattleToOverworld`), which stretches the dialogue chain past 3,000
      frames."* The two eliminations above converge on it by exclusion.
      ‼ **A battle tail is RUNTIME state — it cannot be loaded from a save.** The fight must
      actually happen inside the probe, which is why every clean-overworld repro succeeds.

      ‼‼ **FIVE FIXTURE ATTEMPTS, NONE REPRODUCED. Read this before trying a sixth.**
      Every attempt so far has failed to even REACH the teach with a battle tail resident:
      | # | fixture | outcome |
      |---|---|---|
      | 1 | clean overworld, failing moveset | teach SUCCEEDS 457f — moveset ruled out |
      | 2 | clean overworld, full party, target at slot 4 | SUCCEEDS 463f — slot ruled out |
      | 3 | `TEACH_AFTER_GYM` on `prenorman_fodder_grind` | died to a trainer HP refusal (driver fixed) |
      | 4 | same, healed party | wedged IN the gym at f61848 — teach never reached |
      | 5 | same, Marshtomp L45 injected to win | wedged at f56868 — teach never reached |
      | 6 | `TEACH_AFTER_BATTLE=1` (any battle, not the gym) | `battle_seen=False` at 2,466f — **the spin never triggered a battle**, so the probe is broken, NOT evidence |
      ‼ **Attempt 6 is the right IDEA and the cheapest path** — the hypothesis is only that a
      battle tail (`ReturnFromBattleToOverworld`) is resident, which needs ANY battle, not
      Norman's. It failed because `_story_spin` returned without producing an encounter from
      `boxwithdraw.ss1`. **Fix the spin (verified grass tile + a longer budget, the way
      `--driver boxcatch` does it) and attempt 6 should reproduce in minutes.**
      ‼ Do NOT go back to the gym route — three attempts, zero teaches reached.

      **PROBE SCAFFOLD (all wired, only the spin is wrong):** `--driver teachfull TEACH_AFTER_GYM=petalburg
      TEACH_ITEM=HM03` on `prenorman_fodder_grind.ss1` fights Norman, then teaches with no settle.
      HM03 is GIVEN for beating Norman, so the bag control doubles as proof the gym leg completed.
      ‼ **WHAT IT STILL NEEDS: a party that can actually BEAT Norman.**
      That save is a grind save (Whismur L18 / Ninjask L27 / Shedinja L25 / Mightyena L30 /
      Combusken L36 against Norman's L27-31); run 1 died to a trainer-battle HP refusal (fixed —
      the driver now uses `LevelUpTravelBattleStrategy` for trainers, as `boxwithdraw` already
      did) and run 2 wedged inside the gym at f61848 without ever reaching the teach.
      **Inject a party that wins the fight, or capture a save at the moment Norman faints.**
      Everything downstream of that is already wired.



## 2026-08-16 — archived from `04-HANDOFF.md`: the FULL (P6) TRAINING-AREA MAPS block, verbatim

(P6) is CLOSED: its investigation became KI-80, which was fixed and promoted to both forks on
2026-08-16. Archived because the block had begun COMMANDING the decoupling as live work 58 lines
below a banner marking it done — a cold-start audit called that the most expensive defect in the
file, since NEXT ACTIONS is the block an agent executes from. Its three still-live rules were
kept in place; everything else is here.

>    ⛔⛔ **(P6) TRAINING-AREA MAPS — ‼ THIS ITEM WAS WRONG ON BOTH ITS EXAMPLES. DO NOT ACT ON
>    THE OLD WORDING; READ KI-80 FIRST.** Investigated 2026-08-15; the investigation is the
>    deliverable, and it is now GATED (`repro_boss_grass_gate.py`, suite #24).
>    * ⛔ **"Winona has no patch configured, so the relocation machinery is skipped for her"** — the
>      skip is REAL but giving her one is a **REGRESSION**. `grass_is_fodder`
>      (`story_mode.py:1899`) is `("grass" not in cfg) or (wild_max + 8 < team_max)`, and `:1901`
>      makes it a **co-gate** (precisely: `if grass_is_fodder and boss_teaches:` inside `if losses >= 2:`) on `_boss_plan_is_hopeless` **and** `_counter_ladder`, which are its ONLY call sites. Her
>      missing key is the only reason KI-23's counter machinery can fire for her. Add the Route 119
>      patch (band 24-27) and for any team at **L30-35** — her own band is (29,33) — `27+8=35` is
>      NOT `< team_max`, so the counter ladder is **SKIPPED**, silently, behind a healthy-looking
>      `"training harder before re-attempting"` line. That is the path KI-23 measured failing
>      **198 attempts / 41 losses / 41 whiteouts**.
>    * ⛔ **"Norman's patch is L3-5 against a band of L27-31"** — TRUE, and **DELIBERATE**.
>      `story_mode.py:1981-1991` names Norman as the pathological case *by design*: the local patch
>      is the FODDER TRIGGER that fires the relocation, and `training_areas.py` records that
>      ROUTE111 is **the only training relocation this bot has ever performed**, at a measured
>      70-83% Balance→Feather success. "Correcting" his patch would DISABLE that.
>    * ⛔ **Do NOT add a row to `TRAINING_GRASS`** either: `best_training_area` ranks ONE GLOBAL
>      table by `(abs(hi - team_level), -hi)`, so a new row near L29-33 changes the pick for every
>      other caller too, including `counter_hunt.py:647`'s candidate picker for EVERY boss. That is
>      the measured Shoal Cave incident (`08-MISTAKES.md`), restated.


## 2026-08-16 — archived from `04-HANDOFF.md`: the ROOM 9 and ROOMS 1/2/6/3 summaries, merged in place on the 900-line budget

## ✅ ROOM 9 — ARCHIE, KYOGRE, THE ATOLL ESCAPE (driven 2026-08-14) — DETAIL in `28-HANDOFF-ARCHIVE.md`

‼ **Keep only what later work leans on:** `--driver ch20room9` PASSED 2 of 3 — the cavern is driven
END TO END, graded on **`VAR_ROUTE128_STATE == 2`** (never the Kyogre flag, set BEFORE the forced
warp); the atoll escape is **south to `(38,23)`, then Surf onto `(38,24)`** (the landing tile has
ZERO surfable neighbours, so a naive Surf reads as a HUNG LEG). ⚠ **The Archie fight is the chain's
one stochastic element — 2W/1L**, and a LOST run prints nothing (whiteout → Manual → KI-71 abandons
the generator) ⇒ the chapter needs a **whiteout-retry policy** and **pre-boss readiness**.
‼ Two reusable rules: **release is gated on a VAR, never on "looks controllable"**; and press
**A only when a text printer is waiting, B otherwise** (A beside an NPC starts a conversation —
the museum-greeter rule, `08-MISTAKES.md`).
## ✅ ROOM 8 (driven 2026-08-14) — DETAIL MOVED to `28-HANDOFF-ARCHIVE.md` (same day, when the PC/PARTY queue replaced the Ch20 queue)

Moved for the R3 budget. ‼ **Keep only what later work leans on:** `--driver ch20room8` PASSED
twice (clean 9/9, plus a FAULT run that EXERCISED the jam-recovery handler — `recovered=True`),
and ⛔ **step 9 faces LEFT, never UP** (`(5,3)` permanently seals the exit). Two adversarial
passes preceded the drive and BOTH changed something: an offline refutation of the 9-push table
(verdict SURVIVES) supplied the template data that turned KI-77's window into the exact
prediction *"8 of 12 boulders visible at arrival"*, which the live run matched exactly; and a diff
review caught the recovery handler HARDCODING an arrow-warp direction instead of deriving it from
the live tile. ⇒ *the happy path cannot exercise an error path — fault-inject it on purpose.*
## 🛡 THE DOC CONSISTENCY LAYER (2026-08-14) — the DIRECTIVE now lives in `CLAUDE.md`; read it before editing any doc

**Gate suite: `run_gates.py` PRINTS the count and is authoritative — this prose is not.**
`audit_doc_consistency.py` forbids the docs contradicting themselves or the code; `CLAUDE.md`
carries pairs **P1-P4** (banner↔queue, KI header↔body, STATE↔changelog, README↔files), **Tier 1**
(an independent agent per completed item's doc diff) and **Tier 2** (a cold-start agent at session
end). ⚠ **The gate is a FLOOR, not a sweep** — on 2026-08-15 it saw only 3 of 7 stale drift claims.
Origin detail: `28-HANDOFF-ARCHIVE.md`.

## ✅ ROOMS 1, 2, 6 AND 3 (driven 2026-08-13) — BANNERS in `28-HANDOFF-ARCHIVE.md`

All DRIVEN AND PASSING; ⛔ do not rebuild. ‼ **Four reusable rules:** *assert the OUTCOME, not the position
you expected* (Room 6); *the instrument was wrong, not the claim* (Room 3 — a discriminator counted
battles RUN-WIDE and printed a false REFUTED over data that CONFIRMED it); *copy upstream's ROUTE,
never its CONTROL FLOW* (Rooms 1/2 — pushes go through the bounded `strength_push`); and
**`FLAG_SYS_USE_STRENGTH` is cleared on EVERY WARP** — the code was safe, the COMMENTS were wrong.
⚠ Room 6's arrow-warp derived-direction branch is still UNEXECUTED; KI-77's despawn window (20x17)
has since predicted a live dump exactly.


---

# ARCHIVED 2026-08-17 — 04-HANDOFF NEXT ACTIONS items 2b-5 ("older framing")

Moved out of `04-HANDOFF.md` on the R3 900-line budget. The queue header had already labelled
these "older framing"; by 2026-08-17 every one was DONE or RETRACTED. Verbatim, unedited.

> 2b. **‼ THE NEXT BUILD IS NO LONGER BLOCKED THE WAY THE DOCS SAID.** §Ch20/§Ch21 need **Dive
>    USED**, and KI-63 is real (no party member learns it, party 6/6). But the thing four documents
>    called the gate — `POKEBOT_BOX_OVERFLOW_CATCH` being off and "one unhandled text box" away —
>    **is false and has been since 2026-08-07.** It defaults to ON; the text box needs no handling.
>    **Verify it yourself at `story_mode.py:2241-2243` before believing either version.**
>    **THE PLAN (measured against `modules/data`, detail in KI-54's new section):**
>    * **Spheal**, ~50% of the `SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM` LAND table at L26-32, catch rate
>      255, learns **Surf AND Dive**. Mossdeep → Route 125 → the entrance room is **one warp**.
>      ⚠ TIDE is the one risk: the high-tide maps have **no encounter header at all**, and which RTC
>      hours give low tide is **UNVERIFIED**. Tide-free fallback: **Marill on Route 120** (15%, L25-27).
>    * ⛔ **RETRACTED 2026-08-13 — THE DEPOSIT PATH NAMED BELOW CANNOT DO THIS JOB.** Superseded by
>      `ai-research-notes/2026-08-13-ki63-dive-learner-acquisition-plan.md`. Verified directly:
>      `withdraw_from_box` opens with `target = find_in_box(pids); if target is None: return`
>      (`modules/story/pc_trip.py:420-421`), so with nothing yet boxed **it returns having done nothing** — its
>      deposit block is only reachable as a side effect of withdrawing an already-boxed PID. And
>      `deposit_dead_weight_if_worth_it` **is** a standalone one-deposit primitive but is a **silent
>      no-op** behind `POKEBOT_PC_ROTATION` (`pc_trip.py:83`). ⇒ **A new narrow, ungated,
>      one-deposit function must be written.** ‼ Also: **deposit-first is the wrong ORDER** —
>      `ensure_hm_learner` checks for an existing learner *before* the party-full check, so try it
>      first and deposit only on that specific failure. (Still true from the old text: the victim is
>      **Skitty L17**, and Zigzagoon L15 is EXEMPT as sole Surf carrier — re-measured 2026-08-13.)
>      Superseded text: Freeing one slot reuses `withdraw_from_box`'s deposit block (~`modules/story/pc_trip.py:437-461`), which is live-proven and deposits exactly ONE mon.
>    * ⛔ **Do NOT fetch the Super Rod first** — Sharpedo/Wailmer are real, but it needs three missing
>      subsystems (no rod chapter, no fishing capability at all, and `_hm_hunting_grounds` reads
>      land encounters only) against one `TRAINING_GRASS` row.
>    * ✅ **THE TIDE IS NOT A BLOCKER (measured 2026-08-12).** The high-tide "maps" have no encounter
>      header and no warps — they only own a LAYOUT that gets borrowed onto map (24,46), and the
>      encounter table keys off map number, not layout. **The Spheal 50% table is live at BOTH
>      tides** (65 walkable encounter tiles at high, 332 at low). No tide handling needed.
>      **Surf is the only gate** and we have it: `MOSSDEEP_CITY → ROUTE125` routes in 119 waypoints,
>      Zigzagoon L15 knows Surf, and Route 125 → the entrance room is one warp.
>    * ‼ **BUT THE REAL GATE IS STILL THE FULL PARTY** — `ensure_hm_learner` raises when the party is
>      ≥6 **before** it ever looks for a hunting ground. Free the slot first; the ground is
>      necessary, not sufficient.
>    * ⚠ Two hazards recorded in KI-54 before anyone codes in that room: `MapLocation` always
>      resolves the **low-tide** layout for (24,46), so in-room planning at high tide plans against
>      the wrong map; and (20,30) counts as a south-arrow warp, so never spin on or below it.
> 3. ✅ **DONE 2026-08-13 — KI-59 IS FIXED (both halves) AND GATED as `repro_impassable_dirs.py`.**
>    A/B on `VICTORY_ROAD_1F`: exit 1 → exit 0, 29/29 mismatches → 0/29, and `calculate_path` went
>    from NO-PATH-from-every-direction to `OK len=1` on the legal approaches. `MOSSDEEP_CITY`
>    collateral control byte-identical. ✅ **PROMOTED 2026-08-14 — nothing is left on this item, and drift is ZERO.**
>    ⛔ **The next sentence is STALE** (it asked for a promotion that has since happened; its drift figure is
>    not restated because the doc gate scans for one and cannot tell a quotation from a claim):
>    *(stale)* The only thing left on this item is PROMOTION, which is the USER's call. The retraction that reprioritised it follows.
>    ⛔ **RETRACTED 2026-08-13, MEASURED — "Fix KI-59 before the cavern exists" was WRONG.** The 115
>    `Impassable *` tiles in the cavern are real, but **every one has `collision=1`** and
>    `map_path.py:128` is the **`elif` of `if tile.collision != 0:` (`:118`)** — so **none of them
>    reach the buggy branch**, and the prescribed A/B on `SEAFLOOR_CAVERN_ROOM1` would have measured
>    a **zero delta**. KI-59 does **not** gate §Ch20/§Ch21. It is REAL and live on **401 of 2,658**
>    such tiles game-wide (15.1%), chiefly the **REGI TOMBS (144)**, **SHOAL CAVE (98)** and
>    **VICTORY ROAD (58)** ⇒ it is a prerequisite of the **REGI ARC (item 4)**, not of the cavern.
>    Measured by `probe_impassable_dirs.py` (NEW), with a fresh-process reverse-order control against
>    KI-73 cache poisoning. Fix specified + hazards pre-checked in `#24-impassabledirs`.
>    Superseded text: Fix KI-59 before the cavern exists — it is armed there (115 `Impassable *` tiles across Rooms 1-9). A/B on `SEAFLOOR_CAVERN_ROOM1`.
> 4. ✅ **THE PROMOTION ALREADY HAPPENED** (2026-08-12, user-approved, driven on `--build custom`).
>    Do NOT ask for it again. The line below is superseded; only the battle-policy half is still
>    the user's call. Superseded text: Two things remain the USER's call: **promoting §Ch18 + §Ch19 to `custom-pokebot/`**, and the
>    **boss/status battle-policy** decision further down.
> 5. Before building anything, skim `08-MISTAKES.md`'s last entries — five were written today and
>    three of them are about tests or gates that were green while something was broken.

1. **✅ §Ch18 IS DONE (2026-08-12) — the Mind Badge is won and Segment 18 is wired into the ladder.**
   The ladder reached **19/24** with this item (current: **20 of 24 beats**, since §Ch19). Three drivers, all PASS:
   * `--driver mossdeeptravel` → Surf Lilycove → Mossdeep, enter the gym. Anchor
     `saves/in_mossdeep_gym.ss1`.
   * `--driver mossdeepgym` → solve the statue puzzle. `at_leaders=True at=(23,8) whiteouts=0`,
     117 steps in a single plan. Anchor `saves/at_mossdeep_leaders.ss1`.
   * `--driver mossdeepbadge` → the whole chapter. `badge=True at=(23,8) controllable=True
     whiteouts=0`, `BADGE07_GET` after 754 frames. Anchor **`saves/post_mossdeep_gym.ss1`**.

   ‼ **TWO PATHS REMAIN UNEXERCISED, and neither should be described as tested.** (a) The
   executor's own `_ride_out_interruption` branch logged **zero** times — the trainer battles that
   fired were handled by the standard `TrainerApproachListener` / `BattleListener`. (b) The **real
   whiteout path**: both runs had `whiteouts=0`, so the recovery is proven only by fault injection
   (`repro_gym_whiteout_guard.py`), never by a live loss.

   ‼ **WHAT ADVERSARIAL REVIEW CAUGHT THAT THE PASSING RUN COULD NOT.** `walk_to_the_leaders`
   checked the gym map only at entry and then reasoned in gym-local coordinates forever — a
   whiteout would have had it planning gym routes from Pokémon Center coordinates — and it raised
   `RuntimeError` where the chapter catches `BotModeError`, so the re-enter-and-re-solve recovery
   **could never have fired**. Both fixed. *A green happy-path run says nothing about error paths.*

   ‼ **AND §Ch18 WAS STRANDING THE RUN** — found later the same day, by the adversarial pass for
   §Ch19, *after* §Ch18 had been driven twice, committed and reported complete. It ended on
   `(23,8)`, part of an **eleven-tile island**; `calculate_path((23,8) → (7,35))` raises, and the
   only exit is the `(21,6)` **coord event** (invisible to any warp-graph solver). Fixed with
   `leave_the_gym()` — driven, now ends in `MOSSDEEP_CITY (38,10)` — and **the acceptance test now
   requires being out of the gym**, so the stranded version would fail. *This is KI-56's rule
   violated a second time in the session in which I re-read it.*


---

# ARCHIVED 2026-08-17 — punch-list item `#24-pcwithdraw-proof` (CLOSED 2026-08-07)

Moved out of `03-PUNCH-LIST.md` on the R3 3,600-line budget. Closed long before the move;
verbatim, unedited.

- [x] `#24-pcwithdraw-proof` — **PROVEN 2026-08-07. The withdraw half executes end to end.**
      New harness driver `--driver boxwithdraw` + fixture save `saves/boxwithdraw.ss1` (the end
      state of the proven box-catch run: party 6, box 2). Three consecutive runs, identical:
      ```
      Story: PC — depositing Skitty L17 to make room for Poochyena.
      Story: PC — withdrawing Poochyena from the box.
      Story: PC — Poochyena is in the party; party is now 6.
      [boxwithdraw] RESULT withdrew=True target=Poochyena party_before=6 party_after=6
                    box_before=2 box_after=2 deposited=True map=(0, 5)
      [boxwithdraw] AFTER usable=True second_heal_ok=True still_has_target=True party=6 box=2
      ```
      ‼ **It drives the PRODUCTION call site**, not `withdraw_from_box` directly: the probe sets
      `self._hunted_counter_pids` and calls `heal_in_pokemon_center`, which is the attribute and
      the piggyback the story bot actually uses (`higher_level_actions.py:218-232`). Calling the
      function directly would have proven the function works and NOT that the piggyback fires —
      and the piggyback is the half that was dead.
      ‼ **The no-op assertion matters as much as the positive one.** A second heal at the same
      Centre produced **exactly one** `withdrawing` line in total: with the PID now in the party
      `find_in_box` returns None and the piggyback returns without touching the PC. A
      duplicate-withdraw loop is the regression shape a fires-every-heal piggyback invites.
      ‼ Graded with a capability test, NOT a batch — four batches on 2026-08-06 produced zero
      statistically resolvable finish-rate differences; this took ~45,000 frames.


---

# ARCHIVED 2026-08-17 — the 8 oldest CLOSED items from `03-PUNCH-LIST.md`'s "## Done"

Moved on the R3 3,600-line budget. Every one was already `[x]`. Verbatim, unedited.

- [x] **#24-movelearn-recovery — DONE 2026-07-25. The #1 open item; killed 2 of 5
      cold-start runs (~f1.55M each).** ‼ The filed diagnosis ("the recovery scope is
      the bug, not the move-learn logic") was only the LAST of four links — fixing just
      it would have produced a dead run with a nicer log line. Real chain, from the
      captures `saves/movelearn_hmwedge_{quickattack,slash}.ss1`: Combusken carries
      Rock Smash (an HM **and** its weakest move); a stray A from the "unrecognised
      text" branch answered YES to a prompt the bot had decided to DECLINE; a cursor
      read while the summary screen was still animating in was stale, so A landed on the
      HM slot; the game replied with `Task_HandleInputCantForgetHMsMoves`, **a symbol
      nothing in the codebase referenced**, misreported as the Yes/No; and the handler
      then sat in an UNBOUNDED "screen still opening" branch pressing **nothing for
      6,000 frames**. Fixed: `LearnMoveState.CantForgetHM` checked first; a branch that
      dismisses the refusal AND strikes the refused slot off; no A on an untrusted
      cursor; the wait bounded; and `modules/battle_fault.py` — an OPT-IN channel
      (`handles_battle_faults`) that carries a battle fault to the mode instead of
      raising across the controller stack, so it costs one DERAIL. A/B: WEDGED at
      f23,400 → RESOLVED at f258 / f224, movesets correctly unchanged; stock modes
      verified unchanged. Repros: `repro_movelearn_hm_wedge.py`,
      `repro_movelearn_fault_recovery.py` (3 arms).
- [x] **#24-fortreebadge — SATISFIED 2026-07-25: BADGE 6 WON from a cold start.** Filed
      2026-07-24 when the isolated Fortree drive lost to Winona and whited out — it called
      `do_fortree_gym()` directly with whatever party the save carried, and battle prep
      (lead selection + heal) is the CALLER's job. Confirmed the right way, by a full
      run rather than a gate fix: a fresh title-screen run reached the **Feather Badge =
      end of built content** (38 maps, ~2.48M frames, 0 derails).
- [x] **#24-fortreegates — DONE 2026-07-24: the Fortree Gym rotating-gate puzzle is
      solved LIVE.** `modules/story/fortree_gates.py` is a port of the decomp's
      `src/rotating_gate.c`, validated **4/4** against the emulator. Includes the
      parked-trainer escape: a trainer standing on the path is cleared by RESETTING the
      room (exit + re-enter forces the documented gate reset), not by waiting.
- [x] **#24-harness-savepath — DONE 2026-07-25: stall snapshots are per-run AND
      per-stall.** Two defects in one line. (a) The no-progress auto-save wrote a single
      shared `saves/midstuck.ss1`, so concurrent runs overwrote each other and the
      artifact belonged to no particular failure — that is precisely why the move-learn
      stall had no clean repro, and why one earlier investigation burned effort on a
      `midstuck.ss1` that was a whiteout state from a different map. (b) It fired ONCE
      per run, but a run usually stalls several times and the first stall is typically a
      recoverable hiccup — the interesting capture was the one never taken. Snapshots now
      land in `tools/story-dev/saves/stalls/`, which unblocked `#24-movelearn-recovery`.
- [x] **#24-harness-finish — DONE 2026-07-25: a SUCCESSFUL run no longer reports as a
      hang.** The first cold-start Badge 6 run reached the end of built content at
      f2,483,319, printed "end of built content — handing to manual", and then correctly
      stopped doing anything — so the harness's frame-based no-progress detector fired
      20,000 frames later and the log ended `HANG CONFIRMED`. `compare_runs.py` inherited
      the false signal and classified it `no-path` (a transient, recovered "Could not find
      a path" earlier in the log). The one run that worked looked like the worst kind of
      failure. Both tools now check the bot's own end-of-content message before calling a
      stop a hang.
- [x] #1 — Vendor upstream 40Cakes/pokebot-gen3 (subtree @ 5dd898f8) (2026-07-17).
- [x] #2 — Deep documentation pass + Pokemon_Emerald_AI_Notes.md (2026-07-17).
- [x] #4 — install.py V2 (setup/update/heal + ROM handling) — "worked!" (2026-07-18).

---

# ARCHIVED 2026-08-17 (second draw) - 6 more CLOSED items from 03-PUNCH-LIST's "## Done"

Moved to give the NEXT session working headroom: queue item 0's first act edits that file, and it
was ~6 lines from a hard R3 failure that would have blocked its Tier 0 commit. All were [x].
Verbatim, unedited.

- [x] #5 — Native dashboard GUI + handheld mode — "worked!" (2026-07-18).
- [~] #24-textread — DIALOGUE AWARENESS: read on-screen text to drive interactions
      (user 2026-07-20; design §DA). FEASIBILITY CONFIRMED (decode_string of
      gDisplayedStringBattle / gStringVar4 reads exact text). STARTED: move-learn
      now uses text-driven detection (both builds) — UNIVERSAL (matches generic
      phrases + reads the offered move dynamically, not hardcoded to any move).
      â˜… ROOT CAUSE of the Lv16 hang FOUND & FIXED (ML-13): the Emerald battle Yes/No
      has no task and was detected only by a fragile script-offset; when it stayed
      `Unknown` the old code pressed nothing (is_waiting_for_input gate) → froze.
      `handle_move_replacement_dialogue` rewritten fully text/task-driven;
      `handle_evolution_scene` hand-off hardened. PROVEN by fault-injection A/B on
      both builds (old stalls ~10.6k frames & fails to learn; fix resolves in 394 &
      learns Pursuit + evolves). Faithful repro harness: scratchpad/repro_movelearn.py.
      Still want the user's real-32× confirmation. FULL SYSTEM (next big build):
      Reader (normalized current text + menu/cursor) -> Classifier (text -> interaction
      type) -> Responder (type + story progress + config -> answer; multi-valid
      decisions like fossil/starter = random). Gather conversation dumps {exact text,
      speaker, valid answers, how to answer} from runtime logging + pokeemerald script
      data; build a response table. Subsumes fragile scripted-scene ride-outs; robust
      + deterministic vs flaky task-state. Backstops: no-progress watchdog + advance-
      plain-text-with-A so nothing hard-freezes.

- [x] #24-evo-trainstall (FIXED 2026-07-22: interrupt-safe _rotate_lead_safely + _yield_bounded; proven on evostall.ss1; same fix covers the user's 110k-frame Joey stall) — `train_team`/`_story_spin` can hang right AFTER a
      trainee EVOLVES mid-training (batch run02 2026-07-22: Grovyle evolved +
      learned Fury Cutter on Route 116, then the spin never resumed → 20k-frame
      HANG). Repro save: tools/story-dev/saves/evostall.ss1. Likely the
      post-evolution return-to-overworld transition isn''t ridden out before the
      next spin action (cf. the move-learn / dock-arrival family). Prove + fix.
- [x] #24-pokenav-faithful — ‼ SUPERSEDED: recurred 2026-07-26, see the OPEN entry above. (RESOLVED 2026-07-22: the user ran VIDEO OFF — the renderer-gated fallback fired exactly as designed; keep video off on the weaker test PC, the fallback covers it) — WATCH ITEM (user fresh-run log 2026-07-22 13:24): the
      PokéNav Match-Call tutorial took the STATE-WRITE FALLBACK on a real-GUI run
      (video on) — the faithful play-through previously worked on this hardware.
      By design the fallback is legal (never hang), but check why the faithful
      path didn''t engage (timing? renderer-gate read?) next time it recurs.
- [x] #24-wattson-strength — DONE 2026-07-22 (KI-13 resolved): 0-power move-learn
      guard + Segment 9c prep (Route 117 (31,16) band 20-24) + aftermath-quiet
      riding → run 14 beat Wattson end-to-end; `wattson_done.ss1` verified.
      Residual (folded into #24-movelock): audit the evolution-scene learn flow
      that dropped Marshtomp''s Mud Shot at L16 (moot for Wattson, still a
      move-quality gap).


- [x] #24-hm-learner — HM TEACH VALIDATION + LEARNER ACQUISITION (user report
      2026-07-23, DONE same day): Segment 10b used to teach the HIGHEST-LEVEL mon,
      which loops in the party menu (NOT ABLE) whenever that mon can't learn the
      HM. Now: `hm_learner_slot(item)` picks the best COMPATIBLE party mon;
      `ensure_hm_learner(item)` hunts + catches an accessible learner species when
      the party has none (grounds derived live from ROM encounter tables ×
      TM/HM learnsets — nothing hardcoded, works for every future HM);
      `teach_hm_move` hard-fails truthfully on an incompatible target. A/B-proven
      (repro_hm_learner.py + the hmtest harness driver: fault-injected
      "nobody compatible" → hunted Route 117 → caught Poochyena → taught it).
      Feeds directly into #24-hm-slaves (the acquisition half now exists).

### #24-endlessruns — ENDLESS DEBUG-RESET RUNS (user request, 2026-07-25)

**CLI form: DONE** — `tools/story-dev/endless_runs.py`, smoke-tested.
```
py -3.12 tools/story-dev/endless_runs.py                 # 10 runs, treecko
py -3.12 tools/story-dev/endless_runs.py --count 0       # INFINITE (Ctrl-C)
py -3.12 tools/story-dev/endless_runs.py --count 25 --starters all
```
Back-to-back FRESH runs, unthrottled, debug logging on, appending one row per run to
`tools/story-dev/endless-runs/LEDGER.md` (depth reached · outcome · frames · wall-clock · log).

**Failsafes — each exists because of a failure actually observed 2026-07-24/25:**
* `--run-timeout` (wall clock, default 5400s): the harness's watchdogs are FRAME-based, so a
  wedged emulator process advances no counter and fires nothing. Only an external wall-clock
  bound catches that.
* `--stall-timeout` (default 600s): kills a run whose LOG STOPS GROWING. A run can burn frames
  forever while making zero progress — the 2,000,000-frame fodder grind looked alive throughout.
* **A fresh profile per run, metadata COPIED from a template.** "FRESH boot from title" still
  loads the profile's battery save, which once produced three worthless runs that reported as
  fresh while starting in Fortree with a L39 party. ‼ metadata.yml must be COPIED, not
  synthesised — it carries the ROM reference, and a hand-written one makes every run die
  instantly with "Could not find ROM ``".
* **One bad run never aborts the batch** — every outcome is recorded and the loop continues.
* **Zero frames is never reported as success.** The first cut scraped a 5-second ROM-not-found
  death as `clean-finish`; an overnight batch of those would have read as green.

**`#24-endlessruns-gui` — DONE 2026-07-25, and it shipped as something better than the plan
above.** The plan was a menu item that shells out to this CLI module. That was built first and
FAILED in the user's hands: the dialogs appeared and nothing happened, because "endless debug
reset runs" means *this emulator*, not a separate headless harness.

So it shipped instead as **a real in-process bot mode: `Story (ENDLESS RESET)`**
(`StoryEndlessResetMode`, `plugins/custom_modes/story_mode.py`) — it simply loops
`Story (DEBUG - RESET)`'s `run()`, so every iteration is a hard reset → forced NEW GAME → play,
back to back in the running emulator. In BOTH builds. Count comes from the GUI's
"Endless Debug-Reset Runs…" item (`ENDLESS_RESET_TARGET`, default 10, `0` = forever).

In-process failsafes beyond the CLI's: a `BotModeError` in run 3 is SWALLOWED so runs 4..N still
happen; a hard 3.5M-frame-per-run cap (StoryMode's own watchdog can't catch a wedged watchdog);
the bot mode is re-asserted after every run because a derail can call `set_manual_mode()`; and
the batch's emulation speed + video settings are captured once and restored each run — the first
cut restored `bot_mode` but not the speed, so run 1 ran unthrottled and every run after it
crawled at 1× (user-reported, fixed in `aadad944`).

The CLI form above is NOT superseded — it keeps the fresh-profile-per-run and wall-clock/log-growth
failsafes that an in-process mode cannot have, and remains the right tool for a scripted batch.

- [x] `#24-ch20rename` — ✅ **DONE 2026-08-13.** Renamed and VERIFIED BY RE-RUNNING BOTH, not by a
      diff: `--driver ch21dive` → **`ch20dive`** (class `Ch21DiveMode` → **`Ch20DiveMode`**, all 33
      log tags), `probe_ch21_topology.py` → **`probe_ch20_topology.py`**, and
      `ai-research-notes/2026-08-13-ch21-dive-leg-predictions.md` → **`...-ch20-...`**. Also the
      three `§Ch21` prose occurrences inside `story_harness.py`, each checked individually to be
      about the cavern. **Proof:** `probe_ch20_topology.py` exit 0; `--driver ch20dive` →
      `[ch20dive] ACCEPTANCE: PASS legs=6/6 at_entrance=True got_out=True can_continue=True`.
      Current-state docs `03`/`04`/`05` updated (0 residual old names). ‼ **`06`/`07`/`08` were
      deliberately NOT touched** — append-only history is not rewritten, so 7 references to the old
      names remain there on purpose; **both renamed files carry a provenance header** saying those
      entries mean the new artefacts. 17/17 gates PASS, `lint_docs` PASS. Original item follows.

## 2026-08-17 — CLOSED punch-list items archived verbatim (`#24-handoffbudget` relief valve)

‼ These are **CLOSED** (`[x]`) items moved out of `03-PUNCH-LIST.md` when it reached its
3,600-line R3 limit, which BLOCKS the Tier 0 commit. Nothing was edited — the text below is
verbatim. A one-line stub carrying the same tag remains in the punch list, so any
cross-reference still resolves. ⛔ None of this is outstanding work.

### #24-magmahideout (archived 2026-08-17)

- [x] `#24-magmahideout` — ✅ **DONE 2026-08-10. `GROUDON_AWAKENED_MAGMA_HIDEOUT` is SET, and
      `do_magma_hideout_chapter()` is wired into `story_mode.py` as Segment 15.**
      ```
      [magmahideout] RESULT groudon=True map=MAGMA_HIDEOUT_4F at=(15, 21)
        floors=['MAGMA_HIDEOUT_1F','MAGMA_HIDEOUT_2F_1R','MAGMA_HIDEOUT_3F_1R','MAGMA_HIDEOUT_4F']
        whiteouts=0
      ```
      Binary acceptance, no batch. Full chain driven: Mt. Pyre → Lilycove heal → Mauville heal
      **+ teach Strength** → R111/112 (Rock Smash rock cleared) → cable car → Mt. Chimney →
      Jagged Pass → coord trigger → two Strength pushes → 1F→2F_1R→3F_1R→4F → Maxie.
      ‼ **Maxie is approached ADAPTIVELY** — all four neighbours are tried at runtime, because the
      static read said `(17,21)` and the live arrival said `(15,21)`. The winning run used
      `(15,21)`. Every static claim about this dungeon has been wrong at least once.
      HISTORY — **IN PROGRESS 2026-08-10 (evening). Increments 1-3 WRITTEN;
      increment 1 driven-tested and iterating. Entry model CORRECTED twice today.**

      ‼‼ **THE ENTRY IS A STEP TRIGGER, NOT A WALK.** The door `JAGGED_PASS (16,18)` is covered
      by `METATILE_Lavaridge_RockWall` at runtime (`JaggedPass_OnLoad` →
      `..._ConcealHideoutEntrance`) while `VAR_JAGGED_PASS_STATE <= 1`. A coord_event on one of
      **(21,15) (22,20) (21,20) (14,15) (13,15)** runs `JaggedPass_EventScript_OpenMagmaHideout`,
      which opens the metatiles and sets the var to **2**. The var reaches 1 by itself
      (`JaggedPass_OnResume` checks for the Magma Emblem). **Use `(13,15)`** — 8-10 waypoints
      from the descent's arrival tiles vs 15-23 for the (21,*)/(22,*) trio.
      ‼ `calculate_path` said "(16,20) → (16,18), 2 waypoints" for that sealed tile, because it
      reads the ROM LAYOUT and cannot see a `setmetatile`. **A static PASS is not evidence on a
      map whose scripts rewrite metatiles** (`08-MISTAKES` 2026-08-10). This is the third wrong
      answer about this one door; the other two were "one-way ledges" and "a real south-facing
      ledge", both the same wall.

      **BUILT (in `modules/story/early_game.py`, all compile-clean):**
      `travel_to_magma_hideout_door()` · `open_magma_hideout_entrance()` ·
      `enter_magma_hideout()` · `do_magma_hideout()` · `do_magma_hideout_chapter()`.
      Driver `--driver magmatravel`; probes `probe_magma_anchor.py` (era gate, 4 controls),
      `probe_ch15_travel.py` (route), `probe_ch15_interior.py` (interior).
      ‼ **NOT yet wired into `story_mode.py`** — waiting on a green increment-1 run.

      **MEASURED THIS SESSION:**
      * anchor `post_mtpyre.ss1` VERIFIED READY (guard flag True, `MT_PYRE_STATE`=1, Emblem in
        bag; era control passes against `jagged_descent.ss1`).
      * ‼ **Ch14 hands over a WRECKED party** — 3 of 6 fainted, survivors at 21/117 and 18/109,
        lead's best move at 0 PP, **one Hyper Potion and no Revives**, and the nearest Pokémon
        Center is 276+ waypoints away (Mauville 276 / Fortree 432 / Lilycove 883). It dies ~61
        waypoints in, on ROUTE123. **The whiteout is the game's own recovery and StoryMode
        already handles it** (`on_whiteout` → True); the travel leg now heals at Lilycove and
        Mauville en route and survives.
      * the overland haul WORKS: run 3 reached **ROUTE112 (28,28)**, the cable-car station
        approach, after one whiteout.
      * ‼ **Lavaridge is NOT reachable from ROUTE112 by the live navigator** ("it is not
        walkable from ROUTE112", 3/3) although `calculate_path` scores it 66 waypoints. The
        staging heal there is now best-effort.

      ‼‼ **INCREMENT 3 IS BLOCKED ON `#24-strength` — MEASURED, NOT SUSPECTED.** The driven run
      entered 1F cleanly and stopped dead: `groudon=False map=MAGMA_HIDEOUT_1F at=(10,34)
      floors=['MAGMA_HIDEOUT_1F'] whiteouts=0`. A plain COLLISION flood (no elevation, no
      pathfinder — an independent instrument) shows 1F has **three components**: #0 **299 tiles**
      with the entrance (10,34) and `(25,34)→2F_1R`; #1 **70** with `(31,3)→2F_2R`; #2 **NINE**
      with `(20,22)→2F_3R`. `calculate_path` reaches **44** of #0's 299, and the boundary is
      **exactly three edges, all into Strength boulders** — `(7,23)→(7,22)`, `(7,23)→(6,23)`,
      `(8,22)→(7,22)`. The boulders ARE the gate.
      ‼ **The §Ch15 "shortest route" was WRONG and is corrected**: `(20,22)` is on that nine-tile
      island, i.e. an EXIT from 2F_3R, never an entrance. Real route (all legs verified connected
      to their arrival tiles — 2F_1R 383, 3F_1R 154, 4F 293):
      `1F (25,34) → 2F_1R → (17,33) → 3F_1R → (7,21) → 4F`, then stand `(17,21)` facing Left and
      TALK to Maxie at `(16,21)`. **Everything past 1F is already proven connected.**

### #24-strength (archived 2026-08-17)

- [x] `#24-strength` — ✅ **DONE 2026-08-10.** `ensure_strength_learner()` +
      `strength_push()` + `open_magma_hideout_1f()` in `modules/story/early_game.py`, proven by
      the chapter completing. Kept OUT of `obstacle_clearing` on purpose: that framework's success
      test is "the object is GONE", and a boulder is PUSHED — so the test here is **the boulder
      MOVED**, tracked by `local_id` (the player ends up standing on its old tile).
      ‼ Three bugs found only by driving it, all logged in `08-MISTAKES`: a one-frame press is not
      a walk; `walk_one_tile` leaves the D-pad HELD if abandoned early; and **a flag set by a
      script is not the end of that script** (the avatar was still `lockall`ed — that one cost two
      runs). The teach is done at a HEAL STOP to dodge `#24-teachmsgstall`.
      HISTORY — **NEW 2026-08-10. The blocker on `#24-magmahideout` increment 3, and the
      first hard dependency the story bot has had on an unsupported field move.**
      `obstacle_clearing.KNOWN_BUT_UNSUPPORTED` excludes `EventScript_StrengthBoulder` on purpose:
      *"a boulder is PUSHED, not removed; the success test cannot see it"* — i.e. the existing
      obstacle framework's success test ("is the obstacle gone?") cannot express this move. Two
      pieces are needed and they are independent:
      1. **A party member that knows Strength.** ✅ **CHEAPER THAN EXPECTED — measured
         2026-08-10 on both `post_mtpyre.ss1` and `magma_door.ss1`:**
         * **`HM04` is ALREADY IN THE BAG** (alongside HM02/HM03/HM06) — no Rusturf Tunnel trip.
         * **Badges 1-6 are held**, and field Strength is gated on the **Heat Badge (BADGE04)**,
           which is one of them.
         * ‼ **CORRECTION (measured minutes later, and it reverses the easy part).** I first
           wrote that `Zigzagoon L3` would carry it — it has a free fourth slot and is already
           the Surf slave. **`can_learn_tm_hm(HM04)` is FALSE for Zigzagoon.** Only **two** party
           members can learn Strength at all, and **both have four moves**:
           | slot | mon | moves | can learn HM04 |
           |---|---|---|---|
           | 0 | Mightyena L43 | Tackle / Taunt / Take Down / Bite | **True** |
           | 4 | Sceptile L43 | Rock Smash / Pursuit / Leaf Blade / Slam | **True** |
           | 1,2,3,5 | Zigzagoon, Swellow, Skitty, Castform | — | False |
           ⇒ the teach **costs a move slot on a fighter**. `hm_learner_slot()` picks the
           highest-level compatible mon and breaks the L43 tie toward slot 0, i.e. **Mightyena**;
           `teach_hm_move(replace_slot=None)` then takes the most expendable slot, which is
           **Taunt** (base power 0) — a status move, so the damaging-move count does not drop.
           That is the good outcome and it should be asserted, not assumed.
           ‼ Sceptile is the WORSE carrier: its only 0-power-ish slot is protected (Rock Smash is
           an HM) so the picker would eat a damaging move.
         ⇒ still one `teach_hm_move()` call with existing machinery, but **verify the mon that
         ends up knowing Strength and which move it lost**. ‼ Do the teach at a heal stop, the way
         `#24-pc` piggybacks — not as a detour.
      2. **A success test that works for a PUSH.** The obstacle is not removed, it MOVES, so the
         test must be "did the boulder's tile change / is the target tile now walkable", not
         "did the object disappear". ‼ Do NOT reuse the Rock Smash path unmodified — its test is
         exactly the one that cannot see this.
      ‼ Bound any push loop: a boulder that will not move (pushed against a wall) must fail
      loudly rather than retry, and Rock-Smash rocks respawning on map reload already turned one
      retry loop into 23.9M wasted frames (KI-34).

      HISTORY — ✅ **NOT BLOCKED. READY TO BUILD (2026-08-10). The three-week-old
      deferral was right by accident and wrong in its reason.**
      The door at JAGGED_PASS (16,18) is guarded by a **Team Magma NPC standing on (16,19)**,
      the column's only entry — `OBJ_EVENT_GFX_MAGMA_MEMBER_M`, hidden by flag **847**
      `HIDE_JAGGED_PASS_MAGMA_GUARD` (decomp `JaggedPass/map.json`). Measured:
      | save | guard hidden | `(16,20)→door` |
      |---|---|---|
      | `jagged_descent.ss1` (badges 1-3) | False | FAIL |
      | `post_mtpyre.ss1` (badges 1-6) | **True** | **OK, 2 waypoints** |
      ⇒ **No ledge problem, no KI-24 blind spot, no scripted movement needed** — the planner
      was correctly modelling the guard. In the right era the door is 2 waypoints from a
      tile the bot already reaches, and the chapter runs after Mt. Pyre so the flag is set
      by the time it matters.
      **BUILD ANCHOR: `saves/post_mtpyre.ss1`.** ‼ Do NOT develop this from a pre-Emblem
      save — that error cost seven probes and two wrong conclusions (`08-MISTAKES` 2026-08-10).
      HISTORY — status conflict flagged by triage: THIS entry says **DEFERRED** (the JAGGED_PASS (16,18) door is unreachable from
      the ROUTE112 side), while `04-HANDOFF.md` lists it as the **next story content and the
      largest untouched lever**. Both are current-state files and they disagree, which is
      exactly the case `CLAUDE.md` says to raise rather than resolve unilaterally.
      ‼ **THE TECHNICAL OBJECTION IS NOW CORROBORATED, AND IT IS THE ONLY THING BETWEEN THE BOT
      AND NEW CONTENT** — measured 2026-08-10 (static, with a PASSING control):
      | from | to `MAGMA_HIDEOUT_1F` door (16,18) |
      |---|---|
      | MT_CHIMNEY entry (13,5) | **FAIL** |
      | MT_CHIMNEY entry (14,5) | **FAIL** |
      | door → ROUTE112 exit (14,40) | **FAIL** |
      | CONTROL: entry (13,5) → ROUTE112 exit (14,40) | **OK, 39 waypoints** |
      Warps confirmed from the decomp: JaggedPass exits are (14,40)/(15,40)→ROUTE112,
      (13,5)/(14,5)→MT_CHIMNEY, and **(16,18)→MAGMA_HIDEOUT_1F**. The door tile IS walkable;
      it simply sits in a pocket the descent cannot enter. So `do_jagged_descent()` already
      walking this map does NOT get us the door.
      ‼ **BUT A STATIC FAIL IS 'UNPROVEN', NOT 'IMPOSSIBLE'** — `calculate_path` reads
      dual-elevation terrain and ledges as walls and has called a reachable place
      unreachable before (KI-24). **The deciding test is a DRIVEN one**, and the anchor
      tooling to run it did not exist when this was deferred on 2026-07-26:
      capture a MT_CHIMNEY/JAGGED_PASS anchor with `--driver anchorstory`, then drive
      `--driver groundsweep SWEEP_GROUND=JAGGED_PASS:16,18`. ~20 minutes, and it converts a
      three-week-old deferral into a measured yes/no. **DO THAT BEFORE WRITING THE CHAPTER.**
      ✅ **RE-TESTED PROPERLY 2026-08-10 (two DRIVEN attempts + a purpose-captured anchor):
      the blocker is REAL, and the chapter is BUILDABLE with scripted movement.**
      From the bot's OWN in-descent position `JAGGED_PASS (14,9)` the door and both its
      neighbours are unreachable while the control (continue to the ROUTE112 exit) succeeds
      in 34 waypoints. A walkable flood fill shows the door is in the SAME 238-tile region as
      every warp, so it is **ledge-isolated, not walled off** — `(15,18)`/`(17,18)` are solid
      and the nearest reachable tile is `(14,18)`, two away.
      ⇒ **Do not try to fix generic navigation for this. Write the approach as EXPLICIT
      SCRIPTED MOVEMENT**, which is already this item's own instruction and the project's
      pattern for ledge terrain. Anchors to develop against now exist:
      `saves/jagged_descent.ss1` (JAGGED_PASS (14,9)) and `saves/mt_chimney_top.ss1`.
      HISTORY — **DEFERRED.** Door at JAGGED_PASS (16,18) is unreachable from the
      ROUTE112 side (one-way ledges; a 2026-07-26 probe already failed to path there). Only
      approach is ROUTE112 → cable car → MT_CHIMNEY → descend ⇒ ~8 warps + a scripted ride.

## `#24-relocfloor` — ARCHIVED VERBATIM from `03-PUNCH-LIST.md` on 2026-08-17

> Moved under the R3 line-budget relief valve (the punch list hit its 3,600-line limit while
> `#24-orphans` (5) was being closed). ⛔ NOTHING HERE IS OUTSTANDING — the item was DONE on
> 2026-08-01. Kept verbatim for its measured relocation-floor table and its "only the floor is
> wrong" reasoning, which later training work still leans on.

- [x] `#24-relocfloor` — **DONE 2026-08-01.** Extracted as the pure
      `training_areas.relocation_floor(local_max, trainee_levels, gap)` and wired into
      `_prepare_for_fight`. Repro green, full suite 69/69. Original diagnosis below.

      `#24-relocfloor` — **the training-relocation floor is keyed on the WRONG MON.**
      Diagnosed + repro'd 2026-08-01; the code edit was deliberately held because
      `x4_headless.py:843` relaunches a dead lane's process and a restarted lane would
      re-import mid-batch, mixing two code versions into one measurement.

      `story_mode.py` `_prepare_for_fight`:
      ```python
      floor = max(local_max, team_max_now - self.FODDER_LEVEL_GAP)
      better = best_training_area(team_max_now, min_wild_max=floor, allow=_allow)
      ```
      `team_max_now` is the party's STRONGEST mon, but `need` (the mons being trained) is
      the stragglers — a real batch4 Norman party is `Marshtomp L35 / Ninjask L30 /
      Swellow L32 / Poochyena L12 / Shedinja L20`. Keying the floor to L35 demands wilds
      above L23 and so rejects **ROUTE111 (L19-22)**, the one reachable area, though it is
      near-ideal for a L20 trainee. Measured: `no better area is available` fired **167×**
      in batch4, every one `local grass (max L4)` (ROUTE102), teams L32-41.

      ‼ **ONLY THE FLOOR IS WRONG — do not "key it all to the trainee".** `train_team` runs
      with SWAP-TRAIN on, so a STRONGER team-mate does the fighting; the winnability/scoring
      argument (`best_training_area`'s first parameter) is correctly `team_max_now`.

      **THE EXACT CHANGE:**
      1. Add to `modules/story/training_areas.py`:
         ```python
         def relocation_floor(local_max: int, trainee_levels, fodder_gap: int) -> int:
             """Minimum wild level worth relocating FOR, keyed to the mons being trained."""
             if not trainee_levels:
                 return local_max
             return max(local_max, max(trainee_levels) - fodder_gap)
         ```
      2. In `story_mode.py` `_prepare_for_fight`, replace the `floor = …` line with
         `floor = relocation_floor(local_max, [party[i].level for i in need], self.FODDER_LEVEL_GAP)`
         (leave `best_training_area(team_max_now, …)` unchanged).
      3. `repro_relocation_floor_wrong_mon.py` check 4 goes green. Re-run the full suite.

      **Effect, measured with the real tables** (`allow` restricted to what is reachable
      near Petalburg):
      | party | floor now | pick now | trainee floor | pick |
      |---|---|---|---|---|
      | L35, stragglers L12/L20 | 23 | **None** | 8 | **ROUTE111 L19-22** |
      | L36, straggler L12 | 24 | **None** | 4 | **ROUTE111 L19-22** |
      | L33, stragglers L20/L27 | 21 | ROUTE111 | 15 | ROUTE111 |

      ‼ **NECESSARY BUT PROBABLY NOT SUFFICIENT AT PETALBURG, and say so rather than
      overclaim.** When every richer area is reachable both floors agree and the fix changes
      nothing. From Petalburg even ROUTE111 is often unreachable — which is why some L32-34
      runs refused too. Its real value is unlocking the agreed **pre-emptive training** plan
      (train near Lavaridge, where ROUTE111/ROUTE117 demonstrably ARE reachable, before
      travelling to Petalburg at all). Expect little from this fix alone in a batch.

## `#24-cavethread` — ARCHIVED VERBATIM from `03-PUNCH-LIST.md` on 2026-08-17

> Moved under the R3 line-budget relief valve (the punch list hit its 3,600-line limit while
> `#24-ki76correctness` was being filed). ⛔ NOTHING HERE IS OUTSTANDING — CLOSED 2026-08-05,
> and its own headline says it was NEVER A BLOCKER. Kept verbatim for the multi-hop cave
> reasoning, which later pathfinding work may still want.

- [x] `#24-cavethread` — **‼ CLOSED 2026-08-05: IT WAS NEVER A BLOCKER. Multi-hop cave
      threading ALREADY WORKS, in both directions, with no chain table.**
      Measured (`--driver cavethread`, `reached_dest` = maps actually visited):
      **IN** `DEWFORD_TOWN → ROUTE106 → GRANITE_CAVE_1F → B1F → B2F` (3 warps);
      **OUT** `GRANITE_CAVE_B1F → GRANITE_CAVE_1F → ROUTE106 → DEWFORD_TOWN`.
      MT_PYRE_SUMMIT is the same 3-warp shape ⇒ **`#24-mtpyre` is UNBLOCKED**, and Granite Cave
      B1F/B2F can be unparked as training grounds.
      ‼ **THE ONE REAL GOTCHA: never pass a WARP TILE (door/ladder/stairs) as a navigation
      destination** — walking onto it FIRES it, so the trip ends one map PAST the target and
      the navigator reports success. Both probe runs hit this and both first read as failures.
      Only the stale `_CAVE_EXITS` comment was changed; the tables are kept (redundant, cheap,
      harmless). Full detail: `07-CHANGELOG.md` + `08-MISTAKES.md` 2026-08-05.

      <details><summary>superseded framing (kept for the reasoning trail)</summary>

      ‼ **RE-SCOPED 2026-08-05 — DO NOT BUILD THE CHAIN TABLE YET. MEASURE FIRST.**

      The item used to read "`_CAVE_EXITS`/`_CAVE_ENTRANCES` are SINGLE-HOP, therefore build a
      multi-hop chain table". **The premise behind that conclusion is stale.** Those two tables
      date from 2026-07-26 and their justifying comment says *"the global navigator can NOT
      cross warp levels"* — which was true then and **was fixed on 2026-07-31 by `#24-journey`**.
      `navigate_to_anywhere` is now a multi-hop, self-replanning, live-validated warp navigator,
      and `_navigate_riding_out` (what the training/hunting paths already call) wraps it.

      **STATIC RECON DONE (2026-08-05, no emulator** — replayed `WarpGraph.map_route` against
      the committed ROM cache `cache/warp_graph_BPEE0.json`; script in the changelog entry):
      the graph **already knows every route in question, in BOTH directions** —
      | route | hops |
      |---|---|
      | `ROUTE106 -> GRANITE_CAVE_B2F` | 3 |
      | `GRANITE_CAVE_B2F -> DEWFORD_TOWN` (the leg that dropped 2 real-HW runs) | 4 |
      | `ROUTE122 -> MT_PYRE_SUMMIT` | 3 |
      | `JAGGED_PASS -> MAGMA_HIDEOUT_4F` | 4 |

      ‼ **WHAT THIS DOES AND DOES NOT PROVE.** It refutes "the route data is missing" — the
      thing a hand-built chain table would supply. It does **NOT** prove the bot can WALK it:
      `map_route`'s own docstring warns its connection edges can be **PHANTOMS** (the measured
      Verdanturf->Route116 case). Route known ≠ route walkable. That is the same
      one-measurement-fits-all error KI-39 already cost this project a day on.

      **THE REAL RISK, NAMED:** `_walk_warp_chain` documents a **ONE-WAY LEDGE** on Granite Cave
      1F — within-floor reachability is **DIRECTIONAL**, so the graph's single `GRANITE_CAVE_1F`
      node is really two disjoint sections, which a MAP-granular planner cannot see. The generic
      navigator's `used_warps` + revisit-deprioritisation is a *plausible but unproven* mitigation.

      ⏭ **NEXT ACTION — run the probe, it is already written** (`--driver cavethread`, added to
      `story_harness.py` 2026-08-05; destination tiles come from the warp graph's own ROM
      `to_coords`, so nothing is guessed):
      ```
      cd tools/story-dev
      PYTHONUTF8=1 py -3.12 story_harness.py saves/dewford.ss1 --driver cavethread \
          --frames 600000 --profile repro-cave1
      ```
      **Granite Cave is the deliberate test case, not a convenience:** same 3-warp depth as Mt.
      Pyre Summit, already parked for this, and it carries the hardest known hazard (the ledge).
      If the generic navigator threads Granite Cave in AND back out, `#24-cavethread` collapses
      from "build a chain system" to "delete the two stale tables" — and Mt. Pyre unblocks.
      If it fails, the log names which leg and where, and THAT is the thing to fix.
      ‼ Needs the box; do not run it while a batch is using the lanes.
      </details>

## `#24-r116sweep` — ARCHIVED VERBATIM from `03-PUNCH-LIST.md` on 2026-08-17

> Moved under the R3 line-budget relief valve (the punch list hit its 3,600-line limit while
> `#24-ki76correctness`'s measured driver spec was being written). ⛔ NOTHING HERE IS
> OUTSTANDING — ANSWERED 2026-08-09. Kept verbatim for the reachability method and the
> "do NOT add ROUTE116 to HUNTING_GROUNDS" ruling, which later hunting work still leans on.

- [x] `#24-r116sweep` — ‼ **ANSWERED 2026-08-09: DO NOT ADD ROUTE116 to `HUNTING_GROUNDS`.**
      Driven sweep from the newly captured, verified anchor `saves/mauville_prewattson.ss1`
      (MAUVILLE_CITY (19,15), **badge03=False**, party L16-L20):
      ```
      [sweep] RESULT ground=ROUTE116 arrived=False left=False badge03=False verdict=DO NOT ADD
      ```
      ‼ **READ THE FAILURE PRECISELY — it is not "Route 116 is unreachable".** The journey
      SUCCEEDED: the bot reached ROUTE116 in ~32,000 frames and stood at **(65, 11)**. The
      *intra-map* leg then failed — `Could not find a path from (65/11 @ ROUTE116) to
      (11/7 @ ROUTE116)`. `(11, 7)` is `RUSTBORO_TRAINING_GRASS`, a tile chosen for the
      **pre-Roxanne** era when the route is entered from the WEST; the counter hunt arrives
      from the EAST. `probe_r116_east_grass.py` (2 positive controls, both PASS) measured the
      split: from the east arrival **0 of 138** grass tiles are reachable (17 of 151 walkable,
      a pocket at x 64-78); from the west **136 of 138** are. Logged as **KI-49**.
      **CONSEQUENCE FOR WATTSON — this closes handoff concern #5.** His only legal pre-badge
      counter (Nincada @ ROUTE116) is **not huntable from where the hunt fires**. Combined with
      `#24-progressiongate` (his other option is behind him), **Wattson has no legal huntable
      counter**, and the chain stopping honestly is the CORRECT behaviour, not a gap to fix.
      Beat him with levels/lead. ‼ Do NOT relax the narrowing to manufacture a candidate —
      permissiveness measured 28 wasted treks and 15% conversion; the narrowing took conversion
      to 50% (z = +2.73).
      ‼ **The one thing that could revisit this is KI-49, not the sweep**: if journey planning
      learns to pick an entrance from which the tile is reachable, ROUTE116 becomes worth
      re-sweeping. Until then the verdict stands on driven evidence.

      HISTORY — **TOOL BUILT 2026-08-09, and the two anchors first tried were both invalid;
      the probe itself is what proved it.**
      New `--driver groundsweep` (`SWEEP_GROUND=MAP:x,y SWEEP_RETURN=MAP:x,y`) drives
      `_navigate_riding_out` there and back and prints
      `arrived=… left=… badge03=… verdict=ADD/DO NOT ADD`.
      ‼ It reports `badge03` and the party ON PURPOSE, because that is what exposed both bad
      anchors:
      | save | what it actually is | verdict |
      |---|---|---|
      | `mauville_wedge.ss1` | badge03=False but starts INSIDE the gym at (10,0); leg 1 failed stuck at (4,13) | wrong position — prep runs from the CITY |
      | `wally_done.ss1` | **lone Mudkip L14**, no Devon goods, no PokéNav, no Rustboro rival — the PETALBURG tutorial Wally, not the Mauville one | wrong ERA entirely |
      ‼ **`probe_counter_reachability.py`'s own docstring already warned about this** — *"Anchors
      are verified on load, never trusted by name — several saves in this directory have proven
      misnamed"* — and I ran two before reading it. **Verify the anchor's era and position BEFORE
      spending a run.**
      ✅ **ANCHOR OBTAINED 2026-08-09 — the blocker is gone.** `probe_anchor_inventory.py` read
      all 60 saves and answered the question properly for the first time: **none of them** stood
      in MAUVILLE_CITY with badge03 unheld, so the anchor did not exist and no third guess would
      have found it. It was then MADE with the new `--driver anchorstory` (the real story bot
      plays until it stands on the wanted map, then snapshots; `CAPTURE_FORBID_FLAG=BADGE03_GET`
      guarantees the era) and verified by the inventory probe as a separate instrument:
      **`saves/mauville_prewattson.ss1` — MAUVILLE_CITY (19, 15), badges [1, 2], party L16-L20,
      controllable**, captured in 13,666 frames.
      Run the sweep with:
      `SWEEP_GROUND=ROUTE116:11,7 SWEEP_RETURN=MAUVILLE_CITY:19,15 --driver groundsweep`
      (return tile 19,15 — the anchor's own tile, which the bot provably stood on; 22,6 is
      unverified and Mauville's walkability is exactly what KI-48 shows is not safe to assume).
      ‼ Do not read the `wally_done` run as evidence: `arrived=True` there says Route 116 is
      reachable from PETALBURG in the early game, which is not the question.

## (P1) + (P2) queue blocks — ARCHIVED VERBATIM from `04-HANDOFF.md` on 2026-08-18

> Moved under the R3 line budget during the deep sanity check. ⛔ BOTH ARE DONE, PROMOTED AND
> GATED; nothing here is outstanding. The one caveat that must stay visible is preserved in the
> stub: **KI-78 is NOT fully closed** — its residual cases remain open.

>    ✅ **(P1) The Slugma derail — FIXED, A/B PROVEN, GATED, PROMOTED.** `box_counter_pid` was
>    TYPE-ONLY while its party twin had accepted MOVE answers since 2026-08-08 — a fix applied to
>    one half of a documented pair. Gate `repro_box_counter_move_test.py` (#19) carries a PARITY
>    check so they cannot drift again. Also fixed: `catch_confirmed()` replaced a party-COUNT
>    delta (which a Shedinja spawn could fake) with an IDENTITY verdict.
>    ✅ **(P2) KI-78 Stage 1 — FIXED, A/B PROVEN, GATED (#20), AND PROMOTED (2026-08-14).**
>    Identity is now `(personality, species)`; a Shedinja shares its Ninjask's PID and the old
>    first-match lookup would **RELEASE the wrong Pokémon (permanent)**. ✅ **drift was ZERO at that point (2026-08-14) and
>    the fix is in BOTH forks — it still is**, verified by `--driver ch20dive --build custom` →
>    `ACCEPTANCE: PASS` and by both `--build custom` gates. Superseded: *"drift is 3 —
>    custom-pokebot has the WARNING but not the FIX."*
>    ⛔ **KI-78 is NOT fully closed** — residual cases stay open (debug-fabricated identical
>    pairs, corrupt box slots, Frontier rentals, and the evolved-since-capture path, which is
>    handled but **unexercised by any live caller**). See its entry.

## (P3) + (P3b) party-accounting blocks — ARCHIVED VERBATIM from `04-HANDOFF.md` on 2026-08-18

> Moved under the R3 line budget during the deep sanity check. ⛔ Both are DONE: Stage 0 is BUILT,
> GATED (#22) and DRIVEN, and (P3b) criterion (b) IS ANSWERED — a divergence WAS observed. The two
> rules that later work leans on are preserved in the stub.

>    ✅ **(P3) STAGE 0 — BUILT, GATED (#22), DRIVEN.** `modules/party_accounting.py` adds the
>    readers (**A** `gPlayerPartyCount`, per-slot occupancy) and a divergence log: **HOLE** (empty
>    slot below A — what makes B < A), **OVERFLOW**, **INVALID**, all EXACT from `get_party()`'s own
>    branches, plus **STALE**, ⛔ SAMPLED 1-in-300 (read the scan count, never the bare zero).
>    ✅ It wires NO call site and the gate ASSERTS that, with a byte-identical observer-on/off A/B
>    and a fault-injected observer that must break the LOG and never the read.
>    ✅✅✅ **(P3b) IS ANSWERED BY CRITERION (b) — A DIVERGENCE WAS OBSERVED (2026-08-15). ⛔ THIS
>    SUPERSEDES THIS FILE'S EARLIER "CRITERION (a) MET … NO DIVERGENCE" — THAT CLAIM IS RETRACTED.**
>    `collect_party_accounting.py` now reports **`✅ CRITERION (b) MET — A DIVERGENCE WAS OBSERVED`**:
>    **`HOLE x30` in `boxcounter2`, in BOTH forks** — *slot 5 of `gPlayerPartyCount=6`: counted by
>    the game but (near-)all zero*. Totals are now **967,970 recomputes · 39 drives · 12 drivers**
>    (the earlier ">400k / 11 drivers" and "7 drives / 280,707" figures are both superseded and
>    disagreed with each other).
>    ‼ **THIS IS THE GOOD OUTCOME, AND IT IS EXACTLY WHAT (P3b) PREDICTED.** Its own caveat said the
>    population lacked any PARTY-MUTATING drive, so the cases most likely to make A differ from B
>    were never exercised. `--driver boxcounter2` (Stage 2) became the first such drive — a real PC
>    deposit AND withdraw on a FULL party of 6 — and **the divergence appeared immediately, in both
>    forks.** The make-room deposit is the moment A and B disagree.
>    ⛔ **THE DATA SAT IN THE COMMITTED LEDGER FOR THREE COMMITS WHILE TWO WRAP-UP PASSES RE-ASSERTED
>    "NO DIVERGENCE"** — nobody ran the command this file itself calls the authority. ⇒ *a figure
>    quoted from memory is not a measurement; RUN `collect_party_accounting.py`.*
>    ✅✅ **PARTY-ACCOUNTING STAGE 1 IS THEREFORE UNBLOCKED** (re-pointing the ~35 capacity-shaped
>    call sites at A). It was gated on "the criterion above is met"; criterion (b) IS met, and the
>    collector says what to do next: **reproduce the `HOLE` case, then design Stage 1 around it.**
>    ⛔ Index/menu-cursor call sites STILL stay on B — if A > B an index from A is out of range for
>    the list the bot holds, most likely MID-BATTLE.
>    ‼ **"Stage 1" is OVERLOADED in this file:** *KI-78* Stage 1 is the identity fix and is **DONE
>    and PROMOTED**; *party-accounting* Stage 1 is this one and is now **UNBLOCKED, not forbidden**.
>    Never read one for the other.

## `#24-driftassertions` — ARCHIVED VERBATIM from `03-PUNCH-LIST.md` on 2026-08-18

> Moved under the R3 line budget at wrap-up. ⛔ NOTHING HERE IS OUTSTANDING — DONE 2026-08-17:
> the drift-statement sweep IS a gate (`audit_doc_consistency.check_drift`), A/B-measured 4->9
> sites caught with none lost, 17 fault tests. ‼ Its SEPARATE reduction half is tracked as
> `#24-driftreduction`, which is still OPEN and stays in the punch list.

- [x] `#24-driftassertions` — ✅✅ **DONE 2026-08-17 — THE GATE DELIVERABLE IS BUILT, MEASURED AND
      FAULT-TESTED BOTH WAYS.** `audit_doc_consistency.py::check_drift` now detects CLAIM SHAPE, not
      just the `expect` vocabulary. **A/B against the COMMITTED gate (`git show HEAD:`), same corpus,
      ground truth stubbed identically: 4 sites caught BEFORE → 9 AFTER, none lost.** The five newly
      caught are exactly the ones that had gone stale unseen — `04-HANDOFF:167` (the STATE cell a
      cold start reads), `:168`, `:824` (inside a fence), `:130` and `05-KNOWN-ISSUES:2325`.
      **THE RULE IS MARKER ATTACHMENT** — a figure asserts something about TODAY only when a
      currency marker is attached to the NUMBER (`(LATEST)`, `is <N> again`, `should report N
      differing`), or it is negated, or it is an `expect`ation. ⛔ **NOT "check every number near
      the word drift"**: that was MEASURED at **67** candidate windows, overwhelmingly
      deliberately-preserved history, and would have red-flagged the docs' own past.
      ‼ **THREE things measurement overturned, each of which would have shipped a broken gate:**
      (1) the negation "false positive" this item told me to rule on **does not exist** — the gate
      was silent on all six verbatim phrasings at BOTH ground-truth values, and so was every other
      `check_*`; it was a FALSE NEGATIVE both ways, and the doc advice to "phrase the caveat
      carefully" was steering authors INTO the blind spot (ruling: `06-DECISIONS-LOG.md`).
      (2) ⛔ **UNIT-SCOPED EXEMPTION WOULD HAVE LEFT THE GATE BLIND TO THE MOST AUTHORITATIVE SITE
      IN THE TREE** — `04-HANDOFF`'s STATE drift cell is ONE table row of 7,916 chars carrying a
      `*(Superseded …)*` 283 chars from its live claim, so the whole row was exempt. An independent
      agent caught this in my draft; the exemption is now SPAN-scoped, guarded by `--self-test` D17.
      (3) the authoritative `Expect …: N differing` line lives INSIDE a fence, and `_read()` blanks
      fences — the gate could not see the one line the spec says must carry a digit. Pass 2 now
      reads raw text.
      ✅ **17 fault tests shipped (D9–D22)**, firing tests AND false-positive controls: the
      recursion hazard (a stale figure quoted in prose ABOUT the problem), retraction parentheticals,
      and the measured English false positive (`"TWO unbound reads, not one"`).
      ‼‼ **AN ADVERSARIAL REVIEW OF THE FIRST DRAFT FOUND TWO BYPASSES, BOTH REPRODUCED BEFORE
      FIXING** — every exemption had bound to the NEIGHBOURHOOD of a figure instead of to the
      figure itself, so an innocuous aside containing the words `read`/`until`, or a marker
      retracting a DIFFERENT earlier number within 120 chars, silenced a live claim. Exemptions are
      now claim-bound (marker must PRECEDE the figure; outside a parenthetical it stops at the
      sentence break). D20/D21 are those bypasses, D15/D22 the controls. ⚠ Cross-pass dedup was
      added too — one claim, one finding.
      🔜 **The REDUCTION half was always separate and is now its own item — `#24-driftreduction`.**
      *(Original filing and derivation follow.)*
      ⬆ **PROMOTED TO NEXT ITEM 2026-08-17: THE EVIDENCE IS NOW OVERWHELMING
      AND THE FIX IS A GATE, NOT A HABIT.** On 2026-08-17 the figure flipped 0→1→0→1→0 again, and
      **THREE separate stale drift claims survived my own sweeps** and had to be caught by three
      different audit agents — one of them sat in THE 60-SECOND VERSION, the block written for a
      reader who reads nothing else, telling the next session to ask the user for a ruling already
      given and executed. ‼ **`audit_doc_consistency.py` exits 0 over ALL of them.**
      ⛔ **BUT BE PRECISE ABOUT WHY — corrected 2026-08-17 after an audit read the gate's source:**
      **WORD FORMS ARE ALREADY HANDLED** (`_WORD_NUMBERS` includes `zero`; `_NUM` interpolates it
      into all seven drift patterns, `re.I`). What is genuinely open is **CLAIM-SHAPE** detection:
      the rule is scoped to an EXPECTATION, so `0 as of <date>` and `NOT ZERO` — assertions with no
      `expect` nearby — slip through. ‼ Do NOT re-implement word forms; you would be rebuilding
      working code, which is the defect this very item exists to prevent.
      ✅ **THE DELIVERABLE IS A GATE EXTENSION, and it is cheap:** teach `audit_doc_consistency.py`
      to (a) find EVERY sentence asserting a drift figure, WORD FORMS INCLUDED, and (b) compare each
      against the MEASURED figure from `promote.py`'s own logic. ⛔ **FAULT-TEST IT BOTH WAYS** — prove
      it fires on a stale claim AND that it does NOT fire on a clearly-marked historical one, because
      this file is full of deliberately-preserved past figures and a gate with false positives would
      be bypassed within a day (the project's own rule). ‼ Note the recursion hazard already
      recorded below: the gate red-flagged the ORIGINAL draft of this very bullet.
      *(Original filing:)* **NEW 2026-08-16, from MEASURED churn: the docs assert the absolute
      sandbox→custom drift NUMBER in ~10 places, so EVERY sandbox edit invalidates all of them.**
      In this session alone the figure went **0 → 1 → 0 → 1 → 0 → 3**, and each flip cost ~13 hand
      edits across 4-5 files. ‼ Twice a survivor was missed: once because the stale
      figure was written with a CAPITAL initial and the sweep pattern was lower-case only, once
      because the sweep was piped through `cut` and the match sat off the right-hand end of a long
      table row. *(⚠ Both are DESCRIBED, not reprinted — `audit_doc_consistency` matches literal
      strings and cannot tell a quotation from a claim. It red-flagged the first draft of THIS
      BULLET, which is the failure mode demonstrating itself.)* **The cost is not the typing — it is that a
      13-site hand sweep RELIABLY misses one, and a stale drift figure sends a rollback to the wrong
      commit.**
      ⇒ **THE FIX IS STRUCTURAL: assert the number in ONE place and make every other site point at
      the command.** The docs already say *"MEASURE, don't trust this row — `promote.py --check` is
      the authority"* and then print the number ten more times anyway. Keep the STATE table row (it
      is where a cold start looks) and the HOW TO RUN `Expect:` line (it is a grading claim);
      everywhere else should say *"run `promote.py --check`"* with no digit.
      ✅✅ **HALF DONE 2026-08-16 — THE GATE HALF.** `audit_doc_consistency`'s drift check now also
      matches **`promote.py --check`'s OWN OUTPUT FORMAT** (`N differing`), which was its blind
      spot: a stale `0 differing` had survived a 13-site hand sweep AND the gate. ‼ Adding the
      rule **immediately surfaced THREE MORE stale expectations** the same sweep had missed, all
      buried in very long STATE-table rows. ⛔ Scoped to an EXPECTATION (`expect`/`expects`/
      `expected` within ~70 chars) so a HISTORICAL measurement stays quiet — fault-tested in all
      three directions (D6 fires, D7 quiet, D8 quiet-on-history).
      ⛔⛔ **REFUTED 2026-08-17 — "no longer a correctness risk" IS FALSE.** The figure flipped
      0→1→0→1→0 and **THREE stale claims survived hand sweeps AND the gate**, each caught by a
      different audit agent. ‼ **STRUCTURAL, not random:** the 2026-08-16 rule is scoped to an
      EXPECTATION (`expect`/`expects`/`expected` within ~70 chars) and all three were **CLAIMS** —
      `0 as of 2026-08-16 (LATEST)` (STATE cell), `NOT ZERO … a ruling is owed` (a NEGATION), and
      `it is **1** again as of 2026-08-17`. ⇒ **THE REMAINING GATE WORK IS CLAIM-FORM DETECTION**
      (word forms, capitals, long table-row tails), compared against `real_drift()`.
      ⛔⛔ **RULE THE NEGATION QUESTION FIRST — THE DOCS POINT BOTH WAYS.** `04-HANDOFF` calls
      `NOT ZERO` a MISS to fix; its STATE table records the gate FIRING on that phrasing as a FALSE
      POSITIVE. Likely answer: *PARSE the negation and evaluate it as a claim (`drift ≠ 0`), never
      pattern-match the token* — but that is a RULING: put it in `06-DECISIONS-LOG.md` before coding.
      ‼ **FAULT-TEST THE RECURSION HAZARD:** the gate red-flagged the original draft of this very
      bullet, and this file is now full of *descriptions* of stale figures. A gate that cannot stay
      quiet on prose ABOUT the problem gets bypassed within a day.
      🔜 **THE REDUCTION half is SEPARATE and NOT this item's deliverable** — split out below as
      `#24-driftreduction` on 2026-08-17 so it cannot orphan (the `#24-orphans` lesson).




## ARCHIVED 2026-08-22 from `03-PUNCH-LIST.md` — `#24-faintchooser-fourthspace` (CLOSED)
> Moved VERBATIM for the R3 line budget during deep sanity check PASS 5, which measured the
> punch list at 3,593 of 3,600 lines — 7 free, i.e. the next doc edit would have failed Tier 0
> and blocked a commit mid-session. ⛔ Nothing was deleted or reworded. The item is CLOSED
> (probed, answered, the anomaly is INERT); its stub in `03-PUNCH-LIST.md` keeps the one rule
> later work leans on. Its own content begins immediately below.

### `#24-faintchooser-fourthspace` — a POSSIBLE FOURTH INDEX SPACE in the faint chooser (filed 2026-08-17)

- [x] **✅ PROBED AND ANSWERED 2026-08-17 — NO FOURTH INDEX SPACE IS DEMONSTRATED. The anomaly is
      INERT on the only trajectory we can produce. ⛔ DO NOT "FIX" IT.**
      **The probe:** `--driver ki66faint` gained OBSERVE-ONLY instrumentation — **zero production
      change**, everything captured by rebinding module globals `battle_handler` looks up at call
      time (`get_party_menu_cursor_pos` at `:741`, plus `press_button`).
      **RESULT (fixed code, the one diverging faint available):**
      `menu_order=[1,3,4,5]  diverge=True  accepted=3  accepted_in_menu_order=True`
      ⇒ **H0**: the last cursor the SWEEP read before the menu closed IS in `alive_slots_menu`.
      The suspected double conversion does not manifest. Same shape as the OWNER filter: real in
      the log, inert in behaviour.
      ✅✅ **POSITIVE CONTROL — and it earned its keep.** Against the PRE-FIX build the same probe
      recorded `cursor_reads=66, A-presses=239 (select=152 dismiss=87)`, proving the instrument CAN
      see. ‼ **CITE THE `.harnesslog.txt`, NOT THE `.stdout.txt`** — stdout is TRUNCATED on the abrupt
      exit and does not contain that line; the harness's own log does. ‼ It was run precisely because the first fixed-code result was `cursor_reads=0,
      A-presses=0` — which turned out to be **an instrument bug, not a finding** (see below).
      ⚠ **KNOWN LIMITATION, STATED SO NOBODY GRADES ON IT:** the refusal count is APPROXIMATE.
      Presses are counted via `context.emulator.press_button`, which sees every press while the
      party menu is up — including `scroll_to_party_menu_index`'s, in `menuing.py`, which is NOT
      wrapped. The run recorded 129 "select" presses against only 5 sweep cursor reads, so most
      were not sweep attempts. **Only the ACCEPTANCE clause is graded.**
      ⚠ **n = 1 diverging faint, one deterministic trajectory** (repeat runs are byte-identical, so
      that is a determinism check, NOT replication). The pre-registered rule was satisfied
      (≥1 faint printing `[orders DIVERGE]`), but a second INDEPENDENT trajectory would strengthen it.
      ⛔⛔ **DISCLOSURE — THE ACCEPTANCE CRITERION WAS RELAXED MID-INVESTIGATION, AFTER seeing the
      control's output. Read this before trusting the verdict.** The probe first required
      `in_set AND refusals == 0` for H0. It was relaxed to `in_set` alone once the press data showed
      the refusal count is unusable (129 "select" presses against 5 sweep cursor reads ⇒ most presses
      come from `scroll_to_party_menu_index`, which is not wrapped). ‼ **That is a legitimate reason
      and it was still discovered AFTER the fact, so it is disclosed rather than buried.**
      ✅ **THE VERDICT DOES NOT DEPEND ON IT.** The decisive faint reads `in_set=True, refusals=0`,
      which is **H0 under BOTH the strict and the relaxed rule**. The relaxation only re-labels the
      PRE-FIX CONTROL arm (`in_set=True, refusals=5`: H1 under the old rule, H0 under the new) — and
      that arm is a control, not the result. *(An adversarial review caught the undisclosed change;
      it was right to.)*
      ✅ **THE STRONGEST BEFORE/AFTER, which the first write-up omitted:** on the SAME diverging faint,
      **refusals fell 5 → 0 and attempted fell `[2,4,5,0,1,3]` → `[3]`** between the pre-fix and fixed
      builds. One attempt instead of six. That is a better argument for the `_on_field` fix than the
      instrument-liveness numbers, and it is now recorded rather than left in a raw log.
      ⚠ **AND THE PRE-FIX CONTROL'S SECOND FAINT, also omitted at first:**
      `menu_order=[4,5] diverge=False attempted=[4,5,0,1,2,3] accepted=3 accepted_in_menu_order=False`.
      `accepted_in_menu_order=False` is exactly the shape this item worries about — but it is on the
      NON-diverging faint of the BUGGY build, where `alive_slots` is wrong for the unrelated
      `_on_field` reason, and production's own fallback (`:757-758`) is what widened the set. Marked
      INCONCLUSIVE by the pre-registered rule. ‼ Recorded so nobody discovers it in a raw log and
      thinks it was hidden.
      ⚠ **RESIDUAL OBSERVATION, UNPROVEN:** the strategy nominated party index **2** (Mightyena) while
      the mon actually sent out was **Swellow** (cursor 3). Legal, alive, and sensible — but not the
      nominated mon. Not investigated; recorded so it is not lost.

      *(Original filing, kept for the reasoning:)* **Not a confirmed bug — a MEASURED ANOMALY that needs its own probe.** After KI-66's
      `_on_field` fix, the chooser's own diagnostic reads:
      `alive_slots=[2,3,4,5](party-order) -> [1,3,4,5](menu-order)  [orders DIVERGE]`
      i.e. `_to_menu_order` maps slot **2 → 1**, so the cursor sweep's candidate set
      (`alive_slots_menu`) does **not** contain slot 2 — **the very slot the strategy chose**
      (`CHOSEN new_lead_index=2`). The run still resolved (~89 frames, battle WON), so this is not
      currently costing a wedge.
      ‼ **WHY IT IS SUSPICIOUS:** `party_in_menu = get_party()` is read while the party menu is
      OPEN, i.e. after `UpdatePartyToBattleOrder` has permuted `gPlayerParty`. If those indices are
      already in battle order, then mapping them AGAIN through `map_battle_party_index` (which
      expects an *outside-battle* index, `battle_state.py:343`) is a second conversion of an
      already-converted value. That is the same shape as KI-18, KI-34 and KI-66.
      ⛔ **DELIBERATELY NOT CHANGED.** This is PRE-EXISTING KI-34 machinery that has been shipping,
      the evidence is one trajectory, and reasoning about index spaces in this function has been
      wrong three times already. ⇒ **First deliverable is an OBSERVE-ONLY probe** (the pattern that
      settled KI-66's direction in one run): log cursor, `alive_slots`, `alive_slots_menu` and the
      chosen slot together, on a faint, and establish ground truth from the party dump.
      ⚠ Do NOT "fix" it from the docstring — that docstring has now produced three bugs.



## ARCHIVED 2026-08-22 from `03-PUNCH-LIST.md` — three CLOSED historical blocks (PASS 5)
> Moved VERBATIM for the R3 line budget. All three are fully closed (zero open markers,
> verified by script before the move). ⛔ Nothing was deleted or reworded; each left a
> one-line stub in place. They are batch-review history from 2026-07/08.


<!-- 38 lines, verbatim -->
### ~~READY TO APPLY THE MOMENT BATCH `20260802-160603` LANDS~~ — ✅ APPLIED; header stale
> Closed by triage 2026-08-10. That batch landed on 2026-08-02 and the item below shipped;
> the heading sat here for eight days implying pending work that did not exist.

- [x] `#24-leadcounter` — ✅ **CLOSED 2026-08-10 by triage: it SHIPPED and this entry was stale.**
      Verified in code: `team_policy.lead_rank_key(..., is_hunted_counter: bool = False)`
      (`team_policy.py:263`) and `early_game.py:1712/1735` compute and pass it. It also has a
      recorded post-ship bug (`08-MISTAKES` 2026-08-03 — it was silently dead for two batches),
      which is further proof it was applied. HISTORY — **USER RULING 2026-08-02: super-effectiveness outranks raw level
      ONLY for a mon the counter chain caught for THIS boss.** Not a general rule (that option
      was offered and declined; so was the level-gap variant, which is option (b) of
      `#24-leadpolicy` and was already ruled out). Rationale + rejected alternatives in
      `06-DECISIONS-LOG.md` 2026-08-02.

      **THE EXACT CHANGE:**
      1. `team_policy.lead_rank_key()` gains an OPTIONAL `is_hunted_counter: bool = False`,
         and the key becomes:
         ```python
         (glass_wonder_guard, not can_attack, incoming, not is_hunted_counter, -level)
         ```
         ‼ **AFTER `incoming`, BEFORE the level tie-break.** It promotes the counter over an
         EQUALLY SAFE mon; it must never let a 4×-weak counter lead. Getting this backwards is
         the plausible way the fix becomes a new bug — `repro_lead_hunted_counter.py` check 3
         pins it.
      2. `best_lead_index()` passes the candidate's `is_hunted_counter` through.
      3. Record WHICH mon was hunted for this boss. `StoryMode._counter_hunts[key]` already
         tracks the attempt; store the caught mon's **PID/personality value**, not its slot —
         a party index goes stale the moment anything reorders or deposits (the same hazard
         `pc_trip` guards against).
      4. `early_game._lead_best_matchup()` takes an optional `hunted_pid=None` and sets the
         term for the matching party mon; the Norman/Wattson/Winona prep passes it.
      5. `repro_lead_hunted_counter.py` goes green (currently RED by design). Re-run the suite.

      **Why it matters:** batch5 caught, travelled for and trained a counter to L29 and then
      led **Marshtomp L35** instead, because Machoke and Marshtomp tie on every term the key
      measures and level breaks it. The chain only fires after ~6 losses, so for that boss the
      strongest mon is already PROVEN insufficient.


<!-- 25 lines, verbatim -->
### ‼ BATCH 5 LANDED — the blocker moved a THIRD time, to the LEAD

- [x] `#24-leadpolicy` — **A+C BUILT 2026-08-01.** Pure `team_policy.lead_rank_key()` /
      `best_lead_index()`; `_lead_best_matchup` defers to it. Sort terms not filters (a lone
      Shedinja is still led); both predicates fail SAFE. Option (b) NOT ruled, NOT built —
      `repro_lead_policy.py` check 4 pins the unchanged Whismur-over-Marshtomp behaviour.
      ‼ **MEASURED LIMIT (check 5): this does NOT field the trained counter.** On batch5's
      real party it stops the Shedinja lead and then picks **Marshtomp L35 over Machoke
      L29**, because `can_attack` is binary and 2× STAB earns no credit. **OPEN DECISION —
      should super-effectiveness outrank raw level? That is a NEW question outside A+C and
      is the last link in the chain.** Original diagnosis below.

      `#24-leadpolicy` — **the counter chain's blocker as of batch5. Ruling A+C.** Batch5 proved the chain works end to end — 7 of 9 counters trained,
      `Machop L15 -> L29` evolving to **Machoke** — and then **MACHOKE WAS LED INTO NORMAN
      ZERO TIMES**. Leads chosen: SHEDINJA ×9, MARSHTOMP ×4, SWAMPERT ×4, BLAZIKEN ×2.
      `_lead_best_matchup(["Normal"])` scores `min(incoming_multiplier, -level)`, so Shedinja
      (Bug/Ghost, Normal → 0×) always wins and the trained counter sits in the bag. The entry
      below PREDICTED this exact batch. Catching and training a type counter and then not
      fielding it is the cost of the whole chain with the benefit of none of it.
      **Build (a) require the lead to also have a ≥neutral attacking option + (c) special-case
      1-HP Wonder Guard mons.** ‼ Then size expectations before re-measuring: the chain fires
      on only ~10 of 29 Heat-reaching runs, so even a perfect fix moves the overall
      Heat→Balance rung 79% → ~93% AT BEST. Use the **counter-hunt-runs-only** conditional as
      the instrument (batch4 5/9 → batch5 6/10, z=0.20 — the whole-batch rung dilutes it 3:1).


<!-- 27 lines, verbatim -->
### ‼ BATCH REVIEW 2026-07-26 (bundle `20260726-231412`) — two catastrophic bugs found & FIXED
The x4 bundle showed the batch was **silently producing almost no usable data**, while
reporting most runs as successes. Both root causes are fixed in sandbox with A/B repros.

- [x] `#24-x4-staleslate` — **per-run state never reset between runs.** DONE 2026-07-26.
      `StoryEndlessResetMode.run()` loops on the SAME mode object, so `StoryMode.__init__`
      ran once per BATCH — under a comment asserting the opposite. Measured effects:
      `_rival_attempts` (cap 3) tripped on run 4 in every lane, so **runs 4+ quit at the
      Rustboro rival without fighting** (16/20 P1, 6/9 P2, 5/8 P3 — P1 run 8's log has ZERO
      lost battles yet reports "couldn't beat the rival in 3 tries"); `_defeat_counts`
      carried losses across runs (MT_CHIMNEY #7→#8, FORTREE #8→#9), so boss give-up
      thresholds fired on borrowed defeats — P4 run 2 derailed as "6 losses" after 3.
      FIX: `StoryMode.reset_per_run_state()`, called per run by the endless loop.
      REPRO: `tools/story-dev/repro_endless_per_run_state.py` (A: FAIL on HEAD → B: PASS).
- [x] `#24-x4-honestoutcome` — **failed runs reported as "finished".** DONE 2026-07-26.
      `outcome` defaulted to `"finished"`; only a raised `BotModeError` changed it, but a
      derail can instead call `set_manual_mode()` and return normally. All 16 P1 "finished"
      runs were dead (several "finished (0 frames)"). A batch summary read ~80% success
      against a true ~20%. FIX: a `try/except/else` that detects the hand-to-Manual exit and
      reports `stopped:`. Covered by the same repro.
- [x] `#24-x4-runindex` — **`run_index` still advanced by 2 per run.** DONE 2026-07-26.
      The previous adjacency-based dedupe could never work: the mode signals BEFORE
      `super().run()` while the hard reset happens INSIDE it, so thousands of polls separate
      the two calls. FIX: ownership — `reset_for_new_run(..., authoritative=True)` makes
      main.py's frame-counter fallback stand down.
      REPRO: `tools/story-dev/repro_badgelog_run_index.py`.



## ARCHIVED 2026-08-23 from `04-HANDOFF.md` NEXT ACTIONS — the §Ch20 build-spec detail and the
## "older framing" retractions (CLOSED)
> Moved VERBATIM for the R3 line budget at the end of the 5-pass deep sanity check: `04-HANDOFF.md`
> stood at 897 of 900, i.e. the NEXT session's first doc edit would have failed Tier 0 and blocked a
> commit mid-wrap-up. ⛔ Nothing deleted or reworded. **Verified before the move:** the three
> load-bearing rules it carries (ROCK SMASH is mandatory; the trigger tile is `(17,42)` not
> `(16,42)`; grade on `VAR_ROUTE128_STATE == 2`) each still appear ELSEWHERE in `04-HANDOFF.md`,
> and the full spec lives in `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md`.

>    `ai-research-notes/2026-08-13-ch20-seafloor-cavern-build-spec.md` — an 11-leg list, each with an
>    assertable condition, from a decomp recon that ran an exhaustive Sokoban search over
>    (player × boulder) states. ✅ It independently agrees with our own `probe_ch20_interior.py`.
>    **Its three corrections to what we believed:**
>    1. ‼ **ROCK SMASH IS MANDATORY, not just Strength** — a Strength-only party is *physically
>       stuck in Room 1* (`(5,10)` is a breakable rock and the only way into the row-11 corridor).
>       We have both on Sceptile; the chapter must ASSERT it in pre-flight.
>    2. ⛔ **The trigger tile is `ROOM9 (17,42)`, not `(16,42)`** — corrected in this file and in
>       `story_mode.py`. `(16,42)` is plain floor; upstream's solver stops one tile short of it.
>    3. ⛔ **Grade the chapter on `VAR_ROUTE128_STATE == 2`, NOT on the Kyogre flag.** The flag is set
>       BEFORE a forced `warp MAP_ROUTE128, 38, 22` that immediately starts a SECOND `lockall`
>       cutscene — so a flag-graded chapter reports success while the bot is inside two nested
>       scenes. ‼ And `(38,22)` is a shallow-water **SANDBAR**: the bot lands on an island and must
>       **Surf** off it. Three chapters have shipped stranded; this one strands you by design.
>    ✅ **THE BIGGEST UNKNOWN IS NOW ANSWERED AT THE PLANNING LEVEL (2026-08-13):**
>    `probe_ch20_currents.py` (NEW) put **4 pre-registered predictions** to our REAL planner on the
>    two current mazes and got **4/4, including the DISCRIMINATING one**: `ROOM6 (11,21)->(4,1)`
>    routes, and **`ROOM6 (4,1)->(11,21)` correctly FAILS** — our planner reproduces the currents'
>    ONE-WAY asymmetry independently of the decomp note. ⚠ **BUT AN AUDIT CORRECTED HOW MUCH THAT
>    PROVES (KI-76):** our one-way result comes from an **INVENTED entry mask** (we forbid entering a
>    current head-on against its flow) — the decomp imposes **no entry restriction on currents at
>    all**. The mask is benign and reachability-equivalent here, so the CONCLUSION holds, but
>    "independently reproduced the game's asymmetry" **overstated it**. ‼ **And the slide model is PROVEN in use, not assumed**: P1 emits 13
>    waypoints for a 27-tile Manhattan trip and P4 emits 12 for 24 — impossible with 1-tile steps.
>    ‼ **Measurable from outside the cavern ONLY because Rooms 6/7 have ZERO objects** (so the
>    `active_objects` artifact that invalidated the boulder rooms cannot apply here).
>    ⇒ **Rooms 6/7 can be driven with `navigate_to`; they do NOT need a §Ch18-style solver.**
>    ✅ **KI-76's SAFETY HALF IS FIXED (2026-08-13) and its cap is now PROVEN (2026-08-17):** the
>    512-step cap fails LOUD (fault-tested at cap=3), the four `None` unpacks are guarded, and
>    production has since followed EVERY cross-map chain on ONE shared budget — cap never fired,
>    nothing cycles, longest chain **77** (margin 6.6x). ⛔ The old "32 tiles / ~16x / Routes
>    132-134 UNMEASURED" wording here was stale on all three counts.
>    ‼ **KI-76's CORRECTNESS HALF IS STILL OPEN — and as of 2026-08-17 it finally has its OWN item,
>    `#24-ki76correctness` (`03-PUNCH-LIST.md`). ⛔ ALL numbers, the priority ruling and the
>    startable next action live THERE; they are deliberately not copied here.** Headline only: the
>    two defects are armed in DIFFERENT places (dismount 1,852 chiefly on the routes; ends-on-warp
>    **9, all in ROOM6, zero on the routes**), so KI-76's old single-claim header was half backwards.
>    ✅ **SUPERSEDED 2026-08-13 — the executor HAS now crossed a current** (`--driver ch20room6`,
>    `crossed=True`). Only the tile-by-tile slide model remains unverified.
>    ℹ Upstream `puzzle_solver.py:405` DOES `navigate_to(ROOM6, (4,1))` and its wiki marks the
>    Seafloor Cavern ✅ for Emerald — the strongest available signal that the executor can do it,
>    and still a third-party claim, not evidence.
>    Also: **puzzle state RESETS on every map re-entry** (`FLAG_TEMP_*`), so never cache "solved";
>    `FLAG_SYS_USE_STRENGTH` by contrast persists. **Losing to Archie resets the whole dungeon.** It IS the ladder
>    (`chapters.py:233`, graded `KYOGRE_ESCAPED_SEAFLOOR_CAVERN`; `story_mode.py:3654` = END OF BUILT
>    CONTENT — ✅ **that line was ALREADY FIXED** — it now reads "KI-63 IS RESOLVED"; the string "BLOCKED BY
   KI-63" does not occur in that file. This instruction is retired, 2026-08-13). Uniquely
>    de-risked: the dive leg is **driven 6/6**, KI-63 is wired in sandbox, and `puzzle_solver.py`
>    hands you room coordinates free. Blast radius is **additive** — one module, one segment, no
>    shared code. Two cheap traps: apply **KI-72** (hand-pick the surfacing tile, assert its
>    `tile_type` — never let the planner choose), and ⛔ **THE TRIGGER TILE IS `ROOM9 (17,42)`, NOT
>    `(16,42)`** — corrected 2026-08-13, `(16,42)` is plain floor and fires nothing. It is
>    Archie's cutscene tile — the standing rule is *"and the bot can continue"*.
>    **(iii) `#24-r110mauville` / KI-48** — the highest-frequency OBSERVED defect (72 events in one
>    batch, 3/3 deterministic). Budget a MEASUREMENT; its root cause is still a hypothesis.
>    **(iv) THEN the Regi arc.** ‼ Its real cost, measured: **10 missing gates and ~7 subsystems that
>    do not exist** (fishing as a story capability — `fish()` has zero story callers and rod choice
>    is a **human GUI prompt**; underwater encounters — `EncounterType` has no Underwater member; TM
>    acquisition + `use_tm`; Flash acquisition; a no-KO/no-whiteout legendary policy; a **bounded**
>    exact-tile executor; and **no chapter entry at all**), behind a hard 9-step serial prefix.
>
> 4. ⛔ **NOT NEXT — OLDER FRAMING; a Tier 2 audit flagged that a skimmer could start the Regi arc
>    from here. The live queue is item 0 and its head is **(P4c) `#24-orphans`**. Background only.**
>    **The REGI arc (user-requested) — read KI-69 ‼ AND ITS NEW STUB MARKER.**
>    ⛔ **REGICE IS NOT A TIMED WAIT** — R/S's wait function is an empty stub; Emerald wants a
>    **36-tile perimeter lap in ONE visit** ending exactly on `(8,21)`, reset by any map transition
>    and by one wrong tile. Full ground truth:
>    `ai-research-notes/2026-08-13-regi-arc-decomp-ground-truth.md`. ‼ **WAILORD first, RELICANTH last** (Emerald
>    reversed it; the wrong order fails silently). ‼ **The Regi battle is UNRECOVERABLE** — a KO *or*
>    a whiteout deletes the encounter; only fleeing is safe. Phase A is measured: we have Go-Goggles,
>    HM08, Surf and Rock Smash; we have **no rod at all**, no TM28 Dig, and nobody knows Dive, Dig or
>    Flash. **Relicanth is underwater-only, so Dive (item 3) is upstream of the whole arc.**
>

> ⛔ **THE "OLDER FRAMING" TAIL OF THIS QUEUE — MOVED to `28-HANDOFF-ARCHIVE.md` (2026-08-17).**
>    *(Numbered 2b-5 inside its own block; ⚠ that numbering does NOT refer to the items 3/4 still
>    visible ABOVE, which are LIVE.)* These were the
>    "older framing" the queue header already flagged, and every one of them is now DONE or RETRACTED:
>    2b's Dive/`POKEBOT_BOX_OVERFLOW_CATCH` gate (false since 2026-08-07, and §Ch20 is DRIVEN END TO
>    END anyway), 3's KI-59 fix (**DONE and GATED** as `repro_impassable_dirs.py`), 4's promotion
>    (**already happened** 2026-08-12), and 5's "skim `08-MISTAKES.md`" (now a standing rule in
>    `CLAUDE.md`, not a queue item). ‼ **Nothing was deleted** — read the archive if you need the
>    measurements behind any of them.


## ARCHIVED 2026-08-23 from `03-PUNCH-LIST.md` — `#24-sanitycheck`, the 5-PASS DEEP AUDIT (COMPLETE)
> Moved VERBATIM for the R3 budget: the punch list hit 3,626 of 3,600 while filing
> `#24-abortrecoveryresiduals`. The audit is COMPLETE (all five passes done and committed) and
> nothing in it is a live instruction. ⛔ Nothing deleted or reworded; the stub keeps the METHOD,
> which is the part later work reuses.

### ✅✅ `#24-sanitycheck` — the USER-REQUESTED 5-PASS DEEP AUDIT — **COMPLETE, 5 of 5** (filed 2026-08-18, closed 2026-08-23)

- [x] **✅✅ ALL FIVE PASSES ARE DONE AND COMMITTED. ⛔ DO NOT RE-RUN ANY OF THEM.**
      ‼‼ **THIS LINE SAID "3 of 5" AND THEN "4 of 5" AFTER EACH PASS SHIPPED — THE SAME MISS, TWICE,
      ON THE SAME ITEM, IN ONE SESSION.** Both times the handoff's two halves were updated correctly
      and this third copy was not; the second time it was caught by the **P5 pair added to
      `CLAUDE.md` because of the first**. ⇒ the pair works, and it is the reason this file is now
      right. ⛔ **On finishing an item, `grep` the tree for its own slug and re-read EVERY hit.** ⛔ Filed because a cold-start audit found the queue head pointing at work with **no
      punch-list item at all** — the exact `#24-orphans` shape, and it also meant three commits went
      in without a `(punch-list #N)` tag as DoD step 5 requires.
      **DONE:** pass 1 TRUTH `045bdd1c`, pass 2 CODE HEALTH `e74d6e50`, pass 3 ADVERSARIAL `899f4ce7`.
      ‼‼ **THE METHOD IS THE DELIVERABLE — copy it exactly, it is what made the passes work:**
      **8 agents per pass, ONE ANGLE EACH, sent in ONE message so they run concurrently, and EVERY
      agent required to FAULT-INJECT or RE-DERIVE, never to reason.** That single instruction is what
      found a gate that could not fail and a control that could not fail; the earlier habit of asking
      an agent to *assess* something produced opinions instead.
      ⛔ **VERIFY EVERY FINDING YOURSELF BEFORE ACTING — 2 of ~40 were FALSE POSITIVES** (a truncated
      quote; a correctly-superseded duplicate). An agent report is a NOTE, never truth.
      ‼ **Output contract that kept them readable:** one verdict line, then `SEVERITY | what | what
      you RAN | result | smallest fix`, max ~16 lines, and *anything not executed must be labelled
      CANNOT-REPRODUCE*.
      ✅✅ **PASS 4 IS DONE 2026-08-22 (`42a2d844`) — ⛔ DO NOT RE-RUN IT.** Its lead was right and
      UNDERSTATED: not "9 of 11 sampled" but **21 of 28 gates had no self-test**, and THREE of them
      (`probe_slot_free_plan`, `probe_regi_capabilities`, `probe_dive_routing`) had **zero assertions
      and could not fail at all**. Residuals filed as `#24-fixturecoverage`, `#24-gateselftests`,
      `#24-testrunsweep`, `#24-p4residuals`, `#24-flagnamedocscan`. ✅ KI-82 is CLOSED — it was already
      ruled on 2026-07-18 and was re-affirmed 2026-08-23; ⛔ do not re-raise it.
      ✅ **PASS 5's SCOPE WAS DEFINED AND EXECUTED 2026-08-22/23 — it is on the record so the audit is
      REPRODUCIBLE.** It had none when filed. The eight angles run, one agent each: cold-start from
      the handoff; cold-start from `00-README`; can each filed "startable" item actually be started;
      playbook currency; known-issues navigability; punch-list navigability;
      `24-PLAIN-ENGLISH-STATUS` accuracy; vision/architecture vs reality.
      ⛔ **EIGHT ANGLES, SEVEN AGENTS RETURNED** — the eighth died on an API session limit and was
      RE-RUN the next day, where it produced 17 findings including six commands in
      `02-ARCHITECTURE.md` that could not be run as written. ⇒ **report the angles that RETURNED,
      never the number LAUNCHED.**
      ⚠ Pass 1 agents were READ-ONLY; passes 2-3 executed and fault-injected in scratch. ⛔ Whichever
      you choose, say so in the prompt — and ⛔ do NOT let an agent copy a whole fork to scratch.



## ARCHIVED 2026-08-23 from `03-PUNCH-LIST.md` — five CLOSED items (R3 budget)
> Moved VERBATIM after the punch list hit its 3,600-line limit. Each was script-verified to
> contain ZERO open markers before the move, and each left a one-line stub in place.
> ⛔ Nothing deleted or reworded.


<!-- 38 lines, verbatim: - [x] HISTORY  `#24-rarepredicate` (original spec, 2026-08-06)  **the du -->
- [x] HISTORY — `#24-rarepredicate` (original spec, 2026-08-06) — **the duplicate-catch exemption (`#24-roster` ruling 3). SOLVED — the
      "pseudo-rare" axis is WARP DEPTH, and it needs no new recon.**
      Three OR'd rules: shiny (already works) / rare gender variant / rare species.
      **Rare species = `best_slot_rate <= 4%` OR `warp_depth >= 3`** — 26 of 132 wild species (19%).

      **WARP DEPTH** = 0-1 BFS over the committed `cache/warp_graph_BPEE0.json`: seed every
      non-underwater group-0 map at 0, connection edges cost 0, **warp edges cost 1**, take the MIN
      over all of a species' locations. Histogram (independently reproduced 2026-08-06):
      `d0=59 d1=21 d2=39 d3=7 d4+=3 d99=3` (d99 = no path = **Dive**-gated, deliberate — Dive edges
      are excluded at `warp_graph.py:20`). **`depth>=3` = 13 species, ZERO false positives on
      inspection.** Bagon = **d3** (METEOR_FALLS_B1F_2R, Surf+Waterfall); Skitty = d0 (rate rule
      catches it at 2%).
      **Threshold rationale: there is a CLIFF between 4% and 5%** — the 5% Safari slots add 18
      species at once. 4% is the natural stop.

      ‼ **REJECTED: the encounter-METHOD proxy** (a species available only via `surf_encounters` is
      "Surf-gated"). Measured: 27/132 water-only species are the most UBIQUITOUS in Hoenn
      (Magikarp 53 maps, Tentacool 38, Wailmer 33). Surf-gating is TEMPORAL, not rarity — and Bagon
      is Grass-only anyway. Adding this axis takes the set from 26 to 61.
      ‼ **REJECTED: `nmaps == 1`** — 62/132 (47%), half the dex.

      ✅ **The field-move recon is NOT a prerequisite** — decisive. Warp depth is pure graph
      topology off a cache the bot already loads (`get_warp_graph()`), and the predicate fires at
      ENCOUNTER time, when the bot has by construction already cleared the gate. "Where is
      Waterfall first required" is a routing question this filter never asks. (That recon is still
      a real gap for `counter_plan` routing — just not for this.)

      ‼ **KNOWN FALSE NEGATIVES, accepted:** **Feebas is not in the encounter index at all**
      (`encounter_index.py:75-115` reads `gWildMonHeaders`; the 6-tile mechanic is not in that
      table), so the most iconic pseudo-rare species can never fire this rule. Same for Beldum and
      other gift/static/version-exclusives. Pure-sea endgame species (Luvdisc, Corsola, Staryu) are
      structurally d0 and miss. ‼ And the cutoff is fragile at the boundary: Meteor Falls' d2 rooms
      are ALSO Surf-gated in reality, so `>=3` earns some of its precision by luck of Bagon's room
      being one warp deeper. Treat warp depth as a good INFERENCE, not proof of a required HM.
      Traps found: `custom_catch_filters` runs **≥2× per encounter**, so the "do I own this species"
      lookup must be cached, never a 420-slot box scan; and `is_repeat_encounter` is PID dedup, NOT
      species dedup — do not reuse or name anything near it.


<!-- 33 lines, verbatim: - [x] HISTORY  `#24-movepoolcounters` (original measurement)  **USER DIR -->
- [x] HISTORY — `#24-movepoolcounters` (original measurement) — **USER DIRECTIVE 2026-08-07.**
      > "some pokemon can learn moves of types that can be a counter so its not just the pokemon
      > type, it can be the moves they learn… know the difference between damaging moves,
      > passive/defensive/stat boosting/debuff moves and area/effect moves as well as status
      > moves with no damage"

      `counter_plan.py:155-157` today keeps a candidate only if
      `{t.name for t in species.types} & needed` — pure species typing.
      **Measured with `tools/story-dev/probe_movepool_counters.py` over all 11 huntable grounds:**
      | gating | Winona | Norman | Wattson |
      |---|---|---|---|
      | by species TYPE (today) | 1 | 1 | 1 |
      | + any learnable move of a needed type | +82 | +47 | — |
      | **+ DAMAGING, LEVEL-UP only, power×2.0×STAB ≥ 75** | **+2** | **+0** | **+0** |
      ‼ **The naive version is WORSE THAN TODAY.** Almost the entire raw gain is `TM13 Ice Beam` /
      `TM14 Blizzard` (Gen 3 TMs are single-use and we almost certainly do not own them) and
      `HM06 Rock Smash` at **20 power** — the exact case `CREDIBLE_ANSWER_POWER = 75` was
      calibrated to reject ("a 20-power HM is 2.0x against Normal and still loses to Slaking 27
      times running"). Unfiltered, every Zigzagoon becomes a Norman counter.
      **THREE GATES ARE MANDATORY, in this order:**
      1. **DAMAGING ONLY** — `move.base_power > 0`. Everything at 0 is status / stat-change /
         field effect and cannot answer a type weakness: Toxic, Growl, Sunny Day.
         ‼ **Smog is NOT in that group** — our data has it at **20 bp Poison, `effect=POISON_HIT`**.
         Classify on `base_power`, never on the name or on the presence of a secondary effect.
      2. **OBTAINABLE** — level-up moves within reach of the catch band, or a TM/HM **we own**.
         Never "could learn if we had TM13".
      3. **CREDIBLE POWER** — reuse the existing `power × effectiveness × STAB >= 75`.
      **The whole actionable gain is 2 Winona candidates:** Baltoy learns **Rock Tomb** (L15,
      50bp) on ROUTE111; Slugma learns **Rock Throw** (L15, 50bp) on FIERY_PATH.
      ⇒ Worth building — it is the correct model and it widens a chain that is now **75% of all
      non-finishes** — but it will NOT by itself fix Winona, and it must not be sold as the fix.
      Do `#24-winonaground`'s real diagnosis first.


<!-- 31 lines, verbatim: - [x] `#24-battleitems`   **DONE, PROMOTED 2026-08-10 (user-approved), z -->
- [x] `#24-battleitems` — ✅ **DONE, PROMOTED 2026-08-10 (user-approved), zero source drift.**
      Policy unit-proven (`repro_battle_items.py`, 27 checks, no emulator); a real
      `battle_action_use_item` index-space bug found and fixed underneath it (5 requests → 1
      potion consumed, became 3 → 3); index space proven CONDITIONAL and handled by a
      self-correcting flip; validation batch `20260810-082509` passed its acceptance test
      (flips **20 → 2**, both-spaces-failed **10 → 0**).
      ‼ **OUTCOME UNPROVEN and that is on the record** — finish rate across the four item-era
      batches reads 25.0 → 33.3 → 16.1 → 28.6% at n≈30, nothing resolvable. It was promoted
      because the mechanism is proven and bounded, not because outcomes moved. **Any follow-up
      must be graded on BATTLE-level metrics** (`probe_item_index_space.py`,
      `probe_boss_healing.py`), never the finish rate.
      HISTORY — **USER DIRECTIVE 2026-08-09: "use items intelligently and
      strategically." BUILT, ROOT-CAUSED, FIXED — but its OUTCOME EFFECT IS UNMEASURED.**
      Motivated by measurement: `Slaking` healed **27 times, median +81 HP** in batch
      `20260809-155844` while the bot never used an item; 61.8% of boss-length battles show an
      opponent heal; boss losses end ~88% of non-finishing runs.
      * `modules/story/battle_items.py` — PURE policy (heal amounts from `items.json`, never
        memory). Four rules: only below 35% HP; **cheapest sufficient** item; **never heal into a
        losing race**; **bounded per battle** (the opponent heals too — unbounded is an infinite
        battle, the KI-34 shape). `repro_battle_items.py`: **27 checks, ALL PASS**, no emulator.
      * `StoryItemBattleStrategy` — TRAINER battles only, fails open, so wilds/training/catching
        are bit-identical to before.
      * ‼ **Found and fixed a real bug in `battle_action_use_item`**: it fed a BATTLE-order index
        into a PARTY-MENU scroll, so item use silently did nothing whenever the active mon was not
        at index 0 (5 requests → 1 consumed). After the fix: **3 requests → 3 consumed, Blaziken
        `23/120` → `120/120`**. Ball throwing passes no target and never enters that branch.
      * A **no-op guard** remains: if a request does not raise HP by the next decision, items are
        disabled for that battle (bounds the cost to one turn if execution ever breaks again).
      **NEXT: a batch.** Acceptance should be **boss-battle win rate**, not the finish rate. ‼ Do
      NOT quote the fixture's `badge=True` as proof — it reproduced even when items did nothing.


<!-- 33 lines, verbatim: - [x] `#24-progressiongate` (original finding)   **USER-IDENTIFIED 2026- -->
- [x] `#24-progressiongate` (original finding) — ‼‼ **USER-IDENTIFIED 2026-08-08, VERIFIED. The counter planner has
      NO progression model, and for Wattson it proposes a counter that is behind Wattson.**
      > "I think Slugma is not available before Wattson… keep this sort of logic in mind (pokemon
      > availability). In this instance Slugma is gated behind Rocksmash which you can only use
      > after beating Wattson"

      **Verified with the real `find_counter_candidates`** against a pre-Wattson team (L22):
      ```
      WATTSON needs Ground -> only huntable candidate: Numel @ FIERY_PATH (30%)
      ```
      **That is CIRCULAR.** Fiery Path's only two doors are on ROUTE112; the Mauville→Route 112
      corridor is sealed by a Rock Smash rock at ROUTE111 (18,101) (measured, `#24-smashroute`);
      and Rock Smash **field use requires BADGE03** — Wattson's own badge (`get_rock_smash_hm`
      docstring). So every Fiery Path species — Numel, Slugma, Machop, Torkoal, Koffing — is
      unobtainable until Wattson is already beaten.
      **`FIERY_PATH` has NO entry in `AREA_PREREQ` or `AREA_ITEM_PREREQ`** — confirmed, both
      return `None` — so the planner treats it as freely reachable at any story stage.
      ‼ **`#24-huntreachproof` part 1 made this the ONLY option for Wattson.** Before the
      narrowing he was also offered ROUTE111/ROUTE116 (unreachable in practice, but not
      circular). Now the single surviving candidate is one he gates himself. That is a real
      consequence of my change and it was invisible to every metric I was watching, because
      conversion counts catches and this rung can never even start.
      **FIX:** teach the gate about FIELD MOVES / BADGES. `AREA_PREREQ` already carries a
      vocabulary (`"surf"`, `"region"`) and `_counter_area_allowed` already resolves `"surf"`
      against the party — add `"rocksmash"` (badge-checked) and populate FIERY_PATH, plus any
      other ground behind a field move.
      ‼ **Every entry is a GAME FACT — verify each from the decomp or a live probe, never from
      recall.** The three facts above are already measured and cited; anything added beyond them
      needs the same treatment.
      ‼ **The general rule the user is asking for, beyond this instance:** a counter/hunt target
      is only valid if its LOCATION is reachable AT THAT POINT IN THE STORY. Availability is a
      function of story progress, not just of the encounter table.


<!-- 40 lines, verbatim: - [x] **`#24-counters` phase 2   BUILT 2026-07-30, and LIVE-VALIDATED ma -->
- [x] **`#24-counters` phase 2 — ✅ BUILT 2026-07-30, and LIVE-VALIDATED many times since;
      the "awaiting validation" header was 8 days stale (closed by triage 2026-08-10).**
      Evidence: `best_huntable` (`counter_plan.py:435`) and `hunt` (`counter_hunt.py:426`) are
      live; batch `20260808-131334` measured conversion 15% → 45% (z = +2.39 on REAL catches),
      and `20260809-081643` restored `CAUGHT Machop` 0/7 → 6/7 (z = +3.24) with FALSE catches
      10 → 0. ‼ Its open FOLLOW-UPS live in newer items, not here — see `#24-battleitems`
      and the boss-healing work; the chain's DIAGNOSIS is sound and its premise is what is
      now in question. HISTORY —
      **STEP 1 — the hunting-ground gate** (`hunt_ground_tile` / `huntable` /
      `best_huntable`; `repro_counter_huntable.py`, ALL PASS). Had to land first: the cost
      ranking puts **Victory Road Hariyama at rank 1** for Norman, so an executor built on
      `cands[0]` would have walked a mid-game team into the E4 approach.
      Destinations: Norman → **Machop @ FIERY_PATH (18,19)**, Wattson →
      **Sandshrew @ ROUTE111 (25,55)**, Winona → **Electrike @ ROUTE118 (29,15)**.
      **STEP 2 — the executor.** `modules/story/counter_hunt.py` (arm → hunt → train),
      `StoryMode._counter_ladder`, and a catch-on-sight branch in `on_battle_started`.
      `repro_counter_hunt.py` — **15 checks, ALL PASS.**
      ‼ **Bounded by PER-RUN STATE (`_counter_hunts`), one hunt per boss per run** — a
      retry or frame budget CANNOT bound this, because `_prepare_for_fight` is re-entered
      by the run loop after every lost attempt (the KI-34 shape). The attempt is recorded
      BEFORE the hunt so a derailed hunt still consumes its chance.
      ‼ **The terminal raise is untouched** — every failure path still stops honestly.
      **STEP 2b — destination FALLBACK.** `probe_counter_reachability.py` drove the REAL
      navigation and found the TOP destination UNREACHABLE for 2 of 3 bosses (ROUTE111 is
      Fallarbor-side; ROUTE118 is the KI-24 bridge case) while Norman's FIERY_PATH (18,19)
      **ARRIVED in 2,922 frames**. The ladder now walks the ranked huntable list up to
      `COUNTER_HUNT_MAX_DESTINATIONS = 3`. ‼ Cheap failures cascade, expensive ones do not.
      ⏭ **WHAT IS OWED: a LIVE run.** Nothing here proves the bot can walk to Fiery Path
      from Petalburg, catch a Machop and beat Norman with it. Watch for: does the hunt
      reach (18,19)? does the catch-on-sight branch fire? does `train_counter` accept or
      decline the estimate? and — the regression to fear — does a boss that used to stop
      honestly now loop? Grep new logs for `counter hunt` and `already hunted a counter`.
      Of 36 derails in the newest bundle, **~26 are "boss: N losses with no super-effective
      answer to X. Need one of: Y"** — the chain diagnoses correctly and then ENDS THE RUN.
      Breakdown: Electric→needs Ground ×17, Normal→needs Fighting ×9, Winona ×3.
      `counter_plan.find_counter_candidates` already names reachable species and tiles
      (`story_mode.py:611`, raised at `:1347`); `story_mode.py:619` states plainly that it is
      "PLANNING/LOGGING ONLY — this does not travel, catch, or train anything". Building the
      travel-and-catch step converts ~72% of derails into continued runs. Nothing else on
      this list is close in value.


## 📦 ARCHIVED 2026-08-24 from `03-PUNCH-LIST.md` (R3 budget: 3569/3600, and five research agents were in flight)

> Moved VERBATIM, nothing deleted. Each left a one-line 📦 stub in the punch list carrying its slug,
> its verdict and any LIVE caveat, so a `grep` for the slug still lands and still tells the truth.

---

- [x] `#24-navready-budget` (**KI-43**) — **DONE 2026-07-31.** Fixed via a dedicated
      `_TRANSIENT_WAIT_FRAMES = 600`. Proven twice: `repro_watchdog_budget_collision.py` green
      with a both-ways fault injection, and a live A/B (`gym1_done.ss1 --driver martbuy
      BUYN=30`, 40k frames) — **OLD arm 0 purchases, NEW arm 3 purchases + 3 Premier Balls**,
      money 8628 → 2628. Original diagnosis below.

      **The original diagnosis, kept because it is the evidence:**
      `#24-navready-budget` (**KI-43**) — **`_navigate_when_ready`'s escape hatch is budgeted
      at EXACTLY the watchdog's 18,000 frames, so the `break` is dead code and the derail
      always wins by one frame.** Diagnosed 2026-07-31 from stored logs: 35 of 72 watchdog
      fires are inside `RUSTBORO_CITY_MART` right after `bought Poké Balls`, 31 in
      `LAVARIDGE_TOWN` after the Heat Badge — stationary wedges, NOT the "long journeys"
      the handoff assumed. The mart restock completes **0 of 36** times (baseline 33/33), so
      every restock buys 10 balls instead of 30 and loses 2 free Premier Balls.
      **Fix:** lower the wrapper's cap to ~600 frames (the battle transition it exists for
      clears in a few), so `navigate_to` raises its honest error and `_navigate_riding_out`
      spends a retry. **Prove with a live A/B** — the Rustboro restock is a cheap, 36/36
      failing site today. `repro_watchdog_budget_collision.py` is RED until it is fixed.
      *(That repro is now GREEN — see the DONE line above.)*


---

- [x] `#24-r121gate` — ✅ **CLOSED 2026-08-10: it is ALREADY BUILT. The "ready to build" header
      was the THIRD stale item found this week** (after `#24-leadcounter` and `#24-counters`
      phase 2), and it was caught only because the spec was verified before coding.
      In code: `ROUTE121_AQUA_GATE_TRIGGER = (25, 5)` (`early_game.py:6534`), the guard
      `get_event_var("ROUTE121_STATE") >= 1` (:6572), and `do_mt_pyre_summit()` (:6615),
      which the story run calls at `story_mode.py:3504`.
      ‼ The spec itself was re-verified against the decomp and is CORRECT: coord events at
      **(25,5) (25,6) (25,7) (25,8)** gated on `VAR_ROUTE121_STATE == 0`, grunts at
      (30,7)/(30,8)/(31,7), flag **914** `HIDE_ROUTE_121_TEAM_AQUA_GRUNTS`, and
      `Route121_EventScript_AquaGruntsMoveOut` ends with `setvar VAR_ROUTE121_STATE, 1`.
      ‼ Note the accessor names carry NO `FLAG_`/`VAR_` prefix — `get_event_var` returns −1
      for an unknown name, so `VAR_ROUTE121_STATE` would fail silently.
      HISTORY — **Fully specified, ready to build.**
      Three Team Aqua grunts at (30,7)/(31,7)/(30,8) seal Route 121's only corridor south
      (`FLAG_HIDE_ROUTE_121_TEAM_AQUA_GRUNTS` = 914, measured **False** = visible). Coord trigger
      **(25,5)-(25,8)** at `VAR_ROUTE121_STATE == 0` runs `Route121_EventScript_AquaGruntsMoveOut`,
      which removes them and sets the var to 1. Guard on `VAR_ROUTE121_STATE >= 1`.
      Spec: `12-STORYMODE-DESIGN.md` §Ch14-PRE. ‼ Use explicit adjacent-map legs, not one generic
      journey call — `calculate_path` spans only DIRECTLY CONNECTED maps.


---

- [x] **`#24-x4headless` — DONE 2026-07-31. Headless ENDLESS-RESET batch runner**
      (`tools/story-dev/x4_headless.py`, repro `repro_x4_headless.py`, 55 checks, no emulator).
      Runs N parallel lanes of the USER'S mode — `Story (ENDLESS RESET)`, headless — instead of
      livetest's plain `Story`, so finish rates measured here are finally comparable to the
      user's bundles (plain `Story` ENDS a run on a `BotModeError`; `ENDLESS RESET` swallows it
      and starts a fresh run, so livetest has always been the harsher measurement).
      `--lanes N` (default 4 = the dashboard's split; 8 = **2 per starter + 2 random**, which
      doubles per-starter sample size — needed for starter-specific bugs like
      `#24-starter-gym3`). Bounded by `--minutes` and/or `--runs` (refuses to run unbounded).
      Output `x4-runs/<stamp>/` with `MANIFEST.txt`, `summary.json`, per-lane stdout + the
      debug logs **from this window only**, plus root `INDEX.md`/`LATEST.txt` recording each
      batch's **COMMIT HASH**.
      ‼ **Emulation is ASSERTED, not re-set:** every run's RUN HEADER must read
      `emulation: speed=0 video=True`, checked for the WHOLE batch (the historical bug is
      "run 1 fine, run 2 at 1x"); a violation aborts loudly. Empirically confirmed on a 2-lane
      smoke batch at **~1,211 fps/lane**. Shipped with a fix for `--endless-target`, which was
      parsed and then discarded by every frontend except the tile lane.


---

- [x] **`#24-smashroute` — DONE 2026-07-31. The bot clears a field-move obstacle that seals a
      journey, and can now reach FIERY_PATH from Mauville.** Live A/B
      (`story_harness.py --driver smashroute`, `rocksmash_taught.ss1`): OLD arm
      `arrived=False map=MAUVILLE_CITY`; **NEW arm `arrived=True map=FIERY_PATH`, 45,305
      frames.** `modules/story/obstacle_clearing.py` reads the ROM's own object events (no
      coordinate table to rot — symbol names COUNTED off the ROM: StrengthBoulder 59,
      RockSmash 44, CutTree 33), gates on move+badge+a reachable approach tile, derives the
      stand tile and facing, and delegates to the already-hardened `_smash_rock`. Hooked into
      `_navigate_riding_out` **before** its fail-fast guard — smashing the rock changes the
      world, which is the premise that guard tests.
      ‼ **Only Rock Smash is actionable.** Cut is known-but-never-validated; **Strength is
      excluded deliberately** — a boulder is PUSHED, not removed, so the "object is gone"
      success test can never fire. Both recorded in `KNOWN_BUT_UNSUPPORTED` with reasons.
      ‼ **Shipped with a re-entrancy bug and the sweep caught it** — `clear_obstacle` →
      `_smash_rock` → `_navigate_riding_out` runs through the hook itself. Guarded now; see
      `08-MISTAKES` 2026-07-31. Repro: `repro_obstacle_clearing.py` (24 checks, no emulator).


---

- [x] **`#24-reprorot` — DONE 2026-07-30. The 4 "environmental / needs mgba" failures were
      four DIFFERENT rots, and none needed an emulator it did not have.** All four launched
      mGBA 0.10.2 fine; all four now pass. `repro_boss_training` (stub `self` missing
      `_boss_plan_is_hopeless`), `repro_double_faint` (stub mon missing `.level`),
      `repro_navigate_failfast` (asserted a STRING where the code correctly raises a
      BotModeError SUBCLASS), `repro_sufficiency` (four compounding fixture faults —
      no `grass` in the cfg, no `total_exp`, no `MAX_PREP_TRAINING_FRAMES`, and **no
      emulator at all**, so the ROM encounter tables were unreadable).
      **No production behaviour was wrong in any of them.**
      ‼ **The lasting lesson is `repro_sufficiency`:** two of its four faults produced NO
      crash, because the lookahead sits inside `except Exception: pass` — a missing stub
      attribute became a silently WRONG VERDICT. That is a RECURRENCE of the exact failure
      `_boss_plan_is_hopeless`' own comment warns about. Both stubs are now `_StoryModeStub`,
      which HARVESTS every UPPERCASE constant instead of hand-listing them and raises a
      self-explaining error when the code grows a new dependency. **Copy that pattern into
      any new repro that stands in for `StoryMode`.**


---

- [x] **`#24-menuorder` — DONE 2026-07-30. Story block + ×4 controls hoisted to the TOP of
      the Bot-mode popup** (user request: *"I have to scroll around to activate them and
      end/park them"*). `Park ×4` and `Stop Endless Loop ×4` used to be the LAST TWO entries,
      below the greyed-out modes. New order: Manual → **STORY** (4 modes + Endless
      Debug-Reset + Endless Loop ×4 + Park ×4) → OTHER MODES → disabled → Debug Logging.
      Ordering extracted from the Tk callback into the pure
      `dashboard_gui.build_mode_menu_plan()`; `repro_mode_menu_order.py` (14 checks, no Tk,
      no emulator) asserts it so it cannot drift back.
      ‼ Entries keep a FIXED position — a non-selectable Story mode is greyed IN PLACE
      rather than dropping to the bottom, and `Park ×4` is always shown (greyed when idle).
      Hiding it was the 2026-07-26 choice and it is what made the layout move.
      Story modes matched by PREFIX, so a future `Story (…)` is hoisted automatically.


---

- [x] ~~`#24-team`~~ — ‼ **SUPERSEDED by `#24-organicteam`**, which is ✅ **APPROVED — GATE
      LIFTED** (user 2026-08-06, re-confirmed 2026-08-14). ⛔ This pointer said the target
      "carries the user's 2026-08-05 DEFERRAL — the live instruction" until 2026-08-14; that was
      stale (the deferral was reversed on 2026-08-06). Consolidated 2026-08-10.
      HISTORY — #24-team — ORGANIC TEAM-BUILDING / helper acquisition (user 2026-07-20;
      design in 12-STORYMODE-DESIGN §TB). Bot builds a team to beat gyms/trainers
      but decides to catch "helpers" ORGANICALLY: a rising "recruit urge" that
      grows with failed/struggled battles (increasing re-rolls/odds), weighted by
      real team gaps (type matchup vs the fight, team type-diversity, move
      coverage), pulling candidates from the obtainability+reachability data
      (#41/#42). Random/human-like, not a min-maxer. Needed for Torchic-vs-Roxanne
      and later type-hard gyms; implement when a gym requires it.

---

- [x] **(4) ✅ DONE 2026-08-16 — `story_harness.py` no longer overwrites its log.** The default is
      now `harness_<build>_<driver>_<timestamp>_<pid>.log`, which **cannot collide**, and the run
      PRINTS its path as its first line (`[setup] LOG -> …`) so the "read the flushed log while it
      hangs" workflow still works. `--log` still pins a path exactly.
      ✅ **REGRESSION-TESTED, not just changed:** both arms of a real A/B run back to back now leave
      TWO transcripts with different content (`EXPECTATION = COUPLED` / `= DECOUPLED`); forcing both
      arms onto one path with `--log` reproduces the OLD destruction (arm 1's transcript gone),
      which is the fault test. ‼ The old fix had shipped as a PROSE HABIT ("give each arm a distinct
      `--log`") that a fresh session had no reason to know — this is the same rule as a GATE.
      ⚠ Docs that named `harness_sandbox.log` as the file to read are updated (`04-HANDOFF`,
      `14-AGENT-PLAYBOOK`, `05-KNOWN-ISSUES`); the append-only logs keep their historical wording.

---

- [x] `#24-x4-framebudget` — **the per-run frame cap could not stop a runaway run.** DONE
      2026-07-27. `MAX_FRAMES_PER_RUN` was only checked AFTER `super().run()` returned, so a
      run that never returns never reached it. Three of four lanes spent the night in ONE
      run — P3 hung **27M frames / ~6.5 h** at the Weather Institute (`controllable=False`,
      frozen position, and ZERO STUCK dumps, i.e. the global watchdog was itself what
      wedged); P1 19.9M and P2 13.4M frames in grind loops that are genuinely BUSY, so no
      progress detector can ever see them. ~16 of 29 lane-hours lost. P4 run 12 reported the
      cap after burning 2x it. FIX: `_run_with_frame_budget()` enforces the budget every
      2048 yields from inside the run, re-basing when the frame counter goes backwards at
      the mid-run hard reset. REPRO: `tools/story-dev/repro_endless_frame_budget.py`.

---

- [x] **✅ #24-ch8b-museum — DONE 2026-07-22; the marker was 31 DAYS STALE (found by a PASS 5
      cold-start audit, closed 2026-08-22).** The gating was resolved and decomp-verified the same
      day KI-11 was: `early_game.py:3584-3586` documents that the Team Aqua crowd
      (`FLAG_HIDE_SLATEPORT_CITY_TEAM_AQUA`) seals the doors until you visit Stern's Shipyard and
      talk to Dock, and `deliver_devon_goods_to_stern` is built at `early_game.py:3617`. KI-11 is
      archived RESOLVED (`31-KNOWN-ISSUES-ARCHIVE.md:1080`). ⛔ It did NOT block Ch8b/Ch9 — that
      clause was false for a month. ‼ **The item's OWN text said "(deliver_devon_goods_to_stern is
      built)" while carrying `[ ]`** — a status contradicted by its own body is the cheapest
      possible re-do trap, and this project's 8-day case is what created the triage index.


## 📦 ARCHIVED 2026-08-24 from `04-HANDOFF.md` NEXT ACTIONS (R3 budget: it hit 909/900)

> (P4) Stage 1 + Stage 2 driven-evidence block. Moved VERBATIM, nothing deleted; a 6-line stub
> remains in the handoff carrying the verdict and the DO-NOT-REBUILD marker.
> ‼ The handoff's own banner says ARCHIVE FIRST, WRITE SECOND. I wrote first and R3 went RED —
> the warning was right, and the cost was one extra edit cycle at the end of a long session.

---

>    ✅✅ **STAGE 1 IS DRIVEN (`--driver boxcounter`), BOTH ARMS PASS — the first time
>    `box_counter_pid` ran against REAL `gPokemonStorage` memory rather than `FakeStorage`.**
>    ARM B → the Slugma's PID (found by its MOVE); ARM A
>    (`POKEBOT_BOXCOUNTER_TYPEONLY_A=1`) → `None`, **the user's bug reproduced on demand**.
>    Four controls: `disjoint` (pure FIRE, so the type branch is provably inert), `fixture_ok`
>    (read back through the PRODUCTION reader — mandatory, since a bad fixture is
>    indistinguishable from ARM A's expected miss), `sole`, and `not_excluded`.
>    ✅✅ **STAGE 2 IS DRIVEN (2026-08-15) — `--driver boxcounter2`, matrix {ARM A, ARM B} ×
>    {sandbox, custom} = 4/4 `ACCEPTANCE: PASS`. ⛔ DO NOT REBUILD IT.**
>    It SUBCLASSES `BoxCounterMode`, so every Stage 2 run re-proves Stage 1 first.
>    **ARM B:** the real `heal_in_pokemon_center(FortreeCity)` collected the boxed Slugma —
>    `moved=True` (in party AND gone from box), `knows_rock_throw=True`, `lead_is_counter=True`
>    with a `hunted_pids=None` CONTROL proving the mechanism was decisive
>    (`control=Mightyena L38` → `real=Slugma L15`), and a second heal that NO-OPed *for the
>    attributed reason* (`find_in_box=None` AND still in party). Production made room itself
>    (`depositing Skitty L17`). **ARM A:** `box_counter_pid` → `None` → `_hunted_counter_pids`
>    published EMPTY → the withdraw piggyback did nothing → `still_boxed=True not_in_party=True`
>    and **no deposit at all** — the user's derail, produced by production, not simulated.


## 📦 ARCHIVED 2026-08-24 (2nd) from `04-HANDOFF.md` NEXT ACTIONS — R3 budget hit 909/900 AGAIN

> `#24-driftassertions` history block. Moved VERBATIM, nothing deleted; a 6-line stub remains.
> ‼ SECOND R3 OVERFLOW IN ONE SESSION, hours after logging the ARCHIVE-FIRST rule in
> `08-MISTAKES.md`. The rule is not 'archive when you remember' — it is: run `lint_docs.py`
> BEFORE adding a section to a near-full file, every time.

---

>    ✅✅ **PREVIOUS QUEUE ITEM 0 IS DONE (2026-08-17): `#24-driftassertions` — THE DRIFT-STATEMENT
>    SWEEP IS NOW A GATE. ⛔ DO NOT REBUILD IT.** `audit_doc_consistency.py::check_drift` detects
>    CLAIM SHAPE, not just the `expect` vocabulary. **A/B against the COMMITTED gate (`git show
>    HEAD:`), same corpus, ground truth stubbed identically: 4 sites caught BEFORE → 9 AFTER, none
>    lost.** The five newly caught are the ones that had gone stale unseen, including THIS FILE's
>    `:167` STATE cell and the fenced HOW TO RUN line. **17** fault tests shipped (`--self-test`
>    D9–D22), firing tests AND false-positive controls — including two exemption BYPASSES an
>    adversarial review found in the FIRST DRAFT (D20/D21), each REPRODUCED before it was fixed.
>    ‼ Both had bound the exemption to the NEIGHBOURHOOD of a figure rather than to the figure, so
>    an innocuous aside containing `read`/`until` silenced a live claim. Detail in `03-PUNCH-LIST.md`; the
>    negation ruling is in `06-DECISIONS-LOG.md`. ‼ **What it does NOT do:** the REDUCTION half
>    (one figure, everywhere else points at the command) was always separate and is now its own
>    item, `#24-driftreduction`.
>


## 📦 ARCHIVED 2026-08-24 (3rd) from `04-HANDOFF.md` NEXT ACTIONS — R3 headroom

> Two CLOSED blocks, moved VERBATIM, nothing deleted; each left a stub with its verdict.
> ‼ AN EARLIER ATTEMPT TODAY OVER-ARCHIVED BY 278 LINES and swallowed the `NEXT ACTIONS`
> heading, because the anchor phrase ALSO appears inside the ~6,000-char banner on line 10,
> so the scan started there and ran forward. Caught immediately, fully restored.
> ⇒ SCOPE THE SEARCH TO THE SECTION, AND ASSERT THE BLOCK HOLDS NO LIVE MARKERS BEFORE
> WRITING — that assertion then FIRED on the next candidate and refused a bad move.

---

>    ✅✅ **PREVIOUS QUEUE ITEM 0 IS HALF DONE (2026-08-17): `(P4c) #24-orphans` (1) — THE
>    INSTRUMENTATION HALF IS BUILT, GATED AND A/B-PROVEN. ⛔ DO NOT REBUILD IT.** All five exits of
>    `withdraw_from_box` return `(landed, code, detail)`; its ONE caller BINDS the result and reports
>    it through the new PURE `withdraw_verdict_report`. **MEASURED, live, `--driver boxcounter2` on
>    `fortree_gym_wedge.ss1`: ARM B unfaulted → `verdict landed=True code=landed`, `ACCEPTANCE: PASS`;
>    ARM A `POKEBOT_PCWITHDRAW_FAULT=1` → `verdict landed=False code=did_not_land`, fault provably
>    armed, `ACCEPTANCE: FAIL` — the registry's DOCUMENTED expectation for a faulted arm, not a
>    regression.** Gate #26 `repro_withdraw_verdict.py` **FAILED against the then-unpromoted
>    `custom` tree (exit 1, six named sites) and now PASSES it (exit 0)** — so it was fault-tested
>    against REALITY, and that flip is the promotion's own proof. ✅ **PROMOTED 2026-08-17: drift is 3 (`seafloor_cavern.py` + `story_mode.py` — the §Ch20 chapter and its Segment 19b/20 wiring, sandbox only, UNDER CONSTRUCTION; ⛔ NOT a promotion decision until driven) and nothing awaits the USER's
>    call.** ⛔ **ITS REACTION HALF REMAINS OPEN** — what production should DO about a failed withdraw
>    is the USER's ruling AND is blocked on the unmeasured `sStorage->messageText` offset; read
>    `06-DECISIONS-LOG.md` before touching it.
>

---

>    ✅✅ **PREVIOUS QUEUE ITEM 0 IS DONE (2026-08-17): `#24-abortswallow` ROUND 3. ⛔ DO NOT REDO IT.**
>    **(1) SHIPPED, 37 → 36** — the probe recognises the hand-written guard
>    `if story_should_abort(): raise`; it sits in the HANDLER, and searching the try BODY removes
>    ZERO sites. ⛔⛔ **(2) REFUTED — DO NOT BUILD IT.** I built it (whole-package call graph, 2,208
>    functions) and it cuts 36 → 8, but the UPWARD fault test makes FIVE ALREADY-FIXED sites
>    invisible, including `mossdeep_gym.py:465` — an OBSERVED failure recorded in our own punch list.
>    ⇒ **the predicate is wrong:** after a whiteout an ORDINARY operation fails for an ordinary
>    reason and the handler fabricates a diagnosis; nothing abort-shaped is raised, so the latch is
>    the only evidence — which is why `reraise_if_aborting` is LATCH-keyed. A reachability filter
>    contradicts the design of the guard it filters for. Full reasoning in `03-PUNCH-LIST.md` and
>    `08-MISTAKES.md`.


## 📦 ARCHIVED 2026-08-26 from `04-HANDOFF.md` NEXT ACTIONS (R3 budget, user-redirect edit)

> Moved VERBATIM, nothing deleted; a 3-line stub remains. The guarded method (section-scoped
> search + live-marker assertion) was used — the assertion is what prevented a repeat of the
> 278-line over-archive of 2026-08-24.

---

>    ✅✅ **PREVIOUS QUEUE ITEM 0 IS PART DONE (2026-08-17): `#24-abortswallow` — 8 MORE SITES FIXED,
>    probe **45 → 37**, MEASURED. ⛔ DO NOT REDO THOSE EIGHT.** All eight were hand-verified to reach
>    `_check_abort()` BEFORE being touched — the triage decided what to fix, not the probe.
>    `counter_hunt.py` (its only candidate, now gone) plus `early_game.py`'s meteorite, Rusturf
>    smash, Strength teach and FOUR heal stops. ‼ **The four heal handlers were UNDOING the
>    2026-08-16 guard one frame after it fired** — `heal_in_pokemon_center` re-raises on the latch
>    and they caught it. ⛔ **`counter_hunt.py` needed a DIFFERENT shape**: it catches `Exception`, so
>    it re-raises only BotModeError-family objects — a `PathFindingError` is a `RuntimeError` and
>    re-raising one would escape `StoryMode.run` and leave the global latch STUCK TRUE
>    (`higher_level_actions.py:842`). ✅ Fault-tested both ways with no emulator: latch CLEAR → still
>    swallows (normal operation untouched); latch SET → `StoryAbort` and a laundered `BotModeError`
>    both propagate; latch SET + `PathFindingError` → still swallowed, so the narrowing cannot leak.
>
